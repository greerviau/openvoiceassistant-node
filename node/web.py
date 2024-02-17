import flask
import os
import requests
import time 
import threading
import logging
logger = logging.getLogger("werkzeug")

from node import config
from node.dir import BASEDIR, FILESDIR, WAKEWORDMODELSDIR, LOGFILE
from node.node import Node
from node.updater import Updater
from node.utils.hardware import list_microphones, list_speakers
from node.schemas import NodeConfig

def create_app(node: Node, updater: Updater):

    app = flask.Flask("Node")
        
    @app.route("/api", methods=["GET"])
    def index():
        try:
            updater.check_for_updates()
            update_available = updater.update_available
            version = open(os.path.join(BASEDIR, "VERSION")).read()
            return {
                    "id": config.get("id"),
                    "version": version,
                    "status": "online" if node.run_thread.is_alive() else "crashed",
                    "update_available": update_available
                    }, 200
        except Exception as e:
            logger.exception("Exception in GET /api")
            return {}, 400
    
    @app.route("/api/update", methods=["POST"])
    def update():
        try:
            updater.check_for_updates()
            if updater.update_available:
                threading.Thread(target=updater.update, daemon=True).start()
                return {}, 200
            else:
                return {"No update available"}, 400
        except Exception as e:
            logger.exception("Exception in GET /api")
            return {}, 400
    
    @app.route("/api/restart", methods=["POST"])
    def restart():
        try:
            node.stop()
            time.sleep(3)
            node.start()
        except Exception as e:
            logger.exception("Exception in POST /api/restart")
            return {}, 400
        return {}, 200

    @app.route("/api/config", methods=["GET"])
    def get_config() -> NodeConfig:
        try:
            return config.get(), 200
        except Exception as e:
            logger.exception("Exception in GET /api/config")
            return {}, 400

    @app.route("/api/config", methods=["PUT"])
    def put_config():
        try:
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
        except Exception as e:
            logger.exception("Exception in PUT /api/config")
            return {}, 400
       
    @app.route("/api/play/audio", methods=["POST"])
    def play_audio():
        try:
            data = flask.request.json
            audio_data = data["audio_data"]
            data = bytes.fromhex(audio_data)
            audio_file_path = os.path.join(FILESDIR, "play.wav")
            with open(audio_file_path, "wb") as wav_file:
                wav_file.write(data)
            node.audio_player.interrupt()
            node.audio_player.play_audio_file(audio_file_path, asynchronous=True)
        except Exception as e:
            logger.exception("Exception in POST /api/play/audio")
            return {}, 400
        return {}, 200
    
    @app.route("/api/play/file", methods=["POST"])
    def play_file():
        try:
            data = flask.request.json
            file = data["file"]
            loop = data["loop"]
            audio_file_path = os.path.join(FILESDIR, file)
            if os.file.exists(audio_file_path):
                node.audio_player.interrupt()
                node.audio_player.play_audio_file(audio_file_path, asynchronous=True, loop=loop)
            else:
                return {"error": "Could not find file"}, 404
        except Exception as e:
            logger.exception("Exception in POST /api/play/file")
            return {}, 400
        return {}, 200
    
    @app.route("/api/announce/<text>", methods=["POST"])
    def announce(text: str):
        try:
            respond_response = requests.get(f"{node.hub_api_url}/synthesizer/synthesize/text/{text}")
            context = respond_response.json()
            response_audio_data = context["response_audio_data"]
            data = bytes.fromhex(response_audio_data)
            audio_file_path = os.path.join(FILESDIR, "play.wav")
            with open(audio_file_path, "wb") as wav_file:
                wav_file.write(data)
            node.audio_player.interrupt()
            node.audio_player.play_audio_file(audio_file_path, asynchronous=True)
        except Exception as e:
            logger.exception("Exception in POST /api/announce/<text>")
            return {}, 400
        return {}, 200
    
    @app.route("/api/timer/set", methods=["POST"])
    def set_timer():
        try:
            data = flask.request.json
            durration = data["durration"]
            node.set_timer(durration)
        except Exception as e:
            logger.exception("Exception in POST /api/timer/set")
            return {}, 400
        return {}, 200
    
    @app.route("/api/timer/stop", methods=["POST"])
    def stop_timer():
        try:
            node.stop_timer()
        except AttributeError as e:
            logger.exception("Exception in POST /api/timer/stop")
            return {}, 400
        return {}, 200

    @app.route("/api/timer/remaining", methods=["GET"])
    def timer_remaining_time():
        try:
            return {
                "time_remaining": node.get_timer()
            }, 200
        except AttributeError as e:
            logger.exception("Exception in GET /api/timer/remaining")
            return {}, 400
    
    @app.route("/api/volume/set", methods=["PUT"])
    def set_volume():
        try:
            data = flask.request.json
            volume = data["volume_percent"]
            config.set("volume", volume)
            node.set_volume(volume)
        except Exception as e:
            logger.exception("Exception in PUT /api/volume/set")
            return {}, 400
        return {}, 200

    @app.route("/api/hardware/microphones", methods=["GET"])
    def get_microphones():
        try:
            return list_microphones(), 200
        except AttributeError as e:
            logger.exception("Exception in GET /api/hardware/microphones")
            return {}, 400

    @app.route("/api/hardware/speakers", methods=["GET"])
    def get_speakers():
        try:
            return list_speakers(), 200
        except AttributeError as e:
            logger.exception("Exception in GET /api/hardware/speakers")
            return {}, 400
    
    @app.route("/api/wake_word_models", methods=["GET"])
    def get_wake_word_models():
        try:
            return [model.split(".")[0] for model in os.listdir(WAKEWORDMODELSDIR) if ".onnx" in model], 200
        except AttributeError as e:
            logger.exception("Exception in GET /api/wake_word_models")
            return {}, 400
    
    @app.route("/api/wake_word_model/upload", methods=["POST"])
    def upload_wake_word():
        try:
            if "file" not in flask.request.files:
                raise Exception("No file part")

            file = flask.request.files["file"]

            if file.filename == "":
                raise Exception("No file selected")

            if file and file.filename.rsplit('.')[-1].lower() in ['onnx']:
                filename = os.path.join(WAKEWORDMODELSDIR, file.filename)
                with open(filename, "wb") as file_to_save:
                    file_to_save.write(file.read())
            else:
               raise Exception("Invalid file type")
        except Exception as e:
            logger.exception("Exception in POST /api/wake_word_models/upload")
            return {}, 400
        return {}, 200

    @app.route("/api/upload/file", methods=["POST"])
    def upload_file():
        try:
            if "file" not in flask.request.files:
                raise Exception("No file part")

            file = flask.request.files["file"]

            if file.filename == "":
                raise Exception("No file selected")

            filename = os.path.join(FILESDIR, file.filename)
            with open(filename, "wb") as file_to_save:
                file_to_save.write(file.read())
        except Exception as e:
            logger.exception("Exception in POST /api/upload_file")
            return {}, 400
        return {}, 200
    
    @app.route("/api/logs", methods=["GET"], defaults={'n': 10})
    @app.route("/api/logs/<n>", methods=["GET"])
    def get_logs(n):
        try:
           n = int(n)
           with open(LOGFILE, "r") as file:
                return file.readlines()[-n:], 200
        except Exception as e:
            logger.exception("Exception in GET /api/logs")
            return {}, 400

    return app
    