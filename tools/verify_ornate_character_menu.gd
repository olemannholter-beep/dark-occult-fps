extends SceneTree

var _failures: int = 0


func _assert_cond(cond: bool, msg: String) -> void:
	if cond:
		print("[PASS] " + msg)
	else:
		_failures += 1
		push_error("[FAIL] " + msg)


func _init() -> void:
	print("==================================================================")
	print("  VERIFYING ORNATE GOTHIC CHARACTER MENU & 20-NODE ASTROLABE")
	print("==================================================================")

	# ------------------------------------------------------------------
	# PHASE 1: Verify 4 Stereo UI Foley .wav Assets
	# ------------------------------------------------------------------
	var ui_wavs: Array[String] = [
		"res://assets/audio/sfx/ui_grimoire_open.wav",
		"res://assets/audio/sfx/ui_armor_equip_clank.wav",
		"res://assets/audio/sfx/ui_skill_consecrate_chime.wav",
		"res://assets/audio/sfx/ui_tab_page_turn.wav"
	]
	for wav_path: String in ui_wavs:
		var exists: bool = ResourceLoader.exists(wav_path)
		_assert_cond(exists, "Audio asset exists: " + wav_path)
		if exists:
			var stream: AudioStreamWAV = load(wav_path) as AudioStreamWAV
			_assert_cond(stream != null and stream.stereo, "Audio asset loads as 2-Channel Stereo WAV: " + wav_path)

	# ------------------------------------------------------------------
	# PHASE 2: Verify Obsidian-Vellum & Gilded Filigree Shader
	# ------------------------------------------------------------------
	var shader_path: String = "res://shaders/gothic_vellum_frame.gdshader"
	_assert_cond(ResourceLoader.exists(shader_path), "Shader exists: " + shader_path)
	var vellum_shader: Shader = load(shader_path) as Shader
	_assert_cond(vellum_shader != null, "Shader loads cleanly: " + shader_path)

	# ------------------------------------------------------------------
	# PHASE 3: Verify PlayerLoadoutManager 20-Node Astrolabe & Catalogs
	# ------------------------------------------------------------------
	var armor_catalog: Array[Dictionary] = PlayerLoadoutManager.get_armor_set_catalog()
	_assert_cond(armor_catalog.size() == 4, "PlayerLoadoutManager defines 4 Armor Sets (got %d)" % armor_catalog.size())
	_assert_cond(int(armor_catalog[0]["armor"]) == 35, "Armor 0 (Grave-Stalker) has 35 Armor")
	_assert_cond(int(armor_catalog[1]["armor"]) == 55, "Armor 1 (Inquisitor Brigandine) has 55 Armor")
	_assert_cond(int(armor_catalog[2]["armor"]) == 90, "Armor 2 (Catacomb Juggernaut) has 90 Armor")
	_assert_cond(int(armor_catalog[3]["armor"]) == 65, "Armor 3 (Abyssal Reliquary) has 65 Armor")

	var weapon_mods: Array[Dictionary] = PlayerLoadoutManager.get_weapon_mod_catalog()
	_assert_cond(weapon_mods.size() == 4, "PlayerLoadoutManager defines 4 Alchemical Rite Mods per weapon (got %d)" % weapon_mods.size())

	var spell_catalog: Array[Dictionary] = PlayerLoadoutManager.get_lantern_spell_catalog()
	_assert_cond(spell_catalog.size() == 3, "PlayerLoadoutManager defines 3 Lantern Spells (got %d)" % spell_catalog.size())

	var skill_catalog: Dictionary[String, Dictionary] = PlayerLoadoutManager.get_skill_tree_catalog()
	var skill_ids: Array[String] = PlayerLoadoutManager.get_skill_node_ids()
	_assert_cond(skill_catalog.size() == 20 and skill_ids.size() == 20, "PlayerLoadoutManager defines all 20 Interconnected Skill Nodes (16 core + 4 synergy bridges)")

	var syn_bridges: Array[String] = ["syn_blood_quick", "syn_quick_iron", "syn_iron_eld", "syn_eld_blood"]
	for syn_id: String in syn_bridges:
		_assert_cond(skill_catalog.has(syn_id), "Skill catalog contains cross-path synergy bridge: " + syn_id)
		var prereqs: Array = skill_catalog[syn_id]["prereqs"] as Array
		_assert_cond(prereqs.size() == 2, "Synergy bridge %s requires 2 adjacent Tier-2 prerequisites (got %d)" % [syn_id, prereqs.size()])

	# ------------------------------------------------------------------
	# PHASE 4 & 5: Instantiate town_overworld.tscn and Verify Live UI + 3D Pedestal + Skill Tree
	# ------------------------------------------------------------------
	var level_scn: PackedScene = load("res://scenes/levels/town_overworld.tscn") as PackedScene
	_assert_cond(level_scn != null, "Loaded res://scenes/levels/town_overworld.tscn")
	var level_inst: Node3D = level_scn.instantiate() as Node3D
	root.add_child(level_inst)

	var player: FPSController = level_inst.get_node_or_null("Player") as FPSController
	_assert_cond(player != null, "Found Player node in town_overworld.tscn")

	var lm: PlayerLoadoutManager = player.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	_assert_cond(lm != null, "Found PlayerLoadoutManager on Player")
	_assert_cond(lm.skill_points == 3, "Player starts at Level 1 with 3 skill_points (got %d)" % lm.skill_points)
	_assert_cond(lm.weapon_mod_indices.size() == 3, "PlayerLoadoutManager tracks weapon_mod_indices for all 3 weapons")

	var hud: GothicHudOverhaul = player.find_child("HUD", true, false) as GothicHudOverhaul
	_assert_cond(hud != null and hud.character_menu != null, "Found GothicCharacterMenu inside Player HUD")

	var menu: GothicCharacterMenu = hud.character_menu
	menu.set_menu_open(true)
	_assert_cond(menu.is_menu_open and menu.visible, "GothicCharacterMenu opens cleanly via set_menu_open(true)")
	_assert_cond(menu.vellum_shader_mat != null, "GothicCharacterMenu backing panel uses gothic_vellum_frame.gdshader")
	_assert_cond(menu.sub_viewport != null and menu.sub_viewport.own_world_3d, "GothicCharacterMenu has isolated 3D SubViewport (own_world_3d = true)")
	_assert_cond(menu.pedestal_pivot != null and menu.pedestal_plinth_mesh != null, "Reliquary SubViewport contains rotating PedestalPivot & OctagonalStonePlinth")

	# Test forging & switching armors (0..3) and weapons (0..2) on the live 3D Pedestal
	menu.trigger_grant_test_materials()
	menu.trigger_grant_test_materials()
	for arm_i: int in range(4):
		menu.select_armor_plaque(arm_i)
		_assert_cond(
			lm.equipped_armor_index == arm_i and menu.preview_armor_index == arm_i and menu.preview_gauntlet_node != null,
			"Switching to Armor %d updates equipped_armor_index and 3D preview_gauntlet_node (%s)" % [arm_i, menu.preview_gauntlet_node.name if menu.preview_gauntlet_node != null else "null"]
		)

	var weapon_slots: Array[String] = ["revolver", "shotgun", "stakedriver"]
	for w_slot: int in range(3):
		var mod_to_test: int = (w_slot + 1) % 4
		menu.select_weapon_mod_socket(w_slot, mod_to_test)
		_assert_cond(
			lm.weapon_mod_indices[w_slot] == mod_to_test and menu.preview_weapon_id == weapon_slots[w_slot] and menu.preview_weapon_node != null,
			"Equipping Weapon %d (%s) Mod %d updates weapon_mod_indices and 3D preview_weapon_node (%s)" % [w_slot, weapon_slots[w_slot], mod_to_test, menu.preview_weapon_node.name if menu.preview_weapon_node != null else "null"]
		)

	# Test hover stat delta comparison in the 12-stat Hunter Ledger
	menu.select_armor_plaque(0) # 35 Armor
	var base_ledger: Dictionary[String, float] = lm.compute_stat_ledger(-1, "")
	var hover_juggernaut_ledger: Dictionary[String, float] = lm.compute_stat_ledger(2, "") # 90 Armor (+55 Armor delta, +20 HP delta)
	_assert_cond(base_ledger.size() == 12, "Hunter Ledger computes all 12 live combat & occult stats (got %d)" % base_ledger.size())
	_assert_cond(
		roundi(hover_juggernaut_ledger["max_armor"] - base_ledger["max_armor"]) == 55,
		"Hovering Juggernaut Plate over Grave-Stalker Leather previews +55 Max Armor delta"
	)

	# Test 20-Node Celestial Astrolabe multi-prerequisite enforcement & Synergy Bridge unlocking
	menu.switch_tab(1)
	_assert_cond(menu.active_tab == 1, "Switched to Tab II (Celestial Astrolabe of Rites)")

	# Before prerequisites, syn_blood_quick (requires blood_2 AND quick_2) cannot be unlocked
	_assert_cond(not lm.can_unlock_skill("syn_blood_quick"), "Synergy Bridge syn_blood_quick is locked before prerequisites blood_2 and quick_2")

	# Grant extra SP via Sanctuary Blessing so we can test unlocking both branches + synergy bridge
	menu.trigger_sanctuary_blessing() # +2 SP -> 5 SP
	menu.trigger_sanctuary_blessing() # +2 SP -> 7 SP
	_assert_cond(lm.skill_points == 7, "Sanctuary Blessing button granted +4 SP (total 7 SP)")

	_assert_cond(menu.select_skill_node("blood_1", true), "Unlocked Tier 1 node blood_1 (1 SP)")
	_assert_cond(menu.select_skill_node("blood_2", true), "Unlocked Tier 2 node blood_2 (1 SP)")
	_assert_cond(not lm.can_unlock_skill("syn_blood_quick"), "syn_blood_quick STILL locked when only blood_2 is unlocked (missing quick_2)")

	_assert_cond(menu.select_skill_node("quick_1", true), "Unlocked Tier 1 node quick_1 (1 SP)")
	_assert_cond(menu.select_skill_node("quick_2", true), "Unlocked Tier 2 node quick_2 (1 SP)")
	_assert_cond(lm.can_unlock_skill("syn_blood_quick"), "syn_blood_quick is NOW unlockable once BOTH blood_2 and quick_2 are consecrated")

	_assert_cond(menu.select_skill_node("syn_blood_quick", true), "Unlocked Cross-Path Synergy Bridge syn_blood_quick (2 SP)")
	_assert_cond(menu.active_spark_bursts.size() >= 28, "Unlocking skill spawned 28+ procedural ember sparks (active=%d)" % menu.active_spark_bursts.size())
	_assert_cond(menu.active_shockwave_rings.size() >= 1, "Unlocking skill spawned expanding golden shockwave ring")
	_assert_cond(lm.get_unlocked_skills_count() == 5 and lm.skill_points == 1, "5 skills unlocked, 6 SP spent, 1 SP remaining")

	# Test Rite of Absolution (respec_all_skills)
	var refunded_sp: int = menu.trigger_respec_rites()
	_assert_cond(
		refunded_sp == 6 and lm.skill_points == 7 and lm.get_unlocked_skills_count() == 0,
		"respec_all_skills() refunded all 6 spent SP (total SP=%d, unlocked=%d)" % [lm.skill_points, lm.get_unlocked_skills_count()]
	)

	level_inst.free()

	print("==================================================================")
	if _failures == 0:
		print("  ALL PHASE 1-5 ORNATE CHARACTER MENU CHECKS PASSED (0 FAILURES)")
		print("==================================================================")
		quit(0)
	else:
		push_error("  VERIFICATION FAILED WITH %d ERRORS" % _failures)
		quit(1)
