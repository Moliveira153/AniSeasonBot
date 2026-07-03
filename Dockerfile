FROM python:3.12-slim AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --upgrade pip && pip install .

COPY . .
RUN chmod +x scripts/start_web.sh

FROM base AS bot
CMD ["python", "-m", "app.main"]

FROM base AS web
ENV BOT_MODE=webhook
EXPOSE 8000
CMD ["sh", "scripts/start_web.sh"]

FROM base AS worker
CMD ["arq", "app.workers.scheduler.WorkerSettings"]

FROM base AS health
CMD ["python", "-m", "app.health"]

FROM curlimages/curl:8.5.0 AS curl
CMD ["sh", "-c", "curl -fsS \"${KEEPALIVE_URL}/health\" && echo ' keepalive ok' || echo ' keepalive failed'"]