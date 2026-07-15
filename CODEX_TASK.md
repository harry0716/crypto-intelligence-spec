# Codex 主任務指令

你要在本儲存庫中實作「Crypto Intelligence Daily」。

## 執行原則

- 先閱讀 `docs/` 內所有文件。
- 先建立工作分解與實作順序，再開始撰寫程式。
- 每個階段完成後，執行測試與自我診斷。
- 不得將 API Key、OAuth Token、Gmail 憑證或個資寫入程式碼或 Git 歷史。
- 所有外部資料都必須保存來源、時間戳、原始值與正規化值。
- 所有新聞與政策資料都必須能追溯至來源 URL。
- 所有 AI 產生的判斷必須標示可信度、證據與不確定性。
- 不得把價格相關性直接描述為因果。
- 報告預設使用繁體中文與 Asia/Taipei 時區。

## 實作階段

### Phase 0 — Repository bootstrap

建立：

- Python 3.12 專案
- `src/crypto_intel/`
- `tests/`
- `config/`
- `data/`
- `artifacts/`
- `.github/workflows/`
- `pyproject.toml`
- `.env.example`
- `Makefile`
- `Dockerfile`

### Phase 1 — 市場資料 MVP

至少完成：

- BTC/USD
- BTC/TWD
- USDT/USD
- 24 小時與 7 日漲跌
- 成交量
- 市值
- BTC dominance
- USDT depeg deviation
- 資料截點
- SQLite 保存

優先使用免費、無需 API Key 的官方或公開 API；每個 provider 必須經 adapter abstraction 封裝。

### Phase 2 — 新聞與政策事件

完成：

- RSS 或公開官方來源擷取
- 去重複
- 可信度分級
- 主題分類
- 事件重要性排序
- 每日 Top 10

### Phase 3 — 報告產生

完成：

- HTML 報告
- PDF 報告
- 繁體中文字型
- 圖表
- 來源附註
- 免責聲明

### Phase 4 — Gmail 與 GitHub Actions

完成：

- Gmail OAuth 或 SMTP 寄送介面
- GitHub Actions 每日執行
- workflow_dispatch 手動觸發
- artifacts 上傳
- 失敗通知
- dry-run

### Phase 5 — 三日深度分析

完成：

- 最近 3 日比較
- 報酬率與波動
- 成交量變化
- 新聞情緒
- 政策事件
- 時間領先/落後分析
- 共振與背離
- 假說與後續驗證指標

### Phase 6 — 可觀測性與韌性

完成：

- structured logging
- retry/backoff
- cache
- provider health
- partial failure
- report metadata
- data quality score

## 驗收條件

所有 `docs/VALIDATION_AND_TESTING.md` 定義的 P0 驗證必須通過，才可宣告 MVP 完成。
