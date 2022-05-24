"""
Analysis algorithms to support the application
"""
import math
from geopy import Point
from geopy.distance import distance
import numpy
import random
from sklearn.mixture import GaussianMixture
from typing import Sequence

from .definitions import Sighting, Target, DEFAULT_SPEED
from .utils import logger


def _estimate_segment(sightings: Sequence[Sighting]) -> Target:
    """
    Get the segment that best explains specified sightings.

    Assumes linear motion in both directions where:
        latitude = dlat * t + lat0
        longitude = dlon * t + lon0

    Using this to solve linear regression:

            | t 1 0 0 | | dlat |   | latitude0  |
            | ...     | | lat0 | = | ...        |
        A = | 0 0 t 1 | | dlon |   | longitude0 |
            | ...     | | lon0 |   |            |
    """

    # solve least squares to find lat/lon equations:
    timestamps = numpy.array([s.timestamp for s in sightings])
    zeros = numpy.zeros(len(sightings))
    ones = numpy.ones(len(sightings))

    a = numpy.column_stack((
        numpy.concatenate((timestamps, zeros)),
        numpy.concatenate((ones, zeros)),
        numpy.concatenate((zeros, timestamps)),
        numpy.concatenate((zeros, ones))
    ))

    lat = [s.latitude for s in sightings]
    lon = [s.longitude for s in sightings]
    b = lat + lon

    x, res, rank, s = numpy.linalg.lstsq(a, b, rcond=None)

    logger.debug(f"x={x}, res={res}")

    # construct a segment from the solution
    lat_range = min(lat), max(lat)
    lon_range = min(lon), max(lon)

    if x[0] < 0:
        lat_range = lat_range[1], lat_range[0]

    if x[2] < 0:
        lon_range = lon_range[1], lon_range[0]

    # find t_start from lat/long values:
    t_start = min(
        (lat_range[0] - x[1]) / x[0] if x[0] != 0 else max(timestamps),
        (lon_range[0] - x[3]) / x[2] if x[2] != 0 else max(timestamps)
    )

    # find t_end from lat/long values:
    t_end = max(
        (lat_range[1] - x[1]) / x[0] if x[0] != 0 else min(timestamps),
        (lon_range[1] - x[3]) / x[2] if x[2] != 0 else min(timestamps)
    )

    # compute lat/long range from t_start & t_end:
    lat_range_est = (
        (numpy.array([t_start, 1]) * x[:2]).sum(),
        (numpy.array([t_end, 1]) * x[:2]).sum()
    )

    lon_range_est = (
        (numpy.array([t_start, 1]) * x[2:]).sum(),
        (numpy.array([t_end, 1]) * x[2:]).sum()
    )

    path = (
        Point(latitude=lat_range_est[0], longitude=lon_range_est[0]),
        Point(latitude=lat_range_est[1], longitude=lon_range_est[1])
    )

    return Target(
        start_time=t_start,
        path=path,
        speed=distance(path[0], path[1]).meters / (t_end - t_start)
    )


def sightings_to_targets(sightings: Sequence[Sighting],
                         targets: Sequence[Target]):
    """
    Provided a list of sightings and a list of targets, choose best target per sighting

    :param sightings: list of sightings
    :param targets: list of targets

    Returns a list of assigned target indices.

    For each sighting, identify the "closest" target (temporal & spatial)
    """
    result = []

    for sighting in sightings:
        best_idx = -1
        best_dist = math.inf

        for idx, target in enumerate(targets):
            pos = target.at_time(sighting.timestamp)
            d = distance(pos, sighting.location).meters
            if d < best_dist:
                best_dist = d
                best_idx = idx

        result.append(best_idx)

    return result


def _random_target(sightings: Sequence[Sighting]) -> Target:
    """
    Generate a random segment by connecting two sightings together

    :param sightings: list of sightings
    :return: Target object with single segment path
    """
    start, end = None, None
    while start == end:
        start, end = random.choices(sightings, k=2)

    if start.timestamp > end.timestamp:
        start, end = end, start

    return Target(
        start_time=start.timestamp,
        speed=DEFAULT_SPEED,
        path=[start.location, end.location]
    )


def expectation_maximization(sightings: Sequence[Sighting], n_segments: int, iterations=10) -> Sequence[Target]:
    """
    Runs expectation maximization algorithm to partition sightings into segments.

    The algorithm consists of two repeated steps:

    * Assign sightings to groups of linear segments
    * Estimate segments from assigned sightings

    """
    if len(sightings) < 2:
        return []
    sightings = numpy.array(sightings)

    m = GaussianMixture(n_components=n_segments)
    target_idx = m.fit_predict(numpy.array([
        [s.timestamp, s.latitude, s.longitude] for s in sightings
    ])).flatten()

    # # generate N random segments
    targets = [_estimate_segment([s for i, s in zip(target_idx, sightings) if i == segment]) for segment in range(n_segments)]

    # run expectation maximization algorithm:
    for _ in range(iterations):
        prev_idx = target_idx
        target_idx = numpy.array(sightings_to_targets(sightings, targets))
        if numpy.all(prev_idx == target_idx):
            # stop if no change in assignment
            break

        # now group by target and
        targets = [
            _estimate_segment(sightings[target_idx == i]) for i in set(target_idx)
        ]

        if len(targets) < n_segments:
            # Add more segments.
            # FIXME: improve this part by approximating outliers
            for _ in range(len(targets), n_segments):
                targets.append(_random_target(sightings))

    return targets
