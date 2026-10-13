# Rebar Take-off (Demir Metrajı)

Desktop tool that reads reinforcement (rebar) annotations and dimensions from structural
AutoCAD drawings and produces rebar quantity take-off reports (length, count, weight per
diameter and per room / element). Built and used in 2025 on post-earthquake housing projects
(Hatay, Adıyaman) to replace manual counting.

## How it works

1. `rebar_gui.py` (PyQt6) connects to a running AutoCAD instance over COM (`pywin32`).
2. The user picks rebar texts (e.g. `2x%%C12/15 L=185`, `Etr.%%C10/8`) and dimensions in the
   drawing; `autocad_integration.py` reads them.
3. `rebar_calculator.py` parses the notation, computes lengths and weights per diameter,
   and handles stirrups and mesh reinforcement (`mesh_calculator.py`, `mesh_data.py`).
4. `report_manager.py` writes reports to `metraj_raporlari_<date>/`.
5. `report_watcher.py` + `report_analyzer/` collect the generated reports, total them and
   export to Excel.

`autocad/` holds the AutoLISP side: `EXPORTREBAR` / `ExportRebarData` / `ExportToCSV` export
rebar data from a drawing, `METRAJ` is a dialog-based take-off command.

## Requirements

- Windows, AutoCAD (COM automation), Python 3.11+

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python rebar_gui.py          # main app (starts/attaches AutoCAD)
.venv\Scripts\python report_watcher.py     # report collection and Excel export
```

Mesh unit weights (kg/m²), wire diameters and spacings come from one table: `mesh_data.py`.

## Tests

```bash
python -m unittest discover -s tests -v
```

The tests cover the calculation core (rebar, stirrup, spaced rebar, wall/slab mesh,
connection rebar, report export) with hand-checked values. AutoCAD selection itself is not
covered; it needs a running AutoCAD.

## Status

- Based on the last working version (March 2025); earlier versions are in the git log.
- October 2026 fixes in the calculation core: mesh weights now come from `mesh_data.py`
  (the old table used the cross-section number, e.g. 2.57 instead of 4.03 kg/m² for Q257);
  rebar texts like `2X13∅20 L=397` and `2x%%C12/15 L=185` are computed; stirrup length and
  spacing can come from two texts; result records accept both old and new field names.
- Logs and generated reports are not committed (`.gitignore`).
