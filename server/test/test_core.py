"""
Test core logic implementation
"""
import asyncio
from unittest import IsolatedAsyncioTestCase

from missilemap.missilemap import AsyncServer


class TestCore(IsolatedAsyncioTestCase):

    async def test_asyncserver(self):
        """
        Test running async services and shutting down the core server cleanly
        """
        result = {'test1': 0, 'test2': 0}
        c = asyncio.Event()

        class TestAsyncServer(AsyncServer):

            def __init__(self):
                super().__init__()

                self.run_service(self._run_test1)
                self.run_service(self._run_test2, period=0.001)

            async def _run_test1(self):
                """
                Simple one-shot service
                """
                result['test1'] = 1

            async def _run_test2(self):
                """
                Periodic increment.
                When done, signal that the service is done.
                NOTE: there is no actual guarantee that this service is done after run_test1(), but in practice it does.
                """
                if result['test2'] < 2:
                    result['test2'] += 1
                else:
                    c.set()

        s = TestAsyncServer()
        await asyncio.wait_for(c.wait(), timeout=1)
        await s.shutdown()

        self.assertDictEqual({
            'test1': 1,
            'test2': 2
        }, result)
