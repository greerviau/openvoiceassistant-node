
import time
import collections
import webrtcvad

from node.wake import KaldiWake
from node.utils.audio import *
from node import config


class Listener:
    def __init__(self, node: 'Node'):
        self.node = node
        self.wake_word = config.get('wakeup', 'wake_word')
        self.sample_rate = node.sample_rate
        self.sample_width = node.sample_width
        self.channels = node.channels
        self.sensitivity = node.vad_sensitivity
        self.wakeup_sound = config.get('wakeup', 'wakeup_sound')

        self.stream = node.stream
        self.audio_player = node.audio_player
        self.pause_flag = node.pause_flag

        # Define a recording buffer for the start of the recording
        self.recording_buffer = collections.deque(maxlen=2)
        
        self.wake = KaldiWake(wake_word=self.wake_word,
                              sample_rate=self.sample_rate)
        
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(self.sensitivity)

        self.vad_chunk_size = 960 # 30ms
        self.vad_audio_data = bytes()

        self.engaged_delay = 3 # 5sec
    
    def listen(self, engaged: bool=False):
        self.stream.clear()
        audio_data = []
        if not engaged:
            self.wake.listen_for_wake_word(self.stream)

        self.pause_flag.set()
        
        if self.wakeup_sound:
            self.audio_player.play_audio_file('node/sounds/activate.wav')
            #audio_data = [chunk for chunk in self.stream.recording_buffer]

        # Capture ~0.5 seconds of audio
        s = time.time()
        while time.time() - s < 0.5:
            chunk = self.stream.get_chunk()
            audio_data.append(chunk)

        start = time.time()
        speech_end = 0

        while True:
            chunk = self.stream.get_chunk()

            if chunk:

                audio_data.append(chunk)

                with io.BytesIO() as wav_buffer:
                    wav_file: wave.Wave_write = wave.open(wav_buffer, "wb")
                    with wav_file:
                        wav_file.setframerate(self.sample_rate)
                        wav_file.setsampwidth(self.sample_width)
                        wav_file.setnchannels(self.channels)
                        wav_file.writeframes(chunk)

                    wav_bytes = wav_buffer.getvalue()

                    self.vad_audio_data += maybe_resample_wav(wav_bytes, sample_rate=16000, sample_width=2, channels=1)

                    is_speech = False

                    # Process in chunks of 30ms for webrtcvad
                    while len(self.vad_audio_data) >= self.vad_chunk_size:
                        vad_chunk = self.vad_audio_data[: self.vad_chunk_size]
                        self.vad_audio_data = self.vad_audio_data[self.vad_chunk_size:]

                        # Speech in any chunk counts as speech
                        is_speech = is_speech or self.vad.is_speech(vad_chunk, 16000)

                    if is_speech:
                        speech_end = 0
                    else:
                        if speech_end == 0:
                            is_speech = True
                            speech_end = time.time()
                        elif time.time() - speech_end < 0.5:
                            is_speech = True

                    if engaged and time.time() - start < self.engaged_delay:    # If we are engaged, wait at least 5 seconds to hear something
                        is_speech = True
                    
                    if not is_speech:
                        '''
                        # Capture ~0.5 seconds of audio
                        s = time.time()
                        while time.time() - s < 0.5:
                            chunk = self.stream.get_chunk()
                            audio_data.append(chunk)
                        '''

                        if self.wakeup_sound:
                            self.audio_player.play_audio_file('node/sounds/deactivate.wav', asynchronous=True)
                        return b''.join(audio_data)
                    