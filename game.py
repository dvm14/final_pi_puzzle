"""
game.py — Pi Puzzle Game (simple sequential loop, no threading).

Run:  python game.py   (from the v2/ directory)
"""

import time
import json
import random
from types import SimpleNamespace

import numpy as np
import cv2
import sounddevice as sd
from picamzero import Camera
from gpiozero import DistanceSensor, Button
from piper import PiperVoice

try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    import tensorflow.lite as tflite  # type: ignore

from config import CONFIG, EMOTION_OPTIONS, GESTURE_OPTIONS, LEFT_COLOR_OPTIONS, RIGHT_COLOR_OPTIONS
from display import LCDDisplay

TARGET_AUDIO_RATE = 48000  # USB2.0 speaker sample rate

GESTURE_SPOKEN = {
    "thumbs_up"   : "thumbs up",
    "peace"       : "peace sign",
    "thumbs_down" : "thumbs down",
}

# ---------------------------------------------------------------------------
# Hardware init
# ---------------------------------------------------------------------------

print("Initialising hardware...")

display = LCDDisplay(CONFIG)
display.draw_message("Starting up...", "Please wait")

camera       = Camera()
button       = Button(CONFIG["button_pin"], pull_up=True)
left_sensor  = DistanceSensor(trigger=CONFIG["left_trig"],  echo=CONFIG["left_echo"],  max_distance=4.0)
right_sensor = DistanceSensor(trigger=CONFIG["right_trig"], echo=CONFIG["right_echo"], max_distance=4.0)

# ---------------------------------------------------------------------------
# Voice (Piper TTS)
# ---------------------------------------------------------------------------

print("Loading voice model...")
display.draw_message("Loading voice...", "Please wait")
piper = PiperVoice.load(
    model_path=CONFIG["voice_model_path"],
    config_path=CONFIG["voice_config_path"],
)

def speak(text):
    print(f"[voice] {text}")
    try:
        chunks = []
        for chunk in piper.synthesize(text):
            chunks.append(chunk.audio_float_array)
        if chunks:
            audio = np.concatenate(chunks)
            src_rate = piper.config.sample_rate
            if src_rate != TARGET_AUDIO_RATE:
                target_len = int(len(audio) * TARGET_AUDIO_RATE / src_rate)
                audio = np.interp(
                    np.linspace(0, len(audio), target_len),
                    np.arange(len(audio)),
                    audio,
                )
            sd.play(audio, samplerate=TARGET_AUDIO_RATE, device=1)
            sd.wait()
    except Exception as e:
        print(f"[voice error] {e}")

# ---------------------------------------------------------------------------
# Emotion detection
# ---------------------------------------------------------------------------

print("Loading emotion model...")
display.draw_message("Loading model...", "Please wait")

with open(CONFIG["model_config_path"]) as f:
    _mcfg = json.load(f)

_interp = tflite.Interpreter(model_path=CONFIG["emotion_model_path"])
_interp.allocate_tensors()
_in_idx  = _interp.get_input_details()[0]["index"]
_out_idx = _interp.get_output_details()[0]["index"]

def detect_emotion(frame_rgb):
    img    = cv2.resize(frame_rgb, (_mcfg["img_size"], _mcfg["img_size"]))
    tensor = np.clip(
        np.round(img.astype(np.float32) / _mcfg["in_scale"] + _mcfg["in_zero"]),
        0, 255,
    ).astype(np.uint8)[np.newaxis, ...]

    _interp.set_tensor(_in_idx, tensor)
    _interp.invoke()

    raw   = _interp.get_tensor(_out_idx)[0]
    probs = (raw.astype(np.float32) - _mcfg["out_zero"]) * _mcfg["out_scale"]
    exp   = np.exp(probs - probs.max())
    probs = exp / exp.sum()

    idx   = int(np.argmax(probs))
    label = _mcfg["class_names"][idx]
    conf  = float(probs[idx])

    if conf < CONFIG["emotion_confidence"] or label not in EMOTION_OPTIONS:
        return None
    return label

# ---------------------------------------------------------------------------
# Gesture detection — stub (to be replaced by team member)
# ---------------------------------------------------------------------------

def detect_gestures(frame_rgb):
    """Returns {"Left": gesture_or_None, "Right": gesture_or_None}."""
    return {"Left": None, "Right": None}

# ---------------------------------------------------------------------------
# Sensor helpers
# ---------------------------------------------------------------------------

def read_left_color():
    """Close (≤ threshold) → Pink, far → Red."""
    cm = left_sensor.distance * 100
    return LEFT_COLOR_OPTIONS[0] if cm <= CONFIG["dist_threshold"] else LEFT_COLOR_OPTIONS[1]

def read_right_color():
    """Close (≤ threshold) → Blue, far → Green."""
    cm = right_sensor.distance * 100
    return RIGHT_COLOR_OPTIONS[0] if cm <= CONFIG["dist_threshold"] else RIGHT_COLOR_OPTIONS[1]

