class_name OccultEnemyAI
extends TestDummyEnemy

enum AIState {
	IDLE = 0,
	ALERT = 1,
	CHASE = 2,
	STRAFE_ORBIT = 3,
	WINDUP = 4,
	ATTACK = 5,
	STAGGER = 6,
	DEAD = 7
}

@export var is_passive_dummy: bool = false
@export var combat_archetype: String = "MELEE_RUSHER"
@export var move_speed: float = 3.8
@export var aggro_range: float = 18.0
@export var attack_range: float = 2.4
@export var attack_damage: float = 20.0
@export var attack_cooldown: float = 1.65
@export var windup_duration: float = 0.50
@export var is_champion: bool = false
@export var biome_tier: int = 1

var xp_reward: int = 25
var projectile_speed_mult: float = 1.0
var _base_archetype_hp: float = 100.0
var _base_archetype_dmg: float = 20.0
var _base_archetype_speed: float = 3.8
var _base_windup_duration: float = 0.50
var _cached_base_stats: bool = false

var current_state: int = AIState.IDLE
var state_timer: float = 0.0
var attack_cooldown_timer: float = 0.0
var strafe_sign: float = 1.0
var has_aggroed: bool = false

# 12-to-14 Pivot Biomechanical Rig Nodes
var pelvis_node: Node3D = null
var thigh_l_node: Node3D = null
var shin_l_node: Node3D = null
var thigh_r_node: Node3D = null
var shin_r_node: Node3D = null
var torso_node: Node3D = null
var head_node: Node3D = null
var upper_arm_l_node: Node3D = null
var forearm_l_node: Node3D = null
var upper_arm_r_node: Node3D = null
var forearm_r_node: Node3D = null
var secondary_prop_node: Node3D = null

# Legacy aliases for backwards compatibility
var left_arm_node: Node3D = null
var right_arm_node: Node3D = null

var _pelvis_base_pos: Vector3 = Vector3(0.0, 0.95, 0.0)
var _pelvis_base_rot: Vector3 = Vector3.ZERO
var _thigh_l_base_rot: Vector3 = Vector3.ZERO
var _shin_l_base_rot: Vector3 = Vector3.ZERO
var _thigh_r_base_rot: Vector3 = Vector3.ZERO
var _shin_r_base_rot: Vector3 = Vector3.ZERO
var _torso_base_rot: Vector3 = Vector3.ZERO
var _head_base_rot: Vector3 = Vector3.ZERO
var _uarm_l_base_rot: Vector3 = Vector3.ZERO
var _farm_l_base_rot: Vector3 = Vector3.ZERO
var _uarm_r_base_rot: Vector3 = Vector3.ZERO
var _farm_r_base_rot: Vector3 = Vector3.ZERO
var _sec_prop_base_pos: Vector3 = Vector3.ZERO
var _sec_prop_base_rot: Vector3 = Vector3.ZERO

# Locational Hit-Flinch Springs (decays at exp(-delta * 14.0))
var flinch_torso_rot: Vector3 = Vector3.ZERO
var flinch_head_rot: Vector3 = Vector3.ZERO
var flinch_arm_l: float = 0.0
var flinch_arm_r: float = 0.0

var _walk_cycle_phase: float = 0.0
var _attack_combo_index: int = 0
var _attack_executed_in_cycle: bool = false
var _blink_cooldown_timer: float = 0.0
var _death_collapse_timer: float = 0.0
const DEATH_COLLAPSE_DURATION: float = 0.55
const ATTACK_DURATION: float = 0.36

var _emissive_materials: Array[StandardMaterial3D] = []
var _base_emissive_colors: Array[Color] = []
var _emissive_mesh_instances: Array[MeshInstance3D] = []
var _emissive_surface_indices: Array[int] = []
var _emissive_orig_mats: Array[StandardMaterial3D] = []

var _sfx_player: AudioStreamPlayer3D = null
var _sfx_aggro: AudioStream = null
var _sfx_windup: AudioStream = null
var _sfx_slash: AudioStream = null
var _sfx_spell: AudioStream = null
var _sfx_bell_slam: AudioStream = null

var _status_label: Label3D = null
var _has_taken_damage: bool = false
var _last_displayed_hp: int = -1

# Staggered 0.10s raycast / LOS / stair-lookup throttling (Phase 2.2)
var _raycast_throttle_timer: float = 0.0
var _cached_los: bool = true
var _cached_steered_dir: Vector3 = Vector3.ZERO
var _stair_lookup_timer: float = 0.0
var _cached_stair_entry: Vector3 = Vector3.INF

static var _shared_champ_emissive_mat: StandardMaterial3D = null
static var _shared_telegraph_emissive_mat: StandardMaterial3D = null
static var _shared_shockwave_torus: TorusMesh = null
static var _shared_shockwave_mat: StandardMaterial3D = null
static var _shared_sfx_loaded: bool = false
static var _shared_sfx_aggro: AudioStream = null
static var _shared_sfx_windup: AudioStream = null
static var _shared_sfx_slash: AudioStream = null
static var _shared_sfx_spell: AudioStream = null
static var _shared_sfx_bell_slam: AudioStream = null


static func _ensure_shared_enemy_resources() -> void:
	if _shared_champ_emissive_mat == null:
		_shared_champ_emissive_mat = StandardMaterial3D.new()
		_shared_champ_emissive_mat.albedo_color = Color(1.0, 0.38, 0.12, 1.0)
		_shared_champ_emissive_mat.emission_enabled = true
		_shared_champ_emissive_mat.emission = Color(1.0, 0.38, 0.12, 1.0)
		_shared_champ_emissive_mat.emission_energy_multiplier = 4.2
		_shared_champ_emissive_mat.roughness = 0.45
	if _shared_telegraph_emissive_mat == null:
		_shared_telegraph_emissive_mat = StandardMaterial3D.new()
		_shared_telegraph_emissive_mat.albedo_color = Color(1.0, 0.45, 0.12, 1.0)
		_shared_telegraph_emissive_mat.emission_enabled = true
		_shared_telegraph_emissive_mat.emission = Color(1.0, 0.45, 0.12, 1.0)
		_shared_telegraph_emissive_mat.emission_energy_multiplier = 5.5
		_shared_telegraph_emissive_mat.roughness = 0.35
	if _shared_shockwave_torus == null:
		_shared_shockwave_torus = TorusMesh.new()
		_shared_shockwave_torus.inner_radius = 0.85
		_shared_shockwave_torus.outer_radius = 1.15
		_shared_shockwave_torus.rings = 16
		_shared_shockwave_torus.ring_segments = 8
	if _shared_shockwave_mat == null:
		_shared_shockwave_mat = StandardMaterial3D.new()
		_shared_shockwave_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		_shared_shockwave_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		_shared_shockwave_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
		_shared_shockwave_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
		_shared_shockwave_mat.albedo_color = Color(1.0, 0.48, 0.16, 0.72)


func _strip_any_omni_lights_recursive(node: Node) -> void:
	for child: Node in node.get_children():
		if child is OmniLight3D:
			node.remove_child(child)
			child.free()
		else:
			_strip_any_omni_lights_recursive(child)


func _ready() -> void:
	super._ready()
	_ensure_shared_enemy_resources()
	_strip_any_omni_lights_recursive(self)
	if not _is_dead and current_state != AIState.DEAD:
		collision_layer = 4
		collision_mask = 1 | 2
	floor_max_angle = deg_to_rad(54.0)
	floor_snap_length = 0.55
	floor_stop_on_slope = true
	floor_constant_speed = true
	floor_block_on_wall = true
	_ensure_alive_collision_shape()
	strafe_sign = 1.0 if (get_instance_id() % 2 == 0) else -1.0
	_raycast_throttle_timer = float(get_instance_id() % 6) * 0.016
	_stair_lookup_timer = float(get_instance_id() % 6) * 0.04
	_resolve_articulated_nodes()
	_setup_enemy_audio()
	_apply_archetype_defaults()
	_ensure_status_label()


func _ensure_alive_collision_shape() -> void:
	var col: CollisionShape3D = get_node_or_null("EnemyCapsuleCollider") as CollisionShape3D
	if col == null:
		col = get_node_or_null("CollisionShape3D") as CollisionShape3D
	if col == null:
		for child: Node in get_children():
			if child is CollisionShape3D:
				col = child as CollisionShape3D
				break
	if col == null:
		col = CollisionShape3D.new()
		col.name = "EnemyCapsuleCollider"
		add_child(col)
	var cap: CapsuleShape3D = col.shape as CapsuleShape3D
	if cap == null:
		cap = CapsuleShape3D.new()
		col.shape = cap
	cap.radius = 0.42
	cap.height = 1.85
	col.position = Vector3(0.0, 0.95, 0.0)
	if not _is_dead and current_state != AIState.DEAD:
		col.disabled = false


func _disable_all_colliders_on_death() -> void:
	collision_layer = 0
	collision_mask = 0
	for child: Node in get_children():
		if child is CollisionShape3D:
			(child as CollisionShape3D).disabled = true


func _ensure_status_label() -> void:
	if _status_label != null:
		return
	var existing: Label3D = get_node_or_null("EnemyStatusLabel3D") as Label3D
	if existing != null:
		_status_label = existing
	else:
		_status_label = Label3D.new()
		_status_label.name = "EnemyStatusLabel3D"
		_status_label.position = Vector3(0.0, 2.25, 0.0)
		_status_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		_status_label.font_size = 24
		_status_label.outline_size = 6
		_status_label.modulate = Color(1.0, 0.42, 0.36, 0.92)
		_status_label.visible = false
		add_child(_status_label)
	_update_status_label_text()


func _update_status_label_text() -> void:
	if _status_label != null:
		var hp_int: int = maxi(0, roundi(current_health))
		if hp_int == _last_displayed_hp and not _status_label.text.is_empty():
			return
		_last_displayed_hp = hp_int
		_status_label.text = "%s [%d / %d]" % [
			enemy_title,
			hp_int,
			roundi(max_health)
		]


