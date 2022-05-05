"""
API to manipulate reported sightings
"""
import datetime
# from pydantic import BaseModel
from odmantic import Model as BaseModel


class Sighting(BaseModel):
    """
    Defines a single sighting
    """
    timestamp: int                 # sighting timestamp (in seconds since epoch)
    longitude: float               # location longitude
    latitude: float                # location latitude
    azimuth: float                 # flight direction relative to north pole [-pi..pi]
