"""
metaBus V02 체험 몽타주 프리비즈 (S05: 스키 → 산사 → 달 → 레이싱 → 야구장)
Newtake(Seedance 2.5) 영상 레퍼런스용 — 카메라 · 타이밍 · 움직임 · 하드컷만 지시하는 회색 블로킹

실행:
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      -P build_previs_v02_s05.py -- [--per 6] [--render <frames_dir>] [--frames 10,100]

- --per: 장면당 초 (기본 6 → 30초, 3 → 15초)
- 기존 previs/build_previs.py 의 도형 · 재질 · 사람 · 마스코트 · 카메라 함수를 그대로 가져다 쓴다.
  (스키 · 레이싱 · 야구장 세트는 v0.6 시간표 애니메이션 키가 들어 있어 여기서 새로 블로킹)
- AI 레퍼런스에 글자가 섞이지 않도록 렌더 스탬프는 끈다.
- 움직임 원칙: 동작 중 하드컷, 화면 왼→오 흐름, 컷 끝으로 갈수록 가속.
"""
import bpy
import importlib.util
import math
import os
import sys

PREVIS_DIR = os.environ.get("PREVIS_DIR", "/Users/USER/Projects/NewTake/METABUS-PROMOTION/03_STORYBOARD/previs")
spec = importlib.util.spec_from_file_location("bp", os.path.join(PREVIS_DIR, "build_previs.py"))
bp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bp)
add, mat, person, mascot, light, camera, cam_move, loc_key, empty, hex_rgba = (
    bp.add, bp.mat, bp.person, bp.mascot, bp.light, bp.camera, bp.cam_move, bp.loc_key, bp.empty, bp.hex_rgba)
FPS = bp.FPS

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
PER = float(argv[argv.index("--per") + 1]) if "--per" in argv else 6.0


def fr(sec):
    return int(round(sec * FPS)) + 1


def rot_key(o, frame, rot_deg):
    o.rotation_euler = tuple(math.radians(a) for a in rot_deg)
    o.keyframe_insert("rotation_euler", frame=frame)


def child(root, suffix):
    return next(c for c in root.children if c.name.endswith(suffix))


