# Forensic Audit Report — Milestone 5 (Round 2 Gameplay, Stairwell & Visual Fixes)

- **Auditor**: `teamwork_auditor_r2_1`
- **Working Directory**: `c:\Users\olema\Downloads\alpha branch\.agents\teamwork\teamwork_auditor_r2_1`
- **Work Product**: 10 Modified Files for Milestone 5:
  1. `scripts/player/first_person_body_controller.gd`
  2. `scripts/ui/gothic_hud_overhaul.gd`
  3. `scripts/world/procedural_dungeon_generator.gd`
  4. `tools/build_prefabs_and_level.gd`
  5. `scripts/interaction/occult_portal.gd`
  6. `scripts/player/fps_viewmodel_controller.gd`
  7. `tools/blender_build_voxel_enemies.py`
  8. `tools/blender_build_voxel_town_and_loot.py`
  9. `scripts/items/loot_drop_pickup.gd`
  10. `scenes/levels/town_overworld.tscn`
- **Profile**: General Project (Development Mode per `ORIGINAL_REQUEST.md`)
- **Verdict**: **CLEAN**

---

### Phase Results

- **Static Typing & AGENTS.md Compliance**: PASS — Full explicit static typing across all 7 GDScript files; zero untyped `var`; zero Godot 3.x legacy syntax; zero fabricated `uid://` strings.
- **Hardcoded Output Detection**: PASS — Zero hardcoded test outputs or synthetic pass strings.
- **Facade Detection**: PASS — All functions implement genuine, authentic game and geometry logic.
- **Pre-populated Artifact Detection**: PASS — No pre-populated logs or result files found.
- **Model Geometry & Voxel Forensics**: PASS — Genuine BMesh face deletion in `tools/blender_build_voxel_town_and_loot.py`; genuine BLOCKS octree remeshing in `tools/blender_build_voxel_enemies.py`; discrete faceted micro-voxel geometry confirmed empirically (>79% to 89% discrete faceted faces).
- **Headless CLI Check-Only**: PASS — All 7 GDScript files exit code 0 under `Godot_v4.7.2-stable_win64_console.exe --headless --path . --check-only`.
- **Empirical Oracle Verification**: PASS — 61 of 61 assertions passed cleanly in `tools/verify_challenger_m5_empirics.gd` with 0 failures.

---

## 1. Observation

### 1.1 Direct Source Inspections

1. **`scripts/player/first_person_body_controller.gd`**:
   - Lines 34–39:
     ```gdscript
     func _ready() -> void:
     	_ensure_hierarchy()
     	_bind_loadout_manager()
     	refresh_armor_appearance()
     	_apply_first_person_shadow_only(self)
     ```
   - Lines 124: `_apply_first_person_shadow_only(self)` called at the end of `refresh_armor_appearance()`.
   - Lines 255: `mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY` in `_spawn_box()`.
   - Lines 348–350: `(n as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY` in `_configure_fp_armor_meshes_recursive()`.
   - Lines 385–391:
     ```gdscript
     func _apply_first_person_shadow_only(root_node: Node) -> void:
     	if root_node == null:
     		return
     	if root_node is GeometryInstance3D:
     		(root_node as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
     	for ch: Node in root_node.get_children():
     		_apply_first_person_shadow_only(ch)
     ```
   - All variable and constant declarations are explicitly typed; zero untyped `var`.

2. **`scripts/ui/gothic_hud_overhaul.gd`**:
   - Lines 503–536:
     ```gdscript
     func _draw_top_biome_plaque(c: Control, vp: Vector2, font: Font) -> void:
     	if font == null:
     		return
     	var full_header: String = "── ❖ %s : %s ❖ ──" % [biome_header_title, biome_header_subtitle]
     	var text_w: float = font.get_string_size(full_header, HORIZONTAL_ALIGNMENT_CENTER, -1, 13).x
     	var plaque_w: float = maxf(780.0, text_w + 48.0)
     	var plaque_h: float = 36.0
     	var p_rect: Rect2 = Rect2((vp.x - plaque_w) * 0.5, 18.0, plaque_w, plaque_h)
     ```
   - Dynamically calculates pixel string metrics via `font.get_string_size()`, enforces a minimum of 780.0px with 48.0px padding, eliminating any truncation.

