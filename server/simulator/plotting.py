"""
Plotting support using bokeh & Jupyter
"""
from bokeh.models import GMapOptions
from bokeh.plotting import gmap, GMap
from geopy import Point
from geopy.distance import distance
import math
import os
import pandas
from typing import Sequence, Tuple, Union


from missilemap import Sighting


def render_path(figure: GMap, path: Sequence[Union[Point, Tuple[float, float]]], line_color='blue', line_width=2, line_alpha=0.8):
    """
    Render specified path on the map chart

    :param figure: GMap object
    :param path: sequence of points to render
    :param line_color: line color (default: blue)
    :param line_width: line width (default: 2.0)
    :param line_alpha: line alpha controlling transparency (default: 0.8)
    """
    x_start = []
    y_start = []
    x_end = []
    y_end = []

    for s, e in zip(path[:-1], path[1:]):
        x_start.append(s[1])
        y_start.append(s[0])
        x_end.append(e[1])
        y_end.append(e[0])

    figure.segment(x0=x_start, y0=y_start, x1=x_end, y1=y_end, line_color=line_color, line_width=line_width, line_alpha=line_alpha)


def render(location, zoom=6, plot_width=1400, plot_height=800, api_key: str = None, title=None,
           sightings: Sequence[Sighting] = None, sighting_size=10,
           paths: Sequence[Sequence[Tuple[float, float]]] = None
           ) -> GMap:
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
    :param paths: (optional) list of paths where each path is a sequence of points [(latitude, longitude), ...]

    :return: bokeh.Figure
    """
    if api_key is None:
        if 'MAPS_API_KEY' not in os.environ:
            raise Exception("MAPS_API_KEY environment variable must be defined or api_key= explicitly specified")
        api_key = os.environ['MAPS_API_KEY']

    gmap_options = GMapOptions(lat=location[0], lng=location[1], map_type='roadmap', zoom=zoom)
    figure = gmap(api_key, gmap_options, title=title, width=plot_width, height=plot_height)

    if sightings is not None and len(sightings):
        # render sighting points:
        figure.circle(
            x=[s.longitude for s in sightings],
            y=[s.latitude for s in sightings],
            size=sighting_size, fill_color="red", fill_alpha=0.7, line_color=None)

        arrows = []
        for s in sightings:
            head = distance(kilometers=2).destination((s.latitude, s.longitude),
                                                      bearing=math.degrees(s.bearing if s.bearing > 0 else s.bearing + 2 * math.pi))
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

    if paths is not None and len(paths):
        # render specified paths as segments
        for path in paths:
            render_path(figure, path)

    return figure
