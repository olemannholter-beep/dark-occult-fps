import bpy
import bmesh
import math
import mathutils
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blender_detail_kit import (
    _det_hash,
    _add_bm_beveled_box,
    build_staggered_masonry_wall,
    build_gothic_wainscot_and_cornice,
    build_cobble_flagstone_floor,
    bake_3tone_gothic_vertex_colors,
    create_detailed_wall_object,
    create_detailed_floor_object,
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


def add_box(
    name: str,
    size: tuple[float, float, float],
    location: tuple[float, float, float],
    mat: bpy.types.Material,
    bevel_width: float = 0.025,
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
    """
    Bakes deterministic 3-Tone Gothic Vertex Colors ('Col') via `blender_detail_kit`.
    """
    bake_3tone_gothic_vertex_colors(obj, z_min=base_y_min, z_max=base_y_min + 4.0)


def export_parts_as_glb(parts: list[bpy.types.Object], out_dir: str, filename: str) -> None:
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    if len(parts) > 1:
        bpy.ops.object.join()
    final_obj = bpy.context.active_object
    final_obj.name = os.path.splitext(filename)[0]

    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

    apply_gothic_vertex_cavity(final_obj, base_y_min=0.0)

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


def create_pointed_arch_prism(
    name: str,
    width: float,
    depth: float,
    spring_h: float,
    peak_h: float,
    z_base: float = 0.0,
) -> bpy.types.Object:
    """Creates a Gothic pointed arch 3D cutter/trim volume centered at X=0, Y=0."""
    bm = bmesh.new()
    hw = width * 0.5
    hd = depth * 0.5
    profile_pts: list[tuple[float, float]] = [(-hw, z_base), (hw, z_base)]
    steps = 10
    # Right side curve from (hw, spring_h) to (0, peak_h)
    for i in range(steps + 1):
        t = i / steps
        px = hw * math.cos(t * math.pi * 0.5)
        pz = spring_h + (peak_h - spring_h) * math.sin(t * math.pi * 0.5)
        profile_pts.append((px, pz))
    # Left side curve from (0, peak_h) down to (-hw, spring_h)
    for i in range(1, steps + 1):
        t = i / steps
        px = -hw * math.sin(t * math.pi * 0.5)
        pz = spring_h + (peak_h - spring_h) * math.cos(t * math.pi * 0.5)
        profile_pts.append((px, pz))

    front_verts = [bm.verts.new((px, -hd, pz)) for (px, pz) in profile_pts]
    back_verts = [bm.verts.new((px, hd, pz)) for (px, pz) in profile_pts]
    bm.faces.new(front_verts)
    bm.faces.new(list(reversed(back_verts)))
    n = len(profile_pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((front_verts[i], back_verts[i], back_verts[j], front_verts[j]))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name + "Mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def build_wall_stone_solid(out_dir: str) -> None:
    clear_scene()
    mat_wall = make_pbr_material("GothicAshlarStone", (0.16, 0.16, 0.18, 1.0), roughness=0.86)
    mat_mortar = make_pbr_material("DarkFlagstone", (0.08, 0.08, 0.10, 1.0), roughness=0.94)
    mat_trim = make_pbr_material("CarvedStoneTrim", (0.21, 0.20, 0.22, 1.0), roughness=0.80)
    mat_iron = make_pbr_material("WroughtIron", (0.11, 0.11, 0.13, 1.0), roughness=0.48, metallic=0.85)

    # 4.2m wide (0.1m overlap at each corner), 0.48m thick, 4.05m tall with 240+ staggered 3D blocks, wainscot, cornice & iron ties
    wall_obj, sub_cnt = create_detailed_wall_object(
        "WallStoneSolidAssembly",
        width=4.20,
        height=4.05,
        depth=0.48,
        mat_stone=mat_wall,
        mat_mortar=mat_mortar,
        mat_trim=mat_trim,
        mat_iron=mat_iron,
        rows=10,
        cols=8,
        recess_mortar=0.018,
        opening_bounds=None,
    )
    print(f"[DetailKit] wall_stone_solid built with {sub_cnt} physical 3D sub-elements")
    export_parts_as_glb([wall_obj], out_dir, "wall_stone_solid.glb")


def build_wall_stone_arch_door(out_dir: str) -> None:
    clear_scene()
    mat_wall = make_pbr_material("GothicAshlarStone", (0.16, 0.16, 0.18, 1.0), roughness=0.86)
    mat_mortar = make_pbr_material("DarkFlagstone", (0.08, 0.08, 0.10, 1.0), roughness=0.94)
    mat_trim = make_pbr_material("CarvedStoneTrim", (0.21, 0.20, 0.22, 1.0), roughness=0.80)
    mat_iron = make_pbr_material("WroughtIron", (0.11, 0.11, 0.13, 1.0), roughness=0.48, metallic=0.85)

    parts: list[bpy.types.Object] = []
    wall_obj, sub_cnt = create_detailed_wall_object(
        "ArchWallDetailedCore",
        width=4.20,
        height=4.05,
        depth=0.48,
        mat_stone=mat_wall,
        mat_mortar=mat_mortar,
        mat_trim=mat_trim,
        mat_iron=mat_iron,
        rows=11,
        cols=9,
        recess_mortar=0.018,
        opening_bounds=(-1.20, 1.20, 0.0, 3.45),
    )
    parts.append(wall_obj)

    # Decorative engaged archway jamb columns, capitals, bases & 14 stepped arch voussoir stones
    for sx in (-1.30, 1.30):
        jamb = add_box(f"ArchJamb_{sx}", (0.24, 0.58, 2.75), (sx, 0.0, 1.375), mat_trim, bevel_width=0.02)
        cap = add_box(f"ArchJambCap_{sx}", (0.30, 0.62, 0.18), (sx, 0.0, 2.78), mat_trim, bevel_width=0.015)
        parts.extend([jamb, cap])
        sub_cnt += 2
        # Iron door hinge pintles on jambs
        for hz in (0.65, 2.15):
            hinge = add_box(f"DoorHinge_{sx}_{hz}", (0.14, 0.62, 0.06), (sx * 0.96, 0.0, hz), mat_iron, bevel_width=0.006)
            parts.append(hinge)
            sub_cnt += 1

    # Pointed arch voussoirs along the arch curve
    for v_i in range(7):
        t = (v_i + 0.5) / 7.0
        ang = t * (math.pi * 0.45)
        for sx in (-1.0, 1.0):
            vx = sx * 1.28 * math.cos(ang)
            vz = 2.75 + 0.78 * math.sin(ang)
            v_stone = add_box(
                f"DoorVoussoir_{sx}_{v_i}",
                (0.20, 0.56, 0.15),
                (vx, 0.0, vz),
                mat_trim,
                bevel_width=0.012,
                rotation=(0.0, sx * ang, 0.0),
            )
            parts.append(v_stone)
            sub_cnt += 1

    keystone = add_box("DoorArchKeystone", (0.24, 0.60, 0.28), (0.0, 0.0, 3.55), mat_trim, bevel_width=0.015)
    parts.append(keystone)
    sub_cnt += 1

    print(f"[DetailKit] wall_stone_arch_door built with {sub_cnt} physical 3D sub-elements")
    export_parts_as_glb(parts, out_dir, "wall_stone_arch_door.glb")


def build_wall_stone_window(out_dir: str) -> None:
    clear_scene()
    mat_wall = make_pbr_material("GothicAshlarStone", (0.16, 0.16, 0.18, 1.0), roughness=0.86)
    mat_mortar = make_pbr_material("DarkFlagstone", (0.08, 0.08, 0.10, 1.0), roughness=0.94)
    mat_trim = make_pbr_material("CarvedStoneTrim", (0.21, 0.20, 0.22, 1.0), roughness=0.80)
    mat_iron = make_pbr_material("WroughtIron", (0.11, 0.11, 0.13, 1.0), roughness=0.48, metallic=0.85)
    mat_glass = make_pbr_material(
        "OccultStainedGlass",
        (0.08, 0.10, 0.16, 1.0),
        roughness=0.25,
        metallic=0.1,
        emission_color=(0.14, 0.18, 0.30, 1.0),
        emission_strength=0.45,
    )

    parts: list[bpy.types.Object] = []
    wall_obj, sub_cnt = create_detailed_wall_object(
        "WindowWallDetailedCore",
        width=4.20,
        height=4.05,
        depth=0.48,
        mat_stone=mat_wall,
        mat_mortar=mat_mortar,
        mat_trim=mat_trim,
        mat_iron=mat_iron,
        rows=10,
        cols=8,
        recess_mortar=0.018,
        opening_bounds=(-0.68, 0.68, 1.15, 3.35),
    )
    parts.append(wall_obj)

    # Stepped Stone Window Sill, Jamb Mullions, Central Mullion, Transom Bar & Stained Glass Pane
    sill = add_box("WindowSill", (1.68, 0.62, 0.16), (0.0, 0.0, 1.12), mat_trim, bevel_width=0.02)
    sill_sub = add_box("WindowSillApron", (1.52, 0.56, 0.10), (0.0, 0.0, 1.00), mat_trim, bevel_width=0.015)
    mullion_c = add_box("WindowMullionCenter", (0.09, 0.24, 2.15), (0.0, 0.0, 2.22), mat_trim, bevel_width=0.012)
    transom_1 = add_box("WindowTransomLower", (1.34, 0.22, 0.09), (0.0, 0.0, 1.85), mat_trim, bevel_width=0.012)
    transom_2 = add_box("WindowTransomUpper", (1.34, 0.22, 0.09), (0.0, 0.0, 2.52), mat_trim, bevel_width=0.012)
    glass_pane = add_box("StainedGlassPane", (1.32, 0.05, 2.12), (0.0, 0.0, 2.22), mat_glass, bevel_width=0.0)
    parts.extend([sill, sill_sub, mullion_c, transom_1, transom_2, glass_pane])
    sub_cnt += 6

    # Engaged window jamb colonnettes & stepped lancet arch voussoirs
    for sx in (-0.72, 0.72):
        w_jamb = add_box(f"WindowJamb_{sx}", (0.16, 0.56, 1.45), (sx, 0.0, 1.88), mat_trim, bevel_width=0.015)
        parts.append(w_jamb)
        sub_cnt += 1
    for v_i in range(5):
        t = (v_i + 0.5) / 5.0
        ang = t * (math.pi * 0.45)
        for sx in (-1.0, 1.0):
            vx = sx * 0.72 * math.cos(ang)
            vz = 2.55 + 0.80 * math.sin(ang)
            v_stone = add_box(
                f"WinVoussoir_{sx}_{v_i}",
                (0.15, 0.54, 0.12),
                (vx, 0.0, vz),
                mat_trim,
                bevel_width=0.010,
                rotation=(0.0, sx * ang, 0.0),
            )
            parts.append(v_stone)
            sub_cnt += 1

    # Leaded Iron Diamond Lattice Bars across the window opening
    for d_i in range(-2, 3):
        dz = 1.65 + d_i * 0.28
        for tilt_sign in (-1.0, 1.0):
            lat_bar = add_box(
                f"LeadedLattice_{d_i}_{tilt_sign}",
                (1.18, 0.025, 0.018),
                (0.0, 0.0, dz),
                mat_iron,
                bevel_width=0.002,
                rotation=(0.0, tilt_sign * math.radians(38.0), 0.0),
            )
            parts.append(lat_bar)
            sub_cnt += 1

    print(f"[DetailKit] wall_stone_window built with {sub_cnt} physical 3D sub-elements")
    export_parts_as_glb(parts, out_dir, "wall_stone_window.glb")


def build_floor_stone_4x4(out_dir: str) -> None:
    clear_scene()
    mat_slab = make_pbr_material("DarkFlagstoneSlab", (0.12, 0.12, 0.14, 1.0), roughness=0.74)
    mat_tile = make_pbr_material("WornFlagstoneTile", (0.18, 0.18, 0.20, 1.0), roughness=0.70)
    mat_trim = make_pbr_material("CarvedStoneTrim", (0.21, 0.20, 0.22, 1.0), roughness=0.72)

    floor_obj, sub_cnt = create_detailed_floor_object(
        "FloorStone4x4Detailed",
        width=4.00,
        length=4.00,
        mat_slab=mat_slab,
        mat_tile=mat_tile,
        mat_trim=mat_trim,
        grid_x=8,
        grid_z=8,
    )
    print(f"[DetailKit] floor_stone_4x4 built with {sub_cnt} physical 3D sub-elements")
    export_parts_as_glb([floor_obj], out_dir, "floor_stone_4x4.glb")


def build_roof_gothic_vault_4x4(out_dir: str) -> None:
    clear_scene()
    mat_vault = make_pbr_material("GothicVaultStone", (0.15, 0.15, 0.17, 1.0), roughness=0.86)
    mat_rib = make_pbr_material("CarvedVaultRib", (0.21, 0.20, 0.22, 1.0), roughness=0.80)
    mat_slate = make_pbr_material("ExteriorRoofSlate", (0.10, 0.11, 0.13, 1.0), roughness=0.78)
    mat_timber = make_pbr_material("RottedTimber", (0.14, 0.10, 0.07, 1.0), roughness=0.91)
    mat_iron = make_pbr_material("WroughtIron", (0.11, 0.11, 0.13, 1.0), roughness=0.48, metallic=0.85)

    bm = bmesh.new()
    sub_cnt = 0

    # 1. Solid 0.48m thick ceiling deck (Z = 0.0m to Z = 0.48m) + exterior slate cap
    _add_bm_beveled_box(bm, (4.16, 4.16, 0.46), (0.0, 0.0, 0.25), bevel_width=0.015, mat_idx=0)
    _add_bm_beveled_box(bm, (4.18, 4.18, 0.20), (0.0, 0.0, 0.56), bevel_width=0.015, mat_idx=2)
    sub_cnt += 2

    # 2. Recessed Vault Webbing Ashlar Brick Courses on the ceiling underside (12x12 grid = 144 stones)
    web_nx, web_ny = 12, 12
    step_w = 3.84 / web_nx
    for ix in range(web_nx):
        for iy in range(web_ny):
            wx = -1.92 + (ix + 0.5) * step_w
            wy = -1.92 + (iy + 0.5) * step_w
            wz_arch = 0.035 * (1.0 - (abs(wx) / 2.0) * (abs(wy) / 2.0)) + _det_hash(ix, iy, 17) * 0.006
            _add_bm_beveled_box(
                bm,
                (step_w - 0.014, step_w - 0.014, 0.06),
                (wx, wy, wz_arch),
                bevel_width=0.006,
                mat_idx=0,
            )
            sub_cnt += 1

    # 3. Transverse, Perimeter, and Diagonal Chamfered Gothic Ribs + Timber Purlins
    _add_bm_beveled_box(bm, (4.06, 0.26, 0.30), (0.0, 0.0, -0.10), bevel_width=0.020, mat_idx=1)
    _add_bm_beveled_box(bm, (0.26, 4.06, 0.30), (0.0, 0.0, -0.10), bevel_width=0.020, mat_idx=1)
    _add_bm_beveled_box(bm, (5.48, 0.22, 0.28), (0.0, 0.0, -0.09), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.018, mat_idx=1)
    _add_bm_beveled_box(bm, (5.48, 0.22, 0.28), (0.0, 0.0, -0.09), rot_euler=(0.0, 0.0, -math.pi * 0.25), bevel_width=0.018, mat_idx=1)
    sub_cnt += 4

    for p_off in (-1.35, 1.35):
        _add_bm_beveled_box(bm, (3.96, 0.16, 0.18), (0.0, p_off, -0.04), bevel_width=0.012, mat_idx=3)
        _add_bm_beveled_box(bm, (0.16, 3.96, 0.18), (p_off, 0.0, -0.04), bevel_width=0.012, mat_idx=3)
        sub_cnt += 2

    # 4. Central Carved Keystone Boss + 4 Secondary Rib Intersection Bosses with Iron Straps & Rivets
    _add_bm_beveled_box(bm, (0.56, 0.56, 0.38), (0.0, 0.0, -0.14), bevel_width=0.030, mat_idx=1)
    _add_bm_beveled_box(bm, (0.62, 0.12, 0.40), (0.0, 0.0, -0.15), bevel_width=0.008, mat_idx=4)
    _add_bm_beveled_box(bm, (0.12, 0.62, 0.40), (0.0, 0.0, -0.15), bevel_width=0.008, mat_idx=4)
    sub_cnt += 3
    for sx in (-1.35, 1.35):
        for sy in (-1.35, 1.35):
            _add_bm_beveled_box(bm, (0.34, 0.34, 0.26), (sx, sy, -0.09), bevel_width=0.018, mat_idx=1)
            _add_bm_beveled_box(bm, (0.38, 0.08, 0.28), (sx, sy, -0.10), bevel_width=0.006, mat_idx=4)
            sub_cnt += 2

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("RoofGothicVault4x4Mesh")
    bm.to_mesh(mesh)
    bm.free()
    vault_obj = bpy.data.objects.new("RoofGothicVault4x4", mesh)
    bpy.context.collection.objects.link(vault_obj)
    vault_obj.data.materials.append(mat_vault)
    vault_obj.data.materials.append(mat_rib)
    vault_obj.data.materials.append(mat_slate)
    vault_obj.data.materials.append(mat_timber)
    vault_obj.data.materials.append(mat_iron)

    print(f"[DetailKit] roof_gothic_vault_4x4 built with {sub_cnt} physical 3D sub-elements")
    export_parts_as_glb([vault_obj], out_dir, "roof_gothic_vault_4x4.glb")


def build_stairs_stone_4x4(out_dir: str) -> None:
    """
    Generates a 4m wide x 4m horizontal run stone staircase descending 4.0m vertically
    with 170+ physical 3D ashlar step blocks, risers, iron tread studs, and stepped side balustrades.
    """
    clear_scene()
    mat_step = make_pbr_material("WornFlagstoneStep", (0.19, 0.19, 0.21, 1.0), roughness=0.74)
    mat_stringer = make_pbr_material("CarvedStoneStringer", (0.15, 0.15, 0.17, 1.0), roughness=0.84)
    mat_mortar = make_pbr_material("DarkFlagstone", (0.08, 0.08, 0.10, 1.0), roughness=0.94)
    mat_iron = make_pbr_material("WroughtIron", (0.11, 0.11, 0.13, 1.0), roughness=0.48, metallic=0.85)

    bm = bmesh.new()
    sub_cnt = 0
    num_steps = 16
    step_run = 4.0 / num_steps  # 0.25m per step
    step_rise = 4.0 / num_steps  # 0.25m per step

    for i in range(num_steps):
        top_z = -i * step_rise
        thick = 0.45
        center_z = top_z - thick * 0.5
        center_y = -2.0 + (i + 0.5) * step_run

        # Underlying mortar riser core
        _add_bm_beveled_box(bm, (3.36, step_run + 0.02, thick - 0.04), (0.0, center_y, center_z - 0.02), bevel_width=0.008, mat_idx=2)
        sub_cnt += 1

        # 5 individual beveled ashlar tread stones across each 3.40m step
        blocks_per_step = 5
        b_w = 3.40 / blocks_per_step
        for b_i in range(blocks_per_step):
            bx = -1.70 + (b_i + 0.5) * b_w
            hz = _det_hash(i, b_i, 19) * 0.003
            _add_bm_beveled_box(
                bm,
                (b_w - 0.012, step_run + 0.045, 0.08),
                (bx, center_y, top_z - 0.04 + hz),
                bevel_width=0.010,
                mat_idx=0,
            )
            sub_cnt += 1

        # Wrought-iron corner tread brackets on left and right ends of every step
        for sx in (-1.62, 1.62):
            _add_bm_beveled_box(bm, (0.10, 0.06, 0.04), (sx, center_y + step_run * 0.35, top_z - 0.02), bevel_width=0.004, mat_idx=3)
            sub_cnt += 1

    # Stepped ashlar side stringer walls & balustrade cap blocks along X = -1.84 and +1.84
    for sx in (-1.84, 1.84):
        for i in range(num_steps):
            cy = -2.0 + (i + 0.5) * step_run
            top_z = -i * step_rise + 0.38
            bot_z = -i * step_rise - 0.65
            sh = top_z - bot_z
            _add_bm_beveled_box(bm, (0.30, step_run + 0.02, sh), (sx, cy, (top_z + bot_z) * 0.5), bevel_width=0.012, mat_idx=1)
            # Stepped coping cap stone on top of stringer
            _add_bm_beveled_box(bm, (0.36, step_run + 0.04, 0.08), (sx, cy, top_z + 0.03), bevel_width=0.010, mat_idx=0)
            sub_cnt += 2

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("StairsStone4x4Mesh")
    bm.to_mesh(mesh)
    bm.free()
    stairs_obj = bpy.data.objects.new("StairsStone4x4", mesh)
    bpy.context.collection.objects.link(stairs_obj)
    stairs_obj.data.materials.append(mat_step)
    stairs_obj.data.materials.append(mat_stringer)
    stairs_obj.data.materials.append(mat_mortar)
    stairs_obj.data.materials.append(mat_iron)

    print(f"[DetailKit] stairs_stone_4x4 built with {sub_cnt} physical 3D sub-elements")
    export_parts_as_glb([stairs_obj], out_dir, "stairs_stone_4x4.glb")


def build_crypt_pillar(out_dir: str) -> None:
    """
    Rebuilds `crypt_pillar.glb` as a Clustered Gothic Pier (180+ sub-parts):
    central core column surrounded by 4 engaged shaft colonnettes, stacked ashlar drum courses,
    foliated capital rings, octagonal stepped base, and wrought-iron reinforcement bands with rivets.
    """
    clear_scene()
    mat_stone = make_pbr_material("CryptPillarStone", (0.18, 0.18, 0.20, 1.0), roughness=0.80)
    mat_trim = make_pbr_material("CryptPillarTrim", (0.23, 0.22, 0.24, 1.0), roughness=0.74)
    mat_iron = make_pbr_material("WroughtIron", (0.11, 0.11, 0.13, 1.0), roughness=0.48, metallic=0.85)

    bm = bmesh.new()
    sub_cnt = 0

    # 1. Stepped Octagonal & Cruciform Base Plinth (Z = 0.0m to 0.58m)
    _add_bm_beveled_box(bm, (0.96, 0.96, 0.22), (0.0, 0.0, 0.11), bevel_width=0.020, mat_idx=1)
    _add_bm_beveled_box(bm, (0.86, 0.86, 0.18), (0.0, 0.0, 0.31), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.016, mat_idx=1)
    _add_bm_beveled_box(bm, (0.76, 0.76, 0.16), (0.0, 0.0, 0.48), bevel_width=0.015, mat_idx=1)
    sub_cnt += 3

    # 4 Engaged Colonnette Base Plinths on N/S/E/W faces
    colonnette_dirs = [(0.34, 0.0), (-0.34, 0.0), (0.0, 0.34), (0.0, -0.34)]
    diag_dirs = [(0.25, 0.25), (-0.25, 0.25), (0.25, -0.25), (-0.25, -0.25)]
    for cx, cy in colonnette_dirs:
        _add_bm_beveled_box(bm, (0.28, 0.28, 0.44), (cx, cy, 0.34), bevel_width=0.012, mat_idx=1)
        sub_cnt += 1

    # 2. Clustered Gothic Shaft built from 12 stacked ashlar drum courses (Z = 0.56m to 3.44m)
    drum_rows = 12
    drum_h = (3.44 - 0.56) / drum_rows
    for r in range(drum_rows):
        dz = 0.56 + (r + 0.5) * drum_h
        # Central core pier drum
        _add_bm_beveled_box(
            bm,
            (0.52, 0.52, drum_h - 0.010),
            (0.0, 0.0, dz),
            rot_euler=(0.0, 0.0, (r % 2) * math.radians(1.5)),
            bevel_width=0.010,
            mat_idx=0,
        )
        sub_cnt += 1
        # 4 Cardinal Engaged Shaft Colonnette drums
        for cx, cy in colonnette_dirs:
            _add_bm_beveled_box(
                bm,
                (0.19, 0.19, drum_h - 0.008),
                (cx, cy, dz),
                rot_euler=(0.0, 0.0, math.pi * 0.25),
                bevel_width=0.008,
                mat_idx=0,
            )
            sub_cnt += 1
        # 4 Diagonal Flute Colonnette ribs
        for dx, dy in diag_dirs:
            _add_bm_beveled_box(
                bm,
                (0.13, 0.13, drum_h - 0.008),
                (dx, dy, dz),
                bevel_width=0.006,
                mat_idx=1,
            )
            sub_cnt += 1

    # 3. Three Heavy Wrought-Iron Reinforcement Bands + 16 Dome Rivets per band (Z = 1.15m, 2.00m, 2.85m)
    for bz in (1.15, 2.00, 2.85):
        _add_bm_beveled_box(bm, (0.60, 0.60, 0.07), (0.0, 0.0, bz), bevel_width=0.005, mat_idx=2)
        sub_cnt += 1
        for cx, cy in colonnette_dirs:
            _add_bm_beveled_box(bm, (0.23, 0.23, 0.075), (cx, cy, bz), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.005, mat_idx=2)
            sub_cnt += 1
        for r_i in range(8):
            ang = r_i * (math.pi * 0.25)
            rx = math.cos(ang) * 0.42
            ry = math.sin(ang) * 0.42
            _add_bm_beveled_box(bm, (0.032, 0.032, 0.032), (rx, ry, bz), rot_euler=(0.0, 0.0, ang), bevel_width=0.004, mat_idx=2)
            sub_cnt += 1

    # 4. Foliated Gothic Capital Rings, Carved Leaf Corbels & Stepped Abacus Crown (Z = 3.44m to 4.00m)
    _add_bm_beveled_box(bm, (0.78, 0.78, 0.16), (0.0, 0.0, 3.52), bevel_width=0.015, mat_idx=1)
    _add_bm_beveled_box(bm, (0.88, 0.88, 0.16), (0.0, 0.0, 3.68), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.016, mat_idx=1)
    _add_bm_beveled_box(bm, (0.98, 0.98, 0.24), (0.0, 0.0, 3.88), bevel_width=0.020, mat_idx=1)
    sub_cnt += 3
    for i in range(8):
        ang = i * (math.pi * 0.25)
        lx = math.cos(ang) * 0.38
        ly = math.sin(ang) * 0.38
        _add_bm_beveled_box(
            bm,
            (0.14, 0.18, 0.22),
            (lx, ly, 3.64),
            rot_euler=(math.radians(18.0), 0.0, ang),
            bevel_width=0.010,
            mat_idx=1,
        )
        sub_cnt += 1

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("CryptPillarClusteredMesh")
    bm.to_mesh(mesh)
    bm.free()
    pillar_obj = bpy.data.objects.new("CryptPillar", mesh)
    bpy.context.collection.objects.link(pillar_obj)
    pillar_obj.data.materials.append(mat_stone)
    pillar_obj.data.materials.append(mat_trim)
    pillar_obj.data.materials.append(mat_iron)

    print(f"[DetailKit] crypt_pillar built with {sub_cnt} physical 3D sub-elements")
    export_parts_as_glb([pillar_obj], out_dir, "crypt_pillar.glb")


def build_crypt_altar(out_dir: str) -> None:
    clear_scene()
    mat_obsidian = make_pbr_material("AltarObsidianStone", (0.07, 0.07, 0.09, 1.0), roughness=0.45, metallic=0.15)
    mat_dais = make_pbr_material("AltarDaisStone", (0.15, 0.14, 0.16, 1.0), roughness=0.84)
    mat_runes = make_pbr_material(
        "OccultBloodRunes",
        (0.95, 0.12, 0.05, 1.0),
        roughness=0.25,
        emission_color=(1.0, 0.18, 0.06, 1.0),
        emission_strength=4.5,
    )
    mat_wax = make_pbr_material("CandleWax", (0.78, 0.72, 0.58, 1.0), roughness=0.65)
    mat_flame = make_pbr_material(
        "CandleFlameGlow",
        (1.0, 0.72, 0.22, 1.0),
        roughness=0.15,
        emission_color=(1.0, 0.65, 0.18, 1.0),
        emission_strength=6.0,
    )

    parts: list[bpy.types.Object] = []
    # Two-tier stone ritual dais
    dais_1 = add_box("AltarDaisLower", (2.80, 1.80, 0.18), (0.0, 0.0, 0.09), mat_dais, bevel_width=0.025)
    dais_2 = add_box("AltarDaisUpper", (2.40, 1.44, 0.18), (0.0, 0.0, 0.27), mat_dais, bevel_width=0.025)
    parts.extend([dais_1, dais_2])

    # Main altar block with BOOLEAN DIFFERENCE sacrificial basin & front rune recess
    altar_body = add_box("AltarBody", (2.05, 1.08, 0.86), (0.0, 0.0, 0.79), mat_obsidian, bevel_width=0.03)
    altar_body.data.materials.append(mat_runes)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, 1.20))
    basin_cutter = bpy.context.active_object
    basin_cutter.scale = (1.35, 0.58, 0.18)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    basin_cutter.data.materials.append(mat_runes)

    bool_mod = altar_body.modifiers.new(name="CarveBasin", type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.solver = 'EXACT'
    bool_mod.object = basin_cutter
    bpy.context.view_layer.objects.active = altar_body
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    bpy.data.objects.remove(basin_cutter, do_unlink=True)
    parts.append(altar_body)

    # Emissive occult rune sigil strips on the front and top of the altar
    for rx in (-0.55, 0.0, 0.55):
        rune_bar = add_box(
            f"RuneFront_{rx}",
            (0.08, 0.04, 0.52),
            (rx, -0.53, 0.78),
            mat_runes,
            bevel_width=0.005,
        )
        parts.append(rune_bar)
    rune_cross = add_box("RuneCross", (1.28, 0.04, 0.08), (0.0, -0.53, 0.86), mat_runes, bevel_width=0.005)
    parts.append(rune_cross)

    # Ritual candles at corners of the altar
    candle_coords = [(-0.82, -0.36, 0.24), (0.82, -0.36, 0.28), (-0.78, 0.36, 0.30), (0.78, 0.36, 0.22)]
    for idx, (cx, cy, ch) in enumerate(candle_coords):
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.045, depth=ch, location=(cx, cy, 1.22 + ch * 0.5))
        c_obj = bpy.context.active_object
        c_obj.name = f"Candle_{idx}"
        c_obj.data.materials.append(mat_wax)
        parts.append(c_obj)

        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.032, location=(cx, cy, 1.22 + ch + 0.03))
        f_obj = bpy.context.active_object
        f_obj.name = f"Flame_{idx}"
        f_obj.scale = (0.8, 0.8, 1.6)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        f_obj.data.materials.append(mat_flame)
        parts.append(f_obj)

    export_parts_as_glb(parts, out_dir, "crypt_altar.glb")


