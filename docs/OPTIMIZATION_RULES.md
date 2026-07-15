# 優化與自我診斷準則

## 1. 優化優先順序

1. 正確性
2. 可追溯性
3. 韌性
4. 可維護性
5. 成本
6. 效能
7. 報告美觀

不得為了速度犧牲來源追溯與資料正確性。

## 2. 自動診斷

每次執行產出：

- provider 成功率
- 缺失欄位
- 新聞候選數
- 去重複比例
- Top 10 平均可信度
- LLM token usage
- 執行時間
- PDF 狀態
- email 狀態

## 3. 異常判斷

需要降級或警告：

- provider success rate < 70%
- Top 10 可用事件 < 5
- 市場資料缺少 BTC 或 USDT
- USDT 價格無第二來源
- 新聞超過 50% 來自同一網域
- 社群事件無任何官方或媒體佐證
- LLM 輸出引用不存在來源
- 報告數值與資料庫不一致

## 4. 長期優化

### 第一階段

- 免費 API
- SQLite
- RSS
- 基本 PDF
- Gmail
- GitHub Actions

### 第二階段

- PostgreSQL
- 多 provider consensus
- ETF structured data
- 穩定幣供給
- Reddit / GitHub trend
- 更完整統計模型

### 第三階段

- embedding event clustering
- change-point detection
- Granger causality exploratory test
- lead-lag heatmap
- anomaly detection
- dashboard

### 即時研判

- 即時研判優先沿用既有 provider、資料模型與 SQLite，避免建立第二套資料孤島。
- 先輸出可追溯的規則式整理；只有在已配置且可稽核的模型服務下，才可考慮加入 LLM 摘要。
- 黑天鵝情境優先提高資料更新與交叉驗證密度，而非提高結論的確定性。

注意：即使使用 Granger test，也只能描述預測關係，不得直接宣稱真實因果。

## 5. 模型輸出品質

每個 AI 分析結論必須具備：

- claim
- evidence
- confidence
- uncertainty
- alternative explanation
- follow-up metric
