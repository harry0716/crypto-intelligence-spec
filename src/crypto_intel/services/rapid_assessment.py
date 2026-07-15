from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse
from uuid import uuid4

from crypto_intel.config import AppConfig
from crypto_intel.domain.enums import EventClassification, ImpactDirection
from crypto_intel.domain.models import MarketBundle, NewsEvent
from crypto_intel.infrastructure.database import connect, migrate
from crypto_intel.infrastructure.time import resolve_timezone
from crypto_intel.providers.market.coingecko import CoinGeckoMarketProvider
from crypto_intel.providers.market.static import StaticMarketProvider
from crypto_intel.providers.news.rss import RssNewsProvider
from crypto_intel.repositories.event_repository import EventRepository
from crypto_intel.repositories.market_repository import MarketRepository
from crypto_intel.repositories.rapid_assessment_repository import RapidAssessmentRepository
from crypto_intel.repositories.report_repository import ReportRepository
from crypto_intel.services.analytics import snapshots_from_bundle
from crypto_intel.services.collection import CollectionService
from crypto_intel.services.quality import market_warnings, single_domain_ratio
from crypto_intel.services.ranking import rank_events


MAX_TITLE_LENGTH = 160
MAX_OBSERVATION_LENGTH = 2_000
MAX_SOURCE_URLS = 5


@dataclass(frozen=True)
class ManualAssessmentInput:
    title: str
    observation: str
    stated_direction: ImpactDirection
    urgency: str
    source_urls: list[str]

    @classmethod
    def from_payload(cls, payload: dict) -> "ManualAssessmentInput":
        title = _required_text(payload.get("title"), "情境標題", MAX_TITLE_LENGTH)
        observation = _required_text(payload.get("observation"), "你的觀察", MAX_OBSERVATION_LENGTH)
        try:
            direction = ImpactDirection(str(payload.get("stated_direction", "mixed")))
        except ValueError as exc:
            raise ValueError("市場方向必須是 bullish、bearish、neutral 或 mixed。") from exc
        urgency = str(payload.get("urgency", "high")).lower()
        if urgency not in {"normal", "high", "critical"}:
            raise ValueError("緊急程度必須是 normal、high 或 critical。")
        urls = _validate_source_urls(payload.get("source_urls", []))
        return cls(title, observation, direction, urgency, urls)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "observation": self.observation,
            "stated_direction": self.stated_direction.value,
            "urgency": self.urgency,
            "source_urls": self.source_urls,
        }


