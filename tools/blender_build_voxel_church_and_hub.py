"""
tools/blender_build_voxel_church_and_hub.py
===========================================
Procedural Micro-Voxel Generator for Milestone 1 (Requirement R2):
Wave 1A Church Sanctuary & Hub Stations (16 .glb models).

All models are constructed using the Hyper-Detailed Ultra-Realistic
Micro-Voxel art style via `EnvironmentVoxelBuilder` with 26-neighborhood
cavity ambient occlusion, directional face shading, and deterministic
vertex color baking matching GrimdarkMaterialLibrary.
"""

import math
import os
import sys
import bpy
import bmesh

# Ensure tools directory is in sys.path
tools_dir = os.path.dirname(os.path.abspath(__file__))
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

from blender_micro_voxel_kit import (
    create_environment_voxel_palette,
    EnvironmentVoxelBuilder,
    export_environment_glb,
    make_environment_pbr_material,
)


def clear_scene() -> dict[str, bpy.types.Material]:
    """Clears factory scene and returns fresh 23-material Gothic environment palette."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return create_environment_voxel_palette()


def carve_world_cylinder_y(b: EnvironmentVoxelBuilder, cx_w: float, cz_w: float, wy0: float, wy1: float, r_outer: float) -> None:
    """Helper to carve a cylinder along Y axis."""
    s = b.voxel_size
    iy0, iy1 = int(round(min(wy0, wy1) / s)), int(round(max(wy0, wy1) / s))
    ir = int(math.ceil(r_outer / s)) + 1
    icx, icz = int(round(cx_w / s)), int(round(cz_w / s))
    for iy in range(iy0, iy1 + 1):
        for dx in range(-ir, ir + 1):
            for dz in range(-ir, ir + 1):
                wx = (icx + dx) * s - cx_w
                wz = (icz + dz) * s - cz_w
                if math.sqrt(wx * wx + wz * wz) <= r_outer:
                    b.voxels.pop((icx + dx, iy, icz + dz), None)


# ==============================================================================
# 1. MODULAR ARCHITECTURE: floor_stone_4x4.glb
# ==============================================================================

def build_floor_stone_4x4(out_dir: str, palette: dict[str, bpy.types.Material] | None = None) -> None:
    """
    1. floor_stone_4x4.glb (4.0m x 4.0m x 0.375m floor slab).
    Top surface at Z = 0.0, underside at Z = -0.37m.
    Carved stone perimeter trim, alternating weathered and rough cobble flagstones.
    """
    if palette is None:
        palette = clear_scene()
    print("[Wave 1A] Building floor_stone_4x4...")
    b = EnvironmentVoxelBuilder("floor_stone_4x4", voxel_size=0.04, palette=palette)

    # Base stone slab (underside down to -0.36m)
    b.fill_world_box(-2.0, 2.0, -2.0, 2.0, -0.36, -0.08, "weathered_stone", shade_bias=0.88)

    # Perimeter border trim in carved stone (0.20m border frame)
    b.fill_world_box(-2.0, 2.0, -2.0, -1.80, -0.08, 0.0, "carved_stone_trim", shade_bias=1.04)
    b.fill_world_box(-2.0, 2.0, 1.80, 2.0, -0.08, 0.0, "carved_stone_trim", shade_bias=1.04)
    b.fill_world_box(-2.0, -1.80, -1.80, 1.80, -0.08, 0.0, "carved_stone_trim", shade_bias=1.04)
    b.fill_world_box(1.80, 2.0, -1.80, 1.80, -0.08, 0.0, "carved_stone_trim", shade_bias=1.04)

    # 6x6 interior flagstone tiles with recessed mortar joints
    tile_span = 3.60
    n_tiles = 6
    step = tile_span / n_tiles
    for ix in range(n_tiles):
        for iy in range(n_tiles):
            x0 = -1.80 + ix * step + 0.02
            x1 = -1.80 + (ix + 1) * step - 0.02
            y0 = -1.80 + iy * step + 0.02
            y1 = -1.80 + (iy + 1) * step - 0.02
            mat_k = "cobble_flagstone" if ((ix + iy) % 2 == 0) else "weathered_stone"
            bias = 0.96 + ((ix * 7 + iy * 13) % 9) * 0.015
            b.fill_world_box(x0, x1, y0, y1, -0.08, 0.0, mat_k, shade_bias=bias)

    # Under-slab mortar joints
    b.fill_world_box(-1.80, 1.80, -1.80, 1.80, -0.08, -0.04, "cobble_flagstone", shade_bias=0.82)

    b.build_mesh_object()
    out_path = os.path.join(out_dir, "floor_stone_4x4.glb")
    export_environment_glb(out_path)


# ==============================================================================
# 2. MODULAR ARCHITECTURE: wall_stone_solid.glb
# ==============================================================================

def build_wall_stone_solid(out_dir: str, palette: dict[str, bpy.types.Material] | None = None) -> None:
    """
    2. wall_stone_solid.glb (4.28m wide x 0.64m deep x 4.05m tall solid wall).
    Solid 0.48m core thickness for light-bleed isolation (AGENTS.md Rule 9.4),
    stepped plinth base, staggered ashlar masonry courses, side pilaster buttresses,
    and carved stone cornice with wrought-iron tie plates.
    """
    if palette is None:
        palette = clear_scene()
    print("[Wave 1A] Building wall_stone_solid...")
    b = EnvironmentVoxelBuilder("wall_stone_solid", voxel_size=0.04, palette=palette)

    # Core ashlar masonry wall (0.48m thick, X in [-2.08, 2.08], Y in [-0.24, 0.24])
    b.fill_world_box(-2.08, 2.08, -0.24, 0.24, 0.0, 4.0, "weathered_stone", shade_bias=0.98)

    # Stepped base plinth (0.56m thick, 0.32m high)
    b.fill_world_box(-2.14, 2.14, -0.28, 0.28, 0.0, 0.32, "carved_stone_trim", shade_bias=1.02)
    b.fill_world_box(-2.14, 2.14, -0.26, 0.26, 0.32, 0.40, "carved_stone_trim", shade_bias=1.00)

    # Upper cornice moulding (0.56m thick, Z in [3.84, 4.05])
    b.fill_world_box(-2.14, 2.14, -0.28, 0.28, 3.84, 4.05, "carved_stone_trim", shade_bias=1.04)

    # Staggered ashlar stone texture courses on front (Y = -0.24) and rear (Y = 0.24)
    for course_i in range(8):
        z0 = 0.40 + course_i * 0.42 + 0.02
        z1 = 0.40 + (course_i + 1) * 0.42 - 0.02
        offset = 0.25 if (course_i % 2 == 1) else 0.0
        for block_j in range(8):
            bx0 = -2.00 + offset + block_j * 0.50 + 0.02
            bx1 = min(2.04, bx0 + 0.46)
            if bx0 >= 2.04:
                continue
            bias = 0.94 + ((course_i * 5 + block_j * 11) % 9) * 0.02
            mat_k = "weathered_stone" if (block_j % 3 != 0) else "cobble_flagstone"
            # Front face relief
            b.fill_world_box(bx0, bx1, -0.25, -0.24, z0, z1, mat_k, shade_bias=bias)
            # Rear face relief
            b.fill_world_box(bx0, bx1, 0.24, 0.25, z0, z1, mat_k, shade_bias=bias)

    # Side pilasters / corner quoins (X in [-2.14, -1.90] and [1.90, 2.14], depth to 0.64m)
    for sx in (-2.02, 2.02):
        b.fill_world_box(sx - 0.12, sx + 0.12, -0.32, 0.32, 0.0, 4.05, "carved_stone_trim", shade_bias=1.02)
        # Iron structural tie plates at 3 heights
        for tz in (0.96, 2.32, 3.68):
            b.fill_world_box(sx - 0.08, sx + 0.08, -0.33, -0.31, tz, tz + 0.12, "wrought_iron", shade_bias=1.10)
            b.fill_world_box(sx - 0.08, sx + 0.08, 0.31, 0.33, tz, tz + 0.12, "wrought_iron", shade_bias=1.10)

    # Mid-wall horizontal stringcourse belt at Z = 2.0m
    b.fill_world_box(-2.10, 2.10, -0.26, 0.26, 1.96, 2.06, "carved_stone_trim", shade_bias=1.03)

    b.build_mesh_object()
    out_path = os.path.join(out_dir, "wall_stone_solid.glb")
    export_environment_glb(out_path)


# ==============================================================================
# 3. MODULAR ARCHITECTURE: wall_stone_window.glb
# ==============================================================================

def build_wall_stone_window(out_dir: str, palette: dict[str, bpy.types.Material] | None = None) -> None:
    """
    3. wall_stone_window.glb (4.28m wide x 0.64m deep x 4.05m tall window wall).
    Solid 0.48m core with carved Gothic lancet arch window opening, stepped stone sill,
    stone mullion and transoms, leaded iron diamond lattice, and occult stained glass.
    """
    if palette is None:
        palette = clear_scene()
    print("[Wave 1A] Building wall_stone_window...")
    b = EnvironmentVoxelBuilder("wall_stone_window", voxel_size=0.04, palette=palette)

    # Core ashlar masonry wall
    b.fill_world_box(-2.08, 2.08, -0.24, 0.24, 0.0, 4.0, "weathered_stone", shade_bias=0.98)
    # Stepped base plinth
    b.fill_world_box(-2.14, 2.14, -0.28, 0.28, 0.0, 0.32, "carved_stone_trim", shade_bias=1.02)
    b.fill_world_box(-2.14, 2.14, -0.26, 0.26, 0.32, 0.40, "carved_stone_trim", shade_bias=1.00)
    # Upper cornice moulding
    b.fill_world_box(-2.14, 2.14, -0.28, 0.28, 3.84, 4.05, "carved_stone_trim", shade_bias=1.04)

    # Carve Gothic lancet window opening
    b.carve_world_box(-0.68, 0.68, -0.32, 0.32, 1.16, 2.70)
    b.carve_pointed_arch(cx=0.0, cy=0.0, base_z=1.16, spring_z=2.70, peak_z=3.35, span_w=1.36, depth_y=0.64)

    # Stepped stone window sill
    b.fill_world_box(-0.84, 0.84, -0.31, 0.31, 1.04, 1.16, "carved_stone_trim", shade_bias=1.04)
    b.fill_world_box(-0.76, 0.76, -0.28, 0.28, 0.94, 1.04, "carved_stone_trim", shade_bias=1.00)

    # Lancet arch frame surround in carved stone
    b.fill_world_box(-0.80, -0.68, -0.28, 0.28, 1.16, 2.70, "carved_stone_trim", shade_bias=1.02)
    b.fill_world_box(0.68, 0.80, -0.28, 0.28, 1.16, 2.70, "carved_stone_trim", shade_bias=1.02)
    b.fill_pointed_arch(cx=0.0, cy=0.0, base_z=1.16, spring_z=2.70, peak_z=3.35, span_w=1.36, depth_y=0.56, wall_thick=0.12, mat_key="carved_stone_trim", shade_bias=1.04)

    # Center vertical mullion and horizontal transoms
    b.fill_world_box(-0.06, 0.06, -0.12, 0.12, 1.16, 3.10, "carved_stone_trim", shade_bias=1.03)
    b.fill_world_box(-0.66, 0.66, -0.11, 0.11, 1.84, 1.92, "carved_stone_trim", shade_bias=1.02)
    b.fill_world_box(-0.66, 0.66, -0.11, 0.11, 2.52, 2.60, "carved_stone_trim", shade_bias=1.02)

    # Leaded iron diamond lattice
    for iz_lvl in (1.50, 2.20, 2.90):
        b.fill_world_box(-0.64, 0.64, -0.02, 0.02, iz_lvl - 0.02, iz_lvl + 0.02, "wrought_iron", shade_bias=1.08)

    # Occult stained glass window pane
    b.fill_world_box(-0.64, 0.64, -0.015, 0.015, 1.16, 2.70, "lead_glass", shade_bias=1.08)
    for ix_g in (-0.34, 0.34):
        b.fill_world_box(ix_g - 0.12, ix_g + 0.12, -0.015, 0.015, 2.0, 2.24, "occult_rune", shade_bias=1.15)

    # Side pilasters & iron tie plates
    for sx in (-2.02, 2.02):
        b.fill_world_box(sx - 0.12, sx + 0.12, -0.32, 0.32, 0.0, 4.05, "carved_stone_trim", shade_bias=1.02)
        for tz in (0.96, 2.32, 3.68):
            b.fill_world_box(sx - 0.08, sx + 0.08, -0.33, -0.31, tz, tz + 0.12, "wrought_iron", shade_bias=1.10)
            b.fill_world_box(sx - 0.08, sx + 0.08, 0.31, 0.33, tz, tz + 0.12, "wrought_iron", shade_bias=1.10)

    b.build_mesh_object()
    out_path = os.path.join(out_dir, "wall_stone_window.glb")
    export_environment_glb(out_path)


# ==============================================================================
# 4. MODULAR ARCHITECTURE: wall_stone_arch_door.glb
# ==============================================================================

def build_wall_stone_arch_door(out_dir: str, palette: dict[str, bpy.types.Material] | None = None) -> None:
    """
    4. wall_stone_arch_door.glb (4.28m wide x 0.64m deep x 4.05m tall arch doorway).
    Clear walkable doorway opening (2.4m wide x 3.45m high, Z >= 2.45m),
    pointed arch voussoirs, keystone, engaged jambs, capitals, and wrought-iron hinge pintles.
    """
    if palette is None:
        palette = clear_scene()
    print("[Wave 1A] Building wall_stone_arch_door...")
    b = EnvironmentVoxelBuilder("wall_stone_arch_door", voxel_size=0.04, palette=palette)

    # Core ashlar masonry wall
    b.fill_world_box(-2.08, 2.08, -0.24, 0.24, 0.0, 4.0, "weathered_stone", shade_bias=0.98)
    # Stepped base plinth (outer edges only)
    b.fill_world_box(-2.14, -1.24, -0.28, 0.28, 0.0, 0.32, "carved_stone_trim", shade_bias=1.02)
    b.fill_world_box(1.24, 2.14, -0.28, 0.28, 0.0, 0.32, "carved_stone_trim", shade_bias=1.02)
    # Upper cornice moulding
    b.fill_world_box(-2.14, 2.14, -0.28, 0.28, 3.84, 4.05, "carved_stone_trim", shade_bias=1.04)

    # Carve walkable doorway opening (width 2.40m, height 3.45m >= 2.45m!)
    b.carve_world_box(-1.20, 1.20, -0.32, 0.32, 0.0, 2.65)
    b.carve_pointed_arch(cx=0.0, cy=0.0, base_z=0.0, spring_z=2.65, peak_z=3.45, span_w=2.40, depth_y=0.64)

    # Engaged doorway jambs and moulded capitals
    for sx in (-1.30, 1.30):
        x0 = sx - 0.10 if sx < 0 else sx - 0.02
        x1 = sx + 0.02 if sx < 0 else sx + 0.10
        # Jamb column
        b.fill_world_box(x0, x1, -0.28, 0.28, 0.0, 2.65, "carved_stone_trim", shade_bias=1.03)
        # Moulded capital
        b.fill_world_box(sx - 0.14, sx + 0.14, -0.30, 0.30, 2.65, 2.78, "carved_stone_trim", shade_bias=1.06)
        # Iron door hinge pintles
        for hz in (0.65, 2.15):
            b.fill_world_box(sx - 0.06, sx + 0.06, -0.29, -0.27, hz, hz + 0.08, "wrought_iron", shade_bias=1.12)
            b.fill_world_box(sx - 0.06, sx + 0.06, 0.27, 0.29, hz, hz + 0.08, "wrought_iron", shade_bias=1.12)

    # Pointed arch voussoirs around doorway
    b.fill_pointed_arch(cx=0.0, cy=0.0, base_z=0.0, spring_z=2.65, peak_z=3.45, span_w=2.40, depth_y=0.58, wall_thick=0.18, mat_key="carved_stone_trim", shade_bias=1.04)

    # Prominent central carved keystone at apex
    b.fill_world_box(-0.16, 0.16, -0.30, 0.30, 3.44, 3.65, "carved_stone_trim", shade_bias=1.08)

    # Side pilasters & iron tie plates
    for sx in (-2.02, 2.02):
        b.fill_world_box(sx - 0.12, sx + 0.12, -0.32, 0.32, 0.0, 4.05, "carved_stone_trim", shade_bias=1.02)
        for tz in (0.96, 2.32, 3.68):
            b.fill_world_box(sx - 0.08, sx + 0.08, -0.33, -0.31, tz, tz + 0.12, "wrought_iron", shade_bias=1.10)
            b.fill_world_box(sx - 0.08, sx + 0.08, 0.31, 0.33, tz, tz + 0.12, "wrought_iron", shade_bias=1.10)

    b.build_mesh_object()
    out_path = os.path.join(out_dir, "wall_stone_arch_door.glb")
    export_environment_glb(out_path)


# ==============================================================================
# 5. MODULAR ARCHITECTURE: roof_gothic_vault_4x4.glb
# ==============================================================================

def build_roof_gothic_vault_4x4(out_dir: str, palette: dict[str, bpy.types.Material] | None = None) -> None:
    """
    5. roof_gothic_vault_4x4.glb (4.18m x 4.18m x 1.01m Gothic groined vault).
    Solid 0.48m ceiling deck, exterior slate cap, transverse and diagonal carved ribs,
    keystone boss with wrought-iron strap bindings, and timber purlins.
    """
    if palette is None:
        palette = clear_scene()
    print("[Wave 1A] Building roof_gothic_vault_4x4...")
    b = EnvironmentVoxelBuilder("roof_gothic_vault_4x4", voxel_size=0.04, palette=palette)

    # Solid ceiling deck (Z in [0.0, 0.48])
    b.fill_world_box(-2.08, 2.08, -2.08, 2.08, 0.0, 0.48, "weathered_stone", shade_bias=0.96)

    # Exterior roof slate cap (Z in [0.48, 0.66])
    b.fill_world_box(-2.09, 2.09, -2.09, 2.09, 0.48, 0.66, "dark_slate_roof", shade_bias=1.00)

    # Perimeter moulded stone cornice on underside (Z in [-0.12, 0.0])
    b.fill_world_box(-2.08, 2.08, -2.08, -1.94, -0.12, 0.0, "carved_stone_trim", shade_bias=1.02)
    b.fill_world_box(-2.08, 2.08, 1.94, 2.08, -0.12, 0.0, "carved_stone_trim", shade_bias=1.02)
    b.fill_world_box(-2.08, -1.94, -1.94, 1.94, -0.12, 0.0, "carved_stone_trim", shade_bias=1.02)
    b.fill_world_box(1.94, 2.08, -1.94, 1.94, -0.12, 0.0, "carved_stone_trim", shade_bias=1.02)

    # Transverse ribs along X and Y axes (width 0.28m, descending to Z = -0.28m)
    b.fill_world_box(-2.04, 2.04, -0.14, 0.14, -0.28, 0.0, "carved_stone_trim", shade_bias=1.04)
    b.fill_world_box(-0.14, 0.14, -2.04, 2.04, -0.28, 0.0, "carved_stone_trim", shade_bias=1.04)

    # Diagonal groin ribs crossing at 45 degrees
    s = b.voxel_size
    n_diag = int(round(2.00 / s))
    for di in range(-n_diag, n_diag + 1):
        w_diag = di * s
        # Rib along X = Y
        b.fill_world_box(w_diag - 0.10, w_diag + 0.10, w_diag - 0.10, w_diag + 0.10, -0.26, 0.0, "carved_stone_trim", shade_bias=1.03)
        # Rib along X = -Y
        b.fill_world_box(w_diag - 0.10, w_diag + 0.10, -w_diag - 0.10, -w_diag + 0.10, -0.26, 0.0, "carved_stone_trim", shade_bias=1.03)

    # Heavy timber purlin beams
    for po in (-1.35, 1.35):
        b.fill_world_box(-1.92, 1.92, po - 0.08, po + 0.08, -0.14, 0.0, "charred_timber", shade_bias=0.92)
        b.fill_world_box(po - 0.08, po + 0.08, -1.92, 1.92, -0.14, 0.0, "charred_timber", shade_bias=0.92)

    # Central carved keystone boss (descending to Z = -0.35m)
    b.fill_world_box(-0.28, 0.28, -0.28, 0.28, -0.35, -0.10, "carved_stone_trim", shade_bias=1.06)
    # Wrought-iron strap bindings on keystone
    b.fill_world_box(-0.31, 0.31, -0.06, 0.06, -0.36, -0.12, "wrought_iron", shade_bias=1.12)
    b.fill_world_box(-0.06, 0.06, -0.31, 0.31, -0.36, -0.12, "wrought_iron", shade_bias=1.12)

    # 4 Secondary intersection bosses at (±1.35, ±1.35)
    for sx in (-1.35, 1.35):
        for sy in (-1.35, 1.35):
            b.fill_world_box(sx - 0.16, sx + 0.16, sy - 0.16, sy + 0.16, -0.22, -0.08, "carved_stone_trim", shade_bias=1.04)
            b.fill_world_box(sx - 0.18, sx + 0.18, sy - 0.04, sy + 0.04, -0.23, -0.09, "wrought_iron", shade_bias=1.10)

    b.build_mesh_object()
    out_path = os.path.join(out_dir, "roof_gothic_vault_4x4.glb")
    export_environment_glb(out_path)


# ==============================================================================
# 6. MODULAR ARCHITECTURE: stairs_stone_4x4.glb
# ==============================================================================

def build_stairs_stone_4x4(out_dir: str, palette: dict[str, bpy.types.Material] | None = None) -> None:
    """
    6. stairs_stone_4x4.glb (4.04m wide x 4.045m deep x 4.85m tall stone staircase).
    Descends 4.0m vertically from top landing (Y = -2.0, Z = 0.0) to bottom (Y = +2.0, Z = -4.0)
    with 16 stepped ashlar treads, underlying masonry core, and stepped side stringer parapets.
    """
    if palette is None:
        palette = clear_scene()
    print("[Wave 1A] Building stairs_stone_4x4...")
    b = EnvironmentVoxelBuilder("stairs_stone_4x4", voxel_size=0.04, palette=palette)

    num_steps = 16
    step_run = 4.00 / num_steps   # 0.25m per step
    step_rise = 4.00 / num_steps  # 0.25m per step

    # 16 Stepped treads and inclined vaulted masonry slab (0.48m thick so stairs are walkable above and clear below)
    for i in range(num_steps):
        top_z = -i * step_rise
        bot_z = max(-4.00, top_z - 0.48)
        y_front = -2.00 + i * step_run
        y_back = y_front + step_run

        # Inclined masonry slab under this step only (y_front .. y_back)
        b.fill_world_box(-1.68, 1.68, y_front, y_back, bot_z, top_z - 0.06, "weathered_stone", shade_bias=0.92)

        # Flagstone tread slab
        b.fill_world_box(-1.68, 1.68, y_front, y_back, top_z - 0.06, top_z, "cobble_flagstone", shade_bias=1.02)
        # Nosing strip
        b.fill_world_box(-1.68, 1.68, y_front - 0.02, y_front + 0.02, top_z - 0.06, top_z, "carved_stone_trim", shade_bias=1.04)

    # Stepped side parapets / stringers (X in [-2.02, -1.68] and [1.68, 2.02])
    for sx_side in (-1.0, 1.0):
        x0 = -2.02 if sx_side < 0 else 1.68
        x1 = -1.68 if sx_side < 0 else 2.02

        # Stepped parapet rising 0.45m above the treads along the inclined stringer
        for i in range(num_steps):
            top_z = -i * step_rise
            bot_z = max(-4.16, top_z - 0.56)
            y_front = -2.00 + i * step_run
            y_back = y_front + step_run
            # Parapet wall & stringer beam
            b.fill_world_box(x0, x1, y_front, y_back, bot_z, top_z + 0.38, "weathered_stone", shade_bias=0.96)
            # Stone coping
            b.fill_world_box(x0, x1, y_front, y_back, top_z + 0.38, top_z + 0.45, "carved_stone_trim", shade_bias=1.05)
            # Iron studs on coping
            b.fill_world_box(x0 + 0.08, x1 - 0.08, y_front + 0.10, y_front + 0.15, top_z + 0.45, top_z + 0.47, "wrought_iron", shade_bias=1.12)

    b.build_mesh_object()
    out_path = os.path.join(out_dir, "stairs_stone_4x4.glb")
    export_environment_glb(out_path)


# ==============================================================================
# 7. MODULAR ARCHITECTURE: wall_lantern_sconce.glb
# ==============================================================================

def build_wall_lantern_sconce(out_dir: str, palette: dict[str, bpy.types.Material] | None = None) -> None:
    """
    7. wall_lantern_sconce.glb (0.28m wide x 0.54m deep x 0.47m tall wall sconce).
    Wrought-iron mounting plate, scrolled supporting bracket arm, hexagonal lantern cage
    with peaked canopy, leaded frosted glass panels, and emissive candle flame core.
    """
    if palette is None:
        palette = clear_scene()
    print("[Wave 1A] Building wall_lantern_sconce...")
    b = EnvironmentVoxelBuilder("wall_lantern_sconce", voxel_size=0.015, palette=palette)

    # 1. Wall mounting plate (flush at Y = 0.0m)
    b.fill_world_box(-0.06, 0.06, 0.0, 0.03, -0.14, 0.14, "wrought_iron", shade_bias=1.05)

    # 2. Horizontal iron arm extending outward to Y = 0.44m
    b.fill_world_box(-0.02, 0.02, 0.03, 0.44, 0.03, 0.07, "wrought_iron", shade_bias=1.08)

    # Diagonal scroll brace
    n_pts = 16
    for pt in range(n_pts):
        t = pt / float(n_pts)
        py = 0.03 + t * 0.32
        pz = -0.12 + t * 0.16 + math.sin(t * math.pi) * 0.03
        b.fill_world_box(-0.018, 0.018, py - 0.015, py + 0.015, pz - 0.015, pz + 0.015, "wrought_iron", shade_bias=1.06)

    # 3. Hexagonal Lantern Cage (center at Y = 0.38m, Z = -0.15m)
    cy = 0.38
    cz = -0.15
    r_cage = 0.12

    # Top peaked canopy cap (Z in [-0.02, 0.10])
    for iz_c in range(8):
        tz = iz_c / 7.0
        cur_z = -0.02 + tz * 0.12
        cur_r = r_cage * (1.0 - tz) + 0.015
        b.fill_world_cylinder_z(0.0, cy, cur_z, cur_z + 0.015, cur_r, mat_key="wrought_iron", shade_bias=1.10, octagonal=True)

    # Hanging top loop (Z in [0.10, 0.14])
    b.fill_world_box(-0.02, 0.02, cy - 0.02, cy + 0.02, 0.10, 0.14, "wrought_iron", shade_bias=1.12)

    # Bottom basin (Z in [-0.33, -0.28])
    for iz_b in range(4):
        tz = iz_b / 3.0
        cur_z = -0.33 + tz * 0.05
        cur_r = 0.03 + tz * (r_cage - 0.03)
        b.fill_world_cylinder_z(0.0, cy, cur_z, cur_z + 0.015, cur_r, mat_key="wrought_iron", shade_bias=1.06, octagonal=True)

    # 6 vertical iron corner struts
    for i_strut in range(6):
        ang = i_strut * (math.pi / 3.0)
        sx = math.sin(ang) * r_cage
        sy = cy + math.cos(ang) * r_cage
        b.fill_world_box(sx - 0.012, sx + 0.012, sy - 0.012, sy + 0.012, -0.28, -0.02, "wrought_iron", shade_bias=1.10)

    # Frosted leaded glass panels (Z in [-0.28, -0.02])
    b.fill_world_cylinder_z(0.0, cy, -0.28, -0.02, r_cage - 0.015, r_inner=r_cage - 0.03, mat_key="lead_glass", shade_bias=1.15, octagonal=True)

    # Interior candle and flame core
    b.fill_world_cylinder_z(0.0, cy, -0.28, -0.17, 0.03, mat_key="wax", shade_bias=1.05)
    b.fill_world_cylinder_z(0.0, cy, -0.17, -0.11, 0.022, mat_key="candle_flame", shade_bias=1.35)

    b.build_mesh_object()
    out_path = os.path.join(out_dir, "wall_lantern_sconce.glb")
    export_environment_glb(out_path)


# ==============================================================================
# 8. EXTERIOR CHURCH: church_foundation_plinth.glb
# ==============================================================================

def build_church_foundation_plinth(out_dir: str, palette: dict[str, bpy.types.Material] | None = None) -> None:
    """
    8. church_foundation_plinth.glb (12.70m x 23.125m x 2.755m deep foundation).
    Preserves exact Cutout 1 (stairwell & crypt opening X:[-4.5, 4.5], Y:[-0.5, 12.5]),
    Cutout 2 (subterranean chamber clearance X:[-7.0, 7.0], Y:[1.8, 14.0], Z:[-3.0, -0.5]),
    and 5 Grand South entrance steps descending from local Z = 0.0 to -0.88m with cheek walls.
    """
    if palette is None:
        palette = clear_scene()
    print("[Wave 1A] Building church_foundation_plinth...")
    b = EnvironmentVoxelBuilder("church_foundation_plinth", voxel_size=0.08, palette=palette)

    # Main 2.5m deep plinth block: X in [-6.35, 6.35], Y in [-8.35, 12.60], Z in [-2.50, 0.0]
    b.fill_world_box(-6.35, 6.35, -8.35, 12.60, -2.50, 0.0, "weathered_stone", shade_bias=0.96)

    # Top surface perimeter stone moulding (Z in [0.0, 0.25])
    b.fill_world_box(-6.35, 6.35, -8.35, 12.60, 0.0, 0.25, "carved_stone_trim", shade_bias=1.02)

    # CUTOUT 1: Upper stairwell & crypt opening (CRITICAL REQUIREMENT)
    # Local X in [-4.5, 4.5], local Y in [-0.5, 12.5], Z in [-2.60, 0.35]
    b.carve_world_box(-4.50, 4.50, -0.50, 12.50, -2.60, 0.35)

    # CUTOUT 2: Subterranean Chamber clearance (CRITICAL REQUIREMENT)
    # Local X in [-7.0, 7.0], local Y in [1.80, 14.0], Z in [-3.0, -0.50]
    b.carve_world_box(-7.00, 7.00, 1.80, 14.00, -3.00, -0.50)

    # Grand South entrance steps (Y from -8.25 descending South to -10.35)
    # 5 steps: step_run = 0.42m, step_rise = 0.18m, width 4.20m (X in [-2.10, 2.10])
    num_steps = 5
    step_run = 0.42
    step_rise = 0.18
    for i in range(num_steps):
        top_z = -i * step_rise
        y_back = -8.25 - i * step_run
        y_front = y_back - step_run
        b.fill_world_box(-2.10, 2.10, y_front, -8.25, -2.50, top_z, "cobble_flagstone", shade_bias=1.00)
        # Stone nosing on each tread
        b.fill_world_box(-2.10, 2.10, y_front, y_front + 0.06, top_z - 0.04, top_z, "carved_stone_trim", shade_bias=1.04)

    # Flanking stone cheek walls / parapets beside the entrance steps
    for sx in (-2.35, 2.35):
        b.fill_world_box(sx - 0.26, sx + 0.26, -10.52, -8.25, -2.50, 0.25, "carved_stone_trim", shade_bias=1.02)
        # Iron lantern stanchions atop cheek walls
        b.fill_world_box(sx - 0.08, sx + 0.08, -10.40, -10.24, 0.25, 0.40, "wrought_iron", shade_bias=1.12)

    b.build_mesh_object()
    out_path = os.path.join(out_dir, "church_foundation_plinth.glb")
    export_environment_glb(out_path)


# ==============================================================================
# 9. EXTERIOR CHURCH: church_front_gable_rose.glb
# ==============================================================================

def build_church_front_gable_rose(out_dir: str, palette: dict[str, bpy.types.Material] | None = None) -> None:
    """
    9. church_front_gable_rose.glb (12.77m wide x 0.64m deep x 6.76m tall front gable).
    45-degree triangular ashlar stone wall with sloping stone coping, apex cross,
    and a recessed circular Rose Window (diameter 3.2m) with 8 radial tracery spokes
    and occult stained glass.
    """
    if palette is None:
        palette = clear_scene()
    print("[Wave 1A] Building church_front_gable_rose...")
    b = EnvironmentVoxelBuilder("church_front_gable_rose", voxel_size=0.08, palette=palette)

    # Bottom horizontal cornice moulding (Z in [0.0, 0.26])
    b.fill_world_box(-6.35, 6.35, -0.30, 0.30, 0.0, 0.26, "carved_stone_trim", shade_bias=1.04)

    # 45-degree triangular gable ashlar wall
    s = b.voxel_size
    n_levels = int(round(6.20 / s))
    for iz_lvl in range(n_levels):
        wz0 = iz_lvl * s
        wz1 = (iz_lvl + 1) * s
        wz_mid = (wz0 + wz1) * 0.5
        hw = max(0.0, 6.20 - wz_mid)
        # Triangular ashlar infill
        b.fill_world_box(-hw, hw, -0.26, 0.26, wz0, wz1, "weathered_stone", shade_bias=0.96)
        # Sloping coping edges on East and West
        b.fill_world_box(-hw - 0.16, -hw + 0.08, -0.30, 0.30, wz0, wz1, "carved_stone_trim", shade_bias=1.04)
        b.fill_world_box(hw - 0.08, hw + 0.16, -0.30, 0.30, wz0, wz1, "carved_stone_trim", shade_bias=1.04)

    # Apex stone cross / finial (Z in [6.20, 6.76])
    b.fill_world_box(-0.16, 0.16, -0.28, 0.28, 6.20, 6.76, "carved_stone_trim", shade_bias=1.08)
    b.fill_world_box(-0.36, 0.36, -0.16, 0.16, 6.42, 6.58, "carved_stone_trim", shade_bias=1.08)

    # Recessed Rose Window (center at X = 0.0, Z = 3.10m, radius 1.60m)
    # Carve circular hole
    carve_world_cylinder_y(b, 0.0, 3.10, -0.32, 0.32, 1.60)

    # Outer stone ring (radius 1.50m to 1.68m)
    b.fill_world_cylinder_y(0.0, 3.10, -0.28, 0.28, 1.68, r_inner=1.50, mat_key="carved_stone_trim", shade_bias=1.06)

    # Central tracery boss (radius 0.38m)
    b.fill_world_cylinder_y(0.0, 3.10, -0.24, 0.24, 0.38, mat_key="carved_stone_trim", shade_bias=1.08)

    # 8 Radial stone tracery spokes
    for i_spoke in range(8):
        ang = i_spoke * (math.pi / 4.0)
        c_a = math.cos(ang)
        s_a = math.sin(ang)
        for r_step in range(4, 18):
            rad = r_step * 0.08
            if rad < 1.52:
                px = s_a * rad
                pz = 3.10 + c_a * rad
                b.fill_world_box(px - 0.06, px + 0.06, -0.20, 0.20, pz - 0.06, pz + 0.06, "carved_stone_trim", shade_bias=1.04)

    # Stained glass disk in lead glass with glowing occult runes
    b.fill_world_cylinder_y(0.0, 3.10, -0.04, 0.04, 1.54, mat_key="lead_glass", shade_bias=1.12)
    b.fill_world_cylinder_y(0.0, 3.10, -0.04, 0.04, 0.85, r_inner=0.65, mat_key="occult_rune", shade_bias=1.25)

    b.build_mesh_object()
    out_path = os.path.join(out_dir, "church_front_gable_rose.glb")
    export_environment_glb(out_path)


# ==============================================================================
# 10. EXTERIOR CHURCH: church_pitched_roof_12x16.glb
# ==============================================================================

def build_church_pitched_roof_12x16(out_dir: str, palette: dict[str, bpy.types.Material] | None = None) -> None:
    """
    10. church_pitched_roof_12x16.glb (13.04m wide x 17.04m long x 7.51m tall pitched roof).
    Steep 45-degree Gothic cathedral roof with dark slate roof tiles,
    stone ridge cresting, decorative finials, corbelled eaves, and 4 dormer vents.
    """
    if palette is None:
        palette = clear_scene()
    print("[Wave 1A] Building church_pitched_roof_12x16...")
    b = EnvironmentVoxelBuilder("church_pitched_roof_12x16", voxel_size=0.08, palette=palette)

    # 45-degree sloped roof slabs (X in [-6.40, 6.40], Y in [-8.40, 8.40])
    s = b.voxel_size
    nx = int(round(6.40 / s))
    for ix in range(-nx, nx + 1):
        wx0 = ix * s - s * 0.5
        wx1 = ix * s + s * 0.5
        dist_x = abs((wx0 + wx1) * 0.5)
        if dist_x > 6.40:
            continue
        top_z = 6.25 - dist_x
        bot_z = max(0.0, top_z - 0.38)
        b.fill_world_box(wx0, wx1, -8.40, 8.40, bot_z, top_z, "dark_slate_roof", shade_bias=1.00)

    # Stone ridge cresting along top apex (X = 0.0, Z in [6.20, 6.55])
    b.fill_world_box(-0.24, 0.24, -8.50, 8.50, 6.20, 6.55, "carved_stone_trim", shade_bias=1.04)

    # Front and rear ridge finials (reaching Z = 7.175m)
    for y_fin in (-8.40, 8.40):
        b.fill_world_box(-0.16, 0.16, y_fin - 0.16, y_fin + 0.16, 6.55, 7.175, "carved_stone_trim", shade_bias=1.08)

    # Eaves fascia beam and corbels along East and West sides (X = ±6.40m)
    for sx in (-6.40, 6.40):
        x0 = sx - 0.18 if sx < 0 else sx - 0.06
        x1 = sx + 0.06 if sx < 0 else sx + 0.18
        b.fill_world_box(x0, x1, -8.45, 8.45, -0.15, 0.20, "carved_stone_trim", shade_bias=1.02)
        # Corbel brackets under eaves
        for iy in range(9):
            cy = -7.50 + iy * 1.88
            b.fill_world_box(x0, x1, cy - 0.14, cy + 0.14, -0.34, -0.15, "carved_stone_trim", shade_bias=1.05)

    # 4 Dormer vents at Y = ±4.0m, X = ±3.4m (Z in [2.8, 4.2])
    for dy in (-4.0, 4.0):
        for dx_s in (-1.0, 1.0):
            cx = dx_s * 3.40
            b.fill_world_box(cx - 0.45, cx + 0.45, dy - 0.55, dy + 0.55, 2.75, 3.85, "dark_slate_roof", shade_bias=1.04)
            b.fill_world_box(cx - 0.25, cx + 0.25, dy - 0.58, dy - 0.54, 2.90, 3.40, "charred_timber", shade_bias=0.88)

    b.build_mesh_object()
    out_path = os.path.join(out_dir, "church_pitched_roof_12x16.glb")
    export_environment_glb(out_path)


# ==============================================================================
# 11. EXTERIOR CHURCH: church_buttress.glb
# ==============================================================================

def build_church_buttress(out_dir: str, palette: dict[str, bpy.types.Material] | None = None) -> None:
    """
    11. church_buttress.glb (1.24m wide x 1.95m deep x 9.05m tall stepped buttress).
    Heavy 3-stage stepped Gothic exterior stone buttress with sloped weatherings
    and gabled pinnacle cap.
    """
    if palette is None:
        palette = clear_scene()
    print("[Wave 1A] Building church_buttress...")
    b = EnvironmentVoxelBuilder("church_buttress", voxel_size=0.06, palette=palette)

    # STAGE 1 (Base): Z in [0.0, 3.20], width 1.20m (X in [-0.60, 0.60]), depth 1.80m (Y in [0.0, 1.80])
    b.fill_world_box(-0.60, 0.60, 0.0, 1.80, 0.0, 3.20, "weathered_stone", shade_bias=0.96)
    # Plinth base moulding
    b.fill_world_box(-0.62, 0.62, -0.035, 1.85, 0.0, 0.28, "carved_stone_trim", shade_bias=1.02)

    # Sloped stone weathering 1: Z in [3.20, 3.65], tapers Y from 1.80m to 1.30m
    s = b.voxel_size
    n_w1 = int(round(0.45 / s))
    for i_w in range(n_w1):
        tz = i_w / float(n_w1)
        z0 = 3.20 + i_w * s
        z1 = z0 + s
        y_max = 1.80 - tz * 0.50
        b.fill_world_box(-0.62, 0.62, 0.0, y_max, z0, z1, "carved_stone_trim", shade_bias=1.04)

    # STAGE 2 (Middle): Z in [3.65, 6.20], width 1.10m (X in [-0.55, 0.55]), depth 1.30m (Y in [0.0, 1.30])
    b.fill_world_box(-0.55, 0.55, 0.0, 1.30, 3.65, 6.20, "weathered_stone", shade_bias=0.98)

    # Sloped stone weathering 2: Z in [6.20, 6.65], tapers Y from 1.30m to 0.85m
    n_w2 = int(round(0.45 / s))
    for i_w in range(n_w2):
        tz = i_w / float(n_w2)
        z0 = 6.20 + i_w * s
        z1 = z0 + s
        y_max = 1.30 - tz * 0.45
        b.fill_world_box(-0.57, 0.57, 0.0, y_max, z0, z1, "carved_stone_trim", shade_bias=1.05)

    # STAGE 3 (Top): Z in [6.65, 8.20], width 1.00m (X in [-0.50, 0.50]), depth 0.85m (Y in [0.0, 0.85])
    b.fill_world_box(-0.50, 0.50, 0.0, 0.85, 6.65, 8.20, "weathered_stone", shade_bias=1.00)

    # Gabled stone pinnacle cap (Z in [8.20, 9.045], tapering to apex at Y = 0.425m)
    n_cap = int(round(0.85 / s))
    for i_c in range(n_cap):
        tz = i_c / float(n_cap)
        z0 = 8.20 + i_c * s
        z1 = z0 + s
        hw_x = 0.52 * (1.0 - tz)
        hw_y = 0.44 * (1.0 - tz)
        b.fill_world_box(-hw_x, hw_x, 0.425 - hw_y, 0.425 + hw_y, z0, z1, "carved_stone_trim", shade_bias=1.08)

    b.build_mesh_object()
    out_path = os.path.join(out_dir, "church_buttress.glb")
    export_environment_glb(out_path)


# ==============================================================================
# 12. EXTERIOR CHURCH: church_bell_tower_spire.glb
# ==============================================================================

def build_church_bell_tower_spire(out_dir: str, palette: dict[str, bpy.types.Material] | None = None) -> None:
    """
    12. church_bell_tower_spire.glb (4.86m x 4.86m x 18.50m tall Gothic bell tower).
    Base tower stage, open belfry stage with lancet sound openings, hanging tarnished bronze
    church bell, corner stone pinnacles, octagonal needle spire, and occult iron cross finial.
    """
    if palette is None:
        palette = clear_scene()
    print("[Wave 1A] Building church_bell_tower_spire...")
    b = EnvironmentVoxelBuilder("church_bell_tower_spire", voxel_size=0.08, palette=palette)

    # 1. Base Tower Stage (Z in [0.0, 5.0], X, Y in [-2.25, 2.25])
    b.fill_world_box(-2.25, 2.25, -2.25, 2.25, 0.0, 5.0, "weathered_stone", shade_bias=0.96)
    # Corner quoins on base stage
    for sx in (-2.25, 2.05):
        for sy in (-2.25, 2.05):
            b.fill_world_box(sx, sx + 0.20, sy, sy + 0.20, 0.0, 5.0, "carved_stone_trim", shade_bias=1.02)
    # Moulded stringcourse cornice at Z = 5.0m
    b.fill_world_box(-2.35, 2.35, -2.35, 2.35, 4.85, 5.15, "carved_stone_trim", shade_bias=1.05)

    # 2. Belfry Stage (Z in [5.0, 10.5], X, Y in [-2.20, 2.20])
    b.fill_world_box(-2.20, 2.20, -2.20, 2.20, 5.0, 10.5, "weathered_stone", shade_bias=0.98)
    # Carve hollow interior chamber
    b.carve_world_box(-1.60, 1.60, -1.60, 1.60, 5.20, 10.30)

    # Carve lancet arch openings on all 4 sides (width 1.50m, Z in [6.0, 9.60])
    # North & South openings
    b.carve_world_box(-0.75, 0.75, -2.25, 2.25, 6.0, 8.80)
    b.carve_pointed_arch(0.0, 0.0, base_z=6.0, spring_z=8.80, peak_z=9.60, span_w=1.50, depth_y=4.50)
    # East & West openings
    b.carve_world_box(-2.25, 2.25, -0.75, 0.75, 6.0, 8.80)
    # Carve pointed arch along Y for East/West
    s = b.voxel_size
    n_arch = int(round(0.80 / s))
    for ia in range(n_arch):
        wz = 8.80 + ia * s
        hw = max(0.0, 0.75 * math.cos((ia / float(n_arch)) * (math.pi * 0.45)))
        b.carve_world_box(-2.25, 2.25, -hw, hw, wz, wz + s)

    # Tarnished Bronze Church Bell (Z in [7.5, 8.85])
    # Iron bell hanging beam
    b.fill_world_box(-1.65, 1.65, -0.14, 0.14, 8.70, 8.95, "wrought_iron", shade_bias=1.08)
    # Bell body
    b.fill_world_cylinder_z(0.0, 0.0, 7.60, 8.45, 0.55, mat_key="bronze", shade_bias=1.04)
    # Bell flared rim
    b.fill_world_cylinder_z(0.0, 0.0, 7.45, 7.65, 0.68, mat_key="bronze", shade_bias=1.08)

    # 3. Belfry Parapet & 4 Corner Pinnacles (Z in [10.5, 12.7])
    b.fill_world_box(-2.35, 2.35, -2.35, 2.35, 10.5, 11.15, "carved_stone_trim", shade_bias=1.04)
    b.carve_world_box(-1.95, 1.95, -1.95, 1.95, 10.65, 11.20)
    # 4 Corner stone pinnacles
    for px in (-2.05, 2.05):
        for py in (-2.05, 2.05):
            b.fill_world_box(px - 0.28, px + 0.28, py - 0.28, py + 0.28, 11.15, 12.00, "carved_stone_trim", shade_bias=1.05)
            # Tapered pyramid top
            for ip in range(8):
                tp = ip / 7.0
                hw = 0.28 * (1.0 - tp)
                b.fill_world_box(px - hw, px + hw, py - hw, py + hw, 12.00 + ip * s, 12.00 + (ip + 1) * s, "carved_stone_trim", shade_bias=1.08)

    # 4. Octagonal Needle Spire (Z in [10.5, 17.0])
    n_spire = int(round(6.50 / s))
    for isp in range(n_spire):
        tz = isp / float(n_spire)
        wz = 10.50 + isp * s
        rad = 2.15 * (1.0 - tz) + 0.15
        b.fill_world_cylinder_z(0.0, 0.0, wz, wz + s, rad, mat_key="dark_slate_roof", shade_bias=1.02, octagonal=True)

    # 5. Wrought-Iron Occult Cross Finial (Z in [17.0, 18.50])
    # Main upright shaft
    b.fill_world_box(-0.06, 0.06, -0.06, 0.06, 17.0, 18.50, "wrought_iron", shade_bias=1.12)
    # Horizontal crossbar
    b.fill_world_box(-0.35, 0.35, -0.05, 0.05, 17.95, 18.07, "wrought_iron", shade_bias=1.12)
    # Halo ring around cross intersection
    b.fill_world_cylinder_y(0.0, 18.01, -0.04, 0.04, 0.22, r_inner=0.16, mat_key="wrought_iron", shade_bias=1.15)

    b.build_mesh_object()
    out_path = os.path.join(out_dir, "church_bell_tower_spire.glb")
    export_environment_glb(out_path)


# ==============================================================================
# 13. HUB STATION: hub_weapon_workbench.glb
# ==============================================================================

def build_hub_weapon_workbench(out_dir: str, palette: dict[str, bpy.types.Material] | None = None) -> None:
    """
    13. hub_weapon_workbench.glb (2.88m wide x 1.16m deep x 2.22m tall Gunsmith Bench).
    Pegged charred oak workbench with wrought-iron corner brackets, mounted gunsmith vice
    clamping an octagonal rifle barrel, tool rack displaying silver blades and ritual carbine,
    brass cartridge blocks, munitions crate, powder keg, open ledger, and blue-flame burner.
    """
    if palette is None:
        palette = clear_scene()
    print("[Wave 1A] Building hub_weapon_workbench...")
    b = EnvironmentVoxelBuilder("hub_weapon_workbench", voxel_size=0.025, palette=palette)

    # 1. Flagstone floor footpads (Z in [0.0, 0.08])
    for fx in (-1.24, 0.0, 1.24):
        b.fill_world_box(fx - 0.14, fx + 0.14, -0.52, 0.52, 0.0, 0.08, "cobble_flagstone", shade_bias=0.94)

    # 2. 6 Heavy timber legs (Z in [0.08, 0.84])
    for lx in (-1.24, 0.0, 1.24):
        for ly in (-0.42, 0.42):
            b.fill_world_box(lx - 0.07, lx + 0.07, ly - 0.07, ly + 0.07, 0.08, 0.84, "charred_timber", shade_bias=0.92)
            # Iron shoe at bottom
            b.fill_world_box(lx - 0.08, lx + 0.08, ly - 0.08, ly + 0.08, 0.08, 0.16, "wrought_iron", shade_bias=1.06)
            # Top mortise bracket
            b.fill_world_box(lx - 0.085, lx + 0.085, ly - 0.085, ly + 0.085, 0.76, 0.84, "wrought_iron", shade_bias=1.08)

    # 3. Lower timber storage shelf & cross stretchers (Z in [0.26, 0.36])
    b.fill_world_box(-1.24, 1.24, -0.44, -0.38, 0.26, 0.34, "charred_timber", shade_bias=0.90)
    b.fill_world_box(-1.24, 1.24, 0.38, 0.44, 0.26, 0.34, "charred_timber", shade_bias=0.90)
    b.fill_world_box(-1.20, 1.20, -0.38, 0.38, 0.32, 0.36, "charred_timber", shade_bias=0.94)

    # Under-bench ammunition crate
    b.fill_world_box(-0.95, -0.35, -0.30, 0.20, 0.36, 0.70, "charred_timber", shade_bias=0.88)
    b.fill_world_box(-0.96, -0.34, -0.31, 0.21, 0.45, 0.48, "wrought_iron", shade_bias=1.05)
    b.fill_world_box(-0.96, -0.34, -0.31, 0.21, 0.60, 0.63, "wrought_iron", shade_bias=1.05)

    # Under-bench powder keg
    b.fill_world_cylinder_z(0.60, -0.05, 0.36, 0.72, 0.20, mat_key="charred_timber", shade_bias=0.86)
    b.fill_world_cylinder_z(0.60, -0.05, 0.44, 0.47, 0.205, r_inner=0.19, mat_key="bronze", shade_bias=1.05)
    b.fill_world_cylinder_z(0.60, -0.05, 0.62, 0.65, 0.205, r_inner=0.19, mat_key="bronze", shade_bias=1.05)

    # 4. Heavy 2.80m x 1.08m butcher-block oak tabletop (Z in [0.84, 0.96])
    b.fill_world_box(-1.40, 1.40, -0.54, 0.54, 0.84, 0.96, "charred_timber", shade_bias=0.96)
    # Recessed parts tray carved in tabletop
    b.carve_world_box(-0.45, 0.15, -0.44, -0.20, 0.92, 0.98)
    b.fill_world_box(-0.45, 0.15, -0.44, -0.20, 0.90, 0.92, "wrought_iron", shade_bias=1.04)

    # 4 Wrought-iron corner bumper brackets
    for cx in (-1.38, 1.38):
        for cy in (-0.52, 0.52):
            b.fill_world_box(cx - 0.05, cx + 0.05, cy - 0.05, cy + 0.05, 0.83, 0.97, "wrought_iron", shade_bias=1.10)

    # 5. Mounted Gunsmith Vice on front-left (-0.88, -0.34, 0.96)
    b.fill_world_box(-1.02, -0.74, -0.44, -0.24, 0.96, 1.02, "wrought_iron", shade_bias=1.08)
    b.fill_world_box(-0.94, -0.82, -0.42, -0.26, 1.02, 1.18, "wrought_iron", shade_bias=1.12)
    # Clamped octagonal rifle barrel extending across vice
    b.fill_world_box(-1.25, -0.45, -0.36, -0.32, 1.08, 1.12, "wrought_iron", shade_bias=1.15)

    # 6. Tool Pegboard / Backrack (at Y in [0.44, 0.52], Z in [0.96, 2.20])
    b.fill_world_box(-1.30, 1.30, 0.44, 0.52, 0.96, 2.20, "charred_timber", shade_bias=0.90)
    b.fill_world_box(-1.32, 1.32, 0.43, 0.53, 2.16, 2.22, "carved_stone_trim", shade_bias=1.02)

    # Mounted ritual carbine silhouette on backboard
    b.fill_world_box(-0.70, 0.70, 0.41, 0.44, 1.70, 1.82, "bronze", shade_bias=1.10)
    b.fill_world_box(-0.55, -0.15, 0.41, 0.44, 1.62, 1.70, "charred_timber", shade_bias=0.88)
    b.fill_world_box(0.20, 0.65, 0.41, 0.44, 1.74, 1.78, "wrought_iron", shade_bias=1.12)

    # Displayed silver daggers
    for dx_i in (-0.95, -0.75, 0.85, 1.05):
        b.fill_world_box(dx_i - 0.03, dx_i + 0.03, 0.41, 0.44, 1.25, 1.55, "silver", shade_bias=1.20)
        b.fill_world_box(dx_i - 0.06, dx_i + 0.06, 0.41, 0.44, 1.48, 1.51, "bronze", shade_bias=1.10)

    # Brass cartridge block rows on tabletop
    for bx in (-0.15, 0.05, 0.25):
        b.fill_world_box(bx, bx + 0.12, 0.10, 0.28, 0.96, 1.02, "bronze", shade_bias=1.10)
        for cz in (1.02, 1.05):
            b.fill_world_box(bx + 0.02, bx + 0.10, 0.14, 0.24, cz, cz + 0.03, "bronze", shade_bias=1.15)

    # 7. Blue-Flame Alchemical Burner & Open Ledger on right side
    # Brass crucible burner base at (0.92, -0.22, 0.96)
    b.fill_world_cylinder_z(0.92, -0.22, 0.96, 1.08, 0.12, mat_key="bronze", shade_bias=1.10, octagonal=True)
    # Glowing blue soul flame core
    b.fill_world_cylinder_z(0.92, -0.22, 1.08, 1.22, 0.07, mat_key="blue_soul", shade_bias=1.35)
    b.fill_world_cylinder_z(0.92, -0.22, 1.10, 1.18, 0.04, mat_key="occult_rune", shade_bias=1.40)

    # Open gunsmith ledger with parchment pages
    b.fill_world_box(0.40, 0.72, -0.40, -0.10, 0.96, 0.99, "charred_timber", shade_bias=0.85)
    b.fill_world_box(0.42, 0.70, -0.38, -0.12, 0.99, 1.015, "wax", shade_bias=1.05)

    b.build_mesh_object()
    out_path = os.path.join(out_dir, "hub_weapon_workbench.glb")
    export_environment_glb(out_path)


# ==============================================================================
# 14. HUB STATION: hub_armor_reliquary_stand.glb
# ==============================================================================

def build_hub_armor_reliquary_stand(out_dir: str, palette: dict[str, bpy.types.Material] | None = None) -> None:
    """
    14. hub_armor_reliquary_stand.glb (2.20m wide x 1.02m deep x 2.42m tall Inquisitor's Armor Rack).
    Stepped flagstone and timber dais with consecrated gold rune inlay, iron mannequin frame
    supporting fluted silver and bronze cuirass, pauldrons, great-helm with cross visor,
    halo finial, flanked by an iron-bound munitions chest and shield reliquary.
    """
    if palette is None:
        palette = clear_scene()
    print("[Wave 1A] Building hub_armor_reliquary_stand...")
    b = EnvironmentVoxelBuilder("hub_armor_reliquary_stand", voxel_size=0.025, palette=palette)

    # 1. Stepped flagstone and timber dais (Z in [0.0, 0.28])
    b.fill_world_box(-1.10, 1.10, -0.51, 0.51, 0.0, 0.16, "cobble_flagstone", shade_bias=0.96)
    # Consecrated gold rune inlay groove around perimeter
    b.fill_world_box(-1.02, 1.02, -0.45, -0.41, 0.14, 0.165, "gold", shade_bias=1.20)
    b.fill_world_box(-1.02, 1.02, 0.41, 0.45, 0.14, 0.165, "gold", shade_bias=1.20)
    b.fill_world_box(-1.02, -0.98, -0.45, 0.45, 0.14, 0.165, "gold", shade_bias=1.20)
    b.fill_world_box(0.98, 1.02, -0.45, 0.45, 0.14, 0.165, "gold", shade_bias=1.20)

    # Upper timber deck (Z in [0.16, 0.28])
    b.fill_world_box(-0.92, 0.92, -0.36, 0.36, 0.16, 0.28, "charred_timber", shade_bias=0.90)

    # 2. Central Mannequin Iron Stand Post & Crossbeam (Z in [0.28, 2.22])
    b.fill_world_box(-0.21, 0.21, -0.16, 0.26, 0.28, 0.38, "wrought_iron", shade_bias=1.06)
    b.fill_world_cylinder_z(0.0, 0.05, 0.36, 2.15, 0.055, mat_key="wrought_iron", shade_bias=1.08)
    # Shoulder crossbeam at Z = 1.76m
    b.fill_world_box(-0.48, 0.48, 0.0, 0.10, 1.72, 1.80, "wrought_iron", shade_bias=1.10)

    # Gothic Iron Halo Finial (Z in [2.15, 2.422])
    b.fill_world_cylinder_y(0.0, 2.24, 0.03, 0.07, 0.18, r_inner=0.14, mat_key="bronze", shade_bias=1.15)
    b.fill_world_box(-0.02, 0.02, 0.03, 0.07, 2.38, 2.422, "wrought_iron", shade_bias=1.18)

    # 3. Fluted Silver & Bronze Cuirass (Z in [1.25, 1.76])
    # Main breastplate
    b.fill_world_box(-0.26, 0.26, -0.14, 0.20, 1.35, 1.75, "silver", shade_bias=1.18)
    # Lower plackart
    b.fill_world_box(-0.23, 0.23, -0.15, 0.18, 1.22, 1.40, "wrought_iron", shade_bias=1.05)
    # Center ornamental bronze ridge
    b.fill_world_box(-0.03, 0.03, -0.16, -0.13, 1.25, 1.75, "bronze", shade_bias=1.20)
    # Gorget neck collar
    b.fill_world_box(-0.17, 0.17, -0.10, 0.18, 1.75, 1.88, "silver", shade_bias=1.15)

    # Articulated pauldrons on shoulders
    for sx in (-0.42, 0.42):
        b.fill_world_box(sx - 0.12, sx + 0.12, -0.10, 0.18, 1.62, 1.84, "silver", shade_bias=1.16)
        b.fill_world_box(sx - 0.14, sx + 0.14, -0.11, 0.19, 1.72, 1.76, "bronze", shade_bias=1.18)

    # Hanging tassets / fauld lames (Z in [1.02, 1.24])
    for tx in (-0.16, 0.16):
        b.fill_world_box(tx - 0.09, tx + 0.09, -0.13, -0.07, 1.05, 1.24, "wrought_iron", shade_bias=1.04)

    # 4. Inquisitor Great-Helm (Z in [1.88, 2.18])
    b.fill_world_cylinder_z(0.0, 0.04, 1.88, 2.18, 0.14, mat_key="silver", shade_bias=1.18, octagonal=True)
    # Bronze face cross visor
    b.fill_world_box(-0.02, 0.02, -0.12, -0.08, 1.94, 2.14, "bronze", shade_bias=1.22)
    b.fill_world_box(-0.10, 0.10, -0.12, -0.08, 2.02, 2.06, "bronze", shade_bias=1.22)

    # 5. Flanking Munitions Chest (Left, X in [-0.95, -0.48])
    b.fill_world_box(-0.90, -0.48, -0.22, 0.22, 0.28, 0.65, "charred_timber", shade_bias=0.88)
    b.fill_world_box(-0.91, -0.47, -0.23, 0.23, 0.38, 0.42, "wrought_iron", shade_bias=1.06)
    b.fill_world_box(-0.91, -0.47, -0.23, 0.23, 0.55, 0.58, "wrought_iron", shade_bias=1.06)

    # 6. Flanking Shield Reliquary (Right, X in [0.48, 0.90])
    b.fill_world_box(0.52, 0.86, -0.10, 0.12, 0.28, 1.15, "silver", shade_bias=1.12)
    b.fill_world_box(0.50, 0.88, -0.11, 0.13, 0.65, 0.72, "bronze", shade_bias=1.20)
    b.fill_world_box(0.66, 0.72, -0.11, 0.13, 0.40, 1.05, "bronze", shade_bias=1.20)

    b.build_mesh_object()
    out_path = os.path.join(out_dir, "hub_armor_reliquary_stand.glb")
    export_environment_glb(out_path)


# ==============================================================================
# 15. HUB STATION: hub_sanctuary_upgrade_font.glb
# ==============================================================================

def build_hub_sanctuary_upgrade_font(out_dir: str, palette: dict[str, bpy.types.Material] | None = None) -> None:
    """
    15. hub_sanctuary_upgrade_font.glb (1.60m diameter x 1.88m tall Consecrated Font & Crucible).
    Stepped octagonal carved limestone pedestal, fluted bronze ritual basin filled with
    glowing consecrated gold oil, surrounded by 4 upright iron stanchions with hanging censers.
    """
    if palette is None:
        palette = clear_scene()
    print("[Wave 1A] Building hub_sanctuary_upgrade_font...")
    b = EnvironmentVoxelBuilder("hub_sanctuary_upgrade_font", voxel_size=0.025, palette=palette)

    # 1. Stepped Octagonal Limestone Pedestal Plinth (Z in [0.0, 0.32])
    # Step 1: radius 0.80m, Z in [0.0, 0.16]
    b.fill_world_cylinder_z(0.0, 0.0, 0.0, 0.16, 0.80, mat_key="cobble_flagstone", shade_bias=0.96, octagonal=True)
    # Step 2: radius 0.64m, Z in [0.16, 0.32]
    b.fill_world_cylinder_z(0.0, 0.0, 0.16, 0.32, 0.64, mat_key="weathered_stone", shade_bias=1.00, octagonal=True)

    # 2. Central Octagonal Limestone & Bronze Shaft (Z in [0.32, 1.00])
    b.fill_world_cylinder_z(0.0, 0.0, 0.32, 1.00, 0.34, mat_key="weathered_stone", shade_bias=0.98, octagonal=True)
    # 8 Radiating flying buttress ribs around the shaft
    for ir in range(8):
        ang = ir * (math.pi / 4.0)
        rx = math.cos(ang) * 0.40
        ry = math.sin(ang) * 0.40
        b.fill_world_box(rx - 0.05, rx + 0.05, ry - 0.05, ry + 0.05, 0.36, 0.96, "carved_stone_trim", shade_bias=1.04)

    # 3. Fluted Bronze & Carved Stone Ritual Basin (Z in [0.98, 1.38])
    # Main outer bronze bowl
    b.fill_world_cylinder_z(0.0, 0.0, 0.98, 1.36, 0.68, mat_key="bronze", shade_bias=1.08, octagonal=True)
    # Carved stone rim border
    b.fill_world_cylinder_z(0.0, 0.0, 1.34, 1.38, 0.70, r_inner=0.64, mat_key="carved_stone_trim", shade_bias=1.06, octagonal=True)

    # Recessed hollow carved inside basin (radius 0.54m, Z in [1.12, 1.39])
    b.carve_world_cylinder_z(0.0, 0.0, 1.12, 1.39, 0.54)

    # Consecrated liquid gold / amber oil pool (Z in [1.12, 1.28])
    b.fill_world_cylinder_z(0.0, 0.0, 1.12, 1.28, 0.52, mat_key="gold", shade_bias=1.35)

    # 4. 4 Upright Wrought-Iron Stanchions with Hanging Censers (Z in [0.16, 1.878])
    # Positioned at diagonals (±0.56, ±0.56)
    for px in (-0.56, 0.56):
        for py in (-0.56, 0.56):
            # Iron post rising to Z = 1.878m
            b.fill_world_box(px - 0.03, px + 0.03, py - 0.03, py + 0.03, 0.16, 1.84, "wrought_iron", shade_bias=1.10)
            # Curved hook top
            b.fill_world_box(px - 0.04, px + 0.04, py - 0.04, py + 0.04, 1.82, 1.878, "wrought_iron", shade_bias=1.14)
            # Hanging bronze censer vessel at Z in [1.38, 1.54]
            b.fill_world_cylinder_z(px, py, 1.38, 1.54, 0.08, mat_key="bronze", shade_bias=1.12, octagonal=True)
            # Glowing ember core inside censer
            b.fill_world_cylinder_z(px, py, 1.48, 1.56, 0.045, mat_key="candle_flame", shade_bias=1.35)

    b.build_mesh_object()
    out_path = os.path.join(out_dir, "hub_sanctuary_upgrade_font.glb")
    export_environment_glb(out_path)


# ==============================================================================
# 16. HUB STATION / ARCHITECTURE: occult_rift_portal.glb
# ==============================================================================

def build_occult_rift_portal(out_dir: str, palette: dict[str, bpy.types.Material] | None = None) -> None:
    """
    16. occult_rift_portal.glb (3.60m wide x 1.24m deep x 4.30m tall blood-stone portal).
    CRITICAL NODE HIERARCHY REQUIREMENT:
      Root Object: 'OccultRiftArchway'
      Child Object: 'PortalVortexMesh' (parented to OccultRiftArchway with 0..1 UVs).
    Stepped plinth, twin twisted rune-carved obelisk pillars, pointed arch voussoirs,
    hanging wrought-iron chains, and separate child plane PortalVortexMesh for occult_portal.gd.
    """
    if palette is None:
        palette = clear_scene()
    print("[Wave 1A] Building occult_rift_portal...")

    # Build Root Archway via EnvironmentVoxelBuilder
    b = EnvironmentVoxelBuilder("OccultRiftArchway", voxel_size=0.04, palette=palette)

    # 1. Stepped Plinth Base (Z in [0.0, 0.28], width 3.60m, depth 1.24m)
    b.fill_world_box(-1.80, 1.80, -0.62, 0.62, 0.0, 0.14, "cobble_flagstone", shade_bias=0.94)
    b.fill_world_box(-1.66, 1.66, -0.52, 0.52, 0.14, 0.28, "carved_stone_trim", shade_bias=1.02)

    # 2. Twin Twisted Rune-Carved Obelisk Pillars at X = ±1.32m (Z in [0.28, 2.92])
    for side_s in (-1.0, 1.0):
        px = side_s * 1.32
        # Pedestal base
        b.fill_world_box(px - 0.33, px + 0.33, -0.33, 0.33, 0.28, 0.50, "carved_stone_trim", shade_bias=1.04)

        # Twisting obelisk drums
        n_drums = 12
        for idr in range(n_drums):
            z0 = 0.50 + idr * 0.20
            z1 = z0 + 0.20
            twist = side_s * idr * 0.10
            taper = 0.26 - idr * 0.005
            # Drum core
            b.fill_world_box(px - taper, px + taper, -taper, taper, z0, z1, "weathered_stone", shade_bias=0.96)
            # Glowing occult rune strips on front and rear faces
            b.fill_world_box(px - 0.04, px + 0.04, -taper - 0.015, -taper + 0.015, z0 + 0.04, z1 - 0.04, "occult_rune", shade_bias=1.35)
            b.fill_world_box(px - 0.04, px + 0.04, taper - 0.015, taper + 0.015, z0 + 0.04, z1 - 0.04, "occult_rune", shade_bias=1.35)
            # Iron binding collar on alternating drums
            if idr % 2 == 1:
                b.fill_world_box(px - taper - 0.03, px + taper + 0.03, -taper - 0.03, taper + 0.03, z0 + 0.08, z0 + 0.13, "wrought_iron", shade_bias=1.12)

        # Capital & side pier pinnacle (Z in [2.90, 3.68])
        b.fill_world_box(px - 0.34, px + 0.34, -0.34, 0.34, 2.90, 3.12, "carved_stone_trim", shade_bias=1.06)
        b.fill_world_box(px - 0.18, px + 0.18, -0.18, 0.18, 3.12, 3.68, "carved_stone_trim", shade_bias=1.08)

    # 3. Pointed Gothic Archway Voussoirs (springing from Z = 2.88m up to 4.25m)
    # Pointed arch voussoir ring
    b.fill_pointed_arch(0.0, 0.0, base_z=2.00, spring_z=2.88, peak_z=3.95, span_w=2.40, depth_y=0.56, wall_thick=0.28, mat_key="carved_stone_trim", shade_bias=1.06)

    # Central Pointed Keystone & Occult Crown at Z = 3.90m..4.25m
    b.fill_world_box(-0.18, 0.18, -0.32, 0.32, 3.90, 4.18, "carved_stone_trim", shade_bias=1.10)
    b.fill_world_box(-0.06, 0.06, -0.33, 0.33, 3.94, 4.14, "occult_rune", shade_bias=1.40)
    b.fill_world_box(-0.08, 0.08, -0.08, 0.08, 4.18, 4.30, "wrought_iron", shade_bias=1.15)

    # 4. Hanging Wrought-Iron Chains Draped from Upper Arch Shoulders
    for side_s in (-1.0, 1.0):
        for ch_i in range(12):
            cz = 3.25 - ch_i * 0.085
            cx = side_s * (1.02 + math.sin(ch_i * 0.35) * 0.04)
            b.fill_world_box(cx - 0.025, cx + 0.025, -0.025, 0.025, cz - 0.04, cz + 0.04, "wrought_iron", shade_bias=1.12)

    # Build the Root Archway Object
    arch_obj = b.build_mesh_object()
    arch_obj.name = "OccultRiftArchway"

    # 5. Build Separate Central Child Plane `PortalVortexMesh` (2.20m wide x 3.20m tall)
    bm_v = bmesh.new()
    v_w, v_h = 2.20, 3.20
    z_bot = 0.28
    uv_layer = bm_v.loops.layers.uv.new("UVMap")

    grid_nx, grid_nz = 12, 16
    v_grid: list[list[bmesh.types.BMVert]] = []
    for iz in range(grid_nz + 1):
        row_v: list[bmesh.types.BMVert] = []
        tz = iz / float(grid_nz)
        vz = z_bot + tz * v_h
        arch_narrow = 1.0 if tz < 0.72 else max(0.20, 1.0 - ((tz - 0.72) / 0.28) ** 1.4)
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

    # Assign PortalVortexSurface material
    mat_vortex = make_environment_pbr_material(
        "PortalVortexSurface",
        (0.95, 0.55, 0.22),
        roughness=0.15,
        emission_rgb=(1.0, 0.60, 0.24),
        emission_strength=2.8,
    )
    vortex_obj.data.materials.append(mat_vortex)

    # Parent PortalVortexMesh to OccultRiftArchway (CRITICAL CONTRACT for occult_portal.gd)
    vortex_obj.parent = arch_obj

    # Select both for export
    bpy.ops.object.select_all(action='DESELECT')
    arch_obj.select_set(True)
    vortex_obj.select_set(True)
    bpy.context.view_layer.objects.active = arch_obj

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "occult_rift_portal.glb")
    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format='GLB',
        use_selection=True,
        export_yup=True,
        export_apply=False,
        export_attributes=True,
    )
    print(f"[MicroVoxelEnvironment] Exported occult_rift_portal with child PortalVortexMesh -> {out_path}")


# ==============================================================================
# MAIN ENTRYPOINT & CLI DISPATCH
# ==============================================================================

MODELS_MAP = {
    # 7 Modular Architecture Pieces (church_kit)
    "floor_stone_4x4": (build_floor_stone_4x4, "church_kit"),
    "wall_stone_solid": (build_wall_stone_solid, "church_kit"),
    "wall_stone_window": (build_wall_stone_window, "church_kit"),
    "wall_stone_arch_door": (build_wall_stone_arch_door, "church_kit"),
    "roof_gothic_vault_4x4": (build_roof_gothic_vault_4x4, "church_kit"),
    "stairs_stone_4x4": (build_stairs_stone_4x4, "church_kit"),
    "wall_lantern_sconce": (build_wall_lantern_sconce, "church_kit"),
    # 5 Exterior Church Components (church_kit)
    "church_foundation_plinth": (build_church_foundation_plinth, "church_kit"),
    "church_front_gable_rose": (build_church_front_gable_rose, "church_kit"),
    "church_pitched_roof_12x16": (build_church_pitched_roof_12x16, "church_kit"),
    "church_bell_tower_spire": (build_church_bell_tower_spire, "church_kit"),
    "church_buttress": (build_church_buttress, "church_kit"),
    # 4 Hub Stations (church_kit and architecture)
    "hub_weapon_workbench": (build_hub_weapon_workbench, "church_kit"),
    "hub_armor_reliquary_stand": (build_hub_armor_reliquary_stand, "church_kit"),
    "hub_sanctuary_upgrade_font": (build_hub_sanctuary_upgrade_font, "church_kit"),
    "occult_rift_portal": (build_occult_rift_portal, "architecture"),
}


def main() -> None:
    # Resolve project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    church_kit_dir = os.path.join(project_root, "assets", "models", "church_kit")
    arch_dir = os.path.join(project_root, "assets", "models", "architecture")
    os.makedirs(church_kit_dir, exist_ok=True)
    os.makedirs(arch_dir, exist_ok=True)

    # Parse arguments
    target_model = None
    for arg in sys.argv:
        if arg.startswith("--model="):
            target_model = arg.split("=", 1)[1].strip()

    if target_model and target_model in MODELS_MAP:
        func, folder = MODELS_MAP[target_model]
        out_dir = arch_dir if folder == "architecture" else church_kit_dir
        print(f"=== Building Single Model: {target_model} ===")
        func(out_dir)
    else:
        print(f"=== Building All 16 Wave 1A Models ===")
        for name, (func, folder) in MODELS_MAP.items():
            out_dir = arch_dir if folder == "architecture" else church_kit_dir
            print(f"--- [{name}] ---")
            func(out_dir)
        print("=== Wave 1A Complete: All 16 Models Generated Successfully ===")


if __name__ == "__main__":
    main()
