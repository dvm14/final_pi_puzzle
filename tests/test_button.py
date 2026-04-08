"""
test_button.py — Confirm the button on GPIO21 is wired and working.

Run:  python test_button.py
Press the button a few times. You should see "Button pressed!" each time.
Press Ctrl+C to quit.
"""

import time
import RPi.GPIO as GPIO
from config import CONFIG

PIN = CONFIG["button_pin"]

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print(f"Listening on GPIO{PIN}. Press the button (Ctrl+C to quit)...")

try:
    while True:
        if GPIO.input(PIN) == GPIO.LOW:
            print("Button pressed!")
            time.sleep(0.3)   # debounce
        time.sleep(0.05)
except KeyboardInterrupt:
    print("Done.")
finally:
    GPIO.cleanup()
