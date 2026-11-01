"""
tools/blender_build_voxel_crypt_kit.py
Builds 21 Hyper-Detailed Ultra-Realistic Micro-Voxel Crypt, Catacomb & Clutter Assets.
Standard: Godot 4.7, 4m x 4m x 4m modular grid, light-bleed isolation (wall thickness >= 0.48m).
Palette: Unified 23-material PBR Gothic environment palette with Col vertex color baking.
"""
import math
import os
import sys
import time
import bpy
import bmesh
from mathutils import Vector, Euler

# Import shared micro-voxel kit and environment palette
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blender_micro_voxel_kit import (
    create_environment_voxel_palette,
    EnvironmentVoxelBuilder,
    export_environment_glb,
)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_DIR = os.path.join(PROJECT_ROOT, "assets", "models", "church_kit")


def clear_scene() -> None:
    """Resets Blender to factory empty state for deterministic, clean model building."""
    bpy.ops.wm.read_factory_settings(use_empty=True)


def add_voxel_skull(
    builder: EnvironmentVoxelBuilder,
    cx: float,
    cy: float,
    cz: float,
    scale: float = 0.11,
    mat_key: str = "bone",
    yaw: float = 0.0,
) -> None:
    """Generates a detailed micro-voxel skull with cranium, brow, eye sockets, and maxilla."""
    # Cranium dome
    builder.fill_world_box(
        cx - scale * 0.75, cx + scale * 0.75,
        cy - scale * 0.85, cy + scale * 0.85,
        cz - scale * 0.15, cz + scale * 0.95,
        mat_key=mat_key, shade_bias=1.02,
    )
    # Facial structure / snout
    builder.fill_world_box(
        cx - scale * 0.55, cx + scale * 0.55,
        cy - scale * 1.05, cy - scale * 0.40,
        cz - scale * 0.55, cz + scale * 0.15,
        mat_key=mat_key, shade_bias=0.96,
    )
    # Teeth / jaw teeth line
    builder.fill_world_box(
        cx - scale * 0.40, cx + scale * 0.40,
        cy - scale * 1.00, cy - scale * 0.55,
        cz - scale * 0.75, cz - scale * 0.50,
        mat_key=mat_key, shade_bias=0.90,
    )
    # Eye sockets (carve)
    builder.carve_world_box(
        cx - scale * 0.52, cx - scale * 0.14,
        cy - scale * 1.15, cy - scale * 0.85,
        cz - scale * 0.12, cz + scale * 0.28,
    )
    builder.carve_world_box(
        cx + scale * 0.14, cx + scale * 0.52,
        cy - scale * 1.15, cy - scale * 0.85,
        cz - scale * 0.12, cz + scale * 0.28,
    )
    # Nasal cavity
    builder.carve_world_box(
        cx - scale * 0.10, cx + scale * 0.10,
        cy - scale * 1.15, cy - scale * 0.90,
        cz - scale * 0.35, cz - scale * 0.10,
    )


def add_voxel_candle(
    builder: EnvironmentVoxelBuilder,
    cx: float,
    cy: float,
    cz_base: float,
    height: float = 0.22,
    radius: float = 0.045,
    has_flame: bool = True,
) -> None:
    """Places a ritual candle with solidified dripping wax base and glowing voxel flame."""
    # Wax shaft
    builder.fill_world_cylinder_z(
        cx, cy, cz_base, cz_base + height,
        r_outer=radius, r_inner=0.0,
        mat_key="wax", shade_bias=1.02,
    )
    # Dripping wax pools and lobes at base
    builder.fill_world_box(
        cx - radius * 1.4, cx + radius * 1.4,
        cy - radius * 1.4, cy + radius * 1.4,
        cz_base, cz_base + max(0.02, height * 0.28),
        mat_key="wax", shade_bias=0.95,
    )
    # Individual wax drip droplet
    builder.set_world(cx + radius * 1.1, cy, cz_base + height * 0.55, "wax", 0.94)
    builder.set_world(cx - radius * 1.05, cy + radius * 0.3, cz_base + height * 0.40, "wax", 0.94)
    # Wick
    wz = cz_base + height
    builder.fill_world_box(
        cx - 0.008, cx + 0.008,
        cy - 0.008, cy + 0.008,
        wz, wz + 0.025,
        mat_key="charred_timber", shade_bias=0.80,
    )
    # Glowing CandleFlameGlow flame tip
    if has_flame:
        builder.fill_world_box(
            cx - 0.016, cx + 0.016,
            cy - 0.016, cy + 0.016,
            wz + 0.02, wz + 0.075,
            mat_key="candle_flame", shade_bias=1.12,
        )
        builder.fill_world_box(
            cx - 0.009, cx + 0.009,
            cy - 0.009, cy + 0.009,
            wz + 0.075, wz + 0.10,
            mat_key="candle_flame", shade_bias=1.20,
        )


def add_voxel_chain_segment(
    builder: EnvironmentVoxelBuilder,
    p0: tuple[float, float, float],
    p1: tuple[float, float, float],
    link_w: float = 0.05,
    link_h: float = 0.09,
    mat_key: str = "wrought_iron",
) -> None:
    """Generates interlocking micro-voxel chain links connecting two world points."""
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    dz = p1[2] - p0[2]
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    if length <= 0.01:
        return
    num_links = max(1, int(round(length / link_h)))
    for i in range(num_links):
        t = (i + 0.5) / float(num_links)
        lx = p0[0] + dx * t
        ly = p0[1] + dy * t
        lz = p0[2] + dz * t
        half_w = link_w * 0.5
        half_h = link_h * 0.5
        if i % 2 == 0:
            builder.fill_world_box(lx - half_w, lx + half_w, ly - 0.02, ly + 0.02, lz - half_h, lz + half_h, mat_key, 1.0)
            builder.carve_world_box(lx - half_w * 0.45, lx + half_w * 0.45, ly - 0.03, ly + 0.03, lz - half_h * 0.5, lz + half_h * 0.5)
        else:
            builder.fill_world_box(lx - 0.02, lx + 0.02, ly - half_w, ly + half_w, lz - half_h, lz + half_h, mat_key, 0.96)
            builder.carve_world_box(lx - 0.03, lx + 0.03, ly - half_w * 0.45, ly + half_w * 0.45, lz - half_h * 0.5, lz + half_h * 0.5)


def add_voxel_grimoire(
    builder: EnvironmentVoxelBuilder,
    cx: float,
    cy: float,
    cz: float,
    sx: float = 0.28,
    sy: float = 0.38,
    sz: float = 0.10,
    cover_mat: str = "charred_timber",
    has_runes: bool = True,
) -> None:
    """Builds a thick leather/timber-bound occult grimoire with parchment pages and glowing sigil."""
    # Leather/wood cover boards
    builder.fill_world_box(
        cx - sx * 0.5, cx + sx * 0.5,
        cy - sy * 0.5, cy + sy * 0.5,
        cz, cz + sz,
        mat_key=cover_mat, shade_bias=0.94,
    )
    # Aged parchment page edges (inset on 3 sides)
    builder.fill_world_box(
        cx - sx * 0.44, cx + sx * 0.44,
        cy - sy * 0.45, cy + sy * 0.45,
        cz + sz * 0.18, cz + sz * 0.82,
        mat_key="bone", shade_bias=1.02,
    )
    # Metal corner brackets and binding clasps
    builder.fill_world_box(
        cx - sx * 0.52, cx - sx * 0.38,
        cy - sy * 0.52, cy - sy * 0.38,
        cz - 0.005, cz + sz + 0.005,
        mat_key="bronze", shade_bias=1.05,
    )
    builder.fill_world_box(
        cx + sx * 0.38, cx + sx * 0.52,
        cy - sy * 0.52, cy - sy * 0.38,
        cz - 0.005, cz + sz + 0.005,
        mat_key="bronze", shade_bias=1.05,
    )
    # Glowing Occult Rune sigil on the top cover
    if has_runes:
        builder.fill_world_box(
            cx - sx * 0.22, cx + sx * 0.22,
            cy - sy * 0.22, cy + sy * 0.22,
            cz + sz, cz + sz + 0.015,
            mat_key="occult_rune", shade_bias=1.15,
        )


