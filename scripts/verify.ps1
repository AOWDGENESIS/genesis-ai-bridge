[CmdletBinding()]
param([switch]$Live)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Root = Split-Path -Parent $PSScriptRoot
$Launcher = Join-Path $PSScriptRoot 'genesis-bridge.py'
$python = Get-Command py -ErrorAction SilentlyContinue
if ($null -ne $python) { $pythonArgs = @('-3',$Launcher) } else { $python = Get-Command python -ErrorAction Stop; $pythonArgs = @($Launcher) }

function Invoke-Checked {
    param([Parameter(Mandatory)][string[]]$Arguments)
    & $python.Source @pythonArgs @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Prüfung fehlgeschlagen (ExitCode $LASTEXITCODE)." }
}

Write-Host '1/3 Python-Kompilierung' -ForegroundColor Cyan
& $python.Source -m compileall -q (Join-Path $Root 'src')
if ($LASTEXITCODE -ne 0) { throw 'compileall fehlgeschlagen.' }
Write-Host '2/3 Unit-/Integrations-Tests' -ForegroundColor Cyan
& $python.Source -m unittest discover -s (Join-Path $Root 'tests') -v
if ($LASTEXITCODE -ne 0) { throw 'Tests fehlgeschlagen.' }
if ($Live) {
    Write-Host '3/3 Live-Diagnose mit Ollama/OpenClaw' -ForegroundColor Cyan
    Invoke-Checked @('verify-loop','--rounds','5')
} else {
    Write-Host '3/3 Live-Diagnose übersprungen. Mit -Live auf Zielrechner ausführen.' -ForegroundColor Yellow
}
Write-Host 'Verifikation abgeschlossen.' -ForegroundColor Green
