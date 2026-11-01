import bpy
import bmesh
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blender_set0_candle_bearer import Set0MicroVoxelBuilder, VOXEL_SIZE_SET0

VOXEL_SIZE: float = VOXEL_SIZE_SET0


class MicroVoxelBuilder(Set0MicroVoxelBuilder):
    def __init__(self, voxel_size: float = VOXEL_SIZE_SET0) -> None:
        super().__init__("Sets123_VoxelPiece", voxel_size=voxel_size)

    def fill_cylinder_y(
        self,
        cx: int,
        y0: int,
        y1: int,
        cz: int,
        r: float,
        mat_idx: int,
        shade_bias: float = 1.0,
    ) -> None:
        ir = int(math.ceil(r))
        for iy in range(min(y0, y1), max(y0, y1) + 1):
            for dx in range(-ir, ir + 1):
                for dz in range(-ir, ir + 1):
                    if dx * dx + dz * dz <= r * r + 0.25:
                        self.set_voxel(cx + dx, iy, cz + dz, mat_idx, shade_bias)

    def bake_to_blender_object(self, name: str, mats: list) -> bpy.types.Object:
        self.name = name
        return self.build_mesh_object(mats)


def clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def export_glb(obj: bpy.types.Object, out_path: str) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
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
    tri_count = sum(len(p.vertices) - 2 for p in obj.data.polygons if len(p.vertices) >= 3)
    fsize = os.path.getsize(out_path) if os.path.exists(out_path) else 0
    print(f"[Sets 1-3 7mm] {os.path.basename(out_path)} | tris={tri_count} | size={fsize} bytes")


# Bespoke Material Palette for Sets 1, 2, and 3 (0.007m / 7mm micro-voxel pipeline)
SETS_123_MATERIAL_SPECS: list[tuple[str, tuple[float, float, float], float, float, tuple[float, float, float] | None, float]] = [
    # --- SET 1: Winged Fluted Inquisitor Plate ---
    ("Set1_DarkSteel_22252a", (0.133, 0.145, 0.165), 0.88, 0.36, None, 0.0),         # 0: Fluted dark-steel plate
    ("Set1_ForgedIron_383d46", (0.220, 0.239, 0.275), 0.86, 0.34, None, 0.0),        # 1: Raised forged-iron Synod cross & ridges
    ("Set1_Chainmail_181a1d", (0.094, 0.102, 0.114), 0.82, 0.52, None, 0.0),         # 2: Dark chainmail under-layer
    ("Set1_BronzeTrim_8c734b", (0.549, 0.451, 0.294), 0.84, 0.40, None, 0.0),        # 3: Tarnished bronze trim, mounts & bosses
    ("Set1_StrapLeather_2b211a", (0.169, 0.129, 0.102), 0.06, 0.84, None, 0.0),      # 4: Buckled inner leather straps & belt
    ("Set1_EmberVisor_ff5511", (1.000, 0.333, 0.067), 0.05, 0.20, (1.000, 0.333, 0.067), 2.4),  # 5: Glowing ember visor interior
    # --- SET 2: Abyssal Mitre-Helm Warden ---
    ("Set2_MitreIron_262230", (0.149, 0.133, 0.188), 0.86, 0.38, None, 0.0),         # 6: Pointed mitre-helm dark violet-iron
    ("Set2_ObsidianPlate_221f2b", (0.133, 0.122, 0.169), 0.88, 0.35, None, 0.0),     # 7: V-shaped obsidian-iron carapace lames
    ("Set2_SilverViolet_5e5473", (0.369, 0.329, 0.451), 0.85, 0.34, None, 0.0),      # 8: Raised silver-violet trim & spikes
    ("Set2_AbyssShadow_120f18", (0.071, 0.059, 0.094), 0.20, 0.88, None, 0.0),       # 9: Recessed T-visor shadow
    ("Set2_Nocturnite_8822cc", (0.533, 0.133, 0.800), 0.10, 0.22, (0.533, 0.133, 0.800), 1.8),  # 10: Glowing violet Nocturnite veins
    # --- SET 3: Skeletal Cinder-Cage Warden ---
    ("Set3_SkullBone_b8a68e", (0.722, 0.651, 0.557), 0.04, 0.76, None, 0.0),         # 11: Bleached bone skull visage
    ("Set3_RibBone_9c8c74", (0.612, 0.549, 0.455), 0.05, 0.78, None, 0.0),           # 12: Bone sternum, clavicles & finger-bones
    ("Set3_SocketDark_110e0c", (0.067, 0.055, 0.047), 0.05, 0.94, None, 0.0),        # 13: Recessed eye sockets & charred core
    ("Set3_CrownIron_242220", (0.141, 0.133, 0.125), 0.85, 0.44, None, 0.0),         # 14: Jagged iron crown, halo & leg cages
    ("Set3_CageRibIron_2a2624", (0.165, 0.149, 0.141), 0.84, 0.45, None, 0.0),       # 15: Forged-iron anatomical ribcage
    ("Set3_CenserBrass_8c6d3a", (0.549, 0.427, 0.227), 0.82, 0.42, None, 0.0),       # 16: Reliquary censer brass & rivets
    ("Set3_CandleWax_d8c39e", (0.847, 0.765, 0.620), 0.02, 0.66, None, 0.0),         # 17: Burning tallow shoulder candles
    ("Set3_CinderRune_ff6611", (1.000, 0.400, 0.067), 0.00, 0.18, (1.000, 0.400, 0.067), 2.8),  # 18: Glowing orange-gold cinder runes
    ("Set3_CandleFlame_ff8811", (1.000, 0.533, 0.067), 0.00, 0.16, (1.000, 0.533, 0.067), 2.5), # 19: Candle flames & censer ember glow
]


def make_sets_123_materials() -> list[bpy.types.Material]:
    mats: list[bpy.types.Material] = []
    for name, rgb, met, rough, em_rgb, em_str in SETS_123_MATERIAL_SPECS:
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        nt = mat.node_tree
        nodes = nt.nodes
        links = nt.links
        bsdf = nodes.get("Principled BSDF")
        if bsdf is not None:
            vcol = nodes.new(type="ShaderNodeVertexColor")
            vcol.layer_name = "Col"
            links.new(vcol.outputs["Color"], bsdf.inputs["Base Color"])
            bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
            bsdf.inputs["Metallic"].default_value = met
            bsdf.inputs["Roughness"].default_value = rough
            if em_rgb is not None and "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = (em_rgb[0], em_rgb[1], em_rgb[2], 1.0)
                bsdf.inputs["Emission Strength"].default_value = em_str
        mats.append(mat)
    return mats


def _run_boolean_remesh_seed(seed_Or_v, radius: float = 0.095, height_or_mat: float = 0.20) -> None:
    v = seed_Or_v if isinstance(seed_Or_v, Set0MicroVoxelBuilder) else MicroVoxelBuilder(VOXEL_SIZE)
    bm_outer = bmesh.new()
    bmesh.ops.create_uvsphere(bm_outer, u_segments=14, v_segments=10, radius=max(0.03, radius))
    bm_inner = bmesh.new()
    bmesh.ops.create_uvsphere(bm_inner, u_segments=14, v_segments=10, radius=max(0.015, radius - 0.012))
    v.apply_boolean_remesh_volume(bm_outer, bm_inner, mat_idx=0, octree_depth=8)
    bm_outer.free()
    bm_inner.free()
    v.voxels.clear()


# ==============================================================================
# SET 1 — WINGED FLUTED INQUISITOR PLATE (head_1, chest_1, hands_1, legs_1, feet_1)
# ==============================================================================

