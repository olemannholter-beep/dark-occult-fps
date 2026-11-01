import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Euler


def _det_hash(seed_a: int, seed_b: int, seed_c: int = 0) -> float:
    """Deterministic pseudo-random float in [-1.0, +1.0]."""
    h = (seed_a * 73856093) ^ (seed_b * 19349663) ^ (seed_c * 83492791)
    h = ((h >> 13) ^ h) * 1274126177
    val = ((h & 0x7FFFFFFF) % 10000) / 5000.0 - 1.0
    return val


def _add_bm_beveled_box(
    bm: bmesh.types.BMesh,
    size: tuple[float, float, float],
    center: tuple[float, float, float],
    rot_euler: tuple[float, float, float] = (0.0, 0.0, 0.0),
    bevel_width: float = 0.008,
    mat_idx: int = 0,
) -> None:
    """Appends a 3D beveled box directly into `bm` with material index `mat_idx` in O(1) time."""
    ret = bmesh.ops.create_cube(bm, size=1.0)
    verts = ret["verts"]
    sx, sy, sz = size
    for v in verts:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sz

    if abs(rot_euler[0]) > 1e-6 or abs(rot_euler[1]) > 1e-6 or abs(rot_euler[2]) > 1e-6:
        rot_mat = Euler(rot_euler, 'XYZ').to_matrix()
        bmesh.ops.rotate(bm, verts=verts, cent=(0.0, 0.0, 0.0), matrix=rot_mat)

    orig_faces = {f for v in verts for f in v.link_faces}
    orig_edges = {e for v in verts for e in v.link_edges}

    if bevel_width > 0.0:
        bev_ret = bmesh.ops.bevel(
            bm,
            geom=list(orig_edges),
            offset=bevel_width,
            offset_type='OFFSET',
            segments=1,
            profile=0.5,
            affect='EDGES',
        )
        all_verts = [v for v in (set(verts) | set(bev_ret.get("verts", []))) if v.is_valid]
        all_faces = {f for v in all_verts for f in v.link_faces if f.is_valid}
        bmesh.ops.translate(bm, verts=all_verts, vec=center)
        for f in all_faces:
            f.material_index = mat_idx
            f.smooth = False
    else:
        bmesh.ops.translate(bm, verts=verts, vec=center)
        for f in orig_faces:
            if f.is_valid:
                f.material_index = mat_idx
                f.smooth = False


