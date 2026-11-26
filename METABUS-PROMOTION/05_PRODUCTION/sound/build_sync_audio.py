"""
metaBus 30초 — 컷에 맞춘 사운드(임시음, 합성) · 파이썬 표준 라이브러리만 사용

실행:  python3 build_sync_audio.py play        → sync_play_v4_30s.wav       (모션그래픽 PLAY v4 타임라인)
       python3 build_sync_audio.py cinematic   → sync_cinematic_30s.wav     (시네마틱 30초 편집 타임라인)
       (48 kHz / 16 bit / stereo, 피크만 맞춤 — 최종 음량은 ffmpeg-skill loudness.py 로 -14 LUFS)

build_temp_audio.py(v0.6 · 14컷 시각에 고정)와 달리, 아래 CUES 에 컷 시각만 바꿔 넣으면 같은 소리를 다시 배치한다.
음악은 120 BPM(박 0.5초). 드롭 시각을 박 기준점으로 삼아 스키 · 급정지 · 레이싱 · 야구장 · 엔딩 PLAY가 박 위에 떨어지게 한다.
모든 소리는 합성 임시음 — 라이선스 확보한 실제 음원으로 교체할 때도 같은 큐 시각을 쓴다.
"""
import math
import os
import random
import struct
import sys
import wave

SR = 48000
DUR = 30.0
N = int(SR * DUR)
HERE = os.path.dirname(os.path.abspath(__file__))
BEAT = 0.5                     # 120 BPM

# ---------------------------------------------------------------- 컷 시각표 (초)
CUES = {
    # play_30s_v4/index.html SHOTS + 장면 함수 안 세부 시각
    "play": dict(
        out="sync_play_v4_30s.wav",
        noti=[(6.1, 0.0)],                      # S02 폰 화면 알림
        tap=[(7.62, -0.3), (8.0, 0.3)],         # 서윤 · 준호 터치
        shimmer=8.0, play_hit=8.5,              # 빛 퍼짐 → ▶가 PLAY로 폭발
        bus=(9.0, 2.0), brake=10.85,            # 버스 접근 · 정차
        door=(11.9, 13.0),                      # 문 빛이 화면을 덮음
        temple_bell=13.0, temple_bell2=19.0,    # 산사 마당 · 법당
        whoosh=[(15.6, 0.45, 1), (16.0, 0.4, -1)],   # 틸트업 · 틸트다운
        build=(9.0, 13.0), calm_end=9.0,
        drop=17.0, drop_end=26.0,               # 스키부터 박
        ski=(17.5, 0.95), snow=18.42,           # 활강 · 급정지 눈보라
        moon_riser=(21.9, 22.5),                # 별이 커져 헤드라이트로
        engine=(22.5, 0.75), passby=23.2,       # 레이싱 돌진 · 통과
        crowd=(24.0, 2.0),                      # 야구장
        ending_hit=26.0, logo=27.95,            # PLAY 슬램 · 로고
    ),
    # edit/cinematic_30s.sh 컷 경계(프레임 합산 /24)
    "cinematic": dict(
        out="sync_cinematic_30s.wav",
        noti=[(1.4, -0.2), (5.0, 0.2)],         # 서윤 방 · 준호 폰
        tap=[(7.35, -0.3), (8.95, 0.3)],        # 서윤 터치 · 준호 터치 클로즈업
        shimmer=8.95, play_hit=None,
        bus=(9.79, 2.13), brake=11.6,
        door=(11.92, 13.375),
        temple_bell=13.375, temple_bell2=20.25,
        whoosh=[(16.3, 0.5, 1), (16.875, 0.35, -1)],
        build=(9.79, 13.375), calm_end=9.79,
        drop=16.875, drop_end=24.92,
        ski=(16.875, 2.6), snow=19.55,
        moon_riser=(23.0, 23.42),
        engine=(23.42, 0.9), passby=24.33,
        crowd=(24.92, 2.08),
        ending_hit=27.0, logo=28.55,
    ),
}

rnd = random.Random(7)
L = [0.0] * N
R = [0.0] * N


# ---------------------------------------------------------------- 기본 도구 (build_temp_audio.py 와 같은 합성 방식)
def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def add(start, samples, gain=1.0, pan=0.0):
    i0 = int(start * SR)
    gl = gain * math.cos((pan + 1) * math.pi / 4)
    gr = gain * math.sin((pan + 1) * math.pi / 4)
    for k, s in enumerate(samples):
        i = i0 + k
        if 0 <= i < N:
            L[i] += s * gl
            R[i] += s * gr


