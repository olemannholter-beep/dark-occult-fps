"""
Blender 5.x Procedural 3D Asset Builder — Biomes 2, 3 & 4 Hero Architectural Kits
Generates 9 high-detail gothic dungeon architectural & centerpiece assets (`90–155+` parts each)
with 3-tone vertex cavity colors and material-slot pre-export mesh joining (`<= 8` mesh nodes per GLB):

Biome 2 (*The Iron Necropolis*):
1. necropolis_wall_armory_4x4.glb      (4.0m x 4.0m x 0.5m, 125+ parts)
2. necropolis_iron_maiden_monolith.glb (2.4m x 3.8m x 2.4m, 145+ parts)
3. necropolis_hanging_war_brazier.glb  (1.8m x 1.8m, 95+ parts)

Biome 3 (*The Astral Reliquary*):
4. reliquary_wall_grimoire_4x4.glb     (4.0m x 4.0m x 0.5m, 135+ parts)
5. reliquary_astral_orrery_monolith.glb(2.6m x 3.9m x 2.6m, 152+ parts)
6. reliquary_chandelier_astrolabe.glb  (2.0m x 1.8m, 98+ parts)

Biome 4 (*The Blood-Forged Abattoir*):
7. abattoir_wall_furnace_4x4.glb       (4.0m x 4.0m x 0.5m, 130+ parts)
8. abattoir_blood_press_monolith.glb   (2.5m x 3.8m x 2.5m, 148+ parts)
9. abattoir_hanging_hook_rack.glb      (1.8m x 1.8m, 94+ parts)
"""

import math
import os
import sys
import bpy
import bmesh
from mathutils import Matrix, Vector, Euler

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import blender_detail_kit as kit


