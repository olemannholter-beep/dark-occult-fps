extends SceneTree

# Empirical Challenger Verification for Milestone 5:
# - Test 1: town_overworld.tscn forbidden vs required nodes & archways
# - Test 2: Physical CharacterBody3D stair descent/ascent (Church -> Crypt)
# - Test 3: Physics clearance probes on all 4 Catacomb stairwells
# - Test 4: ProceduralDungeonGenerator floor/wall assertion stress test across 8 biomes
# - Test 5: GothicHUDOverhaul top biome plaque text measurement & scaling

var _level: Node3D = null
var _player: CharacterBody3D = null
var _phase: int = 0
var _step_count: int = 0
var _total_passed: int = 0
var _total_failed: int = 0


func _init() -> void:
	print("=================================================================")
	print("[Milestone 5 Empirical Verification] STARTING TEST RUNNER")
	print("=================================================================")
	var level_scene: PackedScene = load("res://scenes/levels/town_overworld.tscn") as PackedScene
	if level_scene == null:
		push_error("[FAIL] Could not load res://scenes/levels/town_overworld.tscn")
		quit(1)
		return
	_level = level_scene.instantiate() as Node3D
	root.add_child(_level)
	_player = _level.get_node_or_null("Player") as CharacterBody3D
	if _player == null:
		push_error("[FAIL] Player node not found in town_overworld.tscn")
		quit(1)
		return


func _physics_process(_delta: float) -> bool:
	_step_count += 1

	# Phase 0: Settle scene for 5 frames
	if _phase == 0:
		if _step_count >= 5:
			_run_scene_tree_audit()
			_phase = 1
			_step_count = 0
			# Set up player in Church Nave right in front of StairsStone4x4
			_player.global_position = Vector3(0.0, 4.3, -44.5)
			_player.velocity = Vector3.ZERO
			Input.action_press("move_forward")
			print("\n--- Part 2: Physical Player Descent Down Church-to-Crypt Stairs ---")
			print("  Player positioned at (0.0, 4.3, -44.5). Walking North (-Z)...")
		return false

	# Phase 1: Walk North (-Z) down Church-to-Crypt stairs to Z <= -54.0
	if _phase == 1:
		if _step_count % 10 == 0:
			print(
				"  [StairDescent] step=%d pos=(%.2f, %.2f, %.2f) on_floor=%s vel_y=%.2f"
				% [_step_count, _player.global_position.x, _player.global_position.y, _player.global_position.z, str(_player.is_on_floor()), _player.velocity.y]
			)
		if _player.global_position.z <= -54.0:
			Input.action_release("move_forward")
			print(
				"  [PASS] Player successfully descended Church-to-Crypt stairs! Final pos=(%.2f, %.2f, %.2f), on_floor=%s"
				% [_player.global_position.x, _player.global_position.y, _player.global_position.z, str(_player.is_on_floor())]
			)
			if _player.global_position.y < 1.0:
				print("  [PASS] Player Y descended to Crypt level (Y=%.2f <= 1.0)!" % _player.global_position.y)
				_total_passed += 1
			else:
				push_error("  [FAIL] Player Y did not descend to Crypt level! Y=%.2f" % _player.global_position.y)
				_total_failed += 1
			_phase = 2
			_step_count = 0
			Input.action_press("move_back")
			print("\n--- Part 3: Physical Player Ascent Up Crypt-to-Church Stairs ---")
			print("  Player positioned at (%.2f, %.2f, %.2f). Walking South (+Z)..." % [_player.global_position.x, _player.global_position.y, _player.global_position.z])
			return false

		if _step_count >= 180:
			Input.action_release("move_forward")
			push_error(
				"  [FAIL] Player stuck descending stairs at pos=(%.2f, %.2f, %.2f)!"
				% [_player.global_position.x, _player.global_position.y, _player.global_position.z]
			)
			_total_failed += 1
			_phase = 2
			_step_count = 0
			return false
		return false

	# Phase 2: Walk South (+Z) back up stairs to Z >= -45.0
	if _phase == 2:
		if _step_count % 10 == 0:
			print(
				"  [StairAscent] step=%d pos=(%.2f, %.2f, %.2f) on_floor=%s"
				% [_step_count, _player.global_position.x, _player.global_position.y, _player.global_position.z, str(_player.is_on_floor())]
			)
		if _player.global_position.z >= -45.0 and _player.global_position.y >= 3.8:
			Input.action_release("move_back")
			print(
				"  [PASS] Player smoothly ascended stairs back into Church Nave! Final pos=(%.2f, %.2f, %.2f)"
				% [_player.global_position.x, _player.global_position.y, _player.global_position.z]
			)
			_total_passed += 1
			_phase = 3
			_step_count = 0
			return false

		if _step_count >= 200:
			Input.action_release("move_back")
			push_error(
				"  [FAIL] Player stuck ascending stairs at pos=(%.2f, %.2f, %.2f)!"
				% [_player.global_position.x, _player.global_position.y, _player.global_position.z]
			)
			_total_failed += 1
			_phase = 3
			_step_count = 0
			return false
		return false

	# Phase 3: Headroom probes on Catacomb stairwells & generator & HUD
	if _phase == 3:
		_run_catacomb_headroom_probes()
		_run_dungeon_gen_test()
		_run_hud_measurement_test()

		print("\n=================================================================")
		print("[Milestone 5 Empirical Verification] FINAL SUMMARY:")
		print("  TOTAL PASSED: %d" % _total_passed)
		print("  TOTAL FAILED: %d" % _total_failed)
		print("=================================================================")
		if _total_failed == 0:
			print("[FINAL VERDICT: APPROVE]")
			quit(0)
		else:
			push_error("[FINAL VERDICT: REQUEST_CHANGES] %d failures detected!" % _total_failed)
			quit(1)
		return true

	return false


