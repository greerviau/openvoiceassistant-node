import flask
import os
import requests
import time 
import threading

from node import config
from node.node import Node
from node.utils.hardware import list_microphones, list_speakers
from node.schemas import NodeConfig

def create_app(node: Node, node_thread: threading.Thread):

    app = flask.Flask("Node")

    @app.route("/api", methods=["GET"])
    def index():
        return {"id": node.id}, 200

    @app.route("/api/config", methods=["GET"])
    def get_config() -> NodeConfig:
        return config.get(), 200

    @app.route("/api/config", methods=["PUT"])
    def put_config():
        node_config = flask.request.json
        config.set("name", node_config["name"])
        config.set("area", node_config["area"])
        config.set("wake_word", node_config["wake_word"])
        config.set("wake_word_conf_threshold", node_config["wake_word_conf_threshold"])
        config.set("wakeup_sound", node_config["wakeup_sound"])
        config.set("vad_sensitivity", node_config["vad_sensitivity"])
        config.set("vad_threshold", node_config["vad_threshold"])
        config.set("speex_noise_suppression", node_config["speex_noise_suppression"])
        config.set("mic_index", node_config["mic_index"])
        config.set("speaker_index", node_config["speaker_index"])
        config.set("volume", node_config["volume"])
        return node_config, 200
       
    @app.route("/api/play/audio", methods=["POST"])
    def play_audio():
        try:
            data = flask.request.json
            audio_data = data["audio_data"]
            data = bytes.fromhex(audio_data)
            audio_file_path = os.path.join(node.file_dump, "play.wav")
            with open(audio_file_path, "wb") as wav_file:
                wav_file.write(data)
            node.audio_player.interrupt()
            node.audio_player.play_audio_file(audio_file_path, asynchronous=True)
        except Exception as e:
            print(e)
        return {}, 200
    
    @app.route("/api/play/file", methods=["POST"])
    def play_file():
        try:
            data = flask.request.json
            file = data["file"]
            loop = data["loop"]
            audio_file_path = os.path.join(node.file_dump, file)
            if os.file.exists(audio_file_path):
                node.audio_player.interrupt()
                node.audio_player.play_audio_file(audio_file_path, asynchronous=True, loop=loop)
            else:
                return {"error": "Could not find file"}, 404
        except Exception as e:
            print(e)
        return {}, 200
    
    @app.route("/api/announce/<text>", methods=["POST"])
    def announce(text: str):
        try:
            respond_response = requests.get(f"{node.hub_api_url}/synthesizer/synthesize/text/{text}")
            context = respond_response.json()
            response_audio_data = context["response_audio_data"]
            data = bytes.fromhex(response_audio_data)
            audio_file_path = os.path.join(node.file_dump, "play.wav")
            with open(audio_file_path, "wb") as wav_file:
                wav_file.write(data)
            node.audio_player.interrupt()
            node.audio_player.play_audio_file(audio_file_path, asynchronous=True)
        except Exception as e:
            print(e)
        return {}, 200
    
    @app.route("/api/set_timer", methods=["POST"])
    def set_timer():
        data = flask.request.json
        durration = data["durration"]
        node.set_timer(durration)
        return {}, 200
    
    @app.route("/api/stop_timer", methods=["GET"])
    def stop_timer():
        try:
            node.stop_timer()
        except AttributeError:
            return {}, 400
        return {}, 200

    @app.route("/api/timer_remaining_time", methods=["GET"])
    def timer_remaining_time():
        return {
            "time_remaining": node.get_timer()
        }, 200
    
    @app.route("/api/set_volume", methods=["PUT"])
    def set_volume():
        try:
            data = flask.request.json
            volume = data["volume_percent"]
            config.set("volume", volume)
            node.set_volume(volume)
        except Exception as e:
            print(e)
        return {}, 200

    @app.route("/api/microphones", methods=["GET"])
    def get_microphones():
        return list_microphones(), 200

    @app.route("/api/speakers", methods=["GET"])
    def get_speakers():
        return list_speakers(), 200
    
    @app.route("/api/wake_word_models", methods=["GET"])
    def get_wake_word_models():
        return [model.split(".")[0] for model in os.listdir(node.wake_word_model_dump) if ".onnx" in model], 200

    @app.route("/api/restart", methods=["POST"])
    def restart():
        try:
            nonlocal node_thread
            node.stop()
            node_thread.join()
            time.sleep(3)
            node_thread = threading.Thread(target=node.start, daemon=True)
            node_thread.start()
        except Exception as e:
            print(e)
            return {}, 400
        return {}, 200
    
    @app.route("/api/upload/wake_word_model", methods=["POST"])
    def upload_wake_word():
        try:
            if "file" not in flask.request.files:
                raise Exception("No file part")

            file = flask.request.files["file"]

            if file.filename == "":
                raise Exception("No file selected")
            
            print(file.filename)

            if file and file.filename.split('.')[-1].lower() in ['.onnx']:
                filename = os.path.join(node.wake_word_model_dump, file.filename)
                file.save(filename)

                return {}, 200
            else:
               raise Exception("Invalid file type")
        except Exception as e:
            print(e)
            return {}, 400

    return app
    