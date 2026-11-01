import bpy
import bmesh
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blender_detail_kit import bake_3tone_gothic_vertex_colors


def clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_pbr_material(
    name: str,
    base_color: tuple[float, float, float, float],
    roughness: float,
    metallic: float = 0.0,
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = base_color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
    return mat


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    if edge1 == edge0:
        return 0.0
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def compute_terrain_height(gx: float, gz: float) -> tuple[float, float]:
    """
    Compute elevation in Godot world coordinates (gx, gz) where:
    - Valley path runs from gz = +38 (Y ~ 0.15) North to gz = -10.5 (Y = 3.20)
    - House A pad around (-16, +14) flattened near Y = 0.85
    - House B pad around (+16, +8) flattened near Y = 1.15
    - Hilltop church plateau around gx in [-9, +9], gz in [-34, -11.5] flattened at Y = 3.55
      (just under the 0.35m church floor slab whose top is at Y = 4.0m)
    Returns (height_y, flatten_weight) where flatten_weight in [0, 1] suppresses displace noise.
    """
    # Base rolling hills (low-frequency smooth undulations)
    hills = (
        1.45 * math.sin(gx * 0.05) * math.cos(gz * 0.045)
        + 0.95 * math.cos((gx + 15.0) * 0.08) * math.sin((gz - 8.0) * 0.075)
        + 0.25 * math.sin(gx * 0.14 + gz * 0.13)
    )
    # Rise naturally toward edges of the valley (East/West ridges) and North hill
    edge_ridge = 0.0030 * (gx * gx)
    north_slope = smoothstep(20.0, -22.0, gz) * 3.4 + smoothstep(-20.0, -38.0, gz) * 1.6
    base_h = max(0.0, 0.55 + hills * 0.60 + edge_ridge + north_slope)

    # 1. Valley Road mask: x centered near 0, z from +44 to -10.0 (wide smooth margin)
    road_z_factor = smoothstep(48.0, 34.0, gz) * smoothstep(-14.5, -9.0, gz)
    road_x_dist = abs(gx - 1.2 * math.sin(gz * 0.09))
    road_mask = (1.0 - smoothstep(4.5, 11.5, road_x_dist)) * road_z_factor
    # Smoothly ramp road from Y = 0.15 at gz = +28 up to Y = 3.20 at gz = -10.0
    road_progress = smoothstep(26.0, -10.2, gz)
    road_h = 0.15 + road_progress * (3.20 - 0.15)

    # 2. House A footprint pad (West side, gx = -16, gz = +14, target Y = 0.85)
    dist_ha = math.hypot((gx - (-16.0)) / 1.1, (gz - 14.0) / 1.2)
    mask_ha = 1.0 - smoothstep(5.5, 11.5, dist_ha)
    h_ha = 0.85

    # 3. House B footprint pad (East side, gx = +16, gz = +8, target Y = 1.15)
    dist_hb = math.hypot((gx - 16.0) / 1.1, (gz - 8.0) / 1.2)
    mask_hb = 1.0 - smoothstep(5.5, 11.5, dist_hb)
    h_hb = 1.15

    # 4. Church Hilltop Plateau:
    # Front plaza (gz in [-12.0, -8.5], gx in [-15.0, +15.0]) at Y = 3.20m
    # Grand Cruciform Cathedral & Crypt plateau (gz in [-59.0, -12.0], gx in [-15.0, +15.0]) at Y = 3.55m
    box_dx = max(0.0, abs(gx) - 15.0)
    if gz > -22.0:
        box_dz = max(0.0, gz - (-9.0))
    else:
        box_dz = max(0.0, (-59.0) - gz)
    dist_church = math.hypot(box_dx, box_dz)
    mask_church = 1.0 - smoothstep(0.5, 10.5, dist_church)
    church_ramp = smoothstep(-9.5, -12.2, gz)
    h_church = 3.20 + church_ramp * (3.55 - 3.20)

    # Blend masks cleanly
    h = base_h
    h = h * (1.0 - road_mask) + road_h * road_mask
    h = h * (1.0 - mask_ha) + h_ha * mask_ha
    h = h * (1.0 - mask_hb) + h_hb * mask_hb
    h = h * (1.0 - mask_church) + h_church * mask_church

    flatten_weight = max(road_mask, mask_ha, mask_hb, mask_church)
    return (h, flatten_weight)


def build_terrain() -> None:
    clear_scene()

    mat_grass = make_pbr_material("OccultMoorGrass", (0.09, 0.11, 0.08, 1.0), roughness=0.92)
    mat_path = make_pbr_material("DarkMudPath", (0.14, 0.11, 0.09, 1.0), roughness=0.88)
    mat_cliff = make_pbr_material("CragCliffStone", (0.16, 0.16, 0.18, 1.0), roughness=0.84)

    # Create 120m x 120m high-density grid (160 x 160 subdivisions = 0.75m spacing)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=160, y_segments=160, size=60.0)

    mesh = bpy.data.meshes.new("TerrainTownMesh")
    bm.to_mesh(mesh)
    bm.free()

    terrain_obj = bpy.data.objects.new("TerrainTown", mesh)
    bpy.context.collection.objects.link(terrain_obj)

    terrain_obj.data.materials.append(mat_grass)
    terrain_obj.data.materials.append(mat_path)
    terrain_obj.data.materials.append(mat_cliff)

    # Vertex group for procedural DISPLACE modifier (strictly suppressed on walkable road & plateaus)
    vg_displace = terrain_obj.vertex_groups.new(name="HillsideDisplace")

    for v in mesh.vertices:
        # Blender (bx, by, bz) -> Godot (gx = bx, gy = bz, gz = -by)
        gx = v.co.x
        gz = -v.co.y
        hy, flat_w = compute_terrain_height(gx, gz)
        v.co.z = hy
        raw_disp = max(0.0, 1.0 - flat_w)
        disp_weight = raw_disp * raw_disp
        vg_displace.add([v.index], disp_weight, 'REPLACE')

    mesh.update()

    # Assign material indices based on position/slope
    for poly in mesh.polygons:
        cx = poly.center.x
        cz = -poly.center.y
        road_x_dist = abs(cx - 1.2 * math.sin(cz * 0.09))
        is_road = (road_x_dist < 3.6 and -11.5 <= cz <= 36.0)
        is_plaza = (abs(cx) < 8.5 and -34.0 <= cz <= -9.5)
        if is_road or is_plaza:
            poly.material_index = 1  # DarkMudPath
        elif poly.normal.z < 0.86 or poly.center.z > 4.2:
            poly.material_index = 2  # CragCliffStone
        else:
            poly.material_index = 0  # OccultMoorGrass

    # Add procedural texture + DISPLACE modifier (AGENTS.md Rule 7.2 & 9.1)
    tex = bpy.data.textures.new("TerrainRockNoise", type='CLOUDS')
    tex.noise_scale = 5.5
    tex.noise_depth = 2

    disp_mod = terrain_obj.modifiers.new(name="OrganicDisplace", type='DISPLACE')
    disp_mod.texture = tex
    disp_mod.vertex_group = "HillsideDisplace"
    disp_mod.direction = 'Z'
    disp_mod.mid_level = 0.5
    disp_mod.strength = 0.35

    # Smooth modifier so terrain trimesh has zero sharp micro-ledges anywhere
    smooth_mod = terrain_obj.modifiers.new(name="SmoothWalkableSurface", type='SMOOTH')
    smooth_mod.factor = 0.45
    smooth_mod.iterations = 3
    smooth_mod.use_x = False
    smooth_mod.use_y = False
    smooth_mod.use_z = True

    bpy.context.view_layer.objects.active = terrain_obj
    bpy.ops.object.modifier_apply(modifier=disp_mod.name)
    bpy.ops.object.modifier_apply(modifier=smooth_mod.name)

    # Ensure terrain over buried Level-0 Crypt wings (Y = 0.0m..4.05m) outside the Church Nave
    # stays strictly above Y = 4.35m so the terrain underside never intersects crypt ceilings.
    for v in terrain_obj.data.vertices:
        gx = v.co.x
        gz = -v.co.y
        if -30.0 <= gx <= 30.0 and gz <= -47.5:
            in_church_nave = (-13.8 <= gx <= 13.8 and gz >= -57.8)
            if not in_church_nave:
                z_blend = smoothstep(-47.5, -49.5, gz)
                min_roof_cover = 3.55 + z_blend * (4.35 - 3.55)
                if v.co.z < min_roof_cover:
                    v.co.z = min_roof_cover
    terrain_obj.data.update()

    # CRITICAL (AGENTS.md Rule 9.1): Carve BOOLEAN DIFFERENCE cutout for stairwell & Crypt under Grand Cruciform Cathedral
    # World X in [-13.8, +13.8], World Z in [-57.8, -22.0]
    # Center in Godot: gx = 0.0, gz = -39.9 -> Blender: bx = 0.0, by = +39.9
    # Size: width X = 27.6m, length Y = 35.8m, height Z = 20.0m
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 39.9, 2.0))
    cutter = bpy.context.active_object
    cutter.name = "CryptTerrainCutter"
    cutter.scale = (27.6, 35.8, 20.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    bool_mod = terrain_obj.modifiers.new(name="CryptCutoutBoolean", type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.solver = 'EXACT'
    bool_mod.object = cutter

    bpy.context.view_layer.objects.active = terrain_obj
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)

    # Delete cutter helper
    bpy.data.objects.remove(cutter, do_unlink=True)

    # Triangulate & shade smooth with weighted normals for clean trimesh collision & shading
    tri_mod = terrain_obj.modifiers.new(name="Triangulate", type='TRIANGULATE')
    bpy.ops.object.modifier_apply(modifier=tri_mod.name)

    for poly in terrain_obj.data.polygons:
        poly.use_smooth = True

    # Bake subtle vertex cavity / slope shading into 'Col' clamped to [0.65, 1.00]
    t_mesh = terrain_obj.data
    if "Col" in t_mesh.color_attributes:
        col_attr = t_mesh.color_attributes["Col"]
    else:
        col_attr = t_mesh.color_attributes.new(name="Col", type='BYTE_COLOR', domain='CORNER')
    for poly in t_mesh.polygons:
        slope_shade = max(0.68, min(1.00, 0.72 + 0.28 * max(0.0, poly.normal.z)))
        for loop_idx in poly.loop_indices:
            col_attr.data[loop_idx].color = (slope_shade, slope_shade, slope_shade, 1.0)

    out_dir = os.path.join(os.getcwd(), "assets", "models")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "terrain_town.glb")

    bpy.ops.object.select_all(action='DESELECT')
    terrain_obj.select_set(True)
    bpy.context.view_layer.objects.active = terrain_obj

    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format='GLB',
        use_selection=True,
        export_yup=True,
        export_apply=True,
        export_materials='EXPORT',
        export_all_vertex_colors=True,
        export_active_vertex_color_when_no_material=True,
    )
    print(f"[SUCCESS] Exported terrain to {out_path}")


if __name__ == "__main__":
    build_terrain()
