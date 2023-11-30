import wave
import os
import io
import threading
import sounddevice as sd
import soundfile as sf

from node import config
from node.utils.audio import *

class AudioPlayer:
    def __init__(self, node):
        self.speaker_idx = node.speaker_idx
        self.speaker_sample_rate = node.sample_rate
        self.speaker_sample_width = node.sample_width
        self.speaker_channels = node.audio_channels

    def play_audio_file(self, file: str, asynchronous: bool = False):
        def play_audio():
            data, fs = sf.read(file, dtype='float32')  
            sd.play(data, fs, device=self.speaker_idx)
            status = sd.wait()
        if asynchronous:
            threading.Thread(target=play_audio, daemon=True).start()
        else:
            play_audio()