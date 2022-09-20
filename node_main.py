from distutils.command.config import config
import click
from node import Node
from utils.hardware import select_mic
from utils.network import scan_for_hub, get_local_ip, get_subnet
import requests
import flask
import threading

from managers.config_manager import ConfigManager

@click.command()
@click.option('--debug', is_flag=True)
def run_node(debug):

    config_manager = ConfigManager()

    if not config_manager.get('device_ip'):
        config_manager.set('device_ip', value = get_local_ip())

    if not config_manager.get('web_port'):
        config_manager.set('web_port', value = 5001)

    if not config_manager.get('hub_port'):
        config_manager.set('hub_port', value = 5001)

    if not config_manager.get('hub_ip'):
        config_manager.set('hub_ip', value = scan_for_hub(get_subnet(device_ip), hub_port))

    if not config_manager.get('hub_api_url'):
        config_manager.set('hub_api_url', value = f'http://{hub_ip}:{hub_port}/api')

    if not config_manager.get('mic_tag'):
        ind, tag = select_mic('microphone')
        config_manager.set('mic_tag', value = tag)
        config_manager.set('mic_index', value = ind)
    
    device_ip = config_manager.get('device_ip')
    web_port = config_manager.get('web_port')
    hub_port = config_manager.get('hub_port')
    hub_ip = config_manager.get('hub_ip')
    hub_api_url = config_manager.get('hub_api_url')
    mic_tag = config_manager.get('mic_tag')
    mic_index = config_manager.get('mic_index')

    if not config_manager.get('node_id'):
        _ = device_ip.split('.')[-1]
        config_manager.set('node_id', value=f'new_node_{_}')

    node_id = config_manager.get('node_id')

    sync_data = {
        'ip': device_ip,
        'port': web_port,
        'address': f'http://{device_ip}:{web_port}/api',
        'node_id': node_id
    }
    try:
        response = requests.get(f'{hub_api_url}/node/sync', json=sync_data)
        if response.status_code != 200:
            raise
    except:
        raise RuntimeError('HUB Sync Failed')

    node = Node(node_id, mic_index, hub_api_url, debug)
    node_thread = threading.Thread(target=node.start)
    node_thread.start()

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

    app.run(host='0.0.0.0', port=web_port, debug=debug)

if __name__ == '__main__':
    run_node()
    