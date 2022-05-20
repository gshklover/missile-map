from unittest import TestCase

from geopy import Point
from geopy.distance import distance

from missilemap.utils import closest_point
from simulator import Simulator, Observer, random_location
from missilemap.definitions import Target


class TestSimulator(TestCase):
    """
    Test simulation environment
    """

    def test_sightings(self):
        """
        Test generating sightings from a set of targets and observers
        """
        # r = random.Random(12345)

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
                observers.append(Observer(location=random_location(p_from, p_to, DEFAULT_RADIUS), radius=DEFAULT_RADIUS))

        sim = Simulator(targets=[Target(path=path)], observers=observers)

        sightings = sim.sightings

        # check that sightings are within DEFAULT_RADIUS from one of the segments
        for s in sightings:
            is_ok = False

            for segment_from, segment_to in zip(path[:-1], path[1:]):
                alpha = closest_point(
                    (segment_from.latitude, segment_from.longitude),
                    (segment_to.latitude, segment_to.longitude),
                    (s.latitude, s.longitude)
                )
                alpha = min(1.0, max(0.0, alpha))

                loc = (
                    segment_from.latitude * (1 - alpha) + segment_to.latitude * alpha,
                    segment_from.longitude * (1 - alpha) + segment_to.longitude * alpha
                )
                d = distance((s.latitude, s.longitude), loc).meters
                if d <= DEFAULT_RADIUS:
                    is_ok = True
                    break

            self.assertTrue(is_ok)