func _apply_archetype_defaults() -> void:
	match combat_archetype:
		"MELEE_RUSHER":
			move_speed = 4.8
			attack_range = 2.3
			attack_damage = 18.0 * depth_scale
			attack_cooldown = 1.25
		"SHIELD_GUARD":
			move_speed = 3.1
			attack_range = 2.5
			attack_damage = 24.0 * depth_scale
			attack_cooldown = 1.85
			if flat_armor < 12.0:
				flat_armor = 15.0
		"RANGED_CASTER":
			move_speed = 3.4
			attack_range = 11.5
			attack_damage = 20.0 * depth_scale
			attack_cooldown = 2.6
		"HEAVY_BRUTE":
			move_speed = 3.2
			attack_range = 3.2
			attack_damage = 28.0 * depth_scale
			attack_cooldown = 2.1
			if flat_armor < 10.0:
				flat_armor = 15.0
		"RANGED_LOBBER_EXPLODER":
			move_speed = 3.2
			attack_range = 11.0
			attack_damage = 22.0 * depth_scale
			attack_cooldown = 2.6
		"BLINK_WRAITH":
			move_speed = 4.4
			attack_range = 10.5
			attack_damage = 21.0 * depth_scale
			attack_cooldown = 2.1
		"SONIC_JUGGERNAUT":
			move_speed = 3.0
			attack_range = 3.2
			attack_damage = 32.0 * depth_scale
			attack_cooldown = 2.3
			if flat_armor < 15.0:
				flat_armor = 18.0
		"ELITE_HYBRID_LORD":
			move_speed = 4.2
			attack_range = 9.5
			attack_damage = 30.0 * depth_scale
			attack_cooldown = 1.85
			if flat_armor < 12.0:
				flat_armor = 14.0
		"RANGED_BONE_ARBALEST":
			move_speed = 3.3
			attack_range = 14.0
			attack_damage = 19.0 * depth_scale
			attack_cooldown = 2.2
		"RANGED_SPREAD_HEXER":
			move_speed = 3.4
			attack_range = 12.5
			attack_damage = 16.0 * depth_scale
			attack_cooldown = 2.5
		"RANGED_CANTOR_SWARM":
			move_speed = 3.6
			attack_range = 13.0
			attack_damage = 18.0 * depth_scale
			attack_cooldown = 2.4
		"RANGED_PLAGUE_MORTAR":
			move_speed = 3.0
			attack_range = 13.5
			attack_damage = 23.0 * depth_scale
			attack_cooldown = 2.7
	if not _cached_base_stats:
		_cached_base_stats = true
		_base_archetype_hp = maxf(60.0, max_health)
		_base_archetype_dmg = maxf(10.0, attack_damage)
		_base_archetype_speed = maxf(2.0, move_speed)
		_base_windup_duration = maxf(0.25, windup_duration)


func apply_depth_scaling(tier: int, b_id: int = 0) -> void:
	super.apply_depth_scaling(tier, b_id)
	_apply_archetype_defaults()


func configure_for_biome_tier(tier: int, is_champion_flag: bool = false) -> void:
	if not _cached_base_stats:
		_apply_archetype_defaults()
	biome_tier = clampi(tier, 1, 8)
	biome_relic_id = biome_tier
	is_champion = is_champion_flag

	var t_steps: float = float(biome_tier - 1)
	var hp_mult: float = 1.0 + t_steps * 0.34
	var dmg_mult: float = 1.0 + t_steps * 0.22
	var spd_mult: float = 1.0 + t_steps * 0.035
	var windup_mult: float = maxf(0.50, 1.0 - t_steps * 0.05)

	max_health = roundf(_base_archetype_hp * hp_mult)
	attack_damage = roundf(_base_archetype_dmg * dmg_mult)
	move_speed = _base_archetype_speed * spd_mult
	projectile_speed_mult = spd_mult
	windup_duration = _base_windup_duration * windup_mult
	xp_reward = roundi(25.0 * (1.0 + pow(t_steps, 1.35) * 0.54))

	if is_champion:
		scale = Vector3(1.22, 1.22, 1.22)
		max_health = roundf(max_health * 1.65)
		attack_damage = roundf(attack_damage * 1.20)
		xp_reward = roundi(float(xp_reward) * 1.50)
		if not enemy_title.begins_with("Anointed "):
			enemy_title = "Anointed " + enemy_title
		_apply_champion_rim_glow()
	else:
		scale = Vector3.ONE

	current_health = max_health
	_update_status_label_text()


func _apply_champion_rim_glow() -> void:
	_ensure_shared_enemy_resources()
	_strip_any_omni_lights_recursive(self)
	for i: int in range(_emissive_mesh_instances.size()):
		var mi: MeshInstance3D = _emissive_mesh_instances[i]
		if mi != null and is_instance_valid(mi):
			mi.set_surface_override_material(_emissive_surface_indices[i], _shared_champ_emissive_mat)
	for i: int in range(_base_emissive_colors.size()):
		_base_emissive_colors[i] = Color(1.0, 0.38, 0.12, 1.0)


func promote_to_anointed_champion() -> void:
	configure_for_biome_tier(maxi(1, biome_tier), true)


func configure_as_elite_champion() -> void:
	configure_for_biome_tier(maxi(1, biome_tier), true)


func _resolve_articulated_nodes() -> void:
	pelvis_node = find_child("Pelvis", true, false) as Node3D
	thigh_l_node = find_child("ThighL", true, false) as Node3D
	shin_l_node = find_child("ShinL", true, false) as Node3D
	thigh_r_node = find_child("ThighR", true, false) as Node3D
	shin_r_node = find_child("ShinR", true, false) as Node3D
	torso_node = find_child("Torso", true, false) as Node3D
	head_node = find_child("Head", true, false) as Node3D
	upper_arm_l_node = find_child("UpperArmL", true, false) as Node3D
	forearm_l_node = find_child("ForearmL", true, false) as Node3D
	upper_arm_r_node = find_child("UpperArmR", true, false) as Node3D
	forearm_r_node = find_child("ForearmR", true, false) as Node3D
	secondary_prop_node = find_child("SecondaryProp", true, false) as Node3D

	if upper_arm_l_node == null:
		upper_arm_l_node = find_child("LeftArm", true, false) as Node3D
	if upper_arm_r_node == null:
		upper_arm_r_node = find_child("RightArm", true, false) as Node3D
	left_arm_node = upper_arm_l_node
	right_arm_node = upper_arm_r_node

	if pelvis_node != null:
		_pelvis_base_pos = pelvis_node.position
		_pelvis_base_rot = pelvis_node.rotation
	if thigh_l_node != null:
		_thigh_l_base_rot = thigh_l_node.rotation
	if shin_l_node != null:
		_shin_l_base_rot = shin_l_node.rotation
	if thigh_r_node != null:
		_thigh_r_base_rot = thigh_r_node.rotation
	if shin_r_node != null:
		_shin_r_base_rot = shin_r_node.rotation
	if torso_node != null:
		_torso_base_rot = torso_node.rotation
	if head_node != null:
		_head_base_rot = head_node.rotation
	if upper_arm_l_node != null:
		_uarm_l_base_rot = upper_arm_l_node.rotation
	if forearm_l_node != null:
		_farm_l_base_rot = forearm_l_node.rotation
	if upper_arm_r_node != null:
		_uarm_r_base_rot = upper_arm_r_node.rotation
	if forearm_r_node != null:
		_farm_r_base_rot = forearm_r_node.rotation
	if secondary_prop_node != null:
		_sec_prop_base_pos = secondary_prop_node.position
		_sec_prop_base_rot = secondary_prop_node.rotation

	_emissive_materials.clear()
	_base_emissive_colors.clear()
	_emissive_mesh_instances.clear()
	_emissive_surface_indices.clear()
	_emissive_orig_mats.clear()
	_collect_emissive_materials_recursive(self)


func _collect_emissive_materials_recursive(node: Node) -> void:
	if node is MeshInstance3D:
		var mi: MeshInstance3D = node as MeshInstance3D
		if mi.mesh != null:
			for s_idx: int in range(mi.mesh.get_surface_count()):
				var mat: Material = mi.get_surface_override_material(s_idx)
				if mat == null:
					mat = mi.mesh.surface_get_material(s_idx)
				if mat is StandardMaterial3D:
					var std_mat: StandardMaterial3D = mat as StandardMaterial3D
					var mname: String = mat.resource_name.to_lower()
					if (
						std_mat.emission_enabled
						or mname.contains("emissive")
						or mname.contains("rune")
						or mname.contains("bile")
						or mname.contains("soul")
						or mname.contains("crimson")
						or mname.contains("flame")
					):
						_emissive_mesh_instances.append(mi)
						_emissive_surface_indices.append(s_idx)
						_emissive_orig_mats.append(std_mat)
						_emissive_materials.append(std_mat)
						_base_emissive_colors.append(std_mat.emission)
	for child: Node in node.get_children():
		_collect_emissive_materials_recursive(child)


func _setup_enemy_audio() -> void:
	if _sfx_player == null:
		_sfx_player = AudioStreamPlayer3D.new()
		_sfx_player.name = "EnemyCombatSFX3D"
		_sfx_player.unit_size = 4.5
		_sfx_player.max_distance = 26.0
		_sfx_player.volume_db = -1.5
		add_child(_sfx_player)
	if not _shared_sfx_loaded:
		_shared_sfx_loaded = true
		if ResourceLoader.exists("res://assets/audio/sfx/enemy_aggro_roar.wav"):
			_shared_sfx_aggro = load("res://assets/audio/sfx/enemy_aggro_roar.wav") as AudioStream
		if ResourceLoader.exists("res://assets/audio/sfx/enemy_windup_telegraph.wav"):
			_shared_sfx_windup = load("res://assets/audio/sfx/enemy_windup_telegraph.wav") as AudioStream
		if ResourceLoader.exists("res://assets/audio/sfx/enemy_melee_slash.wav"):
			_shared_sfx_slash = load("res://assets/audio/sfx/enemy_melee_slash.wav") as AudioStream
		if ResourceLoader.exists("res://assets/audio/sfx/enemy_spell_cast.wav"):
			_shared_sfx_spell = load("res://assets/audio/sfx/enemy_spell_cast.wav") as AudioStream
		if ResourceLoader.exists("res://assets/audio/sfx/enemy_sonic_bell_slam.wav"):
			_shared_sfx_bell_slam = load("res://assets/audio/sfx/enemy_sonic_bell_slam.wav") as AudioStream
	_sfx_aggro = _shared_sfx_aggro
	_sfx_windup = _shared_sfx_windup
	_sfx_slash = _shared_sfx_slash
	_sfx_spell = _shared_sfx_spell
	_sfx_bell_slam = _shared_sfx_bell_slam


func _play_enemy_sfx(stream: AudioStream) -> void:
	if _sfx_player != null and stream != null and is_inside_tree():
		_sfx_player.stream = stream
		_sfx_player.play()


