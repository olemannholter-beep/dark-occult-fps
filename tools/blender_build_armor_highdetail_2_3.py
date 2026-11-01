import bpy
import math
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from blender_micro_voxel_kit import MicroVoxelBuilder, make_micro_voxel_materials

OUTPUT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "assets", "models", "armor"))
VOXEL_SIZE = 0.018

HEAD_CLEARANCE = lambda wx, wy, wz: (-0.06 <= wz <= 0.20) and ((wx / 0.092) ** 2 + (wy / 0.098) ** 2 < 1.0)
CHEST_CLEARANCE = lambda wx, wy, wz: (-0.12 <= wz <= 0.50) and ((wx / 0.168) ** 2 + (wy / 0.114) ** 2 < 1.0)
LEGS_CLEARANCE = lambda wx, wy, wz: (wz >= -0.04) and (((wx * 1.15 + 0.125) / 0.145) ** 2 + ((wy * 1.15) / 0.100) ** 2 < 1.0)


def clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def add_elliptical_layer(
    b: MicroVoxelBuilder,
    iy: int,
    rx_in: float,
    ry_in: float,
    thick: float,
    mat_idx: int = 0,
    shade_bias: float = 1.0,
    tint_b: float = 0.5,
    cx: float = 0.0,
    cz: float = 0.0,
) -> None:
    s = b.voxel_size
    rx_out = rx_in + thick
    ry_out = ry_in + thick
    ix_max = int(math.ceil(( abs(cx) + rx_out) / s)) + 1
    iz_max = int(math.ceil(( abs(cz) + ry_out) / s)) + 1
    for ix in range(-ix_max, ix_max + 1):
        for iz in range(-iz_max, iz_max + 1):
            wx = (ix + 0.5) * s - cx
            wy = (iz + 0.5) * s - cz
            d_in = (wx / max(0.001, rx_in)) ** 2 + (wy / max(0.001, ry_in)) ** 2
            d_out = (wx / max(0.001, rx_out)) ** 2 + (wy / max(0.001, ry_out)) ** 2
            if d_in >= 1.0 and d_out <= 1.0:
                b.set_voxel(ix, iy, iz, mat_idx, shade_bias, tint_b)


def build_set2_head(b: MicroVoxelBuilder) -> None:
    # Set 2 — Vigil of the Cinder / Siege Juggernaut (HEAD):
    # Stepped frog-mouth / furnace-brazier siege greathelm (iy = -3..19)
    for iy in range(-3, 14):
        if iy <= 0:
            rx, ry, th = 0.108, 0.114, 0.038
            mat = 2 if iy in (-3, 0) else 0
        elif iy <= 9:
            rx, ry, th = 0.102, 0.108, 0.040
            mat = 2 if iy in (4, 9) else 0
        else:
            t = (iy - 9) / 5.0
            rx = 0.102 * (1.0 - t * 0.16)
            ry = 0.108 * (1.0 - t * 0.16)
            th = 0.038
            mat = 2 if iy == 13 else 0
        add_elliptical_layer(b, iy, rx, ry, th, mat_idx=mat, shade_bias=1.0, tint_b=0.52)

    # Solid top cap under the brazier crown (iy = 12..13)
    for iy in (12, 13):
        for ix in range(-5, 6):
            for iz in range(-5, 6):
                if ix * ix + iz * iz <= 24:
                    b.set_voxel(ix, iy, iz, 0 if iy == 12 else 2, 1.0, 0.55)

    # Stepped frog-mouth siege prow protruding forward (iz = 6..11, iy = 1..10)
    for iy in range(1, 11):
        prow_z = 11 - abs(iy - 5) // 2
        for iz in range(6, prow_z + 1):
            half_w = max(1, 6 - (iz - 5))
            for ix in range(-half_w, half_w + 1):
                is_keel = abs(ix) == 0
                is_trim = iy in (1, 5, 10) or abs(ix) == half_w
                mat = 2 if (is_keel or is_trim) else 0
                b.set_voxel(ix, iy, iz, mat, 1.03 if is_keel else 0.98, 0.58)

    # Slotted furnace grate visor revealing glowing cinder embers (mat_idx = 3)
    for iy in range(6, 10):
        for ix in range(-4, 5):
            b.set_voxel(ix, iy, 7, 3, 1.08, 0.90)
            b.set_voxel(ix, iy, 8, 3 if (ix % 2 != 0 and iy in (7, 8)) else 0, 1.04, 0.75)
            for iz in range(9, 12):
                if (ix, iy, iz) in b.voxels:
                    if ix % 2 == 0 or iy == 9:
                        b.set_voxel(ix, iy, iz, 2, 1.04, 0.65)
                    else:
                        b.carve_voxel(ix, iy, iz)

    # Lower furnace breather vents on the frog-mouth jaw (iy = 2..4)
    for iy in (2, 4):
        for ix in (-3, -2, 2, 3):
            b.set_voxel(ix, iy, 8, 3, 1.05, 0.85)
            b.carve_voxel(ix, iy, 9)

    # Side ear-bastions & bolted cheek plates
    for sx in (-1, 1):
        b.fill_box(sx * 6, sx * 8, 3, 9, -2, 3, mat_idx=0, shade_bias=0.98, tint_b=0.50)
        b.fill_box(sx * 8, sx * 8, 4, 8, -1, 2, mat_idx=2, shade_bias=1.02, tint_b=0.62)
        b.set_voxel(sx * 8, 6, 0, 3, 1.06, 0.88)
        b.set_voxel(sx * 8, 6, 1, 3, 1.06, 0.88)

    # Top-mounted iron brazier crown (iy = 13..15) with glowing coal bed & melted wax candles
    for ix in range(-4, 5):
        for iz in range(-4, 5):
            r2 = ix * ix + iz * iz
            if r2 <= 18:
                b.set_voxel(ix, 13, iz, 3 if r2 <= 10 else 2, 1.05, 0.80)
                if 11 <= r2 <= 18:
                    b.set_voxel(ix, 14, iz, 0, 1.0, 0.52)
                    if (ix + iz) % 2 == 0:
                        b.set_voxel(ix, 15, iz, 2, 1.04, 0.65)

    # Melted wax candles with cascading drips & multi-stepped voxel flames (reaches iy = 19)
    b.add_shoulder_candle(-3, 14, 0, height=3, wax_mat=1, flame_mat=3)
    b.add_shoulder_candle(2, 14, 0, height=3, wax_mat=1, flame_mat=3)
    b.add_shoulder_candle(0, 14, -3, height=3, wax_mat=1, flame_mat=3)


