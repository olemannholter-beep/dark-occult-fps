"""
tools/blender_build_voxel_dungeons_biomes.py
Builds 15 Hyper-Detailed Ultra-Realistic Micro-Voxel Dungeon Models:
- 6 Ossuary Variety Pieces (res://assets/models/ossuary_variety/)
- 9 Biomes 2-4 Dungeon Kit Pieces (res://assets/models/dungeon/)
Strictly conforms to Godot 4.7 static typing, 4m x 4m grid bounds,
0.50m solid dungeon wall thicknesses (Rule 9.4), and proper origin placement.
"""

import math
import os
import sys
import bpy
import bmesh
from mathutils import Vector, Euler

# Import micro-voxel kit and environment palette
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from blender_micro_voxel_kit import (
    create_environment_voxel_palette,
    EnvironmentVoxelBuilder,
    export_environment_glb,
)

PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
OSSUARY_DIR = os.path.join(PROJECT_ROOT, "assets", "models", "ossuary_variety")
DUNGEON_DIR = os.path.join(PROJECT_ROOT, "assets", "models", "dungeon")


def clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


# ==============================================================================
# PARAMETRIC VOXEL MICRO-HELPERS
# ==============================================================================

def add_skull_voxel(
    vb: EnvironmentVoxelBuilder,
    cx: float,
    cy: float,
    cz: float,
    scale: float = 1.0,
    rot_z: float = 0.0,
) -> None:
    """Carves and builds a recognizable gothic skull cluster out of micro-voxels."""
    s = scale
    hw = 0.09 * s
    hd = 0.10 * s
    hh = 0.09 * s
    cos_a = math.cos(rot_z)
    sin_a = math.sin(rot_z)

    # Cranium block
    for dx in (-0.06 * s, 0.0, 0.06 * s):
        for dy in (-0.06 * s, 0.0, 0.06 * s):
            for dz in (-0.04 * s, 0.0, 0.05 * s):
                rx = cx + dx * cos_a - dy * sin_a
                ry = cy + dx * sin_a + dy * cos_a
                vb.set_world(rx, ry, cz + dz, "bone", 1.0)

    # Brow ridge & cheekbones
    for dx in (-0.08 * s, 0.08 * s):
        rx = cx + dx * cos_a - (-0.08 * s) * sin_a
        ry = cy + dx * sin_a + (-0.08 * s) * cos_a
        vb.set_world(rx, ry, cz + 0.01 * s, "bone", 1.05)

    # Maxilla / dental arch
    for dx in (-0.04 * s, 0.0, 0.04 * s):
        rx = cx + dx * cos_a - (-0.09 * s) * sin_a
        ry = cy + dx * sin_a + (-0.09 * s) * cos_a
        vb.set_world(rx, ry, cz - 0.06 * s, "bone", 0.95)

    # Recessed eye cavities
    for dx in (-0.045 * s, 0.045 * s):
        rx = cx + dx * cos_a - (-0.08 * s) * sin_a
        ry = cy + dx * sin_a + (-0.08 * s) * cos_a
        vb.carve_world_box(rx - 0.02, rx + 0.02, ry - 0.02, ry + 0.02, cz - 0.01, cz + 0.03)


def add_candle_voxel(
    vb: EnvironmentVoxelBuilder,
    cx: float,
    cy: float,
    cz: float,
    height: float = 0.18,
    radius: float = 0.035,
) -> None:
    """Builds a melting wax candle with dripping rivulets and emissive flame core."""
    vb.fill_world_cylinder_z(cx, cy, cz, cz + height, radius, 0.0, "wax", 1.02)
    # Wax drips running down sides
    vb.set_world(cx + radius + 0.015, cy, cz + height * 0.4, "wax", 0.95)
    vb.set_world(cx - radius - 0.015, cy + 0.01, cz + height * 0.25, "wax", 0.93)
    vb.set_world(cx, cy + radius + 0.015, cz + height * 0.5, "wax", 0.94)
    # Candle wick
    vb.set_world(cx, cy, cz + height + 0.015, "wrought_iron", 0.8)
    # Emissive flame
    fz = cz + height + 0.04
    vb.set_world(cx, cy, fz, "candle_flame", 1.1)
    vb.set_world(cx, cy, fz + 0.03, "candle_flame", 1.2)


def add_chain_voxel(
    vb: EnvironmentVoxelBuilder,
    p0: tuple[float, float, float],
    p1: tuple[float, float, float],
    mat_key: str = "wrought_iron",
    sag: float = 0.0,
) -> None:
    """Builds an interlocking 3D micro-voxel chain between world coordinates p0 and p1."""
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    dz = p1[2] - p0[2]
    dist = math.sqrt(dx * dx + dy * dy + dz * dz)
    steps = max(3, int(math.ceil(dist / 0.06)))
    for i in range(steps + 1):
        t = i / float(steps)
        cx = p0[0] + dx * t
        cy = p0[1] + dy * t
        cz = p0[2] + dz * t - math.sin(t * math.pi) * sag
        vb.set_world(cx, cy, cz, mat_key, 1.0)
        # Alternate orientation for interlocking chain look
        if i % 2 == 0:
            vb.set_world(cx + 0.02, cy, cz, mat_key, 0.92)
            vb.set_world(cx - 0.02, cy, cz, mat_key, 0.92)
        else:
            vb.set_world(cx, cy + 0.02, cz, mat_key, 0.94)
            vb.set_world(cx, cy - 0.02, cz, mat_key, 0.94)