func _set_telegraph_glow(flare_active: bool, _flare_energy: float = 5.5) -> void:
	_ensure_shared_enemy_resources()
	for i: int in range(_emissive_mesh_instances.size()):
		var mi: MeshInstance3D = _emissive_mesh_instances[i]
		if mi != null and is_instance_valid(mi):
			if flare_active:
				mi.set_surface_override_material(_emissive_surface_indices[i], _shared_telegraph_emissive_mat)
			elif is_champion:
				mi.set_surface_override_material(_emissive_surface_indices[i], _shared_champ_emissive_mat)
			else:
				mi.set_surface_override_material(_emissive_surface_indices[i], _emissive_orig_mats[i])


func _is_player_in_sanctuary_safe_zone(p_pos: Vector3) -> bool:
	return p_pos.y >= 2.8 and p_pos.z > -20.5 and p_pos.z < 5.0 and absf(p_pos.x) < 10.0


func _find_player_node() -> Node3D:
	if not is_inside_tree() or get_tree() == null:
		return null
	var grp_p: Node = get_tree().get_first_node_in_group("player")
	if grp_p is Node3D:
		return grp_p as Node3D
	var root_scn: Node = get_tree().current_scene if get_tree().current_scene != null else get_tree().root
	if root_scn != null:
		var p: Node3D = root_scn.find_child("Player", true, false) as Node3D
		if p == null:
			p = root_scn.find_child("FPSPlayer", true, false) as Node3D
		return p
	return null


func _physics_process(delta: float) -> void:
	# 5. Procedural Multi-Joint Death Collapse (DEAD state over 0.55s)
	if _is_dead or current_state == AIState.DEAD:
		current_state = AIState.DEAD
		_update_death_collapse(delta)
		return

	# Process DoT timers from parent TestDummyEnemy
	if _bile_dot_timer > 0.0:
		_bile_dot_timer = maxf(0.0, _bile_dot_timer - delta)
		super.apply_damage(_bile_dot_dps * delta, true)
		if _bile_dot_timer <= 0.0 and _bile_particles != null:
			_bile_particles.emitting = false
		if _is_dead:
			return

	if _burn_dot_timer > 0.0 and not _is_dead:
		_burn_dot_timer = maxf(0.0, _burn_dot_timer - delta)
		super.apply_damage(_burn_dot_dps * delta, true)
		if _is_dead:
			return

	if _blink_cooldown_timer > 0.0:
		_blink_cooldown_timer = maxf(0.0, _blink_cooldown_timer - delta)

	if attack_cooldown_timer > 0.0:
		attack_cooldown_timer = maxf(0.0, attack_cooldown_timer - delta)

	# Decay locational hit-flinch springs at exp(-delta * 14.0)
	var flinch_decay: float = exp(-delta * 14.0)
	flinch_torso_rot *= flinch_decay
	flinch_head_rot *= flinch_decay
	flinch_arm_l *= flinch_decay
	flinch_arm_r *= flinch_decay

	# Passive test range dummy mode
	if is_passive_dummy:
		if _shackle_timer > 0.0:
			_shackle_timer = maxf(0.0, _shackle_timer - delta)
		else:
			_time_acc += delta
			var sway_x: float = sin(_time_acc * 0.85 + _phase_offset) * (patrol_radius * 0.25)
			var sway_z: float = cos(_time_acc * 0.65 + _phase_offset) * (patrol_radius * 0.25)
			position = Vector3(_spawn_origin.x + sway_x, _spawn_origin.y, _spawn_origin.z + sway_z)
		_animate_articulated_rig(delta, 0.0, null, 0.0)
		return

	# Shackle / Stagger override
	if _shackle_timer > 0.0:
		_shackle_timer = maxf(0.0, _shackle_timer - delta)
		current_state = AIState.STAGGER
		velocity = Vector3.ZERO
		_set_telegraph_glow(false)
		_animate_articulated_rig(delta, 0.0, null, 0.0)
		if _shackle_timer <= 0.0:
			current_state = AIState.CHASE if has_aggroed else AIState.IDLE
		return

	var player: Node3D = _find_player_node()
	if player == null or _is_player_in_sanctuary_safe_zone(player.global_position):
		current_state = AIState.IDLE
		velocity = Vector3.ZERO
		if _status_label != null:
			_status_label.visible = false
		_set_telegraph_glow(false)
		_animate_articulated_rig(delta, 0.0, null, 0.0)
		return

	var dist_sq: float = global_position.distance_squared_to(player.global_position)
	var to_player: Vector3 = player.global_position - global_position
	var vert_diff: float = absf(to_player.y)

	# Distance-Based Enemy AI Throttling (Phase 6.2):
	# If > 30m away (dist_sq > 900.0) or vertical difference > 9.0m, hibernate AI, skip whisker raycasts, and hide Label3D
	if dist_sq > 900.0 or vert_diff > 9.0:
		velocity = Vector3.ZERO
		if _status_label != null:
			_status_label.visible = false
		return

	if _status_label != null:
		_status_label.visible = (dist_sq <= 196.0) or _has_taken_damage

	var flat_to_player: Vector3 = Vector3(to_player.x, 0.0, to_player.z)
	var dist_to_player: float = flat_to_player.length()

	# Face player smoothly on Y axis:
	# Enemy .glb meshes have their visual face, eyes, weapons, and shield along local -Z (-global_transform.basis.z).
	# atan2(-dx, -dz) aligns -global_transform.basis.z directly toward flat_to_player.
	if dist_to_player > 0.05:
		var target_yaw: float = atan2(-flat_to_player.x, -flat_to_player.z)
		rotation.y = lerp_angle(rotation.y, target_yaw, clampf(delta * 8.5, 0.0, 1.0))

	match current_state:
		AIState.IDLE:
			velocity.x = 0.0
			velocity.z = 0.0
			_apply_gravity_only(delta)
			if dist_to_player <= aggro_range and vert_diff <= 6.5:
				_enter_alert_state()
		AIState.ALERT:
			velocity.x = 0.0
			velocity.z = 0.0
			_apply_gravity_only(delta)
			state_timer -= delta
			if state_timer <= 0.0:
				current_state = AIState.CHASE
		AIState.CHASE, AIState.STRAFE_ORBIT:
			_process_chase_and_positioning(delta, player, flat_to_player, dist_to_player)
		AIState.WINDUP:
			velocity.x = 0.0
			velocity.z = 0.0
			_apply_gravity_only(delta)
			state_timer -= delta
			if state_timer <= 0.0:
				_enter_attack_state(player)
		AIState.ATTACK:
			velocity.x = 0.0
			velocity.z = 0.0
			_apply_gravity_only(delta)
			state_timer -= delta
			if state_timer <= 0.0:
				_set_telegraph_glow(false)
				current_state = AIState.CHASE
		AIState.STAGGER:
			velocity.x = 0.0
			velocity.z = 0.0
			_apply_gravity_only(delta)
			state_timer -= delta
			if state_timer <= 0.0:
				current_state = AIState.CHASE

	var horiz_speed: float = Vector2(velocity.x, velocity.z).length()
	_animate_articulated_rig(delta, horiz_speed, player, dist_sq)


func _apply_gravity_only(delta: float) -> void:
	if not is_inside_tree():
		return
	if not is_on_floor():
		velocity.y -= 24.0 * delta
	else:
		velocity.y = -0.1
	move_and_slide()
	_spawn_origin = position


func _enter_alert_state() -> void:
	has_aggroed = true
	current_state = AIState.ALERT
	state_timer = 0.22
	_play_enemy_sfx(_sfx_aggro)
	_set_telegraph_glow(false)


func _has_line_of_sight_to_player(player: Node3D) -> bool:
	if player == null or not is_instance_valid(player) or not is_inside_tree() or get_world_3d() == null:
		return false
	var space_state: PhysicsDirectSpaceState3D = get_world_3d().direct_space_state
	if space_state == null:
		return true
	var from_pos: Vector3 = global_position + Vector3(0.0, 1.30, 0.0)
	var to_pos: Vector3 = player.global_position + Vector3(0.0, 1.50, 0.0)
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(from_pos, to_pos, 1)
	var exclude_rids: Array[RID] = [self.get_rid()]
	if player is CollisionObject3D:
		exclude_rids.append((player as CollisionObject3D).get_rid())
	query.exclude = exclude_rids
	var hit: Dictionary = space_state.intersect_ray(query)
	if hit.is_empty():
		return true
	var col_obj: Object = hit.get("collider", null)
	if col_obj is Node and ((col_obj as Node).name == "Player" or (col_obj as Node).name == "FPSPlayer" or (col_obj as Node).is_in_group("player")):
		return true
	return false


func _find_nearest_staircase_entry_pos(player: Node3D) -> Vector3:
	if not is_inside_tree() or get_tree() == null:
		return Vector3.INF
	if _stair_lookup_timer > 0.0 and _cached_stair_entry != Vector3.INF:
		return _cached_stair_entry
	_stair_lookup_timer = 0.35
	var search_root: Node = get_parent() if get_parent() != null else get_tree().current_scene
	if search_root == null:
		return Vector3.INF
	var best_pos: Vector3 = Vector3.INF
	var best_dist_sq: float = 900.0
	var player_higher: bool = (player.global_position.y > global_position.y)
	for ch: Node in search_root.get_children():
		if ch is Node3D:
			var n3d: Node3D = ch as Node3D
			if n3d.name.begins_with("ProcStairs") or n3d.name.begins_with("StairsStone"):
				var entry_local: Vector3 = Vector3(0.0, -3.8, -2.2) if player_higher else Vector3(0.0, 0.0, 2.2)
				var entry_world: Vector3 = n3d.to_global(entry_local)
				if absf(entry_world.y - global_position.y) <= 2.4:
					var d_sq: float = global_position.distance_squared_to(entry_world)
					if d_sq < best_dist_sq:
						best_dist_sq = d_sq
						best_pos = entry_world
	_cached_stair_entry = best_pos
	return best_pos


