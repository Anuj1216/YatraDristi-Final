import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from src.data.features import run_feature_engineering_pipeline


if __name__ == "__main__":
    result = run_feature_engineering_pipeline()

    print("=== Feature Engineering Completed ===")
    print("Processed shape:", result["processed_shape"])
    print("Featured shape:", result["featured_shape"])
    print("Saved file:", result["featured_file"])
    print("\nPreview:")
    print(result["preview"])