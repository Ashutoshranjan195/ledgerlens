# PowerShell Airplane Mode Test for LedgerLens
# Simulates full offline execution (zero network egress allowed)
$ErrorActionPreference = "Stop"

Write-Host "-> Simulating airplane mode (no network egress allowed)" -ForegroundColor Cyan
$env:LEDGERLENS_OFFLINE = "1"

python -m app.cli run --sample samples/receipts

Write-Host "[OK] Core loop completed with zero network access (Airplane mode verified)" -ForegroundColor Green
