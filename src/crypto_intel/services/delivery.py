from __future__ import annotations

from crypto_intel.config import AppConfig
from crypto_intel.domain.models import ReportMetadata
from crypto_intel.repositories.report_repository import ReportRepository


class DeliveryService:
    def __init__(self, config: AppConfig, repository: ReportRepository) -> None:
        self.config = config
        self.repository = repository

    def deliver(self, metadata: ReportMetadata, no_email: bool) -> dict[str, str]:
        results: dict[str, str] = {}
        if metadata.dry_run or no_email or not self.config.email_enabled:
            message = "dry-run/no-email: Gmail delivery skipped."
            self.repository.log_delivery(metadata.report_date, "gmail", "skipped", metadata.dry_run, message)
            results["gmail"] = "skipped"
        else:
            message = "Gmail delivery interface is not configured in MVP."
            self.repository.log_delivery(metadata.report_date, "gmail", "failed", metadata.dry_run, message)
            results["gmail"] = "failed"
        self.repository.log_delivery(
            metadata.report_date,
            "artifact",
            "ready",
            metadata.dry_run,
            f"Artifacts written to {metadata.html_path}",
        )
        results["artifact"] = "ready"
        return results

