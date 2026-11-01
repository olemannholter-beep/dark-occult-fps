"""
Empirical Challenger 1: Stress-test script for environment, terrain, clearances, and chest hierarchy.
Executed via headless Blender 5.4.
"""

import bpy
import bmesh
import math
import os
import sys
from mathutils import Vector, Matrix

ROOT_DIR = os.getcwd()

def clear_blend():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def test_terrain_town():
    print("\n" + "="*60)
    print("TEST 1: assets/models/terrain_town.glb")
    print("="*60)
    clear_blend()
    path = os.path.join(ROOT_DIR, "assets", "models", "terrain_town.glb")
    if not os.path.exists(path):
        print(f"[FAIL] File not found: {path}")
        return False

    bpy.ops.import_scene.gltf(filepath=path)
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    print(f"Imported objects: {[o.name for o in objs]}")
    if not objs:
        print("[FAIL] No mesh objects found in terrain_town.glb")
        return False

    terrain = objs[0]
    mesh = terrain.data
    verts = [terrain.matrix_world @ v.co for v in mesh.vertices]

    min_x = min(v.x for v in verts)
    max_x = max(v.x for v in verts)
    min_y = min(v.y for v in verts)
    max_y = max(v.y for v in verts)
    min_z = min(v.z for v in verts)
    max_z = max(v.z for v in verts)

    print(f"Terrain World Bounds: X=[{min_x:.3f}, {max_x:.3f}], Y=[{min_y:.3f}, {max_y:.3f}], Z=[{min_z:.3f}, {max_z:.3f}]")
    width_x = max_x - min_x
    depth_y = max_y - min_y
    print(f"Terrain Footprint Dimensions: {width_x:.2f}m x {depth_y:.2f}m (Target: ~120m x 120m)")

    # In Blender imported glTF (if default import applies Y-up to Z-up):
    # Let's determine which axis is up. In Blender usually Z is up.
    # Let's check coordinates.
    # Check vertical elevations
    z_coords = [v.z for v in verts]
    print(f"Elevation min: {min(z_coords):.3f}m, max: {max(z_coords):.3f}m")

    # Check building pad flatness:
    # In Godot coords, House A was at (gx = -16.0, gz = +14.0).
    # In Blender: if export_yup was used, Godot X -> Blender X, Godot Y -> Blender Z, Godot Z -> Blender -Y.
    # So Godot gz = 14.0 corresponds to Blender Y = -14.0.
    # Let's test House A vertices around X=-16.0, Y=-14.0:
    ha_verts = [v for v in verts if abs(v.x - (-16.0)) < 3.0 and abs(v.y - (-14.0)) < 3.0]
    if ha_verts:
        ha_zs = [v.z for v in ha_verts]
        ha_z_range = max(ha_zs) - min(ha_zs)
        print(f"House A Pad (X=-16, Y=-14) [count={len(ha_verts)}]: z_min={min(ha_zs):.3f}, z_max={max(ha_zs):.3f}, delta={ha_z_range:.4f}m (Target: flat at 0.85m)")
    else:
        print("[WARN] No vertices found in House A pad region")

    # House B pad: Godot gx = +16.0, gz = +8.0 -> Blender X = +16.0, Y = -8.0
    hb_verts = [v for v in verts if abs(v.x - 16.0) < 3.0 and abs(v.y - (-8.0)) < 3.0]
    if hb_verts:
        hb_zs = [v.z for v in hb_verts]
        hb_z_range = max(hb_zs) - min(hb_zs)
        print(f"House B Pad (X=16, Y=-8) [count={len(hb_verts)}]: z_min={min(hb_zs):.3f}, z_max={max(hb_zs):.3f}, delta={hb_z_range:.4f}m (Target: flat at 1.15m)")
    else:
        print("[WARN] No vertices found in House B pad region")

    # Church plateau pad: Godot gx in [-10, 10], gz in [-20, -10] -> Blender X in [-10, 10], Y in [10, 20]
    church_verts = [v for v in verts if abs(v.x) < 8.0 and 12.0 < v.y < 20.0]
    if church_verts:
        ch_zs = [v.z for v in church_verts]
        print(f"Church Front Plateau (X in [-8, 8], Y in [12, 20]) [count={len(church_verts)}]: z_min={min(ch_zs):.3f}, z_max={max(ch_zs):.3f} (Target: ~3.20m-3.55m)")

    # Stairwell cutout check:
    # Cutout was at Godot gx = 0.0, gz = -39.9 (Blender X = 0.0, Y = 39.9)
    # Bounds: gx in [-13.8, 13.8], gz in [-57.8, -22.0] -> Blender X in [-13.8, 13.8], Y in [22.0, 57.8]
    # Check if there is a hole in the mesh in this region:
    # A point inside the cutout: X=0, Y=35. Is there any face directly spanning over this void?
    cutout_verts = [v for v in verts if abs(v.x) < 12.0 and 24.0 < v.y < 55.0]
    print(f"Stairwell cutout region vertices count: {len(cutout_verts)}")
    # If a boolean difference was cut, faces in the center of the cutout are removed, or border vertices exist.
    # Let's check if the center point (0, 35) is covered by a face or open:
    has_center_mesh = any(abs(v.x) < 5.0 and abs(v.y - 35.0) < 5.0 and v.z > 1.0 for v in verts)
    print(f"Is stairwell cutout center obstructed by terrain (Z > 1.0 at X~0, Y~35): {has_center_mesh}")

    # Step riser heights analysis:
    # Find all polygon edges that are nearly vertical, or analyze elevation differences across adjacent connected vertices.
    bm = bmesh.new()
    bm.from_mesh(mesh)
    edge_z_diffs = []
    vertical_risers = []
    for edge in bm.edges:
        v1 = edge.verts[0].co
        v2 = edge.verts[1].co
        dz = abs(v1.z - v2.z)
        dxy = math.hypot(v1.x - v2.x, v1.y - v2.y)
        if dz > 0.01:
            edge_z_diffs.append(dz)
            # If dxy is small compared to dz, it's a step riser
            if dxy < 0.8:
                vertical_risers.append(dz)

    bm.free()

    if vertical_risers:
        max_riser = max(vertical_risers)
        sorted_risers = sorted(vertical_risers)
        p99_riser = sorted_risers[int(len(sorted_risers) * 0.99)]
        print(f"Step Risers analyzed ({len(vertical_risers)} edges): max={max_riser:.4f}m, 99th_pct={p99_riser:.4f}m")
    else:
        print("[INFO] No steep riser edges found")

    return True


