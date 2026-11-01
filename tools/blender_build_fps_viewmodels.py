import bpy
import bmesh
import math
import os
import sys
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blender_detail_kit import bake_3tone_gothic_vertex_colors


def clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_pbr_material(
    name: str,
    base_color: tuple[float, float, float, float],
    roughness: float,
    metallic: float = 0.0,
    emission_color: tuple[float, float, float, float] | None = None,
    emission_strength: float = 0.0,
    alpha: float = 1.0,
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
        if "Alpha" in bsdf.inputs and alpha < 1.0:
            bsdf.inputs["Alpha"].default_value = alpha
            if hasattr(mat, "blend_method"):
                mat.blend_method = 'BLEND'
        if emission_color is not None and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = emission_color
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def finalize_part(
    obj: bpy.types.Object,
    mat: bpy.types.Material,
    bevel_width: float = 0.002,
    bevel_segments: int = 2,
    smooth_shade: bool = True,
) -> bpy.types.Object:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    if len(obj.data.materials) == 0:
        obj.data.materials.append(mat)
    if bevel_width > 0.0:
        bev = obj.modifiers.new(name="Bevel", type='BEVEL')
        bev.width = bevel_width
        bev.segments = bevel_segments
        bev.limit_method = 'ANGLE'
        bev.angle_limit = math.radians(32.0)
        bpy.ops.object.modifier_apply(modifier=bev.name)
    if smooth_shade and isinstance(obj.data, bpy.types.Mesh):
        for poly in obj.data.polygons:
            poly.use_smooth = True
    return obj


def apply_gothic_vertex_cavity(obj: bpy.types.Object, base_z_min: float = -0.3) -> None:
    """Bakes deterministic 3-tone gothic vertex colors ('Col') with crevice grime and convex edge highlights."""
    bake_3tone_gothic_vertex_colors(obj, z_min=base_z_min, z_max=base_z_min + 0.45)


def join_into_hierarchy_node(
    node_name: str,
    parts: list[bpy.types.Object],
    pivot_loc: tuple[float, float, float] = (0.0, 0.0, 0.0),
    parent_obj: bpy.types.Object | None = None,
) -> bpy.types.Object:
    """
    Joins all mesh sub-parts in `parts` into a single Mesh object named `node_name`
    whose origin is placed strictly at `pivot_loc` (Rule 7.2 Mandatory Pre-Export Hierarchy Joining).
    """
    print(f"[Join] Joining {len(parts)} sub-components into '{node_name}' at pivot {pivot_loc}")
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

    # Shift vertex geometry by -pivot_loc and set object location to pivot_loc
    px, py, pz = pivot_loc
    if abs(px) > 1e-6 or abs(py) > 1e-6 or abs(pz) > 1e-6:
        bm = bmesh.new()
        bm.from_mesh(joined.data)
        bmesh.ops.translate(bm, verts=bm.verts, vec=(-px, -py, -pz))
        bm.to_mesh(joined.data)
        bm.free()
        joined.data.update()
    joined.location = pivot_loc
    joined.rotation_euler = (0.0, 0.0, 0.0)
    joined.scale = (1.0, 1.0, 1.0)

    apply_gothic_vertex_cavity(joined)

    if parent_obj is not None:
        joined.parent = parent_obj

    return joined


# ==============================================================================
# PARAMETRIC DETAIL GENERATORS (AGENTS.md Section 7.2)
# ==============================================================================

def spawn_rivet_line(
    prefix: str,
    points: list[tuple[float, float, float]],
    radius: float,
    mat: bpy.types.Material,
) -> list[bpy.types.Object]:
    """Spawns dome-headed rivets at the given 3D coordinates."""
    rivets: list[bpy.types.Object] = []
    for idx, pt in enumerate(points):
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=10,
            ring_count=6,
            radius=radius,
            location=pt,
        )
        rv = bpy.context.active_object
        rv.name = f"{prefix}_Rivet_{idx}"
        finalize_part(rv, mat, bevel_width=0.0, smooth_shade=True)
        rivets.append(rv)
    return rivets


def spawn_chain_links(
    prefix: str,
    top_z: float,
    count: int,
    step_z: float,
    major_r: float,
    minor_r: float,
    mat: bpy.types.Material,
) -> list[bpy.types.Object]:
    """Spawns interlocking 90-degree alternating 3D chain links along the Z axis."""
    links: list[bpy.types.Object] = []
    for i in range(count):
        lz = top_z - i * step_z
        rot_z = math.radians(90.0) if (i % 2 == 1) else 0.0
        bpy.ops.mesh.primitive_torus_add(
            major_radius=major_r,
            minor_radius=minor_r,
            major_segments=16,
            minor_segments=8,
            location=(0.0, 0.0, lz),
            rotation=(math.radians(90.0), 0.0, rot_z),
        )
        lk = bpy.context.active_object
        lk.name = f"{prefix}_ChainLink_{i}"
        lk.scale = (0.78, 1.0, 1.25)
        finalize_part(lk, mat, bevel_width=0.0, smooth_shade=True)
        links.append(lk)
    return links


def spawn_articulated_finger(
    prefix: str,
    base_loc: tuple[float, float, float],
    base_rot: tuple[float, float, float],
    length_scale: float,
    mat_steel: bpy.types.Material,
    mat_brass: bpy.types.Material,
) -> list[bpy.types.Object]:
    """
    Spawns a 4-part articulated gothic finger (3 overlapping scalloped armor lames + 1 knuckle gadling spike).
    """
    f_parts: list[bpy.types.Object] = []
    bx, by, bz = base_loc
    rx, ry, rz = base_rot

    # Knuckle gadling pyramid stud
    bpy.ops.mesh.primitive_cone_add(
        vertices=4,
        radius1=0.0045,
        radius2=0.001,
        depth=0.005,
        location=(bx, by - 0.004, bz + 0.005),
        rotation=(rx, ry, rz + math.radians(45.0)),
    )
    gad = bpy.context.active_object
    gad.name = f"{prefix}_Gadling"
    finalize_part(gad, mat_brass, bevel_width=0.0005, smooth_shade=False)
    f_parts.append(gad)

    # 3 Overlapping Phalanx Lames (Proximal, Middle, Distal)
    for p_idx in range(3):
        t = p_idx / 2.0
        seg_len = 0.011 * length_scale * (1.0 - 0.15 * t)
        seg_w = 0.0085 * (1.0 - 0.12 * t)
        # Step forward/down along finger curl
        off_y = 0.007 * p_idx * math.cos(rx)
        off_z = -0.007 * p_idx * math.sin(rx)
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(bx, by + off_y, bz + off_z),
            rotation=(rx + math.radians(p_idx * 18.0), ry, rz),
        )
        lame = bpy.context.active_object
        lame.name = f"{prefix}_Lame_{p_idx}"
        lame.scale = (seg_w, seg_len, 0.0075)
        finalize_part(lame, mat_steel, bevel_width=0.0012, smooth_shade=True)
        f_parts.append(lame)

    return f_parts


def spawn_gothic_filigree(
    prefix: str,
    side_x: float,
    y_center: float,
    z_center: float,
    mat_brass: bpy.types.Material,
    mat_rune: bpy.types.Material,
) -> list[bpy.types.Object]:
    """Spawns ornate gothic sideplate filigree ribs, rosette bosses, and glowing rune inlays."""
    fil_parts: list[bpy.types.Object] = []

    # Main bevel-edged brass filigree plate
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(side_x, y_center, z_center))
    plate = bpy.context.active_object
    plate.name = f"{prefix}_FiligreePlate"
    plate.scale = (0.0022, 0.042, 0.034)
    finalize_part(plate, mat_brass, bevel_width=0.0008, smooth_shade=True)
    fil_parts.append(plate)

    # 2 Raised Scroll Ribs
    for r_idx, z_off in enumerate([-0.010, 0.010]):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(side_x * 1.06, y_center + 0.004, z_center + z_off))
        rib = bpy.context.active_object
        rib.name = f"{prefix}_ScrollRib_{r_idx}"
        rib.scale = (0.0015, 0.032, 0.003)
        finalize_part(rib, mat_brass, bevel_width=0.0005, smooth_shade=True)
        fil_parts.append(rib)

    # Glowing Occult Cross Inlay
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(side_x * 1.08, y_center, z_center))
    rune_v = bpy.context.active_object
    rune_v.name = f"{prefix}_RuneCrossV"
    rune_v.scale = (0.0012, 0.018, 0.0025)
    finalize_part(rune_v, mat_rune, bevel_width=0.0003, smooth_shade=False)
    fil_parts.append(rune_v)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(side_x * 1.08, y_center + 0.003, z_center))
    rune_h = bpy.context.active_object
    rune_h.name = f"{prefix}_RuneCrossH"
    rune_h.scale = (0.0012, 0.0025, 0.012)
    finalize_part(rune_h, mat_rune, bevel_width=0.0003, smooth_shade=False)
    fil_parts.append(rune_h)

    return fil_parts


def spawn_cartridge_assembly(
    ch_idx: int,
    ch_x: float,
    ch_z: float,
    cyl_len: float,
    mat_brass: bpy.types.Material,
    mat_silver: bpy.types.Material,
    mat_rune: bpy.types.Material,
) -> list[bpy.types.Object]:
    """
    Spawns a 4-part loaded occult cartridge inside cylinder chamber `ch_idx`:
    1. Rim + Casing body (Brass)
    2. Silver Primer cap at rear (-Y)
    3. Glowing Crimson Rune Ring around primer
    4. Pointed Silver Bullet tip protruding at front (+Y)
    """
    c_parts: list[bpy.types.Object] = []

    # 1. Brass Casing Rim & Body at rear of chamber
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=14,
        radius=0.0068,
        depth=0.003,
        location=(ch_x, -cyl_len * 0.49, ch_z),
        rotation=(math.radians(90.0), 0.0, 0.0),
    )
    casing = bpy.context.active_object
    casing.name = f"CartridgeCasing_{ch_idx}"
    finalize_part(casing, mat_brass, bevel_width=0.0005, smooth_shade=True)
    c_parts.append(casing)

    # 2. Silver Primer Cap
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=12,
        radius=0.0032,
        depth=0.0035,
        location=(ch_x, -cyl_len * 0.495, ch_z),
        rotation=(math.radians(90.0), 0.0, 0.0),
    )
    primer = bpy.context.active_object
    primer.name = f"CartridgePrimer_{ch_idx}"
    finalize_part(primer, mat_silver, bevel_width=0.0004, smooth_shade=True)
    c_parts.append(primer)

    # 3. Glowing Rune Ring around primer
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.0050,
        minor_radius=0.0009,
        major_segments=14,
        minor_segments=6,
        location=(ch_x, -cyl_len * 0.50, ch_z),
        rotation=(math.radians(90.0), 0.0, 0.0),
    )
    rune = bpy.context.active_object
    rune.name = f"CartridgeRune_{ch_idx}"
    finalize_part(rune, mat_rune, bevel_width=0.0, smooth_shade=True)
    c_parts.append(rune)

    # 4. Pointed Silver Bullet Ogive inside front of chamber (+Y)
    bpy.ops.mesh.primitive_cone_add(
        vertices=14,
        radius1=0.0058,
        radius2=0.0008,
        depth=0.014,
        location=(ch_x, cyl_len * 0.42, ch_z),
        rotation=(math.radians(-90.0), 0.0, 0.0),
    )
    bullet = bpy.context.active_object
    bullet.name = f"CartridgeBullet_{ch_idx}"
    finalize_part(bullet, mat_silver, bevel_width=0.0005, smooth_shade=True)
    c_parts.append(bullet)

    return c_parts


