class_name TestDummyEnemy
extends CharacterBody3D

signal enemy_died(enemy: TestDummyEnemy)

@export var enemy_title: String = "Ossuary Skeleton"
@export var max_health: float = 90.0
@export var current_health: float = 90.0
@export var essence_reward: int = 25
@export var patrol_radius: float = 1.6
@export var depth_scale: float = 1.0
@export var guaranteed_relic_drop: bool = false
@export var biome_relic_id: int = 0
@export var flat_armor: float = 0.0

var _spawn_origin: Vector3 = Vector3.ZERO
var _time_acc: float = 0.0
var _phase_offset: float = 0.0
var _is_dead: bool = false

var _bile_dot_timer: float = 0.0
var _bile_dot_dps: float = 12.0
var _burn_dot_timer: float = 0.0
var _burn_dot_dps: float = 15.0
var _shackle_timer: float = 0.0
var _bile_particles: GPUParticles3D = null

static var _shared_bile_proc_mat: ParticleProcessMaterial = null
static var _shared_bile_quad: QuadMesh = null


func _ready() -> void:
	add_to_group("enemies")
	_spawn_origin = position
	_phase_offset = float(get_instance_id() % 1000) * 0.017
	if flat_armor <= 0.0 and enemy_title.to_lower().contains("penitent"):
		flat_armor = 15.0
	current_health = max_health


func apply_depth_scaling(tier: int, b_id: int = 0) -> void:
	depth_scale = 1.0 + float(maxi(1, tier) - 1) * 0.30
	max_health = roundf(max_health * depth_scale)
	current_health = max_health
	if b_id >= 1 and b_id <= 8:
		biome_relic_id = b_id


func is_alive() -> bool:
	return not _is_dead and current_health > 0.0


func is_shackled() -> bool:
	return _shackle_timer > 0.0


func is_corroded() -> bool:
	return _bile_dot_timer > 0.0


func apply_bile_dot(dps: float = 12.0, duration: float = 4.0) -> void:
	if _is_dead:
		return
	_bile_dot_dps = dps
	_bile_dot_timer = maxf(_bile_dot_timer, duration)
	_ensure_bile_particles()


func apply_burn_dot(dps: float = 15.0, duration: float = 4.0) -> void:
	if _is_dead:
		return
	_burn_dot_dps = dps
	_burn_dot_timer = maxf(_burn_dot_timer, duration)


func apply_shackle_debuff(duration: float = 4.0) -> void:
	if _is_dead:
		return
	_shackle_timer = maxf(_shackle_timer, duration)


func apply_knockback_stagger(push_vec: Vector3, stagger_sec: float = 0.35) -> void:
	if _is_dead:
		return
	var horiz: Vector3 = Vector3(push_vec.x, 0.0, push_vec.z)
	_spawn_origin += horiz
	position += horiz
	_shackle_timer = maxf(_shackle_timer, stagger_sec)


func _ensure_bile_particles() -> void:
	if _bile_particles != null:
		_bile_particles.emitting = true
		return
	if _shared_bile_proc_mat == null:
		_shared_bile_proc_mat = ParticleProcessMaterial.new()
		_shared_bile_proc_mat.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
		_shared_bile_proc_mat.emission_sphere_radius = 0.45
		_shared_bile_proc_mat.gravity = Vector3(0.0, 0.8, 0.0)
		_shared_bile_proc_mat.initial_velocity_min = 0.2
		_shared_bile_proc_mat.initial_velocity_max = 0.6
		_shared_bile_proc_mat.color = Color(0.42, 0.96, 0.30, 0.85)
	if _shared_bile_quad == null:
		_shared_bile_quad = QuadMesh.new()
		_shared_bile_quad.size = Vector2(0.05, 0.05)
		var s_mat: StandardMaterial3D = StandardMaterial3D.new()
		s_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		s_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		s_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
		s_mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
		s_mat.albedo_color = Color(0.42, 0.96, 0.30, 0.85)
		_shared_bile_quad.material = s_mat

	_bile_particles = GPUParticles3D.new()
	_bile_particles.name = "CorrosiveBileParticles"
	_bile_particles.position = Vector3(0.0, 1.0, 0.0)
	_bile_particles.amount = 10
	_bile_particles.lifetime = 0.7
	_bile_particles.process_material = _shared_bile_proc_mat
	_bile_particles.draw_pass_1 = _shared_bile_quad
	add_child(_bile_particles)


