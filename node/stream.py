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

class Stream(threading.Thread):
    def __init__(self, 
                 node: 'Node',
                 frames_per_buffer: int = 1024,
                 recording_buffer_size: int = 12
    ):
        self.node = node
        self.device_idx = node.mic_idx
        self.sample_rate = node.sample_rate
        self.channels = node.channels
        self.sample_width = node.sample_width
        self.frames_per_buffer = frames_per_buffer

        # Define a buffer to store audio frames
        self.buffer = queue.Queue()

        self.STOP_RECORDING = threading.Event()

    def start_stream(self):
        self.STOP_RECORDING.clear()
        threading.Thread(target=self.run_stream, daemon=True).start()

    def stop_stream(self):
        self.STOP_RECORDING.set()

    def run_stream(self):
        pass

    def get_chunk(self) -> bytes:
        return self.buffer.get()

    def clear(self):
        self.buffer.queue.clear()

class PyaudioStream(Stream):

    def run_stream(self):
        try:
            audio = pyaudio.PyAudio()

            def callback(in_data, frame_count, time_info, status):
                if in_data:
                    self.buffer.put_nowait(in_data)

                return (None, pyaudio.paContinue)

            # Open device
            mic = audio.open(
                input_device_index=self.device_idx,
                channels=self.channels,
                format=audio.get_format_from_width(self.sample_width),
                rate=self.sample_rate,
                frames_per_buffer=self.frames_per_buffer,
                input=True,
                stream_callback=callback
            )

            assert mic is not None
            mic.start_stream()
            print("Pyaudio stream started")

            while mic.is_active():
                time.sleep(0.1)
                if self.STOP_RECORDING.is_set():
                    break

            print("Finished recording")
            mic.stop_stream()
            audio.terminate()

        except Exception as e:
            print(repr(e))
            print("Error recording")
            raise e

class SounddeviceStream(Stream):

    def run_stream(self):
        try:

            def callback(in_data, frame_count, time_info, status):
                if in_data:
                    self.buffer.put_nowait(bytes(in_data))
                    self.recording_buffer.append(bytes(in_data))

            with sd.RawInputStream(
                samplerate=self.sample_rate, 
                channels=self.channels,
                device=self.device_idx, 
                callback=callback, 
                blocksize=self.frames_per_buffer, 
                dtype="int16"):

                while not self.STOP_RECORDING.is_set():
                    time.sleep(0.1)
        
        except Exception as e:
            print(repr(e))
            print("Error recording")