from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path

from crypto_intel.config import AppConfig
from crypto_intel.domain.models import MarketBundle, NewsEvent, ReportMetadata
from crypto_intel.infrastructure.time import resolve_timezone
from crypto_intel.services.quality import source_diversity
from crypto_intel.services.source_governance import approved_source_profiles, event_governance


DISCLAIMER = (
    "\u672c\u5831\u544a\u70ba\u8cc7\u8a0a\u6574\u7406\u8207\u6559\u80b2\u7528\u9014\uff0c\u4e0d\u69cb\u6210\u6295\u8cc7\u5efa\u8b70\u3002"
    "\u5a92\u9ad4\u5831\u5c0e\u3001\u672a\u7d93\u5b98\u65b9\u4ea4\u53c9\u78ba\u8a8d\u7684\u8cc7\u8a0a\uff0c\u5747\u4ee5\u300c\u5f85\u4ea4\u53c9\u78ba\u8a8d\u300d\u5448\u73fe\u3002"
)

TOPIC_LABELS = {
    "Regulation": "\u76e3\u7ba1",
    "Security": "\u8cc7\u5b89",
    "ETF": "ETF",
    "Stablecoin": "\u7a69\u5b9a\u5e63",
    "Exchange": "\u4ea4\u6613\u6240",
    "RWA": "RWA",
    "Derivatives": "\u885d\u751f\u6027\u5546\u54c1",
    "Macro": "\u5b8f\u89c0",
    "BTC": "\u6bd4\u7279\u5e63",
    "GitHub": "\u958b\u767c\u6d3b\u52d5",
    "Market": "\u5e02\u5834",
}

