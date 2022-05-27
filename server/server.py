"""
REST API server for MissileMap backend.

Run:
    uvicorn server:app --reload

Environment variables:
    MISSILEMAP_DATABASE - database name to use (default: 'missilemap')
"""
import json
import time
import os

from fastapi import FastAPI, status
from missilemap import Sighting, MissileMap
from missilemap.storage import get_storage

CONFIG_NAME = 'MISSILEMAP_CONFIG'


def load_config():
    """
    Load configuration file specified by MISSILEMAP_CONFIG environment variable
    :return:
    """
    if CONFIG_NAME in os.environ:
        with open(os.environ[CONFIG_NAME], 'rb') as stream:
            return json.load(stream)
    return {}


# global application configuration:
config = load_config()

# FastAPI application
app = FastAPI(
    title="MissileMap",
    description="MissileMap REST API server"
)

# initialize DB storage:
storage = get_storage(database=os.environ.get('MISSILEMAP_DATABASE', 'missilemap'))  # odmantic object storage

# initialize core application logic:
core = MissileMap(storage=storage)


# @app.get('/sightings')
# async def _get_sightings():
#     """
#     Get list of reported threats
#     """
#     return await core.list_sightings()


@app.post('/sightings', status_code=status.HTTP_201_CREATED)
async def _post_sighting(sighting: Sighting):
    """
    Post a new sighting

    :param sighting: sighting object
    """
    sighting.timestamp = int(time.time())  # override timestamp
    return await core.add_sighting(sighting)


@app.get('/targets')
async def _get_targets():
    """
    Get list of currently identified targets
    """
    return await core.list_targets()


# @app.post('/register')
# async def _register_user(user):
#     """
#     Called to register a new user
#
#     :param user:
#     :return:
#     """
#     pass
