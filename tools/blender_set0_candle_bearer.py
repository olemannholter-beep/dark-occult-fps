import bpy
import bmesh
import math
import os
from mathutils import Vector

VOXEL_SIZE_SET0: float = 0.007  # 7mm micro-voxels (~254 voxels tall for 1.78m Hunter)

# Set 0 Bespoke Material Palette: (name, hex_rgb, metallic, roughness, emission_hex, emission_strength)
SET0_MATERIAL_SPECS: list[tuple[str, tuple[float, float, float], float, float, tuple[float, float, float] | None, float]] = [
    ("Set0_MaskSilver_737a80", (0.451, 0.478, 0.502), 0.86, 0.38, None, 0.0),      # 0: Silver-iron mask, star clasp, toe caps
    ("Set0_BlackIron_24272a", (0.141, 0.153, 0.165), 0.85, 0.46, None, 0.0),       # 1: Blackened iron chains, tear-slits, soles
    ("Set0_HoodOuter_3a2e24", (0.227, 0.180, 0.141), 0.04, 0.88, None, 0.0),       # 2: Weathered umber/olive cowl
    ("Set0_InnerShadow_261e18", (0.149, 0.118, 0.094), 0.03, 0.94, None, 0.0),     # 3: Deep hood shadow & dark recessed leather
    ("Set0_MantleOlive_463c2e", (0.275, 0.235, 0.180), 0.04, 0.89, None, 0.0),     # 4: Layered jagged shoulder mantle
    ("Set0_TunicCharcoal_222526", (0.133, 0.145, 0.149), 0.05, 0.86, None, 0.0),   # 5: Tailored dark charcoal buttoned undertunic
    ("Set0_BeltLeather_3d2b1f", (0.239, 0.169, 0.122), 0.06, 0.82, None, 0.0),     # 6: Buckled leather waist belt
    ("Set0_Brass_9e733b", (0.620, 0.451, 0.231), 0.84, 0.42, None, 0.0),           # 7: Tarnished brass buckle & sanctus bell
    ("Set0_CandleWax_d8c39e", (0.847, 0.765, 0.620), 0.02, 0.66, None, 0.0),       # 8: Tallow shoulder candles with wax ribs
    ("Set0_TomeLeather_362b23", (0.212, 0.169, 0.137), 0.06, 0.84, None, 0.0),     # 9: Reliquary tome leather cover
    ("Set0_TomePages_c2b088", (0.761, 0.690, 0.533), 0.02, 0.78, None, 0.0),       # 10: Reliquary tome page block
    ("Set0_Vambrace_33241b", (0.200, 0.141, 0.106), 0.06, 0.83, None, 0.0),        # 11: Dark-leather forearm vambraces
    ("Set0_Breeches_1e2022", (0.118, 0.125, 0.133), 0.05, 0.87, None, 0.0),        # 12: Separate sculpted dark breeches
    ("Set0_CoatOuter_3d2f23", (0.239, 0.184, 0.137), 0.04, 0.88, None, 0.0),       # 13: Flared open-front greatcoat tails
    ("Set0_SkirtInner_33382f", (0.200, 0.220, 0.184), 0.04, 0.90, None, 0.0),      # 14: Inner tattered olive-slate skirt
    ("Set0_Boots_2e2017", (0.180, 0.125, 0.090), 0.07, 0.82, None, 0.0),           # 15: Knee-high leather hunter boots
    ("Set0_Bronze_8c734b", (0.549, 0.451, 0.294), 0.82, 0.44, None, 0.0),          # 16: Bronze ankle & shin buckles
    ("Set0_EyeCrimson_d92b14", (0.851, 0.169, 0.078), 0.10, 0.25, (0.851, 0.169, 0.078), 2.2),  # 17: Glowing crimson pupils
    ("Set0_CandleFlame_ff8811", (1.000, 0.533, 0.067), 0.00, 0.18, (1.000, 0.533, 0.067), 2.5), # 18: Warm orange-gold flame tips
]


def make_set0_materials() -> list[bpy.types.Material]:
    mats: list[bpy.types.Material] = []
    for name, rgb, met, rough, em_rgb, em_str in SET0_MATERIAL_SPECS:
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        nt = mat.node_tree
        nodes = nt.nodes
        links = nt.links
        bsdf = nodes.get("Principled BSDF")
        if bsdf is not None:
            vcol = nodes.new(type="ShaderNodeVertexColor")
            vcol.layer_name = "Col"
            links.new(vcol.outputs["Color"], bsdf.inputs["Base Color"])
            bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
            bsdf.inputs["Metallic"].default_value = met
            bsdf.inputs["Roughness"].default_value = rough
            if em_rgb is not None and "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = (em_rgb[0], em_rgb[1], em_rgb[2], 1.0)
                bsdf.inputs["Emission Strength"].default_value = em_str
        mats.append(mat)
    return mats