def build_detailed_arm_gauntlet(
    prefix: str,
    is_left: bool,
    z_offset: float,
    mat_leather: bpy.types.Material,
    mat_steel: bpy.types.Material,
    mat_brass: bpy.types.Material,
) -> list[bpy.types.Object]:
    """
    Constructs a 56-sub-component Gothic Hunter Gauntlet along a strict coaxial forearm vector:
    - Tapered leather sleeve + 2 raised stitched piping seams
    - Tapered Gothic steel vambrace (`radius_wrist = 0.042m`, `radius_elbow = 0.058m` on left arm)
      with flanged wrist and elbow cuffs
    - 4 coaxial buckled leather straps wrapping cleanly OVER the steel plate (`+0.0042m` proud, zero clipping)
    - 16 dome-headed brass rivets seated along the vambrace edges
    - Embossed dorsal metacarpal plate with 3 Gothic ridges
    - 5 fully articulated fingers (4 fingers x 4 parts + 4-part thumb = 20 parts)
    """
    parts: list[bpy.types.Object] = []
    sign: float = -1.0 if is_left else 1.0

    if is_left:
        # Angles cleanly from the lower-left corner into the bail handle without crowding the near plane
        elbow_pt = Vector((-0.068, -0.115, -0.155 + z_offset))
        wrist_pt = Vector((-0.010, -0.028, -0.012 + z_offset))
        radius_wrist: float = 0.034
        radius_elbow: float = 0.046
    else:
        # Right forearm angles cleanly into the revolver birdshead grip
        elbow_pt = Vector((0.032, -0.205, -0.072 + z_offset))
        wrist_pt = Vector((0.012, -0.052, -0.016 + z_offset))
        radius_wrist = 0.036
        radius_elbow = 0.048

    axis_vec: Vector = wrist_pt - elbow_pt
    arm_len: float = axis_vec.length
    arm_dir: Vector = axis_vec.normalized()
    arm_quat = Vector((0.0, 0.0, 1.0)).rotation_difference(arm_dir)
    arm_rot = arm_quat.to_euler('XYZ')
    perp_x: Vector = arm_quat @ Vector((1.0, 0.0, 0.0))
    perp_y: Vector = arm_quat @ Vector((0.0, 1.0, 0.0))

    # 1. Tapered Pleated Leather Forearm Sleeve (spans full elbow_pt -> wrist_pt)
    sleeve_center: Vector = elbow_pt.lerp(wrist_pt, 0.50)
    bpy.ops.mesh.primitive_cone_add(
        vertices=18,
        radius1=radius_elbow * 0.94,
        radius2=radius_wrist * 0.92,
        depth=arm_len,
        location=tuple(sleeve_center),
        rotation=tuple(arm_rot),
    )
    sleeve = bpy.context.active_object
    sleeve.name = f"{prefix}_LeatherSleeve"
    finalize_part(sleeve, mat_leather, bevel_width=0.002, smooth_shade=True)
    parts.append(sleeve)

    # 2. Raised Leather Piping Ribs (2 longitudinal seams inset along the sleeve)
    for s_idx, side_s in enumerate([-1.0, 1.0]):
        seam_pos: Vector = sleeve_center + perp_x * (side_s * radius_wrist * 0.85)
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=8,
            radius=0.0025,
            depth=arm_len * 0.92,
            location=tuple(seam_pos),
            rotation=tuple(arm_rot),
        )
        pipe = bpy.context.active_object
        pipe.name = f"{prefix}_SleevePiping_{s_idx}"
        finalize_part(pipe, mat_leather, bevel_width=0.0005, smooth_shade=True)
        parts.append(pipe)

    # 3. Tapered Gothic Steel Vambrace + Flanged Wrist & Elbow Cuffs (100% coaxial with sleeve)
    vamb_t0: float = 0.10
    vamb_t1: float = 0.90
    vamb_center: Vector = elbow_pt.lerp(wrist_pt, (vamb_t0 + vamb_t1) * 0.5)
    vamb_len: float = arm_len * (vamb_t1 - vamb_t0)

    bpy.ops.mesh.primitive_cone_add(
        vertices=18,
        radius1=radius_elbow,
        radius2=radius_wrist,
        depth=vamb_len,
        location=tuple(vamb_center),
        rotation=tuple(arm_rot),
    )
    dorsal_vp = bpy.context.active_object
    dorsal_vp.name = f"{prefix}_DorsalPlate"
    finalize_part(dorsal_vp, mat_steel, bevel_width=0.002, smooth_shade=True)
    parts.append(dorsal_vp)

    # Flanged Wrist Cuff at t = 0.88
    wrist_cuff_pos: Vector = elbow_pt.lerp(wrist_pt, 0.88)
    bpy.ops.mesh.primitive_cone_add(
        vertices=18,
        radius1=radius_wrist + 0.0025,
        radius2=radius_wrist + 0.0010,
        depth=0.028,
        location=tuple(wrist_cuff_pos),
        rotation=tuple(arm_rot),
    )
    wrist_cuff = bpy.context.active_object
    wrist_cuff.name = f"{prefix}_WristCuff"
    finalize_part(wrist_cuff, mat_steel, bevel_width=0.0018, smooth_shade=True)
    parts.append(wrist_cuff)

    # Flanged Elbow Guard Cuff at t = 0.12
    elbow_cuff_pos: Vector = elbow_pt.lerp(wrist_pt, 0.12)
    bpy.ops.mesh.primitive_cone_add(
        vertices=18,
        radius1=radius_elbow + 0.0025,
        radius2=radius_elbow + 0.0010,
        depth=0.032,
        location=tuple(elbow_cuff_pos),
        rotation=tuple(arm_rot),
    )
    elbow_cuff = bpy.context.active_object
    elbow_cuff.name = f"{prefix}_ElbowGuardFlange"
    finalize_part(elbow_cuff, mat_steel, bevel_width=0.0018, smooth_shade=True)
    parts.append(elbow_cuff)

    # 4. 4 Coaxial Buckled Leather Straps (major_radius = r_steel + 0.0042m so straps wrap cleanly OVER armor)
    strap_t_stations: list[float] = [0.24, 0.42, 0.60, 0.78]
    for st_idx, t_s in enumerate(strap_t_stations):
        u_vamb: float = (t_s - vamb_t0) / (vamb_t1 - vamb_t0)
        r_steel_at_t: float = radius_elbow + (radius_wrist - radius_elbow) * u_vamb
        strap_major_r: float = r_steel_at_t + 0.0042
        strap_pos: Vector = elbow_pt.lerp(wrist_pt, t_s)

        bpy.ops.mesh.primitive_torus_add(
            major_radius=strap_major_r,
            minor_radius=0.0034,
            major_segments=24,
            minor_segments=10,
            location=tuple(strap_pos),
            rotation=tuple(arm_rot),
        )
        st = bpy.context.active_object
        st.name = f"{prefix}_Strap_{st_idx}"
        finalize_part(st, mat_leather, bevel_width=0.0, smooth_shade=True)
        parts.append(st)

        # Curved Brass Buckle Frame on outer/dorsal side of strap
        buckle_pos: Vector = strap_pos + perp_x * (sign * (strap_major_r + 0.0015)) + perp_y * 0.004
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=tuple(buckle_pos),
            rotation=tuple(arm_rot),
        )
        bk = bpy.context.active_object
        bk.name = f"{prefix}_BuckleFrame_{st_idx}"
        bk.scale = (0.0045, 0.011, 0.011)
        finalize_part(bk, mat_brass, bevel_width=0.001, smooth_shade=True)
        parts.append(bk)

        # Brass Buckle Tongue Pin
        tongue_pos: Vector = buckle_pos + perp_x * (sign * 0.002)
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=8,
            radius=0.0012,
            depth=0.009,
            location=tuple(tongue_pos),
            rotation=tuple(arm_rot),
        )
        tg = bpy.context.active_object
        tg.name = f"{prefix}_BuckleTongue_{st_idx}"
        finalize_part(tg, mat_brass, bevel_width=0.0003, smooth_shade=True)
        parts.append(tg)

    # 5. 16 Dome-Headed Brass Rivets seated cleanly on the tapered vambrace surface
    rivet_pts: list[tuple[float, float, float]] = []
    for r_i in range(8):
        t_r: float = 0.18 + (r_i / 7.0) * 0.64
        u_r: float = (t_r - vamb_t0) / (vamb_t1 - vamb_t0)
        r_surf: float = radius_elbow + (radius_wrist - radius_elbow) * u_r + 0.0008
        center_r: Vector = elbow_pt.lerp(wrist_pt, t_r)
        for side_r in [-1.0, 1.0]:
            rv_vec: Vector = (perp_x * (side_r * 0.78) + perp_y * 0.62).normalized() * r_surf
            pt_r: Vector = center_r + rv_vec
            rivet_pts.append((pt_r.x, pt_r.y, pt_r.z))
    parts.extend(spawn_rivet_line(f"{prefix}_Vambrace", rivet_pts, 0.0022, mat_brass))

    # 5B. 6 Embossed Gothic Fluted Armor Ribs along the dorsal steel vambrace
    for fl_i in range(6):
        fl_ang: float = (-0.55 + (fl_i / 5.0) * 1.10)
        fl_dir: Vector = (perp_x * math.sin(fl_ang) + perp_y * math.cos(fl_ang)).normalized()
        r_mid: float = (radius_elbow + radius_wrist) * 0.5 + 0.0012
        fl_pos: Vector = vamb_center + fl_dir * r_mid
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=6,
            radius=0.0016,
            depth=vamb_len * 0.86,
            location=tuple(fl_pos),
            rotation=tuple(arm_rot),
        )
        fl_rib = bpy.context.active_object
        fl_rib.name = f"{prefix}_VambraceFlute_{fl_i}"
        finalize_part(fl_rib, mat_steel, bevel_width=0.0004, smooth_shade=True)
        parts.append(fl_rib)

    # 5C. 24 Raised Leather Cross-Stitching Segments along both sleeve piping seams (12 per side)
    for s_idx, side_s in enumerate([-1.0, 1.0]):
        for st_k in range(12):
            t_st: float = 0.08 + (st_k / 11.0) * 0.82
            r_sl: float = (radius_elbow + (radius_wrist - radius_elbow) * t_st) * 0.90
            st_pt: Vector = elbow_pt.lerp(wrist_pt, t_st) + (perp_x * (side_s * 0.92) - perp_y * 0.35).normalized() * r_sl
            bpy.ops.mesh.primitive_cube_add(
                size=1.0,
                location=tuple(st_pt),
                rotation=tuple(arm_rot),
            )
            stitch = bpy.context.active_object
            stitch.name = f"{prefix}_SleeveStitch_{s_idx}_{st_k}"
            stitch.scale = (0.0032, 0.0016, 0.0024)
            finalize_part(stitch, mat_brass, bevel_width=0.0003, smooth_shade=True)
            parts.append(stitch)

    # 5D. 8 Scalloped Cuff Boss Rivets (4 on wrist cuff, 4 on elbow cuff)
    cuff_rivet_pts: list[tuple[float, float, float]] = []
    for cf_t, cf_r in [(0.88, radius_wrist + 0.0022), (0.12, radius_elbow + 0.0022)]:
        cf_c: Vector = elbow_pt.lerp(wrist_pt, cf_t)
        for c_i in range(4):
            c_ang = -0.75 + (c_i / 3.0) * 1.50
            c_vec = (perp_x * math.sin(c_ang) + perp_y * math.cos(c_ang)).normalized() * cf_r
            cp: Vector = cf_c + c_vec
            cuff_rivet_pts.append((cp.x, cp.y, cp.z))
    parts.extend(spawn_rivet_line(f"{prefix}_CuffBoss", cuff_rivet_pts, 0.0020, mat_brass))

    # 6. Embossed Dorsal Metacarpal Plate + 3 Gothic Fluted Ridges
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(sign * 0.008, -0.026, -0.004 + z_offset),
        rotation=(math.radians(-10.0), sign * math.radians(12.0), 0.0),
    )
    hand_plate = bpy.context.active_object
    hand_plate.name = f"{prefix}_MetacarpalPlate"
    hand_plate.scale = (0.036, 0.046, 0.012)
    finalize_part(hand_plate, mat_steel, bevel_width=0.002, smooth_shade=True)
    parts.append(hand_plate)

    for ridge_i, rx_off in enumerate([-0.010, 0.0, 0.010]):
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(sign * 0.008 + rx_off, -0.025, 0.003 + z_offset),
            rotation=(math.radians(-10.0), sign * math.radians(12.0), 0.0),
        )
        ridge = bpy.context.active_object
        ridge.name = f"{prefix}_DorsalRidge_{ridge_i}"
        ridge.scale = (0.0032, 0.040, 0.0038)
        finalize_part(ridge, mat_brass, bevel_width=0.0008, smooth_shade=True)
        parts.append(ridge)

    # 7. 5 Articulated Fingers (4 main fingers + 1 articulated thumb = 20 sub-parts)
    for f_idx in range(4):
        if is_left:
            # Wrapped over horizontal lantern bail handle
            fx = -0.018 + f_idx * 0.012
            floc = (fx, 0.004, -0.005 + z_offset)
            frot = (math.radians(42.0), 0.0, 0.0)
        else:
            # Right hand: index finger (f_idx=0) reaches toward trigger; others wrap grip
            fz = (-0.018 - f_idx * 0.013) + z_offset
            fy = 0.002 if f_idx == 0 else -0.012
            floc = (0.014, fy, fz)
            frot = (math.radians(15.0 if f_idx == 0 else 55.0), math.radians(20.0), math.radians(30.0))

        parts.extend(
            spawn_articulated_finger(
                f"{prefix}_Finger_{f_idx}",
                floc,
                frot,
                1.0 if f_idx in (1, 2) else 0.88,
                mat_steel,
                mat_brass,
            )
        )

    # Articulated Thumb (4 sub-parts)
    thumb_loc = (sign * (-0.016), -0.010, -0.004 + z_offset)
    thumb_rot = (math.radians(25.0), sign * math.radians(-25.0), sign * math.radians(-30.0))
    parts.extend(
        spawn_articulated_finger(
            f"{prefix}_Thumb",
            thumb_loc,
            thumb_rot,
            0.82,
            mat_steel,
            mat_brass,
        )
    )

    return parts


# ==============================================================================
# 1. LEFT VIEWMODEL: OCCULT SWINGING LANTERN (115+ SUB-COMPONENTS)
# ==============================================================================

