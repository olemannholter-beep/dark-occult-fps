import bpy
import bmesh
import math
from mathutils import Vector


def make_micro_voxel_materials(set_idx: int = 0) -> list[bpy.types.Material]:
    """
    Creates the 4 Gothic PBR materials (Mat_Iron, Mat_Leather, Mat_Brass, Mat_RuneGlow)
    wired with a Vertex Color ('Col') node multiplying Base Color so both Blender Workbench/EEVEE
    and Godot's StandardMaterial3D / gothic_armory_plate.gdshader display crisp micro-voxel shading.
    """
    rune_rgb = (0.533, 0.133, 0.800, 1.0) if (set_idx % 4) == 3 else (0.851, 0.251, 0.078, 1.0)
    specs = [
        (f"Set{set_idx}_Mat_Iron", (0.122, 0.125, 0.141, 1.0), 0.85, 0.45, None, 0.0),
        (f"Set{set_idx}_Mat_Leather", (0.149, 0.110, 0.094, 1.0), 0.05, 0.84, None, 0.0),
        (f"Set{set_idx}_Mat_Brass", (0.431, 0.333, 0.169, 1.0), 0.80, 0.48, None, 0.0),
        (f"Set{set_idx}_Mat_RuneGlow", rune_rgb, 0.15, 0.28, rune_rgb, 2.2),
    ]
    mats: list[bpy.types.Material] = []
    for name, rgba, met, rough, em_rgba, em_str in specs:
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
            bsdf.inputs["Base Color"].default_value = rgba
            bsdf.inputs["Metallic"].default_value = met
            bsdf.inputs["Roughness"].default_value = rough
            if em_rgba is not None and "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = em_rgba
                bsdf.inputs["Emission Strength"].default_value = em_str
        mats.append(mat)
    return mats


