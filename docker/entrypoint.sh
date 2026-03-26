#!/bin/sh
set -e
exec llmdocs serve \
  --config /app/llmdocs.yaml \
  --data-dir /data/chroma \
  --host 0.0.0.0 \
  --port "${PORT:-8080}"
