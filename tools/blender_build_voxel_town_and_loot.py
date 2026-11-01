"""
Blender Procedural Builder: Wave 1D Town Overworld, Stepped Micro-Voxel Terrain & Loot
Targets (13 GLB models):
  church_kit/:
    - town_street_lamp_iron.glb
    - town_graveyard_wall_fence_6m.glb
    - town_road_curb_8m.glb
    - town_gravestone_cluster.glb
  models/:
    - house_abandoned_a.glb (3.0m deep plinth + entrance steps)
    - house_abandoned_b.glb (3.0m deep plinth + entrance steps)
    - dead_tree_gnarled.glb
    - grass_clump_wild.glb
    - terrain_town.glb (120x120m stepped micro-voxel terrain, 0.18m steps, stairwell cutout)
  items/:
    - loot_blood_echo_cluster.glb
    - loot_occult_relic_talisman.glb
    - loot_alchemical_elixir.glb
    - prop_gothic_reliquary_chest.glb (ChestBase parent, ChestLid child pivoted at Y=+0.41, Z=0.58)
"""

import bpy
import bmesh
import math
import os
import random
import sys
from mathutils import Vector, Euler

# Import shared micro-voxel environment palette
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blender_micro_voxel_kit import create_environment_voxel_palette

CHURCH_KIT_DIR = os.path.join(os.getcwd(), "assets", "models", "church_kit")
ROOT_MODELS_DIR = os.path.join(os.getcwd(), "assets", "models")
ITEMS_DIR = os.path.join(os.getcwd(), "assets", "models", "items")


def clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def _add_bm_beveled_box(
    bm: bmesh.types.BMesh,
    size: tuple[float, float, float],
    center: tuple[float, float, float],
    rot_euler: tuple[float, float, float] = (0.0, 0.0, 0.0),
    bevel_width: float = 0.008,
    mat_idx: int = 0,
) -> None:
    """Appends a 3D beveled box directly into bm with material index mat_idx in O(1) time."""
    ret = bmesh.ops.create_cube(bm, size=1.0)
    verts = ret["verts"]
    sx, sy, sz = size
    for v in verts:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sz

    if abs(rot_euler[0]) > 1e-6 or abs(rot_euler[1]) > 1e-6 or abs(rot_euler[2]) > 1e-6:
        rot_mat = Euler(rot_euler, 'XYZ').to_matrix()
        bmesh.ops.rotate(bm, verts=verts, cent=(0.0, 0.0, 0.0), matrix=rot_mat)

    orig_faces = {f for v in verts for f in v.link_faces}
    orig_edges = {e for v in verts for e in v.link_edges}

    if bevel_width > 0.0:
        bev_ret = bmesh.ops.bevel(
            bm,
            geom=list(orig_edges),
            offset=bevel_width,
            offset_type='OFFSET',
            segments=1,
            profile=0.5,
            affect='EDGES',
        )
        all_verts = [v for v in (set(verts) | set(bev_ret.get("verts", []))) if v.is_valid]
        all_faces = {f for v in all_verts for f in v.link_faces if f.is_valid}
        bmesh.ops.translate(bm, verts=all_verts, vec=center)
        for f in all_faces:
            f.material_index = mat_idx
            f.smooth = False
    else:
        bmesh.ops.translate(bm, verts=verts, vec=center)
        for f in orig_faces:
            if f.is_valid:
                f.material_index = mat_idx
                f.smooth = False


def bake_gothic_vertex_colors(
    obj: bpy.types.Object,
    z_min: float = 0.0,
    z_max: float = 4.0,
) -> None:
    """Computes deterministic cavity and height gradient vertex colors into 'Col' attribute."""
    mesh = obj.data
    if not isinstance(mesh, bpy.types.Mesh):
        return

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    v_factors: dict[int, float] = {}
    for v in bm.verts:
        signed_angles: list[float] = []
        unsigned_angles: list[float] = []
        for e in v.link_edges:
            if len(e.link_faces) == 2:
                try:
                    s_ang = e.calc_face_angle_signed(0.0)
                except ValueError:
                    s_ang = 0.0
                u_ang = e.calc_face_angle(0.0)
                signed_angles.append(s_ang)
                unsigned_angles.append(u_ang)

        min_signed = min(signed_angles) if signed_angles else 0.0
        max_signed = max(signed_angles) if signed_angles else 0.0
        avg_unsigned = sum(unsigned_angles) / max(1, len(unsigned_angles))

        tone = 0.82
        if min_signed < -0.05:
            concave_t = min(1.0, abs(min_signed) / 0.85)
            tone = 0.82 - concave_t * (0.82 - 0.60)
        elif max_signed > 0.35 or avg_unsigned > 0.38:
            convex_t = min(1.0, max(max_signed, avg_unsigned) / 0.95)
            tone = 0.82 + convex_t * (0.99 - 0.82)

        rel_z = v.co.z - z_min
        span_z = max(0.5, z_max - z_min)
        if rel_z < span_z * 0.4:
            soot_t = max(0.0, min(1.0, rel_z / (span_z * 0.4)))
            soot_mult = 0.70 + 0.30 * (soot_t * soot_t)
            tone = max(0.60, tone * soot_mult)

        v_factors[v.index] = max(0.60, min(1.00, tone))

    smoothed: dict[int, float] = {}
    for v in bm.verts:
        nbrs = [other.index for e in v.link_edges for other in e.verts if other != v]
        if nbrs:
            avg_nbr = sum(v_factors[idx] for idx in nbrs) / len(nbrs)
            smoothed[v.index] = max(0.60, min(1.00, v_factors[v.index] * 0.78 + avg_nbr * 0.22))
        else:
            smoothed[v.index] = v_factors[v.index]

    bm.free()

    if "Col" in mesh.color_attributes:
        col_attr = mesh.color_attributes["Col"]
    else:
        col_attr = mesh.color_attributes.new(name="Col", type='BYTE_COLOR', domain='CORNER')

    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            v_idx = mesh.loops[loop_idx].vertex_index
            c = smoothed.get(v_idx, 0.82)
            col_attr.data[loop_idx].color = (c, c, c, 1.0)


