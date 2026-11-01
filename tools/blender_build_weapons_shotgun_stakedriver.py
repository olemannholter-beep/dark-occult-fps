import os
import sys
import math
import bpy
from mathutils import Vector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from blender_micro_voxel_kit import WeaponVoxelBuilder, create_weapon_voxel_palette

VOXEL_SIZE = 0.004
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "assets", "models", "weapons")


def clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def add_wax_candle_stub(
    vb: WeaponVoxelBuilder,
    cx_w: float,
    cy_w: float,
    base_z_w: float,
    height_voxels: int = 5,
) -> None:
    """Adds a melted wax candle stub with drips and a multi-stepped glowing voxel flame."""
    s = vb.voxel_size
    icx = int(round(cx_w / s))
    icy = int(round(cy_w / s))
    iz0 = int(round(base_z_w / s))
    for dz in range(height_voxels):
        for dx in (0, 1):
            for dy in (0, 1):
                vb.set_voxel(icx + dx, icy + dy, iz0 + dz, "wax", 1.02)
    # Cascading wax drips
    vb.set_voxel(icx - 1, icy, iz0, "wax", 0.95)
    vb.set_voxel(icx + 2, icy + 1, iz0, "wax", 0.95)
    vb.set_voxel(icx, icy + 2, iz0 - 1, "wax", 0.92)
    vb.set_voxel(icx + 1, icy - 1, iz0 + 1, "wax", 0.94)
    # Glowing voxel flame (amber outer + bright core tip)
    fz = iz0 + height_voxels
    vb.set_voxel(icx, icy, fz, "flame_outer", 1.0)
    vb.set_voxel(icx + 1, icy, fz, "flame_outer", 1.0)
    vb.set_voxel(icx, icy + 1, fz, "flame_outer", 1.0)
    vb.set_voxel(icx, icy, fz + 1, "flame_core", 1.05)
    vb.set_voxel(icx, icy, fz + 2, "flame_core", 1.08)


