import click
import threading

from node.node import Node
from node.web import create_app

@click.command()
@click.option("--debug", is_flag=True)
@click.option("--no_sync", is_flag=True)
@click.option("--sync_up", is_flag=True)
def main(debug, no_sync, sync_up):
    node = Node(debug, no_sync, sync_up)
    node_thread = threading.Thread(target=node.start, daemon=True)
    node_thread.start()
    
    app = create_app(node, node_thread)
    app.run(host="0.0.0.0", port=7234)

if __name__ == "__main__":
    main()