"""
metaBus 엔딩 크레딧 모션그래픽 v3 — ending_storybord.png 기준
(25.0–30.0초, 5초 / 120프레임, 16:9 · 9:16)

실행:
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      -P build_ending.py -- --aspect 16x9 --out <frames_dir> [--frames 10,30,60,110]
  (--aspect 9x16 로 세로 레이아웃 렌더)

스토리보드 (로컬 프레임 1 = 25.0초)
  E01  25.0–26.0s  f1–24    스마트폰 등장      3/4 Front, Slow Push-in   알림이 도착하며 화면에 빛이 퍼짐
  E02  26.0–27.0s  f25–48   유리 초대장 등장    정면, Gentle Zoom-in      유리 카드가 부드럽게 올라옴
  E03  27.0–28.5s  f49–84   브랜드로 수렴      중앙 고정                  초대장이 빛과 함께 로고로 전환
  E04  28.5–30.0s  f85–120  엔딩              중앙 고정                  로고와 URL이 남으며 페이드아웃

주의
  - 'm' 심볼·워드마크는 원본 파일이 없어 스토리보드 이미지를 보고 근사 재현. 원본 SVG 확보 시 교체.
  - 문구는 스토리보드 그대로 (초대장: "새로운 경험이 / 기다리고 있습니다." + [참여하기 >]).
"""
import bpy
import math
import os
import random
import sys

FPS = 24
FRAMES = 120
FONT_KR = "/System/Library/Fonts/AppleSDGothicNeo.ttc"         # Apple SD Gothic Neo Regular
FONT_WORD = "/System/Library/Fonts/Supplemental/Futura.ttc"    # Futura Medium (워드마크)
FONT_UI = "/System/Library/Fonts/Avenir.ttc"                   # Avenir Book
FONT_UI_BOLD = "/System/Library/Fonts/Avenir Next.ttc"         # Avenir Next Bold
FONT_CLOCK = "/System/Library/Fonts/SFNS.ttf"                  # System Font (잠금화면 시계)

TXT = {
    "clock": "9:41",
    "date": "11월 16일 일요일",
    "app": "metaBus",
    "banner": "새로운 경험이 기다리고 있습니다.",
    "now": "지금",
    "card1": "새로운 경험이",
    "card2": "기다리고 있습니다.",
    "button": "참여하기",
    "url": "metabus.app",
}

C = {
    "bg": "#04050F", "bg_center": "#121540",
    "blue": "#4F6BFF", "violet": "#8B5CF6", "sky": "#8FA8FF", "lilac": "#B9B4E6",
    "white": "#FFFFFF", "ink": "#14162E", "muted": "#5E6080",
    "glass_top": "#3A3F9A", "glass_bottom": "#161850",
    "banner": "#D4D2E4", "phone": "#26282F", "screen_top": "#2C3166", "screen_bottom": "#0E1026",
    "flash": "#DCE3FF",
}


# ---------------------------------------------------------------- color / material
def lin(h):
    h = h.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


def _new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    if hasattr(m, "surface_render_method"):
        m.surface_render_method = "BLENDED"
    m.node_tree.nodes.clear()
    return m, m.node_tree


