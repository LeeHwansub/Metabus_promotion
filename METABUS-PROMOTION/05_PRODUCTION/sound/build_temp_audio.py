"""
metaBus 30초 홍보영상 임시 사운드 (가이드용) — 파이썬 표준 라이브러리만 사용

실행:  /opt/homebrew/bin/python3.12 build_temp_audio.py
출력:  temp_mix_30s.wav   (48 kHz / 16 bit / stereo, 음량 미조정 — ffmpeg-skill loudness.py 로 -14 LUFS)
       notification.wav   (알림음 단독 — S01 두 번, 엔딩 E01 에서 같은 소리)

타임라인은 03_STORYBOARD/storyboard.json (v0.6, 14컷) 기준.
모든 소리는 합성한 임시음이며, 실제 음원(라이선스 확보)으로 교체할 때 같은 타이밍을 쓴다.
"""
import math
import os
import random
import struct
import wave

SR = 48000
DUR = 30.0
N = int(SR * DUR)
HERE = os.path.dirname(os.path.abspath(__file__))
rnd = random.Random(7)

L = [0.0] * N
R = [0.0] * N


# ---------------------------------------------------------------- 기본 도구
def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def add(start, samples, gain=1.0, pan=0.0):
    """mono samples 를 start(초) 위치에 pan(-1..1) 으로 더함."""
    i0 = int(start * SR)
    gl = gain * math.cos((pan + 1) * math.pi / 4)
    gr = gain * math.sin((pan + 1) * math.pi / 4)
    for k, s in enumerate(samples):
        i = i0 + k
        if 0 <= i < N:
            L[i] += s * gl
            R[i] += s * gr


def env(n, a, d, s_level, r):
    """ADSR (초 단위) → 길이 n 의 배열."""
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
    out = []
    for i in range(n):
        t = i / SR
        f = freq * (1 + vib * math.sin(2 * math.pi * 5 * t))
        out.append(e[i] * sum(amp * math.sin(2 * math.pi * f * h * t) for h, amp in harmonics))
    return out


def bell(freq, dur, bright=1.0):
    """비화성 배음 + 지수 감쇠 = 벨/차임."""
    n = int(dur * SR)
    parts = ((1.0, 1.0, 2.2), (2.0, 0.5 * bright, 3.5), (2.76, 0.35 * bright, 4.5), (5.4, 0.15 * bright, 7.0))
    out = []
    for i in range(n):
        t = i / SR
        att = min(1.0, i / (0.004 * SR))
        out.append(att * sum(a * math.exp(-k * t) * math.sin(2 * math.pi * freq * m * t) for m, a, k in parts))
    return out


def noise(dur, lp=0.2, hp=0.0, shape=None):
    """필터 노이즈. lp/hp: one-pole 계수(0..1), shape(t_norm)->gain."""
    n = int(dur * SR)
    out, y, yh, prev = [], 0.0, 0.0, 0.0
    for i in range(n):
        y += lp * (rnd.uniform(-1, 1) - y)    # low-pass
        v = y
        if hp:
            yh = hp * (yh + v - prev)         # high-pass
            prev = v
            v = yh
        out.append(v * (shape(i / n) if shape else 1.0))
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


# ---------------------------------------------------------------- 알림음 (동일 사운드 3회)
def notification():
    out = [0.0] * int(1.1 * SR)
    for off, n, g in ((0.0, 88, 0.5), (0.11, 95, 0.45)):   # E6 → B6
        o = int(off * SR)
        for i, v in enumerate(bell(midi(n), 0.9, 0.8)):
            if o + i < len(out):
                out[o + i] += g * v
    return out


NOTI = notification()
for t, pan in ((2.3, -0.2), (5.8, 0.2), (25.15, 0.0)):   # S01_C01, S01_C02, 엔딩 E01
    add(t, NOTI, 0.55, pan)

