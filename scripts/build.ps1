<#
.SYNOPSIS
    SPEMA Reproducible Secure Build & Quality Gate Pipeline
.DESCRIPTION
    Executes all pre-flight security checks, linters, SAST scanners, and automated tests.
#>

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "SPEMA Secure Build Pipeline (v1.3.0 Baseline)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Step 1: Secret Scan & Git Hygiene
Write-Host "`n[1/4] Running Secret Scanner & Git Hygiene Verification..." -ForegroundColor Yellow
python scripts/security_check.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Security check failed! Build aborted." -ForegroundColor Red
    exit 1
}

# Step 2: Ruff Linter
Write-Host "`n[2/4] Running Ruff Code Quality & Static Analysis..." -ForegroundColor Yellow
ruff check src/ tests/
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Ruff linting checks failed! Build aborted." -ForegroundColor Red
    exit 1
}

# Step 3: Bandit SAST Scan
Write-Host "`n[3/4] Running Bandit Static Application Security Testing (SAST)..." -ForegroundColor Yellow
bandit -c bandit.yaml -r src/
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Bandit SAST vulnerabilities detected! Build aborted." -ForegroundColor Red
    exit 1
}

# Step 4: Pytest Automated Suite
Write-Host "`n[4/4] Executing Comprehensive Automated Test Suite..." -ForegroundColor Yellow
pytest -v tests/
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Automated test suite failures detected! Build aborted." -ForegroundColor Red
    exit 1
}

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "[SUCCESS] All Security Gates Passed! Build Baseline is Green." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
exit 0