def build_set2_chest(b: MicroVoxelBuilder) -> None:
    # Set 2 — Vigil of the Cinder / Siege Juggernaut (CHEST):
    # Multi-stepped siege plate cuirass (iy = -10..30) outside (0.168, 0.114) inner ellipse
    for iy in range(0, 25):
        t = iy / 24.0
        rx = 0.174 + t * 0.022
        ry = 0.120 + t * 0.018
        th = 0.042 if (iy % 5 != 0) else 0.050
        mat = 2 if (iy in (0, 5, 11, 17, 23, 24)) else 0
        add_elliptical_layer(b, iy, rx, ry, th, mat_idx=mat, shade_bias=1.0, tint_b=0.52)
        # Carve arm sockets at upper sides (iy = 14..22)
        if 14 <= iy <= 22:
            b.carve_box(-15, -9, iy, iy, -4, 4)
            b.carve_box(9, 15, iy, iy, -4, 4)

    # Vertical furnace exhaust louver grilles on front chest (recessed mat_idx=3 ember glow)
    for sx in (-1, 1):
        for iy in range(6, 20):
            for ix in range(2, 7):
                px = sx * ix
                b.set_voxel(px, iy, 7, 3, 1.08, 0.90)
                if iy % 2 == 0:
                    b.set_voxel(px, iy, 8, 2 if ix in (2, 6) else 0, 1.02, 0.60)
                    b.set_voxel(px, iy, 9, 2, 1.04, 0.66)
                else:
                    b.set_voxel(px, iy, 8, 3, 1.06, 0.88)
                    b.carve_voxel(px, iy, 9)

    # Heavy central sternum keel & dorsal furnace spine
    b.fill_box(-1, 1, 3, 22, 8, 9, mat_idx=2, shade_bias=1.04, tint_b=0.65)
    for iy in range(4, 22, 3):
        b.fill_box(-2, 2, iy, iy + 1, -9, -8, mat_idx=2, shade_bias=1.02, tint_b=0.60)
        b.set_voxel(0, iy, -9, 3, 1.06, 0.88)

    # Towering stepped Dreadnought smokestack & candle pauldrons (ix = -18..18, iy = 18..28)
    for sx in (-1, 1):
        for tier, (y0, y1, x_in, x_out, z_span) in enumerate([
            (18, 21, 9, 18, 6),
            (21, 24, 9, 17, 5),
            (24, 26, 10, 16, 4),
        ]):
            xa, xb = sx * x_in, sx * x_out
            b.fill_box(xa, xb, y0, y1, -z_span, z_span, mat_idx=0, shade_bias=1.0, tint_b=0.52)
            # Stepped brass border rims
            b.fill_box(xa, xb, y0, y0, -z_span, z_span, mat_idx=2, shade_bias=1.04, tint_b=0.64)
            b.fill_box(xb, xb, y0, y1, -z_span, z_span, mat_idx=2, shade_bias=1.04, tint_b=0.64)
            # Carve underside hollow of pauldron
            b.carve_box(sx * (x_in + 1), sx * (x_out - 2), y0, y0 + 1, -(z_span - 2), z_span - 2)

        # Dreadnought exhaust smokestacks on rear of pauldron
        for stack_z in (-3, 0):
            sx_pipe = sx * 12
            b.fill_box(sx_pipe - 1, sx_pipe + 1, 25, 28, stack_z - 1, stack_z + 1, mat_idx=0, shade_bias=0.96, tint_b=0.48)
            b.fill_box(sx_pipe - 1, sx_pipe + 1, 28, 28, stack_z - 1, stack_z + 1, mat_idx=2, shade_bias=1.04, tint_b=0.65)
            b.set_voxel(sx_pipe, 28, stack_z, 3, 1.08, 0.92)

        # Melted wax shoulder candles on forward pauldron crest
        cx_c = -14 if sx < 0 else 13
        b.add_shoulder_candle(cx_c, 25, 2, height=3, wax_mat=1, flame_mat=3)

    # Heavy criss-crossing 3D iron chains across chest & back
    b.add_3d_chain((-9, 21, 8), (9, 9, 8), mat_idx=0, sag_voxels=1.8)
    b.add_3d_chain((9, 21, 8), (-9, 9, 8), mat_idx=0, sag_voxels=1.8)
    b.add_3d_chain((-8, 20, -8), (8, 9, -8), mat_idx=2, sag_voxels=1.5)

    # Waist belt, 3D buckles, brass cinder-censer & iron-bound pyre tome
    for iy in range(-2, 2):
        add_elliptical_layer(b, iy, 0.174, 0.120, 0.046, mat_idx=1 if iy in (-1, 0) else 2, shade_bias=1.0, tint_b=0.58)
    b.add_3d_buckle(0, 0, 9, half_w=2, half_h=2, frame_mat=2, pin_mat=0)
    b.add_3d_buckle(0, 0, -9, half_w=2, half_h=2, frame_mat=2, pin_mat=0)

    # Brass cinder-censer on right hip (ix = 10..12, iy = -6..-1, iz = 2..5)
    b.fill_box(10, 12, -6, -2, 2, 5, mat_idx=2, shade_bias=1.04, tint_b=0.66)
    b.fill_box(10, 12, -4, -3, 2, 5, mat_idx=3, shade_bias=1.08, tint_b=0.90)
    b.add_3d_chain((10, 0, 4), (11, -2, 4), mat_idx=2, sag_voxels=0.5)

    # Iron-bound pyre tome on left hip (ix = -12..-10, iy = -6..0, iz = 1..5)
    b.fill_box(-12, -10, -6, -1, 1, 5, mat_idx=1, shade_bias=0.98, tint_b=0.45)
    b.fill_box(-12, -10, -6, -6, 1, 5, mat_idx=2, shade_bias=1.02, tint_b=0.65)
    b.fill_box(-12, -10, -1, -1, 1, 5, mat_idx=2, shade_bias=1.02, tint_b=0.65)
    b.fill_box(-12, -12, -5, -2, 2, 4, mat_idx=3, shade_bias=1.06, tint_b=0.88)

    # Jagged scorched tattered skirt plates & perforated cloth flaps (iy = -10..-2)
    for iy in range(-10, -2):
        add_elliptical_layer(b, iy, 0.174, 0.120, 0.036, mat_idx=1 if iy < -5 else 0, shade_bias=0.94, tint_b=0.48)
        for ix in range(-12, 13):
            for iz in range(-9, 10):
                # Open front/back walking split & sawtooth jagged hem
                if abs(ix) <= 2 and iz > 0 and iy < -4:
                    b.carve_voxel(ix, iy, iz)
                saw_limit = -10 + ((abs(ix * 3 + iz * 5)) % 4)
                if iy < saw_limit:
                    b.carve_voxel(ix, iy, iz)
                elif iy in (-8, -6, -5) and ((ix * 7 + iz * 11 + iy * 3) % 13 == 0):
                    b.carve_voxel(ix, iy, iz)