def build_viewmodel_right_shotgun() -> list[bpy.types.Object]:
    clear_scene()
    palette = create_weapon_voxel_palette()
    s = VOXEL_SIZE

    # =========================================================================
    # 1. Root Node: ShotgunFrame (pivot_xyz = (0.0, 0.0, 0.0))
    # =========================================================================
    frame_vb = WeaponVoxelBuilder("ShotgunFrame", voxel_size=s, pivot_xyz=(0.0, 0.0, 0.0), palette=palette)

    # A. Sawed-Off Walnut Pistol-Grip Stock (wy = -0.105 .. -0.004, wz = -0.072 .. 0.016)
    for step_i in range(26):
        t = step_i / 25.0
        wy_a = -0.004 - t * 0.101
        wy_b = wy_a - 0.005
        wz_top = 0.016 - t * 0.044
        wz_bot = -0.016 - t * 0.056
        wx_half = 0.014 + t * 0.003
        frame_vb.fill_world_box(-wx_half, wx_half, wy_b, wy_a, wz_bot, wz_top, "walnut", 0.96)
        # Brass checkering ribs along the grip flanks
        if step_i % 3 == 1 and 0.15 <= t <= 0.85:
            frame_vb.fill_world_box(
                -(wx_half + 0.002),
                wx_half + 0.002,
                wy_a - 0.002,
                wy_a,
                wz_bot + 0.006,
                wz_top - 0.006,
                "brass",
                1.0,
            )

    # 6 Glowing crimson rune stock inlays on wx = ±0.017
    for r_idx in range(6):
        rt = 0.18 + r_idx * 0.12
        r_wy = -0.006 - rt * 0.095
        r_wz = -0.002 - rt * 0.048
        for side_x in (-0.017, 0.017):
            frame_vb.fill_world_box(side_x - 0.001, side_x + 0.001, r_wy - 0.003, r_wy + 0.003, r_wz - 0.005, r_wz + 0.005, "rune", 1.06)

    # Heavy brass skull butt-plate (wy = -0.105 .. -0.092)
    frame_vb.fill_world_box(-0.018, 0.018, -0.105, -0.092, -0.072, -0.026, "brass", 1.02)
    # Embossed bone skull relief on rear of butt-plate
    frame_vb.fill_world_box(-0.010, 0.010, -0.109, -0.103, -0.062, -0.036, "bone", 1.04)
    frame_vb.fill_world_box(-0.006, -0.003, -0.110, -0.105, -0.050, -0.044, "rune", 1.06)
    frame_vb.fill_world_box(0.003, 0.006, -0.110, -0.105, -0.050, -0.044, "rune", 1.06)

    # Bottom sling swivel ring beneath butt-stock
    frame_vb.fill_cylinder_x(-0.096, -0.076, -0.005, 0.005, r_outer=0.008, r_inner=0.004, mat_key="brass", shade_bias=1.0)

    # B. Standing Breech Block, Water-Table Receiver & Dual Triggers (wy = -0.022 .. 0.062, wz = -0.012 .. 0.040)
    # Wide blued_steel standing breech block
    frame_vb.fill_world_box(-0.022, 0.022, -0.018, 0.016, -0.006, 0.040, "blued_steel", 0.98)
    # Upper tang extending back onto stock wrist
    frame_vb.fill_world_box(-0.008, 0.008, -0.036, -0.016, 0.012, 0.022, "gothic_steel", 1.0)
    # Horizontal water-table bed (wy = 0.016 .. 0.060, wz = -0.008 .. 0.008)
    frame_vb.fill_world_box(-0.021, 0.021, 0.016, 0.060, -0.008, 0.008, "blued_steel", 0.96)
    frame_vb.fill_world_box(-0.016, 0.016, 0.018, 0.058, 0.006, 0.011, "gothic_steel", 1.02)

    # Ornate brass gothic filigree sideplates & silver rivets on wx = ±0.023
    for side_x in (-0.023, 0.023):
        frame_vb.fill_world_box(side_x - 0.001, side_x + 0.001, -0.020, 0.052, -0.004, 0.026, "brass", 1.02)
        frame_vb.fill_world_box(side_x - 0.001, side_x + 0.001, -0.014, 0.012, 0.024, 0.036, "brass", 1.04)
        for ry in (-0.014, 0.002, 0.018, 0.034, 0.048):
            for rz in (0.000, 0.018):
                frame_vb.set_world(side_x + (0.002 if side_x > 0 else -0.002), ry, rz, "silver", 1.08)

    # Front lower hinge pin knuckle at (0.0, 0.055, -0.002) (brass)
    frame_vb.fill_cylinder_x(0.055, -0.002, -0.024, 0.024, r_outer=0.009, r_inner=0.0, mat_key="brass", shade_bias=1.04)
    frame_vb.fill_cylinder_x(0.055, -0.002, -0.026, 0.026, r_outer=0.004, r_inner=0.0, mat_key="silver", shade_bias=1.08)

    # Scrolled brass trigger guard bow (wy = -0.024 .. 0.016, wz = -0.036 .. -0.008)
    frame_vb.fill_world_box(-0.007, 0.007, -0.024, 0.016, -0.036, -0.030, "brass", 1.0)
    frame_vb.fill_world_box(-0.007, 0.007, 0.010, 0.016, -0.034, -0.008, "brass", 1.0)
    frame_vb.fill_world_box(-0.007, 0.007, -0.024, -0.018, -0.034, -0.012, "brass", 1.0)
    # Scroll finial at rear of trigger guard
    frame_vb.fill_world_box(-0.006, 0.006, -0.030, -0.022, -0.040, -0.032, "brass", 1.04)

    # Dual curved brass triggers (wy = 0.002 and -0.010)
    frame_vb.fill_world_box(-0.004, -0.001, 0.000, 0.005, -0.026, -0.008, "brass", 1.06)
    frame_vb.fill_world_box(0.001, 0.004, -0.012, -0.007, -0.026, -0.008, "brass", 1.06)

    root_shotgun = frame_vb.build_mesh_object(parent_obj=None)

    # =========================================================================
    # 2. Child Node: BarrelAssembly (pivot_xyz = (0.0, 0.055, -0.002))
    # =========================================================================
    barrel_pivot = (0.0, 0.055, -0.002)
    barrel_vb = WeaponVoxelBuilder("BarrelAssembly", voxel_size=s, pivot_xyz=barrel_pivot, palette=palette)

    # Carved walnut splinter forend (wx = -0.018 .. 0.018, wy = 0.060 .. 0.210, wz = -0.006 .. 0.012)
    barrel_vb.fill_world_box(-0.018, 0.018, 0.060, 0.202, -0.006, 0.012, "walnut", 0.96)
    # Brass forend iron tip & under-lug latch
    barrel_vb.fill_world_box(-0.017, 0.017, 0.200, 0.214, -0.005, 0.012, "brass", 1.04)
    barrel_vb.fill_world_box(-0.010, 0.010, 0.052, 0.085, -0.008, 0.006, "gothic_steel", 0.98)

    # Twin Side-by-Side 10-Gauge Octagonal/Round Barrels (wx = -0.0135 and +0.0135, wy = 0.018 .. 0.365, wz = 0.022)
    for bx in (-0.0135, 0.0135):
        # Reinforced heavy octagonal breech chambers (wy = 0.018 .. 0.110)
        barrel_vb.fill_cylinder_y(bx, 0.022, 0.018, 0.110, r_outer=0.0145, r_inner=0.007, mat_key="blued_steel", shade_bias=1.0, octagonal=True)
        # Main round barrels (wy = 0.110 .. 0.365)
        barrel_vb.fill_cylinder_y(bx, 0.022, 0.110, 0.365, r_outer=0.013, r_inner=0.007, mat_key="blued_steel", shade_bias=0.98, octagonal=False)
        # Flared muzzle crown ring
        barrel_vb.fill_cylinder_y(bx, 0.022, 0.355, 0.365, r_outer=0.0145, r_inner=0.007, mat_key="gothic_steel", shade_bias=1.04, octagonal=True)
        # Dark bore interiors (r <= 0.007)
        barrel_vb.fill_cylinder_y(bx, 0.022, 0.064, 0.365, r_outer=0.007, r_inner=0.0, mat_key="bore", shade_bias=0.55, octagonal=False)
        # Twin silver under-barrel bayonet spikes protruding at the muzzle (wy = 0.340 .. 0.385, wz = 0.004)
        for b_step in range(12):
            bt = b_step / 11.0
            by_w = 0.340 + bt * 0.045
            bw_half = max(0.002, (1.0 - bt * 0.75) * 0.005)
            bh_half = max(0.002, (1.0 - bt * 0.75) * 0.005)
            barrel_vb.fill_world_box(bx - bw_half, bx + bw_half, by_w, by_w + 0.004, 0.004 - bh_half, 0.004 + bh_half, "silver", 1.06)

    # 3 Stepped brass cathedral barrel-bands (wy = 0.115, 0.225, 0.335) with gothic arch cutouts
    for band_y in (0.115, 0.225, 0.335):
        barrel_vb.fill_world_box(-0.029, 0.029, band_y - 0.008, band_y + 0.008, 0.004, 0.038, "brass", 1.04)
        # Carve gothic arch cutouts on the upper side flanks of each band
        barrel_vb.carve_world_box(-0.031, 0.031, band_y - 0.003, band_y + 0.003, 0.016, 0.028)
        # Re-restore barrel walls inside the band
        for bx in (-0.0135, 0.0135):
            barrel_vb.fill_cylinder_y(bx, 0.022, band_y - 0.009, band_y + 0.009, r_outer=0.013, r_inner=0.007, mat_key="blued_steel", shade_bias=0.98)
            barrel_vb.fill_cylinder_y(bx, 0.022, band_y - 0.009, band_y + 0.009, r_outer=0.007, r_inner=0.0, mat_key="bore", shade_bias=0.55)

    # Raised ventilated center sighting rib (wx = -0.005 .. 0.005, wy = 0.025 .. 0.355, wz = 0.034 .. 0.042)
    barrel_vb.fill_world_box(-0.005, 0.005, 0.025, 0.355, 0.034, 0.042, "gothic_steel", 1.02)
    for vent_i in range(10):
        vy = 0.042 + vent_i * 0.030
        barrel_vb.carve_world_box(-0.006, 0.006, vy, vy + 0.012, 0.034, 0.038)

    # 6 Glowing crimson rune hellfire channels along the sighting rib & breech
    for r_i in range(6):
        ry = 0.035 + r_i * 0.052
        barrel_vb.fill_world_box(-0.003, 0.003, ry, ry + 0.018, 0.040, 0.043, "rune", 1.08)

    # Twin brass + flame_core front bead sights near muzzle
    for sx in (-0.008, 0.008):
        barrel_vb.fill_world_box(sx - 0.002, sx + 0.002, 0.346, 0.354, 0.036, 0.046, "brass", 1.04)
        barrel_vb.set_world(sx, 0.350, 0.048, "flame_core", 1.10)

    # Melted wax candle stub / purity seal on the left breech band
    barrel_vb.fill_world_box(-0.032, -0.026, 0.095, 0.112, 0.006, 0.026, "rune", 1.02)
    add_wax_candle_stub(barrel_vb, -0.026, 0.112, 0.036, height_voxels=4)

    barrel_node = barrel_vb.build_mesh_object(parent_obj=root_shotgun)

    # =========================================================================
    # 2b. Child Nodes: ShellLeft & ShellRight (parent_obj = barrel_node)
    # =========================================================================
    shell_nodes: list[bpy.types.Object] = []
    for s_name, sx in (("ShellLeft", -0.013), ("ShellRight", 0.013)):
        spivot = (sx, 0.018, 0.022)
        svb = WeaponVoxelBuilder(s_name, voxel_size=s, pivot_xyz=spivot, palette=palette)
        # Crimson rune hull (wy = 0.018 .. 0.062, r = 0.008)
        svb.fill_cylinder_y(sx, 0.022, 0.024, 0.062, r_outer=0.008, r_inner=0.0, mat_key="rune", shade_bias=1.02)
        # Brass head sleeve (wy = 0.016 .. 0.026)
        svb.fill_cylinder_y(sx, 0.022, 0.016, 0.026, r_outer=0.0085, r_inner=0.0, mat_key="brass", shade_bias=1.04)
        # Flanged brass extractor rim (wy = 0.014 .. 0.017, r = 0.0095)
        svb.fill_cylinder_y(sx, 0.022, 0.014, 0.017, r_outer=0.0095, r_inner=0.0, mat_key="brass", shade_bias=1.06)
        # Silver center primer at rear face
        svb.fill_cylinder_y(sx, 0.022, 0.013, 0.016, r_outer=0.004, r_inner=0.0, mat_key="silver", shade_bias=1.08)
        s_obj = svb.build_mesh_object(parent_obj=barrel_node)
        # Offset by barrel_node's local origin so world location is exact spivot
        s_obj.location = (
            spivot[0] - barrel_pivot[0],
            spivot[1] - barrel_pivot[1],
            spivot[2] - barrel_pivot[2],
        )
        shell_nodes.append(s_obj)

    # =========================================================================
    # 3. Child Nodes: HammerLeft, HammerRight, TopLever (parent_obj = root_shotgun)
    # =========================================================================
    hammer_nodes: list[bpy.types.Object] = []
    for h_name, hx in (("HammerLeft", -0.0135), ("HammerRight", 0.0135)):
        hpivot = (hx, -0.016, 0.032)
        hvb = WeaponVoxelBuilder(h_name, voxel_size=s, pivot_xyz=hpivot, palette=palette)
        hvb.fill_world_box(hx - 0.003, hx + 0.003, -0.022, -0.010, 0.026, 0.046, "blued_steel", 1.02)
        # Rabbit-ear gothic spur curving backward and upward
        hvb.fill_world_box(hx - 0.003, hx + 0.003, -0.032, -0.018, 0.042, 0.054, "brass", 1.06)
        hvb.fill_world_box(hx - 0.002, hx + 0.002, -0.014, -0.006, 0.038, 0.044, "silver", 1.06)
        hammer_nodes.append(hvb.build_mesh_object(parent_obj=root_shotgun))

    lever_pivot = (0.0, -0.010, 0.038)
    lvb = WeaponVoxelBuilder("TopLever", voxel_size=s, pivot_xyz=lever_pivot, palette=palette)
    lvb.fill_world_box(-0.005, 0.005, -0.028, -0.004, 0.038, 0.044, "brass", 1.04)
    lvb.fill_world_box(-0.003, 0.009, -0.034, -0.024, 0.038, 0.045, "brass", 1.06)
    lvb.set_world(0.0, -0.010, 0.045, "silver", 1.08)
    lever_node = lvb.build_mesh_object(parent_obj=root_shotgun)

    return [root_shotgun, barrel_node, *shell_nodes, *hammer_nodes, lever_node]


