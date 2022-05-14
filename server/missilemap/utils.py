"""
General purpose utilities
"""
import math
from typing import Sequence, Union, Tuple
import numpy
from geopy import Point


def closest_point(p1: Sequence[float], p2: Sequence[float], x: Sequence[float]) -> float:
    """
    Compute alpha of the point on the segment p1 + alpha * (p2 - p1) closest to specified point x.

    :param p1: first segment point (float, float)
    :param p2: second segment point (float, float)
    :param x: reference point
    :return: alpha value. If alpha value is < 0 or > 1.0, the closest point is not within the segment between p1 and p2

    Implementation:
        result = p1 + alpha * (p2 - p1)
        (result - x) * (p2 - p1) = 0
        ((p1 - x) + alpha * (p2 - p1)) * (p2 - p1) = 0
        (p1 - x) * (p2 - p1) + alpha * (p2 - p1) * (p2 - p1) = 0
        alpha = ((x - p1) * (p2 - p1)) / ((p2 - p1) * (p2 - p1))
    """
    p1 = numpy.asarray(p1)
    p2 = numpy.asarray(p2)
    x = numpy.asarray(x)

    assert((p1.shape[0] == 2) and (p2.shape[0] == 2) and (x.shape[0] == 2))

    p2_p1 = p2 - p1
    p2_p1_dot = numpy.dot(p2_p1, p2_p1)
    if p2_p1_dot == 0:
        return 0.0

    return numpy.dot(x - p1, p2_p1) / p2_p1_dot


def get_bearing(p1: Union[Point, Tuple[float, float]], p2: Union[Point, Tuple[float, float]]) -> float:
    """
    Calculate approximate initial bearing for a segment from p1 to p2

    The formulae used is the following:
        θ = atan2(sin(Δlong).cos(lat2), cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))

    :param p1: Point or tuple [latitude, longitude]
    :param p2: Point or tuple [latitude, longitude]
    :return: approximate bearing based on spherical model
    """
    # source: https://gist.github.com/jeromer/2005586 (public domain)
    lat1 = math.radians(p1[0])
    lat2 = math.radians(p2[0])

    diff_longitude = math.radians(p2[1] - p1[1])

    x = math.sin(diff_longitude) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(diff_longitude)

    return math.atan2(x, y)


def normalize_bearing(bearing: float) -> float:
    """
    Normalize bearing within [-pi..+pi]

    :param bearing: bearing in radians
    :return: value in range [-pi..+pi]
    """
    two_pi = 2 * math.pi

    while bearing > math.pi:
        bearing -= two_pi

    while bearing < -math.pi:
        bearing += two_pi

    return bearing
