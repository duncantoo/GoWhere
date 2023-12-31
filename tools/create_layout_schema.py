"""Decide which colour to make countries and which territories to hide."""

import itertools
import pathlib
import sys

import pandas as pd
from thefuzz import fuzz

root_path = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(root_path / "pythonapp"))

import utils


resource_path = root_path / "resources"
region_path = resource_path / "Natural_Earth_quick_start" / "50m_cultural" / "ne_50m_admin_0_countries.shp"
schema_path = resource_path / "country_schema.csv"

regions = utils.read_regions(region_path)

schema = pd.DataFrame(
    index=regions["SOVEREIGNT"].unique(),
    columns=["names", "region_indexes", "colour", "order", "disputed"],
).rename_axis("country")

# Hide territories which are too small.
territories_to_country = regions[["NAME", "NAME_LONG"]].groupby(regions["SOVEREIGNT"])

country_area = regions.set_index("SOVEREIGNT")["geometry"].apply(lambda g: g.area)
global_area = country_area.sum()

for country, territories in territories_to_country:
    # schema.loc[country, "names"]
    territories["AREA"] = regions.loc[territories.index, "geometry"].apply(lambda g: g.area)
    name_candidates = territories[["NAME", "NAME_LONG"]].stack()
    name_similarity = name_candidates.apply(lambda n: fuzz.ratio(n, country))
    name_matches = name_candidates[name_similarity.sort_values(ascending=False) > 95]
    # If we have a really high match name then use this as the main territory.
    # Otherwise, use the largest land mass.
    if len(name_matches) > 0:
        main_id = name_matches.index.get_level_values(0)[0]
    else:
        main_id = None

    areas = territories["AREA"].sort_values(ascending=False)
    if main_id is None:
        main_id = areas.index[0]

    country_fraction = areas / areas[main_id]
    global_fraction = areas / global_area
    # Discard if < 5% main area and < 1e-4 global
    territory_discard = (country_fraction < 0.05) & (global_fraction < 1e-4)

    schema.at[country, "region_indexes"] = list(territory_discard[~territory_discard].index)
    schema.at[country, "names"] = list({country, *territories.loc[main_id, ["NAME", "NAME_LONG"]]})
    # Natural Earth already contains colours codes where adjacent countries have different colours which are consistent
    # amongst territories of the same sovereignty.
    colour_int = regions.loc[territories.index[0], "MAPCOLOR7"]
    schema.at[country, "colour"] = f"C{colour_int}"
    schema.at[country, "order"] = areas.sum()

# Mark special cases.
schema["disputed"] = False
schema.loc[["Kashmir", "Northern Cyprus", "Western Sahara", "Somaliland"], "disputed"] = True
schema = schema.drop("Antarctica")

# Larger areas get smaller rank.
# We will draw the countries in ascending rank order, finishing with the smallest countries.
schema["order"] = schema["order"].rank(ascending=False).astype(int)
schema.to_csv(schema_path)