# ---------------------------------------------------------------- 세트
def set_ski(ox, t0):
    """① 스키: 화면 왼→오 활강(+Y) → 급정지 → 눈이 카메라 쪽으로 튐."""
    deg = 15
    sz = lambda y: 10 - y * math.tan(math.radians(deg))
    add("plane", "v_ski_slope", (ox, 10, sz(10)), (14, 30, 1), rot=(-deg, 0, 0), material=mat("v_snow", "#F4F8FF", rough=.3))
    for i, dx in enumerate((-30, -14, 16, 32)):
        add("cone", f"v_mtn_{i}", (ox + dx - 40, 30 + i * 12, -5), (16, 16, 20 + i % 2 * 6), material=mat("v_mtn", "#DDE6F2"))
    for i in range(14):  # 옆을 스치는 나무·깃발 = 속도감
        y = -10 + i * 3.2
        add("cone", f"v_tree_{i}", (ox - 3.5 - (i % 3), y, sz(y) + 1.2), (.7, .7, 1.6), material=mat("v_tree", "#2F5A45"))
        add("cyl", f"v_flag_{i}", (ox + 2.2, y + 1.6, sz(y + 1.6) + .6), (.04, .04, .6), material=mat("v_flag", "#FCC024", 2))
    light("v_ski_sun", "SUN", (ox, 0, 30), "#FFF2D6", 5, rot=(45, 0, 20))
    sk = person("v_skier", (ox, -8, sz(-8)), "#B7A6E8", "#E8E4F4", height=1.6)
    add("cube", "v_skis", (ox, -8, sz(-8) + .03), (.18, .9, .02), material=mat("v_ski", "#222222"), parent=sk)
    d = PER
    keys = [(0, -8), (.55, 6), (.72, 10), (.82, 11.2), (1.0, 11.6)]          # 가속 → 급정지
    for u, y in keys:
        loc_key(sk, fr(t0 + u * d), (ox, y, sz(y)))
    rot_key(sk, fr(t0 + .7 * d), (0, 0, 0))
    rot_key(sk, fr(t0 + .8 * d), (0, -8, -70))                              # 옆으로 틀며 멈춤 (카빙 스톱)
    for i in range(36):                                                     # 튀는 눈 덩어리 → 카메라 쪽(+X)으로
        sx, sy = (i % 6) * .25 - .6, (i // 6) * .25 - .6
        sn = add("sphere", f"v_spray_{i}", (ox, 11.2 + sy, sz(11.2) + .2), (.12, .12, .12), material=mat("v_spray", "#FFFFFF", 1.5))
        bp.scale_key(sn, 1, .001); bp.scale_key(sn, fr(t0 + .76 * d), .001)
        loc_key(sn, fr(t0 + .76 * d), (ox, 11.2 + sy, sz(11.2) + .2))
        bp.scale_key(sn, fr(t0 + .8 * d), .4 + (i % 4) * .15)
        loc_key(sn, fr(t0 + d), (ox + 4.5 + (i % 5) * .3, 11.2 + sy * 3, sz(11.2) + .6 + sx * 2))
        bp.scale_key(sn, fr(t0 + d), 1.6 + (i % 3) * .5)
    cam = camera("CAM_ski", (ox + 5, -10, sz(-10) + 1.4), (ox, -7, sz(-7) + 1), 35)
    tgt = empty("CAM_ski_target", (ox, -8, sz(-8) + 1))
    c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
    for u, y in keys:                                                        # 옆에서 같은 속도로 따라감
        cam.location = (ox + 5, y - 2.2, sz(y) + 1.5); cam.keyframe_insert("location", frame=fr(t0 + u * d))
        loc_key(tgt, fr(t0 + u * d), (ox, y + .8, sz(y) + 1))
    return cam


def set_temple_hall(ox, t0):
    """② 산사 법당: 합장 → 숙여 절 (측면 미디엄, 천천히 접근)."""
    add("plane", "v_floor", (ox, 0, 0), (10, 10, 1), material=mat("v_wood_floor", "#7A5534"))
    add("cube", "v_back_wall", (ox, 6, 3), (10, .2, 3), material=mat("v_wall", "#8A3B2A"))
    for i, dx in enumerate((-4, 4)):
        add("cyl", f"v_pillar_{i}", (ox + dx, 3, 3), (.3, .3, 3), material=mat("v_pillar", "#B0402E"))
    add("cube", "v_altar", (ox, 4.6, .5), (2.2, .8, .5), material=mat("v_altar", "#5A2A1A"))
    add("sphere", "v_buddha_body", (ox, 4.8, 1.9), (1.0, .8, 1.0), material=mat("v_gold", "#E0B04A", 1.2, rough=.25))
    add("sphere", "v_buddha_head", (ox, 4.8, 3.3), (.5, .5, .55), material=mat("v_gold", "#E0B04A", 1.2, rough=.25))
    for i, dx in enumerate((-1.6, 1.6)):
        add("sphere", f"v_lantern_{i}", (ox + dx, 3.5, 4.2), (.3, .3, .3), material=mat("v_lantern", "#FF9EB5", 3))
    light("v_temple_warm", "POINT", (ox, 2, 3), "#FFD8A0", 800)
    mk = person("v_monk", (ox, 1.5, 0), "#5A5A5A", "#7A7A7A", hair="#1A1A1A")
    d = PER
    torso, head, hair = child(mk, "_torso"), child(mk, "_head"), child(mk, "_hair")
    for o in (torso, head, hair):
        loc_key(o, fr(t0 + .45 * d), tuple(o.location))
    loc_key(torso, fr(t0 + .8 * d), (torso.location.x, torso.location.y + .18, torso.location.z - .1))   # 앞으로 숙임
    loc_key(head, fr(t0 + .8 * d), (head.location.x, head.location.y + .42, head.location.z - .38))
    loc_key(hair, fr(t0 + .8 * d), (hair.location.x, hair.location.y + .42, hair.location.z - .38))
    hands = add("cube", "v_palms", (ox, 1.3, 1.25), (.05, .05, .14), material=mat("v_skin", "#E8C4A0"), parent=mk)
    loc_key(hands, fr(t0 + .45 * d), (ox, 1.3, 1.25)); loc_key(hands, fr(t0 + .8 * d), (ox, 1.55, .95))
    # 비스듬한 측면: 앞쪽에 합장하는 준호(왼쪽 1/3), 뒤쪽에 불상이 함께 보이도록
    cam = camera("CAM_temple", (ox - 4.2, -3.2, 1.5), (ox + .3, 3.2, 1.6), 35)
    cam_move(cam, fr(t0), fr(t0 + d), (ox - 4.2, -3.2, 1.5), (ox + .3, 3.2, 1.6), (ox - 3.4, -2.4, 1.45), (ox + .2, 3.0, 1.5))
    bp.linear(cam)
    return cam


def set_moon(ox, t0):
    """③ 달: 가볍게 점프 → 무중력으로 떠오르며 천천히 회전, 멀리 지구."""
    add("plane", "v_moon_ground", (ox, 0, 0), (30, 30, 1), material=mat("v_moon", "#9A9AA0", rough=.95))
    for i in range(18):
        add("sphere", f"v_crater_{i}", (ox - 12 + (i * 7) % 24, -6 + (i * 5) % 20, -.15), (.8 + i % 3 * .4, .8 + i % 3 * .4, .25),
            material=mat("v_crater", "#7C7C84"))
    add("sphere", "v_earth", (ox + 22, 70, 14), (4.5, 4.5, 4.5), material=mat("v_earth", "#3C7BD9", 1.5))
    light("v_moon_sun", "SUN", (ox, 0, 20), "#FFFFFF", 4, rot=(40, 0, -40))
    a = person("v_astro", (ox, 2, 0), "#EEEEF4", "#EEEEF4", height=1.6)
    add("sphere", "v_helmet", (ox, 2, 1.45), (.22, .22, .22), material=mat("v_glass", "#CFE4FF", .3, rough=.05), parent=a)
    d = PER
    loc_key(a, fr(t0), (ox, 2, 0)); loc_key(a, fr(t0 + .2 * d), (ox, 2, 0))
    loc_key(a, fr(t0 + d), (ox + .6, 2, 1.8))
    rot_key(a, fr(t0 + .2 * d), (0, 0, 0)); rot_key(a, fr(t0 + d), (18, -12, 40))
    # 우주인을 크게(미디엄 와이드) → 떠오르며 점점 넓어짐, 지구는 오른쪽 위
    cam = camera("CAM_moon", (ox - .6, -2.4, 1.0), (ox + .4, 2, 1.0), 35)
    cam_move(cam, fr(t0), fr(t0 + d), (ox - .6, -2.4, 1.0), (ox + .4, 2, 1.0), (ox - 1.2, -4.6, 1.6), (ox + .8, 2, 1.9))
    bp.linear(cam)
    return cam


def set_race(ox, t0):
    """④ 레이싱: 헤드라이트가 다가옴 → 렌즈 바로 앞을 오른쪽→왼쪽으로 통과."""
    add("plane", "v_track", (ox, 0, 0), (140, 7, 1), material=mat("v_track", "#2A2A30"))
    add("plane", "v_grass", (ox, -14, -.01), (140, 7, 1), material=mat("v_grass", "#3E6A3E"))
    for i in range(46):
        c = "#E03C3C" if i % 2 else "#F4F4F4"
        add("cube", f"v_curb_{i}", (ox - 130 + i * 6, 7.1, .1), (1.5, .15, .1), material=mat("v_curb" + c, c))
        add("cube", f"v_stand_{i}", (ox - 130 + i * 6, 12, 2), (2.8, 1.5, 2), material=mat("v_stand", "#4A4A6A"))
    car = empty("v_car", (ox + 70, 0, 0))
    add("cube", "v_car_body", (ox + 70, 0, .45), (2.3, .95, .32), material=mat("v_car_white", "#F2F2F6", rough=.2), parent=car)
    add("cube", "v_car_stripe", (ox + 70, 0, .78), (2.3, .3, .02), material=mat("v_car_blue", "#2E56D9"), parent=car)
    for i, dy in enumerate((-.65, .65)):
        add("sphere", f"v_headlight_{i}", (ox + 67.8, dy, .5), (.28, .28, .18), material=mat("v_head", "#FFFFFF", 40), parent=car)
    light("v_race_sun", "SUN", (ox, 0, 20), "#FFB070", 3, rot=(75, 0, -60))
    d = PER
    # 차 원점(ox+70)에서 몸체가 만들어졌으므로 이동량으로 키를 잡는다: 38m 앞에서 출발 → 렌즈 앞 통과
    car.location = (ox + 38, 0, 0); car.keyframe_insert("location", frame=fr(t0))
    loc_key(car, fr(t0 + .65 * d), (ox + 12, 0, 0)); loc_key(car, fr(t0 + .85 * d), (ox - 12, 0, 0))
    loc_key(car, fr(t0 + d), (ox - 40, 0, 0))
    cam = camera("CAM_race", (ox, -2.6, .55), (ox + 25, .3, .6), 28)
    cam_move(cam, fr(t0), fr(t0 + .6 * d), (ox, -2.6, .55), (ox + 25, .3, .6), (ox, -2.4, .5), (ox + 20, .3, .55))
    return cam


def set_stadium(ox, t0):
    """⑤ 야구장: 세 명이 응원봉을 흔들고 꽃가루, 카메라가 밀고 들어감."""
    add("plane", "v_field", (ox, -10, 0), (30, 20, 1), material=mat("v_field", "#2F7A3A"))
    add("cube", "v_dome", (ox, 10, 14), (40, 20, .3), material=mat("v_dome", "#20205A"))
    for tier in range(7):
        add("cube", f"v_tier_{tier}", (ox, 2 + tier * 1.4, .4 + tier * .8), (30, .7, .4), material=mat("v_tier", "#3C30B4"))
        for i in range(26):
            c = ["#F4F4F4", "#6060E4", "#FCC024"][(i + tier) % 3]
            add("cyl", f"v_fan_{tier}_{i}", (ox - 25 + i * 2, 2 + tier * 1.4, 1.2 + tier * .8), (.2, .2, .4), material=mat("v_fan" + c, c), vertices=8)
    light("v_flood", "AREA", (ox, -6, 12), "#FFF6E0", 4000, rot=(-30, 0, 0), size=20)
    d = PER
    for name, dx in (("v_seoyun", -.75), ("v_junho", .75)):
        p = person(name, (ox + dx, 0, 0), "#F4F4F4", "#20306A", height=1.6 if "seoyun" in name else 1.7)
        st = add("cyl", name + "_stick", (ox + dx + .28, 0, 2.0), (.04, .04, .32), material=mat("v_stick", "#9FB2FF", 6), parent=p)
        for k in range(int(PER * 3) + 1):                                   # 박자에 맞춰 흔들기
            rot_key(st, fr(t0 + k / 3), (0, 35 if k % 2 else -35, 0))
    mascot("v_mascot", (ox, -.1, 0))
    for i in range(80):                                                     # 꽃가루
        c = ["#FCC024", "#906CFC", "#FFFFFF"][i % 3]
        cf = add("cube", f"v_conf_{i}", (ox - 4 + (i * 37 % 80) / 10, -1 + (i % 7) * .4, 6), (.05, .05, .01), material=mat("v_conf" + c, c, 2))
        x0, y0 = cf.location.x, cf.location.y
        loc_key(cf, fr(t0), (x0, y0, 6 + (i % 5)))
        loc_key(cf, fr(t0 + d), (x0 + (i % 3 - 1) * .5, y0, -.2 + (i % 5) * .3))
        rot_key(cf, fr(t0), (0, 0, 0)); rot_key(cf, fr(t0 + d), (i * 40 % 360, i * 70 % 360, 0))
    cam = camera("CAM_stadium", (ox, -6.5, 1.6), (ox, 0, 1.4), 35)
    cam_move(cam, fr(t0), fr(t0 + d), (ox, -6.5, 1.6), (ox, 0, 1.4), (ox, -4.2, 1.5), (ox, 0, 1.45))
    bp.linear(cam)
    return cam


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    total = PER * 5
    sc.frame_start, sc.frame_end = 1, fr(total) - 1
    w = bpy.data.worlds.new("v02_world"); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    sets = [(set_ski, 0, "#BFDFFF", 1.5), (set_temple_hall, 200, "#3A2418", .6), (set_moon, 400, "#02030A", .2),
            (set_race, 600, "#FFB070", 1.2), (set_stadium, 900, "#14144A", .6)]
    for i, (fn, ox, col, strength) in enumerate(sets):
        t0 = i * PER
        cam = fn(ox, t0)
        m = sc.timeline_markers.new(fn.__name__, frame=fr(t0)); m.camera = cam
        for t in (t0, t0 + PER - 1 / FPS):                                   # 장면마다 하늘색 즉시 전환 (하드컷)
            bg.inputs["Color"].default_value = hex_rgba(col); bg.inputs["Strength"].default_value = strength
            bg.inputs["Color"].keyframe_insert("default_value", frame=fr(t)); bg.inputs["Strength"].keyframe_insert("default_value", frame=fr(t))
    ad = w.node_tree.animation_data
    if ad and ad.action:
        for fc in bp.iter_fcurves(w.node_tree) if hasattr(bp, "iter_fcurves") else []:
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"
    sc.camera = sc.timeline_markers[0].camera
    r = sc.render
    r.engine = "BLENDER_EEVEE"
    r.resolution_x, r.resolution_y, r.resolution_percentage = 1280, 720, 100
    if hasattr(sc, "eevee") and hasattr(sc.eevee, "taa_render_samples"):
        sc.eevee.taa_render_samples = 8
    r.use_stamp = False                                                       # AI 레퍼런스용: 글자 없음
    r.image_settings.file_format = "PNG"
    out_blend = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"previs_v02_s05_{int(total)}s.blend")
    bpy.ops.wm.save_as_mainfile(filepath=out_blend)
    print(f"[previs_v02_s05] per={PER}s total={total}s frames={sc.frame_end} saved {out_blend}")
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
