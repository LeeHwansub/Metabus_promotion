#!/usr/bin/env bash
# metaBus 시네마틱 30초 16:9 — Higgsfield 생성 컷 19개(27초) + 엔딩 3초 + 임시 사운드
# 사용: bash cinematic_30s.sh [METABUS-PROMOTION 경로]   (영상·사운드는 gitignore 대상이라 원본 체크아웃 경로를 넘김)
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "$0")/../.." && pwd)}"
CUTS="$ROOT/05_PRODUCTION/higgsfield_gen/cuts_v1"
ENDING="$ROOT/05_PRODUCTION/motion_graphics/ending_three/ending_three_16x9.mp4"
# v2: 컷에 맞춘 사운드(sound/build_sync_audio.py cinematic → loudness.py -14 LUFS). v1은 v0.6 타이밍의 임시 믹스였음
SOUND="$ROOT/05_PRODUCTION/sound/sync_cinematic_30s_-14LUFS.wav"
OUT_DIR="$ROOT/06_FINAL/cinematic"
OUT="$OUT_DIR/metaBus_cinematic_30s_16x9_v2.mp4"
mkdir -p "$OUT_DIR"

# 컷 · 시작 프레임 · 사용 프레임 (24fps). V02 타이밍(S01 0–6 · S02 6–9 · S03 9–13 · S04 13–17 · S05 17–27)에 맞춰 줄임
# 남길 부분: 동작이 끝으로 이어지는 컷(07 빛 퍼짐 · 13 활강 시작 · 17 돌진)은 뒤쪽, 나머지는 앞쪽 위주
SPEC=(
  "01_S01_C01_seoyun_room 0 67"
  "02_S01_C02a_busstop_wide 11 48"
  "03_S01_C02b_junho_phone 0 25"
  "04_S02_C01_phone_screen 0 29"
  "05_S02_C02A_seoyun_tap 0 21"
  "06_S02_C02B_junho_phone 0 16"
  "07_S02_C02B_junho_tap_close 6 29"
  "08_S03_C01a_bus_far 3 22"
  "09_S03_C01b_bus_arrive 0 29"
  "10_S03_C02_mascot_door 0 35"
  "11_S04_C01_temple_yard 0 41"
  "12_S04_C02_prayer_beads_pov 0 43"
  "13_S05_C01a_ski_slope 6 29"
  "14_S05_C01b_ski_stop_snow 0 52"
  "15_S05_C02_prayer_buddha 6 43"
  "16_S05_C03_moon 0 33"
  "17_S05_C04a_racecar_charge 2 22"
  "18_S05_C04b_racecar_passby 0 14"
  "19_S05_C05_stadium 0 50"
)

INPUTS=(); FILT=""; LABELS=""; i=0; total=0
for row in "${SPEC[@]}"; do
  read -r id start n <<<"$row"
  INPUTS+=(-i "$CUTS/$id.mp4")
  extra=""
  # 19 야구장: 아래 광고판의 깨진 글자 제거 — 위 기준 90%만 잘라 확대
  [[ $id == 19_* ]] && extra="crop=iw:ih*0.9:0:0,"
  FILT+="[$i:v]trim=start_frame=${start}:end_frame=$((start+n)),setpts=PTS-STARTPTS,${extra}scale=1920:1080:flags=lanczos,unsharp=5:5:0.4,setsar=1,fps=24,format=yuv420p[v$i];"
  LABELS+="[v$i]"; i=$((i+1)); total=$((total+n))
done
# 엔딩: 참여하기 카드(0–2초)는 V02 원칙(엔딩 카드에 버튼 없음)에 맞춰 빼고 도시 · 버스 → 로고 3초만
INPUTS+=(-i "$ENDING")
FILT+="[$i:v]trim=start_frame=48:end_frame=120,setpts=PTS-STARTPTS,scale=1920:1080,setsar=1,fps=24,format=yuv420p[v$i];"
LABELS+="[v$i]"; total=$((total+72)); i=$((i+1))
FILT+="${LABELS}concat=n=$i:v=1:a=0[vout];"
FILT+="[$i:a]atrim=0:30,afade=t=out:st=29.3:d=0.7,aresample=48000[aout]"
INPUTS+=(-i "$SOUND")

echo "컷 $((i-1))개 + 엔딩, 총 ${total}프레임 ($(echo "scale=3; $total/24" | bc)초)"
ffmpeg -v error -y "${INPUTS[@]}" -filter_complex "$FILT" -map "[vout]" -map "[aout]" \
  -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -r 24 -movflags +faststart \
  -c:a aac -b:a 192k -shortest "$OUT"
echo "→ $OUT"
