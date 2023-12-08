import time
import os
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
        print("Starting node")
        self.running = True
        self.run()

    def stop(self):
        self.running = False

    def restart(self):
        self.stop()
        print("Restarting node...")
        self.initialize()
        self.start()

    def initialize(self):

        self.base_dir = os.path.realpath(os.path.dirname(__file__))
        self.sounds_dir = os.path.join(self.base_dir, 'sounds')
        self.file_dump = os.path.join(self.base_dir, 'file_dump')
        
        os.makedirs(self.sounds_dir, exist_ok=True)
        os.makedirs(self.file_dump, exist_ok=True)

        self.pause_flag = threading.Event()

        self.timer = None

        self.node_id = config.get("node_id")
        self.node_name = config.get("node_name")
        self.node_area = config.get("node_area")
        self.hub_ip = config.get("hub_ip")
        self.wake_word = config.get("wake_word")
        self.wakeup_sound = config.get("wakeup_sound")
        self.mic_idx = config.get("mic_index")
        self.speaker_idx = config.get("speaker_index")
        self.vad_sensitivity = config.get("vad_sensitivity")
        self.volume = config.get("volume")

        self.hub_api_url = f"http://{self.hub_ip}:{5010}/api"

        # MICROPHONE SETTINGS
        print("\nAvailable Microphones:")
        [print(f"- {mic}") for mic in list_microphones()]

        _, self.mic_tag = select_mic(self.mic_idx)

        print("\nMicrophone supported sample rates")
        rates = [16000, 48000, 32000, 8000]
        supported_rates = get_supported_samplerates(self.mic_idx, rates)
        [print(f"- {rate}") for rate in supported_rates]

        self.sample_rate = supported_rates[0]
        self.sample_width = 2
        self.audio_channels = 1

        # SPEAKER SETTINGS
        print("\nAvailable Speakers")
        [print(f"- {speaker}") for speaker in list_speakers()]

        _, self.speaker_tag = select_speaker(self.speaker_idx)

        # LISTENER SETTINGS
        print("\nNode Info")
        print(f"- ID:             {self.node_id}")
        print(f"- Name:           {self.node_name}")
        print(f"- HUB:            {self.hub_ip}")
        print(f"- Wake Word:      {self.wake_word}")
        print(f"\nIO Settings")
        print(f"- Microphone:     {self.mic_tag}")
        print(f"- Microphone IDX: {self.mic_idx}")
        print(f"- Sample Rate:    {self.sample_rate}")
        print(f"- Sample Width:   {self.sample_width}")
        print(f"- Audio Channels: {self.audio_channels}")
        print(f"- Speaker:        {self.speaker_tag}\n")

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

                
        print("Mainloop end")

    def set_volume(self, volume: int):
        if volume >= 0 and volume <= 100:
            mixer_card = alsaaudio.mixers(cardindex=self.speaker_idx)[0]
            mixer = alsaaudio.Mixer(mixer_card, cardindex=self.speaker_idx, device=mixer_card)
            mixer.setvolume(volume)
        else:
            print("Failed to set volume: (Out of range 0-1)")

    def set_timer(self, durration_seconds: int):
        if self.timer == None:
            def timer_finished():
                self.timer.cancel()
                self.timer = None
                self.audio_player.play_audio_file(os.path.join(self.file_dump, "alarm.wav"), asynchronous=True, loop=True)
            self.timer = Timer(durration_seconds, timer_finished)
            self.timer.start()

    def stop_timer(self):
        self.timer.cancel()
        self.timer = None

    def get_timer(self):
        if self.timer:
            return int(self.timer.remaining())
        else:
            return 0