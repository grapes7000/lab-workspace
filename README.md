# Lab Workspace v1

Cross-platform PySide6 desktop workspace for Windows and Linux.

## Included in v1

- Collapsible scientific calculator on the left
- Quick laboratory calculations for mass, moles, molarity, dilution, and ppm
- Upper scratchpad with debounced autosave and revision history
- Lower final-document editor with autosave, open, save, Save As, Markdown export, and revision history
- Resizable upper/lower editor split
- SQLite persistence stored locally
- Restore-safe history: restoring creates a new revision
- Diff viewer with deleted lines muted red and added lines green
- Find text in either editor
- Word and character counts
- Light and dark themes
- Window and splitter state restoration
- Cross-platform paths through `pathlib`

## Requirements

- Python 3.10 or newer
- PySide6

## Install

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m lab_workspace
```

### Linux Bash

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m lab_workspace
```

If PySide6 is already available in a Conda environment, activate that environment and run `python -m lab_workspace`.

## Data locations

By default, application data is stored in the project-local `data/` directory. Set `LAB_WORKSPACE_DATA_DIR` to use another location.

Windows PowerShell:

```powershell
$env:LAB_WORKSPACE_DATA_DIR = "$HOME\LabWorkspaceData"
python -m lab_workspace
```

Linux Bash:

```bash
export LAB_WORKSPACE_DATA_DIR="$HOME/.local/share/lab-workspace"
python -m lab_workspace
```

## Important

Use nonconfidential test data first. This is a local v1 application, not a validated laboratory information management system. Verify all scientific calculations independently before operational use.
