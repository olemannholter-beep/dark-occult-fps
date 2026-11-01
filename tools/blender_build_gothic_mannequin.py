import bpy
import math
import os
import sys
from mathutils import Vector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from blender_micro_voxel_kit import MicroVoxelBuilder, make_micro_voxel_materials

OUTPUT_GLB = os.path.abspath(
    os.path.join(SCRIPT_DIR, "..", "assets", "models", "armor", "gothic_arming_mannequin.glb")
)
OUTPUT_BLEND = os.path.abspath(
    os.path.join(SCRIPT_DIR, "..", ".mcp_captures", "gothic_arming_mannequin_template.blend")
)
VOXEL_SIZE = 0.016


def clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def interp_profile(z: float, profile: list[tuple[float, float, float]]) -> tuple[float, float]:
    if z <= profile[0][0]:
        return profile[0][1], profile[0][2]
    if z >= profile[-1][0]:
        return profile[-1][1], profile[-1][2]
    for i in range(len(profile) - 1):
        z0, rx0, ry0 = profile[i]
        z1, rx1, ry1 = profile[i + 1]
        if z0 <= z <= z1:
            t = (z - z0) / max(1e-6, z1 - z0)
            return rx0 + (rx1 - rx0) * t, ry0 + (ry1 - ry0) * t
    return profile[-1][1], profile[-1][2]


def build_stand_base(vox: MicroVoxelBuilder) -> None:
    """1. Wrought-Iron Tailor's Stand Base (Z = 0.00m..0.84m)."""
    s = vox.voxel_size
    # Stepped octagonal pedestal base (Z = 0.00..0.10m)
    for iy in range(0, int(round(0.10 / s)) + 1):
        wz = (iy + 0.5) * s
        rad = 0.19 - (wz / 0.10) * 0.09
        ir = int(math.ceil(rad / s)) + 1
        is_brass_ring = iy in (1, 5)
        for ix in range(-ir, ir + 1):
            for iz in range(-ir, ir + 1):
                wx, wy, _ = vox.get_world_center(ix, iy, iz)
                d_oct = max(abs(wx), abs(wy), (abs(wx) + abs(wy)) * 0.72)
                if d_oct <= rad:
                    mat = 2 if (is_brass_ring and d_oct >= rad - s * 1.3) else 0
                    vox.set_voxel(ix, iy, iz, mat, 0.94, 0.52)

    # 4 Scrolled Wrought-Iron Quad-Legs
    for leg_i in range(4):
        ang = leg_i * (math.pi * 0.5) + math.pi * 0.25
        dx, dy = math.cos(ang), math.sin(ang)
        for step in range(16):
            t = step / 15.0
            r_dist = 0.04 + t * 0.18
            lx = dx * r_dist
            ly = dy * r_dist
            lz = 0.09 * (1.0 - t * 0.75) + math.sin(t * math.pi) * 0.022
            for dz_off in (-s, 0.0, s):
                vox.set_world_voxel(lx, ly, max(0.008, lz + dz_off), 0, 0.92, 0.48)
            if step in (4, 11, 15):
                vox.set_world_voxel(lx, ly, lz + s * 1.5, 2, 1.02, 0.65)

    # Central iron finial post (Z = 0.10..0.84m) with brass collar rings
    for iy in range(int(round(0.10 / s)), int(round(0.84 / s)) + 1):
        wz = (iy + 0.5) * s
        is_collar = abs(wz - 0.28) < 0.018 or abs(wz - 0.54) < 0.018 or abs(wz - 0.78) < 0.018
        rad = 0.036 if is_collar else 0.026
        ir = int(math.ceil(rad / s)) + 1
        for ix in range(-ir, ir + 1):
            for iz in range(-ir, ir + 1):
                wx, wy, _ = vox.get_world_center(ix, iy, iz)
                if math.hypot(wx, wy) <= rad:
                    vox.set_voxel(ix, iy, iz, 2 if is_collar else 0, 0.96, 0.58 if is_collar else 0.48)


