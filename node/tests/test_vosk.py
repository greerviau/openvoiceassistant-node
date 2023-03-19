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
model = vosk.Model("../../model")
rec = vosk.KaldiRecognizer(model, samplerate)

# Define a buffer to store audio frames
buffer = queue.Queue()
# Define a recording buffer for the start of the recording
recording_buffer = collections.deque(maxlen=2)

# Define a flag to indicate if speech has started
speech_started = False

# Define a callback function to process audio data from the stream
def callback(indata, frames, time, status):
    # Add audio data to the buffer
    buffer.put(bytes(indata))

# Set up the sounddevice stream
with sd.RawInputStream(samplerate=samplerate, device=DEVICE, callback=callback, blocksize=8000, dtype="int16"):
    print("Listening for hotword...")
    dump_fn = None
    while True:
        try:
            # Get audio frames from the buffer
            frame = buffer.get()

            # Add audio frames to the Vosk recognizer
            if rec.AcceptWaveform(frame):
                print('Recording stopped')
                print(rec.Result())
                dump_fn.close()
                dump_fn = None
                speech_started = False
                recording_buffer.clear()    # Clear out the recording buffer
            else:
                # Check if speech has started
                partial = json.loads(rec.PartialResult())
                print(partial)
                text = partial["partial"]
                if HOTWORD in text.split() and not speech_started:  # Check for hotword
                    print("Hotword detected")
                    dump_fn = wave.open("audio.wav", "wb")  # Open file to record audio
                    dump_fn.setnchannels(1)
                    dump_fn.setsampwidth(2)
                    dump_fn.setframerate(samplerate)
                    for f in recording_buffer:  # Write the recording buffer to the file
                        dump_fn.writeframes(f)
                    speech_started = True
                    print('Recording started...')

            # If we havent detected the hotword, write audio frames to the buffer
            # The recording buffer avoids a cutoff at the begining of the recording
            if not speech_started:
                recording_buffer.append(frame)
                
            # If we have detected the hotword start writing audio frames to file
            if dump_fn is not None and speech_started:
                dump_fn.writeframes(frame)

        except KeyboardInterrupt:
            break
