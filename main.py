import ast
import pathlib
import tkinter as tk

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from slugify import slugify
from ttkwidgets import autocomplete
from thefuzz import fuzz

import autocomplete_box
from autocomplete_box import MatchOnlyAutocompleteCombobox


root_path = pathlib.Path(__file__).parent
region_path = root_path / "Natural_Earth_quick_start" / "50m_cultural" / "ne_50m_admin_0_countries.shp"
schema_path = root_path / "schema.csv"

regions = gpd.read_file(region_path)
schema = pd.read_csv(
    schema_path,
    index_col="country",
    converters={
        "names": ast.literal_eval,
        "region_indexes": ast.literal_eval,
        # "colour": str,
    },
)


candidate_colours = dict(
    C1="#F5A573",
    C2="#E4CD88",
    C3="#F2EC7E",
    C4="#A1E2AF",
    C5="#91E2CE",
)
shadow_colours = dict(
    C1="#231810",
    C2="#221F15",
    C3="#232312",
    C4="#19231B",
    C5="#1A2925",
)


def world_to_screen(canvas, v):
    return (v + np.array((180, -90))) * np.array((canvas.winfo_reqwidth() / 360, -canvas.winfo_reqheight() / 180))


def screen_to_world(canvas, v):
    return v * np.array((360 / canvas.width, -180 / canvas.height)) - np.array((180, -90))


def encode_tag(country_name):
    """Return string slugified for tagging."""
    return slugify(country_name, separator="_")

class WorldMap():
    def __init__(self, canvas, regions, schema):
        self.canvas = canvas
        self.regions = regions
        self.schema = schema
        self.selected = None
        self.highlighted = None
        self.country_state = self.schema.copy()
        self.country_state["selected"] = False
        self.country_state["highlighted"] = False
        self.country_state["guess"] = ""
        polygons = self.create_countries(canvas, regions, schema)
        self.regions["polygons"] = polygons
        self.remove_select()
        return

    def create_countries(self, canvas, countries, schema):
        # Create countries in rank order, from biggest to smallest. Ensures smaller countries are on the top.
        for country_name, scheme in schema.sort_values("order").iterrows():
            for index in scheme["region_indexes"]:
                self.create_country(canvas, countries.loc[index, "geometry"], country_name, fill="grey")
            self.refresh_colour(country_name)

    def create_country(self, canvas, country, name, outline="black", fill="grey", width=1):
        if max([fuzz.ratio(name, c) for c in ["Italy", "Vatican", "San Marino"]]) > 80:
            x = 0
        polygon_ids = self.create_polygon_for_geometry(canvas, country, name, outline, fill, width)
        for _id in polygon_ids:
            canvas.tag_bind(_id, "<Enter>", lambda e: self.do_highlight(name, e))
            canvas.tag_bind(_id, "<Leave>", lambda e: self.remove_highlight(name, e))
            canvas.tag_bind(_id, "<ButtonRelease-1>", lambda e: self.do_select(name, e))
            canvas.tag_bind(_id, "<Double-Button-1>", lambda e: self.force_select(name, e))

    def do_highlight(self, tag, event):
        country_guess_text.set(self.country_state.at[tag, "guess"])
        self.country_state.loc[tag, "highlighted"] = True
        self.refresh_colour(tag)

    def remove_highlight(self, tag, event):
        country_guess_text.set("")
        self.country_state.loc[tag, "highlighted"] = False
        self.refresh_colour(tag)

    def remove_select(self):
        if self.selected is not None:
            self.country_state.loc[self.selected, "selected"] = False
            self.refresh_colour(self.selected)
        self.selected = None
        instruction_text.set("Make selection")

    def _do_select(self, tag, event):
        if self.selected:
            self.country_state.loc[self.selected, "selected"] = False
            self.refresh_colour(self.selected)
        self.country_state.loc[tag, "selected"] = True
        self.refresh_colour(tag)
        self.selected = tag
        instruction_text.set("Guess country")

    def do_select(self, tag, event):
        """Only select if we have not already guessed it."""
        if not len(self.country_state.at[tag, "guess"]):
            self._do_select(tag, event)

    def force_select(self, tag, event):
        """Remove guess and select."""
        old_guess = self.country_state.loc[tag, "guess"]
        self.country_state.loc[tag, "guess"] = ""
        self._do_select(tag, event)
        unset_country(self, old_guess)

    def make_guess(self, guess):
        if self.selected:
            self.country_state.loc[self.selected, "guess"] = guess
            self.remove_select()
            user_entry_text.set("")

    def get_colours(self, country):
        """Return (outline, fill) colours."""
        state = self.country_state.loc[country]
        if len(state["guess"]):
            return ("grey", shadow_colours[state["colour"]])
        elif state["selected"]:
            return ("black", "green")
        elif state["highlighted"]:
            return ("black", "white")
        else:
            return ("black", candidate_colours[state["colour"]])
    def refresh_colour(self, country):
        outline, fill = self.get_colours(country)
        self.canvas.itemconfigure(encode_tag(country), outline=outline, fill=fill)
        return (outline, fill)

    @staticmethod
    def create_polygon_for_geometry(canvas, geometry, name, outline, fill, width):
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
                    *world_to_screen(canvas, np.array(line.coords)).flatten(),
                    outline=outline,
                    fill=fill,
                    width=width,
                    tags=encode_tag(name),
                )
                ids.append(_id)
        return ids


