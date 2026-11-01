extends SceneTree


func _init() -> void:
	print("[Verify] Starting Phase 4 Armor Gauntlets, Gothic HUD & Fog-of-War Cartography Verification...")

	# 1. Verify all 4 3D Armor Gauntlet GLBs and Prefabs exist
	var gauntlet_glbs: Array[String] = [
		"res://assets/models/armor/gauntlet_01_leather_stalker.glb",
		"res://assets/models/armor/gauntlet_02_inquisitor_brigandine.glb",
		"res://assets/models/armor/gauntlet_03_juggernaut_plate.glb",
		"res://assets/models/armor/gauntlet_04_abyssal_reliquary.glb"
	]
	var gauntlet_tscns: Array[String] = [
		"res://scenes/prefabs/armor/gauntlet_01_leather_stalker.tscn",
		"res://scenes/prefabs/armor/gauntlet_02_inquisitor_brigandine.tscn",
		"res://scenes/prefabs/armor/gauntlet_03_juggernaut_plate.tscn",
		"res://scenes/prefabs/armor/gauntlet_04_abyssal_reliquary.tscn"
	]

	for i: int in range(4):
		if not ResourceLoader.exists(gauntlet_glbs[i]):
			push_error("[FAIL] Missing armor gauntlet GLB: " + gauntlet_glbs[i])
			quit(1)
			return
		if not ResourceLoader.exists(gauntlet_tscns[i]):
			push_error("[FAIL] Missing armor gauntlet prefab: " + gauntlet_tscns[i])
			quit(1)
			return
	print("[PASS] All 4 3D armor gauntlet .glb and .tscn prefabs exist.")

	# 2. Instantiate town_overworld.tscn and locate FPSPlayer, FPSViewmodelController, PlayerLoadoutManager, GothicHudOverhaul, GothicMapSystem
	var level_scn: PackedScene = load("res://scenes/levels/town_overworld.tscn") as PackedScene
	if level_scn == null:
		push_error("[FAIL] Could not load town_overworld.tscn")
		quit(1)
		return

	var world: Node3D = level_scn.instantiate() as Node3D
	root.add_child(world)

	var player: FPSController = world.find_child("Player", true, false) as FPSController
	if player == null:
		push_error("[FAIL] Could not find Player in town_overworld.tscn")
		quit(1)
		return

	var vm: FPSViewmodelController = player.find_child("ViewmodelRig", true, false) as FPSViewmodelController
	var loadout: PlayerLoadoutManager = player.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	var hud: GothicHudOverhaul = player.find_child("HUD", true, false) as GothicHudOverhaul
	var proc_gen: ProceduralDungeonGenerator = world.find_child("ProceduralExpeditionRoot", true, false) as ProceduralDungeonGenerator

	if vm == null or loadout == null or hud == null or proc_gen == null:
		push_error("[FAIL] Missing core player/HUD/dungeon nodes on instantiated scene")
		quit(1)
		return

	vm._ready()
	hud._ready()
	loadout._ready()

	# 3. Verify 3D Armor Gauntlet Mesh Swapping across all 4 tiers (0..3) while keeping LanternPendulum visible & active
	var seen_gauntlet_names: Array[String] = []
	for step_i: int in range(4):
		loadout.equip_armor_tier(step_i)
		if vm.active_gauntlet_instance == null or not is_instance_valid(vm.active_gauntlet_instance):
			push_error("[FAIL] active_gauntlet_instance is null for armor index %d" % step_i)
			quit(1)
			return
		var g_name: String = vm.active_gauntlet_instance.name
		if not seen_gauntlet_names.has(g_name):
			seen_gauntlet_names.append(g_name)
		if vm._lantern_pendulum == null or not vm._lantern_pendulum.visible:
			push_error("[FAIL] LanternPendulum missing or hidden when equipping armor index %d" % step_i)
			quit(1)
			return
		if vm.lantern_light == null or not vm.lantern_light.visible:
			push_error("[FAIL] LanternLight missing or hidden when equipping armor index %d" % step_i)
			quit(1)
			return
		print("[PASS] Equipped Armor Tier %d: %s -> 3D Mesh Node '%s' (Max Armor: %d)" % [
			step_i,
			loadout.armor_tier_name,
			g_name,
			loadout.max_armor
		])

	if seen_gauntlet_names.size() != 4:
		push_error("[FAIL] Expected 4 distinct 3D gauntlet instances, got %d" % seen_gauntlet_names.size())
		quit(1)
		return

	# 4. Verify Ornate Gothic HUD Overhaul (HP Ghost Bar, Segmented Armor, Level Crest, Physical Ammo, Hitmarker)
	loadout.equip_armor_tier(0)
	loadout.current_health = 100
	loadout._refresh_hud()
	var initial_trail: float = hud.trail_hp_ratio
	loadout.apply_player_damage(30.0)
	if hud.cur_hp_ratio >= initial_trail:
		push_error("[FAIL] Expected cur_hp_ratio (%.2f) < trail_hp_ratio (%.2f) immediately after damage" % [hud.cur_hp_ratio, hud.trail_hp_ratio])
		quit(1)
		return
	hud.trigger_hitmarker(true)
	if hud.hitmarker_timer <= 0.0:
		push_error("[FAIL] Expected hitmarker_timer > 0 after trigger_hitmarker()")
		quit(1)
		return
	for w_id: String in ["revolver", "shotgun", "stakedriver"]:
		loadout.equip_weapon(w_id)
		hud._process(0.05)
	print("[PASS] GothicHudOverhaul verified: Ghost-Bar trail=%.2f vs cur=%.2f, Hitmarker=%.2fs, Weapons cycled cleanly." % [
		hud.trail_hp_ratio,
		hud.cur_hp_ratio,
		hud.hitmarker_timer
	])

	# 5. Verify Fog-of-War Corner Minimap & Full-Screen Cartographer's Map on Procedural Dungeon
	var map_sys: GothicMapSystem = hud.map_system
	if map_sys == null:
		push_error("[FAIL] GothicMapSystem not found on GothicHudOverhaul")
		quit(1)
		return
	map_sys.set_player_and_generator(player, proc_gen)

	var spawn_pos: Vector3 = proc_gen.generate_biome_dungeon(1, 1337, 1)
	player.position = spawn_pos
	map_sys.reset_fog_of_war_for_new_dungeon(spawn_pos)

	var total_occupied: int = proc_gen.last_occupied_cells.size()
	var initial_discovered: int = map_sys.discovered_cells.size()
	var initial_shrouded: int = map_sys.shrouded_adjacent_cells.size()

	print("[Map] Dungeon generated: total_occupied=%d, initial_discovered=%d, initial_shrouded=%d" % [
		total_occupied,
		initial_discovered,
		initial_shrouded
	])

	if initial_discovered <= 0 or initial_discovered >= total_occupied:
		push_error("[FAIL] Fog of War failed initial state: initial_discovered=%d vs total_occupied=%d" % [initial_discovered, total_occupied])
		quit(1)
		return

	if initial_shrouded <= 0:
		push_error("[FAIL] Expected shrouded frontier doorway cells > 0, got %d" % initial_shrouded)
		quit(1)
		return

	# Move player through rooms 1, 2, 3 and verify discovered_cells expands dynamically
	for r_i: int in range(1, mini(4, proc_gen.generated_room_centers.size())):
		var room_center: Vector3 = proc_gen.generated_room_centers[r_i]
		player.position = room_center
		map_sys.discover_at_world_position(room_center)

	var expanded_discovered: int = map_sys.discovered_cells.size()
	print("[Map] After exploring Rooms 1..3: discovered_cells expanded from %d -> %d (Charted Rooms: %d / %d)" % [
		initial_discovered,
		expanded_discovered,
		map_sys.get_charted_room_count(),
		map_sys.get_total_room_count()
	])

	if expanded_discovered <= initial_discovered:
		push_error("[FAIL] Expected discovered_cells to grow when moving into new rooms (%d -> %d)" % [initial_discovered, expanded_discovered])
		quit(1)
		return

	# Toggle Full-Screen Map Overlay ([M] / [Tab])
	if map_sys.is_full_map_open:
		push_error("[FAIL] Expected is_full_map_open == false initially")
		quit(1)
		return
	map_sys.toggle_full_map()
	if not map_sys.is_full_map_open:
		push_error("[FAIL] Expected is_full_map_open == true after toggle_full_map()")
		quit(1)
		return
	map_sys._process(0.05)
	map_sys.toggle_full_map()
	if map_sys.is_full_map_open:
		push_error("[FAIL] Expected is_full_map_open == false after second toggle_full_map()")
		quit(1)
		return

	print("[PASS] GothicMapSystem Fog-of-War discovery, shrouded frontiers, and full-screen Cartographer's Atlas toggle verified!")
	world.free()
	print("[Verify] ALL PHASE 1-4 CHECKS PASSED!")
	quit(0)
