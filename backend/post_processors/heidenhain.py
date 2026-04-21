from .base import PostProcessor
from typing import List
from ..core.gcode_parser import GcodeCommand

class HeidenhainPostProcessor(PostProcessor):
    def process(self, commands: List[GcodeCommand]) -> str:
        lines = [self.get_header()]
        for cmd in commands:
            if cmd.command == 'G00': line = 'L'
            elif cmd.command == 'G01': line = 'L'
            else: continue
            if cmd.x is not None: line += f" X+{cmd.x:.3f}"
            if cmd.y is not None: line += f" Y+{cmd.y:.3f}"
            if cmd.z is not None: line += f" Z+{cmd.z:.3f}"
            if cmd.feed_rate: line += f" F{int(cmd.feed_rate)}"
            lines.append(line)
        lines.append(self.get_footer())
        return '\n'.join(lines)
    def get_header(self): return "BEGIN PGM CNC-GUIDE MM\nBLK FORM 0.1 Z X+0 Y+0 Z-20\nBLK FORM 0.2 X+100 Y+100 Z+0"
    def get_footer(self): return "END PGM CNC-GUIDE MM"
