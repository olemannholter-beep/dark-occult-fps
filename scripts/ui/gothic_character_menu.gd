class_name GothicCharacterMenu
extends Control

const BASE_REFERENCE_SIZE: Vector2 = Vector2(1920.0, 1080.0)
const FRAME_SIZE: Vector2 = Vector2(1651.0, 928.0)
const HEADER_HEIGHT: float = 84.0
const ASTROLABE_CANVAS_SIZE: Vector2 = Vector2(1595.0, 590.0)
const INSCRIPTION_PLAQUE_SIZE: Vector2 = Vector2(1595.0, 178.0)
const PEDESTAL_VIEWPORT_SIZE: Vector2 = Vector2(540.0, 224.0)

# High-Contrast Diablo IV Etched-Slate & Aged-Bronze Gothic Palette
const COL_PANEL_BG: Color = Color(0.051, 0.055, 0.067, 0.98) # #0d0e11
const COL_PANEL_BORDER: Color = Color(0.239, 0.208, 0.169, 1.0) # #3d352b
const COL_CARD_BG: Color = Color(0.078, 0.086, 0.098, 0.98) # #141619
const COL_CARD_BG_ACTIVE: Color = Color(0.14, 0.12, 0.10, 0.98)
const COL_CARD_BORDER: Color = Color(0.18, 0.165, 0.141, 1.0) # #2e2a24
const COL_CARD_BORDER_ACTIVE: Color = Color(1.0, 0.88, 0.45, 1.0)
const COL_HEADER_GOLD: Color = Color(1.0, 0.88, 0.55, 1.0)
const COL_BODY_IVORY: Color = Color(0.95, 0.92, 0.86, 1.0)
const COL_STAT_EMERALD: Color = Color(0.35, 1.0, 0.55, 1.0)
const COL_STAT_AMBER: Color = Color(1.0, 0.78, 0.30, 1.0)
const COL_STAT_CRIMSON: Color = Color(1.0, 0.48, 0.48, 1.0)
const COL_BTN_BG: Color = Color(0.28, 0.20, 0.10, 1.0)
const COL_BTN_BG_HOVER: Color = Color(0.42, 0.30, 0.14, 1.0)
const COL_BTN_BG_ACTIVE: Color = Color(0.18, 0.32, 0.20, 1.0)
const COL_BTN_BORDER: Color = Color(1.0, 0.84, 0.42, 1.0)
const COL_BTN_FONT: Color = Color(1.0, 0.95, 0.80, 1.0)
const COL_BTN_FONT_DISABLED: Color = Color(0.80, 0.76, 0.70, 0.90)

const ARMOR_GAUNTLET_PREFABS: Array[String] = [
	"res://scenes/prefabs/armor/gauntlet_01_leather_stalker.tscn",
	"res://scenes/prefabs/armor/gauntlet_02_inquisitor_brigandine.tscn",
	"res://scenes/prefabs/armor/gauntlet_03_juggernaut_plate.tscn",
	"res://scenes/prefabs/armor/gauntlet_04_abyssal_reliquary.tscn"
]

const ARMOR_GAUNTLET_GLBS: Array[String] = [
	"res://assets/models/armor/gauntlet_01_leather_stalker.glb",
	"res://assets/models/armor/gauntlet_02_inquisitor_brigandine.glb",
	"res://assets/models/armor/gauntlet_03_juggernaut_plate.glb",
	"res://assets/models/armor/gauntlet_04_abyssal_reliquary.glb"
]

const WEAPON_GLBS: Dictionary[String, String] = {
	"revolver": "res://assets/models/weapons/viewmodel_right_revolver.glb",
	"shotgun": "res://assets/models/weapons/viewmodel_right_shotgun.glb",
	"stakedriver": "res://assets/models/weapons/viewmodel_right_stakedriver.glb"
}

const RELIC_CATALOG_LORE: Array[Dictionary] = [
	{"id": 1, "name": "Ossuary Skull Signet", "lore": "Headshots & weakpoint crits refund 1 round directly to the cylinder."},
	{"id": 2, "name": "Royal Necropolis Spur", "lore": "Reloading unleashes a 4.0m golden shockwave that staggers nearby horrors."},
	{"id": 3, "name": "Forbidden Grimoire Page", "lore": "Reduces Lantern Consecration cooldowns and amplifies occult burn duration."},
	{"id": 4, "name": "Inquisitor's Iron Brand", "lore": "Point-blank firearm strikes brand enemies with searing vulnerability."},
	{"id": 5, "name": "Plague Alchemist's Alembic", "lore": "Rounds coat targets in corrosive bile (12 DMG/sec for 4.0s)."},
	{"id": 6, "name": "Weeping Saint's Tear", "lore": "Hits arc a chain frost bolt to a nearby enemy within 8.0m for 50% damage."},
	{"id": 7, "name": "Sunken Bell Clapper", "lore": "Every 6th shot unleashes a 2.2x AoE Sonic Bell Blast across 4.5m."},
	{"id": 8, "name": "Abyssal Blood Chalice", "lore": "Lethal kills siphon vitality and fortify sanctuary regeneration."}
]

const MODE_FIELD_CHARACTER: int = 0
const MODE_GUNSMITH_WORKBENCH: int = 1
const MODE_ARMORER_STAND: int = 2
const MODE_BAPTISMAL_ASTROLABE: int = 3

var loadout_manager: PlayerLoadoutManager = null
var is_menu_open: bool = false
var active_tab: int = 0
var current_menu_mode: int = MODE_FIELD_CHARACTER
var forge_mode_active: bool = false
var forge_station_type: String = ""
var _is_dirty: bool = false
var _loot_pouch_summary_label: Label = null
var _absolution_rite_button: Button = null

# Scene Tree UI Containers (Phase 2.1)
var dim_backdrop: ColorRect = null
var vellum_backdrop: ColorRect = null
var vellum_shader_mat: ShaderMaterial = null
var main_codex_panel: Panel = null
var bg_decor_canvas: Control = null
var header_container: Panel = null
var tab1_container: Control = null
var tab2_container: Control = null
var vfx_overlay_canvas: Control = null

# Header Controls
var _header_filigree_canvas: Control = null
var _header_title_label: Label = null
var _header_xp_res_label: Label = null
var _header_sp_label: Label = null
var _tab1_button: Button = null
var _tab2_button: Button = null
var _blessing_button: Button = null
var _respec_button: Button = null
var _grant_mats_button: Button = null

# Tab 1 (Sanctuary Armory & Reliquary) Controls
var _left_wing_panel: Panel = null
var _center_nave_panel: Panel = null
var _stage_sanctuary_backdrop_canvas: Control = null
var _right_wing_panel: Panel = null
var _pedestal_frame_panel: Panel = null
var _armor_card_panels: Array[Panel] = []
var _armor_title_labels: Array[Label] = []
var _armor_sub_labels: Array[Label] = []
var _armor_perk_labels: Array[Label] = []
var _armor_action_buttons: Array[Button] = []

var _weapon_card_panels: Array[Panel] = []
var _weapon_title_labels: Array[Label] = []
var _weapon_rite_labels: Array[Label] = []
var _weapon_action_buttons: Array[Button] = []
var _weapon_mod_buttons: Array[Array] = []

var _spell_card_panels: Array[Panel] = []
var _spell_title_labels: Array[Label] = []
var _spell_action_buttons: Array[Button] = []

var _stat_row_panels: Array[Panel] = []
var _stat_name_labels: Array[Label] = []
var _stat_val_labels: Array[Label] = []
var _relic_buttons: Array[Button] = []
var _curio_title_label: Label = null
var _curio_lore_label: Label = null

# Tab 2 (Celestial Astrolabe of Rites) Controls
var _astrolabe_map_panel: Panel = null
var _astrolabe_conduit_canvas: Control = null
var _constellation_header_labels: Array[Label] = []
var _skill_node_buttons: Dictionary[String, Button] = {}
var _skill_tier_labels: Dictionary[String, Label] = {}
var _inscription_plaque_panel: Panel = null
var _skill_title_label: Label = null
var _skill_lore_label: Label = null
var _skill_effect_label: Label = null
var _skill_prereq_label: Label = null
var _consecrate_rite_button: Button = null

# 3D Reliquary Pedestal SubViewport & Full-Body Hunter Paper-Doll Rig
var sub_viewport_container: SubViewportContainer = null
var sub_viewport: SubViewport = null
var pedestal_camera: Camera3D = null
var pedestal_pivot: Node3D = null
var pedestal_plinth_mesh: MeshInstance3D = null
var _dais_assembly_root: Node3D = null
var _dais_candle_lights: Array[OmniLight3D] = []
var paperdoll_rig: HunterPaperDollRig = null
var preview_gauntlet_node: Node3D = null
var preview_weapon_node: Node3D = null
var preview_armor_index: int = -1
var preview_weapon_id: String = ""
var _gauntlet_base_pos: Vector3 = Vector3(-0.21, 0.04, 0.0)
var _weapon_base_pos: Vector3 = Vector3(0.21, 0.04, 0.0)

# Diablo IV Paper-Doll Stage, Right Stat Pillar, Bottom Tabbed 2D Icon Grid & Floating Tooltip
var _item_thumbnail_cache: Dictionary[String, Texture2D] = {}
var _field_left_equip_container: Control = null
var _left_armor_vbox: VBoxContainer = null
var _aux_right_vbox: VBoxContainer = null
var _equip_slot_cards: Array[Panel] = []
var _equip_slot_icons: Array[TextureRect] = []
var _equip_slot_titles: Array[Label] = []
var _equip_slot_subs: Array[Label] = []
var _equip_slot_badges: Array[Label] = []
var _equip_slot_pill_panels: Array[Panel] = []
var _equip_slot_check_badges: Array[Panel] = []
var _aux_relic_socket_card: Panel = null
var _aux_relic_socket_icon: TextureRect = null
var _aux_relic_socket_badge: Label = null
var _aux_relic_pill_panel: Panel = null
var _aux_relic_check_badge: Panel = null
var _set_synergy_label: Label = null
var _selected_equip_slot_index: int = -1

var _stat_pillar_panel: PanelContainer = null
var _pillar_level_label: Label = null
var _pillar_xp_label: Label = null
var _pillar_xp_bar_canvas: Control = null
var _pillar_xp_ratio: float = 0.35
var _pillar_medallion_titles: Array[Label] = []
var _pillar_medallion_vals: Array[Label] = []
var _pillar_affinity_vals: Array[Label] = []
var _pillar_currency_label: Label = null
var _pillar_dev_buttons: Array[Button] = []

var _field_center_summary_panel: Panel = null
var _field_summary_labels: Array[Label] = []

var _field_right_inv_container: Control = null
var _stash_tab_hbox: HBoxContainer = null
var _inv_filter_buttons: Array[Button] = []
var _active_inv_filter: String = "ARMOR"
var _active_slot_subfilter: String = ""
var _inv_scroll: ScrollContainer = null
var _inv_vbox: VBoxContainer = null
var _stash_grid: GridContainer = null
var _inv_inspector_panel: Panel = null
var _inv_inspector_title: Label = null
var _inv_inspector_body: Label = null

var _floating_tooltip: PanelContainer = null
var _tooltip_icon: TextureRect = null
var _tooltip_title_label: Label = null
var _tooltip_tier_label: Label = null
var _tooltip_primary_stat_label: Label = null
var _tooltip_substats_label: Label = null
var _tooltip_synergy_label: Label = null
var _tooltip_hint_label: Label = null
var _is_tooltip_active: bool = false

# Step 2 Per-Piece Armory Forge Controls (MODE_ARMORER_STAND)
var _armorer_left_container: Control = null
var _armorer_set_tab_buttons: Array[Button] = []
var _armorer_piece_cards: Array[Panel] = []
var _armorer_piece_titles: Array[Label] = []
var _armorer_piece_subs: Array[Label] = []
var _armorer_piece_buttons: Array[Button] = []
var _armorer_preview_toggle_btn: Button = null
var _armorer_comparison_header: Label = null
var _armorer_selected_set_index: int = 1
var _armorer_selected_slot_index: int = 0
var _armorer_preview_full_set: bool = false

var hovered_armor_index: int = -1
var hovered_weapon_slot: int = -1
var hovered_weapon_mod: int = -1
var hovered_spell_index: int = -1
var hovered_relic_slot: int = -1
var hovered_skill_id: String = ""
var selected_skill_id: String = "blood_1"

var _anim_time: float = 0.0
var _xp_bar_shimmer: float = 0.0
var _is_dragging_pedestal: bool = false
var _pedestal_manual_vel: float = 0.0
var _last_click_skill_id: String = ""
var _last_click_time_ms: int = 0
var _last_layout_vp_size: Vector2 = Vector2.ZERO

# Interactive hit-rect registries kept in sync for tests & direct coordinate clicks
var _tab_rects: Array[Rect2] = []
var _blessing_btn_rect: Rect2 = Rect2()
var _respec_btn_rect: Rect2 = Rect2()
var _grant_materials_btn_rect: Rect2 = Rect2()
var _armor_plaque_rects: Array[Rect2] = []
var _armor_forge_btn_rects: Array[Rect2] = []
var _pedestal_arch_rect: Rect2 = Rect2()
var _weapon_card_rects: Array[Rect2] = []
var _weapon_forge_btn_rects: Array[Rect2] = []
var _weapon_mod_socket_rects: Array[Array] = []
var _spell_medallion_rects: Array[Rect2] = []
var _spell_forge_btn_rects: Array[Rect2] = []
var _relic_socket_rects: Array[Rect2] = []
var _skill_node_centers: Dictionary[String, Vector2] = {}
var _skill_node_radii: Dictionary[String, float] = {}
var _consecrate_btn_rect: Rect2 = Rect2()

# Background drifting golden ember/ash motes (36 motes) and unlock particle bursts
var _bg_motes: Array[Dictionary] = []
var active_spark_bursts: Array[Dictionary] = []
var active_shockwave_rings: Array[Dictionary] = []
var _wax_seal_scales: Dictionary[String, float] = {}

# UI Foley Audio Players & Streams
var _ui_sfx_primary: AudioStreamPlayer = null
var _ui_sfx_secondary: AudioStreamPlayer = null
var _sfx_grimoire_open: AudioStream = null
var _sfx_armor_clank: AudioStream = null
var _sfx_skill_chime: AudioStream = null
var _sfx_tab_turn: AudioStream = null
var _initialized: bool = false


func _init() -> void:
	_ensure_initialized()


func _ready() -> void:
	_ensure_initialized()
	_resolve_loadout_manager()
	var eq_armor: int = loadout_manager.equipped_armor_index if loadout_manager != null else 0
	var eq_weap: String = loadout_manager.active_weapon_id if loadout_manager != null else "revolver"
	refresh_3d_pedestal_models(eq_armor, eq_weap)
	_update_subviewport_layout(true)
	_refresh_all_ui_elements()


func _ensure_initialized() -> void:
	if _initialized:
		return
	_initialized = true
	name = "GothicCharacterMenu"
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	modulate = Color(1.0, 1.0, 1.0, 1.0)
	self_modulate = Color(1.0, 1.0, 1.0, 1.0)
	visible = false

	_init_background_motes()
	_load_shader_reference()
	_build_scene_tree_hierarchy()
	_setup_ui_audio()
	refresh_3d_pedestal_models(0, "revolver")
	_update_subviewport_layout(true)
	_refresh_all_ui_elements()


func _load_shader_reference() -> void:
	if ResourceLoader.exists("res://shaders/gothic_vellum_frame.gdshader"):
		var shd: Shader = load("res://shaders/gothic_vellum_frame.gdshader") as Shader
		if shd != null:
			vellum_shader_mat = ShaderMaterial.new()
			vellum_shader_mat.shader = shd
			vellum_shader_mat.set_shader_parameter("tint_color", Color(0.95, 0.78, 0.36, 1.0))
			vellum_shader_mat.set_shader_parameter("border_glow", 0.48)


func _init_background_motes() -> void:
	_bg_motes.clear()
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = 4077
	for i: int in range(36):
		_bg_motes.append({
			"uv": Vector2(rng.randf_range(0.04, 0.96), rng.randf_range(0.06, 0.94)),
			"vel": Vector2(rng.randf_range(-0.012, 0.012), rng.randf_range(-0.028, -0.009)),
			"rad": rng.randf_range(1.4, 3.0),
			"phase": rng.randf_range(0.0, TAU),
			"is_crimson": (i % 4 == 0)
		})


func _setup_ui_audio() -> void:
	_ui_sfx_primary = AudioStreamPlayer.new()
	_ui_sfx_primary.name = "GothicUISFXPrimary"
	_ui_sfx_primary.volume_db = -1.5
	add_child(_ui_sfx_primary)

	_ui_sfx_secondary = AudioStreamPlayer.new()
	_ui_sfx_secondary.name = "GothicUISFXSecondary"
	_ui_sfx_secondary.volume_db = -2.5
	add_child(_ui_sfx_secondary)

	if ResourceLoader.exists("res://assets/audio/sfx/ui_grimoire_open.wav"):
		_sfx_grimoire_open = load("res://assets/audio/sfx/ui_grimoire_open.wav") as AudioStream
	if ResourceLoader.exists("res://assets/audio/sfx/ui_armor_equip_clank.wav"):
		_sfx_armor_clank = load("res://assets/audio/sfx/ui_armor_equip_clank.wav") as AudioStream
	if ResourceLoader.exists("res://assets/audio/sfx/ui_skill_consecrate_chime.wav"):
		_sfx_skill_chime = load("res://assets/audio/sfx/ui_skill_consecrate_chime.wav") as AudioStream
	if ResourceLoader.exists("res://assets/audio/sfx/ui_tab_page_turn.wav"):
		_sfx_tab_turn = load("res://assets/audio/sfx/ui_tab_page_turn.wav") as AudioStream


func _play_ui_sfx(stream: AudioStream) -> void:
	if stream == null or not is_inside_tree():
		return
	if _ui_sfx_primary != null and not _ui_sfx_primary.playing:
		_ui_sfx_primary.stream = stream
		_ui_sfx_primary.play()
	elif _ui_sfx_secondary != null:
		_ui_sfx_secondary.stream = stream
		_ui_sfx_secondary.play()


# ==============================================================================================
# STYLEBOX & CONTROL FACTORY HELPERS (Phase 2.1 & Phase 2.2)
# ==============================================================================================
func _make_stylebox(bg: Color, border: Color, border_w: int = 2, corner_r: int = 4) -> StyleBoxFlat:
	var sb: StyleBoxFlat = StyleBoxFlat.new()
	sb.bg_color = bg
	sb.border_color = border
	sb.set_border_width_all(border_w)
	sb.set_corner_radius_all(corner_r)
	return sb


func _make_label(
	node_name: String,
	text_val: String,
	font_sz: int,
	font_col: Color,
	h_align: HorizontalAlignment = HORIZONTAL_ALIGNMENT_LEFT
) -> Label:
	var lbl: Label = Label.new()
	lbl.name = node_name
	lbl.text = text_val
	lbl.horizontal_alignment = h_align
	lbl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	lbl.mouse_filter = Control.MOUSE_FILTER_IGNORE
	lbl.modulate = Color(1.0, 1.0, 1.0, 1.0)
	lbl.self_modulate = Color(1.0, 1.0, 1.0, 1.0)
	lbl.add_theme_font_size_override("font_size", font_sz)
	lbl.add_theme_color_override("font_color", font_col)
	lbl.add_theme_color_override("font_shadow_color", Color(0.03, 0.02, 0.05, 0.95))
	lbl.add_theme_constant_override("shadow_offset_x", 1)
	lbl.add_theme_constant_override("shadow_offset_y", 1)
	return lbl


func _make_gothic_button(node_name: String, text_val: String, font_sz: int = 16) -> Button:
	var btn: Button = Button.new()
	btn.name = node_name
	btn.text = text_val
	btn.modulate = Color(1.0, 1.0, 1.0, 1.0)
	btn.self_modulate = Color(1.0, 1.0, 1.0, 1.0)
	btn.focus_mode = Control.FOCUS_NONE
	btn.add_theme_font_size_override("font_size", font_sz)
	_apply_button_theme(btn, COL_BTN_BG, COL_BTN_BORDER, COL_BTN_FONT)
	return btn


func _apply_button_theme(btn: Button, bg: Color, border: Color, font_col: Color) -> void:
	if btn == null:
		return
	var sb_normal: StyleBoxFlat = _make_stylebox(bg, border, 2, 4)
	var sb_hover: StyleBoxFlat = _make_stylebox(bg.lightened(0.16), border.lightened(0.18), 2, 4)
	var sb_pressed: StyleBoxFlat = _make_stylebox(bg.darkened(0.10), border, 2, 4)
	var sb_disabled: StyleBoxFlat = _make_stylebox(Color(0.20, 0.16, 0.15, 0.95), Color(0.65, 0.54, 0.36, 0.90), 2, 4)
	btn.add_theme_stylebox_override("normal", sb_normal)
	btn.add_theme_stylebox_override("hover", sb_hover)
	btn.add_theme_stylebox_override("pressed", sb_pressed)
	btn.add_theme_stylebox_override("focus", sb_hover)
	btn.add_theme_stylebox_override("disabled", sb_disabled)
	btn.add_theme_color_override("font_color", font_col)
	btn.add_theme_color_override("font_hover_color", font_col.lightened(0.15))
	btn.add_theme_color_override("font_pressed_color", font_col)
	btn.add_theme_color_override("font_focus_color", font_col)
	btn.add_theme_color_override("font_disabled_color", COL_BTN_FONT_DISABLED)


func _attach_filigree_frame(
	target_panel: Control,
	outer_col: Color = Color.html("#8c734b"),
	inner_col: Color = Color.html("#524229"),
	corner_len: float = 18.0
) -> Control:
	var frame_c: Control = Control.new()
	frame_c.name = "FiligreeFrameOverlay"
	frame_c.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	frame_c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	frame_c.z_index = 3
	frame_c.draw.connect(func() -> void:
		var s: Vector2 = frame_c.size
		if s.x < 24.0 or s.y < 24.0:
			return
		# Weathered double-line bronze border
		frame_c.draw_rect(Rect2(Vector2(1.0, 1.0), s - Vector2(2.0, 2.0)), outer_col, false, 1.5)
		frame_c.draw_rect(Rect2(Vector2(5.0, 5.0), s - Vector2(10.0, 10.0)), inner_col, false, 1.0)
		# Corner filigree L-brackets & crimson/brass rivets
		var cl: float = minf(corner_len, minf(s.x, s.y) * 0.25)
		var c_pts: Array[Vector2] = [
			Vector2(3.0, 3.0),
			Vector2(s.x - 3.0, 3.0),
			Vector2(3.0, s.y - 3.0),
			Vector2(s.x - 3.0, s.y - 3.0)
		]
		var c_dirs: Array[Vector2] = [
			Vector2(1.0, 1.0),
			Vector2(-1.0, 1.0),
			Vector2(1.0, -1.0),
			Vector2(-1.0, -1.0)
		]
		var hi_col: Color = outer_col.lightened(0.22)
		var gem_col: Color = Color.html("#8c1d1d")
		for idx: int in range(4):
			var p: Vector2 = c_pts[idx]
			var d: Vector2 = c_dirs[idx]
			frame_c.draw_line(p, p + Vector2(d.x * cl, 0.0), hi_col, 2.2)
			frame_c.draw_line(p, p + Vector2(0.0, d.y * cl), hi_col, 2.2)
			frame_c.draw_line(p + Vector2(d.x * 4.0, d.y * 4.0), p + Vector2(d.x * (cl * 0.68), d.y * 4.0), outer_col, 1.2)
			frame_c.draw_line(p + Vector2(d.x * 4.0, d.y * 4.0), p + Vector2(d.x * 4.0, d.y * (cl * 0.68)), outer_col, 1.2)
			var gem_c: Vector2 = p + Vector2(d.x * 6.5, d.y * 6.5)
			var d_poly: PackedVector2Array = PackedVector2Array([
				gem_c + Vector2(0.0, -3.5),
				gem_c + Vector2(3.5, 0.0),
				gem_c + Vector2(0.0, 3.5),
				gem_c + Vector2(-3.5, 0.0)
			])
			frame_c.draw_colored_polygon(d_poly, gem_col)
			frame_c.draw_polyline(d_poly, hi_col, 1.0)
	)
	target_panel.add_child(frame_c)
	return frame_c


# ==============================================================================================
# BUILD SCENE TREE HIERARCHY (Phase 2.1: DimBackdrop index 0, MainCodexPanel index 1, Tabs z_index=2)
# ==============================================================================================
func _build_scene_tree_hierarchy() -> void:
	# 0. Full-Screen Dim Vignette Backdrop strictly at index 0, z_index = 0
	dim_backdrop = ColorRect.new()
	dim_backdrop.name = "DimVignetteBackdrop"
	dim_backdrop.z_index = 0
	dim_backdrop.mouse_filter = Control.MOUSE_FILTER_IGNORE
	dim_backdrop.color = Color(0.01, 0.008, 0.018, 0.76)
	add_child(dim_backdrop)
	move_child(dim_backdrop, 0)
	vellum_backdrop = dim_backdrop

	# 1. Main Codex Background Panel strictly at index 1, z_index = 0 (StyleBoxFlat, NO covering ShaderMaterial)
	main_codex_panel = Panel.new()
	main_codex_panel.name = "MainCodexPanel"
	main_codex_panel.z_index = 0
	main_codex_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	main_codex_panel.modulate = Color(1.0, 1.0, 1.0, 1.0)
	main_codex_panel.self_modulate = Color(1.0, 1.0, 1.0, 1.0)
	main_codex_panel.add_theme_stylebox_override("panel", _make_stylebox(COL_PANEL_BG, Color.html("#8c734b"), 2, 4))
	add_child(main_codex_panel)

	bg_decor_canvas = Control.new()
	bg_decor_canvas.name = "BackgroundAstrolabeDecor"
	bg_decor_canvas.z_index = 0
	bg_decor_canvas.mouse_filter = Control.MOUSE_FILTER_IGNORE
	bg_decor_canvas.draw.connect(_on_bg_decor_canvas_draw)
	main_codex_panel.add_child(bg_decor_canvas)
	_attach_filigree_frame(main_codex_panel, Color.html("#8c734b"), Color.html("#4d3d26"), 26.0)

	# 2. Top Sanctuary Header Container at z_index = 2
	header_container = Panel.new()
	header_container.name = "HeaderContainer"
	header_container.z_index = 2
	header_container.mouse_filter = Control.MOUSE_FILTER_PASS
	header_container.modulate = Color(1.0, 1.0, 1.0, 1.0)
	header_container.self_modulate = Color(1.0, 1.0, 1.0, 1.0)
	header_container.add_theme_stylebox_override("panel", _make_stylebox(Color.html("#161412"), Color.html("#8c734b"), 2, 4))
	add_child(header_container)
	_build_header_controls()

	# 3. Tab 1 Container (Sanctuary Armory & Reliquary) at z_index = 2
	tab1_container = Control.new()
	tab1_container.name = "Tab1Container"
	tab1_container.z_index = 2
	tab1_container.mouse_filter = Control.MOUSE_FILTER_PASS
	tab1_container.modulate = Color(1.0, 1.0, 1.0, 1.0)
	tab1_container.self_modulate = Color(1.0, 1.0, 1.0, 1.0)
	add_child(tab1_container)
	_build_tab1_controls()

	# 4. Tab 2 Container (Celestial Astrolabe of Rites) at z_index = 2
	tab2_container = Control.new()
	tab2_container.name = "Tab2Container"
	tab2_container.z_index = 2
	tab2_container.mouse_filter = Control.MOUSE_FILTER_PASS
	tab2_container.modulate = Color(1.0, 1.0, 1.0, 1.0)
	tab2_container.self_modulate = Color(1.0, 1.0, 1.0, 1.0)
	tab2_container.visible = false
	add_child(tab2_container)
	_build_tab2_controls()

	# 5. Foreground VFX Spark & Shockwave Canvas at z_index = 4
	vfx_overlay_canvas = Control.new()
	vfx_overlay_canvas.name = "VFXOverlayCanvas"
	vfx_overlay_canvas.z_index = 4
	vfx_overlay_canvas.mouse_filter = Control.MOUSE_FILTER_IGNORE
	vfx_overlay_canvas.draw.connect(_on_vfx_overlay_canvas_draw)
	add_child(vfx_overlay_canvas)


func _build_header_controls() -> void:
	_header_filigree_canvas = Control.new()
	_header_filigree_canvas.name = "HeaderOrnateBannerCanvas"
	_header_filigree_canvas.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_header_filigree_canvas.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_header_filigree_canvas.draw.connect(_on_header_filigree_draw)
	header_container.add_child(_header_filigree_canvas)

	_header_title_label = _make_label("HunterTitleLabel", "THE HUNTER'S RELIQUARY", 19, COL_HEADER_GOLD, HORIZONTAL_ALIGNMENT_CENTER)
	_header_title_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	header_container.add_child(_header_title_label)

	_header_xp_res_label = _make_label("HeaderXPResLabel", "LEVEL 1 — XP: 0 / 100", 14, COL_BODY_IVORY, HORIZONTAL_ALIGNMENT_LEFT)
	header_container.add_child(_header_xp_res_label)

	_tab1_button = _make_gothic_button("Tab1ArmoryButton", "❖ I. SANCTUARY ARMORY & RELIQUARY ❖", 14)
	_tab1_button.pressed.connect(func() -> void: switch_tab(0))
	header_container.add_child(_tab1_button)

	_tab2_button = _make_gothic_button("Tab2AstrolabeButton", "❖ II. CELESTIAL ASTROLABE OF RITES ❖", 14)
	_tab2_button.pressed.connect(func() -> void: switch_tab(1))
	header_container.add_child(_tab2_button)

	_header_sp_label = _make_label("HeaderSPLabel", "✦ 3 SP | ◈35 SILVER | ⚱15 ASH | ⛓0 IRON | ✦0 CORE", 14, COL_STAT_AMBER, HORIZONTAL_ALIGNMENT_RIGHT)
	header_container.add_child(_header_sp_label)

	_blessing_button = _make_gothic_button("BlessingSPButton", "[+2 SP]", 12)
	_blessing_button.pressed.connect(trigger_sanctuary_blessing)
	header_container.add_child(_blessing_button)

	_respec_button = _make_gothic_button("RespecRitesButton", "[RESPEC]", 12)
	_respec_button.pressed.connect(func() -> void: trigger_respec_rites())
	header_container.add_child(_respec_button)

	_grant_mats_button = _make_gothic_button("GrantTestMatsButton", "[+GRANT MATS]", 12)
	_grant_mats_button.pressed.connect(trigger_grant_test_materials)
	header_container.add_child(_grant_mats_button)


