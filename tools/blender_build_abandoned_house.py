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


def clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_pbr_material(
    name: str,
    base_color: tuple[float, float, float, float],
    roughness: float,
    metallic: float = 0.0,
    emission_color: tuple[float, float, float, float] | None = None,
    emission_strength: float = 0.0,
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    if bsdf is not None:
        vcol_node = nodes.new(type="ShaderNodeVertexColor")
        vcol_node.layer_name = "Col"
        mix_node = nodes.new(type="ShaderNodeMix")
        mix_node.data_type = 'RGBA'
        mix_node.blend_type = 'MULTIPLY'
        mix_node.inputs[0].default_value = 1.0
        mix_node.inputs[6].default_value = base_color
        links.new(vcol_node.outputs["Color"], mix_node.inputs[7])
        links.new(mix_node.outputs[2], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if emission_color is not None and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = emission_color
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def add_box(
    name: str,
    size: tuple[float, float, float],
    location: tuple[float, float, float],
    mat: bpy.types.Material,
    bevel_width: float = 0.03,
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    obj.data.materials.append(mat)
    if bevel_width > 0.0:
        bev = obj.modifiers.new(name="Bevel", type='BEVEL')
        bev.width = bevel_width
        bev.segments = 2
        bpy.ops.object.modifier_apply(modifier=bev.name)
    return obj


def apply_gothic_vertex_cavity(obj: bpy.types.Object, base_y_min: float = 0.0) -> None:
    bake_3tone_gothic_vertex_colors(obj, z_min=base_y_min, z_max=base_y_min + 6.5)


def build_house_variant(
    filename: str,
    width_x: float,
    depth_y: float,
    wall_height: float,
    roof_peak: float,
    sag_amount: float,
    has_side_annex: bool,
) -> None:
    clear_scene()

    mat_plinth = make_pbr_material("WeatheredStonePlinth", (0.17, 0.17, 0.18, 1.0), roughness=0.88)
    mat_plaster = make_pbr_material("GrimDaubPlaster", (0.24, 0.22, 0.19, 1.0), roughness=0.90)
    mat_timber = make_pbr_material("CharredOakTimber", (0.08, 0.06, 0.05, 1.0), roughness=0.82)
    mat_roof = make_pbr_material("DarkSlateRoof", (0.10, 0.11, 0.13, 1.0), roughness=0.78)
    mat_boards = make_pbr_material("RottedBoardPlank", (0.16, 0.12, 0.08, 1.0), roughness=0.86)
    mat_recess = make_pbr_material("DarkInteriorRecess", (0.03, 0.03, 0.04, 1.0), roughness=0.95)
    mat_iron = make_pbr_material("WroughtIron", (0.11, 0.11, 0.13, 1.0), roughness=0.48, metallic=0.85)

    parts: list[bpy.types.Object] = []
    sub_cnt = 0

    # 1. Mandatory 2.5m deep stone foundation plinth (Z = -2.5m to Z = 0.0m)
    plinth = add_box(
        "FoundationPlinth",
        (width_x + 0.4, depth_y + 0.4, 2.5),
        (0.0, 0.0, -1.25),
        mat_plinth,
        bevel_width=0.06,
    )
    parts.append(plinth)
    sub_cnt += 1

    # 2. Main upper house body (Z = 0.0 to wall_height) with BOOLEAN DIFFERENCE cavities
    front_y = -depth_y * 0.5
    body = add_box(
        "HouseBody",
        (width_x, depth_y, wall_height),
        (0.0, 0.0, wall_height * 0.5),
        mat_plaster,
        bevel_width=0.04,
    )
    body.data.materials.append(mat_recess)

    cutters: list[bpy.types.Object] = []
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, front_y + 0.12, 1.15))
    door_cutter = bpy.context.active_object
    door_cutter.scale = (1.35, 0.55, 2.30)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    cutters.append(door_cutter)

    win_x_offset = width_x * 0.30
    for sx in (-1.0, 1.0):
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(sx * win_x_offset, front_y + 0.10, 1.65),
        )
        wc = bpy.context.active_object
        wc.scale = (1.15, 0.45, 1.35)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        cutters.append(wc)

    for sx in (-1.0, 1.0):
        for sy in (-depth_y * 0.24, depth_y * 0.24):
            bpy.ops.mesh.primitive_cube_add(
                size=1.0,
                location=(sx * (width_x * 0.5 - 0.10), sy, 1.70),
            )
            swc = bpy.context.active_object
            swc.scale = (0.45, 1.10, 1.30)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            cutters.append(swc)

    bpy.ops.object.select_all(action='DESELECT')
    for c in cutters:
        c.select_set(True)
    bpy.context.view_layer.objects.active = cutters[0]
    bpy.ops.object.join()
    combined_cutter = bpy.context.active_object
    combined_cutter.name = "HouseWindowDoorCutters"
    combined_cutter.data.materials.append(mat_recess)

    bool_mod = body.modifiers.new(name="CarveOpenings", type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.solver = 'EXACT'
    bool_mod.object = combined_cutter
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    bpy.data.objects.remove(combined_cutter, do_unlink=True)
    parts.append(body)
    sub_cnt += 1

    # 3. Pitched Gothic Gable Roof Core with subtle vertex sag
    bm_roof = bmesh.new()
    rx = width_x * 0.5 + 0.45
    ry = depth_y * 0.5 + 0.50
    z_base = wall_height - 0.05
    z_top = wall_height + roof_peak

    y_stations = [-ry, -ry * 0.5, 0.0, ry * 0.5, ry]
    station_rings = []
    for y_val in y_stations:
        mid_factor = 1.0 - (abs(y_val) / ry) ** 2
        sag = -sag_amount * mid_factor
        skew_x = 0.08 * mid_factor if has_side_annex else -0.06 * mid_factor
        v_left_eave = bm_roof.verts.new((-rx, y_val, z_base + sag * 0.3))
        v_left_inner = bm_roof.verts.new((-rx + 0.25, y_val, z_base - 0.20 + sag * 0.3))
        v_peak_top = bm_roof.verts.new((skew_x, y_val, z_top + sag))
        v_peak_inner = bm_roof.verts.new((skew_x, y_val, z_top - 0.28 + sag))
        v_right_eave = bm_roof.verts.new((rx, y_val, z_base + sag * 0.3))
        v_right_inner = bm_roof.verts.new((rx - 0.25, y_val, z_base - 0.20 + sag * 0.3))
        station_rings.append((v_left_eave, v_left_inner, v_peak_top, v_peak_inner, v_right_eave, v_right_inner))

    for i in range(len(station_rings) - 1):
        a0, a1, a2, a3, a4, a5 = station_rings[i]
        b0, b1, b2, b3, b4, b5 = station_rings[i + 1]
        bm_roof.faces.new((a0, b0, b2, a2))
        bm_roof.faces.new((a2, b2, b4, a4))
        bm_roof.faces.new((a1, a3, b3, b1))
        bm_roof.faces.new((a3, a5, b5, b3))
        bm_roof.faces.new((a0, a1, b1, b0))
        bm_roof.faces.new((a4, b4, b5, a5))

    for ring, flip in ((station_rings[0], False), (station_rings[-1], True)):
        v0, v1, v2, v3, v4, v5 = ring
        if not flip:
            bm_roof.faces.new((v0, v2, v3, v1))
            bm_roof.faces.new((v2, v4, v5, v3))
        else:
            bm_roof.faces.new((v0, v1, v3, v2))
            bm_roof.faces.new((v2, v3, v5, v4))

    bmesh.ops.recalc_face_normals(bm_roof, faces=bm_roof.faces)
    roof_mesh = bpy.data.meshes.new("PitchedRoofMesh")
    bm_roof.to_mesh(roof_mesh)
    bm_roof.free()
    roof_obj = bpy.data.objects.new("PitchedRoof", roof_mesh)
    bpy.context.collection.objects.link(roof_obj)
    roof_obj.data.materials.append(mat_roof)
    parts.append(roof_obj)
    sub_cnt += 1

    # Gable filler triangles on front and back of house
    for sy in (-1.0, 1.0):
        bm_g = bmesh.new()
        gy1 = sy * (depth_y * 0.5 - 0.15)
        gy2 = sy * (depth_y * 0.5 + 0.02)
        gx_half = width_x * 0.5
        va0 = bm_g.verts.new((-gx_half, gy1, wall_height - 0.05))
        va1 = bm_g.verts.new((gx_half, gy1, wall_height - 0.05))
        va2 = bm_g.verts.new((0.0, gy1, wall_height + roof_peak - 0.15))
        vb0 = bm_g.verts.new((-gx_half, gy2, wall_height - 0.05))
        vb1 = bm_g.verts.new((gx_half, gy2, wall_height - 0.05))
        vb2 = bm_g.verts.new((0.0, gy2, wall_height + roof_peak - 0.15))
        bm_g.faces.new((va0, va1, va2))
        bm_g.faces.new((vb0, vb2, vb1))
        bm_g.faces.new((va0, vb0, vb1, va1))
        bm_g.faces.new((va1, vb1, vb2, va2))
        bm_g.faces.new((va2, vb2, vb0, va0))
        bmesh.ops.recalc_face_normals(bm_g, faces=bm_g.faces)
        g_mesh = bpy.data.meshes.new(f"GableWall_{sy}")
        bm_g.to_mesh(g_mesh)
        bm_g.free()
        g_obj = bpy.data.objects.new(f"GableWall_{sy}", g_mesh)
        bpy.context.collection.objects.link(g_obj)
        g_obj.data.materials.append(mat_plaster)
        parts.append(g_obj)
        sub_cnt += 1

    # 4. Ultra-Detail Kitbashing Pass inside a unified BMesh:
    #    - Plinth Ashlar Quoins & Sagging Multi-Stone Porch Steps
    #    - Heavy Timber Framing, Diagonal Bracing & 3D Wooden Pegs
    #    - Shuttered Gothic Windows with Wrought-Iron Hinges & Boarded Planks
    #    - 120+ Individual Overlapping 3D Roof Slates & Ridge Tiles
    #    - Exposed Brick Chimney Stack with 24 Brick Courses & Chimney Pots
    bm_det = bmesh.new()
    # Material indices on bm_det: 0=mat_plinth, 1=mat_timber, 2=mat_roof, 3=mat_boards, 4=mat_iron

    # 4a. Sagging Multi-Stone Porch Steps + Foundation Quoins
    for step_idx in range(5):
        step_h = 0.22
        step_d = 0.36
        step_y = front_y - 0.2 - (step_idx + 0.5) * step_d
        foundation_depth = 1.6 - step_idx * 0.18
        step_w = 2.2 + step_idx * 0.12
        # Split each step into 3 uneven sagging ashlar stones
        for s_block in range(3):
            bw = (step_w / 3.0) - 0.015
            bx = -step_w * 0.5 + (s_block + 0.5) * (step_w / 3.0)
            sag_z = -0.025 if s_block == 1 else _det_hash(step_idx, s_block, 11) * 0.012
            tilt_y = math.radians(_det_hash(step_idx, s_block, 19) * 1.8)
            _add_bm_beveled_box(
                bm_det,
                (bw, step_d + 0.04, foundation_depth),
                (bx, step_y, -step_idx * step_h - foundation_depth * 0.5 + sag_z),
                rot_euler=(0.0, tilt_y, 0.0),
                bevel_width=0.014,
                mat_idx=0,
            )
            sub_cnt += 1

    # Plinth corner quoins
    for q_r in range(5):
        qz = -2.2 + q_r * 0.45
        for sx in (-1.0, 1.0):
            for sy in (-1.0, 1.0):
                _add_bm_beveled_box(
                    bm_det,
                    (0.45, 0.45, 0.38),
                    (sx * (width_x * 0.5 + 0.04), sy * (depth_y * 0.5 + 0.04), qz),
                    bevel_width=0.015,
                    mat_idx=0,
                )
                sub_cnt += 1

    # 4b. Timber Framing Posts, Girts, Diagonal Braces & 3D Pegs
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            _add_bm_beveled_box(
                bm_det,
                (0.26, 0.26, wall_height + 0.1),
                (sx * width_x * 0.5, sy * depth_y * 0.5, wall_height * 0.5),
                bevel_width=0.012,
                mat_idx=1,
            )
            sub_cnt += 1

    for z_h in (0.12, wall_height * 0.52, wall_height - 0.10):
        for sy in (-1.0, 1.0):
            _add_bm_beveled_box(bm_det, (width_x + 0.24, 0.22, 0.20), (0.0, sy * depth_y * 0.5, z_h), bevel_width=0.012, mat_idx=1)
            sub_cnt += 1
            # 6 Protruding oak joinery pegs along each horizontal beam
            for peg_i in range(6):
                px = -width_x * 0.42 + peg_i * (width_x * 0.84 / 5.0)
                _add_bm_beveled_box(
                    bm_det,
                    (0.036, 0.08, 0.036),
                    (px, sy * (depth_y * 0.5 + 0.10), z_h),
                    bevel_width=0.004,
                    mat_idx=3,
                )
                sub_cnt += 1
        for sx in (-1.0, 1.0):
            _add_bm_beveled_box(bm_det, (0.22, depth_y + 0.24, 0.20), (sx * width_x * 0.5, 0.0, z_h), bevel_width=0.012, mat_idx=1)
            sub_cnt += 1

    # Doorway frame, planked gothic door leaf & wrought-iron strap hinges
    for sx in (-0.72, 0.72):
        _add_bm_beveled_box(bm_det, (0.16, 0.28, 2.38), (sx, front_y - 0.02, 1.19), bevel_width=0.012, mat_idx=1)
        sub_cnt += 1
    _add_bm_beveled_box(bm_det, (1.68, 0.30, 0.20), (0.0, front_y - 0.02, 2.36), bevel_width=0.012, mat_idx=1)
    sub_cnt += 1

    # Recessed Heavy Planked Door inside doorway cavity (5 vertical oak planks + 2 iron hinge straps)
    for dp_i in range(5):
        dpx = -0.48 + dp_i * 0.24
        _add_bm_beveled_box(bm_det, (0.22, 0.06, 2.22), (dpx, front_y + 0.18, 1.12), bevel_width=0.006, mat_idx=3)
        sub_cnt += 1
    for dh_z in (0.55, 1.75):
        _add_bm_beveled_box(bm_det, (0.95, 0.03, 0.06), (-0.12, front_y + 0.14, dh_z), bevel_width=0.004, mat_idx=4)
        sub_cnt += 1

    # 4c. Shuttered Gothic Windows with Wrought-Iron Hinges & Crooked Boarded Planks
    for sx in (-1.0, 1.0):
        wx = sx * win_x_offset
        # Window timber frame surround
        _add_bm_beveled_box(bm_det, (1.36, 0.24, 0.14), (wx, front_y - 0.04, 0.96), bevel_width=0.010, mat_idx=1)
        _add_bm_beveled_box(bm_det, (1.32, 0.22, 0.12), (wx, front_y - 0.04, 2.36), bevel_width=0.010, mat_idx=1)
        sub_cnt += 2
        # Left & Right wooden shutters (slightly ajar/crooked) + iron strap hinges
        for sh_side in (-1.0, 1.0):
            sh_x = wx + sh_side * 0.68
            sh_yaw = sh_side * math.radians(16.0)
            sh_tilt = _det_hash(int(sx + 2), int(sh_side + 2), 31) * 0.05
            _add_bm_beveled_box(
                bm_det,
                (0.46, 0.05, 1.28),
                (sh_x, front_y - 0.08, 1.66),
                rot_euler=(sh_tilt, 0.0, sh_yaw),
                bevel_width=0.006,
                mat_idx=3,
            )
            for hz_off in (-0.42, 0.42):
                _add_bm_beveled_box(
                    bm_det,
                    (0.36, 0.03, 0.045),
                    (sh_x, front_y - 0.10, 1.66 + hz_off),
                    rot_euler=(sh_tilt, 0.0, sh_yaw),
                    bevel_width=0.003,
                    mat_idx=4,
                )
            sub_cnt += 3
        # Crooked boarded planks nailed across window
        for p_idx, z_off in enumerate((1.32, 1.66, 1.98)):
            tilt = (0.07 if (p_idx % 2 == 0) else -0.09) * sx
            _add_bm_beveled_box(
                bm_det,
                (1.28, 0.06, 0.15),
                (wx, front_y - 0.03, z_off),
                rot_euler=(0.0, tilt, 0.0),
                bevel_width=0.008,
                mat_idx=3,
            )
            sub_cnt += 1

    # 4d. 112 Individual Overlapping 3D Roof Slate Rows & Ridge Cap Tiles
    slope_angle = math.atan2(roof_peak, rx)
    slope_len = math.hypot(rx, roof_peak)
    slate_rows = 7
    slate_cols = 8
    for side_s in (-1.0, 1.0):
        for sr in range(slate_rows):
            t_r = (sr + 0.5) / slate_rows
            dist_from_eave = t_r * (slope_len - 0.15)
            base_sx = side_s * (rx - dist_from_eave * math.cos(slope_angle))
            base_sz = z_base + dist_from_eave * math.sin(slope_angle) + 0.03
            stagger = 0.5 if (sr % 2 == 1) else 0.0
            col_len = (ry * 1.92) / slate_cols
            for sc in range(slate_cols):
                sy_pos = -ry * 0.94 + (sc + 0.5 + (stagger - 0.25) * 0.3) * col_len
                mid_f = max(0.0, 1.0 - (abs(sy_pos) / ry) ** 2)
                sag_z = -sag_amount * mid_f * (0.3 + 0.7 * t_r)
                jit_rot = _det_hash(sr, sc, int(side_s + 5)) * 0.035
                _add_bm_beveled_box(
                    bm_det,
                    (slope_len / slate_rows + 0.06, col_len - 0.03, 0.038),
                    (base_sx, sy_pos, base_sz + sag_z),
                    rot_euler=(jit_rot, side_s * slope_angle + 0.03, 0.0),
                    bevel_width=0.005,
                    mat_idx=2,
                )
                sub_cnt += 1

    # Ridge cap tiles along the roof peak
    for rc_i in range(10):
        ry_pos = -ry * 0.90 + rc_i * ((ry * 1.80) / 9.0)
        mid_f = max(0.0, 1.0 - (abs(ry_pos) / ry) ** 2)
        sag_z = -sag_amount * mid_f
        _add_bm_beveled_box(
            bm_det,
            (0.32, (ry * 1.80) / 9.0 - 0.02, 0.10),
            (0.0, ry_pos, z_top + sag_z + 0.03),
            bevel_width=0.008,
            mat_idx=2,
        )
        sub_cnt += 1

    # 4e. Exposed Brick & Ashlar Chimney Stack with 18 Individual Brick/Stone Courses & Twin Chimney Pots
    chimney_x = width_x * 0.36 if not has_side_annex else -width_x * 0.36
    chimney_y = depth_y * 0.28
    chimney_bot = -2.40
    chimney_top = wall_height + roof_peak + 0.95
    # Core shaft
    _add_bm_beveled_box(
        bm_det,
        (0.88, 0.88, chimney_top - chimney_bot),
        (chimney_x, chimney_y, (chimney_top + chimney_bot) * 0.5),
        bevel_width=0.015,
        mat_idx=0,
    )
    sub_cnt += 1
    # 16 Stepped Brick/Quoin Courses around the upper chimney stack
    for c_row in range(16):
        cz = wall_height * 0.35 + c_row * ((chimney_top - wall_height * 0.35) / 16.0)
        cw_r = 0.96 if (c_row % 2 == 0) else 0.92
        _add_bm_beveled_box(
            bm_det,
            (cw_r, cw_r, 0.18),
            (chimney_x + _det_hash(c_row, 7, 3) * 0.01, chimney_y, cz),
            bevel_width=0.010,
            mat_idx=0,
        )
        sub_cnt += 1
    # Chimney crown corbel & 2 octagonal terracotta/stone chimney pots
    _add_bm_beveled_box(bm_det, (1.12, 1.12, 0.16), (chimney_x, chimney_y, chimney_top + 0.06), bevel_width=0.015, mat_idx=0)
    for pot_dx in (-0.22, 0.22):
        _add_bm_beveled_box(bm_det, (0.24, 0.24, 0.42), (chimney_x + pot_dx, chimney_y, chimney_top + 0.32), bevel_width=0.012, mat_idx=4)
    sub_cnt += 3

    # Optional side annex for House B variety
    if has_side_annex:
        _add_bm_beveled_box(bm_det, (2.8, depth_y * 0.62, 2.5), (width_x * 0.5 + 1.3, 0.4, -1.25), bevel_width=0.025, mat_idx=0)
        _add_bm_beveled_box(bm_det, (2.6, depth_y * 0.58, wall_height * 0.72), (width_x * 0.5 + 1.2, 0.4, wall_height * 0.36), bevel_width=0.020, mat_idx=3)
        _add_bm_beveled_box(
            bm_det,
            (3.0, depth_y * 0.66, 0.22),
            (width_x * 0.5 + 1.3, 0.4, wall_height * 0.75),
            rot_euler=(0.0, 0.28, 0.0),
            bevel_width=0.020,
            mat_idx=2,
        )
        sub_cnt += 3

    bmesh.ops.recalc_face_normals(bm_det, faces=bm_det.faces)
    det_mesh = bpy.data.meshes.new("HouseDetailKitMesh")
    bm_det.to_mesh(det_mesh)
    bm_det.free()
    det_obj = bpy.data.objects.new("HouseDetailKit", det_mesh)
    bpy.context.collection.objects.link(det_obj)
    det_obj.data.materials.append(mat_plinth)
    det_obj.data.materials.append(mat_timber)
    det_obj.data.materials.append(mat_roof)
    det_obj.data.materials.append(mat_boards)
    det_obj.data.materials.append(mat_iron)
    parts.append(det_obj)

    # Join all parts into single unified asset with multi-slot materials
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    final_obj = bpy.context.active_object
    final_obj.name = os.path.splitext(filename)[0]

    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

    apply_gothic_vertex_cavity(final_obj, base_y_min=-1.2)

    out_dir = os.path.join(os.getcwd(), "assets", "models")
    os.makedirs(out_dir, exist_ok=True)
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
    print(f"[DetailKit] {filename} built with {sub_cnt} physical 3D sub-elements -> {out_path}")


if __name__ == "__main__":
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
