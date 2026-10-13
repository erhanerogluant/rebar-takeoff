@echo off
rem Rebar Take-off kurulumu: sanal ortam + gerekli paketler
cd /d "%~dp0"
where python >nul 2>nul || (echo Python bulunamadi. https://www.python.org/downloads/ adresinden Python 3.11+ kurun ^(Add to PATH secili^). & pause & exit /b 1)
if not exist .venv python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt || (echo Paket kurulumu basarisiz. & pause & exit /b 1)
.venv\Scripts\python -m unittest discover -s tests
echo.
echo Kurulum tamam. Calistirmak icin run.bat
pause
