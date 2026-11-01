# Survey 2 Handoff Report: Feature 2 (Stairwells & Floor Slabs) & Feature 3 (Compass Text Truncation)

**Author:** Survey Explorer 2 (`teamwork_explorer_survey_r2_2`)  
**Target Recipient:** Orchestrator (`7caaf02e-4314-4901-b634-7676eb41a540`)  
**Scope:**
1. **Feature 2:** Stairwell Wall Blockage & square-block stone texture covering all stairs across the game.
2. **Feature 3:** Top Compass / Biome Header text truncation in `scripts/ui/gothic_hud_overhaul.gd`.

---

## 1. Observation

### A. Feature 3: HUD Compass / Biome Plaque Text Truncation
- **File:** `scripts/ui/gothic_hud_overhaul.gd`
- **Location:** Lines 503–536 (`_draw_top_biome_plaque()`)
- **Direct Code Quote:**
  ```gdscript
  503: func _draw_top_biome_plaque(c: Control, vp: Vector2, font: Font) -> void:
  504: 	if font == null:
  505: 		return
  506: 	var plaque_w: float = 540.0
  507: 	var plaque_h: float = 36.0
  508: 	var p_rect: Rect2 = Rect2((vp.x - plaque_w) * 0.5, 18.0, plaque_w, plaque_h)
  ...
  525: 	var full_header: String = "── ❖ %s : %s ❖ ──" % [biome_header_title, biome_header_subtitle]
  526: 	c.draw_string(
  527: 		font,
  528: 		Vector2(p_rect.position.x, p_rect.position.y + 23.0),
  529: 		full_header,
  530: 		HORIZONTAL_ALIGNMENT_CENTER,
  531: 		plaque_w,
  532: 		13,
  533: 		Color(0.98, 0.86, 0.54, 0.96 * a)
  534: 	)
  ```
- **Observed Behavior:**
  When entering the Catacombs, `biome_header_title` is `"SUBTERRANEAN CATACOMB SANCTUMS"` and `biome_header_subtitle` is `"EIGHT PORTAL CHAMBERS (SAFE HARBOUR)"` (lines 218–219).
  The resulting `full_header` string is 80 characters long (`"── ❖ SUBTERRANEAN CATACOMB SANCTUMS : EIGHT PORTAL CHAMBERS (SAFE HARBOUR) ❖ ──"`). At font size 13, this text occupies ~715–730 pixels in width. Because `plaque_w` is hardcoded to `540.0`, `draw_string()` clips the text at 540 pixels, displaying `"... (SAFE HARB"` with the ending truncated.

---

### B. Feature 2: All Stairs Covered by Square-Block Stone Texture & Blocked by Walls

#### 1. Procedural Dungeon Generator (`scripts/world/procedural_dungeon_generator.gd`)
- **Floor Sealer Covering Stairs (Lines 898–920):**
  ```gdscript
  898: 		var below_cell: Vector3i = Vector3i(cell.x, cell.y - 1, cell.z)
  899: 		var is_outer_bottom: bool = not occupied_cells.has(below_cell)
  900: 		var is_balcony_floor: bool = balcony_floor_cells.has(cell) and not bridge_cells.has(cell)
  901: 		if is_outer_bottom or is_balcony_floor:
  902: 			var use_cistern: bool = false
  903: 			if is_outer_bottom and cistern_ratio > 0.0 and not stair_cells.has(cell):
  ...
  910: 				else "res://scenes/prefabs/architecture/floor_stone_4x4.tscn"
  912: 			_spawn_prefab(cell_arch_parent, floor_path, "ProcFloor_%d" % cell_idx, world_pos)
  916: 			var sub_floor: MeshInstance3D = MeshInstance3D.new()
  917: 			sub_floor.name = "SealerSubFloor_%d" % cell_idx
  918: 			sub_floor.mesh = floor_slab_mesh
  ```
  **Observation:** While line 903 checks `not stair_cells.has(cell)` to avoid placing water cisterns on stairs, line 901 does **NOT** check `not stair_cells.has(cell)` or `not stair_cells.has(below_cell)`. Since stair cells have no cell occupied below them (`is_outer_bottom == true`), `ProcFloor_%d` (`floor_stone_4x4.tscn`, a 6×6 square flagstone block grid) and `SealerSubFloor_%d` are spawned at `world_pos`, placing a flat stone floor slab directly on top of the descending stair slope!
