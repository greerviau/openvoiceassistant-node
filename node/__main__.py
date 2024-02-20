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
@click.option("--port", required=False, default = 7234, type=int)
@click.option("--hub_port", required=False, default = 7123, type=int)
def main(debug, no_sync, sync_up, port, hub_port):

    logger = logging.getLogger()
    log_level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(log_level)

    # Create a file handler and set its level to DEBUG or INFO
    file_handler = TimedRotatingFileHandler(LOGFILE, when='midnight', interval=1, backupCount=10)
    file_handler.suffix = "%Y-%m-%d.log"  # Append date to log file name
    file_handler.setLevel(log_level)

    # Create a console handler and set its level to DEBUG or INFO
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)-12s - %(levelname)-8s: %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("==== STARTING NODE ====")
    logger.debug("===== DEBUG MODE ======")

    updater = Updater()
    updater.start()
    
    node = Node(no_sync, sync_up, hub_port)
    node.start()
    
    app = create_app(node, updater)
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()