# Windows Native Powershell Installer for LedgerLens
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "       Installing LedgerLens for Windows (Local-First)    " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$AppDir = "$HOME\AppData\Local\ledgerlens"
New-Item -ItemType Directory -Force -Path $AppDir | Out-Null

Write-Host "→ Setting up Python environment..." -ForegroundColor Green
python -m venv .venv
.\.venv\Scripts\pip install --upgrade pip
.\.venv\Scripts\pip install -e .

Write-Host "→ Initializing SQLite database and local schema..." -ForegroundColor Green
.\.venv\Scripts\python -m app.cli update --schema

Write-Host ""
Write-Host "✅ LedgerLens successfully installed on Windows!" -ForegroundColor Green
Write-Host "Launch with: .\.venv\Scripts\python -m app.main" -ForegroundColor Yellow