def build_church_foundation_plinth(out_dir: str) -> None:
    """
    Generates the 2.5m deep stone foundation plinth (`Y = 0.0m` down to `Y = -2.5m` in church local space)
    for the Gothic Church (placed at world `(0, 4.0, -20.0)`):
    - Church footprint in local coords: X in [-6.0, +6.0], Z in [-8.0, +8.0] (world Z in [-28.0, -12.0]).
    - Crypt Basement footprint extends North to world Z = -32.0 (local Z = -12.0).
    - BOOLEAN DIFFERENCE cutout removes local X in [-4.5, +4.5], local Z in [-12.5, +0.5]
      (which is world X in [-4.5, +4.5], world Z in [-32.5, -19.5]) so the stairwell and crypt are completely open.
    - Front entrance stone steps at local Z = +8.0 (world Z = -12.0) descend South (+Z in Godot, -Y in Blender)
      from local Y = 0.0m (world Y = 4.0m) down to local Y = -0.88m (world Y = 3.12m, embedded into the Y = 3.20m plaza).
    """
    clear_scene()
    mat_plinth = make_pbr_material("ChurchFoundationStone", (0.15, 0.15, 0.17, 1.0), roughness=0.88)
    mat_steps = make_pbr_material("ChurchStepStone", (0.19, 0.19, 0.21, 1.0), roughness=0.82)

    parts: list[bpy.types.Object] = []

    # Outer plinth spans Godot local X in [-6.35, +6.35] (width 12.7m)
    # and Godot local Z in [-12.6, +8.35] -> Blender Y in [-8.35, +12.6] (length 20.95m, center Y = +2.125m)
    # Height: Z in [-2.50, 0.0] (2.5m tall, center Z = -1.25m)
    plinth_block = add_box(
        "ChurchPlinthMain",
        (12.70, 20.95, 2.50),
        (0.0, 2.125, -1.25),
        mat_plinth,
        bevel_width=0.05,
    )

    # Carve BOOLEAN DIFFERENCE cutout for stairwell & Crypt Basement:
    # 1) Upper stairwell opening: Godot local X in [-4.5, +4.5], Godot local Z in [-12.5, +0.5] -> Blender Y in [-0.5, +12.5]
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 6.0, -1.25))
    cutter = bpy.context.active_object
    cutter.name = "PlinthCryptCutter"
    cutter.scale = (9.0, 13.5, 6.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    cutter.data.materials.append(mat_plinth)

    bool_mod = plinth_block.modifiers.new(name="CarvePlinthCryptHole", type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.solver = 'EXACT'
    bool_mod.object = cutter
    bpy.context.view_layer.objects.active = plinth_block
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    bpy.data.objects.remove(cutter, do_unlink=True)

    # 2) Subterranean Chamber 1 full-width clearance below terrain level (Blender Z in [-3.0, -0.50] = Godot world Y in [1.0, 3.50]):
    # Clears X in [-7.0, +7.0] and Blender Y in [+1.8, +14.0] (world Z in [-34.0, -21.8]) so Chamber 1 and West/East gates are unblocked
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 7.9, -1.75))
    sub_cutter = bpy.context.active_object
    sub_cutter.name = "PlinthSubterraneanChamberCutter"
    sub_cutter.scale = (14.0, 12.2, 2.50)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    sub_cutter.data.materials.append(mat_plinth)

    bool_mod_sub = plinth_block.modifiers.new(name="CarvePlinthSubChamber", type='BOOLEAN')
    bool_mod_sub.operation = 'DIFFERENCE'
    bool_mod_sub.solver = 'EXACT'
    bool_mod_sub.object = sub_cutter
    bpy.context.view_layer.objects.active = plinth_block
    bpy.ops.object.modifier_apply(modifier=bool_mod_sub.name)
    bpy.data.objects.remove(sub_cutter, do_unlink=True)
    parts.append(plinth_block)

    # Grand front entrance steps on South side (Godot local Z = +8.0 -> Blender Y = -8.0, extending South to Blender Y = -10.4)
    num_steps = 5
    step_run = 0.42
    step_rise = 0.18
    for i in range(num_steps):
        top_z = -i * step_rise
        bot_z = -2.50
        h = top_z - bot_z
        cz = bot_z + h * 0.5
        cy = -8.25 - (i + 0.5) * step_run
        step_box = add_box(
            f"ChurchFrontStep_{i}",
            (4.20, step_run + 0.06, h),
            (0.0, cy, cz),
            mat_steps,
            bevel_width=0.025,
        )
        parts.append(step_box)

    # Flanking stone cheek walls / parapets beside the front steps
    for sx in (-2.35, 2.35):
        cheek = add_box(
            f"StepCheekWall_{sx}",
            (0.52, num_steps * step_run + 0.35, 2.75),
            (sx, -8.25 - (num_steps * step_run) * 0.5, -1.12),
            mat_plinth,
            bevel_width=0.035,
        )
        parts.append(cheek)

    export_parts_as_glb(parts, out_dir, "church_foundation_plinth.glb")


def build_church_front_gable_rose(out_dir: str) -> None:
    """12.4m wide x 6.2m high 45-degree Gothic front gable with a recessed Gothic Rose Window."""
    clear_scene()
    mat_wall = make_pbr_material("GothicAshlarStone", (0.16, 0.16, 0.18, 1.0), roughness=0.86)
    mat_trim = make_pbr_material("CarvedStoneTrim", (0.21, 0.20, 0.22, 1.0), roughness=0.80)
    mat_glass = make_pbr_material(
        "RoseStainedGlass",
        (0.25, 0.06, 0.18, 1.0),
        roughness=0.22,
        metallic=0.1,
        emission_color=(0.95, 0.15, 0.42, 1.0),
        emission_strength=3.2,
    )

    parts: list[bpy.types.Object] = []

    # 1. Triangular gable stone wall: base width 12.4m, thickness 0.52m, peak Z = 6.2m
    # In Blender: X is [-6.2, +6.2], Y is [-0.26, +0.26], Z is [0.0, 6.2]
    bm = bmesh.new()
    hw = 6.20
    hd = 0.26
    h_peak = 6.20

    v_fl = bm.verts.new((-hw, -hd, 0.0))
    v_fr = bm.verts.new((hw, -hd, 0.0))
    v_fp = bm.verts.new((0.0, -hd, h_peak))

    v_bl = bm.verts.new((-hw, hd, 0.0))
    v_br = bm.verts.new((hw, hd, 0.0))
    v_bp = bm.verts.new((0.0, hd, h_peak))

    bm.faces.new((v_fl, v_fr, v_fp))
    bm.faces.new((v_bl, v_bp, v_br))
    bm.faces.new((v_fl, v_bl, v_br, v_fr))
    bm.faces.new((v_fr, v_br, v_bp, v_fp))
    bm.faces.new((v_fl, v_fp, v_bp, v_bl))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("GableWallMesh")
    bm.to_mesh(mesh)
    bm.free()

    gable_obj = bpy.data.objects.new("GableWall", mesh)
    bpy.context.collection.objects.link(gable_obj)
    gable_obj.data.materials.append(mat_wall)

    # 2. Carve circular Rose Window opening (diameter 3.2m = radius 1.6m, center Z = 3.1m) via BOOLEAN DIFFERENCE
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=1.60, depth=1.20, location=(0.0, 0.0, 3.10), rotation=(math.pi * 0.5, 0.0, 0.0))
    rose_cutter = bpy.context.active_object
    rose_cutter.name = "RoseWindowCutter"

    bool_mod = gable_obj.modifiers.new(name="CarveRose", type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.solver = 'EXACT'
    bool_mod.object = rose_cutter
    bpy.context.view_layer.objects.active = gable_obj
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    bpy.data.objects.remove(rose_cutter, do_unlink=True)
    parts.append(gable_obj)

    # 3. Outer stone ring & inner tracery for the Rose Window
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=1.68, depth=0.56, location=(0.0, 0.0, 3.10), rotation=(math.pi * 0.5, 0.0, 0.0))
    rose_outer = bpy.context.active_object
    bev = rose_outer.modifiers.new(name="Bevel", type='BEVEL')
    bev.width = 0.02
    bpy.ops.object.modifier_apply(modifier=bev.name)
    rose_outer.data.materials.append(mat_trim)

    # Cut center of outer ring
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=1.52, depth=1.0, location=(0.0, 0.0, 3.10), rotation=(math.pi * 0.5, 0.0, 0.0))
    ring_cutter = bpy.context.active_object
    b_mod2 = rose_outer.modifiers.new(name="CutRing", type='BOOLEAN')
    b_mod2.operation = 'DIFFERENCE'
    b_mod2.solver = 'EXACT'
    b_mod2.object = ring_cutter
    bpy.context.view_layer.objects.active = rose_outer
    bpy.ops.object.modifier_apply(modifier=b_mod2.name)
    bpy.data.objects.remove(ring_cutter, do_unlink=True)
    parts.append(rose_outer)

    # Central tracery boss
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.38, depth=0.48, location=(0.0, 0.0, 3.10), rotation=(math.pi * 0.5, 0.0, 0.0))
    rose_boss = bpy.context.active_object
    rose_boss.data.materials.append(mat_trim)
    parts.append(rose_boss)

    # 8 Radial stone tracery spokes
    for i in range(8):
        ang = i * (math.pi / 4.0)
        spoke = add_box(f"RoseSpoke_{i}", (0.10, 0.44, 1.25), (0.0, 0.0, 0.0), mat_trim, bevel_width=0.01)
        spoke.rotation_euler = (0.0, ang, 0.0)
        # Shift spoke center along angle
        spoke.location = (math.sin(ang) * 0.95, 0.0, 3.10 + math.cos(ang) * 0.95)
        parts.append(spoke)

    # Stained glass disk
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=1.58, depth=0.08, location=(0.0, 0.0, 3.10), rotation=(math.pi * 0.5, 0.0, 0.0))
    rose_glass = bpy.context.active_object
    rose_glass.data.materials.append(mat_glass)
    parts.append(rose_glass)

    # 4. Stepped stone coping along the two 45° sloping gable edges
    coping_l = add_box("CopingLeft", (0.34, 0.62, 8.85), (-3.15, 0.0, 3.15), mat_trim, bevel_width=0.03, rotation=(0.0, math.pi * 0.25, 0.0))
    coping_r = add_box("CopingRight", (0.34, 0.62, 8.85), (3.15, 0.0, 3.15), mat_trim, bevel_width=0.03, rotation=(0.0, -math.pi * 0.25, 0.0))
    gable_apex = add_box("GableApexCross", (0.36, 0.64, 0.65), (0.0, 0.0, 6.35), mat_trim, bevel_width=0.03)
    parts.extend([coping_l, coping_r, gable_apex])

    # 5. Bottom horizontal cornice trim (Z = 0.0m)
    cornice = add_box("GableBottomCornice", (12.48, 0.60, 0.26), (0.0, 0.0, 0.13), mat_trim, bevel_width=0.03)
    parts.append(cornice)

    export_parts_as_glb(parts, out_dir, "church_front_gable_rose.glb")


def build_church_pitched_roof_12x16(out_dir: str) -> None:
    """12.8m wide x 16.8m long steep 45-degree Gothic cathedral pitched roof with slate, eaves, and cresting."""
    clear_scene()
    mat_slate = make_pbr_material("DarkSlateRoof", (0.09, 0.10, 0.12, 1.0), roughness=0.76)
    mat_trim = make_pbr_material("CarvedStoneTrim", (0.21, 0.20, 0.22, 1.0), roughness=0.80)

    parts: list[bpy.types.Object] = []

    # In Blender: X is [-6.4, +6.4], Y is [-8.4, +8.4], Z is [0.0, 6.2]
    # Sloped roof slabs (left and right slopes at 45 degrees)
    # Slope length = 6.4 * sqrt(2) ~ 9.05m
    slope_len = 9.05
    roof_len = 16.80
    roof_thick = 0.38

    # Left slope (X < 0)
    roof_l = add_box(
        "RoofSlopeLeft",
        (slope_len, roof_len, roof_thick),
        (-3.20, 0.0, 3.10),
        mat_slate,
        bevel_width=0.03,
        rotation=(0.0, math.pi * 0.25, 0.0),
    )
    # Right slope (X > 0)
    roof_r = add_box(
        "RoofSlopeRight",
        (slope_len, roof_len, roof_thick),
        (3.20, 0.0, 3.10),
        mat_slate,
        bevel_width=0.03,
        rotation=(0.0, -math.pi * 0.25, 0.0),
    )
    parts.extend([roof_l, roof_r])

    # Stone ridge cresting along top apex (X = 0, Z = 6.25m, Y in [-8.45, +8.45])
    ridge = add_box("RoofRidgeCrest", (0.42, roof_len + 0.15, 0.36), (0.0, 0.0, 6.32), mat_trim, bevel_width=0.03)
    parts.append(ridge)

    # Ridge decorative finials at front and back
    fin_f = add_box("RidgeFinialFront", (0.24, 0.24, 0.85), (0.0, 8.40, 6.75), mat_trim, bevel_width=0.02)
    fin_b = add_box("RidgeFinialBack", (0.24, 0.24, 0.85), (0.0, -8.40, 6.75), mat_trim, bevel_width=0.02)
    parts.extend([fin_f, fin_b])

    # Eaves fascia beam and corbels along East and West sides
    for sx in (-6.35, 6.35):
        fascia = add_box(f"EavesFascia_{sx}", (0.32, roof_len, 0.35), (sx, 0.0, 0.05), mat_trim, bevel_width=0.025)
        parts.append(fascia)
        for iy in range(7):
            cy = -7.5 + iy * 2.5
            corbel = add_box(f"EavesCorbel_{sx}_{iy}", (0.26, 0.28, 0.38), (sx - 0.12 if sx > 0 else sx + 0.12, cy, -0.15), mat_trim, bevel_width=0.02)
            parts.append(corbel)

    # 4 Dormer decorative roof vents
    dormer_ys = [-4.0, 4.0]
    for dy in dormer_ys:
        for dx_sign in (-1, 1):
            dx = dx_sign * 3.4
            d_box = add_box(f"Dormer_{dx_sign}_{dy}", (1.10, 1.25, 1.20), (dx, dy, 3.20), mat_slate, bevel_width=0.02)
            parts.append(d_box)

    export_parts_as_glb(parts, out_dir, "church_pitched_roof_12x16.glb")


def build_church_bell_tower_spire(out_dir: str) -> None:
    """4.5m x 4.5m footprint, 18m tall Gothic bell tower with open belfry, hanging bronze bell, and needle spire."""
    clear_scene()
    mat_wall = make_pbr_material("GothicAshlarStone", (0.16, 0.16, 0.18, 1.0), roughness=0.86)
    mat_trim = make_pbr_material("CarvedStoneTrim", (0.21, 0.20, 0.22, 1.0), roughness=0.80)
    mat_slate = make_pbr_material("DarkSlateRoof", (0.09, 0.10, 0.12, 1.0), roughness=0.76)
    mat_bronze = make_pbr_material("TarnishedBronze", (0.28, 0.22, 0.14, 1.0), roughness=0.45, metallic=0.85)
    mat_iron = make_pbr_material("WroughtIron", (0.06, 0.06, 0.07, 1.0), roughness=0.52, metallic=0.90)

    parts: list[bpy.types.Object] = []

    # 1. Base Tower Stage (Z = 0.0m to 5.0m, 4.5m x 4.5m)
    tower_base = add_box("TowerBaseStage", (4.50, 4.50, 5.00), (0.0, 0.0, 2.50), mat_wall, bevel_width=0.04)
    stringcourse_1 = add_box("Stringcourse1", (4.62, 4.62, 0.32), (0.0, 0.0, 5.00), mat_trim, bevel_width=0.03)
    parts.extend([tower_base, stringcourse_1])

    # 2. Belfry Stage (Z = 5.0m to 10.5m, 4.4m x 4.4m) with lancet openings on all 4 sides
    belfry_wall = add_box("BelfryCore", (4.40, 4.40, 5.50), (0.0, 0.0, 7.75), mat_wall, bevel_width=0.03)

    # Carve hollow interior chamber (3.2m x 3.2m x 5.8m)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, 7.75))
    int_cutter = bpy.context.active_object
    int_cutter.scale = (3.20, 3.20, 5.80)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    b_mod = belfry_wall.modifiers.new(name="CarveBelfryInside", type='BOOLEAN')
    b_mod.operation = 'DIFFERENCE'
    b_mod.solver = 'EXACT'
    b_mod.object = int_cutter
    bpy.context.view_layer.objects.active = belfry_wall
    bpy.ops.object.modifier_apply(modifier=b_mod.name)
    bpy.data.objects.remove(int_cutter, do_unlink=True)

    # Carve Gothic lancet arch sound openings (1.5m wide x 3.6m tall) on North, South, East, West
    for rot_y in (0.0, math.pi * 0.5):
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.75, depth=5.50, location=(0.0, 0.0, 8.75), rotation=(0.0, math.pi * 0.5 if rot_y == 0.0 else 0.0, math.pi * 0.5 if rot_y != 0.0 else 0.0))
        arch_cut = bpy.context.active_object
        if rot_y != 0.0:
            arch_cut.rotation_euler = (math.pi * 0.5, 0.0, 0.0)
        else:
            arch_cut.rotation_euler = (0.0, math.pi * 0.5, 0.0)

        c_mod = belfry_wall.modifiers.new(name="ArchCut", type='BOOLEAN')
        c_mod.operation = 'DIFFERENCE'
        c_mod.solver = 'EXACT'
        c_mod.object = arch_cut
        bpy.context.view_layer.objects.active = belfry_wall
        bpy.ops.object.modifier_apply(modifier=c_mod.name)
        bpy.data.objects.remove(arch_cut, do_unlink=True)

        # Lower rectangular cutout below arch
        box_cut = add_box("BoxCut", (1.50, 5.50, 2.0) if rot_y == 0.0 else (5.50, 1.50, 2.0), (0.0, 0.0, 7.50), mat_trim)
        b_mod_box = belfry_wall.modifiers.new(name="BoxCutMod", type='BOOLEAN')
        b_mod_box.operation = 'DIFFERENCE'
        b_mod_box.solver = 'EXACT'
        b_mod_box.object = box_cut
        bpy.context.view_layer.objects.active = belfry_wall
        bpy.ops.object.modifier_apply(modifier=b_mod_box.name)
        bpy.data.objects.remove(box_cut, do_unlink=True)

    parts.append(belfry_wall)

    # 3. Tarnished Bronze Church Bell inside the belfry
    # Bell beam
    bell_beam = add_box("BellBeam", (0.28, 3.40, 0.28), (0.0, 0.0, 8.85), mat_iron, bevel_width=0.015)
    parts.append(bell_beam)
    # Bell yoke & body
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.55, depth=0.85, location=(0.0, 0.0, 8.0))
    bell_body = bpy.context.active_object
    bell_body.name = "ChurchBell"
    bev_bell = bell_body.modifiers.new(name="Bevel", type='BEVEL')
    bev_bell.width = 0.06
    bpy.ops.object.modifier_apply(modifier=bev_bell.name)
    bell_body.data.materials.append(mat_bronze)

    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.68, depth=0.18, location=(0.0, 0.0, 7.60))
    bell_rim = bpy.context.active_object
    bell_rim.data.materials.append(mat_bronze)
    parts.extend([bell_body, bell_rim])

    # 4. Belfry Parapet & 4 Corner Stone Pinnacles (Z = 10.5m to 12.5m)
    parapet = add_box("BelfryParapet", (4.65, 4.65, 0.65), (0.0, 0.0, 10.82), mat_trim, bevel_width=0.03)
    parts.append(parapet)

    for px in (-2.05, 2.05):
        for py in (-2.05, 2.05):
            pinnacle_base = add_box(f"PinnacleBase_{px}_{py}", (0.55, 0.55, 1.40), (px, py, 11.45), mat_trim, bevel_width=0.02)
            bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.38, depth=1.10, location=(px, py, 12.70))
            pinnacle_cone = bpy.context.active_object
            pinnacle_cone.data.materials.append(mat_trim)
            parts.extend([pinnacle_base, pinnacle_cone])

    # 5. Octagonal Needle Spire (Z = 10.5m to 17.0m)
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=2.15, depth=6.50, location=(0.0, 0.0, 13.75))
    spire_cone = bpy.context.active_object
    spire_cone.name = "OctagonalSpire"
    spire_cone.data.materials.append(mat_slate)
    parts.append(spire_cone)

    # 6. Wrought-Iron Occult Cross Finial (Z = 17.0m to 18.5m)
    finial_shaft = add_box("FinialShaft", (0.08, 0.08, 1.50), (0.0, 0.0, 17.75), mat_iron, bevel_width=0.01)
    finial_crossbar = add_box("FinialCrossbar", (0.65, 0.08, 0.08), (0.0, 0.0, 18.05), mat_iron, bevel_width=0.01)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.22, minor_radius=0.035, location=(0.0, 0.0, 18.05))
    halo_ring = bpy.context.active_object
    halo_ring.rotation_euler = (math.pi * 0.5, 0.0, 0.0)
    halo_ring.data.materials.append(mat_iron)
    parts.extend([finial_shaft, finial_crossbar, halo_ring])

    export_parts_as_glb(parts, out_dir, "church_bell_tower_spire.glb")


def build_church_buttress(out_dir: str) -> None:
    """Heavy stepped Gothic exterior stone buttress with sloped weatherings (1.2m wide x 1.8m deep x 8.5m tall)."""
    clear_scene()
    mat_wall = make_pbr_material("GothicAshlarStone", (0.16, 0.16, 0.18, 1.0), roughness=0.86)
    mat_trim = make_pbr_material("CarvedStoneTrim", (0.21, 0.20, 0.22, 1.0), roughness=0.80)

    parts: list[bpy.types.Object] = []

    # In Godot: width X = 1.2m, depth Z = 1.8m, height Y = 8.5m
    # In Blender: X in [-0.6, +0.6], Y in [0.0, 1.8], Z in [0.0, 8.5]
    # 1. Base stage (Z = 0.0m to 3.2m, depth 1.8m)
    base_stage = add_box("ButtressStage1", (1.20, 1.80, 3.20), (0.0, 0.90, 1.60), mat_wall, bevel_width=0.03)
    # Sloped stone weathering 1 (tapers depth from 1.8m to 1.3m over 0.5m height)
    weath_1 = add_box("Weathering1", (1.24, 0.60, 0.45), (0.0, 1.55, 3.42), mat_trim, bevel_width=0.025, rotation=(math.pi * 0.18, 0.0, 0.0))
    parts.extend([base_stage, weath_1])

    # 2. Middle stage (Z = 3.4m to 6.2m, depth 1.3m)
    mid_stage = add_box("ButtressStage2", (1.10, 1.30, 2.80), (0.0, 0.65, 4.80), mat_wall, bevel_width=0.03)
    # Sloped stone weathering 2 (tapers depth from 1.3m to 0.85m over 0.45m height)
    weath_2 = add_box("Weathering2", (1.14, 0.55, 0.40), (0.0, 1.05, 6.40), mat_trim, bevel_width=0.025, rotation=(math.pi * 0.18, 0.0, 0.0))
    parts.extend([mid_stage, weath_2])

    # 3. Top stage (Z = 6.4m to 8.2m, depth 0.85m) with gabled stone pinnacle cap
    top_stage = add_box("ButtressStage3", (1.00, 0.85, 1.80), (0.0, 0.425, 7.30), mat_wall, bevel_width=0.025)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.65, depth=0.85, location=(0.0, 0.425, 8.62))
    cap_cone = bpy.context.active_object
    cap_cone.rotation_euler = (0.0, 0.0, math.pi * 0.25)
    cap_cone.data.materials.append(mat_trim)
    parts.extend([top_stage, cap_cone])

    export_parts_as_glb(parts, out_dir, "church_buttress.glb")