def build_viewmodel_left_lantern() -> None:
    clear_scene()

    # Satin/Matte PBR Materials (Zero harsh mirror glare)
    mat_leather = make_pbr_material("WeatheredLeather", (0.12, 0.085, 0.065, 1.0), roughness=0.86)
    mat_steel = make_pbr_material("GothicPlateSteel", (0.18, 0.19, 0.21, 1.0), roughness=0.42, metallic=0.88)
    mat_brass = make_pbr_material("TarnishedBrass", (0.46, 0.36, 0.18, 1.0), roughness=0.48, metallic=0.85)
    mat_iron = make_pbr_material("WroughtIron", (0.09, 0.09, 0.10, 1.0), roughness=0.52, metallic=0.86)
    mat_glass = make_pbr_material(
        "AmberLanternGlass",
        (1.0, 0.68, 0.28, 0.24),
        roughness=0.15,
        metallic=0.05,
        emission_color=(1.0, 0.62, 0.22, 1.0),
        emission_strength=0.6,
        alpha=0.24,
    )
    mat_wax = make_pbr_material("CandleWax", (0.76, 0.70, 0.56, 1.0), roughness=0.82)
    mat_flame_core = make_pbr_material(
        "EmissiveFlameCore",
        (1.0, 0.85, 0.45, 1.0),
        roughness=0.15,
        emission_color=(1.0, 0.72, 0.25, 1.0),
        emission_strength=4.8,
    )
    mat_flame_outer = make_pbr_material(
        "EmissiveAmberFlame",
        (1.0, 0.55, 0.18, 1.0),
        roughness=0.20,
        emission_color=(1.0, 0.48, 0.15, 1.0),
        emission_strength=2.6,
    )
    mat_rune = make_pbr_material(
        "GlowingOccultRune",
        (0.95, 0.18, 0.32, 1.0),
        roughness=0.28,
        emission_color=(1.0, 0.14, 0.28, 1.0),
        emission_strength=3.2,
    )

    # ------------------------------------------------------------------
    # NODE 1: LeftArmGauntlet (60+ sub-parts joined into root node)
    # Lift hand & bail swivel to Z = +0.22 so when LeftHandPivot sits at (-0.31, -0.28, -0.42),
    # the tapered forearm rises from the bottom-left corner while the lantern hangs in full view!
    # ------------------------------------------------------------------
    hand_z_lift: float = 0.18
    gauntlet_parts: list[bpy.types.Object] = build_detailed_arm_gauntlet(
        "LeftHand",
        is_left=True,
        z_offset=0.048 + hand_z_lift,
        mat_leather=mat_leather,
        mat_steel=mat_steel,
        mat_brass=mat_brass,
    )

    # Ornate Bail Handle gripped by hand + 2 Brass Bail Collars + Top Swivel Shackle at (0, 0, hand_z_lift)
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.032,
        minor_radius=0.0042,
        major_segments=24,
        minor_segments=10,
        location=(0.0, 0.0, 0.028 + hand_z_lift),
        rotation=(math.radians(90.0), 0.0, 0.0),
    )
    bail = bpy.context.active_object
    bail.name = "LanternBailHandle"
    bail.scale = (0.92, 1.0, 1.0)
    finalize_part(bail, mat_iron, bevel_width=0.0, smooth_shade=True)
    gauntlet_parts.append(bail)

    for c_idx, cx in enumerate([-0.028, 0.028]):
        bpy.ops.mesh.primitive_torus_add(
            major_radius=0.006,
            minor_radius=0.002,
            major_segments=12,
            minor_segments=6,
            location=(cx, 0.0, 0.028 + hand_z_lift),
            rotation=(0.0, math.radians(90.0), 0.0),
        )
        col_ring = bpy.context.active_object
        col_ring.name = f"BailCollar_{c_idx}"
        finalize_part(col_ring, mat_brass, bevel_width=0.0, smooth_shade=True)
        gauntlet_parts.append(col_ring)

    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.010,
        minor_radius=0.003,
        major_segments=16,
        minor_segments=8,
        location=(0.0, 0.0, hand_z_lift),
        rotation=(0.0, math.radians(90.0), 0.0),
    )
    eyelet = bpy.context.active_object
    eyelet.name = "BailSwivelEyelet"
    finalize_part(eyelet, mat_brass, bevel_width=0.0, smooth_shade=True)
    gauntlet_parts.append(eyelet)

    root_arm = join_into_hierarchy_node("LeftArmGauntlet", gauntlet_parts, pivot_loc=(0.0, 0.0, 0.0))

    # ------------------------------------------------------------------
    # NODE 2: LanternPendulum (62+ sub-parts joined with pivot at (0,0,0))
    # ------------------------------------------------------------------
    pendulum_parts: list[bpy.types.Object] = []

    # 2A. 5 Interlocking 3D Iron Chain Links from Z = -0.008 to Z = -0.044
    pendulum_parts.extend(
        spawn_chain_links(
            "Lantern",
            top_z=-0.008,
            count=5,
            step_z=0.0085,
            major_r=0.0075,
            minor_r=0.0022,
            mat=mat_iron,
        )
    )

    # 2B. Gothic Cross/Spike Finial Crown & Tiered Pagoda Chimney Cap with BOOLEAN Vent Louvers
    bpy.ops.mesh.primitive_cone_add(
        vertices=8,
        radius1=0.010,
        radius2=0.001,
        depth=0.018,
        location=(0.0, 0.0, -0.042),
    )
    finial = bpy.context.active_object
    finial.name = "ChimneyFinialSpike"
    finalize_part(finial, mat_brass, bevel_width=0.001, smooth_shade=True)
    pendulum_parts.append(finial)

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=12,
        radius=0.028,
        depth=0.026,
        location=(0.0, 0.0, -0.056),
    )
    chimney = bpy.context.active_object
    chimney.name = "PagodaChimneyCap"
    finalize_part(chimney, mat_iron, bevel_width=0.002, smooth_shade=True)

    # Carve 6 scalloped heat-vent louvers into the chimney cap via BOOLEAN DIFFERENCE
    for v_i in range(6):
        ang = v_i * (math.pi / 3.0)
        vx = math.cos(ang) * 0.026
        vy = math.sin(ang) * 0.026
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=8,
            radius=0.0045,
            depth=0.016,
            location=(vx, vy, -0.056),
            rotation=(0.0, math.radians(90.0), ang),
        )
        louver_cut = bpy.context.active_object
        mod_b = chimney.modifiers.new(name=f"Louver_{v_i}", type='BOOLEAN')
        mod_b.operation = 'DIFFERENCE'
        mod_b.object = louver_cut
        bpy.context.view_layer.objects.active = chimney
        bpy.ops.object.modifier_apply(modifier=mod_b.name)
        bpy.data.objects.remove(louver_cut, do_unlink=True)
    pendulum_parts.append(chimney)

    # Upper pagoda drip brim
    bpy.ops.mesh.primitive_cone_add(
        vertices=6,
        radius1=0.042,
        radius2=0.026,
        depth=0.012,
        location=(0.0, 0.0, -0.046),
    )
    pagoda_brim = bpy.context.active_object
    pagoda_brim.name = "PagodaUpperBrim"
    finalize_part(pagoda_brim, mat_brass, bevel_width=0.0015, smooth_shade=True)
    pendulum_parts.append(pagoda_brim)

    # Main Hexagonal Steeply Pitched Roof Dome + Cornice Molding Ring
    bpy.ops.mesh.primitive_cone_add(
        vertices=6,
        radius1=0.074,
        radius2=0.028,
        depth=0.036,
        location=(0.0, 0.0, -0.078),
    )
    roof_dome = bpy.context.active_object
    roof_dome.name = "LanternRoofDome"
    finalize_part(roof_dome, mat_iron, bevel_width=0.002, smooth_shade=True)
    pendulum_parts.append(roof_dome)

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=6,
        radius=0.076,
        depth=0.010,
        location=(0.0, 0.0, -0.098),
    )
    cornice = bpy.context.active_object
    cornice.name = "LanternUpperCornice"
    finalize_part(cornice, mat_brass, bevel_width=0.0015, smooth_shade=True)
    pendulum_parts.append(cornice)

    # 2C. Ornate Wrought-Iron Cage:
    # 6 Twisted Spiral Corner Pillars + 12 Brass Rivet Collars + 6 Gothic Trefoil Arch Frames + 6 Wire Guard Bars
    cage_z_center = -0.175
    cage_h = 0.148
    cage_r = 0.068
    for i in range(6):
        angle = i * (math.pi / 3.0)
        bx = math.cos(angle) * cage_r
        by = math.sin(angle) * cage_r

        # Corner Strut Pillar
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=8,
            radius=0.0045,
            depth=cage_h,
            location=(bx, by, cage_z_center),
        )
        strut = bpy.context.active_object
        strut.name = f"CageCornerStrut_{i}"
        finalize_part(strut, mat_iron, bevel_width=0.001, smooth_shade=True)
        pendulum_parts.append(strut)

        # Upper & Lower Brass Rivet Collars on each strut (12 total)
        for c_z in [cage_z_center + cage_h * 0.44, cage_z_center - cage_h * 0.44]:
            bpy.ops.mesh.primitive_torus_add(
                major_radius=0.0062,
                minor_radius=0.0018,
                major_segments=12,
                minor_segments=6,
                location=(bx, by, c_z),
            )
            col = bpy.context.active_object
            col.name = f"StrutCollar_{i}_{int(c_z*100)}"
            finalize_part(col, mat_brass, bevel_width=0.0, smooth_shade=True)
            pendulum_parts.append(col)

        # Face midpoint for Gothic Trefoil Arch & Protective Wire Bar & Recessed Glass Pane
        face_ang = angle + (math.pi / 6.0)
        fx = math.cos(face_ang) * (cage_r * 0.866)
        fy = math.sin(face_ang) * (cage_r * 0.866)

        # Pointed Gothic Trefoil Arch Crown at top of pane
        bpy.ops.mesh.primitive_torus_add(
            major_radius=0.024,
            minor_radius=0.0025,
            major_segments=14,
            minor_segments=6,
            location=(fx, fy, cage_z_center + cage_h * 0.36),
            rotation=(math.radians(90.0), 0.0, face_ang + math.radians(90.0)),
        )
        trefoil = bpy.context.active_object
        trefoil.name = f"GothicPaneArch_{i}"
        trefoil.scale = (1.0, 1.25, 1.0)
        finalize_part(trefoil, mat_iron, bevel_width=0.0, smooth_shade=True)
        pendulum_parts.append(trefoil)

        # Lower Protective Wire Guard Bar
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=8,
            radius=0.0018,
            depth=0.064,
            location=(fx * 1.03, fy * 1.03, cage_z_center - cage_h * 0.20),
            rotation=(math.radians(90.0), 0.0, face_ang),
        )
        wire = bpy.context.active_object
        wire.name = f"PaneGuardWire_{i}"
        finalize_part(wire, mat_brass, bevel_width=0.0004, smooth_shade=True)
        pendulum_parts.append(wire)

        # Individual Recessed Translucent Amber Glass Pane (6 panes)
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(fx * 0.94, fy * 0.94, cage_z_center),
            rotation=(0.0, 0.0, face_ang),
        )
        pane = bpy.context.active_object
        pane.name = f"TranslucentGlassPane_{i}"
        pane.scale = (0.0025, 0.056, cage_h - 0.012)
        finalize_part(pane, mat_glass, bevel_width=0.0005, smooth_shade=False)
        pendulum_parts.append(pane)

    # 2D. Detailed Inner Burner Assembly (Visible through translucent glass):
    # Turned Brass Oil Fount Reservoir + Perforated Gallery + Knurled Wick-Adjuster Thumbwheel + Stem
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16,
        radius=0.032,
        depth=0.018,
        location=(0.0, 0.0, -0.238),
    )
    fount = bpy.context.active_object
    fount.name = "BrassOilFount"
    finalize_part(fount, mat_brass, bevel_width=0.002, smooth_shade=True)
    pendulum_parts.append(fount)

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16,
        radius=0.024,
        depth=0.010,
        location=(0.0, 0.0, -0.226),
    )
    gallery = bpy.context.active_object
    gallery.name = "BurnerGalleryRing"
    finalize_part(gallery, mat_brass, bevel_width=0.001, smooth_shade=True)
    pendulum_parts.append(gallery)

    # Wick Adjuster Stem & Knurled Thumbwheel protruding to the side
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=8,
        radius=0.0022,
        depth=0.038,
        location=(0.028, 0.0, -0.226),
        rotation=(0.0, math.radians(90.0), 0.0),
    )
    wick_stem = bpy.context.active_object
    wick_stem.name = "WickAdjusterStem"
    finalize_part(wick_stem, mat_brass, bevel_width=0.0004, smooth_shade=True)
    pendulum_parts.append(wick_stem)

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=12,
        radius=0.0075,
        depth=0.003,
        location=(0.046, 0.0, -0.226),
        rotation=(0.0, math.radians(90.0), 0.0),
    )
    thumbwheel = bpy.context.active_object
    thumbwheel.name = "WickThumbwheel"
    finalize_part(thumbwheel, mat_brass, bevel_width=0.0005, smooth_shade=True)
    pendulum_parts.append(thumbwheel)

    # Glowing Occult Rune Collar around the burner
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.025,
        minor_radius=0.0024,
        major_segments=18,
        minor_segments=8,
        location=(0.0, 0.0, -0.222),
    )
    rune_collar = bpy.context.active_object
    rune_collar.name = "BurnerRuneCollar"
    finalize_part(rune_collar, mat_rune, bevel_width=0.0, smooth_shade=True)
    pendulum_parts.append(rune_collar)

    # Melted Ritual Tallow Candle + 6 Sculpted Dripping Wax Tendrils + Braided Wick
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=14,
        radius=0.016,
        depth=0.052,
        location=(0.0, 0.0, -0.198),
    )
    candle = bpy.context.active_object
    candle.name = "RitualTallowCandle"
    finalize_part(candle, mat_wax, bevel_width=0.0025, smooth_shade=True)
    pendulum_parts.append(candle)

    for w_i in range(6):
        wang = w_i * (math.pi / 3.0) + 0.25
        wx = math.cos(wang) * 0.0155
        wy = math.sin(wang) * 0.0155
        drip_len = 0.022 + (w_i % 3) * 0.008
        bpy.ops.mesh.primitive_cone_add(
            vertices=8,
            radius1=0.0032,
            radius2=0.0008,
            depth=drip_len,
            location=(wx, wy, -0.178 - drip_len * 0.5),
            rotation=(math.radians(180.0), 0.0, 0.0),
        )
        drip = bpy.context.active_object
        drip.name = f"WaxDripIcicle_{w_i}"
        finalize_part(drip, mat_wax, bevel_width=0.0005, smooth_shade=True)
        pendulum_parts.append(drip)

    # Charred Braided Wick
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=8,
        radius=0.0016,
        depth=0.010,
        location=(0.0, 0.0, -0.168),
    )
    wick = bpy.context.active_object
    wick.name = "CharredWick"
    finalize_part(wick, mat_iron, bevel_width=0.0003, smooth_shade=True)
    pendulum_parts.append(wick)

    # 2-Layer Glowing Inner Flame Core + Outer Teardrop Aura
    bpy.ops.mesh.primitive_cone_add(
        vertices=12,
        radius1=0.0065,
        radius2=0.0008,
        depth=0.022,
        location=(0.0, 0.0, -0.156),
    )
    flame_inner = bpy.context.active_object
    flame_inner.name = "InnerFlameCore"
    finalize_part(flame_inner, mat_flame_core, bevel_width=0.001, smooth_shade=True)
    pendulum_parts.append(flame_inner)

    bpy.ops.mesh.primitive_cone_add(
        vertices=12,
        radius1=0.0105,
        radius2=0.0012,
        depth=0.032,
        location=(0.0, 0.0, -0.154),
    )
    flame_outer = bpy.context.active_object
    flame_outer.name = "OuterFlameAura"
    finalize_part(flame_outer, mat_flame_outer, bevel_width=0.0015, smooth_shade=True)
    pendulum_parts.append(flame_outer)

    # 2E. Heavy Flanged Octagonal Base Plate, Sub-Plinth & Bottom Finial Ring
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=6,
        radius=0.076,
        depth=0.014,
        location=(0.0, 0.0, -0.254),
    )
    base_plate = bpy.context.active_object
    base_plate.name = "LanternFlangedBase"
    finalize_part(base_plate, mat_iron, bevel_width=0.002, smooth_shade=True)
    pendulum_parts.append(base_plate)

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=6,
        radius=0.056,
        depth=0.012,
        location=(0.0, 0.0, -0.266),
    )
    base_plinth = bpy.context.active_object
    base_plinth.name = "LanternBasePlinth"
    finalize_part(base_plinth, mat_brass, bevel_width=0.0015, smooth_shade=True)
    pendulum_parts.append(base_plinth)

    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.012,
        minor_radius=0.0028,
        major_segments=14,
        minor_segments=6,
        location=(0.0, 0.0, -0.278),
        rotation=(math.radians(90.0), 0.0, 0.0),
    )
    bottom_ring = bpy.context.active_object
    bottom_ring.name = "LanternBottomRing"
    finalize_part(bottom_ring, mat_brass, bevel_width=0.0, smooth_shade=True)
    pendulum_parts.append(bottom_ring)

    # 2F. 6 Ornate Gothic Trefoil Finial Spurs around Pagoda Brim + 12 Mullion Rosette Rivets
    for tr_i in range(6):
        tang = tr_i * (math.tau / 6.0)
        tx = math.cos(tang) * 0.041
        ty = math.sin(tang) * 0.041
        bpy.ops.mesh.primitive_cone_add(
            vertices=6,
            radius1=0.0042,
            radius2=0.0008,
            depth=0.014,
            location=(tx, ty, -0.040),
            rotation=(0.0, 0.0, tang),
        )
        trefoil = bpy.context.active_object
        trefoil.name = f"PagodaTrefoilSpur_{tr_i}"
        finalize_part(trefoil, mat_brass, bevel_width=0.0004, smooth_shade=True)
        pendulum_parts.append(trefoil)

    mullion_rosette_pts: list[tuple[float, float, float]] = []
    for m_i in range(6):
        mang = m_i * (math.tau / 6.0)
        mx = math.cos(mang) * 0.071
        my = math.sin(mang) * 0.071
        mullion_rosette_pts.append((mx, my, -0.118))
        mullion_rosette_pts.append((mx, my, -0.222))
    pendulum_parts.extend(spawn_rivet_line("MullionRosette", mullion_rosette_pts, 0.0024, mat_brass))

    # Additional 2-Layer Flame Wisp Spire & Hot Ember Base Collar (4-layer total flame)
    bpy.ops.mesh.primitive_cone_add(
        vertices=10,
        radius1=0.0042,
        radius2=0.0004,
        depth=0.038,
        location=(0.0, 0.0, -0.146),
    )
    flame_wisp = bpy.context.active_object
    flame_wisp.name = "FlameWispSpire"
    finalize_part(flame_wisp, mat_flame_core, bevel_width=0.0005, smooth_shade=True)
    pendulum_parts.append(flame_wisp)

    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.0055,
        minor_radius=0.0016,
        major_segments=12,
        minor_segments=6,
        location=(0.0, 0.0, -0.168),
    )
    ember_collar = bpy.context.active_object
    ember_collar.name = "HotEmberWickCollar"
    finalize_part(ember_collar, mat_flame_outer, bevel_width=0.0, smooth_shade=True)
    pendulum_parts.append(ember_collar)

    # 2G. Suspended Miniature Incense Censer Charm below LanternBottomRing (10 sub-parts)
    pendulum_parts.extend(
        spawn_chain_links(
            "LowerCharmChain",
            top_z=-0.284,
            count=4,
            step_z=0.0065,
            major_r=0.0042,
            minor_r=0.0011,
            mat=mat_iron,
        )
    )
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=12,
        ring_count=8,
        radius=0.011,
        location=(0.0, 0.0, -0.318),
    )
    charm_pod = bpy.context.active_object
    charm_pod.name = "IncenseCharmPod"
    finalize_part(charm_pod, mat_brass, bevel_width=0.0, smooth_shade=True)
    pendulum_parts.append(charm_pod)

    bpy.ops.mesh.primitive_cone_add(
        vertices=8,
        radius1=0.0055,
        radius2=0.0008,
        depth=0.014,
        location=(0.0, 0.0, -0.332),
        rotation=(math.pi, 0.0, 0.0),
    )
    charm_drop = bpy.context.active_object
    charm_drop.name = "IncenseCharmFinialDrop"
    finalize_part(charm_drop, mat_brass, bevel_width=0.0005, smooth_shade=True)
    pendulum_parts.append(charm_drop)

    for cv_i in range(4):
        c_ang = cv_i * (math.pi * 0.5)
        cvx = math.cos(c_ang) * 0.0105
        cvy = math.sin(c_ang) * 0.0105
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=8,
            ring_count=6,
            radius=0.0022,
            location=(cvx, cvy, -0.318),
        )
        c_bead = bpy.context.active_object
        c_bead.name = f"CharmRuneBead_{cv_i}"
        finalize_part(c_bead, mat_flame_outer, bevel_width=0.0, smooth_shade=True)
        pendulum_parts.append(c_bead)

    pendulum_node = join_into_hierarchy_node(
        "LanternPendulum",
        pendulum_parts,
        pivot_loc=(0.0, 0.0, 0.0),
        parent_obj=root_arm,
    )
    pendulum_node.location = (0.0, 0.0, hand_z_lift)

    os.makedirs("assets/models/weapons", exist_ok=True)
    export_path = os.path.abspath("assets/models/weapons/viewmodel_left_lantern.glb")
    bpy.ops.export_scene.gltf(
        filepath=export_path,
        export_format='GLB',
        use_selection=False,
        export_apply=False,
        export_all_vertex_colors=True,
        export_active_vertex_color_when_no_material=True,
    )
    print(f"[Blender] Exported Left Lantern Viewmodel: {export_path}")


