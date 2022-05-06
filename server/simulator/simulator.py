"""
Simulator code for validation
"""
import datetime
import geopy.distance
import math
import numpy

from missilemap import Sighting
from missilemap.definitions import Location


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
