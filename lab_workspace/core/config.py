import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("LAB_WORKSPACE_DATA_DIR", PROJECT_ROOT / "data")).expanduser()
EXPORT_DIR = PROJECT_ROOT / "exports"
DATABASE_PATH = DATA_DIR / "lab_workspace.db"


def ensure_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