func _process_chase_and_positioning(
	delta: float,
	player: Node3D,
	flat_to_player: Vector3,
	dist_to_player: float
) -> void:
	if _stair_lookup_timer > 0.0:
		_stair_lookup_timer = maxf(0.0, _stair_lookup_timer - delta)
	_raycast_throttle_timer -= delta
	var refresh_rays: bool = (_raycast_throttle_timer <= 0.0)
	if refresh_rays:
		_raycast_throttle_timer = 0.10
		_cached_los = _has_line_of_sight_to_player(player)

	var is_ranged: bool = (
		combat_archetype == "RANGED_CASTER"
		or combat_archetype == "RANGED_LOBBER_EXPLODER"
		or combat_archetype == "BLINK_WRAITH"
	)
	var elev_diff: float = absf(player.global_position.y - global_position.y)
	var has_los: bool = _cached_los

	if is_ranged:
		if dist_to_player <= attack_range and attack_cooldown_timer <= 0.0 and has_los:
			_enter_windup_state()
			return
		var desired_dir: Vector3 = flat_to_player.normalized() if dist_to_player > 0.05 else get_forward_dir()
		var right_perp: Vector3 = Vector3(-desired_dir.z, 0.0, desired_dir.x) * strafe_sign
		if elev_diff > 2.2 and not has_los:
			var stair_target: Vector3 = _find_nearest_staircase_entry_pos(player)
			if stair_target != Vector3.INF and dist_to_player < 5.5:
				var to_stair: Vector3 = Vector3(stair_target.x - global_position.x, 0.0, stair_target.z - global_position.z)
				if to_stair.length_squared() > 0.05:
					desired_dir = to_stair.normalized()
			else:
				desired_dir = (-desired_dir * 0.80 + right_perp * 0.60).normalized()
			current_state = AIState.STRAFE_ORBIT
		elif dist_to_player < 6.5:
			current_state = AIState.STRAFE_ORBIT
			desired_dir = (-desired_dir * 0.55 + right_perp * 0.85).normalized()
		elif dist_to_player <= 11.5:
			current_state = AIState.STRAFE_ORBIT
			desired_dir = (right_perp * 0.90 + desired_dir * 0.25).normalized()
		else:
			current_state = AIState.CHASE
		if refresh_rays or _cached_steered_dir.length_squared() < 0.01:
			_cached_steered_dir = _compute_whisker_steered_direction(desired_dir)
		velocity.x = _cached_steered_dir.x * move_speed
		velocity.z = _cached_steered_dir.z * move_speed
		_apply_horizontal_step(delta)
		return

	var effective_range: float = attack_range
	if combat_archetype == "ELITE_HYBRID_LORD":
		effective_range = 9.5 if ((_attack_combo_index % 2 == 1) and has_los) else 3.0

	if dist_to_player <= effective_range and elev_diff <= 2.2 and attack_cooldown_timer <= 0.0:
		_enter_windup_state()
		return

	current_state = AIState.CHASE
	var target_move_dir: Vector3 = flat_to_player.normalized() if dist_to_player > 0.05 else get_forward_dir()

	if elev_diff > 2.2:
		var stair_entry: Vector3 = _find_nearest_staircase_entry_pos(player)
		if stair_entry != Vector3.INF:
			var flat_to_stair: Vector3 = Vector3(stair_entry.x - global_position.x, 0.0, stair_entry.z - global_position.z)
			if flat_to_stair.length_squared() > 0.25:
				target_move_dir = flat_to_stair.normalized()
			else:
				target_move_dir = flat_to_player.normalized()

	if refresh_rays or _cached_steered_dir.length_squared() < 0.01:
		_cached_steered_dir = _compute_whisker_steered_direction(target_move_dir)
	velocity.x = _cached_steered_dir.x * move_speed
	velocity.z = _cached_steered_dir.z * move_speed
	_apply_horizontal_step(delta)


func _compute_whisker_steered_direction(desired_dir: Vector3) -> Vector3:
	if desired_dir.length_squared() < 0.001 or not is_inside_tree() or get_world_3d() == null:
		return desired_dir

	var space_state: PhysicsDirectSpaceState3D = get_world_3d().direct_space_state
	if space_state == null:
		return desired_dir

	var waist_origin: Vector3 = global_position + Vector3(0.0, 0.95, 0.0)
	var fan_angles_deg: Array[float] = [0.0, -27.0, 27.0, -55.0, 55.0]
	var ray_length: float = 2.6

	var accum_dir: Vector3 = Vector3.ZERO
	var valid_rays: int = 0

	for ang_deg: float in fan_angles_deg:
		var rad: float = deg_to_rad(ang_deg)
		var ray_dir: Vector3 = desired_dir.rotated(Vector3.UP, rad).normalized()
		var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
			waist_origin,
			waist_origin + ray_dir * ray_length,
			1
		)
		query.exclude = [self.get_rid()]
		var hit: Dictionary = space_state.intersect_ray(query)
		if hit.is_empty():
			var weight: float = 1.35 if absf(ang_deg) < 1.0 else (1.0 if absf(ang_deg) < 30.0 else 0.75)
			accum_dir += ray_dir * weight
			valid_rays += 1
		else:
			var col_obj: Object = hit.get("collider", null)
			if col_obj is Node and ((col_obj as Node).name == "Player" or (col_obj as Node).is_in_group("player")):
				return desired_dir

	if valid_rays > 0 and accum_dir.length_squared() > 0.001:
		return accum_dir.normalized()

	return Vector3(-desired_dir.z, 0.0, desired_dir.x).normalized() * strafe_sign


func _apply_horizontal_step(delta: float) -> void:
	if not is_inside_tree():
		var step_vec: Vector3 = Vector3(velocity.x, 0.0, velocity.z) * delta
		global_position += step_vec
		_spawn_origin = position
		return

	if not is_on_floor():
		velocity.y -= 24.0 * delta
	else:
		velocity.y = -0.1

	move_and_slide()

	if is_on_wall():
		var wall_n: Vector3 = get_wall_normal()
		wall_n.y = 0.0
		if wall_n.length_squared() > 0.001:
			wall_n = wall_n.normalized()
			var horiz_v: Vector3 = Vector3(velocity.x, 0.0, velocity.z).slide(wall_n)
			velocity.x = horiz_v.x
			velocity.z = horiz_v.z

	_spawn_origin = position


func _enter_windup_state() -> void:
	current_state = AIState.WINDUP
	state_timer = windup_duration
	_attack_executed_in_cycle = false
	velocity.x = 0.0
	velocity.z = 0.0
	_play_enemy_sfx(_sfx_windup)
	_set_telegraph_glow(true, 5.8)


func _enter_attack_state(player: Node3D) -> void:
	current_state = AIState.ATTACK
	state_timer = ATTACK_DURATION
	attack_cooldown_timer = attack_cooldown
	_set_telegraph_glow(false)

	if _attack_executed_in_cycle or player == null or not is_instance_valid(player):
		return
	_attack_executed_in_cycle = true
	_attack_combo_index += 1

	var to_player: Vector3 = player.global_position - global_position
	var dist: float = Vector3(to_player.x, 0.0, to_player.z).length()
	var dir_to_player: Vector3 = ((player.global_position + Vector3(0.0, 1.0, 0.0)) - (global_position + Vector3(0.0, 1.25, 0.0))).normalized()
	var has_los: bool = _has_line_of_sight_to_player(player)

	match combat_archetype:
		"RANGED_CASTER":
			if has_los:
				_play_enemy_sfx(_sfx_spell)
				_fire_projectile_at_player(player, dir_to_player, Color(0.84, 0.36, 1.0, 1.0), 13.5 * projectile_speed_mult, 0.0, 1.2)
		"RANGED_BONE_ARBALEST":
			if has_los:
				_play_enemy_sfx(_sfx_spell)
				_fire_projectile_at_player(player, dir_to_player, Color(0.95, 0.72, 0.32, 1.0), 21.0 * projectile_speed_mult, 0.0, 0.0)
		"RANGED_SPREAD_HEXER":
			if has_los:
				_play_enemy_sfx(_sfx_spell)
				for fan_deg: float in [-14.0, 0.0, 14.0]:
					var s_dir: Vector3 = dir_to_player.rotated(Vector3.UP, deg_to_rad(fan_deg))
					_fire_projectile_at_player(player, s_dir, Color(0.82, 0.28, 1.0, 1.0), 15.0 * projectile_speed_mult, 0.0, 0.3)
		"RANGED_CANTOR_SWARM":
			if has_los:
				_play_enemy_sfx(_sfx_spell)
				_fire_projectile_at_player(player, dir_to_player, Color(0.32, 0.88, 1.0, 1.0), 12.5 * projectile_speed_mult, 0.0, 1.65)
		"RANGED_LOBBER_EXPLODER", "RANGED_PLAGUE_MORTAR":
			if has_los:
				_play_enemy_sfx(_sfx_spell)
				_fire_projectile_at_player(player, dir_to_player + Vector3(0.0, 0.14, 0.0), Color(0.42, 0.96, 0.28, 1.0), 13.5 * projectile_speed_mult, 2.8, 0.0)
		"BLINK_WRAITH":
			if has_los:
				_play_enemy_sfx(_sfx_spell)
				_fire_projectile_at_player(player, dir_to_player, Color(0.28, 0.78, 1.0, 1.0), 14.5 * projectile_speed_mult, 0.0, 1.5)
		"HEAVY_BRUTE", "SONIC_JUGGERNAUT":
			_play_enemy_sfx(_sfx_bell_slam)
			_spawn_ground_shockwave_ring(Color(1.0, 0.55, 0.16, 1.0), 3.6)
			if dist <= attack_range + 0.8 and absf(to_player.y) <= 2.2:
				_deal_direct_damage_to_player(player, attack_damage)
		"ELITE_HYBRID_LORD":
			if dist <= 3.3 or (_attack_combo_index % 2 == 1 and dist <= 3.6):
				_play_enemy_sfx(_sfx_slash)
				_spawn_ground_shockwave_ring(Color(0.95, 0.12, 0.18, 1.0), 3.4)
				if dist <= 3.6 and absf(to_player.y) <= 2.2:
					_deal_direct_damage_to_player(player, attack_damage)
			elif has_los:
				_play_enemy_sfx(_sfx_spell)
				for fan_deg: float in [-14.0, 0.0, 14.0]:
					var f_dir: Vector3 = dir_to_player.rotated(Vector3.UP, deg_to_rad(fan_deg))
					_fire_projectile_at_player(player, f_dir, Color(0.95, 0.12, 0.18, 1.0), 13.5, 0.0, 0.8)
		_:
			_play_enemy_sfx(_sfx_slash)
			if dist <= attack_range + 0.65 and absf(to_player.y) <= 2.2:
				_deal_direct_damage_to_player(player, attack_damage)


