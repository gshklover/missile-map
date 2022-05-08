"""
API to manipulate reported sightings
"""
from odmantic import Model as BaseModel


class Sighting(BaseModel):
    """
    Defines a single sighting
    """
    timestamp: int = 0             # sighting timestamp (in seconds since epoch)
    longitude: float               # location longitude
    latitude: float                # location latitude
    bearing: float                 # flight direction relative to north pole [-pi..pi]
