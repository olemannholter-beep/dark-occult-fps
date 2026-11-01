import bpy
import bmesh
import math
import os
import random


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


def build_grass_clump(out_dir: str) -> None:
    clear_scene()
    mat_grass = make_pbr_material("OccultWindsweptGrass", (0.11, 0.13, 0.08, 1.0), roughness=0.88)

    bm = bmesh.new()

    # 9 varied, curved grass blades
    # Blender coords: X=right, Y=forward, Z=up -> Godot: X=right, Y=up, Z=-forward
    random.seed(42)
    blade_configs = [
        {"angle": 0.0, "rad": 0.05, "height": 0.58, "tilt": 0.28, "bend": 0.14, "w": 0.038},
        {"angle": 0.72, "rad": 0.08, "height": 0.64, "tilt": 0.35, "bend": 0.18, "w": 0.042},
        {"angle": 1.45, "rad": 0.06, "height": 0.48, "tilt": 0.25, "bend": 0.12, "w": 0.035},
        {"angle": 2.10, "rad": 0.11, "height": 0.54, "tilt": 0.38, "bend": 0.16, "w": 0.036},
        {"angle": 2.85, "rad": 0.07, "height": 0.62, "tilt": 0.30, "bend": 0.15, "w": 0.040},
        {"angle": 3.60, "rad": 0.09, "height": 0.52, "tilt": 0.34, "bend": 0.14, "w": 0.034},
        {"angle": 4.25, "rad": 0.05, "height": 0.66, "tilt": 0.26, "bend": 0.13, "w": 0.044},
        {"angle": 4.95, "rad": 0.10, "height": 0.45, "tilt": 0.42, "bend": 0.19, "w": 0.032},
        {"angle": 5.65, "rad": 0.07, "height": 0.56, "tilt": 0.32, "bend": 0.15, "w": 0.038},
    ]

    for cfg in blade_configs:
        ang = cfg["angle"]
        r = cfg["rad"]
        h = cfg["height"]
        tilt = cfg["tilt"]
        bend = cfg["bend"]
        base_w = cfg["w"]

        # Base origin of blade
        bx = r * math.cos(ang)
        by = r * math.sin(ang)

        # Direction vector in XY that blade leans toward
        dir_x = math.cos(ang)
        dir_y = math.sin(ang)
        # Perpendicular vector in XY for blade width
        perp_x = -dir_y
        perp_y = dir_x

        num_segments = 5
        prev_left = None
        prev_right = None

        for s in range(num_segments + 1):
            t = s / float(num_segments)
            # Quadratic curve outward and upward
            cur_z = h * t
            cur_reach = tilt * (t * t) + bend * (t * t * t)
            cx = bx + dir_x * cur_reach
            cy = by + dir_y * cur_reach

            # Width tapers to near zero at tip
            w = base_w * (1.0 - t * 0.92) * 0.5

            vl = bm.verts.new((cx - perp_x * w, cy - perp_y * w, cur_z))
            vr = bm.verts.new((cx + perp_x * w, cy + perp_y * w, cur_z))

            if prev_left is not None and prev_right is not None:
                bm.faces.new((prev_left, prev_right, vr, vl))
            prev_left = vl
            prev_right = vr

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("GrassClumpMesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("GrassClumpWild", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat_grass)

    for poly in obj.data.polygons:
        poly.use_smooth = True

    out_path = os.path.join(out_dir, "grass_clump_wild.glb")
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format='GLB',
        use_selection=True,
        export_yup=True,
        export_apply=True,
        export_materials='EXPORT',
    )
    print(f"[SUCCESS] Exported {out_path}")


