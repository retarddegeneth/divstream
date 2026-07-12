#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
pkill -f "python.*div-router.*app.py" 2>/dev/null || true
python app.py
