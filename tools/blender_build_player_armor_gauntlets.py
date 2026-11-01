import bpy
import math
import os
import sys
from mathutils import Vector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from blender_micro_voxel_kit import MicroVoxelBuilder, make_micro_voxel_materials

ARMOR_OUT_DIR = os.path.join(PROJECT_ROOT, "assets", "models", "armor")
VOXEL_SIZE = 0.009  # 9mm hero viewmodel micro-voxels


def clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def get_forearm_frame() -> tuple[Vector, Vector, float, Vector, Vector, Vector, float, float]:
    """
    Returns the exact first-person left-forearm frame:
      elbow_pt = Vector((-0.068, -0.115, 0.073))
      wrist_pt = Vector((-0.010, -0.028, 0.216))
    """
    elbow_pt = Vector((-0.068, -0.115, 0.073))
    wrist_pt = Vector((-0.010, -0.028, 0.216))
    axis = wrist_pt - elbow_pt
    arm_len = axis.length
    arm_dir = axis.normalized()
    quat = Vector((0.0, 0.0, 1.0)).rotation_difference(arm_dir)
    perp_x = (quat @ Vector((1.0, 0.0, 0.0))).normalized()
    perp_y = (quat @ Vector((0.0, 1.0, 0.0))).normalized()
    return elbow_pt, wrist_pt, arm_len, arm_dir, perp_x, perp_y, 0.046, 0.034


def carve_hollow_forearm_bore(vox: MicroVoxelBuilder) -> None:
    """Carves the hollow interior cylinder (r_inner = r_limb * 0.72) along the forearm vector."""
    elbow_pt, wrist_pt, arm_len, arm_dir, _, _, r_elbow, r_wrist = get_forearm_frame()

    def is_inside_bore(wx: float, wy: float, wz: float) -> bool:
        p = Vector((wx, wy, wz)) - elbow_pt
        proj = p.dot(arm_dir)
        if proj < -0.008 or proj > arm_len * 0.94:
            return False
        t = max(0.0, min(1.0, proj / arm_len))
        r_limb = r_elbow + (r_wrist - r_elbow) * t
        r_inner = r_limb * 0.72
        radial = (p - arm_dir * proj).length
        return radial < r_inner

    vox.enforce_inner_clearance(is_inside_bore)


