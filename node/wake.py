import vosk
import json

vosk.SetLogLevel(-1)

class KaldiWake:
    def __init__(self,
                 wake_word: str,
                 sample_rate: int
    ):
        self.wake_word = wake_word
        self.sample_rate = sample_rate
        try:
            self.model = vosk.Model(lang="en-us")
        except:
            self.model = vosk.Model("vosk_model")

    def reset(self):
        self.rec = vosk.KaldiRecognizer(self.model, 
                                        self.sample_rate,
                                        #f"["{self.wake_word}", "[unk]"]"
                                        )
    
    def listen_for_wake_word(self, chunk: bytes):
        # Add audio frames to the Vosk recognizer
        if self.rec.AcceptWaveform(chunk):
            res = json.loads(self.rec.Result())
            print(res)
            if self.wake_word in res["text"]:
                print("Wake word!")
                return True
            else:
                return False
        else:
            # Check if speech has started
            partial = json.loads(self.rec.PartialResult())
            print(partial["partial"])
            if self.wake_word in partial["partial"]:
                print("Wake word!")
                return True

