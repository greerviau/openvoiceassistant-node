import queue
import vosk
import sounddevice as sd
import pyaudio
import json
import wave
import collections
import webrtcvad
import numpy as np
import torch
torch.set_num_threads(1)
import torchaudio
torchaudio.set_audio_backend("soundfile")
from typing import List

class Listener:
    def __init__(self, wake_word: str, device_idx: int, samplerate: int, sensitivity: int, write_file: bool = True):
        self.wake_word = wake_word
        self.device_idx = device_idx
        self.samplerate = samplerate
        self.sensitivity = sensitivity
        self.write_file = write_file
        self.recording_file = "recording.wav"
        self.wave_file = None
        self.audio_frames = []

        # Define a buffer to store audio frames
        self.buffer = queue.Queue()
        # Define a recording buffer for the start of the recording
        self.recording_buffer = collections.deque(maxlen=2)
    
    # Define a callback function to process audio data from the stream
    def callback(self, indata, frames, time, status):
        # Add audio data to the buffer
        self.buffer.put(bytes(indata))

    def record_frame(self, audio_frame: bytes):
        if self.write_file:
            if self.wave_file is None:
                self.wave_file = wave.open(self.recording_file, "wb")
                self.wave_file.setnchannels(1)
                self.wave_file.setsampwidth(2)
                self.wave_file.setframerate(self.samplerate)
            self.wave_file.writeframes(audio_frame)
        self.audio_frames.append(audio_frame)
    
    def stop_recording(self):
        if self.wave_file:
            self.wave_file.close()

    def reset_recording(self):
        self.wave_file = None
        self.audio_frames = []

    def get_audio_frames(self) -> List[bytes]:
        return self.audio_frames
    
    def get_audio_data(self) -> bytes:
        return b''.join(self.audio_frames)

    def get_audio_data_hex(self) -> str:
        return self.get_audio_data().hex()

class VoskListener(Listener):
    def __init__(self, wake_word: str, device_idx: int, samplerate: int, sensitivity: int, write_file: bool = True):
        super().__init__(wake_word, device_idx, samplerate, sensitivity)
        # Define the Vosk model and its configuration
        self.model = vosk.Model("model")

    def listen(self, engaged: bool):

        # Define a flag to indicate if speech has started
        recording_started = False

        # Set up the sounddevice stream
        with sd.RawInputStream(
            samplerate=self.samplerate, 
            channels=1,
            device=self.device_idx, 
            callback=self.callback, 
            blocksize=8000, 
            dtype="int16"):
            
            while True:
                try:
                    rec = vosk.KaldiRecognizer(self.model, self.samplerate)
                    print('Listening...')
                    while True:
                            # Get audio frames from the buffer
                            frame = self.buffer.get()

                            # Add audio frames to the Vosk recognizer
                            if rec.AcceptWaveform(frame):
                                final_text = ''
                                if recording_started:
                                    print('Recording stopped')
                                    final = json.loads(rec.Result())
                                    print(final)
                                    final_text = final["text"]
                                    self.stop_recording()
                                    recording_started = False
                                    # Clear out the recording buffer
                                    self.recording_buffer.clear()
                                if self.wake_word in final_text or engaged:
                                    return self.get_audio_data()
                                else:
                                    print('Command did not engage')
                                    break
                            else:
                                # Check if speech has started
                                partial = json.loads(rec.PartialResult())
                                partial_text = partial["partial"]
                                # Check for hotword
                                if not recording_started and partial_text not in ['', 'the']:
                                    self.reset_recording()
                                    # Write the recording buffer to the file
                                    for f in self.recording_buffer:
                                        self.record_frame(f)
                                    recording_started = True
                                    print('Recording started...')
                                
                            # If we have detected the hotword start writing audio frames to file
                            # If we havent detected the hotword, write audio frames to the buffer
                            # The recording buffer avoids a cutoff at the begining of the recording
                            if recording_started:
                                self.record_frame(frame)
                            else:
                                self.recording_buffer.append(frame)

                except KeyboardInterrupt:
                    break

