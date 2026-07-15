from __future__ import annotations

import sys
import tempfile
import unittest
from dataclasses import replace
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
TEST_TMP = ROOT / ".test_tmp"
TEST_TMP.mkdir(exist_ok=True)

from crypto_intel.config import load_config
from crypto_intel.providers.news.static import StaticNewsProvider
from crypto_intel.services.ranking import select_diverse_events
from crypto_intel.services.analytics import exchange_spread_pct, return_pct, usdt_depeg
from crypto_intel.services.deduplication import deduplicate_events
from crypto_intel.services.deep_analysis import should_run_deep_analysis
from crypto_intel.services.normalization import normalize_symbol
from crypto_intel.services.ranking import rank_events


class CoreServiceTests(unittest.TestCase):
    def test_normalize_symbol(self) -> None:
        self.assertEqual(normalize_symbol("bitcoin"), "BTC")
        self.assertEqual(normalize_symbol(" usdt "), "USDT")

    def test_market_math(self) -> None:
        self.assertAlmostEqual(return_pct(110, 100), 10.0)
        self.assertAlmostEqual(usdt_depeg(0.998), 0.002)
        self.assertAlmostEqual(exchange_spread_pct([100, 105]), 5.0)

    def test_deduplicate_and_rank(self) -> None:
        events = StaticNewsProvider().fetch_events()
        duplicated = events + [events[0]]
        unique = deduplicate_events(duplicated)
        self.assertEqual(len(unique), len(events))
        ranked = rank_events(unique, 5)
        self.assertEqual(len(ranked), 5)
        self.assertGreaterEqual(ranked[0].importance, ranked[-1].importance)

    def test_source_diversity_cap_prevents_one_domain_from_filling_report(self) -> None:
        events = StaticNewsProvider().fetch_events()
        diversified = []
        for index, event in enumerate(events):
            source = "https://one.example/news" if index < 6 else f"https://source-{index}.example/news"
            diversified.append(replace(event, source_url=source, source_name=source))
        selected = select_diverse_events(diversified, limit=6, max_per_source=2)
        one_source_count = sum("one.example" in event.source_url for event in selected)
        self.assertEqual(len(selected), 6)
        self.assertLessEqual(one_source_count, 2)

    def test_three_day_trigger(self) -> None:
        self.assertFalse(should_run_deep_analysis(date(2026, 7, 15), None))
        self.assertFalse(should_run_deep_analysis(date(2026, 7, 15), date(2026, 7, 13)))
        self.assertTrue(should_run_deep_analysis(date(2026, 7, 15), date(2026, 7, 12)))

    def test_config_loader_handles_simple_lists(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            path = Path(tmp) / "config.yaml"
            path.write_text(
                "app:\n  timezone: Asia/Taipei\nreport:\n  output_formats:\n    - html\n    - pdf\n",
                encoding="utf-8",
            )
            config = load_config(path)
            self.assertEqual(config.timezone, "Asia/Taipei")
            self.assertEqual(config.raw["report"]["output_formats"], ["html", "pdf"])


if __name__ == "__main__":
    unittest.main()
