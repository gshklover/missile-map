"""
Object storage support
"""
from abc import ABC, abstractmethod
from typing import Sequence

from odmantic import AIOEngine

from missilemap import Sighting


class ISightingStorage(ABC):
    """
    Sighting storage interface (asynchronous)
    """
    @abstractmethod
    async def add_sighting(self, sighting: Sighting) -> Sighting:
        raise NotImplementedError()

    @abstractmethod
    async def list_sightings(self) -> Sequence[Sighting]:
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

    async def add_sighting(self, sighting: Sighting):
        """
        Add a sighting to in-memory storage
        """
        self._sightings[sighting.id] = sighting
        return sighting

    async def list_sightings(self) -> Sequence[Sighting]:
        """
        Get all sightings
        """
        return list(self._sightings.values())


class MongoDBStorage(ISightingStorage):
    """
    MongoDB-based storage implementation
    """
    def __init__(self, db: AIOEngine):
        self.db = db

    async def add_sighting(self, sighting: Sighting):
        """
        Store sighting into DB

        :param sighting: sighting object
        """
        return await self.db.save(sighting)

    async def list_sightings(self) -> Sequence[Sighting]:
        """
        List stored sightings
        """
        return await self.db.find(model=Sighting)


def get_storage(database='missilemap') -> ISightingStorage:
    """
    Get model storage backend.

    :param database: database name to use
    """
    # object database
    return MongoDBStorage(db=AIOEngine(database=database))
