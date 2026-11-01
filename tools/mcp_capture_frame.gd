extends SceneTree

var _frame_count: int = 0
var _target_frames: int = 45
var _view_mode: String = "overview"
var _level_instance: Node3D = null
var _capture_cam: Camera3D = null


func _init() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	for arg: String in args:
		if arg.begins_with("--view="):
			_view_mode = arg.trim_prefix("--view=")
		elif arg.begins_with("--frames="):
			_target_frames = int(arg.trim_prefix("--frames="))

	DirAccess.make_dir_recursive_absolute("res://.mcp_captures")

	var main_scene: PackedScene = load("res://scenes/levels/town_overworld.tscn") as PackedScene
	if main_scene == null:
		push_error("Failed to load res://scenes/levels/town_overworld.tscn")
		quit(1)
		return

	_level_instance = main_scene.instantiate() as Node3D
	root.add_child(_level_instance)

	if (
		_view_mode == "fps_viewmodel"
		or _view_mode == "fps_shotgun"
		or _view_mode == "fps_stakedriver"
		or _view_mode == "hub_workbench"
		or _view_mode == "hub_armor_stand"
		or _view_mode == "menu_tab1"
		or _view_mode == "menu_field"
		or _view_mode == "menu_set1"
		or _view_mode == "menu_set2"
		or _view_mode == "menu_set3"
		or _view_mode == "menu_tab2"
	):

		var player: Node3D = _level_instance.get_node_or_null("Player") as Node3D
		if player != null:
			var p_cam: Camera3D = player.get_node_or_null("Head/Camera3D") as Camera3D
			var head: Node3D = player.get_node_or_null("Head") as Node3D
			var loadout: PlayerLoadoutManager = player.get_node_or_null("PlayerLoadoutManager") as PlayerLoadoutManager
			var vm: FPSViewmodelController = player.find_child("ViewmodelRig", true, false) as FPSViewmodelController
			var hud_o: GothicHudOverhaul = player.find_child("HUD", true, false) as GothicHudOverhaul
			if _view_mode == "fps_viewmodel":
				player.position = Vector3(0.0, 4.05, -14.0)
			elif _view_mode == "fps_shotgun":
				player.position = Vector3(0.0, 4.05, -14.0)
				if loadout != null:
					loadout.equip_weapon("shotgun")
					loadout.cycle_weapon_mod(2)
				if vm != null:
					vm.recoil_offset_rot = Vector3.ZERO
					vm.recoil_offset_pos = Vector3.ZERO
					vm._apply_hand_transforms()
			elif _view_mode == "fps_stakedriver":
				player.position = Vector3(0.0, 4.05, -14.0)
				if loadout != null:
					loadout.equip_weapon("stakedriver")
					loadout.cycle_weapon_mod(1)
				if vm != null:
					vm.recoil_offset_rot = Vector3.ZERO
					vm.recoil_offset_pos = Vector3.ZERO
					vm._apply_hand_transforms()
			elif _view_mode == "hub_workbench":
				player.position = Vector3(-7.6, 4.05, -36.0)
				player.rotation = Vector3(0.0, deg_to_rad(90.0), 0.0)
				if head != null:
					head.rotation = Vector3(deg_to_rad(-8.0), 0.0, 0.0)
				if loadout != null:
					loadout.cycle_weapon_mod(1)
			elif _view_mode == "hub_armor_stand":
				player.position = Vector3(7.6, 4.05, -36.0)
				player.rotation = Vector3(0.0, deg_to_rad(-90.0), 0.0)
				if head != null:
					head.rotation = Vector3(deg_to_rad(-8.0), 0.0, 0.0)
				if loadout != null:
					loadout.cycle_armor_tier(2)
					loadout.cycle_weapon_mod(2)
			elif _view_mode in ["menu_tab1", "menu_field", "menu_set1", "menu_set2", "menu_set3"]:
				player.position = Vector3(0.0, 4.05, -14.0)
				if hud_o != null and hud_o.character_menu != null:
					hud_o.character_menu.set_menu_open(true)
					hud_o.character_menu.switch_tab(0)

			elif _view_mode == "menu_tab2":
				player.position = Vector3(0.0, 4.05, -14.0)
				if hud_o != null and hud_o.character_menu != null:
					hud_o.character_menu.set_menu_open(true)
					hud_o.character_menu.switch_tab(1)
					hud_o.character_menu.select_skill_node("blood_1", true)
			if p_cam != null:
				_capture_cam = p_cam
				_capture_cam.make_current()
				return

	_capture_cam = Camera3D.new()
	_capture_cam.name = "MCPCaptureCamera3D"
	_capture_cam.fov = 70.0
	_level_instance.add_child(_capture_cam)
	_apply_camera_preset(_view_mode)
	_capture_cam.make_current()
	var player_node: Node3D = _level_instance.get_node_or_null("Player") as Node3D
	if player_node != null:
		var hud_node: CanvasLayer = player_node.find_child("HUD", true, false) as CanvasLayer
		if hud_node != null:
			hud_node.visible = false
		player_node.position = _capture_cam.position + _capture_cam.transform.basis.z * 2.5
	var zone_mgr: ZonePerformanceManager = _level_instance.find_child("ZonePerformanceManager", true, false) as ZonePerformanceManager
	if zone_mgr != null:
		zone_mgr.evaluate_zones_now(_capture_cam.position)


