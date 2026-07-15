from __future__ import annotations

import sys
import tempfile
import unittest
from dataclasses import replace
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
TEST_TMP = Path(tempfile.gettempdir()) / "crypto-intel-tests"
TEST_TMP.mkdir(exist_ok=True)

from crypto_intel.config import load_config
from crypto_intel.providers.news.static import StaticNewsProvider
from crypto_intel.services.analytics import exchange_spread_pct, return_pct, usdt_depeg
from crypto_intel.services.deduplication import deduplicate_events
from crypto_intel.services.deep_analysis import should_run_deep_analysis
from crypto_intel.services.normalization import normalize_symbol
from crypto_intel.services.ranking import rank_events, select_diverse_events
from crypto_intel.services.source_governance import event_governance, govern_event


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
        unique = deduplicate_events(events + [events[0]])
        self.assertEqual(len(unique), len(events))
        ranked = rank_events(unique, 5)
        self.assertEqual(len(ranked), 5)
        self.assertGreaterEqual(ranked[0].importance, ranked[-1].importance)

    def test_source_diversity_cap_prevents_one_domain_from_filling_report(self) -> None:
        events = StaticNewsProvider().fetch_events()
        diversified = [
            replace(event, source_url="https://one.example/news" if index < 6 else f"https://source-{index}.example/news")
            for index, event in enumerate(events)
        ]
        selected = select_diverse_events(diversified, limit=6, max_per_source=2)
        self.assertLessEqual(sum("one.example" in event.source_url for event in selected), 2)

    def test_three_day_trigger(self) -> None:
        self.assertFalse(should_run_deep_analysis(date(2026, 7, 15), None))
        self.assertFalse(should_run_deep_analysis(date(2026, 7, 15), date(2026, 7, 13)))
        self.assertTrue(should_run_deep_analysis(date(2026, 7, 15), date(2026, 7, 12)))

    def test_config_loader_handles_simple_lists(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            path = Path(tmp) / "config.yaml"
            path.write_text("app:\n  timezone: Asia/Taipei\nreport:\n  output_formats:\n    - html\n    - pdf\n", encoding="utf-8")
            self.assertEqual(load_config(path).raw["report"]["output_formats"], ["html", "pdf"])

    def test_media_source_requires_confirmation_and_official_source_is_primary(self) -> None:
        event = StaticNewsProvider().fetch_events()[0]
        media = govern_event(replace(event, source_url="https://www.coindesk.com/example"))
        official = govern_event(replace(event, source_url="https://www.sec.gov/news/example"))
        self.assertTrue(event_governance(media)["requires_confirmation"])
        self.assertEqual(event_governance(official)["verification_status"], "primary_source")
        self.assertGreater(official.quality_score, media.quality_score)


if __name__ == "__main__":
    unittest.main()
