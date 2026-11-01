import sys
import os
import bpy

print("=== STARTING COMPREHENSIVE ADVERSARIAL AUDIT ===")

models_to_audit = [
    # Wave 1A (16 models)
    "assets/models/church_kit/floor_stone_4x4.glb",
    "assets/models/church_kit/wall_stone_solid.glb",
    "assets/models/church_kit/wall_stone_window.glb",
    "assets/models/church_kit/wall_stone_arch_door.glb",
    "assets/models/church_kit/roof_gothic_vault_4x4.glb",
    "assets/models/church_kit/stairs_stone_4x4.glb",
    "assets/models/church_kit/wall_lantern_sconce.glb",
    "assets/models/church_kit/church_foundation_plinth.glb",
    "assets/models/church_kit/church_front_gable_rose.glb",
    "assets/models/church_kit/church_pitched_roof_12x16.glb",
    "assets/models/church_kit/church_bell_tower_spire.glb",
    "assets/models/church_kit/church_buttress.glb",
    "assets/models/church_kit/hub_weapon_workbench.glb",
    "assets/models/church_kit/hub_armor_reliquary_stand.glb",
    "assets/models/church_kit/hub_sanctuary_upgrade_font.glb",
    "assets/models/architecture/occult_rift_portal.glb",
    # Wave 1B (21 models)
    "assets/models/church_kit/crypt_corridor_vault_4x4.glb",
    "assets/models/church_kit/crypt_wall_ossuary_4x4.glb",
    "assets/models/church_kit/crypt_archway_portcullis_4x4.glb",
    "assets/models/church_kit/crypt_pillar.glb",
    "assets/models/church_kit/crypt_containment_hull.glb",
    "assets/models/church_kit/crypt_iron_gate_cell_4x4.glb",
    "assets/models/church_kit/crypt_drowned_cistern_4x4.glb",
    "assets/models/church_kit/crypt_rotting_bookshelf_4x4.glb",
    "assets/models/church_kit/crypt_altar.glb",
    "assets/models/church_kit/crypt_sarcophagus_ornate.glb",
    "assets/models/church_kit/crypt_lectern_grimoire.glb",
    "assets/models/church_kit/crypt_hanging_cage.glb",
    "assets/models/church_kit/crypt_plague_cauldron.glb",
    "assets/models/church_kit/crypt_weeping_statue_pedestal.glb",
    "assets/models/church_kit/crypt_sunken_bell_crater.glb",
    "assets/models/church_kit/crypt_ritual_obelisk.glb",
    "assets/models/church_kit/standing_iron_brazier.glb",
    "assets/models/church_kit/clutter_ceiling_chains_roots.glb",
    "assets/models/church_kit/clutter_melted_candle_cluster.glb",
    "assets/models/church_kit/clutter_rubble_bones_pile.glb",
    "assets/models/church_kit/clutter_wooden_crates_barrels.glb",
    # Wave 1C (15 models)
    "assets/models/ossuary_variety/ossuary_stone_bridge_4x4.glb",
    "assets/models/ossuary_variety/ossuary_balcony_railing_4m.glb",
    "assets/models/ossuary_variety/ossuary_buttress_arch_4x4.glb",
    "assets/models/ossuary_variety/ossuary_bone_chandelier.glb",
    "assets/models/ossuary_variety/ossuary_spine_reliquary_monolith.glb",
    "assets/models/ossuary_variety/ossuary_burial_niche_divider_4x4.glb",
    "assets/models/dungeon/necropolis_wall_armory_4x4.glb",
    "assets/models/dungeon/necropolis_iron_maiden_monolith.glb",
    "assets/models/dungeon/necropolis_hanging_war_brazier.glb",
    "assets/models/dungeon/reliquary_wall_grimoire_4x4.glb",
    "assets/models/dungeon/reliquary_astral_orrery_monolith.glb",
    "assets/models/dungeon/reliquary_chandelier_astrolabe.glb",
    "assets/models/dungeon/abattoir_wall_furnace_4x4.glb",
    "assets/models/dungeon/abattoir_blood_press_monolith.glb",
    "assets/models/dungeon/abattoir_hanging_hook_rack.glb",
]

print(f"Total models to audit: {len(models_to_audit)}")
assert len(models_to_audit) == 52, f"Expected 52 models, got {len(models_to_audit)}"

findings = []

for rel_path in models_to_audit:
    abs_path = os.path.abspath(rel_path)
    if not os.path.exists(abs_path):
        findings.append(f"MISSING FILE: {rel_path}")
        continue

    size = os.path.getsize(abs_path)
    if size < 1000:
        findings.append(f"EMPTY/CORRUPT FILE (<1KB): {rel_path} ({size} bytes)")
        continue

    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        bpy.ops.import_scene.gltf(filepath=abs_path)
    except Exception as e:
        findings.append(f"GLTF IMPORT CRASH: {rel_path}: {e}")
        continue

    mesh_objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not mesh_objs:
        findings.append(f"NO MESH OBJECTS: {rel_path}")
        continue

    for o in mesh_objs:
        # Check vertex count
        vc = len(o.data.vertices)
        if vc == 0:
            findings.append(f"EMPTY MESH: {rel_path} - object {o.name}")
        # Check materials
        mats = [slot.material for slot in o.material_slots if slot.material]
        if not mats:
            findings.append(f"NO MATERIALS: {rel_path} - object {o.name}")
        # Check vertex color
        if not o.data.color_attributes:
            findings.append(f"NO VERTEX COLOR: {rel_path} - object {o.name}")

print(f"Audited {len(models_to_audit)} models.")
if findings:
    print(f"FAILED with {len(findings)} findings:")
    for f in findings:
        print(" - " + f)
else:
    print("ALL 52 MODELS PASSED STRUCTURAL INTEGRITY AUDIT!")
