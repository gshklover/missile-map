"""
Object storage support
"""
from abc import ABC, abstractmethod
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine
from typing import Sequence


from missilemap import Sighting


class ISightingStorage(ABC):
    """
    Sighting storage interface (asynchronous)
    """
    @property
    def checksum(self) -> int:
        """
        Returns a number representing checksum that changes when sightings are added/removed
        """
        raise NotImplementedError()

    @abstractmethod
    async def add_sighting(self, sighting: Sighting) -> Sighting:
        """
        Adds a new sighting to the storage
        """
        raise NotImplementedError()

    @abstractmethod
    async def remove_sighting(self, sighting: Sighting):
        """
        Removes an existing sighting from the storage
        """
        raise NotImplementedError()

    @abstractmethod
    async def list_sightings(self) -> Sequence[Sighting]:
        """
        List current set of sightings
        """
        raise NotImplementedError()

    @abstractmethod
    async def clear_sightings(self):
        """
        Clear all sightings
        """
        raise NotImplementedError()


class MemoryStorage(ISightingStorage):
    """
    Default in-memory storage implementation
    """

    def __init__(self):
        """
        Initialize the object
        """
        self._sightings = {}
        self._checksum = 0

    @property
    def checksum(self) -> int:
        return self._checksum

    async def add_sighting(self, sighting: Sighting):
        """
        Add a sighting to in-memory storage
        """
        self._sightings[sighting.id] = sighting
        self._checksum += 1
        return sighting

    async def remove_sighting(self, sighting: Sighting):
        """
        Removes a sighting from the storage
        """
        self._sightings.pop(sighting.id)
        self._checksum += 1

    async def list_sightings(self) -> Sequence[Sighting]:
        """
        Get all sightings
        """
        return list(self._sightings.values())

    async def clear_sightings(self):
        """
        Clear all sightings
        """
        self._checksum += 1
        self._sightings.clear()


class MongoDBStorage(ISightingStorage):
    """
    MongoDB-based storage implementation
    """
    def __init__(self, db: AIOEngine):
        self.db = db
        self._checksum = 0

    @property
    def checksum(self) -> int:
        """
        Checksum is incremented on add/remove calls
        """
        return self._checksum

    async def add_sighting(self, sighting: Sighting):
        """
        Store sighting into DB

        :param sighting: sighting object
        """
        res = await self.db.save(sighting)
        self._checksum += 1
        return res

    async def remove_sighting(self, sighting: Sighting):
        """
        Remove specified sighting from the storage
        """
        await self.db.delete(sighting)
        self._checksum += 1

    async def list_sightings(self) -> Sequence[Sighting]:
        """
        List stored sightings
        """
        return await self.db.find(model=Sighting)

    async def clear_sightings(self):
        """
        Clear all sightings
        """
        self._checksum += 1
        return await self.db.get_collection(Sighting).drop()


def get_storage(db_type="mongodb", url='mongodb://localhost:21017', database='missilemap') -> ISightingStorage:
    """
    Get model storage backend.

    :param db_type: DB type. One of: "mongodb", "memory"
    :param url: MongoDB URL (default: mongodb://localhost:27017)
    :param database: database name to use
    """
    if db_type == 'mongodb':
        # object database
        client = AsyncIOMotorClient(url)
        return MongoDBStorage(db=AIOEngine(motor_client=client, database=database))
    elif db_type == 'memory':
        return MemoryStorage()
    else:
        raise ValueError(f'Unknown DB type: {db_type}')