def build_base_hollow_vambrace_and_hand(
    vox: MicroVoxelBuilder,
    plate_mat: int = 0,
    under_mat: int = 1,
    trim_mat: int = 2,
    finger_mat: int = 0,
    strap_ts: tuple[float, ...] = (0.22, 0.50, 0.78),
    lame_steps: int = 5,
    claw_tips: bool = False,
    heavy_box_fingers: bool = False,
) -> None:
    """
    Builds the hollow armored vambrace along elbow_pt -> wrist_pt, wrap-around straps with
    3D buckles, articulated wrist bridge, armored metacarpal hand, 5 curled fingers, and lantern bail.
    """
    elbow_pt, wrist_pt, arm_len, arm_dir, perp_x, perp_y, r_elbow, r_wrist = get_forearm_frame()
    s = vox.voxel_size

    # 1. Hollow Forearm Vambrace Shell with Stepped Lames & Trim Rings
    n_slices = 44
    for i in range(n_slices + 1):
        t = i / float(n_slices)
        center = elbow_pt.lerp(wrist_pt, t)
        r_limb = r_elbow + (r_wrist - r_elbow) * t
        r_inner = r_limb * 0.72
        lame_phase = (t * lame_steps) % 1.0
        shingle_boost = 0.0035 * (1.0 - lame_phase)
        is_lame_lip = lame_phase < 0.14
        is_strap = any(abs(t - st) < 0.045 for st in strap_ts)

        n_ang = 48
        for a_i in range(n_ang):
            ang = (a_i / float(n_ang)) * math.tau
            ca, sa = math.cos(ang), math.sin(ang)
            radial_dir = perp_x * ca + perp_y * sa
            flute = 0.0022 * math.cos(ang * 8.0) if sa > -0.2 else 0.0

            # Inner leather lining layer + outer armored plate layer
            for r_step in range(3):
                rf = r_inner + s * 0.45 + r_step * (s * 0.65)
                if r_step == 2:
                    rf = r_limb + shingle_boost + flute
                pt = center + radial_dir * rf
                if is_strap and r_step == 2:
                    vox.set_world_voxel(pt.x, pt.y, pt.z, 1, 0.94, 0.38)
                elif is_lame_lip and r_step == 2:
                    vox.set_world_voxel(pt.x, pt.y, pt.z, trim_mat, 1.03, 0.68)
                elif r_step == 0:
                    vox.set_world_voxel(pt.x, pt.y, pt.z, under_mat, 0.86, 0.40)
                else:
                    # Dorsal plate vs ventral leather/plate
                    mat = plate_mat if (sa > -0.35 or plate_mat == 1) else under_mat
                    vox.set_world_voxel(pt.x, pt.y, pt.z, mat, 0.98, 0.54)

        # 3D Pin-Buckles on underside (-perp_y) for each strap
        for st in strap_ts:
            if abs(t - st) < 0.012:
                b_center = center - perp_y * (r_limb + 0.006)
                for dx in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        bp = b_center + perp_x * (dx * s) + arm_dir * (dz * s)
                        is_frame = abs(dx) == 1 or abs(dz) == 1
                        vox.set_world_voxel(bp.x, bp.y, bp.z, 2 if is_frame else 0, 1.04, 0.72)

    # 2. Articulated Metacarpal Hand Shell & Leather Palm (Z = 0.214..0.252)
    for hz_i in range(12):
        ht = hz_i / 11.0
        hc = wrist_pt.lerp(Vector((-0.006, -0.010, 0.246)), ht)
        rx = 0.026 + math.sin(ht * math.pi) * 0.005
        ry = 0.018
        for dx_i in range(-4, 5):
            for dy_i in range(-3, 4):
                p = hc + perp_x * (dx_i * s * 0.75) + perp_y * (dy_i * s * 0.75)
                if abs(dx_i) <= 1 and abs(dy_i) <= 1 and hz_i < 8:
                    continue
                is_dorsal = dy_i >= 1
                is_trim = hz_i in (0, 5, 11) and is_dorsal
                mat = trim_mat if is_trim else (plate_mat if is_dorsal else 1)
                vox.set_world_voxel(p.x, p.y, p.z, mat, 1.0 if is_dorsal else 0.90, 0.58)

    # 3. 4 Articulated Curled Fingers + Knuckle Guards (Z = 0.238..0.282)
    for f_i in range(4):
        fx = -0.020 + f_i * 0.012
        f_scale = 1.0 if f_i in (1, 2) else 0.90
        knuckle = Vector((fx, -0.004, 0.244))
        # Knuckle stud / guard
        vox.set_world_voxel(knuckle.x, knuckle.y - s * 0.8, knuckle.z + s * 0.6, trim_mat, 1.05, 0.74)
        if heavy_box_fingers:
            vox.set_world_voxel(knuckle.x, knuckle.y - s * 1.5, knuckle.z + s, trim_mat, 1.06, 0.78)

        curr = knuckle
        for ph_i in range(3):
            curl_ang = math.radians(25.0 + ph_i * 38.0)
            seg_len = (0.018 - ph_i * 0.002) * f_scale
            nxt = curr + Vector((0.0, math.sin(curl_ang) * seg_len, math.cos(curl_ang) * seg_len * (0.65 - ph_i * 0.35)))
            for k in range(4):
                p = curr.lerp(nxt, k / 3.0)
                vox.set_world_voxel(p.x, p.y, p.z, finger_mat, 0.98, 0.56)
                if heavy_box_fingers or ph_i == 0:
                    vox.set_world_voxel(p.x, p.y - s * 0.6, p.z + s * 0.5, finger_mat, 1.02, 0.62)
            curr = nxt

        if claw_tips:
            claw_p = curr + Vector((0.0, 0.010, -0.008))
            vox.set_world_voxel(claw_p.x, claw_p.y, claw_p.z, 0, 1.06, 0.78)
            vox.set_world_voxel(claw_p.x, claw_p.y + s * 0.7, claw_p.z - s * 0.7, 0, 1.08, 0.85)

    # 4. Opposable Curled Thumb (3 phalanges)
    th_curr = Vector((0.018, -0.014, 0.228))
    for th_i in range(3):
        nxt = th_curr + Vector((-0.004, 0.008, 0.009 - th_i * 0.003))
        for k in range(3):
            p = th_curr.lerp(nxt, k / 2.0)
            vox.set_world_voxel(p.x, p.y, p.z, finger_mat if th_i < 2 else trim_mat, 0.98, 0.58)
        th_curr = nxt

    # 5. Wrought-Iron Lantern Bail Arch & Brass Swivel Collars (Z = 0.180..0.218)
    for b_i in range(25):
        ang = math.pi * (b_i / 24.0)
        bx = math.cos(ang) * 0.028
        bz = 0.212 - math.sin(ang) * 0.030
        vox.set_world_voxel(bx, 0.0, bz, 2 if b_i in (0, 1, 12, 23, 24) else 0, 1.0, 0.62)

    carve_hollow_forearm_bore(vox)


