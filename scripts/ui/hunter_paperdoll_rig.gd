class_name HunterPaperDollRig
extends Node3D

const WEAPON_GLB_PATHS: Dictionary[String, String] = {
	"revolver": "res://assets/models/weapons/viewmodel_right_revolver.glb",
	"shotgun": "res://assets/models/weapons/viewmodel_right_shotgun.glb",
	"stakedriver": "res://assets/models/weapons/viewmodel_right_stakedriver.glb"
}
const LANTERN_GLB_PATH: String = "res://assets/models/weapons/viewmodel_left_lantern.glb"
const MANNEQUIN_GLB_PATH: String = "res://assets/models/armor/gothic_arming_mannequin.glb"
const ARMORY_PLATE_SHADER_PATH: String = "res://shaders/gothic_armory_plate.gdshader"
const GAUNTLET_GLB_PATHS: Array[String] = [
	"res://assets/models/armor/gauntlet_01_leather_stalker.glb",
	"res://assets/models/armor/gauntlet_02_inquisitor_brigandine.glb",
	"res://assets/models/armor/gauntlet_03_juggernaut_plate.glb",
	"res://assets/models/armor/gauntlet_04_abyssal_reliquary.glb"
]
const BASE_HIP_X: float = 0.25
static var _armor_scene_cache: Dictionary[String, PackedScene] = {}
static var _armory_shader_cache: Shader = null

var plinth_root: Node3D = null
var studio_lighting_root: Node3D = null
var under_body_root: Node3D = null
var mannequin_instance: Node3D = null
var head_root: Node3D = null
var chest_root: Node3D = null
var hands_root: Node3D = null
var legs_root: Node3D = null
var feet_root: Node3D = null
var weapon_hand_mount: Node3D = null
var lantern_hip_mount: Node3D = null
var key_light: OmniLight3D = null
var rim_light: SpotLight3D = null
var plinth_light: OmniLight3D = null

var equipped_slots: Dictionary[String, int] = {
	"HEAD": -1,
	"CHEST": -1,
	"HANDS": -1,
	"LEGS": -1,
	"FEET": -1
}
var equipped_slot_model_paths: Dictionary[String, String] = {
	"HEAD": "",
	"CHEST": "",
	"HANDS": "",
	"LEGS": "",
	"FEET": ""
}
var active_weapon_id: String = ""
var _weapon_instance: Node3D = null
var _lantern_instance: Node3D = null
var _breath_time: float = 0.0
var _initialized: bool = false


func _init() -> void:
	_ensure_rig_hierarchy()


func _ready() -> void:
	_ensure_rig_hierarchy()
	var p: Node = get_parent()
	if p != null and p.get_parent() != null and p.get_parent().has_node("GothicKeyLight"):
		if studio_lighting_root != null:
			studio_lighting_root.visible = false
	for slot_k: String in ["HEAD", "CHEST", "HANDS", "LEGS", "FEET"]:
		if equipped_slots.get(slot_k, -1) < 0:
			equip_slot_visual(slot_k, 0)
	if active_weapon_id.is_empty():
		equip_weapon_visual("revolver")


func _ensure_rig_hierarchy() -> void:
	if _initialized:
		return
	_initialized = true
	name = "HunterPaperDollRig"
	preload_all_armor_scenes()

	plinth_root = Node3D.new()
	plinth_root.name = "ObsidianPlinthRoot"
	add_child(plinth_root)
	_spawn_cyl(plinth_root, "OctagonalStonePlinth", Vector3(0.0, -0.07, 0.0), 0.48, 0.54, 0.14, _make_mat(Color.html("#1f2024"), 0.15, 0.86), 8)
	_spawn_cyl(plinth_root, "PlinthBrassRing", Vector3(0.0, 0.005, 0.0), 0.49, 0.49, 0.02, _make_mat(Color.html("#6e552b"), 0.80, 0.50), 8)

	_build_studio_lighting()
	_build_anatomical_under_body()

	feet_root = Node3D.new()
	feet_root.name = "FeetRoot"
	add_child(feet_root)

	legs_root = Node3D.new()
	legs_root.name = "LegsRoot"
	add_child(legs_root)

	chest_root = Node3D.new()
	chest_root.name = "ChestRoot"
	chest_root.rotation_degrees = Vector3.ZERO
	add_child(chest_root)

	hands_root = Node3D.new()
	hands_root.name = "HandsRoot"
	hands_root.rotation_degrees = Vector3.ZERO
	add_child(hands_root)

	head_root = Node3D.new()
	head_root.name = "HeadRoot"
	head_root.rotation_degrees = Vector3.ZERO
	add_child(head_root)

	# Left Hip / Revolver Mount (X < 0, canted outward +12 deg on Z)
	weapon_hand_mount = Node3D.new()
	weapon_hand_mount.name = "WeaponHandMount"
	weapon_hand_mount.position = Vector3(-BASE_HIP_X, 0.96, 0.14)
	weapon_hand_mount.rotation_degrees = Vector3(-16.0, -142.0, 12.0)
	hands_root.add_child(weapon_hand_mount)

	# Right Hip / Weeper's Lantern Mount (X > 0, canted outward -12 deg on Z)
	lantern_hip_mount = Node3D.new()
	lantern_hip_mount.name = "LanternHipMount"
	lantern_hip_mount.position = Vector3(BASE_HIP_X, 0.94, 0.16)
	lantern_hip_mount.rotation_degrees = Vector3(10.0, 168.0, -12.0)
	hands_root.add_child(lantern_hip_mount)


