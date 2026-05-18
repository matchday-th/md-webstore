#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"
NGROK_BIN="${NGROK_BIN:-ngrok}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [ -d "$ROOT_DIR/venv" ]; then
  # Reuse the local virtualenv when present.
  # shellcheck disable=SC1091
  source "$ROOT_DIR/venv/bin/activate"
  PYTHON_BIN="python"
fi

if ! command -v "$NGROK_BIN" >/dev/null 2>&1; then
  echo "ngrok command not found. Install ngrok first."
  exit 1
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python command '$PYTHON_BIN' not found."
  exit 1
fi

if ! lsof -nP -iTCP:27017 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "MongoDB is not listening on port 27017."
  echo "Start MongoDB first, then rerun ./run_tunnel.sh"
  exit 1
fi

if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "App already listening on port $PORT."
else
  echo "Starting FastAPI on port $PORT..."
  DEBUG="${DEBUG:-True}" "$PYTHON_BIN" -m uvicorn backend.main:app --host "$HOST" --port "$PORT" > /tmp/ecommerce_uvicorn.log 2>&1 &
  APP_PID=$!

  for _ in $(seq 1 20); do
    if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done

  if ! lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "FastAPI failed to start. Recent log output:"
    tail -n 40 /tmp/ecommerce_uvicorn.log || true
    if [ -n "${APP_PID:-}" ] && kill -0 "$APP_PID" >/dev/null 2>&1; then
      kill "$APP_PID" >/dev/null 2>&1 || true
    fi
    exit 1
  fi
fi

UPSTREAM_HOST="${UPSTREAM_HOST:-127.0.0.1}"

echo "Starting ngrok for http://$UPSTREAM_HOST:$PORT ..."
exec "$NGROK_BIN" http "$UPSTREAM_HOST:$PORT" --log stdout
