# 🎮 Emotion Puzzle Game 🧩

A Raspberry Pi-powered spatial puzzle game where the player must match a randomly generated combination of facial expressions, hand gestures, and physical hand positions (color zones) — detected live using a camera and ultrasonic sensors. 

Say goodbye to traditional buttons, and use your body's proprioception to unlock the invisible mechanisms in thin air! 🪄

## 🎯 How to play

The game runs for **5 rounds**. Each round displays a target combination on the LCD screen:

* 📸 **Face** — Happy, Surprise, or Disgust
* 🤚 **Left hand gesture** — Thumbs Up, Peace, or Thumbs Down
* ✋ **Right hand gesture** — Thumbs Up, Peace, or Thumbs Down
* 🌸 **Left hand zone** — Pink (15–25 cm) or Red (35–45 cm)
* 🌊 **Right hand zone** — Blue (15–25 cm) or Green (35–45 cm)

⏳ You have **5 seconds** to get into position, then must **HOLD for 3 seconds**. A snapshot is taken at the end of the hold. 
🏆 **Score ≥ 3/5 = WIN.**

---

## 🛠️ Hardware

| Component | Details |
|---|---|
| **Board** 🍓 | Raspberry Pi 4 or 5 |
| **Camera** 📷 | Pi Camera Module (`picamzero`) |
| **Display** 📺 | 16×2 I2C LCD (`lcd_i2c`, default address `0x27`) |
| **Left Sensor** 📏 | HC-SR04 — TRIG=GPIO16, ECHO=GPIO20 (BCM) |
| **Right Sensor** 📏 | HC-SR04 — TRIG=GPIO23, ECHO=GPIO24 (BCM) |

### 🔌 Wiring Guide

**1. HC-SR04 Ultrasonic Sensors (×2)**

```text
[Left Sensor - Pink/Red Zone]
VCC        → 5V (Pin 2 or 4)
GND        → GND
TRIG       → GPIO 16 (Pin 36)
ECHO       → GPIO 20 (Pin 38)  ⚠️ [Use 1kΩ + 2kΩ voltage divider!]

[Right Sensor - Blue/Green Zone]
VCC        → 5V (Pin 2 or 4)
GND        → GND
TRIG       → GPIO 23 (Pin 16)
ECHO       → GPIO 24 (Pin 18)  ⚠️ [Use 1kΩ + 2kΩ voltage divider!]
```
> ⚠️ **CRITICAL:** The HC-SR04 ECHO pin outputs 5V. You **MUST** use a voltage divider to bring it down to 3.3V before connecting it to the Pi GPIO to prevent hardware damage.

**2. Start Button**
```text
One leg    → GPIO 21 (Pin 40)
Other leg  → GND
```
*(The button uses the Pi's internal pull-up resistor — no external resistor needed. Press = LOW signal.)*

**3. 16×2 I2C LCD**
```text
VCC     → 5V
GND     → GND
SDA     → GPIO 2 / SDA (Pin 3)
SCL     → GPIO 3 / SCL (Pin 5)
```
*(If the LCD doesn't show anything, try changing the I2C address to `0x3F` in `config.py`)*

---

## 📂 Project Structure

```text
final_pi_puzzle/
├── 🎮 game.py          # Entry point — main game loop & state machine
├── 👁️ detector.py      # EmotionDetector & GestureDetector logic
├── 📡 sensor.py        # UltrasonicSensor class mapped to color zones
├── 📺 display.py       # LCDDisplay class (16×2 I2C)
├── 🧠 game_logic.py    # RoundTarget, DetectionResult, scoring, state enum
├── ⚙️ config.py        # All configuration constants & UI color hex codes
├── 📁 models/
│   ├── emotionnet_int8.tflite   # INT8 quantized EfficientNetB0
│   └── emotion_model_config.json # img_size, class_names, quant params
└── 📄 requirements.txt
```

---

## 🚀 Setup & Installation

### 1. Install dependencies

On the Raspberry Pi:
```bash
pip install -r requirements.txt
```

On a dev machine (for simulation/testing):
```bash
pip install tflite-runtime numpy opencv-python mediapipe
# lcd_i2c, RPi.GPIO, picamzero are Pi-only — skip them for local testing
```

### 2. Add the ML model files

Ensure your trained model files are correctly placed in the `models/` directory:
* `models/emotionnet_int8.tflite`
* `models/emotion_model_config.json`

### 3. Run the Game

```bash
python game.py
```

---

## 💻 Simulation Mode (Dev Machine Friendly)

The game detects missing hardware at startup and falls back gracefully so you can test the logic on your laptop:

| Missing Hardware | Fallback Behavior 🛡️ |
|---|---|
| `picamzero` | Generates blank black frames (camera thread still runs smoothly). |
| `RPi.GPIO` | Simulates distance data, randomly outputting Pink/Red/Blue/Green. |
| `lcd_i2c` | Prints formatted LCD ASCII UI directly to the terminal console. |

---

## ⚙️ Configuration (`config.py`)

All tunable values and game aesthetics live in `config.py`. Key settings include:
* **Zone Thresholds:** Adjust the physical cm distance for near/far zones directly in `sensor.py`.
* **Game Flow:** Tweak `prepare_seconds`, `hold_seconds`, and `pass_threshold`.
* **UI Theme:** `UI_THEME_HEX` contains the low-saturation, retro-style hex codes corresponding to the physical zones (Dusty Pink, Retro Red, Slate Blue, Sage Green) for future dashboard expansions.

---

## 👩‍💻 For the Gesture Detection Team Member (Diya)

Implement the `GestureDetector` stub inside `detector.py`. The system is already fully wired into the main loop — you only need to fill in the MediaPipe logic:

1.  `__init__`: initialize `mediapipe.solutions.hands.Hands`
2.  `_is_finger_extended(landmarks, tip_idx, pip_idx)`
3.  `_is_thumb_extended(landmarks, handedness, threshold)`
4.  `_classify_landmarks(landmarks, handedness)` → `(gesture_str, confidence)`
5.  `detect(frame_rgb)` → `{"Left": (gesture, conf), "Right": (gesture, conf)}`

*Input frames are RGB numpy arrays (`picamzero` format) — no color conversion needed before passing to MediaPipe.*

**Gesture Rules:**
* 👍 `thumbs_up` — thumb extended, all other fingers curled
* 👎 `thumbs_down` — thumb extended downward (`tip.y > ip.y`), all others curled
* ✌️ `peace` — index + middle extended, thumb + ring + pinky curled