# ==============================================================================
# 2. RIGHT VIEWMODEL: MECHANICAL OCCULT REVOLVER (140+ SUB-COMPONENTS)
# ==============================================================================

def build_viewmodel_right_revolver() -> None:
    """
    Builds the 140+ sub-component Occult Revolver oriented so Blender +Y -> Godot -Z (Forward)
    and Blender +Z -> Godot +Y (Up).
    Joined into clean mechanical hierarchy nodes:
      RevolverFrame (root)
        ├── Cylinder (pivoted at (0, 0.038, 0.013) along Y spin axis)
        ├── Hammer (pivoted at (0, -0.028, 0.036))
        ├── Trigger (pivoted at (0, 0.008, -0.022))
        ├── SideGearWheel (pivoted at (-0.018, 0.002, 0.012))
        ├── EjectorRod (pivoted at (0, 0.21, 0.010))
        └── MuzzleAnchor (empty at (0, 0.32, 0.028))
    """
    clear_scene()

    # Satin/Matte PBR Materials (No white polygon glare)
    mat_blued = make_pbr_material("BluedSteel", (0.10, 0.11, 0.13, 1.0), roughness=0.42, metallic=0.88)
    mat_brass = make_pbr_material("TarnishedBrass", (0.46, 0.36, 0.18, 1.0), roughness=0.48, metallic=0.85)
    mat_silver = make_pbr_material("OccultSilver", (0.58, 0.60, 0.64, 1.0), roughness=0.36, metallic=0.92)
    mat_walnut = make_pbr_material("DarkOiledWalnut", (0.14, 0.08, 0.045, 1.0), roughness=0.82)
    mat_leather = make_pbr_material("WeatheredLeather", (0.12, 0.085, 0.065, 1.0), roughness=0.86)
    mat_steel_plate = make_pbr_material("GothicPlateSteel", (0.18, 0.19, 0.21, 1.0), roughness=0.42, metallic=0.88)
    mat_rune = make_pbr_material(
        "GlowingOccultRune",
        (0.95, 0.18, 0.32, 1.0),
        roughness=0.28,
        emission_color=(1.0, 0.14, 0.28, 1.0),
        emission_strength=3.4,
    )

    # ------------------------------------------------------------------
    # NODE 1: RevolverFrame (95+ sub-parts joined into root node)
    # ------------------------------------------------------------------
    frame_parts: list[bpy.types.Object] = build_detailed_arm_gauntlet(
        "RightHand",
        is_left=False,
        z_offset=0.0,
        mat_leather=mat_leather,
        mat_steel=mat_steel_plate,
        mat_brass=mat_brass,
    )

    # 1A. Carved Walnut Birdshead Grip + Diamond Checkering Ribs + 6 Glowing Sigils + Brass Skull/Octagonal Butt-Cap
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0.0, -0.042, -0.052),
        rotation=(math.radians(-26.0), 0.0, 0.0),
    )
    grip = bpy.context.active_object
    grip.name = "WalnutBirdsheadGrip"
    grip.scale = (0.026, 0.042, 0.098)
    finalize_part(grip, mat_walnut, bevel_width=0.004, smooth_shade=True)
    frame_parts.append(grip)

    # 6 Carved Checkering Ribs & 6 Glowing Sigil Inlays on left and right grip panels
    for side_x in [-0.0135, 0.0135]:
        for g_i in range(3):
            gz_off = -0.032 - g_i * 0.018
            gy_off = -0.034 - g_i * 0.008
            bpy.ops.mesh.primitive_cube_add(
                size=1.0,
                location=(side_x, gy_off, gz_off),
                rotation=(math.radians(-26.0), 0.0, 0.0),
            )
            sigil = bpy.context.active_object
            sigil.name = f"GripRuneSigil_{'L' if side_x < 0 else 'R'}_{g_i}"
            sigil.scale = (0.0018, 0.014, 0.006)
            finalize_part(sigil, mat_rune, bevel_width=0.0003, smooth_shade=False)
            frame_parts.append(sigil)
        for fg_i in range(4):
            fg_z = -0.026 - fg_i * 0.015
            fg_y = -0.028 - fg_i * 0.007
            bpy.ops.mesh.primitive_cube_add(
                size=1.0,
                location=(side_x * 0.98, fg_y, fg_z),
                rotation=(math.radians(-26.0), 0.0, 0.0),
            )
            fg_rib = bpy.context.active_object
            fg_rib.name = f"GripCheckeringRib_{'L' if side_x < 0 else 'R'}_{fg_i}"
            fg_rib.scale = (0.0022, 0.026, 0.0032)
            finalize_part(fg_rib, mat_brass, bevel_width=0.0004, smooth_shade=True)
            frame_parts.append(fg_rib)

    # Flanged Brass Octagonal Butt-Cap + Finial Boss + Lanyard Loop
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=8,
        radius=0.022,
        depth=0.014,
        location=(0.0, -0.064, -0.098),
        rotation=(math.radians(-26.0), 0.0, 0.0),
    )
    butt_cap = bpy.context.active_object
    butt_cap.name = "FlangedBrassButtCap"
    butt_cap.scale = (0.68, 1.0, 1.0)
    finalize_part(butt_cap, mat_brass, bevel_width=0.002, smooth_shade=True)
    frame_parts.append(butt_cap)

    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.0095,
        minor_radius=0.0022,
        major_segments=16,
        minor_segments=6,
        location=(0.0, -0.072, -0.112),
        rotation=(0.0, math.radians(90.0), 0.0),
    )
    lanyard = bpy.context.active_object
    lanyard.name = "ButtLanyardRing"
    finalize_part(lanyard, mat_brass, bevel_width=0.0, smooth_shade=True)
    frame_parts.append(lanyard)

    # 1B. Multi-Stepped Gothic Receiver Frame, Top Strap, Crane Shelf, Hinged Loading Gate & Filigree
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -0.012, 0.008))
    receiver = bpy.context.active_object
    receiver.name = "StandingBreechReceiver"
    receiver.scale = (0.030, 0.048, 0.052)
    finalize_part(receiver, mat_blued, bevel_width=0.003, smooth_shade=True)
    frame_parts.append(receiver)

    # Hinged Side Loading Gate on Right Side (+X)
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=10,
        radius=0.012,
        depth=0.032,
        location=(0.015, 0.002, 0.012),
        rotation=(math.radians(90.0), 0.0, 0.0),
    )
    load_gate = bpy.context.active_object
    load_gate.name = "SideLoadingGate"
    load_gate.scale = (0.45, 1.0, 1.0)
    finalize_part(load_gate, mat_brass, bevel_width=0.0015, smooth_shade=True)
    frame_parts.append(load_gate)

    # Ornate Gothic Filigree Sideplates on Left and Right (8 sub-parts)
    for sx in [-0.0155, 0.0155]:
        frame_parts.extend(spawn_gothic_filigree(f"Receiver_{'L' if sx < 0 else 'R'}", sx, -0.014, 0.008, mat_brass, mat_rune))

    # 10 Precision Receiver Screw Heads / Pins (5 per side)
    screw_pts: list[tuple[float, float, float]] = []
    for sx in [-0.0165, 0.0165]:
        screw_pts.extend([
            (sx, -0.028, 0.028),
            (sx, -0.028, -0.008),
            (sx, 0.002, -0.014),
            (sx, 0.072, -0.018),
            (sx, 0.072, 0.044),
        ])
    frame_parts.extend(spawn_rivet_line("ReceiverScrew", screw_pts, 0.0022, mat_silver))
    for sc_idx, (sc_x, sc_y, sc_z) in enumerate(screw_pts):
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(sc_x * 1.03, sc_y, sc_z),
            rotation=(math.radians(25.0 * (sc_idx % 3)), 0.0, 0.0),
        )
        sc_slot = bpy.context.active_object
        sc_slot.name = f"ReceiverScrewSlot_{sc_idx}"
        sc_slot.scale = (0.0010, 0.0036, 0.0008)
        finalize_part(sc_slot, mat_blued, bevel_width=0.0002, smooth_shade=False)
        frame_parts.append(sc_slot)

    # Top Strap + Micro-Adjustable V-Notch Rear Sight (3 parts)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.038, 0.046))
    top_strap = bpy.context.active_object
    top_strap.name = "TopStrap"
    top_strap.scale = (0.024, 0.096, 0.012)
    finalize_part(top_strap, mat_blued, bevel_width=0.002, smooth_shade=True)
    frame_parts.append(top_strap)

    for rs_x in [-0.005, 0.005]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(rs_x, -0.004, 0.054))
        rs_ear = bpy.context.active_object
        rs_ear.name = f"RearSightEar_{'L' if rs_x < 0 else 'R'}"
        rs_ear.scale = (0.004, 0.014, 0.006)
        finalize_part(rs_ear, mat_brass, bevel_width=0.0008, smooth_shade=True)
        frame_parts.append(rs_ear)
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=8,
            ring_count=6,
            radius=0.0011,
            location=(rs_x, -0.011, 0.055),
        )
        rs_dot = bpy.context.active_object
        rs_dot.name = f"RearSightRuneDot_{'L' if rs_x < 0 else 'R'}"
        finalize_part(rs_dot, mat_rune, bevel_width=0.0, smooth_shade=True)
        frame_parts.append(rs_dot)

    # Lower Frame Crane Shelf + Scrolled Brass Trigger Guard Bow + Spur
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.038, -0.020))
    crane_shelf = bpy.context.active_object
    crane_shelf.name = "FrameCraneShelf"
    crane_shelf.scale = (0.022, 0.088, 0.012)
    finalize_part(crane_shelf, mat_blued, bevel_width=0.002, smooth_shade=True)
    frame_parts.append(crane_shelf)

    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.024,
        minor_radius=0.0036,
        major_segments=20,
        minor_segments=8,
        location=(0.0, 0.006, -0.034),
        rotation=(0.0, math.radians(90.0), 0.0),
    )
    trig_guard = bpy.context.active_object
    trig_guard.name = "ScrolledTriggerGuard"
    trig_guard.scale = (0.72, 1.22, 0.82)
    finalize_part(trig_guard, mat_brass, bevel_width=0.0, smooth_shade=True)
    frame_parts.append(trig_guard)

    # 1C. Heavy Octagonal Barrel Assembly + 8 Ventilated Rib Bridges + Front Sight + Under-Barrel Shroud
    # Strictly locked to X = 0.0 along the longitudinal Y barrel axis!
    # NOTE: In XYZ Euler order, rotation=(pi/2, pi/8, 0.0) tilts the cylinder onto Y and rolls the octagon
    # by 22.5 deg around Y so the top flat is horizontal at Z = barrel_z + 0.021*cos(22.5 deg) = barrel_z + 0.0194!
    barrel_len = 0.22
    barrel_y_center = 0.19
    barrel_z = 0.028
    muzzle_y = barrel_y_center + barrel_len * 0.5
    barrel_top_flat_z = barrel_z + 0.021 * math.cos(math.radians(22.5))

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=8,
        radius=0.021,
        depth=barrel_len,
        location=(0.0, barrel_y_center, barrel_z),
        rotation=(math.radians(90.0), math.radians(22.5), 0.0),
    )
    barrel = bpy.context.active_object
    barrel.name = "OctagonalBarrel"
    finalize_part(barrel, mat_blued, bevel_width=0.002, smooth_shade=False)

    # Deep Muzzle Bore Cutout via BOOLEAN DIFFERENCE
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16,
        radius=0.0115,
        depth=0.14,
        location=(0.0, muzzle_y - 0.04, barrel_z),
        rotation=(math.radians(90.0), 0.0, 0.0),
    )
    bore_cutter = bpy.context.active_object
    mod_bore = barrel.modifiers.new(name="BoreCut", type='BOOLEAN')
    mod_bore.operation = 'DIFFERENCE'
    mod_bore.object = bore_cutter
    bpy.context.view_layer.objects.active = barrel
    bpy.ops.object.modifier_apply(modifier=mod_bore.name)
    bpy.data.objects.remove(bore_cutter, do_unlink=True)
    frame_parts.append(barrel)

    # Rifled Muzzle Crown Collar
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.0145,
        minor_radius=0.0022,
        major_segments=16,
        minor_segments=8,
        location=(0.0, muzzle_y, barrel_z),
        rotation=(math.radians(90.0), 0.0, 0.0),
    )
    crown = bpy.context.active_object
    crown.name = "MuzzleCrownCollar"
    finalize_part(crown, mat_brass, bevel_width=0.0, smooth_shade=True)
    frame_parts.append(crown)

    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.0132,
        minor_radius=0.0011,
        major_segments=16,
        minor_segments=6,
        location=(0.0, muzzle_y + 0.0012, barrel_z),
        rotation=(math.radians(90.0), 0.0, 0.0),
    )
    crown_rune = bpy.context.active_object
    crown_rune.name = "MuzzleCrownRuneRing"
    finalize_part(crown_rune, mat_rune, bevel_width=0.0, smooth_shade=True)
    frame_parts.append(crown_rune)

    # 12 Lateral Barrel Flat Filigree Ribs & Glowing Occult Rune Channels along left/right octagonal flats
    for b_side in [-1.0, 1.0]:
        bx_flat = b_side * 0.0195
        for bf_i in range(3):
            by_seg = (barrel_y_center - 0.055) + bf_i * 0.055
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx_flat, by_seg, barrel_z + 0.003))
            b_fil = bpy.context.active_object
            b_fil.name = f"BarrelFiligreeRib_{'L' if b_side < 0 else 'R'}_{bf_i}"
            b_fil.scale = (0.0016, 0.038, 0.0034)
            finalize_part(b_fil, mat_brass, bevel_width=0.0004, smooth_shade=True)
            frame_parts.append(b_fil)

            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx_flat * 1.04, by_seg, barrel_z - 0.003))
            b_rune = bpy.context.active_object
            b_rune.name = f"BarrelRuneStrip_{'L' if b_side < 0 else 'R'}_{bf_i}"
            b_rune.scale = (0.0012, 0.028, 0.0018)
            finalize_part(b_rune, mat_rune, bevel_width=0.0002, smooth_shade=False)
            frame_parts.append(b_rune)

    # Top Ventilated Sighting Rib + 8 Milled Vent Bridge Pillars (strictly X = 0.0, flush on barrel_top_flat_z)
    rib_z = barrel_top_flat_z + 0.0042
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, barrel_y_center, rib_z))
    top_rib = bpy.context.active_object
    top_rib.name = "VentilatedTopRib"
    top_rib.scale = (0.011, barrel_len, 0.0040)
    finalize_part(top_rib, mat_blued, bevel_width=0.0008, smooth_shade=True)
    frame_parts.append(top_rib)

    for v_i in range(8):
        vy = (barrel_y_center - barrel_len * 0.44) + v_i * (barrel_len * 0.125)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, vy, barrel_top_flat_z + 0.0014))
        pillar = bpy.context.active_object
        pillar.name = f"RibBridgePillar_{v_i}"
        pillar.scale = (0.0095, 0.008, 0.0032)
        finalize_part(pillar, mat_brass, bevel_width=0.0005, smooth_shade=True)
        frame_parts.append(pillar)

    # Dovetailed Front Sight Base + Brass Blade + Glowing Rune Bead (strictly X = 0.0)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, muzzle_y - 0.016, rib_z + 0.0032))
    fs_base = bpy.context.active_object
    fs_base.name = "FrontSightDovetail"
    fs_base.scale = (0.012, 0.018, 0.0032)
    finalize_part(fs_base, mat_brass, bevel_width=0.0006, smooth_shade=True)
    frame_parts.append(fs_base)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, muzzle_y - 0.016, rib_z + 0.0085))
    fs_blade = bpy.context.active_object
    fs_blade.name = "FrontSightBlade"
    fs_blade.scale = (0.0032, 0.014, 0.0095)
    finalize_part(fs_blade, mat_brass, bevel_width=0.0005, smooth_shade=True)
    frame_parts.append(fs_blade)

    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=10,
        ring_count=6,
        radius=0.0022,
        location=(0.0, muzzle_y - 0.022, rib_z + 0.011),
    )
    fs_dot = bpy.context.active_object
    fs_dot.name = "FrontSightRuneDot"
    finalize_part(fs_dot, mat_rune, bevel_width=0.0, smooth_shade=True)
    frame_parts.append(fs_dot)

    # Under-Barrel Crane Lock & Ejector Shroud Housing
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=8,
        radius=0.009,
        depth=barrel_len * 0.55,
        location=(0.0, barrel_y_center - 0.035, barrel_z - 0.018),
        rotation=(math.radians(90.0), 0.0, 0.0),
    )
    shroud = bpy.context.active_object
    shroud.name = "UnderBarrelShroud"
    finalize_part(shroud, mat_blued, bevel_width=0.0012, smooth_shade=True)
    frame_parts.append(shroud)

    root_frame = join_into_hierarchy_node("RevolverFrame", frame_parts, pivot_loc=(0.0, 0.0, 0.0))

    # ------------------------------------------------------------------
    # NODE 2: Cylinder (38+ sub-parts joined with pivot at (0, 0.038, 0.013))
    # ------------------------------------------------------------------
    cyl_pos = (0.0, 0.038, 0.013)
    cyl_len = 0.062
    cyl_radius = 0.030
    cyl_parts: list[bpy.types.Object] = []

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24,
        radius=cyl_radius,
        depth=cyl_len,
        location=cyl_pos,
        rotation=(math.radians(90.0), 0.0, 0.0),
    )
    cyl_body = bpy.context.active_object
    cyl_body.name = "CylinderBody"
    finalize_part(cyl_body, mat_blued, bevel_width=0.0018, smooth_shade=True)

    # Carve 6 bored-through chambers via BOOLEAN DIFFERENCE
    for ch_idx in range(6):
        ch_ang = ch_idx * (math.pi / 3.0)
        ch_x = cyl_pos[0] + math.cos(ch_ang) * (cyl_radius * 0.62)
        ch_z = cyl_pos[2] + math.sin(ch_ang) * (cyl_radius * 0.62)
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=14,
            radius=0.0068,
            depth=cyl_len + 0.01,
            location=(ch_x, cyl_pos[1], ch_z),
            rotation=(math.radians(90.0), 0.0, 0.0),
        )
        ch_cut = bpy.context.active_object
        mod_ch = cyl_body.modifiers.new(name=f"ChamberBore_{ch_idx}", type='BOOLEAN')
        mod_ch.operation = 'DIFFERENCE'
        mod_ch.object = ch_cut
        bpy.context.view_layer.objects.active = cyl_body
        bpy.ops.object.modifier_apply(modifier=mod_ch.name)
        bpy.data.objects.remove(ch_cut, do_unlink=True)

    cyl_parts.append(cyl_body)

    # Rear Ratcheting Star Extractor Gear + Center Arbor Pin
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=12,
        radius=0.012,
        depth=0.004,
        location=(cyl_pos[0], cyl_pos[1] - cyl_len * 0.51, cyl_pos[2]),
        rotation=(math.radians(90.0), 0.0, 0.0),
    )
    ratchet = bpy.context.active_object
    ratchet.name = "RatchetExtractorStar"
    finalize_part(ratchet, mat_brass, bevel_width=0.0005, smooth_shade=True)
    cyl_parts.append(ratchet)

    # 6 Exterior Flutes with Glowing Crimson Rune Strips + 6 Loaded Cartridges (24 parts)
    for ch_idx in range(6):
        ch_ang = ch_idx * (math.pi / 3.0)
        ch_x = cyl_pos[0] + math.cos(ch_ang) * (cyl_radius * 0.62)
        ch_z = cyl_pos[2] + math.sin(ch_ang) * (cyl_radius * 0.62)

        # Exterior Flute Brass Rib & Glowing Rune Inlay
        fl_ang = ch_ang + math.pi / 6.0
        fl_x = cyl_pos[0] + math.cos(fl_ang) * (cyl_radius * 0.98)
        fl_z = cyl_pos[2] + math.sin(fl_ang) * (cyl_radius * 0.98)
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(fl_x, cyl_pos[1], fl_z),
            rotation=(0.0, fl_ang, 0.0),
        )
        fl_rune = bpy.context.active_object
        fl_rune.name = f"CylinderFluteRune_{ch_idx}"
        fl_rune.scale = (0.0022, cyl_len * 0.72, 0.0022)
        finalize_part(fl_rune, mat_rune, bevel_width=0.0003, smooth_shade=False)
        cyl_parts.append(fl_rune)

        # Brass Flute Framing Rib & Rear Cylinder Stop Locking Notch
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(fl_x * 0.985, cyl_pos[1], fl_z * 0.985),
            rotation=(0.0, fl_ang, 0.0),
        )
        fl_brass = bpy.context.active_object
        fl_brass.name = f"CylinderFluteBrassFrame_{ch_idx}"
        fl_brass.scale = (0.0036, cyl_len * 0.78, 0.0014)
        finalize_part(fl_brass, mat_brass, bevel_width=0.0003, smooth_shade=True)
        cyl_parts.append(fl_brass)

        st_x = cyl_pos[0] + math.cos(ch_ang) * (cyl_radius * 0.99)
        st_z = cyl_pos[2] + math.sin(ch_ang) * (cyl_radius * 0.99)
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(st_x, cyl_pos[1] - cyl_len * 0.34, st_z),
            rotation=(0.0, ch_ang, 0.0),
        )
        stop_notch = bpy.context.active_object
        stop_notch.name = f"CylinderStopNotch_{ch_idx}"
        stop_notch.scale = (0.0028, 0.0075, 0.0020)
        finalize_part(stop_notch, mat_silver, bevel_width=0.0003, smooth_shade=True)
        cyl_parts.append(stop_notch)

        # 4-part Loaded Cartridge inside each chamber
        for cp in spawn_cartridge_assembly(ch_idx, ch_x, ch_z, cyl_len, mat_brass, mat_silver, mat_rune):
            cp.location.y += cyl_pos[1]
            cyl_parts.append(cp)

    join_into_hierarchy_node("Cylinder", cyl_parts, pivot_loc=cyl_pos, parent_obj=root_frame)

    # ------------------------------------------------------------------
    # NODE 3: Hammer (Pivoted at (0, -0.028, 0.036))
    # ------------------------------------------------------------------
    hammer_pivot = (0.0, -0.028, 0.036)
    hammer_parts: list[bpy.types.Object] = []

    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0.0, -0.036, 0.048),
        rotation=(math.radians(-18.0), 0.0, 0.0),
    )
    h_body = bpy.context.active_object
    h_body.name = "HammerBody"
    h_body.scale = (0.008, 0.018, 0.032)
    finalize_part(h_body, mat_blued, bevel_width=0.0015, smooth_shade=True)
    hammer_parts.append(h_body)

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=12,
        radius=0.006,
        depth=0.013,
        location=(0.0, -0.048, 0.058),
        rotation=(0.0, math.radians(90.0), 0.0),
    )
    h_spur = bpy.context.active_object
    h_spur.name = "HammerCheckeredSpur"
    finalize_part(h_spur, mat_brass, bevel_width=0.0008, smooth_shade=True)
    hammer_parts.append(h_spur)

    for kn_i in range(6):
        kny = -0.052 + kn_i * 0.0018
        knz = 0.0635 - abs(kn_i - 2.5) * 0.0005
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(0.0, kny, knz),
        )
        kn_rib = bpy.context.active_object
        kn_rib.name = f"HammerSpurKnurl_{kn_i}"
        kn_rib.scale = (0.0125, 0.0010, 0.0016)
        finalize_part(kn_rib, mat_silver, bevel_width=0.0002, smooth_shade=False)
        hammer_parts.append(kn_rib)

    bpy.ops.mesh.primitive_cone_add(
        vertices=10,
        radius1=0.003,
        radius2=0.0008,
        depth=0.010,
        location=(0.0, -0.024, 0.052),
        rotation=(math.radians(-90.0), 0.0, 0.0),
    )
    h_nose = bpy.context.active_object
    h_nose.name = "HammerFiringPinNose"
    finalize_part(h_nose, mat_silver, bevel_width=0.0004, smooth_shade=True)
    hammer_parts.append(h_nose)

    join_into_hierarchy_node("Hammer", hammer_parts, pivot_loc=hammer_pivot, parent_obj=root_frame)

    # ------------------------------------------------------------------
    # NODE 4: Trigger (Pivoted at (0, 0.008, -0.022))
    # ------------------------------------------------------------------
    trigger_pivot = (0.0, 0.008, -0.022)
    trig_parts: list[bpy.types.Object] = []

    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0.0, 0.004, -0.034),
        rotation=(math.radians(-20.0), 0.0, 0.0),
    )
    t_blade = bpy.context.active_object
    t_blade.name = "SerratedTriggerBlade"
    t_blade.scale = (0.006, 0.010, 0.024)
    finalize_part(t_blade, mat_brass, bevel_width=0.001, smooth_shade=True)
    trig_parts.append(t_blade)

    join_into_hierarchy_node("Trigger", trig_parts, pivot_loc=trigger_pivot, parent_obj=root_frame)

    # ------------------------------------------------------------------
    # NODE 5: SideGearWheel (Clockwork Occult Gear on Left Receiver at (-0.017, 0.002, 0.012))
    # ------------------------------------------------------------------
    gear_pivot = (-0.017, 0.002, 0.012)
    gear_parts: list[bpy.types.Object] = []

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16,
        radius=0.012,
        depth=0.0035,
        location=gear_pivot,
        rotation=(0.0, math.radians(90.0), 0.0),
    )
    g_wheel = bpy.context.active_object
    g_wheel.name = "ClockworkGearWheel"
    finalize_part(g_wheel, mat_brass, bevel_width=0.0005, smooth_shade=True)
    gear_parts.append(g_wheel)

    for gt_i in range(8):
        gt_ang = gt_i * (math.pi / 4.0)
        gy = gear_pivot[1] + math.cos(gt_ang) * 0.012
        gz = gear_pivot[2] + math.sin(gt_ang) * 0.012
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(gear_pivot[0], gy, gz),
            rotation=(gt_ang, 0.0, 0.0),
        )
        tooth = bpy.context.active_object
        tooth.name = f"GearTooth_{gt_i}"
        tooth.scale = (0.003, 0.003, 0.0035)
        finalize_part(tooth, mat_brass, bevel_width=0.0004, smooth_shade=True)
        gear_parts.append(tooth)

    join_into_hierarchy_node("SideGearWheel", gear_parts, pivot_loc=gear_pivot, parent_obj=root_frame)

    # ------------------------------------------------------------------
    # NODE 6: EjectorRod (Under-barrel rod + 8 helical return spring coils + knurled head)
    # ------------------------------------------------------------------
    ejector_pivot = (0.0, 0.21, 0.010)
    ej_parts: list[bpy.types.Object] = []

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=10,
        radius=0.0038,
        depth=0.095,
        location=(0.0, 0.235, 0.010),
        rotation=(math.radians(90.0), 0.0, 0.0),
    )
    ej_shaft = bpy.context.active_object
    ej_shaft.name = "EjectorRodShaft"
    finalize_part(ej_shaft, mat_silver, bevel_width=0.0005, smooth_shade=True)
    ej_parts.append(ej_shaft)

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=14,
        radius=0.0085,
        depth=0.014,
        location=(0.0, 0.282, 0.010),
        rotation=(math.radians(90.0), 0.0, 0.0),
    )
    ej_head = bpy.context.active_object
    ej_head.name = "EjectorKnurledHead"
    finalize_part(ej_head, mat_brass, bevel_width=0.001, smooth_shade=True)
    ej_parts.append(ej_head)

    # 8 Helical Return Spring Coils around the Ejector Rod
    for sp_i in range(8):
        spy = 0.215 + sp_i * 0.0075
        bpy.ops.mesh.primitive_torus_add(
            major_radius=0.0062,
            minor_radius=0.0012,
            major_segments=14,
            minor_segments=6,
            location=(0.0, spy, 0.010),
            rotation=(math.radians(82.0), 0.0, 0.0),
        )
        coil = bpy.context.active_object
        coil.name = f"EjectorSpringCoil_{sp_i}"
        finalize_part(coil, mat_brass, bevel_width=0.0, smooth_shade=True)
        ej_parts.append(coil)

    join_into_hierarchy_node("EjectorRod", ej_parts, pivot_loc=ejector_pivot, parent_obj=root_frame)

    # ------------------------------------------------------------------
    # NODE 7: MuzzleAnchor (Empty at front tip of barrel bore)
    # ------------------------------------------------------------------
    muzzle_anchor = bpy.data.objects.new("MuzzleAnchor", None)
    muzzle_anchor.empty_display_type = 'SINGLE_ARROW'
    muzzle_anchor.empty_display_size = 0.05
    muzzle_anchor.location = (0.0, muzzle_y + 0.02, barrel_z)
    bpy.context.collection.objects.link(muzzle_anchor)
    muzzle_anchor.parent = root_frame
    muzzle_anchor.matrix_parent_inverse = root_frame.matrix_world.inverted()

    os.makedirs("assets/models/weapons", exist_ok=True)
    export_path = os.path.abspath("assets/models/weapons/viewmodel_right_revolver.glb")
    bpy.ops.export_scene.gltf(
        filepath=export_path,
        export_format='GLB',
        use_selection=False,
        export_apply=False,
        export_all_vertex_colors=True,
        export_active_vertex_color_when_no_material=True,
    )
    print(f"[Blender] Exported Right Revolver Viewmodel: {export_path}")


