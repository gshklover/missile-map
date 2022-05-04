"""
REST API server for MissileMap backend.

Run:
    uvicorn server:app --reload
"""

from fastapi import FastAPI, status
from missilemap import Sighting
from missilemap.storage import get_storage

"""
Starlette/FastAPI application 
"""
app = FastAPI(
    title="MissileMap",
    description="MissileMap REST API server"
)

# odmantic object storage
db = get_storage()


@app.get('/sightings')
async def _get_sightings():
    """
    Get list of reported threats
    """
    return await db.find(model=Sighting)


@app.post('/sightings', status_code=status.HTTP_201_CREATED)
async def _post_sighting(sighting: Sighting):
    """
    Post a new sighting

    :param sighting: sighting object
    """
    return await db.save(sighting)


# @app.post('/register')
# async def _register_user(user):
#     """
#     Called to register a new user
#
#     :param user:
#     :return:
#     """
#     pass
