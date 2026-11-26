#!/usr/bin/env bash
# metaBus 시네마틱 30초 16:9 — Higgsfield 생성 컷 19개(27초) + 엔딩 3초 + 사운드트랙
# 버전: v1 임시 합성음(v0.6 타이밍) · v2 컷에 맞춘 합성음 · v3 실제 녹음 사운드트랙 + HyperFrames 형식 엔딩
#       v4 버스 · 체험 구간 속도감(빨리 감기 · 푸시인 줌 · 휩 블러). 컷 길이와 시작 시각은 그대로라 사운드트랙 싱크 유지
#       v5 07컷(준호 터치 클로즈업) 삭제 · 30초 제한 해제 → 버스 · 체험 컷을 짧게 잘라 1.25~1.6배 빠르게(약 24.7초).
#          컷 시각이 바뀌어 사운드트랙도 새로 만듦(sound/real/audio/sounddesign_cine_v5.json, 드롭 = 14.083초 스키 컷)
# 사용: bash cinematic_30s.sh [METABUS-PROMOTION 경로]   (영상·사운드는 gitignore 대상이라 원본 체크아웃 경로를 넘김)
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "$0")/../.." && pwd)}"
CUTS="$ROOT/05_PRODUCTION/higgsfield_gen/cuts_v1"
# v3: HyperFrames 형식 엔딩(ending_hf/index-cine.html, 로고만 3초)을 렌더한 영상. v2는 ending_three(예전 흰 버스 · 참여하기 카드)
ENDING="$ROOT/05_PRODUCTION/motion_graphics/ending_hf/ending_cine_16x9.mp4"
SOUND="$ROOT/05_PRODUCTION/sound/real/out/audio/soundtrack_cine_v5.wav"   # 실제 녹음 사운드트랙(real-sound, v5: audio/sounddesign_cine_v5.json)
OUT_DIR="$ROOT/06_FINAL/cinematic"
OUT="$OUT_DIR/metaBus_cinematic_16x9_v5.mp4"
mkdir -p "$OUT_DIR"

# 컷 · 시작 프레임 · 사용 프레임 (24fps). V02 타이밍(S01 0–6 · S02 6–9 · S03 9–13 · S04 13–17 · S05 17–27)에 맞춰 줄임
# 남길 부분: 동작이 끝으로 이어지는 컷(07 빛 퍼짐)은 뒤쪽, 나머지는 앞쪽 위주
# v4 추가 열(선택): 속도(원본을 n×속도 프레임 써서 n프레임에 담음) · 줌(컷 동안 푸시인 비율, 빠르게 시작해 느려짐) · 휩(in/out/both: 컷 경계 2프레임 가로 모션 블러)
SPEC=(
  "01_S01_C01_seoyun_room 0 67"
  "02_S01_C02a_busstop_wide 11 48"
  "03_S01_C02b_junho_phone 0 25"
  "04_S02_C01_phone_screen_invite 0 29"   # 초대 카드를 입힌 컷 (edit/invite_overlay.sh)
  "05_S02_C02A_seoyun_tap 0 21"
  "06_S02_C02B_junho_phone 0 16"
  "08_S03_C01a_bus_far 0 16 1.5625 0.22 out"
  "09_S03_C01b_bus_arrive 0 20 1.45 0.12 in"
  "10_S03_C02_mascot_door 0 26 1.346 0.10 -"
  "11_S04_C01_temple_yard 0 36 1.2777 0.04 -"
  "12_S04_C02_prayer_beads_pov 0 34 1.2647 0 -"
  "13_S05_C01a_ski_slope 0 22 1.5909 0.16 in"
  "14_S05_C01b_ski_stop_snow 0 38 1.368 0.12 out"
  "15_S05_C02_prayer_buddha 0 34 1.6176 0.10 in"
  "16_S05_C03_moon 0 24 1.375 0.08 out"
  "17_S05_C04a_racecar_charge 0 15 1.6 0.28 in"
  "18_S05_C04b_racecar_passby 0 10 1.4 0.06 both"
  "19_S05_C05_stadium 0 50 1.00 0.08 in"   # v5: 응원은 이전처럼 원래 속도 · 2.08초
)

INPUTS=(); FILT=""; LABELS=""; i=0; total=0
for row in "${SPEC[@]}"; do
  read -r id start n speed zoom whip <<<"$row"
  speed=${speed:-1}; zoom=${zoom:-0}; whip=${whip:--}
  INPUTS+=(-i "$CUTS/$id.mp4")
  extra=""
  # 19 야구장: 아래 광고판의 깨진 글자 제거 — 위 기준 90%만 잘라 확대
  [[ $id == 19_* ]] && extra="crop=iw:ih*0.9:0:0,"
  src=$(python3 -c "import math; print(math.ceil($n*$speed))")
  dur=$(python3 -c "print($n/24)")
  move=""
  if [[ $zoom != 0 ]]; then   # 푸시인: 1 → 1+zoom, ease-out(빠르게 시작)
    move+=",scale=w='trunc(1920*(1+${zoom}*(1-pow(1-min(t/${dur},1),2)))/2)*2':h=-2:eval=frame,crop=1920:1080"
  fi
  case $whip in   # 휩: 컷 경계 2프레임(0.083초) 가로 모션 블러
    in)   move+=",avgblur=sizeX=60:sizeY=1:enable='lt(t,0.083)'" ;;
    out)  move+=",avgblur=sizeX=60:sizeY=1:enable='gte(t,${dur}-0.083)'" ;;
    both) move+=",avgblur=sizeX=60:sizeY=1:enable='lt(t,0.083)+gte(t,${dur}-0.083)'" ;;
  esac
  FILT+="[$i:v]trim=start_frame=${start}:end_frame=$((start+src)),setpts=(PTS-STARTPTS)/${speed},fps=24,tpad=stop_mode=clone:stop=3,trim=end_frame=${n},setpts=PTS-STARTPTS,${extra}scale=1920:1080:flags=lanczos${move},unsharp=5:5:0.4,setsar=1,format=yuv420p[v$i];"
  LABELS+="[v$i]"; i=$((i+1)); total=$((total+n))
done
# 엔딩: 로고 3초 (ending_hf 시네마틱 모드)
INPUTS+=(-i "$ENDING")
FILT+="[$i:v]trim=start_frame=0:end_frame=72,setpts=PTS-STARTPTS,scale=1920:1080,setsar=1,fps=24,format=yuv420p[v$i];"
LABELS+="[v$i]"; total=$((total+72)); i=$((i+1))
FILT+="${LABELS}concat=n=$i:v=1:a=0[vout];"
DUR=$(python3 -c "print($total/24)"); FADE=$(python3 -c "print($total/24-0.7)")   # v5: 길이가 30초 고정이 아님
FILT+="[$i:a]atrim=0:${DUR},afade=t=out:st=${FADE}:d=0.7,aresample=48000[aout]"
INPUTS+=(-i "$SOUND")

echo "컷 $((i-1))개 + 엔딩, 총 ${total}프레임 ($(echo "scale=3; $total/24" | bc)초)"
ffmpeg -v error -y "${INPUTS[@]}" -filter_complex "$FILT" -map "[vout]" -map "[aout]" \
  -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -r 24 -movflags +faststart \
  -c:a aac -b:a 192k "$OUT"   # -shortest 빼기: 오디오(atrim)가 이미 영상 길이라, 있으면 반올림으로 마지막 영상 프레임이 잘림
echo "→ $OUT"
