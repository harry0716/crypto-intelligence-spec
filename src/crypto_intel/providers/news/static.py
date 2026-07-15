from __future__ import annotations

from datetime import datetime, timedelta, timezone

from crypto_intel.domain.enums import EventClassification, ImpactDirection
from crypto_intel.domain.models import NewsEvent


class StaticNewsProvider:
    name = "static-news-fixture"

    def fetch_events(self) -> list[NewsEvent]:
        now = datetime.now(timezone.utc)
        rows = [
            ("Bitcoin ETF flow remains a key market signal", "ETF fund flow is monitored as a liquidity proxy.", "ETF"),
            ("Stablecoin peg monitoring shows mild USDT deviation", "USDT trades close to one dollar with low deviation.", "Stablecoin"),
            ("Exchange reserve transparency remains in focus", "Market participants continue to track proof-of-reserves updates.", "Exchange"),
            ("Regulators publish digital asset consultation calendar", "Upcoming consultation windows may affect compliance planning.", "Regulation"),
            ("DeFi risk teams flag bridge security posture", "Bridge controls and incident response remain high-priority risk areas.", "Security"),
            ("Tokenized treasury products continue to draw attention", "RWA products are being watched for capital rotation signals.", "RWA"),
            ("Mining difficulty and hash rate trend are steady", "Network security indicators remain part of BTC structure monitoring.", "BTC"),
            ("Options market watches BTC volatility term structure", "Derivatives pricing may reflect changing hedging demand.", "Derivatives"),
            ("Public repositories show wallet tooling activity", "Developer activity can be a weak but useful ecosystem signal.", "GitHub"),
            ("Macro calendar may affect crypto liquidity", "Rates and dollar liquidity remain relevant cross-asset inputs.", "Macro"),
        ]
        events: list[NewsEvent] = []
        for index, (title, summary, topic) in enumerate(rows):
            events.append(
                NewsEvent(
                    title=title,
                    summary=summary,
                    event_time=now - timedelta(hours=index + 1),
                    source_name=self.name,
                    source_url=f"fixture://news/{index + 1}",
                    affected_assets=["BTC", "USDT"] if index < 2 else ["BTC"],
                    impact_direction=ImpactDirection.NEUTRAL,
                    short_term_impact="需觀察後續價格、成交量與官方資料交叉驗證。",
                    medium_term_impact="若趨勢延續，可能影響市場風險偏好與資金配置。",
                    confidence=0.60,
                    classification=EventClassification.INFERENCE,
                    evidence=[summary],
                    topic=topic,
                    importance=0.5,
                    quality_score=70,
                )
            )
        return events

