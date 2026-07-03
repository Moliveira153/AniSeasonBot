#!/usr/bin/env sh
set -eu

echo "Starting Anime Season Bot (webhook mode)..."

if [ "${RUN_MIGRATIONS_ON_STARTUP:-true}" = "true" ]; then
  echo "Running database migrations..."
  alembic upgrade head
fi

# uvicorn aceita apenas: critical, error, warning, info, debug, trace (minúsculas)
UVICORN_LOG_LEVEL=$(printf '%s' "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')

exec uvicorn app.web:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers 1 \
  --timeout-keep-alive 75 \
  --log-level "${UVICORN_LOG_LEVEL}"