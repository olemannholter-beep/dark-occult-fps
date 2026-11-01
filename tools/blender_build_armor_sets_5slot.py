import bpy
import bmesh
import math
import os
import sys
from mathutils import Vector, Euler

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from blender_detail_kit import _add_bm_beveled_box, bake_3tone_gothic_vertex_colors

OUTPUT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "assets", "models", "armor"))


def clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_pbr_mat(
    name: str,
    base_color: tuple[float, float, float, float],
    metallic: float,
    roughness: float,
    emission: tuple[float, float, float, float] | None = None,
    emission_strength: float = 0.0,
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    if bsdf is None:
        bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")

    vcol = nodes.new(type="ShaderNodeVertexColor")
    vcol.layer_name = "Col"
    mix = nodes.new(type="ShaderNodeMixRGB")
    mix.blend_type = 'MULTIPLY'
    mix.inputs[0].default_value = 1.0
    mix.inputs[1].default_value = base_color
    links.new(vcol.outputs["Color"], mix.inputs[2])
    links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])

    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission is not None and emission_strength > 0.0:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = emission
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def get_set_materials(set_idx: int) -> list[bpy.types.Material]:
    if set_idx == 0:
        return [
            make_pbr_mat("Set0_LeatherPrimary", (0.24, 0.16, 0.11, 1.0), 0.18, 0.72),
            make_pbr_mat("Set0_DarkCoat", (0.13, 0.10, 0.09, 1.0), 0.10, 0.85),
            make_pbr_mat("Set0_SilverTrim", (0.78, 0.76, 0.72, 1.0), 0.88, 0.32),
            make_pbr_mat("Set0_AmberLens", (0.95, 0.65, 0.22, 1.0), 0.20, 0.25, (1.0, 0.62, 0.18, 1.0), 2.4),
        ]
    if set_idx == 1:
        return [
            make_pbr_mat("Set1_SanctifiedSteel", (0.24, 0.30, 0.40, 1.0), 0.88, 0.32),
            make_pbr_mat("Set1_CrimsonVelvet", (0.42, 0.09, 0.13, 1.0), 0.12, 0.80),
            make_pbr_mat("Set1_GildedCross", (0.90, 0.76, 0.34, 1.0), 0.92, 0.26),
            make_pbr_mat("Set1_ParchmentSeal", (0.86, 0.80, 0.66, 1.0), 0.05, 0.88),
        ]
    if set_idx == 2:
        return [
            make_pbr_mat("Set2_GildedPlate", (0.80, 0.64, 0.26, 1.0), 0.92, 0.26),
            make_pbr_mat("Set2_DarkIron", (0.24, 0.23, 0.27, 1.0), 0.84, 0.40),
            make_pbr_mat("Set2_BrightBrass", (0.98, 0.84, 0.38, 1.0), 0.95, 0.22),
            make_pbr_mat("Set2_EmberSlit", (1.0, 0.48, 0.16, 1.0), 0.30, 0.30, (1.0, 0.45, 0.12, 1.0), 2.6),
        ]
    return [
        make_pbr_mat("Set3_AbyssalObsidian", (0.15, 0.10, 0.20, 1.0), 0.84, 0.32),
        make_pbr_mat("Set3_OssuaryBone", (0.80, 0.75, 0.64, 1.0), 0.12, 0.76),
        make_pbr_mat("Set3_ReliquaryGold", (0.92, 0.72, 0.30, 1.0), 0.90, 0.28),
        make_pbr_mat("Set3_VioletSigil", (0.88, 0.24, 1.0, 1.0), 0.20, 0.24, (0.88, 0.24, 1.0, 1.0), 3.2),
    ]


def add_cyl(
    bm: bmesh.types.BMesh,
    r_bot: float,
    r_top: float,
    height: float,
    center: tuple[float, float, float],
    rot_deg: tuple[float, float, float] = (0.0, 0.0, 0.0),
    segs: int = 12,
    mat_idx: int = 0,
) -> None:
    ret = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r_bot, radius2=r_top, depth=height)
    verts = ret["verts"]
    if any(abs(a) > 1e-4 for a in rot_deg):
        rmat = Euler((math.radians(rot_deg[0]), math.radians(rot_deg[1]), math.radians(rot_deg[2])), 'XYZ').to_matrix()
        bmesh.ops.rotate(bm, verts=verts, cent=(0.0, 0.0, 0.0), matrix=rmat)
    bmesh.ops.translate(bm, verts=verts, vec=center)
    faces = {f for v in verts for f in v.link_faces if f.is_valid}
    for f in faces:
        f.material_index = mat_idx
        f.smooth = True


