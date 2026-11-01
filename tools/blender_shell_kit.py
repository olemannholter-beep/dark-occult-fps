import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Euler


def make_gothic_preset_materials(set_idx: int) -> list[bpy.types.Material]:
    """
    Returns the 4 dark gothic PBR materials wired with Vertex Color 'Col':
      0: Blackened Iron (#1f2024, metallic 0.85, roughness 0.45)
      1: Cured Stalker Leather (#261c18, metallic 0.05, roughness 0.82)
      2: Tarnished Synod Brass (#6e552b, metallic 0.80, roughness 0.50, zero emission)
      3: Cinder (#d94014) or Abyssal (#8822cc) Runes (recessed accents only, energy 2.0)
    """
    rune_col = (0.533, 0.133, 0.800, 1.0) if set_idx == 3 else (0.851, 0.251, 0.078, 1.0)
    specs = [
        (f"Set{set_idx}_BlackenedIron", (0.122, 0.125, 0.141, 1.0), 0.85, 0.45, None, 0.0),
        (f"Set{set_idx}_CuredStalkerLeather", (0.149, 0.110, 0.094, 1.0), 0.05, 0.82, None, 0.0),
        (f"Set{set_idx}_TarnishedSynodBrass", (0.431, 0.333, 0.169, 1.0), 0.80, 0.50, None, 0.0),
        (f"Set{set_idx}_RecessedRunes", rune_col, 0.15, 0.30, rune_col, 2.0),
    ]
    mats: list[bpy.types.Material] = []
    for name, bcol, met, rough, em_col, em_str in specs:
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        bsdf = nodes.get("Principled BSDF") or nodes.new(type="ShaderNodeBsdfPrincipled")
        vcol = nodes.new(type="ShaderNodeVertexColor")
        vcol.layer_name = "Col"
        mix = nodes.new(type="ShaderNodeMix")
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs[0].default_value = 1.0
        mix.inputs[6].default_value = bcol
        links.new(vcol.outputs["Color"], mix.inputs[7])
        links.new(mix.outputs[2], bsdf.inputs["Base Color"])
        bsdf.inputs["Metallic"].default_value = met
        bsdf.inputs["Roughness"].default_value = rough
        if em_col is not None and em_str > 0.0:
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = em_col
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = em_str
        mats.append(mat)
    return mats


def bake_ao_and_curvature_vertex_colors(
    obj: bpy.types.Object,
    z_min: float = -0.5,
    z_max: float = 1.8,
) -> None:
    """
    Bakes per-vertex Crevice Ambient Occlusion into COLOR.r and Forged Edge Curvature into COLOR.g:
      - R channel (AO): 0.38..0.55 in concave crevices under straps/lames, 0.85..0.98 on exposed plates
      - G channel (Curvature): 0.90..1.00 on sharp convex bevel edges, 0.50 on flat plates, 0.25 in recesses
      - B channel: vertical ground-soot gradient (0.60 at base -> 0.95 at top)
    """
    mesh = obj.data
    if not isinstance(mesh, bpy.types.Mesh):
        return

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    ao_map: dict[int, float] = {}
    curv_map: dict[int, float] = {}
    soot_map: dict[int, float] = {}
    z_span = max(0.2, z_max - z_min)

    for v in bm.verts:
        signed_angles: list[float] = []
        unsigned_angles: list[float] = []
        for e in v.link_edges:
            if len(e.link_faces) == 2:
                try:
                    s_ang = e.calc_face_angle_signed(0.0)
                except ValueError:
                    s_ang = 0.0
                u_ang = e.calc_face_angle(0.0)
                signed_angles.append(s_ang)
                unsigned_angles.append(u_ang)

        min_s = min(signed_angles) if signed_angles else 0.0
        max_s = max(signed_angles) if signed_angles else 0.0
        avg_u = sum(unsigned_angles) / max(1, len(unsigned_angles))

        # R channel: Crevice AO
        ao = 0.88
        if min_s < -0.04:
            t_conc = min(1.0, abs(min_s) / 0.75)
            ao = 0.88 - t_conc * 0.48
        elif max_s > 0.25:
            ao = min(0.98, 0.88 + min(1.0, max_s / 0.90) * 0.10)

        # G channel: Edge Curvature (0.50 on flat faces, 0.85..1.0 on convex bevels, 0.20..0.40 in concave seams)
        curv = 0.50
        if max_s > 0.18 or avg_u > 0.24:
            t_edge = min(1.0, max(max_s, avg_u) / 0.65)
            curv = 0.50 + t_edge * 0.49
        elif min_s < -0.08:
            t_rec = min(1.0, abs(min_s) / 0.75)
            curv = 0.50 - t_rec * 0.28

        rel_z = max(0.0, min(1.0, (v.co.z - z_min) / z_span))
        soot = 0.62 + 0.36 * rel_z
        ao_map[v.index] = max(0.35, min(1.0, ao * (0.82 + 0.18 * rel_z)))
        curv_map[v.index] = max(0.15, min(1.0, curv))
        soot_map[v.index] = soot

    # 1-ring neighbor smoothing for AO while preserving crisp edge curvature
    ao_smooth: dict[int, float] = {}
    for v in bm.verts:
        nbrs = [other.index for e in v.link_edges for other in e.verts if other != v]
        if nbrs:
            ao_smooth[v.index] = ao_map[v.index] * 0.72 + (sum(ao_map[i] for i in nbrs) / len(nbrs)) * 0.28
        else:
            ao_smooth[v.index] = ao_map[v.index]

    bm.free()

    col_attr = mesh.color_attributes.get("Col")
    if col_attr is None:
        col_attr = mesh.color_attributes.new(name="Col", type='BYTE_COLOR', domain='CORNER')

    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            v_idx = mesh.loops[loop_idx].vertex_index
            r = ao_smooth.get(v_idx, 0.86)
            g = curv_map.get(v_idx, 0.50)
            b = soot_map.get(v_idx, 0.80)
            col_attr.data[loop_idx].color = (r, g, b, 1.0)


