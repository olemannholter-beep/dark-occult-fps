class_name OccultPortal
extends Node3D

@export var biome_id: int = 1
@export var biome_title: String = "The Endless Ossuary"
@export var portal_tint: Color = Color(1.0, 0.65, 0.28, 1.0)
@export var is_return_portal: bool = false
@export var return_destination: Vector3 = Vector3(0.0, 0.5, -26.0)
@export var depth_tier: int = 1

var _vortex_mesh: MeshInstance3D = null
var _vortex_material: ShaderMaterial = null
var _glow_light: OmniLight3D = null
var _trigger_area: Area3D = null
var _hum_audio: AudioStreamPlayer3D = null
var _warp_audio: AudioStreamPlayer = null
var _is_generating_rift: bool = false


func _ready() -> void:
	if scale.is_equal_approx(Vector3.ONE):
		scale = Vector3(0.76, 0.76, 0.76)
	_setup_vortex_shader()
	_setup_glow_light()
	_setup_audio()
	_setup_trigger_area()


func configure_portal(
	p_biome_id: int,
	p_title: String,
	p_tint: Color,
	p_is_return: bool,
	p_return_dest: Vector3,
	p_depth_tier: int = 1
) -> void:
	biome_id = p_biome_id
	biome_title = p_title
	portal_tint = p_tint
	is_return_portal = p_is_return
	return_destination = p_return_dest
	depth_tier = p_depth_tier
	if is_inside_tree():
		_setup_vortex_shader()
		_setup_glow_light()


func _setup_vortex_shader() -> void:
	_vortex_mesh = find_child("PortalVortexMesh", true, false) as MeshInstance3D
	if _vortex_mesh == null:
		_vortex_mesh = MeshInstance3D.new()
		_vortex_mesh.name = "PortalVortexMesh"
		var quad: QuadMesh = QuadMesh.new()
		quad.size = Vector2(2.2 * 0.76, 3.2 * 0.76)
		_vortex_mesh.mesh = quad
		_vortex_mesh.position = Vector3(0.0, 1.92 * 0.76, 0.0)
		add_child(_vortex_mesh)
	elif _vortex_mesh.mesh is QuadMesh:
		(_vortex_mesh.mesh as QuadMesh).size = Vector2(2.2 * 0.76, 3.2 * 0.76)
		_vortex_mesh.position = Vector3(0.0, 1.92 * 0.76, 0.0)
	_vortex_mesh.visibility_range_end = 0.0

	var shader: Shader = null
	if ResourceLoader.exists("res://shaders/portal_vortex.gdshader"):
		shader = load("res://shaders/portal_vortex.gdshader") as Shader

	_vortex_material = ShaderMaterial.new()
	if shader != null:
		_vortex_material.shader = shader
		var secondary_col: Color = Color(
			clampf(portal_tint.r * 0.28, 0.02, 1.0),
			clampf(portal_tint.g * 0.22, 0.02, 1.0),
			clampf(portal_tint.b * 0.34, 0.02, 1.0),
			1.0
		)
		_vortex_material.set_shader_parameter("portal_color_primary", portal_tint)
		_vortex_material.set_shader_parameter("portal_color_secondary", secondary_col)
		_vortex_material.set_shader_parameter("vortex_speed", 1.85)
	_vortex_mesh.material_override = _vortex_material
	_vortex_mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


func _setup_glow_light() -> void:
	_glow_light = find_child("PortalGlowLight", true, false) as OmniLight3D
	if _glow_light == null:
		_glow_light = OmniLight3D.new()
		_glow_light.name = "PortalGlowLight"
		_glow_light.position = Vector3(0.0, 2.0 * 0.76, 0.0)
		add_child(_glow_light)
	else:
		_glow_light.position = Vector3(0.0, 2.0 * 0.76, 0.0)

	_glow_light.light_color = portal_tint
	_glow_light.light_energy = 2.35
	_glow_light.omni_range = 10.5
	_glow_light.omni_attenuation = 1.35
	_glow_light.shadow_enabled = false
	_glow_light.distance_fade_enabled = true
	_glow_light.distance_fade_begin = 22.0
	_glow_light.distance_fade_length = 6.0


