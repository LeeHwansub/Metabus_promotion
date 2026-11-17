# IMAGE PROMPTS

> Shot ID는 `03_STORYBOARD/storyboard.json`과 공통 키. Negative는 `negative_prompts.md` 참조.
> 툴: TODO (ChatGPT 이미지 생성 등) — 프롬프트는 툴 비종속 영어로 작성.
> ⚠️ 초안. `{BLOCK}` 표기는 아래 공통 블록 문장을 그대로 붙여 넣는다.

## 사용 규칙
1. 모든 컷은 **16:9로 생성**, 핵심 피사체는 **9:16 세로 안전 영역(중앙)** 안에 배치.
2. 캐릭터 일관성: 먼저 생성해 채택한 이미지를 **참조 이미지로 첨부**해서 다음 컷을 생성 (서윤·준호·마스코트·버스 각각).
3. 마스코트·버스 컷에는 `01_VISUAL/brand/metabus.png`, `metabus2.png`를 참조 이미지로 첨부.
4. 화면 속 한글 텍스트·로고는 AI로 생성하지 않음 → 편집 단계에서 합성.
5. 미확정 항목(🔸 표시)은 확정 후 해당 블록만 교체.
6. 변신 컷은 현실 인물 채택 이미지를 참조로 첨부해 눈매·얼굴형을 유지.

---

## 공통 블록

**{STYLE_REAL}** — SCENE 01~03 현실
```
cinematic realistic 3D render, photorealistic film still, anamorphic lens look, shallow depth of field, cool desaturated blue-gray color grading, low saturation, soft film grain, quiet and heavy mood
```

**{STYLE_STYLIZED}** — SCENE 04~06 가상 세계
```
high-quality stylized 3D animation film still, Pixar-like character design, warm golden natural light, rich vibrant colors, soft volumetric light, whimsical fantasy atmosphere
```

**{LIGHT_INVITE}** — 초대의 빛
```
soft warm golden glow, gentle and mysterious, subtle floating light particles, not sci-fi, no neon, no lasers
```

**{FRAME}**
```
16:9 cinematic composition, key subjects centered within a vertical 9:16 safe area
```

**{CHAR_01_REAL}** 김서윤 현실 🔸의상 미확정(교복 셔츠 기준, 실내복이면 `comfortable loungewear`로 교체)
```
18-year-old Korean high school girl, shoulder-length straight black hair, slim build, tired droopy eyes, no makeup, white school uniform shirt
```

**{CHAR_02_REAL}** 이준호 현실
```
29-year-old Korean office worker man, short slightly messy black hair, average build, faint dark circles, light stubble, dark navy suit, loosened tie, bag over his shoulder
```

**{CHAR_01_SKIER}** 서윤 — 스키어
```
stylized 3D teenage Korean girl skier, same eye shape and face shape as her real self, shoulder-length black hair visible under the helmet, bright ski jacket, goggles, gloves, ski poles
```

**{CHAR_02_MONK}** 준호 — 스님
```
stylized 3D young Korean Buddhist monk, same eye shape and face shape as his real self, shaved head, gray monk robes, wooden prayer beads, calm expression
```

**{CHAR_02_RACER}** 준호 — 레이서
```
stylized 3D young Korean race car driver, same eye shape and face shape as his real self, racing suit, helmet with open visor
```

**{FAN}** 응원단 관중 (서윤·준호 공통 스타일)
```
stylized 3D baseball fans in matching cheering jerseys, holding cheering sticks, no real team or sponsor logos
```

**{BUS}** (확정 — 참고 이미지 기준)
```
rounded futuristic shuttle bus, royal indigo body with periwinkle side highlights, glowing yellow accent lines, large side windows with warm interior light, "metaBus" logo and yellow M emblem on the side
```

**{MASCOT}**
```
cute cream-colored cat-like mascot, brown patches around big brown eyes, whiskers, long striped tail, purple conductor cap with yellow M emblem and yellow band, purple double-breasted uniform with yellow buttons, yellow scarf, holding a yellow star-shaped wand, stylized 3D
```

---

## SCENE 01. 반복되는 일상 (00–07초)

