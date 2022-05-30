"""
REST API server for MissileMap backend.

Run:
    uvicorn server:app --reload

Environment variables:
    MISSILEMAP_CONFIG - server configuration file path

Config file structure:
    {
        'testing': False,
        'mongodb: {
            'url': 'mongodb://localhost:21017',
            'db_name': 'missilemap'
        }
    }
"""
import geopy
from fastapi import FastAPI, status
from fastapi.encoders import jsonable_encoder
import json
import time
import os
from typing import List


from missilemap import Sighting, MissileMap, Target
from missilemap.storage import get_storage


CONFIG_NAME = 'MISSILEMAP_CONFIG'
DEFAULT_DB_URL = 'mongodb://localhost:21017'
DEFAULT_DB_NAME = 'missilemap'
TESTING = False

# custom JSON encoders
CUSTOM_ENCODER = {
    Target: Target.json_encoder
}


def load_config():
    """
    Load configuration file specified by MISSILEMAP_CONFIG environment variable
    :return:
    """
    if CONFIG_NAME in os.environ:
        with open(os.environ[CONFIG_NAME], 'rb') as stream:
            return json.load(stream)
    return {}


# =================================
# Global application configuration:
# =================================
config = load_config()
TESTING = config.get('testing', False)

# FastAPI application
app = FastAPI(
    title="MissileMap",
    description="MissileMap REST API server"
)

# ======================
# Initialize DB storage:
# ======================
db_url = config.get('mongodb', {}).get('url', DEFAULT_DB_URL)
db_name = config.get('mongodb', {}).get('db_name', DEFAULT_DB_NAME)
storage = get_storage(url=db_url, database=db_name)  # odmantic object storage

# ===================================
# Initialize core application logic:
# ===================================
extra_args = {}
if TESTING:
    extra_args['cleanup_interval'] = -1

core = MissileMap(storage=storage, **extra_args)


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
    if not TESTING:
        sighting.timestamp = int(time.time())  # override timestamp
    return await core.add_sighting(sighting)


@app.get('/targets')
async def _get_targets() -> List[Target]:
    """
    Get list of currently identified targets
    """
    return jsonable_encoder(await core.list_targets(), custom_encoder=CUSTOM_ENCODER)


# @app.post('/register')
# async def _register_user(user):
#     """
#     Called to register a new user
#
#     :param user:
#     :return:
#     """
#     pass
