# Project history

Decisions and changes, newest first. Read this before starting new work and add a dated
entry after each working session.

---

## 2026-10-14: Moved to GitHub, calculation core fixed, tests added

**Which version and why**
- More than ten copies existed on disk (several `exportrebar` folders on the desktop and on a
  USB backup). The chosen one is the 4 March 2025 version: the most complete (report
  watcher, analyzer, mesh reports), and its folder holds reports produced until June 2025,
  so it was used in practice.
- Cursor's local history was checked: its latest entry (16 March 2025) is an undo that
  restores the 26 February version; no newer code exists there. The 4 March version was
  developed on another machine.
- Both candidates were run with the same inputs: in the 26 February version the wall mesh
  calculation does not work; in the 4 March version it does.
- Earlier versions are committed in date order (24 Feb → 25 Feb → 26 Feb → 4 Mar 2025).

**Fixes in the calculation core (`rebar_calculator.py`)**
- Mesh unit weights were wrong: Q257 was 2.57 kg/m² (the cross-section number) instead of
  4.03 kg/m². All mesh lookups now use `mesh_data.py`. Unknown mesh codes are rejected with
  a warning instead of silently using 5.0 kg/m².
  - The current AutoCAD wall/slab mesh workflow already used `mesh_data.py`, so mesh reports
    produced with it were most likely correct; the wrong table was on older code paths.
- `RebarData` was constructed with two sets of field names (`count`/`weight_per_meter` and
  `piece_count`/`unit_weight`); stirrup, connection-bar and slab-mesh records crashed. Both
  names are accepted now.
- The connection-bar path unpacked two values from `calculate_weight`, which returns one.
- Counted bar texts (`2X13∅20 L=397`) were not computed, and in spaced bar texts
  (`2x%%C12/15 L=185`) the diameter was read as the length. Both are computed now.
- Stirrup length and spacing given in two texts (`ƒ10 Etr. l=168` + `Etr.%%C10/8`) are
  merged; a missing spacing gives a message instead of a crash.
- A bare letter C (as in "C30 concrete") was treated as a diameter mark.
- On a clean checkout the report analyzer crashed at start-up because `logs/` was missing.
- Removed the unused `mesh_calculator.py`, which held another wrong mesh table.

**Tests:** `tests/test_rebar_calculator.py`, 15 tests with hand-checked values. All pass; the
same tests give 12 failures on the code before the fixes. A fresh clone installed with
`install.bat` passes them as well.

**Known gaps / next steps**
- Entity picking inside AutoCAD is not covered by tests; try it on a real drawing.
- `autocad_integration.py` still contains older console flows that call `input()`; the GUI
  uses its own flow. Could be simplified.
- Opening the GUI starts AutoCAD in the background if it is not running. Moving the
  connection to a "Connect" button would be friendlier.
- The older mesh flow converts `TR` meshes to `R` (TR257 2.57 vs R257 2.63 kg/m²); review.
- Add screenshots to the README before making the repository public.
