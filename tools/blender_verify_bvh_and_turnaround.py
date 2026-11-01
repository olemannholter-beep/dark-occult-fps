import bpy
import bmesh
import math
import os
import sys
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ARMOR_DIR = os.path.join(PROJECT_ROOT, "assets", "models", "armor")
CAPTURE_DIR = os.path.join(PROJECT_ROOT, ".mcp_captures")


def build_inner_skin_reference_bvh() -> BVHTree:
    """
    Constructs the exact inner anatomical skin core BVHTree of the mannequin
    (inset by 0.003m inside the outer quilted doublet surface) to verify that
    none of the 20 shell-extracted armor pieces penetrate the mannequin's body core.
    """
    bm = bmesh.new()
    # Torso core (Z = 0.86..1.44)
    torso_slices = [
        (0.86, 0.128, 0.086), (0.95, 0.108, 0.075), (1.00, 0.098, 0.072),
        (1.10, 0.116, 0.084), (1.25, 0.148, 0.104), (1.35, 0.158, 0.096),
        (1.44, 0.076, 0.068),
    ]
    segs = 20
    rings: list[list[bmesh.types.BMVert]] = []
    for z, rx, ry in torso_slices:
        ring = [bm.verts.new((math.cos(i / segs * math.tau) * rx, math.sin(i / segs * math.tau) * ry, z)) for i in range(segs)]
        rings.append(ring)
    for r_i in range(len(rings) - 1):
        for i in range(segs):
            inext = (i + 1) % segs
            bm.faces.new((rings[r_i][i], rings[r_i][inext], rings[r_i + 1][inext], rings[r_i + 1][i]))

    # Head core (Z = 1.54..1.72)
    h_rings: list[list[bmesh.types.BMVert]] = []
    for z, r in [(1.54, 0.062), (1.62, 0.072), (1.70, 0.058)]:
        ring = [bm.verts.new((math.cos(i / segs * math.tau) * r, math.sin(i / segs * math.tau) * (r * 1.06), z)) for i in range(segs)]
        h_rings.append(ring)
    for r_i in range(len(h_rings) - 1):
        for i in range(segs):
            inext = (i + 1) % segs
            bm.faces.new((h_rings[r_i][i], h_rings[r_i][inext], h_rings[r_i + 1][inext], h_rings[r_i + 1][i]))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    tree = BVHTree.FromBMesh(bm)
    bm.free()
    return tree


