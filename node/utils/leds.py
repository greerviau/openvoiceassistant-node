import time
import threading
from gpiozero import LED

from node.utils import apa102

class Pixels:
    def __init__(self):
        self.n_pixels = 0
        self.dev = apa102.APA102(num_led=0)
        
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

    def show(self, pixels):
        if self.n_pixels > 0:
            for i in range(self.n_pixels):
                self.dev.set_pixel(i, int(pixels[i][0]), int(pixels[i][1]), int(pixels[i][2]))

            self.dev.show()

class Respeaker4MicHat(Pixels):
    def __init__(self):
        Pixels.__init__(self)
        self.n_pixels = 12
        self.pixels = [[0,0,0] for _ in range(self.n_pixels)]
        self.stop = False

    def wakeup(self):
        self.stop = False
        def run():
            fade = 0
            while not self.stop:
                self.pixels = [[0, 128, fade] for _ in range(self.n_pixels)]
                self.show(self.pixels)
                time.sleep(0.01)
                fade += 1
                if fade > 12:
                    break
        threading.Thread(target=run, daemon=True).start()

    def listen(self):
        self.stop = False
        def run():
            step = 1
            fade = 0
            while not self.stop:
                self.pixels = [[0, 128, fade] for _ in range(self.n_pixels)]
                self.show(self.pixels)
                time.sleep(0.01)
                if fade <= 0:
                    step = 1
                    time.sleep(0.4)
                elif fade >= 12:
                    step = -1
                    time.sleep(0.4)

                fade += step
        threading.Thread(target=run, daemon=True).start()

    def think(self):
        self.stop = False
        def run():
            self.pixels = [[0, 128, 12] for _ in range(self.n_pixels)]
            self.show(self.pixels)
            pos = 0
            while not self.stop:
                self.pixels[pos] = [0, 128, 12]
                pos += 1
                self.pixels[pos-1] = [0, 128, 0]
                self.show(self.pixels)
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
                self.pixels = [[0, 128, fade] for _ in range(self.n_pixels)]
                self.show(self.pixels)
                time.sleep(0.01)
                if fade <= 0:
                    step = 1
                    time.sleep(0.4)
                elif fade >= 12:
                    step = -1
                    time.sleep(0.4)

                fade += step
        threading.Thread(target=run, daemon=True).start()

    def off(self):
        self.stop = True
        self.show([[0,0,0] for _ in range(self.n_pixels)])

    def interrupt(self):
        self.stop = True
        time.sleep(0.1)