3. **`scripts/world/procedural_dungeon_generator.gd`**:
   - Lines 729–743:
     ```gdscript
     func _is_stair_passage_boundary(cell: Vector3i, face_dir: Vector3i, stair_cells: Dictionary[Vector3i, int]) -> bool:
     	if stair_cells.has(cell):
     		var rot_deg: int = stair_cells[cell]
     		var b_entry: Vector3i = _get_stair_bottom_entry_cell(cell, rot_deg)
     		var b_dir: Vector3i = b_entry - cell
     		if face_dir == b_dir or face_dir == -b_dir:
     			return true
     	var below: Vector3i = Vector3i(cell.x, cell.y - 1, cell.z)
     	if stair_cells.has(below):
     		var rot_deg: int = stair_cells[below]
     		var b_entry: Vector3i = _get_stair_bottom_entry_cell(below, rot_deg)
     		var b_dir: Vector3i = b_entry - below
     		if face_dir == b_dir or face_dir == -b_dir:
     			return true
     	return false
     ```
   - Lines 918 & 949: Floor slabs and pit balcony railings explicitly check `and not stair_cells.has(cell) and not stair_cells.has(below_cell)`.
   - Lines 1020, 1054, 1088, 1122: Wall generation checks `not _is_stair_passage_boundary(cell, face_dir, stair_cells)` before spawning walls across stair entries/exits.
   - Lines 1936–1937: `OSSUARY_L_CATACOMB` carves `for dy in range(h): occupied_cells[Vector3i(gx + dx, gy + dy, gz + dz)] = true`, eliminating single-tier corridor bulkhead blockages.

4. **`tools/build_prefabs_and_level.gd`**:
   - Lines 2380–2382:
     ```gdscript
     var is_stair_cell: bool = group_id.begins_with("stair_") or (cell == Vector3i(0, 0, -5))
     var below_cell: Vector3i = Vector3i(cell.x, cell.y - 1, cell.z)
     if not is_stair_cell and occupied_cells.get(below_cell, "") != group_id and not placed_floors.has(cell):
     ```
   - Lines 2420–2421 & 2443: Wall sealer checks `if open_passages.has(w_key): continue` and `if not placed_walls.has(w_key) and not open_passages.has(w_key):`.
   - Lines 3018–3022: Registered `stair_church_crypt` passage keys into `open_passages`.
   - Lines 3281, 3423–3424, 3505–3506: Low portcullises converted to high open archways (`p_wall_door`), and high bulkhead positions registered into `open_passages`.

5. **`scripts/interaction/occult_portal.gd`**:
   - Line 17: `var _is_generating_rift: bool = false`.
   - Lines 211–216: Guard `if player == null or _is_generating_rift: return` and set `_is_generating_rift = true`.
   - Lines 220–279: Spawns full-screen `CanvasLayer` at `layer = 120` with dark etched-slate backdrop `ColorRect` (`Color(0.03, 0.03, 0.04, 0.96)`), `PanelContainer` with `StyleBoxFlat` border, centered `TitleLabel` (`"DESCENDING INTO %s..." % biome_title.to_upper()`), and `SubtitleLabel`.
   - Lines 280–283: `if DisplayServer.get_name() != "headless": await get_tree().process_frame; await get_tree().process_frame`.
   - Lines 301–315: Resets `_is_generating_rift = false`, animates smooth fade tween (`modulate:a` to `0.0` over `0.35s`), and frees overlay layer.

