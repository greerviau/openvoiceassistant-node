import requests
import wave
import pydub
import time
from typing import List
import sounddevice as sd

from node import config
from node.listener import VoskListener, WebRTCVADListener, SileroVADListener
from node.utils.hardware import list_microphones, list_speakers, select_mic, select_speaker, get_supported_samplerates
from node.utils.audio import play_audio_file
#from .utils import noisereduce

class Node:
    def __init__(self, debug: bool):
        self.set_config()
        self.debug = debug

    def start(self):
        print('Starting node')
        self.running = True
        self.mainloop()

    def stop(self):
        self.running = False

    def restart(self):
        self.stop()
        print('Restarting node...')
        self.set_config()
        self.start()

    def set_config(self):
        self.node_id = config.get('node_id')
        self.node_name = config.get('node_name')
        self.mic_index = config.get('mic_index')
        self.speaker_index = config.get('speaker_index')
        hub_ip = config.get('hub_ip')
        vad_sensitivity = config.get('vad_sensitivity')
        min_audio_sample_length = config.get('min_audio_sample_length')
        audio_sample_buffer_length = config.get('audio_sample_buffer_length')

        print(f'Node Name: {self.node_name}')

        self.hub_api_url = f'http://{hub_ip}:{5010}/api'
        
        print('Available Microphones:')
        [print(mic) for mic in list_microphones()]

        _, mic_tag = select_mic(self.mic_index)

        #devinfo = self.paudio.get_device_info_by_index(self.mic_index)  # Or whatever device you care about

        #self.MIN_SAMPLE_FRAMES = int(min_audio_sample_length * 1000 / self.INTERVAL)

        #self.BUFFER_SIZE = int(audio_sample_buffer_length * 1000) / self.INTERVAL

        samplerates = [16000, 48000, 32000, 8000]   # Try 16000 first because avoids downsampling on HUB for transcription
        self.SAMPLERATE = 16000

        print(get_supported_samplerates(self.mic_index, samplerates))

        self.listener = VoskListener(config.get("wake_word"), self.mic_index, self.SAMPLERATE, vad_sensitivity)

        print('Available Speakers')
        [print(speaker) for speaker in list_speakers()]

        _, speaker_tag = select_speaker(self.speaker_index)

        print('Settings')
        print('Selected Mic: ', mic_tag)
        print('Samplerate: ', self.SAMPLERATE)
        print('Speaker Mic: ', speaker_tag)
        #print('Min Sample Frames: ', self.MIN_SAMPLE_FRAMES)

    def process_audio(self, audio_data: bytes):
        print('Sending audio')

        audio_data_str = audio_data.hex()

        time_sent = time.time()

        payload = {
            'command_audio_data_str': audio_data_str, 
            'command_audio_sample_rate': self.SAMPLERATE, 
            'command_audio_sample_width': 2, 
            'command_audio_channels': 1, 
            'command_text': '',
            'node_callback': '', 
            'node_id': self.node_id, 
            'engage': False,
            'last_time_engaged': self.last_time_engaged,
            'time_sent': time_sent
        }

        try:
            respond_response = requests.post(
                f'{self.hub_api_url}/respond/audio',
                json=payload
            )
        except Exception as e:
            print(repr(e))
            print('Lost connection to HUB')
            connect = False
            while not connect:
                try:
                    retry_response = requests.get(
                        self.hub_api_url,
                        json=payload,
                        timeout=30
                    )
                    if retry_response.status_code == 200:
                        connect = True
                        print('\nConnected')
                    else:
                        raise
                except:
                    print('Retrying...')
                    time.sleep(1)

        if respond_response.status_code == 200:

            self.last_time_engaged = time_sent

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
            
            #wave_obj = sa.WaveObject.from_wave_file("response.wav")
            #play_obj = wave_obj.play()
            #play_obj.wait_done()
            play_audio_file('response.wav', device_idx=self.speaker_index)
        else:
            print('Hub did not respond')

    def mainloop(self):
        print('Microphone stream started')

        self.last_time_engaged = time.time()
        print('Listening...')
        while self.running:
            audio_data = self.listener.listen(False)
            self.process_audio(audio_data)
                
        print('Mainloop end')