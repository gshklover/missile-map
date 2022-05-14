"""
Simulator code for validation
"""
import dataclasses
import datetime
import random
from typing import Sequence, Tuple, Optional

import bokeh.plotting
import geopy.distance
from geopy import Point
from geopy.distance import distance
import math
import numpy

from missilemap import Sighting
from missilemap.definitions import Location
from .plotting import render
from missilemap.utils import closest_point, get_bearing, normalize_bearing

# default target speed: 800km/h
DEFAULT_SPEED = 800000/3600


def random_sighting(location: Location, distance: float, azimuth: float) -> Sighting:
    """
    Generates a random sighting around the specified point

    :param location: location
    :param distance: standard deviation distance in kilometers
    :param azimuth: sighting direction

    :return: a random sighting sampled with normal distribution around mean=location and std=distance
    """

    # add azimuth noise:
    azimuth += numpy.random.normal(loc=0, scale=math.pi/10)
    if azimuth > math.pi:
        azimuth -= 2 * math.pi
    elif azimuth < -math.pi:
        azimuth += 2 * math.pi

    # add location noise with normal around specified location
    location = geopy.distance.distance(kilometers=abs(numpy.random.normal(0, distance))).destination(location, bearing=numpy.random.randint(0, 360))

    return Sighting(
        latitude=location[0],
        longitude=location[1],
        timestamp=datetime.datetime.now().timestamp(),
        azimuth=azimuth
    )


def random_location(from_location, to_location, distance: float):
    """
    Generate random locations along the specified path (with random distance from the path)

    :param from_location: Point or tuple (latitude, longitude)
    :param to_location: Point or tuple (latitude, longitude)
    :param distance: distance from the segment
    :return:
    """
    alpha = random.random()

    pos = (
        from_location[0] * (1 - alpha) + alpha * to_location[0],
        from_location[1] * (1 - alpha) + alpha * to_location[1]
    )

    distance *= random.random() / 1000

    return geopy.distance.distance(kilometers=distance).destination(pos, bearing=random.random() * 360)


def _add_bearing_noise(bearing: float, noise: float) -> float:
    """
    Add random bearing noise

    :param bearing: original bearing, radians [-pi..+pi]
    :param noise: max absolute noise (radians)
    :return: modified bearing
    """
    return normalize_bearing(bearing + noise * (random.random() * 2 - 1))


class Target:
    """
    Base class for simulated targets.
    A target moves along a specified path with a fixed speed.
    """
    __slots__ = ('start_time', 'speed', 'path', 'distances')

    def __init__(self, start_time: int = 0, speed: float = DEFAULT_SPEED, path: Sequence[Point] = None):
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


class Observer:
    """
    Base class for simulated observers.
    An observer sends a sighting when observing a target.
    """
    __slots__ = ('location', 'radius')

    def __init__(self, location: Point, radius: float):
        """
        Initializes an observer.

        :param location: location of the observer on the map
        :param radius: observation radius (meters). Will only see targets within the specified radius.
        """
        self.location = location
        self.radius = radius


# defines a simulation field
@dataclasses.dataclass
class Field:
    latitude_range: Tuple[float, float]
    longitude_range: Tuple[float, float]

    @property
    def center(self) -> Tuple[float, float]:
        return (
            0.5 * (self.latitude_range[0] + self.latitude_range[1]),
            0.5 * (self.longitude_range[0] + self.longitude_range[1])
        )


DEFAULT_FIELD = Field(
    latitude_range=(48.598, 49.248),
    longitude_range=(32.767, 33.780)
)

DEFAULT_BEARING_NOISE = math.pi / 10  # default bearing noise (0..1.0)


class Simulator:
    """
    Over-time simulator for tracking missile sightings.
    Analysis is performed off-line. Simulation starts at timestamp=0. All timestamps are relative to the simulation start time.
    """

    def __init__(self,
                 targets: Sequence[Target], observers: Sequence[Observer],
                 field: Field = DEFAULT_FIELD,
                 bearing_noise=DEFAULT_BEARING_NOISE):
        self.field = field
        self.targets = tuple(targets)
        self.observers = tuple(observers)
        self.bearing_noise = bearing_noise
        self.sightings = self._generate_sightings(self.targets, self.observers)

    def _generate_sightings(self, targets: Sequence[Target], observers: Sequence[Observer]) -> Sequence[Sighting]:
        """
        Perform analysis of targets and observers and generate sightings.

        :param targets: list of targets with time
        :param observers: list of observers with time
        :return: list of all sightings generated by targets and observers
        """
        result = []
        for target in targets:
            for observer in observers:
                s = self._get_sighting_for(target, observer)
                if s is not None:
                    result.append(s)

        return sorted(result, key=lambda x: x.timestamp)

    def _analyze_sightings(self, sightings: Sequence[Sighting]):
        """
        Perform sighting analysis and generate predictions

        :param sightings: set of available sightings
        :return: list of predicted targets
        """

        raise NotImplementedError()

    def _get_sighting_for(self, target: Target, observer: Observer) -> Optional[Sighting]:
        """
        Get possible sighting for the specified observer and target.

        :param observer: observer object
        :param target: target object
        :return: Sighting if sighting was generated, or None
        """
        total_time = target.start_time  # total time spent on the path (seconds)

        # find a segment closest to the observer
        closest_sighting = None
        closest_distance = -math.inf  # closest observed distance (meters)

        for segment_from, segment_to, segment_distance in zip(target.path[:-1], target.path[1:], target.distances):
            # find point on the segment closest to the observer:
            alpha = closest_point(
                (segment_from.latitude, segment_from.longitude),
                (segment_to.latitude, segment_to.longitude),
                (observer.location.latitude, observer.location.longitude)
            )
            alpha = min(max(alpha, 0.0), 1.0)

            segment_loc = (
                segment_from.latitude * (1 - alpha) + segment_to.latitude * alpha,
                segment_from.longitude * (1 - alpha) + segment_to.longitude * alpha
            )
            d = distance(segment_loc, observer.location).meters

            if d >= observer.radius:
                if closest_sighting is not None:
                    return closest_sighting
                else:
                    continue

            # select closest
            if closest_sighting is None or d < closest_distance:
                segment_time = distance(segment_from, segment_loc).meters / target.speed
                segment_bearing = _add_bearing_noise(get_bearing(segment_from, segment_to), self.bearing_noise)

                closest_sighting = Sighting(
                    timestamp=total_time + segment_time,
                    latitude=observer.location.latitude,
                    longitude=observer.location.longitude,
                    bearing=segment_bearing
                )
                closest_distance = d

            # total time spent so far on the path:
            total_time += segment_distance / target.speed

        return closest_sighting

    def render(self, timestamp=None, plot_width=1400, plot_height=800) -> bokeh.plotting.GMap:
        """
        Render current simulation state over a map.

        :param timestamp: (optional) timestamp for analysis
        :param plot_width: (optional) figure width (pixels, default=1400)
        :param plot_height: (optional) figure height (pixels, default=800)

        :return: bokeh.plotting.GMap chart
        """
        sightings = self.sightings

        if timestamp is not None:
            sightings = [s for s in self.sightings if s.timestamp <= timestamp]

        return render(
            location=self.field.center,
            plot_width=plot_width,
            plot_height=plot_height,
            sightings=sightings,
            paths=[[(p.latitude, p.longitude) for p in target.path] for target in self.targets]
        )
