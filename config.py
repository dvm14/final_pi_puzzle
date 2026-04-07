"""
config.py — Configuration constants and game options for the Emotion Puzzle Game.
"""

CONFIG = {
    # ------------------------------------------------------------------
    # File Paths
    # ------------------------------------------------------------------
    "emotion_model_path"    : "models/emotionnet_int8.tflite",
    "model_config_path"     : "models/emotion_model_config.json",

    # ------------------------------------------------------------------
    # Camera Settings (picamzero)
    # ------------------------------------------------------------------
    "camera_width"          : 640,
    "camera_height"         : 480,

    # ------------------------------------------------------------------
    # Display Settings (LCD I2C 16x2)
    # ------------------------------------------------------------------
    "lcd_i2c_address"       : 0x27,   # Common default; try 0x3F if 0x27 doesn't work
    "lcd_cols"              : 16,
    "lcd_rows"              : 2,

    # ------------------------------------------------------------------
    # GPIO Pins (BCM Mode) - MUST match your physical wiring
    # ------------------------------------------------------------------
    "left_trig"             : 16,
    "left_echo"             : 20,
    "right_trig"            : 23,
    "right_echo"            : 24,
    "button_pin"            : 21,

    # ------------------------------------------------------------------
    # Game Timing & Flow (Seconds)
    # ------------------------------------------------------------------
    "prepare_seconds"       : 5,      # Time allowed to get into position
    "hold_seconds"          : 3,      # Time required to hold the pose
    "result_display_seconds": 2,      # How long to show pass/fail per round
    "round_start_seconds"   : 2,      # How long to display the target before countdown

    # ------------------------------------------------------------------
    # Game Rules
    # ------------------------------------------------------------------
    "total_rounds"          : 5,
    "pass_threshold"        : 3,      # Minimum successful rounds required to win

    # ------------------------------------------------------------------
    # Detection Thresholds & Sampling
    # ------------------------------------------------------------------
    "emotion_confidence"    : 0.50,   # Minimum confidence for a valid emotion
    "gesture_confidence"    : 0.70,   # Minimum confidence for a valid hand gesture
    "ultrasonic_samples"    : 5,      # Number of pulses to average per distance reading
}

# ---------------------------------------------------------------------------
# Game Target Options
# ---------------------------------------------------------------------------

EMOTION_OPTIONS  = ["Happy", "Surprise", "Disgust"]
GESTURE_OPTIONS  = ["thumbs_up", "peace", "thumbs_down"]

# Left and right hand specific color zones (replaces generic distance options)
LEFT_COLOR_OPTIONS  = ["Pink", "Red"]
RIGHT_COLOR_OPTIONS = ["Blue", "Green"]


# ---------------------------------------------------------------------------
# LCD Display Abbreviations (Strictly limited to fit the 16x2 grid)
# ---------------------------------------------------------------------------

EMOTION_SHORT  = {
    "Happy": "Hap", 
    "Surprise": "Sur", 
    "Disgust": "Dis"
}

GESTURE_SHORT  = {
    "thumbs_up": "T-Up", 
    "peace": "Pce", 
    "thumbs_down": "T-Dn"
}

DISTANCE_SHORT = {
    "Pink": "Pnk", 
    "Red": "Red", 
    "Blue": "Blu", 
    "Green": "Grn", 
    "None": "---"
}


# ---------------------------------------------------------------------------
# Visual UI Theme Constants (Optional)
# ---------------------------------------------------------------------------
# Low-saturation, retro-style hex codes mapped to the logical color triggers.
# Useful if you expand the game to include a web dashboard or external display.
UI_THEME_HEX = {
    "Pink":  "#d4a3a3",  # Muted dusty pink
    "Red":   "#a36b6b",  # Desaturated brick/retro red
    "Blue":  "#899ca1",  # Slate/grey-blue
    "Green": "#9eb09e"   # Soft sage green
}