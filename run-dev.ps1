# PowerShell script to activate the local .venv and run Uvicorn
$venvActivate = Join-Path $PSScriptRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    & $venvActivate
} else {
    Write-Error "Could not find .venv virtualenv. Please create/activate the correct venv."
    exit 1
}
Write-Output "Starting Uvicorn using .venv Python..."
python -m uvicorn app.main:app --reload
