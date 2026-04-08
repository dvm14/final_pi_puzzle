"""
display.py — LCDDisplay for 16x2 I2C LCD (lcd_i2c library).

Confirmed working API:
  LCD_I2C(address, cols, rows)
  lcd.backlight.on()
  lcd.blink.off()
  lcd.clear()
  lcd.cursor.setPos(row, col)   ← row first, then col
  lcd.write_text(text)
"""

from lcd_i2c import LCD_I2C
from config import CONFIG, EMOTION_SHORT, GESTURE_SHORT


def _pad(text, width=16):
    """Left-justify and pad/truncate to exactly `width` characters."""
    return text[:width].ljust(width)


class LCDDisplay:

    def __init__(self, config=CONFIG):
        self._cols = config["lcd_cols"]
        self._rows = config["lcd_rows"]
        self._lcd  = LCD_I2C(config["lcd_i2c_address"], self._cols, self._rows)
        self._lcd.backlight.on()
        self._lcd.blink.off()

    def _write(self, line0, line1=""):
        """Write two lines to the LCD, padded to 16 chars each."""
        self._lcd.clear()
        self._lcd.cursor.setPos(0, 0)
        self._lcd.write_text(_pad(line0, self._cols))
        self._lcd.cursor.setPos(1, 0)
        self._lcd.write_text(_pad(line1, self._cols))

    def draw_intro(self):
        self._write("Pi Puzzle", "Key to start...")

    def draw_ready_prompt(self):
        self._write("Are you ready?", "Press button...")

    def draw_round_start(self, round_num, target):
        e  = EMOTION_SHORT.get(target.emotion,       target.emotion[:3])
        lg = GESTURE_SHORT.get(target.left_gesture,  target.left_gesture[:4])
        rg = GESTURE_SHORT.get(target.right_gesture, target.right_gesture[:4])
        total = CONFIG["total_rounds"]
        self._write(f"R{round_num}/{total} E:{e} L:{lg}",
                    f"R:{rg} LC:{target.left_color} RC:{target.right_color}")

    def draw_countdown(self, target, seconds_left, round_num):
        e  = EMOTION_SHORT.get(target.emotion,      target.emotion[:3])
        lg = GESTURE_SHORT.get(target.left_gesture, target.left_gesture[:4])
        total = CONFIG["total_rounds"]
        self._write(f"R{round_num}/{total} E:{e} L:{lg}",
                    f"Ready! {seconds_left:4.1f}s")

    def draw_hold(self, seconds_left, total_hold):
        fraction_done = 1.0 - (seconds_left / total_hold)
        filled = int(round(fraction_done * 8))
        bar = "#" * max(0, min(8, filled)) + "-" * (8 - max(0, min(8, filled)))
        self._write("HOLD!", f"[{bar}]{seconds_left:>4.1f}s")

    def draw_result(self, passed, target, detection):
        header = "** PASS! **" if passed else "** FAIL  **"

        def mark(t, d):
            return "O" if t == d else "X"

        e_m  = mark(target.emotion,      detection.emotion)
        lg_m = mark(target.left_gesture, detection.left_gesture)
        rg_m = mark(target.right_gesture, detection.right_gesture)
        lc_m = mark(target.left_color,   detection.left_color)
        rc_m = mark(target.right_color,  detection.right_color)
        self._write(header, f"E:{e_m} L:{lg_m} R:{rg_m} C:{lc_m}{rc_m}")

    def draw_show_score_prompt(self):
        self._write("Game over!", "Btn: show score")

    def draw_final_score(self, score, round_results):
        total   = CONFIG["total_rounds"]
        outcome = "WIN!" if score >= CONFIG["pass_threshold"] else "LOSE"
        marks   = " ".join(f"R{i+1}:{'O' if ok else 'X'}"
                           for i, ok in enumerate(round_results))
        self._write(f"Score:{score}/{total} {outcome}", marks)

    def draw_play_again_prompt(self):
        self._write("Play again?", "Press button...")

    def draw_message(self, line0, line1=""):
        self._write(line0, line1)

    def close(self):
        self._lcd.clear()
        self._lcd.backlight.off()
