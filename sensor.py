"""
UltrasonicSensor — HC-SR04 driver with simulation fallback.

If RPi.GPIO is not importable, readings are simulated with random values.
"""

import time
import random
import warnings

try:
    import RPi.GPIO as GPIO
    _GPIO_AVAILABLE = True
except ImportError:
    _GPIO_AVAILABLE = False
    warnings.warn("[sensor] RPi.GPIO not available — simulating ultrasonic sensors.")


def cm_to_zone(cm, config):
    """Convert a distance in cm to a zone string using CONFIG thresholds."""
    if cm is None:
        return None
    if cm <= config["dist_close_max"]:
        return "close"
    if cm <= config["dist_middle_max"]:
        return "middle"
    return "far"


class UltrasonicSensor:
    """
    Manages one HC-SR04 sensor.

    Parameters
    ----------
    trig_pin : int  BCM pin number for TRIG
    echo_pin : int  BCM pin number for ECHO
    config   : dict CONFIG dict (for thresholds and sample count)
    """

    _gpio_initialised = False  # class-level flag so GPIO.setmode is called once

    def __init__(self, trig_pin, echo_pin, config):
        self.trig = trig_pin
        self.echo = echo_pin
        self._config = config
        self._simulated = not _GPIO_AVAILABLE

        if not self._simulated:
            self._setup_gpio()

    # ------------------------------------------------------------------
    # GPIO setup
    # ------------------------------------------------------------------

    def _setup_gpio(self):
        if not UltrasonicSensor._gpio_initialised:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            UltrasonicSensor._gpio_initialised = True

        GPIO.setup(self.trig, GPIO.OUT)
        GPIO.setup(self.echo, GPIO.IN)
        GPIO.output(self.trig, False)
        time.sleep(0.05)  # let sensor settle

    def cleanup(self):
        """Release GPIO pins (call from game.py's finally block)."""
        if not self._simulated:
            GPIO.cleanup([self.trig, self.echo])

    # ------------------------------------------------------------------
    # Single reading
    # ------------------------------------------------------------------

    def _read_once(self):
        """
        Fire one ultrasonic pulse and return the distance in cm,
        or None if the measurement times out.
        """
        if self._simulated:
            return random.uniform(5, 80)

        # Send 10 µs pulse
        GPIO.output(self.trig, True)
        time.sleep(0.00001)
        GPIO.output(self.trig, False)

        timeout = time.monotonic() + 0.04  # 40 ms max wait

        # Wait for echo to go high
        pulse_start = time.monotonic()
        while GPIO.input(self.echo) == 0:
            pulse_start = time.monotonic()
            if pulse_start > timeout:
                return None

        # Wait for echo to go low
        pulse_end = time.monotonic()
        while GPIO.input(self.echo) == 1:
            pulse_end = time.monotonic()
            if pulse_end > timeout:
                return None

        duration = pulse_end - pulse_start
        distance = (duration * 34300) / 2  # speed of sound ≈ 343 m/s
        return round(distance, 1)

    # ------------------------------------------------------------------
    # Averaged reading
    # ------------------------------------------------------------------

    def read_cm(self):
        """
        Return the average of N valid readings (N = config["ultrasonic_samples"]).
        Returns None if no valid reading could be obtained.
        """
        n = self._config["ultrasonic_samples"]
        readings = []
        for _ in range(n):
            val = self._read_once()
            if val is not None:
                readings.append(val)
            time.sleep(0.01)  # small gap between pulses

        if not readings:
            return None
        return round(sum(readings) / len(readings), 1)

    def read_zone(self):
        """Return the distance zone string ('close', 'middle', 'far') or None."""
        return cm_to_zone(self.read_cm(), self._config)
