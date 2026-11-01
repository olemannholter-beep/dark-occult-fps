class_name GothicHudOverhaul
extends CanvasLayer

@export var viewmodel_controller: FPSViewmodelController

var map_system: GothicMapSystem = null
var character_menu: GothicCharacterMenu = null
var _canvas_drawer: Control = null

# Exposed state for verification & smooth HUD animations
var cur_hp_val: int = 100
var max_hp_val: int = 100
var trail_hp_ratio: float = 1.0
var cur_hp_ratio: float = 1.0
var _ghost_hold_timer: float = 0.0

var cur_armor_val: int = 25
var max_armor_val: int = 25
var armor_title_str: String = "Grave-Stalker's Boiled Leather"

var hunter_level_val: int = 1
var cur_xp_val: int = 0
var next_xp_val: int = 100
var essence_val: int = 300
var silver_val: int = 35
var bone_ash_val: int = 15
var cursed_iron_val: int = 0
var soul_cores_val: int = 0
var blessing_lvl_val: int = 1
var unspent_points_val: int = 0

var bloodlust_rank_val: int = 1
var quicksilver_rank_val: int = 1
var ironclad_rank_val: int = 1
var eldritch_rank_val: int = 1

var active_weapon_id_str: String = "revolver"
var active_weapon_title_str: String = "Occult Revolver"
var weapon_mod_str: String = "Blood-Iron Rounds"
var weapon_dmg_val: float = 38.0
var current_ammo_val: int = 6
var max_ammo_val: int = 6

var active_spell_name_str: String = "Soul-Pyre Blast"
var spell_cooldown_rem: float = 0.0
var spell_cooldown_max: float = 6.0
var active_relic_list: Array[String] = []

var biome_header_title: String = "SANCTUARY OF THE ASHEN CHAPEL"
var biome_header_subtitle: String = "SAFE HARBOUR HUB"
var biome_header_fade_timer: float = 4.0
var biome_header_alpha: float = 0.92

var spread_offset: float = 0.0
var reticle_spread_px: float = 0.0
var reticle_spread_vel: float = 0.0
var reticle_rotation_rad: float = 0.0
var reticle_rot_vel: float = 0.0

var hitmarker_timer: float = 0.0
var hitmarker_duration: float = 0.22
var hitmarker_is_crit: bool = false
var hitmarker_scale: float = 1.0
var hitmarker_rotation: float = 0.0
var hitmarker_color: Color = Color(1.0, 0.92, 0.72, 1.0)

# Preserved Control nodes for backwards compatibility with existing scripts/tests
var _ammo_label: Label = null
var _spell_relic_label: Label = null
var _reticle: Control = null
var _status_panel: PanelContainer = null
var _status_label: Label = null
var _loadout_sub_label: Label = null
var _attribute_prompt_label: Label = null
var _prompt_panel: PanelContainer = null
var _prompt_label: Label = null
var _banner_panel: PanelContainer = null
var _banner_label: Label = null
var _banner_timer: float = 0.0
var _portal_vignette: ColorRect = null
var _vignette_alpha: float = 0.0
var _vignette_color: Color = Color(1.0, 0.65, 0.28, 0.0)


func _on_canvas_drawer_draw() -> void:
	if _canvas_drawer != null and is_instance_valid(_canvas_drawer):
		_draw_gothic_hud(_canvas_drawer)


func _init() -> void:
	layer = 10
	_build_hud_elements()


func _ready() -> void:
	layer = 10
	if is_inside_tree() and get_tree() != null and get_tree().root != null:
		var root_win: Window = get_tree().root
		root_win.content_scale_size = Vector2i(1920, 1080)
		root_win.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
		root_win.content_scale_aspect = Window.CONTENT_SCALE_ASPECT_EXPAND
		root_win.content_scale_stretch = Window.CONTENT_SCALE_STRETCH_FRACTIONAL

	# Clean up any duplicate/serialized children under HUD from older .tscn files
	for child: Node in get_children():
		if child != _canvas_drawer and child != map_system and child != _prompt_panel and child != _banner_panel and child != _portal_vignette and child != character_menu and child.name != "LegacyLabelMirror":
			remove_child(child)
			child.queue_free()
	_build_hud_elements()
	if character_menu != null and is_instance_valid(character_menu):
		move_child(character_menu, get_child_count() - 1)
	if _canvas_drawer != null and is_instance_valid(_canvas_drawer):
		if not _canvas_drawer.draw.is_connected(_on_canvas_drawer_draw):
			_canvas_drawer.draw.connect(_on_canvas_drawer_draw)
		_canvas_drawer.queue_redraw()

	if viewmodel_controller == null and get_parent() != null:
		viewmodel_controller = get_parent().find_child("ViewmodelRig", true, false) as FPSViewmodelController

	if viewmodel_controller != null:
		if not viewmodel_controller.ammo_changed.is_connected(_on_ammo_changed):
			viewmodel_controller.ammo_changed.connect(_on_ammo_changed)
		_on_ammo_changed(viewmodel_controller.current_ammo, viewmodel_controller.max_ammo)
	else:
		_on_ammo_changed(6, 6)


