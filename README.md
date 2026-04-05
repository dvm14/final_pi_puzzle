# Emotion Puzzle Game

A Raspberry Pi puzzle game where the player must match a randomly generated combination of facial expression, hand gestures, and hand distances — detected live using a camera and ultrasonic sensors.

## How to play

The game runs 5 rounds. Each round shows a target combination on the LCD:

- **Face** — Happy, Surprise, or Disgust
- **Left hand gesture** — Thumbs Up, Peace, or Thumbs Down
- **Right hand gesture** — Thumbs Up, Peace, or Thumbs Down
- **Left hand distance** — Close (0–20 cm), Middle (21–50 cm), or Far (>50 cm)
- **Right hand distance** — same zones

You have **5 seconds** to get into position, then must **hold for 3 seconds**. A snapshot is taken at the end of the hold. Score ≥ 3/5 = WIN.

---

## Hardware

| Component | Details |
|---|---|
| Board | Raspberry Pi 4 or 5 |
| Camera | Pi Camera Module (picamzero) |
| Display | 16×2 I2C LCD (`lcd_i2c`, default address `0x27`) |
| Left ultrasonic | HC-SR04 — TRIG=GPIO23, ECHO=GPIO24 (BCM) |
| Right ultrasonic | HC-SR04 — TRIG=GPIO27, ECHO=GPIO22 (BCM) |

### HC-SR04 wiring (×2)

```
Sensor Pin → Pi Pin
VCC        → 5V (Pin 2 or 4)
GND        → GND
TRIG       → GPIO23 (Pin 16)  ← left sensor
ECHO       → GPIO24 (Pin 18)  ← left sensor  [use 1kΩ + 2kΩ voltage divider]
TRIG       → GPIO27 (Pin 13)  ← right sensor
ECHO       → GPIO22 (Pin 15)  ← right sensor [use 1kΩ + 2kΩ voltage divider]
```

> ⚠️ The HC-SR04 ECHO pin outputs 5 V. Use a voltage divider to bring it to 3.3 V before connecting to the Pi GPIO.

### 16×2 I2C LCD wiring

```
LCD Pin → Pi Pin
VCC     → 5V
GND     → GND
SDA     → GPIO2 / SDA (Pin 3)
SCL     → GPIO3 / SCL (Pin 5)
```

If the LCD doesn't show anything, try I2C address `0x3F` in `config.py` (`lcd_i2c_address`).

---

## Project structure

```
final_pi_puzzle/
├── game.py          # Entry point — main game loop & state machine
├── detector.py      # EmotionDetector (complete) + GestureDetector (stub)
├── sensor.py        # UltrasonicSensor class
├── display.py       # LCDDisplay class (16×2 I2C)
├── game_logic.py    # RoundTarget, DetectionResult, scoring, state enum
├── config.py        # All configuration constants
├── models/
│   ├── emotionnet_int8.tflite   # INT8 quantized EfficientNetB0 (provided)
│   └── model_config.json        # img_size, class_names, quant params
├── assets/
│   └── (optional extras)
└── requirements.txt
```

---

## Setup

### 1. Install dependencies

On the Pi:
```bash
pip install -r requirements.txt
```

On a dev machine (for simulation):
```bash
pip install tflite-runtime numpy opencv-python
# lcd_i2c, RPi.GPIO, picamzero are Pi-only — skip them for local testing
```

### 2. Add the model files

Place your trained model files in `models/`:
```
models/emotionnet_int8.tflite
models/model_config.json
```

`model_config.json` must contain:
```json
{
  "img_size": 224,
  "class_names": ["..."],
  "in_scale": 0.0,
  "in_zero": 0,
  "out_scale": 0.0,
  "out_zero": 0
}
```

### 3. Run

```bash
python game.py
```

---

## Simulation mode (dev machine)

The game detects missing hardware at startup and falls back gracefully:

| Missing | Fallback |
|---|---|
| `picamzero` | Blank black frames (camera thread still runs) |
| `RPi.GPIO` | Random distances between 5–80 cm |
| `lcd_i2c` | Prints LCD output to the console |

This means you can test the full game loop on a laptop before touching the Pi.

---

## Configuration

All tunable values live in `config.py`. Key settings:

| Key | Default | Description |
|---|---|---|
| `lcd_i2c_address` | `0x27` | I2C address of the LCD |
| `dist_close_max` | `20` cm | Upper bound for "close" zone |
| `dist_middle_max` | `50` cm | Upper bound for "middle" zone |
| `prepare_seconds` | `5` | Countdown duration per round |
| `hold_seconds` | `3` | Hold duration before snapshot |
| `total_rounds` | `5` | Number of rounds per game |
| `pass_threshold` | `3` | Minimum rounds correct to win |
| `emotion_confidence` | `0.50` | Min confidence for emotion prediction |
| `gesture_confidence` | `0.70` | Min confidence for gesture prediction |

---

## For the gesture detection team member

Implement `GestureDetector` in `detector.py`. The stub is already wired into the game — you only need to fill in:

1. `__init__`: initialise `mediapipe.solutions.hands.Hands`
2. `_is_finger_extended(landmarks, tip_idx, pip_idx)`
3. `_is_thumb_extended(landmarks, handedness, threshold)`
4. `_classify_landmarks(landmarks, handedness)` → `(gesture_str, confidence)`
5. `detect(frame_rgb)` → `{"Left": (gesture, conf), "Right": (gesture, conf)}`

Frames are RGB numpy arrays (picamzero format) — no colour conversion needed before passing to MediaPipe.

Gesture rules:
- `thumbs_up` — thumb extended, all other fingers curled
- `thumbs_down` — thumb extended downward (`tip.y > ip.y`), all others curled
- `peace` — index + middle extended, thumb + ring + pinky curled
