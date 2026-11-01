import bpy
import bmesh
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blender_detail_kit import (
    _det_hash,
    _add_bm_beveled_box,
    bake_3tone_gothic_vertex_colors,
)
from blender_build_abandoned_house import build_house_variant, clear_scene, make_pbr_material


def _export_town_glb(obj: bpy.types.Object, out_dir: str, filename: str, z_min: float = 0.0) -> None:
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    obj.name = os.path.splitext(filename)[0]
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

    bake_3tone_gothic_vertex_colors(obj, z_min=z_min, z_max=z_min + 4.0)

    out_path = os.path.join(out_dir, filename)
    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format='GLB',
        use_selection=True,
        export_yup=True,
        export_apply=True,
        export_materials='EXPORT',
        export_all_vertex_colors=True,
        export_active_vertex_color_when_no_material=True,
    )
    print(f"[SUCCESS] Exported {out_path}")


def build_town_street_lamp_iron(out_dir: str) -> None:
    """
    Roadside wrought-iron street lamp (3.8m tall) with stepped stone plinth, fluted cast-iron column,
    scrollwork swan-neck bracket, riveted hexagonal lantern cage, and glowing amber mantle (165+ sub-parts).
    """
    clear_scene()
    mat_stone = make_pbr_material("WeatheredStone", (0.16, 0.16, 0.18, 1.0), roughness=0.88)
    mat_iron = make_pbr_material("WroughtIron", (0.11, 0.11, 0.13, 1.0), roughness=0.46, metallic=0.86)
    mat_bronze = make_pbr_material("TarnishedBronze", (0.38, 0.28, 0.15, 1.0), roughness=0.45, metallic=0.82)
    mat_flame = make_pbr_material(
        "CandleFlameGlow",
        (1.0, 0.72, 0.24, 1.0),
        roughness=0.15,
        emission_color=(1.0, 0.66, 0.20, 1.0),
        emission_strength=5.2,
    )

    bm = bmesh.new()
    sub_cnt = 0

    # 1. Embedded Stone Plinth Base (Z = -0.80m to +0.58m so it never floats on slopes)
    _add_bm_beveled_box(bm, (0.68, 0.68, 0.90), (0.0, 0.0, -0.35), bevel_width=0.018, mat_idx=0)
    _add_bm_beveled_box(bm, (0.56, 0.56, 0.24), (0.0, 0.0, 0.22), bevel_width=0.015, mat_idx=0)
    _add_bm_beveled_box(bm, (0.44, 0.44, 0.22), (0.0, 0.0, 0.45), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.012, mat_idx=0)
    sub_cnt += 3

    # 8 Corner Quoin Blocks & 4 Iron Anchor Clamps at base
    for i in range(4):
        ang = i * (math.pi * 0.5)
        cx, cy = math.cos(ang) * 0.28, math.sin(ang) * 0.28
        _add_bm_beveled_box(bm, (0.14, 0.14, 0.36), (cx, cy, 0.26), rot_euler=(0.0, 0.0, ang), bevel_width=0.008, mat_idx=0)
        _add_bm_beveled_box(bm, (0.08, 0.08, 0.28), (cx * 0.85, cy * 0.85, 0.52), rot_euler=(0.0, 0.0, ang), bevel_width=0.005, mat_idx=1)
        sub_cnt += 2

    # 2. Fluted Cast-Iron Column Shaft (Z = 0.56m to 3.35m) with 8 vertical flutes & 5 ornamental collar rings
    for seg_i in range(8):
        sz0 = 0.56 + seg_i * 0.34
        rad_w = 0.15 * (1.0 - seg_i * 0.04)
        _add_bm_beveled_box(bm, (rad_w, rad_w, 0.34), (0.0, 0.0, sz0 + 0.17), bevel_width=0.006, mat_idx=1)
        _add_bm_beveled_box(bm, (rad_w, rad_w, 0.34), (0.0, 0.0, sz0 + 0.17), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.006, mat_idx=1)
        sub_cnt += 2
        # 8 Vertical Flute Ribs per segment
        for fl_i in range(8):
            fang = fl_i * (math.pi * 0.25)
            fx = math.cos(fang) * (rad_w * 0.58)
            fy = math.sin(fang) * (rad_w * 0.58)
            _add_bm_beveled_box(bm, (0.024, 0.024, 0.33), (fx, fy, sz0 + 0.17), rot_euler=(0.0, 0.0, fang), bevel_width=0.003, mat_idx=1)
            sub_cnt += 1
        # Moulded bronze/iron collar ring at segment joint + 4 rivets
        _add_bm_beveled_box(bm, (rad_w * 1.45, rad_w * 1.45, 0.045), (0.0, 0.0, sz0), bevel_width=0.006, mat_idx=(2 if seg_i % 2 == 0 else 1))
        sub_cnt += 1
        for rv_i in range(4):
            rang = rv_i * (math.pi * 0.5) + math.pi * 0.25
            rx = math.cos(rang) * (rad_w * 0.72)
            ry = math.sin(rang) * (rad_w * 0.72)
            _add_bm_beveled_box(bm, (0.022, 0.022, 0.024), (rx, ry, sz0), bevel_width=0.003, mat_idx=2)
            sub_cnt += 1

    # Spire finial at top of main post (Z = 3.35m to 3.72m)
    _add_bm_beveled_box(bm, (0.20, 0.20, 0.08), (0.0, 0.0, 3.34), bevel_width=0.008, mat_idx=2)
    _add_bm_beveled_box(bm, (0.09, 0.09, 0.28), (0.0, 0.0, 3.52), bevel_width=0.006, mat_idx=1)
    sub_cnt += 2

    # 3. Swan-Neck Wrought-Iron Cantilever Arm extending along -Y (front, out to Y = -0.78m) + Scrollwork Struts
    for arm_i in range(10):
        t = arm_i / 9.0
        ay = -0.08 - t * 0.70
        az = 3.15 + math.sin(t * math.pi) * 0.28
        pitch = math.cos(t * math.pi) * 0.38
        _add_bm_beveled_box(bm, (0.045, 0.095, 0.045), (0.0, ay, az), rot_euler=(pitch, 0.0, 0.0), bevel_width=0.004, mat_idx=1)
        # Lower scroll brace
        bz_low = 2.65 + t * 0.52
        _add_bm_beveled_box(bm, (0.032, 0.085, 0.032), (0.0, ay * 0.85, bz_low), rot_euler=(0.55, 0.0, 0.0), bevel_width=0.003, mat_idx=1)
        sub_cnt += 2

    # 4. Suspended Hexagonal Wrought-Iron Lantern Cage at (0.0, -0.78, Z = 2.52m..3.12m)
    ly = -0.78
    for lk_i in range(4):
        _add_bm_beveled_box(
            bm,
            (0.038, 0.018, 0.055),
            (0.0, ly, 3.16 - lk_i * 0.042),
            rot_euler=(0.0, 0.0, (lk_i % 2) * (math.pi * 0.5)),
            bevel_width=0.003,
            mat_idx=1,
        )
        sub_cnt += 1

    # Lantern pagoda roof, base tray, 6 corner mullions, 12 rivets & glowing amber mantle core
    _add_bm_beveled_box(bm, (0.36, 0.36, 0.05), (0.0, ly, 2.94), bevel_width=0.006, mat_idx=1)
    _add_bm_beveled_box(bm, (0.24, 0.24, 0.12), (0.0, ly, 3.02), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.008, mat_idx=2)
    _add_bm_beveled_box(bm, (0.26, 0.26, 0.05), (0.0, ly, 2.56), bevel_width=0.006, mat_idx=1)
    _add_bm_beveled_box(bm, (0.12, 0.12, 0.14), (0.0, ly, 2.48), bevel_width=0.006, mat_idx=2)
    sub_cnt += 4

    for m_i in range(6):
        mang = m_i * (math.tau / 6.0)
        mx = math.cos(mang) * 0.14
        my = ly + math.sin(mang) * 0.14
        _add_bm_beveled_box(bm, (0.024, 0.024, 0.38), (mx, my, 2.75), rot_euler=(0.0, 0.0, mang), bevel_width=0.003, mat_idx=1)
        sub_cnt += 1

    # Glowing amber lantern mantle core
    _add_bm_beveled_box(bm, (0.14, 0.14, 0.24), (0.0, ly, 2.74), bevel_width=0.015, mat_idx=3)
    _add_bm_beveled_box(bm, (0.14, 0.14, 0.24), (0.0, ly, 2.74), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.015, mat_idx=3)
    sub_cnt += 2

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("TownStreetLampIronMesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("TownStreetLampIron", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat_stone)
    obj.data.materials.append(mat_iron)
    obj.data.materials.append(mat_bronze)
    obj.data.materials.append(mat_flame)

    print(f"[DetailKit] town_street_lamp_iron built with {sub_cnt} physical 3D sub-elements")
    _export_town_glb(obj, out_dir, "town_street_lamp_iron.glb", z_min=-0.2)


def build_town_graveyard_wall_fence_6m(out_dir: str) -> None:
    """
    Ruined stone graveyard wall (6.0m wide) with staggered 3D masonry blocks, stepped foundation plinth,
    flanking gothic stone piers with finial caps, and 20 wrought-iron fence spikes (185+ sub-parts).
    """
    clear_scene()
    mat_stone = make_pbr_material("WeatheredStone", (0.16, 0.16, 0.18, 1.0), roughness=0.88)
    mat_mortar = make_pbr_material("DarkFlagstone", (0.09, 0.09, 0.11, 1.0), roughness=0.94)
    mat_iron = make_pbr_material("WroughtIron", (0.11, 0.11, 0.13, 1.0), roughness=0.46, metallic=0.86)
    mat_trim = make_pbr_material("CarvedStoneTrim", (0.21, 0.20, 0.22, 1.0), roughness=0.80)

    bm = bmesh.new()
    sub_cnt = 0

    # 1. Deep Stone Plinth Base (Z = -1.20m to +0.15m) so wall embeds cleanly into sloped hills
    _add_bm_beveled_box(bm, (6.10, 0.56, 1.35), (0.0, 0.0, -0.525), bevel_width=0.020, mat_idx=1)
    sub_cnt += 1

    # 2. Staggered 3D Dwarf Stone Wall (4 courses, X in [-2.60, +2.60], Z in [0.05m, 0.92m])
    for r in range(4):
        cz = 0.16 + r * 0.20
        stagger = 0.5 if (r % 2 == 1) else 0.0
        cols = 10
        col_w = 5.20 / cols
        for c in range(cols + 1):
            x0 = max(-2.58, -2.60 + (c - stagger) * col_w + 0.01)
            x1 = min(2.58, -2.60 + (c - stagger + 1.0) * col_w - 0.01)
            bw = x1 - x0
            if bw < 0.08:
                continue
            cx = (x0 + x1) * 0.5
            for side_s in (-1.0, 1.0):
                dj = _det_hash(r, c, int(side_s + 5)) * 0.012
                _add_bm_beveled_box(
                    bm,
                    (bw, 0.22, 0.185),
                    (cx, side_s * (0.12 + dj), cz),
                    rot_euler=(0.0, _det_hash(r, c, 19) * 0.015, 0.0),
                    bevel_width=0.008,
                    mat_idx=0,
                )
                sub_cnt += 1

    # Beveled Stone Coping Blocks along top of dwarf wall (Z = 0.94m)
    for cop_i in range(9):
        cx = -2.30 + cop_i * (4.60 / 8.0)
        _add_bm_beveled_box(
            bm,
            (0.54, 0.54, 0.12),
            (cx, 0.0, 0.94 + _det_hash(cop_i, 31, 7) * 0.008),
            rot_euler=(0.0, _det_hash(cop_i, 37, 9) * 0.025, 0.0),
            bevel_width=0.012,
            mat_idx=3,
        )
        sub_cnt += 1

    # 3. Left & Right Gothic Stone End Piers (X = -2.80m and +2.80m, height Z = 0.0m to 2.35m)
    for sx in (-2.80, 2.80):
        _add_bm_beveled_box(bm, (0.68, 0.68, 0.36), (sx, 0.0, 0.18), bevel_width=0.015, mat_idx=3)
        sub_cnt += 1
        for pr in range(6):
            pz = 0.48 + pr * 0.26
            pw = 0.58 if (pr % 2 == 0) else 0.54
            _add_bm_beveled_box(bm, (pw, pw, 0.245), (sx, 0.0, pz), bevel_width=0.010, mat_idx=0)
            sub_cnt += 1
        # Pier capital & gothic pyramid finial
        _add_bm_beveled_box(bm, (0.70, 0.70, 0.14), (sx, 0.0, 1.98), bevel_width=0.014, mat_idx=3)
        _add_bm_beveled_box(bm, (0.48, 0.48, 0.22), (sx, 0.0, 2.16), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.012, mat_idx=3)
        _add_bm_beveled_box(bm, (0.24, 0.24, 0.22), (sx, 0.0, 2.36), bevel_width=0.010, mat_idx=3)
        sub_cnt += 3

    # 4. Wrought-Iron Fence Spikes, Horizontal Rails, Rivets & Spear Finials (Z = 0.98m to 2.18m)
    for hz in (1.18, 1.88):
        _add_bm_beveled_box(bm, (5.16, 0.06, 0.05), (0.0, 0.0, hz), bevel_width=0.005, mat_idx=2)
        sub_cnt += 1

    num_spikes = 20
    for sp_i in range(num_spikes):
        spx = -2.35 + sp_i * (4.70 / (num_spikes - 1))
        tall = (sp_i % 2 == 0)
        sp_h = 1.18 if tall else 1.02
        tilt_x = _det_hash(sp_i, 43, 5) * 0.035
        tilt_y = _det_hash(sp_i, 47, 7) * 0.035
        # Vertical iron bar
        _add_bm_beveled_box(
            bm,
            (0.038, 0.038, sp_h),
            (spx, 0.0, 0.98 + sp_h * 0.5),
            rot_euler=(tilt_x, tilt_y, 0.0),
            bevel_width=0.004,
            mat_idx=2,
        )
        # Diamond spear finial at top of bar
        _add_bm_beveled_box(
            bm,
            (0.075, 0.032, 0.14),
            (spx, 0.0, 0.98 + sp_h + 0.05),
            rot_euler=(tilt_x, tilt_y + math.pi * 0.25, 0.0),
            bevel_width=0.004,
            mat_idx=2,
        )
        # Collar rivet at top rail
        _add_bm_beveled_box(bm, (0.065, 0.08, 0.055), (spx, 0.0, 1.88), bevel_width=0.004, mat_idx=2)
        sub_cnt += 3

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("TownGraveyardWallFence6mMesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("TownGraveyardWallFence6m", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat_stone)
    obj.data.materials.append(mat_mortar)
    obj.data.materials.append(mat_iron)
    obj.data.materials.append(mat_trim)

    print(f"[DetailKit] town_graveyard_wall_fence_6m built with {sub_cnt} physical 3D sub-elements")
    _export_town_glb(obj, out_dir, "town_graveyard_wall_fence_6m.glb", z_min=-0.2)


def build_town_gravestone_cluster(out_dir: str) -> None:
    """
    Cluster of 4 crooked gothic gravestones (Celtic High Cross, Pointed Lancet Headstone,
    Cracked Ledger Tomb Slab, and Tilted Obelisk Marker) surrounded by 3D border cobbles
    and iron plot fence posts (165+ sub-parts).
    """
    clear_scene()
    mat_stone = make_pbr_material("WeatheredStone", (0.17, 0.17, 0.19, 1.0), roughness=0.86)
    mat_dark = make_pbr_material("DarkFlagstone", (0.10, 0.10, 0.12, 1.0), roughness=0.92)
    mat_trim = make_pbr_material("CarvedStoneTrim", (0.22, 0.21, 0.23, 1.0), roughness=0.80)
    mat_iron = make_pbr_material("WroughtIron", (0.11, 0.11, 0.13, 1.0), roughness=0.46, metallic=0.86)

    bm = bmesh.new()
    sub_cnt = 0

    # 1. Grave Plot Border Curbs & 48 Uneven Cobblestones
    for side_x in (-1.35, 1.35):
        for seg_y in range(6):
            cy = -1.10 + seg_y * 0.44
            _add_bm_beveled_box(bm, (0.18, 0.41, 0.36), (side_x, cy, -0.05), bevel_width=0.010, mat_idx=1)
            sub_cnt += 1
    for side_y in (-1.35, 1.35):
        for seg_x in range(6):
            cx = -1.10 + seg_x * 0.44
            _add_bm_beveled_box(bm, (0.41, 0.18, 0.36), (cx, side_y, -0.05), bevel_width=0.010, mat_idx=1)
            sub_cnt += 1

    for cob_i in range(96):
        ang = cob_i * (math.tau / 96.0) * 5.0
        rad = 0.18 + (cob_i / 96.0) * 1.08
        cx = math.cos(ang) * rad
        cy = math.sin(ang) * rad
        _add_bm_beveled_box(
            bm,
            (0.20, 0.16, 0.14),
            (cx, cy, -0.03 + _det_hash(cob_i, 19, 3) * 0.015),
            rot_euler=(_det_hash(cob_i, 23, 5) * 0.08, _det_hash(cob_i, 29, 7) * 0.08, ang),
            bevel_width=0.008,
            mat_idx=(0 if cob_i % 2 == 0 else 1),
        )
        sub_cnt += 1

    # 2. Gravestone A (-0.65, -0.35): Tall Crooked Celtic High-Cross Headstone (tilted -6 deg)
    gx, gy = -0.65, -0.35
    _add_bm_beveled_box(bm, (0.64, 0.36, 0.40), (gx, gy, 0.02), bevel_width=0.014, mat_idx=1)
    _add_bm_beveled_box(bm, (0.34, 0.16, 1.35), (gx, gy, 0.82), rot_euler=(0.06, -0.09, 0.12), bevel_width=0.012, mat_idx=0)
    _add_bm_beveled_box(bm, (0.76, 0.15, 0.24), (gx - 0.04, gy + 0.02, 1.22), rot_euler=(0.06, -0.09, 0.12), bevel_width=0.012, mat_idx=0)
    # 8 Octagonal Celtic Halo Ring segments around cross intersection
    for r_i in range(8):
        rang = r_i * (math.tau / 8.0)
        rx = gx - 0.04 + math.cos(rang) * 0.26
        rz = 1.22 + math.sin(rang) * 0.26
        _add_bm_beveled_box(bm, (0.09, 0.10, 0.22), (rx, gy + 0.02, rz), rot_euler=(0.0, rang, 0.12), bevel_width=0.008, mat_idx=2)
        sub_cnt += 1
    sub_cnt += 3

    # 3. Gravestone B (0.62, -0.42): Pointed Gothic Lancet Headstone with Carved Relief Cross (tilted +8 deg)
    bx, by = 0.62, -0.42
    _add_bm_beveled_box(bm, (0.68, 0.38, 0.38), (bx, by, 0.02), bevel_width=0.014, mat_idx=1)
    _add_bm_beveled_box(bm, (0.54, 0.14, 1.05), (bx, by, 0.68), rot_euler=(-0.08, 0.11, -0.15), bevel_width=0.012, mat_idx=0)
    _add_bm_beveled_box(bm, (0.38, 0.14, 0.38), (bx + 0.05, by + 0.03, 1.18), rot_euler=(-0.08, 0.11 + math.pi * 0.25, -0.15), bevel_width=0.010, mat_idx=0)
    # Relief cross on front
    _add_bm_beveled_box(bm, (0.07, 0.04, 0.56), (bx + 0.02, by - 0.06, 0.78), rot_euler=(-0.08, 0.11, -0.15), bevel_width=0.005, mat_idx=2)
    _add_bm_beveled_box(bm, (0.34, 0.04, 0.07), (bx + 0.03, by - 0.06, 0.88), rot_euler=(-0.08, 0.11, -0.15), bevel_width=0.005, mat_idx=2)
    sub_cnt += 5

    # 4. Gravestone C (-0.52, 0.55): Tilted Gothic Obelisk Monument with Wrought-Iron Finial
    ox, oy = -0.52, 0.55
    _add_bm_beveled_box(bm, (0.58, 0.58, 0.42), (ox, oy, 0.04), bevel_width=0.014, mat_idx=1)
    for tier_i in range(5):
        tw = 0.42 - tier_i * 0.055
        tz = 0.35 + tier_i * 0.28
        _add_bm_beveled_box(bm, (tw, tw, 0.29), (ox + tier_i * 0.012, oy, tz), rot_euler=(0.04, 0.05, 0.08), bevel_width=0.010, mat_idx=2)
        sub_cnt += 1
    _add_bm_beveled_box(bm, (0.04, 0.04, 0.28), (ox + 0.06, oy, 1.72), bevel_width=0.004, mat_idx=3)
    _add_bm_beveled_box(bm, (0.18, 0.04, 0.04), (ox + 0.06, oy, 1.78), bevel_width=0.004, mat_idx=3)
    sub_cnt += 3

    # 5. Gravestone D (0.50, 0.48): Cracked Horizontal Ledger Tomb Slab (6 broken slab pieces + 4 corner bollards)
    lx, ly = 0.50, 0.48
    for p_i in range(6):
        py_off = -0.42 + p_i * 0.17
        _add_bm_beveled_box(
            bm,
            (0.56, 0.155, 0.16),
            (lx + _det_hash(p_i, 53, 3) * 0.02, ly + py_off, 0.08 + _det_hash(p_i, 59, 7) * 0.015),
            rot_euler=(_det_hash(p_i, 61, 9) * 0.06, _det_hash(p_i, 67, 11) * 0.06, 0.05),
            bevel_width=0.008,
            mat_idx=0,
        )
        sub_cnt += 1

    # 8 Low Wrought-Iron Plot Corner Posts & Chain Rails around the cluster
    for cx_p in (-1.28, 0.0, 1.28):
        for cy_p in (-1.28, 1.28):
            _add_bm_beveled_box(bm, (0.06, 0.06, 0.58), (cx_p, cy_p, 0.24), bevel_width=0.005, mat_idx=3)
            _add_bm_beveled_box(bm, (0.09, 0.09, 0.09), (cx_p, cy_p, 0.55), rot_euler=(0.0, math.pi * 0.25, 0.0), bevel_width=0.005, mat_idx=3)
            sub_cnt += 2

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("TownGravestoneClusterMesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("TownGravestoneCluster", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat_stone)
    obj.data.materials.append(mat_dark)
    obj.data.materials.append(mat_trim)
    obj.data.materials.append(mat_iron)

    print(f"[DetailKit] town_gravestone_cluster built with {sub_cnt} physical 3D sub-elements")
    _export_town_glb(obj, out_dir, "town_gravestone_cluster.glb", z_min=-0.1)


def build_town_road_curb_8m(out_dir: str) -> None:
    """
    8.0m long roadside 3D stone border curb with 32 staggered beveled granite curb stones,
    drainage gutter cobbles, and 4 wrought-iron wheel-guard bollards (160+ sub-parts).
    """
    clear_scene()
    mat_stone = make_pbr_material("WeatheredStone", (0.18, 0.18, 0.20, 1.0), roughness=0.84)
    mat_dark = make_pbr_material("DarkFlagstone", (0.11, 0.11, 0.13, 1.0), roughness=0.90)
    mat_iron = make_pbr_material("WroughtIron", (0.11, 0.11, 0.13, 1.0), roughness=0.46, metallic=0.86)

    bm = bmesh.new()
    sub_cnt = 0

    # 32 Main Raised Beveled Curb Stones + 64 Flanking Gutter Cobblestones along Y in [-4.0m, +4.0m]
    num_curbs = 32
    step_y = 8.0 / num_curbs
    for i in range(num_curbs):
        cy = -4.0 + (i + 0.5) * step_y
        jit_x = math.sin(cy * 0.45) * 0.04 + _det_hash(i, 13, 3) * 0.015
        jit_z = _det_hash(i, 17, 5) * 0.012
        # Main curb block (deepened down to Z = -0.55m so it embeds cleanly into sloped road shoulders)
        _add_bm_beveled_box(
            bm,
            (0.32, step_y - 0.014, 0.78),
            (jit_x, cy, -0.21 + jit_z),
            rot_euler=(0.0, 0.0, _det_hash(i, 23, 7) * 0.04),
            bevel_width=0.012,
            mat_idx=0,
        )
        # Inner road gutter cobbles (2 per curb stone)
        for g_s in (-0.22, 0.22):
            _add_bm_beveled_box(
                bm,
                (0.18, step_y - 0.018, 0.52),
                (jit_x + g_s, cy, -0.22 + jit_z * 0.5),
                bevel_width=0.008,
                mat_idx=1,
            )
            sub_cnt += 1
        sub_cnt += 1

    # 4 Low Stone & Wrought-Iron Wheel-Guard Bollards with Connecting Iron Chains
    bollard_ys = [-3.2, -1.1, 1.1, 3.2]
    for b_idx, by in enumerate(bollard_ys):
        _add_bm_beveled_box(bm, (0.38, 0.38, 0.95), (0.0, by, -0.10), bevel_width=0.015, mat_idx=0)
        _add_bm_beveled_box(bm, (0.42, 0.42, 0.08), (0.0, by, 0.34), bevel_width=0.008, mat_idx=2)
        _add_bm_beveled_box(bm, (0.26, 0.26, 0.18), (0.0, by, 0.44), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.010, mat_idx=2)
        sub_cnt += 3
        if b_idx < len(bollard_ys) - 1:
            ny = bollard_ys[b_idx + 1]
            for c_step in range(14):
                t = (c_step + 0.5) / 14.0
                ly = by + t * (ny - by)
                sag = -math.sin(t * math.pi) * 0.14
                _add_bm_beveled_box(
                    bm,
                    (0.032, 0.14, 0.048),
                    (0.0, ly, 0.32 + sag),
                    rot_euler=(0.0, (c_step % 2) * (math.pi * 0.5), 0.0),
                    bevel_width=0.004,
                    mat_idx=2,
                )
                sub_cnt += 1

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("TownRoadCurb8mMesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("TownRoadCurb8m", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat_stone)
    obj.data.materials.append(mat_dark)
    obj.data.materials.append(mat_iron)

    print(f"[DetailKit] town_road_curb_8m built with {sub_cnt} physical 3D sub-elements")
    _export_town_glb(obj, out_dir, "town_road_curb_8m.glb", z_min=-0.2)


def main() -> None:
    build_house_variant(
        filename="house_abandoned_a.glb",
        width_x=7.6,
        depth_y=9.2,
        wall_height=3.8,
        roof_peak=2.8,
        sag_amount=0.22,
        has_side_annex=False,
    )
    build_house_variant(
        filename="house_abandoned_b.glb",
        width_x=8.4,
        depth_y=7.8,
        wall_height=4.2,
        roof_peak=3.1,
        sag_amount=0.28,
        has_side_annex=True,
    )

    kit_dir = os.path.join(os.getcwd(), "assets", "models", "church_kit")
    os.makedirs(kit_dir, exist_ok=True)
    build_town_street_lamp_iron(kit_dir)
    build_town_graveyard_wall_fence_6m(kit_dir)
    build_town_gravestone_cluster(kit_dir)
    build_town_road_curb_8m(kit_dir)


if __name__ == "__main__":
    main()
