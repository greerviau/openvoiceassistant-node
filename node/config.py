import os
import json
import typing
import uuid
import random

from .utils.network import get_my_ip, scan_for_hub

class Configuration:
    def __init__(self):
        self.loc = os.path.realpath(os.path.dirname(__file__))
        self.config_path = f'{self.loc}/config.json'
        print(f'Loading config: {self.config_path}')
        self.config = {}
        self.load_config()

    def get(self, *keys: typing.List[str]):
        keys = list(keys)
        dic = self.config.copy()
        for key in keys:
            try:
                dic = dic[key]
            except KeyError:
                return None
        return dic

    def set(self, *keys: typing.List[typing.Any]):
        keys = list(keys)
        value = keys.pop(-1)
        d = self.config
        for key in keys[:-1]:
            d = d.setdefault(key, {})
        d[keys[-1]] = value
        self.save_config()
        return value
        
    def config_exists(self):
        return os.path.exists(self.config_path)

    def save_config(self):
        print('Config saved')
        with open(self.config_path, 'w') as config_file:
            config_file.write(json.dumps(self.config, indent=4))

    def load_config(self) -> typing.Dict:
        if not os.path.exists(self.config_path):
            print('Loading default config')
            self.config = self.__default_config()
            self.save_config()
        else:
            print('Loading existing config')
            self.config = json.load(open(self.config_path, 'r'))

    def __default_config(self):
        device_ip = get_my_ip()
        hub_port = 5010
        hub_ip = scan_for_hub(device_ip, hub_port)
        mic_index = 0
        random.seed(device_ip)
        node_id = f'new_node_{uuid.UUID(bytes=bytes(random.getrandbits(8) for _ in range(16)), version=4).hex}'

        return {
            "node_id": node_id,
            "node_name": node_id,
            "device_ip": device_ip,
            "hub_ip": hub_ip,
            "mic_index": mic_index,
            "min_audio_sample_length": 1,
            "audio_sample_buffer_length": 0.3,
            "vad_sensitivity": 3
        }

    def __repr__(self) -> typing.Dict:
        return self.config