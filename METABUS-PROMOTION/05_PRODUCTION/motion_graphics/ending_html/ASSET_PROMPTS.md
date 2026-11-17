# 엔딩(HTML) 이미지 에셋 — GPT 생성 프롬프트

> 기준: `05_PRODUCTION/motion_graphics/ending/ending_storybord2.png` (E03, E04)
> 생성한 이미지를 `assets/` 에 아래 **파일명 그대로** 넣으면 `index.html`이 자동으로 사용합니다.
> 이미지가 없으면 화면 왼쪽 아래에 "이미지 필요" 표시가 나옵니다.
> 공통: **글자·로고·워터마크 없이** (로고·문구는 코드로 얹음), 스토리보드와 같은 **파스텔 라벤더 노을 / 시네마틱 일러스트** 톤.

| 파일 | 장면 | 비율 / 크기 | 배경 |
|---|---|---|---|
| `assets/e03_bg_16x9.png` | E03 미래 도시 배경 | 16:9, 1920×1080 이상 | 불투명 |
| `assets/e03_bg_9x16.png` | E03 미래 도시 배경 | 9:16, 1080×1920 이상 | 불투명 |
| `assets/e03_bus_16x9.png` | E03 버스 (단독) | 가로형 (약 1.6:1) | **투명 PNG** |
| `assets/e03_bus_9x16.png` | E03 버스 (단독) | 가로형 (약 1.6:1), 위와 같은 이미지 써도 됨 | **투명 PNG** |
| `assets/e04_bg_16x9.png` | E04 브랜드 엔딩 배경 | 16:9 | 불투명 |
| `assets/e04_bg_9x16.png` | E04 브랜드 엔딩 배경 | 9:16 | 불투명 |

---

## E03 — 미래 도시 배경 (`e03_bg_*`)
버스는 따로 합성하므로 **버스 없이**, 아래쪽에 버스가 달릴 도로 공간을 비워 둡니다.
```
Cinematic illustrated futuristic city at golden-lavender dusk, low camera angle from road level.
Elegant white and lavender skyscrapers with round floating sky platforms and glowing blue rim lights,
soft pink and peach sunset clouds, pastel lavender sky, light haze and depth, gentle bloom.
A smooth glossy road in the foreground running left to right with subtle blue light trails, empty of vehicles.
Calm, dreamy, premium, anime-inspired cinematic illustration, soft volumetric light.
No text, no logos, no people, no vehicles.
```
- 16:9: `wide 16:9 composition, road across the lower third`
- 9:16: `vertical 9:16 composition, road in the lower quarter, tall towers and sky above`

## E03 — 버스 (`e03_bus_*`, 투명 배경)
```
A sleek futuristic electric shuttle bus, 3/4 front view from a low angle, driving toward the left.
Glossy pearl-white body with a dark navy panoramic window band, rounded aerodynamic shape,
thin glowing blue LED light strips along the lower body and front pillars, slim white headlights.
The word "metaBus" in a clean rounded geometric font on the side.
Soft lavender sunset reflections on the body, cinematic illustration matching a pastel dusk scene.
Isolated on a transparent background, no ground, no shadow box, no other objects.
```
- 측면 "metaBus" 글자가 깨지면 문장에서 해당 줄을 빼고 생성 → 글자는 나중에 합성 가능

## E04 — 브랜드 엔딩 배경 (`e04_bg_*`)
로고·URL·궤도 링은 코드로 얹으므로 **중앙은 비워 둡니다.**
```
Cinematic dreamy night-to-dusk sky for a brand ending screen. Deep indigo sky at the top fading to soft lavender
near the horizon, faint stars. At the bottom, the curved edge of a planet-like horizon with a thin glowing
periwinkle rim light, a tiny futuristic city skyline silhouette with soft lights along the curve.
Fluffy pastel lavender-white clouds rising at the lower left and lower right corners.
Large clean empty space in the center for a logo. Soft bloom, premium, calm.
No text, no logos, no rings, no people.
```
- 16:9: `wide 16:9 composition`
- 9:16: `vertical 9:16 composition, horizon curve in the bottom fifth`

---

## 넣은 뒤 렌더
`ending_html` 폴더에서 실행:
```bash
./render.sh 16x9
```
```bash
./render.sh 9x16
```
