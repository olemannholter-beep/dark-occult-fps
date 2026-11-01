import sys
import os
import bpy
import mathutils

print("=== STARTING INDEPENDENT M2 (R3) VERIFICATION ===")

CHURCH_DIR = os.path.abspath("assets/models/church_kit")

target_models = [
    "crypt_corridor_vault_4x4.glb",
    "crypt_wall_ossuary_4x4.glb",
    "crypt_archway_portcullis_4x4.glb",
    "crypt_pillar.glb",
    "crypt_containment_hull.glb",
    "crypt_iron_gate_cell_4x4.glb",
    "crypt_drowned_cistern_4x4.glb",
    "crypt_rotting_bookshelf_4x4.glb",
    "crypt_altar.glb",
    "crypt_sarcophagus_ornate.glb",
    "crypt_lectern_grimoire.glb",
    "crypt_hanging_cage.glb",
    "crypt_plague_cauldron.glb",
    "crypt_weeping_statue_pedestal.glb",
    "crypt_sunken_bell_crater.glb",
    "crypt_ritual_obelisk.glb",
    "standing_iron_brazier.glb",
    "clutter_ceiling_chains_roots.glb",
    "clutter_melted_candle_cluster.glb",
    "clutter_rubble_bones_pile.glb",
    "clutter_wooden_crates_barrels.glb",
]

assert len(target_models) == 21, f"Expected 21 models, got {len(target_models)}"

model_stats = {}

for name in target_models:
    path = os.path.join(CHURCH_DIR, name)
    assert os.path.exists(path), f"File missing: {path}"
    size = os.path.getsize(path)
    assert size > 1000, f"File {name} is suspiciously small: {size} bytes"

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
    }
    print(f"[{name}] size={size} bytes, verts={total_verts}, dims={dims}, vcol={has_vcol}")

# 1. Wall thickness checks (>= 0.48m for light isolation)
# For crypt_wall_ossuary_4x4: wall runs along X (-2 to 2), thickness is along Y
wall_ossuary_thick = model_stats["crypt_wall_ossuary_4x4.glb"]["dims"][1]
print(f"crypt_wall_ossuary_4x4 thickness (Y): {wall_ossuary_thick:.3f}m")
assert wall_ossuary_thick >= 0.48, f"crypt_wall_ossuary_4x4 thickness {wall_ossuary_thick:.3f}m < 0.48m"

# crypt_archway_portcullis_4x4: arch along X, thickness is along Y
arch_portcullis_thick = model_stats["crypt_archway_portcullis_4x4.glb"]["dims"][1]
print(f"crypt_archway_portcullis_4x4 thickness (Y): {arch_portcullis_thick:.3f}m")
assert arch_portcullis_thick >= 0.48, f"crypt_archway_portcullis_4x4 thickness {arch_portcullis_thick:.3f}m < 0.48m"

# crypt_iron_gate_cell_4x4: thickness along Y
iron_gate_thick = model_stats["crypt_iron_gate_cell_4x4.glb"]["dims"][1]
print(f"crypt_iron_gate_cell_4x4 thickness (Y): {iron_gate_thick:.3f}m")
assert iron_gate_thick >= 0.48, f"crypt_iron_gate_cell_4x4 thickness {iron_gate_thick:.3f}m < 0.48m"

# crypt_rotting_bookshelf_4x4: thickness along Y
bookshelf_thick = model_stats["crypt_rotting_bookshelf_4x4.glb"]["dims"][1]
print(f"crypt_rotting_bookshelf_4x4 thickness (Y): {bookshelf_thick:.3f}m")
assert bookshelf_thick >= 0.48, f"crypt_rotting_bookshelf_4x4 thickness {bookshelf_thick:.3f}m < 0.48m"

# 2. Portcullis archway clearance check (clearance height >= 2.45m)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(CHURCH_DIR, "crypt_archway_portcullis_4x4.glb"))
arch_obj = bpy.context.scene.objects[0]
arch_mesh = arch_obj.data

# Check center archway opening in X [-0.5, 0.5], Y [-0.2, 0.2]
# Find the lowest vertex above the floor (Z > 0.1) in the walkway
walkway_verts_z = [v.co.z for v in arch_mesh.vertices if abs(v.co.x) < 0.6 and abs(v.co.y) < 0.2 and v.co.z > 0.1]
portcullis_clearance = min(walkway_verts_z) if walkway_verts_z else 0.0
print(f"crypt_archway_portcullis archway clearance height: {portcullis_clearance:.3f}m")
assert portcullis_clearance >= 2.45, f"Portcullis clearance {portcullis_clearance:.3f}m is < 2.45m"

# 3. crypt_containment_hull.glb check: inward-facing normals
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(CHURCH_DIR, "crypt_containment_hull.glb"))
hull_obj = bpy.context.scene.objects[0]
hull_mesh = hull_obj.data

# The interior center of the containment hull
interior_center = mathutils.Vector((0.0, 52.5, -3.1))

# Check face normals: For an inward-pointing face, the normal should point towards interior_center.
# (face_center - interior_center).dot(face_normal) should be negative!
inward_count = 0
outward_count = 0

for poly in hull_mesh.polygons:
    face_center = poly.center
    face_normal = poly.normal
    vec_from_center = face_center - interior_center
    dot = vec_from_center.dot(face_normal)
    if dot < -0.001:
        inward_count += 1
    elif dot > 0.001:
        outward_count += 1

print(f"crypt_containment_hull polygons: total={len(hull_mesh.polygons)}, inward={inward_count}, outward={outward_count}")
assert inward_count > 0 and outward_count == 0, f"crypt_containment_hull has outward-facing normals! inward={inward_count}, outward={outward_count}"

print("=== M2 (R3) INDEPENDENT VERIFICATION PASSED SUCCESSFULLY ===")
