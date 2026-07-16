# Runtime Operations

## Report Output Locations

Daily reports are written to the directory configured by `REPORT_OUTPUT_DIR`.
The default is:

```text
artifacts/
```

For a report date of `YYYY-MM-DD`, the daily job creates:

```text
artifacts/Crypto_Market_Intelligence_YYYY-MM-DD.html
artifacts/Crypto_Market_Intelligence_YYYY-MM-DD.pdf
artifacts/Crypto_Market_Intelligence_YYYY-MM-DD.json
```

Manual workbench assessments are written under:

```text
artifacts/rapid/
```

The SQLite database is stored at:

```text
data/crypto_intelligence.db
```

GitHub Actions also uploads `artifacts/` as a workflow artifact with the retention
period defined in `.github/workflows/daily-report.yml`.

## Local Workbench

The manual intelligence workbench listens on:

```text
http://127.0.0.1:8765
```

Manual start:

```powershell
.\scripts\start_workbench.ps1
```

Direct foreground start:

```powershell
$env:PYTHONPATH = "src"
python -m crypto_intel.cli serve --host 127.0.0.1 --port 8765
```

Logs are written to:

```text
logs/workbench.out.log
logs/workbench.err.log
```

## Start Workbench After Reboot

Install the Windows scheduled task:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install_workbench_startup_task.ps1
```

The task name is:

```text
CryptoIntelligenceWorkbench
```

It runs after Windows sign-in and starts the local workbench if port `8765` is
not already in use.

If Windows denies Task Scheduler registration, the installer falls back to a
per-user Startup shortcut with the same name:

```text
CryptoIntelligenceWorkbench.lnk
```

Remove it with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\uninstall_workbench_startup_task.ps1
```

## Codex Schedule

The Codex automation is separate from GitHub Actions and the Windows startup
task. Its purpose is to check the daily report workflow and local artifacts from
inside Codex.

Expected Codex automation:

```text
Crypto Intelligence 每日報告檢查
Daily at 08:00
Project: C:\Users\harry\crypto-intelligence-spec
```

If the Codex schedule page does not show it, inspect:

```text
C:\Users\harry\.codex\automations\automation\automation.toml
```

The job should be `ACTIVE` and point at the `crypto-intelligence-spec` project.
