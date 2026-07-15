# 部署規格

## 1. GitHub Actions

必要 workflow：

- `daily-report.yml`
- `ci.yml`
- `security.yml`

### daily-report.yml

觸發：

- schedule
- workflow_dispatch

注意：GitHub Actions cron 使用 UTC。

若每日台灣時間 08:00：

```yaml
cron: "0 0 * * *"
```

流程：

1. checkout
2. setup-python
3. install dependencies
4. run database migration
5. execute report
6. upload artifact
7. send Gmail
8. write summary

## 2. GitHub Artifact

保留：

- PDF
- HTML
- metadata JSON
- sanitized log

建議 retention 30–90 天。

## 3. Gmail

優先：

- Gmail OAuth 2.0

替代：

- Gmail App Password + SMTP

正式環境不得使用個人密碼。

## 4. Google Drive

列為 optional provider，MVP 不阻塞。

## 5. Docker

Docker 用於本機與伺服器部署一致性。

入口：

```bash
python -m crypto_intel.cli daily-report
```

必要參數：

```bash
--date
--timezone Asia/Taipei
--dry-run
--no-email
--deep-analysis
```

## 6. 本機驗證

```bash
cp .env.example .env
make install
make test
make report-dry-run
```

## 7. 本機即時情報工作台

啟動：

```bash
make workbench
```

預設網址為 `http://127.0.0.1:8765`。也可指定連接埠：

```bash
python -m crypto_intel.cli serve --port 8766
```

工作台的設定、SQLite 資料庫與 `artifacts/rapid/` 產物沿用每日系統的 `config/default.yaml` 與環境變數。工作台只作本機資料整理，不需要啟動 GitHub Actions，也不會寄送郵件。
