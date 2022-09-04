from select import select
import click
from node import Node
from utils.hardware import select_mic
from utils.network import scan_for_hub, get_local_ip, get_subnet
import requests
from flask import Flask
import threading

@click.command()
@click.option('--node_id')
@click.option('--mic_tag', default='microphone', help='String tag of the microphone to use')
@click.option('--hub_ip', default=None, help='IP of the hub to connect to')
@click.option('--hub_port', default=5000, help='Port for the hub API')
@click.option('--cli', is_flag=True)
@click.option('--debug', is_flag=True)
def run_node(node_id, mic_tag, hub_ip, hub_port, cli, debug):

    mic_index, _ = select_mic(mic_tag)
    
    ip = get_local_ip()
    web_port = 5000

    if not hub_ip:
        hub_ip = scan_for_hub(get_subnet(ip), hub_port)
    
    hub_api_uri = f'http://{hub_ip}:{hub_port}/api'

    sync_data = {
        'ip': ip,
        'port': web_port,
        'address': f'http://{ip}:{web_port}/api',
        'node_id': node_id
    }
    try:
        response = requests.get(f'{hub_api_uri}/sync', json=sync_data)
        if response.status_code != 200:
            raise
    except:
        raise RuntimeError('HUB Sync Failed')

    node = Node(node_id, mic_index, hub_api_uri, cli, debug)
    node_thread = threading.Thread(target=node.start)
    node_thread.start()

    app = Flask('Node')

    @app.route('/api/', methods=['GET'])
    def index():
        return {}, 200

    @app.route('/api/status', methods=['GET'])
    def index():
        return {}, 200

    @app.route('/api/config', methods=['GET'])
    def index():
        return {}, 200

    @app.route('/api/config', methods=['PUT'])
    def index():
        return {}, 200

    app.run(host='0.0.0.0', port=web_port, debug=debug)

if __name__ == '__main__':
    run_node()
    