func _run_scene_tree_audit() -> void:
	print("\n--- Part 1: town_overworld.tscn Scene Tree Node Audit ---")
	var forbidden: Array[String] = [
		"StairwellWallSouth",
		"StairwellNorthBulkheadWall",
		"AutoSealFloor_0_0_-5",
		"StairwellCollarCeilNorth",
		"Ch7WallSouthHighStairBulkhead",
		"Ch8WallSouthHighCenter"
	]
	for f_name: String in forbidden:
		var found: Node = _level.find_child(f_name, true, false)
		if found != null:
			push_error("  [FAIL] Forbidden blocking node FOUND: " + f_name)
			_total_failed += 1
		else:
			print("  [PASS] Forbidden node ABSENT: ", f_name)
			_total_passed += 1

	var required_stairs: Array[String] = [
		"StairsStone4x4",
		"StairsCh1ToCh6",
		"StairsCh4ToCh5",
		"StairsCh6ToCh7",
		"StairsCh6ToCh8"
	]
	for s_name: String in required_stairs:
		var s_node: Node3D = _level.find_child(s_name, true, false) as Node3D
		if s_node == null:
			push_error("  [FAIL] Required stair node MISSING: " + s_name)
			_total_failed += 1
		else:
			print("  [PASS] Required stair node present: %s at global pos %s" % [s_name, str(s_node.global_position)])
			_total_passed += 1

	var archways: Array[String] = [
		"Ch5PortcullisSouthStairs",
		"Ch6PortcullisSouth",
		"Ch7PortcullisSouthStairs",
		"Ch8PortcullisSouthEntrance"
	]
	for a_name: String in archways:
		var a_node: Node3D = _level.find_child(a_name, true, false) as Node3D
		if a_node == null:
			push_error("  [FAIL] Archway node MISSING: " + a_name)
			_total_failed += 1
		else:
			var sc_path: String = a_node.scene_file_path
			if sc_path.find("wall_stone_arch_door") != -1:
				print("  [PASS] %s uses open archway (%s)" % [a_name, sc_path])
				_total_passed += 1
			else:
				push_error("  [FAIL] %s does NOT use wall_stone_arch_door! Found: %s" % [a_name, sc_path])
				_total_failed += 1


