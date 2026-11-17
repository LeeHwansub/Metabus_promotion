"""
metaBus 홍보영상 30초 프리비즈 생성 스크립트 (블록아웃 + 색감)

실행:
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      -P build_previs.py -- [--render <frames_dir>] [--frames 10,100,200]

- 컷 수는 ../storyboard.json 의 shots 를 기준으로 검증한다. (컷 구간은 아래 cut() 정의에 반영)
- 세트는 X축으로 떨어뜨려 배치하고, 컷마다 카메라를 타임라인 마커에 바인딩한다.
- 결과: 같은 폴더에 previs.blend 저장. --render 지정 시 PNG 시퀀스 렌더.
- 렌더 이미지 좌상단 스탬프에 컷 이름(마커)·시간·프레임이 찍힌다.
"""
import bpy
import json
import math
import os
import sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
STORYBOARD = os.path.join(HERE, "..", "storyboard.json")
FONT_KR = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
FPS = 24


# ---------------------------------------------------------------- utils
def f(sec):
    """초 → 프레임 (1-based)."""
    return int(round(sec * FPS)) + 1


def hex_rgba(h, a=1.0):
    h = h.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, a)


_mats = {}


def mat(name, color, emit=0.0, rough=0.6):
    key = (name, color, emit)
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = hex_rgba(color)
    bsdf.inputs["Roughness"].default_value = rough
    if emit:
        bsdf.inputs["Emission Color"].default_value = hex_rgba(color)
        bsdf.inputs["Emission Strength"].default_value = emit
    _mats[key] = m
    return m


def emit_key(m, frame, strength):
    sock = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    sock.default_value = strength
    sock.keyframe_insert("default_value", frame=frame)


def parent_to(o, parent, world_loc):
    """부모(회전·스케일 없는 empty)에 연결하면서 월드 위치 유지."""
    o.parent = parent
    o.location = Vector(world_loc) - parent.location


def add(kind, name, loc, scale=(1, 1, 1), rot=(0, 0, 0), material=None, parent=None, **kw):
    ops = {
        "cube": bpy.ops.mesh.primitive_cube_add,
        "sphere": bpy.ops.mesh.primitive_uv_sphere_add,
        "cyl": bpy.ops.mesh.primitive_cylinder_add,
        "cone": bpy.ops.mesh.primitive_cone_add,
        "plane": bpy.ops.mesh.primitive_plane_add,
        "torus": bpy.ops.mesh.primitive_torus_add,
    }
    ops[kind](location=loc, rotation=[math.radians(r) for r in rot], **kw)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    if material:
        o.data.materials.append(material)
    if parent:
        parent_to(o, parent, loc)
    return o


def empty(name, loc):
    o = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(o)
    o.location = loc
    return o


def text(name, body, loc, size=0.3, color="#FFFFFF", emit=2.0, rot=(90, 0, 0), font=None, parent=None):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    if font:
        cu.font = font
    o = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = [math.radians(r) for r in rot]
    o.data.materials.append(mat(name + "_m", color, emit))
    if parent:
        parent_to(o, parent, loc)
    return o


def light(name, kind, loc, color, energy, rot=(0, 0, 0), size=None):
    ld = bpy.data.lights.new(name, kind)
    ld.color = hex_rgba(color)[:3]
    ld.energy = energy
    if size and kind == "SPOT":
        ld.spot_size = math.radians(size)
    if size and kind == "AREA":
        ld.size = size
    o = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = [math.radians(r) for r in rot]
    return o


def energy_key(lo, frame, value):
    lo.data.energy = value
    lo.data.keyframe_insert("energy", frame=frame)


def loc_key(o, frame, loc):
    o.location = loc
    o.keyframe_insert("location", frame=frame)


def scale_key(o, frame, s):
    o.scale = (s, s, s)
    o.keyframe_insert("scale", frame=frame)


def look_at(o, target):
    d = Vector(target) - o.location
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def camera(name, loc, target, lens=35):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_fit = "VERTICAL"  # 9:16 중앙 크롭 시 세로 화각 유지
    o = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(o)
    o.location = loc
    look_at(o, target)
    return o


def cam_move(o, f0, f1, loc0, tgt0, loc1, tgt1, steps=6):
    """위치·타깃을 선형 보간하며 중간 키마다 look-at을 다시 계산
    (회전만 직선 보간하면 크레인/트래킹 중 피사체가 화면 밖으로 밀림)."""
    loc0, tgt0, loc1, tgt1 = map(Vector, (loc0, tgt0, loc1, tgt1))
    n = steps if (loc0 != loc1 or tgt0 != tgt1) else 1
    for i in range(n + 1):
        t = i / n
        o.location = loc0.lerp(loc1, t)
        look_at(o, tgt0.lerp(tgt1, t))
        fr = round(f0 + (f1 - f0) * t)
        o.keyframe_insert("location", frame=fr)
        o.keyframe_insert("rotation_euler", frame=fr)


def iter_fcurves(obj):
    ad = obj.animation_data
    if not (ad and ad.action):
        return []
    act = ad.action
    if hasattr(act, "fcurves") and len(act.fcurves):
        return list(act.fcurves)
    # Blender 4.4+ layered action
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for bag in getattr(strip, "channelbags", []):
                out.extend(bag.fcurves)
    return out


def linear(obj):
    for fc in iter_fcurves(obj):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"


