"""
test_sensors.py — Confirm both HC-SR04 sensors are reading distances correctly.

Run:  python test_sensors.py
Move your hands closer and farther away. You should see live distance readings
and zone labels. Press Ctrl+C to quit.
"""

import time
from gpiozero import DistanceSensor
from config import CONFIG

left_sensor  = DistanceSensor(trigger=CONFIG["left_trig"],  echo=CONFIG["left_echo"],  max_distance=4.0)
right_sensor = DistanceSensor(trigger=CONFIG["right_trig"], echo=CONFIG["right_echo"], max_distance=4.0)


def zone(cm):
    if cm is None:
        return "none"
    if cm <= CONFIG["dist_close_max"]:
        return "close"
    if cm <= CONFIG["dist_middle_max"]:
        return "middle"
    return "far"


print("Reading sensors (Ctrl+C to quit)...\n")

try:
    while True:
        l_cm = round(left_sensor.distance  * 100, 1)
        r_cm = round(right_sensor.distance * 100, 1)
        print(f"LEFT:  {l_cm:>6} cm  →  {zone(l_cm):<8}  |  "
              f"RIGHT: {r_cm:>6} cm  →  {zone(r_cm)}")
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\nDone.")
