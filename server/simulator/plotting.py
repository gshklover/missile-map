"""
Plotting support using bokeh & Jupyter
"""
import os

from bokeh.models import GMapOptions
from bokeh.plotting import gmap, GMap


def render(location, zoom=6, plot_width=1400, plot_height=800, api_key: str = None, title=None) -> GMap:
    """
    Render a map with sightings.

    :param location: (latitude, longitude) pair
    :param zoom: map zoom factor. zoom=6 is approximately whole of Ukraine, zoom=10 is around a city
    :param plot_width: (optional) plot width in pixels
    :param plot_height: (optional) plot height in pixels
    :param api_key: Google Maps API key with JavaScript support enabled
    :param title: (optional) figure title

    :return: bokeh.Figure
    """
    if api_key is None:
        if 'MAPS_API_KEY' not in os.environ:
            raise Exception("MAPS_API_KEY environment variable must be defined or api_key= explicitly specified")
        api_key = os.environ['MAPS_API_KEY']

    gmap_options = GMapOptions(lat=location[0], lng=location[1], map_type='roadmap', zoom=zoom)
    return gmap(api_key, gmap_options, title=title, width=plot_width, height=plot_height)