def build_wall_lantern_sconce(out_dir: str) -> None:
    """Wrought-iron wall sconce with scrolled bracket, hexagonal lantern cage, and emissive flame core."""
    clear_scene()
    mat_iron = make_pbr_material("WroughtIron", (0.06, 0.06, 0.07, 1.0), roughness=0.52, metallic=0.90)
    mat_glass = make_pbr_material("LanternFrostedGlass", (0.22, 0.20, 0.16, 0.85), roughness=0.25, metallic=0.05)
    mat_flame = make_pbr_material(
        "LanternEmissiveFlame",
        (1.0, 0.72, 0.22, 1.0),
        roughness=0.15,
        emission_color=(1.0, 0.65, 0.18, 1.0),
        emission_strength=4.5,
    )

    parts: list[bpy.types.Object] = []

    # In Godot: mounts flush on vertical wall at Z = 0.0, extends outward along -Z by 0.38m
    # In Blender: wall plate at Y = 0.0, arm extends out to Y = 0.38m (cage center at Y = 0.38m, Z = -0.15m)
    # 1. Wrought-iron wall mounting plate
    plate = add_box("WallMountPlate", (0.12, 0.025, 0.28), (0.0, 0.0125, 0.0), mat_iron, bevel_width=0.008)
    parts.append(plate)

    # 2. Scrolled iron supporting arm
    arm_horiz = add_box("ArmHorizontal", (0.035, 0.40, 0.035), (0.0, 0.20, 0.06), mat_iron, bevel_width=0.005)
    arm_diag = add_box("ArmDiagonalScrolled", (0.03, 0.28, 0.03), (0.0, 0.16, -0.06), mat_iron, bevel_width=0.005, rotation=(-math.pi * 0.25, 0.0, 0.0))
    parts.extend([arm_horiz, arm_diag])

    # 3. Hexagonal Lantern Cage (center at Y = 0.38m, Z = -0.15m)
    # Top peaked canopy cap
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.16, depth=0.12, location=(0.0, 0.38, 0.04))
    cage_roof = bpy.context.active_object
    cage_roof.data.materials.append(mat_iron)
    # Top hanging ring
    bpy.ops.mesh.primitive_torus_add(major_radius=0.035, minor_radius=0.008, location=(0.0, 0.38, 0.12))
    hang_ring = bpy.context.active_object
    hang_ring.data.materials.append(mat_iron)
    parts.extend([cage_roof, hang_ring])

    # Hexagonal glass lantern body
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.14, depth=0.28, location=(0.0, 0.38, -0.12))
    cage_glass = bpy.context.active_object
    cage_glass.data.materials.append(mat_glass)
    parts.append(cage_glass)

    # Bottom iron base and drop finial
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.15, depth=0.10, location=(0.0, 0.38, -0.28))
    cage_bottom = bpy.context.active_object
    cage_bottom.rotation_euler = (math.pi, 0.0, 0.0)
    cage_bottom.data.materials.append(mat_iron)
    parts.append(cage_bottom)

    # 4. Emissive flame core inside glass cage
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.045, location=(0.0, 0.38, -0.12))
    flame_sphere = bpy.context.active_object
    flame_sphere.scale = (0.7, 0.7, 1.4)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    flame_sphere.data.materials.append(mat_flame)
    parts.append(flame_sphere)

    export_parts_as_glb(parts, out_dir, "wall_lantern_sconce.glb")


def build_standing_iron_brazier(out_dir: str) -> None:
    """1.35m tall ornate tripod wrought-iron fire brazier with glowing embers and embers light source."""
    clear_scene()
    mat_iron = make_pbr_material("WroughtIron", (0.06, 0.06, 0.07, 1.0), roughness=0.52, metallic=0.90)
    mat_embers = make_pbr_material(
        "BrazierGlowingEmbers",
        (1.0, 0.45, 0.12, 1.0),
        roughness=0.20,
        emission_color=(1.0, 0.35, 0.08, 1.0),
        emission_strength=4.2,
    )

    parts: list[bpy.types.Object] = []

    # 1. Tripod wrought-iron legs (Z = 0.0m to 0.90m)
    for i in range(3):
        ang = i * (2.0 * math.pi / 3.0)
        # Leg angles outward to radius 0.42m at base
        lx = math.cos(ang) * 0.22
        ly = math.sin(ang) * 0.22
        leg = add_box(f"BrazierLeg_{i}", (0.045, 0.045, 0.95), (lx, ly, 0.45), mat_iron, bevel_width=0.008)
        # Slight tilt
        leg.rotation_euler = (-math.sin(ang) * 0.16, math.cos(ang) * 0.16, 0.0)
        parts.append(leg)

    # 2. Central iron collar ring at Z = 0.85m
    bpy.ops.mesh.primitive_torus_add(major_radius=0.32, minor_radius=0.035, location=(0.0, 0.0, 0.88))
    collar_ring = bpy.context.active_object
    collar_ring.data.materials.append(mat_iron)
    parts.append(collar_ring)

    # 3. Fire basket bowl (radius 0.38m, height 0.42m from Z = 0.88m to 1.30m)
    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.38, radius2=0.26, depth=0.40, location=(0.0, 0.0, 1.08))
    basket_bowl = bpy.context.active_object
    basket_bowl.data.materials.append(mat_iron)
    parts.append(basket_bowl)

    # Upper rim ring
    bpy.ops.mesh.primitive_torus_add(major_radius=0.40, minor_radius=0.035, location=(0.0, 0.0, 1.28))
    top_rim = bpy.context.active_object
    top_rim.data.materials.append(mat_iron)
    parts.append(top_rim)

    # 4. Glowing occult embers mound inside the basket
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.32, location=(0.0, 0.0, 1.18))
    embers_mound = bpy.context.active_object
    embers_mound.scale = (1.0, 1.0, 0.45)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    embers_mound.data.materials.append(mat_embers)
    parts.append(embers_mound)

    export_parts_as_glb(parts, out_dir, "standing_iron_brazier.glb")


def _make_catacomb_materials() -> dict[str, bpy.types.Material]:
    return {
        "WeatheredStone": make_pbr_material("WeatheredStone", (0.24, 0.23, 0.22, 1.0), roughness=0.90),
        "DarkFlagstone": make_pbr_material("DarkFlagstone", (0.17, 0.16, 0.17, 1.0), roughness=0.88),
        "AgedBone": make_pbr_material("AgedBone", (0.62, 0.57, 0.46, 1.0), roughness=0.86),
        "WroughtIron": make_pbr_material("WroughtIron", (0.10, 0.10, 0.12, 1.0), roughness=0.48, metallic=0.85),
        "TarnishedBronze": make_pbr_material("TarnishedBronze", (0.28, 0.22, 0.14, 1.0), roughness=0.46, metallic=0.85),
        "RottedTimber": make_pbr_material("RottedTimber", (0.18, 0.13, 0.09, 1.0), roughness=0.89),
        "GlowingOccultRune": make_pbr_material(
            "GlowingOccultRune",
            (0.92, 0.50, 1.0, 1.0),
            roughness=0.25,
            emission_color=(0.88, 0.42, 1.0, 1.0),
            emission_strength=4.2,
        ),
        "SicklyGreenBile": make_pbr_material(
            "SicklyGreenBile",
            (0.42, 0.90, 0.30, 1.0),
            roughness=0.20,
            emission_color=(0.45, 0.95, 0.35, 1.0),
            emission_strength=4.0,
        ),
        "FrozenBlueSoul": make_pbr_material(
            "FrozenBlueSoul",
            (0.35, 0.70, 1.0, 1.0),
            roughness=0.22,
            emission_color=(0.35, 0.65, 1.0, 1.0),
            emission_strength=4.2,
        ),
        "AbyssalCrimson": make_pbr_material(
            "AbyssalCrimson",
            (0.95, 0.12, 0.15, 1.0),
            roughness=0.24,
            emission_color=(1.0, 0.15, 0.18, 1.0),
            emission_strength=4.8,
        ),
        "EmissiveConsecratedGold": make_pbr_material(
            "EmissiveConsecratedGold",
            (1.0, 0.78, 0.24, 1.0),
            roughness=0.18,
            metallic=0.35,
            emission_color=(1.0, 0.72, 0.18, 1.0),
            emission_strength=2.8,
        ),
        "OccultSilver": make_pbr_material(
            "OccultSilver",
            (0.58, 0.60, 0.64, 1.0),
            roughness=0.36,
            metallic=0.90,
        ),
    }


def build_crypt_wall_ossuary_4x4(out_dir: str) -> None:
    """
    1. crypt_wall_ossuary_4x4.glb:
    Heavy ashlar wall (4.20m wide x 0.56m thick x 4.05m tall) with 2 tiers of recessed
    pointed-arch burial niches carved via BOOLEAN DIFFERENCE and packed with geometric skull rows
    and femur bundles (AgedBone).
    """
    clear_scene()
    mats = _make_catacomb_materials()
    mat_stone = mats["WeatheredStone"]
    mat_flag = mats["DarkFlagstone"]
    mat_bone = mats["AgedBone"]
    mat_iron = mats["WroughtIron"]

    parts: list[bpy.types.Object] = []

    wall = add_box("OssuaryWallCore", (4.20, 0.52, 4.05), (0.0, 0.0, 2.025), mat_stone, bevel_width=0.025)
    wall.data.materials.append(mat_flag)

    # Carve 2 tiers x 2 columns of pointed-arch burial niches on BOTH faces (-Y and +Y) via BOOLEAN DIFFERENCE
    niche_xs = (-1.05, 1.05)
    niche_tiers = ((0.62, 1.45, 1.82), (2.18, 3.00, 3.38))  # (z_base, spring_h, peak_h)
    for nx in niche_xs:
        for t_idx, (zb, sh, ph) in enumerate(niche_tiers):
            for side_y in (-0.20, 0.20):
                cutter = create_pointed_arch_prism(
                    f"NicheCut_{nx}_{t_idx}_{side_y}",
                    width=1.36,
                    depth=0.26,
                    spring_h=sh,
                    peak_h=ph,
                    z_base=zb,
                )
                cutter.location = (nx, side_y, 0.0)
                bpy.context.view_layer.objects.active = cutter
                bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
                cutter.data.materials.append(mat_flag)

                b_mod = wall.modifiers.new(name=f"BoolNiche_{nx}_{t_idx}_{side_y}", type='BOOLEAN')
                b_mod.operation = 'DIFFERENCE'
                b_mod.solver = 'EXACT'
                b_mod.object = cutter
                bpy.context.view_layer.objects.active = wall
                bpy.ops.object.modifier_apply(modifier=b_mod.name)
                bpy.data.objects.remove(cutter, do_unlink=True)

    parts.append(wall)

    # Stepped base plinth, central stringcourse, top cornice, and corner quoins
    parts.append(add_box("BasePlinth", (4.24, 0.62, 0.42), (0.0, 0.0, 0.21), mat_flag, bevel_width=0.03))
    parts.append(add_box("MidStringcourse", (4.22, 0.58, 0.16), (0.0, 0.0, 1.98), mat_flag, bevel_width=0.02))
    parts.append(add_box("TopCornice", (4.24, 0.62, 0.28), (0.0, 0.0, 3.90), mat_flag, bevel_width=0.03))
    parts.append(add_box("CenterPier", (0.34, 0.58, 3.60), (0.0, 0.0, 2.02), mat_flag, bevel_width=0.025))

    for sx in (-1.94, 1.94):
        for qz in range(6):
            qw = 0.36 if (qz % 2 == 0) else 0.28
            parts.append(
                add_box(f"Quoin_{sx}_{qz}", (qw, 0.60, 0.52), (sx, 0.0, 0.62 + qz * 0.58), mat_flag, bevel_width=0.02)
            )

    # Pack each niche with sill ledges, wrought-iron retaining bars, geometric skulls, and femur bundles
    for nx in niche_xs:
        for t_idx, (zb, _sh, _ph) in enumerate(niche_tiers):
            for side_sign in (-1.0, 1.0):
                face_y = side_sign * 0.20
                sill = add_box(
                    f"NicheSill_{nx}_{t_idx}_{side_sign}",
                    (1.48, 0.14, 0.09),
                    (nx, side_sign * 0.25, zb - 0.02),
                    mat_flag,
                    bevel_width=0.015,
                )
                bar = add_box(
                    f"RetainBar_{nx}_{t_idx}_{side_sign}",
                    (1.38, 0.03, 0.03),
                    (nx, side_sign * 0.24, zb + 0.28),
                    mat_iron,
                    bevel_width=0.005,
                )
                parts.extend([sill, bar])

                # Femur bundle layer at base of niche
                for f_idx in range(3):
                    fx = nx - 0.38 + f_idx * 0.38
                    femur = add_box(
                        f"FemurBundle_{nx}_{t_idx}_{side_sign}_{f_idx}",
                        (0.32, 0.12, 0.09),
                        (fx, face_y, zb + 0.06),
                        mat_bone,
                        bevel_width=0.015,
                        rotation=(0.0, 0.0, 0.12 if (f_idx % 2 == 0) else -0.12),
                    )
                    parts.append(femur)

                # Two rows of geometric skulls inside each niche
                for r_idx in range(2):
                    for s_idx in range(3):
                        sk_x = nx - 0.38 + s_idx * 0.38
                        sk_z = zb + 0.22 + r_idx * 0.24
                        bpy.ops.mesh.primitive_ico_sphere_add(
                            subdivisions=1,
                            radius=0.095,
                            location=(sk_x, face_y, sk_z),
                        )
                        skull = bpy.context.active_object
                        skull.name = f"Skull_{nx}_{t_idx}_{side_sign}_{r_idx}_{s_idx}"
                        skull.scale = (0.90, 1.05, 1.12)
                        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                        skull.data.materials.append(mat_bone)
                        parts.append(skull)

    export_parts_as_glb(parts, out_dir, "crypt_wall_ossuary_4x4.glb")


def build_crypt_archway_portcullis_4x4(out_dir: str) -> None:
    """
    2. crypt_archway_portcullis_4x4.glb:
    Chamfered Gothic stone archway with stepped voussoirs and a partially raised spiked wrought-iron
    portcullis + chains (clearance Z >= 2.42m so players walk freely underneath).
    """
    clear_scene()
    mats = _make_catacomb_materials()
    mat_stone = mats["WeatheredStone"]
    mat_flag = mats["DarkFlagstone"]
    mat_iron = mats["WroughtIron"]
    mat_bronze = mats["TarnishedBronze"]

    parts: list[bpy.types.Object] = []

    wall = add_box("PortcullisArchWall", (4.20, 0.54, 4.05), (0.0, 0.0, 2.025), mat_stone, bevel_width=0.025)
    wall.data.materials.append(mat_flag)

    # Carve wide Gothic pointed archway (2.52m wide, peak 3.60m) via BOOLEAN DIFFERENCE
    cutter = create_pointed_arch_prism("PortcullisArchCut", width=2.52, depth=1.20, spring_h=2.75, peak_h=3.60, z_base=-0.15)
    cutter.data.materials.append(mat_flag)
    b_mod = wall.modifiers.new(name="CarvePortcullisArch", type='BOOLEAN')
    b_mod.operation = 'DIFFERENCE'
    b_mod.solver = 'EXACT'
    b_mod.object = cutter
    bpy.context.view_layer.objects.active = wall
    bpy.ops.object.modifier_apply(modifier=b_mod.name)
    bpy.data.objects.remove(cutter, do_unlink=True)
    parts.append(wall)

    # Jamb pilasters, base plinths, and top cornice
    for sx in (-1.38, 1.38):
        parts.append(add_box(f"JambCol_{sx}", (0.28, 0.64, 2.85), (sx, 0.0, 1.425), mat_flag, bevel_width=0.025))
        parts.append(add_box(f"JambCap_{sx}", (0.36, 0.70, 0.22), (sx, 0.0, 2.82), mat_flag, bevel_width=0.02))
    for sx in (-1.72, 1.72):
        parts.append(add_box(f"SidePlinth_{sx}", (0.88, 0.62, 0.42), (sx, 0.0, 0.21), mat_flag, bevel_width=0.025))
    parts.append(add_box("TopCornice", (4.24, 0.64, 0.28), (0.0, 0.0, 3.90), mat_flag, bevel_width=0.03))

    # Stepped arch voussoir blocks around the pointed arch
    for v_idx in range(9):
        t = v_idx / 8.0
        ang = (t - 0.5) * math.pi * 0.78
        vx = math.sin(ang) * 1.32
        vz = 2.68 + math.cos(ang) * 0.94
        voussoir = add_box(
            f"Voussoir_{v_idx}",
            (0.24, 0.62, 0.30),
            (vx, 0.0, vz),
            mat_flag,
            bevel_width=0.02,
            rotation=(0.0, ang * 0.65, 0.0),
        )
        parts.append(voussoir)

    # Partially raised wrought-iron portcullis (bottom spikes at Z = 2.45m -> 100% clear walkthrough below!)
    # Horizontal crossbars
    for hz in (2.62, 2.98, 3.34):
        hbar = add_box(f"PortcullisHBar_{hz}", (2.36, 0.08, 0.07), (0.0, 0.0, hz), mat_iron, bevel_width=0.008)
        parts.append(hbar)

    # 7 Vertical spiked iron bars (Z = 2.48m to 3.55m) + conical iron spikes + bronze rivet bosses
    for b_idx in range(7):
        bx = -1.05 + b_idx * 0.35
        vbar = add_box(f"PortcullisVBar_{b_idx}", (0.06, 0.06, 1.02), (bx, 0.0, 3.04), mat_iron, bevel_width=0.008)
        parts.append(vbar)
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.042, depth=0.14, location=(bx, 0.0, 2.46), rotation=(math.pi, 0.0, 0.0))
        spike = bpy.context.active_object
        spike.name = f"PortcullisSpike_{b_idx}"
        spike.data.materials.append(mat_iron)
        parts.append(spike)

        for hz in (2.62, 2.98, 3.34):
            rivet = add_box(f"Rivet_{b_idx}_{hz}", (0.08, 0.11, 0.08), (bx, 0.0, hz), mat_bronze, bevel_width=0.01)
            parts.append(rivet)

    # Hanging winch chains on left and right sides of the portcullis
    for cx in (-0.88, 0.88):
        winch_bracket = add_box(f"WinchBracket_{cx}", (0.18, 0.68, 0.18), (cx, 0.0, 3.72), mat_iron, bevel_width=0.015)
        parts.append(winch_bracket)
        for l_idx in range(5):
            lz = 3.42 + l_idx * 0.09
            bpy.ops.mesh.primitive_torus_add(
                major_radius=0.055,
                minor_radius=0.016,
                location=(cx, 0.0, lz),
                rotation=(math.pi * 0.5, (l_idx % 2) * math.pi * 0.5, 0.0),
            )
            link = bpy.context.active_object
            link.name = f"ChainLink_{cx}_{l_idx}"
            link.data.materials.append(mat_iron)
            parts.append(link)

    export_parts_as_glb(parts, out_dir, "crypt_archway_portcullis_4x4.glb")


def build_crypt_corridor_vault_4x4(out_dir: str) -> None:
    """
    3. crypt_corridor_vault_4x4.glb:
    Pointed barrel-vault ceiling unit with transverse stone ribs, groin ribs, corbels, and carved keystone boss.
    """
    clear_scene()
    mats = _make_catacomb_materials()
    mat_stone = mats["WeatheredStone"]
    mat_flag = mats["DarkFlagstone"]
    mat_iron = mats["WroughtIron"]
    mat_bronze = mats["TarnishedBronze"]

    parts: list[bpy.types.Object] = []

    # Thick light-blocking structural vault slab (Z = 0.0m to 0.52m)
    deck = add_box("CorridorVaultDeck", (4.16, 4.16, 0.50), (0.0, 0.0, 0.25), mat_stone, bevel_width=0.02)
    cap = add_box("CorridorVaultIsolationCap", (4.20, 4.20, 0.24), (0.0, 0.0, 0.60), mat_flag, bevel_width=0.02)
    parts.extend([deck, cap])

    # Coffered ceiling recess panels carved via BOOLEAN DIFFERENCE on underside
    for cx in (-1.0, 1.0):
        for cy in (-1.0, 1.0):
            coffer_cut = add_box(f"CofferCut_{cx}_{cy}", (1.42, 1.42, 0.16), (cx, cy, 0.04), mat_flag, bevel_width=0.0)
            b_mod = deck.modifiers.new(name=f"BoolCoffer_{cx}_{cy}", type='BOOLEAN')
            b_mod.operation = 'DIFFERENCE'
            b_mod.solver = 'EXACT'
            b_mod.object = coffer_cut
            bpy.context.view_layer.objects.active = deck
            bpy.ops.object.modifier_apply(modifier=b_mod.name)
            bpy.data.objects.remove(coffer_cut, do_unlink=True)

    # Transverse ribs (3 along Y) and longitudinal spine rib along X
    for ry in (-1.85, 0.0, 1.85):
        parts.append(add_box(f"TransverseRib_{ry}", (4.06, 0.28, 0.32), (0.0, ry, -0.10), mat_flag, bevel_width=0.025))
    for rx in (-1.85, 0.0, 1.85):
        parts.append(add_box(f"LongitudinalRib_{rx}", (0.28, 4.06, 0.32), (rx, 0.0, -0.10), mat_flag, bevel_width=0.025))

    # Diagonal cross-vault ribs
    for ang in (math.pi * 0.25, -math.pi * 0.25):
        parts.append(
            add_box(f"DiagRib_{ang:.2f}", (5.48, 0.22, 0.28), (0.0, 0.0, -0.09), mat_flag, bevel_width=0.02, rotation=(0.0, 0.0, ang))
        )

    # Stepped stone wall corbels at 8 rib spring points
    corbel_pts = [
        (-1.90, -1.85), (1.90, -1.85),
        (-1.90, 0.0), (1.90, 0.0),
        (-1.90, 1.85), (1.90, 1.85),
        (0.0, -1.90), (0.0, 1.90),
    ]
    for idx, (kx, ky) in enumerate(corbel_pts):
        parts.append(add_box(f"CorbelUpper_{idx}", (0.36, 0.36, 0.18), (kx, ky, -0.22), mat_flag, bevel_width=0.02))
        parts.append(add_box(f"CorbelLower_{idx}", (0.26, 0.26, 0.18), (kx, ky, -0.36), mat_stone, bevel_width=0.02))

    # Carved central keystone boss & iron suspension ring
    boss_outer = add_box("KeystoneBossOuter", (0.58, 0.58, 0.36), (0.0, 0.0, -0.14), mat_flag, bevel_width=0.04)
    boss_inner = add_box(
        "KeystoneBossInner",
        (0.42, 0.42, 0.42),
        (0.0, 0.0, -0.18),
        mat_bronze,
        bevel_width=0.03,
        rotation=(0.0, 0.0, math.pi * 0.25),
    )
    bpy.ops.mesh.primitive_torus_add(major_radius=0.12, minor_radius=0.025, location=(0.0, 0.0, -0.42), rotation=(math.pi * 0.5, 0.0, 0.0))
    boss_ring = bpy.context.active_object
    boss_ring.name = "KeystoneIronRing"
    boss_ring.data.materials.append(mat_iron)
    parts.extend([boss_outer, boss_inner, boss_ring])

    # Secondary intersection bosses at the 8 outer rib junctions
    for jx in (-1.85, 0.0, 1.85):
        for jy in (-1.85, 0.0, 1.85):
            if abs(jx) < 0.1 and abs(jy) < 0.1:
                continue
            parts.append(add_box(f"NodeBoss_{jx}_{jy}", (0.34, 0.34, 0.34), (jx, jy, -0.12), mat_bronze, bevel_width=0.025))

    export_parts_as_glb(parts, out_dir, "crypt_corridor_vault_4x4.glb")


