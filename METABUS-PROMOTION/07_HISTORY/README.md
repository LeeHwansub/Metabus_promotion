# metaBus 30초 홍보영상 — 제작 변천 기록

작성 2026-11-26 · 저장소 [LeeHwansub/Metabus_promotion](https://github.com/LeeHwansub/Metabus_promotion)

이 문서는 기획부터 v4까지 무엇이 어떤 순서로 바뀌었는지, 그리고 그 근거를 확인하는 방법을 정리한다.
근거는 세 가지로 남겼다.

| 근거 | 확인 방법 |
|---|---|
| git 커밋 | `git show <해시>` — 아래 표의 해시는 모두 `main`에 들어 있다 |
| GitHub PR | 아래 PR 링크 (변경 파일 · 설명 · 병합 시각) |
| 로컬 결과물 (영상 · 음원, gitignore) | `shasum -a 256 <파일>` 앞 16자리가 아래 표와 같으면 같은 파일 |

기획 상세(대사 · 컷 · 결정 이유)는 Claude Design [프로덕션 바이블 캔버스](https://claude.ai/artifact/Hjc5hMWASdLobUTAnNPAyq)와
Notion [metaBus 30초 홍보영상 — 제작 기록](https://app.notion.com/p/4217340c076d811c8c99eddee118e395)
(하위: [제작 기록](https://app.notion.com/p/4247340c076d814b9dc7cbcb80ba8027) · [스토리보드 변천](https://app.notion.com/p/4247340c076d8116aef3d51fb9f8d194))에 있다.
두 곳 모두 비공개라 열람하려면 공유가 필요하다.

---

## 1. 스토리보드 변천

| 단계 | 날짜 | 컷 | 바뀐 점 | 근거 |
|---|---|---|---|---|
| 최초 기획 | 11-17 | 15컷 | 6개 시퀀스. 버스 탑승 장면 · 버스 내부 트래킹 · 손 POV로 변신 공개 | 커밋 `e708d7e` `03_STORYBOARD/storyboard.md` |
| 탑승 생략 결정 | 11-17 | — | 버스 도착 → 문이 열리며 빛이 화면을 덮고 바로 다음 장면 | 전환 수정안 storyboard.md "2026-11-17 결정" |
| **v0.6 전환 수정안** | 11-20 | 14컷 | 장면을 잇는 전환 확정: 산사 합장 → 카메라가 올라가 불상 얼굴 → 전환 · 스키 급정지 눈보라가 화면을 덮음 · 레이싱카가 렌즈 앞을 지나감 · 야구장 옆모습 → 뒷모습 → 크레인업 → 엔딩. 카메라 원칙(인물 1/3, 35~50mm, 앞쪽 사물로 깊이) 추가 | **이 폴더** `2026-11-20_storyboard_v0.6_transitions_draft/` (커밋되지 않았던 작업본 원문) |
| v0.6 커밋본 | 11-22 | 14컷 | 전환 수정안을 정리해 커밋 (구간 시각 · 프롬프트 일부 조정) | 커밋 `5ab5d4d` · PR #1 |
| **V02 확정** | 11-20 결정 · 11-22 반영 | 16컷 | S01 2 · S02 2 · S03 2 · S04 2 · S05 5 · S06 3. 준호 산사 → 서윤 스키는 하늘을 거치는 시선 틸트. 엔딩 3컷 4초, 엔딩 카드에 [참여하기] 없음. 서윤 우주복 · 달 장면 추가 | 프로덕션 바이블 캔버스 "03 씬 · 컷 (16컷)" · 프리비즈 스크립트 커밋 `1103385` |

v0.6 전환 수정안과 v0.6 커밋본의 차이는 `2026-11-20_storyboard_v0.6_transitions_draft/diff_vs_v0.6_commit_5ab5d4d.patch`에 있다
(storyboard.md 7줄 · storyboard.json 10줄 · image_prompts.md 20줄).

> 참고: 저장소의 `03_STORYBOARD/storyboard.md`는 아직 v0.6(14컷) 문서다. V02(16컷) 원본은 캔버스에 있다.

## 2. 영상 버전 변천

| 버전 | 날짜 | 내용 | 근거 (커밋 · PR) |
|---|---|---|---|
| 엔딩 v3 · 애니매틱 v1 · 임시 사운드 | 11-22 | Three.js 엔딩, 스틸 애니매틱, v0.6 타이밍 합성음 | `7a3caa5` · PR #1 |
| PLAY v1 | 11-22 | 'PLAY' 한 단어를 30초 동안 변주, 9번 등장 | `ad263f3` · PR #1 |
| PLAY v2 (A안) | 11-22 | 과하다는 피드백 → 큰 PLAY 4번(초대 · 스키 · 야구장 · 엔딩) | `1416416` · PR #1 |
| 프리비즈 V02 · PLAY v3 샘플 | 11-23 | Blender 회색 블록 30초(15컷), PLAY 이후 움직임 연결형 빠른 컷 10초 | `1103385` · PR #1 |
| AI 영상 · 소재 정리 | 11-23 | Higgsfield 30초 생성본을 19컷으로 분할, 모션그래픽용 프레임 · 누끼 시퀀스 | `da710ef` · PR #2 |
| **PLAY v4 · 시네마틱 v2 · 싱크 사운드** | 11-26 | v2 구성에 생성 영상 컷, 시네마틱 30초 편집, 컷 시각에 맞춘 120 BPM 합성음 | `57e5efa` · PR #3 |

PR: [#1](https://github.com/LeeHwansub/Metabus_promotion/pull/1) (11-23 병합) · [#2](https://github.com/LeeHwansub/Metabus_promotion/pull/2) (11-23 병합) · [#3](https://github.com/LeeHwansub/Metabus_promotion/pull/3) (11-26 병합)

## 3. AI 영상 생성 시도

| 도구 | 날짜 | 결과 | 남은 근거 |
|---|---|---|---|
| Newtake (Seedance 2.5) | 11-23 | 30초 전체가 약 2,070크레딧(보유 100) → 불가. 체험 10초도 Flash 325 · Draft 500 → 불가 | Newtake 캔버스 1 노드 기록 |
| Newtake Flash 480p | 11-23 | 스키 4초만 생성(52크레딧). 캐릭터 일치 · 애니 톤 | `05_PRODUCTION/newtake_gen/S05_ski_4s_flash480_v1.mp4` |
| Higgsfield (Seedance 2.5 Flash 720p) | 11-23 | 무료 1회로 30초 한 번에. 프리비즈 영상 1 + 컷 이미지 20 + 시트 9 | 19컷 `05_PRODUCTION/higgsfield_gen/cuts_v1/` · 목록 `05_PRODUCTION/motion_graphics/clips/clips.json` |

> Higgsfield 원본 30초 파일(`hf_20261123_033913_…mp4`)은 2026-11-26 확인 시 로컬에서 삭제돼 있었다.
> 19컷(합 721프레임 = 원본 프레임 수)이 남아 있어 내용 손실은 없고, 원본은 Higgsfield 웹 프로젝트에 남아 있다.

## 4. 결과물 해시 (SHA-256 앞 16자리 · gitignore 로컬 파일)

| 파일 (METABUS-PROMOTION/ 기준) | 크기(byte) | 수정 시각 | SHA-256 |
|---|---|---|---|
| `06_FINAL/play/metaBus_PLAY_30s_v4_16x9.mp4` | 27,675,465 | 2026-11-26 11:10 | `c82e0f4b15588082` |
| `06_FINAL/play/metaBus_PLAY_30s_v4_9x16.mp4` | 26,744,761 | 2026-11-26 11:19 | `7474e94673610adc` |
| `06_FINAL/cinematic/metaBus_cinematic_30s_16x9_v2.mp4` | 30,802,597 | 2026-11-26 11:08 | `f68bb9eb5bcbd024` |
| `06_FINAL/cinematic/metaBus_cinematic_30s_16x9_v1.mp4` | 30,800,592 | 2026-11-26 11:05 | `7f345afb626717e4` |
| `05_PRODUCTION/sound/sync_play_v4_30s_-14LUFS.wav` | 5,760,078 | 2026-11-26 11:07 | `28ee939ec3a1efc3` |
| `05_PRODUCTION/sound/sync_cinematic_30s_-14LUFS.wav` | 5,760,078 | 2026-11-26 11:07 | `d9920c95215f96ce` |
| `03_STORYBOARD/previs/v02_full/previs_v02_full_30s_16x9.mp4` | 4,122,901 | 2026-11-22 15:19 | `f82c79f71fc713a4` |
| `05_PRODUCTION/newtake_gen/S05_ski_4s_flash480_v1.mp4` | 3,967,243 | 2026-11-23 11:27 | `98ffd550968e05d8` |
| `05_PRODUCTION/motion_graphics/play_30s_v2/metaBus_PLAY_30s_v2_16x9.mp4` | 17,236,318 | 2026-11-22 11:15 | `207b7047235c8297` |
| `05_PRODUCTION/motion_graphics/play_30s/metaBus_PLAY_30s_16x9.mp4` | 17,807,748 | 2026-11-22 10:49 | `75a17977cf9c5367` |

검증 기록(v4 · 시네마틱 v2): 세 영상 모두 30.000초 · 720프레임, ffmpeg-skill `check.py` YouTube/Reels 통과(자막 없음 경고만), -14 LUFS · 진피크 -1.9 dBTP.

## 5. 브랜치 정리 (2026-11-26)

모두 `main`에 병합된 뒤 삭제했다. 마지막 커밋이 `main`의 조상이라 해시로 언제든 다시 꺼낼 수 있다(`git switch -c <이름> <해시>`).

| 브랜치 | 마지막 커밋 | 쓰임 |
|---|---|---|
| `origin/feature/ending` | `57e5efa` | PR #1 · #2 · #3 head |
| `feature/ending` (로컬) | `ad263f3` | 초기 작업 체크아웃 |
| `play-v2` | `57e5efa` | v2~v4 작업 worktree |
| `worktree-play-v2` | `4c54241` | worktree 생성 시 기본 브랜치 (작업 없음) |
| `worktree-storyboard-transitions` | `4c54241` | v0.6 전환 수정안 worktree — 커밋되지 않은 3개 파일은 이 폴더에 원문 보존 |