# ==============================================================================
# MODEL 1: crypt_corridor_vault_4x4.glb
# Modular barrel-vault ceiling unit (4.2m x 4.2m x 0.74m)
# Interface Z=0.0 (flush with 4m wall tops); ribs hang down into -Z (-0.42m to 0.0m)
# Solid upper isolation cap extends Z=0.0m to 0.52m (thickness >= 0.50m)
# ==============================================================================
def build_voxel_crypt_corridor_vault_4x4(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    builder = EnvironmentVoxelBuilder("CryptCorridorVault", voxel_size=0.04, palette=palette)

    # 1. Structural solid vault slab (Z = 0.0m to +0.50m, 4.2m x 4.2m)
    builder.fill_world_box(-2.10, 2.10, -2.10, 2.10, 0.00, 0.50, mat_key="weathered_stone", shade_bias=1.0)
    builder.fill_world_box(-2.12, 2.12, -2.12, 2.12, 0.44, 0.72, mat_key="cobble_flagstone", shade_bias=0.92)

    # 2. Underside coffered recesses (carved into ceiling underside from Z=0.0 to +0.16m)
    for cx in (-1.05, 1.05):
        for cy in (-1.05, 1.05):
            builder.carve_world_box(cx - 0.72, cx + 0.72, cy - 0.72, cy + 0.72, 0.00, 0.16)

    # 3. Transverse ribs along Y and longitudinal spine ribs along X (hanging Z = -0.32m to 0.0m)
    for ry in (-1.88, 0.0, 1.88):
        builder.fill_world_box(-2.06, 2.06, ry - 0.15, ry + 0.15, -0.32, 0.02, mat_key="carved_stone_trim", shade_bias=0.98)
    for rx in (-1.88, 0.0, 1.88):
        builder.fill_world_box(rx - 0.15, rx + 0.15, -2.06, 2.06, -0.32, 0.02, mat_key="carved_stone_trim", shade_bias=0.98)

    # 4. Diagonal cross-vault ribs connecting corners
    diag_pts = 48
    for i in range(diag_pts + 1):
        t = (i / float(diag_pts)) * 2.0 - 1.0  # -1.0 to +1.0
        wx = t * 1.95
        wy = t * 1.95
        builder.fill_world_box(wx - 0.11, wx + 0.11, wy - 0.11, wy + 0.11, -0.26, 0.02, mat_key="cobble_flagstone", shade_bias=0.94)
        builder.fill_world_box(wx - 0.11, wx + 0.11, -wy - 0.11, -wy + 0.11, -0.26, 0.02, mat_key="cobble_flagstone", shade_bias=0.94)

    # 5. Stepped stone wall corbels at rib spring anchors (descending to Z = -0.42m)
    corbel_coords = [
        (-1.95, -1.88), (1.95, -1.88),
        (-1.95, 0.0), (1.95, 0.0),
        (-1.95, 1.88), (1.95, 1.88),
        (0.0, -1.95), (0.0, 1.95),
    ]
    for kx, ky in corbel_coords:
        builder.fill_world_box(kx - 0.18, kx + 0.18, ky - 0.18, ky + 0.18, -0.28, -0.12, mat_key="carved_stone_trim", shade_bias=1.0)
        builder.fill_world_box(kx - 0.14, kx + 0.14, ky - 0.14, ky + 0.14, -0.42, -0.28, mat_key="weathered_stone", shade_bias=0.90)

    # 6. Central carved keystone boss & wrought-iron suspension ring (Z = -0.44m to 0.0m)
    builder.fill_world_box(-0.30, 0.30, -0.30, 0.30, -0.38, 0.02, mat_key="carved_stone_trim", shade_bias=1.04)
    builder.fill_world_cylinder_z(0.0, 0.0, -0.44, -0.38, r_outer=0.22, r_inner=0.0, mat_key="bronze", shade_bias=1.08, octagonal=True)
    builder.fill_world_box(-0.12, 0.12, -0.03, 0.03, -0.56, -0.44, mat_key="wrought_iron", shade_bias=0.92)
    builder.carve_world_box(-0.06, 0.06, -0.04, 0.04, -0.52, -0.46)

    builder.build_mesh_object()
    out_path = os.path.join(out_dir, "crypt_corridor_vault_4x4.glb")
    export_environment_glb(out_path)


# ==============================================================================
# MODEL 2: crypt_wall_ossuary_4x4.glb
# Double-faced catacomb ossuary wall (4.20m wide x 0.54m thick x 4.05m tall)
# Solid ashlar core >= 0.50m thickness for light-bleed isolation
# 2 tiers of pointed-arch burial niches packed with skulls and femur bundles
# ==============================================================================
def build_voxel_crypt_wall_ossuary_4x4(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    builder = EnvironmentVoxelBuilder("CryptWallOssuary", voxel_size=0.04, palette=palette)

    # 1. Solid heavy ashlar wall core (4.20m wide x 0.54m deep x 4.05m tall)
    builder.fill_world_box(-2.10, 2.10, -0.27, 0.27, 0.00, 4.05, mat_key="weathered_stone", shade_bias=1.0)

    # 2. Stepped base plinth, central stringcourse, and top cornice
    builder.fill_world_box(-2.12, 2.12, -0.32, 0.32, 0.00, 0.42, mat_key="cobble_flagstone", shade_bias=0.94)
    builder.fill_world_box(-2.12, 2.12, -0.30, 0.30, 1.94, 2.08, mat_key="carved_stone_trim", shade_bias=0.98)
    builder.fill_world_box(-2.12, 2.12, -0.32, 0.32, 3.82, 4.05, mat_key="carved_stone_trim", shade_bias=1.02)
    builder.fill_world_box(-0.18, 0.18, -0.30, 0.30, 0.42, 3.82, mat_key="carved_stone_trim", shade_bias=0.96)

    # 3. Corner quoins (alternating bond along vertical edges)
    for sx in (-2.00, 2.00):
        for qz in range(7):
            qw = 0.38 if (qz % 2 == 0) else 0.28
            builder.fill_world_box(sx - qw * 0.5, sx + qw * 0.5, -0.31, 0.31, 0.48 + qz * 0.48, 0.48 + (qz + 1) * 0.48 - 0.04, mat_key="cobble_flagstone", shade_bias=0.95)

    # 4. Pointed-arch burial niches carved on both faces (-Y and +Y)
    niche_xs = (-1.05, 1.05)
    niche_tiers = ((0.52, 1.35, 1.78), (2.16, 2.98, 3.42))  # (base_z, spring_z, peak_z)
    for nx in niche_xs:
        for zb, sh, ph in niche_tiers:
            # Carve front niche (-Y face)
            builder.carve_pointed_arch(nx, -0.27, zb, sh, ph, span_w=1.34, depth_y=0.36)
            # Carve back niche (+Y face)
            builder.carve_pointed_arch(nx, 0.27, zb, sh, ph, span_w=1.34, depth_y=0.36)

            # Sills and iron retaining crossbars for both faces
            for side_sign in (-1.0, 1.0):
                face_y = side_sign * 0.18
                # Stone sill ledge
                builder.fill_world_box(nx - 0.72, nx + 0.72, side_sign * 0.28 - 0.06, side_sign * 0.28 + 0.06, zb - 0.04, zb + 0.06, mat_key="carved_stone_trim", shade_bias=1.0)
                # Wrought-iron retaining bar across niche
                builder.fill_world_box(nx - 0.68, nx + 0.68, face_y - 0.02, face_y + 0.02, zb + 0.32, zb + 0.36, mat_key="wrought_iron", shade_bias=0.90)

                # Layer of femur bundles at base of niche
                for f_idx in range(4):
                    fx = nx - 0.48 + f_idx * 0.32
                    builder.fill_world_box(fx - 0.14, fx + 0.14, face_y - 0.05, face_y + 0.05, zb + 0.04, zb + 0.14, mat_key="bone", shade_bias=0.98)

                # Two stacked rows of AgedBone geometric skulls inside niche
                for r_idx in range(2):
                    for s_idx in range(4):
                        sk_x = nx - 0.46 + s_idx * 0.30
                        sk_z = zb + 0.18 + r_idx * 0.26
                        add_voxel_skull(builder, sk_x, face_y, sk_z, scale=0.10, mat_key="bone")

    builder.build_mesh_object()
    out_path = os.path.join(out_dir, "crypt_wall_ossuary_4x4.glb")
    export_environment_glb(out_path)


# ==============================================================================
# MODEL 3: crypt_archway_portcullis_4x4.glb
# Gothic archway wall (4.20m x 0.54m x 4.05m) with raised wrought-iron portcullis
# Walkable opening width = 2.52m, peak Z = 3.60m
# Spikes end at Z = 2.45m (> 2.2m player clearance)
# ==============================================================================
def build_voxel_crypt_archway_portcullis_4x4(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    builder = EnvironmentVoxelBuilder("CryptArchwayPortcullis", voxel_size=0.04, palette=palette)

    # 1. Solid wall (4.20m wide x 0.54m deep x 4.05m tall)
    builder.fill_world_box(-2.10, 2.10, -0.27, 0.27, 0.00, 4.05, mat_key="weathered_stone", shade_bias=1.0)

    # 2. Carve wide Gothic pointed archway (width 2.52m, spring 2.70m, peak 3.60m)
    builder.carve_pointed_arch(0.0, 0.0, base_z=0.00, spring_z=2.70, peak_z=3.60, span_w=2.52, depth_y=0.60)

    # 3. Base plinths, jamb pilasters, and top cornice
    for sx in (-1.74, 1.74):
        builder.fill_world_box(sx - 0.38, sx + 0.38, -0.32, 0.32, 0.00, 0.42, mat_key="cobble_flagstone", shade_bias=0.94)
    builder.fill_world_box(-2.12, 2.12, -0.32, 0.32, 3.82, 4.05, mat_key="carved_stone_trim", shade_bias=1.02)

    # Jamb colonnettes flanking archway
    for sx in (-1.38, 1.38):
        builder.fill_world_box(sx - 0.16, sx + 0.16, -0.31, 0.31, 0.00, 2.75, mat_key="carved_stone_trim", shade_bias=0.98)
        builder.fill_world_box(sx - 0.20, sx + 0.20, -0.33, 0.33, 2.68, 2.82, mat_key="carved_stone_trim", shade_bias=1.04)

    # 4. Stepped voussoir arch stones around curve
    for v_idx in range(11):
        t = v_idx / 10.0
        ang = (t - 0.5) * math.pi * 0.76
        vx = math.sin(ang) * 1.35
        vz = 2.68 + math.cos(ang) * 0.95
        builder.fill_world_box(vx - 0.14, vx + 0.14, -0.30, 0.30, vz - 0.14, vz + 0.14, mat_key="carved_stone_trim", shade_bias=1.0)

    # 5. Partially raised wrought-iron portcullis (Z = 2.45m to 3.55m)
    # 3 Horizontal crossbars
    for hz in (2.64, 2.98, 3.32):
        builder.fill_world_box(-1.22, 1.22, -0.04, 0.04, hz - 0.04, hz + 0.04, mat_key="wrought_iron", shade_bias=0.96)

    # 7 Vertical spiked iron bars + conical spikes at Z = 2.45m
    for b_idx in range(7):
        bx = -1.05 + b_idx * 0.35
        builder.fill_world_box(bx - 0.035, bx + 0.035, -0.035, 0.035, 2.48, 3.55, mat_key="wrought_iron", shade_bias=0.98)
        # Downward spike
        builder.fill_world_box(bx - 0.02, bx + 0.02, -0.02, 0.02, 2.42, 2.48, mat_key="wrought_iron", shade_bias=1.04)
        # Bronze rivet bosses at crossbar intersections
        for hz in (2.64, 2.98, 3.32):
            builder.fill_world_box(bx - 0.05, bx + 0.05, -0.055, 0.055, hz - 0.05, hz + 0.05, mat_key="bronze", shade_bias=1.10)

    # 6. Winch brackets and suspension chains on left/right sides
    for cx in (-0.88, 0.88):
        builder.fill_world_box(cx - 0.10, cx + 0.10, -0.32, 0.32, 3.65, 3.82, mat_key="wrought_iron", shade_bias=0.92)
        add_voxel_chain_segment(builder, (cx, 0.0, 3.75), (cx, 0.0, 3.32), link_w=0.06, link_h=0.08, mat_key="wrought_iron")

    builder.build_mesh_object()
    out_path = os.path.join(out_dir, "crypt_archway_portcullis_4x4.glb")
    export_environment_glb(out_path)


# ==============================================================================
# MODEL 4: crypt_pillar.glb
# Clustered Gothic Pier (0.96m x 0.96m base x 4.0m height)
# Stacked ashlar drum courses, 4 engaged colonnettes, iron collar rings with rivets
# ==============================================================================
def build_voxel_crypt_pillar(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    builder = EnvironmentVoxelBuilder("CryptPillar", voxel_size=0.04, palette=palette)

    # 1. Stepped octagonal base plinths (Z = 0.0m to 0.56m)
    builder.fill_world_cylinder_z(0.0, 0.0, 0.00, 0.22, r_outer=0.48, r_inner=0.0, mat_key="cobble_flagstone", shade_bias=0.92, octagonal=True)
    builder.fill_world_cylinder_z(0.0, 0.0, 0.22, 0.40, r_outer=0.42, r_inner=0.0, mat_key="cobble_flagstone", shade_bias=0.96, octagonal=True)
    builder.fill_world_cylinder_z(0.0, 0.0, 0.40, 0.56, r_outer=0.38, r_inner=0.0, mat_key="carved_stone_trim", shade_bias=1.00, octagonal=True)

    # 4 Engaged colonnette plinth footings
    colonnette_offsets = [(0.32, 0.0), (-0.32, 0.0), (0.0, 0.32), (0.0, -0.32)]
    for cx, cy in colonnette_offsets:
        builder.fill_world_box(cx - 0.14, cx + 0.14, cy - 0.14, cy + 0.14, 0.20, 0.56, mat_key="carved_stone_trim", shade_bias=0.98)

    # 2. Clustered shaft drums (Z = 0.56m to 3.48m)
    builder.fill_world_cylinder_z(0.0, 0.0, 0.56, 3.48, r_outer=0.28, r_inner=0.0, mat_key="weathered_stone", shade_bias=1.00, octagonal=True)
    for cx, cy in colonnette_offsets:
        builder.fill_world_cylinder_z(cx, cy, 0.56, 3.48, r_outer=0.14, r_inner=0.0, mat_key="weathered_stone", shade_bias=1.02)

    # Subtle ashlar drum horizontal mortar seams (every 0.24m)
    for r in range(12):
        dz = 0.56 + r * 0.24
        builder.fill_world_cylinder_z(0.0, 0.0, dz, dz + 0.04, r_outer=0.29, r_inner=0.27, mat_key="cobble_flagstone", shade_bias=0.88, octagonal=True)

    # 3. Wrought-iron reinforcement bands + bronze rivets at Z = 1.15m, 2.00m, 2.85m
    for rz in (1.15, 2.00, 2.85):
        builder.fill_world_cylinder_z(0.0, 0.0, rz - 0.04, rz + 0.04, r_outer=0.46, r_inner=0.28, mat_key="wrought_iron", shade_bias=0.94)
        for ang_idx in range(8):
            ang = ang_idx * (math.pi / 4.0)
            rx = math.cos(ang) * 0.44
            ry = math.sin(ang) * 0.44
            builder.fill_world_box(rx - 0.02, rx + 0.02, ry - 0.02, ry + 0.02, rz - 0.02, rz + 0.02, mat_key="bronze", shade_bias=1.12)

    # 4. Foliated capital & abacus rings (Z = 3.48m to 4.00m)
    builder.fill_world_cylinder_z(0.0, 0.0, 3.48, 3.66, r_outer=0.38, r_inner=0.0, mat_key="carved_stone_trim", shade_bias=1.02, octagonal=True)
    for cx, cy in colonnette_offsets:
        builder.fill_world_box(cx - 0.16, cx + 0.16, cy - 0.16, cy + 0.16, 3.48, 3.70, mat_key="carved_stone_trim", shade_bias=1.04)
    builder.fill_world_cylinder_z(0.0, 0.0, 3.66, 3.84, r_outer=0.44, r_inner=0.0, mat_key="carved_stone_trim", shade_bias=1.06, octagonal=True)
    builder.fill_world_box(-0.48, 0.48, -0.48, 0.48, 3.84, 4.00, mat_key="cobble_flagstone", shade_bias=0.96)

    builder.build_mesh_object()
    out_path = os.path.join(out_dir, "crypt_pillar.glb")
    export_environment_glb(out_path)


# ==============================================================================
# MODEL 5: crypt_containment_hull.glb
# Subterranean dark-stone occlusion hull wrapping crypt volume
# (X in [-32, 32], Y in [19, 86], Z in [-10, 3.8]) with top church nave opening (X:[-5.8, 5.8], Y:[19, 27.8])
# Normals point strictly INWARD toward center (0.0, 52.5, -3.1)
# ==============================================================================
def build_voxel_crypt_containment_hull(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    mat_hull = palette["containment_hull"]

    bm = bmesh.new()
    color_layer = bm.loops.layers.color.new("Col")

    x_min, x_max = -32.0, 32.0
    y_min, y_max = 19.0, 86.0
    z_min, z_max = -10.0, 3.8
    cx_min, cx_max = -5.8, 5.8
    cy_cut = 27.8

    # 8 outer corner vertices
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

    # Inward faces
    # 1. Floor (normal +Z)
    bm.faces.new((v_bl_sw, v_bl_se, v_bl_ne, v_bl_nw))
    # 2. West wall (normal +X)
    bm.faces.new((v_bl_sw, v_bl_nw, v_tl_nw, v_tl_sw))
    # 3. East wall (normal -X)
    bm.faces.new((v_bl_se, v_tl_se, v_tl_ne, v_bl_ne))
    # 4. South wall at Y=19 (normal +Y)
    bm.faces.new((v_bl_sw, v_tl_sw, v_tl_se, v_bl_se))
    # 5. North wall at Y=86 (normal -Y)
    bm.faces.new((v_bl_nw, v_bl_ne, v_tl_ne, v_tl_nw))
    # 6. Top ceiling West slab
    bm.faces.new((v_tl_sw, v_tl_nw, v_tc_far_w, v_tc_sw))
    # 7. Top ceiling East slab
    bm.faces.new((v_tc_se, v_tc_far_e, v_tl_ne, v_tl_se))
    # 8. Top ceiling North center slab
    bm.faces.new((v_tc_nw, v_tc_far_w, v_tc_far_e, v_tc_ne))

    center_pt = Vector((0.0, 52.5, -3.1))
    for f in bm.faces:
        f.normal_update()
        to_center = center_pt - f.calc_center_median()
        if f.normal.dot(to_center) < 0.0:
            f.normal_flip()
        f.material_index = 0
        f.smooth = False
        for loop in f.loops:
            loop[color_layer] = (0.06, 0.06, 0.08, 1.0)

    mesh = bpy.data.meshes.new("CryptContainmentHullMesh")
    bm.to_mesh(mesh)
    bm.free()

    hull_obj = bpy.data.objects.new("CryptContainmentHull", mesh)
    bpy.context.collection.objects.link(hull_obj)
    hull_obj.data.materials.append(mat_hull)

    out_path = os.path.join(out_dir, "crypt_containment_hull.glb")
    export_environment_glb(out_path)


# ==============================================================================
# MODEL 6: crypt_iron_gate_cell_4x4.glb
# Modular dungeon cell wall (4.20m x 0.50m x 4.05m)
# Central arch doorway (1.48m x 2.95m) with swung-open iron gate (passable!)
# Left & right barred window openings above 1.15m dwarf walls
# ==============================================================================
def build_voxel_crypt_iron_gate_cell_4x4(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    builder = EnvironmentVoxelBuilder("CryptIronGateCell", voxel_size=0.04, palette=palette)

    # 1. Solid stone frame wall (4.20m x 0.50m x 4.05m)
    builder.fill_world_box(-2.10, 2.10, -0.25, 0.25, 0.00, 4.05, mat_key="weathered_stone", shade_bias=1.0)

    # 2. Carve central pointed-arch cell doorway (span 1.48m, spring 2.35m, peak 2.95m)
    builder.carve_pointed_arch(0.0, 0.0, base_z=0.00, spring_z=2.35, peak_z=2.95, span_w=1.48, depth_y=0.55)

    # 3. Carve left and right barred window openings above 1.15m dwarf wall
    for wx in (-1.34, 1.34):
        builder.carve_world_box(wx - 0.44, wx + 0.44, -0.28, 0.28, 1.15, 3.15)

    # 4. Plinths, dwarf sills, and top cornice
    builder.fill_world_box(-2.12, 2.12, -0.28, 0.28, 3.82, 4.05, mat_key="carved_stone_trim", shade_bias=1.02)
    for wx in (-1.34, 1.34):
        builder.fill_world_box(wx - 0.50, wx + 0.50, -0.28, 0.28, 0.00, 0.40, mat_key="cobble_flagstone", shade_bias=0.94)
        builder.fill_world_box(wx - 0.48, wx + 0.48, -0.29, 0.29, 1.08, 1.18, mat_key="carved_stone_trim", shade_bias=1.00)

    # Central doorway jamb colonnettes
    for sx in (-0.78, 0.78):
        builder.fill_world_box(sx - 0.12, sx + 0.12, -0.28, 0.28, 0.00, 2.45, mat_key="carved_stone_trim", shade_bias=0.98)

    # 5. Heavy vertical wrought-iron bars in window openings + riveted crossbars
    for wx in (-1.34, 1.34):
        for hz in (1.55, 2.15, 2.75):
            builder.fill_world_box(wx - 0.46, wx + 0.46, -0.03, 0.03, hz - 0.03, hz + 0.03, mat_key="wrought_iron", shade_bias=0.95)
        for b_idx in range(4):
            bx = wx - 0.33 + b_idx * 0.22
            builder.fill_world_box(bx - 0.025, bx + 0.025, -0.025, 0.025, 1.15, 3.15, mat_key="wrought_iron", shade_bias=1.00)
            for hz in (1.55, 2.15, 2.75):
                builder.fill_world_box(bx - 0.038, bx + 0.038, -0.045, 0.045, hz - 0.038, hz + 0.038, mat_key="bronze", shade_bias=1.12)

    # 6. Swung-open wrought-iron cell gate (hinged at left jamb, swung open into -Y by ~52 degrees)
    gate_w = 1.40
    gate_h = 2.40
    pivot_x = -0.74
    pivot_y = -0.15
    open_angle = math.radians(52.0)
    cos_a = math.cos(open_angle)
    sin_a = math.sin(open_angle)

    # Gate frame perimeter
    gate_steps = 32
    for s_i in range(gate_steps + 1):
        t = s_i / float(gate_steps)
        gx = pivot_x + (t * gate_w) * cos_a
        gy = pivot_y - (t * gate_w) * sin_a
        builder.fill_world_box(gx - 0.02, gx + 0.02, gy - 0.02, gy + 0.02, 0.04, 0.10, mat_key="wrought_iron", shade_bias=0.98)
        builder.fill_world_box(gx - 0.02, gx + 0.02, gy - 0.02, gy + 0.02, gate_h - 0.06, gate_h, mat_key="wrought_iron", shade_bias=0.98)
        # 3 Middle horizontal crossbars
        for hz in (0.75, 1.45, 2.10):
            builder.fill_world_box(gx - 0.018, gx + 0.018, gy - 0.018, gy + 0.018, hz - 0.025, hz + 0.025, mat_key="wrought_iron", shade_bias=0.96)

    # 6 Vertical gate bars
    for vb_i in range(7):
        frac = vb_i / 6.0
        bx = pivot_x + (frac * gate_w) * cos_a
        by = pivot_y - (frac * gate_w) * sin_a
        builder.fill_world_box(bx - 0.02, bx + 0.02, by - 0.02, by + 0.02, 0.04, gate_h, mat_key="wrought_iron", shade_bias=1.02)
        # Top spear spikes
        builder.fill_world_box(bx - 0.012, bx + 0.012, by - 0.012, by + 0.012, gate_h, gate_h + 0.08, mat_key="wrought_iron", shade_bias=1.08)

    # Lock box & keyhole fixture
    lock_x = pivot_x + (0.92 * gate_w) * cos_a
    lock_y = pivot_y - (0.92 * gate_w) * sin_a
    builder.fill_world_box(lock_x - 0.06, lock_x + 0.06, lock_y - 0.06, lock_y + 0.06, 0.95, 1.15, mat_key="bronze", shade_bias=1.12)

    builder.build_mesh_object()
    out_path = os.path.join(out_dir, "crypt_iron_gate_cell_4x4.glb")
    export_environment_glb(out_path)


# ==============================================================================
# MODEL 7: crypt_drowned_cistern_4x4.glb
# Recessed octagonal well/pool floor tile (4.0m x 4.0m slab, Z = -0.38m to 0.0m)
# Recessed basin (r = 1.32m, depth -0.28m), water at Z = -0.12m
# Flush wrought-iron drainage grates at Z = -0.02m (100% walkable!)
# ==============================================================================
def build_voxel_crypt_drowned_cistern_4x4(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    builder = EnvironmentVoxelBuilder("CryptDrownedCistern", voxel_size=0.04, palette=palette)

    # 1. Structural 4.0m x 4.0m floor slab (Z = -0.38m to 0.0m)
    builder.fill_world_box(-2.00, 2.00, -2.00, 2.00, -0.38, 0.00, mat_key="cobble_flagstone", shade_bias=0.94)

    # 2. Carve octagonal cistern basin (radius 1.32m, depth Z = -0.28m to +0.02m)
    builder.carve_world_cylinder_z(0.0, 0.0, -0.28, 0.02, r_outer=1.32)

    # 3. 8 Stone curb coping blocks around octagonal rim (Z = -0.02m to +0.06m)
    for i in range(8):
        ang = i * (math.pi / 4.0) + (math.pi / 8.0)
        cx = math.cos(ang) * 1.36
        cy = math.sin(ang) * 1.36
        builder.fill_world_box(cx - 0.16, cx + 0.16, cy - 0.16, cy + 0.16, -0.02, 0.06, mat_key="carved_stone_trim", shade_bias=1.02)

    # 4. Submerged stone steps on north/south edges inside basin
    for step_i in range(3):
        sz = -0.10 - step_i * 0.06
        sy = 1.15 - step_i * 0.20
        builder.fill_world_box(-0.60, 0.60, sy - 0.10, sy + 0.10, sz - 0.06, sz, mat_key="weathered_stone", shade_bias=0.88)
        builder.fill_world_box(-0.60, 0.60, -sy - 0.10, -sy + 0.10, sz - 0.06, sz, mat_key="weathered_stone", shade_bias=0.88)

    # 5. Dark cistern water disk (Z = -0.16m to -0.10m, radius 1.28m)
    builder.fill_world_cylinder_z(0.0, 0.0, -0.16, -0.10, r_outer=1.28, r_inner=0.0, mat_key="water", shade_bias=1.04, octagonal=True)

    # 6. Flush wrought-iron drainage grates across the basin at Z = -0.02m
    # Octagonal perimeter iron ring
    builder.fill_world_cylinder_z(0.0, 0.0, -0.04, 0.00, r_outer=1.30, r_inner=1.22, mat_key="wrought_iron", shade_bias=0.96, octagonal=True)

    # Heavy crossed primary beams
    builder.fill_world_box(-1.28, 1.28, -0.06, 0.06, -0.04, 0.00, mat_key="wrought_iron", shade_bias=1.00)
    builder.fill_world_box(-0.06, 0.06, -1.28, 1.28, -0.04, 0.00, mat_key="wrought_iron", shade_bias=1.00)

    # Concentric inner octagonal iron ring
    builder.fill_world_cylinder_z(0.0, 0.0, -0.04, 0.00, r_outer=0.72, r_inner=0.66, mat_key="wrought_iron", shade_bias=0.98, octagonal=True)

    # Drainage grating slats along X
    for gy in range(-6, 7):
        wy = gy * 0.18
        if abs(wy) > 1.20 or abs(wy) < 0.08:
            continue
        span_x = math.sqrt(max(0.0, 1.25 * 1.25 - wy * wy))
        builder.fill_world_box(-span_x, span_x, wy - 0.018, wy + 0.018, -0.035, 0.00, mat_key="wrought_iron", shade_bias=0.94)

    builder.build_mesh_object()
    out_path = os.path.join(out_dir, "crypt_drowned_cistern_4x4.glb")
    export_environment_glb(out_path)


# ==============================================================================
# MODEL 8: crypt_rotting_bookshelf_4x4.glb
# Modular gothic reliquary shelving (3.86m wide x 0.68m deep x 3.75m tall)
# Charred timber stiles, 5 shelves, trefoil crown, tilted tomes with glowing runes, skulls
# ==============================================================================
def build_voxel_crypt_rotting_bookshelf_4x4(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    builder = EnvironmentVoxelBuilder("CryptRottingBookshelf", voxel_size=0.04, palette=palette)

    # 1. Back panel (3.82m wide x 0.08m deep x 3.68m tall) at Y = 0.28m
    builder.fill_world_box(-1.91, 1.91, 0.24, 0.32, 0.00, 3.68, mat_key="charred_timber", shade_bias=0.90)

    # 2. 4 Vertical timber stiles (X = -1.86, -0.62, 0.62, 1.86) + iron corner brackets
    stiles_x = (-1.86, -0.62, 0.62, 1.86)
    for sx in stiles_x:
        builder.fill_world_box(sx - 0.07, sx + 0.07, -0.32, 0.32, 0.00, 3.72, mat_key="charred_timber", shade_bias=0.96)
        # Base and top iron reinforcement brackets
        builder.fill_world_box(sx - 0.09, sx + 0.09, -0.34, 0.34, 0.00, 0.36, mat_key="wrought_iron", shade_bias=0.94)
        builder.fill_world_box(sx - 0.09, sx + 0.09, -0.34, 0.34, 3.32, 3.48, mat_key="wrought_iron", shade_bias=0.94)

    # 3. 5 Horizontal timber shelves (Z = 0.24, 0.92, 1.60, 2.28, 2.96)
    shelf_zs = (0.24, 0.92, 1.60, 2.28, 2.96)
    for sz in shelf_zs:
        builder.fill_world_box(-1.91, 1.91, -0.32, 0.32, sz, sz + 0.08, mat_key="charred_timber", shade_bias=1.00)
        # Front lip iron trim
        builder.fill_world_box(-1.91, 1.91, -0.34, -0.31, sz, sz + 0.08, mat_key="wrought_iron", shade_bias=1.04)

    # 4. Gothic crown header with 3 trefoil arch cutouts
    builder.fill_world_box(-1.95, 1.95, -0.33, 0.33, 3.48, 3.75, mat_key="charred_timber", shade_bias=1.02)
    for cx in (-1.24, 0.0, 1.24):
        builder.carve_pointed_arch(cx, 0.0, base_z=3.20, spring_z=3.42, peak_z=3.66, span_w=0.88, depth_y=0.70)

    # 5. Packed contents on shelves: tilted grimoires, skulls, and parchment scroll tubes
    # Bay centers between stiles: -1.24, 0.0, 1.24
    bay_centers = (-1.24, 0.0, 1.24)

    # Shelf 1 (Z=0.32): Heavy ancient tomes and ledger stacks
    for bc in bay_centers:
        for t_i in range(5):
            tx = bc - 0.40 + t_i * 0.20
            add_voxel_grimoire(builder, tx, 0.0, 0.32, sx=0.16, sy=0.48, sz=0.42, has_runes=(t_i % 2 == 0))
        # Skulls resting on bottom shelf
        add_voxel_skull(builder, bc + 0.44, 0.02, 0.44, scale=0.11, mat_key="bone")

    # Shelf 2 (Z=1.00): Occult tomes with glowing runes & chained books
    for bc in bay_centers:
        for t_i in range(4):
            tx = bc - 0.36 + t_i * 0.24
            add_voxel_grimoire(builder, tx, 0.0, 1.00, sx=0.18, sy=0.46, sz=0.45, cover_mat="charred_timber", has_runes=True)
        # Retaining chain across bay
        add_voxel_chain_segment(builder, (bc - 0.55, -0.30, 1.28), (bc + 0.55, -0.30, 1.28), link_w=0.04, link_h=0.06, mat_key="wrought_iron")

    # Shelf 3 (Z=1.68): Alternating skulls, scroll canisters, and tilted grimoires
    for bc in bay_centers:
        add_voxel_skull(builder, bc - 0.35, 0.04, 1.80, scale=0.11, mat_key="bone")
        add_voxel_skull(builder, bc + 0.35, 0.04, 1.80, scale=0.11, mat_key="bone")
        add_voxel_grimoire(builder, bc, 0.0, 1.68, sx=0.22, sy=0.44, sz=0.42, has_runes=True)
        # Rolled scroll rolls
        builder.fill_world_cylinder_y(bc - 0.12, 1.78, -0.18, 0.18, r_outer=0.045, r_inner=0.0, mat_key="bone", shade_bias=0.98)
        builder.fill_world_cylinder_y(bc + 0.12, 1.78, -0.18, 0.18, r_outer=0.045, r_inner=0.0, mat_key="bone", shade_bias=0.98)

    # Shelf 4 (Z=2.36): Rare grimoires with vibrant GlowingOccultRune inlays
    for bc in bay_centers:
        for t_i in range(5):
            tx = bc - 0.38 + t_i * 0.19
            add_voxel_grimoire(builder, tx, 0.0, 2.36, sx=0.15, sy=0.44, sz=0.40, has_runes=(t_i % 2 == 1))

    builder.build_mesh_object()
    out_path = os.path.join(out_dir, "crypt_rotting_bookshelf_4x4.glb")
    export_environment_glb(out_path)


# ==============================================================================
# MODEL 9: crypt_altar.glb
# Focal Prop: Sacrificial crypt altar on 2-tier dais (2.80m x 1.80m x 1.50m)
# Carved obsidian basin, glowing blood rune channels, 4 corner lit candles
# ==============================================================================
def build_voxel_crypt_altar(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    builder = EnvironmentVoxelBuilder("CryptAltar", voxel_size=0.025, palette=palette)

    # 1. Two-tier stone ritual dais
    # Lower dais (2.80m x 1.80m x 0.18m)
    builder.fill_world_box(-1.40, 1.40, -0.90, 0.90, 0.00, 0.18, mat_key="cobble_flagstone", shade_bias=0.92)
    # Upper dais (2.40m x 1.44m x 0.18m)
    builder.fill_world_box(-1.20, 1.20, -0.72, 0.72, 0.18, 0.36, mat_key="carved_stone_trim", shade_bias=0.96)

    # 2. Main altar body block (2.05m x 1.08m x 0.86m, Z = 0.36m to 1.22m)
    builder.fill_world_box(-1.025, 1.025, -0.54, 0.54, 0.36, 1.22, mat_key="weathered_stone", shade_bias=1.00)

    # Plinth base molding & top altar table cornice
    builder.fill_world_box(-1.06, 1.06, -0.58, 0.58, 0.36, 0.46, mat_key="carved_stone_trim", shade_bias=1.02)
    builder.fill_world_box(-1.08, 1.08, -0.60, 0.60, 1.14, 1.22, mat_key="carved_stone_trim", shade_bias=1.04)

    # 3. Carve sacrificial blood basin into top (1.35m x 0.58m x 0.16m deep)
    builder.carve_world_box(-0.68, 0.68, -0.29, 0.29, 1.06, 1.23)

    # Basin bottom blood rune channels
    builder.fill_world_box(-0.64, 0.64, -0.04, 0.04, 1.06, 1.08, mat_key="crimson", shade_bias=1.15)
    builder.fill_world_box(-0.04, 0.04, -0.26, 0.26, 1.06, 1.08, mat_key="crimson", shade_bias=1.15)
    builder.fill_world_cylinder_z(0.0, 0.0, 1.06, 1.08, r_outer=0.18, r_inner=0.13, mat_key="crimson", shade_bias=1.20)

    # 4. Front face carved occult rune strip and recessed relief
    builder.fill_world_box(-0.85, 0.85, -0.555, -0.535, 0.65, 0.85, mat_key="occult_rune", shade_bias=1.18)
    # Flanking carved pilasters on front and back faces
    for px in (-0.95, -0.45, 0.45, 0.95):
        builder.fill_world_box(px - 0.05, px + 0.05, -0.56, -0.53, 0.46, 1.14, mat_key="carved_stone_trim", shade_bias=1.05)
        builder.fill_world_box(px - 0.05, px + 0.05, 0.53, 0.56, 0.46, 1.14, mat_key="carved_stone_trim", shade_bias=1.05)

    # 5. 4 Corner bronze candle dishes + wax candles with glowing flames
    candle_corners = [
        (-0.96, -0.48), (0.96, -0.48),
        (-0.96, 0.48), (0.96, 0.48),
    ]
    for cx, cy in candle_corners:
        # Bronze saucer tray
        builder.fill_world_cylinder_z(cx, cy, 1.22, 1.24, r_outer=0.08, r_inner=0.0, mat_key="bronze", shade_bias=1.08)
        # Main candle
        add_voxel_candle(builder, cx, cy, cz_base=1.24, height=0.24, radius=0.035, has_flame=True)
        # Secondary shorter melting candle adjacent
        add_voxel_candle(builder, cx + (0.05 if cx < 0 else -0.05), cy + (0.04 if cy < 0 else -0.04), cz_base=1.24, height=0.12, radius=0.025, has_flame=True)

    builder.build_mesh_object()
    out_path = os.path.join(out_dir, "crypt_altar.glb")
    export_environment_glb(out_path)


# ==============================================================================
# MODEL 10: crypt_sarcophagus_ornate.glb
# Focal Prop: Stepped tomb chest (1.56m x 2.68m x 1.45m)
# 2-tier plinth, blind arch carvings, hollow interior with skeleton, lid cracked open 8°
# ==============================================================================
def build_voxel_crypt_sarcophagus_ornate(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    builder = EnvironmentVoxelBuilder("CryptSarcophagusOrnate", voxel_size=0.025, palette=palette)

    # 1. 2-tier stepped stone plinth
    # Lower plinth (1.56m x 2.68m x 0.18m)
    builder.fill_world_box(-0.78, 0.78, -1.34, 1.34, 0.00, 0.18, mat_key="cobble_flagstone", shade_bias=0.92)
    # Upper plinth (1.36m x 2.48m x 0.16m)
    builder.fill_world_box(-0.68, 0.68, -1.24, 1.24, 0.18, 0.34, mat_key="carved_stone_trim", shade_bias=0.96)

    # 2. Main sarcophagus chest (1.18m wide x 2.28m long x 0.72m tall, Z = 0.34m to 1.06m)
    builder.fill_world_box(-0.59, 0.59, -1.14, 1.14, 0.34, 1.06, mat_key="weathered_stone", shade_bias=1.00)
    # Base and rim trim moldings
    builder.fill_world_box(-0.62, 0.62, -1.18, 1.18, 0.34, 0.44, mat_key="carved_stone_trim", shade_bias=1.02)
    builder.fill_world_box(-0.62, 0.62, -1.18, 1.18, 0.98, 1.06, mat_key="carved_stone_trim", shade_bias=1.04)

    # 3. Carve hollow interior tomb cavity (0.86m x 1.96m x 0.54m deep)
    builder.carve_world_box(-0.43, 0.43, -0.98, 0.98, 0.52, 1.07)

    # 4. Interior contents: glowing rune bed + skeletal remains
    builder.fill_world_box(-0.38, 0.38, -0.92, 0.92, 0.52, 0.54, mat_key="occult_rune", shade_bias=1.12)
    # Ancient skull at head end (-Y)
    add_voxel_skull(builder, 0.0, -0.72, 0.59, scale=0.13, mat_key="bone")
    # Spine & rib cage slats
    for ry in range(-5, 6):
        wy = ry * 0.11
        builder.fill_world_box(-0.24, 0.24, wy - 0.02, wy + 0.02, 0.54, 0.60, mat_key="bone", shade_bias=0.96)
    # Crossed arm femurs
    builder.fill_world_box(-0.28, 0.28, 0.10, 0.22, 0.56, 0.62, mat_key="bone", shade_bias=0.98)

    # 5. Blind-arch recesses along left and right exterior sides
    for sy in (-0.70, 0.0, 0.70):
        # Left side (-X)
        builder.carve_world_box(-0.60, -0.52, sy - 0.22, sy + 0.22, 0.50, 0.94)
        builder.fill_world_box(-0.59, -0.53, sy - 0.20, sy + 0.20, 0.52, 0.92, mat_key="cobble_flagstone", shade_bias=0.88)
        # Right side (+X)
        builder.carve_world_box(0.52, 0.60, sy - 0.22, sy + 0.22, 0.50, 0.94)
        builder.fill_world_box(0.53, 0.59, sy - 0.20, sy + 0.20, 0.52, 0.92, mat_key="cobble_flagstone", shade_bias=0.88)

    # 6. Heavy sculpted stone lid (1.24m x 2.34m x 0.22m) cracked open 8° along Y axis
    # Pivot point along right edge (+X): lid tilts up on left edge (-X)
    lid_w = 1.24
    lid_steps = 48
    ang_rad = math.radians(8.0)
    cos_t = math.cos(ang_rad)
    sin_t = math.sin(ang_rad)
    for s_i in range(lid_steps + 1):
        frac = s_i / float(lid_steps)  # 0.0 (right) to 1.0 (left)
        wx = 0.62 - frac * lid_w * cos_t
        wz = 1.06 + frac * lid_w * sin_t
        builder.fill_world_box(wx - 0.02, wx + 0.02, -1.17, 1.17, wz, wz + 0.18, mat_key="carved_stone_trim", shade_bias=1.02)
        # Central raised cross crest on lid
        builder.fill_world_box(wx - 0.015, wx + 0.015, -0.85, 0.85, wz + 0.18, wz + 0.22, mat_key="weathered_stone", shade_bias=1.06)

    builder.build_mesh_object()
    out_path = os.path.join(out_dir, "crypt_sarcophagus_ornate.glb")
    export_environment_glb(out_path)


# ==============================================================================
# MODEL 11: crypt_lectern_grimoire.glb
# Focal Prop: Gothic lectern reading stand (1.20m x 1.20m x 1.85m)
# Octagonal stone base, iron claw feet, fluted shaft, open leather grimoire with glowing runes
# ==============================================================================
def build_voxel_crypt_lectern_grimoire(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    builder = EnvironmentVoxelBuilder("CryptLecternGrimoire", voxel_size=0.025, palette=palette)

    # 1. Stepped octagonal stone dais & plinths (Z = 0.0m to 0.32m)
    builder.fill_world_cylinder_z(0.0, 0.0, 0.00, 0.16, r_outer=0.58, r_inner=0.0, mat_key="cobble_flagstone", shade_bias=0.92, octagonal=True)
    builder.fill_world_cylinder_z(0.0, 0.0, 0.16, 0.30, r_outer=0.42, r_inner=0.0, mat_key="carved_stone_trim", shade_bias=0.98, octagonal=True)

    # 2. 4 Wrought-iron claw feet extending from corners
    for i in range(4):
        ang = i * (math.pi * 0.5) + math.pi * 0.25
        fx = math.cos(ang) * 0.38
        fy = math.sin(ang) * 0.38
        builder.fill_world_box(fx - 0.07, fx + 0.07, fy - 0.07, fy + 0.07, 0.28, 0.48, mat_key="wrought_iron", shade_bias=0.95)
        # Claw talons
        builder.fill_world_box(fx * 1.18 - 0.04, fx * 1.18 + 0.04, fy * 1.18 - 0.04, fy * 1.18 + 0.04, 0.26, 0.36, mat_key="bronze", shade_bias=1.08)

    # 3. Fluted central wrought-iron shaft (Z = 0.30m to 1.35m) + decorative rings
    builder.fill_world_cylinder_z(0.0, 0.0, 0.30, 1.35, r_outer=0.12, r_inner=0.0, mat_key="wrought_iron", shade_bias=1.00, octagonal=True)
    for rz in (0.55, 0.95):
        builder.fill_world_cylinder_z(0.0, 0.0, rz - 0.03, rz + 0.03, r_outer=0.18, r_inner=0.10, mat_key="bronze", shade_bias=1.12, octagonal=True)

    # 4. Angled reading cradle wings (Z = 1.35m to 1.62m, tilted ~24° back toward +Y)
    builder.fill_world_box(-0.35, 0.35, -0.14, 0.14, 1.32, 1.40, mat_key="bronze", shade_bias=1.05)

    # Slanted desk board
    cradle_steps = 30
    tilt_rad = math.radians(24.0)
    cos_t = math.cos(tilt_rad)
    sin_t = math.sin(tilt_rad)
    for c_i in range(cradle_steps + 1):
        frac = c_i / float(cradle_steps)  # 0.0 (front) to 1.0 (back)
        wy = -0.22 + frac * 0.44 * cos_t
        wz = 1.38 + frac * 0.44 * sin_t
        builder.fill_world_box(-0.42, 0.42, wy - 0.015, wy + 0.015, wz, wz + 0.03, mat_key="charred_timber", shade_bias=0.96)

    # Front bottom book-stop lip
    builder.fill_world_box(-0.44, 0.44, -0.24, -0.20, 1.38, 1.46, mat_key="bronze", shade_bias=1.10)

    # 5. Open ancient grimoire resting on cradle (left and right page spreads with glowing runes)
    for c_i in range(2, cradle_steps - 1):
        frac = c_i / float(cradle_steps)
        wy = -0.22 + frac * 0.44 * cos_t
        wz = 1.38 + frac * 0.44 * sin_t + 0.03
        # Left page spread (-X)
        builder.fill_world_box(-0.38, -0.02, wy - 0.015, wy + 0.015, wz, wz + 0.04, mat_key="bone", shade_bias=1.02)
        # Right page spread (+X)
        builder.fill_world_box(0.02, 0.38, wy - 0.015, wy + 0.015, wz, wz + 0.04, mat_key="bone", shade_bias=1.02)
        # Center binding spine
        builder.fill_world_box(-0.03, 0.03, wy - 0.015, wy + 0.015, wz - 0.01, wz + 0.03, mat_key="charred_timber", shade_bias=0.90)

    # Glowing occult rune sigils inlaid onto open parchment pages
    for r_i in range(8, 22, 3):
        frac = r_i / float(cradle_steps)
        wy = -0.22 + frac * 0.44 * cos_t
        wz = 1.38 + frac * 0.44 * sin_t + 0.07
        builder.fill_world_box(-0.32, -0.08, wy - 0.01, wy + 0.01, wz, wz + 0.015, mat_key="occult_rune", shade_bias=1.20)
        builder.fill_world_box(0.08, 0.32, wy - 0.01, wy + 0.01, wz, wz + 0.015, mat_key="occult_rune", shade_bias=1.20)

    builder.build_mesh_object()
    out_path = os.path.join(out_dir, "crypt_lectern_grimoire.glb")
    export_environment_glb(out_path)


# ==============================================================================
# MODEL 12: crypt_hanging_cage.glb
# Focal Prop: Suspended rib-cage gibbet (0.80m x 0.80m x 2.93m)
# Cage hangs at Z = 1.25m..2.55m; prisoner skeleton inside; chain links up to Z = 3.88m
# ==============================================================================
def build_voxel_crypt_hanging_cage(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    builder = EnvironmentVoxelBuilder("CryptHangingCage", voxel_size=0.025, palette=palette)

    # 1. Bottom drop finial spike (Z = 0.95m to 1.30m)
    for sp_i in range(14):
        sz = 0.95 + sp_i * 0.025
        rad = 0.02 + sp_i * 0.012
        builder.fill_world_cylinder_z(0.0, 0.0, sz, sz + 0.025, r_outer=rad, r_inner=0.0, mat_key="wrought_iron", shade_bias=1.04, octagonal=True)

    # 2. Horizontal wrought-iron hoop rings forming cage barrel (Z = 1.30m to 2.45m)
    hoop_zs = (1.30, 1.58, 1.86, 2.14, 2.42)
    for hz in hoop_zs:
        builder.fill_world_cylinder_z(0.0, 0.0, hz - 0.025, hz + 0.025, r_outer=0.38, r_inner=0.33, mat_key="wrought_iron", shade_bias=0.98)

    # Floor cross-grid at Z = 1.30m
    builder.fill_world_box(-0.36, 0.36, -0.025, 0.025, 1.28, 1.32, mat_key="wrought_iron", shade_bias=0.96)
    builder.fill_world_box(-0.025, 0.025, -0.36, 0.36, 1.28, 1.32, mat_key="wrought_iron", shade_bias=0.96)

    # 3. 8 Vertical wrought-iron cage straps + bronze rivets at intersections
    for i in range(8):
        ang = i * (math.pi / 4.0)
        vx = math.cos(ang) * 0.36
        vy = math.sin(ang) * 0.36
        builder.fill_world_box(vx - 0.025, vx + 0.025, vy - 0.025, vy + 0.025, 1.30, 2.45, mat_key="wrought_iron", shade_bias=1.00)
        for hz in hoop_zs:
            builder.fill_world_box(vx * 1.05 - 0.02, vx * 1.05 + 0.02, vy * 1.05 - 0.02, vy * 1.05 + 0.02, hz - 0.02, hz + 0.02, mat_key="bronze", shade_bias=1.12)

    # 4. Top cage dome gathering bars (Z = 2.45m to 2.75m) into suspension eyelet
    for d_i in range(12):
        dz = 2.45 + d_i * 0.025
        d_rad = 0.36 * (1.0 - (d_i / 12.0))
        builder.fill_world_cylinder_z(0.0, 0.0, dz, dz + 0.025, r_outer=d_rad + 0.03, r_inner=max(0.0, d_rad - 0.03), mat_key="wrought_iron", shade_bias=0.96, octagonal=True)

    # Heavy suspension eyelet
    builder.fill_world_cylinder_y(0.0, 2.78, -0.04, 0.04, r_outer=0.08, r_inner=0.03, mat_key="bronze", shade_bias=1.12)

    # 5. Prisoner skeletal remains inside cage
    # Skull hanging at Z = 1.95m
    add_voxel_skull(builder, 0.0, 0.04, 1.95, scale=0.12, mat_key="bone")
    # Rib cage & spine (Z = 1.62m to 1.88m)
    for rz_i in range(5):
        wz = 1.65 + rz_i * 0.05
        builder.fill_world_cylinder_z(0.0, 0.0, wz, wz + 0.025, r_outer=0.18, r_inner=0.12, mat_key="bone", shade_bias=0.95)
    # Dangling leg femurs resting on cage floor
    builder.fill_world_box(-0.12, -0.06, -0.04, 0.04, 1.32, 1.65, mat_key="bone", shade_bias=0.98)
    builder.fill_world_box(0.06, 0.12, -0.04, 0.04, 1.32, 1.65, mat_key="bone", shade_bias=0.98)

    # 6. Suspension chains extending from eyelet (Z = 2.82m) to ceiling plate (Z = 3.88m)
    add_voxel_chain_segment(builder, (0.0, 0.0, 2.82), (0.0, 0.0, 3.84), link_w=0.06, link_h=0.09, mat_key="wrought_iron")
    # Ceiling rosette plate & 4 rivets
    builder.fill_world_cylinder_z(0.0, 0.0, 3.84, 3.88, r_outer=0.22, r_inner=0.0, mat_key="wrought_iron", shade_bias=1.04, octagonal=True)
    for ang_i in range(4):
        ang = ang_i * (math.pi * 0.5)
        rx = math.cos(ang) * 0.15
        ry = math.sin(ang) * 0.15
        builder.fill_world_box(rx - 0.02, rx + 0.02, ry - 0.02, ry + 0.02, 3.82, 3.86, mat_key="bronze", shade_bias=1.12)

    builder.build_mesh_object()
    out_path = os.path.join(out_dir, "crypt_hanging_cage.glb")
    export_environment_glb(out_path)


# ==============================================================================
# MODEL 13: crypt_plague_cauldron.glb
# Focal Prop: 2.2m cast-iron alchemical basin on stone furnace ring (2.4m x 2.4m x 2.95m)
# Boiling SicklyGreenBile with bubbles, rising distillation pipes, collector dome
# ==============================================================================
def build_voxel_crypt_plague_cauldron(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    builder = EnvironmentVoxelBuilder("CryptPlagueCauldron", voxel_size=0.025, palette=palette)

    # 1. Circular stone furnace ring (outer radius 1.20m, Z = 0.0m to 0.68m)
    builder.fill_world_cylinder_z(0.0, 0.0, 0.00, 0.68, r_outer=1.20, r_inner=0.88, mat_key="weathered_stone", shade_bias=0.96)
    builder.fill_world_cylinder_z(0.0, 0.0, 0.00, 0.18, r_outer=1.24, r_inner=0.0, mat_key="cobble_flagstone", shade_bias=0.92)

    # 4 Firebox vent portals carved into furnace ring
    for rot_z in (0.0, math.pi * 0.5):
        vx = 0.22 if rot_z == 0.0 else 1.30
        vy = 1.30 if rot_z == 0.0 else 0.22
        builder.carve_world_box(-vx, vx, -vy, vy, 0.16, 0.52)
        # Glowing embers inside firebox
        builder.fill_world_box(-0.45, 0.45, -0.45, 0.45, 0.08, 0.28, mat_key="candle_flame", shade_bias=1.15)

    # 2. Heavy cast-iron cauldron body (Z = 0.60m to 2.20m, belly radius up to 1.10m)
    cauldron_layers = 32
    for l_i in range(cauldron_layers):
        lz = 0.60 + l_i * 0.05
        t = l_i / float(cauldron_layers)
        # Bulging barrel profile
        r_outer = 0.85 + math.sin(t * math.pi) * 0.25
        r_inner = max(0.0, r_outer - 0.08)
        builder.fill_world_cylinder_z(0.0, 0.0, lz, lz + 0.05, r_outer=r_outer, r_inner=r_inner, mat_key="wrought_iron", shade_bias=1.00)

    # Upper heavy rim collar & flange torus (Z = 2.15m to 2.24m)
    builder.fill_world_cylinder_z(0.0, 0.0, 2.15, 2.24, r_outer=1.02, r_inner=0.84, mat_key="bronze", shade_bias=1.08)

    # 3. Boiling SicklyGreenBile pool surface inside (Z = 1.95m to 2.08m)
    builder.fill_world_cylinder_z(0.0, 0.0, 1.95, 2.08, r_outer=0.88, r_inner=0.0, mat_key="green_bile", shade_bias=1.12)

    # 9 Boiling bubbles & foam mounds on surface
    bubble_coords = [
        (0.0, 0.0, 0.14), (-0.35, 0.25, 0.10), (0.38, -0.22, 0.11),
        (0.28, 0.42, 0.09), (-0.42, -0.32, 0.10), (-0.12, 0.52, 0.08),
        (0.48, 0.18, 0.08), (0.12, -0.55, 0.09), (-0.28, -0.15, 0.12),
    ]
    for bx, by, brad in bubble_coords:
        builder.fill_world_cylinder_z(bx, by, 2.06, 2.06 + brad * 0.9, r_outer=brad, r_inner=0.0, mat_key="green_bile", shade_bias=1.22)

    # 4. 3 Distillation copper/bronze pipes rising from rim into collector dome (Z = 2.20m to 2.95m)
    pipe_angles = (0.0, math.pi * 0.67, math.pi * 1.33)
    for p_ang in pipe_angles:
        px = math.cos(p_ang) * 0.72
        py = math.sin(p_ang) * 0.72
        # Vertical riser
        builder.fill_world_cylinder_z(px, py, 2.20, 2.75, r_outer=0.065, r_inner=0.035, mat_key="bronze", shade_bias=1.04)
        # Arching elbow toward center
        builder.fill_world_box(min(px, px * 0.4), max(px, px * 0.4), min(py, py * 0.4), max(py, py * 0.4), 2.72, 2.82, mat_key="bronze", shade_bias=1.06)

    # Central condenser collector dome at Z = 2.75m to 2.95m
    builder.fill_world_cylinder_z(0.0, 0.0, 2.75, 2.95, r_outer=0.32, r_inner=0.0, mat_key="bronze", shade_bias=1.10, octagonal=True)

    builder.build_mesh_object()
    out_path = os.path.join(out_dir, "crypt_plague_cauldron.glb")
    export_environment_glb(out_path)


# ==============================================================================
# MODEL 14: crypt_weeping_statue_pedestal.glb
# Focal Prop: 3.6m hooded monolith figure / cenotaph (2.2m x 2.4m x 3.65m)
# Stepped pedestal, front offering basin, streaming FrozenBlueSoul spectral tears
# ==============================================================================
def build_voxel_crypt_weeping_statue_pedestal(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    builder = EnvironmentVoxelBuilder("CryptWeepingStatuePedestal", voxel_size=0.025, palette=palette)

    # 1. Stepped cenotaph pedestal (Z = 0.0m to 0.96m)
    # Step 1 (2.20m x 2.40m x 0.22m)
    builder.fill_world_box(-1.10, 1.10, -1.20, 1.20, 0.00, 0.22, mat_key="cobble_flagstone", shade_bias=0.92)
    # Step 2 (1.76m x 1.96m x 0.22m)
    builder.fill_world_box(-0.88, 0.88, -0.98, 0.98, 0.22, 0.44, mat_key="carved_stone_trim", shade_bias=0.96)
    # Pedestal core (1.32m x 1.56m x 0.52m)
    builder.fill_world_box(-0.66, 0.66, -0.68, 0.88, 0.44, 0.96, mat_key="weathered_stone", shade_bias=1.00)

    # 2. Front stone tear-offering basin (Y = -0.62m, Z = 0.44m to 1.08m)
    builder.fill_world_box(-0.56, 0.56, -1.05, -0.22, 0.44, 1.08, mat_key="carved_stone_trim", shade_bias=1.02)
    # Carve basin cavity
    builder.carve_world_box(-0.44, 0.44, -0.95, -0.32, 0.84, 1.10)
    # Glowing FrozenBlueSoul spectral tear pool
    builder.fill_world_box(-0.42, 0.42, -0.93, -0.34, 0.82, 0.96, mat_key="blue_soul", shade_bias=1.20)

    # 3. Towering 3.6m robed gothic figure (Z = 0.96m to 3.60m) bowed forward
    robe_layers = 52
    for r_i in range(robe_layers):
        frac = r_i / float(robe_layers)
        wz = 0.96 + r_i * 0.05
        # Forward lean of torso and cowl toward -Y
        lean_y = -0.22 * frac
        rad_x = 0.56 * (1.0 - frac * 0.52)
        rad_y = 0.64 * (1.0 - frac * 0.52)
        builder.fill_world_box(
            -rad_x, rad_x,
            0.15 + lean_y - rad_y * 0.5, 0.15 + lean_y + rad_y * 0.5,
            wz, wz + 0.05,
            mat_key="weathered_stone", shade_bias=1.00 - frac * 0.08,
        )

    # 4. Draped hooded cowl over bowed head (Z = 3.10m to 3.58m)
    builder.fill_world_cylinder_z(0.0, -0.12, 3.10, 3.58, r_outer=0.34, r_inner=0.0, mat_key="carved_stone_trim", shade_bias=1.04)
    # Deep facial cowl void (carve dark recess)
    builder.carve_world_box(-0.16, 0.16, -0.42, -0.16, 3.12, 3.42)

    # 5. Glowing FrozenBlueSoul spectral tear streams running down face and robes into basin
    # Left and right tear streams from eye sockets
    builder.fill_world_box(-0.10, -0.06, -0.28, -0.22, 3.18, 3.32, mat_key="blue_soul", shade_bias=1.25)
    builder.fill_world_box(0.06, 0.10, -0.28, -0.22, 3.18, 3.32, mat_key="blue_soul", shade_bias=1.25)

    # Flowing cascading tear rivulets down chest robes into basin
    stream_pts = 36
    for s_i in range(stream_pts):
        frac = s_i / float(stream_pts)
        sz = 3.18 - frac * 2.22
        sy = -0.26 - frac * 0.38
        builder.fill_world_box(-0.06, 0.06, sy - 0.03, sy + 0.03, sz - 0.04, sz + 0.04, mat_key="blue_soul", shade_bias=1.22)

    builder.build_mesh_object()
    out_path = os.path.join(out_dir, "crypt_weeping_statue_pedestal.glb")
    export_environment_glb(out_path)


# ==============================================================================
# MODEL 15: crypt_sunken_bell_crater.glb
# Focal Prop: 2.6m cracked cathedral bell tilted 25° in shattered crater (4.3m x 4.3m x 2.4m)
# Shattered rubble ring, jagged AbyssalCrimson crack fissure, broken yoke, wrapping chains
# ==============================================================================
def build_voxel_crypt_sunken_bell_crater(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    builder = EnvironmentVoxelBuilder("CryptSunkenBellCrater", voxel_size=0.03, palette=palette)

    # 1. Shattered stone floor crater mound (outer radius 2.15m, Z = 0.0m to 0.52m)
    builder.fill_world_cylinder_z(0.0, 0.0, 0.00, 0.44, r_outer=2.15, r_inner=0.0, mat_key="cobble_flagstone", shade_bias=0.92)
    # Carve jagged impact crater bowl (radius 1.55m, down to Z = 0.06m)
    builder.carve_world_cylinder_z(0.0, 0.0, 0.06, 0.46, r_outer=1.55)

    # Masonry rubble blocks strewn around the crater perimeter
    for r_i in range(24):
        ang = r_i * (math.tau / 24.0) + (r_i % 3) * 0.15
        dist = 1.62 + (r_i % 4) * 0.12
        rx = math.cos(ang) * dist
        ry = math.sin(ang) * dist
        builder.fill_world_box(rx - 0.14, rx + 0.14, ry - 0.14, ry + 0.14, 0.32, 0.54, mat_key="weathered_stone", shade_bias=0.96)

    # 2. Tilted 2.6m tarnished bronze cathedral bell (Z = 0.12m to 2.20m, tilted 25° toward +X)
    tilt_rad = math.radians(25.0)
    cos_t = math.cos(tilt_rad)
    sin_t = math.sin(tilt_rad)

    bell_slices = 36
    for b_i in range(bell_slices):
        h_frac = b_i / float(bell_slices)
        # Flare skirt at base, waist in middle, head crown at top
        if h_frac < 0.25:
            rad = 1.25 - (h_frac / 0.25) * 0.35  # 1.25 down to 0.90
        elif h_frac < 0.85:
            rad = 0.90 - ((h_frac - 0.25) / 0.60) * 0.25  # 0.90 down to 0.65
        else:
            rad = 0.65 - ((h_frac - 0.85) / 0.15) * 0.20  # 0.65 down to 0.45

        # Local Z along tilted bell axis
        local_z = b_i * 0.065
        center_x = local_z * sin_t
        center_z = 0.20 + local_z * cos_t

        builder.fill_world_cylinder_z(
            center_x, 0.0, center_z, center_z + 0.065,
            r_outer=rad, r_inner=max(0.0, rad - 0.10),
            mat_key="bronze", shade_bias=1.02,
        )

    # 3. Jagged glowing AbyssalCrimson fracture fissure splitting open the bell flank
    for f_i in range(12, 28):
        h_frac = f_i / float(bell_slices)
        local_z = f_i * 0.065
        center_x = local_z * sin_t
        center_z = 0.20 + local_z * cos_t
        # Fissure on +Y face of the bell
        builder.fill_world_box(
            center_x - 0.08, center_x + 0.08,
            0.65, 0.82,
            center_z - 0.04, center_z + 0.04,
            mat_key="crimson", shade_bias=1.24,
        )

    # 4. Broken charred timber yoke at crown & wrapping iron chains
    yoke_x = (bell_slices * 0.065) * sin_t
    yoke_z = 0.20 + (bell_slices * 0.065) * cos_t
    builder.fill_world_box(yoke_x - 0.25, yoke_x + 0.25, -0.65, 0.65, yoke_z, yoke_z + 0.24, mat_key="charred_timber", shade_bias=0.88)
    builder.fill_world_box(yoke_x - 0.28, yoke_x + 0.28, -0.35, 0.35, yoke_z + 0.22, yoke_z + 0.32, mat_key="wrought_iron", shade_bias=0.95)

    # Chains draped over bell body into crater
    add_voxel_chain_segment(builder, (yoke_x, -0.45, yoke_z + 0.10), (0.85, -0.95, 0.35), link_w=0.06, link_h=0.09, mat_key="wrought_iron")
    add_voxel_chain_segment(builder, (yoke_x, 0.45, yoke_z + 0.10), (-0.85, 0.95, 0.35), link_w=0.06, link_h=0.09, mat_key="wrought_iron")

    builder.build_mesh_object()
    out_path = os.path.join(out_dir, "crypt_sunken_bell_crater.glb")
    export_environment_glb(out_path)


# ==============================================================================
# MODEL 16: crypt_ritual_obelisk.glb
# Focal Prop: 3.82m tall tapered octagonal dark slate monolith (1.9m x 1.9m x 3.82m)
# 3-step plinth, 4 cardinal rune channels (AbyssalCrimson), 4 candle dishes
# ==============================================================================
def build_voxel_crypt_ritual_obelisk(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    builder = EnvironmentVoxelBuilder("CryptRitualObelisk", voxel_size=0.025, palette=palette)

    # 1. 3-step stone plinth (Z = 0.0m to 0.66m)
    # Step 1 (1.90m x 1.90m x 0.22m)
    builder.fill_world_box(-0.95, 0.95, -0.95, 0.95, 0.00, 0.22, mat_key="cobble_flagstone", shade_bias=0.92)
    # Step 2 (1.52m x 1.52m x 0.22m)
    builder.fill_world_box(-0.76, 0.76, -0.76, 0.76, 0.22, 0.44, mat_key="carved_stone_trim", shade_bias=0.96)
    # Step 3 (1.18m x 1.18m x 0.22m)
    builder.fill_world_box(-0.59, 0.59, -0.59, 0.59, 0.44, 0.66, mat_key="carved_stone_trim", shade_bias=1.00)

    # 2. Tapered octagonal obelisk monolith shaft (Z = 0.66m to 3.45m)
    obelisk_layers = 56
    for o_i in range(obelisk_layers):
        frac = o_i / float(obelisk_layers)
        oz = 0.66 + o_i * 0.05
        # Taper from radius 0.48m down to 0.26m
        rad = 0.48 - frac * 0.22
        builder.fill_world_cylinder_z(0.0, 0.0, oz, oz + 0.05, r_outer=rad, r_inner=0.0, mat_key="weathered_stone", shade_bias=1.02 - frac * 0.05, octagonal=True)

    # Pyramidal pyramidion apex cap (Z = 3.45m to 3.82m)
    for cap_i in range(15):
        frac = cap_i / 15.0
        cz = 3.45 + cap_i * 0.025
        rad = 0.26 * (1.0 - frac)
        builder.fill_world_cylinder_z(0.0, 0.0, cz, cz + 0.025, r_outer=max(0.015, rad), r_inner=0.0, mat_key="carved_stone_trim", shade_bias=1.08, octagonal=True)

    # 3. 4 Cardinal deeply recessed vertical rune channels with glowing AbyssalCrimson
    channel_zs = (1.00, 3.20)
    # North/South faces (Y = +-rad)
    for c_i in range(20, 52):
        frac = c_i / float(obelisk_layers)
        oz = 0.66 + c_i * 0.05
        rad = 0.48 - frac * 0.22
        # -Y channel
        builder.fill_world_box(-0.045, 0.045, -rad - 0.01, -rad + 0.04, oz, oz + 0.04, mat_key="crimson", shade_bias=1.24)
        # +Y channel
        builder.fill_world_box(-0.045, 0.045, rad - 0.04, rad + 0.01, oz, oz + 0.04, mat_key="crimson", shade_bias=1.24)
        # -X channel
        builder.fill_world_box(-rad - 0.01, -rad + 0.04, -0.045, 0.045, oz, oz + 0.04, mat_key="crimson", shade_bias=1.24)
        # +X channel
        builder.fill_world_box(rad - 0.04, rad + 0.01, -0.045, 0.045, oz, oz + 0.04, mat_key="crimson", shade_bias=1.24)

    # 4. 4 Bronze candle dishes on Step 2 corners with lit candles
    corner_coords = [(-0.66, -0.66), (0.66, -0.66), (-0.66, 0.66), (0.66, 0.66)]
    for cx, cy in corner_coords:
        builder.fill_world_cylinder_z(cx, cy, 0.44, 0.46, r_outer=0.08, r_inner=0.0, mat_key="bronze", shade_bias=1.08)
        add_voxel_candle(builder, cx, cy, cz_base=0.46, height=0.22, radius=0.035, has_flame=True)

    builder.build_mesh_object()
    out_path = os.path.join(out_dir, "crypt_ritual_obelisk.glb")
    export_environment_glb(out_path)


# ==============================================================================
# MODEL 17: standing_iron_brazier.glb
# Focal Prop: 1.35m tall ornate tripod wrought-iron fire brazier (0.84m x 0.84m x 1.35m)
# Tripod legs (base r = 0.42m), iron collar ring, fire basket bowl, glowing embers
# ==============================================================================
def build_voxel_standing_iron_brazier(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    builder = EnvironmentVoxelBuilder("StandingIronBrazier", voxel_size=0.02, palette=palette)

    # 1. Tripod wrought-iron legs (Z = 0.0m to 0.90m, base radius 0.42m angled to 0.22m)
    leg_angles = (0.0, math.pi * 0.667, math.pi * 1.333)
    leg_steps = 36
    for ang in leg_angles:
        for s_i in range(leg_steps):
            frac = s_i / float(leg_steps)
            lz = frac * 0.90
            rad = 0.42 * (1.0 - frac) + 0.22 * frac
            lx = math.cos(ang) * rad
            ly = math.sin(ang) * rad
            builder.fill_world_box(lx - 0.025, lx + 0.025, ly - 0.025, ly + 0.025, lz, lz + 0.03, mat_key="wrought_iron", shade_bias=1.00)
        # Leg claw foot footing at ground
        fx = math.cos(ang) * 0.43
        fy = math.sin(ang) * 0.43
        builder.fill_world_box(fx - 0.04, fx + 0.04, fy - 0.04, fy + 0.04, 0.00, 0.06, mat_key="bronze", shade_bias=1.08)

    # 2. Central iron collar ring at Z = 0.84m to 0.92m (radius 0.30m)
    builder.fill_world_cylinder_z(0.0, 0.0, 0.84, 0.92, r_outer=0.32, r_inner=0.24, mat_key="wrought_iron", shade_bias=1.02)
    for ang in leg_angles:
        rx = math.cos(ang) * 0.32
        ry = math.sin(ang) * 0.32
        builder.fill_world_box(rx - 0.03, rx + 0.03, ry - 0.03, ry + 0.03, 0.84, 0.92, mat_key="bronze", shade_bias=1.14)

    # 3. Fire basket bowl (Z = 0.88m to 1.30m, bowl radius 0.38m)
    bowl_slices = 20
    for b_i in range(bowl_slices):
        bz = 0.88 + b_i * 0.02
        t = b_i / float(bowl_slices)
        r_out = 0.26 + t * 0.12
        builder.fill_world_cylinder_z(0.0, 0.0, bz, bz + 0.02, r_outer=r_out, r_inner=max(0.0, r_out - 0.04), mat_key="wrought_iron", shade_bias=0.96)

    # Upper rim torus collar (Z = 1.28m to 1.34m)
    builder.fill_world_cylinder_z(0.0, 0.0, 1.28, 1.34, r_outer=0.40, r_inner=0.34, mat_key="bronze", shade_bias=1.08)

    # 4. Glowing amber embers mound inside bowl (Z = 1.05m to 1.26m)
    builder.fill_world_cylinder_z(0.0, 0.0, 1.05, 1.20, r_outer=0.34, r_inner=0.0, mat_key="candle_flame", shade_bias=1.16)
    builder.fill_world_cylinder_z(0.0, 0.0, 1.20, 1.26, r_outer=0.24, r_inner=0.0, mat_key="candle_flame", shade_bias=1.24)

    builder.build_mesh_object()
    out_path = os.path.join(out_dir, "standing_iron_brazier.glb")
    export_environment_glb(out_path)


# ==============================================================================
# MODEL 18: clutter_ceiling_chains_roots.glb
# Clutter Asset: Hanging chains, forged meat hooks, and petrified tree roots
# Ceiling anchor Z = 0.0m, hanging down to Z = -2.10m (1.8m x 1.8m x 2.1m)
# ==============================================================================
def build_voxel_clutter_ceiling_chains_roots(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    builder = EnvironmentVoxelBuilder("ClutterCeilingChainsRoots", voxel_size=0.02, palette=palette)

    # 1. 5 Ceiling Iron Anchor Rosettes + Hanging Chain Strands + Forged Meat Hooks
    chain_anchors = [
        (0.0, 0.0, -1.95),
        (-0.65, 0.45, -1.70),
        (0.62, -0.42, -1.82),
        (-0.52, -0.58, -1.45),
        (0.55, 0.60, -1.55),
    ]
    for ax, ay, bot_z in chain_anchors:
        # Ceiling collar plate (Z = -0.04m to 0.0m)
        builder.fill_world_cylinder_z(ax, ay, -0.04, 0.00, r_outer=0.14, r_inner=0.0, mat_key="wrought_iron", shade_bias=1.02, octagonal=True)
        for r_ang in (0.0, math.pi * 0.5, math.pi, math.pi * 1.5):
            rx = ax + math.cos(r_ang) * 0.10
            ry = ay + math.sin(r_ang) * 0.10
            builder.fill_world_box(rx - 0.015, rx + 0.015, ry - 0.015, ry + 0.015, -0.05, -0.02, mat_key="bronze", shade_bias=1.12)

        # Hanging chain links down to bot_z
        add_voxel_chain_segment(builder, (ax, ay, -0.04), (ax, ay, bot_z), link_w=0.05, link_h=0.08, mat_key="wrought_iron")

        # Forged iron meat hook at bottom (curved sickle shape)
        builder.fill_world_box(ax - 0.018, ax + 0.018, ay - 0.018, ay + 0.018, bot_z - 0.08, bot_z, mat_key="wrought_iron", shade_bias=1.04)
        builder.fill_world_box(ax - 0.018, ax + 0.07, ay - 0.018, ay + 0.018, bot_z - 0.14, bot_z - 0.08, mat_key="wrought_iron", shade_bias=1.00)
        builder.fill_world_box(ax + 0.05, ax + 0.09, ay - 0.018, ay + 0.018, bot_z - 0.10, bot_z - 0.02, mat_key="bronze", shade_bias=1.10)

    # 2. 10 Gnarled Petrified Tree Roots breaking through ceiling vaults
    root_origins = [
        (-0.25, -0.20), (0.28, 0.18), (-0.42, 0.15),
        (0.35, -0.28), (-0.15, 0.45), (0.12, -0.55),
        (-0.58, -0.15), (0.48, 0.32), (-0.32, -0.48), (0.22, 0.52),
    ]
    for r_idx, (rx, ry) in enumerate(root_origins):
        root_len = 0.65 + (r_idx % 4) * 0.22
        steps = int(round(root_len / 0.03))
        prev_x, prev_y, prev_z = rx, ry, 0.0
        for s_i in range(steps):
            frac = s_i / float(steps)
            cur_z = -frac * root_len
            # Gnarled winding offsets
            wiggle_x = math.sin(frac * 6.28 + r_idx) * 0.08
            wiggle_y = math.cos(frac * 4.71 + r_idx * 0.7) * 0.08
            cur_x = rx + wiggle_x
            cur_y = ry + wiggle_y
            thick = max(0.015, 0.045 * (1.0 - frac * 0.75))
            builder.fill_world_box(cur_x - thick, cur_x + thick, cur_y - thick, cur_y + thick, cur_z - 0.03, cur_z, mat_key="charred_timber", shade_bias=0.90)

    builder.build_mesh_object()
    out_path = os.path.join(out_dir, "clutter_ceiling_chains_roots.glb")
    export_environment_glb(out_path)


# ==============================================================================
# MODEL 19: clutter_melted_candle_cluster.glb
# Clutter Asset: 14 varied ritual candles with melted wax pools (0.68m x 0.52m x 0.42m)
# Wrought-iron/bronze tray, 24 wax pool lobes, dripping rivulets, wicks and flames
# ==============================================================================
def build_voxel_clutter_melted_candle_cluster(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    builder = EnvironmentVoxelBuilder("ClutterMeltedCandleCluster", voxel_size=0.015, palette=palette)

    # 1. Base Wrought-Iron & Tarnished Bronze Ritual Saucer Tray (0.68m x 0.52m x 0.03m)
    builder.fill_world_box(-0.34, 0.34, -0.26, 0.26, 0.00, 0.02, mat_key="wrought_iron", shade_bias=0.95)
    builder.fill_world_box(-0.32, 0.32, -0.24, 0.24, 0.015, 0.03, mat_key="bronze", shade_bias=1.04)

    # 2. 24 Solidified Melted Wax Pool Lobes spreading across the tray
    wax_lobe_coords = [
        (0.0, 0.0, 0.18), (-0.16, 0.08, 0.14), (0.18, -0.06, 0.15),
        (-0.08, -0.14, 0.13), (0.12, 0.14, 0.13), (-0.22, -0.10, 0.11),
        (0.24, 0.08, 0.12), (0.04, -0.18, 0.10), (-0.14, 0.18, 0.11),
        (0.20, -0.16, 0.10), (-0.26, 0.06, 0.09), (0.10, -0.12, 0.12),
        (-0.04, 0.10, 0.14), (-0.18, -0.18, 0.09), (0.16, 0.18, 0.09),
        (-0.28, -0.04, 0.08), (0.26, -0.08, 0.09), (0.02, 0.20, 0.08),
        (-0.10, -0.20, 0.08), (0.22, 0.12, 0.09), (-0.20, 0.15, 0.08),
        (0.06, -0.08, 0.12), (-0.06, 0.04, 0.13), (0.14, 0.02, 0.12),
    ]
    for wx, wy, wrad in wax_lobe_coords:
        builder.fill_world_cylinder_z(wx, wy, 0.02, 0.05, r_outer=wrad, r_inner=0.0, mat_key="wax", shade_bias=0.96)

    # 3. 14 Varied Ritual Candles with dripping wax rivulets and glowing flames
    candle_cluster_specs = [
        (0.00, 0.00, 0.34, 0.042),
        (-0.12, 0.06, 0.26, 0.035),
        (0.14, -0.05, 0.28, 0.038),
        (-0.06, -0.12, 0.21, 0.032),
        (0.10, 0.12, 0.22, 0.032),
        (-0.20, -0.08, 0.18, 0.030),
        (0.22, 0.06, 0.19, 0.030),
        (0.04, -0.16, 0.15, 0.028),
        (-0.12, 0.15, 0.16, 0.028),
        (0.18, -0.14, 0.14, 0.026),
        (-0.24, 0.05, 0.12, 0.025),
        (0.24, -0.06, 0.11, 0.024),
        (-0.03, 0.16, 0.10, 0.024),
        (0.02, -0.08, 0.38, 0.044),
    ]
    for cx, cy, ch, crad in candle_cluster_specs:
        add_voxel_candle(builder, cx, cy, cz_base=0.03, height=ch, radius=crad, has_flame=True)

    builder.build_mesh_object()
    out_path = os.path.join(out_dir, "clutter_melted_candle_cluster.glb")
    export_environment_glb(out_path)


# ==============================================================================
# MODEL 20: clutter_rubble_bones_pile.glb
# Clutter Asset: Corner rubble mound with broken pillars, skulls, bones, and chains
# Radial mound r = 0.95m, height Z = 0.0m to 0.45m
# ==============================================================================
def build_voxel_clutter_rubble_bones_pile(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    builder = EnvironmentVoxelBuilder("ClutterRubbleBonesPile", voxel_size=0.02, palette=palette)

    # 1. Base mound core (radial mound r = 0.95m, Z = 0.0m to 0.22m)
    builder.fill_world_cylinder_z(0.0, 0.0, 0.00, 0.12, r_outer=0.92, r_inner=0.0, mat_key="cobble_flagstone", shade_bias=0.90)
    builder.fill_world_cylinder_z(0.0, 0.0, 0.12, 0.22, r_outer=0.68, r_inner=0.0, mat_key="weathered_stone", shade_bias=0.94)

    # 2. 48 Fallen Masonry Blocks & Flagstone Shards placed deterministically
    for i in range(48):
        ang = (i / 48.0) * math.tau + (i % 5) * 0.22
        layer = i // 16
        rad = (0.20 + (1.0 - layer * 0.25) * 0.65) * (0.80 + (i % 7) * 0.05)
        bx = math.cos(ang) * rad
        by = math.sin(ang) * rad
        bz = 0.04 + layer * 0.07 + (i % 4) * 0.03
        sx = 0.12 + (i % 5) * 0.03
        sy = 0.11 + (i % 4) * 0.03
        sz = 0.06 + (i % 3) * 0.02
        m_key = "weathered_stone" if (i % 3 != 0) else "cobble_flagstone"
        builder.fill_world_box(bx - sx * 0.5, bx + sx * 0.5, by - sy * 0.5, by + sy * 0.5, bz, bz + sz, mat_key=m_key, shade_bias=0.96)

    # 3. 3 Broken Fluted Pillar Drum Fragments lying in rubble
    drum_coords = [
        (-0.28, 0.15, 0.12, 0.22),
        (0.32, -0.22, 0.10, 0.20),
        (0.05, 0.38, 0.08, 0.24),
    ]
    for dx, dy, dz, drad in drum_coords:
        builder.fill_world_cylinder_z(dx, dy, dz, dz + 0.26, r_outer=drad, r_inner=0.0, mat_key="carved_stone_trim", shade_bias=1.02, octagonal=True)

    # 4. 8 Geometric Gothic Skulls nestled into crevices
    skull_coords = [
        (0.00, 0.00, 0.26), (-0.38, -0.25, 0.15), (0.42, 0.20, 0.14),
        (-0.15, -0.45, 0.12), (0.25, 0.40, 0.12), (-0.52, 0.12, 0.11),
        (0.48, -0.32, 0.10), (0.05, -0.22, 0.24),
    ]
    for sk_x, sk_y, sk_z in skull_coords:
        add_voxel_skull(builder, sk_x, sk_y, sk_z, scale=0.10, mat_key="bone")

    # 5. 20 Bone Segments (femurs, tibias, ribs) scattered throughout
    for b_i in range(20):
        ang = b_i * (math.tau / 20.0) + (b_i % 3) * 0.3
        dist = 0.35 + (b_i % 6) * 0.08
        fx = math.cos(ang) * dist
        fy = math.sin(ang) * dist
        fz = 0.06 + (b_i % 4) * 0.05
        builder.fill_world_box(fx - 0.14, fx + 0.14, fy - 0.03, fy + 0.03, fz, fz + 0.05, mat_key="bone", shade_bias=0.98)

    # 6. 18 Rusted Wrought-Iron Chain Links draped across mound
    add_voxel_chain_segment(builder, (-0.45, -0.35, 0.18), (0.35, 0.35, 0.16), link_w=0.045, link_h=0.07, mat_key="wrought_iron")
    add_voxel_chain_segment(builder, (0.40, -0.30, 0.15), (-0.25, 0.40, 0.14), link_w=0.045, link_h=0.07, mat_key="wrought_iron")

    builder.build_mesh_object()
    out_path = os.path.join(out_dir, "clutter_rubble_bones_pile.glb")
    export_environment_glb(out_path)


# ==============================================================================
# MODEL 21: clutter_wooden_crates_barrels.glb
# Clutter Asset: 2 oak staved barrels with iron hoops + 2 slatted munitions crates
# Footprint 1.50m x 1.20m x 1.15m
# ==============================================================================
def build_voxel_clutter_wooden_crates_barrels(out_dir: str) -> None:
    clear_scene()
    palette = create_environment_voxel_palette()
    builder = EnvironmentVoxelBuilder("ClutterWoodenCratesBarrels", voxel_size=0.02, palette=palette)

    # 1. Barrel 1 at (-0.46, 0.16) (radius 0.34m, height 0.86m, Z = 0.0m to 0.86m)
    b1_x, b1_y = -0.46, 0.16
    barrel_slices = 28
    for s_i in range(barrel_slices):
        bz = s_i * 0.03
        t = s_i / float(barrel_slices)
        # Bulging barrel profile
        rad = 0.28 + math.sin(t * math.pi) * 0.06
        builder.fill_world_cylinder_z(b1_x, b1_y, bz, bz + 0.03, r_outer=rad, r_inner=0.0, mat_key="charred_timber", shade_bias=0.96)

    # 4 Iron hoops on Barrel 1
    for hz in (0.10, 0.32, 0.54, 0.76):
        t = (hz / 0.86)
        rad = 0.28 + math.sin(t * math.pi) * 0.06
        builder.fill_world_cylinder_z(b1_x, b1_y, hz - 0.025, hz + 0.025, r_outer=rad + 0.015, r_inner=rad - 0.02, mat_key="wrought_iron", shade_bias=1.02)
        # Bronze bunghole bung on barrel top
        builder.fill_world_cylinder_z(b1_x, b1_y, 0.85, 0.88, r_outer=0.04, r_inner=0.0, mat_key="bronze", shade_bias=1.12)

    # 2. Barrel 2 at (0.04, 0.36) (radius 0.30m, height 0.76m, Z = 0.0m to 0.76m)
    b2_x, b2_y = 0.04, 0.36
    for s_i in range(25):
        bz = s_i * 0.03
        t = s_i / 25.0
        rad = 0.25 + math.sin(t * math.pi) * 0.05
        builder.fill_world_cylinder_z(b2_x, b2_y, bz, bz + 0.03, r_outer=rad, r_inner=0.0, mat_key="charred_timber", shade_bias=0.96)

    # 4 Iron hoops on Barrel 2
    for hz in (0.09, 0.28, 0.48, 0.67):
        t = (hz / 0.76)
        rad = 0.25 + math.sin(t * math.pi) * 0.05
        builder.fill_world_cylinder_z(b2_x, b2_y, hz - 0.02, hz + 0.02, r_outer=rad + 0.015, r_inner=rad - 0.02, mat_key="wrought_iron", shade_bias=1.02)

    # 3. Large Slatted Munitions Crate at (0.42, -0.22) (0.64m x 0.64m x 0.62m)
    c1_x, c1_y = 0.42, -0.22
    # Crate timber body
    builder.fill_world_box(c1_x - 0.32, c1_x + 0.32, c1_y - 0.32, c1_y + 0.32, 0.00, 0.62, mat_key="charred_timber", shade_bias=0.98)
    # Slat grooving (horizontal slat seams)
    for sz in (0.15, 0.30, 0.45):
        builder.fill_world_box(c1_x - 0.33, c1_x + 0.33, c1_y - 0.33, c1_y + 0.33, sz - 0.01, sz + 0.01, mat_key="charred_timber", shade_bias=0.82)

    # Iron corner brackets & bronze rivets on Crate 1
    for cx in (c1_x - 0.32, c1_x + 0.32):
        for cy in (c1_y - 0.32, c1_y + 0.32):
            builder.fill_world_box(cx - 0.04, cx + 0.04, cy - 0.04, cy + 0.04, 0.00, 0.62, mat_key="wrought_iron", shade_bias=1.02)
            for rz in (0.06, 0.56):
                builder.fill_world_box(cx - 0.045, cx + 0.045, cy - 0.045, cy + 0.045, rz - 0.02, rz + 0.02, mat_key="bronze", shade_bias=1.14)

    # 4. Small Slatted Supply Crate at (-0.22, -0.32) (0.52m x 0.52m x 0.48m)
    c2_x, c2_y = -0.22, -0.32
    builder.fill_world_box(c2_x - 0.26, c2_x + 0.26, c2_y - 0.26, c2_y + 0.26, 0.00, 0.48, mat_key="charred_timber", shade_bias=0.96)
    for sz in (0.16, 0.32):
        builder.fill_world_box(c2_x - 0.27, c2_x + 0.27, c2_y - 0.27, c2_y + 0.27, sz - 0.01, sz + 0.01, mat_key="charred_timber", shade_bias=0.80)

    # Iron corner brackets on Crate 2
    for cx in (c2_x - 0.26, c2_x + 0.26):
        for cy in (c2_y - 0.26, c2_y + 0.26):
            builder.fill_world_box(cx - 0.035, cx + 0.035, cy - 0.035, cy + 0.035, 0.00, 0.48, mat_key="wrought_iron", shade_bias=1.02)

    builder.build_mesh_object()
    out_path = os.path.join(out_dir, "clutter_wooden_crates_barrels.glb")
    export_environment_glb(out_path)


# ==============================================================================
# MAIN BATCH BUILDER RUNNER
# ==============================================================================
def main() -> None:
    print("=" * 72)
    print("STARTING WAVE 1B: CRYPT, CATACOMBS & CLUTTER MICRO-VOXEL BLENDER BUILD")
    print(f"Target Directory: {OUT_DIR}")
    print("=" * 72)
    os.makedirs(OUT_DIR, exist_ok=True)
    t_start = time.time()

    builders = [
        # Modular Crypt Kit (8 models)
        ("crypt_corridor_vault_4x4.glb", build_voxel_crypt_corridor_vault_4x4),
        ("crypt_wall_ossuary_4x4.glb", build_voxel_crypt_wall_ossuary_4x4),
        ("crypt_archway_portcullis_4x4.glb", build_voxel_crypt_archway_portcullis_4x4),
        ("crypt_pillar.glb", build_voxel_crypt_pillar),
        ("crypt_containment_hull.glb", build_voxel_crypt_containment_hull),
        ("crypt_iron_gate_cell_4x4.glb", build_voxel_crypt_iron_gate_cell_4x4),
        ("crypt_drowned_cistern_4x4.glb", build_voxel_crypt_drowned_cistern_4x4),
        ("crypt_rotting_bookshelf_4x4.glb", build_voxel_crypt_rotting_bookshelf_4x4),
        # Crypt Focal Props (9 models)
        ("crypt_altar.glb", build_voxel_crypt_altar),
        ("crypt_sarcophagus_ornate.glb", build_voxel_crypt_sarcophagus_ornate),
        ("crypt_lectern_grimoire.glb", build_voxel_crypt_lectern_grimoire),
        ("crypt_hanging_cage.glb", build_voxel_crypt_hanging_cage),
        ("crypt_plague_cauldron.glb", build_voxel_crypt_plague_cauldron),
        ("crypt_weeping_statue_pedestal.glb", build_voxel_crypt_weeping_statue_pedestal),
        ("crypt_sunken_bell_crater.glb", build_voxel_crypt_sunken_bell_crater),
        ("crypt_ritual_obelisk.glb", build_voxel_crypt_ritual_obelisk),
        ("standing_iron_brazier.glb", build_voxel_standing_iron_brazier),
        # Clutter Assets (4 models)
        ("clutter_ceiling_chains_roots.glb", build_voxel_clutter_ceiling_chains_roots),
        ("clutter_melted_candle_cluster.glb", build_voxel_clutter_melted_candle_cluster),
        ("clutter_rubble_bones_pile.glb", build_voxel_clutter_rubble_bones_pile),
        ("clutter_wooden_crates_barrels.glb", build_voxel_clutter_wooden_crates_barrels),
    ]

    for idx, (filename, fn) in enumerate(builders, start=1):
        b_t0 = time.time()
        print(f"[{idx:02d}/21] Building {filename}...")
        fn(OUT_DIR)
        b_dur = time.time() - b_t0
        target_file = os.path.join(OUT_DIR, filename)
        f_size = os.path.getsize(target_file) if os.path.exists(target_file) else 0
        print(f"        -> Completed in {b_dur:.2f}s ({f_size:,} bytes)")

    total_dur = time.time() - t_start
    print("=" * 72)
    print(f"WAVE 1B BUILD COMPLETE: All 21 models successfully generated in {total_dur:.2f}s")
    print("=" * 72)


if __name__ == "__main__":
    main()
