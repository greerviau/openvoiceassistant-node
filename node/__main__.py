import click
import requests
import threading

from .node import Node
from .web import create_app
from .config import Configuration

@click.command()
@click.option('--debug', is_flag=True)
@click.option('--web_port', default=5005)
def run_node(debug, web_port):

    config = Configuration()

    # Run Startup Sync with HUB

    node_id = config.get('node_id')
    node_name = config.get('node_name')
    device_ip = config.get('device_ip')
    hub_api_url = config.get('hub_api_url')
    mic_index = config.get('mic_index')
    mic_tag = config.get('mic_tag')
    min_audio_sample_length = config.get('min_audio_sample_length')
    vad_sensitivity = config.get('vad_sensitivity')

    sync_data = {        
        'node_id': node_id,
        'node_name': node_name,
        'node_api_url': f'http://{device_ip}:{web_port}/api',
        'mic_index': mic_index,
        'min_audio_sample_length': min_audio_sample_length,
        'vad_sensitivity': vad_sensitivity
    }

    try:
        response = requests.put(f'{hub_api_url}/node/sync', json=sync_data, timeout=5)
        if response.status_code != 200:
            print(response.json())
            raise
    except:
        raise RuntimeError('HUB Sync Failed')

    node = Node(config, debug)
    
    app = create_app(node)

    web_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=web_port))
    web_thread.setDaemon(True)
    web_thread.start()

    node.start()

if __name__ == '__main__':
    run_node()