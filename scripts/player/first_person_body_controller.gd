class_name FirstPersonBodyController
extends Node3D

var loadout_manager: PlayerLoadoutManager = null
var torso_node: Node3D = null
var left_leg_pivot: Node3D = null
var right_leg_pivot: Node3D = null
var left_boot_pivot: Node3D = null
var right_boot_pivot: Node3D = null
var head_shadow_mesh: MeshInstance3D = null
var _coat_tail_left: MeshInstance3D = null
var _coat_tail_right: MeshInstance3D = null

var equipped_chest_set: int = -1
var equipped_legs_set: int = -1
var equipped_feet_set: int = -1
var equipped_chest_model_path: String = ""
var equipped_legs_model_path: String = ""
var equipped_feet_model_path: String = ""
static var _fp_armor_cache: Dictionary[String, PackedScene] = {}

var _stride_phase: float = 0.0
var _tracked_yaw: float = 0.0
var _yaw_initialized: bool = false
var _landing_compress: float = 0.0
var _was_grounded: bool = true
var _initialized: bool = false


func _init() -> void:
	_ensure_hierarchy()


func _ready() -> void:
	_ensure_hierarchy()
	_bind_loadout_manager()
	refresh_armor_appearance()
	_apply_first_person_shadow_only(self)


func _ensure_hierarchy() -> void:
	if _initialized:
		return
	_initialized = true
	name = "FirstPersonBodyController"
	position = Vector3(0.0, 0.0, -0.16)

	torso_node = Node3D.new()
	torso_node.name = "TorsoNode"
	torso_node.position = Vector3(0.0, 1.12, 0.24)
	add_child(torso_node)

	left_leg_pivot = Node3D.new()
	left_leg_pivot.name = "LeftLegPivot"
	left_leg_pivot.position = Vector3(-0.16, 0.88, 0.22)
	add_child(left_leg_pivot)

	left_boot_pivot = Node3D.new()
	left_boot_pivot.name = "BootPivot"
	left_boot_pivot.position = Vector3(0.0, -0.44, 0.0)
	left_leg_pivot.add_child(left_boot_pivot)

	right_leg_pivot = Node3D.new()
	right_leg_pivot.name = "RightLegPivot"
	right_leg_pivot.position = Vector3(0.16, 0.88, 0.22)
	add_child(right_leg_pivot)

	right_boot_pivot = Node3D.new()
	right_boot_pivot.name = "BootPivot"
	right_boot_pivot.position = Vector3(0.0, -0.44, 0.0)
	right_leg_pivot.add_child(right_boot_pivot)

	# Shadow-Only Head & Shoulders Proxy at Y = 1.62m so full-body silhouette shadows cast on dungeon floors/walls
	head_shadow_mesh = MeshInstance3D.new()
	head_shadow_mesh.name = "HeadShadowMesh"
	var h_cyl: CylinderMesh = CylinderMesh.new()
	h_cyl.top_radius = 0.19
	h_cyl.bottom_radius = 0.14
	h_cyl.height = 0.34
	h_cyl.radial_segments = 12
	head_shadow_mesh.mesh = h_cyl
	head_shadow_mesh.position = Vector3(0.0, 1.62, 0.20)
	head_shadow_mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
	add_child(head_shadow_mesh)

	_rebuild_chest_geometry(0)
	_rebuild_legs_geometry(0)
	_rebuild_feet_geometry(0)


func _bind_loadout_manager() -> void:
	if loadout_manager != null and is_instance_valid(loadout_manager):
		if not loadout_manager.loadout_changed.is_connected(refresh_armor_appearance):
			loadout_manager.loadout_changed.connect(refresh_armor_appearance)
		return
	var p: Node = get_parent()
	while p != null:
		var lm: PlayerLoadoutManager = p.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
		if lm != null:
			loadout_manager = lm
			if not loadout_manager.loadout_changed.is_connected(refresh_armor_appearance):
				loadout_manager.loadout_changed.connect(refresh_armor_appearance)
			return
		p = p.get_parent()


func refresh_armor_appearance() -> void:
	_ensure_hierarchy()
	_bind_loadout_manager()
	var chest_idx: int = 0
	var legs_idx: int = 0
	var feet_idx: int = 0
	if loadout_manager != null:
		chest_idx = posmod(int(loadout_manager.equipped_armor_slots.get("CHEST", loadout_manager.equipped_armor_index)), 4)
		legs_idx = posmod(int(loadout_manager.equipped_armor_slots.get("LEGS", loadout_manager.equipped_armor_index)), 4)
		feet_idx = posmod(int(loadout_manager.equipped_armor_slots.get("FEET", loadout_manager.equipped_armor_index)), 4)

	if chest_idx != equipped_chest_set or equipped_chest_model_path.is_empty():
		_rebuild_chest_geometry(chest_idx)
	if legs_idx != equipped_legs_set or equipped_legs_model_path.is_empty():
		_rebuild_legs_geometry(legs_idx)
	if feet_idx != equipped_feet_set or equipped_feet_model_path.is_empty():
		_rebuild_feet_geometry(feet_idx)
	_apply_first_person_shadow_only(self)


