#!/usr/bin/env bash
# v2: 합성은 invite_overlay.py(프레임마다 화면 검출 + 소수점 아핀). v1(ffmpeg 정수 픽셀 스케일)은 글자가 떨려 보여 교체
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "$0")/../.." && pwd)}"
PY="${PY:-$HOME/tools/earshot/.venv/bin/python}"   # numpy · Pillow 가 있는 파이썬
"$PY" "$(dirname "$0")/invite_overlay.py" "$ROOT"
