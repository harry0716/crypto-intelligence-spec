# 報告資料結構

建議輸出 JSON：

```json
{
  "report_date": "2026-07-15",
  "timezone": "Asia/Taipei",
  "generated_at": "2026-07-15T08:00:00+08:00",
  "market": {},
  "top_events": [],
  "regulatory_events": [],
  "social_hotspots": [],
  "correlation_observations": [],
  "risks": [],
  "watchlist_24_72h": [],
  "deep_analysis": null,
  "sources": [],
  "data_quality": {},
  "disclaimer": ""
}
```

`top_events[]`：

```json
{
  "title": "",
  "summary": "",
  "event_time": "",
  "source_name": "",
  "source_url": "",
  "affected_assets": [],
  "impact_direction": "bullish|bearish|neutral|mixed",
  "short_term_impact": "",
  "medium_term_impact": "",
  "confidence": 0.0,
  "classification": "fact|inference|rumor",
  "evidence": []
}
```

## 即時研判輸出

`artifacts/rapid/*.json` 使用下列頂層欄位：

```json
{
  "assessment_id": "rapid-20260715T120000-abcdefgh",
  "created_at": "2026-07-15T12:00:00+08:00",
  "timezone": "Asia/Taipei",
  "manual_input": {},
  "market": {},
  "immediate_judgement": {
    "summary": "",
    "classification": "inference",
    "confidence": 0.0,
    "evidence": [],
    "uncertainty": "",
    "follow_up": []
  },
  "related_events": [],
  "warnings": [],
  "method": {},
  "artifacts": {},
  "disclaimer": ""
}
```

`manual_input` 必須包含 `title`、`observation`、`stated_direction`、`urgency` 與 `source_urls`。即使提供來源 URL，使用者自己輸入的推測也維持 `inference`，只有被 provider 擷取且可追溯的資訊才可列為 `fact`。