func _process(delta: float) -> void:
	# 1. Delayed Damage Ghost Bar (trail_hp_ratio smoothly decays over 0.45s behind cur_hp_ratio)
	cur_hp_ratio = clampf(float(cur_hp_val) / float(maxi(1, max_hp_val)), 0.0, 1.0)
	if trail_hp_ratio > cur_hp_ratio:
		if _ghost_hold_timer > 0.0:
			_ghost_hold_timer = maxf(0.0, _ghost_hold_timer - delta)
		else:
			trail_hp_ratio = move_toward(trail_hp_ratio, cur_hp_ratio, delta / 0.45)
	else:
		trail_hp_ratio = cur_hp_ratio

	# 2. Spring-Animated Dynamic Crosshair & Animated Expanding/Rotating Hitmarker
	var move_spread_target: float = 0.0
	if viewmodel_controller != null and viewmodel_controller._player != null:
		var p_node: CharacterBody3D = viewmodel_controller._player
		var horiz_spd: float = Vector2(p_node.velocity.x, p_node.velocity.z).length()
		move_spread_target += horiz_spd * 0.8
		if p_node is FPSController and (p_node as FPSController).is_dashing:
			move_spread_target += 16.0
		if not p_node.is_on_floor():
			move_spread_target += 10.0

	var dt_spring: float = minf(delta, 0.033)
	var spread_force: float = (move_spread_target - reticle_spread_px) * 145.0 - reticle_spread_vel * 16.5
	reticle_spread_vel += spread_force * dt_spring
	reticle_spread_px = maxf(0.0, reticle_spread_px + reticle_spread_vel * dt_spring)
	spread_offset = reticle_spread_px

	var rot_force: float = (-reticle_rotation_rad) * 160.0 - reticle_rot_vel * 17.0
	reticle_rot_vel += rot_force * dt_spring
	reticle_rotation_rad += reticle_rot_vel * dt_spring

	if hitmarker_timer > 0.0:
		hitmarker_timer = maxf(0.0, hitmarker_timer - delta)
		var elapsed: float = hitmarker_duration - hitmarker_timer
		var snap_t: float = clampf(elapsed / 0.09, 0.0, 1.0)
		var eased_snap: float = 1.0 - pow(1.0 - snap_t, 3.0)
		var start_scale: float = 2.1 if hitmarker_is_crit else 1.65
		hitmarker_scale = lerpf(start_scale, 1.0, eased_snap)
		hitmarker_rotation = lerpf(deg_to_rad(12.0), 0.0, eased_snap)

	# 3. Top-Center Biome Header gentle fade to 35% opacity after 4.0s
	if biome_header_fade_timer > 0.0:
		biome_header_fade_timer = maxf(0.0, biome_header_fade_timer - delta)
		biome_header_alpha = 0.95
	else:
		biome_header_alpha = move_toward(biome_header_alpha, 0.35, delta * 0.45)

	_update_biome_header_from_world()

	# 4. Portal Vignette & RPG Banner timers
	if _vignette_alpha > 0.001 and _portal_vignette != null:
		_vignette_alpha = maxf(0.0, _vignette_alpha - delta * 1.45)
		_portal_vignette.color = Color(
			_vignette_color.r,
			_vignette_color.g,
			_vignette_color.b,
			_vignette_alpha
		)
		_portal_vignette.visible = _vignette_alpha > 0.005
	elif _portal_vignette != null and _portal_vignette.visible:
		_portal_vignette.visible = false

	if _banner_timer > 0.0 and _banner_panel != null:
		_banner_timer = maxf(0.0, _banner_timer - delta)
		_banner_panel.visible = _banner_timer > 0.0

	if _canvas_drawer != null:
		_canvas_drawer.queue_redraw()


func _update_biome_header_from_world() -> void:
	if map_system == null:
		return
	var p: Node3D = map_system._player
	if p == null or not is_instance_valid(p):
		return
	var pos: Vector3 = p.global_position if p.is_inside_tree() else p.position
	var new_title: String = biome_header_title
	var new_sub: String = biome_header_subtitle

	if pos.y <= -100.0 and map_system._dungeon_gen != null:
		var gen: ProceduralDungeonGenerator = map_system._dungeon_gen
		var prof: Dictionary = gen.get_biome_profile(gen.active_biome_id)
		new_title = String(prof.get("title", "THE ENDLESS OSSUARY")).to_upper()
		if not gen.last_mood_mutator_name.is_empty():
			new_sub = gen.last_mood_mutator_name.to_upper()
		else:
			new_sub = "DEPTH TIER %d EXPEDITION" % gen.active_depth_tier
	elif pos.z <= -21.0:
		new_title = "SUBTERRANEAN CATACOMB SANCTUMS"
		new_sub = "EIGHT PORTAL CHAMBERS (SAFE HARBOUR)"
	elif pos.z <= 8.5 and absf(pos.x) <= 7.0:
		new_title = "CHAPEL NAVE WORKSHOP"
		new_sub = "CONSECRATED HUNTER SANCTUARY"
	else:
		new_title = "ASHEN VALLEY OVERWORLD"
		new_sub = "THE FORSAKEN TOWN ROAD"

	if new_title != biome_header_title or new_sub != biome_header_subtitle:
		biome_header_title = new_title
		biome_header_subtitle = new_sub
		biome_header_fade_timer = 4.0
		biome_header_alpha = 0.95


func trigger_hitmarker(is_kill_or_headshot: bool = false) -> void:
	hitmarker_duration = 0.22
	hitmarker_timer = 0.22
	hitmarker_is_crit = is_kill_or_headshot
	hitmarker_scale = 2.1 if is_kill_or_headshot else 1.65
	hitmarker_rotation = deg_to_rad(12.0)
	hitmarker_color = (
		Color(1.0, 0.18, 0.15, 1.0)
		if is_kill_or_headshot
		else Color(1.0, 0.92, 0.72, 1.0)
	)
	reticle_spread_px = clampf(reticle_spread_px + (8.0 if is_kill_or_headshot else 5.0), 0.0, 64.0)
	spread_offset = reticle_spread_px
	if _canvas_drawer != null:
		_canvas_drawer.queue_redraw()


func add_reticle_spread(amount: float = 24.0) -> void:
	reticle_spread_px = clampf(reticle_spread_px + amount, 0.0, 64.0)
	reticle_spread_vel += amount * 4.5
	reticle_rotation_rad += deg_to_rad(15.0)
	reticle_rot_vel += deg_to_rad(65.0)
	spread_offset = reticle_spread_px
	if _canvas_drawer != null:
		_canvas_drawer.queue_redraw()


func flash_portal_vignette(tint: Color) -> void:
	_vignette_color = tint
	_vignette_alpha = 0.58
	if _portal_vignette != null:
		_portal_vignette.color = Color(tint.r, tint.g, tint.b, _vignette_alpha)
		_portal_vignette.visible = true


func show_rpg_banner(banner_text: String, tint: Color = Color(1.0, 0.84, 0.32, 1.0), duration: float = 3.2) -> void:
	if _banner_panel == null or _banner_label == null:
		return
	_banner_label.text = banner_text
	_banner_label.add_theme_color_override("font_color", tint)
	_banner_panel.visible = true
	_banner_timer = duration
	biome_header_fade_timer = 4.0


