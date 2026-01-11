# I2C Scanner MicroPython
from machine import Pin, I2C
from ssd1306 import SSD1306
from board_led import BoardLED
from xbox import Xbox360Interface
import usb.device

import time


OLED_WIDTH: int = 128
OLED_HEIGHT: int = 64


def measure_text(s: str) -> tuple[int, int]:
    return len(s) * 8, 8


def cycle(arr):
    while True:
        for x in arr:
            yield x


def hsv_to_rgb(h, brightness=1.0):
    # h: 0.0 ~ 1.0
    # brightness: 0.0 ~ 1.0

    i = int(h * 6)
    f = h * 6 - i
    q = 1.0 - f
    t = f
    i = i % 6

    if i == 0:
        r, g, b = 1.0, t, 0.0
    elif i == 1:
        r, g, b = q, 1.0, 0.0
    elif i == 2:
        r, g, b = 0.0, 1.0, t
    elif i == 3:
        r, g, b = 0.0, q, 1.0
    elif i == 4:
        r, g, b = t, 0.0, 1.0
    else:  # i == 5
        r, g, b = 1.0, 0.0, q

    # 统一亮度缩放
    r = int(255 * r * brightness)
    g = int(255 * g * brightness)
    b = int(255 * b * brightness)

    return r, g, b


class Hitbox:
    i2c: I2C
    oled: SSD1306

    up: Pin
    down: Pin
    left: Pin
    right: Pin

    gamepad: Xbox360Interface

    def __init__(self) -> None:
        BoardLED.on(255, 0, 0)

        self.up = Pin(5, Pin.IN, Pin.PULL_UP)
        self.down = Pin(4, Pin.IN, Pin.PULL_UP)
        self.left = Pin(3, Pin.IN, Pin.PULL_UP)
        self.right = Pin(2, Pin.IN, Pin.PULL_UP)

        self.h = 0.0

        self.init_i2c()
        self.oled = SSD1306(OLED_WIDTH, OLED_HEIGHT, self.i2c)

        self.init_gp()

    def init_i2c(self):
        self.i2c = I2C(scl=Pin(1), sda=Pin(0))

        print("I2C SCANNER")
        devices = self.i2c.scan()

        if len(devices) == 0:
            print("No i2c device !")
        else:
            print("i2c devices found:", len(devices))

            for device in devices:
                print("I2C hexadecimal address: ", hex(device))

    def init_gp(self):
        self.gamepad = Xbox360Interface()
        usb.device.get().init(self.gamepad, builtin_driver=True)

        count_of_dot = cycle([1, 2, 3])

        while not self.gamepad.is_open():
            self.oled.fill(0)
            self.text_centered_xy(f"Connecting{next(count_of_dot) * '.'}")
            self.oled.show()

            time.sleep_ms(100)

    def run(self):
        self.oled.fill(0)
        self.text_centered_xy("HEllo!!")
        self.oled.show()

        while True:
            r, g, b = hsv_to_rgb(self.h, 0.05)
            BoardLED.on(r, g, b)
            self.h += 0.01
            if self.h >= 1.0:
                self.h = 0.0

            if self.up.value() == 0:
                self.gamepad.press_button(4)
            else:
                self.gamepad.release_button(4)
            if self.down.value() == 0:
                self.gamepad.press_button(1)
            else:
                self.gamepad.release_button(1)
            if self.left.value() == 0:
                self.gamepad.press_button(3)
            else:
                self.gamepad.release_button(3)
            if self.right.value() == 0:
                self.gamepad.press_button(2)
            else:
                self.gamepad.release_button(2)

            time.sleep(0.05)

        self.stop()

    def stop(self):
        BoardLED.off()

        print("finish")

    def text_centered_xy(self, text: str):
        w, h = measure_text(text)
        x = (OLED_WIDTH - w) // 2
        y = (OLED_HEIGHT - h) // 2
        self.oled.text(text, x, y)


if __name__ == "__main__":
    hb = Hitbox()

    hb.run()
