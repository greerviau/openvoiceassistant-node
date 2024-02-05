
import time
import os
import collections
import webrtcvad
import queue
import sounddevice as sd

from node.wake import OpenWakeWord
from node.utils.audio import *


class Listener:
    def __init__(self, node, frames_per_buffer: int = 4000):
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
        
        self.wake = OpenWakeWord(node, wake_word=self.wake_word)
        
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(self.sensitivity)

        self.vad_chunk_size = 960 # 30ms

        self.engaged_delay = 1 # seconds
    
    def listen(self, engaged: bool=False): 
        buffer = queue.Queue()

        def callback(in_data, frame_count, time_info, status):
            buffer.put(bytes(in_data))

        if not engaged:        
            print("Listening for wake word")
            with sd.RawInputStream(samplerate=self.sample_rate, 
                                    device=self.mic_idx, 
                                    channels=self.channels, 
                                    blocksize=self.frames_per_buffer,
                                    dtype="int16",
                                    callback=callback):
                self.wake.reset()
                while True:
                    if not self.node.running.is_set():
                        return
                    if self.wake.listen_for_wake_word(buffer.get()): 
                        print("Wake word!")
                        break
                    
        self.node.audio_player.interrupt()
        if self.node.led_controller:
            self.node.led_controller.listen()
        
        if self.wakeup_sound:           
            self.node.audio_player.play_audio_file(os.path.join(self.node.sounds_dir, "activate.wav"), asynchronous=True)
            #audio_data = [chunk for chunk in stream.recording_buffer]

        audio_data = []

        buffer = queue.Queue()

        with wave.open(os.path.join(self.node.file_dump, "command.wav"), "wb") as wav_file:
            wav_file.setframerate(self.sample_rate)
            wav_file.setsampwidth(self.sample_width)
            wav_file.setnchannels(self.channels)

            with sd.RawInputStream(samplerate=self.sample_rate, 
                                        device=self.mic_idx, 
                                        channels=self.channels, 
                                        blocksize=self.frames_per_buffer,
                                        dtype="int16",
                                        callback=callback):

                start = time.time()
                not_speech_start_time = None
                vad_audio_data = bytes()
                while True:
                    if not self.node.running.is_set():
                        return
                    chunk = buffer.get()
                    if chunk:

                        wav_file.writeframes(chunk)

                        audio_data.append(chunk)
                        vad_audio_data += chunk

                        is_speech = False

                        # Process in chunks of 30ms for webrtcvad
                        while len(vad_audio_data) >= self.vad_chunk_size:
                            if not self.node.running.is_set():
                                return
                            vad_chunk = vad_audio_data[: self.vad_chunk_size]
                            vad_audio_data = vad_audio_data[self.vad_chunk_size:]

                            # Speech in any chunk counts as speech
                            is_speech = is_speech or self.vad.is_speech(vad_chunk, self.sample_rate)
                        
                        #print(is_speech)

                        if time.time() - start < self.engaged_delay:    # If we are engaged, wait a few seconds to hear something
                            is_speech = True
                        elif not is_speech:
                            if not not_speech_start_time:
                                not_speech_start_time = time.time()
                            if time.time() - not_speech_start_time > 0.5:   # Make sure we get at least .5 seconds of no speech
                                not_speech_start_time = None
                                if self.wakeup_sound:
                                    self.node.audio_player.interrupt()
                                    self.node.audio_player.play_audio_file(os.path.join(self.node.sounds_dir, "deactivate.wav"), asynchronous=True)
                                return b"".join(audio_data)
                            