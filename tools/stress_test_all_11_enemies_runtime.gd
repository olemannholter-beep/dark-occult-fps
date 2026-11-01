extends SceneTree

const ALL_11_PREFABS: Array[String] = [
	"res://scenes/prefabs/enemies/enemy_ossuary_skeleton.tscn",
	"res://scenes/prefabs/enemies/enemy_plague_acolyte.tscn",
	"res://scenes/prefabs/enemies/enemy_iron_penitent.tscn",
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
	call_deferred("_run_runtime_stress_test")


func _run_runtime_stress_test() -> void:
	print("=== STARTING FULL RUNTIME BIOMECHANICS & FACING STRESS TEST (ALL 11 ENEMIES) ===")
	var arena: Node3D = Node3D.new()
	arena.name = "StressArena"
	root.add_child(arena)

	var floor_body: StaticBody3D = StaticBody3D.new()
	var floor_col: CollisionShape3D = CollisionShape3D.new()
	var floor_box: BoxShape3D = BoxShape3D.new()
	floor_box.size = Vector3(100.0, 1.0, 100.0)
	floor_col.shape = floor_box
	floor_col.position = Vector3(0.0, -0.5, 0.0)
	floor_body.add_child(floor_col)
	arena.add_child(floor_body)

	var dummy_player: Node3D = Node3D.new()
	dummy_player.name = "Player"
	dummy_player.add_to_group("player")
	arena.add_child(dummy_player)
	dummy_player.global_position = Vector3(0.0, 0.0, 0.0)

	var total_failures: int = 0

	for idx: int in range(ALL_11_PREFABS.size()):
		var p_path: String = ALL_11_PREFABS[idx]
		var scn: PackedScene = load(p_path) as PackedScene
		if scn == null:
			push_error("[FAIL] Could not load prefab: " + p_path)
			total_failures += 1
			continue

		var enemy: OccultEnemyAI = scn.instantiate() as OccultEnemyAI
		if enemy == null:
			push_error("[FAIL] Prefab is not OccultEnemyAI: " + p_path)
			total_failures += 1
			continue

		# Spawn in circle around dummy player at radius 8.0m
		var angle: float = float(idx) * (TAU / float(ALL_11_PREFABS.size()))
		var spawn_pos: Vector3 = Vector3(cos(angle) * 8.0, 0.0, sin(angle) * 8.0)
		arena.add_child(enemy)
		enemy.global_position = spawn_pos
		enemy.rotation = Vector3(0.0, randf_range(-PI, PI), 0.0) # Start with arbitrary angle
		enemy.is_passive_dummy = false

		# Settle and let facing converge toward player
		for _step: int in range(60):
			enemy._physics_process(1.0 / 60.0)

		# 1. Facing Check
		var to_player: Vector3 = (dummy_player.global_position - enemy.global_position)
		to_player.y = 0.0
		var dir_to_p: Vector3 = to_player.normalized()
		var forward_dir: Vector3 = enemy.get_forward_dir()
		forward_dir.y = 0.0
		forward_dir = forward_dir.normalized()
		var facing_dot: float = forward_dir.dot(dir_to_p)

		if facing_dot <= 0.95:
			push_error("[FAIL] %s failed facing check! dot=%.4f" % [enemy.name, facing_dot])
			total_failures += 1

		# 2. Articulated Locomotion Gait Check
		var thigh_l: Node3D = enemy.find_child("ThighL", true, false) as Node3D
		var shin_l: Node3D = enemy.find_child("ShinL", true, false) as Node3D
		var thigh_r: Node3D = enemy.find_child("ThighR", true, false) as Node3D
		var shin_r: Node3D = enemy.find_child("ShinR", true, false) as Node3D
		var torso: Node3D = enemy.find_child("Torso", true, false) as Node3D
		var head: Node3D = enemy.find_child("Head", true, false) as Node3D
		var upper_arm_r: Node3D = enemy.find_child("UpperArmR", true, false) as Node3D
		var forearm_r: Node3D = enemy.find_child("ForearmR", true, false) as Node3D

		enemy.current_state = OccultEnemyAI.AIState.CHASE
		for _step2: int in range(32):
			enemy._physics_process(0.025)

		var gait_ok: bool = true
		if is_zero_approx(thigh_l.rotation.x) and is_zero_approx(thigh_r.rotation.x):
			push_error("[FAIL] %s thighs did not rotate in gait!" % enemy.name)
			gait_ok = false
			total_failures += 1
		if is_zero_approx(shin_l.rotation.x) or is_zero_approx(shin_r.rotation.x):
			push_error("[FAIL] %s knees did not bend in gait!" % enemy.name)
			gait_ok = false
			total_failures += 1

		# 3. Headshot Impact & Flinch
		var head_hit_pos: Vector3 = enemy.global_position + Vector3(0.0, 1.65, 0.0)
		var shot_dir: Vector3 = -dir_to_p
		enemy.take_damage(10.0, false, head_hit_pos, shot_dir)
		var flinch_len: float = enemy.flinch_head_rot.length() + enemy.flinch_torso_rot.length()
		if flinch_len < 0.10:
			push_error("[FAIL] %s did not register flinch recoil! flinch_len=%.4f" % [enemy.name, flinch_len])
			total_failures += 1

		# 4. Clear flinch & Test WINDUP -> ATTACK Cycle
		enemy.flinch_head_rot = Vector3.ZERO
		enemy.flinch_torso_rot = Vector3.ZERO
		enemy.flinch_arm_l = 0.0
		enemy.flinch_arm_r = 0.0

		enemy.current_state = OccultEnemyAI.AIState.WINDUP
		enemy.windup_duration = 0.45
		enemy.state_timer = 0.05
		enemy._physics_process(0.01)

		var windup_torso_y: float = torso.rotation.y
		var windup_arm_r_x: float = upper_arm_r.rotation.x
		var windup_farm_r_x: float = forearm_r.rotation.x

		enemy.current_state = OccultEnemyAI.AIState.ATTACK
		enemy._attack_executed_in_cycle = true
		enemy.state_timer = 0.02
		enemy._physics_process(0.01)

		var attack_torso_y: float = torso.rotation.y
		var attack_arm_r_x: float = upper_arm_r.rotation.x
		var attack_farm_r_x: float = forearm_r.rotation.x

		# Check for NaN / Inf safety across all transforms
		var nan_detected: bool = (
			is_nan(enemy.global_position.x) or is_nan(torso.rotation.x)
			or is_nan(upper_arm_r.rotation.x) or is_nan(shin_l.rotation.x)
		)
		if nan_detected:
			push_error("[FAIL] NaN detected in %s transforms!" % enemy.name)
			total_failures += 1

		print(
			"  [%02d/11] %s | archetype=%s | facing_dot=%.4f | gait_ok=%s | flinch=%.3f | windup_arm=%.2f -> atk_arm=%.2f" % [
				idx + 1,
				enemy.name,
				enemy.combat_archetype,
				facing_dot,
				str(gait_ok),
				flinch_len,
				windup_arm_r_x,
				attack_arm_r_x
			]
		)

		enemy.queue_free()

	print("\n=======================================================")
	if total_failures == 0:
		print("=== ALL 11 ENEMIES PASSED RUNTIME BIOMECHANICS & FACING STRESS TESTS (0 FAILURES)! ===")
		quit(0)
	else:
		push_error("=== RUNTIME STRESS TESTS FAILED WITH %d TOTAL FAILURES! ===" % total_failures)
		quit(1)
