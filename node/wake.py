import os
import numpy as np
import openwakeword
import logging
logger = logging.getLogger("wake")

from openwakeword.model import Model

from node.dir import WAKEWORDMODELSDIR

class OpenWakeWord:
    def __init__(self,
                 node,
                 wake_word: str,
                 inference_framework: str = 'onnx',
    ):
        self.node = node
        self.wake_word = wake_word
        inference_framework = inference_framework
        self.confidence_threshold = node.wake_word_conf_threshold

        model_file = os.path.join(WAKEWORDMODELSDIR, f"{wake_word}.onnx")
        if not os.path.exists(model_file):
            raise RuntimeError("Wake word model file does not exist")
        
        openwakeword.utils.download_models()
        self.owwModel = Model(wakeword_models=[model_file], 
                              enable_speex_noise_suppression=self.node.speex_noise_suppression,
                              vad_threshold=self.node.vad_threshold,
                              inference_framework=inference_framework
        )

    def reset(self):
        self.owwModel.reset()

    def listen_for_wake_word(self, chunk: bytes) -> bool:
        audio = np.frombuffer(chunk, dtype=np.int16)
        # Feed to openWakeWord model
        prediction = self.owwModel.predict(audio)
        logger.debug(prediction)
        if prediction[self.wake_word] > self.confidence_threshold: return True
        return False