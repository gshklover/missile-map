"""
Type definitions for missile-map core package
"""
from collections import namedtuple

# geographical location
Location = namedtuple('Location', ('latitude', 'longitude'))
