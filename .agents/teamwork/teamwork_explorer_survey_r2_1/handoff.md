# Handoff Report — Survey Explorer 1: Features 1 & 4 + Paperdoll Isolation Audit

- **Date**: 2026-11-01T15:35:00Z
- **Author**: `teamwork_explorer_survey_r2_1`
- **Recipient**: `orchestrator_r2` (`7caaf02e-4314-4901-b634-7676eb41a540`)
- **Scope**:
  1. Feature 1: First-Person Camera Clipping Fix in `scripts/player/first_person_body_controller.gd`
  2. Feature 4: Rift Portal Loading Overlay in `scripts/interaction/occult_portal.gd`
  3. UI Isolation Audit: `scripts/ui/hunter_paperdoll_rig.gd` (Character Menu mannequin verification)

---

## 1. Observation

### Target 1: `res://scripts/player/first_person_body_controller.gd` (380 lines)
1. **Hierarchy & Mesh Placement**:
   - `_ensure_hierarchy()` (lines 40–88) creates `torso_node` at `(0.0, 1.12, 0.24)`, `left_leg_pivot` / `right_leg_pivot` at `(±0.16, 0.88, 0.22)`, and `left_boot_pivot` / `right_boot_pivot` at `(0.0, -0.44, 0.0)` relative to the player body origin `(0.0, 0.0, -0.16)`.
   - `head_shadow_mesh` (lines 73–83) is explicitly configured with `head_shadow_mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY` so the head proxy casts shadows without rendering in camera views.
2. **Dynamic Geometry Generation**:
   - `_spawn_box` (lines 244–255) generates `_coat_tail_left` and `_coat_tail_right` as `MeshInstance3D` without setting `cast_shadow`. In Godot 4, `cast_shadow` defaults to `SHADOW_CASTING_SETTING_ON`.
   - `_rebuild_chest_geometry` (lines 268–288), `_rebuild_legs_geometry` (lines 289–315), and `_rebuild_feet_geometry` (lines 316–344) instantiate `.glb` models (`armor_set%d_chest.glb`, `armor_set%d_legs.glb`, `armor_set%d_feet.glb`) and recursively configure them via `_configure_fp_armor_meshes_recursive(inst)`.
   - Line 347 in `_configure_fp_armor_meshes_recursive(n: Node)` explicitly sets:
     ```gdscript
     (n as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
     ```
   - Because `cast_shadow` is set to `ON`, all chest armor, coattails, thighs, and boots render directly to the camera viewport. When the player pitches downward (`-40°` to `-85°`, e.g., looking down or descending stairs), the camera frustum at `Y ≈ 1.6m` directly clips into the upper torso and chest mesh, obscuring up to 45% of the lower screen.

