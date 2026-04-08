"""
test_lcd.py — Confirm the 16x2 I2C LCD is wired and working.

Run:  python test_lcd.py
You should see a sequence of messages on the LCD.
If nothing shows, try changing lcd_i2c_address to 0x3F in config.py.
Run `i2cdetect -y 1` to find the actual address.
"""

import time
from lcd_i2c import LCD_I2C
from config import CONFIG

#lcd = LCD_I2C(CONFIG["lcd_i2c_address"], CONFIG["lcd_cols"], CONFIG["lcd_rows"])
lcd = LCD_I2C(39, 16, 2)
lcd.backlight.on()
lcd.blink.off()
#lcd.begin() #there is no begin() method in the LCD_I2C class, so this line can be removed

def show(line0, line1="", hold=2.0):
    global lcd
    lcd.clear()
    lcd.cursor.setPos(0, 0)
    lcd.write_text(line0[:16].ljust(16))
    lcd.cursor.setPos(1, 0)
    lcd.write_text(line1[:16].ljust(16))
    time.sleep(hold)

print("Testing LCD...")

show("LCD test", "Hello!")
show("Line 0: top", "Line 1: bottom")
show("1234567890123456", "abcdefghijklmnop")  # full 16-char rows
show("Done!", "")

lcd.clear()
print("LCD test complete.")
