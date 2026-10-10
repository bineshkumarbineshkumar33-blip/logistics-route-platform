# One-time setup for Windows PowerShell. Run from the project root:  .\scripts\setup.ps1
$ErrorActionPreference = "Stop"
Write-Host "== Backend =="
Set-Location backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
Set-Location ..\frontend
Write-Host "== Frontend =="
npm install
Set-Location ..
Write-Host "Setup finished. Next: open two terminals (see README step 3)."
