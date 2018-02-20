from logger import Logger
import threading
import time
from lib.neopixel import *

# LED strip configuration:
LED_COUNT = 77  # Number of LED pixels.
LED_PIN = 10  # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10  # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53
LED_STRIP = ws.WS2811_STRIP_GRB  # Strip type and colour ordering


class LEDStrip:
    def __init__(self):
        self.thr = None
        self.stopping = False
        # Create NeoPixel object with appropriate configuration.
        self.strip = Adafruit_NeoPixel(
            LED_COUNT, LED_PIN, LED_FREQ_HZ,
            LED_DMA, LED_INVERT, LED_BRIGHTNESS,
            LED_CHANNEL, LED_STRIP)
        # Intialize the library (must be called once before other functions).
        self.strip.begin()
        # Make sure the lights start in an off state
        self.strip.setBrightness(0)
        self.strip.show()

    @staticmethod
    def wheel(pos):
        """Generate rainbow colors across 0-255 positions."""
        if pos < 85:
            return Color(pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return Color(255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return Color(0, pos * 3, 255 - pos * 3)

    def rainbow(self, wait_ms=20, iterations=1):
        """Draw rainbow that fades across all pixels at once."""
        for j in range(256 * iterations):
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, self.wheel((i + j) & 255))
            self.strip.show()
            time.sleep(wait_ms / 1000.0)
            if self.stopping:
                return

    def stop(self):
        self.stopping = True

    def run(self):
        if self.thr is not None:
            if self.thr.isAlive():
                return
        self.thr = LEDThread(0, 'loop', self)
        self.strip.setBrightness(LED_BRIGHTNESS)
        self.strip.show()
        self.stopping = False
        self.thr.start()

    def loop(self):
        while not self.stopping:
            Logger.write.debug('LED strip rainbow!')
            self.rainbow()

        # Fade it out
        for b in range(LED_BRIGHTNESS, 0, -3):
            self.strip.setBrightness(b)
            time.sleep(20 / 1000.0)
            self.strip.show()
        # Make sure the lights are off
        self.strip.setBrightness(0)
        self.strip.show()

class LEDThread(threading.Thread):
    def __init__(self, thread_id, name, led_strip):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.name = name
        self.led_strip = led_strip

    def run(self):
        self.led_strip.loop()