# ==============================================================================
# 3. RIGHT VIEWMODEL: GOTHIC DOUBLE-BARREL COACH GUN (135+ SUB-COMPONENTS)
# ==============================================================================

def build_viewmodel_right_shotgun() -> None:
    """
    Builds the 135+ sub-component Break-Action Double-Barrel Coach Gun oriented so
    Blender +Y -> Godot -Z (Forward) and Blender +Z -> Godot +Y (Up).
    Joined into clean mechanical hierarchy nodes:
      ShotgunFrame (root)
        ├── BarrelAssembly (pivoted at front lower hinge pin (0, 0.055, -0.002))
        │     ├── ShellLeft (pivoted at (-0.013, 0.018, 0.022))
        │     └── ShellRight (pivoted at (0.013, 0.018, 0.022))
        ├── HammerLeft (pivoted at (-0.012, -0.018, 0.032))
        ├── HammerRight (pivoted at (0.012, -0.018, 0.032))
        └── TopLever (pivoted at (0.0, -0.012, 0.038))
    """
    clear_scene()

    mat_blued = make_pbr_material("BluedSteel", (0.10, 0.11, 0.13, 1.0), roughness=0.42, metallic=0.88)
    mat_brass = make_pbr_material("TarnishedBrass", (0.46, 0.36, 0.18, 1.0), roughness=0.48, metallic=0.85)
    mat_silver = make_pbr_material("OccultSilver", (0.58, 0.60, 0.64, 1.0), roughness=0.36, metallic=0.92)
    mat_walnut = make_pbr_material("DarkOiledWalnut", (0.14, 0.08, 0.045, 1.0), roughness=0.82)
    mat_leather = make_pbr_material("WeatheredLeather", (0.12, 0.085, 0.065, 1.0), roughness=0.86)
    mat_steel_plate = make_pbr_material("GothicPlateSteel", (0.18, 0.19, 0.21, 1.0), roughness=0.42, metallic=0.88)
    mat_bore = make_pbr_material("DarkBoreShadow", (0.01, 0.01, 0.012, 1.0), roughness=0.96, metallic=0.0)
    mat_rune = make_pbr_material(
        "GlowingOccultRune",
        (0.95, 0.18, 0.32, 1.0),
        roughness=0.28,
        emission_color=(1.0, 0.14, 0.28, 1.0),
        emission_strength=3.4,
    )

    # ------------------------------------------------------------------
    # NODE 1: ShotgunFrame (Right Gauntlet + Walnut Stock + Standing Breech + Filigree)
    # ------------------------------------------------------------------
    frame_parts: list[bpy.types.Object] = build_detailed_arm_gauntlet(
        "RightHandShotgun",
        is_left=False,
        z_offset=0.0,
        mat_leather=mat_leather,
        mat_steel=mat_steel_plate,
        mat_brass=mat_brass,
    )

    # Curved Walnut Sawed-Off Grip Stock + Checkering + Brass Skull Butt-Plate
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0.0, -0.055, -0.044),
        rotation=(math.radians(-22.0), 0.0, 0.0),
    )
    stock = bpy.context.active_object
    stock.name = "CoachGunWalnutStock"
    stock.scale = (0.032, 0.088, 0.082)
    finalize_part(stock, mat_walnut, bevel_width=0.004, smooth_shade=True)
    frame_parts.append(stock)

    # Brass Skull Butt-Plate & Pommel Cap
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0.0, -0.098, -0.064),
        rotation=(math.radians(-22.0), 0.0, 0.0),
    )
    butt_plate = bpy.context.active_object
    butt_plate.name = "BrassSkullButtPlate"
    butt_plate.scale = (0.034, 0.012, 0.084)
    finalize_part(butt_plate, mat_brass, bevel_width=0.002, smooth_shade=True)
    frame_parts.append(butt_plate)

    # Checkering Ribs & Glowing Sigils on Stock
    for side_x in [-0.0165, 0.0165]:
        for ck_i in range(4):
            cky = -0.036 - ck_i * 0.012
            ckz = -0.028 - ck_i * 0.011
            bpy.ops.mesh.primitive_cube_add(
                size=1.0,
                location=(side_x, cky, ckz),
                rotation=(math.radians(-22.0), 0.0, 0.0),
            )
            ck_rib = bpy.context.active_object
            ck_rib.name = f"StockCheckering_{'L' if side_x < 0 else 'R'}_{ck_i}"
            ck_rib.scale = (0.0018, 0.004, 0.032)
            finalize_part(ck_rib, mat_brass, bevel_width=0.0004, smooth_shade=True)
            frame_parts.append(ck_rib)

            bpy.ops.mesh.primitive_cube_add(
                size=1.0,
                location=(side_x * 1.02, cky + 0.004, ckz),
                rotation=(math.radians(-22.0), 0.0, 0.0),
            )
            st_rune = bpy.context.active_object
            st_rune.name = f"StockRuneInlay_{'L' if side_x < 0 else 'R'}_{ck_i}"
            st_rune.scale = (0.0014, 0.010, 0.004)
            finalize_part(st_rune, mat_rune, bevel_width=0.0003, smooth_shade=False)
            frame_parts.append(st_rune)

    # Heavy Break-Action Standing Breech & Water-Table Receiver
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0.0, -0.002, 0.016),
    )
    breech = bpy.context.active_object
    breech.name = "StandingBreechBlock"
    breech.scale = (0.044, 0.036, 0.042)
    finalize_part(breech, mat_blued, bevel_width=0.003, smooth_shade=True)
    frame_parts.append(breech)

    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0.0, 0.030, -0.001),
    )
    water_table = bpy.context.active_object
    water_table.name = "ReceiverWaterTable"
    water_table.scale = (0.042, 0.064, 0.016)
    finalize_part(water_table, mat_blued, bevel_width=0.0025, smooth_shade=True)
    frame_parts.append(water_table)

    # Front Lower Hinge Pin Knuckle at (0, 0.055, -0.002)
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=14,
        radius=0.0075,
        depth=0.046,
        location=(0.0, 0.055, -0.002),
        rotation=(0.0, math.radians(90.0), 0.0),
    )
    hinge_pin = bpy.context.active_object
    hinge_pin.name = "ShotgunHingePin"
    finalize_part(hinge_pin, mat_brass, bevel_width=0.001, smooth_shade=True)
    frame_parts.append(hinge_pin)

    # Dual Curved Triggers + Trigger Guard Bow + Tang Safety Slide
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.022,
        minor_radius=0.0035,
        major_segments=18,
        minor_segments=8,
        location=(0.0, -0.006, -0.024),
        rotation=(0.0, math.radians(90.0), 0.0),
    )
    t_guard = bpy.context.active_object
    t_guard.name = "ShotgunTriggerGuard"
    t_guard.scale = (1.0, 1.35, 0.75)
    finalize_part(t_guard, mat_brass, bevel_width=0.0, smooth_shade=True)
    frame_parts.append(t_guard)

    for tr_i, ty_off in enumerate([0.002, -0.010]):
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(0.003 if tr_i == 0 else -0.003, ty_off, -0.022),
            rotation=(math.radians(-18.0), 0.0, 0.0),
        )
        trig = bpy.context.active_object
        trig.name = f"DualTrigger_{tr_i}"
        trig.scale = (0.0045, 0.008, 0.020)
        finalize_part(trig, mat_brass, bevel_width=0.0008, smooth_shade=True)
        frame_parts.append(trig)

    # Engraved Gothic Sideplate Filigree & Receiver Rivets
    frame_parts.extend(spawn_gothic_filigree("ShotgunLeftSide", -0.0225, 0.006, 0.010, mat_brass, mat_rune))
    frame_parts.extend(spawn_gothic_filigree("ShotgunRightSide", 0.0225, 0.006, 0.010, mat_brass, mat_rune))

    rec_rivet_pts: list[tuple[float, float, float]] = []
    for sx in [-0.0228, 0.0228]:
        for ry in [-0.012, 0.002, 0.016, 0.032]:
            rec_rivet_pts.append((sx, ry, 0.002))
            rec_rivet_pts.append((sx, ry, 0.022))
    frame_parts.extend(spawn_rivet_line("ShotgunReceiver", rec_rivet_pts, 0.0020, mat_brass))

    root_shotgun = join_into_hierarchy_node("ShotgunFrame", frame_parts, pivot_loc=(0.0, 0.0, 0.0))

    # ------------------------------------------------------------------
    # NODE 2: BarrelAssembly (Pivoted at Front Lower Hinge Pin (0, 0.055, -0.002))
    # ------------------------------------------------------------------
    hinge_pivot = (0.0, 0.055, -0.002)
    barrel_parts: list[bpy.types.Object] = []

    barrel_len: float = 0.34
    barrel_y_center: float = 0.018 + barrel_len * 0.5
    barrel_z: float = 0.022

    # Twin Side-by-Side Heavy Damascus/Blued-Steel Barrels + Deeply Bored Muzzles
    for b_idx, bx in enumerate([-0.0135, 0.0135]):
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=18,
            radius=0.0132,
            depth=barrel_len,
            location=(bx, barrel_y_center, barrel_z),
            rotation=(math.radians(90.0), 0.0, 0.0),
        )
        b_tube = bpy.context.active_object
        b_tube.name = f"ShotgunBarrelTube_{b_idx}"
        finalize_part(b_tube, mat_blued, bevel_width=0.0012, smooth_shade=True)
        barrel_parts.append(b_tube)

        # Heavy Muzzle Crown Collar & Dark Bore Recess
        bpy.ops.mesh.primitive_torus_add(
            major_radius=0.0134,
            minor_radius=0.0022,
            major_segments=18,
            minor_segments=8,
            location=(bx, 0.018 + barrel_len, barrel_z),
            rotation=(math.radians(90.0), 0.0, 0.0),
        )
        crown = bpy.context.active_object
        crown.name = f"BarrelMuzzleCrown_{b_idx}"
        finalize_part(crown, mat_brass, bevel_width=0.0, smooth_shade=True)
        barrel_parts.append(crown)

        bpy.ops.mesh.primitive_cylinder_add(
            vertices=16,
            radius=0.0102,
            depth=0.016,
            location=(bx, 0.018 + barrel_len - 0.006, barrel_z),
            rotation=(math.radians(90.0), 0.0, 0.0),
        )
        bore = bpy.context.active_object
        bore.name = f"BarrelDarkBore_{b_idx}"
        finalize_part(bore, mat_bore, bevel_width=0.0, smooth_shade=False)
        barrel_parts.append(bore)

        # Twin Brass Front Bead Sights
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=10,
            ring_count=8,
            radius=0.0032,
            location=(bx * 0.85, 0.018 + barrel_len - 0.012, barrel_z + 0.015),
        )
        bead = bpy.context.active_object
        bead.name = f"FrontBeadSight_{b_idx}"
        finalize_part(bead, mat_brass, bevel_width=0.0, smooth_shade=True)
        barrel_parts.append(bead)

    # Full-Length Raised Ventilated Top Rib + 7 Vent Stanchion Posts + Glowing Center Rune Strip
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0.0, barrel_y_center, barrel_z + 0.0145),
    )
    top_rib = bpy.context.active_object
    top_rib.name = "VentilatedTopRib"
    top_rib.scale = (0.012, barrel_len * 0.96, 0.0035)
    finalize_part(top_rib, mat_blued, bevel_width=0.0008, smooth_shade=True)
    barrel_parts.append(top_rib)

    for vp_i in range(7):
        vpy = 0.036 + vp_i * 0.048
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(0.0, vpy, barrel_z + 0.010),
        )
        v_post = bpy.context.active_object
        v_post.name = f"RibVentPost_{vp_i}"
        v_post.scale = (0.010, 0.012, 0.006)
        finalize_part(v_post, mat_brass, bevel_width=0.0005, smooth_shade=True)
        barrel_parts.append(v_post)

        # Glowing Occult Rune Segment along both barrels
        for side_s in [-1.0, 1.0]:
            bpy.ops.mesh.primitive_cube_add(
                size=1.0,
                location=(side_s * 0.0255, vpy, barrel_z + 0.002),
            )
            b_rune = bpy.context.active_object
            b_rune.name = f"BarrelSideRune_{vp_i}_{'L' if side_s < 0 else 'R'}"
            b_rune.scale = (0.0018, 0.024, 0.0032)
            finalize_part(b_rune, mat_rune, bevel_width=0.0003, smooth_shade=False)
            barrel_parts.append(b_rune)

    # 3 Heavy Reinforced Brass Barrel Clamps
    for cl_i, cly in enumerate([0.085, 0.195, 0.305]):
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(0.0, cly, barrel_z),
        )
        clamp = bpy.context.active_object
        clamp.name = f"BrassBarrelClamp_{cl_i}"
        clamp.scale = (0.056, 0.016, 0.029)
        finalize_part(clamp, mat_brass, bevel_width=0.0015, smooth_shade=True)
        barrel_parts.append(clamp)

    # Under-Barrel Walnut Splinter Forend Grip + Recessed Glowing Occult Runes
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0.0, 0.145, 0.003),
    )
    forend = bpy.context.active_object
    forend.name = "WalnutSplinterForend"
    forend.scale = (0.044, 0.155, 0.022)
    finalize_part(forend, mat_walnut, bevel_width=0.0035, smooth_shade=True)
    barrel_parts.append(forend)

    for fr_i in range(4):
        fry = 0.092 + fr_i * 0.034
        for sx in [-0.0225, 0.0225]:
            bpy.ops.mesh.primitive_cube_add(
                size=1.0,
                location=(sx, fry, 0.003),
            )
            fr_rune = bpy.context.active_object
            fr_rune.name = f"ForendRuneInlay_{fr_i}_{'L' if sx < 0 else 'R'}"
            fr_rune.scale = (0.0016, 0.020, 0.005)
            finalize_part(fr_rune, mat_rune, bevel_width=0.0003, smooth_shade=False)
            barrel_parts.append(fr_rune)

    barrel_node = join_into_hierarchy_node(
        "BarrelAssembly",
        barrel_parts,
        pivot_loc=hinge_pivot,
        parent_obj=root_shotgun,
    )

    # ------------------------------------------------------------------
    # NODES 2A & 2B: ShellLeft & ShellRight (Pivoted at Rear Breech inside BarrelAssembly)
    # ------------------------------------------------------------------
    for sh_idx, (sh_name, sh_x) in enumerate([("ShellLeft", -0.0135), ("ShellRight", 0.0135)]):
        sh_pivot = (sh_x, 0.018, barrel_z)
        sh_parts: list[bpy.types.Object] = spawn_cartridge_assembly(
            sh_idx,
            sh_x,
            barrel_z,
            0.044,
            mat_brass,
            mat_silver,
            mat_rune,
        )
        for sp in sh_parts:
            sp.location.y += 0.038
        join_into_hierarchy_node(sh_name, sh_parts, pivot_loc=sh_pivot, parent_obj=barrel_node)

    # ------------------------------------------------------------------
    # NODES 3 & 4: HammerLeft & HammerRight (Twin Rabbit-Ear Gothic Hammers)
    # ------------------------------------------------------------------
    for hm_name, hmx in [("HammerLeft", -0.0135), ("HammerRight", 0.0135)]:
        hm_pivot = (hmx, -0.016, 0.032)
        hm_parts: list[bpy.types.Object] = []
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(hmx, -0.024, 0.045),
            rotation=(math.radians(-22.0), 0.0, 0.0),
        )
        hm_body = bpy.context.active_object
        hm_body.name = f"{hm_name}_Body"
        hm_body.scale = (0.006, 0.016, 0.028)
        finalize_part(hm_body, mat_blued, bevel_width=0.0012, smooth_shade=True)
        hm_parts.append(hm_body)

        bpy.ops.mesh.primitive_cylinder_add(
            vertices=10,
            radius=0.005,
            depth=0.009,
            location=(hmx, -0.034, 0.056),
            rotation=(0.0, math.radians(90.0), 0.0),
        )
        hm_spur = bpy.context.active_object
        hm_spur.name = f"{hm_name}_Spur"
        finalize_part(hm_spur, mat_brass, bevel_width=0.0006, smooth_shade=True)
        hm_parts.append(hm_spur)

        join_into_hierarchy_node(hm_name, hm_parts, pivot_loc=hm_pivot, parent_obj=root_shotgun)

    # ------------------------------------------------------------------
    # NODE 5: TopLever (Break-Action Thumb Lever at (0, -0.010, 0.038))
    # ------------------------------------------------------------------
    lever_pivot = (0.0, -0.010, 0.038)
    lv_parts: list[bpy.types.Object] = []
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0.0, -0.022, 0.040),
    )
    lv_arm = bpy.context.active_object
    lv_arm.name = "TopLeverArm"
    lv_arm.scale = (0.008, 0.026, 0.005)
    finalize_part(lv_arm, mat_brass, bevel_width=0.0008, smooth_shade=True)
    lv_parts.append(lv_arm)

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=12,
        radius=0.0065,
        depth=0.006,
        location=(0.004, -0.034, 0.040),
    )
    lv_thumb = bpy.context.active_object
    lv_thumb.name = "TopLeverThumbPaddle"
    finalize_part(lv_thumb, mat_brass, bevel_width=0.0008, smooth_shade=True)
    lv_parts.append(lv_thumb)

    join_into_hierarchy_node("TopLever", lv_parts, pivot_loc=lever_pivot, parent_obj=root_shotgun)

    os.makedirs("assets/models/weapons", exist_ok=True)
    export_path = os.path.abspath("assets/models/weapons/viewmodel_right_shotgun.glb")
    bpy.ops.export_scene.gltf(
        filepath=export_path,
        export_format='GLB',
        use_selection=False,
        export_apply=False,
        export_all_vertex_colors=True,
        export_active_vertex_color_when_no_material=True,
    )
    print(f"[Blender] Exported Right Shotgun Viewmodel: {export_path}")