- **Solid Walls Blocking Corridor Staircases (Lines 635–647, 1002–1055, 1690–1701):**
  When a staircase connects two vertical tiers (`prev.gy` to `next_gy = prev.gy - 1` along -Z):
  - At the bottom stair cell (`(corr_x, next_gy, cz)`), the cell to the South (`cz + 1`) was carved at `prev.gy`, meaning `(corr_x, next_gy, cz + 1)` is **empty**.
  - In `_seal_voxel_cells()`, line 1037 checks `if not occupied_cells.has(Vector3i(cell.x, cell.y, cell.z + 1)):`. This evaluates to true, unconditionally spawning `ProcWallS_%d` (`wall_stone_solid.tscn`) and `ColWallS_%d` across the foot of the staircase!
  - At the upper headroom cell (`(corr_x, prev.gy, cz)`), if the adjacent room or corridor ceiling is single-height, the North neighbor `(corr_x, prev.gy, cz - 1)` is empty, spawning `ProcWallN_%d` across the top entrance of the staircase!
- **Bulkhead Wall Over `OSSUARY_L_CATACOMB` (Lines 1912–1920):**
  ```gdscript
  1912: 		"OSSUARY_L_CATACOMB":
  1913: 			# 4x4 footprint with top-right 2x2 quadrant (dx in 2..3, dz in 0..1) left un-carved -> 90-degree L-bend
  1914: 			for dx: int in range(w):
  1915: 				for dz: int in range(l):
  1916: 					var is_uncarved_quadrant: bool = (dx >= 2 and dz <= 1)
  1917: 					if is_uncarved_quadrant:
  1918: 						continue
  1919: 					occupied_cells[Vector3i(gx + dx, gy, gz + dz)] = true
  ```
  **Observation:** Unlike all other archetypes (line 1930) which iterate `for dy in range(h):`, `OSSUARY_L_CATACOMB` only sets `occupied_cells` for `dy = 0`. For 2-cell-high dungeons (`h = 2`), layer `gy + 1` remains empty. The incoming corridor (2 cells high) encounters an empty cell at `gy + 1` and `_seal_voxel_cells()` spawns a solid stone wall across the top 4 meters of the corridor, dropping a 4m solid bulkhead in front of the player.

---

#### 2. Level Prefab & Town Scene (`tools/build_prefabs_and_level.gd`)
- **Church-to-Crypt Central Stairwell (`StairsStone4x4`):**
  - In `church` (local `Y = 4.0`), `StairsStone4x4` is placed at `Vector3(0.0, 0.0, -50.0)` (World `(0, 4, -50)`), descending North from World `Z = -48.0` (`Y = 4.0`) to `Z = -52.0` (`Y = 0.0`).
  - In `ch1` (`CryptBasement` container at World `Z = -28.0`):
    - **Line 3016:** `_spawn_prefab(root, ch1, p_wall_solid, "StairwellWallSouth", Vector3(0.0, -0.65, -19.55))`. Local `Z = -19.55` corresponds to World `Z = -47.55`—literally 0.45m from the top step! This is a solid wall directly blocking access to the stairs.
    - **Line 3019:** `_spawn_prefab(root, ch1, p_wall_solid, "StairwellNorthBulkheadWall", Vector3(0.0, 4.0, -24.05))`. Local `Z = -24.05` is World `Z = -52.05`. Local `Y = 4.0` is World `Y = 4.0`. This is a solid wall at the bottom step rising up into the Church nave floor from `Y = 4.0` to `8.0`.
    - **Line 3021:** `_spawn_prefab(root, ch1, p_floor, "StairwellCollarCeilNorth", Vector3(0.0, 4.0, -26.05))`. Places a stone floor slab at World `Z = -54.05`.
    - **Line 3015 & 2381:** `_register_crypt_room_cell(occupied_cells, 0, 0, -5, "ch1")` registers cell `(0, 0, -5)`. Cell `(0, -1, -5)` is empty. `_seal_crypt_grid_boundaries()` evaluates line 2381 and spawns `AutoSealFloor_0_0_-5` (`floor_stone_4x4.tscn`) at World `Z = -48.0`, sealing the top of the stairwell with a square stone floor slab!