# ==============================================================================
# 1. ossuary_stone_bridge_4x4.glb (4m span x 2.2m walkway)
# ==============================================================================
def build_ossuary_stone_bridge_4x4(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    vb = EnvironmentVoxelBuilder(
        name="ossuary_stone_bridge_4x4",
        voxel_size=0.04,
        palette=palette,
        pivot_xyz=(0.0, 0.0, 0.0),
    )

    # 1. Core structural stone deck slab (walkway surface at Z = 0.0, span Y: [-2.0, 2.0], width X: [-1.08, 1.08])
    vb.fill_world_box(-1.08, 1.08, -2.0, 2.0, -0.24, 0.0, "weathered_stone", 0.95)

    # 32 Flagstone walkway cobble slabs across bridge deck (4 cols x 8 rows)
    for r in range(8):
        cy = -1.75 + r * 0.50
        for c in range(4):
            cx = -0.75 + c * 0.50
            mat_k = "cobble_flagstone" if (r + c) % 2 == 0 else "carved_stone_trim"
            vb.fill_world_box(cx - 0.22, cx + 0.22, cy - 0.22, cy + 0.22, -0.04, 0.04, mat_k, 1.02)

    # 2. Twin Underslung Gothic Ribbed Arch Ribs spanning Y = -1.95 to +1.95 (dropping to Z = -1.18m)
    for sx in (-0.96, 0.96):
        # End abutment piers at Y = -1.85 and +1.85
        for sy in (-1.82, 1.82):
            vb.fill_world_box(sx - 0.17, sx + 0.17, sy - 0.18, sy + 0.18, -1.18, -0.20, "carved_stone_trim", 0.92)

        # 11 Voussoir arch blocks along each underslung rib curve
        for vi in range(11):
            t = (vi - 5.0) / 5.0  # -1.0 to +1.0
            vy = t * 1.68
            vz = -0.32 - (1.0 - t * t) * 0.65
            vb.fill_world_box(sx - 0.14, sx + 0.14, vy - 0.18, vy + 0.18, vz - 0.12, vz + 0.12, "carved_stone_trim", 0.96)

    # 4 Transverse stone cross-beams under bridge deck
    for bi in range(5):
        by = -1.50 + bi * 0.75
        vb.fill_world_box(-1.05, 1.05, by - 0.11, by + 0.11, -0.36, -0.20, "weathered_stone", 0.90)

    # 3. Low crenellated stone side curbs & bollards along left/right edges (X = +-1.02)
    for sx in (-1.02, 1.02):
        # Continuous curb plinth
        vb.fill_world_box(sx - 0.12, sx + 0.12, -2.0, 2.0, 0.0, 0.18, "carved_stone_trim", 1.0)

        # 6 Crenellated merlon blocks per side
        for mi in range(6):
            my = -1.65 + mi * 0.66
            vb.fill_world_box(sx - 0.12, sx + 0.12, my - 0.18, my + 0.18, 0.18, 0.34, "weathered_stone", 0.98)

        # 3 Tall stone bollards per side capped with Ossuary Skulls & Wrought-Iron Rings
        for py in (-1.80, 0.0, 1.80):
            # Bollard base, shaft, capital
            vb.fill_world_box(sx - 0.16, sx + 0.16, py - 0.16, py + 0.16, 0.16, 0.32, "carved_stone_trim", 1.0)
            vb.fill_world_box(sx - 0.12, sx + 0.12, py - 0.12, py + 0.12, 0.32, 0.88, "weathered_stone", 0.95)
            vb.fill_world_box(sx - 0.15, sx + 0.15, py - 0.15, py + 0.15, 0.88, 1.00, "carved_stone_trim", 1.02)

            # Skull cap on bollard
            rot_face = math.pi * 0.5 if sx < 0 else -math.pi * 0.5
            add_skull_voxel(vb, sx, py, 1.08, scale=1.0, rot_z=rot_face)

            # Wrought-iron tie ring band
            vb.fill_world_box(sx - 0.14, sx + 0.14, py - 0.06, py + 0.06, 0.74, 0.82, "wrought_iron", 1.0)

        # Hanging Wrought-Iron Chain Side-Rails (2 spans per side)
        for span_center_y in (-0.90, 0.90):
            p_start = (sx, span_center_y - 0.80, 0.80)
            p_end = (sx, span_center_y + 0.80, 0.80)
            add_chain_voxel(vb, p_start, p_end, mat_key="wrought_iron", sag=0.22)

    vb.build_mesh_object()
    out_path = os.path.join(out_dir, "ossuary_stone_bridge_4x4.glb")
    export_environment_glb(out_path)
    print(f"[Wave1C] Exported -> {out_path}")


# ==============================================================================
# 2. ossuary_balcony_railing_4m.glb (4.0m wide x 1.1m tall)
# ==============================================================================
def build_ossuary_balcony_railing_4m(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    vb = EnvironmentVoxelBuilder(
        name="ossuary_balcony_railing_4m",
        voxel_size=0.035,
        palette=palette,
        pivot_xyz=(0.0, 0.0, 0.0),
    )

    # 1. Stepped base plinth & coping rail (4.02m W along X, 0.36m D along Y, 0.22m tall)
    vb.fill_world_box(-2.01, 2.01, -0.18, 0.18, 0.0, 0.14, "weathered_stone", 0.95)
    vb.fill_world_box(-1.98, 1.98, -0.15, 0.15, 0.14, 0.22, "carved_stone_trim", 1.0)

    # Heavy top handrail & sub-cornice (Z = 0.92 to 1.06)
    vb.fill_world_box(-1.98, 1.98, -0.15, 0.15, 0.92, 0.99, "weathered_stone", 0.96)
    vb.fill_world_box(-2.02, 2.02, -0.18, 0.18, 0.99, 1.06, "carved_stone_trim", 1.05)

    # 2. 3 Heavy Gothic Pier Newel Posts (at X = -1.86, 0.0, +1.86)
    for px in (-1.86, 0.0, 1.86):
        # Post shaft & molded capital
        vb.fill_world_box(px - 0.16, px + 0.16, -0.19, 0.19, 0.05, 1.02, "carved_stone_trim", 0.98)
        vb.fill_world_box(px - 0.19, px + 0.19, -0.21, 0.21, 1.02, 1.14, "carved_stone_trim", 1.04)

        # Wrought-iron finial spike atop each newel post (Z = 1.14 to 1.34)
        vb.fill_world_cylinder_z(px, 0.0, 1.14, 1.34, 0.04, 0.0, "wrought_iron", 1.0)
        vb.set_world(px, 0.0, 1.36, "wrought_iron", 1.1)

        # Relief skull inset on newel post front (-Y) and back (+Y)
        add_skull_voxel(vb, px, -0.16, 0.58, scale=0.82, rot_z=0.0)
        add_skull_voxel(vb, px, 0.16, 0.58, scale=0.82, rot_z=math.pi)

    # 3. 2 Bay Spans (Left Bay: X in [-1.60, -0.26], Right Bay: X in [0.26, 1.60])
    for bay_sign in (-1.0, 1.0):
        bay_cx = bay_sign * 0.93

        # Central pierced stone skull-relief medallion panel in each bay
        vb.fill_world_box(bay_cx - 0.24, bay_cx + 0.24, -0.11, 0.11, 0.22, 0.88, "weathered_stone", 0.94)
        vb.fill_world_box(bay_cx - 0.19, bay_cx + 0.19, -0.13, 0.13, 0.28, 0.82, "carved_stone_trim", 1.0)
        add_skull_voxel(vb, bay_cx, -0.09, 0.55, scale=0.92, rot_z=0.0)
        add_skull_voxel(vb, bay_cx, 0.09, 0.55, scale=0.92, rot_z=math.pi)

        # 6 Gothic Colonnette Balusters flanking central medallion per bay (3 per side)
        for side_s in (-1.0, 1.0):
            for bi in range(3):
                bx = bay_cx + side_s * (0.34 + bi * 0.17)
                # Base, shaft, iron collar, capital
                vb.fill_world_box(bx - 0.055, bx + 0.055, -0.09, 0.09, 0.22, 0.31, "carved_stone_trim", 1.0)
                vb.fill_world_cylinder_z(bx, 0.0, 0.31, 0.80, 0.045, 0.0, "weathered_stone", 0.95)
                vb.fill_world_box(bx - 0.05, bx + 0.05, -0.07, 0.07, 0.52, 0.57, "wrought_iron", 0.9)
                vb.fill_world_box(bx - 0.055, bx + 0.055, -0.09, 0.09, 0.80, 0.90, "carved_stone_trim", 1.02)

        # 9 Wrought-Iron Pickets & Spikes along top rail per bay (Z = 1.06 to 1.24)
        for si in range(9):
            sx = (bay_cx - 0.64) + si * 0.16
            vb.fill_world_cylinder_z(sx, 0.0, 1.06, 1.24, 0.02, 0.0, "wrought_iron", 1.0)
            vb.set_world(sx, 0.0, 1.26, "wrought_iron", 1.1)

    # 4 Melted Tallow Candles along the balustrade handrail
    for cx in (-1.45, -0.42, 0.42, 1.45):
        add_candle_voxel(vb, cx, 0.0, 1.06, height=0.16, radius=0.03)

    vb.build_mesh_object()
    out_path = os.path.join(out_dir, "ossuary_balcony_railing_4m.glb")
    export_environment_glb(out_path)
    print(f"[Wave1C] Exported -> {out_path}")


# ==============================================================================
# 3. ossuary_buttress_arch_4x4.glb (4m x 4m walk-through rib)
# ==============================================================================
def build_ossuary_buttress_arch_4x4(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    vb = EnvironmentVoxelBuilder(
        name="ossuary_buttress_arch_4x4",
        voxel_size=0.04,
        palette=palette,
        pivot_xyz=(0.0, 0.0, 0.0),
    )

    # 1. Twin Heavy Side Buttress Piers at X = -1.62 and +1.62 (leaving wide 2.52m walk-through opening in center)
    for sx in (-1.0, 1.0):
        px = sx * 1.62
        # Stepped plinth base (Z = 0.0 to 0.44)
        vb.fill_world_box(px - 0.43, px + 0.43, -0.48, 0.48, 0.0, 0.22, "weathered_stone", 0.92)
        vb.fill_world_box(px - 0.39, px + 0.39, -0.44, 0.44, 0.22, 0.44, "carved_stone_trim", 1.0)

        # Main masonry pier shaft & core (Z = 0.44 to 3.05)
        vb.fill_world_box(px - 0.34, px + 0.34, -0.38, 0.38, 0.44, 3.05, "weathered_stone", 0.95)

        # Outer and inner vertical gothic pilasters
        vb.fill_world_box(px + sx * 0.28 - 0.09, px + sx * 0.28 + 0.09, -0.42, 0.42, 0.44, 3.05, "carved_stone_trim", 1.0)
        vb.fill_world_box(px - sx * 0.28 - 0.09, px - sx * 0.28 + 0.09, -0.42, 0.42, 0.44, 3.05, "carved_stone_trim", 1.0)

        # Pier capital at Z = 3.05 to 3.25
        vb.fill_world_box(px - 0.41, px + 0.41, -0.46, 0.46, 3.05, 3.25, "carved_stone_trim", 1.04)

        # 5 Tiered Skull & Femur Niches stacked up each pier
        for tier in range(5):
            tz = 0.65 + tier * 0.48
            # Stone shelf divider
            vb.fill_world_box(px - 0.26, px + 0.26, -0.41, 0.41, tz - 0.18, tz - 0.11, "carved_stone_trim", 1.0)
            # Bone bundles on shelf
            vb.fill_world_box(px - 0.18, px + 0.18, -0.36, 0.36, tz - 0.11, tz - 0.04, "bone", 0.95)
            # Skulls looking inward toward walkway and outward on Y faces
            add_skull_voxel(vb, px - sx * 0.18, 0.0, tz, scale=0.88, rot_z=sx * math.pi * 0.5)
            add_skull_voxel(vb, px, -0.32, tz, scale=0.82, rot_z=0.0)
            add_skull_voxel(vb, px, 0.32, tz, scale=0.82, rot_z=math.pi)

        # Wrought-iron structural strap bands around pier
        for bz in (0.95, 1.95, 2.85):
            vb.fill_world_box(px - 0.38, px + 0.38, -0.44, 0.44, bz - 0.04, bz + 0.04, "wrought_iron", 0.9)

    # 2. Upper Spandrel Beam & Cornice at Z = 3.85..4.05 spanning full 4.04m width
    vb.fill_world_box(-2.0, 2.0, -0.39, 0.39, 3.85, 3.96, "weathered_stone", 0.95)
    vb.fill_world_box(-2.02, 2.02, -0.44, 0.44, 3.96, 4.05, "carved_stone_trim", 1.05)

    # 3. Pointed Gothic Vaulting Rib Arch (springing at Z = 3.05 to peak Z = 3.82)
    for sx in (-1.0, 1.0):
        for vi in range(9):
            t = (vi + 0.5) / 9.0
            ang = t * (math.pi * 0.44)
            vx = sx * 1.48 * math.cos(ang)
            vz = 3.05 + 0.78 * math.sin(ang)
            vb.fill_world_box(vx - 0.12, vx + 0.12, -0.42, 0.42, vz - 0.11, vz + 0.11, "carved_stone_trim", 1.02)
            # Inner iron rib trim
            vb.fill_world_box(vx * 0.95 - 0.07, vx * 0.95 + 0.07, -0.44, 0.44, vz - 0.16, vz - 0.08, "wrought_iron", 0.9)

    # Central Arch Keystone with Horned Boss Skull
    vb.fill_world_box(-0.17, 0.17, -0.46, 0.46, 3.65, 3.95, "carved_stone_trim", 1.05)
    add_skull_voxel(vb, 0.0, -0.44, 3.78, scale=1.1, rot_z=0.0)
    add_skull_voxel(vb, 0.0, 0.44, 3.78, scale=1.1, rot_z=math.pi)

    # Hanging Rusted Iron Chains from Arch Haunches (X = -1.02 and +1.02)
    for cx in (-1.02, 1.02):
        p0 = (cx, 0.0, 3.35)
        p1 = (cx, 0.0, 2.30)
        add_chain_voxel(vb, p0, p1, mat_key="wrought_iron", sag=0.0)

    vb.build_mesh_object()
    out_path = os.path.join(out_dir, "ossuary_buttress_arch_4x4.glb")
    export_environment_glb(out_path)
    print(f"[Wave1C] Exported -> {out_path}")


# ==============================================================================
# 4. ossuary_bone_chandelier.glb (Suspended 2.6m-wide Ceiling Centerpiece)
# ==============================================================================
def build_ossuary_bone_chandelier(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    vb = EnvironmentVoxelBuilder(
        name="ossuary_bone_chandelier",
        voxel_size=0.035,
        palette=palette,
        pivot_xyz=(0.0, 0.0, 0.0),
    )

    # 1. Ceiling Rosette Mount at Z = 2.34m & Central Suspension Column down to Z = 0.25m
    vb.fill_world_box(-0.32, 0.32, -0.32, 0.32, 2.26, 2.40, "wrought_iron", 0.95)
    vb.fill_world_cylinder_z(0.0, 0.0, 2.10, 2.26, 0.22, 0.0, "bronze", 1.02)
    vb.fill_world_cylinder_z(0.0, 0.0, 0.25, 2.10, 0.08, 0.0, "wrought_iron", 0.92)

    # Bottom iron drop finial & cage boss (Z = 0.08 to 0.35)
    vb.fill_world_cylinder_z(0.0, 0.0, 0.20, 0.35, 0.18, 0.0, "bronze", 1.04)
    vb.fill_world_cylinder_z(0.0, 0.0, 0.08, 0.20, 0.06, 0.0, "wrought_iron", 0.9)

    # 2. Lower Outer Wheel (Radius = 1.25m, 2.50m wide at Z = 0.55m, 16 polygonal segments)
    r_outer = 1.25
    z_outer = 0.55
    vb.fill_world_cylinder_z(0.0, 0.0, z_outer - 0.07, z_outer + 0.07, r_outer + 0.06, r_outer - 0.06, "wrought_iron", 0.96)
    vb.fill_world_cylinder_z(0.0, 0.0, z_outer - 0.04, z_outer + 0.04, r_outer - 0.04, r_outer - 0.12, "bone", 1.02)

    # 16 Skull-and-Candle Stations around the outer wheel
    for i in range(16):
        ang = (i / 16.0) * math.tau
        vx = r_outer * math.cos(ang)
        vy = r_outer * math.sin(ang)
        # Brass drip pan
        vb.fill_world_box(vx - 0.10, vx + 0.10, vy - 0.10, vy + 0.10, z_outer + 0.07, z_outer + 0.11, "bronze", 1.05)
        # Outward-facing ossuary skull
        add_skull_voxel(vb, vx * 1.04, vy * 1.04, z_outer, scale=0.82, rot_z=ang + math.pi * 0.5)
        # Lit tallow candle atop skull
        add_candle_voxel(vb, vx, vy, z_outer + 0.11, height=0.20, radius=0.035)

    # 8 Radial Spokes + 8 Suspension Chains for outer wheel
    for i in range(8):
        ang = (i / 8.0) * math.tau
        # Horizontal spoke to hub
        for r_step in range(4, int(r_outer / 0.04)):
            rw = r_step * 0.04
            vb.set_world(rw * math.cos(ang), rw * math.sin(ang), z_outer, "wrought_iron", 0.94)

        # Suspension chain rising from outer wheel (Z = 0.65) to upper hub (Z = 2.10)
        p0 = (r_outer * math.cos(ang), r_outer * math.sin(ang), z_outer + 0.10)
        p1 = (0.20 * math.cos(ang), 0.20 * math.sin(ang), 2.10)
        add_chain_voxel(vb, p0, p1, mat_key="wrought_iron", sag=0.0)

    # 3. Upper Inner Tiered Wheel (Radius = 0.72m at Z = 1.25m, 8 segments + 8 candles)
    r_inner = 0.72
    z_inner = 1.25
    vb.fill_world_cylinder_z(0.0, 0.0, z_inner - 0.06, z_inner + 0.06, r_inner + 0.05, r_inner - 0.05, "bronze", 1.02)
    for i in range(8):
        ang = (i / 8.0) * math.tau
        vx = r_inner * math.cos(ang)
        vy = r_inner * math.sin(ang)
        vb.fill_world_box(vx - 0.08, vx + 0.08, vy - 0.08, vy + 0.08, z_inner + 0.06, z_inner + 0.10, "bronze", 1.05)
        add_candle_voxel(vb, vx, vy, z_inner + 0.10, height=0.18, radius=0.032)
        # Spoke to center column
        for r_step in range(3, int(r_inner / 0.04)):
            rw = r_step * 0.04
            vb.set_world(rw * math.cos(ang), rw * math.sin(ang), z_inner, "bronze", 0.98)

    vb.build_mesh_object()
    out_path = os.path.join(out_dir, "ossuary_bone_chandelier.glb")
    export_environment_glb(out_path)
    print(f"[Wave1C] Exported -> {out_path}")


# ==============================================================================
# 5. ossuary_spine_reliquary_monolith.glb (Tall Floor Centerpiece - 3.4m tall)
# ==============================================================================
def build_ossuary_spine_reliquary_monolith(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    vb = EnvironmentVoxelBuilder(
        name="ossuary_spine_reliquary_monolith",
        voxel_size=0.035,
        palette=palette,
        pivot_xyz=(0.0, 0.0, 0.0),
    )

    # 1. Stepped Octagonal Stone Plinth Base (Z = 0.0 to 0.72m)
    vb.fill_world_cylinder_z(0.0, 0.0, 0.0, 0.24, 0.82, 0.0, "weathered_stone", 0.92, octagonal=True)
    vb.fill_world_cylinder_z(0.0, 0.0, 0.24, 0.48, 0.68, 0.0, "carved_stone_trim", 1.0, octagonal=True)
    vb.fill_world_cylinder_z(0.0, 0.0, 0.48, 0.72, 0.55, 0.0, "carved_stone_trim", 1.04, octagonal=True)

    # 4 Corner Guardian Skulls & candles on plinth ledge (Z = 0.72m)
    for i in range(4):
        ang = (i / 4.0) * math.tau + math.pi * 0.25
        rx = 0.58 * math.cos(ang)
        ry = 0.58 * math.sin(ang)
        add_skull_voxel(vb, rx, ry, 0.78, scale=0.95, rot_z=ang + math.pi * 0.5)

        ang_c = (i / 4.0) * math.tau
        add_candle_voxel(vb, 0.62 * math.cos(ang_c), 0.62 * math.sin(ang_c), 0.72, height=0.20, radius=0.034)

    # 2. 8 Wrought-Iron Reliquary Cage Vertical Ribs rising from Z = 0.72m to Z = 3.05m
    for i in range(8):
        ang = (i / 8.0) * math.tau
        rx = 0.44 * math.cos(ang)
        ry = 0.44 * math.sin(ang)
        vb.fill_world_box(rx - 0.035, rx + 0.035, ry - 0.035, ry + 0.035, 0.72, 3.05, "wrought_iron", 0.92)

    # Iron hoop straps around cage ribs at 4 heights
    for hz in (1.05, 1.65, 2.25, 2.85):
        vb.fill_world_cylinder_z(0.0, 0.0, hz - 0.04, hz + 0.04, 0.46, 0.42, "wrought_iron", 1.0)

    # 3. Towering Fused Vertebrae Spine Column inside the cage (18 articulated vertebrae)
    for vi in range(18):
        vz = 0.80 + vi * 0.125
        twist = vi * 0.22
        # Vertebral centrum body
        vb.fill_world_cylinder_z(0.0, 0.0, vz - 0.045, vz + 0.045, 0.15, 0.0, "bone", 1.0)
        # Transverse bone processes
        cos_t = math.cos(twist)
        sin_t = math.sin(twist)
        for d in (-0.22, 0.22):
            vb.set_world(d * cos_t, d * sin_t, vz, "bone", 1.05)
            vb.set_world(-d * sin_t, d * cos_t, vz, "bone", 1.05)

    # 4. Blazing Crimson Soul Core at heart of monolith (Z = 1.95m)
    vb.fill_world_box(-0.16, 0.16, -0.16, 0.16, 1.75, 2.15, "crimson", 1.2)
    vb.fill_world_cylinder_z(0.0, 0.0, 1.82, 2.08, 0.20, 0.0, "crimson", 1.25)

    # 3 Orbiting Tarnished-Brass Astrolabe Rings around upper monolith
    for r_ast, r_z, rot_off in ((0.62, 1.95, 0.0), (0.68, 2.02, 0.4), (0.56, 1.88, -0.4)):
        vb.fill_world_cylinder_z(0.0, 0.0, r_z - 0.025, r_z + 0.025, r_ast + 0.03, r_ast - 0.03, "bronze", 1.05)

    # 5. Crown Reliquary Cap & 4 Horned Skull Effigies at Z = 3.05m..3.42m
    vb.fill_world_box(-0.38, 0.38, -0.38, 0.38, 3.05, 3.18, "carved_stone_trim", 1.04)
    vb.fill_world_cylinder_z(0.0, 0.0, 3.18, 3.42, 0.10, 0.0, "wrought_iron", 0.95)
    vb.set_world(0.0, 0.0, 3.44, "bronze", 1.1)

    for i in range(4):
        ang = (i / 4.0) * math.tau
        add_skull_voxel(vb, 0.36 * math.cos(ang), 0.36 * math.sin(ang), 3.16, scale=0.90, rot_z=ang + math.pi * 0.5)

    vb.build_mesh_object()
    out_path = os.path.join(out_dir, "ossuary_spine_reliquary_monolith.glb")
    export_environment_glb(out_path)
    print(f"[Wave1C] Exported -> {out_path}")


# ==============================================================================
# 6. ossuary_burial_niche_divider_4x4.glb (Interior Cover/Maze Wall - 3.2m x 2.8m)
# ==============================================================================
def build_ossuary_burial_niche_divider_4x4(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    vb = EnvironmentVoxelBuilder(
        name="ossuary_burial_niche_divider_4x4",
        voxel_size=0.035,
        palette=palette,
        pivot_xyz=(0.0, 0.0, 0.0),
    )

    # 1. Stepped Stone Base Plinth (3.28m W along X, 0.62m D along Y, 0.36m tall)
    vb.fill_world_box(-1.64, 1.64, -0.31, 0.31, 0.0, 0.18, "weathered_stone", 0.92)
    vb.fill_world_box(-1.60, 1.60, -0.27, 0.27, 0.18, 0.36, "carved_stone_trim", 1.0)

    # 2. Twin Outer Stone End-Piers at X = -1.46 and +1.46 (height 2.80m)
    for sx in (-1.46, 1.46):
        vb.fill_world_box(sx - 0.18, sx + 0.18, -0.28, 0.28, 0.36, 2.65, "weathered_stone", 0.95)
        vb.fill_world_box(sx - 0.21, sx + 0.21, -0.31, 0.31, 2.65, 2.80, "carved_stone_trim", 1.04)
        add_skull_voxel(vb, sx, 0.0, 2.86, scale=0.92, rot_z=0.0)

    # 3. Central Open Barred Iron Window Frame (X in [-0.52, +0.52], Z in [1.05, 2.35])
    # Jamb pillars flanking center window at X = -0.56 and +0.56
    for jx in (-0.56, 0.56):
        vb.fill_world_box(jx - 0.09, jx + 0.09, -0.26, 0.26, 0.36, 2.60, "carved_stone_trim", 1.0)

    # Window sill & lintel
    vb.fill_world_box(-0.62, 0.62, -0.28, 0.28, 0.98, 1.08, "carved_stone_trim", 1.02)
    vb.fill_world_box(-0.62, 0.62, -0.28, 0.28, 2.32, 2.44, "carved_stone_trim", 1.02)

    # Lower center masonry panel below window (Z = 0.36 to 0.98)
    vb.fill_world_box(-0.52, 0.52, -0.22, 0.22, 0.36, 0.98, "weathered_stone", 0.94)

    # 5 Vertical Wrought-Iron Window Bars + 2 Crossbars inside window opening
    for bi in range(5):
        bx = -0.36 + bi * 0.18
        vb.fill_world_cylinder_z(bx, 0.0, 1.08, 2.32, 0.02, 0.0, "wrought_iron", 0.9)
    for bz in (1.42, 1.98):
        vb.fill_world_box(-0.52, 0.52, -0.03, 0.03, bz - 0.025, bz + 0.025, "wrought_iron", 0.9)

    # 4. Left & Right Burial Niche Bays (X centered at -1.01 and +1.01, 4 vertical tiers each)
    for bay_x in (-1.01, 1.01):
        # Spine wall inside niche bay
        vb.fill_world_box(bay_x - 0.36, bay_x + 0.36, -0.14, 0.14, 0.36, 2.56, "weathered_stone", 0.92)

        for tier in range(4):
            tz = 0.55 + tier * 0.52
            # Stone niche shelf
            vb.fill_world_box(bay_x - 0.38, bay_x + 0.38, -0.25, 0.25, tz - 0.14, tz - 0.06, "carved_stone_trim", 1.0)
            # Skulls on front (-Y) and back (+Y) per shelf tier
            for off_x in (-0.18, 0.18):
                add_skull_voxel(vb, bay_x + off_x, -0.16, tz, scale=0.80, rot_z=0.0)
                add_skull_voxel(vb, bay_x + off_x, 0.16, tz, scale=0.80, rot_z=math.pi)

    # 5. Top Stepped Cornice along Z = 2.56..2.85m
    vb.fill_world_box(-1.61, 1.61, -0.27, 0.27, 2.56, 2.70, "weathered_stone", 0.95)
    vb.fill_world_box(-1.64, 1.64, -0.30, 0.30, 2.70, 2.85, "carved_stone_trim", 1.04)

    # 6 Melted Tallow Candles along window sill and top cornice ledge
    for cx in (-0.32, 0.0, 0.32):
        add_candle_voxel(vb, cx, -0.22, 1.08, height=0.15, radius=0.028)
        add_candle_voxel(vb, cx, 0.22, 1.08, height=0.15, radius=0.028)

    vb.build_mesh_object()
    out_path = os.path.join(out_dir, "ossuary_burial_niche_divider_4x4.glb")
    export_environment_glb(out_path)
    print(f"[Wave1C] Exported -> {out_path}")


# ==============================================================================
# 7. necropolis_wall_armory_4x4.glb (Biome 2: The Iron Necropolis)
# ==============================================================================
def build_necropolis_wall_armory_4x4(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    vb = EnvironmentVoxelBuilder(
        name="necropolis_wall_armory_4x4",
        voxel_size=0.04,
        palette=palette,
        pivot_xyz=(0.0, 0.0, 0.0),
    )

    # 1. Solid Core Wall Backing (Rule 9.4: solid 0.50m total wall thickness, Y in [-0.25, 0.25])
    vb.fill_world_box(-2.0, 2.0, -0.05, 0.25, 0.0, 4.0, "weathered_stone", 0.92)

    # Stepped lower plinths
    vb.fill_world_box(-2.0, 2.0, -0.25, 0.25, 0.0, 0.24, "carved_stone_trim", 1.0)
    vb.fill_world_box(-2.0, 2.0, -0.22, 0.22, 0.24, 0.46, "carved_stone_trim", 1.04)

    # Upper heavy cornices
    vb.fill_world_box(-2.0, 2.0, -0.22, 0.22, 3.55, 3.72, "carved_stone_trim", 1.0)
    vb.fill_world_box(-2.0, 2.0, -0.25, 0.25, 3.72, 4.0, "carved_stone_trim", 1.06)

    # 3 Vertical armored stone pilasters (X = -1.82, 0.0, +1.82)
    for px in (-1.82, 0.0, 1.82):
        vb.fill_world_box(px - 0.17, px + 0.17, -0.24, 0.24, 0.46, 3.55, "carved_stone_trim", 0.98)
        # Iron armor faceplate with rivets
        vb.fill_world_box(px - 0.11, px + 0.11, -0.26, -0.18, 0.60, 3.42, "wrought_iron", 1.0)
        for rz in range(7):
            vb.set_world(px, -0.27, 0.80 + rz * 0.40, "bronze", 1.1)

    # 2. Twin Armory Alcoves (Left X = -0.92, Right X = +0.92)
    for cx in (-0.92, 0.92):
        # Alcove arch framing voussoirs
        for v_i in range(9):
            ang = math.pi * (0.10 + 0.80 * (v_i / 8.0))
            vx = cx + math.cos(ang) * 0.62
            vz = 2.75 + math.sin(ang) * 0.52
            vb.fill_world_box(vx - 0.08, vx + 0.08, -0.20, -0.06, vz - 0.07, vz + 0.07, "carved_stone_trim", 1.02)

        # Portcullis vertical iron bars & bottom spikes
        for b_i in range(6):
            bx = cx - 0.50 + b_i * 0.20
            vb.fill_world_cylinder_z(bx, -0.14, 0.88, 2.75, 0.022, 0.0, "wrought_iron", 0.9)
            vb.fill_world_cylinder_z(bx, -0.14, 0.74, 0.88, 0.03, 0.0, "wrought_iron", 1.0)
            vb.set_world(bx, -0.14, 0.70, "wrought_iron", 1.1)

        # Horizontal portcullis cross-straps
        for hz in (1.15, 1.95, 2.65):
            vb.fill_world_box(cx - 0.58, cx + 0.58, -0.16, -0.12, hz - 0.035, hz + 0.035, "wrought_iron", 0.95)

        # Glowing cold-amber forge slits behind portcullis (Z = 1.35, 1.95, 2.55)
        for sz in (1.35, 1.95, 2.55):
            vb.fill_world_box(cx - 0.42, cx + 0.42, -0.08, -0.04, sz - 0.05, sz + 0.05, "candle_flame", 1.25)

        # Crossed Halberds mounted in front of alcove
        for h_dir in (-1, 1):
            tilt = h_dir * 0.42
            cos_t = math.cos(tilt)
            sin_t = math.sin(tilt)
            # Shaft
            for step in range(-14, 15):
                dist = step * 0.07
                hx = cx + dist * sin_t
                hz = 1.95 + dist * cos_t
                vb.set_world(hx, -0.22, hz, "charred_timber", 0.95)
            # Halberd axe head & spear point at upper tip
            tip_x = cx + 1.0 * sin_t
            tip_z = 1.95 + 1.0 * cos_t
            vb.fill_world_box(tip_x - 0.12, tip_x + 0.12, -0.24, -0.20, tip_z - 0.15, tip_z + 0.05, "wrought_iron", 1.0)
            vb.fill_world_cylinder_z(tip_x, -0.22, tip_z + 0.05, tip_z + 0.28, 0.035, 0.0, "wrought_iron", 1.05)
            vb.set_world(tip_x, -0.22, tip_z + 0.30, "wrought_iron", 1.1)

        # Central Riveted Tower Shield at the crossing
        vb.fill_world_box(cx - 0.28, cx + 0.28, -0.26, -0.22, 1.56, 2.34, "wrought_iron", 0.98)
        vb.fill_world_box(cx - 0.22, cx + 0.22, -0.28, -0.26, 1.64, 2.26, "bronze", 1.04)
        vb.fill_world_cylinder_y(cx, 1.95, -0.30, -0.27, 0.10, 0.0, "bronze", 1.1)

    vb.build_mesh_object()
    out_path = os.path.join(out_dir, "necropolis_wall_armory_4x4.glb")
    export_environment_glb(out_path)
    print(f"[Wave1C] Exported -> {out_path}")


# ==============================================================================
# 8. necropolis_iron_maiden_monolith.glb (Biome 2: The Iron Necropolis)
# ==============================================================================
def build_necropolis_iron_maiden_monolith(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    vb = EnvironmentVoxelBuilder(
        name="necropolis_iron_maiden_monolith",
        voxel_size=0.035,
        palette=palette,
        pivot_xyz=(0.0, 0.0, 0.0),
    )

    # 1. Stepped Octagonal War-Plinth (Z = 0.0 to 0.85m)
    vb.fill_world_cylinder_z(0.0, 0.0, 0.0, 0.32, 1.20, 0.0, "weathered_stone", 0.92, octagonal=True)
    vb.fill_world_cylinder_z(0.0, 0.0, 0.32, 0.60, 1.05, 0.0, "carved_stone_trim", 1.0, octagonal=True)
    vb.fill_world_cylinder_z(0.0, 0.0, 0.60, 0.85, 0.90, 0.0, "wrought_iron", 0.95, octagonal=True)

    # 2. Towering Iron Maiden Sarcophagus Body & Crown (Z = 0.85m to 3.80m)
    # Lower Torso (Z = 0.85 to 2.10)
    vb.fill_world_cylinder_z(0.0, 0.0, 0.85, 2.10, 0.70, 0.0, "wrought_iron", 0.96, octagonal=True)
    # Upper Torso (Z = 2.10 to 2.95)
    vb.fill_world_cylinder_z(0.0, 0.0, 2.10, 2.95, 0.64, 0.0, "wrought_iron", 0.98, octagonal=True)
    # Helm (Z = 2.95 to 3.50)
    vb.fill_world_cylinder_z(0.0, 0.0, 2.95, 3.50, 0.46, 0.0, "wrought_iron", 1.0, octagonal=True)
    # Top Spire (Z = 3.50 to 3.80)
    vb.fill_world_cylinder_z(0.0, 0.0, 3.50, 3.80, 0.16, 0.0, "bronze", 1.05, octagonal=True)
    vb.set_world(0.0, 0.0, 3.82, "bronze", 1.15)

    # Glowing amber eye/visor slits on 4 cardinal faces
    for i in range(4):
        ang = i * (math.pi * 0.5)
        vx = math.cos(ang) * 0.44
        vy = math.sin(ang) * 0.44
        vb.fill_world_box(vx - 0.12, vx + 0.12, vy - 0.05, vy + 0.05, 3.20, 3.28, "candle_flame", 1.3)

        # Chest slits
        cx = math.cos(ang) * 0.64
        cy = math.sin(ang) * 0.64
        vb.fill_world_box(cx - 0.09, cx + 0.09, cy - 0.05, cy + 0.05, 1.85, 2.45, "candle_flame", 1.25)

    # 3. 4 Spiked Greatswords & 4 Forge-Brazier Basins at the corners
    for i in range(4):
        # Diagonal Greatswords
        ang = i * (math.pi * 0.5) + math.pi * 0.25
        sx = math.cos(ang) * 0.84
        sy = math.sin(ang) * 0.84
        # Blade (Z = 1.05 to 2.90)
        vb.fill_world_box(sx - 0.08, sx + 0.08, sy - 0.03, sy + 0.03, 1.05, 2.90, "wrought_iron", 1.0)
        # Crossguard at Z = 2.75
        vb.fill_world_box(sx - 0.26, sx + 0.26, sy - 0.05, sy + 0.05, 2.70, 2.78, "bronze", 1.05)
        # Grip & pommel
        vb.fill_world_cylinder_z(sx, sy, 2.78, 3.18, 0.03, 0.0, "charred_timber", 0.95)
        vb.fill_world_cylinder_z(sx, sy, 3.18, 3.28, 0.06, 0.0, "bronze", 1.1)

        # Cardinal Forge-Brazier Basins
        c_ang = i * (math.pi * 0.5)
        bx = math.cos(c_ang) * 0.96
        by = math.sin(c_ang) * 0.96
        vb.fill_world_cylinder_z(bx, by, 0.35, 0.85, 0.20, 0.0, "carved_stone_trim", 1.0, octagonal=True)
        vb.fill_world_cylinder_z(bx, by, 0.85, 1.10, 0.28, 0.0, "wrought_iron", 0.95)
        vb.fill_world_cylinder_z(bx, by, 1.10, 1.25, 0.22, 0.0, "candle_flame", 1.3)

    # 4. Heavy 3D Chain Links wrapping sarcophagus
    for i in range(4):
        ang1 = i * (math.pi * 0.5)
        ang2 = (i + 1) * (math.pi * 0.5)
        p_start = (math.cos(ang1) * 0.74, math.sin(ang1) * 0.74, 1.25)
        p_end = (math.cos(ang2) * 0.68, math.sin(ang2) * 0.68, 2.65)
        add_chain_voxel(vb, p_start, p_end, mat_key="wrought_iron", sag=0.0)

    # 5. Spiked iron bands around sarcophagus (Z = 1.20, 1.85, 2.50)
    for z_band in (1.20, 1.85, 2.50):
        vb.fill_world_cylinder_z(0.0, 0.0, z_band - 0.05, z_band + 0.05, 0.74, 0.68, "bronze", 1.02, octagonal=True)

    vb.build_mesh_object()
    out_path = os.path.join(out_dir, "necropolis_iron_maiden_monolith.glb")
    export_environment_glb(out_path)
    print(f"[Wave1C] Exported -> {out_path}")


# ==============================================================================
# 9. necropolis_hanging_war_brazier.glb (Biome 2: The Iron Necropolis)
# ==============================================================================
def build_necropolis_hanging_war_brazier(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    vb = EnvironmentVoxelBuilder(
        name="necropolis_hanging_war_brazier",
        voxel_size=0.035,
        palette=palette,
        pivot_xyz=(0.0, 0.0, 0.0),
    )

    # 1. Ceiling anchor mount at Z = 0.0, hanging down to Z = -1.75m
    vb.fill_world_cylinder_z(0.0, 0.0, -0.12, 0.0, 0.22, 0.0, "wrought_iron", 0.95, octagonal=True)
    vb.fill_world_cylinder_z(0.0, 0.0, -1.15, -0.12, 0.04, 0.0, "wrought_iron", 0.92)

    # 2. Outer War-Ring & Brass Trim at Z = -1.20m (Radius = 0.78m)
    r_war = 0.78
    z_war = -1.20
    vb.fill_world_cylinder_z(0.0, 0.0, z_war - 0.06, z_war + 0.06, r_war + 0.06, r_war - 0.06, "wrought_iron", 0.96)
    vb.fill_world_cylinder_z(0.0, 0.0, z_war + 0.04, z_war + 0.08, r_war + 0.03, r_war - 0.03, "bronze", 1.05)

    # Inner Coal Basket & Glowing Ember Core at Z = -1.35m
    r_coal = 0.46
    vb.fill_world_cylinder_z(0.0, 0.0, z_war - 0.22, z_war - 0.06, r_coal, 0.0, "wrought_iron", 0.92, octagonal=True)
    vb.fill_world_cylinder_z(0.0, 0.0, z_war - 0.10, z_war + 0.10, r_coal - 0.08, 0.0, "candle_flame", 1.3)

    # Bottom finial drop spike at Z = -1.65m
    vb.fill_world_cylinder_z(0.0, 0.0, -1.65, z_war - 0.22, 0.10, 0.0, "bronze", 1.05, octagonal=True)
    vb.set_world(0.0, 0.0, -1.68, "bronze", 1.15)

    # 3. 4 Radial suspension chains from ceiling mount (Z = -0.10) to outer war-ring (Z = -1.16)
    for i in range(4):
        ang = i * (math.pi * 0.5)
        p0 = (0.12 * math.cos(ang), 0.12 * math.sin(ang), -0.10)
        p1 = (r_war * math.cos(ang), r_war * math.sin(ang), z_war + 0.04)
        add_chain_voxel(vb, p0, p1, mat_key="wrought_iron", sag=0.0)

    # 4. 12 Perimeter war-spikes + 12 glowing flame pods + 12 radial spokes
    for i in range(12):
        ang = i * (2.0 * math.pi / 12.0)
        rx = r_war * math.cos(ang)
        ry = r_war * math.sin(ang)

        # Downward spike
        vb.fill_world_cylinder_z(rx, ry, z_war - 0.26, z_war - 0.06, 0.035, 0.0, "wrought_iron", 0.9)
        vb.set_world(rx, ry, z_war - 0.28, "wrought_iron", 1.05)

        # Upward glowing flame tip
        vb.fill_world_cylinder_z(rx, ry, z_war + 0.06, z_war + 0.20, 0.035, 0.0, "candle_flame", 1.25)

        # Spoke to central hub
        for r_step in range(3, int(r_war / 0.04)):
            rw = r_step * 0.04
            vb.set_world(rw * math.cos(ang), rw * math.sin(ang), z_war, "wrought_iron", 0.94)

    vb.build_mesh_object()
    out_path = os.path.join(out_dir, "necropolis_hanging_war_brazier.glb")
    export_environment_glb(out_path)
    print(f"[Wave1C] Exported -> {out_path}")


# ==============================================================================
# 10. reliquary_wall_grimoire_4x4.glb (Biome 3: The Astral Reliquary)
# ==============================================================================
def build_reliquary_wall_grimoire_4x4(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    vb = EnvironmentVoxelBuilder(
        name="reliquary_wall_grimoire_4x4",
        voxel_size=0.04,
        palette=palette,
        pivot_xyz=(0.0, 0.0, 0.0),
    )

    # 1. Solid Core Wall Backing (Rule 9.4: solid 0.50m total wall thickness, Y in [-0.25, 0.25])
    vb.fill_world_box(-2.0, 2.0, -0.05, 0.25, 0.0, 4.0, "weathered_stone", 0.92)

    # Stepped plinth & upper cornice
    vb.fill_world_box(-2.0, 2.0, -0.25, 0.25, 0.0, 0.24, "carved_stone_trim", 1.0)
    vb.fill_world_box(-2.0, 2.0, -0.22, 0.22, 0.24, 0.44, "carved_stone_trim", 1.02)
    vb.fill_world_box(-2.0, 2.0, -0.25, 0.25, 3.72, 4.0, "carved_stone_trim", 1.06)

    # 4 Library Pilasters (X = -1.85, -0.62, +0.62, +1.85)
    for px in (-1.85, -0.62, 0.62, 1.85):
        vb.fill_world_box(px - 0.13, px + 0.13, -0.23, 0.23, 0.44, 3.72, "carved_stone_trim", 0.98)
        # Brass inlay strip
        vb.fill_world_box(px - 0.04, px + 0.04, -0.25, -0.21, 0.60, 3.55, "bronze", 1.05)

    # 2. 3 Horizontal Library Shelves across Left & Right Alcoves
    for cx in (-1.24, 1.24):
        for sz in (0.95, 1.75, 2.55, 3.25):
            vb.fill_world_box(cx - 0.48, cx + 0.48, -0.20, 0.0, sz - 0.04, sz + 0.04, "charred_timber", 0.92)
            vb.fill_world_box(cx - 0.48, cx + 0.48, -0.24, -0.20, sz - 0.02, sz + 0.02, "bronze", 1.05)

    # 3. 36 Chained Occult Tomes & Grimoires on shelves (18 per side)
    for cx in (-1.24, 1.24):
        for s_idx, sz in enumerate((1.16, 1.96, 2.76)):
            for b_i in range(6):
                bx = cx - 0.38 + b_i * 0.15
                h_var = 0.26 + ((b_i + s_idx) % 3) * 0.04
                cover_mat = "charred_timber" if (b_i % 2 == 0) else "wrought_iron"
                # Book cover block
                vb.fill_world_box(bx - 0.05, bx + 0.05, -0.19, -0.06, sz - h_var * 0.5, sz + h_var * 0.5, cover_mat, 0.95)
                # Pages
                vb.fill_world_box(bx - 0.035, bx + 0.035, -0.21, -0.17, sz - h_var * 0.45, sz + h_var * 0.45, "bone", 1.02)
                # Brass chain link
                vb.set_world(bx, -0.22, sz, "bronze", 1.1)

    # 4. Central Astral Astrolabe Relief & Glowing Violet Rune Inlays (Z = 2.10)
    vb.fill_world_cylinder_y(0.0, 2.10, -0.24, -0.16, 0.48, 0.42, "bronze", 1.05)
    vb.fill_world_cylinder_y(0.0, 2.10, -0.25, -0.18, 0.30, 0.24, "bronze", 1.05)
    # Center crystal
    vb.fill_world_cylinder_y(0.0, 2.10, -0.26, -0.20, 0.10, 0.0, "occult_rune", 1.3)

    # 12 Radial Spokes & Rune Inlays
    for r_i in range(12):
        ang = r_i * (2.0 * math.pi / 12.0)
        rx = math.cos(ang) * 0.38
        rz = 2.10 + math.sin(ang) * 0.38
        vb.set_world(rx, -0.22, rz, "bronze", 1.08)
        # Violet rune
        r_rune_x = math.cos(ang) * 0.52
        r_rune_z = 2.10 + math.sin(ang) * 0.52
        vb.fill_world_box(r_rune_x - 0.04, r_rune_x + 0.04, -0.22, -0.18, r_rune_z - 0.04, r_rune_z + 0.04, "occult_rune", 1.3)

    # Lower central scroll niches (Z = 1.05 to 1.35)
    for sc_i in range(8):
        sx = -0.32 + (sc_i % 4) * 0.21
        sz = 1.08 + (sc_i // 4) * 0.22
        vb.fill_world_cylinder_y(sx, sz, -0.22, -0.06, 0.045, 0.0, "bone", 1.0)
        vb.set_world(sx, -0.23, sz, "bronze", 1.1)

    vb.build_mesh_object()
    out_path = os.path.join(out_dir, "reliquary_wall_grimoire_4x4.glb")
    export_environment_glb(out_path)
    print(f"[Wave1C] Exported -> {out_path}")


# ==============================================================================
# 11. reliquary_astral_orrery_monolith.glb (Biome 3: The Astral Reliquary)
# ==============================================================================
def build_reliquary_astral_orrery_monolith(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    vb = EnvironmentVoxelBuilder(
        name="reliquary_astral_orrery_monolith",
        voxel_size=0.035,
        palette=palette,
        pivot_xyz=(0.0, 0.0, 0.0),
    )

    # 1. Stepped Obsidian & Brass Plinth Base (Z = 0.0 to 1.45m)
    vb.fill_world_cylinder_z(0.0, 0.0, 0.0, 0.36, 1.28, 0.0, "weathered_stone", 0.92, octagonal=True)
    vb.fill_world_cylinder_z(0.0, 0.0, 0.36, 0.70, 1.10, 0.0, "carved_stone_trim", 1.0, octagonal=True)
    vb.fill_world_cylinder_z(0.0, 0.0, 0.70, 0.95, 0.94, 0.0, "bronze", 1.04, octagonal=True)
    vb.fill_world_cylinder_z(0.0, 0.0, 0.95, 1.80, 0.50, 0.0, "weathered_stone", 0.95, octagonal=True)

    # 8 Arcane Violet Rune Inlays & Plinth Obelisks around column
    for i in range(8):
        ang = i * (2.0 * math.pi / 8.0)
        rx = math.cos(ang) * 0.48
        ry = math.sin(ang) * 0.48
        vb.fill_world_box(rx - 0.04, rx + 0.04, ry - 0.04, ry + 0.04, 1.15, 1.65, "occult_rune", 1.35)

        ox = math.cos(ang) * 1.05
        oy = math.sin(ang) * 1.05
        vb.fill_world_cylinder_z(ox, oy, 0.70, 1.25, 0.10, 0.0, "bronze", 1.05, octagonal=True)
        vb.set_world(ox, oy, 1.28, "gold", 1.15)

    # 2. Multi-Ringed Brass Celestial Astrolabe centered at Z = 2.65m
    center_z = 2.65
    ring_radii = (1.08, 0.96, 0.84, 0.72, 0.58, 0.44)
    for idx, r_maj in enumerate(ring_radii):
        mat_k = "gold" if (idx % 2 == 0) else "bronze"
        vb.fill_world_cylinder_z(0.0, 0.0, center_z - 0.03, center_z + 0.03, r_maj + 0.03, r_maj - 0.03, mat_k, 1.06)

    # Central Crystalline Soul-Pillar & Twin Cones
    vb.fill_world_cylinder_z(0.0, 0.0, center_z - 0.35, center_z + 0.35, 0.20, 0.0, "occult_rune", 1.35, octagonal=True)
    vb.fill_world_cylinder_z(0.0, 0.0, 3.50, 3.85, 0.12, 0.0, "bronze", 1.05, octagonal=True)
    vb.set_world(0.0, 0.0, 3.88, "gold", 1.2)

    # 4 Curved Cradle Buttresses at diagonal quadrants
    for i in range(4):
        ang = i * (math.pi * 0.5)
        bx = math.cos(ang) * 0.88
        by = math.sin(ang) * 0.88
        vb.fill_world_box(bx - 0.08, bx + 0.08, by - 0.08, by + 0.08, 1.0, 2.70, "wrought_iron", 0.94)

        # Support chain
        p0 = (bx, by, 1.10)
        p1 = (math.cos(ang + 0.5) * 0.48, math.sin(ang + 0.5) * 0.48, 2.05)
        add_chain_voxel(vb, p0, p1, mat_key="bronze", sag=0.0)

    # 16 Planetary shards & degree ticks around outer ring
    for i in range(16):
        ang = i * (2.0 * math.pi / 16.0)
        tx = math.cos(ang) * 1.12
        ty = math.sin(ang) * 1.12
        vb.set_world(tx, ty, center_z, "gold", 1.1)

        if i % 2 == 0:
            orb_r = 0.75 + (i % 4) * 0.10
            oz = center_z + math.sin(ang * 2.0) * 0.28
            orb_mat = "occult_rune" if (i % 4 == 0) else "bronze"
            vb.fill_world_cylinder_z(math.cos(ang) * orb_r, math.sin(ang) * orb_r, oz - 0.05, oz + 0.05, 0.06, 0.0, orb_mat, 1.25)

    vb.build_mesh_object()
    out_path = os.path.join(out_dir, "reliquary_astral_orrery_monolith.glb")
    export_environment_glb(out_path)
    print(f"[Wave1C] Exported -> {out_path}")


# ==============================================================================
# 12. reliquary_chandelier_astrolabe.glb (Biome 3: The Astral Reliquary)
# ==============================================================================
def build_reliquary_chandelier_astrolabe(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    vb = EnvironmentVoxelBuilder(
        name="reliquary_chandelier_astrolabe",
        voxel_size=0.035,
        palette=palette,
        pivot_xyz=(0.0, 0.0, 0.0),
    )

    # 1. Ceiling mount rose at Z = 0.0, hanging down to Z = -1.80m
    vb.fill_world_cylinder_z(0.0, 0.0, -0.12, 0.0, 0.24, 0.0, "bronze", 1.05, octagonal=True)
    vb.fill_world_cylinder_z(0.0, 0.0, -1.50, -0.12, 0.035, 0.0, "bronze", 1.0)

    # 2. Concentric Brass Rings at Z = -1.18m
    r_outer = 0.88
    r_mid = 0.58
    z_ring = -1.18
    vb.fill_world_cylinder_z(0.0, 0.0, z_ring - 0.04, z_ring + 0.04, r_outer + 0.04, r_outer - 0.04, "bronze", 1.05)
    vb.fill_world_cylinder_z(0.0, 0.0, z_ring + 0.12, z_ring + 0.18, r_mid + 0.03, r_mid - 0.03, "gold", 1.1)

    # Central violet crystal pendulum at Z = -1.58m
    vb.fill_world_cylinder_z(0.0, 0.0, -1.68, -1.45, 0.15, 0.0, "occult_rune", 1.35, octagonal=True)
    vb.set_world(0.0, 0.0, -1.72, "occult_rune", 1.4)

    # 3. 4 Suspension chains from ceiling rose (Z = -0.10) to outer ring (Z = -1.15)
    for i in range(4):
        ang = i * (math.pi * 0.5)
        p0 = (0.12 * math.cos(ang), 0.12 * math.sin(ang), -0.10)
        p1 = (r_outer * math.cos(ang), r_outer * math.sin(ang), z_ring + 0.04)
        add_chain_voxel(vb, p0, p1, mat_key="bronze", sag=0.0)

    # 4. 14 Floating Violet Crystal Prisms + Brass Holders + Radial Spokes
    for i in range(14):
        ang = i * (2.0 * math.pi / 14.0)
        rx = r_outer * math.cos(ang)
        ry = r_outer * math.sin(ang)

        # Upper crystal shard
        vb.fill_world_cylinder_z(rx, ry, z_ring + 0.06, z_ring + 0.22, 0.045, 0.0, "occult_rune", 1.3)
        # Lower crystal shard
        vb.fill_world_cylinder_z(rx, ry, z_ring - 0.22, z_ring - 0.06, 0.045, 0.0, "occult_rune", 1.3)
        # Spoke to hub
        for r_step in range(2, int(r_outer / 0.04)):
            rw = r_step * 0.04
            vb.set_world(rw * math.cos(ang), rw * math.sin(ang), z_ring, "bronze", 1.02)

    vb.build_mesh_object()
    out_path = os.path.join(out_dir, "reliquary_chandelier_astrolabe.glb")
    export_environment_glb(out_path)
    print(f"[Wave1C] Exported -> {out_path}")


# ==============================================================================
# 13. abattoir_wall_furnace_4x4.glb (Biome 4: The Blood-Forged Abattoir)
# ==============================================================================
def build_abattoir_wall_furnace_4x4(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    vb = EnvironmentVoxelBuilder(
        name="abattoir_wall_furnace_4x4",
        voxel_size=0.04,
        palette=palette,
        pivot_xyz=(0.0, 0.0, 0.0),
    )

    # 1. Solid Core Wall Backing (Rule 9.4: solid 0.50m total wall thickness, Y in [-0.25, 0.25])
    vb.fill_world_box(-2.0, 2.0, -0.05, 0.25, 0.0, 4.0, "weathered_stone", 0.90)

    # Brutalist lower iron plinth & upper cornice
    vb.fill_world_box(-2.0, 2.0, -0.25, 0.25, 0.0, 0.44, "wrought_iron", 0.96)
    vb.fill_world_box(-2.0, 2.0, -0.25, 0.25, 3.68, 4.0, "wrought_iron", 0.98)

    # 5 Vertical wrought-iron ribs (X = -1.84, -0.92, 0.0, 0.92, 1.84)
    for rx in (-1.84, -0.92, 0.0, 0.92, 1.84):
        vb.fill_world_box(rx - 0.11, rx + 0.11, -0.24, 0.24, 0.44, 3.68, "wrought_iron", 0.94)

    # 2. 4 Recessed Furnace Chambers (X = -1.38, -0.46, +0.46, +1.38)
    for fx in (-1.38, -0.46, 0.46, 1.38):
        # Searing crimson glow
        vb.fill_world_box(fx - 0.33, fx + 0.33, -0.10, -0.04, 0.65, 2.25, "crimson", 1.3)

        # 4 Vertical heavy grate bars
        for b_i in range(4):
            bx = fx - 0.24 + b_i * 0.16
            vb.fill_world_cylinder_z(bx, -0.16, 0.65, 2.25, 0.024, 0.0, "wrought_iron", 0.92)

        # Horizontal grate crossbars
        for gz in (0.95, 1.45, 1.95):
            vb.fill_world_box(fx - 0.36, fx + 0.36, -0.18, -0.14, gz - 0.03, gz + 0.03, "wrought_iron", 0.95)

    # 3. 4 Skull-Crusher Cogwheels in Upper Frieze (Z = 2.95m)
    for gx in (-1.38, -0.46, 0.46, 1.38):
        vb.fill_world_cylinder_y(gx, 2.95, -0.22, -0.16, 0.32, 0.24, "wrought_iron", 0.96)
        vb.fill_world_cylinder_y(gx, 2.95, -0.24, -0.18, 0.11, 0.0, "bronze", 1.05)
        # 8 Cogwheel teeth
        for t_i in range(8):
            ang = t_i * (2.0 * math.pi / 8.0)
            tx = gx + math.cos(ang) * 0.34
            tz = 2.95 + math.sin(ang) * 0.34
            vb.fill_world_box(tx - 0.04, tx + 0.04, -0.22, -0.16, tz - 0.04, tz + 0.04, "wrought_iron", 1.0)

    # 4. Hanging Meat-Hook Chains across the bays (Z = 2.85 to 1.15)
    for cx in (-1.38, -0.46, 0.46, 1.38):
        p0 = (cx, -0.24, 2.85)
        p1 = (cx, -0.24, 1.25)
        add_chain_voxel(vb, p0, p1, mat_key="wrought_iron", sag=0.0)
        # Hook shank & point
        vb.fill_world_cylinder_z(cx, -0.26, 1.02, 1.25, 0.025, 0.0, "wrought_iron", 0.92)
        vb.fill_world_box(cx - 0.04, cx + 0.04, -0.32, -0.26, 1.00, 1.08, "bronze", 1.1)
        vb.set_world(cx, -0.34, 1.12, "bronze", 1.2)

    vb.build_mesh_object()
    out_path = os.path.join(out_dir, "abattoir_wall_furnace_4x4.glb")
    export_environment_glb(out_path)
    print(f"[Wave1C] Exported -> {out_path}")


# ==============================================================================
# 14. abattoir_blood_press_monolith.glb (Biome 4: The Blood-Forged Abattoir)
# ==============================================================================
def build_abattoir_blood_press_monolith(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    vb = EnvironmentVoxelBuilder(
        name="abattoir_blood_press_monolith",
        voxel_size=0.035,
        palette=palette,
        pivot_xyz=(0.0, 0.0, 0.0),
    )

    # 1. Heavy Cast-Iron & Stone Blood-Trough Base (Z = 0.0 to 0.70m)
    vb.fill_world_cylinder_z(0.0, 0.0, 0.0, 0.36, 1.25, 0.0, "weathered_stone", 0.90, octagonal=True)
    vb.fill_world_cylinder_z(0.0, 0.0, 0.36, 0.70, 1.10, 0.0, "wrought_iron", 0.95, octagonal=True)

    # Heavy press platen at Z = 2.15 (radius 0.86m) & Top Crown at Z = 3.35 (radius 0.92m)
    vb.fill_world_cylinder_z(0.0, 0.0, 2.05, 2.25, 0.86, 0.0, "wrought_iron", 0.96, octagonal=True)
    vb.fill_world_cylinder_z(0.0, 0.0, 3.25, 3.45, 0.92, 0.0, "wrought_iron", 0.98, octagonal=True)

    # 2. Giant Central Screw-Spindle with Helical Threads (Z = 0.70 to 3.50)
    vb.fill_world_cylinder_z(0.0, 0.0, 0.70, 3.50, 0.18, 0.0, "wrought_iron", 0.94)
    for t_i in range(16):
        tz = 0.95 + t_i * 0.14
        vb.fill_world_cylinder_z(0.0, 0.0, tz - 0.02, tz + 0.02, 0.22, 0.17, "bronze", 1.05)

    # Top Turn-Wheel at Z = 3.62 (radius 0.72m)
    vb.fill_world_cylinder_z(0.0, 0.0, 3.58, 3.66, 0.72, 0.64, "wrought_iron", 0.96)
    for w_i in range(8):
        ang = w_i * (2.0 * math.pi / 8.0)
        for r_step in range(3, int(0.72 / 0.04)):
            rw = r_step * 0.04
            vb.set_world(rw * math.cos(ang), rw * math.sin(ang), 3.62, "bronze", 1.05)

    # 3. 4 Crimson Glass Collection Vats (radius 0.68m, Z = 0.82 to 1.95)
    for i in range(4):
        ang = i * (math.pi * 0.5)
        vx = math.cos(ang) * 0.68
        vy = math.sin(ang) * 0.68
        vb.fill_world_cylinder_z(vx, vy, 0.85, 1.95, 0.22, 0.0, "crimson", 1.35)
        vb.fill_world_cylinder_z(vx, vy, 0.80, 0.85, 0.25, 0.0, "bronze", 1.05)
        vb.fill_world_cylinder_z(vx, vy, 1.95, 2.00, 0.25, 0.0, "bronze", 1.05)

        # 4 Corner Guide Pillars & Gargoyle Drainage Spouts
        c_ang = ang + math.pi * 0.25
        cx = math.cos(c_ang) * 0.84
        cy = math.sin(c_ang) * 0.84
        vb.fill_world_box(cx - 0.09, cx + 0.09, cy - 0.09, cy + 0.09, 0.70, 3.35, "wrought_iron", 0.94)

        # Spout & blood trough
        sx = math.cos(ang) * 1.02
        sy = math.sin(ang) * 1.02
        vb.fill_world_box(sx - 0.11, sx + 0.11, sy - 0.11, sy + 0.11, 0.65, 0.78, "carved_stone_trim", 1.0)
        vb.fill_world_box(sx - 0.06, sx + 0.06, sy - 0.06, sy + 0.06, 0.74, 0.80, "crimson", 1.3)

    # 4. Platen Crushing Spikes beneath platen (Z = 1.85 to 2.05)
    for s_i in range(12):
        s_ang = s_i * (2.0 * math.pi / 12.0)
        sp_x = math.cos(s_ang) * 0.62
        sp_y = math.sin(s_ang) * 0.62
        vb.fill_world_cylinder_z(sp_x, sp_y, 1.85, 2.05, 0.04, 0.0, "wrought_iron", 0.92)
        vb.set_world(sp_x, sp_y, 1.82, "wrought_iron", 1.05)

    vb.build_mesh_object()
    out_path = os.path.join(out_dir, "abattoir_blood_press_monolith.glb")
    export_environment_glb(out_path)
    print(f"[Wave1C] Exported -> {out_path}")


# ==============================================================================
# 15. abattoir_hanging_hook_rack.glb (Biome 4: The Blood-Forged Abattoir)
# ==============================================================================
def build_abattoir_hanging_hook_rack(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    vb = EnvironmentVoxelBuilder(
        name="abattoir_hanging_hook_rack",
        voxel_size=0.035,
        palette=palette,
        pivot_xyz=(0.0, 0.0, 0.0),
    )

    # 1. Ceiling mount plate at Z = 0.0, hanging down to Z = -1.75m
    vb.fill_world_cylinder_z(0.0, 0.0, -0.12, 0.0, 0.24, 0.0, "wrought_iron", 0.95, octagonal=True)
    vb.fill_world_cylinder_z(0.0, 0.0, -1.25, -0.12, 0.04, 0.0, "wrought_iron", 0.92)

    # 2. Circular Butcher's Wheel at Z = -1.18m (radius = 0.80m)
    r_wheel = 0.80
    z_wheel = -1.18
    vb.fill_world_cylinder_z(0.0, 0.0, z_wheel - 0.05, z_wheel + 0.05, r_wheel + 0.05, r_wheel - 0.05, "wrought_iron", 0.96)
    vb.fill_world_cylinder_z(0.0, 0.0, z_wheel - 0.04, z_wheel + 0.04, 0.44, 0.38, "bronze", 1.05)

    # Central crimson ember cage
    vb.fill_world_cylinder_z(0.0, 0.0, z_wheel - 0.16, z_wheel + 0.08, 0.28, 0.0, "crimson", 1.35, octagonal=True)
    vb.fill_world_cylinder_z(0.0, 0.0, -1.60, z_wheel - 0.16, 0.10, 0.0, "wrought_iron", 0.92, octagonal=True)
    vb.set_world(0.0, 0.0, -1.63, "wrought_iron", 1.05)

    # 3. 4 Suspension chains from ceiling mount (Z = -0.10) to wheel (Z = -1.14)
    for i in range(4):
        ang = i * (math.pi * 0.5)
        p0 = (0.12 * math.cos(ang), 0.12 * math.sin(ang), -0.10)
        p1 = (r_wheel * math.cos(ang), r_wheel * math.sin(ang), z_wheel + 0.04)
        add_chain_voxel(vb, p0, p1, mat_key="wrought_iron", sag=0.0)

    # 4. 10 Hanging Meat Hooks + Perimeter Crimson Ember Pods + Radial Spokes
    for i in range(10):
        ang = i * (2.0 * math.pi / 10.0)
        rx = r_wheel * math.cos(ang)
        ry = r_wheel * math.sin(ang)

        # Spoke to hub
        for r_step in range(3, int(r_wheel / 0.04)):
            rw = r_step * 0.04
            vb.set_world(rw * math.cos(ang), rw * math.sin(ang), z_wheel, "wrought_iron", 0.94)

        # Drop rod (Z = -1.18 to -1.45)
        vb.fill_world_cylinder_z(rx, ry, -1.45, z_wheel - 0.05, 0.02, 0.0, "wrought_iron", 0.9)

        # Curved meat hook point (Z = -1.45 to -1.65)
        hook_tip_x = rx * 1.08
        hook_tip_y = ry * 1.08
        vb.fill_world_box(hook_tip_x - 0.03, hook_tip_x + 0.03, hook_tip_y - 0.03, hook_tip_y + 0.03, -1.60, -1.45, "bronze", 1.05)
        vb.set_world(hook_tip_x, hook_tip_y, -1.63, "bronze", 1.15)

        # Perimeter crimson pod
        vb.fill_world_cylinder_z(rx, ry, z_wheel + 0.05, z_wheel + 0.18, 0.045, 0.0, "crimson", 1.3)

    vb.build_mesh_object()
    out_path = os.path.join(out_dir, "abattoir_hanging_hook_rack.glb")
    export_environment_glb(out_path)
    print(f"[Wave1C] Exported -> {out_path}")


# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================
def main() -> None:
    os.makedirs(OSSUARY_DIR, exist_ok=True)
    os.makedirs(DUNGEON_DIR, exist_ok=True)

    print("=" * 70)
    print("STARTING WAVE 1C: OSSUARY VARIETY & BIOMES 2-4 VOXEL BUILDER")
    print("=" * 70)

    # 1. 6 Ossuary Variety Pieces
    print("\n--- BUILDING 6 OSSUARY VARIETY ASSETS ---")
    build_ossuary_stone_bridge_4x4(OSSUARY_DIR)
    build_ossuary_balcony_railing_4m(OSSUARY_DIR)
    build_ossuary_buttress_arch_4x4(OSSUARY_DIR)
    build_ossuary_bone_chandelier(OSSUARY_DIR)
    build_ossuary_spine_reliquary_monolith(OSSUARY_DIR)
    build_ossuary_burial_niche_divider_4x4(OSSUARY_DIR)

    # 2. 9 Biomes 2-4 Dungeon Kit Pieces
    print("\n--- BUILDING 9 BIOMES 2-4 DUNGEON KIT ASSETS ---")
    build_necropolis_wall_armory_4x4(DUNGEON_DIR)
    build_necropolis_iron_maiden_monolith(DUNGEON_DIR)
    build_necropolis_hanging_war_brazier(DUNGEON_DIR)
    build_reliquary_wall_grimoire_4x4(DUNGEON_DIR)
    build_reliquary_astral_orrery_monolith(DUNGEON_DIR)
    build_reliquary_chandelier_astrolabe(DUNGEON_DIR)
    build_abattoir_wall_furnace_4x4(DUNGEON_DIR)
    build_abattoir_blood_press_monolith(DUNGEON_DIR)
    build_abattoir_hanging_hook_rack(DUNGEON_DIR)

    print("\n" + "=" * 70)
    print("SUCCESS: ALL 15 WAVE 1C MODELS EXPORTED CLEANLY.")
    print("=" * 70)


if __name__ == "__main__":
    main()
