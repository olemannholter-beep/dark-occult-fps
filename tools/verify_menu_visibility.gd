extends SceneTree

var _failures: int = 0


func _assert_cond(cond: bool, msg: String) -> void:
	if cond:
		print("[PASS] " + msg)
	else:
		_failures += 1
		push_error("[FAIL] " + msg)


func _collect_controls(node: Node, out_labels: Array[Label], out_buttons: Array[Button]) -> void:
	if node is Label:
		out_labels.append(node as Label)
	elif node is Button:
		out_buttons.append(node as Button)
	for child: Node in node.get_children():
		_collect_controls(child, out_labels, out_buttons)


func _initialize() -> void:
	print("==================================================================")
	print("  VERIFYING 4K UI SCALING & HIGH-CONTRAST GOTHIC MENU VISIBILITY")
	print("==================================================================")

	# ------------------------------------------------------------------
	# 1. Verify project.godot 1920x1080 Canvas Scaling Settings
	# ------------------------------------------------------------------
	var vp_w: int = int(ProjectSettings.get_setting("display/window/size/viewport_width", 0))
	var vp_h: int = int(ProjectSettings.get_setting("display/window/size/viewport_height", 0))
	var stretch_mode: String = String(ProjectSettings.get_setting("display/window/stretch/mode", ""))
	var stretch_aspect: String = String(ProjectSettings.get_setting("display/window/stretch/aspect", ""))
	var stretch_scale_mode: String = String(ProjectSettings.get_setting("display/window/stretch/scale_mode", ""))

	_assert_cond(vp_w == 1920 and vp_h == 1080, "Reference viewport resolution is 1920x1080 (got %dx%d)" % [vp_w, vp_h])
	_assert_cond(stretch_mode == "canvas_items", "Stretch mode is 'canvas_items' (got '%s')" % stretch_mode)
	_assert_cond(stretch_aspect == "expand", "Stretch aspect is 'expand' (got '%s')" % stretch_aspect)
	_assert_cond(stretch_scale_mode == "fractional", "Stretch scale_mode is 'fractional' (got '%s')" % stretch_scale_mode)

	# ------------------------------------------------------------------
	# 2. Instantiate town_overworld.tscn and Open GothicCharacterMenu
	# ------------------------------------------------------------------
	var level_scn: PackedScene = load("res://scenes/levels/town_overworld.tscn") as PackedScene
	_assert_cond(level_scn != null, "Loaded res://scenes/levels/town_overworld.tscn")
	var level_inst: Node3D = level_scn.instantiate() as Node3D
	root.add_child(level_inst)
	await process_frame

	var player: FPSController = level_inst.get_node_or_null("Player") as FPSController
	_assert_cond(player != null, "Found Player node in town_overworld.tscn")

	var hud: GothicHudOverhaul = player.find_child("HUD", true, false) as GothicHudOverhaul
	_assert_cond(hud != null and hud.character_menu != null, "Found GothicCharacterMenu inside Player HUD")

	var menu: GothicCharacterMenu = hud.character_menu
	menu.set_menu_open(true)
	await process_frame

	_assert_cond(menu.is_menu_open and menu.visible, "GothicCharacterMenu is open and visible")

	# ------------------------------------------------------------------
	# 3. Verify Dynamic 86% Viewport Sizing & Draw Order / Z-Index
	# ------------------------------------------------------------------
	var vp_size: Vector2 = menu._get_viewport_size()
	var expected_size: Vector2 = Vector2(vp_size.x * 0.86, vp_size.y * 0.86)
	var expected_pos: Vector2 = vp_size * 0.07

	_assert_cond(menu.dim_backdrop != null and menu.dim_backdrop.get_index() == 0, "Dim vignette backdrop is strictly at child index 0 (got %d)" % (menu.dim_backdrop.get_index() if menu.dim_backdrop != null else -1))
	_assert_cond(menu.main_codex_panel != null and menu.main_codex_panel.get_index() == 1, "MainCodexPanel is behind content at child index 1 (got %d)" % (menu.main_codex_panel.get_index() if menu.main_codex_panel != null else -1))
	_assert_cond(menu.main_codex_panel.material == null, "MainCodexPanel has no covering ShaderMaterial")
	_assert_cond(
		menu.main_codex_panel.size.distance_to(expected_size) < 2.0 and menu.main_codex_panel.position.distance_to(expected_pos) < 2.0,
		"MainCodexPanel is dynamically sized to 86%% of viewport (%s at %s)" % [str(menu.main_codex_panel.size), str(menu.main_codex_panel.position)]
	)

	_assert_cond(
		menu.tab1_container != null and menu.tab1_container.z_index == 2 and menu.tab2_container != null and menu.tab2_container.z_index == 2,
		"Tab1Container and Tab2Container are at z_index == 2 above background"
	)

	# ------------------------------------------------------------------
	# 4. Verify All Child Labels & Buttons Have modulate.a == 1.0 & Bright font_color (v > 0.75)
	# ------------------------------------------------------------------
	var labels: Array[Label] = []
	var buttons: Array[Button] = []
	_collect_controls(menu, labels, buttons)

	_assert_cond(labels.size() >= 30, "Menu contains %d structured Label nodes (>= 30)" % labels.size())
	_assert_cond(buttons.size() >= 30, "Menu contains %d interactive Button nodes (>= 30)" % buttons.size())

	var dark_or_faded_labels: int = 0
	for lbl: Label in labels:
		var fc: Color = lbl.get_theme_color("font_color")
		if not is_equal_approx(lbl.modulate.a, 1.0) or not is_equal_approx(lbl.self_modulate.a, 1.0) or fc.v <= 0.75:
			dark_or_faded_labels += 1
			push_error("Label '%s' failed brightness check: modulate.a=%.2f, font_color=%s (v=%.2f)" % [lbl.name, lbl.modulate.a, str(fc), fc.v])

	_assert_cond(dark_or_faded_labels == 0, "All %d child Labels have modulate.a == 1.0 and bright font_color (v > 0.75)" % labels.size())

	var dark_or_faded_buttons: int = 0
	for btn: Button in buttons:
		var bfc: Color = btn.get_theme_color("font_color")
		var dfc: Color = btn.get_theme_color("font_disabled_color")
		if not is_equal_approx(btn.modulate.a, 1.0) or not is_equal_approx(btn.self_modulate.a, 1.0) or bfc.v <= 0.75 or dfc.v <= 0.75:
			dark_or_faded_buttons += 1
			push_error("Button '%s' failed brightness check: modulate.a=%.2f, font_color=%s (v=%.2f), disabled=%s (v=%.2f)" % [btn.name, btn.modulate.a, str(bfc), bfc.v, str(dfc), dfc.v])

	_assert_cond(dark_or_faded_buttons == 0, "All %d child Buttons have modulate.a == 1.0 and bright font_color (v > 0.75)" % buttons.size())

	# ------------------------------------------------------------------
	# 5. Verify Tab I & Tab II Switching, Visibility, and Container Sizes (> 800 x 500)
	# ------------------------------------------------------------------
	menu.switch_tab(0)
	await process_frame
	_assert_cond(
		menu.tab1_container.visible and not menu.tab2_container.visible and menu.tab1_container.size.x > 800.0 and menu.tab1_container.size.y > 500.0,
		"Tab I (Sanctuary Armory) active: visible == true, size = %s (> 800x500)" % str(menu.tab1_container.size)
	)

	menu.switch_tab(1)
	await process_frame
	_assert_cond(
		menu.tab2_container.visible and not menu.tab1_container.visible and menu.tab2_container.size.x > 800.0 and menu.tab2_container.size.y > 500.0,
		"Tab II (Celestial Astrolabe) active: visible == true, size = %s (> 800x500)" % str(menu.tab2_container.size)
	)

	# ------------------------------------------------------------------
	# 6. Verify 3D SubViewport Pedestal Lighting & Station Interaction Deduplication
	# ------------------------------------------------------------------
	var world_env: WorldEnvironment = menu.sub_viewport.find_child("PedestalWorldEnv", true, false) as WorldEnvironment
	var key_light: OmniLight3D = menu.sub_viewport.find_child("AmberKeyLight", true, false) as OmniLight3D
	var rim_light: OmniLight3D = menu.sub_viewport.find_child("MoonlightCyanRimLight", true, false) as OmniLight3D
	_assert_cond(
		world_env != null and world_env.environment != null and world_env.environment.ambient_light_energy >= 1.8,
		"3D Pedestal WorldEnvironment has bright ambient_light_energy >= 1.8"
	)
	_assert_cond(
		key_light != null and key_light.light_energy >= 3.2 and key_light.omni_range >= 8.0 and rim_light != null and rim_light.light_energy >= 3.2 and rim_light.omni_range >= 8.0,
		"3D Pedestal has 2 strong OmniLight3D lights (light_energy = 3.2, omni_range = 8.0)"
	)

	var wb: SanctuaryForgeStation = level_inst.find_child("HubWeaponWorkbench", true, false) as SanctuaryForgeStation
	var lm: PlayerLoadoutManager = player.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	if wb != null and lm != null:
		wb.interact(lm)
		var menu_count: int = 0
		for ch: Node in hud.get_children():
			if ch is GothicCharacterMenu:
				menu_count += 1
		_assert_cond(menu_count == 1 and menu.is_menu_open and menu.active_tab == 0, "Station interaction opens single GothicCharacterMenu with zero duplicate overlays")

	level_inst.free()

	print("==================================================================")
	if _failures == 0:
		print("  ALL MENU VISIBILITY & 4K SCALING CHECKS PASSED (0 FAILURES)")
		print("==================================================================")
		quit(0)
	else:
		push_error("  VERIFICATION FAILED WITH %d ERRORS" % _failures)
		quit(1)