# ---------------------------------------------------------------- 인물 (블록아웃 마네킹)
def person(name, loc, top, bottom, skin="#E8C4A0", height=1.7, seated=False, hair="#111111", bald=False, facing=-1):
    """facing: -1 = -Y 방향을 봄(기본), +1 = +Y 방향을 봄. 앉은 자세의 다리·뒷머리 위치에 반영."""
    root = empty(name, loc)
    x, y, z = loc
    if seated:
        add("cube", name + "_legs", (x, y + 0.25 * facing, z + 0.5), (0.18, 0.3, 0.08), material=mat(bottom, bottom), parent=root)
        torso_z, head_z = z + 0.85, z + 1.3
    else:
        add("cyl", name + "_legs", (x, y, z + 0.45), (0.15, 0.15, 0.45), material=mat(bottom, bottom), parent=root)
        torso_z, head_z = z + height * 0.62, z + height * 0.9
    add("cyl", name + "_torso", (x, y, torso_z), (0.2, 0.14, 0.3), material=mat(top, top), parent=root)
    add("sphere", name + "_head", (x, y, head_z), (0.12, 0.13, 0.14), material=mat(skin, skin), parent=root)
    if not bald:
        add("sphere", name + "_hair", (x, y - 0.02 * facing, head_z + 0.03), (0.13, 0.13, 0.12), material=mat(hair, hair), parent=root)
    return root


def mascot(name, loc):
    x, y, z = loc
    root = empty(name, loc)
    purple, cream, yellow = "#6030A8", "#F5E6CC", "#FCC024"
    add("cyl", name + "_body", (x, y, z + 0.45), (0.22, 0.2, 0.3), material=mat("mascot_purple", purple), parent=root)
    add("sphere", name + "_head", (x, y, z + 0.95), (0.26, 0.24, 0.24), material=mat("mascot_cream", cream), parent=root)
    add("torus", name + "_scarf", (x, y, z + 0.73), (0.22, 0.22, 0.5), material=mat("mascot_yellow", yellow), parent=root,
        major_radius=1, minor_radius=0.25)
    add("cyl", name + "_cap", (x, y, z + 1.2), (0.25, 0.25, 0.07), material=mat("mascot_purple", purple), parent=root)
    add("cube", name + "_M", (x, y - 0.26, z + 1.2), (0.06, 0.01, 0.05), material=mat("mascot_yellow_e", yellow, 3), parent=root)
    return root


# ---------------------------------------------------------------- 세트
def set_room(ox):
    """S01_C01 / S02_C02A / S03_C01A — 늦은 밤 학생 방."""
    wall = mat("room_wall", "#3A4250")
    add("plane", "room_floor", (ox, 0, 0), (4, 4, 1), material=mat("room_floor", "#2A2E36"))
    add("cube", "room_wall_back", (ox, 3, 1.5), (4, 0.05, 1.5), material=wall)
    add("cube", "room_wall_side", (ox - 3, 0, 1.5), (0.05, 4, 1.5), material=wall)
    add("cube", "room_wall_side_r", (ox + 3, 0, 1.5), (0.05, 4, 1.5), material=wall)  # S03_C01 대칭 와이드용
    add("cube", "desk", (ox, 1.2, 0.75), (0.8, 0.4, 0.03), material=mat("desk", "#5A4632"))
    for i, (dx, h) in enumerate([(-0.55, 0.25), (-0.35, 0.18), (0.5, 0.3)]):
        add("cube", f"books_{i}", (ox + dx, 1.35, 0.78 + h / 2), (0.12, 0.17, h / 2),
            material=mat(f"book{i}", ["#6A7A99", "#8A6A5A", "#5A7A6A"][i]))
    add("cube", "workbook_open", (ox, 1.05, 0.79), (0.22, 0.15, 0.005), material=mat("paper", "#D8D8D0"))
    phone = add("cube", "phone_room", (ox + 0.3, 1.0, 0.79), (0.035, 0.07, 0.004), material=mat("phone_screen_room", "#FFD9A0"))
    light("lamp_room", "SPOT", (ox - 0.4, 1.3, 1.6), "#FFB36B", 60, rot=(20, 0, 0), size=70)
    person("seoyun_real", (ox, 0.55, 0), "#F2F2F2", "#2A3550", seated=True, facing=1)  # 책상(+Y)을 봄
    add("cube", "chair", (ox, 0.45, 0.45), (0.25, 0.25, 0.03), material=mat("chair", "#222222"))
    fill = light("room_fill_cool", "AREA", (ox + 1.5, -1.5, 2.5), "#6F8FB8", 40, rot=(50, 0, 30), size=3)
    return dict(phone=phone, fill=fill, face=(ox, 0.55, 1.3))


