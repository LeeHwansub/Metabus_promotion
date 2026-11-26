#!/usr/bin/env bash
# index.html(16:9)에서 루트 크기와 is-v 클래스만 바꿔 index-9x16.html 생성 (디자인은 한 파일에서 관리)
cd "$(dirname "$0")"
sed -e 's/id="root" data-composition-id="ending" data-width="1920" data-height="1080"/id="root" class="is-v" data-composition-id="ending" data-width="1080" data-height="1920"/' -e 's/style="width:1920px;height:1080px"/style="width:1080px;height:1920px"/' -e 's/width="1920" height="1080"><\/canvas>/width="1080" height="1920"><\/canvas>/' index.html > index-9x16.html
grep -q "class=\"is-v\"" index-9x16.html && echo "index-9x16.html OK"
