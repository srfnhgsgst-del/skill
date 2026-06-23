@echo off
echo StockFund Analyzer - Starting...
echo.
"C:\Users\khw\AppData\Local\Programs\Python\Python313\python.exe" -m pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [FAIL] pip install failed. Try manually:
    echo "C:\Users\khw\AppData\Local\Programs\Python\Python313\python.exe" -m pip install -r requirements.txt
    pause
    exit /b 1
)
echo [OK] Dependencies ready
echo.
echo Server: http://localhost:9200
echo Frontend: (open separately) frontend/index.html
echo.
"C:\Users\khw\AppData\Local\Programs\Python\Python313\python.exe" main.py
pause