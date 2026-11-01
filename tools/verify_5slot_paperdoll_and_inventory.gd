extends SceneTree


func _init() -> void:
	var loadout: PlayerLoadoutManager = PlayerLoadoutManager.new()
	root.add_child(loadout)
	var menu: GothicCharacterMenu = GothicCharacterMenu.new()
	menu.loadout_manager = loadout
	root.add_child(menu)

	menu.open_field_character_menu()

	assert(menu.paperdoll_rig != null and is_instance_valid(menu.paperdoll_rig), "HunterPaperDollRig must be instantiated in GothicCharacterMenu")
	assert(menu.paperdoll_rig.head_root != null and menu.paperdoll_rig.head_root.name == "HeadRoot", "HeadRoot must exist")
	assert(menu.paperdoll_rig.chest_root != null and menu.paperdoll_rig.chest_root.name == "ChestRoot", "ChestRoot must exist")
	assert(menu.paperdoll_rig.hands_root != null and menu.paperdoll_rig.hands_root.name == "HandsRoot", "HandsRoot must exist")
	assert(menu.paperdoll_rig.legs_root != null and menu.paperdoll_rig.legs_root.name == "LegsRoot", "LegsRoot must exist")
	assert(menu.paperdoll_rig.feet_root != null and menu.paperdoll_rig.feet_root.name == "FeetRoot", "FeetRoot must exist")

	assert(menu.pedestal_camera != null, "PedestalCamera3D must exist")
	assert(menu.pedestal_camera.position.is_equal_approx(Vector3(0.0, 1.05, 2.55)), "PedestalCamera3D must frame the full-body Hunter at (0, 1.05, 2.55)")
	assert(menu._equip_slot_cards.size() == 7, "Left Panel must have 7 clickable equipment slot cards")
	assert(menu._inv_filter_buttons.size() == 4, "Right Panel must have 4 category filter buttons")

	loadout.equip_armor_slot("HEAD", 1)
	assert(int(loadout.equipped_armor_slots["HEAD"]) == 1, "equip_armor_slot('HEAD', 1) must update equipped_armor_slots['HEAD'] == 1")
	assert(int(menu.paperdoll_rig.equipped_slots["HEAD"]) == 1, "paperdoll_rig HeadRoot must sync live to set 1")
	assert(menu._equip_slot_titles[0].text.contains("Winged Sallet Helm"), "Left [ HEAD SLOT ] card must display Winged Sallet Helm")

	print("VERIFY_5SLOT_PAPERDOLL_AND_INVENTORY: ALL ASSERTIONS PASSED")
	quit(0)
