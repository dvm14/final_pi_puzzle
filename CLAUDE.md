# Emotion Puzzle Game — Claude Code Instructions

## Project Overview
A Raspberry Pi puzzle game where the player must match a randomly generated combination of:
- **Facial expression** (detected via EfficientNetB0 TFLite model)
- **Left hand gesture** (detected via MediaPipe Hands)
- **Right hand gesture** (detected via MediaPipe Hands)
- **Left hand distance** (measured via HC-SR04 ultrasonic sensor)
- **Right hand distance** (measured via HC-SR04 ultrasonic sensor)

The game runs 5 rounds. Each round shows a target combination. The player has 5 seconds to get into position and must hold it for 3 seconds. A snapshot is taken at the end of the hold to check all 5 conditions. Score is out of 5 — pass requires 3 or more correct rounds.

---

## Hardware

| Component | Details |
|---|---|
| Board | Raspberry Pi 4 or 5 |
| Camera | Pi Camera Module or USB webcam (index 0) |
| Display | Small SPI TFT LCD (ST7735 / ST7789 / ILI9341) via luma.lcd |
| Left ultrasonic | HC-SR04 — TRIG=GPIO23, ECHO=GPIO24 (BCM) |
| Right ultrasonic | HC-SR04 — TRIG=GPIO27, ECHO=GPIO22 (BCM) |

All GPIO pins and distance thresholds must be defined in a single `CONFIG` dict at the top of `game.py` so they are easy to change.

---

## ML Models (pre-trained, provided by user)

### Emotion Model
- **File:** `emotionnet_int8.tflite`
- **Type:** EfficientNetB0 fine-tuned, INT8 quantized TFLite
- **Config file:** `model_config.json` (contains `img_size`, `class_names`, `in_scale`, `in_zero`, `out_scale`, `out_zero`)
- **Valid emotion classes for this game:** `Happy`, `Surprise`, `Disgust` (model outputs 7 classes total — only use these 3)
- **Preprocessing:** `img = (img / 127.5) - 1.0` then quantize to uint8 using `in_scale` and `in_zero`

### Hand Gesture Detection
- **Library:** MediaPipe Hands (`mediapipe` package)
- **No separate model file needed** — use `mp.solutions.hands` or the Tasks API
- **Gestures to classify:** `thumbs_up`, `peace`, `thumbs_down`
- **Classify from landmarks** using finger extension logic (see Gesture Classification section below)
- Detect **both hands simultaneously** in a single frame
- Identify left vs right hand using MediaPipe's `handedness` output

---

## Game Options

```python
EMOTION_OPTIONS  = ["Happy", "Surprise", "Disgust"]
GESTURE_OPTIONS  = ["thumbs_up", "peace", "thumbs_down"]
DISTANCE_OPTIONS = ["close", "middle", "far"]
```

Each round randomly picks one from each list for all 5 components independently.

---

## Distance Zones

```python
# Configurable in CONFIG
DIST_CLOSE_MAX  = 20   # 0–20 cm   → "close"
DIST_MIDDLE_MAX = 50   # 21–50 cm  → "middle"
                       # >50 cm    → "far"
```

Average 5 sensor readings per measurement to reduce noise. Return `None` if no valid reading.

---

## Game Flow (state machine)

```
INTRO → ROUND_START → COUNTDOWN (5s) → HOLD (3s) → DETECT → RESULT → 
  (repeat for 5 rounds) → FINAL_SCORE
```

### State details

| State | What happens |
|---|---|
| `INTRO` | Show game title, instructions, "Press button / any key to start" |
| `ROUND_START` | Display round number (e.g. "Round 2 / 5") and target combination for 2 seconds |
| `COUNTDOWN` | Live 5-second countdown displayed on LCD. Camera feed runs in background thread |
| `HOLD` | "HOLD!" displayed. 3-second progress bar. Camera + sensors run in background |
| `DETECT` | Capture one frame, run emotion + gesture detection, read both sensors. Compare against target |
| `RESULT` | Show ✅ PASS or ❌ FAIL + what was detected vs what was needed. Display for 2 seconds |
| `FINAL_SCORE` | Show score X/5, "SUCCESS!" or "FAILED", breakdown of each round |

### Round failure
If the player does not hold for the full 3 seconds (e.g. moves away), the round is marked as FAIL automatically and the game moves to the next round.

---

## Gesture Classification Logic

Use MediaPipe hand landmarks. Each fingertip landmark index vs its PIP joint index:

```
Thumb  : tip=4,  ip=3   (special case — compare x position for left/right hand)
Index  : tip=8,  pip=6
Middle : tip=12, pip=10
Ring   : tip=16, pip=14
Pinky  : tip=20, pip=18
```

A finger is **extended** if `tip.y < pip.y` (tip is above pip in image coords).  
Thumb is extended if `|tip.x - ip.x| > threshold` (accounting for hand orientation).

### Gesture rules
```
thumbs_up   : thumb extended, all other fingers curled
thumbs_down : thumb extended downward (tip.y > ip.y), all others curled
peace       : index + middle extended, thumb + ring + pinky curled
```

Return gesture name + confidence (use a simple 0.0/1.0 or rule-based score).

---

## Display (LCD via luma.lcd)

Use **Pillow** (`PIL`) to draw each frame as an image, then push to the LCD.  
Do NOT try to render OpenCV frames directly to the LCD.

### LCD layout per state