func _build_hud_elements() -> void:
	if _canvas_drawer != null and is_instance_valid(_canvas_drawer):
		if not _canvas_drawer.draw.is_connected(_on_canvas_drawer_draw):
			_canvas_drawer.draw.connect(_on_canvas_drawer_draw)
		return
	# 1. Custom Procedural Gothic HUD Canvas Drawer (Vitality Crest, Arsenal Panel, Biome Plaque, Occult Reticle)
	var drawer: Control = Control.new()
	drawer.name = "GothicHudCanvasDrawer"
	drawer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	drawer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	drawer.draw.connect(_on_canvas_drawer_draw)
	add_child(drawer)
	_canvas_drawer = drawer
	_reticle = drawer

	# 2. Fog-of-War Corner Astrolabe Minimap & Full-Screen Cartographer's Map Overlay
	map_system = GothicMapSystem.new()
	map_system.name = "GothicMapSystem"
	add_child(map_system)

	# 3. Hidden Backing Labels for 100% Backwards Compatibility with Existing Tests/Scripts
	var compat_holder: Control = Control.new()
	compat_holder.name = "LegacyLabelMirror"
	compat_holder.visible = false
	compat_holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(compat_holder)

	_ammo_label = Label.new()
	_ammo_label.name = "AmmoLabel"
	compat_holder.add_child(_ammo_label)

	_spell_relic_label = Label.new()
	_spell_relic_label.name = "SpellAndRelicLabel"
	compat_holder.add_child(_spell_relic_label)

	_status_panel = PanelContainer.new()
	_status_panel.name = "StatusPanel"
	compat_holder.add_child(_status_panel)

	_status_label = Label.new()
	_status_label.name = "StatusLabel"
	_status_panel.add_child(_status_label)

	_loadout_sub_label = Label.new()
	_loadout_sub_label.name = "LoadoutSubLabel"
	_status_panel.add_child(_loadout_sub_label)

	_attribute_prompt_label = Label.new()
	_attribute_prompt_label.name = "AttributePromptLabel"
	_status_panel.add_child(_attribute_prompt_label)

	# 4. Center-Screen Contextual Interaction Prompt
	_prompt_panel = PanelContainer.new()
	_prompt_panel.name = "InteractionPromptPanel"
	_prompt_panel.anchor_left = 0.5
	_prompt_panel.anchor_right = 0.5
	_prompt_panel.anchor_top = 0.5
	_prompt_panel.anchor_bottom = 0.5
	_prompt_panel.offset_left = -280.0
	_prompt_panel.offset_top = 42.0
	_prompt_panel.offset_right = 280.0
	_prompt_panel.offset_bottom = 128.0
	_prompt_panel.visible = false
	_prompt_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE

	var prompt_style: StyleBoxFlat = StyleBoxFlat.new()
	prompt_style.bg_color = Color(0.04, 0.025, 0.04, 0.90)
	prompt_style.border_color = Color(0.84, 0.66, 0.30, 0.94)
	prompt_style.set_border_width_all(2)
	prompt_style.set_corner_radius_all(3)
	prompt_style.content_margin_left = 18.0
	prompt_style.content_margin_right = 18.0
	prompt_style.content_margin_top = 10.0
	prompt_style.content_margin_bottom = 10.0
	_prompt_panel.add_theme_stylebox_override("panel", prompt_style)
	add_child(_prompt_panel)

	_prompt_label = Label.new()
	_prompt_label.name = "InteractionPromptLabel"
	_prompt_label.text = ""
	_prompt_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_prompt_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_prompt_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_prompt_label.add_theme_font_size_override("font_size", 18)
	_prompt_label.add_theme_color_override("font_color", Color(1.0, 0.92, 0.70, 1.0))
	_prompt_label.add_theme_color_override("font_shadow_color", Color(0.06, 0.02, 0.03, 0.95))
	_prompt_label.add_theme_constant_override("shadow_offset_x", 1)
	_prompt_label.add_theme_constant_override("shadow_offset_y", 1)
	_prompt_panel.add_child(_prompt_label)

	# 5. Top-Center RPG Level-Up & Relic Banner
	_banner_panel = PanelContainer.new()
	_banner_panel.name = "RPGBannerPanel"
	_banner_panel.anchor_left = 0.5
	_banner_panel.anchor_right = 0.5
	_banner_panel.anchor_top = 0.0
	_banner_panel.anchor_bottom = 0.0
	_banner_panel.offset_left = -420.0
	_banner_panel.offset_top = 64.0
	_banner_panel.offset_right = 420.0
	_banner_panel.offset_bottom = 126.0
	_banner_panel.visible = false
	_banner_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE

	var banner_style: StyleBoxFlat = StyleBoxFlat.new()
	banner_style.bg_color = Color(0.07, 0.05, 0.08, 0.96)
	banner_style.border_color = Color(1.0, 0.82, 0.36, 1.0)
	banner_style.set_border_width_all(2)
	banner_style.set_corner_radius_all(3)
	banner_style.content_margin_left = 18.0
	banner_style.content_margin_right = 18.0
	banner_style.content_margin_top = 10.0
	banner_style.content_margin_bottom = 10.0
	_banner_panel.add_theme_stylebox_override("panel", banner_style)
	add_child(_banner_panel)

	_banner_label = Label.new()
	_banner_label.name = "RPGBannerLabel"
	_banner_label.text = ""
	_banner_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_banner_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_banner_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_banner_label.add_theme_font_size_override("font_size", 19)
	_banner_label.add_theme_color_override("font_color", Color(1.0, 0.88, 0.50, 1.0))
	_banner_panel.add_child(_banner_label)

	# 6. Dimensional Rift Screen Flash Vignette Overlay
	_portal_vignette = ColorRect.new()
	_portal_vignette.name = "PortalFlashVignette"
	_portal_vignette.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_portal_vignette.color = Color(1.0, 0.65, 0.28, 0.0)
	_portal_vignette.visible = false
	_portal_vignette.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_portal_vignette)

	# 7. Masterwork Gothic Character Menu & 20-Node Celestial Astrolabe Skill Tree ([C] / [K] / [I])
	character_menu = GothicCharacterMenu.new()
	character_menu.name = "GothicCharacterMenu"
	add_child(character_menu)


func _draw_gothic_hud(c: Control) -> void:
	var vp: Vector2 = c.get_viewport_rect().size
	if vp.x < 100.0 or vp.y < 100.0:
		vp = Vector2(1920.0, 1080.0)

	var font: Font = ThemeDB.fallback_font
	_draw_center_occult_reticle(c, vp * 0.5)
	_draw_top_biome_plaque(c, vp, font)
	_draw_crafting_material_strip(c, vp, font)
	_draw_bottom_left_vitality_panel(c, vp, font)
	_draw_bottom_right_arsenal_panel(c, vp, font)


