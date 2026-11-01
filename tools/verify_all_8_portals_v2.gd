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


func _collect_omni_lights(node: Node, out_lights: Array[OmniLight3D]) -> void:
	if node is OmniLight3D:
		out_lights.append(node as OmniLight3D)
	for child: Node in node.get_children():
		_collect_omni_lights(child, out_lights)


func _count_nodes_matching(node: Node, substring: String) -> int:
	var count: int = 0
	if String(node.name).contains(substring) or String(node.scene_file_path).contains(substring):
		count += 1
	for child: Node in node.get_children():
		count += _count_nodes_matching(child, substring)
	return count


func _init() -> void:
	call_deferred("_run_verification")


func _run_verification() -> void:
	print("=== [VerifyAll8PortalsV2] Starting Biomes 2-4 Hero Kits & All 8 Portals V2 Vertical Voxel Verification ===")
	var failures: int = 0

	# 1. Verify all 9 bespoke Biome 2, 3, and 4 .tscn prefabs
	var hero_prefabs: Array[String] = [
		"res://scenes/prefabs/dungeon/necropolis_wall_armory_4x4.tscn",
		"res://scenes/prefabs/dungeon/necropolis_iron_maiden_monolith.tscn",
		"res://scenes/prefabs/dungeon/necropolis_hanging_war_brazier.tscn",
		"res://scenes/prefabs/dungeon/reliquary_wall_grimoire_4x4.tscn",
		"res://scenes/prefabs/dungeon/reliquary_astral_orrery_monolith.tscn",
		"res://scenes/prefabs/dungeon/reliquary_chandelier_astrolabe.tscn",
		"res://scenes/prefabs/dungeon/abattoir_wall_furnace_4x4.tscn",
		"res://scenes/prefabs/dungeon/abattoir_blood_press_monolith.tscn",
		"res://scenes/prefabs/dungeon/abattoir_hanging_hook_rack.tscn"
	]

	for p_path: String in hero_prefabs:
		if not ResourceLoader.exists(p_path):
			push_error("[FAIL] Missing hero prefab: " + p_path)
			failures += 1
			continue
		var ps: PackedScene = load(p_path) as PackedScene
		var inst: Node3D = ps.instantiate() as Node3D
		if inst == null:
			push_error("[FAIL] Could not instantiate hero prefab: " + p_path)
			failures += 1
			continue
		var meshes: Array[MeshInstance3D] = []
		_collect_meshes(inst, meshes)
		var shapes: Array[CollisionShape3D] = []
		_collect_shapes(inst, shapes)
		var lights: Array[OmniLight3D] = []
		_collect_omni_lights(inst, lights)

		var is_chandelier: bool = (
			p_path.ends_with("brazier.tscn")
			or p_path.ends_with("astrolabe.tscn")
			or p_path.ends_with("rack.tscn")
		)
		if meshes.is_empty() or meshes.size() > 8:
			push_error("[FAIL] Prefab %s mesh count %d outside [1..8]" % [p_path, meshes.size()])
			failures += 1
		if not lights.is_empty():
			push_error("[FAIL] Prefab %s contains %d OmniLight3D nodes (must be 0)" % [p_path, lights.size()])
			failures += 1
		if not is_chandelier:
			if shapes.is_empty():
				push_error("[FAIL] Wall/Monolith prefab %s missing BoxShape3D collider" % p_path)
				failures += 1
			for m: MeshInstance3D in meshes:
				if m.visibility_range_end > 0.0:
					push_error("[FAIL] Wall/Monolith mesh %s has visibility_range_end=%.1f (must be 0.0)" % [p_path, m.visibility_range_end])
					failures += 1
		print("[PASS] Hero Prefab %s (meshes=%d, colliders=%d, lights=%d)" % [
			p_path.get_file(), meshes.size(), shapes.size(), lights.size()
		])
		inst.free()

	# 2. Instantiate town_overworld.tscn and verify all 8 Biomes on V2 Vertical Voxel Engine
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

	var ray_dirs: Array[Vector3] = []
	for dx: int in [-1, 0, 1]:
		for dy: int in [-1, 0, 1]:
			for dz: int in [-1, 0, 1]:
				if dx == 0 and dy == 0 and dz == 0:
					continue
				ray_dirs.append(Vector3(float(dx), float(dy), float(dz)).normalized())

	var space_state: PhysicsDirectSpaceState3D = level.get_world_3d().direct_space_state

	var expected_biome_kits: Dictionary[int, Array] = {
		2: ["necropolis_wall_armory_4x4", "necropolis_iron_maiden_monolith", "necropolis_hanging_war_brazier"],
		3: ["reliquary_wall_grimoire_4x4", "reliquary_astral_orrery_monolith", "reliquary_chandelier_astrolabe"],
		4: ["abattoir_wall_furnace_4x4", "abattoir_blood_press_monolith", "abattoir_hanging_hook_rack"]
	}

	for b_id: int in range(1, 9):
		var spawn_pos: Vector3 = gen.generate_biome_dungeon(b_id, 2026 + b_id * 17, 1, Vector3(0.0, 0.5, -26.0))
		player.global_position = spawn_pos
		await process_frame
		await physics_frame
		await physics_frame

		if gen.active_room_count != 10 or gen.room_containers.size() != 10:
			push_error("[FAIL] Biome %d expected 10 RoomContainers, got %d" % [b_id, gen.room_containers.size()])
			failures += 1

		if gen.last_stair_cells.size() < 3:
			push_error("[FAIL] Biome %d expected >= 3 vertical staircases, got %d" % [b_id, gen.last_stair_cells.size()])
			failures += 1

		var railing_count: int = _count_nodes_matching(gen, "ossuary_balcony_railing_4m")
		if railing_count <= 0:
			push_error("[FAIL] Biome %d spawned 0 balcony railings!" % b_id)
			failures += 1

		for r_i: int in range(gen.room_containers.size()):
			var rc: Node3D = gen.room_containers[r_i]
			var r_lights: Array[OmniLight3D] = []
			_collect_omni_lights(rc, r_lights)
			if r_lights.size() > 2:
				push_error("[FAIL] Biome %d RoomContainer_%d has %d OmniLights (max 2)" % [b_id, r_i, r_lights.size()])
				failures += 1

		if expected_biome_kits.has(b_id):
			var kit_list: Array = expected_biome_kits[b_id]
			for k_name_var: Variant in kit_list:
				var k_name: String = String(k_name_var)
				var cnt: int = _count_nodes_matching(gen, k_name)
				if cnt <= 0:
					push_error("[FAIL] Biome %d did not spawn bespoke kit piece '%s'" % [b_id, k_name])
					failures += 1

		# Check 26-direction spherical raycast watertightness in every room
		var escaped_rays: int = 0
		for r_center: Vector3 in gen.generated_room_centers:
			for dir: Vector3 in ray_dirs:
				var q: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(r_center, r_center + dir * 200.0, 1)
				var hit: Dictionary = space_state.intersect_ray(q)
				if hit.is_empty():
					escaped_rays += 1
		if escaped_rays > 0:
			push_error("[FAIL] Biome %d leaked %d/260 spherical raycasts!" % [b_id, escaped_rays])
			failures += 1

		# Check Boss Sanctum Completion Chest
		var boss_chest: ReliquaryChest = gen.find_child("Room9_ReliquaryChest", true, false) as ReliquaryChest
		if boss_chest == null or not boss_chest.is_completion_chest or boss_chest.chest_biome_id != b_id:
			push_error("[FAIL] Biome %d missing Boss Sanctum Completion ReliquaryChest (Room9_ReliquaryChest)" % b_id)
			failures += 1

		# Check Map Data
		var map_data: Dictionary = gen.get_dungeon_map_data()
		if (map_data.get("occupied_cells", {}) as Dictionary).is_empty():
			push_error("[FAIL] Biome %d get_dungeon_map_data() occupied_cells is empty" % b_id)
			failures += 1

		print("[PASS] Portal %d ('%s') -> Rooms=%d | Stairs=%d | Railings=%d | EscapedRays=%d/260 | CompletionChest=OK" % [
			b_id,
			gen.last_mood_mutator_name,
			gen.active_room_count,
			gen.last_stair_cells.size(),
			railing_count,
			escaped_rays
		])

	gen.clear_generated_dungeon()
	root.remove_child(level)
	level.free()

	if failures > 0:
		push_error("=== [VerifyAll8PortalsV2] FAILED with %d errors ===" % failures)
		quit(1)
	else:
		print("=== [VerifyAll8PortalsV2] ALL 9 HERO PREFABS & ALL 8 V2 VERTICAL PORTALS VERIFIED 100% (0 ERRORS) ===")
		quit(0)
