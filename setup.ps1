param([switch]$SkipModel)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    & py -3.12 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Install 64-bit Python 3.12 with the Python launcher first.' }
}
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $python -c 'import struct,sys; sys.exit(0 if struct.calcsize("P")==8 else 1)'
if ($LASTEXITCODE -ne 0) { throw 'A 64-bit Python installation is required.' }
& $python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'Could not upgrade pip.' }
& $python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
if (-not $SkipModel) {
    & $python scripts\download_model.py
    if ($LASTEXITCODE -ne 0) { throw 'Model download failed. See README.md for manual installation.' }
}
Write-Host 'Setup complete. Open the VBS launcher, or run .venv\Scripts\python.exe app\server.py.'
