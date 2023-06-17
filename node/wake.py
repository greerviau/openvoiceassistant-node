import vosk
import json

from node.stream import Stream

vosk.SetLogLevel(-1)

class KaldiWake:
    def __init__(self,
                 wake_word: str,
                 sample_rate: int
    ):
        self.wake_word = wake_word
        self.sample_rate = sample_rate
        try:
            self.model = vosk.Model(lang='en-us')
        except:
            self.model = vosk.Model('vosk_model')
    
    def listen_for_wake_word(self, stream: Stream):
        print('Listening for wake word...')
        while True:
            rec = vosk.KaldiRecognizer(self.model, 
                                        self.sample_rate,
                                        #f'["{self.wake_word}", "[unk]"]'
                                        )
            while True:
                chunk = stream.get_chunk()

                # Add audio frames to the Vosk recognizer
                if rec.AcceptWaveform(chunk):
                    res = json.loads(rec.Result())
                    #print(res)
                    if self.wake_word in res['text']:
                        print('Wake word!')
                        return
                    else:
                        break
                else:
                    # Check if speech has started
                    partial = json.loads(rec.PartialResult())
                    #print(partial["partial"])
                    if self.wake_word in partial["partial"]:
                        print('Wake word!')
                        return