def build_quilted_torso(vox: MicroVoxelBuilder) -> None:
    """2. Anatomical Diamond-Quilted Arming Doublet Torso (Z = 0.82m..1.48m)."""
    s = vox.voxel_size
    torso_profile = [
        (0.82, 0.140, 0.092),
        (0.86, 0.138, 0.090),
        (0.93, 0.118, 0.082),
        (1.00, 0.102, 0.076),
        (1.08, 0.118, 0.086),
        (1.16, 0.138, 0.098),
        (1.25, 0.154, 0.106),
        (1.32, 0.162, 0.108),
        (1.38, 0.148, 0.096),
        (1.42, 0.088, 0.078),
        (1.45, 0.066, 0.068),
        (1.48, 0.064, 0.066),
    ]
    iy_min = int(round(0.82 / s))
    iy_max = int(round(1.48 / s))
    for iy in range(iy_min, iy_max + 1):
        wz = (iy + 0.5) * s
        rx, ry = interp_profile(wz, torso_profile)
        cy = -0.005 * math.sin(((wz - 0.82) / 0.66) * math.pi)
        irx = int(math.ceil((rx + 0.03) / s)) + 1
        iry = int(math.ceil((ry + 0.03) / s)) + 1
        is_belt = 0.98 <= wz <= 1.035
        is_hem = wz <= 0.845
        for ix in range(-irx, irx + 1):
            for iz in range(-iry, iry + 1):
                wx, wy, _ = vox.get_world_center(ix, iy, iz)
                dy = wy - cy
                mod_ry = ry
                if 1.18 <= wz <= 1.35 and dy < -0.01:
                    pec = math.sin(((wz - 1.18) / 0.17) * math.pi)
                    mod_ry += 0.010 * pec * (0.4 + 0.6 * min(1.0, abs(wx) / 0.08))
                d_norm = math.sqrt((wx / max(1e-4, rx)) ** 2 + (dy / max(1e-4, mod_ry)) ** 2)
                quilt_cell = (ix + iy + iz) % 3 != 0
                quilt_pad = 0.055 if (quilt_cell and not is_belt) else 0.0
                if d_norm <= 1.0 + quilt_pad and d_norm >= 0.45:
                    if is_belt and d_norm >= 0.88:
                        mat = 2 if (abs(wz - 1.008) > 0.018 and (ix % 3 == 0)) else 1
                        vox.set_voxel(ix, iy, iz, mat, 0.95, 0.35 if mat == 1 else 0.68)
                    elif is_hem and d_norm >= 0.90 and (ix % 2 == 0):
                        vox.set_voxel(ix, iy, iz, 2, 1.0, 0.65)
                    else:
                        tint = 0.55 if quilt_cell else 0.42
                        bias = 1.01 if quilt_cell else 0.90
                        vox.set_voxel(ix, iy, iz, 1, bias, tint)
        iz_front = int(round((-(cy - ry - 0.008)) / s))
        vox.set_voxel(0, iy, iz_front, 0, 0.88, 0.42)
        if iy % 3 == 0 and 1.05 <= wz <= 1.40:
            vox.set_voxel(-1, iy, iz_front + 1, 2, 1.04, 0.72)
            vox.set_voxel(1, iy, iz_front + 1, 2, 1.04, 0.72)

    iy_belt = int(round(1.005 / s))
    iz_belt = int(round(0.088 / s))
    vox.add_3d_buckle(0, iy_belt, iz_belt, half_w=2, half_h=2, frame_mat=2, pin_mat=0)