func _apply_camera_preset(preset: String) -> void:
	if _capture_cam == null:
		return
	match preset:
		"overview":
			_capture_cam.look_at_from_position(Vector3(0.0, 14.5, 34.0), Vector3(0.0, 3.5, -14.0), Vector3.UP)
		"church", "church_exterior":
			_capture_cam.look_at_from_position(Vector3(5.5, 6.2, -3.5), Vector3(0.0, 5.5, -14.0), Vector3.UP)
		"church_interior":
			var hud_node: CanvasLayer = _level_instance.find_child("HUD", true, false) as CanvasLayer
			if hud_node != null:
				hud_node.visible = false
			_capture_cam.look_at_from_position(Vector3(0.0, 5.8, -11.9), Vector3(0.0, 4.9, -18.5), Vector3.UP)
		"crypt", "crypt_basement":
			_capture_cam.look_at_from_position(Vector3(0.0, 2.1, -52.2), Vector3(0.0, 1.3, -59.5), Vector3.UP)
		"chamber_ossuary_hub":
			_capture_cam.look_at_from_position(Vector3(0.0, 2.0, -23.5), Vector3(0.0, 1.4, -33.5), Vector3.UP)
		"chamber_sarcophagi":
			_capture_cam.look_at_from_position(Vector3(-11.2, 2.1, -30.0), Vector3(-22.0, 1.2, -30.0), Vector3.UP)
		"chamber_library":
			_capture_cam.look_at_from_position(Vector3(-16.0, 1.9, -46.8), Vector3(-16.0, 1.35, -55.0), Vector3.UP)
		"chamber_gaol":
			_capture_cam.look_at_from_position(Vector3(11.2, 1.9, -28.0), Vector3(22.0, 1.5, -28.0), Vector3.UP)
		"chamber_plague_cistern":
			_capture_cam.look_at_from_position(Vector3(18.0, -1.8, -39.5), Vector3(18.0, -2.8, -46.5), Vector3.UP)
		"chamber_weeping_saint":
			_capture_cam.look_at_from_position(Vector3(0.0, -1.8, -39.5), Vector3(0.0, -2.1, -47.0), Vector3.UP)
		"chamber_sunken_bell":
			_capture_cam.look_at_from_position(Vector3(-18.0, -5.2, -63.2), Vector3(-18.0, -6.8, -70.2), Vector3.UP)
		"boss", "chamber_abyssal_sanctum":
			_capture_cam.look_at_from_position(Vector3(0.0, -6.5, -98.0), Vector3(0.0, -7.5, -108.0), Vector3.UP)
		"stairs_church_to_crypt":
			_capture_cam.look_at_from_position(Vector3(0.0, 5.8, -46.5), Vector3(0.0, 1.0, -53.5), Vector3.UP)
			var s_light: OmniLight3D = OmniLight3D.new()
			s_light.light_color = Color(1.0, 0.85, 0.65)
			s_light.light_energy = 3.0
			s_light.omni_range = 18.0
			_capture_cam.add_child(s_light)
		"stairs_ch1_to_ch6":
			_capture_cam.look_at_from_position(Vector3(0.0, 1.85, -60.5), Vector3(0.0, -2.5, -68.0), Vector3.UP)
		"stairs_ch4_to_ch5":
			_capture_cam.look_at_from_position(Vector3(24.0, 1.85, -60.5), Vector3(24.0, -2.5, -68.0), Vector3.UP)
		"stairs_ch6_to_ch7":
			_capture_cam.look_at_from_position(Vector3(-12.0, -2.15, -84.5), Vector3(-12.0, -6.5, -92.0), Vector3.UP)
		"stairs_ch6_to_ch8":
			_capture_cam.look_at_from_position(Vector3(0.0, -2.15, -80.5), Vector3(0.0, -6.5, -88.0), Vector3.UP)
		"stairs_dungeon":
			var d_gen: ProceduralDungeonGenerator = _level_instance.find_child("ProceduralDungeonGenerator", true, false) as ProceduralDungeonGenerator
			if d_gen == null:
				d_gen = ProceduralDungeonGenerator.new()
				d_gen.name = "ProceduralDungeonGenerator"
				_level_instance.add_child(d_gen)
			d_gen.generate_v2_vertical_dungeon(0, 1, 101)
			if not d_gen._spawned_stair_world_positions.is_empty():
				var sp: Vector3 = d_gen._spawned_stair_world_positions[0]
				_capture_cam.look_at_from_position(sp + Vector3(4.0, -1.6, 5.8), sp + Vector3(2.0, -2.2, 0.0), Vector3.UP)
				var cam_light: OmniLight3D = OmniLight3D.new()
				cam_light.light_color = Color(1.0, 0.85, 0.65)
				cam_light.light_energy = 3.5
				cam_light.omni_range = 22.0
				_capture_cam.add_child(cam_light)
		"sky_and_foliage":
			_capture_cam.look_at_from_position(Vector3(0.0, 2.4, 20.0), Vector3(0.0, 8.5, -18.0), Vector3.UP)
		_:
			_capture_cam.look_at_from_position(Vector3(0.0, 14.5, 34.0), Vector3(0.0, 3.5, -14.0), Vector3.UP)


