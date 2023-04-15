import io
import subprocess
from typing import Union
import wave
import os
import numpy as np
import io

def convert_wav(
        wav: Union[wave.Wave_read, bytes],
        sample_rate: int,
        sample_width: int,
        channels: int,
    ) -> bytes:

        if isinstance(wav, wave.Wave_read):
            wav_bytes = wav.readframes(wav.getnframes())
        else:
            wav_bytes = wav

        return subprocess.run(
            [
                "sox",
                "-t",
                "wav",
                "-",
                "-r",
                str(sample_rate),
                "-e",
                "signed-integer",
                "-b",
                str(sample_width * 8),
                "-c",
                str(channels),
                "-t",
                "raw",
                "-",
            ],
            check=True,
            stdout=subprocess.PIPE,
            input=wav_bytes,
        ).stdout

def maybe_convert_wav(
    wav: Union[wave.Wave_read, bytes],
    sample_rate: int,
    sample_width: int,
    channels: int,
) -> bytes:

    if isinstance(wav, wave.Wave_read):
        wav_bytes = wav.readframes(wav.getnframes())
        wav_file = wav
    else:
        wav_bytes = wav
        wav_file = wave.open(io.BytesIO(wav_bytes), "rb")

    if (
        (wav_file.getframerate() != sample_rate)
        or (wav_file.getsampwidth() != sample_width)
        or (wav_file.getnchannels() != channels)
    ):
        # Return converted wav
        return convert_wav(
            wav_bytes,
            sample_rate=sample_rate,
            sample_width=sample_width,
            channels=channels,
        )

    # Return original audio
    return wav_file.readframes(wav_file.getnframes())


def save_wave(wave_file: str, audio_data: bytes, sample_rate: int, sample_width: int, channels: int):

    wf = wave.open(wave_file, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(sample_width)
    wf.setframerate(sample_rate)
    wf.writeframes(audio_data)

def create_wave(audio_data: bytes, sample_rate: int, sample_width: int, channels: int) -> wave.Wave_read:
    
    wav_data = convert_to_wav(audio_data, sample_rate, sample_width, channels)
    wf = wave.open(io.BytesIO(wav_data), 'rb')

    return wf

def convert_to_wav(audio_data: bytes, sample_rate: int, sample_width: int, channels: int) -> bytes:
    wave_io = io.BytesIO()
    wf = wave.open(wave_io, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(sample_width)
    wf.setframerate(sample_rate)
    wf.writeframes(audio_data)

    return wave_io.getvalue()

def load_wave(wave_file_path: str):
    if not os.path.exists(wave_file_path):
        raise RuntimeError('Audio file does not exist')
    return wave.open(wave_file_path, 'rb')