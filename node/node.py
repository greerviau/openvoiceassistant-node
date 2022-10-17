import pyaudio
import webrtcvad
import base64
import requests
import numpy as np
import wave
import pydub
from pydub.playback import play
import simpleaudio as sa
import time
from io import BytesIO

from .config import Configuration

#from utils import noisereduce


class Node:
    def __init__(self, config: Configuration, debug: bool):
        self.set_config(config)
        self.debug = debug

    def start(self):
        print('Starting node')
        self.running = True
        self.mainloop()

    def stop(self):
        self.running = False

    def set_config(self, config: Configuration):
        self.config = config
        self.node_id = config.get('node_id')
        self.mic_index = config.get('mic_index')
        self.hub_api_uri = config.get('hub_api_url')

        self.vad = webrtcvad.Vad()
        self.vad.set_mode(3)
        
        self.paudio = pyaudio.PyAudio()

        devinfo = self.paudio.get_device_info_by_index(self.mic_index)  # Or whatever device you care about.

        self.INTERVAL = 30   # ms
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.SAMPLE_WIDTH = self.paudio.get_sample_size(self.FORMAT)

        supported_rates = [16000, 48000, 32000, 8000]
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
            #audio_data = np.fromstring(data, dtype=np.int16)
            #reduce_noise = noisereduce.reduce_noise(y=audio_data, sr=self.SAMPLE_RATE)
            is_speech = self.vad.is_speech(data, self.SAMPLE_RATE)
            #print('Is speech: ', is_speech)
            if is_speech:
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
                print('Done')
                if len(frames) > 40:
                    print('Sending audio')

                    audio_data = b''.join(frames)

                    wf = wave.open('command.wav', 'wb')
                    wf.setnchannels(self.CHANNELS)
                    wf.setsampwidth(self.SAMPLE_WIDTH)
                    wf.setframerate(self.SAMPLE_RATE)
                    wf.writeframes(audio_data)
                    wf.close()

                    audio_data_str = audio_data.hex()

                    time_sent = time.time()

                    payload = {
                        'command_audio_data_str': audio_data_str, 
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
                    except Exception as e:
                        print(repr(e))
                        print('Lost connection to HUB')
                        connect = False
                        while not connect:
                            try:
                                retry_response = requests.get(
                                    self.hub_api_uri,
                                    json=payload
                                )
                                if retry_response.status_code == 200:
                                    connect = True
                                    print('\nConnected')
                                else:
                                    raise
                            except:
                                print('\rRetrying...', end='')
                                time.sleep(1)
                            
                        continue

                    if respond_response.status_code == 200:

                        last_time_engaged = time_sent

                        context = respond_response.json()

                        print('TTTranscribe: ', context['time_to_transcribe'])
                        print('TTUnderstand: ', context['time_to_understand'])
                        print('TTSynth: ', context['time_to_synthesize'])

                        print('Command: ', context['command'])
                        response_audio_data_str = context['response_audio_data_str']
                        response_sample_rate = context['response_sample_rate']
                        response_sample_width = context['response_sample_width']
                        print('Samplerate: ', response_sample_rate)
                        print('Samplewidth: ', response_sample_width)
                        audio_bytes = bytes.fromhex(response_audio_data_str)

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
                            wave_obj = sa.WaveObject.from_wave_file("response.wav")
                            play_obj = wave_obj.play()
                            play_obj.wait_done()
                    else:
                        print('Hub did not respond')

                frames = []
                buffer = []
                done = False
                
        print('Mainloop end')