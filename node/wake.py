import vosk
import os
import json

import numpy as np
from openwakeword.model import Model

vosk.SetLogLevel(-1)

class KaldiWake:
    def __init__(self,
                 node,
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
        pass

    def listen_for_wake_word(self, chunk: bytes):
        self.rec = vosk.KaldiRecognizer(self.model, 
                                        self.sample_rate,
                                        #f'["{self.wake_word}", "[unk]"]' This makes a lot of false positives for some reason
                                        )
        # Add audio frames to the Vosk recognizer
        if self.rec.AcceptWaveform(chunk):
            res = json.loads(self.rec.Result())
            #print(res)
            if self.wake_word in res["text"]:
                print("Wake word!")
                return True
            else:
                return False
        else:
            # Check if speech has started
            partial = json.loads(self.rec.PartialResult())
            #print(partial["partial"])
            if self.wake_word in partial["partial"]:
                print("Wake word!")
                return True

class OpenWakeWord:
    def __init__(self,
                 node,
                 wake_word: str,
                 inference_framework: str = 'onnx',
    ):
        self.node = node
        self.wake_word = wake_word
        self.inference_framework = inference_framework
        self.confidence_threshold = node.wake_word_conf_threshold
        self.model_file = os.path.join(node.wake_word_model_dump, f"{wake_word}.onnx")
        if not os.path.exists(self.model_file):
            raise RuntimeError("Wake word model file does not exist")
        
        self.owwModel = Model(wakeword_models=[self.model_file], 
                              enable_speex_noise_suppression=self.node.speex_noise_suppression,
                              vad_threshold=self.node.vad_threshold,
                              inference_framework=self.inference_framework
        )

    def reset(self):
        self.owwModel = Model(wakeword_models=[self.model_file], 
                              enable_speex_noise_suppression=self.node.speex_noise_suppression,
                              vad_threshold=self.node.vad_threshold,
                              inference_framework=self.inference_framework
        )

    def listen_for_wake_word(self, chunk: bytes):
        audio = np.frombuffer(chunk, dtype=np.int16)
        # Feed to openWakeWord model
        prediction = self.owwModel.predict(audio)
        #print(self.owwModel.prediction_buffer)
        if prediction[self.wake_word] > self.confidence_threshold: return True
        return False