import requests
import wave
import pydub
import time
from typing import List
import sounddevice as sd

from node import config
from node.listener import Listener
from node.audio_player import AudioPlayer
from node.utils.hardware import list_microphones, list_speakers, select_mic, select_speaker, get_supported_samplerates
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

        self.hub_api_url = f'http://{hub_ip}:{5010}/api'
        
        print('Available Microphones:')
        [print(mic) for mic in list_microphones()]

        _, mic_tag = select_mic(self.mic_index)

        samplerates = [16000, 48000, 32000, 8000]   # Try 16000 first because avoids downsampling on HUB for transcription
        self.sample_rate = 16000
        self.sample_width = 2
        self.channels = 1

        print(get_supported_samplerates(self.mic_index, samplerates))

        self.listener = Listener(wake_word=config.get("wake_word"),
                                device_idx=self.mic_index, 
                                sample_rate=self.sample_rate, 
                                sample_width=self.sample_width,
                                channels=self.channels,
                                sensitivity=vad_sensitivity)

        print('Available Speakers')
        [print(speaker) for speaker in list_speakers()]

        _, speaker_tag = select_speaker(self.speaker_index)

        self.audio_player = AudioPlayer(self.speaker_index)

        print('Node Info')
        print('- ID: ', self.node_name)
        print('- Name: ', self.node_name)
        print('- HUB: ', hub_ip)
        print('Settings')
        print('- Selected Mic: ', mic_tag)
        print('- Speaker Mic: ', speaker_tag)
        print('- Samplerate: ', self.sample_rate)
        print('- VAD Sensitivity: ', vad_sensitivity)

    def process_audio(self, audio_data: bytes):
        print('Sending to server')

        '''
        wf = wave.open('command.wav', 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(self.sample_rate)
        wf.writeframes(audio_data)
        wf.close()
        '''

        audio_data_str = audio_data.hex()

        time_sent = time.time()

        payload = {
            'command_audio_data_str': audio_data_str, 
            'command_audio_sample_rate': self.sample_rate, 
            'command_audio_sample_width': 2, 
            'command_audio_channels': 1, 
            'command_text': '',
            'node_callback': '', 
            'node_id': self.node_id,
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
                    print('Retrying in 5...')
                    time.sleep(5)

        if respond_response.status_code == 200:

            self.last_time_engaged = time_sent

            context = respond_response.json()

            response = context['response']

            print('Command: ', context['cleaned_command'])
            print('Response: ', context['response'])
            print('Deltas')
            print('- Transcribe: ', context['time_to_transcribe'])
            print('- Understand: ', context['time_to_understand'])
            print('- Synth: ', context['time_to_synthesize'])

            response_audio_data_str = context['response_audio_data_str']
            response_sample_rate = context['response_audio_sample_rate']
            response_sample_width = context['response_audio_sample_width']
            audio_bytes = bytes.fromhex(response_audio_data_str)

            if response is not None:
                self.audio_player.play_audio(audio_bytes, 
                                            response_sample_rate, 
                                            response_sample_width)
        else:
            print('HUB did not respond')

    def mainloop(self):
        self.last_time_engaged = time.time()
        while self.running:
            audio_data = self.listener.listen()
            self.process_audio(audio_data)
                
        print('Mainloop end')