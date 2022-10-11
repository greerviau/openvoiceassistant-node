import pyaudio
import webrtcvad
import base64
import requests
import numpy as np
import wave
import pydub
from pydub.playback import play
from playsound import playsound
import time
from io import BytesIO

from utils import noisereduce


class Node:
    def __init__(self, node_id, mic_index, hub_api_uri, debug):
        self.node_id = node_id
        self.mic_index = mic_index
        self.hub_api_uri = hub_api_uri
        self.debug = debug

        self.vad = webrtcvad.Vad()
        self.vad.set_mode(3)
        
        self.paudio = pyaudio.PyAudio()

        devinfo = self.paudio.get_device_info_by_index(self.mic_index)  # Or whatever device you care about.

        self.INTERVAL = 30   # ms
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.SAMPLE_WIDTH = self.paudio.get_sample_size(self.FORMAT)

        supported_rates = [48000, 32000, 16000, 8000]
        self.SAMPLE_RATE = None
        for rate in supported_rates:
            if self.paudio.is_format_supported(rate, input_device=devinfo['index'], input_channels=self.CHANNELS, input_format=self.FORMAT):
                self.SAMPLE_RATE = rate
                break

        if self.SAMPLE_RATE is None:
            raise RuntimeError('Failed to set samplerate')

        self.CHUNK = int(self.SAMPLE_RATE * self.INTERVAL / 1000) 

        print('Mic Settings')
        print('Interval: ', self.INTERVAL)
        print('Channels: ', self.CHANNELS)
        print('Samplerate: ', self.SAMPLE_RATE)
        print('Chunk Size: ', self.CHUNK)

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
                rate=self.SAMPLE_RATE,
                input=True,
                frames_per_buffer=self.CHUNK)
        
        print('Microphone stream started')

        last_time_engaged = time.time()

        buffer = []
        frames = []
        voice_detected = False
        done = False
        while self.running:
            data = stream.read(self.CHUNK, exception_on_overflow=False)
            audio_data = np.fromstring(data, dtype=np.int16)
            reduce_noise = noisereduce.reduce_noise(y=audio_data, sr=self.SAMPLE_RATE)
            is_speech = self.vad.is_speech(reduce_noise.tobytes(), self.SAMPLE_RATE)
            print('Is speech: ', is_speech)
            if is_speech:
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
                self.__log('Done')
                if len(frames) > 40:
                    self.__log('Sending audio')

                    audio_data = b''.join(frames)

                    wf = wave.open('command.wav', 'wb')
                    wf.setnchannels(self.CHANNELS)
                    wf.setsampwidth(self.SAMPLE_WIDTH)
                    wf.setframerate(self.SAMPLE_RATE)
                    wf.writeframes(audio_data)
                    wf.close()

                    raw_base64 = base64.b64encode(audio_data).decode('utf-8')

                    time_sent = time.time()

                    payload = {
                        'command_audio_data_b64': raw_base64, 
                        'command_audio_sample_rate': self.SAMPLE_RATE, 
                        'command_audio_sample_width': self.SAMPLE_WIDTH, 
                        'command_audio_channels': self.CHANNELS, 
                        'command_text': '',
                        'node_callback': '', 
                        'node_id': self.node_id, 
                        'engage': False,
                        'last_time_engaged': last_time_engaged,
                        'time_sent': time_sent
                    }

                    try:
                        respond_response = requests.post(
                            f'{self.hub_api_uri}/respond/audio',
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
                        response_audio_data_b64 = context['response_audio_data_b64']
                        response_sample_rate = context['response_sample_rate']
                        response_sample_width = context['response_sample_width']
                        print('Samplerate: ', response_sample_rate)
                        print('Samplewidth: ', response_sample_width)
                        audio_bytes = base64.b64decode(response_audio_data_b64.encode('utf-8'))

                        audio_segment = pydub.AudioSegment(
                            audio_bytes, 
                            frame_rate=response_sample_rate,
                            sample_width=response_sample_width, 
                            channels=1
                        )
                        audio_segment.export('response.wav', format='wav')
                        try:
                            play(audio_segment)
                        except:
                            playsound('response.wav')

                frames = []
                buffer = []
                done = False