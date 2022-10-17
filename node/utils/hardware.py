import typing

import speech_recognition as sr 
import sounddevice as sd

def list_microphones() -> typing.List[str]:
    mics = sr.Microphone.list_microphone_names()
    mic_list = [f'{i}: {microphone}' for i, microphone in enumerate(mics)]

def select_mic(mic_tag: str) -> typing.Tuple[int, str]:
    microphones = sr.Microphone.list_microphone_names()
    for i, microphone in enumerate(microphones):
        print(f'{i} {microphone}')
    try:
        mic_index = [idx for idx, element in enumerate(microphones) if mic_tag in element.lower()][0]
    except:
        raise RuntimeError('Mic does not exist')
    mic = microphones[mic_index]
    print('Microphone: ', mic)
    return mic_index, mic

def get_samplerate(mic_index: int) -> int:
    mic_info = sd.query_devices(mic_index, 'input')
    samplerate = int(mic_info['default_samplerate'])
    return samplerate