def flat_mat(name, stops, axis=None, strength=1.0):
    """조명 영향 없는 단색/그라데이션 + 알파. stops: '#hex' | [(pos,'#hex'),...], axis: None|'x'|'y'|'radial'.
    (material, alpha 소켓, emission strength 소켓) 반환."""
    m, nt = _new_mat(name)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = strength
    if isinstance(stops, str):
        em.inputs["Color"].default_value = lin(stops)
    else:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        rn = nt.nodes.new("ShaderNodeValToRGB")
        ramp = rn.color_ramp
        while len(ramp.elements) < len(stops):
            ramp.elements.new(0.5)
        for el, (pos, col) in zip(ramp.elements, stops):
            el.position, el.color = pos, lin(col)
        if axis == "radial":
            sub = nt.nodes.new("ShaderNodeVectorMath")
            sub.operation = "SUBTRACT"
            sub.inputs[1].default_value = (0.5, 0.5, 0.5)
            ln = nt.nodes.new("ShaderNodeVectorMath")
            ln.operation = "LENGTH"
            mr = nt.nodes.new("ShaderNodeMapRange")
            mr.inputs["From Max"].default_value = 0.72
            nt.links.new(tc.outputs["Generated"], sub.inputs[0])
            nt.links.new(sub.outputs[0], ln.inputs[0])
            nt.links.new(ln.outputs["Value"], mr.inputs["Value"])
            nt.links.new(mr.outputs["Result"], rn.inputs["Fac"])
        else:
            sep = nt.nodes.new("ShaderNodeSeparateXYZ")
            nt.links.new(tc.outputs["Generated"], sep.inputs[0])
            nt.links.new(sep.outputs["Y" if axis == "y" else "X"], rn.inputs["Fac"])
        nt.links.new(rn.outputs["Color"], em.inputs["Color"])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    mix.inputs["Fac"].default_value = 1.0
    return m, mix.inputs["Fac"], em.inputs["Strength"]


def glow_mat(name, color, falloff=2.2):
    """중심→바깥으로 사라지는 부드러운 빛. (material, 강도 소켓) 반환."""
    m, nt = _new_mat(name)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sub = nt.nodes.new("ShaderNodeVectorMath")
    sub.operation = "SUBTRACT"
    sub.inputs[1].default_value = (0.5, 0.5, 0.5)
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Max"].default_value = 0.5
    mr.inputs["To Min"].default_value = 1.0
    mr.inputs["To Max"].default_value = 0.0
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = falloff
    amt = nt.nodes.new("ShaderNodeMath")
    amt.operation = "MULTIPLY"
    amt.inputs[1].default_value = 0.0
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = lin(color)
    mix = nt.nodes.new("ShaderNodeMixShader")
    for a, b in ((tc.outputs["Generated"], sub.inputs[0]), (sub.outputs[0], ln.inputs[0]),
                 (ln.outputs["Value"], mr.inputs["Value"]), (mr.outputs["Result"], pw.inputs[0]),
                 (pw.outputs[0], amt.inputs[0]), (amt.outputs[0], mix.inputs["Fac"]),
                 (tr.outputs[0], mix.inputs[1]), (em.outputs[0], mix.inputs[2]), (mix.outputs[0], out.inputs["Surface"])):
        nt.links.new(a, b)
    return m, amt.inputs[1]


def lit_mat(name, color, metallic=0.0, rough=0.4):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = lin(color)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    return m


# ---------------------------------------------------------------- geometry
def rr_points(w, h, r, seg=14):
    hw, hh = w / 2, h / 2
    pts = []
    for cx, cy, a0 in ((hw - r, -hh + r, -90), (hw - r, hh - r, 0), (-hw + r, hh - r, 90), (-hw + r, -hh + r, 180)):
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def ellipse_points(rx, ry, n=160):
    return [(rx * math.cos(i * math.tau / n), ry * math.sin(i * math.tau / n)) for i in range(n)]


def _link(name, data, material, parent, loc):
    o = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(o)
    if material:
        o.data.materials.append(material)
    o.parent = parent
    o.location = loc
    return o


def poly(name, pts, z, material, parent, xy=(0, 0)):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(x, y, 0) for x, y in pts], [], [list(range(len(pts)))])
    return _link(name, me, material, parent, (xy[0], xy[1], z))


def band(name, outer, inner, z, material, parent, xy=(0, 0)):
    """outer/inner 점 수가 같은 닫힌 띠 (테두리, 타원 링)."""
    n = len(outer)
    me = bpy.data.meshes.new(name)
    me.from_pydata([(x, y, 0) for x, y in outer + inner], [],
                   [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)])
    return _link(name, me, material, parent, (xy[0], xy[1], z))


def rr_ring(name, w, h, r, t, z, material, parent):
    return band(name, rr_points(w, h, r), rr_points(w - 2 * t, h - 2 * t, max(r - t, 0.01)), z, material, parent)


