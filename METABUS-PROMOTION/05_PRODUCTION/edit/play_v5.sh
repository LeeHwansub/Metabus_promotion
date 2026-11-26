#!/usr/bin/env bash
# metaBus 모션그래픽 PLAY v5 (16:9 · 9:16) — 26초
#   본편 0–22초: motion_graphics/play_30s_v4/index-v5.html (07컷 → 06컷 · 버스/체험 빨리 감기 · 9:16 인물 위치 수정)
#   엔딩 22–26초: motion_graphics/ending_hf (v4.2와 같은 HyperFrames 형식 PLAY 엔딩, 96프레임)
#   사운드: sound/real/out/audio/soundtrack_play_v5.wav (sound/real/audio/sounddesign_play_v5.json, QA 통과)
# 사용: bash play_v5.sh [METABUS-PROMOTION 원본 체크아웃 경로]   (영상 · 사운드는 gitignore 대상)
# Chrome 헤드리스로 렌더하므로 일반 터미널에서 실행 (백그라운드 작업 환경에서는 Chrome이 시작되지 않음)
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"                 # 이 체크아웃의 05_PRODUCTION (렌더할 페이지)
ROOT="${1:-$(cd "$HERE/.." && pwd)}"                    # 사운드 · 출력이 있는 체크아웃
SOUND="$ROOT/05_PRODUCTION/sound/real/out/audio/soundtrack_play_v5.wav"
OUT_DIR="$ROOT/06_FINAL/play"
TMP="${TMPDIR:-/tmp}/metabus_play_v5"
MAIN=528; END=96                                         # 22초 + 4초 (24fps)
mkdir -p "$OUT_DIR" "$TMP"
[[ -f $SOUND ]] || { echo "사운드트랙 없음: $SOUND"; exit 1; }

for A in 16x9 9x16; do
  echo "== $A 본편 ${MAIN}프레임"
  (cd "$HERE/motion_graphics/play_30s_v4" && node render.mjs $A "$TMP/main_$A" --page index-v5.html --frames $MAIN)
  echo "== $A 엔딩 ${END}프레임"
  PAGE=$([[ $A == 9x16 ]] && echo index-9x16.html || echo index.html)
  (cd "$HERE/motion_graphics/ending_hf" && node render.mjs $A "$TMP/end_$A" --page $PAGE --frames $END)
  OUT="$OUT_DIR/metaBus_PLAY_v5_$A.mp4"
  ffmpeg -v error -y -framerate 24 -start_number 0 -i "$TMP/main_$A/f_%04d.png" \
    -framerate 24 -start_number 0 -i "$TMP/end_$A/f_%04d.png" -i "$SOUND" \
    -filter_complex "[0:v]format=yuv420p[a];[1:v]format=yuv420p[b];[a][b]concat=n=2:v=1:a=0[v];[2:a]atrim=0:26,aresample=48000[au]" \
    -map "[v]" -map "[au]" -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -r 24 -c:a aac -b:a 192k -movflags +faststart "$OUT"
  echo "→ $OUT ($(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 "$OUT")프레임)"
done
