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
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = base_color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if emission_color is not None and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = emission_color
            bsdf.inputs["Emission Strength"].default_value = emission_strength
        vcol = nodes.new(type="ShaderNodeVertexColor")
        vcol.layer_name = "Col"
        mix = nodes.new(type="ShaderNodeMix")
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs[0].default_value = 1.0
        mix.inputs[6].default_value = base_color
        links.new(vcol.outputs["Color"], mix.inputs[7])
        links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    return mat


def create_ossuary_palette() -> list[bpy.types.Material]:
    """
    Returns standard material palette for Ossuary Variety assets:
      0: GothicAshlarStone
      1: DarkFlagstone
      2: CarvedStoneTrim
      3: WroughtIron
      4: AgedBone
      5: TarnishedBrass
      6: TallowWax
      7: EmissiveAmberFlame
      8: EmissiveCrimsonSoul
    """
    return [
        make_pbr_material("GothicAshlarStone", (0.16, 0.16, 0.18, 1.0), roughness=0.88),
        make_pbr_material("DarkFlagstone", (0.09, 0.09, 0.11, 1.0), roughness=0.92),
        make_pbr_material("CarvedStoneTrim", (0.22, 0.21, 0.23, 1.0), roughness=0.82),
        make_pbr_material("WroughtIron", (0.11, 0.11, 0.13, 1.0), roughness=0.48, metallic=0.85),
        make_pbr_material("AgedBone", (0.58, 0.53, 0.43, 1.0), roughness=0.78),
        make_pbr_material("TarnishedBrass", (0.48, 0.36, 0.18, 1.0), roughness=0.42, metallic=0.82),
        make_pbr_material("TallowWax", (0.68, 0.60, 0.44, 1.0), roughness=0.72),
        make_pbr_material(
            "EmissiveAmberFlame",
            (1.0, 0.68, 0.22, 1.0),
            roughness=0.25,
            metallic=0.0,
            emission_color=(1.0, 0.62, 0.18, 1.0),
            emission_strength=3.4,
        ),
        make_pbr_material(
            "EmissiveCrimsonSoul",
            (0.95, 0.18, 0.12, 1.0),
            roughness=0.22,
            metallic=0.0,
            emission_color=(1.0, 0.22, 0.14, 1.0),
            emission_strength=3.6,
        ),
    ]


def _add_skull_cluster_bm(
    bm: bmesh.types.BMesh,
    center: tuple[float, float, float],
    scale: float = 1.0,
    rot_z: float = 0.0,
    mat_bone_idx: int = 4,
    mat_dark_idx: int = 1,
) -> int:
    """Adds a 5-part gothic skull (cranium, brow ridge, jaw, 2 recessed eye sockets) to bm."""
    cx, cy, cz = center
    s = scale
    # Cranium dome
    _add_bm_beveled_box(bm, (0.18 * s, 0.20 * s, 0.16 * s), (cx, cy, cz + 0.04 * s), (0.0, 0.0, rot_z), 0.025 * s, mat_bone_idx)
    # Brow & cheekbones
    _add_bm_beveled_box(bm, (0.19 * s, 0.10 * s, 0.06 * s), (cx, cy - 0.06 * s * math.cos(rot_z), cz + 0.03 * s), (0.0, 0.0, rot_z), 0.012 * s, mat_bone_idx)
    # Lower jaw / maxilla
    _add_bm_beveled_box(bm, (0.13 * s, 0.12 * s, 0.09 * s), (cx, cy - 0.04 * s * math.cos(rot_z), cz - 0.05 * s), (0.0, 0.0, rot_z), 0.012 * s, mat_bone_idx)
    # Dark eye sockets
    for sx in (-1.0, 1.0):
        ex = cx + sx * 0.048 * s * math.cos(rot_z)
        ey = cy - 0.09 * s
        _add_bm_beveled_box(bm, (0.042 * s, 0.04 * s, 0.042 * s), (ex, ey, cz + 0.02 * s), (0.0, 0.0, rot_z), 0.005 * s, mat_dark_idx)
    return 5


def _add_candle_bm(
    bm: bmesh.types.BMesh,
    pos: tuple[float, float, float],
    height: float = 0.22,
    radius: float = 0.035,
    mat_wax_idx: int = 6,
    mat_flame_idx: int = 7,
) -> int:
    px, py, pz = pos
    # Wax base drip collar
    _add_bm_beveled_box(bm, (radius * 2.5, radius * 2.5, 0.03), (px, py, pz + 0.015), (0.0, 0.0, 0.0), 0.006, mat_wax_idx)
    # Wax column
    _add_bm_beveled_box(bm, (radius * 2.0, radius * 2.0, height), (px, py, pz + height * 0.5), (0.0, 0.0, 0.0), 0.008, mat_wax_idx)
    # Emissive flame tear
    _add_bm_beveled_box(bm, (radius * 1.1, radius * 1.1, 0.07), (px, py, pz + height + 0.035), (0.0, 0.0, 0.78), 0.006, mat_flame_idx)
    return 3


