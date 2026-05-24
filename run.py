from pathlib import Path
import subprocess
import sys


def main() -> None:
    project_root = Path(__file__).resolve().parent
    app_file = project_root / "app" / "main.py"

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_file),
    ]

    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()