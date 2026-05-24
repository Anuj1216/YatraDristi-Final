import requests


def get_route(from_lat, from_lon, to_lat, to_lon):
    url = f"https://router.project-osrm.org/route/v1/driving/{from_lon},{from_lat};{to_lon},{to_lat}?overview=full&geometries=geojson"

    response = requests.get(url)
    response.raise_for_status()

    data = response.json()

    route = data["routes"][0]

    return {
        "distance_km": route["distance"] / 1000,
        "duration_min": route["duration"] / 60,
        "route_points": [(coord[1], coord[0]) for coord in route["geometry"]["coordinates"]],
    }


def geocode_and_route(
    from_place: str,
    to_place: str,
    from_lat: float,
    from_lon: float,
    to_lat: float,
    to_lon: float,
):
    origin = {"lat": from_lat, "lon": from_lon}
    destination = {"lat": to_lat, "lon": to_lon}

    route = get_route(from_lat, from_lon, to_lat, to_lon)

    return {
        "origin": origin,
        "destination": destination,
        "route": route,
    }