def disc(name, r, xy, z, material, parent, n=28):
    return poly(name, [(r * math.cos(i * math.tau / n), r * math.sin(i * math.tau / n)) for i in range(n)], z, material, parent, xy)


def text(name, body, font, size, xy, z, material, parent, align="CENTER", spacing=1.0, bold=0.0):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body, cu.font, cu.size = body, font, size
    cu.align_x, cu.align_y = align, "CENTER"
    cu.space_character, cu.offset = spacing, bold
    return _link(name, cu, material, parent, (xy[0], xy[1], z))


def group(name, xy=(0, 0), z=0.0, parent=None):
    o = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(o)
    o.parent = parent
    o.location = (xy[0], xy[1], z)
    return o


def m_mark(name, height, xy, z, material, parent):
    """'m' 심볼 근사: 두 아치를 한 붓으로 잇는 굵은 스트로크 + 이탤릭 기울기."""
    s = height
    slant = 0.32
    r = 0.3 * s
    stem = 0.5 * s
    def arc(cx, cy):
        return [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(180, -1, -15)]
    a_pts = [(0, 0), (0, stem)] + arc(r, stem)[1:] + [(2 * r, 0)]
    b_pts = [(2 * r, stem)] + arc(3 * r, stem)[1:] + [(4 * r, 0)]
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.13 * s
    cu.bevel_resolution = 6
    cu.use_fill_caps = True
    ox = -2 * r - slant * (stem + r) / 2
    oy = -(stem + r) / 2
    for pts in (a_pts, b_pts):
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for p, (x, y) in zip(sp.points, pts):
            p.co = (x + slant * y + ox, y + oy, 0, 1)
    # 둥근 끝: 각 스트로크 끝점에 구
    o = _link(name, cu, material, parent, (xy[0], xy[1], z))
    for i, pts in enumerate((a_pts, b_pts)):
        for j, (x, y) in enumerate((pts[0], pts[-1])):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.13 * s, segments=16, ring_count=8,
                                                 location=(x + slant * y + ox, y + oy, 0))
            sph = bpy.context.active_object
            sph.name = f"{name}_cap{i}{j}"
            sph.data.materials.append(material)
            sph.parent = o
    return o


# ---------------------------------------------------------------- animation
_pending = []


def key(target, path, frame, value, interp="QUART", easing="EASE_IN_OUT"):
    setattr(target, path, value)
    target.keyframe_insert(path, frame=frame)
    _pending.append((target.id_data, frame, interp, easing))


def fade(items, keys):
    """items: [socket] 또는 [(socket, max)], keys: [(frame, 0~1, [easing])]."""
    for it in items:
        s, mx = it if isinstance(it, tuple) else (it, 1.0)
        for fr, v, *e in keys:
            key(s, "default_value", fr, v * mx, "QUART", e[0] if e else "EASE_IN_OUT")


def _fcurves(idb):
    ad = getattr(idb, "animation_data", None)
    if not (ad and ad.action):
        return []
    act = ad.action
    if hasattr(act, "fcurves") and len(act.fcurves):
        return list(act.fcurves)
    res = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for bag in getattr(strip, "channelbags", []):
                res.extend(bag.fcurves)
    return res


def apply_interp():
    want, owners = {}, {}
    for idb, frame, interp, easing in _pending:
        owners[idb.name_full] = idb
        want[(idb.name_full, frame)] = (interp, easing)
    for name, idb in owners.items():
        for fc in _fcurves(idb):
            for kp in fc.keyframe_points:
                iv = want.get((name, int(round(kp.co.x))))
                if iv:
                    kp.interpolation, kp.easing = iv


def look_at(o, target):
    from mathutils import Vector
    o.rotation_euler = (Vector(target) - o.location).to_track_quat("-Z", "Y").to_euler()


def persp_cam(name, lens):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_fit = "VERTICAL"
    o = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(o)
    return o


