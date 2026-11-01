import sys
import os
import bpy

print("=== STARTING INDEPENDENT M3 (R4) VERIFICATION ===")

OSSUARY_DIR = os.path.abspath("assets/models/ossuary_variety")
DUNGEON_DIR = os.path.abspath("assets/models/dungeon")

target_models = [
    ("ossuary_stone_bridge_4x4.glb", os.path.join(OSSUARY_DIR, "ossuary_stone_bridge_4x4.glb"), "ground"),
    ("ossuary_balcony_railing_4m.glb", os.path.join(OSSUARY_DIR, "ossuary_balcony_railing_4m.glb"), "ground"),
    ("ossuary_buttress_arch_4x4.glb", os.path.join(OSSUARY_DIR, "ossuary_buttress_arch_4x4.glb"), "ground"),
    ("ossuary_bone_chandelier.glb", os.path.join(OSSUARY_DIR, "ossuary_bone_chandelier.glb"), "ground"),
    ("ossuary_spine_reliquary_monolith.glb", os.path.join(OSSUARY_DIR, "ossuary_spine_reliquary_monolith.glb"), "ground"),
    ("ossuary_burial_niche_divider_4x4.glb", os.path.join(OSSUARY_DIR, "ossuary_burial_niche_divider_4x4.glb"), "ground"),
    ("necropolis_wall_armory_4x4.glb", os.path.join(DUNGEON_DIR, "necropolis_wall_armory_4x4.glb"), "wall"),
    ("necropolis_iron_maiden_monolith.glb", os.path.join(DUNGEON_DIR, "necropolis_iron_maiden_monolith.glb"), "ground"),
    ("necropolis_hanging_war_brazier.glb", os.path.join(DUNGEON_DIR, "necropolis_hanging_war_brazier.glb"), "hanging"),
    ("reliquary_wall_grimoire_4x4.glb", os.path.join(DUNGEON_DIR, "reliquary_wall_grimoire_4x4.glb"), "wall"),
    ("reliquary_astral_orrery_monolith.glb", os.path.join(DUNGEON_DIR, "reliquary_astral_orrery_monolith.glb"), "ground"),
    ("reliquary_chandelier_astrolabe.glb", os.path.join(DUNGEON_DIR, "reliquary_chandelier_astrolabe.glb"), "hanging"),
    ("abattoir_wall_furnace_4x4.glb", os.path.join(DUNGEON_DIR, "abattoir_wall_furnace_4x4.glb"), "wall"),
    ("abattoir_blood_press_monolith.glb", os.path.join(DUNGEON_DIR, "abattoir_blood_press_monolith.glb"), "ground"),
    ("abattoir_hanging_hook_rack.glb", os.path.join(DUNGEON_DIR, "abattoir_hanging_hook_rack.glb"), "hanging"),
]

assert len(target_models) == 15, f"Expected 15 models, got {len(target_models)}"

model_stats = {}

for name, path, prop_type in target_models:
    assert os.path.exists(path), f"File missing: {path}"
    size = os.path.getsize(path)
    assert size > 1000000, f"File {name} size {size} is less than 1MB"

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)

    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    total_verts = sum(len(o.data.vertices) for o in objs)
    has_vcol = any(bool(o.data.color_attributes) for o in objs)

    min_co = [float("inf")] * 3
    max_co = [float("-inf")] * 3
    for o in objs:
        for v in o.data.vertices:
            world_co = o.matrix_world @ v.co
            for i in range(3):
                min_co[i] = min(min_co[i], world_co[i])
                max_co[i] = max(max_co[i], world_co[i])

    dims = [round(max_co[i] - min_co[i], 3) for i in range(3)]
    model_stats[name] = {
        "size": size,
        "verts": total_verts,
        "dims": dims,
        "min_co": [round(c, 3) for c in min_co],
        "max_co": [round(c, 3) for c in max_co],
        "vcol": has_vcol,
        "type": prop_type,
    }
    print(f"[{name}] type={prop_type}, size={size}, verts={total_verts}, min_co={model_stats[name]['min_co']}, max_co={model_stats[name]['max_co']}, dims={dims}, vcol={has_vcol}")