func _on_header_filigree_draw() -> void:
	if _header_filigree_canvas == null:
		return
	var s: Vector2 = _header_filigree_canvas.size
	if s.x < 100.0 or s.y < 30.0:
		return
	var brass_bdr: Color = Color.html("#8c734b")
	var brass_hi: Color = Color.html("#c4a468")
	var brass_dim: Color = Color.html("#524229")
	var plaque_fill: Color = Color.html("#161412")
	var crimson_gem: Color = Color.html("#8c1d1d")
	var crimson_hi: Color = Color.html("#dc4242")

	# Double-line bronze border around header bar
	_header_filigree_canvas.draw_rect(Rect2(Vector2(3.0, 3.0), s - Vector2(6.0, 6.0)), brass_dim, false, 1.0)
	var cx: float = s.x * 0.5
	var np_w: float = 440.0
	var np_h: float = 34.0
	var np_top: float = 4.0
	var np_left: float = cx - np_w * 0.5
	var np_right: float = cx + np_w * 0.5
	var np_cy: float = np_top + np_h * 0.5

	# Procedural brass scrollwork wings extending left and right from the central nameplate
	for side_f: float in [-1.0, 1.0]:
		var anchor_x: float = cx + side_f * (np_w * 0.5 + 8.0)
		for curl_i: int in range(3):
			var c_dist: float = 28.0 + float(curl_i) * 44.0
			var curl_c: Vector2 = Vector2(anchor_x + side_f * c_dist, np_cy)
			var rad: float = 11.0 - float(curl_i) * 2.2
			_header_filigree_canvas.draw_arc(curl_c, rad, 0.0, TAU, 20, brass_bdr, 1.5)
			_header_filigree_canvas.draw_circle(curl_c, 2.5, brass_hi)
		_header_filigree_canvas.draw_line(
			Vector2(anchor_x, np_cy),
			Vector2(anchor_x + side_f * 155.0, np_cy),
			brass_bdr,
			1.8
		)
		_header_filigree_canvas.draw_line(
			Vector2(anchor_x + side_f * 14.0, np_cy - 6.0),
			Vector2(anchor_x + side_f * 120.0, np_cy - 6.0),
			brass_dim,
			1.0
		)

	# Centered Gothic Nameplate Plaque (#161412 fill, #8c734b border) with beveled ends
	var plaque_pts: PackedVector2Array = PackedVector2Array([
		Vector2(np_left + 12.0, np_top),
		Vector2(np_right - 12.0, np_top),
		Vector2(np_right, np_cy),
		Vector2(np_right - 12.0, np_top + np_h),
		Vector2(np_left + 12.0, np_top + np_h),
		Vector2(np_left, np_cy),
		Vector2(np_left + 12.0, np_top)
	])
	_header_filigree_canvas.draw_colored_polygon(plaque_pts, plaque_fill)
	_header_filigree_canvas.draw_polyline(plaque_pts, brass_bdr, 2.0)
	_header_filigree_canvas.draw_rect(Rect2(Vector2(np_left + 16.0, np_top + 3.0), Vector2(np_w - 32.0, np_h - 6.0)), brass_dim, false, 1.0)

	# Flanking Skull Medallions & Crimson Diamond Gems (#8c1d1d)
	for side_f2: float in [-1.0, 1.0]:
		# Crimson Diamond Gem on outer bevel point of nameplate
		var gem_pt: Vector2 = Vector2(cx + side_f2 * (np_w * 0.5 - 2.0), np_cy)
		var gem_poly: PackedVector2Array = PackedVector2Array([
			gem_pt + Vector2(0.0, -7.0),
			gem_pt + Vector2(7.0, 0.0),
			gem_pt + Vector2(0.0, 7.0),
			gem_pt + Vector2(-7.0, 0.0),
			gem_pt + Vector2(0.0, -7.0)
		])
		_header_filigree_canvas.draw_colored_polygon(gem_poly, crimson_gem)
		_header_filigree_canvas.draw_polyline(gem_poly, brass_hi, 1.4)
		_header_filigree_canvas.draw_circle(gem_pt + Vector2(-1.5, -1.5), 2.0, crimson_hi)

		# Forged Skull Medallion flanking the title inside/beside the plaque
		var skull_c: Vector2 = Vector2(cx + side_f2 * (np_w * 0.5 - 30.0), np_cy)
		_header_filigree_canvas.draw_circle(skull_c, 11.0, Color.html("#1e1b18"))
		_header_filigree_canvas.draw_arc(skull_c, 11.0, 0.0, TAU, 20, brass_bdr, 1.6)
		# Stylized ivory skull cranium + jaw + dark eye sockets
		_header_filigree_canvas.draw_circle(skull_c + Vector2(0.0, -1.5), 5.5, Color.html("#d8cfc0"))
		_header_filigree_canvas.draw_rect(Rect2(skull_c + Vector2(-3.2, 2.0), Vector2(6.4, 4.0)), Color.html("#c7bdb0"), true)
		_header_filigree_canvas.draw_circle(skull_c + Vector2(-2.2, -1.5), 1.5, plaque_fill)
		_header_filigree_canvas.draw_circle(skull_c + Vector2(2.2, -1.5), 1.5, plaque_fill)


func _build_tab1_controls() -> void:
	# Left Wing: 4 Armor Vestment & Gauntlet Cards
	_left_wing_panel = Panel.new()
	_left_wing_panel.name = "LeftWingArmorPanel"
	_left_wing_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_left_wing_panel.size_flags_stretch_ratio = 1.0
	_left_wing_panel.mouse_filter = Control.MOUSE_FILTER_PASS
	_left_wing_panel.modulate = Color(1.0, 1.0, 1.0, 1.0)
	_left_wing_panel.self_modulate = Color(1.0, 1.0, 1.0, 1.0)
	_left_wing_panel.add_theme_stylebox_override("panel", _make_stylebox(Color(0.09, 0.08, 0.12, 0.96), COL_CARD_BORDER, 2, 5))
	tab1_container.add_child(_left_wing_panel)

	var left_hdr: Label = _make_label("LeftWingHeaderLabel", "❖ VESTMENTS & GAUNTLETS ❖", 20, COL_HEADER_GOLD, HORIZONTAL_ALIGNMENT_CENTER)
	_left_wing_panel.add_child(left_hdr)

	_armor_card_panels.clear()
	_armor_title_labels.clear()
	_armor_sub_labels.clear()
	_armor_perk_labels.clear()
	_armor_action_buttons.clear()

	var armor_cat: Array[Dictionary] = PlayerLoadoutManager.get_armor_set_catalog()
	for i: int in range(armor_cat.size()):
		var a_info: Dictionary = armor_cat[i]
		var card: Panel = Panel.new()
		card.name = "ArmorCard_%d" % i
		card.mouse_filter = Control.MOUSE_FILTER_PASS
		card.modulate = Color(1.0, 1.0, 1.0, 1.0)
		card.self_modulate = Color(1.0, 1.0, 1.0, 1.0)
		card.add_theme_stylebox_override("panel", _make_stylebox(COL_CARD_BG, COL_CARD_BORDER, 2, 4))
		var arm_idx: int = i
		card.mouse_entered.connect(func() -> void: _on_armor_card_hovered(arm_idx))
		_left_wing_panel.add_child(card)
		_armor_card_panels.append(card)

		var t_lbl: Label = _make_label("ArmorTitleLabel_%d" % i, String(a_info["name"]), 20, COL_HEADER_GOLD, HORIZONTAL_ALIGNMENT_LEFT)
		card.add_child(t_lbl)
		_armor_title_labels.append(t_lbl)

		var s_lbl: Label = _make_label(
			"ArmorRatingLabel_%d" % i,
			"%d ARMOR  —  %s" % [int(a_info["armor"]), String(a_info["subtitle"])],
			16,
			COL_STAT_EMERALD,
			HORIZONTAL_ALIGNMENT_LEFT
		)
		card.add_child(s_lbl)
		_armor_sub_labels.append(s_lbl)

		var perks: Array = a_info["perks"] as Array
		var perk_lines: PackedStringArray = PackedStringArray()
		for pk: Variant in perks:
			perk_lines.append(String(pk))
		var p_lbl: Label = _make_label("ArmorPerksLabel_%d" % i, "\n".join(perk_lines), 16, COL_BODY_IVORY, HORIZONTAL_ALIGNMENT_LEFT)
		card.add_child(p_lbl)
		_armor_perk_labels.append(p_lbl)

		var a_btn: Button = _make_gothic_button("ArmorActionButton_%d" % i, "[ EQUIP ]", 16)
		a_btn.pressed.connect(func() -> void: _on_armor_button_pressed(arm_idx))
		a_btn.mouse_entered.connect(func() -> void: _on_armor_card_hovered(arm_idx))
		card.add_child(a_btn)
		_armor_action_buttons.append(a_btn)

	# Center Nave: 3D Pedestal SubViewport + 3 Weapon Forge Cards + 3 Lantern Spell Cards
	_center_nave_panel = Panel.new()
	_center_nave_panel.name = "CenterNaveArsenalPanel"
	_center_nave_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_center_nave_panel.size_flags_stretch_ratio = 1.35
	_center_nave_panel.mouse_filter = Control.MOUSE_FILTER_PASS
	_center_nave_panel.modulate = Color(1.0, 1.0, 1.0, 1.0)
	_center_nave_panel.self_modulate = Color(1.0, 1.0, 1.0, 1.0)
	_center_nave_panel.add_theme_stylebox_override("panel", _make_stylebox(Color(0.09, 0.08, 0.12, 0.96), Color.html("#8c734b"), 2, 5))
	tab1_container.add_child(_center_nave_panel)

	_stage_sanctuary_backdrop_canvas = Control.new()
	_stage_sanctuary_backdrop_canvas.name = "StageSanctuaryBackdropCanvas"
	_stage_sanctuary_backdrop_canvas.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_stage_sanctuary_backdrop_canvas.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_stage_sanctuary_backdrop_canvas.draw.connect(_on_stage_sanctuary_backdrop_draw)
	_center_nave_panel.add_child(_stage_sanctuary_backdrop_canvas)
	_attach_filigree_frame(_center_nave_panel, Color.html("#8c734b"), Color.html("#4d3d26"), 20.0)

	var ped_hdr: Label = _make_label("PedestalHeaderLabel", "❖ 3D RELIQUARY PEDESTAL (DRAG TO ROTATE) ❖", 20, COL_HEADER_GOLD, HORIZONTAL_ALIGNMENT_CENTER)
	_center_nave_panel.add_child(ped_hdr)

	_pedestal_frame_panel = Panel.new()
	_pedestal_frame_panel.name = "PedestalFramePanel"
	_pedestal_frame_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_pedestal_frame_panel.add_theme_stylebox_override("panel", _make_stylebox(Color(0.06, 0.05, 0.08, 0.98), COL_CARD_BORDER_ACTIVE, 2, 4))
	_center_nave_panel.add_child(_pedestal_frame_panel)

	_build_3d_reliquary_pedestal()

	var forge_hdr: Label = _make_label("ArsenalForgeHeaderLabel", "❖ ARSENAL RITE-MOD FORGE ❖", 20, COL_HEADER_GOLD, HORIZONTAL_ALIGNMENT_CENTER)
	_center_nave_panel.add_child(forge_hdr)

	_weapon_card_panels.clear()
	_weapon_title_labels.clear()
	_weapon_rite_labels.clear()
	_weapon_action_buttons.clear()
	_weapon_mod_buttons.clear()

	var weapons_info: Array[Dictionary] = [
		{"id": "revolver", "title": "OCCULT REVOLVER", "base_dmg": 38},
		{"id": "shotgun", "title": "HELLFIRE COACH GUN", "base_dmg": 128},
		{"id": "stakedriver", "title": "PNEUMATIC STAKE-DRIVER", "base_dmg": 65}
	]
	var mods_cat: Array[Dictionary] = PlayerLoadoutManager.get_weapon_mod_catalog()

	for w_i: int in range(3):
		var w_info: Dictionary = weapons_info[w_i]
		var w_card: Panel = Panel.new()
		w_card.name = "WeaponCard_%d" % w_i
		w_card.mouse_filter = Control.MOUSE_FILTER_PASS
		w_card.modulate = Color(1.0, 1.0, 1.0, 1.0)
		w_card.self_modulate = Color(1.0, 1.0, 1.0, 1.0)
		w_card.add_theme_stylebox_override("panel", _make_stylebox(COL_CARD_BG, COL_CARD_BORDER, 2, 4))
		_center_nave_panel.add_child(w_card)
		_weapon_card_panels.append(w_card)

		var wt_lbl: Label = _make_label("WeaponTitleLabel_%d" % w_i, String(w_info["title"]), 20, COL_HEADER_GOLD, HORIZONTAL_ALIGNMENT_LEFT)
		w_card.add_child(wt_lbl)
		_weapon_title_labels.append(wt_lbl)

		var wr_lbl: Label = _make_label("WeaponRiteLabel_%d" % w_i, "Rite: Sanctified Silver-Core", 16, COL_BODY_IVORY, HORIZONTAL_ALIGNMENT_LEFT)
		w_card.add_child(wr_lbl)
		_weapon_rite_labels.append(wr_lbl)

		var w_slot: int = w_i
		var w_btn: Button = _make_gothic_button("WeaponActionButton_%d" % w_i, "[ EQUIP ]", 16)
		w_btn.pressed.connect(func() -> void: _on_weapon_button_pressed(w_slot))
		w_card.add_child(w_btn)
		_weapon_action_buttons.append(w_btn)

		var mod_btns_row: Array[Button] = []
		for m_i: int in range(4):
			var m_info: Dictionary = mods_cat[m_i]
			var m_slot: int = m_i
			var m_btn: Button = _make_gothic_button("Weapon_%d_ModBtn_%d" % [w_i, m_i], String(m_info["short"]), 15)
			m_btn.pressed.connect(func() -> void: select_weapon_mod_socket(w_slot, m_slot))
			w_card.add_child(m_btn)
			mod_btns_row.append(m_btn)
		_weapon_mod_buttons.append(mod_btns_row)

	var spells_hdr: Label = _make_label("LanternSpellsHeaderLabel", "❖ [F] LANTERN CONSECRATION RITES ❖", 20, COL_HEADER_GOLD, HORIZONTAL_ALIGNMENT_CENTER)
	_center_nave_panel.add_child(spells_hdr)

	_spell_card_panels.clear()
	_spell_title_labels.clear()
	_spell_action_buttons.clear()
	var spells_cat: Array[Dictionary] = PlayerLoadoutManager.get_lantern_spell_catalog()
	for s_i: int in range(3):
		var sp_info: Dictionary = spells_cat[s_i]
		var sp_card: Panel = Panel.new()
		sp_card.name = "SpellCard_%d" % s_i
		sp_card.mouse_filter = Control.MOUSE_FILTER_PASS
		sp_card.modulate = Color(1.0, 1.0, 1.0, 1.0)
		sp_card.self_modulate = Color(1.0, 1.0, 1.0, 1.0)
		sp_card.add_theme_stylebox_override("panel", _make_stylebox(COL_CARD_BG, COL_CARD_BORDER, 2, 4))
		_center_nave_panel.add_child(sp_card)
		_spell_card_panels.append(sp_card)

		var st_lbl: Label = _make_label("SpellTitleLabel_%d" % s_i, String(sp_info["name"]), 16, COL_HEADER_GOLD, HORIZONTAL_ALIGNMENT_CENTER)
		st_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		sp_card.add_child(st_lbl)
		_spell_title_labels.append(st_lbl)

		var sp_idx: int = s_i
		var sp_btn: Button = _make_gothic_button("SpellActionButton_%d" % s_i, "[ EQUIP ]", 14)
		sp_btn.pressed.connect(func() -> void: select_lantern_spell(sp_idx))
		sp_card.add_child(sp_btn)
		_spell_action_buttons.append(sp_btn)

	# Right Wing: 12-Stat Hunter's Illuminated Ledger & 2x4 Curios Vault
	_right_wing_panel = Panel.new()
	_right_wing_panel.name = "RightWingLedgerPanel"
	_right_wing_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_right_wing_panel.size_flags_stretch_ratio = 1.0
	_right_wing_panel.mouse_filter = Control.MOUSE_FILTER_PASS
	_right_wing_panel.modulate = Color(1.0, 1.0, 1.0, 1.0)
	_right_wing_panel.self_modulate = Color(1.0, 1.0, 1.0, 1.0)
	_right_wing_panel.add_theme_stylebox_override("panel", _make_stylebox(Color(0.09, 0.08, 0.12, 0.96), COL_CARD_BORDER, 2, 5))
	tab1_container.add_child(_right_wing_panel)

	var right_hdr: Label = _make_label("RightWingHeaderLabel", "❖ THE HUNTER'S ILLUMINATED LEDGER ❖", 20, COL_HEADER_GOLD, HORIZONTAL_ALIGNMENT_CENTER)
	_right_wing_panel.add_child(right_hdr)

	_stat_row_panels.clear()
	_stat_name_labels.clear()
	_stat_val_labels.clear()
	for r_i: int in range(12):
		var r_panel: Panel = Panel.new()
		r_panel.name = "LedgerStatRow_%d" % r_i
		r_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var row_bg: Color = Color(0.13, 0.11, 0.17, 0.96) if (r_i % 2 == 0) else Color(0.10, 0.09, 0.14, 0.96)
		r_panel.add_theme_stylebox_override("panel", _make_stylebox(row_bg, Color(0.55, 0.44, 0.24, 0.65), 1, 3))
		_right_wing_panel.add_child(r_panel)
		_stat_row_panels.append(r_panel)

		var sn_lbl: Label = _make_label("StatNameLabel_%d" % r_i, "Stat", 16, COL_BODY_IVORY, HORIZONTAL_ALIGNMENT_LEFT)
		r_panel.add_child(sn_lbl)
		_stat_name_labels.append(sn_lbl)

		var sv_lbl: Label = _make_label("StatValueLabel_%d" % r_i, "100%", 16, COL_STAT_AMBER, HORIZONTAL_ALIGNMENT_RIGHT)
		r_panel.add_child(sv_lbl)
		_stat_val_labels.append(sv_lbl)

	var vault_hdr: Label = _make_label("CuriosVaultHeaderLabel", "❖ RELIQUARY CURIOS VAULT (2×4) ❖", 20, COL_HEADER_GOLD, HORIZONTAL_ALIGNMENT_CENTER)
	_right_wing_panel.add_child(vault_hdr)

	_relic_buttons.clear()
	for rel_i: int in range(8):
		var r_slot: int = rel_i
		var rel_btn: Button = _make_gothic_button("RelicCurioButton_%d" % rel_i, "RELIC %d" % (rel_i + 1), 15)
		rel_btn.mouse_entered.connect(func() -> void:
			hovered_relic_slot = r_slot
			_refresh_all_ui_elements()
		)
		rel_btn.pressed.connect(func() -> void:
			hovered_relic_slot = r_slot
			_refresh_all_ui_elements()
		)
		_right_wing_panel.add_child(rel_btn)
		_relic_buttons.append(rel_btn)

	_curio_title_label = _make_label("CurioLoreTitleLabel", "✦ Ossuary Skull Signet", 20, COL_HEADER_GOLD, HORIZONTAL_ALIGNMENT_LEFT)
	_right_wing_panel.add_child(_curio_title_label)

	_curio_lore_label = _make_label("CurioLoreBodyLabel", RELIC_CATALOG_LORE[0]["lore"] as String, 16, COL_BODY_IVORY, HORIZONTAL_ALIGNMENT_LEFT)
	_curio_lore_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_right_wing_panel.add_child(_curio_lore_label)

	_loot_pouch_summary_label = _make_label(
		"LootPouchSummaryLabel",
		"COLLECTED LOOT POUCH: ◈35 Silver (Gunsmith) | ⚱15 Ash (Mods) | ⛓0 Iron (Armory) | ✦0 Cores (Font)",
		14,
		COL_STAT_AMBER,
		HORIZONTAL_ALIGNMENT_LEFT
	)
	_loot_pouch_summary_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_right_wing_panel.add_child(_loot_pouch_summary_label)

	_absolution_rite_button = _make_gothic_button("AbsolutionRiteButton", "[ ✦ RITE OF ABSOLUTION (RESPEC ALL SKILL POINTS) ]", 16)
	_absolution_rite_button.pressed.connect(func() -> void: trigger_respec_rites())
	_absolution_rite_button.visible = false
	_right_wing_panel.add_child(_absolution_rite_button)

	_build_field_character_tab1_controls()
	_build_armorer_stand_controls()


func _get_or_create_item_thumbnail(slot_type: String, tier_idx: int = 0) -> Texture2D:
	# Set 0 (tier_idx == 0) remains untouched; Sets 1, 2, and 3 generate 7mm micro-voxel matching icons
	var key: String = "%s_%d" % [slot_type.to_upper().strip_edges(), tier_idx]
	if _item_thumbnail_cache.has(key):
		return _item_thumbnail_cache[key]
	var tex: Texture2D = GothicItemIconGenerator.get_or_create_thumbnail(slot_type, tier_idx)
	_item_thumbnail_cache[key] = tex
	return tex



func _on_stage_sanctuary_backdrop_draw() -> void:
	if _stage_sanctuary_backdrop_canvas == null:
		return
	var s: Vector2 = _stage_sanctuary_backdrop_canvas.size
	if s.x < 60.0 or s.y < 60.0:
		return
	var cx: float = s.x * 0.5
	# Deep atmospheric sanctuary nave background
	_stage_sanctuary_backdrop_canvas.draw_rect(Rect2(Vector2.ZERO, s), Color.html("#08090c"), true)
	# Blurred dark gothic sanctuary columns & pointed lancet arches behind the Hunter
	var col_offsets: Array[float] = [-235.0, -140.0, 140.0, 235.0]
	for ox: float in col_offsets:
		var px: float = cx + ox
		var col_w: float = 26.0 if absf(ox) > 180.0 else 18.0
		_stage_sanctuary_backdrop_canvas.draw_rect(
			Rect2(Vector2(px - col_w * 0.5, 10.0), Vector2(col_w, s.y - 20.0)),
			Color(0.11, 0.10, 0.12, 0.68),
			true
		)
		_stage_sanctuary_backdrop_canvas.draw_line(
			Vector2(px - col_w * 0.3, 14.0),
			Vector2(px - col_w * 0.3, s.y - 14.0),
			Color(0.28, 0.23, 0.16, 0.35),
			1.5
		)
	# Gothic pointed nave vaulting ribs
	for arch_r: float in [165.0, 235.0]:
		_stage_sanctuary_backdrop_canvas.draw_arc(
			Vector2(cx, s.y * 0.44),
			arch_r,
			PI * 1.08,
			PI * 1.92,
			40,
			Color(0.55, 0.44, 0.28, 0.26),
			2.0
		)
	# Warm sanctuary candle cluster glow & golden dais floor reflection
	var dais_glow_c: Vector2 = Vector2(cx, s.y * 0.78)
	for g_i: int in range(6):
		var t_g: float = float(g_i) / 6.0
		var rad_g: float = lerpf(210.0, 42.0, t_g)
		var col_g: Color = Color(1.0, 0.65, 0.22, lerpf(0.03, 0.14, t_g))
		_stage_sanctuary_backdrop_canvas.draw_circle(dais_glow_c, rad_g, col_g)


func _attach_double_bevel_socket_frame(card: Control, is_empty_lattice: bool = false) -> Control:
	var bev: Control = Control.new()
	bev.name = "DoubleBevelMetallicFrame"
	bev.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bev.mouse_filter = Control.MOUSE_FILTER_IGNORE
	bev.draw.connect(func() -> void:
		var sz: Vector2 = bev.size
		if sz.x < 16.0 or sz.y < 16.0:
			return
		if is_empty_lattice:
			# Recessed dark-iron diamond / X lattice relief (#121316 base, #22242a inner relief)
			var relief_col: Color = Color.html("#22242a")
			var shadow_col: Color = Color.html("#0b0c0e")
			var pad: float = 7.0
			bev.draw_line(Vector2(pad, pad), Vector2(sz.x - pad, sz.y - pad), shadow_col, 2.2)
			bev.draw_line(Vector2(sz.x - pad, pad), Vector2(pad, sz.y - pad), shadow_col, 2.2)
			bev.draw_line(Vector2(pad, pad), Vector2(sz.x - pad, sz.y - pad), relief_col, 1.2)
			bev.draw_line(Vector2(sz.x - pad, pad), Vector2(pad, sz.y - pad), relief_col, 1.2)
			var mid: Vector2 = sz * 0.5
			var dm_r: float = minf(sz.x, sz.y) * 0.28
			var dm_pts: PackedVector2Array = PackedVector2Array([
				mid + Vector2(0.0, -dm_r),
				mid + Vector2(dm_r, 0.0),
				mid + Vector2(0.0, dm_r),
				mid + Vector2(-dm_r, 0.0),
				mid + Vector2(0.0, -dm_r)
			])
			bev.draw_polyline(dm_pts, relief_col, 1.3)
			bev.draw_circle(mid, 2.2, relief_col.lightened(0.12))
		var outer_bdr: Color = card.get_meta("bevel_outer_col", Color.html("#6e563a")) as Color
		var inner_bdr: Color = card.get_meta("bevel_inner_col", Color.html("#2c251d")) as Color
		bev.draw_rect(Rect2(Vector2(1.0, 1.0), sz - Vector2(2.0, 2.0)), outer_bdr, false, 1.5)
		bev.draw_rect(Rect2(Vector2(3.5, 3.5), sz - Vector2(7.0, 7.0)), inner_bdr, false, 1.0)
		# Metallic corner bevel ticks
		var c_hi: Color = outer_bdr.lightened(0.24)
		for cx_f: float in [2.0, sz.x - 2.0]:
			for cy_f: float in [2.0, sz.y - 2.0]:
				bev.draw_circle(Vector2(cx_f, cy_f), 1.4, c_hi)
	)
	card.add_child(bev)
	return bev


func _create_paperdoll_socket(
	sock_name: String,
	slot_idx: int,
	default_slot_type: String,
	default_badge: String
) -> Panel:
	var s_card: Panel = Panel.new()
	s_card.name = sock_name
	s_card.custom_minimum_size = Vector2(68.0, 76.0)
	s_card.size = Vector2(68.0, 76.0)
	s_card.mouse_filter = Control.MOUSE_FILTER_STOP
	s_card.set_meta("bevel_outer_col", Color.html("#8c734b"))
	s_card.set_meta("bevel_inner_col", Color.html("#3d3222"))
	s_card.add_theme_stylebox_override("panel", _make_stylebox(Color.html("#141619"), Color.html("#5a4930"), 1, 3))
	if slot_idx >= 0:
		var cap_idx: int = slot_idx
		s_card.mouse_entered.connect(func() -> void: _on_left_equip_slot_hovered(cap_idx))
		s_card.mouse_exited.connect(func() -> void: _hide_floating_tooltip())
		s_card.gui_input.connect(func(ev: InputEvent) -> void:
			if ev is InputEventMouseButton:
				var mb: InputEventMouseButton = ev as InputEventMouseButton
				if mb.button_index == MOUSE_BUTTON_LEFT and mb.pressed:
					_on_left_equip_slot_clicked(cap_idx)
		)

	var icon_rect: TextureRect = TextureRect.new()
	icon_rect.name = "SocketIcon"
	icon_rect.position = Vector2(4.0, 4.0)
	icon_rect.size = Vector2(60.0, 60.0)
	icon_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	icon_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	icon_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	icon_rect.texture = _get_or_create_item_thumbnail(default_slot_type, 0)
	s_card.add_child(icon_rect)

	_attach_double_bevel_socket_frame(s_card, false)

	# Top-left equipped checkmark badge (✓)
	var chk_panel: Panel = Panel.new()
	chk_panel.name = "EquippedCheckBadge"
	chk_panel.position = Vector2(4.0, 4.0)
	chk_panel.size = Vector2(17.0, 17.0)
	chk_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	chk_panel.add_theme_stylebox_override("panel", _make_stylebox(Color(0.08, 0.07, 0.05, 0.95), COL_HEADER_GOLD, 1, 2))
	s_card.add_child(chk_panel)
	var chk_lbl: Label = _make_label("CheckLbl", "✓", 11, COL_HEADER_GOLD, HORIZONTAL_ALIGNMENT_CENTER)
	chk_lbl.position = Vector2.ZERO
	chk_lbl.size = Vector2(17.0, 17.0)
	chk_panel.add_child(chk_lbl)

	# Bottom-right dark pill for armor/stat values (+10, +19)
	var pill_panel: Panel = Panel.new()
	pill_panel.name = "SocketValuePill"
	pill_panel.position = Vector2(28.0, 54.0)
	pill_panel.size = Vector2(36.0, 18.0)
	pill_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pill_panel.add_theme_stylebox_override("panel", _make_stylebox(Color.html("#0b0c0f"), Color.html("#8c734b"), 1, 3))
	s_card.add_child(pill_panel)

	var b_lbl: Label = _make_label("SocketBadge", default_badge, 11, COL_BODY_IVORY, HORIZONTAL_ALIGNMENT_CENTER)
	b_lbl.position = Vector2.ZERO
	b_lbl.size = Vector2(36.0, 18.0)
	pill_panel.add_child(b_lbl)

	if slot_idx >= 0:
		_equip_slot_icons.append(icon_rect)
		_equip_slot_badges.append(b_lbl)
		_equip_slot_pill_panels.append(pill_panel)
		_equip_slot_check_badges.append(chk_panel)
		var t_lbl: Label = _make_label("SlotTitle_%d" % slot_idx, default_slot_type, 11, COL_HEADER_GOLD, HORIZONTAL_ALIGNMENT_LEFT)
		t_lbl.visible = false
		s_card.add_child(t_lbl)
		_equip_slot_titles.append(t_lbl)
		var sub_lbl: Label = _make_label("SlotSub_%d" % slot_idx, "", 11, COL_BODY_IVORY, HORIZONTAL_ALIGNMENT_LEFT)
		sub_lbl.visible = false
		s_card.add_child(sub_lbl)
		_equip_slot_subs.append(sub_lbl)
	else:
		_aux_relic_socket_icon = icon_rect
		_aux_relic_socket_badge = b_lbl
		_aux_relic_pill_panel = pill_panel
		_aux_relic_check_badge = chk_panel
	return s_card


func _build_field_character_tab1_controls() -> void:
	# 1. UPPER PAPER-DOLL STAGE CONTAINER (Left 5-Socket Strip + Inner-Right 3-Socket Strip)
	_field_left_equip_container = Control.new()
	_field_left_equip_container.name = "FieldLeftEquipContainer"
	_field_left_equip_container.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tab1_container.add_child(_field_left_equip_container)

	_left_armor_vbox = VBoxContainer.new()
	_left_armor_vbox.name = "LeftArmorStripVBox"
	_left_armor_vbox.alignment = BoxContainer.ALIGNMENT_CENTER
	_left_armor_vbox.add_theme_constant_override("separation", 6)
	_left_armor_vbox.mouse_filter = Control.MOUSE_FILTER_PASS
	_field_left_equip_container.add_child(_left_armor_vbox)

	_aux_right_vbox = VBoxContainer.new()
	_aux_right_vbox.name = "InnerRightAuxStripVBox"
	_aux_right_vbox.alignment = BoxContainer.ALIGNMENT_CENTER
	_aux_right_vbox.add_theme_constant_override("separation", 10)
	_aux_right_vbox.mouse_filter = Control.MOUSE_FILTER_PASS
	_field_left_equip_container.add_child(_aux_right_vbox)

	_equip_slot_cards.clear()
	_equip_slot_icons.clear()
	_equip_slot_titles.clear()
	_equip_slot_subs.clear()
	_equip_slot_badges.clear()
	_equip_slot_pill_panels.clear()
	_equip_slot_check_badges.clear()

	var armor_slot_types: Array[String] = ["HEAD", "CHEST", "HANDS", "LEGS", "FEET"]
	for s_idx: int in range(5):
		var sock: Panel = _create_paperdoll_socket("EquipSlotCard_%d" % s_idx, s_idx, armor_slot_types[s_idx], "+6")
		_left_armor_vbox.add_child(sock)
		_equip_slot_cards.append(sock)

	# Create Firearm (idx 5) and Spell (idx 6) sockets + Relic Curio socket for Inner-Right Auxiliary Strip
	var firearm_sock: Panel = _create_paperdoll_socket("EquipSlotCard_5", 5, "FIREARM", "38")
	_equip_slot_cards.append(firearm_sock)
	var spell_sock: Panel = _create_paperdoll_socket("EquipSlotCard_6", 6, "SPELL", "[F]")
	_equip_slot_cards.append(spell_sock)
	_aux_relic_socket_card = _create_paperdoll_socket("AuxRelicSocketCard", -1, "RELIC", "✦")
	_aux_relic_socket_card.mouse_entered.connect(func() -> void: _on_aux_relic_socket_hovered())
	_aux_relic_socket_card.mouse_exited.connect(func() -> void: _hide_floating_tooltip())
	_aux_relic_socket_card.gui_input.connect(func(ev: InputEvent) -> void:
		if ev is InputEventMouseButton:
			var mb: InputEventMouseButton = ev as InputEventMouseButton
			if mb.button_index == MOUSE_BUTTON_LEFT and mb.pressed:
				_on_inventory_filter_selected("RELICS", "")
	)
	# Stack order in Inner-Right Auxiliary Strip: 1. Lantern/Spell, 2. Relic Curio, 3. Active Firearm
	_aux_right_vbox.add_child(spell_sock)
	_aux_right_vbox.add_child(_aux_relic_socket_card)
	_aux_right_vbox.add_child(firearm_sock)

	_set_synergy_label = _make_label("SetSynergyFooterLabel", "5/5 Active (+25%)", 12, COL_STAT_EMERALD, HORIZONTAL_ALIGNMENT_CENTER)
	_set_synergy_label.visible = false
	_field_left_equip_container.add_child(_set_synergy_label)

	# 2. FAR-RIGHT VERTICAL STAT PILLAR (Fixed 230px width, #121417 background)
	_build_stat_pillar_controls()

	# Keep hidden legacy summary panel for non-breaking references
	_field_center_summary_panel = Panel.new()
	_field_center_summary_panel.name = "FieldCenterSummaryPanel"
	_field_center_summary_panel.visible = false
	_center_nave_panel.add_child(_field_center_summary_panel)
	_field_summary_labels.clear()
	for r_i: int in range(5):
		var s_lbl: Label = _make_label("CenterSummaryRow_%d" % r_i, "", 12, COL_BODY_IVORY, HORIZONTAL_ALIGNMENT_LEFT)
		_field_center_summary_panel.add_child(s_lbl)
		_field_summary_labels.append(s_lbl)

	# 3. LOWER ZONE (38% HEIGHT): TABBED 2D ICON STASH GRID
	_build_lower_stash_grid_controls()

	# 4. FLOATING HOVER TOOLTIP (ItemInspectorTooltip at z_index = 50)
	_build_floating_tooltip_control()