def cam_keys(cam, keys):
    """keys: [(frame, loc, target)] — 각 키에서 look-at 재계산."""
    for fr, loc, tgt in keys:
        cam.location = loc
        look_at(cam, tgt)
        cam.keyframe_insert("location", frame=fr)
        cam.keyframe_insert("rotation_euler", frame=fr)
        _pending.append((cam, fr, "SINE", "EASE_IN_OUT"))


def cam_overlay(cam, name, color, keys, size=4):
    """카메라 바로 앞 판 (플래시/페이드). keys: [(frame, alpha)].
    정사영 카메라는 거리와 무관하게 실제 크기로 찍히므로 size를 ortho_scale보다 크게."""
    m, a, _ = flat_mat(name, color)
    p = poly(name, rr_points(size, size, 0.01), 0, m, cam)
    p.location = (0, 0, -0.12)
    if hasattr(p, "visible_shadow"):
        p.visible_shadow = False
    for fr, v in keys:
        key(a, "default_value", fr, v, "SINE", "EASE_IN_OUT")
    return p


# ---------------------------------------------------------------- build
def build(aspect):
    bpy.ops.wm.read_factory_settings(use_empty=True)
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
        print("[ending] WARN: Standard view transform 설정 실패")
    sc.render.image_settings.file_format = "PNG"

    F = {k: bpy.data.fonts.load(v) for k, v in
         (("kr", FONT_KR), ("word", FONT_WORD), ("ui", FONT_UI), ("uib", FONT_UI_BOLD), ("clock", FONT_CLOCK))}

    world = bpy.data.worlds.new("w")
    sc.world = world
    world.use_nodes = True
    bgn = world.node_tree.nodes["Background"]
    bgn.inputs["Color"].default_value = lin(C["bg"])
    bgn.inputs["Strength"].default_value = 1.0

    logo_grad = [(0.0, C["blue"]), (1.0, C["violet"])]

    # ================================================================ A. 폰 세트 (E01, E02)
    phone = group("phone")
    body_m = lit_mat("phone_body", C["phone"], metallic=0.85, rough=0.28)
    body = poly("phone_body", rr_points(3.6, 7.6, 0.58), 0.0, body_m, phone)
    sol = body.modifiers.new("solid", "SOLIDIFY")
    sol.thickness, sol.offset = 0.32, -1
    bev = body.modifiers.new("bevel", "BEVEL")
    bev.width, bev.segments = 0.08, 4
    scr_m, _, scr_str = flat_mat("screen", [(0.0, C["screen_bottom"]), (1.0, C["screen_top"])], "y", strength=0.7)
    poly("screen", rr_points(3.4, 7.4, 0.5), 0.004, scr_m, phone)
    island_m, _, _ = flat_mat("island", "#000000")
    poly("island", rr_points(1.05, 0.3, 0.15), 0.008, island_m, phone, (0, 3.3))
    # 잠금화면
    lock = group("lock", parent=phone)
    lock_alpha = []

    def lm(name, stops, axis=None, alpha=1.0):
        m, a, _ = flat_mat(name, stops, axis)
        lock_alpha.append((a, alpha))
        return m

    text("clock", TXT["clock"], F["clock"], 1.25, (0, 2.15), 0.01, lm("clock", C["white"], alpha=0.92), lock)
    text("date", TXT["date"], F["kr"], 0.24, (0, 1.32), 0.01, lm("date", C["white"], alpha=0.85), lock)
    # 상태바 아이콘(간략)
    for i, w in enumerate((0.05, 0.05, 0.05, 0.05)):
        poly(f"sig{i}", rr_points(w, 0.06 + i * 0.03, 0.01), 0.01, lm(f"sig{i}", C["white"]), lock, (0.85 + i * 0.08, 3.35 + i * 0.015))
    poly("battery", rr_points(0.32, 0.14, 0.04), 0.01, lm("battery", C["white"]), lock, (1.3, 3.36))
    # 알림 배너
    banner = group("banner", (0, -0.35), 0.0, parent=phone)
    ban_alpha = []

    def bm(name, stops, axis=None, alpha=1.0):
        m, a, _ = flat_mat(name, stops, axis)
        ban_alpha.append((a, alpha))
        return m

    poly("banner_bg", rr_points(3.05, 0.98, 0.26), 0.012, bm("banner_bg", C["banner"], alpha=0.86), banner)
    poly("banner_icon_bg", rr_points(0.6, 0.6, 0.15), 0.016, bm("banner_icon_bg", [(0.0, "#1B1E5E"), (1.0, "#2C3290")], "y"), banner, (-1.08, 0))
    m_mark("banner_icon_m", 0.32, (-1.08, 0), 0.03, bm("banner_icon_m", logo_grad, "x"), banner)
    text("banner_app", TXT["app"], F["uib"], 0.22, (-0.66, 0.17), 0.016, bm("banner_app", C["ink"]), banner, align="LEFT")
    text("banner_txt", TXT["banner"], F["kr"], 0.17, (-0.66, -0.15), 0.016, bm("banner_txt", "#33354F"), banner, align="LEFT")
    text("banner_now", TXT["now"], F["kr"], 0.15, (1.28, 0.18), 0.016, bm("banner_now", C["muted"]), banner, align="RIGHT")
    sg_m, sg_amt = glow_mat("screen_glow", C["sky"], falloff=1.8)
    poly("screen_glow", rr_points(5.5, 5.5, 2.74), 0.02, sg_m, phone, (0, -0.35))
    # 배경 보케 (도심 불빛, DOF로 흐려짐)
    rnd = random.Random(5)
    bok = group("bokeh")
    for i in range(60):  # 카메라 시선 방향(폰 뒤 위쪽). 가장자리가 부드러운 원으로 '흐린 빛망울' 표현
        col = rnd.choice(["#FFB870", "#FFD9A0", "#7F9BFF", "#A98BFF", "#C9D2FF", "#6A7BD8"])
        m, amt = glow_mat(f"bok{i}", col, falloff=0.45)
        r = rnd.uniform(1.0, 2.6)
        disc(f"bok{i}", r, (rnd.uniform(-30, 30), rnd.uniform(10, 60)), rnd.uniform(-40, -14), m, bok, n=40)
        amt.default_value = rnd.uniform(0.18, 0.5)
    # 조명
    def area(name, loc, color, energy, size, target):
        ld = bpy.data.lights.new(name, "AREA")
        ld.color, ld.energy, ld.size = lin(color)[:3], energy, size
        o = bpy.data.objects.new(name, ld)
        bpy.context.collection.objects.link(o)
        o.location = loc
        look_at(o, target)
    area("key", (-5, -4, 9), "#E8ECFF", 900, 4, (0, 0, 0))
    area("rim_blue", (5, 6, -3), C["blue"], 1500, 3, (0, 0, 0))
    area("rim_violet", (-5, 6, -3), C["violet"], 1200, 3, (0, 0, 0))

    # 잠금화면·배너 타이밍 (E01)
    fade(lock_alpha, [(1, 1.0), (25, 1.0), (31, 0.0)])
    fade(ban_alpha, [(1, 0.0), (5, 0.0), (11, 1.0, "EASE_OUT"), (26, 1.0), (32, 0.0)])
    key(banner, "location", 5, (0, 0.15, 0), "QUART", "EASE_OUT")
    key(banner, "location", 12, (0, -0.35, 0), "QUART", "EASE_OUT")
    fade([sg_amt], [(1, 0.0), (6, 0.0), (14, 0.55, "EASE_OUT"), (24, 0.3), (34, 0.1)])
    for fr, v in ((1, 0.55), (6, 0.55), (14, 1.0), (24, 0.85)):
        key(scr_str, "default_value", fr, v, "QUART", "EASE_OUT")

    # ---------------- 유리 초대장 (E02)
    card = group("card", (0, -1.2), 0.5)
    cw, ch = 3.15, 2.5
    card_alpha = []

    def cm(name, stops, axis=None, alpha=1.0, strength=1.0):
        m, a, st = flat_mat(name, stops, axis, strength)
        card_alpha.append((a, alpha))
        return m, st

    cg_m, cg_amt = glow_mat("card_glow", C["blue"], falloff=1.6)
    poly("card_glow", rr_points(cw + 2.6, ch + 2.6, (ch + 2.6) / 2 - 0.01), -0.02, cg_m, card)
    poly("card_glass", rr_points(cw, ch, 0.22), 0.0, cm("card_glass", [(0.0, C["glass_bottom"]), (1.0, C["glass_top"])], "y", alpha=0.78)[0], card)
    rim_m, rim_str = cm("card_rim", [(0.0, C["sky"]), (0.5, C["blue"]), (1.0, C["violet"])], "x", strength=1.6)
    rr_ring("card_rim", cw, ch, 0.22, 0.022, 0.004, rim_m, card)
    m_mark("card_m", 0.36, (0, 0.86), 0.02, cm("card_m", logo_grad, "x")[0], card)
    text("card_word", TXT["app"], F["word"], 0.38, (0, 0.44), 0.01, cm("card_word", C["white"])[0], card, spacing=1.04)
    poly("card_div", rr_points(2.3, 0.008, 0.004), 0.01, cm("card_div", [(0.0, C["glass_top"]), (0.5, C["lilac"]), (1.0, C["glass_top"])], "x", alpha=0.6)[0], card, (0, 0.17))
    text("card_l1", TXT["card1"], F["kr"], 0.27, (0, -0.12), 0.01, cm("card_l1", C["white"])[0], card)
    text("card_l2", TXT["card2"], F["kr"], 0.27, (0, -0.46), 0.01, cm("card_l2", C["white"])[0], card)
    btn = group("card_btn", (0, -0.9), 0.01, parent=card)
    poly("btn_bg", rr_points(1.95, 0.42, 0.21), 0.0, cm("btn_bg", [(0.0, C["blue"]), (1.0, C["violet"])], "x")[0], btn)
    text("btn_t", TXT["button"], F["kr"], 0.19, (-0.08, -0.01), 0.01, cm("btn_t", C["white"])[0], btn)
    text("btn_arrow", ">", F["ui"], 0.2, (0.72, 0.0), 0.01, cm("btn_arrow", C["white"])[0], btn)

    fade(card_alpha, [(1, 0.0), (25, 0.0), (35, 1.0, "EASE_OUT"), (44, 1.0), (48, 0.6)])
    fade([cg_amt], [(25, 0.0), (35, 0.22, "EASE_OUT"), (44, 0.3), (48, 0.9)])
    key(card, "location", 25, (0, -1.2, 0.5), "QUART", "EASE_OUT")
    key(card, "location", 37, (0, 0.25, 1.2), "QUART", "EASE_OUT")
    key(card, "rotation_euler", 25, (math.radians(10), 0, 0), "QUART", "EASE_OUT")
    key(card, "rotation_euler", 37, (math.radians(3), 0, 0), "QUART", "EASE_OUT")
    key(card, "scale", 25, (0.9, 0.9, 0.9), "QUART", "EASE_OUT")
    key(card, "scale", 37, (1, 1, 1), "QUART", "EASE_OUT")
    for fr, v in ((25, 1.6), (42, 1.6), (48, 6.0)):  # 로고 전환 직전 테두리가 밝아짐
        key(rim_str, "default_value", fr, v, "QUART", "EASE_IN")

    # ---------------- 카메라 E01 / E02
    cam1 = persp_cam("cam_E01", 50)
    cam1.data.dof.use_dof = True
    cam1.data.dof.focus_object = phone
    cam1.data.dof.aperture_fstop = 1.4
    # 3/4 Front: 폰 아래쪽-오른쪽에서 올려다보듯 → 폰이 서 있는 듯한 원근 (위쪽이 뒤로 기움)
    cam_keys(cam1, [(1, (2.6, -7.2, 8.4), (0.1, 0.9, 0)), (24, (2.1, -6.0, 7.0), (0.1, 0.7, 0))])

    d2 = 11.6 if vertical else 6.2
    cam2 = persp_cam("cam_E02", 40)
    cam2.data.dof.use_dof = True
    cam2.data.dof.focus_object = card
    cam2.data.dof.aperture_fstop = 1.8
    cam_keys(cam2, [(25, (0, 0.2, d2), (0, 0.2, 0.8)), (48, (0, 0.25, d2 * 0.88), (0, 0.25, 0.9))])
    cam_overlay(cam2, "flash_out", C["flash"], [(43, 0.0), (48, 0.7)])

    # ================================================================ B. 로고 세트 (E03, E04)
    LX = 200.0
    LS = 0.86 if vertical else 1.0
    lroot = group("logo_set", (LX, 0))
    W, H = (9, 16) if vertical else (16, 9)
    bg_m, _, _ = flat_mat("logo_bg", [(0.0, C["bg_center"]), (1.0, C["bg"])], "radial")
    poly("logo_bg", rr_points(W + 2, H + 2, 0.01), -2.0, bg_m, lroot)
    # 별
    for i in range(55):
        x, y = rnd.uniform(-W / 2, W / 2), rnd.uniform(-H / 2, H / 2)
        if abs(x) < 4.5 * LS and abs(y) < 2.0:
            continue
        m, a, _ = flat_mat(f"star{i}", C["white"])
        disc(f"star{i}", rnd.uniform(0.008, 0.022), (x, y), -1.9, m, lroot, n=12)
        base = rnd.uniform(0.15, 0.5)
        fade([a], [(49, base * 0.5), (80, base), (FRAMES, base * 0.7)])
    # 궤도 링 (E03)
    orbit = group("orbit", (0, 0.1), -1.0, parent=lroot)
    orbit.rotation_euler[2] = math.radians(-16)
    or_m, or_a, _ = flat_mat("orbit", [(0.0, "#0A0C30"), (0.55, C["blue"]), (0.85, C["sky"]), (1.0, C["violet"])], "x", strength=1.4)
    band("orbit_ring", ellipse_points(6.9 * LS, 2.2 * LS), ellipse_points(6.9 * LS - 0.03, 2.2 * LS - 0.03), 0, or_m, orbit)
    og_m, og_amt = glow_mat("orbit_glow", C["blue"], falloff=1.4)
    poly("orbit_glow", ellipse_points(8.5 * LS, 3.2 * LS, 64), -0.05, og_m, orbit)
    fade([or_a], [(49, 0.0), (60, 1.0, "EASE_OUT"), (84, 0.8), (100, 0.0)])
    fade([og_amt], [(49, 0.0), (60, 0.18), (84, 0.12), (100, 0.0)])
    key(orbit, "rotation_euler", 49, (0, 0, math.radians(-22)), "SINE", "EASE_OUT")
    key(orbit, "rotation_euler", 100, (0, 0, math.radians(-8)), "SINE", "EASE_OUT")
    # 지평선 아크 (E04)
    hy = -6.3 if vertical else -3.55
    hz = group("horizon", (0, hy - 30), -0.8, parent=lroot)
    hz_m, hz_a, _ = flat_mat("horizon_fill", "#03040C")
    disc("horizon_fill", 30, (0, 0), 0, hz_m, hz, n=360)
    hr_m, hr_a, _ = flat_mat("horizon_rim", [(0.0, C["violet"]), (0.5, C["sky"]), (1.0, C["violet"])], "x", strength=2.0)
    band("horizon_rim", ellipse_points(30, 30, 360), ellipse_points(29.96, 29.96, 360), 0.01, hr_m, hz)
    hg_m, hg_amt = glow_mat("horizon_glow", C["blue"], falloff=1.5)
    poly("horizon_glow", ellipse_points(11 * LS, 2.2, 64), 0.0, hg_m, lroot, (0, hy + 0.1))
    fade([hz_a, hr_a], [(84, 0.0), (96, 1.0, "EASE_OUT"), (FRAMES, 1.0)])
    fade([hg_amt], [(84, 0.0), (98, 0.5, "EASE_OUT"), (FRAMES, 0.4)])
    key(hz, "location", 84, (0, hy - 30.8, -0.8), "QUART", "EASE_OUT")
    key(hz, "location", 100, (0, hy - 30, -0.8), "QUART", "EASE_OUT")
    # 로고
    logo = group("logo", (0, 0.2), 0, parent=lroot)
    lg_alpha = []

    def gm(name, stops, axis=None):
        m, a, _ = flat_mat(name, stops, axis)
        lg_alpha.append(a)
        return m

    lgw_m, lgw_amt = glow_mat("logo_glow", C["blue"], falloff=1.8)
    poly("logo_glow", ellipse_points(6.5, 3.6, 64), -0.3, lgw_m, logo)
    m_mark("logo_m", 1.25, (0, 1.05), 0.0, gm("logo_m", logo_grad, "x"), logo)
    text("logo_word", TXT["app"], F["word"], 1.55, (0, -0.55), 0.0, gm("logo_word", C["white"]), logo, spacing=1.04)
    fade(lg_alpha, [(49, 0.0), (61, 1.0, "EASE_OUT"), (FRAMES, 1.0)])
    fade([lgw_amt], [(49, 0.6), (60, 0.25), (84, 0.18), (FRAMES, 0.08)])
    key(logo, "scale", 49, (LS * 0.92,) * 3, "QUART", "EASE_OUT")
    key(logo, "scale", 63, (LS,) * 3, "QUART", "EASE_OUT")
    key(logo, "location", 84, (0, 0.2, 0), "QUART", "EASE_IN_OUT")
    key(logo, "location", 98, (0, 0.55, 0), "QUART", "EASE_IN_OUT")
    key(logo, "scale", 84, (LS,) * 3, "QUART", "EASE_IN_OUT")
    key(logo, "scale", 98, (LS * 0.86,) * 3, "QUART", "EASE_IN_OUT")
    # URL
    um, ua, _ = flat_mat("url", C["lilac"])
    url = text("url", TXT["url"], F["ui"], 0.5 * LS, (0, -1.25 * LS), 0.0, um, lroot, spacing=1.16)
    fade([ua], [(84, 0.0), (90, 0.0), (100, 1.0, "EASE_OUT"), (FRAMES, 1.0)])
    key(url, "location", 90, (0, -1.45 * LS, 0), "QUART", "EASE_OUT")
    key(url, "location", 100, (0, -1.25 * LS, 0), "QUART", "EASE_OUT")

    cd = bpy.data.cameras.new("cam_E03")
    cd.type, cd.ortho_scale = "ORTHO", 16
    cam3 = bpy.data.objects.new("cam_E03", cd)
    bpy.context.collection.objects.link(cam3)
    cam3.location = (LX, 0, 10)
    cam_overlay(cam3, "flash_in", C["flash"], [(49, 0.6), (54, 0.0)], size=40)
    cam_overlay(cam3, "fade_out", "#000000", [(108, 0.0), (FRAMES, 1.0)], size=40)

    # 컷 전환
    for name, fr, cam in (("E01 phone / 3-4 front push-in", 1, cam1), ("E02 glass invitation / front zoom-in", 25, cam2),
                          ("E03 brand convergence / center lock", 49, cam3), ("E04 ending / center lock", 85, cam3)):
        sc.timeline_markers.new(name, frame=fr).camera = cam
    sc.camera = cam1

    apply_interp()
    return sc


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    aspect = argv[argv.index("--aspect") + 1] if "--aspect" in argv else "16x9"
    assert aspect in ("16x9", "9x16")
    scene = build(aspect)
    here = os.path.dirname(os.path.abspath(__file__))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(here, f"ending_{aspect}.blend"))
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
    print(f"[ending] aspect={aspect} done")
