import typing

class NodeConfig(typing.TypedDict):
    node_id: str
    node_name: str
    node_api_url: str
    mic_index: int
    min_audio_sample_length: int
    vad_sensitivity: int