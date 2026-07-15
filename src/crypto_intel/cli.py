from __future__ import annotations

import argparse
from datetime import datetime

from crypto_intel.config import load_config
from crypto_intel.infrastructure.database import connect, migrate
from crypto_intel.infrastructure.logging import configure_logging
from crypto_intel.infrastructure.time import resolve_timezone
from crypto_intel.providers.market.coingecko import CoinGeckoMarketProvider
from crypto_intel.providers.market.static import StaticMarketProvider
from crypto_intel.providers.news.rss import RssNewsProvider
from crypto_intel.repositories.event_repository import EventRepository
from crypto_intel.repositories.market_repository import MarketRepository
from crypto_intel.repositories.report_repository import ReportRepository
from crypto_intel.services.analytics import snapshots_from_bundle
from crypto_intel.services.collection import CollectionService
from crypto_intel.services.deep_analysis import should_run_deep_analysis
from crypto_intel.services.delivery import DeliveryService
from crypto_intel.services.quality import market_warnings, single_domain_ratio, source_diversity
from crypto_intel.services.report import ReportService
from crypto_intel.web import run_server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="crypto-intel")
    sub = parser.add_subparsers(dest="command", required=True)
    daily = sub.add_parser("daily-report")
    daily.add_argument("--date", help="Report date in YYYY-MM-DD.")
    daily.add_argument("--timezone", default=None)
    daily.add_argument("--dry-run", action="store_true")
    daily.add_argument("--no-email", action="store_true")
    daily.add_argument("--deep-analysis", action="store_true")
    daily.add_argument("--config", default="config/default.yaml")
    serve = sub.add_parser("serve", help="Start the local real-time intelligence workbench.")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", default=8765, type=int)
    serve.add_argument("--config", default="config/default.yaml")
    args = parser.parse_args(argv)
    if args.command == "daily-report":
        return run_daily_report(args)
    if args.command == "serve":
        config = load_config(args.config)
        run_server(config, args.host, args.port)
        return 0
    return 2


def run_daily_report(args: argparse.Namespace) -> int:
    configure_logging()
    config = load_config(args.config)
    timezone = args.timezone or config.timezone
    today = args.date or datetime.now(resolve_timezone(timezone)).date().isoformat()
    dry_run = args.dry_run or config.dry_run

    conn = connect(config.database_url)
    migrate(conn)
    try:
        market_repo = MarketRepository(conn)
        event_repo = EventRepository(conn)
        report_repo = ReportRepository(conn)

        collector = CollectionService(
            market_provider=CoinGeckoMarketProvider(),
            fallback_market_provider=StaticMarketProvider(),
            news_providers=[RssNewsProvider()],
        )
        market, market_health = collector.collect_market()
        events, news_health = collector.collect_events(
            config.top_event_count,
            max_event_age_hours=config.max_event_age_hours,
            max_per_source=config.max_events_per_source,
        )
        warnings = market_warnings(market)
        if len(events) < config.minimum_event_count:
            warnings.append("Top 10 可用事件少於最低門檻。")
        if single_domain_ratio(events) > config.max_single_domain_ratio:
            warnings.append("新聞來源集中度過高，需留意單一來源偏誤。")
        diversity = source_diversity(events)
        if diversity["independent_sources"] < config.minimum_independent_sources:
            warnings.append(
                f"可用情報僅涵蓋 {diversity['independent_sources']} 個獨立來源，今日事件解讀需保守。"
            )

        report_repo.save_provider_health(market_health + news_health)
        market_repo.save_many(snapshots_from_bundle(market))
        event_repo.save_many(events)

        last_deep = report_repo.last_deep_analysis_date()
        deep_analysis = args.deep_analysis or should_run_deep_analysis(
            datetime.fromisoformat(today).date(),
            last_deep,
            config.deep_analysis_interval_days,
        )
        _, metadata = ReportService(config).compose(today, market, events, deep_analysis, dry_run, warnings)
        report_repo.save_report(metadata)
        DeliveryService(config, report_repo).deliver(metadata, no_email=args.no_email)
    finally:
        conn.close()

    print(f"HTML: {metadata.html_path}")
    print(f"PDF: {metadata.pdf_path}")
    print(f"JSON: {metadata.json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
