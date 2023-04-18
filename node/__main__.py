import click
import requests
import threading

from node import config
from node.node import Node
from node.web import create_app

@click.command()
@click.option('--debug', is_flag=True)
@click.option('--no_sync', is_flag=True)
def run_node(debug, no_sync):

    if not no_sync:

        # Run Startup Sync with HUB

        print('Node Syncing with HUB...')

        node_id = config.get('node_id')
        node_name = config.get('node_name')
        device_ip = config.get('device_ip')
        hub_ip = config.get('hub_ip')
        wakeup = config.get('wakeup')
        recording = config.get('recording')
        playback = config.get('playback')

        hub_api_url = f'http://{hub_ip}:5010/api'

        sync_data = {        
            'node_id': node_id,
            'node_name': node_name,
            'node_api_url': f'http://{device_ip}:5005/api',
            'wakeup': wakeup,
            'recording': recording,
            'playback': playback
        }

        try:
            response = requests.put(f'{hub_api_url}/node/sync', json=sync_data, timeout=5)
            if response.status_code != 200:
                print(response.json())
                response.raise_for_status()

            config_json = response.json()
            print(config_json)
            config.set('node_name', config_json['node_name'])
            config.set('wakeup', config_json['wakeup'])
            config.set('recording', config_json['recording'])
            config.set('playback', config_json['playback'])

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