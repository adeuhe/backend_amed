# =============================================================================
# ECL Audit & Benchmarking Workbench — Run Script (PowerShell)
# =============================================================================

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " ECL Audit & Benchmarking Workbench — Engine PSAK 413 Syariah" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Cyan

# 1. Set working directory to script location
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# 2. Check Python installation
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python tidak ditemukan di PATH system Anda." -ForegroundColor Red
    Write-Host "Silakan install Python 3.10+ terlebih dahulu." -ForegroundColor Yellow
    Pause
    exit 1
}

# 3. Check & install required dependencies
Write-Host "[INFO] Memeriksa & menginstall dependensi dari requirements.txt..." -ForegroundColor Yellow
python -m pip install -r requirements.txt --quiet

# 4. Launch FastAPI Uvicorn Server & Open Browser
$EnvPort = "5154"
if (Test-Path ".env") {
    $PortMatch = Select-String -Path ".env" -Pattern "APP_PORT\s*=\s*(\d+)"
    if ($PortMatch) {
        $EnvPort = $PortMatch.Matches[0].Groups[1].Value
    }
}

Write-Host "[SUCCESS] Memulai server FastAPI uvicorn pada port $EnvPort..." -ForegroundColor Green
Write-Host "[URL] http://localhost:$EnvPort/ecl-audit-benchmarking-workbench" -ForegroundColor Cyan
Write-Host "Tekan Ctrl+C di terminal ini untuk menghentikan server.`n" -ForegroundColor Gray

# Open browser automatically after 2 seconds
Start-Job -ScriptBlock {
    param($Port)
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:$Port/ecl-audit-benchmarking-workbench"
} -ArgumentList $EnvPort | Out-Null

# Run main application
python main.py