class WebRTCVADListener(Listener):
    def __init__(self, wake_word: str, device_idx: int, samplerate: int, sensitivity: int, write_file: bool = True):
        super().__init__(wake_word, device_idx, samplerate)

        self.vad = webrtcvad.Vad()
        self.vad.set_mode(sensitivity)

        self.blocksize = int((samplerate * 30) / 1000)

        self.speech_detected_thresh = 3

        self.channels = [1]

        self.mapping = [c - 1 for c in self.channels]

    def listen(self, engaged: bool):

        # Define a flag to indicate if speech has started
        recording_started = False

        # Set up the sounddevice stream
        with sd.RawInputStream(
            samplerate=self.samplerate, 
            channels=max(self.channels),
            device=self.device_idx, 
            callback=self.callback, 
            blocksize=self.blocksize, 
            dtype="int16"):

            speech_detected = 0

            while True:
                try:
                    # Get audio frames from the buffer
                    frame = self.buffer.get()

                    if self.vad.is_speech(frame, self.samplerate):
                        print('speech')
                        speech_detected += 1
                    else:
                        print('no speech')
                        speech_detected = 0

                    if speech_detected > self.speech_detected_thresh and not recording_started:
                        print('Speech detected')
                        print('Recording...')
                        recording_started = True
                        self.reset_recording()
                        # Write the recording buffer to the file
                        for f in self.recording_buffer:
                            self.record_frame(f)
                    elif not speech_detected and recording_started:
                        print('Recording stopped')
                        recording_started = False
                        self.stop_recording()
                        # Clear out the recording buffer
                        self.recording_buffer.clear()
                        #return self.get_audio_data()
                        
                    # If we have detected the hotword start writing audio frames to file
                    # If we havent detected the hotword, write audio frames to the buffer
                    # The recording buffer avoids a cutoff at the begining of the recording
                    if recording_started:
                        self.record_frame(frame)
                    else:
                        self.recording_buffer.append(frame)

                except KeyboardInterrupt:
                    break

class SileroVADListener(Listener):
    def __init__(self, wake_word: str, device_idx: int, samplerate: int, sensitivity: int, write_file: bool = True):
        super().__init__(wake_word, device_idx, samplerate)

        self.model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                              model='silero_vad',
                              force_reload=False)
        
        (get_speech_timestamps,
        save_audio,
        read_audio,
        VADIterator,
        collect_chunks) = utils

        self.blocksize = int(self.samplerate / 10)

        self.speech_detected_thresh = 3

    # Provided by Alexander Veysov
    def int2float(self, sound):
        abs_max = np.abs(sound).max()
        sound = sound.astype('float32')
        if abs_max > 0:
            sound *= 1/abs_max
        sound = sound.squeeze()  # depends on the use case
        return sound
    
    def is_speech(self, audio_chunk):
        
        audio_int16 = np.frombuffer(audio_chunk, np.int16)

        audio_float32 = self.int2float(audio_int16)
        
        # get the confidences and add them to the list to plot them later
        confidence = self.model(torch.from_numpy(audio_float32), 16000).item()
        print(confidence)
        return True

    def listen(self, engaged: bool):

        # Define a flag to indicate if speech has started
        recording_started = False

        # Set up the sounddevice stream
        stream = pyaudio.PyAudio().open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.samplerate,
            input=True,
            frames_per_buffer=self.blocksize,
            input_device_index=self.device_idx)

        speech_detected = 0

        while True:
            try:
                # Get audio frames from the buffer
                frame = stream.read(16000, exception_on_overflow=False)

                #frame = noisereduce.reduce_noise(frame, 1536)

                if self.is_speech(frame):
                    print('speech')
                    speech_detected += 1
                else:
                    print('no speech')
                    speech_detected = 0

                if speech_detected > self.speech_detected_thresh and not recording_started:
                    print('Speech detected')
                    print('Recording...')
                    recording_started = True
                    self.reset_recording()
                    # Write the recording buffer to the file
                    for f in self.recording_buffer:
                        self.record_frame(f)
                elif not speech_detected and recording_started:
                    print('Recording stopped')
                    recording_started = False
                    self.stop_recording()
                    # Clear out the recording buffer
                    self.recording_buffer.clear()
                    #return self.get_audio_data()
                    
                # If we have detected the hotword start writing audio frames to file
                # If we havent detected the hotword, write audio frames to the buffer
                # The recording buffer avoids a cutoff at the begining of the recording
                if recording_started:
                    self.record_frame(frame)
                else:
                    self.recording_buffer.append(frame)

            except KeyboardInterrupt:
                break