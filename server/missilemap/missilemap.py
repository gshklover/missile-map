"""
Core logic implementation for missile map application
"""
from typing import Sequence

from .sighting import Sighting
from .user import User


class MissileMap:
    """
    Core logic implementation for missile map server
    """

    def __init__(self, db):
        self._db = db

    async def add_sighting(self, sighting: Sighting) -> Sighting:
        """
        Add a new sighting to the storage.

        :param sighting:
        :return: the sighting object
        """
        return await self._db.save(sighting)

    async def list_sightings(self) -> Sequence[Sighting]:
        """
        Get list of reported sightings
        """
        return await self._db.find(model=Sighting)

    async def register_user(self, User):
        """
        Perform user registration

        :param User:
        :return:
        """