func _process(delta: float) -> void:
	_breath_time += delta
	var b_sin: float = sin(_breath_time * 2.1)
	if chest_root != null:
		chest_root.position.y = b_sin * 0.008
	if hands_root != null:
		hands_root.position.y = b_sin * 0.010
	if head_root != null:
		head_root.position.y = b_sin * 0.006
	if lantern_hip_mount != null:
		var cant_sign: float = -1.0 if lantern_hip_mount.position.x >= 0.0 else 1.0
		lantern_hip_mount.rotation.z = deg_to_rad(12.0 * cant_sign) + sin(_breath_time * 2.8) * 0.04


func refresh_from_loadout(loadout: Node) -> void:
	_ensure_rig_hierarchy()
	if loadout == null:
		return
	var slots_dict: Dictionary = {}
	if "equipped_armor_slots" in loadout:
		slots_dict = loadout.get("equipped_armor_slots") as Dictionary
	var fallback_set: int = int(loadout.get("equipped_armor_index")) if ("equipped_armor_index" in loadout) else 0
	for slot_k: String in ["HEAD", "CHEST", "HANDS", "LEGS", "FEET"]:
		var s_idx: int = posmod(int(slots_dict.get(slot_k, fallback_set)), 4)
		equip_slot_visual(slot_k, s_idx)
	var weap_id: String = String(loadout.get("active_weapon_id")) if ("active_weapon_id" in loadout) else "revolver"
	equip_weapon_visual(weap_id)


func _clear_slot_meshes(container: Node3D) -> void:
	for child: Node in container.get_children():
		if child == weapon_hand_mount or child == lantern_hip_mount:
			continue
		container.remove_child(child)
		child.free()


func _get_set_palette(set_idx: int) -> Dictionary[String, Variant]:
	match posmod(set_idx, 4):
		1:
			return {
				"primary": _make_mat(Color(0.20, 0.25, 0.34), 0.88, 0.34),
				"secondary": _make_mat(Color(0.42, 0.08, 0.12), 0.10, 0.84),
				"trim": _make_mat(Color(0.86, 0.72, 0.34), 0.88, 0.32),
				"glow": _make_mat(Color(0.45, 0.86, 1.0), 0.0, 0.2, true)
			}
		2:
			return {
				"primary": _make_mat(Color(0.68, 0.56, 0.28), 0.92, 0.28),
				"secondary": _make_mat(Color(0.22, 0.20, 0.24), 0.82, 0.42),
				"trim": _make_mat(Color(0.96, 0.80, 0.36), 0.94, 0.24),
				"glow": _make_mat(Color(1.0, 0.72, 0.24), 0.0, 0.2, true)
			}
		3:
			return {
				"primary": _make_mat(Color(0.14, 0.09, 0.18), 0.78, 0.36),
				"secondary": _make_mat(Color(0.76, 0.72, 0.64), 0.15, 0.78),
				"trim": _make_mat(Color(0.92, 0.20, 0.32), 0.85, 0.30),
				"glow": _make_mat(Color(0.84, 0.36, 1.0), 0.0, 0.2, true)
			}
		_:
			return {
				"primary": _make_mat(Color(0.18, 0.13, 0.10), 0.22, 0.72),
				"secondary": _make_mat(Color(0.11, 0.09, 0.12), 0.12, 0.86),
				"trim": _make_mat(Color(0.68, 0.54, 0.28), 0.82, 0.38),
				"glow": _make_mat(Color(1.0, 0.68, 0.26), 0.0, 0.2, true)
			}


