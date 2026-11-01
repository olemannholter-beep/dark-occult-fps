import bpy
import math
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from blender_micro_voxel_kit import (
    MicroVoxelBuilder,
    make_micro_voxel_materials,
)
from blender_set0_candle_bearer import (
    export_all_set0_starter,
)

OUTPUT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "assets", "models", "armor"))
VOXEL_SIZE = 0.018

HEAD_CLEARANCE = lambda wx, wy, wz: (-0.06 <= wz <= 0.20) and ((wx / 0.092) ** 2 + (wy / 0.098) ** 2 < 1.0)
CHEST_CLEARANCE = lambda wx, wy, wz: (-0.12 <= wz <= 0.50) and ((wx / 0.168) ** 2 + (wy / 0.114) ** 2 < 1.0)
LEGS_CLEARANCE = lambda wx, wy, wz: (wz >= -0.04) and (((wx * 1.15 + 0.125) / 0.145) ** 2 + ((wy * 1.15) / 0.100) ** 2 < 1.0)
FEET_CLEARANCE = lambda wx, wy, wz: (wz >= -0.09) and ((wx / 0.048) ** 2 + (wy / 0.048) ** 2 < 1.0)


def clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def fill_elliptical_ring(
    v: MicroVoxelBuilder,
    iy: int,
    rx_in: float,
    rz_in: float,
    rx_out: float,
    rz_out: float,
    mat_idx: int,
    shade_bias: float = 1.0,
    tint_b: float = 0.5,
    cx: float = 0.0,
    cz: float = 0.0,
    iz_min: int = -99,
    iz_max: int = 99,
) -> None:
    max_x = int(math.ceil(abs(cx) + rx_out + 1))
    max_z = int(math.ceil(abs(cz) + rz_out + 1))
    for ix in range(-max_x, max_x + 1):
        for iz in range(max(-max_z, iz_min), min(max_z, iz_max) + 1):
            dx = (ix + 0.5) - cx
            dz = (iz + 0.5) - cz
            d_out = (dx / max(0.1, rx_out)) ** 2 + (dz / max(0.1, rz_out)) ** 2
            if d_out <= 1.0:
                if rx_in <= 0.0 or rz_in <= 0.0:
                    v.set_voxel(ix, iy, iz, mat_idx, shade_bias, tint_b)
                else:
                    d_in = (dx / rx_in) ** 2 + (dz / rz_in) ** 2
                    if d_in >= 1.0:
                        v.set_voxel(ix, iy, iz, mat_idx, shade_bias, tint_b)


