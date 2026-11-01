extends SceneTree

const ENEMY_PREFABS: Array[String] = [
	"res://scenes/prefabs/enemies/enemy_01_ossuary_executioner.tscn",
	"res://scenes/prefabs/enemies/enemy_02_necropolis_praetorian.tscn",
	"res://scenes/prefabs/enemies/enemy_03_reliquary_hexweaver.tscn",
	"res://scenes/prefabs/enemies/enemy_04_inquisitor_rackmaster.tscn",
	"res://scenes/prefabs/enemies/enemy_05_plague_bloater.tscn",
	"res://scenes/prefabs/enemies/enemy_06_weeping_banshee.tscn",
	"res://scenes/prefabs/enemies/enemy_07_bell_juggernaut.tscn",
	"res://scenes/prefabs/enemies/enemy_08_abyssal_archon.tscn"
]


func _init() -> void:
	call_deferred("_run_verification")


func _find_first_mesh_instance(node: Node) -> MeshInstance3D:
	if node is MeshInstance3D and (node as MeshInstance3D).mesh != null:
		return node as MeshInstance3D
	for child: Node in node.get_children():
		var found: MeshInstance3D = _find_first_mesh_instance(child)
		if found != null:
			return found
	return null


func _run_verification() -> void:
	print("=== STARTING ENEMY FACING & SHIELD/PROJECTILE DIRECTION VERIFICATION ===")
	var test_root: Node3D = Node3D.new()
	test_root.name = "FacingTestRoot"
	root.add_child(test_root)

	var player: Node3D = Node3D.new()
	player.name = "Player"
	player.add_to_group("player")
	test_root.add_child(player)
	player.global_position = Vector3(6.0, 0.0, 8.0) # 10.0m away along (0.6, 0, 0.8)

	var failures: int = 0

	# 1. Verify all 8 enemy archetypes rotate so their visual front (-Z) & weapon/arm meshes face the player
	for i: int in range(ENEMY_PREFABS.size()):
		var path: String = ENEMY_PREFABS[i]
		var ps: PackedScene = load(path) as PackedScene
		if ps == null:
			push_error("Failed to load enemy prefab: %s" % path)
			failures += 1
			continue

		var enemy: OccultEnemyAI = ps.instantiate() as OccultEnemyAI
		if enemy == null:
			push_error("Enemy prefab is not OccultEnemyAI: %s" % path)
			failures += 1
			continue

		test_root.add_child(enemy)
		enemy.global_position = Vector3.ZERO
		enemy.rotation = Vector3(0.0, -1.2, 0.0) # Start facing an arbitrary wrong angle
		enemy.is_passive_dummy = false

		# Simulate 60 physics ticks (1.0s) so rotation converges
		var dt: float = 1.0 / 60.0
		for _step: int in range(60):
			enemy._physics_process(dt)

		var flat_to_player: Vector3 = Vector3(
			player.global_position.x - enemy.global_position.x,
			0.0,
			player.global_position.z - enemy.global_position.z
		).normalized()

		var fwd_dir: Vector3 = enemy.get_forward_dir()
		var facing_dot: float = fwd_dir.dot(flat_to_player)

		# Also verify physical world-space position of ForearmR/RightArm weapon mesh AABB center relative to its shoulder pivot in rest pose
		var arm_forward_dot: float = 1.0
		if enemy.torso_node != null:
			enemy.torso_node.rotation = Vector3.ZERO
		if enemy.upper_arm_r_node != null:
			enemy.upper_arm_r_node.rotation = Vector3.ZERO
		if enemy.forearm_r_node != null:
			enemy.forearm_r_node.rotation = Vector3.ZERO
		var weapon_limb_node: Node3D = enemy.forearm_r_node if enemy.forearm_r_node != null else enemy.right_arm_node
		if weapon_limb_node != null and enemy.right_arm_node != null:
			var arm_mi: MeshInstance3D = _find_first_mesh_instance(weapon_limb_node)
			if arm_mi != null:
				var arm_world_center: Vector3 = arm_mi.global_transform * arm_mi.mesh.get_aabb().get_center()
				var shoulder_world_pos: Vector3 = enemy.right_arm_node.global_position
				var arm_vec_flat: Vector3 = Vector3(
					arm_world_center.x - shoulder_world_pos.x,
					0.0,
					arm_world_center.z - shoulder_world_pos.z
				).normalized()
				arm_forward_dot = arm_vec_flat.dot(flat_to_player)

		print(
			"  [Enemy %02d] %s | archetype=%s | facing_dot=%.4f | weapon_arm_world_dot=%.4f" % [
				i + 1,
				enemy.enemy_title,
				enemy.combat_archetype,
				facing_dot,
				arm_forward_dot
			]
		)

		if facing_dot <= 0.98:
			push_error("Enemy %s failed facing_dot check: %.4f (expected > 0.98)" % [enemy.enemy_title, facing_dot])
			failures += 1
		if arm_forward_dot <= 0.50:
			push_error("Enemy %s physical weapon/arm mesh is facing away from player: %.4f" % [enemy.enemy_title, arm_forward_dot])
			failures += 1

		enemy.queue_free()

	await process_frame

	# 2. Verify Biome 2 SHIELD_GUARD frontal block vs. rear backstab bypass
	var sg_ps: PackedScene = load("res://scenes/prefabs/enemies/enemy_02_necropolis_praetorian.tscn") as PackedScene
	var sg_enemy: OccultEnemyAI = sg_ps.instantiate() as OccultEnemyAI
	test_root.add_child(sg_enemy)
	sg_enemy.global_position = Vector3.ZERO
	sg_enemy.is_passive_dummy = false
	sg_enemy.max_health = 500.0
	sg_enemy.current_health = 500.0

	# Face player at (0, 0, 10)
	player.global_position = Vector3(0.0, 0.0, 10.0)
	for _s: int in range(60):
		sg_enemy._physics_process(1.0 / 60.0)

	var front_dealt: float = sg_enemy.apply_damage(100.0, false)
	# Now move player directly BEHIND the Praetorian (0, 0, -10) without rotating Praetorian
	player.global_position = Vector3(0.0, 0.0, -10.0)
	var back_dealt: float = sg_enemy.apply_damage(100.0, false)

	print(
		"  [SHIELD_GUARD Check] Frontal 100 raw dmg -> dealt %.1f | Rear backstab 100 raw dmg -> dealt %.1f" % [
			front_dealt,
			back_dealt
		]
	)
	if not (front_dealt < 35.0 and back_dealt > 75.0):
		push_error("SHIELD_GUARD directional block failed: front=%.1f, back=%.1f" % [front_dealt, back_dealt])
		failures += 1

	sg_enemy.queue_free()
	await process_frame

	# 3. Verify Ranged Projectile spawns 1.2m in front of enemy toward player
	var rc_ps: PackedScene = load("res://scenes/prefabs/enemies/enemy_03_reliquary_hexweaver.tscn") as PackedScene
	var rc_enemy: OccultEnemyAI = rc_ps.instantiate() as OccultEnemyAI
	test_root.add_child(rc_enemy)
	rc_enemy.global_position = Vector3.ZERO
	rc_enemy.is_passive_dummy = false
	player.global_position = Vector3(0.0, 0.0, 10.0)
	for _s2: int in range(60):
		rc_enemy._physics_process(1.0 / 60.0)

	var dir_to_p: Vector3 = ((player.global_position + Vector3(0.0, 1.0, 0.0)) - (rc_enemy.global_position + Vector3(0.0, 1.30, 0.0))).normalized()
	var proj: EnemyProjectile = rc_enemy._fire_projectile_at_player(
		player,
		dir_to_p,
		Color(0.84, 0.36, 1.0, 1.0),
		13.5,
		0.0,
		1.2
	)
	if proj == null:
		push_error("Ranged enemy failed to spawn EnemyProjectile")
		failures += 1
	else:
		var spawn_offset: Vector3 = proj.global_position - rc_enemy.global_position
		var horiz_offset: Vector3 = Vector3(spawn_offset.x, 0.0, spawn_offset.z)
		var forward_dist: float = horiz_offset.dot(Vector3(0.0, 0.0, 1.0))
		var vel_dot: float = proj.velocity.normalized().dot(dir_to_p)
		print(
			"  [Projectile Check] Spawn forward offset=%.2fm (expected ~1.20m) | velocity_dot=%.4f" % [
				forward_dist,
				vel_dot
			]
		)
		if absf(forward_dist - 1.20) > 0.10 or vel_dot < 0.95:
			push_error("Projectile spawn direction/offset mismatch: dist=%.2f, vel_dot=%.4f" % [forward_dist, vel_dot])
			failures += 1

	if failures > 0:
		push_error("verify_enemy_facing.gd FAILED with %d error(s)" % failures)
		quit(1)
		return

	print("=== ALL 8 ENEMY ARCHETYPES FACING, SHIELD & PROJECTILE CHECKS PASSED (0 ERRORS) ===")
	quit(0)
