#!/usr/bin/env bash
# 04컷(S02_C01 폰 화면)에 초대 카드(motion_graphics/invite_card, 투명 PNG 시퀀스)를 화면에 맞춰 입힘 → 04_..._invite.mp4
# 화면 위치(1280x720 기준)는 프레임 0 · 28을 측정해 선형으로 따라감: 폰이 정면이고 약 6% 푸시인만 있어 원근 보정은 불필요
#   왼쪽 467→459 · 오른쪽 791→801(밝기 검출) · 위 40→24 · 아래 656→680(격자 측정)  → 프레임 n(0~32)마다
#   x = 467-0.25n, y = 40-0.5n, 폭 = 324+0.5625n, 높이 = 616+1.25n
# 사용: bash invite_overlay.sh [METABUS-PROMOTION 경로]   (카드 렌더: cd motion_graphics/invite_card && node render.mjs card <ROOT>/05_PRODUCTION/motion_graphics/invite_card/frames --frames 33)
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "$0")/../.." && pwd)}"
CUT="$ROOT/05_PRODUCTION/higgsfield_gen/cuts_v1/04_S02_C01_phone_screen.mp4"
CARD="$ROOT/05_PRODUCTION/motion_graphics/invite_card/frames/f_%04d.png"
OUT="$ROOT/05_PRODUCTION/higgsfield_gen/cuts_v1/04_S02_C01_phone_screen_invite.mp4"
ffmpeg -v error -y -i "$CUT" -framerate 24 -start_number 0 -i "$CARD" -filter_complex \
  "[1:v]format=rgba,scale=w='trunc(324+0.5625*n)':h='trunc(616+1.25*n)':eval=frame[c];[0:v][c]overlay=x='467-0.25*n':y='40-0.5*n':eval=frame:format=auto:eof_action=pass,format=yuv420p[v]" \
  -map "[v]" -c:v libx264 -crf 14 -preset slow -r 24 "$OUT"
echo "→ $OUT ($(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 "$OUT") frames)"
