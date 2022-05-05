"""
Unit-testing for storage objects
"""

import datetime
from unittest import IsolatedAsyncioTestCase

from missilemap.storage import get_storage
from missilemap import Sighting


class TestStorage(IsolatedAsyncioTestCase):
    """
    Test working with storage objects
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Initialize DB
        """
        pass

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Cleanup
        """
        pass

    async def test_sighting(self):
        """
        Test storing and retrieving sighting objects
        """
        items = [
            Sighting(timestamp=1234, latitude=1, longitude=2, azimuth=0.1),
            Sighting(timestamp=2345, latitude=2, longitude=3, azimuth=0.2)
        ]
        db = get_storage('test')

        # cleanup:
        await db.get_collection(Sighting).drop()

        # run the test:
        await db.save_all(items)

        result = await db.find(Sighting)

        self.assertListEqual(result, items)