def build_articulated_shell_lames(
    bm: bmesh.types.BMesh,
    stations: list[tuple[Vector, float, float]],
    num_lames: int = 5,
    segs_u: int = 28,
    rows_per_lame: int = 4,
    skin_offset: float = 0.006,
    thickness: float = 0.0045,
    shingle_step: float = 0.0025,
    angle_start: float = 0.0,
    angle_sweep: float = math.tau,
    flute_count: int = 10,
    flute_amp: float = 0.0022,
    border_trim: bool = True,
    plate_mat_idx: int = 0,
    trim_mat_idx: int = 2,
    recess_rune_every: int = 0,
    rune_mat_idx: int = 3,
) -> int:
    """
    Extracts/builds articulated overlapping gothic shell lames from anatomical station curves:
      - Offset >= `skin_offset` (0.004m..0.008m) outside the mannequin skin surface
      - Each overlapping lame steps outward by `shingle_step` (+0.0025m) along the surface normal
      - Solidified with inner & outer shell walls (`thickness` = 0.0035m..0.006m) and beveled borders
      - Embosses 3D cathedral rib-fluting, raised 0.002m border trim, and optional recessed rune channels
    Returns number of generated sub-elements.
    """
    closed_loop = abs(angle_sweep - math.tau) < 1e-3
    u_count = segs_u if closed_loop else (segs_u + 1)
    n_stat = len(stations)
    if n_stat < 2:
        return 0

    def sample_station(t_global: float) -> tuple[Vector, float, float]:
        t_clamped = max(0.0, min(1.0, t_global)) * (n_stat - 1)
        idx0 = min(n_stat - 2, int(math.floor(t_clamped)))
        frac = t_clamped - idx0
        c0, rx0, ry0 = stations[idx0]
        c1, rx1, ry1 = stations[idx0 + 1]
        return (
            c0.lerp(c1, frac),
            rx0 + (rx1 - rx0) * frac,
            ry0 + (ry1 - ry0) * frac,
        )

    parts = 0
    for lame_i in range(num_lames):
        t0 = max(0.0, (lame_i - 0.14) / num_lames)
        t1 = min(1.0, (lame_i + 1.0) / num_lames)
        lame_normal_off = skin_offset + (lame_i % 3) * shingle_step

        outer_rings: list[list[bmesh.types.BMVert]] = []
        inner_rings: list[list[bmesh.types.BMVert]] = []

        for r_i in range(rows_per_lame + 1):
            frac_v = r_i / rows_per_lame
            t_val = t0 + (t1 - t0) * frac_v
            cent, rx, ry = sample_station(t_val)
            is_border_row = (r_i == 0 or r_i == rows_per_lame)
            trim_bump = 0.0020 if (border_trim and is_border_row) else 0.0
            shingle_flare = (1.0 - frac_v) * shingle_step

            o_ring: list[bmesh.types.BMVert] = []
            i_ring: list[bmesh.types.BMVert] = []

            for u_i in range(u_count):
                u_frac = (u_i / segs_u)
                ang = angle_start + u_frac * angle_sweep
                ca, sa = math.cos(ang), math.sin(ang)

                flute = 0.0
                if flute_count > 0 and not is_border_row:
                    flute = math.cos(u_frac * flute_count * math.tau) * flute_amp

                in_r_x = rx + lame_normal_off + shingle_flare
                in_r_y = ry + lame_normal_off + shingle_flare
                out_r_x = in_r_x + thickness + trim_bump + flute
                out_r_y = in_r_y + thickness + trim_bump + flute

                iv = bm.verts.new((cent.x + ca * in_r_x, cent.y + sa * in_r_y, cent.z))
                ov = bm.verts.new((cent.x + ca * out_r_x, cent.y + sa * out_r_y, cent.z))
                i_ring.append(iv)
                o_ring.append(ov)

            inner_rings.append(i_ring)
            outer_rings.append(o_ring)

        # Stitch outer & inner solidified shell faces + top/bottom beveled rim caps
        for r_i in range(rows_per_lame):
            is_border_band = (r_i == 0 or r_i == rows_per_lame - 1)
            for u_i in range(segs_u):
                u_next = (u_i + 1) % u_count if closed_loop else (u_i + 1)
                m_use = trim_mat_idx if (border_trim and is_border_band) else plate_mat_idx
                if recess_rune_every > 0 and not is_border_band and (u_i % recess_rune_every == 0) and (lame_i % 2 == 1):
                    m_use = rune_mat_idx
                try:
                    fo = bm.faces.new((
                        outer_rings[r_i][u_i],
                        outer_rings[r_i][u_next],
                        outer_rings[r_i + 1][u_next],
                        outer_rings[r_i + 1][u_i],
                    ))
                    fo.material_index = m_use
                    fo.smooth = True
                    fi = bm.faces.new((
                        inner_rings[r_i][u_next],
                        inner_rings[r_i][u_i],
                        inner_rings[r_i + 1][u_i],
                        inner_rings[r_i + 1][u_next],
                    ))
                    fi.material_index = plate_mat_idx
                    fi.smooth = True
                except ValueError:
                    pass

        # Rim thickness caps at bottom (r_i = 0) and top (r_i = rows_per_lame)
        for u_i in range(segs_u):
            u_next = (u_i + 1) % u_count if closed_loop else (u_i + 1)
            try:
                fb = bm.faces.new((inner_rings[0][u_i], inner_rings[0][u_next], outer_rings[0][u_next], outer_rings[0][u_i]))
                fb.material_index = trim_mat_idx
                fb.smooth = True
                ft = bm.faces.new((outer_rings[-1][u_i], outer_rings[-1][u_next], inner_rings[-1][u_next], inner_rings[-1][u_i]))
                ft.material_index = trim_mat_idx
                ft.smooth = True
            except ValueError:
                pass

        if not closed_loop:
            for r_i in range(rows_per_lame):
                try:
                    fl = bm.faces.new((inner_rings[r_i][0], outer_rings[r_i][0], outer_rings[r_i + 1][0], inner_rings[r_i + 1][0]))
                    fl.material_index = trim_mat_idx
                    fr = bm.faces.new((outer_rings[r_i][-1], inner_rings[r_i][-1], inner_rings[r_i + 1][-1], outer_rings[r_i + 1][-1]))
                    fr.material_index = trim_mat_idx
                except ValueError:
                    pass
        parts += 4

    return parts


