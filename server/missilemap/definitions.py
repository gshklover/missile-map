"""
Type definitions for missile-map core package
"""
from collections import namedtuple

# type used for storing sightings
Timestamp = int

# geographical location
Location = namedtuple('Location', ('latitude', 'longitude'))
