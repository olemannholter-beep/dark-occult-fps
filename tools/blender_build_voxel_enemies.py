import bpy
import bmesh
import math
import os
import sys
from mathutils import Vector, Euler

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from blender_detail_kit import bake_3tone_gothic_vertex_colors

ENEMIES_OUT_DIR = os.path.join(PROJECT_ROOT, "assets", "models", "enemies")


def clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_pbr_material(
    name: str,
    base_color: tuple[float, float, float, float],
    roughness: float = 0.86,
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


def create_enemy_palette() -> dict[str, bpy.types.Material]:
    return {
        "AgedBone": make_pbr_material("AgedBone", (0.76, 0.71, 0.59, 1.0), roughness=0.86, metallic=0.0),
        "WroughtIron": make_pbr_material("WroughtIron", (0.15, 0.16, 0.18, 1.0), roughness=0.48, metallic=0.85),
        "GothicPlateSteel": make_pbr_material("GothicPlateSteel", (0.20, 0.23, 0.28, 1.0), roughness=0.38, metallic=0.88),
        "TarnishedBronze": make_pbr_material("TarnishedBronze", (0.58, 0.44, 0.22, 1.0), roughness=0.40, metallic=0.86),
        "WeatheredLeather": make_pbr_material("WeatheredLeather", (0.20, 0.12, 0.08, 1.0), roughness=0.84, metallic=0.0),
        "RottedTimber": make_pbr_material("RottedTimber", (0.24, 0.16, 0.10, 1.0), roughness=0.90, metallic=0.0),
        "WeatheredStone": make_pbr_material("WeatheredStone", (0.28, 0.27, 0.30, 1.0), roughness=0.90, metallic=0.0),
        "ObsidianPlate": make_pbr_material("ObsidianPlate", (0.10, 0.08, 0.11, 1.0), roughness=0.32, metallic=0.90),
        "SilveredSteel": make_pbr_material("SilveredSteel", (0.76, 0.79, 0.84, 1.0), roughness=0.28, metallic=0.94),
        "EmissiveAmberFlame": make_pbr_material(
            "EmissiveAmberFlame",
            (1.0, 0.62, 0.18, 1.0),
            roughness=0.22,
            metallic=0.05,
            emission_color=(1.0, 0.64, 0.20, 1.0),
            emission_strength=3.2,
        ),
        "GlowingOccultRune": make_pbr_material(
            "GlowingOccultRune",
            (0.84, 0.32, 1.0, 1.0),
            roughness=0.24,
            metallic=0.10,
            emission_color=(0.86, 0.36, 1.0, 1.0),
            emission_strength=3.2,
        ),
        "SicklyGreenBile": make_pbr_material(
            "SicklyGreenBile",
            (0.42, 0.96, 0.28, 1.0),
            roughness=0.20,
            metallic=0.05,
            emission_color=(0.45, 0.98, 0.32, 1.0),
            emission_strength=2.8,
        ),
        "FrozenBlueSoul": make_pbr_material(
            "FrozenBlueSoul",
            (0.28, 0.76, 1.0, 1.0),
            roughness=0.20,
            metallic=0.10,
            emission_color=(0.32, 0.80, 1.0, 1.0),
            emission_strength=3.2,
        ),
        "AbyssalCrimson": make_pbr_material(
            "AbyssalCrimson",
            (0.95, 0.10, 0.16, 1.0),
            roughness=0.22,
            metallic=0.15,
            emission_color=(0.98, 0.12, 0.18, 1.0),
            emission_strength=3.5,
        ),
    }


def make_box(
    name: str,
    loc: tuple[float, float, float],
    size: tuple[float, float, float],
    mat: bpy.types.Material,
    rot: tuple[float, float, float] = (0.0, 0.0, 0.0),
    bevel: float = 0.008,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    obj.data.materials.append(mat)
    if bevel > 0.0:
        bev = obj.modifiers.new(name="Bevel", type='BEVEL')
        bev.width = bevel
        bev.segments = 2
        bev.limit_method = 'ANGLE'
        bpy.ops.object.modifier_apply(modifier=bev.name)
    return obj


def remesh_to_micro_voxels(obj: bpy.types.Object, voxel_size: float = 0.010) -> bpy.types.Object:
    """Converts smooth primitives to crisp 8mm-12mm micro-voxel blocks with flat shading."""
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    dim_max = max(obj.dimensions)
    if dim_max < 0.008:
        return obj
    n_blocks = max(2, int(round(dim_max / voxel_size)))
    depth = max(3, min(7, int(math.ceil(math.log2(n_blocks)))))
    rem = obj.modifiers.new(name="MicroVoxelBlocks", type='REMESH')
    rem.mode = 'BLOCKS'
    rem.octree_depth = depth
    rem.scale = 0.90
    rem.use_remove_disconnected = False
    rem.use_smooth_shade = False
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=rem.name)
    return obj


def make_cyl(
    name: str,
    loc: tuple[float, float, float],
    radius: float,
    depth: float,
    mat: bpy.types.Material,
    rot: tuple[float, float, float] = (0.0, 0.0, 0.0),
    verts: int = 12,
    bevel: float = 0.006,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    obj.data.materials.append(mat)
    remesh_to_micro_voxels(obj, voxel_size=0.010)
    return obj


def make_cone(
    name: str,
    loc: tuple[float, float, float],
    r1: float,
    r2: float,
    depth: float,
    mat: bpy.types.Material,
    rot: tuple[float, float, float] = (0.0, 0.0, 0.0),
    verts: int = 10,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    obj.data.materials.append(mat)
    remesh_to_micro_voxels(obj, voxel_size=0.010)
    return obj


def make_torus(
    name: str,
    loc: tuple[float, float, float],
    major_r: float,
    minor_r: float,
    mat: bpy.types.Material,
    rot: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(
        major_segments=14, minor_segments=8,
        major_radius=major_r, minor_radius=minor_r,
        location=loc, rotation=rot,
    )
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    obj.data.materials.append(mat)
    remesh_to_micro_voxels(obj, voxel_size=0.010)
    return obj


def make_sphere(
    name: str,
    loc: tuple[float, float, float],
    radius: float,
    mat: bpy.types.Material,
    scale_xyz: tuple[float, float, float] = (1.0, 1.0, 1.0),
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=radius, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale_xyz
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    obj.data.materials.append(mat)
    remesh_to_micro_voxels(obj, voxel_size=0.010)
    return obj


def spawn_chain_strand(
    prefix: str,
    start_pt: tuple[float, float, float],
    count: int,
    step_vec: tuple[float, float, float],
    major_r: float,
    minor_r: float,
    mat: bpy.types.Material,
) -> list[bpy.types.Object]:
    out: list[bpy.types.Object] = []
    sx, sy, sz = start_pt
    dx, dy, dz = step_vec
    for i in range(count):
        lx = sx + dx * i
        ly = sy + dy * i
        lz = sz + dz * i
        rz = math.radians(90.0) if (i % 2 == 1) else 0.0
        lk = make_torus(f"{prefix}_Chain_{i}", (lx, ly, lz), major_r, minor_r, mat, (math.radians(90.0), 0.0, rz))
        out.append(lk)
    return out


def spawn_rivet_cluster(
    prefix: str,
    pts: list[tuple[float, float, float]],
    radius: float,
    mat: bpy.types.Material,
) -> list[bpy.types.Object]:
    out: list[bpy.types.Object] = []
    for idx, pt in enumerate(pts):
        out.append(make_sphere(f"{prefix}_Riv_{idx}", pt, radius, mat))
    return out


def join_into_hierarchy_node(
    node_name: str,
    parts: list[bpy.types.Object],
    pivot_world: tuple[float, float, float],
    parent_obj: bpy.types.Object | None,
    parent_world: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> bpy.types.Object:
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(parts) > 1:
        bpy.ops.object.join()
    joined = bpy.context.active_object
    joined.name = node_name
    joined.data.name = f"{node_name}_Mesh"

    px, py, pz = pivot_world
    py_gltf = -py
    parent_py_gltf = -parent_world[1]
    bm = bmesh.new()
    bm.from_mesh(joined.data)
    for v in bm.verts:
        v.co.y = -v.co.y
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(-px, -py_gltf, -pz))
    bm.to_mesh(joined.data)
    bm.free()
    joined.data.update()

    bake_3tone_gothic_vertex_colors(joined, z_min=-1.0, z_max=1.2)

    if parent_obj is not None:
        joined.parent = parent_obj
        joined.location = (
            px - parent_world[0],
            py_gltf - parent_py_gltf,
            pz - parent_world[2],
        )
    else:
        joined.location = (px, py_gltf, pz)
    joined.rotation_euler = (0.0, 0.0, 0.0)
    joined.scale = (1.0, 1.0, 1.0)
    return joined


def export_articulated_enemy_glb(
    filename: str,
    pelvis_parts: list[bpy.types.Object],
    thigh_l_parts: list[bpy.types.Object],
    shin_l_parts: list[bpy.types.Object],
    thigh_r_parts: list[bpy.types.Object],
    shin_r_parts: list[bpy.types.Object],
    torso_parts: list[bpy.types.Object],
    head_parts: list[bpy.types.Object],
    upper_arm_l_parts: list[bpy.types.Object],
    forearm_l_parts: list[bpy.types.Object],
    upper_arm_r_parts: list[bpy.types.Object],
    forearm_r_parts: list[bpy.types.Object],
    secondary_prop_parts: list[bpy.types.Object],
    pivots: dict[str, tuple[float, float, float]] | None = None,
) -> int:
    total_parts = (
        len(pelvis_parts) + len(thigh_l_parts) + len(shin_l_parts)
        + len(thigh_r_parts) + len(shin_r_parts) + len(torso_parts)
        + len(head_parts) + len(upper_arm_l_parts) + len(forearm_l_parts)
        + len(upper_arm_r_parts) + len(forearm_r_parts) + len(secondary_prop_parts)
    )
    if pivots is None:
        pivots = {
            "Pelvis": (0.0, 0.0, 0.95),
            "ThighL": (-0.14, 0.0, 0.88),
            "ShinL": (-0.14, 0.0, 0.50),
            "ThighR": (0.14, 0.0, 0.88),
            "ShinR": (0.14, 0.0, 0.50),
            "Torso": (0.0, 0.0, 1.05),
            "Head": (0.0, 0.0, 1.58),
            "UpperArmL": (-0.30, 0.0, 1.46),
            "ForearmL": (-0.30, -0.04, 1.21),
            "UpperArmR": (0.30, 0.0, 1.46),
            "ForearmR": (0.30, -0.04, 1.21),
            "SecondaryProp": (0.0, 0.0, 1.38),
        }

    p_pelvis = pivots["Pelvis"]
    p_thigh_l = pivots["ThighL"]
    p_shin_l = pivots["ShinL"]
    p_thigh_r = pivots["ThighR"]
    p_shin_r = pivots["ShinR"]
    p_torso = pivots["Torso"]
    p_head = pivots["Head"]
    p_uarm_l = pivots["UpperArmL"]
    p_farm_l = pivots["ForearmL"]
    p_uarm_r = pivots["UpperArmR"]
    p_farm_r = pivots["ForearmR"]
    p_sec = pivots["SecondaryProp"]

    pelvis_obj = join_into_hierarchy_node("Pelvis", pelvis_parts, p_pelvis, None, (0.0, 0.0, 0.0))
    thigh_l_obj = join_into_hierarchy_node("ThighL", thigh_l_parts, p_thigh_l, pelvis_obj, p_pelvis)
    _shin_l_obj = join_into_hierarchy_node("ShinL", shin_l_parts, p_shin_l, thigh_l_obj, p_thigh_l)
    thigh_r_obj = join_into_hierarchy_node("ThighR", thigh_r_parts, p_thigh_r, pelvis_obj, p_pelvis)
    _shin_r_obj = join_into_hierarchy_node("ShinR", shin_r_parts, p_shin_r, thigh_r_obj, p_thigh_r)

    torso_obj = join_into_hierarchy_node("Torso", torso_parts, p_torso, pelvis_obj, p_pelvis)
    _head_obj = join_into_hierarchy_node("Head", head_parts, p_head, torso_obj, p_torso)
    uarm_l_obj = join_into_hierarchy_node("UpperArmL", upper_arm_l_parts, p_uarm_l, torso_obj, p_torso)
    _farm_l_obj = join_into_hierarchy_node("ForearmL", forearm_l_parts, p_farm_l, uarm_l_obj, p_uarm_l)
    uarm_r_obj = join_into_hierarchy_node("UpperArmR", upper_arm_r_parts, p_uarm_r, torso_obj, p_torso)
    _farm_r_obj = join_into_hierarchy_node("ForearmR", forearm_r_parts, p_farm_r, uarm_r_obj, p_uarm_r)

    if len(secondary_prop_parts) > 0:
        _sec_obj = join_into_hierarchy_node("SecondaryProp", secondary_prop_parts, p_sec, torso_obj, p_torso)

    os.makedirs(ENEMIES_OUT_DIR, exist_ok=True)
    out_path = os.path.join(ENEMIES_OUT_DIR, filename)
    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format='GLB',
        use_selection=False,
        export_apply=False,
    )
    print(f"[VoxelEnemyBuilder] Exported {filename} with {total_parts} physical 3D sub-elements -> {out_path}")
    return total_parts


# ==============================================================================
# SHARED ANATOMICAL & ARMOR SUB-ASSEMBLIES (Facing Blender -Y -> Godot -Z)
# ==============================================================================

def build_articulated_legs_and_pelvis(
    mats: dict[str, bpy.types.Material],
    mat_primary: bpy.types.Material,
    mat_trim: bpy.types.Material,
    mat_accent: bpy.types.Material,
    include_tassets: bool = True,
    robe_skirt: bool = False,
) -> tuple[
    list[bpy.types.Object],
    list[bpy.types.Object],
    list[bpy.types.Object],
    list[bpy.types.Object],
    list[bpy.types.Object],
]:
    pelvis_parts: list[bpy.types.Object] = []
    thigh_l_parts: list[bpy.types.Object] = []
    shin_l_parts: list[bpy.types.Object] = []
    thigh_r_parts: list[bpy.types.Object] = []
    shin_r_parts: list[bpy.types.Object] = []

    # Pelvis girdle, codpiece, belt & buckle
    pelvis_parts.append(make_box("PelvisCore", (0.0, 0.0, 0.92), (0.34, 0.22, 0.16), mat_primary))
    pelvis_parts.append(make_box("WaistBelt", (0.0, 0.0, 0.98), (0.37, 0.25, 0.055), mats["WeatheredLeather"]))
    pelvis_parts.append(make_box("BeltBuckle", (0.0, -0.13, 0.98), (0.09, 0.03, 0.075), mat_trim))
    pelvis_parts.append(make_sphere("BuckleStud", (0.0, -0.145, 0.98), 0.022, mat_trim))
    pelvis_parts.append(make_box("SacralPlate", (0.0, 0.11, 0.91), (0.16, 0.035, 0.14), mat_trim))

    if include_tassets:
        for side_i, sx in enumerate((-1.0, 1.0)):
            for t_idx in range(2):
                tz = 0.88 - t_idx * 0.06
                ty = -0.11 - t_idx * 0.015
                pelvis_parts.append(
                    make_box(
                        f"PelvisTasset_{side_i}_{t_idx}",
                        (sx * 0.12, ty, tz),
                        (0.12, 0.035, 0.075),
                        mat_primary,
                        (math.radians(-14.0), 0.0, sx * math.radians(-8.0)),
                    )
                )

    if robe_skirt:
        for r_i in range(5):
            rz = 0.86 - r_i * 0.08
            r_scale = 1.0 + r_i * 0.09
            pelvis_parts.append(
                make_cone(
                    f"RobeSkirtLame_{r_i}",
                    (0.0, 0.01, rz),
                    0.24 * r_scale,
                    0.20 * r_scale,
                    0.09,
                    mat_accent,
                    verts=12,
                )
            )

    # Thighs & Shins (Symmetrical L & R)
    for side_i, (sx, thigh_list, shin_list) in enumerate((
        (-1.0, thigh_l_parts, shin_l_parts),
        (1.0, thigh_r_parts, shin_r_parts),
    )):
        pref = "LegL" if side_i == 0 else "LegR"
        thigh_list.append(make_sphere(f"{pref}_HipJoint", (sx * 0.14, 0.0, 0.88), 0.052, mat_trim))
        thigh_list.append(make_cyl(f"{pref}_Cuisse", (sx * 0.14, -0.01, 0.72), 0.058, 0.26, mat_primary, (math.radians(-8.0), 0.0, 0.0)))
        for b_idx in range(2):
            thigh_list.append(
                make_torus(
                    f"{pref}_CuisseBand_{b_idx}",
                    (sx * 0.14, -0.01, 0.77 - b_idx * 0.09),
                    0.062,
                    0.009,
                    mat_trim,
                    (math.radians(-8.0), 0.0, 0.0),
                )
            )

        shin_list.append(make_sphere(f"{pref}_KneePoleyn", (sx * 0.14, -0.03, 0.50), 0.055, mat_trim))
        shin_list.append(make_cone(f"{pref}_KneeSpike", (sx * 0.14, -0.08, 0.50), 0.024, 0.003, 0.075, mat_trim, (math.radians(-90.0), 0.0, 0.0)))
        shin_list.append(make_cyl(f"{pref}_Greave", (sx * 0.14, 0.0, 0.30), 0.052, 0.32, mat_primary))
        for g_idx in range(2):
            shin_list.append(make_torus(f"{pref}_GreaveRing_{g_idx}", (sx * 0.14, 0.0, 0.36 - g_idx * 0.12), 0.056, 0.008, mat_trim))
        shin_list.append(make_box(f"{pref}_SabatonAnkle", (sx * 0.14, -0.03, 0.10), (0.10, 0.14, 0.08), mat_primary))
        shin_list.append(make_box(f"{pref}_SabatonToe", (sx * 0.14, -0.12, 0.05), (0.09, 0.14, 0.06), mat_trim, (math.radians(-12.0), 0.0, 0.0)))
        shin_list.append(make_cone(f"{pref}_ToeSpur", (sx * 0.14, -0.20, 0.04), 0.016, 0.002, 0.055, mat_trim, (math.radians(-90.0), 0.0, 0.0)))

    return pelvis_parts, thigh_l_parts, shin_l_parts, thigh_r_parts, shin_r_parts


def build_ribcage_and_cuirass_torso(
    mats: dict[str, bpy.types.Material],
    mat_cuirass: bpy.types.Material,
    mat_trim: bpy.types.Material,
    mat_glow: bpy.types.Material,
    exposed_ribs: bool = False,
) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    # Spine column on back (+Y)
    for v_idx in range(6):
        vz = 1.04 + v_idx * 0.068
        parts.append(make_cyl(f"SpineVert_{v_idx}", (0.0, 0.08, vz), 0.048, 0.052, mats["AgedBone"]))
        parts.append(make_cone(f"SpineSpur_{v_idx}", (0.0, 0.14, vz), 0.022, 0.004, 0.065, mat_trim, (math.radians(-75.0), 0.0, 0.0)))

    # Sternum & 6 Rib Pairs on front (-Y)
    parts.append(make_box("SternumBar", (0.0, -0.12, 1.28), (0.065, 0.04, 0.34), mat_trim if not exposed_ribs else mats["AgedBone"]))
    for r_idx in range(6):
        rz = 1.08 + r_idx * 0.062
        rw = 0.16 + math.sin((r_idx / 5.0) * math.pi) * 0.05
        for side_i, sx in enumerate((-1.0, 1.0)):
            parts.append(
                make_box(
                    f"RibArc_{r_idx}_{side_i}",
                    (sx * rw, -0.02, rz),
                    (0.14, 0.19, 0.026),
                    mats["AgedBone"] if exposed_ribs else mat_cuirass,
                    (0.0, 0.0, sx * math.radians(18.0)),
                )
            )

    if not exposed_ribs:
        parts.append(make_box("BreastplateCore", (0.0, -0.02, 1.28), (0.38, 0.24, 0.38), mat_cuirass))
        parts.append(make_box("GorgetCollar", (0.0, -0.01, 1.50), (0.28, 0.22, 0.08), mat_trim))

    # Glowing runic heart / core
    parts.append(make_sphere("ChestRunicHeart", (0.0, -0.09, 1.30), 0.062, mat_glow))

    # Shoulder Pauldrons (3 overlapping lames + spike per side)
    for side_i, sx in enumerate((-1.0, 1.0)):
        for p_idx in range(3):
            pz = 1.48 - p_idx * 0.045
            parts.append(
                make_box(
                    f"PauldronLame_{side_i}_{p_idx}",
                    (sx * (0.26 + p_idx * 0.02), 0.0, pz),
                    (0.16, 0.22, 0.055),
                    mat_cuirass,
                    (0.0, sx * math.radians(18.0 + p_idx * 8.0), 0.0),
                )
            )
        parts.append(make_cone(f"PauldronSpike_{side_i}", (sx * 0.29, 0.0, 1.55), 0.032, 0.003, 0.11, mat_trim, (0.0, sx * math.radians(22.0), 0.0)))

    # Chest rivet lines
    riv_pts = [
        (-0.14, -0.14, 1.16), (0.14, -0.14, 1.16),
        (-0.16, -0.14, 1.28), (0.16, -0.14, 1.28),
        (-0.14, -0.14, 1.40), (0.14, -0.14, 1.40),
    ]
    parts.extend(spawn_rivet_cluster("Torso", riv_pts, 0.014, mat_trim))
    return parts


def build_gothic_skull_or_helm_head(
    mats: dict[str, bpy.types.Material],
    mat_helm: bpy.types.Material,
    mat_trim: bpy.types.Material,
    mat_eyes: bpy.types.Material,
    horn_pairs: int = 1,
    visor_slits: int = 4,
) -> list[bpy.types.Object]:
    parts: list[bpy.types.Object] = []
    # Neck column, cranium dome, brow ridge, mandible
    parts.append(make_cyl("NeckCol", (0.0, 0.01, 1.58), 0.058, 0.10, mats["WroughtIron"]))
    parts.append(make_sphere("CraniumDome", (0.0, 0.0, 1.69), 0.115, mat_helm, (0.92, 1.08, 1.05)))
    parts.append(make_box("BrowRidge", (0.0, -0.095, 1.71), (0.16, 0.06, 0.035), mat_trim))
    parts.append(make_box("JawMandible", (0.0, -0.055, 1.59), (0.12, 0.11, 0.065), mat_helm))

    # Glowing eyes on front (-Y)
    for side_i, sx in enumerate((-1.0, 1.0)):
        parts.append(make_sphere(f"GlowingEye_{side_i}", (sx * 0.042, -0.105, 1.675), 0.022, mat_eyes))
        parts.append(make_box(f"CheekPlate_{side_i}", (sx * 0.085, -0.06, 1.63), (0.035, 0.09, 0.075), mat_trim))

    for v_idx in range(visor_slits):
        vx = -0.045 + (v_idx / max(1, visor_slits - 1)) * 0.09
        parts.append(make_box(f"VisorBar_{v_idx}", (vx, -0.112, 1.615), (0.012, 0.022, 0.065), mat_trim))

    parts.append(make_torus("CrownBand", (0.0, 0.0, 1.74), 0.108, 0.014, mat_trim))
    for h_idx in range(horn_pairs):
        hz = 1.74 + h_idx * 0.035
        for side_i, sx in enumerate((-1.0, 1.0)):
            parts.append(
                make_cone(
                    f"HelmHorn_{h_idx}_{side_i}",
                    (sx * (0.11 + h_idx * 0.03), 0.02, hz + 0.06),
                    0.028,
                    0.003,
                    0.18,
                    mat_trim,
                    (math.radians(18.0), sx * math.radians(28.0 + h_idx * 14.0), 0.0),
                )
            )
    return parts


def build_articulated_arm_pair(
    prefix: str,
    side_sign: float,
    mats: dict[str, bpy.types.Material],
    mat_armor: bpy.types.Material,
    mat_trim: bpy.types.Material,
) -> tuple[list[bpy.types.Object], list[bpy.types.Object]]:
    upper_parts: list[bpy.types.Object] = []
    forearm_parts: list[bpy.types.Object] = []
    ax = side_sign * 0.30

    # Upper arm
    upper_parts.append(make_sphere(f"{prefix}_ShoulderJoint", (ax, 0.0, 1.46), 0.058, mat_trim))
    upper_parts.append(make_cyl(f"{prefix}_UpperArm", (ax, -0.02, 1.34), 0.056, 0.24, mat_armor, (math.radians(-12.0), 0.0, 0.0)))
    for l_i in range(2):
        upper_parts.append(make_torus(f"{prefix}_ArmBand_{l_i}", (ax, -0.01 - l_i * 0.02, 1.38 - l_i * 0.08), 0.060, 0.009, mat_trim, (math.radians(-12.0), 0.0, 0.0)))

    # Forearm
    forearm_parts.append(make_sphere(f"{prefix}_ElbowCouter", (ax, -0.04, 1.21), 0.058, mat_trim))
    forearm_parts.append(make_cone(f"{prefix}_ElbowSpike", (ax + side_sign * 0.05, -0.02, 1.21), 0.020, 0.002, 0.065, mat_trim, (0.0, side_sign * math.radians(90.0), 0.0)))
    forearm_parts.append(make_cyl(f"{prefix}_Forearm", (ax, -0.17, 1.15), 0.050, 0.26, mat_armor, (math.radians(-68.0), 0.0, 0.0)))
    for s_i in range(2):
        forearm_parts.append(make_torus(f"{prefix}_VambraceRing_{s_i}", (ax, -0.12 - s_i * 0.09, 1.17 - s_i * 0.04), 0.053, 0.008, mat_trim, (math.radians(-68.0), 0.0, 0.0)))
    forearm_parts.append(make_box(f"{prefix}_HandFist", (ax, -0.30, 1.10), (0.085, 0.095, 0.075), mat_trim))
    for f_i in range(4):
        fx = ax - 0.03 + f_i * 0.02
        forearm_parts.append(make_box(f"{prefix}_Finger_{f_i}", (fx, -0.35, 1.09), (0.016, 0.045, 0.042), mat_armor))

    return upper_parts, forearm_parts


# ==============================================================================
# COMMON ENEMY BUILDERS (Skeleton, Acolyte, Penitent)
# ==============================================================================

def build_enemy_ossuary_skeleton() -> int:
    clear_scene()
    mats = create_enemy_palette()

    pelvis_parts, thigh_l, shin_l, thigh_r, shin_r = build_articulated_legs_and_pelvis(
        mats, mats["AgedBone"], mats["WroughtIron"], mats["AgedBone"], include_tassets=True, robe_skirt=False
    )
    torso_parts = build_ribcage_and_cuirass_torso(
        mats, mats["AgedBone"], mats["WroughtIron"], mats["EmissiveAmberFlame"], exposed_ribs=True
    )
    for sx_i, sx in enumerate((-1.0, 1.0)):
        torso_parts.append(make_sphere(f"SkelPaulSkull_{sx_i}", (sx * 0.28, -0.05, 1.51), 0.055, mats["AgedBone"]))
        torso_parts.append(make_sphere(f"SkelPaulEye_{sx_i}", (sx * 0.30, -0.09, 1.51), 0.014, mats["EmissiveAmberFlame"]))

    # SecondaryProp: Dorsal Bone Spurs along the Spine
    sec_parts: list[bpy.types.Object] = []
    for sp_i in range(5):
        sz = 1.15 + sp_i * 0.08
        sec_parts.append(make_cone(f"SpineBoneSpur_{sp_i}", (0.0, 0.16, sz), 0.024, 0.003, 0.14, mats["AgedBone"], (math.radians(-70.0), 0.0, 0.0)))
    sec_parts.extend(spawn_chain_strand("SkelBackChain", (0.0, 0.12, 1.48), 5, (0.0, 0.0, -0.06), 0.022, 0.005, mats["WroughtIron"]))

    head_parts = build_gothic_skull_or_helm_head(
        mats, mats["AgedBone"], mats["WroughtIron"], mats["EmissiveAmberFlame"], horn_pairs=1, visor_slits=4
    )

    uarm_l, farm_l = build_articulated_arm_pair("SkelL", -1.0, mats, mats["AgedBone"], mats["WroughtIron"])
    uarm_r, farm_r = build_articulated_arm_pair("SkelR", 1.0, mats, mats["AgedBone"], mats["WroughtIron"])

    # ForearmL: Bone Buckler Shield
    farm_l.append(make_sphere("SkelBucklerBoss", (-0.30, -0.36, 1.14), 0.105, mats["AgedBone"]))
    farm_l.append(make_torus("SkelBucklerRim", (-0.30, -0.36, 1.14), 0.115, 0.014, mats["WroughtIron"], (math.radians(90.0), 0.0, 0.0)))
    farm_l.append(make_cone("SkelBucklerSpike", (-0.30, -0.46, 1.14), 0.025, 0.003, 0.085, mats["WroughtIron"], (math.radians(90.0), 0.0, 0.0)))

    # ForearmR: Notched Bone Executioner Cleaver
    rx = 0.30
    farm_r.append(make_cyl("SkelCleaverHilt", (rx, -0.31, 1.12), 0.020, 0.32, mats["WeatheredLeather"]))
    farm_r.append(make_sphere("SkelCleaverPommel", (rx, -0.31, 0.94), 0.032, mats["TarnishedBronze"]))
    farm_r.append(make_box("SkelCleaverGuard", (rx, -0.31, 1.24), (0.04, 0.16, 0.035), mats["WroughtIron"]))
    farm_r.append(make_box("SkelCleaverBlade", (rx, -0.40, 1.54), (0.022, 0.16, 0.54), mats["SilveredSteel"]))
    farm_r.append(make_box("SkelCleaverRune", (rx, -0.37, 1.52), (0.026, 0.025, 0.40), mats["EmissiveAmberFlame"]))
    for n_i in range(3):
        nz = 1.38 + n_i * 0.11
        farm_r.append(make_cone(f"SkelCleaverSaw_{n_i}", (rx, -0.49, nz), 0.018, 0.002, 0.055, mats["AgedBone"], (math.radians(90.0), 0.0, 0.0)))

    return export_articulated_enemy_glb(
        "enemy_ossuary_skeleton.glb",
        pelvis_parts, thigh_l, shin_l, thigh_r, shin_r,
        torso_parts, head_parts, uarm_l, farm_l, uarm_r, farm_r, sec_parts
    )


def build_enemy_plague_acolyte() -> int:
    clear_scene()
    mats = create_enemy_palette()

    pelvis_parts, thigh_l, shin_l, thigh_r, shin_r = build_articulated_legs_and_pelvis(
        mats, mats["WeatheredLeather"], mats["TarnishedBronze"], mats["RottedTimber"], include_tassets=True, robe_skirt=True
    )
    torso_parts = build_ribcage_and_cuirass_torso(
        mats, mats["WeatheredLeather"], mats["TarnishedBronze"], mats["SicklyGreenBile"], exposed_ribs=False
    )

    # SecondaryProp: 3 Alchemical Distill Vials on Back
    sec_parts: list[bpy.types.Object] = []
    sec_parts.append(make_box("VialHarnessBack", (0.0, 0.14, 1.34), (0.28, 0.05, 0.12), mats["WeatheredLeather"]))
    for v_i in range(3):
        vx = -0.09 + v_i * 0.09
        sec_parts.append(make_cyl(f"PlagueFlask_{v_i}", (vx, 0.18, 1.34), 0.028, 0.18, mats["SicklyGreenBile"]))
        sec_parts.append(make_sphere(f"FlaskStopper_{v_i}", (vx, 0.18, 1.44), 0.018, mats["TarnishedBronze"]))

    head_parts = build_gothic_skull_or_helm_head(
        mats, mats["WeatheredLeather"], mats["TarnishedBronze"], mats["SicklyGreenBile"], horn_pairs=0, visor_slits=3
    )
    # Plague Doctor Bird-Beak Mask & Goggles
    head_parts.append(make_cone("AcolyteBeak", (0.0, -0.21, 1.63), 0.062, 0.007, 0.24, mats["TarnishedBronze"], (math.radians(78.0), 0.0, 0.0)))
    for sx_i, sx in enumerate((-1.0, 1.0)):
        head_parts.append(make_torus(f"AcolyteGoggle_{sx_i}", (sx * 0.045, -0.11, 1.68), 0.028, 0.007, mats["TarnishedBronze"], (math.radians(90.0), 0.0, 0.0)))

    uarm_l, farm_l = build_articulated_arm_pair("AcolyteL", -1.0, mats, mats["WeatheredLeather"], mats["TarnishedBronze"])
    uarm_r, farm_r = build_articulated_arm_pair("AcolyteR", 1.0, mats, mats["WeatheredLeather"], mats["TarnishedBronze"])

    # ForearmL: Alchemical Poison Flask Focus
    farm_l.append(make_sphere("AcolyteFlaskBody", (-0.30, -0.38, 1.10), 0.065, mats["SicklyGreenBile"]))
    farm_l.append(make_cyl("AcolyteFlaskNeck", (-0.30, -0.38, 1.18), 0.022, 0.08, mats["TarnishedBronze"]))

    # ForearmR: Toxic Censer Flail
    rx = 0.30
    farm_r.append(make_cyl("AcolyteCenserRod", (rx, -0.34, 1.22), 0.018, 0.72, mats["TarnishedBronze"]))
    farm_r.extend(spawn_chain_strand("AcolyteChain", (rx, -0.34, 1.56), 5, (0.0, -0.03, -0.055), 0.024, 0.006, mats["TarnishedBronze"]))
    c_pos = (rx, -0.49, 1.24)
    farm_r.append(make_sphere("AcolyteBrazier", c_pos, 0.092, mats["SicklyGreenBile"]))
    farm_r.append(make_torus("AcolyteBrazierRing", c_pos, 0.102, 0.014, mats["TarnishedBronze"]))
    farm_r.append(make_torus("AcolyteBrazierRing2", c_pos, 0.102, 0.014, mats["TarnishedBronze"], (math.radians(90.0), 0.0, 0.0)))

    return export_articulated_enemy_glb(
        "enemy_plague_acolyte.glb",
        pelvis_parts, thigh_l, shin_l, thigh_r, shin_r,
        torso_parts, head_parts, uarm_l, farm_l, uarm_r, farm_r, sec_parts
    )


def build_enemy_iron_penitent() -> int:
    clear_scene()
    mats = create_enemy_palette()

    pelvis_parts, thigh_l, shin_l, thigh_r, shin_r = build_articulated_legs_and_pelvis(
        mats, mats["WroughtIron"], mats["GothicPlateSteel"], mats["WeatheredLeather"], include_tassets=True, robe_skirt=False
    )
    torso_parts = build_ribcage_and_cuirass_torso(
        mats, mats["WroughtIron"], mats["GothicPlateSteel"], mats["AbyssalCrimson"], exposed_ribs=False
    )
    sec_parts: list[bpy.types.Object] = []
    # Penitent cross and heavy hanging back chains
    sec_parts.append(make_box("PenitentCrossVert", (0.0, 0.14, 1.48), (0.06, 0.05, 0.46), mats["WroughtIron"]))
    sec_parts.append(make_box("PenitentCrossHoriz", (0.0, 0.14, 1.56), (0.28, 0.05, 0.06), mats["WroughtIron"]))
    sec_parts.extend(spawn_chain_strand("PenitentChainL", (-0.12, 0.14, 1.48), 6, (0.0, 0.0, -0.055), 0.026, 0.007, mats["WroughtIron"]))
    sec_parts.extend(spawn_chain_strand("PenitentChainR", (0.12, 0.14, 1.48), 6, (0.0, 0.0, -0.055), 0.026, 0.007, mats["WroughtIron"]))

    # Spiked Iron Penitent Cage Helmet
    head_parts = build_gothic_skull_or_helm_head(
        mats, mats["WroughtIron"], mats["GothicPlateSteel"], mats["AbyssalCrimson"], horn_pairs=1, visor_slits=4
    )
    head_parts.append(make_torus("PenitentHoopBot", (0.0, 0.0, 1.56), 0.140, 0.014, mats["WroughtIron"]))
    head_parts.append(make_torus("PenitentHoopTop", (0.0, 0.0, 1.84), 0.135, 0.014, mats["WroughtIron"]))
    for b_i in range(6):
        ang = (b_i / 6.0) * math.tau
        bx = math.cos(ang) * 0.140
        by = math.sin(ang) * 0.140
        head_parts.append(make_cyl(f"PenitentBar_{b_i}", (bx, by, 1.70), 0.009, 0.30, mats["WroughtIron"]))
        head_parts.append(make_cone(f"PenitentBarSpike_{b_i}", (bx, by, 1.88), 0.015, 0.002, 0.065, mats["GothicPlateSteel"]))

    uarm_l, farm_l = build_articulated_arm_pair("PenitentL", -1.0, mats, mats["WroughtIron"], mats["GothicPlateSteel"])
    uarm_r, farm_r = build_articulated_arm_pair("PenitentR", 1.0, mats, mats["WroughtIron"], mats["GothicPlateSteel"])

    # ForearmL: Manacled Fist & Broken Shackle Chains
    farm_l.append(make_torus("PenitentManacle", (-0.30, -0.26, 1.12), 0.065, 0.015, mats["WroughtIron"]))
    farm_l.extend(spawn_chain_strand("ManacleChain", (-0.30, -0.26, 1.06), 4, (0.0, 0.0, -0.05), 0.024, 0.006, mats["WroughtIron"]))

    # ForearmR: Heavy Spiked Morningstar Flail
    rx = 0.32
    farm_r.append(make_cyl("PenitentFlailShaft", (rx, -0.32, 1.28), 0.024, 0.90, mats["RottedTimber"]))
    farm_r.extend(spawn_chain_strand("PenitentFlailChain", (rx, -0.34, 1.72), 5, (0.0, -0.04, -0.05), 0.028, 0.008, mats["WroughtIron"]))
    ball_pos = (rx, -0.54, 1.46)
    farm_r.append(make_sphere("PenitentBall", ball_pos, 0.110, mats["WroughtIron"]))
    farm_r.append(make_sphere("PenitentBallGlow", ball_pos, 0.090, mats["AbyssalCrimson"]))
    for sp_i in range(10):
        phi = (sp_i / 10.0) * math.tau
        z_tilt = ((sp_i % 3) - 1) * 0.45
        spx = ball_pos[0] + math.cos(phi) * 0.12
        spy = ball_pos[1] + math.sin(phi) * 0.12
        spz = ball_pos[2] + z_tilt * 0.10
        farm_r.append(make_cone(f"PenitentSpike_{sp_i}", (spx, spy, spz), 0.024, 0.002, 0.090, mats["SilveredSteel"], (z_tilt, math.sin(phi), -math.cos(phi))))

    return export_articulated_enemy_glb(
        "enemy_iron_penitent.glb",
        pelvis_parts, thigh_l, shin_l, thigh_r, shin_r,
        torso_parts, head_parts, uarm_l, farm_l, uarm_r, farm_r, sec_parts
    )


# ==============================================================================
# BIOME 1–4 ENEMY BUILDERS
# ==============================================================================

def build_enemy_01_ossuary_executioner() -> int:
    clear_scene()
    mats = create_enemy_palette()

    pelvis_parts, thigh_l, shin_l, thigh_r, shin_r = build_articulated_legs_and_pelvis(
        mats, mats["WroughtIron"], mats["TarnishedBronze"], mats["AgedBone"], include_tassets=True, robe_skirt=False
    )
    torso_parts = build_ribcage_and_cuirass_torso(
        mats, mats["WroughtIron"], mats["TarnishedBronze"], mats["EmissiveAmberFlame"], exposed_ribs=True
    )
    for sx_i, sx in enumerate((-1.0, 1.0)):
        torso_parts.append(make_sphere(f"PauldronSkull_{sx_i}", (sx * 0.28, -0.06, 1.52), 0.055, mats["AgedBone"]))
        torso_parts.append(make_sphere(f"PauldronSkullEye_{sx_i}", (sx * 0.30, -0.10, 1.52), 0.014, mats["EmissiveAmberFlame"]))

    # SecondaryProp: Hanging Iron Chains & Executioner Trophy Rack on Chest/Back
    sec_parts: list[bpy.types.Object] = []
    sec_parts.extend(spawn_chain_strand("ExecFrontChainL", (-0.12, -0.14, 1.42), 7, (0.02, 0.0, -0.045), 0.024, 0.006, mats["WroughtIron"]))
    sec_parts.extend(spawn_chain_strand("ExecFrontChainR", (0.12, -0.14, 1.42), 7, (-0.02, 0.0, -0.045), 0.024, 0.006, mats["WroughtIron"]))

    head_parts = build_gothic_skull_or_helm_head(
        mats, mats["AgedBone"], mats["WroughtIron"], mats["EmissiveAmberFlame"], horn_pairs=1, visor_slits=5
    )

    uarm_l, farm_l = build_articulated_arm_pair("ExecL", -1.0, mats, mats["WroughtIron"], mats["TarnishedBronze"])
    uarm_r, farm_r = build_articulated_arm_pair("ExecR", 1.0, mats, mats["WroughtIron"], mats["TarnishedBronze"])

    # Dual Notched Bone-Cleaver Blades in both hands
    for arm_list, side_s, prefix in ((farm_l, -1.0, "CleaverL"), (farm_r, 1.0, "CleaverR")):
        hx = side_s * 0.30
        arm_list.append(make_cyl(f"{prefix}_Hilt", (hx, -0.31, 1.12), 0.020, 0.34, mats["WeatheredLeather"]))
        arm_list.append(make_sphere(f"{prefix}_Pommel", (hx, -0.31, 0.94), 0.032, mats["TarnishedBronze"]))
        arm_list.append(make_box(f"{prefix}_Crossguard", (hx, -0.31, 1.24), (0.04, 0.18, 0.035), mats["WroughtIron"]))
        arm_list.append(make_box(f"{prefix}_BladeMain", (hx, -0.40, 1.56), (0.022, 0.16, 0.58), mats["SilveredSteel"]))
        arm_list.append(make_box(f"{prefix}_BladeRune", (hx, -0.37, 1.54), (0.026, 0.025, 0.44), mats["EmissiveAmberFlame"]))
        for n_i in range(4):
            nz = 1.36 + n_i * 0.11
            arm_list.append(make_cone(f"{prefix}_SawTooth_{n_i}", (hx, -0.49, nz), 0.018, 0.002, 0.055, mats["AgedBone"], (math.radians(90.0), 0.0, 0.0)))

    return export_articulated_enemy_glb(
        "enemy_01_ossuary_executioner.glb",
        pelvis_parts, thigh_l, shin_l, thigh_r, shin_r,
        torso_parts, head_parts, uarm_l, farm_l, uarm_r, farm_r, sec_parts
    )


def build_enemy_02_necropolis_praetorian() -> int:
    clear_scene()
    mats = create_enemy_palette()

    pelvis_parts, thigh_l, shin_l, thigh_r, shin_r = build_articulated_legs_and_pelvis(
        mats, mats["GothicPlateSteel"], mats["TarnishedBronze"], mats["WeatheredLeather"], include_tassets=True, robe_skirt=True
    )
    torso_parts = build_ribcage_and_cuirass_torso(
        mats, mats["GothicPlateSteel"], mats["TarnishedBronze"], mats["EmissiveAmberFlame"], exposed_ribs=False
    )
    # SecondaryProp: Royal Necropolis Sun-Crest Halo on Back of Torso
    sec_parts: list[bpy.types.Object] = []
    sec_parts.append(make_torus("RoyalSunHalo", (0.0, 0.06, 1.62), 0.24, 0.016, mats["TarnishedBronze"], (math.radians(90.0), 0.0, 0.0)))
    for r_i in range(8):
        ang = (r_i / 8.0) * math.pi
        rx = math.cos(ang) * 0.28
        rz = 1.62 + math.sin(ang) * 0.28
        sec_parts.append(make_cone(f"HaloSpoke_{r_i}", (rx, 0.06, rz), 0.016, 0.002, 0.09, mats["TarnishedBronze"], (0.0, math.radians(90.0) - ang, 0.0)))

    head_parts = build_gothic_skull_or_helm_head(
        mats, mats["TarnishedBronze"], mats["GothicPlateSteel"], mats["EmissiveAmberFlame"], horn_pairs=2, visor_slits=6
    )
    for p_i in range(6):
        py = -0.06 + p_i * 0.03
        pz = 1.84 + math.sin((p_i / 5.0) * math.pi) * 0.06
        head_parts.append(make_box(f"HelmPlume_{p_i}", (0.0, py, pz), (0.035, 0.045, 0.14), mats["AbyssalCrimson"]))

    uarm_l, farm_l = build_articulated_arm_pair("PraetL", -1.0, mats, mats["GothicPlateSteel"], mats["TarnishedBronze"])
    uarm_r, farm_r = build_articulated_arm_pair("PraetR", 1.0, mats, mats["GothicPlateSteel"], mats["TarnishedBronze"])

    # ForearmL: Carved Sarcophagus-Lid Greatshield
    sx = -0.34
    farm_l.append(make_box("ShieldSlab", (sx, -0.36, 1.12), (0.06, 0.56, 1.18), mats["WeatheredStone"], (0.0, 0.0, math.radians(22.0))))
    farm_l.append(make_box("ShieldRimTop", (sx - 0.02, -0.36, 1.71), (0.08, 0.60, 0.06), mats["TarnishedBronze"], (0.0, 0.0, math.radians(22.0))))
    farm_l.append(make_box("ShieldRimBot", (sx - 0.02, -0.36, 0.53), (0.08, 0.60, 0.06), mats["TarnishedBronze"], (0.0, 0.0, math.radians(22.0))))
    farm_l.append(make_box("ShieldCrossVert", (sx - 0.035, -0.38, 1.12), (0.03, 0.09, 1.04), mats["TarnishedBronze"]))
    farm_l.append(make_box("ShieldCrossHoriz", (sx - 0.035, -0.38, 1.24), (0.03, 0.48, 0.09), mats["TarnishedBronze"]))
    farm_l.append(make_sphere("ShieldCenterBoss", (sx - 0.05, -0.40, 1.24), 0.075, mats["EmissiveAmberFlame"]))
    for sr_i in range(8):
        sz = 0.62 + (sr_i % 4) * 0.32
        sy = -0.18 if sr_i < 4 else -0.54
        farm_l.append(make_sphere(f"ShieldStud_{sr_i}", (sx - 0.04, sy, sz), 0.022, mats["TarnishedBronze"]))

    # ForearmR: Flanged Royal Halberd
    rx = 0.32
    farm_r.append(make_cyl("HalberdShaft", (rx, -0.32, 1.25), 0.022, 1.95, mats["RottedTimber"]))
    for b_i in range(5):
        farm_r.append(make_torus(f"ShaftBand_{b_i}", (rx, -0.32, 0.55 + b_i * 0.34), 0.026, 0.006, mats["TarnishedBronze"]))
    farm_r.append(make_cone("HalberdTopPike", (rx, -0.32, 2.34), 0.028, 0.002, 0.36, mats["SilveredSteel"]))
    farm_r.append(make_box("HalberdAxeBlade", (rx, -0.48, 1.98), (0.022, 0.28, 0.42), mats["SilveredSteel"]))
    farm_r.append(make_box("HalberdRuneInlay", (rx, -0.42, 1.98), (0.026, 0.04, 0.32), mats["EmissiveAmberFlame"]))
    farm_r.append(make_cone("HalberdBackFluke", (rx, -0.16, 1.98), 0.032, 0.003, 0.22, mats["TarnishedBronze"], (math.radians(-90.0), 0.0, 0.0)))

    return export_articulated_enemy_glb(
        "enemy_02_necropolis_praetorian.glb",
        pelvis_parts, thigh_l, shin_l, thigh_r, shin_r,
        torso_parts, head_parts, uarm_l, farm_l, uarm_r, farm_r, sec_parts
    )


def build_enemy_03_reliquary_hexweaver() -> int:
    clear_scene()
    mats = create_enemy_palette()

    pelvis_parts, thigh_l, shin_l, thigh_r, shin_r = build_articulated_legs_and_pelvis(
        mats, mats["WeatheredLeather"], mats["TarnishedBronze"], mats["WeatheredLeather"], include_tassets=True, robe_skirt=True
    )
    torso_parts = build_ribcage_and_cuirass_torso(
        mats, mats["WeatheredLeather"], mats["TarnishedBronze"], mats["GlowingOccultRune"], exposed_ribs=False
    )
    for sc_i in range(6):
        ang = (sc_i / 6.0) * math.pi - math.pi * 0.5
        torso_parts.append(make_cyl(f"ScrollTube_{sc_i}", (math.sin(ang) * 0.22, 0.14, 1.15 + (sc_i % 2) * 0.12), 0.028, 0.24, mats["TarnishedBronze"], (0.0, math.radians(25.0), 0.0)))

    # SecondaryProp: Brass Astrolabe Halo & 3 Orbiting Open Grimoires
    sec_parts: list[bpy.types.Object] = []
    sec_parts.append(make_torus("AstrolabeOuter", (0.0, 0.10, 1.66), 0.32, 0.016, mats["TarnishedBronze"], (math.radians(90.0), 0.0, 0.0)))
    sec_parts.append(make_torus("AstrolabeInner", (0.0, 0.10, 1.66), 0.22, 0.012, mats["GlowingOccultRune"], (math.radians(72.0), math.radians(24.0), 0.0)))
    for g_idx, (gx, gy, gz) in enumerate((
        (-0.42, -0.28, 1.32),
        (0.0, -0.44, 1.42),
        (0.42, -0.28, 1.32),
    )):
        sec_parts.append(make_box(f"GrimoireCoverL_{g_idx}", (gx - 0.04, gy, gz), (0.09, 0.14, 0.016), mats["WeatheredLeather"], (0.0, math.radians(-20.0), 0.0)))
        sec_parts.append(make_box(f"GrimoireCoverR_{g_idx}", (gx + 0.04, gy, gz), (0.09, 0.14, 0.016), mats["WeatheredLeather"], (0.0, math.radians(20.0), 0.0)))
        sec_parts.append(make_box(f"GrimoirePagesL_{g_idx}", (gx - 0.035, gy, gz + 0.014), (0.08, 0.13, 0.018), mats["AgedBone"], (0.0, math.radians(-16.0), 0.0)))
        sec_parts.append(make_box(f"GrimoirePagesR_{g_idx}", (gx + 0.035, gy, gz + 0.014), (0.08, 0.13, 0.018), mats["AgedBone"], (0.0, math.radians(16.0), 0.0)))
        sec_parts.append(make_sphere(f"GrimoireOrb_{g_idx}", (gx, gy, gz + 0.06), 0.032, mats["GlowingOccultRune"]))

    head_parts = build_gothic_skull_or_helm_head(
        mats, mats["AgedBone"], mats["TarnishedBronze"], mats["GlowingOccultRune"], horn_pairs=1, visor_slits=3
    )
    head_parts.append(make_cone("ScholarCowlPeak", (0.0, 0.04, 1.84), 0.14, 0.01, 0.26, mats["WeatheredLeather"], (math.radians(22.0), 0.0, 0.0)))

    uarm_l, farm_l = build_articulated_arm_pair("HexL", -1.0, mats, mats["WeatheredLeather"], mats["TarnishedBronze"])
    uarm_r, farm_r = build_articulated_arm_pair("HexR", 1.0, mats, mats["WeatheredLeather"], mats["TarnishedBronze"])

    # ForearmR: Glowing Hex Staff
    farm_r.append(make_cyl("HexStaffShaft", (0.30, -0.32, 1.15), 0.018, 1.65, mats["WroughtIron"]))
    farm_r.append(make_torus("HexStaffRing", (0.30, -0.32, 2.02), 0.095, 0.014, mats["TarnishedBronze"], (math.radians(90.0), 0.0, 0.0)))
    farm_r.append(make_sphere("HexStaffCore", (0.30, -0.32, 2.02), 0.052, mats["GlowingOccultRune"]))

    return export_articulated_enemy_glb(
        "enemy_03_reliquary_hexweaver.glb",
        pelvis_parts, thigh_l, shin_l, thigh_r, shin_r,
        torso_parts, head_parts, uarm_l, farm_l, uarm_r, farm_r, sec_parts
    )


def build_enemy_04_inquisitor_rackmaster() -> int:
    clear_scene()
    mats = create_enemy_palette()

    pelvis_parts, thigh_l, shin_l, thigh_r, shin_r = build_articulated_legs_and_pelvis(
        mats, mats["WroughtIron"], mats["GothicPlateSteel"], mats["WeatheredLeather"], include_tassets=True, robe_skirt=False
    )
    torso_parts = build_ribcage_and_cuirass_torso(
        mats, mats["WeatheredLeather"], mats["WroughtIron"], mats["EmissiveAmberFlame"], exposed_ribs=False
    )
    sec_parts: list[bpy.types.Object] = []
    sec_parts.extend(spawn_chain_strand("RackTorsoChainL", (-0.18, -0.14, 1.44), 6, (0.0, 0.0, -0.055), 0.028, 0.007, mats["WroughtIron"]))
    sec_parts.extend(spawn_chain_strand("RackTorsoChainR", (0.18, -0.14, 1.44), 6, (0.0, 0.0, -0.055), 0.028, 0.007, mats["WroughtIron"]))

    # Head inside a Spiked Iron Gibbet Cage
    head_parts = build_gothic_skull_or_helm_head(
        mats, mats["WroughtIron"], mats["GothicPlateSteel"], mats["EmissiveAmberFlame"], horn_pairs=1, visor_slits=4
    )
    head_parts.append(make_torus("GibbetHoopBot", (0.0, 0.0, 1.56), 0.145, 0.015, mats["WroughtIron"]))
    head_parts.append(make_torus("GibbetHoopMid", (0.0, 0.0, 1.72), 0.150, 0.015, mats["WroughtIron"]))
    head_parts.append(make_torus("GibbetHoopTop", (0.0, 0.0, 1.88), 0.140, 0.015, mats["WroughtIron"]))
    for b_i in range(6):
        ang = (b_i / 6.0) * math.tau
        bx = math.cos(ang) * 0.145
        by = math.sin(ang) * 0.145
        head_parts.append(make_cyl(f"GibbetBar_{b_i}", (bx, by, 1.72), 0.010, 0.34, mats["WroughtIron"]))
        head_parts.append(make_cone(f"GibbetTopSpike_{b_i}", (bx, by, 1.92), 0.016, 0.002, 0.07, mats["GothicPlateSteel"]))

    uarm_l, farm_l = build_articulated_arm_pair("RackL", -1.0, mats, mats["WroughtIron"], mats["GothicPlateSteel"])
    uarm_r, farm_r = build_articulated_arm_pair("RackR", 1.0, mats, mats["WroughtIron"], mats["GothicPlateSteel"])

    # ForearmL: Torturer's Catch-Hook & Manacles
    farm_l.append(make_cyl("HookShaft", (-0.30, -0.36, 1.15), 0.020, 0.72, mats["WroughtIron"], (math.radians(-45.0), 0.0, 0.0)))
    farm_l.append(make_torus("HookCurve", (-0.30, -0.62, 1.38), 0.085, 0.018, mats["SilveredSteel"], (0.0, math.radians(90.0), 0.0)))
    farm_l.append(make_cone("HookBarb", (-0.30, -0.70, 1.38), 0.024, 0.002, 0.09, mats["SilveredSteel"], (math.radians(120.0), 0.0, 0.0)))

    # ForearmR: Spiked Wrought-Iron Flail
    rx = 0.32
    farm_r.append(make_cyl("FlailShaft", (rx, -0.32, 1.28), 0.024, 0.92, mats["RottedTimber"]))
    farm_r.extend(spawn_chain_strand("FlailChain", (rx, -0.34, 1.74), 5, (0.0, -0.04, -0.05), 0.028, 0.008, mats["WroughtIron"]))
    ball_pos = (rx, -0.54, 1.46)
    farm_r.append(make_sphere("FlailMorningstarBall", ball_pos, 0.115, mats["WroughtIron"]))
    farm_r.append(make_sphere("FlailCoreGlow", ball_pos, 0.095, mats["EmissiveAmberFlame"]))
    for sp_i in range(10):
        phi = (sp_i / 10.0) * math.tau
        z_tilt = ((sp_i % 3) - 1) * 0.45
        spx = ball_pos[0] + math.cos(phi) * 0.12
        spy = ball_pos[1] + math.sin(phi) * 0.12
        spz = ball_pos[2] + z_tilt * 0.10
        farm_r.append(make_cone(f"FlailSpike_{sp_i}", (spx, spy, spz), 0.024, 0.002, 0.095, mats["SilveredSteel"], (z_tilt, math.sin(phi), -math.cos(phi))))

    return export_articulated_enemy_glb(
        "enemy_04_inquisitor_rackmaster.glb",
        pelvis_parts, thigh_l, shin_l, thigh_r, shin_r,
        torso_parts, head_parts, uarm_l, farm_l, uarm_r, farm_r, sec_parts
    )


# ==============================================================================
# BIOME 5–8 ENEMY BUILDERS & MAIN ENTRYPOINT
# ==============================================================================

def build_enemy_05_plague_bloater() -> int:
    clear_scene()
    mats = create_enemy_palette()

    pelvis_parts, thigh_l, shin_l, thigh_r, shin_r = build_articulated_legs_and_pelvis(
        mats, mats["WeatheredLeather"], mats["TarnishedBronze"], mats["WeatheredLeather"], include_tassets=True, robe_skirt=True
    )
    torso_parts = build_ribcage_and_cuirass_torso(
        mats, mats["WeatheredLeather"], mats["TarnishedBronze"], mats["SicklyGreenBile"], exposed_ribs=False
    )
    # SecondaryProp: Pressurized Dorsal Toxic Bile Tank on Back
    sec_parts: list[bpy.types.Object] = []
    sec_parts.append(make_cyl("BileTankCore", (0.0, 0.22, 1.34), 0.165, 0.52, mats["SicklyGreenBile"]))
    sec_parts.append(make_sphere("BileTankDomeTop", (0.0, 0.22, 1.60), 0.165, mats["TarnishedBronze"]))
    sec_parts.append(make_sphere("BileTankDomeBot", (0.0, 0.22, 1.08), 0.165, mats["TarnishedBronze"]))
    for h_i in range(4):
        sec_parts.append(make_torus(f"BileTankHoop_{h_i}", (0.0, 0.22, 1.14 + h_i * 0.13), 0.172, 0.015, mats["WroughtIron"]))
    for v_i in range(4):
        ang = (v_i / 4.0) * math.tau + 0.4
        sec_parts.append(make_cyl(f"BileTankCageRib_{v_i}", (math.cos(ang) * 0.17, 0.22 + math.sin(ang) * 0.17, 1.34), 0.012, 0.50, mats["WroughtIron"]))
    for sx_i, sx in enumerate((-1.0, 1.0)):
        sec_parts.append(make_torus(f"DistillPipe_{sx_i}", (sx * 0.16, 0.06, 1.56), 0.11, 0.018, mats["TarnishedBronze"], (0.0, math.radians(90.0), 0.0)))

    head_parts = build_gothic_skull_or_helm_head(
        mats, mats["WeatheredLeather"], mats["TarnishedBronze"], mats["SicklyGreenBile"], horn_pairs=0, visor_slits=3
    )
    head_parts.append(make_cone("PlagueBirdBeak", (0.0, -0.22, 1.63), 0.068, 0.008, 0.26, mats["TarnishedBronze"], (math.radians(78.0), 0.0, 0.0)))
    for sx_i, sx in enumerate((-1.0, 1.0)):
        head_parts.append(make_torus(f"PlagueGoggleRim_{sx_i}", (sx * 0.045, -0.11, 1.68), 0.030, 0.007, mats["TarnishedBronze"], (math.radians(90.0), 0.0, 0.0)))

    uarm_l, farm_l = build_articulated_arm_pair("PlagueL", -1.0, mats, mats["WeatheredLeather"], mats["TarnishedBronze"])
    uarm_r, farm_r = build_articulated_arm_pair("PlagueR", 1.0, mats, mats["WeatheredLeather"], mats["TarnishedBronze"])

    # ForearmL: Bile Sprayer Nozzle
    farm_l.append(make_cyl("BileSprayerBody", (-0.30, -0.40, 1.12), 0.042, 0.32, mats["SicklyGreenBile"], (math.radians(90.0), 0.0, 0.0)))
    farm_l.append(make_cone("BileSprayerNozzle", (-0.30, -0.62, 1.12), 0.028, 0.006, 0.16, mats["TarnishedBronze"], (math.radians(90.0), 0.0, 0.0)))

    # ForearmR: Toxic Censer Flail
    rx = 0.30
    farm_r.append(make_cyl("CenserRod", (rx, -0.34, 1.22), 0.018, 0.72, mats["TarnishedBronze"]))
    farm_r.extend(spawn_chain_strand("CenserChain", (rx, -0.34, 1.56), 5, (0.0, -0.03, -0.055), 0.024, 0.006, mats["TarnishedBronze"]))
    c_pos = (rx, -0.49, 1.24)
    farm_r.append(make_sphere("CenserBrazierCore", c_pos, 0.095, mats["SicklyGreenBile"]))
    farm_r.append(make_torus("CenserRingA", c_pos, 0.105, 0.014, mats["TarnishedBronze"]))
    farm_r.append(make_torus("CenserRingB", c_pos, 0.105, 0.014, mats["TarnishedBronze"], (math.radians(90.0), 0.0, 0.0)))

    return export_articulated_enemy_glb(
        "enemy_05_plague_bloater.glb",
        pelvis_parts, thigh_l, shin_l, thigh_r, shin_r,
        torso_parts, head_parts, uarm_l, farm_l, uarm_r, farm_r, sec_parts
    )


def build_enemy_06_weeping_banshee() -> int:
    clear_scene()
    mats = create_enemy_palette()

    pelvis_parts, thigh_l, shin_l, thigh_r, shin_r = build_articulated_legs_and_pelvis(
        mats, mats["WeatheredStone"], mats["SilveredSteel"], mats["WeatheredStone"], include_tassets=True, robe_skirt=True
    )
    torso_parts = build_ribcage_and_cuirass_torso(
        mats, mats["WeatheredStone"], mats["SilveredSteel"], mats["FrozenBlueSoul"], exposed_ribs=True
    )
    # Sculpted Weeping Stone Wings on Back of Torso
    for side_i, sx in enumerate((-1.0, 1.0)):
        torso_parts.append(make_box(f"WingRootArch_{side_i}", (sx * 0.22, 0.14, 1.48), (0.28, 0.06, 0.12), mats["WeatheredStone"], (0.0, sx * math.radians(-28.0), 0.0)))
        for f_i in range(7):
            fx = sx * (0.20 + f_i * 0.055)
            fz = 1.54 - f_i * 0.065
            flen = 0.48 - f_i * 0.035
            torso_parts.append(
                make_box(
                    f"WingFeather_{side_i}_{f_i}",
                    (fx, 0.16, fz - flen * 0.4),
                    (0.048, 0.032, flen),
                    mats["WeatheredStone"] if (f_i % 2 == 0) else mats["FrozenBlueSoul"],
                    (0.0, sx * math.radians(12.0 + f_i * 4.0), 0.0),
                )
            )

    head_parts = build_gothic_skull_or_helm_head(
        mats, mats["WeatheredStone"], mats["SilveredSteel"], mats["FrozenBlueSoul"], horn_pairs=1, visor_slits=3
    )
    for sx_i, sx in enumerate((-1.0, 1.0)):
        head_parts.append(make_box(f"FrozenTearStreak_{sx_i}", (sx * 0.042, -0.115, 1.62), (0.016, 0.018, 0.09), mats["FrozenBlueSoul"]))

    uarm_l, farm_l = build_articulated_arm_pair("BansheeL", -1.0, mats, mats["WeatheredStone"], mats["SilveredSteel"])
    uarm_r, farm_r = build_articulated_arm_pair("BansheeR", 1.0, mats, mats["WeatheredStone"], mats["SilveredSteel"])

    # Elongated Spectral Claws
    for arm_list, side_s, pref in ((farm_l, -1.0, "ClawL"), (farm_r, 1.0, "ClawR")):
        hx = side_s * 0.30
        for c_i in range(4):
            cx = hx - 0.036 + c_i * 0.024
            arm_list.append(
                make_cone(
                    f"{pref}_Talon_{c_i}",
                    (cx, -0.44, 1.07),
                    0.012,
                    0.001,
                    0.18,
                    mats["FrozenBlueSoul"],
                    (math.radians(80.0), 0.0, 0.0),
                )
            )

    # SecondaryProp: Chained Spectral Soul Lantern
    sec_parts: list[bpy.types.Object] = []
    sec_parts.extend(spawn_chain_strand("BansheeLanternChain", (-0.32, -0.34, 1.26), 5, (0.0, 0.0, -0.05), 0.022, 0.005, mats["SilveredSteel"]))
    sec_parts.append(make_sphere("BansheeSoulLantern", (-0.32, -0.34, 0.98), 0.075, mats["FrozenBlueSoul"]))
    sec_parts.append(make_torus("BansheeLanternCage", (-0.32, -0.34, 0.98), 0.085, 0.012, mats["SilveredSteel"], (math.radians(90.0), 0.0, 0.0)))

    return export_articulated_enemy_glb(
        "enemy_06_weeping_banshee.glb",
        pelvis_parts, thigh_l, shin_l, thigh_r, shin_r,
        torso_parts, head_parts, uarm_l, farm_l, uarm_r, farm_r, sec_parts
    )


def build_enemy_07_bell_juggernaut() -> int:
    clear_scene()
    mats = create_enemy_palette()

    pelvis_parts, thigh_l, shin_l, thigh_r, shin_r = build_articulated_legs_and_pelvis(
        mats, mats["TarnishedBronze"], mats["WroughtIron"], mats["GothicPlateSteel"], include_tassets=True, robe_skirt=False
    )
    torso_parts = build_ribcage_and_cuirass_torso(
        mats, mats["TarnishedBronze"], mats["WroughtIron"], mats["EmissiveAmberFlame"], exposed_ribs=False
    )
    # Cathedral Bell Shell encasing Torso
    torso_parts.append(make_cone("CathedralBellShell", (0.0, 0.0, 1.28), 0.42, 0.24, 0.62, mats["TarnishedBronze"], verts=18))
    torso_parts.append(make_torus("BellSoundBowRim", (0.0, 0.0, 0.98), 0.42, 0.032, mats["TarnishedBronze"]))
    torso_parts.append(make_torus("BellShoulderBand", (0.0, 0.0, 1.48), 0.28, 0.022, mats["WroughtIron"]))
    for cr_i in range(6):
        ang = (cr_i / 6.0) * math.tau
        torso_parts.append(
            make_box(
                f"BellGlowingCrack_{cr_i}",
                (math.cos(ang) * 0.33, math.sin(ang) * 0.33, 1.24),
                (0.025, 0.025, 0.36),
                mats["EmissiveAmberFlame"],
                (0.0, 0.0, ang),
            )
        )
    for rv_i in range(12):
        ang = (rv_i / 12.0) * math.tau
        torso_parts.append(make_sphere(f"BellRimRivet_{rv_i}", (math.cos(ang) * 0.41, math.sin(ang) * 0.41, 1.04), 0.018, mats["WroughtIron"]))

    # SecondaryProp: Internal Bell-Clapper Pendulum & Chains
    sec_parts: list[bpy.types.Object] = []
    sec_parts.extend(spawn_chain_strand("BellInnerChain", (0.0, 0.0, 1.32), 4, (0.0, 0.0, -0.08), 0.030, 0.008, mats["WroughtIron"]))
    sec_parts.append(make_sphere("BellInnerClapperBall", (0.0, 0.0, 0.96), 0.095, mats["EmissiveAmberFlame"]))

    head_parts = build_gothic_skull_or_helm_head(
        mats, mats["TarnishedBronze"], mats["WroughtIron"], mats["EmissiveAmberFlame"], horn_pairs=1, visor_slits=5
    )
    head_parts.append(make_torus("BellCrownShackle", (0.0, 0.0, 1.84), 0.095, 0.020, mats["WroughtIron"], (math.radians(90.0), 0.0, 0.0)))

    uarm_l, farm_l = build_articulated_arm_pair("JugL", -1.0, mats, mats["TarnishedBronze"], mats["WroughtIron"])
    uarm_r, farm_r = build_articulated_arm_pair("JugR", 1.0, mats, mats["TarnishedBronze"], mats["WroughtIron"])

    # ForearmR: Giant Broken Bell-Clapper Warhammer
    rx = 0.34
    farm_r.append(make_cyl("HammerGreatShaft", (rx, -0.32, 1.22), 0.028, 1.75, mats["WroughtIron"]))
    for g_i in range(5):
        farm_r.append(make_torus(f"HammerShaftRing_{g_i}", (rx, -0.32, 0.60 + g_i * 0.32), 0.034, 0.008, mats["TarnishedBronze"]))
    head_z = 2.02
    farm_r.append(make_cyl("ClapperWarhead", (rx, -0.32, head_z), 0.14, 0.48, mats["TarnishedBronze"], (math.radians(90.0), 0.0, 0.0)))
    farm_r.append(make_sphere("ClapperStrikeFront", (rx, -0.56, head_z), 0.145, mats["EmissiveAmberFlame"]))
    farm_r.append(make_cone("ClapperBackSpike", (rx, -0.02, head_z), 0.09, 0.008, 0.24, mats["WroughtIron"], (math.radians(-90.0), 0.0, 0.0)))
    for fl_i in range(6):
        ang = (fl_i / 6.0) * math.tau
        farm_r.append(
            make_box(
                f"WarheadFlange_{fl_i}",
                (rx + math.cos(ang) * 0.14, -0.32, head_z + math.sin(ang) * 0.14),
                (0.028, 0.44, 0.035),
                mats["WroughtIron"],
                (0.0, ang, 0.0),
            )
        )

    return export_articulated_enemy_glb(
        "enemy_07_bell_juggernaut.glb",
        pelvis_parts, thigh_l, shin_l, thigh_r, shin_r,
        torso_parts, head_parts, uarm_l, farm_l, uarm_r, farm_r, sec_parts
    )


def build_enemy_08_abyssal_archon() -> int:
    clear_scene()
    mats = create_enemy_palette()

    pelvis_parts, thigh_l, shin_l, thigh_r, shin_r = build_articulated_legs_and_pelvis(
        mats, mats["ObsidianPlate"], mats["TarnishedBronze"], mats["AbyssalCrimson"], include_tassets=True, robe_skirt=True
    )
    torso_parts = build_ribcage_and_cuirass_torso(
        mats, mats["ObsidianPlate"], mats["TarnishedBronze"], mats["AbyssalCrimson"], exposed_ribs=False
    )
    # SecondaryProp: 6 Floating Ritual Obelisk Shards
    sec_parts: list[bpy.types.Object] = []
    for ob_i in range(6):
        ang = (ob_i / 6.0) * math.pi
        ox = math.cos(ang) * 0.44
        oz = 1.52 + math.sin(ang) * 0.34
        sec_parts.append(make_box(f"FloatingObeliskBody_{ob_i}", (ox, 0.12, oz), (0.055, 0.055, 0.24), mats["ObsidianPlate"], (0.0, math.radians(15.0) * math.cos(ang), 0.0)))
        sec_parts.append(make_cone(f"FloatingObeliskTip_{ob_i}", (ox, 0.12, oz + 0.16), 0.042, 0.002, 0.09, mats["AbyssalCrimson"]))
        sec_parts.append(make_box(f"FloatingObeliskRune_{ob_i}", (ox, 0.09, oz), (0.020, 0.015, 0.18), mats["AbyssalCrimson"]))

    # 6-Horned Gothic Blood-Knight Helm
    head_parts = build_gothic_skull_or_helm_head(
        mats, mats["ObsidianPlate"], mats["TarnishedBronze"], mats["AbyssalCrimson"], horn_pairs=3, visor_slits=6
    )

    uarm_l, farm_l = build_articulated_arm_pair("ArchonL", -1.0, mats, mats["ObsidianPlate"], mats["TarnishedBronze"])
    uarm_r, farm_r = build_articulated_arm_pair("ArchonR", 1.0, mats, mats["ObsidianPlate"], mats["TarnishedBronze"])

    # ForearmL: Abyssal Blood Sigil Shield
    farm_l.append(make_torus("ArchonBloodSigilOuter", (-0.34, -0.40, 1.18), 0.22, 0.018, mats["TarnishedBronze"], (0.0, math.radians(90.0), 0.0)))
    farm_l.append(make_torus("ArchonBloodSigilInner", (-0.34, -0.40, 1.18), 0.13, 0.014, mats["AbyssalCrimson"], (0.0, math.radians(90.0), 0.0)))
    for sp_i in range(6):
        ang = (sp_i / 6.0) * math.tau
        farm_l.append(
            make_cone(
                f"SigilSpike_{sp_i}",
                (-0.34, -0.40 + math.cos(ang) * 0.24, 1.18 + math.sin(ang) * 0.24),
                0.020,
                0.002,
                0.08,
                mats["AbyssalCrimson"],
                (math.cos(ang) * 1.5, 0.0, math.sin(ang) * 1.5),
            )
        )

    # ForearmR: Twin-Bladed Ritual Blood Glaive
    rx = 0.34
    farm_r.append(make_cyl("GlaiveShaft", (rx, -0.32, 1.25), 0.024, 1.85, mats["ObsidianPlate"]))
    for r_i in range(6):
        farm_r.append(make_torus(f"GlaiveGripRing_{r_i}", (rx, -0.32, 0.55 + r_i * 0.28), 0.030, 0.007, mats["TarnishedBronze"]))
    for end_s, end_z in ((1.0, 2.26), (-1.0, 0.24)):
        farm_r.append(make_box(f"GlaiveGuard_{end_s}", (rx, -0.32, end_z - end_s * 0.12), (0.045, 0.22, 0.04), mats["TarnishedBronze"]))
        farm_r.append(make_box(f"GlaiveBlade_{end_s}", (rx, -0.38, end_z + end_s * 0.18), (0.020, 0.14, 0.52), mats["SilveredSteel"]))
        farm_r.append(make_box(f"GlaiveBloodFuller_{end_s}", (rx, -0.36, end_z + end_s * 0.16), (0.025, 0.035, 0.42), mats["AbyssalCrimson"]))
        for b_i in range(3):
            bz = end_z + end_s * (0.06 + b_i * 0.12)
            farm_r.append(make_cone(f"GlaiveBarb_{end_s}_{b_i}", (rx, -0.47, bz), 0.018, 0.002, 0.065, mats["AbyssalCrimson"], (math.radians(90.0), 0.0, 0.0)))

    return export_articulated_enemy_glb(
        "enemy_08_abyssal_archon.glb",
        pelvis_parts, thigh_l, shin_l, thigh_r, shin_r,
        torso_parts, head_parts, uarm_l, farm_l, uarm_r, farm_r, sec_parts
    )


def main() -> None:
    print("[VoxelEnemyBuilder] Starting procedural generation of all 11 articulated enemy & boss models...")
    counts: dict[str, int] = {}
    counts["enemy_ossuary_skeleton.glb"] = build_enemy_ossuary_skeleton()
    counts["enemy_plague_acolyte.glb"] = build_enemy_plague_acolyte()
    counts["enemy_iron_penitent.glb"] = build_enemy_iron_penitent()
    counts["enemy_01_ossuary_executioner.glb"] = build_enemy_01_ossuary_executioner()
    counts["enemy_02_necropolis_praetorian.glb"] = build_enemy_02_necropolis_praetorian()
    counts["enemy_03_reliquary_hexweaver.glb"] = build_enemy_03_reliquary_hexweaver()
    counts["enemy_04_inquisitor_rackmaster.glb"] = build_enemy_04_inquisitor_rackmaster()
    counts["enemy_05_plague_bloater.glb"] = build_enemy_05_plague_bloater()
    counts["enemy_06_weeping_banshee.glb"] = build_enemy_06_weeping_banshee()
    counts["enemy_07_bell_juggernaut.glb"] = build_enemy_07_bell_juggernaut()
    counts["enemy_08_abyssal_archon.glb"] = build_enemy_08_abyssal_archon()

    print("\n==============================================================================")
    print("[VoxelEnemyBuilder] SUCCESS: ALL 11 ARTICULATED ENEMY & BOSS MODELS EXPORTED!")
    print("==============================================================================")
    for model_name, cnt in counts.items():
        print(f"  - {model_name:38s}: {cnt:3d} physical 3D sub-elements")
    print(f"Total physical 3D parts across 11 models: {sum(counts.values())}")


if __name__ == "__main__":
    main()
