from .base import PostProcessor
from typing import List
from ..core.gcode_parser import GcodeCommand

class FanucPostProcessor(PostProcessor):
    def process(self, commands: List[GcodeCommand]) -> str:
        lines = [self.get_header()]
        n = 10
        for cmd in commands:
            parts = [f"N{n}", cmd.command]
            if cmd.x is not None: parts.append(f"X{cmd.x:.4f}")
            if cmd.y is not None: parts.append(f"Y{cmd.y:.4f}")
            if cmd.z is not None: parts.append(f"Z{cmd.z:.4f}")
            if cmd.feed_rate: parts.append(f"F{int(cmd.feed_rate)}")
            if cmd.spindle_speed: parts.append(f"S{int(cmd.spindle_speed)}")
            lines.append(' '.join(parts))
            n += 10
        lines.append(self.get_footer())
        return '\n'.join(lines)

    def get_header(self) -> str:
        return "O0001\n(FANUC)\nG54 G90 G21"

    def get_footer(self) -> str:
        return "M30\n%"
