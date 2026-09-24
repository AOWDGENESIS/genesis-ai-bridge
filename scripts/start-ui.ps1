[CmdletBinding()]
param([int]$Port = 8787)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Launcher = Join-Path $PSScriptRoot 'genesis-bridge.py'
$python = Get-Command py -ErrorAction SilentlyContinue
if ($null -ne $python) { & $python.Source -3 $Launcher web --host 127.0.0.1 --port $Port }
else { & (Get-Command python -ErrorAction Stop).Source $Launcher web --host 127.0.0.1 --port $Port }
if ($LASTEXITCODE -ne 0) { throw "Weboberfläche fehlgeschlagen (ExitCode $LASTEXITCODE)." }