def add_box(
    bm: bmesh.types.BMesh,
    size: tuple[float, float, float],
    center: tuple[float, float, float],
    rot_deg: tuple[float, float, float] = (0.0, 0.0, 0.0),
    bevel: float = 0.005,
    mat_idx: int = 0,
) -> None:
    rot_rad = (math.radians(rot_deg[0]), math.radians(rot_deg[1]), math.radians(rot_deg[2]))
    _add_bm_beveled_box(bm, size, center, rot_rad, bevel, mat_idx)



def build_head_bm(bm: bmesh.types.BMesh, set_idx: int) -> None:
    # Neck gorget & lower skull base (origin at neck base Z = 0, facing -Y in Blender -> +Z in Godot)
    add_cyl(bm, 0.088, 0.076, 0.08, (0.0, 0.0, 0.03), segs=12, mat_idx=1)
    add_cyl(bm, 0.105, 0.112, 0.14, (0.0, 0.0, 0.11), segs=14, mat_idx=0)
    add_box(bm, (0.14, 0.08, 0.07), (0.0, -0.055, 0.065), bevel=0.01, mat_idx=1)

    if set_idx == 0:
        # Set 0: Wide-brimmed leather Hunter Tricorn hat, shadowed face scarf, amber ocular lenses
        add_box(bm, (0.17, 0.14, 0.10), (0.0, -0.02, 0.08), bevel=0.012, mat_idx=1)
        for sx in (-1.0, 1.0):
            add_cyl(bm, 0.026, 0.024, 0.028, (sx * 0.044, -0.108, 0.118), (90.0, 0.0, 0.0), segs=10, mat_idx=2)
            add_cyl(bm, 0.019, 0.019, 0.032, (sx * 0.044, -0.112, 0.118), (90.0, 0.0, 0.0), segs=10, mat_idx=3)
        # Tricorn crown + 3-folded wide brim + silver hatband buckle
        add_cyl(bm, 0.125, 0.102, 0.12, (0.0, 0.01, 0.21), segs=12, mat_idx=0)
        add_cyl(bm, 0.128, 0.126, 0.026, (0.0, 0.01, 0.168), segs=12, mat_idx=1)
        add_box(bm, (0.042, 0.014, 0.034), (0.0, -0.122, 0.168), bevel=0.003, mat_idx=2)
        add_box(bm, (0.34, 0.34, 0.018), (0.0, -0.01, 0.155), bevel=0.005, mat_idx=0)
        add_box(bm, (0.28, 0.045, 0.065), (0.0, -0.155, 0.182), (28.0, 0.0, 0.0), bevel=0.006, mat_idx=0)
        for sx in (-1.0, 1.0):
            add_box(bm, (0.045, 0.28, 0.065), (sx * 0.152, 0.01, 0.182), (0.0, sx * -28.0, sx * 18.0), bevel=0.006, mat_idx=0)

    elif set_idx == 1:
        # Set 1: Winged Sallet Helm, riveted visor slit, crimson throat aventail, forehead cross crest
        add_cyl(bm, 0.118, 0.105, 0.16, (0.0, 0.0, 0.14), segs=14, mat_idx=0)
        add_cyl(bm, 0.126, 0.145, 0.09, (0.0, 0.04, 0.055), (18.0, 0.0, 0.0), segs=12, mat_idx=0)
        add_box(bm, (0.19, 0.13, 0.085), (0.0, -0.055, 0.118), bevel=0.01, mat_idx=0)
        add_box(bm, (0.15, 0.03, 0.014), (0.0, -0.118, 0.124), bevel=0.002, mat_idx=1)
        # Forehead Gilded Cross Crest + Side Steel Wings
        add_box(bm, (0.018, 0.022, 0.11), (0.0, -0.116, 0.175), bevel=0.003, mat_idx=2)
        add_box(bm, (0.075, 0.022, 0.018), (0.0, -0.116, 0.188), bevel=0.003, mat_idx=2)
        for sx in (-1.0, 1.0):
            add_box(bm, (0.022, 0.14, 0.13), (sx * 0.132, 0.01, 0.175), (14.0, sx * 16.0, 0.0), bevel=0.004, mat_idx=2)

    elif set_idx == 2:
        # Set 2: Siege Greathelm (ribbed barrel helm, brass cross faceplate, crown rivets)
        add_cyl(bm, 0.126, 0.120, 0.23, (0.0, 0.0, 0.135), segs=16, mat_idx=0)
        add_cyl(bm, 0.132, 0.128, 0.032, (0.0, 0.0, 0.242), segs=16, mat_idx=2)
        add_box(bm, (0.032, 0.25, 0.028), (0.0, 0.0, 0.258), bevel=0.005, mat_idx=2)
        # Brass cross faceplate + glowing ember eye slit
        add_box(bm, (0.028, 0.024, 0.19), (0.0, -0.124, 0.135), bevel=0.004, mat_idx=2)
        add_box(bm, (0.19, 0.024, 0.032), (0.0, -0.118, 0.148), bevel=0.004, mat_idx=2)
        add_box(bm, (0.15, 0.018, 0.012), (0.0, -0.126, 0.148), bevel=0.002, mat_idx=3)
        for sx in (-1.0, 1.0):
            for rz in (0.075, 0.105):
                add_box(bm, (0.038, 0.018, 0.010), (sx * 0.056, -0.116, rz), bevel=0.002, mat_idx=1)

    else:
        # Set 3: Bone-Cage Crown, Blind Seer Mask, violet sigil halo spikes
        add_cyl(bm, 0.112, 0.104, 0.18, (0.0, 0.0, 0.12), segs=14, mat_idx=0)
        add_box(bm, (0.16, 0.06, 0.14), (0.0, -0.088, 0.118), bevel=0.014, mat_idx=1)
        add_box(bm, (0.026, 0.018, 0.065), (0.0, -0.120, 0.145), bevel=0.003, mat_idx=3)
        add_box(bm, (0.065, 0.018, 0.022), (0.0, -0.120, 0.152), bevel=0.003, mat_idx=3)
        add_cyl(bm, 0.124, 0.128, 0.028, (0.0, 0.0, 0.205), segs=14, mat_idx=2)
        for i in range(7):
            ang = -math.pi * 0.75 + (i / 6.0) * (math.pi * 1.5)
            px = math.sin(ang) * 0.122
            py = -math.cos(ang) * 0.122
            add_box(bm, (0.018, 0.018, 0.11), (px, py, 0.255), (0.0, 0.0, math.degrees(-ang)), bevel=0.003, mat_idx=1 if i % 2 == 0 else 2)
            if i in (2, 3, 4):
                add_box(bm, (0.012, 0.012, 0.045), (px * 1.05, py * 1.05, 0.31), bevel=0.002, mat_idx=3)



