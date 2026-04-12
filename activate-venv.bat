@echo off
REM Quick script to activate Python virtual environment and show status
REM Usage: Double-click or run from command prompt

echo.
echo ========================================
echo  SlimZero v1 - Python Venv Activation
echo ========================================
echo.

cd /d "%~dp0"

if not exist venv\ (
    echo ERROR: Virtual environment not found!
    echo Create it first: python -m venv venv
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo ========================================
echo  ✓ Virtual environment is ACTIVE
echo ========================================
echo.
echo Python: 
python --version
echo.
echo PIP:
python -m pip --version
echo.
echo Available commands:
echo  - pip list               (show installed packages)
echo  - pip install X          (install package X)
echo  - python script.py       (run a script)
echo  - pytest                 (run tests)
echo  - flake8 src/            (lint code)
echo  - deactivate             (exit venv)
echo.
cmd /k