def add_wrap_strap_with_buckle(
    bm: bmesh.types.BMesh,
    center: Vector,
    rx: float,
    ry: float,
    strap_width: float = 0.015,
    strap_thick: float = 0.0022,
    buckle_angle: float = -math.pi * 0.5,
    segs: int = 24,
    leather_mat_idx: int = 1,
    brass_mat_idx: int = 2,
) -> int:
    """
    Generates a physical wrap-around leather strap (0.015m wide, 0.002m thick) hugging
    an elliptical limb/torso cross-section, complete with a brass pin-buckle frame and tongue.
    """
    half_w = strap_width * 0.5
    rings_in: list[list[bmesh.types.BMVert]] = []
    rings_out: list[list[bmesh.types.BMVert]] = []
    for row_z in (-half_w, half_w):
        r_in: list[bmesh.types.BMVert] = []
        r_out: list[bmesh.types.BMVert] = []
        for s_i in range(segs):
            ang = (s_i / segs) * math.tau
            ca, sa = math.cos(ang), math.sin(ang)
            r_in.append(bm.verts.new((center.x + ca * rx, center.y + sa * ry, center.z + row_z)))
            r_out.append(bm.verts.new((center.x + ca * (rx + strap_thick), center.y + sa * (ry + strap_thick), center.z + row_z)))
        rings_in.append(r_in)
        rings_out.append(r_out)

    for s_i in range(segs):
        s_next = (s_i + 1) % segs
        try:
            fo = bm.faces.new((rings_out[0][s_i], rings_out[0][s_next], rings_out[1][s_next], rings_out[1][s_i]))
            fo.material_index = leather_mat_idx
            fo.smooth = True
            fi = bm.faces.new((rings_in[0][s_next], rings_in[0][s_i], rings_in[1][s_i], rings_in[1][s_next]))
            fi.material_index = leather_mat_idx
            ft = bm.faces.new((rings_out[1][s_i], rings_out[1][s_next], rings_in[1][s_next], rings_in[1][s_i]))
            ft.material_index = leather_mat_idx
            fb = bm.faces.new((rings_in[0][s_i], rings_in[0][s_next], rings_out[0][s_next], rings_out[0][s_i]))
            fb.material_index = leather_mat_idx
        except ValueError:
            pass

    # Brass pin-buckle frame + center pin at buckle_angle
    ca, sa = math.cos(buckle_angle), math.sin(buckle_angle)
    bx = center.x + ca * (rx + strap_thick + 0.0018)
    by = center.y + sa * (ry + strap_thick + 0.0018)
    bz = center.z
    rot_z = buckle_angle + math.pi * 0.5
    rmat = Euler((0.0, 0.0, rot_z), 'XYZ').to_matrix()

    for b_size, b_off in [
        ((0.022, 0.0035, 0.0032), Vector((0.0, 0.0, half_w + 0.001))),
        ((0.022, 0.0035, 0.0032), Vector((0.0, 0.0, -half_w - 0.001))),
        ((0.0035, 0.0035, strap_width + 0.004), Vector((-0.010, 0.0, 0.0))),
        ((0.0035, 0.0035, strap_width + 0.004), Vector((0.010, 0.0, 0.0))),
        ((0.014, 0.0028, 0.0024), Vector((0.002, -0.001, 0.0))),  # Buckle pin tongue
    ]:
        ret = bmesh.ops.create_cube(bm, size=1.0)
        vs = ret["verts"]
        for v in vs:
            v.co.x *= b_size[0]
            v.co.y *= b_size[1]
            v.co.z *= b_size[2]
            v.co += b_off
        bmesh.ops.rotate(bm, verts=vs, cent=(0.0, 0.0, 0.0), matrix=rmat)
        bmesh.ops.translate(bm, verts=vs, vec=(bx, by, bz))
        for f in {f for v in vs for f in v.link_faces}:
            f.material_index = brass_mat_idx
            f.smooth = False

    return 6