class MicroVoxelBuilder:
    """
    Hyper-Detailed Ultra-Realistic Micro-Voxel Builder ported from the 'micro voxel' agent
    architecture (`VoxelPartBuilder`).
    Coordinate Mapping (Blender Z-up, -Y forward -> exports to Godot +Y up, +Z forward):
      - Grid `ix` = Right (+X in Blender & Godot): wx = origin.x + ix * voxel_size
      - Grid `iy` = Up (+Z in Blender, +Y in Godot): wz = origin.z + iy * voxel_size
      - Grid `iz` = Forward (-Y in Blender, +Z in Godot): wy = origin.y - iz * voxel_size
    """

    def __init__(
        self,
        name: str,
        voxel_size: float = 0.018,
        origin: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> None:
        self.name: str = name
        self.voxel_size: float = voxel_size
        self.origin: tuple[float, float, float] = origin
        # Maps (ix, iy, iz) -> (mat_idx, shade_bias, tint_b)
        self.voxels: dict[tuple[int, int, int], tuple[int, float, float]] = {}

    def set_voxel(
        self,
        ix: int,
        iy: int,
        iz: int,
        mat_idx: int = 0,
        shade_bias: float = 1.0,
        tint_b: float = 0.5,
    ) -> None:
        self.voxels[(int(ix), int(iy), int(iz))] = (int(mat_idx), float(shade_bias), float(tint_b))

    def carve_voxel(self, ix: int, iy: int, iz: int) -> None:
        self.voxels.pop((int(ix), int(iy), int(iz)), None)

    def get_world_center(self, ix: int, iy: int, iz: int) -> tuple[float, float, float]:
        s = self.voxel_size
        ox, oy, oz = self.origin
        return (
            ox + (ix + 0.5) * s,
            oy - (iz + 0.5) * s,
            oz + (iy + 0.5) * s,
        )

    def set_world_voxel(
        self,
        wx: float,
        wy: float,
        wz: float,
        mat_idx: int = 0,
        shade_bias: float = 1.0,
        tint_b: float = 0.5,
    ) -> None:
        s = self.voxel_size
        ox, oy, oz = self.origin
        ix = int(math.floor((wx - ox) / s))
        iz = int(math.floor((oy - wy) / s))
        iy = int(math.floor((wz - oz) / s))
        self.voxels[(ix, iy, iz)] = (int(mat_idx), float(shade_bias), float(tint_b))

    def fill_box(
        self,
        x0: int,
        x1: int,
        y0: int,
        y1: int,
        z0: int,
        z1: int,
        mat_idx: int = 0,
        shade_bias: float = 1.0,
        tint_b: float = 0.5,
    ) -> None:
        for ix in range(min(x0, x1), max(x0, x1) + 1):
            for iy in range(min(y0, y1), max(y0, y1) + 1):
                for iz in range(min(z0, z1), max(z0, z1) + 1):
                    self.voxels[(ix, iy, iz)] = (mat_idx, shade_bias, tint_b)

    def carve_box(self, x0: int, x1: int, y0: int, y1: int, z0: int, z1: int) -> None:
        for ix in range(min(x0, x1), max(x0, x1) + 1):
            for iy in range(min(y0, y1), max(y0, y1) + 1):
                for iz in range(min(z0, z1), max(z0, z1) + 1):
                    self.voxels.pop((ix, iy, iz), None)

    def hollow_box(
        self,
        x0: int,
        x1: int,
        y0: int,
        y1: int,
        z0: int,
        z1: int,
        mat_idx: int = 0,
        shade_bias: float = 1.0,
        tint_b: float = 0.5,
        wall: int = 1,
    ) -> None:
        xa, xb = min(x0, x1), max(x0, x1)
        ya, yb = min(y0, y1), max(y0, y1)
        za, zb = min(z0, z1), max(z0, z1)
        for ix in range(xa, xb + 1):
            for iy in range(ya, yb + 1):
                for iz in range(za, zb + 1):
                    if (
                        ix < xa + wall or ix > xb - wall
                        or iy < ya + wall or iy > yb - wall
                        or iz < za + wall or iz > zb - wall
                    ):
                        self.voxels[(ix, iy, iz)] = (mat_idx, shade_bias, tint_b)

    def add_3d_chain(
        self,
        p0: tuple[int, int, int],
        p1: tuple[int, int, int],
        mat_idx: int = 0,
        sag_voxels: float = 1.5,
    ) -> None:
        """Builds an interlocking 3D micro-voxel chain between two voxel coordinates."""
        dist = math.sqrt((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2 + (p1[2] - p0[2]) ** 2)
        steps = max(4, int(dist * 1.4))
        for i in range(steps + 1):
            t = i / float(steps)
            cx = int(round(p0[0] + (p1[0] - p0[0]) * t))
            cy = int(round(p0[1] + (p1[1] - p0[1]) * t - math.sin(t * math.pi) * sag_voxels))
            cz = int(round(p0[2] + (p1[2] - p0[2]) * t))
            self.set_voxel(cx, cy, cz, mat_idx, 1.0, 0.55)
            if i % 2 == 0:
                self.set_voxel(cx, cy + 1, cz, mat_idx, 0.94, 0.50)
            else:
                self.set_voxel(cx + (1 if cx >= 0 else -1), cy, cz, mat_idx, 0.92, 0.48)

    def add_shoulder_candle(
        self,
        cx: int,
        base_y: int,
        cz: int,
        height: int = 5,
        wax_mat: int = 1,
        flame_mat: int = 3,
    ) -> None:
        """
        Spawns a signature 'micro voxel' melted wax candle with cascading wax drips
        and a multi-stepped glowing voxel flame on top.
        """
        for dy in range(height):
            for dx in (0, 1):
                for dz in (0, 1):
                    self.set_voxel(cx + dx, base_y + dy, cz + dz, wax_mat, 1.02, 0.92)
        # Cascading melted wax drips down the sides
        self.set_voxel(cx - 1, base_y, cz, wax_mat, 0.96, 0.88)
        self.set_voxel(cx + 2, base_y, cz + 1, wax_mat, 0.96, 0.88)
        self.set_voxel(cx, base_y - 1, cz + 2, wax_mat, 0.94, 0.86)
        self.set_voxel(cx + 1, base_y + 1, cz - 1, wax_mat, 0.95, 0.88)
        # Multi-stepped glowing voxel flame (base + tall bright core)
        fy = base_y + height
        self.set_voxel(cx, fy, cz, flame_mat, 1.0, 0.70)
        self.set_voxel(cx + 1, fy, cz, flame_mat, 1.0, 0.70)
        self.set_voxel(cx, fy, cz + 1, flame_mat, 1.0, 0.70)
        self.set_voxel(cx, fy + 1, cz, flame_mat, 1.05, 0.90)
        self.set_voxel(cx, fy + 2, cz, flame_mat, 1.08, 1.00)

    def add_3d_buckle(
        self,
        cx: int,
        cy: int,
        cz: int,
        half_w: int = 2,
        half_h: int = 2,
        frame_mat: int = 2,
        pin_mat: int = 0,
    ) -> None:
        """Builds a 3D hollow iron/brass belt buckle protruding 1 voxel forward (+Z)."""
        for dx in range(-half_w, half_w + 1):
            for dy in range(-half_h, half_h + 1):
                if abs(dx) == half_w or abs(dy) == half_h:
                    self.set_voxel(cx + dx, cy + dy, cz, frame_mat, 1.02, 0.65)
                elif dx == 0 and dy == 0:
                    self.set_voxel(cx, cy, cz, pin_mat, 0.98, 0.55)

    def enforce_inner_clearance(self, clearance_predicate) -> int:
        """
        Removes any voxel whose world-space 8 corners or center violate `clearance_predicate(wx, wy, wz)`.
        Returns number of carved interior voxels.
        """
        s = self.voxel_size
        ox, oy, oz = self.origin
        to_remove: list[tuple[int, int, int]] = []
        for (ix, iy, iz) in self.voxels.keys():
            wx0 = ox + ix * s
            wx1 = wx0 + s
            wy0 = oy - (iz + 1) * s
            wy1 = oy - iz * s
            wz0 = oz + iy * s
            wz1 = wz0 + s
            violated = False
            for wx in (wx0, (wx0 + wx1) * 0.5, wx1):
                for wy in (wy0, (wy0 + wy1) * 0.5, wy1):
                    for wz in (wz0, (wz0 + wz1) * 0.5, wz1):
                        if clearance_predicate(wx, wy, wz):
                            violated = True
                            break
                    if violated:
                        break
                if violated:
                    break
            if violated:
                to_remove.append((ix, iy, iz))
        for k in to_remove:
            del self.voxels[k]
        return len(to_remove)

    def build_bmesh(self) -> bmesh.types.BMesh:
        """
        Builds a clean manifold-cull BMesh with internal 6-neighbor face culling,
        26-neighborhood Cavity AO, directional face shading, and deterministic hash jitter.
        """
        bm = bmesh.new()
        color_layer = bm.loops.layers.color.new("Col")
        s = self.voxel_size
        ox, oy, oz = self.origin

        if not self.voxels:
            return bm

        ys = [k[1] for k in self.voxels.keys()]
        iy_min, iy_max = min(ys), max(ys)
        iy_span = max(1.0, float(iy_max - iy_min))

        # 6 orthogonal neighbor directions in (ix, iy, iz) grid space
        # Recall: wx = ox + ix*s (+X), wy = oy - (iz+1)*s .. oy - iz*s (-Y is +iz), wz = oz + iy*s (+Z is +iy)
        dirs = [
            ((1, 0, 0), ((1, 0, 1), (1, 0, 0), (1, 1, 0), (1, 1, 1)), 0.93),     # +X Right
            ((-1, 0, 0), ((0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)), 0.93),    # -X Left
            ((0, 1, 0), ((0, 1, 1), (1, 1, 1), (1, 1, 0), (0, 1, 0)), 1.06),     # +Y Up (+Z Blender)
            ((0, -1, 0), ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)), 0.78),    # -Y Down (-Z Blender)
            ((0, 0, 1), ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)), 1.00),     # +Z Forward (-Y Blender)
            ((0, 0, -1), ((1, 0, 0), (0, 0, 0), (0, 1, 0), (1, 1, 0)), 0.96),    # -Z Back (+Y Blender)
        ]

        for (ix, iy, iz), (mat_idx, shade_bias, tint_b) in self.voxels.items():
            # Deterministic per-voxel hash jitter (±4%)
            rng_val = ((ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791)) & 0xFFFF
            jitter = ((rng_val / 65535.0) - 0.5) * 0.08

            # 26-neighborhood Cavity Ambient Occlusion
            occ_neighbors = 0
            for nx in (-1, 0, 1):
                for ny in (-1, 0, 1):
                    for nz in (-1, 0, 1):
                        if nx == 0 and ny == 0 and nz == 0:
                            continue
                        if (ix + nx, iy + ny, iz + nz) in self.voxels:
                            occ_neighbors += 1

            ao = 1.0 - (occ_neighbors / 26.0) * 0.30
            height_grad = min(1.0, max(0.74, 0.76 + ((iy - iy_min) / iy_span) * 0.24))
            # Outer stepped voxel rims get forged-edge highlight in COLOR.g
            edge_g = 0.84 if occ_neighbors <= 13 else 0.42

            for (dx, dy, dz), corners, dir_shade in dirs:
                if (ix + dx, iy + dy, iz + dz) in self.voxels:
                    continue

                verts = []
                for cx, cy, cz in corners:
                    wx = ox + (ix + cx) * s
                    wy = oy - (iz + cz) * s
                    wz = oz + (iy + cy) * s
                    verts.append(bm.verts.new((wx, wy, wz)))

                face = bm.faces.new((verts[0], verts[1], verts[2], verts[3]))
                face.material_index = mat_idx
                face.smooth = False

                val = max(0.45, min(1.0, height_grad * ao * shade_bias * dir_shade + jitter))
                if tint_b > 0.75:
                    # Warm candle wax / parchment / bone-ivory highlight
                    col_rgba = (min(1.0, val * 1.10), min(1.0, val * 1.04), min(1.0, val * 0.88), 1.0)
                elif tint_b < 0.45:
                    # Deep charcoal inner waistcoat / recessed cloth layer
                    col_rgba = (val * 0.78, val * 0.78, val * 0.82, 1.0)
                else:
                    col_rgba = (val, val, val, 1.0)
                for loop in face.loops:
                    loop[color_layer] = col_rgba

        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        return bm

    def build_mesh_object(
        self,
        mats: list[bpy.types.Material],
        parent: bpy.types.Object | None = None,
    ) -> bpy.types.Object:
        bm = self.build_bmesh()
        mesh = bpy.data.meshes.new(self.name + "_Mesh")
        bm.to_mesh(mesh)
        bm.free()

        for m in mats:
            mesh.materials.append(m)

        obj = bpy.data.objects.new(self.name, mesh)
        bpy.context.collection.objects.link(obj)
        if parent is not None:
            obj.parent = parent
        return obj