- **Catacomb Staircases & Portcullis Blockers:**
  - **Auto-Sealer Exterior Wall Leak (Line 2418):**
    ```gdscript
    2418: 			if n_group.is_empty():
    2419: 				# Exterior boundary face: MUST be sealed by a solid wall (never open or portcullis)
    ...
    2426: 				if not placed_walls.has(w_key):
    2427: 					_spawn_crypt_wall(...)
    ```
    **Observation:** Line 2418 does **NOT** check `not open_passages.has(w_key)`!
    When a staircase descends from `Y = 0` to `Y = -4` (e.g., `stair_1_6`, `stair_4_5`, `stair_6_7`, `stair_6_8`), the upper stair cell at `gy` has an empty neighbor in horizontal space because the lower chamber ceiling is at `gy - 1`. Because `n_group.is_empty()`, line 2418 unconditionally spawns a solid exterior stone wall (`AutoSealWallExt_*`) across the upper stairwell opening, completely walling off the stairs!
  - **Low Portcullis Prefabs & Solid Overhead Bulkheads at Stair Landings:**
    - Line 3277: `Ch5PortcullisSouthStairs` (`Vector3(wx, -4.0, -38.0)`) placed right at the foot of `StairsCh4ToCh5`.
    - Line 3342: `Ch6PortcullisSouth` (`Vector3(wx, -4.0, -38.0)`) placed right at the foot of `StairsCh1ToCh6`.
    - Line 3419–3420: `Ch7PortcullisSouthStairs` at `Vector3(wx, -8.0, -62.0)` AND `Ch7WallSouthHighStairBulkhead` (`p_wall_solid`) at `Vector3(wx, -4.0, -62.0)` placed directly across the descent of `StairsCh6ToCh7`. A player walking down hits `Ch7WallSouthHighStairBulkhead` at head height!
    - Line 3501–3502: `Ch8PortcullisSouthEntrance` at `Vector3(wx, -8.0, -62.0)` AND `Ch8WallSouthHighCenter` (`p_wall_solid`) at `Vector3(wx, -4.0, -62.0)` placed directly across the bottom opening of `StairsCh6ToCh8`.

---

#### 3. Blender Town Terrain (`tools/blender_build_voxel_town_and_loot.py`)
- **Location:** Lines 1392–1407 (`build_terrain_town()`)
- **Direct Code Quote:**
  ```python
  1392:     # 4. Mandatory Boolean Stairwell Cutout: Size 27.6m (X) x 35.8m (Y) x 20.0m (Z) at gx = 0.0, gz = -39.9
  1393:     bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 39.9, 2.0))
  1394:     cutter = bpy.context.active_object
  1395:     cutter.name = "CryptTerrainCutter"
  1396:     cutter.scale = (27.6, 35.8, 20.0)
  1397:     bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
  1398: 
  1399:     bool_mod = terrain_obj.modifiers.new(name="CryptCutoutBoolean", type='BOOLEAN')
  1400:     bool_mod.operation = 'DIFFERENCE'
  1401:     bool_mod.solver = 'EXACT'
  1402:     bool_mod.object = cutter
  ```
- **Observed Behavior:**
  `terrain_obj` is an open 2.5D displaced mesh surface (non-manifold sheet). Applying a 3D box `BOOLEAN` `DIFFERENCE` with `solver = 'EXACT'` to a zero-thickness non-manifold sheet generates degenerate bridging polygons, non-manifold intersection seams, and planar artifacts across the stairwell void between World `Z = -22.0` and `Z = -57.8`.

---

## 2. Logic Chain