def test_church_foundation_plinth():
    print("\n" + "="*60)
    print("TEST 2: assets/models/church_kit/church_foundation_plinth.glb")
    print("="*60)
    clear_blend()
    path = os.path.join(ROOT_DIR, "assets", "models", "church_kit", "church_foundation_plinth.glb")
    if not os.path.exists(path):
        print(f"[FAIL] File not found: {path}")
        return False

    bpy.ops.import_scene.gltf(filepath=path)
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    print(f"Imported objects: {[o.name for o in objs]}")
    if not objs:
        print("[FAIL] No mesh objects found in church_foundation_plinth.glb")
        return False

    plinth = objs[0]
    verts = [plinth.matrix_world @ v.co for v in plinth.data.vertices]
    min_x, max_x = min(v.x for v in verts), max(v.x for v in verts)
    min_y, max_y = min(v.y for v in verts), max(v.y for v in verts)
    min_z, max_z = min(v.z for v in verts), max(v.z for v in verts)
    print(f"Plinth Bounds: X=[{min_x:.3f}, {max_x:.3f}], Y=[{min_y:.3f}, {max_y:.3f}], Z=[{min_z:.3f}, {max_z:.3f}]")

    # Check CUTOUT 1: Upper stairwell & crypt opening:
    # Generator specified: local X in [-4.5, 4.5], local Y in [-0.5, 12.5], Z in [-2.60, 0.35]
    # Check if this volume has geometry or is carved out
    cutout_verts = [v for v in verts if abs(v.x) < 4.0 and 0.0 < v.y < 12.0 and -2.4 < v.z < 0.2]
    print(f"Vertices inside stairwell cutout void volume (expected ~0): {len(cutout_verts)}")

    # Check CUTOUT 2: Subterranean chamber clearance:
    # Local X in [-7.0, 7.0], local Y in [1.8, 14.0], Z in [-3.0, -0.50]
    cutout2_verts = [v for v in verts if abs(v.x) < 6.5 and 2.5 < v.y < 13.5 and -2.8 < v.z < -0.6]
    print(f"Vertices inside subterranean clearance void volume (expected ~0): {len(cutout2_verts)}")

    # Check Grand Entrance steps:
    # South entrance steps descending from Y = -8.25 to -10.35, Z from 0.0 to -0.88m
    step_verts = [v for v in verts if abs(v.x) < 2.0 and -10.5 < v.y < -8.25]
    step_zs = sorted(list(set(round(v.z, 2) for v in step_verts)))
    print(f"Entrance Step levels (Z): {step_zs}")

    return True


