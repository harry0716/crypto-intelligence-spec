$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$StartScript = Resolve-Path (Join-Path $ScriptDir "start_workbench.ps1")
$TaskName = "CryptoIntelligenceWorkbench"
try {
    $Action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$StartScript`""
    $Trigger = New-ScheduledTaskTrigger -AtLogOn
    $Settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -MultipleInstances IgnoreNew

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Description "Start the local Crypto Intelligence workbench at http://127.0.0.1:8765 after Windows sign-in." `
        -Force | Out-Null

    Write-Host "Installed scheduled task: $TaskName"
} catch {
    $StartupDir = [Environment]::GetFolderPath("Startup")
    $ShortcutPath = Join-Path $StartupDir "$TaskName.lnk"
    $Shell = New-Object -ComObject WScript.Shell
    $Shortcut = $Shell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = "powershell.exe"
    $Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$StartScript`""
    $Shortcut.WorkingDirectory = Split-Path -Parent $StartScript
    $Shortcut.WindowStyle = 7
    $Shortcut.Description = "Start the local Crypto Intelligence workbench at http://127.0.0.1:8765 after Windows sign-in."
    $Shortcut.Save()
    Write-Host "Scheduled task was not available; installed Startup shortcut: $ShortcutPath"
}