func _setup_audio() -> void:
	_hum_audio = find_child("PortalHumAudio3D", true, false) as AudioStreamPlayer3D
	if _hum_audio == null:
		_hum_audio = AudioStreamPlayer3D.new()
		_hum_audio.name = "PortalHumAudio3D"
		_hum_audio.position = Vector3(0.0, 1.8 * 0.76, 0.0)
		_hum_audio.unit_size = 4.5
		_hum_audio.max_distance = 18.0
		_hum_audio.volume_db = -5.0
		add_child(_hum_audio)

	if ResourceLoader.exists("res://assets/audio/sfx/portal_hum_loop.wav"):
		var hum_stream: AudioStream = load("res://assets/audio/sfx/portal_hum_loop.wav") as AudioStream
		if hum_stream is AudioStreamWAV:
			var wav: AudioStreamWAV = hum_stream as AudioStreamWAV
			wav.loop_mode = AudioStreamWAV.LOOP_FORWARD
			wav.loop_begin = 0
			wav.loop_end = int(wav.get_length() * float(wav.mix_rate))
		_hum_audio.stream = hum_stream
		if is_inside_tree() and not _hum_audio.playing:
			_hum_audio.play()

	_warp_audio = find_child("PortalWarpSFX", true, false) as AudioStreamPlayer
	if _warp_audio == null:
		_warp_audio = AudioStreamPlayer.new()
		_warp_audio.name = "PortalWarpSFX"
		_warp_audio.volume_db = -1.5
		add_child(_warp_audio)

	if ResourceLoader.exists("res://assets/audio/sfx/portal_warp_enter.wav"):
		_warp_audio.stream = load("res://assets/audio/sfx/portal_warp_enter.wav") as AudioStream


func _setup_trigger_area() -> void:
	_trigger_area = find_child("PortalTriggerArea", true, false) as Area3D
	if _trigger_area == null:
		_trigger_area = Area3D.new()
		_trigger_area.name = "PortalTriggerArea"
		_trigger_area.collision_layer = 1
		_trigger_area.collision_mask = 1
		_trigger_area.monitoring = true
		_trigger_area.monitorable = true
		add_child(_trigger_area)

		var col_shape: CollisionShape3D = CollisionShape3D.new()
		col_shape.name = "CollisionShape3D"
		var box: BoxShape3D = BoxShape3D.new()
		box.size = Vector3(2.1 * 0.76, 3.2 * 0.76, 0.75)
		col_shape.shape = box
		col_shape.position = Vector3(0.0, 1.85 * 0.76, 0.0)
		_trigger_area.add_child(col_shape)

	if not _trigger_area.body_entered.is_connected(_on_trigger_area_body_entered):
		_trigger_area.body_entered.connect(_on_trigger_area_body_entered)


func _on_trigger_area_body_entered(body: Node3D) -> void:
	if body == null:
		return
	if body is FPSController or body.name == "FPSPlayer":
		var now_ms: int = Time.get_ticks_msec()
		var last_ms: int = int(body.get_meta("last_portal_warp_msec", -99999))
		if now_ms - last_ms < 850:
			return
		trigger_portal_warp(body)


func get_prompt_text(_loadout: Node) -> String:
	if is_return_portal:
		return "[E] Return through Rift to Sanctuary Crypt\nRestores Safe-Zone Passage"
	var roman: String = _to_roman(depth_tier)
	return "[E] Enter Rift: %s (Procedural Tier %s)\nBiome %d Expedition — Walk in or Press [E]" % [
		biome_title,
		roman,
		biome_id
	]


func interact(loadout: Node) -> void:
	if loadout == null:
		return
	var player: Node3D = null
	if loadout is PlayerLoadoutManager:
		player = (loadout as PlayerLoadoutManager).player_controller
	if player == null and loadout.get_parent() is Node3D:
		player = loadout.get_parent() as Node3D
	if player != null:
		trigger_portal_warp(player)


func cycle_option(_loadout: Node) -> void:
	pass