def build_chest_bm(bm: bmesh.types.BMesh, set_idx: int) -> None:
    # Core torso block (origin at waist Z = 0, extending up to shoulders Z = +0.52 and skirt Z = -0.32)
    add_box(bm, (0.35, 0.23, 0.30), (0.0, 0.0, 0.33), bevel=0.018, mat_idx=0)
    add_box(bm, (0.29, 0.20, 0.22), (0.0, 0.0, 0.11), bevel=0.014, mat_idx=1)
    # Waist utility belt + buckle
    add_box(bm, (0.31, 0.22, 0.055), (0.0, 0.0, 0.02), bevel=0.006, mat_idx=1)
    add_box(bm, (0.068, 0.024, 0.068), (0.0, -0.114, 0.02), bevel=0.004, mat_idx=2)
    # Upper arm sleeves (L/R)
    for sx in (-1.0, 1.0):
        add_cyl(bm, 0.058, 0.068, 0.26, (sx * 0.235, 0.0, 0.33), (0.0, sx * 8.0, 0.0), segs=12, mat_idx=1)

    if set_idx == 0:
        # Set 0: Highwayman Greatcoat (capes, bandolier + 4 silver vials, flared skirt tails)
        for sx in (-1.0, 1.0):
            add_box(bm, (0.18, 0.27, 0.12), (sx * 0.15, 0.0, 0.45), (0.0, sx * 14.0, 0.0), bevel=0.012, mat_idx=0)
            add_box(bm, (0.15, 0.24, 0.32), (sx * 0.105, 0.02, -0.16), (6.0, sx * 6.0, 0.0), bevel=0.01, mat_idx=1)
        add_box(bm, (0.055, 0.25, 0.44), (0.0, -0.01, 0.26), (0.0, 32.0, 0.0), bevel=0.006, mat_idx=0)
        for i in range(4):
            t = -0.09 + i * 0.06
            add_cyl(bm, 0.014, 0.014, 0.065, (t, -0.128, 0.29 - i * 0.045), (0.0, 15.0, 0.0), segs=8, mat_idx=2)
            add_cyl(bm, 0.011, 0.011, 0.035, (t, -0.132, 0.29 - i * 0.045), (0.0, 15.0, 0.0), segs=8, mat_idx=3)

    elif set_idx == 1:
        # Set 1: Sanctified Brigandine Cuirass (steel breastplate, cross crest,pauldrons, wax seal)
        add_box(bm, (0.37, 0.25, 0.28), (0.0, -0.01, 0.34), bevel=0.016, mat_idx=0)
        add_box(bm, (0.032, 0.024, 0.22), (0.0, -0.136, 0.34), bevel=0.004, mat_idx=2)
        add_box(bm, (0.15, 0.024, 0.032), (0.0, -0.136, 0.37), bevel=0.004, mat_idx=2)
        for sx in (-1.0, 1.0):
            add_box(bm, (0.17, 0.26, 0.14), (sx * 0.21, 0.0, 0.45), (0.0, sx * 18.0, 0.0), bevel=0.012, mat_idx=0)
            add_box(bm, (0.18, 0.03, 0.03), (sx * 0.21, -0.12, 0.45), (0.0, sx * 18.0, 0.0), bevel=0.004, mat_idx=2)
            add_box(bm, (0.14, 0.23, 0.28), (sx * 0.095, 0.01, -0.14), (0.0, sx * 5.0, 0.0), bevel=0.008, mat_idx=1)
        add_box(bm, (0.045, 0.015, 0.12), (-0.11, -0.128, 0.23), bevel=0.002, mat_idx=3)

    elif set_idx == 2:
        # Set 2: Catacomb Juggernaut Fluted Plate (massive V-prow breastplate, 3-tier siege pauldrons, faulds)
        add_box(bm, (0.40, 0.28, 0.31), (0.0, -0.015, 0.34), bevel=0.02, mat_idx=0)
        add_box(bm, (0.055, 0.06, 0.29), (0.0, -0.145, 0.34), bevel=0.008, mat_idx=2)
        for sx in (-1.0, 1.0):
            for tier in range(3):
                tz = 0.49 - tier * 0.055
                add_box(bm, (0.20 - tier * 0.015, 0.28 - tier * 0.02, 0.085), (sx * (0.22 + tier * 0.012), 0.0, tz), (0.0, sx * (14.0 + tier * 6.0), 0.0), bevel=0.01, mat_idx=0 if tier != 1 else 2)
            for fauld in range(3):
                fz = -0.04 - fauld * 0.065
                add_box(bm, (0.15, 0.24, 0.06), (sx * 0.095, 0.0, fz), (0.0, sx * 6.0, 0.0), bevel=0.006, mat_idx=0 if fauld % 2 == 0 else 1)

    else:
        # Set 3: Abyssal Reliquary Mantle (obsidian robe, bone ribcage harness, violet soul core, skull pauldrons)
        add_box(bm, (0.36, 0.24, 0.30), (0.0, 0.0, 0.33), bevel=0.015, mat_idx=0)
        add_cyl(bm, 0.042, 0.042, 0.036, (0.0, -0.125, 0.34), (90.0, 0.0, 0.0), segs=12, mat_idx=3)
        for r in range(4):
            rz = 0.23 + r * 0.055
            add_box(bm, (0.34, 0.025, 0.022), (0.0, -0.122, rz), bevel=0.004, mat_idx=1)
        for sx in (-1.0, 1.0):
            add_box(bm, (0.18, 0.25, 0.14), (sx * 0.21, 0.0, 0.45), (0.0, sx * 15.0, 0.0), bevel=0.014, mat_idx=1)
            add_box(bm, (0.03, 0.03, 0.11), (sx * 0.24, -0.04, 0.54), (0.0, sx * -12.0, 0.0), bevel=0.004, mat_idx=2)
            add_box(bm, (0.15, 0.24, 0.34), (sx * 0.10, 0.01, -0.17), (0.0, sx * 7.0, 0.0), bevel=0.008, mat_idx=0)