func _draw_crafting_material_strip(c: Control, vp: Vector2, font: Font) -> void:
	if map_system != null and map_system.is_full_map_open:
		return
	if character_menu != null and character_menu.is_menu_open:
		return
	var strip_w: float = 248.0
	var strip_h: float = 30.0
	var strip_rect: Rect2 = Rect2(vp.x - strip_w - 22.0, 272.0, strip_w, strip_h)
	c.draw_rect(strip_rect, Color(0.035, 0.025, 0.04, 0.90), true)
	c.draw_rect(strip_rect, Color(0.76, 0.58, 0.28, 0.88), false, 1.4)
	if font != null:
		var mat_txt: String = "◈%d   ⚱%d   ⛓%d   ✦%d" % [silver_val, bone_ash_val, cursed_iron_val, soul_cores_val]
		c.draw_string(
			font,
			strip_rect.position + Vector2(8.0, 20.0),
			mat_txt,
			HORIZONTAL_ALIGNMENT_CENTER,
			strip_w - 16.0,
			12,
			Color(0.96, 0.86, 0.56, 0.96)
		)


func _draw_center_occult_reticle(c: Control, center: Vector2) -> void:
	if map_system != null and map_system.is_full_map_open:
		return
	if character_menu != null and character_menu.is_menu_open:
		return

	var base_rad: float = 9.0 + reticle_spread_px * 0.55
	var ring_col: Color = Color(1.0, 0.84, 0.56, 0.45)
	c.draw_arc(center, base_rad, 0.0, TAU, 32, ring_col, 1.35)
	c.draw_circle(center, 1.8, Color(1.0, 0.90, 0.70, 0.72))

	# 4 Fine Directional Alchemical Tick Marks expanding with reticle_spread_px and twisting by reticle_rotation_rad
	var tick_inner: float = base_rad + 2.5
	var tick_outer: float = tick_inner + 6.5 + minf(reticle_spread_px * 0.15, 5.0)
	var tick_col: Color = Color(1.0, 0.78, 0.48, 0.58)
	var base_angles: Array[float] = [0.0, PI * 0.5, PI, PI * 1.5]
	for ang: float in base_angles:
		var rot_ang: float = ang + reticle_rotation_rad
		var d: Vector2 = Vector2(cos(rot_ang), sin(rot_ang))
		c.draw_line(center + d * tick_inner, center + d * tick_outer, tick_col, 1.65)

	# Animated Expanding & Rotating Double-Slash Occult Hitmarker (✕) on Enemy Hit (0.22s flash)
	if hitmarker_timer > 0.0:
		var hm_alpha: float = clampf(hitmarker_timer / maxf(hitmarker_duration, 0.01), 0.0, 1.0)
		var hm_col: Color = Color(hitmarker_color.r, hitmarker_color.g, hitmarker_color.b, hm_alpha)
		var diag_angles: Array[float] = [PI * 0.25, PI * 0.75, PI * 1.25, PI * 1.75]
		var inner_r: float = 4.5 * hitmarker_scale
		var outer_r: float = 14.5 * hitmarker_scale
		var line_w: float = 2.6 if hitmarker_is_crit else 2.1
		for d_ang: float in diag_angles:
			var r_ang: float = d_ang + hitmarker_rotation
			var dd: Vector2 = Vector2(cos(r_ang), sin(r_ang))
			var perp: Vector2 = Vector2(-dd.y, dd.x) * 1.65
			# Double-slash occult crossbars
			c.draw_line(center + dd * inner_r + perp, center + dd * outer_r + perp, hm_col, line_w)
			c.draw_line(center + dd * (inner_r + 1.2) - perp, center + dd * (outer_r - 1.2) - perp, hm_col.lightened(0.18), line_w * 0.78)

		# 8 Outer Micro-Sparks on Headshot or Lethal Kill (hitmarker_is_crit == true)
		if hitmarker_is_crit:
			var spark_inner: float = outer_r + 2.5
			var spark_outer: float = spark_inner + 6.5 * hitmarker_scale
			for s_idx: int in range(8):
				var s_ang: float = float(s_idx) * (TAU / 8.0) + hitmarker_rotation * 0.65
				var sd: Vector2 = Vector2(cos(s_ang), sin(s_ang))
				c.draw_line(center + sd * spark_inner, center + sd * spark_outer, hm_col, 1.8)


func _draw_top_biome_plaque(c: Control, vp: Vector2, font: Font) -> void:
	if font == null:
		return
	var full_header: String = "── ❖ %s : %s ❖ ──" % [biome_header_title, biome_header_subtitle]
	var text_w: float = font.get_string_size(full_header, HORIZONTAL_ALIGNMENT_CENTER, -1, 13).x
	var plaque_w: float = maxf(780.0, text_w + 48.0)
	var plaque_h: float = 36.0
	var p_rect: Rect2 = Rect2((vp.x - plaque_w) * 0.5, 18.0, plaque_w, plaque_h)
	var a: float = biome_header_alpha

	c.draw_rect(p_rect, Color(0.03, 0.02, 0.04, 0.72 * a), true)
	c.draw_line(
		Vector2(p_rect.position.x + 16.0, p_rect.end.y),
		Vector2(p_rect.end.x - 16.0, p_rect.end.y),
		Color(0.84, 0.66, 0.30, 0.85 * a),
		1.5
	)
	c.draw_line(
		Vector2(p_rect.position.x + 48.0, p_rect.position.y),
		Vector2(p_rect.end.x - 48.0, p_rect.position.y),
		Color(0.68, 0.52, 0.24, 0.65 * a),
		1.0
	)

	c.draw_string(
		font,
		Vector2(p_rect.position.x, p_rect.position.y + 23.0),
		full_header,
		HORIZONTAL_ALIGNMENT_CENTER,
		plaque_w,
		13,
		Color(0.98, 0.86, 0.54, 0.96 * a)
	)


