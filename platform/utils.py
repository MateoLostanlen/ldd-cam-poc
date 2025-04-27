from geopy.distance import geodesic
from geopy import Point
import dash_leaflet as dl


def build_vision_polygon(site_lat, site_lon, azimuth, opening_angle, dist_km):

    center = [site_lat, site_lon]

    points1 = []
    points2 = []

    for i in reversed(range(1, opening_angle + 1)):
        azimuth1 = (azimuth - i / 2) % 360
        azimuth2 = (azimuth + i / 2) % 360

        point = geodesic(kilometers=dist_km).destination(
            Point(site_lat, site_lon), azimuth1
        )
        points1.append([point.latitude, point.longitude])

        point = geodesic(kilometers=dist_km).destination(
            Point(site_lat, site_lon), azimuth2
        )
        points2.append([point.latitude, point.longitude])

    points = [center, *points1, *list(reversed(points2))]

    polygon = dl.Polygon(
        id="vision_polygon",
        color="#ff7800",
        opacity=0.5,
        fillOpacity=0.2,
        positions=points,
    )

    return polygon, azimuth