def build_viewmodel_right_stakedriver() -> list[bpy.types.Object]:
    clear_scene()
    palette = create_weapon_voxel_palette()
    s = VOXEL_SIZE

    # =========================================================================
    # 1. Root Node: DriverFrame (pivot_xyz = (0.0, 0.0, 0.0))
    # =========================================================================
    frame_vb = WeaponVoxelBuilder("DriverFrame", voxel_size=s, pivot_xyz=(0.0, 0.0, 0.0), palette=palette)

    # A. Heavy Rear Recoil Grip (wy = -0.075 .. -0.005, wz = -0.092 .. 0.008)
    for g_i in range(22):
        t = g_i / 21.0
        wz_a = 0.008 - t * 0.094
        wz_b = wz_a - 0.005
        wy_rear = -0.044 - t * 0.031
        wy_front = -0.005 - t * 0.026
        frame_vb.fill_world_box(-0.014, 0.014, wy_rear, wy_front, wz_b, wz_a, "walnut", 0.96)
        if g_i % 4 == 1:
            frame_vb.fill_world_box(-0.016, 0.016, wy_rear + 0.004, wy_front - 0.004, wz_b, wz_a, "brass", 1.02)

    # Brass pommel cap at bottom of grip (wz = -0.094 .. -0.084)
    frame_vb.fill_world_box(-0.017, 0.017, -0.078, -0.028, -0.094, -0.084, "brass", 1.04)
    frame_vb.fill_world_box(-0.010, 0.010, -0.068, -0.038, -0.100, -0.092, "wrought_iron", 0.96)

    # Reinforced wrought_iron knuckle bow & heavy brass industrial trigger
    frame_vb.fill_world_box(-0.008, 0.008, 0.014, 0.022, -0.078, -0.008, "wrought_iron", 0.98)
    frame_vb.fill_world_box(-0.008, 0.008, -0.034, 0.022, -0.082, -0.074, "wrought_iron", 0.98)
    frame_vb.fill_world_box(-0.004, 0.004, -0.002, 0.006, -0.038, -0.008, "brass", 1.06)

    # B. Pneumatic Receiver Chassis & Cathedral Arch Rail Guides (wx = -0.022 .. 0.022, wy = -0.022 .. 0.235, wz = -0.008 .. 0.038)
    frame_vb.fill_world_box(-0.022, 0.022, -0.022, 0.235, -0.008, 0.034, "blued_steel", 0.98)
    # Gothic steel upper side rails
    frame_vb.fill_world_box(-0.023, -0.012, -0.018, 0.232, 0.014, 0.036, "gothic_steel", 1.02)
    frame_vb.fill_world_box(0.012, 0.023, -0.018, 0.232, 0.014, 0.036, "gothic_steel", 1.02)
    # Carve open top track channel (wx = -0.010 .. 0.010, wz = 0.016 .. 0.038)
    frame_vb.carve_world_box(-0.010, 0.010, -0.014, 0.236, 0.016, 0.040)

    # 6 Stepped brass cathedral arch guide ribs bridging the open top track channel
    for arch_y in (0.005, 0.047, 0.089, 0.131, 0.173, 0.215):
        # Side pillars of cathedral arch
        frame_vb.fill_world_box(-0.025, -0.012, arch_y - 0.004, arch_y + 0.004, -0.006, 0.040, "brass", 1.04)
        frame_vb.fill_world_box(0.012, 0.025, arch_y - 0.004, arch_y + 0.004, -0.006, 0.040, "brass", 1.04)
        # Upper arch bridge leaving clearance for StakeRam (cz=0.026, r=0.009)
        frame_vb.fill_world_box(-0.018, 0.018, arch_y - 0.004, arch_y + 0.004, 0.036, 0.044, "brass", 1.06)
        frame_vb.fill_world_box(-0.006, 0.006, arch_y - 0.003, arch_y + 0.003, 0.044, 0.048, "silver", 1.08)

    # 12 Glowing rune power strips (6 per side) along both chassis flanks
    for p_idx in range(6):
        py_w = -0.006 + p_idx * 0.040
        for side_x in (-0.023, 0.023):
            frame_vb.fill_world_box(side_x - 0.001, side_x + 0.001, py_w, py_w + 0.020, 0.002, 0.010, "rune", 1.08)

    # C. Side-Mounted Pressurized Alchemical Steam Cylinder (wx = -0.028, wy = 0.085 .. 0.205, wz = 0.008)
    # Glowing flame_outer & flame_core cylindrical pressure vessel (r = 0.010)
    frame_vb.fill_cylinder_y(-0.028, 0.008, 0.093, 0.197, r_outer=0.010, r_inner=0.005, mat_key="flame_outer", shade_bias=1.04)
    frame_vb.fill_cylinder_y(-0.028, 0.008, 0.093, 0.197, r_outer=0.005, r_inner=0.0, mat_key="flame_core", shade_bias=1.08)
    # Brass end-caps (wy = 0.085 .. 0.094 and 0.196 .. 0.205)
    frame_vb.fill_cylinder_y(-0.028, 0.008, 0.085, 0.094, r_outer=0.012, r_inner=0.0, mat_key="brass", shade_bias=1.04)
    frame_vb.fill_cylinder_y(-0.028, 0.008, 0.196, 0.205, r_outer=0.012, r_inner=0.0, mat_key="brass", shade_bias=1.04)
    # Center brass reinforcement band
    frame_vb.fill_cylinder_y(-0.028, 0.008, 0.141, 0.149, r_outer=0.012, r_inner=0.009, mat_key="brass", shade_bias=1.06)
    # Protective brass cage bars running lengthwise
    for cage_off_x, cage_off_z in ((-0.012, 0.0), (0.0, 0.012), (0.0, -0.012)):
        cx = -0.028 + cage_off_x
        cz = 0.008 + cage_off_z
        frame_vb.fill_world_box(cx - 0.002, cx + 0.002, 0.088, 0.202, cz - 0.002, cz + 0.002, "brass", 1.02)
    # 3 Braided brass pressure pipes connecting cylinder to receiver (wz = -0.006, 0.004, 0.022)
    for pipe_y, pipe_z in ((0.090, -0.006), (0.145, 0.004), (0.200, 0.022)):
        frame_vb.fill_world_box(-0.028, -0.018, pipe_y - 0.004, pipe_y + 0.004, pipe_z - 0.004, pipe_z + 0.004, "brass", 1.04)

    # Receiver-mounted melted wax candle stub with glowing voxel flame on rear-right arch
    add_wax_candle_stub(frame_vb, 0.016, 0.064, 0.036, height_voxels=5)

    # D. Serrated Lower Ritual Cleaver Bayonet Blade (wx = -0.005 .. 0.005, wy = 0.110 .. 0.345, wz = -0.048 .. -0.004)
    # Heavy bone dorsal spine (wz = -0.014 .. -0.004)
    frame_vb.fill_world_box(-0.005, 0.005, 0.110, 0.325, -0.014, -0.004, "bone", 1.02)
    # Brass mounting collar joining cleaver to front receiver underbelly
    frame_vb.fill_world_box(-0.012, 0.012, 0.110, 0.145, -0.016, -0.004, "brass", 1.04)
    # Razor-stepped silver cleaver blade (wz = -0.042 .. -0.014) tapering at forward tip (wy = 0.300 .. 0.345)
    for c_step in range(58):
        ct = c_step / 57.0
        cy_w = 0.115 + ct * 0.230
        if cy_w <= 0.300:
            cz_bot = -0.042
            cx_half = 0.004
        else:
            tip_t = (cy_w - 0.300) / 0.045
            cz_bot = -0.042 + tip_t * 0.030
            cx_half = max(0.002, 0.004 * (1.0 - tip_t * 0.5))
        frame_vb.fill_world_box(-cx_half, cx_half, cy_w, cy_w + 0.004, cz_bot, -0.014, "silver", 1.04)
        # Beveled razor edge along bottom of cleaver
        frame_vb.fill_world_box(-0.002, 0.002, cy_w, cy_w + 0.004, cz_bot - 0.003, cz_bot, "silver", 1.08)

    # 7 Stepped saw-teeth along the lower edge (wz = -0.048)
    for tooth_i in range(7):
        ty_w = 0.130 + tooth_i * 0.024
        frame_vb.fill_world_box(-0.002, 0.002, ty_w, ty_w + 0.010, -0.048, -0.041, "silver", 1.08)
        frame_vb.fill_world_box(-0.002, 0.002, ty_w + 0.004, ty_w + 0.010, -0.051, -0.046, "silver", 1.10)

    # Recessed glowing rune blood-fuller channel along cleaver flanks (wx = ±0.004)
    frame_vb.fill_world_box(-0.005, 0.005, 0.145, 0.295, -0.024, -0.018, "rune", 1.08)

    root_driver = frame_vb.build_mesh_object(parent_obj=None)

    # =========================================================================
    # 2. Child Mechanical Node: StakeRam (pivot_xyz = (0.0, 0.140, 0.026))
    # =========================================================================
    ram_pivot = (0.0, 0.140, 0.026)
    ram_vb = WeaponVoxelBuilder("StakeRam", voxel_size=s, pivot_xyz=ram_pivot, palette=palette)
    # Sliding octagonal blued_steel & silver harpoon shaft (wy = 0.010 .. 0.285, cz = 0.026, r = 0.009)
    ram_vb.fill_cylinder_y(0.0, 0.026, 0.010, 0.160, r_outer=0.009, r_inner=0.0, mat_key="blued_steel", shade_bias=1.0, octagonal=True)
    ram_vb.fill_cylinder_y(0.0, 0.026, 0.160, 0.285, r_outer=0.009, r_inner=0.0, mat_key="silver", shade_bias=1.04, octagonal=True)
    # Brass piston sealing rings & rear strike cap
    for ring_y in (0.014, 0.068, 0.122, 0.176):
        ram_vb.fill_cylinder_y(0.0, 0.026, ring_y - 0.003, ring_y + 0.003, r_outer=0.0105, r_inner=0.0, mat_key="brass", shade_bias=1.06, octagonal=True)
    # Glowing rune blood-grooves along the harpoon shaft
    ram_vb.fill_world_box(-0.010, 0.010, 0.185, 0.275, 0.024, 0.028, "rune", 1.08)
    # Stepped pyramidal barbed silver tip (wy = 0.285 .. 0.355)
    for t_step in range(18):
        tt = t_step / 17.0
        ty_w = 0.285 + tt * 0.070
        tr = max(0.002, (1.0 - tt * 0.82) * 0.011)
        ram_vb.fill_world_box(-tr, tr, ty_w, ty_w + 0.004, 0.026 - tr, 0.026 + tr, "silver", 1.08)
    # Rearward-swept harpoon barbs at wy = 0.282 .. 0.298
    ram_vb.fill_world_box(-0.016, 0.016, 0.282, 0.292, 0.022, 0.030, "silver", 1.08)
    ram_vb.fill_world_box(-0.012, 0.012, 0.292, 0.302, 0.023, 0.029, "silver", 1.08)

    ram_node = ram_vb.build_mesh_object(parent_obj=root_driver)

    # =========================================================================
    # 3. Child Mechanical Node: FlywheelGear (pivot_xyz = (-0.024, 0.045, 0.016))
    # =========================================================================
    fw_pivot = (-0.024, 0.045, 0.016)
    fw_vb = WeaponVoxelBuilder("FlywheelGear", voxel_size=s, pivot_xyz=fw_pivot, palette=palette)
    # Outer brass rim (r_outer = 0.022, r_inner = 0.015)
    fw_vb.fill_cylinder_x(0.045, 0.016, -0.029, -0.021, r_outer=0.022, r_inner=0.015, mat_key="brass", shade_bias=1.04)
    # 4 Cross spokes
    fw_vb.fill_world_box(-0.028, -0.022, 0.025, 0.065, 0.013, 0.019, "brass", 1.0)
    fw_vb.fill_world_box(-0.028, -0.022, 0.042, 0.048, -0.004, 0.036, "brass", 1.0)
    # 12 Clockwork gear teeth around perimeter (r = 0.024)
    for tooth_idx in range(12):
        ang = (tooth_idx / 12.0) * math.tau
        ty = 0.045 + math.cos(ang) * 0.023
        tz = 0.016 + math.sin(ang) * 0.023
        fw_vb.fill_world_box(-0.029, -0.021, ty - 0.002, ty + 0.002, tz - 0.002, tz + 0.002, "brass", 1.08)
    # Glowing rune center hub
    fw_vb.fill_cylinder_x(0.045, 0.016, -0.031, -0.020, r_outer=0.007, r_inner=0.0, mat_key="rune", shade_bias=1.08)

    fw_node = fw_vb.build_mesh_object(parent_obj=root_driver)

    # =========================================================================
    # 4. Child Mechanical Node: LoadingCrank (pivot_xyz = (0.024, 0.025, 0.016))
    # =========================================================================
    crank_pivot = (0.024, 0.025, 0.016)
    crank_vb = WeaponVoxelBuilder("LoadingCrank", voxel_size=s, pivot_xyz=crank_pivot, palette=palette)
    # Hub boss on right receiver
    crank_vb.fill_cylinder_x(0.025, 0.016, 0.020, 0.029, r_outer=0.008, r_inner=0.0, mat_key="brass", shade_bias=1.04)
    # Right-side brass winding crank arm (wy = 0.025, wz = 0.016 .. 0.044)
    crank_vb.fill_world_box(0.022, 0.028, 0.021, 0.029, 0.016, 0.046, "brass", 1.04)
    # Walnut handle knob protruding outward to the right (wx = 0.026 .. 0.042, wz = 0.042)
    crank_vb.fill_cylinder_x(0.025, 0.042, 0.026, 0.044, r_outer=0.006, r_inner=0.0, mat_key="walnut", shade_bias=1.0)
    crank_vb.fill_cylinder_x(0.025, 0.042, 0.043, 0.046, r_outer=0.007, r_inner=0.0, mat_key="brass", shade_bias=1.06)

    crank_node = crank_vb.build_mesh_object(parent_obj=root_driver)

    return [root_driver, ram_node, fw_node, crank_node]


def export_glb(filepath: str, objects: list[bpy.types.Object]) -> tuple[int, int]:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    total_verts = 0
    total_tris = 0
    for obj in objects:
        if obj.type == "MESH" and obj.data is not None:
            total_verts += len(obj.data.vertices)
            total_tris += sum(max(0, len(p.vertices) - 2) for p in obj.data.polygons)

    bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format="GLB",
        export_apply=False,
        export_yup=True,
        export_attributes=True,
    )
    print(f"[EXPORTED] {filepath} | Objects: {len(objects)} | Verts: {total_verts} | Tris: {total_tris}")
    return total_verts, total_tris


def main() -> None:
    shotgun_objs = build_viewmodel_right_shotgun()
    shotgun_path = os.path.join(OUTPUT_DIR, "viewmodel_right_shotgun.glb")
    export_glb(shotgun_path, shotgun_objs)

    driver_objs = build_viewmodel_right_stakedriver()
    driver_path = os.path.join(OUTPUT_DIR, "viewmodel_right_stakedriver.glb")
    export_glb(driver_path, driver_objs)


if __name__ == "__main__":
    main()