# 1. Wall thickness checks (solid 0.50m walls)
# In Blender imported space: walls have width along X, height along Z, and thickness along Y
wall_names = [
    "necropolis_wall_armory_4x4.glb",
    "reliquary_wall_grimoire_4x4.glb",
    "abattoir_wall_furnace_4x4.glb",
]

for wname in wall_names:
    thick = model_stats[wname]["dims"][1]
    print(f"[{wname}] Wall thickness (Y dim): {thick:.3f}m")
    assert thick >= 0.50, f"Wall {wname} thickness {thick:.3f}m is < 0.50m!"

# 2. Origin checks: ceiling vs ground
# In Blender imported space:
# Hanging props should have ceiling contact at Z = 0.0, extending down to negative Z!
hanging_names = [
    "necropolis_hanging_war_brazier.glb",
    "reliquary_chandelier_astrolabe.glb",
    "abattoir_hanging_hook_rack.glb",
]

for hname in hanging_names:
    max_z = model_stats[hname]["max_co"][2]
    min_z = model_stats[hname]["min_co"][2]
    print(f"[{hname}] Hanging prop Z bounds: [{min_z:.3f}, {max_z:.3f}]")
    assert abs(max_z - 0.0) < 0.05, f"Hanging prop {hname} max Z {max_z:.3f} is not at ceiling (0.0)!"
    assert min_z < -1.0, f"Hanging prop {hname} does not hang downwards into -Z space ({min_z:.3f})!"

# Ground props: min Z should be at or near 0.0 (within 0.05m), max Z > 0.5
ground_names = [
    "ossuary_balcony_railing_4m.glb",
    "ossuary_buttress_arch_4x4.glb",
    "ossuary_spine_reliquary_monolith.glb",
    "ossuary_burial_niche_divider_4x4.glb",
    "necropolis_iron_maiden_monolith.glb",
    "reliquary_astral_orrery_monolith.glb",
    "abattoir_blood_press_monolith.glb",
]

for gname in ground_names:
    min_z = model_stats[gname]["min_co"][2]
    max_z = model_stats[gname]["max_co"][2]
    print(f"[{gname}] Ground prop Z bounds: [{min_z:.3f}, {max_z:.3f}]")
    assert abs(min_z - 0.0) < 0.05, f"Ground prop {gname} min Z {min_z:.3f} is not at ground (0.0)!"
    assert max_z > 1.0, f"Ground prop {gname} does not extend upward into +Z space ({max_z:.3f})!"

# ossuary_stone_bridge_4x4.glb: Walkway at Z=0.0, arch rib extends into -Z
bridge_min_z = model_stats["ossuary_stone_bridge_4x4.glb"]["min_co"][2]
bridge_max_z = model_stats["ossuary_stone_bridge_4x4.glb"]["max_co"][2]
print(f"[ossuary_stone_bridge_4x4.glb] Bridge Z bounds: [{bridge_min_z:.3f}, {bridge_max_z:.3f}]")
assert bridge_min_z < -0.8 and bridge_max_z > 0.8, "Bridge does not span above and below deck origin"

# ossuary_bone_chandelier.glb: base at 0.05, candle ring at 0.55m
chand_min_z = model_stats["ossuary_bone_chandelier.glb"]["min_co"][2]
chand_max_z = model_stats["ossuary_bone_chandelier.glb"]["max_co"][2]
print(f"[ossuary_bone_chandelier.glb] Chandelier Z bounds: [{chand_min_z:.3f}, {chand_max_z:.3f}]")
assert abs(chand_min_z - 0.05) < 0.05, f"ossuary_bone_chandelier min Z {chand_min_z:.3f} mismatch"

print("=== M3 (R4) INDEPENDENT VERIFICATION PASSED SUCCESSFULLY ===")