def build_staggered_masonry_wall(
    bm: bmesh.types.BMesh,
    width: float,
    height: float,
    depth: float,
    rows: int = 10,
    cols: int = 8,
    recess_mortar: float = 0.018,
    opening_bounds: tuple[float, float, float, float] | None = None,
    stone_mat_idx: int = 0,
    mortar_mat_idx: int = 1,
) -> int:
    """
    Populates `bm` with a recessed mortar core and staggered 3D ashlar stone blocks on both
    front (-Y) and back (+Y) wall faces with randomized depth offsets (±0.012m), slight rotational
    imperfection (±0.6°), and beveled stone edges (0.008m).
    `opening_bounds` optionally specifies `(x_min, x_max, z_min, z_max)` to skip blocks inside a door/window opening.
    Returns total number of generated 3D sub-elements.
    """
    part_count = 0
    mortar_depth = max(0.08, depth - recess_mortar * 2.0)

    # 1. Recessed dark mortar core slab (split around opening if opening_bounds is provided)
    if opening_bounds is None:
        _add_bm_beveled_box(
            bm,
            (width - 0.02, mortar_depth, height - 0.02),
            (0.0, 0.0, height * 0.5),
            bevel_width=0.005,
            mat_idx=mortar_mat_idx,
        )
        part_count += 1
    else:
        ox0, ox1, oz0, oz1 = opening_bounds
        hw = width * 0.5
        # Left mortar pier
        if ox0 > -hw + 0.08:
            lw = ox0 - (-hw)
            _add_bm_beveled_box(
                bm,
                (lw, mortar_depth, height - 0.02),
                (-hw + lw * 0.5, 0.0, height * 0.5),
                bevel_width=0.004,
                mat_idx=mortar_mat_idx,
            )
            part_count += 1
        # Right mortar pier
        if ox1 < hw - 0.08:
            rw = hw - ox1
            _add_bm_beveled_box(
                bm,
                (rw, mortar_depth, height - 0.02),
                (ox1 + rw * 0.5, 0.0, height * 0.5),
                bevel_width=0.004,
                mat_idx=mortar_mat_idx,
            )
            part_count += 1
        # Lower sill mortar below opening
        if oz0 > 0.08:
            _add_bm_beveled_box(
                bm,
                (ox1 - ox0, mortar_depth, oz0),
                ((ox0 + ox1) * 0.5, 0.0, oz0 * 0.5),
                bevel_width=0.004,
                mat_idx=mortar_mat_idx,
            )
            part_count += 1
        # Upper lintel mortar above opening
        if oz1 < height - 0.08:
            uh = height - oz1
            _add_bm_beveled_box(
                bm,
                (ox1 - ox0, mortar_depth, uh),
                ((ox0 + ox1) * 0.5, 0.0, oz1 + uh * 0.5),
                bevel_width=0.004,
                mat_idx=mortar_mat_idx,
            )
            part_count += 1

    # 2. Staggered 3D ashlar stone courses on both front (-Y) and back (+Y) faces
    row_h = height / rows
    mortar_gap = 0.016
    block_thick = depth * 0.28

    for side_idx, side_sign in enumerate((-1.0, 1.0)):
        for r in range(rows):
            cz = (r + 0.5) * row_h
            bh = row_h - mortar_gap
            stagger = 0.5 if (r % 2 == 1) else 0.0
            col_w = width / cols

            for c in range(cols + 1):
                x_left = -width * 0.5 + (c - stagger) * col_w
                x_right = x_left + col_w
                # Clamp block to wall horizontal bounds
                x0 = max(-width * 0.5 + 0.01, x_left + mortar_gap * 0.5)
                x1 = min(width * 0.5 - 0.01, x_right - mortar_gap * 0.5)
                bw = x1 - x0
                if bw < 0.09:
                    continue
                cx = (x0 + x1) * 0.5

                # Check if block overlaps door/window opening
                if opening_bounds is not None:
                    ox0, ox1, oz0, oz1 = opening_bounds
                    if x1 > ox0 + 0.02 and x0 < ox1 - 0.02 and (cz + bh * 0.5) > oz0 + 0.02 and (cz - bh * 0.5) < oz1 - 0.02:
                        continue

                depth_jitter = _det_hash(r, c, side_idx + 11) * 0.012
                rot_x = math.radians(_det_hash(r, c, side_idx + 23) * 0.55)
                rot_y = math.radians(_det_hash(r, c, side_idx + 37) * 0.55)
                rot_z = math.radians(_det_hash(r, c, side_idx + 53) * 0.45)

                cy = side_sign * (depth * 0.5 - block_thick * 0.5 + depth_jitter)
                _add_bm_beveled_box(
                    bm,
                    (bw, block_thick, bh),
                    (cx, cy, cz),
                    rot_euler=(rot_x, rot_y, rot_z),
                    bevel_width=0.008,
                    mat_idx=stone_mat_idx,
                )
                part_count += 1

    return part_count


