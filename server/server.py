"""
REST API server for MissileMap backend.

Run:
    uvicorn server:app --reload

Environment variables:
    MISSILEMAP_DATABASE - database name to use (default: 'missilemap')
"""
import time
import os

from fastapi import FastAPI, status
from missilemap import Sighting, MissileMap
from missilemap.storage import get_storage

# FastAPI application
app = FastAPI(
    title="MissileMap",
    description="MissileMap REST API server"
)

# initialize DB storage:
db = get_storage(database=os.environ.get('MISSILEMAP_DATABASE', 'missilemap'))  # odmantic object storage

# initialize core application logic:
core = MissileMap(db=db)


@app.get('/sightings')
async def _get_sightings():
    """
    Get list of reported threats
    """
    return await core.list_sightings()


@app.post('/sightings', status_code=status.HTTP_201_CREATED)
async def _post_sighting(sighting: Sighting):
    """
    Post a new sighting

    :param sighting: sighting object
    """
    sighting.timestamp = int(time.time())  # override timestamp
    return await core.add_sighting(sighting)


# @app.post('/register')
# async def _register_user(user):
#     """
#     Called to register a new user
#
#     :param user:
#     :return:
#     """
#     pass