def build_synod_death_mask(vox: MicroVoxelBuilder) -> None:
    """3. Chiseled Blackened-Iron Synod Death Mask (Z = 1.44m..1.74m)."""
    s = vox.voxel_size
    for iy in range(int(round(1.44 / s)), int(round(1.50 / s)) + 1):
        wz = (iy + 0.5) * s
        rx, ry = 0.074, 0.072
        for ix in range(-6, 7):
            for iz in range(-6, 7):
                wx, wy, _ = vox.get_world_center(ix, iy, iz)
                d = math.sqrt((wx / rx) ** 2 + (wy / ry) ** 2)
                if 0.65 <= d <= 1.05:
                    is_rim = iy == int(round(1.49 / s)) and (ix % 2 == 0)
                    vox.set_voxel(ix, iy, iz, 2 if is_rim else 1, 0.96, 0.65 if is_rim else 0.44)
    vox.add_3d_buckle(0, int(round(1.465 / s)), 5, half_w=1, half_h=1, frame_mat=2, pin_mat=0)

    iy_start = int(round(1.49 / s))
    iy_end = int(round(1.74 / s))
    for iy in range(iy_start, iy_end + 1):
        wz = (iy + 0.5) * s
        t = (wz - 1.49) / 0.25
        if t < 0.22:
            rx, ry = 0.056 + t * 0.055, 0.064 + t * 0.055
        elif t < 0.68:
            u = (t - 0.22) / 0.46
            rx = 0.068 + math.sin(u * math.pi) * 0.008
            ry = 0.076 + math.sin(u * math.pi) * 0.010
        else:
            u = (t - 0.68) / 0.32
            rx = 0.070 * math.cos(u * math.pi * 0.44)
            ry = 0.078 * math.cos(u * math.pi * 0.44)

        for ix in range(-6, 7):
            for iz in range(-6, 7):
                wx, wy, _ = vox.get_world_center(ix, iy, iz)
                d = math.sqrt((wx / max(0.018, rx)) ** 2 + (wy / max(0.020, ry)) ** 2)
                if d <= 1.0:
                    is_front_mask = iz >= 2 and 1.51 <= wz <= 1.70 and abs(ix) <= 4
                    tint = 0.65 if is_front_mask else 0.50
                    bias = 1.02 if is_front_mask else 0.92
                    vox.set_voxel(ix, iy, iz, 0, bias, tint)

    iy_eye_lo = int(round(1.60 / s))
    iy_eye_hi = int(round(1.635 / s))
    iy_nose_lo = int(round(1.565 / s))
    iy_brow = iy_eye_hi + 1

    for ix in range(-3, 4):
        vox.set_voxel(ix, iy_brow, 5, 0, 1.04, 0.72)
        if abs(ix) in (2, 3):
            vox.set_voxel(ix, iy_eye_lo - 1, 5, 0, 1.00, 0.66)

    for iy in range(iy_nose_lo, iy_brow + 1):
        vox.set_voxel(0, iy, 5, 0, 1.05, 0.74)
        if iy <= iy_eye_lo:
            vox.set_voxel(0, iy, 6, 0, 1.06, 0.76)

    for side in (-1, 1):
        ex = side * 2
        for iy in range(iy_eye_lo, iy_eye_hi + 1):
            for dx in (0, side):
                vox.carve_voxel(ex + dx, iy, 6)
                vox.carve_voxel(ex + dx, iy, 5)
                vox.carve_voxel(ex + dx, iy, 4)
            vox.set_voxel(ex, iy, 3, 3, 1.0, 0.85)
            vox.set_voxel(ex + side, iy, 3, 0, 0.60, 0.25)

        for ty in range(iy_eye_lo - 4, iy_eye_lo):
            vox.carve_voxel(ex, ty, 5)
            vox.set_voxel(ex, ty, 4, 0, 0.68, 0.30)

    iy_mouth = int(round(1.535 / s))
    for ix in (-1, 0, 1):
        vox.carve_voxel(ix, iy_mouth, 5)
        vox.set_voxel(ix, iy_mouth, 4, 0, 0.70, 0.32)


def build_limb_tube(
    vox: MicroVoxelBuilder,
    pts: list[tuple[Vector, float, float]],
    strap_ts: list[float],
    side_s: float,
) -> None:
    s = vox.voxel_size
    total_segs = len(pts) - 1
    for seg_i in range(total_segs):
        p0, rx0, ry0 = pts[seg_i]
        p1, rx1, ry1 = pts[seg_i + 1]
        steps = max(8, int(math.ceil((p1 - p0).length / (s * 0.45))))
        for st in range(steps + 1):
            f = st / float(steps)
            global_t = (seg_i + f) / float(total_segs)
            c = p0.lerp(p1, f)
            rx = rx0 + (rx1 - rx0) * f
            ry = ry0 + (ry1 - ry0) * f
            is_strap = any(abs(global_t - ts) < 0.045 for ts in strap_ts)
            ir = int(math.ceil(max(rx, ry) / s)) + 1
            c_ix = int(round(c.x / s))
            c_iy = int(round(c.z / s))
            c_iz = int(round(-c.y / s))
            for dx in range(-ir, ir + 1):
                for dy in range(-ir, ir + 1):
                    for dz in range(-1, 2):
                        ix, iy, iz = c_ix + dx, c_iy + dz, c_iz + dy
                        wx, wy, wz = vox.get_world_center(ix, iy, iz)
                        if abs(wz - c.z) > s * 0.95:
                            continue
                        d = math.sqrt(((wx - c.x) / max(1e-4, rx)) ** 2 + ((wy - c.y) / max(1e-4, ry)) ** 2)
                        quilt = (ix + iy + iz) % 3 != 0
                        pad = 0.06 if (quilt and not is_strap) else 0.0
                        if 0.45 <= d <= 1.0 + pad:
                            if is_strap and d >= 0.86:
                                is_buckle = dy >= ir - 2 and dx == 0
                                vox.set_voxel(ix, iy, iz, 2 if is_buckle else 0, 0.96, 0.65 if is_buckle else 0.46)
                            else:
                                vox.set_voxel(ix, iy, iz, 1, 1.0 if quilt else 0.90, 0.55 if quilt else 0.42)


