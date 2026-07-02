from src.config.settings import DASHBOARD_WEATHER_LOCATIONS
from src.services.weather_service import get_current_weather


def get_dashboard_weather():

    weather = {}

    for place, (lat, lon) in DASHBOARD_WEATHER_LOCATIONS.items():

        try:
            weather[place] = get_current_weather(lat, lon)

        except Exception:
            weather[place] = None

    return weather