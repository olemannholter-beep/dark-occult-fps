extends SceneTree


func _init() -> void:
	print("[VerifyEnemyBiomechanics] Starting 14-pivot biomechanical rig & animation verification...")
	call_deferred("_run_verification")


func _run_verification() -> void:
	var prefab_paths: Array[String] = [
		"res://scenes/prefabs/enemies/enemy_01_ossuary_executioner.tscn",
		"res://scenes/prefabs/enemies/enemy_02_necropolis_praetorian.tscn",
		"res://scenes/prefabs/enemies/enemy_03_reliquary_hexweaver.tscn",
		"res://scenes/prefabs/enemies/enemy_04_inquisitor_rackmaster.tscn",
		"res://scenes/prefabs/enemies/enemy_05_plague_bloater.tscn",
		"res://scenes/prefabs/enemies/enemy_06_weeping_banshee.tscn",
		"res://scenes/prefabs/enemies/enemy_07_bell_juggernaut.tscn",
		"res://scenes/prefabs/enemies/enemy_08_abyssal_archon.tscn"
	]

	var required_nodes: Array[String] = [
		"Pelvis",
		"ThighL",
		"ShinL",
		"ThighR",
		"ShinR",
		"Torso",
		"Head",
		"UpperArmL",
		"ForearmL",
		"UpperArmR",
		"ForearmR",
		"SecondaryProp"
	]

	var root_test: Node3D = Node3D.new()
	root_test.name = "BiomechanicsTestArena"
	root.add_child(root_test)

	var floor_body: StaticBody3D = StaticBody3D.new()
	floor_body.collision_layer = 1
	floor_body.collision_mask = 1
	var floor_col: CollisionShape3D = CollisionShape3D.new()
	var floor_box: BoxShape3D = BoxShape3D.new()
	floor_box.size = Vector3(200.0, 1.0, 200.0)
	floor_col.shape = floor_box
	floor_col.position = Vector3(0.0, -0.5, 0.0)
	floor_body.add_child(floor_col)
	root_test.add_child(floor_body)

	var dummy_player: Node3D = Node3D.new()
	dummy_player.name = "FPSPlayer"
	dummy_player.add_to_group("player")
	root_test.add_child(dummy_player)
	dummy_player.global_position = Vector3(0.0, 0.0, 0.0)

	for i: int in range(prefab_paths.size()):
		var p_path: String = prefab_paths[i]
		var scn: PackedScene = load(p_path) as PackedScene
		if scn == null:
			push_error("Failed to load prefab: " + p_path)
			quit(1)
			return

		var enemy: OccultEnemyAI = scn.instantiate() as OccultEnemyAI
		if enemy == null:
			push_error("Prefab is not OccultEnemyAI: " + p_path)
			quit(1)
			return

		var angle: float = float(i) * (TAU / 8.0)
		var spawn_pos: Vector3 = Vector3(cos(angle) * 9.0, 0.0, sin(angle) * 9.0)
		root_test.add_child(enemy)
		enemy.global_position = spawn_pos

		# 1. Verify full articulated node tree
		for req_name: String in required_nodes:
			var found_node: Node3D = enemy.find_child(req_name, true, false) as Node3D
			if found_node == null:
				push_error(
					"[FAIL] Enemy " + enemy.name + " (" + p_path + ") missing articulated pivot: "
					+ req_name
				)
				quit(1)
				return

		var pelvis: Node3D = enemy.find_child("Pelvis", true, false) as Node3D
		var thigh_l: Node3D = enemy.find_child("ThighL", true, false) as Node3D
		var shin_l: Node3D = enemy.find_child("ShinL", true, false) as Node3D
		var thigh_r: Node3D = enemy.find_child("ThighR", true, false) as Node3D
		var shin_r: Node3D = enemy.find_child("ShinR", true, false) as Node3D
		var torso: Node3D = enemy.find_child("Torso", true, false) as Node3D
		var head: Node3D = enemy.find_child("Head", true, false) as Node3D
		var upper_arm_r: Node3D = enemy.find_child("UpperArmR", true, false) as Node3D
		var forearm_r: Node3D = enemy.find_child("ForearmR", true, false) as Node3D

		# 2. Step CHASE locomotion and verify ThighL/R rotate AND ShinL/R bend (knee angle != 0.0)
		enemy.current_state = OccultEnemyAI.AIState.CHASE
		for step_idx: int in range(32):
			enemy._physics_process(0.025)

		if is_zero_approx(thigh_l.rotation.x) and is_zero_approx(thigh_r.rotation.x):
			push_error("[FAIL] Enemy " + enemy.name + " ThighL/R did not rotate during CHASE gait!")
			quit(1)
			return
		if is_zero_approx(shin_l.rotation.x) or is_zero_approx(shin_r.rotation.x):
			push_error("[FAIL] Enemy " + enemy.name + " ShinL/R knee angle remained 0.0 during CHASE!")
			quit(1)
			return

		# 5. Verify enemy faces the player head-on (dot > 0.85)
		var to_player: Vector3 = dummy_player.global_position - enemy.global_position
		to_player.y = 0.0
		var dir_to_player: Vector3 = to_player.normalized()
		var forward_dir: Vector3 = enemy.get_forward_dir()
		forward_dir.y = 0.0
		forward_dir = forward_dir.normalized()
		var facing_dot: float = forward_dir.dot(dir_to_player)
		if facing_dot <= 0.85:
			push_error(
				"[FAIL] Enemy " + enemy.name + " not facing player head-on! dot="
				+ str(snappedf(facing_dot, 0.001))
			)
			quit(1)
			return

		# 3. Call take_damage at head height (Y = 1.65) and verify flinch_head_rot / flinch_torso_rot
		var head_hit_pos: Vector3 = enemy.global_position + Vector3(0.0, 1.65, 0.0)
		var shot_dir: Vector3 = -dir_to_player
		enemy.take_damage(8.0, false, head_hit_pos, shot_dir)
		if enemy.flinch_head_rot.length() < 0.1 or enemy.flinch_torso_rot.length() < 0.05:
			push_error(
				"[FAIL] Enemy " + enemy.name + " headshot did not apply non-zero flinch_head_rot/flinch_torso_rot!"
			)
			quit(1)
			return

		# Clear flinch to test clean WINDUP -> ATTACK coil/uncoil
		enemy.flinch_head_rot = Vector3.ZERO
		enemy.flinch_torso_rot = Vector3.ZERO
		enemy.flinch_arm_l = 0.0
		enemy.flinch_arm_r = 0.0

		# 4. Step WINDUP -> ATTACK and verify Torso, UpperArmR, and ForearmR coil and uncoil sequentially
		enemy.current_state = OccultEnemyAI.AIState.WINDUP
		enemy.windup_duration = 0.45
		enemy.state_timer = 0.05 # Near end of windup (p ~ 0.89)
		enemy._physics_process(0.01)

		var windup_torso_y: float = torso.rotation.y
		var windup_arm_r_x: float = upper_arm_r.rotation.x
		var windup_arm_r_y: float = upper_arm_r.rotation.y
		var windup_forearm_r_x: float = forearm_r.rotation.x
		var is_caster: bool = (
			enemy.combat_archetype == "RANGED_CASTER"
			or enemy.combat_archetype == "RANGED_LOBBER_EXPLODER"
			or enemy.combat_archetype == "BLINK_WRAITH"
		)

		if is_caster:
			if windup_torso_y >= -0.15 or windup_arm_r_y >= -0.25 or windup_forearm_r_x <= 0.3:
				push_error(
					"[FAIL] Caster Enemy " + enemy.name + " WINDUP did not coil inward properly! "
					+ "torso.y=" + str(windup_torso_y)
					+ " upper_arm_r.y=" + str(windup_arm_r_y)
					+ " forearm_r.x=" + str(windup_forearm_r_x)
				)
				quit(1)
				return
		else:
			if windup_torso_y >= -0.15 or windup_arm_r_x >= -0.8 or windup_forearm_r_x <= 0.3:
				push_error(
					"[FAIL] Enemy " + enemy.name + " WINDUP did not coil properly! "
					+ "torso.y=" + str(windup_torso_y)
					+ " upper_arm_r.x=" + str(windup_arm_r_x)
					+ " forearm_r.x=" + str(windup_forearm_r_x)
				)
				quit(1)
				return

		enemy.current_state = OccultEnemyAI.AIState.ATTACK
		enemy._attack_executed_in_cycle = true
		enemy.state_timer = 0.02 # Near end of attack strike (p ~ 0.94)
		enemy._physics_process(0.01)

		var attack_torso_y: float = torso.rotation.y
		var attack_arm_r_x: float = upper_arm_r.rotation.x
		var attack_arm_r_y: float = upper_arm_r.rotation.y
		var attack_forearm_r_x: float = forearm_r.rotation.x

		if is_caster:
			if attack_torso_y <= windup_torso_y + 0.4 or attack_arm_r_y <= windup_arm_r_y + 0.6 or attack_forearm_r_x >= windup_forearm_r_x - 0.3:
				push_error(
					"[FAIL] Caster Enemy " + enemy.name + " ATTACK did not thrust wide from WINDUP! "
					+ "attack_torso.y=" + str(attack_torso_y)
					+ " attack_arm_r.y=" + str(attack_arm_r_y)
					+ " attack_forearm_r.x=" + str(attack_forearm_r_x)
				)
				quit(1)
				return
		else:
			if attack_torso_y <= windup_torso_y + 0.4 or attack_arm_r_x <= windup_arm_r_x + 1.2 or attack_forearm_r_x >= windup_forearm_r_x - 0.4:
				push_error(
					"[FAIL] Enemy " + enemy.name + " ATTACK did not uncoil sequentially from WINDUP! "
					+ "attack_torso.y=" + str(attack_torso_y)
					+ " attack_arm_r.x=" + str(attack_arm_r_x)
					+ " attack_forearm_r.x=" + str(attack_forearm_r_x)
				)
				quit(1)
				return

		print(
			"[PASS] " + enemy.name
			+ " (Biome " + str(enemy.biome_relic_id) + ")"
			+ " | facing_dot=" + str(snappedf(facing_dot, 0.001))
			+ " | thigh_l.x=" + str(snappedf(thigh_l.rotation.x, 0.001))
			+ " | shin_l.x=" + str(snappedf(shin_l.rotation.x, 0.001))
			+ " | windup_arm=" + str(snappedf(windup_arm_r_x, 0.01))
			+ " -> attack_arm=" + str(snappedf(attack_arm_r_x, 0.01))
			+ " | head_track.y=" + str(snappedf(head.rotation.y, 0.001))
			+ " | pelvis.y=" + str(snappedf(pelvis.position.y, 0.001))
		)

	print("[VerifyEnemyBiomechanics] All 8 enemy prefabs passed 14-pivot biomechanical rig & animation assertions!")
	root_test.free()
	quit(0)
