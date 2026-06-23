Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  StockFund Analyzer v3.0" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
""

$BackendDir = Join-Path (Split-Path $MyInvocation.MyCommand.Path) "backend"
Set-Location -LiteralPath $BackendDir

try { python --version 2>&1 | Write-Host -ForegroundColor Green } catch {
    Write-Host "[ERROR] Python not found" -ForegroundColor Red
    Read-Host "Press Enter"
    exit 1
}

Write-Host "[*] Installing dependencies..." -ForegroundColor Yellow
python -m pip install -r requirements.txt -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] pip install failed" -ForegroundColor Red
    Read-Host "Press Enter"
    exit 1
}
Write-Host "[OK] Dependencies installed" -ForegroundColor Green
Write-Host ""
Write-Host "[*] Starting server at http://localhost:9200" -ForegroundColor Yellow
Write-Host "[*] Open frontend/index.html in browser" -ForegroundColor Yellow
Write-Host "[*] Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""
python main.py
Read-Host "Press Enter to exit"