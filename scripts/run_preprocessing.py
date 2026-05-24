import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from src.data.preprocess import run_preprocessing_pipeline


if __name__ == "__main__":
    result = run_preprocessing_pipeline()

    print("=== Preprocessing Completed ===")
    print("Raw shape:", result["raw_shape"])
    print("Processed shape:", result["processed_shape"])
    print("Saved file:", result["processed_file"])
    print("\nPreview:")
    print(result["preview"])