# ---------------------------------------------------------------- 효과음
tap = [math.sin(2 * math.pi * 1800 * i / SR) * math.exp(-i / (0.012 * SR)) for i in range(int(0.08 * SR))]
add(8.85, tap, 0.25, -0.3)                                 # S02_C02-A 참여하기
add(9.55, tap, 0.25, 0.3)                                  # S02_C02-B 참여하기

shimmer = [0.0] * int(2.4 * SR)                            # 빛이 퍼짐 (상승 반짝임)
for k in range(4):
    for i, v in enumerate(sweep(midi(84 + k * 3), midi(96 + k * 3), 2.4, shape=swell)):
        shimmer[i] += v
add(9.7, shimmer, 0.05)

add(11.9, noise(1.6, lp=0.08, shape=lambda x: math.sin(math.pi * min(1, x * 1.2)) ** 2), 0.9, 0.6)   # 버스 도착
add(12.4, noise(1.2, lp=0.08, shape=swell), 0.6, -0.2)
add(13.15, noise(0.5, lp=0.6, hp=0.9, shape=lambda x: (1 - x) ** 2), 0.25, 0.3)                     # 정차 브레이크

add(13.28, sweep(midi(60), midi(84), 0.75, shape=lambda x: x ** 2), 0.18)                           # 문이 열리며 빛
add(13.28, noise(0.75, lp=0.3, hp=0.5, shape=lambda x: x ** 3), 0.5)
add(14.0, [math.sin(2 * math.pi * 55 * i / SR) * math.exp(-i / (0.35 * SR)) for i in range(int(1.2 * SR))], 0.5)
add(14.0, bell(midi(72), 1.6, 1.2), 0.18)

add(14.35, bell(midi(45), 2.5, 0.5), 0.3, -0.1)                                                    # 산사 종
add(15.5, noise(4.0, lp=0.05, shape=lambda x: 0.3 + 0.7 * math.sin(math.pi * x)), 0.7, -0.4)        # 스키장 바람
add(15.7, noise(3.6, lp=0.05, shape=lambda x: 0.3 + 0.7 * math.sin(math.pi * x)), 0.7, 0.4)
add(17.0, noise(2.4, lp=0.4, hp=0.3, shape=lambda x: 0.5 + 0.5 * math.sin(math.pi * x * 3) ** 2), 0.12, -0.1)  # 활강

engine, y = [], 0.0                                                                                 # 레이싱 엔진
for v in sweep(70, 160, 2.5, shape=lambda x: 0.6 + 0.4 * x, wave_fn=saw):
    y += 0.15 * (v - y)
    engine.append(y)
add(19.5, engine, 0.35)
add(20.6, noise(0.6, lp=0.1, shape=swell), 0.8, 0.8)                                               # 지나가는 바람


def crowd_shape(x):
    return (0.4 + 0.6 * min(1, x * 2)) * (1 - max(0.0, x - 0.85) / 0.15)


add(21.9, noise(3.2, lp=0.25, hp=0.2, shape=crowd_shape), 0.35, -0.3)                              # 관중 함성
add(22.0, noise(3.1, lp=0.25, hp=0.2, shape=crowd_shape), 0.35, 0.3)

add(25.8, sweep(midi(79), midi(91), 0.6, shape=lambda x: math.sin(math.pi * x)), 0.08)             # E02 카드
add(26.9, noise(0.9, lp=0.1, shape=swell), 0.6, -0.5)                                              # E03 버스 전환
add(28.45, bell(midi(76), 2.0, 1.0), 0.22)                                                         # E04 로고

# ---------------------------------------------------------------- 음악 (100 BPM)
BEAT = 60 / 100
PAD = ((1, 1.0), (2, 0.25), (3, 0.08))


def pad_chord(notes, start, dur, gain, a=1.2, r=1.5):
    for j, n in enumerate(notes):
        add(start, tone(midi(n), dur, PAD, a=a, d=0.3, s=0.9, r=r, vib=0.002), gain, -0.5 + j / max(1, len(notes) - 1))


