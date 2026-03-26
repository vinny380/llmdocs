#!/usr/bin/env bash
# Run the Python demo from the repository root.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
exec python example/demo_index.py