func _draw_bottom_left_vitality_panel(c: Control, vp: Vector2, font: Font) -> void:
	var panel_size: Vector2 = Vector2(396.0, 138.0)
	var p_pos: Vector2 = Vector2(26.0, vp.y - panel_size.y - 24.0)
	var p_rect: Rect2 = Rect2(p_pos, panel_size)

	# 1. Dark Obsidian-and-Brass Chamfered Frame + Corner Rivets
	c.draw_rect(p_rect.grow(3.0), Color(0.07, 0.05, 0.06, 0.92), true)
	c.draw_rect(p_rect, Color(0.035, 0.025, 0.04, 0.90), true)
	c.draw_rect(p_rect.grow(3.0), Color(0.72, 0.56, 0.28, 0.92), false, 2.0)
	c.draw_rect(p_rect, Color(0.46, 0.34, 0.18, 0.85), false, 1.0)

	var corners: Array[Vector2] = [
		p_rect.position + Vector2(5.0, 5.0),
		Vector2(p_rect.end.x - 5.0, p_rect.position.y + 5.0),
		Vector2(p_rect.position.x + 5.0, p_rect.end.y - 5.0),
		p_rect.end - Vector2(5.0, 5.0)
	]
	for rv: Vector2 in corners:
		c.draw_circle(rv, 2.6, Color(0.84, 0.68, 0.34, 0.95))

	# 2. Octagonal Hunter Level Crest (72px x 72px on the left) + Glowing XP Progress Arc
	var crest_center: Vector2 = p_pos + Vector2(48.0, 52.0)
	var crest_rad: float = 33.0
	var oct_pts: PackedVector2Array = PackedVector2Array()
	for i: int in range(8):
		var ang: float = float(i) * (TAU / 8.0) + (PI / 8.0)
		oct_pts.append(crest_center + Vector2(cos(ang), sin(ang)) * crest_rad)
	oct_pts.append(oct_pts[0])
	c.draw_colored_polygon(oct_pts, Color(0.08, 0.05, 0.07, 0.96))
	c.draw_polyline(oct_pts, Color(0.78, 0.60, 0.28, 0.95), 2.0)

	# XP Progress Arc around Crest
	var xp_ratio: float = clampf(float(cur_xp_val) / float(maxi(1, next_xp_val)), 0.05, 1.0)
	c.draw_arc(crest_center, crest_rad - 5.0, -PI * 0.5, -PI * 0.5 + TAU, 32, Color(0.22, 0.16, 0.12, 0.80), 3.0)
	c.draw_arc(crest_center, crest_rad - 5.0, -PI * 0.5, -PI * 0.5 + TAU * xp_ratio, 32, Color(1.0, 0.84, 0.30, 0.98), 3.2)

	if font != null:
		c.draw_string(font, crest_center + Vector2(-22.0, -4.0), "LEVEL", HORIZONTAL_ALIGNMENT_CENTER, 44.0, 10, Color(0.84, 0.72, 0.48, 0.92))
		c.draw_string(font, crest_center + Vector2(-22.0, 14.0), str(hunter_level_val), HORIZONTAL_ALIGNMENT_CENTER, 44.0, 18, Color(1.0, 0.90, 0.52, 1.0))
		c.draw_string(
			font,
			Vector2(p_pos.x + 8.0, p_pos.y + 98.0),
			"XP %d/%d" % [cur_xp_val, next_xp_val],
			HORIZONTAL_ALIGNMENT_CENTER,
			80.0,
			10,
			Color(0.88, 0.78, 0.54, 0.90)
		)
		c.draw_string(
			font,
			Vector2(p_pos.x + 6.0, p_pos.y + 113.0),
			"❖ %d ESS" % essence_val,
			HORIZONTAL_ALIGNMENT_CENTER,
			84.0,
			11,
			Color(0.95, 0.76, 0.34, 0.95)
		)

	# 3. Crimson Blood-Vessel Health Bar (270px x 24px) with Delayed Damage Ghost Bar & 25-HP Rib Ticks
	var bars_x: float = p_pos.x + 98.0
	var hp_rect: Rect2 = Rect2(bars_x, p_pos.y + 16.0, 276.0, 24.0)
	c.draw_rect(hp_rect, Color(0.08, 0.03, 0.04, 0.96), true)

	# Delayed Golden-White Damage Ghost Bar
	var ghost_w: float = (hp_rect.size.x - 4.0) * clampf(trail_hp_ratio, 0.0, 1.0)
	if ghost_w > 0.5:
		c.draw_rect(Rect2(hp_rect.position.x + 2.0, hp_rect.position.y + 2.0, ghost_w, hp_rect.size.y - 4.0), Color(1.0, 0.92, 0.68, 0.88), true)

	# Primary Arterial-Crimson Fill + Top Specular Sheen
	var hp_w: float = (hp_rect.size.x - 4.0) * clampf(cur_hp_ratio, 0.0, 1.0)
	if hp_w > 0.5:
		c.draw_rect(Rect2(hp_rect.position.x + 2.0, hp_rect.position.y + 2.0, hp_w, hp_rect.size.y - 4.0), Color(0.76, 0.09, 0.14, 0.98), true)
		c.draw_rect(Rect2(hp_rect.position.x + 2.0, hp_rect.position.y + 2.0, hp_w, 6.0), Color(0.95, 0.24, 0.28, 0.85), true)

	# Iron Rib Tick Marks every 25 HP
	var rib_count: int = clampi(max_hp_val / 25, 2, 16)
	for r_i: int in range(1, rib_count):
		var rx: float = hp_rect.position.x + (hp_rect.size.x * float(r_i) / float(rib_count))
		c.draw_line(Vector2(rx, hp_rect.position.y + 1.0), Vector2(rx, hp_rect.end.y - 1.0), Color(0.18, 0.12, 0.10, 0.85), 1.5)

	c.draw_rect(hp_rect, Color(0.74, 0.56, 0.28, 0.94), false, 1.5)
	if font != null:
		c.draw_string(
			font,
			Vector2(hp_rect.position.x + 10.0, hp_rect.position.y + 17.0),
			"VITALITY   %d / %d" % [cur_hp_val, max_hp_val],
			HORIZONTAL_ALIGNMENT_LEFT,
			-1,
			13,
			Color(1.0, 0.94, 0.86, 0.98)
		)

	# 4. Segmented Steel-Shield Armor Bar (276px x 18px, 5 Beveled Segments) + Equipped Armor Tier Title
	var arm_rect: Rect2 = Rect2(bars_x, p_pos.y + 48.0, 276.0, 18.0)
	var seg_count: int = 5
	var seg_gap: float = 4.0
	var seg_w: float = (arm_rect.size.x - seg_gap * float(seg_count - 1)) / float(seg_count)
	var arm_ratio: float = clampf(float(cur_armor_val) / float(maxi(1, max_armor_val)), 0.0, 1.0)

	for s_i: int in range(seg_count):
		var sx: float = arm_rect.position.x + float(s_i) * (seg_w + seg_gap)
		var s_rect: Rect2 = Rect2(sx, arm_rect.position.y, seg_w, arm_rect.size.y)
		c.draw_rect(s_rect, Color(0.07, 0.08, 0.11, 0.94), true)

		var seg_start: float = float(s_i) / float(seg_count)
		var seg_fill: float = clampf((arm_ratio - seg_start) * float(seg_count), 0.0, 1.0)
		if seg_fill > 0.01:
			var fw: float = (seg_w - 2.0) * seg_fill
			c.draw_rect(Rect2(sx + 1.0, arm_rect.position.y + 1.0, fw, arm_rect.size.y - 2.0), Color(0.38, 0.54, 0.72, 0.96), true)
			c.draw_rect(Rect2(sx + 1.0, arm_rect.position.y + 1.0, fw, 4.0), Color(0.72, 0.84, 0.96, 0.85), true)
		c.draw_rect(s_rect, Color(0.62, 0.52, 0.32, 0.88), false, 1.2)

	if font != null:
		var short_armor: String = armor_title_str.to_upper()
		c.draw_string(
			font,
			Vector2(bars_x, p_pos.y + 82.0),
			"🛡 %s  (%d / %d)" % [short_armor, cur_armor_val, max_armor_val],
			HORIZONTAL_ALIGNMENT_LEFT,
			278.0,
			11,
			Color(0.84, 0.88, 0.96, 0.95)
		)

	# 5. 4 RPG Attribute Micro-Medallions (Bottom row of panel)
	var med_y: float = p_pos.y + 92.0
	var med_w: float = 66.0
	var med_h: float = 34.0
	var attrs: Array[Dictionary] = [
		{"sym": "♦ BL", "rank": bloodlust_rank_val, "key": "[1]", "col": Color(0.95, 0.32, 0.36, 1.0)},
		{"sym": "⚡ QS", "rank": quicksilver_rank_val, "key": "[2]", "col": Color(0.38, 0.85, 1.0, 1.0)},
		{"sym": "🛡 IC", "rank": ironclad_rank_val, "key": "[3]", "col": Color(0.78, 0.84, 0.92, 1.0)},
		{"sym": "✦ EF", "rank": eldritch_rank_val, "key": "[4]", "col": Color(0.88, 0.48, 1.0, 1.0)}
	]
	for a_i: int in range(4):
		var mx: float = bars_x + float(a_i) * (med_w + 4.0)
		var m_rect: Rect2 = Rect2(mx, med_y, med_w, med_h)
		var can_up: bool = unspent_points_val > 0
		var border_c: Color = Color(1.0, 0.86, 0.28, 0.98) if can_up else Color(0.50, 0.38, 0.22, 0.82)
		c.draw_rect(m_rect, Color(0.06, 0.04, 0.06, 0.94), true)
		c.draw_rect(m_rect, border_c, false, 1.5 if can_up else 1.0)
		if font != null:
			var a_info: Dictionary = attrs[a_i]
			var label_s: String = "%s %d" % [String(a_info["sym"]), int(a_info["rank"])]
			c.draw_string(font, Vector2(mx + 4.0, med_y + 15.0), label_s, HORIZONTAL_ALIGNMENT_CENTER, med_w - 8.0, 11, a_info["col"] as Color)
			var sub_s: String = ("%s +UP" % String(a_info["key"])) if can_up else ("RANK %d" % int(a_info["rank"]))
			var sub_c: Color = Color(1.0, 0.88, 0.32, 0.98) if can_up else Color(0.68, 0.62, 0.52, 0.80)
			c.draw_string(font, Vector2(mx + 2.0, med_y + 29.0), sub_s, HORIZONTAL_ALIGNMENT_CENTER, med_w - 4.0, 9, sub_c)


