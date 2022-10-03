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
from io import BytesIO


class Node:
    def __init__(self, node_id, mic_index, hub_api_uri, debug):
        self.recog = sr.Recognizer()
        self.node_id = node_id
        self.mic_index = mic_index
        self.hub_api_uri = hub_api_uri
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

    def __log(self, text='', end='\n'):
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
        
        print('Microphone stream started')

        last_time_engaged = time.time()

        buffer = []
        frames = []
        voice_detected = False
        done = False
        while self.running:
            data = stream.read(self.CHUNK)
            if self.vad.is_speech(data, self.RATE):
                self.__log('\rRecording...   ', end='')
                voice_detected = True
                if len(buffer) > 0:
                    frames.extend(buffer)
                    buffer = []
                else:
                    frames.append(data)
            elif voice_detected:
                self.__log('\rRecording...   ', end='')
                buffer.append(data)
                if len(buffer) > 20:
                    frames.extend(buffer)
                    buffer = []
                    done = True
                    voice_detected = False
            else:
                self.__log('\rListening...   ', end='')
                buffer.append(data)
                if len(buffer) > 10:
                    buffer.pop(0)
            
            if done:
                print('Done')
                if len(frames) > 40:
                    self.__log()
                    with BytesIO() as wave_file:
                        wf = wave.open(wave_file, 'wb')
                        wf.setnchannels(self.CHANNELS)
                        wf.setsampwidth(self.paudio.get_sample_size(self.FORMAT))
                        wf.setframerate(self.RATE)
                        wf.writeframes(b''.join(frames))
                        wf.close()
                        raw = wave_file.getvalue()

                    raw_base64 = base64.b64encode(raw).decode('utf-8')

                    time_sent = time.time()

                    payload = {
                        'audio_file': raw_base64, 
                        'samplerate': self.RATE, 
                        'callback': '', 
                        'node_id': self.node_id, 
                        'last_time_engaged': last_time_engaged,
                        'time_sent': time_sent
                    }

                    try:
                        respond_response = requests.post(
                            f'{self.hub_api_uri}/respond_to_audio',
                            json=payload
                        )
                    except:
                        self.__log('Lost connection to HUB')
                        connect = False
                        while not connect:
                            try:
                                retry_response = requests.get(
                                    self.hub_api_uri,
                                    json=payload
                                )
                                if retry_response.status_code == 200:
                                    connect = True
                                    self.__log('\nConnected')
                                else:
                                    raise
                            except:
                                self.__log('\rRetrying...', end='')
                                time.sleep(1)
                            
                        continue

                    if respond_response.status_code == 200:

                        last_time_engaged = time_sent

                        context = respond_response.json()

                        if 'callout' in context:
                            callout = context['callout']

                        self.__log(context['command'])
                        audio_data = context['audio_data']
                        sample_rate = context['sample_rate']
                        sample_width = context['sample_width']
                        audio_bytes = base64.b64decode(audio_data)

                        audio_segment = pydub.AudioSegment(
                            audio_bytes, 
                            frame_rate=sample_rate,
                            sample_width=sample_width, 
                            channels=1
                        )
                        play(audio_segment)

                frames = []
                buffer = []
                done = False