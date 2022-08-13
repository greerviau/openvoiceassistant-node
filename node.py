import speech_recognition as sr
import pyaudio
import webrtcvad
import base64
import requests
import numpy as np
import wave
import pydub
from pydub.playback import play
import time
import threading
from io import BytesIO


class Node:
    def __init__(self, mic_index, hub_api_uri, cli, debug):
        self.recog = sr.Recognizer()
        self.mic_index = mic_index
        self.hub_api_uri = hub_api_uri
        self.cli = cli
        self.debug = debug
        

        self.vad = webrtcvad.Vad()
        self.vad.set_mode(3)

        self.paudio = pyaudio.PyAudio()

        devinfo = self.paudio.get_device_info_by_index(self.mic_index)  # Or whatever device you care about.
        if self.paudio.is_format_supported(48000,  # Sample rate
                                input_device=devinfo['index'],
                                input_channels=devinfo['maxInputChannels'],
                                input_format=pyaudio.paInt16):
            print('Supported')
        else:
            print('Not supported')

        self.INTERVAL = 30   # ms
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 48000
        self.CHUNK = int(self.RATE * self.INTERVAL / 1000) 

        self.running = True

    def __log(self, text, end='\n'):
        if self.debug:
            print(text, end=end)

    def start(self):
        print('Starting node')
        self.mainloop()

    def mainloop(self):
        stream = self.paudio.open(format=self.FORMAT,
                channels=self.CHANNELS,
                input_device_index = self.mic_index,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK)

        buffer = []
        frames = []
        voice_detected = False
        done = False
        while self.running:
            data = stream.read(self.CHUNK)
            if self.vad.is_speech(data, self.RATE):
                print('\rRecording...   ', end='')
                voice_detected = True
                if len(buffer) > 0:
                    frames.extend(buffer)
                    buffer = []
                else:
                    frames.append(data)
            elif voice_detected:
                print('\rRecording...   ', end='')
                buffer.append(data)
                if len(buffer) > 20:
                    frames.extend(buffer)
                    buffer = []
                    done = True
                    voice_detected = False
            else:
                print('\rListening...   ', end='')
                buffer.append(data)
                if len(buffer) > 10:
                    buffer.pop(0)
            
            if done:
                if len(frames) > 40:
                    with BytesIO() as wave_file:
                        wf = wave.open(wave_file, 'wb')
                        wf.setnchannels(self.CHANNELS)
                        wf.setsampwidth(self.paudio.get_sample_size(self.FORMAT))
                        wf.setframerate(self.RATE)
                        wf.writeframes(b''.join(frames))
                        wf.close()
                        raw = wave_file.getvalue()

                    raw_base64 = base64.b64encode(raw).decode('utf-8')

                    payload = {'samplerate': self.RATE, 'callback': '', 'audio_file': raw_base64, 'room_id': '1', 'engaged': True}
                    response = requests.post(
                        f'http://{self.hub_api_uri}/respond_to_audio',
                        json=payload
                    )

                    if response.status_code == 200:
                        understanding = response.json()

                        self.__log(understanding['command'])
                        audio_data = understanding['audio_data']
                        audio_buffer = base64.b64decode(audio_data)
                        audio = np.frombuffer(audio_buffer, dtype=np.int16)

                        audio_segment = pydub.AudioSegment(
                            audio.tobytes(), 
                            frame_rate=22050,
                            sample_width=audio.dtype.itemsize, 
                            channels=1
                        )
                        play(audio_segment)

                frames = []
                buffer = []
                done = False