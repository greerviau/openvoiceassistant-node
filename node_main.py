from distutils.command.config import config
import click
from node import Node
from utils.hardware import select_mic
from utils.network import scan_for_hub, get_local_ip, get_subnet
import requests
import flask
import threading

from config import Configuration

@click.command()
@click.option('--debug', is_flag=True)
def run_node(debug):

    config = Configuration()

    if not config.get('device_ip'):
        device_ip = config.setkey('device_ip', value = get_local_ip())
    else:
        device_ip = config.get('device_ip')

    if not config.get('web_port'):
        web_port = config.setkey('web_port', value = 5005)
    else:
        web_port = config.get('web_port')

    if not config.get('hub_port'):
        hub_port = config.setkey('hub_port', value = 5010)
    else:
        hub_port = config.get('hub_port')

    if not config.get('hub_ip'):
        hub_ip = config.setkey('hub_ip', value = scan_for_hub(get_subnet(device_ip), hub_port))
    else:
        hub_ip = config.get('hub_ip')

    if not config.get('hub_api_url'):
        hub_api_url = config.setkey('hub_api_url', value = f'http://{hub_ip}:{hub_port}/api')
    else:
        hub_api_url = config.get('hub_api_url')

    if not config.get('mic_tag'):
        ind, tag = select_mic('microphone')
        mic_tag = config.setkey('mic_tag', value = tag)
        mic_index = config.setkey('mic_index', value = ind)
    else:
        mic_tag = config.get('mic_tag')
        mic_index = config.get('mic_index')

    if not config.get('node_id'):
        _ = device_ip.split('.')[-1]
        node_id = config.setkey('node_id', value=f'new_node_{_}')
    else:
        node_id = config.get('node_id')

    sync_data = {
        'ip': device_ip,
        'port': web_port,
        'address': f'http://{device_ip}:{web_port}/api',
        'node_id': node_id
    }
    try:
        response = requests.put(f'{hub_api_url}/node/sync', json=sync_data)
        if response.status_code != 200:
            print(response.json())
            raise
    except:
        raise RuntimeError('HUB Sync Failed')

    app = flask.Flask('Node')

    @app.route('/api/', methods=['GET'])
    def index():
        return {}, 200

    @app.route('/api/status', methods=['GET'])
    def status():
        return {}, 200

    @app.route('/api/config', methods=['GET'])
    def get_config():
        return {}, 200

    @app.route('/api/config', methods=['PUT'])
    def put_config():
        return {}, 200

    @app.route('/api/restart', methods=['GET'])
    def restart():
        return {}, 200


    web_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=web_port))
    web_thread.setDaemon(True)
    web_thread.start()

    #app.run(host='0.0.0.0', port=web_port, debug=debug)

    node = Node(node_id, mic_index, hub_api_url, debug)
    node.start()

if __name__ == '__main__':
    run_node()
    