1. **Feature 3 (Compass Text Clipping):**
   - The string length is variable and reaches 80 characters for the full biome name and subtitle.
   - Using a fixed width of `540.0` pixels causes `Control.draw_string()` to truncate any text longer than 540 pixels.
   - By querying `font.get_string_size(full_header, ...).x` and setting `plaque_w = maxf(780.0, text_w + 48.0)`, both the backing banner and the text boundary expand dynamically, ensuring complete visibility on all display aspect ratios.

2. **Feature 2 (Square-Block Floor Texture on Stairs):**
   - In Godot, `floor_stone_4x4.tscn` uses a 6×6 square ashlar stone block texture.
   - When the voxel generator or level sealer processes a stair cell, it evaluates `occupied_cells.has(below_cell)`.
   - Stair cells inherently lack an occupied cell directly beneath them in the grid.
   - Consequently, both `_seal_voxel_cells()` in `procedural_dungeon_generator.gd` and `_seal_crypt_grid_boundaries()` in `build_prefabs_and_level.gd` classify the stair cell as an exterior bottom floor and instantiate `floor_stone_4x4.tscn` directly inside the stair cell.
   - This places a horizontal square-block slab directly over the angled stair treads.
   - Therefore, stair cells must be explicitly excluded from bottom face floor generation in both systems:
     - In procedural generation: `if (is_outer_bottom or is_balcony_floor) and not stair_cells.has(cell) and not stair_cells.has(below_cell):`
     - In handcrafted crypt levels: `if not is_stair_cell and occupied_cells.get(below_cell, "") != group_id and not placed_floors.has(cell):`

3. **Feature 2 (Stairwell Wall Blockages):**
   - For any stair connecting tier $Y_1$ to $Y_0$, the upper landing cell has no neighbor at $Y_1$ looking in the direction of the lower room.
   - The auto-sealer's exterior wall check `if n_group.is_empty():` failed to check `open_passages`.
   - It treated the boundary as an outer building perimeter and sealed it with `AutoSealWallExt_*`.
   - By enforcing `if n_group.is_empty(): if open_passages.has(w_key): continue` and registering the stairwell passage keys in `open_passages`, exterior walls will never seal stair openings.
   - In `ch1`, manually placed walls (`StairwellWallSouth`, `StairwellNorthBulkheadWall`) were hardcoded directly in front of the Church-to-Crypt stairs; removing them clears the entry and exit corridors.
   - Replacing the 4 low-hanging spike portcullises (`Ch6PortcullisSouth`, `Ch5PortcullisSouthStairs`, `Ch7PortcullisSouthStairs`, `Ch8PortcullisSouthEntrance`) with open stone archways (`p_wall_door`) and removing the overhead solid bulkheads (`Ch7WallSouthHighStairBulkhead`, `Ch8WallSouthHighCenter`) provides 4+ meters of clear vertical headroom along every catacomb staircase.

4. **Feature 2 (Blender Non-Manifold Terrain Cutout):**
   - The Boolean modifier fails because the terrain grid has no solid volume.
   - BMesh face deletion acts directly on vertices and faces within the bounding box `[-13.8 <= x <= 13.8]` and `[22.0 <= y <= 57.8]` (Blender $+Y$ = Godot $-Z$).
   - Deleting the faces and unlinked vertices deterministically removes all geometry in the cutout zone with zero mesh corruption.

---

## 3. Caveats

1. **Light-Bleeding Prevention:**
   When removing `StairwellWallSouth` and replacing portcullises with `wall_stone_arch_door.tscn`, exterior `DirectionalLight3D` from the town/church must not bleed into the crypt. Because `GothicChurch` nave floor tiles and church perimeter walls are double-sided and cast shadows, sunlight does not reach the crypt. However, crypt chamber lanterns should maintain localized attenuation radii ($\le 12.0\text{m}$) so subterranean chambers retain grimdark contrast.
2. **Camera Collision on Stairs:**
   The stair colliders created by `_create_trimesh_prefab()` use a sloped convex ramp plane `StairRampCollider` (lines 366–395 in `build_prefabs_and_level.gd`). With floor slabs removed, the player character body will glide smoothly up and down the ramp without step-jitter.
