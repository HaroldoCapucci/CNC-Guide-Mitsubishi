from .base import PostProcessor
from typing import List
from ..core.gcode_parser import GcodeCommand

class SiemensPostProcessor(PostProcessor):
    def process(self, commands: List[GcodeCommand]) -> str:
        lines = [self.get_header()]
        for cmd in commands:
            parts = []
            if cmd.command == 'G00': parts.append('G0')
            elif cmd.command == 'G01': parts.append('G1')
            else: parts.append(cmd.command)
            if cmd.x is not None: parts.append(f"X{cmd.x:.3f}")
            if cmd.y is not None: parts.append(f"Y{cmd.y:.3f}")
            if cmd.z is not None: parts.append(f"Z{cmd.z:.3f}")
            if cmd.feed_rate: parts.append(f"F{int(cmd.feed_rate)}")
            lines.append(' '.join(parts))
        lines.append(self.get_footer())
        return '\n'.join(lines)
    def get_header(self): return "MSG ('SIEMENS PROGRAM')\nG54 G90 G71"
    def get_footer(self): return "M30"