# ---------------------------------------------------------------------------
# Game helpers
# ---------------------------------------------------------------------------

def wait_for_button():
    """Block until the button is pressed, then debounce."""
    while not button.is_pressed:
        time.sleep(0.05)
    time.sleep(0.3)

def make_target():
    return SimpleNamespace(
        emotion       = random.choice(EMOTION_OPTIONS),
        left_gesture  = random.choice(GESTURE_OPTIONS),
        right_gesture = random.choice(GESTURE_OPTIONS),
        left_color    = random.choice(LEFT_COLOR_OPTIONS),
        right_color   = random.choice(RIGHT_COLOR_OPTIONS),
    )

def announce_target(round_num, target):
    lg = GESTURE_SPOKEN.get(target.left_gesture,  target.left_gesture)
    rg = GESTURE_SPOKEN.get(target.right_gesture, target.right_gesture)
    speak(
        f"Round {round_num}. "
        f"Show a {target.emotion} face. "
        f"Left hand: {lg}. "
        f"Right hand: {rg}. "
        f"Left color: {target.left_color}. "
        f"Right color: {target.right_color}."
    )

# ---------------------------------------------------------------------------
# Main game loop
# ---------------------------------------------------------------------------

print("Ready!\n")

while True:

    # -- INTRO --
    display.draw_intro()
    speak("Welcome to the Pi Puzzle Game!")

    # -- READY PROMPT --
    display.draw_ready_prompt()
    speak("Are you ready to start? Press the button when you are.")
    wait_for_button()

    records = []

    for round_num in range(1, CONFIG["total_rounds"] + 1):

        # -- ROUND START --
        target = make_target()
        display.draw_round_start(round_num, target)
        announce_target(round_num, target)

        # -- COUNTDOWN --
        speak(f"Get ready. You have {CONFIG['prepare_seconds']} seconds.")
        for secs_left in range(CONFIG["prepare_seconds"], 0, -1):
            display.draw_countdown(target, secs_left, round_num)
            time.sleep(1.0)

        # -- HOLD --
        display.draw_hold(CONFIG["hold_seconds"], CONFIG["hold_seconds"])
        speak("Hold still!")
        for secs_left in range(CONFIG["hold_seconds"], 0, -1):
            display.draw_hold(secs_left, CONFIG["hold_seconds"])
            time.sleep(1.0)

        # -- DETECT --
        frame      = camera.capture_array()
        emotion    = detect_emotion(frame)
        gestures   = detect_gestures(frame)
        left_color  = read_left_color()
        right_color = read_right_color()

        detected = SimpleNamespace(
            emotion       = emotion,
            left_gesture  = gestures["Left"],
            right_gesture = gestures["Right"],
            left_color    = left_color,
            right_color   = right_color,
        )

        passed = (
            detected.emotion       == target.emotion       and
            detected.left_gesture  == target.left_gesture  and
            detected.right_gesture == target.right_gesture and
            detected.left_color    == target.left_color    and
            detected.right_color   == target.right_color
        )
        records.append(passed)

        def ok(t, d):
            return "OK" if t == d else "FAIL"

        print(f"\n--- Round {round_num} results ---")
        print(f"  Emotion     : {detected.emotion or '?':10}  (target: {target.emotion})  {ok(target.emotion, detected.emotion)}")
        print(f"  Left hand   : {detected.left_gesture or '?':10}  (target: {target.left_gesture})  {ok(target.left_gesture, detected.left_gesture)}")
        print(f"  Right hand  : {detected.right_gesture or '?':10}  (target: {target.right_gesture})  {ok(target.right_gesture, detected.right_gesture)}")
        print(f"  Left color  : {detected.left_color or '?':10}  (target: {target.left_color})  {ok(target.left_color, detected.left_color)}")
        print(f"  Right color : {detected.right_color or '?':10}  (target: {target.right_color})  {ok(target.right_color, detected.right_color)}")
        print(f"  --> {'PASS' if passed else 'FAIL'}\n")

        # -- RESULT --
        display.draw_result(passed, target, detected)
        if passed:
            speak("Nice job! You passed that round.")
        else:
            speak("Round failed. Better luck next time.")
        time.sleep(CONFIG["result_display_seconds"])

    # -- SHOW SCORE PROMPT --
    display.draw_show_score_prompt()
    speak("Game over! Press the button to see your score.")
    wait_for_button()

    # -- FINAL SCORE --
    score = sum(records)
    display.draw_final_score(score, records)
    if score >= CONFIG["pass_threshold"]:
        speak(f"You scored {score} out of {CONFIG['total_rounds']}. Congratulations, you won!")
    else:
        speak(f"You scored {score} out of {CONFIG['total_rounds']}. Better luck next time!")
    time.sleep(3.0)

    # -- PLAY AGAIN PROMPT --
    display.draw_play_again_prompt()
    speak("Press the button to play again.")
    wait_for_button()