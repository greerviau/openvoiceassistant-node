import sounddevice as sd
import numpy as np
from openwakeword.model import Model
import time

# Get microphone stream
CHANNELS = 1
RATE = 16000
CHUNK = 1280

owwModel = Model(inference_framework="tflite")

n_models = len(owwModel.models.keys())

# Run capture loop continuosly, checking for wakewords
if __name__ == "__main__":
    # Generate output string header
    print("\n\n")
    print("#"*100)
    print("Listening for wakewords...")
    print("#"*100)
    
    while True:    
        owwModel.reset()
        with sd.InputStream(samplerate=RATE, 
                            channels=CHANNELS, 
                            blocksize=CHUNK,
                            dtype="int16") as stream:
            while True:
                # Get audio
                chunk, _ = stream.read(CHUNK)
                audio = np.frombuffer(chunk, dtype=np.int16)

                # Feed to openWakeWord model
                prediction = owwModel.predict(audio)

                if prediction["alexa"] > 0.8:
                    print("Wake Word!")
                    break
        print("Go somewhere else")
        time.sleep(1)
