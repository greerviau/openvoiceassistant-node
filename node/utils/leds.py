import time
import threading
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
        self.init()
        self.pixels = [[0,0,0] for _ in range(self.n_pixels)]
        self.stop = False

    def wakeup(self):
        self.stop = False
        def run():
            fade = 0
            while not self.stop:
                self.pixels = [[0, 64, fade] for _ in range(self.n_pixels)]
                self.show()
                time.sleep(0.01)
                fade += 1
                if fade > 6:
                    break
        threading.Thread(target=run, daemon=True).start()

    def listen(self):
        self.stop = False
        def run():
            step = 1
            fade = 0
            while not self.stop:
                self.pixels = [[0, 64, fade] for _ in range(self.n_pixels)]
                self.show()
                time.sleep(0.01)
                if fade <= 0:
                    step = 1
                    time.sleep(0.4)
                elif fade >= 6:
                    step = -1
                    time.sleep(0.4)

                fade += step
        threading.Thread(target=run, daemon=True).start()

    def think(self):
        self.stop = False
        def run():
            self.pixels = [[0, 64, 6] for _ in range(self.n_pixels)]
            self.show()
            pos = 1
            while not self.stop:
                self.pixels[pos] = [0, 128, 0]
                self.pixels[pos-1] = [0, 64, 6]
                pos += 1
                self.show()
                if pos >= self.n_pixels: 
                    pos = 0
                time.sleep(0.05)
        threading.Thread(target=run, daemon=True).start()

    def speak(self):
        self.stop = False
        def run():
            step = 1
            fade = 0
            while not self.stop:
                self.pixels = [[0, 64, fade] for _ in range(self.n_pixels)]
                self.show()
                time.sleep(0.01)
                if fade <= 0:
                    step = 1
                    time.sleep(0.4)
                elif fade >= 6:
                    step = -1
                    time.sleep(0.4)

                fade += step
        threading.Thread(target=run, daemon=True).start()

    def off(self):
        self.stop = True
        self.pixels = [[0,0,0] for _ in range(self.n_pixels)]
        self.show()

    def interrupt(self):
        self.stop = True
        time.sleep(0.1)