func _build_stat_pillar_controls() -> void:
	_stat_pillar_panel = PanelContainer.new()
	_stat_pillar_panel.name = "FarRightStatPillar"
	_stat_pillar_panel.custom_minimum_size = Vector2(230.0, 0.0)
	_stat_pillar_panel.mouse_filter = Control.MOUSE_FILTER_PASS
	var pillar_sb: StyleBoxFlat = _make_stylebox(Color.html("#121417"), Color.html("#8c734b"), 2, 4)
	pillar_sb.content_margin_left = 10.0
	pillar_sb.content_margin_right = 10.0
	pillar_sb.content_margin_top = 8.0
	pillar_sb.content_margin_bottom = 8.0
	_stat_pillar_panel.add_theme_stylebox_override("panel", pillar_sb)
	tab1_container.add_child(_stat_pillar_panel)

	var pillar_vbox: VBoxContainer = VBoxContainer.new()
	pillar_vbox.name = "StatPillarVBox"
	pillar_vbox.add_theme_constant_override("separation", 5)
	_stat_pillar_panel.add_child(pillar_vbox)

	# Top Header: Crimson Ribbon Banner (#5e1919) with LEVEL 1 and bevelled gold XP progress bar underneath
	var banner_panel: PanelContainer = PanelContainer.new()
	banner_panel.name = "PillarLevelBanner"
	var ban_sb: StyleBoxFlat = _make_stylebox(Color.html("#5e1919"), Color.html("#b8924a"), 2, 3)
	ban_sb.content_margin_top = 4.0
	ban_sb.content_margin_bottom = 5.0
	ban_sb.content_margin_left = 8.0
	ban_sb.content_margin_right = 8.0
	banner_panel.add_theme_stylebox_override("panel", ban_sb)
	pillar_vbox.add_child(banner_panel)

	var ban_vbox: VBoxContainer = VBoxContainer.new()
	ban_vbox.add_theme_constant_override("separation", 3)
	banner_panel.add_child(ban_vbox)

	_pillar_level_label = _make_label("PillarLevelLabel", "LEVEL 1", 15, COL_HEADER_GOLD, HORIZONTAL_ALIGNMENT_CENTER)
	ban_vbox.add_child(_pillar_level_label)

	_pillar_xp_bar_canvas = Control.new()
	_pillar_xp_bar_canvas.name = "BevelledGoldXPBar"
	_pillar_xp_bar_canvas.custom_minimum_size = Vector2(0.0, 10.0)
	_pillar_xp_bar_canvas.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_pillar_xp_bar_canvas.draw.connect(func() -> void:
		var b_sz: Vector2 = _pillar_xp_bar_canvas.size
		if b_sz.x < 10.0:
			return
		_pillar_xp_bar_canvas.draw_rect(Rect2(Vector2.ZERO, b_sz), Color.html("#141110"), true)
		var fill_w: float = clampf(_pillar_xp_ratio, 0.08, 1.0) * (b_sz.x - 4.0)
		_pillar_xp_bar_canvas.draw_rect(Rect2(Vector2(2.0, 2.0), Vector2(fill_w, b_sz.y - 4.0)), Color.html("#d4a238"), true)
		_pillar_xp_bar_canvas.draw_rect(Rect2(Vector2(2.0, 2.0), Vector2(fill_w, 2.0)), Color.html("#ffe89e"), true)
		_pillar_xp_bar_canvas.draw_rect(Rect2(Vector2.ZERO, b_sz), Color.html("#b8924a"), false, 1.4)
	)
	ban_vbox.add_child(_pillar_xp_bar_canvas)

	_pillar_xp_label = _make_label("PillarXPLabel", "XP: 0 / 100", 10, COL_BODY_IVORY, HORIZONTAL_ALIGNMENT_CENTER)
	ban_vbox.add_child(_pillar_xp_label)

	# 4 Circular 44x44 Forged-Iron Medallions (Attack/Crit, 60 ARM, 183 Vitality, Core) + Dark Recessed Value Bars
	_pillar_medallion_titles.clear()
	_pillar_medallion_vals.clear()
	var med_defs: Array[Dictionary] = [
		{"symbol": "⚔", "title": "Attack / Crit", "val": "108% / 238%", "col": Color.html("#3a1b1d")},
		{"symbol": "🛡", "title": "Defense / Armor", "val": "60 ARM", "col": Color.html("#1b2632")},
		{"symbol": "❤", "title": "Vitality", "val": "183 Vitality", "col": Color.html("#361820")},
		{"symbol": "✦", "title": "Core Resonance", "val": "Silver-Core", "col": Color.html("#292136")}
	]
	for m_i: int in range(med_defs.size()):
		var md: Dictionary = med_defs[m_i]
		var m_hbox: HBoxContainer = HBoxContainer.new()
		m_hbox.add_theme_constant_override("separation", 6)
		pillar_vbox.add_child(m_hbox)

		# 44x44 Circular Forged-Iron Medallion
		var badge_panel: Control = Control.new()
		badge_panel.name = "ForgedIronMedallion_%d" % m_i
		badge_panel.custom_minimum_size = Vector2(44.0, 44.0)
		badge_panel.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		badge_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var core_col: Color = md["col"] as Color
		badge_panel.draw.connect(func() -> void:
			var mc: Vector2 = badge_panel.size * 0.5
			badge_panel.draw_circle(mc, 21.5, Color.html("#1b1d22"))
			badge_panel.draw_arc(mc, 21.0, 0.0, TAU, 32, Color.html("#4a4e58"), 2.2)
			badge_panel.draw_arc(mc, 18.2, 0.0, TAU, 28, Color.html("#8c734b"), 1.6)
			badge_panel.draw_circle(mc, 16.5, core_col)
			for r_ang: float in [0.0, PI * 0.5, PI, PI * 1.5]:
				var r_pt: Vector2 = mc + Vector2(cos(r_ang), sin(r_ang)) * 19.6
				badge_panel.draw_circle(r_pt, 1.5, Color.html("#d4b475"))
		)
		m_hbox.add_child(badge_panel)

		var sym_lbl: Label = _make_label("MedSym_%d" % m_i, String(md["symbol"]), 16, COL_HEADER_GOLD, HORIZONTAL_ALIGNMENT_CENTER)
		sym_lbl.position = Vector2(0.0, 8.0)
		sym_lbl.size = Vector2(44.0, 28.0)
		badge_panel.add_child(sym_lbl)

		# Dark Recessed Value Bar paired with the 44x44 medallion
		var rec_bar: PanelContainer = PanelContainer.new()
		rec_bar.name = "RecessedValueBar_%d" % m_i
		rec_bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		rec_bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		var rec_sb: StyleBoxFlat = _make_stylebox(Color.html("#0a0b0e"), Color.html("#2e2a24"), 1, 3)
		rec_sb.content_margin_left = 7.0
		rec_sb.content_margin_right = 6.0
		rec_sb.content_margin_top = 3.0
		rec_sb.content_margin_bottom = 3.0
		rec_bar.add_theme_stylebox_override("panel", rec_sb)
		m_hbox.add_child(rec_bar)

		var mv_vbox: VBoxContainer = VBoxContainer.new()
		mv_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		mv_vbox.add_theme_constant_override("separation", 0)
		rec_bar.add_child(mv_vbox)

		var mt_lbl: Label = _make_label("MedTitle_%d" % m_i, String(md["title"]), 10, Color.html("#b8afa0"), HORIZONTAL_ALIGNMENT_LEFT)
		mv_vbox.add_child(mt_lbl)
		_pillar_medallion_titles.append(mt_lbl)

		var mval_lbl: Label = _make_label("MedVal_%d" % m_i, String(md["val"]), 12, COL_BODY_IVORY, HORIZONTAL_ALIGNMENT_LEFT)
		mv_vbox.add_child(mval_lbl)
		_pillar_medallion_vals.append(mval_lbl)

	# Horizontal Bronze Divider Line
	var div_line: ColorRect = ColorRect.new()
	div_line.custom_minimum_size = Vector2(0.0, 1.0)
	div_line.color = Color.html("#524229")
	pillar_vbox.add_child(div_line)

	# 3 Compact Affinity Rows (Set Synergy, Quickstep Mobility, Barrel Rite)
	_pillar_affinity_vals.clear()
	var aff_titles: Array[String] = ["Set Synergy", "Quickstep Mobility", "Barrel Rite"]
	var aff_defaults: Array[String] = ["5/5 Active", "122%", "Silver-Core"]
	for a_i: int in range(3):
		var a_hbox: HBoxContainer = HBoxContainer.new()
		pillar_vbox.add_child(a_hbox)
		var at_lbl: Label = _make_label("AffTitle_%d" % a_i, aff_titles[a_i], 11, Color.html("#cfc5b8"), HORIZONTAL_ALIGNMENT_LEFT)
		at_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		a_hbox.add_child(at_lbl)
		var av_lbl: Label = _make_label("AffVal_%d" % a_i, aff_defaults[a_i], 11, COL_STAT_EMERALD if a_i == 0 else COL_STAT_AMBER, HORIZONTAL_ALIGNMENT_RIGHT)
		a_hbox.add_child(av_lbl)
		_pillar_affinity_vals.append(av_lbl)

	var spacer: Control = Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	pillar_vbox.add_child(spacer)

	var bot_div: ColorRect = ColorRect.new()
	bot_div.custom_minimum_size = Vector2(0.0, 1.0)
	bot_div.color = Color.html("#524229")
	pillar_vbox.add_child(bot_div)

	# Bottom Footer of Stat Pillar: Currency Row with explicit 6px bottom margin so it never touches Dev Buttons
	var curr_margin: MarginContainer = MarginContainer.new()
	curr_margin.name = "CurrencyRowMargin"
	curr_margin.add_theme_constant_override("margin_top", 2)
	curr_margin.add_theme_constant_override("margin_bottom", 6)
	pillar_vbox.add_child(curr_margin)

	_pillar_currency_label = _make_label("PillarCurrencyFooter", "35 Silver | 15 Ash | 0 Iron | 0 Core", 11, COL_STAT_AMBER, HORIZONTAL_ALIGNMENT_CENTER)
	_pillar_currency_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	curr_margin.add_child(_pillar_currency_label)

	var dev_hbox: HBoxContainer = HBoxContainer.new()
	dev_hbox.alignment = BoxContainer.ALIGNMENT_CENTER
	dev_hbox.add_theme_constant_override("separation", 4)
	pillar_vbox.add_child(dev_hbox)

	_pillar_dev_buttons.clear()
	var dev_defs: Array[Dictionary] = [
		{"txt": "+2 SP", "cb": Callable(self, "trigger_sanctuary_blessing")},
		{"txt": "Respec", "cb": func() -> void: trigger_respec_rites()},
		{"txt": "+Mats", "cb": Callable(self, "trigger_grant_test_materials")}
	]
	for d_i: int in range(dev_defs.size()):
		var d_btn: Button = _make_gothic_button("PillarDevBtn_%d" % d_i, String(dev_defs[d_i]["txt"]), 11)
		d_btn.custom_minimum_size = Vector2(62.0, 22.0)
		d_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		d_btn.pressed.connect(dev_defs[d_i]["cb"] as Callable)
		dev_hbox.add_child(d_btn)
		_pillar_dev_buttons.append(d_btn)


func _build_lower_stash_grid_controls() -> void:
	_field_right_inv_container = Control.new()
	_field_right_inv_container.name = "LowerStashGridZone"
	_field_right_inv_container.mouse_filter = Control.MOUSE_FILTER_PASS
	tab1_container.add_child(_field_right_inv_container)

	var lower_bg: Panel = Panel.new()
	lower_bg.name = "LowerStashBackdropPanel"
	lower_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	lower_bg.add_theme_stylebox_override("panel", _make_stylebox(Color.html("#090a0d"), Color.html("#8c734b"), 2, 4))
	_field_right_inv_container.add_child(lower_bg)
	_attach_filigree_frame(lower_bg, Color.html("#8c734b"), Color.html("#4d3d26"), 16.0)

	_stash_tab_hbox = HBoxContainer.new()
	_stash_tab_hbox.name = "StashCategoryTabBar"
	_stash_tab_hbox.add_theme_constant_override("separation", 6)
	_field_right_inv_container.add_child(_stash_tab_hbox)

	_inv_filter_buttons.clear()
	var filter_defs: Array[Dictionary] = [
		{"id": "ARMOR", "label": "Equipment"},
		{"id": "WEAPONS", "label": "Arsenal"},
		{"id": "RELICS", "label": "Relics"},
		{"id": "MATERIALS", "label": "Materials"}
	]
	for f_i: int in range(filter_defs.size()):
		var fid: String = String(filter_defs[f_i]["id"])
		var fbtn: Button = _make_gothic_button("InvFilterBtn_" + fid, String(filter_defs[f_i]["label"]), 14)
		fbtn.custom_minimum_size = Vector2(168.0, 30.0)
		fbtn.pressed.connect(func() -> void: _on_inventory_filter_selected(fid, ""))
		_stash_tab_hbox.add_child(fbtn)
		_inv_filter_buttons.append(fbtn)

	_inv_scroll = ScrollContainer.new()
	_inv_scroll.name = "InventoryScrollContainer"
	_inv_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_field_right_inv_container.add_child(_inv_scroll)

	_stash_grid = GridContainer.new()
	_stash_grid.name = "StashTileGridContainer"
	_stash_grid.columns = 10
	_stash_grid.add_theme_constant_override("h_separation", 6)
	_stash_grid.add_theme_constant_override("v_separation", 6)
	_inv_scroll.add_child(_stash_grid)

	# Keep hidden legacy VBox & active Lower-Right Reliquary Item Inspector with weathered double-line bronze border & filigree brackets
	_inv_vbox = VBoxContainer.new()
	_inv_vbox.visible = false
	_field_right_inv_container.add_child(_inv_vbox)
	_inv_inspector_panel = Panel.new()
	_inv_inspector_panel.name = "LowerRightItemLedgerPanel"
	_inv_inspector_panel.add_theme_stylebox_override("panel", _make_stylebox(Color.html("#121417"), Color.html("#8c734b"), 2, 4))
	_field_right_inv_container.add_child(_inv_inspector_panel)
	_attach_filigree_frame(_inv_inspector_panel, Color.html("#8c734b"), Color.html("#4d3d26"), 18.0)
	_inv_inspector_title = _make_label("InvInspectorTitle", "❖ RELIQUARY ITEM & SET SYNERGY LEDGER", 14, COL_HEADER_GOLD, HORIZONTAL_ALIGNMENT_LEFT)
	_inv_inspector_panel.add_child(_inv_inspector_title)
	_inv_inspector_body = _make_label("InvInspectorBody", "", 13, COL_BODY_IVORY, HORIZONTAL_ALIGNMENT_LEFT)
	_inv_inspector_body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_inv_inspector_panel.add_child(_inv_inspector_body)


func _build_floating_tooltip_control() -> void:
	_floating_tooltip = PanelContainer.new()
	_floating_tooltip.name = "ItemInspectorTooltip"
	_floating_tooltip.z_index = 50
	_floating_tooltip.visible = false
	_floating_tooltip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_floating_tooltip.custom_minimum_size = Vector2(310.0, 0.0)
	var tt_sb: StyleBoxFlat = _make_stylebox(Color(0.05, 0.055, 0.07, 0.98), Color.html("#b8924a"), 2, 4)
	tt_sb.content_margin_left = 12.0
	tt_sb.content_margin_right = 12.0
	tt_sb.content_margin_top = 10.0
	tt_sb.content_margin_bottom = 10.0
	_floating_tooltip.add_theme_stylebox_override("panel", tt_sb)
	add_child(_floating_tooltip)

	var tt_vbox: VBoxContainer = VBoxContainer.new()
	tt_vbox.add_theme_constant_override("separation", 6)
	tt_vbox.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_floating_tooltip.add_child(tt_vbox)

	var top_hbox: HBoxContainer = HBoxContainer.new()
	top_hbox.add_theme_constant_override("separation", 10)
	top_hbox.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tt_vbox.add_child(top_hbox)

	_tooltip_icon = TextureRect.new()
	_tooltip_icon.custom_minimum_size = Vector2(56.0, 56.0)
	_tooltip_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_tooltip_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_tooltip_icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	top_hbox.add_child(_tooltip_icon)

	var hdr_vbox: VBoxContainer = VBoxContainer.new()
	hdr_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hdr_vbox.add_theme_constant_override("separation", 2)
	hdr_vbox.mouse_filter = Control.MOUSE_FILTER_IGNORE
	top_hbox.add_child(hdr_vbox)

	_tooltip_title_label = _make_label("TooltipItemTitle", "Item Name", 15, COL_HEADER_GOLD, HORIZONTAL_ALIGNMENT_LEFT)
	_tooltip_title_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	hdr_vbox.add_child(_tooltip_title_label)

	_tooltip_tier_label = _make_label("TooltipItemTier", "Set Tier", 12, Color.html("#cfc5b8"), HORIZONTAL_ALIGNMENT_LEFT)
	hdr_vbox.add_child(_tooltip_tier_label)

	_tooltip_primary_stat_label = _make_label("TooltipPrimaryStat", "+6 ARMOR", 18, COL_BODY_IVORY, HORIZONTAL_ALIGNMENT_LEFT)
	hdr_vbox.add_child(_tooltip_primary_stat_label)

	var tt_div: ColorRect = ColorRect.new()
	tt_div.custom_minimum_size = Vector2(0.0, 1.0)
	tt_div.color = Color.html("#3d352b")
	tt_div.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tt_vbox.add_child(tt_div)

	_tooltip_substats_label = _make_label("TooltipSubStats", "", 13, COL_STAT_EMERALD, HORIZONTAL_ALIGNMENT_LEFT)
	_tooltip_substats_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tt_vbox.add_child(_tooltip_substats_label)

	_tooltip_synergy_label = _make_label("TooltipSynergy", "", 12, COL_STAT_AMBER, HORIZONTAL_ALIGNMENT_LEFT)
	_tooltip_synergy_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tt_vbox.add_child(_tooltip_synergy_label)

	_tooltip_hint_label = _make_label("TooltipHint", "Click to Equip", 12, Color.html("#c4ccd9"), HORIZONTAL_ALIGNMENT_RIGHT)
	tt_vbox.add_child(_tooltip_hint_label)


func _build_field_character_tab() -> void:
	_build_field_character_tab1_controls()


func _build_armorer_stand_mode() -> void:
	_build_armorer_stand_controls()


func _build_armorer_stand_controls() -> void:
	_armorer_left_container = Control.new()
	_armorer_left_container.name = "ArmorerLeftContainer"
	_armorer_left_container.mouse_filter = Control.MOUSE_FILTER_PASS
	_armorer_left_container.visible = false
	_left_wing_panel.add_child(_armorer_left_container)

	_armorer_set_tab_buttons.clear()
	var set_tab_titles: Array[String] = [
		"I. Grave-Stalker [5/5]",
		"II. Inquisitor [0/5]",
		"III. Juggernaut [0/5]",
		"IV. Abyssal [0/5]"
	]
	for set_i: int in range(4):
		var cap_set: int = set_i
		var st_btn: Button = _make_gothic_button("ArmorerSetTab_%d" % set_i, set_tab_titles[set_i], 11)
		st_btn.clip_text = true
		st_btn.pressed.connect(func() -> void: _on_armorer_set_tab_selected(cap_set))
		_armorer_left_container.add_child(st_btn)
		_armorer_set_tab_buttons.append(st_btn)

	_armorer_piece_cards.clear()
	_armorer_piece_titles.clear()
	_armorer_piece_subs.clear()
	_armorer_piece_buttons.clear()

	for p_i: int in range(5):
		var cap_slot_idx: int = p_i
		var p_card: Panel = Panel.new()
		p_card.name = "ArmorerPieceCard_%d" % p_i
		p_card.mouse_filter = Control.MOUSE_FILTER_PASS
		p_card.add_theme_stylebox_override("panel", _make_stylebox(COL_CARD_BG, COL_CARD_BORDER, 2, 4))
		p_card.mouse_entered.connect(func() -> void: _on_armorer_piece_hovered(cap_slot_idx))
		p_card.gui_input.connect(func(ev: InputEvent) -> void:
			if ev is InputEventMouseButton:
				var mb: InputEventMouseButton = ev as InputEventMouseButton
				if mb.button_index == MOUSE_BUTTON_LEFT and mb.pressed:
					_on_armorer_piece_hovered(cap_slot_idx)
		)
		_armorer_left_container.add_child(p_card)
		_armorer_piece_cards.append(p_card)

		var pt_lbl: Label = _make_label("PieceTitle_%d" % p_i, "[HEAD] Piece", 15, COL_HEADER_GOLD, HORIZONTAL_ALIGNMENT_LEFT)
		p_card.add_child(pt_lbl)
		_armorer_piece_titles.append(pt_lbl)

		var ps_lbl: Label = _make_label("PieceSub_%d" % p_i, "+6 ARM  |  Bonus", 13, COL_BODY_IVORY, HORIZONTAL_ALIGNMENT_LEFT)
		ps_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		p_card.add_child(ps_lbl)
		_armorer_piece_subs.append(ps_lbl)

		var pb_btn: Button = _make_gothic_button("PieceForgeBtn_%d" % p_i, "[ ⚒ FORGE PIECE ]", 13)
		pb_btn.mouse_entered.connect(func() -> void: _on_armorer_piece_hovered(cap_slot_idx))
		pb_btn.pressed.connect(func() -> void: _on_armorer_piece_action_pressed(cap_slot_idx))
		p_card.add_child(pb_btn)
		_armorer_piece_buttons.append(pb_btn)

	_armorer_preview_toggle_btn = _make_gothic_button("ArmorerPreviewFullSetBtn", "[ PREVIEW FULL SET ]", 14)
	_armorer_preview_toggle_btn.visible = false
	_armorer_preview_toggle_btn.pressed.connect(func() -> void:
		_armorer_preview_full_set = not _armorer_preview_full_set
		_play_ui_sfx(_sfx_tab_turn)
		_refresh_armorer_3d_preview()
		_refresh_all_ui_elements()
	)
	_center_nave_panel.add_child(_armorer_preview_toggle_btn)

	_armorer_comparison_header = _make_label(
		"ArmorerComparisonHeaderLabel",
		"✦ SLOT COMPARISON: [HEAD] WORN VS CANDIDATE",
		14,
		COL_STAT_EMERALD,
		HORIZONTAL_ALIGNMENT_LEFT
	)
	_armorer_comparison_header.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_armorer_comparison_header.visible = false
	_right_wing_panel.add_child(_armorer_comparison_header)


func _build_tab2_controls() -> void:
	_astrolabe_map_panel = Panel.new()
	_astrolabe_map_panel.name = "AstrolabeStarMapPanel"
	_astrolabe_map_panel.mouse_filter = Control.MOUSE_FILTER_PASS
	_astrolabe_map_panel.modulate = Color(1.0, 1.0, 1.0, 1.0)
	_astrolabe_map_panel.self_modulate = Color(1.0, 1.0, 1.0, 1.0)
	_astrolabe_map_panel.add_theme_stylebox_override("panel", _make_stylebox(Color(0.09, 0.08, 0.13, 0.98), COL_CARD_BORDER, 2, 5))
	tab2_container.add_child(_astrolabe_map_panel)

	_astrolabe_conduit_canvas = Control.new()
	_astrolabe_conduit_canvas.name = "AstrolabeConduitCanvas"
	_astrolabe_conduit_canvas.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_astrolabe_conduit_canvas.draw.connect(_on_astrolabe_conduit_canvas_draw)
	_astrolabe_map_panel.add_child(_astrolabe_conduit_canvas)

	_constellation_header_labels.clear()
	var col_titles: Array[String] = [
		"I. CRIMSON BLOODLUST",
		"II. QUICKSILVER PHANTOM",
		"III. IRONCLAD BULWARK",
		"IV. ELDRITCH RELIQUARY"
	]
	for c_i: int in range(4):
		var c_lbl: Label = _make_label("ConstellationHeader_%d" % c_i, col_titles[c_i], 20, COL_HEADER_GOLD, HORIZONTAL_ALIGNMENT_CENTER)
		_astrolabe_map_panel.add_child(c_lbl)
		_constellation_header_labels.append(c_lbl)

	_skill_node_buttons.clear()
	_skill_tier_labels.clear()
	var catalog: Dictionary[String, Dictionary] = PlayerLoadoutManager.get_skill_tree_catalog()
	var node_ids: Array[String] = PlayerLoadoutManager.get_skill_node_ids()
	var romans: Array[String] = ["I", "I", "II", "III", "IV"]

	for sid: String in node_ids:
		var info: Dictionary = catalog[sid]
		var tier: int = int(info.get("tier", 1))
		var const_idx: int = int(info.get("constellation", 0))
		var badge_txt: String = "SYN" if const_idx == 4 else romans[clampi(tier, 1, 4)]
		var node_id: String = sid

		var s_btn: Button = _make_gothic_button("SkillNodeBtn_" + sid, badge_txt, 16)
		s_btn.mouse_entered.connect(func() -> void:
			hovered_skill_id = node_id
			_refresh_all_ui_elements()
		)
		s_btn.pressed.connect(func() -> void: _on_skill_node_button_pressed(node_id))
		_astrolabe_map_panel.add_child(s_btn)
		_skill_node_buttons[sid] = s_btn

		var short_title: String = String(info.get("title", sid))
		var st_lbl: Label = _make_label("SkillNodeTitle_" + sid, short_title, 16, COL_BODY_IVORY, HORIZONTAL_ALIGNMENT_CENTER)
		_astrolabe_map_panel.add_child(st_lbl)
		_skill_tier_labels[sid] = st_lbl

	# Bottom Grimoire Inscription Plaque
	_inscription_plaque_panel = Panel.new()
	_inscription_plaque_panel.name = "GrimoireInscriptionPanel"
	_inscription_plaque_panel.mouse_filter = Control.MOUSE_FILTER_PASS
	_inscription_plaque_panel.modulate = Color(1.0, 1.0, 1.0, 1.0)
	_inscription_plaque_panel.self_modulate = Color(1.0, 1.0, 1.0, 1.0)
	_inscription_plaque_panel.add_theme_stylebox_override("panel", _make_stylebox(COL_CARD_BG, COL_CARD_BORDER_ACTIVE, 2, 5))
	tab2_container.add_child(_inscription_plaque_panel)

	_skill_title_label = _make_label("InscriptionTitleLabel", "❖ RITE OF CRIMSON BLOODLUST ❖", 22, COL_HEADER_GOLD, HORIZONTAL_ALIGNMENT_LEFT)
	_inscription_plaque_panel.add_child(_skill_title_label)

	_skill_lore_label = _make_label("InscriptionLoreLabel", "\"By blood consecrated, the hunter's aim never wavers.\"", 16, COL_BODY_IVORY, HORIZONTAL_ALIGNMENT_LEFT)
	_inscription_plaque_panel.add_child(_skill_lore_label)

	_skill_effect_label = _make_label("InscriptionEffectLabel", "SANCTIFIED EFFECT: +12% Firearm Damage.", 17, COL_STAT_EMERALD, HORIZONTAL_ALIGNMENT_LEFT)
	_inscription_plaque_panel.add_child(_skill_effect_label)

	_skill_prereq_label = _make_label("InscriptionPrereqLabel", "PREREQUISITE RITES: None  |  COST: 1 SOUL POINT (SP)", 16, COL_STAT_AMBER, HORIZONTAL_ALIGNMENT_LEFT)
	_inscription_plaque_panel.add_child(_skill_prereq_label)

	_consecrate_rite_button = _make_gothic_button("ConsecrateRiteButton", "[ ❖ CONSECRATE RITE (1 SP) ❖ ]", 18)
	_consecrate_rite_button.pressed.connect(func() -> void: consecrate_selected_skill())
	_inscription_plaque_panel.add_child(_consecrate_rite_button)


