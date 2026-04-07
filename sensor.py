"""
sensor.py — UltrasonicSensor driver with color zone logic and simulation fallback.
Button class for GPIO button handling.

If RPi.GPIO is not importable (e.g., running on a dev machine without hardware),
sensor readings and button presses are simulated.
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


def cm_to_color_zone(cm, hand_side):
    """
    Convert distance in centimeters to the specific color zones 
    designated for the left or right hand.
    """
    if cm is None:
        return "None"

    # Define physical distance thresholds for near and far zones (in cm)
    near_min, near_max = 15.0, 25.0  # Near field trigger zone
    far_min, far_max = 35.0, 45.0    # Far field trigger zone

    if hand_side == 'left':
        if near_min <= cm <= near_max:
            return "Pink"
        elif far_min <= cm <= far_max:
            return "Red"
            
    elif hand_side == 'right':
        if near_min <= cm <= near_max:
            return "Blue"
        elif far_min <= cm <= far_max:
            return "Green"

    # Return "None" if the distance falls in the dead zone or is completely out of range
    return "None"


class UltrasonicSensor:
    """
    Manages one HC-SR04 ultrasonic sensor with logic tied to a specific hand side.
    """
    # Class-level flag to ensure GPIO.setmode is only called once globally
    _gpio_initialised = False 

    def __init__(self, trig_pin, echo_pin, config, hand_side='left'):
        """
        Initialize the sensor with specific pins and determine which hand it tracks.
        """
        self.trig = trig_pin
        self.echo = echo_pin
        self._config = config
        self.hand_side = hand_side 
        self._simulated = not _GPIO_AVAILABLE

        if not self._simulated:
            self._setup_gpio()

    def _setup_gpio(self):
        """Set up GPIO pins for the sensor."""
        if not UltrasonicSensor._gpio_initialised:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            UltrasonicSensor._gpio_initialised = True

        GPIO.setup(self.trig, GPIO.OUT)
        GPIO.setup(self.echo, GPIO.IN)
        
        # Ensure Trig pin is set to low initially to avoid false pulses
        GPIO.output(self.trig, False)
        time.sleep(0.05)  # Allow sensor time to settle

    def cleanup(self):
        """Release GPIO pins (should be called during system shutdown)."""
        if not self._simulated:
            GPIO.cleanup([self.trig, self.echo])

    def _read_once(self):
        """
        Fire one ultrasonic pulse and return the distance in cm,
        or return None if the measurement times out.
        """
        if self._simulated:
            return random.uniform(5, 80)

        # Send a 10-microsecond pulse to trigger the sensor
        GPIO.output(self.trig, True)
        time.sleep(0.00001)
        GPIO.output(self.trig, False)

        timeout = time.monotonic() + 0.04  # 40 ms max wait time
        
        # Wait for echo pin to go high
        pulse_start = time.monotonic()
        while GPIO.input(self.echo) == 0:
            pulse_start = time.monotonic()
            if pulse_start > timeout:
                return None

        # Wait for echo pin to go low
        pulse_end = time.monotonic()
        while GPIO.input(self.echo) == 1:
            pulse_end = time.monotonic()
            if pulse_end > timeout:
                return None

        # Calculate distance based on the speed of sound (approx. 34300 cm/s)
        # Divide by 2 because the sound wave travels to the object and back
        duration = pulse_end - pulse_start
        distance = (duration * 34300) / 2  
        return round(distance, 1)

    def read_cm(self):
        """
        Return the average of N valid readings to reduce noise and bounce.
        N is determined by the config["ultrasonic_samples"] parameter.
        """
        n = self._config["ultrasonic_samples"]
        readings = []
        for _ in range(n):
            val = self._read_once()
            if val is not None:
                readings.append(val)
            time.sleep(0.01)  # Small delay between pulses to prevent sound wave crosstalk

        if not readings:
            return None
            
        # Return the averaged distance rounded to 1 decimal place
        return round(sum(readings) / len(readings), 1)

    def read_zone(self):
        """
        Get the averaged distance and map it to the hand-specific color zone.
        """
        return cm_to_color_zone(self.read_cm(), self.hand_side)


class Button:
    """
    A momentary push button wired to a GPIO pin with an internal pull-up resistor.
    The button is considered pressed when the pin reads LOW.
    """

    def __init__(self, pin):
        """Initialize the button."""
        self._pin = pin
        self._simulated = not _GPIO_AVAILABLE

        if not self._simulated:
            # Reuse the shared GPIO initialization guard
            if not UltrasonicSensor._gpio_initialised:
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                UltrasonicSensor._gpio_initialised = True
                
            # Set up the pin as an input with an internal pull-up resistor enabled
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def is_pressed(self):
        """Return True if the physical button is currently held down."""
        if self._simulated:
            return False
            
        # Button is pressed when the circuit is closed, connecting to GND (LOW)
        return GPIO.input(self._pin) == GPIO.LOW

    def cleanup(self):
        """Release the GPIO pin for the button."""
        if not self._simulated:
            GPIO.cleanup([self._pin])