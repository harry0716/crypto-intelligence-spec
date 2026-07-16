from __future__ import annotations

import html
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


ARTIFACTS_DIR = Path("artifacts")
PUBLIC_DIR = Path("public")
WORKFLOW_URL = "https://github.com/harry0716/crypto-intelligence-spec/actions/workflows/daily-report.yml"


def main() -> int:
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    (PUBLIC_DIR / ".nojekyll").write_text("", encoding="utf-8")

    reports = _collect_reports()
    for report in reports:
        report_dir = PUBLIC_DIR / "reports" / report["date"]
        report_dir.mkdir(parents=True, exist_ok=True)
        for key in ("html_path", "pdf_path", "json_path"):
            source = Path(report[key])
            if source.is_file():
                shutil.copy2(source, report_dir / source.name)

    (PUBLIC_DIR / "index.html").write_text(_render_index(reports), encoding="utf-8")
    return 0


def _collect_reports() -> list[dict]:
    reports = []
    for json_path in sorted(ARTIFACTS_DIR.glob("Crypto_Market_Intelligence_*.json"), reverse=True):
        date_part = json_path.stem.removeprefix("Crypto_Market_Intelligence_")
        html_path = json_path.with_suffix(".html")
        pdf_path = json_path.with_suffix(".pdf")
        if not html_path.is_file():
            continue
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        reports.append(
            {
                "date": date_part,
                "title": payload.get("title", f"Crypto Market Intelligence {date_part}"),
                "generated_at": payload.get("generated_at", ""),
                "html_path": str(html_path),
                "pdf_path": str(pdf_path),
                "json_path": str(json_path),
                "html_name": html_path.name,
                "pdf_name": pdf_path.name,
                "json_name": json_path.name,
                "has_pdf": pdf_path.is_file(),
                "source_count": len(payload.get("source_updates", [])),
                "event_count": len(payload.get("top_events", [])),
            }
        )
    return reports


