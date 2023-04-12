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
    def __init__(self, node: 'Node', speaker_idx: int):
        self.node = node
        self.speaker_idx = speaker_idx


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

    def __init__(self, node: 'Node', speaker_idx: int):
        super().__init__(node, speaker_idx)

        self.p = pyaudio.PyAudio()

    def play_audio_bytes(self, audio_bytes: bytes, sample_rate: int, sample_width: int, channels: int, asynchronous:bool=False):
        def play_audio():      

            wf = wave.open(io.BytesIo(), 'rb')
            wf.setframerate(sample_rate)
            wf.setsamplewidth(sample_width)
            wf.setnchannels(channels)
            wf.writeframes(audio_bytes)

            self.pyaudio_stream(wf)
            
        if asynchronous:
            threading.Thread(target=play_audio).start()
        else:
            play_audio()

    def play_audio_file(self, file: str, asynchronous:bool=False):
        def play_audio():
            if not os.path.exists(file):
                raise RuntimeError('Audio file does not exist')

            wf = wave.open(file, 'rb')

            wav_bytes = maybe_convert_wav(wf, sample_rate=48000, sample_width=2, channels=1)

            wf = wave.open(io.BytesIO(), 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(48000)
            wf.writeframes(wav_bytes)
            wf.close()

            self.pyaudio_stream(wf)

        if asynchronous:
            threading.Thread(target=play_audio).start()
        else:
            play_audio()

    def pyaudio_stream(self, wave_file):  
        CHUNK = 1024
        stream = self.p.open(format=self.p.get_format_from_width(wave_file.getsampwidth()),
                            channels=wave_file.getnchannels(),
                            rate=wave_file.getframerate(),
                            output=True,
                            output_device_index=self.speaker_idx)

        data = wave_file.readframes(CHUNK)

        while len(data):
            stream.write(data)
            data = wave_file.readframes(CHUNK)

        stream.stop_stream()
        stream.close()

        self.p.terminate()