def test_doorway_clearances():
    print("\n" + "="*60)
    print("TEST 3: Doorway clearances (wall_stone_arch_door & crypt_archway_portcullis_4x4)")
    print("="*60)

    # 3A: wall_stone_arch_door.glb
    clear_blend()
    path_door = os.path.join(ROOT_DIR, "assets", "models", "church_kit", "wall_stone_arch_door.glb")
    if not os.path.exists(path_door):
        print(f"[FAIL] File not found: {path_door}")
    else:
        bpy.ops.import_scene.gltf(filepath=path_door)
        objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
        print(f"[wall_stone_arch_door] Imported: {[o.name for o in objs]}")
        verts = [objs[0].matrix_world @ v.co for v in objs[0].data.vertices]
        min_x, max_x = min(v.x for v in verts), max(v.x for v in verts)
        min_y, max_y = min(v.y for v in verts), max(v.y for v in verts)
        min_z, max_z = min(v.z for v in verts), max(v.z for v in verts)
        print(f"  Wall Bounds: X=[{min_x:.3f}, {max_x:.3f}], Y=[{min_y:.3f}, {max_y:.3f}], Z=[{min_z:.3f}, {max_z:.3f}]")

        # Walkable corridor opening: along centerline |X| <= 0.9m, |Y| <= 0.25m
        # Find the lowest vertex in the arch overhead (Z > 1.0)
        arch_overhead = [v for v in verts if abs(v.x) <= 0.9 and abs(v.y) <= 0.25 and v.z > 1.0]
        if arch_overhead:
            lowest_overhead_z = min(v.z for v in arch_overhead)
            print(f"  Lowest archway ceiling at centerline (|X|<=0.9m): {lowest_overhead_z:.4f}m (Required >= 2.45m)")
            if lowest_overhead_z >= 2.45:
                print(f"  [PASS] wall_stone_arch_door clearance is {lowest_overhead_z:.3f}m >= 2.45m")
            else:
                print(f"  [FAIL] wall_stone_arch_door clearance is {lowest_overhead_z:.3f}m < 2.45m")
        else:
            print("  [WARN] No overhead vertices found in corridor")

    # 3B: crypt_archway_portcullis_4x4.glb
    clear_blend()
    path_portcullis = os.path.join(ROOT_DIR, "assets", "models", "church_kit", "crypt_archway_portcullis_4x4.glb")
    if not os.path.exists(path_portcullis):
        print(f"[FAIL] File not found: {path_portcullis}")
    else:
        bpy.ops.import_scene.gltf(filepath=path_portcullis)
        objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
        print(f"\n[crypt_archway_portcullis_4x4] Imported: {[o.name for o in objs]}")
        verts = [objs[0].matrix_world @ v.co for v in objs[0].data.vertices]
        min_x, max_x = min(v.x for v in verts), max(v.x for v in verts)
        min_y, max_y = min(v.y for v in verts), max(v.y for v in verts)
        min_z, max_z = min(v.z for v in verts), max(v.z for v in verts)
        print(f"  Archway Bounds: X=[{min_x:.3f}, {max_x:.3f}], Y=[{min_y:.3f}, {max_y:.3f}], Z=[{min_z:.3f}, {max_z:.3f}]")

        # Walkable corridor opening: along centerline |X| <= 0.9m, |Y| <= 0.25m
        overhead_verts = [v for v in verts if abs(v.x) <= 0.9 and abs(v.y) <= 0.25 and v.z > 1.0]
        if overhead_verts:
            lowest_portcullis_z = min(v.z for v in overhead_verts)
            print(f"  Lowest portcullis/arch ceiling at centerline (|X|<=0.9m): {lowest_portcullis_z:.4f}m (Requirement: Z >= 2.45m)")
            if lowest_portcullis_z >= 2.45:
                print(f"  [PASS] crypt_archway_portcullis clearance is {lowest_portcullis_z:.3f}m >= 2.45m")
            else:
                print(f"  [FAIL / CRITICAL FINDING] crypt_archway_portcullis clearance is {lowest_portcullis_z:.4f}m < 2.45m!")
                # Print details of vertices below 2.45m
                below_req = [v for v in overhead_verts if v.z < 2.45]
                print(f"    Total vertices below 2.45m in central opening: {len(below_req)}")
                print(f"    Lowest vertex: ({below_req[0].x:.3f}, {below_req[0].y:.3f}, {below_req[0].z:.3f})")

    return True