func update_body_motion(
	delta: float,
	velocity: Vector3,
	camera_yaw: float,
	camera_pitch: float,
	is_on_floor_flag: bool,
	is_dashing_flag: bool
) -> void:
	if not _initialized:
		_ensure_hierarchy()

	# 1. Yaw Follow with Natural Torso Lag
	if not _yaw_initialized:
		_tracked_yaw = camera_yaw
		_yaw_initialized = true
	else:
		_tracked_yaw = lerp_angle(_tracked_yaw, camera_yaw, minf(1.0, delta * 14.0))
	var yaw_lag: float = wrapf(_tracked_yaw - camera_yaw, -0.38, 0.38)
	rotation.y = yaw_lag

	# 2. Looking-Down Pitch Offset (camera_pitch < -0.35 rad slides torso/legs forward up to 0.10m)
	var look_down_t: float = clampf((-camera_pitch - 0.35) / 0.85, 0.0, 1.0)
	var forward_slide: float = -0.10 * look_down_t
	if not _was_grounded and is_on_floor_flag:
		_landing_compress = 0.07
	_was_grounded = is_on_floor_flag
	_landing_compress = move_toward(_landing_compress, 0.0, delta * 0.32)

	position = Vector3(0.0, -_landing_compress, -0.16 + forward_slide)
	if torso_node != null:
		torso_node.rotation.x = 0.08 * look_down_t + (0.14 if is_dashing_flag else 0.0)

	# 3. Walking / Sprinting Stride Cycle & Quickstep / Airborne Poses
	var h_speed: float = Vector2(velocity.x, velocity.z).length()
	_stride_phase = fmod(_stride_phase + delta * clampf(h_speed * 1.65, 0.0, 14.0), TAU)
	var stride_amp: float = clampf(h_speed / 8.5, 0.0, 1.0) * 0.55

	var l_hip_target: float = 0.0
	var r_hip_target: float = 0.0
	var l_knee_target: float = 0.0
	var r_knee_target: float = 0.0

	if is_dashing_flag:
		l_hip_target = 0.45
		r_hip_target = -0.50
		l_knee_target = -0.35
		r_knee_target = -0.42
	elif not is_on_floor_flag:
		l_hip_target = 0.25
		r_hip_target = -0.15
		l_knee_target = -0.32
		r_knee_target = -0.22
	else:
		var s_val: float = sin(_stride_phase)
		l_hip_target = s_val * stride_amp
		r_hip_target = -s_val * stride_amp
		l_knee_target = -maxf(0.0, -s_val) * 0.45
		r_knee_target = -maxf(0.0, s_val) * 0.45

	var blend: float = minf(1.0, delta * 16.0)
	if left_leg_pivot != null:
		left_leg_pivot.rotation.x = lerpf(left_leg_pivot.rotation.x, l_hip_target, blend)
	if right_leg_pivot != null:
		right_leg_pivot.rotation.x = lerpf(right_leg_pivot.rotation.x, r_hip_target, blend)
	if left_boot_pivot != null:
		left_boot_pivot.rotation.x = lerpf(left_boot_pivot.rotation.x, l_knee_target, blend)
	if right_boot_pivot != null:
		right_boot_pivot.rotation.x = lerpf(right_boot_pivot.rotation.x, r_knee_target, blend)

	if _coat_tail_left != null and _coat_tail_right != null:
		var flare: float = clampf(h_speed * 0.035, 0.0, 0.28) + (0.25 if is_dashing_flag else 0.0)
		_coat_tail_left.rotation.x = 0.14 + flare + maxf(0.0, -l_hip_target) * 0.45
		_coat_tail_right.rotation.x = 0.14 + flare + maxf(0.0, -r_hip_target) * 0.45


func _clear_children(n: Node3D) -> void:
	if n == null:
		return
	for ch: Node in n.get_children():
		n.remove_child(ch)
		ch.queue_free()


func _make_mat(albedo: Color, metallic: float, roughness: float) -> StandardMaterial3D:
	var m: StandardMaterial3D = StandardMaterial3D.new()
	m.albedo_color = albedo
	m.metallic = metallic
	m.roughness = roughness
	return m