def export_gauntlet_vox(vox: MicroVoxelBuilder, set_idx: int, filename: str) -> int:
    mats = make_micro_voxel_materials(set_idx)
    obj = vox.build_mesh_object(mats)
    obj.name = "LeftArmGauntlet"
    obj.data.name = "LeftArmGauntlet_Mesh"

    col_attr = obj.data.color_attributes.get("Col")
    if col_attr is not None:
        obj.data.color_attributes.active_color = col_attr
        obj.data.color_attributes.render_color_index = 0

    os.makedirs(ARMOR_OUT_DIR, exist_ok=True)
    out_path = os.path.join(ARMOR_OUT_DIR, filename)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.export_scene.gltf(
            filepath=out_path,
            export_format='GLB',
            use_selection=True,
            export_apply=True,
            export_yup=True,
            export_attributes=True,
            export_all_vertex_colors=True,
        )
    except TypeError:
        bpy.ops.export_scene.gltf(
            filepath=out_path,
            export_format='GLB',
            use_selection=True,
            export_apply=True,
            export_yup=True,
            export_all_vertex_colors=True,
        )
    tri_count = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    print(f"[MicroVoxel Gauntlet] Exported {filename} | voxels={len(vox.voxels)} | tris={tri_count}")
    return tri_count


def build_gauntlet_01_leather_stalker() -> int:
    """Set 0 Grave-Stalker: Multi-layered stitched leather bracer, dorsal iron splints, wrist shackle & chain."""
    clear_scene()
    vox = MicroVoxelBuilder("Gauntlet01", voxel_size=VOXEL_SIZE, origin=(0.0, 0.0, 0.0))
    build_base_hollow_vambrace_and_hand(
        vox, plate_mat=1, under_mat=1, trim_mat=2, finger_mat=1, strap_ts=(0.20, 0.48, 0.76), lame_steps=4
    )
    elbow_pt, wrist_pt, arm_len, arm_dir, perp_x, perp_y, r_elbow, r_wrist = get_forearm_frame()
    s = vox.voxel_size

    # 3 Dorsal blackened-iron splint strips + brass rivets
    for ang in (-0.46, 0.0, 0.46):
        sp_dir = (perp_x * math.sin(ang) + perp_y * math.cos(ang)).normalized()
        for step in range(28):
            t = 0.14 + (step / 27.0) * 0.70
            r_at = r_elbow + (r_wrist - r_elbow) * t + 0.0055
            p = elbow_pt.lerp(wrist_pt, t) + sp_dir * r_at
            is_rivet = step in (2, 13, 25)
            vox.set_world_voxel(p.x, p.y, p.z, 2 if is_rivet else 0, 1.02, 0.62)

    # Dangling 3D micro-voxel iron wrist shackle & chain links hanging below the wrist
    shackle_p0 = wrist_pt - perp_y * (r_wrist + 0.006) - perp_x * 0.018
    shackle_p1 = wrist_pt - perp_y * (r_wrist + 0.036) + perp_x * 0.014 - arm_dir * 0.018
    p0_idx = (int(round(shackle_p0.x / s)), int(round(shackle_p0.z / s)), int(round(-shackle_p0.y / s)))
    p1_idx = (int(round(shackle_p1.x / s)), int(round(shackle_p1.z / s)), int(round(-shackle_p1.y / s)))
    vox.add_3d_chain(p0_idx, p1_idx, mat_idx=0, sag_voxels=2.2)

    carve_hollow_forearm_bore(vox)
    return export_gauntlet_vox(vox, 0, "gauntlet_01_leather_stalker.glb")


