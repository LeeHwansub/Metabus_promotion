"""
metaBus V02 전체 프리비즈 30초 (S01~S05 13컷, 엔딩 제외) — Newtake 한 번에 생성용 영상 레퍼런스
V02 26초(엔딩 앞) 타이밍을 30/26 배로 늘려 30초에 배치. 편집 때 컷마다 잘라 26초 + 모션그래픽 엔딩.

실행:
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      -P build_previs_v02_full.py -- [--render <frames_dir>] [--frames 10,100]

모션그래픽(play_30s_v2 · v3 샘플) 구조에 맞춘 구도:
  폰 화면 정면·가운데(카드/PLAY 폭발) · 버스 전면 정면(LED) · 문 빛이 화면을 덮음 · 틸트 위 빈 하늘 ·
  스키 인물 뒤 빈 공간+눈보라가 렌즈를 덮음 · 왼→오 흐름 · 달 끝/레이싱 시작 빛나는 점이 가운데 ·
  야구장 세 명 위 관중석 · 주요 피사체 가운데(9:16)
세트: v0.6 build_previs.py(공부방·정류장·폰·버스·산사 마당) + build_previs_v02_s05.py(체험 5장면)
"""
import bpy
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PREVIS_DIR = os.environ.get("PREVIS_DIR", os.path.dirname(HERE))  # 03_STORYBOARD/previs (build_previs.py 위치)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


bp = load("bp", os.path.join(PREVIS_DIR, "build_previs.py"))
s5 = load("s5", os.path.join(HERE, "build_previs_v02_s05.py"))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
FPS = bp.FPS
SCALE = 30 / 26


def T(v02_sec):
    """V02 시간(초) → 30초 프리비즈 시간."""
    return v02_sec * SCALE


