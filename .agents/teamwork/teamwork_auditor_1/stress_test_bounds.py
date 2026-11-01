import os
import sys
import numpy as np
from audit_deep_inspection import parse_glb, get_accessor_data

WORKSPACE = r"c:\Users\olema\Downloads\alpha branch"

MODULAR_MODELS = [
    ("assets/models/church_kit/floor_stone_4x4.glb", 4.0, 4.0, 0.4),
    ("assets/models/church_kit/wall_stone_solid.glb", 4.0, 4.0, 0.6),
    ("assets/models/church_kit/wall_stone_window.glb", 4.0, 4.0, 0.6),
    ("assets/models/church_kit/wall_stone_arch_door.glb", 4.0, 4.0, 0.6),
    ("assets/models/church_kit/roof_gothic_vault_4x4.glb", 4.0, 4.0, 1.2),
    ("assets/models/church_kit/stairs_stone_4x4.glb", 4.0, 4.0, 5.0),
    ("assets/models/church_kit/crypt_wall_ossuary_4x4.glb", 4.0, 4.0, 0.6),
    ("assets/models/church_kit/crypt_archway_portcullis_4x4.glb", 4.0, 4.0, 0.6),
    ("assets/models/church_kit/crypt_iron_gate_cell_4x4.glb", 4.0, 4.0, 0.6),
    ("assets/models/church_kit/crypt_rotting_bookshelf_4x4.glb", 4.0, 4.0, 0.7),
    ("assets/models/ossuary_variety/ossuary_burial_niche_divider_4x4.glb", 4.0, 4.0, 0.6),
    ("assets/models/ossuary_variety/ossuary_buttress_arch_4x4.glb", 4.0, 4.0, 1.5),
    ("assets/models/ossuary_variety/ossuary_stone_bridge_4x4.glb", 4.0, 4.0, 2.5),
    ("assets/models/dungeon/abattoir_wall_furnace_4x4.glb", 4.0, 4.0, 0.6),
    ("assets/models/dungeon/necropolis_wall_armory_4x4.glb", 4.0, 4.0, 0.6),
    ("assets/models/dungeon/reliquary_wall_grimoire_4x4.glb", 4.0, 4.0, 0.6),
]

def stress_test_modular_bounds():
    print("=" * 80)
    print("STRESS TEST: MODULAR ARCHITECTURE BOUNDING BOXES & CLEARANCES")
    print("=" * 80)
    for rel, exp_x, exp_y_or_z, exp_thick in MODULAR_MODELS:
        full = os.path.join(WORKSPACE, rel)
        gltf_json, bin_data = parse_glb(full)
        mesh = gltf_json["meshes"][0]
        pos_acc_idx = mesh["primitives"][0]["attributes"]["POSITION"]
        coords = get_accessor_data(gltf_json, bin_data, pos_acc_idx)
        min_c = coords.min(axis=0)
        max_c = coords.max(axis=0)
        span = max_c - min_c
        print(f"{os.path.basename(rel):<38} | bounds: X[{min_c[0]:.2f}, {max_c[0]:.2f}] Y[{min_c[1]:.2f}, {max_c[1]:.2f}] Z[{min_c[2]:.2f}, {max_c[2]:.2f}] | span: {span[0]:.2f} x {span[1]:.2f} x {span[2]:.2f}")

if __name__ == "__main__":
    stress_test_modular_bounds()
