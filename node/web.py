import click
import requests
import flask
import threading
import uuid

from .node import Node
from .config import Configuration
from .utils.hardware import list_microphones

def create_app(node: Node):

    app = flask.Flask('Node')

    @app.route('/api/', methods=['GET'])
    def index():
        return {}, 200

    @app.route('/api/status', methods=['GET'])
    def status():
        return {}, 200

    @app.route('/api/config', methods=['GET'])
    def get_config():
        return node.config, 200

    @app.route('/api/config', methods=['PUT'])
    def put_config():
        return {}, 200

    @app.route('/api/config', methods=['GET'])
    def get_microphones():
        return list_microphones(), 200

    @app.route('/api/restart', methods=['GET'])
    def restart():
        return {}, 200

    return app
    