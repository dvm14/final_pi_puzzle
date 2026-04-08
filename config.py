CONFIG = {
    # Paths
    "emotion_model_path" : "models/emotionnet_int8.tflite",
    "model_config_path"  : "models/emotion_model_config.json",
    "voice_model_path"   : "models/en_US-libritts-high.onnx",
    "voice_config_path"  : "models/en_US-libritts-high.onnx.json",

    # Camera (picamzero)
    "camera_width"       : 640,
    "camera_height"      : 480,

    # LCD I2C 16x2
    "lcd_i2c_address"    : 39,    # 0x27 in decimal
    "lcd_cols"           : 16,
    "lcd_rows"           : 2,

    # GPIO pins (BCM)
    "left_trig"          : 16,
    "left_echo"          : 20,
    "right_trig"         : 23,
    "right_echo"         : 24,
    "button_pin"         : 21,

    # Distance threshold (cm) — below = first color, above = second color
    "dist_threshold"     : 20,

    # Timing (seconds)
    "prepare_seconds"    : 5,
    "hold_seconds"       : 3,
    "result_display_seconds": 2,
    "round_start_seconds": 2,

    # Game
    "total_rounds"       : 3,
    "pass_threshold"     : 2,

    # Detection thresholds
    "emotion_confidence" : 0.20,
    "gesture_confidence" : 0.70,
    "ultrasonic_samples" : 5,
}

EMOTION_OPTIONS      = ["Happy", "Surprise", "Disgust"]
GESTURE_OPTIONS      = ["thumbs_up", "peace", "thumbs_down"]
LEFT_COLOR_OPTIONS   = ["Pink", "Red"]    # left sensor:  close → Pink, far → Red
RIGHT_COLOR_OPTIONS  = ["Blue", "Green"]  # right sensor: close → Blue, far → Green

EMOTION_SHORT = {"Happy": "Hap", "Surprise": "Sur", "Disgust": "Dis"}
GESTURE_SHORT = {"thumbs_up": "T-Up", "peace": "Pce", "thumbs_down": "T-Dn"}