def finalize_and_export_bm(
    bm: bmesh.types.BMesh,
    materials: list[bpy.types.Material],
    out_dir: str,
    filename: str,
    z_min: float = -1.0,
    z_max: float = 4.0,
) -> None:
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = True

    obj_name = os.path.splitext(filename)[0]
    mesh = bpy.data.meshes.new(obj_name + "Mesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(obj_name, mesh)
    bpy.context.collection.objects.link(obj)
    for mat in materials:
        obj.data.materials.append(mat)

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    bake_3tone_gothic_vertex_colors(obj, z_min=z_min, z_max=z_max)

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


# ==============================================================================
# 1. ossuary_stone_bridge_4x4.glb (4m span x 2.2m walkway)
# ==============================================================================
def build_ossuary_stone_bridge_4x4(out_dir: str) -> None:
    clear_scene()
    mats = create_ossuary_palette()
    bm = bmesh.new()
    sub_cnt = 0

    # Structural stone deck core (walkway surface at Z=0.0, spanning Y from -2.0 to +2.0, width 2.2m along X)
    _add_bm_beveled_box(bm, (2.16, 4.00, 0.24), (0.0, 0.0, -0.14), (0.0, 0.0, 0.0), 0.015, 1)
    sub_cnt += 1

    # 32 Flagstone walkway cobble slabs across the bridge deck (4 cols x 8 rows)
    for r in range(8):
        cy = -1.75 + r * 0.50
        for c in range(4):
            cx = -0.75 + c * 0.50
            jit_z = (_det_hash(r * 13, c * 7) - 0.5) * 0.012
            rot_z = (_det_hash(r * 29, c * 11) - 0.5) * 0.025
            mat_i = 0 if (r + c) % 2 == 0 else 2
            _add_bm_beveled_box(bm, (0.47, 0.47, 0.08), (cx, cy, -0.03 + jit_z), (0.0, 0.0, rot_z), 0.010, mat_i)
            sub_cnt += 1

    # Twin Underslung Gothic Ribbed Arch Ribs spanning Y = -1.95 to +1.95 (depth down to Z = -1.18m)
    for sx in (-0.96, 0.96):
        # End abutment piers at Y = -1.85 and +1.85
        for sy in (-1.82, 1.82):
            _add_bm_beveled_box(bm, (0.34, 0.36, 1.10), (sx, sy, -0.68), (0.0, 0.0, 0.0), 0.018, 2)
            sub_cnt += 1
        # 11 Voussoir arch stones along each rib curve
        for vi in range(11):
            t = (vi - 5.0) / 5.0  # -1.0 to +1.0
            vy = t * 1.68
            vz = -0.32 - (1.0 - t * t) * 0.65
            pitch = t * 0.42
            _add_bm_beveled_box(bm, (0.28, 0.36, 0.24), (sx, vy, vz), (pitch, 0.0, 0.0), 0.014, 2)
            sub_cnt += 1

    # Transverse stone cross-beams under bridge deck
    for bi in range(5):
        by = -1.50 + bi * 0.75
        _add_bm_beveled_box(bm, (2.10, 0.22, 0.24), (0.0, by, -0.32), (0.0, 0.0, 0.0), 0.012, 0)
        sub_cnt += 1

    # Low crenellated stone side curbs & recessed skull niches along left/right edges (X = +-1.02)
    for sx in (-1.02, 1.02):
        # Continuous curb plinth
        _add_bm_beveled_box(bm, (0.22, 4.00, 0.22), (sx, 0.0, 0.10), (0.0, 0.0, 0.0), 0.014, 2)
        sub_cnt += 1
        # 6 Crenellated merlon blocks per side
        for mi in range(6):
            my = -1.65 + mi * 0.66
            _add_bm_beveled_box(bm, (0.24, 0.36, 0.16), (sx, my, 0.28), (0.0, 0.0, 0.0), 0.012, 0)
            sub_cnt += 1

        # 3 Tall Stone Bollards per side capped with Ossuary Skulls & Wrought-Iron Rings
        for pi, py in enumerate((-1.80, 0.0, 1.80)):
            # Bollard base, shaft, capital
            _add_bm_beveled_box(bm, (0.32, 0.32, 0.18), (sx, py, 0.26), (0.0, 0.0, 0.0), 0.014, 2)
            _add_bm_beveled_box(bm, (0.24, 0.24, 0.56), (sx, py, 0.60), (0.0, 0.0, 0.0), 0.014, 0)
            _add_bm_beveled_box(bm, (0.30, 0.30, 0.12), (sx, py, 0.92), (0.0, 0.0, 0.0), 0.012, 2)
            sub_cnt += 3
            # Skull cap on bollard
            rot_face = math.pi * 0.5 if sx < 0 else -math.pi * 0.5
            sub_cnt += _add_skull_cluster_bm(bm, (sx, py, 1.04), scale=0.95, rot_z=rot_face)
            # Wrought-iron tie ring
            _add_bm_beveled_box(bm, (0.28, 0.10, 0.10), (sx, py, 0.78), (0.0, 0.0, 0.0), 0.008, 3)
            sub_cnt += 1

        # Hanging Wrought-Iron Chain Side-Rails (2 spans per side, 10 chain links per span)
        for span_center_y in (-0.90, 0.90):
            for li in range(10):
                u = (li + 0.5) / 10.0  # 0..1
                ly = (span_center_y - 0.78) + u * 1.56
                sag = math.sin(u * math.pi) * 0.22
                lz = 0.80 - sag
                tilt_x = 0.45 if li % 2 == 0 else -0.45
                _add_bm_beveled_box(bm, (0.055, 0.19, 0.09), (sx, ly, lz), (0.0, tilt_x, 0.0), 0.008, 3)
                sub_cnt += 1

    print(f"[OssuaryVarietyKit] ossuary_stone_bridge_4x4 built with {sub_cnt} physical 3D sub-components")
    finalize_and_export_bm(bm, mats, out_dir, "ossuary_stone_bridge_4x4.glb", z_min=-1.2, z_max=1.3)


# ==============================================================================
# 2. ossuary_balcony_railing_4m.glb (4.0m wide x 1.1m tall)
# ==============================================================================
def build_ossuary_balcony_railing_4m(out_dir: str) -> None:
    clear_scene()
    mats = create_ossuary_palette()
    bm = bmesh.new()
    sub_cnt = 0

    # Stepped base plinth & coping rail (4.0m along X, 0.34m deep along Y, 1.10m tall)
    _add_bm_beveled_box(bm, (4.02, 0.36, 0.14), (0.0, 0.0, 0.07), (0.0, 0.0, 0.0), 0.014, 1)
    _add_bm_beveled_box(bm, (3.98, 0.30, 0.10), (0.0, 0.0, 0.18), (0.0, 0.0, 0.0), 0.012, 2)
    # Heavy top handrail & sub-cornice
    _add_bm_beveled_box(bm, (3.98, 0.30, 0.09), (0.0, 0.0, 0.92), (0.0, 0.0, 0.0), 0.012, 0)
    _add_bm_beveled_box(bm, (4.04, 0.36, 0.12), (0.0, 0.0, 1.02), (0.0, 0.0, 0.0), 0.015, 2)
    sub_cnt += 4

    # 3 Heavy Gothic Pier Newel Posts (at X = -1.86, 0.0, +1.86)
    for px in (-1.86, 0.0, 1.86):
        _add_bm_beveled_box(bm, (0.32, 0.38, 0.96), (px, 0.0, 0.52), (0.0, 0.0, 0.0), 0.015, 2)
        _add_bm_beveled_box(bm, (0.38, 0.42, 0.14), (px, 0.0, 1.06), (0.0, 0.0, 0.0), 0.014, 2)
        # Iron finial spike atop each newel post
        _add_bm_beveled_box(bm, (0.08, 0.08, 0.22), (px, 0.0, 1.22), (0.0, 0.0, 0.78), 0.008, 3)
        sub_cnt += 3
        # Relief skull inset on newel post front
        sub_cnt += _add_skull_cluster_bm(bm, (px, -0.14, 0.56), scale=0.78, rot_z=0.0)

    # 2 Bay Spans (Left Bay: X in [-1.60, -0.26], Right Bay: X in [0.26, 1.60])
    for bay_sign in (-1.0, 1.0):
        bay_cx = bay_sign * 0.93
        # Central pierced stone skull-relief medallion panel in each bay
        _add_bm_beveled_box(bm, (0.48, 0.22, 0.66), (bay_cx, 0.0, 0.55), (0.0, 0.0, 0.0), 0.014, 0)
        _add_bm_beveled_box(bm, (0.38, 0.26, 0.54), (bay_cx, 0.0, 0.55), (0.0, 0.0, 0.0), 0.012, 1)
        sub_cnt += 2
        sub_cnt += _add_skull_cluster_bm(bm, (bay_cx, -0.06, 0.55), scale=0.92, rot_z=0.0)
        sub_cnt += _add_skull_cluster_bm(bm, (bay_cx, 0.06, 0.55), scale=0.92, rot_z=math.pi)

        # 6 Gothic Colonnette Balusters flanking the central medallion per bay (3 per side)
        for side_s in (-1.0, 1.0):
            for bi in range(3):
                bx = bay_cx + side_s * (0.34 + bi * 0.17)
                # Base, shaft, collar, capital
                _add_bm_beveled_box(bm, (0.11, 0.18, 0.10), (bx, 0.0, 0.26), (0.0, 0.0, 0.0), 0.008, 2)
                _add_bm_beveled_box(bm, (0.075, 0.12, 0.52), (bx, 0.0, 0.55), (0.0, 0.0, 0.0), 0.008, 0)
                _add_bm_beveled_box(bm, (0.10, 0.15, 0.06), (bx, 0.0, 0.55), (0.0, 0.0, 0.0), 0.006, 3)
                _add_bm_beveled_box(bm, (0.11, 0.18, 0.10), (bx, 0.0, 0.84), (0.0, 0.0, 0.0), 0.008, 2)
                # Pointed gothic lancet arch link above baluster
                _add_bm_beveled_box(bm, (0.13, 0.20, 0.08), (bx, 0.0, 0.89), (0.0, 0.35 * side_s, 0.0), 0.006, 2)
                sub_cnt += 5

        # 9 Wrought-Iron Pickets & Spikes along top rail per bay
        for si in range(9):
            sx = (bay_cx - 0.64) + si * 0.16
            _add_bm_beveled_box(bm, (0.035, 0.035, 0.18), (sx, 0.0, 1.15), (0.0, 0.0, 0.78), 0.004, 3)
            _add_bm_beveled_box(bm, (0.055, 0.055, 0.05), (sx, 0.0, 1.09), (0.0, 0.0, 0.0), 0.004, 3)
            sub_cnt += 2

    # 4 Melted Tallow Candles along the balustrade handrail
    for cx in (-1.45, -0.42, 0.42, 1.45):
        sub_cnt += _add_candle_bm(bm, (cx, 0.0, 1.08), height=0.16, radius=0.03)

    print(f"[OssuaryVarietyKit] ossuary_balcony_railing_4m built with {sub_cnt} physical 3D sub-components")
    finalize_and_export_bm(bm, mats, out_dir, "ossuary_balcony_railing_4m.glb", z_min=0.0, z_max=1.35)


# ==============================================================================
# 3. ossuary_buttress_arch_4x4.glb (4m x 4m walk-through rib)
# ==============================================================================
def build_ossuary_buttress_arch_4x4(out_dir: str) -> None:
    clear_scene()
    mats = create_ossuary_palette()
    bm = bmesh.new()
    sub_cnt = 0

    # Twin Heavy Side Buttress Piers (X = -1.62 and +1.62, leaving a wide 2.52m walk-through opening in center)
    for sx in (-1.0, 1.0):
        px = sx * 1.62
        # Stepped octagonal-style stone plinth base
        _add_bm_beveled_box(bm, (0.86, 0.96, 0.24), (px, 0.0, 0.12), (0.0, 0.0, 0.0), 0.018, 1)
        _add_bm_beveled_box(bm, (0.78, 0.88, 0.22), (px, 0.0, 0.34), (0.0, 0.0, 0.0), 0.015, 2)
        # Main masonry pier core & recessed bone-niche backer
        _add_bm_beveled_box(bm, (0.68, 0.76, 2.60), (px, 0.0, 1.72), (0.0, 0.0, 0.0), 0.016, 1)
        # Outer & inner vertical gothic pilasters
        _add_bm_beveled_box(bm, (0.18, 0.84, 2.65), (px + sx * 0.28, 0.0, 1.74), (0.0, 0.0, 0.0), 0.014, 0)
        _add_bm_beveled_box(bm, (0.18, 0.84, 2.65), (px - sx * 0.28, 0.0, 1.74), (0.0, 0.0, 0.0), 0.014, 2)
        # Pier capital at Z = 3.05
        _add_bm_beveled_box(bm, (0.82, 0.92, 0.22), (px, 0.0, 3.08), (0.0, 0.0, 0.0), 0.016, 2)
        sub_cnt += 6

        # 5 Tiered Skull & Femur Niches stacked up each pier (both front and back faces)
        for tier in range(5):
            tz = 0.62 + tier * 0.48
            # Horizontal stone shelf divider
            _add_bm_beveled_box(bm, (0.52, 0.82, 0.07), (px, 0.0, tz - 0.18), (0.0, 0.0, 0.0), 0.008, 2)
            # Stacked femur logs
            for fi in range(3):
                fx = px + (fi - 1) * 0.13
                _add_bm_beveled_box(bm, (0.06, 0.78, 0.05), (fx, 0.0, tz - 0.11), (0.0, 0.0, 0.08 * (fi - 1)), 0.006, 4)
            sub_cnt += 4
            # Skull looking inward toward the walkway and outward on Y faces
            sub_cnt += _add_skull_cluster_bm(bm, (px - sx * 0.18, 0.0, tz), scale=0.88, rot_z=sx * math.pi * 0.5)
            sub_cnt += _add_skull_cluster_bm(bm, (px, -0.32, tz), scale=0.82, rot_z=0.0)
            sub_cnt += _add_skull_cluster_bm(bm, (px, 0.32, tz), scale=0.82, rot_z=math.pi)

        # Wrought-iron structural strap bands around pier
        for bz in (0.95, 1.95, 2.85):
            _add_bm_beveled_box(bm, (0.76, 0.88, 0.07), (px, 0.0, bz), (0.0, 0.0, 0.0), 0.006, 3)
            sub_cnt += 1

    # Upper Spandrel Beam & Cornice at Z = 3.85..4.02 spanning full 4.0m width
    _add_bm_beveled_box(bm, (4.00, 0.78, 0.24), (0.0, 0.0, 3.88), (0.0, 0.0, 0.0), 0.016, 0)
    _add_bm_beveled_box(bm, (4.04, 0.88, 0.14), (0.0, 0.0, 3.96), (0.0, 0.0, 0.0), 0.014, 2)
    sub_cnt += 2

    # Pointed Gothic Vaulting Rib Arch (9 voussoir stones per side + central keystone)
    for sx in (-1.0, 1.0):
        for vi in range(9):
            t = (vi + 0.5) / 9.0
            ang = t * (math.pi * 0.44)
            vx = sx * 1.48 * math.cos(ang)
            vz = 3.05 + 0.78 * math.sin(ang)
            _add_bm_beveled_box(bm, (0.24, 0.84, 0.22), (vx, 0.0, vz), (0.0, sx * ang, 0.0), 0.014, 2)
            # Inner iron rib trim
            _add_bm_beveled_box(bm, (0.14, 0.88, 0.08), (vx * 0.95, 0.0, vz - 0.06), (0.0, sx * ang, 0.0), 0.008, 3)
            sub_cnt += 2

    # Central Arch Keystone with Horned Boss Skull
    _add_bm_beveled_box(bm, (0.34, 0.92, 0.36), (0.0, 0.0, 3.82), (0.0, 0.0, 0.0), 0.016, 2)
    sub_cnt += 1
    sub_cnt += _add_skull_cluster_bm(bm, (0.0, -0.42, 3.78), scale=1.1, rot_z=0.0)
    sub_cnt += _add_skull_cluster_bm(bm, (0.0, 0.42, 3.78), scale=1.1, rot_z=math.pi)

    # Hanging Rusted Iron Chains from the Arch Haunches (at X = -0.95 and +0.95, safely outside head clearance)
    for cx in (-1.02, 1.02):
        for li in range(8):
            lz = 3.35 - li * 0.13
            rot_z = 0.65 if li % 2 == 0 else -0.65
            _add_bm_beveled_box(bm, (0.06, 0.09, 0.16), (cx, 0.0, lz), (0.0, 0.0, rot_z), 0.008, 3)
            sub_cnt += 1

    print(f"[OssuaryVarietyKit] ossuary_buttress_arch_4x4 built with {sub_cnt} physical 3D sub-components")
    finalize_and_export_bm(bm, mats, out_dir, "ossuary_buttress_arch_4x4.glb", z_min=0.0, z_max=4.05)


# ==============================================================================
# 4. ossuary_bone_chandelier.glb (Suspended 2.6m-wide Ceiling Centerpiece)
# ==============================================================================
def build_ossuary_bone_chandelier(out_dir: str) -> None:
    clear_scene()
    mats = create_ossuary_palette()
    bm = bmesh.new()
    sub_cnt = 0

    # Ceiling Rosette Mount at Z = 2.40m & Central Suspension Column down to Z = 0.25m
    _add_bm_beveled_box(bm, (0.64, 0.64, 0.16), (0.0, 0.0, 2.34), (0.0, 0.0, 0.0), 0.016, 3)
    _add_bm_beveled_box(bm, (0.42, 0.42, 0.22), (0.0, 0.0, 2.18), (0.0, 0.0, 0.78), 0.014, 5)
    _add_bm_beveled_box(bm, (0.16, 0.16, 1.95), (0.0, 0.0, 1.25), (0.0, 0.0, 0.0), 0.012, 3)
    # Bottom iron drop finial & cage boss
    _add_bm_beveled_box(bm, (0.38, 0.38, 0.28), (0.0, 0.0, 0.28), (0.0, 0.0, 0.78), 0.015, 5)
    _add_bm_beveled_box(bm, (0.14, 0.14, 0.32), (0.0, 0.0, 0.08), (0.0, 0.0, 0.78), 0.010, 3)
    sub_cnt += 5

    # Lower Outer Wheel (Radius = 1.28m -> 2.56m wide at Z = 0.55m, 16 polygonal iron & bone segments)
    r_outer = 1.25
    z_outer = 0.55
    for i in range(16):
        ang = (i / 16.0) * math.tau
        ang_mid = ((i + 0.5) / 16.0) * math.tau
        seg_len = 2.0 * r_outer * math.sin(math.pi / 16.0) + 0.04
        mx = r_outer * math.cos(ang_mid)
        my = r_outer * math.sin(ang_mid)
        # Outer wrought-iron band + inner bone rim
        _add_bm_beveled_box(bm, (0.10, seg_len, 0.16), (mx, my, z_outer), (0.0, 0.0, ang_mid), 0.010, 3)
        _add_bm_beveled_box(bm, (0.14, seg_len * 0.9, 0.09), (mx * 0.93, my * 0.93, z_outer), (0.0, 0.0, ang_mid), 0.008, 4)
        sub_cnt += 2

        # 16 Skull-and-Tallow Candle Stations around the outer wheel
        vx = r_outer * math.cos(ang)
        vy = r_outer * math.sin(ang)
        # Brass drip pan
        _add_bm_beveled_box(bm, (0.22, 0.22, 0.04), (vx, vy, z_outer + 0.10), (0.0, 0.0, ang), 0.006, 5)
        sub_cnt += 1
        # Outward-facing ossuary skull mount
        sub_cnt += _add_skull_cluster_bm(bm, (vx * 1.03, vy * 1.03, z_outer), scale=0.80, rot_z=ang + math.pi * 0.5)
        # Lit tallow candle atop skull/drip pan
        sub_cnt += _add_candle_bm(bm, (vx, vy, z_outer + 0.12), height=0.22, radius=0.036)

    # 8 Radial Bone-and-Iron Spokes + 8 Diagonal Suspension Chains for Outer Wheel
    for i in range(8):
        ang = (i / 8.0) * math.tau
        sx = (r_outer * 0.5) * math.cos(ang)
        sy = (r_outer * 0.5) * math.sin(ang)
        _add_bm_beveled_box(bm, (r_outer, 0.07, 0.07), (sx, sy, z_outer), (0.0, 0.0, ang), 0.008, 3)
        sub_cnt += 1
        # 5 Chain links rising from outer wheel to upper hub (Z=0.65 to Z=2.10)
        for li in range(5):
            u = (li + 0.5) / 5.0
            cr = r_outer * (1.0 - u * 0.82)
            cz = z_outer + 0.12 + u * 1.48
            _add_bm_beveled_box(
                bm,
                (0.06, 0.12, 0.28),
                (cr * math.cos(ang), cr * math.sin(ang), cz),
                (0.0, -0.58, ang),
                0.008,
                3,
            )
            sub_cnt += 1

    # Upper Tiered Wheel (Radius = 0.72m at Z = 1.25m, 8 segments + 8 candles)
    r_inner = 0.72
    z_inner = 1.25
    for i in range(8):
        ang = (i / 8.0) * math.tau
        ang_mid = ((i + 0.5) / 8.0) * math.tau
        seg_len = 2.0 * r_inner * math.sin(math.pi / 8.0) + 0.04
        mx = r_inner * math.cos(ang_mid)
        my = r_inner * math.sin(ang_mid)
        _add_bm_beveled_box(bm, (0.09, seg_len, 0.13), (mx, my, z_inner), (0.0, 0.0, ang_mid), 0.008, 5)
        sub_cnt += 1

        vx = r_inner * math.cos(ang)
        vy = r_inner * math.sin(ang)
        _add_bm_beveled_box(bm, (0.18, 0.18, 0.04), (vx, vy, z_inner + 0.08), (0.0, 0.0, ang), 0.006, 5)
        sub_cnt += 1
        sub_cnt += _add_candle_bm(bm, (vx, vy, z_inner + 0.10), height=0.20, radius=0.032)

    print(f"[OssuaryVarietyKit] ossuary_bone_chandelier built with {sub_cnt} physical 3D sub-components")
    finalize_and_export_bm(bm, mats, out_dir, "ossuary_bone_chandelier.glb", z_min=0.0, z_max=2.5)


# ==============================================================================
# 5. ossuary_spine_reliquary_monolith.glb (Tall Floor Centerpiece - 3.4m tall)
# ==============================================================================
def build_ossuary_spine_reliquary_monolith(out_dir: str) -> None:
    clear_scene()
    mats = create_ossuary_palette()
    bm = bmesh.new()
    sub_cnt = 0

    # Stepped Octagonal Stone Plinth Base (Z = 0.0 to 0.72m)
    for rot_z in (0.0, math.pi * 0.25):
        _add_bm_beveled_box(bm, (1.65, 1.65, 0.22), (0.0, 0.0, 0.11), (0.0, 0.0, rot_z), 0.018, 1)
        _add_bm_beveled_box(bm, (1.36, 1.36, 0.24), (0.0, 0.0, 0.33), (0.0, 0.0, rot_z), 0.016, 0)
        _add_bm_beveled_box(bm, (1.10, 1.10, 0.26), (0.0, 0.0, 0.56), (0.0, 0.0, rot_z), 0.015, 2)
        sub_cnt += 3

    # 4 Corner Guardian Skulls & candles on the plinth ledge (Z = 0.69m)
    for i in range(4):
        ang = (i / 4.0) * math.tau + math.pi * 0.25
        rx = 0.58 * math.cos(ang)
        ry = 0.58 * math.sin(ang)
        sub_cnt += _add_skull_cluster_bm(bm, (rx, ry, 0.74), scale=0.95, rot_z=ang + math.pi * 0.5)
        ang_c = (i / 4.0) * math.tau
        sub_cnt += _add_candle_bm(bm, (0.62 * math.cos(ang_c), 0.62 * math.sin(ang_c), 0.68), height=0.20, radius=0.034)

    # 8 Wrought-Iron Reliquary Cage Vertical Ribs rising from Z = 0.68m to Z = 3.05m
    for i in range(8):
        ang = (i / 8.0) * math.tau
        rx = 0.44 * math.cos(ang)
        ry = 0.44 * math.sin(ang)
        _add_bm_beveled_box(bm, (0.065, 0.065, 2.38), (rx, ry, 1.86), (0.0, 0.0, ang), 0.008, 3)
        sub_cnt += 1
        # Iron hoop straps at 4 heights
        for hz in (1.05, 1.65, 2.25, 2.85):
            ang_mid = ((i + 0.5) / 8.0) * math.tau
            _add_bm_beveled_box(
                bm,
                (0.05, 0.36, 0.07),
                (0.44 * math.cos(ang_mid), 0.44 * math.sin(ang_mid), hz),
                (0.0, 0.0, ang_mid),
                0.006,
                3,
            )
            sub_cnt += 1

    # Towering Fused Vertebrae Spine Column inside the cage (18 articulated vertebrae + transverse ribs)
    for vi in range(18):
        vz = 0.80 + vi * 0.125
        twist = vi * 0.22
        # Vertebral centrum body
        _add_bm_beveled_box(bm, (0.28, 0.28, 0.095), (0.0, 0.0, vz), (0.0, 0.0, twist), 0.012, 4)
        # Transverse bone processes & dorsal spinous spur
        _add_bm_beveled_box(bm, (0.52, 0.10, 0.055), (0.0, 0.0, vz), (0.0, 0.0, twist), 0.008, 4)
        _add_bm_beveled_box(bm, (0.10, 0.52, 0.055), (0.0, 0.0, vz), (0.0, 0.0, twist), 0.008, 4)
        sub_cnt += 3

    # Blazing Crimson-Amber Soul Core at the heart of the monolith (Z = 1.95m)
    _add_bm_beveled_box(bm, (0.34, 0.34, 0.62), (0.0, 0.0, 1.95), (0.35, 0.35, 0.0), 0.018, 8)
    _add_bm_beveled_box(bm, (0.38, 0.38, 0.38), (0.0, 0.0, 1.95), (0.0, 0.78, 0.78), 0.015, 7)
    sub_cnt += 2

    # 3 Orbiting Tarnished-Brass Astrolabe Rings around the upper monolith (12 segments each)
    for ring_i, (tilt_x, tilt_y, r_ast) in enumerate(((0.42, 0.15, 0.62), (-0.38, 0.45, 0.68), (0.12, -0.52, 0.56))):
        for si in range(12):
            ang = (si / 12.0) * math.tau
            px = r_ast * math.cos(ang)
            py = r_ast * math.sin(ang) * math.cos(tilt_x)
            pz = 1.95 + r_ast * math.sin(ang) * math.sin(tilt_x) + r_ast * math.cos(ang) * math.sin(tilt_y) * 0.3
            _add_bm_beveled_box(bm, (0.06, 0.34, 0.06), (px, py, pz), (tilt_x, tilt_y, ang), 0.006, 5)
            sub_cnt += 1

    # Crown Reliquary Cap & 4 Horned Skull Effigies at Z = 3.05m..3.42m
    _add_bm_beveled_box(bm, (0.76, 0.76, 0.18), (0.0, 0.0, 3.06), (0.0, 0.0, 0.0), 0.014, 2)
    _add_bm_beveled_box(bm, (0.22, 0.22, 0.42), (0.0, 0.0, 3.26), (0.0, 0.0, 0.78), 0.012, 3)
    sub_cnt += 2
    for i in range(4):
        ang = (i / 4.0) * math.tau
        sub_cnt += _add_skull_cluster_bm(bm, (0.38 * math.cos(ang), 0.38 * math.sin(ang), 3.12), scale=0.90, rot_z=ang + math.pi * 0.5)

    print(f"[OssuaryVarietyKit] ossuary_spine_reliquary_monolith built with {sub_cnt} physical 3D sub-components")
    finalize_and_export_bm(bm, mats, out_dir, "ossuary_spine_reliquary_monolith.glb", z_min=0.0, z_max=3.45)


# ==============================================================================
# 6. ossuary_burial_niche_divider_4x4.glb (Interior Cover/Maze Wall - 3.2m x 2.8m)
# ==============================================================================
def build_ossuary_burial_niche_divider_4x4(out_dir: str) -> None:
    clear_scene()
    mats = create_ossuary_palette()
    bm = bmesh.new()
    sub_cnt = 0

    # Stepped Stone Base Plinth (3.24m wide along X, 0.58m deep along Y, 0.36m tall)
    _add_bm_beveled_box(bm, (3.28, 0.62, 0.18), (0.0, 0.0, 0.09), (0.0, 0.0, 0.0), 0.015, 1)
    _add_bm_beveled_box(bm, (3.20, 0.54, 0.18), (0.0, 0.0, 0.26), (0.0, 0.0, 0.0), 0.014, 2)
    sub_cnt += 2

    # Twin Outer Stone End-Piers at X = -1.46 and +1.46 (height 2.80m)
    for sx in (-1.46, 1.46):
        _add_bm_beveled_box(bm, (0.36, 0.56, 2.42), (sx, 0.0, 1.48), (0.0, 0.0, 0.0), 0.015, 0)
        _add_bm_beveled_box(bm, (0.42, 0.62, 0.16), (sx, 0.0, 2.72), (0.0, 0.0, 0.0), 0.014, 2)
        sub_cnt += 2
        sub_cnt += _add_skull_cluster_bm(bm, (sx, 0.0, 2.86), scale=0.92, rot_z=0.0)

    # Central Open Barred Iron Window Frame (X in [-0.52, +0.52], Z in [1.05, 2.35])
    # Jamb pillars flanking center window at X = -0.56 and +0.56
    for jx in (-0.56, 0.56):
        _add_bm_beveled_box(bm, (0.18, 0.52, 2.30), (jx, 0.0, 1.45), (0.0, 0.0, 0.0), 0.012, 2)
        sub_cnt += 1
    # Window sill & lintel
    _add_bm_beveled_box(bm, (1.24, 0.58, 0.14), (0.0, 0.0, 1.02), (0.0, 0.0, 0.0), 0.012, 2)
    _add_bm_beveled_box(bm, (1.24, 0.58, 0.16), (0.0, 0.0, 2.38), (0.0, 0.0, 0.0), 0.012, 2)
    # Lower center masonry panel below window (Z = 0.35..0.98)
    _add_bm_beveled_box(bm, (1.04, 0.44, 0.64), (0.0, 0.0, 0.66), (0.0, 0.0, 0.0), 0.012, 0)
    sub_cnt += 3

    # 5 Vertical Wrought-Iron Window Bars + 2 Crossbars inside the center window opening
    for bi in range(5):
        bx = -0.36 + bi * 0.18
        _add_bm_beveled_box(bm, (0.04, 0.04, 1.26), (bx, 0.0, 1.70), (0.0, 0.0, 0.0), 0.005, 3)
        sub_cnt += 1
    for bz in (1.42, 1.98):
        _add_bm_beveled_box(bm, (1.04, 0.06, 0.05), (0.0, 0.0, bz), (0.0, 0.0, 0.0), 0.005, 3)
        sub_cnt += 1

    # Left & Right Catacomb Burial Niche Bays (X centered at -1.01 and +1.01, 4 vertical tiers each)
    for bay_x in (-1.01, 1.01):
        # Dark recessed spine wall inside niche bay
        _add_bm_beveled_box(bm, (0.74, 0.28, 2.25), (bay_x, 0.0, 1.46), (0.0, 0.0, 0.0), 0.010, 1)
        sub_cnt += 1
        for tier in range(4):
            tz = 0.55 + tier * 0.54
            # Stone niche shelf
            _add_bm_beveled_box(bm, (0.76, 0.50, 0.08), (bay_x, 0.0, tz - 0.18), (0.0, 0.0, 0.0), 0.010, 2)
            sub_cnt += 1
            # 2 Skulls on front (-Y) and 2 Skulls on back (+Y) per shelf tier
            for off_x in (-0.18, 0.18):
                sub_cnt += _add_skull_cluster_bm(bm, (bay_x + off_x, -0.16, tz), scale=0.80, rot_z=0.0)
                sub_cnt += _add_skull_cluster_bm(bm, (bay_x + off_x, 0.16, tz), scale=0.80, rot_z=math.pi)

    # Top Stepped Cornice & Crenellated Ossuary Crest along Z = 2.60..2.80m
    _add_bm_beveled_box(bm, (3.22, 0.54, 0.16), (0.0, 0.0, 2.56), (0.0, 0.0, 0.0), 0.014, 0)
    _add_bm_beveled_box(bm, (3.28, 0.60, 0.12), (0.0, 0.0, 2.68), (0.0, 0.0, 0.0), 0.014, 2)
    sub_cnt += 2

    # 6 Melted Tallow Candles along the window sill & top cornice ledge
    for cx in (-0.32, 0.0, 0.32):
        sub_cnt += _add_candle_bm(bm, (cx, -0.22, 1.09), height=0.15, radius=0.028)
        sub_cnt += _add_candle_bm(bm, (cx, 0.22, 1.09), height=0.15, radius=0.028)

    print(f"[OssuaryVarietyKit] ossuary_burial_niche_divider_4x4 built with {sub_cnt} physical 3D sub-components")
    finalize_and_export_bm(bm, mats, out_dir, "ossuary_burial_niche_divider_4x4.glb", z_min=0.0, z_max=2.95)


def main() -> None:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(project_root, "assets", "models", "ossuary_variety")
    os.makedirs(out_dir, exist_ok=True)

    build_ossuary_stone_bridge_4x4(out_dir)
    build_ossuary_balcony_railing_4m(out_dir)
    build_ossuary_buttress_arch_4x4(out_dir)
    build_ossuary_bone_chandelier(out_dir)
    build_ossuary_spine_reliquary_monolith(out_dir)
    build_ossuary_burial_niche_divider_4x4(out_dir)
    print("[ALL DONE] Exported all 6 bespoke Ossuary Variety assets.")


if __name__ == "__main__":
    main()
