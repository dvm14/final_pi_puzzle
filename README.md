# Pi Puzzle Game

A Raspberry Pi game where the player matches a randomly generated combination of facial expression, hand gestures, and sensor-based color zones each round. Score 2 or more out of 3 rounds to win.

## How to play

Each round shows and speaks a target combination:

| Input | Options |
|---|---|
| Face | Happy, Surprise, Disgust |
| Left hand gesture | Thumbs Up, Peace, Thumbs Down |
| Right hand gesture | Thumbs Up, Peace, Thumbs Down |
| Left color (distance) | Pink (close ≤ 20 cm) / Red (far > 20 cm) |
| Right color (distance) | Blue (close ≤ 20 cm) / Green (far > 20 cm) |

You have **5 seconds** to get into position, then **hold for 3 seconds**. A snapshot is taken at the end of the hold. Score ≥ 2/3 = WIN.

---

## Hardware

| Component | Details |
|---|---|
| Board | Raspberry Pi 4 or 5 |
| Camera | Pi Camera Module (picamzero) |
| Display | 16×2 I2C LCD (`lcd_i2c`, address `39` / 0x27) |
| Left ultrasonic | HC-SR04 — TRIG=GPIO16, ECHO=GPIO20 |
| Right ultrasonic | HC-SR04 — TRIG=GPIO23, ECHO=GPIO24 |
| Button | Momentary push button — GPIO21 |
| Speaker | USB audio device (device index 1, 48000 Hz) |

### Wiring

**HC-SR04 ultrasonic sensors (×2)**
```
Sensor Pin → Pi Pin
VCC        → 5V
GND        → GND
TRIG       → GPIO16 (Pin 36)  ← left sensor
ECHO       → GPIO20 (Pin 38)  ← left sensor  [voltage divider: 1kΩ + 2kΩ]
TRIG       → GPIO23 (Pin 16)  ← right sensor
ECHO       → GPIO24 (Pin 18)  ← right sensor [voltage divider: 1kΩ + 2kΩ]
```
> ⚠️ HC-SR04 ECHO outputs 5 V — use a voltage divider before connecting to the Pi.

**16×2 I2C LCD**
```
LCD Pin → Pi Pin
VCC     → 5V
GND     → GND
SDA     → GPIO2 / SDA (Pin 3)
SCL     → GPIO3 / SCL (Pin 5)
```

**Button**
```
One leg → GPIO21 (Pin 40)
Other   → GND
```
Uses internal pull-up — no external resistor needed.

---

## Project structure

```
final_pi_puzzle/
├── game.py        # Main game loop (entry point)
├── display.py     # LCDDisplay class
├── config.py      # All configuration and game options
├── models/
│   ├── emotionnet_int8.tflite
│   ├── emotion_model_config.json
│   ├── en_US-libritts-high.onnx
│   └── en_US-libritts-high.onnx.json
├── tests/
│   ├── test_button.py    # Verify button wiring
│   ├── test_lcd.py       # Verify LCD display
│   ├── test_sensors.py   # Verify both ultrasonic sensors
│   ├── test_camera.py    # Verify camera + emotion model
│   └── test_speaker.py   # Verify Piper TTS + speaker
└── README.md
```

---

## Setup

### 1. Enable I2C on the Pi
```bash
sudo raspi-config   # Interface Options → I2C → Enable
i2cdetect -y 1      # Confirm LCD shows up at address 0x27 (= 39)
```

### 2. Install dependencies
```bash
pip install picamzero gpiozero lcd_i2c piper-tts sounddevice numpy opencv-python tflite-runtime
```
#### Models
Download voice and emotion models before running:
```bash
wget -O models/en_US-lessac-medium.onnx \
  'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx?download=true'
wget -O models/en_US-lessac-medium.onnx.json \
  'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json?download=true'
# Copy your emotionnet_int8.tflite into models/
```

### 3. Test each component
Run these from the `final_pi_puzzle/` directory before starting the full game:
```bash
python tests/test_button.py     # press button → "Button pressed!" prints
python tests/test_lcd.py        # messages appear on LCD
python tests/test_sensors.py    # distances update as you move your hands
python tests/test_camera.py     # emotion label prints for each snapshot
python tests/test_speaker.py    # three phrases spoken through the speaker
```

### 4. Run the game
```bash
python game.py
```

---

## Configuration

All tunable values are in `config.py`:

| Key | Default | Description |
|---|---|---|
| `dist_threshold` | `20` cm | Below = Pink/Blue, above = Red/Green |
| `prepare_seconds` | `5` | Countdown duration per round |
| `hold_seconds` | `3` | Hold duration before snapshot |
| `total_rounds` | `3` | Rounds per game |
| `pass_threshold` | `2` | Minimum rounds correct to win |
| `emotion_confidence` | `0.20` | Min confidence for emotion prediction |

---

## Gesture detection

`detect_gestures()` in `game.py` is currently a stub — it always returns `None` for both hands. Replace it with the real MediaPipe implementation when ready. The rest of the game will work without any other changes.