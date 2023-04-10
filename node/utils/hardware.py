from typing import List, Dict, Tuple, Union

import sounddevice as sd
import pyaudio

def find_devices(kind) -> List[Dict]:
    if kind not in ['input', 'output']:
        raise RuntimeError('Device kind must be \"input\" or \"output\"')
    devices = sd.query_devices()
    filtered = {}
    for i, device in enumerate(devices):
        try:
            info = sd.query_devices(i, kind)
            filtered[i] = info
        except ValueError:
            pass
    return filtered

def find_microphones() -> List[Dict]:
    return find_devices('input')

def find_speakers() -> List[Dict]:
    return find_devices('output')

def list_microphones() -> List[str]:
    mics = find_microphones()
    mic_list = []
    for i, info in mics.items():
        #print(info)
        name = info['name']
        mic_list.append(f'{i}: {name}')
    return mic_list

def list_speakers() -> List[str]:
    speakers = find_speakers()
    speaker_list = []
    for i, info in speakers.items():
        #print(info)
        name = info['name']
        speaker_list.append(f'{i}: {name}')
    return speaker_list

def select_mic(mic: Union[str, int]) -> Tuple[int, str]:
    microphones = list_microphones()
    try:
        if isinstance(mic, str):
            mic_index = [idx for idx, element in enumerate(microphones) if mic in element.lower()][0]
        else:
            mic_index = mic
        
        mic_tag = microphones[mic_index]
    except Exception as e:
        raise RuntimeError(f'Microphone does not exist')
        
    return mic_index, mic_tag

def select_speaker(speaker: Union[str, int]) -> Tuple[int, str]:
    speakers = list_speakers()
    try:
        if isinstance(speaker, str):
            speaker_index = [idx for idx, element in enumerate(speakers) if speaker in element.lower()][0]
        else:
            speaker_index = speaker
        
        speaker_tag = speakers[speaker_index]
    except Exception as e:
        raise RuntimeError(f'Speaker does not exist')
        
    return speaker_index, speaker_tag

def get_supported_samplerates(mic_index: int, samplerates: List[int]):
    paudio = pyaudio.PyAudio()
    supported_samplerates = []
    for fs in samplerates:
        try:
            if paudio.is_format_supported(
                    fs, 
                    input_device=mic_index, 
                    input_channels=1, 
                    input_format=pyaudio.paInt16):
                supported_samplerates.append(fs)
        except ValueError:
            pass
    return supported_samplerates

def get_samplerate(mic_index: int) -> int:
    mic_info = sd.query_devices(mic_index, 'input')
    samplerate = int(mic_info['default_samplerate'])
    return samplerate

def get_input_channels(mic_index: int) -> int:
    mic_info = sd.query_devices(mic_index, 'input')
    channels = int(mic_info['max_input_channels'])
    return channels