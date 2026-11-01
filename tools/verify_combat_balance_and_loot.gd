extends SceneTree


func _init() -> void:
	call_deferred("_run_verification")


func _run_verification() -> void:
	print("=== [VerifyCombatBalanceAndLoot] Starting Combat Balance, Scarcity Drops, Pity System & Tier 1-8 Scaling Verification ===")
	var failures: int = 0

	var level_scene: PackedScene = load("res://scenes/levels/town_overworld.tscn") as PackedScene
	if level_scene == null:
		push_error("[FAIL] Could not load town_overworld.tscn")
		quit(1)
		return

	var level: Node3D = level_scene.instantiate() as Node3D
	root.add_child(level)
	await process_frame
	await physics_frame

	var player: FPSController = level.find_child("Player", true, false) as FPSController
	var loadout: PlayerLoadoutManager = level.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	var vm: FPSViewmodelController = level.find_child("ViewmodelRig", true, false) as FPSViewmodelController
	var hud: FPSHUD = level.find_child("HUD", true, false) as FPSHUD

	if player == null or loadout == null or vm == null or hud == null:
		push_error("[FAIL] Missing Player, PlayerLoadoutManager, ViewmodelRig, or HUD")
		quit(1)
		return

	loadout._resolve_dependencies()
	vm._resolve_nodes_and_subcomponents()

	# --------------------------------------------------------------------------
	# 1. Verify 4 Crafting Currencies & 4-Tier Relic Scaling in PlayerLoadoutManager
	# --------------------------------------------------------------------------
	var s0: int = loadout.get_resource_amount("silver")
	var b0: int = loadout.get_resource_amount("bone_ash")
	var i0: int = loadout.get_resource_amount("cursed_iron")
	var c0: int = loadout.get_resource_amount("soul_cores")

	loadout.add_resource("silver", 100)
	loadout.add_resource("bone_ash", 50)
	loadout.add_resource("cursed_iron", 10)
	loadout.add_resource("soul_cores", 4)

	var test_cost: Dictionary[String, int] = {"silver": 40, "bone_ash": 20, "cursed_iron": 3}
	if not loadout.can_afford(test_cost) or not loadout.spend_resources(test_cost):
		push_error("[FAIL] PlayerLoadoutManager.can_afford / spend_resources failed")
		failures += 1
	if (
		loadout.get_resource_amount("silver") != s0 + 60
		or loadout.get_resource_amount("bone_ash") != b0 + 30
		or loadout.get_resource_amount("cursed_iron") != i0 + 7
		or loadout.get_resource_amount("soul_cores") != c0 + 4
	):
		push_error("[FAIL] PlayerLoadoutManager resource balances mismatch after spend_resources")
		failures += 1
	print("[PASS 1A] Verified 4 Crafting Resources (Silver=%d, Bone-Ash=%d, Cursed Iron=%d, Soul-Cores=%d)." % [
		loadout.get_resource_amount("silver"),
		loadout.get_resource_amount("bone_ash"),
		loadout.get_resource_amount("cursed_iron"),
		loadout.get_resource_amount("soul_cores")
	])

	var relic_t1: Dictionary = loadout.grant_random_relic(1, false)
	var relic_t4: Dictionary = loadout.grant_random_relic(8, true)
	var t1_tier: int = int(relic_t1.get("tier", 0))
	var t4_tier: int = int(relic_t4.get("tier", 0))
	if t1_tier < 1 or t1_tier > 2 or t4_tier < 3 or t4_tier > 4:
		push_error("[FAIL] Relic tier scaling out of expected bounds (Portal 1 tier=%d, Portal 8 boss tier=%d)" % [t1_tier, t4_tier])
		failures += 1
	print("[PASS 1B] Verified 4-Tier Relic Scaling (Portal 1 -> Tier %d '%s' [%.2fx], Portal 8 Boss -> Tier %d '%s' [%.2fx])." % [
		t1_tier, String(relic_t1.get("tier_name", "")), float(relic_t1.get("mult", 1.0)),
		t4_tier, String(relic_t4.get("tier_name", "")), float(relic_t4.get("mult", 1.0))
	])

	# --------------------------------------------------------------------------
	# 2. Verify Portal 1-8 Monotonic Enemy Difficulty & Champion Scaling Curve
	# --------------------------------------------------------------------------
	var enemy_ps: PackedScene = load("res://scenes/prefabs/enemies/enemy_01_ossuary_executioner.tscn") as PackedScene
	if enemy_ps == null:
		push_error("[FAIL] Missing enemy_01_ossuary_executioner.tscn")
		quit(1)
		return

	var prev_hp: float = 0.0
	var prev_dmg: float = 0.0
	var prev_spd: float = 0.0
	var prev_windup: float = 999.0
	var prev_xp: int = 0

	for tier_i: int in range(1, 9):
		var en: OccultEnemyAI = enemy_ps.instantiate() as OccultEnemyAI
		level.add_child(en)
		en.configure_for_biome_tier(tier_i, false)
		if en.max_health <= prev_hp or en.attack_damage < prev_dmg or en.move_speed <= prev_spd or en.windup_duration > prev_windup or en.xp_reward < prev_xp:
			push_error("[FAIL] Non-monotonic enemy scaling at Tier %d (HP=%.0f, DMG=%.0f, SPD=%.2f, Windup=%.2f, XP=%d)" % [
				tier_i, en.max_health, en.attack_damage, en.move_speed, en.windup_duration, en.xp_reward
			])
			failures += 1
		prev_hp = en.max_health
		prev_dmg = en.attack_damage
		prev_spd = en.move_speed
		prev_windup = en.windup_duration
		prev_xp = en.xp_reward
		en.free()

	var champ_en: OccultEnemyAI = enemy_ps.instantiate() as OccultEnemyAI
	level.add_child(champ_en)
	champ_en.configure_for_biome_tier(4, true)
	if not champ_en.is_champion or not champ_en.scale.is_equal_approx(Vector3(1.22, 1.22, 1.22)) or not champ_en.enemy_title.begins_with("Anointed "):
		push_error("[FAIL] Anointed Champion configuration failed on Tier 4 enemy")
		failures += 1
	print("[PASS 2] Verified Portal 1->8 Difficulty Curve (Tier 8 HP=%.0f, DMG=%.0f, SPD=%.2f, Windup=%.2fs, XP=%d) & Anointed Champion ('%s', HP=%.0f)." % [
		prev_hp, prev_dmg, prev_spd, prev_windup, prev_xp, champ_en.enemy_title, champ_en.max_health
	])
	champ_en.free()

	# --------------------------------------------------------------------------
	# 3. Verify 32% Scarcity Enemy Drop Rate (Full HP) vs 58% Low-HP Pity Boost (<35% HP)
	# --------------------------------------------------------------------------
	var drop_container: Node3D = Node3D.new()
	drop_container.name = "DropSimulationContainer"
	level.add_child(drop_container)

	# 3A: 200 Standard Enemy Kills at 100% Player HP
	loadout.current_health = loadout.max_health
	var full_hp_kills_with_drops: int = 0
	var full_hp_resource_drops: int = 0
	var full_hp_total_drops: int = 0

	for i: int in range(200):
		var before_c: int = drop_container.get_child_count()
		var sim_en: OccultEnemyAI = enemy_ps.instantiate() as OccultEnemyAI
		drop_container.add_child(sim_en)
		sim_en.position = Vector3(float(i) * 0.5, 0.0, 0.0)
		sim_en.configure_for_biome_tier(3, false)
		sim_en._die_and_spawn_loot()
		var after_c: int = drop_container.get_child_count()
		# sim_en is still a child until queue_free finishes, so new drops = after_c - (before_c + 1)
		var spawned_n: int = after_c - (before_c + 1)
		if spawned_n > 0:
			full_hp_kills_with_drops += 1
			for c_idx: int in range(before_c + 1, after_c):
				var d_node: Node = drop_container.get_child(c_idx)
				if d_node is LootDropPickup:
					full_hp_total_drops += 1
					var cat: String = (d_node as LootDropPickup).drop_category
					if cat == "silver" or cat == "bone_ash" or cat == "cursed_iron" or cat == "soul_cores":
						full_hp_resource_drops += 1

	var full_hp_drop_rate: float = float(full_hp_kills_with_drops) / 200.0
	var full_hp_res_share: float = float(full_hp_resource_drops) / float(maxi(1, full_hp_total_drops))
	if full_hp_drop_rate < 0.20 or full_hp_drop_rate > 0.45:
		push_error("[FAIL] Full-HP Scarcity Drop Rate %.2f outside expected ~32%% range [0.20..0.45]" % full_hp_drop_rate)
		failures += 1
	print("[PASS 3A] Full-HP Scarcity Drop Rate = %.1f%% (%d/200 kills dropped loot; %.1f%% Crafting Materials)." % [
		full_hp_drop_rate * 100.0, full_hp_kills_with_drops, full_hp_res_share * 100.0
	])

	# 3B: 200 Standard Enemy Kills at 20% Player HP (< 35% Low-HP Pity Threshold)
	var low_hp_kills_with_drops: int = 0
	var low_hp_health_drops: int = 0
	var low_hp_total_drops: int = 0

	for i: int in range(200):
		loadout.current_health = int(roundf(float(loadout.max_health) * 0.20))
		var before_c: int = drop_container.get_child_count()
		var sim_en: OccultEnemyAI = enemy_ps.instantiate() as OccultEnemyAI
		drop_container.add_child(sim_en)
		sim_en.position = Vector3(float(i) * 0.5, 0.0, 5.0)
		sim_en.configure_for_biome_tier(3, false)
		sim_en._die_and_spawn_loot()
		var after_c: int = drop_container.get_child_count()
		var spawned_n: int = after_c - (before_c + 1)
		if spawned_n > 0:
			low_hp_kills_with_drops += 1
			for c_idx: int in range(before_c + 1, after_c):
				var d_node: Node = drop_container.get_child(c_idx)
				if d_node is LootDropPickup:
					low_hp_total_drops += 1
					var cat: String = (d_node as LootDropPickup).drop_category
					if cat == "health" or cat == "blood_chalice":
						low_hp_health_drops += 1

	var low_hp_drop_rate: float = float(low_hp_kills_with_drops) / 200.0
	var low_hp_heal_share: float = float(low_hp_health_drops) / float(maxi(1, full_hp_total_drops if low_hp_total_drops == 0 else low_hp_total_drops))
	if low_hp_drop_rate <= full_hp_drop_rate or low_hp_drop_rate < 0.44 or low_hp_heal_share < 0.40:
		push_error("[FAIL] Low-HP Pity Boost failed: drop_rate=%.2f (vs %.2f), heal_share=%.2f" % [
			low_hp_drop_rate, full_hp_drop_rate, low_hp_heal_share
		])
		failures += 1
	print("[PASS 3B] Low-HP 'Blood-Desperation' Pity Boost = %.1f%% (%d/200 kills dropped loot; %.1f%% Crimson Blood Vials)." % [
		low_hp_drop_rate * 100.0, low_hp_kills_with_drops, low_hp_heal_share * 100.0
	])

	# --------------------------------------------------------------------------
	# 4. Verify End-of-Dungeon Completion Jackpot ReliquaryChest
	# --------------------------------------------------------------------------
	var chest_ps: PackedScene = load("res://scenes/prefabs/props/prop_gothic_reliquary_chest.tscn") as PackedScene
	var comp_chest: ReliquaryChest = chest_ps.instantiate() as ReliquaryChest
	comp_chest.is_completion_chest = true
	comp_chest.chest_biome_id = 5
	comp_chest.guaranteed_relic_id = 5
	drop_container.add_child(comp_chest)

	loadout.current_health = 30
	var pre_cores: int = loadout.get_resource_amount("soul_cores")
	var jackpot_drops: Array[LootDropPickup] = comp_chest.open_chest(loadout)
	if jackpot_drops.size() < 4 or loadout.current_health != loadout.max_health or loadout.get_resource_amount("soul_cores") <= pre_cores:
		push_error("[FAIL] Completion Jackpot ReliquaryChest failed (drops=%d, hp=%d/%d, cores=%d)" % [
			jackpot_drops.size(), loadout.current_health, loadout.max_health, loadout.get_resource_amount("soul_cores")
		])
		failures += 1
	else:
		print("[PASS 4] End-of-Dungeon Completion Jackpot ReliquaryChest awarded cache, restored 100%% HP/Armor, and launched %d physical 3D LootDropPickup nodes." % jackpot_drops.size())

	root.remove_child(level)
	level.free()

	if failures > 0:
		push_error("=== [VerifyCombatBalanceAndLoot] FAILED with %d errors ===" % failures)
		quit(1)
	else:
		print("=== [VerifyCombatBalanceAndLoot] ALL COMBAT BALANCE, SCARCITY LOOT, PITY & COMPLETION CHEST CHECKS PASSED 100% ===")
		quit(0)
