from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
TEST_TMP = ROOT / ".test_tmp"
TEST_TMP.mkdir(exist_ok=True)

from crypto_intel.cli import main
from crypto_intel.config import AppConfig
from crypto_intel.providers.market.static import StaticMarketProvider
from crypto_intel.providers.news.static import StaticNewsProvider
from crypto_intel.services.report import ReportService


class DailyReportTests(unittest.TestCase):
    def test_daily_report_dry_run_creates_artifacts(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            root = Path(tmp)
            config_dir = root / "config"
            config_dir.mkdir()
            config_path = config_dir / "default.yaml"
            config_path.write_text(
                """
app:
  timezone: Asia/Taipei
  language: zh-TW
report:
  top_event_count: 10
  deep_analysis_interval_days: 3
quality:
  minimum_event_count: 5
  max_single_domain_ratio: 0.90
delivery:
  email_enabled: false
""".strip(),
                encoding="utf-8",
            )
            old_cwd = Path.cwd()
            old_env = os.environ.copy()
            try:
                os.chdir(root)
                os.environ["DATABASE_URL"] = "sqlite:///data/test.db"
                os.environ["REPORT_OUTPUT_DIR"] = "artifacts"
                os.environ["DRY_RUN"] = "true"
                shutil.copytree(ROOT / "src", root / "src")
                sys.path.insert(0, str(root / "src"))
                code = main(
                    [
                        "daily-report",
                        "--date",
                        "2026-07-15",
                        "--dry-run",
                        "--no-email",
                        "--config",
                        str(config_path),
                    ]
                )
            finally:
                os.chdir(old_cwd)
                os.environ.clear()
                os.environ.update(old_env)
            self.assertEqual(code, 0)
            self.assertTrue((root / "artifacts" / "Crypto_Market_Intelligence_2026-07-15.html").exists())
            self.assertTrue((root / "artifacts" / "Crypto_Market_Intelligence_2026-07-15.json").exists())
            self.assertTrue((root / "artifacts" / "Crypto_Market_Intelligence_2026-07-15.pdf").exists())
            self.assertTrue((root / "data" / "test.db").exists())

    def test_beginner_report_uses_chinese_guidance_and_preserves_original_title(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            root = Path(tmp)
            event = StaticNewsProvider().fetch_events()[0]
            config = AppConfig(report_output_dir=root / "artifacts")
            payload, metadata = ReportService(config).compose(
                "2026-07-15",
                StaticMarketProvider().fetch_market_bundle(),
                [event],
                deep_analysis=False,
                dry_run=True,
                warnings=["測試用資料品質提醒。"],
            )
            html = Path(metadata.html_path).read_text(encoding="utf-8")
            self.assertIn("先看這裡：今天的三個重點", html)
            self.assertIn("中文導讀", html)
            self.assertIn(event.title, html)
            self.assertEqual(payload["data_quality"]["source_diversity"]["independent_sources"], 1)


if __name__ == "__main__":
    unittest.main()
