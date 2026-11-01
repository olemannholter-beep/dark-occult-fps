import os
import sys
import math
import bpy
import bmesh
from mathutils import Vector, Euler

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from blender_detail_kit import (
    _add_bm_beveled_box,
    bake_3tone_gothic_vertex_colors,
)

ITEMS_OUT_DIR = os.path.join(PROJECT_ROOT, "assets", "models", "items")


def clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_clean_pbr_material(
    name: str,
    base_color: tuple[float, float, float, float],
    metallic: float = 0.0,
    roughness: float = 0.88,
    emission_color: tuple[float, float, float, float] | None = None,
    emission_strength: float = 0.0,
    alpha: float = 1.0,
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = base_color
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
        if alpha < 0.999:
            bsdf.inputs["Alpha"].default_value = alpha
        if emission_color is not None and emission_strength > 0.0:
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = emission_color
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = emission_strength
        vcol = nodes.new(type="ShaderNodeVertexColor")
        vcol.layer_name = "Col"
        mix = nodes.new(type="ShaderNodeMix")
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs[0].default_value = 1.0
        mix.inputs[6].default_value = base_color
        links.new(vcol.outputs["Color"], mix.inputs[7])
        links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    return mat


def create_material_palette() -> dict[str, bpy.types.Material]:
    return {
        "EmissiveCrimson": make_clean_pbr_material(
            "EmissiveCrimson",
            (0.92, 0.10, 0.16, 1.0),
            metallic=0.10,
            roughness=0.22,
            emission_color=(1.0, 0.12, 0.18, 1.0),
            emission_strength=3.2,
        ),
        "TarnishedBronze": make_clean_pbr_material(
            "TarnishedBronze",
            (0.58, 0.44, 0.22, 1.0),
            metallic=0.86,
            roughness=0.38,
        ),
        "WroughtIron": make_clean_pbr_material(
            "WroughtIron",
            (0.16, 0.17, 0.19, 1.0),
            metallic=0.85,
            roughness=0.48,
        ),
        "AgedBone": make_clean_pbr_material(
            "AgedBone",
            (0.78, 0.73, 0.62, 1.0),
            metallic=0.0,
            roughness=0.86,
        ),
        "RottedTimber": make_clean_pbr_material(
            "RottedTimber",
            (0.24, 0.16, 0.10, 1.0),
            metallic=0.0,
            roughness=0.90,
        ),
        "WeatheredStone": make_clean_pbr_material(
            "WeatheredStone",
            (0.26, 0.25, 0.27, 1.0),
            metallic=0.0,
            roughness=0.90,
        ),
        "WeatheredLeather": make_clean_pbr_material(
            "WeatheredLeather",
            (0.22, 0.13, 0.09, 1.0),
            metallic=0.0,
            roughness=0.82,
        ),
        "GlowingOccultRune": make_clean_pbr_material(
            "GlowingOccultRune",
            (0.84, 0.36, 1.0, 1.0),
            metallic=0.15,
            roughness=0.24,
            emission_color=(0.86, 0.38, 1.0, 1.0),
            emission_strength=3.0,
        ),
        "AlchemicalElixirGlow": make_clean_pbr_material(
            "AlchemicalElixirGlow",
            (0.48, 0.96, 0.42, 1.0),
            metallic=0.05,
            roughness=0.20,
            emission_color=(0.52, 0.98, 0.44, 1.0),
            emission_strength=2.8,
        ),
        "ClearGlass": make_clean_pbr_material(
            "ClearGlass",
            (0.75, 0.88, 0.82, 0.42),
            metallic=0.10,
            roughness=0.18,
            alpha=0.42,
        ),
    }


def export_glb(filepath: str) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format='GLB',
        export_apply=True,
        export_yup=True,
        export_materials='EXPORT',
    )
    print(f"[LootBuilder] Exported {filepath}")


