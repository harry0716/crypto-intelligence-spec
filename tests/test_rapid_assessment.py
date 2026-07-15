from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
TEST_TMP = ROOT / ".test_tmp"
TEST_TMP.mkdir(exist_ok=True)

from crypto_intel.config import AppConfig
from crypto_intel.providers.market.static import StaticMarketProvider
from crypto_intel.providers.news.static import StaticNewsProvider
from crypto_intel.services.rapid_assessment import ManualAssessmentInput, RapidAssessmentService
from crypto_intel.web import create_server


class FakeCollectionService:
    def __init__(self, *args: object, **kwargs: object) -> None:
        pass

    def collect_market(self):
        return StaticMarketProvider().fetch_market_bundle(), []

    def collect_events(self, limit: int):
        return StaticNewsProvider().fetch_events()[:limit], []


class RapidAssessmentTests(unittest.TestCase):
    def test_manual_input_rejects_invalid_url(self) -> None:
        with self.assertRaisesRegex(ValueError, "http 或 https"):
            ManualAssessmentInput.from_payload(
                {
                    "title": "異常訊號",
                    "observation": "觀察到價格與流動性異常。",
                    "source_urls": ["file:///secret"],
                }
            )

    def test_assessment_creates_traceable_artifacts_and_history(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            root = Path(tmp)
            config = AppConfig(
                database_url=f"sqlite:///{root / 'data' / 'rapid.db'}",
                report_output_dir=root / "artifacts",
            )
            input_data = ManualAssessmentInput.from_payload(
                {
                    "title": "交易所提領異常 <待確認>",
                    "observation": "社群出現提領延遲，尚待官方公告確認。",
                    "stated_direction": "bearish",
                    "urgency": "critical",
                    "source_urls": ["https://example.com/status"],
                }
            )
            with patch("crypto_intel.services.rapid_assessment.CollectionService", FakeCollectionService):
                service = RapidAssessmentService(config)
                result = service.assess(input_data)
                history = service.recent_assessments()

            self.assertEqual(result["immediate_judgement"]["classification"], "inference")
            self.assertTrue(Path(result["artifacts"]["json_path"]).is_file())
            self.assertTrue(Path(result["artifacts"]["html_path"]).is_file())
            html = Path(result["artifacts"]["html_path"]).read_text(encoding="utf-8")
            self.assertIn("&lt;待確認&gt;", html)
            payload = json.loads(Path(result["artifacts"]["json_path"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["manual_input"]["urgency"], "critical")
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["html_url"], result["artifacts"]["html_url"])

    def test_workbench_homepage_is_available_locally(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            root = Path(tmp)
            config = AppConfig(
                database_url=f"sqlite:///{root / 'data' / 'rapid.db'}",
                report_output_dir=root / "artifacts",
            )
            server = create_server(config, port=0)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                connection = HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
                connection.request("GET", "/")
                response = connection.getresponse()
                body = response.read().decode("utf-8")
                self.assertEqual(response.status, 200)
                self.assertIn("即時工作台", body)
                connection.request("GET", "/artifacts/not-a-report.html")
                forbidden = connection.getresponse()
                forbidden.read()
                self.assertEqual(forbidden.status, 404)
            finally:
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    unittest.main()
