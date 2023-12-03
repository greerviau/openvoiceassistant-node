import click
import requests
import threading

from node import config
from node.node import Node
from node.web import create_app
from node.utils.network import get_my_ip, scan_for_hub

@click.command()
@click.option('--debug', is_flag=True)
@click.option('--no_sync', is_flag=True)
@click.option('--sync_up', is_flag=True)
def run_node(debug, no_sync, sync_up):

    if not no_sync:

        # Run Startup Sync with HUB

        print('Node Syncing with HUB...')

        node_id = config.get('node_id')
        node_name = config.get('node_name')
        node_area = config.get('node_area')
        device_ip = get_my_ip()
        hub_ip = config.get('hub_ip')
        wake_word = config.get('wake_word')
        wakeup_sound = config.get('wakeup_sound')
        mic_index = config.get('mic_index')
        vad_sensitivity = config.get('vad_sensitivity')
        speaker_index = config.get('speaker_index')

        if not hub_ip:
            hub_ip = scan_for_hub(device_ip, 5010)
            config.set('hub_ip', hub_ip)

        hub_api_url = f'http://{hub_ip}:5010/api'

        sync_data = {        
            'node_id': node_id,
            'node_name': node_name,
            'node_area': node_area,
            'node_api_url': f'http://{device_ip}:5005/api',
            'wake_word': wake_word,
            'wakeup_sound': wakeup_sound,
            'mic_index': mic_index,
            'vad_sensitivity': vad_sensitivity,
            'speaker_index': speaker_index
        }

        try:
            response = requests.put(f'{hub_api_url}/node/{"sync_up" if sync_up else "sync_down"}', json=sync_data, timeout=5)
            if response.status_code != 200:
                print(response.json())
                response.raise_for_status()

            config_json = response.json()
            print(config_json)
            config.set('node_name', config_json['node_name'])
            config.set('node_area', config_json['node_area'])
            config.set('wake_word', config_json['wake_word'])
            config.set('wakeup_sound', config_json['wakeup_sound'])
            config.set('mic_index', config_json['mic_index'])
            config.set('vad_sensitivity', config_json['vad_sensitivity'])
            config.set('speaker_index', config_json['speaker_index'])

        except Exception as e:
            print(repr(e))
            raise RuntimeError('HUB Sync Failed')

        print('Sync Complete')

    node = Node(debug)
    
    app = create_app(node)

    web_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5005))
    web_thread.daemon = True
    web_thread.start()

    node.start()

if __name__ == '__main__':
    run_node()