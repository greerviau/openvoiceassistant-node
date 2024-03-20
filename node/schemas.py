import typing

class NodeConfig(typing.TypedDict):
    node_id: str
    node_name: str
    device_ip: str
    hub_up: str
    mic_index: int
    min_audio_sample_length: int
    audio_sample_buffer_length: int
    vad_sensitivity: int
    wake_word: str