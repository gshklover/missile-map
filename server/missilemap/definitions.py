"""
Type definitions for missile-map core package
"""
from geopy import Point
from geopy.distance import distance
from odmantic import Model as BaseModel
from typing import Sequence

# timestamps are seconds since epoch (mostly using ints)
Timestamp = int

# default target speed: 800km/h
DEFAULT_SPEED = 800000/3600


class Target:
    """
    Base class for simulated targets.
    A target moves along a specified path with a fixed speed.
    """
    __slots__ = ('start_time', 'speed', 'path', 'distances')

    def __init__(self, start_time: Timestamp = 0, speed: float = DEFAULT_SPEED, path: Sequence[Point] = None):
        """
        Initializes a target object with trip start time, path and speed.
        Distance (meters) per path segment is computed automatically.

        :param start_time: start time for target (seconds since epoch)
        :param speed: target speed (m/sec)
        :param path: target path [(lat, long), ...]
        """
        self.start_time = start_time
        self.speed = speed
        self.path = tuple(path) if path else tuple()
        self.distances = tuple([
            distance(prev_pos, next_pos).meters for prev_pos, next_pos in zip(self.path[:-1], self.path[1:])
        ])

    @property
    def start_location(self) -> Point:
        """
        Target start location
        """
        return self.path[0]

    @property
    def end_location(self) -> Point:
        """
        Target end location
        """
        return self.path[-1]

    @property
    def total_distance(self) -> float:
        return sum(self.distances)

    def __str__(self) -> str:
        """
        For debugging
        """
        return f"Target(start_time={self.start_time}, speed={self.speed}, path={self.path})"

    def __repr__(self) -> str:
        return self.__str__()


class Sighting(BaseModel):
    """
    Defines a single sighting
    """
    timestamp: int = 0             # sighting timestamp (in seconds since epoch)
    latitude: float                # location latitude (degrees)
    longitude: float               # location longitude (degrees)
    bearing: float                 # flight direction relative to north pole [-pi..pi]
