@echo off
echo StockFund Analyzer - Starting...
echo.
python -m pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [FAIL] pip install failed
    pause
    exit /b 1
)
echo [OK] Dependencies ready
echo.
echo Server: http://localhost:9200
echo Frontend: frontend\index.html
echo.
python main.py
pause