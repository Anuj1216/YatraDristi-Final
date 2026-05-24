import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from src.config.settings import RAW_DATA_FILE, RAW_SHEET_NAME

OUTPUT_FILE = PROJECT_ROOT / "data" / "exports" / "unique_places.csv"


def main():
    df = pd.read_excel(RAW_DATA_FILE, sheet_name=RAW_SHEET_NAME)

    if "place_name" not in df.columns:
        raise ValueError("Column 'place_name' not found in dataset.")

    places = (
        df["place_name"]
        .astype(str)
        .str.strip()
        .str.title()
        .unique()
    )

    places_df = pd.DataFrame({"place_name": sorted(places)})
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    places_df.to_csv(OUTPUT_FILE, index=False)

    print(f"✅ Extracted {len(places_df)} unique places")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()