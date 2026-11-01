extends SceneTree


func _init() -> void:
	call_deferred("_run_verification")


func _run_verification() -> void:
	print("[VerifyHub] Loading town_overworld.tscn...")
	var packed: PackedScene = load("res://scenes/levels/town_overworld.tscn") as PackedScene
	if packed == null:
		push_error("[VerifyHub] FAIL: Could not load town_overworld.tscn")
		quit(1)
		return

	var level: Node3D = packed.instantiate() as Node3D
	root.add_child(level)

	await process_frame
	await physics_frame
	await process_frame

	var workbench: HubStation = level.find_child("HubWeaponWorkbench", true, false) as HubStation
	var armor_stand: HubStation = level.find_child("HubArmorReliquaryStand", true, false) as HubStation
	var upgrade_font: HubStation = level.find_child("HubSanctuaryUpgradeFont", true, false) as HubStation
	var player: FPSController = level.find_child("Player", true, false) as FPSController
	if player == null:
		player = level.find_child("FPSPlayer", true, false) as FPSController

	if workbench == null or armor_stand == null or upgrade_font == null:
		push_error("[VerifyHub] FAIL: Missing one or more HubStation nodes in town_overworld.tscn")
		quit(1)
		return

	if player == null:
		push_error("[VerifyHub] FAIL: Missing FPSPlayer in town_overworld.tscn")
		quit(1)
		return

	var loadout: PlayerLoadoutManager = player.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	var vm: FPSViewmodelController = player.find_child("ViewmodelRig", true, false) as FPSViewmodelController
	var hud: FPSHUD = player.find_child("HUD", true, false) as FPSHUD
	var cam: Camera3D = player.find_child("Camera3D", true, false) as Camera3D

	if loadout == null or vm == null or hud == null or cam == null:
		push_error("[VerifyHub] FAIL: Missing PlayerLoadoutManager, ViewmodelRig, HUD, or Camera3D on FPSPlayer")
		quit(1)
		return

	print("[VerifyHub] Found all 3 HubStation nodes:")
	print("  - HubWeaponWorkbench @ ", workbench.global_position, " type=", workbench.station_type)
	print("  - HubArmorReliquaryStand @ ", armor_stand.global_position, " type=", armor_stand.station_type)
	print("  - HubSanctuaryUpgradeFont @ ", upgrade_font.global_position, " type=", upgrade_font.station_type)

	# 1. Verify RayCast3D focus and Weapon Workbench interaction
	player.global_position = Vector3(2.1, 4.0, -16.0)
	player.rotation = Vector3(0.0, deg_to_rad(-90.0), 0.0)
	if player.head != null:
		player.head.rotation = Vector3(deg_to_rad(-10.0), 0.0, 0.0)

	await physics_frame
	await process_frame

	if loadout._focused_station != workbench:
		push_error("[VerifyHub] FAIL: InteractionRayCast3D did not focus HubWeaponWorkbench (got: %s)" % str(loadout._focused_station))
		quit(1)
		return
	print("[VerifyHub] PASS: RayCast3D focused HubWeaponWorkbench; prompt = ", hud._prompt_label.text.replace("\n", " | "))

	# Cycle Weapon Mod 1 -> Quick-Silver Piercers
	workbench.interact(loadout)
	if loadout.weapon_mod_name != "Quick-Silver Piercers" or not is_equal_approx(loadout.damage_per_shot, 45.0):
		push_error("[VerifyHub] FAIL: Weapon Mod Tier 1 mismatch: " + loadout.weapon_mod_name)
		quit(1)
		return
	print("[VerifyHub] PASS: Weapon Mod cycled to ", loadout.weapon_mod_name, " (DMG=", loadout.damage_per_shot, ", RuneColor=", vm.active_rune_color, ")")

	# Cycle Weapon Mod 2 -> Brimstone Hellfire
	workbench.interact(loadout)
	if loadout.weapon_mod_name != "Brimstone Hellfire" or not is_equal_approx(loadout.damage_per_shot, 60.0):
		push_error("[VerifyHub] FAIL: Weapon Mod Tier 2 mismatch: " + loadout.weapon_mod_name)
		quit(1)
		return
	print("[VerifyHub] PASS: Weapon Mod cycled to ", loadout.weapon_mod_name, " (DMG=", loadout.damage_per_shot, ", RuneColor=", vm.active_rune_color, ")")

	# 2. Verify RayCast3D focus and Armor Reliquary Stand interaction
	player.global_position = Vector3(-2.1, 4.0, -16.0)
	player.rotation = Vector3(0.0, deg_to_rad(90.0), 0.0)
	if player.head != null:
		player.head.rotation = Vector3(deg_to_rad(-10.0), 0.0, 0.0)

	await physics_frame
	await process_frame

	if loadout._focused_station != armor_stand:
		push_error("[VerifyHub] FAIL: InteractionRayCast3D did not focus HubArmorReliquaryStand (got: %s)" % str(loadout._focused_station))
		quit(1)
		return
	print("[VerifyHub] PASS: RayCast3D focused HubArmorReliquaryStand; prompt = ", hud._prompt_label.text.replace("\n", " | "))

	# Cycle Armor Tier 1 -> Inquisitor Blued-Steel Plate (75 Armor)
	armor_stand.interact(loadout)
	if loadout.max_armor != 75 or loadout.current_armor != 75:
		push_error("[VerifyHub] FAIL: Armor Tier 1 mismatch: " + str(loadout.max_armor))
		quit(1)
		return
	print("[VerifyHub] PASS: Armor cycled to ", loadout.armor_tier_name, " (Armor=", loadout.current_armor, ", GauntletColor=", vm.active_armor_plate_color, ")")

	# Cycle Armor Tier 2 -> Gilded Cathedral Templar Armor (125 Armor)
	armor_stand.interact(loadout)
	if loadout.max_armor != 125 or loadout.current_armor != 125:
		push_error("[VerifyHub] FAIL: Armor Tier 2 mismatch: " + str(loadout.max_armor))
		quit(1)
		return
	print("[VerifyHub] PASS: Armor cycled to ", loadout.armor_tier_name, " (Armor=", loadout.current_armor, ", GauntletColor=", vm.active_armor_plate_color, ")")

	# 3. Verify RayCast3D focus and Sanctuary Upgrade Font interaction
	player.global_position = Vector3(0.0, 4.0, -12.6)
	player.rotation = Vector3(0.0, 0.0, 0.0)
	if player.head != null:
		player.head.rotation = Vector3(deg_to_rad(-18.0), 0.0, 0.0)

	await physics_frame
	await process_frame

	if loadout._focused_station != upgrade_font:
		push_error("[VerifyHub] FAIL: InteractionRayCast3D did not focus HubSanctuaryUpgradeFont (got: %s)" % str(loadout._focused_station))
		quit(1)
		return
	print("[VerifyHub] PASS: RayCast3D focused HubSanctuaryUpgradeFont; prompt = ", hud._prompt_label.text.replace("\n", " | "))

	vm.current_ammo = 2
	upgrade_font.interact(loadout)
	if loadout.occult_essence != 250 or loadout.occult_blessing_level != 2 or loadout.max_health != 125 or vm.current_ammo != 6:
		push_error("[VerifyHub] FAIL: Sanctuary Upgrade Font state mismatch")
		quit(1)
		return
	print(
		"[VerifyHub] PASS: Consecrated Sanctuary Upgrade -> Lv.%d | HP=%d/%d | Essence=%d | LanternBonus=+%.1fm | Ammo=%d/%d"
		% [loadout.occult_blessing_level, loadout.current_health, loadout.max_health, loadout.occult_essence, loadout.lantern_radius_bonus, vm.current_ammo, vm.max_ammo]
	)
	print("[VerifyHub] ALL HUNTER'S SANCTUARY HUB VERIFICATION CHECKS PASSED 100%!")
	level.queue_free()
	await process_frame
	quit(0)
