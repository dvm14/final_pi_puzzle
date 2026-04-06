"""
display.py — LCDDisplay

Drives a 16×2 I2C LCD (lcd_i2c library) with a console fallback
for dev machines where the hardware is not available.

Each draw_* method formats the game state into two 16-character strings
and sends them to the LCD (or prints them to stdout in simulation).

16×2 layout key
  Line 0 (top)  : primary info
  Line 1 (bottom): secondary info / countdown / progress bar
"""

import warnings
import time

try:
    from lcd_i2c import LCD_I2C
    _LCD_AVAILABLE = True
except ImportError:
    _LCD_AVAILABLE = False
    warnings.warn("[display] lcd_i2c not available — printing to console instead.")

from config import (
    CONFIG,
    EMOTION_SHORT, GESTURE_SHORT, DISTANCE_SHORT,
)


def _pad(text, width=16):
    """Left-justify and pad/truncate to exactly `width` characters."""
    return text[:width].ljust(width)


def _progress_bar(fraction, width=10):
    """Return a simple ASCII progress bar string of given width."""
    filled = int(round(fraction * width))
    filled = max(0, min(width, filled))
    return "#" * filled + "-" * (width - filled)


class LCDDisplay:
    """
    Manages the 16×2 I2C LCD.  Falls back to console output on dev machines.

    Parameters
    ----------
    config : dict  CONFIG dict
    """

    def __init__(self, config=CONFIG):
        self._cols = config["lcd_cols"]   # 16
        self._rows = config["lcd_rows"]   # 2
        self._lcd  = None

        if _LCD_AVAILABLE:
            self._lcd = LCD_I2C(config["lcd_i2c_address"], config["lcd_cols"],
                                config["lcd_rows"])
            self._lcd.begin()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _write(self, line0, line1=""):
        """
        Display two lines on the LCD (or print to console).

        Parameters are automatically padded/truncated to 16 chars.
        """
        l0 = _pad(line0, self._cols)
        l1 = _pad(line1, self._cols)

        if self._lcd is not None:
            self._lcd.clear()
            self._lcd.print(l0)             # writes to line 0
            self._lcd.setCursor(0, 1)
            self._lcd.print(l1)             # writes to line 1
        else:
            # Console fallback — draw a simple box
            border = "+" + "-" * self._cols + "+"
            print(border)
            print(f"|{l0}|")
            print(f"|{l1}|")
            print(border)

    # ------------------------------------------------------------------
    # State screens
    # ------------------------------------------------------------------

    def draw_intro(self):
        """
        +----------------+
        |Emotion Puzzle  |
        |Key to start... |
        +----------------+
        """
        self._write("Emotion Puzzle", "Key to start...")

    def draw_round_start(self, round_num, target):
        """
        Show round number and target (abbreviated to fit 16 chars).

        Line 0: R1/5 E:Hap L:T-Up
        Line 1: R:Pce LD:Cls RD:Fr

        Parameters
        ----------
        round_num : int (1-based)
        target    : RoundTarget
        """
        e  = EMOTION_SHORT.get(target.emotion, target.emotion[:3])
        lg = GESTURE_SHORT.get(target.left_gesture,  target.left_gesture[:4])
        rg = GESTURE_SHORT.get(target.right_gesture, target.right_gesture[:4])
        ld = DISTANCE_SHORT.get(target.left_distance,  target.left_distance[:3])
        rd = DISTANCE_SHORT.get(target.right_distance, target.right_distance[:3])

        total = CONFIG["total_rounds"]
        line0 = f"R{round_num}/{total} E:{e} L:{lg}"
        line1 = f"R:{rg} LD:{ld} RD:{rd}"
        self._write(line0, line1)

    def draw_countdown(self, target, seconds_left, round_num):
        """
        Line 0: abbreviated target (same as round_start line 0)
        Line 1: Get ready!  3.2s

        Parameters
        ----------
        seconds_left : float
        """
        e  = EMOTION_SHORT.get(target.emotion, target.emotion[:3])
        lg = GESTURE_SHORT.get(target.left_gesture,  target.left_gesture[:4])
        total = CONFIG["total_rounds"]

        line0 = f"R{round_num}/{total} E:{e} L:{lg}"
        line1 = f"Ready! {seconds_left:4.1f}s"
        self._write(line0, line1)

    def draw_hold(self, seconds_left, total_hold):
        """
        Line 0: HOLD!
        Line 1: [########--] 1.2s

        Parameters
        ----------
        seconds_left : float  time remaining
        total_hold   : float  CONFIG["hold_seconds"]
        """
        fraction_done = 1.0 - (seconds_left / total_hold)
        bar = _progress_bar(fraction_done, width=8)
        time_str = f"{seconds_left:.1f}s"
        line1 = f"[{bar}]{time_str:>5}"
        self._write("HOLD!", line1)

    def draw_result(self, passed, target, detection):
        """
        Line 0: PASS! or FAIL
        Line 1: tick/cross per condition (E L R LD RD)

        Parameters
        ----------
        passed    : bool
        target    : RoundTarget
        detection : DetectionResult
        """
        header = "** PASS! **" if passed else "** FAIL  **"

        def mark(t, d):
            return "O" if t == d else "X"

        e_m  = mark(target.emotion,        detection.emotion)
        lg_m = mark(target.left_gesture,   detection.left_gesture)
        rg_m = mark(target.right_gesture,  detection.right_gesture)
        ld_m = mark(target.left_distance,  detection.left_distance)
        rd_m = mark(target.right_distance, detection.right_distance)

        line1 = f"E:{e_m} L:{lg_m} R:{rg_m} D:{ld_m}{rd_m}"
        self._write(header, line1)

    def draw_final_score(self, score, round_results):
        """
        Line 0: Score: X/5 WIN  (or LOSE)
        Line 1: R1:O R2:X R3:O ...

        Parameters
        ----------
        score         : int
        round_results : list[bool]
        """
        total     = CONFIG["total_rounds"]
        threshold = CONFIG["pass_threshold"]
        outcome   = "WIN!" if score >= threshold else "LOSE"
        line0 = f"Score:{score}/{total} {outcome}"

        marks = " ".join(
            f"R{i+1}:{'O' if ok else 'X'}" for i, ok in enumerate(round_results)
        )
        self._write(line0, marks)

    def draw_ready_prompt(self):
        """
        +----------------+
        |Are you ready?  |
        |Press button... |
        +----------------+
        """
        self._write("Are you ready?", "Press button...")

    def draw_show_score_prompt(self):
        """
        +----------------+
        |Game over!      |
        |Btn: show score |
        +----------------+
        """
        self._write("Game over!", "Btn: show score")

    def draw_play_again_prompt(self):
        """
        +----------------+
        |Play again?     |
        |Press button... |
        +----------------+
        """
        self._write("Play again?", "Press button...")

    def draw_message(self, line0, line1=""):
        """Generic two-line message (used for errors or transient states)."""
        self._write(line0, line1)

    def close(self):
        """Clean up the LCD."""
        if self._lcd is not None:
            try:
                self._lcd.clear()
                self._lcd.noBacklight()
            except Exception:
                pass
