from abc import ABC, abstractmethod
from typing import List
from ..core.gcode_parser import GcodeCommand

class PostProcessor(ABC):
    @abstractmethod
    def process(self, commands: List[GcodeCommand]) -> str:
        pass

    @abstractmethod
    def get_header(self) -> str:
        pass

    @abstractmethod
    def get_footer(self) -> str:
        pass