func trigger_portal_warp(player: Node3D) -> void:
	if player == null or _is_generating_rift:
		return

	player.set_meta("last_portal_warp_msec", Time.get_ticks_msec())

	if _warp_audio != null and _warp_audio.stream != null and is_inside_tree():
		_warp_audio.play()

	var hud: FPSHUD = player.find_child("HUD", true, false) as FPSHUD
	if hud != null:
		hud.flash_portal_vignette(portal_tint)

	if is_return_portal:
		player.global_position = return_destination
		if player is CharacterBody3D:
			(player as CharacterBody3D).velocity = Vector3.ZERO
		return

	_is_generating_rift = true

	var overlay_layer: CanvasLayer = null
	var root_ctrl: Control = null
	if is_inside_tree() and get_tree() != null and get_tree().root != null:
		overlay_layer = CanvasLayer.new()
		overlay_layer.name = "RiftLoadingOverlayLayer"
		overlay_layer.layer = 120

		root_ctrl = Control.new()
		root_ctrl.name = "RiftLoadingOverlayRoot"
		root_ctrl.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		root_ctrl.mouse_filter = Control.MOUSE_FILTER_STOP
		overlay_layer.add_child(root_ctrl)

		var bg_rect: ColorRect = ColorRect.new()
		bg_rect.name = "Backdrop"
		bg_rect.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		bg_rect.color = Color(0.03, 0.03, 0.04, 0.96)
		bg_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
		root_ctrl.add_child(bg_rect)

		var panel: PanelContainer = PanelContainer.new()
		panel.name = "CenterPanel"
		panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
		panel.mouse_filter = Control.MOUSE_FILTER_IGNORE

		var panel_style: StyleBoxFlat = StyleBoxFlat.new()
		panel_style.bg_color = Color(0.05, 0.05, 0.06, 0.92)
		panel_style.border_color = Color(0.72, 0.58, 0.32, 1.0)
		panel_style.set_border_width_all(2)
		panel_style.set_corner_radius_all(4)
		panel_style.content_margin_left = 36.0
		panel_style.content_margin_right = 36.0
		panel_style.content_margin_top = 24.0
		panel_style.content_margin_bottom = 24.0
		panel.add_theme_stylebox_override("panel", panel_style)
		root_ctrl.add_child(panel)

		var vbox: VBoxContainer = VBoxContainer.new()
		vbox.name = "VBox"
		vbox.add_theme_constant_override("separation", 12)
		panel.add_child(vbox)

		var title_lbl: Label = Label.new()
		title_lbl.name = "TitleLabel"
		title_lbl.text = "DESCENDING INTO %s..." % biome_title.to_upper()
		title_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		title_lbl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		title_lbl.add_theme_font_size_override("font_size", 22)
		title_lbl.add_theme_color_override("font_color", Color(1.0, 0.88, 0.55, 1.0))
		vbox.add_child(title_lbl)

		var sub_lbl: Label = Label.new()
		sub_lbl.name = "SubtitleLabel"
		sub_lbl.text = "CARVING SUBTERRANEAN VOXEL SANCTUMS & SEALING OSSUARY VAULTS..."
		sub_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		sub_lbl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		sub_lbl.add_theme_font_size_override("font_size", 14)
		sub_lbl.add_theme_color_override("font_color", Color(0.78, 0.75, 0.70, 0.88))
		vbox.add_child(sub_lbl)

		get_tree().root.add_child(overlay_layer)

		if DisplayServer.get_name() != "headless":
			await get_tree().process_frame
			await get_tree().process_frame

	var target_biome: int = biome_id
	var target_tier: int = depth_tier
	var target_return: Vector3 = return_destination

	var gen: Node = _find_dungeon_generator()
	if gen != null and gen.has_method("generate_biome_dungeon"):
		var run_seed: int = int(Time.get_ticks_usec() ^ (randi() << 1))
		var spawn_pos: Variant = gen.call("generate_biome_dungeon", target_biome, run_seed, target_tier, target_return)
		if spawn_pos is Vector3:
			player.global_position = spawn_pos as Vector3
			if player is CharacterBody3D:
				(player as CharacterBody3D).velocity = Vector3.ZERO
		if target_biome == 1 and hud != null and gen is ProceduralDungeonGenerator:
			var p_gen: ProceduralDungeonGenerator = gen as ProceduralDungeonGenerator
			if not p_gen.last_mood_mutator_name.is_empty():
				var banner_text: String = "%s — %s" % [
					p_gen.last_mood_mutator_name.to_upper(),
					p_gen.last_vista_name
				]
				hud.show_rpg_banner(banner_text, p_gen.last_mood_mutator_color, 4.0)

	if is_instance_valid(self):
		_is_generating_rift = false

	if overlay_layer != null and is_instance_valid(overlay_layer):
		var tw: Tween = overlay_layer.create_tween()
		if tw != null and root_ctrl != null and is_instance_valid(root_ctrl):
			tw.tween_property(root_ctrl, "modulate:a", 0.0, 0.35)
			tw.finished.connect(func() -> void:
				if is_instance_valid(overlay_layer):
					overlay_layer.queue_free()
			)
		else:
			overlay_layer.queue_free()


func _find_dungeon_generator() -> Node:
	if not is_inside_tree():
		return null
	var root: Window = get_tree().root
	if root == null:
		return null
	var node: Node = root.find_child("ProceduralExpeditionRoot", true, false)
	return node


func _to_roman(num: int) -> String:
	var table: Array[String] = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
	if num >= 1 and num <= table.size():
		return table[num - 1]
	return str(num)
