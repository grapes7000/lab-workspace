import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DATA=Path(os.environ.get("LAB_WORKSPACE_DATA_DIR",ROOT/"data")).expanduser()
DB=DATA/"lab_workspace_combined.db"
EXPORTS=ROOT/"exports"
def ensure():
 DATA.mkdir(parents=True,exist_ok=True); EXPORTS.mkdir(parents=True,exist_ok=True)

# Names used by the restored writing workspace.
DATABASE_PATH=DB
EXPORT_DIR=EXPORTS
ensure_directories=ensure
