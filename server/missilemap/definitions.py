"""
Type definitions for missile-map core package
"""
import dataclasses
from geopy import Point
from geopy.distance import distance
from odmantic import Model as BaseModel
from typing import Sequence, Optional

# timestamps are seconds since epoch (mostly using ints)
from missilemap.utils import interpolate

Timestamp = int

# default target speed: 800km/h
DEFAULT_SPEED = 800000/3600


@dataclasses.dataclass(init=False)
class Target:
    """
    Base class for simulated targets.
    A target moves along a specified path with a fixed speed.
    """
    start_time: Timestamp  # start time in seconds since epoch
    end_time: Timestamp    # end time (when target reaches the end of the path)
    speed: float           # target speed in m/sec
    path: Sequence[Point]  # target path

    def __init__(self, start_time: Timestamp = 0, speed: float = DEFAULT_SPEED, path: Sequence[Point] = None):
        """
        Initializes a target object with trip start time, path and speed.
        Distance (meters) per path segment is computed automatically.

        :param start_time: start time for target (seconds since epoch)
        :param speed: target speed (m/sec)
        :param path: target path [(lat, long), ...]
        """
        super().__init__()

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
                return interpolate(self.path[0], self.path[1], (timestamp - self.start_time) / (self.end_time - self.start_time))
                # meters = self.speed * (self.start_time - timestamp)
                # return distance(meters=meters).destination(self.path[1], bearing=get_bearing(self.path[0], self.path[1]))
            else:
                return None

        if timestamp >= self.end_time:
            if extrapolate:
                return interpolate(self.path[-2], self.path[-1], (timestamp - self.start_time) / (self.end_time - self.start_time))
                # meters = self.speed * (timestamp - self.end_time)
                # return distance(meters=meters).destination(self.path[-1], bearing=get_bearing(self.path[-2], self.path[-1]))
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

    @staticmethod
    def json_encoder(target):
        """
        Converts Target to json
        """
        return {
            'start_time': target.start_time,
            'speed': target.speed,
            'path': [
                [p.latitude, p.longitude] for p in target.path
            ]
        }

    @staticmethod
    def json_decoder(json_obj: dict):
        """
        Converts JSON to Target
        """
        return Target(
            start_time=Timestamp(json_obj['start_time']),
            speed=float(json_obj['speed']),
            path=[Point(*p) for p in json_obj['path']]
        )


class Sighting(BaseModel):
    """
    Defines a single sighting
    """
    timestamp: int                 # sighting timestamp (in seconds since epoch)
    latitude: float                # location latitude (degrees)
    longitude: float               # location longitude (degrees)
    bearing: float                 # flight direction relative to north pole [-pi..pi]

    @property
    def location(self) -> Point:
        """
        Get location as geopy.Point()
        """
        return Point(latitude=self.latitude, longitude=self.longitude)
