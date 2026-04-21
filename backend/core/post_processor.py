from ..post_processors.mitsubishi import MitsubishiPostProcessor
from ..post_processors.fanuc import FanucPostProcessor
from ..post_processors.haas import HaasPostProcessor
from ..post_processors.siemens import SiemensPostProcessor
from ..post_processors.heidenhain import HeidenhainPostProcessor

class PostProcessorFactory:
    _processors = {
        'mitsubishi': MitsubishiPostProcessor,
        'fanuc': FanucPostProcessor,
        'haas': HaasPostProcessor,
        'siemens': SiemensPostProcessor,
        'heidenhain': HeidenhainPostProcessor,
    }
    @classmethod
    def create(cls, machine_type: str):
        proc = cls._processors.get(machine_type.lower())
        if not proc: raise ValueError(f"Unknown machine: {machine_type}")
        return proc()
