import requests
from datetime import datetime

API_KEY = "5d12b20f7a61e5357d7c771a422e92d4"

CURRENT_URL = "https://api.openweathermap.org/data/4.0/onecall/current"
TIMELINE_URL = "https://api.openweathermap.org/data/4.0/onecall/timeline/1h"

# Biratnagar coordinates
lat = 26.4525
lon = 87.2718

print("=" * 60)
print("CURRENT WEATHER")
print("=" * 60)

current = requests.get(
    CURRENT_URL,
    params={
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,
        "units": "metric",
    },
).json()

print(current)

print()
print("=" * 60)
print("TIMELINE FORECAST")
print("=" * 60)

timeline = requests.get(
    TIMELINE_URL,
    params={
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,
        "units": "metric",
    },
).json()

for hour in timeline["data"][:12]:

    weather = hour["weather"][0]

    print(
        datetime.fromtimestamp(hour["dt"]).strftime("%Y-%m-%d %H:%M"),
        "|",
        weather["main"],
        "|",
        weather["description"],
        "| Temp:",
        hour["temp"],
        "| POP:",
        hour.get("pop", 0),
    )