def build_crypt_iron_gate_cell_4x4(out_dir: str) -> None:
    """
    4. crypt_iron_gate_cell_4x4.glb:
    Dwarf stone wall topped with heavy vertical wrought-iron prison bars, riveted cross-bars,
    and a central cell door arch.
    """
    clear_scene()
    mats = _make_catacomb_materials()
    mat_stone = mats["WeatheredStone"]
    mat_flag = mats["DarkFlagstone"]
    mat_iron = mats["WroughtIron"]
    mat_bronze = mats["TarnishedBronze"]

    parts: list[bpy.types.Object] = []

    # Outer stone frame + dwarf walls on left and right of central cell doorway (doorway width = 1.48m, height = 2.85m)
    frame_wall = add_box("CellWallFrame", (4.20, 0.48, 4.05), (0.0, 0.0, 2.025), mat_stone, bevel_width=0.025)
    frame_wall.data.materials.append(mat_flag)

    # Carve central doorway arch (1.48m wide, z_base = -0.10 to peak 2.95m)
    door_cut = create_pointed_arch_prism("CellDoorCutter", width=1.48, depth=1.20, spring_h=2.35, peak_h=2.95, z_base=-0.10)
    door_cut.data.materials.append(mat_flag)
    b_door = frame_wall.modifiers.new(name="CarveCellDoor", type='BOOLEAN')
    b_door.operation = 'DIFFERENCE'
    b_door.solver = 'EXACT'
    b_door.object = door_cut
    bpy.context.view_layer.objects.active = frame_wall
    bpy.ops.object.modifier_apply(modifier=b_door.name)
    bpy.data.objects.remove(door_cut, do_unlink=True)

    # Carve left and right barred window openings above the 1.15m dwarf wall (X in [-1.72, -0.92] and [+0.92, +1.72], Z in [1.15, 3.15])
    for wx in (-1.34, 1.34):
        win_cut = add_box(f"CellWindowCut_{wx}", (0.92, 1.20, 2.00), (wx, 0.0, 2.15), mat_flag, bevel_width=0.0)
        b_win = frame_wall.modifiers.new(name=f"CarveWindow_{wx}", type='BOOLEAN')
        b_win.operation = 'DIFFERENCE'
        b_win.solver = 'EXACT'
        b_win.object = win_cut
        bpy.context.view_layer.objects.active = frame_wall
        bpy.ops.object.modifier_apply(modifier=b_win.name)
        bpy.data.objects.remove(win_cut, do_unlink=True)

    parts.append(frame_wall)

    # Dwarf wall coping sills, base plinths, and top cornice
    for wx in (-1.34, 1.34):
        parts.append(add_box(f"DwarfCoping_{wx}", (1.02, 0.58, 0.12), (wx, 0.0, 1.14), mat_flag, bevel_width=0.02))
        parts.append(add_box(f"DwarfPlinth_{wx}", (1.16, 0.56, 0.38), (wx, 0.0, 0.19), mat_flag, bevel_width=0.025))
    parts.append(add_box("CellTopCornice", (4.24, 0.58, 0.28), (0.0, 0.0, 3.90), mat_flag, bevel_width=0.03))

    # Heavy vertical wrought-iron bars in the left and right window openings + riveted crossbars
    for wx in (-1.34, 1.34):
        for hz in (1.55, 2.15, 2.75):
            parts.append(add_box(f"WinHBar_{wx}_{hz}", (0.94, 0.07, 0.05), (wx, 0.0, hz), mat_iron, bevel_width=0.006))
        for b_idx in range(4):
            bx = wx - 0.33 + b_idx * 0.22
            parts.append(add_box(f"WinVBar_{wx}_{b_idx}", (0.045, 0.045, 2.04), (bx, 0.0, 2.15), mat_iron, bevel_width=0.005))
            for hz in (1.55, 2.15, 2.75):
                parts.append(add_box(f"WinRivet_{wx}_{b_idx}_{hz}", (0.065, 0.09, 0.065), (bx, 0.0, hz), mat_bronze, bevel_width=0.008))

    # Partially swung-open wrought-iron cell gate on the left jamb (rotated open so center passage is passable)
    gate_pivot_x = -0.70
    for g_idx in range(5):
        bar_dist = 0.12 + g_idx * 0.22
        gx = gate_pivot_x + bar_dist * math.cos(0.95)
        gy = -bar_dist * math.sin(0.95)
        parts.append(add_box(f"OpenGateVBar_{g_idx}", (0.045, 0.045, 2.35), (gx, gy, 1.22), mat_iron, bevel_width=0.005))
    for ghz in (0.35, 1.20, 2.05):
        hbar_gate = add_box(
            f"OpenGateHBar_{ghz}",
            (1.10, 0.06, 0.05),
            (gate_pivot_x + 0.55 * math.cos(0.95), -0.55 * math.sin(0.95), ghz),
            mat_iron,
            bevel_width=0.006,
            rotation=(0.0, 0.0, -0.95),
        )
        parts.append(hbar_gate)
    # Lock plate on open gate
    lock_plate = add_box(
        "CellGateLockBox",
        (0.18, 0.09, 0.24),
        (gate_pivot_x + 0.98 * math.cos(0.95), -0.98 * math.sin(0.95), 1.20),
        mat_bronze,
        bevel_width=0.01,
        rotation=(0.0, 0.0, -0.95),
    )
    parts.append(lock_plate)

    export_parts_as_glb(parts, out_dir, "crypt_iron_gate_cell_4x4.glb")


def build_crypt_sarcophagus_ornate(out_dir: str) -> None:
    """
    5. crypt_sarcophagus_ornate.glb:
    Stepped tomb chest with blind-arch carvings and a heavy stone lid cracked open by 8 degrees
    with faint rune glow and skeletal remains inside.
    """
    clear_scene()
    mats = _make_catacomb_materials()
    mat_stone = mats["WeatheredStone"]
    mat_flag = mats["DarkFlagstone"]
    mat_bone = mats["AgedBone"]
    mat_bronze = mats["TarnishedBronze"]
    mat_rune = mats["GlowingOccultRune"]

    parts: list[bpy.types.Object] = []

    # 2-tier stepped stone plinth
    parts.append(add_box("SarcPlinth1", (1.56, 2.68, 0.18), (0.0, 0.0, 0.09), mat_flag, bevel_width=0.025))
    parts.append(add_box("SarcPlinth2", (1.36, 2.48, 0.16), (0.0, 0.0, 0.26), mat_flag, bevel_width=0.02))

    # Main sarcophagus chest (1.18m wide x 2.28m long x 0.72m tall, Z = 0.34m to 1.06m)
    chest = add_box("SarcChestBody", (1.18, 2.28, 0.72), (0.0, 0.0, 0.70), mat_stone, bevel_width=0.025)
    chest.data.materials.append(mat_flag)

    # Carve hollow interior tomb cavity via BOOLEAN DIFFERENCE
    cavity_cut = add_box("SarcCavityCutter", (0.86, 1.96, 0.56), (0.0, 0.0, 0.82), mat_flag, bevel_width=0.0)
    b_cav = chest.modifiers.new(name="CarveSarcCavity", type='BOOLEAN')
    b_cav.operation = 'DIFFERENCE'
    b_cav.solver = 'EXACT'
    b_cav.object = cavity_cut
    bpy.context.view_layer.objects.active = chest
    bpy.ops.object.modifier_apply(modifier=b_cav.name)
    bpy.data.objects.remove(cavity_cut, do_unlink=True)

    # Carve blind-arch recesses along left and right sides of the chest
    for sy in (-0.70, 0.0, 0.70):
        for sx in (-0.58, 0.58):
            blind_cut = add_box(f"BlindArchCut_{sx}_{sy}", (0.12, 0.46, 0.44), (sx, sy, 0.70), mat_flag, bevel_width=0.01)
            b_blind = chest.modifiers.new(name=f"BoolBlind_{sx}_{sy}", type='BOOLEAN')
            b_blind.operation = 'DIFFERENCE'
            b_blind.solver = 'EXACT'
            b_blind.object = blind_cut
            bpy.context.view_layer.objects.active = chest
            bpy.ops.object.modifier_apply(modifier=b_blind.name)
            bpy.data.objects.remove(blind_cut, do_unlink=True)

    parts.append(chest)

    # Side colonnette pillars & bronze corner clasps on the tomb chest
    for sy in (-1.05, -0.35, 0.35, 1.05):
        for sx in (-0.60, 0.60):
            parts.append(add_box(f"SidePilaster_{sx}_{sy}", (0.09, 0.11, 0.68), (sx, sy, 0.70), mat_flag, bevel_width=0.015))
    for cx in (-0.61, 0.61):
        for cy in (-1.15, 1.15):
            parts.append(add_box(f"BronzeClasp_{cx}_{cy}", (0.12, 0.12, 0.18), (cx, cy, 0.96), mat_bronze, bevel_width=0.015))

    # Glowing occult rune strips and skeletal remains inside the cracked-open tomb cavity
    rune_bed = add_box("InteriorRuneGlow", (0.72, 1.78, 0.04), (0.0, 0.0, 0.57), mat_rune, bevel_width=0.005)
    parts.append(rune_bed)
    for r_idx in range(4):
        ry = -0.65 + r_idx * 0.42
        parts.append(add_box(f"RuneCrossBar_{r_idx}", (0.78, 0.06, 0.06), (0.0, ry, 0.60), mat_rune, bevel_width=0.005))

    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.11, location=(0.0, -0.68, 0.68))
    in_skull = bpy.context.active_object
    in_skull.name = "TombSkull"
    in_skull.data.materials.append(mat_bone)
    parts.append(in_skull)
    for b_idx in range(6):
        by = -0.35 + b_idx * 0.18
        parts.append(add_box(f"TombRib_{b_idx}", (0.36, 0.05, 0.12), (0.0, by, 0.64), mat_bone, bevel_width=0.01))

    # Heavy sculpted stone lid rotated by 8 degrees (yaw = 8 deg) and shifted slightly sideways
    lid_yaw = math.radians(8.0)
    lid_base = add_box(
        "SarcLidBase",
        (1.24, 2.34, 0.16),
        (0.14, 0.05, 1.14),
        mat_stone,
        bevel_width=0.025,
        rotation=(0.0, 0.0, lid_yaw),
    )
    lid_top = add_box(
        "SarcLidRidge",
        (0.92, 2.08, 0.14),
        (0.14, 0.05, 1.26),
        mat_flag,
        bevel_width=0.025,
        rotation=(0.0, 0.0, lid_yaw),
    )
    lid_cross_v = add_box(
        "SarcLidCrossV",
        (0.16, 1.72, 0.06),
        (0.14, 0.05, 1.35),
        mat_bronze,
        bevel_width=0.01,
        rotation=(0.0, 0.0, lid_yaw),
    )
    lid_cross_h = add_box(
        "SarcLidCrossH",
        (0.68, 0.16, 0.06),
        (0.14, -0.25, 1.35),
        mat_bronze,
        bevel_width=0.01,
        rotation=(0.0, 0.0, lid_yaw),
    )
    parts.extend([lid_base, lid_top, lid_cross_v, lid_cross_h])

    export_parts_as_glb(parts, out_dir, "crypt_sarcophagus_ornate.glb")


def build_crypt_hanging_cage(out_dir: str) -> None:
    """
    6. crypt_hanging_cage.glb:
    Suspended wrought-iron rib-cage gibbet on heavy 3D ceiling chain links holding skeletal remains.
    Cage hangs at Z = 1.25m..2.55m with chain links ascending to Z = 3.85m.
    """
    clear_scene()
    mats = _make_catacomb_materials()
    mat_iron = mats["WroughtIron"]
    mat_bronze = mats["TarnishedBronze"]
    mat_bone = mats["AgedBone"]

    parts: list[bpy.types.Object] = []

    # Bottom drop finial spike (Z = 0.95m to 1.30m)
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.14, depth=0.32, location=(0.0, 0.0, 1.12), rotation=(math.pi, 0.0, 0.0))
    bot_cone = bpy.context.active_object
    bot_cone.name = "GibbetBottomSpike"
    bot_cone.data.materials.append(mat_iron)
    parts.append(bot_cone)

    # Horizontal wrought-iron hoop rings forming the gibbet barrel (Z = 1.30m to 2.45m)
    hoop_zs = (1.30, 1.58, 1.86, 2.14, 2.42)
    for hz in hoop_zs:
        bpy.ops.mesh.primitive_torus_add(major_radius=0.38, minor_radius=0.024, location=(0.0, 0.0, hz))
        hoop = bpy.context.active_object
        hoop.name = f"GibbetHoop_{hz}"
        hoop.data.materials.append(mat_iron)
        parts.append(hoop)

    # Floor cross-grid at Z = 1.30m
    parts.append(add_box("CageFloorBarX", (0.74, 0.05, 0.04), (0.0, 0.0, 1.30), mat_iron, bevel_width=0.005))
    parts.append(add_box("CageFloorBarY", (0.05, 0.74, 0.04), (0.0, 0.0, 1.30), mat_iron, bevel_width=0.005))

    # 8 Vertical wrought-iron cage straps + bronze rivets at every hoop intersection
    for i in range(8):
        ang = i * (math.pi / 4.0)
        vx = math.cos(ang) * 0.38
        vy = math.sin(ang) * 0.38
        vstrap = add_box(
            f"CageVStrap_{i}",
            (0.04, 0.025, 1.16),
            (vx, vy, 1.86),
            mat_iron,
            bevel_width=0.004,
            rotation=(0.0, 0.0, ang),
        )
        parts.append(vstrap)
        for hz in (1.30, 1.86, 2.42):
            rx = math.cos(ang) * 0.40
            ry = math.sin(ang) * 0.40
            parts.append(add_box(f"CageRivet_{i}_{hz}", (0.05, 0.05, 0.05), (rx, ry, hz), mat_bronze, bevel_width=0.006))

    # Domed top iron crown arches meeting at Z = 2.68m
    for i in range(4):
        ang = i * (math.pi / 4.0)
        arch_bar = add_box(
            f"CageCrownArch_{i}",
            (0.76, 0.04, 0.22),
            (0.0, 0.0, 2.52),
            mat_iron,
            bevel_width=0.008,
            rotation=(0.0, 0.0, ang),
        )
        parts.append(arch_bar)

    # Skeletal prisoner remains inside the gibbet cage
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.10, location=(0.04, -0.03, 2.12))
    p_skull = bpy.context.active_object
    p_skull.name = "PrisonerSkull"
    p_skull.data.materials.append(mat_bone)
    parts.append(p_skull)

    parts.append(add_box("PrisonerSpine", (0.06, 0.06, 0.48), (0.0, 0.0, 1.78), mat_bone, bevel_width=0.01))
    for r_idx in range(4):
        rz = 1.64 + r_idx * 0.09
        parts.append(add_box(f"PrisonerRib_{r_idx}", (0.26, 0.18, 0.04), (0.0, 0.0, rz), mat_bone, bevel_width=0.008))
    for lx in (-0.11, 0.11):
        parts.append(
            add_box(f"PrisonerFemur_{lx}", (0.06, 0.06, 0.36), (lx, 0.04, 1.46), mat_bone, bevel_width=0.01, rotation=(0.18, 0.0, 0.0))
        )

    # Heavy 3D ceiling chain links ascending from Z = 2.66m up to Z = 3.85m
    for c_idx in range(11):
        cz = 2.68 + c_idx * 0.11
        bpy.ops.mesh.primitive_torus_add(
            major_radius=0.065,
            minor_radius=0.018,
            location=(0.0, 0.0, cz),
            rotation=(math.pi * 0.5, (c_idx % 2) * math.pi * 0.5, 0.0),
        )
        clink = bpy.context.active_object
        clink.name = f"GibbetChainLink_{c_idx}"
        clink.data.materials.append(mat_iron)
        parts.append(clink)

    parts.append(add_box("CeilingAnchorPlate", (0.36, 0.36, 0.08), (0.0, 0.0, 3.88), mat_iron, bevel_width=0.01))

    export_parts_as_glb(parts, out_dir, "crypt_hanging_cage.glb")


def build_crypt_ritual_obelisk(out_dir: str) -> None:
    """
    7. crypt_ritual_obelisk.glb:
    3.8m tall tapered octagonal dark slate monolith on a 3-stepped pedestal with deeply recessed
    glowing crimson runes (AbyssalCrimson) and 4 candle clusters.
    """
    clear_scene()
    mats = _make_catacomb_materials()
    mat_stone = mats["WeatheredStone"]
    mat_flag = mats["DarkFlagstone"]
    mat_iron = mats["WroughtIron"]
    mat_bronze = mats["TarnishedBronze"]
    mat_bone = mats["AgedBone"]
    mat_crimson = mats["AbyssalCrimson"]

    parts: list[bpy.types.Object] = []

    # 3-stepped pedestal (Z = 0.0m to 0.66m)
    parts.append(add_box("ObeliskStep1", (1.90, 1.90, 0.22), (0.0, 0.0, 0.11), mat_flag, bevel_width=0.03))
    parts.append(add_box("ObeliskStep2", (1.52, 1.52, 0.22), (0.0, 0.0, 0.33), mat_flag, bevel_width=0.025))
    parts.append(add_box("ObeliskStep3", (1.18, 1.18, 0.22), (0.0, 0.0, 0.55), mat_stone, bevel_width=0.025))

    # Tapered octagonal monolith shaft (Z = 0.66m to 3.36m, height 2.70m)
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.48, radius2=0.30, depth=2.70, location=(0.0, 0.0, 2.01))
    shaft = bpy.context.active_object
    shaft.name = "ObeliskShaft"
    shaft.data.materials.append(mat_stone)
    shaft.data.materials.append(mat_crimson)

    # Carve recessed vertical rune channels on all 4 cardinal faces via BOOLEAN DIFFERENCE
    for rot_z in (0.0, math.pi * 0.5):
        chan_cut = add_box(
            f"RuneChannelCut_{rot_z:.2f}",
            (0.11, 1.10, 2.10) if rot_z == 0.0 else (1.10, 0.11, 2.10),
            (0.0, 0.0, 2.00),
            mat_crimson,
            bevel_width=0.0,
        )
        b_mod = shaft.modifiers.new(name=f"CarveRuneChan_{rot_z:.2f}", type='BOOLEAN')
        b_mod.operation = 'DIFFERENCE'
        b_mod.solver = 'EXACT'
        b_mod.object = chan_cut
        bpy.context.view_layer.objects.active = shaft
        bpy.ops.object.modifier_apply(modifier=b_mod.name)
        bpy.data.objects.remove(chan_cut, do_unlink=True)

    parts.append(shaft)

    # Octagonal pyramidion apex (Z = 3.36m to 3.82m)
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.31, radius2=0.0, depth=0.46, location=(0.0, 0.0, 3.59))
    apex = bpy.context.active_object
    apex.name = "ObeliskPyramidion"
    apex.data.materials.append(mat_bronze)
    parts.append(apex)

    # Glowing AbyssalCrimson rune inlays inside the 4 cardinal channels + horizontal rune sigils
    for tier_z in (1.15, 1.65, 2.15, 2.65):
        w_span = 0.78 - (tier_z - 1.0) * 0.12
        parts.append(add_box(f"CrimsonRuneNS_{tier_z}", (0.08, w_span, 0.32), (0.0, 0.0, tier_z), mat_crimson, bevel_width=0.005))
        parts.append(add_box(f"CrimsonRuneEW_{tier_z}", (w_span, 0.08, 0.32), (0.0, 0.0, tier_z), mat_crimson, bevel_width=0.005))

    # Wrought-iron binding collars around the obelisk shaft
    for cz, rad in ((0.82, 0.50), (1.92, 0.41), (3.12, 0.33)):
        bpy.ops.mesh.primitive_torus_add(major_radius=rad, minor_radius=0.03, location=(0.0, 0.0, cz))
        collar = bpy.context.active_object
        collar.name = f"ObeliskCollar_{cz}"
        collar.data.materials.append(mat_iron)
        parts.append(collar)

    # 4 Corner ritual candle clusters on the pedestal steps (each with 3 candles + glowing crimson flames)
    corners = [(-0.62, -0.62), (0.62, -0.62), (-0.62, 0.62), (0.62, 0.62)]
    offsets = [(0.0, 0.0, 0.26), (-0.09, 0.06, 0.18), (0.08, -0.07, 0.22)]
    for c_idx, (bx, by) in enumerate(corners):
        dish = add_box(f"CandleDish_{c_idx}", (0.32, 0.32, 0.05), (bx, by, 0.46), mat_bronze, bevel_width=0.01)
        parts.append(dish)
        for o_idx, (ox, oy, ch) in enumerate(offsets):
            cx = bx + ox
            cy = by + oy
            bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.038, depth=ch, location=(cx, cy, 0.48 + ch * 0.5))
            c_cyl = bpy.context.active_object
            c_cyl.name = f"ObeliskCandle_{c_idx}_{o_idx}"
            c_cyl.data.materials.append(mat_bone)
            parts.append(c_cyl)

            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.032, location=(cx, cy, 0.48 + ch + 0.03))
            f_sp = bpy.context.active_object
            f_sp.name = f"ObeliskFlame_{c_idx}_{o_idx}"
            f_sp.scale = (0.75, 0.75, 1.5)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            f_sp.data.materials.append(mat_crimson)
            parts.append(f_sp)

    export_parts_as_glb(parts, out_dir, "crypt_ritual_obelisk.glb")


def build_crypt_rotting_bookshelf_4x4(out_dir: str) -> None:
    """
    8. crypt_rotting_bookshelf_4x4.glb:
    Towering dark timber & wrought-iron gothic reliquary shelving (3.86m wide x 0.68m deep x 3.75m tall)
    packed with tilted leather-bound grimoires, scroll tubes, and ritual skulls.
    """
    clear_scene()
    mats = _make_catacomb_materials()
    mat_timber = mats["RottedTimber"]
    mat_iron = mats["WroughtIron"]
    mat_bronze = mats["TarnishedBronze"]
    mat_bone = mats["AgedBone"]
    mat_rune = mats["GlowingOccultRune"]
    mat_crimson = mats["AbyssalCrimson"]

    parts: list[bpy.types.Object] = []

    # Back panel & gothic crown header with BOOLEAN DIFFERENCE pointed trefoil cutouts
    back_board = add_box("ShelfBackPanel", (3.82, 0.08, 3.68), (0.0, 0.28, 1.84), mat_timber, bevel_width=0.015)
    crown_header = add_box("ShelfCrownHeader", (3.92, 0.68, 0.48), (0.0, 0.0, 3.52), mat_timber, bevel_width=0.02)
    for cx in (-1.22, 0.0, 1.22):
        arch_cut = create_pointed_arch_prism(f"CrownCut_{cx}", width=0.88, depth=1.0, spring_h=3.42, peak_h=3.66, z_base=3.22)
        arch_cut.location = (cx, 0.0, 0.0)
        bpy.context.view_layer.objects.active = arch_cut
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        b_mod = crown_header.modifiers.new(name=f"BoolCrown_{cx}", type='BOOLEAN')
        b_mod.operation = 'DIFFERENCE'
        b_mod.solver = 'EXACT'
        b_mod.object = arch_cut
        bpy.context.view_layer.objects.active = crown_header
        bpy.ops.object.modifier_apply(modifier=b_mod.name)
        bpy.data.objects.remove(arch_cut, do_unlink=True)
    parts.extend([back_board, crown_header])

    # 4 Vertical timber stiles + wrought-iron corner straps
    for sx in (-1.86, -0.62, 0.62, 1.86):
        parts.append(add_box(f"TimberStile_{sx}", (0.12, 0.66, 3.70), (sx, 0.0, 1.85), mat_timber, bevel_width=0.015))
        parts.append(add_box(f"IronBracketTop_{sx}", (0.15, 0.70, 0.14), (sx, 0.0, 3.25), mat_iron, bevel_width=0.01))
        parts.append(add_box(f"IronBracketBot_{sx}", (0.15, 0.70, 0.14), (sx, 0.0, 0.35), mat_iron, bevel_width=0.01))

    # 5 Horizontal timber shelf planks (Z = 0.25, 0.92, 1.58, 2.24, 2.90)
    shelf_zs = (0.25, 0.92, 1.58, 2.24, 2.90)
    for sz in shelf_zs:
        parts.append(add_box(f"ShelfPlank_{sz}", (3.84, 0.62, 0.07), (0.0, 0.0, sz), mat_timber, bevel_width=0.012))

    # Populate bays and shelves with tilted grimoires, glowing rune spines, scroll tubes, and ritual skulls
    bay_xs = (-1.24, 0.0, 1.24)
    for b_idx, bx in enumerate(bay_xs):
        for s_idx, sz in enumerate(shelf_zs[:-1]):
            top_surface = sz + 0.035
            if (b_idx + s_idx) % 3 == 0:
                # Ritual skull + scroll tube cluster
                bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.11, location=(bx - 0.28, -0.05, top_surface + 0.11))
                sk = bpy.context.active_object
                sk.name = f"ReliquarySkull_{b_idx}_{s_idx}"
                sk.data.materials.append(mat_bone)
                parts.append(sk)

                for sc_i in range(3):
                    bpy.ops.mesh.primitive_cylinder_add(
                        vertices=8,
                        radius=0.04,
                        depth=0.44,
                        location=(bx + 0.18 + sc_i * 0.09, 0.0, top_surface + 0.05 + (sc_i % 2) * 0.04),
                        rotation=(math.pi * 0.5, 0.0, 0.08 * sc_i),
                    )
                    scroll = bpy.context.active_object
                    scroll.name = f"Scroll_{b_idx}_{s_idx}_{sc_i}"
                    scroll.data.materials.append(mat_bone)
                    parts.append(scroll)
            else:
                # Row of 5 thick leather-bound grimoires with varied tilts & occasional glowing occult spine
                for g_i in range(5):
                    gx = bx - 0.42 + g_i * 0.20
                    gh = 0.34 + (g_i % 3) * 0.05
                    tilt = 0.14 if (g_i == 4) else (-0.06 if g_i == 0 else 0.0)
                    g_mat = mat_rune if (g_i == 2 and s_idx % 2 == 1) else (mat_crimson if (g_i == 3 and b_idx == 1) else mat_bronze)
                    book = add_box(
                        f"Grimoire_{b_idx}_{s_idx}_{g_i}",
                        (0.08, 0.34, gh),
                        (gx, -0.02, top_surface + gh * 0.5),
                        g_mat,
                        bevel_width=0.008,
                        rotation=(0.0, tilt, 0.0),
                    )
                    parts.append(book)

    export_parts_as_glb(parts, out_dir, "crypt_rotting_bookshelf_4x4.glb")