class RapidAssessmentService:
    """Produces a traceable, rule-based response to a user-supplied market observation."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def assess(self, manual_input: ManualAssessmentInput) -> dict:
        started_at = datetime.now(resolve_timezone(self.config.timezone))
        collector = CollectionService(
            market_provider=CoinGeckoMarketProvider(),
            fallback_market_provider=StaticMarketProvider(),
            news_providers=[RssNewsProvider()],
        )
        market, market_health = collector.collect_market()
        events, news_health = collector.collect_events(
            self.config.top_event_count,
            max_event_age_hours=self.config.max_event_age_hours,
            max_per_source=self.config.max_events_per_source,
        )
        warnings = market_warnings(market)
        if len(events) < self.config.minimum_event_count:
            warnings.append("即時事件數量低於最低門檻，需避免過度解讀。")
        if single_domain_ratio(events) > self.config.max_single_domain_ratio:
            warnings.append("即時事件來源集中度偏高，需補充獨立來源。")

        manual_event = _manual_event(manual_input, started_at.astimezone(timezone.utc))
        related_events = rank_events(events + [manual_event], self.config.top_event_count)
        assessment_id = f"rapid-{started_at:%Y%m%dT%H%M%S}-{uuid4().hex[:8]}"
        assessment = {
            "assessment_id": assessment_id,
            "created_at": started_at.isoformat(),
            "timezone": self.config.timezone,
            "manual_input": manual_input.to_dict(),
            "market": market.to_dict(),
            "immediate_judgement": _immediate_judgement(market, manual_input, warnings),
            "related_events": [event.to_dict() for event in related_events],
            "warnings": warnings,
            "method": {
                "type": "rule_based",
                "description": "以即時市場快照、公開來源事件與使用者觀察交叉整理；不產生投資建議。",
                "input_handling": "使用者輸入僅作為待驗證的觀察或假設，未附可驗證來源時不會升格為事實。",
            },
            "disclaimer": "本研判僅供研究與風險資訊整理，不構成投資建議。市場資料可能延遲或不完整；相關性不代表因果。",
        }
        artifacts = self._write_artifacts(assessment)
        assessment["artifacts"] = artifacts

        conn = connect(self.config.database_url)
        migrate(conn)
        try:
            MarketRepository(conn).save_many(snapshots_from_bundle(market))
            EventRepository(conn).save_many(events + [manual_event])
            ReportRepository(conn).save_provider_health(market_health + news_health)
            RapidAssessmentRepository(conn).save(assessment)
        finally:
            conn.close()
        return assessment

    def recent_assessments(self) -> list[dict]:
        conn = connect(self.config.database_url)
        migrate(conn)
        try:
            return RapidAssessmentRepository(conn).recent()
        finally:
            conn.close()

    def _write_artifacts(self, assessment: dict) -> dict:
        output_dir = self.config.report_output_dir / "rapid"
        output_dir.mkdir(parents=True, exist_ok=True)
        base = assessment["assessment_id"]
        json_path = output_dir / f"{base}.json"
        html_path = output_dir / f"{base}.html"
        paths = {
            "json_path": str(json_path),
            "html_path": str(html_path),
            "html_url": f"/artifacts/{html_path.name}",
        }
        assessment["artifacts"] = paths
        json_path.write_text(json.dumps(assessment, ensure_ascii=False, indent=2), encoding="utf-8")
        html_path.write_text(render_rapid_html(assessment), encoding="utf-8")
        return paths


def render_rapid_html(assessment: dict) -> str:
    market = assessment["market"]
    judgement = assessment["immediate_judgement"]
    input_data = assessment["manual_input"]
    evidence = "".join(
        f'<li><a href="{html.escape(url, quote=True)}">{html.escape(url)}</a></li>' for url in input_data["source_urls"]
    ) or "<li>未提供外部來源；此觀察以推論處理。</li>"
    event_rows = "".join(
        "<tr>"
        f"<td>{html.escape(event['title'])}</td>"
        f"<td>{html.escape(event['classification'])}</td>"
        f"<td>{event['confidence']:.2f}</td>"
        f"<td><a href=\"{html.escape(event['source_url'], quote=True)}\">{html.escape(event['source_name'])}</a></td>"
        "</tr>"
        for event in assessment["related_events"]
    )
    return f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><title>{html.escape(input_data['title'])}</title>
<style>body{{font-family:"Microsoft JhengHei",Arial,sans-serif;margin:32px;color:#18232d;line-height:1.6}}h1,h2{{color:#0f5a4f}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #d8e0e5;padding:8px;text-align:left}}th{{background:#eef6f3}}.box{{padding:16px;background:#f7faf9;border-left:4px solid #0f8b78}}.warn{{padding:16px;background:#fff8df;border-left:4px solid #c58917}}</style>
</head><body><h1>Crypto Intelligence 即時研判</h1><p>{html.escape(assessment['created_at'])}｜{html.escape(assessment['timezone'])}</p>
<h2>手動觀察</h2><div class="box"><strong>{html.escape(input_data['title'])}</strong><p>{html.escape(input_data['observation'])}</p><p>方向：{html.escape(input_data['stated_direction'])}｜緊急程度：{html.escape(input_data['urgency'])}</p><ul>{evidence}</ul></div>
<h2>即時判斷</h2><div class="box"><p>{html.escape(judgement['summary'])}</p><p>信心：{judgement['confidence']:.2f}｜分類：{html.escape(judgement['classification'])}</p><p>不確定性：{html.escape(judgement['uncertainty'])}</p></div>
<h2>市場快照</h2><ul><li>BTC/USD：{_market_value(market.get('btc_usd'))}</li><li>USDT/USD：{_market_value(market.get('usdt_usd'))}</li><li>BTC Dominance：{market.get('btc_dominance')}</li><li>USDT depeg：{market.get('usdt_depeg')}</li></ul>
<h2>關聯情報</h2><table><tr><th>標題</th><th>分類</th><th>可信度</th><th>來源</th></tr>{event_rows}</table>
<h2>風險與限制</h2><div class="warn"><ul>{''.join(f'<li>{html.escape(item)}</li>' for item in assessment['warnings']) or '<li>目前無額外系統警示。</li>'}</ul></div><p>{html.escape(assessment['disclaimer'])}</p></body></html>"""