func _deal_direct_damage_to_player(player: Node3D, dmg: float) -> void:
	var lm: PlayerLoadoutManager = player.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	if lm == null and get_tree() != null and get_tree().root != null:
		lm = get_tree().root.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	if lm != null:
		lm.apply_player_damage(dmg)


func get_forward_dir() -> Vector3:
	var fwd: Vector3 = -global_transform.basis.z
	fwd.y = 0.0
	if fwd.length_squared() < 0.0001:
		return Vector3(0.0, 0.0, -1.0)
	return fwd.normalized()


func is_attack_from_front(attacker_or_hit_pos: Vector3 = Vector3.ZERO) -> bool:
	var forward_dir: Vector3 = get_forward_dir()
	if attacker_or_hit_pos != Vector3.ZERO:
		var to_hit: Vector3 = Vector3(
			attacker_or_hit_pos.x - global_position.x,
			0.0,
			attacker_or_hit_pos.z - global_position.z
		)
		if to_hit.length_squared() > 0.0001:
			return forward_dir.dot(to_hit.normalized()) > 0.0
	var player: Node3D = _find_player_node()
	if player != null and is_instance_valid(player):
		var to_player: Vector3 = Vector3(
			player.global_position.x - global_position.x,
			0.0,
			player.global_position.z - global_position.z
		)
		if to_player.length_squared() > 0.0001:
			return forward_dir.dot(to_player.normalized()) > 0.0
	return true


func _fire_projectile_at_player(
	player: Node3D,
	dir_vec: Vector3,
	col: Color,
	proj_speed: float,
	arc_grav: float,
	homing: float
) -> EnemyProjectile:
	var scene_parent: Node = get_parent() if get_parent() != null else self
	var forward_dir: Vector3 = get_forward_dir()
	var spawn_pos: Vector3 = global_position + Vector3(0.0, 1.30, 0.0) + forward_dir * 1.2
	var aim_dir: Vector3 = dir_vec.normalized()
	if player != null and is_instance_valid(player):
		var to_target: Vector3 = (player.global_position + Vector3(0.0, 1.0, 0.0)) - spawn_pos
		if to_target.length_squared() > 0.01:
			aim_dir = (to_target.normalized() + Vector3(0.0, dir_vec.y - (dir_vec.normalized().y if dir_vec.length_squared() > 0.001 else 0.0), 0.0)).normalized()
	return EnemyProjectile.spawn_projectile(
		scene_parent,
		spawn_pos,
		aim_dir,
		attack_damage,
		col,
		proj_speed,
		arc_grav,
		homing,
		self,
		player
	)


func _spawn_ground_shockwave_ring(_col: Color, _radius: float) -> void:
	if not is_inside_tree() or get_tree() == null:
		return
	var scene_root: Node = get_parent() if get_parent() != null else get_tree().current_scene
	if scene_root == null:
		return

	_ensure_shared_enemy_resources()
	var ring_mi: MeshInstance3D = MeshInstance3D.new()
	ring_mi.name = "EnemyShockwaveRing"
	ring_mi.mesh = _shared_shockwave_torus
	ring_mi.material_override = _shared_shockwave_mat
	ring_mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	scene_root.add_child(ring_mi)
	ring_mi.global_position = global_position + Vector3(0.0, 0.25, 0.0)

	var tw: Tween = ring_mi.create_tween()
	tw.tween_property(ring_mi, "scale", Vector3(2.6, 1.0, 2.6), 0.35)
	tw.tween_callback(ring_mi.queue_free)


# ==============================================================================
# PHASE 2: BIOMECHANICAL PROCEDURAL ANIMATION SOLVER (12-14 PIVOT RIG)
# ==============================================================================

func _animate_articulated_rig(
	delta: float,
	speed_val: float,
	player: Node3D = null,
	dist_sq: float = 0.0
) -> void:
	if pelvis_node == null:
		return

	# Gate full joint math to when distance_sq < 484.0 (22m) for peak FPS
	if dist_sq > 484.0:
		return

	# Compute Predatory Head & Torso Look-At Tracking angles
	var look_yaw: float = 0.0
	var look_pitch: float = 0.0
	if (
		player != null
		and is_instance_valid(player)
		and (
			current_state == AIState.ALERT
			or current_state == AIState.CHASE
			or current_state == AIState.STRAFE_ORBIT
			or current_state == AIState.WINDUP
		)
	):
		var head_world: Vector3 = global_position + Vector3(0.0, 1.58, 0.0)
		var player_cam_world: Vector3 = player.global_position + Vector3(0.0, 1.55, 0.0)
		var to_cam: Vector3 = player_cam_world - head_world
		var flat_len: float = Vector2(to_cam.x, to_cam.z).length()
		if flat_len > 0.05:
			var world_yaw_to_player: float = atan2(-to_cam.x, -to_cam.z)
			var rel_yaw: float = wrapf(world_yaw_to_player - rotation.y, -PI, PI)
			look_yaw = clampf(rel_yaw * 0.65, -0.75, 0.75)
			var raw_pitch: float = atan2(to_cam.y, flat_len)
			look_pitch = clampf(raw_pitch * 0.50, -0.45, 0.45)

	# --------------------------------------------------------------------------
	# STATE: STAGGER (Heavy Buckling Stagger + Flinch Springs)
	# --------------------------------------------------------------------------
	if current_state == AIState.STAGGER:
		var b_stagger: float = clampf(delta * 16.0, 0.0, 1.0)
		pelvis_node.position = pelvis_node.position.lerp(_pelvis_base_pos + Vector3(0.0, -0.18, 0.0), b_stagger)
		pelvis_node.rotation = pelvis_node.rotation.lerp(_pelvis_base_rot, b_stagger)
		if thigh_l_node != null:
			thigh_l_node.rotation = thigh_l_node.rotation.lerp(_thigh_l_base_rot + Vector3(0.55, 0.0, 0.08), b_stagger)
		if shin_l_node != null:
			shin_l_node.rotation = shin_l_node.rotation.lerp(_shin_l_base_rot + Vector3(-0.95, 0.0, 0.0), b_stagger)
		if thigh_r_node != null:
			thigh_r_node.rotation = thigh_r_node.rotation.lerp(_thigh_r_base_rot + Vector3(0.55, 0.0, -0.08), b_stagger)
		if shin_r_node != null:
			shin_r_node.rotation = shin_r_node.rotation.lerp(_shin_r_base_rot + Vector3(-0.95, 0.0, 0.0), b_stagger)
		if torso_node != null:
			torso_node.rotation = torso_node.rotation.lerp(_torso_base_rot + Vector3(0.38, 0.0, 0.14), b_stagger) + flinch_torso_rot
		if head_node != null:
			head_node.rotation = head_node.rotation.lerp(_head_base_rot + Vector3(0.42, 0.0, -0.15), b_stagger) + flinch_head_rot
		if upper_arm_l_node != null:
			upper_arm_l_node.rotation = upper_arm_l_node.rotation.lerp(_uarm_l_base_rot + Vector3(0.35 + flinch_arm_l, 0.0, 0.55), b_stagger)
		if forearm_l_node != null:
			forearm_l_node.rotation = forearm_l_node.rotation.lerp(_farm_l_base_rot + Vector3(-0.35, 0.0, 0.0), b_stagger)
		if upper_arm_r_node != null:
			upper_arm_r_node.rotation = upper_arm_r_node.rotation.lerp(_uarm_r_base_rot + Vector3(0.35 + flinch_arm_r, 0.0, -0.55), b_stagger)
		if forearm_r_node != null:
			forearm_r_node.rotation = forearm_r_node.rotation.lerp(_farm_r_base_rot + Vector3(-0.35, 0.0, 0.0), b_stagger)
		return

	# --------------------------------------------------------------------------
	# STATE: WINDUP (Nonlinear ease(p, 0.45) Coil + 35Hz Muscular Tension Tremor)
	# --------------------------------------------------------------------------
	if current_state == AIState.WINDUP:
		var w_dur: float = maxf(0.05, windup_duration)
		var p_raw: float = clampf(1.0 - (state_timer / w_dur), 0.0, 1.0)
		var p_coil: float = ease(p_raw, 0.45)
		_walk_cycle_phase += delta * TAU * 35.0
		var tremor: float = sin(_walk_cycle_phase) * 0.035 * p_raw

		var is_caster_windup: bool = (
			combat_archetype == "RANGED_CASTER"
			or combat_archetype == "RANGED_LOBBER_EXPLODER"
			or combat_archetype == "BLINK_WRAITH"
		)

		pelvis_node.position = _pelvis_base_pos + Vector3(0.0, 0.04 * p_coil, 0.0)
		if thigh_l_node != null:
			thigh_l_node.rotation = _thigh_l_base_rot + Vector3(-0.18 * p_coil, 0.0, 0.0)
		if shin_l_node != null:
			shin_l_node.rotation = _shin_l_base_rot + Vector3(-0.22 * p_coil, 0.0, 0.0)
		if thigh_r_node != null:
			thigh_r_node.rotation = _thigh_r_base_rot + Vector3(0.24 * p_coil, 0.0, 0.0)
		if shin_r_node != null:
			shin_r_node.rotation = _shin_r_base_rot + Vector3(-0.32 * p_coil, 0.0, 0.0)

		if torso_node != null:
			torso_node.rotation = _torso_base_rot + Vector3(
				0.22 * p_coil + tremor * 0.5,
				-0.55 * p_coil + look_yaw * 0.25,
				0.0
			) + flinch_torso_rot

		if head_node != null:
			head_node.rotation = _head_base_rot + Vector3(
				look_pitch - 0.12 * p_coil,
				look_yaw + 0.35 * p_coil,
				tremor * 0.4
			) + flinch_head_rot

		if is_caster_windup:
			# Ranged casters draw both arms forward & inward toward the chest during WINDUP
			if upper_arm_l_node != null:
				upper_arm_l_node.rotation = _uarm_l_base_rot + Vector3(0.55 * p_coil + tremor + flinch_arm_l, 0.55 * p_coil, -0.32 * p_coil)
			if forearm_l_node != null:
				forearm_l_node.rotation = _farm_l_base_rot + Vector3(0.75 * p_coil + tremor, 0.55 * p_coil, 0.0)
			if upper_arm_r_node != null:
				upper_arm_r_node.rotation = _uarm_r_base_rot + Vector3(0.55 * p_coil - tremor + flinch_arm_r, -0.55 * p_coil, 0.32 * p_coil)
			if forearm_r_node != null:
				forearm_r_node.rotation = _farm_r_base_rot + Vector3(0.75 * p_coil + tremor, -0.55 * p_coil, 0.0)
		else:
			# Melee/Brute/Hybrid: raises UpperArmR high (-2.1 rad), bends ForearmR (+1.1 rad) with 35Hz tension tremor
			if upper_arm_r_node != null:
				upper_arm_r_node.rotation = _uarm_r_base_rot + Vector3(-2.10 * p_coil + tremor + flinch_arm_r, -0.18 * p_coil, -0.22 * p_coil)
			if forearm_r_node != null:
				forearm_r_node.rotation = _farm_r_base_rot + Vector3(1.10 * p_coil + tremor, 0.0, 0.0)
			if upper_arm_l_node != null:
				upper_arm_l_node.rotation = _uarm_l_base_rot + Vector3(0.65 * p_coil + flinch_arm_l, 0.25 * p_coil, 0.20 * p_coil)
			if forearm_l_node != null:
				forearm_l_node.rotation = _farm_l_base_rot + Vector3(0.45 * p_coil, 0.0, 0.0)

		if secondary_prop_node != null:
			secondary_prop_node.rotation.y += delta * 5.2
		return

	# --------------------------------------------------------------------------
	# STATE: ATTACK (Violent ease(p, 3.2) Whip Snap & Follow-Through)
	# --------------------------------------------------------------------------
	if current_state == AIState.ATTACK:
		var a_dur: float = maxf(0.05, ATTACK_DURATION)
		var p_atk_raw: float = clampf(1.0 - (state_timer / a_dur), 0.0, 1.0)
		var p_whip: float = ease(p_atk_raw, 3.2)

		var is_caster_atk: bool = (
			combat_archetype == "RANGED_CASTER"
			or combat_archetype == "RANGED_LOBBER_EXPLODER"
			or combat_archetype == "BLINK_WRAITH"
		)

		pelvis_node.position = _pelvis_base_pos + Vector3(0.0, -0.07 * p_whip, 0.0)
		if thigh_l_node != null:
			thigh_l_node.rotation = _thigh_l_base_rot + Vector3(0.32 * p_whip, 0.0, 0.0)
		if shin_l_node != null:
			shin_l_node.rotation = _shin_l_base_rot + Vector3(-0.38 * p_whip, 0.0, 0.0)
		if thigh_r_node != null:
			thigh_r_node.rotation = _thigh_r_base_rot + Vector3(-0.28 * p_whip, 0.0, 0.0)
		if shin_r_node != null:
			shin_r_node.rotation = _shin_r_base_rot + Vector3(-0.15 * p_whip, 0.0, 0.0)

		if torso_node != null:
			var t_x: float = lerpf(0.22, -0.28, p_whip)
			var t_y: float = lerpf(-0.55, 0.48, p_whip)
			torso_node.rotation = _torso_base_rot + Vector3(t_x, t_y, 0.0) + flinch_torso_rot

		if head_node != null:
			head_node.rotation = _head_base_rot + Vector3(lerpf(-0.12, 0.18, p_whip), look_yaw * 0.5, 0.0) + flinch_head_rot

		if is_caster_atk:
			# Thrust both arms wide open on projectile release
			if upper_arm_l_node != null:
				upper_arm_l_node.rotation = _uarm_l_base_rot + Vector3(lerpf(0.55, 0.65, p_whip) + flinch_arm_l, lerpf(0.55, -0.65, p_whip), 0.45 * p_whip)
			if forearm_l_node != null:
				forearm_l_node.rotation = _farm_l_base_rot + Vector3(lerpf(0.75, 0.0, p_whip), 0.0, 0.0)
			if upper_arm_r_node != null:
				upper_arm_r_node.rotation = _uarm_r_base_rot + Vector3(lerpf(0.55, 0.65, p_whip) + flinch_arm_r, lerpf(-0.55, 0.65, p_whip), -0.45 * p_whip)
			if forearm_r_node != null:
				forearm_r_node.rotation = _farm_r_base_rot + Vector3(lerpf(0.75, 0.0, p_whip), 0.0, 0.0)
		else:
			# Uncoils Torso forward (+0.48 rad twist, -0.28 rad lunge), whips UpperArmR down (+0.85 rad), snaps ForearmR straight (0.0 rad)
			if upper_arm_r_node != null:
				var u_rx: float = lerpf(-2.10, 0.85, p_whip)
				upper_arm_r_node.rotation = _uarm_r_base_rot + Vector3(u_rx + flinch_arm_r, 0.15 * p_whip, 0.10 * p_whip)
			if forearm_r_node != null:
				var f_rx: float = lerpf(1.10, 0.0, p_whip)
				forearm_r_node.rotation = _farm_r_base_rot + Vector3(f_rx, 0.0, 0.0)
			if upper_arm_l_node != null:
				upper_arm_l_node.rotation = _uarm_l_base_rot + Vector3(lerpf(0.65, -0.35, p_whip) + flinch_arm_l, 0.0, 0.25)
			if forearm_l_node != null:
				forearm_l_node.rotation = _farm_l_base_rot + Vector3(lerpf(0.45, 0.15, p_whip), 0.0, 0.0)
		return

	# --------------------------------------------------------------------------
	# STATE: IDLE / ALERT / CHASE / STRAFE_ORBIT — 8 Biome-Specific Locomotion Gaits
	# --------------------------------------------------------------------------
	var speed_ratio: float = clampf(speed_val / maxf(1.0, move_speed), 0.0, 1.35)
	_update_biomechanical_locomotion(delta, speed_ratio, look_yaw, look_pitch)