3. **Save File Compatibility:**
   Level prefabs baked into `town_overworld.tscn` will update upon running the builder tool. Runtime procedural dungeons generated via `procedural_dungeon_generator.gd` will immediately benefit without requiring database migrations.

---

## 4. Conclusion (Surgical Implementation Diffs)

### Fix 1: `scripts/ui/gothic_hud_overhaul.gd`
**Target Lines:** 503–536  
**Change:** Dynamically size plaque width based on font text metrics.

```gdscript
<<<< BEFORE (Line 506)
	var plaque_w: float = 540.0
	var plaque_h: float = 36.0
	var p_rect: Rect2 = Rect2((vp.x - plaque_w) * 0.5, 18.0, plaque_w, plaque_h)
	var a: float = biome_header_alpha
==== AFTER
	var full_header: String = "── ❖ %s : %s ❖ ──" % [biome_header_title, biome_header_subtitle]
	var text_w: float = font.get_string_size(full_header, HORIZONTAL_ALIGNMENT_CENTER, -1, 13).x
	var plaque_w: float = maxf(780.0, text_w + 48.0)
	var plaque_h: float = 36.0
	var p_rect: Rect2 = Rect2((vp.x - plaque_w) * 0.5, 18.0, plaque_w, plaque_h)
	var a: float = biome_header_alpha
>>>>
```

---

### Fix 2: `tools/blender_build_voxel_town_and_loot.py`
**Target Lines:** 1392–1407  
**Change:** Replace fragile Boolean modifier with deterministic BMesh face deletion.

```python
<<<< BEFORE (Lines 1392-1407)
    # 4. Mandatory Boolean Stairwell Cutout: Size 27.6m (X) x 35.8m (Y) x 20.0m (Z) at gx = 0.0, gz = -39.9
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
    bpy.data.objects.remove(cutter, do_unlink=True)
==== AFTER
    # 4. Deterministic BMesh Stairwell Cutout: Size 27.6m (X) x 35.8m (Y) at gx = 0.0, gy = 39.9 (Godot gz = -39.9)
    # Deletes all faces in range X in [-13.8, 13.8], Y in [22.0, 57.8]
    bm_cut = bmesh.new()
    bm_cut.from_mesh(terrain_obj.data)
    faces_to_delete = [
        f for f in bm_cut.faces
        if -13.8 <= f.calc_center_median().x <= 13.8 and 22.0 <= f.calc_center_median().y <= 57.8
    ]
    bmesh.ops.delete(bm_cut, geom=faces_to_delete, context='FACES')
    verts_to_delete = [v for v in bm_cut.verts if len(v.link_faces) == 0]
    bmesh.ops.delete(bm_cut, geom=verts_to_delete, context='VERTS')
    bm_cut.to_mesh(terrain_obj.data)
    bm_cut.free()
    terrain_obj.data.update()
>>>>
```

---

### Fix 3: `scripts/world/procedural_dungeon_generator.gd`

#### A. Floor Slab Prevention on Stairs (Line 901):
```gdscript
<<<< BEFORE (Line 901)
		if is_outer_bottom or is_balcony_floor:
==== AFTER
		if (is_outer_bottom or is_balcony_floor) and not stair_cells.has(cell) and not stair_cells.has(below_cell):
>>>>
```

#### B. Wall Sealer Corridor Stair Bypass (Lines 1002–1137):
Define helper `_is_stair_passage_boundary(cell: Vector3i, face_dir: Vector3i, stair_cells: Dictionary[Vector3i, int]) -> bool`:
```gdscript
func _is_stair_passage_boundary(cell: Vector3i, face_dir: Vector3i, stair_cells: Dictionary[Vector3i, int]) -> bool:
	if stair_cells.has(cell):
		var rot_deg: int = stair_cells[cell]
		var b_entry: Vector3i = _get_stair_bottom_entry_cell(cell, rot_deg)
		if (b_entry - cell) == face_dir:
			return true
	var below: Vector3i = Vector3i(cell.x, cell.y - 1, cell.z)
	if stair_cells.has(below):
		var rot_deg: int = stair_cells[below]
		var t_land: Vector3i = _get_stair_top_landing_cell(below, rot_deg)
		if (t_land - cell) == face_dir:
			return true
	return false
```
In `_seal_voxel_cells()`, check `_is_stair_passage_boundary` before placing `ProcWallN`, `ProcWallS`, `ProcWallW`, or `ProcWallE`. If true, skip wall placement.

