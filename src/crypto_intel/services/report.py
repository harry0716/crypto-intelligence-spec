from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path

from crypto_intel.config import AppConfig
from crypto_intel.domain.models import MarketBundle, NewsEvent, ReportMetadata
from crypto_intel.infrastructure.time import resolve_timezone


DISCLAIMER = (
    "本報告僅供研究與資訊整理，不構成投資建議；資料可能延遲、錯誤或不完整。"
    "價格與事件相關性不代表因果，使用者應自行驗證。"
)


class ReportService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.output_dir = config.report_output_dir

    def compose(
        self,
        report_date: str,
        market: MarketBundle,
        top_events: list[NewsEvent],
        deep_analysis: bool,
        dry_run: bool,
        warnings: list[str],
    ) -> tuple[dict, ReportMetadata]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        generated_at = datetime.now(resolve_timezone(self.config.timezone))
        base = f"Crypto_Market_Intelligence_{report_date}"
        payload = {
            "report_date": report_date,
            "timezone": self.config.timezone,
            "generated_at": generated_at.isoformat(),
            "market": market.to_dict(),
            "top_events": [event.to_dict() for event in top_events],
            "regulatory_events": [event.to_dict() for event in top_events if event.topic == "Regulation"],
            "social_hotspots": [],
            "correlation_observations": [
                {
                    "claim": "本 MVP 僅列出價格與事件的同日觀察，不宣稱因果。",
                    "confidence": 0.4,
                    "uncertainty": "需累積更多歷史資料後才能做 lead-lag 分析。",
                }
            ],
            "risks": _risks(market, top_events, warnings),
            "watchlist_24_72h": _watchlist(top_events),
            "deep_analysis": _deep_analysis_stub(deep_analysis),
            "sources": _sources(top_events),
            "data_quality": {
                "event_count": len(top_events),
                "warnings": warnings,
            },
            "disclaimer": DISCLAIMER,
        }
        json_path = self.output_dir / f"{base}.json"
        html_path = self.output_dir / f"{base}.html"
        pdf_path = self.output_dir / f"{base}.pdf"
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        html_path.write_text(render_html(payload), encoding="utf-8")
        actual_pdf_path = write_pdf(pdf_path, payload)
        metadata = ReportMetadata(
            report_date=report_date,
            timezone=self.config.timezone,
            generated_at=generated_at,
            html_path=str(html_path),
            pdf_path=str(actual_pdf_path) if actual_pdf_path else None,
            json_path=str(json_path),
            deep_analysis=deep_analysis,
            dry_run=dry_run,
            warnings=warnings,
        )
        return payload, metadata