static func preload_all_armor_scenes() -> void:
	_get_cached_armor_scene(MANNEQUIN_GLB_PATH)
	for s_i: int in range(4):
		for slot_id: String in ["head", "chest", "legs", "feet"]:
			var p: String = "res://assets/models/armor/armor_set%d_%s.glb" % [s_i, slot_id]
			_get_cached_armor_scene(p)
		_get_cached_armor_scene(get_armor_glb_path("HANDS", s_i))


static func get_armor_glb_path(slot_name: String, set_idx: int) -> String:
	var s_key: String = slot_name.to_upper().strip_edges()
	var c_idx: int = posmod(set_idx, 4)
	if s_key == "HANDS":
		var hands_set_path: String = "res://assets/models/armor/armor_set%d_hands.glb" % c_idx
		if ResourceLoader.exists(hands_set_path):
			return hands_set_path
		if ResourceLoader.exists(GAUNTLET_GLB_PATHS[c_idx]):
			return GAUNTLET_GLB_PATHS[c_idx]
		var alt_weap_gauntlet: String = "res://assets/models/weapons/gauntlet_0%d.glb" % (c_idx + 1)
		if ResourceLoader.exists(alt_weap_gauntlet):
			return alt_weap_gauntlet
		return GAUNTLET_GLB_PATHS[c_idx]
	var slot_low: String = s_key.to_lower()
	return "res://assets/models/armor/armor_set%d_%s.glb" % [c_idx, slot_low]


static func _get_cached_armor_scene(res_path: String) -> PackedScene:
	if _armor_scene_cache.has(res_path):
		return _armor_scene_cache[res_path]
	if ResourceLoader.exists(res_path):
		var scn: PackedScene = load(res_path) as PackedScene
		if scn != null:
			_armor_scene_cache[res_path] = scn
			return scn
	return null


func preview_single_armor_piece(slot_name: String, set_idx: int) -> void:
	equip_slot_visual(slot_name, set_idx)