def make_weapon_pbr_material(
    name: str,
    base_rgb: tuple[float, float, float],
    roughness: float = 0.45,
    metallic: float = 0.85,
    emission_rgb: tuple[float, float, float] | None = None,
    emission_strength: float = 0.0,
    alpha: float = 1.0,
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat["_base_rgb"] = (float(base_rgb[0]), float(base_rgb[1]), float(base_rgb[2]))
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new(type="ShaderNodeOutputMaterial")
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    vcol = nodes.new(type="ShaderNodeVertexColor")
    vcol.layer_name = "Col"

    links.new(vcol.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic

    if alpha < 1.0 and "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = alpha
        if hasattr(mat, "blend_method"):
            mat.blend_method = 'BLEND'

    if emission_rgb is not None and emission_strength > 0.0:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*emission_rgb, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = emission_strength

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def create_weapon_voxel_palette() -> dict[str, bpy.types.Material]:
    return {
        "blued_steel": make_weapon_pbr_material("BluedSteel", (0.20, 0.22, 0.26), roughness=0.40, metallic=0.88),
        "gothic_steel": make_weapon_pbr_material("GothicPlateSteel", (0.28, 0.30, 0.35), roughness=0.42, metallic=0.88),
        "silver": make_weapon_pbr_material("OccultSilver", (0.72, 0.75, 0.80), roughness=0.32, metallic=0.92),
        "brass": make_weapon_pbr_material("TarnishedBrass", (0.68, 0.52, 0.25), roughness=0.42, metallic=0.86),
        "wrought_iron": make_weapon_pbr_material("WroughtIron", (0.16, 0.17, 0.19), roughness=0.48, metallic=0.85),
        "walnut": make_weapon_pbr_material("DarkOiledWalnut", (0.28, 0.15, 0.09), roughness=0.78, metallic=0.04),
        "leather": make_weapon_pbr_material("WeatheredLeather", (0.22, 0.14, 0.10), roughness=0.84, metallic=0.04),
        "bone": make_weapon_pbr_material("AgedBone", (0.74, 0.68, 0.56), roughness=0.76, metallic=0.04),
        "wax": make_weapon_pbr_material("CandleWax", (0.86, 0.78, 0.60), roughness=0.68, metallic=0.0),
        "bore": make_weapon_pbr_material("DarkBoreShadow", (0.03, 0.03, 0.04), roughness=0.96, metallic=0.0),
        "glass": make_weapon_pbr_material(
            "AmberLanternGlass",
            (1.0, 0.68, 0.28),
            roughness=0.15,
            metallic=0.05,
            emission_rgb=(1.0, 0.62, 0.22),
            emission_strength=0.6,
            alpha=0.24,
        ),
        "flame_outer": make_weapon_pbr_material(
            "EmissiveAmberFlame",
            (1.0, 0.55, 0.16),
            roughness=0.20,
            metallic=0.0,
            emission_rgb=(1.0, 0.48, 0.14),
            emission_strength=3.2,
        ),
        "flame_core": make_weapon_pbr_material(
            "EmissiveFlameCore",
            (1.0, 0.90, 0.52),
            roughness=0.12,
            metallic=0.0,
            emission_rgb=(1.0, 0.82, 0.38),
            emission_strength=5.4,
        ),
        "rune": make_weapon_pbr_material(
            "GlowingOccultRune",
            (0.96, 0.20, 0.32),
            roughness=0.25,
            metallic=0.10,
            emission_rgb=(1.0, 0.16, 0.28),
            emission_strength=3.6,
        ),
    }


class WeaponVoxelBuilder:
    """
    Hero Viewmodel Weapon & Lantern Micro-Voxel Builder.
    Blender Coordinate Convention (matching `tools/blender_build_fps_viewmodels.py` with `export_yup=True`):
      - `ix` = Right (+X in Blender -> +X in Godot): wx = ix * voxel_size
      - `iy` = Forward along barrel (+Y in Blender -> -Z Forward in Godot): wy = iy * voxel_size
      - `iz` = Up (+Z in Blender -> +Y Up in Godot): wz = iz * voxel_size
    """

    def __init__(
        self,
        name: str,
        voxel_size: float = 0.004,
        pivot_xyz: tuple[float, float, float] = (0.0, 0.0, 0.0),
        palette: dict[str, bpy.types.Material] | None = None,
    ) -> None:
        self.name: str = name
        self.voxel_size: float = voxel_size
        self.pivot_xyz: tuple[float, float, float] = pivot_xyz
        self.palette: dict[str, bpy.types.Material] = palette if palette is not None else {}
        self.voxels: dict[tuple[int, int, int], tuple[str, float]] = {}

    def set_voxel(self, ix: int, iy: int, iz: int, mat_key: str, shade_bias: float = 1.0) -> None:
        self.voxels[(int(ix), int(iy), int(iz))] = (mat_key, float(shade_bias))

    def carve_voxel(self, ix: int, iy: int, iz: int) -> None:
        self.voxels.pop((int(ix), int(iy), int(iz)), None)

    def set_world(self, wx: float, wy: float, wz: float, mat_key: str, shade_bias: float = 1.0) -> None:
        s = self.voxel_size
        self.set_voxel(int(round(wx / s)), int(round(wy / s)), int(round(wz / s)), mat_key, shade_bias)

    def fill_box(
        self,
        x0: int,
        x1: int,
        y0: int,
        y1: int,
        z0: int,
        z1: int,
        mat_key: str,
        shade_bias: float = 1.0,
    ) -> None:
        for ix in range(min(x0, x1), max(x0, x1) + 1):
            for iy in range(min(y0, y1), max(y0, y1) + 1):
                for iz in range(min(z0, z1), max(z0, z1) + 1):
                    self.voxels[(ix, iy, iz)] = (mat_key, shade_bias)

    def carve_box(self, x0: int, x1: int, y0: int, y1: int, z0: int, z1: int) -> None:
        for ix in range(min(x0, x1), max(x0, x1) + 1):
            for iy in range(min(y0, y1), max(y0, y1) + 1):
                for iz in range(min(z0, z1), max(z0, z1) + 1):
                    self.voxels.pop((ix, iy, iz), None)

    def fill_world_box(
        self,
        wx0: float,
        wx1: float,
        wy0: float,
        wy1: float,
        wz0: float,
        wz1: float,
        mat_key: str,
        shade_bias: float = 1.0,
    ) -> None:
        s = self.voxel_size
        self.fill_box(
            int(round(min(wx0, wx1) / s)),
            int(round(max(wx0, wx1) / s)),
            int(round(min(wy0, wy1) / s)),
            int(round(max(wy0, wy1) / s)),
            int(round(min(wz0, wz1) / s)),
            int(round(max(wz0, wz1) / s)),
            mat_key,
            shade_bias,
        )

    def carve_world_box(
        self,
        wx0: float,
        wx1: float,
        wy0: float,
        wy1: float,
        wz0: float,
        wz1: float,
    ) -> None:
        s = self.voxel_size
        self.carve_box(
            int(round(min(wx0, wx1) / s)),
            int(round(max(wx0, wx1) / s)),
            int(round(min(wy0, wy1) / s)),
            int(round(max(wy0, wy1) / s)),
            int(round(min(wz0, wz1) / s)),
            int(round(max(wz0, wz1) / s)),
        )

    def fill_cylinder_y(
        self,
        cx_w: float,
        cz_w: float,
        wy0: float,
        wy1: float,
        r_outer: float,
        r_inner: float = 0.0,
        mat_key: str = "blued_steel",
        shade_bias: float = 1.0,
        octagonal: bool = False,
    ) -> None:
        s = self.voxel_size
        iy0, iy1 = int(round(min(wy0, wy1) / s)), int(round(max(wy0, wy1) / s))
        ir = int(math.ceil(r_outer / s)) + 1
        icx, icz = int(round(cx_w / s)), int(round(cz_w / s))
        for iy in range(iy0, iy1 + 1):
            for dx in range(-ir, ir + 1):
                for dz in range(-ir, ir + 1):
                    wx = (icx + dx) * s - cx_w
                    wz = (icz + dz) * s - cz_w
                    if octagonal:
                        dist = max(abs(wx), abs(wz), (abs(wx) + abs(wz)) * 0.7071)
                    else:
                        dist = math.sqrt(wx * wx + wz * wz)
                    if r_inner <= dist <= r_outer:
                        self.voxels[(icx + dx, iy, icz + dz)] = (mat_key, shade_bias)

    def fill_cylinder_z(
        self,
        cx_w: float,
        cy_w: float,
        wz0: float,
        wz1: float,
        r_outer: float,
        r_inner: float = 0.0,
        mat_key: str = "wrought_iron",
        shade_bias: float = 1.0,
        octagonal: bool = False,
    ) -> None:
        s = self.voxel_size
        iz0, iz1 = int(round(min(wz0, wz1) / s)), int(round(max(wz0, wz1) / s))
        ir = int(math.ceil(r_outer / s)) + 1
        icx, icy = int(round(cx_w / s)), int(round(cy_w / s))
        for iz in range(iz0, iz1 + 1):
            for dx in range(-ir, ir + 1):
                for dy in range(-ir, ir + 1):
                    wx = (icx + dx) * s - cx_w
                    wy = (icy + dy) * s - cy_w
                    if octagonal:
                        dist = max(abs(wx), abs(wy), (abs(wx) + abs(wy)) * 0.7071)
                    else:
                        dist = math.sqrt(wx * wx + wy * wy)
                    if r_inner <= dist <= r_outer:
                        self.voxels[(icx + dx, icy + dy, iz)] = (mat_key, shade_bias)

    def fill_cylinder_x(
        self,
        cy_w: float,
        cz_w: float,
        wx0: float,
        wx1: float,
        r_outer: float,
        r_inner: float = 0.0,
        mat_key: str = "brass",
        shade_bias: float = 1.0,
    ) -> None:
        s = self.voxel_size
        ix0, ix1 = int(round(min(wx0, wx1) / s)), int(round(max(wx0, wx1) / s))
        ir = int(math.ceil(r_outer / s)) + 1
        icy, icz = int(round(cy_w / s)), int(round(cz_w / s))
        for ix in range(ix0, ix1 + 1):
            for dy in range(-ir, ir + 1):
                for dz in range(-ir, ir + 1):
                    wy = (icy + dy) * s - cy_w
                    wz = (icz + dz) * s - cz_w
                    dist = math.sqrt(wy * wy + wz * wz)
                    if r_inner <= dist <= r_outer:
                        self.voxels[(ix, icy + dy, icz + dz)] = (mat_key, shade_bias)

    def build_mesh_object(self, parent_obj: bpy.types.Object | None = None) -> bpy.types.Object:
        bm = bmesh.new()
        color_layer = bm.loops.layers.color.new("Col")
        s = self.voxel_size
        px, py, pz = self.pivot_xyz

        mat_keys = list(self.palette.keys())
        mat_index_map = {k: i for i, k in enumerate(mat_keys)}

        if self.voxels:
            zs = [k[2] for k in self.voxels.keys()]
            iz_min, iz_max = min(zs), max(zs)
            iz_span = max(1.0, float(iz_max - iz_min))

            # Outward-wound quad corners in right-handed (wx, wy, wz) where +ix=+X, +iy=+Y, +iz=+Z
            dirs = [
                ((1, 0, 0), ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)), 0.94),     # +X Right
                ((-1, 0, 0), ((0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1)), 0.94),    # -X Left
                ((0, 1, 0), ((1, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1)), 0.98),     # +Y Forward
                ((0, -1, 0), ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)), 0.96),    # -Y Rear
                ((0, 0, 1), ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)), 1.06),     # +Z Up
                ((0, 0, -1), ((0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0)), 0.80),    # -Z Down
            ]

            for (ix, iy, iz), (mat_key, shade_bias) in self.voxels.items():
                m_idx = mat_index_map.get(mat_key, 0)
                mat_obj = self.palette[mat_keys[m_idx]]
                base_rgb = mat_obj.get("_base_rgb", (0.5, 0.5, 0.5))

                rng_val = ((ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791)) & 0xFFFF
                jitter = ((rng_val / 65535.0) - 0.5) * 0.08

                occ_neighbors = 0
                for nx in (-1, 0, 1):
                    for ny in (-1, 0, 1):
                        for nz in (-1, 0, 1):
                            if nx == 0 and ny == 0 and nz == 0:
                                continue
                            if (ix + nx, iy + ny, iz + nz) in self.voxels:
                                occ_neighbors += 1

                ao = 1.0 - (occ_neighbors / 26.0) * 0.28
                height_grad = min(1.0, max(0.76, 0.78 + ((iz - iz_min) / iz_span) * 0.22))

                for (dx, dy, dz), corners, dir_shade in dirs:
                    if (ix + dx, iy + dy, iz + dz) in self.voxels:
                        continue

                    verts = []
                    for cx, cy, cz in corners:
                        wx = (ix + cx - 0.5) * s - px
                        wy = (iy + cy - 0.5) * s - py
                        wz = (iz + cz - 0.5) * s - pz
                        verts.append(bm.verts.new((wx, wy, wz)))

                    face = bm.faces.new((verts[0], verts[1], verts[2], verts[3]))
                    face.material_index = m_idx
                    face.smooth = False

                    val = max(0.48, min(1.08, height_grad * ao * shade_bias * dir_shade + jitter))
                    col = (
                        max(0.0, min(1.0, base_rgb[0] * val)),
                        max(0.0, min(1.0, base_rgb[1] * val)),
                        max(0.0, min(1.0, base_rgb[2] * val)),
                        1.0,
                    )
                    for loop in face.loops:
                        loop[color_layer] = col

        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.00005)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        mesh = bpy.data.meshes.new(self.name + "_Mesh")
        bm.to_mesh(mesh)
        bm.free()

        for k in mat_keys:
            mesh.materials.append(self.palette[k])

        obj = bpy.data.objects.new(self.name, mesh)
        bpy.context.collection.objects.link(obj)
        obj.location = self.pivot_xyz
        if parent_obj is not None:
            obj.parent = parent_obj
        return obj


