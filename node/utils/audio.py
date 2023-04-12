import io
import subprocess
from typing import Union
import wave

def convert_wav(
        wav_bytes: bytes,
        sample_rate: int,
        sample_width: int,
        channels: int,
    ) -> bytes:

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
    wav: Union[bytes, wave.Wave_read],
    sample_rate: int,
    sample_width: int,
    channels: int,
) -> bytes:

    if isinstance(wav, wave.Wave_read):
        wav_bytes = wav.readframes(wav.getnframes())
    else:
        wav_bytes = wav

    with io.BytesIO(wav_bytes) as wav_io:
        with wave.open(wav_io, "rb") as wav_file:
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