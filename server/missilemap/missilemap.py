"""
Core logic implementation for missile map application
"""
from typing import Sequence

from . import Sighting
from .storage import ISightingStorage


class MissileMap:
    """
    Core logic implementation for missile map server
    """
    TARGET_SPEED_RANGE = (700000/3600, 1000000/3600)  # target speed range (min, max)

    def __init__(self, storage: ISightingStorage):
        self._storage = storage

    async def add_sighting(self, sighting: Sighting) -> Sighting:
        """
        Add a new sighting to the storage.

        :param sighting:
        :return: the sighting object
        """
        return await self._storage.add_sighting(sighting)

    async def list_sightings(self) -> Sequence[Sighting]:
        """
        Get list of reported sightings
        """
        return await self._storage.list_sightings()

    async def register_user(self, User):
        """
        Perform user registration

        :param User:
        :return:
        """
        raise NotImplementedError()

    def analyze_sightings(self, sightings):
        """
        Analyze specified sightings and produce predicted set of targets

        :param sightings:
        :return:
        """
        # estimate number of linear segments

        raise NotImplementedError()
