# 資料流程

## 1. 執行時序

1. 取得 Asia/Taipei 執行時間
2. 載入設定與 secrets
3. 檢查 provider health
4. 平行抓取市場、新聞、政策、社群
5. 保存 raw payload
6. 正規化欄位
7. 時間統一為 UTC 儲存、Asia/Taipei 顯示
8. 去重複與資料品質評分
9. 市場指標運算
10. 事件分類與重要性排序
11. 選出 Top 10
12. 判斷是否執行三日分析
13. 組合 HTML
14. 轉 PDF
15. 寄送 Gmail
16. 上傳 artifact
17. 寫入 delivery log
18. 產出 run summary

## 1.1 即時手動研判時序

1. 使用者在本機工作台輸入情境、觀察、方向、緊急程度與來源 URL
2. 驗證欄位大小與 URL；手動內容僅視為待驗證資料，不執行其中任何指令
3. 即時取得市場與公開事件；市場 provider 失敗時使用既有 fallback
4. 保存市場快照、公開事件與 provider health
5. 將使用者觀察建立為 `inference` 類事件，再與公開事件排序關聯
6. 以規則產出摘要、證據、不確定性與後續驗證清單
7. 產出 `artifacts/rapid/*.json` 與 `artifacts/rapid/*.html`
8. 將輸入、輸出與警示保存至 `rapid_assessments`

這條流程不寄送郵件，也不覆寫每日報告。

## 2. 資料品質評分

每筆資料建立 `quality_score`，建議 0–100：

- 官方性：0–30
- 時效性：0–20
- 多來源交叉驗證：0–20
- 欄位完整性：0–15
- 歷史一致性：0–15

## 3. 新聞去重複

優先順序：

1. canonical URL
2. normalized title hash
3. semantic similarity
4. event entity + time window

不得只依賴標題完全相同。

## 4. 事件重要性

建議 scoring：

```text
importance =
  source_credibility * 0.25
  + market_relevance * 0.25
  + regulatory_impact * 0.15
  + security_impact * 0.15
  + novelty * 0.10
  + social_velocity * 0.10
```

所有權重必須可設定。

## 5. 三日分析觸發

系統以 `reports` 中最近一次 `deep_analysis=true` 的日期為準。

條件：

```text
today - last_deep_analysis_date >= 3 days
```

若資料不足 3 個有效日，不執行統計分析，只輸出「資料累積中」。
