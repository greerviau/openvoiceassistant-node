import os
import json
import typing
import uuid
import random
import logging
logger = logging.getLogger("config")

from node.utils.network import get_my_ip
from node.utils.hardware import list_speakers, list_microphones

loc = os.path.realpath(os.path.dirname(__file__))
config_path = f"{loc}/config.json"
config = {}

def get(*keys: typing.List[str]) -> typing.Any:
    global config
    keys = list(keys)
    dic = config.copy()
    for key in keys:
        try:
            dic = dic[key]
        except KeyError:
            return None
    return dic

def set(*keys: typing.List[typing.Any]) -> typing.Any:
    global config
    keys = list(keys)
    value = keys.pop(-1)
    d = config
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value
    save_config()
    return value
    
def config_exists() -> bool:
    global config_path
    return os.path.exists(config_path)

def save_config():
    global config, config_path
    with open(config_path, "w") as config_file:
        config_file.write(json.dumps(config, indent=4))
    logger.debug("Config saved")

def verify_config():
    global config
    default_config = __default_config()
    if list(default_config.keys()) == list(config.keys()):
        return
    config_clone = config.copy()
    for key, value in default_config.items():
        if key not in config_clone:
            config_clone[key] = value
    for key, value in config_clone.items():
        if key not in default_config:
            config_clone.pop(key)
    config = config_clone
    save_config()

def load_config() -> typing.Dict:
    global config, config_path
    logger.info(f"Loading config: {config_path}")
    if not os.path.exists(config_path):
        logger.info("Initializing default config")
        config = __default_config()
        save_config()
    else:
        logger.info("Loading existing config")
        config = json.load(open(config_path, "r"))
        verify_config()

def __default_config() -> typing.Dict:
    def check_speex():
        try: 
            import speexdsp_ns 
            return True
        except: 
            return False
    device_ip = get_my_ip()
    random.seed(device_ip)
    node_id = f"{uuid.UUID(bytes=bytes(random.getrandbits(8) for _ in range(16)), version=4).hex}"

    return {
        "id": node_id,
        "name": f"node_{node_id}",
        "area": "",
        "hub_ip": "",
        "wake_word": "ova",
        "wake_word_conf_threshold": 0.8,
        "wakeup_sound": True,
        "vad_sensitivity": 3,
        "vad_threshold": 0.0,
        "speex_noise_suppression": False,
        "speex_available": check_speex(),    
        "mic_index": list_microphones()[0]["idx"],
        "speaker_index": list_speakers()[0]["idx"],
        "volume": 100
    }

load_config()