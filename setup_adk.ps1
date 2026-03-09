# PowerShell Setup Script for Google ADK (Windows)

Write-Host "========================================"
Write-Host " Setting up Virtual Environment (ADK)..."
Write-Host "========================================"

# Check if UV is installed
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "UV is not installed. Installing UV via astral..." -ForegroundColor Yellow
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
} else {
    Write-Host "UV is already installed." -ForegroundColor Green
}

# Create venv
if (-not (Test-Path ".venv")) {
    Write-Host "Creating Virtual Environment (.venv)..."
    uv venv
}

Write-Host "`n========================================"
Write-Host " Installing Google ADK Dependencies..."
Write-Host "========================================"
uv pip install -r adk_requirements.txt

Write-Host "`n========================================================`n" -ForegroundColor Cyan
Write-Host "               ADK SETUP COMPLETE (WINDOWS)             `n" -ForegroundColor Cyan
Write-Host "========================================================`n" -ForegroundColor Cyan
Write-Host "To activate the environment, run:" -ForegroundColor Yellow
Write-Host ".venv\Scripts\activate`n"
Write-Host "To run the built-in UI:" -ForegroundColor Yellow
Write-Host "uv run adk run web`n"
