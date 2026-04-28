@echo off
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel%==0 (
    set PYTHON_CMD=python
) else (
    set PYTHON_CMD=py -3
)

echo Installing dependencies...
%PYTHON_CMD% -m pip install -r requirements.txt
if errorlevel 1 (
    echo Dependency installation failed. Please install Python 3.10+ and try again.
    pause
    exit /b 1
)

echo Starting Flask backend...
start "Aqua Sentinel API" cmd /k "%PYTHON_CMD% backend.py"

echo Starting Streamlit dashboard...
timeout /t 2 >nul
%PYTHON_CMD% -m streamlit run app.py

pause