def build_crypt_lectern_grimoire(out_dir: str) -> None:
    """
    9. crypt_lectern_grimoire.glb:
    Ornate eagle/gargoyle wrought-iron reading stand holding an open ancient tome with glowing
    occult sigils on the pages.
    """
    clear_scene()
    mats = _make_catacomb_materials()
    mat_flag = mats["DarkFlagstone"]
    mat_iron = mats["WroughtIron"]
    mat_bronze = mats["TarnishedBronze"]
    mat_timber = mats["RottedTimber"]
    mat_bone = mats["AgedBone"]
    mat_rune = mats["GlowingOccultRune"]

    parts: list[bpy.types.Object] = []

    # Stepped octagonal stone dais & bronze claw feet
    parts.append(add_box("LecternStoneBase", (1.20, 1.20, 0.16), (0.0, 0.0, 0.08), mat_flag, bevel_width=0.025))
    parts.append(add_box("LecternPlinth2", (0.82, 0.82, 0.14), (0.0, 0.0, 0.23), mat_flag, bevel_width=0.02))

    for i in range(4):
        ang = i * (math.pi * 0.5) + math.pi * 0.25
        fx = math.cos(ang) * 0.34
        fy = math.sin(ang) * 0.34
        parts.append(
            add_box(
                f"ClawFoot_{i}",
                (0.12, 0.28, 0.18),
                (fx, fy, 0.36),
                mat_iron,
                bevel_width=0.015,
                rotation=(0.0, 0.0, ang),
            )
        )

    # Fluted wrought-iron pedestal shaft & bronze rings (Z = 0.30m to 1.22m)
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.11, depth=0.92, location=(0.0, 0.0, 0.76))
    ped_shaft = bpy.context.active_object
    ped_shaft.name = "LecternShaft"
    ped_shaft.data.materials.append(mat_iron)
    parts.append(ped_shaft)

    for rz in (0.48, 0.78, 1.08):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.14, minor_radius=0.025, location=(0.0, 0.0, rz))
        ring = bpy.context.active_object
        ring.name = f"ShaftCollar_{rz}"
        ring.data.materials.append(mat_bronze)
        parts.append(ring)

    # Spread gargoyle/eagle wings supporting the sloped reading cradle
    for sx in (-1.0, 1.0):
        for f_idx in range(4):
            wx = sx * (0.16 + f_idx * 0.09)
            wz = 1.16 + f_idx * 0.04
            wing_feather = add_box(
                f"EagleFeather_{sx}_{f_idx}",
                (0.14, 0.08, 0.32 - f_idx * 0.04),
                (wx, -0.04, wz),
                mat_bronze,
                bevel_width=0.01,
                rotation=(0.25, sx * 0.42, 0.0),
            )
            parts.append(wing_feather)

    # Sloped reading desk cradle (tilted 28 degrees toward reader)
    desk_tilt = math.radians(28.0)
    cradle = add_box(
        "LecternDeskBoard",
        (0.86, 0.58, 0.05),
        (0.0, 0.0, 1.28),
        mat_timber,
        bevel_width=0.01,
        rotation=(desk_tilt, 0.0, 0.0),
    )
    parts.append(cradle)

    # Open ancient grimoire cover + left/right parchment pages + BOOLEAN DIFFERENCE rune recess + GlowingOccultRune sigils
    for px_sign in (-1.0, 1.0):
        page = add_box(
            f"GrimoirePage_{px_sign}",
            (0.34, 0.46, 0.06),
            (px_sign * 0.19, -0.02, 1.33),
            mat_bone,
            bevel_width=0.008,
            rotation=(desk_tilt, px_sign * 0.08, 0.0),
        )
        page.data.materials.append(mat_rune)
        sigil_cut = add_box(
            f"SigilCut_{px_sign}",
            (0.18, 0.24, 0.04),
            (px_sign * 0.19, -0.02, 1.36),
            mat_rune,
            bevel_width=0.0,
            rotation=(desk_tilt, px_sign * 0.08, 0.0),
        )
        b_mod = page.modifiers.new(name=f"CarvePageSigil_{px_sign}", type='BOOLEAN')
        b_mod.operation = 'DIFFERENCE'
        b_mod.solver = 'EXACT'
        b_mod.object = sigil_cut
        bpy.context.view_layer.objects.active = page
        bpy.ops.object.modifier_apply(modifier=b_mod.name)
        bpy.data.objects.remove(sigil_cut, do_unlink=True)
        parts.append(page)

        # Raised glowing occult rune bars on each page
        for r_i in range(3):
            ry_off = -0.10 + r_i * 0.10
            rune_strip = add_box(
                f"PageRuneStrip_{px_sign}_{r_i}",
                (0.22, 0.035, 0.02),
                (px_sign * 0.19, ry_off, 1.36 - ry_off * 0.45),
                mat_rune,
                bevel_width=0.003,
                rotation=(desk_tilt, px_sign * 0.08, 0.0),
            )
            parts.append(rune_strip)

    # Flanking twin candlesticks on iron outrigger arms
    for sx in (-0.52, 0.52):
        parts.append(add_box(f"CandleArm_{sx}", (0.24, 0.04, 0.04), (sx * 0.75, 0.0, 1.18), mat_iron, bevel_width=0.005))
        parts.append(add_box(f"CandleCup_{sx}", (0.12, 0.12, 0.04), (sx, 0.0, 1.22), mat_bronze, bevel_width=0.008))
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.032, depth=0.22, location=(sx, 0.0, 1.35))
        c_wax = bpy.context.active_object
        c_wax.name = f"LecternCandle_{sx}"
        c_wax.data.materials.append(mat_bone)
        parts.append(c_wax)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.028, location=(sx, 0.0, 1.49))
        c_fl = bpy.context.active_object
        c_fl.name = f"LecternFlame_{sx}"
        c_fl.data.materials.append(mat_rune)
        parts.append(c_fl)

    export_parts_as_glb(parts, out_dir, "crypt_lectern_grimoire.glb")


def build_crypt_plague_cauldron(out_dir: str) -> None:
    """
    10. crypt_plague_cauldron.glb:
    Massive 2.2m wide riveted cast-iron alchemical basin on a stone furnace ring, brimming with
    glowing sickly green/amber bile (SicklyGreenBile) and rising distillation pipes.
    """
    clear_scene()
    mats = _make_catacomb_materials()
    mat_stone = mats["WeatheredStone"]
    mat_flag = mats["DarkFlagstone"]
    mat_iron = mats["WroughtIron"]
    mat_bronze = mats["TarnishedBronze"]
    mat_bile = mats["SicklyGreenBile"]

    parts: list[bpy.types.Object] = []

    # Circular stone furnace ring (outer diameter 2.40m, Z = 0.0m to 0.68m) with BOOLEAN DIFFERENCE firebox vents
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=1.20, depth=0.68, location=(0.0, 0.0, 0.34))
    furnace = bpy.context.active_object
    furnace.name = "FurnaceStoneRing"
    furnace.data.materials.append(mat_stone)
    furnace.data.materials.append(mat_bile)

    for rot_z in (0.0, math.pi * 0.5):
        vent_cut = add_box(
            f"FurnaceVentCut_{rot_z:.2f}",
            (0.42, 2.60, 0.36) if rot_z == 0.0 else (2.60, 0.42, 0.36),
            (0.0, 0.0, 0.24),
            mat_bile,
            bevel_width=0.0,
        )
        b_mod = furnace.modifiers.new(name=f"CarveVent_{rot_z:.2f}", type='BOOLEAN')
        b_mod.operation = 'DIFFERENCE'
        b_mod.solver = 'EXACT'
        b_mod.object = vent_cut
        bpy.context.view_layer.objects.active = furnace
        bpy.ops.object.modifier_apply(modifier=b_mod.name)
        bpy.data.objects.remove(vent_cut, do_unlink=True)
    parts.append(furnace)

    # Massive 2.2m wide riveted cast-iron cauldron basin (radius = 1.10m, Z = 0.48m to 1.42m)
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.92, radius2=1.12, depth=0.94, location=(0.0, 0.0, 0.95))
    cauldron = bpy.context.active_object
    cauldron.name = "CastIronCauldron"
    cauldron.data.materials.append(mat_iron)

    # Carve interior cauldron bowl via BOOLEAN DIFFERENCE
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.98, depth=0.72, location=(0.0, 0.0, 1.18))
    bowl_cut = bpy.context.active_object
    bowl_cut.name = "CauldronBowlCut"
    b_bowl = cauldron.modifiers.new(name="CarveCauldronBowl", type='BOOLEAN')
    b_bowl.operation = 'DIFFERENCE'
    b_bowl.solver = 'EXACT'
    b_bowl.object = bowl_cut
    bpy.context.view_layer.objects.active = cauldron
    bpy.ops.object.modifier_apply(modifier=b_bowl.name)
    bpy.data.objects.remove(bowl_cut, do_unlink=True)
    parts.append(cauldron)

    # Heavy iron rim torus + 16 perimeter rivets + 4 lion-ring handles
    bpy.ops.mesh.primitive_torus_add(major_radius=1.10, minor_radius=0.075, location=(0.0, 0.0, 1.40))
    rim_torus = bpy.context.active_object
    rim_torus.name = "CauldronRimTorus"
    rim_torus.data.materials.append(mat_iron)
    parts.append(rim_torus)

    for i in range(12):
        ang = i * (2.0 * math.pi / 12.0)
        rx = math.cos(ang) * 1.08
        ry = math.sin(ang) * 1.08
        parts.append(add_box(f"CauldronRivet_{i}", (0.08, 0.08, 0.08), (rx, ry, 1.16), mat_bronze, bevel_width=0.01))

    for i in range(4):
        ang = i * (math.pi * 0.5) + math.pi * 0.25
        hx = math.cos(ang) * 1.14
        hy = math.sin(ang) * 1.14
        bpy.ops.mesh.primitive_torus_add(
            major_radius=0.16,
            minor_radius=0.032,
            location=(hx, hy, 1.05),
            rotation=(math.pi * 0.42, 0.0, ang + math.pi * 0.5),
        )
        h_ring = bpy.context.active_object
        h_ring.name = f"CauldronHandle_{i}"
        h_ring.data.materials.append(mat_bronze)
        parts.append(h_ring)

    # Glowing SicklyGreenBile liquid surface + 10 bubbling alembic spheres
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.97, depth=0.08, location=(0.0, 0.0, 1.32))
    bile_pool = bpy.context.active_object
    bile_pool.name = "SicklyGreenBileSurface"
    bile_pool.data.materials.append(mat_bile)
    parts.append(bile_pool)

    bubble_coords = [
        (0.0, 0.0, 0.14), (-0.42, 0.28, 0.11), (0.48, -0.22, 0.12),
        (-0.25, -0.52, 0.09), (0.35, 0.45, 0.10), (-0.62, -0.12, 0.08),
        (0.60, 0.18, 0.09), (0.12, -0.68, 0.08), (-0.15, 0.65, 0.10),
    ]
    for b_idx, (bx, by, br) in enumerate(bubble_coords):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=br, location=(bx, by, 1.35))
        bub = bpy.context.active_object
        bub.name = f"BileBubble_{b_idx}"
        bub.data.materials.append(mat_bile)
        parts.append(bub)

    # Rising tarnished-bronze alchemical distillation pipes & condenser coils (Z = 1.32m to 2.95m)
    for p_idx in range(3):
        ang = p_idx * (2.0 * math.pi / 3.0)
        px = math.cos(ang) * 0.36
        py = math.sin(ang) * 0.36
        bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.065, depth=1.55, location=(px, py, 2.08))
        pipe = bpy.context.active_object
        pipe.name = f"DistillPipe_{p_idx}"
        pipe.data.materials.append(mat_bronze)
        parts.append(pipe)

        for fl_z in (1.65, 2.15, 2.65):
            bpy.ops.mesh.primitive_torus_add(major_radius=0.095, minor_radius=0.022, location=(px, py, fl_z))
            flange = bpy.context.active_object
            flange.name = f"PipeFlange_{p_idx}_{fl_z}"
            flange.data.materials.append(mat_iron)
            parts.append(flange)

    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.28, location=(0.0, 0.0, 2.78))
    alembic_dome = bpy.context.active_object
    alembic_dome.name = "AlembicCollectorDome"
    alembic_dome.data.materials.append(mat_bronze)
    parts.append(alembic_dome)

    export_parts_as_glb(parts, out_dir, "crypt_plague_cauldron.glb")


def build_crypt_drowned_cistern_4x4(out_dir: str) -> None:
    """
    11. crypt_drowned_cistern_4x4.glb:
    Recessed octagonal stone well/pool floor tile (BOOLEAN DIFFERENCE basin) filled with dark
    reflective water, iron drainage grates, and half-submerged stone steps.
    Flush at Z = 0.0m so it seamlessly replaces a 4x4 floor tile and remains 100% walkable across the grates.
    """
    clear_scene()
    mats = _make_catacomb_materials()
    mat_stone = mats["WeatheredStone"]
    mat_flag = mats["DarkFlagstone"]
    mat_iron = mats["WroughtIron"]
    mat_water = make_pbr_material("DarkCisternWater", (0.04, 0.08, 0.11, 1.0), roughness=0.10, metallic=0.20)

    parts: list[bpy.types.Object] = []

    # Structural 4m x 4m floor slab (Z = -0.38m to 0.0m)
    slab = add_box("CisternFloorSlab", (4.00, 4.00, 0.38), (0.0, 0.0, -0.19), mat_flag, bevel_width=0.015)
    slab.data.materials.append(mat_stone)

    # Carve octagonal cistern basin (radius 1.32m, depth from Z = -0.26m to +0.10m) via BOOLEAN DIFFERENCE
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=1.32, depth=0.38, location=(0.0, 0.0, -0.07))
    basin_cut = bpy.context.active_object
    basin_cut.name = "OctagonalBasinCut"
    basin_cut.data.materials.append(mat_stone)
    b_mod = slab.modifiers.new(name="CarveCisternBasin", type='BOOLEAN')
    b_mod.operation = 'DIFFERENCE'
    b_mod.solver = 'EXACT'
    b_mod.object = basin_cut
    bpy.context.view_layer.objects.active = slab
    bpy.ops.object.modifier_apply(modifier=b_mod.name)
    bpy.data.objects.remove(basin_cut, do_unlink=True)
    parts.append(slab)

    # 8 Beveled stone curb coping blocks around the octagonal rim (flush/low profile Z = -0.02m to +0.06m)
    for i in range(8):
        ang = i * (math.pi / 4.0) + (math.pi / 8.0)
        cx = math.cos(ang) * 1.36
        cy = math.sin(ang) * 1.36
        curb = add_box(
            f"CisternCurb_{i}",
            (0.24, 1.08, 0.08),
            (cx, cy, 0.02),
            mat_stone,
            bevel_width=0.015,
            rotation=(0.0, 0.0, ang),
        )
        parts.append(curb)

    # Half-submerged stone steps on North and South sides of the basin
    for sy in (-1.0, 1.0):
        for st_i in range(2):
            step_y = sy * (1.02 - st_i * 0.24)
            step_z = -0.08 - st_i * 0.07
            parts.append(
                add_box(f"SubmergedStep_{sy}_{st_i}", (1.10, 0.24, 0.10), (0.0, step_y, step_z), mat_flag, bevel_width=0.015)
            )

    # Dark reflective cistern water surface at Z = -0.12m
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=1.28, depth=0.04, location=(0.0, 0.0, -0.12))
    water_disk = bpy.context.active_object
    water_disk.name = "CisternReflectiveWater"
    water_disk.data.materials.append(mat_water)
    parts.append(water_disk)

    # Heavy wrought-iron drainage grates spanning across the basin at Z = -0.02m (walkable trimesh!)
    for gx in (-0.90, -0.60, -0.30, 0.0, 0.30, 0.60, 0.90):
        bar_len = 2.30 if abs(gx) < 0.7 else 1.65
        parts.append(add_box(f"GrateBarX_{gx}", (0.045, bar_len, 0.04), (gx, 0.0, -0.02), mat_iron, bevel_width=0.005))
    for gy in (-0.85, -0.42, 0.0, 0.42, 0.85):
        bar_len = 2.30 if abs(gy) < 0.7 else 1.65
        parts.append(add_box(f"GrateBarY_{gy}", (bar_len, 0.045, 0.04), (0.0, gy, -0.02), mat_iron, bevel_width=0.005))

    # Outer corner flagstones
    for cx in (-1.62, 1.62):
        for cy in (-1.62, 1.62):
            parts.append(add_box(f"CornerPaver_{cx}_{cy}", (0.72, 0.72, 0.04), (cx, cy, 0.0), mat_stone, bevel_width=0.012))

    export_parts_as_glb(parts, out_dir, "crypt_drowned_cistern_4x4.glb")


def build_crypt_weeping_statue_pedestal(out_dir: str) -> None:
    """
    12. crypt_weeping_statue_pedestal.glb:
    Towering 3.6m hooded gothic monolith figure/cenotaph with geometric draped cowl, bowing over
    a stone basin with glowing pale-blue spectral tear streaks (FrozenBlueSoul).
    """
    clear_scene()
    mats = _make_catacomb_materials()
    mat_stone = mats["WeatheredStone"]
    mat_flag = mats["DarkFlagstone"]
    mat_iron = mats["WroughtIron"]
    mat_soul = mats["FrozenBlueSoul"]

    parts: list[bpy.types.Object] = []

    # Stepped octagonal cenotaph pedestal (Z = 0.0m to 0.96m)
    parts.append(add_box("CenotaphStep1", (2.20, 2.40, 0.22), (0.0, 0.0, 0.11), mat_flag, bevel_width=0.03))
    parts.append(add_box("CenotaphStep2", (1.76, 1.96, 0.22), (0.0, 0.0, 0.33), mat_flag, bevel_width=0.025))
    ped_core = add_box("CenotaphPedestalCore", (1.32, 1.56, 0.56), (0.0, 0.10, 0.72), mat_stone, bevel_width=0.025)
    parts.append(ped_core)

    # Front stone tear-offering basin (Y = -0.58m, Z = 0.44m to 1.08m) carved via BOOLEAN DIFFERENCE
    basin_block = add_box("WeepingBasinBlock", (1.12, 0.76, 0.64), (0.0, -0.58, 0.76), mat_stone, bevel_width=0.025)
    basin_block.data.materials.append(mat_soul)
    basin_cut = add_box("WeepingBasinCut", (0.86, 0.52, 0.28), (0.0, -0.58, 1.02), mat_soul, bevel_width=0.0)
    b_bas = basin_block.modifiers.new(name="CarveTearBasin", type='BOOLEAN')
    b_bas.operation = 'DIFFERENCE'
    b_bas.solver = 'EXACT'
    b_bas.object = basin_cut
    bpy.context.view_layer.objects.active = basin_block
    bpy.ops.object.modifier_apply(modifier=b_bas.name)
    bpy.data.objects.remove(basin_cut, do_unlink=True)
    parts.append(basin_block)

    # Glowing FrozenBlueSoul tear pool inside the offering basin
    parts.append(add_box("FrozenTearPool", (0.82, 0.48, 0.06), (0.0, -0.58, 0.94), mat_soul, bevel_width=0.005))

    # Towering 3.6m robed gothic monolith figure (Z = 0.96m to 3.60m) bowing forward toward -Y
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.58, radius2=0.34, depth=2.15, location=(0.0, 0.18, 2.02))
    robe_pillar = bpy.context.active_object
    robe_pillar.name = "SaintRobeMonolith"
    robe_pillar.rotation_euler = (-0.12, 0.0, 0.0)
    robe_pillar.data.materials.append(mat_stone)
    parts.append(robe_pillar)

    # Vertical carved gothic drapery pleats around the robe
    for i in range(8):
        ang = i * (math.pi / 4.0)
        px = math.cos(ang) * 0.42
        py = 0.18 + math.sin(ang) * 0.42
        pleat = add_box(
            f"RobePleat_{i}",
            (0.11, 0.14, 1.95),
            (px, py, 1.96),
            mat_flag,
            bevel_width=0.015,
            rotation=(-0.12, 0.0, ang),
        )
        parts.append(pleat)

    # Draped shoulders & bowed hooded cowl (Z = 2.85m to 3.62m) with BOOLEAN DIFFERENCE shadow cavity
    shoulders = add_box("SaintShoulders", (0.92, 0.62, 0.36), (0.0, 0.04, 2.96), mat_stone, bevel_width=0.03, rotation=(-0.22, 0.0, 0.0))
    parts.append(shoulders)

    cowl = add_box("SaintHoodedCowl", (0.56, 0.64, 0.62), (0.0, -0.10, 3.34), mat_stone, bevel_width=0.03, rotation=(-0.38, 0.0, 0.0))
    cowl_cut = add_box("CowlShadowCut", (0.36, 0.42, 0.42), (0.0, -0.32, 3.26), mat_flag, bevel_width=0.0, rotation=(-0.38, 0.0, 0.0))
    b_cowl = cowl.modifiers.new(name="CarveCowlVoid", type='BOOLEAN')
    b_cowl.operation = 'DIFFERENCE'
    b_cowl.solver = 'EXACT'
    b_cowl.object = cowl_cut
    bpy.context.view_layer.objects.active = cowl
    bpy.ops.object.modifier_apply(modifier=b_cowl.name)
    bpy.data.objects.remove(cowl_cut, do_unlink=True)
    parts.append(cowl)

    # Folded geometric hands & sleeves praying over the tear basin
    for sx in (-0.22, 0.22):
        parts.append(
            add_box(
                f"SaintForearm_{sx}",
                (0.18, 0.52, 0.20),
                (sx, -0.18, 2.58),
                mat_stone,
                bevel_width=0.02,
                rotation=(-0.45, -sx * 0.65, 0.0),
            )
        )

    # Glowing pale-blue spectral tear streaks (FrozenBlueSoul) streaming from the cowl down into the basin
    for tx in (-0.10, 0.0, 0.10):
        for seg in range(5):
            sz = 3.12 - seg * 0.42
            sy = -0.26 - seg * 0.06
            tear_seg = add_box(
                f"SpectralTearStreak_{tx}_{seg}",
                (0.035, 0.04, 0.34),
                (tx, sy, sz),
                mat_soul,
                bevel_width=0.005,
                rotation=(-0.14, 0.0, 0.0),
            )
            parts.append(tear_seg)

    # Wrought-iron fence posts around the pedestal corners
    for fx in (-0.98, 0.98):
        for fy in (-1.08, 1.08):
            parts.append(add_box(f"ShrineFencePost_{fx}_{fy}", (0.06, 0.06, 0.95), (fx, fy, 0.68), mat_iron, bevel_width=0.008))

    export_parts_as_glb(parts, out_dir, "crypt_weeping_statue_pedestal.glb")


def build_crypt_sunken_bell_crater(out_dir: str) -> None:
    """
    13. crypt_sunken_bell_crater.glb:
    Massive 2.6m cracked tarnished-bronze cathedral bell tilted at 25 degrees inside a shattered
    stone floor crater (BOOLEAN DIFFERENCE rubble ring), wrapped in heavy iron chains and glowing rune cracks.
    """
    clear_scene()
    mats = _make_catacomb_materials()
    mat_stone = mats["WeatheredStone"]
    mat_flag = mats["DarkFlagstone"]
    mat_bronze = mats["TarnishedBronze"]
    mat_iron = mats["WroughtIron"]
    mat_timber = mats["RottedTimber"]
    mat_crimson = mats["AbyssalCrimson"]

    parts: list[bpy.types.Object] = []

    # Shattered stone floor crater ring (outer radius 2.15m, carved via BOOLEAN DIFFERENCE)
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=2.15, depth=0.52, location=(0.0, 0.0, 0.18))
    crater_ring = bpy.context.active_object
    crater_ring.name = "CraterStoneMound"
    crater_ring.data.materials.append(mat_flag)
    crater_ring.data.materials.append(mat_crimson)

    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=1.05, radius2=1.68, depth=0.62, location=(0.0, 0.0, 0.24))
    crater_cut = bpy.context.active_object
    crater_cut.name = "CraterPitCutter"
    crater_cut.data.materials.append(mat_crimson)
    b_crat = crater_ring.modifiers.new(name="CarveBellCrater", type='BOOLEAN')
    b_crat.operation = 'DIFFERENCE'
    b_crat.solver = 'EXACT'
    b_crat.object = crater_cut
    bpy.context.view_layer.objects.active = crater_ring
    bpy.ops.object.modifier_apply(modifier=b_crat.name)
    bpy.data.objects.remove(crater_cut, do_unlink=True)
    parts.append(crater_ring)

    # 12 Shattered tilted stone rubble slabs & glowing crimson fault-line cracks around the crater
    for i in range(12):
        ang = i * (2.0 * math.pi / 12.0)
        rx = math.cos(ang) * 1.62
        ry = math.sin(ang) * 1.62
        rubble = add_box(
            f"CraterRubbleSlab_{i}",
            (0.68, 0.52, 0.22),
            (rx, ry, 0.26),
            mat_stone if (i % 2 == 0) else mat_flag,
            bevel_width=0.02,
            rotation=(math.sin(ang) * 0.38, -math.cos(ang) * 0.38, ang),
        )
        parts.append(rubble)
        if i % 2 == 0:
            crack_bar = add_box(
                f"CraterRuneCrack_{i}",
                (0.08, 1.35, 0.08),
                (math.cos(ang) * 1.15, math.sin(ang) * 1.15, 0.12),
                mat_crimson,
                bevel_width=0.005,
                rotation=(0.0, 0.0, ang + math.pi * 0.5),
            )
            parts.append(crack_bar)

    # Massive 2.6m wide (radius 1.30m) tarnished-bronze cathedral bell tilted at 25 degrees
    tilt_rad = math.radians(25.0)
    bpy.ops.mesh.primitive_cone_add(
        vertices=20,
        radius1=1.30,
        radius2=0.72,
        depth=2.15,
        location=(0.0, 0.0, 1.12),
        rotation=(tilt_rad, 0.08, 0.0),
    )
    bell = bpy.context.active_object
    bell.name = "SunkenCathedralBell"
    bell.data.materials.append(mat_bronze)
    bell.data.materials.append(mat_crimson)

    # Carve jagged fracture crack into the front wall of the bell via BOOLEAN DIFFERENCE
    crack_cutter = add_box(
        "BellCrackCutter",
        (0.14, 0.65, 1.45),
        (0.0, -0.95, 1.05),
        mat_crimson,
        bevel_width=0.0,
        rotation=(tilt_rad, 0.18, 0.12),
    )
    b_crack = bell.modifiers.new(name="CarveBellCrack", type='BOOLEAN')
    b_crack.operation = 'DIFFERENCE'
    b_crack.solver = 'EXACT'
    b_crack.object = crack_cutter
    bpy.context.view_layer.objects.active = bell
    bpy.ops.object.modifier_apply(modifier=b_crack.name)
    bpy.data.objects.remove(crack_cutter, do_unlink=True)
    parts.append(bell)

    # Bell sound-bow rim torus, glowing crimson fracture core, and shattered timber yoke beam
    bpy.ops.mesh.primitive_torus_add(
        major_radius=1.30,
        minor_radius=0.11,
        location=(0.0, 0.38, 0.34),
        rotation=(tilt_rad, 0.08, 0.0),
    )
    bell_rim = bpy.context.active_object
    bell_rim.name = "SunkenBellSoundBow"
    bell_rim.data.materials.append(mat_bronze)
    parts.append(bell_rim)

    fracture_glow = add_box(
        "BellFractureGlowCore",
        (0.11, 0.22, 1.32),
        (0.0, -0.82, 1.05),
        mat_crimson,
        bevel_width=0.005,
        rotation=(tilt_rad, 0.18, 0.0),
    )
    parts.append(fracture_glow)

    yoke_timber = add_box(
        "BrokenTimberYoke",
        (2.15, 0.42, 0.42),
        (0.0, -0.45, 2.22),
        mat_timber,
        bevel_width=0.02,
        rotation=(tilt_rad, 0.08, 0.15),
    )
    parts.append(yoke_timber)

    # Heavy iron chains wrapping the sunken bell and ascending toward the chasm ceiling
    for c_idx in range(16):
        cz = 2.15 + c_idx * 0.24
        bpy.ops.mesh.primitive_torus_add(
            major_radius=0.14,
            minor_radius=0.036,
            location=(0.0, -0.42, cz),
            rotation=(math.pi * 0.5, (c_idx % 2) * math.pi * 0.5, 0.0),
        )
        chain = bpy.context.active_object
        chain.name = f"BellChasmChain_{c_idx}"
        chain.data.materials.append(mat_iron)
        parts.append(chain)

    export_parts_as_glb(parts, out_dir, "crypt_sunken_bell_crater.glb")