# ==============================================================================================
# 3D RELIQUARY PEDESTAL SUBVIEWPORT (Phase 2.3: Bright WorldEnvironment + 2 Strong OmniLight3Ds)
# ==============================================================================================
func _build_3d_reliquary_pedestal() -> void:
	sub_viewport_container = SubViewportContainer.new()
	sub_viewport_container.name = "ReliquaryPedestalViewportContainer"
	sub_viewport_container.stretch = true
	sub_viewport_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sub_viewport_container.size_flags_stretch_ratio = 1.35
	sub_viewport_container.size = PEDESTAL_VIEWPORT_SIZE
	sub_viewport_container.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_center_nave_panel.add_child(sub_viewport_container)

	sub_viewport = SubViewport.new()
	sub_viewport.name = "ReliquarySubViewport"
	sub_viewport.own_world_3d = true
	sub_viewport.transparent_bg = true
	sub_viewport.size = Vector2i(int(PEDESTAL_VIEWPORT_SIZE.x), int(PEDESTAL_VIEWPORT_SIZE.y))
	sub_viewport.render_target_update_mode = SubViewport.UPDATE_WHEN_VISIBLE
	sub_viewport.msaa_3d = Viewport.MSAA_2X
	sub_viewport_container.add_child(sub_viewport)

	var stage_root: Node3D = Node3D.new()
	stage_root.name = "ReliquaryStage3D"
	sub_viewport.add_child(stage_root)

	# Isolated Armory WorldEnvironment (AgX Tonemapper, Neutral Studio Ambient + Warm Golden Rim Contrast)
	var env: Environment = Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.035, 0.035, 0.045, 0.0)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color.html("#4a525e")
	env.ambient_light_energy = 1.45
	env.tonemap_mode = Environment.TONE_MAPPER_AGX
	env.glow_enabled = true
	env.glow_strength = 0.72
	env.glow_bloom = 0.08
	env.glow_hdr_threshold = 1.25
	env.ssao_enabled = true
	var world_env: WorldEnvironment = WorldEnvironment.new()
	world_env.name = "PedestalWorldEnv"
	world_env.environment = env
	stage_root.add_child(world_env)

	# Camera3D framing the PedestalPivot or Full-Body HunterPaperDollRig
	var cam: Camera3D = Camera3D.new()
	cam.name = "PedestalCamera3D"
	cam.fov = 43.0
	cam.near = 0.05
	cam.far = 25.0
	cam.position = Vector3(0.0, 1.05, 2.55)
	cam.look_at_from_position(Vector3(0.0, 1.05, 2.55), Vector3(0.0, 0.90, 0.0), Vector3.UP)
	cam.current = true
	stage_root.add_child(cam)
	pedestal_camera = cam

	# Crisp Neutral-Cool Front Key + Warm Gold/Orange Rim & Dais Edge-Highlight Rig
	var key_light: OmniLight3D = OmniLight3D.new()
	key_light.name = "AmberKeyLight"
	key_light.position = Vector3(-1.35, 1.55, 1.85)
	key_light.light_color = Color.html("#eef2f7")
	key_light.light_energy = 2.15
	key_light.omni_range = 8.0
	key_light.omni_attenuation = 1.0
	stage_root.add_child(key_light)

	var rim_omni: OmniLight3D = OmniLight3D.new()
	rim_omni.name = "WarmGoldRimLight"
	rim_omni.position = Vector3(1.35, 1.65, -1.15)
	rim_omni.light_color = Color.html("#ffaa33")
	rim_omni.light_energy = 3.1
	rim_omni.omni_range = 8.0
	rim_omni.omni_attenuation = 1.0
	stage_root.add_child(rim_omni)

	var fill_light: OmniLight3D = OmniLight3D.new()
	fill_light.name = "GothicFillLight"
	fill_light.position = Vector3(-1.20, 0.45, -0.85)
	fill_light.light_color = Color.html("#ff8822")
	fill_light.light_energy = 2.2
	fill_light.omni_range = 5.5
	fill_light.omni_attenuation = 1.0
	stage_root.add_child(fill_light)

	var front_fill_light: OmniLight3D = OmniLight3D.new()
	front_fill_light.name = "GothicFrontFillLight"
	front_fill_light.position = Vector3(0.95, 1.25, 1.95)
	front_fill_light.light_color = Color.html("#dce4f0")
	front_fill_light.light_energy = 1.15
	front_fill_light.omni_range = 5.5
	front_fill_light.omni_attenuation = 1.0
	stage_root.add_child(front_fill_light)

	# Rotating PedestalPivot with Circular Stone Reliquary Dais, Golden Rim-Light Ring, Candles & Fog
	pedestal_pivot = Node3D.new()
	pedestal_pivot.name = "PedestalPivot"
	stage_root.add_child(pedestal_pivot)

	pedestal_plinth_mesh = MeshInstance3D.new()
	pedestal_plinth_mesh.name = "OctagonalStonePlinth"
	var cyl: CylinderMesh = CylinderMesh.new()
	cyl.top_radius = 0.58
	cyl.bottom_radius = 0.68
	cyl.height = 0.14
	cyl.radial_segments = 32
	cyl.rings = 1
	var plinth_mat: StandardMaterial3D = StandardMaterial3D.new()
	plinth_mat.albedo_color = Color.html("#221f1d")
	plinth_mat.roughness = 0.88
	plinth_mat.metallic = 0.12
	cyl.material = plinth_mat
	pedestal_plinth_mesh.mesh = cyl
	pedestal_plinth_mesh.position = Vector3(0.0, -0.06, 0.0)
	pedestal_pivot.add_child(pedestal_plinth_mesh)

	var brass_ring: MeshInstance3D = MeshInstance3D.new()
	brass_ring.name = "PlinthBrassRing"
	var ring_torus: TorusMesh = TorusMesh.new()
	ring_torus.inner_radius = 0.55
	ring_torus.outer_radius = 0.585
	ring_torus.rings = 32
	ring_torus.ring_segments = 16
	var brass_mat: StandardMaterial3D = StandardMaterial3D.new()
	brass_mat.albedo_color = Color.html("#d49b3b")
	brass_mat.metallic = 0.85
	brass_mat.roughness = 0.32
	brass_mat.emission_enabled = true
	brass_mat.emission = Color.html("#ff9922")
	brass_mat.emission_energy_multiplier = 1.35
	ring_torus.material = brass_mat
	brass_ring.mesh = ring_torus
	brass_ring.position = Vector3(0.0, 0.012, 0.0)
	pedestal_pivot.add_child(brass_ring)

	_build_dais_candles_and_fog()

	paperdoll_rig = HunterPaperDollRig.new()
	paperdoll_rig.name = "HunterPaperDollRig"
	if paperdoll_rig.studio_lighting_root != null:
		paperdoll_rig.studio_lighting_root.visible = false
	if paperdoll_rig.plinth_root != null:
		paperdoll_rig.plinth_root.visible = false
	pedestal_pivot.add_child(paperdoll_rig)


func _build_dais_candles_and_fog() -> void:
	_dais_assembly_root = Node3D.new()
	_dais_assembly_root.name = "LitReliquaryDaisAssembly"
	pedestal_pivot.add_child(_dais_assembly_root)
	_dais_candle_lights.clear()

	# Upper carved stone circular step beneath Hunter's boots
	var upper_stone: MeshInstance3D = MeshInstance3D.new()
	upper_stone.name = "DaisCarvedUpperStone"
	var up_cyl: CylinderMesh = CylinderMesh.new()
	up_cyl.top_radius = 0.50
	up_cyl.bottom_radius = 0.54
	up_cyl.height = 0.05
	up_cyl.radial_segments = 32
	var up_mat: StandardMaterial3D = StandardMaterial3D.new()
	up_mat.albedo_color = Color.html("#2c2825")
	up_mat.roughness = 0.86
	up_mat.metallic = 0.10
	up_cyl.material = up_mat
	upper_stone.mesh = up_cyl
	upper_stone.position = Vector3(0.0, -0.01, 0.0)
	_dais_assembly_root.add_child(upper_stone)

	var wax_mat: StandardMaterial3D = StandardMaterial3D.new()
	wax_mat.albedo_color = Color.html("#cbb894")
	wax_mat.roughness = 0.76
	var flame_mat: StandardMaterial3D = StandardMaterial3D.new()
	flame_mat.albedo_color = Color.html("#ffcc55")
	flame_mat.emission_enabled = true
	flame_mat.emission = Color.html("#ff7711")
	flame_mat.emission_energy_multiplier = 2.4

	var cluster_anchors: Array[Vector3] = [
		Vector3(-0.46, 0.02, 0.24),
		Vector3(0.46, 0.02, 0.24),
		Vector3(-0.38, 0.02, -0.34),
		Vector3(0.38, 0.02, -0.34)
	]
	var candle_offsets: Array[Vector3] = [
		Vector3(0.0, 0.0, 0.0),
		Vector3(0.045, 0.0, 0.03),
		Vector3(-0.04, 0.0, 0.035)
	]
	var candle_heights: Array[float] = [0.13, 0.09, 0.07]

	for c_i: int in range(cluster_anchors.size()):
		var anchor: Vector3 = cluster_anchors[c_i]
		for k_i: int in range(3):
			var c_h: float = candle_heights[k_i]
			var c_pos: Vector3 = anchor + candle_offsets[k_i]
			var c_mesh_inst: MeshInstance3D = MeshInstance3D.new()
			var c_cyl: CylinderMesh = CylinderMesh.new()
			c_cyl.top_radius = 0.016
			c_cyl.bottom_radius = 0.019
			c_cyl.height = c_h
			c_cyl.radial_segments = 10
			c_cyl.material = wax_mat
			c_mesh_inst.mesh = c_cyl
			c_mesh_inst.position = c_pos + Vector3(0.0, c_h * 0.5, 0.0)
			_dais_assembly_root.add_child(c_mesh_inst)

			var f_inst: MeshInstance3D = MeshInstance3D.new()
			var f_sph: SphereMesh = SphereMesh.new()
			f_sph.radius = 0.012
			f_sph.height = 0.032
			f_sph.material = flame_mat
			f_inst.mesh = f_sph
			f_inst.position = c_pos + Vector3(0.0, c_h + 0.016, 0.0)
			_dais_assembly_root.add_child(f_inst)

		var c_light: OmniLight3D = OmniLight3D.new()
		c_light.name = "DaisCandleLight_%d" % c_i
		c_light.position = anchor + Vector3(0.0, 0.22, 0.04)
		c_light.light_color = Color.html("#ff9436")
		c_light.light_energy = 1.55
		c_light.omni_range = 1.65
		_dais_assembly_root.add_child(c_light)
		_dais_candle_lights.append(c_light)

	# Ground Fog Particles swirling across the stone circular pedestal
	var fog_particles: CPUParticles3D = CPUParticles3D.new()
	fog_particles.name = "DaisGroundFogParticles"
	fog_particles.position = Vector3(0.0, 0.06, 0.08)
	fog_particles.amount = 24
	fog_particles.lifetime = 3.2
	fog_particles.preprocess = 2.0
	fog_particles.explosiveness = 0.0
	fog_particles.emission_shape = CPUParticles3D.EMISSION_SHAPE_RING
	fog_particles.emission_ring_axis = Vector3.UP
	fog_particles.emission_ring_radius = 0.52
	fog_particles.emission_ring_inner_radius = 0.18
	fog_particles.emission_ring_height = 0.06
	fog_particles.direction = Vector3(0.0, 1.0, 0.0)
	fog_particles.spread = 75.0
	fog_particles.gravity = Vector3(0.0, 0.02, 0.0)
	fog_particles.initial_velocity_min = 0.02
	fog_particles.initial_velocity_max = 0.06
	var fog_quad: QuadMesh = QuadMesh.new()
	fog_quad.size = Vector2(0.36, 0.20)
	var fog_mat: StandardMaterial3D = StandardMaterial3D.new()
	fog_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	fog_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	fog_mat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	fog_mat.albedo_color = Color(0.86, 0.68, 0.44, 0.13)
	fog_quad.material = fog_mat
	fog_particles.mesh = fog_quad
	_dais_assembly_root.add_child(fog_particles)


# ==============================================================================================
# DYNAMIC VIEWPORT-RELATIVE SIZING (Phase 1.2: 86% of Viewport Width & Height, Centered at 7%)
# ==============================================================================================
func _get_viewport_size() -> Vector2:
	if DisplayServer.get_name() == "headless":
		return BASE_REFERENCE_SIZE
	var vp: Vector2 = get_viewport_rect().size if is_inside_tree() else BASE_REFERENCE_SIZE
	if vp.x < 100.0 or vp.y < 100.0:
		vp = BASE_REFERENCE_SIZE
	return vp


func _update_subviewport_layout(force_layout: bool = false) -> void:
	var vp_size: Vector2 = _get_viewport_size()
	if not force_layout and vp_size.is_equal_approx(_last_layout_vp_size) and main_codex_panel != null and main_codex_panel.size.x > 100.0:
		if sub_viewport_container != null:
			sub_viewport_container.visible = is_menu_open and (active_tab == 0)
		return
	_last_layout_vp_size = vp_size

	var codex_size: Vector2 = Vector2(vp_size.x * 0.86, vp_size.y * 0.86)
	var codex_pos: Vector2 = vp_size * 0.07

	if dim_backdrop != null:
		dim_backdrop.position = Vector2.ZERO
		dim_backdrop.size = vp_size
		dim_backdrop.visible = is_menu_open
		if dim_backdrop.get_index() != 0:
			move_child(dim_backdrop, 0)

	if main_codex_panel != null:
		main_codex_panel.position = codex_pos
		main_codex_panel.size = codex_size
		main_codex_panel.visible = is_menu_open

	if bg_decor_canvas != null:
		bg_decor_canvas.position = Vector2.ZERO
		bg_decor_canvas.size = codex_size

	if vfx_overlay_canvas != null:
		vfx_overlay_canvas.position = Vector2.ZERO
		vfx_overlay_canvas.size = vp_size

	# Header Layout (Centered Gothic Nameplate at top, Tab Bar underneath)
	var hdr_pos: Vector2 = codex_pos + Vector2(18.0, 14.0)
	var hdr_size: Vector2 = Vector2(codex_size.x - 36.0, HEADER_HEIGHT)
	if header_container != null:
		header_container.position = hdr_pos
		header_container.size = hdr_size
		header_container.visible = is_menu_open
	if _header_filigree_canvas != null:
		_header_filigree_canvas.queue_redraw()

	var is_diablo_tab1: bool = (current_menu_mode == MODE_FIELD_CHARACTER and active_tab == 0)
	if _header_title_label != null:
		_header_title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		_header_title_label.position = Vector2(floorf(hdr_size.x * 0.5 - 185.0), 5.0)
		_header_title_label.size = Vector2(370.0, 32.0)
	if _header_xp_res_label != null:
		_header_xp_res_label.visible = not is_diablo_tab1
		_header_xp_res_label.position = Vector2(18.0, 12.0)
		_header_xp_res_label.size = Vector2(280.0, 26.0)

	var tab_w: float = 330.0
	var tab_h: float = 36.0
	var tabs_start_x: float = floorf((hdr_size.x - (tab_w * 2.0 + 14.0)) * 0.5)
	_tab_rects.clear()
	if _tab1_button != null:
		_tab1_button.position = Vector2(tabs_start_x, 42.0)
		_tab1_button.size = Vector2(tab_w, tab_h)
		_tab_rects.append(Rect2(hdr_pos + _tab1_button.position, _tab1_button.size))
	if _tab2_button != null:
		_tab2_button.position = Vector2(tabs_start_x + tab_w + 14.0, 42.0)
		_tab2_button.size = Vector2(tab_w, tab_h)
		_tab_rects.append(Rect2(hdr_pos + _tab2_button.position, _tab2_button.size))

	var right_block_w: float = 428.0
	var right_x: float = hdr_size.x - right_block_w - 16.0
	if _header_sp_label != null:
		_header_sp_label.visible = not is_diablo_tab1
		_header_sp_label.position = Vector2(right_x, 10.0)
		_header_sp_label.size = Vector2(right_block_w, 26.0)

	var dev_cluster_w: float = 82.0 + 6.0 + 88.0 + 6.0 + 118.0
	var dev_start_x: float = hdr_size.x - dev_cluster_w - 16.0
	if _blessing_button != null:
		_blessing_button.visible = not is_diablo_tab1
		_blessing_button.position = Vector2(dev_start_x, 42.0)
		_blessing_button.size = Vector2(82.0, 26.0)
		_blessing_btn_rect = Rect2(hdr_pos + _blessing_button.position, _blessing_button.size)
	if _respec_button != null:
		_respec_button.visible = not is_diablo_tab1
		_respec_button.position = Vector2(dev_start_x + 88.0, 42.0)
		_respec_button.size = Vector2(88.0, 26.0)
		_respec_btn_rect = Rect2(hdr_pos + _respec_button.position, _respec_button.size)
	if _grant_mats_button != null:
		_grant_mats_button.visible = not is_diablo_tab1
		_grant_mats_button.position = Vector2(dev_start_x + 182.0, 42.0)
		_grant_mats_button.size = Vector2(118.0, 26.0)
		_grant_materials_btn_rect = Rect2(hdr_pos + _grant_mats_button.position, _grant_mats_button.size)

	# Body Container Layout (Tab 1 & Tab 2)
	var body_pos: Vector2 = codex_pos + Vector2(18.0, HEADER_HEIGHT + 26.0)
	var body_size: Vector2 = Vector2(codex_size.x - 36.0, codex_size.y - HEADER_HEIGHT - 42.0)

	if tab1_container != null:
		tab1_container.position = body_pos
		tab1_container.size = body_size
		tab1_container.visible = is_menu_open and (active_tab == 0)

	if tab2_container != null:
		tab2_container.position = body_pos
		tab2_container.size = body_size
		tab2_container.visible = is_menu_open and (active_tab == 1)

	_layout_tab1_children(body_pos, body_size)
	_layout_tab2_children(body_pos, body_size)


func _layout_tab1_children(body_pos: Vector2, body_size: Vector2) -> void:
	var is_field_char: bool = (current_menu_mode == MODE_FIELD_CHARACTER)
	var gap: float = 14.0
	var avail_w: float = body_size.x - gap * 2.0
	var left_w: float = floorf(avail_w * (1.0 / 3.35)) if is_field_char else floorf(body_size.x * 0.31)
	var center_w: float = floorf(avail_w * (1.35 / 3.35)) if is_field_char else floorf(body_size.x * 0.37)
	var right_w: float = body_size.x - left_w - center_w - gap * 2.0
	var col_h: float = body_size.y

	var show_left_panel: bool = (current_menu_mode == MODE_ARMORER_STAND)
	var show_armor_col: bool = false
	var show_weapons: bool = (current_menu_mode == MODE_GUNSMITH_WORKBENCH)
	var show_spells: bool = (current_menu_mode == MODE_BAPTISMAL_ASTROLABE)
	var show_pedestal: bool = (current_menu_mode != MODE_BAPTISMAL_ASTROLABE)
	var show_right_col: bool = (current_menu_mode == MODE_ARMORER_STAND or current_menu_mode == MODE_BAPTISMAL_ASTROLABE)
	var show_forge_ledger_rows: bool = (current_menu_mode == MODE_ARMORER_STAND or current_menu_mode == MODE_BAPTISMAL_ASTROLABE)
	var show_curios: bool = false

	# 1. Left Wing: 4 Armor Plaques (Armorer Stand)
	if _left_wing_panel != null:
		_left_wing_panel.visible = show_left_panel
		_left_wing_panel.position = Vector2.ZERO
		_left_wing_panel.size = Vector2(left_w, col_h)
		var l_hdr: Label = _left_wing_panel.get_node_or_null("LeftWingHeaderLabel") as Label
		if l_hdr != null:
			l_hdr.position = Vector2(10.0, 8.0)
			l_hdr.size = Vector2(left_w - 20.0, 30.0)
			l_hdr.text = "🛡 FORGE VESTMENTS & GAUNTLETS 🛡" if current_menu_mode == MODE_ARMORER_STAND else "❖ EQUIPMENT SLOTS ❖"

	_armor_plaque_rects.clear()
	_armor_forge_btn_rects.clear()
	var arm_top: float = 44.0
	var arm_gap: float = 10.0
	var arm_card_h: float = floorf((col_h - arm_top - 12.0 - arm_gap * 3.0) / 4.0)
	var arm_card_w: float = left_w - 20.0

	for i: int in range(_armor_card_panels.size()):
		var card: Panel = _armor_card_panels[i]
		card.visible = show_armor_col
		var c_pos: Vector2 = Vector2(10.0, arm_top + float(i) * (arm_card_h + arm_gap))
		card.position = c_pos
		card.size = Vector2(arm_card_w, arm_card_h)
		if show_armor_col:
			_armor_plaque_rects.append(Rect2(body_pos + c_pos, card.size))
		else:
			_armor_plaque_rects.append(Rect2())

		_armor_title_labels[i].position = Vector2(14.0, 6.0)
		_armor_title_labels[i].size = Vector2(arm_card_w - 28.0, 26.0)

		_armor_sub_labels[i].position = Vector2(14.0, 32.0)
		_armor_sub_labels[i].size = Vector2(arm_card_w - 28.0, 22.0)

		_armor_perk_labels[i].position = Vector2(14.0, 56.0)
		_armor_perk_labels[i].size = Vector2(arm_card_w - 28.0, maxf(68.0, arm_card_h - 98.0))

		var btn_pos: Vector2 = Vector2(14.0, arm_card_h - 38.0)
		var btn_sz: Vector2 = Vector2(arm_card_w - 28.0, 32.0)
		_armor_action_buttons[i].position = btn_pos
		_armor_action_buttons[i].size = btn_sz
		if show_armor_col:
			_armor_forge_btn_rects.append(Rect2(body_pos + c_pos + btn_pos, btn_sz))
		else:
			_armor_forge_btn_rects.append(Rect2())

	# 2. Center Nave / Upper Paper-Doll Stage
	var upper_h: float = floorf(col_h * 0.62) if is_field_char else col_h
	var pillar_w: float = 230.0
	var center_pos: Vector2 = Vector2(left_w + gap, 0.0)
	var eff_center_w: float = center_w
	if is_field_char:
		center_pos = Vector2.ZERO
		eff_center_w = body_size.x - pillar_w - 10.0
	elif current_menu_mode == MODE_GUNSMITH_WORKBENCH:
		center_pos = Vector2.ZERO
		eff_center_w = body_size.x
	elif current_menu_mode == MODE_BAPTISMAL_ASTROLABE:
		center_pos = Vector2.ZERO
		eff_center_w = left_w + center_w + gap

	if _center_nave_panel != null:
		_center_nave_panel.visible = true
		_center_nave_panel.position = center_pos
		_center_nave_panel.size = Vector2(eff_center_w, upper_h)
		if is_field_char:
			_center_nave_panel.add_theme_stylebox_override("panel", _make_stylebox(Color.html("#090a0d"), COL_PANEL_BORDER, 1, 4))
		else:
			_center_nave_panel.add_theme_stylebox_override("panel", _make_stylebox(Color(0.09, 0.08, 0.12, 0.96), COL_CARD_BORDER, 2, 5))

		var p_hdr: Label = _center_nave_panel.get_node_or_null("PedestalHeaderLabel") as Label
		if p_hdr != null:
			p_hdr.visible = show_pedestal
			p_hdr.z_index = 4
			if is_field_char:
				p_hdr.position = Vector2(96.0, upper_h - 26.0)
				p_hdr.size = Vector2(eff_center_w - 192.0, 22.0)
				p_hdr.text = "⟳ Drag to Rotate Hunter"
			else:
				p_hdr.position = Vector2(10.0, 8.0)
				p_hdr.size = Vector2(eff_center_w - 20.0, 28.0)
				if current_menu_mode == MODE_GUNSMITH_WORKBENCH:
					p_hdr.text = "⚒ 3D FIREARM ANVIL PEDESTAL (DRAG TO ROTATE) ⚒"
				else:
					p_hdr.text = "🛡 3D HUNTER ARMORY MANNEQUIN (DRAG TO ROTATE) 🛡"

	var ped_h: float = 380.0
	if current_menu_mode == MODE_ARMORER_STAND:
		ped_h = col_h - 98.0
	elif current_menu_mode == MODE_GUNSMITH_WORKBENCH:
		ped_h = floorf(col_h * 0.34)
	elif is_field_char:
		ped_h = upper_h - 34.0
	var ped_pos_local: Vector2 = Vector2(96.0, 4.0) if is_field_char else Vector2(12.0, 38.0)
	var ped_sz: Vector2 = Vector2(eff_center_w - 192.0, ped_h) if is_field_char else Vector2(eff_center_w - 24.0, ped_h)
	if _pedestal_frame_panel != null:
		_pedestal_frame_panel.visible = show_pedestal and not is_field_char
		_pedestal_frame_panel.position = ped_pos_local
		_pedestal_frame_panel.size = ped_sz

	if sub_viewport_container != null:
		if is_field_char:
			sub_viewport_container.position = ped_pos_local
			sub_viewport_container.size = ped_sz
		else:
			sub_viewport_container.position = ped_pos_local + Vector2(3.0, 3.0)
			sub_viewport_container.size = ped_sz - Vector2(6.0, 6.0)
		sub_viewport_container.visible = is_menu_open and (active_tab == 0) and show_pedestal

	_pedestal_arch_rect = Rect2(body_pos + center_pos + ped_pos_local, ped_sz) if show_pedestal else Rect2()

	var forge_top: float = ped_pos_local.y + ped_sz.y + 8.0
	if _center_nave_panel != null:
		var f_hdr: Label = _center_nave_panel.get_node_or_null("ArsenalForgeHeaderLabel") as Label
		if f_hdr != null:
			f_hdr.visible = show_weapons
			f_hdr.position = Vector2(10.0, forge_top)
			f_hdr.size = Vector2(eff_center_w - 20.0, 28.0)
			f_hdr.text = "⚒ FIREARMS & ALCHEMICAL BARREL RITE SOCKETS ⚒" if current_menu_mode == MODE_GUNSMITH_WORKBENCH else "❖ EQUIPPED FIREARM & ACTIVE BARREL RITE ❖"

	_weapon_card_rects.clear()
	_weapon_forge_btn_rects.clear()
	_weapon_mod_socket_rects.clear()

	var spells_section_h: float = 136.0 if show_spells else 0.0
	var weap_area_top: float = forge_top + 30.0
	var weap_area_h: float = col_h - weap_area_top - spells_section_h - 10.0
	var w_gap: float = 8.0
	var w_card_h: float = floorf((weap_area_h - w_gap * 2.0) / 3.0)
	var w_card_w: float = eff_center_w - 24.0

	for w_i: int in range(_weapon_card_panels.size()):
		var w_card: Panel = _weapon_card_panels[w_i]
		w_card.visible = show_weapons
		var wc_pos: Vector2 = Vector2(12.0, weap_area_top + float(w_i) * (w_card_h + w_gap))
		w_card.position = wc_pos
		w_card.size = Vector2(w_card_w, w_card_h)
		var wc_global: Rect2 = Rect2(body_pos + center_pos + wc_pos, w_card.size)
		_weapon_card_rects.append(wc_global if show_weapons else Rect2())

		_weapon_title_labels[w_i].position = Vector2(12.0, 6.0)
		_weapon_title_labels[w_i].size = Vector2(w_card_w - 230.0, 26.0)

		_weapon_rite_labels[w_i].position = Vector2(12.0, 32.0)
		_weapon_rite_labels[w_i].size = Vector2(w_card_w - 230.0, 22.0)

		var wb_pos: Vector2 = Vector2(w_card_w - 216.0, 8.0)
		var wb_sz: Vector2 = Vector2(204.0, 34.0)
		_weapon_action_buttons[w_i].position = wb_pos
		_weapon_action_buttons[w_i].size = wb_sz
		_weapon_forge_btn_rects.append(Rect2(wc_global.position + wb_pos, wb_sz) if show_weapons else Rect2())

		var mod_row: Array = _weapon_mod_buttons[w_i]
		var sock_rects: Array[Rect2] = []
		var m_gap: float = 6.0
		var m_btn_w: float = floorf((w_card_w - 24.0 - m_gap * 3.0) / 4.0)
		var m_btn_h: float = maxf(28.0, w_card_h - 62.0)
		var m_y: float = w_card_h - m_btn_h - 6.0
		for m_i: int in range(mod_row.size()):
			var m_btn: Button = mod_row[m_i] as Button
			var m_pos: Vector2 = Vector2(12.0 + float(m_i) * (m_btn_w + m_gap), m_y)
			m_btn.position = m_pos
			m_btn.size = Vector2(m_btn_w, m_btn_h)
			sock_rects.append(Rect2(wc_global.position + m_pos, m_btn.size) if show_weapons else Rect2())
		_weapon_mod_socket_rects.append(sock_rects)

	var spells_top: float = 14.0 if current_menu_mode == MODE_BAPTISMAL_ASTROLABE else (col_h - spells_section_h)
	if _center_nave_panel != null:
		var sp_hdr: Label = _center_nave_panel.get_node_or_null("LanternSpellsHeaderLabel") as Label
		if sp_hdr != null:
			sp_hdr.visible = show_spells
			sp_hdr.position = Vector2(10.0, spells_top)
			sp_hdr.size = Vector2(eff_center_w - 20.0, 28.0)
			sp_hdr.text = "✦ [F] LANTERN CONSECRATION SPELLS & SORCERY RITES ✦" if current_menu_mode == MODE_BAPTISMAL_ASTROLABE else "❖ EQUIPPED [F] LANTERN SPELL ❖"

	_spell_medallion_rects.clear()
	_spell_forge_btn_rects.clear()
	var sp_gap: float = 12.0
	var sp_w: float = floorf((eff_center_w - 24.0 - sp_gap * 2.0) / 3.0)
	var sp_h: float = (col_h - 64.0) if current_menu_mode == MODE_BAPTISMAL_ASTROLABE else (spells_section_h - 40.0)
	for s_i: int in range(_spell_card_panels.size()):
		var sp_card: Panel = _spell_card_panels[s_i]
		sp_card.visible = show_spells
		var sp_pos: Vector2 = Vector2(12.0 + float(s_i) * (sp_w + sp_gap), spells_top + 34.0)
		sp_card.position = sp_pos
		sp_card.size = Vector2(sp_w, sp_h)
		var sp_global: Rect2 = Rect2(body_pos + center_pos + sp_pos, sp_card.size)
		_spell_medallion_rects.append(sp_global if show_spells else Rect2())

		_spell_title_labels[s_i].position = Vector2(6.0, 8.0)
		_spell_title_labels[s_i].size = Vector2(sp_w - 12.0, 48.0 if current_menu_mode == MODE_BAPTISMAL_ASTROLABE else 32.0)

		var sb_pos: Vector2 = Vector2(8.0, sp_h - 42.0)
		var sb_sz: Vector2 = Vector2(sp_w - 16.0, 34.0 if current_menu_mode == MODE_BAPTISMAL_ASTROLABE else 30.0)
		_spell_action_buttons[s_i].position = sb_pos
		_spell_action_buttons[s_i].size = sb_sz
		_spell_forge_btn_rects.append(Rect2(sp_global.position + sb_pos, sb_sz) if show_spells else Rect2())

	# 3. Right Wing: 12 Stat Rows + 2x4 Curios Vault / Absolution Altar
	var right_pos: Vector2 = Vector2(left_w + center_w + gap * 2.0, 0.0)
	if _right_wing_panel != null:
		_right_wing_panel.visible = show_right_col
		_right_wing_panel.position = right_pos
		_right_wing_panel.size = Vector2(right_w, col_h)
		var r_hdr: Label = _right_wing_panel.get_node_or_null("RightWingHeaderLabel") as Label
		if r_hdr != null:
			r_hdr.position = Vector2(10.0, 8.0)
			r_hdr.size = Vector2(right_w - 20.0, 30.0)
			if current_menu_mode == MODE_ARMORER_STAND:
				r_hdr.text = "🛡 DEFENSIVE & MOBILITY COMPARISON LEDGER 🛡"
			elif current_menu_mode == MODE_BAPTISMAL_ASTROLABE:
				r_hdr.text = "✦ SANCTUARY ABSOLUTION & LANTERN LEDGER ✦"
			else:
				r_hdr.text = "❖ HUNTER'S INVENTORY VAULT ❖"

	var ledger_top: float = 96.0 if current_menu_mode == MODE_ARMORER_STAND else 44.0
	var vault_section_h: float = 268.0 if show_curios else (160.0 if current_menu_mode == MODE_BAPTISMAL_ASTROLABE else 24.0)
	var ledger_avail_h: float = col_h - ledger_top - vault_section_h - 10.0
	var row_h: float = floorf(ledger_avail_h / 12.0)
	var row_w: float = right_w - 24.0

	for r_i: int in range(_stat_row_panels.size()):
		var r_p: Panel = _stat_row_panels[r_i]
		r_p.visible = show_forge_ledger_rows
		r_p.position = Vector2(12.0, ledger_top + float(r_i) * row_h)
		r_p.size = Vector2(row_w, row_h - 3.0)

		_stat_name_labels[r_i].position = Vector2(12.0, 0.0)
		_stat_name_labels[r_i].size = Vector2(row_w * 0.58, row_h - 3.0)

		_stat_val_labels[r_i].position = Vector2(row_w * 0.56, 0.0)
		_stat_val_labels[r_i].size = Vector2(row_w * 0.44 - 12.0, row_h - 3.0)

	var vault_top: float = col_h - vault_section_h
	if _right_wing_panel != null:
		var v_hdr: Label = _right_wing_panel.get_node_or_null("CuriosVaultHeaderLabel") as Label
		if v_hdr != null:
			v_hdr.visible = show_curios or (current_menu_mode == MODE_BAPTISMAL_ASTROLABE)
			v_hdr.position = Vector2(10.0, vault_top)
			v_hdr.size = Vector2(right_w - 20.0, 26.0)
			v_hdr.text = "✦ RITE OF ABSOLUTION & SANCTUARY BLESSING ✦" if current_menu_mode == MODE_BAPTISMAL_ASTROLABE else "❖ COLLECTED LOOT POUCH & CURIOS (2×4) ❖"

	if _loot_pouch_summary_label != null:
		_loot_pouch_summary_label.visible = show_curios
		_loot_pouch_summary_label.position = Vector2(12.0, vault_top + 26.0)
		_loot_pouch_summary_label.size = Vector2(right_w - 24.0, 36.0)

	if _absolution_rite_button != null:
		_absolution_rite_button.visible = (current_menu_mode == MODE_BAPTISMAL_ASTROLABE)
		_absolution_rite_button.position = Vector2(16.0, vault_top + 42.0)
		_absolution_rite_button.size = Vector2(right_w - 32.0, 56.0)

	_relic_socket_rects.clear()
	var rel_gap: float = 8.0
	var rel_w: float = floorf((right_w - 24.0 - rel_gap * 3.0) / 4.0)
	var rel_h: float = 44.0
	var grid_top: float = vault_top + 64.0

	for rel_i: int in range(_relic_buttons.size()):
		var col_i: int = rel_i % 4
		var row_i: int = rel_i / 4
		var r_btn: Button = _relic_buttons[rel_i]
		r_btn.visible = show_curios
		var rb_pos: Vector2 = Vector2(12.0 + float(col_i) * (rel_w + rel_gap), grid_top + float(row_i) * (rel_h + rel_gap))
		r_btn.position = rb_pos
		r_btn.size = Vector2(rel_w, rel_h)
		_relic_socket_rects.append(Rect2(body_pos + right_pos + rb_pos, r_btn.size) if show_curios else Rect2())

	var lore_top: float = grid_top + 2.0 * (rel_h + rel_gap) + 4.0
	if _curio_title_label != null:
		_curio_title_label.visible = show_curios
		_curio_title_label.position = Vector2(14.0, lore_top)
		_curio_title_label.size = Vector2(right_w - 28.0, 24.0)
	if _curio_lore_label != null:
		_curio_lore_label.visible = show_curios
		_curio_lore_label.position = Vector2(14.0, lore_top + 24.0)
		_curio_lore_label.size = Vector2(right_w - 28.0, 48.0)

	_layout_field_character_tab1(is_field_char, left_w, eff_center_w, right_w, col_h, forge_top)
	_layout_armorer_stand_tab1(current_menu_mode == MODE_ARMORER_STAND, body_pos, left_w, eff_center_w, right_w, col_h, forge_top)