def env(n, a, d, s_level, r):
    out = []
    a_n, d_n, r_n = int(a * SR), int(d * SR), int(r * SR)
    sus_n = max(0, n - a_n - d_n - r_n)
    for i in range(n):
        if i < a_n:
            v = i / max(1, a_n)
        elif i < a_n + d_n:
            v = 1 - (1 - s_level) * (i - a_n) / max(1, d_n)
        elif i < a_n + d_n + sus_n:
            v = s_level
        else:
            v = s_level * max(0.0, 1 - (i - a_n - d_n - sus_n) / max(1, r_n))
        out.append(v)
    return out


def tone(freq, dur, harmonics=((1, 1.0),), a=0.01, d=0.1, s=0.7, r=0.2, vib=0.0):
    n = int(dur * SR)
    e = env(n, a, d, s, r)
    return [e[i] * sum(amp * math.sin(2 * math.pi * freq * (1 + vib * math.sin(2 * math.pi * 5 * i / SR)) * h * i / SR)
                       for h, amp in harmonics) for i in range(n)]


def bell(freq, dur, bright=1.0):
    n = int(dur * SR)
    parts = ((1.0, 1.0, 2.2), (2.0, 0.5 * bright, 3.5), (2.76, 0.35 * bright, 4.5), (5.4, 0.15 * bright, 7.0))
    return [min(1.0, i / (0.004 * SR)) * sum(a * math.exp(-k * i / SR) * math.sin(2 * math.pi * freq * m * i / SR) for m, a, k in parts)
            for i in range(n)]


def noise(dur, lp=0.2, hp=0.0, shape=None):
    n = int(dur * SR)
    out, y, yh, prev = [], 0.0, 0.0, 0.0
    for i in range(n):
        y += lp * (rnd.uniform(-1, 1) - y)
        v = y
        if hp:
            yh = hp * (yh + v - prev)
            prev = v
            v = yh
        out.append(v * (shape(i / n) if shape else 1.0))
    return out


def noise_sweep(dur, lp0, lp1, shape):
    """저역통과 계수를 lp0→lp1 로 바꾸는 노이즈 = 휙 지나가는 소리."""
    n = int(dur * SR)
    out, y = [], 0.0
    for i in range(n):
        k = i / n
        y += (lp0 + (lp1 - lp0) * k) * (rnd.uniform(-1, 1) - y)
        out.append(y * shape(k))
    return out


def sweep(f0, f1, dur, shape=lambda k: k, wave_fn=math.sin):
    n = int(dur * SR)
    out, ph = [], 0.0
    for i in range(n):
        k = i / n
        ph += 2 * math.pi * f0 * (f1 / f0) ** k / SR
        out.append(wave_fn(ph) * shape(k))
    return out


def saw(ph):
    return 2 * ((ph / (2 * math.pi)) % 1.0) - 1


def swell(x):
    return math.sin(math.pi * x) ** 2


KICK = [math.sin(2 * math.pi * (48 + 90 * math.exp(-i / (0.025 * SR))) * i / SR) * math.exp(-i / (0.14 * SR)) for i in range(int(0.45 * SR))]
HAT = noise(0.06, lp=0.9, hp=0.95, shape=lambda x: (1 - x) ** 4)
IMPACT = [math.sin(2 * math.pi * (36 + 60 * math.exp(-i / (0.05 * SR))) * i / SR) * math.exp(-i / (0.6 * SR)) for i in range(int(1.6 * SR))]
NOTI = [0.0] * int(1.1 * SR)
for _off, _n, _g in ((0.0, 88, 0.5), (0.11, 95, 0.45)):          # E6 → B6 (기존 알림음과 같은 소리)
    for _i, _v in enumerate(bell(midi(_n), 0.9, 0.8)):
        if int(_off * SR) + _i < len(NOTI):
            NOTI[int(_off * SR) + _i] += _g * _v
TAP = [math.sin(2 * math.pi * 1800 * i / SR) * math.exp(-i / (0.012 * SR)) for i in range(int(0.08 * SR))]