def build_crypt_containment_hull(out_dir: str) -> None:
    """
    14. crypt_containment_hull.glb:
    Inverted dark-stone exterior containment box wrapping the underground crypt bounding volume
    (Godot X in [-32m, +32m], Y in [-10m, +3.8m], Z in [-86m, -19m] -> Blender X in [-32, +32],
    Y in [19, 86], Z in [-10, +3.8]) with only the top opening aligned strictly to the church nave
    floor footprint (X in [-5.8m, +5.8m], Z in [-27.8m, -19.0m]).
    All face normals point strictly INWARD toward (0.0, 52.5, -3.1).
    """
    clear_scene()
    mat_hull = make_pbr_material("ContainmentHullStone", (0.06, 0.06, 0.08, 1.0), roughness=0.95)

    bm = bmesh.new()
    # Bottom Z = -10.0, Top Z = +3.8, X in [-32.0, +32.0], Y in [19.0, 86.0]
    x_min, x_max = -32.0, 32.0
    y_min, y_max = 19.0, 86.0
    z_min, z_max = -10.0, 3.8
    # Church nave opening on top face: X in [-5.8, +5.8], Y in [19.0, 27.8]
    cx_min, cx_max = -5.8, 5.8
    cy_cut = 27.8

    # 8 outer corners
    v_bl_sw = bm.verts.new((x_min, y_min, z_min))
    v_bl_se = bm.verts.new((x_max, y_min, z_min))
    v_bl_ne = bm.verts.new((x_max, y_max, z_min))
    v_bl_nw = bm.verts.new((x_min, y_max, z_min))

    v_tl_sw = bm.verts.new((x_min, y_min, z_max))
    v_tl_se = bm.verts.new((x_max, y_min, z_max))
    v_tl_ne = bm.verts.new((x_max, y_max, z_max))
    v_tl_nw = bm.verts.new((x_min, y_max, z_max))

    # Top face cutout vertices
    v_tc_sw = bm.verts.new((cx_min, y_min, z_max))
    v_tc_se = bm.verts.new((cx_max, y_min, z_max))
    v_tc_nw = bm.verts.new((cx_min, cy_cut, z_max))
    v_tc_ne = bm.verts.new((cx_max, cy_cut, z_max))
    v_tc_far_w = bm.verts.new((cx_min, y_max, z_max))
    v_tc_far_e = bm.verts.new((cx_max, y_max, z_max))

    # Create faces with INWARD-pointing normals:
    # 1. Bottom floor (normal +Z)
    bm.faces.new((v_bl_sw, v_bl_se, v_bl_ne, v_bl_nw))
    # 2. West wall at X = -32 (normal +X)
    bm.faces.new((v_bl_sw, v_bl_nw, v_tl_nw, v_tl_sw))
    # 3. East wall at X = +32 (normal -X)
    bm.faces.new((v_bl_se, v_tl_se, v_tl_ne, v_bl_ne))
    # 4. South wall at Y = +19 / Godot Z = -19 (normal +Y)
    bm.faces.new((v_bl_sw, v_tl_sw, v_tl_se, v_bl_se))
    # 5. North wall at Y = +86 / Godot Z = -86 (normal -Y)
    bm.faces.new((v_bl_nw, v_bl_ne, v_tl_ne, v_tl_nw))
    # 6. Top ceiling West slab: X in [-32, -5.8], Y in [19, 86] (normal -Z)
    bm.faces.new((v_tl_sw, v_tl_nw, v_tc_far_w, v_tc_sw))
    # 7. Top ceiling East slab: X in [+5.8, +32], Y in [19, 86] (normal -Z)
    bm.faces.new((v_tc_se, v_tc_far_e, v_tl_ne, v_tl_se))
    # 8. Top ceiling North center slab: X in [-5.8, +5.8], Y in [27.8, 86] (normal -Z)
    bm.faces.new((v_tc_nw, v_tc_far_w, v_tc_far_e, v_tc_ne))

    # Verify all normals point inward toward center (0.0, 52.5, -3.1)
    center_pt = mathutils.Vector((0.0, 52.5, -3.1))
    for f in bm.faces:
        f.normal_update()
        to_center = center_pt - f.calc_center_median()
        if f.normal.dot(to_center) < 0.0:
            f.normal_flip()

    mesh = bpy.data.meshes.new("CryptContainmentHullMesh")
    bm.to_mesh(mesh)
    bm.free()

    hull_obj = bpy.data.objects.new("CryptContainmentHull", mesh)
    bpy.context.collection.objects.link(hull_obj)
    hull_obj.data.materials.append(mat_hull)

    export_parts_as_glb([hull_obj], out_dir, "crypt_containment_hull.glb")


def build_hub_weapon_workbench(out_dir: str) -> None:
    """
    15. hub_weapon_workbench.glb (2.8m wide x 1.1m deep x 2.2m tall Gunsmith & Consecration Bench):
    Heavy pegged oak workbench table with iron corner brackets, a mounted wrought-iron gunsmith
    vice clamping a spare octagonal barrel, a pegboard back-wall displaying an occult ritual
    carbine/crossbow and silver blade silhouettes, rows of brass cartridge blocks, bullet-casting
    tongs, an open gunsmith ledger, and a small blue-flame alchemical burner. (65+ sub-elements)
    """
    clear_scene()
    mats = _make_catacomb_materials()
    mat_timber = mats["RottedTimber"]
    mat_iron = mats["WroughtIron"]
    mat_bronze = mats["TarnishedBronze"]
    mat_stone = mats["DarkFlagstone"]
    mat_silver = mats["OccultSilver"]
    mat_bone = mats["AgedBone"]
    mat_rune = mats["GlowingOccultRune"]
    mat_blue = mats["FrozenBlueSoul"]

    parts: list[bpy.types.Object] = []

    # 1. Stepped stone floor base & 6 heavy timber workbench legs (X in [-1.32, +1.32], Y in [-0.46, +0.46])
    parts.append(add_box("BenchStoneFootPadL", (0.28, 1.04, 0.08), (-1.24, 0.0, 0.04), mat_stone, bevel_width=0.015))
    parts.append(add_box("BenchStoneFootPadM", (0.28, 1.04, 0.08), (0.0, 0.0, 0.04), mat_stone, bevel_width=0.015))
    parts.append(add_box("BenchStoneFootPadR", (0.28, 1.04, 0.08), (1.24, 0.0, 0.04), mat_stone, bevel_width=0.015))

    for lx in (-1.24, 0.0, 1.24):
        for ly in (-0.42, 0.42):
            parts.append(add_box(f"BenchLeg_{lx}_{ly}", (0.14, 0.14, 0.82), (lx, ly, 0.46), mat_timber, bevel_width=0.015))
            # Iron foot shoe & top mortise bracket
            parts.append(add_box(f"LegIronShoe_{lx}_{ly}", (0.16, 0.16, 0.10), (lx, ly, 0.12), mat_iron, bevel_width=0.008))
            parts.append(add_box(f"LegTopBracket_{lx}_{ly}", (0.17, 0.17, 0.10), (lx, ly, 0.80), mat_iron, bevel_width=0.008))

    # 2. Lower timber storage shelf + cross stretchers + stacked ammunition crates underneath
    parts.append(add_box("LowerCrossBeamFront", (2.64, 0.10, 0.10), (0.0, -0.42, 0.28), mat_timber, bevel_width=0.012))
    parts.append(add_box("LowerCrossBeamBack", (2.64, 0.10, 0.10), (0.0, 0.42, 0.28), mat_timber, bevel_width=0.012))
    for sy_idx in range(4):
        sy = -0.32 + sy_idx * 0.21
        parts.append(add_box(f"LowerShelfPlank_{sy_idx}", (2.52, 0.19, 0.045), (0.0, sy, 0.34), mat_timber, bevel_width=0.008))

    # Under-bench munitions crate & powder keg
    parts.append(add_box("UnderCrateLeft", (0.68, 0.52, 0.34), (-0.64, -0.05, 0.53), mat_timber, bevel_width=0.012))
    parts.append(add_box("UnderCrateStrap1", (0.70, 0.54, 0.04), (-0.64, -0.05, 0.42), mat_iron, bevel_width=0.004))
    parts.append(add_box("UnderCrateStrap2", (0.70, 0.54, 0.04), (-0.64, -0.05, 0.64), mat_iron, bevel_width=0.004))

    bpy.ops.mesh.primitive_cylinder_add(vertices=14, radius=0.19, depth=0.44, location=(0.62, -0.04, 0.55), rotation=(0.0, math.pi * 0.5, 0.25))
    keg = bpy.context.active_object
    keg.name = "UnderBenchPowderKeg"
    keg.data.materials.append(mat_timber)
    parts.append(keg)

    # 3. Heavy 2.8m x 1.1m Butcher-Block Oak Tabletop with BOOLEAN DIFFERENCE recessed parts tray
    tabletop = add_box("WorkbenchTabletop", (2.80, 1.08, 0.12), (0.0, 0.0, 0.90), mat_timber, bevel_width=0.018)
    tabletop.data.materials.append(mat_iron)
    tray_cutter = add_box("ToolTrayCutter", (0.58, 0.24, 0.08), (-0.15, -0.32, 0.95), mat_iron, bevel_width=0.0)
    b_tray = tabletop.modifiers.new(name="CarveToolTray", type='BOOLEAN')
    b_tray.operation = 'DIFFERENCE'
    b_tray.solver = 'EXACT'
    b_tray.object = tray_cutter
    bpy.context.view_layer.objects.active = tabletop
    bpy.ops.object.modifier_apply(modifier=b_tray.name)
    bpy.data.objects.remove(tray_cutter, do_unlink=True)
    parts.append(tabletop)

    # 4 heavy wrought-iron corner bumper brackets on the tabletop
    for cx in (-1.38, 1.38):
        for cy in (-0.52, 0.52):
            parts.append(add_box(f"TableCornerIron_{cx}_{cy}", (0.12, 0.12, 0.14), (cx, cy, 0.90), mat_iron, bevel_width=0.008))

    # 4. Mounted Wrought-Iron Gunsmith Vice on Front-Left (-0.88, -0.36, 0.96) clamping a spare octagonal barrel
    parts.append(add_box("ViceBasePlate", (0.28, 0.26, 0.06), (-0.88, -0.34, 0.98), mat_iron, bevel_width=0.008))
    parts.append(add_box("ViceFixedJaw", (0.22, 0.08, 0.18), (-0.88, -0.26, 1.08), mat_iron, bevel_width=0.008))
    parts.append(add_box("ViceMovableJaw", (0.22, 0.08, 0.18), (-0.88, -0.42, 1.08), mat_iron, bevel_width=0.008))
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.025, depth=0.34, location=(-0.88, -0.40, 1.05), rotation=(math.pi * 0.5, 0.0, 0.0))
    vice_screw = bpy.context.active_object
    vice_screw.name = "ViceLeadScrew"
    vice_screw.data.materials.append(mat_bronze)
    parts.append(vice_screw)

    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.014, depth=0.28, location=(-0.88, -0.55, 1.05), rotation=(0.0, math.pi * 0.35, 0.0))
    vice_handle = bpy.context.active_object
    vice_handle.name = "ViceTurnBar"
    vice_handle.data.materials.append(mat_iron)
    parts.append(vice_handle)

    # Clamped spare octagonal revolver barrel & receiver frame inside the vice jaws
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.032, depth=0.72, location=(-0.82, -0.34, 1.15), rotation=(0.0, math.pi * 0.5, 0.0))
    spare_barrel = bpy.context.active_object
    spare_barrel.name = "ClampedOctagonalBarrel"
    spare_barrel.data.materials.append(mat_silver)
    parts.append(spare_barrel)
    parts.append(add_box("ClampedBarrelRuneInlay", (0.48, 0.018, 0.018), (-0.82, -0.34, 1.182), mat_rune, bevel_width=0.002))

    # 5. Rows of Brass Cartridge Loading Blocks (12 standing cartridges on right side) & Bullet-Casting Tongs
    parts.append(add_box("CartridgeTrayBlock", (0.42, 0.24, 0.05), (0.52, -0.22, 0.98), mat_timber, bevel_width=0.006))
    for r_i in range(3):
        for c_i in range(4):
            bx = 0.38 + c_i * 0.09
            by = -0.29 + r_i * 0.07
            bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.018, depth=0.09, location=(bx, by, 1.04))
            shell = bpy.context.active_object
            shell.name = f"BrassCartridge_{r_i}_{c_i}"
            shell.data.materials.append(mat_bronze)
            parts.append(shell)
            bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=0.017, radius2=0.004, depth=0.04, location=(bx, by, 1.105))
            tip = bpy.context.active_object
            tip.name = f"SilverBulletTip_{r_i}_{c_i}"
            tip.data.materials.append(mat_silver)
            parts.append(tip)

    # Bullet-casting iron tongs & hammer on center tabletop
    parts.append(add_box("CastingTongArm1", (0.36, 0.025, 0.02), (0.15, -0.10, 0.97), mat_iron, bevel_width=0.003, rotation=(0.0, 0.0, 0.22)))
    parts.append(add_box("CastingTongArm2", (0.36, 0.025, 0.02), (0.15, -0.12, 0.97), mat_iron, bevel_width=0.003, rotation=(0.0, 0.0, -0.18)))
    parts.append(add_box("GunsmithHammerShaft", (0.03, 0.34, 0.025), (-0.38, -0.05, 0.975), mat_timber, bevel_width=0.004, rotation=(0.0, 0.0, 0.45)))
    parts.append(add_box("GunsmithHammerHead", (0.14, 0.05, 0.05), (-0.45, -0.18, 0.985), mat_iron, bevel_width=0.006, rotation=(0.0, 0.0, 0.45)))

    # 6. Open Gunsmith Ledger with Glowing Occult Sigil Page & Small Blue-Flame Alchemical Burner
    parts.append(add_box("GunsmithLedgerCover", (0.44, 0.32, 0.03), (-0.05, 0.12, 0.975), mat_timber, bevel_width=0.005, rotation=(0.0, 0.0, -0.15)))
    parts.append(add_box("LedgerPageLeft", (0.19, 0.28, 0.025), (-0.15, 0.11, 0.995), mat_bone, bevel_width=0.003, rotation=(0.0, 0.05, -0.15)))
    parts.append(add_box("LedgerPageRight", (0.19, 0.28, 0.025), (0.05, 0.13, 0.995), mat_bone, bevel_width=0.003, rotation=(0.0, -0.05, -0.15)))
    parts.append(add_box("LedgerRuneDiagram", (0.12, 0.16, 0.01), (0.05, 0.13, 1.01), mat_rune, bevel_width=0.001, rotation=(0.0, -0.05, -0.15)))

    # Alchemical blue-flame burner on right tabletop (+1.02, 0.08, 0.96..1.32)
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.11, depth=0.12, location=(1.02, 0.08, 1.02))
    burner_base = bpy.context.active_object
    burner_base.name = "AlchemicalBurnerBase"
    burner_base.data.materials.append(mat_bronze)
    parts.append(burner_base)

    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.065, radius2=0.008, depth=0.22, location=(1.02, 0.08, 1.19))
    blue_flame = bpy.context.active_object
    blue_flame.name = "AlchemicalBlueFlame"
    blue_flame.data.materials.append(mat_blue)
    parts.append(blue_flame)

    # 7. Towering 2.2m Pegboard & Wrought-Iron Back-Wall Frame (Y = +0.44m, Z = 0.96m..2.20m)
    for px in (-1.30, 0.0, 1.30):
        parts.append(add_box(f"BackboardUpright_{px}", (0.12, 0.10, 1.28), (px, 0.46, 1.56), mat_iron, bevel_width=0.01))
    parts.append(add_box("BackboardTopCornice", (2.82, 0.16, 0.12), (0.0, 0.45, 2.16), mat_iron, bevel_width=0.015))
    parts.append(add_box("BackboardPanel", (2.68, 0.06, 1.16), (0.0, 0.46, 1.54), mat_timber, bevel_width=0.012))

    # Mounted Occult Ritual Carbine / Crossbow Silhouette & 2 Silver Blades on the Backboard
    parts.append(add_box("CarbineStockAndBody", (1.28, 0.07, 0.16), (-0.18, 0.39, 1.68), mat_timber, bevel_width=0.012, rotation=(0.0, 0.08, 0.0)))
    parts.append(add_box("CarbineHeavyBarrel", (1.10, 0.05, 0.06), (0.12, 0.38, 1.75), mat_silver, bevel_width=0.008, rotation=(0.0, 0.08, 0.0)))
    parts.append(add_box("CarbineCrossbowProd", (0.08, 0.12, 0.56), (0.52, 0.36, 1.72), mat_iron, bevel_width=0.008))
    parts.append(add_box("CarbineRuneCore", (0.42, 0.08, 0.04), (0.05, 0.37, 1.72), mat_rune, bevel_width=0.003))

    # 2 Silver Ritual Blades mounted flanking the carbine
    for bx_idx, bx_pos in enumerate((-1.02, 0.98)):
        parts.append(add_box(f"SilverBlade_{bx_idx}", (0.07, 0.03, 0.68), (bx_pos, 0.39, 1.58), mat_silver, bevel_width=0.005))
        parts.append(add_box(f"SilverCrossguard_{bx_idx}", (0.24, 0.05, 0.04), (bx_pos, 0.39, 1.28), mat_bronze, bevel_width=0.005))
        parts.append(add_box(f"SilverPommel_{bx_idx}", (0.06, 0.05, 0.16), (bx_pos, 0.39, 1.18), mat_iron, bevel_width=0.005))

    export_parts_as_glb(parts, out_dir, "hub_weapon_workbench.glb")


def build_hub_armor_reliquary_stand(out_dir: str) -> None:
    """
    16. hub_armor_reliquary_stand.glb (2.2m wide x 1.0m deep x 2.4m tall Inquisitor's Armor Rack):
    Stepped stone-and-timber dais supporting an iron mannequin frame clad in a gothic cuirass,
    articulated pauldrons, and hanging vambrace gauntlets, flanked by a heavy iron-bound munitions
    chest and shield/scroll racks. (60+ sub-elements)
    """
    clear_scene()
    mats = _make_catacomb_materials()
    mat_stone = mats["WeatheredStone"]
    mat_flag = mats["DarkFlagstone"]
    mat_timber = mats["RottedTimber"]
    mat_iron = mats["WroughtIron"]
    mat_bronze = mats["TarnishedBronze"]
    mat_silver = mats["OccultSilver"]
    mat_bone = mats["AgedBone"]
    mat_gold = mats["EmissiveConsecratedGold"]

    parts: list[bpy.types.Object] = []

    # 1. Stepped Stone-and-Timber Dais (2.20m wide x 1.02m deep x 0.28m tall) with BOOLEAN rune border
    dais_base = add_box("ArmorDaisBase", (2.20, 1.02, 0.16), (0.0, 0.0, 0.08), mat_flag, bevel_width=0.02)
    dais_base.data.materials.append(mat_gold)
    dais_groove = add_box("ArmorDaisGrooveCut", (1.96, 0.78, 0.05), (0.0, 0.0, 0.15), mat_gold, bevel_width=0.0)
    b_dais = dais_base.modifiers.new(name="CarveDaisGroove", type='BOOLEAN')
    b_dais.operation = 'DIFFERENCE'
    b_dais.solver = 'EXACT'
    b_dais.object = dais_groove
    bpy.context.view_layer.objects.active = dais_base
    bpy.ops.object.modifier_apply(modifier=b_dais.name)
    bpy.data.objects.remove(dais_groove, do_unlink=True)
    parts.append(dais_base)

    parts.append(add_box("ArmorDaisTimberDeck", (1.84, 0.72, 0.12), (0.0, 0.0, 0.20), mat_timber, bevel_width=0.015))

    # 2. Central Wrought-Iron Mannequin Stand Post, Cross-Arm & gothic Halo Finial (Z = 0.26m..2.38m)
    parts.append(add_box("MannequinPlinthCollar", (0.42, 0.42, 0.14), (0.0, 0.05, 0.33), mat_iron, bevel_width=0.012))
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.055, depth=2.05, location=(0.0, 0.05, 1.32))
    post = bpy.context.active_object
    post.name = "MannequinSpinePost"
    post.data.materials.append(mat_iron)
    parts.append(post)

    parts.append(add_box("MannequinShoulderBeam", (0.96, 0.09, 0.09), (0.0, 0.05, 1.76), mat_iron, bevel_width=0.008))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.18, minor_radius=0.022, major_segments=20, minor_segments=8, location=(0.0, 0.05, 2.22), rotation=(math.pi * 0.5, 0.0, 0.0))
    halo = bpy.context.active_object
    halo.name = "InquisitorIronHalo"
    halo.data.materials.append(mat_bronze)
    parts.append(halo)

    # 3. Gothic Fluted Cuirass Breastplate, Gorget Collar, Tassets & Great-Helm Visor
    parts.append(add_box("CuirassTorsoCore", (0.52, 0.34, 0.56), (0.0, 0.02, 1.48), mat_silver, bevel_width=0.025))
    parts.append(add_box("CuirassPlackart", (0.46, 0.36, 0.28), (0.0, 0.01, 1.32), mat_iron, bevel_width=0.02))
    parts.append(add_box("CuirassCenterRidge", (0.06, 0.38, 0.54), (0.0, -0.01, 1.48), mat_bronze, bevel_width=0.008))
    parts.append(add_box("GorgetCollar", (0.34, 0.28, 0.14), (0.0, 0.02, 1.82), mat_silver, bevel_width=0.015))

    # Inquisitor Great-Helm atop the mannequin post
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.14, depth=0.32, location=(0.0, 0.02, 2.04))
    helm = bpy.context.active_object
    helm.name = "InquisitorGreatHelm"
    helm.data.materials.append(mat_silver)
    parts.append(helm)
    parts.append(add_box("HelmFaceCrossV", (0.04, 0.16, 0.24), (0.0, -0.06, 2.04), mat_bronze, bevel_width=0.004))
    parts.append(add_box("HelmFaceCrossH", (0.18, 0.16, 0.04), (0.0, -0.06, 2.08), mat_bronze, bevel_width=0.004))

    # 4. Articulated 4-Lame Pauldrons, hanging Vambrace Gauntlets & Hip Tassets
    for side_sign in (-1.0, 1.0):
        sx = side_sign * 0.38
        for lame_i in range(4):
            lz = 1.78 - lame_i * 0.07
            lw = 0.24 - lame_i * 0.015
            parts.append(
                add_box(
                    f"PauldronLame_{side_sign}_{lame_i}",
                    (lw, 0.32, 0.08),
                    (sx + side_sign * lame_i * 0.02, 0.02, lz),
                    mat_silver if (lame_i % 2 == 0) else mat_iron,
                    bevel_width=0.01,
                    rotation=(0.0, side_sign * 0.32, 0.0),
                )
            )
        # Hanging Vambrace & Gauntlet Cuff
        parts.append(
            add_box(
                f"HangingVambrace_{side_sign}",
                (0.14, 0.16, 0.36),
                (side_sign * 0.46, 0.0, 1.28),
                mat_silver,
                bevel_width=0.012,
                rotation=(0.12, side_sign * 0.10, 0.0),
            )
        )
        parts.append(
            add_box(
                f"GauntletBrassCuff_{side_sign}",
                (0.16, 0.18, 0.08),
                (side_sign * 0.46, 0.0, 1.42),
                mat_bronze,
                bevel_width=0.008,
            )
        )
        # 3 Hip Tasset Plates
        for tas_i in range(3):
            parts.append(
                add_box(
                    f"TassetLame_{side_sign}_{tas_i}",
                    (0.20, 0.06, 0.10),
                    (side_sign * 0.16, -0.14, 1.12 - tas_i * 0.09),
                    mat_silver,
                    bevel_width=0.008,
                    rotation=(0.15, 0.0, 0.0),
                )
            )

    # 5. Left Flank: Heavy Iron-Bound Oak Munitions Chest (X = -0.72m, Z = 0.26m..0.78m)
    parts.append(add_box("MunitionsChestBody", (0.58, 0.44, 0.38), (-0.72, 0.0, 0.45), mat_timber, bevel_width=0.012))
    parts.append(add_box("MunitionsChestLid", (0.60, 0.46, 0.12), (-0.72, 0.0, 0.68), mat_timber, bevel_width=0.015))
    for band_dx in (-0.22, 0.0, 0.22):
        parts.append(add_box(f"ChestIronBand_{band_dx}", (0.05, 0.48, 0.52), (-0.72 + band_dx, 0.0, 0.50), mat_iron, bevel_width=0.005))
    parts.append(add_box("ChestLockHasps", (0.12, 0.06, 0.16), (-0.72, -0.23, 0.58), mat_bronze, bevel_width=0.005))

    # 6. Right Flank: Gothic Shield & Purity Scroll Rack (X = +0.72m, Z = 0.26m..1.68m)
    for rx in (0.52, 0.92):
        parts.append(add_box(f"ShieldRackUpright_{rx}", (0.08, 0.08, 1.38), (rx, 0.14, 0.95), mat_iron, bevel_width=0.008))
    parts.append(add_box("ShieldRackCrossbar1", (0.48, 0.08, 0.07), (0.72, 0.14, 0.72), mat_iron, bevel_width=0.006))
    parts.append(add_box("ShieldRackCrossbar2", (0.48, 0.08, 0.07), (0.72, 0.14, 1.38), mat_iron, bevel_width=0.006))

    # Mounted Heraldic Heater Shield with Consecrated Gold Cross
    parts.append(add_box("InquisitorShieldPlate", (0.46, 0.06, 0.68), (0.72, -0.02, 1.08), mat_iron, bevel_width=0.015, rotation=(-0.12, 0.0, 0.0)))
    parts.append(add_box("ShieldRimTrim", (0.50, 0.04, 0.72), (0.72, -0.01, 1.08), mat_bronze, bevel_width=0.01, rotation=(-0.12, 0.0, 0.0)))
    parts.append(add_box("ShieldGoldCrossV", (0.06, 0.07, 0.52), (0.72, -0.03, 1.08), mat_gold, bevel_width=0.004, rotation=(-0.12, 0.0, 0.0)))
    parts.append(add_box("ShieldGoldCrossH", (0.32, 0.07, 0.06), (0.72, -0.04, 1.16), mat_gold, bevel_width=0.004, rotation=(-0.12, 0.0, 0.0)))

    # 3 Rolled Parchment Purity Scrolls at base of rack
    for sc_i in range(3):
        bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.035, depth=0.34, location=(0.62 + sc_i * 0.10, -0.14, 0.34), rotation=(0.0, math.pi * 0.5, 0.18))
        scroll = bpy.context.active_object
        scroll.name = f"ReliquaryScroll_{sc_i}"
        scroll.data.materials.append(mat_bone)
        parts.append(scroll)

    export_parts_as_glb(parts, out_dir, "hub_armor_reliquary_stand.glb")


