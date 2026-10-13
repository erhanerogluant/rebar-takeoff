@echo off
rem Rebar Take-off: AutoCAD acikken calistirin. Raporlar icin: run.bat reports
cd /d "%~dp0"
if not exist .venv (echo Once install.bat calistirin. & pause & exit /b 1)
if /i "%~1"=="reports" (.venv\Scripts\python report_watcher.py) else (.venv\Scripts\python rebar_gui.py)