def export_single_glb(
    filepath: str,
    target_objs: list[bpy.types.Object],
    apply_transforms: bool = True,
) -> None:
    """Exports specified objects to a glTF 2.0 binary (.glb) file."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in target_objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = target_objs[0]

    bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format='GLB',
        use_selection=True,
        export_yup=True,
        export_apply=apply_transforms,
        export_materials='EXPORT',
        export_all_vertex_colors=True,
        export_active_vertex_color_when_no_material=True,
    )
    sz = os.path.getsize(filepath) if os.path.exists(filepath) else 0
    print(f"[SUCCESS] Exported {filepath} ({sz} bytes)")


def add_branch_mesh(
    bm: bmesh.types.BMesh,
    points: list[tuple[float, float, float]],
    radii: list[float],
    sides: int = 8,
    mat_idx: int = 0,
) -> None:
    """Lofts a tapered multi-segment branch or trunk mesh through 3D points."""
    rings: list[list[bmesh.types.BMVert]] = []
    for idx, (px, py, pz) in enumerate(points):
        r = radii[idx]
        if idx < len(points) - 1:
            dx = points[idx + 1][0] - px
            dy = points[idx + 1][1] - py
            dz = points[idx + 1][2] - pz
        else:
            dx = px - points[idx - 1][0]
            dy = py - points[idx - 1][1]
            dz = pz - points[idx - 1][2]

        fwd = Vector((dx, dy, dz)).normalized()
        up = Vector((0.0, 0.0, 1.0)) if abs(fwd.z) < 0.9 else Vector((1.0, 0.0, 0.0))
        side = fwd.cross(up).normalized()
        norm = side.cross(fwd).normalized()

        ring_verts: list[bmesh.types.BMVert] = []
        for s in range(sides):
            ang = s * (2.0 * math.pi / sides)
            vx = px + (side.x * math.cos(ang) + norm.x * math.sin(ang)) * r
            vy = py + (side.y * math.cos(ang) + norm.y * math.sin(ang)) * r
            vz = pz + (side.z * math.cos(ang) + norm.z * math.sin(ang)) * r
            ring_verts.append(bm.verts.new((vx, vy, vz)))
        rings.append(ring_verts)

    for seg in range(len(rings) - 1):
        r1, r2 = rings[seg], rings[seg + 1]
        for i in range(sides):
            ni = (i + 1) % sides
            face = bm.faces.new((r1[i], r2[i], r2[ni], r1[ni]))
            face.material_index = mat_idx
            face.smooth = True

    cap_base = bm.faces.new(rings[0])
    cap_base.material_index = mat_idx
    cap_tip = bm.faces.new(list(reversed(rings[-1])))
    cap_tip.material_index = mat_idx


# ==============================================================================
# TOWN STREET & GRAVEYARD KIT (4 Models in church_kit/)
# ==============================================================================


def build_town_street_lamp_iron(out_dir: str) -> None:
    """Roadside wrought-iron street lamp (3.8m tall) with embedded stone plinth, fluted column, swan-neck bracket, hexagonal lantern cage, and candle flame glow."""
    clear_scene()
    palette = create_environment_voxel_palette()
    mat_stone = palette["weathered_stone"]
    mat_iron = palette["wrought_iron"]
    mat_bronze = palette["bronze"]
    mat_flame = palette["candle_flame"]

    bm = bmesh.new()
    sub_cnt = 0

    # 1. Embedded Stone Plinth Base (Z = -0.80m to +0.58m so it never floats on slopes)
    _add_bm_beveled_box(bm, (0.68, 0.68, 0.90), (0.0, 0.0, -0.35), bevel_width=0.018, mat_idx=0)
    _add_bm_beveled_box(bm, (0.56, 0.56, 0.24), (0.0, 0.0, 0.22), bevel_width=0.015, mat_idx=0)
    _add_bm_beveled_box(bm, (0.44, 0.44, 0.22), (0.0, 0.0, 0.45), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.012, mat_idx=0)
    sub_cnt += 3

    for i in range(4):
        ang = i * (math.pi * 0.5)
        cx, cy = math.cos(ang) * 0.28, math.sin(ang) * 0.28
        _add_bm_beveled_box(bm, (0.14, 0.14, 0.36), (cx, cy, 0.26), rot_euler=(0.0, 0.0, ang), bevel_width=0.008, mat_idx=0)
        _add_bm_beveled_box(bm, (0.08, 0.08, 0.28), (cx * 0.85, cy * 0.85, 0.52), rot_euler=(0.0, 0.0, ang), bevel_width=0.005, mat_idx=1)
        sub_cnt += 2

    # 2. Fluted Cast-Iron Column Shaft (Z = 0.56m to 3.35m)
    for seg_i in range(8):
        sz0 = 0.56 + seg_i * 0.34
        rad_w = 0.15 * (1.0 - seg_i * 0.04)
        _add_bm_beveled_box(bm, (rad_w, rad_w, 0.34), (0.0, 0.0, sz0 + 0.17), bevel_width=0.006, mat_idx=1)
        _add_bm_beveled_box(bm, (rad_w, rad_w, 0.34), (0.0, 0.0, sz0 + 0.17), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.006, mat_idx=1)
        sub_cnt += 2
        for fl_i in range(8):
            fang = fl_i * (math.pi * 0.25)
            fx = math.cos(fang) * (rad_w * 0.58)
            fy = math.sin(fang) * (rad_w * 0.58)
            _add_bm_beveled_box(bm, (0.024, 0.024, 0.33), (fx, fy, sz0 + 0.17), rot_euler=(0.0, 0.0, fang), bevel_width=0.003, mat_idx=1)
            sub_cnt += 1
        _add_bm_beveled_box(bm, (rad_w * 1.45, rad_w * 1.45, 0.045), (0.0, 0.0, sz0), bevel_width=0.006, mat_idx=(2 if seg_i % 2 == 0 else 1))
        sub_cnt += 1
        for rv_i in range(4):
            rang = rv_i * (math.pi * 0.5) + math.pi * 0.25
            rx = math.cos(rang) * (rad_w * 0.72)
            ry = math.sin(rang) * (rad_w * 0.72)
            _add_bm_beveled_box(bm, (0.022, 0.022, 0.024), (rx, ry, sz0), bevel_width=0.003, mat_idx=2)
            sub_cnt += 1

    # Spire capital at top of main post
    _add_bm_beveled_box(bm, (0.20, 0.20, 0.08), (0.0, 0.0, 3.34), bevel_width=0.008, mat_idx=2)
    _add_bm_beveled_box(bm, (0.09, 0.09, 0.28), (0.0, 0.0, 3.52), bevel_width=0.006, mat_idx=1)
    sub_cnt += 2

    # 3. Swan-neck Cantilever Bracket Arm (arching out toward -Y by 0.72m)
    bracket_pts = [
        (0.0, -0.05, 3.30),
        (0.0, -0.22, 3.42),
        (0.0, -0.44, 3.55),
        (0.0, -0.66, 3.58),
        (0.0, -0.80, 3.45),
        (0.0, -0.80, 3.25),
    ]
    for b_idx in range(len(bracket_pts) - 1):
        p0, p1 = bracket_pts[b_idx], bracket_pts[b_idx + 1]
        mid = ((p0[0] + p1[0]) * 0.5, (p0[1] + p1[1]) * 0.5, (p0[2] + p1[2]) * 0.5)
        dy = p1[1] - p0[1]
        dz = p1[2] - p0[2]
        seg_len = math.hypot(dy, dz)
        pitch = math.atan2(dz, dy)
        _add_bm_beveled_box(bm, (0.045, seg_len, 0.045), mid, rot_euler=(-pitch + math.pi * 0.5, 0.0, 0.0), bevel_width=0.004, mat_idx=1)
        sub_cnt += 1

    # 4. Hexagonal Wrought-Iron Lantern Cage + Glowing Core
    lan_y = -0.80
    lan_z = 2.92
    _add_bm_beveled_box(bm, (0.34, 0.34, 0.05), (0.0, lan_y, lan_z), bevel_width=0.006, mat_idx=1)
    _add_bm_beveled_box(bm, (0.34, 0.34, 0.05), (0.0, lan_y, lan_z), rot_euler=(0.0, 0.0, math.pi / 3.0), bevel_width=0.006, mat_idx=1)
    _add_bm_beveled_box(bm, (0.42, 0.42, 0.06), (0.0, lan_y, lan_z + 0.48), bevel_width=0.006, mat_idx=1)
    _add_bm_beveled_box(bm, (0.42, 0.42, 0.06), (0.0, lan_y, lan_z + 0.48), rot_euler=(0.0, 0.0, math.pi / 3.0), bevel_width=0.006, mat_idx=1)
    sub_cnt += 4

    for c_i in range(6):
        c_ang = c_i * (math.pi / 3.0)
        cx = math.cos(c_ang) * 0.16
        cy = lan_y + math.sin(c_ang) * 0.16
        _add_bm_beveled_box(bm, (0.024, 0.024, 0.48), (cx, cy, lan_z + 0.24), rot_euler=(0.0, 0.0, c_ang), bevel_width=0.003, mat_idx=1)
        sub_cnt += 1

    _add_bm_beveled_box(bm, (0.28, 0.28, 0.16), (0.0, lan_y, lan_z + 0.57), bevel_width=0.006, mat_idx=1)
    _add_bm_beveled_box(bm, (0.04, 0.04, 0.20), (0.0, lan_y, lan_z + 0.72), bevel_width=0.003, mat_idx=2)
    sub_cnt += 2

    # Glowing amber candle mantle core
    _add_bm_beveled_box(bm, (0.12, 0.12, 0.26), (0.0, lan_y, lan_z + 0.22), bevel_width=0.010, mat_idx=3)
    sub_cnt += 1

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

    bake_gothic_vertex_colors(obj, z_min=-0.8, z_max=3.8)
    export_single_glb(os.path.join(out_dir, "town_street_lamp_iron.glb"), [obj])


def build_town_graveyard_wall_fence_6m(out_dir: str) -> None:
    """6m wide gothic perimeter graveyard wall with embedded foundation, ashlar stone courses, end piers, and spear-tipped iron railings."""
    clear_scene()
    palette = create_environment_voxel_palette()
    mat_stone = palette["weathered_stone"]
    mat_trim = palette["carved_stone_trim"]
    mat_iron = palette["wrought_iron"]

    bm = bmesh.new()
    sub_cnt = 0

    # 1. Embedded Foundation Plinth (Z = -1.20m to +0.15m)
    _add_bm_beveled_box(bm, (6.20, 0.64, 1.35), (0.0, 0.0, -0.525), bevel_width=0.025, mat_idx=0)
    sub_cnt += 1

    # 2. 4-course Ashlar Stone Wall (Z = 0.15m to 1.15m)
    for c_i in range(4):
        cz = 0.15 + (c_i + 0.5) * 0.25
        num_blocks = 9
        block_w = 5.20 / num_blocks
        stagger = (c_i % 2) * (block_w * 0.5)
        for b_i in range(num_blocks):
            bx = -2.60 + (b_i + 0.5) * block_w + (stagger if b_i < num_blocks - 1 else 0.0)
            if abs(bx) < 2.55:
                _add_bm_beveled_box(bm, (block_w - 0.02, 0.44, 0.23), (bx, 0.0, cz), bevel_width=0.012, mat_idx=0)
                sub_cnt += 1

    # Stone Wall Coping Cap (Z = 1.15m to 1.28m)
    _add_bm_beveled_box(bm, (5.40, 0.52, 0.13), (0.0, 0.0, 1.215), bevel_width=0.015, mat_idx=1)
    sub_cnt += 1

    # 3. Two End Piers at X = -2.75m and +2.75m
    for px in (-2.75, 2.75):
        _add_bm_beveled_box(bm, (0.64, 0.64, 1.30), (px, 0.0, 0.65), bevel_width=0.020, mat_idx=0)
        _add_bm_beveled_box(bm, (0.72, 0.72, 0.12), (px, 0.0, 1.36), bevel_width=0.015, mat_idx=1)
        _add_bm_beveled_box(bm, (0.54, 0.54, 0.22), (px, 0.0, 1.53), bevel_width=0.010, mat_idx=1)
        sub_cnt += 3

    # 4. Wrought-Iron Railing with 20 Spear Finials (Z = 1.28m to 2.25m)
    _add_bm_beveled_box(bm, (5.10, 0.045, 0.045), (0.0, 0.0, 1.34), bevel_width=0.005, mat_idx=2)
    _add_bm_beveled_box(bm, (5.10, 0.045, 0.045), (0.0, 0.0, 1.95), bevel_width=0.005, mat_idx=2)
    sub_cnt += 2

    for sp_i in range(20):
        sp_x = -2.35 + sp_i * (4.70 / 19.0)
        _add_bm_beveled_box(bm, (0.028, 0.028, 0.82), (sp_x, 0.0, 1.72), bevel_width=0.004, mat_idx=2)
        _add_bm_beveled_box(bm, (0.042, 0.042, 0.14), (sp_x, 0.0, 2.18), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.003, mat_idx=2)
        sub_cnt += 2

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("TownGraveyardWallMesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("TownGraveyardWallFence6m", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat_stone)
    obj.data.materials.append(mat_trim)
    obj.data.materials.append(mat_iron)

    bake_gothic_vertex_colors(obj, z_min=-1.2, z_max=2.3)
    export_single_glb(os.path.join(out_dir, "town_graveyard_wall_fence_6m.glb"), [obj])


def build_town_road_curb_8m(out_dir: str) -> None:
    """8m long modular street curb kit with embedded base, 32 beveled curb stones, drainage gutter cobbles, and 4 mooring bollards with sagging chains."""
    clear_scene()
    palette = create_environment_voxel_palette()
    mat_stone = palette["weathered_stone"]
    mat_cobble = palette["cobble_flagstone"]
    mat_iron = palette["wrought_iron"]

    bm = bmesh.new()
    sub_cnt = 0

    # 1. Embedded Plinth Base (Z = -0.55m to +0.05m)
    _add_bm_beveled_box(bm, (8.10, 0.75, 0.60), (0.0, 0.0, -0.25), bevel_width=0.02, mat_idx=0)
    sub_cnt += 1

    # 2. 32 Beveled Curb Stones (Z = 0.05m to 0.24m)
    num_curbs = 32
    curb_w = 8.0 / num_curbs
    for c_i in range(num_curbs):
        cx = -4.0 + (c_i + 0.5) * curb_w
        _add_bm_beveled_box(bm, (curb_w - 0.015, 0.36, 0.20), (cx, 0.0, 0.15), bevel_width=0.010, mat_idx=0)
        sub_cnt += 1

    # 3. Drainage Gutter Cobbles along curb face (Y = -0.32m)
    for g_i in range(24):
        gx = -3.90 + (g_i + 0.5) * (7.80 / 24.0)
        _add_bm_beveled_box(bm, (0.28, 0.24, 0.12), (gx, -0.28, 0.06), bevel_width=0.008, mat_idx=1)
        sub_cnt += 1

    # 4. 4 Wrought-Iron Mooring Bollards + Sagging Chains
    bollard_xs = (-3.2, -1.07, 1.07, 3.2)
    for bx in bollard_xs:
        _add_bm_beveled_box(bm, (0.16, 0.16, 0.08), (bx, 0.0, 0.28), bevel_width=0.008, mat_idx=2)
        _add_bm_beveled_box(bm, (0.12, 0.12, 0.44), (bx, 0.0, 0.54), bevel_width=0.006, mat_idx=2)
        _add_bm_beveled_box(bm, (0.15, 0.15, 0.08), (bx, 0.0, 0.78), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.008, mat_idx=2)
        sub_cnt += 3

    # Sagging chain links between bollards
    for b_idx in range(len(bollard_xs) - 1):
        x0, x1 = bollard_xs[b_idx], bollard_xs[b_idx + 1]
        span_w = x1 - x0
        for l_i in range(6):
            t = (l_i + 0.5) / 6.0
            lx = x0 + t * span_w
            sag = math.sin(t * math.pi) * 0.18
            lz = 0.68 - sag
            _add_bm_beveled_box(bm, (span_w / 6.5, 0.03, 0.03), (lx, 0.0, lz), bevel_width=0.004, mat_idx=2)
            sub_cnt += 1

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("TownRoadCurb8mMesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("TownRoadCurb8m", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat_stone)
    obj.data.materials.append(mat_cobble)
    obj.data.materials.append(mat_iron)

    bake_gothic_vertex_colors(obj, z_min=-0.55, z_max=0.85)
    export_single_glb(os.path.join(out_dir, "town_road_curb_8m.glb"), [obj])


def build_town_gravestone_cluster(out_dir: str) -> None:
    """Cemetery plot cluster with Celtic cross, pointed lancet headstone, slanted ledger, obelisk, stone border, and iron chain posts."""
    clear_scene()
    palette = create_environment_voxel_palette()
    mat_stone = palette["weathered_stone"]
    mat_trim = palette["carved_stone_trim"]
    mat_iron = palette["wrought_iron"]

    bm = bmesh.new()
    sub_cnt = 0

    # 1. Embedded Plot Foundation Slab (Z = -0.65m to +0.06m)
    _add_bm_beveled_box(bm, (3.40, 2.60, 0.70), (0.0, 0.0, -0.29), bevel_width=0.02, mat_idx=0)
    sub_cnt += 1

    # Surrounding Stone Curb Border
    _add_bm_beveled_box(bm, (3.50, 0.20, 0.18), (0.0, -1.25, 0.12), bevel_width=0.010, mat_idx=1)
    _add_bm_beveled_box(bm, (3.50, 0.20, 0.18), (0.0, 1.25, 0.12), bevel_width=0.010, mat_idx=1)
    _add_bm_beveled_box(bm, (0.20, 2.40, 0.18), (-1.65, 0.0, 0.12), bevel_width=0.010, mat_idx=1)
    _add_bm_beveled_box(bm, (0.20, 2.40, 0.18), (1.65, 0.0, 0.12), bevel_width=0.010, mat_idx=1)
    sub_cnt += 4

    # 2. Monument A: Celtic Cross (at X = -0.95m, Y = 0.55m)
    _add_bm_beveled_box(bm, (0.64, 0.44, 0.26), (-0.95, 0.55, 0.16), bevel_width=0.012, mat_idx=0)
    _add_bm_beveled_box(bm, (0.50, 0.34, 0.22), (-0.95, 0.55, 0.38), bevel_width=0.010, mat_idx=0)
    _add_bm_beveled_box(bm, (0.22, 0.16, 1.40), (-0.95, 0.55, 1.12), bevel_width=0.008, mat_idx=1)
    _add_bm_beveled_box(bm, (0.85, 0.15, 0.20), (-0.95, 0.55, 1.38), bevel_width=0.008, mat_idx=1)
    # Celtic Ring
    for r_i in range(8):
        rang = r_i * (math.pi * 0.25)
        rx = -0.95 + math.cos(rang) * 0.30
        rz = 1.38 + math.sin(rang) * 0.30
        _add_bm_beveled_box(bm, (0.08, 0.14, 0.08), (rx, 0.55, rz), rot_euler=(0.0, -rang, 0.0), bevel_width=0.004, mat_idx=1)
        sub_cnt += 1
    sub_cnt += 4

    # 3. Monument B: Lancet Headstone (at X = 0.85m, Y = 0.50m)
    _add_bm_beveled_box(bm, (0.58, 0.36, 0.24), (0.85, 0.50, 0.15), bevel_width=0.010, mat_idx=0)
    _add_bm_beveled_box(bm, (0.44, 0.14, 0.95), (0.85, 0.50, 0.72), rot_euler=(0.04, -0.06, 0.08), bevel_width=0.008, mat_idx=0)
    _add_bm_beveled_box(bm, (0.32, 0.13, 0.28), (0.85, 0.50, 1.25), rot_euler=(0.0, math.pi * 0.25, 0.08), bevel_width=0.006, mat_idx=1)
    sub_cnt += 3

    # 4. Monument C: Slanted Ledger Grave Slab (at X = -0.80m, Y = -0.45m)
    _add_bm_beveled_box(bm, (1.25, 0.72, 0.22), (-0.80, -0.45, 0.14), rot_euler=(0.03, 0.06, -0.04), bevel_width=0.012, mat_idx=0)
    _add_bm_beveled_box(bm, (1.15, 0.62, 0.12), (-0.80, -0.45, 0.28), rot_euler=(0.03, 0.06, -0.04), bevel_width=0.008, mat_idx=1)
    sub_cnt += 2

    # 5. Monument D: Tapered Gothic Obelisk (at X = 0.90m, Y = -0.55m)
    _add_bm_beveled_box(bm, (0.52, 0.52, 0.24), (0.90, -0.55, 0.15), bevel_width=0.010, mat_idx=0)
    _add_bm_beveled_box(bm, (0.38, 0.38, 0.80), (0.90, -0.55, 0.65), bevel_width=0.008, mat_idx=0)
    _add_bm_beveled_box(bm, (0.26, 0.26, 0.32), (0.90, -0.55, 1.16), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.006, mat_idx=1)
    sub_cnt += 3

    # 6. 4 Iron Corner Plot Posts
    corner_pts = [(-1.55, -1.15), (1.55, -1.15), (-1.55, 1.15), (1.55, 1.15)]
    for cx, cy in corner_pts:
        _add_bm_beveled_box(bm, (0.08, 0.08, 0.44), (cx, cy, 0.30), bevel_width=0.005, mat_idx=2)
        _add_bm_beveled_box(bm, (0.11, 0.11, 0.08), (cx, cy, 0.54), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.004, mat_idx=2)
        sub_cnt += 2

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("TownGravestoneClusterMesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("TownGravestoneCluster", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat_stone)
    obj.data.materials.append(mat_trim)
    obj.data.materials.append(mat_iron)

    bake_gothic_vertex_colors(obj, z_min=-0.65, z_max=1.85)
    export_single_glb(os.path.join(out_dir, "town_gravestone_cluster.glb"), [obj])


# ==============================================================================
# ABANDONED HOUSES (House A & House B with 3.0m deep plinths)
# ==============================================================================


def build_abandoned_house_variant(
    out_dir: str,
    filename: str,
    width_x: float,
    depth_y: float,
    wall_height: float,
    roof_peak: float,
    sag_amount: float,
    has_side_annex: bool,
) -> None:
    """Builds a gothic abandoned town house with mandatory 3.0m deep foundation plinth, entrance steps, timber framing, sagging roof, and stone chimney."""
    clear_scene()
    palette = create_environment_voxel_palette()
    mat_plinth = palette["weathered_stone"]
    mat_plaster = palette["dirty_plaster"]
    mat_timber = palette["charred_timber"]
    mat_roof = palette["dark_slate_roof"]
    mat_iron = palette["wrought_iron"]
    mat_dark = palette["containment_hull"]

    bm = bmesh.new()
    sub_cnt = 0
    front_y = -depth_y * 0.5
    back_y = depth_y * 0.5
    half_w = width_x * 0.5

    # 1. Mandatory 3.0m Deep Stone Foundation Plinth (Z = -3.0m to 0.0m per Rule 9.2)
    _add_bm_beveled_box(bm, (width_x + 0.44, depth_y + 0.44, 3.0), (0.0, 0.0, -1.50), bevel_width=0.045, mat_idx=0)
    sub_cnt += 1

    # Plinth Corner Quoins (8 courses of stepped corner stones at all 4 corners)
    for q_i in range(8):
        qz = -0.20 - q_i * 0.35
        for sx in (-1, 1):
            for sy in (-1, 1):
                qx = sx * (half_w + 0.24)
                qy = sy * (depth_y * 0.5 + 0.24)
                qw = 0.48 if (q_i % 2 == 0) else 0.36
                qd = 0.36 if (q_i % 2 == 0) else 0.48
                _add_bm_beveled_box(bm, (qw, qd, 0.32), (qx, qy, qz), bevel_width=0.015, mat_idx=0)
                sub_cnt += 1

    # 2. Multi-Stone Sagging Porch Entrance Steps leading up to doorway
    for s_i in range(5):
        step_z = -0.50 + s_i * 0.10
        step_y = front_y - 0.20 - (4 - s_i) * 0.30
        step_w = 2.40 + (4 - s_i) * 0.15
        _add_bm_beveled_box(bm, (step_w, 0.34, 0.22), (0.0, step_y, step_z), bevel_width=0.015, mat_idx=0)
        sub_cnt += 1

    # 3. Main Plaster House Walls (Z = 0.0 to wall_height)
    wall_thick = 0.36
    # Left (-X) and Right (+X) solid walls
    _add_bm_beveled_box(bm, (wall_thick, depth_y, wall_height), (-half_w + wall_thick * 0.5, 0.0, wall_height * 0.5), bevel_width=0.02, mat_idx=1)
    _add_bm_beveled_box(bm, (wall_thick, depth_y, wall_height), (half_w - wall_thick * 0.5, 0.0, wall_height * 0.5), bevel_width=0.02, mat_idx=1)
    # Back (+Y) wall
    _add_bm_beveled_box(bm, (width_x - wall_thick * 2.0, wall_thick, wall_height), (0.0, back_y - wall_thick * 0.5, wall_height * 0.5), bevel_width=0.02, mat_idx=1)
    # Front (-Y) wall piers (left and right of central doorway)
    door_w = 1.45
    door_h = 2.35
    front_pier_w = (width_x - door_w) * 0.5
    _add_bm_beveled_box(bm, (front_pier_w, wall_thick, wall_height), (-half_w + front_pier_w * 0.5, front_y + wall_thick * 0.5, wall_height * 0.5), bevel_width=0.02, mat_idx=1)
    _add_bm_beveled_box(bm, (front_pier_w, wall_thick, wall_height), (half_w - front_pier_w * 0.5, front_y + wall_thick * 0.5, wall_height * 0.5), bevel_width=0.02, mat_idx=1)
    # Wall above doorway
    _add_bm_beveled_box(bm, (door_w, wall_thick, wall_height - door_h), (0.0, front_y + wall_thick * 0.5, door_h + (wall_height - door_h) * 0.5), bevel_width=0.02, mat_idx=1)
    # Recessed dark interior backing
    _add_bm_beveled_box(bm, (door_w - 0.1, 0.05, door_h - 0.1), (0.0, front_y + wall_thick + 0.1, door_h * 0.5), bevel_width=0.01, mat_idx=5)
    sub_cnt += 7

    # 4. Timber Framing (Corner posts, wall plates, diagonal cross-braces, lintels)
    beam_w = 0.18
    # 4 Vertical Corner Posts
    for sx in (-1, 1):
        for sy in (-1, 1):
            px = sx * (half_w - beam_w * 0.5)
            py = sy * (depth_y * 0.5 - beam_w * 0.5)
            _add_bm_beveled_box(bm, (beam_w, beam_w, wall_height + 0.08), (px, py, wall_height * 0.5), bevel_width=0.010, mat_idx=2)
            sub_cnt += 1

    # Horizontal Wall Plates (lower and upper rim beams)
    for hz in (0.12, wall_height - 0.08):
        _add_bm_beveled_box(bm, (width_x + 0.08, beam_w, beam_w), (0.0, front_y - beam_w * 0.2, hz), bevel_width=0.008, mat_idx=2)
        _add_bm_beveled_box(bm, (width_x + 0.08, beam_w, beam_w), (0.0, back_y + beam_w * 0.2, hz), bevel_width=0.008, mat_idx=2)
        _add_bm_beveled_box(bm, (beam_w, depth_y + 0.08, beam_w), (-half_w - beam_w * 0.2, 0.0, hz), bevel_width=0.008, mat_idx=2)
        _add_bm_beveled_box(bm, (beam_w, depth_y + 0.08, beam_w), (half_w + beam_w * 0.2, 0.0, hz), bevel_width=0.008, mat_idx=2)
        sub_cnt += 4

    # Heavy Doorway Frame (two timber posts and heavy oak lintel)
    _add_bm_beveled_box(bm, (beam_w, beam_w * 1.4, door_h), (-door_w * 0.5 - beam_w * 0.4, front_y, door_h * 0.5), bevel_width=0.010, mat_idx=2)
    _add_bm_beveled_box(bm, (beam_w, beam_w * 1.4, door_h), (door_w * 0.5 + beam_w * 0.4, front_y, door_h * 0.5), bevel_width=0.010, mat_idx=2)
    _add_bm_beveled_box(bm, (door_w + beam_w * 2.0, beam_w * 1.4, beam_w), (0.0, front_y, door_h + beam_w * 0.5), bevel_width=0.010, mat_idx=2)
    sub_cnt += 3

    # Wrought-Iron Strap Hinges on door
    _add_bm_beveled_box(bm, (0.55, 0.04, 0.08), (-door_w * 0.25, front_y - 0.03, 0.65), bevel_width=0.004, mat_idx=4)
    _add_bm_beveled_box(bm, (0.55, 0.04, 0.08), (-door_w * 0.25, front_y - 0.03, 1.75), bevel_width=0.004, mat_idx=4)
    sub_cnt += 2

    # Shuttered Windows with Boarded Planks (Front and Side facades)
    win_locs = [
        (-half_w * 0.58, front_y, 1.85, (0.0, 0.0, 0.0)),
        (half_w * 0.58, front_y, 1.85, (0.0, 0.0, 0.0)),
        (-half_w, -depth_y * 0.22, 1.85, (0.0, 0.0, math.pi * 0.5)),
        (-half_w, depth_y * 0.22, 1.85, (0.0, 0.0, math.pi * 0.5)),
    ]
    for wx, wy, wz, w_rot in win_locs:
        _add_bm_beveled_box(bm, (1.20, 0.16, 1.40), (wx, wy, wz), rot_euler=w_rot, bevel_width=0.010, mat_idx=2)
        _add_bm_beveled_box(bm, (0.95, 0.05, 1.15), (wx, wy, wz), rot_euler=w_rot, bevel_width=0.006, mat_idx=5)
        # Boarded diagonal wooden planks across window
        _add_bm_beveled_box(bm, (1.25, 0.04, 0.18), (wx, wy - 0.04, wz - 0.18), rot_euler=(w_rot[0], w_rot[1] + 0.22, w_rot[2]), bevel_width=0.005, mat_idx=2)
        _add_bm_beveled_box(bm, (1.25, 0.04, 0.18), (wx, wy - 0.04, wz + 0.18), rot_euler=(w_rot[0], w_rot[1] - 0.20, w_rot[2]), bevel_width=0.005, mat_idx=2)
        sub_cnt += 4

    # 5. Pitched Gothic Gable Roof with Subtle Vertex Sag
    roof_hw = half_w + 0.45
    roof_hd = depth_y * 0.5 + 0.50
    # Left and Right roof planes (pitched inward to ridge at X = 0.0)
    for side_x in (-1, 1):
        plane_cx = side_x * (roof_hw * 0.5)
        pitch_ang = math.atan2(roof_peak, roof_hw)
        rot_y = -side_x * pitch_ang
        slope_len = math.hypot(roof_hw, roof_peak)
        _add_bm_beveled_box(bm, (slope_len, roof_hd * 2.0, 0.14), (plane_cx, 0.0, wall_height + roof_peak * 0.5 - sag_amount * 0.4), rot_euler=(0.0, rot_y, 0.0), bevel_width=0.018, mat_idx=3)
        sub_cnt += 1

    # Ridge Cap Beam + Finial Spikes
    _add_bm_beveled_box(bm, (0.28, roof_hd * 2.04, 0.18), (0.0, 0.0, wall_height + roof_peak - sag_amount), bevel_width=0.010, mat_idx=3)
    sub_cnt += 1
    for f_sy in (-1, 1):
        _add_bm_beveled_box(bm, (0.12, 0.12, 0.45), (0.0, f_sy * roof_hd, wall_height + roof_peak + 0.20), bevel_width=0.006, mat_idx=4)
        sub_cnt += 1

    # Gable Wall Triangles (Front and Back)
    for sy in (-1, 1):
        gy = sy * (depth_y * 0.5)
        _add_bm_beveled_box(bm, (width_x - 0.1, wall_thick, roof_peak * 0.6), (0.0, gy, wall_height + roof_peak * 0.3), bevel_width=0.015, mat_idx=1)
        sub_cnt += 1

    # 6. Exposed Stone Chimney Stack (extending up from Z = -0.5m to above roof peak)
    chim_x = half_w - 0.45
    chim_y = depth_y * 0.25
    chim_h = wall_height + roof_peak + 1.10
    _add_bm_beveled_box(bm, (0.95, 0.95, chim_h), (chim_x, chim_y, chim_h * 0.5 - 0.5), bevel_width=0.025, mat_idx=0)
    _add_bm_beveled_box(bm, (1.08, 1.08, 0.16), (chim_x, chim_y, chim_h - 0.58), bevel_width=0.015, mat_idx=0)
    # Dual terracotta/stone chimney pots
    _add_bm_beveled_box(bm, (0.28, 0.28, 0.48), (chim_x - 0.22, chim_y, chim_h - 0.26), bevel_width=0.008, mat_idx=0)
    _add_bm_beveled_box(bm, (0.28, 0.28, 0.48), (chim_x + 0.22, chim_y, chim_h - 0.26), bevel_width=0.008, mat_idx=0)
    sub_cnt += 4

    # 7. Optional Side Annex for House B
    if has_side_annex:
        ann_w = 3.20
        ann_d = 4.80
        ann_h = 2.65
        ann_x = half_w + ann_w * 0.5
        ann_y = -depth_y * 0.05
        # 3.0m deep plinth for annex
        _add_bm_beveled_box(bm, (ann_w + 0.3, ann_d + 0.3, 3.0), (ann_x, ann_y, -1.50), bevel_width=0.04, mat_idx=0)
        # Annex walls
        _add_bm_beveled_box(bm, (ann_w, ann_d, ann_h), (ann_x, ann_y, ann_h * 0.5), bevel_width=0.02, mat_idx=1)
        # Lean-to pitched roof
        lean_len = math.hypot(ann_w + 0.4, 0.9)
        lean_pitch = math.atan2(0.9, ann_w + 0.4)
        _add_bm_beveled_box(bm, (lean_len, ann_d + 0.4, 0.12), (ann_x, ann_y, ann_h + 0.45), rot_euler=(0.0, lean_pitch, 0.0), bevel_width=0.015, mat_idx=3)
        # Annex door
        _add_bm_beveled_box(bm, (1.10, 0.12, 1.90), (ann_x, ann_y - ann_d * 0.5, 0.95), bevel_width=0.008, mat_idx=2)
        sub_cnt += 4

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(os.path.splitext(filename)[0] + "Mesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(os.path.splitext(filename)[0], mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat_plinth)
    obj.data.materials.append(mat_plaster)
    obj.data.materials.append(mat_timber)
    obj.data.materials.append(mat_roof)
    obj.data.materials.append(mat_iron)
    obj.data.materials.append(mat_dark)

    bake_gothic_vertex_colors(obj, z_min=-3.0, z_max=wall_height + roof_peak + 1.2)
    export_single_glb(os.path.join(out_dir, filename), [obj])


# ==============================================================================
# FOLIAGE ASSETS (Wild Grass & Dead Gnarled Tree in assets/models/)
# ==============================================================================


def build_grass_clump_wild(out_dir: str) -> None:
    """Wild windswept moor grass clump with 12 curved 3D grass blades and windswept tilt."""
    clear_scene()
    palette = create_environment_voxel_palette()
    mat_grass = palette["moor_grass"]

    bm = bmesh.new()
    blade_configs = [
        {"angle": 0.00, "rad": 0.05, "height": 0.58, "tilt": 0.28, "bend": 0.14, "w": 0.040},
        {"angle": 0.58, "rad": 0.08, "height": 0.65, "tilt": 0.35, "bend": 0.18, "w": 0.044},
        {"angle": 1.15, "rad": 0.06, "height": 0.50, "tilt": 0.25, "bend": 0.12, "w": 0.038},
        {"angle": 1.72, "rad": 0.10, "height": 0.56, "tilt": 0.38, "bend": 0.16, "w": 0.038},
        {"angle": 2.28, "rad": 0.07, "height": 0.64, "tilt": 0.30, "bend": 0.15, "w": 0.042},
        {"angle": 2.85, "rad": 0.09, "height": 0.54, "tilt": 0.34, "bend": 0.14, "w": 0.036},
        {"angle": 3.42, "rad": 0.05, "height": 0.68, "tilt": 0.26, "bend": 0.13, "w": 0.045},
        {"angle": 4.00, "rad": 0.10, "height": 0.48, "tilt": 0.42, "bend": 0.19, "w": 0.034},
        {"angle": 4.56, "rad": 0.07, "height": 0.58, "tilt": 0.32, "bend": 0.15, "w": 0.040},
        {"angle": 5.12, "rad": 0.09, "height": 0.62, "tilt": 0.36, "bend": 0.17, "w": 0.042},
        {"angle": 5.68, "rad": 0.06, "height": 0.52, "tilt": 0.28, "bend": 0.14, "w": 0.038},
        {"angle": 6.15, "rad": 0.08, "height": 0.60, "tilt": 0.33, "bend": 0.16, "w": 0.040},
    ]

    for cfg in blade_configs:
        ang = cfg["angle"]
        r = cfg["rad"]
        h = cfg["height"]
        tilt = cfg["tilt"]
        bend = cfg["bend"]
        base_w = cfg["w"]

        bx = r * math.cos(ang)
        by = r * math.sin(ang)
        dir_x = math.cos(ang)
        dir_y = math.sin(ang)
        perp_x = -dir_y
        perp_y = dir_x

        num_segments = 6
        prev_left = None
        prev_right = None

        for s in range(num_segments + 1):
            t = s / float(num_segments)
            cur_z = h * t
            cur_reach = tilt * (t * t) + bend * (t * t * t)
            cx = bx + dir_x * cur_reach
            cy = by + dir_y * cur_reach
            w = base_w * (1.0 - t * 0.90) * 0.5

            vl = bm.verts.new((cx - perp_x * w, cy - perp_y * w, cur_z))
            vr = bm.verts.new((cx + perp_x * w, cy + perp_y * w, cur_z))

            if prev_left is not None and prev_right is not None:
                face = bm.faces.new((prev_left, prev_right, vr, vl))
                face.material_index = 0
                face.smooth = True
            prev_left = vl
            prev_right = vr

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("GrassClumpMesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("GrassClumpWild", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat_grass)

    bake_gothic_vertex_colors(obj, z_min=0.0, z_max=0.7)
    export_single_glb(os.path.join(out_dir, "grass_clump_wild.glb"), [obj])


def build_dead_tree_gnarled(out_dir: str) -> None:
    """5.5m tall gnarled twisting dead tree with buttress roots and 3 main claw branching limbs."""
    clear_scene()
    palette = create_environment_voxel_palette()
    mat_bark = palette["charred_timber"]

    bm = bmesh.new()

    # 1. Main Gnarled Trunk (Z = 0.0m to 5.5m)
    trunk_pts = [
        (0.0, 0.0, 0.0),
        (0.04, 0.02, 0.6),
        (-0.06, 0.08, 1.4),
        (-0.12, 0.05, 2.2),
        (0.02, -0.04, 3.1),
        (0.14, -0.09, 3.9),
        (0.22, -0.15, 4.7),
        (0.28, -0.21, 5.5),
    ]
    trunk_radii = [0.46, 0.38, 0.32, 0.26, 0.20, 0.15, 0.10, 0.04]
    add_branch_mesh(bm, trunk_pts, trunk_radii, sides=10, mat_idx=0)

    # 4 Buttress Roots anchoring into the soil
    root_configs = [
        [(0.25, 0.0, 0.4), (0.55, 0.05, 0.15), (0.85, 0.08, -0.25)],
        [(-0.22, 0.15, 0.4), (-0.52, 0.35, 0.15), (-0.78, 0.52, -0.25)],
        [(0.05, 0.25, 0.4), (0.12, 0.58, 0.15), (0.18, 0.88, -0.25)],
        [(-0.10, -0.24, 0.4), (-0.25, -0.55, 0.15), (-0.38, -0.85, -0.25)],
    ]
    for r_pts in root_configs:
        add_branch_mesh(bm, r_pts, [0.18, 0.12, 0.04], sides=6, mat_idx=0)

    # 2. Main Branch 1 (splitting North-West at Z = 2.2m up to Z = 4.8m)
    b1_pts = [
        (-0.12, 0.05, 2.2),
        (-0.35, 0.28, 2.8),
        (-0.68, 0.52, 3.4),
        (-1.08, 0.74, 4.0),
        (-1.42, 0.88, 4.5),
        (-1.75, 0.96, 4.8),
    ]
    add_branch_mesh(bm, b1_pts, [0.19, 0.16, 0.13, 0.09, 0.06, 0.03], sides=8, mat_idx=0)

    # Sub-branch 1A (claws downward)
    b1a_pts = [
        (-0.68, 0.52, 3.4),
        (-0.95, 0.42, 3.2),
        (-1.24, 0.34, 3.0),
        (-1.48, 0.28, 2.75),
    ]
    add_branch_mesh(bm, b1a_pts, [0.08, 0.06, 0.04, 0.02], sides=6, mat_idx=0)

    # 3. Main Branch 2 (splitting North-East at Z = 2.8m up to Z = 5.2m)
    b2_pts = [
        (-0.02, 0.02, 2.8),
        (0.35, 0.26, 3.4),
        (0.72, 0.55, 4.0),
        (1.15, 0.78, 4.6),
        (1.52, 0.94, 5.0),
        (1.85, 1.05, 5.2),
    ]
    add_branch_mesh(bm, b2_pts, [0.20, 0.17, 0.13, 0.09, 0.06, 0.03], sides=8, mat_idx=0)

    # Sub-branch 2A (twisting upward)
    b2a_pts = [
        (0.72, 0.55, 4.0),
        (0.92, 0.45, 4.4),
        (1.12, 0.38, 4.8),
        (1.28, 0.32, 5.15),
    ]
    add_branch_mesh(bm, b2a_pts, [0.07, 0.05, 0.035, 0.02], sides=6, mat_idx=0)

    # 4. Main Branch 3 (arching South at Z = 3.3m up to Z = 4.7m)
    b3_pts = [
        (0.06, -0.06, 3.3),
        (0.12, -0.42, 3.8),
        (0.18, -0.85, 4.2),
        (0.25, -1.25, 4.5),
        (0.30, -1.55, 4.7),
    ]
    add_branch_mesh(bm, b3_pts, [0.17, 0.14, 0.10, 0.06, 0.03], sides=8, mat_idx=0)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("DeadTreeMesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("DeadTreeGnarled", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat_bark)

    bake_gothic_vertex_colors(obj, z_min=-0.25, z_max=5.5)
    export_single_glb(os.path.join(out_dir, "dead_tree_gnarled.glb"), [obj])


# ==============================================================================
# LOOT DROPS & INTERACTIVE RELIQUARY CHEST (4 Models in assets/models/items/)
# ==============================================================================


def build_loot_blood_echo_cluster(out_dir: str) -> None:
    """Faceted crimson blood-crystal shard cluster encircled by two orbiting tarnished-brass astrolabe gimbal rings."""
    clear_scene()
    palette = create_environment_voxel_palette()
    mat_crimson = palette["crimson"]
    mat_bronze = palette["bronze"]
    mat_iron = palette["wrought_iron"]

    bm = bmesh.new()
    center_z = 0.38
    sub_parts = 0

    # 1. Central crimson core + 20 radiating faceted crystal shards
    _add_bm_beveled_box(bm, (0.14, 0.14, 0.36), (0.0, 0.0, center_z), rot_euler=(0.12, -0.08, 0.45), bevel_width=0.018, mat_idx=0)
    sub_parts += 1

    for i in range(20):
        ang = (i / 20.0) * math.tau
        tier = i % 3
        tilt = 0.38 + tier * 0.26
        rad = 0.05 + tier * 0.025
        c_len = 0.24 - tier * 0.035
        c_thick = 0.055 - tier * 0.008
        cx = math.cos(ang) * rad
        cy = math.sin(ang) * rad
        cz = center_z + (0.04 if tier == 0 else (-0.03 if tier == 1 else 0.0))
        rx = math.sin(ang) * tilt
        ry = -math.cos(ang) * tilt
        _add_bm_beveled_box(bm, (c_thick, c_thick, c_len), (cx, cy, cz), rot_euler=(rx, ry, ang), bevel_width=0.010, mat_idx=0)
        sub_parts += 1

    # 2. Two orbiting tarnished-brass astrolabe gimbal rings with degree studs
    for ring_idx, ring_tilt in enumerate(((0.55, 0.25, 0.0), (-0.48, 0.35, 0.78))):
        ring_r = 0.24 + ring_idx * 0.035
        ring_rot = Euler(ring_tilt, 'XYZ')
        segs = 18
        for s_i in range(segs):
            a0 = (s_i / float(segs)) * math.tau
            seg_len = (math.tau * ring_r) / segs * 1.06
            local_pt = Vector((math.cos(a0) * ring_r, math.sin(a0) * ring_r, 0.0))
            local_pt.rotate(ring_rot)
            world_pt = (local_pt.x, local_pt.y, center_z + local_pt.z)
            seg_eul = Euler((ring_tilt[0], ring_tilt[1], a0 + math.pi * 0.5), 'XYZ')
            _add_bm_beveled_box(bm, (0.024, seg_len, 0.016), world_pt, rot_euler=(seg_eul.x, seg_eul.y, seg_eul.z), bevel_width=0.003, mat_idx=1)
            sub_parts += 1
            if s_i % 3 == 0:
                stud_pt = Vector((math.cos(a0) * (ring_r + 0.016), math.sin(a0) * (ring_r + 0.016), 0.0))
                stud_pt.rotate(ring_rot)
                _add_bm_beveled_box(bm, (0.022, 0.022, 0.022), (stud_pt.x, stud_pt.y, center_z + stud_pt.z), rot_euler=ring_tilt, bevel_width=0.004, mat_idx=2)
                sub_parts += 1

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("LootBloodEchoClusterMesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("LootBloodEchoCluster", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat_crimson)
    obj.data.materials.append(mat_bronze)
    obj.data.materials.append(mat_iron)

    bake_gothic_vertex_colors(obj, z_min=0.0, z_max=0.8)
    export_single_glb(os.path.join(out_dir, "loot_blood_echo_cluster.glb"), [obj])


def build_loot_occult_relic_talisman(out_dir: str) -> None:
    """Ornate gothic reliquary medallion with wrought-iron frame, 16 sunburst spikes, bone skull relief, glowing arcane rune center, and 3 chain tassels."""
    clear_scene()
    palette = create_environment_voxel_palette()
    mat_iron = palette["wrought_iron"]
    mat_bronze = palette["bronze"]
    mat_bone = palette["bone"]
    mat_rune = palette["occult_rune"]

    bm = bmesh.new()
    center_z = 0.42
    sub_parts = 0

    # 1. Wrought-iron octagonal medallion backing & 4 gothic cross arms
    _add_bm_beveled_box(bm, (0.26, 0.04, 0.26), (0.0, 0.0, center_z), bevel_width=0.008, mat_idx=0)
    _add_bm_beveled_box(bm, (0.26, 0.038, 0.26), (0.0, 0.0, center_z), rot_euler=(0.0, math.radians(45.0), 0.0), bevel_width=0.008, mat_idx=0)
    _add_bm_beveled_box(bm, (0.44, 0.045, 0.085), (0.0, 0.0, center_z), bevel_width=0.006, mat_idx=0)
    _add_bm_beveled_box(bm, (0.085, 0.045, 0.46), (0.0, 0.0, center_z), bevel_width=0.006, mat_idx=0)
    sub_parts += 4

    # 2. 16 Tarnished-bronze sunburst spikes & perimeter rivets
    for i in range(16):
        ang = (i / 16.0) * math.tau
        r_spike = 0.19 if (i % 2 == 0) else 0.155
        sx = math.cos(ang) * r_spike
        sz = center_z + math.sin(ang) * r_spike
        _add_bm_beveled_box(bm, (0.026, 0.024, 0.095 if (i % 2 == 0) else 0.065), (sx, 0.0, sz), rot_euler=(0.0, ang - math.pi * 0.5, 0.0), bevel_width=0.004, mat_idx=1)
        rx = math.cos(ang) * 0.115
        rz = center_z + math.sin(ang) * 0.115
        _add_bm_beveled_box(bm, (0.018, 0.052, 0.018), (rx, 0.0, rz), bevel_width=0.003, mat_idx=1)
        sub_parts += 2

    # 3. Miniature Skull Relief on both front and back faces
    for side_y in (-0.028, 0.028):
        _add_bm_beveled_box(bm, (0.09, 0.032, 0.085), (0.0, side_y, center_z + 0.075), bevel_width=0.010, mat_idx=2)
        _add_bm_beveled_box(bm, (0.065, 0.028, 0.045), (0.0, side_y, center_z + 0.022), bevel_width=0.006, mat_idx=2)
        for tooth_i in range(-2, 3):
            _add_bm_beveled_box(bm, (0.010, 0.034, 0.018), (tooth_i * 0.012, side_y, center_z + 0.005), bevel_width=0.002, mat_idx=2)
        sub_parts += 7

    # 4. Glowing Arcane Gemstone Center + 4 rune shards
    _add_bm_beveled_box(bm, (0.095, 0.062, 0.095), (0.0, 0.0, center_z - 0.045), rot_euler=(0.0, math.radians(45.0), 0.0), bevel_width=0.012, mat_idx=3)
    for arm_x, arm_z in ((-0.16, 0.0), (0.16, 0.0), (0.0, 0.17), (0.0, -0.17)):
        _add_bm_beveled_box(bm, (0.036, 0.054, 0.036), (arm_x, 0.0, center_z + arm_z), rot_euler=(0.0, math.radians(45.0), 0.0), bevel_width=0.005, mat_idx=3)
    sub_parts += 5

    # 5. 3 Hanging Chain Tassels at bottom (15 links total)
    for tx in (-0.09, 0.0, 0.09):
        for l_i in range(5):
            lz = center_z - 0.21 - l_i * 0.032
            rot_y = math.radians(90.0) if (l_i % 2 == 1) else 0.0
            _add_bm_beveled_box(bm, (0.024, 0.014, 0.036), (tx, 0.0, lz), rot_euler=(0.0, 0.0, rot_y), bevel_width=0.003, mat_idx=0)
            sub_parts += 1

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("LootOccultRelicTalismanMesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("LootOccultRelicTalisman", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat_iron)
    obj.data.materials.append(mat_bronze)
    obj.data.materials.append(mat_bone)
    obj.data.materials.append(mat_rune)

    bake_gothic_vertex_colors(obj, z_min=0.0, z_max=0.75)
    export_single_glb(os.path.join(out_dir, "loot_occult_relic_talisman.glb"), [obj])


def build_loot_alchemical_elixir(out_dir: str) -> None:
    """Ribbed alchemical glass flask strapped in leather and brass cages with stepped micro-voxel assembly."""
    clear_scene()
    palette = create_environment_voxel_palette()
    mat_glow = palette["green_bile"]
    mat_glass = palette["lead_glass"]
    mat_bronze = palette["bronze"]
    mat_leather = palette["charred_timber"]

    bm = bmesh.new()
    sub_parts = 0

    # 1. Base Stand: Stepped concentric bronze plinth tiers
    _add_bm_beveled_box(bm, (0.18, 0.18, 0.03), (0.0, 0.0, 0.015), bevel_width=0.002, mat_idx=2)
    _add_bm_beveled_box(bm, (0.18, 0.18, 0.03), (0.0, 0.0, 0.015), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.002, mat_idx=2)
    _add_bm_beveled_box(bm, (0.15, 0.15, 0.03), (0.0, 0.0, 0.045), bevel_width=0.002, mat_idx=2)
    sub_parts += 3

    # 2. Glowing Golden-Green Core: Stepped micro-voxel liquid layers (mat_idx=0)
    core_tiers = [
        (0.12, 0.04, 0.08),
        (0.15, 0.05, 0.125),
        (0.17, 0.05, 0.175),
        (0.17, 0.05, 0.225),
        (0.15, 0.05, 0.275),
        (0.11, 0.04, 0.32),
    ]
    for w, h, z in core_tiers:
        _add_bm_beveled_box(bm, (w, w, h), (0.0, 0.0, z), bevel_width=0.002, mat_idx=0)
        _add_bm_beveled_box(bm, (w, w, h), (0.0, 0.0, z), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.002, mat_idx=0)
        sub_parts += 2

    # 3. Flask Belly & Shoulder: Stepped concentric glass tiers (mat_idx=1)
    glass_tiers = [
        (0.16, 0.04, 0.08),
        (0.19, 0.05, 0.125),
        (0.22, 0.05, 0.175),
        (0.22, 0.05, 0.225),
        (0.19, 0.05, 0.275),
        (0.15, 0.04, 0.32),
        (0.12, 0.03, 0.355),
    ]
    for w, h, z in glass_tiers:
        _add_bm_beveled_box(bm, (w, w, h), (0.0, 0.0, z), bevel_width=0.002, mat_idx=1)
        _add_bm_beveled_box(bm, (w, w, h), (0.0, 0.0, z), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.002, mat_idx=1)
        sub_parts += 2

    # 4. Neck Collar & Flared Lip (mat_idx=1 glass)
    _add_bm_beveled_box(bm, (0.09, 0.09, 0.06), (0.0, 0.0, 0.40), bevel_width=0.002, mat_idx=1)
    _add_bm_beveled_box(bm, (0.09, 0.09, 0.06), (0.0, 0.0, 0.40), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.002, mat_idx=1)
    _add_bm_beveled_box(bm, (0.12, 0.12, 0.03), (0.0, 0.0, 0.445), bevel_width=0.002, mat_idx=1)
    _add_bm_beveled_box(bm, (0.12, 0.12, 0.03), (0.0, 0.0, 0.445), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.002, mat_idx=1)
    sub_parts += 4

    # 5. Bronze Cage Ribs & Clasp Rings (mat_idx=2)
    for sx in (-0.115, 0.115):
        for sy in (-0.115, 0.115):
            _add_bm_beveled_box(bm, (0.022, 0.022, 0.26), (sx, sy, 0.20), bevel_width=0.002, mat_idx=2)
            _add_bm_beveled_box(bm, (0.026, 0.026, 0.02), (sx * 1.05, sy * 1.05, 0.10), bevel_width=0.002, mat_idx=2)
            _add_bm_beveled_box(bm, (0.026, 0.026, 0.02), (sx * 1.05, sy * 1.05, 0.28), bevel_width=0.002, mat_idx=2)
            sub_parts += 3

    for rz, rw in ((0.10, 0.23), (0.20, 0.24), (0.30, 0.20)):
        _add_bm_beveled_box(bm, (rw, rw, 0.02), (0.0, 0.0, rz), bevel_width=0.002, mat_idx=2)
        _add_bm_beveled_box(bm, (rw, rw, 0.02), (0.0, 0.0, rz), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.002, mat_idx=2)
        sub_parts += 2

    _add_bm_beveled_box(bm, (0.11, 0.11, 0.025), (0.0, 0.0, 0.38), bevel_width=0.002, mat_idx=2)
    _add_bm_beveled_box(bm, (0.11, 0.11, 0.025), (0.0, 0.0, 0.38), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.002, mat_idx=2)
    sub_parts += 2

    # 6. Leather Straps & Cork Stopper (mat_idx=3)
    _add_bm_beveled_box(bm, (0.25, 0.05, 0.03), (0.0, 0.0, 0.22), bevel_width=0.002, mat_idx=3)
    _add_bm_beveled_box(bm, (0.05, 0.25, 0.03), (0.0, 0.0, 0.22), bevel_width=0.002, mat_idx=3)
    _add_bm_beveled_box(bm, (0.075, 0.075, 0.04), (0.0, 0.0, 0.465), bevel_width=0.002, mat_idx=3)
    _add_bm_beveled_box(bm, (0.085, 0.085, 0.03), (0.0, 0.0, 0.495), bevel_width=0.002, mat_idx=3)
    sub_parts += 4

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("LootAlchemicalElixirMesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("LootAlchemicalElixir", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat_glow)
    obj.data.materials.append(mat_glass)
    obj.data.materials.append(mat_bronze)
    obj.data.materials.append(mat_leather)

    bake_gothic_vertex_colors(obj, z_min=0.0, z_max=0.55)
    export_single_glb(os.path.join(out_dir, "loot_alchemical_elixir.glb"), [obj])


def build_prop_gothic_reliquary_chest(out_dir: str) -> None:
    """Interactive reliquary chest preserving parent ChestBase and child ChestLid pivoted at Y=+0.41, Z=0.58."""
    clear_scene()
    palette = create_environment_voxel_palette()
    mat_timber = palette["charred_timber"]
    mat_iron = palette["wrought_iron"]
    mat_bronze = palette["bronze"]
    mat_bone = palette["bone"]
    mat_crimson = palette["crimson"]

    # ------------------------------------------------------------------
    # PART A: ChestBase (Parent object at 0.0, 0.0, 0.0)
    # ------------------------------------------------------------------
    bm_base = bmesh.new()
    base_parts = 0

    # 1. 4 Stepped Iron Lion-Paw Corner Feet
    for sx in (-0.62, 0.62):
        for sy in (-0.36, 0.36):
            _add_bm_beveled_box(bm_base, (0.20, 0.20, 0.08), (sx, sy, 0.04), bevel_width=0.010, mat_idx=1)
            base_parts += 1

    # 2. Oak Planks forming the chest body & floor
    _add_bm_beveled_box(bm_base, (1.32, 0.80, 0.06), (0.0, 0.0, 0.10), bevel_width=0.008, mat_idx=0)
    base_parts += 1

    for sy in (-0.39, 0.39):
        for r_i in range(4):
            pz = 0.17 + r_i * 0.115
            _add_bm_beveled_box(bm_base, (1.34, 0.06, 0.108), (0.0, sy, pz), bevel_width=0.007, mat_idx=0)
            base_parts += 1

    for sx in (-0.64, 0.64):
        for r_i in range(4):
            pz = 0.17 + r_i * 0.115
            _add_bm_beveled_box(bm_base, (0.06, 0.78, 0.108), (sx, 0.0, pz), bevel_width=0.007, mat_idx=0)
            base_parts += 1

    # 3. Wrought-Iron Corner Posts, 4 Vertical Strap Bands & Rivets
    for sx in (-0.67, 0.67):
        for sy in (-0.41, 0.41):
            _add_bm_beveled_box(bm_base, (0.08, 0.08, 0.52), (sx, sy, 0.33), bevel_width=0.008, mat_idx=1)
            base_parts += 1

    strap_xs = (-0.42, -0.14, 0.14, 0.42)
    for bx in strap_xs:
        for sy in (-0.425, 0.425):
            _add_bm_beveled_box(bm_base, (0.065, 0.025, 0.50), (bx, sy, 0.33), bevel_width=0.004, mat_idx=1)
            base_parts += 1
            for rz in (0.16, 0.32, 0.48):
                _add_bm_beveled_box(bm_base, (0.024, 0.036, 0.024), (bx, sy, rz), bevel_width=0.003, mat_idx=2)
                base_parts += 1

    for sx in (-0.69, 0.69):
        _add_bm_beveled_box(bm_base, (0.03, 0.24, 0.08), (sx, 0.0, 0.36), bevel_width=0.005, mat_idx=1)
        _add_bm_beveled_box(bm_base, (0.05, 0.18, 0.03), (sx * 1.03, 0.0, 0.31), bevel_width=0.004, mat_idx=2)
        base_parts += 2

    # 4. Skull Padlock Escutcheon with Glowing Ruby Eyes & Velvet Bed
    _add_bm_beveled_box(bm_base, (0.20, 0.04, 0.24), (0.0, -0.435, 0.44), bevel_width=0.008, mat_idx=2)
    _add_bm_beveled_box(bm_base, (0.11, 0.05, 0.12), (0.0, -0.455, 0.46), bevel_width=0.012, mat_idx=3)
    _add_bm_beveled_box(bm_base, (0.075, 0.045, 0.06), (0.0, -0.455, 0.39), bevel_width=0.006, mat_idx=3)
    _add_bm_beveled_box(bm_base, (0.024, 0.055, 0.024), (-0.026, -0.465, 0.465), bevel_width=0.003, mat_idx=4)
    _add_bm_beveled_box(bm_base, (0.024, 0.055, 0.024), (0.026, -0.465, 0.465), bevel_width=0.003, mat_idx=4)
    _add_bm_beveled_box(bm_base, (1.20, 0.68, 0.08), (0.0, 0.0, 0.24), bevel_width=0.012, mat_idx=4)
    base_parts += 6

    bmesh.ops.recalc_face_normals(bm_base, faces=bm_base.faces)
    mesh_base = bpy.data.meshes.new("ChestBaseMesh")
    bm_base.to_mesh(mesh_base)
    bm_base.free()

    obj_base = bpy.data.objects.new("ChestBase", mesh_base)
    bpy.context.collection.objects.link(obj_base)
    obj_base.data.materials.append(mat_timber)
    obj_base.data.materials.append(mat_iron)
    obj_base.data.materials.append(mat_bronze)
    obj_base.data.materials.append(mat_bone)
    obj_base.data.materials.append(mat_crimson)
    bake_gothic_vertex_colors(obj_base, z_min=0.0, z_max=0.95)

    # ------------------------------------------------------------------
    # PART B: ChestLid (Child object pivoted at back hinge: Y = +0.41, Z = 0.58)
    # ------------------------------------------------------------------
    hinge_y = 0.41
    hinge_z = 0.58

    bm_lid = bmesh.new()
    lid_parts = 0
    num_staves = 7

    for s_i in range(num_staves):
        t = (s_i / float(num_staves - 1)) * math.pi
        world_y = math.cos(t) * 0.40
        world_z = hinge_z + math.sin(t) * 0.32 + 0.04
        local_y = world_y - hinge_y
        local_z = world_z - hinge_z
        pitch = -(t - math.pi * 0.5)
        _add_bm_beveled_box(bm_lid, (1.36, 0.14, 0.055), (0.0, local_y, local_z), rot_euler=(pitch, 0.0, 0.0), bevel_width=0.007, mat_idx=0)
        lid_parts += 1

    for sx in (-0.65, 0.65):
        _add_bm_beveled_box(bm_lid, (0.06, 0.78, 0.24), (sx, -hinge_y, 0.12), bevel_width=0.008, mat_idx=0)
        _add_bm_beveled_box(bm_lid, (0.08, 0.56, 0.16), (sx, -hinge_y, 0.26), bevel_width=0.008, mat_idx=1)
        lid_parts += 2

    for bx in strap_xs:
        for s_i in range(num_staves):
            t = (s_i / float(num_staves - 1)) * math.pi
            world_y = math.cos(t) * 0.418
            world_z = hinge_z + math.sin(t) * 0.335 + 0.045
            local_y = world_y - hinge_y
            local_z = world_z - hinge_z
            pitch = -(t - math.pi * 0.5)
            _add_bm_beveled_box(bm_lid, (0.07, 0.145, 0.026), (bx, local_y, local_z), rot_euler=(pitch, 0.0, 0.0), bevel_width=0.004, mat_idx=1)
            _add_bm_beveled_box(bm_lid, (0.024, 0.024, 0.036), (bx, local_y, local_z + 0.01), rot_euler=(pitch, 0.0, 0.0), bevel_width=0.003, mat_idx=2)
            lid_parts += 2

    bmesh.ops.recalc_face_normals(bm_lid, faces=bm_lid.faces)
    mesh_lid = bpy.data.meshes.new("ChestLidMesh")
    bm_lid.to_mesh(mesh_lid)
    bm_lid.free()

    obj_lid = bpy.data.objects.new("ChestLid", mesh_lid)
    bpy.context.collection.objects.link(obj_lid)
    obj_lid.parent = obj_base
    obj_lid.location = (0.0, hinge_y, hinge_z)
    obj_lid.data.materials.append(mat_timber)
    obj_lid.data.materials.append(mat_iron)
    obj_lid.data.materials.append(mat_bronze)
    bake_gothic_vertex_colors(obj_lid, z_min=-0.1, z_max=0.45)

    # Export both objects with apply_transforms=False to preserve parent-child hierarchy & pivot
    export_single_glb(os.path.join(out_dir, "prop_gothic_reliquary_chest.glb"), [obj_base, obj_lid], apply_transforms=False)


# ==============================================================================
# STEPPED MICRO-VOXEL TERRAIN (terrain_town.glb in assets/models/)
# ==============================================================================


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    if edge1 == edge0:
        return 0.0
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def compute_terrain_height(gx: float, gz: float) -> tuple[float, float]:
    """Computes base terrain elevation in Godot coordinates (gx, gz) with flattened pads for House A, House B, and Church plateau."""
    hills = (
        1.45 * math.sin(gx * 0.05) * math.cos(gz * 0.045)
        + 0.95 * math.cos((gx + 15.0) * 0.08) * math.sin((gz - 8.0) * 0.075)
        + 0.25 * math.sin(gx * 0.14 + gz * 0.13)
    )
    edge_ridge = 0.0030 * (gx * gx)
    north_slope = smoothstep(20.0, -22.0, gz) * 3.4 + smoothstep(-20.0, -38.0, gz) * 1.6
    base_h = max(0.0, 0.55 + hills * 0.60 + edge_ridge + north_slope)

    # 1. Valley Road mask: gz from +38 down to -10.5m
    road_z_factor = smoothstep(48.0, 34.0, gz) * smoothstep(-14.5, -9.0, gz)
    road_x_dist = abs(gx - 1.2 * math.sin(gz * 0.09))
    road_mask = (1.0 - smoothstep(4.5, 11.5, road_x_dist)) * road_z_factor
    road_progress = smoothstep(26.0, -10.2, gz)
    road_h = 0.15 + road_progress * (3.20 - 0.15)

    # 2. House A footprint pad (gx = -16.0, gz = +14.0, target Y = 0.85m)
    dist_ha = math.hypot((gx - (-16.0)) / 1.1, (gz - 14.0) / 1.2)
    mask_ha = 1.0 - smoothstep(5.5, 11.5, dist_ha)
    h_ha = 0.85

    # 3. House B footprint pad (gx = +16.0, gz = +8.0, target Y = 1.15m)
    dist_hb = math.hypot((gx - 16.0) / 1.1, (gz - 8.0) / 1.2)
    mask_hb = 1.0 - smoothstep(5.5, 11.5, dist_hb)
    h_hb = 1.15

    # 4. Church Hilltop Plateau (Cathedral at Y = 3.55m, Front plaza at Y = 3.20m)
    box_dx = max(0.0, abs(gx) - 15.0)
    if gz > -22.0:
        box_dz = max(0.0, gz - (-9.0))
    else:
        box_dz = max(0.0, (-59.0) - gz)
    dist_church = math.hypot(box_dx, box_dz)
    mask_church = 1.0 - smoothstep(0.5, 10.5, dist_church)
    church_ramp = smoothstep(-9.5, -12.2, gz)
    h_church = 3.20 + church_ramp * (3.55 - 3.20)

    # Blend elevations cleanly
    h = base_h
    h = h * (1.0 - road_mask) + road_h * road_mask
    h = h * (1.0 - mask_ha) + h_ha * mask_ha
    h = h * (1.0 - mask_hb) + h_hb * mask_hb
    h = h * (1.0 - mask_church) + h_church * mask_church

    pad_weight = max(mask_ha, mask_hb, mask_church)
    return (h, pad_weight)


def build_terrain_town(out_dir: str) -> None:
    """120m x 120m stepped micro-voxel terrain with 0.18m terracing, flattened building footprints, subterranean roof clearance, and stairwell cutout."""
    clear_scene()
    palette = create_environment_voxel_palette()
    mat_grass = palette["moor_grass"]
    mat_path = palette["mud_path"]
    mat_cliff = palette["cliff_stone"]

    # 1. Create 120m x 120m high-density grid (160 x 160 subdivisions = 0.75m spacing)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=160, y_segments=160, size=60.0)

    mesh = bpy.data.meshes.new("TerrainTownMesh")
    bm.to_mesh(mesh)
    bm.free()

    terrain_obj = bpy.data.objects.new("TerrainTown", mesh)
    bpy.context.collection.objects.link(terrain_obj)

    terrain_obj.data.materials.append(mat_grass)
    terrain_obj.data.materials.append(mat_path)
    terrain_obj.data.materials.append(mat_cliff)

    # 2. Compute elevations with 0.18m stepped micro-voxel terracing
    step_riser = 0.18  # <= 0.20m to satisfy Godot player max_step_height = 0.36
    for v in mesh.vertices:
        gx = v.co.x
        gz = -v.co.y
        hy, pad_w = compute_terrain_height(gx, gz)
        hy_stepped = round(hy / step_riser) * step_riser
        final_h = hy_stepped * (1.0 - pad_w) + hy * pad_w
        v.co.z = final_h

    mesh.update()

    # Assign materials based on road/plaza proximity and slope
    for poly in mesh.polygons:
        cx = poly.center.x
        cz = -poly.center.y
        road_x_dist = abs(cx - 1.2 * math.sin(cz * 0.09))
        is_road = (road_x_dist < 3.6 and -11.5 <= cz <= 36.0)
        is_plaza = (abs(cx) < 8.5 and -34.0 <= cz <= -9.5)
        if is_road or is_plaza:
            poly.material_index = 1  # mud_path
        elif poly.normal.z < 0.86 or poly.center.z > 4.2:
            poly.material_index = 2  # cliff_stone
        else:
            poly.material_index = 0  # moor_grass

    # 3. Subterranean Roof Clearance: outside church nave, ensure terrain is >= 4.35m
    for v in terrain_obj.data.vertices:
        gx = v.co.x
        gz = -v.co.y
        if -30.0 <= gx <= 30.0 and gz <= -47.5:
            in_church_nave = (-13.8 <= gx <= 13.8 and gz >= -57.8)
            if not in_church_nave:
                z_blend = smoothstep(-47.5, -49.5, gz)
                min_roof_cover = 3.55 + z_blend * (4.35 - 3.55)
                if v.co.z < min_roof_cover:
                    v.co.z = min_roof_cover
    terrain_obj.data.update()

    # 4. Deterministic BMesh Stairwell Cutout: Size 27.6m (X) x 35.8m (Y) at gx = 0.0, gy = 39.9 (Godot gz = -39.9)
    # Deletes all faces in range X in [-13.8, 13.8], Y in [22.0, 57.8]
    bm_cut = bmesh.new()
    bm_cut.from_mesh(terrain_obj.data)
    faces_to_delete = [
        f for f in bm_cut.faces
        if -13.8 <= f.calc_center_median().x <= 13.8 and 22.0 <= f.calc_center_median().y <= 57.8
    ]
    bmesh.ops.delete(bm_cut, geom=faces_to_delete, context='FACES')
    verts_to_delete = [v for v in bm_cut.verts if len(v.link_faces) == 0]
    bmesh.ops.delete(bm_cut, geom=verts_to_delete, context='VERTS')
    bm_cut.to_mesh(terrain_obj.data)
    bm_cut.free()
    terrain_obj.data.update()

    # 5. Triangulate & bake cavity/slope vertex colors into 'Col'
    bpy.context.view_layer.objects.active = terrain_obj
    terrain_obj.select_set(True)
    tri_mod = terrain_obj.modifiers.new(name="Triangulate", type='TRIANGULATE')
    bpy.ops.object.modifier_apply(modifier=tri_mod.name)

    for poly in terrain_obj.data.polygons:
        poly.use_smooth = True

    t_mesh = terrain_obj.data
    if "Col" in t_mesh.color_attributes:
        col_attr = t_mesh.color_attributes["Col"]
    else:
        col_attr = t_mesh.color_attributes.new(name="Col", type='BYTE_COLOR', domain='CORNER')

    for poly in t_mesh.polygons:
        slope_shade = max(0.65, min(1.00, 0.72 + 0.28 * max(0.0, poly.normal.z)))
        for loop_idx in poly.loop_indices:
            col_attr.data[loop_idx].color = (slope_shade, slope_shade, slope_shade, 1.0)

    export_single_glb(os.path.join(out_dir, "terrain_town.glb"), [terrain_obj])


# ==============================================================================
# MAIN PIPELINE ENTRYPOINT
# ==============================================================================


def main() -> None:
    print("=" * 70)
    print("STARTING BLENDER VOXEL TOWN AND LOOT BUILD (Wave 1D - 13 GLBs)")
    print("=" * 70)

    os.makedirs(CHURCH_KIT_DIR, exist_ok=True)
    os.makedirs(ROOT_MODELS_DIR, exist_ok=True)
    os.makedirs(ITEMS_DIR, exist_ok=True)

    # 1. 4 church_kit models
    print("\n--- [1/13] Building town_street_lamp_iron.glb ---")
    build_town_street_lamp_iron(CHURCH_KIT_DIR)

    print("\n--- [2/13] Building town_graveyard_wall_fence_6m.glb ---")
    build_town_graveyard_wall_fence_6m(CHURCH_KIT_DIR)

    print("\n--- [3/13] Building town_road_curb_8m.glb ---")
    build_town_road_curb_8m(CHURCH_KIT_DIR)

    print("\n--- [4/13] Building town_gravestone_cluster.glb ---")
    build_town_gravestone_cluster(CHURCH_KIT_DIR)

    # 2. 5 root models (houses, foliage, terrain)
    print("\n--- [5/13] Building house_abandoned_a.glb ---")
    build_abandoned_house_variant(
        out_dir=ROOT_MODELS_DIR,
        filename="house_abandoned_a.glb",
        width_x=7.6,
        depth_y=9.2,
        wall_height=3.8,
        roof_peak=2.8,
        sag_amount=0.22,
        has_side_annex=False,
    )

    print("\n--- [6/13] Building house_abandoned_b.glb ---")
    build_abandoned_house_variant(
        out_dir=ROOT_MODELS_DIR,
        filename="house_abandoned_b.glb",
        width_x=8.4,
        depth_y=7.8,
        wall_height=4.2,
        roof_peak=3.1,
        sag_amount=0.28,
        has_side_annex=True,
    )

    print("\n--- [7/13] Building grass_clump_wild.glb ---")
    build_grass_clump_wild(ROOT_MODELS_DIR)

    print("\n--- [8/13] Building dead_tree_gnarled.glb ---")
    build_dead_tree_gnarled(ROOT_MODELS_DIR)

    # 3. 4 items models (loot drops & chest)
    print("\n--- [9/13] Building loot_blood_echo_cluster.glb ---")
    build_loot_blood_echo_cluster(ITEMS_DIR)

    print("\n--- [10/13] Building loot_occult_relic_talisman.glb ---")
    build_loot_occult_relic_talisman(ITEMS_DIR)

    print("\n--- [11/13] Building loot_alchemical_elixir.glb ---")
    build_loot_alchemical_elixir(ITEMS_DIR)

    print("\n--- [12/13] Building prop_gothic_reliquary_chest.glb ---")
    build_prop_gothic_reliquary_chest(ITEMS_DIR)

    # 4. Stepped micro-voxel terrain
    print("\n--- [13/13] Building terrain_town.glb ---")
    build_terrain_town(ROOT_MODELS_DIR)

    print("\n" + "=" * 70)
    print("VERIFYING ALL 13 TARGET GLB FILES ON DISK:")
    print("=" * 70)

    target_files = [
        os.path.join(CHURCH_KIT_DIR, "town_street_lamp_iron.glb"),
        os.path.join(CHURCH_KIT_DIR, "town_graveyard_wall_fence_6m.glb"),
        os.path.join(CHURCH_KIT_DIR, "town_road_curb_8m.glb"),
        os.path.join(CHURCH_KIT_DIR, "town_gravestone_cluster.glb"),
        os.path.join(ROOT_MODELS_DIR, "house_abandoned_a.glb"),
        os.path.join(ROOT_MODELS_DIR, "house_abandoned_b.glb"),
        os.path.join(ROOT_MODELS_DIR, "grass_clump_wild.glb"),
        os.path.join(ROOT_MODELS_DIR, "dead_tree_gnarled.glb"),
        os.path.join(ROOT_MODELS_DIR, "terrain_town.glb"),
        os.path.join(ITEMS_DIR, "loot_blood_echo_cluster.glb"),
        os.path.join(ITEMS_DIR, "loot_occult_relic_talisman.glb"),
        os.path.join(ITEMS_DIR, "loot_alchemical_elixir.glb"),
        os.path.join(ITEMS_DIR, "prop_gothic_reliquary_chest.glb"),
    ]

    all_ok = True
    for fp in target_files:
        if os.path.exists(fp):
            sz = os.path.getsize(fp)
            status = "OK" if sz > 1000 else "FAIL (< 1000 bytes)"
            if sz <= 1000:
                all_ok = False
            print(f"  [{status}] {fp} ({sz:,} bytes)")
        else:
            all_ok = False
            print(f"  [MISSING] {fp}")

    if all_ok:
        print("\n[ALL 13 TARGET GLBS SUCCESSFULLY GENERATED AND VERIFIED!]")
    else:
        print("\n[ERROR: One or more target files failed verification!]")
        sys.exit(1)


if __name__ == "__main__":
    main()
