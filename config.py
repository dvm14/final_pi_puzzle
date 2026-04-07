"""
config.py — Configuration constants and game options for the Emotion Puzzle Game.

This file acts as the single source of truth for all magic numbers, pin layouts, 
and game rules. Keeping them here allows you to easily tweak the gameplay 
without having to search through the core logic files.
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
    # GPIO Pins (BCM Mode) - MUST match your physical wiring!
    # ------------------------------------------------------------------
    "left_trig"             : 16,
    "left_echo"             : 20,
    "right_trig"            : 23,
    "right_echo"            : 24,
    "button_pin"            : 21,

    # ------------------------------------------------------------------
    # Game Timing & Flow (Seconds)
    # ------------------------------------------------------------------
    "prepare_seconds"       : 5,      # Time allowed for the player to get into position
    "hold_seconds"          : 3,      # Time required to steadily hold the pose
    "result_display_seconds": 2,      # How long to show the pass/fail result per round
    
    # Increased from 2 to 5 to allow the TTS (Text-to-Speech) engine 
    # enough time to finish reading the instructions before the countdown starts.
    "round_start_seconds"   : 5,      

    # ------------------------------------------------------------------
    # Game Rules
    # ------------------------------------------------------------------
    "total_rounds"          : 5,
    "pass_threshold"        : 3,      # Minimum successful rounds required to win the game

    # ------------------------------------------------------------------
    # Detection Thresholds & Sampling
    # ------------------------------------------------------------------
    "emotion_confidence"    : 0.50,   # Minimum confidence for a valid AI emotion detection
    "gesture_confidence"    : 0.70,   # Minimum confidence for a valid hand gesture
    "ultrasonic_samples"    : 5,      # Number of pulses to average per distance reading (reduces noise)
}

# ---------------------------------------------------------------------------
# Game Target Options
# ---------------------------------------------------------------------------
# The system randomly selects one item from each of these lists to generate a round's target.

EMOTION_OPTIONS  = ["Happy", "Surprise", "Disgust"]
GESTURE_OPTIONS  = ["thumbs_up", "peace", "thumbs_down"]

# Left and right hand specific color zones (replaces generic distance options)
LEFT_COLOR_OPTIONS  = ["Pink", "Red"]
RIGHT_COLOR_OPTIONS = ["Blue", "Green"]


# ---------------------------------------------------------------------------
# LCD Display Abbreviations
# ---------------------------------------------------------------------------
# Because the LCD only has 16 characters per row, we must strictly abbreviate
# the targets so they don't overflow and break the UI.

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
# Visual UI Theme Constants (Optional / For Future Use)
# ---------------------------------------------------------------------------
# Low-saturation, retro-style hex codes mapped to the logical color triggers.
# These can be used if you expand the game to include a web dashboard or external monitor.
UI_THEME_HEX = {
    "Pink":  "#d4a3a3",  # Muted dusty pink
    "Red":   "#a36b6b",  # Desaturated brick/retro red
    "Blue":  "#899ca1",  # Slate/grey-blue
    "Green": "#9eb09e"   # Soft sage green
}