func _update_biomechanical_locomotion(
	delta: float,
	speed_ratio: float,
	look_yaw: float,
	look_pitch: float
) -> void:
	var is_floating_wraith: bool = (
		combat_archetype == "RANGED_CASTER"
		or combat_archetype == "BLINK_WRAITH"
	)
	var is_crushing_brute: bool = (
		combat_archetype == "HEAVY_BRUTE"
		or combat_archetype == "SONIC_JUGGERNAUT"
	)

	if speed_ratio > 0.05:
		var freq: float = 3.2 if combat_archetype == "MELEE_RUSHER" else (2.1 if is_crushing_brute else 2.65)
		_walk_cycle_phase += delta * speed_ratio * move_speed * freq
	else:
		_walk_cycle_phase += delta * 1.85

	var w: float = _walk_cycle_phase

	if is_floating_wraith:
		# Biome 3 & 6 (RANGED_CASTER / BLINK_WRAITH): Zero-gravity levitation + phase-lagged trailing legs & orbiting SecondaryProp
		var hover_y: float = sin(w * 1.15) * 0.075 + cos(w * 2.30) * 0.025 + 0.08
		pelvis_node.position = _pelvis_base_pos + Vector3(0.0, hover_y, 0.0)
		pelvis_node.rotation = _pelvis_base_rot + Vector3(-0.10 * speed_ratio, 0.0, sin(w * 0.8) * 0.04)

		var trail_thigh_l: float = -0.22 * speed_ratio + sin(w - 0.6) * 0.12
		var trail_shin_l: float = -0.35 * speed_ratio + sin(w - 1.3) * 0.18 - 0.12
		var trail_thigh_r: float = -0.22 * speed_ratio + cos(w - 0.6) * 0.12
		var trail_shin_r: float = -0.35 * speed_ratio + cos(w - 1.3) * 0.18 - 0.12

		if thigh_l_node != null:
			thigh_l_node.rotation = _thigh_l_base_rot + Vector3(trail_thigh_l, 0.0, 0.0)
		if shin_l_node != null:
			shin_l_node.rotation = _shin_l_base_rot + Vector3(trail_shin_l, 0.0, 0.0)
		if thigh_r_node != null:
			thigh_r_node.rotation = _thigh_r_base_rot + Vector3(trail_thigh_r, 0.0, 0.0)
		if shin_r_node != null:
			shin_r_node.rotation = _shin_r_base_rot + Vector3(trail_shin_r, 0.0, 0.0)

		if torso_node != null:
			torso_node.rotation = _torso_base_rot + Vector3(
				-0.08 * speed_ratio + sin(w) * 0.04,
				look_yaw * 0.25 + cos(w * 0.7) * 0.06,
				sin(w * 0.8) * 0.05
			) + flinch_torso_rot
		if head_node != null:
			head_node.rotation = _head_base_rot + Vector3(look_pitch, look_yaw, 0.0) + flinch_head_rot

		if upper_arm_l_node != null:
			upper_arm_l_node.rotation = _uarm_l_base_rot + Vector3(0.35 + sin(w) * 0.14 + flinch_arm_l, 0.15, 0.22)
		if forearm_l_node != null:
			forearm_l_node.rotation = _farm_l_base_rot + Vector3(0.45 + cos(w) * 0.12, 0.0, 0.0)
		if upper_arm_r_node != null:
			upper_arm_r_node.rotation = _uarm_r_base_rot + Vector3(0.35 - sin(w) * 0.14 + flinch_arm_r, -0.15, -0.22)
		if forearm_r_node != null:
			forearm_r_node.rotation = _farm_r_base_rot + Vector3(0.45 - cos(w) * 0.12, 0.0, 0.0)

		if secondary_prop_node != null:
			secondary_prop_node.rotation.y += delta * 2.4
			secondary_prop_node.position = _sec_prop_base_pos + Vector3(0.0, sin(w * 1.6) * 0.05, 0.0)
		return

	# Grounded Bipeds (Biomes 1, 2, 4, 5, 7, 8): True Knee & Hip Walk Cycle
	var stride_amp: float = 0.62 * speed_ratio
	var knee_bend_amp: float = 0.96 * speed_ratio # Up to ~55 deg (0.96 rad) knee bend during back-swing/lift!

	if is_crushing_brute:
		stride_amp = 0.52 * speed_ratio
		knee_bend_amp = 0.85 * speed_ratio
	elif combat_archetype == "SHIELD_GUARD":
		stride_amp = 0.46 * speed_ratio
		knee_bend_amp = 0.78 * speed_ratio

	var thigh_l_x: float = sin(w) * stride_amp
	var shin_l_x: float = -maxf(0.0, -sin(w + 0.35)) * knee_bend_amp - 0.08
	var thigh_r_x: float = sin(w + PI) * stride_amp
	var shin_r_x: float = -maxf(0.0, -sin(w + PI + 0.35)) * knee_bend_amp - 0.08

	if thigh_l_node != null:
		thigh_l_node.rotation = _thigh_l_base_rot + Vector3(thigh_l_x, 0.0, 0.0)
	if shin_l_node != null:
		shin_l_node.rotation = _shin_l_base_rot + Vector3(shin_l_x, 0.0, 0.0)
	if thigh_r_node != null:
		thigh_r_node.rotation = _thigh_r_base_rot + Vector3(thigh_r_x, 0.0, 0.0)
	if shin_r_node != null:
		shin_r_node.rotation = _shin_r_base_rot + Vector3(shin_r_x, 0.0, 0.0)

	# Double-frequency vertical hip bounce + hip sway
	var hip_bounce: float = -absf(cos(w)) * 0.065 * speed_ratio
	if is_crushing_brute and speed_ratio > 0.05:
		hip_bounce = -pow(absf(sin(w)), 1.6) * 0.085 * speed_ratio
	elif speed_ratio <= 0.05:
		hip_bounce = sin(w) * 0.015

	pelvis_node.position = _pelvis_base_pos + Vector3(0.0, hip_bounce, 0.0)
	pelvis_node.rotation = _pelvis_base_rot + Vector3(0.0, 0.0, cos(w) * 0.06 * speed_ratio)

	# Distinct Biome Upper-Body Postures
	var spine_twist_y: float = -sin(w) * 0.14 * speed_ratio + look_yaw * 0.25
	var torso_lean_x: float = -0.12 * speed_ratio
	var torso_roll_z: float = cos(w) * 0.05 * speed_ratio
	var head_twitch_y: float = 0.0
	var head_twitch_z: float = 0.0

	match combat_archetype:
		"MELEE_RUSHER":
			# Biome 1 (Ossuary Executioner): Forward predatory torso lean (-16 deg = -0.28 rad), elbows bent 50 deg, cross-body cleaver pumping, nervous head micro-twitches
			torso_lean_x = deg_to_rad(-16.0) * maxf(0.4, speed_ratio)
			head_twitch_y = sin(w * 3.7) * 0.06
			head_twitch_z = cos(w * 4.3) * 0.05
			var pump: float = sin(w) * 0.52 * speed_ratio
			if upper_arm_l_node != null:
				upper_arm_l_node.rotation = _uarm_l_base_rot + Vector3(0.25 + pump + flinch_arm_l, 0.22 * cos(w), 0.12)
			if forearm_l_node != null:
				forearm_l_node.rotation = _farm_l_base_rot + Vector3(deg_to_rad(50.0) + absf(pump) * 0.25, 0.18, 0.0)
			if upper_arm_r_node != null:
				upper_arm_r_node.rotation = _uarm_r_base_rot + Vector3(0.25 - pump + flinch_arm_r, -0.22 * cos(w), -0.12)
			if forearm_r_node != null:
				forearm_r_node.rotation = _farm_r_base_rot + Vector3(deg_to_rad(50.0) + absf(pump) * 0.25, -0.18, 0.0)
			if secondary_prop_node != null:
				secondary_prop_node.rotation.x = sin(w * 2.0) * 0.12 * speed_ratio

		"SHIELD_GUARD":
			# Biome 2 (Necropolis Praetorian): Disciplined heavy march; Greatshield locked across chest (ForearmL.rotation.y = 0.65, rotation.x = 0.45), halberd couched
			torso_lean_x = -0.08 * speed_ratio
			var breath_sway: float = sin(w * 0.5) * 0.03
			if upper_arm_l_node != null:
				upper_arm_l_node.rotation = _uarm_l_base_rot + Vector3(0.38 + breath_sway + flinch_arm_l, 0.28, 0.0)
			if forearm_l_node != null:
				forearm_l_node.rotation = _farm_l_base_rot + Vector3(0.45 + breath_sway, 0.65, 0.0)
			if upper_arm_r_node != null:
				upper_arm_r_node.rotation = _uarm_r_base_rot + Vector3(-0.22 - sin(w) * 0.18 * speed_ratio + flinch_arm_r, 0.0, -0.10)
			if forearm_r_node != null:
				forearm_r_node.rotation = _farm_r_base_rot + Vector3(0.36, 0.0, 0.0)

		"HEAVY_BRUTE", "SONIC_JUGGERNAUT":
			# Biome 4 & 7 (Rack-Master & Bell Juggernaut): Wide lateral torso roll (±0.11 rad) + secondary pendulum swing
			torso_lean_x = -0.14 * speed_ratio
			torso_roll_z = cos(w) * 0.11 * maxf(0.35, speed_ratio)
			var swing_arm: float = sin(w) * 0.34 * speed_ratio
			if upper_arm_l_node != null:
				upper_arm_l_node.rotation = _uarm_l_base_rot + Vector3(swing_arm + flinch_arm_l, 0.0, 0.16)
			if forearm_l_node != null:
				forearm_l_node.rotation = _farm_l_base_rot + Vector3(0.42, 0.0, 0.0)
			if upper_arm_r_node != null:
				upper_arm_r_node.rotation = _uarm_r_base_rot + Vector3(-swing_arm + flinch_arm_r, 0.0, -0.16)
			if forearm_r_node != null:
				forearm_r_node.rotation = _farm_r_base_rot + Vector3(0.48 + sin(w - 0.7) * 0.22, 0.0, 0.0)
			if secondary_prop_node != null:
				secondary_prop_node.rotation = _sec_prop_base_rot + Vector3(sin(w * 2.0) * 0.18, 0.0, -cos(w) * 0.22)

		"ELITE_HYBRID_LORD":
			# Biome 8 (Abyssal Archon): Regal wide-stance glide-stride with floating obelisk shards bobbing out of phase
			torso_lean_x = -0.09 * speed_ratio
			var regal_swing: float = sin(w) * 0.28 * speed_ratio
			if upper_arm_l_node != null:
				upper_arm_l_node.rotation = _uarm_l_base_rot + Vector3(0.25 + regal_swing + flinch_arm_l, 0.18, 0.15)
			if forearm_l_node != null:
				forearm_l_node.rotation = _farm_l_base_rot + Vector3(0.38, 0.0, 0.0)
			if upper_arm_r_node != null:
				upper_arm_r_node.rotation = _uarm_r_base_rot + Vector3(0.15 - regal_swing + flinch_arm_r, -0.12, -0.18)
			if forearm_r_node != null:
				forearm_r_node.rotation = _farm_r_base_rot + Vector3(0.35, 0.0, 0.0)
			if secondary_prop_node != null:
				secondary_prop_node.position = _sec_prop_base_pos + Vector3(0.0, sin(w * 1.5 + 0.8) * 0.08, 0.0)
				secondary_prop_node.rotation = _sec_prop_base_rot + Vector3(0.0, sin(w * 0.9) * 0.22, cos(w * 1.2) * 0.08)

		_:
			# Biome 5 (RANGED_LOBBER_EXPLODER — Plague Bloater): Sloshing dorsal tank & swinging censer
			torso_lean_x = -0.15 * speed_ratio
			var lob_swing: float = sin(w) * 0.36 * speed_ratio
			if upper_arm_l_node != null:
				upper_arm_l_node.rotation = _uarm_l_base_rot + Vector3(lob_swing + flinch_arm_l, 0.0, 0.12)
			if forearm_l_node != null:
				forearm_l_node.rotation = _farm_l_base_rot + Vector3(0.45, 0.0, 0.0)
			if upper_arm_r_node != null:
				upper_arm_r_node.rotation = _uarm_r_base_rot + Vector3(-lob_swing + flinch_arm_r, 0.0, -0.12)
			if forearm_r_node != null:
				forearm_r_node.rotation = _farm_r_base_rot + Vector3(0.45 + cos(w) * 0.22, 0.0, 0.0)
			if secondary_prop_node != null:
				secondary_prop_node.rotation = _sec_prop_base_rot + Vector3(sin(w * 2.0) * 0.10, 0.0, cos(w) * 0.14)

	if torso_node != null:
		torso_node.rotation = _torso_base_rot + Vector3(torso_lean_x, spine_twist_y, torso_roll_z) + flinch_torso_rot
	if head_node != null:
		head_node.rotation = _head_base_rot + Vector3(look_pitch, look_yaw + head_twitch_y, head_twitch_z) + flinch_head_rot


