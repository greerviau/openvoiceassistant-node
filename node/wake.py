import queue
import vosk
import sounddevice as sd
import json
import wave
import collections
from node.stream import Stream

class KaldiWake:
    def __init__(self,
                 wake_word: str,
                 sample_rate: int
    ):
        self.wake_word = wake_word
        self.sample_rate = sample_rate
        self.model = vosk.Model(lang='en-us')
    
    def listen_for_wake_word(self, stream: Stream):
        while True:
            rec = vosk.KaldiRecognizer(self.model, 
                                        self.sample_rate,
                                        f'["{self.wake_word}"]')
            print('Listening for wake word...')
            while True:
                chunk = stream.get_chunk()

                # Add audio frames to the Vosk recognizer
                if rec.AcceptWaveform(chunk):
                    res = json.loads(rec.Result())
                    #print(res)
                    print('Wake word!')
                    if res['text']:
                        return
                    else:
                        break
                else:
                    # Check if speech has started
                    partial = json.loads(rec.PartialResult())
                    #print(partial["partial"])

