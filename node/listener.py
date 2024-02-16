
import time
import os
import webrtcvad
import queue
import sounddevice as sd
import logging
logger = logging.getLogger("listener")

from node.wake import OpenWakeWord
from node.utils.audio import *


class Listener:
    def __init__(self, node, frames_per_buffer: int = 1280):
        self.node = node
        self.wake_word = node.wake_word
        self.mic_idx = node.mic_idx
        self.sample_rate = node.sample_rate
        self.sample_width = node.sample_width
        self.channels = node.audio_channels
        self.frames_per_buffer = frames_per_buffer
        self.sensitivity = node.vad_sensitivity
        self.wakeup_sound = node.wakeup_sound
        self.enable_speex = node.speex_noise_suppression
        self.noise_suppression = None
        if self.enable_speex:
            from speexdsp_ns import NoiseSuppression
            self.noise_suppression = NoiseSuppression.create(self.frames_per_buffer, self.sample_rate)
        
        self.wake = OpenWakeWord(node, wake_word=self.wake_word)
        
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(self.sensitivity)

        self.vad_chunk_size = 960 # 30ms

        self.engaged_delay = 1 # seconds
    
    def listen(self, engaged: bool=False): 
        self.wake.reset()
        buffer = queue.Queue()

        def callback(indata, frames, time, status):
            buffer.put(bytes(indata))

        with sd.InputStream(samplerate=self.sample_rate, 
                        device=self.mic_idx, 
                        channels=self.channels, 
                        blocksize=self.frames_per_buffer,
                        callback=callback,
                        dtype="int16") as stream:
            
            if not engaged:        
                logger.info("Listening for wake word")
                while True:
                    if not self.node.running.is_set():
                        return
                    chunk = buffer.get()
                    if self.wake.listen_for_wake_word(chunk): 
                        logger.info("Wake word!")
                        buffer.queue.clear()
                        break
                    
            self.node.audio_player.interrupt()
            if self.node.led_controller:
                self.node.led_controller.listen()
            
            if self.wakeup_sound:           
                self.node.audio_player.play_audio_file(os.path.join(self.node.sounds_dir, "activate.wav"), asynchronous=True)

            audio_data = []

            with wave.open(os.path.join(self.node.file_dump, "command.wav"), "wb") as wav_file:
                wav_file.setframerate(self.sample_rate)
                wav_file.setsampwidth(self.sample_width)
                wav_file.setnchannels(self.channels)

                start = time.time()
                not_speech_start_time = None
                vad_audio_data = bytes()
                while True:
                    if not self.node.running.is_set():
                        return
                    chunk = buffer.get()
                    if chunk:
                        if self.enable_speex and self.noise_suppression:
                            chunk = self.noise_suppression.process(chunk)
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
                            