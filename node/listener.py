
import time
import collections
import webrtcvad
import queue
import sounddevice as sd

from node.wake import KaldiWake
from node.utils.audio import *
from node import config


class Listener:
    def __init__(self, node, frames_per_buffer: int = 1024):
        self.node = node
        self.wake_word = node.wake_word
        self.mic_idx = node.mic_idx
        self.sample_rate = node.sample_rate
        self.sample_width = node.sample_width
        self.channels = node.audio_channels
        self.frames_per_buffer = frames_per_buffer
        self.sensitivity = node.vad_sensitivity
        self.wakeup_sound = node.wakeup_sound

        # Define a recording buffer for the start of the recording
        self.recording_buffer = collections.deque(maxlen=2)
        
        self.wake = KaldiWake(wake_word=self.wake_word,
                              sample_rate=self.sample_rate)
        
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(self.sensitivity)

        self.vad_chunk_size = 960 # 30ms
        self.vad_audio_data = bytes()

        self.engaged_delay = 3 # seconds
    
    def listen(self, engaged: bool=False): 
        buffer = queue.Queue()

        def callback(in_data, frame_count, time_info, status):
            buffer.put(bytes(in_data))

        if not engaged:        
            print('Stream started')
            with sd.RawInputStream(samplerate=self.sample_rate, 
                                    device=self.mic_idx, 
                                    channels=self.channels, 
                                    blocksize=self.frames_per_buffer,
                                    dtype="int16",
                                    callback=callback):
                self.wake.reset()
                while True:
                    if self.wake.listen_for_wake_word(buffer.get()): break
                    
        self.node.audio_player.stop_playing()
        self.node.pause_flag.set()
        
        if self.wakeup_sound:
            self.node.audio_player.play_audio_file('node/sounds/activate.wav', asynchronous=True)
            #audio_data = [chunk for chunk in stream.recording_buffer]

        audio_data = []

        buffer.queue.clear()

        with sd.RawInputStream(samplerate=self.sample_rate, 
                                    device=self.mic_idx, 
                                    channels=self.channels, 
                                    blocksize=self.frames_per_buffer,
                                    dtype="int16",
                                    callback=callback):

            start = time.time()

            while True:
                chunk = buffer.get()
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

                        self.vad_audio_data += maybe_resample_wav(wav_bytes, sample_rate=self.sample_rate, sample_width=2, channels=1)

                        is_speech = False

                        # Process in chunks of 30ms for webrtcvad
                        while len(self.vad_audio_data) >= self.vad_chunk_size:
                            vad_chunk = self.vad_audio_data[: self.vad_chunk_size]
                            self.vad_audio_data = self.vad_audio_data[self.vad_chunk_size:]

                            # Speech in any chunk counts as speech
                            is_speech = is_speech or self.vad.is_speech(vad_chunk, self.sample_rate)
                        
                        
                        print(is_speech)
                        '''
                        if is_speech:
                            speech_end = 0
                        else:
                            if speech_end == 0:
                                is_speech = True
                                speech_end = time.time()
                            elif time.time() - speech_end < 0.5:
                                is_speech = True
                        '''

                        if time.time() - start < self.engaged_delay:    # If we are engaged, wait a few seconds to hear something
                            is_speech = True
                        if not is_speech:
                            '''
                            # Capture ~0.5 seconds of audio
                            s = time.time()
                            while time.time() - s < 0.5:
                                chunk = stream.get_chunk()
                                audio_data.append(chunk)
                            '''

                            if self.wakeup_sound:
                                self.node.audio_player.play_audio_file('node/sounds/deactivate.wav', asynchronous=True)
                            return b''.join(audio_data)
                        