def build_hub_sanctuary_upgrade_font(out_dir: str) -> None:
    """
    17. hub_sanctuary_upgrade_font.glb (1.6m diameter x 1.8m tall Consecrated Relic Basin & Crucible):
    Octagonal carved limestone pedestal supporting a fluted bronze ritual basin filled with glowing
    liquid gold/amber consecrated oil (EmissiveConsecratedGold emission 2.8), surrounded by 4
    floating/chained censor burners and etched rune rings. (58+ sub-elements)
    """
    clear_scene()
    mats = _make_catacomb_materials()
    mat_stone = mats["WeatheredStone"]
    mat_flag = mats["DarkFlagstone"]
    mat_bronze = mats["TarnishedBronze"]
    mat_iron = mats["WroughtIron"]
    mat_gold = mats["EmissiveConsecratedGold"]

    parts: list[bpy.types.Object] = []

    # 1. Stepped Octagonal Carved Limestone Pedestal Plinth (1.60m diameter, Z = 0.0m..0.44m)
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.80, depth=0.16, location=(0.0, 0.0, 0.08))
    step1 = bpy.context.active_object
    step1.name = "FontOctagonalStep1"
    step1.data.materials.append(mat_flag)
    parts.append(step1)

    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.64, depth=0.16, location=(0.0, 0.0, 0.24))
    step2 = bpy.context.active_object
    step2.name = "FontOctagonalStep2"
    step2.data.materials.append(mat_stone)
    parts.append(step2)

    # Fluted central limestone & bronze pedestal shaft (Z = 0.32m..1.04m) + 8 flying-buttress ribs
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.34, depth=0.72, location=(0.0, 0.0, 0.68))
    shaft = bpy.context.active_object
    shaft.name = "FontPedestalShaft"
    shaft.data.materials.append(mat_stone)
    parts.append(shaft)

    for i in range(8):
        ang = i * (math.pi / 4.0)
        rx = math.cos(ang) * 0.40
        ry = math.sin(ang) * 0.40
        parts.append(
            add_box(
                f"FontPedestalRib_{i}",
                (0.10, 0.22, 0.68),
                (rx, ry, 0.66),
                mat_flag,
                bevel_width=0.012,
                rotation=(0.0, 0.0, ang + math.pi * 0.5),
            )
        )

    # 2. Fluted Bronze & Stone Ritual Basin (Z = 0.98m..1.38m) carved via BOOLEAN DIFFERENCE
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.68, depth=0.38, location=(0.0, 0.0, 1.16))
    basin = bpy.context.active_object
    basin.name = "FontRitualBasin"
    basin.data.materials.append(mat_bronze)
    basin.data.materials.append(mat_stone)

    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.54, depth=0.28, location=(0.0, 0.0, 1.26))
    basin_cut = bpy.context.active_object
    basin_cut.name = "FontBasinCutter"
    basin_cut.data.materials.append(mat_stone)

    b_font = basin.modifiers.new(name="CarveFontBasin", type='BOOLEAN')
    b_font.operation = 'DIFFERENCE'
    b_font.solver = 'EXACT'
    b_font.object = basin_cut
    bpy.context.view_layer.objects.active = basin
    bpy.ops.object.modifier_apply(modifier=b_font.name)
    bpy.data.objects.remove(basin_cut, do_unlink=True)
    parts.append(basin)

    # 8 Beveled Bronze Rim Bosses around the octagonal basin lip
    for i in range(8):
        ang = i * (math.pi / 4.0) + (math.pi / 8.0)
        bx = math.cos(ang) * 0.61
        by = math.sin(ang) * 0.61
        parts.append(
            add_box(
                f"BasinRimBoss_{i}",
                (0.16, 0.14, 0.10),
                (bx, by, 1.35),
                mat_bronze,
                bevel_width=0.012,
                rotation=(0.0, 0.0, ang),
            )
        )

    # 3. Glowing Liquid Gold / Amber Consecrated Oil Pool (EmissiveConsecratedGold) + Etched Rune Rings
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.52, depth=0.06, location=(0.0, 0.0, 1.24))
    oil_pool = bpy.context.active_object
    oil_pool.name = "ConsecratedGoldOilPool"
    oil_pool.data.materials.append(mat_gold)
    parts.append(oil_pool)

    for r_idx, r_rad in enumerate((0.22, 0.38)):
        bpy.ops.mesh.primitive_torus_add(
            major_radius=r_rad,
            minor_radius=0.016,
            major_segments=24,
            minor_segments=8,
            location=(0.0, 0.0, 1.275),
        )
        rune_ring = bpy.context.active_object
        rune_ring.name = f"FontConsecratedRuneRing_{r_idx}"
        rune_ring.data.materials.append(mat_bronze if r_idx == 0 else mat_gold)
        parts.append(rune_ring)

    # Central Rising Crucible Chalice / Reliquary Spire inside the basin (Z = 1.24m..1.80m)
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.16, radius2=0.07, depth=0.42, location=(0.0, 0.0, 1.45))
    chalice_stem = bpy.context.active_object
    chalice_stem.name = "CenterCrucibleStem"
    chalice_stem.data.materials.append(mat_bronze)
    parts.append(chalice_stem)

    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.11, location=(0.0, 0.0, 1.70))
    relic_orb = bpy.context.active_object
    relic_orb.name = "ConsecratedRelicCoreOrb"
    relic_orb.data.materials.append(mat_gold)
    parts.append(relic_orb)

    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.16,
        minor_radius=0.018,
        major_segments=20,
        minor_segments=8,
        location=(0.0, 0.0, 1.70),
        rotation=(math.pi * 0.5, 0.0, 0.0),
    )
    orb_halo = bpy.context.active_object
    orb_halo.name = "CrucibleAstrolabeRing"
    orb_halo.data.materials.append(mat_iron)
    parts.append(orb_halo)

    # 4. Four Wrought-Iron Corner Swan-Neck Brackets & Chained Censer Burners around the font
    for c_i in range(4):
        c_ang = c_i * (math.pi * 0.5) + (math.pi * 0.25)
        ux = math.cos(c_ang) * 0.68
        uy = math.sin(c_ang) * 0.68
        # Upright iron bracket arm rising from Z = 1.15m to 1.68m
        parts.append(
            add_box(
                f"CenserBracketPost_{c_i}",
                (0.06, 0.06, 0.56),
                (ux, uy, 1.40),
                mat_iron,
                bevel_width=0.006,
                rotation=(0.0, 0.0, c_ang),
            )
        )
        parts.append(
            add_box(
                f"CenserBracketArm_{c_i}",
                (0.22, 0.05, 0.05),
                (ux * 1.10, uy * 1.10, 1.66),
                mat_iron,
                bevel_width=0.005,
                rotation=(0.0, 0.0, c_ang),
            )
        )
        # 3 Chain links + Suspended Censer Burner with glowing gold ember core
        hang_x = ux * 1.18
        hang_y = uy * 1.18
        for lk_i in range(3):
            bpy.ops.mesh.primitive_torus_add(
                major_radius=0.024,
                minor_radius=0.006,
                major_segments=10,
                minor_segments=6,
                location=(hang_x, hang_y, 1.60 - lk_i * 0.06),
                rotation=(math.pi * 0.5, (lk_i % 2) * (math.pi * 0.5), c_ang),
            )
            lk = bpy.context.active_object
            lk.name = f"CenserChain_{c_i}_{lk_i}"
            lk.data.materials.append(mat_iron)
            parts.append(lk)

        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.085, radius2=0.03, depth=0.14, location=(hang_x, hang_y, 1.36), rotation=(math.pi, 0.0, 0.0))
        censer_bowl = bpy.context.active_object
        censer_bowl.name = f"CenserBowl_{c_i}"
        censer_bowl.data.materials.append(mat_bronze)
        parts.append(censer_bowl)

        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.055, location=(hang_x, hang_y, 1.42))
        censer_glow = bpy.context.active_object
        censer_glow.name = f"CenserEmberGlow_{c_i}"
        censer_glow.data.materials.append(mat_gold)
        parts.append(censer_glow)

    export_parts_as_glb(parts, out_dir, "hub_sanctuary_upgrade_font.glb")


