import speech_recognition as sr 
import sounddevice as sd

def select_mic(mic_tag):
    microphones = sr.Microphone.list_microphone_names()
    print(microphones)
    try:
        mic_index = [idx for idx, element in enumerate(microphones) if mic_tag in element.lower()][0]
    except:
        raise RuntimeError('Mic does not exist')
    mic = microphones[mic_index]
    print('Microphone: ', mic)
    return mic_index, mic

def get_samplerate(mic_index):
    mic_info = sd.query_devices(mic_index, 'input')
    samplerate = int(mic_info['default_samplerate'])
    return samplerate