6. **`scripts/player/fps_viewmodel_controller.gd`**:
   - Lines 134–136: Declares `_weapon_mount_recoil_pos: Vector3`, `_weapon_mount_recoil_rot: Vector3`, and `_weapon_recoil_tween: Tween`.
   - Lines 939–951:
     ```gdscript
     func trigger_shoot_recoil(intensity: float = 1.0) -> void:
     	if _weapon_recoil_tween != null and _weapon_recoil_tween.is_valid():
     		_weapon_recoil_tween.kill()
     	_weapon_mount_recoil_pos = Vector3(0.0, 0.0, 0.055 * intensity)
     	_weapon_mount_recoil_rot = Vector3(deg_to_rad(5.5 * intensity), 0.0, 0.0)
     	_apply_hand_transforms()
     	_weapon_recoil_tween = create_tween()
     	_weapon_recoil_tween.set_parallel(true)
     	_weapon_recoil_tween.tween_property(self, "_weapon_mount_recoil_pos", Vector3.ZERO, 0.14).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
     	_weapon_recoil_tween.tween_property(self, "_weapon_mount_recoil_rot", Vector3.ZERO, 0.14).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
     ```
   - Lines 1018–1019: Applies `+ _weapon_mount_recoil_pos` and `+ _weapon_mount_recoil_rot` to `right_hand_pivot.position` and `rotation`.
   - Triggered at lines 1536 (`_fire_revolver`), 1606 (`_fire_shotgun`), and 1753 (`_fire_stakedriver`).

7. **`tools/blender_build_voxel_town_and_loot.py`**:
   - Lines 1417–1430:
     ```python
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
     ```
   - Genuine deterministic BMesh face and orphan vertex deletion.

8. **`tools/blender_build_voxel_enemies.py`**:
   - Lines 130–147: `remesh_to_micro_voxels(obj: bpy.types.Object, voxel_size: float = 0.010)` adds `REMESH` modifier with `mode='BLOCKS'`, dynamic octree depth `depth = max(3, min(7, int(math.ceil(math.log2(n_blocks)))))`, `scale=0.90`, and `use_smooth_shade=False`, and applies it to every primitive sub-element before hierarchy assembly.

9. **`scripts/items/loot_drop_pickup.gd`**:
   - Lines 39–47 & 60–73: Replaced `SphereMesh` with a `SurfaceTool` stepped micro-voxel box cluster (4 concentric cubic tiers, 144 vertices with strictly cardinal unit normals, zero smooth shading).

10. **`scenes/levels/town_overworld.tscn`**:
    - Header is `[gd_scene format=4]` (no fabricated `uid="..."`).
    - Ext_resources reference `type`, `path`, and `id` without fabricated UIDs.
    - Zero `[connection` blocks.

---

### 1.2 Tool Execution Results

#### Independent CLI Static Analysis (`godot --headless --path . --check-only -s <script>`)
- `scripts/player/first_person_body_controller.gd`: Exit code `0`
- `scripts/ui/gothic_hud_overhaul.gd`: Exit code `0`
- `scripts/world/procedural_dungeon_generator.gd`: Exit code `0`
- `tools/build_prefabs_and_level.gd`: Exit code `0`
- `scripts/interaction/occult_portal.gd`: Exit code `0`
- `scripts/player/fps_viewmodel_controller.gd`: Exit code `0`
- `scripts/items/loot_drop_pickup.gd`: Exit code `0`

