import flask
import requests

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
        return config.get(), 200

    @app.route('/api/config', methods=['PUT'])
    def put_config():
        node_config = flask.request.json
        config.set('node_name', node_config.node_name)
        config.set('mic_index', node_config.mic_index)
        config.set('min_audio_sample_length', node_config.min_audio_sample_length)
        config.set('vad_sensitivity', node_config.vad_sensitivity)
        node.restart()
        return node_config, 200
       
    @app.route('/api/play/audio', methods=['POST'])
    def play_audio():
        try:
            context = flask.request.json
            response_audio_data = context['response_audio_data']
            data = bytes.fromhex(response_audio_data)
            with open('play.wav', 'wb') as wav_file:
                wav_file.write(data)
            node.audio_player.play_audio_file('play.wav', asynchronous=True)
        except Exception as e:
            print(e)
        return {}, 200
    
    @app.route('/api/play/text', methods=['POST'])
    def play_text():
        try:
            data = flask.request.json
            text = data['text']
            respond_response = requests.get(f'{node.hub_api_url}/synthesizer/synthesize/{text}')
            context = respond_response.json()
            response_audio_data = context['response_audio_data']
            data = bytes.fromhex(response_audio_data)
            with open('play.wav', 'wb') as wav_file:
                wav_file.write(data)
            node.audio_player.play_audio_file('play.wav', asynchronous=True)
        except Exception as e:
            print(e)
        return {}, 200
    
    @app.route('/api/set_timer', methods=['POST'])
    def set_timer():
        data = flask.request.json
        durration = data['durration']
        node.set_timer(durration)
        return {}, 200

    @app.route('/api/timer_remaining_time', methods=['GET'])
    def timer_remaining_time():
        return {
            "time_remaining": node.get_timer()
        }, 200
    
    @app.route('/api/set_volume', methods=['PUT'])
    def set_volume():
        try:
            data = flask.request.json
            volume = data['volume_percent']
            config.set('volume', volume)
            node.set_volume(volume)
        except Exception as e:
            print(e)
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
    