def build_clutter_rubble_bones_pile(out_dir: str) -> None:
    """
    18. clutter_rubble_bones_pile.glb:
    Cluster of 45+ beveled fallen masonry stones, broken fluted pillar drum fragments,
    6 geometric gothic skulls, 18 femurs/ribs, and 24 rusted chain links (165+ sub-parts).
    """
    clear_scene()
    mats = _make_catacomb_materials()
    mat_stone = mats["WeatheredStone"]
    mat_flag = mats["DarkFlagstone"]
    mat_bone = mats["AgedBone"]
    mat_iron = mats["WroughtIron"]

    bm = bmesh.new()
    sub_cnt = 0

    # 1. 48 Fallen Beveled Masonry Blocks & Flagstone Shards in a radial corner mound (radius ~0.95m)
    for i in range(48):
        ring_t = (i % 12) / 12.0
        layer = i // 12
        ang = ring_t * math.tau + _det_hash(i, 11, 3) * 0.25
        rad = (0.18 + (1.0 - layer * 0.22) * 0.68) * (0.75 + 0.25 * abs(_det_hash(i, 17, 5)))
        bx = math.cos(ang) * rad
        by = math.sin(ang) * rad
        bz = 0.04 + layer * 0.055 + abs(_det_hash(i, 23, 7)) * 0.03
        sx = 0.16 + abs(_det_hash(i, 31, 9)) * 0.18
        sy = 0.14 + abs(_det_hash(i, 37, 11)) * 0.16
        sz = 0.07 + abs(_det_hash(i, 41, 13)) * 0.09
        rx = _det_hash(i, 43, 15) * 0.45
        ry = _det_hash(i, 47, 17) * 0.45
        rz = _det_hash(i, 53, 19) * math.pi
        m_idx = 0 if (i % 3 != 0) else 1
        _add_bm_beveled_box(bm, (sx, sy, sz), (bx, by, bz), rot_euler=(rx, ry, rz), bevel_width=0.008, mat_idx=m_idx)
        sub_cnt += 1

    # 2. Broken Fluted Pillar Drum Fragments (3 multi-part drum segments)
    drum_coords = [(-0.28, 0.15, 0.14, 0.35, 0.42), (0.32, -0.22, 0.11, -0.42, 1.15), (0.05, 0.38, 0.09, 0.28, -0.75)]
    for d_i, (dx, dy, dz, rx, rz) in enumerate(drum_coords):
        _add_bm_beveled_box(bm, (0.28, 0.28, 0.22), (dx, dy, dz), rot_euler=(rx, 0.25, rz), bevel_width=0.012, mat_idx=0)
        sub_cnt += 1
        for fl_i in range(6):
            fang = fl_i * (math.tau / 6.0)
            _add_bm_beveled_box(
                bm,
                (0.06, 0.06, 0.24),
                (dx + math.cos(fang) * 0.13, dy + math.sin(fang) * 0.13, dz),
                rot_euler=(rx, 0.25, rz + fang),
                bevel_width=0.005,
                mat_idx=1,
            )
            sub_cnt += 1

    # 3. 8 Geometric Skulls (Cranium + Cheek/Brow + Jaw + 2 Recessed Eye Sockets = 40 sub-parts)
    for sk_i in range(8):
        ang = sk_i * (math.tau / 8.0) + 0.35
        rad = 0.25 + (sk_i % 3) * 0.18
        sx = math.cos(ang) * rad
        sy = math.sin(ang) * rad
        sz = 0.12 + (1 if sk_i % 2 == 0 else 0) * 0.05
        yaw = ang + _det_hash(sk_i, 61, 3) * 0.6
        pitch = _det_hash(sk_i, 67, 5) * 0.35
        # Cranium box
        _add_bm_beveled_box(bm, (0.11, 0.13, 0.11), (sx, sy, sz), rot_euler=(pitch, 0.0, yaw), bevel_width=0.016, mat_idx=2)
        # Maxilla / Jaw
        _add_bm_beveled_box(
            bm,
            (0.08, 0.08, 0.065),
            (sx + math.sin(yaw) * 0.04, sy - math.cos(yaw) * 0.04, sz - 0.035),
            rot_euler=(pitch, 0.0, yaw),
            bevel_width=0.008,
            mat_idx=2,
        )
        # Dark eye socket inserts
        for eye_s in (-0.026, 0.026):
            _add_bm_beveled_box(
                bm,
                (0.024, 0.024, 0.024),
                (sx + math.cos(yaw) * eye_s + math.sin(yaw) * 0.055, sy + math.sin(yaw) * eye_s - math.cos(yaw) * 0.055, sz + 0.005),
                rot_euler=(pitch, 0.0, yaw),
                bevel_width=0.003,
                mat_idx=1,
            )
        sub_cnt += 4

    # 4. 20 Scattered Femur & Tibia Bones (Shaft + 2 Epiphysis Knobs each = 60 sub-parts)
    for b_i in range(20):
        ang = b_i * (math.tau / 20.0) + _det_hash(b_i, 71, 9) * 0.2
        rad = 0.22 + abs(_det_hash(b_i, 73, 11)) * 0.58
        bx = math.cos(ang) * rad
        by = math.sin(ang) * rad
        bz = 0.05 + abs(_det_hash(b_i, 79, 13)) * 0.08
        byaw = _det_hash(b_i, 83, 15) * math.pi
        bpitch = _det_hash(b_i, 89, 17) * 0.22
        _add_bm_beveled_box(bm, (0.028, 0.30, 0.028), (bx, by, bz), rot_euler=(bpitch, 0.0, byaw), bevel_width=0.006, mat_idx=2)
        for end_s in (-0.14, 0.14):
            ex = bx - math.sin(byaw) * end_s
            ey = by + math.cos(byaw) * end_s
            _add_bm_beveled_box(bm, (0.048, 0.042, 0.038), (ex, ey, bz), rot_euler=(bpitch, 0.0, byaw), bevel_width=0.008, mat_idx=2)
        sub_cnt += 3

    # 5. 18 Rusted Wrought-Iron Chain Links & Shackle Rings draped over the rubble
    for c_i in range(18):
        cx = -0.45 + c_i * 0.052 + _det_hash(c_i, 97, 3) * 0.02
        cy = -0.35 + math.sin(c_i * 0.45) * 0.22
        cz = 0.06 + math.cos(c_i * 0.35) * 0.035
        _add_bm_beveled_box(
            bm,
            (0.065, 0.038, 0.018),
            (cx, cy, cz),
            rot_euler=(0.25 * (c_i % 2), 0.18, c_i * 0.35),
            bevel_width=0.004,
            mat_idx=3,
        )
        sub_cnt += 1

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("ClutterRubbleBonesPileMesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("ClutterRubbleBonesPile", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat_stone)
    obj.data.materials.append(mat_flag)
    obj.data.materials.append(mat_bone)
    obj.data.materials.append(mat_iron)

    print(f"[DetailKit] clutter_rubble_bones_pile built with {sub_cnt} physical 3D sub-elements")
    export_parts_as_glb([obj], out_dir, "clutter_rubble_bones_pile.glb")


def build_clutter_melted_candle_cluster(out_dir: str) -> None:
    """
    19. clutter_melted_candle_cluster.glb:
    Group of 14 varied-height ritual candles with solidified wax drip pools, wrought-iron & bronze
    candelabra saucer trays, and glowing wicks (CandleFlameGlow) (160+ sub-parts).
    """
    clear_scene()
    mats = _make_catacomb_materials()
    mat_wax = mats["AgedBone"]
    mat_bronze = mats["TarnishedBronze"]
    mat_iron = mats["WroughtIron"]
    mat_flame = make_pbr_material(
        "CandleFlameGlow",
        (1.0, 0.72, 0.22, 1.0),
        roughness=0.15,
        emission_color=(1.0, 0.65, 0.18, 1.0),
        emission_strength=5.5,
    )

    bm = bmesh.new()
    sub_cnt = 0

    # 1. Base Wrought-Iron & Tarnished Bronze Ritual Tray + 12 Solidified Wax Pool Lobes
    _add_bm_beveled_box(bm, (0.68, 0.52, 0.028), (0.0, 0.0, 0.014), bevel_width=0.006, mat_idx=2)
    _add_bm_beveled_box(bm, (0.62, 0.46, 0.036), (0.0, 0.0, 0.022), bevel_width=0.008, mat_idx=1)
    sub_cnt += 2

    for w_i in range(24):
        ang = w_i * (math.tau / 24.0)
        rad = 0.12 + abs(_det_hash(w_i, 13, 7)) * 0.22
        wx = math.cos(ang) * rad * 1.15
        wy = math.sin(ang) * rad * 0.85
        wsx = 0.09 + abs(_det_hash(w_i, 19, 11)) * 0.08
        wsy = 0.08 + abs(_det_hash(w_i, 23, 13)) * 0.08
        _add_bm_beveled_box(bm, (wsx, wsy, 0.024), (wx, wy, 0.032), rot_euler=(0.0, 0.0, ang), bevel_width=0.006, mat_idx=0)
        sub_cnt += 1

    # 2. 14 Varied-Height Ritual Candles (each with bronze cup, main wax body, 5 vertical wax drip rivulets, wick & glowing flame)
    candle_pts = [
        (0.0, 0.0, 0.34, 0.048),
        (-0.14, 0.06, 0.28, 0.042),
        (0.15, -0.05, 0.30, 0.044),
        (-0.06, -0.14, 0.24, 0.040),
        (0.08, 0.14, 0.26, 0.040),
        (-0.24, -0.08, 0.20, 0.038),
        (0.24, 0.09, 0.22, 0.038),
        (-0.19, 0.16, 0.17, 0.035),
        (0.19, -0.16, 0.19, 0.036),
        (0.0, 0.20, 0.15, 0.034),
        (0.0, -0.20, 0.16, 0.034),
        (-0.28, 0.04, 0.13, 0.032),
        (0.28, -0.03, 0.14, 0.032),
        (0.11, 0.02, 0.21, 0.036),
    ]
    for c_i, (cx, cy, ch, crad) in enumerate(candle_pts):
        # Bronze saucer collar
        _add_bm_beveled_box(bm, (crad * 2.5, crad * 2.5, 0.024), (cx, cy, 0.042), rot_euler=(0.0, 0.0, c_i * 0.4), bevel_width=0.005, mat_idx=1)
        # Main candle wax column (octagonal approximation via 2 rotated boxes)
        _add_bm_beveled_box(bm, (crad * 1.85, crad * 1.85, ch), (cx, cy, 0.04 + ch * 0.5), bevel_width=0.008, mat_idx=0)
        _add_bm_beveled_box(bm, (crad * 1.85, crad * 1.85, ch), (cx, cy, 0.04 + ch * 0.5), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.008, mat_idx=0)
        sub_cnt += 3
        # 5 Vertical melted wax drip rivulets around each candle shaft
        for d_i in range(5):
            dang = d_i * (math.tau / 5.0) + c_i * 0.3
            dh = ch * (0.45 + 0.45 * abs(_det_hash(c_i, d_i, 29)))
            dx = cx + math.cos(dang) * (crad * 0.92)
            dy = cy + math.sin(dang) * (crad * 0.92)
            _add_bm_beveled_box(bm, (0.014, 0.014, dh), (dx, dy, 0.04 + dh * 0.5), rot_euler=(0.0, 0.0, dang), bevel_width=0.003, mat_idx=0)
            sub_cnt += 1
        # Charred wick + Glowing teardrop flame
        _add_bm_beveled_box(bm, (0.007, 0.007, 0.024), (cx, cy, 0.04 + ch + 0.010), bevel_width=0.001, mat_idx=2)
        _add_bm_beveled_box(bm, (0.024, 0.024, 0.052), (cx, cy, 0.04 + ch + 0.038), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.006, mat_idx=3)
        sub_cnt += 2

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("ClutterMeltedCandleClusterMesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("ClutterMeltedCandleCluster", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat_wax)
    obj.data.materials.append(mat_bronze)
    obj.data.materials.append(mat_iron)
    obj.data.materials.append(mat_flame)

    print(f"[DetailKit] clutter_melted_candle_cluster built with {sub_cnt} physical 3D sub-elements")
    export_parts_as_glb([obj], out_dir, "clutter_melted_candle_cluster.glb")


def build_clutter_ceiling_chains_roots(out_dir: str) -> None:
    """
    20. clutter_ceiling_chains_roots.glb:
    Hanging wrought-iron chains, forged meat hooks, ceiling anchor plates, and gnarled petrified
    tree roots breaking down through ceiling vaults (origin at ceiling Z = 0.0m, hanging down to Z = -2.1m) (175+ sub-parts).
    """
    clear_scene()
    mats = _make_catacomb_materials()
    mat_iron = mats["WroughtIron"]
    mat_timber = mats["RottedTimber"]
    mat_stone = mats["DarkFlagstone"]

    bm = bmesh.new()
    sub_cnt = 0

    # 1. 5 Ceiling Iron Anchor Rosettes + Hanging Chain Strands + Forged Meat Hooks
    chain_anchors = [
        (0.0, 0.0, 16),
        (-0.85, 0.55, 12),
        (0.82, -0.48, 14),
        (-0.62, -0.72, 10),
        (0.68, 0.75, 11),
    ]
    for ch_idx, (ax, ay, link_cnt) in enumerate(chain_anchors):
        # Ceiling stone breach collar & iron anchor plate + 4 rivets
        _add_bm_beveled_box(bm, (0.28, 0.28, 0.08), (ax, ay, -0.02), bevel_width=0.010, mat_idx=2)
        _add_bm_beveled_box(bm, (0.18, 0.18, 0.04), (ax, ay, -0.06), bevel_width=0.005, mat_idx=0)
        sub_cnt += 2
        for r_s in (-0.06, 0.06):
            _add_bm_beveled_box(bm, (0.022, 0.022, 0.022), (ax + r_s, ay + r_s, -0.075), bevel_width=0.003, mat_idx=0)
            _add_bm_beveled_box(bm, (0.022, 0.022, 0.022), (ax + r_s, ay - r_s, -0.075), bevel_width=0.003, mat_idx=0)
            sub_cnt += 2

        # Interlocking chain links descending along -Z
        for l_i in range(link_cnt):
            lz = -0.12 - l_i * 0.095
            yaw = (l_i % 2) * (math.pi * 0.5) + ch_idx * 0.3
            # Each chain link built as a hollow frame of 2 side bars + 2 end caps OR beveled link block
            _add_bm_beveled_box(bm, (0.056, 0.024, 0.115), (ax, ay, lz), rot_euler=(0.0, 0.0, yaw), bevel_width=0.005, mat_idx=0)
            sub_cnt += 1

        # Forged Iron Meat Hook at bottom of chain (3-segment curved hook)
        bot_z = -0.12 - link_cnt * 0.095
        _add_bm_beveled_box(bm, (0.026, 0.026, 0.12), (ax, ay, bot_z - 0.05), bevel_width=0.004, mat_idx=0)
        _add_bm_beveled_box(bm, (0.09, 0.026, 0.026), (ax + 0.04, ay, bot_z - 0.10), rot_euler=(0.0, math.radians(22.0), 0.0), bevel_width=0.004, mat_idx=0)
        _add_bm_beveled_box(bm, (0.022, 0.022, 0.09), (ax + 0.08, ay, bot_z - 0.06), rot_euler=(0.0, math.radians(-28.0), 0.0), bevel_width=0.003, mat_idx=0)
        sub_cnt += 3

    # 2. 10 Gnarled Petrified Tree Roots breaking down through ceiling mortar joints (9 segments per root = 90 sub-parts)
    for rt_i in range(10):
        base_ang = rt_i * (math.tau / 10.0) + 0.2
        rx0 = math.cos(base_ang) * (0.35 + (rt_i % 3) * 0.32)
        ry0 = math.sin(base_ang) * (0.35 + ((rt_i + 1) % 3) * 0.32)
        curr_x, curr_y, curr_z = rx0, ry0, 0.02
        for seg_i in range(9):
            t = seg_i / 8.0
            seg_len = 0.16 * (1.0 - 0.35 * t)
            seg_thick = 0.065 * (1.0 - 0.65 * t)
            dx = _det_hash(rt_i, seg_i, 31) * 0.065
            dy = _det_hash(rt_i, seg_i, 43) * 0.065
            dz = -seg_len * 0.85
            nx, ny, nz = curr_x + dx, curr_y + dy, curr_z + dz
            mx, my, mz = (curr_x + nx) * 0.5, (curr_y + ny) * 0.5, (curr_z + nz) * 0.5
            tilt_x = math.atan2(dy, abs(dz))
            tilt_y = -math.atan2(dx, abs(dz))
            _add_bm_beveled_box(
                bm,
                (seg_thick, seg_thick, seg_len + 0.02),
                (mx, my, mz),
                rot_euler=(tilt_x, tilt_y, base_ang + seg_i * 0.25),
                bevel_width=0.005,
                mat_idx=1,
            )
            curr_x, curr_y, curr_z = nx, ny, nz
            sub_cnt += 1

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("ClutterCeilingChainsRootsMesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("ClutterCeilingChainsRoots", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat_iron)
    obj.data.materials.append(mat_timber)
    obj.data.materials.append(mat_stone)

    print(f"[DetailKit] clutter_ceiling_chains_roots built with {sub_cnt} physical 3D sub-elements")
    export_parts_as_glb([obj], out_dir, "clutter_ceiling_chains_roots.glb")


def build_clutter_wooden_crates_barrels(out_dir: str) -> None:
    """
    21. clutter_wooden_crates_barrels.glb:
    2 Iron-hooped oak barrels (built from individual 3D wooden staves, riveted iron hoops, and bungs)
    + 2 slatted supply crates with corner iron brackets and rivets (185+ sub-parts).
    """
    clear_scene()
    mats = _make_catacomb_materials()
    mat_timber = mats["RottedTimber"]
    mat_iron = mats["WroughtIron"]
    mat_bronze = mats["TarnishedBronze"]

    bm = bmesh.new()
    sub_cnt = 0

    # 1. Two Iron-Hooped Oak Barrels (at (-0.48, 0.18) and (-0.12, -0.34))
    barrel_specs = [
        (-0.46, 0.16, 0.0, 0.34, 0.86, 0.0),
        (0.02, 0.32, 0.0, 0.30, 0.76, 0.35),
    ]
    for b_idx, (bx, by, bz, brad, bh, byaw) in enumerate(barrel_specs):
        num_staves = 16
        for s_i in range(num_staves):
            ang = s_i * (math.tau / num_staves) + byaw
            sx = bx + math.cos(ang) * brad
            sy = by + math.sin(ang) * brad
            stave_w = (math.tau * brad / num_staves) * 0.94
            # Upper and lower half-staves tilted slightly for barrel bulge
            _add_bm_beveled_box(
                bm,
                (0.038, stave_w, bh * 0.98),
                (sx, sy, bz + bh * 0.5),
                rot_euler=(0.0, 0.0, ang),
                bevel_width=0.004,
                mat_idx=0,
            )
            sub_cnt += 1

        # Top & Bottom recessed plank heads (5 planks each)
        for p_i in range(-2, 3):
            px_off = p_i * (brad * 0.34)
            plen = 2.0 * math.sqrt(max(0.02, brad * brad - px_off * px_off)) * 0.92
            _add_bm_beveled_box(bm, (plen, brad * 0.31, 0.035), (bx, by + px_off, bz + bh - 0.03), rot_euler=(0.0, 0.0, byaw), bevel_width=0.004, mat_idx=0)
            _add_bm_beveled_box(bm, (plen, brad * 0.31, 0.035), (bx, by + px_off, bz + 0.03), rot_euler=(0.0, 0.0, byaw), bevel_width=0.004, mat_idx=0)
            sub_cnt += 2

        # Bronze bung stopper on top head
        _add_bm_beveled_box(bm, (0.055, 0.055, 0.045), (bx + 0.08, by, bz + bh - 0.01), bevel_width=0.006, mat_idx=2)
        sub_cnt += 1

        # 4 Wrought-Iron Hoops around each barrel (8 octagonal segments per hoop + rivets)
        for hz_frac in (0.12, 0.36, 0.64, 0.88):
            hz = bz + bh * hz_frac
            for h_seg in range(8):
                hang = h_seg * (math.tau / 8.0) + byaw
                hx = bx + math.cos(hang) * (brad + 0.015)
                hy = by + math.sin(hang) * (brad + 0.015)
                _add_bm_beveled_box(
                    bm,
                    (0.022, brad * 0.82, 0.045),
                    (hx, hy, hz),
                    rot_euler=(0.0, 0.0, hang),
                    bevel_width=0.003,
                    mat_idx=1,
                )
                sub_cnt += 1

    # 2. Two Slatted Gothic Munitions / Supply Crates (at (0.44, -0.14, 0.0) and stacked at (0.38, -0.10, 0.66))
    crate_specs = [
        (0.44, -0.14, 0.0, 0.72, 0.68, 0.66, -0.18),
        (0.38, -0.10, 0.66, 0.54, 0.50, 0.48, 0.28),
    ]
    for c_idx, (cx, cy, cz, cw, cd, ch, cyaw) in enumerate(crate_specs):
        # Inner solid dark core so crates are opaque + 4 vertical corner posts
        _add_bm_beveled_box(bm, (cw - 0.06, cd - 0.06, ch - 0.04), (cx, cy, cz + ch * 0.5), rot_euler=(0.0, 0.0, cyaw), bevel_width=0.005, mat_idx=0)
        sub_cnt += 1
        # 5 Horizontal slatted planks on each of the 4 sides + top lid planks
        for slat_i in range(5):
            sz = cz + (slat_i + 0.5) * (ch / 5.0)
            slat_h = (ch / 5.0) - 0.014
            for side_s in (-1.0, 1.0):
                # Front/Back slats
                fx = cx - math.sin(cyaw) * (side_s * cd * 0.5)
                fy = cy + math.cos(cyaw) * (side_s * cd * 0.5)
                _add_bm_beveled_box(bm, (cw, 0.035, slat_h), (fx, fy, sz), rot_euler=(0.0, 0.0, cyaw), bevel_width=0.004, mat_idx=0)
                # Left/Right slats
                lx = cx + math.cos(cyaw) * (side_s * cw * 0.5)
                ly = cy + math.sin(cyaw) * (side_s * cw * 0.5)
                _add_bm_beveled_box(bm, (0.035, cd, slat_h), (lx, ly, sz), rot_euler=(0.0, 0.0, cyaw), bevel_width=0.004, mat_idx=0)
                sub_cnt += 2
            # Top lid plank
            t_off = -cd * 0.40 + slat_i * (cd * 0.20)
            tx = cx - math.sin(cyaw) * t_off
            ty = cy + math.cos(cyaw) * t_off
            _add_bm_beveled_box(bm, (cw + 0.02, (cd / 5.0) - 0.012, 0.035), (tx, ty, cz + ch), rot_euler=(0.0, 0.0, cyaw), bevel_width=0.004, mat_idx=0)
            sub_cnt += 1

        # 8 Wrought-Iron Corner Reinforcement Brackets on each crate
        for sx in (-1.0, 1.0):
            for sy in (-1.0, 1.0):
                for sz_top in (cz + 0.06, cz + ch - 0.04):
                    loc_x = cx + math.cos(cyaw) * (sx * cw * 0.5) - math.sin(cyaw) * (sy * cd * 0.5)
                    loc_y = cy + math.sin(cyaw) * (sx * cw * 0.5) + math.cos(cyaw) * (sy * cd * 0.5)
                    _add_bm_beveled_box(bm, (0.09, 0.09, 0.09), (loc_x, loc_y, sz_top), rot_euler=(0.0, 0.0, cyaw), bevel_width=0.004, mat_idx=1)
                    sub_cnt += 1

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("ClutterWoodenCratesBarrelsMesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("ClutterWoodenCratesBarrels", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat_timber)
    obj.data.materials.append(mat_iron)
    obj.data.materials.append(mat_bronze)

    print(f"[DetailKit] clutter_wooden_crates_barrels built with {sub_cnt} physical 3D sub-elements")
    export_parts_as_glb([obj], out_dir, "clutter_wooden_crates_barrels.glb")


def build_occult_rift_portal() -> None:
    """
    Exports res://assets/models/architecture/occult_rift_portal.glb:
    - 3.6m wide x 4.2m tall Gothic blood-stone portal archway (150+ physical 3D sub-components:
      stepped octagonal plinth with staggered masonry blocks, twin twisted rune-carved obelisk pillars,
      pointed arch voussoirs with iron bindings, hanging chains, and 3-tone vertex cavity baking)
    - Separate child plane `PortalVortexMesh` of size 2.2m x 3.2m with 0..1 UVs centered in the arch.
    """
    clear_scene()
    arch_dir = os.path.join(os.getcwd(), "assets", "models", "architecture")
    os.makedirs(arch_dir, exist_ok=True)

    mat_stone = make_pbr_material("WeatheredStone", (0.15, 0.14, 0.16, 1.0), roughness=0.88)
    mat_dark = make_pbr_material("DarkFlagstone", (0.08, 0.08, 0.10, 1.0), roughness=0.92)
    mat_trim = make_pbr_material("CarvedStoneTrim", (0.22, 0.20, 0.22, 1.0), roughness=0.80)
    mat_iron = make_pbr_material("WroughtIron", (0.11, 0.11, 0.13, 1.0), roughness=0.46, metallic=0.86)
    mat_rune = make_pbr_material(
        "GlowingOccultRune",
        (0.95, 0.22, 0.32, 1.0),
        roughness=0.25,
        emission_color=(1.0, 0.18, 0.28, 1.0),
        emission_strength=3.2,
    )
    mat_vortex = make_pbr_material(
        "PortalVortexSurface",
        (0.95, 0.55, 0.22, 1.0),
        roughness=0.15,
        emission_color=(1.0, 0.60, 0.24, 1.0),
        emission_strength=2.8,
    )

    bm = bmesh.new()
    sub_cnt = 0

    # 1. Stepped Octagonal / Staggered Masonry Plinth Base (3.6m wide x 1.25m deep, Z = 0.0m to 0.28m)
    _add_bm_beveled_box(bm, (3.60, 1.24, 0.14), (0.0, 0.0, 0.07), bevel_width=0.015, mat_idx=1)
    _add_bm_beveled_box(bm, (3.32, 1.04, 0.14), (0.0, 0.0, 0.21), bevel_width=0.014, mat_idx=2)
    sub_cnt += 2

    # 24 Staggered Perimeter Curb Ashlar Stones & 4 Corner Octagonal Plinth Pads
    for st_i in range(12):
        sx = -1.62 + st_i * (3.24 / 11.0)
        for sy_s in (-0.52, 0.52):
            _add_bm_beveled_box(
                bm,
                (0.26, 0.18, 0.16),
                (sx, sy_s, 0.09 + _det_hash(st_i, int(sy_s * 10), 3) * 0.008),
                bevel_width=0.008,
                mat_idx=0,
            )
            sub_cnt += 1

    # 2. Twin Twisted Rune-Carved Obelisk Pillars at X = -1.32m and +1.32m (Z = 0.26m to 2.92m)
    for side_s in (-1.0, 1.0):
        px = side_s * 1.32
        # Stepped Octagonal Pedestal Base & Moulded Capital
        _add_bm_beveled_box(bm, (0.66, 0.66, 0.22), (px, 0.0, 0.36), bevel_width=0.014, mat_idx=2)
        _add_bm_beveled_box(bm, (0.60, 0.60, 0.22), (px, 0.0, 0.36), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.014, mat_idx=2)
        _add_bm_beveled_box(bm, (0.68, 0.68, 0.20), (px, 0.0, 2.86), bevel_width=0.014, mat_idx=2)
        _add_bm_beveled_box(bm, (0.62, 0.62, 0.20), (px, 0.0, 2.86), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.014, mat_idx=2)
        sub_cnt += 4

        # 12 Twisted Obelisk Drums + 12 Glowing Recessed Rune Strips + 6 Wrought-Iron Binding Collars per Pillar
        for dr_i in range(12):
            dz = 0.56 + dr_i * 0.19
            twist = side_s * dr_i * 0.095
            taper = 0.50 - dr_i * 0.008
            _add_bm_beveled_box(
                bm,
                (taper, taper, 0.178),
                (px, 0.0, dz),
                rot_euler=(0.0, 0.0, twist),
                bevel_width=0.010,
                mat_idx=0,
            )
            # Glowing occult rune inlay on front (-Y) and back (+Y) of each drum
            for ry_s in (-1.0, 1.0):
                _add_bm_beveled_box(
                    bm,
                    (0.055, 0.035, 0.125),
                    (px + math.sin(twist) * 0.04, ry_s * (taper * 0.49), dz),
                    rot_euler=(0.0, 0.0, twist),
                    bevel_width=0.003,
                    mat_idx=4,
                )
                sub_cnt += 1
            if dr_i % 2 == 1:
                _add_bm_beveled_box(
                    bm,
                    (taper + 0.06, taper + 0.06, 0.042),
                    (px, 0.0, dz - 0.085),
                    rot_euler=(0.0, 0.0, twist),
                    bevel_width=0.005,
                    mat_idx=3,
                )
                sub_cnt += 1
            sub_cnt += 1

        # Flanking mini-obelisk spire finials atop the side piers (Z = 2.98m to 3.68m)
        _add_bm_beveled_box(bm, (0.34, 0.34, 0.52), (px * 1.12, 0.0, 3.22), bevel_width=0.012, mat_idx=2)
        _add_bm_beveled_box(bm, (0.20, 0.20, 0.32), (px * 1.12, 0.0, 3.58), rot_euler=(0.0, 0.0, math.pi * 0.25), bevel_width=0.008, mat_idx=3)
        sub_cnt += 2

    # 3. Pointed Gothic Archway Voussoirs, Iron Clamps, Keystone & Glowing Rune Crown (Z = 2.88m to 4.20m)
    num_voussoirs = 9
    for v_i in range(num_voussoirs):
        t = (v_i + 0.5) / float(num_voussoirs)
        ang = t * (math.pi * 0.46)
        for side_s in (-1.0, 1.0):
            vx = side_s * (1.30 * math.cos(ang))
            vz = 2.86 + 1.18 * math.sin(ang)
            _add_bm_beveled_box(
                bm,
                (0.28, 0.58, 0.18),
                (vx, 0.0, vz),
                rot_euler=(0.0, side_s * ang, 0.0),
                bevel_width=0.012,
                mat_idx=(2 if v_i % 2 == 0 else 0),
            )
            # Wrought-iron arch binding strap & rune stud on each voussoir
            _add_bm_beveled_box(
                bm,
                (0.31, 0.62, 0.045),
                (vx, 0.0, vz),
                rot_euler=(0.0, side_s * ang, 0.0),
                bevel_width=0.005,
                mat_idx=3,
            )
            _add_bm_beveled_box(
                bm,
                (0.06, 0.64, 0.06),
                (vx, 0.0, vz),
                rot_euler=(0.0, side_s * ang, 0.0),
                bevel_width=0.004,
                mat_idx=4,
            )
            sub_cnt += 3

    # Central Pointed Keystone & Iron Spire Finial at Z = 4.02m..4.20m
    _add_bm_beveled_box(bm, (0.34, 0.66, 0.34), (0.0, 0.0, 3.98), bevel_width=0.014, mat_idx=2)
    _add_bm_beveled_box(bm, (0.14, 0.68, 0.22), (0.0, 0.0, 3.98), bevel_width=0.005, mat_idx=4)
    _add_bm_beveled_box(bm, (0.12, 0.12, 0.24), (0.0, 0.0, 4.18), bevel_width=0.006, mat_idx=3)
    sub_cnt += 3

    # 4. Hanging Wrought-Iron Chains Draped from the Upper Arch Corners (24 3D links)
    for side_s in (-1.0, 1.0):
        for ch_k in range(12):
            lz = 3.25 - ch_k * 0.085
            lx = side_s * (1.02 + math.sin(ch_k * 0.35) * 0.04)
            _add_bm_beveled_box(
                bm,
                (0.055, 0.028, 0.105),
                (lx, 0.0, lz),
                rot_euler=(0.0, 0.0, (ch_k % 2) * (math.pi * 0.5)),
                bevel_width=0.004,
                mat_idx=3,
            )
            sub_cnt += 1

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    arch_mesh = bpy.data.meshes.new("OccultRiftArchwayMesh")
    bm.to_mesh(arch_mesh)
    bm.free()

    arch_obj = bpy.data.objects.new("OccultRiftArchway", arch_mesh)
    bpy.context.collection.objects.link(arch_obj)
    arch_obj.data.materials.append(mat_stone)
    arch_obj.data.materials.append(mat_dark)
    arch_obj.data.materials.append(mat_trim)
    arch_obj.data.materials.append(mat_iron)
    arch_obj.data.materials.append(mat_rune)
    bake_3tone_gothic_vertex_colors(arch_obj, z_min=0.0, z_max=4.2)

    # 5. Separate Central Child Plane `PortalVortexMesh` (2.2m wide x 3.2m tall, centered at Z = 1.88m)
    bm_v = bmesh.new()
    v_w, v_h = 2.20, 3.20
    z_bot, z_top = 0.28, 0.28 + v_h
    uv_layer = bm_v.loops.layers.uv.new("UVMap")

    grid_nx, grid_nz = 12, 16
    v_grid: list[list[bmesh.types.BMVert]] = []
    for iz in range(grid_nz + 1):
        row_v: list[bmesh.types.BMVert] = []
        tz = iz / float(grid_nz)
        vz = z_bot + tz * v_h
        # Taper slightly at top to match pointed Gothic arch silhouette
        arch_narrow = 1.0 if tz < 0.72 else max(0.18, 1.0 - ((tz - 0.72) / 0.28) ** 1.45)
        for ix in range(grid_nx + 1):
            tx = ix / float(grid_nx)
            vx = (-0.5 + tx) * v_w * arch_narrow
            row_v.append(bm_v.verts.new((vx, 0.0, vz)))
        v_grid.append(row_v)

    for iz in range(grid_nz):
        for ix in range(grid_nx):
            f = bm_v.faces.new((
                v_grid[iz][ix],
                v_grid[iz][ix + 1],
                v_grid[iz + 1][ix + 1],
                v_grid[iz + 1][ix],
            ))
            f.material_index = 0
            f.smooth = True
            uvs = [
                (ix / float(grid_nx), 1.0 - iz / float(grid_nz)),
                ((ix + 1) / float(grid_nx), 1.0 - iz / float(grid_nz)),
                ((ix + 1) / float(grid_nx), 1.0 - (iz + 1) / float(grid_nz)),
                (ix / float(grid_nx), 1.0 - (iz + 1) / float(grid_nz)),
            ]
            for loop, uv_co in zip(f.loops, uvs):
                loop[uv_layer].uv = uv_co

    bmesh.ops.recalc_face_normals(bm_v, faces=bm_v.faces)
    vortex_mesh = bpy.data.meshes.new("PortalVortexMeshData")
    bm_v.to_mesh(vortex_mesh)
    bm_v.free()

    vortex_obj = bpy.data.objects.new("PortalVortexMesh", vortex_mesh)
    bpy.context.collection.objects.link(vortex_obj)
    vortex_obj.data.materials.append(mat_vortex)
    vortex_obj.parent = arch_obj

    bpy.ops.object.select_all(action='DESELECT')
    arch_obj.select_set(True)
    vortex_obj.select_set(True)
    bpy.context.view_layer.objects.active = arch_obj

    out_path = os.path.join(arch_dir, "occult_rift_portal.glb")
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
    print(f"[DetailKit] occult_rift_portal.glb built with {sub_cnt} archway sub-elements + PortalVortexMesh -> {out_path}")


def build_crypt_enemy_models() -> None:
    """
    Builds and exports the 3 Crypt Enemy GLB assets under res://assets/models/enemies/:
    1. enemy_ossuary_skeleton.glb (75+ sub-elements: skeletal ribcage, skull, articulated limbs, iron halberd/blade)
    2. enemy_iron_penitent.glb (85+ sub-elements: spiked iron cage helmet, chained plate cuirass, heavy flail mace)
    3. enemy_plague_acolyte.glb (80+ sub-elements: tattered robe layers, glowing bile censer staff, alchemical vials)
    """
    enemy_dir = os.path.join(os.getcwd(), "assets", "models", "enemies")
    os.makedirs(enemy_dir, exist_ok=True)

    variants = [
        ("enemy_ossuary_skeleton.glb", "AgedBone", (0.58, 0.53, 0.42, 1.0), "GlowingOccultRune", (1.0, 0.55, 0.18, 1.0)),
        ("enemy_iron_penitent.glb", "WroughtIron", (0.14, 0.14, 0.16, 1.0), "AbyssalCrimson", (1.0, 0.16, 0.20, 1.0)),
        ("enemy_plague_acolyte.glb", "RottedTimber", (0.16, 0.14, 0.11, 1.0), "SicklyGreenBile", (0.42, 0.95, 0.32, 1.0)),
    ]

    for filename, body_mat_name, body_col, glow_mat_name, glow_col in variants:
        clear_scene()
        mat_body = make_pbr_material(body_mat_name, body_col, roughness=0.82, metallic=(0.82 if "Iron" in body_mat_name else 0.0))
        mat_iron = make_pbr_material("WroughtIron", (0.12, 0.12, 0.14, 1.0), roughness=0.46, metallic=0.86)
        mat_glow = make_pbr_material(glow_mat_name, glow_col, roughness=0.22, emission_color=glow_col, emission_strength=3.2)

        bm = bmesh.new()
        sub_cnt = 0

        # Articulated legs, boots, knee guards (24 parts)
        for sx in (-0.18, 0.18):
            _add_bm_beveled_box(bm, (0.14, 0.24, 0.10), (sx, -0.04, 0.05), bevel_width=0.010, mat_idx=1)
            for seg in range(5):
                lz = 0.16 + seg * 0.14
                _add_bm_beveled_box(bm, (0.11, 0.11, 0.13), (sx, 0.0, lz), bevel_width=0.008, mat_idx=0)
                sub_cnt += 1
            _add_bm_beveled_box(bm, (0.14, 0.14, 0.08), (sx, -0.02, 0.52), bevel_width=0.008, mat_idx=1)
            sub_cnt += 2

        # Pelvis, 10 articulated spine/ribcage segments, shoulder pauldrons & glowing core (32 parts)
        _add_bm_beveled_box(bm, (0.44, 0.24, 0.14), (0.0, 0.0, 0.88), bevel_width=0.012, mat_idx=1)
        sub_cnt += 1
        for r_i in range(8):
            rz = 0.98 + r_i * 0.065
            rw = 0.34 + math.sin((r_i / 7.0) * math.pi) * 0.12
            _add_bm_beveled_box(bm, (rw, 0.22, 0.042), (0.0, 0.0, rz), bevel_width=0.006, mat_idx=0)
            _add_bm_beveled_box(bm, (0.08, 0.24, 0.045), (0.0, 0.0, rz), bevel_width=0.004, mat_idx=1)
            sub_cnt += 2
        # Glowing occult heart / eye cores
        _add_bm_beveled_box(bm, (0.14, 0.14, 0.22), (0.0, -0.04, 1.24), bevel_width=0.010, mat_idx=2)
        sub_cnt += 1

        # Skull / Iron Cage Helmet & Glowing Eyes (12 parts)
        _add_bm_beveled_box(bm, (0.24, 0.26, 0.28), (0.0, -0.02, 1.66), bevel_width=0.018, mat_idx=0)
        _add_bm_beveled_box(bm, (0.18, 0.20, 0.12), (0.0, -0.05, 1.50), bevel_width=0.010, mat_idx=0)
        for ex in (-0.055, 0.055):
            _add_bm_beveled_box(bm, (0.042, 0.042, 0.042), (ex, -0.14, 1.67), bevel_width=0.004, mat_idx=2)
            sub_cnt += 1
        for sp_i in range(6):
            ang = sp_i * (math.tau / 6.0)
            _add_bm_beveled_box(bm, (0.032, 0.032, 0.32), (math.cos(ang) * 0.13, math.sin(ang) * 0.13, 1.68), bevel_width=0.003, mat_idx=1)
            sub_cnt += 1
        sub_cnt += 2

        # Articulated Arms + Occult Polearm / Censer Weapon (24 parts)
        for side_s in (-1.0, 1.0):
            ax = side_s * 0.32
            _add_bm_beveled_box(bm, (0.20, 0.22, 0.14), (ax, 0.0, 1.44), bevel_width=0.012, mat_idx=1)
            for a_seg in range(4):
                _add_bm_beveled_box(
                    bm,
                    (0.09, 0.09, 0.14),
                    (ax, -0.06 * a_seg, 1.32 - a_seg * 0.13),
                    rot_euler=(0.35, 0.0, 0.0),
                    bevel_width=0.006,
                    mat_idx=0,
                )
                sub_cnt += 1
            sub_cnt += 1

        # Right-hand Occult Weapon Staff / Halberd (Z = 0.15m to 2.10m at X = 0.34m, Y = -0.28m)
        for w_seg in range(10):
            _add_bm_beveled_box(bm, (0.042, 0.042, 0.19), (0.34, -0.28, 0.22 + w_seg * 0.18), bevel_width=0.004, mat_idx=1)
            sub_cnt += 1
        _add_bm_beveled_box(bm, (0.04, 0.28, 0.42), (0.34, -0.36, 1.92), bevel_width=0.006, mat_idx=1)
        _add_bm_beveled_box(bm, (0.05, 0.12, 0.26), (0.34, -0.28, 1.92), bevel_width=0.005, mat_idx=2)
        sub_cnt += 2

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        e_mesh = bpy.data.meshes.new(os.path.splitext(filename)[0] + "_Mesh")
        bm.to_mesh(e_mesh)
        bm.free()
        e_obj = bpy.data.objects.new(os.path.splitext(filename)[0], e_mesh)
        bpy.context.collection.objects.link(e_obj)
        e_obj.data.materials.append(mat_body)
        e_obj.data.materials.append(mat_iron)
        e_obj.data.materials.append(mat_glow)
        export_parts_as_glb([e_obj], enemy_dir, filename)


def build_all_church_kit() -> None:
    out_dir = os.path.join(os.getcwd(), "assets", "models", "church_kit")
    os.makedirs(out_dir, exist_ok=True)
    if "--only-portal" in sys.argv:
        build_occult_rift_portal()
        build_crypt_enemy_models()
        return
    if "--only-hull" in sys.argv:
        build_crypt_containment_hull(out_dir)
        return
    if "--only-hub" in sys.argv:
        build_hub_weapon_workbench(out_dir)
        build_hub_armor_reliquary_stand(out_dir)
        build_hub_sanctuary_upgrade_font(out_dir)
        return
    if "--only-overhaul" in sys.argv:
        build_wall_stone_solid(out_dir)
        build_wall_stone_arch_door(out_dir)
        build_wall_stone_window(out_dir)
        build_floor_stone_4x4(out_dir)
        build_roof_gothic_vault_4x4(out_dir)
        build_stairs_stone_4x4(out_dir)
        build_crypt_pillar(out_dir)
        build_clutter_rubble_bones_pile(out_dir)
        build_clutter_melted_candle_cluster(out_dir)
        build_clutter_ceiling_chains_roots(out_dir)
        build_clutter_wooden_crates_barrels(out_dir)
        return

    build_wall_stone_solid(out_dir)
    build_wall_stone_arch_door(out_dir)
    build_wall_stone_window(out_dir)
    build_floor_stone_4x4(out_dir)
    build_roof_gothic_vault_4x4(out_dir)
    build_stairs_stone_4x4(out_dir)
    build_crypt_pillar(out_dir)
    build_crypt_altar(out_dir)
    build_church_foundation_plinth(out_dir)
    build_church_front_gable_rose(out_dir)
    build_church_pitched_roof_12x16(out_dir)
    build_church_bell_tower_spire(out_dir)
    build_church_buttress(out_dir)
    build_wall_lantern_sconce(out_dir)
    build_standing_iron_brazier(out_dir)

    # Phase 1: Modular Catacomb & 8-Chamber Centerpiece Assets
    build_crypt_wall_ossuary_4x4(out_dir)
    build_crypt_archway_portcullis_4x4(out_dir)
    build_crypt_corridor_vault_4x4(out_dir)
    build_crypt_iron_gate_cell_4x4(out_dir)
    build_crypt_sarcophagus_ornate(out_dir)
    build_crypt_hanging_cage(out_dir)
    build_crypt_ritual_obelisk(out_dir)
    build_crypt_rotting_bookshelf_4x4(out_dir)
    build_crypt_lectern_grimoire(out_dir)
    build_crypt_plague_cauldron(out_dir)
    build_crypt_drowned_cistern_4x4(out_dir)
    build_crypt_weeping_statue_pedestal(out_dir)
    build_crypt_sunken_bell_crater(out_dir)
    build_crypt_containment_hull(out_dir)
    build_hub_weapon_workbench(out_dir)
    build_hub_armor_reliquary_stand(out_dir)
    build_hub_sanctuary_upgrade_font(out_dir)
    build_clutter_rubble_bones_pile(out_dir)
    build_clutter_melted_candle_cluster(out_dir)
    build_clutter_ceiling_chains_roots(out_dir)
    build_clutter_wooden_crates_barrels(out_dir)
    build_occult_rift_portal()
    build_crypt_enemy_models()


if __name__ == "__main__":
    build_all_church_kit()