def build_arms_and_hands(vox: MicroVoxelBuilder) -> None:
    """4. Deltoid Caps, Tapered Forearms & Articulated Micro-Voxel Gloved Hands (Left & Right)."""
    s = vox.voxel_size
    for side_s in (-1.0, 1.0):
        arm_pts = [
            (Vector((side_s * 0.175, 0.000, 1.37)), 0.062, 0.062),
            (Vector((side_s * 0.200, -0.005, 1.31)), 0.056, 0.056),
            (Vector((side_s * 0.225, -0.012, 1.24)), 0.050, 0.050),
            (Vector((side_s * 0.248, -0.028, 1.16)), 0.046, 0.046),
            (Vector((side_s * 0.265, -0.052, 1.09)), 0.041, 0.041),
            (Vector((side_s * 0.278, -0.075, 1.02)), 0.035, 0.035),
        ]
        build_limb_tube(vox, arm_pts, strap_ts=[0.55, 0.78, 0.95], side_s=side_s)

        # Articulated micro-voxel gloved palm at wrist (Z = 0.95..1.02m)
        wrist = Vector((side_s * 0.278, -0.075, 1.02))
        for step in range(10):
            t = step / 9.0
            pz = wrist.z - t * 0.068
            py = wrist.y - t * 0.016
            px = wrist.x + side_s * t * 0.006
            rx = 0.034 + math.sin(t * math.pi) * 0.006
            ry = 0.022 - t * 0.004
            for dx_i in range(-3, 4):
                for dy_i in range(-2, 3):
                    wx = px + dx_i * s * 0.65
                    wy = py + dy_i * s * 0.65
                    if ((wx - px) / rx) ** 2 + ((wy - py) / ry) ** 2 <= 1.05:
                        is_knuckle = step >= 8 and dy_i <= -1
                        vox.set_world_voxel(wx, wy, pz, 0 if is_knuckle else 1, 0.96, 0.52)

        # 4 Curled finger columns
        knuckle_z = wrist.z - 0.070
        for f_i in range(4):
            fx = wrist.x + side_s * 0.006 + (f_i - 1.5) * 0.014 * side_s
            fy = wrist.y - 0.016
            curr = Vector((fx, fy, knuckle_z))
            for ph_i in range(3):
                ang = math.radians(32.0 + ph_i * 36.0)
                seg_l = 0.020 - ph_i * 0.003
                nxt = curr + Vector((0.0, -math.sin(ang) * seg_l, -math.cos(ang) * seg_l))
                for k in range(4):
                    p = curr.lerp(nxt, k / 3.0)
                    vox.set_world_voxel(p.x, p.y, p.z, 0 if ph_i == 0 else 1, 0.94, 0.48)
                curr = nxt

        # Opposable thumb column
        th_curr = Vector((wrist.x - side_s * 0.026, wrist.y - 0.020, wrist.z - 0.034))
        for th_i in range(3):
            ang = math.radians(28.0 + th_i * 28.0)
            nxt = th_curr + Vector((side_s * 0.006, -math.sin(ang) * 0.017, -math.cos(ang) * 0.017))
            for k in range(4):
                p = th_curr.lerp(nxt, k / 3.0)
                vox.set_world_voxel(p.x, p.y, p.z, 1, 0.95, 0.50)
            th_curr = nxt


def build_legs(vox: MicroVoxelBuilder) -> None:
    """5. Quilted Thighs, Knees & Tapered Calves (Left & Right, Z = 0.14m..0.86m)."""
    for side_s in (-1.0, 1.0):
        leg_pts = [
            (Vector((side_s * 0.105, 0.000, 0.86)), 0.072, 0.074),
            (Vector((side_s * 0.112, -0.006, 0.72)), 0.064, 0.066),
            (Vector((side_s * 0.118, -0.010, 0.56)), 0.055, 0.057),
            (Vector((side_s * 0.122, -0.006, 0.42)), 0.052, 0.054),
            (Vector((side_s * 0.125, 0.000, 0.28)), 0.045, 0.047),
            (Vector((side_s * 0.128, 0.005, 0.14)), 0.038, 0.040),
        ]
        build_limb_tube(vox, leg_pts, strap_ts=[0.42, 0.56, 0.85], side_s=side_s)


