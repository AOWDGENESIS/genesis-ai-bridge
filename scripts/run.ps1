[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$File,
    [string]$Task = 'Prüfe die Datei vollständig, finde Fehler und Warnungen und schlage sichere Korrekturen vor.'
)
$ErrorActionPreference = 'Stop'
$Launcher = Join-Path $PSScriptRoot 'genesis-bridge.py'
$python = Get-Command py -ErrorAction SilentlyContinue
if ($null -ne $python) { & $python.Source -3 $Launcher run $File --task $Task }
else { & (Get-Command python -ErrorAction Stop).Source $Launcher run $File --task $Task }
if ($LASTEXITCODE -ne 0) { throw "Bridge-Lauf fehlgeschlagen (ExitCode $LASTEXITCODE)." }
