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
    timestamp: datetime.datetime   # sighting timestamp (FIXME: odmantic only supports naive datetime objects?)
    longitude: float               # location longitude
    latitude: float                # location latitude
    azimuth: float                 # flight direction relative to north pole [-pi..pi]