SOURCE_TYPE_LABELS = {
    "official_primary": "\u5b98\u65b9\u4e00\u624b\u4f86\u6e90",
    "project_primary": "\u5c08\u6848\u4e00\u624b\u4f86\u6e90",
    "specialist_media": "\u5c08\u696d\u5a92\u9ad4",
    "unverified": "\u672a\u5be9\u6838\u4f86\u6e90",
}


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
        source_events: list[NewsEvent] | None = None,
    ) -> tuple[dict, ReportMetadata]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        generated_at = datetime.now(resolve_timezone(self.config.timezone))
        base = f"Crypto_Market_Intelligence_{report_date}"
        diversity = source_diversity(top_events)
        source_registry = self.config.raw.get("source_registry", {})
        event_payloads = [_event_payload(event, source_registry) for event in top_events]
        latest_source_updates = _source_briefs(source_events or top_events, source_registry)
        payload = {
            "report_date": report_date,
            "timezone": self.config.timezone,
            "generated_at": generated_at.isoformat(),
            "market": market.to_dict(),
            "top_events": event_payloads,
            "source_updates": latest_source_updates,
            "beginner_brief": _beginner_brief(market, top_events, warnings),
            "market_reading": _market_reading(market),
            "learning_corner": _learning_corner(top_events),
            "risks": _risks(market, top_events, warnings),
            "watchlist_24_72h": _watchlist(top_events),
            "deep_analysis": _deep_analysis_stub(deep_analysis),
            "sources": latest_source_updates,
            "data_quality": {
                "event_count": len(top_events),
                "source_diversity": diversity,
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
    usdt = market.get("usdt_usd") or {}
    brief = payload["beginner_brief"]
    quality = payload["data_quality"]["source_diversity"]
    source_updates = "".join(_source_update_card(item) for item in payload["source_updates"])
    event_cards = "".join(_event_card(event, index) for index, event in enumerate(payload["top_events"], 1))
    learning = "".join(
        f"<article class=\"term\"><h3>{html.escape(item['term'])}</h3><p>{html.escape(item['explanation'])}</p></article>"
        for item in payload["learning_corner"]
    )
    warnings = "".join(f"<li>{html.escape(item)}</li>" for item in payload["data_quality"]["warnings"])
    takeaways = "".join(f"<li>{html.escape(item)}</li>" for item in brief["takeaways"])
    return f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Crypto Intelligence Daily {html.escape(payload['report_date'])}</title>
<style>
:root{{--ink:#1d2928;--muted:#5c6967;--line:#d9e3df;--paper:#f4f7f5;--panel:#fff;--teal:#087c69;--teal-soft:#e3f3ed;--amber:#9a6700;--amber-soft:#fff5dc;--red:#a33c45;}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font-family:"Noto Sans TC","Microsoft JhengHei",Arial,sans-serif;line-height:1.6}}.wrap{{max-width:1120px;margin:0 auto;padding:34px 20px 54px}}.masthead{{border-bottom:1px solid var(--line);padding-bottom:20px}}.eyebrow{{margin:0;color:var(--teal);font-weight:700;font-size:13px}}h1{{font-size:30px;margin:4px 0}}h2{{font-size:20px;margin:0 0 12px;color:#075e50}}h3{{font-size:16px;margin:0 0 6px}}p{{margin:0 0 10px}}.meta,.muted{{font-size:13px;color:var(--muted)}}.panel{{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:21px;margin-top:16px}}.lead{{background:var(--teal-soft);border-left:4px solid var(--teal)}}.lead .headline{{font-weight:700;font-size:18px}}.market-grid,.terms{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}}.metric,.term{{background:#f8fbf9;border:1px solid #dfe9e4;border-radius:6px;padding:14px}}.metric span{{color:var(--muted);font-size:13px;display:block}}.metric strong{{font-size:20px;display:block;margin:4px 0}}.source-update,.event{{border-top:1px solid var(--line);padding:18px 0}}.source-update:first-of-type,.event:first-of-type{{border-top:0;padding-top:0}}.source-update-grid,.event-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}.badge{{display:inline-block;padding:3px 7px;border-radius:4px;background:#edf2f0;font-size:12px;margin:0 4px 7px 0}}.badge.warning{{background:var(--amber-soft);color:#765000}}.badge.primary{{background:var(--teal-soft);color:#075e50}}a{{color:#096f60}}.original{{background:#f6f8f7;padding:10px;border-radius:4px;font-size:14px}}.risk{{background:var(--amber-soft);border-left:4px solid var(--amber)}}ul{{margin:8px 0;padding-left:22px}}li{{margin:5px 0}}.footer{{font-size:13px;color:var(--muted);padding:18px 0}}@media(max-width:720px){{.market-grid,.terms,.source-update-grid,.event-grid{{grid-template-columns:1fr}}.wrap{{padding:24px 13px 40px}}h1{{font-size:25px}}}}
</style></head><body><main class="wrap">
<header class="masthead"><p class="eyebrow">BEGINNER EDITION</p><h1>Crypto Intelligence Daily</h1><p class="meta">{html.escape(payload['report_date'])} | {html.escape(payload['generated_at'])} | {html.escape(payload['timezone'])}</p></header>
<section class="panel lead"><h2>\u4eca\u65e5\u5148\u8b80\u7d50\u8ad6</h2><p class="headline">{html.escape(brief['headline'])}</p><ul>{takeaways}</ul></section>
<section class="panel"><h2>\u5e02\u5834\u6eab\u5ea6\u8a08</h2><div class="market-grid"><article class="metric"><span>BTC/USD</span><strong>{_money(btc.get('price'), 'USD')}</strong><p>24h {_pct(btc.get('change_24h_pct'))}</p></article><article class="metric"><span>USDT/USD</span><strong>{_money(usdt.get('price'), 'USD')}</strong><p>\u504f\u96e2 1 USD {_pct((market.get('usdt_depeg') or 0) * 100)}</p></article><article class="metric"><span>BTC Dominance</span><strong>{_pct(market.get('btc_dominance'))}</strong><p>\u89c0\u5bdf\u8cc7\u91d1\u662f\u5426\u504f\u5411 BTC</p></article></div><p class="muted">{html.escape(payload['market_reading'])}</p></section>
<section class="panel"><h2>\u4f86\u6e90\u96f7\u9054\uff1a\u5404\u4f86\u6e90\u6700\u65b0\u8cc7\u8a0a</h2><p class="muted">\u6bcf\u5247\u4fdd\u7559\u539f\u6587\u6a19\u984c\u3001\u6458\u8981\u8207\u9023\u7d50\u3002\u5a92\u9ad4\u5831\u5c0e\u672a\u7d93\u4ea4\u53c9\u78ba\u8a8d\u524d\uff0c\u50c5\u4f5c\u70ba\u9032\u4e00\u6b65\u8ffd\u67e5\u7684\u8d77\u9ede\u3002</p>{source_updates or '<p>\u672c\u6b21\u672a\u64f7\u53d6\u5230\u7b26\u5408\u6642\u6548\u689d\u4ef6\u7684\u4f86\u6e90\u8cc7\u8a0a\u3002</p>'}</section>
<section class="panel"><h2>\u4eca\u65e5\u91cd\u9ede\u4e8b\u4ef6</h2>{event_cards or '<p>\u6c92\u6709\u7b26\u5408\u76ee\u524d\u6642\u6548\u8207\u4f86\u6e90\u898f\u5247\u7684\u4e8b\u4ef6\u3002</p>'}</section>
<section class="panel"><h2>\u65b0\u624b\u5b78\u7fd2\u89d2</h2><div class="terms">{learning}</div></section>
<section class="panel risk"><h2>\u8cc7\u6599\u54c1\u8cea\u8207\u98a8\u96aa\u63d0\u793a</h2><p>\u672c\u6b21\u5171\u4f7f\u7528 {quality['independent_sources']} \u500b\u7368\u7acb\u7db2\u57df\uff1b{quality['primary_source_events']} \u5247\u70ba\u5b98\u65b9\u4e00\u624b\u8cc7\u8a0a\uff1b{quality['requires_confirmation_events']} \u5247\u4ecd\u9700\u4ea4\u53c9\u78ba\u8a8d\u3002</p><ul>{warnings or '<li>\u672a\u5075\u6e2c\u5230\u984d\u5916\u54c1\u8cea\u63d0\u793a\u3002</li>'}</ul></section>
<section class="panel"><h2>24-72 \u5c0f\u6642\u8ffd\u8e64</h2><ul>{''.join(f'<li>{html.escape(item)}</li>' for item in payload['watchlist_24_72h'])}</ul></section>
<footer class="footer">{html.escape(payload['disclaimer'])}</footer></main></body></html>"""


def write_pdf(path: Path, payload: dict) -> Path | None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

        pdfmetrics.registerFont(UnicodeCIDFont("MSung-Light"))
        styles = getSampleStyleSheet()
        styles["Normal"].fontName = "MSung-Light"
        styles["Title"].fontName = "MSung-Light"
        story = [Paragraph("Crypto Intelligence Daily", styles["Title"])]
        story.append(Paragraph(payload["beginner_brief"]["headline"], styles["Normal"]))
        story.append(Spacer(1, 10))
        for item in payload["source_updates"]:
            story.append(Paragraph(f"{item['source_name']}: {item['title']}", styles["Normal"]))
        SimpleDocTemplate(str(path), pagesize=A4).build(story)
        return path
    except Exception:
        path.write_bytes(b"%PDF-1.4\n% Crypto Intelligence Daily\n")
        return path


def _event_payload(event: NewsEvent, source_registry: dict) -> dict:
    payload = event.to_dict()
    payload["governance"] = event_governance(event, source_registry)
    return payload


def _source_briefs(events: list[NewsEvent], source_registry: dict) -> list[dict]:
    latest: dict[str, NewsEvent] = {}
    for event in sorted(events, key=lambda item: item.event_time, reverse=True):
        key = event.source_name
        latest.setdefault(key, event)
    briefs = []
    for event in latest.values():
        governance = event_governance(event, source_registry)
        briefs.append({
            "source_name": event.source_name,
            "source_url": event.source_url,
            "event_time": event.event_time.isoformat(),
            "title": event.title,
            "original_summary": _clean_summary(event.summary),
            "topic": event.topic,
            "governance": governance,
            "follow_up": _follow_up(governance),
            "available": True,
        })
    known_names = {item["source_name"] for item in briefs}
    for profile in approved_source_profiles(source_registry):
        if profile.name in known_names:
            continue
        briefs.append({
            "source_name": profile.name,
            "source_url": profile.source_url,
            "event_time": None,
            "title": "No eligible update in the configured freshness window.",
            "original_summary": "",
            "topic": "Market",
            "governance": {
                "tier": profile.tier,
                "source_type": profile.source_type,
                "claim_scope": profile.claim_scope,
                "verification_status": profile.verification_status,
                "requires_confirmation": profile.requires_confirmation,
                "conflict_note": profile.conflict_note,
            },
            "follow_up": "Check the source feed directly if this source is important to your current question.",
            "available": False,
        })
    return briefs


def _source_update_card(item: dict) -> str:
    governance = item["governance"]
    source_url = html.escape(item["source_url"], quote=True)
    verification = "\u5f85\u4ea4\u53c9\u78ba\u8a8d" if governance["requires_confirmation"] else "\u4e00\u624b\u8cc7\u8a0a"
    warning_badge = " warning" if governance["requires_confirmation"] else " primary"
    conflict = f"<p class=\"muted\">\u8a3b\u8a18\uff1a{html.escape(governance['conflict_note'])}</p>" if governance["conflict_note"] else ""
    item_status = "\u672c\u6b21\u7121\u7b26\u5408\u6642\u6548\u7684\u66f4\u65b0" if not item["available"] else verification
    headline = "\u672c\u6b21\u672a\u64f7\u53d6\u5230\u7b26\u5408\u6642\u6548\u689d\u4ef6\u7684\u66f4\u65b0\u3002" if not item["available"] else html.escape(item["title"])
    summary = "\u4f86\u6e90\u4ecd\u5217\u5165\u76e3\u63a7\uff0c\u53ef\u76f4\u63a5\u958b\u555f RSS \u4f86\u6e90\u67e5\u770b\u3002" if not item["available"] else html.escape(item["original_summary"])
    timestamp = item["event_time"] or "N/A"
    return f"""<article class="source-update"><span class="badge">{html.escape(governance['tier'])}</span><span class="badge">{html.escape(SOURCE_TYPE_LABELS.get(governance['source_type'], governance['source_type']))}</span><span class="badge{warning_badge}">{item_status}</span><h3><a href="{source_url}">{html.escape(item['source_name'])}</a></h3><div class="source-update-grid"><div><p><strong>\u6700\u65b0\u539f\u6587\u6a19\u984c\uff1a</strong><a href="{source_url}">{headline}</a></p><p class="original">{summary or '\u539f\u4f86\u6e90\u672a\u63d0\u4f9b\u6458\u8981\u3002'}</p></div><div><p><strong>\u4f7f\u7528\u908a\u754c\uff1a</strong>{html.escape(governance['claim_scope'])}</p><p><strong>\u8ffd\u67e5\u5efa\u8b70\uff1a</strong>{html.escape(item['follow_up'])}</p><p class="muted">\u66f4\u65b0\u6642\u9593\uff1a{html.escape(timestamp)}</p>{conflict}</div></div></article>"""


def _event_card(event: dict, index: int) -> str:
    governance = event["governance"]
    source_url = html.escape(event["source_url"], quote=True)
    status = "\u5f85\u4ea4\u53c9\u78ba\u8a8d" if governance["requires_confirmation"] else "\u4e00\u624b\u8cc7\u8a0a"
    return f"""<article class="event"><p class="muted">{index}. {html.escape(TOPIC_LABELS.get(event['topic'], event['topic']))} | {html.escape(status)}</p><h3><a href="{source_url}">{html.escape(event['title'])}</a></h3><div class="event-grid"><div><p><strong>\u539f\u6587\u6458\u8981\uff1a</strong>{html.escape(_clean_summary(event['summary']))}</p></div><div><p><strong>\u5c0d\u65b0\u624b\u7684\u610f\u7fa9\uff1a</strong>{html.escape(_beginner_event_summary(event))}</p><p class="muted">\u4f86\u6e90\uff1a<a href="{source_url}">{html.escape(event['source_name'])}</a> | \u4fe1\u5fc3\u5ea6 {event['confidence']:.2f}</p></div></div></article>"""


def _beginner_brief(market: MarketBundle, events: list[NewsEvent], warnings: list[str]) -> dict:
    btc = market.btc_usd
    change = btc.change_24h_pct if btc else None
    move = "\u8cc7\u6599\u7f3a\u5931" if change is None else f"24 \u5c0f\u6642 {change:+.2f}%"
    pending = sum(event_governance(event)["requires_confirmation"] for event in events)
    headline = f"BTC {move}\uff1b\u672c\u6b21\u7d0d\u5165 {len(events)} \u5247\u4e8b\u4ef6\uff0c\u5176\u4e2d {pending} \u5247\u5c1a\u5f85\u4ea4\u53c9\u78ba\u8a8d\u3002"
    takeaways = [
        _market_reading(market),
        f"\u672c\u65e5\u6709 {sum(event_governance(event)['verification_status'] == 'primary_source' for event in events)} \u5247\u5b98\u65b9\u4e00\u624b\u8cc7\u8a0a\uff1b\u5a92\u9ad4\u5831\u5c0e\u4e0d\u4f5c\u70ba\u55ae\u4e00\u4e8b\u5be6\u4f9d\u64da\u3002",
        "\u8acb\u5148\u5f9e\u300c\u4f86\u6e90\u96f7\u9054\u300d\u958b\u555f\u539f\u6587\uff0c\u518d\u6c7a\u5b9a\u662f\u5426\u9700\u8981\u7e7c\u7e8c\u8ffd\u8e64\u3002",
    ]
    if warnings:
        takeaways.append("\u4eca\u65e5\u6709\u8cc7\u6599\u54c1\u8cea\u63d0\u793a\uff0c\u5f37\u5ea6\u8f03\u4f4e\u7684\u8a0a\u865f\u4e0d\u61c9\u89e3\u8b80\u70ba\u4ea4\u6613\u5efa\u8b70\u3002")
    return {"headline": headline, "takeaways": takeaways}


def _market_reading(market: MarketBundle) -> str:
    if market.btc_usd is None:
        return "BTC \u5e02\u5834\u50f9\u683c\u8cc7\u6599\u7f3a\u5931\uff0c\u8acb\u4ee5\u4ea4\u6613\u6240\u6216\u884c\u60c5\u4f9b\u61c9\u5546\u7684\u5373\u6642\u5831\u50f9\u70ba\u6e96\u3002"
    btc_text = f"BTC/USD {market.btc_usd.price:,.2f}\uff0c24 \u5c0f\u6642 {market.btc_usd.change_24h_pct or 0:+.2f}%\u3002"
    usdt_text = "USDT \u8cc7\u6599\u7f3a\u5931\u3002" if market.usdt_usd is None else f"USDT/USD {market.usdt_usd.price:.4f}\uff0c\u504f\u96e2 1 USD {(market.usdt_depeg or 0) * 100:.3f}%\u3002"
    return f"{btc_text} {usdt_text} \u9019\u662f\u884c\u60c5\u8b80\u503c\uff0c\u4e0d\u662f\u9810\u6e2c\u3002"


def _learning_corner(events: list[NewsEvent]) -> list[dict[str, str]]:
    terms = [
        {"term": "\u4e00\u624b\u4f86\u6e90", "explanation": "\u4e8b\u4ef6\u7576\u4e8b\u65b9\u7684\u6b63\u5f0f\u516c\u544a\uff0c\u4f8b\u5982\u76e3\u7ba1\u6a5f\u95dc\u7684\u65b0\u805e\u7a3f\u3002"},
        {"term": "\u4ea4\u53c9\u78ba\u8a8d", "explanation": "\u91cd\u5927\u6d88\u606f\u9700\u8981\u5b98\u65b9\u8aaa\u660e\u6216\u5176\u4ed6\u7368\u7acb\u4f86\u6e90\u652f\u6301\uff0c\u4e0d\u53ea\u770b\u55ae\u4e00\u5a92\u9ad4\u3002"},
        {"term": "USDT \u812b\u9328", "explanation": "USDT \u50f9\u683c\u504f\u96e2 1 USD \u7684\u7a0b\u5ea6\uff1b\u504f\u96e2\u8b8a\u5927\u6642\uff0c\u9700\u66f4\u5bc6\u5207\u89c0\u5bdf\u6d41\u52d5\u6027\u3002"},
    ]
    if any(event.topic == "Regulation" for event in events):
        terms.append({"term": "\u76e3\u7ba1\u65b0\u805e", "explanation": "\u76e3\u7ba1\u516c\u544a\u901a\u5e38\u4f86\u81ea\u5b98\u65b9\uff0c\u4f46\u4ecd\u8981\u5206\u6e05\u5176\u662f\u5426\u76f4\u63a5\u95dc\u4fc2\u52a0\u5bc6\u8cc7\u7522\u3002"})
    return terms[:3]


def _beginner_event_summary(event: dict) -> str:
    governance = event["governance"]
    topic = TOPIC_LABELS.get(event["topic"], event["topic"])
    if governance["requires_confirmation"]:
        return f"\u9019\u662f\u95dc\u65bc{topic}\u7684\u5a92\u9ad4\u8cc7\u8a0a\u3002\u5b83\u503c\u5f97\u4f5c\u70ba\u8ffd\u67e5\u7dda\u7d22\uff0c\u4f46\u91cd\u5927\u5f71\u97ff\u4ecd\u9700\u5b98\u65b9\u6216\u5176\u4ed6\u7368\u7acb\u4f86\u6e90\u78ba\u8a8d\u3002"
    if governance["source_type"] == "project_primary":
        return f"\u9019\u662f\u8a72\u5c08\u6848\u7684\u81ea\u8ff0\uff0c\u53ef\u78ba\u8a8d\u5176\u516c\u544a\u5167\u5bb9\uff0c\u4f46\u4e0d\u61c9\u55ae\u7368\u63a8\u8ad6\u6574\u9ad4\u5e02\u5834\u3002"
    return f"\u9019\u662f\u5b98\u65b9\u4e00\u624b\u8cc7\u8a0a\u3002\u8acb\u78ba\u8a8d\u516c\u544a\u662f\u5426\u76f4\u63a5\u95dc\u4fc2 BTC\u3001USDT \u6216\u4f60\u7684\u6301\u5009\u3002"


def _follow_up(governance: dict) -> str:
    if governance["requires_confirmation"]:
        return "\u5c0b\u627e\u5b98\u65b9\u516c\u544a\u6216\u81f3\u5c11\u53e6\u4e00\u500b\u7368\u7acb\u4f86\u6e90\u5f8c\uff0c\u518d\u5224\u65b7\u5176\u5f71\u97ff\u3002"
    if governance["source_type"] == "project_primary":
        return "\u958b\u555f\u539f\u6587\u4e86\u89e3\u516c\u544a\u7bc4\u570d\uff0c\u4e26\u6bd4\u5c0d\u5e02\u5834\u6578\u64da\u8207\u5916\u90e8\u8cc7\u8a0a\u3002"
    return "\u958b\u555f\u5b98\u65b9\u539f\u6587\uff0c\u78ba\u8a8d\u4e8b\u4ef6\u5c0d\u8c61\u3001\u6642\u9593\u8207\u6b63\u5f0f\u884c\u52d5\u3002"


def _clean_summary(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", value)).strip()[:700]


def _risks(market: MarketBundle, events: list[NewsEvent], warnings: list[str]) -> list[str]:
    risks = list(warnings)
    if market.usdt_depeg is not None and market.usdt_depeg > 0.01:
        risks.append("USDT \u504f\u96e2 1 USD \u8d85\u904e 1%\uff0c\u9700\u4ee5\u9ad8\u512a\u5148\u9806\u5e8f\u9a57\u8b49\u3002")
    pending = sum(event_governance(event)["requires_confirmation"] for event in events)
    if pending:
        risks.append(f"{pending} \u5247\u91cd\u9ede\u4e8b\u4ef6\u70ba\u5a92\u9ad4\u8cc7\u8a0a\uff0c\u4e0d\u61c9\u4f5c\u70ba\u55ae\u4e00\u4ea4\u6613\u4f9d\u64da\u3002")
    return risks


def _watchlist(events: list[NewsEvent]) -> list[str]:
    topics: list[str] = []
    for event in events:
        if event.topic not in topics:
            topics.append(event.topic)
    return [f"\u8ffd\u8e64 {TOPIC_LABELS.get(topic, topic)} \u662f\u5426\u51fa\u73fe\u5b98\u65b9\u516c\u544a\u3001\u6578\u64da\u9a57\u8b49\u6216\u7368\u7acb\u4ea4\u53c9\u78ba\u8a8d\u3002" for topic in topics[:5]] or ["\u7e7c\u7e8c\u8ffd\u8e64\u5b98\u65b9\u4f86\u6e90\u662f\u5426\u516c\u5e03\u65b0\u8cc7\u8a0a\u3002"]


def _deep_analysis_stub(enabled: bool) -> dict | None:
    if not enabled:
        return None
    return {"status": "data_accumulating", "summary": "\u6b77\u53f2\u8cc7\u6599\u6301\u7e8c\u7d2f\u7a4d\u4e2d\uff0c\u6df1\u5ea6\u5206\u6790\u4e0d\u4ee3\u8868\u9810\u6e2c\u3002"}


def _money(value: float | None, currency: str) -> str:
    if value is None:
        return "N/A"
    return f"{value:,.4f} {currency}" if value < 10 else f"{value:,.2f} {currency}"


def _pct(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.2f}%"
