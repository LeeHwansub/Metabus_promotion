"""
04컷(S02_C01 폰 화면)에 초대 카드를 입힌다 — v2 (흔들림 · 위치 · 크기 수정)

v1(invite_overlay.sh, ffmpeg)의 문제:
  - 카드를 매 프레임 정수 픽셀 크기로 줄여 붙여(540→약 330px) 크기가 1px씩 끊겨 바뀌며 글자가 떨려 보임
  - 카드 자체 애니메이션(확대 0.94→1, 버튼 눌림)까지 겹쳐 흔들림이 더 커 보임
  - 화면 중간 아래(47%)에 작게(폭 84%) 떠 있어 실제 폰 알림 같지 않음
v2:
  - 화면 경계를 프레임마다 검출(좌우: 밝기, 위아래: 검은 베젤로 바뀌는 지점) → 직선 맞춤으로 잡음 제거
  - 소수점 단위 아핀 변환으로 붙임(정수 반올림 없음) + 영상 질감에 맞춰 아주 약한 흐림
  - 카드는 실제 알림처럼 화면 위쪽(다이내믹 아일랜드 아래), 폭 92%. 등장은 살짝 내려오며 나타나는 것만
  - 카드 그림은 invite_card 렌더 프레임에서 다 자리 잡은 구간(13~22, 버튼 위 빛 포함)만 잘라 씀
    (이 환경에서 Chrome이 비정상 종료해 카드 재렌더가 안 돼서 기존 렌더를 재활용)

사용: python3 invite_overlay.py [METABUS-PROMOTION 경로]
"""
import glob, json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageFilter

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
CUTF = os.path.join(ROOT, "05_PRODUCTION/motion_graphics/play_30s/assets/clips/04_S02_C01_phone_screen")
CARDF = os.path.join(ROOT, "05_PRODUCTION/motion_graphics/invite_card/frames")
OUT = os.path.join(ROOT, "05_PRODUCTION/higgsfield_gen/cuts_v1/04_S02_C01_phone_screen_invite.mp4")
TMP = os.path.join(ROOT, "05_PRODUCTION/higgsfield_gen/cuts_v1/_invite_frames")
os.makedirs(TMP, exist_ok=True)
frames = sorted(glob.glob(os.path.join(CUTF, "f*.jpg")))
N = len(frames)

# ---- 1. 화면 경계 검출 (1280x720)
box = []
for f in frames:
    a = np.asarray(Image.open(f).convert("L")).astype(float)
    cols = np.where((a[250:450] > 95).mean(0) > 0.7)[0]
    cols = cols[(cols > 350) & (cols < 930)]
    x0, x1 = cols.min(), cols.max()
    prof = (a[:, x0 + (x1 - x0) // 4] + a[:, x0 + 3 * (x1 - x0) // 4]) / 2   # 노치를 피한 세로선 두 개
    y = 360
    while y > 0 and prof[y] > 45: y -= 1
    top = y + 1
    y = 360
    while y < 719 and prof[y] > 45: y += 1
    box.append([x0, x1 + 1, top, y])
box = np.array(box, float)
k = np.arange(N)
fit = np.stack([np.polyval(np.polyfit(k, box[:, j], 1), k) for j in range(4)], 1)   # 직선 맞춤
print("screen f0 %s → f%d %s, 잔차 최대 %.1fpx" % (np.round(fit[0], 1).tolist(), N - 1, np.round(fit[-1], 1).tolist(), np.abs(fit - box).max()))

# ---- 2. 카드 스프라이트 (540x1000 캔버스 기준): 자리 잡은 프레임 13~22에서 카드 영역만
def card(i):
    return Image.open(os.path.join(CARDF, "f_%04d.png" % i)).convert("RGBA")
ref = np.asarray(card(22))[..., 3]
ys, xs = np.where(ref > 200)                       # 카드 본체(그림자 · 배경 음영 제외)
cx0, cx1, cy0, cy1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
PAD = 34                                           # 그림자 여유
crop_box = (int(cx0 - PAD), int(cy0 - PAD), int(cx1 + PAD), int(cy1 + PAD))
SCALE = (540 * 0.92) / (cx1 - cx0)                 # 화면 폭의 92%
TOP = 92                                           # 캔버스 1000 기준 위쪽 여백(다이내믹 아일랜드 아래)

def ease(x): return 1 - (1 - max(0.0, min(1.0, x))) ** 3

def layer(kf):
    """캔버스(540x1000) 위 카드 레이어: 0~8프레임 살짝 내려오며 나타남, 이후 버튼 위 빛(원본 13~22)"""
    src = min(22, 13 + max(0, kf - 4))
    sp = card(src).crop(crop_box)
    sp = sp.resize((round(sp.width * SCALE), round(sp.height * SCALE)), Image.LANCZOS)
    e = ease(kf / 8)
    a = np.asarray(sp).astype(float); a[..., 3] *= e
    sp = Image.fromarray(a.astype("uint8"), "RGBA")
    canvas = Image.new("RGBA", (540, 1000), (0, 0, 0, 0))
    canvas.alpha_composite(sp, (round((540 - sp.width) / 2), round(TOP - PAD * SCALE - 22 * (1 - e))))
    return canvas

# ---- 3. 합성: 캔버스 540x1000 → 화면 사각형, 소수점 아핀
for i, f in enumerate(frames):
    bg = Image.open(f).convert("RGBA")
    x0, x1, y0, y1 = fit[i]
    sx, sy = (x1 - x0) / 540.0, (y1 - y0) / 1000.0
    lay = layer(i).transform(bg.size, Image.AFFINE, (1 / sx, 0, -x0 / sx, 0, 1 / sy, -y0 / sy), resample=Image.BICUBIC)
    lay = lay.filter(ImageFilter.GaussianBlur(0.45))   # 영상 질감에 맞춤
    bg.alpha_composite(lay)
    bg.convert("RGB").save(os.path.join(TMP, "f_%04d.png" % i))

subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "24", "-start_number", "0", "-i", os.path.join(TMP, "f_%04d.png"),
                "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt", "yuv420p", "-r", "24", OUT], check=True)
json.dump({"fit": np.round(fit, 2).tolist(), "measured": box.tolist()}, open(OUT.replace(".mp4", "_track.json"), "w"))
print("→", OUT, N, "frames")