# ==============================================================================
# 4. RIGHT VIEWMODEL: CLOCKWORK PNEUMATIC STAKE-DRIVER & CLEAVER (145+ SUB-COMPONENTS)
# ==============================================================================

def build_viewmodel_right_stakedriver() -> None:
    """
    Builds the 145+ sub-component Clockwork Pneumatic Stake-Driver & Ritual Cleaver oriented so
    Blender +Y -> Godot -Z (Forward) and Blender +Z -> Godot +Y (Up).
    Joined into clean mechanical hierarchy nodes:
      DriverFrame (root)
        ├── StakeRam (sliding along longitudinal barrel axis at (0, 0.14, 0.026))
        ├── FlywheelGear (spinning on left side of receiver at (-0.024, 0.045, 0.016))
        └── LoadingCrank (pivoted on right side of receiver at (0.024, 0.025, 0.016))
    """
    clear_scene()

    mat_blued = make_pbr_material("BluedSteel", (0.10, 0.11, 0.13, 1.0), roughness=0.42, metallic=0.88)
    mat_brass = make_pbr_material("TarnishedBrass", (0.46, 0.36, 0.18, 1.0), roughness=0.48, metallic=0.85)
    mat_silver = make_pbr_material("OccultSilver", (0.58, 0.60, 0.64, 1.0), roughness=0.36, metallic=0.92)
    mat_walnut = make_pbr_material("DarkOiledWalnut", (0.14, 0.08, 0.045, 1.0), roughness=0.82)
    mat_leather = make_pbr_material("WeatheredLeather", (0.12, 0.085, 0.065, 1.0), roughness=0.86)
    mat_steel_plate = make_pbr_material("GothicPlateSteel", (0.18, 0.19, 0.21, 1.0), roughness=0.42, metallic=0.88)
    mat_bone = make_pbr_material("AgedBone", (0.56, 0.51, 0.42, 1.0), roughness=0.84, metallic=0.0)
    mat_steam = make_pbr_material(
        "EmissiveAmberFlame",
        (1.0, 0.62, 0.18, 1.0),
        roughness=0.18,
        emission_color=(1.0, 0.55, 0.14, 1.0),
        emission_strength=3.6,
    )
    mat_rune = make_pbr_material(
        "GlowingOccultRune",
        (0.95, 0.18, 0.32, 1.0),
        roughness=0.28,
        emission_color=(1.0, 0.14, 0.28, 1.0),
        emission_strength=3.4,
    )

    # ------------------------------------------------------------------
    # NODE 1: DriverFrame (Right Gauntlet + Pneumatic Chassis + Steam Gauge + Cleaver Blade)
    # ------------------------------------------------------------------
    driver_parts: list[bpy.types.Object] = build_detailed_arm_gauntlet(
        "RightHandDriver",
        is_left=False,
        z_offset=0.0,
        mat_leather=mat_leather,
        mat_steel=mat_steel_plate,
        mat_brass=mat_brass,
    )

    # Heavy Rear Recoil Grip & Industrial Gothic Iron/Brass Receiver Chassis
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0.0, -0.044, -0.048),
        rotation=(math.radians(-20.0), 0.0, 0.0),
    )
    d_grip = bpy.context.active_object
    d_grip.name = "DriverHeavyGrip"
    d_grip.scale = (0.030, 0.048, 0.092)
    finalize_part(d_grip, mat_walnut, bevel_width=0.0035, smooth_shade=True)
    driver_parts.append(d_grip)

    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0.0, 0.095, 0.010),
    )
    chassis = bpy.context.active_object
    chassis.name = "PneumaticDriverChassis"
    chassis.scale = (0.042, 0.26, 0.036)
    finalize_part(chassis, mat_blued, bevel_width=0.003, smooth_shade=True)
    driver_parts.append(chassis)

    # Open Top Rail Track Guides (6 Gothic Arch Guide Ribs + 12 Glowing Rune Strips)
    for rg_i in range(6):
        rgy = 0.005 + rg_i * 0.042
        for sx in [-0.017, 0.017]:
            bpy.ops.mesh.primitive_cube_add(
                size=1.0,
                location=(sx, rgy, 0.032),
            )
            rail_rib = bpy.context.active_object
            rail_rib.name = f"RailGuideRib_{rg_i}_{'L' if sx < 0 else 'R'}"
            rail_rib.scale = (0.006, 0.018, 0.016)
            finalize_part(rail_rib, mat_brass, bevel_width=0.001, smooth_shade=True)
            driver_parts.append(rail_rib)

            bpy.ops.mesh.primitive_cube_add(
                size=1.0,
                location=(sx * 1.15, rgy, 0.014),
            )
            ch_rune = bpy.context.active_object
            ch_rune.name = f"DriverChassisRune_{rg_i}_{'L' if sx < 0 else 'R'}"
            ch_rune.scale = (0.0018, 0.024, 0.0045)
            finalize_part(ch_rune, mat_rune, bevel_width=0.0003, smooth_shade=False)
            driver_parts.append(ch_rune)

    # Side-Mounted Pressurized Alchemical Steam Cylinder (EmissiveAmberFlame Glass Gauge + Brass Cage)
    steam_x: float = -0.028
    steam_y: float = 0.145
    steam_z: float = 0.008
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16,
        radius=0.0105,
        depth=0.115,
        location=(steam_x, steam_y, steam_z),
        rotation=(math.radians(90.0), 0.0, 0.0),
    )
    steam_core = bpy.context.active_object
    steam_core.name = "AlchemicalSteamGaugeCore"
    finalize_part(steam_core, mat_steam, bevel_width=0.0008, smooth_shade=True)
    driver_parts.append(steam_core)

    for cap_y in [steam_y - 0.060, steam_y + 0.060]:
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=16,
            radius=0.013,
            depth=0.012,
            location=(steam_x, cap_y, steam_z),
            rotation=(math.radians(90.0), 0.0, 0.0),
        )
        s_cap = bpy.context.active_object
        s_cap.name = f"SteamCap_{'Rear' if cap_y < steam_y else 'Front'}"
        finalize_part(s_cap, mat_brass, bevel_width=0.001, smooth_shade=True)
        driver_parts.append(s_cap)

    # 3 Braided Copper/Brass Pressure Pipes & 16 Chassis Rivets
    for pp_i, pp_z in enumerate([-0.006, 0.004, 0.022]):
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=10,
            radius=0.0032,
            depth=0.18,
            location=(-0.023, 0.085, pp_z),
            rotation=(math.radians(90.0), 0.0, 0.0),
        )
        pipe = bpy.context.active_object
        pipe.name = f"BrassPressurePipe_{pp_i}"
        finalize_part(pipe, mat_brass, bevel_width=0.0005, smooth_shade=True)
        driver_parts.append(pipe)

    drv_rivets: list[tuple[float, float, float]] = []
    for r_i in range(8):
        ry = -0.015 + r_i * 0.030
        drv_rivets.append((-0.0215, ry, -0.002))
        drv_rivets.append((0.0215, ry, -0.002))
    driver_parts.extend(spawn_rivet_line("DriverChassis", drv_rivets, 0.0022, mat_brass))

    # Serrated Lower Ritual Cleaver Bayonet Blade (AgedBone Spine + OccultSilver Edge + Glowing Runes)
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0.0, 0.225, -0.022),
    )
    cleaver_blade = bpy.context.active_object
    cleaver_blade.name = "RitualCleaverBlade"
    cleaver_blade.scale = (0.007, 0.22, 0.036)
    finalize_part(cleaver_blade, mat_silver, bevel_width=0.0012, smooth_shade=True)
    driver_parts.append(cleaver_blade)

    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0.0, 0.215, -0.006),
    )
    cleaver_spine = bpy.context.active_object
    cleaver_spine.name = "CleaverAgedBoneSpine"
    cleaver_spine.scale = (0.011, 0.20, 0.010)
    finalize_part(cleaver_spine, mat_bone, bevel_width=0.0015, smooth_shade=True)
    driver_parts.append(cleaver_spine)

    # 7 Serrated Cleaver Saw-Teeth + Glowing Blood-Rune Fuller Channel
    for st_i in range(7):
        sty = 0.135 + st_i * 0.026
        bpy.ops.mesh.primitive_cone_add(
            vertices=4,
            radius1=0.008,
            radius2=0.001,
            depth=0.016,
            location=(0.0, sty, -0.044),
            rotation=(math.radians(155.0), 0.0, math.radians(45.0)),
        )
        tooth = bpy.context.active_object
        tooth.name = f"CleaverSawTooth_{st_i}"
        finalize_part(tooth, mat_silver, bevel_width=0.0005, smooth_shade=False)
        driver_parts.append(tooth)

    for side_x in [-0.0042, 0.0042]:
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(side_x, 0.225, -0.020),
        )
        cl_rune = bpy.context.active_object
        cl_rune.name = f"CleaverFullerRune_{'L' if side_x < 0 else 'R'}"
        cl_rune.scale = (0.0015, 0.175, 0.0045)
        finalize_part(cl_rune, mat_rune, bevel_width=0.0003, smooth_shade=False)
        driver_parts.append(cl_rune)

    root_driver = join_into_hierarchy_node("DriverFrame", driver_parts, pivot_loc=(0.0, 0.0, 0.0))

    # ------------------------------------------------------------------
    # NODE 2: StakeRam (Sliding Fluted Octagonal Silver Stake Piston at (0, 0.14, 0.026))
    # ------------------------------------------------------------------
    ram_pivot = (0.0, 0.14, 0.026)
    ram_parts: list[bpy.types.Object] = []

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=8,
        radius=0.0115,
        depth=0.22,
        location=(0.0, 0.14, 0.026),
        rotation=(math.radians(90.0), 0.0, 0.0),
    )
    ram_shaft = bpy.context.active_object
    ram_shaft.name = "OctagonalStakeShaft"
    finalize_part(ram_shaft, mat_silver, bevel_width=0.0012, smooth_shade=True)
    ram_parts.append(ram_shaft)

    bpy.ops.mesh.primitive_cone_add(
        vertices=8,
        radius1=0.0125,
        radius2=0.0012,
        depth=0.075,
        location=(0.0, 0.285, 0.026),
        rotation=(math.radians(-90.0), 0.0, 0.0),
    )
    ram_tip = bpy.context.active_object
    ram_tip.name = "HeavySilverStakePoint"
    finalize_part(ram_tip, mat_silver, bevel_width=0.001, smooth_shade=True)
    ram_parts.append(ram_tip)

    # Glowing Rune Grooves & 6 Return Spring Coils on StakeRam
    for sr_i in range(4):
        s_ang = sr_i * (math.pi * 0.5)
        srx = math.cos(s_ang) * 0.0112
        srz = 0.026 + math.sin(s_ang) * 0.0112
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(srx, 0.165, srz),
            rotation=(0.0, s_ang, 0.0),
        )
        s_rune = bpy.context.active_object
        s_rune.name = f"StakeRamRuneStrip_{sr_i}"
        s_rune.scale = (0.0022, 0.16, 0.0022)
        finalize_part(s_rune, mat_rune, bevel_width=0.0003, smooth_shade=False)
        ram_parts.append(s_rune)

    for sp_i in range(6):
        spy = 0.055 + sp_i * 0.016
        bpy.ops.mesh.primitive_torus_add(
            major_radius=0.0145,
            minor_radius=0.0022,
            major_segments=14,
            minor_segments=6,
            location=(0.0, spy, 0.026),
            rotation=(math.radians(84.0), 0.0, 0.0),
        )
        coil = bpy.context.active_object
        coil.name = f"RamReturnCoil_{sp_i}"
        finalize_part(coil, mat_brass, bevel_width=0.0, smooth_shade=True)
        ram_parts.append(coil)

    join_into_hierarchy_node("StakeRam", ram_parts, pivot_loc=ram_pivot, parent_obj=root_driver)

    # ------------------------------------------------------------------
    # NODE 3: FlywheelGear (Exposed 12-Tooth Brass Clockwork Flywheel at (-0.024, 0.032, 0.016))
    # ------------------------------------------------------------------
    flywheel_pivot = (-0.024, 0.032, 0.016)
    fw_parts: list[bpy.types.Object] = []

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=20,
        radius=0.022,
        depth=0.006,
        location=flywheel_pivot,
        rotation=(0.0, math.radians(90.0), 0.0),
    )
    fw_rim = bpy.context.active_object
    fw_rim.name = "FlywheelRim"
    finalize_part(fw_rim, mat_brass, bevel_width=0.0008, smooth_shade=True)
    fw_parts.append(fw_rim)

    for ft_i in range(12):
        ft_ang = ft_i * (math.tau / 12.0)
        fy = flywheel_pivot[1] + math.cos(ft_ang) * 0.0225
        fz = flywheel_pivot[2] + math.sin(ft_ang) * 0.0225
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(flywheel_pivot[0], fy, fz),
            rotation=(ft_ang, 0.0, 0.0),
        )
        f_tooth = bpy.context.active_object
        f_tooth.name = f"FlywheelTooth_{ft_i}"
        f_tooth.scale = (0.0055, 0.0045, 0.0055)
        finalize_part(f_tooth, mat_brass, bevel_width=0.0004, smooth_shade=True)
        fw_parts.append(f_tooth)

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=12,
        radius=0.0065,
        depth=0.009,
        location=flywheel_pivot,
        rotation=(0.0, math.radians(90.0), 0.0),
    )
    fw_hub = bpy.context.active_object
    fw_hub.name = "FlywheelRuneHub"
    finalize_part(fw_hub, mat_rune, bevel_width=0.0005, smooth_shade=True)
    fw_parts.append(fw_hub)

    join_into_hierarchy_node("FlywheelGear", fw_parts, pivot_loc=flywheel_pivot, parent_obj=root_driver)

    # ------------------------------------------------------------------
    # NODE 4: LoadingCrank (Winding Crank Handle on Right Receiver at (0.024, 0.025, 0.016))
    # ------------------------------------------------------------------
    crank_pivot = (0.024, 0.025, 0.016)
    ck_parts: list[bpy.types.Object] = []

    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0.026, 0.025, 0.030),
    )
    ck_arm = bpy.context.active_object
    ck_arm.name = "LoadingCrankArm"
    ck_arm.scale = (0.005, 0.008, 0.032)
    finalize_part(ck_arm, mat_brass, bevel_width=0.0008, smooth_shade=True)
    ck_parts.append(ck_arm)

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=12,
        radius=0.0055,
        depth=0.018,
        location=(0.034, 0.025, 0.042),
        rotation=(0.0, math.radians(90.0), 0.0),
    )
    ck_knob = bpy.context.active_object
    ck_knob.name = "LoadingCrankKnob"
    finalize_part(ck_knob, mat_walnut, bevel_width=0.0008, smooth_shade=True)
    ck_parts.append(ck_knob)

    join_into_hierarchy_node("LoadingCrank", ck_parts, pivot_loc=crank_pivot, parent_obj=root_driver)

    os.makedirs("assets/models/weapons", exist_ok=True)
    export_path = os.path.abspath("assets/models/weapons/viewmodel_right_stakedriver.glb")
    bpy.ops.export_scene.gltf(
        filepath=export_path,
        export_format='GLB',
        use_selection=False,
        export_apply=False,
        export_all_vertex_colors=True,
        export_active_vertex_color_when_no_material=True,
    )
    print(f"[Blender] Exported Right StakeDriver Viewmodel: {export_path}")


if __name__ == "__main__":
    build_viewmodel_left_lantern()
    build_viewmodel_right_revolver()
    build_viewmodel_right_shotgun()
    build_viewmodel_right_stakedriver()
