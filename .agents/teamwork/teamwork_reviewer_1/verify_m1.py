import sys
import os
import bpy
import mathutils

print("=== STARTING INDEPENDENT M1 (R2) VERIFICATION ===")

CHURCH_DIR = os.path.abspath("assets/models/church_kit")
PORTAL_PATH = os.path.abspath("assets/models/architecture/occult_rift_portal.glb")

target_models = [
    ("floor_stone_4x4.glb", os.path.join(CHURCH_DIR, "floor_stone_4x4.glb")),
    ("wall_stone_solid.glb", os.path.join(CHURCH_DIR, "wall_stone_solid.glb")),
    ("wall_stone_window.glb", os.path.join(CHURCH_DIR, "wall_stone_window.glb")),
    ("wall_stone_arch_door.glb", os.path.join(CHURCH_DIR, "wall_stone_arch_door.glb")),
    ("roof_gothic_vault_4x4.glb", os.path.join(CHURCH_DIR, "roof_gothic_vault_4x4.glb")),
    ("stairs_stone_4x4.glb", os.path.join(CHURCH_DIR, "stairs_stone_4x4.glb")),
    ("wall_lantern_sconce.glb", os.path.join(CHURCH_DIR, "wall_lantern_sconce.glb")),
    ("church_foundation_plinth.glb", os.path.join(CHURCH_DIR, "church_foundation_plinth.glb")),
    ("church_front_gable_rose.glb", os.path.join(CHURCH_DIR, "church_front_gable_rose.glb")),
    ("church_pitched_roof_12x16.glb", os.path.join(CHURCH_DIR, "church_pitched_roof_12x16.glb")),
    ("church_bell_tower_spire.glb", os.path.join(CHURCH_DIR, "church_bell_tower_spire.glb")),
    ("church_buttress.glb", os.path.join(CHURCH_DIR, "church_buttress.glb")),
    ("hub_weapon_workbench.glb", os.path.join(CHURCH_DIR, "hub_weapon_workbench.glb")),
    ("hub_armor_reliquary_stand.glb", os.path.join(CHURCH_DIR, "hub_armor_reliquary_stand.glb")),
    ("hub_sanctuary_upgrade_font.glb", os.path.join(CHURCH_DIR, "hub_sanctuary_upgrade_font.glb")),
    ("occult_rift_portal.glb", PORTAL_PATH),
]

assert len(target_models) == 16, f"Expected 16 models, got {len(target_models)}"

model_stats = {}

for name, path in target_models:
    assert os.path.exists(path), f"File missing: {path}"
    size = os.path.getsize(path)
    assert size > 1000, f"File {name} is suspiciously small: {size} bytes"

    # Reset Blender scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # Import GLB
    bpy.ops.import_scene.gltf(filepath=path)

    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    all_objs = list(bpy.context.scene.objects)
    obj_names = [o.name for o in all_objs]

    # Calculate overall bounding box in Blender imported space
    min_co = [float("inf")] * 3
    max_co = [float("-inf")] * 3
    total_verts = 0
    has_vcol = False

    for o in objs:
        total_verts += len(o.data.vertices)
        if o.data.color_attributes:
            has_vcol = True
        for v in o.data.vertices:
            world_co = o.matrix_world @ v.co
            for i in range(3):
                min_co[i] = min(min_co[i], world_co[i])
                max_co[i] = max(max_co[i], world_co[i])

    dims = [round(max_co[i] - min_co[i], 3) for i in range(3)]
    model_stats[name] = {
        "size": size,
        "obj_names": obj_names,
        "mesh_objs": [o.name for o in objs],
        "total_verts": total_verts,
        "dims": dims,
        "min_co": [round(c, 3) for c in min_co],
        "max_co": [round(c, 3) for c in max_co],
        "has_vcol": has_vcol,
    }
    print(f"[{name}] size={size} bytes, objs={obj_names}, verts={total_verts}, dims={dims}, vcol={has_vcol}")

# Detailed checks
# 1. 4m modular grid bounds check
assert abs(model_stats["floor_stone_4x4.glb"]["dims"][0] - 4.0) < 0.2, f"floor_stone_4x4 X dimension not ~4m: {model_stats['floor_stone_4x4.glb']['dims']}"
assert abs(model_stats["floor_stone_4x4.glb"]["dims"][1] - 4.0) < 0.2, f"floor_stone_4x4 Y dimension not ~4m: {model_stats['floor_stone_4x4.glb']['dims']}"