def riser(t0, t1, gain=0.12):
    d = max(0.1, t1 - t0)
    add(t0, sweep(midi(60), midi(88), d, shape=lambda x: x ** 2), gain * 0.6)
    add(t0, noise_sweep(d, 0.02, 0.6, shape=lambda x: x ** 2.5), gain * 2.5)


def whoosh(t, d, direction):
    add(t, noise_sweep(d, 0.03, 0.5, shape=swell), 0.9, 0.7 * direction)


def build_sfx(c):
    for t, pan in c["noti"]:
        add(t, NOTI, 0.55, pan)
    for t, pan in c["tap"]:
        add(t, TAP, 0.3, pan)
    sh = [0.0] * int(1.6 * SR)                                         # 빛이 퍼짐
    for k in range(4):
        for i, v in enumerate(sweep(midi(84 + k * 3), midi(96 + k * 3), 1.6, shape=swell)):
            sh[i] += v
    add(c["shimmer"], sh, 0.05)
    if c["play_hit"]:                                                   # ▶ → PLAY 폭발
        riser(c["play_hit"] - 0.6, c["play_hit"], 0.1)
        add(c["play_hit"], IMPACT, 0.45)
        add(c["play_hit"], bell(midi(76), 1.4, 1.1), 0.12)
    t0, d = c["bus"]                                                    # 버스 접근
    add(t0, noise(d, lp=0.08, shape=lambda x: math.sin(math.pi * min(1, x * 1.1)) ** 2), 0.9, 0.5)
    add(c["brake"], noise(0.45, lp=0.6, hp=0.9, shape=lambda x: (1 - x) ** 2), 0.22, 0.3)
    a, b = c["door"]                                                    # 문 빛
    riser(a, b, 0.14)
    add(b, [math.sin(2 * math.pi * 55 * i / SR) * math.exp(-i / (0.35 * SR)) for i in range(int(1.2 * SR))], 0.5)
    add(c["temple_bell"], bell(midi(45), 2.6, 0.5), 0.32, -0.1)         # 산사 종
    add(c["temple_bell2"], bell(midi(52), 1.8, 0.6), 0.24, 0.1)
    for t, dd, dr in c["whoosh"]:
        whoosh(t, dd, dr)
    t0, d = c["ski"]                                                    # 활강 · 바람
    add(t0, noise(d, lp=0.4, hp=0.3, shape=lambda x: 0.5 + 0.5 * math.sin(math.pi * x * 3) ** 2), 0.14, -0.1)
    add(t0 - 0.3, noise(d + 0.6, lp=0.05, shape=swell), 0.6, 0.4)
    add(c["snow"], noise_sweep(0.9, 0.7, 0.05, shape=lambda x: (1 - x) ** 1.5), 0.55)   # 급정지 눈보라
    add(c["snow"], IMPACT, 0.25)
    riser(*c["moon_riser"], 0.12)                                       # 별 → 헤드라이트
    t0, d = c["engine"]                                                 # 엔진 접근
    eng, y = [], 0.0
    for v in sweep(70, 190, d, shape=lambda x: 0.4 + 0.6 * x, wave_fn=saw):
        y += 0.15 * (v - y)
        eng.append(y)
    add(t0, eng, 0.4)
    whoosh(c["passby"], 0.7, 1)                                         # 통과
    add(c["passby"], IMPACT, 0.2)
    t0, d = c["crowd"]                                                  # 관중 함성

    def crowd_shape(x):
        return (0.4 + 0.6 * min(1, x * 3)) * (1 - max(0.0, x - 0.85) / 0.15)
    add(t0, noise(d, lp=0.25, hp=0.2, shape=crowd_shape), 0.35, -0.3)
    add(t0 + 0.05, noise(d, lp=0.25, hp=0.2, shape=crowd_shape), 0.35, 0.3)
    add(c["ending_hit"], IMPACT, 0.55)                                  # 엔딩 진입
    whoosh(c["ending_hit"] - 0.4, 0.5, -1)
    add(c["logo"], bell(midi(76), 2.0, 1.0), 0.22)                      # 로고
    for j, n in enumerate([79, 83, 88]):
        add(c["logo"] + 0.15 + j * 0.12, bell(midi(n), 1.2, 0.6), 0.05, -0.3 + j * 0.3)


PAD = ((1, 1.0), (2, 0.25), (3, 0.08))


