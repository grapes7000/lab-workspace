# Lab Workspace v1.2

Cross-platform PySide6 laboratory workspace for Windows and Linux.

## Features

- Named workspaces with isolated Scratchpad and Final Document content/history
- VS Code-style activity rail and collapsible Workspace Explorer
- Rearrangeable dock windows for Writing, Science Calculator, Materials & Samples, and Stoichiometry
- Any registered tool can be promoted into the center work area instead of forcing Writing to stay main
- Optional two-pane center work area with side-by-side or top/bottom layouts
- Scratchpad and final Markdown editor with Edit, Preview, and Side-by-Side modes
- Offline rich Markdown preview with local images, KaTeX math, code highlighting, and Mermaid diagrams
- Append-only document revisions
- Material library with formula, molar mass, density, purity, active fraction, form, and notes
- Sample registry for gasoline, fuels, blends, additives, references, and other samples
- Test-method definitions, test requests, and structured result entry
- Stoichiometry reactant/product tables with formula parsing, molar mass, mass, volume, density, moles, balance checking, limiting reagent, excess, theoretical yield, and actual yield
- Searchable materials, samples, and test requests
- CSV import/export and XLSX workbook export/import
- Immutable calculation history and Markdown reports

## Workspace shell

The far-left activity rail opens the Workspace Explorer and application tools. The Workspace Explorer contains named workspaces and their Scratchpad/Final Document entries. Double-click a workspace or document to activate it.

The center work area is no longer permanently assigned to the text editor. Use either center pane's selector, or **View → Make Main**, to place Writing, the calculator, Materials & Samples, or Stoichiometry in the center. The center can optionally be split into two panes and switched between side-by-side and top/bottom orientations.

Tools that are not in the center remain normal Qt dock windows. They can be closed, reopened from the activity rail, dragged to either side, stacked/tabbed with other docks, or floated. Choosing **Dock** in a center pane returns that tool to a dockable window.

Existing v1.x Scratchpad/Final Document text, revision history, and deleted-fragment recovery records are copied into the first named workspace the first time the new workspace schema is opened.

## Run

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m lab_workspace
```

Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m lab_workspace
```

## Important

Use fictional data for initial testing. This is not a validated LIMS. Independently verify calculations and imported results before operational use. SQLite is the source of truth; CSV and XLSX are interchange formats.
