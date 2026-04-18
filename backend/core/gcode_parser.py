import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

@dataclass
class GcodeCommand:
    command: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    feed_rate: Optional[float] = None
    spindle_speed: Optional[float] = None

class GcodeParser:
    def __init__(self):
        self.commands: List[GcodeCommand] = []

    def parse(self, gcode_content: str) -> List[GcodeCommand]:
        self.commands = []
        lines = gcode_content.strip().split('\n')
        last_command = None
        for line in lines:
            line = self._remove_comments(line).strip()
            if not line:
                continue
            cmd = self._parse_line(line)
            if cmd.command:
                self.commands.append(cmd)
                last_command = cmd
            else:
                if last_command and last_command.command in ('G00', 'G01'):
                    inherited = GcodeCommand(
                        command=last_command.command,
                        x=last_command.x,
                        y=last_command.y,
                        z=last_command.z,
                        feed_rate=last_command.feed_rate,
                        spindle_speed=last_command.spindle_speed
                    )
                    x = re.search(r'X([-\d.]+)', line)
                    y = re.search(r'Y([-\d.]+)', line)
                    z = re.search(r'Z([-\d.]+)', line)
                    if x: inherited.x = float(x.group(1))
                    if y: inherited.y = float(y.group(1))
                    if z: inherited.z = float(z.group(1))
                    self.commands.append(inherited)
        return self.commands

    def _parse_line(self, line: str) -> GcodeCommand:
        cmd = GcodeCommand()
        cmd_match = re.search(r'([GM]\d{2})', line)
        if cmd_match:
            cmd.command = cmd_match.group(1)
        x_match = re.search(r'X([-\d.]+)', line)
        y_match = re.search(r'Y([-\d.]+)', line)
        z_match = re.search(r'Z([-\d.]+)', line)
        f_match = re.search(r'F(\d+)', line)
        s_match = re.search(r'S(\d+)', line)
        if x_match: cmd.x = float(x_match.group(1))
        if y_match: cmd.y = float(y_match.group(1))
        if z_match: cmd.z = float(z_match.group(1))
        if f_match: cmd.feed_rate = float(f_match.group(1))
        if s_match: cmd.spindle_speed = float(s_match.group(1))
        return cmd

    @staticmethod
    def _remove_comments(line: str) -> str:
        if '(' in line:
            line = line[:line.index('(')]
        if ';' in line:
            line = line[:line.index(';')]
        return line.strip()

    def get_path_points(self) -> List[Tuple[float, float, float]]:
        points = []
        x = y = z = 0.0
        for cmd in self.commands:
            if cmd.x is not None: x = cmd.x
            if cmd.y is not None: y = cmd.y
            if cmd.z is not None: z = cmd.z
            if cmd.command in ('G00', 'G01'):
                points.append((x, y, z))
        return points