def build_gauntlet_02_inquisitor_brigandine() -> int:
    """Set 1 Ashen Basilica Paladin: Fluted iron vambrace, gilded Synod cross, elbow couter, wax purity seal."""
    clear_scene()
    vox = MicroVoxelBuilder("Gauntlet02", voxel_size=VOXEL_SIZE, origin=(0.0, 0.0, 0.0))
    build_base_hollow_vambrace_and_hand(
        vox, plate_mat=0, under_mat=1, trim_mat=2, finger_mat=0, strap_ts=(0.24, 0.52, 0.78), lame_steps=5
    )
    elbow_pt, wrist_pt, arm_len, arm_dir, perp_x, perp_y, r_elbow, r_wrist = get_forearm_frame()
    s = vox.voxel_size

    # Raised Gilded Brass Synod Cross Relief on dorsal forearm
    for step in range(-7, 8):
        t = 0.54 + step * 0.016
        r_at = r_elbow + (r_wrist - r_elbow) * t + 0.0065
        p = elbow_pt.lerp(wrist_pt, t) + perp_y * r_at
        vox.set_world_voxel(p.x, p.y, p.z, 2, 1.06, 0.76)
        if step in (-2, 3):
            bar_w = 3 if step == -2 else 2
            for bx in range(-bar_w, bar_w + 1):
                bp = p + perp_x * (bx * s * 0.85)
                vox.set_world_voxel(bp.x, bp.y, bp.z, 2, 1.06, 0.76)

    # Flared Elbow Couter Fan at elbow_pt
    for c_i in range(-4, 5):
        for c_z in range(5):
            t = 0.04 + c_z * 0.025
            ang = c_i * 0.18
            c_dir = (perp_x * math.sin(ang) + perp_y * math.cos(ang)).normalized()
            cp = elbow_pt.lerp(wrist_pt, t) + c_dir * (r_elbow + 0.008 + (4 - c_z) * 0.002)
            vox.set_world_voxel(cp.x, cp.y, cp.z, 2 if c_z == 0 or abs(c_i) == 4 else 0, 1.02, 0.65)

    # Crimson Wax Purity Seal & Stepped Parchment Ribbon on outer forearm
    seal_base = elbow_pt.lerp(wrist_pt, 0.68) - perp_x * (r_wrist + 0.008) + perp_y * 0.008
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            sp = seal_base + perp_y * (dx * s) + arm_dir * (dy * s)
            vox.set_world_voxel(sp.x, sp.y, sp.z, 3, 1.0, 0.80)
    for r_i in range(1, 6):
        rp = seal_base - arm_dir * (r_i * s * 0.9) - perp_y * (r_i * s * 0.35)
        vox.set_world_voxel(rp.x, rp.y, rp.z, 1, 1.04, 0.92)

    carve_hollow_forearm_bore(vox)
    return export_gauntlet_vox(vox, 1, "gauntlet_02_inquisitor_brigandine.glb")


def build_gauntlet_03_juggernaut_plate() -> int:
    """Set 2 Vigil of the Cinder: Heavy siege plate, dorsal furnace vents with glowing ember voxels, cuff candle."""
    clear_scene()
    vox = MicroVoxelBuilder("Gauntlet03", voxel_size=VOXEL_SIZE, origin=(0.0, 0.0, 0.0))
    build_base_hollow_vambrace_and_hand(
        vox,
        plate_mat=0,
        under_mat=2,
        trim_mat=2,
        finger_mat=2,
        strap_ts=(0.22, 0.50, 0.78),
        lame_steps=6,
        heavy_box_fingers=True,
    )
    elbow_pt, wrist_pt, arm_len, arm_dir, perp_x, perp_y, r_elbow, r_wrist = get_forearm_frame()
    s = vox.voxel_size

    # Dorsal Furnace Vent Grilles with recessed glowing cinder ember voxels (mat_idx = 3)
    for v_idx in range(4):
        t = 0.28 + v_idx * 0.14
        r_at = r_elbow + (r_wrist - r_elbow) * t
        vc = elbow_pt.lerp(wrist_pt, t)
        for gx in range(-2, 3):
            ember_p = vc + perp_y * (r_at - 0.001) + perp_x * (gx * s * 0.85)
            vox.set_world_voxel(ember_p.x, ember_p.y, ember_p.z, 3, 1.05, 0.90)
            bar_p = vc + perp_y * (r_at + 0.006) + perp_x * (gx * s * 0.85) + arm_dir * (s * 0.6)
            vox.set_world_voxel(bar_p.x, bar_p.y, bar_p.z, 2, 1.02, 0.68)

    # Melted Wax Mini-Candle / Cinder Brazier node on dorsal cuff
    candle_pos = elbow_pt.lerp(wrist_pt, 0.74) + perp_y * (r_wrist + 0.008) - perp_x * 0.012
    c_ix = int(round(candle_pos.x / s))
    c_iy = int(round(candle_pos.z / s))
    c_iz = int(round(-candle_pos.y / s))
    vox.add_shoulder_candle(c_ix, c_iy, c_iz, height=3, wax_mat=1, flame_mat=3)

    carve_hollow_forearm_bore(vox)
    return export_gauntlet_vox(vox, 2, "gauntlet_03_juggernaut_plate.glb")


