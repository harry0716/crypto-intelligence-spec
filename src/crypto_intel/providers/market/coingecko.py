from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import Request, urlopen

from crypto_intel.domain.enums import ProviderStatus
from crypto_intel.domain.models import MarketBundle, MarketSnapshot


class CoinGeckoMarketProvider:
    name = "coingecko"
    source_url = "https://api.coingecko.com/api/v3/coins/markets"
    global_url = "https://api.coingecko.com/api/v3/global"

    def fetch_market_bundle(self) -> MarketBundle:
        warnings: list[str] = []
        try:
            usd = self._fetch_markets("usd")
            twd = self._fetch_markets("twd")
            global_data = self._fetch_json(self.global_url)
        except (OSError, URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError) as exc:
            return MarketBundle(None, None, None, None, None, ProviderStatus.FAILED, [str(exc)])

        observed_at = datetime.now(timezone.utc)
        btc_usd_raw = usd["bitcoin"]
        usdt_usd_raw = usd["tether"]
        btc_twd_raw = twd.get("bitcoin")

        btc_usd = self._snapshot("BTC", "USD", btc_usd_raw, observed_at, usd)
        usdt_usd = self._snapshot("USDT", "USD", usdt_usd_raw, observed_at, usd)
        if btc_twd_raw:
            btc_twd = self._snapshot("BTC", "TWD", btc_twd_raw, observed_at, twd)
        else:
            btc_twd = None
            warnings.append("BTC/TWD missing from provider.")

        btc_dominance = (
            global_data.get("data", {})
            .get("market_cap_percentage", {})
            .get("btc")
        )
        usdt_depeg = abs(usdt_usd.price - 1.0) if usdt_usd else None
        return MarketBundle(
            btc_usd=btc_usd,
            btc_twd=btc_twd,
            usdt_usd=usdt_usd,
            btc_dominance=btc_dominance,
            usdt_depeg=usdt_depeg,
            provider_status=ProviderStatus.SUCCESS,
            warnings=warnings,
        )

    def _fetch_markets(self, currency: str) -> dict[str, dict]:
        url = (
            f"{self.source_url}?vs_currency={currency}&ids=bitcoin,tether"
            "&price_change_percentage=24h,7d"
        )
        rows = self._fetch_json(url)
        return {row["id"]: row for row in rows}

    def _fetch_json(self, url: str) -> dict | list:
        req = Request(url, headers={"User-Agent": "crypto-intelligence-daily/0.1"})
        with urlopen(req, timeout=20) as response:  # noqa: S310 - fixed public HTTPS endpoints.
            return json.loads(response.read().decode("utf-8"))

    def _snapshot(
        self,
        symbol: str,
        quote_currency: str,
        row: dict,
        observed_at: datetime,
        raw: dict,
    ) -> MarketSnapshot:
        return MarketSnapshot(
            symbol=symbol,
            quote_currency=quote_currency,
            price=float(row["current_price"]),
            market_cap=_optional_float(row.get("market_cap")),
            volume_24h=_optional_float(row.get("total_volume")),
            change_24h_pct=_optional_float(row.get("price_change_percentage_24h_in_currency")),
            change_7d_pct=_optional_float(row.get("price_change_percentage_7d_in_currency")),
            observed_at=observed_at,
            provider=self.name,
            source_url=self.source_url,
            raw=raw,
        )


def _optional_float(value: object) -> float | None:
    return None if value is None else float(value)