#### Empirical Test Suite Execution (`tools/verify_challenger_m5_empirics.gd`)
```
================================================================================
>>> EMPIRICAL CHALLENGER TEST SUITE: RUNNING HEADLESS ORACLE TESTS <<<
================================================================================

--- TEST 1: FirstPersonBodyController Shadow-Only Geometry ---
  [PASS] FirstPersonBodyController has >= 3 GeometryInstance3D nodes (found 8)
  [PASS] All GeometryInstance3D on _ready() have SHADOWS_ONLY (bad: [])
  [PASS] Armor Set 0 maintains SHADOWS_ONLY on all 8 meshes
  [PASS] Armor Set 1 maintains SHADOWS_ONLY on all 8 meshes
  [PASS] Armor Set 2 maintains SHADOWS_ONLY on all 8 meshes
  [PASS] Armor Set 3 maintains SHADOWS_ONLY on all 8 meshes
  [PASS] Dynamic mesh converted to SHADOWS_ONLY via _apply_first_person_shadow_only()
  Finished Test 1.

--- TEST 2: FPSViewmodelController Mount Recoil Kick & Recovery ---
  [PASS] Initial _weapon_mount_recoil_pos is Vector3.ZERO
  [PASS] Initial _weapon_mount_recoil_rot is Vector3.ZERO
  [PASS] Recoil kick +Z is 0.055 (actual: 0.0550)
  [PASS] Recoil pitch +X is deg_to_rad(5.5) (actual: 0.0960)
  [PASS] Right hand pivot displaced towards camera by recoil
  [PASS] Right hand pivot pitched upward by recoil
  [PASS] Rapid-fire does NOT accumulate additive position drift (pos.z = 0.0550)
  [PASS] Rapid-fire does NOT accumulate additive pitch drift (rot.x = 0.0960)
  [PASS] Recoil position returns cleanly to Vector3.ZERO after tween (len: 0.000000)
  [PASS] Recoil rotation returns cleanly to Vector3.ZERO after tween (len: 0.000000)
  [PASS] Right hand pivot position returns to base position
  [PASS] Right hand pivot rotation returns to base rotation
  Finished Test 2.

--- TEST 3: OccultPortal Re-Entrancy & Loading Overlay ---
  [PASS] Initial portal._is_generating_rift is false
  [PASS] Re-entrancy guard blocks concurrent trigger_portal_warp execution
  [PASS] RiftLoadingOverlayLayer spawned on root during rift generation
  [PASS] RiftLoadingOverlayLayer has layer == 120 (actual: 120)
  [PASS] Loading overlay root has MOUSE_FILTER_STOP
  [PASS] Backdrop ColorRect has Color(0.03, 0.03, 0.04, 0.96)
  [PASS] TitleLabel has text: 'DESCENDING INTO THE ENDLESS OSSUARY...'
  [PASS] SubtitleLabel contains 'CARVING SUBTERRANEAN VOXEL SANCTUMS'
  [PASS] RiftLoadingOverlayLayer is freed after fade-out tween
  [PASS] Return portal teleports player to return_destination
  [PASS] Return portal zeroes player velocity
  [PASS] Return portal does not set _is_generating_rift
  Finished Test 3.

--- TEST 4: Micro-Voxel 3D Assets Integrity ---
  [PASS] Successfully loaded PackedScene: res://assets/models/enemies/enemy_01_ossuary_executioner.glb
  [PASS] Instantiated root is Node3D: res://assets/models/enemies/enemy_01_ossuary_executioner.glb
  [PASS] enemy_01_ossuary_executioner.glb has 12 MeshInstance3D nodes
  [PASS] enemy_01_ossuary_executioner.glb has valid material slot assignments across all surfaces
  [PASS] enemy_01_ossuary_executioner.glb has baked vertex cavity colors (Mesh.ARRAY_COLOR)
    enemy_01_ossuary_executioner.glb: 3652 total sampled faces, 2890 discrete faceted/box faces (ratio: 79.13%)
  [PASS] enemy_01_ossuary_executioner.glb has discrete faceted micro-voxel geometry (ratio: 79.13% >= 75%)
  [PASS] enemy_01_ossuary_executioner.glb preserves all 12 articulated hierarchy nodes (missing: [])
  [PASS] Successfully loaded PackedScene: res://assets/models/enemies/enemy_03_reliquary_hexweaver.glb
  [PASS] Instantiated root is Node3D: res://assets/models/enemies/enemy_03_reliquary_hexweaver.glb
  [PASS] enemy_03_reliquary_hexweaver.glb has 12 MeshInstance3D nodes
  [PASS] enemy_03_reliquary_hexweaver.glb has valid material slot assignments across all surfaces
  [PASS] enemy_03_reliquary_hexweaver.glb has baked vertex cavity colors (Mesh.ARRAY_COLOR)
    enemy_03_reliquary_hexweaver.glb: 3403 total sampled faces, 3049 discrete faceted/box faces (ratio: 89.60%)
  [PASS] enemy_03_reliquary_hexweaver.glb has discrete faceted micro-voxel geometry (ratio: 89.60% >= 75%)
  [PASS] enemy_03_reliquary_hexweaver.glb preserves all 12 articulated hierarchy nodes (missing: [])
  [PASS] Successfully loaded PackedScene: res://assets/models/items/loot_alchemical_elixir.glb
  [PASS] Instantiated root is Node3D: res://assets/models/items/loot_alchemical_elixir.glb
  [PASS] loot_alchemical_elixir.glb has 1 MeshInstance3D nodes
  [PASS] loot_alchemical_elixir.glb has valid material slot assignments across all surfaces
  [PASS] loot_alchemical_elixir.glb has baked vertex cavity colors (Mesh.ARRAY_COLOR)
    loot_alchemical_elixir.glb: 498 total sampled faces, 426 discrete faceted/box faces (ratio: 85.54%)
  [PASS] loot_alchemical_elixir.glb has discrete faceted micro-voxel geometry (ratio: 85.54% >= 75%)
  Finished Test 4.

--- TEST 5: LootDropPickup Fallback Micro-Voxel Mesh ---
  [PASS] _shared_crystal_mesh is instantiated
  [PASS] _shared_crystal_mesh is an ArrayMesh
  [PASS] _shared_crystal_mesh is NOT a SphereMesh
  [PASS] _shared_crystal_mesh has 1 surface
  [PASS] Fallback mesh has 144 vertices (4 micro-voxel boxes * 36 verts) [actual: 144]
  [PASS] Fallback mesh has 144 normals [actual: 144]
  [PASS] 100% of fallback mesh normals are strictly cardinal unit vectors (zero smooth normals)
  [PASS] LootDropPickup creates FacetedCrystalCore MeshInstance3D
  [PASS] FacetedCrystalCore uses the micro-voxel ArrayMesh
  [PASS] FacetedCrystalCore does NOT use SphereMesh
  Finished Test 5.

================================================================================
>>> EMPIRICAL TEST SUITE SUMMARY <<<
Total Assertions Passed: 61
Total Failures: 0
>>> FINAL VERDICT: ALL TESTS PASSED CLEANLY (VERDICT: APPROVE) <<<
================================================================================
```

