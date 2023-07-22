import pathlib
import tkinter as tk

import geopandas as gpd
import numpy as np
import shapely

path = pathlib.Path(__file__).parent / "Natural_Earth_quick_start" / "50m_cultural" / "ne_50m_admin_0_countries.shp"

regions = gpd.read_file(path)

screen_w = 800
screen_h = 600


def world_to_screen(v):
    return (v + np.array((180, -90))) * np.array((screen_w / 360, -screen_h / 180))


def screen_to_world(v):
    return v * np.array((360 / screen_w, -180 / screen_h)) - np.array((180, -90))

class WorldMap():
    def __init__(self, canvas, regions):
        self.canvas = canvas
        self.regions = regions
        self.selected = None
        self.highlighted = None
        polygons = self.create_polygons(canvas, regions)
        self.regions["polygons"] = polygons
        self.regions["guess"] = ""

        return


    def draw(self):
        for geometry in regions["geometry"]:
            self.draw_region(self.canvas, geometry)

    def create_polygons(self, canvas, regions):
        polygons = []
        for _, region in regions.iterrows():
            polygon = self.create_polygon(canvas, region["geometry"], region["SOVEREIGNT"])
            polygons.append(polygon)
        return polygons

    def create_polygon(self, canvas, geometry, name, outline="black", fill="grey", width=1):
        if isinstance(geometry, shapely.MultiPolygon):
            polys = geometry.geoms
        else:
            polys = [geometry]
        polygons = []
        for poly in polys:
            polygons = []
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
                    tags=name,
                )
                canvas.tag_bind(id, "<Enter>", lambda e: self.do_highlight(name, e))
                canvas.tag_bind(id, "<Leave>", lambda e: self.remove_highlight(name, e))
                canvas.tag_bind(id, "<ButtonRelease-1>", lambda e: self.do_select(name, e))
                polygons.append(id)
        return polygons

    def do_highlight(self, tag, event):
        if (tag != self.selected) & (not self.regions.set_index("NAME").loc[tag, "guess"]):
            event.widget.itemconfigure(tag, fill="white")
    def remove_highlight(self, tag, event):
        if tag != self.selected:
            event.widget.itemconfigure(tag, fill="grey")
    def do_select(self, tag, event):
        if not self.regions.set_index("NAME").loc[tag, "guess"]:
            event.widget.itemconfigure(self.selected, fill="grey")
            self.selected = tag
            event.widget.itemconfigure(tag, fill="green")



root = tk.Tk()
canvas = tk.Canvas(root, width=screen_w, height=screen_h)
canvas.pack(fill="both", expand=True)

from tkinter import ttk
user_entry_text = tk.StringVar()
user_entry = ttk.Combobox(root, values=sorted(regions["SOVEREIGNT"].to_list()), textvariable=user_entry_text)

world_map = WorldMap(canvas, regions)
user_entry.pack()

def set_country(world_map, event):
    if world_map.selected:
        world_map.regions.set_index("NAME").loc[world_map.selected, "guess"] = user_entry_text.get()
        print(world_map.selected, user_entry_text.get())
    else:
        print(user_entry_text.get())


user_entry.bind("<<ComboboxSelected>>", lambda e: set_country(world_map, e))
user_entry.bind("<Return>", lambda e: set_country(world_map, e))

root.mainloop()

quit(0)

