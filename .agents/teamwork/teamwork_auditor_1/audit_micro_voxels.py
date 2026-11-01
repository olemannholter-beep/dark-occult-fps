import os
import sys
import json
import struct
import numpy as np

WORKSPACE = r"c:\Users\olema\Downloads\alpha branch"

# Target 76 GLB files across all 5 waves
WAVE_MODELS = {
    "Wave 1A (Church & Hub)": [
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
    ],
    "Wave 1B (Crypt & Clutter)": [
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
    ],
    "Wave 1C (Ossuary & Biomes 2-4)": [
        "assets/models/ossuary_variety/ossuary_balcony_railing_4m.glb",
        "assets/models/ossuary_variety/ossuary_bone_chandelier.glb",
        "assets/models/ossuary_variety/ossuary_burial_niche_divider_4x4.glb",
        "assets/models/ossuary_variety/ossuary_buttress_arch_4x4.glb",
        "assets/models/ossuary_variety/ossuary_spine_reliquary_monolith.glb",
        "assets/models/ossuary_variety/ossuary_stone_bridge_4x4.glb",
        "assets/models/dungeon/abattoir_blood_press_monolith.glb",
        "assets/models/dungeon/abattoir_hanging_hook_rack.glb",
        "assets/models/dungeon/abattoir_wall_furnace_4x4.glb",
        "assets/models/dungeon/necropolis_hanging_war_brazier.glb",
        "assets/models/dungeon/necropolis_iron_maiden_monolith.glb",
        "assets/models/dungeon/necropolis_wall_armory_4x4.glb",
        "assets/models/dungeon/reliquary_astral_orrery_monolith.glb",
        "assets/models/dungeon/reliquary_chandelier_astrolabe.glb",
        "assets/models/dungeon/reliquary_wall_grimoire_4x4.glb",
    ],
    "Wave 1D (Town, Terrain & Loot)": [
        "assets/models/church_kit/town_gravestone_cluster.glb",
        "assets/models/church_kit/town_graveyard_wall_fence_6m.glb",
        "assets/models/church_kit/town_road_curb_8m.glb",
        "assets/models/church_kit/town_street_lamp_iron.glb",
        "assets/models/house_abandoned_a.glb",
        "assets/models/house_abandoned_b.glb",
        "assets/models/dead_tree_gnarled.glb",
        "assets/models/grass_clump_wild.glb",
        "assets/models/terrain_town.glb",
        "assets/models/items/loot_alchemical_elixir.glb",
        "assets/models/items/loot_blood_echo_cluster.glb",
        "assets/models/items/loot_occult_relic_talisman.glb",
        "assets/models/items/prop_gothic_reliquary_chest.glb",
    ],
    "Wave 1E (11 Enemies & Bosses)": [
        "assets/models/enemies/enemy_ossuary_skeleton.glb",
        "assets/models/enemies/enemy_plague_acolyte.glb",
        "assets/models/enemies/enemy_iron_penitent.glb",
        "assets/models/enemies/enemy_01_ossuary_executioner.glb",
        "assets/models/enemies/enemy_02_necropolis_praetorian.glb",
        "assets/models/enemies/enemy_03_reliquary_hexweaver.glb",
        "assets/models/enemies/enemy_04_inquisitor_rackmaster.glb",
        "assets/models/enemies/enemy_05_plague_bloater.glb",
        "assets/models/enemies/enemy_06_weeping_banshee.glb",
        "assets/models/enemies/enemy_07_bell_juggernaut.glb",
        "assets/models/enemies/enemy_08_abyssal_archon.glb",
    ],
}

def parse_glb(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    if len(data) < 12:
        return False, "File too small (< 12 bytes)", None, None
    magic, version, length = struct.unpack("<4sII", data[:12])
    if magic != b"glTF":
        return False, f"Invalid magic {magic}, expected b'glTF'", None, None
    if version != 2:
        return False, f"Invalid version {version}, expected 2", None, None
    if length != len(data):
        return False, f"Header length {length} != actual byte length {len(data)}", None, None

    # Parse Chunk 0 (JSON)
    pos = 12
    chunk0_len, chunk0_type = struct.unpack("<II", data[pos:pos+8])
    pos += 8
    if chunk0_type != 0x4E4F534A: # 'JSON'
        return False, f"Invalid chunk 0 type {chunk0_type:08x}, expected JSON", None, None
    json_bytes = data[pos:pos+chunk0_len]
    pos += chunk0_len
    gltf_json = json.loads(json_bytes.decode("utf-8"))

    # Parse Chunk 1 (BIN) if present
    bin_data = None
    if pos < len(data):
        chunk1_len, chunk1_type = struct.unpack("<II", data[pos:pos+8])
        pos += 8
        if chunk1_type == 0x004E4942: # 'BIN\0'
            bin_data = data[pos:pos+chunk1_len]

    return True, "Valid glTF 2.0 binary", gltf_json, bin_data

def audit_models():
    print("=" * 80)
    print("AUDIT 1: MODEL INVENTORY & GLTF 2.0 BINARY INTEGRITY AUDIT")
    print("=" * 80)
    total_checked = 0
    passed = 0
    failed = 0
    failures = []

    for wave_name, rel_paths in WAVE_MODELS.items():
        print(f"\n--- {wave_name} ({len(rel_paths)} models) ---")
        for rel in rel_paths:
            total_checked += 1
            full_path = os.path.join(WORKSPACE, rel)
            if not os.path.exists(full_path):
                print(f"[FAIL MISSING] {rel}")
                failed += 1
                failures.append((rel, "Missing on disk"))
                continue
            sz = os.path.getsize(full_path)
            if sz < 1000:
                print(f"[FAIL TRIVIAL] {rel} (size={sz} bytes)")
                failed += 1
                failures.append((rel, f"Trivially small size: {sz} bytes"))
                continue
            valid, msg, gltf_json, bin_data = parse_glb(full_path)
            if not valid:
                print(f"[FAIL CORRUPT] {rel} ({msg})")
                failed += 1
                failures.append((rel, msg))
                continue

            # Check nodes and primitives
            node_names = [n.get("name", "") for n in gltf_json.get("nodes", [])]
            mesh_count = len(gltf_json.get("meshes", []))
            has_color = False
            vert_count = 0
            for m in gltf_json.get("meshes", []):
                for p in m.get("primitives", []):
                    attrs = p.get("attributes", {})
                    if "COLOR_0" in attrs:
                        has_color = True
                    if "POSITION" in attrs:
                        pos_acc_idx = attrs["POSITION"]
                        pos_acc = gltf_json["accessors"][pos_acc_idx]
                        vert_count += pos_acc.get("count", 0)

            print(f"[PASS] {os.path.basename(rel):<35} | {sz:>10,} bytes | nodes={len(node_names):>2} | meshes={mesh_count:>2} | verts={vert_count:>6,} | color={has_color}")
            passed += 1

    print(f"\nModel Inventory Summary: Total={total_checked}, Passed={passed}, Failed={failed}")
    return failures

if __name__ == "__main__":
    failures = audit_models()
    if failures:
        print(f"FAILED with {len(failures)} errors!")
        sys.exit(1)
    else:
        print("ALL MODELS PASSED INVENTORY AUDIT!")
