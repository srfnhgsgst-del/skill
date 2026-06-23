@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================
echo   StockFund Analyzer - System Check
echo ============================================
echo.

cd /d %~dp0

:: Check 1: Python location
echo [1/4] Checking Python...
where python 2>nul
if %errorlevel% neq 0 (
    echo [FAIL] python command not found.
    where py 2>nul
    if %errorlevel% equ 0 (
        echo [INFO] py command found. Using py instead.
        set PY=py
    ) else (
        echo [HELP] Install Python 3.8+ from https://www.python.org/downloads/
        echo.    Make sure to check "Add Python to PATH"
        goto :end
    )
) else (
    set PY=python
)
python --version 2>nul
echo.

:: Check 2: PIP
echo [2/4] Checking pip...
python -m pip --version 2>nul
if %errorlevel% neq 0 (
    echo [FAIL] pip not available
    echo [HELP] Run: python -m ensurepip
    goto :end
)
echo.

:: Check 3: Dependencies
echo [3/4] Checking dependencies...
cd backend
python -c "import fastapi; import uvicorn; import yfinance; import pandas; print('All imports OK')" 2>nul
if %errorlevel% neq 0 (
    echo [WARN] Dependencies missing. Installing...
    pip install -r requirements.txt
) else (
    echo [OK] All dependencies installed.
)
echo.

:: Check 4: Port 8000
echo [4/4] Checking port 8000...
netstat -an | find ":8000 " >nul
if %errorlevel% equ 0 (
    echo [WARN] Port 8000 is already in use. Close other programs first.
) else (
    echo [OK] Port 8000 is available.
)
echo.

echo ============================================
echo   Ready to start!
echo ============================================
echo.
echo Run this command manually:
echo   cd backend ^&^& python main.py
echo.
echo Or open frontend/index.html in browser
echo.
:end
pause