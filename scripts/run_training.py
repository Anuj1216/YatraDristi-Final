import sys
from pathlib import Path
PROJECT_ROOT = Path.cwd()
sys.path.append(str(PROJECT_ROOT))

from src.training.train import run_training_pipeline

result = run_training_pipeline()
print(result)