#### C. `OSSUARY_L_CATACOMB` 2-Tier Carve (Lines 1912–1920):
```gdscript
<<<< BEFORE (Lines 1912-1920)
		"OSSUARY_L_CATACOMB":
			# 4x4 footprint with top-right 2x2 quadrant (dx in 2..3, dz in 0..1) left un-carved -> 90-degree L-bend
			for dx: int in range(w):
				for dz: int in range(l):
					var is_uncarved_quadrant: bool = (dx >= 2 and dz <= 1)
					if is_uncarved_quadrant:
						continue
					occupied_cells[Vector3i(gx + dx, gy, gz + dz)] = true
==== AFTER
		"OSSUARY_L_CATACOMB":
			# 4x4 footprint with top-right 2x2 quadrant (dx in 2..3, dz in 0..1) left un-carved -> 90-degree L-bend
			for dx: int in range(w):
				for dz: int in range(l):
					var is_uncarved_quadrant: bool = (dx >= 2 and dz <= 1)
					if is_uncarved_quadrant:
						continue
					for dy: int in range(h):
						occupied_cells[Vector3i(gx + dx, gy + dy, gz + dz)] = true
>>>>
```

---

### Fix 4: `tools/build_prefabs_and_level.gd`

#### A. Clear Church-to-Crypt Stairwell Passage (Lines 3014–3024):
```gdscript
<<<< BEFORE (Lines 3014-3024)
	# Register Church Nave Stairwell Entry cell (0, 0, -5) and seal stairwell collar at Z in [-24, -20], X in [-2, +2]
	_register_crypt_room_cell(occupied_cells, 0, 0, -5, "ch1")
	_spawn_prefab(root, ch1, p_wall_solid, "StairwellWallSouth", Vector3(0.0, -0.65, -19.55))
	_spawn_prefab(root, ch1, p_wall_solid, "StairwellWallWest", Vector3(-2.0, 0.0, -22.0), 90.0)
	_spawn_prefab(root, ch1, p_wall_solid, "StairwellWallEast", Vector3(2.0, 0.0, -22.0), 90.0)
	_spawn_prefab(root, ch1, p_wall_solid, "StairwellNorthBulkheadWall", Vector3(0.0, 4.0, -24.05))
	_spawn_prefab(root, ch1, p_vault_corr, "StairwellUpperVault", Vector3(0.0, 8.0, -22.0))
	var collar_ceil_n: Node3D = _spawn_prefab(root, ch1, p_floor, "StairwellCollarCeilNorth", Vector3(0.0, 4.0, -26.05))
	collar_ceil_n.scale = Vector3(1.015, 1.0, 1.015)
	_spawn_prefab(root, ch1, p_lantern, "LanternStairwell", Vector3(0.0, 2.4, -20.25), 0.0)
==== AFTER
	# Register Church Nave Stairwell Entry cell (0, 0, -5) with unobstructed passage into Crypt
	_register_crypt_room_cell(occupied_cells, 0, 0, -5, "stair_church_crypt")
	open_passages[_wall_grid_key(Vector3(0.0, 0.0, -20.0))] = true
	open_passages[_wall_grid_key(Vector3(0.0, 0.0, -22.0))] = true
	open_passages[_wall_grid_key(Vector3(0.0, 4.0, -22.0))] = true
	open_passages[_wall_grid_key(Vector3(0.0, 4.0, -24.0))] = true

	_spawn_prefab(root, ch1, p_wall_solid, "StairwellWallWest", Vector3(-2.0, 0.0, -22.0), 90.0)
	_spawn_prefab(root, ch1, p_wall_solid, "StairwellWallEast", Vector3(2.0, 0.0, -22.0), 90.0)
	_spawn_prefab(root, ch1, p_vault_corr, "StairwellUpperVault", Vector3(0.0, 8.0, -22.0))
	_spawn_prefab(root, ch1, p_lantern, "LanternStairwell", Vector3(0.0, 2.4, -20.25), 0.0)
>>>>
```

