import os
import sys
import json
import struct
import numpy as np

WORKSPACE = r"c:\Users\olema\Downloads\alpha branch"

def parse_glb(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    magic, version, length = struct.unpack("<4sII", data[:12])
    pos = 12
    chunk0_len, chunk0_type = struct.unpack("<II", data[pos:pos+8])
    pos += 8
    json_bytes = data[pos:pos+chunk0_len]
    pos += chunk0_len
    gltf_json = json.loads(json_bytes.decode("utf-8"))
    bin_data = None
    if pos < len(data):
        chunk1_len, chunk1_type = struct.unpack("<II", data[pos:pos+8])
        pos += 8
        bin_data = data[pos:pos+chunk1_len]
    return gltf_json, bin_data

def get_buffer_view_data(gltf_json, bin_data, buffer_view_idx):
    bv = gltf_json["bufferViews"][buffer_view_idx]
    byte_offset = bv.get("byteOffset", 0)
    byte_length = bv["byteLength"]
    return bin_data[byte_offset:byte_offset + byte_length]

def get_accessor_data(gltf_json, bin_data, accessor_idx):
    acc = gltf_json["accessors"][accessor_idx]
    bv_idx = acc["bufferView"]
    bv_data = get_buffer_view_data(gltf_json, bin_data, bv_idx)
    acc_offset = acc.get("byteOffset", 0)
    component_type = acc["componentType"] # 5126 = FLOAT
    count = acc["count"]
    acc_type = acc["type"] # 'VEC3', 'SCALAR', etc.

    if component_type == 5126: # FLOAT
        fmt = "f"
        stride = 4
    elif component_type == 5123: # UNSIGNED_SHORT
        fmt = "H"
        stride = 2
    elif component_type == 5125: # UNSIGNED_INT
        fmt = "I"
        stride = 4
    else:
        raise ValueError(f"Unsupported component type: {component_type}")

    components_per_element = 1
    if acc_type == "VEC2":
        components_per_element = 2
    elif acc_type == "VEC3":
        components_per_element = 3
    elif acc_type == "VEC4":
        components_per_element = 4

    raw_format = f"<{count * components_per_element}{fmt}"
    element_size = stride * components_per_element
    total_bytes = count * element_size
    unpacked = struct.unpack(raw_format, bv_data[acc_offset:acc_offset + total_bytes])
    if components_per_element > 1:
        return np.array(unpacked, dtype=np.float32).reshape((count, components_per_element))
    else:
        return np.array(unpacked)

def audit_hierarchies():
    print("=" * 80)
    print("AUDIT 2: NODE & HIERARCHY INTEGRITY AUDIT")
    print("=" * 80)

    # 1. Reliquary Chest
    chest_path = os.path.join(WORKSPACE, "assets/models/items/prop_gothic_reliquary_chest.glb")
    gltf_chest, _ = parse_glb(chest_path)
    nodes = gltf_chest.get("nodes", [])
    print(f"\n--- Checking Reliquary Chest: {os.path.basename(chest_path)} ---")
    node_names = [n.get("name") for n in nodes]
    print(f"Nodes found: {node_names}")
    assert "ChestBase" in node_names, "Missing ChestBase"
    assert "ChestLid" in node_names, "Missing ChestLid"
    base_idx = node_names.index("ChestBase")
    lid_idx = node_names.index("ChestLid")
    base_node = nodes[base_idx]
    lid_node = nodes[lid_idx]
    print(f"ChestBase: children={base_node.get('children')}, translation={base_node.get('translation')}")
    print(f"ChestLid: children={lid_node.get('children')}, translation={lid_node.get('translation')}")
    assert lid_idx in base_node.get("children", []), "ChestLid must be a child of ChestBase"
    lid_trans = lid_node.get("translation", [0, 0, 0])
    print(f"[PASS] Reliquary Chest hierarchy confirmed: ChestLid is child of ChestBase with pivot offset {lid_trans}")

    # 2. Occult Rift Portal
    portal_path = os.path.join(WORKSPACE, "assets/models/architecture/occult_rift_portal.glb")
    gltf_portal, _ = parse_glb(portal_path)
    p_nodes = gltf_portal.get("nodes", [])
    print(f"\n--- Checking Occult Rift Portal: {os.path.basename(portal_path)} ---")
    p_names = [n.get("name") for n in p_nodes]
    print(f"Nodes found: {p_names}")
    assert "OccultRiftArchway" in p_names, "Missing OccultRiftArchway"
    assert "PortalVortexMesh" in p_names, "Missing PortalVortexMesh"
    arch_idx = p_names.index("OccultRiftArchway")
    vort_idx = p_names.index("PortalVortexMesh")
    arch_node = p_nodes[arch_idx]
    vort_node = p_nodes[vort_idx]
    print(f"OccultRiftArchway: children={arch_node.get('children')}, translation={arch_node.get('translation')}")
    print(f"PortalVortexMesh: children={vort_node.get('children')}, translation={vort_node.get('translation')}")
    assert vort_idx in arch_node.get("children", []), "PortalVortexMesh must be child of OccultRiftArchway"
    print(f"[PASS] Occult Rift Portal hierarchy confirmed: PortalVortexMesh is child of OccultRiftArchway")

    # 3. Enemy Hierarchies (11 enemies)
    print("\n--- Checking All 11 Enemy Models Articulated Hierarchies ---")
    enemy_dir = os.path.join(WORKSPACE, "assets/models/enemies")
    required_enemy_nodes = [
        "Pelvis", "Torso", "Head",
        "UpperArmL", "ForearmL", "UpperArmR", "ForearmR",
        "ThighL", "ShinL", "ThighR", "ShinR", "SecondaryProp"
    ]
    enemy_files = [f for f in sorted(os.listdir(enemy_dir)) if f.endswith(".glb")]
    print(f"Found {len(enemy_files)} enemy GLB files in {enemy_dir}")

    all_enemies_passed = True
    for ef in enemy_files:
        ef_path = os.path.join(enemy_dir, ef)
        gltf_e, _ = parse_glb(ef_path)
        e_nodes = gltf_e.get("nodes", [])
        e_names = [n.get("name") for n in e_nodes]
        missing = [r for r in required_enemy_nodes if r not in e_names]
        if missing:
            print(f"[FAIL] {ef}: Missing nodes: {missing}")
            all_enemies_passed = False
            continue

        # Check parenting relationships
        name_to_idx = {name: idx for idx, name in enumerate(e_names)}
        pelvis_idx = name_to_idx["Pelvis"]
        torso_idx = name_to_idx["Torso"]
        head_idx = name_to_idx["Head"]
        u_arm_l_idx = name_to_idx["UpperArmL"]
        f_arm_l_idx = name_to_idx["ForearmL"]
        u_arm_r_idx = name_to_idx["UpperArmR"]
        f_arm_r_idx = name_to_idx["ForearmR"]
        thigh_l_idx = name_to_idx["ThighL"]
        shin_l_idx = name_to_idx["ShinL"]
        thigh_r_idx = name_to_idx["ThighR"]
        shin_r_idx = name_to_idx["ShinR"]
        sec_prop_idx = name_to_idx["SecondaryProp"]

        pelvis_children = e_nodes[pelvis_idx].get("children", [])
        torso_children = e_nodes[torso_idx].get("children", [])
        u_arm_l_children = e_nodes[u_arm_l_idx].get("children", [])
        u_arm_r_children = e_nodes[u_arm_r_idx].get("children", [])
        thigh_l_children = e_nodes[thigh_l_idx].get("children", [])
        thigh_r_children = e_nodes[thigh_r_idx].get("children", [])

        checks = [
            (torso_idx in pelvis_children, "Torso is child of Pelvis"),
            (thigh_l_idx in pelvis_children, "ThighL is child of Pelvis"),
            (thigh_r_idx in pelvis_children, "ThighR is child of Pelvis"),
            (head_idx in torso_children, "Head is child of Torso"),
            (u_arm_l_idx in torso_children, "UpperArmL is child of Torso"),
            (u_arm_r_idx in torso_children, "UpperArmR is child of Torso"),
            (sec_prop_idx in torso_children, "SecondaryProp is child of Torso"),
            (f_arm_l_idx in u_arm_l_children, "ForearmL is child of UpperArmL"),
            (f_arm_r_idx in u_arm_r_children, "ForearmR is child of UpperArmR"),
            (shin_l_idx in thigh_l_children, "ShinL is child of ThighL"),
            (shin_r_idx in thigh_r_children, "ShinR is child of ThighR"),
        ]

        failed_checks = [msg for success, msg in checks if not success]
        if failed_checks:
            print(f"[FAIL] {ef}: Hierarchy parenting failures: {failed_checks}")
            all_enemies_passed = False
        else:
            print(f"[PASS] {ef:<36} | 12/12 nodes verified | 11/11 parenting relationships verified")

    assert all_enemies_passed, "Some enemy models failed hierarchy audit"
    print("\nALL 11 ENEMY HIERARCHIES VERIFIED CLEAN!")

def audit_terrain():
    print("\n" + "=" * 80)
    print("AUDIT 3: TERRAIN INTEGRITY AUDIT")
    print("=" * 80)

    terrain_path = os.path.join(WORKSPACE, "assets/models/terrain_town.glb")
    gltf_t, bin_data = parse_glb(terrain_path)

    # Extract all positions
    pos_acc_idx = gltf_t["meshes"][0]["primitives"][0]["attributes"]["POSITION"]
    coords = get_accessor_data(gltf_t, bin_data, pos_acc_idx)
    print(f"Terrain Town loaded: {len(coords):,} vertices")

    # In glTF with export_yup=True:
    # glTF X = Godot X
    # glTF Y = Godot Y (up)
    # glTF Z = Godot Z
    xs = coords[:, 0]
    ys = coords[:, 1] # height
    zs = coords[:, 2]

    print(f"X bounds: [{xs.min():.2f}, {xs.max():.2f}]")
    print(f"Y bounds (height): [{ys.min():.2f}, {ys.max():.2f}]")
    print(f"Z bounds: [{zs.min():.2f}, {zs.max():.2f}]")

    # 1. Step Height Quantization
    # Collect unique height values
    unique_heights = np.unique(np.round(ys, 3))
    height_diffs = np.diff(unique_heights)
    # Filter out microscopic floating point step differences (< 0.01)
    significant_diffs = height_diffs[height_diffs > 0.05]
    print(f"Found {len(unique_heights)} unique terrace heights.")
    print(f"Height differences between successive terraces: min={significant_diffs.min():.4f}m, median={np.median(significant_diffs):.4f}m, max={significant_diffs.max():.4f}m")
    max_step = significant_diffs.max()
    print(f"Maximum step height: {max_step:.4f}m (Constraint: <= 0.20m, within max_step_height = 0.36m)")
    assert max_step <= 0.201, f"Step height {max_step} exceeds 0.20m!"
    print(f"[PASS] Step height quantization verified: all steps <= 0.20m (target 0.18m)")

    # 2. Building Footprints
    # House A: centered at gx = -16.0, gz = +14.0 (inner radius 4.5m)
    dist_house_a = np.sqrt((xs - (-16.0))**2 + (zs - 14.0)**2)
    house_a_verts = ys[dist_house_a < 4.5]
    print(f"\nHouse A pad (X=-16, Z=+14, r<4.5m): {len(house_a_verts)} vertices, height range: [{house_a_verts.min():.3f}, {house_a_verts.max():.3f}] (expected ~0.85m)")
    assert np.allclose(house_a_verts, 0.85, atol=0.06), f"House A footprint not flat at 0.85m! Range: {house_a_verts.min()} - {house_a_verts.max()}"
    print(f"[PASS] House A footprint flattened cleanly at Y = 0.85m")

    # House B: centered at gx = +16.0, gz = +8.0 (inner radius 4.5m)
    dist_house_b = np.sqrt((xs - 16.0)**2 + (zs - 8.0)**2)
    house_b_verts = ys[dist_house_b < 4.5]
    print(f"House B pad (X=+16, Z=+8, r<4.5m): {len(house_b_verts)} vertices, height range: [{house_b_verts.min():.3f}, {house_b_verts.max():.3f}] (expected ~1.15m)")
    assert np.allclose(house_b_verts, 1.15, atol=0.06), f"House B footprint not flat at 1.15m! Range: {house_b_verts.min()} - {house_b_verts.max()}"
    print(f"[PASS] House B footprint flattened cleanly at Y = 1.15m")

    # Church Plateau: gx in [-12, 12], gz in [-45, -15]
    church_mask = (xs >= -12.0) & (xs <= 12.0) & (zs >= -45.0) & (zs <= -15.0)
    # exclude cutout if any
    church_verts = ys[church_mask]
    print(f"Church plateau area: {len(church_verts)} vertices, median height: {np.median(church_verts):.3f}m")

    # 3. Stairwell Opening at X=0, Z=-22
    # In Godot coordinates: bounds X in [-13.8, 13.8], Z in [-57.8, -22.0]
    # Check if there are ground vertices blocking the stairwell descent at Z in [-55, -23], X in [-10, 10]
    stairwell_mask = (np.abs(xs) < 10.0) & (zs > -55.0) & (zs < -23.0) & (ys > 0.5)
    blocking_stair_verts = np.sum(stairwell_mask)
    print(f"\nStairwell cutout check (X:[-10, 10], Z:[-55, -23], Y > 0.5m): blocking terrain vertices = {blocking_stair_verts}")
    assert blocking_stair_verts == 0, f"Stairwell opening is BLOCKED by {blocking_stair_verts} terrain vertices!"
    print(f"[PASS] Stairwell opening at X=0, Z=-22 is completely UNBLOCKED (0 vertices)")

if __name__ == "__main__":
    audit_hierarchies()
    audit_terrain()
    print("\nALL DEEP INSPECTIONS PASSED CLEANLY!")
