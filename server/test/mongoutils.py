"""
Utilities for running unittests with MongoDB
"""
import os
import random
import shutil
import subprocess
import tempfile
from socket import socket

_TMP_DIR: str = None
_SERVER: subprocess.Popen = None
_PORT: int = 0
_REF_COUNT = 0


def select_port() -> int:
    """
    Try to bind to a random port
    """
    s = socket()
    for i in range(1000):
        port = random.randrange(1025, 65000)
        try:
            s.bind(('127.0.0.1', port))
        except:  # noqa
            continue
        else:
            s.close()
            return port

    raise Exception("Failed to allocate a port")


def start_mongodb():
    """
    Start mongodb server if not started yet
    """
    global _REF_COUNT, _SERVER, _TMP_DIR, _PORT

    _REF_COUNT += 1

    if _SERVER is not None:
        return _PORT

    # start mongodb (FIXME: need a way to pass configuration into server:app)
    _TMP_DIR = tempfile.mkdtemp(prefix='test_server')
    log_file = os.path.join(_TMP_DIR, 'mongodb.log')
    _PORT = select_port()

    print(f"INFO: Starting MongoDB with port={_PORT}. Log file: {log_file}")

    with open(log_file, 'w') as log_stream:
        _SERVER = subprocess.Popen(['mongod', '--dbpath', _TMP_DIR, '--port', str(_PORT)], stdout=log_stream, stderr=log_stream)

    # TODO: wait for the process to start
    return _PORT


def stop_mongodb():
    """
    Stop MongoDB session
    """
    global _REF_COUNT, _SERVER

    _REF_COUNT = max(0, _REF_COUNT - 1)

    if _REF_COUNT == 0 and _SERVER is not None:
        _SERVER.terminate()
        _SERVER.wait(timeout=10)
        _SERVER = None
        shutil.rmtree(_TMP_DIR, ignore_errors=True)