func _draw_bottom_right_arsenal_panel(c: Control, vp: Vector2, font: Font) -> void:
	var panel_size: Vector2 = Vector2(360.0, 134.0)
	var p_pos: Vector2 = Vector2(vp.x - panel_size.x - 26.0, vp.y - panel_size.y - 24.0)
	var p_rect: Rect2 = Rect2(p_pos, panel_size)

	# 1. Obsidian-and-Brass Chamfered Frame + Corner Rivets
	c.draw_rect(p_rect.grow(3.0), Color(0.07, 0.05, 0.06, 0.92), true)
	c.draw_rect(p_rect, Color(0.035, 0.025, 0.04, 0.90), true)
	c.draw_rect(p_rect.grow(3.0), Color(0.72, 0.56, 0.28, 0.92), false, 2.0)
	c.draw_rect(p_rect, Color(0.46, 0.34, 0.18, 0.85), false, 1.0)

	# 2. Ornate Left-Hand Lantern Spell Medallion ([F]) on Left Side of Arsenal Panel
	var spell_center: Vector2 = p_pos + Vector2(52.0, 56.0)
	var spell_rad: float = 34.0
	c.draw_circle(spell_center, spell_rad, Color(0.08, 0.04, 0.07, 0.96))
	c.draw_arc(spell_center, spell_rad, 0.0, TAU, 36, Color(0.78, 0.60, 0.28, 0.95), 2.0)

	# Radial Cooldown Sweep
	var ready_ratio: float = 1.0
	if spell_cooldown_rem > 0.01:
		ready_ratio = clampf(1.0 - (spell_cooldown_rem / maxf(spell_cooldown_max, 0.1)), 0.0, 1.0)
	var spell_col: Color = Color(1.0, 0.68, 0.24, 0.96) if spell_cooldown_rem <= 0.05 else Color(0.45, 0.36, 0.28, 0.75)
	c.draw_arc(spell_center, spell_rad - 5.0, -PI * 0.5, -PI * 0.5 + TAU * ready_ratio, 32, spell_col, 3.5)

	if font != null:
		var cd_label: String = "[F] READY" if spell_cooldown_rem <= 0.05 else ("%.1fs" % spell_cooldown_rem)
		c.draw_string(font, spell_center + Vector2(-30.0, -4.0), "LANTERN", HORIZONTAL_ALIGNMENT_CENTER, 60.0, 9, Color(0.84, 0.72, 0.50, 0.90))
		c.draw_string(font, spell_center + Vector2(-30.0, 11.0), cd_label, HORIZONTAL_ALIGNMENT_CENTER, 60.0, 11, spell_col)
		c.draw_string(
			font,
			Vector2(p_pos.x + 8.0, p_pos.y + 106.0),
			active_spell_name_str,
			HORIZONTAL_ALIGNMENT_CENTER,
			90.0,
			10,
			Color(0.96, 0.82, 0.54, 0.94)
		)
		c.draw_string(
			font,
			Vector2(p_pos.x + 8.0, p_pos.y + 121.0),
			"[G] Cycle | Relics: %d" % active_relic_list.size(),
			HORIZONTAL_ALIGNMENT_CENTER,
			90.0,
			9,
			Color(0.78, 0.68, 0.52, 0.88)
		)

	# 3. Weapon Title & Consecration Mod Inscription
	var right_x: float = p_pos.x + 104.0
	if font != null:
		c.draw_string(
			font,
			Vector2(right_x, p_pos.y + 24.0),
			active_weapon_title_str.to_upper(),
			HORIZONTAL_ALIGNMENT_LEFT,
			244.0,
			15,
			Color(1.0, 0.88, 0.56, 0.98)
		)
		c.draw_string(
			font,
			Vector2(right_x, p_pos.y + 41.0),
			"%s (%.0f DMG)" % [weapon_mod_str, weapon_dmg_val],
			HORIZONTAL_ALIGNMENT_LEFT,
			244.0,
			11,
			Color(0.88, 0.62, 0.42, 0.92)
		)

	# 4. Physical Visual Ammo Counter (_draw() Cylinder / Shells / Railway Spikes)
	var ammo_center: Vector2 = Vector2(right_x + 42.0, p_pos.y + 74.0)
	if active_weapon_id_str == "shotgun":
		# 2 Heavy 12-Gauge Brass-and-Crimson Shells
		for sh_i: int in range(2):
			var s_rect: Rect2 = Rect2(right_x + 12.0 + float(sh_i) * 28.0, p_pos.y + 54.0, 18.0, 38.0)
			var loaded: bool = sh_i < current_ammo_val
			c.draw_rect(s_rect, Color(0.76, 0.14, 0.18, 0.95) if loaded else Color(0.14, 0.10, 0.12, 0.85), true)
			c.draw_rect(Rect2(s_rect.position.x, s_rect.end.y - 10.0, s_rect.size.x, 10.0), Color(0.88, 0.72, 0.30, 0.96) if loaded else Color(0.28, 0.24, 0.18, 0.85), true)
			c.draw_rect(s_rect, Color(0.92, 0.76, 0.38, 0.92), false, 1.2)
	elif active_weapon_id_str == "stakedriver":
		# 4 Heavy Iron Railway Spikes + Steam Pressure Gauge
		for sp_i: int in range(4):
			var sp_x: float = right_x + 8.0 + float(sp_i) * 18.0
			var loaded_sp: bool = sp_i < current_ammo_val
			var sp_col: Color = Color(0.84, 0.88, 0.94, 0.96) if loaded_sp else Color(0.20, 0.18, 0.22, 0.75)
			var pts: PackedVector2Array = PackedVector2Array([
				Vector2(sp_x + 5.0, p_pos.y + 52.0),
				Vector2(sp_x + 10.0, p_pos.y + 62.0),
				Vector2(sp_x + 8.0, p_pos.y + 90.0),
				Vector2(sp_x + 2.0, p_pos.y + 90.0),
				Vector2(sp_x, p_pos.y + 62.0)
			])
			c.draw_colored_polygon(pts, sp_col)
	else:
		# 6-Chamber Rotating Brass Revolver Cylinder Icon
		var cyl_rad: float = 22.0
		c.draw_circle(ammo_center, cyl_rad, Color(0.14, 0.11, 0.10, 0.96))
		c.draw_arc(ammo_center, cyl_rad, 0.0, TAU, 28, Color(0.82, 0.66, 0.32, 0.96), 2.0)
		c.draw_circle(ammo_center, 4.0, Color(0.45, 0.36, 0.22, 0.95))
		for ch_i: int in range(6):
			var ang: float = float(ch_i) * (TAU / 6.0) - PI * 0.5
			var ch_pt: Vector2 = ammo_center + Vector2(cos(ang), sin(ang)) * 12.5
			var is_loaded: bool = ch_i < current_ammo_val
			if is_loaded:
				c.draw_circle(ch_pt, 4.8, Color(0.92, 0.76, 0.34, 0.98))
				c.draw_circle(ch_pt, 2.2, Color(0.95, 0.24, 0.20, 0.98))
			else:
				c.draw_circle(ch_pt, 4.5, Color(0.05, 0.04, 0.06, 0.95))
				c.draw_arc(ch_pt, 4.5, 0.0, TAU, 12, Color(0.38, 0.30, 0.20, 0.75), 1.0)

	# Roman Numeral Ammo Readout
	if font != null:
		var romans: Array[String] = ["0", "I", "II", "III", "IV", "V", "VI"]
		var cur_r: String = romans[current_ammo_val] if current_ammo_val >= 0 and current_ammo_val < romans.size() else str(current_ammo_val)
		var max_r: String = romans[max_ammo_val] if max_ammo_val >= 0 and max_ammo_val < romans.size() else str(max_ammo_val)
		var ammo_col: Color = Color(0.96, 0.26, 0.22, 0.98) if current_ammo_val == 0 else Color(1.0, 0.88, 0.62, 0.98)
		c.draw_string(
			font,
			Vector2(right_x + 92.0, p_pos.y + 82.0),
			"%s / %s" % [cur_r, max_r],
			HORIZONTAL_ALIGNMENT_LEFT,
			150.0,
			24,
			ammo_col
		)

	# 5. Weapon Quick-Select Pip-Boxes ([1] Revolver | [2] Coach Gun | [3] Stake-Driver)
	var slots: Array[Dictionary] = [
		{"id": "revolver", "label": "[1] REVOLVER"},
		{"id": "shotgun", "label": "[2] COACH GUN"},
		{"id": "stakedriver", "label": "[3] STAKE-DRIVER"}
	]
	var slot_y: float = p_pos.y + 102.0
	var slot_w: float = 78.0
	for s_idx: int in range(slots.size()):
		var sl_info: Dictionary = slots[s_idx]
		var is_act: bool = (String(sl_info["id"]) == active_weapon_id_str)
		var sl_rect: Rect2 = Rect2(right_x + float(s_idx) * (slot_w + 4.0), slot_y, slot_w, 22.0)
		c.draw_rect(sl_rect, Color(0.18, 0.12, 0.08, 0.95) if is_act else Color(0.06, 0.04, 0.06, 0.88), true)
		c.draw_rect(sl_rect, Color(1.0, 0.84, 0.36, 0.98) if is_act else Color(0.45, 0.34, 0.20, 0.75), false, 1.5 if is_act else 1.0)
		if font != null:
			c.draw_string(
				font,
				Vector2(sl_rect.position.x + 2.0, sl_rect.position.y + 15.0),
				String(sl_info["label"]),
				HORIZONTAL_ALIGNMENT_CENTER,
				slot_w - 4.0,
				9,
				Color(1.0, 0.92, 0.62, 1.0) if is_act else Color(0.70, 0.62, 0.50, 0.85)
			)


