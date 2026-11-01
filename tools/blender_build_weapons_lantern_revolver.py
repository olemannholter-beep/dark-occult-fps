import os
import sys
import math
import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from blender_micro_voxel_kit import WeaponVoxelBuilder, create_weapon_voxel_palette

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "assets", "models", "weapons")


def clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def export_glb(filepath: str) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format="GLB",
        export_apply=False,
        export_yup=True,
        export_attributes=True,
    )
    print(f"[MicroVoxelWeapons] Exported -> {filepath}")


def count_scene_stats() -> tuple[int, int]:
    total_tris = 0
    total_verts = 0
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH" and obj.data is not None:
            mesh = obj.data
            total_verts += len(mesh.vertices)
            for poly in mesh.polygons:
                total_tris += max(0, len(poly.vertices) - 2)
    return total_verts, total_tris


def build_viewmodel_left_lantern() -> None:
    """
    Model 1: Weeper's Reliquary Lantern (`viewmodel_left_lantern.glb`)
    Ultra-fine 4mm micro-voxel hierarchy (`LeftArmGauntlet` -> `LanternPendulum`).
    """
    clear_scene()
    palette = create_weapon_voxel_palette()
    s = 0.004

    # 1. Root Node: LeftArmGauntlet (Bail Handle arch & twin brass bail collars)
    bail_vb = WeaponVoxelBuilder("LeftArmGauntlet", voxel_size=s, pivot_xyz=(0.0, 0.0, 0.0), palette=palette)

    # Ornate wrought-iron bail handle arch & twin brass bail collars around (0, 0, 0.180 .. 0.235)
    for deg in range(-75, 76, 4):
        rad = math.radians(deg)
        bx = math.sin(rad) * 0.036
        bz = 0.180 + math.cos(rad) * 0.052
        bail_vb.fill_world_box(bx - 0.004, bx + 0.004, -0.006, 0.006, bz - 0.004, bz + 0.004, "wrought_iron", 1.02)
        if abs(deg) <= 28:
            # Knurled brass grip sleeve at apex of bail arch
            bail_vb.fill_world_box(bx - 0.006, bx + 0.006, -0.008, 0.008, bz - 0.005, bz + 0.005, "brass", 1.06)
        elif abs(deg) in (44, 60):
            bail_vb.fill_world_box(bx - 0.005, bx + 0.005, -0.007, 0.007, bz - 0.004, bz + 0.004, "brass", 1.04)

    # Twin brass bail side trunnion collars & central swivel shackle at wz = 0.180
    for side in (-1, 1):
        bail_vb.fill_world_box(side * 0.038 - 0.005, side * 0.038 + 0.005, -0.008, 0.008, 0.176, 0.188, "brass", 1.06)
        bail_vb.fill_world_box(side * 0.022, side * 0.036, -0.004, 0.004, 0.178, 0.184, "wrought_iron", 0.96)
    bail_vb.fill_cylinder_z(0.0, 0.0, 0.176, 0.190, r_outer=0.014, r_inner=0.0, mat_key="brass", shade_bias=1.05, octagonal=True)
    bail_vb.fill_cylinder_z(0.0, 0.0, 0.190, 0.204, r_outer=0.008, r_inner=0.0, mat_key="wrought_iron", shade_bias=0.98, octagonal=True)

    root_arm = bail_vb.build_mesh_object(parent_obj=None)

    # 2. Child Node: LanternPendulum (local coords hanging downward from wz = 0.0 to -0.340)
    pend_vb = WeaponVoxelBuilder("LanternPendulum", voxel_size=s, pivot_xyz=(0.0, 0.0, 0.0), palette=palette)

    # Top Suspension Chain (wz = -0.004 .. -0.044): 5 interlocking 3D chain links + brass finial spike
    for link_idx in range(5):
        lz0 = -0.004 - link_idx * 0.008
        lz1 = lz0 - 0.010
        if link_idx % 2 == 0:
            pend_vb.fill_world_box(-0.008, 0.008, -0.003, 0.003, lz1, lz0, "wrought_iron", 0.98)
            pend_vb.carve_world_box(-0.003, 0.003, -0.004, 0.004, lz1 + 0.003, lz0 - 0.003)
        else:
            pend_vb.fill_world_box(-0.003, 0.003, -0.008, 0.008, lz1, lz0, "wrought_iron", 0.94)
            pend_vb.carve_world_box(-0.004, 0.004, -0.003, 0.003, lz1 + 0.003, lz0 - 0.003)

    # Brass finial crown & spike at wz = -0.044
    pend_vb.fill_cylinder_z(0.0, 0.0, -0.050, -0.040, r_outer=0.014, r_inner=0.0, mat_key="brass", shade_bias=1.06, octagonal=True)

    # Stepped Gothic Pagoda Chimney Cap (wz = -0.044 .. -0.088)
    pagoda_tiers = [
        (-0.056, -0.048, 0.016, "wrought_iron"),
        (-0.064, -0.056, 0.024, "brass"),
        (-0.072, -0.064, 0.030, "wrought_iron"),
        (-0.080, -0.072, 0.038, "wrought_iron"),
        (-0.088, -0.080, 0.046, "brass"),
    ]
    for z0, z1, rad, m_key in pagoda_tiers:
        pend_vb.fill_cylinder_z(0.0, 0.0, z0, z1, r_outer=rad, r_inner=max(0.0, rad - 0.010), mat_key=m_key, shade_bias=1.0, octagonal=True)

    # Carve physical heat-vent louver cutouts and place inner glowing ember ring
    for angle_deg in range(0, 360, 45):
        ar = math.radians(angle_deg)
        vx = math.cos(ar) * 0.026
        vy = math.sin(ar) * 0.026
        pend_vb.carve_world_box(vx - 0.004, vx + 0.004, vy - 0.004, vy + 0.004, -0.074, -0.064)
    pend_vb.fill_cylinder_z(0.0, 0.0, -0.074, -0.066, r_outer=0.018, r_inner=0.012, mat_key="flame_outer", shade_bias=1.05, octagonal=True)

    # 4 stepped brass corner horns/spires on pagoda eaves
    for sx in (-1, 1):
        for sy in (-1, 1):
            hx, hy = sx * 0.034, sy * 0.034
            pend_vb.fill_world_box(hx - 0.004, hx + 0.004, hy - 0.004, hy + 0.004, -0.088, -0.074, "brass", 1.06)
            pend_vb.fill_world_box(hx + sx * 0.004 - 0.003, hx + sx * 0.004 + 0.003, hy + sy * 0.004 - 0.003, hy + sy * 0.004 + 0.003, -0.080, -0.066, "brass", 1.08)

    # Octagonal Reliquary Cage & Gothic Arch Pillars (wz = -0.088 .. -0.228)
    # Upper (wz = -0.088 .. -0.100) and lower (wz = -0.214 .. -0.228) rings
    pend_vb.fill_cylinder_z(0.0, 0.0, -0.095, -0.088, r_outer=0.045, r_inner=0.028, mat_key="wrought_iron", shade_bias=0.98, octagonal=True)
    pend_vb.fill_cylinder_z(0.0, 0.0, -0.100, -0.095, r_outer=0.043, r_inner=0.028, mat_key="brass", shade_bias=1.04, octagonal=True)
    pend_vb.fill_cylinder_z(0.0, 0.0, -0.220, -0.214, r_outer=0.043, r_inner=0.026, mat_key="brass", shade_bias=1.04, octagonal=True)
    pend_vb.fill_cylinder_z(0.0, 0.0, -0.228, -0.220, r_outer=0.046, r_inner=0.0, mat_key="wrought_iron", shade_bias=0.96, octagonal=True)

    # Translucent Amber Glass cylinder (wz = -0.214 .. -0.102, r = 0.030 .. 0.035)
    pend_vb.fill_cylinder_z(0.0, 0.0, -0.214, -0.102, r_outer=0.035, r_inner=0.029, mat_key="glass", shade_bias=1.02, octagonal=True)

    # 8 vertical stepped wrought_iron cage pillars + gothic pointed-arch tracery crowns + 4 glowing rune cross inlays
    for i in range(8):
        ang = i * (math.pi / 4.0)
        px = math.cos(ang) * 0.042
        py = math.sin(ang) * 0.042
        pend_vb.fill_world_box(px - 0.004, px + 0.004, py - 0.004, py + 0.004, -0.224, -0.092, "wrought_iron", 0.96)
        # Protruding brass rivets on top and bottom rings
        rx = math.cos(ang) * 0.047
        ry = math.sin(ang) * 0.047
        pend_vb.set_world(rx, ry, -0.094, "brass", 1.08)
        pend_vb.set_world(rx, ry, -0.222, "brass", 1.08)
        # Mid-pillar brass band
        pend_vb.fill_world_box(px - 0.005, px + 0.005, py - 0.005, py + 0.005, -0.162, -0.154, "brass", 1.05)

        # Gothic pointed-arch tracery crowns between adjacent pillars (wz = -0.100 .. -0.118)
        next_ang = (i + 1) * (math.pi / 4.0)
        for step_t in (0.25, 0.50, 0.75):
            ax = (math.cos(ang) * (1.0 - step_t) + math.cos(next_ang) * step_t) * 0.041
            ay = (math.sin(ang) * (1.0 - step_t) + math.sin(next_ang) * step_t) * 0.041
            az = -0.104 if step_t == 0.50 else -0.112
            pend_vb.fill_world_box(ax - 0.003, ax + 0.003, ay - 0.003, ay + 0.003, az - 0.004, -0.100, "wrought_iron", 0.95)

        # 4 glowing rune cross/sigil inlays on the 4 cardinal pillars
        if i % 2 == 0:
            ix_out = math.cos(ang) * 0.045
            iy_out = math.sin(ang) * 0.045
            for dz_off in (-0.012, -0.008, -0.004, 0.0, 0.004, 0.008, 0.012):
                pend_vb.set_world(ix_out, iy_out, -0.158 + dz_off, "rune", 1.06)
            tx = -math.sin(ang) * 0.004
            ty = math.cos(ang) * 0.004
            pend_vb.set_world(ix_out + tx, iy_out + ty, -0.154, "rune", 1.06)
            pend_vb.set_world(ix_out - tx, iy_out - ty, -0.154, "rune", 1.06)

    # Melted Ritual Candle (r <= 0.016, wz = -0.212 .. -0.162) with asymmetric wax drips
    pend_vb.fill_cylinder_z(0.0, 0.0, -0.212, -0.162, r_outer=0.015, r_inner=0.0, mat_key="wax", shade_bias=1.02, octagonal=False)
    wax_drips = [
        (0.016, 0.004, -0.212, -0.166),
        (-0.015, 0.006, -0.212, -0.172),
        (0.005, -0.016, -0.212, -0.168),
        (-0.008, -0.014, -0.212, -0.178),
    ]
    for dx_w, dy_w, wz0, wz1 in wax_drips:
        pend_vb.fill_world_box(dx_w - 0.003, dx_w + 0.003, dy_w - 0.003, dy_w + 0.003, wz0, wz1, "wax", 0.96)
    pend_vb.set_world(0.0, 0.0, -0.160, "wrought_iron", 0.85)  # Charred wick

    # Multi-stepped Soul-Flame (wz = -0.160 .. -0.125): inner flame_core + outer flame_outer + floating embers
    pend_vb.fill_world_box(-0.008, 0.008, -0.008, 0.008, -0.156, -0.136, "flame_outer", 1.04)
    pend_vb.fill_world_box(-0.005, 0.005, -0.005, 0.005, -0.136, -0.126, "flame_outer", 1.06)
    pend_vb.fill_world_box(-0.004, 0.004, -0.004, 0.004, -0.154, -0.132, "flame_core", 1.08)
    pend_vb.set_world(0.0, 0.0, -0.124, "flame_core", 1.08)
    pend_vb.set_world(0.010, -0.006, -0.120, "flame_outer", 1.06)
    pend_vb.set_world(-0.008, 0.008, -0.116, "flame_core", 1.08)

    # Stepped Oil Reservoir Base & Dangling Incense Charm (wz = -0.228 .. -0.336)
    pend_vb.fill_cylinder_z(0.0, 0.0, -0.244, -0.228, r_outer=0.040, r_inner=0.0, mat_key="brass", shade_bias=1.02, octagonal=True)
    pend_vb.fill_cylinder_z(0.0, 0.0, -0.258, -0.244, r_outer=0.030, r_inner=0.0, mat_key="wrought_iron", shade_bias=0.96, octagonal=True)
    pend_vb.fill_cylinder_z(0.0, 0.0, -0.268, -0.258, r_outer=0.018, r_inner=0.0, mat_key="brass", shade_bias=1.04, octagonal=True)

    # Lower iron cage skirt fins
    for i in range(4):
        ang = i * (math.pi / 2.0) + (math.pi / 4.0)
        fx, fy = math.cos(ang) * 0.034, math.sin(ang) * 0.034
        pend_vb.fill_world_box(fx - 0.004, fx + 0.004, fy - 0.004, fy + 0.004, -0.256, -0.228, "wrought_iron", 0.94)

    # 3-link dangling wrought_iron chain (wz = -0.268 .. -0.305)
    for c_idx in range(3):
        cz0 = -0.268 - c_idx * 0.012
        cz1 = cz0 - 0.014
        if c_idx % 2 == 0:
            pend_vb.fill_world_box(-0.006, 0.006, -0.003, 0.003, cz1, cz0, "wrought_iron", 0.96)
        else:
            pend_vb.fill_world_box(-0.003, 0.003, -0.006, 0.006, cz1, cz0, "wrought_iron", 0.92)

    # Spherical/octagonal brass IncenseCharmPod (wz = -0.305 .. -0.336) with 4 glowing flame_outer rune beads
    pend_vb.fill_cylinder_z(0.0, 0.0, -0.314, -0.305, r_outer=0.012, r_inner=0.0, mat_key="brass", shade_bias=1.04, octagonal=True)
    pend_vb.fill_cylinder_z(0.0, 0.0, -0.326, -0.314, r_outer=0.018, r_inner=0.0, mat_key="brass", shade_bias=1.06, octagonal=True)
    pend_vb.fill_cylinder_z(0.0, 0.0, -0.336, -0.326, r_outer=0.010, r_inner=0.0, mat_key="wrought_iron", shade_bias=0.96, octagonal=True)
    for bx, by in ((0.018, 0.0), (-0.018, 0.0), (0.0, 0.018), (0.0, -0.018)):
        pend_vb.set_world(bx, by, -0.320, "flame_outer", 1.08)

    pendulum_node = pend_vb.build_mesh_object(parent_obj=root_arm)
    pendulum_node.location = (0.0, 0.0, 0.18)

    out_path = os.path.join(OUTPUT_DIR, "viewmodel_left_lantern.glb")
    export_glb(out_path)
    verts, tris = count_scene_stats()
    total_vox = len(bail_vb.voxels) + len(pend_vb.voxels)
    print(f"[LanternStats] Voxels={total_vox}, Verts={verts}, Tris={tris}")


