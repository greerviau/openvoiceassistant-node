import os
import json
import typing
import uuid
import random

from node.utils.network import get_my_ip, scan_for_hub
from node.utils.hardware import find_speakers, find_microphones

loc = os.path.realpath(os.path.dirname(__file__))
config_path = f"{loc}/config.json"
config = {}

def get(*keys: typing.List[str]):
    global config
    keys = list(keys)
    dic = config.copy()
    for key in keys:
        try:
            dic = dic[key]
        except KeyError:
            return None
    return dic

def set(*keys: typing.List[typing.Any]):
    global config
    keys = list(keys)
    value = keys.pop(-1)
    d = config
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value
    save_config()
    return value
    
def config_exists():
    global config_path
    return os.path.exists(config_path)

def save_config():
    global config, config_path
    with open(config_path, "w") as config_file:
        config_file.write(json.dumps(config, indent=4))

def load_config() -> typing.Dict:
    global config, config_path
    print(f"Loading config: {config_path}")
    if not os.path.exists(config_path):
        print("Initializing default config")
        config = __default_config()
        save_config()
    else:
        print("Loading existing config")
        config = json.load(open(config_path, "r"))

def __default_config():
    device_ip = get_my_ip()
    hub_ip = scan_for_hub(device_ip, 5010)
    random.seed(device_ip)
    node_id = f"{uuid.UUID(bytes=bytes(random.getrandbits(8) for _ in range(16)), version=4).hex}"

    return {
        "node_id": node_id,
        "node_name": f"node_{node_id}",
        "node_area": "",
        "hub_ip": hub_ip,
        "wake_word": "computer",
        "wakeup_sound": True,
        "mic_index": 0,
        "vad_sensitivity": 3,
        "speaker_index": 0,
        "volume": 100
    }

load_config()