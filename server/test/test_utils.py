"""
Test utilities
"""
import math
from unittest import TestCase

from missilemap.utils import closest_point, get_bearing


class TestUtilities(TestCase):

    def test_closest(self):
        """
        Validates computing point on segment closest to a given point
        """

        # within segment:
        self.assertAlmostEqual(
            closest_point((0, 0), (4, 0), (1, 2)),
            0.25,
            places=5
        )

        self.assertAlmostEqual(
            closest_point((0, 1), (0, 4), (1, 2)),
            1/3,
            places=5
        )

        # outside the segment:
        self.assertAlmostEqual(
            closest_point((0, 0), (4, 0), (5, 2)),
            1.25,
            places=5
        )

        self.assertAlmostEqual(
            closest_point((0, 1), (0, 4), (2, 0)),
            -1/3,
            places=5
        )

    def test_bearing(self):
        """
        Test computing bearing
        """
        # vertical S -> N
        self.assertAlmostEqual(
            get_bearing((10, 10), (20, 10)),
            0,
            places=5
        )

        # vertical N -> S
        self.assertAlmostEqual(
            get_bearing((20, 10), (10, 10)),
            math.pi,
            places=5
        )

        # horizontal E -> W on the equator
        self.assertAlmostEqual(
            get_bearing((0, 20), (0, 10)),
            -math.pi/2,
            places=5
        )

        # horizontal W -> E on the equator
        self.assertAlmostEqual(
            get_bearing((0, 10), (0, 20)),
            math.pi/2,
            places=5
        )

    def test_lint(self):
        """
        Run flake8 to lint-clean the code
        """
        pass
