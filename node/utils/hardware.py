import typing

import speech_recognition as sr 
import sounddevice as sd

def list_microphones() -> typing.List[str]:
    mics = sr.Microphone.list_microphone_names()
    mic_list = [f'{i}: {microphone}' for i, microphone in enumerate(mics)]

def select_mic(mic: typing.Union[str, int]) -> typing.Tuple[int, str]:
    microphones = sr.Microphone.list_microphone_names()
    for i, microphone in enumerate(microphones):
        print(f'{i} {microphone}')
    try:
        if isinstance(mic, str):
            mic_index = [idx for idx, element in enumerate(microphones) if mic in element.lower()][0]
        else:
            mic_index = mic
        
        mic_tag = microphones[mic_index]
    except:
        raise RuntimeError('Mic does not exist')
    print('Microphone: ', mic_tag)
    return mic_index, mic_tag

def get_samplerate(mic_index: int) -> int:
    mic_info = sd.query_devices(mic_index, 'input')
    samplerate = int(mic_info['default_samplerate'])
    return samplerate

def get_input_channels(mic_index: int) -> int:
    mic_info = sd.query_devices(mic_index, 'input')
    channels = int(mic_info['max_input_channels'])
    return channels