import click
import logging
from logging.handlers import TimedRotatingFileHandler

from node.dir import LOGFILE
from node.node import Node
from node.updater import Updater
from node.web import create_app

@click.command()
@click.option("--debug", is_flag=True)
@click.option("--no_sync", is_flag=True)
@click.option("--sync_up", is_flag=True)
def main(debug, no_sync, sync_up):

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create a file handler and set its level to DEBUG or INFO
    file_handler = TimedRotatingFileHandler(LOGFILE, when='midnight', interval=1, backupCount=10)
    file_handler.suffix = "%Y-%m-%d.log"  # Append date to log file name
    file_handler.setLevel(logging.INFO)

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

    logger.info("======STARTING NODE======")

    updater = Updater()
    updater.start()
    
    node = Node(debug, no_sync, sync_up)
    node.start()
    
    app = create_app(node, updater)
    app.run(host="0.0.0.0", port=7234)

if __name__ == "__main__":
    main()