def build_set0_head(v: MicroVoxelBuilder) -> None:
    """
    Set 0 — Grave-Stalker's Boiled Leather / Voxel Inquisitor Head:
    Swept wide-brimmed micro-voxel Inquisitor slouch/tricorn hat (iy=7..17, wide stepped brim
    ix=-12..12, iz=-11..12 with upturned side folds and jagged tattered brim notches),
    brass hat-band buckle (iz=+8), deep hooded cowl (mat_idx=1), riveted iron plague-beak mask
    protruding forward (iz=6..12), and recessed glowing ember ocular voxels (mat_idx=3) with dark tear-grooves.
    """
    # 1. Deep hooded leather cowl & high collar (iy = -3..8) outside head clearance
    for iy in range(-3, 9):
        t = (iy + 3) / 11.0
        rx_in = 5.5 - t * 0.2
        rz_in = 5.9 - t * 0.2
        rx_out = rx_in + (2.4 if iy <= 0 else 2.0)
        rz_out = rz_in + (2.4 if iy <= 0 else 2.0)
        mat = 2 if iy == -3 else 1
        fill_elliptical_ring(v, iy, rx_in, rz_in, rx_out, rz_out, mat, 0.96, 0.45)

    # Buckled leather collar strap around neck (iy = -1)
    fill_elliptical_ring(v, -1, 6.2, 6.6, 8.0, 8.4, 1, 0.92, 0.38)
    v.add_3d_buckle(0, -1, 8, half_w=2, half_h=1, frame_mat=2, pin_mat=0)

    # 2. Riveted iron face-plate & protruding plague-beak mask (iy = 0..6, iz = 6..12)
    for iy in range(0, 7):
        fill_elliptical_ring(v, iy, 5.6, 6.0, 7.6, 8.2, 0, 1.02, 0.55, iz_min=2, iz_max=10)

    # Stepped tapering plague beak protruding forward (+iz = 6..12)
    for iz in range(6, 13):
        prog = (iz - 6) / 6.0
        hw = max(1, int(round(3.8 * (1.0 - prog * 0.72))))
        y_bot = int(round(0.0 - prog * 1.5))
        y_top = int(round(4.2 - prog * 2.5))
        for ix in range(-hw, hw + 1):
            for iy in range(y_bot, y_top + 1):
                if abs(ix) >= hw - 1 or iy in (y_bot, y_top) or iz >= 11:
                    # Brass central nasal spine & rivets along beak ridge
                    is_spine = (ix == 0 and iy == y_top)
                    is_rivet = (abs(ix) == hw and (iz % 2 == 0) and iy == (y_bot + y_top) // 2)
                    mat = 2 if (is_spine or is_rivet) else 0
                    v.set_voxel(ix, iy, iz, mat, 1.04 if mat == 2 else 0.98, 0.60)

    # 3. Recessed glowing ember ocular lenses (mat_idx=3) with brass rims & dark vertical tear-grooves
    for sx in (-1, 1):
        ox = sx * 3
        # Brass goggle housing around eye
        for dx in range(-1, 2):
            for dy in range(4, 7):
                if abs(dx) == 1 or dy in (4, 6):
                    v.set_voxel(ox + dx, dy, 8, 2, 1.04, 0.68)
        # Glowing ember core
        v.set_voxel(ox, 5, 7, 3, 1.08, 0.95)
        v.set_voxel(ox, 5, 8, 3, 1.10, 0.98)
        # Dark vertical tear-groove below eye
        for ty in (1, 2, 3):
            v.set_voxel(ox, ty, 8, 0, 0.72, 0.25)

    # 4. Swept wide-brimmed Inquisitor slouch/tricorn hat (iy = 7..17)
    # Wide stepped brim (ix = -12..12, iz = -11..12) with upturned side folds
    for ix in range(-12, 13):
        for iz in range(-11, 13):
            r = math.sqrt((ix / 12.0) ** 2 + (iz / 11.5) ** 2)
            if 0.42 <= r <= 1.05:
                # Upturned side tricorn folds & swept front peak
                fold_up = 0
                if abs(ix) >= 8:
                    fold_up = min(3, int((abs(ix) - 7) * 0.85))
                elif iz >= 8:
                    fold_up = min(2, int((iz - 7) * 0.6))
                by = 7 + fold_up
                # Tattered brim notches on back/sides
                if r > 0.88 and ((ix * 5 + iz * 7) % 11 == 0):
                    continue
                is_rim = r >= 0.90
                v.set_voxel(ix, by, iz, 2 if (is_rim and (ix + iz) % 3 == 0) else 1, 0.96, 0.48)
                if is_rim and fold_up > 0:
                    v.set_voxel(ix, by + 1, iz, 1, 0.92, 0.42)

    # Hat band (iy = 8..9) + 3D brass buckle at front (iz = +8)
    fill_elliptical_ring(v, 8, 4.8, 5.2, 7.2, 7.6, 2, 1.04, 0.66)
    fill_elliptical_ring(v, 9, 4.8, 5.2, 7.2, 7.6, 1, 0.94, 0.40)
    v.add_3d_buckle(0, 9, 8, half_w=2, half_h=2, frame_mat=2, pin_mat=0)

    # Tall tapered slouch crown (iy = 10..17) with forward/side inquisitor crease
    for iy in range(10, 18):
        t = (iy - 10) / 7.0
        rx_out = 6.8 * (1.0 - t * 0.42)
        rz_out = 7.2 * (1.0 - t * 0.38)
        rx_in = max(0.0, rx_out - 2.2) if iy < 16 else 0.0
        rz_in = max(0.0, rz_out - 2.2) if iy < 16 else 0.0
        shift_z = int(round(t * 1.5))
        fill_elliptical_ring(v, iy, rx_in, rz_in, rx_out, rz_out, 1, 0.98, 0.46, cz=shift_z)
        if iy in (13, 16):
            fill_elliptical_ring(v, iy, rx_out - 0.9, rz_out - 0.9, rx_out + 0.3, rz_out + 0.3, 2, 1.02, 0.62, cz=shift_z)

    v.enforce_inner_clearance(HEAD_CLEARANCE)


def build_set0_chest(v: MicroVoxelBuilder) -> None:
    """
    Set 0 — Grave-Stalker's Boiled Leather / Voxel Inquisitor Chest:
    Multi-layer stepped dark leather coat (mat_idx=1) over buttoned inner waistcoat,
    jagged stepped shoulder mantle (ix=-16..16, iy=18..26) with physical perforated voxel holes,
    shoulder-mounted melted wax candles (add_shoulder_candle on left & right shoulders),
    3D forged iron neck chain (add_3d_chain) + tarnished brass bell amulet (mat_idx=2),
    diagonal cross-body bandolier with 8 brass-tipped cartridges + chained grimoire tome on the hip,
    heavy waist belt with 3D hollow iron buckle, and flared split coat-tails (iy=-10..0) with tattered holes.
    """
    # 1. Multi-layer stepped dark leather coat over buttoned inner waistcoat (iy = 0..24)
    for iy in range(0, 25):
        t = iy / 24.0
        rx_in = 9.6 + math.sin(t * math.pi) * 1.1
        rz_in = 6.6 + math.sin(t * math.pi) * 0.8
        rx_out = rx_in + 2.3
        rz_out = rz_in + 2.3
        fill_elliptical_ring(v, iy, rx_in, rz_in, rx_out, rz_out, 1, 0.96, 0.44)
        # Buttoned inner waistcoat & lapel trim at front center (+iz)
        if iy >= 3 and (iy % 3 == 0):
            v.set_voxel(-1, iy, int(round(rz_out)), 2, 1.04, 0.65)
            v.set_voxel(1, iy, int(round(rz_out)), 2, 1.04, 0.65)
        for lx in (-3, 3):
            v.set_voxel(lx, iy, int(round(rz_out)), 0 if iy % 2 == 0 else 2, 1.00, 0.55)

    # 2. Flared split coat-tails (iy = -10..0) with perforated tattered holes
    for iy in range(-10, 1):
        flare = (0 - iy) * 0.25
        rx_in = 9.6 + flare
        rz_in = 6.6 + flare * 0.7
        rx_out = rx_in + 2.2
        rz_out = rz_in + 2.2
        fill_elliptical_ring(v, iy, rx_in, rz_in, rx_out, rz_out, 1, 0.92, 0.40)
        # Split front & back openings + tattered 1x1/2x2 perforations
        v.carve_box(-2, 2, iy, iy, -14, 14)
        for ix in range(-14, 15):
            for iz in range(-12, 13):
                if iy <= -5 and ((ix * 7 + iy * 13 + iz * 5) % 11 == 0):
                    v.carve_voxel(ix, iy, iz)

    # 3. Heavy waist belt (iy = 0..2) with 3D hollow iron/brass buckle & hip grimoire tome
    for iy in (0, 1, 2):
        mat = 2 if iy == 1 else 0
        fill_elliptical_ring(v, iy, 9.8, 6.7, 12.4, 9.2, mat, 1.02, 0.58)
    v.add_3d_buckle(0, 1, 10, half_w=3, half_h=2, frame_mat=2, pin_mat=0)

    # Chained Grimoire Tome on right hip (ix = 11..14, iy = -6..0, iz = -2..4)
    v.fill_box(11, 13, -6, -1, -2, 3, 1, 0.94, 0.36)
    v.fill_box(12, 14, -5, -2, -1, 2, 2, 1.04, 0.72)  # Brass cover clasps & pages
    v.set_voxel(14, -3, 0, 3, 1.08, 0.92)  # Glowing occult sigil on cover
    v.add_3d_chain((11, 1, 2), (13, -2, 1), mat_idx=0, sag_voxels=1.5)

    # 4. Jagged stepped shoulder mantle (ix = -16..16, iy = 18..26) with perforated voxel holes
    for iy in range(18, 27):
        mt = (iy - 18) / 8.0
        span_x = int(round(16 - mt * 4.0))
        rx_in = 9.7
        rz_in = 6.7
        rx_out = float(span_x)
        rz_out = 9.6 - mt * 1.4
        fill_elliptical_ring(v, iy, rx_in, rz_in, rx_out, rz_out, 1, 0.98, 0.48)
        # Brass trimmed upper collar rim & jagged perforated holes
        for ix in range(-span_x, span_x + 1):
            for iz in range(-10, 11):
                if iy in (18, 19) and ((ix * 3 + iz * 5 + iy) % 9 == 0):
                    v.carve_voxel(ix, iy, iz)
                elif iy == 25 and abs(ix) <= 12 and (ix + iz) % 2 == 0:
                    if (ix, iy, iz) in v.voxels:
                        v.set_voxel(ix, iy, iz, 2, 1.04, 0.66)

    # 5. Shoulder-mounted melted wax candles on left & right shoulders
    v.add_shoulder_candle(-13, 25, 0, height=5, wax_mat=1, flame_mat=3)
    v.add_shoulder_candle(12, 25, -1, height=4, wax_mat=1, flame_mat=3)

    # 6. 3D forged iron neck chain + tarnished brass bell amulet at chest
    v.add_3d_chain((-7, 23, 8), (0, 16, 10), mat_idx=0, sag_voxels=1.6)
    v.add_3d_chain((7, 23, 8), (0, 16, 10), mat_idx=0, sag_voxels=1.6)
    # Tarnished brass bell amulet (mat_idx = 2) at (0, 13..15, 10)
    v.fill_box(-1, 1, 13, 15, 9, 11, 2, 1.05, 0.70)
    v.set_voxel(0, 12, 10, 3, 1.08, 0.90)

    # 7. Diagonal cross-body bandolier with 8 brass-tipped cartridges across chest
    for i in range(8):
        bx = -8 + i * 2
        by = 21 - i * 2
        bz = 9
        v.fill_box(bx - 1, bx + 1, by - 1, by + 1, bz - 1, bz, 1, 0.92, 0.38)
        # Cartridge: brass casing (mat_idx=2) + iron bullet tip (mat_idx=0)
        v.set_voxel(bx, by, bz + 1, 2, 1.06, 0.72)
        v.set_voxel(bx, by + 1, bz + 1, 0, 1.00, 0.55)

    v.enforce_inner_clearance(CHEST_CLEARANCE)


def build_set0_legs(v: MicroVoxelBuilder) -> None:
    """
    Set 0 — Grave-Stalker's Boiled Leather / Voxel Inquisitor Legs:
    Single-leg piece spanning local wz = -0.68..+0.02 (iy = -38..+1).
    Stepped quilted stalker cuisse & knee-cop (iy = -38..0) with wrap-around leather thigh straps,
    3D brass buckles, strapped side holster pocket, and fluted iron knee cap (mat_idx=0) with dangling chains.
    """
    # 1. Stepped quilted stalker cuisse & lower greave transition (iy = -38..0)
    for iy in range(-38, 1):
        t = (iy + 38) / 38.0
        rx_in = 3.0 + t * 0.7
        rz_in = 3.0 + t * 0.7
        rx_out = rx_in + 2.0
        rz_out = rz_in + 2.0
        mat = 1
        # Quilted diamond seam ridges
        if (iy % 4 == 0):
            rx_out += 0.3
            rz_out += 0.3
        fill_elliptical_ring(v, iy, rx_in, rz_in, rx_out, rz_out, mat, 0.96, 0.45)

    # 2. Wrap-around leather thigh straps & 3D brass buckles at iy = -8, -16, -28
    for sy in (-8, -16, -28):
        fill_elliptical_ring(v, sy, 3.4, 3.4, 6.0, 6.0, 0, 0.94, 0.48)
        v.add_3d_buckle(0, sy, 6, half_w=2, half_h=1, frame_mat=2, pin_mat=0)

    # 3. Strapped side holster pocket on outer thigh (+ix = 5..7, iy = -17..-7, iz = -2..3)
    v.fill_box(5, 7, -17, -7, -2, 3, 1, 0.94, 0.40)
    v.fill_box(5, 8, -9, -6, -2, 3, 2, 1.04, 0.66)  # Brass holster flap clasp
    for c_i in range(4):
        cz = -1 + c_i
        v.set_voxel(8, -13, cz, 2, 1.06, 0.72)
        v.set_voxel(8, -12, cz, 0, 1.00, 0.55)

    # 4. Fluted iron knee-cop (poleyn, iy = -25..-18, front +iz) with dangling chain links
    for iy in range(-25, -17):
        k_bulge = 1.2 if -23 <= iy <= -20 else 0.6
        fill_elliptical_ring(v, iy, 3.3, 3.3, 5.8 + k_bulge, 6.2 + k_bulge, 0, 1.02, 0.56, iz_min=0, iz_max=8)
        if iy in (-24, -21, -18):
            v.set_voxel(0, iy, 7, 2, 1.06, 0.68)
    v.add_3d_chain((-5, -21, 4), (0, -26, 6), mat_idx=0, sag_voxels=1.4)
    v.add_3d_chain((5, -21, 4), (0, -26, 6), mat_idx=0, sag_voxels=1.4)

    v.enforce_inner_clearance(LEGS_CLEARANCE)


def build_set0_feet(v: MicroVoxelBuilder) -> None:
    """
    Set 0 — Grave-Stalker's Boiled Leather / Voxel Inquisitor Feet:
    Heavy folded-cuff Inquisitor hunting boots (iy = -10..13) with wide folded top cuff (iy = 8..13),
    3D ankle iron buckles & straps, stepped armored toe cap (iz = 4..9), and cleated tread notches
    carved into the sole (iy = -10).
    """
    # 1. Boot shaft (iy = -7..8) & wide folded cavalier top cuff (iy = 8..13)
    for iy in range(-7, 14):
        is_cuff = iy >= 8
        rx_in = 2.8
        rz_in = 2.8
        rx_out = (5.4 + (13 - iy) * 0.25) if is_cuff else 4.6
        rz_out = (5.4 + (13 - iy) * 0.25) if is_cuff else 4.6
        mat = 2 if iy in (8, 13) else 1
        fill_elliptical_ring(v, iy, rx_in, rz_in, rx_out, rz_out, mat, 0.96, 0.46)

    # 2. 3D ankle & shin iron straps + brass buckles (iy = -3, +3, +7)
    for sy in (-3, 3, 7):
        fill_elliptical_ring(v, sy, 3.0, 3.0, 5.4, 5.4, 0, 0.98, 0.52)
        v.add_3d_buckle(0, sy, 5, half_w=2, half_h=1, frame_mat=2, pin_mat=0)

    # 3. Heavy boot foot & stepped armored iron toe cap (iy = -9..-5, iz = -5..9)
    for iy in range(-9, -4):
        h_t = (iy + 9) / 5.0
        max_z = int(round(9 - h_t * 3.0))
        hw = int(round(4.5 - h_t * 0.6))
        for ix in range(-hw, hw + 1):
            for iz in range(-5, max_z + 1):
                if (ix / (hw + 0.4)) ** 2 + ((iz - 1.5) / (max_z + 4.5)) ** 2 <= 1.0:
                    is_toecap = iz >= 4
                    is_trim = (iz == 4 and iy == -6) or (abs(ix) == hw and iy == -8)
                    mat = 2 if is_trim else (0 if is_toecap else 1)
                    v.set_voxel(ix, iy, iz, mat, 1.00, 0.54)

    # 4. Heavy cleated sole at iy = -10 with carved tread notches
    for ix in range(-4, 5):
        for iz in range(-5, 10):
            if (ix / 4.6) ** 2 + ((iz - 1.8) / 7.8) ** 2 <= 1.0:
                # Carve deep cleated tread grooves at iz = -1, 2, 5
                if iz in (-1, 2, 5) and abs(ix) <= 3:
                    continue
                v.set_voxel(ix, -10, iz, 0, 0.82, 0.35)

    v.enforce_inner_clearance(FEET_CLEARANCE)



def build_set1_head(v: MicroVoxelBuilder) -> None:
    """
    Set 1 — Ashen Basilica Paladin Head:
    Tall stepped cathedral barbute / winged greathelm (mat_idx=0) with raised brass T-visor cross (mat_idx=2),
    glowing T-slit ocular runes (mat_idx=3), swept stepped brass angel-wings on both sides (ix=±7..±11, iy=4..16),
    and high riveted gorget.
    """
    # 1. High riveted steel gorget & buckled neck collar (iy = -3..1)
    for iy in range(-3, 2):
        rx_in = 5.5
        rz_in = 5.9
        rx_out = 7.9 if iy <= -1 else 7.5
        rz_out = 8.3 if iy <= -1 else 7.9
        mat = 2 if iy in (-3, 0) else 0
        fill_elliptical_ring(v, iy, rx_in, rz_in, rx_out, rz_out, mat, 1.00, 0.56)
    v.add_3d_buckle(0, -1, -8, half_w=2, half_h=1, frame_mat=2, pin_mat=0)

    # 2. Tall stepped cathedral barbute / greathelm bowl (iy = 2..15)
    for iy in range(2, 16):
        t = (iy - 2) / 13.0
        dome_scale = 1.0 if iy <= 10 else (1.0 - ((iy - 10) / 5.5) * 0.46)
        rx_out = 7.6 * dome_scale
        rz_out = 8.0 * dome_scale
        rx_in = max(0.0, rx_out - 2.2) if iy <= 13 else 0.0
        rz_in = max(0.0, rz_out - 2.2) if iy <= 13 else 0.0
        fill_elliptical_ring(v, iy, rx_in, rz_in, rx_out, rz_out, 0, 1.00, 0.54)
        # Fluted vertical cathedral ribs on the crown & back
        if iy <= 12:
            for rib_x in (-5, -3, 0, 3, 5):
                v.set_voxel(rib_x, iy, -int(round(rz_out)), 2 if rib_x == 0 else 0, 1.04, 0.62)

    # Stepped brass cathedral ridge crest across top of helm (iy = 13..17, ix = 0)
    for iz in range(-6, 7):
        crest_h = 16 if abs(iz) <= 3 else 15
        for iy in range(13, crest_h + 1):
            v.set_voxel(0, iy, iz, 2, 1.06, 0.70)
        if iz % 2 == 0 and abs(iz) <= 4:
            v.set_voxel(0, crest_h + 1, iz, 2, 1.08, 0.74)

    # 3. Raised brass T-visor cross (mat_idx=2) & glowing T-slit ocular runes (mat_idx=3) at front (+iz)
    # Glowing T-slit horizontal eye-bar (iy = 5, ix = -4..4) & vertical nasal slit (ix = 0, iy = 1..6)
    for ix in range(-4, 5):
        v.set_voxel(ix, 5, 7, 3, 1.08, 0.95)
        v.set_voxel(ix, 5, 8, 3, 1.10, 0.98)
        # Brass brow & cheek visor trim framing the glowing slit
        v.set_voxel(ix, 6, 8, 2, 1.06, 0.70)
        v.set_voxel(ix, 4, 8, 2, 1.04, 0.68)
    for iy in range(1, 9):
        v.set_voxel(0, iy, 8, 3 if 2 <= iy <= 5 else 2, 1.08, 0.85)
        for sx in (-1, 1):
            if iy in (1, 2, 3, 7, 8):
                v.set_voxel(sx, iy, 8, 2, 1.05, 0.68)
    # Breathing vent perforations on lower faceplate
    for sx in (-1, 1):
        for vx in (2, 4):
            for vy in (1, 3):
                v.carve_voxel(sx * vx, vy, 7)
                v.set_voxel(sx * vx, vy, 8, 2, 1.02, 0.64)

    # 4. Swept stepped brass angel-wings on both sides (ix = ±7..±11, iy = 4..16)
    for sx in (-1, 1):
        # Wing mount boss on temple
        v.fill_box(sx * 7, sx * 8, 5, 8, -1, 2, 2, 1.04, 0.68)
        for step in range(8):
            wx = sx * (8 + (step // 3))
            wy_base = 5 + step
            wz = 1 - step
            feather_len = 4 + (step % 3)
            for dy in range(feather_len):
                mat = 2 if (dy >= feather_len - 2 or step % 2 == 0) else 0
                v.set_voxel(wx, wy_base + dy, wz, mat, 1.06, 0.72)
                if step >= 4 and dy == feather_len - 1:
                    v.set_voxel(sx * (abs(wx) + 1), wy_base + dy, wz - 1, 2, 1.08, 0.76)

    v.enforce_inner_clearance(HEAD_CLEARANCE)


def build_set1_chest(v: MicroVoxelBuilder) -> None:
    """
    Set 1 — Ashen Basilica Paladin Chest:
    Multi-stepped fluted gothic plate cuirass (mat_idx=0) with a bold 3D stepped brass Synod cross relief
    across the sternum (mat_idx=2), tiered cathedral pauldrons (ix=-17..17) crowned with lit sanctuary
    wax candles (add_shoulder_candle) and crimson wax purity seals with stepped parchment ribbons,
    heavy chain belt (add_3d_chain) suspending a 3D brass censer & reliquary tome, and tattered split
    paladin tabard skirts (iy=-10..0, mat_idx=1) with brass hem border & battle-worn voxel perforations.
    """
    # 1. Multi-stepped fluted gothic plate cuirass (iy = 0..24)
    for iy in range(0, 25):
        t = iy / 24.0
        lame_step = 0.35 if (iy % 4 == 0) else 0.0
        rx_in = 9.6 + math.sin(t * math.pi) * 1.1
        rz_in = 6.6 + math.sin(t * math.pi) * 0.8
        rx_out = rx_in + 2.4 + lame_step
        rz_out = rz_in + 2.4 + lame_step
        mat = 2 if iy in (0, 24) else 0
        fill_elliptical_ring(v, iy, rx_in, rz_in, rx_out, rz_out, mat, 1.00, 0.56)

    # 2. Bold 3D stepped brass Synod cross relief across the sternum (iy = 6..21, front +iz)
    for iy in range(6, 22):
        for ix in (-1, 0, 1):
            mat = 3 if (ix == 0 and iy == 15) else 2
            v.set_voxel(ix, iy, 10, mat, 1.08, 0.75)
            if ix == 0:
                v.set_voxel(0, iy, 11, mat, 1.10, 0.82)
    # Crossbars of Synod cross at iy = 15 (main) and iy = 19 (upper)
    for ix in range(-5, 6):
        v.set_voxel(ix, 15, 10, 2, 1.08, 0.74)
        v.set_voxel(ix, 14, 10, 2, 1.04, 0.68)
        if abs(ix) <= 3:
            v.set_voxel(ix, 19, 10, 2, 1.08, 0.74)

    # 3. Tiered cathedral pauldrons (ix = -17..17, iy = 18..26) + haute-piece neck guards
    for sx in (-1, 1):
        for tier in range(3):
            y0 = 18 + tier * 2
            y1 = y0 + 2
            x_in = 10 + tier
            x_out = 17 - tier
            for ix in range(x_in, x_out + 1):
                for iy in range(y0, y1 + 1):
                    for iz in range(-6, 7):
                        if ((iz / 6.5) ** 2 + ((ix - x_in) / 7.5) ** 2) <= 1.05:
                            is_rim = (ix == x_out or iy == y0 or abs(iz) == 6)
                            v.set_voxel(sx * ix, iy, iz, 2 if is_rim else 0, 1.02, 0.60)
        # Upright brass cathedral haute-piece guard at ix = ±11, iy = 24..27
        v.fill_box(sx * 11, sx * 11, 24, 27, -4, 4, 2, 1.06, 0.72)

    # Lit sanctuary wax candles crowning both pauldrons
    v.add_shoulder_candle(-14, 25, 0, height=5, wax_mat=1, flame_mat=3)
    v.add_shoulder_candle(13, 25, 0, height=5, wax_mat=1, flame_mat=3)

    # Crimson wax purity seals (mat_idx=3) with stepped parchment ribbons (mat_idx=1/2)
    for sx, sy, sz in ((-13, 19, 6), (13, 19, 6), (-6, 9, 9)):
        v.fill_box(sx - 1, sx, sy, sy + 1, sz, sz + 1, 3, 1.08, 0.90)
        for ry in range(1, 5):
            v.set_voxel(sx, sy - ry, sz + (ry // 3), 1 if ry < 4 else 2, 0.98, 0.65)

    # 4. Heavy chain belt (add_3d_chain) suspending 3D brass censer & reliquary tome
    for iy in (0, 1):
        fill_elliptical_ring(v, iy, 9.8, 6.7, 12.5, 9.3, 2 if iy == 1 else 0, 1.02, 0.62)
    v.add_3d_buckle(0, 1, 10, half_w=3, half_h=2, frame_mat=2, pin_mat=3)
    v.add_3d_chain((-9, 2, 8), (0, -2, 10), mat_idx=2, sag_voxels=1.5)
    v.add_3d_chain((9, 2, 8), (0, -2, 10), mat_idx=2, sag_voxels=1.5)

    # 3D Brass Censer with glowing incense core on right hip (ix = 11..14, iy = -8..-2, iz = 2..5)
    v.add_3d_chain((11, 1, 4), (12, -3, 4), mat_idx=2, sag_voxels=1.0)
    v.fill_box(11, 14, -7, -4, 2, 5, 2, 1.06, 0.72)
    v.fill_box(12, 13, -6, -5, 3, 4, 3, 1.10, 0.95)
    # Reliquary Tome on left hip (ix = -14..-11, iy = -7..-1, iz = -2..3)
    v.fill_box(-13, -11, -7, -1, -2, 3, 1, 0.94, 0.42)
    v.fill_box(-14, -12, -6, -2, -1, 2, 2, 1.06, 0.70)

    # 5. Tattered split paladin tabard skirts (iy = -10..0, mat_idx=1) with brass hem & perforations
    for iy in range(-10, 1):
        flare = (0 - iy) * 0.25
        rx_in = 9.6 + flare
        rz_in = 6.6 + flare * 0.7
        rx_out = rx_in + 2.2
        rz_out = rz_in + 2.2
        mat = 2 if iy == -10 else 1
        fill_elliptical_ring(v, iy, rx_in, rz_in, rx_out, rz_out, mat, 0.96, 0.48)
        # Split side & center openings + battle-worn voxel perforations
        v.carve_box(-2, 2, iy, iy, -14, 14)
        for ix in range(-14, 15):
            for iz in range(-12, 13):
                if iy <= -5 and ((ix * 11 + iy * 7 + iz * 3) % 10 == 0):
                    v.carve_voxel(ix, iy, iz)

    v.enforce_inner_clearance(CHEST_CLEARANCE)



def build_set1_legs(v: MicroVoxelBuilder) -> None:
    """
    Set 1 — Ashen Basilica Paladin Legs:
    Single-leg piece spanning local wz = -0.68..+0.02 (iy = -38..+1).
    Stepped articulated plate cuisse lames & winged poleyn knee-guard (mat_idx=0) with raised
    brass cross ridges (mat_idx=2), rear leather straps, and hanging chain-maille voxel fringes.
    """
    # 1. Stepped articulated plate cuisse lames & upper shin plates (iy = -38..0)
    for iy in range(-38, 1):
        t = (iy + 38) / 38.0
        lame_step = 0.45 if (iy % 5 == 0) else 0.0
        rx_in = 3.0 + t * 0.7
        rz_in = 3.0 + t * 0.7
        rx_out = rx_in + 2.1 + lame_step
        rz_out = rz_in + 2.1 + lame_step
        mat = 2 if (iy % 5 == 0) else 0
        fill_elliptical_ring(v, iy, rx_in, rz_in, rx_out, rz_out, mat, 1.00, 0.56)

    # 2. Rear leather straps & brass buckles at iy = -7, -15, -29 (-iz back of leg)
    for sy in (-7, -15, -29):
        fill_elliptical_ring(v, sy, 3.4, 3.4, 6.1, 6.1, 1, 0.94, 0.44)
        v.add_3d_buckle(0, sy, -6, half_w=2, half_h=1, frame_mat=2, pin_mat=0)

    # 3. Winged poleyn knee-guard (iy = -25..-17, front +iz) with raised brass cross ridges
    for iy in range(-25, -16):
        k_bulge = 1.4 if -23 <= iy <= -19 else 0.7
        fill_elliptical_ring(v, iy, 3.3, 3.3, 6.0 + k_bulge, 6.4 + k_bulge, 0, 1.04, 0.58, iz_min=0, iz_max=8)
        # Raised vertical brass cross ridge down knee-cop center
        v.set_voxel(0, iy, 7, 2, 1.08, 0.72)
        if iy == -21:
            for kx in range(-3, 4):
                v.set_voxel(kx, iy, 7, 3 if kx == 0 else 2, 1.08, 0.78)
            # Swept side poleyn wings at ix = ±6..±7
            for sx in (-1, 1):
                v.fill_box(sx * 6, sx * 7, -23, -18, 0, 3, 2, 1.06, 0.70)

    # 4. Hanging chain-maille voxel fringes at upper tasset & below knee
    v.add_3d_chain((-5, -3, 4), (0, -9, 6), mat_idx=2, sag_voxels=1.4)
    v.add_3d_chain((5, -3, 4), (0, -9, 6), mat_idx=2, sag_voxels=1.4)
    v.add_3d_chain((-5, -24, 4), (0, -28, 6), mat_idx=0, sag_voxels=1.2)
    v.add_3d_chain((5, -24, 4), (0, -28, 6), mat_idx=0, sag_voxels=1.2)

    v.enforce_inner_clearance(LEGS_CLEARANCE)


def build_set1_feet(v: MicroVoxelBuilder) -> None:
    """
    Set 1 — Ashen Basilica Paladin Feet:
    Articulated overlapping gothic sabatons (mat_idx=0) with brass-trimmed shin greave crest (mat_idx=2),
    ankle spur + rowel wheel at iz = -6, and stepped pointed solleret toe lames (iz = 4..10).
    """
    # 1. Articulated gothic shin greave & brass-trimmed knee-cuff crest (iy = -7..13)
    for iy in range(-7, 14):
        lame_step = 0.35 if (iy % 4 == 0) else 0.0
        rx_in = 2.8
        rz_in = 2.8
        rx_out = 4.7 + lame_step + (0.6 if iy >= 10 else 0.0)
        rz_out = 4.7 + lame_step + (0.6 if iy >= 10 else 0.0)
        mat = 2 if (iy >= 11 or iy % 4 == 0) else 0
        fill_elliptical_ring(v, iy, rx_in, rz_in, rx_out, rz_out, mat, 1.00, 0.56)
        # Raised brass shin crest along front center (+iz)
        if iy >= -4:
            v.set_voxel(0, iy, int(round(rz_out)), 2, 1.08, 0.72)

    # 2. Rear ankle straps + sanctified heel spur & star rowel wheel at iz = -6..-8
    for sy in (-2, 5):
        v.add_3d_buckle(0, sy, -5, half_w=2, half_h=1, frame_mat=2, pin_mat=0)
    # Heel spur yoke & rowel wheel at iy = -7, iz = -5..-8
    v.fill_box(-3, 3, -7, -7, -5, -4, 2, 1.04, 0.68)
    v.fill_box(0, 0, -7, -7, -7, -5, 2, 1.06, 0.70)
    for dy, dz in ((0, -8), (1, -7), (-1, -7), (0, -6)):
        v.set_voxel(0, -7 + dy, dz, 2, 1.08, 0.75)

    # 3. Articulated overlapping gothic sabatons & stepped pointed solleret toe lames (iz = 4..10)
    for iy in range(-9, -4):
        h_t = (iy + 9) / 5.0
        max_z = int(round(10 - h_t * 3.5))
        for iz in range(-5, max_z + 1):
            taper_w = 1.0 if iz <= 4 else max(0.25, 1.0 - ((iz - 4) / 6.5) * 0.75)
            hw = max(1, int(round((4.5 - h_t * 0.5) * taper_w)))
            for ix in range(-hw, hw + 1):
                is_lame_ridge = (iz >= 3 and iz % 2 == 0 and iy == -6) or (ix == 0 and iz >= 4)
                mat = 2 if is_lame_ridge else 0
                v.set_voxel(ix, iy, iz, mat, 1.02, 0.58)

    # 4. Cleated steel sabaton sole at iy = -10
    for ix in range(-4, 5):
        for iz in range(-5, 10):
            if (ix / 4.5) ** 2 + ((iz - 2.0) / 8.0) ** 2 <= 1.0:
                if iz in (-1, 2, 5) and abs(ix) <= 3:
                    continue
                v.set_voxel(ix, -10, iz, 0, 0.84, 0.38)

    v.enforce_inner_clearance(FEET_CLEARANCE)


def export_piece(set_idx: int, slot: str, builder_fn) -> tuple[str, int, int, int]:
    clear_scene()
    mats = make_micro_voxel_materials(set_idx)
    builder = MicroVoxelBuilder(f"Armor_Set{set_idx}_{slot}", voxel_size=VOXEL_SIZE)
    builder_fn(builder)
    voxel_count = len(builder.voxels)
    obj = builder.build_mesh_object(mats)
    tri_count = sum(len(p.vertices) - 2 for p in obj.data.polygons)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"armor_set{set_idx}_{slot}.glb")
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_all_vertex_colors=True,
    )
    fsize = os.path.getsize(out_path) if os.path.exists(out_path) else 0
    print(
        f"[Micro-Voxel Armor 0-1] armor_set{set_idx}_{slot}.glb | voxels={voxel_count} | tris={tri_count} | mesh_nodes=1 | size={fsize} bytes"
    )
    return out_path, voxel_count, tri_count, fsize


def main() -> None:
    only_set_0 = ("--only-set-0" in sys.argv) or ("--set0" in sys.argv)
    if only_set_0:
        export_all_set0_starter(OUTPUT_DIR)
        print("[Micro-Voxel Armor 0-1] --only-set-0 active: exported 5 Set 0 pieces + base mannequin; skipping Set 1.")
        return

    from blender_sets_1_2_3_7mm import export_sets_1_2_3_7mm
    selected_sets = [1]
    for i, arg in enumerate(sys.argv):
        if arg == "--sets" and i + 1 < len(sys.argv):
            selected_sets = [int(x.strip()) for x in sys.argv[i + 1].split(",") if x.strip().isdigit() and int(x.strip()) in (1, 2, 3)]
        elif arg.startswith("--sets="):
            selected_sets = [int(x.strip()) for x in arg.split("=", 1)[1].split(",") if x.strip().isdigit() and int(x.strip()) in (1, 2, 3)]
    export_sets_1_2_3_7mm(OUTPUT_DIR, tuple(selected_sets))



if __name__ == "__main__":
    main()

