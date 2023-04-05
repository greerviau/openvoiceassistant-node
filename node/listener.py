
import time
import collections
import webrtcvad
from typing import List, Tuple

from node.stream import PyaudioStream
from node.wake import KaldiWake
from node.audio_player import AudioPlayer
from node import config


class Listener:
    def __init__(self, 
                 wake_word: str, 
                 device_idx: int, 
                 sample_rate: int, 
                 sample_width: int,
                 channels: int,
                 sensitivity: int,
                 audio_player: AudioPlayer
    ):
        self.wake_word = wake_word
        self.device_idx = device_idx
        self.sample_rate = sample_rate
        self.sample_width = sample_width
        self.channels = channels
        self.sensitivity = sensitivity
        self.wakeup_sound = config.get('wakeup', 'wakeup_sound')

        self.audio_player = audio_player

        # Define a recording buffer for the start of the recording
        self.recording_buffer = collections.deque(maxlen=2)

        self.stream = PyaudioStream(device_idx=self.device_idx,
                                    sample_rate=self.sample_rate,
                                    channels=self.channels,
                                    sample_width=self.sample_width,
                                    frames_per_buffer=1200)

        #self.starting_sample_size = 
        
        self.stream.start_stream()
        
        self.wake = KaldiWake(wake_word=self.wake_word,
                              sample_rate=self.sample_rate)
        
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(sensitivity)

        self.vad_chunk_size = 960 # 30ms
        self.vad_audio_data = bytes()

        self.engaged_delay = 5 # 5sec
    
    def listen(self, engaged: bool=False):
        audio_data = []
        if not engaged:
            self.wake.listen_for_wake_word(self.stream)
            if self.wakeup_sound:
                self.audio_player.play_audio_file('node/sounds/activate.wav')
            #audio_data = [chunk for chunk in self.stream.recording_buffer]

        # Capture ~0.5 seconds of audio
        for _ in range(20):
            chunk = self.stream.get_chunk()
            audio_data.append(chunk)

        start = time.time()

        while True:
            chunk = self.stream.get_chunk()

            audio_data.append(chunk)

            self.vad_audio_data += chunk

            is_speech = False

            # Process in chunks of 30ms for webrtcvad
            while len(self.vad_audio_data) >= self.vad_chunk_size:
                vad_chunk = self.vad_audio_data[: self.vad_chunk_size]
                self.vad_audio_data = self.vad_audio_data[self.vad_chunk_size:]

                # Speech in any chunk counts as speech
                is_speech = is_speech or self.vad.is_speech(vad_chunk, 16000)

                if engaged and time.time() - start < self.engaged_delay:    # If we are engaged, wait at least 5 seconds to hear something
                    is_speech = True

            if not is_speech:
                # Capture ~0.5 seconds of audio
                for _ in range(10):
                    chunk = self.stream.get_chunk()
                    audio_data.append(chunk)
                if self.wakeup_sound:
                    self.audio_player.play_audio_file('node/sounds/deactivate.wav', asynchronous=True)
                return b''.join(audio_data)