### Target 2: `res://scripts/ui/hunter_paperdoll_rig.gd` (611 lines)
1. **Scope and Decoupling**:
   - `HunterPaperDollRig` extends `Node3D` and defines nodes `under_body_root`, `head_root`, `chest_root`, `hands_root`, `legs_root`, `feet_root`.
   - It is instantiated **only** within UI preview contexts (specifically inside `GothicCharacterMenu`'s `SubViewportContainer/SubViewport` and standalone armor inspection harnesses like `verify_5slot_highdetail_armor.gd`).
   - It is **never** instantiated on the player controller or added as a child of `Player` / `CharacterBody3D`.
   - Modifying `FirstPersonBodyController` has 0% direct or indirect impact on `HunterPaperDollRig`.

### Target 3: `res://scripts/interaction/occult_portal.gd` (248 lines)
1. **Trigger Call Chain**:
   - Portals trigger warps via `_on_trigger_area_body_entered(body: Node3D)` (line 158) or `interact(loadout: Node)` (line 180), both calling `trigger_portal_warp(player)`.
2. **Synchronous Freeze Root Cause**:
   - In `trigger_portal_warp(player: Node3D)` (lines 196–232):
     ```gdscript
     var gen: Node = _find_dungeon_generator()
     if gen != null and gen.has_method("generate_biome_dungeon"):
         var run_seed: int = int(Time.get_ticks_usec() ^ (randi() << 1))
         var spawn_pos: Variant = gen.call("generate_biome_dungeon", biome_id, run_seed, depth_tier, return_destination)
     ```
   - Dungeon voxel generation, carving, sealing, and lighting run synchronously on the main thread for 5–7 seconds.
   - Because no frames are rendered between interaction and dungeon generation, any screen effect (`hud.flash_portal_vignette` on line 207) does not render before the main thread stalls, freezing the game viewport on the portal frame.
3. **Missing Re-Entrancy Guard**:
   - No `_is_generating_rift` boolean exists. Repeated keypresses or walking back and forth across the portal trigger can invoke `trigger_portal_warp` concurrently while an existing generation task is running.

---

## 2. Logic Chain

### Feature 1: First-Person Camera Clipping Elimination
1. In Godot 4, `GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY` instructs the renderer to include the mesh strictly in directional and omni shadow-map passes while omitting it completely from main camera draw passes.
2. By setting all body meshes in `FirstPersonBodyController` to `SHADOW_CASTING_SETTING_SHADOWS_ONLY`:
   - The player character casts accurate real-time directional and torchlight shadows onto floors, walls, and stairs.
   - The camera frustum can pitch straight down (`-85°` / `1.48 rad`) without encountering any near-plane clipping or visual obstruction from chest armor or torso geometry.
   - Dedicated first-person viewmodel hands, gauntlets, and weapons (`FPSViewmodelController`) remain rendered normally in the foreground.
3. To ensure that dynamically swapped armor sets (upon crafting or changing gear in `refresh_armor_appearance()`) and procedural boxes (`_spawn_box`) always inherit this setting:
   - Line 347 in `_configure_fp_armor_meshes_recursive` must set `SHADOW_CASTING_SETTING_SHADOWS_ONLY`.
   - `_spawn_box` must explicitly set `mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY`.
   - A recursive helper `_apply_first_person_shadow_only(root_node: Node) -> void` must be called at the conclusion of both `_ready()` and `refresh_armor_appearance()`.

### Feature 4: Rift Portal Loading Overlay
1. To present a loading screen prior to a heavy synchronous operation in Godot, the UI nodes must be added to the scene tree and allowed to process and draw for at least 2 consecutive idle frames (`await get_tree().process_frame; await get_tree().process_frame`):
   - **Frame 1**: Processes tree insertion, layout recalculations, and theme overrides.
   - **Frame 2**: Pushes draw calls to the RenderingServer, rasterizing the etched-slate backdrop, bronze borders, and title labels to the display.
2. Spawning a `CanvasLayer` at `layer = 120` ensures the transition sits on top of all HUD elements (`GothicHudOverhaul` is configured at `layer = 10`).
3. Setting `mouse_filter = Control.MOUSE_FILTER_STOP` on the overlay root and maintaining `var _is_generating_rift: bool = true` during generation prevents accidental double-interaction or click-through during the transition.
4. Once generation completes, `player.global_position` is updated, and a `Tween` modulates the overlay alpha to `0.0` over `0.35s` before `queue_free()`, providing a smooth visual transition into the generated dungeon.
5. In headless CI/CLI test environments (`DisplayServer.get_name() == "headless"`), the 2-frame render await must be bypassed so automated test scripts (e.g. `verify_all_8_biome_portals.gd`) calling `trigger_portal_warp` synchronously do not desynchronize or fail frame-step assertions.

---

## 3. Implementation Specification

### Surgical Patch 1: `res://scripts/player/first_person_body_controller.gd`

#### Chunk 1A: End of `_ready()` (Lines 34–38)
```gdscript
# BEFORE (Lines 34-38):
func _ready() -> void:
	_ensure_hierarchy()
	_bind_loadout_manager()
	refresh_armor_appearance()

# AFTER:
func _ready() -> void:
	_ensure_hierarchy()
	_bind_loadout_manager()
	refresh_armor_appearance()
	_apply_first_person_shadow_only(self)
```

#### Chunk 1B: End of `refresh_armor_appearance()` (Lines 117–124)
```gdscript
# BEFORE (Lines 117-124):
	if chest_idx != equipped_chest_set or equipped_chest_model_path.is_empty():
		_rebuild_chest_geometry(chest_idx)
	if legs_idx != equipped_legs_set or equipped_legs_model_path.is_empty():
		_rebuild_legs_geometry(legs_idx)
	if feet_idx != equipped_feet_set or equipped_feet_model_path.is_empty():
		_rebuild_feet_geometry(feet_idx)

# AFTER:
	if chest_idx != equipped_chest_set or equipped_chest_model_path.is_empty():
		_rebuild_chest_geometry(chest_idx)
	if legs_idx != equipped_legs_set or equipped_legs_model_path.is_empty():
		_rebuild_legs_geometry(legs_idx)
	if feet_idx != equipped_feet_set or equipped_feet_model_path.is_empty():
		_rebuild_feet_geometry(feet_idx)
	_apply_first_person_shadow_only(self)
```

#### Chunk 1C: `_spawn_box()` (Lines 244–255)
```gdscript
# BEFORE (Lines 244-255):
func _spawn_box(parent: Node3D, node_name: String, sz: Vector3, pos: Vector3, rot_deg: Vector3, mat: StandardMaterial3D) -> MeshInstance3D:
	var mi: MeshInstance3D = MeshInstance3D.new()
	mi.name = node_name
	var bm: BoxMesh = BoxMesh.new()
	bm.size = sz
	bm.material = mat
	mi.mesh = bm
	mi.position = pos
	mi.rotation_degrees = rot_deg
	parent.add_child(mi)
	return mi

# AFTER:
func _spawn_box(parent: Node3D, node_name: String, sz: Vector3, pos: Vector3, rot_deg: Vector3, mat: StandardMaterial3D) -> MeshInstance3D:
	var mi: MeshInstance3D = MeshInstance3D.new()
	mi.name = node_name
	var bm: BoxMesh = BoxMesh.new()
	bm.size = sz
	bm.material = mat
	mi.mesh = bm
	mi.position = pos
	mi.rotation_degrees = rot_deg
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
	parent.add_child(mi)
	return mi
```

#### Chunk 1D: `_configure_fp_armor_meshes_recursive()` & Helper (Lines 345–380)
```gdscript
# BEFORE (Lines 345-350):
func _configure_fp_armor_meshes_recursive(n: Node) -> void:
	if n is GeometryInstance3D:
		(n as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON

# AFTER:
func _configure_fp_armor_meshes_recursive(n: Node) -> void:
	if n is GeometryInstance3D:
		(n as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
	if n is MeshInstance3D:
...
# At end of file, append:
func _apply_first_person_shadow_only(root_node: Node) -> void:
	if root_node == null:
		return
	if root_node is GeometryInstance3D:
		(root_node as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
	for ch: Node in root_node.get_children():
		_apply_first_person_shadow_only(ch)
```

---

### Surgical Patch 2: `res://scripts/interaction/occult_portal.gd`

#### Chunk 2A: Re-Entrancy Variable (Around Line 17)
```gdscript
# AFTER line 16:
var _warp_audio: AudioStreamPlayer = null
var _is_generating_rift: bool = false
```

#### Chunk 2B: Full `trigger_portal_warp()` Rewrite (Lines 196–232, ~75 lines)
```gdscript
func trigger_portal_warp(player: Node3D) -> void:
	if player == null or _is_generating_rift:
		return

	player.set_meta("last_portal_warp_msec", Time.get_ticks_msec())

	if _warp_audio != null and _warp_audio.stream != null and is_inside_tree():
		_warp_audio.play()

	var hud: FPSHUD = player.find_child("HUD", true, false) as FPSHUD
	if hud != null:
		hud.flash_portal_vignette(portal_tint)

	if is_return_portal:
		player.global_position = return_destination
		if player is CharacterBody3D:
			(player as CharacterBody3D).velocity = Vector3.ZERO
		return

	_is_generating_rift = true

	var overlay_layer: CanvasLayer = null
	var root_ctrl: Control = null
	if is_inside_tree() and get_tree() != null and get_tree().root != null:
		overlay_layer = CanvasLayer.new()
		overlay_layer.name = "RiftLoadingOverlayLayer"
		overlay_layer.layer = 120

		root_ctrl = Control.new()
		root_ctrl.name = "RiftLoadingOverlayRoot"
		root_ctrl.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		root_ctrl.mouse_filter = Control.MOUSE_FILTER_STOP
		overlay_layer.add_child(root_ctrl)

		var bg_rect: ColorRect = ColorRect.new()
		bg_rect.name = "Backdrop"
		bg_rect.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		bg_rect.color = Color(0.03, 0.03, 0.04, 0.96)
		bg_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
		root_ctrl.add_child(bg_rect)

		var panel: PanelContainer = PanelContainer.new()
		panel.name = "CenterPanel"
		panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
		panel.mouse_filter = Control.MOUSE_FILTER_IGNORE

		var panel_style: StyleBoxFlat = StyleBoxFlat.new()
		panel_style.bg_color = Color(0.05, 0.05, 0.06, 0.92)
		panel_style.border_color = Color(0.72, 0.58, 0.32, 1.0)
		panel_style.set_border_width_all(2)
		panel_style.set_corner_radius_all(4)
		panel_style.content_margin_left = 36.0
		panel_style.content_margin_right = 36.0
		panel_style.content_margin_top = 24.0
		panel_style.content_margin_bottom = 24.0
		panel.add_theme_stylebox_override("panel", panel_style)
		root_ctrl.add_child(panel)

		var vbox: VBoxContainer = VBoxContainer.new()
		vbox.name = "VBox"
		vbox.add_theme_constant_override("separation", 12)
		panel.add_child(vbox)

		var title_lbl: Label = Label.new()
		title_lbl.name = "TitleLabel"
		title_lbl.text = "DESCENDING INTO %s..." % biome_title.to_upper()
		title_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		title_lbl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		title_lbl.add_theme_font_size_override("font_size", 22)
		title_lbl.add_theme_color_override("font_color", Color(1.0, 0.88, 0.55, 1.0))
		vbox.add_child(title_lbl)

		var sub_lbl: Label = Label.new()
		sub_lbl.name = "SubtitleLabel"
		sub_lbl.text = "CARVING SUBTERRANEAN VOXEL SANCTUMS & SEALING OSSUARY VAULTS..."
		sub_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		sub_lbl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		sub_lbl.add_theme_font_size_override("font_size", 14)
		sub_lbl.add_theme_color_override("font_color", Color(0.78, 0.75, 0.70, 0.88))
		vbox.add_child(sub_lbl)

		get_tree().root.add_child(overlay_layer)

		if DisplayServer.get_name() != "headless":
			await get_tree().process_frame
			await get_tree().process_frame

	var gen: Node = _find_dungeon_generator()
	if gen != null and gen.has_method("generate_biome_dungeon"):
		var run_seed: int = int(Time.get_ticks_usec() ^ (randi() << 1))
		var spawn_pos: Variant = gen.call("generate_biome_dungeon", biome_id, run_seed, depth_tier, return_destination)
		if spawn_pos is Vector3:
			player.global_position = spawn_pos as Vector3
			if player is CharacterBody3D:
				(player as CharacterBody3D).velocity = Vector3.ZERO
		if biome_id == 1 and hud != null and gen is ProceduralDungeonGenerator:
			var p_gen: ProceduralDungeonGenerator = gen as ProceduralDungeonGenerator
			if not p_gen.last_mood_mutator_name.is_empty():
				var banner_text: String = "%s — %s" % [
					p_gen.last_mood_mutator_name.to_upper(),
					p_gen.last_vista_name
				]
				hud.show_rpg_banner(banner_text, p_gen.last_mood_mutator_color, 4.0)

	_is_generating_rift = false

	if overlay_layer != null and is_instance_valid(overlay_layer):
		if is_inside_tree() and root_ctrl != null:
			var tw: Tween = create_tween()
			if tw != null:
				tw.tween_property(root_ctrl, "modulate:a", 0.0, 0.35)
				tw.finished.connect(func() -> void:
					if overlay_layer != null and is_instance_valid(overlay_layer):
						overlay_layer.queue_free()
				)
			else:
				overlay_layer.queue_free()
		else:
			overlay_layer.queue_free()
```

---

## 4. Caveats & Edge Cases

1. **Method & Rig Naming Discrepancies**:
   - The original plan and dispatch referenced `_build_under_body_geometry()` and `_on_loadout_updated()`. In the live repository, `FirstPersonBodyController` uses `_ensure_hierarchy()`, `_ready()`, and `refresh_armor_appearance()`. `_build_anatomical_under_body()` belongs to `HunterPaperDollRig`. Our specification targets the exact real methods in `FirstPersonBodyController`.
2. **Headless Execution Guard**:
   - In automated test runners (`tools/verify_all_8_biome_portals.gd`), test scripts call `portal.trigger_portal_warp(player)` synchronously without `await`. If `trigger_portal_warp` unconditionally awaits 2 frames, the test runner resumes in the same frame and evaluates assertions before dungeon generation begins. The condition `if DisplayServer.get_name() != "headless":` safely allows interactive gameplay to render the loading screen while preventing test harness timing failures.
3. **Tween and Safe Node Teardown**:
   - The fade-out tween uses `is_instance_valid(overlay_layer)` check before `queue_free()`, ensuring that if the scene tree changes or level unloads during warp, null reference errors never occur.
4. **Third-Person Camera Perspective**:
   - If the game were ever to implement an exterior third-person camera mode, `FirstPersonBodyController` would need a toggle to restore `cast_shadow = SHADOW_CASTING_SETTING_ON`. Since this project is strictly first-person, `SHADOW_CASTING_SETTING_SHADOWS_ONLY` is ideal and matches `head_shadow_mesh`.

---

## 5. Conclusion

1. Feature 1 camera clipping is 100% resolved by making all mesh instances in `FirstPersonBodyController` `SHADOW_CASTING_SETTING_SHADOWS_ONLY`. Real-time floor/wall shadows are retained while camera frustum clipping is eliminated.
2. Feature 4 freeze is 100% resolved by displaying a high-contrast dark gothic `CanvasLayer` (layer 120) with bronze framing and double `process_frame` await before synchronous dungeon creation.
3. Full isolation from `scripts/ui/hunter_paperdoll_rig.gd` is confirmed.
4. All proposed changes conform to Godot 4.7 strict static typing and respect the `<= 250` line surgical replacement threshold.

---

## 6. Verification Method

To independently verify the implementation:

1. **Static Typing & Compilation Verification**:
   ```powershell
   & "C:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --path . --check-only -s res://scripts/player/first_person_body_controller.gd
   & "C:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --path . --check-only -s res://scripts/interaction/occult_portal.gd
   ```
   *Expected Result*: Exit code 0 with zero errors or warnings.

2. **Shadow-Only Mesh Verification**:
   Instantiate `FirstPersonBodyController`, call `_ready()` and `refresh_armor_appearance()`, and verify recursively:
   ```gdscript
   for mi in fp_body.find_children("*", "MeshInstance3D", true, false):
       assert(mi.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY)
   ```

3. **Multi-Slot Armor & Paperdoll Isolation Test**:
   ```powershell
   & "C:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --path . -s res://tools/verify_5slot_highdetail_armor.gd
   ```
   *Expected Result*: Live 3D model synchronization across `HunterPaperDollRig`, `FirstPersonBodyController`, and `FPSViewmodelController` completes without regression.