# ==============================================================================
# 4. LOCATIONAL BULLET HIT-FLINCH SPRINGS & 5. PROCEDURAL DEATH COLLAPSE
# ==============================================================================

func _apply_locational_hit_flinch(hit_pos: Vector3) -> void:
	if hit_pos == Vector3.ZERO:
		flinch_torso_rot += Vector3(0.22, 0.0, 0.0)
		flinch_head_rot += Vector3(0.28, 0.0, 0.0)
		return

	var local_y: float = hit_pos.y - global_position.y
	var rel_vec: Vector3 = hit_pos - global_position
	var right_dot: float = global_transform.basis.x.dot(rel_vec)

	if local_y > 1.45:
		# Headshot: Snaps Head backward (+0.65) and Torso back (+0.28)
		flinch_head_rot.x = clampf(flinch_head_rot.x + 0.65, -1.2, 1.2)
		flinch_torso_rot.x = clampf(flinch_torso_rot.x + 0.28, -0.9, 0.9)
	elif right_dot < -0.08:
		# Left Shoulder / Left Side Hit: Twists Torso away (+0.42 rad) and jerks UpperArmL backward (+0.75 rad)
		flinch_torso_rot.y = clampf(flinch_torso_rot.y + 0.42, -1.0, 1.0)
		flinch_torso_rot.x = clampf(flinch_torso_rot.x + 0.18, -0.9, 0.9)
		flinch_arm_l = clampf(flinch_arm_l + 0.75, -1.4, 1.4)
	elif right_dot > 0.08:
		# Right Shoulder / Right Side Hit: Twists Torso away (-0.42 rad) and jerks UpperArmR backward (+0.75 rad)
		flinch_torso_rot.y = clampf(flinch_torso_rot.y - 0.42, -1.0, 1.0)
		flinch_torso_rot.x = clampf(flinch_torso_rot.x + 0.18, -0.9, 0.9)
		flinch_arm_r = clampf(flinch_arm_r + 0.75, -1.4, 1.4)
	else:
		# Center-mass torso hit
		flinch_torso_rot.x = clampf(flinch_torso_rot.x + 0.32, -0.9, 0.9)
		flinch_head_rot.x = clampf(flinch_head_rot.x + 0.25, -1.2, 1.2)


