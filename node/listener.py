
import time
import os
import wave
import webrtcvad
import queue
import sounddevice as sd
import logging
logger = logging.getLogger("listener")

from node.dir import FILESDIR, SOUNDSDIR
from node.wake import OpenWakeWord


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
    
    def listen(self): 
        self.wake.reset()
        buffer = queue.Queue()
        logger.info("Listening...")

        def callback(indata, frames, time, status):
            buffer.put(bytes(indata))

        with sd.InputStream(samplerate=self.sample_rate, 
                        device=self.mic_idx, 
                        channels=self.channels, 
                        blocksize=self.frames_per_buffer,
                        callback=callback,
                        dtype="int16"):
            
            if not self.node.engaged:        
                while self.node.running.is_set():
                    chunk = buffer.get()
                    if self.wake.listen_for_wake_word(chunk): 
                        logger.info("Wake word!")
                        break
                    
            self.node.audio_player.interrupt()
            if self.node.led_controller:
                self.node.led_controller.listen()
            
            if self.wakeup_sound:           
                self.node.audio_player.play_audio_file(os.path.join(SOUNDSDIR, "activate.wav"), asynchronous=True)

            with wave.open(os.path.join(FILESDIR, "command.wav"), "wb") as wav_file:
                wav_file.setframerate(self.sample_rate)
                wav_file.setsampwidth(self.sample_width)
                wav_file.setnchannels(self.channels)

                start = time.time()
                not_speech_start_time = None
                vad_audio_data = bytes()
                while self.node.running.is_set():
                    chunk = buffer.get()
                    if chunk:
                        if self.enable_speex and self.noise_suppression:
                            chunk = self.noise_suppression.process(chunk)
                        wav_file.writeframes(chunk)

                        vad_audio_data += chunk
                        is_speech = False

                        # Process in chunks of 30ms for webrtcvad
                        while len(vad_audio_data) >= self.vad_chunk_size and self.node.running.is_set():
                            vad_chunk = vad_audio_data[: self.vad_chunk_size]
                            vad_audio_data = vad_audio_data[self.vad_chunk_size:]

                            # Speech in any chunk counts as speech
                            is_speech = is_speech or self.vad.is_speech(vad_chunk, self.sample_rate)

                        if time.time() - start < self.engaged_delay:    # If we are engaged, wait a few seconds to hear something
                            is_speech = True
                        elif not is_speech:
                            if not not_speech_start_time:
                                not_speech_start_time = time.time()
                            elif time.time() - not_speech_start_time > 0.5:   # Make sure we get at least .5 seconds of no speech
                                if self.wakeup_sound:
                                    self.node.audio_player.interrupt()
                                    self.node.audio_player.play_audio_file(os.path.join(SOUNDSDIR, "deactivate.wav"), asynchronous=True)
                                return
                            
    def listen_omni_directional(self):
        self.wake.reset()
        buffer = queue.Queue()
        wake_word_detected = False
        logger.info("Listening...")

        def callback(indata, frames, time, status):
            buffer.put(bytes(indata))

        with sd.InputStream(samplerate=self.sample_rate, 
                        device=self.mic_idx, 
                        channels=self.channels, 
                        blocksize=self.frames_per_buffer,
                        callback=callback,
                        dtype="int16"):
            while self.node.running.is_set():
                audio_data = []
                speech_started = False
                not_speech_start_time = None
                vad_audio_data = bytes()
                while self.node.running.is_set():
                    chunk = buffer.get()
                    if chunk:
                        if self.enable_speex and self.noise_suppression:
                            chunk = self.noise_suppression.process(chunk)

                        vad_audio_data += chunk
                        is_speech = False

                        # Process in chunks of 30ms for webrtcvad
                        while len(vad_audio_data) >= self.vad_chunk_size and self.node.running.is_set():
                            vad_chunk = vad_audio_data[: self.vad_chunk_size]
                            vad_audio_data = vad_audio_data[self.vad_chunk_size:]

                            # Speech in any chunk counts as speech
                            is_speech = is_speech or self.vad.is_speech(vad_chunk, self.sample_rate)

                        if not wake_word_detected and self.wake.listen_for_wake_word(chunk): 
                            logger.info("Wake word!")
                            wake_word_detected = True   

                        if is_speech:
                            speech_started = True
                        if speech_started:
                            audio_data.append(chunk)
                            if not is_speech:
                                if not not_speech_start_time:
                                    not_speech_start_time = time.time()
                                elif time.time() - not_speech_start_time > 0.5:   # Make sure we get at least .5 seconds of no speech
                                    if not wake_word_detected:
                                        break
                                    if self.wakeup_sound:
                                        self.node.audio_player.interrupt()
                                        self.node.audio_player.play_audio_file(os.path.join(SOUNDSDIR, "deactivate.wav"), asynchronous=True)
                                   
                                    with wave.open(os.path.join(FILESDIR, "command.wav"), "wb") as wav_file:
                                        wav_file.setframerate(self.sample_rate)
                                        wav_file.setsampwidth(self.sample_width)
                                        wav_file.setnchannels(self.channels)
                                        for chunk in audio_data:
                                            wav_file.writeframes(chunk)
                                    return
                
            