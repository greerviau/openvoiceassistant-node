import queue
import vosk
import sounddevice as sd
import json
import wave
import collections

# Define hotword to trigger audio recording
HOTWORD = "computer"
DEVICE = 0

print(sd.query_devices())

device_info = sd.query_devices(DEVICE, "input")
# soundfile expects an int, sounddevice provides a float:
samplerate = int(device_info["default_samplerate"])

# Define the Vosk model and its configuration
model = vosk.Model(lang='en-us')
rec = vosk.KaldiRecognizer(model, 
                           samplerate,
                           '["computer"]')

# Define a buffer to store audio frames
buffer = queue.Queue()

# Define a callback function to process audio data from the stream
def callback(indata, frames, time, status):
    # Add audio data to the buffer
    buffer.put(bytes(indata))

# Set up the sounddevice stream
with sd.RawInputStream(samplerate=samplerate, device=DEVICE, callback=callback, blocksize=8000, dtype="int16"):
    while True:
        try:
            # Get audio frames from the buffer
            frame = buffer.get()

            # Add audio frames to the Vosk recognizer
            if rec.AcceptWaveform(frame):
                print(rec.Result())
            else:
                # Check if speech has started
                partial = json.loads(rec.PartialResult())
                print(partial["partial"])


        except KeyboardInterrupt:
            break