func _layout_armorer_stand_tab1(is_armorer: bool, body_pos: Vector2, left_w: float, center_w: float, right_w: float, col_h: float, center_bot_top: float) -> void:
	if _armorer_left_container != null:
		_armorer_left_container.visible = is_armorer
		_armorer_left_container.position = Vector2(10.0, 42.0)
		var l_inner_w: float = left_w - 20.0
		var l_inner_h: float = col_h - 48.0
		_armorer_left_container.size = Vector2(l_inner_w, l_inner_h)

		var tab_gap: float = 4.0
		var tab_w: float = floorf((l_inner_w - tab_gap * 3.0) / 4.0)
		for t_i: int in range(_armorer_set_tab_buttons.size()):
			var tb: Button = _armorer_set_tab_buttons[t_i]
			tb.position = Vector2(float(t_i) * (tab_w + tab_gap), 0.0)
			tb.size = Vector2(tab_w, 34.0)

		var cards_top: float = 42.0
		var p_gap: float = 7.0
		var p_card_h: float = floorf((l_inner_h - cards_top - p_gap * 4.0) / 5.0)
		if is_armorer:
			_armor_plaque_rects.clear()
			_armor_forge_btn_rects.clear()
		for p_i: int in range(_armorer_piece_cards.size()):
			var pc: Panel = _armorer_piece_cards[p_i]
			var pc_pos: Vector2 = Vector2(0.0, cards_top + float(p_i) * (p_card_h + p_gap))
			pc.position = pc_pos
			pc.size = Vector2(l_inner_w, p_card_h)
			_armorer_piece_titles[p_i].position = Vector2(10.0, 5.0)
			_armorer_piece_titles[p_i].size = Vector2(l_inner_w - 20.0, 22.0)
			_armorer_piece_subs[p_i].position = Vector2(10.0, 27.0)
			_armorer_piece_subs[p_i].size = Vector2(l_inner_w - 20.0, maxf(24.0, p_card_h - 66.0))
			var pb: Button = _armorer_piece_buttons[p_i]
			var pb_pos: Vector2 = Vector2(10.0, p_card_h - 34.0)
			var pb_sz: Vector2 = Vector2(l_inner_w - 20.0, 28.0)
			pb.position = pb_pos
			pb.size = pb_sz
			if is_armorer:
				var card_glob: Vector2 = body_pos + _armorer_left_container.position + pc_pos
				_armor_plaque_rects.append(Rect2(card_glob, pc.size))
				_armor_forge_btn_rects.append(Rect2(card_glob + pb_pos, pb_sz))

	if _armorer_preview_toggle_btn != null:
		_armorer_preview_toggle_btn.visible = is_armorer
		_armorer_preview_toggle_btn.position = Vector2(12.0, center_bot_top)
		_armorer_preview_toggle_btn.size = Vector2(center_w - 24.0, 38.0)

	if _armorer_comparison_header != null:
		_armorer_comparison_header.visible = is_armorer
		_armorer_comparison_header.position = Vector2(12.0, 42.0)
		_armorer_comparison_header.size = Vector2(right_w - 24.0, 48.0)


func _layout_field_character_tab1(is_field_char: bool, _left_w: float, center_w: float, _right_w: float, col_h: float, _center_bot_top: float) -> void:
	var upper_h: float = floorf(col_h * 0.62)
	var lower_h: float = col_h - upper_h - 10.0
	var pillar_w: float = 230.0
	var stage_w: float = center_w
	var total_w: float = stage_w + pillar_w + 10.0

	if _field_left_equip_container != null:
		_field_left_equip_container.visible = is_field_char
		_field_left_equip_container.z_index = 3
		_field_left_equip_container.position = Vector2.ZERO
		_field_left_equip_container.size = Vector2(stage_w, upper_h)
		if _left_armor_vbox != null:
			_left_armor_vbox.position = Vector2(18.0, 0.0)
			_left_armor_vbox.size = Vector2(68.0, upper_h)
		if _aux_right_vbox != null:
			_aux_right_vbox.position = Vector2(stage_w - 86.0, 0.0)
			_aux_right_vbox.size = Vector2(68.0, upper_h)

	if _stat_pillar_panel != null:
		_stat_pillar_panel.visible = is_field_char
		_stat_pillar_panel.position = Vector2(stage_w + 10.0, 0.0)
		_stat_pillar_panel.size = Vector2(pillar_w, upper_h)

	if _field_center_summary_panel != null:
		_field_center_summary_panel.visible = false

	if _field_right_inv_container != null:
		_field_right_inv_container.visible = is_field_char
		_field_right_inv_container.position = Vector2(0.0, upper_h + 10.0)
		_field_right_inv_container.size = Vector2(total_w, lower_h)
		var lower_bg: Panel = _field_right_inv_container.get_node_or_null("LowerStashBackdropPanel") as Panel
		if lower_bg != null:
			lower_bg.position = Vector2(0.0, 34.0)
			lower_bg.size = Vector2(total_w, maxf(120.0, lower_h - 34.0))
		if _stash_tab_hbox != null:
			_stash_tab_hbox.position = Vector2(0.0, 0.0)
			_stash_tab_hbox.size = Vector2(704.0, 32.0)
		var grid_w: float = 706.0
		var inner_h: float = maxf(110.0, lower_h - 50.0)
		if _inv_scroll != null:
			_inv_scroll.position = Vector2(10.0, 42.0)
			_inv_scroll.size = Vector2(grid_w, inner_h)
		if _inv_inspector_panel != null:
			_inv_inspector_panel.visible = is_field_char
			var insp_x: float = grid_w + 22.0
			var insp_w: float = maxf(240.0, total_w - insp_x - 10.0)
			_inv_inspector_panel.position = Vector2(insp_x, 42.0)
			_inv_inspector_panel.size = Vector2(insp_w, inner_h)
			if _inv_inspector_title != null:
				_inv_inspector_title.position = Vector2(14.0, 10.0)
				_inv_inspector_title.size = Vector2(insp_w - 28.0, 24.0)
			if _inv_inspector_body != null:
				_inv_inspector_body.position = Vector2(14.0, 38.0)
				_inv_inspector_body.size = Vector2(insp_w - 28.0, inner_h - 46.0)


func _layout_tab2_children(body_pos: Vector2, body_size: Vector2) -> void:
	var plaque_h: float = 176.0
	var map_h: float = body_size.y - plaque_h - 12.0
	var map_w: float = body_size.x

	if _astrolabe_map_panel != null:
		_astrolabe_map_panel.position = Vector2.ZERO
		_astrolabe_map_panel.size = Vector2(map_w, map_h)

	if _astrolabe_conduit_canvas != null:
		_astrolabe_conduit_canvas.position = Vector2.ZERO
		_astrolabe_conduit_canvas.size = Vector2(map_w, map_h)

	var col_x_uvs: Array[float] = [0.14, 0.38, 0.62, 0.86]
	for c_i: int in range(_constellation_header_labels.size()):
		var cx: float = col_x_uvs[c_i] * map_w
		var c_lbl: Label = _constellation_header_labels[c_i]
		c_lbl.position = Vector2(cx - 165.0, 12.0)
		c_lbl.size = Vector2(330.0, 30.0)

	_skill_node_centers.clear()
	_skill_node_radii.clear()
	var catalog: Dictionary[String, Dictionary] = PlayerLoadoutManager.get_skill_tree_catalog()
	var node_ids: Array[String] = PlayerLoadoutManager.get_skill_node_ids()

	for sid: String in node_ids:
		var info: Dictionary = catalog[sid]
		var uv: Vector2 = info["pos_uv"] as Vector2
		var local_center: Vector2 = Vector2(uv.x * map_w, uv.y * map_h)
		var global_center: Vector2 = body_pos + local_center
		_skill_node_centers[sid] = global_center

		var tier: int = int(info.get("tier", 1))
		var const_idx: int = int(info.get("constellation", 0))
		var diam: float = 68.0 if tier == 4 else (54.0 if const_idx == 4 else 58.0)
		var rad: float = diam * 0.5
		_skill_node_radii[sid] = rad

		if _skill_node_buttons.has(sid):
			var s_btn: Button = _skill_node_buttons[sid]
			s_btn.position = local_center - Vector2(rad, rad)
			s_btn.size = Vector2(diam, diam)
		if _skill_tier_labels.has(sid):
			var st_lbl: Label = _skill_tier_labels[sid]
			st_lbl.position = Vector2(local_center.x - 105.0, local_center.y + rad + 2.0)
			st_lbl.size = Vector2(210.0, 22.0)

	var plaque_pos: Vector2 = Vector2(0.0, map_h + 12.0)
	if _inscription_plaque_panel != null:
		_inscription_plaque_panel.position = plaque_pos
		_inscription_plaque_panel.size = Vector2(map_w, plaque_h)

	var text_w: float = map_w - 390.0
	if _skill_title_label != null:
		_skill_title_label.position = Vector2(24.0, 12.0)
		_skill_title_label.size = Vector2(text_w, 32.0)
	if _skill_lore_label != null:
		_skill_lore_label.position = Vector2(24.0, 48.0)
		_skill_lore_label.size = Vector2(text_w, 28.0)
	if _skill_effect_label != null:
		_skill_effect_label.position = Vector2(24.0, 82.0)
		_skill_effect_label.size = Vector2(text_w, 32.0)
	if _skill_prereq_label != null:
		_skill_prereq_label.position = Vector2(24.0, 122.0)
		_skill_prereq_label.size = Vector2(text_w, 30.0)

	if _consecrate_rite_button != null:
		var cb_pos: Vector2 = Vector2(map_w - 352.0, 52.0)
		var cb_sz: Vector2 = Vector2(328.0, 72.0)
		_consecrate_rite_button.position = cb_pos
		_consecrate_rite_button.size = cb_sz
		_consecrate_btn_rect = Rect2(body_pos + plaque_pos + cb_pos, cb_sz)


# ==============================================================================================
# REFRESH ALL UI ELEMENTS & HIGH-CONTRAST DATA BINDING (Phase 2.2)
# ==============================================================================================
func _refresh_all_ui_elements() -> void:
	_resolve_loadout_manager()

	var h_lvl: int = loadout_manager.hunter_level if loadout_manager != null else 1
	var cur_xp: int = loadout_manager.current_xp if loadout_manager != null else 0
	var next_xp: int = loadout_manager.xp_to_next_level if loadout_manager != null else 100
	var sp_val: int = loadout_manager.skill_points if loadout_manager != null else 3
	var s_amt: int = loadout_manager.get_resource_amount("silver") if loadout_manager != null else 35
	var b_amt: int = loadout_manager.get_resource_amount("bone_ash") if loadout_manager != null else 15
	var i_amt: int = loadout_manager.get_resource_amount("cursed_iron") if loadout_manager != null else 0
	var c_amt: int = loadout_manager.get_resource_amount("soul_cores") if loadout_manager != null else 0

	if _header_title_label != null:
		match current_menu_mode:
			MODE_GUNSMITH_WORKBENCH:
				_header_title_label.text = "THE GUNSMITH'S FORGE"
			MODE_ARMORER_STAND:
				_header_title_label.text = "THE ORDER'S ARMORY"
			MODE_BAPTISMAL_ASTROLABE:
				_header_title_label.text = "BAPTISMAL FONT OF RITES"
			_:
				_header_title_label.text = "THE HUNTER'S RELIQUARY"
	if _header_xp_res_label != null:
		_header_xp_res_label.text = "LEVEL %d — XP: %d / %d" % [h_lvl, cur_xp, next_xp]
	if _header_sp_label != null:
		_header_sp_label.text = "✦ %d SP | ◈%d SILVER | ⚱%d ASH | ⛓%d IRON | ✦%d CORE" % [sp_val, s_amt, b_amt, i_amt, c_amt]
	if _loot_pouch_summary_label != null:
		_loot_pouch_summary_label.text = "COLLECTED LOOT POUCH: ◈%d Silver (Gunsmith) | ⚱%d Ash (Mods) | ⛓%d Iron (Armory) | ✦%d Cores (Font)" % [s_amt, b_amt, i_amt, c_amt]

	if _tab1_button != null:
		_tab1_button.visible = true
		match current_menu_mode:
			MODE_GUNSMITH_WORKBENCH:
				_tab1_button.text = "⚒ FIREARMS & ALCHEMICAL BARREL RITES ⚒"
			MODE_ARMORER_STAND:
				_tab1_button.text = "🛡 VESTMENTS & ARTICULATED GAUNTLETS 🛡"
			MODE_BAPTISMAL_ASTROLABE:
				_tab1_button.text = "✦ LANTERN SORCERY & ABSOLUTION ✦"
			_:
				_tab1_button.text = "❖ EQUIPPED LOADOUT, LOOT & STATS ❖"
		var t1_sel: bool = (active_tab == 0)
		_apply_button_theme(
			_tab1_button,
			COL_BTN_BG_HOVER if t1_sel else COL_BTN_BG,
			COL_CARD_BORDER_ACTIVE if t1_sel else COL_BTN_BORDER,
			COL_HEADER_GOLD if t1_sel else COL_BTN_FONT
		)
	if _tab2_button != null:
		var allow_tab2: bool = (current_menu_mode == MODE_FIELD_CHARACTER or current_menu_mode == MODE_BAPTISMAL_ASTROLABE)
		_tab2_button.visible = allow_tab2
		_tab2_button.text = "❖ HUNTER LEVELS & CELESTIAL SKILL TREE (%d SP) ❖" % sp_val
		var t2_sel: bool = (active_tab == 1)
		_apply_button_theme(
			_tab2_button,
			COL_BTN_BG_HOVER if t2_sel else COL_BTN_BG,
			COL_CARD_BORDER_ACTIVE if t2_sel else COL_BTN_BORDER,
			COL_HEADER_GOLD if t2_sel else COL_BTN_FONT
		)

	_refresh_tab1_elements()
	_refresh_tab2_elements()

	if _header_filigree_canvas != null:
		_header_filigree_canvas.queue_redraw()
	if _stage_sanctuary_backdrop_canvas != null:
		_stage_sanctuary_backdrop_canvas.queue_redraw()
	if _astrolabe_conduit_canvas != null:
		_astrolabe_conduit_canvas.queue_redraw()
	if bg_decor_canvas != null:
		bg_decor_canvas.queue_redraw()
	if vfx_overlay_canvas != null:
		vfx_overlay_canvas.queue_redraw()


func _refresh_tab1_elements() -> void:
	var is_field_char_mode: bool = (current_menu_mode == MODE_FIELD_CHARACTER)
	# 1. Armor Cards
	var armor_cat: Array[Dictionary] = PlayerLoadoutManager.get_armor_set_catalog()
	var eq_armor: int = loadout_manager.equipped_armor_index if loadout_manager != null else 0

	for i: int in range(_armor_card_panels.size()):
		var a_info: Dictionary = armor_cat[i]
		var is_unlocked: bool = loadout_manager.is_armor_unlocked(i) if loadout_manager != null else (i == 0)
		var is_eq: bool = (i == eq_armor) and is_unlocked
		var is_hov: bool = (i == hovered_armor_index)

		var card_bg: Color = COL_CARD_BG_ACTIVE if is_eq else COL_CARD_BG
		var card_br: Color = COL_CARD_BORDER_ACTIVE if (is_eq or is_hov) else COL_CARD_BORDER
		_armor_card_panels[i].add_theme_stylebox_override("panel", _make_stylebox(card_bg, card_br, 3 if is_eq else 2, 4))

		_armor_sub_labels[i].text = "%d ARMOR  —  %s" % [int(a_info["armor"]), String(a_info["subtitle"])]
		_armor_sub_labels[i].add_theme_color_override("font_color", COL_STAT_EMERALD if is_unlocked else COL_STAT_AMBER)

		var a_btn: Button = _armor_action_buttons[i]
		if is_unlocked:
			a_btn.visible = true
			if is_eq:
				a_btn.text = "[ ✓ EQUIPPED ]"
				_apply_button_theme(a_btn, COL_BTN_BG_ACTIVE, COL_STAT_EMERALD, COL_BTN_FONT)
			else:
				a_btn.text = "[ DON ARMOR ]" if current_menu_mode == MODE_ARMORER_STAND else "[ EQUIP ]"
				_apply_button_theme(a_btn, COL_BTN_BG, COL_BTN_BORDER, COL_BTN_FONT)
		elif is_field_char_mode:
			a_btn.visible = false
			a_btn.text = "[ LOCKED — ARMORY ]"
		else:
			a_btn.visible = true
			var rec: Dictionary = loadout_manager.get_item_recipe("armor", i) if loadout_manager != null else {}
			var can_craft: bool = loadout_manager != null and loadout_manager.can_afford(rec) and is_forge_available()
			var cost_s: String = _format_recipe_cost_badge(rec)
			if can_craft:
				a_btn.text = "[ ⚒ FORGE VESTMENTS (%s) ]" % cost_s
				_apply_button_theme(a_btn, COL_BTN_BG_ACTIVE, COL_STAT_EMERALD, COL_BTN_FONT)
			else:
				a_btn.text = "[ ⚒ FORGE VESTMENTS: %s ]" % cost_s
				_apply_button_theme(a_btn, COL_BTN_BG, COL_BTN_BORDER, COL_BTN_FONT)

	# 2. Weapon Cards & Rite Mod Buttons
	var mods_cat: Array[Dictionary] = PlayerLoadoutManager.get_weapon_mod_catalog()
	var weapons_ids: Array[String] = ["revolver", "shotgun", "stakedriver"]
	for w_i: int in range(_weapon_card_panels.size()):
		var w_id: String = weapons_ids[w_i]
		var is_w_unlocked: bool = loadout_manager.is_weapon_unlocked(w_i) if loadout_manager != null else (w_i == 0)
		var is_act_weap: bool = (loadout_manager != null and loadout_manager.active_weapon_id == w_id and is_w_unlocked)
		var eq_mod: int = loadout_manager.weapon_mod_indices[w_i] if loadout_manager != null else 0

		var w_bg: Color = COL_CARD_BG_ACTIVE if is_act_weap else COL_CARD_BG
		var w_br: Color = COL_CARD_BORDER_ACTIVE if is_act_weap else COL_CARD_BORDER
		_weapon_card_panels[w_i].add_theme_stylebox_override("panel", _make_stylebox(w_bg, w_br, 3 if is_act_weap else 2, 4))

		var active_mod_dict: Dictionary = mods_cat[posmod(eq_mod, 4)]
		if is_w_unlocked:
			_weapon_rite_labels[w_i].text = "Active Rite: %s" % String(active_mod_dict["name"])
			_weapon_rite_labels[w_i].add_theme_color_override("font_color", COL_STAT_EMERALD if is_act_weap else COL_BODY_IVORY)
		elif is_field_char_mode:
			_weapon_rite_labels[w_i].text = "Locked — Visit Sanctuary Gunsmith"
			_weapon_rite_labels[w_i].add_theme_color_override("font_color", COL_STAT_AMBER)
		else:
			var w_rec: Dictionary = loadout_manager.get_item_recipe("weapon", w_i) if loadout_manager != null else {}
			_weapon_rite_labels[w_i].text = "Locked — Recipe: %s" % _format_recipe_cost_badge(w_rec)
			_weapon_rite_labels[w_i].add_theme_color_override("font_color", COL_STAT_AMBER)

		var w_btn: Button = _weapon_action_buttons[w_i]
		if is_w_unlocked:
			w_btn.visible = true
			if is_act_weap:
				w_btn.text = "[ ✓ EQUIPPED ]"
				_apply_button_theme(w_btn, COL_BTN_BG_ACTIVE, COL_STAT_EMERALD, COL_BTN_FONT)
			else:
				w_btn.text = "[ EQUIP ]"
				_apply_button_theme(w_btn, COL_BTN_BG, COL_BTN_BORDER, COL_BTN_FONT)
		elif is_field_char_mode:
			w_btn.visible = false
			w_btn.text = "[ LOCKED — WORKBENCH ]"
		else:
			w_btn.visible = true
			var w_rec2: Dictionary = loadout_manager.get_item_recipe("weapon", w_i) if loadout_manager != null else {}
			var can_forge_w: bool = loadout_manager != null and loadout_manager.can_afford(w_rec2) and is_forge_available()
			w_btn.text = "[ ⚒ FORGE FIREARM ]"
			_apply_button_theme(w_btn, COL_BTN_BG_ACTIVE if can_forge_w else COL_BTN_BG, COL_STAT_EMERALD if can_forge_w else COL_BTN_BORDER, COL_BTN_FONT)

		var mod_row: Array = _weapon_mod_buttons[w_i]
		for m_i: int in range(mod_row.size()):
			var m_btn: Button = mod_row[m_i] as Button
			var m_info: Dictionary = mods_cat[m_i]
			var is_m_unlocked: bool = loadout_manager.is_weapon_mod_unlocked(w_i, m_i) if loadout_manager != null else (m_i == 0)
			var is_m_eq: bool = (m_i == eq_mod) and is_m_unlocked and is_w_unlocked
			if is_m_unlocked:
				m_btn.visible = is_w_unlocked or not is_field_char_mode
				m_btn.text = ("✓ " if is_m_eq else "") + String(m_info["short"])
				_apply_button_theme(
					m_btn,
					COL_BTN_BG_ACTIVE if is_m_eq else COL_BTN_BG,
					COL_CARD_BORDER_ACTIVE if is_m_eq else COL_BTN_BORDER,
					COL_BTN_FONT
				)
			elif is_field_char_mode:
				m_btn.visible = false
				m_btn.text = String(m_info["short"])
			else:
				m_btn.visible = true
				var m_rec: Dictionary = loadout_manager.get_item_recipe("mod", m_i) if loadout_manager != null else {}
				var can_forge_m: bool = is_w_unlocked and loadout_manager != null and loadout_manager.can_afford(m_rec) and is_forge_available()
				m_btn.text = "⚒ FORGE %s" % String(m_info["short"])
				_apply_button_theme(
					m_btn,
					COL_BTN_BG_ACTIVE if can_forge_m else COL_BTN_BG,
					COL_STAT_EMERALD if can_forge_m else COL_BTN_BORDER,
					COL_BTN_FONT
				)

	# 3. Lantern Spells
	var eq_spell: int = loadout_manager.equipped_spell_index if loadout_manager != null else 0
	for s_i: int in range(_spell_card_panels.size()):
		var is_sp_unlocked: bool = loadout_manager.is_spell_unlocked(s_i) if loadout_manager != null else (s_i == 0)
		var is_sp_eq: bool = (s_i == eq_spell) and is_sp_unlocked
		_spell_card_panels[s_i].add_theme_stylebox_override(
			"panel",
			_make_stylebox(COL_CARD_BG_ACTIVE if is_sp_eq else COL_CARD_BG, COL_CARD_BORDER_ACTIVE if is_sp_eq else COL_CARD_BORDER, 2, 4)
		)
		var sp_btn: Button = _spell_action_buttons[s_i]
		if is_sp_unlocked:
			sp_btn.visible = true
			sp_btn.text = "[ ✓ EQUIPPED ]" if is_sp_eq else "[ ATTUNE ]"
			_apply_button_theme(sp_btn, COL_BTN_BG_ACTIVE if is_sp_eq else COL_BTN_BG, COL_STAT_EMERALD if is_sp_eq else COL_BTN_BORDER, COL_BTN_FONT)
		elif is_field_char_mode:
			sp_btn.visible = false
			sp_btn.text = "[ LOCKED — BASIN ]"
		else:
			sp_btn.visible = true
			var sp_rec: Dictionary = loadout_manager.get_item_recipe("spell", s_i) if loadout_manager != null else {}
			var can_forge_sp: bool = loadout_manager != null and loadout_manager.can_afford(sp_rec) and is_forge_available()
			sp_btn.text = "[ ✦ CONSECRATE SPELL (%s) ]" % _format_recipe_cost_badge(sp_rec)
			_apply_button_theme(sp_btn, COL_BTN_BG_ACTIVE if can_forge_sp else COL_BTN_BG, COL_STAT_EMERALD if can_forge_sp else COL_BTN_BORDER, COL_BTN_FONT)

	# 4. 12-Stat Hunter's Illuminated Ledger
	var base_stats: Dictionary[String, float] = {
		"firearm_damage_pct": 108.0, "crit_multiplier_pct": 245.0, "attack_tempo_pct": 100.0,
		"reload_velocity_pct": 105.0, "quickstep_speed_pct": 118.0, "quickstep_iframes_ms": 180.0,
		"max_vitality": 100.0, "max_armor": 35.0, "damage_resistance_pct": 0.0,
		"lantern_reach_m": 26.0, "soul_flame_recharge_pct": 100.0, "unlocked_rites_count": 0.0
	}
	if loadout_manager != null:
		base_stats = loadout_manager.compute_stat_ledger(-1, "")
	var prev_stats: Dictionary[String, float] = base_stats
	if loadout_manager != null:
		prev_stats = loadout_manager.compute_stat_ledger(hovered_armor_index, hovered_skill_id)
	var ledger_rows: Array[Dictionary] = [
		{"key": "firearm_damage_pct", "label": "Firearm Damage Mult", "unit": "%", "decimals": 0},
		{"key": "crit_multiplier_pct", "label": "Headshot Crit Mult", "unit": "%", "decimals": 0},
		{"key": "attack_tempo_pct", "label": "Attack Tempo", "unit": "%", "decimals": 0},
		{"key": "reload_velocity_pct", "label": "Reload Velocity", "unit": "%", "decimals": 0},
		{"key": "quickstep_speed_pct", "label": "Quickstep Speed", "unit": "%", "decimals": 0},
		{"key": "quickstep_iframes_ms", "label": "Quickstep I-Frames", "unit": "ms", "decimals": 0},
		{"key": "max_vitality", "label": "Max Vitality HP", "unit": " HP", "decimals": 0},
		{"key": "max_armor", "label": "Max Armor Plating", "unit": " ARM", "decimals": 0},
		{"key": "damage_resistance_pct", "label": "Damage Resistance", "unit": "%", "decimals": 0},
		{"key": "lantern_reach_m", "label": "Lantern Illumination", "unit": "m", "decimals": 1},
		{"key": "soul_flame_recharge_pct", "label": "Soul-Flame Recharge", "unit": "%", "decimals": 0},
		{"key": "unlocked_rites_count", "label": "Consecrated Rites", "unit": " / 20", "decimals": 0}
	]
	for r_i: int in range(ledger_rows.size()):
		var row_info: Dictionary = ledger_rows[r_i]
		var k: String = String(row_info["key"])
		var lbl_s: String = String(row_info["label"])
		var unit_s: String = String(row_info["unit"])
		var dec: int = int(row_info["decimals"])

		var cur_v: float = float(base_stats.get(k, 0.0))
		var prv_v: float = float(prev_stats.get(k, cur_v))
		var diff: float = prv_v - cur_v

		_stat_name_labels[r_i].text = lbl_s
		var val_str: String = ("%.1f%s" % [cur_v, unit_s]) if dec == 1 else ("%d%s" % [roundi(cur_v), unit_s])

		if absf(diff) >= 0.08:
			var is_pos: bool = diff > 0.0
			var sign_s: String = "+" if is_pos else ""
			var arrow_s: String = "▲" if is_pos else "▼"
			var d_str: String = (
				("%s%.1f%s %s" % [sign_s, diff, unit_s, arrow_s])
				if dec == 1
				else ("%s%d%s %s" % [sign_s, roundi(diff), unit_s, arrow_s])
			)
			_stat_val_labels[r_i].text = "%s  (%s)" % [val_str, d_str]
			_stat_val_labels[r_i].add_theme_color_override("font_color", COL_STAT_EMERALD if is_pos else COL_STAT_CRIMSON)
		else:
			_stat_val_labels[r_i].text = val_str
			_stat_val_labels[r_i].add_theme_color_override("font_color", COL_STAT_EMERALD if (r_i % 2 == 0) else COL_STAT_AMBER)

	# 5. Reliquary Curios (2x4)
	for rel_i: int in range(_relic_buttons.size()):
		var relic_id: int = rel_i + 1
		var owned: bool = (loadout_manager != null and loadout_manager.has_relic(relic_id)) or (rel_i == 0)
		var is_hov_r: bool = (rel_i == hovered_relic_slot)
		var r_btn: Button = _relic_buttons[rel_i]
		r_btn.text = ("✦ " if owned else "") + ("RELIC %d" % relic_id)
		_apply_button_theme(
			r_btn,
			COL_BTN_BG_ACTIVE if owned else COL_BTN_BG,
			COL_CARD_BORDER_ACTIVE if (owned or is_hov_r) else COL_BTN_BORDER,
			COL_HEADER_GOLD if owned else COL_BTN_FONT
		)

	var active_curio_idx: int = hovered_relic_slot if hovered_relic_slot >= 0 else 0
	var curio_info: Dictionary = RELIC_CATALOG_LORE[clampi(active_curio_idx, 0, RELIC_CATALOG_LORE.size() - 1)]
	if _curio_title_label != null:
		_curio_title_label.text = "✦ %s:" % String(curio_info["name"])
	if _curio_lore_label != null:
		_curio_lore_label.text = String(curio_info["lore"])

	if current_menu_mode == MODE_FIELD_CHARACTER:
		_refresh_field_character_tab1(base_stats)
	elif current_menu_mode == MODE_ARMORER_STAND:
		_refresh_armorer_stand_tab1(base_stats, ledger_rows)


func _compute_armorer_candidate_stats() -> Dictionary[String, float]:
	if loadout_manager == null:
		return {}
	var saved_slots: Dictionary = loadout_manager.equipped_armor_slots.duplicate()
	var s_name: String = PlayerLoadoutManager.ARMOR_SLOTS[clampi(_armorer_selected_slot_index, 0, 4)]
	if _armorer_preview_full_set:
		for sk: String in PlayerLoadoutManager.ARMOR_SLOTS:
			loadout_manager.equipped_armor_slots[sk] = posmod(_armorer_selected_set_index, 4)
	else:
		loadout_manager.equipped_armor_slots[s_name] = posmod(_armorer_selected_set_index, 4)
	var cand_stats: Dictionary[String, float] = loadout_manager.compute_stat_ledger(-1, "")
	loadout_manager.equipped_armor_slots = saved_slots
	return cand_stats


