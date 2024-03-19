import time
import os
import threading
import requests
import logging
logger = logging.getLogger("node")

from node import config
from node.dir import BASEDIR, SOUNDSDIR
from node.listener import Listener
from node.audio_player import AudioPlayer
from node.processor import Processor
from node.timer import Timer
from node.utils.hardware import list_microphones, select_mic, get_supported_samplerates, list_speakers, select_speaker
from node.utils.network import get_my_ip, scan_for_hub

class Node:
    def __init__(self, no_sync: bool, sync_up: bool, port: int, hub_port: int):
        self.no_sync = no_sync
        self.sync_up = sync_up
        self.port = port
        self.hub_port = hub_port
        self.running = threading.Event()
        self.running.set()

    def stop(self):
        logger.info("Stopping node")
        self.running.clear()
        self.stop_timer()
        self.run_thread.join()

    def start(self):
        logger.info("Starting node")
        self.running.set()
        self.run_thread = threading.Thread(target=self.run, daemon=True)
        self.run_thread.start()

    def restart(self):
        logger.info("Restarting node")
        self.stop()
        time.sleep(3)
        self.start()

    def sync(self, sync_up: bool = False):
        # Run Startup Sync with HUB
        logger.info("Node Syncing with HUB...")

        version = open(os.path.join(BASEDIR, "VERSION")).read()
        device_ip = get_my_ip()

        node_id = config.get("id")
        node_name = config.get("name")
        node_area = config.get("area")
        hub_ip = config.get("hub_ip")
        wake_word = config.get("wake_word")
        wake_word_conf_threshold = config.get("wake_word_conf_threshold")
        wakeup_sound = config.get("wakeup_sound")
        vad_sensitivity = config.get("vad_sensitivity")
        vad_threshold = config.get("vad_threshold")
        speex_noise_suppression = config.get("speex_noise_suppression")
        speex_available = config.get("speex_available")
        mic_index = config.get("mic_index")
        speaker_index = config.get("speaker_index")
        volume = config.get("volume")

        if not hub_ip:
            hub_ip = scan_for_hub(device_ip, self.hub_port)
            config.set("hub_ip", hub_ip)

        hub_api_url = f"http://{hub_ip}:{self.hub_port}/api"

        sync_data = {     
                "id": node_id,
                "name": node_name,
                "area": node_area,
                "version": version,
                "address": f"{device_ip}:{self.port}",
                "wake_word": wake_word,
                "wake_word_conf_threshold": wake_word_conf_threshold, 
                "wakeup_sound": wakeup_sound,
                "vad_sensitivity": vad_sensitivity,
                "vad_threshold": vad_threshold,
                "speex_noise_suppression": speex_noise_suppression,
                "speex_available": speex_available,
                "mic_index": mic_index,
                "speaker_index": speaker_index,
                "volume": volume,
                "restart_required": False
            }

        synced = False
        while not synced:
            try:
                if sync_up:
                    logger.info("Pushing local configuration to HUB")
                    response = requests.put(f"{hub_api_url}/node/{node_id}/sync_up", json=sync_data, timeout=5)
                else:
                    logger.info("Pulling configuration from HUB")
                    response = requests.put(f"{hub_api_url}/node/{node_id}/sync_down", json=sync_data, timeout=5)
            
                if response.status_code != 200:
                    raise RuntimeError(response.json()["detail"])
                else:
                    synced = True
            except Exception as e:
                logger.error("HUB Sync Failed")
                logger.info("Retrying in 30 seconds...")
                time.sleep(30)

        try:
            config_json = response.json()
            logger.info("Node config:")
            logger.info(config_json)

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
            logger.exception("HUB Sync Failed")
            raise

        logger.info("Sync Complete!")

    def initialize(self):
        if not self.no_sync: self.sync(self.sync_up)
        logger.info("Initializing...")

        self.timer = None
        self.engaged = False

        self.id = config.get("id")
        self.name = config.get("name")
        self.area = config.get("area")
        self.hub_ip = config.get("hub_ip")
        self.wake_word = config.get("wake_word")
        self.wakeup_sound = config.get("wakeup_sound")
        self.wake_word_conf_threshold = config.get("wake_word_conf_threshold")
        self.speex_noise_suppression = config.get("speex_noise_suppression") and config.get("speex_available")
        self.mic_idx = config.get("mic_index")
        self.speaker_idx = config.get("speaker_index")
        self.vad_sensitivity = config.get("vad_sensitivity")
        self.vad_threshold = config.get("vad_threshold")
        self.volume = config.get("volume")

        self.hub_api_url = f"http://{self.hub_ip}:{7123}/api"

        # MICROPHONE SETTINGS
        logger.info("Available Microphones:")
        [logger.info(f"- {mic}") for mic in list_microphones()]

        try:
            _, self.mic_tag = select_mic(self.mic_idx)
        except:
            logger.warning("Specified mic does not exist")
            mic = list_microphones()[0]
            self.mic_tag = mic["name"]
            self.mic_idx = mic["idx"]
            config.set("mic_index", self.mic_idx)
            self.sync(sync_up=True)

        logger.info("Microphone supported sample rates")
        supported_rates = get_supported_samplerates(self.mic_idx, [16000, 48000, 32000, 8000])
        [logger.info(f"- {rate}") for rate in supported_rates]

        self.sample_rate = supported_rates[0]
        self.sample_width = 2
        self.audio_channels = 1

        # SPEAKER SETTINGS
        logger.info("Available Speakers")
        [logger.info(f"- {speaker}") for speaker in list_speakers()]

        try:
            _, self.speaker_tag = select_speaker(self.speaker_idx)
        except:
            logger.warning("Specified speaker does not exist")
            speaker = list_speakers()[0]
            self.speaker_tag = speaker["name"]
            self.speaker_idx = speaker["idx"]
            config.set("speaker_index", self.speaker_idx)
            self.sync(sync_up=True)

        # SETTINGS
        logger.info("Node Info")
        logger.info(f"- ID:             {self.id}")
        logger.info(f"- Name:           {self.name}")
        logger.info(f"- Area:           {self.area}")
        logger.info(f"- HUB:            {self.hub_ip}")
        logger.info("Wakeword Settings")
        logger.info(f"- Wake Word:      {self.wake_word}")
        logger.info(f"- Wake Conf:      {self.wake_word_conf_threshold}")
        logger.info(f"- Vad Thresh:     {self.vad_threshold}")
        logger.info(f"- Noise Suppress: {self.speex_noise_suppression}")
        logger.info(f"- Wakeup Sound:   {self.wakeup_sound}")
        logger.info(f"IO Settings")
        logger.info(f"- Microphone:     {self.mic_tag}")
        logger.info(f"- Microphone IDX: {self.mic_idx}")
        logger.info(f"- Speaker:        {self.speaker_tag}")
        logger.info(f"- Speaker IDX:    {self.speaker_idx}")
        logger.info(f"- Sample Rate:    {self.sample_rate}")
        logger.info(f"- Sample Width:   {self.sample_width}")
        logger.info(f"- Audio Channels: {self.audio_channels}")
        logger.info(f"- Volume:         {self.volume}")

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
            logger.error(f"Failed to initialize mixer")
            self.mixer = None

        # INITIALIZING COMPONENTS
        self.audio_player = AudioPlayer(self)
        self.listener = Listener(self)
        self.processor = Processor(self)
    
    def run(self):
        self.initialize()
        logger.info("Mainloop running")
        self.last_time_engaged = time.time()
        while self.running.is_set():
            self.listener.listen()
            if not self.running.is_set():
                break
            self.processor.process_audio()
            if self.led_controller:
                self.led_controller.off()         
        logger.warning("Mainloop end")

    def set_volume(self, volume: int):
        if volume >= 0 and volume <= 100:
            if self.mixer:
                self.mixer.setvolume(volume)
                logger.info(f"Volume set {volume}")
                return
        logger.error("Failed to set volume: (Out of range 0-1)")

    def set_timer(self, durration_seconds: int):
        if self.timer == None:
            def timer_finished():
                self.timer.cancel()
                self.timer = None
                self.audio_player.play_audio_file(os.path.join(SOUNDSDIR, "alarm.wav"), asynchronous=True, loop=True)
            self.timer = Timer(durration_seconds, timer_finished)
            self.timer.start()

    def stop_timer(self):
        if self.timer:
            self.timer.cancel()
        self.timer = None

    def get_timer(self) -> int:
        if self.timer:
            return int(self.timer.remaining())
        else:
            return 0