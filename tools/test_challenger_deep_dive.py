"""
Deep Dive empirical analysis of step risers on terrain_town.glb
and portcullis clearance on crypt_archway_portcullis_4x4.glb.
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector

ROOT_DIR = os.getcwd()

def clear_blend():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def deep_dive_terrain():
    print("\n" + "="*70)
    print("DEEP DIVE 1: terrain_town.glb Step Risers Analysis")
    print("="*70)
    clear_blend()
    path = os.path.join(ROOT_DIR, "assets", "models", "terrain_town.glb")
    bpy.ops.import_scene.gltf(filepath=path)
    terrain = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
    mesh = terrain.data

    # Map materials: 0=grass, 1=road/path, 2=cliff
    mat_names = [m.name for m in terrain.data.materials]
    print(f"Materials on terrain: {mat_names}")

    bm = bmesh.new()
    bm.from_mesh(mesh)

    # 1. Edge-based step analysis partitioned by area
    # Road / Path: polygons with material_index == 1 (mud_path)
    # Check edges belonging to road/path faces
    road_edges = []
    grass_edges = []
    cliff_edges = []
    all_step_edges = []

    for edge in bm.edges:
        if not edge.link_faces:
            continue
        v1 = edge.verts[0].co
        v2 = edge.verts[1].co
        dz = abs(v1.z - v2.z)
        dxy = math.hypot(v1.x - v2.x, v1.y - v2.y)

        # Look for connected faces
        mat_indices = {f.material_index for f in edge.link_faces}
        is_road = (1 in mat_indices)
        is_cliff = (2 in mat_indices)

        # In Godot, a player walking encounters step height differences.
        # If an edge is nearly vertical (riser) or represents elevation change between grid points:
        if dz > 0.005:
            all_step_edges.append((dz, dxy, v1, v2, mat_indices))
            if is_road:
                road_edges.append((dz, dxy, v1, v2))
            elif is_cliff:
                cliff_edges.append((dz, dxy, v1, v2))
            else:
                grass_edges.append((dz, dxy, v1, v2))

    print(f"\n--- Elevation Step Analysis across Terrain ---")
    print(f"Total edges with elevation change (dz > 0.005m): {len(all_step_edges)}")

    # Distinct elevation steps (quantization levels)
    # The math in generator was: round(hy / 0.18) * 0.18
    # So ideal terraced steps are multiples of 0.18m (0.18, 0.36, 0.54, etc.)
    all_zs = sorted([v.co.z for v in bm.verts])
    distinct_zs = []
    for z in all_zs:
        if not distinct_zs or abs(z - distinct_zs[-1]) > 0.02:
            distinct_zs.append(round(z, 3))
    print(f"Total distinct elevation plateaus detected: {len(distinct_zs)}")
    z_diffs = [round(distinct_zs[i+1] - distinct_zs[i], 3) for i in range(len(distinct_zs)-1)]
    print(f"Sample elevation step increments between consecutive plateaus: {z_diffs[:20]}")

    # Check Road / Path steps:
    print(f"\n--- Road / Path Edges (Walkable primary route) ---")
    print(f"Total road edges: {len(road_edges)}")
    if road_edges:
        road_dzs = [e[0] for e in road_edges]
        max_road_dz = max(road_dzs)
        avg_road_dz = sum(road_dzs) / len(road_dzs)
        road_over_20cm = [e for e in road_edges if e[0] > 0.20]
        road_over_36cm = [e for e in road_edges if e[0] > 0.36]
        print(f"Road max dz: {max_road_dz:.4f}m, avg dz: {avg_road_dz:.4f}m")
        print(f"Road edges with dz > 0.20m: {len(road_over_20cm)} ({len(road_over_20cm)/len(road_edges)*100:.1f}%)")
        print(f"Road edges with dz > 0.36m (Godot max_step_height): {len(road_over_36cm)}")
        if road_over_20cm:
            print(f"Sample road edge > 0.20m: dz={road_over_20cm[0][0]:.3f}m at v1=({road_over_20cm[0][2].x:.2f}, {road_over_20cm[0][2].y:.2f}, {road_over_20cm[0][2].z:.2f})")

    # Check Grass / Overworld steps:
    print(f"\n--- Moor Grass Edges (Overworld field) ---")
    if grass_edges:
        grass_dzs = [e[0] for e in grass_edges]
        grass_over_20cm = [e for e in grass_edges if e[0] > 0.20]
        grass_over_36cm = [e for e in grass_edges if e[0] > 0.36]
        print(f"Grass max dz: {max(grass_dzs):.4f}m, avg dz: {sum(grass_dzs)/len(grass_dzs):.4f}m")
        print(f"Grass edges with dz > 0.20m: {len(grass_over_20cm)} ({len(grass_over_20cm)/len(grass_edges)*100:.1f}%)")
        print(f"Grass edges with dz > 0.36m: {len(grass_over_36cm)}")

    # Check Cliff edges:
    print(f"\n--- Cliff Edges (Steep perimeter / rock walls) ---")
    if cliff_edges:
        cliff_dzs = [e[0] for e in cliff_edges]
        print(f"Cliff max dz: {max(cliff_dzs):.4f}m, count={len(cliff_edges)}")

    bm.free()

def deep_dive_portcullis():
    print("\n" + "="*70)
    print("DEEP DIVE 2: crypt_archway_portcullis_4x4.glb Portcullis Geometry")
    print("="*70)
    clear_blend()
    path = os.path.join(ROOT_DIR, "assets", "models", "church_kit", "crypt_archway_portcullis_4x4.glb")
    bpy.ops.import_scene.gltf(filepath=path)
    obj = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]

    # Find the portcullis parts vs wall parts
    # Looking at materials:
    mat_names = [m.name for m in obj.data.materials]
    print(f"Materials on portcullis: {mat_names}")

    # Inspect all vertices that form the downward spikes
    verts = [obj.matrix_world @ v.co for v in obj.data.vertices]

    # Find all vertices with Z < 2.45m in the archway opening |X| < 1.20m, |Y| < 0.20m, Z > 1.0m
    spike_verts = [v for v in verts if abs(v.x) < 1.20 and abs(v.y) < 0.20 and 1.5 < v.z < 2.45]
    print(f"Number of spike vertices below 2.45m: {len(spike_verts)}")
    if spike_verts:
        spike_zs = sorted(list(set(round(v.z, 3) for v in spike_verts)))
        print(f"Unique Z elevation levels of spike tips below 2.45m: {spike_zs}")
        # Group by spike X position
        spike_groups = {}
        for v in spike_verts:
            bx = round(v.x, 2)
            # Find nearest cluster
            found = False
            for k in spike_groups:
                if abs(k - bx) < 0.05:
                    spike_groups[k].append(v)
                    found = True
                    break
            if not found:
                spike_groups[bx] = [v]

        print(f"Identified {len(spike_groups)} spike locations across archway:")
        for bx, svs in sorted(spike_groups.items()):
            min_z = min(v.z for v in svs)
            print(f"  Spike at X = {bx:+.2f}m: lowest tip Z = {min_z:.3f}m (deficiency: {2.45 - min_z:.3f}m below 2.45m)")

    # Also check the stone archway spring and peak
    arch_stone_verts = [v for v in verts if abs(v.x) < 1.20 and abs(v.y) > 0.10 and v.z > 2.0]
    if arch_stone_verts:
        print(f"Stone arch masonry ceiling at centerline: lowest Z = {min(v.z for v in arch_stone_verts):.3f}m")

def deep_dive_wall_arch():
    print("\n" + "="*70)
    print("DEEP DIVE 3: wall_stone_arch_door.glb Arch Clearance")
    print("="*70)
    clear_blend()
    path = os.path.join(ROOT_DIR, "assets", "models", "church_kit", "wall_stone_arch_door.glb")
    bpy.ops.import_scene.gltf(filepath=path)
    obj = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
    verts = [obj.matrix_world @ v.co for v in obj.data.vertices]

    # Centerline opening |X| <= 0.6m, |Y| <= 0.20m, Z > 1.0m
    arch_verts = [v for v in verts if abs(v.x) <= 0.60 and abs(v.y) <= 0.20 and v.z > 1.0]
    if arch_verts:
        min_arch_z = min(v.z for v in arch_verts)
        print(f"wall_stone_arch_door central opening lowest ceiling: Z = {min_arch_z:.3f}m (Passes >= 2.45m by {min_arch_z - 2.45:.3f}m)")

    # At door jamb edges |X| = 1.0m
    jamb_verts = [v for v in verts if 0.9 <= abs(v.x) <= 1.15 and abs(v.y) <= 0.20 and v.z > 1.0]
    if jamb_verts:
        min_jamb_z = min(v.z for v in jamb_verts)
        print(f"wall_stone_arch_door spring line at jambs (|X|~1.0m): Z = {min_jamb_z:.3f}m")

if __name__ == "__main__":
    deep_dive_terrain()
    deep_dive_portcullis()
    deep_dive_wall_arch()
