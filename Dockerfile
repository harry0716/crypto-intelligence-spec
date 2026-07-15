FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY config ./config

RUN pip install --no-cache-dir -e ".[pdf]"

ENV APP_ENV=production
ENTRYPOINT ["python", "-m", "crypto_intel.cli"]
CMD ["daily-report", "--dry-run", "--no-email"]