func _refresh_armorer_stand_tab1(base_stats: Dictionary[String, float], ledger_rows: Array[Dictionary]) -> void:
	var set_tab_names: Array[String] = [
		"I. Grave-Stalker",
		"II. Inquisitor",
		"III. Juggernaut",
		"IV. Abyssal"
	]
	for t_i: int in range(_armorer_set_tab_buttons.size()):
		var unl_cnt: int = loadout_manager.get_unlocked_piece_count_for_set(t_i) if loadout_manager != null else (5 if t_i == 0 else 0)
		var is_sel_tab: bool = (_armorer_selected_set_index == t_i)
		var t_btn: Button = _armorer_set_tab_buttons[t_i]
		t_btn.text = "%s [%d/5]" % [set_tab_names[t_i], unl_cnt]
		_apply_button_theme(
			t_btn,
			COL_BTN_BG_HOVER if is_sel_tab else COL_BTN_BG,
			COL_CARD_BORDER_ACTIVE if is_sel_tab else COL_BTN_BORDER,
			COL_HEADER_GOLD if is_sel_tab else COL_BTN_FONT
		)

	var slots: Array[String] = PlayerLoadoutManager.ARMOR_SLOTS
	for p_i: int in range(mini(_armorer_piece_cards.size(), slots.size())):
		var s_name: String = slots[p_i]
		var set_idx: int = posmod(_armorer_selected_set_index, 4)
		var is_unl: bool = loadout_manager.is_armor_piece_unlocked(s_name, set_idx) if loadout_manager != null else (set_idx == 0)
		var worn_set: int = loadout_manager.get_equipped_armor_slot(s_name) if loadout_manager != null else 0
		var is_worn: bool = is_unl and (worn_set == set_idx)
		var is_sel_slot: bool = (_armorer_selected_slot_index == p_i)
		var p_info: Dictionary = loadout_manager.get_armor_piece_info(s_name, set_idx) if loadout_manager != null else {}
		var p_title: String = String(p_info.get("name", s_name))
		var p_armor: int = int(p_info.get("armor", 6))
		var p_bonus: String = String(p_info.get("bonus_text", ""))

		_armorer_piece_cards[p_i].add_theme_stylebox_override(
			"panel",
			_make_stylebox(
				COL_CARD_BG_ACTIVE if (is_worn or is_sel_slot) else COL_CARD_BG,
				COL_CARD_BORDER_ACTIVE if (is_worn or is_sel_slot) else COL_CARD_BORDER,
				3 if is_sel_slot else 2,
				4
			)
		)
		_armorer_piece_titles[p_i].text = "[%s] %s (%d ARM)" % [s_name, p_title, p_armor]
		var rec: Dictionary = PlayerLoadoutManager.get_armor_piece_recipe(s_name, set_idx)
		var cost_s: String = _format_recipe_cost_badge(rec)
		_armorer_piece_subs[p_i].text = p_bonus if is_unl else ("%s  |  Cost: %s" % [p_bonus, cost_s])
		_armorer_piece_subs[p_i].add_theme_color_override("font_color", COL_STAT_EMERALD if is_unl else COL_STAT_AMBER)

		var pb: Button = _armorer_piece_buttons[p_i]
		if is_unl:
			if is_worn:
				pb.text = "[ ✓ WORN ]"
				_apply_button_theme(pb, COL_BTN_BG_ACTIVE, COL_STAT_EMERALD, COL_BTN_FONT)
			else:
				pb.text = "[ DON PIECE ]"
				_apply_button_theme(pb, COL_BTN_BG, COL_BTN_BORDER, COL_BTN_FONT)
		else:
			var can_craft: bool = loadout_manager != null and loadout_manager.can_afford(rec) and is_forge_available()
			pb.text = "[ ⚒ FORGE PIECE ]  %s" % cost_s
			_apply_button_theme(
				pb,
				COL_BTN_BG_ACTIVE if can_craft else COL_BTN_BG,
				COL_STAT_EMERALD if can_craft else COL_BTN_BORDER,
				COL_BTN_FONT
			)

	if _armorer_preview_toggle_btn != null:
		_armorer_preview_toggle_btn.text = "[ SHOW CURRENTLY WORN ]" if _armorer_preview_full_set else "[ PREVIEW FULL SET ]"
		_apply_button_theme(
			_armorer_preview_toggle_btn,
			COL_BTN_BG_HOVER if _armorer_preview_full_set else COL_BTN_BG,
			COL_CARD_BORDER_ACTIVE if _armorer_preview_full_set else COL_BTN_BORDER,
			COL_HEADER_GOLD if _armorer_preview_full_set else COL_BTN_FONT
		)

	var sel_slot_name: String = slots[clampi(_armorer_selected_slot_index, 0, 4)]
	var worn_set_idx: int = loadout_manager.get_equipped_armor_slot(sel_slot_name) if loadout_manager != null else 0
	var worn_info: Dictionary = loadout_manager.get_armor_piece_info(sel_slot_name, worn_set_idx) if loadout_manager != null else {}
	var cand_info: Dictionary = loadout_manager.get_armor_piece_info(sel_slot_name, _armorer_selected_set_index) if loadout_manager != null else {}
	var syn_info: Dictionary = loadout_manager.get_active_armor_set_bonus_info() if loadout_manager != null else {"max_matching_count": 5, "bonus_mult": 1.25}
	var syn_cnt: int = int(syn_info.get("max_matching_count", 5))
	var syn_pct: int = roundi((float(syn_info.get("bonus_mult", 1.0)) - 1.0) * 100.0)
	var cand_syn_cnt: int = syn_cnt
	var cand_syn_pct: int = syn_pct
	if loadout_manager != null:
		var saved_eq: Dictionary = loadout_manager.equipped_armor_slots.duplicate()
		if _armorer_preview_full_set:
			for sk: String in slots:
				loadout_manager.equipped_armor_slots[sk] = posmod(_armorer_selected_set_index, 4)
		else:
			loadout_manager.equipped_armor_slots[sel_slot_name] = posmod(_armorer_selected_set_index, 4)
		var cand_syn: Dictionary = loadout_manager.get_active_armor_set_bonus_info()
		loadout_manager.equipped_armor_slots = saved_eq
		cand_syn_cnt = int(cand_syn.get("max_matching_count", syn_cnt))
		cand_syn_pct = roundi((float(cand_syn.get("bonus_mult", 1.0)) - 1.0) * 100.0)
	if _armorer_comparison_header != null:
		_armorer_comparison_header.text = "✦ [%s vs %s]: %s (%d ARM)  ➔  %s (%d ARM)\n✦ SET SYNERGY: %d/5 (+%d%%) ➔ %d/5 (+%d%%)  [3/5: +10%% | 5/5: +25%%]" % [
			sel_slot_name, sel_slot_name,
			String(worn_info.get("name", sel_slot_name)), int(worn_info.get("armor", 6)),
			String(cand_info.get("name", sel_slot_name)), int(cand_info.get("armor", 6)),
			syn_cnt, syn_pct, cand_syn_cnt, cand_syn_pct
		]

	var cand_stats: Dictionary[String, float] = _compute_armorer_candidate_stats()
	if not cand_stats.is_empty():
		for r_i: int in range(ledger_rows.size()):
			var row_info: Dictionary = ledger_rows[r_i]
			var k: String = String(row_info["key"])
			var unit_s: String = String(row_info["unit"])
			var dec: int = int(row_info["decimals"])
			var cur_v: float = float(base_stats.get(k, 0.0))
			var prv_v: float = float(cand_stats.get(k, cur_v))
			var diff: float = prv_v - cur_v
			var val_str: String = ("%.1f%s" % [cur_v, unit_s]) if dec == 1 else ("%d%s" % [roundi(cur_v), unit_s])
			if absf(diff) >= 0.08:
				var is_pos: bool = diff > 0.0
				var sign_s: String = "+" if is_pos else ""
				var arrow_s: String = "▲" if is_pos else "▼"
				var d_str: String = (("%s%.1f%s %s" % [sign_s, diff, unit_s, arrow_s]) if dec == 1 else ("%s%d%s %s" % [sign_s, roundi(diff), unit_s, arrow_s]))
				_stat_val_labels[r_i].text = "%s  (%s)" % [val_str, d_str]
				_stat_val_labels[r_i].add_theme_color_override("font_color", COL_STAT_EMERALD if is_pos else COL_STAT_CRIMSON)
			else:
				_stat_val_labels[r_i].text = val_str
				_stat_val_labels[r_i].add_theme_color_override("font_color", COL_STAT_EMERALD if (r_i % 2 == 0) else COL_STAT_AMBER)


func _get_set_tier_border_color(tier_idx: int) -> Color:
	match posmod(tier_idx, 4):
		0:
			return Color.html("#6e563a")
		1:
			return Color.html("#527da8")
		2:
			return Color.html("#8854b8")
		_:
			return Color.html("#c45b33")


func _refresh_field_character_tab1(base_stats: Dictionary[String, float]) -> void:
	if _active_inv_filter == "ALL":
		_active_inv_filter = "ARMOR"

	# 1. Refresh Left 5 Vertical Armor Strip Sockets (HEAD, CHEST, HANDS, LEGS, FEET)
	var slots: Array[String] = PlayerLoadoutManager.ARMOR_SLOTS
	for s_i: int in range(5):
		if s_i >= _equip_slot_cards.size():
			break
		var s_name: String = slots[s_i]
		var eq_set: int = 0
		if loadout_manager != null and loadout_manager.equipped_armor_slots.has(s_name):
			eq_set = clampi(int(loadout_manager.equipped_armor_slots[s_name]), 0, 3)
		var p_info: Dictionary = (
			loadout_manager.get_armor_piece_info(s_name, eq_set)
			if loadout_manager != null
			else {"name": s_name, "armor": 10, "bonus_text": "Standard Protection"}
		)
		var is_sel_slot: bool = (_selected_equip_slot_index == s_i)
		var border_col: Color = COL_CARD_BORDER_ACTIVE if is_sel_slot else _get_set_tier_border_color(eq_set)
		_equip_slot_cards[s_i].set_meta("bevel_outer_col", border_col)
		_equip_slot_cards[s_i].set_meta("bevel_inner_col", border_col.darkened(0.38))
		_equip_slot_cards[s_i].add_theme_stylebox_override(
			"panel",
			_make_stylebox(Color.html("#181b20") if is_sel_slot else Color.html("#141619"), border_col, 2 if is_sel_slot else 1, 3)
		)
		var bev_n: Control = _equip_slot_cards[s_i].get_node_or_null("DoubleBevelMetallicFrame") as Control
		if bev_n != null:
			bev_n.queue_redraw()
		if s_i < _equip_slot_pill_panels.size() and _equip_slot_pill_panels[s_i] != null:
			_equip_slot_pill_panels[s_i].add_theme_stylebox_override("panel", _make_stylebox(Color.html("#0b0c0f"), border_col, 1, 3))
		if s_i < _equip_slot_icons.size() and _equip_slot_icons[s_i] != null:
			_equip_slot_icons[s_i].texture = _get_or_create_item_thumbnail(s_name, eq_set)
		_equip_slot_titles[s_i].text = "[%s] %s" % [s_name, String(p_info.get("name", s_name))]
		_equip_slot_badges[s_i].text = "+%d" % int(p_info.get("armor", 10))
		_equip_slot_subs[s_i].text = String(p_info.get("bonus_text", ""))
		_equip_slot_subs[s_i].visible = false

	# 2. Refresh Inner-Right Auxiliary Strip Sockets (Spell, Relic Curio, Firearm)
	var wid: String = loadout_manager.active_weapon_id if loadout_manager != null else "revolver"
	var w_slot: int = loadout_manager.get_weapon_slot_index(wid) if loadout_manager != null else 0
	var w_titles: Array[String] = ["Occult Revolver", "Hellfire Coach Gun", "Pneumatic Stake-Driver"]
	var mods_cat: Array[Dictionary] = PlayerLoadoutManager.get_weapon_mod_catalog()
	var m_idx: int = loadout_manager.weapon_mod_indices[clampi(w_slot, 0, 2)] if loadout_manager != null else 0
	var m_info: Dictionary = mods_cat[posmod(m_idx, 4)]

	if _equip_slot_cards.size() >= 7:
		var sel5: bool = (_selected_equip_slot_index == 5)
		var bdr5: Color = COL_CARD_BORDER_ACTIVE if sel5 else _get_set_tier_border_color(w_slot)
		_equip_slot_cards[5].set_meta("bevel_outer_col", bdr5)
		_equip_slot_cards[5].set_meta("bevel_inner_col", bdr5.darkened(0.38))
		_equip_slot_cards[5].add_theme_stylebox_override(
			"panel",
			_make_stylebox(Color.html("#181b20") if sel5 else Color.html("#141619"), bdr5, 2 if sel5 else 1, 3)
		)
		var bev5: Control = _equip_slot_cards[5].get_node_or_null("DoubleBevelMetallicFrame") as Control
		if bev5 != null:
			bev5.queue_redraw()
		if _equip_slot_pill_panels.size() > 5 and _equip_slot_pill_panels[5] != null:
			_equip_slot_pill_panels[5].add_theme_stylebox_override("panel", _make_stylebox(Color.html("#0b0c0f"), bdr5, 1, 3))
		if _equip_slot_icons.size() > 5 and _equip_slot_icons[5] != null:
			_equip_slot_icons[5].texture = _get_or_create_item_thumbnail("FIREARM", w_slot)
		_equip_slot_titles[5].text = "[FIREARM] %s" % w_titles[clampi(w_slot, 0, 2)]
		_equip_slot_badges[5].text = "+%d" % (12 + w_slot * 4)
		_equip_slot_subs[5].text = "Barrel Rite: %s (%s)" % [String(m_info.get("name", "")), String(m_info.get("desc", ""))]
		_equip_slot_subs[5].visible = false

		var spells_cat: Array[Dictionary] = PlayerLoadoutManager.get_lantern_spell_catalog()
		var sp_idx: int = posmod(loadout_manager.equipped_spell_index if loadout_manager != null else 0, 3)
		var sp_info: Dictionary = spells_cat[sp_idx]
		var sel6: bool = (_selected_equip_slot_index == 6)
		var bdr6: Color = COL_CARD_BORDER_ACTIVE if sel6 else _get_set_tier_border_color(sp_idx + 1)
		_equip_slot_cards[6].set_meta("bevel_outer_col", bdr6)
		_equip_slot_cards[6].set_meta("bevel_inner_col", bdr6.darkened(0.38))
		_equip_slot_cards[6].add_theme_stylebox_override(
			"panel",
			_make_stylebox(Color.html("#181b20") if sel6 else Color.html("#141619"), bdr6, 2 if sel6 else 1, 3)
		)
		var bev6: Control = _equip_slot_cards[6].get_node_or_null("DoubleBevelMetallicFrame") as Control
		if bev6 != null:
			bev6.queue_redraw()
		if _equip_slot_pill_panels.size() > 6 and _equip_slot_pill_panels[6] != null:
			_equip_slot_pill_panels[6].add_theme_stylebox_override("panel", _make_stylebox(Color.html("#0b0c0f"), bdr6, 1, 3))
		if _equip_slot_icons.size() > 6 and _equip_slot_icons[6] != null:
			_equip_slot_icons[6].texture = _get_or_create_item_thumbnail("SPELL", sp_idx)
		_equip_slot_titles[6].text = "[SPELL] %s" % String(sp_info.get("name", ""))
		_equip_slot_badges[6].text = "[F]"
		_equip_slot_subs[6].text = String(sp_info.get("desc", ""))
		_equip_slot_subs[6].visible = false

	if _aux_relic_socket_card != null:
		var sel_rel: bool = (_active_inv_filter == "RELICS" and _selected_equip_slot_index == 7)
		var bdr_rel: Color = COL_CARD_BORDER_ACTIVE if sel_rel else _get_set_tier_border_color(2)
		_aux_relic_socket_card.set_meta("bevel_outer_col", bdr_rel)
		_aux_relic_socket_card.set_meta("bevel_inner_col", bdr_rel.darkened(0.38))
		_aux_relic_socket_card.add_theme_stylebox_override(
			"panel",
			_make_stylebox(Color.html("#181b20") if sel_rel else Color.html("#141619"), bdr_rel, 2 if sel_rel else 1, 3)
		)
		var bev_r: Control = _aux_relic_socket_card.get_node_or_null("DoubleBevelMetallicFrame") as Control
		if bev_r != null:
			bev_r.queue_redraw()
		if _aux_relic_pill_panel != null:
			_aux_relic_pill_panel.add_theme_stylebox_override("panel", _make_stylebox(Color.html("#0b0c0f"), bdr_rel, 1, 3))
		if _aux_relic_socket_icon != null:
			_aux_relic_socket_icon.texture = _get_or_create_item_thumbnail("RELIC", 0)
		if _aux_relic_socket_badge != null:
			_aux_relic_socket_badge.text = "+1"

	# 3. Refresh Far-Right Vertical Stat Pillar (Crimson Ribbon Banner, 4 Medallions, 3 Affinities, Footer)
	var syn_info: Dictionary = (
		loadout_manager.get_active_armor_set_bonus_info()
		if loadout_manager != null
		else {"max_matching_count": 5, "dominant_set_index": 0, "bonus_mult": 1.25}
	)
	var dom_set: int = clampi(int(syn_info.get("dominant_set_index", 0)), 0, 3)
	var match_cnt: int = int(syn_info.get("max_matching_count", 5))
	var b_pct: int = roundi((float(syn_info.get("bonus_mult", 1.0)) - 1.0) * 100.0)
	var armor_sets_cat: Array[Dictionary] = PlayerLoadoutManager.get_armor_set_catalog()
	var syn_label_str: String = "%s: %d/5 Active (+%d%% Set Bonus)" % [String(armor_sets_cat[dom_set]["name"]), match_cnt, b_pct]
	if _set_synergy_label != null:
		_set_synergy_label.text = "✦ SET SYNERGY: %s" % syn_label_str

	var lvl_val: int = int(loadout_manager.get("hunter_level")) if (loadout_manager != null and "hunter_level" in loadout_manager) else 1
	var xp_val: int = int(loadout_manager.get("current_xp")) if (loadout_manager != null and "current_xp" in loadout_manager) else 0
	var sp_val: int = loadout_manager.skill_points if loadout_manager != null else 3
	_pillar_xp_ratio = clampf(float(xp_val) / 100.0, 0.32, 1.0)
	if _pillar_xp_bar_canvas != null:
		_pillar_xp_bar_canvas.queue_redraw()
	if _pillar_level_label != null:
		_pillar_level_label.text = "LEVEL %d" % maxi(1, lvl_val)
	if _pillar_xp_label != null:
		_pillar_xp_label.text = "XP: %d / 100  •  %d SP" % [xp_val, sp_val]

	var rite_short: String = String(m_info.get("name", "Silver-Core")).replace(" Rounds", "").replace(" Rite", "")
	if _pillar_medallion_vals.size() >= 3:
		_pillar_medallion_vals[0].text = "%d%% / %d%% Crit" % [
			roundi(float(base_stats.get("firearm_damage_pct", 108.0))),
			roundi(float(base_stats.get("crit_multiplier_pct", 238.0)))
		]
		var disp_arm: int = maxi(60, roundi(float(base_stats.get("max_armor", 60.0))))
		var disp_vit: int = maxi(183, roundi(float(base_stats.get("max_vitality", 183.0))))
		_pillar_medallion_vals[1].text = "%d ARM" % disp_arm
		_pillar_medallion_vals[2].text = "%d Vitality" % disp_vit
		if _pillar_medallion_vals.size() >= 4:
			_pillar_medallion_vals[3].text = "%s (%d/5)" % [rite_short, match_cnt]

	if _pillar_affinity_vals.size() >= 3:
		_pillar_affinity_vals[0].text = "%d/5 Active" % match_cnt
		_pillar_affinity_vals[1].text = "%d%%" % roundi(float(base_stats.get("quickstep_speed_pct", 122.0)))
		_pillar_affinity_vals[2].text = rite_short

	var sil_v: int = loadout_manager.get_resource_amount("silver") if loadout_manager != null else 35
	var ash_v: int = loadout_manager.get_resource_amount("bone_ash") if loadout_manager != null else 15
	var irn_v: int = loadout_manager.get_resource_amount("cursed_iron") if loadout_manager != null else 0
	var cor_v: int = loadout_manager.get_resource_amount("soul_cores") if loadout_manager != null else 0
	if _pillar_currency_label != null:
		_pillar_currency_label.text = "%d Silver | %d Ash | %d Iron | %d Core" % [sil_v, ash_v, irn_v, cor_v]

	# 4. Refresh Lower Zone Category Tab Bar & 2D Tile Stash Grid
	var f_ids: Array[String] = ["ARMOR", "WEAPONS", "RELICS", "MATERIALS"]
	for f_i: int in range(mini(_inv_filter_buttons.size(), f_ids.size())):
		var is_f_act: bool = (_active_inv_filter == f_ids[f_i])
		_apply_button_theme(
			_inv_filter_buttons[f_i],
			COL_BTN_BG_HOVER if is_f_act else COL_BTN_BG,
			COL_CARD_BORDER_ACTIVE if is_f_act else COL_BTN_BORDER,
			COL_HEADER_GOLD if is_f_act else COL_BTN_FONT
		)

	_rebuild_inventory_vault_list()
	if paperdoll_rig != null and is_instance_valid(paperdoll_rig):
		paperdoll_rig.refresh_from_loadout(loadout_manager)


func _show_floating_tooltip(
	icon_tex: Texture2D,
	item_title: String,
	set_tier_text: String,
	primary_stat_text: String,
	substats_text: String,
	synergy_text: String,
	hint_text: String
) -> void:
	if _floating_tooltip == null or not is_instance_valid(_floating_tooltip):
		return
	if _tooltip_icon != null:
		_tooltip_icon.texture = icon_tex
	if _tooltip_title_label != null:
		_tooltip_title_label.text = item_title
	if _tooltip_tier_label != null:
		_tooltip_tier_label.text = set_tier_text
	if _tooltip_primary_stat_label != null:
		_tooltip_primary_stat_label.text = primary_stat_text
	if _tooltip_substats_label != null:
		_tooltip_substats_label.text = substats_text
		_tooltip_substats_label.visible = not substats_text.is_empty()
	if _tooltip_synergy_label != null:
		_tooltip_synergy_label.text = synergy_text
		_tooltip_synergy_label.visible = not synergy_text.is_empty()
	if _tooltip_hint_label != null:
		_tooltip_hint_label.text = hint_text
	_floating_tooltip.visible = true
	_floating_tooltip.reset_size()
	_update_floating_tooltip_position()


func _hide_floating_tooltip() -> void:
	if _floating_tooltip != null and is_instance_valid(_floating_tooltip):
		_floating_tooltip.visible = false


func _update_floating_tooltip_position() -> void:
	if _floating_tooltip == null or not is_instance_valid(_floating_tooltip) or not _floating_tooltip.visible:
		return
	var vp: Vector2 = _get_viewport_size()
	var m_pos: Vector2 = get_local_mouse_position()
	var tt_sz: Vector2 = _floating_tooltip.size
	if tt_sz.x < 200.0:
		tt_sz = Vector2(310.0, 150.0)
	var target_pos: Vector2 = m_pos + Vector2(18.0, 14.0)
	if target_pos.x + tt_sz.x > vp.x - 16.0:
		target_pos.x = maxf(16.0, m_pos.x - tt_sz.x - 16.0)
	if target_pos.y + tt_sz.y > vp.y - 16.0:
		target_pos.y = maxf(16.0, vp.y - tt_sz.y - 16.0)
	_floating_tooltip.position = target_pos


func _on_aux_relic_socket_hovered() -> void:
	var r_info: Dictionary = RELIC_CATALOG_LORE[0]
	var tex: Texture2D = _get_or_create_item_thumbnail("RELIC", 0)
	_show_floating_tooltip(
		tex,
		String(r_info["name"]),
		"Sanctified Relic Curio  •  Tier I",
		"PASSIVE RELIC EFFECT",
		String(r_info["lore"]),
		"Reliquary Resonance: Active while carried in pouch",
		"Click to Filter Relics"
	)


func _on_left_equip_slot_hovered(slot_idx: int) -> void:
	_resolve_loadout_manager()
	if slot_idx >= 0 and slot_idx < 5:
		var s_name: String = PlayerLoadoutManager.ARMOR_SLOTS[slot_idx]
		var eq_set: int = int(loadout_manager.equipped_armor_slots.get(s_name, 0)) if loadout_manager != null else 0
		var p_info: Dictionary = loadout_manager.get_armor_piece_info(s_name, eq_set) if loadout_manager != null else {}
		var p_name: String = String(p_info.get("name", s_name))
		var set_name: String = String(p_info.get("set_name", "Armor Set"))
		var arm_v: int = int(p_info.get("armor", 6))
		var passive_s: String = String(p_info.get("passive_bonus", String(p_info.get("bonus_text", ""))))
		var syn_info: Dictionary = loadout_manager.get_active_armor_set_bonus_info() if loadout_manager != null else {"max_matching_count": 5, "bonus_mult": 1.25}
		var match_cnt: int = int(syn_info.get("max_matching_count", 5))
		var b_pct: int = roundi((float(syn_info.get("bonus_mult", 1.0)) - 1.0) * 100.0)
		var tex: Texture2D = _get_or_create_item_thumbnail(s_name, eq_set)
		_set_inspector_text("✦ [%s] %s" % [s_name, p_name], "%s  |  +%d ARM  |  %s" % [set_name, arm_v, passive_s])
		_show_floating_tooltip(
			tex,
			p_name,
			"%s  •  [%s SLOT]" % [set_name, s_name],
			"+%d ARMOR" % arm_v,
			passive_s.replace(" | ", "\n"),
			"Set Synergy (%d/5 Active): +%d%% Set Bonus" % [match_cnt, b_pct],
			"Equipped  •  Click to Filter %s" % s_name
		)
	elif slot_idx == 5:
		var wid: String = loadout_manager.active_weapon_id if loadout_manager != null else "revolver"
		var w_slot: int = loadout_manager.get_weapon_slot_index(wid) if loadout_manager != null else 0
		var w_titles: Array[String] = ["Occult Revolver", "Hellfire Coach Gun", "Pneumatic Stake-Driver"]
		var mods_cat: Array[Dictionary] = PlayerLoadoutManager.get_weapon_mod_catalog()
		var m_idx: int = loadout_manager.weapon_mod_indices[clampi(w_slot, 0, 2)] if loadout_manager != null else 0
		var m_info: Dictionary = mods_cat[posmod(m_idx, 4)]
		var tex5: Texture2D = _get_or_create_item_thumbnail("FIREARM", w_slot)
		_show_floating_tooltip(
			tex5,
			w_titles[clampi(w_slot, 0, 2)],
			"Consecrated Hunter Firearm  •  Tier %d" % (w_slot + 1),
			"108% ATTACK POWER",
			"Barrel Rite: %s\n%s" % [String(m_info.get("name", "")), String(m_info.get("desc", ""))],
			"Alchemical Chambering Active",
			"Equipped  •  Click to View Arsenal"
		)
	elif slot_idx == 6:
		var spells_cat: Array[Dictionary] = PlayerLoadoutManager.get_lantern_spell_catalog()
		var sp_idx: int = posmod(loadout_manager.equipped_spell_index if loadout_manager != null else 0, 3)
		var sp_info: Dictionary = spells_cat[sp_idx]
		var tex6: Texture2D = _get_or_create_item_thumbnail("SPELL", sp_idx)
		_show_floating_tooltip(
			tex6,
			String(sp_info.get("name", "Searing Pyre")),
			"Weeper's Lantern Consecration  •  [F] Active",
			"OCCULT LANTERN RITE",
			String(sp_info.get("desc", "")),
			"Scales with Eldritch Reliquary Constellation",
			"Equipped  •  Click to View Arsenal"
		)


func _on_left_equip_slot_clicked(slot_idx: int) -> void:
	_selected_equip_slot_index = slot_idx
	_play_ui_sfx(_sfx_tab_turn)
	if slot_idx >= 0 and slot_idx < 5:
		var s_name: String = PlayerLoadoutManager.ARMOR_SLOTS[slot_idx]
		_active_inv_filter = "ARMOR"
		_active_slot_subfilter = s_name
		_on_left_equip_slot_hovered(slot_idx)
	elif slot_idx == 5 or slot_idx == 6:
		_active_inv_filter = "WEAPONS"
		_active_slot_subfilter = ""
		_on_left_equip_slot_hovered(slot_idx)
	_refresh_all_ui_elements()


func _on_inventory_filter_selected(filter_id: String, slot_subfilter: String) -> void:
	_active_inv_filter = filter_id
	_active_slot_subfilter = slot_subfilter
	if slot_subfilter.is_empty():
		_selected_equip_slot_index = -1
	_play_ui_sfx(_sfx_tab_turn)
	_refresh_all_ui_elements()


func _on_equip_armor_piece_pressed(slot_name: String, set_idx: int) -> void:
	_resolve_loadout_manager()
	if loadout_manager != null:
		loadout_manager.equip_armor_slot(slot_name, set_idx)
	if paperdoll_rig != null and is_instance_valid(paperdoll_rig):
		paperdoll_rig.refresh_from_loadout(loadout_manager)
	_play_ui_sfx(_sfx_armor_clank)
	_refresh_all_ui_elements()


func _set_inspector_text(title: String, body: String) -> void:
	if _inv_inspector_title != null:
		_inv_inspector_title.text = title
	if _inv_inspector_body != null:
		_inv_inspector_body.text = body


func _create_stash_tile_cell(
	cell_name: String,
	icon_tex: Texture2D,
	is_equipped: bool,
	is_highlighted_slot: bool,
	tier_idx: int,
	badge_text: String,
	on_click: Callable,
	on_hover: Callable
) -> Panel:
	var cell: Panel = Panel.new()
	cell.name = cell_name
	cell.custom_minimum_size = Vector2(64.0, 64.0)
	cell.size = Vector2(64.0, 64.0)
	cell.mouse_filter = Control.MOUSE_FILTER_STOP
	var is_empty: bool = (icon_tex == null)
	var bg_col: Color = Color.html("#121316") if is_empty else (Color.html("#191d22") if is_equipped else Color.html("#141619"))
	var bdr_col: Color = Color.html("#22242a")
	var bdr_w: int = 1
	if not is_empty:
		bdr_col = _get_set_tier_border_color(tier_idx)
		if is_highlighted_slot:
			bdr_col = COL_CARD_BORDER_ACTIVE
			bdr_w = 2
		elif is_equipped:
			bdr_col = COL_HEADER_GOLD
			bdr_w = 2
	cell.set_meta("bevel_outer_col", bdr_col)
	cell.set_meta("bevel_inner_col", Color.html("#22242a") if is_empty else bdr_col.darkened(0.38))
	cell.add_theme_stylebox_override("panel", _make_stylebox(bg_col, bdr_col, bdr_w, 3))

	if not is_empty:
		var t_rect: TextureRect = TextureRect.new()
		t_rect.name = "TileIcon"
		t_rect.texture = icon_tex
		t_rect.position = Vector2(4.0, 4.0)
		t_rect.size = Vector2(56.0, 56.0)
		t_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		t_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		t_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
		cell.add_child(t_rect)

	_attach_double_bevel_socket_frame(cell, is_empty)

	if not is_empty:
		if is_equipped:
			var chk_bg: Panel = Panel.new()
			chk_bg.name = "EquippedCheckBadge"
			chk_bg.position = Vector2(4.0, 4.0)
			chk_bg.size = Vector2(17.0, 17.0)
			chk_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
			chk_bg.add_theme_stylebox_override("panel", _make_stylebox(Color(0.08, 0.07, 0.05, 0.95), COL_HEADER_GOLD, 1, 2))
			cell.add_child(chk_bg)
			var chk_lbl: Label = _make_label("CheckLbl", "✓", 11, COL_HEADER_GOLD, HORIZONTAL_ALIGNMENT_CENTER)
			chk_lbl.position = Vector2.ZERO
			chk_lbl.size = Vector2(17.0, 17.0)
			chk_bg.add_child(chk_lbl)

		if not badge_text.is_empty():
			var b_bg: Panel = Panel.new()
			b_bg.name = "TileArmorValuePill"
			b_bg.position = Vector2(26.0, 43.0)
			b_bg.size = Vector2(34.0, 17.0)
			b_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
			b_bg.add_theme_stylebox_override("panel", _make_stylebox(Color.html("#0b0c0f"), bdr_col, 1, 3))
			cell.add_child(b_bg)
			var b_lbl: Label = _make_label("TileCornerBadge", badge_text, 10, COL_BODY_IVORY, HORIZONTAL_ALIGNMENT_CENTER)
			b_lbl.position = Vector2.ZERO
			b_lbl.size = Vector2(34.0, 17.0)
			b_bg.add_child(b_lbl)

		cell.mouse_entered.connect(on_hover)
		cell.mouse_exited.connect(func() -> void: _hide_floating_tooltip())
		cell.gui_input.connect(func(ev: InputEvent) -> void:
			if ev is InputEventMouseButton:
				var mb: InputEventMouseButton = ev as InputEventMouseButton
				if mb.button_index == MOUSE_BUTTON_LEFT and mb.pressed and on_click.is_valid():
					on_click.call()
		)
	return cell


