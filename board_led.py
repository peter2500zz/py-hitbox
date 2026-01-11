from machine import Pin
import neopixel

# WS2812 在 GP16
pin = Pin(16, Pin.OUT)
np = neopixel.NeoPixel(pin, 1)

class BoardLED:
    @staticmethod
    def on(r: int, g: int, b: int):
        np[0] = (r, g, b)
        np.write()

    @staticmethod
    def off():
        np[0] = (0, 0, 0)
        np.write()