assert abs(model_stats["wall_stone_solid.glb"]["dims"][0] - 4.0) < 0.5, f"wall_stone_solid X dimension not ~4m: {model_stats['wall_stone_solid.glb']['dims']}"
assert abs(model_stats["wall_stone_solid.glb"]["dims"][2] - 4.0) < 0.2, f"wall_stone_solid Z dimension not ~4m: {model_stats['wall_stone_solid.glb']['dims']}"

assert abs(model_stats["roof_gothic_vault_4x4.glb"]["dims"][0] - 4.0) < 0.3, f"roof_gothic_vault_4x4 X dimension not ~4m"
assert abs(model_stats["stairs_stone_4x4.glb"]["dims"][0] - 4.0) < 0.2, f"stairs_stone_4x4 X dimension not ~4m"

# 2. Check door clearance in wall_stone_arch_door.glb
# Let's inspect door cutout by checking mesh vertices in center X [-0.5, 0.5]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=target_models[3][1]) # wall_stone_arch_door
door_mesh = bpy.context.scene.objects[0].data
# Find lowest vertex near center (x in [-0.5, 0.5], y near wall center) above floor (z > 0.1)
center_verts_z = [v.co.z for v in door_mesh.vertices if abs(v.co.x) < 0.8 and abs(v.co.y) < 0.3 and v.co.z > 0.1]
door_clearance = min(center_verts_z) if center_verts_z else 0.0
print(f"wall_stone_arch_door archway opening clearance height: {door_clearance:.3f}m")
assert door_clearance >= 2.45, f"Door archway clearance {door_clearance:.3f}m is less than 2.45m!"

# 3. Check church_foundation_plinth.glb stairwell opening and South entrance steps
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(CHURCH_DIR, "church_foundation_plinth.glb"))
plinth_obj = bpy.context.scene.objects[0]
plinth_mesh = plinth_obj.data

# In Blender space: plinth has dims ~ [12.72, 23.28, 2.96]
# Upper stairwell cutout was specified at X in [-4.5, 4.5], Y in [-0.5, 12.5]
# Let's check if the plinth top surface has a cutout in this region!
# A solid top would have vertices at max_z across X in [-4, 4], Y in [2, 10].
max_z = max(v.co.z for v in plinth_mesh.vertices)
min_z = min(v.co.z for v in plinth_mesh.vertices)
print(f"church_foundation_plinth min_z={min_z:.3f}, max_z={max_z:.3f}")

# Check top surface vertices at max_z: are there vertices inside the cutout area?
top_verts_in_cutout = [v for v in plinth_mesh.vertices if abs(v.co.x) < 3.0 and 2.0 < v.co.y < 9.0 and v.co.z > max_z - 0.2]
print(f"Vertices on top surface in stairwell cutout area (X in [-3,3], Y in [2,9]): {len(top_verts_in_cutout)}")
assert len(top_verts_in_cutout) == 0, f"Stairwell cutout is blocked! Found {len(top_verts_in_cutout)} vertices at top surface!"

# Check South entrance steps: Y is negative or steps descend from 0.0 to -0.88m
# Check vertices with Y < -9.0 or near South edge:
south_verts = [v for v in plinth_mesh.vertices if v.co.y < -9.5]
print(f"South steps vertices count: {len(south_verts)}, min Y={min(v.co.y for v in plinth_mesh.vertices):.3f}")
assert len(south_verts) > 100, "South steps appear to be missing or insufficient!"

# 4. Check occult_rift_portal.glb hierarchy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=PORTAL_PATH)
scene_objs = {o.name: o for o in bpy.context.scene.objects}
print(f"occult_rift_portal objects: {list(scene_objs.keys())}")
assert "OccultRiftArchway" in scene_objs, "OccultRiftArchway not found in occult_rift_portal.glb"
assert "PortalVortexMesh" in scene_objs, "PortalVortexMesh not found in occult_rift_portal.glb"

arch = scene_objs["OccultRiftArchway"]
vortex = scene_objs["PortalVortexMesh"]
print(f"PortalVortexMesh parent: {vortex.parent.name if vortex.parent else None}")
assert vortex.parent == arch, f"PortalVortexMesh is not parented to OccultRiftArchway! Parent: {vortex.parent}"

# Check vortex mesh has UV coordinates
assert vortex.type == "MESH", "PortalVortexMesh is not a mesh object"
assert len(vortex.data.uv_layers) > 0, "PortalVortexMesh has no UV layers"
print(f"PortalVortexMesh UV layer: {vortex.data.uv_layers[0].name}, loops: {len(vortex.data.loops)}")

print("=== M1 (R2) INDEPENDENT VERIFICATION PASSED SUCCESSFULLY ===")
