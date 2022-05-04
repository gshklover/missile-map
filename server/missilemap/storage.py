"""
Object storage support
"""
# from abc import ABC, abstractmethod

from odmantic import AIOEngine, Model as BaseModel
# from typing import Sequence


# class ICollection(ABC):
#     """
#     Basic async CRUD collection interface
#     """
#     @abstractmethod
#     async def insert_one(self, item: BaseModel):
#         """
#         Insert new item into collection
#
#         :param item:
#         :return:
#         """
#         raise NotImplementedError()
#
#     @abstractmethod
#     async def insert_many(self, items: Sequence[BaseModel]):
#         """
#         Insert specified object into the collection
#
#         :param items: list of items to insert
#         """
#         raise NotImplementedError()
#
#     @abstractmethod
#     async def update_one(self, item: BaseModel):
#         """
#         Update single object
#         """
#         raise NotImplementedError()
#
#     @abstractmethod
#     async def find_one(self, item_id):
#         """
#         Find single object by object ID
#
#         :param item_id:
#         :return:
#         """
#         raise NotImplementedError()
#
#     @abstractmethod
#     async def find_many(self) -> Sequence[BaseModel]:
#         raise NotImplementedError()
#
#     @abstractmethod
#     async def remove_one(self, item_id):
#         raise NotImplementedError()
#
#     @abstractmethod
#     async def remove_many(self):
#         raise NotImplementedError()
#
#
# class IStorage:
#     """
#     Basic storage management interface
#     """
#     def get_collection(self, name: str) -> ICollection:
#         """
#         Get collection specified by name
#
#         :param name: collection name
#         :return:
#         """
#         raise NotImplementedError()
#
#
# class MongoDBStorage(IStorage):
#     """
#     IStorage implementation based on odmantic
#     """
#     def __init__(self, database='missilemap'):
#         self._db = AIOEngine(database=database)
#
#     def get_collection(self, name: str) -> ICollection:
#         return MongoDBCollection(self._db, name)
#
#
# class MongoDBCollection(ICollection):
#     """
#     Wrapper over dmantic storage implementing ICollection interface
#     """
#     def __init__(self, db: AIOEngine, name: str):
#         pass


def get_storage(database='missilemap'):
    """
    Get object storage

    :param database: database name to use
    """
    # object database
    return AIOEngine(database=database)
