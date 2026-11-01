extends SceneTree


func _init() -> void:
	call_deferred("_run_verification")


func _collect_enemies(node: Node, out_list: Array[Node]) -> void:
	if node is OccultEnemyAI or node is TestDummyEnemy:
		out_list.append(node)
	for child: Node in node.get_children():
		_collect_enemies(child, out_list)


func _collect_portals(node: Node, out_list: Array[OccultPortal]) -> void:
	if node is OccultPortal:
		out_list.append(node as OccultPortal)
	for child: Node in node.get_children():
		_collect_portals(child, out_list)


func _collect_hub_stations(node: Node, out_list: Array[HubStation]) -> void:
	if node is HubStation:
		out_list.append(node as HubStation)
	for child: Node in node.get_children():
		_collect_hub_stations(child, out_list)


func _collect_collision_shapes(node: Node, out_shapes: Array[Shape3D]) -> void:
	if node is CollisionShape3D:
		var cs: CollisionShape3D = node as CollisionShape3D
		if cs.shape != null:
			out_shapes.append(cs.shape)
	for child: Node in node.get_children():
		_collect_collision_shapes(child, out_shapes)


func _assert_primitive_collider_prefab(prefab_path: String) -> bool:
	var ps: PackedScene = load(prefab_path) as PackedScene
	if ps == null:
		push_error("[VerifySafeHubPerf] Failed to load prefab: " + prefab_path)
		return false
	var inst: Node = ps.instantiate()
	var shapes: Array[Shape3D] = []
	_collect_collision_shapes(inst, shapes)
	inst.free()
	if shapes.is_empty():
		push_error("[VerifySafeHubPerf] No CollisionShape3D found in: " + prefab_path)
		return false
	for sh: Shape3D in shapes:
		if sh is ConcavePolygonShape3D:
			push_error("[VerifySafeHubPerf] Forbidden ConcavePolygonShape3D found in: " + prefab_path)
			return false
		if not (sh is BoxShape3D or sh is CylinderShape3D):
			push_error("[VerifySafeHubPerf] Expected BoxShape3D or CylinderShape3D in: " + prefab_path)
			return false
	return true


