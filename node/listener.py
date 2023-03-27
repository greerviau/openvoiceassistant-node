import queue
import vosk
import sounddevice as sd
import pyaudio
import json
import wave
import collections
import webrtcvad
from typing import List, Tuple

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

class KaldiListener(Listener):
    def __init__(self, wake_word: str, device_idx: int, samplerate: int, sensitivity: int, write_file: bool = True):
        super().__init__(wake_word, device_idx, samplerate, sensitivity, write_file)
        # Define the Vosk model and its configuration
        self.model = vosk.Model(lang='en-us')

    def listen(self, engaged: bool, interrupt: Tuple[bool] = (False)):

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
                                    final_text = final["text"].lower().strip()
                                    self.stop_recording()
                                    recording_started = False
                                    # Clear out the recording buffer
                                    self.recording_buffer.clear()
                                    if self.wake_word in final_text or engaged:
                                        return (self.get_audio_data(), True)
                                    else:
                                        print('Command did not engage')
                                        break
                                else:
                                    print('No Recording')
                                    break
                            else:
                                # Check if speech has started
                                partial = json.loads(rec.PartialResult())
                                partial_text = partial["partial"].lower().strip()
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
        super().__init__(wake_word, device_idx, samplerate, write_file)

        self.vad = webrtcvad.Vad()
        self.vad.set_mode(sensitivity)

        self.blocksize = int((samplerate * 30) / 1000)

        self.speech_detected_thresh = 3

        self.channels = [1]

        self.mapping = [c - 1 for c in self.channels]

    def listen(self, engaged: bool, interrupt: Tuple[bool] = (False)):

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