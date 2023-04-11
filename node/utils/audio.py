import io
import subprocess
import typing
import wave

def convert_wav(
        self,
        wav_bytes: bytes,
        sample_rate: typing.Optional[int] = None,
        sample_width: typing.Optional[int] = None,
        channels: typing.Optional[int] = None,
    ) -> bytes:
        """Converts WAV data to required format with sox. Return raw audio."""
        if sample_rate is None:
            sample_rate = self.sample_rate

        if sample_width is None:
            sample_width = self.sample_width

        if channels is None:
            channels = self.channels

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
    self,
    wav_bytes: bytes,
    sample_rate: typing.Optional[int] = None,
    sample_width: typing.Optional[int] = None,
    channels: typing.Optional[int] = None,
) -> bytes:
    """Converts WAV data to required format if necessary. Returns raw audio."""
    if sample_rate is None:
        sample_rate = self.sample_rate

    if sample_width is None:
        sample_width = self.sample_width

    if channels is None:
        channels = self.channels

    with io.BytesIO(wav_bytes) as wav_io:
        with wave.open(wav_io, "rb") as wav_file:
            if (
                (wav_file.getframerate() != sample_rate)
                or (wav_file.getsampwidth() != sample_width)
                or (wav_file.getnchannels() != channels)
            ):
                # Return converted wav
                return self.convert_wav(
                    wav_bytes,
                    sample_rate=sample_rate,
                    sample_width=sample_width,
                    channels=channels,
                )

            # Return original audio
            return wav_file.readframes(wav_file.getnframes())