import requests
import wave
import time
import threading
import alsaaudio

from node import config
from node.listener import Listener
from node.audio_player import AudioPlayer
from node.processor import Processor
from node.timer import Timer
from node.utils.hardware import list_microphones, select_mic, get_supported_samplerates, list_speakers, select_speaker

class Node:
    def __init__(self, debug: bool):
        self.debug = debug

        self.initialize()

    def start(self):
        print('Starting node')
        self.running = True
        self.run()

    def stop(self):
        self.running = False

    def restart(self):
        self.stop()
        print('Restarting node...')
        self.initialize()
        self.start()

    def initialize(self):

        self.pause_flag = threading.Event()

        self.timer = None

        self.node_id = config.get('node_id')
        self.node_name = config.get('node_name')
        self.hub_ip = config.get('hub_ip')
        self.wake_word = config.get('wake_word')
        self.wakeup_sound = config.get('wakeup_sound')
        self.mic_idx = config.get('mic_index')
        self.speaker_idx = config.get('speaker_index')
        self.vad_sensitivity = config.get('vad_sensitivity')
        self.volume = config.get('volume')

        self.hub_api_url = f'http://{self.hub_ip}:{5010}/api'

        # MICROPHONE SETTINGS
        print('\nAvailable Microphones:')
        [print(f'- {mic}') for mic in list_microphones()]

        _, self.mic_tag = select_mic(self.mic_idx)

        print("\nMicrophone supported sample rates")
        rates = [16000, 48000, 32000, 8000]
        supported_rates = get_supported_samplerates(self.mic_idx, rates)
        [print(f'- {rate}') for rate in supported_rates]

        self.sample_rate = supported_rates[0]
        self.sample_width = 2
        self.audio_channels = 1

        # SPEAKER SETTINGS
        print('\nAvailable Speakers')
        [print(f'- {speaker}') for speaker in list_speakers()]

        _, self.speaker_tag = select_speaker(self.speaker_idx)

        # LISTENER SETTINGS
        print('\n\nNode Info')
        print('- ID:             ', self.node_id)
        print('- Name:           ', self.node_name)
        print('- HUB:            ', self.hub_ip)
        print('- Wake Word:      ', self.wake_word)
        print('IO Settings')
        print('- Microphone:     ', self.mic_tag)
        print('- Microphone IDX: ', self.mic_idx)
        print('- Sample Rate:    ', self.sample_rate)
        print('- Sample Width:   ', self.sample_width)
        print('- Audio Channels: ', self.audio_channels)
        print('- Speaker:        ', self.speaker_tag)

        self.set_volume(self.volume)
        
        # INITIALIZING COMPONENTS
        self.audio_player = AudioPlayer(self)
        self.listener = Listener(self, frames_per_buffer=1600)
        self.processor = Processor(self)
    
    def run(self):
        self.last_time_engaged = time.time()
        engaged = False
        while self.running:
            audio_data = self.listener.listen(engaged)
            engaged = self.processor.process_audio(audio_data)
            self.pause_flag.clear()

                
        print('Mainloop end')

    def set_volume(self, volume: int):
        if volume >= 0 and volume <= 100:
            mixer_card = alsaaudio.mixers(cardindex=self.speaker_idx)[0]
            mixer = alsaaudio.Mixer(mixer_card, cardindex=self.speaker_idx, device=mixer_card)
            mixer.setvolume(volume)
        else:
            print('Failed to set volume: (Out of range 0-1)')

    def set_timer(self, durration_seconds: int):
        if self.timer == None:
            def timer_finished():
                self.audio_player.play_audio_file('node/sounds/alarm.wav', asynchronous=True, loop=True)
            self.timer = Timer(durration_seconds, timer_finished)
            self.timer.start()

    def get_timer(self):
        if self.timer:
            return self.timer.remaining()
        else:
            return 0