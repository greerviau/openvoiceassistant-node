import click
import logging
import os
from datetime import datetime

from node.node import Node
from node.updater import Updater
from node.web import create_app

@click.command()
@click.option("--debug", is_flag=True)
@click.option("--no_sync", is_flag=True)
@click.option("--sync_up", is_flag=True)
def main(debug, no_sync, sync_up):
    now = datetime.now()
    folder = now.strftime("logs/%m-%Y/%d")
    file = now.strftime("log_%H-%M-%S.log")
    log_file_path = os.path.join(folder, file)
    os.makedirs(folder, exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Create a file handler and set its level to DEBUG or INFO
    file_handler = logging.FileHandler(log_file_path, mode='w')
    file_handler.setLevel(logging.DEBUG if debug else logging.INFO)

    # Create a console handler and set its level to DEBUG or INFO
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)

    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)-12s - %(levelname)-8s: %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    updater = Updater()
    updater.start()
    
    node = Node(debug, no_sync, sync_up)
    node.start()
    
    app = create_app(node, updater, log_file_path)
    app.run(host="0.0.0.0", port=7234)

if __name__ == "__main__":
    main()