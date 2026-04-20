import math
from dataclasses import dataclass
from typing import List, Tuple
from .gcode_parser import GcodeCommand

@dataclass
class EstimationResult:
    total_time_seconds: float
    total_distance_mm: float
    estimated_cost: float
    rapid_moves: int
    cutting_moves: int
    total_time_formatted: str

class TimeEstimator:
    def __init__(self, hourly_rate: float = 150.0):
        self.hourly_rate = hourly_rate
        self.rapid_speed = 5000
        self.default_feed = 500

    def estimate(self, commands: List[GcodeCommand]) -> EstimationResult:
        total_time = 0.0
        total_distance = 0.0
        rapid_moves = 0
        cutting_moves = 0
        current_pos = (0.0, 0.0, 0.0)
        current_feed = self.default_feed

        for cmd in commands:
            new_pos = self._get_position(current_pos, cmd)
            distance = self._distance_3d(current_pos, new_pos)

            if cmd.command == 'G00':
                speed = self.rapid_speed
                rapid_moves += 1
            elif cmd.command == 'G01':
                speed = cmd.feed_rate if cmd.feed_rate else current_feed
                cutting_moves += 1
            else:
                speed = current_feed

            if cmd.feed_rate:
                current_feed = cmd.feed_rate

            if speed > 0:
                total_time += distance / speed
            total_distance += distance
            current_pos = new_pos

        total_time_seconds = total_time * 60
        estimated_cost = (total_time_seconds / 3600) * self.hourly_rate
        hours = int(total_time_seconds // 3600)
        minutes = int((total_time_seconds % 3600) // 60)
        seconds = int(total_time_seconds % 60)

        return EstimationResult(
            total_time_seconds=total_time_seconds,
            total_distance_mm=total_distance,
            estimated_cost=estimated_cost,
            rapid_moves=rapid_moves,
            cutting_moves=cutting_moves,
            total_time_formatted=f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        )

    def _get_position(self, current, cmd):
        x = cmd.x if cmd.x is not None else current[0]
        y = cmd.y if cmd.y is not None else current[1]
        z = cmd.z if cmd.z is not None else current[2]
        return (x, y, z)

    def _distance_3d(self, p1, p2):
        return math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2 + (p2[2]-p1[2])**2)