def build_legs_bm(bm: bmesh.types.BMesh, set_idx: int) -> None:
    # Single leg unit (origin at hip joint Z = 0, extending down to ankle Z = -0.74)
    # Fits cleanly inside LeftLegPivot / RightLegPivot on both PaperDoll and FirstPersonBody
    add_cyl(bm, 0.068, 0.082, 0.36, (0.0, 0.0, -0.18), segs=12, mat_idx=1)
    add_cyl(bm, 0.052, 0.066, 0.36, (0.0, 0.0, -0.54), segs=12, mat_idx=0)
    # Knee poleyn guard at Z = -0.36
    add_box(bm, (0.125, 0.085, 0.13), (0.0, -0.045, -0.36), bevel=0.014, mat_idx=0)

    if set_idx == 0:
        # Set 0: Stalker Breeches (quilted thigh breeches, leather knee-straps, silver thigh buckle)
        for sz in (-0.12, -0.24, -0.46, -0.58):
            add_cyl(bm, 0.076 if sz > -0.35 else 0.064, 0.076 if sz > -0.35 else 0.064, 0.024, (0.0, 0.0, sz), segs=12, mat_idx=0)
        add_box(bm, (0.036, 0.018, 0.036), (0.0, -0.078, -0.24), bevel=0.004, mat_idx=2)

    elif set_idx == 1:
        # Set 1: Tasset Greaves (crimson cuisses, steel poleyn knee wings, fluted shin greaves)
        add_box(bm, (0.135, 0.045, 0.24), (0.0, -0.058, -0.18), bevel=0.008, mat_idx=0)
        add_box(bm, (0.155, 0.095, 0.095), (0.0, -0.052, -0.36), bevel=0.01, mat_idx=2)
        add_box(bm, (0.115, 0.065, 0.28), (0.0, -0.048, -0.54), bevel=0.01, mat_idx=0)
        add_box(bm, (0.022, 0.022, 0.26), (0.0, -0.078, -0.54), bevel=0.003, mat_idx=2)

    elif set_idx == 2:
        # Set 2: Fluted Poleyn Greaves (heavy gilded thigh armor, spiked knee poleyns, siege shin cylinders)
        add_cyl(bm, 0.078, 0.092, 0.32, (0.0, 0.0, -0.18), segs=14, mat_idx=0)
        add_box(bm, (0.165, 0.11, 0.14), (0.0, -0.055, -0.36), bevel=0.014, mat_idx=2)
        add_cyl(bm, 0.022, 0.004, 0.055, (0.0, -0.115, -0.36), (90.0, 0.0, 0.0), segs=8, mat_idx=2)
        add_cyl(bm, 0.064, 0.076, 0.32, (0.0, 0.0, -0.54), segs=14, mat_idx=0)

    else:
        # Set 3: Ritual Pillar Greaves (obsidian shin guards, bone femur splints, violet sigil bands)
        add_box(bm, (0.032, 0.032, 0.28), (-0.048, -0.052, -0.18), bevel=0.005, mat_idx=1)
        add_box(bm, (0.032, 0.032, 0.28), (0.048, -0.052, -0.18), bevel=0.005, mat_idx=1)
        add_box(bm, (0.135, 0.095, 0.13), (0.0, -0.052, -0.36), bevel=0.012, mat_idx=1)
        add_cyl(bm, 0.065, 0.065, 0.022, (0.0, 0.0, -0.48), segs=12, mat_idx=3)