def _manual_event(data: ManualAssessmentInput, event_time: datetime) -> NewsEvent:
    has_sources = bool(data.source_urls)
    evidence = data.source_urls or ["使用者輸入；尚待外部來源驗證。"]
    return NewsEvent(
        title=data.title,
        summary=data.observation,
        event_time=event_time,
        source_name="manual-workbench",
        source_url=data.source_urls[0] if has_sources else "manual://observation",
        affected_assets=["BTC", "USDT"],
        impact_direction=data.stated_direction,
        short_term_impact="需對照即時價格、成交量與獨立來源後再確認。",
        medium_term_impact="僅在事件持續並獲得多來源驗證後，才適合納入中期情境。",
        confidence=0.70 if has_sources else 0.35,
        classification=EventClassification.INFERENCE,
        evidence=evidence,
        topic="Market",
        importance=0.5,
        quality_score=70 if has_sources else 35,
    )


def _immediate_judgement(market: MarketBundle, data: ManualAssessmentInput, warnings: list[str]) -> dict:
    facts: list[str] = []
    if market.btc_usd:
        change = market.btc_usd.change_24h_pct
        change_text = "資料未提供" if change is None else f"{change:+.2f}%"
        facts.append(f"BTC/USD 為 {market.btc_usd.price:,.2f}，24 小時變動 {change_text}。")
    if market.usdt_usd:
        facts.append(f"USDT/USD 為 {market.usdt_usd.price:.4f}，偏離 1 美元 {market.usdt_depeg or 0:.4f}。")
    if data.stated_direction == ImpactDirection.BEARISH:
        stance = "使用者觀察偏向利空；目前應優先確認流動性、穩定幣偏離與事件是否有官方佐證。"
    elif data.stated_direction == ImpactDirection.BULLISH:
        stance = "使用者觀察偏向利多；仍需確認是否伴隨成交量與獨立來源支持，避免把短期反應視為趨勢。"
    else:
        stance = "目前方向尚不明確；先將此情境視為待驗證假設，持續追蹤價格、流動性與官方更新。"
    if data.urgency == "critical":
        stance += " 此情境標記為最高緊急程度，應縮短下一次資料複查間隔。"
    uncertainty = "；".join(warnings) if warnings else "單次快照與公開事件不足以證明因果或持續性。"
    confidence = 0.55 if data.source_urls and not warnings else 0.40
    return {
        "summary": " ".join(facts + [stance]),
        "classification": "inference",
        "confidence": confidence,
        "evidence": facts + data.source_urls,
        "uncertainty": uncertainty,
        "follow_up": [
            "追蹤 BTC 24 小時價格與成交量是否同向變化。",
            "確認 USDT/USD 偏離是否擴大，並補充第二個獨立市場來源。",
            "檢查關鍵事件是否出現官方公告或可信媒體的交叉驗證。",
        ],
    }


def _required_text(value: object, field: str, maximum: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if not text:
        raise ValueError(f"{field}不可空白。")
    if len(text) > maximum:
        raise ValueError(f"{field}不可超過 {maximum} 個字元。")
    return text


def _validate_source_urls(value: object) -> list[str]:
    if isinstance(value, str):
        candidates = value.splitlines()
    elif isinstance(value, list):
        candidates = value
    else:
        candidates = []
    urls: list[str] = []
    for candidate in candidates:
        url = str(candidate).strip()
        if not url:
            continue
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("來源連結僅接受完整的 http 或 https 網址。")
        if url not in urls:
            urls.append(url)
    if len(urls) > MAX_SOURCE_URLS:
        raise ValueError(f"最多可加入 {MAX_SOURCE_URLS} 個來源連結。")
    return urls


def _market_value(snapshot: dict | None) -> str:
    if not snapshot:
        return "N/A"
    return f"{snapshot['price']:,.4f} {snapshot['quote_currency']}"
