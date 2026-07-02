import sys
from pathlib import Path
import time
import requests
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

INPUT_FILE = PROJECT_ROOT / "data" / "exports" / "unique_places.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "exports" / "place_master_coordinates.csv"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def geocode_place(place_name):
    params = {
        "q": f"{place_name}, Nepal",
        "format": "json",
        "limit": 1,
        "countrycodes": "np",
    }

    headers = {
        "User-Agent": "YatraDristiProject/1.0"
    }

    try:
        response = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if len(data) == 0:
            return None

        result = data[0]

        return {
            "latitude": float(result["lat"]),
            "longitude": float(result["lon"]),
            "display_name": result.get("display_name", ""),
        }

    except Exception as e:
        print(f"❌ Error for {place_name}: {e}")
        return None


def main():
    df = pd.read_csv(INPUT_FILE)

    results = []

    for idx, row in df.iterrows():
        place = row["place_name"]
        print(f"Geocoding {idx + 1}/{len(df)}: {place}")

        geo = geocode_place(place)

        if geo:
            results.append({
                "place_name": place,
                "resolved_place_name": place,
                "latitude": geo["latitude"],
                "longitude": geo["longitude"],
                "display_name": geo["display_name"],
                "status": "OK",
            })
        else:
            results.append({
                "place_name": place,
                "resolved_place_name": place,
                "latitude": "",
                "longitude": "",
                "display_name": "",
                "status": "NOT_FOUND",
            })

        time.sleep(1)  

    result_df = pd.DataFrame(results)
    result_df.to_csv(OUTPUT_FILE, index=False)

    print("\n✅ Geocoding completed")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()