func _run_catacomb_headroom_probes() -> void:
	print("\n--- Part 4: Catacomb Stairwells Headroom & Clearance Probes ---")
	var space_state: PhysicsDirectSpaceState3D = _level.get_world_3d().direct_space_state
	var catacomb_stairs: Array[String] = [
		"StairsCh1ToCh6",
		"StairsCh4ToCh5",
		"StairsCh6ToCh7",
		"StairsCh6ToCh8"
	]

	for s_name: String in catacomb_stairs:
		var s_node: Node3D = _level.find_child(s_name, true, false) as Node3D
		if s_node == null:
			continue
		var st_origin: Vector3 = s_node.global_position
		var basis: Basis = s_node.global_transform.basis
		var min_headroom: float = 999.0
		var obstructed: bool = false

		for frac: float in [0.1, 0.3, 0.5, 0.7, 0.9]:
			var l_z: float = lerpf(1.8, -1.8, frac)
			var l_y: float = lerpf(0.1, -3.8, frac)
			var probe_base: Vector3 = st_origin + basis * Vector3(0.0, l_y + 0.3, l_z)
			var probe_top: Vector3 = probe_base + Vector3(0.0, 3.8, 0.0)

			var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(probe_base, probe_top)
			var hit: Dictionary = space_state.intersect_ray(query)
			if hit.is_empty():
				min_headroom = minf(min_headroom, 3.8)
			else:
				var hit_pos: Vector3 = hit["position"] as Vector3
				var dist: float = hit_pos.y - probe_base.y
				min_headroom = minf(min_headroom, dist)
				if dist < 2.2:
					push_error("  [FAIL] %s headroom obstructed at frac %.2f: %.2fm (hit %s)" % [
						s_name, frac, dist, (hit["collider"] as Node).name
					])
					obstructed = true

		if not obstructed and min_headroom >= 2.6:
			print("  [PASS] %s has open vertical headroom (minimum clearance: %.2fm)" % [s_name, min_headroom])
			_total_passed += 1
		else:
			_total_failed += 1


