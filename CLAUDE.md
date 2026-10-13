# CLAUDE.md — Rebar Take-off

Windows desktop tool that produces rebar quantity take-offs from AutoCAD drawings (Python,
PyQt6, AutoCAD COM, AutoLISP). Details: [README.md](README.md).

**At the start of a session read [docs/HISTORY.md](docs/HISTORY.md)**: which version was
chosen and why, what was fixed, open items. Add a dated entry there (newest first) after
each session.

## Rules
- Code, README and commit messages in English.
- Unit weights come from one place: bar weights from `RebarCalculator.weight_table`, meshes
  from `mesh_data.py`. Never guess a value that is not in a table; warn and reject.
- Every change that affects take-off results needs a test with hand-checked values.
- Do not instantiate code that connects to AutoCAD (`rebar_gui.RebarCalculatorGUI()`,
  `AutoCADIntegration()`) in tests: it starts AutoCAD in the background.

## Commands
```bash
install.bat                                   # .venv + requirements + tests
run.bat                                       # GUI (with AutoCAD open)
.venv\Scripts\python -m unittest discover -s tests -v
```