def build_set2_legs(b: MicroVoxelBuilder) -> None:
    # Set 2 — Vigil of the Cinder / Siege Juggernaut (LEGS):
    # Heavy stepped siege-plate cuisse & piston-ribbed knee bastion (iy = -38..0)
    for iy in range(-38, 1):
        t = (iy + 38) / 38.0
        rx = 0.068 + t * 0.022
        ry = 0.072 + t * 0.022
        th = 0.036 if (iy % 6 != 0) else 0.044
        mat = 2 if (iy in (-38, -32, -25, -18, -10, -3, 0)) else 0
        add_elliptical_layer(b, iy, rx, ry, th, mat_idx=mat, shade_bias=1.0, tint_b=0.52)

    # Piston-ribbed knee bastion (iy = -26..-15, iz = 4..8) with brass-rimmed ember vents
    for iy in range(-26, -14):
        half_w = 4 if -23 <= iy <= -17 else 3
        for ix in range(-half_w, half_w + 1):
            is_rim = iy in (-26, -21, -15) or abs(ix) == half_w
            b.set_voxel(ix, iy, 6, 2 if is_rim else 0, 1.02, 0.58)
            if -24 <= iy <= -16 and abs(ix) <= 3:
                b.set_voxel(ix, iy, 7, 2 if (iy % 2 == 0 or abs(ix) == 3) else 3, 1.06, 0.80)

    # Side piston rods & outer tasset shields (ix = 4..7, iy = -14..0)
    for sx in (-1, 1):
        b.fill_box(sx * 5, sx * 6, -34, -6, -1, 1, mat_idx=2, shade_bias=1.02, tint_b=0.64)
        for iy in range(-32, -8, 6):
            b.set_voxel(sx * 6, iy, 0, 3, 1.08, 0.90)
    for iy in range(-14, 0):
        b.fill_box(5, 7, iy, iy, -4, 4, mat_idx=2 if iy in (-14, -7, -1) else 0, shade_bias=1.0, tint_b=0.55)
        if iy in (-11, -9, -5, -3):
            b.set_voxel(7, iy, 0, 3, 1.06, 0.88)

    # Wrap-around 3D iron chains & thigh buckles
    b.add_3d_chain((-5, -8, 6), (5, -12, 6), mat_idx=0, sag_voxels=1.2)
    b.add_3d_chain((5, -28, 6), (-5, -31, 6), mat_idx=2, sag_voxels=1.0)
    b.add_3d_buckle(0, -9, 6, half_w=2, half_h=1, frame_mat=2, pin_mat=0)


