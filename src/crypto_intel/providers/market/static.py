from __future__ import annotations

from datetime import datetime, timezone

from crypto_intel.domain.enums import ProviderStatus
from crypto_intel.domain.models import MarketBundle, MarketSnapshot


class StaticMarketProvider:
    name = "static-fixture"
    source_url = "fixture://market/static"

    def fetch_market_bundle(self) -> MarketBundle:
        observed_at = datetime.now(timezone.utc)
        btc_usd = MarketSnapshot(
            symbol="BTC",
            quote_currency="USD",
            price=65000.0,
            market_cap=1_280_000_000_000.0,
            volume_24h=32_000_000_000.0,
            change_24h_pct=1.2,
            change_7d_pct=4.8,
            observed_at=observed_at,
            provider=self.name,
            source_url=self.source_url,
            raw={"fixture": True},
        )
        btc_twd = MarketSnapshot(
            symbol="BTC",
            quote_currency="TWD",
            price=2_112_500.0,
            market_cap=None,
            volume_24h=None,
            change_24h_pct=1.2,
            change_7d_pct=4.8,
            observed_at=observed_at,
            provider=self.name,
            source_url=self.source_url,
            raw={"fixture": True, "formula": "BTC/USD * USD/TWD"},
            inferred=True,
        )
        usdt_usd = MarketSnapshot(
            symbol="USDT",
            quote_currency="USD",
            price=1.0004,
            market_cap=112_000_000_000.0,
            volume_24h=51_000_000_000.0,
            change_24h_pct=0.01,
            change_7d_pct=0.02,
            observed_at=observed_at,
            provider=self.name,
            source_url=self.source_url,
            raw={"fixture": True},
        )
        return MarketBundle(
            btc_usd=btc_usd,
            btc_twd=btc_twd,
            usdt_usd=usdt_usd,
            btc_dominance=52.4,
            usdt_depeg=abs(usdt_usd.price - 1.0),
            provider_status=ProviderStatus.DEGRADED,
            warnings=["Using static market fixture because live provider was unavailable."],
        )