func _process(_delta: float) -> bool:
	_frame_count += 1
	if _frame_count == 2 and _level_instance != null:
		var player: Node3D = _level_instance.get_node_or_null("Player") as Node3D
		if player != null:
			var hud_o: GothicHudOverhaul = player.find_child("HUD", true, false) as GothicHudOverhaul
			var loadout: PlayerLoadoutManager = player.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
			if _view_mode == "menu_tab1" and hud_o != null and hud_o.character_menu != null:
				if loadout != null:
					loadout.reset_for_new_run()
					loadout.grant_test_materials()
					loadout.craft_unlock_armor_piece("CHEST", 1)
					loadout.equip_armor_slot("CHEST", 1)
					loadout.craft_unlock_armor_piece("HEAD", 1)
					loadout.equip_armor_slot("HEAD", 1)
				hud_o.character_menu.open_at_forge_station("armor")
			elif _view_mode in ["menu_field", "menu_set1", "menu_set2", "menu_set3"] and hud_o != null and hud_o.character_menu != null:
				var target_set: int = 0
				if _view_mode == "menu_set1":
					target_set = 1
				elif _view_mode == "menu_set2":
					target_set = 2
				elif _view_mode == "menu_set3":
					target_set = 3
				if loadout != null:
					loadout.reset_for_new_run()
					for g_i: int in range(8):
						loadout.grant_test_materials()
					for u_set: int in [1, 2, 3]:
						for s_u: String in ["HEAD", "CHEST", "HANDS", "LEGS", "FEET"]:
							loadout.craft_unlock_armor_piece(s_u, u_set)
					for s_k: String in ["HEAD", "CHEST", "HANDS", "LEGS", "FEET"]:
						loadout.equip_armor_slot(s_k, target_set)
				hud_o.character_menu.open_field_character_menu()
				if hud_o.character_menu.paperdoll_rig != null:
					hud_o.character_menu.paperdoll_rig.rotation_degrees.y = -16.0
				if hud_o.character_menu._floating_tooltip != null:
					hud_o.character_menu._floating_tooltip.visible = false

			elif _view_mode == "fps_viewmodel" and loadout != null:
				loadout.reset_for_new_run()
				loadout.grant_test_materials()
				loadout.craft_unlock_armor_piece("HANDS", 2)
				loadout.equip_armor_slot("HANDS", 2)
			elif _view_mode == "menu_tab2" and hud_o != null and hud_o.character_menu != null:
				hud_o.character_menu.set_menu_open(true)
				hud_o.character_menu.switch_tab(1)
				hud_o.character_menu.select_skill_node("blood_1", true)
	if _frame_count < _target_frames:
		return false

	var physics_report: Dictionary[String, Variant] = _run_physics_verification()
	_save_screenshot_and_telemetry(_view_mode, physics_report)
	quit(0)
	return true


