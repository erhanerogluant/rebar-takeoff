# Rebar Take-off (Demir Metrajı)

Desktop tool that reads reinforcement (rebar) annotations and dimensions from structural
AutoCAD drawings and produces rebar quantity take-off reports (length, count and weight per
diameter, per room or element). Built in 2025 and used on post-earthquake housing projects
(Hatay, Adıyaman) to replace manual counting.

**Türkçe özet:** AutoCAD statik çizimlerinden demir yazılarını ve ölçüleri okuyup çap bazında
boy, adet ve ağırlık metrajı çıkaran masaüstü uygulaması. Kurulum aşağıda; geçmiş ve kararlar
[docs/GECMIS.md](docs/GECMIS.md) içinde.

## Install (Windows)

Requirements: Windows, AutoCAD (any version with COM automation), Python 3.11+
([python.org](https://www.python.org/downloads/), tick "Add python.exe to PATH").

```bash
git clone https://github.com/erhanerogluant/rebar-takeoff.git
cd rebar-takeoff
install.bat        # creates .venv, installs requirements, runs the tests
```

Or by hand:

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

## Run

1. Open the drawing in AutoCAD.
2. `run.bat` (or `.venv\Scripts\python rebar_gui.py`). The app attaches to the running
   AutoCAD; if none is running it starts one in the background.
3. Pick rebar texts and dimensions in the drawing; reports are written to
   `metraj_raporlari_<date>/`.
4. `run.bat reports` opens the report watcher, which totals the reports and exports to Excel.

The AutoLISP side is in `autocad/`: load with `APPLOAD`, then run `EXPORTREBAR`,
`ExportRebarData`, `ExportToCSV`, `ExportToExcel` or the dialog-based `METRAJ` command.

## How it works

| File | Role |
|---|---|
| `rebar_gui.py` | PyQt6 window, selection workflow |
| `autocad_integration.py` | AutoCAD COM connection (`pywin32`), entity selection |
| `rebar_calculator.py` | Parses rebar notation, computes counts, lengths, weights |
| `mesh_data.py` | Mesh (hasır) table: kg/m², wire diameter, spacing — the single source |
| `report_manager.py` | Writes take-off reports |
| `report_watcher.py`, `report_analyzer/` | Collects reports, totals, Excel export |

Supported texts include `2X13∅20 L=397` (counted bars), `2x%%C12/15 L=185` (spaced bars, count
from the picked dimension), `ƒ10 Etr. l=168` + `Etr.%%C10/8` (stirrup), `2xQ257` + `215x500`
(wall mesh), `Q257/257 450/215` (slab mesh).

## Tests

```bash
.venv\Scripts\python -m unittest discover -s tests -v
```

The tests cover the calculation core with hand-checked values. Picking entities in AutoCAD is
not covered; it needs a running AutoCAD.

## Status

- Based on the last working version (March 2025); earlier versions are in the git log.
- October 2026: calculation core fixed and covered by tests (see [docs/GECMIS.md](docs/GECMIS.md)).
- Logs and generated reports are not committed (`.gitignore`).
