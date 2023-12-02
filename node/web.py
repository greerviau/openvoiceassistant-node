import flask

from node import config
from node.node import Node
from node.utils.hardware import list_microphones, list_speakers
from node.schemas import NodeConfig

def create_app(node: Node):

    app = flask.Flask('Node')

    @app.route('/api/', methods=['GET'])
    def index():
        return {}, 200

    @app.route('/api/config', methods=['GET'])
    def get_config() -> NodeConfig:
        return config.config, 200

    @app.route('/api/config', methods=['PUT'])
    def put_config():
        node_config = flask.request.json
        config.set('node_name', node_config.node_name)
        config.set('mic_index', node_config.mic_index)
        config.set('min_audio_sample_length', node_config.min_audio_sample_length)
        config.set('vad_sensitivity', node_config.vad_sensitivity)
        node.restart()
        return node_config, 200
    
    @app.route('/api/play_alarm', methods=['POST'])
    def play_alarm():
        node.play_alarm()
        return {}, 200

    @app.route('/api/stop_alarm', methods=['POST'])
    def stop_alarm():
        node.stop_alarm()
        return {}, 200
    
    @app.route('/api/set_volume', methods=['PUT'])
    def set_volume():
        data = flask.request.json
        volume = data.volume_percent
        node.set_volume(volume)
        return {}, 200

    @app.route('/api/microphones', methods=['GET'])
    def get_microphones():
        return list_microphones(), 200

    @app.route('/api/speakers', methods=['GET'])
    def get_speakers():
        return list_speakers(), 200

    @app.route('/api/restart', methods=['GET'])
    def restart():
        node.restart()
        return {}, 200

    return app
    