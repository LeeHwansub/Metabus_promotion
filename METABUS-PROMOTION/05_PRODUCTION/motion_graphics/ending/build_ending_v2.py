"""
metaBus 엔딩 크레딧 모션그래픽 — ending_storybord2.png 기준 (v2 안)
(25.0–30.0초, 5초 / 120프레임, 16:9 · 9:16)

실행:
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      -P build_ending_v2.py -- --aspect 16x9 --out <frames_dir> [--frames 10,30,60,110]

스토리보드 2 (로컬 프레임 1 = 25.0초)
  E01  25.0–25.8s  f1–19    알림 도착             3/4 Front, Slow Push-in   스마트폰 화면에 알림 등장
  E02  25.8–27.0s  f20–48   유리 초대장 등장       정면, 카드 등장             유리 카드가 부드럽게 떠오름 (궤도 링)
  E03  27.0–28.5s  f49–84   버스와 함께하는 초대    로우 앵글, 버스 등장        버스가 달리며 배경(미래 도시)이 펼쳐짐
  E04  28.5–30.0s  f85–120  브랜드 엔딩            정면 고정                  로고와 URL이 부드럽게 등장하며 페이드아웃

공통 부품(머티리얼, 도형, m 심볼, 애니메이션 헬퍼)은 build_ending.py(v3)에서 가져온다.
'm' 심볼·워드마크·버스는 원본이 없어 스토리보드 이미지를 보고 근사 재현.
"""
import bpy
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_ending as base  # noqa: E402
from build_ending import (C, TXT, lin, flat_mat, glow_mat, lit_mat, rr_points, ellipse_points, poly, band,  # noqa: E402
                          rr_ring, disc, text, group, m_mark, key, fade, apply_interp, look_at, persp_cam,
                          cam_keys, cam_overlay)

FPS = 24
FRAMES = 120
V = {  # storyboard2 팔레트 (밝은 라벤더 노을 톤)
    "sky_top": "#2B2F86", "sky_mid": "#6E6FD6", "sky_low": "#B9A8F0", "sky_horizon": "#F6CBE2",
    "cloud": "#F1EAFF", "cloud_shade": "#C8BCF2", "city": "#9EA2DA",
    "road": "#B6B1E8", "led": "#5B7BFF", "bus_white": "#F3F3F9", "bus_glass": "#141634",
    "planet": "#2E3192",
}


def prim(kind, name, loc, scale, material, parent, rot=(0, 0, 0), **kw):
    ops = {"cube": bpy.ops.mesh.primitive_cube_add, "cyl": bpy.ops.mesh.primitive_cylinder_add,
           "sphere": bpy.ops.mesh.primitive_uv_sphere_add, "torus": bpy.ops.mesh.primitive_torus_add}
    ops[kind](**kw)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(material)
    o.parent = parent
    o.location = loc
    o.scale = scale
    o.rotation_euler = [math.radians(r) for r in rot]
    return o


