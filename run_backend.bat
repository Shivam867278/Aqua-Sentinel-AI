@echo off
cd /d "%~dp0"
where python >nul 2>nul
if %errorlevel%==0 (
    python -m pip install -r requirements.txt
    python backend.py
) else (
    py -3 -m pip install -r requirements.txt
    py -3 backend.py
)
pause
