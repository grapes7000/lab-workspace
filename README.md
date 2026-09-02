# Lab Workspace v1.2

Cross-platform PySide6 laboratory workspace for Windows and Linux.

## Features

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