func equip_slot_visual(slot_name: String, set_idx: int) -> void:
	_ensure_rig_hierarchy()
	var s_key: String = slot_name.to_upper().strip_edges()
	var c_idx: int = posmod(set_idx, 4)
	var model_path: String = get_armor_glb_path(s_key, c_idx)
	if int(equipped_slots.get(s_key, -1)) == c_idx and String(equipped_slot_model_paths.get(s_key, "")) == model_path:
		return
	equipped_slots[s_key] = c_idx
	equipped_slot_model_paths[s_key] = model_path
	var scn: PackedScene = _get_cached_armor_scene(model_path)

	match s_key:
		"HEAD":
			_clear_slot_meshes(head_root)
			head_root.set_meta("source_model_path", model_path)
			if scn != null:
				var inst: Node3D = scn.instantiate() as Node3D
				if inst != null:
					inst.name = "ArmorHead_Set%d" % c_idx
					inst.position = Vector3(0.0, 1.54, 0.0)
					inst.scale = Vector3.ONE
					inst.set_meta("source_model_path", model_path)
					_apply_grimdark_armory_shader_recursive(inst, c_idx)
					head_root.add_child(inst)
		"CHEST":
			_clear_slot_meshes(chest_root)
			chest_root.set_meta("source_model_path", model_path)
			if scn != null:
				var inst_c: Node3D = scn.instantiate() as Node3D
				if inst_c != null:
					inst_c.name = "ArmorChest_Set%d" % c_idx
					inst_c.position = Vector3(0.0, 0.96, 0.0)
					inst_c.scale = Vector3.ONE
					inst_c.set_meta("source_model_path", model_path)
					_apply_grimdark_armory_shader_recursive(inst_c, c_idx)
					chest_root.add_child(inst_c)
		"HANDS":
			_clear_slot_meshes(hands_root)
			hands_root.set_meta("source_model_path", model_path)
			if scn != null:
				if model_path.contains("armor_set"):
					var h_inst: Node3D = scn.instantiate() as Node3D
					if h_inst != null:
						h_inst.name = "ArmorGauntlet_Pair_Set%d" % c_idx
						h_inst.position = Vector3(0.0, 1.05, 0.0)
						h_inst.rotation_degrees = Vector3.ZERO
						h_inst.scale = Vector3.ONE
						h_inst.set_meta("source_model_path", model_path)
						_apply_grimdark_armory_shader_recursive(h_inst, c_idx)
						hands_root.add_child(h_inst)
				else:
					for side_f: float in [-1.0, 1.0]:
						var s_tag: String = "L" if side_f < 0.0 else "R"
						var g_inst: Node3D = scn.instantiate() as Node3D
						if g_inst != null:
							var n_dir: Vector3 = Vector3(side_f * 0.92, 0.0, 0.38).normalized()
							var fit_g: Dictionary = _compute_surface_normal_offset("HANDS", c_idx, n_dir)
							g_inst.name = "ArmorGauntlet_%s_Set%d" % [s_tag, c_idx]
							g_inst.position = Vector3(side_f * 0.22, 1.05, 0.05) + (fit_g["offset"] as Vector3)
							g_inst.rotation_degrees = Vector3(35.0, 0.0 if side_f > 0.0 else 180.0, side_f * -12.0)
							g_inst.scale = Vector3(side_f * 0.65, 0.65, 0.65)
							g_inst.set_meta("source_model_path", model_path)
							_apply_grimdark_armory_shader_recursive(g_inst, c_idx)
							hands_root.add_child(g_inst)
			if _lantern_instance == null and ResourceLoader.exists(LANTERN_GLB_PATH):
				var l_scn: PackedScene = load(LANTERN_GLB_PATH) as PackedScene
				if l_scn != null:
					_lantern_instance = l_scn.instantiate() as Node3D
					if _lantern_instance != null:
						_lantern_instance.scale = Vector3.ONE * 0.55
						lantern_hip_mount.add_child(_lantern_instance)
		"LEGS":
			_clear_slot_meshes(legs_root)
			legs_root.set_meta("source_model_path", model_path)
			if scn != null:
				for side_l: float in [-1.0, 1.0]:
					var l_tag: String = "L" if side_l < 0.0 else "R"
					var leg_inst: Node3D = scn.instantiate() as Node3D
					if leg_inst != null:
						leg_inst.name = "ArmorLeg_%s_Set%d" % [l_tag, c_idx]
						leg_inst.position = Vector3(side_l * 0.125, 0.88, 0.0)
						leg_inst.rotation_degrees = Vector3.ZERO
						leg_inst.scale = Vector3(-1.0 if side_l < 0.0 else 1.0, 1.0, 1.0)
						leg_inst.set_meta("source_model_path", model_path)
						_apply_grimdark_armory_shader_recursive(leg_inst, c_idx)
						legs_root.add_child(leg_inst)
		"FEET":
			_clear_slot_meshes(feet_root)
			feet_root.set_meta("source_model_path", model_path)
			if scn != null:
				for side_b: float in [-1.0, 1.0]:
					var f_tag: String = "L" if side_b < 0.0 else "R"
					var boot_inst: Node3D = scn.instantiate() as Node3D
					if boot_inst != null:
						boot_inst.name = "ArmorBoot_%s_Set%d" % [f_tag, c_idx]
						boot_inst.position = Vector3(side_b * 0.125, 0.18, 0.0)
						boot_inst.rotation_degrees = Vector3(0.0, side_b * -6.0, 0.0)
						boot_inst.scale = Vector3(-1.0 if side_b < 0.0 else 1.0, 1.0, 1.0)
						boot_inst.set_meta("source_model_path", model_path)
						_apply_grimdark_armory_shader_recursive(boot_inst, c_idx)
						feet_root.add_child(boot_inst)

	_update_holster_mounts_for_armor()



func equip_weapon_visual(weapon_id: String) -> void:
	_ensure_rig_hierarchy()
	var w_key: String = weapon_id if WEAPON_GLB_PATHS.has(weapon_id) else "revolver"
	if active_weapon_id == w_key and _weapon_instance != null and is_instance_valid(_weapon_instance):
		return
	active_weapon_id = w_key
	if _weapon_instance != null and is_instance_valid(_weapon_instance):
		if _weapon_instance.get_parent() != null:
			_weapon_instance.get_parent().remove_child(_weapon_instance)
		_weapon_instance.free()
		_weapon_instance = null
	var w_path: String = WEAPON_GLB_PATHS[w_key]
	if ResourceLoader.exists(w_path):
		var w_scn: PackedScene = load(w_path) as PackedScene
		if w_scn != null:
			_weapon_instance = w_scn.instantiate() as Node3D
			if _weapon_instance != null:
				_weapon_instance.scale = Vector3.ONE * 0.58
				weapon_hand_mount.add_child(_weapon_instance)


