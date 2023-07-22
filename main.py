import pathlib
import tkinter as tk

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from slugify import slugify
from tkinter import ttk
from ttkwidgets import autocomplete

from autocomplete_box import MatchOnlyAutocompleteCombobox


path = pathlib.Path(__file__).parent / "Natural_Earth_quick_start" / "50m_cultural" / "ne_50m_admin_0_countries.shp"

regions = gpd.read_file(path)

screen_w = 800
screen_h = 600


def world_to_screen(v):
    return (v + np.array((180, -90))) * np.array((screen_w / 360, -screen_h / 180))


def screen_to_world(v):
    return v * np.array((360 / screen_w, -180 / screen_h)) - np.array((180, -90))


def encode_tag(country_name):
    """Return string slugified for tagging."""
    return slugify(country_name, separator="_")

class WorldMap():
    def __init__(self, canvas, regions):
        self.canvas = canvas
        self.regions = regions
        self.selected = None
        self.highlighted = None
        polygons = self.create_polygons(canvas, regions)
        self.regions["polygons"] = polygons
        self.country_state = pd.concat({
            country: pd.Series(dict(selected=False, highlighted=False, colour="grey", guess=np.nan))
            for country in self.regions["SOVEREIGNT"].unique()
        },
            axis=1,
        ).T
        return

    def draw(self):
        for geometry in regions["geometry"]:
            self.draw_region(self.canvas, geometry)

    def create_polygons(self, canvas, regions):
        for _, region in regions.iterrows():
            self.create_polygon(canvas, region["geometry"], region["SOVEREIGNT"])

    def create_polygon(self, canvas, geometry, name, outline="black", fill="grey", width=1):
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
                id = canvas.create_polygon(
                    *world_to_screen(np.array(line.coords)).flatten(),
                    outline=outline,
                    fill=fill,
                    width=width,
                    tags=encode_tag(name),
                )
                if name.lower().startswith("united"):
                    x = 0
                    y = 0
                canvas.tag_bind(id, "<Enter>", lambda e: self.do_highlight(name, e))
                canvas.tag_bind(id, "<Leave>", lambda e: self.remove_highlight(name, e))
                canvas.tag_bind(id, "<ButtonRelease-1>", lambda e: self.do_select(name, e))
                canvas.tag_bind(id, "<Double-Button-1>", lambda e: self.force_select(name, e))

    def do_highlight(self, tag, event):
        self.country_state.loc[tag, "highlighted"] = True
        self.refresh_colour(tag)
    def remove_highlight(self, tag, event):
        self.country_state.loc[tag, "highlighted"] = False
        self.refresh_colour(tag)

    def _do_select(self, tag, event):
        if self.selected:
            self.country_state.loc[self.selected, "selected"] = False
            self.refresh_colour(self.selected)
        self.country_state.loc[tag, "selected"] = True
        self.refresh_colour(tag)
        self.selected = tag
    def do_select(self, tag, event):
        """Only select if we have not already guessed it."""
        if pd.isnull(self.country_state.loc[tag, "guess"]):
            self._do_select(tag, event)
    def force_select(self, tag, event):
        """Remove guess and select."""
        self.country_state.loc[tag, "guess"] = np.nan
        self._do_select(tag, event)

    def make_guess(self, guess):
        if self.selected:
            self.country_state.loc[self.selected, "guess"] = guess
            self.country_state.loc[self.selected, "selected"] = False
            self.refresh_colour(self.selected)
            self.selected = None
            user_entry_text.set("")

    def get_colours(self, country):
        """Return (outline, fill) colours."""
        state = self.country_state.loc[country]
        if not pd.isnull(state["guess"]):
            return ("grey", "black")
        elif state["selected"]:
            return ("black", "green")
        elif state["highlighted"]:
            return ("black", "white")
        else:
            return ("black", state["colour"])
    def refresh_colour(self, country):
        outline, fill = self.get_colours(country)
        self.canvas.itemconfigure(encode_tag(country), outline=outline, fill=fill)
        return (outline, fill)


root = tk.Tk()
canvas = tk.Canvas(root, width=screen_w, height=screen_h)
canvas.pack(side=tk.BOTTOM)

user_entry_text = tk.StringVar()
user_entry = autocomplete.AutocompleteCombobox(
    root,
    completevalues=sorted(regions["SOVEREIGNT"].to_list()),
    textvariable=user_entry_text,
)
# user_entry = ttk.Combobox(root, values=sorted(regions["SOVEREIGNT"].to_list()), textvariable=user_entry_text)

world_map = WorldMap(canvas, regions)
user_entry.pack(side=tk.TOP)

def set_country(world_map, event):
    guess = user_entry_text.get()
    if world_map.selected:
        user_entry.set_completion_list(list(set(user_entry._completion_list) - {guess}))
        print(world_map.selected, guess)
        world_map.make_guess(guess)
    else:
        print(guess)


user_entry.bind("<<ComboboxSelected>>", lambda e: set_country(world_map, e))
user_entry.bind("<Return>", lambda e: set_country(world_map, e))

root.mainloop()

quit(0)

