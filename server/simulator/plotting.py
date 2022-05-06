"""
Plotting support using bokeh & Jupyter
"""
import math
import os
from typing import Sequence

import pandas
from bokeh.models import GMapOptions
from bokeh.plotting import gmap, GMap
from geopy.distance import distance

from missilemap import Sighting


def render(location, zoom=6, plot_width=1400, plot_height=800, api_key: str = None, title=None,
           sightings: Sequence[Sighting] = None, sighting_size=10) -> GMap:
    """
    Render a map with sightings.

    :param location: (latitude, longitude) pair
    :param zoom: map zoom factor. zoom=6 is approximately whole of Ukraine, zoom=10 is around a city
    :param plot_width: (optional) plot width in pixels
    :param plot_height: (optional) plot height in pixels
    :param api_key: Google Maps API key with JavaScript support enabled
    :param title: (optional) figure title
    :param sightings: (optional) list of sightings to display
    :param sighting_size: (optional) circle size for sightings in pixels (default: 10)

    :return: bokeh.Figure
    """
    if api_key is None:
        if 'MAPS_API_KEY' not in os.environ:
            raise Exception("MAPS_API_KEY environment variable must be defined or api_key= explicitly specified")
        api_key = os.environ['MAPS_API_KEY']

    gmap_options = GMapOptions(lat=location[0], lng=location[1], map_type='roadmap', zoom=zoom)
    figure = gmap(api_key, gmap_options, title=title, width=plot_width, height=plot_height)

    if sightings is not None:
        # render signting points:
        figure.circle(
            x=[s.longitude for s in sightings],
            y=[s.latitude for s in sightings],
            size=sighting_size, fill_color="red", fill_alpha=0.7, line_color=None)

        arrows = []
        for s in sightings:
            head = distance(kilometers=2).destination((s.latitude, s.longitude), bearing=s.azimuth if s.azimuth > 0 else s.azimuth + 2 * math.pi)
            arrows.append({
                'x_start': s.longitude,
                'y_start': s.latitude,
                'x_end': head[1],
                'y_end': head[0]
            })

            # render arrows (NOTE: adding Arrow did not work for some reason)
            # for arrow in arrows:
            #     p.add_layout(Arrow(
            #         x_start=arrow['x_start'],
            #         start_units='data', end_units='data',
            #         y_start=arrow['y_start'],
            #         x_end=arrow['x_end'],
            #         y_end=arrow['y_end'],
            #         line_color='red',
            #         line_width=2
            #     ))

        arrows = pandas.DataFrame(arrows)
        figure.segment(
            x0=arrows['x_start'].values,
            y0=arrows['y_start'].values,
            x1=arrows['x_end'].values,
            y1=arrows['y_end'].values,
            line_color='red',
            line_width=1
        )

    return figure
