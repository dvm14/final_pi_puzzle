"""
game.py — Main game loop for the Emotion Puzzle Game.

Threading model:
  Main thread   : state machine, display, game logic
  Camera thread : continuous picamzero capture, stores latest RGB frame
  Sensor thread : polls both HC-SR04 sensors every 200 ms

Camera fallback:
  If picamzero is not importable (dev machine), the camera thread generates
  a blank (black) RGB frame so the rest of the code path still runs.

Run:
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
from sensor import UltrasonicSensor
from detector import EmotionDetector, GestureDetector
from display import LCDDisplay
from game_logic import (
    GameState, RoundTarget, DetectionResult, RoundRecord,
    random_target, compute_score, game_passed,
)


# ---------------------------------------------------------------------------
# Camera thread
# ---------------------------------------------------------------------------

class CameraThread(threading.Thread):
    """
    Continuously captures RGB frames from picamzero (or generates blank frames
    in simulation mode).  Stores the latest frame under a Lock.
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
                    frame = self._cam.capture_array()  # RGB numpy array
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
        """Return the latest captured frame (or None if not yet ready)."""
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    def wait_for_first_frame(self, timeout=5.0):
        """Block until the first frame is captured, or timeout."""
        return self._ready.wait(timeout=timeout)

    def stop(self):
        self._stop.set()


# ---------------------------------------------------------------------------
# Sensor thread
# ---------------------------------------------------------------------------

class SensorThread(threading.Thread):
    """
    Polls both HC-SR04 sensors every 200 ms and stores the latest zone readings.
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
        """Return (left_zone, right_zone) — each a string or None."""
        with self._lock:
            return self._left_zone, self._right_zone

    def stop(self):
        self._stop.set()


# ---------------------------------------------------------------------------
# Main game
# ---------------------------------------------------------------------------

class EmotionPuzzleGame:

    def __init__(self):
        self._cfg = CONFIG

        # Hardware / detection
        self._left_sensor  = UltrasonicSensor(
            self._cfg["left_trig"], self._cfg["left_echo"], self._cfg
        )
        self._right_sensor = UltrasonicSensor(
            self._cfg["right_trig"], self._cfg["right_echo"], self._cfg
        )
        self._emotion_detector  = EmotionDetector()
        self._gesture_detector  = GestureDetector()
        self._display           = LCDDisplay(self._cfg)

        # Threads
        self._cam_thread    = CameraThread(self._cfg)
        self._sensor_thread = SensorThread(self._left_sensor, self._right_sensor)

        # Game state
        self._state        : GameState       = GameState.INTRO
        self._round_num    : int             = 0
        self._records      : list            = []
        self._current_target: RoundTarget | None = None
        self._state_start  : float          = 0.0   # time.monotonic() at state entry

    # ------------------------------------------------------------------
    # State machine helpers
    # ------------------------------------------------------------------

    def _enter(self, state: GameState):
        self._state       = state
        self._state_start = time.monotonic()

    def _elapsed(self) -> float:
        return time.monotonic() - self._state_start

    def _remaining(self, duration: float) -> float:
        return max(0.0, duration - self._elapsed())

    # ------------------------------------------------------------------
    # State handlers — called every loop tick
    # ------------------------------------------------------------------

    def _handle_intro(self):
        self._display.draw_intro()
        # Wait for any key (console) or a fixed delay on Pi without keyboard
        time.sleep(0.1)
        # Transition automatically after showing the screen for a moment,
        # or wait for keyboard input on dev machines.
        if self._elapsed() >= 3.0:
            self._round_num = 0
            self._records   = []
            self._enter(GameState.ROUND_START)

    def _handle_round_start(self):
        if self._elapsed() < 0.01:
            # First tick: generate target
            self._round_num    += 1
            self._current_target = random_target()

        self._display.draw_round_start(self._round_num, self._current_target)
        time.sleep(0.05)

        if self._elapsed() >= self._cfg["round_start_seconds"]:
            self._enter(GameState.COUNTDOWN)

    def _handle_countdown(self):
        remaining = self._remaining(self._cfg["prepare_seconds"])
        self._display.draw_countdown(self._current_target, remaining, self._round_num)
        time.sleep(1.0 / 15)  # ~15 FPS refresh

        if remaining <= 0:
            self._enter(GameState.HOLD)

    def _handle_hold(self):
        remaining = self._remaining(self._cfg["hold_seconds"])
        self._display.draw_hold(remaining, self._cfg["hold_seconds"])
        time.sleep(1.0 / 15)

        if remaining <= 0:
            self._enter(GameState.DETECT)

    def _handle_detect(self):
        # Grab latest frame and sensor readings at this exact moment
        frame = self._cam_thread.get_frame()
        left_zone, right_zone = self._sensor_thread.get_zones()

        emotion_label, _ = self._emotion_detector.predict(frame)
        gesture_result   = self._gesture_detector.detect(frame) if frame is not None \
                           else {"Left": (None, 0.0), "Right": (None, 0.0)}

        left_gesture,  _ = gesture_result["Left"]
        right_gesture, _ = gesture_result["Right"]

        detection = DetectionResult(
            emotion        = emotion_label,
            left_gesture   = left_gesture,
            right_gesture  = right_gesture,
            left_distance  = left_zone,
            right_distance = right_zone,
        )

        passed = detection.matches(self._current_target)
        self._records.append(RoundRecord(
            round_num = self._round_num,
            target    = self._current_target,
            detection = detection,
            passed    = passed,
        ))

        # Stash for RESULT state
        self._last_detection = detection
        self._last_passed    = passed

        self._enter(GameState.RESULT)

    def _handle_result(self):
        if self._elapsed() < 0.01:
            self._display.draw_result(
                self._last_passed, self._current_target, self._last_detection
            )

        time.sleep(0.05)

        if self._elapsed() >= self._cfg["result_display_seconds"]:
            if self._round_num < self._cfg["total_rounds"]:
                self._enter(GameState.ROUND_START)
            else:
                self._enter(GameState.FINAL_SCORE)

    def _handle_final_score(self):
        if self._elapsed() < 0.01:
            score         = compute_score(self._records)
            round_results = [r.passed for r in self._records]
            self._display.draw_final_score(score, round_results)

        time.sleep(0.1)

        # Restart after a pause
        if self._elapsed() >= 5.0:
            self._enter(GameState.INTRO)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        self._cam_thread.start()
        self._sensor_thread.start()

        # Wait for camera to produce the first frame
        if not self._cam_thread.wait_for_first_frame(timeout=5.0):
            warnings.warn("[game] Camera did not produce a frame within 5 s — continuing anyway.")

        self._enter(GameState.INTRO)

        _handlers = {
            GameState.INTRO       : self._handle_intro,
            GameState.ROUND_START : self._handle_round_start,
            GameState.COUNTDOWN   : self._handle_countdown,
            GameState.HOLD        : self._handle_hold,
            GameState.DETECT      : self._handle_detect,
            GameState.RESULT      : self._handle_result,
            GameState.FINAL_SCORE : self._handle_final_score,
        }

        while True:
            _handlers[self._state]()

    def shutdown(self):
        """Clean up all hardware resources."""
        self._cam_thread.stop()
        self._sensor_thread.stop()
        self._left_sensor.cleanup()
        self._right_sensor.cleanup()
        self._display.close()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    game = EmotionPuzzleGame()
    try:
        game.run()
    except KeyboardInterrupt:
        print("\n[game] Interrupted — shutting down.")
    finally:
        game.shutdown()
