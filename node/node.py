import requests
import wave
import pydub
import time
from typing import List
import sounddevice as sd
import threading

from node import config
from node.utils.audio import save_wave
from node.listener import Listener
from node.stream import PyaudioStream
from node.audio_player import PyaudioPlayer
from node.utils.hardware import list_microphones, list_speakers, select_mic, select_speaker, get_supported_samplerates, get_input_channels
#from .utils import noisereduce

class Node:
    def __init__(self, debug: bool):
        self.debug = debug

        self.hub_callback = ''

        self.pause_flag = threading.Event()

        self.alarm_thread = None
        self.alarm_flag = threading.Event()

        self.initialize()

    def start(self):
        print('Starting node')
        self.running = True
        self.mainloop()

    def stop(self):
        self.running = False

    def restart(self):
        self.stop()
        print('Restarting node...')
        self.initialize()
        self.start()

    def initialize(self):
        self.node_id = config.get('node_id')
        self.node_name = config.get('node_name')
        self.mic_idx = config.get('mic_index')
        self.speaker_idx = config.get('speaker_index')
        self.hub_ip = config.get('hub_ip')
        self.vad_sensitivity = config.get('vad_sensitivity')

        self.hub_api_url = f'http://{self.hub_ip}:{5010}/api'
        
        print('Available Microphones:')
        [print(mic) for mic in list_microphones()]

        _, mic_tag = select_mic(self.mic_idx)

        rates = [16000, 48000, 32000, 8000]
        supported_rates = get_supported_samplerates(self.mic_idx, rates)
        print("Microphone supported sample rates")
        for rate in supported_rates:
            print(rate)

        self.sample_rate = supported_rates[0]
        self.sample_width = 2
        self.channels = 1
        
        print('Available Speakers')
        [print(speaker) for speaker in list_speakers()]

        _, speaker_tag = select_speaker(self.speaker_idx)

        self.audio_player = PyaudioPlayer(self)

        self.stream = PyaudioStream(self, frames_per_buffer=1200)
        
        self.stream.start_stream()

        self.listener = Listener(self)

        print('Node Info')
        print('- ID: ', self.node_id)
        print('- Name: ', self.node_name)
        print('- HUB: ', self.hub_ip)
        print('Settings')
        print('- Microphone: ', mic_tag)
        print('- Speaker: ', speaker_tag)
        print('- Sample Rate: ', self.sample_rate)
        print('- Sample Width: ', self.sample_width)
        print('- Channels: ', self.channels)
        print('- VAD Sensitivity: ', self.vad_sensitivity)

    def process_audio(self, audio_data: bytes):
        print('Sending to server')

        engaged = False

        wf = wave.open('command.wav', 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.sample_width)
        wf.setframerate(self.sample_rate)
        wf.writeframes(audio_data)
        wf.close()

        time_sent = time.time()

        payload = {
            'node_id': self.node_id,
            'command_audio_data_hex': audio_data.hex(), 
            'command_audio_sample_rate': self.sample_rate, 
            'command_audio_sample_width': self.sample_width, 
            'command_audio_channels': self.channels,
            'hub_callback': self.hub_callback,
            'last_time_engaged': self.last_time_engaged,
            'time_sent': time_sent
        }

        try:
            respond_response = requests.post(
                f'{self.hub_api_url}/respond/audio',
                json=payload,
                timeout=5
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
            self.hub_callback = context['hub_callback']

            if self.hub_callback:
                engaged = True

            print('Command: ', context['cleaned_command'])
            print('Response: ', context['response'])
            print('Deltas')
            print('- Transcribe: ', context['time_to_transcribe'])
            print('- Understand: ', context['time_to_understand'])
            print('- Synth: ', context['time_to_synthesize'])

            response_audio_data_hex = context['response_audio_data_hex']
            response_sample_rate = context['response_audio_sample_rate']
            response_sample_width = context['response_audio_sample_width']

            if response is not None:

                save_wave('response.wav',
                            bytes.fromhex(response_audio_data_hex),
                            response_sample_rate,
                            response_sample_width)
                
                self.audio_player.play_audio_file('response.wav')
                time.sleep(0.2)
        else:
            print('HUB did not respond')

        return engaged

    def mainloop(self):
        self.last_time_engaged = time.time()
        engaged = False
        while self.running:
            audio_data = self.listener.listen(engaged)
            engaged = self.process_audio(audio_data)
            self.pause_flag.clear()

                
        print('Mainloop end')

    def play_alarm(self):
        def alarm():
            while not self.alarm_flag.is_set():
                if not self.pause_flag.is_set():
                    print('Play alarm')
                    self.audio_player.play_audio_file('node/sounds/alarm.wav')
                time.sleep(0.1)
            print('Alarm finished')
        if not self.alarm_thread:
            self.alarm_thread = threading.Thread(target=alarm, daemon=True)
            self.alarm_thread.start()

    def stop_alarm(self):
        if self.alarm_thread:
            self.alarm_flag.set()
            self.alarm_thread = None