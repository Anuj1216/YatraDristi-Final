import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from src.config.settings import RAW_DATA_FILE, RAW_SHEET_NAME

MASTER_FILE = PROJECT_ROOT / "data" / "exports" / "place_master_coordinates.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "raw" / "accidents_updated.xlsx"


def main():
    df = pd.read_excel(RAW_DATA_FILE, sheet_name=RAW_SHEET_NAME)
    master_df = pd.read_csv(MASTER_FILE)

    master_df = master_df.dropna(subset=["latitude", "longitude"])

    coord_map = {
        row["place_name"]: (row["latitude"], row["longitude"])
        for _, row in master_df.iterrows()
    }

    new_lat = []
    new_lon = []

    for _, row in df.iterrows():
        place = str(row["place_name"]).strip().title()

        if place in coord_map:
            lat, lon = coord_map[place]
        else:
            lat = row["latitude"]
            lon = row["longitude"]

        new_lat.append(lat)
        new_lon.append(lon)

    df["latitude"] = new_lat
    df["longitude"] = new_lon

    df.to_excel(OUTPUT_FILE, index=False)

    print("✅ Dataset updated with corrected coordinates")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()