func _get_set_materials(set_idx: int) -> Dictionary[String, StandardMaterial3D]:
	match posmod(set_idx, 4):
		1:
			return {
				"primary": _make_mat(Color(0.22, 0.28, 0.38, 1.0), 0.86, 0.34),
				"secondary": _make_mat(Color(0.38, 0.10, 0.14, 1.0), 0.12, 0.82),
				"trim": _make_mat(Color(0.84, 0.86, 0.92, 1.0), 0.90, 0.28)
			}
		2:
			return {
				"primary": _make_mat(Color(0.82, 0.66, 0.28, 1.0), 0.92, 0.26),
				"secondary": _make_mat(Color(0.28, 0.26, 0.30, 1.0), 0.80, 0.38),
				"trim": _make_mat(Color(0.98, 0.84, 0.38, 1.0), 0.94, 0.22)
			}
		3:
			return {
				"primary": _make_mat(Color(0.16, 0.11, 0.20, 1.0), 0.82, 0.34),
				"secondary": _make_mat(Color(0.76, 0.72, 0.62, 1.0), 0.18, 0.78),
				"trim": _make_mat(Color(0.92, 0.22, 0.36, 1.0), 0.86, 0.28)
			}
		_:
			return {
				"primary": _make_mat(Color(0.24, 0.17, 0.12, 1.0), 0.28, 0.74),
				"secondary": _make_mat(Color(0.15, 0.11, 0.09, 1.0), 0.15, 0.86),
				"trim": _make_mat(Color(0.76, 0.58, 0.26, 1.0), 0.84, 0.36)
			}


func _spawn_box(parent: Node3D, node_name: String, sz: Vector3, pos: Vector3, rot_deg: Vector3, mat: StandardMaterial3D) -> MeshInstance3D:
	var mi: MeshInstance3D = MeshInstance3D.new()
	mi.name = node_name
	var bm: BoxMesh = BoxMesh.new()
	bm.size = sz
	bm.material = mat
	mi.mesh = bm
	mi.position = pos
	mi.rotation_degrees = rot_deg
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
	parent.add_child(mi)
	return mi


static func _get_fp_cached_scene(res_path: String) -> PackedScene:
	if _fp_armor_cache.has(res_path):
		return _fp_armor_cache[res_path]
	if ResourceLoader.exists(res_path):
		var scn: PackedScene = load(res_path) as PackedScene
		if scn != null:
			_fp_armor_cache[res_path] = scn
			return scn
	return null


func _rebuild_chest_geometry(set_idx: int) -> void:
	equipped_chest_set = posmod(set_idx, 4)
	equipped_chest_model_path = "res://assets/models/armor/armor_set%d_chest.glb" % equipped_chest_set
	_clear_children(torso_node)
	if torso_node != null:
		torso_node.set_meta("source_model_path", equipped_chest_model_path)
	var scn: PackedScene = _get_fp_cached_scene(equipped_chest_model_path)
	if scn != null and torso_node != null:
		var inst: Node3D = scn.instantiate() as Node3D
		if inst != null:
			inst.name = "FPChestArmor_Set%d" % equipped_chest_set
			inst.position = Vector3(0.0, -0.18, -0.02)
			inst.rotation_degrees = Vector3(0.0, 180.0, 0.0)
			inst.set_meta("source_model_path", equipped_chest_model_path)
			_configure_fp_armor_meshes_recursive(inst)
			torso_node.add_child(inst)
	var mats: Dictionary[String, StandardMaterial3D] = _get_set_materials(equipped_chest_set)
	_coat_tail_left = _spawn_box(torso_node, "CoatTailLeft", Vector3(0.18, 0.36, 0.04), Vector3(-0.12, -0.38, 0.06), Vector3(8.0, 0.0, 4.0), mats["secondary"])
	_coat_tail_right = _spawn_box(torso_node, "CoatTailRight", Vector3(0.18, 0.36, 0.04), Vector3(0.12, -0.38, 0.06), Vector3(8.0, 0.0, -4.0), mats["secondary"])


