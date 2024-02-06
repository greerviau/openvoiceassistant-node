import time
import os
import threading
import requests

from node import config
from node.listener import Listener
from node.audio_player import AudioPlayer
from node.processor import Processor
from node.timer import Timer
from node.utils.hardware import list_microphones, select_mic, get_supported_samplerates, list_speakers, select_speaker
from node.utils.network import get_my_ip, scan_for_hub

class Node:
    def __init__(self, debug: bool, no_sync: bool, sync_up: bool):
        self.debug = debug
        self.no_sync = no_sync
        self.sync_up = sync_up
        self.running = threading.Event()
        self.running.set()

    def stop(self):
        print("Stopping node")
        self.running.clear()

    def start(self):
        self.initialize()
        print("Starting node")
        self.running.set()
        self.run()

    def sync(self, sync_up: bool = False):
        # Run Startup Sync with HUB
        print("Node Syncing with HUB...")

        node_id = config.get("id")
        node_name = config.get("name")
        node_area = config.get("area")
        device_ip = get_my_ip()
        hub_ip = config.get("hub_ip")
        wake_word = config.get("wake_word")
        wake_word_conf_threshold = config.get("wake_word_conf_threshold")
        wakeup_sound = config.get("wakeup_sound")
        vad_sensitivity = config.get("vad_sensitivity")
        vad_threshold = config.get("vad_threshold")
        speex_noise_suppression = config.get("speex_noise_suppression")
        mic_index = config.get("mic_index")
        speaker_index = config.get("speaker_index")
        volume = config.get("volume")

        if not hub_ip:
            hub_ip = scan_for_hub(device_ip, 7123)
            config.set("hub_ip", hub_ip)

        hub_api_url = f"http://{hub_ip}:7123/api"

        sync_data = {     
                "id": node_id,
                "name": node_name,
                "area": node_area,
                "api_url": f"http://{device_ip}:7234/api",
                "wake_word": wake_word,
                "wake_word_conf_threshold": wake_word_conf_threshold, 
                "wakeup_sound": wakeup_sound,
                "vad_sensitivity": vad_sensitivity,
                "vad_threshold": vad_threshold,
                "speex_noise_suppression": speex_noise_suppression,
                "mic_index": mic_index,
                "speaker_index": speaker_index,
                "volume": volume,
                "restart_required": False
            }

        synced = False
        while not synced:
            try:
                if sync_up:
                    print("Pushing local configuration to HUB")
                    response = requests.put(f"{hub_api_url}/node/{node_id}/sync_up", json=sync_data, timeout=5)
                else:
                    print("Pulling configuration from HUB")
                    response = requests.put(f"{hub_api_url}/node/{node_id}/sync_down", json=sync_data, timeout=5)
            
                if response.status_code != 200:
                    raise RuntimeError(response.json()["detail"])
                else:
                    synced = True
            except Exception as e:
                print(f"HUB Sync Failed | {repr(e)}")
                print("Retrying in 30 seconds...")
                time.sleep(30)

        try:
            config_json = response.json()
            print("Node config:")
            print(config_json)

            config.set("name", config_json["name"])
            config.set("area", config_json["area"])
            config.set("wake_word", config_json["wake_word"])
            config.set("wake_word_conf_threshold", config_json["wake_word_conf_threshold"])
            config.set("wakeup_sound", config_json["wakeup_sound"])
            config.set("vad_sensitivity", config_json["vad_sensitivity"])
            config.set("vad_threshold", config_json["vad_threshold"])
            config.set("speex_noise_suppression", config_json["speex_noise_suppression"])
            config.set("mic_index", config_json["mic_index"])
            config.set("speaker_index", config_json["speaker_index"])
            config.set("volume", config_json["volume"])

        except Exception as e:
            #print(repr(e))
            raise RuntimeError(f"HUB Sync Failed | {repr(e)}")

        print("Sync Complete!")

    def initialize(self):
        if not self.no_sync: self.sync(self.sync_up)
        print("Initializing...")
        self.base_dir = os.path.realpath(os.path.dirname(__file__))
        self.sounds_dir = os.path.join(self.base_dir, 'sounds')
        self.file_dump = os.path.join(self.base_dir, 'file_dump')
        self.wake_word_model_dump = os.path.join(self.base_dir, "wakeword_models")
        
        os.makedirs(self.sounds_dir, exist_ok=True)
        os.makedirs(self.file_dump, exist_ok=True)
        os.makedirs(self.wake_word_model_dump, exist_ok=True)

        self.timer = None

        self.id = config.get("id")
        self.name = config.get("name")
        self.area = config.get("area")
        self.hub_ip = config.get("hub_ip")
        self.wake_word = config.get("wake_word")
        self.wakeup_sound = config.get("wakeup_sound")
        self.wake_word_conf_threshold = config.get("wake_word_conf_threshold")
        self.speex_noise_suppression = config.get("speex_noise_suppression")
        self.mic_idx = config.get("mic_index")
        self.speaker_idx = config.get("speaker_index")
        self.vad_sensitivity = config.get("vad_sensitivity")
        self.vad_threshold = config.get("vad_threshold")
        self.volume = config.get("volume")

        self.hub_api_url = f"http://{self.hub_ip}:{7123}/api"

        # MICROPHONE SETTINGS
        print("\nAvailable Microphones:")
        [print(f"- {mic}") for mic in list_microphones()]

        try:
            _, self.mic_tag = select_mic(self.mic_idx)
        except:
            print("Specified mic does not exist")
            mic = list_microphones()[0]
            self.mic_tag = mic["name"]
            self.mic_idx = mic["idx"]
            config.set("mic_index", self.mic_idx)
            self.sync(sync_up=True)

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

        try:
            _, self.speaker_tag = select_speaker(self.speaker_idx)
        except:
            print("Specified speaker does not exist")
            speaker = list_speakers()[0]
            self.speaker_tag = speaker["name"]
            self.speaker_idx = speaker["idx"]
            config.set("speaker_index", self.speaker_idx)
            self.sync(sync_up=True)

        # SETTINGS
        if self.debug: print("==DEBUG MODE==")
        print("\nNode Info")
        print(f"- ID:             {self.id}")
        print(f"- Name:           {self.name}")
        print(f"- Area:           {self.area}")
        print(f"- HUB:            {self.hub_ip}")
        print("\nWakeword Settings")
        print(f"- Wake Word:      {self.wake_word}")
        print(f"- Wake Conf:      {self.wake_word_conf_threshold}")
        print(f"- Vad Thresh:     {self.vad_threshold}")
        print(f"- Noise Suppress: {self.speex_noise_suppression}")
        print(f"- Wakeup Sound:   {self.wakeup_sound}")
        print(f"\nIO Settings")
        print(f"- Microphone:     {self.mic_tag}")
        print(f"- Microphone IDX: {self.mic_idx}")
        print(f"- Speaker:        {self.speaker_tag}")
        print(f"- Speaker IDX:    {self.speaker_idx}")
        print(f"- Sample Rate:    {self.sample_rate}")
        print(f"- Sample Width:   {self.sample_width}")
        print(f"- Audio Channels: {self.audio_channels}")
        print(f"- Volume:         {self.volume}")

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
        except Exception as e:
            print(f"Failed to initialize mixer | {repr(e)}")
            self.mixer = None

        # INITIALIZING COMPONENTS
        self.audio_player = AudioPlayer(self)
        self.listener = Listener(self, frames_per_buffer=1600)
        self.processor = Processor(self)
    
    def run(self):
        self.last_time_engaged = time.time()
        engaged = False
        while self.running.is_set():
            audio_data = self.listener.listen(engaged)
            if not self.running.is_set():
                break
            engaged = self.processor.process_audio(audio_data)
            if self.led_controller:
                self.led_controller.off()         
        print("Mainloop end")

    def set_volume(self, volume: int):
        if volume >= 0 and volume <= 100:
            if self.mixer:
                self.mixer.setvolume(volume)
                print(f"Volume set {volume}")
                return
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