def build_feet_bm(bm: bmesh.types.BMesh, set_idx: int) -> None:
    # Single boot unit (origin at ankle Z = 0, sole grounded at Z = -0.18, toe extending toward -Y -> +Z in Godot)
    add_cyl(bm, 0.056, 0.062, 0.14, (0.0, 0.0, -0.05), segs=12, mat_idx=0)
    add_box(bm, (0.115, 0.24, 0.095), (0.0, -0.055, -0.132), bevel=0.014, mat_idx=0)
    add_box(bm, (0.122, 0.25, 0.028), (0.0, -0.055, -0.166), bevel=0.004, mat_idx=1)

    if set_idx == 0:
        # Set 0: Shadow-Step Boots (cuffed leather boots, silver spur straps, steel toe caps)
        add_cyl(bm, 0.068, 0.062, 0.055, (0.0, 0.0, -0.01), segs=12, mat_idx=1)
        add_box(bm, (0.120, 0.085, 0.075), (0.0, -0.145, -0.138), bevel=0.012, mat_idx=2)
        add_box(bm, (0.126, 0.035, 0.028), (0.0, 0.045, -0.135), bevel=0.004, mat_idx=2)

    elif set_idx == 1:
        # Set 1: Sanctified Sabatons (overlapping articulated steel lames, cross ankle cuff, heel spurs)
        for i in range(3):
            add_box(bm, (0.122 - i * 0.006, 0.065, 0.085 - i * 0.008), (0.0, -0.05 - i * 0.045, -0.128 - i * 0.006), bevel=0.008, mat_idx=0 if i != 1 else 2)
        add_box(bm, (0.024, 0.024, 0.09), (0.0, -0.062, -0.045), bevel=0.003, mat_idx=2)

    elif set_idx == 2:
        # Set 2: Ironclad Sabatons (wide bear-paw plated sabatons, brass toe ridges, heavy iron soles)
        add_box(bm, (0.142, 0.26, 0.105), (0.0, -0.06, -0.128), bevel=0.016, mat_idx=0)
        add_box(bm, (0.035, 0.25, 0.025), (0.0, -0.06, -0.075), bevel=0.005, mat_idx=2)
        add_box(bm, (0.148, 0.27, 0.036), (0.0, -0.06, -0.162), bevel=0.005, mat_idx=1)

    else:
        # Set 3: Ash-Walker Treads (cloven bone-talon sabatons, gold ankle shackles, obsidian heels)
        add_cyl(bm, 0.066, 0.066, 0.032, (0.0, 0.0, -0.035), segs=12, mat_idx=2)
        for sx in (-1.0, 1.0):
            add_box(bm, (0.042, 0.095, 0.055), (sx * 0.032, -0.155, -0.145), bevel=0.008, mat_idx=1)
        add_box(bm, (0.118, 0.025, 0.022), (0.0, -0.115, -0.095), bevel=0.003, mat_idx=3)


def export_piece(set_idx: int, slot: str, builder_fn) -> None:
    clear_scene()
    mats = get_set_materials(set_idx)
    mesh = bpy.data.meshes.new(f"Armor_Set{set_idx}_{slot}")
    obj = bpy.data.objects.new(f"Armor_Set{set_idx}_{slot}", mesh)
    bpy.context.collection.objects.link(obj)
    for m in mats:
        obj.data.materials.append(m)

    bm = bmesh.new()
    builder_fn(bm, set_idx)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    bake_3tone_gothic_vertex_colors(obj)

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
    )
    print(f"[5-Slot Armor Builder] Exported: {out_path}")


def main() -> None:
    builders = [
        ("head", build_head_bm),
        ("chest", build_chest_bm),
        ("legs", build_legs_bm),
        ("feet", build_feet_bm),
    ]
    for set_idx in range(4):
        for slot, fn in builders:
            export_piece(set_idx, slot, fn)
    print("[5-Slot Armor Builder] ALL 16 ARMOR GLBs EXPORTED SUCCESSFULLY.")


if __name__ == "__main__":
    main()
