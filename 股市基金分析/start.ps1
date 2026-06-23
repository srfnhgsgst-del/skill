Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  StockFund Analyzer v3.0" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
""

$Py = "C:\Users\khw\AppData\Local\Programs\Python\Python313\python.exe"
$BackendDir = Join-Path (Split-Path $MyInvocation.MyCommand.Path) "backend"

if (-not (Test-Path $Py)) {
    Write-Host "[ERROR] Python not found at: $Py" -ForegroundColor Red
    Read-Host "Press Enter"
    exit 1
}

Set-Location -LiteralPath $BackendDir
Write-Host "[OK] Python 3.13.14" -ForegroundColor Green

Write-Host "[*] Installing dependencies..." -ForegroundColor Yellow
& $Py -m pip install -r requirements.txt 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] pip install failed" -ForegroundColor Red
    Read-Host "Press Enter"
    exit 1
}
Write-Host "[OK] Dependencies installed" -ForegroundColor Green

Write-Host ""
Write-Host "[*] Starting server at http://localhost:9100" -ForegroundColor Yellow
Write-Host "[*] Open frontend/index.html in browser" -ForegroundColor Yellow
Write-Host "[*] Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""
& $Py main.py
Read-Host "Press Enter to exit"