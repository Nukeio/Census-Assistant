# Census Assistant PowerShell Launcher
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Starting Census Assistant Application Server" -ForegroundColor Green
Write-Host "Lakhipur Circle - By Shahin Sha A. - S. A. Ahmed" -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Cyan

if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..."
    python -m venv venv
}

& ".\venv\Scripts\python.exe" -m pip install -r requirements.txt
& ".\venv\Scripts\python.exe" -m backend.main
