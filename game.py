"""
game.py — Main game loop for the Emotion Puzzle Game.

Threading model:
  Main thread   : State machine, display rendering, and core game logic.
  Camera thread : Continuously captures frames from picamzero, stores latest RGB frame.
  Sensor thread : Polls both HC-SR04 sensors every 200 ms.

Camera fallback:
  If picamzero is not importable (e.g., running on a dev machine), the camera thread 
  generates a blank (black) RGB frame so the rest of the code path still runs without crashing.

Button simulation:
  If RPi.GPIO is not importable, the button never registers a physical press.
  Prompt states (READY_PROMPT, SHOW_SCORE_PROMPT, PLAY_AGAIN_PROMPT) will
  auto-advance after a short timeout so the game can still be tested on a laptop.

How to run:
  python game.py
"""

import threading
import time
import warnings
import numpy as np

try:
    from picamzero import Camera as PiCamera
    _PICAM_AVAILABLE = True
except ImportError:
    _PICAM_AVAILABLE = False
    warnings.warn("[game] picamzero not available — camera frames will be blank (simulation).")

from config import CONFIG
from sensor import UltrasonicSensor, Button
from detector import EmotionDetector, GestureDetector
from display import LCDDisplay
from game_logic import (
    GameState, RoundTarget, DetectionResult, RoundRecord,
    random_target, compute_score, game_passed,
)

# How long to wait before auto-advancing a button-prompt state in simulation mode
_SIM_PROMPT_TIMEOUT = 3.0


# ---------------------------------------------------------------------------
# Camera thread
# ---------------------------------------------------------------------------

class CameraThread(threading.Thread):
    """
    Continuously captures RGB frames from picamzero (or generates blank frames
    in simulation mode). Stores the latest frame safely using a Threading Lock.
    """

    def __init__(self, config=CONFIG):
        super().__init__(daemon=True)
        self._lock   = threading.Lock()
        self._frame  = None
        self._ready  = threading.Event()
        self._stop   = threading.Event()
        self._w      = config["camera_width"]
        self._h      = config["camera_height"]
        self._cam    = None

    def run(self):
        if _PICAM_AVAILABLE:
            self._cam = PiCamera()
        try:
            while not self._stop.is_set():
                if _PICAM_AVAILABLE:
                    frame = self._cam.capture_array()  # Captures an RGB numpy array
                else:
                    frame = np.zeros((self._h, self._w, 3), dtype=np.uint8)
                
                with self._lock:
                    self._frame = frame
                self._ready.set()
        finally:
            if self._cam is not None:
                try:
                    self._cam.close()
                except Exception:
                    pass

    def get_frame(self):
        """Return a copy of the latest captured frame (or None if not yet ready)."""
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    def wait_for_first_frame(self, timeout=5.0):
        """Block the execution until the first frame is successfully captured, or timeout."""
        return self._ready.wait(timeout=timeout)

    def stop(self):
        """Signal the thread to stop capturing and exit."""
        self._stop.set()


# ---------------------------------------------------------------------------
# Sensor thread
# ---------------------------------------------------------------------------

class SensorThread(threading.Thread):
    """
    Polls both HC-SR04 sensors every 200 ms and stores the latest color zone readings.
    """

    def __init__(self, left_sensor: UltrasonicSensor, right_sensor: UltrasonicSensor):
        super().__init__(daemon=True)
        self._left   = left_sensor
        self._right  = right_sensor
        self._lock   = threading.Lock()
        self._stop   = threading.Event()
        self._left_zone  = None
        self._right_zone = None

    def run(self):
        while not self._stop.is_set():
            lz = self._left.read_zone()
            rz = self._right.read_zone()
            
            with self._lock:
                self._left_zone  = lz
                self._right_zone = rz
            time.sleep(0.2)

    def get_zones(self):
        """Return a tuple of (left_zone, right_zone) — each is a color string or None."""
        with self._lock:
            return self._left_zone, self._right_zone

    def stop(self):
        """Signal the sensor thread to stop reading and exit."""
        self._stop.set()


# ---------------------------------------------------------------------------
# Main game core
# ---------------------------------------------------------------------------