def emit_mat(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = lin(color)
    b.inputs["Emission Color"].default_value = lin(color)
    b.inputs["Emission Strength"].default_value = strength
    return m


def sparkle(name, xy, size, z, parent, keys):
    """4갈래 반짝임 (가는 마름모 2개)."""
    g = group(name, xy, z, parent=parent)
    m, a, _ = flat_mat(name, C["white"])
    poly(name + "_v", [(0, size), (size * 0.12, 0), (0, -size), (-size * 0.12, 0)], 0, m, g)
    poly(name + "_h", [(size, 0), (0, size * 0.12), (-size, 0), (0, -size * 0.12)], 0, m, g)
    fade([a], keys)
    return g


def half_ring(name, rx, ry, t, a0, a1, z, parent, stops, strength):
    n = 90
    pts = lambda r_x, r_y: [(r_x * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                             r_y * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    outer, inner = pts(rx, ry), pts(rx - t, ry - t)
    me = bpy.data.meshes.new(name)
    me.from_pydata([(x, y, 0) for x, y in outer + inner], [],
                   [(i, i + 1, n + 1 + i + 1, n + 1 + i) for i in range(n)])
    m, a, _ = flat_mat(name, stops, "x", strength)
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    o.parent = parent
    o.location = (0, 0, z)
    return a


def glass_card(parent, F, alpha_list, rim_strength=1.6, with_text=True, w=3.15, h=2.5):
    """밝은 톤 유리 초대장. 알파 소켓은 alpha_list에 (socket, max)로 추가. 테두리 강도 소켓 반환."""
    def cm(name, stops, axis=None, alpha=1.0, strength=1.0):
        m, a, st = flat_mat(name, stops, axis, strength)
        alpha_list.append((a, alpha))
        return m, st

    p = parent.name
    grad = [(0.0, C["blue"]), (1.0, C["violet"])]
    poly(p + "_glass", rr_points(w, h, 0.22), 0.0, cm(p + "_glass", [(0.0, "#5A5CB8"), (1.0, "#8E8EE0")], "y", alpha=0.55)[0], parent)
    rim_m, rim_st = cm(p + "_rim", [(0.0, C["white"]), (0.5, C["sky"]), (1.0, C["violet"])], "x", strength=rim_strength)
    rr_ring(p + "_rim", w, h, 0.22, 0.022, 0.004, rim_m, parent)
    if with_text:
        m_mark(p + "_m", 0.36, (0, 0.86), 0.02, cm(p + "_m", grad, "x")[0], parent)
        text(p + "_word", TXT["app"], F["word"], 0.38, (0, 0.44), 0.01, cm(p + "_word", C["white"])[0], parent, spacing=1.04)
        poly(p + "_div", rr_points(2.3, 0.008, 0.004), 0.01,
             cm(p + "_div", [(0.0, "#8E8EE0"), (0.5, C["white"]), (1.0, "#8E8EE0")], "x", alpha=0.7)[0], parent, (0, 0.17))
        text(p + "_l1", TXT["card1"], F["kr"], 0.27, (0, -0.12), 0.01, cm(p + "_l1", C["white"])[0], parent)
        text(p + "_l2", TXT["card2"], F["kr"], 0.27, (0, -0.46), 0.01, cm(p + "_l2", C["white"])[0], parent)
        btn = group(p + "_btn", (0, -0.9), 0.01, parent=parent)
        poly(p + "_btn_bg", rr_points(1.95, 0.42, 0.21), 0.0, cm(p + "_btn_bg", grad, "x")[0], btn)
        text(p + "_btn_t", TXT["button"], F["kr"], 0.19, (-0.08, -0.01), 0.01, cm(p + "_btn_t", C["white"])[0], btn)
        text(p + "_btn_a", ">", F["ui"], 0.2, (0.72, 0.0), 0.01, cm(p + "_btn_a", C["white"])[0], btn)
    else:
        m_mark(p + "_m", 0.9, (0, 0), 0.02, cm(p + "_m", grad, "x")[0], parent)
    return rim_st


def make_bus(name, parent, F):
    """storyboard2 버스: 흰 차체 + 남색 유리 띠 + 파란 LED, 측면 metaBus. 앞쪽 = -X."""
    bus = group(name, parent=parent)
    white = lit_mat("bus_white", V["bus_white"], 0.0, 0.22)
    glass = lit_mat("bus_glass", V["bus_glass"], 0.2, 0.08)
    led = emit_mat("bus_led", V["led"], 8)
    body = prim("cube", "bus_body", (0, 0, 1.75), (5.4, 1.3, 1.25), white, bus)
    b = body.modifiers.new("bevel", "BEVEL")
    b.width, b.segments = 0.7, 10  # 둥근 셔틀 실루엣
    # 남색 유리 띠: 흰 차체 안쪽에 얇게 (차체보다 크면 버스 전체가 검게 보임)
    win = prim("cube", "bus_window", (-0.05, 0, 2.05), (5.38, 1.315, 0.36), glass, bus)  # 앞까지 이어지는 유리 띠
    b = win.modifiers.new("bevel", "BEVEL")
    b.width, b.segments = 0.3, 6
    prim("cube", "bus_led_side", (0, -1.33, 0.78), (5.0, 0.02, 0.035), led, bus)
    prim("cube", "bus_led_front_l", (-5.45, -0.95, 1.6), (0.04, 0.04, 0.7), led, bus)
    prim("cube", "bus_led_front_r", (-5.45, 0.95, 1.6), (0.04, 0.04, 0.7), led, bus)
    prim("cube", "bus_headlight", (-5.6, 0, 0.95), (0.03, 0.9, 0.06), emit_mat("bus_head", "#EAF0FF", 12), bus)
    tire = lit_mat("tire", "#1A1B22", 0, 0.6)
    for i, (x, y) in enumerate(((-3.3, -1.2), (-3.3, 1.2), (3.3, -1.2), (3.3, 1.2))):
        prim("cyl", f"bus_wheel{i}", (x, y, 0.55), (0.58, 0.58, 0.22), tire, bus, rot=(90, 0, 0))
    lw = text("bus_word", TXT["app"], F["word"], 0.75, (1.0, 0), 0, emit_mat("bus_word_m", "#1A1C4A", 0), bus)
    lw.location = (1.0, -1.335, 1.3)
    lw.rotation_euler = (math.radians(90), 0, 0)
    mg = group("bus_front_m", parent=bus)
    mg.location = (-5.62, 0, 2.1)
    mg.rotation_euler = (math.radians(90), 0, math.radians(-90))
    m_mark("bus_front_m_mark", 0.45, (0, 0), 0, emit_mat("bus_m", C["sky"], 4), mg)
    return bus


def build(aspect):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    base._pending.clear()
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, FRAMES
    vertical = aspect == "9x16"
    sc.render.resolution_x, sc.render.resolution_y = (1080, 1920) if vertical else (1920, 1080)
    sc.render.resolution_percentage = 100
    sc.render.engine = "BLENDER_EEVEE"
    if hasattr(sc.eevee, "taa_render_samples"):
        sc.eevee.taa_render_samples = 48
    try:
        sc.view_settings.view_transform = "Standard"
    except TypeError:
        print("[ending_v2] WARN: Standard view transform 설정 실패")
    sc.render.image_settings.file_format = "PNG"

    F = {k: bpy.data.fonts.load(v) for k, v in
         (("kr", base.FONT_KR), ("word", base.FONT_WORD), ("ui", base.FONT_UI), ("uib", base.FONT_UI_BOLD),
          ("clock", base.FONT_CLOCK))}
    world = bpy.data.worlds.new("w")
    sc.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = lin("#8C86D6")
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
    rnd = random.Random(21)
    logo_grad = [(0.0, C["blue"]), (1.0, C["violet"])]

    def area(name, loc, color, energy, size, target):
        ld = bpy.data.lights.new(name, "AREA")
        ld.color, ld.energy, ld.size = lin(color)[:3], energy, size
        o = bpy.data.objects.new(name, ld)
        bpy.context.collection.objects.link(o)
        o.location = loc
        look_at(o, target)
        return o

    # ================================================================ A. 폰 세트 (E01, E02) — 원점
    phone = group("phone")
    body = poly("phone_body", rr_points(3.6, 7.6, 0.58), 0.0, lit_mat("phone_body", "#3A3D4C", 0.85, 0.25), phone)
    s = body.modifiers.new("solid", "SOLIDIFY")
    s.thickness, s.offset = 0.32, -1
    b = body.modifiers.new("bevel", "BEVEL")
    b.width, b.segments = 0.08, 4
    scr_m, _, scr_str = flat_mat("screen", [(0.0, "#3B3E86"), (1.0, "#8C88D8")], "y", strength=0.8)
    poly("screen", rr_points(3.4, 7.4, 0.5), 0.004, scr_m, phone)
    poly("island", rr_points(1.05, 0.3, 0.15), 0.008, flat_mat("island", "#000000")[0], phone, (0, 3.3))
    lock = group("lock", parent=phone)
    lock_a = []

    def lm(name, stops, axis=None, alpha=1.0):
        m, a, _ = flat_mat(name, stops, axis)
        lock_a.append((a, alpha))
        return m

    text("clock", TXT["clock"], F["clock"], 1.25, (0, 2.15), 0.01, lm("clock", C["white"], alpha=0.95), lock)
    text("date", TXT["date"], F["kr"], 0.24, (0, 1.32), 0.01, lm("date", C["white"], alpha=0.9), lock)
    for i in range(4):
        poly(f"sig{i}", rr_points(0.05, 0.06 + i * 0.03, 0.01), 0.01, lm(f"sig{i}", C["white"]), lock, (0.85 + i * 0.08, 3.35 + i * 0.015))
    poly("battery", rr_points(0.32, 0.14, 0.04), 0.01, lm("battery", C["white"]), lock, (1.3, 3.36))
    banner = group("banner", (0, -0.35), 0.0, parent=phone)
    ban_a = []

    def bm(name, stops, axis=None, alpha=1.0):
        m, a, _ = flat_mat(name, stops, axis)
        ban_a.append((a, alpha))
        return m

    poly("banner_bg", rr_points(3.05, 0.98, 0.26), 0.012, bm("banner_bg", "#ECEAF8", alpha=0.9), banner)
    poly("banner_icon_bg", rr_points(0.6, 0.6, 0.15), 0.016, bm("banner_icon_bg", [(0.0, "#1B1E5E"), (1.0, "#2C3290")], "y"), banner, (-1.08, 0))
    m_mark("banner_icon_m", 0.32, (-1.08, 0), 0.03, bm("banner_icon_m", logo_grad, "x"), banner)
    text("banner_app", TXT["app"], F["uib"], 0.22, (-0.66, 0.17), 0.016, bm("banner_app", C["ink"]), banner, align="LEFT")
    text("banner_txt", TXT["banner"], F["kr"], 0.17, (-0.66, -0.15), 0.016, bm("banner_txt", "#33354F"), banner, align="LEFT")
    text("banner_now", TXT["now"], F["kr"], 0.15, (1.28, 0.18), 0.016, bm("banner_now", C["muted"]), banner, align="RIGHT")
    # 알림 '띵' 표시선 (폰 왼쪽 위)
    ding = group("ding", (-2.35, 1.6), 0.05, parent=phone)
    ding_a = []
    for i, ang in enumerate((150, 175, 200)):
        m, a, _ = flat_mat(f"ding{i}", C["white"])
        ding_a.append(a)
        ln = poly(f"ding{i}", rr_points(0.5, 0.07, 0.035), 0, m, ding)
        ln.location = (0.55 * math.cos(math.radians(ang)), 0.55 * math.sin(math.radians(ang)), 0)
        ln.rotation_euler[2] = math.radians(ang)
    fade(ding_a, [(1, 0.0), (6, 0.0), (9, 1.0, "EASE_OUT"), (19, 0.0)])
    key(ding, "scale", 6, (0.7, 0.7, 0.7), "QUART", "EASE_OUT")
    key(ding, "scale", 10, (1, 1, 1), "QUART", "EASE_OUT")
    sg_m, sg_amt = glow_mat("screen_glow", "#C9D2FF", falloff=1.8)
    poly("screen_glow", rr_points(5.5, 5.5, 2.74), 0.02, sg_m, phone, (0, -0.35))
    # 배경: 라벤더 노을 하늘 + 부드러운 빛망울
    bok = group("bokeh")
    sky_m, _, _ = flat_mat("phone_sky", [(0.0, "#6A6AC8"), (0.6, "#A49AE6"), (1.0, "#F2C6DE")], "y")
    sky = poly("phone_sky", rr_points(160, 160, 0.01), 0, sky_m, bok)
    sky.location = (0, 30, -48)
    for i in range(55):
        col = rnd.choice(["#FFD2B8", "#FFE6CC", "#B9C4FF", "#D3C2FF", "#FFFFFF", "#9FA8F0"])
        m, amt = glow_mat(f"bok{i}", col, falloff=0.45)
        disc(f"bok{i}", rnd.uniform(1.2, 3.0), (rnd.uniform(-30, 30), rnd.uniform(5, 60)), rnd.uniform(-40, -14), m, bok, n=40)
        amt.default_value = rnd.uniform(0.25, 0.6)
    area("key", (-5, -4, 9), "#F0F2FF", 1100, 4, (0, 0, 0))
    area("rim_blue", (5, 6, -3), C["blue"], 1500, 3, (0, 0, 0))
    area("rim_pink", (-5, 6, -3), "#F2A6D0", 1100, 3, (0, 0, 0))

    fade(lock_a, [(1, 1.0), (20, 1.0), (27, 0.0)])
    fade(ban_a, [(1, 0.0), (2, 0.0), (8, 1.0, "EASE_OUT"), (20, 1.0), (26, 0.0)])
    key(banner, "location", 2, (0, 0.15, 0), "QUART", "EASE_OUT")
    key(banner, "location", 9, (0, -0.35, 0), "QUART", "EASE_OUT")
    fade([sg_amt], [(1, 0.0), (3, 0.0), (10, 0.5, "EASE_OUT"), (19, 0.3), (28, 0.1)])
    for fr, v in ((1, 0.7), (3, 0.7), (10, 1.0)):
        key(scr_str, "default_value", fr, v, "QUART", "EASE_OUT")

    # ---------------- 유리 초대장 + 궤도 링 (E02)
    card = group("card", (0, -1.2), 0.5)
    card_a = []
    cg_m, cg_amt = glow_mat("card_glow", "#9DB0FF", falloff=1.6)
    poly("card_glow", rr_points(5.8, 5.2, 2.59), -0.03, cg_m, card)
    rim_st = glass_card(card, F, card_a)
    orbit = group("card_orbit", (0, -0.15), parent=card)
    orbit.rotation_euler = (0, 0, math.radians(-14))
    ostops = [(0.0, C["sky"]), (0.5, C["white"]), (1.0, C["violet"])]
    # 위쪽 반은 카드 윗변 뒤, 아래쪽 반은 카드 아래 모서리 앞을 지나도록 (본문 글자를 가리지 않게)
    or_alpha = [half_ring("orbit_back", 2.95, 1.42, 0.03, 0, 180, -0.02, orbit, ostops, 2.2),
                half_ring("orbit_front", 2.95, 1.42, 0.03, 180, 360, 0.05, orbit, ostops, 2.2)]
    for i, (x, y, sz) in enumerate(((-2.1, 1.35, 0.16), (2.2, 1.0, 0.12), (-1.9, -1.3, 0.1), (2.4, -0.4, 0.14))):
        sparkle(f"spark{i}", (x, y), sz, 0.06, card, [(20, 0.0), (30 + i * 3, 1.0), (40 + i * 2, 0.3), (48, 0.9)])

    fade(card_a, [(1, 0.0), (20, 0.0), (32, 1.0, "EASE_OUT"), (44, 1.0), (48, 0.7)])
    fade(or_alpha, [(1, 0.0), (24, 0.0), (36, 1.0, "EASE_OUT"), (48, 1.0)])
    fade([cg_amt], [(20, 0.0), (32, 0.25, "EASE_OUT"), (44, 0.3), (48, 0.8)])
    key(card, "location", 20, (0, -1.2, 0.5), "QUART", "EASE_OUT")
    key(card, "location", 34, (0, 0.25, 1.2), "QUART", "EASE_OUT")
    key(card, "rotation_euler", 20, (math.radians(10), math.radians(-4), math.radians(4)), "QUART", "EASE_OUT")
    key(card, "rotation_euler", 34, (math.radians(4), math.radians(-6), math.radians(3)), "QUART", "EASE_OUT")
    key(card, "scale", 20, (0.9, 0.9, 0.9), "QUART", "EASE_OUT")
    key(card, "scale", 34, (1, 1, 1), "QUART", "EASE_OUT")
    key(orbit, "rotation_euler", 24, (0, 0, math.radians(-22)), "SINE", "EASE_OUT")
    key(orbit, "rotation_euler", 48, (0, 0, math.radians(-10)), "SINE", "EASE_OUT")
    for fr, v in ((20, 1.6), (42, 1.6), (48, 5.0)):
        key(rim_st, "default_value", fr, v, "QUART", "EASE_IN")

    cam1 = persp_cam("cam_E01", 50)
    cam1.data.dof.use_dof = True
    cam1.data.dof.focus_object = phone
    cam1.data.dof.aperture_fstop = 1.4
    cam_keys(cam1, [(1, (2.4, -6.2, 7.6), (0.0, 1.0, 0)), (19, (2.0, -5.3, 6.5), (0.0, 0.9, 0))])
    d2 = 11.6 if vertical else 6.4
    cam2 = persp_cam("cam_E02", 40)
    cam2.data.dof.use_dof = True
    cam2.data.dof.focus_object = card
    cam2.data.dof.aperture_fstop = 1.8
    cam_keys(cam2, [(20, (0, 0.2, d2), (0, 0.2, 0.8)), (48, (0, 0.25, d2 * 0.9), (0, 0.25, 0.9))])
    cam_overlay(cam2, "flash_out", "#F2F0FF", [(44, 0.0), (48, 0.75)])

    # ================================================================ B. 버스 + 미래 도시 (E03) — x=400
    BX = 400.0
    city = group("city", (BX, 0))
    prim("cube", "road", (0, 0, -0.05), (80, 9, 0.05), lit_mat("road", V["road"], 0.0, 0.12), city)
    prim("cube", "ground", (0, 40, -0.1), (120, 40, 0.05), lit_mat("ground", "#8E8AD2", 0, 0.5), city)
    for i, (y, col) in enumerate(((-3.2, C["blue"]), (3.2, C["violet"]), (-6.5, C["sky"]))):  # 도로 라이트 라인
        prim("cube", f"trail{i}", (0, y, 0.01), (80, 0.04, 0.01), emit_mat(f"trail{i}", col, 6), city)
    # 360 높이 중 지평선(z≈0)이 아래 ~8% 지점 → 그 위로 분홍→라벤더→남색
    csky_m, _, _ = flat_mat("city_sky", [(0.0, V["sky_horizon"]), (0.12, V["sky_horizon"]), (0.2, V["sky_low"]),
                                         (0.32, V["sky_mid"]), (0.55, V["sky_top"])], "y")
    sk = poly("city_sky", rr_points(500, 360, 0.01), 0, csky_m, city)  # 저각 광각에서도 가장자리가 안 보이게
    sk.location = (0, 110, 150)
    sk.rotation_euler = (math.radians(90), 0, 0)
    # 카메라가 +X 쪽을 비스듬히 보므로 +X 방향에도 같은 하늘판 (가장자리가 화면에 안 보이게)
    sk2 = poly("city_sky_x", rr_points(2000, 360, 0.01), 0, csky_m, city)
    sk2.location = (300, 0, 150)
    sk2.rotation_euler = (math.radians(90), 0, math.radians(90))
    # 타워 + 공중 플랫폼 (스태거로 솟아오르며 '배경이 펼쳐짐')
    tower_m = lit_mat("tower", V["city"], 0.3, 0.3)
    win_m = emit_mat("tower_win", "#E8EEFF", 3)
    rim_m = emit_mat("platform_rim", "#9FB6FF", 5)
    plat_m = lit_mat("platform", "#D9D6F5", 0.1, 0.25)
    for i in range(26):
        x = rnd.uniform(-45, 45)
        y = rnd.uniform(14, 70)
        if abs(x) < 6 and y < 25:
            y += 15
        h = rnd.uniform(8, 34)
        r = rnd.uniform(0.8, 2.2)
        tg = group(f"tower{i}", (x, y), 0, parent=city)
        prim("cyl", f"tower{i}_body", (0, 0, h / 2), (r, r, h / 2), tower_m, tg, vertices=24)
        prim("cyl", f"tower{i}_win", (0, 0, h * 0.75), (r * 1.01, r * 1.01, 0.12), win_m, tg, vertices=24)
        if rnd.random() < 0.55:
            pz, pr = h * rnd.uniform(0.45, 0.8), rnd.uniform(3, 6)
            prim("cyl", f"tower{i}_plat", (0, 0, pz), (pr, pr, 0.18), plat_m, tg, vertices=48)
            prim("torus", f"tower{i}_platrim", (0, 0, pz - 0.05), (pr, pr, 0.6), rim_m, tg, major_radius=1, minor_radius=0.03)
        st = 49 + min(int((y - 14) / 4), 14)
        key(tg, "scale", 49, (1, 1, 0.02), "QUART", "EASE_OUT")
        key(tg, "scale", st, (1, 1, 0.02), "QUART", "EASE_OUT")
        key(tg, "scale", st + 12, (1, 1, 1), "QUART", "EASE_OUT")
    # 구름
    cloud_m = emit_mat("cloud", V["cloud"], 0.35)
    for i in range(16):
        cx, cy, cz = rnd.uniform(-60, 60), rnd.uniform(60, 100), rnd.uniform(2, 14)
        cg = group(f"cloud{i}", (cx, cy), cz, parent=city)
        for j in range(5):
            r = rnd.uniform(2.5, 5.5)
            prim("sphere", f"cloud{i}_{j}", (rnd.uniform(-6, 6), rnd.uniform(-1.5, 1.5), rnd.uniform(-0.8, 1.6)),
                 (r * 1.4, r, r * 0.7), cloud_m, cg, segments=20, ring_count=10)
        key(cg, "location", 49, (cx + 6, cy, cz), "SINE", "EASE_OUT")
        key(cg, "location", 84, (cx, cy, cz), "SINE", "EASE_OUT")
    # 하늘에 떠 있는 유리 카드 (E02에서 이어짐)
    sky_card = group("sky_card", (6.5, 14), 11, parent=city)
    sky_card.rotation_euler = (math.radians(80), 0, math.radians(-18))
    sk_a = []
    glass_card(sky_card, F, sk_a, rim_strength=2.5, with_text=False, w=4.6, h=3.4)
    fade(sk_a, [(49, 0.0), (58, 1.0, "EASE_OUT"), (84, 1.0)])
    key(sky_card, "location", 49, (8.5, 14, 13.5), "QUART", "EASE_OUT")
    key(sky_card, "location", 66, (6.5, 14, 11), "QUART", "EASE_OUT")
    # 버스
    bus = make_bus("bus", city, F)
    key(bus, "location", 49, (16, 0, 0), "QUART", "EASE_OUT")
    key(bus, "location", 84, (1.5, 0, 0), "QUART", "EASE_OUT")
    sun = bpy.data.lights.new("city_sun", "SUN")
    sun.color, sun.energy = lin("#FFD6E6")[:3], 5.5
    so = bpy.data.objects.new("city_sun", sun)
    bpy.context.collection.objects.link(so)
    so.rotation_euler = (math.radians(55), 0, math.radians(140))
    area("bus_fill", (BX - 8, -10, 6), "#DCE2FF", 3000, 10, (BX, 0, 1.5))

    cam3 = persp_cam("cam_E03", 24)
    if vertical:  # 세로: 더 뒤에서 버스 중앙을 봐서 버스 전체가 폭 안에 들어오게
        cam_keys(cam3, [(49, (BX - 16, -12, 0.6), (BX + 12, 0, 2.6)), (84, (BX - 14, -11, 0.6), (BX + 1.5, 0, 2.3))])
    else:
        cam_keys(cam3, [(49, (BX - 8, -8.5, 0.55), (BX + 6, 4, 3.0)), (84, (BX - 6.5, -7.8, 0.6), (BX + 1, 3, 2.6))])
    cam_overlay(cam3, "flash_in", "#F2F0FF", [(49, 0.6), (54, 0.0)])

    # ================================================================ C. 브랜드 엔딩 (E04) — x=800, 정사영
    LX = 800.0
    LS = 0.86 if vertical else 1.0
    W, H = (9, 16) if vertical else (16, 9)
    lroot = group("logo_set", (LX, 0))
    bg_m, _, _ = flat_mat("end_sky", [(0.0, "#8E86D8"), (0.4, "#4A4EB8"), (1.0, V["sky_top"])], "y")
    poly("end_sky", rr_points(W + 2, H + 2, 0.01), -2.0, bg_m, lroot)
    for i in range(45):
        x, y = rnd.uniform(-W / 2, W / 2), rnd.uniform(0, H / 2)
        if abs(x) < 4.5 * LS and abs(y) < 2.2:
            continue
        m, a, _ = flat_mat(f"estar{i}", C["white"])
        disc(f"estar{i}", rnd.uniform(0.01, 0.025), (x, y), -1.9, m, lroot, n=12)
        fade([a], [(85, 0.0), (100, rnd.uniform(0.3, 0.7)), (FRAMES, 0.4)])
    sparkle("esp0", (-5.2 * LS, 1.6), 0.18, -1.0, lroot, [(85, 0.0), (98, 1.0), (110, 0.4)])
    sparkle("esp1", (5.6 * LS, 2.4), 0.14, -1.0, lroot, [(88, 0.0), (102, 1.0), (114, 0.5)])
    # 궤도 링
    eo = group("end_orbit", (0, 0.35), -1.0, parent=lroot)
    eo.rotation_euler[2] = math.radians(-10)
    eo_m, eo_a, _ = flat_mat("end_orbit", [(0.0, "#2A2E86"), (0.5, C["sky"]), (0.8, C["white"]), (1.0, C["violet"])], "x", 1.6)
    band("end_orbit", ellipse_points(7.0 * LS, 2.3 * LS), ellipse_points(7.0 * LS - 0.03, 2.3 * LS - 0.03), 0, eo_m, eo)
    fade([eo_a], [(85, 0.0), (98, 1.0, "EASE_OUT"), (FRAMES, 0.9)])
    key(eo, "rotation_euler", 85, (0, 0, math.radians(-16)), "SINE", "EASE_OUT")
    key(eo, "rotation_euler", FRAMES, (0, 0, math.radians(-8)), "SINE", "EASE_OUT")
    # 지평선(행성) + 도시 실루엣
    hy = -6.0 if vertical else -3.3
    hz = group("e_horizon", (0, hy - 30), -0.8, parent=lroot)
    hzf_m, hzf_a, _ = flat_mat("e_horizon_fill", [(0.0, "#1A1C66"), (1.0, V["planet"])], "y")
    disc("e_horizon_fill", 30, (0, 0), 0, hzf_m, hz, n=360)
    hr_m, hr_a, _ = flat_mat("e_horizon_rim", [(0.0, C["violet"]), (0.5, C["white"]), (1.0, C["violet"])], "x", 2.0)
    band("e_horizon_rim", ellipse_points(30, 30, 360), ellipse_points(29.95, 29.95, 360), 0.01, hr_m, hz)
    sky_a = []
    for i in range(36):
        x = -8 + i * 0.45 + rnd.uniform(-0.1, 0.1)
        if abs(x) > (W / 2 + 0.5):
            continue
        h = rnd.uniform(0.12, 0.7) * (1.0 if abs(x) > 2.5 else 0.6)
        top = math.sqrt(max(30 ** 2 - x ** 2, 0))
        m, a, _ = flat_mat(f"skyl{i}", "#3B3E9E")
        sky_a.append(a)
        poly(f"skyl{i}", rr_points(rnd.uniform(0.12, 0.3), h * 2, 0.01), -0.005, m, hz, (x, top))
    hg_m, hg_amt = glow_mat("e_horizon_glow", "#B7C6FF", falloff=1.5)
    poly("e_horizon_glow", ellipse_points(12 * LS, 2.0, 64), 0.0, hg_m, lroot, (0, hy + 0.1))
    fade([hzf_a, hr_a] + sky_a, [(85, 0.0), (96, 1.0, "EASE_OUT"), (FRAMES, 1.0)])
    fade([hg_amt], [(85, 0.0), (98, 0.5, "EASE_OUT"), (FRAMES, 0.45)])
    key(hz, "location", 85, (0, hy - 30.8, -0.8), "QUART", "EASE_OUT")
    key(hz, "location", 100, (0, hy - 30, -0.8), "QUART", "EASE_OUT")
    # 양옆 구름
    cl_a = []
    for side in (-1, 1):
        base_x = side * (W / 2 - (1.4 if vertical else 1.8))
        for j in range(6):
            r = rnd.uniform(0.6, 1.3) * (0.8 if vertical else 1.0)
            m, a, _ = flat_mat(f"ecl{side}_{j}", [(0.0, V["cloud_shade"]), (1.0, V["cloud"])], "y")
            cl_a.append((a, 0.95))
            disc(f"ecl{side}_{j}", r, (base_x + side * rnd.uniform(-0.6, 1.4) - side * j * 0.35,
                                         hy + 0.4 + rnd.uniform(-0.2, 1.0) + j * 0.1), -0.6 + j * 0.01, m, lroot, n=36)
    fade(cl_a, [(85, 0.0), (98, 1.0, "EASE_OUT"), (FRAMES, 1.0)])
    # 로고 + URL
    logo = group("e_logo", (0, 0.45), 0, parent=lroot)
    lgw_m, lgw_amt = glow_mat("e_logo_glow", "#9DB0FF", falloff=1.8)
    poly("e_logo_glow", ellipse_points(6.5, 3.6, 64), -0.3, lgw_m, logo)
    lm_m, lm_a, _ = flat_mat("e_logo_m", logo_grad, "x")
    m_mark("e_logo_m", 1.25, (0, 1.05), 0.0, lm_m, logo)
    lw_m, lw_a, _ = flat_mat("e_logo_word", C["white"])
    text("e_logo_word", TXT["app"], F["word"], 1.55, (0, -0.55), 0.0, lw_m, logo, spacing=1.04)
    fade([lm_a, lw_a], [(85, 0.0), (97, 1.0, "EASE_OUT"), (FRAMES, 1.0)])
    fade([lgw_amt], [(85, 0.0), (97, 0.25), (FRAMES, 0.15)])
    key(logo, "scale", 85, (LS * 0.92,) * 3, "QUART", "EASE_OUT")
    key(logo, "scale", 99, (LS,) * 3, "QUART", "EASE_OUT")
    um, ua, _ = flat_mat("e_url", "#E4E0FF")
    url = text("e_url", TXT["url"], F["ui"], 0.5 * LS, (0, -1.3 * LS), 0.0, um, lroot, spacing=1.16)
    fade([ua], [(85, 0.0), (92, 0.0), (102, 1.0, "EASE_OUT"), (FRAMES, 1.0)])
    key(url, "location", 92, (0, -1.5 * LS, 0), "QUART", "EASE_OUT")
    key(url, "location", 102, (0, -1.3 * LS, 0), "QUART", "EASE_OUT")

    cd = bpy.data.cameras.new("cam_E04")
    cd.type, cd.ortho_scale = "ORTHO", 16
    cam4 = bpy.data.objects.new("cam_E04", cd)
    bpy.context.collection.objects.link(cam4)
    cam4.location = (LX, 0, 10)
    cam_overlay(cam4, "e_flash", "#F2F0FF", [(85, 0.5), (91, 0.0)], size=40)
    cam_overlay(cam4, "e_fade", "#000000", [(110, 0.0), (FRAMES, 1.0)], size=40)

    for name, fr, cam in (("E01 notification / 3-4 front push-in", 1, cam1),
                          ("E02 glass invitation / front", 20, cam2),
                          ("E03 bus invitation / low angle", 49, cam3),
                          ("E04 brand ending / front lock", 85, cam4)):
        sc.timeline_markers.new(name, frame=fr).camera = cam
    sc.camera = cam1
    apply_interp()
    return sc


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    aspect = argv[argv.index("--aspect") + 1] if "--aspect" in argv else "16x9"
    assert aspect in ("16x9", "9x16")
    scene = build(aspect)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"ending_v2_{aspect}.blend"))
    if "--out" in argv:
        out = argv[argv.index("--out") + 1]
        os.makedirs(out, exist_ok=True)
        if "--frames" in argv:
            for fr in map(int, argv[argv.index("--frames") + 1].split(",")):
                scene.frame_set(fr)
                scene.render.filepath = os.path.join(out, f"test_{fr:03d}")
                bpy.ops.render.render(write_still=True)
        else:
            scene.render.filepath = os.path.join(out, "f_")
            bpy.ops.render.render(animation=True)
    print(f"[ending_v2] aspect={aspect} done")
