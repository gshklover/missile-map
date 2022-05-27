"""
Test for analysis code
"""
import random
from unittest import TestCase

import numpy
from geopy import Point

from missilemap import Target
from missilemap.analysis import expectation_maximization, sightings_to_targets
from simulator import Observer, random_location, Simulator


class TestAnalysis(TestCase):

    def test_expectation_maximization(self):
        r = random.Random(12345)

        path = [
            Point(45.361285195897885, 33.90794799044153),
            Point(47.487079766379715, 33.081535775384715),
            Point(49.47728424495352, 27.901909920451157),
            Point(49.83269083681804, 24.09401307480089)
        ]

        # generate observer locations:
        DEFAULT_RADIUS = 5000
        observers = []

        for p_from, p_to in zip(path[:-1], path[1:]):
            for _ in range(10):
                observers.append(Observer(location=random_location(p_from, p_to, DEFAULT_RADIUS, random=r), radius=DEFAULT_RADIUS))

        sim = Simulator(targets=[Target(path=path)], observers=observers, random=r)

        proj = expectation_maximization(
            sightings=sim.sightings,
            n_segments=len(path) - 1,
            iterations=100
        )

        # expected to reconstruct the original segments with 10 sightings per segment
        res = sightings_to_targets(sightings=sim.sightings, targets=proj)
        counts = numpy.bincount(res)
        self.assertListEqual(list(counts), [9, 10, 11])
