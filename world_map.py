import copy
import enum
import re

import numpy as np
import pandas as pd
import shapely

import utils


CountryState = enum.Enum("CountryState", "open highlighted selected guessed verified disputed")


def create_polygon_for_geometry(canvas, geometry, tag, outline, fill, width):
    ids = []
    if isinstance(geometry, shapely.MultiPolygon):
        polys = geometry.geoms
    else:
        polys = [geometry]
    for poly in polys:
        boundary = poly.boundary
        if isinstance(boundary, shapely.MultiLineString):
            lines = boundary.geoms
        else:
            lines = [boundary]
        for line in lines:
            _id = canvas.create_polygon(
                # *utils.world_to_screen(canvas, np.array(line.coords)).flatten(),
                *utils.world_to_screen(canvas, utils.wgs84_to_mercator(np.array(line.coords))).flatten(),
                outline=outline,
                fill=fill,
                width=width,
                tags=tag,
            )
            ids.append(_id)
    return ids


def substitute_style_schema(country_style, colour_options, country_colour_code):
    country_style = copy.deepcopy(country_style)
    for state, state_value in country_style.items():
        for style_type, style_value in state_value.items():
            match = re.match(r"(C[A-Z]+)", style_value)
            if match:
                country_style[state][style_type] = colour_options[match.group(1)][country_colour_code]
    return country_style


class Country:
    def __init__(self, canvas, tag, name, shape, style_schema, bindings):
        self._canvas = canvas
        self.tag = tag
        self.name = name
        self.shape = shape
        self._state = None
        self.style_schema = style_schema
        self._draw_shape(canvas, shape, tag, bindings)
        self.state = CountryState.open

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._state = state
        style = self.style_schema[state.name]
        self._canvas.itemconfigure(self.tag, outline=style["outline"], fill=style["fill"])

    def _draw_shape(self, canvas, shape, tag, bindings, outline="black", fill="grey", width=1):
        if not isinstance(shape, pd.Series):
            shape = pd.Series([shape])
        for _shape in shape:
            self._make_polygon(canvas, _shape, tag, bindings, outline, fill, width)

    def _make_polygon(self, canvas, shape, tag, bindings, outline, fill, width):
        polygon_ids = create_polygon_for_geometry(canvas, shape, tag, outline, fill, width)
        for _id in polygon_ids:
            for binding in bindings:
                # The binding functions take the country name as argument instead of event.
                # Lists break lambdas (closure) so we make a function to properly convert each function.
                def get_binding_function(func):
                    return lambda _: func(self.name)
                canvas.tag_bind(_id, binding[0], get_binding_function(binding[1]))
                # canvas.tag_bind(_id, binding[0], binding[1])

    def __repr__(self):
        return f"<{type(self)} {self.name}>"


class WorldMap:
    def __init__(self, canvas, regions, country_schema, style_schema, country_bindings):
        # Background is blue for the sea.
        canvas.configure(bg="#006994")

        self.canvas = canvas
        self.regions = regions
        self.country_schema = country_schema
        self.style_schema = style_schema
        self.selected = None
        self.highlighted = None

        self.countries = {name: Country(
            canvas,
            utils.encode_tag(name),
            name,
            regions.at[name, "geometry"],
            substitute_style_schema(style_schema["country_style"],
                                    style_schema["colour_codes"],
                                    country_schema.at[name, "colour"]),
            country_bindings,
        )
            # Create countries in rank order, from biggest to smallest. Ensures smaller countries are on the top.
            for name, row in country_schema.sort_values("order").iterrows()
        }
        for country in country_schema.index[country_schema["disputed"]]:
            self.countries[country].state = CountryState.disputed

        # Zoom in.
        self.canvas.scan_dragto(20, 20, gain=1)
