import threading
import sounddevice as sd
import soundfile as sf

class AudioPlayer:
    def __init__(self, node):
        self.node = node
        self.speaker_idx = node.speaker_idx

    def play_audio_file(self, file: str, asynchronous: bool = False, loop: bool = False):
            if asynchronous == False and loop == True:
                raise RuntimeWarning("Infinite loop detected")

            data, fs = sf.read(file, dtype="float32")  
            sd.play(data, fs, device=self.speaker_idx, blocking=(not asynchronous), loop=loop)

    def interrupt(self):
        print("Audio interrupted")
        sd.stop()

    def play_sounddevice(self, file):
        data, fs = sf.read(file, dtype="float32")  
        sd.play(data, fs, device=self.speaker_idx, blocking=True)

    def play_output_stream(self, file):
        event = threading.Event()
        
        with sf.SoundFile(file) as wf:
            def callback(outdata, frames, time, status):
                data = wf.buffer_read(frames, dtype="float32")
                if len(outdata) > len(data):
                    outdata[:len(data)] = data
                    outdata[len(data):] = b"\x00" * (len(outdata) - len(data))
                    raise sd.CallbackStop
                else:
                    outdata[:] = data

                stream = sd.RawOutputStream(samplerate=wf.samplerate,
                                            device=self.speaker_idx,
                                            dtype="float32",
                                            channels=wf.channels,
                                            callback=callback,
                                            blocksize=1024,
                                            finished_callback=event.set)
                with stream:
                    event.wait()