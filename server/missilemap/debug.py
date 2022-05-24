"""
Debug utilities.
"""


class Profiling:
    """
    Helper class to add profiling to a block
    """
    def __init__(self):
        self._profile = None

    def __enter__(self):
        import cProfile

        self._profile = cProfile.Profile()
        self._profile.enable()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._profile.disable()
        self._profile.print_stats(sort='cumtime')


def profiling():
    """
    Used for profiling a block of code in a notebook

    example::
        >> with profiling():
              ...
    """
    return Profiling()
