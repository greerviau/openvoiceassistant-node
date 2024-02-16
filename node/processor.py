import requests
import os
import time
import logging
logger = logging.getLogger("processor")

class Processor():
    def __init__(self, node):
        self.node = node
        
        self.hub_callback = ""

    def process_audio(self, audio_data: bytes):
        logger.info("Sending audio data to HUB for processing")

        if self.node.led_controller:
            self.node.led_controller.think()

        engaged = False

        time_sent = time.time()

        command_audio_data = open(os.path.join(self.node.file_dump, "command.wav"), "rb").read()

        payload = {
            "node_id": self.node.id,
            "node_name": self.node.name,
            "node_area": self.node.area,
            "command_audio_data": command_audio_data.hex(),
            "hub_callback": self.hub_callback,
            "last_time_engaged": self.node.last_time_engaged,
            "time_sent": time_sent
        }

        self.hub_callback = ""

        try:
            respond_response = requests.post(
                f"{self.node.hub_api_url}/respond/audio",
                json=payload
            )
        except Exception as e:
            logger.error(f"Lost connection to HUB | {repr(e)}")
            return

        try:         
            respond_response.raise_for_status()

            context = respond_response.json()
            response = context["response"]

            logger.info(f"Command: {context['command']}")
            logger.info(f"Cleaned Command: {context['cleaned_command']}")
            logger.info(f"Encoded Command: {context['encoded_command']}")
            logger.info(f"Skill: {context['skill']}")
            logger.info(f"Action: {context['action']}")
            logger.info(f"Conf: {context['conf']}")
            logger.info(f"Response: {response}")
            logger.info("Deltas")
            logger.info(f"- Time to Send: {context['time_received'] - context['time_sent']}")
            logger.info(f"- Transcribe: {context['time_to_transcribe']}")
            logger.info(f"- Understand: {context['time_to_understand']}")
            logger.info(f"- Action: {context['time_to_action']}")
            logger.info(f"- Synth: {context['time_to_synthesize']}")
            logger.info(f"- Run Pipeline: {context['time_to_run_pipeline']}")
            logger.info(f"- Time to Return: {time.time() - context['time_returned']}")
            logger.info(f"- Total: {time.time() - context['time_sent']}")
            
            if response:
                if self.node.led_controller:
                    self.node.led_controller.speak()

                self.last_time_engaged = time_sent

                self.hub_callback = context["hub_callback"]

                if self.hub_callback: engaged = True
                
                response_audio_data = context["response_audio_data"]
                data = bytes.fromhex(response_audio_data)
                response_file_path = os.path.join(self.node.file_dump, "response.wav")
                with open(response_file_path, "wb") as wav_file:
                    wav_file.write(data)
                        
                self.node.audio_player.interrupt()
                self.node.audio_player.play_audio_file(response_file_path)

            else:
                raise Exception("No response from HUB")
            
        except Exception as e:
            logger.exception("Exception while processing audio")

        return engaged