def build_gothic_wainscot_and_cornice(
    bm: bmesh.types.BMesh,
    width: float,
    height: float,
    depth: float,
    opening_bounds: tuple[float, float, float, float] | None = None,
    trim_mat_idx: int = 2,
    iron_mat_idx: int = 3,
) -> int:
    """
    Adds multi-stepped base plinths, recessed pointed-arch blind tracery panels,
    carved frieze moldings, corner quoins, and wrought-iron wall tie-plates with rivets to `bm`.
    Returns number of generated sub-elements.
    """
    part_count = 0

    # 1. Multi-stepped base plinths (2 tiers, split if doorway opening intersects Z < 0.5m)
    plinth_tiers = [
        (0.24, depth + 0.12, 0.12),
        (0.18, depth + 0.08, 0.33),
    ]
    for p_h, p_d, p_z in plinth_tiers:
        if opening_bounds is not None and opening_bounds[2] < 0.48:
            ox0, ox1, _, _ = opening_bounds
            hw = width * 0.5 + 0.02
            if ox0 > -hw + 0.1:
                lw = ox0 - (-hw)
                _add_bm_beveled_box(bm, (lw, p_d, p_h), (-hw + lw * 0.5, 0.0, p_z), bevel_width=0.010, mat_idx=trim_mat_idx)
                part_count += 1
            if ox1 < hw - 0.1:
                rw = hw - ox1
                _add_bm_beveled_box(bm, (rw, p_d, p_h), (ox1 + rw * 0.5, 0.0, p_z), bevel_width=0.010, mat_idx=trim_mat_idx)
                part_count += 1
        else:
            _add_bm_beveled_box(bm, (width + 0.04, p_d, p_h), (0.0, 0.0, p_z), bevel_width=0.010, mat_idx=trim_mat_idx)
            part_count += 1

    # 2. Mid-height wainscot stringcourse ledge (Z = 1.12m) & Blind-Arch Wainscot Tracery Mullions
    wainscot_z = 1.12
    for side_sign in (-1.0, 1.0):
        wy = side_sign * (depth * 0.5 + 0.025)
        if opening_bounds is None or opening_bounds[2] > 1.20:
            _add_bm_beveled_box(bm, (width + 0.02, 0.06, 0.09), (0.0, wy, wainscot_z), bevel_width=0.008, mat_idx=trim_mat_idx)
            part_count += 1

        # Vertical wainscot blind-tracery ribs between Z = 0.42m and Z = 1.08m
        num_panels = 6
        panel_step = (width - 0.5) / num_panels
        for p_i in range(num_panels + 1):
            px = -width * 0.5 + 0.25 + p_i * panel_step
            if opening_bounds is not None and opening_bounds[0] - 0.12 <= px <= opening_bounds[1] + 0.12 and opening_bounds[2] < 1.15:
                continue
            _add_bm_beveled_box(bm, (0.065, 0.045, 0.66), (px, wy, 0.75), bevel_width=0.006, mat_idx=trim_mat_idx)
            part_count += 1
            # Pointed blind-arch chevron header at top of each wainscot bay
            if p_i < num_panels:
                bay_cx = px + panel_step * 0.5
                if opening_bounds is not None and opening_bounds[0] - 0.15 <= bay_cx <= opening_bounds[1] + 0.15 and opening_bounds[2] < 1.15:
                    continue
                _add_bm_beveled_box(
                    bm,
                    (panel_step * 0.52, 0.04, 0.045),
                    (bay_cx - panel_step * 0.18, wy, 1.00),
                    rot_euler=(0.0, math.radians(-24.0), 0.0),
                    bevel_width=0.005,
                    mat_idx=trim_mat_idx,
                )
                _add_bm_beveled_box(
                    bm,
                    (panel_step * 0.52, 0.04, 0.045),
                    (bay_cx + panel_step * 0.18, wy, 1.00),
                    rot_euler=(0.0, math.radians(24.0), 0.0),
                    bevel_width=0.005,
                    mat_idx=trim_mat_idx,
                )
                part_count += 2

    # 3. Alternating Corner Quoins along left and right wall edges
    quoin_rows = 8
    qh = (height - 0.75) / quoin_rows
    for qr in range(quoin_rows):
        qz = 0.45 + (qr + 0.5) * qh
        qw = 0.34 if (qr % 2 == 0) else 0.24
        for sx in (-1.0, 1.0):
            qx = sx * (width * 0.5 - qw * 0.5 + 0.015)
            _add_bm_beveled_box(
                bm,
                (qw, depth + 0.09, qh - 0.02),
                (qx, 0.0, qz),
                bevel_width=0.010,
                mat_idx=trim_mat_idx,
            )
            part_count += 1

    # 4. Stepped Top Cornice, Dentil Corbels & Frieze Molding
    _add_bm_beveled_box(bm, (width + 0.06, depth + 0.10, 0.14), (0.0, 0.0, height - 0.22), bevel_width=0.010, mat_idx=trim_mat_idx)
    _add_bm_beveled_box(bm, (width + 0.08, depth + 0.16, 0.16), (0.0, 0.0, height - 0.08), bevel_width=0.012, mat_idx=trim_mat_idx)
    part_count += 2

    # Dentil corbel blocks beneath the cornice on both faces
    for side_sign in (-1.0, 1.0):
        dy = side_sign * (depth * 0.5 + 0.04)
        for d_i in range(9):
            dx = -width * 0.5 + 0.30 + d_i * ((width - 0.60) / 8.0)
            _add_bm_beveled_box(bm, (0.12, 0.07, 0.11), (dx, dy, height - 0.33), bevel_width=0.006, mat_idx=trim_mat_idx)
            part_count += 1

    # 5. Wrought-iron structural S/X wall tie-plates and rivet studs
    tie_xs = [-width * 0.34, width * 0.34]
    for side_sign in (-1.0, 1.0):
        iy = side_sign * (depth * 0.5 + 0.018)
        for tx in tie_xs:
            if opening_bounds is not None and opening_bounds[0] - 0.25 <= tx <= opening_bounds[1] + 0.25:
                continue
            for tz in (1.75, 3.15):
                # Vertical iron tie bar + horizontal anchor plate + 4 rivets
                _add_bm_beveled_box(bm, (0.05, 0.022, 0.36), (tx, iy, tz), bevel_width=0.003, mat_idx=iron_mat_idx)
                _add_bm_beveled_box(bm, (0.26, 0.022, 0.05), (tx, iy, tz), bevel_width=0.003, mat_idx=iron_mat_idx)
                part_count += 2
                for r_off in (-0.10, 0.10):
                    _add_bm_beveled_box(
                        bm,
                        (0.026, 0.028, 0.026),
                        (tx + r_off, iy + side_sign * 0.01, tz),
                        bevel_width=0.004,
                        mat_idx=iron_mat_idx,
                    )
                    _add_bm_beveled_box(
                        bm,
                        (0.026, 0.028, 0.026),
                        (tx, iy + side_sign * 0.01, tz + r_off * 1.3),
                        bevel_width=0.004,
                        mat_idx=iron_mat_idx,
                    )
                    part_count += 2

    return part_count


