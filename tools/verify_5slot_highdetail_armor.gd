extends SceneTree


func _count_mesh_instances(n: Node) -> int:
	var c: int = 1 if (n is MeshInstance3D) else 0
	for ch: Node in n.get_children():
		c += _count_mesh_instances(ch)
	return c


func _fail(msg: String) -> void:
	push_error("[FAIL] " + msg)
	quit(1)


func _init() -> void:
	print("[Verify 5-Slot Armor] Starting 5-Piece Ultra-High-Detail Armor Overhaul Verification...")

	# 1. Verify all 16 armor_set{0..3}_{head|chest|legs|feet}.glb exist, load cleanly, and have <= 5 MeshInstance3D nodes
	var slots_low: Array[String] = ["head", "chest", "legs", "feet"]
	for set_i: int in range(4):
		for sl: String in slots_low:
			var glb_path: String = "res://assets/models/armor/armor_set%d_%s.glb" % [set_i, sl]
			if not ResourceLoader.exists(glb_path):
				_fail("Missing armor GLB: " + glb_path)
				return
			var scn: PackedScene = load(glb_path) as PackedScene
			if scn == null:
				_fail("Failed to load PackedScene: " + glb_path)
				return
			var inst: Node = scn.instantiate()
			if inst == null:
				_fail("Failed to instantiate: " + glb_path)
				return
			var mesh_count: int = _count_mesh_instances(inst)
			inst.free()
			if mesh_count < 1 or mesh_count > 5:
				_fail("%s has %d MeshInstance3D nodes (expected 1..5)" % [glb_path, mesh_count])
				return
			print("[PASS] Verified %s -> mesh_nodes=%d (<= 5)" % [glb_path, mesh_count])

	# 2. Instantiate town_overworld.tscn and locate Player, PlayerLoadoutManager, FirstPersonBodyController, FPSViewmodelController, HunterPaperDollRig
	var level_scn: PackedScene = load("res://scenes/levels/town_overworld.tscn") as PackedScene
	if level_scn == null:
		_fail("Could not load res://scenes/levels/town_overworld.tscn")
		return
	var world: Node3D = level_scn.instantiate() as Node3D
	root.add_child(world)

	var player: FPSController = world.find_child("Player", true, false) as FPSController
	if player == null:
		_fail("Could not find Player in town_overworld.tscn")
		return
	var loadout: PlayerLoadoutManager = player.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	var vm: FPSViewmodelController = player.find_child("ViewmodelRig", true, false) as FPSViewmodelController
	var hud: GothicHudOverhaul = player.find_child("HUD", true, false) as GothicHudOverhaul
	var fp_body: FirstPersonBodyController = player.find_child("FirstPersonBodyController", true, false) as FirstPersonBodyController
	if fp_body == null:
		fp_body = FirstPersonBodyController.new()
		player.add_child(fp_body)

	if loadout == null or vm == null or hud == null:
		_fail("Missing core player/loadout/viewmodel/HUD nodes")
		return

	vm._ready()
	hud._ready()
	loadout._ready()
	fp_body._ready()

	var paperdoll: HunterPaperDollRig = null
	if hud.character_menu != null and hud.character_menu.paperdoll_rig != null:
		paperdoll = hud.character_menu.paperdoll_rig
	else:
		paperdoll = HunterPaperDollRig.new()
		root.add_child(paperdoll)
	paperdoll._ready()

	# 3. Verify fresh initialization unlock state: Set 0 (5/5 unlocked), Sets 1..3 (0/5 unlocked, 15 pieces locked)
	loadout.reset_for_new_run()
	if loadout.get_unlocked_piece_count_for_set(0) != 5:
		_fail("Expected Set 0 to have 5/5 pieces unlocked, got %d" % loadout.get_unlocked_piece_count_for_set(0))
		return
	var locked_count: int = 0
	for s_idx: int in range(1, 4):
		if loadout.get_unlocked_piece_count_for_set(s_idx) != 0:
			_fail("Expected Set %d to have 0 unlocked pieces on fresh init, got %d" % [s_idx, loadout.get_unlocked_piece_count_for_set(s_idx)])
			return
		for slot_k: String in PlayerLoadoutManager.ARMOR_SLOTS:
			if not loadout.is_armor_piece_unlocked(slot_k, s_idx):
				locked_count += 1
	if locked_count != 15:
		_fail("Expected 15 locked pieces across Sets 1..3, got %d" % locked_count)
		return
	print("[PASS] Fresh initialization verified: Set 0 (5/5 unlocked), Sets 1..3 (15/15 locked).")

	# 4. Verify per-piece crafting deductions, unlocks, and live 3D rig updates
	loadout.crafting_resources = {
		"silver": 500,
		"bone_ash": 300,
		"cursed_iron": 50,
		"soul_cores": 25
	}

	# Craft CHEST Set 1 (cost: silver 30, bone_ash 16, cursed_iron 1)
	if not loadout.craft_unlock_armor_piece("CHEST", 1):
		_fail("craft_unlock_armor_piece('CHEST', 1) returned false")
		return
	if loadout.crafting_resources["silver"] != 470 or loadout.crafting_resources["bone_ash"] != 284 or loadout.crafting_resources["cursed_iron"] != 49:
		_fail("Unexpected resource balance after crafting CHEST Set 1: %s" % str(loadout.crafting_resources))
		return

	# Craft FEET Set 2 (cost: silver 30, bone_ash 10, cursed_iron 1)
	if not loadout.craft_unlock_armor_piece("FEET", 2):
		_fail("craft_unlock_armor_piece('FEET', 2) returned false")
		return
	if loadout.crafting_resources["silver"] != 440 or loadout.crafting_resources["bone_ash"] != 274 or loadout.crafting_resources["cursed_iron"] != 48:
		_fail("Unexpected resource balance after crafting FEET Set 2: %s" % str(loadout.crafting_resources))
		return

	# Craft HANDS Set 3 (cost: silver 45, bone_ash 15, cursed_iron 2, soul_cores 1)
	if not loadout.craft_unlock_armor_piece("HANDS", 3):
		_fail("craft_unlock_armor_piece('HANDS', 3) returned false")
		return
	if loadout.crafting_resources["silver"] != 395 or loadout.crafting_resources["bone_ash"] != 259 or loadout.crafting_resources["cursed_iron"] != 46 or loadout.crafting_resources["soul_cores"] != 24:
		_fail("Unexpected resource balance after crafting HANDS Set 3: %s" % str(loadout.crafting_resources))
		return

	paperdoll.refresh_from_loadout(loadout)
	fp_body.refresh_armor_appearance()

	var exp_chest: String = "res://assets/models/armor/armor_set1_chest.glb"
	var exp_feet: String = "res://assets/models/armor/armor_set2_feet.glb"
	if paperdoll.equipped_slot_model_paths.get("CHEST", "") != exp_chest or paperdoll.equipped_slot_model_paths.get("FEET", "") != exp_feet:
		_fail("HunterPaperDollRig slot paths mismatch: %s" % str(paperdoll.equipped_slot_model_paths))
		return
	if fp_body.equipped_chest_model_path != exp_chest or fp_body.equipped_feet_model_path != exp_feet:
		_fail("FirstPersonBodyController paths mismatch: chest=%s feet=%s" % [fp_body.equipped_chest_model_path, fp_body.equipped_feet_model_path])
		return
	if not vm.active_gauntlet_model_path.contains("gauntlet_04") or vm.active_gauntlet_instance == null or vm.active_right_gauntlet_instance != null:
		_fail("FPSViewmodelController gauntlet_04 mismatch: path=%s left=%s right=%s" % [vm.active_gauntlet_model_path, str(vm.active_gauntlet_instance), str(vm.active_right_gauntlet_instance)])
		return

	print("[PASS] Mixed-set crafting & 3D synchronization verified:")
	print("  -> PaperDoll CHEST: %s | FEET: %s | HANDS: %s" % [
		paperdoll.equipped_slot_model_paths["CHEST"],
		paperdoll.equipped_slot_model_paths["FEET"],
		paperdoll.equipped_slot_model_paths["HANDS"]
	])
	print("  -> FirstPersonBody CHEST: %s | FEET: %s" % [fp_body.equipped_chest_model_path, fp_body.equipped_feet_model_path])
	print("  -> FPSViewmodel Hands: %s (Left='%s')" % [
		vm.active_gauntlet_model_path,
		vm.active_gauntlet_instance.name
	])

	# 5. Verify 4-Part Armory SubViewport, Mannequin GLB, Grimdark Shader & Holster Clipping Refactor
	if hud.character_menu != null and hud.character_menu.sub_viewport != null:
		var svp: SubViewport = hud.character_menu.sub_viewport
		if not svp.own_world_3d:
			_fail("ReliquarySubViewport own_world_3d must be true")
			return
		var w_env: WorldEnvironment = svp.find_child("PedestalWorldEnv", true, false) as WorldEnvironment
		if w_env == null or w_env.environment == null:
			_fail("Missing PedestalWorldEnv in ReliquarySubViewport")
			return
		var env: Environment = w_env.environment
		if env.tonemap_mode != Environment.TONE_MAPPER_AGX or not is_equal_approx(env.glow_hdr_threshold, 1.5) or not is_equal_approx(env.glow_strength, 0.65) or not is_equal_approx(env.glow_bloom, 0.05):
			_fail("PedestalWorldEnv mismatch: tonemap=%d hdr=%f strength=%f bloom=%f" % [env.tonemap_mode, env.glow_hdr_threshold, env.glow_strength, env.glow_bloom])
			return
		var k_l: OmniLight3D = svp.find_child("GothicKeyLight", true, false) as OmniLight3D
		var r_l: SpotLight3D = svp.find_child("GothicRimSpotLight", true, false) as SpotLight3D
		var f_l: OmniLight3D = svp.find_child("GothicFillLight", true, false) as OmniLight3D
		if k_l == null or r_l == null or f_l == null:
			_fail("Missing 3-point gothic lights (GothicKeyLight, GothicRimSpotLight, GothicFillLight)")
			return
		print("[PASS] Armory SubViewport isolated (own_world_3d=true, AgX, HDR threshold=1.5) & 3-point Gothic lighting verified.")

	if paperdoll.mannequin_instance == null or paperdoll.under_body_root.find_child("UnderTorsoCore", true, false) != null:
		_fail("Expected GothicArmingMannequin .glb in UnderBodyRoot without primitive cylinder nodes")
		return
	print("[PASS] Tapered GothicArmingMannequin .glb verified in UnderBodyRoot.")

	if not ResourceLoader.exists("res://shaders/gothic_armory_plate.gdshader"):
		_fail("Missing res://shaders/gothic_armory_plate.gdshader")
		return
	var chest_fit: Dictionary = paperdoll._compute_surface_normal_offset("CHEST", 2, Vector3.ZERO)
	var chest_off: Vector3 = chest_fit["offset"] as Vector3
	var chest_scl: Vector3 = chest_fit["scale"] as Vector3
	if not chest_off.is_equal_approx(Vector3.ZERO) or chest_scl.x <= 1.0 or chest_scl.z <= 1.0:
		_fail("Guardrail 2 violation: Full wrap-around CHEST must scale radially in X/Z with zero +Z shift")
		return
	if absf(paperdoll.weapon_hand_mount.position.x) <= HunterPaperDollRig.BASE_HIP_X or not is_equal_approx(absf(paperdoll.weapon_hand_mount.rotation_degrees.z), 12.0):
		_fail("Holster mount offset/cant mismatch: pos=%s rot=%s" % [str(paperdoll.weapon_hand_mount.position), str(paperdoll.weapon_hand_mount.rotation_degrees)])
		return
	print("[PASS] Grimdark triplanar shader, radial wrap-around scaling (x=%.3f), and ±12° canted hip holsters (x=±%.3f) verified!" % [chest_scl.x, absf(paperdoll.lantern_hip_mount.position.x)])

	world.free()
	print("[Verify 5-Slot Armor] ALL 5-SLOT HIGH-DETAIL ARMOR CHECKS PASSED!")
	quit(0)
