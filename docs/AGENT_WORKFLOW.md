# Codex 子代理與工作流程

本專案適合使用多代理，但主代理必須掌握整體一致性。

## 1. 主代理

責任：

- 讀取全部規格
- 建立 implementation plan
- 切分子任務
- 控制介面一致性
- 合併程式碼
- 執行完整測試
- 判斷是否符合驗收

## 2. 建議子代理

### Agent A — Data Providers

負責：

- 市場 provider
- 新聞 provider
- 監管來源
- retry、rate limit、cache
- provider contract tests

### Agent B — Data Model and Storage

負責：

- Pydantic models
- SQLite schema
- migration
- repositories
- data provenance

### Agent C — Analytics

負責：

- 市場指標
- 波動率
- 價差
- USDT depeg
- correlation
- lag analysis
- divergence detection

### Agent D — Intelligence and Ranking

負責：

- 去重複
- 事件分類
- Top 10 scoring
- 可信度
- 事實／推論／傳聞區分
- prompt injection 防護

### Agent E — Reporting

負責：

- Jinja2 HTML
- PDF
- 字型
- 圖表
- email summary
- accessibility

### Agent F — DevOps and Security

負責：

- GitHub Actions
- Docker
- secrets
- Gmail
- artifact upload
- dependency scanning
- logging

### Agent G — QA

負責：

- unit tests
- integration tests
- golden report
- failure simulation
- acceptance checklist

## 3. 合併規則

- 所有 agent 使用已定義的 domain model
- 不得私自改 public interface
- 介面變更需由主代理統一
- 每個 PR 或 patch 必須包含測試
- 不得以 mock 通過掩蓋真實 integration failure

## 4. Codex 每階段自我回報格式

```text
完成項目：
變更檔案：
測試結果：
已知限制：
風險：
下一步：
```