#### B. Crypt Auto-Sealer Floor and Exterior Wall Safeguards (Lines 2379–2427):
```gdscript
<<<< BEFORE (Line 2381)
		var below_cell: Vector3i = Vector3i(cell.x, cell.y - 1, cell.z)
		if occupied_cells.get(below_cell, "") != group_id and not placed_floors.has(cell):
==== AFTER
		var is_stair_cell: bool = group_id.begins_with("stair_") or (cell == Vector3i(0, 0, -5))
		var below_cell: Vector3i = Vector3i(cell.x, cell.y - 1, cell.z)
		if not is_stair_cell and occupied_cells.get(below_cell, "") != group_id and not placed_floors.has(cell):
>>>>
```
```gdscript
<<<< BEFORE (Line 2418)
			if n_group.is_empty():
				# Exterior boundary face: MUST be sealed by a solid wall (never open or portcullis)
==== AFTER
			if n_group.is_empty():
				if open_passages.has(w_key):
					continue
				# Exterior boundary face: MUST be sealed by a solid wall (never open or portcullis)
>>>>
```

#### C. Catacomb Portcullis Replacement & Headroom Clearance:
- In Chamber 5 (line 3277): Replace `p_portcullis` at `Ch5PortcullisSouthStairs` with `p_wall_door`.
- In Chamber 6 (line 3342): Replace `p_portcullis` at `Ch6PortcullisSouth` with `p_wall_door`.
- In Chamber 7 (lines 3418–3421): Replace `p_portcullis` at `Ch7PortcullisSouthStairs` with `p_wall_door`, and delete `Ch7WallSouthHighStairBulkhead`. Register `open_passages[_wall_grid_key(Vector3(-12.0, -4.0, -62.0))] = true`.
- In Chamber 8 (lines 3500–3503): Replace `p_portcullis` at `Ch8PortcullisSouthEntrance` with `p_wall_door`, and delete `Ch8WallSouthHighCenter`. Register `open_passages[_wall_grid_key(Vector3(0.0, -4.0, -62.0))] = true`.

---

## 5. Verification Method

1. **CLI Static Typing & Syntax Verification (`AGENTS.md` Rule 5):**
   ```bash
   godot --headless --path . --check-only -s res://scripts/ui/gothic_hud_overhaul.gd
   godot --headless --path . --check-only -s res://scripts/world/procedural_dungeon_generator.gd
   godot --headless --path . --check-only -s res://tools/build_prefabs_and_level.gd
   ```
   **Expected Result:** Exit code 0, zero parser warnings, zero static typing errors.

2. **Town & Level Bake Test:**
   ```bash
   godot --headless --path . -s res://tools/build_prefabs_and_level.gd
   ```
   Inspect generated nodes under `town_overworld.tscn`:
   - Confirm `StairwellWallSouth` and `StairwellNorthBulkheadWall` are absent.
   - Confirm `AutoSealFloor_0_0_-5` is absent.
   - Confirm `Ch7WallSouthHighStairBulkhead` and `Ch8WallSouthHighCenter` are absent.
   - Confirm `Ch5PortcullisSouthStairs`, `Ch6PortcullisSouth`, `Ch7PortcullisSouthStairs`, and `Ch8PortcullisSouthEntrance` are instances of `wall_stone_arch_door.tscn`.

3. **HUD Compass String Rendering Verification:**
   Launch the game or trigger the HUD with `biome_header_title = "SUBTERRANEAN CATACOMB SANCTUMS"` and `biome_header_subtitle = "EIGHT PORTAL CHAMBERS (SAFE HARBOUR)"`.
   Inspect `res://.mcp_captures/latest_frame.png` or editor viewport to confirm the header banner spans $\ge 780\text{px}$ and displays the full text with trailing `"(SAFE HARBOUR)"` completely visible without ellipses or clipping.
