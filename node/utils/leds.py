import time
import threading
import numpy as np
from gpiozero import LED

from node.utils import apa102

class Pixels:
    def __init__(self):
        self.n_pixels = 0

    def init(self):
        self.dev = apa102.APA102(num_led=self.n_pixels)
        
        self.power = LED(5)
        self.power.on()

    def wakeup(self):
        pass

    def listen(self):
        pass

    def think(self):
        pass

    def speak(self):
        pass

    def off(self):
        pass

    def interrupt(self):
        pass

    def show(self):
        if self.n_pixels > 0:
            for i in range(self.n_pixels):
                pixel = self.pixels[i]
                self.dev.set_pixel(i, int(pixel[0]), int(pixel[1]), int(pixel[2]))

            self.dev.show()

class Respeaker4MicHat(Pixels):
    def __init__(self):
        Pixels.__init__(self)
        self.n_pixels = 12
        self.color = np.array([0, 255, 0]) / 2
        self.init()
        self.pixels = np.array([[0,0,0] for _ in range(self.n_pixels)])
        self.show()
        time.sleep(0.1)
        self.brightness = 0
        self.stop = False

    def fade(self, direction = 1, speed=0.05):
        #brightness = 0 if direction == 1 else 1
        while not self.stop:
            self.pixels = np.array([self.color for _ in range(self.n_pixels)]) * self.brightness
            self.show()
            time.sleep(0.05)
            self.brightness += speed * direction
            if self.brightness <= 0 or self.brightness > 1:
                break

    def listen(self):
        self.stop = False
        def run():
            self.brightness = 0
            self.fade(direction = 1)

        threading.Thread(target=run, daemon=True).start()

    def think(self):
        self.stop = False
        def run():
            pos = 0
            pattern = np.concatenate((self.color, self.color/2, self.color/4), axis=None)
            while not self.stop:
                self.pixels[pos:pos+3] = pattern
                self.pixels[pos+3:pos+6] = pattern
                self.pixels[pos+6:pos+9] = pattern
                pos += 1
                self.show()
                if pos >= 3: 
                    pos = 0
                time.sleep(0.1)

        threading.Thread(target=run, daemon=True).start()

    def speak(self):
        self.stop = False
        def run():
            while not self.stop:
                self.brightness = 1
                self.fade(direction = 1)
                self.fade(direction = -1)

        threading.Thread(target=run, daemon=True).start()

    def off(self):
        self.stop = False
        def run():
            self.fade(direction = -1, speed = 0.1)
            self.pixels = np.array([[0,0,0] for _ in range(self.n_pixels)])
            self.show()
            self.brightness = 0
            self.stop = True

        threading.Thread(target=run, daemon=True).start()

    def interrupt(self):
        self.stop = True
        time.sleep(0.05)