from ..post_processors import MitsubishiPostProcessor, FanucPostProcessor

class PostProcessorFactory:
    _processors = {
        'mitsubishi': MitsubishiPostProcessor,
        'fanuc': FanucPostProcessor,
    }

    @classmethod
    def create(cls, machine_type: str):
        processor_class = cls._processors.get(machine_type.lower())
        if not processor_class:
            raise ValueError(f"Unknown machine type: {machine_type}")
        return processor_class()
