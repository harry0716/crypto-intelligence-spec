# 系統架構

## 1. 邏輯架構

```text
Scheduler
   |
   v
Collectors
   |-- Market Providers
   |-- News Providers
   |-- Regulatory Providers
   |-- Social Providers
   v
Normalization
   v
Data Quality + Deduplication
   v
Storage
   |-- SQLite
   |-- Raw JSON cache
   v
Analytics
   |-- Market Metrics
   |-- Event Scoring
   |-- Sentiment
   |-- Correlation/Lag
   v
Report Composer
   |-- HTML
   |-- PDF
   v
Delivery
   |-- Gmail
   |-- GitHub Artifact
   |-- Optional Google Drive

Manual Workbench (localhost)
   |
   v
Rapid Assessment Service
   |-- validates manual observation and source URLs
   |-- reuses Market and News Providers
   |-- records evidence, uncertainty and artifacts
   v
SQLite + artifacts/rapid
```

## 2. 建議模組

```text
src/crypto_intel/
  cli.py
  config.py
  domain/
    models.py
    enums.py
  providers/
    base.py
    market/
    news/
    regulatory/
    social/
  services/
    collection.py
    normalization.py
    quality.py
    deduplication.py
    ranking.py
    analytics.py
    deep_analysis.py
    report.py
    delivery.py
    rapid_assessment.py
  repositories/
    market_repository.py
    event_repository.py
    report_repository.py
  infrastructure/
    database.py
    logging.py
    retry.py
    cache.py
  web.py
  templates/
    report.html.j2
    email.html.j2
```

## 3. Provider Adapter

每個 provider 實作統一介面：

```python
class MarketProvider(Protocol):
    name: str

    async def fetch_market_snapshot(self) -> MarketSnapshot:
        ...
```

Provider 回傳的 domain model 必須一致，核心服務不得依賴 provider 專屬欄位。

## 4. 儲存策略

MVP 使用 SQLite。

後續可切換 PostgreSQL，但 repository interface 不變。

資料表至少包含：

- market_snapshots
- exchange_quotes
- stablecoin_metrics
- news_events
- event_sources
- reports
- delivery_logs
- provider_health
- analysis_features
- rapid_assessments

## 6. 即時研判邊界

`web.py` 提供本機工作台，`rapid_assessment.py` 是唯一能把手動輸入送入資料流程的 service。它會把輸入正規化為 `ManualAssessmentInput`，明確標記為推論，並另外保存 `rapid_assessments` 稽核紀錄。每日報告的 CLI 流程不依賴工作台，因此定時工作不會因 GUI 停止而中斷。

## 5. 失敗降級

- 市場主 provider 失效：切換 secondary provider
- BTC/TWD 缺失：使用 BTC/USD × USD/TWD，並標註推算
- 社群來源缺失：報告仍產出，但標示「社群資料不足」
- PDF 失敗：寄送 HTML 並保留錯誤
- Gmail 失敗：上傳 GitHub artifact，workflow 標記失敗
