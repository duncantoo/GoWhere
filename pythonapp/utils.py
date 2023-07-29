import geopandas as gpd
import numpy as np
from slugify import slugify


def wgs84_to_mercator(v):
    v = np.asarray(v)
    x = v[..., 0]
    y = np.rad2deg(np.log(np.tan((v[..., 1] / 90 + 1) * np.pi / 4)))
    return np.stack([x, y], axis=-1)


def world_to_screen(canvas, v):
    return 2 * (v + np.array((180, -90))) * np.array((1.35, -1.35))


def screen_to_world(canvas, v):
    return v * np.array((360 / canvas.width, -180 / canvas.height)) - np.array((180, -90))


def encode_tag(country_name):
    """Return string slugified for tagging."""
    return slugify(country_name, separator="_")


def read_regions(path):
    regions = gpd.read_file(path)
    # Special cases. Split sovereignty.
    regions.loc[regions["NAME"] == "Palestine", "SOVEREIGNT"] = "Palestine"

    return regions