def build_set2_feet(b: MicroVoxelBuilder) -> None:
    # Set 2 — Vigil of the Cinder / Siege Juggernaut (FEET):
    # Colossal dreadnought siege sabatons (iy = -10..13) with battering-ram prow & cleated treads
    for iy in range(-6, 14):
        rx, ry = 0.056, 0.060
        th = 0.036 if (iy % 4 != 0) else 0.042
        mat = 2 if iy in (-5, 0, 5, 10, 13) else 0
        add_elliptical_layer(b, iy, rx, ry, th, mat_idx=mat, shade_bias=1.0, tint_b=0.52)

    # Vertical brass shin-ribs & glowing furnace ankle vents (mat_idx = 3)
    for ix in (-2, 0, 2):
        b.fill_box(ix, ix, -4, 12, 5, 6, mat_idx=2, shade_bias=1.04, tint_b=0.65)
    for sx in (-1, 1):
        for iy in (-3, -1, 1, 3):
            b.set_voxel(sx * 5, iy, 1, 3, 1.08, 0.92)
            b.set_voxel(sx * 5, iy, 2, 2, 1.02, 0.62)
        b.add_3d_buckle(0, 6, 6, half_w=2, half_h=1, frame_mat=2, pin_mat=0)

    # Wide reinforced battering-ram toe prow (iy = -9..-4, iz = -4..10)
    for iy in range(-9, -4):
        z_max = 10 - max(0, iy + 6)
        for iz in range(-5, z_max + 1):
            half_w = 4 if iz <= 6 else 3
            for ix in range(-half_w, half_w + 1):
                is_trim = (iy == -9) or (iz >= z_max - 1) or (abs(ix) == half_w) or (iz % 3 == 0 and iy == -5)
                mat = 2 if is_trim else 0
                b.set_voxel(ix, iy, iz, mat, 1.02 if is_trim else 0.96, 0.58)
        if iy in (-7, -6):
            b.set_voxel(-2, iy, z_max, 3, 1.08, 0.90)
            b.set_voxel(2, iy, z_max, 3, 1.08, 0.90)

    # Deep cleated sole treads at iy = -10
    for iz in range(-5, 10):
        if iz % 2 == 0:
            for ix in range(-4, 5):
                b.set_voxel(ix, -10, iz, 0 if abs(ix) < 4 else 2, 0.85, 0.45)


