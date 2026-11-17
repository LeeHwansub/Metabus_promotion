#!/usr/bin/env bash
# metaBus 엔딩 (HTML) → PNG 시퀀스 → MP4
# 사용: ./render.sh 16x9|9x16 [frames_dir]
#   index.html?t=<초>&a=<비율> 을 Chrome 헤드리스로 프레임마다 캡처 (24fps × 5초 = 120프레임)
#   결과: ending_html_<aspect>.mp4 (이 폴더)
set -euo pipefail

ASPECT="${1:-16x9}"
case "$ASPECT" in
  16x9) SIZE="1920,1080" ;;
  9x16) SIZE="1080,1920" ;;
  *) echo "aspect must be 16x9 or 9x16" >&2; exit 1 ;;
esac
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${2:-${TMPDIR:-/tmp}/metabus_ending_${ASPECT}}"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FPS=24
FRAMES=120

mkdir -p "$OUT"
export HERE OUT CHROME SIZE ASPECT FPS

shoot() {
  local f="$1"
  local png t
  png="$OUT/f_$(printf '%04d' "$f").png"
  [ -s "$png" ] && [ -z "${FORCE:-}" ] && return 0   # 이미 찍은 프레임은 건너뜀 (FORCE=1 로 전부 다시)
  t=$(awk -v f="$f" -v fps="$FPS" 'BEGIN { printf "%.5f", f / fps }')
  # Chrome 헤드리스는 스크린샷을 저장하고도 0이 아닌 코드로 끝나는 경우가 있어 종료 코드는 무시하고 파일로 판정
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
    --allow-file-access-from-files --window-size="$SIZE" --virtual-time-budget=1500 \
    --screenshot="$png" "file://$HERE/index.html?t=$t&a=$ASPECT" >/dev/null 2>&1 || true
}
export -f shoot
export FORCE="${FORCE:-}"

seq 0 $((FRAMES - 1)) | xargs -P 6 -I{} bash -c 'shoot {}' || true

count=$(ls "$OUT"/f_*.png | wc -l | tr -d ' ')
if [ "$count" -ne "$FRAMES" ]; then
  echo "captured $count / $FRAMES frames" >&2
  exit 1
fi

ffmpeg -y -loglevel error -framerate "$FPS" -i "$OUT/f_%04d.png" -c:v libx264 -pix_fmt yuv420p -crf 14 \
  "$HERE/ending_html_${ASPECT}.mp4"
echo "done: $HERE/ending_html_${ASPECT}.mp4 ($count frames)"
