import requests
import os
import time

class Processor():
    def __init__(self, node):
        self.node = node
        
        self.hub_callback = ""

    def process_audio(self, audio_data: bytes):
        print("Sending audio data to HUB for processing")

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
            print(f"Lost connection to HUB | {repr(e)}")
            return

        try:         
            respond_response.raise_for_status()

            context = respond_response.json()
            response = context["response"]

            print("Command: ", context["command"])
            print("Cleaned Command: ", context["cleaned_command"])
            print("Encoded Command: ", context["encoded_command"])
            print("Skill:", context["skill"])
            print("Action:", context["action"])
            print("Conf:", context["conf"])
            print("Response: ", response)
            print("Deltas")
            print("- Time to Send: ", context["time_recieved"] - context["time_sent"])
            print("- Transcribe: ", context["time_to_transcribe"])
            print("- Understand: ", context["time_to_understand"])
            print("- Action: ", context["time_to_action"])
            print("- Synth: ", context["time_to_synthesize"])
            print("- Run Pipeline: ", context["time_to_run_pipeline"])
            print("- Time to Return: ", time.time() - context["time_returned"])
            print("- Total: ", time.time() - context["time_sent"])
            
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
            print(e)

        return engaged