def set_busstop(ox):
    """S01_C02 / S02_C02B / S03_C01B — 퇴근길 정류장."""
    add("plane", "street_ground", (ox, 0, 0), (12, 8, 1), material=mat("asphalt", "#1E2228"))
    add("cube", "sidewalk", (ox, 1.5, 0.08), (12, 2, 0.08), material=mat("sidewalk", "#3A3E44"))
    for i, dx in enumerate((-1.4, 1.4)):
        add("cube", f"shelter_post_{i}", (ox + dx, 2.4, 1.25), (0.05, 0.05, 1.25), material=mat("metal", "#555B63"))
    add("cube", "shelter_roof", (ox, 2.2, 2.5), (1.6, 0.6, 0.05), material=mat("metal", "#555B63"))
    add("cube", "shelter_back", (ox, 2.75, 1.3), (1.5, 0.03, 0.9), material=mat("glass", "#7A8AA0", 0.3))
    for i, dx in enumerate((-6, 6)):
        add("cyl", f"streetlight_pole_{i}", (ox + dx, 1, 2.5), (0.06, 0.06, 2.5), material=mat("metal", "#555B63"))
        light(f"streetlight_{i}", "SPOT", (ox + dx, 1, 4.9), "#9FB4D6", 400, size=80)
    car = add("cube", "passing_car_light", (ox - 15, -2, 0.6), (0.6, 0.2, 0.1), material=mat("carlight", "#FFEED0", 20))
    loc_key(car, f(3), (ox - 15, -2, 0.6))
    loc_key(car, f(7), (ox + 15, -2, 0.6))
    phone = add("cube", "phone_stop", (ox + 0.18, 1.55, 1.25), (0.035, 0.004, 0.07), rot=(-20, 0, 0),
                material=mat("phone_screen_stop", "#FFD9A0"))
    person("junho_real", (ox, 1.8, 0.16), "#1C2440", "#1C2440")
    add("cube", "junho_bag", (ox + 0.25, 1.85, 1.0), (0.05, 0.18, 0.15), material=mat("bag", "#2B2B2B"))
    fill = light("stop_fill_cool", "AREA", (ox, -3, 3), "#5A78A8", 80, rot=(60, 0, 0), size=6)
    return dict(phone=phone, fill=fill, face=(ox, 1.8, 1.7))


def set_bus(name, loc):
    """참고 이미지 기준 버스: 둥근 셔틀, 로열 인디고, 노란 라인, 측면 metaBus."""
    x, y, z = loc
    root = empty(name, loc)
    body = add("cube", name + "_body", (x, y, z + 1.6), (5.5, 1.25, 1.4), material=mat("bus_indigo", "#181890", rough=0.3), parent=root)
    bev = body.modifiers.new("bevel", "BEVEL")
    bev.width, bev.segments = 0.5, 6
    add("cube", name + "_stripe", (x, y - 1.27, z + 0.85), (5.4, 0.02, 0.06), material=mat("bus_yellow", "#FCC024", 4), parent=root)
    add("cube", name + "_windows", (x + 0.3, y - 1.27, z + 2.1), (4.6, 0.02, 0.45), material=mat("bus_window", "#FFC98A", 2.5), parent=root)
    add("cube", name + "_side_hl", (x, y - 1.26, z + 1.3), (5.3, 0.01, 0.12), material=mat("bus_peri", "#6060E4"), parent=root)
    add("cube", name + "_door", (x - 3.6, y - 1.28, z + 1.4), (0.6, 0.02, 1.0), material=mat("bus_door", "#FFD9A0", 3), parent=root)
    text(name + "_logo", "metaBus", (x + 1.5, y - 1.31, z + 1.25), size=0.55, color="#FFFFFF", emit=3, parent=root)
    for i, dx in enumerate((-3.6, 3.6)):
        add("cyl", f"{name}_wheel_{i}", (x + dx, y - 1.0, z + 0.45), (0.45, 0.45, 0.25), rot=(90, 0, 0), material=mat("tire", "#111111"), parent=root)
    add("cube", name + "_headlight", (x - 5.5, y - 0.7, z + 1.0), (0.05, 0.25, 0.12), material=mat("headlight", "#FFF4D6", 15), parent=root)
    return root


def set_magic_stop(ox):
    """S03_C02 — metaBus 정류장 (밤하늘, M 사인)."""
    add("plane", "magic_ground", (ox, 0, 0), (20, 10, 1), material=mat("magic_ground", "#3C30B4"))
    add("cube", "magic_road_glow", (ox, 2.9, 0.01), (20, 0.08, 0.01), material=mat("starroad", "#906CFC", 4))
    add("cyl", "m_sign_pole", (ox - 4, 1.5, 1.2), (0.05, 0.05, 1.2), material=mat("metal", "#555B63"))
    add("cube", "m_sign", (ox - 4, 1.5, 2.6), (0.35, 0.05, 0.35), material=mat("m_sign", "#FCC024", 5))
    text("m_sign_M", "M", (ox - 4, 1.44, 2.6), size=0.5, color="#0C0C6C", emit=0)
    for i in range(30):  # 떠 있는 별
        add("sphere", f"star_{i}", (ox - 15 + (i * 7.3) % 30, 6 + (i * 3.1) % 6, 3 + (i * 1.7) % 6), (0.05, 0.05, 0.05),
            material=mat("star", "#FFFFFF", 8), segments=8, ring_count=4)
    # 버스는 인물 뒤(+Y) 차선에 서고, 문·로고가 있는 면(-Y)이 인물·카메라를 향한다
    BY = 4.6
    bus = set_bus("bus_arrive", (ox + 30, BY, 0))
    loc_key(bus, f(12.0), (ox + 30, BY, 0))
    loc_key(bus, f(13.2), (ox + 1.5, BY, 0))
    m = mascot("mascot_door", (ox - 2.1, BY - 1.75, 0))
    scale_key(m, 1, 0.001)
    scale_key(m, f(13.0), 0.001)
    scale_key(m, f(13.3), 1.0)
    person("seoyun_magic", (ox - 3.0, 1.2, 0), "#F2F2F2", "#2A3550", height=1.6)
    person("junho_magic", (ox - 1.3, 1.0, 0), "#1C2440", "#1C2440")
    light("magic_warm", "AREA", (ox - 2, -4, 4), "#FFC98A", 400, rot=(50, 0, 0), size=8)