class _KitHelpers:
    @staticmethod
    def clear_scene() -> None:
        bpy.ops.wm.read_factory_settings(use_empty=True)

    @staticmethod
    def make_pbr_material(
        name: str,
        rgb: tuple[float, float, float],
        roughness: float = 0.85,
        metallic: float = 0.0,
        emission: tuple[float, float, float] | None = None,
        emission_strength: float = 0.0,
    ) -> bpy.types.Material:
        mat = bpy.data.materials.new(name=name)
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        bsdf = nodes.get("Principled BSDF")
        base_rgba = (rgb[0], rgb[1], rgb[2], 1.0)
        if bsdf is not None:
            bsdf.inputs["Base Color"].default_value = base_rgba
            bsdf.inputs["Roughness"].default_value = roughness
            bsdf.inputs["Metallic"].default_value = metallic
            if emission is not None and "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = (emission[0], emission[1], emission[2], 1.0)
                bsdf.inputs["Emission Strength"].default_value = emission_strength
            vcol = nodes.new(type="ShaderNodeVertexColor")
            vcol.layer_name = "Col"
            mix = nodes.new(type="ShaderNodeMix")
            mix.data_type = 'RGBA'
            mix.blend_type = 'MULTIPLY'
            mix.inputs[0].default_value = 1.0
            mix.inputs[6].default_value = base_rgba
            links.new(vcol.outputs["Color"], mix.inputs[7])
            links.new(mix.outputs[2], bsdf.inputs["Base Color"])
        return mat

    @staticmethod
    def _new_bm_obj(name: str, bm: bmesh.types.BMesh, mat: bpy.types.Material) -> bpy.types.Object:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for f in bm.faces:
            f.smooth = True
        mesh = bpy.data.meshes.new(name + "Mesh")
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        obj.data.materials.append(mat)
        return obj

    @staticmethod
    def create_beveled_box(
        name: str,
        loc: tuple[float, float, float],
        size: tuple[float, float, float],
        mat: bpy.types.Material,
        bevel_width: float = 0.012,
        rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> bpy.types.Object:
        bm = bmesh.new()
        kit._add_bm_beveled_box(bm, size, loc, rotation, bevel_width, 0)
        return _KitHelpers._new_bm_obj(name, bm, mat)

    @staticmethod
    def create_beveled_cylinder(
        name: str,
        loc: tuple[float, float, float],
        radius: float,
        depth: float,
        mat: bpy.types.Material,
        vertices: int = 12,
        rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> bpy.types.Object:
        bm = bmesh.new()
        rot_mat = Euler(rotation, 'XYZ').to_matrix().to_4x4()
        xform = Matrix.Translation(Vector(loc)) @ rot_mat
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=False,
            segments=vertices,
            radius1=radius,
            radius2=radius,
            depth=depth,
            matrix=xform,
        )
        return _KitHelpers._new_bm_obj(name, bm, mat)

    @staticmethod
    def create_tapered_prism(
        name: str,
        loc: tuple[float, float, float],
        r_bottom: float,
        r_top: float,
        depth: float,
        mat: bpy.types.Material,
        sides: int = 8,
        rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> bpy.types.Object:
        bm = bmesh.new()
        rot_mat = Euler(rotation, 'XYZ').to_matrix().to_4x4()
        xform = Matrix.Translation(Vector(loc)) @ rot_mat
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=False,
            segments=sides,
            radius1=r_bottom,
            radius2=r_top,
            depth=depth,
            matrix=xform,
        )
        return _KitHelpers._new_bm_obj(name, bm, mat)

    @staticmethod
    def create_torus_ring(
        name: str,
        loc: tuple[float, float, float],
        major_radius: float,
        minor_radius: float,
        mat: bpy.types.Material,
        major_seg: int = 24,
        minor_seg: int = 8,
        rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> bpy.types.Object:
        bpy.ops.mesh.primitive_torus_add(
            major_segments=major_seg,
            minor_segments=minor_seg,
            major_radius=major_radius,
            minor_radius=minor_radius,
            location=loc,
            rotation=rotation,
        )
        obj = bpy.context.active_object
        obj.name = name
        obj.data.materials.clear()
        obj.data.materials.append(mat)
        for poly in obj.data.polygons:
            poly.use_smooth = True
        return obj

    @staticmethod
    def spawn_rivet_line(
        prefix: str,
        p0: Vector,
        p1: Vector,
        count: int,
        radius: float,
        mat: bpy.types.Material,
        axis: str = "Y",
    ) -> list[bpy.types.Object]:
        objs: list[bpy.types.Object] = []
        for i in range(count):
            t = i / max(1, count - 1)
            p = p0.lerp(p1, t)
            objs.append(
                _KitHelpers.create_beveled_box(
                    f"{prefix}_{i}",
                    (p.x, p.y, p.z),
                    (radius * 2.0, radius * 1.4, radius * 2.0),
                    mat,
                    bevel_width=radius * 0.35,
                )
            )
        return objs

    @staticmethod
    def spawn_chain_links(
        prefix: str,
        p0: Vector,
        p1: Vector,
        count: int,
        mat: bpy.types.Material,
        link_radius: float = 0.045,
        wire_radius: float = 0.012,
    ) -> list[bpy.types.Object]:
        objs: list[bpy.types.Object] = []
        diff = p1 - p0
        base_yaw = math.atan2(diff.y, diff.x)
        for i in range(count):
            t = (i + 0.5) / max(1, count)
            p = p0.lerp(p1, t)
            roll = (math.pi * 0.5) if (i % 2 == 1) else 0.0
            objs.append(
                _KitHelpers.create_beveled_box(
                    f"{prefix}_{i}",
                    (p.x, p.y, p.z),
                    (link_radius * 2.1, wire_radius * 2.4, link_radius * 1.35),
                    mat,
                    bevel_width=wire_radius * 0.4,
                    rotation=(roll, 0.0, base_yaw),
                )
            )
        return objs

    @staticmethod
    def finalize_and_export_glb(
        out_path: str,
        parts: list[bpy.types.Object],
        base_rgb: tuple[float, float, float] = (0.20, 0.20, 0.22),
        cavity_rgb: tuple[float, float, float] = (0.08, 0.08, 0.10),
        edge_rgb: tuple[float, float, float] = (0.38, 0.36, 0.32),
    ) -> None:
        # Group mesh objects by material so each GLB exports with <= 8 mesh nodes (1 per material slot)
        by_mat: dict[str, list[bpy.types.Object]] = {}
        for o in parts:
            if o is None or o.type != 'MESH':
                continue
            mat_name = o.data.materials[0].name if len(o.data.materials) > 0 and o.data.materials[0] is not None else "Default"
            by_mat.setdefault(mat_name, []).append(o)

        joined_objs: list[bpy.types.Object] = []
        for mat_name, group in by_mat.items():
            bpy.ops.object.select_all(action='DESELECT')
            for g_obj in group:
                g_obj.select_set(True)
            bpy.context.view_layer.objects.active = group[0]
            if len(group) > 1:
                bpy.ops.object.join()
            j_obj = bpy.context.view_layer.objects.active
            j_obj.name = f"Mesh_{mat_name}"
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            kit.bake_3tone_gothic_vertex_colors(j_obj, z_min=-1.8, z_max=4.0)
            joined_objs.append(j_obj)

        bpy.ops.object.select_all(action='DESELECT')
        for j_obj in joined_objs:
            j_obj.select_set(True)
        if joined_objs:
            bpy.context.view_layer.objects.active = joined_objs[0]

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
        print(f"[Biomes2to4Kit] Exported {out_path} ({len(parts)} parts joined into {len(joined_objs)} material-slot meshes)")


for _attr in (
    "clear_scene",
    "make_pbr_material",
    "create_beveled_box",
    "create_beveled_cylinder",
    "create_tapered_prism",
    "create_torus_ring",
    "spawn_rivet_line",
    "spawn_chain_links",
    "finalize_and_export_glb",
):
    setattr(kit, _attr, getattr(_KitHelpers, _attr))

PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
OUT_DIR = os.path.join(PROJECT_ROOT, "assets", "models", "dungeon")


def make_materials() -> dict:
    return {
        "StoneDark": kit.make_pbr_material("StoneDark", (0.20, 0.19, 0.18), roughness=0.92, metallic=0.0),
        "StoneTrim": kit.make_pbr_material("StoneTrim", (0.27, 0.25, 0.23), roughness=0.88, metallic=0.0),
        "WroughtIron": kit.make_pbr_material("WroughtIron", (0.14, 0.15, 0.17), roughness=0.46, metallic=0.86),
        "TarnishedBrass": kit.make_pbr_material("TarnishedBrass", (0.58, 0.45, 0.22), roughness=0.40, metallic=0.88),
        "Bone": kit.make_pbr_material("Bone", (0.64, 0.58, 0.47), roughness=0.84, metallic=0.0),
        "DarkTimber": kit.make_pbr_material("DarkTimber", (0.18, 0.11, 0.08), roughness=0.88, metallic=0.0),
        "EmissiveAmberFlame": kit.make_pbr_material(
            "EmissiveAmberFlame",
            (1.0, 0.58, 0.16),
            roughness=0.25,
            metallic=0.0,
            emission=(1.0, 0.52, 0.12),
            emission_strength=5.2,
        ),
        "EmissiveVioletRune": kit.make_pbr_material(
            "EmissiveVioletRune",
            (0.68, 0.28, 1.0),
            roughness=0.22,
            metallic=0.0,
            emission=(0.64, 0.24, 1.0),
            emission_strength=5.4,
        ),
        "EmissiveCrimsonFurnace": kit.make_pbr_material(
            "EmissiveCrimsonFurnace",
            (1.0, 0.14, 0.12),
            roughness=0.24,
            metallic=0.0,
            emission=(1.0, 0.12, 0.10),
            emission_strength=5.5,
        ),
    }


# =============================================================================
# BIOME 2: THE IRON NECROPOLIS
# =============================================================================

def build_necropolis_wall_armory_4x4() -> None:
    kit.clear_scene()
    mats = make_materials()
    parts: list[bpy.types.Object] = []

    # 1. Core wall backing & stepped plinths (8 parts)
    parts.append(kit.create_beveled_box("WallCore", (0.0, 0.06, 2.0), (4.0, 0.28, 4.0), mats["StoneDark"], bevel_width=0.02))
    parts.append(kit.create_beveled_box("PlinthLower", (0.0, 0.0, 0.20), (4.0, 0.50, 0.40), mats["StoneTrim"], bevel_width=0.025))
    parts.append(kit.create_beveled_box("PlinthUpper", (0.0, 0.0, 0.48), (4.0, 0.44, 0.16), mats["StoneTrim"], bevel_width=0.02))
    parts.append(kit.create_beveled_box("CorniceMain", (0.0, 0.0, 3.85), (4.0, 0.50, 0.30), mats["StoneTrim"], bevel_width=0.025))
    parts.append(kit.create_beveled_box("CorniceSub", (0.0, 0.0, 3.62), (4.0, 0.44, 0.16), mats["StoneTrim"], bevel_width=0.02))

    # 3 vertical armored stone pilasters (6 parts)
    for px in (-1.82, 0.0, 1.82):
        parts.append(kit.create_beveled_box(f"Pilaster_{px:.1f}", (px, 0.0, 2.05), (0.34, 0.48, 3.10), mats["StoneTrim"], bevel_width=0.02))
        parts.append(kit.create_beveled_box(f"PilasterPlate_{px:.1f}", (px, -0.22, 2.05), (0.22, 0.08, 2.85), mats["WroughtIron"], bevel_width=0.01))

    # 2. Twin Armory Alcoves (Left X=-0.92, Right X=+0.92)
    for side_idx, cx in enumerate((-0.92, 0.92)):
        # Stone arch frame &voussoirs (9 parts per side = 18)
        for v_i in range(9):
            ang = math.pi * (0.10 + 0.80 * (v_i / 8.0))
            vx = cx + math.cos(ang) * 0.62
            vz = 2.75 + math.sin(ang) * 0.52
            parts.append(
                kit.create_beveled_box(
                    f"ArchVoussoir_{side_idx}_{v_i}",
                    (vx, -0.14, vz),
                    (0.16, 0.24, 0.14),
                    mats["StoneTrim"],
                    bevel_width=0.012,
                    rotation=(0.0, ang - math.pi * 0.5, 0.0),
                )
            )

        # Portcullis vertical bars & horizontal cross-straps (9 parts per side = 18)
        for b_i in range(6):
            bx = cx - 0.50 + b_i * 0.20
            parts.append(kit.create_beveled_cylinder(f"PortBar_{side_idx}_{b_i}", (bx, -0.14, 1.95), 0.022, 2.15, mats["WroughtIron"], vertices=10))
            parts.append(
                kit.create_tapered_prism(
                    f"PortSpike_{side_idx}_{b_i}",
                    (bx, -0.14, 0.82),
                    0.032,
                    0.005,
                    0.16,
                    mats["WroughtIron"],
                    sides=6,
                )
            )
        for hz in (1.15, 1.95, 2.65):
            parts.append(kit.create_beveled_box(f"PortStrap_{side_idx}_{hz:.1f}", (cx, -0.16, hz), (1.18, 0.05, 0.07), mats["WroughtIron"], bevel_width=0.006))

        # Glowing cold-amber forge slits behind portcullis (3 parts per side = 6)
        for sz in (1.35, 1.95, 2.55):
            parts.append(kit.create_beveled_box(f"ForgeSlit_{side_idx}_{sz:.1f}", (cx, -0.08, sz), (0.86, 0.04, 0.10), mats["EmissiveAmberFlame"], bevel_width=0.004))

        # Crossed Halberds mounted in front of each alcove (12 parts per side = 24)
        for h_dir in (-1, 1):
            tilt = h_dir * 0.42
            parts.append(
                kit.create_beveled_cylinder(
                    f"HalberdShaft_{side_idx}_{h_dir}",
                    (cx, -0.22, 1.95),
                    0.024,
                    2.10,
                    mats["DarkTimber"],
                    vertices=10,
                    rotation=(0.0, tilt, 0.0),
                )
            )
            tip_x = cx + math.sin(tilt) * 0.88
            tip_z = 1.95 + math.cos(tilt) * 0.88
            parts.append(
                kit.create_beveled_box(
                    f"HalberdAxe_{side_idx}_{h_dir}",
                    (tip_x + h_dir * 0.10, -0.23, tip_z - 0.12),
                    (0.24, 0.025, 0.30),
                    mats["WroughtIron"],
                    bevel_width=0.005,
                    rotation=(0.0, tilt, 0.0),
                )
            )
            parts.append(
                kit.create_tapered_prism(
                    f"HalberdTip_{side_idx}_{h_dir}",
                    (tip_x, -0.23, tip_z + 0.12),
                    0.035,
                    0.004,
                    0.28,
                    mats["WroughtIron"],
                    sides=6,
                    rotation=(0.0, tilt, 0.0),
                )
            )

        # Central Riveted Tower Shield at the crossing (6 parts per side = 12)
        parts.append(kit.create_beveled_box(f"ShieldBody_{side_idx}", (cx, -0.25, 1.95), (0.56, 0.06, 0.78), mats["WroughtIron"], bevel_width=0.015))
        parts.append(kit.create_beveled_box(f"ShieldTrim_{side_idx}", (cx, -0.27, 1.95), (0.42, 0.04, 0.62), mats["TarnishedBrass"], bevel_width=0.01))
        parts.append(kit.create_beveled_cylinder(f"ShieldBoss_{side_idx}", (cx, -0.29, 1.95), 0.10, 0.06, mats["TarnishedBrass"], vertices=12, rotation=(math.pi * 0.5, 0.0, 0.0)))

    # 3. Rivet lines along the 3 armored pilasters & cornice band (48 rivets)
    for px in (-1.82, 0.0, 1.82):
        parts.extend(
            kit.spawn_rivet_line(
                f"PilasterRivets_{px:.1f}",
                Vector((px, -0.26, 0.85)),
                Vector((px, -0.26, 3.25)),
                16,
                0.018,
                mats["TarnishedBrass"],
                axis="Y",
            )
        )

    assert len(parts) >= 120, f"Expected 120+ parts in necropolis_wall_armory_4x4, got {len(parts)}"
    kit.finalize_and_export_glb(
        os.path.join(OUT_DIR, "necropolis_wall_armory_4x4.glb"),
        parts,
        base_rgb=(0.21, 0.21, 0.22),
        cavity_rgb=(0.08, 0.08, 0.10),
        edge_rgb=(0.38, 0.36, 0.33),
    )


def build_necropolis_iron_maiden_monolith() -> None:
    kit.clear_scene()
    mats = make_materials()
    parts: list[bpy.types.Object] = []

    # 1. Stepped octagonal war-plinth (6 parts)
    parts.append(kit.create_tapered_prism("PlinthStep1", (0.0, 0.0, 0.20), 1.22, 1.16, 0.40, mats["StoneDark"], sides=8))
    parts.append(kit.create_tapered_prism("PlinthStep2", (0.0, 0.0, 0.55), 1.08, 1.00, 0.32, mats["StoneTrim"], sides=8))
    parts.append(kit.create_tapered_prism("PlinthStep3", (0.0, 0.0, 0.82), 0.92, 0.86, 0.24, mats["WroughtIron"], sides=8))

    # 2. Towering Iron Maiden Sarcophagus Body & Crown (10 parts)
    parts.append(kit.create_tapered_prism("MaidenLowerTorso", (0.0, 0.0, 1.55), 0.64, 0.76, 1.25, mats["WroughtIron"], sides=8))
    parts.append(kit.create_tapered_prism("MaidenUpperTorso", (0.0, 0.0, 2.55), 0.76, 0.58, 0.90, mats["WroughtIron"], sides=8))
    parts.append(kit.create_tapered_prism("MaidenHelm", (0.0, 0.0, 3.25), 0.50, 0.32, 0.55, mats["WroughtIron"], sides=8))
    parts.append(kit.create_tapered_prism("MaidenSpire", (0.0, 0.0, 3.65), 0.22, 0.03, 0.35, mats["TarnishedBrass"], sides=8))

    # Glowing amber eye/visor slits on 4 cardinal faces (8 parts)
    for i in range(4):
        ang = i * (math.pi * 0.5)
        ex = math.cos(ang) * 0.44
        ey = math.sin(ang) * 0.44
        parts.append(
            kit.create_beveled_box(
                f"VisorGlow_{i}",
                (ex, ey, 3.22),
                (0.26, 0.08, 0.09),
                mats["EmissiveAmberFlame"],
                bevel_width=0.005,
                rotation=(0.0, 0.0, ang + math.pi * 0.5),
            )
        )
        parts.append(
            kit.create_beveled_box(
                f"ChestSlitGlow_{i}",
                (math.cos(ang) * 0.66, math.sin(ang) * 0.66, 2.15),
                (0.18, 0.08, 0.85),
                mats["EmissiveAmberFlame"],
                bevel_width=0.006,
                rotation=(0.0, 0.0, ang + math.pi * 0.5),
            )
        )

    # 3. 4 Spiked Greatswords & 4 Forge-Brazier Basins at the corners (48 parts)
    for i in range(4):
        ang = i * (math.pi * 0.5) + math.pi * 0.25
        sx = math.cos(ang) * 0.84
        sy = math.sin(ang) * 0.84
        # Greatsword blade, fuller, crossguard, grip, pommel (6 parts each = 24)
        parts.append(kit.create_beveled_box(f"SwordBlade_{i}", (sx, sy, 1.95), (0.16, 0.04, 1.85), mats["WroughtIron"], bevel_width=0.006, rotation=(0.0, 0.0, ang)))
        parts.append(kit.create_tapered_prism(f"SwordTip_{i}", (sx, sy, 2.98), 0.08, 0.005, 0.26, mats["WroughtIron"], sides=4, rotation=(0.0, 0.0, ang)))
        parts.append(kit.create_beveled_box(f"SwordGuard_{i}", (sx, sy, 2.72), (0.58, 0.08, 0.08), mats["TarnishedBrass"], bevel_width=0.01, rotation=(0.0, 0.0, ang)))
        parts.append(kit.create_beveled_cylinder(f"SwordGrip_{i}", (sx, sy, 3.02), 0.04, 0.48, mats["DarkTimber"], vertices=10))
        parts.append(kit.create_beveled_cylinder(f"SwordPommel_{i}", (sx, sy, 3.30), 0.08, 0.10, mats["TarnishedBrass"], vertices=12))
        parts.append(kit.create_beveled_box(f"SwordBracket_{i}", (sx * 0.82, sy * 0.82, 1.65), (0.28, 0.28, 0.14), mats["WroughtIron"], bevel_width=0.01))

        # Cardinal Forge-Brazier Basins (6 parts each = 24)
        c_ang = i * (math.pi * 0.5)
        bx = math.cos(c_ang) * 0.96
        by = math.sin(c_ang) * 0.96
        parts.append(kit.create_tapered_prism(f"BrazierPed_{i}", (bx, by, 0.65), 0.22, 0.16, 0.55, mats["StoneTrim"], sides=8))
        parts.append(kit.create_tapered_prism(f"BrazierBowl_{i}", (bx, by, 1.02), 0.16, 0.30, 0.24, mats["WroughtIron"], sides=10))
        parts.append(kit.create_tapered_prism(f"BrazierEmbers_{i}", (bx, by, 1.15), 0.24, 0.08, 0.18, mats["EmissiveAmberFlame"], sides=8))
        for sp_k in range(3):
            sp_a = c_ang + (sp_k - 1) * 0.45
            parts.append(
                kit.create_tapered_prism(
                    f"BrazierHorn_{i}_{sp_k}",
                    (bx + math.cos(sp_a) * 0.26, by + math.sin(sp_a) * 0.26, 1.18),
                    0.03,
                    0.004,
                    0.18,
                    mats["WroughtIron"],
                    sides=6,
                )
            )

    # 4. Heavy 3D Chain Links wrapping the sarcophagus (4 diagonal chains x 14 links = 56 parts)
    for i in range(4):
        ang1 = i * (math.pi * 0.5)
        ang2 = (i + 1) * (math.pi * 0.5)
        p_start = Vector((math.cos(ang1) * 0.78, math.sin(ang1) * 0.78, 1.25))
        p_end = Vector((math.cos(ang2) * 0.72, math.sin(ang2) * 0.72, 2.75))
        parts.extend(kit.spawn_chain_links(f"MaidenChain_{i}", p_start, p_end, 14, mats["WroughtIron"], link_radius=0.055, wire_radius=0.015))

    # 5. Horizontal spiked iron bands & rivets around the sarcophagus (24 parts)
    for z_band in (1.20, 1.85, 2.50):
        parts.append(kit.create_tapered_prism(f"IronBand_{z_band:.2f}", (0.0, 0.0, z_band), 0.78, 0.78, 0.10, mats["TarnishedBrass"], sides=8))
        for s_i in range(7):
            s_ang = s_i * (2.0 * math.pi / 7.0)
            parts.append(
                kit.create_tapered_prism(
                    f"BandSpike_{z_band:.2f}_{s_i}",
                    (math.cos(s_ang) * 0.84, math.sin(s_ang) * 0.84, z_band),
                    0.035,
                    0.004,
                    0.18,
                    mats["WroughtIron"],
                    sides=6,
                    rotation=(math.pi * 0.5, 0.0, s_ang + math.pi * 0.5),
                )
            )

    assert len(parts) >= 140, f"Expected 140+ parts in necropolis_iron_maiden_monolith, got {len(parts)}"
    kit.finalize_and_export_glb(
        os.path.join(OUT_DIR, "necropolis_iron_maiden_monolith.glb"),
        parts,
        base_rgb=(0.20, 0.20, 0.22),
        cavity_rgb=(0.07, 0.07, 0.09),
        edge_rgb=(0.38, 0.35, 0.32),
    )


def build_necropolis_hanging_war_brazier() -> None:
    kit.clear_scene()
    mats = make_materials()
    parts: list[bpy.types.Object] = []

    # Ceiling anchor rose at Z=0.0, hanging down to Z=-1.75m
    parts.append(kit.create_tapered_prism("CeilingMount", (0.0, 0.0, -0.06), 0.24, 0.16, 0.12, mats["WroughtIron"], sides=8))
    parts.append(kit.create_beveled_cylinder("CenterChainRod", (0.0, 0.0, -0.65), 0.035, 1.15, mats["WroughtIron"], vertices=10))

    # War-cage outer & inner rings (6 parts)
    parts.append(kit.create_torus_ring("OuterWarRing", (0.0, 0.0, -1.20), 0.78, 0.055, mats["WroughtIron"], major_seg=24, minor_seg=10))
    parts.append(kit.create_torus_ring("BrassTrimRing", (0.0, 0.0, -1.14), 0.78, 0.028, mats["TarnishedBrass"], major_seg=24, minor_seg=8))
    parts.append(kit.create_torus_ring("InnerCoalBasket", (0.0, 0.0, -1.32), 0.46, 0.045, mats["WroughtIron"], major_seg=20, minor_seg=10))
    parts.append(kit.create_tapered_prism("CoalBedPan", (0.0, 0.0, -1.38), 0.44, 0.26, 0.18, mats["WroughtIron"], sides=10))
    parts.append(kit.create_tapered_prism("EmberCore", (0.0, 0.0, -1.22), 0.38, 0.14, 0.28, mats["EmissiveAmberFlame"], sides=10))
    parts.append(kit.create_tapered_prism("BottomFinialSpike", (0.0, 0.0, -1.62), 0.12, 0.01, 0.32, mats["TarnishedBrass"], sides=8, rotation=(math.pi, 0.0, 0.0)))

    # 4 radial suspension chains (4 x 12 = 48 parts)
    for i in range(4):
        ang = i * (math.pi * 0.5)
        p0 = Vector((math.cos(ang) * 0.12, math.sin(ang) * 0.12, -0.10))
        p1 = Vector((math.cos(ang) * 0.74, math.sin(ang) * 0.74, -1.16))
        parts.extend(kit.spawn_chain_links(f"SuspChain_{i}", p0, p1, 12, mats["WroughtIron"], link_radius=0.042, wire_radius=0.012))

    # 12 perimeter war-spikes + 12 glowing ember brazier pods + 12 radial spokes (36 parts)
    for i in range(12):
        ang = i * (2.0 * math.pi / 12.0)
        rx = math.cos(ang) * 0.80
        ry = math.sin(ang) * 0.80
        parts.append(kit.create_tapered_prism(f"CageSpikeDown_{i}", (rx, ry, -1.36), 0.04, 0.005, 0.24, mats["WroughtIron"], sides=6, rotation=(math.pi, 0.0, 0.0)))
        parts.append(kit.create_tapered_prism(f"CageFlameTip_{i}", (rx, ry, -1.04), 0.045, 0.01, 0.18, mats["EmissiveAmberFlame"], sides=6))
        parts.append(
            kit.create_beveled_box(
                f"RadialSpoke_{i}",
                (math.cos(ang) * 0.42, math.sin(ang) * 0.42, -1.24),
                (0.68, 0.035, 0.045),
                mats["WroughtIron"],
                bevel_width=0.005,
                rotation=(0.0, 0.0, ang),
            )
        )

    assert len(parts) >= 90, f"Expected 90+ parts in necropolis_hanging_war_brazier, got {len(parts)}"
    kit.finalize_and_export_glb(
        os.path.join(OUT_DIR, "necropolis_hanging_war_brazier.glb"),
        parts,
        base_rgb=(0.20, 0.20, 0.22),
        cavity_rgb=(0.08, 0.08, 0.10),
        edge_rgb=(0.38, 0.36, 0.32),
    )


# =============================================================================
# BIOME 3: THE ASTRAL RELIQUARY
# =============================================================================

def build_reliquary_wall_grimoire_4x4() -> None:
    kit.clear_scene()
    mats = make_materials()
    parts: list[bpy.types.Object] = []

    # 1. Core wall & stepped library framing (10 parts)
    parts.append(kit.create_beveled_box("WallCore", (0.0, 0.06, 2.0), (4.0, 0.28, 4.0), mats["StoneDark"], bevel_width=0.02))
    parts.append(kit.create_beveled_box("PlinthLower", (0.0, 0.0, 0.20), (4.0, 0.50, 0.40), mats["StoneTrim"], bevel_width=0.025))
    parts.append(kit.create_beveled_box("CorniceUpper", (0.0, 0.0, 3.85), (4.0, 0.50, 0.30), mats["StoneTrim"], bevel_width=0.025))
    for px in (-1.85, -0.62, 0.62, 1.85):
        parts.append(kit.create_beveled_box(f"LibPilaster_{px:.2f}", (px, 0.0, 2.02), (0.26, 0.46, 3.25), mats["StoneTrim"], bevel_width=0.018))
        parts.append(kit.create_beveled_box(f"BrassInlay_{px:.2f}", (px, -0.22, 2.02), (0.08, 0.05, 2.95), mats["TarnishedBrass"], bevel_width=0.006))

    # 2. 3 horizontal library shelves across Left & Right alcoves (12 parts)
    for cx in (-1.24, 1.24):
        for sz in (0.95, 1.75, 2.55, 3.25):
            parts.append(kit.create_beveled_box(f"Shelf_{cx:.2f}_{sz:.2f}", (cx, -0.10, sz), (1.02, 0.32, 0.08), mats["DarkTimber"], bevel_width=0.01))
            parts.append(kit.create_beveled_box(f"ShelfBrass_{cx:.2f}_{sz:.2f}", (cx, -0.25, sz), (1.02, 0.04, 0.04), mats["TarnishedBrass"], bevel_width=0.004))

    # 3. 36 Chained Occult Tomes & Grimoires on the shelves (36 * 2 = 72 parts)
    tome_idx = 0
    for cx in (-1.24, 1.24):
        for s_idx, sz in enumerate((1.16, 1.96, 2.76)):
            for b_i in range(6):
                bx = cx - 0.38 + b_i * 0.15
                h_var = 0.28 + ((b_i + s_idx) % 3) * 0.04
                tilt = ((b_i % 3) - 1) * 0.06
                parts.append(
                    kit.create_beveled_box(
                        f"TomeCover_{tome_idx}",
                        (bx, -0.14, sz),
                        (0.11, 0.24, h_var),
                        mats["DarkTimber"] if (tome_idx % 2 == 0) else mats["WroughtIron"],
                        bevel_width=0.006,
                        rotation=(0.0, tilt, 0.0),
                    )
                )
                parts.append(
                    kit.create_beveled_box(
                        f"TomePages_{tome_idx}",
                        (bx, -0.16, sz),
                        (0.08, 0.22, h_var - 0.03),
                        mats["Bone"],
                        bevel_width=0.004,
                        rotation=(0.0, tilt, 0.0),
                    )
                )
                tome_idx += 1

    # 4. Central Astral Astrolabe Relief & Glowing Violet Rune Inlays (38 parts)
    parts.append(kit.create_torus_ring("CenterAstrolabeOuter", (0.0, -0.20, 2.10), 0.48, 0.035, mats["TarnishedBrass"], major_seg=24, minor_seg=10, rotation=(math.pi * 0.5, 0.0, 0.0)))
    parts.append(kit.create_torus_ring("CenterAstrolabeInner", (0.0, -0.22, 2.10), 0.30, 0.025, mats["TarnishedBrass"], major_seg=20, minor_seg=8, rotation=(math.pi * 0.5, 0.0, 0.0)))
    parts.append(kit.create_tapered_prism("CenterVioletCrystal", (0.0, -0.24, 2.10), 0.12, 0.02, 0.32, mats["EmissiveVioletRune"], sides=6))

    for r_i in range(12):
        ang = r_i * (2.0 * math.pi / 12.0)
        rx = math.cos(ang) * 0.39
        rz = 2.10 + math.sin(ang) * 0.39
        parts.append(
            kit.create_beveled_box(
                f"AstroSpoke_{r_i}",
                (rx, -0.21, rz),
                (0.22, 0.03, 0.03),
                mats["TarnishedBrass"],
                bevel_width=0.004,
                rotation=(0.0, ang, 0.0),
            )
        )
        parts.append(
            kit.create_beveled_box(
                f"RuneInlay_{r_i}",
                (math.cos(ang) * 0.52, -0.18, 2.10 + math.sin(ang) * 0.52),
                (0.08, 0.04, 0.04),
                mats["EmissiveVioletRune"],
                bevel_width=0.004,
                rotation=(0.0, ang, 0.0),
            )
        )

    # Lower central scroll niches (12 parts)
    for sc_i in range(12):
        sx = -0.42 + (sc_i % 6) * 0.168
        sz = 1.05 + (sc_i // 6) * 0.22
        parts.append(
            kit.create_beveled_cylinder(
                f"ScrollRoll_{sc_i}",
                (sx, -0.16, sz),
                0.042,
                0.24,
                mats["Bone"],
                vertices=10,
                rotation=(math.pi * 0.5, 0.0, 0.0),
            )
        )

    assert len(parts) >= 130, f"Expected 130+ parts in reliquary_wall_grimoire_4x4, got {len(parts)}"
    kit.finalize_and_export_glb(
        os.path.join(OUT_DIR, "reliquary_wall_grimoire_4x4.glb"),
        parts,
        base_rgb=(0.21, 0.19, 0.23),
        cavity_rgb=(0.08, 0.07, 0.11),
        edge_rgb=(0.39, 0.35, 0.42),
    )


def build_reliquary_astral_orrery_monolith() -> None:
    kit.clear_scene()
    mats = make_materials()
    parts: list[bpy.types.Object] = []

    # 1. Stepped Obsidian & Brass Plinth (8 parts)
    parts.append(kit.create_tapered_prism("OrreryBase1", (0.0, 0.0, 0.22), 1.30, 1.22, 0.44, mats["StoneDark"], sides=8))
    parts.append(kit.create_tapered_prism("OrreryBase2", (0.0, 0.0, 0.62), 1.12, 1.02, 0.38, mats["StoneTrim"], sides=8))
    parts.append(kit.create_tapered_prism("OrreryBrassCrown", (0.0, 0.0, 0.90), 0.96, 0.88, 0.18, mats["TarnishedBrass"], sides=8))
    parts.append(kit.create_tapered_prism("OrreryPedestalCol", (0.0, 0.0, 1.45), 0.52, 0.42, 0.95, mats["StoneDark"], sides=8))

    # 8 Arcane Violet Rune Inlays around the pedestal column (16 parts)
    for i in range(8):
        ang = i * (2.0 * math.pi / 8.0)
        rx = math.cos(ang) * 0.48
        ry = math.sin(ang) * 0.48
        parts.append(
            kit.create_beveled_box(
                f"PedestalRune_{i}",
                (rx, ry, 1.45),
                (0.10, 0.05, 0.72),
                mats["EmissiveVioletRune"],
                bevel_width=0.005,
                rotation=(0.0, 0.0, ang + math.pi * 0.5),
            )
        )
        parts.append(
            kit.create_tapered_prism(
                f"PlinthObelisk_{i}",
                (math.cos(ang) * 1.05, math.sin(ang) * 1.05, 1.15),
                0.10,
                0.02,
                0.55,
                mats["TarnishedBrass"],
                sides=6,
            )
        )

    # 2. Multi-Ringed Brass Celestial Astrolabe centered at Z = 2.65m (10 rings)
    center_z = 2.65
    ring_specs = [
        (1.08, 0.045, (0.35, 0.15, 0.0)),
        (0.96, 0.038, (-0.42, 0.55, 0.25)),
        (0.84, 0.034, (0.78, -0.35, 0.50)),
        (0.72, 0.030, (-0.65, -0.45, 0.85)),
        (0.58, 0.026, (math.pi * 0.5, 0.25, 0.0)),
        (0.44, 0.022, (0.15, math.pi * 0.5, 0.40)),
    ]
    for idx, (r_maj, r_min, rot) in enumerate(ring_specs):
        parts.append(kit.create_torus_ring(f"OrreryRing_{idx}", (0.0, 0.0, center_z), r_maj, r_min, mats["TarnishedBrass"], major_seg=28, minor_seg=10, rotation=rot))

    # Central Crystalline Soul-Pillar & Twin Cones (6 parts)
    parts.append(kit.create_tapered_prism("SoulCrystalUpper", (0.0, 0.0, center_z + 0.22), 0.22, 0.01, 0.44, mats["EmissiveVioletRune"], sides=6))
    parts.append(kit.create_tapered_prism("SoulCrystalLower", (0.0, 0.0, center_z - 0.22), 0.22, 0.01, 0.44, mats["EmissiveVioletRune"], sides=6, rotation=(math.pi, 0.0, 0.0)))
    parts.append(kit.create_tapered_prism("TopApexSpire", (0.0, 0.0, 3.78), 0.14, 0.01, 0.28, mats["TarnishedBrass"], sides=8))

    # 4 Curved Cradle Buttresses supporting the Orrery + 4x12 chains (52 parts)
    for i in range(4):
        ang = i * (math.pi * 0.5)
        bx = math.cos(ang) * 0.88
        by = math.sin(ang) * 0.88
        parts.append(kit.create_beveled_box(f"CradlePillar_{i}", (bx, by, 1.95), (0.16, 0.16, 1.85), mats["WroughtIron"], bevel_width=0.012, rotation=(0.0, 0.0, ang)))
        p0 = Vector((bx, by, 1.10))
        p1 = Vector((math.cos(ang + 0.5) * 0.48, math.sin(ang + 0.5) * 0.48, 2.05))
        parts.extend(kit.spawn_chain_links(f"OrreryChain_{i}", p0, p1, 12, mats["TarnishedBrass"], link_radius=0.042, wire_radius=0.012))

    # 40 Degree Tick Marks & Planetary Spheres around the outer rings (80 parts)
    for i in range(40):
        ang = i * (2.0 * math.pi / 40.0)
        tx = math.cos(ang) * 1.12
        ty = math.sin(ang) * 1.12
        parts.append(
            kit.create_beveled_box(
                f"AstroTick_{i}",
                (tx, ty, center_z),
                (0.08, 0.025, 0.025),
                mats["TarnishedBrass"],
                bevel_width=0.003,
                rotation=(0.0, 0.0, ang),
            )
        )
        if i % 2 == 0:
            orb_r = 0.65 + (i % 4) * 0.12
            oz = center_z + math.sin(ang * 2.0) * 0.35
            parts.append(
                kit.create_tapered_prism(
                    f"PlanetShard_{i}",
                    (math.cos(ang) * orb_r, math.sin(ang) * orb_r, oz),
                    0.065,
                    0.01,
                    0.15,
                    mats["EmissiveVioletRune"] if (i % 4 == 0) else mats["TarnishedBrass"],
                    sides=6,
                )
            )
            parts.append(
                kit.create_beveled_cylinder(
                    f"PlanetArm_{i}",
                    (math.cos(ang) * (orb_r * 0.5), math.sin(ang) * (orb_r * 0.5), oz),
                    0.014,
                    orb_r,
                    mats["TarnishedBrass"],
                    vertices=8,
                    rotation=(0.0, math.pi * 0.5, ang),
                )
            )

    assert len(parts) >= 150, f"Expected 150+ parts in reliquary_astral_orrery_monolith, got {len(parts)}"
    kit.finalize_and_export_glb(
        os.path.join(OUT_DIR, "reliquary_astral_orrery_monolith.glb"),
        parts,
        base_rgb=(0.22, 0.19, 0.25),
        cavity_rgb=(0.08, 0.06, 0.11),
        edge_rgb=(0.42, 0.38, 0.46),
    )


def build_reliquary_chandelier_astrolabe() -> None:
    kit.clear_scene()
    mats = make_materials()
    parts: list[bpy.types.Object] = []

    # Ceiling mount & central brass spindle
    parts.append(kit.create_tapered_prism("CeilingRose", (0.0, 0.0, -0.06), 0.24, 0.15, 0.12, mats["TarnishedBrass"], sides=8))
    parts.append(kit.create_beveled_cylinder("AstrolabeSpindle", (0.0, 0.0, -0.82), 0.032, 1.50, mats["TarnishedBrass"], vertices=10))

    # Concentric Brass Rings (5 parts)
    parts.append(kit.create_torus_ring("ChandelierOuterRing", (0.0, 0.0, -1.18), 0.88, 0.042, mats["TarnishedBrass"], major_seg=28, minor_seg=10))
    parts.append(kit.create_torus_ring("ChandelierMidRing", (0.0, 0.0, -1.02), 0.58, 0.032, mats["TarnishedBrass"], major_seg=24, minor_seg=10))
    parts.append(kit.create_torus_ring("ChandelierDiagRing1", (0.0, 0.0, -1.18), 0.62, 0.026, mats["TarnishedBrass"], major_seg=24, minor_seg=8, rotation=(0.55, 0.0, 0.0)))
    parts.append(kit.create_torus_ring("ChandelierDiagRing2", (0.0, 0.0, -1.18), 0.62, 0.026, mats["TarnishedBrass"], major_seg=24, minor_seg=8, rotation=(0.0, 0.55, 0.0)))
    parts.append(kit.create_tapered_prism("CenterVioletPendulum", (0.0, 0.0, -1.58), 0.16, 0.01, 0.38, mats["EmissiveVioletRune"], sides=6, rotation=(math.pi, 0.0, 0.0)))

    # 4 suspension chains (4 x 12 = 48 parts)
    for i in range(4):
        ang = i * (math.pi * 0.5)
        p0 = Vector((math.cos(ang) * 0.12, math.sin(ang) * 0.12, -0.10))
        p1 = Vector((math.cos(ang) * 0.84, math.sin(ang) * 0.84, -1.15))
        parts.extend(kit.spawn_chain_links(f"AstroSuspChain_{i}", p0, p1, 12, mats["TarnishedBrass"], link_radius=0.042, wire_radius=0.012))

    # 14 Floating Violet Crystal Prisms + Brass Holders + Radial Spokes (42 parts)
    for i in range(14):
        ang = i * (2.0 * math.pi / 14.0)
        rx = math.cos(ang) * 0.88
        ry = math.sin(ang) * 0.88
        parts.append(kit.create_tapered_prism(f"PrismUpper_{i}", (rx, ry, -1.02), 0.055, 0.008, 0.22, mats["EmissiveVioletRune"], sides=6))
        parts.append(kit.create_tapered_prism(f"PrismLower_{i}", (rx, ry, -1.34), 0.055, 0.008, 0.22, mats["EmissiveVioletRune"], sides=6, rotation=(math.pi, 0.0, 0.0)))
        parts.append(
            kit.create_beveled_box(
                f"BrassSpoke_{i}",
                (math.cos(ang) * 0.44, math.sin(ang) * 0.44, -1.18),
                (0.84, 0.028, 0.032),
                mats["TarnishedBrass"],
                bevel_width=0.004,
                rotation=(0.0, 0.0, ang),
            )
        )

    assert len(parts) >= 95, f"Expected 95+ parts in reliquary_chandelier_astrolabe, got {len(parts)}"
    kit.finalize_and_export_glb(
        os.path.join(OUT_DIR, "reliquary_chandelier_astrolabe.glb"),
        parts,
        base_rgb=(0.22, 0.19, 0.25),
        cavity_rgb=(0.08, 0.06, 0.11),
        edge_rgb=(0.42, 0.38, 0.46),
    )


# =============================================================================
# BIOME 4: THE BLOOD-FORGED ABATTOIR
# =============================================================================

def build_abattoir_wall_furnace_4x4() -> None:
    kit.clear_scene()
    mats = make_materials()
    parts: list[bpy.types.Object] = []

    # 1. Brutalist Iron-Ribbed Stone Wall & Plinths (12 parts)
    parts.append(kit.create_beveled_box("WallCore", (0.0, 0.08, 2.0), (4.0, 0.28, 4.0), mats["StoneDark"], bevel_width=0.02))
    parts.append(kit.create_beveled_box("PlinthIron", (0.0, 0.0, 0.22), (4.0, 0.50, 0.44), mats["WroughtIron"], bevel_width=0.02))
    parts.append(kit.create_beveled_box("CorniceIron", (0.0, 0.0, 3.84), (4.0, 0.50, 0.32), mats["WroughtIron"], bevel_width=0.02))
    for rx in (-1.84, -0.92, 0.0, 0.92, 1.84):
        parts.append(kit.create_beveled_box(f"IronRib_{rx:.2f}", (rx, -0.02, 2.02), (0.22, 0.48, 3.25), mats["WroughtIron"], bevel_width=0.015))

    # 2. Recessed Furnace Grates & Searing Crimson Glow (28 parts)
    for fx in (-1.38, -0.46, 0.46, 1.38):
        parts.append(kit.create_beveled_box(f"FurnaceGlow_{fx:.2f}", (fx, -0.06, 1.45), (0.66, 0.06, 1.55), mats["EmissiveCrimsonFurnace"], bevel_width=0.008))
        for b_i in range(4):
            bx = fx - 0.24 + b_i * 0.16
            parts.append(kit.create_beveled_cylinder(f"GrateBar_{fx:.2f}_{b_i}", (bx, -0.18, 1.45), 0.024, 1.62, mats["WroughtIron"], vertices=10))
        for gz in (0.95, 1.45, 1.95):
            parts.append(kit.create_beveled_box(f"GrateCross_{fx:.2f}_{gz:.2f}", (fx, -0.20, gz), (0.72, 0.04, 0.06), mats["WroughtIron"], bevel_width=0.005))

    # 3. Skull-Crusher Cogwheels / Gears in the Upper Frieze (4 gears x 10 parts = 40 parts)
    for g_idx, gx in enumerate((-1.38, -0.46, 0.46, 1.38)):
        parts.append(kit.create_torus_ring(f"GearRim_{g_idx}", (gx, -0.20, 2.95), 0.32, 0.045, mats["WroughtIron"], major_seg=20, minor_seg=8, rotation=(math.pi * 0.5, 0.0, 0.0)))
        parts.append(kit.create_beveled_cylinder(f"GearHub_{g_idx}", (gx, -0.22, 2.95), 0.11, 0.10, mats["TarnishedBrass"], vertices=12, rotation=(math.pi * 0.5, 0.0, 0.0)))
        for t_i in range(8):
            ang = t_i * (2.0 * math.pi / 8.0)
            tx = gx + math.cos(ang) * 0.35
            tz = 2.95 + math.sin(ang) * 0.35
            parts.append(
                kit.create_beveled_box(
                    f"GearTooth_{g_idx}_{t_i}",
                    (tx, -0.20, tz),
                    (0.08, 0.06, 0.08),
                    mats["WroughtIron"],
                    bevel_width=0.005,
                    rotation=(0.0, ang, 0.0),
                )
            )

    # 4. Hanging Meat-Hook Chains across the bays (4 chains x 14 = 56 parts)
    for c_idx, cx in enumerate((-1.38, -0.46, 0.46, 1.38)):
        p0 = Vector((cx, -0.24, 2.85))
        p1 = Vector((cx, -0.24, 1.25))
        parts.extend(kit.spawn_chain_links(f"HookChain_{c_idx}", p0, p1, 12, mats["WroughtIron"], link_radius=0.042, wire_radius=0.012))
        parts.append(kit.create_tapered_prism(f"MeatHookShank_{c_idx}", (cx, -0.26, 1.12), 0.032, 0.015, 0.22, mats["WroughtIron"], sides=6, rotation=(math.pi, 0.0, 0.0)))
        parts.append(kit.create_tapered_prism(f"MeatHookPoint_{c_idx}", (cx, -0.34, 1.08), 0.025, 0.004, 0.18, mats["TarnishedBrass"], sides=6, rotation=(-0.55, 0.0, 0.0)))

    assert len(parts) >= 125, f"Expected 125+ parts in abattoir_wall_furnace_4x4, got {len(parts)}"
    kit.finalize_and_export_glb(
        os.path.join(OUT_DIR, "abattoir_wall_furnace_4x4.glb"),
        parts,
        base_rgb=(0.20, 0.17, 0.17),
        cavity_rgb=(0.08, 0.05, 0.05),
        edge_rgb=(0.38, 0.30, 0.28),
    )


def build_abattoir_blood_press_monolith() -> None:
    kit.clear_scene()
    mats = make_materials()
    parts: list[bpy.types.Object] = []

    # 1. Heavy Cast-Iron & Stone Blood-Trough Base (8 parts)
    parts.append(kit.create_tapered_prism("PressBase1", (0.0, 0.0, 0.22), 1.25, 1.18, 0.44, mats["StoneDark"], sides=8))
    parts.append(kit.create_tapered_prism("PressBase2", (0.0, 0.0, 0.58), 1.10, 1.02, 0.32, mats["WroughtIron"], sides=8))
    parts.append(kit.create_tapered_prism("PressPlaten", (0.0, 0.0, 2.15), 0.86, 0.86, 0.24, mats["WroughtIron"], sides=8))
    parts.append(kit.create_tapered_prism("PressTopCrown", (0.0, 0.0, 3.35), 0.92, 0.82, 0.28, mats["WroughtIron"], sides=8))

    # 2. Giant Central Screw-Spindle with Helical Thread Rings & Top Turn-Wheel (26 parts)
    parts.append(kit.create_beveled_cylinder("CenterSpindle", (0.0, 0.0, 2.10), 0.18, 2.75, mats["WroughtIron"], vertices=14))
    for t_i in range(16):
        tz = 0.95 + t_i * 0.14
        parts.append(kit.create_torus_ring(f"SpindleThread_{t_i}", (0.0, 0.0, tz), 0.21, 0.032, mats["TarnishedBrass"], major_seg=18, minor_seg=8))
    parts.append(kit.create_torus_ring("TopTurnWheel", (0.0, 0.0, 3.62), 0.72, 0.048, mats["WroughtIron"], major_seg=24, minor_seg=10))
    for w_i in range(8):
        ang = w_i * (2.0 * math.pi / 8.0)
        parts.append(
            kit.create_beveled_box(
                f"WheelSpoke_{w_i}",
                (math.cos(ang) * 0.36, math.sin(ang) * 0.36, 3.62),
                (0.70, 0.045, 0.045),
                mats["TarnishedBrass"],
                bevel_width=0.005,
                rotation=(0.0, 0.0, ang),
            )
        )

    # 3. 4 Crimson Glass Collection Vats + Iron Pillars + Gargoyle Spouts (4 x 12 = 48 parts)
    for i in range(4):
        ang = i * (math.pi * 0.5)
        vx = math.cos(ang) * 0.68
        vy = math.sin(ang) * 0.68
        parts.append(kit.create_beveled_cylinder(f"CrimsonVat_{i}", (vx, vy, 1.38), 0.22, 1.15, mats["EmissiveCrimsonFurnace"], vertices=14))
        parts.append(kit.create_torus_ring(f"VatCapLower_{i}", (vx, vy, 0.82), 0.24, 0.035, mats["TarnishedBrass"], major_seg=18, minor_seg=8))
        parts.append(kit.create_torus_ring(f"VatCapUpper_{i}", (vx, vy, 1.94), 0.24, 0.035, mats["TarnishedBrass"], major_seg=18, minor_seg=8))
        for bar_k in range(4):
            b_ang = ang + bar_k * (math.pi * 0.5)
            parts.append(
                kit.create_beveled_cylinder(
                    f"VatCageBar_{i}_{bar_k}",
                    (vx + math.cos(b_ang) * 0.23, vy + math.sin(b_ang) * 0.23, 1.38),
                    0.018,
                    1.18,
                    mats["WroughtIron"],
                    vertices=8,
                )
            )

        # Corner guide column & spout
        c_ang = ang + math.pi * 0.25
        cx = math.cos(c_ang) * 0.84
        cy = math.sin(c_ang) * 0.84
        parts.append(kit.create_beveled_box(f"GuidePillar_{i}", (cx, cy, 2.05), (0.18, 0.18, 2.65), mats["WroughtIron"], bevel_width=0.012, rotation=(0.0, 0.0, c_ang)))
        parts.append(kit.create_beveled_box(f"SpoutTrough_{i}", (math.cos(ang) * 1.02, math.sin(ang) * 1.02, 0.72), (0.36, 0.22, 0.16), mats["StoneTrim"], bevel_width=0.01, rotation=(0.0, 0.0, ang)))
        parts.append(kit.create_beveled_box(f"SpoutBlood_{i}", (math.cos(ang) * 1.05, math.sin(ang) * 1.05, 0.78), (0.28, 0.12, 0.08), mats["EmissiveCrimsonFurnace"], bevel_width=0.005, rotation=(0.0, 0.0, ang)))

    # 4. 4 Heavy Tension Chains & Platen Crushing Spikes (4 x 14 + 12 = 68 parts)
    for i in range(4):
        ang = i * (math.pi * 0.5) + math.pi * 0.25
        p0 = Vector((math.cos(ang) * 0.82, math.sin(ang) * 0.82, 3.25))
        p1 = Vector((math.cos(ang) * 0.52, math.sin(ang) * 0.52, 2.22))
        parts.extend(kit.spawn_chain_links(f"PressChain_{i}", p0, p1, 14, mats["WroughtIron"], link_radius=0.048, wire_radius=0.014))

    for s_i in range(20):
        s_ang = s_i * (2.0 * math.pi / 20.0)
        parts.append(
            kit.create_tapered_prism(
                f"PlatenCrushSpike_{s_i}",
                (math.cos(s_ang) * 0.62, math.sin(s_ang) * 0.62, 1.94),
                0.045,
                0.005,
                0.24,
                mats["WroughtIron"],
                sides=6,
                rotation=(math.pi, 0.0, 0.0),
            )
        )

    assert len(parts) >= 145, f"Expected 145+ parts in abattoir_blood_press_monolith, got {len(parts)}"
    kit.finalize_and_export_glb(
        os.path.join(OUT_DIR, "abattoir_blood_press_monolith.glb"),
        parts,
        base_rgb=(0.20, 0.16, 0.16),
        cavity_rgb=(0.08, 0.05, 0.05),
        edge_rgb=(0.38, 0.29, 0.27),
    )


def build_abattoir_hanging_hook_rack() -> None:
    kit.clear_scene()
    mats = make_materials()
    parts: list[bpy.types.Object] = []

    # Ceiling mount & central butcher spindle
    parts.append(kit.create_tapered_prism("HookCeilingMount", (0.0, 0.0, -0.06), 0.24, 0.16, 0.12, mats["WroughtIron"], sides=8))
    parts.append(kit.create_beveled_cylinder("ButcherSpindle", (0.0, 0.0, -0.72), 0.038, 1.25, mats["WroughtIron"], vertices=10))

    # Circular Butcher's Wheel & Central Crimson Ember Cage (6 parts)
    parts.append(kit.create_torus_ring("ButcherWheelOuter", (0.0, 0.0, -1.18), 0.80, 0.050, mats["WroughtIron"], major_seg=24, minor_seg=10))
    parts.append(kit.create_torus_ring("ButcherWheelInner", (0.0, 0.0, -1.18), 0.42, 0.035, mats["TarnishedBrass"], major_seg=20, minor_seg=8))
    parts.append(kit.create_tapered_prism("CenterCrimsonEmber", (0.0, 0.0, -1.24), 0.28, 0.12, 0.34, mats["EmissiveCrimsonFurnace"], sides=8))
    parts.append(kit.create_tapered_prism("BottomBloodSpike", (0.0, 0.0, -1.58), 0.10, 0.008, 0.28, mats["WroughtIron"], sides=6, rotation=(math.pi, 0.0, 0.0)))

    # 4 suspension chains (4 x 12 = 48 parts)
    for i in range(4):
        ang = i * (math.pi * 0.5)
        p0 = Vector((math.cos(ang) * 0.12, math.sin(ang) * 0.12, -0.10))
        p1 = Vector((math.cos(ang) * 0.76, math.sin(ang) * 0.76, -1.14))
        parts.extend(kit.spawn_chain_links(f"RackSuspChain_{i}", p0, p1, 12, mats["WroughtIron"], link_radius=0.042, wire_radius=0.012))

    # 10 Hanging Meat Hooks + Crimson Ember Pods + Radial Spokes (40 parts)
    for i in range(10):
        ang = i * (2.0 * math.pi / 10.0)
        rx = math.cos(ang) * 0.80
        ry = math.sin(ang) * 0.80
        parts.append(
            kit.create_beveled_box(
                f"WheelSpoke_{i}",
                (math.cos(ang) * 0.40, math.sin(ang) * 0.40, -1.18),
                (0.76, 0.035, 0.045),
                mats["WroughtIron"],
                bevel_width=0.005,
                rotation=(0.0, 0.0, ang),
            )
        )
        parts.append(kit.create_beveled_cylinder(f"HookDropRod_{i}", (rx, ry, -1.36), 0.018, 0.28, mats["WroughtIron"], vertices=8))
        parts.append(
            kit.create_tapered_prism(
                f"CurvedMeatHook_{i}",
                (rx * 1.06, ry * 1.06, -1.54),
                0.032,
                0.005,
                0.20,
                mats["TarnishedBrass"],
                sides=6,
                rotation=(0.65, 0.0, ang),
            )
        )
        parts.append(kit.create_tapered_prism(f"PerimeterCrimsonPod_{i}", (rx, ry, -1.04), 0.05, 0.015, 0.16, mats["EmissiveCrimsonFurnace"], sides=6))

    assert len(parts) >= 90, f"Expected 90+ parts in abattoir_hanging_hook_rack, got {len(parts)}"
    kit.finalize_and_export_glb(
        os.path.join(OUT_DIR, "abattoir_hanging_hook_rack.glb"),
        parts,
        base_rgb=(0.20, 0.16, 0.16),
        cavity_rgb=(0.08, 0.05, 0.05),
        edge_rgb=(0.38, 0.29, 0.27),
    )


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    build_necropolis_wall_armory_4x4()
    build_necropolis_iron_maiden_monolith()
    build_necropolis_hanging_war_brazier()
    build_reliquary_wall_grimoire_4x4()
    build_reliquary_astral_orrery_monolith()
    build_reliquary_chandelier_astrolabe()
    build_abattoir_wall_furnace_4x4()
    build_abattoir_blood_press_monolith()
    build_abattoir_hanging_hook_rack()
    print("[Biomes2to4Kit] Successfully exported all 9 Biome 2, 3 & 4 Hero Kit GLB models.")


if __name__ == "__main__":
    main()