---

## 2. Logic Chain

1. **Static Typing & Codebase Standards**:
   - Observation 1.1 shows every function signature across all modified GDScript files specifies explicit parameter types and explicit return types (`-> void`, `-> bool`, `-> MeshInstance3D`, etc.).
   - Observation 1.1 shows typed collections (`Dictionary[String, PackedScene]`, `Dictionary[String, bool]`, `Array[Vector3i]`, `Array[PackedVector3Array]`) and explicitly typed local/member variables.
   - Observation 1.2 shows all 7 files pass `godot --headless --path . --check-only` with exit code 0.
   - Observation 1.1(10) verifies zero fabricated UIDs and zero `[connection` scene blocks in `town_overworld.tscn`.
   - Step conclusion: Strict Godot 4.7 typing and codebase integrity standards are fully satisfied.

2. **Authenticity & Non-Facade Verification**:
   - Observation 1.1(1) verifies that `_apply_first_person_shadow_only()` recursively visits all child nodes and sets `cast_shadow = SHADOW_CASTING_SETTING_SHADOWS_ONLY` on every `GeometryInstance3D`.
   - Observation 1.1(2) verifies that `_draw_top_biome_plaque()` calls `font.get_string_size()` to measure header width and dynamically adjusts plaque dimensions.
   - Observation 1.1(3) & 1.1(4) verify that `_is_stair_passage_boundary()` and `open_passages` check real 3D grid vectors (`_get_stair_bottom_entry_cell`) to prevent floor/wall blockage on stair passages.
   - Observation 1.1(5) verifies that `trigger_portal_warp()` builds a full `CanvasLayer` UI hierarchy with custom `StyleBoxFlat` and centered labels, awaiting frames before heavy execution.
   - Observation 1.1(6) verifies that `trigger_shoot_recoil()` drives actual offset variables applied in `_apply_hand_transforms()` and interpolates them back via parallel `Tween`.
   - Step conclusion: Zero facades, zero dummy mocks, zero hardcoded test outputs. All logic is authentic.

