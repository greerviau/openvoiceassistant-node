import threading
import time
import sounddevice as sd
import soundfile as sf

class AudioPlayer:
    def __init__(self, node):
        self.node = node
        self.speaker_idx = node.speaker_idx
        self.speaker_busy = False

    def play_audio_file(self, file: str, asynchronous: bool = False):
        def play_audio():
            while self.speaker_busy:
                time.sleep(0.1)
            
            self.speaker_busy = True
            self.play_output_stream(file)
            self.speaker_busy = False

        if asynchronous:
            threading.Thread(target=play_audio, daemon=True).start()
        else:
            play_audio()

    def play_sounddevice(self, file):
        data, fs = sf.read(file, dtype='float32')  
        sd.play(data, fs, device=self.speaker_idx)
        status = sd.wait()

    def play_output_stream(self, file):
        event = threading.Event()
        def callback(outdata, frames, time, status):
            data = wf.buffer_read(frames, dtype='float32')
            if len(outdata) > len(data):
                outdata[:len(data)] = data
                outdata[len(data):] = b'\x00' * (len(outdata) - len(data))
                raise sd.CallbackStop
            else:
                outdata[:] = data

        with sf.SoundFile(file) as wf:
            stream = sd.RawOutputStream(samplerate=wf.samplerate,
                                    channels=wf.channels,
                                    callback=callback,
                                    blocksize=1024,
                                    finished_callback=self.node.pause_flag.set)
            with stream:
                event.wait()