**ROUND_START / COUNTDOWN:**
```
┌─────────────────────┐
│   Round 2 / 5       │  ← yellow, top
│                     │
│ Face  : 😊 Happy    │  ← white, small font
│ L Hand: 👍 Thumbs Up│
│ R Hand: ✌️  Peace   │
│ L Dist: 📏 Close    │
│ R Dist: 📏 Far      │
│                     │
│     ⏱  3s           │  ← cyan countdown, large
└─────────────────────┘
```

**HOLD:**
```
┌─────────────────────┐
│       HOLD!         │  ← large orange text
│  ███████░░░  2.1s   │  ← progress bar + time remaining
└─────────────────────┘
```

**RESULT:**
```
┌─────────────────────┐
│    ✅ PASS!          │  ← green   OR   ❌ FAIL   ← red
│                     │
│ Face  : ✅ Happy     │  ← green tick if correct, red X if wrong
│ L Hand: ❌ Thumbs Up │
│ ...                 │
└─────────────────────┘
```

**FINAL_SCORE:**
```
┌─────────────────────┐
│    Score: 4 / 5     │  ← large
│   🎉 SUCCESS!        │  ← green if ≥3, red FAILED if <3
│                     │
│ R1: ✅  R2: ❌  ...  │  ← round breakdown
└─────────────────────┘
```

### Font
Use `ImageFont.truetype` with a TTF font if available, fall back to `ImageFont.load_default()`.  
Suggested font sizes: title=20, body=13, countdown=36.

---

## File Structure

```
emotion_puzzle_game/
├── game.py                  # Main game loop (entry point)
├── detector.py              # EmotionDetector + GestureDetector classes
├── sensor.py                # UltrasonicSensor class
├── display.py               # LCDDisplay class — all Pillow drawing logic
├── game_logic.py            # RoundTarget, DetectionResult, scoring, state machine
├── config.py                # CONFIG dict + all constants
├── assets/
│   ├── font.ttf             # Optional TTF font
│   └── title_screen.png     # Optional splash image
├── models/
│   ├── emotionnet_int8.tflite
│   ├── model_config.json
│   └── face_landmarker.task # (optional, only if using FaceLandmarker Tasks API)
├── requirements.txt
└── README.md
```

---

## Threading Model

The game loop runs on the **main thread**. Camera capture and sensor reads run on **background threads** to avoid blocking the display.

```
Main thread     : state machine, display rendering, game logic
Camera thread   : continuous cv2.VideoCapture read, stores latest frame
Sensor thread   : polls both ultrasonic sensors every 200ms, stores latest readings
Detection       : runs on main thread at snapshot moment (DETECT state)
```

Use `threading.Lock()` to protect shared frame and sensor data.

---

## Simulation Mode

The code must run on a **development machine without GPIO or LCD hardware** for testing:
- If `RPi.GPIO` is not importable → simulate sensor readings with `random.uniform(5, 80)`
- If `luma.lcd` is not importable → display game frames in an `cv2.imshow()` window instead
- Print a warning at startup for each simulated component

---

## Configuration (config.py)

```python
CONFIG = {
    # Paths
    "emotion_model_path"    : "models/emotionnet_int8.tflite",
    "model_config_path"     : "models/model_config.json",

    # Camera
    "camera_index"          : 0,
    "camera_width"          : 640,
    "camera_height"         : 480,

    # LCD
    "lcd_width"             : 240,
    "lcd_height"            : 240,

    # GPIO pins (BCM)
    "left_trig"             : 23,
    "left_echo"             : 24,
    "right_trig"            : 27,
    "right_echo"            : 22,

    # Distance thresholds (cm)
    "dist_close_max"        : 20,
    "dist_middle_max"       : 50,

    # Timing (seconds)
    "prepare_seconds"       : 5,
    "hold_seconds"          : 3,
    "result_display_seconds": 2,
    "round_start_seconds"   : 2,

    # Game
    "total_rounds"          : 5,
    "pass_threshold"        : 3,

    # Detection thresholds
    "emotion_confidence"    : 0.50,
    "gesture_confidence"    : 0.70,
    "ultrasonic_samples"    : 5,
}
```

---

## Requirements (requirements.txt)

```
mediapipe==0.10.14
opencv-python
tflite-runtime      # use tensorflow on non-Pi
numpy
Pillow
luma.lcd
luma.core
RPi.GPIO            # Pi only
```

---

## Build Order

Build files in this order to avoid circular imports:

1. `config.py` — constants and CONFIG dict
2. `sensor.py` — UltrasonicSensor (depends only on config + RPi.GPIO)
3. `detector.py` — EmotionDetector + GestureDetector (depends on config + mediapipe + tflite)
4. `display.py` — LCDDisplay (depends on config + Pillow + luma.lcd)
5. `game_logic.py` — RoundTarget, DetectionResult, state machine logic (depends on config)
6. `game.py` — wires everything together, runs the main loop

---

## Key Implementation Notes

- **Always close GPIO** cleanly in a `try/finally` block in `game.py`
- **Camera thread** should set a `threading.Event` to signal when a frame is ready
- **Emotion detection** runs on a single captured frame — do not average across frames
- **Gesture detection** runs on the same captured frame as emotion — single MediaPipe Hands inference
- If MediaPipe Hands detects only one hand, only that hand's gesture is checked; the other is marked as `None` (which will not match any target → round fails)
- **LCD refresh rate** should target ~15 FPS during countdown/hold states — no need for higher
- All display text must be **left-padded** to fit within `lcd_width` — truncate long strings if needed
- Use `time.monotonic()` not `time.time()` for all game timing to avoid clock drift issues