func _make_mat(col: Color, met: float, rough: float, emissive: bool = false) -> StandardMaterial3D:
	var mat: StandardMaterial3D = StandardMaterial3D.new()
	mat.albedo_color = col
	mat.metallic = met
	mat.roughness = rough
	if emissive:
		mat.emission_enabled = true
		mat.emission = col
		mat.emission_energy_multiplier = 2.2
	return mat


func _spawn_cyl(parent: Node3D, n_name: String, pos: Vector3, r_top: float, r_bot: float, h: float, mat: StandardMaterial3D, segs: int = 8) -> MeshInstance3D:
	var mi: MeshInstance3D = MeshInstance3D.new()
	mi.name = n_name
	var cyl: CylinderMesh = CylinderMesh.new()
	cyl.top_radius = r_top
	cyl.bottom_radius = r_bot
	cyl.height = h
	cyl.radial_segments = segs
	cyl.material = mat
	mi.mesh = cyl
	mi.position = pos
	parent.add_child(mi)
	return mi


func _spawn_box(parent: Node3D, n_name: String, pos: Vector3, sz: Vector3, mat: StandardMaterial3D) -> MeshInstance3D:
	var mi: MeshInstance3D = MeshInstance3D.new()
	mi.name = n_name
	var bm: BoxMesh = BoxMesh.new()
	bm.size = sz
	bm.material = mat
	mi.mesh = bm
	mi.position = pos
	parent.add_child(mi)
	return mi


func _build_studio_lighting() -> void:
	studio_lighting_root = Node3D.new()
	studio_lighting_root.name = "StudioLightingRoot"
	add_child(studio_lighting_root)

	# Key Light (OmniLight3D): front-left, color #ffaa55, energy 1.1, range 4.0
	key_light = OmniLight3D.new()
	key_light.name = "WarmGoldKeyLight"
	key_light.light_color = Color.html("#ffaa55")
	key_light.light_energy = 1.1
	key_light.omni_range = 4.0
	key_light.position = Vector3(-1.15, 1.35, 1.45)
	studio_lighting_root.add_child(key_light)

	# Rim Light (SpotLight3D): top-rear, color #6688aa, energy 1.8, angled down at shoulders/hat
	rim_light = SpotLight3D.new()
	rim_light.name = "ColdCyanRimLight"
	rim_light.light_color = Color.html("#6688aa")
	rim_light.light_energy = 1.8
	rim_light.spot_range = 5.0
	rim_light.spot_angle = 42.0
	rim_light.position = Vector3(0.0, 2.35, -1.35)
	rim_light.rotation_degrees = Vector3(-34.0, 180.0, 0.0)
	studio_lighting_root.add_child(rim_light)

	# Fill Light (OmniLight3D): front-right low, color #553377, energy 0.35
	plinth_light = OmniLight3D.new()
	plinth_light.name = "CrimsonPlinthUnderGlow"
	plinth_light.light_color = Color.html("#553377")
	plinth_light.light_energy = 0.35
	plinth_light.omni_range = 3.5
	plinth_light.position = Vector3(1.10, 0.55, 1.25)
	studio_lighting_root.add_child(plinth_light)


func _build_anatomical_under_body() -> void:
	under_body_root = Node3D.new()
	under_body_root.name = "UnderBodyRoot"
	add_child(under_body_root)

	var m_scn: PackedScene = _get_cached_armor_scene(MANNEQUIN_GLB_PATH)
	if m_scn != null:
		mannequin_instance = m_scn.instantiate() as Node3D
		if mannequin_instance != null:
			mannequin_instance.name = "GothicArmingMannequin"
			mannequin_instance.position = Vector3.ZERO
			_apply_mannequin_doublet_materials_recursive(mannequin_instance)
			under_body_root.add_child(mannequin_instance)


func _apply_mannequin_doublet_materials_recursive(n: Node) -> void:
	_apply_grimdark_armory_shader_recursive(n, 0)