func update_status_bar(
	cur_hp: int,
	max_hp: int,
	cur_armor: int,
	armor_name: String,
	essence: int,
	weapon_mod: String,
	dmg: float,
	blessing_lvl: int,
	hunter_lvl: int = 1,
	cur_xp: int = 0,
	next_xp: int = 100,
	max_arm: int = 25,
	unspent_pts: int = 0,
	attr_summary: String = "",
	active_weapon_title: String = "Occult Revolver"
) -> void:
	var new_ratio: float = clampf(float(cur_hp) / float(maxi(1, max_hp)), 0.0, 1.0)
	if new_ratio < cur_hp_ratio:
		# Trigger delayed ghost bar hold when taking damage
		_ghost_hold_timer = 0.12
	elif new_ratio > trail_hp_ratio:
		trail_hp_ratio = new_ratio

	cur_hp_val = cur_hp
	max_hp_val = maxi(1, max_hp)
	cur_hp_ratio = new_ratio
	cur_armor_val = cur_armor
	max_armor_val = maxi(1, maxi(cur_armor, max_arm))
	armor_title_str = armor_name
	essence_val = essence
	weapon_mod_str = weapon_mod
	weapon_dmg_val = dmg
	blessing_lvl_val = blessing_lvl
	hunter_level_val = hunter_lvl
	cur_xp_val = cur_xp
	next_xp_val = maxi(1, next_xp)
	unspent_points_val = unspent_pts
	active_weapon_title_str = active_weapon_title

	if viewmodel_controller != null:
		active_weapon_id_str = viewmodel_controller.active_weapon_id
		if viewmodel_controller.loadout_manager != null:
			var lm: PlayerLoadoutManager = viewmodel_controller.loadout_manager
			bloodlust_rank_val = lm.bloodlust_rank
			quicksilver_rank_val = lm.quicksilver_rank
			ironclad_rank_val = lm.ironclad_rank
			eldritch_rank_val = lm.eldritch_rank
			if character_menu != null and character_menu.loadout_manager == null:
				character_menu.loadout_manager = lm
				character_menu._connect_loadout_signals()

	if _status_label != null:
		_status_label.text = (
			"LV. %d HUNTER (XP: %d/%d)  |  HP: %d/%d  |  ARMOR: %d/%d [%s]  |  ESSENCE: %d"
			% [hunter_lvl, cur_xp, next_xp, cur_hp, max_hp, cur_armor, maxi(cur_armor, max_arm), armor_name, essence]
		)
	if _loadout_sub_label != null:
		var extra: String = ("  |  " + attr_summary) if not attr_summary.is_empty() else ""
		_loadout_sub_label.text = (
			"WEAPON: %s  |  CONSECRATION: %s (%.0f DMG)  |  BLESSING: Lv.%d%s"
			% [active_weapon_title, weapon_mod, dmg, blessing_lvl, extra]
		)
	if _attribute_prompt_label != null:
		_attribute_prompt_label.visible = unspent_pts > 0
		if unspent_pts > 0:
			_attribute_prompt_label.text = (
				"ATTRIBUTE POINTS AVAILABLE (%d): [1] +Bloodlust  [2] +Quicksilver  [3] +Ironclad  [4] +Eldritch"
				% unspent_pts
			)
	if _canvas_drawer != null:
		_canvas_drawer.queue_redraw()