func _rebuild_legs_geometry(set_idx: int) -> void:
	equipped_legs_set = posmod(set_idx, 4)
	equipped_legs_model_path = "res://assets/models/armor/armor_set%d_legs.glb" % equipped_legs_set
	for leg_piv: Node3D in [left_leg_pivot, right_leg_pivot]:
		if leg_piv == null:
			continue
		leg_piv.set_meta("source_model_path", equipped_legs_model_path)
		for ch: Node in leg_piv.get_children():
			if ch != left_boot_pivot and ch != right_boot_pivot:
				leg_piv.remove_child(ch)
				ch.free()
	var scn: PackedScene = _get_fp_cached_scene(equipped_legs_model_path)
	for s_i: int in range(2):
		var leg_p: Node3D = left_leg_pivot if s_i == 0 else right_leg_pivot
		var side_sign: float = -1.0 if s_i == 0 else 1.0
		if leg_p != null and scn != null:
			var inst_l: Node3D = scn.instantiate() as Node3D
			if inst_l != null:
				inst_l.name = "FPLegArmor_%s_Set%d" % ["L" if s_i == 0 else "R", equipped_legs_set]
				inst_l.position = Vector3(0.0, 0.0, 0.0)
				inst_l.rotation_degrees = Vector3(0.0, 180.0, 0.0)
				inst_l.scale = Vector3(side_sign, 1.0, 1.0)
				inst_l.set_meta("source_model_path", equipped_legs_model_path)
				_configure_fp_armor_meshes_recursive(inst_l)
				leg_p.add_child(inst_l)


func _rebuild_feet_geometry(set_idx: int) -> void:
	equipped_feet_set = posmod(set_idx, 4)
	equipped_feet_model_path = "res://assets/models/armor/armor_set%d_feet.glb" % equipped_feet_set
	if left_boot_pivot != null:
		left_boot_pivot.set_meta("source_model_path", equipped_feet_model_path)
		for ch_l: Node in left_boot_pivot.get_children():
			left_boot_pivot.remove_child(ch_l)
			ch_l.free()
	if right_boot_pivot != null:
		right_boot_pivot.set_meta("source_model_path", equipped_feet_model_path)
		for ch_r: Node in right_boot_pivot.get_children():
			right_boot_pivot.remove_child(ch_r)
			ch_r.free()
	var scn: PackedScene = _get_fp_cached_scene(equipped_feet_model_path)
	for s_b: int in range(2):
		var b_piv: Node3D = left_boot_pivot if s_b == 0 else right_boot_pivot
		var side_sign_b: float = -1.0 if s_b == 0 else 1.0
		if b_piv != null and scn != null:
			var inst_b: Node3D = scn.instantiate() as Node3D
			if inst_b != null:
				inst_b.name = "FPBootArmor_%s_Set%d" % ["L" if s_b == 0 else "R", equipped_feet_set]
				inst_b.position = Vector3(0.0, -0.26, -0.02)
				inst_b.rotation_degrees = Vector3(0.0, 180.0, 0.0)
				inst_b.scale = Vector3(side_sign_b, 1.0, 1.0)
				inst_b.set_meta("source_model_path", equipped_feet_model_path)
				_configure_fp_armor_meshes_recursive(inst_b)
				b_piv.add_child(inst_b)


func _configure_fp_armor_meshes_recursive(n: Node) -> void:
	if n is GeometryInstance3D:
		(n as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
	if n is MeshInstance3D:
		var mi: MeshInstance3D = n as MeshInstance3D
		if mi.mesh != null:
			var sc: int = mi.mesh.get_surface_count()
			for s_i: int in range(sc):
				var mat: Material = mi.get_surface_override_material(s_i)
				if mat == null:
					mat = mi.mesh.surface_get_material(s_i)
				if mat is StandardMaterial3D:
					var sm: StandardMaterial3D = (mat as StandardMaterial3D).duplicate() as StandardMaterial3D
					var m_name: String = mat.resource_name.to_lower()
					sm.vertex_color_use_as_albedo = true
					if m_name.contains("mat_iron"):
						sm.albedo_color = Color.html("#2c3038")
						sm.metallic = 0.82
						sm.roughness = 0.46
					elif m_name.contains("mat_leather"):
						sm.albedo_color = Color.html("#32241e")
						sm.metallic = 0.08
						sm.roughness = 0.80
					elif m_name.contains("mat_brass"):
						sm.albedo_color = Color.html("#7a5e30")
						sm.metallic = 0.80
						sm.roughness = 0.48
					elif m_name.contains("mat_runeglow"):
						sm.albedo_color = Color.html("#d94014")
						sm.emission_enabled = true
						sm.emission = Color.html("#d94014")
						sm.emission_energy_multiplier = 2.0
					mi.set_surface_override_material(s_i, sm)
	for ch: Node in n.get_children():
		_configure_fp_armor_meshes_recursive(ch)


func _apply_first_person_shadow_only(root_node: Node) -> void:
	if root_node == null:
		return
	if root_node is GeometryInstance3D:
		(root_node as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
	for ch: Node in root_node.get_children():
		_apply_first_person_shadow_only(ch)
