import queue
import time
import threading
import sounddevice as sd

class MicrophoneStream():
    def __init__(self, 
                 node,
                 frames_per_buffer: int = 1024,
                 recording_buffer_size: int = 12
    ):
        self.mic_idx = node.mic_idx
        self.sample_rate = node.sample_rate
        self.sample_width = node.sample_width
        self.channels = node.audio_channels
        self.frames_per_buffer = frames_per_buffer

        # Define a buffer to store audio frames
        self.buffer = queue.Queue()

        self.RECORDING = False
        self.record_thread = None

    def start(self):
        self.RECORDING = True
        self.record_thread = threading.Thread(target=self.record, daemon=True)
        self.record_thread.start()

    def stop(self):
        self.RECORDING = False
        self.record_thread.join()
        self.buffer.queue.clear()

    def record(self):
        def callback(in_data, frame_count, time_info, status):
            self.buffer.put(bytes(in_data))
        try:
            print('Stream started')
            with sd.RawInputStream(samplerate=self.sample_rate, 
                                    device=self.mic_idx, 
                                    channels=self.channels, 
                                    blocksize=self.frames_per_buffer,
                                    dtype="int16",
                                    callback=callback):
                while self.RECORDING:
                    time.sleep(0.1)

        except Exception as e:
            print(repr(e))
            print("Error recording")
            raise e

    def get_chunk(self) -> bytes:
        return self.buffer.get()