def add_branch_mesh(
    bm: bmesh.types.BMesh,
    points: list[tuple[float, float, float]],
    radii: list[float],
    sides: int = 8,
) -> None:
    """Lofts a 3D tube with varied radius along a sequence of 3D points."""
    if len(points) < 2:
        return

    rings: list[list[bmesh.types.BMVert]] = []

    for idx, pt in enumerate(points):
        r = radii[idx]
        if idx == 0:
            fwd = (points[1][0] - pt[0], points[1][1] - pt[1], points[1][2] - pt[2])
        elif idx == len(points) - 1:
            fwd = (pt[0] - points[idx - 1][0], pt[1] - points[idx - 1][1], pt[2] - points[idx - 1][2])
        else:
            fwd = (points[idx + 1][0] - points[idx - 1][0], points[idx + 1][1] - points[idx - 1][1], points[idx + 1][2] - points[idx - 1][2])

        mag = math.hypot(math.hypot(fwd[0], fwd[1]), fwd[2])
        if mag > 0.0001:
            fwd = (fwd[0] / mag, fwd[1] / mag, fwd[2] / mag)
        else:
            fwd = (0.0, 0.0, 1.0)

        # Build orthonormal basis around forward tangent
        up_ref = (0.0, 1.0, 0.0) if abs(fwd[2]) > 0.9 else (0.0, 0.0, 1.0)
        # side = fwd x up_ref
        sx = fwd[1] * up_ref[2] - fwd[2] * up_ref[1]
        sy = fwd[2] * up_ref[0] - fwd[0] * up_ref[2]
        sz = fwd[0] * up_ref[1] - fwd[1] * up_ref[0]
        s_len = math.hypot(math.hypot(sx, sy), sz)
        if s_len > 0.0001:
            side = (sx / s_len, sy / s_len, sz / s_len)
        else:
            side = (1.0, 0.0, 0.0)

        # up = side x fwd
        ux = side[1] * fwd[2] - side[2] * fwd[1]
        uy = side[2] * fwd[0] - side[0] * fwd[2]
        uz = side[0] * fwd[1] - side[1] * fwd[0]
        up = (ux, uy, uz)

        ring_verts: list[bmesh.types.BMVert] = []
        for i in range(sides):
            th = i * (2.0 * math.pi / sides)
            c = math.cos(th) * r
            s = math.sin(th) * r
            vx = pt[0] + side[0] * c + up[0] * s
            vy = pt[1] + side[1] * c + up[1] * s
            vz = pt[2] + side[2] * c + up[2] * s
            ring_verts.append(bm.verts.new((vx, vy, vz)))

        rings.append(ring_verts)

    # Bridge rings
    for idx in range(len(rings) - 1):
        r1 = rings[idx]
        r2 = rings[idx + 1]
        for i in range(sides):
            ni = (i + 1) % sides
            bm.faces.new((r1[i], r2[i], r2[ni], r1[ni]))

    # Cap base and tip
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))


