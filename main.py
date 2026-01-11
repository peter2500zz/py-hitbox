# I2C Scanner MicroPython
from io import StringIO
from machine import Pin, I2C
from ssd1306 import SSD1306
from board_led import BoardLED
from xbox import Xbox360Interface
import usb.device
from keymgr import KeyMgr, KeyState

import sys
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
    direction: list[int]
    keymgr: KeyMgr

    def __init__(self) -> None:
        BoardLED.on(0, 255, 0)

        self.up = Pin(2, Pin.IN, Pin.PULL_UP)
        self.down = Pin(3, Pin.IN, Pin.PULL_UP)
        self.left = Pin(4, Pin.IN, Pin.PULL_UP)
        self.right = Pin(5, Pin.IN, Pin.PULL_UP)

        self.direction = [0, 0]

        self.h = 0.0

        self.keymgr = KeyMgr()

        self.__init_i2c()
        self.oled = SSD1306(OLED_WIDTH, OLED_HEIGHT, self.i2c)

        self.__init_gp()

    def __init_i2c(self):
        self.i2c = I2C(scl=Pin(1), sda=Pin(0))

        print("I2C SCANNER")
        devices = self.i2c.scan()

        if len(devices) == 0:
            print("No i2c device !")
        else:
            print("i2c devices found:", len(devices))

            for device in devices:
                print("I2C hexadecimal address: ", hex(device))

    def __init_gp(self):
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

        try:
            while True:
                self.__loop()
        except Exception as e:
            buf = StringIO()
            sys.print_exception(e, buf)

            self.__show_error(buf.getvalue())

        self.stop()

    def __loop(self):
        self.oled.fill(0)

        r, g, b = hsv_to_rgb(self.h, 0.05)
        BoardLED.on(r, g, b)
        self.h += 0.01
        if self.h >= 1.0:
            self.h = 0.0

        changed = False

        state = self.keymgr.update("up", self.up.value() == 0)
        if state == KeyState.Press:
            self.direction[1] = -127
            changed = True
        elif state == KeyState.Release:
            self.direction[1] = 0
            changed = True

        state = self.keymgr.update("down", self.down.value() == 0)
        if state == KeyState.Press:
            self.direction[1] = 127
            changed = True
        elif state == KeyState.Release:
            self.direction[1] = 0
            changed = True

        state = self.keymgr.update("left", self.left.value() == 0)
        if state == KeyState.Press:
            self.direction[0] = -127
            changed = True
        elif state == KeyState.Release:
            self.direction[0] = 0
            changed = True

        state = self.keymgr.update("right", self.right.value() == 0)
        if state == KeyState.Press:
            self.direction[0] = 127
            changed = True
        elif state == KeyState.Release:
            self.direction[0] = 0
            changed = True

        if changed:
            self.gamepad.move_left_stick(*self.direction)
            BoardLED.on(0, 0, 8)

        self.oled.show()

    def __show_error(self, error_traceback: str):
        MAX_CHARS = 16
        SCREEN_LINES = 8
        PAUSE_FRAMES = 10
        FRAME_DELAY = 0.15

        # 1. 拆成每行 <=16 字符的 buffer
        buffer = []
        for text in error_traceback.splitlines():
            while len(text) > MAX_CHARS:
                buffer.append(text[:MAX_CHARS])
                text = text[MAX_CHARS:]
            buffer.append(text)

        offset = 0
        direction = 1  # 1 向下，-1 向上
        pause = 0
        err_led_state = True

        # 2. 无限滚动显示
        while True:
            BoardLED.on(255 if err_led_state else 0, 0, 0)
            err_led_state = not err_led_state

            self.oled.fill(0)

            for i in range(SCREEN_LINES):
                idx = offset + i
                if idx >= len(buffer):
                    break
                self.oled.text(buffer[idx], 0, i * 8)

            self.oled.show()

            # 行数不够，不滚
            if len(buffer) <= SCREEN_LINES:
                time.sleep(FRAME_DELAY)
                continue

            # 首尾停留
            if pause > 0:
                pause -= 1
                time.sleep(FRAME_DELAY)
                continue

            offset += direction

            # 到底部
            if offset >= len(buffer) - SCREEN_LINES:
                offset = len(buffer) - SCREEN_LINES
                direction = -1
                pause = PAUSE_FRAMES

            # 到顶部
            elif offset <= 0:
                offset = 0
                direction = 1
                pause = PAUSE_FRAMES

            time.sleep(FRAME_DELAY)

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