class EmotionPuzzleGame:

    def __init__(self):
        self._cfg = CONFIG

        # Hardware / detection initialization
        # Note: Added hand_side parameters to map distances to specific colors
        self._left_sensor  = UltrasonicSensor(
            self._cfg["left_trig"], self._cfg["left_echo"], self._cfg, hand_side='left'
        )
        self._right_sensor = UltrasonicSensor(
            self._cfg["right_trig"], self._cfg["right_echo"], self._cfg, hand_side='right'
        )
        self._button            = Button(self._cfg["button_pin"])
        self._emotion_detector  = EmotionDetector()
        self._gesture_detector  = GestureDetector()
        self._display           = LCDDisplay(self._cfg)

        # Initialize background threads
        self._cam_thread    = CameraThread(self._cfg)
        self._sensor_thread = SensorThread(self._left_sensor, self._right_sensor)

        # Game state tracking variables
        self._state         : GameState        = GameState.INTRO
        self._round_num     : int              = 0
        self._records       : list             = []
        self._current_target: RoundTarget | None = None
        self._state_start   : float            = 0.0
        self._last_detection: DetectionResult | None = None
        self._last_passed   : bool             = False

    # ------------------------------------------------------------------
    # State machine helpers
    # ------------------------------------------------------------------

    def _enter(self, state: GameState):
        """Transition to a new game state and record the starting time."""
        self._state       = state
        self._state_start = time.monotonic()

    def _elapsed(self) -> float:
        """Calculate how much time has passed since entering the current state."""
        return time.monotonic() - self._state_start

    def _remaining(self, duration: float) -> float:
        """Calculate the remaining time for states that have a fixed duration."""
        return max(0.0, duration - self._elapsed())

    def _button_pressed_or_timeout(self, timeout=_SIM_PROMPT_TIMEOUT) -> bool:
        """
        Return True if the physical button is pressed, OR (in simulation mode)
        if the prompt has been displayed for longer than `timeout` seconds.
        """
        if self._button.is_pressed():
            return True
        if not _PICAM_AVAILABLE and self._elapsed() >= timeout:
            return True
        return False

    # ------------------------------------------------------------------
    # State handlers
    # ------------------------------------------------------------------

    def _handle_intro(self):
        """Show the title screen briefly, then transition to the ready prompt."""
        if self._elapsed() < 0.01:
            self._display.draw_intro()
        time.sleep(0.1)
        if self._elapsed() >= 2.0:
            self._enter(GameState.READY_PROMPT)

    def _handle_ready_prompt(self):
        """Display 'Are you ready to start?' and wait for a button press."""
        if self._elapsed() < 0.01:
            self._round_num = 0
            self._records   = []
            self._display.draw_ready_prompt()
        time.sleep(0.05)
        
        if self._button_pressed_or_timeout():
            time.sleep(0.3)  # Add a slight delay for physical button debounce
            self._enter(GameState.ROUND_START)

    def _handle_round_start(self):
        """Initialize a new round, generate a random target, and show it for 2 seconds."""
        if self._elapsed() < 0.01:
            self._round_num     += 1
            self._current_target = random_target()

        self._display.draw_round_start(self._round_num, self._current_target)
        time.sleep(0.05)

        if self._elapsed() >= self._cfg["round_start_seconds"]:
            self._enter(GameState.COUNTDOWN)

    def _handle_countdown(self):
        """Display a live 5-second countdown for the player to get into position."""
        remaining = self._remaining(self._cfg["prepare_seconds"])
        self._display.draw_countdown(self._current_target, remaining, self._round_num)
        time.sleep(1.0 / 15) # Maintain approx 15 FPS refresh rate for the LCD

        if remaining <= 0:
            self._enter(GameState.HOLD)

    def _handle_hold(self):
        """Display the 'HOLD' screen with a progress bar for 3 seconds."""
        remaining = self._remaining(self._cfg["hold_seconds"])
        self._display.draw_hold(remaining, self._cfg["hold_seconds"])
        time.sleep(1.0 / 15)

        if remaining <= 0:
            self._enter(GameState.DETECT)

    def _handle_detect(self):
        """
        The critical snapshot moment: grab the latest camera frame and sensor zones,
        run AI inferences, and verify against the target.
        """
        frame = self._cam_thread.get_frame()
        left_zone, right_zone = self._sensor_thread.get_zones()

        # Run AI detection on the captured frame
        emotion_label, _ = self._emotion_detector.predict(frame)
        gesture_result   = self._gesture_detector.detect(frame) if frame is not None \
                           else {"Left": (None, 0.0), "Right": (None, 0.0)}

        left_gesture,  _ = gesture_result["Left"]
        right_gesture, _ = gesture_result["Right"]

        # Compile everything into a DetectionResult object
        detection = DetectionResult(
            emotion        = emotion_label,
            left_gesture   = left_gesture,
            right_gesture  = right_gesture,
            left_distance  = left_zone,
            right_distance = right_zone,
        )

        # Check if the player perfectly matched the target combination
        passed = detection.matches(self._current_target)
        
        self._records.append(RoundRecord(
            round_num = self._round_num,
            target    = self._current_target,
            detection = detection,
            passed    = passed,
        ))

        self._last_detection = detection
        self._last_passed    = passed

        self._enter(GameState.RESULT)

    def _handle_result(self):
        """Display PASS or FAIL and a breakdown of which conditions were met."""
        if self._elapsed() < 0.01:
            self._display.draw_result(
                self._last_passed, self._current_target, self._last_detection
            )
        time.sleep(0.05)

        # Show result for 2 seconds before moving to the next round or the end screen
        if self._elapsed() >= self._cfg["result_display_seconds"]:
            if self._round_num < self._cfg["total_rounds"]:
                self._enter(GameState.ROUND_START)
            else:
                self._enter(GameState.SHOW_SCORE_PROMPT)

    def _handle_show_score_prompt(self):
        """Display 'Game over! Press button to show score' and wait for input."""
        if self._elapsed() < 0.01:
            self._display.draw_show_score_prompt()
        time.sleep(0.05)
        
        if self._button_pressed_or_timeout():
            time.sleep(0.3)  # Debounce
            self._enter(GameState.FINAL_SCORE)

    def _handle_final_score(self):
        """Display the final score out of 5, then move to the play-again prompt."""
        if self._elapsed() < 0.01:
            score         = compute_score(self._records)
            round_results = [r.passed for r in self._records]
            self._display.draw_final_score(score, round_results)
        time.sleep(0.1)

        if self._elapsed() >= self._cfg["result_display_seconds"] + 1.0:
            self._enter(GameState.PLAY_AGAIN_PROMPT)

    def _handle_play_again_prompt(self):
        """Display 'Play again? Press button' — wait for input, then restart the game."""
        if self._elapsed() < 0.01:
            self._display.draw_play_again_prompt()
        time.sleep(0.05)
        
        if self._button_pressed_or_timeout():
            time.sleep(0.3)  # Debounce
            self._enter(GameState.INTRO)

    # ------------------------------------------------------------------
    # Main execution loop
    # ------------------------------------------------------------------

    def run(self):
        """Start background threads and initiate the game state machine."""
        self._cam_thread.start()
        self._sensor_thread.start()

        if not self._cam_thread.wait_for_first_frame(timeout=5.0):
            warnings.warn("[game] Camera did not produce a frame within 5s — continuing anyway.")

        self._enter(GameState.INTRO)

        # Map each GameState to its respective handler function
        _handlers = {
            GameState.INTRO             : self._handle_intro,
            GameState.READY_PROMPT      : self._handle_ready_prompt,
            GameState.ROUND_START       : self._handle_round_start,
            GameState.COUNTDOWN         : self._handle_countdown,
            GameState.HOLD              : self._handle_hold,
            GameState.DETECT            : self._handle_detect,
            GameState.RESULT            : self._handle_result,
            GameState.SHOW_SCORE_PROMPT : self._handle_show_score_prompt,
            GameState.FINAL_SCORE       : self._handle_final_score,
            GameState.PLAY_AGAIN_PROMPT : self._handle_play_again_prompt,
        }

        # Infinite state machine loop
        while True:
            _handlers[self._state]()

    def shutdown(self):
        """Clean up all hardware resources and stop threads gracefully."""
        self._cam_thread.stop()
        self._sensor_thread.stop()
        self._left_sensor.cleanup()
        self._right_sensor.cleanup()
        self._button.cleanup()
        self._display.close()


# ---------------------------------------------------------------------------
# Script Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    game = EmotionPuzzleGame()
    try:
        game.run()
    except KeyboardInterrupt:
        print("\n[game] Interrupted by user — shutting down safely.")
    finally:
        game.shutdown()