class Set0MicroVoxelBuilder:
    """
    7mm (0.007m, octree_depth=8 equivalent) Micro-Voxel Builder for Set 0 (Hooded Candle-Bearer Starter).
    Coordinates:
      ix = +X Right (wx = ix * s)
      iy = +Z Up in Blender / +Y Up in Godot (wz = iy * s)
      iz = -Y Forward in Blender / +Z Forward in Godot (wy = -iz * s)
    Bakes deterministic Per-Voxel Color Jitter (±8% value/warmth per 3D grid coordinate) +
    26-neighbor Cavity AO into COLOR.rgb:
      R = crevice AO (0.50 - 1.00)
      G = raised 1-voxel edge highlight (0.00 - 1.00)
      B = per-voxel warmth shift (0.42 - 0.58, centered at 0.50)
    """

    def __init__(self, name: str, voxel_size: float = VOXEL_SIZE_SET0) -> None:
        self.name: str = name
        self.voxel_size: float = voxel_size
        # Maps (ix, iy, iz) -> (mat_idx, shade_bias)
        self.voxels: dict[tuple[int, int, int], tuple[int, float]] = {}

    def set_voxel(self, ix: int, iy: int, iz: int, mat_idx: int, shade_bias: float = 1.0) -> None:
        self.voxels[(int(ix), int(iy), int(iz))] = (int(mat_idx), float(shade_bias))

    def carve_voxel(self, ix: int, iy: int, iz: int) -> None:
        self.voxels.pop((int(ix), int(iy), int(iz)), None)

    def fill_box(self, x0: int, x1: int, y0: int, y1: int, z0: int, z1: int, mat_idx: int, shade_bias: float = 1.0) -> None:
        for ix in range(min(x0, x1), max(x0, x1) + 1):
            for iy in range(min(y0, y1), max(y0, y1) + 1):
                for iz in range(min(z0, z1), max(z0, z1) + 1):
                    self.voxels[(ix, iy, iz)] = (mat_idx, shade_bias)

    def carve_box(self, x0: int, x1: int, y0: int, y1: int, z0: int, z1: int) -> None:
        for ix in range(min(x0, x1), max(x0, x1) + 1):
            for iy in range(min(y0, y1), max(y0, y1) + 1):
                for iz in range(min(z0, z1), max(z0, z1) + 1):
                    self.voxels.pop((ix, iy, iz), None)

    def fill_ring(
        self,
        iy: int,
        rx_in: float,
        rz_in: float,
        rx_out: float,
        rz_out: float,
        mat_idx: int,
        shade_bias: float = 1.0,
        cx: float = 0.0,
        cz: float = 0.0,
        ix_min: int = -999,
        ix_max: int = 999,
        iz_min: int = -999,
        iz_max: int = 999,
    ) -> None:
        max_x = int(math.ceil(abs(cx) + rx_out + 1))
        max_z = int(math.ceil(abs(cz) + rz_out + 1))
        for ix in range(max(-max_x, ix_min), min(max_x, ix_max) + 1):
            for iz in range(max(-max_z, iz_min), min(max_z, iz_max) + 1):
                dx = (ix + 0.5) - cx
                dz = (iz + 0.5) - cz
                d_out = (dx / max(0.1, rx_out)) ** 2 + (dz / max(0.1, rz_out)) ** 2
                if d_out <= 1.0:
                    if rx_in <= 0.0 or rz_in <= 0.0:
                        self.voxels[(ix, iy, iz)] = (mat_idx, shade_bias)
                    else:
                        d_in = (dx / rx_in) ** 2 + (dz / rz_in) ** 2
                        if d_in >= 1.0:
                            self.voxels[(ix, iy, iz)] = (mat_idx, shade_bias)

    def add_voxel_chain(
        self,
        p0: tuple[int, int, int],
        p1: tuple[int, int, int],
        mat_idx: int = 1,
        sag_voxels: float = 3.0,
    ) -> None:
        dist = math.sqrt((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2 + (p1[2] - p0[2]) ** 2)
        steps = max(8, int(dist * 1.5))
        for i in range(steps + 1):
            t = i / float(steps)
            cx = int(round(p0[0] + (p1[0] - p0[0]) * t))
            cy = int(round(p0[1] + (p1[1] - p0[1]) * t - math.sin(t * math.pi) * sag_voxels))
            cz = int(round(p0[2] + (p1[2] - p0[2]) * t))
            self.set_voxel(cx, cy, cz, mat_idx, 1.0)
            link_phase = i % 3
            if link_phase == 0:
                self.set_voxel(cx, cy + 1, cz, mat_idx, 0.95)
                self.set_voxel(cx, cy - 1, cz, mat_idx, 0.90)
            elif link_phase == 1:
                self.set_voxel(cx + (1 if cx >= 0 else -1), cy, cz + 1, mat_idx, 0.96)

    def add_tallow_candle(
        self,
        cx: int,
        base_y: int,
        cz: int,
        height: int = 8,
        wax_mat: int = 8,
        flame_mat: int = 18,
    ) -> None:
        # 2x2 micro-voxel tallow shaft
        for dy in range(height):
            for dx in (0, 1):
                for dz in (0, 1):
                    self.set_voxel(cx + dx, base_y + dy, cz + dz, wax_mat, 1.02)
        # Dripped wax voxel ribs down the sides & pooled wax base
        for r_dy in range(max(2, height - 2)):
            self.set_voxel(cx - 1, base_y + r_dy, cz, wax_mat, 0.96)
            if r_dy < height // 2:
                self.set_voxel(cx + 2, base_y + r_dy, cz + 1, wax_mat, 0.95)
                self.set_voxel(cx, base_y + r_dy - 1, cz + 2, wax_mat, 0.94)
        self.set_voxel(cx + 1, base_y, cz - 1, wax_mat, 0.94)
        # Warm orange-gold flame tip (#ff8811, emission 2.5)
        fy = base_y + height
        self.set_voxel(cx, fy, cz, flame_mat, 1.05)
        self.set_voxel(cx + 1, fy, cz, flame_mat, 1.05)
        self.set_voxel(cx, fy, cz + 1, flame_mat, 1.05)
        self.set_voxel(cx, fy + 1, cz, flame_mat, 1.08)
        self.set_voxel(cx + 1, fy + 1, cz, flame_mat, 1.06)
        self.set_voxel(cx, fy + 2, cz, flame_mat, 1.10)

    def add_buckle_3d(
        self,
        cx: int,
        cy: int,
        cz: int,
        half_w: int = 3,
        half_h: int = 2,
        frame_mat: int = 7,
        pin_mat: int = 0,
    ) -> None:
        for dx in range(-half_w, half_w + 1):
            for dy in range(-half_h, half_h + 1):
                if abs(dx) == half_w or abs(dy) == half_h:
                    self.set_voxel(cx + dx, cy + dy, cz, frame_mat, 1.04)
                elif dy == 0 and dx in (0, 1):
                    self.set_voxel(cx + dx, cy, cz, pin_mat, 1.02)

    def apply_boolean_remesh_volume(
        self,
        outer_bm: bmesh.types.BMesh,
        inner_bm: bmesh.types.BMesh,
        mat_idx: int,
        octree_depth: int = 8,
    ) -> None:
        """
        Runs Blender BOOLEAN (DIFFERENCE) subtracting the inner mannequin volume (+0.003m margin)
        followed by REMESH (mode='BLOCKS', octree_depth=8, use_remove_disconnected=False)
        anchored to a 256 * 0.007m = 1.792m reference span so block size is exactly 7mm,
        and registers the resulting hollow shell voxels into self.voxels.
        """
        s = self.voxel_size
        # Add 1.792m (256 * 0.007m) guide corners so octree_depth=8 yields exact 7mm blocks
        half_span = (2 ** octree_depth) * s * 0.5
        bmesh.ops.create_cube(outer_bm, size=s)
        for sign in (-1.0, 1.0):
            v_guide = outer_bm.verts.new((0.0, 0.0, sign * half_span))
            outer_bm.verts.ensure_lookup_table()

        outer_me = bpy.data.meshes.new("_TmpOuterShell")
        outer_bm.to_mesh(outer_me)
        outer_obj = bpy.data.objects.new("_TmpOuterShell", outer_me)
        bpy.context.collection.objects.link(outer_obj)

        inner_me = bpy.data.meshes.new("_TmpInnerCutter")
        inner_bm.to_mesh(inner_me)
        inner_obj = bpy.data.objects.new("_TmpInnerCutter", inner_me)
        bpy.context.collection.objects.link(inner_obj)

        bool_mod = outer_obj.modifiers.new(name="HollowInnerShell", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = inner_obj
        if hasattr(bool_mod, "solver"):
            bool_mod.solver = 'FLOAT'

        rem_mod = outer_obj.modifiers.new(name="MicroVoxelBlocks", type='REMESH')
        rem_mod.mode = 'BLOCKS'
        rem_mod.octree_depth = octree_depth
        rem_mod.use_remove_disconnected = False

        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = outer_obj.evaluated_get(depsgraph)
        eval_me = eval_obj.to_mesh()

        for poly in eval_me.polygons:
            c = poly.center
            if abs(c.z) > half_span - s * 2.0:
                continue
            ix = int(round(c.x / s))
            iy = int(round(c.z / s))
            iz = int(round(-c.y / s))
            self.voxels[(ix, iy, iz)] = (mat_idx, 1.0)

        eval_obj.to_mesh_clear()
        bpy.data.objects.remove(outer_obj, do_unlink=True)
        bpy.data.objects.remove(inner_obj, do_unlink=True)
        bpy.data.meshes.remove(outer_me)
        bpy.data.meshes.remove(inner_me)

    def subtract_inner_mannequin_clearance(self, clearance_fn) -> int:
        """
        Hollow Inner Shell subtraction (+0.003m margin beyond inner mannequin volume):
        carves any voxel inside the mannequin clearance envelope.
        """
        s = self.voxel_size
        to_remove: list[tuple[int, int, int]] = []
        for (ix, iy, iz) in self.voxels.keys():
            wx = (ix + 0.5) * s
            wy = -(iz + 0.5) * s
            wz = (iy + 0.5) * s
            if clearance_fn(wx, wy, wz):
                to_remove.append((ix, iy, iz))
        for k in to_remove:
            del self.voxels[k]
        return len(to_remove)

    def build_bmesh(self) -> bmesh.types.BMesh:
        bm = bmesh.new()
        color_layer = bm.loops.layers.color.new("Col")
        s = self.voxel_size
        voxels_dict = self.voxels
        if not voxels_dict:
            return bm

        ys = [k[1] for k in voxels_dict.keys()]
        iy_min, iy_max = min(ys), max(ys)
        iy_span = max(1.0, float(iy_max - iy_min))

        # 6 orthogonal neighbor directions + coplanar tangent pairs for 1-voxel edge detection
        dirs = [
            ((1, 0, 0), ((1, 0, 1), (1, 0, 0), (1, 1, 0), (1, 1, 1)), 0.94, ((0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))),
            ((-1, 0, 0), ((0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)), 0.94, ((0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))),
            ((0, 1, 0), ((0, 1, 1), (1, 1, 1), (1, 1, 0), (0, 1, 0)), 1.05, ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1))),
            ((0, -1, 0), ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)), 0.76, ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1))),
            ((0, 0, 1), ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)), 1.00, ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0))),
            ((0, 0, -1), ((1, 0, 0), (0, 0, 0), (0, 1, 0), (1, 1, 0)), 0.92, ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0))),
        ]

        for (ix, iy, iz), (mat_idx, shade_bias) in voxels_dict.items():
            # Fast internal face cull check
            exposed_dirs = []
            for d_entry in dirs:
                dx, dy, dz = d_entry[0]
                if (ix + dx, iy + dy, iz + dz) not in voxels_dict:
                    exposed_dirs.append(d_entry)
            if not exposed_dirs:
                continue

            # Deterministic Per-Voxel Color Jitter (±8% value & warmth per 3D grid coordinate)
            h_val = ((ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791)) & 0xFFFF
            h_wrm = ((ix * 49979693) ^ (iy * 86028121) ^ (iz * 32452843)) & 0xFFFF
            val_jitter = ((h_val / 65535.0) - 0.5) * 0.16   # -0.08 .. +0.08 (±8%)
            wrm_jitter = ((h_wrm / 65535.0) - 0.5) * 0.16   # -0.08 .. +0.08 (±8%)

            # 26-neighborhood Cavity AO + overhead crevice occlusion
            occ_neighbors = 0
            for nx in (-1, 0, 1):
                for ny in (-1, 0, 1):
                    for nz in (-1, 0, 1):
                        if nx == 0 and ny == 0 and nz == 0:
                            continue
                        if (ix + nx, iy + ny, iz + nz) in voxels_dict:
                            occ_neighbors += 1

            overhead_occ = 1.0 if ((ix, iy + 2, iz) in voxels_dict or (ix, iy + 1, iz + 1) in voxels_dict) else 0.0
            ao_base = 1.0 - (occ_neighbors / 26.0) * 0.42 - overhead_occ * 0.08
            height_grad = 0.86 + ((iy - iy_min) / iy_span) * 0.14
            b_warm = max(0.0, min(1.0, 0.50 + wrm_jitter))

            for (dx, dy, dz), corners, dir_shade, tangents in exposed_dirs:
                verts = [
                    bm.verts.new(((ix + cx) * s, -(iz + cz) * s, (iy + cy) * s))
                    for (cx, cy, cz) in corners
                ]
                face = bm.faces.new((verts[0], verts[1], verts[2], verts[3]))
                face.material_index = mat_idx
                face.smooth = False

                # Count empty coplanar neighbors & diagonal step creases for raised 1-voxel edge highlight (G)
                empty_coplanar = 0
                step_creases = 0
                for tx, ty, tz in tangents:
                    if (ix + tx, iy + ty, iz + tz) not in voxels_dict:
                        empty_coplanar += 1
                    if (ix + dx + tx, iy + dy + ty, iz + dz + tz) in voxels_dict:
                        step_creases += 1

                r_crevice = max(
                    0.50,
                    min(1.0, (ao_base - step_creases * 0.045) * height_grad * dir_shade * shade_bias + val_jitter),
                )
                g_edge = max(
                    0.0,
                    min(1.0, (empty_coplanar / 4.0) * 0.78 + max(0.0, (13 - occ_neighbors) / 13.0) * 0.32),
                )
                col_rgba = (r_crevice, g_edge, b_warm, 1.0)
                for loop in face.loops:
                    loop[color_layer] = col_rgba

        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.00005)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        return bm

    def build_mesh_object(self, mats: list[bpy.types.Material]) -> bpy.types.Object:
        bm = self.build_bmesh()
        mesh = bpy.data.meshes.new(self.name + "_Mesh")
        bm.to_mesh(mesh)
        bm.free()
        for m in mats:
            mesh.materials.append(m)
        obj = bpy.data.objects.new(self.name, mesh)
        bpy.context.collection.objects.link(obj)
        col_attr = obj.data.color_attributes.get("Col")
        if col_attr is not None:
            obj.data.color_attributes.active_color = col_attr
            obj.data.color_attributes.render_color_index = 0
        return obj


