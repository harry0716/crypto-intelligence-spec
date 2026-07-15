# Crypto Intelligence Daily — Codex 開發文件組

本文件組定義一套可部署於 GitHub、由 GitHub Actions 定時執行的「比特幣與 USDT 每日市場情報系統」。

系統目標：

1. 每日收集 BTC、USDT、穩定幣、ETF、DeFi、RWA、監管、交易所、資安與社群資訊。
2. 產出繁體中文 PDF 與 HTML 報告。
3. 透過 Gmail 寄送報告，並可選擇備份到 Google Drive。
4. 每 3 日執行一次深度分析，持續累積歷史特徵。
5. 所有結論必須區分「事實、推論、傳聞」，不得把相關性直接宣稱為因果。
6. 系統必須可擴充、可測試、可觀測、可回溯，並避免被單一資料來源綁定。

## 建議閱讀順序

1. `CODEX_TASK.md`
2. `docs/SYSTEM_SPEC.md`
3. `docs/ARCHITECTURE.md`
4. `docs/DATA_PIPELINE.md`
5. `docs/AGENT_WORKFLOW.md`
6. `docs/VALIDATION_AND_TESTING.md`
7. `docs/SECURITY_AND_COMPLIANCE.md`
8. `docs/DEPLOYMENT.md`
9. `docs/OPTIMIZATION_RULES.md`

## 交付原則

Codex 應先完成 MVP，通過驗證後再擴充。不得一開始就加入過多付費 API、複雜鏈上分析或高成本社群資料抓取。

## 即時情報工作台

除了每日批次報告，系統提供本機 Web GUI，讓使用者在出現突發市場事件、黑天鵝訊號或新假設時進行即時研判。啟動後開啟瀏覽器前往 `http://127.0.0.1:8765`：

```bash
make workbench
```

工作台會收集當下市場資料與公開事件，將使用者觀察視為待驗證推論，輸出即時判斷、佐證、風險與不確定性。每次結果會保存至 `artifacts/rapid/` 與 SQLite；不會寄信、不會下單，也不會產生投資建議。

## 每日報告閱讀方式

每日報告預設為初學者版：先用繁體中文說明市場重點與閱讀限制，再呈現市場數據、事件的中文導讀、學習名詞與後續觀察清單。原文標題、來源名稱與連結會保留，方便直接追溯。系統只會保留 72 小時內的事件，且同一來源最多兩則；資料不足時會明確標示，而不以重複來源或範例內容湊滿。