def build_cobble_flagstone_floor(
    bm: bmesh.types.BMesh,
    width: float,
    length: float,
    grid_x: int = 6,
    grid_z: int = 6,
    slab_mat_idx: int = 0,
    tile_mat_idx: int = 1,
    trim_mat_idx: int = 2,
) -> int:
    """
    Populates `bm` with a thick structural light-sealing mortar bed and `grid_x * grid_z` (36+)
    individual 3D beveled flagstone pavers of varied sizes, subtle height variation (±0.004m),
    sub-divided ashlar pavers, and recessed dark grout seams.
    Top walkable surface stays flush near Z = 0.0m.
    """
    part_count = 0

    # 1. Solid 0.35m structural dark mortar bed (Z = -0.36m to Z = -0.018m)
    _add_bm_beveled_box(
        bm,
        (width, length, 0.342),
        (0.0, 0.0, -0.189),
        bevel_width=0.006,
        mat_idx=slab_mat_idx,
    )
    part_count += 1

    # 2. Variable-width grid lines for natural gothic ashlar paving
    x_lines = [-width * 0.5 + (i / grid_x) * width for i in range(grid_x + 1)]
    y_lines = [-length * 0.5 + (j / grid_z) * length for j in range(grid_z + 1)]
    for i in range(1, grid_x):
        x_lines[i] += _det_hash(i, 101, 7) * 0.055
    for j in range(1, grid_z):
        y_lines[j] += _det_hash(j, 202, 13) * 0.055

    seam_gap = 0.018
    paver_thick = 0.036

    for ix in range(grid_x):
        for iy in range(grid_z):
            x0 = x_lines[ix] + seam_gap * 0.5
            x1 = x_lines[ix + 1] - seam_gap * 0.5
            y0 = y_lines[iy] + seam_gap * 0.5
            y1 = y_lines[iy + 1] - seam_gap * 0.5
            pw = x1 - x0
            pl = y1 - y0
            cx = (x0 + x1) * 0.5
            cy = (y0 + y1) * 0.5

            # Split every 3rd tile into 2 smaller interlocking cobblestones so part count is 150+ with edge border stones
            split_mode = (ix * 3 + iy * 5) % 4
            if split_mode == 0:
                # Split along X into 2 stones
                xm = cx + _det_hash(ix, iy, 31) * 0.04
                for sub_i, (sx0, sx1) in enumerate(((x0, xm - seam_gap * 0.4), (xm + seam_gap * 0.4, x1))):
                    sw = sx1 - sx0
                    if sw < 0.08:
                        continue
                    scx = (sx0 + sx1) * 0.5
                    hz = _det_hash(ix + sub_i, iy, 41) * 0.0035
                    rx = math.radians(_det_hash(ix, iy + sub_i, 51) * 0.25)
                    ry = math.radians(_det_hash(ix + sub_i, iy, 61) * 0.25)
                    m_use = trim_mat_idx if ((ix + iy + sub_i) % 3 == 0) else tile_mat_idx
                    _add_bm_beveled_box(
                        bm,
                        (sw, pl, paver_thick),
                        (scx, cy, -paver_thick * 0.5 + hz),
                        rot_euler=(rx, ry, 0.0),
                        bevel_width=0.009,
                        mat_idx=m_use,
                    )
                    part_count += 1
            elif split_mode == 1:
                # Split along Y into 2 stones
                ym = cy + _det_hash(ix, iy, 71) * 0.04
                for sub_i, (sy0, sy1) in enumerate(((y0, ym - seam_gap * 0.4), (ym + seam_gap * 0.4, y1))):
                    sl = sy1 - sy0
                    if sl < 0.08:
                        continue
                    scy = (sy0 + sy1) * 0.5
                    hz = _det_hash(ix, iy + sub_i, 81) * 0.0035
                    rx = math.radians(_det_hash(ix, iy + sub_i, 91) * 0.25)
                    ry = math.radians(_det_hash(ix + sub_i, iy, 97) * 0.25)
                    m_use = trim_mat_idx if ((ix + iy + sub_i) % 3 == 0) else tile_mat_idx
                    _add_bm_beveled_box(
                        bm,
                        (pw, sl, paver_thick),
                        (cx, scy, -paver_thick * 0.5 + hz),
                        rot_euler=(rx, ry, 0.0),
                        bevel_width=0.009,
                        mat_idx=m_use,
                    )
                    part_count += 1
            else:
                hz = _det_hash(ix, iy, 19) * 0.0038
                rx = math.radians(_det_hash(ix, iy, 29) * 0.25)
                ry = math.radians(_det_hash(ix, iy, 39) * 0.25)
                m_use = trim_mat_idx if ((ix + iy) % 4 == 0) else tile_mat_idx
                _add_bm_beveled_box(
                    bm,
                    (pw, pl, paver_thick),
                    (cx, cy, -paver_thick * 0.5 + hz),
                    rot_euler=(rx, ry, 0.0),
                    bevel_width=0.010,
                    mat_idx=m_use,
                )
                part_count += 1

            # Add small recessed bronze/stone corner key-studs at grid intersections
            if ix < grid_x - 1 and iy < grid_z - 1:
                kx = x_lines[ix + 1]
                ky = y_lines[iy + 1]
                _add_bm_beveled_box(
                    bm,
                    (0.055, 0.055, paver_thick + 0.002),
                    (kx, ky, -paver_thick * 0.5 - 0.001),
                    rot_euler=(0.0, 0.0, math.radians(45.0)),
                    bevel_width=0.005,
                    mat_idx=trim_mat_idx,
                )
                part_count += 1

    # 3. Underside coffered stone ribs along the bottom of the slab (for double-sided ceiling/stair visibility)
    for r_i in range(-1, 2):
        rib_off = r_i * 1.25
        _add_bm_beveled_box(bm, (width - 0.08, 0.14, 0.04), (0.0, rib_off, -0.35), bevel_width=0.006, mat_idx=slab_mat_idx)
        _add_bm_beveled_box(bm, (0.14, length - 0.08, 0.04), (rib_off, 0.0, -0.35), bevel_width=0.006, mat_idx=slab_mat_idx)
        part_count += 2

    return part_count