def set_bus_interior(ox):
    """S04_C01 — 버스 내부."""
    add("plane", "int_floor", (ox, 0, 0), (6, 1.3, 1), material=mat("int_floor", "#2A2470"))
    add("cube", "int_wall_l", (ox, 1.3, 1.2), (6, 0.05, 1.2), material=mat("int_wall", "#181890"))
    add("cube", "int_wall_r", (ox, -1.3, 1.2), (6, 0.05, 1.2), material=mat("int_wall", "#181890"))
    add("cube", "int_ceiling", (ox, 0, 2.4), (6, 1.3, 0.05), material=mat("int_ceiling", "#3C30B4"))
    add("cube", "int_ceiling_light", (ox, 0, 2.34), (5.5, 0.08, 0.01), material=mat("int_light", "#FCC024", 6))
    for i in range(5):
        for side in (-0.8, 0.8):
            add("cube", f"seat_{i}_{side}", (ox - 4 + i * 2, side, 0.45), (0.35, 0.3, 0.1), material=mat("seat", "#6060E4"))
    person("seoyun_bus", (ox, 0.8, 0.1), "#F2F2F2", "#2A3550", seated=True)
    person("junho_bus", (ox, -0.8, 0.1), "#1C2440", "#1C2440", seated=True)
    glow = light("int_glow", "POINT", (ox, 0, 1.8), "#FFC98A", 10)
    energy_key(glow, f(14), 10)
    energy_key(glow, f(16), 600)
    return dict(center=(ox, 0, 1.2))


def pov_hands(prefix, cam_loc, color, prop):
    """POV 손 블록아웃: 카메라 앞 아래쪽에 손 2개 + 소품."""
    x, y, z = cam_loc
    for i, dx in enumerate((-0.12, 0.12)):
        add("cube", f"{prefix}_hand_{i}", (x + dx, y + 0.35, z - 0.35), (0.05, 0.08, 0.025), material=mat(prefix + "_hand", color))
    if prop == "beads":
        add("torus", f"{prefix}_beads", (x, y + 0.38, z - 0.33), (0.1, 0.1, 0.1), material=mat("beads", "#6B3E1F"),
            major_radius=1, minor_radius=0.12)
    if prop == "poles":
        for i, dx in enumerate((-0.12, 0.12)):
            add("cyl", f"{prefix}_pole_{i}", (x + dx, y + 0.6, z - 0.9), (0.012, 0.012, 0.6), rot=(25, 0, 0), material=mat("pole", "#C0C0C0"))
        for i, dx in enumerate((-0.15, 0.15)):
            add("cube", f"{prefix}_ski_{i}", (x + dx, y + 0.5, z - 1.62), (0.05, 0.9, 0.01), material=mat("ski", "#E03C3C"))


def set_temple(ox):
    """S04_C02 A — 새벽 산사."""
    add("plane", "temple_ground", (ox, 0, 0), (15, 15, 1), material=mat("temple_ground", "#B8A88A"))
    add("cube", "temple_hall", (ox, 6, 1.5), (3, 1.5, 1.5), material=mat("temple_wood", "#8A3B2A"))
    add("cone", "temple_roof", (ox, 6, 3.6), (4.2, 2.2, 0.8), material=mat("temple_roof", "#3A3A3A"), vertices=4)
    for i, dx in enumerate((-12, -5, 6, 13)):
        add("cone", f"mountain_t_{i}", (ox + dx, 25, 0), (7, 7, 6 + i % 2 * 3), material=mat("mountain", "#6F8A8A"))
    person("junho_monk", (ox, 1, 0), "#7A7A7A", "#7A7A7A", bald=True)
    light("temple_sun", "SUN", (ox, 0, 10), "#FFE2B0", 3, rot=(55, 0, -30))
    pov = (ox, -4, 1.6)
    pov_hands("monk", pov, "#E8C4A0", "beads")
    return dict(monk_face=(ox, 1, 1.55), pov=pov)


SLOPE_DEG = 15


def slope_z(y):
    """스키 슬로프 표면 높이 (y=-9 부근이 꼭대기)."""
    return 7.76 - max(0.0, y + 9) * math.tan(math.radians(SLOPE_DEG))


def set_ski(ox):
    """S04_C02 B / S05_C01 — 스키장."""
    add("plane", "ski_slope", (ox, 20, 0), (12, 30, 1), rot=(-SLOPE_DEG, 0, 0), material=mat("snow", "#F4F8FF", rough=0.3))
    add("plane", "ski_top", (ox, -13, 7.76), (12, 4, 1), material=mat("snow", "#F4F8FF", rough=0.3))
    for i, dx in enumerate((-25, -12, 14, 28)):
        add("cone", f"mountain_s_{i}", (ox + dx, 60, -5), (14, 14, 18 + i % 2 * 6), material=mat("mountain_snow", "#DDE6F2"))
    for i in range(10):  # 속도감용 깃발
        y = 0 + i * 5
        add("cyl", f"ski_flag_{i}", (ox + (3 if i % 2 else -3), y, slope_z(y) + 0.6), (0.04, 0.04, 0.6), material=mat("flag", "#FCC024", 2))
    light("ski_sun", "SUN", (ox, 0, 20), "#FFF2D6", 5, rot=(45, 0, 20))
    skier = person("seoyun_skier", (ox, -10, 7.76), "#E03C3C", "#2A2A2A", height=1.6)
    loc_key(skier, f(19), (ox, -10, 7.76))
    loc_key(skier, f(21), (ox - 2, 25, slope_z(25)))
    linear(skier)
    pov = (ox + 4, -13, 9.4)
    pov_hands("ski", pov, "#E03C3C", "poles")
    return dict(pov=pov)