root = tk.Tk()
root.geometry("800x500")
# Sea blue background colour
map_frame = autocomplete_box.ZoomFrame(root)
menu_frame = tk.Frame(root)

canvas = map_frame.canvas

user_entry_text = tk.StringVar()
country_guess_text = tk.StringVar()
instruction_text = tk.StringVar()
progress_text = tk.StringVar()
score_text = tk.StringVar()
user_entry = autocomplete.AutocompleteCombobox(
    menu_frame,
    completevalues=sorted(regions["SOVEREIGNT"].to_list()),
    textvariable=user_entry_text,
)
user_entry.focus_set()
instruction_label = tk.Label(menu_frame, textvariable=instruction_text, width=15, fg="grey")
country_guess = tk.Label(menu_frame, textvariable=country_guess_text, width=20, fg="grey")
progress_label = tk.Label(menu_frame, textvariable=progress_text, width=15)
verify_button = tk.Button(menu_frame, text="Verify")
score_label = tk.Label(menu_frame, textvariable=score_text)

progress_text.set("Progress")
score_text.set("Score")
score = 0

world_map = WorldMap(canvas, regions, schema)


def _set_progress(world_map):
    total_guesses = world_map.country_state['guess'].astype(bool).sum()
    progress_text.set(f"Progress: {total_guesses}/{world_map.country_state.shape[0]}")


def set_country(world_map, event):
    guess = user_entry_text.get()
    if world_map.selected:
        user_entry.set_completion_list(list(set(user_entry._completion_list) - {guess}))
        print(world_map.selected, guess)
        world_map.make_guess(guess)
        _set_progress(world_map)
    else:
        print(guess)

def unset_country(world_map, old_guess):
    country_replacement = set(world_map.country_state.index.intersection({old_guess}))
    user_entry.set_completion_list(list(set(user_entry._completion_list) | country_replacement))
    _set_progress(world_map)


def verify_results(world_map, event):
    guesses = world_map.country_state["guess"]
    marking = pd.Series({
        country: guess in world_map.schema.at[country, "names"]
        for country, guess in guesses[guesses.astype(bool)].items()
    })

    print(f"You got {marking.sum().astype(int)} correct and {(~marking).sum().astype(int)} incorrect")
    for country, guess in guesses[marking[~marking].index].items():
        world_map.force_select(country, event)
    global score
    score = score + marking.sum() - (~marking).sum()
    score_text.set(f"Score: {score}")


user_entry.bind("<<ComboboxSelected>>", lambda e: set_country(world_map, e))
user_entry.bind("<Return>", lambda e: set_country(world_map, e))
verify_button.bind("<ButtonRelease-1>", lambda e: verify_results(world_map, e))

instruction_label.grid(row=0, column=0)
user_entry.grid(row=0, column=1)
country_guess.grid(row=0, column=2)
progress_label.grid(row=0, column=3)
verify_button.grid(row=0, column=4)
score_label.grid(row=0, column=5)

menu_frame.grid(row=0, sticky="NW")
map_frame.grid(row=1, sticky="NSEW")

root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(0, weight=0)
root.grid_rowconfigure(1, weight=1)

root.mainloop()

quit(0)
