extends SceneTree


func _collect_meshes(node: Node, out_meshes: Array[MeshInstance3D]) -> void:
	if node is MeshInstance3D:
		out_meshes.append(node as MeshInstance3D)
	for child: Node in node.get_children():
		_collect_meshes(child, out_meshes)


func _collect_shapes(node: Node, out_shapes: Array[CollisionShape3D]) -> void:
	if node is CollisionShape3D:
		out_shapes.append(node as CollisionShape3D)
	for child: Node in node.get_children():
		_collect_shapes(child, out_shapes)


func _count_nodes_matching(node: Node, substring: String) -> int:
	var count: int = 0
	if node.name.contains(substring) or node.scene_file_path.contains(substring):
		count += 1
	for child: Node in node.get_children():
		count += _count_nodes_matching(child, substring)
	return count


func _init() -> void:
	call_deferred("_run_verification")


func _run_verification() -> void:
	print("=== [VerifyPortal1Diversity] Starting Portal 1 ('The Endless Ossuary') Diversity Verification ===")
	var failures: int = 0

	# 1. Verify all 6 bespoke Ossuary Variety .glb and .tscn prefabs exist and instantiate cleanly
	var variety_prefabs: Array[String] = [
		"res://scenes/prefabs/ossuary_variety/ossuary_stone_bridge_4x4.tscn",
		"res://scenes/prefabs/ossuary_variety/ossuary_balcony_railing_4m.tscn",
		"res://scenes/prefabs/ossuary_variety/ossuary_buttress_arch_4x4.tscn",
		"res://scenes/prefabs/ossuary_variety/ossuary_bone_chandelier.tscn",
		"res://scenes/prefabs/ossuary_variety/ossuary_spine_reliquary_monolith.tscn",
		"res://scenes/prefabs/ossuary_variety/ossuary_burial_niche_divider_4x4.tscn"
	]

	for p_path: String in variety_prefabs:
		if not ResourceLoader.exists(p_path):
			push_error("[FAIL] Missing Ossuary Variety prefab: " + p_path)
			failures += 1
			continue
		var ps: PackedScene = load(p_path) as PackedScene
		var inst: Node3D = ps.instantiate() as Node3D
		if inst == null:
			push_error("[FAIL] Could not instantiate prefab: " + p_path)
			failures += 1
			continue
		var meshes: Array[MeshInstance3D] = []
		_collect_meshes(inst, meshes)
		var shapes: Array[CollisionShape3D] = []
		_collect_shapes(inst, shapes)
		var is_chandelier: bool = p_path.ends_with("ossuary_bone_chandelier.tscn")
		if meshes.is_empty():
			push_error("[FAIL] Prefab has zero MeshInstance3D nodes: " + p_path)
			failures += 1
		if not is_chandelier and shapes.is_empty():
			push_error("[FAIL] Structural/Centerpiece prefab has zero CollisionShape3D nodes: " + p_path)
			failures += 1
		for cs: CollisionShape3D in shapes:
			if cs.shape is ConcavePolygonShape3D:
				push_error("[FAIL] Prefab uses ConcavePolygonShape3D instead of fast primitive BoxShape3D: " + p_path)
				failures += 1
		print("[PASS] Verified prefab %s (meshes=%d, primitive_colliders=%d)" % [
			p_path.get_file(),
			meshes.size(),
			shapes.size()
		])
		inst.free()

	# 2. Load town_overworld.tscn and locate ProceduralExpeditionRoot
	var level_scene: PackedScene = load("res://scenes/levels/town_overworld.tscn") as PackedScene
	if level_scene == null:
		push_error("[FAIL] Could not load town_overworld.tscn")
		quit(1)
		return

	var level: Node3D = level_scene.instantiate() as Node3D
	root.add_child(level)
	await process_frame
	await physics_frame

	var player: CharacterBody3D = level.find_child("Player", true, false) as CharacterBody3D
	var gen: ProceduralDungeonGenerator = level.find_child("ProceduralExpeditionRoot", true, false) as ProceduralDungeonGenerator
	if gen == null or player == null:
		push_error("[FAIL] Missing Player or ProceduralExpeditionRoot in town_overworld.tscn")
		quit(1)
		return

	# Prepare 26-direction spherical raycast vectors for watertight verification
	var ray_dirs: Array[Vector3] = []
	for dx: int in [-1, 0, 1]:
		for dy: int in [-1, 0, 1]:
			for dz: int in [-1, 0, 1]:
				if dx == 0 and dy == 0 and dz == 0:
					continue
				ray_dirs.append(Vector3(float(dx), float(dy), float(dz)).normalized())

	var space_state: PhysicsDirectSpaceState3D = level.get_world_3d().direct_space_state
	var seeds_to_test: Array[int] = [1001, 1002, 1003]
	var observed_vistas: Dictionary[String, bool] = {}
	var observed_mutators: Dictionary[String, bool] = {}
	var total_variety_counts: Dictionary[String, int] = {
		"ossuary_stone_bridge_4x4": 0,
		"ossuary_balcony_railing_4m": 0,
		"ossuary_buttress_arch_4x4": 0,
		"ossuary_bone_chandelier": 0,
		"ossuary_spine_reliquary_monolith": 0,
		"ossuary_burial_niche_divider_4x4": 0
	}

	# 3. Generate 3 consecutive Portal 1 dungeons with 3 different seeds
	for run_i: int in range(seeds_to_test.size()):
		var s_val: int = seeds_to_test[run_i]
		var spawn_pos: Vector3 = gen.generate_biome_dungeon(1, s_val, 1, Vector3(0.0, 0.5, -26.0))
		player.global_position = spawn_pos
		await process_frame
		await physics_frame
		await physics_frame

		observed_vistas[gen.last_vista_name] = true
		observed_mutators[gen.last_mood_mutator_name] = true

		# Count unique OSSUARY_* archetypes in this dungeon run
		var unique_ossuary_archetypes: Dictionary[String, bool] = {}
		var consecutive_repeats: int = 0
		for a_i: int in range(gen.last_spawned_archetypes.size()):
			var arch_name: String = gen.last_spawned_archetypes[a_i]
			if arch_name.begins_with("OSSUARY_") or arch_name.begins_with("VISTA_"):
				unique_ossuary_archetypes[arch_name] = true
			if a_i > 0 and gen.last_spawned_archetypes[a_i] == gen.last_spawned_archetypes[a_i - 1]:
				consecutive_repeats += 1

		if unique_ossuary_archetypes.size() < 6:
			push_error("[FAIL] Seed %d spawned fewer than 6 unique archetypes (%d)" % [s_val, unique_ossuary_archetypes.size()])
			failures += 1
		if consecutive_repeats > 0:
			push_error("[FAIL] Seed %d had %d consecutive room archetype repeats!" % [s_val, consecutive_repeats])
			failures += 1

		# Count spawned instances of all 6 new Ossuary Variety prefabs
		for key: String in total_variety_counts.keys():
			var c: int = _count_nodes_matching(gen, key)
			total_variety_counts[key] += c

		# Run 26-direction spherical raycast watertight check in every room (including chasm bridge & sunken pit rooms)
		var total_escaped: int = 0
		for r_i: int in range(gen.generated_room_centers.size()):
			var r_center: Vector3 = gen.generated_room_centers[r_i]
			var room_escaped: int = 0
			for dir: Vector3 in ray_dirs:
				var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
					r_center,
					r_center + dir * 200.0,
					1
				)
				var hit: Dictionary = space_state.intersect_ray(query)
				if hit.is_empty():
					room_escaped += 1
			total_escaped += room_escaped
			if room_escaped > 0:
				push_error("[FAIL] Seed %d Room %d (%s) leaked %d/26 spherical raycasts!" % [
					s_val,
					r_i,
					gen.last_spawned_archetypes[r_i],
					room_escaped
				])
				failures += 1

		print("[PASS] Seed %d -> Vista='%s' | Mutator='%s' | UniqueArchetypes=%d | Rooms=%d | Spawn=%s | RaycastEscaped=%d/260" % [
			s_val,
			gen.last_vista_name,
			gen.last_mood_mutator_name,
			unique_ossuary_archetypes.size(),
			gen.active_room_count,
			str(spawn_pos),
			total_escaped
		])

	if observed_vistas.size() < 3:
		push_error("[FAIL] Expected 3 distinct Starting Vista rooms across 3 seeds, got %d" % observed_vistas.size())
		failures += 1
	else:
		print("[PASS] 3 seeds produced %d distinct Starting Vista rooms: %s" % [
			observed_vistas.size(),
			str(observed_vistas.keys())
		])

	if observed_mutators.size() < 3:
		push_error("[FAIL] Expected 3 distinct Ossuary Mood Mutators across 3 seeds, got %d" % observed_mutators.size())
		failures += 1
	else:
		print("[PASS] 3 seeds rolled all %d Ossuary Mood Mutators: %s" % [
			observed_mutators.size(),
			str(observed_mutators.keys())
		])

	for key: String in total_variety_counts.keys():
		var cnt: int = total_variety_counts[key]
		if cnt <= 0:
			push_error("[FAIL] Bespoke Ossuary Variety prefab '%s' was never spawned!" % key)
			failures += 1
		else:
			print("[PASS] Bespoke Ossuary Variety prefab '%s' spawned %d times across 3 runs" % [key, cnt])

	gen.clear_generated_dungeon()
	gen._prefab_cache.clear()
	gen._sealer_mat = null
	root.remove_child(level)
	level.free()

	if failures > 0:
		push_error("=== [VerifyPortal1Diversity] FAILED with %d errors ===" % failures)
		quit(1)
	else:
		print("=== [VerifyPortal1Diversity] ALL PORTAL 1 DIVERSITY, PREFAB & WATERTIGHT CHECKS PASSED (0 ERRORS) ===")
		quit(0)