def set_race(ox):
    """S05_C02 — 카레이싱 트랙 (직선 구간)."""
    add("plane", "track", (ox, 0, 0), (120, 6, 1), material=mat("track", "#2A2A30"))
    add("plane", "grass_l", (ox, 12, -0.01), (120, 6, 1), material=mat("grass", "#3E8A3E"))
    add("plane", "grass_r", (ox, -12, -0.01), (120, 6, 1), material=mat("grass", "#3E8A3E"))
    for i in range(40):  # 연석·기둥 = 속도감
        c = "#E03C3C" if i % 2 else "#F4F4F4"
        add("cube", f"curb_{i}", (ox - 110 + i * 6, 6.1, 0.1), (1.5, 0.15, 0.1), material=mat("curb" + c, c))
        add("cyl", f"marker_{i}", (ox - 110 + i * 6, -7, 1), (0.1, 0.1, 1), material=mat("marker", "#FCC024", 2))
    car = empty("race_car", (ox - 60, 0, 0))
    add("cube", "race_car_body", (ox - 60, 0, 0.5), (2.2, 0.9, 0.35), material=mat("race_car", "#6030A8", rough=0.2), parent=car)
    add("sphere", "race_car_helmet", (ox - 60.3, 0, 1.0), (0.22, 0.22, 0.22), material=mat("helmet", "#FCC024"), parent=car)
    loc_key(car, f(21), (ox - 60, 0, 0))
    loc_key(car, f(23), (ox + 60, 0, 0))
    linear(car)
    light("race_sun", "SUN", (ox, 0, 20), "#FFB070", 4, rot=(70, 0, -60))


def set_stadium(ox):
    """S05_C03 / S06_C01 — 야구장."""
    add("plane", "field", (ox, 0, 0), (30, 30, 1), material=mat("field", "#2F7A3A"))
    add("plane", "infield", (ox, -10, 0.01), (8, 8, 1), rot=(0, 0, 45), material=mat("infield", "#B07A4A"))
    for tier in range(6):
        add("cube", f"stand_{tier}", (ox, 22 + tier * 1.6, 0.5 + tier * 0.9), (30, 0.8, 0.5), material=mat("stand", "#3C30B4"))
        for i in range(24):
            if (i + tier) % 3 == 0:
                continue
            c = ["#FCC024", "#F4F4F4", "#6060E4"][(i + tier) % 3]
            add("cyl", f"fan_{tier}_{i}", (ox - 23 + i * 2, 22 + tier * 1.6, 1.4 + tier * 0.9), (0.2, 0.2, 0.4),
                material=mat("fan" + c, c), vertices=8)
    floods = []
    for i, dx in enumerate((-28, 28)):
        add("cyl", f"flood_pole_{i}", (ox + dx, 30, 8), (0.2, 0.2, 8), material=mat("metal", "#555B63"))
        floods.append(light(f"floodlight_{i}", "SPOT", (ox + dx, 30, 16), "#FFF6E0", 6000, rot=(50, 0, 180 + (20 if dx < 0 else -20)), size=70))
    for name, dx in (("seoyun_fan", -0.6), ("junho_fan", 0.6)):
        p = person(name, (ox + dx, 21.2, 1.0), "#FCC024", "#2A3550", height=1.6 if "seoyun" in name else 1.7)
        add("cyl", name + "_stick", (ox + dx + 0.25, 21.2, 2.9), (0.03, 0.03, 0.3), material=mat("stick", "#FCC024", 6), parent=p)
    mascot("mascot_stadium", (ox + 1.35, 21.2, 1.0))  # 9:16 안전 영역 안쪽
    sunset = light("stadium_sunset", "SUN", (ox, 0, 20), "#FF8A4A", 0, rot=(80, 0, 150))
    energy_key(sunset, f(25.0), 0)
    energy_key(sunset, f(25.1), 5)
    energy_key(sunset, f(27), 0.5)
    for fl in floods:
        energy_key(fl, f(25.0), 6000)
        energy_key(fl, f(25.1), 500)
        energy_key(fl, f(27), 50)
    return dict(stands=(ox, 21.2, 2.2))


