import pyaudio
import wave
import os
from typing import Tuple

def play_audio_file(file: str, device_idx: int, stop_playing: Tuple[bool] = [False], p: pyaudio.PyAudio = pyaudio.PyAudio()):

    CHUNK = 1024

    if not os.path.exists(file):
        raise RuntimeError('File does not exist')

    wf = wave.open(file, 'rb')

    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True,
                    output_device_index=device_idx)

    data = wf.readframes(CHUNK)

    while len(data):
        if stop_playing[0]:
            break
        stream.write(data)
        data = wf.readframes(CHUNK)

    stream.stop_stream()
    stream.close()

    p.terminate()