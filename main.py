# I2C Scanner MicroPython
from machine import Pin, SoftI2C
import ssd1306

# You can choose any other combination of I2C pins
i2c = SoftI2C(scl=Pin(1), sda=Pin(0))

print("I2C SCANNER")
devices = i2c.scan()

if len(devices) == 0:
    print("No i2c device !")
else:
    print("i2c devices found:", len(devices))

    for device in devices:
        print("I2C hexadecimal address: ", hex(device))

oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306(oled_width, oled_height, i2c)

oled.text("Hello, World 1!", 0, 0)
oled.text("Hello, World 2!", 0, 10)
oled.text("Hello, World 3!", 0, 20)

oled.show()
