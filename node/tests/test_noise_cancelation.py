import pyaudio
import wave
import simpleaudio as sa
import threading

INTERVAL = 30
RATE = 16000
CHUNK = int(RATE * INTERVAL / 1000)
FORMAT = pyaudio.paInt16
CHANNELS = 1
RECORD_SECONDS = 10
WAVE_OUTPUT_FILENAME = "output.wav"

p = pyaudio.PyAudio()

stream = p.open(format=FORMAT,
                channels=1,
                rate=RATE,
                input=True,
                output=True,
                input_device_index=1,
                frames_per_buffer=CHUNK)

def play_audio():
    print('Playing audio...')
    wave_obj = sa.WaveObject.from_wave_file("recording.wav")
    play_obj = wave_obj.play()

play_thread = threading.Thread(target=play_audio)
play_thread.start()

print('Recording...')

frames = []

for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(data)

print("Done recording")

stream.stop_stream()
stream.close()
p.terminate()

wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(p.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(b''.join(frames))
wf.close()
