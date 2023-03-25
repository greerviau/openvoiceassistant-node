import pyaudio
import wave
import os
import pydub
from pydub.playback import play
from typing import Tuple

class AudioPlayer:
    def __init__(self, speaker_idx: int):
        self.speaker_idx = speaker_idx

        self.p = pyaudio.PyAudio()


    def play_audio(self, audio_bytes: bytes, sample_rate: int, sample_width: int, interrupt: Tuple[bool] = [False]):        
        try:
            self.play_pydub(audio_bytes, sample_rate, sample_width, interrupt=interrupt)
            return
        except Exception as e:
            print('Failed to play with pydub')
            print(repr(e))

        try:
            audio_segment = pydub.AudioSegment(
                audio_bytes, 
                frame_rate=sample_rate,
                sample_width=sample_width, 
                channels=1
            )
            audio_segment.export('response.wav', format='wav')
            
            self.play_pyaudio('response.wav', interrupt=interrupt)
            return
        except Exception as e:
            print('Failed to play with pyaduio')
            print(repr(e))

    def play_pydub(self, audio_bytes: bytes, sample_rate: int, sample_width: int, interrupt: Tuple[bool] = [False]):
        audio = pydub.AudioSegment(
            audio_bytes, 
            frame_rate=sample_rate,
            sample_width=sample_width, 
            channels=1
        )
        play(audio)

    def play_pyaudio(self, file: str, interrupt: Tuple[bool] = [False]):
        CHUNK = 1024

        if not os.path.exists(file):
            raise RuntimeError('File does not exist')

        wf = wave.open(file, 'rb')

        stream = self.p.open(format=self.p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True,
                        output_device_index=self.speaker_idx)

        data = wf.readframes(CHUNK)

        while len(data):
            if interrupt[0]:
                break
            stream.write(data)
            data = wf.readframes(CHUNK)

        stream.stop_stream()
        stream.close()

        self.p.terminate()