3. **Voxel & BMesh Forensics**:
   - Observation 1.1(7) confirms `tools/blender_build_voxel_town_and_loot.py` utilizes `bmesh.ops.delete` targeting faces in `[-13.8, 13.8]` x `[22.0, 57.8]` and cleans unlinked vertices, providing a clean open stairwell cutout.
   - Observation 1.1(8) confirms `tools/blender_build_voxel_enemies.py` applies `REMESH` with `mode='BLOCKS'` and dynamic octree depths on primitives before joining into articulated hierarchies.
   - Observation 1.2 confirms through empirical sampling in Test 4 that `enemy_01`, `enemy_03`, and `loot_alchemical_elixir` possess 79.13% to 89.60% discrete faceted micro-voxel faces with baked cavity vertex colors and 12 intact articulated hierarchy nodes.
   - Step conclusion: 3D model generation and micro-voxel forensics are fully genuine and verified.

---

## 3. Caveats

1. **Unmodified Code Finding (`ReliquaryChest.reward_scale`)**:
   - In `scripts/world/procedural_dungeon_generator.gd` (lines 2331 and 2379, unedited during this milestone), code assigns `rc.reward_scale = reward_sc` on instances of `ReliquaryChest`.
   - `scripts/interaction/reliquary_chest.gd` defines `@export var depth_scale: float = 1.0` and does not declare `reward_scale`.
   - When generating procedural dungeons with reward scaling, Godot prints a runtime script error:
     `Invalid assignment of property or key 'reward_scale' with value of type 'float' on a base object of type 'StaticBody3D (ReliquaryChest)'.`
   - Per auditor constraints ("Audit-only — do NOT modify implementation code"), this is recorded as an observation for follow-up, not modified. It does not constitute an integrity violation under Development mode.

2. **Dungeon Generator Multi-Warp Lifecycle (`OccultPortal.is_inside_tree`)**:
   - When calling `trigger_portal_warp()` multiple times consecutively in test environments where the level or portal may be freed during generation, calling `is_inside_tree()` on `self` after generator completion should check `is_instance_valid(self)`.

---

## 4. Conclusion

The work product for Milestone 5 (5 Gameplay, Stairwell, and Visual Fixes) contains **authentic, robust implementations** that satisfy all requirements from `ORIGINAL_REQUEST.md` and `AGENTS.md`. Zero integrity violations, zero facades, zero hardcoded test strings, and zero untyped variables were detected.

**Final Verdict**: **CLEAN**

---

## 5. Verification Method

To independently re-verify all claims in this report:

1. **Verify Static Typing via Headless CLI**:
   ```powershell
   & "c:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --path . --check-only -s res://scripts/player/first_person_body_controller.gd
   & "c:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --path . --check-only -s res://scripts/ui/gothic_hud_overhaul.gd
   & "c:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --path . --check-only -s res://scripts/world/procedural_dungeon_generator.gd
   & "c:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --path . --check-only -s res://tools/build_prefabs_and_level.gd
   & "c:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --path . --check-only -s res://scripts/interaction/occult_portal.gd
   & "c:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --path . --check-only -s res://scripts/player/fps_viewmodel_controller.gd
   & "c:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --path . --check-only -s res://scripts/items/loot_drop_pickup.gd
   ```
   *Expected result*: Exit code 0 on all 7 scripts.

2. **Run Empirical Headless Oracle Tests**:
   ```powershell
   & "c:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --path . -s res://tools/verify_challenger_m5_empirics.gd
   ```
   *Expected result*: Exit code 0, 61 passed assertions, 0 failures.

3. **Inspect Models & Geometry**:
   - Inspect `tools/blender_build_voxel_town_and_loot.py` lines 1417–1430 for `bmesh.ops.delete`.
   - Inspect `tools/blender_build_voxel_enemies.py` lines 130–147 for `REMESH` `BLOCKS`.
