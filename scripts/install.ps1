[CmdletBinding()]
param(
    [ValidateSet('claude-host','openclaw-host','ui')]
    [string]$Mode = 'claude-host'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Root = Split-Path -Parent $PSScriptRoot
$Launcher = Join-Path $PSScriptRoot 'genesis-bridge.py'

function Invoke-Python {
    param([Parameter(Mandatory)][string[]]$Arguments)
    $python = Get-Command py -ErrorAction SilentlyContinue
    if ($null -ne $python) {
        & $python.Source -3 $Launcher @Arguments
    } else {
        $python = Get-Command python -ErrorAction Stop
        & $python.Source $Launcher @Arguments
    }
    if ($LASTEXITCODE -ne 0) { throw "Python-Aufruf fehlgeschlagen (ExitCode $LASTEXITCODE)." }
}

Write-Host 'Genesis AI Bridge – sichere Einrichtung' -ForegroundColor Cyan
Invoke-Python @('setup','--mode',$Mode)
Write-Host 'Konfiguration geschrieben. Jetzt vollständige Diagnose:' -ForegroundColor Cyan
try { Invoke-Python @('doctor') }
catch { Write-Warning $_.Exception.Message; exit 1 }
Write-Host 'Fertig. Claude Desktop/OpenClaw danach vollständig neu starten.' -ForegroundColor Green
