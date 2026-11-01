extends SceneTree


func _init() -> void:
	call_deferred("_run_verification")


func _run_verification() -> void:
	print("[VerifyProgression] Starting comprehensive RPG Progression, 3D Loot & Active Lantern Spell verification...")
	var level_scene: PackedScene = load("res://scenes/levels/town_overworld.tscn") as PackedScene
	if level_scene == null:
		push_error("[VerifyProgression] Failed to load town_overworld.tscn")
		quit(1)
		return

	var level: Node3D = level_scene.instantiate() as Node3D
	root.add_child(level)
	await process_frame

	var player: FPSController = level.find_child("Player", true, false) as FPSController
	var loadout: PlayerLoadoutManager = level.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	var vm: FPSViewmodelController = level.find_child("ViewmodelRig", true, false) as FPSViewmodelController
	var hud: FPSHUD = level.find_child("HUD", true, false) as FPSHUD

	if player == null or loadout == null or vm == null or hud == null:
		push_error("[VerifyProgression] Missing Player / PlayerLoadoutManager / ViewmodelRig / HUD")
		quit(1)
		return

	loadout._resolve_dependencies()
	vm._resolve_nodes_and_subcomponents()

	# -------------------------------------------------------------------------
	# 1. Verify ReliquaryChest opening & physical LootDropPickup spawning
	# -------------------------------------------------------------------------
	var sanct_chest: ReliquaryChest = level.find_child("SanctuaryReliquaryChest", true, false) as ReliquaryChest
	var ow_chest: ReliquaryChest = level.find_child("OverworldTestReliquaryChest", true, false) as ReliquaryChest
	if sanct_chest == null or ow_chest == null:
		push_error("[VerifyProgression] Missing SanctuaryReliquaryChest or OverworldTestReliquaryChest in town_overworld.tscn")
		quit(1)
		return

	var chest_drops: Array[LootDropPickup] = ow_chest.open_chest()
	if not ow_chest.is_opened or chest_drops.size() != 4:
		push_error("[VerifyProgression] ReliquaryChest did not spawn 4 physical LootDropPickup nodes (got %d)" % chest_drops.size())
		quit(1)
		return
	print("[VerifyProgression] PASS 1A: OverworldTestReliquaryChest opened and launched %d physical 3D LootDropPickup nodes." % chest_drops.size())

	# -------------------------------------------------------------------------
	# 2. Verify TestDummyEnemy death spawns physical 3D LootDropPickups
	# -------------------------------------------------------------------------
	var dummy_1: TestDummyEnemy = level.find_child("CombatRangeDummy_1", true, false) as TestDummyEnemy
	var dummy_2: TestDummyEnemy = level.find_child("CombatRangeDummy_2", true, false) as TestDummyEnemy
	var dummy_3: TestDummyEnemy = level.find_child("CombatRangeDummy_3", true, false) as TestDummyEnemy
	if dummy_1 == null or dummy_2 == null or dummy_3 == null:
		push_error("[VerifyProgression] Missing CombatRangeDummy_1/2/3 in town_overworld.tscn")
		quit(1)
		return

	var props_parent: Node = dummy_1.get_parent()
	var before_children: int = props_parent.get_child_count()
	dummy_1.guaranteed_relic_drop = true
	dummy_1.biome_relic_id = 1
	dummy_1.apply_damage(999.0)
	var after_children: int = props_parent.get_child_count()
	if after_children <= before_children:
		push_error("[VerifyProgression] Killing TestDummyEnemy did not spawn LootDropPickup nodes!")
		quit(1)
		return
	print("[VerifyProgression] PASS 1B: Killing CombatRangeDummy_1 spawned physical 3D LootDropPickup nodes in the scene tree.")

	# -------------------------------------------------------------------------
	# 3. Verify XP Collection -> Hunter Level-Up (1 -> 2) & +2 Attribute Points
	# -------------------------------------------------------------------------
	var start_level: int = loadout.hunter_level
	var start_pts: int = loadout.unspent_attribute_points
	for d: LootDropPickup in chest_drops:
		if is_instance_valid(d) and d.drop_category == "xp_essence":
			d.collect_pickup(player)
	loadout.add_xp(50)

	if loadout.hunter_level <= start_level or loadout.unspent_attribute_points < start_pts + 2:
		push_error(
			"[VerifyProgression] Level-up failed: level=%d (was %d), pts=%d (was %d)"
			% [loadout.hunter_level, start_level, loadout.unspent_attribute_points, start_pts]
		)
		quit(1)
		return
	print(
		"[VerifyProgression] PASS 2: Hunter leveled up (%d -> %d) and gained +2 Attribute Points (total unspent: %d)."
		% [start_level, loadout.hunter_level, loadout.unspent_attribute_points]
	)

	# -------------------------------------------------------------------------
	# 4. Verify Spending Attribute Points ([1] Bloodlust, [2] Quicksilver, [3] Ironclad, [4] Eldritch Focus)
	# -------------------------------------------------------------------------
	var reload_before: float = loadout.reload_speed_mult
	var speed_before: float = player.move_speed
	var dmg_before: float = loadout.damage_per_shot
	var hp_before: int = loadout.max_health
	var eld_before: float = loadout.eldritch_damage_mult

	loadout.spend_attribute_point(2) # Quicksilver
	loadout.spend_attribute_point(1) # Bloodlust
	loadout.spend_attribute_point(3) # Ironclad
	loadout.spend_attribute_point(4) # Eldritch Focus

	if loadout.reload_speed_mult <= reload_before or player.move_speed <= speed_before:
		push_error("[VerifyProgression] Quicksilver rank-up did not increase reload_speed_mult / move_speed!")
		quit(1)
		return
	if loadout.damage_per_shot <= dmg_before:
		push_error("[VerifyProgression] Bloodlust rank-up did not increase damage_per_shot!")
		quit(1)
		return
	if loadout.max_health <= hp_before:
		push_error("[VerifyProgression] Ironclad rank-up did not increase max_health!")
		quit(1)
		return
	if loadout.eldritch_damage_mult <= eld_before:
		push_error("[VerifyProgression] Eldritch Focus rank-up did not increase eldritch_damage_mult!")
		quit(1)
		return
	print(
		"[VerifyProgression] PASS 3: All 4 Attributes verified (DMG: %.0f->%.0f, Reload: %.2f->%.2f, Speed: %.2f->%.2f, HP: %d->%d, Eldritch: %.2f->%.2f)."
		% [
			dmg_before, loadout.damage_per_shot,
			reload_before, loadout.reload_speed_mult,
			speed_before, player.move_speed,
			hp_before, loadout.max_health,
			eld_before, loadout.eldritch_damage_mult
		]
	)

	# -------------------------------------------------------------------------
	# 5. Verify Collecting Relics & Mechanical Combat Modifiers
	# -------------------------------------------------------------------------
	# Collect Relic 5 (Plague Alchemist's Alembic) from chest_drops
	for d: LootDropPickup in chest_drops:
		if is_instance_valid(d) and d.drop_category == "relic":
			d.collect_pickup(player)
	loadout.acquire_relic(1) # Ossuary Skull Signet (Headshot ammo refund + +25% crit DMG)
	loadout.acquire_relic(6) # Weeping Saint's Tear (Chain Frost Bolt to nearby enemy within 8m)
	loadout.acquire_relic(7) # Sunken Bell Clapper (2.2x 6th-shot AoE Sonic Bell Blast)
	loadout.acquire_relic(8) # Abyssal Blood Chalice (+15 HP & Blood Frenzy on kill)

	if not loadout.has_relic(1) or not loadout.has_relic(5) or not loadout.has_relic(6) or not loadout.has_relic(7):
		push_error("[VerifyProgression] Relics were not registered in active_relics!")
		quit(1)
		return

	# Boost dummy_2 and dummy_3 health so we can inspect shot mechanics before they die
	dummy_2.max_health = 2000.0
	dummy_2.current_health = 2000.0
	dummy_3.max_health = 2000.0
	dummy_3.current_health = 2000.0

	# Test Headshot Refund (Relic 1) + Corrosive Bile DoT (Relic 5) + Chain Frost Bolt (Relic 6)
	vm.current_ammo = 4
	var d3_hp_before: float = dummy_3.current_health
	var normal_dmg: float = vm.fire_at_enemy_target(dummy_2, false, false)
	if not dummy_2.is_corroded():
		push_error("[VerifyProgression] Relic 5 (Plague Alchemist's Alembic) did not apply Corrosive Bile DoT!")
		quit(1)
		return
	if dummy_3.current_health >= d3_hp_before:
		push_error("[VerifyProgression] Relic 6 (Weeping Saint's Tear) did not arc Chain Frost Bolt to nearby enemy!")
		quit(1)
		return

	var ammo_before_crit: int = vm.current_ammo
	var _crit_dmg: float = vm.fire_at_enemy_target(dummy_2, true, false)
	if vm.current_ammo != ammo_before_crit:
		push_error("[VerifyProgression] Relic 1 (Ossuary Skull Signet) did not refund 1 round on headshot!")
		quit(1)
		return

	# Test 6th-shot 2.2x AoE Sonic Bell Blast (Relic 7)
	var sixth_shot_dmg: float = vm.fire_at_enemy_target(dummy_2, false, true)
	if sixth_shot_dmg < normal_dmg * 2.15:
		push_error(
			"[VerifyProgression] Relic 7 (Sunken Bell Clapper) 6th shot did not apply 2.2x damage (got %.1f vs normal %.1f)"
			% [sixth_shot_dmg, normal_dmg]
		)
		quit(1)
		return
	print(
		"[VerifyProgression] PASS 4: Relics 1, 5, 6, 7 verified (Normal DMG=%.1f, 6th-Shot Bell Blast DMG=%.1f, Bile DoT=true, Chain Frost=true, Crit Refund=true)."
		% [normal_dmg, sixth_shot_dmg]
	)

	# -------------------------------------------------------------------------
	# 6. Verify Active Left-Hand Lantern Occult Abilities ([F] to cast, [G] to cycle)
	# -------------------------------------------------------------------------
	player.global_position = dummy_2.global_position + Vector3(0.0, 0.0, 3.0)
	vm.ability_cooldown_remaining = 0.0
	vm.active_spell_index = 0 # Soul-Pyre Blast
	var d2_hp_pre_spell0: float = dummy_2.current_health
	var cast_ok_0: bool = vm.cast_active_lantern_ability()
	if not cast_ok_0 or dummy_2.current_health >= d2_hp_pre_spell0 or vm.left_recoil_offset_pos.length() < 0.05:
		push_error("[VerifyProgression] Spell 0 (Soul-Pyre Blast) failed to cast, animate LeftHandPivot, or damage enemy!")
		quit(1)
		return

	# Cycle to Spell 1 (Shackles of the Penitent)
	vm.cycle_lantern_ability(1)
	vm.ability_cooldown_remaining = 0.0
	var cast_ok_1: bool = vm.cast_active_lantern_ability()
	if not cast_ok_1 or not dummy_2.is_shackled():
		push_error("[VerifyProgression] Spell 1 (Shackles of the Penitent) failed to shackle enemy!")
		quit(1)
		return

	# Cycle to Spell 2 (Abyssal Blood Nova) and verify HP leech
	loadout.current_health = 50
	vm.cycle_lantern_ability(1)
	vm.ability_cooldown_remaining = 0.0
	var cast_ok_2: bool = vm.cast_active_lantern_ability()
	if not cast_ok_2 or loadout.current_health <= 50:
		push_error("[VerifyProgression] Spell 2 (Abyssal Blood Nova) failed to leech HP back to player!")
		quit(1)
		return
	print("[VerifyProgression] PASS 5: All 3 Active Left-Hand Lantern Spells ([F]/[G]) verified (Pyre Burn, Penitent Shackle, Blood Nova Leech).")

	# -------------------------------------------------------------------------
	# 7. Verify Procedural Dungeon Chest Spawning & Depth Tier Enemy Scaling
	# -------------------------------------------------------------------------
	var proc_gen: ProceduralDungeonGenerator = level.find_child("ProceduralExpeditionRoot", true, false) as ProceduralDungeonGenerator
	if proc_gen == null:
		push_error("[VerifyProgression] Missing ProceduralExpeditionRoot")
		quit(1)
		return

	proc_gen.generate_biome_dungeon(3, 4242, 2, Vector3(0.0, 0.5, -26.0))
	await process_frame

	var boss_chest: ReliquaryChest = proc_gen.find_child("Room11_ReliquaryChest", true, false) as ReliquaryChest
	var any_proc_enemy: TestDummyEnemy = proc_gen.find_child("Room1_Enemy_0", true, false) as TestDummyEnemy
	if boss_chest == null or boss_chest.guaranteed_relic_id != 3:
		push_error("[VerifyProgression] Procedural dungeon did not spawn ReliquaryChest with guaranteed_relic_id=3!")
		quit(1)
		return
	if any_proc_enemy == null or any_proc_enemy.depth_scale < 1.29:
		push_error("[VerifyProgression] Procedural enemy did not receive depth_tier=2 scaling (1.30x)!")
		quit(1)
		return
	print(
		"[VerifyProgression] PASS 6: Procedural Dungeon spawned ReliquaryChest (Relic ID=%d) and scaled Depth 2 enemies (scale=%.2fx)."
		% [boss_chest.guaranteed_relic_id, any_proc_enemy.depth_scale]
	)

	print("[VerifyProgression] ALL 6 RPG PROGRESSION, 3D LOOT & ACTIVE SPELL CHECKS PASSED 100%!")
	root.remove_child(level)
	level.free()
	quit(0)