### IMG_S01_C01
- Shot: S01_C01 (00–03초) · 캐릭터: CHAR_01
```
{STYLE_REAL}, late night in a small teenage bedroom, desk piled high with workbooks and reference books, a single desk lamp as the only light, {CHAR_01_REAL} has just put down her pen, eyes closed, exhausted expression, a smartphone on the desk lighting up with a notification, medium close-up, eye level, {FRAME}
```
- 결과 파일: `03_STORYBOARD/storyboard_images/S01_C01.png` · 채택: [ ]

### IMG_S01_C02
- Shot: S01_C02 (03–07초) · 캐릭터: CHAR_02
```
{STYLE_REAL}, late evening city bus stop after work, streetlights and blurred car light streaks in the background, {CHAR_02_REAL} standing and waiting for the bus, looking down at his smartphone with a tired expression, the phone screen lighting his face, medium shot, eye level, {FRAME}
```
- 결과 파일: `03_STORYBOARD/storyboard_images/S01_C02.png` · 채택: [ ]

---

## SCENE 02. metaBus의 초대 (07–10초)

### IMG_S02_C01
- Shot: S02_C01 (07–08.5초) · 알림 UI는 편집에서 합성 (`01_VISUAL/visual_guide.md` 7번)
```
{STYLE_REAL}, extreme close-up of a smartphone held in a hand in a dark room, the screen glowing with {LIGHT_INVITE}, a clean empty notification card area in the center of the screen for later UI compositing, no text on screen, {FRAME}
```
- 결과 파일: `03_STORYBOARD/storyboard_images/S02_C01.png` · 채택: [ ]

### IMG_S02_C02 (A: 서윤 / B: 준호)
- Shot: S02_C02 (08.5–10초) · 두 장 생성 후 교차/분할 편집
```
A) {STYLE_REAL}, close-up of {CHAR_01_REAL} at her desk at night tapping a button on her smartphone, {LIGHT_INVITE} spreading gently from the screen and lighting her surprised face, {FRAME}

B) {STYLE_REAL}, close-up of {CHAR_02_REAL} at a night bus stop tapping a button on his smartphone, {LIGHT_INVITE} spreading gently from the screen and lighting his surprised face, {FRAME}
```
- 결과 파일: `S02_C02_A.png`, `S02_C02_B.png` · 채택: [ ]

---

## SCENE 03. 새로운 세계로 이동 (10–14초)

### IMG_S03_C01 (A: 방 / B: 정류장)
- Shot: S03_C01 (10–12초)
```
A) {STYLE_REAL} gradually turning warmer, {LIGHT_INVITE} spreading from a smartphone into a dark teenage bedroom, the walls dissolving into a magical bus stop under a starry violet night sky, a glowing yellow M bus stop sign appearing, {CHAR_01_REAL} standing in awe, wide shot, {FRAME}

B) {STYLE_REAL} gradually turning warmer, {LIGHT_INVITE} spreading from a smartphone across a city bus stop at night, the street dissolving into a magical bus stop under a starry violet night sky, a glowing yellow M bus stop sign appearing, {CHAR_02_REAL} standing in awe, wide shot, {FRAME}
```
- 결과 파일: `S03_C01_A.png`, `S03_C01_B.png` · 채택: [ ]

### IMG_S03_C02
- Shot: S03_C02 (12–14초) · 캐릭터: CHAR_01, CHAR_02, MASCOT_01 · 참조: brand 이미지 첨부
- 연출: 실사 인물 + 스타일라이즈 마스코트 공존 (새로운 세계의 첫 신호)
```
low angle cinematic shot, {BUS} arriving and stopping at a magical bus stop under a starry violet sky, headlights and warm light filling the scene, the door open, {MASCOT} standing at the door giving a cheerful salute, {CHAR_01_REAL} and {CHAR_02_REAL} stepping toward the door, realistic humans with a stylized mascot, {LIGHT_INVITE}, {FRAME}
```
- 결과 파일: `03_STORYBOARD/storyboard_images/S03_C02.png` · 채택: [ ]

---

## SCENE 04. 현실의 나에서 새로운 캐릭터로 (14–19초)

### IMG_S04_C01
- Shot: S04_C01 (14–16초) · 캐릭터: CHAR_01, CHAR_02
```
cinematic interior of {BUS}, cozy futuristic cabin with indigo seats and yellow accent lights, warm glowing light wrapping around {CHAR_01_REAL} and {CHAR_02_REAL} seated inside, realism starting to soften, tracking shot moving into the cabin, {LIGHT_INVITE}, {FRAME}
```
- 결과 파일: `03_STORYBOARD/storyboard_images/S04_C01.png` · 채택: [ ]

