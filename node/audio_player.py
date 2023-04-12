import pyaudio
import wave
import os
import io
import pydub
from pydub.playback import play
from typing import Tuple
import threading

from node.utils.audio import *

class AudioPlayer:
    def __init__(self, node: 'Node'):
        self.node = node
        self.speaker_idx = node.speaker_idx
        self.sample_rate = node.sample_rate


class PydubPlayer(AudioPlayer):

    def play_audio_bytes(self, audio_bytes: bytes, sample_rate: int, sample_width: int, channels: int, asynchronous:bool=False):
        def play_audio():
            audio = pydub.AudioSegment(
                audio_bytes, 
                frame_rate=sample_rate,
                sample_width=sample_width, 
                channels=channels
            )
            play(audio)
        if asynchronous:
            threading.Thread(target=play_audio).start()
        else:
            play_audio()

    def play_audio_file(self, file: str, asynchronous:bool=False):
        def play_audio():
            audio = pydub.AudioSegment.from_wav(file)
            play(audio)

        if asynchronous:
            threading.Thread(target=play_audio).start()
        else:
            play_audio()

class PyaudioPlayer(AudioPlayer):

    def __init__(self, node: 'Node'):
        super().__init__(node)

        self.p = pyaudio.PyAudio()

    def play_audio_bytes(self, audio_bytes: bytes, sample_rate: int, sample_width: int, channels: int, asynchronous:bool=False):
        def play_audio():      

            self.pyaudio_stream(wave.open(io.BytesIO(audio_bytes), "rb"))
            
        if asynchronous:
            threading.Thread(target=play_audio).start()
        else:
            play_audio()

    def play_audio_file(self, file: str, asynchronous:bool=False):
        def play_audio():
            if not os.path.exists(file):
                raise RuntimeError('Audio file does not exist')

            wf = wave.open(file, 'rb')

            self.pyaudio_stream(wf)

        if asynchronous:
            threading.Thread(target=play_audio).start()
        else:
            play_audio()

    def pyaudio_stream(self, wave_file):  
        CHUNK = 1024
        stream = self.p.open(format=self.p.get_format_from_width(wave_file.getsampwidth()),
                            channels=wave_file.getnchannels(),
                            rate=self.sample_rate,
                            output=True,
                            output_device_index=self.speaker_idx)

        data = wave_file.readframes(CHUNK)

        while len(data):
            stream.write(data)
            data = wave_file.readframes(CHUNK)

        stream.stop_stream()
        stream.close()

        self.p.terminate()