def build_set3_head(b: MicroVoxelBuilder) -> None:
    # Set 3 — Abyssal Ossuary Warden / Eldritch Reliquary (HEAD):
    # Towering jagged obsidian-iron & bone-ribbed Ossuary Mitre Crown (iy = -3..19)
    for iy in range(-3, 12):
        rx, ry = 0.104, 0.110
        th = 0.038
        mat = 2 if iy in (-3, 0, 10) else 0
        add_elliptical_layer(b, iy, rx, ry, th, mat_idx=mat, shade_bias=0.96, tint_b=0.48)

    # Towering twin-peaked Ossuary Mitre Crown (iy = 11..19)
    for iy in range(11, 20):
        t = (iy - 11) / 8.0
        half_w = max(2, int(round(6 * (1.0 - t * 0.55))))
        z_front = max(3, int(round(7 * (1.0 - t * 0.35))))
        z_back = min(-2, int(round(-6 * (1.0 - t * 0.45))))
        for ix in range(-half_w, half_w + 1):
            for iz in range(z_back, z_front + 1):
                if abs(ix) >= half_w - 1 or iz >= z_front - 1 or iz <= z_back + 1:
                    is_rib = (abs(ix) == 0) or (abs(ix) == half_w) or (iy == 19)
                    if is_rib:
                        b.set_voxel(ix, iy, iz, 1 if (iy % 2 == 0) else 2, 1.04, 0.90)
                    else:
                        b.set_voxel(ix, iy, iz, 0, 0.94, 0.45)

    # Chiseled skeletal death-visage mask (mat_idx = 1, tint_b = 0.92 bone-ivory) on front face (iz = 6..8, iy = 0..10)
    for iy in range(0, 11):
        half_w = 4 if iy >= 3 else 3
        for ix in range(-half_w, half_w + 1):
            b.set_voxel(ix, iy, 7, 1, 1.02, 0.92)
            if abs(ix) <= half_w - 1 and iy in (1, 2, 5, 8, 9):
                b.set_voxel(ix, iy, 8, 1, 1.04, 0.94)

    # Deeply recessed eye sockets + glowing abyssal violet eyes & 3rd-eye crown gem (mat_idx = 3)
    for sx in (-1, 1):
        for ex in (sx * 2, sx * 3):
            for ey in (6, 7):
                b.carve_voxel(ex, ey, 8)
                b.set_voxel(ex, ey, 7, 3, 1.08, 0.95)
        # Vertical tear-slit grooves below eyes (iy = 2..5)
        for ty in range(2, 6):
            b.carve_voxel(sx * 2, ty, 8)
            b.set_voxel(sx * 2, ty, 7, 0, 0.78, 0.35)
    # Skeletal teeth ribs at jaw (iy = 0..2)
    for ix in (-2, 0, 2):
        b.set_voxel(ix, 1, 8, 1, 1.04, 0.94)
        b.set_voxel(ix, 2, 8, 1, 1.04, 0.94)
    # 3rd-eye abyssal crown gem (iy = 10..12, ix = -1..1, iz = 7..8)
    b.fill_box(-1, 1, 10, 12, 7, 8, mat_idx=2, shade_bias=1.04, tint_b=0.68)
    b.set_voxel(0, 11, 8, 3, 1.08, 0.96)
    b.set_voxel(0, 14, 6, 3, 1.08, 0.96)

    # Sweeping bone/brass cathedral spires on the temples (ix = ±7..±10, iy = 4..17)
    for sx in (-1, 1):
        for dy in range(0, 14):
            iy = 4 + dy
            ix = sx * (7 + dy // 5)
            iz = 1 - dy // 4
            b.fill_box(ix, ix + sx, iy, iy, iz - 1, iz + 1, mat_idx=1 if dy % 2 == 0 else 2, shade_bias=1.02, tint_b=0.92)
            if dy in (4, 9, 13):
                b.set_voxel(ix + sx, iy, iz, 3, 1.08, 0.95)



def build_set3_chest(b: MicroVoxelBuilder) -> None:
    # Set 3 — Abyssal Ossuary Warden / Eldritch Reliquary (CHEST):
    # Bone-ribbed thoracic cage & obsidian plate cuirass (iy = -10..30)
    for iy in range(0, 25):
        t = iy / 24.0
        rx = 0.174 + t * 0.022
        ry = 0.120 + t * 0.018
        th = 0.040
        mat = 2 if iy in (0, 6, 18, 24) else 0
        add_elliptical_layer(b, iy, rx, ry, th, mat_idx=mat, shade_bias=0.95, tint_b=0.46)
        if 14 <= iy <= 22:
            b.carve_box(-15, -9, iy, iy, -4, 4)
            b.carve_box(9, 15, iy, iy, -4, 4)

    # Articulated gothic bone ribs (mat_idx = 1, tint_b = 0.90) & dorsal vertebral spine
    for iy in range(5, 22, 3):
        for sx in (-1, 1):
            for ix in range(2, 9):
                px = sx * ix
                pz = 8 if ix <= 5 else 7
                b.set_voxel(px, iy, pz, 1, 1.04, 0.90)
                b.set_voxel(px, iy, pz + 1, 1, 1.06, 0.92)
        # Dorsal vertebral spine & brass reliquary arches on back
        b.fill_box(-1, 1, iy, iy + 1, -9, -8, mat_idx=1, shade_bias=1.04, tint_b=0.90)
        b.set_voxel(0, iy, -9, 3, 1.08, 0.95)

    # Sunken sternum soul-cage with glowing abyssal heart-core (mat_idx = 3)
    for iy in range(10, 18):
        for ix in range(-2, 3):
            b.set_voxel(ix, iy, 7, 3, 1.08, 0.95)
            if abs(ix) == 2 or iy in (10, 14, 17):
                b.set_voxel(ix, iy, 8, 2, 1.04, 0.68)
                b.set_voxel(ix, iy, 9, 1, 1.04, 0.90)
            else:
                b.set_voxel(ix, iy, 8, 3, 1.08, 0.96)
                b.carve_voxel(ix, iy, 9)

    # Cathedral ossuary pauldrons (ix = -18..18) topped with melted ritual candles & void flames
    for sx in (-1, 1):
        for y0, y1, x_in, x_out, z_span in [
            (18, 21, 9, 18, 6),
            (21, 24, 9, 17, 5),
            (24, 26, 10, 16, 4),
        ]:
            xa, xb = sx * x_in, sx * x_out
            b.fill_box(xa, xb, y0, y1, -z_span, z_span, mat_idx=0, shade_bias=0.95, tint_b=0.46)
            b.fill_box(xa, xb, y0, y0, -z_span, z_span, mat_idx=2, shade_bias=1.04, tint_b=0.66)
            b.carve_box(sx * (x_in + 1), sx * (x_out - 2), y0, y0 + 1, -(z_span - 2), z_span - 2)
        # Bone cathedral arches on pauldrons
        for iz in (-3, 0, 3):
            b.fill_box(sx * 11, sx * 17, 22, 26, iz, iz, mat_idx=1, shade_bias=1.04, tint_b=0.90)
            b.set_voxel(sx * 17, 24, iz, 3, 1.08, 0.95)
        # Cluster of melted ritual candles on shoulders
        cx_a = -15 if sx < 0 else 13
        cx_b = -12 if sx < 0 else 11
        b.add_shoulder_candle(cx_a, 25, -1, height=4, wax_mat=1, flame_mat=3)
        b.add_shoulder_candle(cx_b, 26, 2, height=3, wax_mat=1, flame_mat=3)

    # Interlocking 3D iron chains suspending abyssal grimoire & skull-censer at waist
    b.add_3d_chain((-9, 21, 8), (0, 10, 9), mat_idx=2, sag_voxels=1.5)
    b.add_3d_chain((9, 21, 8), (0, 10, 9), mat_idx=2, sag_voxels=1.5)
    b.add_3d_chain((-9, 10, 8), (9, 2, 8), mat_idx=0, sag_voxels=1.6)
    for iy in range(-2, 2):
        add_elliptical_layer(b, iy, 0.174, 0.120, 0.044, mat_idx=2 if iy in (-2, 1) else 0, shade_bias=1.0, tint_b=0.58)
    b.add_3d_buckle(0, 0, 9, half_w=2, half_h=2, frame_mat=2, pin_mat=1)

    # Skull-censer on right hip & abyssal grimoire on left hip
    b.fill_box(10, 12, -5, -1, 2, 5, mat_idx=1, shade_bias=1.04, tint_b=0.92)
    b.set_voxel(12, -3, 3, 3, 1.08, 0.96)
    b.set_voxel(12, -3, 4, 3, 1.08, 0.96)
    b.fill_box(-12, -10, -6, 0, 1, 5, mat_idx=0, shade_bias=0.92, tint_b=0.42)
    b.fill_box(-12, -10, -6, -6, 1, 5, mat_idx=2, shade_bias=1.04, tint_b=0.66)
    b.fill_box(-12, -12, -5, -1, 2, 4, mat_idx=3, shade_bias=1.08, tint_b=0.95)

    # Deeply tattered, perforated ritual vestments (iy = -10..-2) with sawtooth hems & 1x1/2x2 holes
    for iy in range(-10, -2):
        add_elliptical_layer(b, iy, 0.174, 0.120, 0.036, mat_idx=0 if iy % 3 != 0 else 2, shade_bias=0.92, tint_b=0.45)
        for ix in range(-12, 13):
            for iz in range(-9, 10):
                if abs(ix) <= 2 and iy < -4:
                    b.carve_voxel(ix, iy, iz)
                saw = -10 + ((abs(ix * 5 + iz * 3)) % 5)
                if iy < saw:
                    b.carve_voxel(ix, iy, iz)
                elif (ix * 11 + iz * 7 + iy * 5) % 11 == 0:
                    b.carve_voxel(ix, iy, iz)
                    b.carve_voxel(ix + 1, iy, iz)


def build_set3_legs(b: MicroVoxelBuilder) -> None:
    # Set 3 — Abyssal Ossuary Warden / Eldritch Reliquary (LEGS):
    # Ribbed bone-and-obsidian thigh cages & spiked skull-arch knee-cops (iy = -38..0)
    for iy in range(-38, 1):
        t = (iy + 38) / 38.0
        rx = 0.068 + t * 0.022
        ry = 0.072 + t * 0.022
        th = 0.036
        mat = 2 if iy in (-38, -26, -14, -1) else 0
        add_elliptical_layer(b, iy, rx, ry, th, mat_idx=mat, shade_bias=0.95, tint_b=0.48)
        # Bone rib cages every 4 voxel rows
        if iy % 4 == 0 and iy < -3:
            add_elliptical_layer(b, iy, rx + 0.020, ry + 0.020, 0.020, mat_idx=1, shade_bias=1.04, tint_b=0.90)

    # Glowing abyssal rune channels along front & outer thigh (mat_idx = 3)
    for iy in range(-35, -5, 2):
        b.set_voxel(0, iy, 5, 3, 1.08, 0.95)
        b.set_voxel(5, iy, 0, 3, 1.08, 0.95)

    # Spiked skull-arch knee-cops (iy = -25..-15, iz = 5..8)
    for iy in range(-25, -14):
        half_w = 4 if -22 <= iy <= -17 else 3
        for ix in range(-half_w, half_w + 1):
            b.set_voxel(ix, iy, 6, 1 if abs(ix) <= 2 else 2, 1.04, 0.90 if abs(ix) <= 2 else 0.65)
            if -23 <= iy <= -17 and abs(ix) <= 2:
                b.set_voxel(ix, iy, 7, 1, 1.05, 0.92)
    b.set_voxel(-1, -19, 7, 3, 1.08, 0.96)
    b.set_voxel(1, -19, 7, 3, 1.08, 0.96)
    b.set_voxel(0, -16, 7, 3, 1.08, 0.96)

    # Dangling 3D chain links & brass buckles
    b.add_3d_chain((-5, -7, 6), (5, -13, 6), mat_idx=2, sag_voxels=1.5)
    b.add_3d_chain((5, -26, 5), (-5, -32, 5), mat_idx=0, sag_voxels=1.2)
    b.add_3d_buckle(0, -8, 6, half_w=2, half_h=1, frame_mat=2, pin_mat=1)


def build_set3_feet(b: MicroVoxelBuilder) -> None:
    # Set 3 — Abyssal Ossuary Warden / Eldritch Reliquary (FEET):
    # Clawed ossuary greaves & talon sabatons (iy = -10..13)
    for iy in range(-6, 14):
        rx, ry = 0.056, 0.060
        th = 0.036
        mat = 2 if iy in (-5, 1, 7, 13) else 0
        add_elliptical_layer(b, iy, rx, ry, th, mat_idx=mat, shade_bias=0.95, tint_b=0.46)

    # Bone-ivory shin spines (mat_idx = 1, tint_b = 0.92) & abyssal rune inlays (mat_idx = 3)
    for iy in range(-4, 13):
        b.fill_box(-1, 1, iy, iy, 5, 6, mat_idx=1 if iy % 2 == 0 else 2, shade_bias=1.04, tint_b=0.92)
        if iy % 3 == 0:
            b.set_voxel(0, iy, 6, 3, 1.08, 0.96)
            b.set_voxel(-5, iy, 0, 3, 1.08, 0.95)
            b.set_voxel(5, iy, 0, 3, 1.08, 0.95)
    b.add_3d_buckle(0, 7, 6, half_w=2, half_h=1, frame_mat=2, pin_mat=1)

    # Talon sabaton foot body (iy = -9..-4, iz = -5..7)
    for iy in range(-9, -4):
        for iz in range(-5, 8):
            half_w = 4 if iz <= 4 else 3
            for ix in range(-half_w, half_w + 1):
                is_bone = (abs(ix) in (0, 2) and iy == -5)
                mat = 1 if is_bone else (2 if iy == -9 or abs(ix) == half_w else 0)
                b.set_voxel(ix, iy, iz, mat, 1.04 if is_bone else 0.95, 0.92 if is_bone else 0.50)

    # 3 articulated front toe-claws (iz = 5..10) in bone-ivory & brass
    for claw_x in (-3, 0, 3):
        for iz in range(5, 11):
            cy = -6 if iz <= 7 else (-7 if iz <= 9 else -8)
            b.set_voxel(claw_x, cy, iz, 1, 1.06, 0.94)
            b.set_voxel(claw_x, cy - 1, iz, 2 if iz < 9 else 1, 1.02, 0.88)

    # Cleated sole treads at iy = -10
    for iz in range(-5, 9):
        if iz % 2 == 0:
            for ix in range(-4, 5):
                b.set_voxel(ix, -10, iz, 0 if abs(ix) < 4 else 2, 0.84, 0.44)


def export_piece(set_idx: int, slot: str, builder_fn) -> tuple[str, int, int, int]:
    clear_scene()
    mats = make_micro_voxel_materials(set_idx)
    builder = MicroVoxelBuilder(f"Armor_Set{set_idx}_{slot}", voxel_size=VOXEL_SIZE)
    builder_fn(builder)

    if slot == "head":
        builder.enforce_inner_clearance(HEAD_CLEARANCE)
    elif slot == "chest":
        builder.enforce_inner_clearance(CHEST_CLEARANCE)
    elif slot == "legs":
        builder.enforce_inner_clearance(LEGS_CLEARANCE)

    vox_count = len(builder.voxels)
    obj = builder.build_mesh_object(mats)
    tri_count = sum(len(p.vertices) - 2 for p in obj.data.polygons if len(p.vertices) >= 3)

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
    print(f"[Micro-Voxel Armor 2-3] armor_set{set_idx}_{slot}.glb | voxels={vox_count} | tris={tri_count} | mesh_nodes=1 | size={fsize} bytes")
    return out_path, vox_count, tri_count, fsize


def main() -> None:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from blender_sets_1_2_3_7mm import export_sets_1_2_3_7mm
    selected_sets = [2, 3]
    for i, arg in enumerate(sys.argv):
        if arg == "--sets" and i + 1 < len(sys.argv):
            selected_sets = [int(x.strip()) for x in sys.argv[i + 1].split(",") if x.strip().isdigit() and int(x.strip()) in (1, 2, 3)]
        elif arg.startswith("--sets="):
            selected_sets = [int(x.strip()) for x in arg.split("=", 1)[1].split(",") if x.strip().isdigit() and int(x.strip()) in (1, 2, 3)]
    export_sets_1_2_3_7mm(OUTPUT_DIR, tuple(selected_sets))



if __name__ == "__main__":
    main()