def build_dead_tree(out_dir: str) -> None:
    clear_scene()
    mat_bark = make_pbr_material("GothicCharredBark", (0.08, 0.07, 0.07, 1.0), roughness=0.92)

    bm = bmesh.new()

    # 1. Main gnarled trunk (Z = 0.0m to 5.5m)
    trunk_pts = [
        (0.0, 0.0, 0.0),
        (0.04, 0.02, 0.6),
        (-0.06, 0.08, 1.4),
        (-0.12, 0.05, 2.2),
        (0.02, -0.04, 3.1),
        (0.14, -0.09, 3.9),
        (0.22, -0.15, 4.7),
        (0.28, -0.21, 5.5),
    ]
    trunk_radii = [0.44, 0.36, 0.30, 0.25, 0.20, 0.15, 0.10, 0.04]
    add_branch_mesh(bm, trunk_pts, trunk_radii, sides=10)

    # 2. Main Branch 1 (splitting North-West at Z = 2.2m up to Z = 4.8m)
    b1_pts = [
        (-0.12, 0.05, 2.2),
        (-0.35, 0.28, 2.8),
        (-0.68, 0.52, 3.4),
        (-1.08, 0.74, 4.0),
        (-1.42, 0.88, 4.5),
        (-1.75, 0.96, 4.8),
    ]
    b1_radii = [0.18, 0.15, 0.12, 0.09, 0.06, 0.03]
    add_branch_mesh(bm, b1_pts, b1_radii, sides=8)

    # Sub-branch 1A (claws downward)
    b1a_pts = [
        (-0.68, 0.52, 3.4),
        (-0.95, 0.42, 3.2),
        (-1.24, 0.34, 3.0),
        (-1.48, 0.28, 2.75),
    ]
    add_branch_mesh(bm, b1a_pts, [0.08, 0.06, 0.04, 0.02], sides=6)

    # 3. Main Branch 2 (splitting North-East at Z = 2.8m up to Z = 5.2m)
    b2_pts = [
        (-0.02, 0.02, 2.8),
        (0.35, 0.26, 3.4),
        (0.72, 0.55, 4.0),
        (1.15, 0.78, 4.6),
        (1.52, 0.94, 5.0),
        (1.85, 1.05, 5.2),
    ]
    b2_radii = [0.19, 0.16, 0.13, 0.09, 0.06, 0.03]
    add_branch_mesh(bm, b2_pts, b2_radii, sides=8)

    # Sub-branch 2A (twisting upward)
    b2a_pts = [
        (0.72, 0.55, 4.0),
        (0.92, 0.45, 4.4),
        (1.12, 0.38, 4.8),
        (1.28, 0.32, 5.15),
    ]
    add_branch_mesh(bm, b2a_pts, [0.07, 0.05, 0.035, 0.02], sides=6)

    # 4. Main Branch 3 (arching South at Z = 3.3m up to Z = 4.7m)
    b3_pts = [
        (0.06, -0.06, 3.3),
        (0.12, -0.42, 3.8),
        (0.18, -0.85, 4.2),
        (0.25, -1.25, 4.5),
        (0.30, -1.55, 4.7),
    ]
    b3_radii = [0.16, 0.13, 0.10, 0.06, 0.03]
    add_branch_mesh(bm, b3_pts, b3_radii, sides=8)

    # Sub-branch 3A (claws out West)
    b3a_pts = [
        (0.18, -0.85, 4.2),
        (-0.15, -1.10, 4.1),
        (-0.45, -1.35, 3.9),
    ]
    add_branch_mesh(bm, b3a_pts, [0.06, 0.04, 0.02], sides=6)

    # 5. Gnarled ground root flares (Z = 0.6m down to 0.0m)
    root_configs = [
        [(0.0, 0.0, 0.6), (-0.28, -0.25, 0.28), (-0.65, -0.55, 0.05), (-0.95, -0.78, 0.0)],
        [(0.0, 0.0, 0.6), (0.28, -0.22, 0.28), (0.65, -0.48, 0.05), (0.92, -0.68, 0.0)],
        [(0.0, 0.0, 0.6), (-0.26, 0.28, 0.28), (-0.58, 0.58, 0.05), (-0.88, 0.85, 0.0)],
        [(0.0, 0.0, 0.6), (0.25, 0.26, 0.28), (0.55, 0.54, 0.05), (0.84, 0.78, 0.0)],
    ]
    for r_pts in root_configs:
        add_branch_mesh(bm, r_pts, [0.22, 0.16, 0.10, 0.04], sides=6)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("DeadTreeMesh")
    bm.to_mesh(mesh)
    bm.free()

    tree_obj = bpy.data.objects.new("DeadTreeGnarled", mesh)
    bpy.context.collection.objects.link(tree_obj)
    tree_obj.data.materials.append(mat_bark)

    for poly in tree_obj.data.polygons:
        poly.use_smooth = True

    # Add procedural texture + DISPLACE modifier for deep rough charred bark crevice texture
    tex = bpy.data.textures.new("BarkGnarledNoise", type='CLOUDS')
    tex.noise_scale = 0.65
    tex.noise_depth = 3

    disp_mod = tree_obj.modifiers.new(name="BarkDisplace", type='DISPLACE')
    disp_mod.texture = tex
    disp_mod.mid_level = 0.5
    disp_mod.strength = 0.045

    bpy.context.view_layer.objects.active = tree_obj
    bpy.ops.object.modifier_apply(modifier=disp_mod.name)

    out_path = os.path.join(out_dir, "dead_tree_gnarled.glb")
    bpy.ops.object.select_all(action='DESELECT')
    tree_obj.select_set(True)

    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format='GLB',
        use_selection=True,
        export_yup=True,
        export_apply=True,
        export_materials='EXPORT',
    )
    print(f"[SUCCESS] Exported {out_path}")


def build_all_foliage() -> None:
    out_dir = os.path.join(os.getcwd(), "assets", "models")
    os.makedirs(out_dir, exist_ok=True)
    build_grass_clump(out_dir)
    build_dead_tree(out_dir)


if __name__ == "__main__":
    build_all_foliage()