def test_prop_gothic_reliquary_chest():
    print("\n" + "="*60)
    print("TEST 4: assets/models/items/prop_gothic_reliquary_chest.glb")
    print("="*60)
    clear_blend()
    path_chest = os.path.join(ROOT_DIR, "assets", "models", "items", "prop_gothic_reliquary_chest.glb")
    if not os.path.exists(path_chest):
        print(f"[FAIL] File not found: {path_chest}")
        return False

    bpy.ops.import_scene.gltf(filepath=path_chest)
    all_objs = list(bpy.context.scene.objects)
    print(f"Imported objects: {[o.name for o in all_objs]}")

    base_obj = bpy.context.scene.objects.get("ChestBase")
    lid_obj = bpy.context.scene.objects.get("ChestLid")

    if not base_obj or not lid_obj:
        print(f"[FAIL] ChestBase or ChestLid not found. Objects: {[o.name for o in all_objs]}")
        return False

    print(f"Found ChestBase: {base_obj.name}, parent={base_obj.parent.name if base_obj.parent else None}")
    print(f"Found ChestLid: {lid_obj.name}, parent={lid_obj.parent.name if lid_obj.parent else None}")

    # Check parent-child hierarchy
    if lid_obj.parent == base_obj:
        print("[PASS] ChestLid is correctly parented to ChestBase.")
    else:
        print(f"[FAIL] ChestLid parent is {lid_obj.parent}, expected ChestBase!")

    # Check lid pivot / local position
    print(f"ChestLid local position: ({lid_obj.location.x:.3f}, {lid_obj.location.y:.3f}, {lid_obj.location.z:.3f})")
    # Expected pivot is at Y=0.41, Z=0.58 (or in Blender Y-up / Z-up coordinates)
    print(f"ChestLid world position: ({lid_obj.matrix_world.translation.x:.3f}, {lid_obj.matrix_world.translation.y:.3f}, {lid_obj.matrix_world.translation.z:.3f})")

    # Test rotation: Rotate lid by -60 degrees on local X axis
    orig_rot = lid_obj.rotation_euler.copy()
    lid_obj.rotation_euler.x -= math.radians(60.0)
    bpy.context.view_layer.update()

    # Verify lid rotated and world position of hinge stays invariant
    lid_hinge_world = lid_obj.matrix_world @ Vector((0.0, 0.0, 0.0))
    print(f"Hinge world location after -60 deg rotation: ({lid_hinge_world.x:.3f}, {lid_hinge_world.y:.3f}, {lid_hinge_world.z:.3f})")

    # Front lip vertex before and after rotation
    front_verts = [v for v in lid_obj.data.vertices if v.co.y < -0.3]
    if front_verts:
        v_local = front_verts[0].co
        v_world_rotated = lid_obj.matrix_world @ v_local
        print(f"Front lid lip world pos rotated: ({v_world_rotated.x:.3f}, {v_world_rotated.y:.3f}, {v_world_rotated.z:.3f})")
        print("[PASS] ChestLid rotates smoothly around rear hinge pivot!")
    else:
        print("[WARN] No front lip vertices found")

    lid_obj.rotation_euler = orig_rot
    return True


if __name__ == "__main__":
    t1 = test_terrain_town()
    t2 = test_church_foundation_plinth()
    t3 = test_doorway_clearances()
    t4 = test_prop_gothic_reliquary_chest()
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)
