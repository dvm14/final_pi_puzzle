# Emotion Puzzle Game — Project Plan

## Phase 1: Scaffold & Config
- [ ] Create project folder structure (`game/`, `models/`, `assets/`)
- [ ] Write `config.py` with full CONFIG dict and all game option lists
- [ ] Write `requirements.txt`
- [ ] Write `README.md` with setup and wiring instructions

## Phase 2: Hardware Modules
- [ ] Write `sensor.py` — UltrasonicSensor class
  - Single reading, averaged reading, simulation fallback
  - `cm_to_zone()` helper using CONFIG thresholds
- [ ] Smoke test sensor on Pi: print distance readings every second

## Phase 3: Detection Modules
- [ ] Write `detector.py` — EmotionDetector class
  - Load TFLite INT8 model + model_config.json
  - `predict(frame)` → returns (label, confidence) or (None, 0.0)
  - Only return label if it's in EMOTION_OPTIONS
- [ ] Write `detector.py` — GestureDetector class
  - MediaPipe Hands setup (max 2 hands)
  - `classify_landmarks(hand_landmarks, handedness)` → gesture string
  - Finger extension logic for thumbs_up / peace / thumbs_down
  - `detect(frame)` → returns dict: `{"Left": (gesture, conf), "Right": (gesture, conf)}`
- [ ] Smoke test both detectors with a webcam feed, print predictions

## Phase 4: Display Module
- [ ] Write `display.py` — LCDDisplay class
  - Init luma.lcd device (ST7789 default) with OpenCV fallback
  - `draw_intro()` — title screen
  - `draw_round_start(round_num, target)` — show target combination
  - `draw_countdown(target, seconds_left)` — target + large countdown
  - `draw_hold(seconds_left, total)` — HOLD! + progress bar
  - `draw_result(passed, target, detection)` — per-condition tick/cross
  - `draw_final_score(score, round_results)` — final screen
  - All drawing uses Pillow, pushed to LCD via `device.display(image)`
- [ ] Test display standalone: cycle through all screens with dummy data

## Phase 5: Game Logic
- [ ] Write `game_logic.py`
  - `RoundTarget` dataclass + `random_target()` factory
  - `DetectionResult` dataclass + `matches(target, config)` method
  - `GameState` enum: INTRO, ROUND_START, COUNTDOWN, HOLD, DETECT, RESULT, FINAL_SCORE
  - `RoundRecord` dataclass: target, detection, passed (for final score screen)

## Phase 6: Main Game Loop
- [ ] Write `game.py`
  - Camera background thread (stores latest frame with Lock)
  - Sensor background thread (polls every 200ms, stores latest readings)
  - Main loop: state machine driving display + detection
  - COUNTDOWN state: update display ~15 FPS, check time elapsed
  - HOLD state: display progress bar, trigger DETECT at end
  - DETECT state: grab latest frame, run EmotionDetector + GestureDetector + sensors
  - RESULT state: show pass/fail for 2 seconds
  - FINAL_SCORE state: show score, wait for keypress to restart
  - Clean GPIO shutdown in try/finally

## Phase 7: Integration Testing
- [ ] Test full game loop in simulation mode on dev machine
- [ ] Test on Pi with camera only (no LCD/sensors) using cv2.imshow fallback
- [ ] Test with full hardware: camera + sensors + LCD
- [ ] Tune distance thresholds for actual play distance
- [ ] Tune emotion/gesture confidence thresholds

## Phase 8: Polish
- [ ] Add a buzzer/beep at round start and on pass/fail (optional GPIO buzzer)
- [ ] Add a best-of-3 game mode option in CONFIG
- [ ] Add logging to a `game_log.csv` (timestamp, round, target, detected, passed)
- [ ] Consider adding a "practice mode" that shows live detections without scoring

---

## Wiring Reference

### HC-SR04 Ultrasonic Sensor (×2)

```
Sensor Pin → Pi Pin
VCC        → 5V (Pin 2 or 4)
GND        → GND (Pin 6, 9, 14, etc.)
TRIG       → GPIO23 (Pin 16) — left sensor
ECHO       → GPIO24 (Pin 18) — left sensor  [use voltage divider: 1kΩ + 2kΩ]
TRIG       → GPIO27 (Pin 13) — right sensor
ECHO       → GPIO22 (Pin 15) — right sensor [use voltage divider: 1kΩ + 2kΩ]
```

⚠️ The HC-SR04 ECHO pin outputs 5V — use a voltage divider to bring it to 3.3V for the Pi GPIO input.

### SPI TFT LCD (ST7789 example)

```
LCD Pin → Pi Pin
VCC     → 3.3V (Pin 1)
GND     → GND
SCL     → GPIO11 / SPI0_CLK (Pin 23)
SDA     → GPIO10 / SPI0_MOSI (Pin 19)
RES     → GPIO25 (Pin 22)
DC      → GPIO24 (Pin 18)  ← adjust if clashes with sensor
CS      → GPIO8  / SPI0_CE0 (Pin 24)
BL      → 3.3V or GPIO (for brightness control)
```

---

## Notes for Claude Code

- Start by reading `CLAUDE.md` for full context before writing any code
- Build in the order listed in Phase 1–6 above
- Run smoke tests after Phase 2 and Phase 3 before proceeding
- The simulation fallbacks (no GPIO, no LCD) are critical — test on laptop first
- Keep all magic numbers in `config.py` — nothing hardcoded in other files
- Use `time.monotonic()` for all timing
