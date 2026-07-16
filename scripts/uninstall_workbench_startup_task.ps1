$ErrorActionPreference = "Stop"

$TaskName = "CryptoIntelligenceWorkbench"
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

$StartupDir = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupDir "$TaskName.lnk"
if (Test-Path $ShortcutPath) {
    Remove-Item -LiteralPath $ShortcutPath -Force
    Write-Host "Removed Startup shortcut: $ShortcutPath"
}

Write-Host "Removed startup registration: $TaskName"