func _compute_surface_normal_offset(slot_name: String, set_idx: int, normal_dir: Vector3) -> Dictionary[String, Variant]:
	var s_key: String = slot_name.to_upper().strip_edges()
	var c_idx: int = posmod(set_idx, 4)
	var r_limb: float = 0.14
	var t_plate: float = 0.018 + float(c_idx) * 0.008
	match s_key:
		"HEAD":
			r_limb = 0.095
			t_plate = 0.016 + float(c_idx) * 0.006
		"CHEST":
			r_limb = 0.168
			t_plate = 0.024 + float(c_idx) * 0.010
		"HANDS":
			r_limb = 0.052
			t_plate = 0.018 + float(c_idx) * 0.006
		"LEGS":
			r_limb = 0.076
			t_plate = 0.020 + float(c_idx) * 0.008
		"FEET":
			r_limb = 0.058
			t_plate = 0.018 + float(c_idx) * 0.006

	var clearance: float = r_limb + (t_plate * 0.5) + 0.005
	var radial_scale: float = clearance / maxf(r_limb, 0.05)

	# Guardrail 2: Full wrap-around meshes (HEAD, CHEST, FEET) scale radially in X/Z to clear r_limb
	# around the entire circumference rather than shifting exclusively forward on +Z.
	if s_key == "HEAD" or s_key == "CHEST" or s_key == "FEET":
		return {
			"offset": Vector3.ZERO,
			"scale": Vector3(radial_scale, 1.0, radial_scale),
			"clearance": clearance
		}

	# One-sided / directional limb plates & gauntlets translate outward along the socket surface normal
	var n_vec: Vector3 = normal_dir.normalized() if normal_dir.length_squared() > 0.0001 else Vector3.ZERO
	return {
		"offset": n_vec * clearance,
		"scale": Vector3(radial_scale, 1.0, radial_scale),
		"clearance": clearance
	}


func _update_holster_mounts_for_armor() -> void:
	var chest_tier: int = maxi(0, int(equipped_slots.get("CHEST", 0)))
	var legs_tier: int = maxi(0, int(equipped_slots.get("LEGS", 0)))
	var tier_max: int = maxi(chest_tier, legs_tier)
	var armor_margin: float = 0.035 + float(tier_max) * 0.024
	if legs_root != null and legs_root.get_child_count() > 0:
		for ch: Node in legs_root.get_children():
			if ch is Node3D:
				var leg_n: Node3D = ch as Node3D
				for sub: Node in leg_n.get_children():
					if sub is MeshInstance3D:
						var mi: MeshInstance3D = sub as MeshInstance3D
						if mi.mesh != null:
							var half_w: float = mi.mesh.get_aabb().size.x * 0.5 * absf(leg_n.scale.x)
							armor_margin = maxf(armor_margin, half_w * 0.38 + float(tier_max) * 0.018)

	var hip_x: float = BASE_HIP_X + armor_margin
	var show_hip_holsters: bool = false
	if weapon_hand_mount != null:
		weapon_hand_mount.visible = show_hip_holsters
		weapon_hand_mount.position = Vector3(-hip_x, 0.96, 0.14)
		weapon_hand_mount.rotation_degrees = Vector3(-16.0, -142.0, 12.0)
	if lantern_hip_mount != null:
		lantern_hip_mount.visible = show_hip_holsters
		lantern_hip_mount.position = Vector3(hip_x, 0.94, 0.16)
		lantern_hip_mount.rotation_degrees = Vector3(10.0, 168.0, -12.0)