func _run_physics_verification() -> Dictionary[String, Variant]:
	var space_state: PhysicsDirectSpaceState3D = root.world_3d.direct_space_state
	var report: Dictionary[String, Variant] = {}

	# 1. Verify terrain cutout is open at Church-to-Crypt stairwell (X=0, Z=-50) from Y=5.2 down to Y=0.5
	var stair_ray: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		Vector3(0.0, 5.2, -50.0),
		Vector3(0.0, 0.5, -50.0)
	)
	var stair_hit: Dictionary = space_state.intersect_ray(stair_ray)
	var stair_hit_pos: Vector3 = stair_hit.get("position", Vector3.ZERO) as Vector3
	var stair_hit_name: String = ""
	if stair_hit.has("collider") and stair_hit["collider"] != null:
		var col_node: Node = stair_hit["collider"] as Node
		if col_node != null and col_node.get_parent() != null:
			stair_hit_name = col_node.get_parent().name
	report["stairwell_ray_hit_node"] = stair_hit_name
	report["stairwell_ray_hit_y"] = stair_hit_pos.y

	# 2. Verify open doorway passage into Church at Y=5.0, X=0, from Z=-10.5 to Z=-13.5
	var church_door_ray: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		Vector3(0.0, 5.2, -10.5),
		Vector3(0.0, 5.2, -13.5)
	)
	var church_door_hit: Dictionary = space_state.intersect_ray(church_door_ray)
	report["church_doorway_clear"] = church_door_hit.is_empty()

	# 3. Verify open archway passage from bottom of stairs (Z=-52.0) into Crypt Basement (Z=-55.0) at Y=1.2
	var crypt_door_ray: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		Vector3(0.0, 1.2, -52.0),
		Vector3(0.0, 1.2, -55.0)
	)
	var crypt_door_hit: Dictionary = space_state.intersect_ray(crypt_door_ray)
	report["crypt_archway_clear"] = crypt_door_hit.is_empty()

	# 4. Verify Crypt Basement floor support at Chamber 1 (0, -56.0)
	var crypt_floor_ray: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		Vector3(0.0, 2.0, -56.0),
		Vector3(0.0, -1.0, -56.0)
	)
	var crypt_floor_hit: Dictionary = space_state.intersect_ray(crypt_floor_ray)
	var crypt_floor_y: float = -999.0
	if not crypt_floor_hit.is_empty():
		crypt_floor_y = (crypt_floor_hit["position"] as Vector3).y
	report["crypt_floor_y"] = crypt_floor_y

	return report


func _save_screenshot_and_telemetry(view_name: String, physics_report: Dictionary[String, Variant]) -> void:
	if DisplayServer.get_name() != "headless":
		var tex: ViewportTexture = root.get_texture()
		if tex != null:
			var img: Image = tex.get_image()
			if img != null:
				var view_path: String = "res://.mcp_captures/capture_" + view_name + ".png"
				img.save_png(view_path)
				img.save_png("res://.mcp_captures/latest_frame.png")
				print("[Capture] Saved screenshot: " + view_path)

	var state: Dictionary[String, Variant] = {
		"view_mode": view_name,
		"frames_rendered": _frame_count,
		"camera_position": [
			_capture_cam.global_position.x if _capture_cam != null else 0.0,
			_capture_cam.global_position.y if _capture_cam != null else 0.0,
			_capture_cam.global_position.z if _capture_cam != null else 0.0,
		],
		"physics_verification": physics_report,
	}
	var file: FileAccess = FileAccess.open("res://.mcp_captures/scene_state.json", FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify(state, "\t"))
		file.close()
	print("[Capture] Telemetry: " + JSON.stringify(state))
