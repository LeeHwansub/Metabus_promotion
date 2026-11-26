#!/usr/bin/env bash
# ending_hf/assets 재생성 (assets 폴더는 .gitignore 대상)
#  - 폰트: Google Fonts 공식 저장소 (OFL)  - GSAP 3.14.2: HyperFrames 저장소 레지스트리 사본
#  - 배경: Higgsfield 19컷(야구장) 마지막 프레임을 흐림·어둡게 (motion_graphics/play_30s/assets/clips 필요)
# 사용: bash fetch_assets.sh [HyperFrames 저장소 경로(기본 ~/tools/hyperframes)]
set -euo pipefail
cd "$(dirname "$0")"; HF="${1:-$HOME/tools/hyperframes}"
mkdir -p assets/fonts
curl -sL -o assets/fonts/ArchivoBlack-Regular.ttf "https://github.com/google/fonts/raw/main/ofl/archivoblack/ArchivoBlack-Regular.ttf"
curl -sL -o assets/fonts/Nunito-Variable.ttf "https://github.com/google/fonts/raw/main/ofl/nunito/Nunito%5Bwght%5D.ttf"
cp "$HF/registry/blocks/orbit-card/assets/gsap-3.14.2.min.js" assets/gsap.min.js
C=../play_30s/assets/clips/19_S05_C05_stadium/f0050.jpg
ffmpeg -v error -y -i "$C" -vf "scale=1920:1080,crop=1920:1080,gblur=sigma=18,eq=brightness=-0.12:saturation=0.8,colorbalance=bs=0.12:bm=0.08" -q:v 2 assets/stadium_blur.jpg
ffmpeg -v error -y -i "$C" -vf "scale=-1:1920,crop=1080:1920,gblur=sigma=18,eq=brightness=-0.12:saturation=0.8,colorbalance=bs=0.12:bm=0.08" -q:v 2 assets/stadium_blur_9x16.jpg
echo "assets ready"
