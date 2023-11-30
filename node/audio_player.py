import threading
import time
import sounddevice as sd
import soundfile as sf

class AudioPlayer:
    def __init__(self, node):
        self.speaker_idx = node.speaker_idx
        self.speaker_busy = False

    def play_audio_file(self, file: str, asynchronous: bool = False):
        def play_audio():
            while self.speaker_busy:
                time.sleep(0.1)
            
            self.speaker_busy = True
            data, fs = sf.read(file, dtype='float32')  
            sd.play(data, fs, device=self.speaker_idx)
            status = sd.wait()
            self.speaker_busy = False

        if asynchronous:
            threading.Thread(target=play_audio, daemon=True).start()
        else:
            play_audio()