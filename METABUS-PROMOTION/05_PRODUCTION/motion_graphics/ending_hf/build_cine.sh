#!/usr/bin/env bash
# 시네마틱용 엔딩(16:9, 3초, PLAY 없이 로고만): index.html 에서 is-cine 클래스와 길이만 바꿈
cd "$(dirname "$0")"
sed -e 's/id="root" data-composition-id="ending" data-width="1920" data-height="1080" data-start="0" data-duration="4"/id="root" class="is-cine" data-composition-id="ending" data-width="1920" data-height="1080" data-start="0" data-duration="3"/' index.html > index-cine.html
grep -q "class=\"is-cine\"" index-cine.html && echo "index-cine.html OK"
