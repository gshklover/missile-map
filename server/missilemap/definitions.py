"""
Type definitions for missile-map core package
"""
from geopy import Point
from geopy.distance import distance
from odmantic import Model as BaseModel
from typing import Sequence, Optional

# timestamps are seconds since epoch (mostly using ints)
from missilemap.utils import get_bearing, interpolate

Timestamp = int

# default target speed: 800km/h
DEFAULT_SPEED = 800000/3600


class Target:
    """
    Base class for simulated targets.
    A target moves along a specified path with a fixed speed.
    """
    __slots__ = ('start_time', 'speed', 'path', 'distances', 'end_time')

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
        self.end_time = self.start_time + sum(self.distances) / self.speed

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

    def at_time(self, timestamp: Timestamp, extrapolate=True) -> Optional[Point]:
        """
        Compute target location at specified time.

        :param timestamp: Query timestamp.
        :param extrapolate: if True (default), extrapolate outside specified path.

        :return: Closest point. If timestamp is < self.start_time or > self.start_time + sum(self.distances) / self.speed
            the function returns extrapolated point.
        """

        if timestamp <= self.start_time:
            if extrapolate:
                meters = self.speed * (self.start_time - timestamp)
                return distance(meters=meters).destination(self.path[1], bearing=get_bearing(self.path[0], self.path[1]))
            else:
                return None

        if timestamp >= self.end_time:
            if extrapolate:
                meters = self.speed * (timestamp - self.end_time)
                return distance(meters=meters).destination(self.path[-1], bearing=get_bearing(self.path[-2], self.path[-1]))
            else:
                return None

        total_time = self.start_time
        for start_point, end_point, dist in zip(self.path[:-1], self.path[1:], self.distances):
            d_time = dist / self.speed
            if timestamp <= total_time + d_time:
                return interpolate(start_point, end_point, (timestamp - total_time) / d_time)

            total_time += d_time

        return self.path[-1]

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

    @property
    def location(self) -> Point:
        """
        Get location as geopy.Point()
        """
        return Point(latitude=self.latitude, longitude=self.longitude)
