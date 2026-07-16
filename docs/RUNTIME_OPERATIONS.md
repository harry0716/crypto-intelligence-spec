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

The same workflow also builds a GitHub Pages portal from the generated report:

```text
public/
public/index.html
public/reports/YYYY-MM-DD/
```

GitHub Pages is a static remote entry point. It can display generated reports,
PDFs, and JSON payloads, but it cannot run the local Python rapid-assessment
backend directly.

The workflow publishes the same `public/` directory in two ways:

```text
GitHub Actions Pages deployment
gh-pages branch
```

If the public URL returns GitHub's default 404 page, open repository Settings >
Pages and set the source to either `GitHub Actions` or `Deploy from a branch:
gh-pages / root`.

For private repositories, GitHub Pages availability depends on the GitHub plan.
If the API or Settings page says the current plan does not support Pages, the
workflow still publishes the static portal to the `gh-pages` branch and uploads
the report artifact, but the public `github.io` URL will remain unavailable
until the repository is public or the account plan supports private Pages.

Published report history is intentionally kept on the `gh-pages` branch under:

```text
reports/YYYY-MM-DD/
```

Before each deployment, the workflow restores the current `gh-pages` contents,
adds the newly generated report, and rebuilds `index.html`. This keeps the main
branch clean while preserving online report history.

The `Security` workflow also adapts to repository visibility. Private
repositories on plans without code scanning support run local security smoke
checks only. CodeQL is enabled automatically when the repository is public,
because SARIF upload requires GitHub code scanning support.

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
