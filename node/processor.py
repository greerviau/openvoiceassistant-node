import requests
import wave
import time

from node.utils.audio import save_wave

class Processor():
    def __init__(self, node):
        self.node = node
        
        self.hub_callback = ''

    def process_audio(self, audio_data: bytes):
        print('Sending audio data to HUB for processing')

        engaged = False

        wf = wave.open('command.wav', 'wb')
        wf.setframerate(self.node.sample_rate)
        wf.setsampwidth(self.node.sample_width)
        wf.setnchannels(self.node.audio_channels)
        wf.writeframes(audio_data)
        wf.close()

        time_sent = time.time()

        payload = {
            'node_id': self.node.node_id,
            'command_audio_data_hex': audio_data.hex(), 
            'command_audio_sample_rate': self.node.sample_rate, 
            'command_audio_sample_width': self.node.sample_width, 
            'command_audio_channels': self.node.audio_channels,
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
            print('Time Deltas')
            print('- Transcribe: ', context['time_to_transcribe'])
            print('- Understand: ', context['time_to_understand'])
            print('- Synth: ', context['time_to_synthesize'])

            response_audio_data_hex = context['response_audio_data_hex']
            response_sample_rate = context['response_audio_sample_rate']
            response_sample_width = context['response_audio_sample_width']

            if response is not None:
                save_wave('response.wav',
                            bytes.fromhex(response_audio_data_hex),
                            response_sample_rate,
                            response_sample_width,
                            1)
                
                self.node.audio_player.play_audio_file('response.wav')
                time.sleep(0.2)
        else:
            print('No response from HUB')

        return engaged