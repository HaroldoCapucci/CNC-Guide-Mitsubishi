from .base import PostProcessor
from typing import List
from ..core.gcode_parser import GcodeCommand

class HaasPostProcessor(PostProcessor):
    def process(self, commands: List[GcodeCommand]) -> str:
        lines = [self.get_header()]
        for cmd in commands:
            parts = [cmd.command]
            if cmd.x is not None: parts.append(f"X{cmd.x:.4f}")
            if cmd.y is not None: parts.append(f"Y{cmd.y:.4f}")
            if cmd.z is not None: parts.append(f"Z{cmd.z:.4f}")
            if cmd.feed_rate: parts.append(f"F{int(cmd.feed_rate)}")
            lines.append(' '.join(parts))
        lines.append(self.get_footer())
        return '\n'.join(lines)
    def get_header(self): return "O0001 (HAAS)\nG54 G90 G21"
    def get_footer(self): return "M30\n%"