def build_viewmodel_right_revolver() -> None:
    """
    Model 2: Occult Revolver (`viewmodel_right_revolver.glb`)
    Ultra-fine 3.5mm micro-voxel hierarchy (`RevolverFrame` + 6 child mechanical nodes).
    """
    clear_scene()
    palette = create_weapon_voxel_palette()
    s = 0.0035

    # 1. Root Node: RevolverFrame
    frame_vb = WeaponVoxelBuilder("RevolverFrame", voxel_size=s, pivot_xyz=(0.0, 0.0, 0.0), palette=palette)

    # Carved Walnut Birdshead Grip (wy = -0.075 .. -0.008, wz = -0.105 .. 0.005)
    for step_idx in range(30):
        t = step_idx / 29.0
        wz = 0.004 - t * 0.106
        wy_center = -0.022 - t * 0.044
        half_y = 0.014 + math.sin(t * math.pi) * 0.006
        half_x = 0.011 + math.sin(t * math.pi) * 0.003
        frame_vb.fill_world_box(
            -half_x, half_x,
            wy_center - half_y, wy_center + half_y,
            wz - 0.002, wz + 0.002,
            "walnut", 1.0,
        )
        # Backstrap & frontstrap steel spine
        frame_vb.fill_world_box(-0.006, 0.006, wy_center - half_y - 0.003, wy_center - half_y, wz - 0.002, wz + 0.002, "blued_steel", 0.96)
        if 4 <= step_idx <= 24 and step_idx % 3 == 0:
            # Brass diamond checkering ribs on both sides (wx = +-0.014)
            for sx in (-1, 1):
                frame_vb.fill_world_box(
                    sx * (half_x + 0.001) - 0.001, sx * (half_x + 0.001) + 0.001,
                    wy_center - 0.008, wy_center + 0.008,
                    wz - 0.0015, wz + 0.0015,
                    "brass", 1.05,
                )

    # 6 recessed glowing crimson rune sigil inlays on walnut grip panels
    for side in (-1, 1):
        for r_idx, (ry, rz) in enumerate(((-0.036, -0.032), (-0.044, -0.054), (-0.052, -0.076))):
            frame_vb.set_world(side * 0.013, ry, rz, "rune", 1.08)
            frame_vb.set_world(side * 0.013, ry + (0.0035 if r_idx % 2 == 0 else -0.0035), rz, "rune", 1.06)

    # Flanged octagonal brass skull butt-cap (wy = -0.068, wz = -0.102) & bottom brass lanyard ring
    frame_vb.fill_cylinder_z(0.0, -0.066, -0.106, -0.095, r_outer=0.016, r_inner=0.0, mat_key="brass", shade_bias=1.06, octagonal=True)
    frame_vb.fill_cylinder_x(-0.066, -0.112, -0.005, 0.005, r_outer=0.008, r_inner=0.0035, mat_key="brass", shade_bias=1.04)

    # Standing Breech Receiver, Top Strap & Trigger Guard (wy = -0.032 .. 0.092, wz = -0.024 .. 0.054)
    # Standing breech block
    frame_vb.fill_world_box(-0.014, 0.014, -0.032, -0.001, -0.018, 0.042, "blued_steel", 0.98)
    # Carve hammer slot in standing breech
    frame_vb.carve_world_box(-0.0045, 0.0045, -0.034, -0.010, 0.016, 0.044)
    # Lower crane shelf & front frame lug
    frame_vb.fill_world_box(-0.013, 0.013, 0.000, 0.090, -0.022, -0.010, "blued_steel", 0.96)
    frame_vb.fill_world_box(-0.014, 0.014, 0.075, 0.092, -0.014, 0.044, "blued_steel", 1.00)
    # Arching blued_steel top strap
    frame_vb.fill_world_box(-0.011, 0.011, -0.010, 0.088, 0.040, 0.051, "blued_steel", 1.02)
    # Ensure central cylinder window (wy = 0.002 .. 0.074, wz = -0.008 .. 0.038) is completely open
    frame_vb.carve_world_box(-0.028, 0.028, 0.002, 0.074, -0.008, 0.038)

    # Brass V-notch rear sight ears & 2 glowing rune sight dots at wy = -0.010, wz = 0.055
    for sx in (-1, 1):
        frame_vb.fill_world_box(sx * 0.006 - 0.002, sx * 0.006 + 0.002, -0.014, -0.004, 0.051, 0.057, "brass", 1.06)
        frame_vb.set_world(sx * 0.006, -0.014, 0.055, "rune", 1.08)

    # Ornate brass gothic filigree sideplates & silver screw heads on wx = +-0.015
    for sx in (-1, 1):
        frame_vb.fill_world_box(sx * 0.015 - 0.0015, sx * 0.015 + 0.0015, -0.026, -0.004, -0.012, 0.026, "brass", 1.05)
        frame_vb.fill_world_box(sx * 0.014 - 0.0015, sx * 0.014 + 0.0015, 0.010, 0.070, -0.020, -0.012, "brass", 1.04)
        for sy, sz in ((-0.022, 0.018), (-0.008, -0.006), (0.082, 0.002)):
            frame_vb.set_world(sx * 0.016, sy, sz, "silver", 1.08)

    # Right-side hinged brass loading gate (wx = +0.016, wy = 0.002, wz = 0.012)
    frame_vb.fill_world_box(0.014, 0.019, -0.004, 0.010, 0.002, 0.022, "brass", 1.06)

    # Scrolled brass trigger guard bow (wy = -0.012 .. 0.028, wz = -0.048 .. -0.020)
    frame_vb.fill_world_box(-0.005, 0.005, -0.012, 0.028, -0.048, -0.020, "brass", 1.04)
    frame_vb.carve_world_box(-0.007, 0.007, -0.006, 0.022, -0.042, -0.020)
    frame_vb.fill_world_box(-0.004, 0.004, -0.016, -0.008, -0.052, -0.044, "brass", 1.06)

    # Octagonal Cathedral Barrel, Ventilated Rib & Under-Barrel Reliquary Chain (wy = 0.076 .. 0.325)
    frame_vb.fill_cylinder_y(0.0, 0.028, 0.076, 0.322, r_outer=0.014, r_inner=0.006, mat_key="blued_steel", shade_bias=1.00, octagonal=True)
    frame_vb.fill_cylinder_y(0.0, 0.028, 0.080, 0.322, r_outer=0.006, r_inner=0.0, mat_key="bore", shade_bias=0.60, octagonal=False)

    # Brass muzzle crown collar (wy = 0.305 .. 0.322) & silver cathedral front sight blade with glowing rune bead
    frame_vb.fill_cylinder_y(0.0, 0.028, 0.305, 0.322, r_outer=0.016, r_inner=0.007, mat_key="brass", shade_bias=1.06, octagonal=True)
    frame_vb.fill_world_box(-0.0025, 0.0025, 0.295, 0.315, 0.042, 0.056, "silver", 1.08)
    frame_vb.fill_world_box(-0.002, 0.002, 0.300, 0.310, 0.056, 0.060, "silver", 1.08)
    frame_vb.set_world(0.0, 0.295, 0.055, "rune", 1.08)

    # Full-length ventilated top sighting rib (wz = 0.040 .. 0.048) with 5 physical rectangular vent cutouts
    frame_vb.fill_world_box(-0.005, 0.005, 0.088, 0.292, 0.040, 0.048, "blued_steel", 1.03)
    for v_idx in range(5):
        vy0 = 0.102 + v_idx * 0.036
        frame_vb.carve_world_box(-0.007, 0.007, vy0, vy0 + 0.018, 0.041, 0.045)
        frame_vb.fill_world_box(-0.006, 0.006, vy0 - 0.004, vy0, 0.040, 0.049, "brass", 1.05)

    # 6 recessed glowing rune blood-channels along both barrel side flats (wx = +-0.014)
    for sx in (-1, 1):
        for b_idx in range(3):
            by0 = 0.110 + b_idx * 0.058
            frame_vb.fill_world_box(sx * 0.014 - 0.001, sx * 0.014 + 0.001, by0, by0 + 0.032, 0.026, 0.030, "rune", 1.08)

    # Reinforced under-barrel ejector shroud (wz = 0.006 .. 0.016)
    frame_vb.fill_world_box(-0.009, 0.009, 0.076, 0.292, 0.006, 0.016, "blued_steel", 0.95)
    frame_vb.carve_world_box(-0.005, 0.005, 0.180, 0.290, 0.005, 0.014)
    frame_vb.fill_world_box(-0.010, 0.010, 0.132, 0.148, 0.004, 0.018, "brass", 1.05)

    # Melted wax purity seal + dangling 3-link wrought_iron chain & brass skull charm (wy = 0.14, wz = -0.025 .. 0.004)
    frame_vb.fill_world_box(0.009, 0.015, 0.134, 0.146, 0.006, 0.016, "rune", 1.04)
    frame_vb.fill_world_box(0.010, 0.014, 0.136, 0.144, -0.004, 0.008, "wax", 1.02)
    for c_idx in range(3):
        cz0 = 0.004 - c_idx * 0.007
        frame_vb.fill_world_box(-0.003, 0.003, 0.137, 0.143, cz0 - 0.007, cz0, "wrought_iron", 0.96)
    frame_vb.fill_world_box(-0.005, 0.005, 0.135, 0.145, -0.026, -0.016, "brass", 1.06)
    frame_vb.set_world(-0.0035, 0.145, -0.020, "rune", 1.08)
    frame_vb.set_world(0.0035, 0.145, -0.020, "rune", 1.08)

    revolver_frame = frame_vb.build_mesh_object(parent_obj=None)

    # 2. Child Node: Cylinder (pivot_xyz = (0.0, 0.038, 0.013))
    cyl_vb = WeaponVoxelBuilder("Cylinder", voxel_size=s, pivot_xyz=(0.0, 0.038, 0.013), palette=palette)
    cyl_vb.fill_cylinder_y(0.0, 0.013, 0.005, 0.071, r_outer=0.022, r_inner=0.004, mat_key="blued_steel", shade_bias=1.00, octagonal=False)
    for ch_idx in range(6):
        ang = ch_idx * (math.pi / 3.0)
        ch_x = math.cos(ang) * 0.013
        ch_z = 0.013 + math.sin(ang) * 0.013
        # Recessed dark chamber bore at front + rear brass .45 cartridge rim & silver primer
        cyl_vb.fill_cylinder_y(ch_x, ch_z, 0.056, 0.072, r_outer=0.0045, r_inner=0.0, mat_key="bore", shade_bias=0.55)
        cyl_vb.fill_cylinder_y(ch_x, ch_z, 0.004, 0.009, r_outer=0.005, r_inner=0.0, mat_key="brass", shade_bias=1.06)
        cyl_vb.set_world(ch_x, 0.004, ch_z, "silver", 1.08)
        # Fluted groove between chambers with glowing rune flute inlay
        fl_ang = ang + (math.pi / 6.0)
        fx = math.cos(fl_ang) * 0.021
        fz = 0.013 + math.sin(fl_ang) * 0.021
        cyl_vb.carve_world_box(fx - 0.003, fx + 0.003, 0.014, 0.060, fz - 0.003, fz + 0.003)
        cyl_vb.fill_world_box(
            math.cos(fl_ang) * 0.018 - 0.0015, math.cos(fl_ang) * 0.018 + 0.0015,
            0.020, 0.054,
            0.013 + math.sin(fl_ang) * 0.018 - 0.0015, 0.013 + math.sin(fl_ang) * 0.018 + 0.0015,
            "rune", 1.06,
        )
    # Rear brass ratchet star & front brass collar ring
    cyl_vb.fill_cylinder_y(0.0, 0.013, 0.003, 0.007, r_outer=0.007, r_inner=0.0, mat_key="brass", shade_bias=1.05)
    cyl_vb.fill_cylinder_y(0.0, 0.013, 0.034, 0.042, r_outer=0.0225, r_inner=0.019, mat_key="brass", shade_bias=1.05)
    cyl_vb.build_mesh_object(parent_obj=revolver_frame)

    # 3. Child Node: Hammer (pivot_xyz = (0.0, -0.028, 0.036))
    ham_vb = WeaponVoxelBuilder("Hammer", voxel_size=s, pivot_xyz=(0.0, -0.028, 0.036), palette=palette)
    ham_vb.fill_world_box(-0.0035, 0.0035, -0.034, -0.018, 0.028, 0.048, "blued_steel", 1.00)
    ham_vb.fill_world_box(-0.0045, 0.0045, -0.045, -0.026, 0.046, 0.058, "brass", 1.06)
    ham_vb.fill_world_box(-0.0025, 0.0025, -0.020, -0.014, 0.038, 0.045, "silver", 1.08)
    ham_vb.build_mesh_object(parent_obj=revolver_frame)

    # 4. Child Node: Trigger (pivot_xyz = (0.0, 0.008, -0.022))
    trig_vb = WeaponVoxelBuilder("Trigger", voxel_size=s, pivot_xyz=(0.0, 0.008, -0.022), palette=palette)
    trig_vb.fill_world_box(-0.0025, 0.0025, 0.004, 0.014, -0.030, -0.018, "brass", 1.05)
    trig_vb.fill_world_box(-0.0025, 0.0025, 0.002, 0.010, -0.038, -0.028, "brass", 1.06)
    trig_vb.build_mesh_object(parent_obj=revolver_frame)

    # 5. Child Node: SideGearWheel (pivot_xyz = (-0.018, 0.002, 0.012))
    gear_vb = WeaponVoxelBuilder("SideGearWheel", voxel_size=s, pivot_xyz=(-0.018, 0.002, 0.012), palette=palette)
    gear_vb.fill_cylinder_x(0.002, 0.012, -0.021, -0.015, r_outer=0.011, r_inner=0.0, mat_key="brass", shade_bias=1.06)
    for t_idx in range(8):
        tang = t_idx * (math.pi / 4.0)
        gy = 0.002 + math.cos(tang) * 0.013
        gz = 0.012 + math.sin(tang) * 0.013
        gear_vb.set_world(-0.018, gy, gz, "brass", 1.08)
    gear_vb.set_world(-0.022, 0.002, 0.012, "silver", 1.08)
    gear_vb.build_mesh_object(parent_obj=revolver_frame)

    # 6. Child Node: EjectorRod (pivot_xyz = (0.0, 0.210, 0.010))
    ej_vb = WeaponVoxelBuilder("EjectorRod", voxel_size=s, pivot_xyz=(0.0, 0.210, 0.010), palette=palette)
    ej_vb.fill_cylinder_y(0.0, 0.010, 0.185, 0.285, r_outer=0.0035, r_inner=0.0, mat_key="silver", shade_bias=1.06)
    ej_vb.fill_cylinder_y(0.0, 0.010, 0.278, 0.292, r_outer=0.006, r_inner=0.0, mat_key="brass", shade_bias=1.06)
    for sp_y in (0.194, 0.208, 0.222, 0.236, 0.250, 0.264):
        ej_vb.fill_cylinder_y(0.0, 0.010, sp_y - 0.002, sp_y + 0.002, r_outer=0.005, r_inner=0.0, mat_key="brass", shade_bias=1.04)
    ej_vb.build_mesh_object(parent_obj=revolver_frame)

    # 7. Child Node: MuzzleAnchor Empty at (0.0, 0.340, 0.028)
    muzzle = bpy.data.objects.new("MuzzleAnchor", None)
    muzzle.empty_display_size = 0.02
    muzzle.location = (0.0, 0.340, 0.028)
    muzzle.parent = revolver_frame
    bpy.context.collection.objects.link(muzzle)

    out_path = os.path.join(OUTPUT_DIR, "viewmodel_right_revolver.glb")
    export_glb(out_path)
    verts, tris = count_scene_stats()
    total_vox = (
        len(frame_vb.voxels)
        + len(cyl_vb.voxels)
        + len(ham_vb.voxels)
        + len(trig_vb.voxels)
        + len(gear_vb.voxels)
        + len(ej_vb.voxels)
    )
    print(f"[RevolverStats] Voxels={total_vox}, Verts={verts}, Tris={tris}")


if __name__ == "__main__":
    build_viewmodel_left_lantern()
    build_viewmodel_right_revolver()