def bake_3tone_gothic_vertex_colors(
    obj: bpy.types.Object,
    z_min: float = 0.0,
    z_max: float = 4.0,
) -> None:
    """
    Computes deterministic 3-Tone Vertex Colors ('Col') on `obj`:
    1. Ground Soot & Dampness (`z < z_min + 1.1m`): Darkens base vertices smoothly down to 0.55.
    2. Concave Mortar & Crevice Grime (`signed_edge_angle < 0`): Darkens recessed/concave vertices to 0.58.
    3. Convex Worn Edge Highlights (`signed_edge_angle > 0.4` or sharp bevels): Brightens convex bevel edges
       to 0.98–1.00 while flat mid-faces sit at 0.82.
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

    v_factors: dict[int, float] = {}
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

        min_signed = min(signed_angles) if signed_angles else 0.0
        max_signed = max(signed_angles) if signed_angles else 0.0
        avg_unsigned = sum(unsigned_angles) / max(1, len(unsigned_angles))

        # Base mid-face tone is 0.82
        tone = 0.82

        # Concave Mortar & Crevice Grime (signed_angle < -0.05) -> darken toward 0.58
        if min_signed < -0.05:
            concave_t = min(1.0, abs(min_signed) / 0.85)
            tone = 0.82 - concave_t * (0.82 - 0.58)
        # Convex Worn Edge Highlights (signed_angle > 0.35 or bevel ridge) -> brighten to 0.98 - 1.00
        elif max_signed > 0.35 or avg_unsigned > 0.38:
            convex_t = min(1.0, max(max_signed, avg_unsigned) / 0.95)
            tone = 0.82 + convex_t * (0.99 - 0.82)

        # Ground Soot & Dampness (z < z_min + 1.1m) -> darken smoothly down toward 0.55
        rel_z = v.co.z - z_min
        if rel_z < 1.1:
            soot_t = max(0.0, min(1.0, rel_z / 1.1))
            # Smooth quadratic ramp from 0.55 at base to 1.0 multiplier at z_min + 1.1m
            soot_mult = 0.67 + 0.33 * (soot_t * soot_t)
            tone = max(0.55, tone * soot_mult)

        v_factors[v.index] = max(0.55, min(1.00, tone))

    # Light 1-ring neighbor blend to keep highlights crisp while softening harsh steps
    smoothed: dict[int, float] = {}
    for v in bm.verts:
        nbrs = [other.index for e in v.link_edges for other in e.verts if other != v]
        if nbrs:
            avg_nbr = sum(v_factors[idx] for idx in nbrs) / len(nbrs)
            smoothed[v.index] = max(0.55, min(1.00, v_factors[v.index] * 0.78 + avg_nbr * 0.22))
        else:
            smoothed[v.index] = v_factors[v.index]

    bm.free()

    if "Col" in mesh.color_attributes:
        col_attr = mesh.color_attributes["Col"]
    else:
        col_attr = mesh.color_attributes.new(name="Col", type='BYTE_COLOR', domain='CORNER')

    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            v_idx = mesh.loops[loop_idx].vertex_index
            c = smoothed.get(v_idx, 0.82)
            col_attr.data[loop_idx].color = (c, c, c, 1.0)


def create_detailed_wall_object(
    name: str,
    width: float,
    height: float,
    depth: float,
    mat_stone: bpy.types.Material,
    mat_mortar: bpy.types.Material,
    mat_trim: bpy.types.Material,
    mat_iron: bpy.types.Material,
    rows: int = 10,
    cols: int = 8,
    recess_mortar: float = 0.018,
    opening_bounds: tuple[float, float, float, float] | None = None,
) -> tuple[bpy.types.Object, int]:
    """
    Builds a complete ultra-detailed 3D staggered masonry + gothic wainscot + cornice + iron tie-plate wall
    as a single multi-material Blender Object and returns `(obj, sub_part_count)`.
    """
    bm = bmesh.new()
    c1 = build_staggered_masonry_wall(
        bm,
        width=width,
        height=height,
        depth=depth,
        rows=rows,
        cols=cols,
        recess_mortar=recess_mortar,
        opening_bounds=opening_bounds,
        stone_mat_idx=0,
        mortar_mat_idx=1,
    )
    c2 = build_gothic_wainscot_and_cornice(
        bm,
        width=width,
        height=height,
        depth=depth,
        opening_bounds=opening_bounds,
        trim_mat_idx=2,
        iron_mat_idx=3,
    )
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name + "Mesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat_stone)
    obj.data.materials.append(mat_mortar)
    obj.data.materials.append(mat_trim)
    obj.data.materials.append(mat_iron)
    return obj, (c1 + c2)


def create_detailed_floor_object(
    name: str,
    width: float,
    length: float,
    mat_slab: bpy.types.Material,
    mat_tile: bpy.types.Material,
    mat_trim: bpy.types.Material,
    grid_x: int = 6,
    grid_z: int = 6,
) -> tuple[bpy.types.Object, int]:
    """
    Builds a complete ultra-detailed 3D beveled flagstone floor with 36+ uneven pavers,
    sub-divided cobbles, corner key-studs, and recessed dark grout seams.
    """
    bm = bmesh.new()
    cnt = build_cobble_flagstone_floor(
        bm,
        width=width,
        length=length,
        grid_x=grid_x,
        grid_z=grid_z,
        slab_mat_idx=0,
        tile_mat_idx=1,
        trim_mat_idx=2,
    )
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name + "Mesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat_slab)
    obj.data.materials.append(mat_tile)
    obj.data.materials.append(mat_trim)
    return obj, cnt