def set_endcard(ox, font):
    """S06_C02~C04 — 알림 UI, 로고, URL (실제 제작은 모션그래픽, 여기선 타이밍 확인용)."""
    add("plane", "end_bg", (ox, 3, 0), (20, 20, 1), rot=(90, 0, 0), material=mat("end_bg", "#0C0C6C"))
    card = empty("noti_card", (ox, 2.9, 0))
    add("cube", "noti_panel", (ox, 2.95, 0), (1.6, 0.02, 0.85), material=mat("noti_panel_end", "#F4F2FF", 0.25), parent=card)
    for i, (body, z, size, c) in enumerate([("metaBus", 0.55, 0.22, "#181890"),
                                             ("새로운 경험이 기다리고 있습니다.", 0.2, 0.12, "#333355"),
                                             ("metaBus에 참여하시겠습니까?", -0.05, 0.13, "#181890")]):
        text(f"noti_line_{i}", body, (ox, 2.9, z), size=size, color=c, emit=0, font=font, parent=card)
    add("cube", "noti_button", (ox, 2.92, -0.5), (0.6, 0.02, 0.15), material=mat("noti_btn_end", "#FCC024", 0.3), parent=card)
    text("noti_btn_text", "참여하기", (ox, 2.89, -0.5), size=0.13, color="#0C0C6C", emit=0, font=font, parent=card)
    logo = empty("logo", (ox, 2.9, 0.1))
    add("cube", "logo_ticket", (ox - 1.4, 2.95, 0.1), (0.38, 0.02, 0.28), material=mat("logo_yellow", "#FCC024", 0.4), parent=logo)
    text("logo_M", "M", (ox - 1.4, 2.9, 0.1), size=0.42, color="#111111", emit=0, parent=logo)
    text("logo_word", "metaBus", (ox + 0.4, 2.9, 0.1), size=0.6, color="#C8B8FF", emit=3, parent=logo)
    url = text("url", "metabus.app", (ox, 2.9, -0.6), size=0.22, color="#FFFFFF", emit=2)
    # 표시 타이밍: 카드(27–28초) → 로고(28초~) → URL(29초~)
    for o, on, off in ((card, f(27), f(28)), (logo, f(28), None), (url, f(29), None)):
        scale_key(o, 1, 0.001)
        scale_key(o, on - 1, 0.001)
        scale_key(o, on + 4, 1.0)
        if off:
            scale_key(o, off - 3, 1.0)
            scale_key(o, off, 0.001)
    glow = light("end_glow", "POINT", (ox, 1, 0.5), "#FFC98A", 0)
    energy_key(glow, f(28), 0)
    energy_key(glow, f(28.5), 200)
    energy_key(glow, f(29.5), 200)
    energy_key(glow, f(30), 0)
    return dict(center=(ox, 2.9, 0))


def set_phone_closeup(ox, font):
    """S02_C01 — 폰 화면 인서트 (동일 알림 UI)."""
    add("plane", "pc_dark", (ox, 0, 0), (3, 3, 1), material=mat("pc_dark", "#14161C"))
    add("cube", "pc_phone", (ox, 0, 0.02), (0.4, 0.8, 0.02), material=mat("pc_body", "#0A0A0A"))
    add("cube", "pc_screen", (ox, 0, 0.045), (0.37, 0.76, 0.005), material=mat("pc_screen", "#2A2A40", 0.5))
    add("cube", "pc_card", (ox, 0.15, 0.055), (0.33, 0.2, 0.003), material=mat("pc_card", "#F4F2FF", 1.5))
    for i, (body, dy, size) in enumerate([("metaBus", 0.27, 0.06), ("새로운 경험이 기다리고 있습니다.", 0.19, 0.03),
                                           ("metaBus에 참여하시겠습니까?", 0.12, 0.035)]):
        text(f"pc_line_{i}", body, (ox, dy, 0.062), size=size, color="#181890", emit=0.5, font=font, rot=(0, 0, 0))
    add("cube", "pc_btn", (ox, 0.02, 0.06), (0.14, 0.035, 0.002), material=mat("noti_btn", "#FCC024", 2))
    text("pc_btn_t", "참여하기", (ox, 0.02, 0.064), size=0.03, color="#0C0C6C", emit=0, font=font, rot=(0, 0, 0))
    glow = light("pc_glow", "POINT", (ox, 0, 0.4), "#FFC98A", 2)
    energy_key(glow, f(7), 2)
    energy_key(glow, f(8.5), 30)
    return dict(center=(ox, 0.1, 0.05))


# ---------------------------------------------------------------- world (색감 전환)
def setup_world():
    w = bpy.data.worlds.new("previs_world")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    keys = [  # (sec, color, strength): 현실 쿨톤 → 초대 → 가상 세계 웜톤 → 엔딩
        (0, "#1A2230", 0.4), (7, "#1A2230", 0.4), (10, "#1E1A3A", 0.5), (12, "#0C0C6C", 0.8),
        (14, "#0C0C6C", 0.8), (16, "#FFD8A8", 1.2), (19, "#BFDFFF", 1.5), (21, "#FFB070", 1.2),
        (23, "#0C0C6C", 0.6), (25.0, "#0C0C6C", 0.6), (25.1, "#FF9A60", 0.8), (27, "#3A1A40", 0.3),
        (27.05, "#0C0C6C", 0.3), (30, "#05052A", 0.1),
    ]
    for sec, c, s in keys:
        bg.inputs["Color"].default_value = hex_rgba(c)
        bg.inputs["Strength"].default_value = s
        bg.inputs["Color"].keyframe_insert("default_value", frame=f(sec))
        bg.inputs["Strength"].keyframe_insert("default_value", frame=f(sec))


