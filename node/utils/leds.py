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
        self.stop = False

    def fade(self, direction = 1, speed=0.05):
        brightness = 0 if direction else 1
        while not self.stop:
            self.pixels = np.array([self.color for _ in range(self.n_pixels)]) * brightness
            self.show()
            time.sleep(0.05)
            brightness += speed * direction
            print(brightness)
            if brightness <= 0 or brightness > 1:
                break

    def listen(self):
        self.stop = False
        def run():
            self.fade(direction = 1)

        threading.Thread(target=run, daemon=True).start()

    def think(self):
        self.stop = False
        def run():
            pos = 0
            while not self.stop:
                self.pixels = np.array([[0,0,0] for _ in range(self.n_pixels)])
                self.pixels[pos] = self.color
                self.pixels[pos+3] = self.color
                self.pixels[pos+6] = self.color
                self.pixels[pos+9] = self.color
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
                self.fade(direction = 1)
                self.fade(direction = -1)

        threading.Thread(target=run, daemon=True).start()

    def off(self):
        self.stop = False
        def run():
            self.fade(direction = -1)

        threading.Thread(target=run, daemon=True).start()
        
        self.stop = True

    def interrupt(self):
        self.stop = True
        time.sleep(0.1)