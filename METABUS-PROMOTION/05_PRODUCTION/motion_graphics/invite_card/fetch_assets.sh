#!/usr/bin/env bash
# invite_card/assets 재생성 (assets는 .gitignore): Noto Sans KR · Nunito(OFL, Google Fonts) + GSAP(ending_hf/assets 사본)
set -euo pipefail; cd "$(dirname "$0")"; mkdir -p assets/fonts
curl -sL -o assets/fonts/NotoSansKR-Variable.ttf "https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf"
curl -sL -o assets/fonts/Nunito-Variable.ttf "https://github.com/google/fonts/raw/main/ofl/nunito/Nunito%5Bwght%5D.ttf"
cp ../ending_hf/assets/gsap.min.js assets/gsap.min.js && echo "assets ready"