### IMG_S04_C02 (A: 준호 스님 / B: 서윤 스키) — 첫 변신 공개
- Shot: S04_C02 (16–19초) · 각 2장: ① POV 손 ② 고개를 든 공간 공개
- 변신 과정은 그리지 않음. 담백한 톤.
```
A1) {STYLE_STYLIZED}, first-person POV looking down at his own hands holding wooden prayer beads, gray monk robe sleeves, soft morning light, {FRAME}
A2) {STYLE_STYLIZED}, a quiet Korean mountain temple at dawn, mist over the mountains, {CHAR_02_MONK} standing in the courtyard looking around calmly, wide shot, {FRAME}

B1) {STYLE_STYLIZED}, first-person POV looking down at her own gloved hands gripping ski poles, skis on fresh snow, bright sunlight, {FRAME}
B2) {STYLE_STYLIZED}, the top of a snowy ski slope with a vast mountain view, {CHAR_01_SKIER} standing ready at the edge, wide shot, {FRAME}
```
- 결과 파일: `S04_C02_A1.png`, `S04_C02_A2.png`, `S04_C02_B1.png`, `S04_C02_B2.png` · 채택: [ ]

---

## SCENE 05. metaBus에서 만나는 다양한 경험 (19–25초)
> 체험형 몽타주. 실제 서비스 화면은 AI 생성 대신 캡처/녹화 삽입 (편집 단계).

### IMG_S05_C01 — 스키장 활강
- Shot: S05_C01 (19–21초) · 캐릭터: CHAR_01
```
{STYLE_STYLIZED}, {CHAR_01_SKIER} carving down a snowy slope at high speed, powder snow spraying in the air, sparkling sunlight, dynamic low angle, motion and speed, {FRAME}
```
- 결과 파일: `03_STORYBOARD/storyboard_images/S05_C01.png` · 채택: [ ]

### IMG_S05_C02 — 카레이싱 ⭐Newtake 영상 후보
- Shot: S05_C02 (21–23초) · 캐릭터: CHAR_02
```
{STYLE_STYLIZED}, {CHAR_02_RACER} driving a sleek race car at full speed on a vibrant race track, motion blur, low tracking angle beside the car, sunset light, exhilarating, no real brand or sponsor logos, {FRAME}
```
- 결과 파일: `03_STORYBOARD/storyboard_images/S05_C02.png` · 채택: [ ]
- 이 이미지를 Newtake 영상 생성의 시작 프레임으로 사용

### IMG_S05_C03 — 야구장 응원 (소셜)
- Shot: S05_C03 (23–25초) · 캐릭터: CHAR_01, CHAR_02, MASCOT_01
```
{STYLE_STYLIZED}, a packed baseball stadium at night under bright floodlights, {FAN}, the teenage girl and the young man from earlier meeting in the stands and cheering together, {MASCOT} cheering beside them, confetti, joyful energy, {FRAME}
```
- 결과 파일: `03_STORYBOARD/storyboard_images/S05_C03.png` · 채택: [ ]

---

## SCENE 06. 다시 도착한 초대 (25–30초)

### IMG_S06_C01 — 경험의 여운
- Shot: S06_C01 (25–27초) · 앞 컷들의 교차 편집 + 마지막 1장
```
{STYLE_STYLIZED}, after the game, the baseball stadium under a warm sunset sky, the two fans and {MASCOT} sitting together in the stands, warm light slowly fading, peaceful, wide shot, {FRAME}
```
- 결과 파일: `03_STORYBOARD/storyboard_images/S06_C01.png` · 채택: [ ]

### IMG_S06_C02 ~ C04 — AI 생성 제외
- S06_C02 알림 UI, S06_C03 로고, S06_C04 `metabus.app` → **모션그래픽/편집 제작**
- 배경 플레이트만 필요 시:
```
deep night navy background with a soft violet starry glow and faint warm golden light in the center, minimal, clean, empty space for a logo, 16:9
```
- 결과 파일: `03_STORYBOARD/storyboard_images/S06_BG.png` · 채택: [ ]