def render_html(payload: dict) -> str:
    market = payload["market"]
    btc = market.get("btc_usd") or {}
    btc_twd = market.get("btc_twd") or {}
    usdt = market.get("usdt_usd") or {}
    rows = "\n".join(_event_row(event, index) for index, event in enumerate(payload["top_events"], 1))
    warnings = "".join(f"<li>{html.escape(item)}</li>" for item in payload["data_quality"].get("warnings", []))
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <title>Crypto Market Intelligence {html.escape(payload["report_date"])}</title>
  <style>
    body {{ font-family: "Noto Sans TC", "Microsoft JhengHei", Arial, sans-serif; margin: 32px; color: #17202a; }}
    h1, h2 {{ color: #102a43; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
    th, td {{ border: 1px solid #d9e2ec; padding: 8px; vertical-align: top; }}
    th {{ background: #f0f4f8; text-align: left; }}
    .muted {{ color: #627d98; }}
    .risk {{ background: #fffbea; border-left: 4px solid #f0b429; padding: 12px; }}
  </style>
</head>
<body>
  <h1>Crypto Intelligence Daily</h1>
  <p class="muted">日期：{html.escape(payload["report_date"])}｜時區：{html.escape(payload["timezone"])}｜產生時間：{html.escape(payload["generated_at"])}</p>
  <h2>今日市場總覽</h2>
  <table>
    <tr><th>指標</th><th>數值</th><th>來源</th></tr>
    <tr><td>BTC/USD</td><td>{_money(btc.get("price"), "USD")}</td><td>{html.escape(btc.get("provider", ""))}</td></tr>
    <tr><td>BTC/TWD</td><td>{_money(btc_twd.get("price"), "TWD")} {"(推算)" if btc_twd.get("inferred") else ""}</td><td>{html.escape(btc_twd.get("provider", ""))}</td></tr>
    <tr><td>USDT/USD</td><td>{_money(usdt.get("price"), "USD")}</td><td>{html.escape(usdt.get("provider", ""))}</td></tr>
    <tr><td>BTC dominance</td><td>{_pct(market.get("btc_dominance"))}</td><td>provider/global</td></tr>
    <tr><td>USDT depeg</td><td>{market.get("usdt_depeg")}</td><td>abs(price - 1)</td></tr>
  </table>
  <h2>今日最重要 10 條情報</h2>
  <table>
    <tr><th>#</th><th>標題</th><th>分類</th><th>影響</th><th>可信度</th><th>來源</th></tr>
    {rows}
  </table>
  <h2>風險警示</h2>
  <div class="risk"><ul>{warnings or "<li>目前無重大系統警示。</li>"}</ul></div>
  <h2>未來 24 至 72 小時觀察清單</h2>
  <ul>{"".join(f"<li>{html.escape(item)}</li>" for item in payload["watchlist_24_72h"])}</ul>
  <h2>免責聲明</h2>
  <p>{html.escape(payload["disclaimer"])}</p>
</body>
</html>
"""


def write_pdf(path: Path, payload: dict) -> Path | None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfgen import canvas

        font = "Helvetica"
        for candidate in [
            Path("C:/Windows/Fonts/msjh.ttc"),
            Path("C:/Windows/Fonts/NotoSansTC-Regular.ttf"),
        ]:
            if candidate.exists():
                pdfmetrics.registerFont(TTFont("CIDailyCJK", str(candidate)))
                font = "CIDailyCJK"
                break
        c = canvas.Canvas(str(path), pagesize=A4)
        c.setFont(font, 14)
        y = 800
        lines = [
            "Crypto Intelligence Daily",
            f"日期: {payload['report_date']}  時區: {payload['timezone']}",
            "今日市場總覽與 Top 10 情報請以 HTML/JSON 為完整版本。",
            DISCLAIMER,
        ]
        for event in payload["top_events"][:10]:
            lines.append(f"- {event['title']} ({event['classification']}, confidence={event['confidence']})")
        for line in lines:
            c.drawString(40, y, line[:95])
            y -= 24
            if y < 60:
                c.showPage()
                c.setFont(font, 14)
                y = 800
        c.save()
        return path
    except Exception:
        path.write_bytes(_minimal_pdf_bytes(payload))
        return path


def _minimal_pdf_bytes(payload: dict) -> bytes:
    text = f"Crypto Intelligence Daily {payload['report_date']} - see HTML/JSON for Traditional Chinese report."
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    body = f"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj
4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
5 0 obj << /Length {len(escaped) + 48} >> stream
BT /F1 14 Tf 72 720 Td ({escaped}) Tj ET
endstream endobj
xref
0 6
0000000000 65535 f 
trailer << /Root 1 0 R /Size 6 >>
startxref
0
%%EOF
"""
    return body.encode("latin-1", errors="replace")


def _event_row(event: dict, index: int) -> str:
    title = html.escape(event["title"])
    summary = html.escape(event["summary"])
    source_url = html.escape(event["source_url"], quote=True)
    return (
        f"<tr><td>{index}</td><td><strong>{title}</strong><br>{summary}</td>"
        f"<td>{html.escape(event['classification'])}</td>"
        f"<td>{html.escape(event['impact_direction'])}</td>"
        f"<td>{event['confidence']:.2f}</td>"
        f"<td><a href=\"{source_url}\">{html.escape(event['source_name'])}</a></td></tr>"
    )


def _money(value: float | None, currency: str) -> str:
    if value is None:
        return "N/A"
    return f"{value:,.4f} {currency}" if value < 10 else f"{value:,.2f} {currency}"


def _pct(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.2f}%"


def _risks(market: MarketBundle, events: list[NewsEvent], warnings: list[str]) -> list[str]:
    risks = list(warnings)
    if market.usdt_depeg is not None and market.usdt_depeg > 0.01:
        risks.append("USDT 偏離 1 美元超過 1%，需提高穩定幣風險監控。")
    if len(events) < 5:
        risks.append("可用事件少於 5 筆，今日情報完整性不足。")
    return risks


def _watchlist(events: list[NewsEvent]) -> list[str]:
    topics = []
    for event in events:
        if event.topic not in topics:
            topics.append(event.topic)
    return [f"追蹤 {topic} 類事件是否有官方後續或市場量價反應。" for topic in topics[:6]]


def _deep_analysis_stub(enabled: bool) -> dict | None:
    if not enabled:
        return None
    return {
        "status": "data_accumulating",
        "summary": "三日深度分析已觸發；若有效歷史資料不足，僅輸出累積狀態。",
    }


def _sources(events: list[NewsEvent]) -> list[dict]:
    return [
        {
            "name": event.source_name,
            "url": event.source_url,
            "event_time": event.event_time.isoformat(),
        }
        for event in events
    ]
