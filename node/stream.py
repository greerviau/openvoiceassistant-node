import queue
import pyaudio
import time
import threading

class Stream():
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

    def start(self):
        self.STOP_RECORDING.clear()
        threading.Thread(target=self.record, daemon=True).start()

    def stop(self):
        self.STOP_RECORDING.set()

    def record(self):
        pass

    def get_chunk(self) -> bytes:
        return self.buffer.get()

    def clear(self):
        self.buffer.queue.clear()

class PyaudioStream(Stream):

    def record(self):
        try:
            audio = pyaudio.PyAudio()

            def callback(in_data, frame_count, time_info, status):
                if in_data:
                    self.buffer.put(in_data)

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

            print("Finished recording")
            mic.stop_stream()
            audio.terminate()

        except Exception as e:
            print(repr(e))
            print("Error recording")
            raise e