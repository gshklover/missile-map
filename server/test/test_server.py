"""
Unit testing for REST server
"""
import os
import random
import shutil
import subprocess
import tempfile
import time
from unittest import IsolatedAsyncioTestCase

# requires "Mark directory as -> Source root on top level directory"
from clientapi import ClientAPI
from missilemap import Sighting
from missilemap.storage import get_storage

PROJ_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
PORT = 8000
URL = f'http://localhost:{PORT}'


class TestServer(IsolatedAsyncioTestCase):
    """
    Test REST API server
    """
    _server = None

    @classmethod
    def setUpClass(cls) -> None:
        """
        Called once when initializing the tests
        """
        # start mongodb (FIXME: need a way to pass configuration into server:app)
        cls._tmp_dir = tempfile.mkdtemp(prefix='test_server')

        # start a server process
        cls._server = subprocess.Popen([
            'uvicorn', 'server:app', '--port', str(PORT)
        ], cwd=PROJ_DIR, env={
            **os.environ,
            'MISSILEMAP_DATABASE': 'test'
        })

        cls._api = ClientAPI(base_url=URL)
        time.sleep(3)  # TODO: identify when the application is launched by waiting for the socket to open

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Called once after running the tests
        """
        cls._server.terminate()
        shutil.rmtree(cls._tmp_dir)

    async def test_sightings(self):
        """
        Test inserting sightings
        """
        # cleanup test DB:
        db = get_storage('test').db  # noqa. Assuming it is MongoDBStorage.
        await db.get_collection(Sighting).drop()

        sightings = [
            Sighting(
                timestamp=random.randint(0, 10000),
                latitude=1.0,
                longitude=2.0,
                azimuth=3.0
            ),
            Sighting(
                timestamp=random.randint(0, 10000),
                latitude=1.0,
                longitude=2.0,
                azimuth=3.0
            )
        ]

        for s in sightings:
            self._api.add_sighting(s)

        result = self._api.list_sightings()

        self.assertListEqual(result, sightings)

    async def test_targets(self):
        """
        Test querying identified targets
        """
        pass