func update_crafting_resources(silver: int, bone_ash: int, cursed_iron: int, soul_cores: int) -> void:
	silver_val = silver
	bone_ash_val = bone_ash
	cursed_iron_val = cursed_iron
	soul_cores_val = soul_cores
	if _canvas_drawer != null:
		_canvas_drawer.queue_redraw()
	if character_menu != null and character_menu.is_menu_open:
		character_menu.queue_redraw()


func update_spell_and_relics_display(
	spell_name: String,
	cooldown_rem: float,
	relic_names: Array[String],
	active_weapon_title: String = "Occult Revolver"
) -> void:
	active_spell_name_str = spell_name
	spell_cooldown_rem = cooldown_rem
	active_relic_list = relic_names.duplicate()
	active_weapon_title_str = active_weapon_title
	if viewmodel_controller != null:
		active_weapon_id_str = viewmodel_controller.active_weapon_id

	if _spell_relic_label != null:
		var cd_str: String = "READY" if cooldown_rem <= 0.05 else ("%.1fs" % cooldown_rem)
		var relics_str: String = "None" if relic_names.is_empty() else ", ".join(relic_names)
		_spell_relic_label.text = (
			"[Q] Swap Weapon (1: Revolver | 2: Coach Gun | 3: Stake-Driver)\n[F] %s (%s)  |  [G] Cycle Spell\nRELICS (%d): %s"
			% [spell_name, cd_str, relic_names.size(), relics_str]
		)
	if _canvas_drawer != null:
		_canvas_drawer.queue_redraw()


func set_interaction_prompt(prompt_text: String, show_prompt: bool) -> void:
	if _prompt_panel == null or _prompt_label == null:
		return
	_prompt_panel.visible = show_prompt
	if show_prompt:
		_prompt_label.text = prompt_text


func _on_ammo_changed(current: int, max_val: int) -> void:
	current_ammo_val = current
	max_ammo_val = maxi(1, max_val)
	if viewmodel_controller != null:
		active_weapon_id_str = viewmodel_controller.active_weapon_id
		active_weapon_title_str = viewmodel_controller.get_active_weapon_display_name()

	if _ammo_label != null:
		var roman_numerals: Array[String] = ["0", "I", "II", "III", "IV", "V", "VI"]
		var curr_str: String = roman_numerals[current] if current >= 0 and current < roman_numerals.size() else str(current)
		var max_str: String = roman_numerals[max_val] if max_val >= 0 and max_val < roman_numerals.size() else str(max_val)
		var weapon_prefix: String = active_weapon_title_str.to_upper()
		_ammo_label.text = "%s  —  %s  /  %s" % [weapon_prefix, curr_str, max_str]
	if _canvas_drawer != null:
		_canvas_drawer.queue_redraw()