def fr(sec):
    return int(round(sec * FPS)) + 1


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, 30 * FPS
    font = bpy.data.fonts.load(bp.FONT_KR)
    RX, SX, PCX, MX, TX = 0, 40, -30, 90, 200
    room = bp.set_room(RX)
    stop = bp.set_busstop(SX)
    bp.set_phone_closeup(PCX, font)
    bp.set_magic_stop(MX)
    temple = bp.set_temple(TX)
    w = bpy.data.worlds.new("v02_full_world"); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    cams = []

    def cut(label, s0, s1, loc0, tgt0, loc1=None, tgt1=None, lens=35, sky=("#1A2230", .4)):
        cam = bp.camera("CAM_" + label, loc0, tgt0, lens)
        bp.cam_move(cam, fr(s0), fr(s1), loc0, tgt0, loc1 or loc0, tgt1 or tgt0)
        bp.linear(cam)
        cams.append((label, s0, cam, sky))
        return cam

    # ---------------- S01 반복되는 일상 (V02 0–6)
    cut("S01_C01_seoyun_room", T(0), T(3), (RX + .95, 2.0, 1.42), (RX + .7, .75, 1.12), (RX + .75, 1.7, 1.38), (RX + .6, .75, 1.14), 45)
    ph = stop["phone"].location
    c = cut("S01_C02_junho_stop", T(3), T(5.3), (SX - 3.6, -3.4, 1.15), (SX - 1.4, 1.8, 1.45), (SX - 2.6, -2.6, 1.2), (SX - 1.2, 1.8, 1.45), 35)
    bp.cam_move(c, fr(T(5.3)), fr(T(6)), (SX - 2.6, -2.6, 1.2), (SX - 1.2, 1.8, 1.45), (ph.x + .2, ph.y - .55, ph.z + .12), tuple(ph))  # 폰으로 접근
    # ---------------- S02 초대 (V02 6–9): 폰 화면 정면·가운데
    cut("S02_C01_phone_front", T(6), T(7.5), (PCX, .15, 1.7), (PCX, .15, 0), (PCX, .15, 1.45), (PCX, .15, 0), 50, ("#14161C", .3))
    pr, ps = room["phone"].location, stop["phone"].location
    cut("S02_C02A_tap_seoyun", T(7.5), T(8.25), (pr.x + .18, pr.y - .32, pr.z + .38), (pr.x, pr.y + .03, pr.z), lens=50)
    cut("S02_C02B_tap_junho", T(8.25), T(9), (ps.x + .25, ps.y - .75, ps.z - .15), (ps.x - .05, ps.y + .25, ps.z + .3),
        (ps.x + .18, ps.y - .55, ps.z - .1), (ps.x - .05, ps.y + .25, ps.z + .3), 50)
    for lo in (room["fill"], stop["fill"]):                                  # 참여 순간 빛이 퍼짐
        bp.energy_key(lo, fr(T(8.3)), lo.data.energy); bp.energy_key(lo, fr(T(9)), lo.data.energy * 8)
    # ---------------- S03 셔틀 (V02 9–13): 버스 전면 정면 로우앵글 → 마스코트 환영 · 문 빛
    BY = 4.6
    cut("S03_C01_bus_front", T(9), T(11), (MX - 16, BY - .3, .7), (MX + 6, BY, 1.6), (MX - 13, BY - .3, .65), (MX + 3, BY, 1.6), 35, ("#0C0C6C", .8))
    cut("S03_C02_mascot_door", T(11), T(13), (MX - 4.4, -1.9, .5), (MX - 1.6, 4.2, 1.9), (MX - 3.6, -1.5, .55), (MX - 2.0, 3.6, 1.7), 28, ("#0C0C6C", .8))
    door = bp.light("door_burst", "AREA", (MX - 2.1, 3.0, 1.4), "#FFE6C0", 0, rot=(-90, 0, 0), size=2.5)
    bp.energy_key(door, fr(T(12.2)), 0); bp.energy_key(door, fr(T(13)), 6000)
    # ---------------- S04 새로운 캐릭터 (V02 13–17): 산사 마당 → 염주 손 POV → 틸트업(하늘) → [컷] → 틸트다운 → 슬로프 꼭대기 서윤
    cut("S04_C01_temple_yard", T(13), T(15), (TX - 2.2, -6.5, 1.5), (TX + .3, 1, 1.4), (TX - 1.8, -5.6, 1.5), (TX + .3, 1, 1.4), 35, ("#FFD8A8", 1.2))
    tp = temple["pov"]
    hands = (tp[0], tp[1] + .32, tp[2] - .42)
    c = bp.camera("CAM_S04_C02a_pov_tiltup", tp, hands, 24)
    bp.cam_move(c, fr(T(15)), fr(T(15.6)), tp, hands, tp, hands)
    bp.cam_move(c, fr(T(15.6)), fr(T(16)), tp, hands, tp, (tp[0], tp[1] + 2, tp[2] + 12))       # 하늘로
    cams.append(("S04_C02a_pov_tiltup", T(15), c, ("#FFD8A8", 1.2)))
    # ---------------- S05 체험 (V02 17–26) — 체험 세트(1000~)의 스키 꼭대기를 S04 끝 공개에도 사용
    KX = 1000
    sz = lambda y: 10 - y * 0.2679
    c = bp.camera("CAM_S04_C02b_tiltdown", (KX + 3.5, -11, sz(-11) + 1.6), (KX, -8, sz(-8) + 12), 30)
    bp.cam_move(c, fr(T(16)), fr(T(16.45)), (KX + 3.5, -11, sz(-11) + 1.6), (KX, -8, sz(-8) + 12), (KX + 3.5, -11, sz(-11) + 1.6), (KX, -8, sz(-8) + 1.0))
    cams.append(("S04_C02b_tiltdown_skier", T(16), c, ("#BFDFFF", 1.5)))
    exp = [(s5.set_ski, KX, 17, 19, ("#BFDFFF", 1.5)), (s5.set_temple_hall, 1200, 19, 20.5, ("#3A2418", .6)),
           (s5.set_moon, 1400, 20.5, 22.5, ("#02030A", .2)), (s5.set_race, 1600, 22.5, 24, ("#FFB070", 1.2)),
           (s5.set_stadium, 1900, 24, 26, ("#14144A", .6))]
    for fn, ox, a, b, sky in exp:
        s5.PER = T(b) - T(a)                                                 # 장면 길이(체험 세트 함수가 참조)
        cam = fn(ox, T(a))
        cams.append((fn.__name__, T(a), cam, sky))
    # 달 끝: 별 하나가 가운데에서 커짐 → 레이싱 헤드라이트 (빛의 매치 컷)
    star = bp.add("sphere", "v_match_star", (1400 + .4, 9, 2.2), (.05, .05, .05), material=bp.mat("v_star", "#FFFFFF", 40))
    bp.scale_key(star, fr(T(21.6)), .05); bp.scale_key(star, fr(T(22.5)), .9)

    # 하드컷: 마커마다 카메라, 하늘색 즉시 전환
    for label, s0, cam, (col, st) in cams:
        m = sc.timeline_markers.new(label, frame=fr(s0)); m.camera = cam
        bg.inputs["Color"].default_value = bp.hex_rgba(col); bg.inputs["Strength"].default_value = st
        bg.inputs["Color"].keyframe_insert("default_value", frame=fr(s0)); bg.inputs["Strength"].keyframe_insert("default_value", frame=fr(s0))
    for fc in bp.iter_fcurves(w.node_tree):
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"
    sc.camera = cams[0][2]
    r = sc.render
    r.engine = "BLENDER_EEVEE"
    r.resolution_x, r.resolution_y, r.resolution_percentage = 1280, 720, 100
    if hasattr(sc, "eevee") and hasattr(sc.eevee, "taa_render_samples"):
        sc.eevee.taa_render_samples = 8
    r.use_stamp = False
    r.image_settings.file_format = "PNG"
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "previs_v02_full_30s.blend"))
    print(f"[previs_v02_full] cuts={len(cams)} frames={sc.frame_end}")
    for label, s0, _, _ in cams:
        print(f"  {s0:6.2f}s  f{fr(s0):4d}  {label}")
    return sc


if __name__ == "__main__":
    scene = build()
    if "--render" in argv:
        out = argv[argv.index("--render") + 1]
        os.makedirs(out, exist_ok=True)
        if "--frames" in argv:
            for f_ in map(int, argv[argv.index("--frames") + 1].split(",")):
                scene.frame_set(f_)
                scene.render.filepath = os.path.join(out, f"test_{f_:04d}")
                bpy.ops.render.render(write_still=True)
        else:
            scene.render.filepath = os.path.join(out, "f_")
            bpy.ops.render.render(animation=True)
