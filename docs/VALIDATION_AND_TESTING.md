# 驗證與測試

## 1. P0 驗收

### 市場資料

- BTC/USD 可取得
- USDT/USD 可取得
- 24h 與 7d 漲跌計算正確
- USDT depeg = abs(price - 1)
- 所有資料具來源與時間戳
- BTC/TWD 若為推算，需標示 inferred=true

### 新聞

- 至少取得 10 筆候選事件
- 去重複後可排序
- 每筆有來源 URL
- 事件分類可解析
- 可信度在合法範圍
- 事件時效符合設定門檻
- 單一來源不超過設定入選數；來源不足時顯示品質警示

### 報告

- HTML 可開啟
- PDF 可開啟
- 繁體中文不亂碼
- PDF 有日期、時區、來源與免責聲明
- 檔名正確
- 初學者版主說明使用繁體中文，原文標題與來源 URL 可追溯

### 寄信

- dry-run 不寄信
- 正式模式附件存在
- Gmail 失敗時有明確 log
- 不在 log 顯示 token

### GitHub Actions

- workflow_dispatch 可執行
- schedule 可執行
- artifact 可下載
- 失敗時 job 為 failed

### 即時情報工作台

- 本機首頁可開啟，且不需外部 SaaS 或帳號
- 無標題、無觀察、過長文字與不合法 URL 必須被拒絕
- 成功研判會產生 HTML/JSON，並寫入 `rapid_assessments`
- 使用者輸入必須在產物中維持 `inference`，不得升格為 `fact`
- 產物頁只能開啟工作台產生的檔案，不得藉由路徑讀取任意檔案
- 每日 `daily-report` dry-run 流程仍可正常產出既有三種報告格式

## 2. 單元測試

至少涵蓋：

- normalize symbol
- timezone conversion
- return calculation
- volatility calculation
- USDT depeg
- exchange spread
- deduplication
- ranking
- three-day trigger
- filename generation

## 3. 整合測試

- provider → normalization → database
- database → analytics → report
- report → PDF
- report → email dry-run

## 4. 故障注入

模擬：

- HTTP 429
- HTTP 500
- timeout
- malformed JSON
- missing field
- duplicate article
- PDF engine failure
- Gmail failure
- partial provider outage

## 5. Golden Report

建立固定 fixture，產出 golden HTML/PDF metadata，避免版型與欄位意外退化。

## 6. 資料合理性檢查

- USDT/USD 若偏離 1 超過 5%，標記 critical
- BTC 價格 <= 0 視為 invalid
- 24h 成交量 < 0 視為 invalid
- 同一 provider 時間倒退視為 anomaly
- 價格跳變超過設定門檻時需第二來源驗證