def build_set0_head_7mm(v: Set0MicroVoxelBuilder) -> None:
    """
    Set 0 HEAD — Hooded Synod Death-Mask (7mm micro-voxels, mounted at Y=1.54m):
    - Deep, draped weathered umber/olive cowl (#3a2e24 outer, #261e18 inner shadow) with 1-voxel stepped tattered edges.
    - Recessed inside the hood: sculpted, solemn silver-iron face mask (#737a80) with defined brow, nasal bridge,
      vertical black tear-slits under the eyes, and 2-voxel glowing crimson ocular pupils (#d92b14, emission 2.2).
    """
    # 0. BOOLEAN DIFFERENCE + REMESH (mode='BLOCKS', octree_depth=8) base hood volume
    bm_outer = bmesh.new()
    bmesh.ops.create_uvsphere(bm_outer, u_segments=16, v_segments=12, radius=0.102)
    for vert in bm_outer.verts:
        vert.co.z = vert.co.z * 1.25 + 0.06
    bm_inner = bmesh.new()
    bmesh.ops.create_uvsphere(bm_inner, u_segments=16, v_segments=12, radius=0.088)
    for vert in bm_inner.verts:
        vert.co.z = vert.co.z * 1.20 + 0.05
    v.apply_boolean_remesh_volume(bm_outer, bm_inner, mat_idx=2, octree_depth=8)
    bm_outer.free()
    bm_inner.free()
    v.voxels.clear()

    # 1. Draped Weathered Umber/Olive Cowl (#3a2e24 outer = 2, #261e18 inner shadow = 3)
    for iy in range(-11, 35):
        if iy < 0:
            # Flared cowl skirt draping onto collar (iy = -11..-1)
            t_sk = (0 - iy) / 11.0
            rx_in = 11.2 + t_sk * 2.5
            rz_in = 11.6 + t_sk * 2.2
            rx_out = rx_in + 2.4
            rz_out = rz_in + 2.4
            cz = -0.8
        elif iy <= 18:
            # Main hood vault framing temples and cheeks (iy = 0..18)
            u = iy / 18.0
            rx_in = 11.2 + math.sin(u * math.pi) * 1.2
            rz_in = 11.8 + math.sin(u * math.pi) * 1.4
            rx_out = rx_in + 2.3
            rz_out = rz_in + 2.5
            cz = -0.5 - u * 1.2
        else:
            # Pointed gothic hood peak sweeping forward & back (iy = 19..34)
            u = (iy - 18) / 16.0
            rx_out = 13.2 * (1.0 - u * 0.82)
            rz_out = 14.0 * (1.0 - u * 0.68)
            rx_in = max(0.0, rx_out - 2.4) if iy < 30 else 0.0
            rz_in = max(0.0, rz_out - 2.4) if iy < 30 else 0.0
            cz = -1.5 + u * 4.2

        # Outer cowl layer (#3a2e24) with front face arch opening
        front_arch_open = 9 if iy <= 14 else max(2, int(round(9 - (iy - 14) * 1.1)))
        for ix in range(-18, 19):
            for iz in range(-19, 18):
                dx = (ix + 0.5)
                dz = (iz + 0.5) - cz
                d_out = (dx / max(0.5, rx_out)) ** 2 + (dz / max(0.5, rz_out)) ** 2
                d_in = (dx / max(0.5, rx_in)) ** 2 + (dz / max(0.5, rz_in)) ** 2 if rx_in > 0.2 else 99.0
                if d_out <= 1.0 and d_in >= 1.0:
                    # Carve front hood opening so silver-iron face mask sits recessed inside
                    if -5 <= iy <= 20 and iz >= 9 and abs(ix) <= front_arch_open:
                        continue
                    # 1-voxel stepped tattered edges along bottom cowl skirt and front hood rim
                    if iy <= -8 and ((ix * 7 + iz * 5 + iy * 3) % 7 == 0):
                        continue
                    if iz >= 8 and abs(abs(ix) - (front_arch_open + 1)) <= 1 and ((iy * 5 + ix * 3) % 5 == 0):
                        continue
                    # Sculpted +1 voxel cloth fold ribs along cowl sides and crown
                    is_inner_shadow = (d_in < 1.32) or (iz >= 7 and abs(ix) <= front_arch_open + 2 and iy <= 21)
                    v.set_voxel(ix, iy, iz, 3 if is_inner_shadow else 2, 0.90 if is_inner_shadow else 1.00)
                    if not is_inner_shadow and (abs(ix) in (6, 12) or (ix == 0 and iz <= 0)) and d_out >= 0.82:
                        v.set_voxel(ix, iy, iz + (1 if iz > 0 else -1), 2, 1.04)

    # 2. Recessed Inner Shadow Vault behind face mask (#261e18, mat_idx = 3)
    for iy in range(-5, 21):
        v.fill_ring(iy, 8.8, 9.2, 11.2, 11.6, 3, 0.85, iz_min=2, iz_max=10)

    # 3. Solemn Silver-Iron Face Mask (#737a80, mat_idx = 0) recessed inside hood (iz = 9..12, iy = -5..17)
    for iy in range(-5, 18):
        u_m = (iy + 5) / 22.0
        half_w = int(round(6.8 - max(0.0, (0.35 - u_m) * 7.5) - max(0.0, (u_m - 0.78) * 9.0)))
        for ix in range(-half_w, half_w + 1):
            z_curve = int(round(11.4 - (abs(ix) / max(1.0, float(half_w + 1))) ** 1.6 * 2.6))
            for dz in (-1, 0):
                v.set_voxel(ix, iy, z_curve + dz, 0, 1.02)

    # Defined Silver-Iron Brow Ridge (iy = 11..13), Nasal Bridge (ix = -1..1, iy = 2..12), & Cheekbones
    for ix in range(-6, 7):
        z_brow = int(round(12.2 - (abs(ix) / 7.0) ** 1.5 * 2.0))
        v.set_voxel(ix, 12, z_brow, 0, 1.06)
        if abs(ix) <= 4:
            v.set_voxel(ix, 13, z_brow, 0, 1.05)
        if abs(ix) in (3, 4, 5):
            v.set_voxel(ix, 6, z_brow - 1, 0, 1.04)  # Cheekbone ridge

    for iy in range(2, 13):
        nose_z = 12 if iy >= 8 else 13
        v.set_voxel(0, iy, nose_z, 0, 1.08)
        if iy <= 6:
            v.set_voxel(-1, iy, nose_z - 1, 0, 1.03)
            v.set_voxel(1, iy, nose_z - 1, 0, 1.03)

    # Solemn slit mouth groove (iy = -1)
    for ix in range(-2, 3):
        v.set_voxel(ix, -1, 10, 1, 0.78)
        v.carve_voxel(ix, -1, 11)

    # 4. Recessed Eye Sockets, 2-Voxel Glowing Crimson Pupils (#d92b14, mat_idx=17), & Black Tear-Slits (mat_idx=1)
    for sx in (-1, 1):
        for dx in (2, 3, 4, 5):
            ex = sx * dx
            for ey in (9, 10, 11):
                v.carve_voxel(ex, ey, 12)
                v.carve_voxel(ex, ey, 11)
                v.set_voxel(ex, ey, 9, 1, 0.75)
        # 2-voxel glowing crimson ocular pupils (#d92b14, emission 2.2)
        v.set_voxel(sx * 3, 10, 10, 17, 1.08)
        v.set_voxel(sx * 4, 10, 10, 17, 1.08)
        # Vertical black tear-slits under the eyes (iy = 1..8)
        for ty in range(1, 9):
            tx = sx * 3
            v.carve_voxel(tx, ty, 11)
            v.set_voxel(tx, ty, 10, 1, 0.70)

    # 5. Hollow Inner Shell (+0.003m margin beyond inner head core)
    v.subtract_inner_mannequin_clearance(
        lambda wx, wy, wz: (-0.08 <= wz <= 0.21) and ((wx / 0.068) ** 2 + (wy / 0.072) ** 2 < 1.0)
    )