func _rebuild_inventory_vault_list() -> void:
	if _stash_grid == null or not is_instance_valid(_stash_grid):
		return
	for ch: Node in _stash_grid.get_children():
		_stash_grid.remove_child(ch)
		ch.queue_free()

	var eff_filter: String = _active_inv_filter if _active_inv_filter != "ALL" else "ARMOR"
	var spawned_cells: int = 0
	var syn_info: Dictionary = loadout_manager.get_active_armor_set_bonus_info() if loadout_manager != null else {"max_matching_count": 5, "bonus_mult": 1.25}
	var match_cnt: int = int(syn_info.get("max_matching_count", 5))
	var b_pct: int = roundi((float(syn_info.get("bonus_mult", 1.0)) - 1.0) * 100.0)

	# 1. Equipment Tab (Unlocked Armor Pieces across all 5 slots & 4 sets; highlights matching slot if filtered)
	if eff_filter == "ARMOR":
		for set_i: int in range(4):
			for s_name: String in PlayerLoadoutManager.ARMOR_SLOTS:
				var unlocked_p: bool = loadout_manager.is_armor_piece_unlocked(s_name, set_i) if loadout_manager != null else (set_i == 0)
				if not unlocked_p:
					continue
				var eq_set_for_slot: int = int(loadout_manager.equipped_armor_slots.get(s_name, 0)) if loadout_manager != null else 0
				var p_info: Dictionary = loadout_manager.get_armor_piece_info(s_name, set_i) if loadout_manager != null else {}
				var p_name: String = String(p_info.get("name", s_name))
				var set_name: String = String(p_info.get("set_name", "Armor Set"))
				var arm_v: int = int(p_info.get("armor", 6))
				var passive_s: String = String(p_info.get("passive_bonus", String(p_info.get("bonus_text", ""))))
				var is_eq: bool = (eq_set_for_slot == set_i)
				var is_hl: bool = (not _active_slot_subfilter.is_empty() and _active_slot_subfilter == s_name)
				var cap_slot: String = s_name
				var cap_set: int = set_i
				var tex: Texture2D = _get_or_create_item_thumbnail(s_name, set_i)
				var tile: Panel = _create_stash_tile_cell(
					"StashArmor_%s_%d" % [s_name, set_i],
					tex,
					is_eq,
					is_hl,
					set_i,
					"+%d" % arm_v,
					func() -> void: _on_equip_armor_piece_pressed(cap_slot, cap_set),
					func() -> void:
						_show_floating_tooltip(
							tex,
							p_name,
							"%s  •  [%s SLOT]" % [set_name, cap_slot],
							"+%d ARMOR" % arm_v,
							passive_s.replace(" | ", "\n"),
							"Set Synergy (%d/5 Active): +%d%% Set Bonus" % [match_cnt, b_pct],
							"Currently Equipped" if is_eq else "Click to Equip"
						)
				)
				_stash_grid.add_child(tile)
				spawned_cells += 1

	# 2. Arsenal Tab (Unlocked Firearms & Lantern Consecration Spells)
	elif eff_filter == "WEAPONS":
		var w_titles: Array[String] = ["Occult Revolver", "Hellfire Coach Gun", "Pneumatic Stake-Driver"]
		var mods_cat: Array[Dictionary] = PlayerLoadoutManager.get_weapon_mod_catalog()
		for w_i: int in range(3):
			var w_unl: bool = loadout_manager.is_weapon_unlocked(w_i) if loadout_manager != null else (w_i == 0)
			if not w_unl:
				continue
			var wid: String = loadout_manager.get_weapon_id_from_slot(w_i) if loadout_manager != null else "revolver"
			var is_w_eq: bool = (loadout_manager != null and loadout_manager.active_weapon_id == wid)
			var eq_m: int = loadout_manager.weapon_mod_indices[w_i] if loadout_manager != null else 0
			var m_info: Dictionary = mods_cat[posmod(eq_m, 4)]
			var cap_w: int = w_i
			var w_tex: Texture2D = _get_or_create_item_thumbnail("FIREARM", w_i)
			var w_tile: Panel = _create_stash_tile_cell(
				"StashWeapon_%d" % w_i,
				w_tex,
				is_w_eq,
				_selected_equip_slot_index == 5,
				w_i,
				"+%d" % (12 + w_i * 4),
				func() -> void: _on_weapon_button_pressed(cap_w),
				func() -> void:
					_show_floating_tooltip(
						w_tex,
						w_titles[cap_w],
						"Consecrated Firearm  •  Tier %d" % (cap_w + 1),
						"108% ATTACK POWER",
						"Barrel Rite: %s\n%s" % [String(m_info.get("name", "")), String(m_info.get("desc", ""))],
						"Alchemical Chambering Active",
						"Currently Equipped" if is_w_eq else "Click to Equip"
					)
			)
			_stash_grid.add_child(w_tile)
			spawned_cells += 1

		var spells_cat: Array[Dictionary] = PlayerLoadoutManager.get_lantern_spell_catalog()
		var eq_sp: int = loadout_manager.equipped_spell_index if loadout_manager != null else 0
		for sp_i: int in range(3):
			var sp_unl: bool = loadout_manager.is_spell_unlocked(sp_i) if loadout_manager != null else (sp_i == 0)
			if not sp_unl:
				continue
			var sp_info: Dictionary = spells_cat[sp_i]
			var is_sp_eq: bool = (eq_sp == sp_i)
			var cap_sp: int = sp_i
			var sp_tex: Texture2D = _get_or_create_item_thumbnail("SPELL", sp_i)
			var sp_tile: Panel = _create_stash_tile_cell(
				"StashSpell_%d" % sp_i,
				sp_tex,
				is_sp_eq,
				_selected_equip_slot_index == 6,
				sp_i + 1,
				"[F]",
				func() -> void: select_lantern_spell(cap_sp),
				func() -> void:
					_show_floating_tooltip(
						sp_tex,
						String(sp_info["name"]),
						"Weeper's Lantern Spell  •  [F] Active",
						"OCCULT LANTERN RITE",
						String(sp_info["desc"]),
						"Scales with Eldritch Reliquary Constellation",
						"Currently Equipped" if is_sp_eq else "Click to Equip"
					)
			)
			_stash_grid.add_child(sp_tile)
			spawned_cells += 1

	# 3. Relics Tab (Collected Reliquary Curios)
	elif eff_filter == "RELICS":
		for rel_i: int in range(RELIC_CATALOG_LORE.size()):
			var rel_id: int = rel_i + 1
			var owned: bool = (loadout_manager != null and loadout_manager.has_relic(rel_id)) or (rel_i == 0)
			if not owned:
				continue
			var r_info: Dictionary = RELIC_CATALOG_LORE[rel_i]
			var r_tex: Texture2D = _get_or_create_item_thumbnail("RELIC", rel_i % 4)
			var r_tile: Panel = _create_stash_tile_cell(
				"StashRelic_%d" % rel_id,
				r_tex,
				true,
				false,
				(rel_i + 1) % 4,
				"✦%d" % rel_id,
				Callable(),
				func() -> void:
					_show_floating_tooltip(
						r_tex,
						String(r_info["name"]),
						"Sanctified Relic Curio  •  Reliquary #" + str(rel_id),
						"PASSIVE CURIO RESONANCE",
						String(r_info["lore"]),
						"Active while carried in Reliquary Pouch",
						"Passive Effect Active"
					)
			)
			_stash_grid.add_child(r_tile)
			spawned_cells += 1

	# 4. Materials Tab (Silver Shillings, Bone Ash, Cursed Iron, Soul Cores)
	elif eff_filter == "MATERIALS":
		var mat_defs: Array[Dictionary] = [
			{"name": "Silver Shillings", "tier": 0, "amt": loadout_manager.get_resource_amount("silver") if loadout_manager != null else 35, "desc": "Stamped sanctuary silver used at the Gunsmith Workbench."},
			{"name": "Sanctified Bone Ash", "tier": 1, "amt": loadout_manager.get_resource_amount("bone_ash") if loadout_manager != null else 15, "desc": "Calcined martyr ash used to consecrate Barrel Rites & Armor."},
			{"name": "Cursed Tomb-Iron", "tier": 2, "amt": loadout_manager.get_resource_amount("cursed_iron") if loadout_manager != null else 0, "desc": "Quenched catacomb iron required for heavy gothic plate forging."},
			{"name": "Eldritch Soul Cores", "tier": 3, "amt": loadout_manager.get_resource_amount("soul_cores") if loadout_manager != null else 0, "desc": "Crystallized abyssal essence required for masterwork rites."}
		]
		for m_i: int in range(mat_defs.size()):
			var md: Dictionary = mat_defs[m_i]
			var m_tex: Texture2D = _get_or_create_item_thumbnail("MATERIAL", int(md["tier"]))
			var m_amt: int = int(md["amt"])
			var m_tile: Panel = _create_stash_tile_cell(
				"StashMat_%d" % m_i,
				m_tex,
				false,
				false,
				int(md["tier"]),
				"x%d" % m_amt,
				Callable(),
				func() -> void:
					_show_floating_tooltip(
						m_tex,
						String(md["name"]),
						"Alchemical Crafting Material",
						"QUANTITY: %d" % m_amt,
						String(md["desc"]),
						"Used at Sanctuary Forge Stations",
						"Crafting Resource"
					)
			)
			_stash_grid.add_child(m_tile)
			spawned_cells += 1

	# Pad empty dark-slate lattice cells so minimum total cells >= 30 (3 rows x 10 columns)
	var min_cells: int = maxi(30, int(ceilf(float(spawned_cells) / 10.0)) * 10)
	while spawned_cells < min_cells:
		var empty_cell: Panel = _create_stash_tile_cell(
			"EmptyStashCell_%d" % spawned_cells,
			null,
			false,
			false,
			0,
			"",
			Callable(),
			Callable()
		)
		_stash_grid.add_child(empty_cell)
		spawned_cells += 1


func _refresh_tab2_elements() -> void:
	var catalog: Dictionary[String, Dictionary] = PlayerLoadoutManager.get_skill_tree_catalog()
	var node_ids: Array[String] = PlayerLoadoutManager.get_skill_node_ids()
	var romans: Array[String] = ["I", "I", "II", "III", "IV"]

	for sid: String in node_ids:
		if not _skill_node_buttons.has(sid):
			continue
		var s_btn: Button = _skill_node_buttons[sid]
		var info: Dictionary = catalog[sid]
		var tier: int = int(info.get("tier", 1))
		var const_idx: int = int(info.get("constellation", 0))
		var badge_txt: String = "SYN" if const_idx == 4 else romans[clampi(tier, 1, 4)]

		var is_unlocked: bool = loadout_manager != null and loadout_manager.is_skill_unlocked(sid)
		var is_avail: bool = loadout_manager != null and loadout_manager.can_unlock_skill(sid)
		var is_sel: bool = (selected_skill_id == sid) or (hovered_skill_id == sid)

		if is_unlocked:
			s_btn.text = "✓ " + badge_txt
			_apply_button_theme(s_btn, COL_BTN_BG_ACTIVE, COL_STAT_EMERALD, COL_HEADER_GOLD)
		elif is_avail:
			s_btn.text = "✦ " + badge_txt
			_apply_button_theme(s_btn, COL_BTN_BG_HOVER if is_sel else COL_BTN_BG, COL_CARD_BORDER_ACTIVE, COL_BTN_FONT)
		else:
			s_btn.text = badge_txt
			_apply_button_theme(s_btn, COL_BTN_BG, COL_CARD_BORDER_ACTIVE if is_sel else COL_BTN_BORDER, COL_BTN_FONT)

		if _skill_tier_labels.has(sid):
			var st_lbl: Label = _skill_tier_labels[sid]
			st_lbl.add_theme_color_override(
				"font_color",
				COL_STAT_EMERALD if is_unlocked else (COL_HEADER_GOLD if (is_avail or is_sel) else COL_BODY_IVORY)
			)

	var active_id: String = hovered_skill_id if not hovered_skill_id.is_empty() else selected_skill_id
	if not catalog.has(active_id):
		active_id = "blood_1"
	var s_info: Dictionary = catalog[active_id]
	var cost: int = int(s_info.get("cost", 1))
	var is_s_unlocked: bool = loadout_manager != null and loadout_manager.is_skill_unlocked(active_id)
	var prereqs_ok: bool = loadout_manager != null and loadout_manager.are_skill_prereqs_met(active_id)
	var can_unlock: bool = loadout_manager != null and loadout_manager.can_unlock_skill(active_id)

	var prereq_names: Array[String] = []
	var prereqs: Array = s_info.get("prereqs", []) as Array
	for pre_var: Variant in prereqs:
		var pid: String = String(pre_var)
		if catalog.has(pid):
			prereq_names.append(String(catalog[pid]["title"]))
	var prereq_str: String = "None (Root Constellation Rite)" if prereq_names.is_empty() else ", ".join(prereq_names)

	if _skill_title_label != null:
		_skill_title_label.text = "❖ %s  —  [%s]" % [String(s_info["title"]).to_upper(), String(s_info["subtitle"])]
	if _skill_lore_label != null:
		_skill_lore_label.text = String(s_info["lore_quote"])
	if _skill_effect_label != null:
		_skill_effect_label.text = "SANCTIFIED EFFECT:  " + String(s_info["desc"])
	if _skill_prereq_label != null:
		_skill_prereq_label.text = "PREREQUISITE RITES:  %s   |   COST: %d SOUL POINTS (SP)" % [prereq_str, cost]
		_skill_prereq_label.add_theme_color_override("font_color", COL_STAT_EMERALD if prereqs_ok else COL_STAT_AMBER)

	if _consecrate_rite_button != null:
		if is_s_unlocked:
			_consecrate_rite_button.text = "[ ✓ RITE CONSECRATED ]"
			_apply_button_theme(_consecrate_rite_button, COL_BTN_BG_ACTIVE, COL_STAT_EMERALD, COL_HEADER_GOLD)
		elif can_unlock:
			_consecrate_rite_button.text = "[ ❖ CONSECRATE RITE (%d SP) ❖ ]" % cost
			_apply_button_theme(_consecrate_rite_button, COL_BTN_BG_HOVER, COL_CARD_BORDER_ACTIVE, COL_BTN_FONT)
		else:
			_consecrate_rite_button.text = "[ CONSECRATE RITE (%d SP) ]" % cost
			_apply_button_theme(_consecrate_rite_button, COL_BTN_BG, COL_BTN_BORDER, COL_BTN_FONT)


# ==============================================================================================
# BUTTON & INTERACTION CALLBACKS
# ==============================================================================================
func _on_armor_card_hovered(arm_idx: int) -> void:
	if hovered_armor_index != arm_idx:
		hovered_armor_index = arm_idx
		refresh_3d_pedestal_models(arm_idx, preview_weapon_id)
		_refresh_all_ui_elements()


func _on_armor_button_pressed(arm_idx: int) -> void:
	_resolve_loadout_manager()
	if loadout_manager != null and not loadout_manager.is_armor_unlocked(arm_idx):
		var burst_pt: Vector2 = _armor_forge_btn_rects[arm_idx].get_center() if arm_idx < _armor_forge_btn_rects.size() else Vector2(320.0, 420.0)
		if is_forge_available() and loadout_manager.can_afford(loadout_manager.get_item_recipe("armor", arm_idx)):
			forge_and_unlock_item("armor", arm_idx, 0, burst_pt)
			return
	select_armor_plaque(arm_idx)


func _on_weapon_button_pressed(w_slot: int) -> void:
	_resolve_loadout_manager()
	var w_clamped: int = clampi(w_slot, 0, 2)
	if loadout_manager != null:
		var wid: String = loadout_manager.get_weapon_id_from_slot(w_clamped)
		if not loadout_manager.is_weapon_unlocked(w_clamped):
			var burst_pt: Vector2 = _weapon_forge_btn_rects[w_clamped].get_center() if w_clamped < _weapon_forge_btn_rects.size() else Vector2(820.0, 520.0)
			if is_forge_available() and loadout_manager.can_afford(loadout_manager.get_item_recipe("weapon", w_clamped)):
				forge_and_unlock_item("weapon", w_clamped, 0, burst_pt)
				return
			loadout_manager.notify_locked_forge_required()
			refresh_3d_pedestal_models(preview_armor_index, wid)
			_play_ui_sfx(_sfx_armor_clank)
			_refresh_all_ui_elements()
			return
		loadout_manager.equip_weapon(wid)
		refresh_3d_pedestal_models(preview_armor_index, wid)
		_play_ui_sfx(_sfx_tab_turn)
		_refresh_all_ui_elements()


func _on_skill_node_button_pressed(sid: String) -> void:
	var now_ms: int = Time.get_ticks_msec()
	var is_double_or_selected: bool = (selected_skill_id == sid) or (_last_click_skill_id == sid and (now_ms - _last_click_time_ms) < 550)
	_last_click_skill_id = sid
	_last_click_time_ms = now_ms
	select_skill_node(sid, is_double_or_selected)


func _resolve_loadout_manager() -> void:
	if loadout_manager != null and is_instance_valid(loadout_manager):
		_connect_loadout_signals()
		return

	var cur: Node = self
	while cur != null:
		if cur is GothicHudOverhaul:
			var hud_o: GothicHudOverhaul = cur as GothicHudOverhaul
			if hud_o.viewmodel_controller != null and hud_o.viewmodel_controller.loadout_manager != null:
				loadout_manager = hud_o.viewmodel_controller.loadout_manager
				break
		var found: Node = cur.find_child("PlayerLoadoutManager", true, false)
		if found is PlayerLoadoutManager:
			loadout_manager = found as PlayerLoadoutManager
			break
		cur = cur.get_parent()

	if loadout_manager == null and is_inside_tree() and get_tree() != null:
		var p_node: Node = get_tree().get_first_node_in_group("player")
		if p_node != null:
			loadout_manager = p_node.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager

	_connect_loadout_signals()


func _connect_loadout_signals() -> void:
	if loadout_manager == null or not is_instance_valid(loadout_manager):
		return
	if not loadout_manager.loadout_changed.is_connected(_on_loadout_changed):
		loadout_manager.loadout_changed.connect(_on_loadout_changed)
	if not loadout_manager.crafting_resources_changed.is_connected(_on_crafting_resources_changed):
		loadout_manager.crafting_resources_changed.connect(_on_crafting_resources_changed)
	if not loadout_manager.skill_unlocked.is_connected(_on_skill_unlocked):
		loadout_manager.skill_unlocked.connect(_on_skill_unlocked)
	if not loadout_manager.skills_respecced.is_connected(_on_skills_respecced):
		loadout_manager.skills_respecced.connect(_on_skills_respecced)


func _on_crafting_resources_changed() -> void:
	if not visible and not is_menu_open:
		_is_dirty = true
		return
	_refresh_all_ui_elements()
	queue_redraw()


func _on_loadout_changed() -> void:
	if not visible and not is_menu_open:
		_is_dirty = true
		return
	if loadout_manager != null:
		var target_armor: int = hovered_armor_index if hovered_armor_index >= 0 else loadout_manager.equipped_armor_index
		refresh_3d_pedestal_models(target_armor, loadout_manager.active_weapon_id)
	_refresh_all_ui_elements()
	queue_redraw()


func _on_skill_unlocked(skill_id: String) -> void:
	_wax_seal_scales[skill_id] = 2.2
	if not visible and not is_menu_open:
		_is_dirty = true
		return
	_spawn_skill_unlock_vfx(skill_id)
	_refresh_all_ui_elements()
	queue_redraw()


func _on_skills_respecced() -> void:
	_wax_seal_scales.clear()
	if not visible and not is_menu_open:
		_is_dirty = true
		return
	_refresh_all_ui_elements()
	queue_redraw()


func _compute_local_mesh_aabb(root_node: Node3D, cur_node: Node, accum_xform: Transform3D, state: Dictionary) -> void:
	if cur_node is MeshInstance3D:
		var mi: MeshInstance3D = cur_node as MeshInstance3D
		if mi.mesh != null:
			var m_aabb: AABB = accum_xform * mi.get_aabb()
			if not bool(state.get("has_aabb", false)):
				state["aabb"] = m_aabb
				state["has_aabb"] = true
			else:
				var prev_aabb: AABB = state["aabb"] as AABB
				state["aabb"] = prev_aabb.merge(m_aabb)
	for child: Node in cur_node.get_children():
		var next_xform: Transform3D = accum_xform
		if child is Node3D and child != root_node:
			next_xform = accum_xform * (child as Node3D).transform
		_compute_local_mesh_aabb(root_node, child, next_xform, state)


func _frame_pedestal_model(inst: Node3D, target_center: Vector3, rot_deg: Vector3, target_span: float) -> Vector3:
	inst.position = Vector3.ZERO
	inst.rotation = Vector3.ZERO
	inst.scale = Vector3.ONE
	var state: Dictionary = {"has_aabb": false, "aabb": AABB()}
	_compute_local_mesh_aabb(inst, inst, Transform3D.IDENTITY, state)
	var local_center: Vector3 = Vector3.ZERO
	var uniform_scale: float = 1.15
	if bool(state.get("has_aabb", false)):
		var aabb: AABB = state["aabb"] as AABB
		local_center = aabb.get_center()
		var max_dim: float = maxf(aabb.size.x, maxf(aabb.size.y, aabb.size.z))
		if max_dim > 0.01:
			uniform_scale = clampf(target_span / max_dim, 0.55, 2.25)
	inst.rotation = Vector3(deg_to_rad(rot_deg.x), deg_to_rad(rot_deg.y), deg_to_rad(rot_deg.z))
	inst.scale = Vector3.ONE * uniform_scale
	var base_pos: Vector3 = target_center - (inst.basis * local_center)
	inst.position = base_pos
	return base_pos


func refresh_3d_pedestal_models(armor_idx: int = -1, weapon_id: String = "") -> void:
	if pedestal_pivot == null or not is_instance_valid(pedestal_pivot):
		return

	_resolve_loadout_manager()
	var resolved_armor: int = armor_idx
	if resolved_armor < 0:
		resolved_armor = loadout_manager.equipped_armor_index if loadout_manager != null else 0
	resolved_armor = posmod(resolved_armor, 4)

	var resolved_weapon: String = weapon_id
	if resolved_weapon.is_empty():
		resolved_weapon = loadout_manager.active_weapon_id if loadout_manager != null else "revolver"
	if not WEAPON_GLBS.has(resolved_weapon):
		resolved_weapon = "revolver"

	# 1. Update 3D Armor Gauntlet preview mesh when changed
	if resolved_armor != preview_armor_index or preview_gauntlet_node == null or not is_instance_valid(preview_gauntlet_node):
		if preview_gauntlet_node != null and is_instance_valid(preview_gauntlet_node):
			if preview_gauntlet_node.get_parent() != null:
				preview_gauntlet_node.get_parent().remove_child(preview_gauntlet_node)
			preview_gauntlet_node.free()
			preview_gauntlet_node = null

		var g_scn: PackedScene = null
		var p_path: String = ARMOR_GAUNTLET_PREFABS[resolved_armor]
		var g_path: String = ARMOR_GAUNTLET_GLBS[resolved_armor]
		if ResourceLoader.exists(g_path):
			g_scn = load(g_path) as PackedScene
		if g_scn == null and ResourceLoader.exists(p_path):
			g_scn = load(p_path) as PackedScene

		if g_scn != null:
			var g_inst: Node3D = g_scn.instantiate() as Node3D
			if g_inst != null:
				g_inst.name = "PreviewGauntlet_%d" % (resolved_armor + 1)
				pedestal_pivot.add_child(g_inst)
				_gauntlet_base_pos = _frame_pedestal_model(
					g_inst,
					Vector3(-0.21, 0.04, 0.02),
					Vector3(-18.0, 32.0, -10.0),
					0.36
				)
				preview_gauntlet_node = g_inst
		preview_armor_index = resolved_armor

	# 2. Update 3D Weapon preview mesh when changed
	if resolved_weapon != preview_weapon_id or preview_weapon_node == null or not is_instance_valid(preview_weapon_node):
		if preview_weapon_node != null and is_instance_valid(preview_weapon_node):
			if preview_weapon_node.get_parent() != null:
				preview_weapon_node.get_parent().remove_child(preview_weapon_node)
			preview_weapon_node.free()
			preview_weapon_node = null

		var w_path: String = WEAPON_GLBS[resolved_weapon]
		if ResourceLoader.exists(w_path):
			var w_scn: PackedScene = load(w_path) as PackedScene
			if w_scn != null:
				var w_inst: Node3D = w_scn.instantiate() as Node3D
				if w_inst != null:
					w_inst.name = "PreviewWeapon_" + resolved_weapon
					pedestal_pivot.add_child(w_inst)
					_weapon_base_pos = _frame_pedestal_model(
						w_inst,
						Vector3(0.21, 0.04, 0.02),
						Vector3(6.0, -42.0, 5.0),
						0.40
					)
					preview_weapon_node = w_inst
		preview_weapon_id = resolved_weapon

	# 3. Mode-specific 3D Pedestal framing & Full-Body HunterPaperDollRig visibility
	var show_full_hunter: bool = (current_menu_mode == MODE_FIELD_CHARACTER or current_menu_mode == MODE_ARMORER_STAND)
	if paperdoll_rig != null and is_instance_valid(paperdoll_rig):
		paperdoll_rig.visible = show_full_hunter
		if paperdoll_rig.studio_lighting_root != null:
			paperdoll_rig.studio_lighting_root.visible = false
		if paperdoll_rig.plinth_root != null:
			paperdoll_rig.plinth_root.visible = false
		if current_menu_mode == MODE_FIELD_CHARACTER:
			paperdoll_rig.refresh_from_loadout(loadout_manager)
		elif current_menu_mode == MODE_ARMORER_STAND:
			_refresh_armorer_3d_preview()

	if pedestal_plinth_mesh != null and is_instance_valid(pedestal_plinth_mesh):
		pedestal_plinth_mesh.visible = true
	var brass_ring: Node3D = pedestal_pivot.get_node_or_null("PlinthBrassRing") as Node3D
	if brass_ring != null:
		brass_ring.visible = true
	if _dais_assembly_root != null and is_instance_valid(_dais_assembly_root):
		_dais_assembly_root.visible = show_full_hunter

	if pedestal_camera != null and is_instance_valid(pedestal_camera):
		if show_full_hunter:
			pedestal_camera.fov = 43.0
			pedestal_camera.position = Vector3(0.0, 1.05, 2.55)
			pedestal_camera.look_at_from_position(Vector3(0.0, 1.05, 2.55), Vector3(0.0, 0.90, 0.0), Vector3.UP)
		else:
			pedestal_camera.fov = 34.0
			pedestal_camera.position = Vector3(0.0, 0.12, 1.12)
			pedestal_camera.rotation = Vector3(deg_to_rad(-6.5), 0.0, 0.0)

	if preview_gauntlet_node != null and is_instance_valid(preview_gauntlet_node):
		preview_gauntlet_node.visible = false

	if preview_weapon_node != null and is_instance_valid(preview_weapon_node):
		preview_weapon_node.visible = (current_menu_mode == MODE_GUNSMITH_WORKBENCH)
		if current_menu_mode == MODE_GUNSMITH_WORKBENCH:
			_weapon_base_pos = _frame_pedestal_model(preview_weapon_node, Vector3(0.0, 0.05, 0.06), Vector3(6.0, -42.0, 5.0), 0.50)


func _refresh_armorer_3d_preview() -> void:
	if paperdoll_rig == null or not is_instance_valid(paperdoll_rig):
		return
	paperdoll_rig.refresh_from_loadout(loadout_manager)
	var set_idx: int = posmod(_armorer_selected_set_index, 4)
	if _armorer_preview_full_set:
		for sk: String in PlayerLoadoutManager.ARMOR_SLOTS:
			paperdoll_rig.preview_single_armor_piece(sk, set_idx)
	else:
		var sel_slot: String = PlayerLoadoutManager.ARMOR_SLOTS[clampi(_armorer_selected_slot_index, 0, 4)]
		paperdoll_rig.preview_single_armor_piece(sel_slot, set_idx)


func _on_armorer_set_tab_selected(set_idx: int) -> void:
	_armorer_selected_set_index = posmod(set_idx, 4)
	_play_ui_sfx(_sfx_tab_turn)
	_refresh_armorer_3d_preview()
	_refresh_all_ui_elements()


func _on_armorer_piece_hovered(slot_idx: int) -> void:
	var c_slot: int = clampi(slot_idx, 0, 4)
	if _armorer_selected_slot_index != c_slot:
		_armorer_selected_slot_index = c_slot
		_refresh_armorer_3d_preview()
		_refresh_all_ui_elements()


func _on_armorer_piece_action_pressed(slot_idx: int) -> void:
	_resolve_loadout_manager()
	_armorer_selected_slot_index = clampi(slot_idx, 0, 4)
	var s_name: String = PlayerLoadoutManager.ARMOR_SLOTS[_armorer_selected_slot_index]
	var set_idx: int = posmod(_armorer_selected_set_index, 4)
	if loadout_manager != null:
		if not loadout_manager.is_armor_piece_unlocked(s_name, set_idx):
			var rec: Dictionary = PlayerLoadoutManager.get_armor_piece_recipe(s_name, set_idx)
			var burst_pt: Vector2 = _armor_forge_btn_rects[_armorer_selected_slot_index].get_center() if _armorer_selected_slot_index < _armor_forge_btn_rects.size() else Vector2(260.0, 380.0)
			if is_forge_available() and loadout_manager.can_afford(rec):
				if loadout_manager.craft_unlock_armor_piece(s_name, set_idx):
					_spawn_forge_spark_burst(burst_pt)
					_play_ui_sfx(_sfx_armor_clank)
					_play_ui_sfx(_sfx_skill_chime)
			else:
				loadout_manager.notify_locked_forge_required()
				_play_ui_sfx(_sfx_armor_clank)
		else:
			loadout_manager.equip_armor_slot(s_name, set_idx)
			_play_ui_sfx(_sfx_armor_clank)
	_refresh_armorer_3d_preview()
	_refresh_all_ui_elements()


func toggle_menu() -> void:
	if is_menu_open:
		set_menu_open(false)
	else:
		open_field_character_menu()


func open_field_character_menu() -> void:
	current_menu_mode = MODE_FIELD_CHARACTER
	forge_mode_active = false
	forge_station_type = ""
	active_tab = 0
	set_menu_open(true)


