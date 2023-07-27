import ast
import pathlib
import tkinter as ttk

import pandas as pd
import yaml

from menu import Menu
import tkk_plus
import utils
from world_map import (
    CountryState,
    WorldMap,
)


root_path = pathlib.Path(__file__).parent
region_path = root_path / "Natural_Earth_quick_start" / "50m_cultural" / "ne_50m_admin_0_countries.shp"
country_schema_path = root_path / "country_schema.csv"
style_schema_path = root_path / "style_schema.yaml"


regions = utils.read_regions(region_path).set_index("SOVEREIGNT")
country_schema = pd.read_csv(
    country_schema_path,
    index_col="country",
    converters={
        "names": ast.literal_eval,
        "region_indexes": ast.literal_eval,
        # "colour": str,
    },
)
with open(style_schema_path, "r") as f:
    style_schema = yaml.safe_load(f)


class GoWhere:
    def __init__(self, master_frame, regions, country_schema, style_schema):
        # Stop changing focus with tab key.
        root.unbind_all("<<NextWindow>>")
        root.unbind_all("<<PrevWindow>>")
        map_frame = tkk_plus.ZoomFrame(root)
        canvas = map_frame.canvas
        world_map = WorldMap(
            canvas, regions, country_schema, style_schema,
            country_bindings=[
                ("<Enter>", self.apply_highlight_country),
                ("<Leave>", self.remove_highlight_country),
                ("<ButtonRelease-1>", self.weak_select_country),
                ("<Double-Button-1>", self.strong_select_country),
            ],
            )

        menu_frame = ttk.Frame(root)
        valid_countries = country_schema.index[~country_schema["disputed"]]
        menu = Menu(menu_frame, valid_countries, self.make_guess, self.verify_results)

        menu_frame.grid(row=0, sticky="NW")
        map_frame.grid(row=1, sticky="NSEW")

        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(0, weight=0)
        root.grid_rowconfigure(1, weight=1)

        self.valid_countries = valid_countries
        self.master_frame = master_frame
        self.menu = menu
        self.world_map = world_map
        self.countries_guessed = pd.Series(dtype="object")
        self.countries_correct = []
        self.deselect_country(regions.index[0])

    def make_guess(self, user_entry):
        selected_country = self.world_map.selected
        if (selected_country and user_entry):
            self.countries_guessed[selected_country.name] = user_entry
            self.menu.remove_country_option(user_entry)
            self.menu.reset_user_entry()
            self.menu.progress = len(self.countries_correct) + len(self.countries_guessed)
            selected_country.state = CountryState.guessed
            self.deselect_country(selected_country.name)

    def verify_results(self):
        marking = self.countries_guessed.index == self.countries_guessed
        correct = self.countries_guessed.index[marking]
        incorrect = self.countries_guessed.index[~marking]

        print(f"You got {len(correct)} correct and {len(incorrect)} incorrect")

        self.countries_correct.extend(correct)
        for country in correct:
            self.world_map.countries[country].state = CountryState.verified
        for country, guess in self.countries_guessed[incorrect].items():
            self.world_map.countries[country].state = CountryState.open
            self.menu.add_country_option(guess)
        self.menu.score += marking.sum() - (~marking).sum()
        self.menu.progress = len(self.countries_correct)

        self.countries_guessed = pd.Series(dtype="object")

        if len(self.countries_correct) == len(self.valid_countries):
            print(f"Finished with score {self.menu.score}!")

    def apply_highlight_country(self, name):
        country = self.world_map.countries[name]
        old_country = self.world_map.highlighted
        if old_country:
            self.remove_highlight_country(old_country.name)
        if country.state == CountryState.open:
            country.state = CountryState.highlighted
        display_text = self.countries_guessed.get(name) or (name if name in self.countries_correct else "")
        self.menu.display_country(display_text)

    def remove_highlight_country(self, name):
        country = self.world_map.countries[name]
        if country.state == CountryState.highlighted:
            country.state = CountryState.open

    def deselect_country(self, name):
        country = self.world_map.countries[name]
        if country.state == CountryState.selected:
            country.state = CountryState.open
        self.world_map.selected = None
        self.menu.instruction_text = "Make selection"

    def weak_select_country(self, name):
        country = self.world_map.countries[name]
        old_country = self.world_map.selected
        if old_country:
            self.deselect_country(old_country.name)
        if country.state in (CountryState.open, CountryState.highlighted):
            country.state = CountryState.selected
            self.world_map.selected = country
            self.menu.instruction_text = "Guess country"

    def strong_select_country(self, name):
        country = self.world_map.countries[name]
        if country.state in (CountryState.open, CountryState.highlighted, CountryState.guessed):
            del self.countries_guessed[name]
            self.menu.add_country_option(name)
            self.menu.progress = len(self.countries_correct) + len(self.countries_guessed)
            # We re-use the weak-select method. First put the country in a state where it can be weak-selected.
            country.state = CountryState.highlighted
            self.weak_select_country(name)


if __name__ == "__main__":
    root = ttk.Tk()
    root.geometry("1000x600")
    gowhere = GoWhere(root, regions, country_schema, style_schema)
    root.mainloop()
