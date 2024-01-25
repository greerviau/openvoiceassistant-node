import time
import os

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

        self.timer = None

        self.node_id = config.get("node_id")
        self.node_name = config.get("node_name")
        self.node_area = config.get("node_area")
        self.hub_ip = config.get("hub_ip")
        self.wake_word_engine = config.get("wake_word_engine")
        self.wake_word = config.get("wake_word")
        self.wakeup_sound = config.get("wakeup_sound")
        self.wake_word_conf_threshold = config.get("wake_word_conf_threshold")
        self.mic_idx = config.get("mic_index")
        self.speaker_idx = config.get("speaker_index")
        self.vad_sensitivity = config.get("vad_sensitivity")
        self.vad_threshold = config.get("vad_threshold")
        self.speex_noise_suppression = config.get("speex_noise_suppression")
        self.volume = config.get("volume")

        self.hub_api_url = f"http://{self.hub_ip}:{7123}/api"

        # MICROPHONE SETTINGS
        print("\nAvailable Microphones:")
        [print(f"- {mic}") for mic in list_microphones()]

        _, self.mic_tag = select_mic(self.mic_idx)

        print("\nMicrophone supported sample rates")
        rates = [48000, 32000, 16000, 8000]
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
        print(f"- Wake Engine:    {self.wake_word_engine}")
        print(f"- Wake Word:      {self.wake_word}")
        print(f"- Wake Conf:      {self.wake_word_conf_threshold}")
        print(f"- Vad Thresh:     {self.vad_threshold}")
        print(f"\nIO Settings")
        print(f"- Microphone:     {self.mic_tag}")
        print(f"- Microphone IDX: {self.mic_idx}")
        print(f"- Speaker:        {self.speaker_tag}")
        print(f"- Speaker IDX:    {self.speaker_idx}")
        print(f"- Sample Rate:    {self.sample_rate}")
        print(f"- Sample Width:   {self.sample_width}")
        print(f"- Audio Channels: {self.audio_channels}")

        try:
            from node.utils.leds import Pixels, Respeaker4MicHat
            if "seeed-4mic-voicecard" in self.mic_tag:
                self.led_controller = Respeaker4MicHat()
            else:
                self.led_controller = Pixels()
        except:
            self.led_controller = None

        try:
            import alsaaudio
            mixer_card = alsaaudio.mixers(cardindex=self.speaker_idx)[0]
            self.mixer = alsaaudio.Mixer(mixer_card, cardindex=self.speaker_idx, device=mixer_card)
            self.set_volume(self.volume)
        except:
            self.mixer = None

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
            if self.led_controller:
                self.led_controller.off()

                
        print("Mainloop end")

    def set_volume(self, volume: int):
        if volume >= 0 and volume <= 100:
            if self.mixer:
                self.mixer.setvolume(volume)
        else:
            print("Failed to set volume: (Out of range 0-1)")

    def set_timer(self, durration_seconds: int):
        if self.timer == None:
            def timer_finished():
                self.timer.cancel()
                self.timer = None
                self.audio_player.play_audio_file(os.path.join(self.sounds_dir, "alarm.wav"), asynchronous=True, loop=True)
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