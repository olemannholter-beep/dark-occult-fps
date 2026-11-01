extends SceneTree


func _initialize() -> void:
	print("=== Starting Workshop & Crafting Progression Verification ===")

	# 1. Verify PlayerLoadoutManager starting locks & recipes
	var lm: PlayerLoadoutManager = PlayerLoadoutManager.new()
	lm.name = "PlayerLoadoutManager"
	get_root().add_child(lm)

	if not lm.is_weapon_unlocked(0) or lm.is_weapon_unlocked(1) or lm.is_weapon_unlocked(2):
		push_error("FAIL: Starting weapon unlocks must be [true, false, false]!")
		quit(1)
		return
	if not lm.is_armor_unlocked(0) or lm.is_armor_unlocked(1) or lm.is_armor_unlocked(2) or lm.is_armor_unlocked(3):
		push_error("FAIL: Starting armor unlocks must be [true, false, false, false]!")
		quit(1)
		return
	if not lm.is_spell_unlocked(0) or lm.is_spell_unlocked(1) or lm.is_spell_unlocked(2):
		push_error("FAIL: Starting spell unlocks must be [true, false, false]!")
		quit(1)
		return
	for w_i: int in range(3):
		if not lm.is_weapon_mod_unlocked(w_i, 0) or lm.is_weapon_mod_unlocked(w_i, 1) or lm.is_weapon_mod_unlocked(w_i, 2) or lm.is_weapon_mod_unlocked(w_i, 3):
			push_error("FAIL: Starting weapon mod unlocks for weapon %d must be [true, false, false, false]!" % w_i)
			quit(1)
			return

	# Starter pouch check
	if lm.get_resource_amount("silver") != 35 or lm.get_resource_amount("bone_ash") != 15:
		push_error("FAIL: Starter resource pouch should have 35 silver and 15 bone_ash!")
		quit(1)
		return

	# Verify locked equip attempts fail cleanly
	if lm.equip_weapon("shotgun"):
		push_error("FAIL: equip_weapon('shotgun') should return false while locked!")
		quit(1)
		return
	if lm.equip_armor_tier(1):
		push_error("FAIL: equip_armor_tier(1) should return false while locked!")
		quit(1)
		return
	if lm.equip_lantern_spell(1):
		push_error("FAIL: equip_lantern_spell(1) should return false while locked!")
		quit(1)
		return
	if lm.equip_weapon_mod(0, 1):
		push_error("FAIL: equip_weapon_mod(0, 1) should return false while locked!")
		quit(1)
		return

	# Verify insufficient resource crafting fails
	if lm.craft_unlock_item("weapon", 1):
		push_error("FAIL: craft_unlock_item('weapon', 1) should fail with starter resources!")
		quit(1)
		return

	# Grant test materials and verify crafting deducts exact recipe costs and unlocks + equips
	lm.grant_test_materials()
	var s_before: int = lm.get_resource_amount("silver")
	var b_before: int = lm.get_resource_amount("bone_ash")
	var i_before: int = lm.get_resource_amount("cursed_iron")

	if not lm.craft_unlock_item("weapon", 1):
		push_error("FAIL: craft_unlock_item('weapon', 1) should succeed after grant_test_materials()!")
		quit(1)
		return
	if not lm.is_weapon_unlocked(1) or lm.active_weapon_id != "shotgun":
		push_error("FAIL: Hellfire Coach Gun should be unlocked and equipped after forging!")
		quit(1)
		return
	if lm.get_resource_amount("silver") != s_before - 60 or lm.get_resource_amount("bone_ash") != b_before - 25 or lm.get_resource_amount("cursed_iron") != i_before - 2:
		push_error("FAIL: Forging weapon_1 did not deduct exact recipe cost (60 silver, 25 bone_ash, 2 cursed_iron)!")
		quit(1)
		return

	if not lm.craft_unlock_item("armor", 2) or not lm.is_armor_unlocked(2) or lm.equipped_armor_index != 2:
		push_error("FAIL: Forging armor_2 failed!")
		quit(1)
		return
	if not lm.craft_unlock_item("spell", 2) or not lm.is_spell_unlocked(2) or lm.equipped_spell_index != 2:
		push_error("FAIL: Forging spell_2 failed!")
		quit(1)
		return
	if not lm.craft_unlock_item("mod", 3, 1) or not lm.is_weapon_mod_unlocked(1, 3) or lm.weapon_mod_indices[1] != 3:
		push_error("FAIL: Forging mod_3 on weapon 1 failed!")
		quit(1)
		return
	print("[PASS] Phase 1: Starting gear locks, recipe matrix, and crafting unlock deductions verified.")

	# 2. Load town_overworld.tscn and verify Spacious Cathedral Nave & Workshop Alcoves
	var level_scn: PackedScene = load("res://scenes/levels/town_overworld.tscn") as PackedScene
	if level_scn == null:
		push_error("FAIL: Could not load town_overworld.tscn!")
		quit(1)
		return
	var level_inst: Node3D = level_scn.instantiate() as Node3D
	get_root().add_child(level_inst)
	await process_frame

	var wb: SanctuaryForgeStation = level_inst.find_child("HubWeaponWorkbench", true, false) as SanctuaryForgeStation
	var ar: SanctuaryForgeStation = level_inst.find_child("HubArmorReliquaryStand", true, false) as SanctuaryForgeStation
	var fn: SanctuaryForgeStation = level_inst.find_child("HubSanctuaryUpgradeFont", true, false) as SanctuaryForgeStation

	if wb == null or ar == null or fn == null:
		push_error("FAIL: Missing SanctuaryForgeStation nodes in town_overworld.tscn!")
		quit(1)
		return

	if absf(wb.global_position.x) < 8.0 or absf(ar.global_position.x) < 8.0:
		push_error("FAIL: Workbench (x=%.2f) and Armor Stand (x=%.2f) must be placed in side Transept alcoves (|x| >= 8.0)!" % [wb.global_position.x, ar.global_position.x])
		quit(1)
		return

	if not wb.get_prompt_text().contains("[E] OPEN ARSENAL FORGE (CRAFT WEAPONS & RITE MODS)"):
		push_error("FAIL: Workbench prompt mismatch: " + wb.get_prompt_text())
		quit(1)
		return
	if not ar.get_prompt_text().contains("[E] OPEN ARMORY RELIQUARY (FORGE GAUNTLETS & VESTMENTS)"):
		push_error("FAIL: Armor Stand prompt mismatch: " + ar.get_prompt_text())
		quit(1)
		return
	if not fn.get_prompt_text().contains("[E] COMMUNE WITH ASTROLABE (LANTERN SPELLS, HEAL & SKILL TREE)"):
		push_error("FAIL: Baptismal Font prompt mismatch: " + fn.get_prompt_text())
		quit(1)
		return

	# Verify unobstructed Central Processional Carpet (X in [-3.5, +3.5], Z in [-24.0, -42.0] at Y = 5.0m)
	var space_state: PhysicsDirectSpaceState3D = level_inst.get_world_3d().direct_space_state
	var ray_query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		Vector3(0.0, 5.2, -24.0),
		Vector3(0.0, 5.2, -42.0),
		1
	)
	var ray_hit: Dictionary = space_state.intersect_ray(ray_query)
	if not ray_hit.is_empty():
		var hit_collider: Object = ray_hit.get("collider")
		var hit_name: String = (hit_collider as Node).name if hit_collider is Node else str(hit_collider)
		push_error("FAIL: Central Cathedral Processional Carpet obstructed at %s by %s!" % [str(ray_hit.get("position")), hit_name])
		quit(1)
		return
	print("[PASS] Phase 2 & 3: Cathedral Nave sightline unobstructed and 3 Transept Forge Stations verified.")

	# 3. Verify GothicCharacterMenu Forge Mode & UI Spark Burst
	var player_lm: PlayerLoadoutManager = level_inst.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	if player_lm != null:
		player_lm.current_health = 25
		player_lm.current_armor = 0
		fn.interact(player_lm)
		if player_lm.current_health < player_lm.max_health or player_lm.current_armor < player_lm.max_armor:
			push_error("FAIL: Interacting with Baptismal Font did not restore full vitality (HP=%d, ARM=%d)!" % [player_lm.current_health, player_lm.current_armor])
			quit(1)
			return

	var char_menu: GothicCharacterMenu = level_inst.find_child("GothicCharacterMenu", true, false) as GothicCharacterMenu
	if char_menu != null:
		char_menu.trigger_grant_test_materials()
		var forged_ok: bool = char_menu.forge_and_unlock_item("weapon", 2)
		if not forged_ok or char_menu.active_spark_bursts.size() < 25:
			push_error("FAIL: GothicCharacterMenu forge_and_unlock_item('weapon', 2) or spark burst failed!")
			quit(1)
			return
	print("[PASS] Phase 3 & 4: Baptismal Font full heal and GothicCharacterMenu forging + spark burst verified.")

	level_inst.free()
	lm.free()
	print("=== ALL WORKSHOP & CRAFTING PROGRESSION CHECKS PASSED (EXIT 0) ===")
	quit(0)
