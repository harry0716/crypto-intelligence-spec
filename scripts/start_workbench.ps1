$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
$LogsDir = Join-Path $RepoRoot "logs"
$OutLog = Join-Path $LogsDir "workbench.out.log"
$ErrLog = Join-Path $LogsDir "workbench.err.log"
$Runner = Join-Path $ScriptDir "run_workbench.cmd"

New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null

$portInUse = Test-NetConnection -ComputerName 127.0.0.1 -Port 8765 -InformationLevel Quiet -WarningAction SilentlyContinue
if ($portInUse) {
    Add-Content -Path $OutLog -Value "$(Get-Date -Format o) workbench already running on 127.0.0.1:8765"
    exit 0
}

Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c `"$Runner`" >> `"$OutLog`" 2>> `"$ErrLog`"" `
    -WorkingDirectory $RepoRoot `
    -WindowStyle Hidden

Add-Content -Path $OutLog -Value "$(Get-Date -Format o) workbench start requested"
