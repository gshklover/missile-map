"""
Unit testing for REST server
"""
import asyncio
import json
import os
import random
import subprocess
import time
import tempfile
from unittest import IsolatedAsyncioTestCase

# requires "Mark directory as -> Source root on top level directory"
from geopy import Point

from clientapi import ClientAPI
from missilemap import Sighting, Target
from missilemap.storage import get_storage
from simulator import Observer, Simulator, random_location

from test.mongoutils import start_mongodb, stop_mongodb

PROJ_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
PORT = 8000
URL = f'http://localhost:{PORT}'
TEST_DB = 'test'


class TestServer(IsolatedAsyncioTestCase):
    """
    Test REST API server
    """
    _server = None
    _db_port = None

    @classmethod
    def setUpClass(cls) -> None:
        """
        Called once when initializing the tests
        """
        # start an empty MongoDB server with random port
        cls._db_port = start_mongodb()

        # save config
        config = {
            'testing': True,
            'mongodb': {
                "url": f"mongodb://localhost:{cls._db_port}",
                "db_name": "test"
            }
        }

        fd, cfg_file = tempfile.mkstemp(prefix='testconfig', suffix='.json')
        os.close(fd)
        with open(cfg_file, 'w') as stream:
            json.dump(config, stream)

        # start a server process
        cls._server = subprocess.Popen([
            'uvicorn', 'server:app', '--port', str(PORT)
        ], cwd=PROJ_DIR, env={
            **os.environ,
            'MISSILEMAP_CONFIG': cfg_file
        })

        cls._api = ClientAPI(base_url=URL)
        time.sleep(3)  # TODO: identify when the application is launched by waiting for the socket to open

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Called once after running the tests
        """
        cls._server.terminate()
        stop_mongodb()

    async def asyncSetUp(self) -> None:
        """
        This code is executed before every test.
        """
        await self._clean_sightings()  # cleanup sightings before executing any tests

    async def _clean_sightings(self):
        """
        Clean sightings DB
        """
        storage = get_storage(url=f"mongodb://localhost:{self._db_port}", database=TEST_DB)
        db = storage.db  # noqa. Assuming it is MongoDBStorage.
        await db.get_collection(Sighting).drop()

    async def test_sightings(self):
        """
        Test inserting sightings
        """
        sightings = [
            Sighting(
                timestamp=random.randint(0, 10000),
                latitude=1.0,
                longitude=2.0,
                bearing=3.0
            ),
            Sighting(
                timestamp=random.randint(0, 10000),
                latitude=1.0,
                longitude=2.0,
                bearing=3.0
            )
        ]

        for s in sightings:
            self._api.add_sighting(s)

        storage = get_storage(url=f"mongodb://localhost:{self._db_port}", database=TEST_DB)
        result = sorted(await storage.list_sightings(), key=lambda x: x.timestamp)

        self.assertListEqual(result, sorted(sightings, key=lambda x: x.timestamp))

    async def test_targets(self):
        """
        Test querying identified targets
        """
        r = random.Random(12345)

        # generate sightings using simulator object:
        path = [
            Point(45.361285195897885, 33.90794799044153),
            Point(47.487079766379715, 33.081535775384715),
            Point(49.47728424495352, 27.901909920451157),
            Point(49.83269083681804, 24.09401307480089)
        ]

        path2 = [
            Point(45.361285195897885, 33.90794799044153),
            Point(49.3, 33.081535775384715),
            Point(50.3, 28.3)
        ]

        # generate observer locations:
        DEFAULT_RADIUS = 5000
        observers = []

        for p_from, p_to in zip(path[:-1], path[1:]):
            for _ in range(10):
                observers.append(Observer(location=random_location(p_from, p_to, DEFAULT_RADIUS, random=r), radius=DEFAULT_RADIUS))

        for p_from, p_to in zip(path2[:-1], path2[1:]):
            for _ in range(10):
                observers.append(Observer(location=random_location(p_from, p_to, DEFAULT_RADIUS, random=r), radius=DEFAULT_RADIUS))

        sim = Simulator(targets=[
            Target(path=path, start_time=0),
            Target(path=path2, start_time=30),
        ], observers=observers, random=r)

        # push sightings to the server:
        sightings = sim.sightings
        for s in sightings:
            self._api.add_sighting(s)

        # wait for the sightings to be analyzed
        targets = []
        for i in range(5):
            await asyncio.sleep(1)
            targets = self._api.list_targets()
            if len(targets):
                break

        print([t.to_json() for t in targets])

        self.assertEqual(5, len(targets))
