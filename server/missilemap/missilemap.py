"""
Core logic implementation for missile map application
"""
import asyncio
from typing import Sequence

from .definitions import Sighting, Target
from .analysis import analyze_sightings
from .storage import ISightingStorage

DEFAULT_CLEANUP_INTERVAL = 3.0   # time between cleanup intervals
DEFAULT_ANALYSIS_INTERVAL = 1.0  # minimum time (seconds) between analysis rounds


class AsyncServer:
    """
    Base class for asynchronous server implementation with support for services
    """
    def __init__(self):
        # async services support
        self._shutting_down = asyncio.Event()  # set when shutdown process is initiated
        self._services = []  # list of tasks representing current services

    async def shutdown(self):
        """
        Shutdown any running services and wait for completion.
        """
        self._shutting_down.set()
        while len(self._services):
            await self._services.pop()

    def run_service(self, func, period=None, name=None):
        """
        Runs specified co-routine as a service

        :param func: async routine
        :param period: (optional) if specified, will execute specified routine with specified period (seconds)
        :param name: (optional) task name

        :return:
        """
        if period is not None:
            task = asyncio.get_running_loop().create_task(self._run_periodic(func, period), name=name)
        else:
            task = asyncio.get_running_loop().create_task(func(), name=name)

        self._services.append(task)
        # TODO: filter out completed tasks from self._services

    async def _run_periodic(self, func, period):
        """
        Runs specified co-routine with specified period

        :param func: function to run
        :param period: period (seconds)
        """
        while not self._shutting_down.is_set():
            try:
                await asyncio.wait_for(self._shutting_down.wait(), timeout=period)
            except asyncio.TimeoutError:
                await func()
            else:
                break


class MissileMap(AsyncServer):
    """
    Core logic implementation for missile map server.
    Uses dependency injection for main components such as sightings storage.

    The implementation is asynchronous: services run in a loop until shutdown is called.
    """
    TARGET_SPEED_RANGE = (700000/3600, 1000000/3600)  # target speed range (min, max)

    @property
    def storage(self) -> ISightingStorage:
        """
        Returns sightings storage object
        """
        return self._storage

    def __init__(self, storage: ISightingStorage,
                 analysis_interval: float = DEFAULT_ANALYSIS_INTERVAL,
                 cleanup_interval: float = DEFAULT_CLEANUP_INTERVAL):
        """
        Initializes MissileMap object

        :param storage: storage for sightings
        :param cleanup_interval: if > 0, specified time (seconds) between sightings cleanup intervals
        """
        super().__init__()
        self._storage = storage
        self._targets = []

        # create a service that will run periodic analysis
        if analysis_interval > 0:
            self.run_service(self._analysis_service, period=analysis_interval)
        if cleanup_interval > 0:
            self.run_service(self._cleanup_service, period=cleanup_interval)

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

    async def list_targets(self) -> Sequence[Target]:
        """
        Get current list of identified targets
        """
        return self._targets

    async def register_user(self, User):
        """
        Perform user registration

        :param User:
        :return:
        """
        raise NotImplementedError()

    async def _analysis_service(self):
        """
        Runs periodic analysis on the set of sightings.

        FIXME: use separate process to run the computation
        """
        self._targets = analyze_sightings(await self.list_sightings())

    async def _cleanup_service(self):
        """
        Runs periodic cleanup for the sightings
        """
        pass