def build_set1_head_7mm(mats: list) -> bpy.types.Object:
    """
    Set 1 HEAD — Winged Ember-Visor Barbute:
    - Rounded, fluted dark-steel helm (#22252a = 0) with raised central cranial ridge (#383d46 = 1).
    - Recessed vertical visor grill slits (4 narrow vertical bars) with warm glowing ember interior (#ff5511 = 5, emission 2.4).
    - Swept-back feathered dark-iron wings mounted to left/right temples at 35° with stepped 1-voxel feather layering
      and tarnished bronze base mounts (#8c734b = 3).
    """
    v = MicroVoxelBuilder(VOXEL_SIZE)
    _run_boolean_remesh_seed(v, radius=0.098)


    # 1. Rounded Fluted Dark-Steel Barbute Dome & Cheek Plates (iy = -9..26)
    for iy in range(-9, 27):
        if iy < 0:
            rx_in, rz_in = 10.6, 11.0
            rx_out, rz_out = 13.0, 13.4
        elif iy <= 15:
            rx_in, rz_in = 10.5, 11.0
            rx_out, rz_out = 12.8, 13.4
        else:
            u = (iy - 15) / 11.0
            scale_d = math.cos(u * math.pi * 0.46)
            rx_out = max(2.0, 12.8 * scale_d)
            rz_out = max(2.0, 13.4 * scale_d)
            rx_in = max(0.0, rx_out - 2.4) if iy < 24 else 0.0
            rz_in = max(0.0, rz_out - 2.4) if iy < 24 else 0.0

        is_bronze_rim = iy in (-9, -8, 15)
        for ix in range(-15, 16):
            for iz in range(-15, 16):
                d_out = (ix / max(0.5, rx_out)) ** 2 + (iz / max(0.5, rz_out)) ** 2
                d_in = (ix / max(0.5, rx_in)) ** 2 + (iz / max(0.5, rz_in)) ** 2 if rx_in > 0.2 else 99.0
                if d_out <= 1.0 and d_in >= 1.0:
                    # Fluted cranial pleat ridges (+1 voxel on alternating ribs)
                    is_flute = (abs(ix) % 3 == 0) and iy >= 12
                    mat = 3 if is_bronze_rim else (1 if is_flute else 0)
                    v.set_voxel(ix, iy, iz, mat, 1.03 if is_flute else 0.99)

    # Raised central cranial comb/ridge (#383d46 = 1 with #8c734b = 3 crest trim)
    for iy in range(13, 30):
        z_span = int(round(13 - max(0, iy - 18) * 0.9))
        for iz in range(-z_span, z_span + 1):
            is_crest_top = (iy >= 27) or (abs(iz) == z_span)
            v.fill_box(-1, 1, iy, iy, iz, iz, 3 if is_crest_top else 1, 1.06)

    # 2. Recessed Vertical Visor Grill Slits (4 narrow vertical bars) + Glowing Ember Interior (#ff5511 = 5)
    for iy in range(2, 13):
        for ix in range(-7, 8):
            v.carve_box(ix, ix, iy, iy, 11, 15)
            # Glowing ember interior backdrop at iz = 9..10
            v.set_voxel(ix, iy, 10, 5, 1.08)
            v.set_voxel(ix, iy, 9, 5, 1.05)
            # Bronze visor frame around top (iy=12), bottom (iy=2), and sides (|ix|=7)
            if iy in (2, 12) or abs(ix) == 7:
                v.set_voxel(ix, iy, 12, 3, 1.05)
            # 4 Narrow Vertical Grill Bars at ix = -5, -2, +2, +5 (plus central nasal bridge at ix=0, iy>=8)
            elif ix in (-5, -2, 2, 5) or (ix == 0 and iy >= 8):
                v.set_voxel(ix, iy, 12, 1 if ix == 0 else 0, 1.04)

    # 3. Swept-Back Feathered Dark-Iron Wings on Left & Right Temples (angled 35° up & back, bronze mounts #8c734b = 3)
    for sx in (-1, 1):
        # Tarnished bronze temple rosette mount (|ix| = 13..15, iy = 7..12, iz = 2..7)
        v.fill_box(sx * 13, sx * 15, 7, 12, 2, 7, 3, 1.05)
        # 5 Layered Feathered Wing Pinions sweeping back (-iz) & upward (+iy) at 35°
        for f_layer in range(5):
            len_steps = 22 - f_layer * 2
            base_y = 9 + f_layer * 2
            base_z = 5 - f_layer * 1
            for st in range(len_steps):
                wy = int(round(base_y + st * 0.82 - f_layer * 0.4))
                wz = int(round(base_z - st * 0.95))
                wx = sx * (14 + f_layer // 2 + st // 5)
                is_tip = st >= len_steps - 3
                is_edge = (st % 3 == 0) or (f_layer == 0)
                mat_w = 3 if (st <= 2 or is_tip) else (1 if is_edge else 0)
                v.set_voxel(wx, wy, wz, mat_w, 1.05 if is_edge else 0.98)
                v.set_voxel(wx, wy + 1, wz, 0, 0.96)

    v.subtract_inner_mannequin_clearance(
        lambda wx, wy, wz: (-0.08 <= wz <= 0.21) and ((wx / 0.068) ** 2 + (wy / 0.072) ** 2 < 1.0)
    )
    return v.bake_to_blender_object("Set1_WingedEmberBarbute_7mm", mats)


def build_set1_chest_7mm(mats: list) -> bpy.types.Object:
    """
    Set 1 CHEST — Fluted Cross Cuirass & Shingled Pauldrons:
    - V-tapered dark-iron breastplate (#22252a = 0) with vertical gothic fluting (alternating 1-voxel pleats)
      and a bold raised forged-iron Synod cross (#383d46 = 1, #8c734b = 3 trim) on the sternum.
    - High flanged gorget collar framed by a 1-voxel tarnished bronze trim border (#8c734b = 3).
    - Multi-tiered rounded pauldrons of 4 overlapping shingled lames cascading down the upper deltoid
      with raised bronze border rims (#8c734b = 3) and visible dark chainmail (#181a1d = 2) underneath.
    """
    v = MicroVoxelBuilder(VOXEL_SIZE)
    _run_boolean_remesh_seed(v, radius=0.14)

    # 1. V-Tapered Fluted Dark-Iron Cuirass (iy = 0..66, 0.28m waist -> 0.48m shoulders)
    for iy in range(0, 67):
        t = iy / 66.0
        rx_out = 19.8 + (t ** 1.12) * 10.8
        rz_out = 13.0 + math.sin(t * math.pi * 0.78) * 3.4
        rx_in = rx_out - 2.4
        rz_in = rz_out - 2.4
        max_x = int(math.ceil(rx_out + 2))
        max_z = int(math.ceil(rz_out + 2))
        for ix in range(-max_x, max_x + 1):
            for iz in range(-max_z, max_z + 1):
                # Vertical gothic fluting: alternating +1 voxel raised / recessed pleats every 3 voxels
                flute_boost = 0.65 if (abs(ix) % 3 == 0 and iy >= 8) else 0.0
                d_out = (ix / (rx_out + flute_boost)) ** 2 + (iz / (rz_out + flute_boost)) ** 2
                d_in = (ix / rx_in) ** 2 + (iz / rz_in) ** 2
                if d_out <= 1.0 and d_in >= 1.0:
                    is_pleat_ridge = (abs(ix) % 3 == 0) and d_out >= 0.84
                    v.set_voxel(ix, iy, iz, 1 if is_pleat_ridge else 0, 1.04 if is_pleat_ridge else 0.96)

    # Articulated Waist Belt (#2b211a = 4) with Tarnished Bronze Trim & Buckle (#8c734b = 3)
    for iy in range(0, 6):
        v.fill_ring(iy, 18.2, 11.6, 20.8, 14.2, 3 if iy in (0, 5) else 4, 1.02)
    v.add_buckle_3d(0, 3, 15, half_w=4, half_h=3, frame_mat=3, pin_mat=1)

    # 2. Bold Raised Forged-Iron Synod Cross on Sternum (iy = 14..56, ix = -11..+11)
    for iy in range(14, 57):
        t_c = iy / 66.0
        iz_st = int(round(13.0 + math.sin(t_c * math.pi * 0.78) * 3.4)) + 1
        half_stem = 3 if iy in (14, 15, 55, 56) else 2
        for ix in range(-half_stem, half_stem + 1):
            is_rim = abs(ix) == half_stem or iy in (14, 56)
            v.set_voxel(ix, iy, iz_st, 3 if is_rim else 1, 1.06)
            if abs(ix) <= 1:
                v.set_voxel(ix, iy, iz_st + 1, 1, 1.08)
    # Horizontal cross-arms of the Synod Cross (iy = 40..45, ix = -11..+11)
    for iy in range(40, 46):
        iz_bar = 16
        for ix in range(-11, 12):
            z_curve = iz_bar - int((abs(ix) / 11.0) ** 1.5 * 2.0)
            is_rim = iy in (40, 45) or abs(ix) == 11
            v.set_voxel(ix, iy, z_curve, 3 if is_rim else 1, 1.06)
            if 41 <= iy <= 44 and abs(ix) <= 9:
                v.set_voxel(ix, iy, z_curve + 1, 1, 1.08)

    # 3. High Flanged Gorget Collar (iy = 62..74) with 1-Voxel Tarnished Bronze Trim Border (#8c734b = 3)
    for iy in range(62, 75):
        u_g = (iy - 62) / 12.0
        rx_g = 15.0 + u_g * 2.2
        rz_g = 14.2 + u_g * 1.8
        is_trim = iy in (62, 68, 73, 74)
        v.fill_ring(iy, rx_g - 2.4, rz_g - 2.4, rx_g, rz_g, 3 if is_trim else 0, 1.04 if is_trim else 0.98)

    # 4. Multi-Tiered Rounded Pauldrons (4 Overlapping Shingled Lames + Visible Dark Chainmail #181a1d = 2 Underneath)
    for side in (-1, 1):
        # Dark chainmail under-layer (#181a1d = 2) hanging beneath the lowest pauldron lame (iy = 30..42)
        for iy in range(30, 43):
            jag = (iy + 30) % 2
            v.fill_ring(
                iy, 4.5, 8.5, 7.5 + jag * 0.4, 13.5, 2, 0.90,
                cx=side * 27.5, cz=0.0, ix_min=side * 27 if side > 0 else -36, ix_max=36 if side > 0 else side * 27
            )
        # 4 Overlapping Shingled Pauldron Lames cascading from iy = 68 down to iy = 38 (spanning 0.48m shoulder width!)
        lame_ranges = [(59, 68, 25.0, 8.8), (52, 60, 26.5, 9.2), (45, 53, 27.8, 9.4), (38, 46, 28.8, 9.0)]
        for l_idx, (y0, y1, cx_off, r_lame) in enumerate(lame_ranges):
            for iy in range(y0, y1 + 1):
                is_bronze_border = (iy == y0) or (iy == y0 + 1) or (l_idx == 0 and iy == y1)
                mat_p = 3 if is_bronze_border else 0
                v.fill_ring(
                    iy, max(2.0, r_lame - 2.5), 10.5, r_lame, 15.2 - l_idx * 0.4, mat_p,
                    1.06 if is_bronze_border else 1.00,
                    cx=side * cx_off, cz=0.0,
                    ix_min=side * 16 if side > 0 else -38,
                    ix_max=38 if side > 0 else side * 16,
                )

    v.subtract_inner_mannequin_clearance(
        lambda wx, wy, wz: (-0.03 <= wz <= 0.52) and ((wx / 0.118) ** 2 + (wy / 0.075) ** 2 < 1.0)
    )

    return v.bake_to_blender_object("Set1_FlutedInquisitorChest_7mm", mats)


def build_set1_hands_7mm(mats: list) -> bpy.types.Object:
    """
    Set 1 HANDS: Articulated Plate Gauntlets (origin at Y = 1.05m).
    - Tapered dark-iron vambraces (#22252a = 0) with flared elbow cops
    - 1-voxel bronze cuff trim (#8c734b = 3)
    - Buckled inner leather straps (#2b211a = 4)
    - Articulated finger lames (#383d46 = 1 / #22252a = 0)
    """
    _run_boolean_remesh_seed("Set1_Hands_Seed", 0.036, 0.24)
    v = MicroVoxelBuilder(VOXEL_SIZE)

    for side in (-1, 1):
        ax = side * 31
        # 1. Tapered dark-iron vambraces (iy = -8..26 -> Y = 0.99m..1.23m) + Flared Elbow Cops (iy = 24..32)
        for iy in range(-8, 33):
            u = max(0.0, min(1.0, (iy + 8) / 34.0))
            flare = 1.8 if iy >= 25 else 0.0
            rx = 5.2 + u * 2.2 + flare
            rz = 5.2 + u * 2.2 + flare
            is_cuff_trim = iy in (-8, -7, 10, 24, 32)
            for ix in range(int(ax - rx - 1), int(ax + rx + 2)):
                # Only outer side for elbow cop above iy=26
                if iy > 26 and side * (ix - ax) < 0:
                    continue
                for iz in range(int(-rz - 1), int(rz + 2)):
                    d = math.sqrt(((ix - ax) / rx) ** 2 + (iz / rz) ** 2)
                    if 0.60 <= d <= 1.0:
                        # Buckled inner leather straps (#2b211a = 4) at iy in (-1, 0, 14, 15) on inner wrist
                        if iy in (-1, 0, 14, 15) and side * (ix - ax) < 0:
                            v.set_voxel(ix, iy, iz, 3 if abs(iz) <= 1 else 4, 1.04)
                        elif is_cuff_trim:
                            v.set_voxel(ix, iy, iz, 3, 1.06)
                        else:
                            # Vertical flute ridges on outer forearm
                            is_flute = (iz in (-3, 0, 3)) and (side * (ix - ax) > 1.5)
                            v.set_voxel(ix, iy, iz, 1 if is_flute else 0, 1.03 if is_flute else 0.98)

        # 2. Articulated Finger Lames & Gauntlet Mitons (iy = -21..-9)
        for iy in range(-21, -8):
            is_knuckle_lame = (iy % 3 == 0)
            for ix in range(ax - 5, ax + 6):
                for iz in range(-5, 6):
                    # 4 articulated finger columns below iy = -14
                    if iy < -14 and (iz % 2 == 0):
                        continue
                    d = math.sqrt(((ix - ax) / 4.8) ** 2 + (iz / 4.8) ** 2)
                    if 0.45 <= d <= 1.0:
                        v.set_voxel(ix, iy, iz, 1 if is_knuckle_lame else 0, 1.04 if is_knuckle_lame else 0.96)

    v.subtract_inner_mannequin_clearance(
        lambda wx, wy, wz: (
            (-0.06 <= wz <= 0.19)
            and (
                ((wx - 0.217) / 0.025) ** 2 + (wy / 0.025) ** 2 < 1.0
                or ((wx + 0.217) / 0.025) ** 2 + (wy / 0.025) ** 2 < 1.0
            )
        )
    )
    return v.bake_to_blender_object("Set1_ArticulatedGauntlets_7mm", mats)


def build_set1_legs_7mm(mats: list) -> bpy.types.Object:
    """
    Set 1 LEGS: Shingled Tassets, Chainmail Hauberk Skirt & Fluted Greaves (single-side at X=±0.125m, Y=0.88m).
    - Articulated waist belt supporting 4-lame shingled hip/thigh tassets with bronze edge trim (#8c734b = 3)
    - Triangular V-hang of dark micro-voxel chainmail (#181a1d = 2) between the upper thighs
    - Distinct fluted thigh cuisses and shin greaves (#22252a = 0 / #383d46 = 1)
    - Rounded knee cops (poleyns) with raised bronze side bosses and trim rings (#8c734b = 3)
    """
    _run_boolean_remesh_seed("Set1_Legs_Seed", 0.068, 0.72)
    v = MicroVoxelBuilder(VOXEL_SIZE)

    # 1. Triangular V-hang of dark micro-voxel chainmail (#181a1d = 2) on inner thigh side (ix < 0)
    for iy in range(-18, 9):
        u_v = (iy + 18) / 26.0
        max_inward = int(3 + u_v * 8)
        for ix in range(-max_inward - 6, -4):
            for iz in range(6, 12):
                if (ix + iy + iz) % 2 == 0 or iy > -10:
                    v.set_voxel(ix, iy, iz, 2, 0.90)

    # 2. 4-Lame Shingled Hip/Thigh Tassets cascading over upper/outer thigh (iy = -26..10)
    tasset_lames = [(2, 10, 12.2), (-7, 3, 12.8), (-16, -6, 13.2), (-25, -15, 13.0)]
    for l_idx, (y0, y1, r_tas) in enumerate(tasset_lames):
        for iy in range(y0, y1 + 1):
            is_trim = (iy == y0) or (iy == y0 + 1) or (l_idx == 0 and iy >= y1 - 1)
            mat_t = 3 if is_trim else 0
            # Outer & front/back hip tasset shield
            v.fill_ring(
                iy, r_tas - 2.2, r_tas - 2.2, r_tas, r_tas,
                mat_t, 1.06 if is_trim else 1.00,
                ix_min=-5, ix_max=16
            )

    # 3. Distinct Fluted Thigh Cuisse, Rounded Knee Cop (Poleyn), and Fluted Shin Greave (iy = -98..8)
    for iy in range(-98, 9):
        u = (iy + 98) / 106.0
        # Anatomical taper: ankle (6.5) -> calf (9.0) -> knee cop (10.5) -> thigh (10.8)
        is_poleyn = -52 <= iy <= -38
        knee_flare = 1.6 * math.cos(((iy + 45) / 7.0) * (math.pi * 0.5)) if is_poleyn else 0.0
        r_leg = 6.6 + u * 3.8 + max(0.0, knee_flare)
        is_bronze_ring = iy in (-98, -97, -52, -38, 7, 8)

        for ix in range(int(-r_leg - 2), int(r_leg + 3)):
            for iz in range(int(-r_leg - 2), int(r_leg + 3)):
                d = math.sqrt((ix / r_leg) ** 2 + (iz / r_leg) ** 2)
                if 0.66 <= d <= 1.0:
                    if is_bronze_ring:
                        v.set_voxel(ix, iy, iz, 3, 1.06)
                    elif is_poleyn and iz > 3:
                        # Raised central knee ridge & bronze trim
                        v.set_voxel(ix, iy, iz, 3 if abs(ix) == 4 else 1, 1.05)
                    else:
                        # Vertical gothic fluting pleats (every 3 voxels in X on front/back)
                        is_flute = (abs(ix) in (0, 3, 6)) and (abs(iz) > 3)
                        v.set_voxel(ix, iy, iz, 1 if is_flute else 0, 1.03 if is_flute else 0.97)

        # Raised bronze side bosses on knee poleyn (iy = -47..-43)
        if -47 <= iy <= -43:
            for bx in (int(r_leg), int(r_leg) + 1):
                for bz in (-2, -1, 0, 1, 2):
                    v.set_voxel(bx, iy, bz, 3, 1.08)

    v.subtract_inner_mannequin_clearance(
        lambda wx, wy, wz: (-0.70 <= wz <= 0.07) and ((wx / 0.044) ** 2 + (wy / 0.044) ** 2 < 1.0)
    )
    return v.bake_to_blender_object("Set1_FlutedInquisitorGreave_7mm", mats)


def build_set1_feet_7mm(mats: list) -> bpy.types.Object:
    """
    Set 1 FEET: Laminated Iron Sabatons (single-side at X=±0.125m, Y=0.18m).
    - Grounded dark-iron sabatons (#22252a = 0)
    - Overlapping forward-stepping foot lames (#383d46 = 1) with bronze heel/toe trim (#8c734b = 3)
    """
    _run_boolean_remesh_seed("Set1_Feet_Seed", 0.055, 0.20)
    v = MicroVoxelBuilder(VOXEL_SIZE)

    # 1. Ankle Greave Cuff (iy = -10..8)
    for iy in range(-10, 9):
        r_ank = 6.8 + max(0, iy) * 0.12
        is_trim = iy in (-10, 0, 7, 8)
        v.fill_ring(iy, r_ank - 2.2, r_ank - 2.2, r_ank, r_ank, 3 if is_trim else 0, 1.05 if is_trim else 0.98)

    # 2. Grounded Sabaton Sole + Overlapping Forward-Stepping Foot Lames (iy = -25..-9, iz = -8..20)
    for iy in range(-25, -8):
        u_h = (iy + 25) / 17.0
        for iz in range(-8, 21):
            u_len = (iz + 8) / 28.0
            # Tapered gothic sabaton toe point
            toe_taper = max(0.25, 1.0 - max(0.0, (u_len - 0.65) * 1.9))
            max_h = -9 - int(max(0.0, u_len - 0.30) * 11.0)
            if iy > max_h:
                continue
            half_w = int((6.8 - u_h * 1.2) * toe_taper)
            for ix in range(-half_w, half_w + 1):
                is_outer = (abs(ix) >= half_w - 1) or (iz <= -7) or (iz >= 19) or (iy >= max_h - 1) or (iy <= -24)
                if not is_outer:
                    continue
                if iy <= -23:
                    # Bronze heel/toe trim at base rim
                    is_heel_toe = (iz <= -5) or (iz >= 14)
                    v.set_voxel(ix, iy, iz, 3 if is_heel_toe else 0, 1.04 if is_heel_toe else 0.88)
                else:
                    # Overlapping forward-stepping foot lames every 4 voxels along iz
                    is_lame_ridge = (iz % 4 == 0) or (ix == 0)
                    is_bronze_rivet = (iz % 4 == 0) and (abs(ix) == max(1, half_w - 1))
                    mat_s = 3 if is_bronze_rivet else (1 if is_lame_ridge else 0)
                    v.set_voxel(ix, iy, iz, mat_s, 1.06 if is_lame_ridge else 0.98)

    v.subtract_inner_mannequin_clearance(
        lambda wx, wy, wz: (-0.12 <= wz <= 0.06) and ((wx / 0.032) ** 2 + (wy / 0.032) ** 2 < 1.0)
    )
    return v.bake_to_blender_object("Set1_LaminatedSabaton_7mm", mats)


# ==============================================================================
# SET 2: ABYSSAL MITRE-HELM WARDEN (7mm Micro-Voxel Resolution)
# Materials: 6=set2_mitre_obsidian_262230, 7=set2_carapace_plate_221f2b,
#            8=set2_silver_violet_5e5473, 9=set2_visor_abyss_120f18,
#            10=set2_nocturnite_vein_8822cc (emission 1.8)
# ==============================================================================
def build_set2_head_7mm(mats: list) -> bpy.types.Object:
    """
    Set 2 HEAD: Tall Ocular Mitre-Helm (origin at Y = 1.54m).
    - Pointed bishop/inquisitor mitre-helm (#262230 = 6)
    - Recessed T-visor faceguard (#120f18 = 9)
    - Raised silver-violet trim borders (#5e5473 = 8)
    - Etched all-seeing ocular sigil on the brow (#8822cc = 10, emission 1.8)
    """
    _run_boolean_remesh_seed("Set2_Head_Seed", 0.125, 0.38)
    v = MicroVoxelBuilder(VOXEL_SIZE)

    # 1. Tall Pointed Bishop/Inquisitor Mitre-Helm Shell (iy = -14..44 -> 40cm tall sovereign spire)
    for iy in range(-14, 45):
        if iy < 12:
            # Lower helm & faceguard dome
            u_low = (iy + 14) / 26.0
            rx = 15.5 + math.sin(u_low * math.pi) * 2.0
            rz = 16.5 + math.sin(u_low * math.pi) * 1.8
        else:
            # Tall pointed cleft mitre crown tapering cleanly to an apex at iy = 44
            u_spire = (iy - 12) / 32.0
            rx = max(2.2, 16.5 * (1.0 - u_spire * 0.86))
            rz = max(3.5, 17.5 * (1.0 - u_spire * 0.78))

        for ix in range(int(-rx - 2), int(rx + 3)):
            for iz in range(int(-rz - 2), int(rz + 3)):
                # Side cleft notch near the top of the mitre (classic twin-horned/cleft bishop mitre silhouette)
                if iy > 26 and abs(iz) <= int((iy - 26) * 0.35):
                    continue
                d = math.sqrt((ix / rx) ** 2 + (iz / rz) ** 2)
                if 0.72 <= d <= 1.0:
                    # Recessed T-Visor Faceguard on front (iz > 6, -10 <= iy <= 6)
                    in_t_horiz = (3 <= iy <= 6) and (abs(ix) <= 9) and (iz > 6)
                    in_t_vert = (-10 <= iy <= 3) and (abs(ix) <= 2) and (iz > 6)
                    if in_t_horiz or in_t_vert:
                        if d <= 0.85:
                            # Glowing Nocturnite ocular slit inside T-visor crossbar
                            is_eye_glow = (iy == 5) and (abs(ix) in (4, 5, 6))
                            v.set_voxel(ix, iy, iz, 10 if is_eye_glow else 9, 1.15 if is_eye_glow else 0.72)
                        continue

                    # Raised silver-violet trim borders (#5e5473 = 8) along mitre edges, central spine, and T-visor rim
                    is_trim = (
                        (abs(ix) >= rx - 1.5 and iy > 10)
                        or (abs(ix) <= 1 and iy > 18 and iz > 0)
                        or (iy in (-14, -13, 11, 12))
                        or (iz > 8 and ((iy in (2, 7) and abs(ix) <= 10) or (-10 <= iy <= 2 and abs(ix) == 3)))
                    )
                    v.set_voxel(ix, iy, iz, 8 if is_trim else 6, 1.06 if is_trim else 0.98)

    # 2. Etched All-Seeing Ocular Sigil on the Brow (iy = 13..23, iz = 15..18)
    for iy in range(13, 24):
        dy = iy - 18
        # Diamond/almond eye contour + central glowing pupil (#8822cc = 10)
        eye_half_w = max(0, 7 - int(abs(dy) * 1.4))
        for ix in range(-eye_half_w - 1, eye_half_w + 2):
            iz_brow = 16 - int(abs(ix) * 0.12)
            is_eye_ring = (abs(ix) == eye_half_w) or (abs(dy) == 4 and abs(ix) <= 2)
            is_pupil = (abs(ix) <= 1 and abs(dy) <= 2)
            if is_pupil or is_eye_ring:
                v.set_voxel(ix, iy, iz_brow, 10, 1.18)
            elif abs(ix) < eye_half_w:
                v.set_voxel(ix, iy, iz_brow - 1, 9, 0.80)

    v.subtract_inner_mannequin_clearance(
        lambda wx, wy, wz: (wz < 0.16) and ((wx / 0.088) ** 2 + (wy / 0.095) ** 2 + ((wz - 0.02) / 0.12) ** 2 < 1.0)
    )
    return v.bake_to_blender_object("Set2_AbyssalMitreHelm_7mm", mats)


def build_set2_chest_7mm(mats: list) -> bpy.types.Object:
    """
    Set 2 CHEST: Heavy Layered Carapace Cuirass (origin at Y = 0.96m).
    - Overlapping V-shaped dark obsidian-iron chest lames (#221f2b = 7 / #262230 = 6)
    - Heavy ridged pauldrons with silver-violet trim (#5e5473 = 8)
    - Recessed violet Nocturnite veins (#8822cc = 10, emission 1.8)
    """
    _run_boolean_remesh_seed("Set2_Chest_Seed", 0.21, 0.56)
    v = MicroVoxelBuilder(VOXEL_SIZE)

    # 1. Heroic V-Tapered Carapace Torso (0.28m waist -> 0.48m shoulders) with V-shaped overlapping lames
    for iy in range(-6, 68):
        u = (iy + 6) / 74.0
        rx = 20.0 + (u ** 1.15) * 9.0
        rz = 14.0 + math.sin(u * math.pi * 0.85) * 4.8

        for ix in range(int(-rx - 2), int(rx + 3)):
            for iz in range(int(-rz - 2), int(rz + 3)):
                d = math.sqrt((ix / rx) ** 2 + (iz / rz) ** 2)
                if 0.72 <= d <= 1.0:
                    # V-shaped chevron lame index
                    v_coord = iy - int(abs(ix) * 0.45)
                    is_lame_border = (v_coord % 9 == 0)
                    # Recessed violet Nocturnite veins (#8822cc = 10) pulsing along chevron channels & central core
                    is_nocturnite_vein = (
                        ((v_coord % 9 == 4) and (4 <= abs(ix) <= 15) and (iz > 6))
                        or (abs(ix) == 1 and 12 <= iy <= 54 and iz > 8 and (iy % 3 != 0))
                    )
                    if is_nocturnite_vein:
                        v.set_voxel(ix, iy, iz, 10, 1.15)
                    elif is_lame_border or iy in (-6, -5, 66, 67):
                        v.set_voxel(ix, iy, iz, 8, 1.06)
                    else:
                        v.set_voxel(ix, iy, iz, 7 if (v_coord // 9) % 2 == 0 else 6, 0.98)

    # 2. Heavy Ridged Carapace Pauldrons (spanning 0.48m heroic shoulder width, iy = 38..72)
    for side in (-1, 1):
        for l_idx, (y0, y1, cx_off, r_p) in enumerate([(58, 72, 25.5, 9.5), (48, 60, 27.2, 9.8), (38, 50, 28.8, 9.2)]):
            for iy in range(y0, y1 + 1):
                is_trim = (iy == y0) or (iy == y1)
                is_vein = (iy == (y0 + y1) // 2)
                mat_p = 10 if is_vein else (8 if is_trim else 7)
                v.fill_ring(
                    iy, max(2.0, r_p - 2.6), 10.8, r_p, 15.6 - l_idx * 0.4, mat_p,
                    1.12 if is_vein else (1.06 if is_trim else 0.98),
                    cx=side * cx_off, cz=0.0,
                    ix_min=side * 16 if side > 0 else -39,
                    ix_max=39 if side > 0 else side * 16,
                )

    v.subtract_inner_mannequin_clearance(
        lambda wx, wy, wz: (-0.03 <= wz <= 0.52) and ((wx / 0.118) ** 2 + (wy / 0.075) ** 2 < 1.0)
    )
    return v.bake_to_blender_object("Set2_AbyssalCarapaceChest_7mm", mats)


def build_set2_hands_7mm(mats: list) -> bpy.types.Object:
    """
    Set 2 HANDS: Spiked Vambraces (origin at Y = 1.05m).
    - Heavy dark-plate gauntlets (#221f2b = 7) with silver-violet trim (#5e5473 = 8)
    - 3 outward-jutting iron forearm spikes per arm (#5e5473 = 8)
    - Violet Nocturnite rune recesses (#8822cc = 10)
    """
    _run_boolean_remesh_seed("Set2_Hands_Seed", 0.038, 0.24)
    v = MicroVoxelBuilder(VOXEL_SIZE)

    for side in (-1, 1):
        ax = side * 31
        for iy in range(-20, 30):
            u = max(0.0, min(1.0, (iy + 8) / 36.0))
            rx = 5.0 + u * 2.5
            rz = 5.0 + u * 2.5
            is_trim = iy in (-20, -9, 0, 12, 28, 29)
            for ix in range(int(ax - rx - 1), int(ax + rx + 2)):
                for iz in range(int(-rz - 1), int(rz + 2)):
                    d = math.sqrt(((ix - ax) / rx) ** 2 + (iz / rz) ** 2)
                    if 0.58 <= d <= 1.0:
                        is_rune = (iy in (4, 5, 16, 17)) and (abs(iz) <= 1) and (side * (ix - ax) > 2.0)
                        v.set_voxel(ix, iy, iz, 10 if is_rune else (8 if is_trim else 7), 1.15 if is_rune else 0.98)

        # 3 Outward-Jutting Iron Forearm Spikes (#5e5473 = 8) at iy = 2, 11, 20
        for sp_y in (2, 11, 20):
            for s_len in range(1, 7):
                sx = ax + side * (6 + s_len)
                sy = sp_y + (s_len // 2)
                half_t = max(0, 2 - s_len // 3)
                for dy in range(-half_t, half_t + 1):
                    for dz in range(-half_t, half_t + 1):
                        v.set_voxel(sx, sy + dy, dz, 8, 1.08)

    v.subtract_inner_mannequin_clearance(
        lambda wx, wy, wz: (
            (-0.06 <= wz <= 0.19)
            and (
                ((wx - 0.217) / 0.025) ** 2 + (wy / 0.025) ** 2 < 1.0
                or ((wx + 0.217) / 0.025) ** 2 + (wy / 0.025) ** 2 < 1.0
            )
        )
    )
    return v.bake_to_blender_object("Set2_SpikedVambraces_7mm", mats)


def build_set2_legs_7mm(mats: list) -> bpy.types.Object:
    """
    Set 2 LEGS: Layered Plate Skirt & Heavy Articulated Greaves (single-side at X=±0.125m, Y=0.88m).
    - Sweeping V-plated fauld/tasset skirts (#262230 = 6 / #221f2b = 7) with silver-violet trim (#5e5473 = 8)
    - Thick articulated greaves with Nocturnite knee runes (#8822cc = 10)
    """
    _run_boolean_remesh_seed("Set2_Legs_Seed", 0.070, 0.72)
    v = MicroVoxelBuilder(VOXEL_SIZE)

    # 1. Sweeping V-plated Fauld/Tasset Skirt (iy = -34..10)
    for iy in range(-34, 11):
        u_sk = (10 - iy) / 44.0
        r_sk = 11.8 + u_sk * 2.8
        v_chevron = (iy - int(u_sk * 6)) % 8
        is_trim = (v_chevron == 0) or (iy <= -33) or (iy >= 9)
        is_vein = (v_chevron == 4) and (iy > -26)
        mat_sk = 10 if is_vein else (8 if is_trim else 6)
        v.fill_ring(iy, r_sk - 2.2, r_sk - 2.2, r_sk, r_sk, mat_sk, 1.12 if is_vein else 1.00, ix_min=-3, ix_max=17)

    # 2. Thick Articulated Greaves (iy = -98..8)
    for iy in range(-98, 9):
        u = (iy + 98) / 106.0
        knee_flare = 1.8 if -52 <= iy <= -38 else 0.0
        r_leg = 6.8 + u * 3.8 + knee_flare
        is_trim = (iy % 14 == 0) or (iy in (-98, -52, -38))
        is_knee_rune = (-47 <= iy <= -43)
        for ix in range(int(-r_leg - 2), int(r_leg + 3)):
            for iz in range(int(-r_leg - 2), int(r_leg + 3)):
                d = math.sqrt((ix / r_leg) ** 2 + (iz / r_leg) ** 2)
                if 0.66 <= d <= 1.0:
                    if is_knee_rune and abs(ix) <= 2 and iz > 4:
                        v.set_voxel(ix, iy, iz, 10, 1.16)
                    else:
                        v.set_voxel(ix, iy, iz, 8 if is_trim else 7, 1.05 if is_trim else 0.98)

    v.subtract_inner_mannequin_clearance(
        lambda wx, wy, wz: (-0.70 <= wz <= 0.07) and ((wx / 0.044) ** 2 + (wy / 0.044) ** 2 < 1.0)
    )
    return v.bake_to_blender_object("Set2_AbyssalPlateGreave_7mm", mats)


def build_set2_feet_7mm(mats: list) -> bpy.types.Object:
    """
    Set 2 FEET: Broad-Toed Heavy Sabatons (single-side at X=±0.125m, Y=0.18m).
    """
    _run_boolean_remesh_seed("Set2_Feet_Seed", 0.056, 0.20)
    v = MicroVoxelBuilder(VOXEL_SIZE)

    for iy in range(-10, 9):
        r_ank = 7.0 + max(0, iy) * 0.12
        v.fill_ring(iy, r_ank - 2.2, r_ank - 2.2, r_ank, r_ank, 8 if iy in (-10, 0, 8) else 7, 1.02)

    for iy in range(-25, -8):
        for iz in range(-8, 20):
            u_len = (iz + 8) / 27.0
            max_h = -9 - int(max(0.0, u_len - 0.32) * 10.5)
            if iy > max_h:
                continue
            # Broad-toed dreadnought sabaton silhouette
            half_w = 7 if u_len < 0.75 else 6
            for ix in range(-half_w, half_w + 1):
                is_outer = (abs(ix) >= half_w - 1) or (iz <= -7) or (iz >= 18) or (iy >= max_h - 1) or (iy <= -24)
                if not is_outer:
                    continue
                is_trim = (iz % 5 == 0) or (iy <= -23)
                is_vein = (ix == 0 and -2 <= iz <= 12 and iy == max_h)
                v.set_voxel(ix, iy, iz, 10 if is_vein else (8 if is_trim else 7), 1.12 if is_vein else 0.98)

    v.subtract_inner_mannequin_clearance(
        lambda wx, wy, wz: (-0.12 <= wz <= 0.06) and ((wx / 0.032) ** 2 + (wy / 0.032) ** 2 < 1.0)
    )
    return v.bake_to_blender_object("Set2_HeavySabaton_7mm", mats)



# ==============================================================================
# SET 3: SKELETAL CINDER-CAGE WARDEN (7mm Micro-Voxel Resolution)
# Materials: 11=set3_ossuary_skull_b8a68e, 12=set3_sternum_bone_9c8c74,
#            13=set3_charred_core_110e0c, 14=set3_iron_crown_242220,
#            15=set3_iron_rib_2a2624, 16=set3_cinder_rune_ff6611 (emission 2.8),
#            17=set3_censer_ember_ff7722 (emission 2.5),
#            18=set3_tallow_wax_d8c39e, 19=set3_candle_flame_ff8811 (emission 2.5)
# ==============================================================================
def build_set3_head_7mm(mats: list) -> bpy.types.Object:
    """
    Set 3 HEAD: Crowned Ossuary Skull & Iron Halo (origin at Y = 1.54m).
    - Sculpted micro-voxel bleached bone skull visage (#b8a68e = 11)
    - Dark recessed eye sockets and nasal cavity (#110e0c = 13)
    - Jagged dark-iron crown (#242220 = 14)
    - Spiked iron halo ring mounted behind the cranium (#242220 = 14 / #2a2624 = 15)
    """
    _run_boolean_remesh_seed("Set3_Head_Seed", 0.125, 0.34)
    v = MicroVoxelBuilder(VOXEL_SIZE)

    # 1. Sculpted Bleached Bone Skull Visage & Cranium (#b8a68e = 11 / #9c8c74 = 12) (iy = -13..18)
    for iy in range(-13, 19):
        u_sk = (iy + 13) / 31.0
        # Narrower jaw (-13..-4), prominent cheekbones (-3..4), rounded cranium (5..18)
        if iy < -4:
            rx, rz = 11.2, 13.5
        elif iy <= 4:
            rx, rz = 14.8, 15.8
        else:
            dome = math.cos(max(0.0, (iy - 5) / 14.0) * (math.pi * 0.46))
            rx, rz = 15.2 * dome, 16.2 * dome

        for ix in range(int(-rx - 2), int(rx + 3)):
            for iz in range(int(-rz - 2), int(rz + 3)):
                d = math.sqrt((ix / max(1.0, rx)) ** 2 + (iz / max(1.0, rz)) ** 2)
                if 0.68 <= d <= 1.0:
                    # Front skull facial anatomy (iz > 6)
                    if iz > 6:
                        # Dark recessed eye sockets (#110e0c = 13) with tiny cinder pinpoint at iy=1..5, |ix|=3..7
                        in_eye = (0 <= iy <= 5) and (3 <= abs(ix) <= 7)
                        # Inverted triangular nasal cavity (#110e0c = 13) at iy=-4..0, |ix|<=2
                        in_nose = (-4 <= iy <= 0) and (abs(ix) <= (1 if iy >= -1 else 2))
                        if in_eye or in_nose:
                            if d <= 0.84:
                                is_cinder_pupil = in_eye and (iy == 2) and (abs(ix) == 5)
                                v.set_voxel(ix, iy, iz, 16 if is_cinder_pupil else 13, 1.20 if is_cinder_pupil else 0.68)
                            continue
                        # Sculpted vertical skull teeth & jaw striations (-12 <= iy <= -6, |ix| <= 7)
                        if -12 <= iy <= -6 and abs(ix) <= 7:
                            is_tooth_gap = (ix % 2 == 0) or (iy == -9)
                            v.set_voxel(ix, iy, iz, 13 if is_tooth_gap else 11, 0.78 if is_tooth_gap else 1.08)
                            continue
                        # Prominent brow ridge & zygomatic cheekbones
                        if iy in (6, 7) or (iy in (-2, -1) and 6 <= abs(ix) <= 11):
                            v.set_voxel(ix, iy, iz + 1, 11, 1.08)

                    v.set_voxel(ix, iy, iz, 11 if iz > 0 else 12, 1.02 if iz > 4 else 0.94)

    # 2. Jagged Dark-Iron Crown (#242220 = 14) encircling the brow (iy = 8..25)
    for ix in range(-17, 18):
        for iz in range(-18, 19):
            angle = math.atan2(ix, iz)
            r_cr = math.sqrt((ix / 15.6) ** 2 + (iz / 16.6) ** 2)
            if 0.88 <= r_cr <= 1.05:
                # 10 jagged crown spikes around circumference
                spike_wave = max(0.0, math.cos(angle * 5.0))
                max_crown_y = 14 + int(spike_wave * 11.0)
                for iy in range(8, max_crown_y + 1):
                    is_rim = (iy in (8, 9)) or (iy >= max_crown_y - 1)
                    v.set_voxel(ix, iy, iz, 15 if is_rim else 14, 1.06 if is_rim else 0.96)

    # 3. Spiked Iron Halo Ring Mounted Behind the Cranium (cz = -13.. -10, radius = 24..28 voxels, cy = 12)
    halo_cy = 12
    for ix in range(-36, 37):
        for iy in range(halo_cy - 36, halo_cy + 37):
            dy = iy - halo_cy
            r_h = math.sqrt(ix * ix + dy * dy)
            angle_h = math.atan2(dy, ix)
            # Circular iron halo band (r = 22.5..26.0)
            if 22.5 <= r_h <= 26.0 and dy >= -14:
                for iz in range(-13, -9):
                    is_rune = (23.8 <= r_h <= 24.8) and (int((angle_h + math.pi) * 12.0) % 2 == 0) and (iz == -10)
                    v.set_voxel(ix, iy, iz, 16 if is_rune else 14, 1.18 if is_rune else 1.02)
            # 12 Radial Iron Halo Spikes projecting outward (r = 26.0..34.5)
            elif 26.0 < r_h <= 34.5 and dy >= -12:
                # Check alignment with 12 radial spokes (every 30 degrees)
                spoke_mod = abs(((angle_h * 180.0 / math.pi) % 30.0) - 15.0)
                taper = (34.5 - r_h) / 8.5
                if spoke_mod <= 2.5 + taper * 4.5:
                    for iz in (-12, -11):
                        v.set_voxel(ix, iy, iz, 15 if r_h > 31.0 else 14, 1.08)

    # Halo support struts connecting back of skull to halo ring
    for side in (-1, 1):
        for t in range(12):
            v.fill_box(side * (8 + t), side * (9 + t), 4 + t // 2, 6 + t // 2, -13, -10, 14, 0.95)

    v.subtract_inner_mannequin_clearance(
        lambda wx, wy, wz: (wz < 0.14) and ((wx / 0.088) ** 2 + (wy / 0.095) ** 2 + ((wz - 0.02) / 0.11) ** 2 < 1.0)
    )
    return v.bake_to_blender_object("Set3_CrownedOssuarySkull_7mm", mats)


def build_set3_chest_7mm(mats: list) -> bpy.types.Object:
    """
    Set 3 CHEST: Skeletal Iron Ribcage, Glowing Cinder Runes & Hanging Censers (origin at Y = 0.96m).
    - Exposed anatomical ribcage armor (#2a2624 = 15 iron ribs / #9c8c74 = 12 bone sternum & clavicles)
    - Dark charred core (#110e0c = 13) etched with vertical glowing orange-gold cinder runes (#ff6611 = 16, emission 2.8) down the sternum
    - Broad dark-iron cage pauldrons (#242220 = 14) topped with clusters of 3 burning tallow candles (#d8c39e = 18 wax, #ff8811 = 19 flames) on both shoulders
    - Long wrought-iron link chains hanging from outer pauldrons suspending glowing reliquary censers (#ff7722 = 17 inner ember glow) at hip height
    """
    _run_boolean_remesh_seed("Set3_Chest_Seed", 0.21, 0.56)
    v = MicroVoxelBuilder(VOXEL_SIZE)

    # 1. Dark Charred Inner Core (#110e0c = 13) with Heroic V-Taper (0.28m waist -> 0.48m shoulders)
    for iy in range(-6, 68):
        u = (iy + 6) / 74.0
        rx_core = 18.8 + (u ** 1.15) * 8.2
        rz_core = 12.8 + math.sin(u * math.pi * 0.85) * 4.2

        for ix in range(int(-rx_core - 3), int(rx_core + 4)):
            for iz in range(int(-rz_core - 3), int(rz_core + 4)):
                d = math.sqrt((ix / rx_core) ** 2 + (iz / rz_core) ** 2)
                if 0.72 <= d <= 0.94:
                    # Glowing vertical orange-gold Cinder Runes (#ff6611 = 16, emission 2.8) down the sternum & intercostal gaps
                    is_sternum_rune = (
                        (abs(ix) <= 2 and 4 <= iy <= 56 and iz > 6 and ((iy % 5 != 0) or abs(ix) == 2))
                        or (4 <= abs(ix) <= 12 and (iy % 9 in (4, 5)) and 10 <= iy <= 54 and iz > 5 and (abs(ix) % 3 != 0))
                    )
                    v.set_voxel(ix, iy, iz, 16 if is_sternum_rune else 13, 1.22 if is_sternum_rune else 0.78)

                # 2. Exposed Anatomical Iron Ribcage (#2a2624 = 15) & Bone Sternum/Clavicles/Spine (#9c8c74 = 12) proud on outer shell
                if 0.90 <= d <= 1.06:
                    # 6 pairs of anatomical curved ribs arching from back spine around sides to front sternum
                    rib_y = iy - int(abs(ix) * 0.18)
                    is_rib_arch = (8 <= iy <= 58) and (rib_y % 9 in (0, 1, 2))
                    is_clavicle = (59 <= iy <= 64) and (abs(ix) <= 24)
                    is_sternum_bone = (8 <= iy <= 62) and (3 <= abs(ix) <= 4) and (iz > 6)
                    is_spine_vertebra = (0 <= iy <= 64) and (abs(ix) <= 3) and (iz < -6) and (iy % 4 != 0)
                    is_waist_belt = -6 <= iy <= 2

                    if is_sternum_bone or is_clavicle or is_spine_vertebra:
                        v.set_voxel(ix, iy, iz, 12 if (iy % 3 != 0) else 11, 1.06)
                    elif is_rib_arch or is_waist_belt:
                        v.set_voxel(ix, iy, iz, 15 if (iy % 2 == 0) else 14, 1.04)

    # 3. Broad Dark-Iron Cage Pauldrons (#242220 = 14 / #2a2624 = 15) + 3 Burning Tallow Candles per Shoulder
    for side in (-1, 1):
        for iy in range(42, 69):
            u_p = (iy - 42) / 26.0
            r_p = 9.6 - u_p * 1.2
            cx_p = side * (28.5 - u_p * 3.0)
            for ix in range(int(cx_p - r_p - 1), int(cx_p + r_p + 2)):
                if side * ix < 16:
                    continue
                for iz in range(-15, 16):
                    d_p = math.sqrt(((ix - cx_p) / r_p) ** 2 + (iz / 15.0) ** 2)
                    if 0.74 <= d_p <= 1.0:
                        # Open-work iron cage bars + glowing ember interior
                        is_cage_bar = (iy in (42, 43, 51, 59, 67, 68)) or (abs(iz) in (0, 5, 10, 14)) or (abs(ix - int(cx_p)) >= int(r_p) - 2)
                        if is_cage_bar:
                            v.set_voxel(ix, iy, iz, 15 if iy in (42, 59, 68) else 14, 1.05)
                        elif d_p <= 0.85 and (iy % 4 == 0) and (iz % 3 == 0):
                            v.set_voxel(ix, iy, iz, 16, 1.15)

        # Cluster of 3 Burning Tallow Candles (#d8c39e = 18 wax, #ff8811 = 19 flames) on each shoulder pauldron
        candle_specs = [
            (side * 24, 67, 2, 11, 2),
            (side * 28, 65, -3, 14, 2),
            (side * 22, 68, -4, 9, 2),
        ]
        for cx, cy, cz, ch, cr in candle_specs:
            # Iron candle cup holder at base
            v.fill_cylinder_y(cx, cy - 1, cy + 1, cz, cr + 1, 14, 0.95)
            # Tallow candle body + wax drip ribs (#d8c39e = 18)
            v.fill_cylinder_y(cx, cy, cy + ch, cz, cr, 18, 1.0)
            for dy_rib in range(1, ch - 1):
                v.set_voxel(cx + side, cy + dy_rib, cz + cr, 18, 1.06)
                if dy_rib < ch // 2:
                    v.set_voxel(cx, cy + dy_rib, cz - cr, 18, 1.04)
            # Warm orange-gold flame tip (#ff8811 = 19, emission 2.5)
            v.set_voxel(cx, cy + ch + 1, cz, 15, 0.70)
            for fy in range(cy + ch + 2, cy + ch + 6):
                for fx in range(cx - 1, cx + 2):
                    for fz in range(cz - 1, cz + 2):
                        if fy < cy + ch + 4 or (fx == cx and fz == cz):
                            v.set_voxel(fx, fy, fz, 19, 1.20)

        # 4. Hanging Wrought-Iron Link Chains from Outer Pauldrons + Glowing Reliquary Censers at Hip Height
        chain_x = side * 26
        chain_z = 8
        # Chain descending from under pauldron (iy = 42) down to hip height (iy = 4)
        for link_idx, cy_link in enumerate(range(6, 43, 3)):
            if link_idx % 2 == 0:
                v.fill_box(chain_x - 1, chain_x + 1, cy_link, cy_link + 2, chain_z, chain_z, 14, 1.02)
            else:
                v.fill_box(chain_x, chain_x, cy_link, cy_link + 2, chain_z - 1, chain_z + 1, 15, 0.96)

        # Glowing Reliquary Censer (#242220 = 14 iron cage + #ff7722 = 17 inner ember glow) suspended at hip (iy = -8..6)
        for iy_c in range(-8, 7):
            dy_c = iy_c - (-1)
            r_cen = max(1.5, 4.6 - abs(dy_c) * 0.45)
            for ix_c in range(int(chain_x - r_cen - 1), int(chain_x + r_cen + 2)):
                for iz_c in range(int(chain_z - r_cen - 1), int(chain_z + r_cen + 2)):
                    dist_c = math.sqrt((ix_c - chain_x) ** 2 + (iz_c - chain_z) ** 2)
                    if dist_c <= r_cen:
                        is_censer_cage = (dist_c >= r_cen - 1.2) and ((iy_c in (-8, -4, -1, 2, 6)) or ((ix_c + iz_c) % 2 == 0))
                        v.set_voxel(ix_c, iy_c, iz_c, 14 if is_censer_cage else 17, 1.05 if is_censer_cage else 1.22)

    v.subtract_inner_mannequin_clearance(
        lambda wx, wy, wz: (-0.03 <= wz <= 0.52) and ((wx / 0.118) ** 2 + (wy / 0.075) ** 2 < 1.0)
    )
    return v.bake_to_blender_object("Set3_SkeletalCinderCageChest_7mm", mats)


def build_set3_hands_7mm(mats: list) -> bpy.types.Object:
    """
    Set 3 HANDS: Skeletal Cage Gauntlets (origin at Y = 1.05m).
    - Open-ribbed blackened-iron vambraces (#242220 = 14 / #2a2624 = 15) over charred core (#110e0c = 13) & cinder glow (#ff6611 = 16)
    - Skeletal finger-bone plate overlays (#b8a68e = 11 / #9c8c74 = 12)
    """
    _run_boolean_remesh_seed("Set3_Hands_Seed", 0.036, 0.24)
    v = MicroVoxelBuilder(VOXEL_SIZE)

    for side in (-1, 1):
        ax = side * 31
        # 1. Open-Ribbed Blackened-Iron Vambraces (iy = -8..28)
        for iy in range(-8, 29):
            u = (iy + 8) / 36.0
            rx = 5.0 + u * 2.2
            rz = 5.0 + u * 2.2
            is_rib_ring = (iy % 5 in (0, 1)) or (iy in (-8, 27, 28))
            for ix in range(int(ax - rx - 1), int(ax + rx + 2)):
                for iz in range(int(-rz - 1), int(rz + 2)):
                    d = math.sqrt(((ix - ax) / rx) ** 2 + (iz / rz) ** 2)
                    if 0.60 <= d <= 1.0:
                        is_long_bar = abs(iz) in (0, 4) or abs(ix - ax) >= rx - 1.2
                        if is_rib_ring or is_long_bar:
                            # Bone ulna/radius ridge on outer dorsal side
                            is_bone_ridge = (abs(iz) <= 1) and (side * (ix - ax) > 2.5) and (iy % 3 != 0)
                            v.set_voxel(ix, iy, iz, 12 if is_bone_ridge else 14, 1.06 if is_bone_ridge else 0.98)
                        else:
                            is_ember = (iy % 5 == 3) and (abs(iz) == 2) and (side * (ix - ax) > 1.5)
                            v.set_voxel(ix, iy, iz, 16 if is_ember else 13, 1.18 if is_ember else 0.78)

        # 2. Skeletal Finger-Bone Plate Overlays (iy = -21..-9)
        for iy in range(-21, -8):
            is_phalange_joint = (iy % 3 == 0)
            for ix in range(ax - 5, ax + 6):
                for iz in range(-5, 6):
                    if iy < -14 and (iz % 2 == 0):
                        continue
                    d = math.sqrt(((ix - ax) / 4.8) ** 2 + (iz / 4.8) ** 2)
                    if 0.45 <= d <= 1.0:
                        is_outer_bone = (side * (ix - ax) > 0) and (not is_phalange_joint)
                        v.set_voxel(ix, iy, iz, 11 if is_outer_bone else 14, 1.08 if is_outer_bone else 0.92)

    v.subtract_inner_mannequin_clearance(
        lambda wx, wy, wz: (
            (-0.06 <= wz <= 0.19)
            and (
                ((wx - 0.217) / 0.025) ** 2 + (wy / 0.025) ** 2 < 1.0
                or ((wx + 0.217) / 0.025) ** 2 + (wy / 0.025) ** 2 < 1.0
            )
        )
    )
    return v.bake_to_blender_object("Set3_SkeletalCageGauntlets_7mm", mats)


def build_set3_legs_7mm(mats: list) -> bpy.types.Object:
    """
    Set 3 LEGS: Rune-Etched Furnace-Grate Leg Cages & Hanging Cinder Tabard (single-side at X=±0.125m, Y=0.88m).
    - Central hanging cloth tabard strip down the front inscribed with glowing vertical cinder runes (#ff6611 = 16, emission 2.8)
    - Thigh/shin furnace-grate iron cages (#242220 = 14 / #2a2624 = 15) framing glowing ember rune columns down the legs
    """
    _run_boolean_remesh_seed("Set3_Legs_Seed", 0.070, 0.72)
    v = MicroVoxelBuilder(VOXEL_SIZE)

    # 1. Central Hanging Cloth Tabard Strip on inner front (ix = -16..-7, iy = -68..8, iz = 9..12)
    for iy in range(-68, 9):
        jag = (iy * 3) % 2 if iy < -58 else 0
        for ix in range(-16 + jag, -6):
            iz_tab = 10 + int(math.sin((iy + 68) * 0.08))
            is_border = (ix in (-16, -7)) or (iy <= -65)
            # Glowing vertical cinder runes (#ff6611 = 16, emission 2.8) inscribed down the front tabard
            is_cinder_rune = (
                (-58 <= iy <= 2)
                and (-14 <= ix <= -9)
                and (
                    (ix in (-12, -11) and (iy % 6 != 0))
                    or ((iy % 8 in (2, 5)) and ix in (-14, -13, -10, -9))
                )
            )
            mat_tab = 16 if is_cinder_rune else (14 if is_border else 13)
            v.set_voxel(ix, iy, iz_tab, mat_tab, 1.22 if is_cinder_rune else (0.96 if is_border else 0.82))

    # 2. Thigh/Shin Furnace-Grate Iron Cages (#242220 = 14) Framing Glowing Ember Rune Columns (iy = -98..8)
    for iy in range(-98, 9):
        u = (iy + 98) / 106.0
        is_knee_skull = -51 <= iy <= -39
        r_leg = 6.8 + u * 3.8 + (1.6 if is_knee_skull else 0.0)
        is_grate_hoop = (iy % 9 in (0, 1)) or (iy in (-98, -52, -38, 7, 8))

        for ix in range(int(-r_leg - 2), int(r_leg + 3)):
            for iz in range(int(-r_leg - 2), int(r_leg + 3)):
                d = math.sqrt((ix / r_leg) ** 2 + (iz / r_leg) ** 2)
                # Inner charred core + glowing vertical cinder rune columns
                if 0.65 <= d <= 0.88:
                    is_leg_rune = (
                        ((abs(ix) <= 2 and iz > 3) or (ix > 3 and abs(iz) <= 2))
                        and (iy % 4 != 0)
                    )
                    v.set_voxel(ix, iy, iz, 16 if is_leg_rune else 13, 1.22 if is_leg_rune else 0.76)

                # Outer Furnace-Grate Iron Cage Bars & Knee Skull Patella (#b8a68e = 11)
                if 0.86 <= d <= 1.04:
                    if is_knee_skull and iz > 4 and abs(ix) <= 5:
                        is_eye = (iy in (-45, -44)) and (abs(ix) in (2, 3))
                        v.set_voxel(ix, iy, iz, 16 if is_eye else 11, 1.20 if is_eye else 1.06)
                    else:
                        is_vert_bar = (abs(ix) in (0, 4, 8)) or (abs(iz) in (0, 4, 8))
                        if is_grate_hoop or is_vert_bar:
                            v.set_voxel(ix, iy, iz, 15 if is_grate_hoop else 14, 1.05)

    v.subtract_inner_mannequin_clearance(
        lambda wx, wy, wz: (-0.70 <= wz <= 0.07) and ((wx / 0.044) ** 2 + (wy / 0.044) ** 2 < 1.0)
    )
    return v.bake_to_blender_object("Set3_FurnaceGrateLegCage_7mm", mats)


def build_set3_feet_7mm(mats: list) -> bpy.types.Object:
    """
    Set 3 FEET: Heavy Riveted Iron Sabatons with Cinder Vents (single-side at X=±0.125m, Y=0.18m).
    """
    _run_boolean_remesh_seed("Set3_Feet_Seed", 0.056, 0.20)
    v = MicroVoxelBuilder(VOXEL_SIZE)

    for iy in range(-10, 9):
        r_ank = 6.9 + max(0, iy) * 0.12
        is_hoop = iy in (-10, -5, 0, 5, 8)
        v.fill_ring(iy, r_ank - 2.2, r_ank - 2.2, r_ank, r_ank, 15 if is_hoop else 14, 1.02)

    for iy in range(-25, -8):
        for iz in range(-8, 20):
            u_len = (iz + 8) / 27.0
            max_h = -9 - int(max(0.0, u_len - 0.30) * 10.5)
            if iy > max_h:
                continue
            half_w = 6 if u_len < 0.72 else 5
            for ix in range(-half_w, half_w + 1):
                is_outer = (abs(ix) >= half_w - 1) or (iz <= -7) or (iz >= 18) or (iy >= max_h - 1) or (iy <= -24)
                if not is_outer:
                    continue
                is_grate_rib = (iz % 4 == 0) or (abs(ix) == half_w) or (iy <= -23)
                is_ember_slit = (not is_grate_rib) and (abs(ix) <= 2) and (-2 <= iz <= 12) and (iy >= max_h - 1)
                v.set_voxel(ix, iy, iz, 16 if is_ember_slit else (15 if is_grate_rib else 14), 1.20 if is_ember_slit else 0.98)

    v.subtract_inner_mannequin_clearance(
        lambda wx, wy, wz: (-0.12 <= wz <= 0.06) and ((wx / 0.032) ** 2 + (wy / 0.032) ** 2 < 1.0)
    )
    return v.bake_to_blender_object("Set3_CinderIronSabaton_7mm", mats)


# ==============================================================================
# EXPORTER FOR SETS 1, 2, AND 3 ONLY (SAFETY LOCK: NEVER TOUCHES SET 0!)
# ==============================================================================
def export_sets_1_2_3_7mm(output_dir: str, sets_to_build: tuple = (1, 2, 3)) -> None:
    os.makedirs(output_dir, exist_ok=True)
    builders_by_set = {
        1: [
            ("armor_set1_head.glb", build_set1_head_7mm),
            ("armor_set1_chest.glb", build_set1_chest_7mm),
            ("armor_set1_hands.glb", build_set1_hands_7mm),
            ("armor_set1_legs.glb", build_set1_legs_7mm),
            ("armor_set1_feet.glb", build_set1_feet_7mm),
        ],
        2: [
            ("armor_set2_head.glb", build_set2_head_7mm),
            ("armor_set2_chest.glb", build_set2_chest_7mm),
            ("armor_set2_hands.glb", build_set2_hands_7mm),
            ("armor_set2_legs.glb", build_set2_legs_7mm),
            ("armor_set2_feet.glb", build_set2_feet_7mm),
        ],
        3: [
            ("armor_set3_head.glb", build_set3_head_7mm),
            ("armor_set3_chest.glb", build_set3_chest_7mm),
            ("armor_set3_hands.glb", build_set3_hands_7mm),
            ("armor_set3_legs.glb", build_set3_legs_7mm),
            ("armor_set3_feet.glb", build_set3_feet_7mm),
        ],
    }

    for set_idx in sets_to_build:
        if set_idx == 0:
            raise RuntimeError("SAFETY LOCK: Set 0 is locked and must NOT be regenerated by blender_sets_1_2_3_7mm.py!")
        if set_idx not in builders_by_set:
            continue
        for filename, builder_fn in builders_by_set[set_idx]:
            clear_scene()
            mats = make_sets_123_materials()
            obj = builder_fn(mats)
            out_path = os.path.join(output_dir, filename)
            export_glb(obj, out_path)


if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    out_dir = os.path.join(project_root, "assets", "models", "armor")
    selected_sets = [1, 2, 3]
    for i, arg in enumerate(sys.argv):
        if arg == "--sets" and i + 1 < len(sys.argv):
            selected_sets = [int(x.strip()) for x in sys.argv[i + 1].split(",") if x.strip().isdigit() and int(x.strip()) in (1, 2, 3)]
        elif arg.startswith("--sets="):
            selected_sets = [int(x.strip()) for x in arg.split("=", 1)[1].split(",") if x.strip().isdigit() and int(x.strip()) in (1, 2, 3)]
    export_sets_1_2_3_7mm(out_dir, tuple(selected_sets))