func _update_death_collapse(delta: float) -> void:
	_death_collapse_timer += delta
	var t: float = clampf(_death_collapse_timer / DEATH_COLLAPSE_DURATION, 0.0, 1.0)
	var p: float = ease(t, 2.2)

	if pelvis_node != null:
		pelvis_node.position = _pelvis_base_pos.lerp(Vector3(_pelvis_base_pos.x, 0.22, _pelvis_base_pos.z), p)
	if thigh_l_node != null:
		thigh_l_node.rotation = _thigh_l_base_rot.lerp(Vector3(0.85, 0.0, 0.15), p)
	if shin_l_node != null:
		shin_l_node.rotation = _shin_l_base_rot.lerp(Vector3(-1.65, 0.0, 0.0), p)
	if thigh_r_node != null:
		thigh_r_node.rotation = _thigh_r_base_rot.lerp(Vector3(0.85, 0.0, -0.15), p)
	if shin_r_node != null:
		shin_r_node.rotation = _shin_r_base_rot.lerp(Vector3(-1.65, 0.0, 0.0), p)
	if torso_node != null:
		torso_node.rotation = _torso_base_rot.lerp(Vector3(-1.35, 0.12, 0.08), p)
	if head_node != null:
		head_node.rotation = _head_base_rot.lerp(Vector3(0.45, 0.25, 0.0), p)
	if upper_arm_l_node != null:
		upper_arm_l_node.rotation = _uarm_l_base_rot.lerp(Vector3(0.45, 0.0, 1.15), p)
	if forearm_l_node != null:
		forearm_l_node.rotation = _farm_l_base_rot.lerp(Vector3(0.20, 0.0, 0.0), p)
	if upper_arm_r_node != null:
		upper_arm_r_node.rotation = _uarm_r_base_rot.lerp(Vector3(0.45, 0.0, -1.15), p)
	if forearm_r_node != null:
		forearm_r_node.rotation = _farm_r_base_rot.lerp(Vector3(0.20, 0.0, 0.0), p)

	# Restore original non-glowing surface materials during death collapse
	if _death_collapse_timer <= delta * 1.5:
		_set_telegraph_glow(false)

	if _death_collapse_timer >= DEATH_COLLAPSE_DURATION:
		queue_free()


func take_damage(
	amount: float,
	armor_piercing: bool = false,
	hit_pos: Vector3 = Vector3.ZERO,
	_hit_normal: Vector3 = Vector3.UP,
	_weapon_mod: String = ""
) -> float:
	return apply_damage_directional(amount, armor_piercing, hit_pos)


func apply_damage(amount: float, armor_piercing: bool = false) -> float:
	return apply_damage_directional(amount, armor_piercing, Vector3.ZERO)


func apply_damage_directional(
	amount: float,
	armor_piercing: bool = false,
	hit_pos: Vector3 = Vector3.ZERO
) -> float:
	if _is_dead or amount <= 0.0:
		return 0.0

	if not is_passive_dummy and not has_aggroed:
		has_aggroed = true
		if current_state == AIState.IDLE:
			current_state = AIState.CHASE

	# Apply locational bullet hit-flinch spring impulse immediately
	_apply_locational_hit_flinch(hit_pos)

	var final_amt: float = amount

	# SHIELD_GUARD reduces frontal non-piercing gunshot damage by 60% while advancing;
	# attacks from behind (front_dot <= 0.0) bypass the tower shield completely.
	if (
		not is_passive_dummy
		and combat_archetype == "SHIELD_GUARD"
		and not armor_piercing
		and (
			current_state == AIState.CHASE
			or current_state == AIState.IDLE
			or current_state == AIState.ALERT
			or current_state == AIState.STRAFE_ORBIT
		)
		and is_attack_from_front(hit_pos)
	):
		final_amt *= 0.40

	var dealt: float = super.apply_damage(final_amt, armor_piercing)
	_has_taken_damage = true
	_update_status_label_text()
	if _status_label != null and not _is_dead:
		_status_label.visible = true

	# BLINK_WRAITH (Biome 6) sidestep-teleports 3.0m laterally after taking a hit
	if not _is_dead and not is_passive_dummy and combat_archetype == "BLINK_WRAITH" and _blink_cooldown_timer <= 0.0:
		_blink_cooldown_timer = 2.4
		_spawn_ground_shockwave_ring(Color(0.28, 0.78, 1.0, 1.0), 1.8)
		var right_vec: Vector3 = global_transform.basis.x.normalized() * strafe_sign
		strafe_sign = -strafe_sign
		var blink_dir: Vector3 = _compute_whisker_steered_direction(right_vec)
		global_position += Vector3(blink_dir.x, 0.0, blink_dir.z) * 3.0
		_spawn_origin = position

	return dealt


func apply_knockback_stagger(push_vec: Vector3, stagger_sec: float = 0.35) -> void:
	if _is_dead:
		return
	var horiz: Vector3 = Vector3(push_vec.x, 0.0, push_vec.z)
	_spawn_origin += horiz
	position += horiz

	# HEAVY_BRUTE & SONIC_JUGGERNAUT are immune to light flinch during WINDUP
	if (combat_archetype == "HEAVY_BRUTE" or combat_archetype == "SONIC_JUGGERNAUT") and current_state == AIState.WINDUP and stagger_sec < 1.0:
		return

	_shackle_timer = maxf(_shackle_timer, stagger_sec)
	current_state = AIState.STAGGER
	state_timer = stagger_sec
	_set_telegraph_glow(false)


func apply_dot(dps: float = 12.0, duration: float = 4.0) -> void:
	apply_bile_dot(dps, duration)


func apply_stun(duration: float = 4.0) -> void:
	apply_shackle_debuff(duration)
	current_state = AIState.STAGGER
	state_timer = duration
	_set_telegraph_glow(false)


func _die_and_spawn_loot() -> void:
	if _is_dead:
		return
	_is_dead = true
	current_state = AIState.DEAD
	_death_collapse_timer = 0.0
	velocity = Vector3.ZERO
	_disable_all_colliders_on_death()
	if _status_label != null:
		_status_label.visible = false

	# RANGED_LOBBER_EXPLODER (Biome 5 Plague Bloater) detonates a toxic AoE cloud on death
	if not is_passive_dummy and combat_archetype == "RANGED_LOBBER_EXPLODER" and is_inside_tree():
		_spawn_ground_shockwave_ring(Color(0.42, 0.96, 0.28, 1.0), 3.8)
		var player: Node3D = _find_player_node()
		if player != null and global_position.distance_to(player.global_position) <= 3.8:
			_deal_direct_damage_to_player(player, 18.0)

	var drop_parent: Node = get_parent() if get_parent() != null else self
	var drop_origin: Vector3 = global_position if is_inside_tree() else position

	var lm: PlayerLoadoutManager = null
	if is_inside_tree() and get_tree() != null and get_tree().root != null:
		lm = get_tree().root.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	if lm == null:
		var curr_n: Node = get_parent()
		while curr_n != null:
			lm = curr_n.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
			if lm != null:
				break
			curr_n = curr_n.get_parent()

	var is_elite_or_champ: bool = is_champion or combat_archetype == "ELITE_HYBRID_LORD" or guaranteed_relic_drop
	var hp_ratio: float = 1.0
	if lm != null and lm.max_health > 0:
		hp_ratio = clampf(float(lm.current_health) / float(lm.max_health), 0.0, 1.0)

	# Award XP directly to PlayerLoadoutManager on every kill (after sampling hp_ratio so level-up heals don't mask low-HP pity)
	if lm != null:
		lm.add_xp(xp_reward)
		lm.on_enemy_killed()

	if is_elite_or_champ:
		# Anointed Champion / Elite Lord: 100% drop rate (2 to 3 LootDropPickup orbs)
		var main_res: String = "silver"
		if biome_tier >= 4 and randf() < 0.55:
			main_res = "soul_cores"
		elif biome_tier >= 3:
			main_res = "cursed_iron"
		elif biome_tier >= 2 and randf() < 0.65:
			main_res = "cursed_iron"
		else:
			main_res = "bone_ash"

		LootDropPickup.spawn_loot_drop(
			drop_parent,
			drop_origin + Vector3(-0.22, 0.0, 0.0),
			main_res,
			0,
			depth_scale,
			biome_tier
		)
		var second_cat: String = "health" if hp_ratio < 0.50 else "silver"
		LootDropPickup.spawn_loot_drop(
			drop_parent,
			drop_origin + Vector3(0.22, 0.0, 0.18),
			second_cat,
			0,
			depth_scale,
			biome_tier
		)
		if guaranteed_relic_drop or randf() < 0.25:
			LootDropPickup.spawn_loot_drop(
				drop_parent,
				drop_origin + Vector3(0.0, 0.0, -0.24),
				"relic",
				biome_relic_id,
				depth_scale,
				biome_tier
			)
	else:
		# Standard Enemy Scarcity Table (32% base drop chance; 58% Blood-Desperation Pity below 35% HP)
		var drop_chance: float = 0.58 if hp_ratio < 0.35 else 0.32
		if randf() < drop_chance:
			var roll: float = randf()
			var chosen_cat: String = "silver"
			if hp_ratio < 0.35:
				# Blood-Desperation Pity: 55% Health, 25% Ammo, 20% Crafting Resource
				if roll < 0.55:
					chosen_cat = "health"
				elif roll < 0.80:
					chosen_cat = "ammo"
				else:
					chosen_cat = _roll_crafting_resource_category()
			elif hp_ratio >= 0.70:
				# High HP: 70% Crafting Resources, 15% Health/Armor, 15% Ammo
				if roll < 0.70:
					chosen_cat = _roll_crafting_resource_category()
				elif roll < 0.85:
					chosen_cat = "elixir"
				else:
					chosen_cat = "ammo"
			else:
				# Mid HP: 30% Health/Armor, 25% Ammo, 45% Crafting Resources
				if roll < 0.30:
					chosen_cat = "health"
				elif roll < 0.55:
					chosen_cat = "ammo"
				else:
					chosen_cat = _roll_crafting_resource_category()

			LootDropPickup.spawn_loot_drop(
				drop_parent,
				drop_origin,
				chosen_cat,
				biome_relic_id,
				depth_scale,
				biome_tier
			)

	enemy_died.emit(self)
	if not is_inside_tree():
		queue_free()


func _roll_crafting_resource_category() -> String:
	var r: float = randf()
	if biome_tier >= 4 and r < 0.14:
		return "soul_cores"
	if biome_tier >= 2 and r < 0.36:
		return "cursed_iron"
	if r < 0.68:
		return "bone_ash"
	return "silver"
