import queue
import vosk
import sounddevice as sd
import pyaudio
import json
import wave
import collections
import webrtcvad
import time
import threading
from typing import List, Tuple

class Stream:
    def __init__(self, 
                 device_idx: int, 
                 sample_rate: int, 
                 channels: int, 
                 sample_width: int,
                 frames_per_buffer: int = 1024
    ):
        
        self.device_idx = device_idx
        self.sample_rate = sample_rate
        self.channels = channels
        self.sample_width = sample_width
        self.frames_per_buffer = frames_per_buffer

        # Define a buffer to store audio frames
        self.buffer = queue.Queue()
        # Define a recording buffer for the start of the recording
        self.recording_buffer = collections.deque(maxlen=2)

        self.RECORDING = False

    def get_chunk(self) -> bytes:
        return self.buffer.get()

class PyaudioStream(Stream):

    def start_stream(self):
        self.RECORDING = True
        threading.Thread(target=self.stream, daemon=True).start()

    def stop_stream(self):
        self.RECORDING = False

    def stream(self):
        try:
            audio = pyaudio.PyAudio()

            def callback(in_data, frame_count, time_info, status):
                if in_data:
                    self.buffer.put(in_data)
                    self.recording_buffer.append(in_data)

                return (None, pyaudio.paContinue)

            # Open device
            mic = audio.open(
                input_device_index=self.device_idx,
                channels=self.channels,
                format=audio.get_format_from_width(self.sample_width),
                rate=self.sample_rate,
                frames_per_buffer=self.frames_per_buffer,
                input=True,
                stream_callback=callback,
            )

            assert mic is not None
            mic.start_stream()
            print("Recording audio")

            while mic.is_active():
                if not self.RECORDING:
                    break
                time.sleep(0.1)

            mic.stop_stream()
            audio.terminate()

        except Exception as e:
            print("Error recording")
