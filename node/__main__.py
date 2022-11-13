import click
import requests
import threading

from .node import Node
from .web import create_app
from .config import Configuration

@click.command()
@click.option('--debug', is_flag=True)
def run_node(debug):

    config = Configuration()

    # Run Startup Sync with HUB

    print('Node Syncing with HUB...')

    node_id = config.get('node_id')
    node_name = config.get('node_name')
    device_ip = config.get('device_ip')
    hub_ip = config.get('hub_ip')
    mic_index = config.get('mic_index')
    min_audio_sample_length = config.get('min_audio_sample_length')
    audio_sample_buffer_length = config.get('audio_sample_buffer_length')
    vad_sensitivity = config.get('vad_sensitivity')

    hub_api_url = f'http://{hub_ip}:{5010}/api'

    sync_data = {        
        'node_id': node_id,
        'node_name': node_name,
        'node_api_url': f'http://{device_ip}:{5005}/api',
        'mic_index': mic_index,
        'min_audio_sample_length': min_audio_sample_length,
        'audio_sample_buffer_length': audio_sample_buffer_length,
        'vad_sensitivity': vad_sensitivity
    }

    try:
        response = requests.put(f'{hub_api_url}/node/sync', json=sync_data, timeout=5)
        if response.status_code != 200:
            print(response.json())
            raise

        config_json = response.json()
        config.set('node_name', config_json['node_name'])
        config.set('mic_index', config_json['mic_index'])
        config.set('min_audio_sample_length', config_json['min_audio_sample_length'])
        config.set('audio_sample_buffer_length', config_json['audio_sample_buffer_length'])
        config.set('vad_sensitivity', config_json['vad_sensitivity'])

    except:
        raise RuntimeError('HUB Sync Failed')

    print('Sync Complete')

    node = Node(config, debug)
    
    app = create_app(node)

    web_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5005))
    web_thread.daemon = True
    web_thread.start()

    node.start()

if __name__ == '__main__':
    run_node()