from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path

from crypto_intel.config import AppConfig
from crypto_intel.domain.models import MarketBundle, NewsEvent, ReportMetadata
from crypto_intel.infrastructure.time import resolve_timezone
from crypto_intel.services.quality import source_diversity


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
        diversity = source_diversity(top_events)
        beginner_brief = _beginner_brief(market, top_events, warnings)
        payload = {
            "report_date": report_date,
            "timezone": self.config.timezone,
            "generated_at": generated_at.isoformat(),
            "market": market.to_dict(),
            "top_events": [event.to_dict() for event in top_events],
            "regulatory_events": [event.to_dict() for event in top_events if event.topic == "Regulation"],
            "social_hotspots": [],
            "beginner_brief": beginner_brief,
            "market_reading": _market_reading(market),
            "learning_corner": _learning_corner(market, top_events),
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
    btc_twd = market.get("btc_twd") or {}
    usdt = market.get("usdt_usd") or {}
    brief = payload["beginner_brief"]
    source_quality = payload["data_quality"]["source_diversity"]
    event_cards = "\n".join(_event_card(event, index) for index, event in enumerate(payload["top_events"], 1))
    warnings = "".join(f"<li>{html.escape(item)}</li>" for item in payload["data_quality"].get("warnings", []))
    learning = "".join(
        f"<article class=\"term\"><h3>{html.escape(item['term'])}</h3><p>{html.escape(item['explanation'])}</p></article>"
        for item in payload["learning_corner"]
    )
    takeaway_items = "".join(f"<li>{html.escape(item)}</li>" for item in brief["takeaways"])
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Crypto Intelligence Daily {html.escape(payload["report_date"])}</title>
  <style>
    :root {{ --ink:#1f2a2e; --muted:#5d6b71; --line:#d8e0dc; --paper:#f4f6f3; --panel:#fff; --teal:#057968; --teal-soft:#e4f3ee; --amber:#a26900; --amber-soft:#fff4d6; --red:#a43c45; --red-soft:#fae9ea; }}
    * {{ box-sizing:border-box; }} body {{ margin:0; background:var(--paper); color:var(--ink); font-family:"Noto Sans TC","Microsoft JhengHei",Arial,sans-serif; line-height:1.65; }}
    .wrap {{ max-width:1100px; margin:0 auto; padding:36px 22px 52px; }} .masthead {{ border-bottom:1px solid var(--line); padding-bottom:24px; margin-bottom:20px; }}
    h1 {{ font-size:28px; margin:0 0 6px; }} h2 {{ color:#075d50; font-size:20px; margin:0 0 14px; }} h3 {{ font-size:15px; margin:0 0 6px; }} p {{ margin:0 0 10px; }}
    .meta,.muted {{ color:var(--muted); font-size:14px; }} .eyebrow {{ color:var(--teal); font-weight:700; font-size:13px; margin-bottom:4px; }}
    .panel {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:22px; margin:16px 0; }} .lead {{ background:var(--teal-soft); border-left:4px solid var(--teal); }}
    .lead .summary {{ font-size:18px; font-weight:700; line-height:1.6; }} .grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }}
    .metric {{ background:#f8faf8; border:1px solid #e0e7e3; border-radius:6px; padding:14px; }} .metric span {{ color:var(--muted); display:block; font-size:13px; }} .metric strong {{ display:block; font-size:19px; margin:4px 0; }} .metric p {{ font-size:13px; margin:0; }}
    .signal {{ display:flex; align-items:center; gap:8px; font-size:14px; margin:8px 0; }} .dot {{ width:10px; height:10px; border-radius:50%; background:var(--teal); flex:none; }} .dot.warn {{ background:var(--amber); }} .dot.risk {{ background:var(--red); }}
    .event {{ border-top:1px solid var(--line); padding:20px 0; }} .event:first-of-type {{ border-top:0; padding-top:0; }} .event-title {{ color:#123d38; font-size:17px; margin:4px 0 10px; }} .event-title a {{ color:inherit; }}
    .tag {{ display:inline-block; font-size:12px; background:#edf2f0; color:#405158; padding:3px 7px; border-radius:4px; margin-right:5px; }} .event-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
    .event-grid p {{ font-size:14px; }} .source {{ color:var(--muted); font-size:13px; }} .source a {{ color:var(--teal); }} ul {{ margin:8px 0; padding-left:22px; }} li {{ margin:5px 0; }}
    .risk {{ background:var(--amber-soft); border-left:4px solid var(--amber); }} .terms {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }} .term {{ background:#f8faf8; border:1px solid #e0e7e3; padding:14px; border-radius:6px; }} .term p {{ font-size:14px; margin:0; }}
    .footer {{ color:var(--muted); font-size:13px; padding-top:16px; }} @media(max-width:720px) {{ .grid,.terms,.event-grid {{ grid-template-columns:1fr; }} .wrap {{ padding:24px 14px 36px; }} h1 {{ font-size:24px; }} }}
  </style>
</head>
<body>
  <main class="wrap">
    <header class="masthead"><p class="eyebrow">BEGINNER EDITION｜初學者版</p><h1>Crypto Intelligence Daily</h1><p class="meta">日期：{html.escape(payload["report_date"])}｜台北時間：{html.escape(payload["generated_at"])}｜市場資料：{html.escape(btc.get("provider", "N/A"))}</p></header>
    <section class="panel lead"><h2>先看這裡：今天的三個重點</h2><p class="summary">{html.escape(brief["headline"])}</p><ul>{takeaway_items}</ul><p class="muted">這是根據當日快照與可用公開來源的整理，不代表買賣建議。</p></section>
    <section class="panel"><h2>市場現在在說什麼？</h2><div class="grid"><article class="metric"><span>BTC/USD</span><strong>{_money(btc.get("price"), "USD")}</strong><p>24 小時 {_pct(btc.get("change_24h_pct"))}｜7 日 {_pct(btc.get("change_7d_pct"))}</p></article><article class="metric"><span>BTC/TWD</span><strong>{_money(btc_twd.get("price"), "TWD")}</strong><p>{"此數值由來源直接提供。" if not btc_twd.get("inferred") else "此數值為推算，需留意匯率影響。"}</p></article><article class="metric"><span>USDT/USD</span><strong>{_money(usdt.get("price"), "USD")}</strong><p>偏離 1 美元：{_pct((market.get("usdt_depeg") or 0) * 100)}</p></article></div><div class="signal"><span class="dot"></span>{html.escape(payload["market_reading"]["btc"])} </div><div class="signal"><span class="dot {payload['market_reading']['usdt_status']}"></span>{html.escape(payload["market_reading"]["usdt"])} </div><div class="signal"><span class="dot warn"></span>{html.escape(payload["market_reading"]["dominance"])} </div></section>
    <section class="panel"><h2>今日情報：中文導讀，原文追溯</h2><p class="muted">每個來源最多保留兩則；當日不足時不以重複來源補滿。</p>{event_cards or '<p>今日沒有足夠新鮮且來源獨立的公開事件可列入。市場快照仍可參考，但事件面應保持保守。</p>'}</section>
    <section class="panel"><h2>初學者學習角</h2><div class="terms">{learning}</div></section>
    <section class="panel risk"><h2>資料品質與閱讀限制</h2><p>本日入選 {payload['data_quality']['event_count']} 則事件，來自 {source_quality['independent_sources']} 個獨立來源；最大來源占比 {_pct(source_quality['largest_source_share'] * 100)}。</p><ul>{warnings or '<li>目前無額外系統警示。</li>'}</ul></section>
    <section class="panel"><h2>接下來 24 至 72 小時要確認什麼？</h2><ul>{"".join(f"<li>{html.escape(item)}</li>" for item in payload["watchlist_24_72h"])}</ul><p class="muted">不要把單日漲跌、單一新聞或單一來源直接解讀成趨勢或因果。</p></section>
    <footer class="footer"><p>{html.escape(payload["disclaimer"])}</p></footer>
  </main>
</body>
</html>
"""


def write_pdf(path: Path, payload: dict) -> Path | None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfgen import canvas

        font = "MSung-Light"
        try:
            pdfmetrics.registerFont(UnicodeCIDFont(font))
        except Exception:
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
        lines = ["Crypto Intelligence Daily｜初學者版", f"日期: {payload['report_date']}  時區: {payload['timezone']}"]
        lines.extend(payload["beginner_brief"]["takeaways"])
        lines.append("今日情報（原文標題）：")
        for event in payload["top_events"][:10]:
            lines.append(f"- {event['title']}")
        lines.append(DISCLAIMER)
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


def _event_card(event: dict, index: int) -> str:
    title = html.escape(event["title"])
    source_url = html.escape(event["source_url"], quote=True)
    return f"""<article class="event"><span class="tag">#{index}</span><span class="tag">{html.escape(_topic_label(event['topic']))}</span><span class="tag">{html.escape(_classification_label(event['classification']))}</span><h3 class="event-title"><a href="{source_url}">{title}</a></h3><div class="event-grid"><div><h3>中文導讀</h3><p>{html.escape(_beginner_event_summary(event))}</p></div><div><h3>為什麼值得看？</h3><p>{html.escape(_beginner_impact(event))}</p></div></div><p class="source">原文來源：<a href="{source_url}">{html.escape(event['source_name'])}</a>｜可信度 {event['confidence']:.2f}｜發生時間 {html.escape(event['event_time'])}</p></article>"""


def _money(value: float | None, currency: str) -> str:
    if value is None:
        return "N/A"
    return f"{value:,.4f} {currency}" if value < 10 else f"{value:,.2f} {currency}"


def _pct(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.2f}%"


TOPIC_LABELS = {
    "Regulation": "監管",
    "Security": "資安",
    "ETF": "ETF",
    "Stablecoin": "穩定幣",
    "Exchange": "交易所",
    "RWA": "實體資產代幣化",
    "Derivatives": "衍生品",
    "Macro": "總體經濟",
    "BTC": "比特幣網路",
    "GitHub": "開發生態",
    "Market": "市場",
}


def _beginner_brief(market: MarketBundle, events: list[NewsEvent], warnings: list[str]) -> dict:
    btc_change = market.btc_usd.change_24h_pct if market.btc_usd else None
    btc_move = _move_description(btc_change)
    usdt_depeg = market.usdt_depeg or 0.0
    event_sentence = (
        f"今天有 {len(events)} 則符合時效與來源多樣性條件的公開事件可供閱讀。"
        if events
        else "今天沒有足夠新鮮且來源獨立的公開事件，因此不將舊聞或範例資料填入報告。"
    )
    headline = f"BTC 今日{btc_move}；USDT 與 1 美元的偏離約 {usdt_depeg * 100:.3f}%。{event_sentence}"
    takeaways = [
        _btc_takeaway(market),
        _usdt_takeaway(market),
        event_sentence,
    ]
    if warnings:
        takeaways.append("資料品質有提醒，請優先閱讀下方的限制說明。")
    return {"headline": headline, "takeaways": takeaways}


def _market_reading(market: MarketBundle) -> dict:
    btc = market.btc_usd
    if btc is None:
        btc_text = "BTC 價格資料暫缺，今天不宜對價格方向做判讀。"
    else:
        btc_text = _btc_takeaway(market)
    depeg = market.usdt_depeg or 0.0
    if depeg < 0.003:
        usdt_text, usdt_status = "USDT 仍接近 1 美元，暫未出現明顯脫鉤訊號。", ""
    elif depeg < 0.01:
        usdt_text, usdt_status = "USDT 有可見偏離，應留意流動性與不同交易場所的報價。", "warn"
    else:
        usdt_text, usdt_status = "USDT 偏離幅度較大，需優先查核流動性、交易所與官方資訊。", "risk"
    dominance = (
        f"BTC 市占率為 {market.btc_dominance:.2f}%。它反映比特幣在整體加密市值的比重，不等於短期漲跌預測。"
        if market.btc_dominance is not None
        else "BTC 市占率資料暫缺。"
    )
    return {"btc": btc_text, "usdt": usdt_text, "usdt_status": usdt_status, "dominance": dominance}


def _learning_corner(market: MarketBundle, events: list[NewsEvent]) -> list[dict[str, str]]:
    topics = {event.topic for event in events}
    terms = [
        {
            "term": "USDT 脫鉤（depeg）",
            "explanation": "USDT 理論上接近 1 美元。偏離愈大，愈需要檢查交易場所流動性與市場壓力，但單一報價不代表整體風險。",
        },
        {
            "term": "BTC 市占率（dominance）",
            "explanation": "比特幣市值占整個加密市場的比例。它可觀察資金是否偏向 BTC，但不能單獨用來預測價格。",
        },
    ]
    if "Regulation" in topics:
        terms.append(
            {
                "term": "監管事件",
                "explanation": "官方公告可能影響長期合規成本或產品設計；除非明確指向加密資產，通常不應直接解讀為當日價格訊號。",
            }
        )
    else:
        terms.append(
            {
                "term": "相關性不是因果",
                "explanation": "價格與新聞在同一天發生，不代表其中一者造成另一者。至少要確認時間順序、成交量與其他獨立證據。",
            }
        )
    return terms


def _beginner_event_summary(event: dict) -> str:
    topic = event["topic"]
    if topic == "Regulation":
        return "這是一則官方監管資訊。先確認它是否直接提到加密資產、穩定幣或 ETF；若沒有，較適合作為背景，而非即時市場訊號。"
    if topic == "Security":
        return "這是資安相關訊息。初學者應先查核受影響的協議、資產與官方事故說明，再判斷是否真的波及持有或使用的服務。"
    if topic == "Stablecoin":
        return "這與穩定幣或其價格穩定性有關。可搭配 USDT/USD 偏離與多個交易場所報價一起看。"
    if topic == "ETF":
        return "這與 ETF 或傳統資金參與有關。它可能影響市場敘事，但單一公告或單日數字不足以證明價格因果。"
    return f"這則資訊歸類為「{_topic_label(topic)}」。先看原文是否直接涉及 BTC、USDT 或加密市場，再評估它的實際關聯性。"


def _beginner_impact(event: dict) -> str:
    assets = "、".join(event.get("affected_assets") or [])
    asset_text = f"系統辨識的可能相關標的：{assets}。" if assets else "系統未將它直接連結到 BTC 或 USDT。"
    return f"{asset_text} 目前分類為「{_classification_label(event['classification'])}」，短期方向為「{_impact_label(event['impact_direction'])}」，需持續以原文與市場數據交叉確認。"


def _topic_label(topic: str) -> str:
    return TOPIC_LABELS.get(topic, topic)


def _classification_label(value: str) -> str:
    return {"fact": "事實", "inference": "推論", "rumor": "傳聞"}.get(value, value)


def _impact_label(value: str) -> str:
    return {"bullish": "偏利多", "bearish": "偏利空", "neutral": "中性", "mixed": "混合"}.get(value, value)


def _move_description(change: float | None) -> str:
    if change is None:
        return "缺少 24 小時變動資料"
    if change >= 2:
        return "明顯上漲"
    if change <= -2:
        return "明顯下跌"
    return "小幅波動"


def _btc_takeaway(market: MarketBundle) -> str:
    btc = market.btc_usd
    if btc is None:
        return "BTC 價格資料暫缺，今天只保留事件與風險觀察。"
    return f"BTC/USD 為 {btc.price:,.2f}，24 小時變動 {_pct(btc.change_24h_pct)}。這描述價格變化，不足以單獨確認趨勢。"


def _usdt_takeaway(market: MarketBundle) -> str:
    usdt = market.usdt_usd
    if usdt is None:
        return "USDT/USD 資料暫缺，無法檢查穩定幣是否接近 1 美元。"
    return f"USDT/USD 為 {usdt.price:.4f}，偏離 1 美元約 {(market.usdt_depeg or 0) * 100:.3f}%。偏離幅度需搭配多個交易場所確認。"


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
    items = [f"追蹤 {_topic_label(topic)} 類事件是否有官方後續或市場量價反應。" for topic in topics[:6]]
    return items or ["等待更多來源獨立且時效足夠的公開事件，再建立事件面判讀。"]


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