def build_set0_chest_7mm(v: Set0MicroVoxelBuilder) -> None:
    """
    Set 0 CHEST — Candle-Bearer Mantle, Collar Bell & Chained Grimoire (7mm micro-voxels, mounted at Y=0.96m):
    - Heroic V-Taper: broad shoulders (0.48m wide = 68 voxels) tapering to a pinched narrow waist (0.28m wide = 40 voxels).
    - Tailored dark charcoal buttoned undertunic (#222526) with buckled leather waist belt (#3d2b1f, brass buckle #9e733b).
    - Layered jagged shoulder mantle (#463c2e) draped over clavicles & deltoids with pixel-stepped frayed hems & cutouts.
    - Shoulder Candles: 3 distinct micro-voxel tallow candles (#d8c39e) on both left & right pauldrons with dripped wax
      ribs and warm orange-gold flame tips (#ff8811, emission 2.5).
    - Collar Bell & Grimoire: tarnished brass sanctus bell (#9e733b) on iron neck chain at sternum, and iron-bound
      reliquary tome (#362b23 cover, #c2b088 page block, #737a80 iron star clasp) slung diagonally to the left hip.
    """
    # 1. V-Tapered Dark Charcoal Buttoned Undertunic (#222526, mat_idx = 5) from waist (iy=0..8) to shoulders (iy=68)
    for iy in range(-2, 70):
        t = max(0.0, min(1.0, iy / 66.0))
        # Waist at iy=0..6 is 0.28m wide (rx_out = 20.0 voxels = 0.140m); shoulders expand to 0.44m under mantle
        v_curve = (t ** 1.15)
        rx_out = 19.8 + v_curve * 11.2
        rz_out = 12.8 + math.sin(t * math.pi * 0.75) * 3.2
        rx_in = rx_out - 2.4
        rz_in = rz_out - 2.4
        v.fill_ring(iy, rx_in, rz_in, rx_out, rz_out, 5, 0.98)

        # Tailored front waistcoat placket & double column of 1-voxel brass buttons (#9e733b, mat_idx = 7)
        iz_front = int(round(rz_out))
        if 7 <= iy <= 42:
            v.set_voxel(0, iy, iz_front, 3, 0.85)  # Center placket seam
            for lx in (-4, 4):
                v.set_voxel(lx, iy, iz_front, 5, 1.03)  # Raised lapel edge
            if iy % 6 == 2:
                v.set_voxel(-2, iy, iz_front + 1, 7, 1.06)
                v.set_voxel(2, iy, iz_front + 1, 7, 1.06)

    # 2. Articulated Buckled Leather Waist Belt (#3d2b1f = 6, brass buckle #9e733b = 7) at pinched 0.28m waist (iy=0..6)
    for iy in range(0, 7):
        is_rim = iy in (0, 6)
        mat_b = 3 if is_rim else 6
        # Protrudes +1 voxel proud (rx_out = 20.8 -> 0.29m outer belt width over 0.28m waist)
        v.fill_ring(iy, 18.2, 11.4, 20.8, 14.0, mat_b, 0.94 if is_rim else 1.02)
        if iy == 3:
            for stud_x in (-16, -12, -8, 8, 12, 16):
                v.set_voxel(stud_x, iy, 14, 7, 1.05)
    # 3D Brass Waist Buckle (#9e733b frame = 7, silver-iron pin = 0) at front center
    v.add_buckle_3d(0, 3, 15, half_w=4, half_h=3, frame_mat=7, pin_mat=0)

    # 3. Layered Jagged Shoulder Mantle (#463c2e, mat_idx = 4) spanning 0.48m heroic shoulder width (ix = -34..+34)
    for iy in range(38, 76):
        mt = (iy - 38) / 37.0
        # Broad 0.48m shoulders at iy = 54..68 (rx_out = 34.3 voxels = 0.240m radius -> 0.480m total width!)
        if iy <= 66:
            shoulder_flare = math.sin(min(1.0, (iy - 38) / 24.0) * (math.pi * 0.5))
            rx_out = 26.0 + shoulder_flare * 8.3
            rz_out = 15.8 + shoulder_flare * 2.4
        else:
            # High upturned collar & pauldron slope (iy = 67..75)
            u_top = (iy - 66) / 9.0
            rx_out = 34.3 * (1.0 - u_top * 0.58)
            rz_out = 18.2 * (1.0 - u_top * 0.32)

        rx_in = max(11.5, rx_out - 2.6)
        rz_in = max(11.5, rz_out - 2.6)
        max_x = int(math.ceil(rx_out + 1))
        max_z = int(math.ceil(rz_out + 1))

        for ix in range(-max_x, max_x + 1):
            # Jagged pixel-stepped V-hem across chest, back, and deltoids
            jag_wave = ((abs(ix) * 5) % 7) - int(abs(ix) * 0.22)
            hem_y = 44 + jag_wave
            if iy < hem_y:
                continue
            for iz in range(-max_z, max_z + 1):
                d_out = (ix / max(0.5, rx_out)) ** 2 + (iz / max(0.5, rz_out)) ** 2
                d_in = (ix / max(0.5, rx_in)) ** 2 + (iz / max(0.5, rz_in)) ** 2
                if d_out <= 1.0 and d_in >= 1.0:
                    # Frayed 1-voxel cutouts & weathered holes near lower hem
                    if iy <= hem_y + 3 and ((ix * 11 + iy * 7 + iz * 5) % 9 == 0):
                        continue
                    # Leave front throat V-notch open at iy >= 66 so collar bell & chin sit cleanly
                    if iy >= 66 and iz >= 10 and abs(ix) <= (iy - 63):
                        continue
                    is_border = (iy <= hem_y + 1) or (iy >= 73)
                    v.set_voxel(ix, iy, iz, 4, 1.04 if is_border else 0.98)

        # Second overlapping upper pauldron cape layer (+1 voxel proud at iy = 56..70)
        if 56 <= iy <= 70:
            v.fill_ring(iy, rx_out - 0.8, rz_out - 0.8, rx_out + 1.1, rz_out + 1.1, 4, 1.03, ix_min=-35, ix_max=-16)
            v.fill_ring(iy, rx_out - 0.8, rz_out - 0.8, rx_out + 1.1, rz_out + 1.1, 4, 1.03, ix_min=16, ix_max=35)

    # 4. Shoulder Candles: 3 Distinct Micro-Voxel Tallow Candles (#d8c39e = 8) + Flames (#ff8811 = 18) per Pauldron
    left_candles = [
        (-31, 67, -1, 7),
        (-27, 69, 2, 10),
        (-23, 68, -3, 6),
    ]
    right_candles = [
        (22, 68, -2, 7),
        (26, 69, 2, 9),
        (30, 67, -1, 6),
    ]
    for cx, cy, cz, ch in left_candles + right_candles:
        v.add_tallow_candle(cx, cy, cz, height=ch, wax_mat=8, flame_mat=18)

    # 5. Collar Bell (#9e733b = 7) hanging from Forged Iron Neck Chain (#24272a = 1) at Sternum
    v.add_voxel_chain((-12, 65, 14), (0, 53, 17), mat_idx=1, sag_voxels=2.2)
    v.add_voxel_chain((12, 65, 14), (0, 53, 17), mat_idx=1, sag_voxels=2.2)
    # Sanctus Bell crown loop (iy = 51..52), bell body (iy = 47..50), flared rim (iy = 45..46), & iron clapper (iy = 44)
    v.fill_box(-1, 1, 51, 52, 16, 17, 7, 1.04)
    v.fill_box(-2, 2, 47, 50, 15, 18, 7, 1.05)
    v.fill_box(-3, 3, 45, 46, 14, 19, 7, 1.08)
    v.carve_box(-1, 1, 45, 46, 16, 17)
    v.set_voxel(0, 44, 17, 0, 1.02)  # Iron bell clapper

    # 6. Chained Reliquary Grimoire Tome Slung Diagonally Across Chest to Left Hip
    # Front & back diagonal voxel-link iron chains (#24272a = 1, #737a80 = 0 highlights)
    v.add_voxel_chain((-16, 65, 15), (19, 6, 12), mat_idx=0, sag_voxels=1.8)
    v.add_voxel_chain((-16, 65, -15), (19, 6, -4), mat_idx=1, sag_voxels=1.8)
    v.add_voxel_chain((16, 65, 15), (-19, 6, 12), mat_idx=1, sag_voxels=1.8)

    # Iron-Bound Reliquary Tome resting at Front-Left Hip (angled on front-hip corner so cover, pages & star clasp show)
    for lx_sign in (-1, 1):
        if lx_sign == -1:
            # Primary Chained Grimoire Tome on hip (ix = -24..-17, iy = -9..+7, iz = +3..+14)
            v.fill_box(-24, -23, -9, 7, 3, 14, 9, 0.98)   # Outer leather cover (#362b23 = 9)
            v.fill_box(-19, -18, -9, 7, 3, 14, 9, 0.96)   # Inner leather cover (#362b23 = 9)
            v.fill_box(-23, -19, 6, 7, 3, 14, 9, 1.02)    # Top leather spine
            # Cream Parchment Page Block (#c2b088 = 10) clearly visible on front (+iz=14) & bottom (-9) edges
            v.fill_box(-22, -20, -8, 5, 4, 14, 10, 1.04)
            # Silver-iron corner brackets & 5-point iron star clasp (#737a80 = 0) on front/outer cover
            for cy_b in (-9, -8, 6, 7):
                for cz_b in (3, 4, 13, 14):
                    v.set_voxel(-25, cy_b, cz_b, 0, 1.06)
                    v.set_voxel(-23, cy_b, 15, 0, 1.06)
            for dy_s, dz_s in ((0, 0), (2, 0), (-2, 0), (0, 2), (0, -2), (1, 1), (-1, 1), (1, -1), (-1, -1)):
                v.set_voxel(-25, -1 + dy_s, 8 + dz_s, 0, 1.08)
            v.fill_box(-25, -18, -2, 0, 14, 15, 0, 1.06)  # Front iron star strap clasp

    # 7. Hollow Inner Shell (+0.003m margin beyond inner torso core)
    v.subtract_inner_mannequin_clearance(
        lambda wx, wy, wz: (-0.03 <= wz <= 0.52) and ((wx / 0.118) ** 2 + (wy / 0.075) ** 2 < 1.0)
    )