def add_border_hex_bolts(
    bm: bmesh.types.BMesh,
    center: Vector,
    rx: float,
    ry: float,
    count: int = 12,
    bolt_radius: float = 0.0022,
    bolt_height: float = 0.0018,
    angle_start: float = 0.0,
    angle_sweep: float = math.tau,
    brass_mat_idx: int = 2,
) -> int:
    """
    Places tiny, sharp 0.0020m..0.0025m hexagonal bolts / low-profile rosette studs
    strictly along a plate border ring with zero emission.
    """
    for i in range(count):
        ang = angle_start + ((i + 0.5) / count) * angle_sweep
        ca, sa = math.cos(ang), math.sin(ang)
        px = center.x + ca * rx
        py = center.y + sa * ry
        pz = center.z
        ret = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=6, radius1=bolt_radius, radius2=bolt_radius * 0.78, depth=bolt_height)
        vs = ret["verts"]
        rmat = Euler((math.radians(90.0), 0.0, ang + math.pi * 0.5), 'XYZ').to_matrix()
        bmesh.ops.rotate(bm, verts=vs, cent=(0.0, 0.0, 0.0), matrix=rmat)
        bmesh.ops.translate(bm, verts=vs, vec=(px, py, pz))
        for f in {f for v in vs for f in v.link_faces}:
            f.material_index = brass_mat_idx
            f.smooth = False
    return count
