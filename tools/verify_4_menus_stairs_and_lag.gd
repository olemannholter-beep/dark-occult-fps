extends SceneTree


func _count_omni_lights(node: Node) -> int:
	var count: int = 0
	if node is OmniLight3D:
		count += 1
	for child: Node in node.get_children():
		count += _count_omni_lights(child)
	return count


func _compute_combined_aabb_height(root: Node3D) -> float:
	var min_y: float = 99999.0
	var max_y: float = -99999.0
	var found: bool = false
	var stack: Array[Node] = [root]
	while not stack.is_empty():
		var cur: Node = stack.pop_back()
		if cur is MeshInstance3D:
			var mi: MeshInstance3D = cur as MeshInstance3D
			if mi.mesh != null and mi.visible:
				var aabb: AABB = mi.get_aabb()
				var rel_y: float = mi.position.y
				min_y = minf(min_y, rel_y + aabb.position.y)
				max_y = maxf(max_y, rel_y + aabb.position.y + aabb.size.y)
				found = true
		for child: Node in cur.get_children():
			stack.append(child)
	if not found:
		return 0.0
	return max_y - min_y


func _init() -> void:
	print("[Verify] Starting Phase 4 Verification: Stairs, Missing Church Tile, Zero-OmniLight Lag Fix & 4 Separate Menus...")

	var level_scn: PackedScene = load("res://scenes/levels/town_overworld.tscn") as PackedScene
	if level_scn == null:
		printerr("[FAIL] Could not load res://scenes/levels/town_overworld.tscn")
		quit(1)
		return

	var level: Node3D = level_scn.instantiate() as Node3D
	root.add_child(level)

	for _f: int in range(4):
		await physics_frame
		await process_frame

	# -------------------------------------------------------------------------
	# ASSERTION 1: FPSPlayer / Player floor_max_angle & floor_snap_length
	# -------------------------------------------------------------------------
	var player: CharacterBody3D = level.find_child("Player", true, false) as CharacterBody3D
	if player == null:
		player = level.find_child("FPSPlayer", true, false) as CharacterBody3D
	if player == null:
		printerr("[FAIL] Player (CharacterBody3D) not found in town_overworld.tscn")
		quit(1)
		return

	var min_angle_rad: float = deg_to_rad(52.0)
	if player.floor_max_angle < min_angle_rad or player.floor_snap_length < 0.55:
		printerr(
			"[FAIL] FPSPlayer stair settings invalid: floor_max_angle=%.2f deg, floor_snap_length=%.2f"
			% [rad_to_deg(player.floor_max_angle), player.floor_snap_length]
		)
		quit(1)
		return
	print(
		"[PASS 1/5] FPSPlayer stair parameters verified: floor_max_angle=%.1f deg, floor_snap_length=%.2fm"
		% [rad_to_deg(player.floor_max_angle), player.floor_snap_length]
	)

	# -------------------------------------------------------------------------
	# ASSERTION 2: Raycast South of Church-to-Crypt Stairs & Baptismal Font Alcove
	# -------------------------------------------------------------------------
	var church_node: Node3D = level.find_child("GothicChurch", true, false) as Node3D
	var church_base_y: float = church_node.global_position.y if church_node != null else 4.0
	var space_state: PhysicsDirectSpaceState3D = level.get_world_3d().direct_space_state
	var south_before_stairs_pt: Vector3 = Vector3(0.0, church_base_y, -46.0)
	var ray_q: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		south_before_stairs_pt + Vector3(0.0, 1.0, 0.0),
		south_before_stairs_pt + Vector3(0.0, -1.0, 0.0),
		1
	)
	var exclude_rids: Array[RID] = [player.get_rid()]
	ray_q.exclude = exclude_rids
	var hit: Dictionary = space_state.intersect_ray(ray_q)
	if hit.is_empty():
		printerr("[FAIL] Missing floor tile South of Church-to-Crypt stairs at (0, %.1f, -46)!" % church_base_y)
		quit(1)
		return
	var hit_pos: Vector3 = hit.get("position", Vector3.ZERO) as Vector3
	var local_hit_y: float = hit_pos.y - church_base_y
	if absf(local_hit_y) > 0.35:
		printerr("[FAIL] Floor raycast at (0, %.1f, -46) hit unexpected local Y=%.3f" % [church_base_y, local_hit_y])
		quit(1)
		return

	var font_node: Node3D = level.find_child("HubSanctuaryUpgradeFont", true, false) as Node3D
	if font_node == null:
		font_node = level.find_child("church_baptismal_font", true, false) as Node3D
	if font_node == null:
		printerr("[FAIL] HubSanctuaryUpgradeFont / church_baptismal_font not found in town_overworld.tscn")
		quit(1)
		return
	if absf(font_node.position.x) < 5.5:
		printerr("[FAIL] Baptismal Font is blocking central aisle: position=%s" % str(font_node.position))
		quit(1)
		return
	print(
		"[PASS 2/5] Church floor tile before stairs sealed (local hit Y=%.3f) & Baptismal Font in side alcove (%s)"
		% [local_hit_y, str(font_node.position)]
	)

	# -------------------------------------------------------------------------
	# ASSERTION 3: Simulate FPSPlayer Walking Up and Down stairs_stone_4x4
	# -------------------------------------------------------------------------
	var test_stage: Node3D = Node3D.new()
	test_stage.name = "StairTestStage"
	test_stage.position = Vector3(400.0, 80.0, 400.0)
	root.add_child(test_stage)

	var floor_scn: PackedScene = load("res://scenes/prefabs/architecture/floor_stone_4x4.tscn") as PackedScene
	var stairs_scn: PackedScene = load("res://scenes/prefabs/architecture/stairs_stone_4x4.tscn") as PackedScene
	var bottom_floor: Node3D = floor_scn.instantiate() as Node3D
	bottom_floor.position = Vector3(0.0, 0.0, -4.0)
	test_stage.add_child(bottom_floor)

	var stair_inst: Node3D = stairs_scn.instantiate() as Node3D
	stair_inst.position = Vector3(0.0, 4.0, 0.0)
	test_stage.add_child(stair_inst)

	var top_floor: Node3D = floor_scn.instantiate() as Node3D
	top_floor.position = Vector3(0.0, 4.0, 4.0)
	test_stage.add_child(top_floor)

	await physics_frame
	await physics_frame

	player.set_physics_process(false)

	# Walk UP the stairs (from Z = -3.2, Y = 0.08 toward Z = +3.2, Y = +4.0)
	player.global_position = test_stage.global_position + Vector3(0.0, 0.10, -3.2)
	player.velocity = Vector3.ZERO
	await physics_frame

	var dt: float = 1.0 / 60.0
	for _step: int in range(110):
		player.velocity.x = 0.0
		player.velocity.z = 5.8
		if not player.is_on_floor():
			player.velocity.y -= 20.0 * dt
		var was_fl: bool = player.is_on_floor()
		player.move_and_slide()
		if was_fl and player.velocity.y <= 0.0:
			player.apply_floor_snap()
		if player.has_method("_apply_stair_step_up_assist"):
			player.call("_apply_stair_step_up_assist", Vector3(0.0, 0.0, 1.0))
		await physics_frame

	var reached_top_y: float = player.global_position.y - test_stage.global_position.y
	if reached_top_y < 3.85:
		printerr("[FAIL] Player failed to walk up stairs to Y=4.0m (reached Y=%.2fm)" % reached_top_y)
		quit(1)
		return

	# Walk DOWN the stairs (from Z = +2.8, Y = 4.05 toward Z = -3.0, Y = 0.0)
	player.global_position = test_stage.global_position + Vector3(0.0, 4.08, 2.8)
	player.velocity = Vector3.ZERO
	await physics_frame
	player.apply_floor_snap()
	await physics_frame

	var floor_contact_frames: int = 0
	var total_descent_frames: int = 90
	for _step2: int in range(total_descent_frames):
		var was_fl2: bool = player.is_on_floor()
		player.velocity.x = 0.0
		player.velocity.z = -5.4
		if not was_fl2:
			player.velocity.y -= 20.0 * dt
		else:
			player.velocity.y = -0.2
		player.move_and_slide()
		if was_fl2 and player.velocity.y <= 0.0:
			player.apply_floor_snap()
		if player.is_on_floor():
			floor_contact_frames += 1
		await physics_frame

	player.set_physics_process(true)

	var contact_ratio: float = float(floor_contact_frames) / float(total_descent_frames)
	if contact_ratio < 0.80:
		printerr("[FAIL] Player lost floor contact descending stairs (contact_ratio=%.2f)" % contact_ratio)
		quit(1)
		return
	print(
		"[PASS 3/5] Staircase ascent (reached Y=+%.2fm without jumping) & descent (%.0f%% floor contact) verified"
		% [reached_top_y, contact_ratio * 100.0]
	)

	# -------------------------------------------------------------------------
	# ASSERTION 4: Zero OmniLight3D on OccultEnemyAI, EnemyProjectile & LootDropPickup
	# -------------------------------------------------------------------------
	var enemy_scn: PackedScene = load("res://scenes/prefabs/enemies/enemy_03_reliquary_hexweaver.tscn") as PackedScene
	var enemy_inst: OccultEnemyAI = enemy_scn.instantiate() as OccultEnemyAI
	enemy_inst.is_champion = true
	test_stage.add_child(enemy_inst)
	await process_frame
	if enemy_inst.has_method("configure_for_biome_tier"):
		enemy_inst.call("configure_for_biome_tier", 3, true)

	var proj_inst: EnemyProjectile = EnemyProjectile.new()
	test_stage.add_child(proj_inst)
	await process_frame

	var loot_inst: LootDropPickup = LootDropPickup.new()
	loot_inst.drop_category = "crafting_resource"
	loot_inst.resource_key = "soul_cores"
	test_stage.add_child(loot_inst)
	await process_frame

	var enemy_lights: int = _count_omni_lights(enemy_inst)
	var proj_lights: int = _count_omni_lights(proj_inst)
	var loot_lights: int = _count_omni_lights(loot_inst)
	var loot_aabb_h: float = _compute_combined_aabb_height(loot_inst)

	if enemy_lights != 0 or proj_lights != 0 or loot_lights != 0:
		printerr(
			"[FAIL] OmniLight3D count must be 0: enemy=%d, projectile=%d, loot=%d"
			% [enemy_lights, proj_lights, loot_lights]
		)
		quit(1)
		return
	if loot_aabb_h > 0.90:
		printerr("[FAIL] LootDropPickup still has tall cone mesh: AABB height=%.2fm (> 0.90m)" % loot_aabb_h)
		quit(1)
		return
	print(
		"[PASS 4/5] Zero OmniLight3D verified (enemy=0, projectile=0, loot=0) & LootDropPickup AABB height=%.2fm (<= 0.90m)"
		% loot_aabb_h
	)

	# -------------------------------------------------------------------------
	# ASSERTION 5: 4 Distinct Menus & < 0.2ms Hidden loadout_changed Signal Cost
	# -------------------------------------------------------------------------
	var loadout_mgr: PlayerLoadoutManager = player.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	var char_menu: GothicCharacterMenu = level.find_child("GothicCharacterMenu", true, false) as GothicCharacterMenu
	if char_menu == null:
		char_menu = player.find_child("GothicCharacterMenu", true, false) as GothicCharacterMenu
	if char_menu == null or loadout_mgr == null:
		printerr("[FAIL] Could not find GothicCharacterMenu or PlayerLoadoutManager")
		quit(1)
		return

	# Ensure closed first and benchmark hidden loadout_changed emission
	char_menu.set_menu_open(false)
	var t0_usec: int = Time.get_ticks_usec()
	for _i: int in range(10):
		loadout_mgr.loadout_changed.emit()
	var avg_hidden_ms: float = float(Time.get_ticks_usec() - t0_usec) / 10000.0
	if avg_hidden_ms >= 0.20:
		printerr("[FAIL] Emitting loadout_changed while hidden took %.4f ms (>= 0.20 ms)" % avg_hidden_ms)
		quit(1)
		return

	# 5A. Pressing [C] opens MODE_FIELD_CHARACTER with 0 forge buttons
	char_menu.toggle_menu()
	var mode_c: int = char_menu.current_menu_mode
	var c_forge_btns: int = char_menu.get_visible_forge_button_count()
	if mode_c != GothicCharacterMenu.MODE_FIELD_CHARACTER or c_forge_btns != 0:
		printerr("[FAIL] [C] menu mode=%d (expected 0) or visible forge buttons=%d (expected 0)" % [mode_c, c_forge_btns])
		quit(1)
		return
	char_menu.set_menu_open(false)

	# 5B. Interacting with the 3 Church stations opens MODE_GUNSMITH_WORKBENCH, MODE_ARMORER_STAND, MODE_BAPTISMAL_ASTROLABE
	var gunsmith_station: SanctuaryForgeStation = level.find_child("HubWeaponWorkbench", true, false) as SanctuaryForgeStation
	var armory_station: SanctuaryForgeStation = level.find_child("HubArmorReliquaryStand", true, false) as SanctuaryForgeStation
	var font_station: SanctuaryForgeStation = level.find_child("HubSanctuaryUpgradeFont", true, false) as SanctuaryForgeStation

	if gunsmith_station == null or armory_station == null or font_station == null:
		printerr("[FAIL] Missing one of the 3 Church SanctuaryForgeStation nodes")
		quit(1)
		return

	gunsmith_station.interact(loadout_mgr)
	if char_menu.current_menu_mode != GothicCharacterMenu.MODE_GUNSMITH_WORKBENCH or char_menu._left_wing_panel.visible:
		printerr("[FAIL] Gunsmith station did not open MODE_GUNSMITH_WORKBENCH cleanly")
		quit(1)
		return

	armory_station.interact(loadout_mgr)
	if char_menu.current_menu_mode != GothicCharacterMenu.MODE_ARMORER_STAND or not char_menu._left_wing_panel.visible or char_menu._weapon_card_panels[0].visible:
		printerr("[FAIL] Armory station did not open MODE_ARMORER_STAND cleanly")
		quit(1)
		return

	font_station.interact(loadout_mgr)
	if char_menu.current_menu_mode != GothicCharacterMenu.MODE_BAPTISMAL_ASTROLABE or char_menu._left_wing_panel.visible or not char_menu._spell_card_panels[0].visible:
		printerr("[FAIL] Baptismal Font station did not open MODE_BAPTISMAL_ASTROLABE cleanly")
		quit(1)
		return

	print(
		"[PASS 5/5] 4 Separate Menus verified (Field Character=0 forge btns, Gunsmith=1, Armory=2, Baptismal=3) & hidden loadout_changed=%.4f ms (< 0.20 ms)"
		% avg_hidden_ms
	)
	print("ALL 5 VERIFICATION ASSERTIONS PASSED!")
	quit(0)
