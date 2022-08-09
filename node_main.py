from select import select
import click
from node import Node
from utils.hardware import select_mic
from utils.network import scan_for_hub, get_local_ip, get_subnet
import requests

@click.command()
@click.option('--mic_tag', default='microphone', help='String tag of the microphone to use')
@click.option('--hub_ip', default=None, help='IP of the hub to connect to')
@click.option('--hub_port', default=5000, help='Port for the hub API')
@click.option('--cli', is_flag=True)
@click.option('--debug', is_flag=True)
def run_node(mic_tag, hub_ip, hub_port, cli, debug):

    mic_index, _ = select_mic(mic_tag)

    if not hub_ip:
        ip = get_local_ip()
        hub_ip = scan_for_hub(get_subnet(ip), hub_port)
    
    hub_api_uri = f'{hub_ip}:{hub_port}'

    response = requests.get(f'http://{hub_ip}:{hub_port}/ova_sync')

    node = Node(mic_index, hub_api_uri, cli, debug)
    node.start()

if __name__ == '__main__':
    run_node()
    