# Build dist\FlipType.exe (single file, no console window)
Set-Location $PSScriptRoot
function Invoke-Step($exe, [string[]]$argList) {
    & $exe @argList
    if ($LASTEXITCODE -ne 0) { Write-Error "Failed: $exe $argList"; exit 1 }
}
if (-not (Test-Path .venv)) { Invoke-Step python @('-m', 'venv', '.venv') }
Invoke-Step .\.venv\Scripts\python.exe @('-m', 'pip', 'install', '-q', '--disable-pip-version-check', '-r', 'requirements-dev.txt')
Invoke-Step .\.venv\Scripts\python.exe @('-m', 'pytest', '-q', 'tests')
Invoke-Step .\.venv\Scripts\pyinstaller.exe @('--noconfirm', '--clean', '--noconsole', '--onefile', '--log-level', 'WARN', '--name', 'FlipType', 'FlipType.pyw')
Write-Host "Built: $PSScriptRoot\dist\FlipType.exe"
