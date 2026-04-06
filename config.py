CONFIG = {
    # Paths
    "emotion_model_path"    : "models/emotionnet_int8.tflite",
    "model_config_path"     : "models/emotion_model_config.json",

    # Camera (picamzero)
    "camera_width"          : 640,
    "camera_height"         : 480,

    # LCD I2C 16x2
    "lcd_i2c_address"       : 0x27,   # common default; try 0x3F if 0x27 doesn't work
    "lcd_cols"              : 16,
    "lcd_rows"              : 2,

    # GPIO pins (BCM)
    "left_trig"             : 16,
    "left_echo"             : 20,
    "right_trig"            : 23,
    "right_echo"            : 24,
    "button_pin"            : 21,

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

EMOTION_OPTIONS  = ["Happy", "Surprise", "Disgust"]
GESTURE_OPTIONS  = ["thumbs_up", "peace", "thumbs_down"]
DISTANCE_OPTIONS = ["close", "middle", "far"]

# Short labels for 16x2 LCD display
EMOTION_SHORT  = {"Happy": "Hap", "Surprise": "Sur", "Disgust": "Dis"}
GESTURE_SHORT  = {"thumbs_up": "T-Up", "peace": "Pce", "thumbs_down": "T-Dn"}
DISTANCE_SHORT = {"close": "Cls", "middle": "Mid", "far": "Far"}