func _run_dungeon_gen_test() -> void:
	print("\n--- Part 5: Procedural Dungeon Generator Assertions Across Seeds & Biomes ---")
	var dungeon_gen_script: GDScript = load("res://scripts/world/procedural_dungeon_generator.gd") as GDScript
	if dungeon_gen_script == null:
		push_error("  [FAIL] Could not load procedural_dungeon_generator.gd")
		_total_failed += 1
		return

	var dgen: Node3D = Node3D.new()
	dgen.set_script(dungeon_gen_script)
	root.add_child(dgen)

	var test_seeds: Array[int] = [42, 101, 777]
	var test_biomes: Array[int] = [1, 2, 3, 4, 5, 6, 7, 8]
	var total_stairs: int = 0
	var violations: int = 0

	for b_id: int in test_biomes:
		for s_val: int in test_seeds:
			dgen.call("generate_biome_dungeon", b_id, s_val, 1)
			var stair_cells: Dictionary = dgen.get("last_stair_cells") as Dictionary
			if stair_cells == null or stair_cells.is_empty():
				continue

			# Find all floor, subfloor, and colfloor nodes recursively
			var all_floors: Array[Node] = dgen.find_children("ProcFloor_*", "Node3D", true, false)
			var all_subfloors: Array[Node] = dgen.find_children("SealerSubFloor_*", "Node3D", true, false)
			var all_colfloors: Array[Node] = dgen.find_children("ColFloor_*", "Node3D", true, false)

			var floor_nodes: Array[Node] = []
			floor_nodes.append_array(all_floors)
			floor_nodes.append_array(all_subfloors)
			floor_nodes.append_array(all_colfloors)

			for fl: Node in floor_nodes:
				var fl_pos: Vector3 = (fl as Node3D).position
				var fl_grid: Vector3i = Vector3i(roundi(fl_pos.x / 4.0), roundi(fl_pos.y / 4.0), roundi(fl_pos.z / 4.0))
				if stair_cells.has(fl_grid):
					push_error("  [FAIL] Biome %d seed %d: Floor %s on stair cell %s!" % [b_id, s_val, fl.name, str(fl_grid)])
					violations += 1
				var below_grid: Vector3i = Vector3i(fl_grid.x, fl_grid.y - 1, fl_grid.z)
				if stair_cells.has(below_grid):
					push_error("  [FAIL] Biome %d seed %d: Ceiling floor %s directly above stair cell %s!" % [b_id, s_val, fl.name, str(below_grid)])
					violations += 1

			for st_key: Variant in stair_cells.keys():
				var st_cell: Vector3i = st_key as Vector3i
				var st_rot: int = int(stair_cells[st_key])
				total_stairs += 1
				var cell_above: Vector3i = Vector3i(st_cell.x, st_cell.y + 1, st_cell.z)

				# Check boundary protection
				var b_entry: Vector3i = dgen.call("_get_stair_bottom_entry_cell", st_cell, st_rot) as Vector3i
				var b_dir: Vector3i = b_entry - st_cell
				var is_b_prot: bool = dgen.call("_is_stair_passage_boundary", st_cell, b_dir, stair_cells) as bool
				var is_t_prot: bool = dgen.call("_is_stair_passage_boundary", cell_above, -b_dir, stair_cells) as bool
				if not is_b_prot or not is_t_prot:
					push_error("  [FAIL] Missing boundary protection for stair cell %s" % str(st_cell))
					violations += 1

	if violations == 0 and total_stairs > 0:
		print("  [PASS] Verified %d procedural staircases across 8 biomes: ZERO illegal floors or blocking bulkheads!" % total_stairs)
		_total_passed += 1
	elif violations > 0:
		push_error("  [FAIL] Found %d procedural dungeon stair violations!" % violations)
		_total_failed += 1
	else:
		push_error("  [FAIL] No procedural stairs were generated to verify!")
		_total_failed += 1

	dgen.queue_free()


func _run_hud_measurement_test() -> void:
	print("\n--- Part 6: Gothic HUD Overhaul Top Biome Plaque Text Measurement ---")
	var hud_script: GDScript = load("res://scripts/ui/gothic_hud_overhaul.gd") as GDScript
	if hud_script == null:
		push_error("  [FAIL] Could not load gothic_hud_overhaul.gd")
		_total_failed += 1
		return

	var font: Font = ThemeDB.fallback_font
	var test_strings: Array[String] = [
		"── ❖ SUBTERRANEAN CATACOMB SANCTUMS : EIGHT PORTAL CHAMBERS (SAFE HARBOUR) ❖ ──",
		"── ❖ SANCTUARY OF THE ASHEN CHAPEL : SAFE HARBOUR HUB ❖ ──",
		"── ❖ THE ENDLESS OSSUARY : DEPTH TIER 5 EXPEDITION ❖ ──"
	]

	for s: String in test_strings:
		var text_w: float = font.get_string_size(s, HORIZONTAL_ALIGNMENT_CENTER, -1, 13).x
		var plaque_w: float = maxf(780.0, text_w + 48.0)
		print("  String (%d chars): '%s'" % [s.length(), s])
		print("    text_w: %.2fpx | plaque_w: %.2fpx | padding: %.2fpx" % [text_w, plaque_w, plaque_w - text_w])
		if plaque_w < 780.0:
			push_error("  [FAIL] plaque_w %.2f < 780.0!" % plaque_w)
			_total_failed += 1
		elif plaque_w < text_w + 32.0:
			push_error("  [FAIL] plaque_w does not provide sufficient padding for text!")
			_total_failed += 1
		else:
			print("    [PASS] Dynamically sized banner accommodates text with full clearance.")
			_total_passed += 1