func _apply_grimdark_armory_shader_recursive(n: Node, set_idx: int) -> void:
	if _armory_shader_cache == null and ResourceLoader.exists(ARMORY_PLATE_SHADER_PATH):
		_armory_shader_cache = load(ARMORY_PLATE_SHADER_PATH) as Shader
	var c_idx: int = posmod(set_idx, 4)
	if n is MeshInstance3D:
		var mi: MeshInstance3D = n as MeshInstance3D
		if mi.mesh != null and _armory_shader_cache != null:
			var sc: int = mi.mesh.get_surface_count()
			for s_i: int in range(sc):
				var orig_mat: Material = mi.mesh.surface_get_material(s_i)
				var m_name: String = orig_mat.resource_name.to_lower() if orig_mat != null else ""
				var smat: ShaderMaterial = ShaderMaterial.new()
				smat.shader = _armory_shader_cache
				smat.set_shader_parameter("use_vertex_color", 1.0)
				smat.set_shader_parameter("triplanar_scale", 22.0)
				smat.set_shader_parameter("macro_patina_scale", 4.5)
				smat.set_shader_parameter("grain_strength", 0.10)
				smat.set_shader_parameter("edge_wear_strength", 0.42)

				if m_name.begins_with("set") and orig_mat is StandardMaterial3D:
					var std_m: StandardMaterial3D = orig_mat as StandardMaterial3D
					var base_c: Color = std_m.albedo_color
					var uscore_idx: int = m_name.rfind("_")
					if uscore_idx >= 0 and m_name.length() - uscore_idx == 7:
						var hex_part: String = m_name.substr(uscore_idx + 1, 6)
						if hex_part.is_valid_hex_number(false):
							base_c = Color.html("#" + hex_part)
					smat.set_shader_parameter("albedo_color", base_c)
					smat.set_shader_parameter("edge_wear_color", base_c.lightened(0.28))
					smat.set_shader_parameter("metallic_val", std_m.metallic)
					smat.set_shader_parameter("roughness_val", std_m.roughness)
					if m_name.contains("eyecrimson"):
						smat.set_shader_parameter("emission_color", Color.html("#d92b14"))
						smat.set_shader_parameter("emission_energy", 2.2)
					elif m_name.contains("candleflame"):
						smat.set_shader_parameter("emission_color", Color.html("#ff8811"))
						smat.set_shader_parameter("emission_energy", 2.5)
					elif m_name.contains("embervisor"):
						smat.set_shader_parameter("emission_color", Color.html("#ff5511"))
						smat.set_shader_parameter("emission_energy", 2.4)
					elif m_name.contains("nocturnite"):
						smat.set_shader_parameter("emission_color", Color.html("#8822cc"))
						smat.set_shader_parameter("emission_energy", 1.8)
					elif m_name.contains("cinderrune"):
						smat.set_shader_parameter("emission_color", Color.html("#ff6611"))
						smat.set_shader_parameter("emission_energy", 2.8)
					elif m_name.contains("censerember"):
						smat.set_shader_parameter("emission_color", Color.html("#ff7722"))
						smat.set_shader_parameter("emission_energy", 2.5)
					else:
						smat.set_shader_parameter("emission_energy", 0.0)

				elif m_name.contains("rune") or m_name.contains("emissive") or m_name.contains("glow") or s_i == 3:
					var rune_col: Color = Color.html("#8822cc") if c_idx == 3 else Color.html("#d94014")
					smat.set_shader_parameter("albedo_color", rune_col)
					smat.set_shader_parameter("edge_wear_color", rune_col.lightened(0.25))
					smat.set_shader_parameter("metallic_val", 0.15)
					smat.set_shader_parameter("roughness_val", 0.30)
					smat.set_shader_parameter("emission_color", rune_col)
					smat.set_shader_parameter("emission_energy", 2.0)
				elif m_name.contains("brass") or m_name.contains("gold") or m_name.contains("trim") or m_name.contains("silver") or s_i == 2:
					smat.set_shader_parameter("albedo_color", Color.html("#8c6d3a"))
					smat.set_shader_parameter("edge_wear_color", Color.html("#b89454"))
					smat.set_shader_parameter("metallic_val", 0.80)
					smat.set_shader_parameter("roughness_val", 0.46)
					smat.set_shader_parameter("emission_energy", 0.0)
				elif m_name.contains("leather") or m_name.contains("coat") or m_name.contains("velvet") or m_name.contains("bone") or (c_idx == 0 and s_i == 0) or (c_idx > 0 and s_i == 1):
					smat.set_shader_parameter("albedo_color", Color.html("#3d2d26"))
					smat.set_shader_parameter("edge_wear_color", Color.html("#5e473d"))
					smat.set_shader_parameter("metallic_val", 0.08)
					smat.set_shader_parameter("roughness_val", 0.78)
					smat.set_shader_parameter("emission_energy", 0.0)
				else:
					smat.set_shader_parameter("albedo_color", Color.html("#363942"))
					smat.set_shader_parameter("edge_wear_color", Color.html("#686e7c"))
					smat.set_shader_parameter("metallic_val", 0.82)
					smat.set_shader_parameter("roughness_val", 0.42)
					smat.set_shader_parameter("emission_energy", 0.0)
				mi.set_surface_override_material(s_i, smat)
	for ch: Node in n.get_children():
		_apply_grimdark_armory_shader_recursive(ch, c_idx)
