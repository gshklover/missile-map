"""
API to manipulate reported sightings
"""
from odmantic import Model as BaseModel


class Sighting(BaseModel):
    """
    Defines a single sighting
    """
    timestamp: int = 0             # sighting timestamp (in seconds since epoch)
    latitude: float                # location latitude
    longitude: float               # location longitude
    bearing: float                 # flight direction relative to north pole [-pi..pi]