def pad_chord(notes, start, dur, gain, a=1.2, r=1.5):
    for j, n in enumerate(notes):
        add(start, tone(midi(n), dur, PAD, a=a, d=0.3, s=0.9, r=r, vib=0.002), gain, -0.5 + j / max(1, len(notes) - 1))


def build_music(c):
    calm_end, (b0, b1), drop, drop_end, end = c["calm_end"], c["build"], c["drop"], c["drop_end"], c["ending_hit"]
    half = calm_end / 2                                                 # 현실(차분): Am9 → Fmaj7
    pad_chord([45, 57, 60, 64, 71], 0.0, half + 0.3, 0.035)
    pad_chord([41, 57, 60, 64, 69], half, calm_end - half + 0.6, 0.035)
    mid = (b0 + b1) / 2                                                 # 버스 · 문 빛(고조): Dsus2 → Esus4
    pad_chord([50, 57, 62, 64, 69], b0, mid - b0 + 0.3, 0.045, a=0.8)
    pad_chord([52, 59, 64, 69, 71], mid, b1 - mid + 0.2, 0.055, a=0.6, r=0.4)
    t = b0
    while t < b1 - 0.01:                                                # 반박 킥으로 긴장
        add(t, KICK, 0.12)
        t += BEAT * 2
    pad_chord([48, 60, 64, 67, 72], b1, drop - b1 + 0.4, 0.03, a=0.6, r=0.6)   # 산사 · 틸트(숨 고르기): C
    prog = [[48, 60, 64, 67, 72], [43, 59, 62, 67, 71], [45, 60, 64, 69, 72], [41, 60, 65, 69, 72]]   # 드롭: C G Am F (한 마디 = 4박 = 2초)
    k = 0
    t = drop
    while t < drop_end - 0.01:
        bar = int((t - drop) / (BEAT * 4)) % 4
        ch = prog[bar]
        if k % 4 == 0:
            pad_chord(ch, t, min(BEAT * 4, drop_end - t) + 0.2, 0.035, a=0.05, r=0.25)
            add(t, tone(midi(ch[0] - 12), BEAT * 4 * 0.95, ((1, 1.0), (2, 0.4)), a=0.01, d=0.2, s=0.7, r=0.1), 0.16)   # 베이스
        add(t, KICK, 0.4)
        add(t + BEAT / 2, HAT, 0.1, 0.3)
        for s in (0, 1):                                                # 8분 아르페지오
            n = ch[1:][(k * 2 + s) % 4] + 12
            add(t + s * BEAT / 2, tone(midi(n), BEAT / 2 * 0.9, ((1, 1.0), (2, 0.3)), a=0.004, d=0.07, s=0.35, r=0.06), 0.05, -0.3 + 0.6 * s)
        t += BEAT
        k += 1
    pad_chord([48, 60, 64, 67, 71], drop_end, end - drop_end + 0.3, 0.04, a=0.1, r=0.3)   # 야구장 → 엔딩 직전
    pad_chord([36, 48, 55, 64, 72, 76], end, DUR - end, 0.05, a=0.02, r=1.2)              # 엔딩 화음


def reverb(buf, mix=0.16):
    out = buf[:]
    for delay, fb in ((0.0297, 0.6), (0.0371, 0.58), (0.0411, 0.56), (0.0437, 0.54)):
        d = int(delay * SR)
        line = [0.0] * N
        for i in range(N):
            v = buf[i] + (line[i - d] * fb if i >= d else 0.0)
            line[i] = v
            out[i] += v * mix / 4
    return out


def main():
    global L, R
    key = sys.argv[1] if len(sys.argv) > 1 else "play"
    c = CUES[key]
    build_music(c)
    build_sfx(c)
    L, R = reverb(L), reverb(R)
    fade_n = int(0.7 * SR)
    for i in range(fade_n):
        g = 1 - i / fade_n
        L[N - fade_n + i] *= g
        R[N - fade_n + i] *= g
    peak = max(max(abs(v) for v in L), max(abs(v) for v in R)) or 1.0
    k = 0.89 / peak
    path = os.path.join(HERE, c["out"])
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        fr = bytearray()
        for a, b in zip(L, R):
            fr += struct.pack("<hh", int(max(-1.0, min(1.0, a * k)) * 32767), int(max(-1.0, min(1.0, b * k)) * 32767))
        w.writeframes(bytes(fr))
    print(f"[audio] {key} → {path}")


if __name__ == "__main__":
    main()
