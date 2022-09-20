import os
import json

DEFAULT_CONFIG = {
    "node_id": "",
    "device_ip": "",
    "web_port": 5001,
    "hub_ip": "",
    "hub_port": 0,
    "mic_tag": "",
    "mic_index": 0
}

class ConfigManager:
    def __init__(self):
        self.config_path = f'{os.getcwd()}/config.json'
        self.config = {}
        self.load_config()
        
    def get(self, *keys):
        try:
            dic = self.config.copy()
            for key in keys:
                dic = dic[key]
            return dic
        except:
            return None

    def set(self, *keys, value=None):
        if value is None:
            raise RuntimeError
        dic = self.config.copy()
        for key in keys[:-1]:
            dic = dic.setdefault(key, {})
        dic[keys[-1]] = value
        self.config = dic
        self.save_config()
        
    def config_exists(self):
        return os.path.exists(self.config_path)

    def save_config(self):
        with open(self.config_path, 'w') as config_file:
            config_file.write(json.dumps(self.config, indent=4))

    def load_config(self) -> dict:
        if not os.path.exists(self.config_path):
            self.config = DEFAULT_CONFIG
            self.save_config(self.config)
        else:
            self.config = json.load(open(self.config_path, 'r'))