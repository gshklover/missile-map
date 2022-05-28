"""
Unit testing for REST server
"""
import json
import os
import random
import subprocess
import time
import tempfile
from unittest import IsolatedAsyncioTestCase

# requires "Mark directory as -> Source root on top level directory"
from clientapi import ClientAPI
from missilemap import Sighting
from missilemap.storage import get_storage
from .mongoutils import start_mongodb, stop_mongodb

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

    async def test_sightings(self):
        """
        Test inserting sightings
        """
        # cleanup test DB:
        storage = get_storage(url=f"mongodb://localhost:{self._db_port}", database=TEST_DB)
        db = storage.db  # noqa. Assuming it is MongoDBStorage.
        await db.get_collection(Sighting).drop()

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

        result = sorted(await storage.list_sightings(), key=lambda x: x.timestamp)
        # result = self._api.list_sightings()
        self.assertListEqual(result, sorted(sightings, key=lambda x: x.timestamp))

    async def test_targets(self):
        """
        Test querying identified targets
        """
        pass
        # db = get_storage('test').db  # noqa. Assuming it is MongoDBStorage.
        # await db.get_collection(Sighting).drop()

