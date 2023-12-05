import requests
import time

class Processor():
    def __init__(self, node):
        self.node = node
        
        self.hub_callback = ''

    def process_audio(self, audio_data: bytes):
        print('Sending audio data to HUB for processing')

        engaged = False

        time_sent = time.time()

        command_audio_data = open('command.wav', 'rb')
        print(type(command_audio_data))

        payload = {
            'node_id': self.node.node_id,
            'node_name': self.node.node_name,
            'node_area': self.node.node_area,
            'command_audio_data': command_audio_data,
            'hub_callback': self.hub_callback,
            'last_time_engaged': self.node.last_time_engaged,
            'time_sent': time_sent
        }

        try:
            respond_response = requests.post(
                f'{self.node.hub_api_url}/respond/audio',
                json=payload
            )
        except Exception as e:
            print(repr(e))
            print('Lost connection to HUB')
            connect = False
            while not connect:
                try:
                    retry_response = requests.get(
                        self.node.hub_api_url,
                        json=payload,
                        timeout=30
                    )
                    if retry_response.status_code == 200:
                        connect = True
                        print('\nConnected')
                    else:
                        raise
                except:
                    print('Retrying in 5...')
                    time.sleep(5)

        if respond_response.status_code == 200:

            self.last_time_engaged = time_sent

            context = respond_response.json()

            response = context['response']
            self.hub_callback = context['hub_callback']

            if self.hub_callback: engaged = True

            print('Command: ', context['cleaned_command'])
            print('Skill:', context['skill'])
            print('Action:', context['action'])
            print('Conf:', context['conf'])
            print('Response: ', response)
            print('Deltas')
            print('- Time to Send: ', context['time_recieved'] - context['time_sent'])
            print('- Transcribe: ', context['time_to_transcribe'])
            print('- Understand: ', context['time_to_understand'])
            print('- Action: ', context['time_to_action'])
            print('- Synth: ', context['time_to_synthesize'])
            print('- Run Pipeline: ', context['time_to_run_pipeline'])
            print('- Time to Return: ', time.time() - context['time_returned'])
            print('- Total: ', time.time() - context['time_sent'])
            
            response_audio_data = context['response_audio_data']
            data = bytes.fromhex(response_audio_data)
            with open('response.wav', 'wb') as wav_file:
                wav_file.write(data)
                    
            self.node.audio_player.play_audio_file('response.wav')
        else:
            print('No response from HUB')

        return engaged