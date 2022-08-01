import speech_recognition as sr 
import sounddevice as sd
import base64
import requests
import numpy as np
import pydub
from pydub.playback import play
import time

microphones = sr.Microphone.list_microphone_names()
mic_tag = 'microphone'
mic_index = [idx for idx, element in enumerate(microphones) if mic_tag in element.lower()][0]
mic = microphones[mic_index]
print('Microphone: ', mic)

mic_info = sd.query_devices(mic_index, 'input')
samplerate = int(mic_info['default_samplerate'])

engaged = True

r = sr.Recognizer()
while True:
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.5)
        print("Say something!")
        audio = r.listen(source)
        sample_rate = audio.sample_rate
        raw = audio.get_wav_data()

        raw_base64 = base64.b64encode(raw).decode('utf-8')

        start_time = time.time()

        files = {'samplerate': samplerate, 'callback': '', 'audio_file': raw_base64, 'room_id': '1', 'engaged': engaged, 'time_sent': start_time}
        response = requests.post(
            f'http://127.0.0.1:5000/understand_from_audio_and_synth',
            json=files
        )
        if response.status_code == 200:
            understanding = response.json()
            time_sent = understanding['time_sent']
            print('Response delay: ', time.time() - time_sent)
            print('Overall delay: ', time.time() - start_time)

            print(understanding['command'])
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