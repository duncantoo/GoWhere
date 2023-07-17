import pathlib

import geopandas as gpd
import numpy as np
import pygame
import shapely

path = pathlib.Path(__file__).parent / "Natural_Earth_quick_start" / "50m_cultural" / "ne_50m_admin_0_countries.shp"

regions = gpd.read_file(path)

clock = pygame.time.Clock()
pygame.init()
pygame.font.init()
my_font = pygame.font.SysFont("Calibri", 20)

screen_w = 800
screen_h = 600
game_display = pygame.display.set_mode((screen_w, screen_h))


def world_to_screen(v):
    return (v + np.array((180, -90))) * np.array((screen_w / 360, -screen_h / 180))


def draw_region(game_display, geometry):
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
            pygame.draw.polygon(game_display, (255, 255, 255), world_to_screen(np.array(line.coords)))


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        print(event)
        for _, region in regions.iterrows():
            geometry = region["geometry"]
            draw_region(game_display, geometry)
            text_surface = my_font.render(region["SOVEREIGNT"], False, (0, 0, 255))
            game_display.blit(text_surface, world_to_screen(np.array(geometry.centroid.coords[0])))

    pygame.display.update()
    clock.tick(60)