def assign_anatomical_vertex_groups(obj: bpy.types.Object) -> None:
    """Assigns all 14 ZONE_* vertex groups for armor compatibility."""
    group_names = [
        "ZONE_HEAD",
        "ZONE_CHEST",
        "ZONE_PAULDRON_L", "ZONE_PAULDRON_R",
        "ZONE_VAMBRACE_L", "ZONE_VAMBRACE_R",
        "ZONE_GAUNTLET_HAND_L", "ZONE_GAUNTLET_HAND_R",
        "ZONE_CUISSE_L", "ZONE_CUISSE_R",
        "ZONE_GREAVE_L", "ZONE_GREAVE_R",
        "ZONE_SABATON_L", "ZONE_SABATON_R",
    ]
    vgroups = {name: obj.vertex_groups.new(name=name) for name in group_names}
    for v in obj.data.vertices:
        x, y, z = v.co.x, v.co.y, v.co.z
        side = "L" if x < 0.0 else "R"
        ax = abs(x)
        if z >= 1.46:
            vgroups["ZONE_HEAD"].add([v.index], 1.0, 'REPLACE')
        if 0.88 <= z <= 1.45 and ax <= 0.195:
            vgroups["ZONE_CHEST"].add([v.index], 1.0, 'REPLACE')
        if 1.24 <= z <= 1.44 and ax >= 0.145:
            vgroups[f"ZONE_PAULDRON_{side}"].add([v.index], 1.0, 'REPLACE')
        if 1.00 <= z <= 1.25 and ax >= 0.19:
            vgroups[f"ZONE_VAMBRACE_{side}"].add([v.index], 1.0, 'REPLACE')
        if 0.86 <= z <= 1.04 and ax >= 0.21:
            vgroups[f"ZONE_GAUNTLET_HAND_{side}"].add([v.index], 1.0, 'REPLACE')
        if 0.50 <= z <= 0.90 and ax >= 0.04:
            vgroups[f"ZONE_CUISSE_{side}"].add([v.index], 1.0, 'REPLACE')
        if 0.15 <= z <= 0.54 and ax >= 0.04:
            vgroups[f"ZONE_GREAVE_{side}"].add([v.index], 1.0, 'REPLACE')
        if 0.0 <= z <= 0.20 and ax >= 0.04:
            vgroups[f"ZONE_SABATON_{side}"].add([v.index], 1.0, 'REPLACE')


def build_gothic_arming_mannequin() -> None:
    clear_scene()
    os.makedirs(os.path.dirname(OUTPUT_GLB), exist_ok=True)
    mats = make_micro_voxel_materials(0)

    vox = MicroVoxelBuilder("GothicArmingMannequin", voxel_size=VOXEL_SIZE, origin=(0.0, 0.0, 0.0))
    build_stand_base(vox)
    build_quilted_torso(vox)
    build_synod_death_mask(vox)
    build_arms_and_hands(vox)
    build_legs(vox)

    obj = vox.build_mesh_object(mats)
    assign_anatomical_vertex_groups(obj)

    col_attr = obj.data.color_attributes.get("Col")
    if col_attr is not None:
        obj.data.color_attributes.active_color = col_attr
        obj.data.color_attributes.render_color_index = 0

    bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.export_scene.gltf(
            filepath=OUTPUT_GLB,
            export_format='GLB',
            use_selection=True,
            export_apply=True,
            export_yup=True,
            export_attributes=True,
            export_all_vertex_colors=True,
        )
    except TypeError:
        bpy.ops.export_scene.gltf(
            filepath=OUTPUT_GLB,
            export_format='GLB',
            use_selection=True,
            export_apply=True,
            export_yup=True,
            export_all_vertex_colors=True,
        )
    tri_count = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    print(
        f"[MicroVoxel Mannequin] Exported {OUTPUT_GLB} & {OUTPUT_BLEND} | "
        f"voxels={len(vox.voxels)} | tris={tri_count} | vgroups={len(obj.vertex_groups)}"
    )


if __name__ == "__main__":
    build_gothic_arming_mannequin()
