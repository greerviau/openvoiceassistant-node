import queue
import vosk
import sounddevice as sd
import pyaudio
import json
import wave
import collections
import webrtcvad
from typing import List, Tuple

from node.stream import PyaudioStream
from node.wake import KaldiWake


class Listener:
    def __init__(self, 
                 wake_word: str, 
                 device_idx: int, 
                 sample_rate: int, 
                 sample_width: int,
                 channels: int,
                 sensitivity: int,
    ):
        self.wake_word = wake_word
        self.device_idx = device_idx
        self.sample_rate = sample_rate
        self.sample_width = sample_width
        self.channels = channels
        self.sensitivity = sensitivity

        # Define a recording buffer for the start of the recording
        self.recording_buffer = collections.deque(maxlen=2)

        self.stream = PyaudioStream(device_idx=self.device_idx,
                                    sample_rate=self.sample_rate,
                                    channels=self.channels,
                                    sample_width=self.sample_width,
                                    frames_per_buffer=8000)
        
        self.stream.start_stream()
        
        self.wake = KaldiWake(wake_word=self.wake_word,
                              sample_rate=self.sample_rate)
        
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(sensitivity)

        self.vad_chunk_size = 960 # 30ms
        self.vad_audio_data = bytes()
    
    def listen(self):
        self.wake.listen_for_wake_word(self.stream)

        audio_data = [chunk for chunk in self.stream.recording_buffer]

        while True:
            chunk = self.stream.get_chunk()

            audio_data.append(chunk)

            self.vad_audio_data += chunk

            is_speech = False

            # Process in chunks of 30ms for webrtcvad
            while len(self.vad_audio_data) >= self.vad_chunk_size:
                vad_chunk = self.vad_audio_data[: self.vad_chunk_size]
                self.vad_audio_data = self.vad_audio_data[
                    self.vad_chunk_size :
                ]

                # Speech in any chunk counts as speech
                is_speech = is_speech or self.vad.is_speech(
                    vad_chunk, 16000
                )
            print(is_speech)

            if not is_speech:
                return b''.join(audio_data)