def build_gauntlet_04_abyssal_reliquary() -> int:
    """Set 3 Abyssal Ossuary Warden: Obsidian-iron plate, bone-ivory arches, violet rune reliquary, chains & claws."""
    clear_scene()
    vox = MicroVoxelBuilder("Gauntlet04", voxel_size=VOXEL_SIZE, origin=(0.0, 0.0, 0.0))
    build_base_hollow_vambrace_and_hand(
        vox,
        plate_mat=0,
        under_mat=1,
        trim_mat=2,
        finger_mat=0,
        strap_ts=(0.24, 0.54, 0.80),
        lame_steps=5,
        claw_tips=True,
    )
    elbow_pt, wrist_pt, arm_len, arm_dir, perp_x, perp_y, r_elbow, r_wrist = get_forearm_frame()
    s = vox.voxel_size

    # Stepped Bone-Ivory Rib Arches (mat_idx = 1, tint_b = 0.90) + Recessed Abyssal Violet Reliquary Window (mat_idx = 3)
    for rib_i in range(5):
        t = 0.20 + rib_i * 0.14
        r_at = r_elbow + (r_wrist - r_elbow) * t + 0.006
        rc = elbow_pt.lerp(wrist_pt, t)
        for a_i in range(-5, 6):
            ang = a_i * 0.16
            r_dir = (perp_x * math.sin(ang) + perp_y * math.cos(ang)).normalized()
            rp = rc + r_dir * r_at
            vox.set_world_voxel(rp.x, rp.y, rp.z, 1, 1.04, 0.90)
        # Glowing abyssal violet rune channel along dorsal spine between ribs
        if rib_i < 4:
            for sub in range(1, 3):
                rt = t + sub * 0.045
                r_mid = r_elbow + (r_wrist - r_elbow) * rt + 0.001
                rune_p = elbow_pt.lerp(wrist_pt, rt) + perp_y * r_mid
                vox.set_world_voxel(rune_p.x, rune_p.y, rune_p.z, 3, 1.06, 0.92)

    # Interlocking 3D Wrist Chains
    c_p0 = wrist_pt + perp_x * (r_wrist + 0.006)
    c_p1 = wrist_pt - perp_x * (r_wrist + 0.006) - perp_y * 0.022
    idx0 = (int(round(c_p0.x / s)), int(round(c_p0.z / s)), int(round(-c_p0.y / s)))
    idx1 = (int(round(c_p1.x / s)), int(round(c_p1.z / s)), int(round(-c_p1.y / s)))
    vox.add_3d_chain(idx0, idx1, mat_idx=0, sag_voxels=2.0)

    carve_hollow_forearm_bore(vox)
    return export_gauntlet_vox(vox, 3, "gauntlet_04_abyssal_reliquary.glb")


def main() -> None:
    t1 = build_gauntlet_01_leather_stalker()
    t2 = build_gauntlet_02_inquisitor_brigandine()
    t3 = build_gauntlet_03_juggernaut_plate()
    t4 = build_gauntlet_04_abyssal_reliquary()
    print(f"[MicroVoxel Gauntlets Summary] All 4 gauntlets built cleanly | tris=({t1}, {t2}, {t3}, {t4})")


if __name__ == "__main__":
    main()
