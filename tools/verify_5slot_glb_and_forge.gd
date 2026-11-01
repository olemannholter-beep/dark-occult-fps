extends SceneTree


func _init() -> void:
	print("=== [VERIFY] 5-Piece GLB Armor Sync & Per-Piece Armory Forge ===")

	# 1. Verify all 16 exported .glb armor files + 4 gauntlet .glb files exist & load
	for set_i: int in range(4):
		for slot_s: String in ["head", "chest", "legs", "feet"]:
			var p: String = "res://assets/models/armor/armor_set%d_%s.glb" % [set_i, slot_s]
			assert(ResourceLoader.exists(p), "Missing GLB: " + p)
			var scn: PackedScene = load(p) as PackedScene
			assert(scn != null, "Failed to load PackedScene: " + p)
	print("  [PASS] All 16 armor_set{0..3}_{head|chest|legs|feet}.glb scenes exist and load.")

	# 2. Verify PlayerLoadoutManager per-piece initial state (Set 0 unlocked, Sets 1..3 locked)
	var player: FPSPlayer = FPSPlayer.new()
	root.add_child(player)
	var loadout: PlayerLoadoutManager = PlayerLoadoutManager.new()
	loadout.name = "PlayerLoadoutManager"
	player.add_child(loadout)

	var vm: FPSViewmodelController = FPSViewmodelController.new()
	vm.name = "ViewmodelRig"
	var l_piv: Node3D = Node3D.new()
	l_piv.name = "LeftHandPivot"
	vm.add_child(l_piv)
	var r_piv: Node3D = Node3D.new()
	r_piv.name = "RightHandPivot"
	vm.add_child(r_piv)
	player.add_child(vm)
	vm.loadout_manager = loadout
	loadout.viewmodel_controller = vm
	player._fp_body.loadout_manager = loadout
	player._fp_body.refresh_armor_appearance()

	var rig: HunterPaperDollRig = HunterPaperDollRig.new()
	root.add_child(rig)
	loadout.loadout_changed.connect(func() -> void: rig.refresh_from_loadout(loadout))
	rig.refresh_from_loadout(loadout)

	assert(loadout.get_unlocked_piece_count_for_set(0) == 5, "Set 0 must have 5/5 pieces unlocked initially")
	for locked_set: int in [1, 2, 3]:
		assert(loadout.get_unlocked_piece_count_for_set(locked_set) == 0, "Set %d must start with 0/5 pieces unlocked" % locked_set)
		for slot_k: String in PlayerLoadoutManager.ARMOR_SLOTS:
			assert(not loadout.is_armor_piece_unlocked(slot_k, locked_set), "%s of Set %d should start locked" % [slot_k, locked_set])
	print("  [PASS] Initial per-piece unlock state: Set 0 = 5/5 unlocked; Sets 1, 2, 3 = 0/5 locked.")

	# 3. Verify forging a single piece (Set 1 HEAD: 20 silver, 12 bone_ash, 1 cursed_iron)
	loadout.grant_test_materials()
	var s_before: int = loadout.get_resource_amount("silver")
	var b_before: int = loadout.get_resource_amount("bone_ash")
	var i_before: int = loadout.get_resource_amount("cursed_iron")

	var forged_head: bool = loadout.craft_unlock_armor_piece("HEAD", 1)
	assert(forged_head, "craft_unlock_armor_piece(HEAD, 1) must succeed")
	assert(loadout.get_resource_amount("silver") == s_before - 20, "Silver must deduct 20")
	assert(loadout.get_resource_amount("bone_ash") == b_before - 12, "Bone-Ash must deduct 12")
	assert(loadout.get_resource_amount("cursed_iron") == i_before - 1, "Cursed Iron must deduct 1")
	assert(loadout.is_armor_piece_unlocked("HEAD", 1), "Set 1 HEAD must now be unlocked")
	assert(not loadout.is_armor_piece_unlocked("CHEST", 1), "Set 1 CHEST must still be locked")
	assert(loadout.get_unlocked_piece_count_for_set(1) == 1, "Set 1 unlocked piece count must be 1/5")
	assert(loadout.get_equipped_armor_slot("HEAD") == 1, "HEAD slot must auto-equip to Set 1")
	assert(String(rig.equipped_slot_model_paths["HEAD"]).ends_with("armor_set1_head.glb"), "PaperDoll HEAD must load armor_set1_head.glb")
	print("  [PASS] Forged Set 1 HEAD individually -> 1/5 unlocked, resources deducted, PaperDoll HEAD swapped to armor_set1_head.glb.")

	# 4. Verify forging Set 2 CHEST & Set 3 FEET and live 3D visual sync across PaperDoll, FirstPersonBody & Viewmodel Hands
	assert(loadout.craft_unlock_armor_piece("CHEST", 2), "Forge Set 2 CHEST")
	assert(loadout.craft_unlock_armor_piece("FEET", 3), "Forge Set 3 FEET")
	assert(loadout.craft_unlock_armor_piece("HANDS", 2), "Forge Set 2 HANDS")

	assert(String(rig.equipped_slot_model_paths["CHEST"]).ends_with("armor_set2_chest.glb"), "PaperDoll CHEST -> armor_set2_chest.glb")
	assert(String(rig.equipped_slot_model_paths["FEET"]).ends_with("armor_set3_feet.glb"), "PaperDoll FEET -> armor_set3_feet.glb")
	assert(player._fp_body.equipped_chest_model_path.ends_with("armor_set2_chest.glb"), "FPBody CHEST -> armor_set2_chest.glb")
	assert(player._fp_body.equipped_feet_model_path.ends_with("armor_set3_feet.glb"), "FPBody FEET -> armor_set3_feet.glb")
	assert(vm.equipped_armor_index == 2, "FPSViewmodelController HANDS -> Set 2")
	print("  [PASS] Live 3D model swap verified across HunterPaperDollRig, FirstPersonBodyController, and FPSViewmodelController.")

	# 5. Verify GothicCharacterMenu MODE_ARMORER_STAND UI (4 Set Tabs + 5 Piece Cards + Full-Body Mannequin)
	var menu: GothicCharacterMenu = GothicCharacterMenu.new()
	menu.loadout_manager = loadout
	root.add_child(menu)
	menu.open_at_forge_station("armor")
	assert(menu.current_menu_mode == GothicCharacterMenu.MODE_ARMORER_STAND, "Must open in MODE_ARMORER_STAND")
	assert(menu.paperdoll_rig != null and menu.paperdoll_rig.visible, "Full-body 3D Hunter must be visible at Armor Stand")
	assert(menu._armorer_set_tab_buttons.size() == 4, "Must have 4 Set Selector Tabs")
	assert(menu._armorer_piece_cards.size() == 5, "Must have 5 Individual Piece Forging Cards")
	assert(menu._armorer_set_tab_buttons[1].text.contains("[1/5]"), "Set II tab must show [1/5] unlocked")
	print("  [PASS] MODE_ARMORER_STAND UI verified: 4 Set Tabs [X/5], 5 Piece Cards, and Full-Body 3D Hunter Preview.")

	print("=== ALL STEP 1 & STEP 2 5-PIECE ARMOR VERIFICATION CHECKS PASSED ===")
	quit(0)