def _render_index(reports: list[dict]) -> str:
    generated = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    latest = reports[0] if reports else None
    cards = "\n".join(_report_card(report) for report in reports)
    latest_panel = _latest_panel(latest)
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Crypto Intelligence | GitHub Portal</title>
  <style>
    :root {{
      --ink: #18242d;
      --muted: #65737c;
      --paper: #f5f6f2;
      --panel: #ffffff;
      --line: #d8e0dc;
      --green: #157764;
      --green-soft: #e6f3ef;
      --amber: #9f6a00;
      --amber-soft: #fff3cf;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: var(--paper); color: var(--ink); font-family: "Noto Sans TC", "Microsoft JhengHei", Arial, sans-serif; letter-spacing: 0; }}
    header {{ background: var(--panel); border-bottom: 1px solid var(--line); }}
    .bar {{ max-width: 1120px; margin: 0 auto; padding: 18px 20px; display: flex; align-items: center; justify-content: space-between; gap: 16px; }}
    .brand {{ font-size: 18px; font-weight: 800; }}
    .badge {{ display: inline-flex; align-items: center; border-radius: 5px; background: var(--green-soft); color: #0b6354; padding: 6px 10px; font-size: 13px; font-weight: 700; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 28px 20px 44px; }}
    .grid {{ display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(300px, .9fr); gap: 18px; align-items: start; }}
    .panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 22px; }}
    h1 {{ font-size: 26px; line-height: 1.25; margin: 0 0 10px; }}
    h2 {{ font-size: 18px; margin: 0 0 14px; }}
    h3 {{ font-size: 16px; margin: 0 0 8px; }}
    p {{ line-height: 1.65; margin: 0 0 12px; }}
    .muted {{ color: var(--muted); font-size: 14px; }}
    .actions {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }}
    a.button {{ display: inline-flex; align-items: center; justify-content: center; min-height: 38px; padding: 9px 12px; border-radius: 5px; text-decoration: none; font-weight: 800; background: var(--green); color: white; }}
    a.button.secondary {{ background: #eef3f0; color: #1e4f45; }}
    a.button.warn {{ background: var(--amber-soft); color: var(--amber); }}
    .reports {{ margin-top: 20px; display: grid; gap: 12px; }}
    .report {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 12px; align-items: center; }}
    .report-title {{ font-weight: 800; margin-bottom: 4px; }}
    .chips {{ display: flex; flex-wrap: wrap; gap: 7px; margin-top: 8px; }}
    .chip {{ background: #f1f5f3; color: #40525b; border-radius: 4px; padding: 4px 7px; font-size: 12px; }}
    .links {{ display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }}
    .links a {{ color: var(--green); font-weight: 800; text-decoration: none; }}
    .note {{ border-left: 4px solid var(--amber); padding: 10px 12px; background: var(--amber-soft); color: #6f4b00; font-size: 14px; }}
    @media (max-width: 820px) {{
      .bar {{ align-items: flex-start; flex-direction: column; }}
      .grid {{ grid-template-columns: 1fr; }}
      .report {{ grid-template-columns: 1fr; }}
      .links {{ justify-content: flex-start; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="bar">
      <div class="brand">Crypto Intelligence | GitHub Portal</div>
      <div class="badge">GitHub Pages 遠端入口</div>
    </div>
  </header>
  <main>
    <section class="grid">
      {latest_panel}
      <aside class="panel">
        <h2>遠端模式邊界</h2>
        <p class="muted">這個頁面部署在 GitHub Pages，可隨時查看最新每日報告。它是靜態入口，不會直接在瀏覽器內執行本機版的即時研判後端。</p>
        <p class="note">需要即時研判時，請使用本機工作台，或到 GitHub Actions 手動執行 daily-report workflow 產生新報告。</p>
        <div class="actions">
          <a class="button warn" href="{WORKFLOW_URL}" target="_blank" rel="noopener noreferrer">開啟 GitHub Actions</a>
        </div>
      </aside>
    </section>
    <section class="reports">
      <h2>報告列表</h2>
      {cards or '<div class="panel muted">目前尚未找到可部署的報告。</div>'}
    </section>
    <p class="muted" style="margin-top:20px">Portal generated at {html.escape(generated)}.</p>
  </main>
</body>
</html>
"""


def _latest_panel(report: dict | None) -> str:
    if report is None:
        return """<section class="panel"><h1>尚未有可用報告</h1><p class="muted">每日 workflow 產生第一份 artifacts 後，這裡會顯示最新報告。</p></section>"""
    report_dir = f"reports/{html.escape(report['date'])}"
    pdf_link = f'<a class="button secondary" href="{report_dir}/{html.escape(report["pdf_name"])}">下載 PDF</a>' if report["has_pdf"] else ""
    return f"""<section class="panel">
        <h1>最新每日情報報告</h1>
        <p class="muted">{html.escape(report['date'])} | {html.escape(report['generated_at'])}</p>
        <p>此入口保留 HTML、PDF 與 JSON 三種版本，方便你在手機、平板或其他電腦上直接查閱。</p>
        <div class="chips">
          <span class="chip">重點事件 {report['event_count']}</span>
          <span class="chip">來源雷達 {report['source_count']}</span>
        </div>
        <div class="actions">
          <a class="button" href="{report_dir}/{html.escape(report['html_name'])}">開啟 HTML 報告</a>
          {pdf_link}
          <a class="button secondary" href="{report_dir}/{html.escape(report['json_name'])}">查看 JSON</a>
        </div>
      </section>"""


def _report_card(report: dict) -> str:
    report_dir = f"reports/{html.escape(report['date'])}"
    pdf_link = f'<a href="{report_dir}/{html.escape(report["pdf_name"])}">PDF</a>' if report["has_pdf"] else ""
    return f"""<article class="report">
      <div>
        <div class="report-title">{html.escape(report['title'])}</div>
        <div class="muted">{html.escape(report['date'])} | {html.escape(report['generated_at'])}</div>
        <div class="chips"><span class="chip">事件 {report['event_count']}</span><span class="chip">來源 {report['source_count']}</span></div>
      </div>
      <div class="links">
        <a href="{report_dir}/{html.escape(report['html_name'])}">HTML</a>
        {pdf_link}
        <a href="{report_dir}/{html.escape(report['json_name'])}">JSON</a>
      </div>
    </article>"""


if __name__ == "__main__":
    raise SystemExit(main())