# ==============================================================================
# ENVIRONMENT & ARCHITECTURAL MICRO-VOXEL SYSTEM (Milestone 0)
# ==============================================================================


def make_environment_pbr_material(
    name: str,
    base_rgb: tuple[float, float, float],
    roughness: float = 0.88,
    metallic: float = 0.0,
    emission_rgb: tuple[float, float, float] | None = None,
    emission_strength: float = 0.0,
    alpha: float = 1.0,
) -> bpy.types.Material:
    """Creates a standard environment PBR material with Vertex Color ('Col') driving Base Color."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat["_base_rgb"] = (float(base_rgb[0]), float(base_rgb[1]), float(base_rgb[2]))
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new(type="ShaderNodeOutputMaterial")
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    vcol = nodes.new(type="ShaderNodeVertexColor")
    vcol.layer_name = "Col"

    links.new(vcol.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic

    if alpha < 1.0 and "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = alpha
        if hasattr(mat, "blend_method"):
            mat.blend_method = "BLEND"

    if emission_rgb is not None and emission_strength > 0.0:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*emission_rgb, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = emission_strength

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def create_environment_voxel_palette() -> dict[str, bpy.types.Material]:
    """
    Returns the unified 23-material Gothic environment palette matching
    GrimdarkMaterialLibrary.get_material_for_name() in scripts/environment/material_library.gd.
    """
    return {
        "weathered_stone": make_environment_pbr_material("WeatheredAshlarStone", (0.32, 0.30, 0.28), roughness=0.92, metallic=0.0),
        "cobble_flagstone": make_environment_pbr_material("RoughCobbleFlagstone", (0.24, 0.23, 0.22), roughness=0.72, metallic=0.0),
        "carved_stone_trim": make_environment_pbr_material("CarvedStoneTrim", (0.36, 0.34, 0.32), roughness=0.84, metallic=0.0),
        "dark_slate_roof": make_environment_pbr_material("DarkSlateRoof", (0.18, 0.19, 0.22), roughness=0.89, metallic=0.0),
        "dirty_plaster": make_environment_pbr_material("DirtyPlaster", (0.38, 0.35, 0.31), roughness=0.93, metallic=0.0),
        "charred_timber": make_environment_pbr_material("RottedCharredTimber", (0.20, 0.14, 0.10), roughness=0.88, metallic=0.0),
        "wrought_iron": make_environment_pbr_material("TarnishedWroughtIron", (0.14, 0.14, 0.16), roughness=0.48, metallic=0.85),
        "bronze": make_environment_pbr_material("TarnishedBronze", (0.28, 0.23, 0.14), roughness=0.46, metallic=0.85),
        "bone": make_environment_pbr_material("AgedBone", (0.62, 0.57, 0.46), roughness=0.88, metallic=0.0),
        "wax": make_environment_pbr_material("CandleWax", (0.76, 0.68, 0.50), roughness=0.56, metallic=0.0),
        "candle_flame": make_environment_pbr_material("CandleFlameGlow", (1.0, 0.72, 0.24), roughness=0.15, metallic=0.0, emission_rgb=(1.0, 0.65, 0.18), emission_strength=4.2),
        "lead_glass": make_environment_pbr_material("LeadGlassWindow", (0.18, 0.22, 0.25), roughness=0.20, metallic=0.10, alpha=0.75),
        "occult_rune": make_environment_pbr_material("GlowingOccultRune", (0.92, 0.50, 1.0), roughness=0.30, metallic=0.0, emission_rgb=(0.88, 0.42, 1.0), emission_strength=2.6),
        "green_bile": make_environment_pbr_material("SicklyGreenBile", (0.42, 0.90, 0.30), roughness=0.24, metallic=0.0, emission_rgb=(0.45, 0.95, 0.35), emission_strength=2.4),
        "blue_soul": make_environment_pbr_material("FrozenBlueSoul", (0.35, 0.70, 1.0), roughness=0.26, metallic=0.0, emission_rgb=(0.35, 0.65, 1.0), emission_strength=2.6),
        "crimson": make_environment_pbr_material("AbyssalCrimson", (0.95, 0.12, 0.15), roughness=0.28, metallic=0.0, emission_rgb=(1.0, 0.15, 0.18), emission_strength=3.0),
        "water": make_environment_pbr_material("DarkCisternWater", (0.05, 0.09, 0.12), roughness=0.14, metallic=0.15),
        "containment_hull": make_environment_pbr_material("DarkContainmentHullStone", (0.06, 0.06, 0.08), roughness=0.95, metallic=0.0),
        "moor_grass": make_environment_pbr_material("TerrainMoorGrass", (0.15, 0.17, 0.12), roughness=0.94, metallic=0.0),
        "mud_path": make_environment_pbr_material("TerrainMudPath", (0.18, 0.15, 0.12), roughness=0.91, metallic=0.0),
        "cliff_stone": make_environment_pbr_material("TerrainCliffStone", (0.24, 0.23, 0.24), roughness=0.92, metallic=0.0),
        "silver": make_environment_pbr_material("OccultSilver", (0.58, 0.60, 0.64), roughness=0.36, metallic=0.88),
        "gold": make_environment_pbr_material("ConsecratedGold", (1.0, 0.78, 0.24), roughness=0.20, metallic=0.35, emission_rgb=(1.0, 0.72, 0.18), emission_strength=2.8),
    }


class EnvironmentVoxelBuilder:
    """
    Blender World-Space Micro-Voxel Builder for Gothic Architecture & Environment Kits.
    Blender Coordinate Convention (matching export_yup=True):
      - `ix` = +X in Blender -> +X in Godot
      - `iy` = +Y in Blender -> -Z (Forward) in Godot
      - `iz` = +Z in Blender -> +Y (Up) in Godot
    """

    def __init__(
        self,
        name: str,
        voxel_size: float = 0.04,
        palette: dict[str, bpy.types.Material] | None = None,
        pivot_xyz: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> None:
        self.name: str = name
        self.voxel_size: float = voxel_size
        self.palette: dict[str, bpy.types.Material] = palette if palette is not None else {}
        self.pivot_xyz: tuple[float, float, float] = pivot_xyz
        self.voxels: dict[tuple[int, int, int], tuple[str, float]] = {}

    def set_voxel(self, ix: int, iy: int, iz: int, mat_key: str, shade_bias: float = 1.0) -> None:
        self.voxels[(int(ix), int(iy), int(iz))] = (mat_key, float(shade_bias))

    def carve_voxel(self, ix: int, iy: int, iz: int) -> None:
        self.voxels.pop((int(ix), int(iy), int(iz)), None)

    def set_world(self, wx: float, wy: float, wz: float, mat_key: str, shade_bias: float = 1.0) -> None:
        s = self.voxel_size
        self.set_voxel(int(round(wx / s)), int(round(wy / s)), int(round(wz / s)), mat_key, shade_bias)

    def fill_box(
        self,
        x0: int,
        x1: int,
        y0: int,
        y1: int,
        z0: int,
        z1: int,
        mat_key: str,
        shade_bias: float = 1.0,
    ) -> None:
        for ix in range(min(x0, x1), max(x0, x1) + 1):
            for iy in range(min(y0, y1), max(y0, y1) + 1):
                for iz in range(min(z0, z1), max(z0, z1) + 1):
                    self.voxels[(ix, iy, iz)] = (mat_key, float(shade_bias))

    def carve_box(self, x0: int, x1: int, y0: int, y1: int, z0: int, z1: int) -> None:
        for ix in range(min(x0, x1), max(x0, x1) + 1):
            for iy in range(min(y0, y1), max(y0, y1) + 1):
                for iz in range(min(z0, z1), max(z0, z1) + 1):
                    self.voxels.pop((ix, iy, iz), None)

    def fill_world_box(
        self,
        x0: float,
        x1: float,
        y0: float,
        y1: float,
        z0: float,
        z1: float,
        mat_key: str,
        shade_bias: float = 1.0,
    ) -> None:
        s = self.voxel_size
        self.fill_box(
            int(round(min(x0, x1) / s)),
            int(round(max(x0, x1) / s)),
            int(round(min(y0, y1) / s)),
            int(round(max(y0, y1) / s)),
            int(round(min(z0, z1) / s)),
            int(round(max(z0, z1) / s)),
            mat_key,
            shade_bias,
        )

    def carve_world_box(
        self,
        x0: float,
        x1: float,
        y0: float,
        y1: float,
        z0: float,
        z1: float,
    ) -> None:
        s = self.voxel_size
        self.carve_box(
            int(round(min(x0, x1) / s)),
            int(round(max(x0, x1) / s)),
            int(round(min(y0, y1) / s)),
            int(round(max(y0, y1) / s)),
            int(round(min(z0, z1) / s)),
            int(round(max(z0, z1) / s)),
        )

    def fill_world_cylinder_z(
        self,
        cx_w: float,
        cy_w: float,
        wz0: float,
        wz1: float,
        r_outer: float,
        r_inner: float = 0.0,
        mat_key: str = "weathered_stone",
        shade_bias: float = 1.0,
        octagonal: bool = False,
    ) -> None:
        s = self.voxel_size
        iz0, iz1 = int(round(min(wz0, wz1) / s)), int(round(max(wz0, wz1) / s))
        ir = int(math.ceil(r_outer / s)) + 1
        icx, icy = int(round(cx_w / s)), int(round(cy_w / s))
        for iz in range(iz0, iz1 + 1):
            for dx in range(-ir, ir + 1):
                for dy in range(-ir, ir + 1):
                    wx = (icx + dx) * s - cx_w
                    wy = (icy + dy) * s - cy_w
                    if octagonal:
                        dist = max(abs(wx), abs(wy), (abs(wx) + abs(wy)) * 0.7071)
                    else:
                        dist = math.sqrt(wx * wx + wy * wy)
                    if r_inner <= dist <= r_outer:
                        self.voxels[(icx + dx, icy + dy, iz)] = (mat_key, float(shade_bias))

    def fill_world_cylinder_y(
        self,
        cx_w: float,
        cz_w: float,
        wy0: float,
        wy1: float,
        r_outer: float,
        r_inner: float = 0.0,
        mat_key: str = "weathered_stone",
        shade_bias: float = 1.0,
        octagonal: bool = False,
    ) -> None:
        s = self.voxel_size
        iy0, iy1 = int(round(min(wy0, wy1) / s)), int(round(max(wy0, wy1) / s))
        ir = int(math.ceil(r_outer / s)) + 1
        icx, icz = int(round(cx_w / s)), int(round(cz_w / s))
        for iy in range(iy0, iy1 + 1):
            for dx in range(-ir, ir + 1):
                for dz in range(-ir, ir + 1):
                    wx = (icx + dx) * s - cx_w
                    wz = (icz + dz) * s - cz_w
                    if octagonal:
                        dist = max(abs(wx), abs(wz), (abs(wx) + abs(wz)) * 0.7071)
                    else:
                        dist = math.sqrt(wx * wx + wz * wz)
                    if r_inner <= dist <= r_outer:
                        self.voxels[(icx + dx, iy, icz + dz)] = (mat_key, float(shade_bias))

    def fill_world_cylinder_x(
        self,
        cy_w: float,
        cz_w: float,
        wx0: float,
        wx1: float,
        r_outer: float,
        r_inner: float = 0.0,
        mat_key: str = "weathered_stone",
        shade_bias: float = 1.0,
        octagonal: bool = False,
    ) -> None:
        s = self.voxel_size
        ix0, ix1 = int(round(min(wx0, wx1) / s)), int(round(max(wx0, wx1) / s))
        ir = int(math.ceil(r_outer / s)) + 1
        icy, icz = int(round(cy_w / s)), int(round(cz_w / s))
        for ix in range(ix0, ix1 + 1):
            for dy in range(-ir, ir + 1):
                for dz in range(-ir, ir + 1):
                    wy = (icy + dy) * s - cy_w
                    wz = (icz + dz) * s - cz_w
                    if octagonal:
                        dist = max(abs(wy), abs(wz), (abs(wy) + abs(wz)) * 0.7071)
                    else:
                        dist = math.sqrt(wy * wy + wz * wz)
                    if r_inner <= dist <= r_outer:
                        self.voxels[(ix, icy + dy, icz + dz)] = (mat_key, float(shade_bias))

    def carve_world_cylinder_z(
        self,
        cx_w: float,
        cy_w: float,
        wz0: float,
        wz1: float,
        r_outer: float,
    ) -> None:
        s = self.voxel_size
        iz0, iz1 = int(round(min(wz0, wz1) / s)), int(round(max(wz0, wz1) / s))
        ir = int(math.ceil(r_outer / s)) + 1
        icx, icy = int(round(cx_w / s)), int(round(cy_w / s))
        for iz in range(iz0, iz1 + 1):
            for dx in range(-ir, ir + 1):
                for dy in range(-ir, ir + 1):
                    wx = (icx + dx) * s - cx_w
                    wy = (icy + dy) * s - cy_w
                    if math.sqrt(wx * wx + wy * wy) <= r_outer:
                        self.voxels.pop((icx + dx, icy + dy, iz), None)

    def carve_pointed_arch(
        self,
        cx: float,
        cy: float,
        base_z: float,
        spring_z: float,
        peak_z: float,
        span_w: float,
        depth_y: float,
    ) -> None:
        s = self.voxel_size
        half_w = span_w * 0.5
        apex_h = peak_z - spring_z
        if apex_h <= 0.001 or half_w <= 0.001:
            return
        c_offset = (apex_h * apex_h - half_w * half_w) / (2.0 * half_w)
        r = half_w + c_offset

        iy0 = int(round((cy - depth_y * 0.5) / s))
        iy1 = int(round((cy + depth_y * 0.5) / s))
        iz0 = int(round(base_z / s))
        iz1 = int(round(peak_z / s))

        for iz in range(iz0, iz1 + 1):
            wz = iz * s
            if wz <= spring_z:
                cur_hw = half_w
            elif wz <= peak_z:
                dz = wz - spring_z
                cur_hw = max(0.0, math.sqrt(max(0.0, r * r - dz * dz)) - c_offset)
            else:
                cur_hw = 0.0

            cur_ix0 = int(round((cx - cur_hw) / s))
            cur_ix1 = int(round((cx + cur_hw) / s))
            for ix in range(cur_ix0, cur_ix1 + 1):
                for iy in range(iy0, iy1 + 1):
                    self.voxels.pop((ix, iy, iz), None)

    def fill_pointed_arch(
        self,
        cx: float,
        cy: float,
        base_z: float,
        spring_z: float,
        peak_z: float,
        span_w: float,
        depth_y: float,
        wall_thick: float,
        mat_key: str = "weathered_stone",
        shade_bias: float = 1.0,
    ) -> None:
        s = self.voxel_size
        half_w = span_w * 0.5
        apex_h = peak_z - spring_z
        if apex_h <= 0.001 or half_w <= 0.001:
            return
        c_offset_in = (apex_h * apex_h - half_w * half_w) / (2.0 * half_w)
        r_in = half_w + c_offset_in

        half_w_out = half_w + wall_thick
        apex_h_out = apex_h + wall_thick
        peak_z_out = peak_z + wall_thick
        c_offset_out = (apex_h_out * apex_h_out - half_w_out * half_w_out) / (2.0 * half_w_out)
        r_out = half_w_out + c_offset_out

        iy0 = int(round((cy - depth_y * 0.5) / s))
        iy1 = int(round((cy + depth_y * 0.5) / s))
        iz0 = int(round(base_z / s))
        iz1 = int(round(peak_z_out / s))

        for iz in range(iz0, iz1 + 1):
            wz = iz * s
            if wz <= spring_z:
                hw_in = half_w
            elif wz <= peak_z:
                dz_in = wz - spring_z
                hw_in = max(0.0, math.sqrt(max(0.0, r_in * r_in - dz_in * dz_in)) - c_offset_in)
            else:
                hw_in = 0.0

            if wz <= spring_z:
                hw_out = half_w_out
            elif wz <= peak_z_out:
                dz_out = wz - spring_z
                hw_out = max(0.0, math.sqrt(max(0.0, r_out * r_out - dz_out * dz_out)) - c_offset_out)
            else:
                hw_out = 0.0

            ix0 = int(round((cx - hw_out) / s))
            ix1 = int(round((cx + hw_out) / s))
            for ix in range(ix0, ix1 + 1):
                wx = ix * s
                dist_x = abs(wx - cx)
                if dist_x <= hw_out:
                    if wz <= peak_z and dist_x < hw_in:
                        continue
                    for iy in range(iy0, iy1 + 1):
                        self.voxels[(ix, iy, iz)] = (mat_key, float(shade_bias))

    def fill_world_stairs_y(
        self,
        x0: float,
        x1: float,
        y0: float,
        y1: float,
        z0: float,
        z1: float,
        num_steps: int,
        mat_key: str = "cobble_flagstone",
        shade_bias: float = 1.0,
    ) -> None:
        if num_steps <= 0:
            return
        dy = (y1 - y0) / float(num_steps)
        dz = (z1 - z0) / float(num_steps)
        for i in range(num_steps):
            step_y0 = y0 + i * dy
            step_y1 = y1
            step_z0 = z0
            step_z1 = z0 + (i + 1) * dz
            self.fill_world_box(x0, x1, step_y0, step_y1, step_z0, step_z1, mat_key, shade_bias)

    def build_bmesh(self) -> bmesh.types.BMesh:
        """
        Builds a manifold-cull BMesh with internal 6-neighbor face culling,
        26-neighborhood Cavity AO (ao = 1.0 - (occ / 26.0) * 0.28),
        directional face shading, and deterministic +-4% hash jitter.
        """
        bm = bmesh.new()
        color_layer = bm.loops.layers.color.new("Col")
        s = self.voxel_size
        px, py, pz = self.pivot_xyz

        mat_keys = list(self.palette.keys())
        mat_index_map = {k: i for i, k in enumerate(mat_keys)}

        if self.voxels:
            zs = [k[2] for k in self.voxels.keys()]
            iz_min, iz_max = min(zs), max(zs)
            iz_span = max(1.0, float(iz_max - iz_min))

            # 6 orthogonal directions in Blender right-handed coords (+X right, +Y forward/north, +Z up)
            dirs = [
                ((1, 0, 0), ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)), 0.94),     # +X Right
                ((-1, 0, 0), ((0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1)), 0.94),    # -X Left
                ((0, 1, 0), ((1, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1)), 0.98),     # +Y North
                ((0, -1, 0), ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)), 0.96),    # -Y South
                ((0, 0, 1), ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)), 1.06),     # +Z Up
                ((0, 0, -1), ((0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0)), 0.80),    # -Z Down
            ]

            for (ix, iy, iz), (mat_key, shade_bias) in self.voxels.items():
                # Fast check: if all 6 orthogonal neighbors exist, this voxel is completely enclosed
                has_exposed = False
                for (dx, dy, dz), _, _ in dirs:
                    if (ix + dx, iy + dy, iz + dz) not in self.voxels:
                        has_exposed = True
                        break
                if not has_exposed:
                    continue

                if mat_key in mat_index_map:
                    m_idx = mat_index_map[mat_key]
                    mat_obj = self.palette[mat_key]
                    base_rgb = mat_obj.get("_base_rgb", (0.5, 0.5, 0.5))
                else:
                    m_idx = 0
                    base_rgb = (0.5, 0.5, 0.5)

                rng_val = ((ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791)) & 0xFFFF
                jitter = ((rng_val / 65535.0) - 0.5) * 0.08  # +-4%

                # 26-neighborhood Cavity Ambient Occlusion
                occ_neighbors = 0
                for nx in (-1, 0, 1):
                    for ny in (-1, 0, 1):
                        for nz in (-1, 0, 1):
                            if nx == 0 and ny == 0 and nz == 0:
                                continue
                            if (ix + nx, iy + ny, iz + nz) in self.voxels:
                                occ_neighbors += 1

                ao = 1.0 - (occ_neighbors / 26.0) * 0.28
                height_grad = min(1.0, max(0.76, 0.78 + ((iz - iz_min) / iz_span) * 0.22))

                for (dx, dy, dz), corners, dir_shade in dirs:
                    if (ix + dx, iy + dy, iz + dz) in self.voxels:
                        continue

                    verts = []
                    for cx, cy, cz in corners:
                        wx = (ix + cx - 0.5) * s - px
                        wy = (iy + cy - 0.5) * s - py
                        wz = (iz + cz - 0.5) * s - pz
                        verts.append(bm.verts.new((wx, wy, wz)))

                    face = bm.faces.new((verts[0], verts[1], verts[2], verts[3]))
                    face.material_index = m_idx
                    face.smooth = False

                    val = max(0.60, min(1.00, height_grad * ao * shade_bias * dir_shade + jitter))
                    col = (val, val, val, 1.0)
                    for loop in face.loops:
                        loop[color_layer] = col

            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.00005)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        return bm

    def build_mesh_object(self, parent_obj: bpy.types.Object | None = None) -> bpy.types.Object:
        """Constructs and links the final bpy.types.Object with assigned materials."""
        bm = self.build_bmesh()
        mesh = bpy.data.meshes.new(self.name + "_Mesh")
        bm.to_mesh(mesh)
        bm.free()

        mat_keys = list(self.palette.keys())
        for k in mat_keys:
            mesh.materials.append(self.palette[k])

        obj = bpy.data.objects.new(self.name, mesh)
        bpy.context.collection.objects.link(obj)
        obj.location = self.pivot_xyz
        if parent_obj is not None:
            obj.parent = parent_obj
        return obj


def export_environment_glb(filepath: str) -> None:
    """Exports active Blender scene to GLB with required glTF 2.0 flags."""
    import os
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format="GLB",
        export_apply=False,
        export_yup=True,
        export_attributes=True,
    )
    print(f"[MicroVoxelEnvironment] Exported -> {filepath}")