def build_set0_hands_7mm(v: Set0MicroVoxelBuilder) -> None:
    """
    Set 0 HANDS — Bilateral Strapped Vambraces, Gloved Fingers & Left Wrist Chain (7mm micro-voxels, mounted at Y=1.05m):
    - Positioned along left & right arms (X = ±0.245m..±0.265m), leaving a wide air gap around the 0.28m waist.
    - Tapered dark-leather forearm vambraces (#33241b = 11) with upper-arm charcoal sleeve bridge (#222526 = 5).
    - 3 raised buckled straps (+1 voxel proud of the sleeve, #261e18 = 3, bronze/brass buckles #8c734b = 16 / #9e733b = 7).
    - Articulated dark-gloved fingers (#261e18 = 3 / #33241b = 11) with silver-iron knuckle studs (#737a80 = 0).
    - 6-link blackened-iron chain (#24272a = 1) hanging from the LEFT wrist cuff.
    """
    for side in (-1, 1):
        # 1. Upper-arm charcoal sleeve bridge (iy = 20..52 -> world Y = 1.19m..1.41m) connecting seamlessly into shoulder mantle
        for iy in range(20, 53):
            u = (iy - 20) / 32.0
            cx = side * (33.5 - u * 6.5)
            cz = 1.5 - u * 2.0
            r_out = 5.4 + u * 1.4
            r_in = r_out - 2.2
            v.fill_ring(iy, r_in, r_in, r_out, r_out, 5, 0.96, cx=cx, cz=cz)
            if iy in (21, 22):
                # Silver-iron elbow couter rim (#737a80 = 0)
                v.fill_ring(iy, r_out - 0.5, r_out - 0.5, r_out + 0.8, r_out + 0.8, 0, 1.04, cx=cx, cz=cz, iz_min=-8, iz_max=2)

        # 2. Tapered Dark-Leather Forearm Vambrace (#33241b = 11, iy = -8..21 -> world Y = 0.99m..1.20m)
        strap_ys = (-5, 4, 13)  # 3 raised buckled straps
        for iy in range(-8, 22):
            t = (iy + 8) / 29.0  # 0 at wrist (-8), 1 at elbow (+21)
            cx = side * (35.5 - t * 2.0)
            cz = 4.5 - t * 3.0
            r_base = 4.4 + t * 1.4
            is_strap = any(abs(iy - sy) <= 1 for sy in strap_ys)
            # Straps sit +1 voxel proud of the sleeve!
            r_out = (r_base + 1.1) if is_strap else r_base
            r_in = max(2.2, r_base - 1.8)
            mat = 3 if is_strap else 11
            v.fill_ring(iy, r_in, r_in, r_out, r_out, mat, 0.94 if is_strap else 1.00, cx=cx, cz=cz)

            # Dorsal blackened-iron splint strips (#24272a = 1) along outer forearm
            if not is_strap and -6 <= iy <= 18:
                ix_outer = int(round(cx + side * r_base))
                iz_mid = int(round(cz))
                v.set_voxel(ix_outer, iy, iz_mid, 1, 1.02)
                v.set_voxel(ix_outer, iy, iz_mid + 2, 1, 1.00)

        # 3D Buckles on the 3 raised straps (outer-front face of forearm)
        for sy in strap_ys:
            t = (sy + 8) / 29.0
            bx = int(round(side * (35.5 - t * 2.0)))
            bz = int(round(4.5 - t * 3.0 + (4.4 + t * 1.4) + 1.2))
            v.add_buckle_3d(bx, sy, bz, half_w=2, half_h=1, frame_mat=16, pin_mat=0)

        # 3. Articulated Dark-Gloved Metacarpal Hand & Fingers (iy = -22..-9 -> world Y = 0.89m..0.98m)
        wrist_x = side * 35.5
        wrist_z = 4.8
        for iy in range(-15, -8):
            ht = (iy + 15) / 7.0
            hx = int(round(wrist_x + side * (1.0 - ht) * 0.5))
            hz = int(round(wrist_z + (1.0 - ht) * 1.0))
            v.fill_box(hx - 2, hx + 2, iy, iy, hz - 3, hz + 3, 11 if iy >= -12 else 3, 0.98)
            # Silver-iron knuckle studs (#737a80 = 0) at iy = -15
            if iy == -15:
                for kz in (-2, 0, 2, 4):
                    v.set_voxel(hx + side * 3, iy, hz + kz, 0, 1.06)

        # 4 Individual Articulated Curled Gloved Fingers (iy = -22..-16)
        for f_i, fz_off in enumerate((-2, 0, 2, 4)):
            f_len = 7 if f_i in (1, 2) else 6
            for dy in range(f_len):
                fy = -16 - dy
                curl_in = 1 if dy >= 4 else 0
                fx = int(round(wrist_x + side * (2 - curl_in)))
                fz = int(round(wrist_z + fz_off))
                v.set_voxel(fx, fy, fz, 3 if dy >= 2 else 11, 0.96)
                v.set_voxel(fx - side, fy, fz, 3, 0.92)

        # Opposable Thumb (iy = -17..-12, forward +iz)
        for dy in range(6):
            ty = -12 - dy
            tx = int(round(wrist_x - side * (1 if dy >= 3 else 0)))
            tz = int(round(wrist_z + 4 + (1 if dy <= 2 else 0)))
            v.set_voxel(tx, ty, tz, 11 if dy < 3 else 3, 0.98)

        # 4. 6-Link Blackened-Iron Chain Hanging from the LEFT Wrist Cuff (side == -1)
        if side == -1:
            chain_x = int(round(wrist_x - 2))
            chain_z = int(round(wrist_z - 1))
            for link_i in range(6):
                ly_top = -8 - link_i * 3
                if link_i % 2 == 0:
                    # Link oriented in X-Y plane (hollow 3x4 ring)
                    for dx in (-1, 0, 1):
                        for dy in range(4):
                            if abs(dx) == 1 or dy in (0, 3):
                                v.set_voxel(chain_x + dx, ly_top - dy, chain_z, 1, 1.02)
                else:
                    # Interlocking link oriented in Z-Y plane (hollow 3x4 ring)
                    for dz in (-1, 0, 1):
                        for dy in range(4):
                            if abs(dz) == 1 or dy in (0, 3):
                                v.set_voxel(chain_x, ly_top - dy, chain_z + dz, 0 if link_i == 5 else 1, 1.04)


