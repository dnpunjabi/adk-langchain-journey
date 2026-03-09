# PowerShell Setup Script for LangChain (Windows)

Write-Host "=============================================="
Write-Host " Setting up Virtual Environment (LangChain)..."
Write-Host "=============================================="

# Check if UV is installed
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "UV is not installed. Installing UV via astral..." -ForegroundColor Yellow
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}
else {
    Write-Host "UV is already installed." -ForegroundColor Green
}

# Create venv
if (-not (Test-Path ".venv")) {
    Write-Host "Creating Virtual Environment (.venv)..."
    uv venv
}

# Create .env if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file with dummy values..." -ForegroundColor Yellow
    $envContent = @"
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=your-service-account-key.json
GEMINI_API_KEY=your-gemini-api-key
MODEL=gemini-2.5-flash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-api-key
LANGCHAIN_PROJECT=ADK-Learning-Journey
"@
    $envContent | Out-File -FilePath ".env" -Encoding utf8
}

Write-Host "`n========================================"
Write-Host " Installing LangChain Dependencies..."
Write-Host "========================================"
uv pip install -r lc_requirements.txt

Write-Host "`n========================================================`n" -ForegroundColor Cyan
Write-Host "            LANGCHAIN SETUP COMPLETE (WINDOWS)          `n" -ForegroundColor Cyan
Write-Host "========================================================`n" -ForegroundColor Cyan
Write-Host "To activate the environment, run:" -ForegroundColor Yellow
Write-Host ".venv\Scripts\activate`n"
Write-Host "To run the Streamlit UX:" -ForegroundColor Yellow
Write-Host "uv run --env-file .env streamlit run lc_app.py`n"