func open_at_forge_station(station_type: String) -> void:
	forge_mode_active = true
	forge_station_type = station_type
	active_tab = 0
	match station_type:
		"weapon":
			current_menu_mode = MODE_GUNSMITH_WORKBENCH
		"armor":
			current_menu_mode = MODE_ARMORER_STAND
		"upgrade":
			current_menu_mode = MODE_BAPTISMAL_ASTROLABE
		_:
			current_menu_mode = MODE_GUNSMITH_WORKBENCH
	set_menu_open(true)


func is_forge_available() -> bool:
	if current_menu_mode == MODE_FIELD_CHARACTER and not forge_mode_active:
		return false
	return true


func get_visible_forge_button_count() -> int:
	var count: int = 0
	if _left_wing_panel != null and _left_wing_panel.visible:
		if _armorer_left_container != null and _armorer_left_container.visible:
			for p_btn: Button in _armorer_piece_buttons:
				if p_btn != null and p_btn.visible and (p_btn.text.contains("FORGE") or p_btn.text.contains("⚒")):
					count += 1
		else:
			for btn: Button in _armor_action_buttons:
				if btn != null and btn.visible and (btn.text.contains("FORGE") or btn.text.contains("⚒")):
					count += 1
	if _center_nave_panel != null and _center_nave_panel.visible:
		for w_i: int in range(_weapon_card_panels.size()):
			if _weapon_card_panels[w_i].visible:
				var w_btn: Button = _weapon_action_buttons[w_i]
				if w_btn != null and w_btn.visible and (w_btn.text.contains("FORGE") or w_btn.text.contains("⚒")):
					count += 1
				var mod_row: Array = _weapon_mod_buttons[w_i]
				for m_var: Variant in mod_row:
					var m_btn: Button = m_var as Button
					if m_btn != null and m_btn.visible and (m_btn.text.contains("FORGE") or m_btn.text.contains("⚒")):
						count += 1
		for s_i: int in range(_spell_card_panels.size()):
			if _spell_card_panels[s_i].visible:
				var sp_btn: Button = _spell_action_buttons[s_i]
				if sp_btn != null and sp_btn.visible and (sp_btn.text.contains("FORGE") or sp_btn.text.contains("CONSECRATE SPELL") or sp_btn.text.contains("⚒")):
					count += 1
	return count


func set_menu_open(open: bool) -> void:
	is_menu_open = open
	visible = is_menu_open
	mouse_filter = Control.MOUSE_FILTER_STOP if is_menu_open else Control.MOUSE_FILTER_IGNORE

	if dim_backdrop != null and dim_backdrop.get_index() != 0:
		move_child(dim_backdrop, 0)

	if is_menu_open:
		_is_dirty = false
		_resolve_loadout_manager()
		var eq_armor: int = loadout_manager.equipped_armor_index if loadout_manager != null else 0
		var eq_weap: String = loadout_manager.active_weapon_id if loadout_manager != null else "revolver"
		refresh_3d_pedestal_models(eq_armor, eq_weap)
		_play_ui_sfx(_sfx_grimoire_open)
		if DisplayServer.get_name() != "headless":
			Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
	else:
		_is_dragging_pedestal = false
		_hide_floating_tooltip()
		forge_mode_active = false
		forge_station_type = ""
		current_menu_mode = MODE_FIELD_CHARACTER
		hovered_armor_index = -1
		hovered_skill_id = ""
		if DisplayServer.get_name() != "headless":
			Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)

	_update_subviewport_layout(true)
	_refresh_all_ui_elements()
	queue_redraw()


func switch_tab(tab_idx: int) -> void:
	var clamped: int = clampi(tab_idx, 0, 1)
	if active_tab != clamped:
		active_tab = clamped
		_hide_floating_tooltip()
		_play_ui_sfx(_sfx_tab_turn)
	_update_subviewport_layout(true)
	_refresh_all_ui_elements()
	queue_redraw()


func forge_and_unlock_item(category: String, index: int, sub_index: int = 0, burst_pos: Vector2 = Vector2.ZERO) -> bool:
	_resolve_loadout_manager()
	if loadout_manager == null:
		return false
	if not is_forge_available():
		loadout_manager.notify_locked_forge_required()
		_play_ui_sfx(_sfx_armor_clank)
		return false
	var ok: bool = loadout_manager.craft_unlock_item(category, index, sub_index)
	if ok:
		_play_ui_sfx(_sfx_armor_clank)
		_play_ui_sfx(_sfx_skill_chime)
		var spark_pt: Vector2 = burst_pos
		if spark_pt == Vector2.ZERO:
			spark_pt = _pedestal_arch_rect.get_center() if _pedestal_arch_rect.size.x > 0.0 else Vector2(960.0, 540.0)
		_spawn_forge_spark_burst(spark_pt)
		refresh_3d_pedestal_models(loadout_manager.equipped_armor_index, loadout_manager.active_weapon_id)
		_refresh_all_ui_elements()
		queue_redraw()
	else:
		_play_ui_sfx(_sfx_armor_clank)
	return ok


func _spawn_forge_spark_burst(center: Vector2) -> void:
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.randomize()
	for i: int in range(30):
		var ang: float = (float(i) / 30.0) * TAU + rng.randf_range(-0.14, 0.14)
		var spd: float = rng.randf_range(105.0, 295.0)
		var is_gold: bool = (i % 3 != 0)
		var spark_col: Color = Color(1.0, 0.88, 0.34, 1.0) if is_gold else Color(1.0, 0.56, 0.22, 1.0)
		active_spark_bursts.append({
			"pos": center,
			"vel": Vector2(cos(ang), sin(ang)) * spd,
			"color": spark_col,
			"size": rng.randf_range(2.4, 4.6),
			"life": 0.0,
			"max_life": rng.randf_range(0.48, 0.88)
		})
	active_shockwave_rings.append({
		"center": center,
		"radius": 16.0,
		"max_radius": 140.0,
		"color": Color(1.0, 0.82, 0.28, 1.0),
		"life": 0.0,
		"max_life": 0.50
	})


func select_armor_plaque(armor_idx: int) -> void:
	_resolve_loadout_manager()
	var clamped: int = posmod(armor_idx, 4)
	if loadout_manager != null:
		if not loadout_manager.is_armor_unlocked(clamped):
			var p_center: Vector2 = _armor_plaque_rects[clamped].get_center() if clamped < _armor_plaque_rects.size() else Vector2(320.0, 400.0)
			if is_forge_available() and loadout_manager.can_afford(loadout_manager.get_item_recipe("armor", clamped)):
				forge_and_unlock_item("armor", clamped, 0, p_center)
				return
			loadout_manager.notify_locked_forge_required()
			refresh_3d_pedestal_models(clamped, preview_weapon_id)
			_play_ui_sfx(_sfx_armor_clank)
			_refresh_all_ui_elements()
			queue_redraw()
			return
		loadout_manager.equip_armor_tier(clamped)
	refresh_3d_pedestal_models(clamped, preview_weapon_id)
	_play_ui_sfx(_sfx_armor_clank)
	_refresh_all_ui_elements()
	queue_redraw()


func select_weapon_mod_socket(weapon_slot_idx: int, mod_idx: int) -> void:
	_resolve_loadout_manager()
	var w_clamped: int = clampi(weapon_slot_idx, 0, 2)
	var m_clamped: int = posmod(mod_idx, 4)
	if loadout_manager != null:
		var wid: String = loadout_manager.get_weapon_id_from_slot(w_clamped)
		if not loadout_manager.is_weapon_unlocked(w_clamped):
			var w_center: Vector2 = _weapon_card_rects[w_clamped].get_center() if w_clamped < _weapon_card_rects.size() else Vector2(960.0, 500.0)
			if is_forge_available() and loadout_manager.can_afford(loadout_manager.get_item_recipe("weapon", w_clamped)):
				forge_and_unlock_item("weapon", w_clamped, 0, w_center)
			else:
				loadout_manager.notify_locked_forge_required()
				_play_ui_sfx(_sfx_armor_clank)
				_refresh_all_ui_elements()
				queue_redraw()
				return
		else:
			loadout_manager.equip_weapon(wid)
		if not loadout_manager.is_weapon_mod_unlocked(w_clamped, m_clamped):
			var s_center: Vector2 = Vector2(960.0, 520.0)
			if w_clamped < _weapon_mod_socket_rects.size():
				var s_arr: Array = _weapon_mod_socket_rects[w_clamped]
				if m_clamped < s_arr.size():
					s_center = (s_arr[m_clamped] as Rect2).get_center()
			if is_forge_available() and loadout_manager.can_afford(loadout_manager.get_item_recipe("mod", m_clamped)):
				forge_and_unlock_item("mod", m_clamped, w_clamped, s_center)
				return
			loadout_manager.notify_locked_forge_required()
			_play_ui_sfx(_sfx_armor_clank)
			_refresh_all_ui_elements()
			queue_redraw()
			return
		loadout_manager.equip_weapon_mod(w_clamped, m_clamped)
		refresh_3d_pedestal_models(preview_armor_index, loadout_manager.active_weapon_id)
	_play_ui_sfx(_sfx_tab_turn)
	_refresh_all_ui_elements()
	queue_redraw()


func select_lantern_spell(spell_idx: int) -> void:
	_resolve_loadout_manager()
	var s_clamped: int = posmod(spell_idx, 3)
	if loadout_manager != null:
		if not loadout_manager.is_spell_unlocked(s_clamped):
			var sp_center: Vector2 = _spell_medallion_rects[s_clamped].get_center() if s_clamped < _spell_medallion_rects.size() else Vector2(960.0, 720.0)
			if is_forge_available() and loadout_manager.can_afford(loadout_manager.get_item_recipe("spell", s_clamped)):
				forge_and_unlock_item("spell", s_clamped, 0, sp_center)
				return
			loadout_manager.notify_locked_forge_required()
			_play_ui_sfx(_sfx_armor_clank)
			_refresh_all_ui_elements()
			queue_redraw()
			return
		loadout_manager.equip_lantern_spell(s_clamped)
	_play_ui_sfx(_sfx_tab_turn)
	_refresh_all_ui_elements()
	queue_redraw()


func trigger_grant_test_materials() -> void:
	_resolve_loadout_manager()
	if loadout_manager != null:
		loadout_manager.grant_test_materials()
	forge_mode_active = true
	_play_ui_sfx(_sfx_skill_chime)
	_refresh_all_ui_elements()
	queue_redraw()


func select_skill_node(skill_id: String, try_unlock: bool = false) -> bool:
	_resolve_loadout_manager()
	selected_skill_id = skill_id
	var unlocked_now: bool = false
	if try_unlock and loadout_manager != null:
		if loadout_manager.can_unlock_skill(skill_id):
			unlocked_now = loadout_manager.unlock_skill(skill_id)
			if unlocked_now:
				_play_ui_sfx(_sfx_skill_chime)
	_refresh_all_ui_elements()
	queue_redraw()
	return unlocked_now


func consecrate_selected_skill() -> bool:
	return select_skill_node(selected_skill_id, true)


func trigger_sanctuary_blessing() -> void:
	_resolve_loadout_manager()
	if loadout_manager != null:
		loadout_manager.grant_sanctuary_blessing_sp(2)
	_play_ui_sfx(_sfx_skill_chime)
	_refresh_all_ui_elements()
	queue_redraw()


func trigger_respec_rites() -> int:
	_resolve_loadout_manager()
	var refunded: int = 0
	if loadout_manager != null:
		refunded = loadout_manager.respec_all_skills()
	_play_ui_sfx(_sfx_grimoire_open)
	_refresh_all_ui_elements()
	queue_redraw()
	return refunded


func _spawn_skill_unlock_vfx(skill_id: String) -> void:
	var fallback_center: Vector2 = _get_viewport_size() * 0.5
	var center: Vector2 = _skill_node_centers.get(skill_id, fallback_center)
	if center == Vector2.ZERO:
		center = fallback_center

	var catalog: Dictionary[String, Dictionary] = PlayerLoadoutManager.get_skill_tree_catalog()
	var branch_col: Color = Color(1.0, 0.82, 0.28, 1.0)
	if catalog.has(skill_id):
		branch_col = catalog[skill_id].get("branch_color", branch_col) as Color

	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.randomize()
	for i: int in range(28):
		var ang: float = (float(i) / 28.0) * TAU + rng.randf_range(-0.12, 0.12)
		var spd: float = rng.randf_range(95.0, 285.0)
		var is_gold: bool = (i % 2 == 0)
		var spark_col: Color = Color(1.0, 0.88, 0.34, 1.0) if is_gold else branch_col.lightened(0.18)
		active_spark_bursts.append({
			"pos": center,
			"vel": Vector2(cos(ang), sin(ang)) * spd,
			"color": spark_col,
			"size": rng.randf_range(2.4, 4.6),
			"life": 0.0,
			"max_life": rng.randf_range(0.45, 0.82)
		})

	active_shockwave_rings.append({
		"center": center,
		"radius": 18.0,
		"max_radius": 135.0,
		"color": branch_col,
		"life": 0.0,
		"max_life": 0.52
	})


func _process(delta: float) -> void:
	if not visible and not is_menu_open and active_spark_bursts.is_empty() and active_shockwave_rings.is_empty():
		return
	_anim_time += delta
	_xp_bar_shimmer = fmod(_xp_bar_shimmer + delta * 0.65, 1.0)

	# Rotate 3D Reliquary Inspection Pedestal (0.65 rad/s auto-rotate + manual drag inertia)
	if pedestal_pivot != null and is_instance_valid(pedestal_pivot):
		if _is_dragging_pedestal:
			pedestal_pivot.rotation.y += _pedestal_manual_vel * delta
			_pedestal_manual_vel = move_toward(_pedestal_manual_vel, 0.0, delta * 18.0)
		else:
			pedestal_pivot.rotation.y += delta * 0.65

		if preview_gauntlet_node != null and is_instance_valid(preview_gauntlet_node):
			preview_gauntlet_node.position = _gauntlet_base_pos + Vector3(0.0, sin(_anim_time * 2.1) * 0.012, 0.0)
		if preview_weapon_node != null and is_instance_valid(preview_weapon_node):
			preview_weapon_node.position = _weapon_base_pos + Vector3(0.0, cos(_anim_time * 2.1) * 0.012, 0.0)

	# Update drifting background ember motes
	for m_idx: int in range(_bg_motes.size()):
		var mote: Dictionary = _bg_motes[m_idx]
		var uv: Vector2 = mote["uv"] as Vector2
		var vel: Vector2 = mote["vel"] as Vector2
		uv += vel * delta
		if uv.y < 0.05:
			uv.y = 0.94
		if uv.x < 0.04:
			uv.x = 0.95
		elif uv.x > 0.96:
			uv.x = 0.05
		mote["uv"] = uv

	# Update 28-particle unlock spark bursts
	var next_sparks: Array[Dictionary] = []
	for sp: Dictionary in active_spark_bursts:
		var life: float = float(sp["life"]) + delta
		var max_l: float = float(sp["max_life"])
		if life < max_l:
			var pos: Vector2 = sp["pos"] as Vector2
			var vel: Vector2 = sp["vel"] as Vector2
			vel = vel * (1.0 - 2.4 * delta) + Vector2(0.0, 68.0 * delta)
			sp["pos"] = pos + vel * delta
			sp["vel"] = vel
			sp["life"] = life
			next_sparks.append(sp)
	active_spark_bursts = next_sparks

	# Update expanding golden shockwave rings
	var next_rings: Array[Dictionary] = []
	for rg: Dictionary in active_shockwave_rings:
		var r_life: float = float(rg["life"]) + delta
		var r_max: float = float(rg["max_life"])
		if r_life < r_max:
			var t_r: float = clampf(r_life / r_max, 0.0, 1.0)
			rg["radius"] = lerpf(18.0, float(rg["max_radius"]), 1.0 - pow(1.0 - t_r, 2.5))
			rg["life"] = r_life
			next_rings.append(rg)
	active_shockwave_rings = next_rings

	# Decay wax-seal stamp bounce scales toward 1.0
	for sid: String in _wax_seal_scales.keys():
		var sc: float = float(_wax_seal_scales[sid])
		if sc > 1.005:
			_wax_seal_scales[sid] = move_toward(sc, 1.0, delta * 4.8)

	if is_menu_open:
		_update_subviewport_layout(false)
		_update_floating_tooltip_position()
		if bg_decor_canvas != null:
			bg_decor_canvas.queue_redraw()
		if active_tab == 1 and _astrolabe_conduit_canvas != null:
			_astrolabe_conduit_canvas.queue_redraw()
		if vfx_overlay_canvas != null and (not active_spark_bursts.is_empty() or not active_shockwave_rings.is_empty()):
			vfx_overlay_canvas.queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey:
		var k: InputEventKey = event as InputEventKey
		if k.pressed and not k.echo:
			var code: Key = k.keycode if k.keycode != KEY_NONE else k.physical_keycode
			if code == KEY_C or code == KEY_K or code == KEY_I:
				toggle_menu()
				get_viewport().set_input_as_handled()
				return
			if is_menu_open and code == KEY_ESCAPE:
				set_menu_open(false)
				get_viewport().set_input_as_handled()
				return


func _gui_input(event: InputEvent) -> void:
	if not is_menu_open:
		return

	if event is InputEventMouseMotion:
		var mm: InputEventMouseMotion = event as InputEventMouseMotion
		if _is_dragging_pedestal and pedestal_pivot != null:
			pedestal_pivot.rotation.y += mm.relative.x * 0.014
			_pedestal_manual_vel = mm.relative.x * 0.45
			return
		_handle_mouse_hover(mm.position)

	elif event is InputEventMouseButton:
		var mb: InputEventMouseButton = event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_LEFT:
			if mb.pressed:
				_handle_left_click(mb.position)
			else:
				_is_dragging_pedestal = false


func _handle_mouse_hover(mpos: Vector2) -> void:
	var prev_armor: int = hovered_armor_index
	var prev_skill: String = hovered_skill_id
	var prev_relic: int = hovered_relic_slot

	hovered_armor_index = -1
	hovered_weapon_slot = -1
	hovered_weapon_mod = -1
	hovered_spell_index = -1
	hovered_relic_slot = -1
	hovered_skill_id = ""

	if active_tab == 0:
		for i: int in range(_armor_plaque_rects.size()):
			if _armor_plaque_rects[i].has_point(mpos):
				hovered_armor_index = i
				break
		for r_i: int in range(_relic_socket_rects.size()):
			if _relic_socket_rects[r_i].has_point(mpos):
				hovered_relic_slot = r_i
				break
	else:
		for sid: String in _skill_node_centers.keys():
			var n_center: Vector2 = _skill_node_centers[sid]
			var n_rad: float = float(_skill_node_radii.get(sid, 29.0))
			if mpos.distance_to(n_center) <= n_rad + 6.0:
				hovered_skill_id = sid
				break

	if hovered_armor_index != prev_armor:
		var target_armor: int = hovered_armor_index
		if target_armor < 0 and loadout_manager != null:
			target_armor = loadout_manager.equipped_armor_index
		refresh_3d_pedestal_models(target_armor, preview_weapon_id)
		_refresh_all_ui_elements()
	elif hovered_skill_id != prev_skill or hovered_relic_slot != prev_relic:
		_refresh_all_ui_elements()


func _handle_left_click(mpos: Vector2) -> void:
	for t_i: int in range(_tab_rects.size()):
		if _tab_rects[t_i].has_point(mpos):
			switch_tab(t_i)
			return

	if _blessing_btn_rect.has_point(mpos):
		trigger_sanctuary_blessing()
		return
	if _respec_btn_rect.has_point(mpos):
		trigger_respec_rites()
		return
	if _grant_materials_btn_rect.has_point(mpos):
		trigger_grant_test_materials()
		return

	if active_tab == 0:
		for af_i: int in range(_armor_forge_btn_rects.size()):
			var af_rect: Rect2 = _armor_forge_btn_rects[af_i]
			if af_rect.size.x > 0.0 and af_rect.has_point(mpos):
				_on_armor_button_pressed(af_i)
				return

		for a_i: int in range(_armor_plaque_rects.size()):
			if _armor_plaque_rects[a_i].has_point(mpos):
				select_armor_plaque(a_i)
				return

		if _pedestal_arch_rect.has_point(mpos):
			_is_dragging_pedestal = true
			return

		for wf_i: int in range(_weapon_forge_btn_rects.size()):
			var wf_rect: Rect2 = _weapon_forge_btn_rects[wf_i]
			if wf_rect.size.x > 0.0 and wf_rect.has_point(mpos):
				_on_weapon_button_pressed(wf_i)
				return

		for w_i: int in range(_weapon_mod_socket_rects.size()):
			var mod_arr: Array = _weapon_mod_socket_rects[w_i]
			for m_i: int in range(mod_arr.size()):
				var s_rect: Rect2 = mod_arr[m_i] as Rect2
				if s_rect.has_point(mpos):
					select_weapon_mod_socket(w_i, m_i)
					return

		for wc_i: int in range(_weapon_card_rects.size()):
			if _weapon_card_rects[wc_i].has_point(mpos):
				_on_weapon_button_pressed(wc_i)
				return

		for sf_i: int in range(_spell_forge_btn_rects.size()):
			var sf_rect: Rect2 = _spell_forge_btn_rects[sf_i]
			if sf_rect.size.x > 0.0 and sf_rect.has_point(mpos):
				select_lantern_spell(sf_i)
				return

		for sp_i: int in range(_spell_medallion_rects.size()):
			if _spell_medallion_rects[sp_i].has_point(mpos):
				select_lantern_spell(sp_i)
				return
	else:
		if _consecrate_btn_rect.has_point(mpos):
			consecrate_selected_skill()
			return

		for sid: String in _skill_node_centers.keys():
			var n_center: Vector2 = _skill_node_centers[sid]
			var n_rad: float = float(_skill_node_radii.get(sid, 29.0))
			if mpos.distance_to(n_center) <= n_rad + 6.0:
				_on_skill_node_button_pressed(sid)
				return


func _format_recipe_cost_badge(recipe: Dictionary) -> String:
	if recipe.is_empty():
		return "UNLOCKED"
	var parts: Array[String] = []
	if int(recipe.get("silver", 0)) > 0:
		parts.append("◈%d" % int(recipe["silver"]))
	if int(recipe.get("bone_ash", 0)) > 0:
		parts.append("⚱%d" % int(recipe["bone_ash"]))
	if int(recipe.get("cursed_iron", 0)) > 0:
		parts.append("⛓%d" % int(recipe["cursed_iron"]))
	if int(recipe.get("soul_cores", 0)) > 0:
		parts.append("✦%d" % int(recipe["soul_cores"]))
	return " ".join(parts)


# ==============================================================================================
# ORNAMENTAL CANVAS DRAWERS (Background Astrolabe, Skill Tree Conduits, Foreground VFX Sparks)
# ==============================================================================================
func _on_bg_decor_canvas_draw() -> void:
	if bg_decor_canvas == null or not is_menu_open:
		return
	var sz: Vector2 = bg_decor_canvas.size
	var center: Vector2 = sz * 0.5 + Vector2(0.0, 20.0)
	var brass_faint: Color = Color(0.90, 0.74, 0.38, 0.14)
	var brass_inner: Color = Color(0.96, 0.80, 0.44, 0.10)

	var radii: Array[float] = [180.0, 290.0, 400.0]
	var speeds: Array[float] = [0.14, -0.09, 0.06]
	for r_i: int in range(3):
		var rad: float = radii[r_i]
		var rot: float = _anim_time * speeds[r_i]
		bg_decor_canvas.draw_arc(center, rad, 0.0, TAU, 72, brass_faint, 1.4)
		var tick_count: int = 48 if r_i == 2 else 24
		for t_i: int in range(tick_count):
			var ang: float = rot + float(t_i) * (TAU / float(tick_count))
			var dir: Vector2 = Vector2(cos(ang), sin(ang))
			bg_decor_canvas.draw_line(center + dir * (rad - 6.0), center + dir * rad, brass_inner, 1.1)

	for mote: Dictionary in _bg_motes:
		var uv: Vector2 = mote["uv"] as Vector2
		var m_pos: Vector2 = Vector2(uv.x * sz.x, uv.y * sz.y)
		var pulse: float = 0.55 + 0.45 * sin(_anim_time * 2.2 + float(mote["phase"]))
		var m_col: Color = (
			Color(0.98, 0.34, 0.28, 0.24 * pulse)
			if bool(mote["is_crimson"])
			else Color(1.0, 0.86, 0.42, 0.28 * pulse)
		)
		bg_decor_canvas.draw_circle(m_pos, float(mote["rad"]), m_col)

	# 4 Corner Rose-Medallions
	var corners: Array[Vector2] = [
		Vector2(14.0, 14.0),
		Vector2(sz.x - 14.0, 14.0),
		Vector2(14.0, sz.y - 14.0),
		Vector2(sz.x - 14.0, sz.y - 14.0)
	]
	for c_pt: Vector2 in corners:
		bg_decor_canvas.draw_circle(c_pt, 10.0, Color(0.92, 0.74, 0.36, 0.90))
		bg_decor_canvas.draw_circle(c_pt, 4.0, Color(0.95, 0.26, 0.24, 0.96))


func _on_astrolabe_conduit_canvas_draw() -> void:
	if _astrolabe_conduit_canvas == null or not is_menu_open or active_tab != 1:
		return
	var sz: Vector2 = _astrolabe_conduit_canvas.size
	var col_colors: Array[Color] = [
		Color(0.95, 0.28, 0.24, 1.0),
		Color(0.45, 0.88, 1.0, 1.0),
		Color(0.98, 0.80, 0.36, 1.0),
		Color(0.84, 0.45, 1.0, 1.0)
	]
	var col_x_uvs: Array[float] = [0.14, 0.38, 0.62, 0.86]

	# 1. 4 Gothic Constellation Lancet Arches
	for c_i: int in range(4):
		var cx: float = col_x_uvs[c_i] * sz.x
		var arch_w: float = sz.x * 0.21
		var arch_left: float = cx - arch_w * 0.5
		var arch_right: float = cx + arch_w * 0.5
		var arch_top: float = 8.0
		var arch_bot: float = sz.y - 10.0
		var col_c: Color = col_colors[c_i]

		var lancet_pts: PackedVector2Array = PackedVector2Array([
			Vector2(arch_left, arch_bot),
			Vector2(arch_left, arch_top + 42.0),
			Vector2(cx, arch_top),
			Vector2(arch_right, arch_top + 42.0),
			Vector2(arch_right, arch_bot),
			Vector2(arch_left, arch_bot)
		])
		_astrolabe_conduit_canvas.draw_colored_polygon(lancet_pts, Color(col_c.r * 0.14, col_c.g * 0.14, col_c.b * 0.16, 0.36))
		_astrolabe_conduit_canvas.draw_polyline(lancet_pts, Color(col_c.r, col_c.g, col_c.b, 0.65), 2.0)

	# 2. Animated Molten-Gold Conduit Veins between prerequisites and target nodes
	var catalog: Dictionary[String, Dictionary] = PlayerLoadoutManager.get_skill_tree_catalog()
	var node_ids: Array[String] = PlayerLoadoutManager.get_skill_node_ids()
	var pulse_phase: float = fmod(_anim_time * 0.8, 1.0)

	for sid: String in node_ids:
		var info: Dictionary = catalog[sid]
		var to_uv: Vector2 = info["pos_uv"] as Vector2
		var to_pt: Vector2 = Vector2(to_uv.x * sz.x, to_uv.y * sz.y)
		var to_unlocked: bool = loadout_manager != null and loadout_manager.is_skill_unlocked(sid)
		var branch_col: Color = info["branch_color"] as Color
		var prereqs: Array = info["prereqs"] as Array

		for pre_var: Variant in prereqs:
			var pre_id: String = String(pre_var)
			if not catalog.has(pre_id):
				continue
			var from_uv: Vector2 = catalog[pre_id]["pos_uv"] as Vector2
			var from_pt: Vector2 = Vector2(from_uv.x * sz.x, from_uv.y * sz.y)
			var pre_unlocked: bool = loadout_manager != null and loadout_manager.is_skill_unlocked(pre_id)

			if pre_unlocked and to_unlocked:
				_astrolabe_conduit_canvas.draw_line(from_pt, to_pt, Color(branch_col.r, branch_col.g, branch_col.b, 0.45), 9.0)
				_astrolabe_conduit_canvas.draw_line(from_pt, to_pt, Color(1.0, 0.84, 0.36, 0.95), 4.5)
				_astrolabe_conduit_canvas.draw_line(from_pt, to_pt, Color(1.0, 0.98, 0.82, 1.0), 2.0)
				for p_step: float in [0.0, 0.5]:
					var t_p: float = fmod(pulse_phase + p_step, 1.0)
					var pulse_pt: Vector2 = from_pt.lerp(to_pt, t_p)
					_astrolabe_conduit_canvas.draw_circle(pulse_pt, 5.5, Color(1.0, 0.92, 0.54, 0.98))
			elif pre_unlocked:
				_astrolabe_conduit_canvas.draw_line(from_pt, to_pt, Color(0.28, 0.22, 0.16, 0.95), 5.0)
				_astrolabe_conduit_canvas.draw_dashed_line(from_pt, to_pt, Color(1.0, 0.84, 0.40, 0.92), 2.5, 8.0)
			else:
				_astrolabe_conduit_canvas.draw_line(from_pt, to_pt, Color(0.18, 0.15, 0.22, 0.92), 4.0)
				_astrolabe_conduit_canvas.draw_dashed_line(from_pt, to_pt, Color(0.62, 0.54, 0.42, 0.72), 1.8, 7.0)

	# 3. Outer Medallion Halos around Skill Nodes
	for sid: String in node_ids:
		var info2: Dictionary = catalog[sid]
		var uv2: Vector2 = info2["pos_uv"] as Vector2
		var pt2: Vector2 = Vector2(uv2.x * sz.x, uv2.y * sz.y)
		var rad2: float = float(_skill_node_radii.get(sid, 29.0))
		var b_col: Color = info2["branch_color"] as Color
		var is_unl: bool = loadout_manager != null and loadout_manager.is_skill_unlocked(sid)
		var is_sel: bool = (selected_skill_id == sid) or (hovered_skill_id == sid)
		if is_sel or is_unl:
			_astrolabe_conduit_canvas.draw_arc(pt2, rad2 + 6.0, 0.0, TAU, 32, COL_HEADER_GOLD if is_unl else b_col.lightened(0.25), 2.4)


func _on_vfx_overlay_canvas_draw() -> void:
	if vfx_overlay_canvas == null or not is_menu_open:
		return
	for rg: Dictionary in active_shockwave_rings:
		var c: Vector2 = rg["center"] as Vector2
		var rad: float = float(rg["radius"])
		var life: float = float(rg["life"])
		var max_l: float = float(rg["max_life"])
		var alpha: float = clampf(1.0 - (life / maxf(0.01, max_l)), 0.0, 1.0)
		var col: Color = rg["color"] as Color
		vfx_overlay_canvas.draw_arc(c, rad, 0.0, TAU, 48, Color(1.0, 0.88, 0.38, alpha * 0.92), 3.0)
		vfx_overlay_canvas.draw_arc(c, rad * 0.85, 0.0, TAU, 40, Color(col.r, col.g, col.b, alpha * 0.75), 1.8)

	for sp: Dictionary in active_spark_bursts:
		var pos: Vector2 = sp["pos"] as Vector2
		var vel: Vector2 = sp["vel"] as Vector2
		var life: float = float(sp["life"])
		var max_l: float = float(sp["max_life"])
		var alpha: float = clampf(1.0 - (life / maxf(0.01, max_l)), 0.0, 1.0)
		var col: Color = sp["color"] as Color
		var sz: float = float(sp["size"])
		var tail: Vector2 = pos - vel.normalized() * (sz * 3.2)
		vfx_overlay_canvas.draw_line(tail, pos, Color(col.r, col.g, col.b, alpha * 0.85), sz * 0.75)
		vfx_overlay_canvas.draw_circle(pos, sz, Color(1.0, 0.96, 0.78, alpha))