def build_set0_legs_7mm(v: Set0MicroVoxelBuilder) -> None:
    """
    Set 0 LEGS — Layered Tattered Greatcoat Skirts & Breeches (7mm micro-voxels, mounted at X=±0.125m, Y=0.88m):
    - Separate sculpted dark breeches (#1e2022 = 12) with knee articulation, maintaining a clean >0.14m gap
      between left and right inner thighs/calves.
    - Framed by flared, open-front greatcoat tails (#3d2f23 outer coat = 13, #33382f inner tattered skirt = 14)
      with stepped 1-voxel holes and jagged bottom hems that part cleanly in the center so both legs are clearly visible.
    """
    # 1. Separate Sculpted Dark Breeches (#1e2022 = 12) with Knee Articulation (iy = -66..+10 -> world Y = 0.42m..0.95m)
    for iy in range(-66, 11):
        t = (iy + 66) / 76.0  # 0 at upper calf (-66), 1 at hip (+10)
        r_out = 5.6 + t * 1.3  # 0.039m at calf to 0.048m at thigh -> 0.154m (>0.14m) gap between inner thighs!
        r_in = r_out - 2.0
        # Subtle tailored seam ridges
        if iy % 8 == 0:
            r_out += 0.25
        v.fill_ring(iy, r_in, r_in, r_out, r_out, 12, 0.98)

    # Sculpted Knee Articulation & Poleyn Ridges (iy = -45..-33 -> world Y = 0.565m..0.65m)
    for iy in range(-45, -32):
        k_bulge = 1.2 if -42 <= iy <= -36 else 0.6
        mat_k = 0 if iy in (-43, -39, -35) else 1
        v.fill_ring(iy, 5.2, 5.2, 6.4 + k_bulge, 6.8 + k_bulge, mat_k, 1.03, iz_min=1, iz_max=9)
    # Buckled knee & thigh straps (#3d2b1f = 6, bronze buckle #8c734b = 16)
    for sy in (-44, -34, -16):
        v.fill_ring(sy, 5.2, 5.2, 7.2, 7.2, 6, 0.96)
        v.add_buckle_3d(0, sy, 8, half_w=2, half_h=1, frame_mat=16, pin_mat=0)

    # 2. Flared, Open-Front Greatcoat Tails (#3d2f23 outer = 13, #33382f inner tattered skirt = 14)
    # Sweeps from narrow 0.28m waist (iy = +12, outer hip at ix = +2) down to iy = -64, flaring outward on +ix
    for iy in range(-64, 13):
        drop = (12 - iy) / 76.0  # 0.0 at waist (+12), 1.0 at bottom hem (-64)
        # Outer flank flare: starts at ix=+2 at waist (world X = 0.125 + 0.014 = 0.139m -> 0.278m waist!)
        # and flares out to ix=+16 at bottom hem (world X = 0.237m)
        coat_rx = 7.2 + drop * 8.8
        coat_rz = 8.4 + drop * 5.2
        coat_cx = 1.5 + drop * 2.5
        coat_cz = -1.2 - drop * 1.5

        max_x = int(math.ceil(coat_cx + coat_rx + 2))
        max_z = int(math.ceil(abs(coat_cz) + coat_rz + 2))
        for ix in range(-4, max_x + 1):
            for iz in range(-max_z, max_z + 1):
                # Keep inner thigh gap (-ix < -4) 100% open from front to back!
                # And part cleanly in the front center (iz >= -1) in an inverted-V opening so both breeches & knees show!
                front_part_x = int(round(1.5 + drop * 6.5))
                if iz >= -1 and ix < front_part_x:
                    continue
                if iz < -1 and ix < -3:
                    continue

                dx = (ix + 0.5) - coat_cx
                dz = (iz + 0.5) - coat_cz
                d_norm = math.sqrt((dx / coat_rx) ** 2 + (dz / coat_rz) ** 2)

                # Jagged sawtooth bottom hems for Outer Coat (-50..-57) vs Inner Tattered Skirt (-56..-64)
                jag_outer = -51 - ((abs(ix * 3 + iz * 5)) % 7)
                jag_inner = -57 - ((abs(ix * 7 + iz * 3)) % 8)

                # Outer Greatcoat Layer (#3d2f23 = 13)
                if iy >= jag_outer and 0.86 <= d_norm <= 1.04:
                    # Stepped 1-voxel and 2-voxel tattered holes near lower hem
                    if iy <= -34 and ((ix * 11 + iy * 7 + iz * 5) % 13 == 0):
                        continue
                    if iy <= -42 and (((ix // 2) * 7 + (iy // 2) * 11 + iz * 3) % 11 == 0):
                        continue
                    is_pleat = ((ix + iz) % 5 == 0) and d_norm >= 0.96
                    v.set_voxel(ix, iy, iz, 13, 1.04 if is_pleat else 0.98)

                # Inner Tattered Skirt Layer (#33382f = 14), recessed 1 voxel inside & hanging below outer coat hem
                if iy >= jag_inner and iy <= -20 and 0.76 <= d_norm < 0.90:
                    if iy <= -44 and ((ix * 5 + iy * 9 + iz * 7) % 9 == 0):
                        continue
                    v.set_voxel(ix, iy, iz, 14, 0.94)

    # 3. Hollow Inner Shell (+0.003m margin beyond inner leg core)
    v.subtract_inner_mannequin_clearance(
        lambda wx, wy, wz: (-0.48 <= wz <= 0.12) and ((wx / 0.028) ** 2 + (wy / 0.028) ** 2 < 1.0)
    )


def build_set0_feet_7mm(v: Set0MicroVoxelBuilder) -> None:
    """
    Set 0 FEET — Buckled Stalker Sabaton-Boots (7mm micro-voxels, mounted at X=±0.125m, Y=0.18m):
    - Distinct left and right knee-high leather hunter boots (#2e2017 = 15) with flared cavalier knee cuffs.
    - Layered shin plates (#3a2e24 = 2 & silver-iron #737a80 = 0), iron toe caps (#737a80 = 0),
      and bronze ankle/shin buckles (#8c734b = 16).
    """
    # 1. Knee-High Leather Hunter Boot Shaft (#2e2017 = 15, iy = -16..+38 -> world Y = 0.068m..0.446m)
    for iy in range(-16, 39):
        t = (iy + 16) / 54.0
        is_cuff = iy >= 28
        r_out = (6.6 + (38 - iy) * 0.12) if is_cuff else (5.4 + t * 1.1)
        r_in = r_out - 2.0
        mat_s = 3 if iy in (28, 38) else 15
        v.fill_ring(iy, r_in, r_in, r_out, r_out, mat_s, 0.98)

    # 2. Layered Shin Plates (+1 voxel proud on front shin, iy = -8..+26, iz = 5..8)
    for iy in range(-8, 27):
        lame_step = (iy + 8) % 7 == 0
        for ix in range(-3, 4):
            z_sh = 7 if abs(ix) <= 1 else 6
            mat_p = 0 if (ix == 0 or lame_step) else 2
            v.set_voxel(ix, iy, z_sh, mat_p, 1.04 if mat_p == 0 else 1.00)

    # 3. Raised Straps & 3D Bronze Ankle/Shin Buckles (#8c734b = 16) at iy = -9, +4, +18
    for sy in (-9, 4, 18):
        v.fill_ring(sy, 4.8, 4.8, 6.8, 6.8, 3, 0.95)
        v.add_buckle_3d(0, sy, 8, half_w=2, half_h=1, frame_mat=16, pin_mat=0)

    # 4. Boot Foot (#2e2017 = 15), Overlapping Silver-Iron Sabaton Toe Cap (#737a80 = 0), & Cleated Sole (#24272a = 1)
    for iy in range(-24, -13):
        h_t = (iy + 24) / 11.0
        max_z = int(round(15 - h_t * 5.0))
        hw = int(round(5.6 - h_t * 0.8))
        for ix in range(-hw, hw + 1):
            for iz in range(-6, max_z + 1):
                if (ix / (hw + 0.5)) ** 2 + ((iz - 3.5) / (max_z + 6.5)) ** 2 <= 1.0:
                    is_toecap = iz >= 6
                    is_lame_ridge = is_toecap and (iz in (6, 10, 13) or ix == 0)
                    mat_f = 0 if is_toecap else 15
                    v.set_voxel(ix, iy, iz, mat_f, 1.06 if is_lame_ridge else 1.00)

    # Cleated Dark-Iron Sole at iy = -26..-25 (world Y = 0.000m..0.014m)
    for iy in (-26, -25):
        for ix in range(-5, 6):
            for iz in range(-6, 16):
                if (ix / 5.6) ** 2 + ((iz - 3.8) / 11.2) ** 2 <= 1.0:
                    if iy == -26 and iz in (-2, 2, 6, 10) and abs(ix) <= 4:
                        continue
                    v.set_voxel(ix, iy, iz, 1, 0.86)

    # 5. Hollow Inner Shell (+0.003m margin beyond inner ankle/calf core)
    v.subtract_inner_mannequin_clearance(
        lambda wx, wy, wz: (wz >= -0.14) and ((wx / 0.025) ** 2 + (wy / 0.025) ** 2 < 1.0)
    )


def build_set0_mannequin_7mm(output_glb_path: str) -> None:
    """
    Rebuilds gothic_arming_mannequin.glb with ZERO central stand pole between the legs
    so the 0.14m inner thigh/calf separation is 100% open air, while providing the inner
    neck, V-tapered torso core, pelvis bridge, and separated leg cores with all 14 ZONE_* vertex groups.
    """
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = make_set0_materials()
    v = Set0MicroVoxelBuilder("GothicArmingMannequin", voxel_size=0.010)
    s = v.voxel_size

    # Pelvis bridge & V-tapered inner torso core (Z = 0.86m..1.52m, NO stand pole below 0.86m!)
    for iy in range(int(round(0.86 / s)), int(round(1.52 / s)) + 1):
        wz = iy * s
        t = (wz - 0.86) / 0.66
        rx = (0.115 if wz < 1.02 else 0.105 + (t - 0.24) * 0.075) / s
        rz = (0.072 if wz < 1.02 else 0.068 + (t - 0.24) * 0.030) / s
        if wz >= 1.42:
            rx, rz = 0.056 / s, 0.056 / s
        v.fill_ring(iy, max(0.0, rx - 1.5), max(0.0, rz - 1.5), rx, rz, 5, 0.92)

    # Separated left & right inner leg cores (X = ±0.125m, Z = 0.16m..0.88m)
    for side in (-1, 1):
        cx = (side * 0.125) / s
        for iy in range(int(round(0.16 / s)), int(round(0.88 / s)) + 1):
            v.fill_ring(iy, 1.0, 1.0, 2.4, 2.4, 12, 0.90, cx=cx, cz=0.0)

    obj = v.build_mesh_object(mats)
    group_names = [
        "ZONE_HEAD", "ZONE_CHEST", "ZONE_PAULDRON_L", "ZONE_PAULDRON_R",
        "ZONE_VAMBRACE_L", "ZONE_VAMBRACE_R", "ZONE_GAUNTLET_HAND_L", "ZONE_GAUNTLET_HAND_R",
        "ZONE_CUISSE_L", "ZONE_CUISSE_R", "ZONE_GREAVE_L", "ZONE_GREAVE_R",
        "ZONE_SABATON_L", "ZONE_SABATON_R",
    ]
    vgroups = {g: obj.vertex_groups.new(name=g) for g in group_names}
    for idx, vert in enumerate(obj.data.vertices):
        vgroups["ZONE_CHEST" if vert.co.z >= 0.86 else ("ZONE_CUISSE_L" if vert.co.x < 0 else "ZONE_CUISSE_R")].add([idx], 1.0, 'REPLACE')

    os.makedirs(os.path.dirname(output_glb_path), exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(
        filepath=output_glb_path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_all_vertex_colors=True,
    )
    print(f"[Set 0 Mannequin] Exported {output_glb_path} | voxels={len(v.voxels)} | tris={len(obj.data.polygons) * 2}")


def export_set0_piece_7mm(slot: str, builder_fn, output_dir: str) -> tuple[str, int, int, int]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = make_set0_materials()
    builder = Set0MicroVoxelBuilder(f"Armor_Set0_{slot}", voxel_size=VOXEL_SIZE_SET0)
    builder_fn(builder)
    voxel_count = len(builder.voxels)
    obj = builder.build_mesh_object(mats)
    tri_count = sum(len(p.vertices) - 2 for p in obj.data.polygons)

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"armor_set0_{slot}.glb")
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_all_vertex_colors=True,
    )
    fsize = os.path.getsize(out_path) if os.path.exists(out_path) else 0
    print(f"[Set 0 7mm Starter] armor_set0_{slot}.glb | voxels={voxel_count} | tris={tri_count} | size={fsize} bytes")
    return out_path, voxel_count, tri_count, fsize


def export_all_set0_starter(output_dir: str) -> None:
    build_set0_mannequin_7mm(os.path.join(output_dir, "gothic_arming_mannequin.glb"))
    jobs = [
        ("head", build_set0_head_7mm),
        ("chest", build_set0_chest_7mm),
        ("hands", build_set0_hands_7mm),
        ("legs", build_set0_legs_7mm),
        ("feet", build_set0_feet_7mm),
    ]
    for slot, fn in jobs:
        export_set0_piece_7mm(slot, fn, output_dir)