pad_chord([45, 57, 60, 64, 71], 0.0, 5.2, 0.035)           # 0–10초: Am9 → Fmaj7 (차분)
pad_chord([41, 57, 60, 64, 69], 5.0, 5.2, 0.035)
pad_chord([50, 57, 62, 64, 69], 10.0, 2.2, 0.045, a=0.8)   # 10–14초: Dsus2 → Esus4 (크레셴도)
pad_chord([52, 59, 64, 69, 71], 12.0, 2.2, 0.055, a=0.6, r=0.4)
prog = [(14.0, [48, 60, 64, 67, 72]), (16.4, [43, 59, 62, 67, 71]), (18.8, [45, 60, 64, 69, 72]), (21.2, [41, 60, 65, 69, 72])]
for i, (st, ch) in enumerate(prog):                        # 14–25초: C → G → Am → F + 아르페지오
    end = prog[i + 1][0] if i + 1 < len(prog) else 25.0
    pad_chord(ch, st, end - st + 0.3, 0.04, a=0.2, r=0.3)
    t, k = st, 0
    while t < end - 0.01:
        n = ch[1:][k % 4] + (12 if (k // 4) % 2 else 0)
        add(t, tone(midi(n), BEAT / 2 * 0.9, ((1, 1.0), (2, 0.3)), a=0.005, d=0.08, s=0.4, r=0.08), 0.06, -0.3 + 0.6 * (k % 2))
        t += BEAT / 2
        k += 1
kick = [math.sin(2 * math.pi * (50 + 80 * math.exp(-i / (0.03 * SR))) * i / SR) * math.exp(-i / (0.12 * SR)) for i in range(int(0.4 * SR))]
t = 14.0
while t < 25.0:                                            # 펄스 (17초부터 강하게)
    add(t, kick, 0.35 if t >= 17.0 else 0.2)
    t += BEAT
pad_chord([48, 60, 64, 67, 71], 25.0, 3.6, 0.035, a=0.4, r=0.8)       # 25–30초: 엔딩
for j, n in enumerate([72, 76, 79, 83]):
    add(25.9 + j * 0.3, bell(midi(n), 1.5, 0.6), 0.05, -0.4 + j * 0.27)
pad_chord([36, 48, 55, 64, 72], 28.4, 1.6, 0.05, a=0.3, r=1.4)


# ---------------------------------------------------------------- 마스터: 간단 리버브 + 페이드 + 정규화
def reverb(buf, mix=0.18):
    out = buf[:]
    for delay, fb in ((0.0297, 0.6), (0.0371, 0.58), (0.0411, 0.56), (0.0437, 0.54)):
        d = int(delay * SR)
        line = [0.0] * N
        for i in range(N):
            v = buf[i] + (line[i - d] * fb if i >= d else 0.0)
            line[i] = v
            out[i] += v * mix / 4
    return out


L, R = reverb(L), reverb(R)
fade_n = int(0.6 * SR)
for i in range(fade_n):                                    # 마지막 0.6초 페이드아웃 (엔딩 화면 페이드와 맞춤)
    g = 1 - i / fade_n
    L[N - fade_n + i] *= g
    R[N - fade_n + i] *= g


def write(path, left, right, peak_target):
    peak = max(max(abs(v) for v in left), max(abs(v) for v in right)) or 1.0
    k = peak_target / peak
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        frames = bytearray()
        for a, b in zip(left, right):
            frames += struct.pack("<hh", int(max(-1.0, min(1.0, a * k)) * 32767), int(max(-1.0, min(1.0, b * k)) * 32767))
        w.writeframes(bytes(frames))


write(os.path.join(HERE, "temp_mix_30s.wav"), L, R, 0.89)          # 약 -1 dBFS (최종 음량은 loudness.py)
write(os.path.join(HERE, "notification.wav"), NOTI, NOTI, 0.7)
print(f"[audio] wrote temp_mix_30s.wav ({DUR}s) and notification.wav")