func _physics_process(delta: float) -> void:
	if _is_dead:
		return

	if _shackle_timer > 0.0:
		_shackle_timer = maxf(0.0, _shackle_timer - delta)
	else:
		_time_acc += delta
		var sway_x: float = sin(_time_acc * 0.85 + _phase_offset) * (patrol_radius * 0.25)
		var sway_z: float = cos(_time_acc * 0.65 + _phase_offset) * (patrol_radius * 0.25)
		position = Vector3(_spawn_origin.x + sway_x, _spawn_origin.y, _spawn_origin.z + sway_z)
		rotation.y += sin(_time_acc * 0.55 + _phase_offset) * 0.25 * delta

	if _bile_dot_timer > 0.0:
		_bile_dot_timer = maxf(0.0, _bile_dot_timer - delta)
		apply_damage(_bile_dot_dps * delta)
		if _bile_dot_timer <= 0.0 and _bile_particles != null:
			_bile_particles.emitting = false

	if _burn_dot_timer > 0.0 and not _is_dead:
		_burn_dot_timer = maxf(0.0, _burn_dot_timer - delta)
		apply_damage(_burn_dot_dps * delta)


func take_damage(
	amount: float,
	armor_piercing: bool = false,
	_hit_pos: Vector3 = Vector3.ZERO,
	_hit_normal: Vector3 = Vector3.UP,
	_weapon_mod: String = ""
) -> float:
	return apply_damage(amount, armor_piercing)


func apply_damage(amount: float, armor_piercing: bool = false) -> float:
	if _is_dead or amount <= 0.0:
		return 0.0
	var effective: float = amount
	if not armor_piercing and flat_armor > 0.0 and amount >= 2.0:
		effective = maxf(1.0, amount - flat_armor)
	current_health = maxf(0.0, current_health - effective)
	if current_health <= 0.0:
		_die_and_spawn_loot()
	return effective


func _die_and_spawn_loot() -> void:
	if _is_dead:
		return
	_is_dead = true

	var drop_parent: Node = get_parent() if get_parent() != null else self
	var drop_origin: Vector3 = global_position if is_inside_tree() else position

	# 1-2 physical XP/Essence Blood Echo clusters
	var xp_count: int = randi_range(1, 2)
	for i: int in range(xp_count):
		LootDropPickup.spawn_loot_drop(
			drop_parent,
			drop_origin + Vector3(float(i) * 0.25 - 0.12, 0.0, 0.0),
			"xp_essence",
			0,
			depth_scale
		)

	# 40% chance for an Alchemical Elixir vial
	if randf() < 0.40 or guaranteed_relic_drop:
		LootDropPickup.spawn_loot_drop(
			drop_parent,
			drop_origin + Vector3(0.25, 0.0, 0.22),
			"elixir",
			0,
			depth_scale
		)

	# 35% chance (or 100% if guaranteed_relic_drop) to pop an Occult Relic Talisman
	if guaranteed_relic_drop or randf() < 0.35:
		LootDropPickup.spawn_loot_drop(
			drop_parent,
			drop_origin + Vector3(-0.25, 0.0, 0.25),
			"relic",
			biome_relic_id,
			depth_scale
		)

	# Notify PlayerLoadoutManager for Abyssal Blood Chalice (Relic 8) on-kill effect
	if is_inside_tree() and get_tree().root != null:
		var lm: PlayerLoadoutManager = get_tree().root.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
		if lm != null:
			lm.on_enemy_killed()

	enemy_died.emit(self)
	queue_free()