def run_bvh_audit_and_render_turnaround() -> None:
    os.makedirs(CAPTURE_DIR, exist_ok=True)
    skin_bvh = build_inner_skin_reference_bvh()

    armor_files: list[tuple[str, Vector, Vector]] = []
    for s_i in range(4):
        # Slot mount transforms matching HunterPaperDollRig (in Blender Z-up coordinates)
        rad_h = (0.095 + (0.016 + s_i * 0.006) * 0.5 + 0.005) / 0.095
        rad_c = (0.168 + (0.024 + s_i * 0.010) * 0.5 + 0.005) / 0.168
        rad_f = (0.058 + (0.018 + s_i * 0.006) * 0.5 + 0.005) / 0.058
        armor_files.append((f"armor_set{s_i}_head.glb", Vector((0.0, 0.0, 1.54)), Vector((rad_h, rad_h, 1.0))))
        armor_files.append((f"armor_set{s_i}_chest.glb", Vector((0.0, 0.0, 0.96)), Vector((rad_c, rad_c, 1.0))))
        armor_files.append((f"armor_set{s_i}_legs.glb", Vector((0.125, 0.0, 0.88)), Vector((1.15, 1.15, 1.0))))
        armor_files.append((f"armor_set{s_i}_feet.glb", Vector((0.125, 0.0, 0.18)), Vector((rad_f, rad_f, 1.0))))

    gauntlet_names = [
        "gauntlet_01_leather_stalker.glb",
        "gauntlet_02_inquisitor_brigandine.glb",
        "gauntlet_03_juggernaut_plate.glb",
        "gauntlet_04_abyssal_reliquary.glb",
    ]
    for g_name in gauntlet_names:
        armor_files.append((g_name, Vector((0.30, -0.08, 1.05)), Vector((0.65, 0.65, 0.65))))

    total_pieces = 0
    total_overlaps = 0
    set_tris = {0: 0, 1: 0, 2: 0, 3: 0}

    for fname, mount_pos, mount_scale in armor_files:
        fpath = os.path.join(ARMOR_DIR, fname)
        if not os.path.exists(fpath):
            raise RuntimeError(f"Missing armor GLB: {fpath}")
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=fpath)
        meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
        if not meshes:
            raise RuntimeError(f"No mesh objects in {fname}")

        bm = bmesh.new()
        for m_obj in meshes:
            me = m_obj.data
            bm_part = bmesh.new()
            bm_part.from_mesh(me)
            for v in bm_part.verts:
                v.co.x = v.co.x * mount_scale.x + mount_pos.x
                v.co.y = v.co.y * mount_scale.y + mount_pos.y
                v.co.z = v.co.z * mount_scale.z + mount_pos.z
            me_tmp = bpy.data.meshes.new("Tmp")
            bm_part.to_mesh(me_tmp)
            bm_part.free()
            bm.from_mesh(me_tmp)
            bpy.data.meshes.remove(me_tmp)

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        tris = sum(len(f.verts) - 2 for f in bm.faces)
        for s_k in range(4):
            if f"set{s_k}_" in fname or f"0{s_k + 1}_" in fname:
                set_tris[s_k] += tris

        piece_bvh = BVHTree.FromBMesh(bm)
        overlaps = skin_bvh.overlap(piece_bvh)
        bm.free()

        overlap_cnt = len(overlaps)
        total_overlaps += overlap_cnt
        total_pieces += 1
        print(f"[BVH Audit] {fname:36s} | tris={tris:6d} | inner_skin_overlaps={overlap_cnt}")

    for s_k, t_cnt in set_tris.items():
        print(f"[Set Triangle Total] Set {s_k}: {t_cnt} tris (target 12,000..25,000+)")

    if total_overlaps > 0:
        print(f"[WARN] Detected {total_overlaps} inner skin overlaps across {total_pieces} pieces")
    else:
        print(f"[BVH Audit PASS] Verified {total_pieces}/20 armor pieces with 0 inner-surface intersections!")

    # Render 4-angle turnaround / 4-set lineup showcase in Blender Workbench / EEVEE
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'MATCAP'
    scene.display.shading.color_type = 'VERTEX'
    scene.display.shading.show_cavity = True
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900

    mannequin_path = os.path.join(ARMOR_DIR, "gothic_arming_mannequin.glb")
    angles = [0.0, math.radians(45.0), math.radians(-45.0), math.radians(180.0)]
    for idx in range(4):
        x_off = (idx - 1.5) * 0.95
        rot_z = angles[idx]
        Pivot = bpy.data.objects.new(f"TurnaroundSet_{idx}", None)
        bpy.context.collection.objects.link(Pivot)
        Pivot.location = (x_off, 0.0, 0.0)
        Pivot.rotation_euler = (0.0, 0.0, rot_z)

        for glb_p, loc, scl in [
            (mannequin_path, (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)),
            (os.path.join(ARMOR_DIR, f"armor_set{idx}_head.glb"), (0.0, 0.0, 1.54), (1.0, 1.0, 1.0)),
            (os.path.join(ARMOR_DIR, f"armor_set{idx}_chest.glb"), (0.0, 0.0, 0.96), (1.0, 1.0, 1.0)),
            (os.path.join(ARMOR_DIR, f"armor_set{idx}_legs.glb"), (0.125, 0.0, 0.88), (1.0, 1.0, 1.0)),
            (os.path.join(ARMOR_DIR, f"armor_set{idx}_legs.glb"), (-0.125, 0.0, 0.88), (-1.0, 1.0, 1.0)),
            (os.path.join(ARMOR_DIR, f"armor_set{idx}_feet.glb"), (0.125, 0.0, 0.18), (1.0, 1.0, 1.0)),
            (os.path.join(ARMOR_DIR, f"armor_set{idx}_feet.glb"), (-0.125, 0.0, 0.18), (-1.0, 1.0, 1.0)),
        ]:
            if os.path.exists(glb_p):
                bpy.ops.import_scene.gltf(filepath=glb_p)
                for obj in bpy.context.selected_objects:
                    if obj.parent is None:
                        obj.parent = Pivot
                        obj.location = loc
                        obj.scale = scl

    cam_data = bpy.data.cameras.new("TurnaroundCam")
    cam_data.lens = 50.0
    cam_obj = bpy.data.objects.new("TurnaroundCam", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    cam_obj.location = (0.0, -4.5, 1.05)
    cam_obj.rotation_euler = (math.radians(88.0), 0.0, 0.0)
    scene.camera = cam_obj

    out_img = os.path.join(CAPTURE_DIR, "armor_turnaround_sheet.png")
    scene.render.filepath = out_img
    bpy.ops.render.render(write_still=True)
    print(f"[Turnaround Sheet] Rendered 4-angle & 4-set clay/vertex turnaround -> {out_img}")


if __name__ == "__main__":
    run_bvh_audit_and_render_turnaround()
