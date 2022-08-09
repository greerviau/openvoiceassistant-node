import speech_recognition as sr
import base64
import requests
import numpy as np
import pydub
from pydub.playback import play
import time
import threading

class Node:
    def __init__(self, mic_index, hub_api_uri, cli, debug):
        self.recog = sr.Recognizer()
        self.mic_index = mic_index
        self.hub_api_uri = hub_api_uri
        self.cli = cli
        self.debug = debug

        self.running = True

    def __log(self, text, end='\n'):
        if self.debug:
            print(text, end=end)

    def start(self):
        print('Starting node')
        self.mainloop()

    def mainloop(self):
        while self.running:
            with sr.Microphone(device_index=self.mic_index) as source:
                self.recog.adjust_for_ambient_noise(source, duration=0.5)
                self.__log('Say something!')
                audio = self.recog.listen(source)
                self.__log('Heard sending to hub')
                sample_rate = audio.sample_rate
                raw = audio.get_wav_data()

                raw_base64 = base64.b64encode(raw).decode('utf-8')

                start_time = time.time()

                payload = {'samplerate': sample_rate, 'callback': '', 'audio_file': raw_base64, 'room_id': '1', 'engaged': True}
                response = requests.post(
                    f'http://{self.hub_api_uri}/respond_to_audio',
                    json=payload
                )

                if response.status_code == 200:
                    understanding = response.json()
                    time_sent = understanding['time_sent']
                    self.__log(f'Response delay: {time.time() - time_sent}')
                    self.__log(f'Overall delay: {time.time() - start_time}')

                    self.__log(understanding['command'])
                    audio_data = understanding['audio_data']
                    audio_buffer = base64.b64decode(audio_data)
                    audio = np.frombuffer(audio_buffer, dtype=np.int16)

                    audio_segment = pydub.AudioSegment(
                        audio.tobytes(), 
                        frame_rate=22050,
                        sample_width=audio.dtype.itemsize, 
                        channels=1
                    )
                    play(audio_segment)