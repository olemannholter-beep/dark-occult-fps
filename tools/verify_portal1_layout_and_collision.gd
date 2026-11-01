extends SceneTree


func _initialize() -> void:
	call_deferred("_run_verification")


func _run_verification() -> void:
	print("[VerifyPortal1] Starting Portal 1 Layout, Stair Alignment, Prop Clearance & Collision Verification...")

	# 1. Verify stairs_stone_4x4.tscn sloped ramp collider
	var stair_scene: PackedScene = load("res://scenes/prefabs/architecture/stairs_stone_4x4.tscn") as PackedScene
	if stair_scene == null:
		push_error("[VerifyPortal1] FAILED: Could not load stairs_stone_4x4.tscn")
		quit(1)
		return

	var stair_inst: Node3D = stair_scene.instantiate() as Node3D
	root.add_child(stair_inst)
	var stair_sb: StaticBody3D = stair_inst.get_node_or_null("StaticBody3D") as StaticBody3D
	if stair_sb == null or (stair_sb.collision_layer & 1) == 0:
		push_error("[VerifyPortal1] FAILED: stairs_stone_4x4.tscn missing StaticBody3D on Layer 1")
		quit(1)
		return
	var ramp_col: CollisionShape3D = stair_sb.get_node_or_null("StairRampCollider") as CollisionShape3D
	if ramp_col == null or ramp_col.shape == null:
		push_error("[VerifyPortal1] FAILED: stairs_stone_4x4.tscn missing StairRampCollider")
		quit(1)
		return
	print("[VerifyPortal1] PASS: stairs_stone_4x4.tscn has Layer 1 StaticBody3D + 45-degree sloped StairRampCollider")
	stair_inst.queue_free()

	# 2. Generate Portal 1 across 5 seeds (101..105) and verify layout & collision invariants
	var gen: ProceduralDungeonGenerator = ProceduralDungeonGenerator.new()
	gen.name = "ProceduralDungeonGenerator"
	root.add_child(gen)

	var test_seeds: Array[int] = [101, 102, 103, 104, 105]
	var total_stairs_checked: int = 0
	var total_centerpieces_checked: int = 0
	var total_enemies_checked: int = 0

	for s_val: int in test_seeds:
		var spawn_pos: Vector3 = gen.generate_biome_dungeon(1, s_val, 1, Vector3(0.0, 0.5, -26.0))
		await process_frame
		await physics_frame

		# A. Verify every spawned stairs_stone_4x4 connects a valid bottom floor cell at gy to a valid top floor cell at gy+1
		for st_cell: Vector3i in gen.last_stair_cells.keys():
			total_stairs_checked += 1
			var st_rot: int = gen.last_stair_cells[st_cell]
			var bottom_cell: Vector3i = gen._get_stair_bottom_entry_cell(st_cell, st_rot)
			var top_cell: Vector3i = gen._get_stair_top_landing_cell(st_cell, st_rot)

			var bottom_walkable: bool = gen._is_walkable_floor_cell(
				bottom_cell,
				gen.last_occupied_cells,
				gen.last_bridge_cells,
				gen.last_balcony_floor_cells,
				gen.last_stair_cells
			)
			var top_walkable: bool = gen._is_walkable_floor_cell(
				top_cell,
				gen.last_occupied_cells,
				gen.last_bridge_cells,
				gen.last_balcony_floor_cells,
				gen.last_stair_cells
			)
			if not bottom_walkable:
				push_error("[VerifyPortal1] FAILED (seed %d): Stair at %s (rot=%d) bottom entry %s is not a walkable floor cell!" % [
					s_val, str(st_cell), st_rot, str(bottom_cell)
				])
				quit(1)
				return
			if not top_walkable:
				push_error("[VerifyPortal1] FAILED (seed %d): Stair at %s (rot=%d) top landing %s is not a walkable floor/balcony cell!" % [
					s_val, str(st_cell), st_rot, str(top_cell)
				])
				quit(1)
				return

		# B. Verify zero centerpieces (ossuary_spine_reliquary_monolith, crypt_sarcophagus_ornate) are within < 3.0m horizontally of any stairs_stone_4x4
		var arch_root: Node3D = gen.get_node_or_null("DungeonArchitecture") as Node3D
		var props_root: Node3D = gen.get_node_or_null("DungeonPropsAndClutter") as Node3D
		var enemies_root: Node3D = gen.get_node_or_null("DungeonEnemies") as Node3D

		var stair_nodes: Array[Node3D] = []
		if arch_root != null:
			for ch: Node in arch_root.get_children():
				if ch is Node3D and ch.name.begins_with("ProcStairs_"):
					stair_nodes.append(ch as Node3D)

		if props_root != null:
			for prop_ch: Node in props_root.get_children():
				if not (prop_ch is Node3D):
					continue
				var p3d: Node3D = prop_ch as Node3D
				var sc_path: String = p3d.scene_file_path
				if sc_path.ends_with("ossuary_spine_reliquary_monolith.tscn") or sc_path.ends_with("crypt_sarcophagus_ornate.tscn"):
					total_centerpieces_checked += 1
					for st_node: Node3D in stair_nodes:
						var stair_base_y: float = st_node.global_position.y - 4.0
						if absf(p3d.global_position.y - stair_base_y) < 4.5:
							var horiz_dist: float = Vector2(
								p3d.global_position.x - st_node.global_position.x,
								p3d.global_position.z - st_node.global_position.z
							).length()
							if horiz_dist < 3.0:
								push_error("[VerifyPortal1] FAILED (seed %d): Centerpiece %s at %s is within %.2fm (< 3.0m) of staircase %s at %s!" % [
									s_val, p3d.name, str(p3d.global_position), horiz_dist, st_node.name, str(st_node.global_position)
								])
								quit(1)
								return

		# C. Verify every OccultEnemyAI has collision_mask & 1 != 0 and valid non-disabled CollisionShape3D
		if enemies_root != null:
			for en_ch: Node in enemies_root.get_children():
				if en_ch is OccultEnemyAI:
					total_enemies_checked += 1
					var ai: OccultEnemyAI = en_ch as OccultEnemyAI
					if (ai.collision_mask & 1) == 0:
						push_error("[VerifyPortal1] FAILED (seed %d): Enemy %s collision_mask (%d) does not include Layer 1!" % [
							s_val, ai.name, ai.collision_mask
						])
						quit(1)
						return
					var cshape: CollisionShape3D = null
					for ch_col: Node in ai.get_children():
						if ch_col is CollisionShape3D:
							cshape = ch_col as CollisionShape3D
							break
					if cshape == null or cshape.disabled or cshape.shape == null:
						push_error("[VerifyPortal1] FAILED (seed %d): Enemy %s missing active CollisionShape3D!" % [
							s_val, ai.name
						])
						quit(1)
						return

		print("[VerifyPortal1] Seed %d OK (spawn=%s, stairs=%d, vista='%s')" % [
			s_val, str(spawn_pos), gen.last_stair_cells.size(), gen.last_vista_name
		])

	# 3. Verify EnemyProjectile shatters on Layer 1 floor/wall collision instead of flying through
	var test_floor: StaticBody3D = StaticBody3D.new()
	test_floor.collision_layer = 1
	test_floor.collision_mask = 1
	test_floor.position = Vector3(0.0, -100.0, 0.0)
	var tf_col: CollisionShape3D = CollisionShape3D.new()
	var tf_box: BoxShape3D = BoxShape3D.new()
	tf_box.size = Vector3(10.0, 0.5, 10.0)
	tf_col.shape = tf_box
	test_floor.add_child(tf_col)
	root.add_child(test_floor)

	var proj: EnemyProjectile = EnemyProjectile.new()
	proj.position = Vector3(0.0, -98.0, 0.0)
	proj.direction = Vector3(0.0, -1.0, 0.0)
	proj.speed = 20.0
	proj.damage = 15.0
	proj.orb_color = Color(0.8, 0.3, 1.0, 1.0)
	root.add_child(proj)
	if (proj.collision_mask & 1) == 0:
		push_error("[VerifyPortal1] FAILED: EnemyProjectile collision_mask does not include Layer 1!")
		quit(1)
		return

	await physics_frame
	for step_i: int in range(15):
		if is_instance_valid(proj) and not proj.is_queued_for_deletion():
			proj._physics_process(0.05)
		await physics_frame

	if is_instance_valid(proj) and not proj.is_queued_for_deletion():
		push_error("[VerifyPortal1] FAILED: EnemyProjectile flew through Layer 1 floor without shattering!")
		quit(1)
		return

	print("[VerifyPortal1] PASS: EnemyProjectile shattered cleanly upon hitting Layer 1 stone slab.")
	print("[VerifyPortal1] ALL CHECKS PASSED across 5 seeds! (stairs=%d, centerpieces=%d, enemies=%d)" % [
		total_stairs_checked, total_centerpieces_checked, total_enemies_checked
	])
	quit(0)