func _run_verification() -> void:
	print("[VerifySafeHubPerf] Starting Safe Harbour Hub & Performance Optimization Verification...")

	# 1. Verify Fast Primitive Colliders on wall_stone_solid.tscn, floor_stone_4x4.tscn, crypt_pillar.tscn
	var p_checks: Array[String] = [
		"res://scenes/prefabs/architecture/wall_stone_solid.tscn",
		"res://scenes/prefabs/architecture/floor_stone_4x4.tscn",
		"res://scenes/prefabs/architecture/crypt_pillar.tscn"
	]
	for p_path: String in p_checks:
		if not _assert_primitive_collider_prefab(p_path):
			quit(1)
			return
	print("[VerifySafeHubPerf] Verified primitive BoxShape3D / CylinderShape3D colliders on wall, floor, and pillar prefabs.")

	# 2. Verify wall_lantern_sconce.tscn OmniLight3D Distance Fade & Shadow settings
	var sconce_ps: PackedScene = load("res://scenes/prefabs/architecture/wall_lantern_sconce.tscn") as PackedScene
	if sconce_ps == null:
		push_error("[VerifySafeHubPerf] Missing wall_lantern_sconce.tscn")
		quit(1)
		return
	var sconce_inst: Node = sconce_ps.instantiate()
	var sconce_light: OmniLight3D = sconce_inst.find_child("LanternOmniLight", true, false) as OmniLight3D
	var crackle_audio: AudioStreamPlayer3D = sconce_inst.find_child("FireCrackle3D", true, false) as AudioStreamPlayer3D
	if sconce_light == null:
		push_error("[VerifySafeHubPerf] Missing LanternOmniLight in wall_lantern_sconce.tscn")
		quit(1)
		return
	if not sconce_light.distance_fade_enabled or sconce_light.shadow_enabled:
		push_error(
			"[VerifySafeHubPerf] wall_lantern_sconce.tscn light mismatch: distance_fade_enabled=%s shadow_enabled=%s"
			% [str(sconce_light.distance_fade_enabled), str(sconce_light.shadow_enabled)]
		)
		quit(1)
		return
	if not is_equal_approx(sconce_light.distance_fade_begin, 16.0) or not is_equal_approx(sconce_light.distance_fade_shadow, 12.0) or not is_equal_approx(sconce_light.distance_fade_length, 6.0):
		push_error("[VerifySafeHubPerf] wall_lantern_sconce.tscn distance fade distances mismatch")
		quit(1)
		return
	if crackle_audio == null or crackle_audio.max_polyphony != 2 or not is_equal_approx(crackle_audio.max_distance, 10.0):
		push_error("[VerifySafeHubPerf] wall_lantern_sconce.tscn FireCrackle3D polyphony/max_distance mismatch")
		quit(1)
		return
	sconce_inst.free()
	print("[VerifySafeHubPerf] Verified wall_lantern_sconce.tscn OmniLight3D distance fade, shadow_enabled=false, and FireCrackle3D limits.")

	# 3. Instantiate town_overworld.tscn
	var level_ps: PackedScene = load("res://scenes/levels/town_overworld.tscn") as PackedScene
	if level_ps == null:
		push_error("[VerifySafeHubPerf] Failed to load town_overworld.tscn")
		quit(1)
		return

	var level: Node3D = level_ps.instantiate() as Node3D
	root.add_child(level)
	await process_frame
	await process_frame

	# 4. Assert ZERO enemies exist anywhere in the static town_overworld.tscn hub
	var static_enemies: Array[Node] = []
	_collect_enemies(level, static_enemies)
	if not static_enemies.is_empty():
		push_error("[VerifySafeHubPerf] Expected 0 static enemies in town_overworld.tscn, found %d" % static_enemies.size())
		quit(1)
		return
	print("[VerifySafeHubPerf] Verified ZERO enemy nodes exist anywhere in the static town_overworld.tscn Safe Harbour hub.")

	# 5. Assert all 8 OccultPortal nodes exist inside the 8 Crypt Chambers & all 3 HubStations exist inside Church Nave + TargetDummyPlaque
	var crypt_zone: Node3D = level.find_child("CryptPortalNexusZone", true, false) as Node3D
	var church_zone: Node3D = level.find_child("ChurchWorkshopZone", true, false) as Node3D
	var town_zone: Node3D = level.find_child("TownExteriorZone", true, false) as Node3D
	var proc_zone: ProceduralDungeonGenerator = level.find_child("ProceduralExpeditionRoot", true, false) as ProceduralDungeonGenerator

	if crypt_zone == null or church_zone == null or town_zone == null or proc_zone == null:
		push_error("[VerifySafeHubPerf] Missing one or more of the 4 logical zone roots in town_overworld.tscn")
		quit(1)
		return

	var portals: Array[OccultPortal] = []
	_collect_portals(crypt_zone, portals)
	if portals.size() != 8:
		push_error("[VerifySafeHubPerf] Expected 8 OccultPortal nodes in CryptPortalNexusZone, found %d" % portals.size())
		quit(1)
		return

	var stations: Array[HubStation] = []
	_collect_hub_stations(church_zone, stations)
	if stations.size() != 3:
		push_error("[VerifySafeHubPerf] Expected 3 HubStation nodes in ChurchWorkshopZone, found %d" % stations.size())
		quit(1)
		return

	var plaque: TargetDummyPlaque = town_zone.find_child("TargetDummyPlaque", true, false) as TargetDummyPlaque
	if plaque == null:
		push_error("[VerifySafeHubPerf] Missing TargetDummyPlaque in TownExteriorZone")
		quit(1)
		return
	plaque.take_damage(42.0, false, plaque.global_position + Vector3(0.0, 1.2, 0.0), Vector3.UP)
	if not is_equal_approx(plaque.last_hit_damage, 42.0) or not is_equal_approx(plaque.total_damage_logged, 42.0):
		push_error("[VerifySafeHubPerf] TargetDummyPlaque.take_damage failed")
		quit(1)
		return
	print("[VerifySafeHubPerf] Verified 8 Crypt Portals, 3 Church Hub Stations, and functional TargetDummyPlaque.")

	# 6. Assert WorldEnvironment & MoonDirectionalLight performance settings
	var world_env: WorldEnvironment = level.find_child("WorldEnvironment", true, false) as WorldEnvironment
	if world_env == null or world_env.environment == null:
		push_error("[VerifySafeHubPerf] Missing WorldEnvironment in town_overworld.tscn")
		quit(1)
		return
	var env: Environment = world_env.environment
	if env.sdfgi_enabled or env.ssil_enabled:
		push_error("[VerifySafeHubPerf] Expected sdfgi_enabled=false and ssil_enabled=false in WorldEnvironment")
		quit(1)
		return
	if env.ambient_light_source != Environment.AMBIENT_SOURCE_SKY or not is_equal_approx(env.ambient_light_sky_contribution, 0.65) or not is_equal_approx(env.ambient_light_energy, 0.45):
		push_error("[VerifySafeHubPerf] WorldEnvironment sky ambient settings mismatch")
		quit(1)
		return
	if not env.ssao_enabled or not is_equal_approx(env.ssao_detail, 0.25) or not env.ssr_enabled or env.ssr_max_steps != 12 or not is_equal_approx(env.volumetric_fog_length, 28.0):
		push_error("[VerifySafeHubPerf] WorldEnvironment SSAO/SSR/VolumetricFog tuning mismatch")
		quit(1)
		return

	var moon: DirectionalLight3D = level.find_child("MoonDirectionalLight", true, false) as DirectionalLight3D
	if moon == null or not is_equal_approx(moon.directional_shadow_max_distance, 38.0) or moon.directional_shadow_mode != DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS:
		push_error("[VerifySafeHubPerf] MoonDirectionalLight shadow settings mismatch")
		quit(1)
		return
	print("[VerifySafeHubPerf] Verified WorldEnvironment (sdfgi=false, ssil=false, half-res SSAO, SSR=12, VolFog=28m) and MoonDirectionalLight (38m, 2-split).")

	# 7. Simulate moving FPSPlayer across all 4 zones and verify ZonePerformanceManager culling
	var player: Node3D = level.find_child("Player", true, false) as Node3D
	var zone_mgr: ZonePerformanceManager = level.find_child("ZonePerformanceManager", true, false) as ZonePerformanceManager
	if player == null or zone_mgr == null:
		push_error("[VerifySafeHubPerf] Missing FPSPlayer or ZonePerformanceManager")
		quit(1)
		return

	# Zone A: Town Valley (Z = 18.0, Y = 1.0) -> Town + Church visible; Crypt + Procedural hidden & disabled
	player.global_position = Vector3(0.0, 1.0, 18.0)
	zone_mgr.evaluate_zones_now(player.global_position)
	if not town_zone.visible or not church_zone.visible or crypt_zone.visible or proc_zone.visible:
		push_error("[VerifySafeHubPerf] Zone A (Town Valley) visibility mismatch")
		quit(1)
		return
	if crypt_zone.process_mode != Node.PROCESS_MODE_DISABLED or proc_zone.process_mode != Node.PROCESS_MODE_DISABLED or not moon.shadow_enabled:
		push_error("[VerifySafeHubPerf] Zone A (Town Valley) process_mode or moon shadow mismatch")
		quit(1)
		return

	# Zone B: Church Workshop (X = 0.0, Y = 4.2, Z = -16.0) -> Church + Town + Crypt visible; Procedural hidden
	player.global_position = Vector3(0.0, 4.2, -16.0)
	zone_mgr.evaluate_zones_now(player.global_position)
	if not church_zone.visible or not town_zone.visible or not crypt_zone.visible or proc_zone.visible:
		push_error("[VerifySafeHubPerf] Zone B (Church Workshop) visibility mismatch")
		quit(1)
		return

	# Zone C: Crypt Portal Nexus (X = 0.0, Y = 0.2, Z = -28.0) -> Crypt visible; Town + Church + Procedural hidden & disabled; Moon shadows disabled
	player.global_position = Vector3(0.0, 0.2, -28.0)
	zone_mgr.evaluate_zones_now(player.global_position)
	if not crypt_zone.visible or town_zone.visible or church_zone.visible or proc_zone.visible:
		push_error("[VerifySafeHubPerf] Zone C (Crypt Portal Nexus) visibility mismatch")
		quit(1)
		return
	if town_zone.process_mode != Node.PROCESS_MODE_DISABLED or church_zone.process_mode != Node.PROCESS_MODE_DISABLED or moon.shadow_enabled:
		push_error("[VerifySafeHubPerf] Zone C (Crypt Portal Nexus) process_mode or moon shadow mismatch")
		quit(1)
		return

	# Zone D: Procedural Expedition (Y = -500.0) -> Trigger expedition generation & verify active enemies spawn exclusively there
	proc_zone.generate_biome_dungeon(1, 1001, 1, Vector3(1.8, 0.5, -26.5))
	await process_frame
	player.global_position = Vector3(0.0, -499.0, 0.0)
	zone_mgr.evaluate_zones_now(player.global_position)
	if not proc_zone.visible or town_zone.visible or church_zone.visible or crypt_zone.visible or moon.visible:
		push_error("[VerifySafeHubPerf] Zone D (Procedural Expedition) visibility mismatch")
		quit(1)
		return
	if town_zone.process_mode != Node.PROCESS_MODE_DISABLED or church_zone.process_mode != Node.PROCESS_MODE_DISABLED or crypt_zone.process_mode != Node.PROCESS_MODE_DISABLED:
		push_error("[VerifySafeHubPerf] Zone D (Procedural Expedition) process_mode mismatch")
		quit(1)
		return

	var proc_enemies: Array[Node] = []
	_collect_enemies(proc_zone, proc_enemies)
	if proc_enemies.size() < 6:
		push_error("[VerifySafeHubPerf] Expected >= 6 active OccultEnemyAI enemies in ProceduralExpeditionRoot, found %d" % proc_enemies.size())
		quit(1)
		return
	for en: Node in proc_enemies:
		var ai: OccultEnemyAI = en as OccultEnemyAI
		if ai == null or ai.is_passive_dummy:
			push_error("[VerifySafeHubPerf] Procedural expedition enemy is null or passive dummy")
			quit(1)
			return
	print("[VerifySafeHubPerf] Verified all 4 ZonePerformanceManager transitions and %d active OccultEnemyAI spawns inside ProceduralExpeditionRoot." % proc_enemies.size())

	level.free()
	print("[VerifySafeHubPerf] ALL SAFE HARBOUR HUB & PERFORMANCE OPTIMIZATION CHECKS PASSED!")
	quit(0)