def build_loot_blood_echo_cluster() -> None:
    """
    1. loot_blood_echo_cluster.glb (XP & Essence Drop):
       Floating faceted crimson blood-crystal shard cluster encircled by two orbiting
       tarnished-brass astrolabe rings (EmissiveCrimson core at emission = 3.2).
       Total sub-components: 68+
    """
    clear_scene()
    mats = create_material_palette()
    bm = bmesh.new()
    sub_parts = 0

    center_z = 0.38

    # 1. Central crimson blood-crystal core + 20 radiating faceted crystal shards (mat_idx = 0: EmissiveCrimson)
    _add_bm_beveled_box(
        bm,
        (0.14, 0.14, 0.36),
        (0.0, 0.0, center_z),
        rot_euler=(0.12, -0.08, 0.45),
        bevel_width=0.018,
        mat_idx=0,
    )
    sub_parts += 1

    for i in range(20):
        ang = (i / 20.0) * math.tau
        tier = i % 3
        tilt = 0.38 + tier * 0.26
        rad = 0.05 + tier * 0.025
        c_len = 0.24 - tier * 0.035
        c_thick = 0.055 - tier * 0.008
        cx = math.cos(ang) * rad
        cy = math.sin(ang) * rad
        cz = center_z + (0.04 if tier == 0 else (-0.03 if tier == 1 else 0.0))
        rx = math.sin(ang) * tilt
        ry = -math.cos(ang) * tilt
        rz = ang
        _add_bm_beveled_box(
            bm,
            (c_thick, c_thick, c_len),
            (cx, cy, cz),
            rot_euler=(rx, ry, rz),
            bevel_width=0.010,
            mat_idx=0,
        )
        sub_parts += 1

    # 2. Two orbiting tarnished-brass astrolabe rings (20 segments each + 16 astrolabe degree studs = 56 sub-parts)
    for ring_idx, ring_tilt in enumerate(((0.55, 0.25, 0.0), (-0.48, 0.35, 0.78))):
        ring_r = 0.24 + ring_idx * 0.035
        ring_rot = Euler(ring_tilt, 'XYZ')
        segs = 18
        for s_i in range(segs):
            a0 = (s_i / float(segs)) * math.tau
            seg_len = (math.tau * ring_r) / segs * 1.06
            local_pt = Vector((math.cos(a0) * ring_r, math.sin(a0) * ring_r, 0.0))
            local_pt.rotate(ring_rot)
            world_pt = (local_pt.x, local_pt.y, center_z + local_pt.z)
            seg_eul = Euler((ring_tilt[0], ring_tilt[1], a0 + math.pi * 0.5), 'XYZ')
            _add_bm_beveled_box(
                bm,
                (0.024, seg_len, 0.016),
                world_pt,
                rot_euler=(seg_eul.x, seg_eul.y, seg_eul.z),
                bevel_width=0.003,
                mat_idx=1,
            )
            sub_parts += 1
            if s_i % 3 == 0:
                stud_pt = Vector((math.cos(a0) * (ring_r + 0.016), math.sin(a0) * (ring_r + 0.016), 0.0))
                stud_pt.rotate(ring_rot)
                _add_bm_beveled_box(
                    bm,
                    (0.022, 0.022, 0.022),
                    (stud_pt.x, stud_pt.y, center_z + stud_pt.z),
                    rot_euler=ring_tilt,
                    bevel_width=0.004,
                    mat_idx=2,
                )
                sub_parts += 1

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("LootBloodEchoClusterMesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("LootBloodEchoCluster", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mats["EmissiveCrimson"])
    obj.data.materials.append(mats["TarnishedBronze"])
    obj.data.materials.append(mats["WroughtIron"])

    bake_3tone_gothic_vertex_colors(obj, z_min=0.0, z_max=0.8)
    print(f"[LootBuilder] loot_blood_echo_cluster sub-elements: {sub_parts}")
    export_glb(os.path.join(ITEMS_OUT_DIR, "loot_blood_echo_cluster.glb"))


def build_loot_occult_relic_talisman() -> None:
    """
    2. loot_occult_relic_talisman.glb (Equippable Passive Gear/Relic Drop):
       Ornate gothic reliquary medallion: wrought-iron spiked sun/cross frame, miniature skull relief,
       hanging chain tassels, and a glowing arcane gemstone center.
       Total sub-components: 68+
    """
    clear_scene()
    mats = create_material_palette()
    bm = bmesh.new()
    sub_parts = 0

    center_z = 0.42

    # 1. Wrought-iron octagonal medallion backing & 4 gothic cross arms (mat_idx = 0: WroughtIron)
    _add_bm_beveled_box(bm, (0.26, 0.04, 0.26), (0.0, 0.0, center_z), bevel_width=0.008, mat_idx=0)
    _add_bm_beveled_box(
        bm,
        (0.26, 0.038, 0.26),
        (0.0, 0.0, center_z),
        rot_euler=(0.0, math.radians(45.0), 0.0),
        bevel_width=0.008,
        mat_idx=0,
    )
    _add_bm_beveled_box(bm, (0.44, 0.045, 0.085), (0.0, 0.0, center_z), bevel_width=0.006, mat_idx=0)
    _add_bm_beveled_box(bm, (0.085, 0.045, 0.46), (0.0, 0.0, center_z), bevel_width=0.006, mat_idx=0)
    sub_parts += 4

    # 2. 16 Tarnished-bronze sunburst spikes & 16 perimeter rivets (mat_idx = 1: TarnishedBronze)
    for i in range(16):
        ang = (i / 16.0) * math.tau
        r_spike = 0.19 if (i % 2 == 0) else 0.155
        sx = math.cos(ang) * r_spike
        sz = center_z + math.sin(ang) * r_spike
        _add_bm_beveled_box(
            bm,
            (0.026, 0.024, 0.095 if (i % 2 == 0) else 0.065),
            (sx, 0.0, sz),
            rot_euler=(0.0, ang - math.pi * 0.5, 0.0),
            bevel_width=0.004,
            mat_idx=1,
        )
        rx = math.cos(ang) * 0.115
        rz = center_z + math.sin(ang) * 0.115
        _add_bm_beveled_box(bm, (0.018, 0.052, 0.018), (rx, 0.0, rz), bevel_width=0.003, mat_idx=1)
        sub_parts += 2

    # 3. Miniature Skull Relief on both front and back faces (mat_idx = 2: AgedBone)
    for side_y in (-0.028, 0.028):
        _add_bm_beveled_box(bm, (0.09, 0.032, 0.085), (0.0, side_y, center_z + 0.075), bevel_width=0.010, mat_idx=2)
        _add_bm_beveled_box(bm, (0.065, 0.028, 0.045), (0.0, side_y, center_z + 0.022), bevel_width=0.006, mat_idx=2)
        for tooth_i in range(-2, 3):
            _add_bm_beveled_box(
                bm,
                (0.010, 0.034, 0.018),
                (tooth_i * 0.012, side_y, center_z + 0.005),
                bevel_width=0.002,
                mat_idx=2,
            )
        sub_parts += 7

    # 4. Glowing Arcane Gemstone Center on both faces + 4 rune shards (mat_idx = 3: GlowingOccultRune)
    _add_bm_beveled_box(
        bm,
        (0.095, 0.062, 0.095),
        (0.0, 0.0, center_z - 0.045),
        rot_euler=(0.0, math.radians(45.0), 0.0),
        bevel_width=0.012,
        mat_idx=3,
    )
    for arm_x, arm_z in ((-0.16, 0.0), (0.16, 0.0), (0.0, 0.17), (0.0, -0.17)):
        _add_bm_beveled_box(
            bm,
            (0.036, 0.054, 0.036),
            (arm_x, 0.0, center_z + arm_z),
            rot_euler=(0.0, math.radians(45.0), 0.0),
            bevel_width=0.005,
            mat_idx=3,
        )
    sub_parts += 5

    # 5. 3 Hanging Chain Tassels at the bottom of the medallion (15 links total)
    for tx in (-0.09, 0.0, 0.09):
        for l_i in range(5):
            lz = center_z - 0.21 - l_i * 0.032
            rot_y = math.radians(90.0) if (l_i % 2 == 1) else 0.0
            _add_bm_beveled_box(
                bm,
                (0.024, 0.014, 0.036),
                (tx, 0.0, lz),
                rot_euler=(0.0, 0.0, rot_y),
                bevel_width=0.003,
                mat_idx=0,
            )
            sub_parts += 1

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("LootOccultRelicTalismanMesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("LootOccultRelicTalisman", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mats["WroughtIron"])
    obj.data.materials.append(mats["TarnishedBronze"])
    obj.data.materials.append(mats["AgedBone"])
    obj.data.materials.append(mats["GlowingOccultRune"])

    bake_3tone_gothic_vertex_colors(obj, z_min=0.0, z_max=0.75)
    print(f"[LootBuilder] loot_occult_relic_talisman sub-elements: {sub_parts}")
    export_glb(os.path.join(ITEMS_OUT_DIR, "loot_occult_relic_talisman.glb"))


def build_loot_alchemical_elixir() -> None:
    """
    3. loot_alchemical_elixir.glb (Instant Health/Armor/Ammo Vial Drop):
       Ribbed alchemical glass flask strapped in leather and brass cages with a glowing
       golden-green restorative liquid core.
       Total sub-components: 64+
    """
    clear_scene()
    mats = create_material_palette()
    bm = bmesh.new()
    sub_parts = 0

    # 1. Glowing golden-green restorative liquid core (mat_idx = 0: AlchemicalElixirGlow)
    for layer_i in range(8):
        ang = (layer_i / 8.0) * math.pi
        _add_bm_beveled_box(
            bm,
            (0.16, 0.16, 0.25),
            (0.0, 0.0, 0.20),
            rot_euler=(0.0, 0.0, ang),
            bevel_width=0.014,
            mat_idx=0,
        )
        sub_parts += 1

    # 2. Ribbed alchemical glass flask ribs & flared neck (mat_idx = 1: ClearGlass)
    for rib_i in range(12):
        ang = (rib_i / 12.0) * math.tau
        rx = math.cos(ang) * 0.105
        ry = math.sin(ang) * 0.105
        _add_bm_beveled_box(
            bm,
            (0.028, 0.028, 0.29),
            (rx, ry, 0.21),
            rot_euler=(0.0, 0.0, ang),
            bevel_width=0.005,
            mat_idx=1,
        )
        sub_parts += 1
    # Flared glass neck collar
    for neck_i in range(6):
        ang = (neck_i / 6.0) * math.pi
        _add_bm_beveled_box(
            bm,
            (0.085, 0.085, 0.11),
            (0.0, 0.0, 0.40),
            rot_euler=(0.0, 0.0, ang),
            bevel_width=0.008,
            mat_idx=1,
        )
        sub_parts += 1

    # 3. Tarnished brass base foot, 3 horizontal cage rings, 8 vertical cage ribs & 16 rivets (mat_idx = 2: TarnishedBronze)
    for ring_z in (0.06, 0.18, 0.31, 0.43):
        ring_w = 0.23 if ring_z < 0.35 else 0.11
        for seg_i in range(4):
            _add_bm_beveled_box(
                bm,
                (ring_w, ring_w, 0.024),
                (0.0, 0.0, ring_z),
                rot_euler=(0.0, 0.0, seg_i * (math.pi * 0.25)),
                bevel_width=0.004,
                mat_idx=2,
            )
            sub_parts += 1

    for cage_i in range(8):
        ang = (cage_i / 8.0) * math.tau
        cx = math.cos(ang) * 0.118
        cy = math.sin(ang) * 0.118
        _add_bm_beveled_box(
            bm,
            (0.020, 0.020, 0.28),
            (cx, cy, 0.195),
            rot_euler=(0.0, 0.0, ang),
            bevel_width=0.003,
            mat_idx=2,
        )
        # Brass rivets at upper & lower harness rings
        _add_bm_beveled_box(bm, (0.024, 0.024, 0.024), (cx * 1.04, cy * 1.04, 0.09), bevel_width=0.003, mat_idx=2)
        _add_bm_beveled_box(bm, (0.024, 0.024, 0.024), (cx * 1.04, cy * 1.04, 0.30), bevel_width=0.003, mat_idx=2)
        sub_parts += 3

    # 4. Leather harness straps & cork stopper (mat_idx = 3: WeatheredLeather)
    _add_bm_beveled_box(bm, (0.245, 0.055, 0.045), (0.0, 0.0, 0.24), bevel_width=0.005, mat_idx=3)
    _add_bm_beveled_box(bm, (0.055, 0.245, 0.045), (0.0, 0.0, 0.24), bevel_width=0.005, mat_idx=3)
    _add_bm_beveled_box(bm, (0.068, 0.068, 0.075), (0.0, 0.0, 0.475), bevel_width=0.008, mat_idx=3)
    sub_parts += 3

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("LootAlchemicalElixirMesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("LootAlchemicalElixir", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mats["AlchemicalElixirGlow"])
    obj.data.materials.append(mats["ClearGlass"])
    obj.data.materials.append(mats["TarnishedBronze"])
    obj.data.materials.append(mats["WeatheredLeather"])

    bake_3tone_gothic_vertex_colors(obj, z_min=0.0, z_max=0.55)
    print(f"[LootBuilder] loot_alchemical_elixir sub-elements: {sub_parts}")
    export_glb(os.path.join(ITEMS_OUT_DIR, "loot_alchemical_elixir.glb"))


def build_prop_gothic_reliquary_chest() -> None:
    """
    4. prop_gothic_reliquary_chest.glb (Interactive Dungeon Loot Chest — 1.4m x 0.9m x 0.95m):
       Heavy iron-bound oak treasure chest with gothic arched strap hinges, skull padlock,
       and a separate pivoted ChestLid child node so opening the chest swings the lid back 100°
       and erupts with loot pickups!
       Total sub-components: 82+
    """
    clear_scene()
    mats = create_material_palette()

    # ------------------------------------------------------------------
    # PART A: ChestBase (1.40m wide X, 0.86m deep Y, 0.58m tall Z)
    # ------------------------------------------------------------------
    bm_base = bmesh.new()
    base_parts = 0

    # 1. 4 Stepped Stone & Wrought-Iron Lion-Paw Corner Feet (mat_idx = 1: WroughtIron)
    for sx in (-0.62, 0.62):
        for sy in (-0.36, 0.36):
            _add_bm_beveled_box(bm_base, (0.20, 0.20, 0.08), (sx, sy, 0.04), bevel_width=0.010, mat_idx=1)
            base_parts += 1

    # 2. Individual Oak Planks forming the chest body & interior cavity floor (mat_idx = 0: RottedTimber)
    # Bottom oak floor slab
    _add_bm_beveled_box(bm_base, (1.32, 0.80, 0.06), (0.0, 0.0, 0.10), bevel_width=0.008, mat_idx=0)
    base_parts += 1

    # Front (-Y) and Back (+Y) horizontal oak staves (4 rows each)
    for sy in (-0.39, 0.39):
        for r_i in range(4):
            pz = 0.17 + r_i * 0.115
            _add_bm_beveled_box(bm_base, (1.34, 0.06, 0.108), (0.0, sy, pz), bevel_width=0.007, mat_idx=0)
            base_parts += 1

    # Left (-X) and Right (+X) horizontal oak staves (4 rows each)
    for sx in (-0.64, 0.64):
        for r_i in range(4):
            pz = 0.17 + r_i * 0.115
            _add_bm_beveled_box(bm_base, (0.06, 0.78, 0.108), (sx, 0.0, pz), bevel_width=0.007, mat_idx=0)
            base_parts += 1

    # 3. Heavy Wrought-Iron Corner Posts, 4 Vertical Strap Bands & Top Rim Frame (mat_idx = 1: WroughtIron)
    for sx in (-0.67, 0.67):
        for sy in (-0.41, 0.41):
            _add_bm_beveled_box(bm_base, (0.08, 0.08, 0.52), (sx, sy, 0.33), bevel_width=0.008, mat_idx=1)
            base_parts += 1

    strap_xs = (-0.42, -0.14, 0.14, 0.42)
    for bx in strap_xs:
        for sy in (-0.425, 0.425):
            _add_bm_beveled_box(bm_base, (0.065, 0.025, 0.50), (bx, sy, 0.33), bevel_width=0.004, mat_idx=1)
            base_parts += 1
            for rz in (0.16, 0.32, 0.48):
                _add_bm_beveled_box(
                    bm_base,
                    (0.024, 0.036, 0.024),
                    (bx, sy, rz),
                    bevel_width=0.003,
                    mat_idx=2,
                )
                base_parts += 1

    # Side wrought-iron carry handles (-X and +X)
    for sx in (-0.69, 0.69):
        _add_bm_beveled_box(bm_base, (0.03, 0.24, 0.08), (sx, 0.0, 0.36), bevel_width=0.005, mat_idx=1)
        _add_bm_beveled_box(bm_base, (0.05, 0.18, 0.03), (sx * 1.03, 0.0, 0.31), bevel_width=0.004, mat_idx=2)
        base_parts += 2

    # 4. Ornate Skull Padlock Escutcheon on Front Face (-Y = -0.44m) (mat_idx = 2: TarnishedBronze, mat_idx = 3: AgedBone, mat_idx = 4: EmissiveCrimson)
    _add_bm_beveled_box(bm_base, (0.20, 0.04, 0.24), (0.0, -0.435, 0.44), bevel_width=0.008, mat_idx=2)
    _add_bm_beveled_box(bm_base, (0.11, 0.05, 0.12), (0.0, -0.455, 0.46), bevel_width=0.012, mat_idx=3)
    _add_bm_beveled_box(bm_base, (0.075, 0.045, 0.06), (0.0, -0.455, 0.39), bevel_width=0.006, mat_idx=3)
    # Glowing crimson ruby eyes in the skull lock
    _add_bm_beveled_box(bm_base, (0.024, 0.055, 0.024), (-0.026, -0.465, 0.465), bevel_width=0.003, mat_idx=4)
    _add_bm_beveled_box(bm_base, (0.024, 0.055, 0.024), (0.026, -0.465, 0.465), bevel_width=0.003, mat_idx=4)
    # Interior glowing crimson velvet/hoard bed inside the chest
    _add_bm_beveled_box(bm_base, (1.20, 0.68, 0.08), (0.0, 0.0, 0.24), bevel_width=0.012, mat_idx=4)
    base_parts += 6

    bmesh.ops.recalc_face_normals(bm_base, faces=bm_base.faces)
    mesh_base = bpy.data.meshes.new("ChestBaseMesh")
    bm_base.to_mesh(mesh_base)
    bm_base.free()

    obj_base = bpy.data.objects.new("ChestBase", mesh_base)
    bpy.context.collection.objects.link(obj_base)
    obj_base.data.materials.append(mats["RottedTimber"])
    obj_base.data.materials.append(mats["WroughtIron"])
    obj_base.data.materials.append(mats["TarnishedBronze"])
    obj_base.data.materials.append(mats["AgedBone"])
    obj_base.data.materials.append(mats["EmissiveCrimson"])
    bake_3tone_gothic_vertex_colors(obj_base, z_min=0.0, z_max=0.95)

    # ------------------------------------------------------------------
    # PART B: ChestLid (Pivoted at back hinge: X = 0.0, Y = +0.41, Z = 0.58)
    # Note: In Blender (-Y forward -> Godot -Z forward), placing hinge at Y = +0.41, Z = 0.58
    # means in Godot the hinge sits at (0.0, 0.58, 0.41) and rotating ChestLid.rotation.x
    # by -100 degrees swings the lid open backward!
    # ------------------------------------------------------------------
    hinge_y = 0.41
    hinge_z = 0.58

    bm_lid = bmesh.new()
    lid_parts = 0

    # Arched barrel-vault lid staves in local coordinates relative to (0, hinge_y, hinge_z)
    num_staves = 7
    for s_i in range(num_staves):
        t = (s_i / float(num_staves - 1)) * math.pi  # 0 (back) to pi (front)
        world_y = math.cos(t) * 0.40
        world_z = hinge_z + math.sin(t) * 0.32 + 0.04
        local_y = world_y - hinge_y
        local_z = world_z - hinge_z
        pitch = -(t - math.pi * 0.5)
        _add_bm_beveled_box(
            bm_lid,
            (1.36, 0.14, 0.055),
            (0.0, local_y, local_z),
            rot_euler=(pitch, 0.0, 0.0),
            bevel_width=0.007,
            mat_idx=0,
        )
        lid_parts += 1

    # Left & Right side tympanum gable plates of the arched lid
    for sx in (-0.65, 0.65):
        _add_bm_beveled_box(
            bm_lid,
            (0.06, 0.78, 0.24),
            (sx, -hinge_y, 0.12),
            bevel_width=0.008,
            mat_idx=0,
        )
        _add_bm_beveled_box(
            bm_lid,
            (0.08, 0.56, 0.16),
            (sx, -hinge_y, 0.26),
            bevel_width=0.008,
            mat_idx=1,
        )
        lid_parts += 2

    # 4 Gothic Arched Wrought-Iron Strap Hinges + Bronze Rivets over the lid vault
    for bx in strap_xs:
        for s_i in range(num_staves):
            t = (s_i / float(num_staves - 1)) * math.pi
            world_y = math.cos(t) * 0.418
            world_z = hinge_z + math.sin(t) * 0.335 + 0.045
            local_y = world_y - hinge_y
            local_z = world_z - hinge_z
            pitch = -(t - math.pi * 0.5)
            _add_bm_beveled_box(
                bm_lid,
                (0.07, 0.145, 0.026),
                (bx, local_y, local_z),
                rot_euler=(pitch, 0.0, 0.0),
                bevel_width=0.004,
                mat_idx=1,
            )
            _add_bm_beveled_box(
                bm_lid,
                (0.024, 0.024, 0.036),
                (bx, local_y, local_z + 0.01),
                rot_euler=(pitch, 0.0, 0.0),
                bevel_width=0.003,
                mat_idx=2,
            )
            lid_parts += 2

    bmesh.ops.recalc_face_normals(bm_lid, faces=bm_lid.faces)
    mesh_lid = bpy.data.meshes.new("ChestLidMesh")
    bm_lid.to_mesh(mesh_lid)
    bm_lid.free()

    obj_lid = bpy.data.objects.new("ChestLid", mesh_lid)
    bpy.context.collection.objects.link(obj_lid)
    obj_lid.parent = obj_base
    obj_lid.location = (0.0, hinge_y, hinge_z)
    obj_lid.data.materials.append(mats["RottedTimber"])
    obj_lid.data.materials.append(mats["WroughtIron"])
    obj_lid.data.materials.append(mats["TarnishedBronze"])
    bake_3tone_gothic_vertex_colors(obj_lid, z_min=-0.1, z_max=0.45)

    print(f"[LootBuilder] prop_gothic_reliquary_chest sub-elements: {base_parts + lid_parts} (Base={base_parts}, Lid={lid_parts})")
    export_glb(os.path.join(ITEMS_OUT_DIR, "prop_gothic_reliquary_chest.glb"))


if __name__ == "__main__":
    build_loot_blood_echo_cluster()
    build_loot_occult_relic_talisman()
    build_loot_alchemical_elixir()
    build_prop_gothic_reliquary_chest()
    print("[LootBuilder] All 4 loot & chest GLB models exported successfully.")