# ---------------------------------------------------------------- main
def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, 30 * FPS
    font = bpy.data.fonts.load(FONT_KR)

    shots = json.load(open(STORYBOARD, encoding="utf-8"))["shots"]
    assert len(shots) == 15, "storyboard.json 컷 수가 바뀌었습니다. 스크립트의 컷 정의를 확인하세요."
    assert abs(sum(s["duration_sec"] for s in shots) - 30) < 1e-6

    RX, SX, PCX, MX, IX, TX, KX, RCX, STX, EX = 0, 40, -30, 90, 150, 200, 260, 400, 600, 700
    room = set_room(RX)
    stop = set_busstop(SX)
    pc = set_phone_closeup(PCX, font)
    set_magic_stop(MX)
    inter = set_bus_interior(IX)
    temple = set_temple(TX)
    ski = set_ski(KX)
    set_race(RCX)
    stad = set_stadium(STX)
    end = set_endcard(EX, font)
    setup_world()

    # 폰 알림 빛 (동일 알림음 타이밍)
    pr, ps = room["phone"].data.materials[0], stop["phone"].data.materials[0]
    for m_, keys in ((pr, [(1, 0), (f(2.2), 0), (f(2.5), 8), (f(11), 40)]),
                     (ps, [(1, 0.5), (f(5.5), 0.5), (f(5.8), 8), (f(12), 40)])):
        for fr, v in keys:
            emit_key(m_, fr, v)
    # S02_C02~S03_C01: 폰에서 시작된 따뜻한 빛이 퍼짐
    for name, ph, s_on, s_full in (("room_phone_glow", room["phone"], 8.5, 11), ("stop_phone_glow", stop["phone"], 9.25, 12)):
        g = light(name, "POINT", tuple(ph.location + Vector((0, 0, 0.15))), "#FFC98A", 0)
        energy_key(g, f(s_on), 0)
        energy_key(g, f(s_on + 0.3), 15)
        energy_key(g, f(s_full), 1500)
    # S03_C01: 초대의 빛이 공간을 덮음 (쿨 → 웜)
    for lo, s0, s1 in ((room["fill"], 10, 11), (stop["fill"], 11, 12)):
        e0 = lo.data.energy
        lo.data.color = hex_rgba("#6F8FB8")[:3]
        lo.data.keyframe_insert("color", frame=f(s0))
        energy_key(lo, f(s0), e0)
        lo.data.color = hex_rgba("#FFC98A")[:3]
        lo.data.keyframe_insert("color", frame=f(s1))
        energy_key(lo, f(s1), e0 * 6)

    # ---------------- 컷 정의 (storyboard.json 구간 기준, A/B·몽타주는 구간 안에서 분할)
    cuts = []

    def cut(label, s0, s1, loc0, tgt0, loc1=None, tgt1=None, lens=35):
        cam = camera("CAM_" + label.split()[0] + "_" + str(len(cuts)), loc0, tgt0, lens)
        cam_move(cam, f(s0), f(s1), loc0, tgt0, loc1 or loc0, tgt1 or tgt0)
        linear(cam)
        cuts.append((label, f(s0), cam))
        return cam

    def cut_path(label, keys, lens=35):
        """다중 키 카메라. keys: [(sec, loc, target), ...]"""
        cam = camera("CAM_" + label.split()[0] + "_" + str(len(cuts)), keys[0][1], keys[0][2], lens)
        for sec, loc, tgt in keys:
            cam.location = loc
            look_at(cam, tgt)
            cam.keyframe_insert("location", frame=f(sec))
            cam.keyframe_insert("rotation_euler", frame=f(sec))
        linear(cam)
        cuts.append((label, f(keys[0][0]), cam))
        return cam

    def fade_to_black(cam, s0, s1):
        """카메라 바로 앞 검은 판의 알파로 페이드아웃 (그림자 없음)."""
        m = bpy.data.materials.new("fade_black")
        m.use_nodes = True
        if hasattr(m, "surface_render_method"):
            m.surface_render_method = "BLENDED"
        nt = m.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        mix = nt.nodes.new("ShaderNodeMixShader")
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (0, 0, 0, 1)
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(em.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs["Surface"])
        fac = mix.inputs["Fac"]
        for fr, v in ((f(s0), 0.0), (f(s1), 1.0)):
            fac.default_value = v
            fac.keyframe_insert("default_value", frame=fr)
        bpy.ops.mesh.primitive_plane_add(size=2)
        p = bpy.context.active_object
        p.name = "fade_plane"
        p.data.materials.append(m)
        p.parent = cam
        p.location = (0, 0, -0.15)
        p.rotation_euler = (0, 0, 0)
        if hasattr(p, "visible_shadow"):
            p.visible_shadow = False

    # 카메라 구도표(Shot ID / 구도 / 움직임) 기준
    # SCENE 01 — 현실
    cut("S01_C01 OTS 3/4 side / slow push-in", 0, 3,
        (RX + 0.55, -0.35, 1.55), (RX + 0.05, 1.1, 0.85), (RX + 0.42, -0.1, 1.5), (RX + 0.05, 1.1, 0.85), 35)
    cut("S01_C02 wide establishing / dolly-in", 3, 7,
        (SX - 1.5, -10, 2.0), (SX, 2, 1.4), (SX - 1.0, -7, 1.8), (SX, 2, 1.4), 24)
    # SCENE 02 — 초대
    cut("S02_C01 top-down insert / static", 7, 8.5, (PCX, 0.15, 1.6), (PCX, 0.15, 0), lens=50)
    ph_r, ph_s = room["phone"].location, stop["phone"].location
    cut("S02_C02-A ECU phone tap / static", 8.5, 9.25, (ph_r.x + 0.2, ph_r.y - 0.38, ph_r.z + 0.3), tuple(ph_r), lens=60)
    cut("S02_C02-B ECU phone tap / static", 9.25, 10, (ph_s.x + 0.2, ph_s.y - 0.4, ph_s.z + 0.18), tuple(ph_s), lens=60)
    # SCENE 03 — 이동
    cut("S03_C01-A wide symmetrical / slow tracking", 10, 11, (RX - 0.3, -3.4, 1.4), (RX - 0.3, 2, 1.0), (RX + 0.3, -3.4, 1.4), (RX + 0.3, 2, 1.0), 22)
    cut("S03_C01-B wide symmetrical / slow tracking", 11, 12, (SX - 0.5, -8, 1.6), (SX - 0.5, 2.4, 1.4), (SX + 0.5, -8, 1.6), (SX + 0.5, 2.4, 1.4), 28)
    cut("S03_C02 low-angle hero / tracking", 12, 14, (MX + 3, -4.5, 0.3), (MX + 8, 4.6, 2.2), (MX - 3, -4.5, 0.3), (MX - 2, 2.5, 1.6), 18)
    # SCENE 04 — 변신 (손 POV 공개)
    cut("S04_C01 interior POV / forward tracking", 14, 16, (IX - 5.5, 0, 1.55), (IX + 6, 0, 1.3), (IX - 1.0, 0, 1.5), (IX + 6, 0, 1.3), 24)
    tp = temple["pov"]
    hands_t = (tp[0], tp[1] + 0.35, tp[2] - 0.4)
    cut_path("S04_C02-A first-person POV / tilt-up (monk)",
             [(16, tp, hands_t), (16.6, tp, hands_t), (17.5, tp, (tp[0], tp[1] + 10, tp[2] + 0.4))], lens=26)
    kp = ski["pov"]
    hands_k = (kp[0], kp[1] + 0.5, kp[2] - 0.6)
    cut_path("S04_C02-B first-person POV / tilt-up (ski)",
             [(17.5, kp, hands_k), (18.1, kp, hands_k), (19, kp, (kp[0], kp[1] + 30, kp[2] - 3))], lens=26)
    # SCENE 05 — 체험 몽타주
    cut("S05_C01 side tracking", 19, 21,
        (KX + 7, -10, 8.76), (KX, -10, 8.66), (KX + 5, 25, slope_z(25) + 1.0), (KX - 2, 25, slope_z(25) + 0.9), 35)

    def car_x(t):  # set_race 키: 21초 RCX-60 → 23초 RCX+60 (등속)
        return RCX - 60 + 60 * (t - 21)

    cut("S05_C02-A low-angle chase", 21, 22.2,
        (car_x(21) - 8, 0, 0.5), (car_x(21) + 4, 0, 0.7), (car_x(22.2) - 7, 0, 0.5), (car_x(22.2) + 4, 0, 0.7), 28)
    cut("S05_C02-B driver POV (Newtake candidate)", 22.2, 23,
        (car_x(22.2) + 0.2, 0, 1.35), (car_x(22.2) + 30, 0, 1.0), (car_x(23) + 0.2, 0, 1.35), (car_x(23) + 30, 0, 1.0), 24)
    cut("S05_C03 medium two-shot / crane-up", 23, 25, (STX, 18.2, 2.6), (STX, 21.2, 2.5), (STX, 16, 7.5), (STX, 21.2, 2.4), 40)
    # SCENE 06 — 재초대
    c = cut("S06_C01 wide back shot / fade-out", 25, 27, (STX + 0.3, 24.4, 4.6), (STX, 5, 0.5), (STX + 0.3, 24.0, 4.5), (STX, 5, 0.5), 24)
    fade_to_black(c, 25.8, 27)
    # S06_C02~C04: 최종 인코딩에서 05_PRODUCTION/motion_graphics/ending 영상으로 교체 (아래는 블록아웃)
    cut("S06_C02 invitation again", 27, 28, (EX, -4, 0), end["center"], lens=50)
    cut("S06_C03 logo", 28, 29, (EX, -4, 0), end["center"], lens=50)
    cut("S06_C04 metabus.app", 29, 30, (EX, -4, 0), end["center"], lens=50)

    for label, frame, cam in cuts:
        m = sc.timeline_markers.new(label, frame=frame)
        m.camera = cam
    sc.camera = cuts[0][2]

    # 렌더 설정
    r = sc.render
    r.engine = "BLENDER_EEVEE"
    r.resolution_x, r.resolution_y, r.resolution_percentage = 1280, 720, 100
    if hasattr(sc, "eevee") and hasattr(sc.eevee, "taa_render_samples"):
        sc.eevee.taa_render_samples = 8
    r.use_stamp = True
    for attr in ("use_stamp_date", "use_stamp_render_time", "use_stamp_camera", "use_stamp_lens", "use_stamp_scene",
                 "use_stamp_filename", "use_stamp_memory", "use_stamp_hostname", "use_stamp_frame_range"):
        if hasattr(r, attr):
            setattr(r, attr, False)
    r.use_stamp_marker = True
    r.use_stamp_time = True
    r.use_stamp_frame = True
    r.stamp_font_size = 18
    r.image_settings.file_format = "PNG"

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "previs.blend"))
    print(f"[previs] cuts={len(cuts)} frames={sc.frame_end} saved previs.blend")
    return sc


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    scene = build()
    if "--render" in argv:
        out = argv[argv.index("--render") + 1]
        os.makedirs(out, exist_ok=True)
        if "--frames" in argv:  # 테스트: --frames 10,100,200
            for fr in map(int, argv[argv.index("--frames") + 1].split(",")):
                scene.frame_set(fr)
                scene.render.filepath = os.path.join(out, f"test_{fr:04d}")
                bpy.ops.render.render(write_still=True)
        else:
            if "--end" in argv:  # 예: --end 648 (27초까지만, 엔딩은 모션그래픽으로 교체)
                scene.frame_end = int(argv[argv.index("--end") + 1])
            scene.render.filepath = os.path.join(out, "f_")
            bpy.ops.render.render(animation=True)
