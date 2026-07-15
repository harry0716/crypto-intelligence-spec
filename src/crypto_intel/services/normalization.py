from __future__ import annotations


ALIASES = {
    "bitcoin": "BTC",
    "xbt": "BTC",
    "btc": "BTC",
    "tether": "USDT",
    "usdt": "USDT",
}


def normalize_symbol(value: str) -> str:
    key = value.strip().lower()
    return ALIASES.get(key, value.strip().upper())

