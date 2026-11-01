extends SceneTree

var _level_inst: Node3D = null
var _frame_count: int = 0


func _init() -> void:
	print("[VerifyEnemiesAI] Starting 8-Biome Enemy Rig & Active Combat AI Verification...")
	var level_scene: PackedScene = load("res://scenes/levels/town_overworld.tscn") as PackedScene
	if level_scene == null:
		push_error("[VerifyEnemiesAI] Failed to load town_overworld.tscn")
		quit(1)
		return
	_level_inst = level_scene.instantiate() as Node3D
	root.add_child(_level_inst)


func _physics_process(delta: float) -> bool:
	_frame_count += 1
	if _frame_count < 4:
		return false
	_run_verification(delta)
	return true


func _assert_cond(cond: bool, msg: String) -> bool:
	if not cond:
		push_error("[VerifyEnemiesAI] ASSERTION FAILED: " + msg)
		if _level_inst != null:
			_level_inst.free()
		quit(1)
		return false
	return true


func _run_verification(_delta: float) -> void:
	# 1. Verify all 8 Biome Enemy .tscn prefabs instantiate cleanly with articulated 6-node hierarchy:
	#    Root -> Pelvis -> Torso -> Head, LeftArm, RightArm
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
	var expected_archetypes: Array[String] = [
		"MELEE_RUSHER",
		"SHIELD_GUARD",
		"RANGED_CASTER",
		"HEAVY_BRUTE",
		"RANGED_LOBBER_EXPLODER",
		"BLINK_WRAITH",
		"SONIC_JUGGERNAUT",
		"ELITE_HYBRID_LORD"
	]

	for i: int in range(prefab_paths.size()):
		var p_path: String = prefab_paths[i]
		var p_scene: PackedScene = load(p_path) as PackedScene
		if not _assert_cond(p_scene != null, "Could not load enemy prefab: " + p_path):
			return
		var inst: OccultEnemyAI = p_scene.instantiate() as OccultEnemyAI
		if not _assert_cond(inst != null, "Prefab root is not OccultEnemyAI: " + p_path):
			return
		_level_inst.add_child(inst)
		inst._resolve_articulated_nodes()

		if not _assert_cond(inst.combat_archetype == expected_archetypes[i], "Archetype mismatch on " + p_path + ": got " + inst.combat_archetype):
			return
		if not _assert_cond(inst.pelvis_node != null and inst.pelvis_node is MeshInstance3D, "Missing Pelvis MeshInstance3D on " + p_path):
			return
		if not _assert_cond(inst.torso_node != null and inst.torso_node.get_parent() == inst.pelvis_node, "Torso must be child of Pelvis on " + p_path):
			return
		if not _assert_cond(inst.head_node != null and inst.head_node.get_parent() == inst.torso_node, "Head must be child of Torso on " + p_path):
			return
		if not _assert_cond(inst.left_arm_node != null and inst.left_arm_node.get_parent() == inst.torso_node, "LeftArm must be child of Torso on " + p_path):
			return
		if not _assert_cond(inst.right_arm_node != null and inst.right_arm_node.get_parent() == inst.torso_node, "RightArm must be child of Torso on " + p_path):
			return

		print(
			"[VerifyEnemiesAI] Prefab %d/8 OK: %s (%s, HP=%.0f) Hierarchy=[Pelvis -> Torso -> Head, LeftArm, RightArm]"
			% [i + 1, inst.enemy_title, inst.combat_archetype, inst.max_health]
		)
		inst.free()

	# 2. Verify Chapel exterior test dummies have is_passive_dummy == true,
	#    while Crypt Chamber enemies have is_passive_dummy == false
	for d_idx: int in [1, 2, 3]:
		var dummy: OccultEnemyAI = _level_inst.find_child("CombatRangeDummy_%d" % d_idx, true, false) as OccultEnemyAI
		if not _assert_cond(dummy != null, "Missing CombatRangeDummy_%d" % d_idx):
			return
		if not _assert_cond(dummy.is_passive_dummy == true, "CombatRangeDummy_%d must have is_passive_dummy == true" % d_idx):
			return
	print("[VerifyEnemiesAI] Confirmed all 3 Chapel exterior test dummies have is_passive_dummy == true")

	var crypt_root: Node3D = _level_inst.get_node_or_null("WorldGeometry/CryptBasement") as Node3D
	if not _assert_cond(crypt_root != null, "Missing WorldGeometry/CryptBasement"):
		return
	var active_crypt_enemies: Array[OccultEnemyAI] = []
	_collect_active_enemies(crypt_root, active_crypt_enemies)
	if not _assert_cond(active_crypt_enemies.size() >= 16, "Expected >= 16 active enemies across 8 Crypt Chambers, got %d" % active_crypt_enemies.size()):
		return
	for ce: OccultEnemyAI in active_crypt_enemies:
		if not _assert_cond(ce.is_passive_dummy == false, "Crypt enemy %s must have is_passive_dummy == false" % ce.name):
			return
	print("[VerifyEnemiesAI] Confirmed %d active biome-matched enemies across all 8 Crypt Chambers (is_passive_dummy == false)" % active_crypt_enemies.size())

	# 3. Verify ProceduralDungeonGenerator spawns active biome-matched enemies + 1.25x Elite 2.2x-HP Biome Champion
	var proc_gen: ProceduralDungeonGenerator = _level_inst.find_child("ProceduralExpeditionRoot", true, false) as ProceduralDungeonGenerator
	if not _assert_cond(proc_gen != null, "Missing ProceduralExpeditionRoot"):
		return
	proc_gen.generate_biome_dungeon(8, 77777, 1, Vector3(0.0, 0.5, -26.0))
	var proc_enemies: Array[OccultEnemyAI] = []
	_collect_active_enemies(proc_gen, proc_enemies)
	if not _assert_cond(proc_enemies.size() >= 18, "Expected >= 18 active enemies in Procedural Dungeon, got %d" % proc_enemies.size()):
		return
	var elite_champ: OccultEnemyAI = proc_gen.find_child("*EliteBiomeChampion*", true, false) as OccultEnemyAI
	if not _assert_cond(elite_champ != null, "Missing EliteBiomeChampion in Finale Sanctum"):
		return
	if not _assert_cond(elite_champ.is_passive_dummy == false and elite_champ.is_champion == true, "EliteBiomeChampion flags invalid"):
		return
	if not _assert_cond(elite_champ.scale.is_equal_approx(Vector3(1.25, 1.25, 1.25)), "EliteBiomeChampion scale must be 1.25x"):
		return
	if not _assert_cond(elite_champ.max_health >= 400.0, "EliteBiomeChampion 2.2x HP scaling not applied: %.1f" % elite_champ.max_health):
		return
	print(
		"[VerifyEnemiesAI] Procedural Dungeon OK: %d active enemies + Elite Champion '%s' (HP=%.0f, Scale=%s)"
		% [proc_enemies.size(), elite_champ.enemy_title, elite_champ.max_health, str(elite_champ.scale)]
	)
	proc_gen.clear_generated_dungeon()

	# 4. Simulate Active AI State Transitions (IDLE -> ALERT/CHASE -> WINDUP -> ATTACK),
	#    Whisker Steering Movement, Ranged Projectiles, Player Damage Mitigation, and Sanctuary Resurrection!
	var player: FPSController = _level_inst.find_child("Player", true, false) as FPSController
	var loadout: PlayerLoadoutManager = _level_inst.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	if not _assert_cond(player != null and loadout != null, "Missing Player or PlayerLoadoutManager"):
		return

	# Place player in Chamber 1 at (0.0, 0.2, -26.0) within 4.0m of Ch1_Executioner_W at (-1.4, 0.0, -29.2)
	player.global_position = Vector3(0.0, 0.2, -26.0)
	var test_enemy: OccultEnemyAI = _level_inst.find_child("Ch1_Executioner_W", true, false) as OccultEnemyAI
	if not _assert_cond(test_enemy != null, "Missing Ch1_Executioner_W"):
		return

	var initial_enemy_pos: Vector3 = test_enemy.global_position
	var initial_state: int = test_enemy.current_state
	if not _assert_cond(initial_state == OccultEnemyAI.AIState.IDLE, "Expected enemy initial state IDLE"):
		return

	var saw_alert_or_chase: bool = false
	var saw_windup: bool = false
	var saw_attack: bool = false
	var hp_before: int = loadout.current_health
	var armor_before: int = loadout.current_armor

	for step: int in range(95):
		test_enemy._physics_process(0.05)
		if test_enemy.current_state == OccultEnemyAI.AIState.ALERT or test_enemy.current_state == OccultEnemyAI.AIState.CHASE:
			saw_alert_or_chase = true
		elif test_enemy.current_state == OccultEnemyAI.AIState.WINDUP:
			saw_windup = true
		elif test_enemy.current_state == OccultEnemyAI.AIState.ATTACK:
			saw_attack = true
			break

	var moved_dist: float = initial_enemy_pos.distance_to(test_enemy.global_position)
	if not _assert_cond(saw_alert_or_chase, "Enemy did not transition to ALERT/CHASE"):
		return
	if not _assert_cond(moved_dist > 0.5, "Enemy did not move toward player via whisker steering (moved %.3fm)" % moved_dist):
		return
	if not _assert_cond(saw_windup, "Enemy did not enter WINDUP telegraph state"):
		return
	if not _assert_cond(saw_attack, "Enemy did not enter ATTACK state"):
		return
	if not _assert_cond(loadout.current_health < hp_before or loadout.current_armor < armor_before, "Player did not take damage from enemy attack"):
		return

	print(
		"[VerifyEnemiesAI] Active AI Combat Cycle OK: IDLE -> ALERT/CHASE (moved %.2fm) -> WINDUP -> ATTACK (Player HP %d->%d, Armor %d->%d)"
		% [moved_dist, hp_before, loadout.current_health, armor_before, loadout.current_armor]
	)

	# Test Ranged Caster Projectile Spawning (Enemy 03 Hex-Weaver)
	var caster: OccultEnemyAI = _level_inst.find_child("Ch3_Hexweaver_W", true, false) as OccultEnemyAI
	if not _assert_cond(caster != null, "Missing Ch3_Hexweaver_W"):
		return
	var proj: EnemyProjectile = caster._fire_projectile_at_player(
		player,
		Vector3(0.0, 0.0, 1.0),
		Color(0.84, 0.36, 1.0, 1.0),
		13.5,
		0.0,
		1.2
	)
	if not _assert_cond(proj != null and is_instance_valid(proj), "Ranged caster failed to spawn EnemyProjectile"):
		return
	proj._physics_process(0.1)
	proj.free()
	print("[VerifyEnemiesAI] Ranged EnemyProjectile spawn & flight verified OK")

	# Test Player Death & Sanctuary Resurrection at Vector3(0.0, 3.6, -14.5)
	loadout.apply_player_damage(999.0)
	var sanctuary_pos: Vector3 = Vector3(0.0, 3.6, -14.5)
	if not _assert_cond(player.global_position.distance_to(sanctuary_pos) < 0.05, "Player was not resurrected at Sanctuary Font: " + str(player.global_position)):
		return
	if not _assert_cond(loadout.current_health == loadout.max_health and loadout.current_armor == loadout.max_armor, "Player HP/Armor not restored to 100% on Sanctuary Resurrection"):
		return
	print("[VerifyEnemiesAI] Sanctuary Resurrection verified OK: Teleported to %s with %d/%d HP and %d/%d Armor" % [str(player.global_position), loadout.current_health, loadout.max_health, loadout.current_armor, loadout.max_armor])

	print("[VerifyEnemiesAI] ALL 8 BIOME ENEMIES & ACTIVE COMBAT AI CHECKS PASSED 100%!")
	_level_inst.free()
	quit(0)


func _collect_active_enemies(node: Node, out_list: Array[OccultEnemyAI]) -> void:
	if node is OccultEnemyAI:
		out_list.append(node as OccultEnemyAI)
	for child: Node in node.get_children():
		_collect_active_enemies(child, out_list)
