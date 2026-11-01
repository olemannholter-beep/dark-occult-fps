class_name EnemyProjectile
extends Area3D

var velocity: Vector3 = Vector3.ZERO
var damage: float = 18.0
var lifetime: float = 4.2
var arc_gravity: float = 0.0
var homing_strength: float = 0.0
var target_player: Node3D = null
var shooter: Node3D = null
var orb_color: Color = Color(0.76, 0.24, 1.0, 1.0)

var _core_mesh: MeshInstance3D = null
var _ring_mesh_a: MeshInstance3D = null
var _ring_mesh_b: MeshInstance3D = null
var _has_detonated: bool = false

static var _shared_col_shape: SphereShape3D = null
static var _shared_core_sphere: SphereMesh = null
static var _shared_ring_box_a: BoxMesh = null
static var _shared_ring_box_b: BoxMesh = null
static var _shared_burst_sphere: SphereMesh = null
static var _shared_core_mats: Dictionary[String, StandardMaterial3D] = {}
static var _shared_ring_mats: Dictionary[String, StandardMaterial3D] = {}


static func _ensure_shared_resources() -> void:
	if _shared_col_shape == null:
		_shared_col_shape = SphereShape3D.new()
		_shared_col_shape.radius = 0.24
	if _shared_core_sphere == null:
		_shared_core_sphere = SphereMesh.new()
		_shared_core_sphere.radius = 0.16
		_shared_core_sphere.height = 0.32
		_shared_core_sphere.radial_segments = 10
		_shared_core_sphere.rings = 5
	if _shared_ring_box_a == null:
		_shared_ring_box_a = BoxMesh.new()
		_shared_ring_box_a.size = Vector3(0.42, 0.04, 0.42)
	if _shared_ring_box_b == null:
		_shared_ring_box_b = BoxMesh.new()
		_shared_ring_box_b.size = Vector3(0.36, 0.36, 0.04)
	if _shared_burst_sphere == null:
		_shared_burst_sphere = SphereMesh.new()
		_shared_burst_sphere.radius = 0.28
		_shared_burst_sphere.height = 0.56
		_shared_burst_sphere.radial_segments = 8
		_shared_burst_sphere.rings = 4


static func _get_shared_core_material(col: Color) -> StandardMaterial3D:
	var key: String = "%.2f_%.2f_%.2f" % [col.r, col.g, col.b]
	if _shared_core_mats.has(key):
		return _shared_core_mats[key]
	var mat: StandardMaterial3D = StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = Color(
		clampf(col.r * 1.25, 0.0, 1.0),
		clampf(col.g * 1.25, 0.0, 1.0),
		clampf(col.b * 1.25, 0.0, 1.0),
		1.0
	)
	_shared_core_mats[key] = mat
	return mat


static func _get_shared_ring_material(col: Color) -> StandardMaterial3D:
	var key: String = "%.2f_%.2f_%.2f" % [col.r, col.g, col.b]
	if _shared_ring_mats.has(key):
		return _shared_ring_mats[key]
	var mat: StandardMaterial3D = StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.albedo_color = Color(col.r, col.g, col.b, 0.82)
	_shared_ring_mats[key] = mat
	return mat


func _ready() -> void:
	collision_layer = 0
	collision_mask = 1 | 2
	monitoring = true
	monitorable = false
	_build_visual_and_collider()
	body_entered.connect(_on_body_entered)


static func spawn_projectile(
	parent: Node,
	origin: Vector3,
	dir: Vector3,
	dmg: float,
	col: Color,
	speed: float = 13.5,
	gravity_arc: float = 0.0,
	homing: float = 0.0,
	from_enemy: Node3D = null,
	player_ref: Node3D = null
) -> EnemyProjectile:
	var proj: EnemyProjectile = EnemyProjectile.new()
	proj.name = "EnemySpellProjectile"
	proj.damage = dmg
	proj.orb_color = col
	proj.arc_gravity = gravity_arc
	proj.homing_strength = homing
	proj.shooter = from_enemy
	proj.target_player = player_ref
	proj.velocity = dir.normalized() * speed
	parent.add_child(proj)
	proj.global_position = origin
	return proj


func _build_visual_and_collider() -> void:
	_ensure_shared_resources()

	var col_shape: CollisionShape3D = CollisionShape3D.new()
	col_shape.name = "CollisionShape3D"
	col_shape.shape = _shared_col_shape
	add_child(col_shape)

	var core_mat: StandardMaterial3D = _get_shared_core_material(orb_color)
	var ring_mat: StandardMaterial3D = _get_shared_ring_material(orb_color)

	_core_mesh = MeshInstance3D.new()
	_core_mesh.name = "OrbCore"
	_core_mesh.mesh = _shared_core_sphere
	_core_mesh.material_override = core_mat
	_core_mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_core_mesh)

	_ring_mesh_a = MeshInstance3D.new()
	_ring_mesh_a.name = "RuneRingA"
	_ring_mesh_a.mesh = _shared_ring_box_a
	_ring_mesh_a.material_override = ring_mat
	_ring_mesh_a.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_ring_mesh_a)

	_ring_mesh_b = MeshInstance3D.new()
	_ring_mesh_b.name = "RuneRingB"
	_ring_mesh_b.mesh = _shared_ring_box_b
	_ring_mesh_b.material_override = ring_mat
	_ring_mesh_b.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_ring_mesh_b)


func _physics_process(delta: float) -> void:
	if _has_detonated:
		return

	lifetime -= delta
	if lifetime <= 0.0:
		_detonate(false)
		return

	if arc_gravity != 0.0:
		velocity.y -= arc_gravity * delta

	if homing_strength > 0.0 and target_player != null and is_instance_valid(target_player):
		var to_target: Vector3 = (target_player.global_position + Vector3(0.0, 1.0, 0.0)) - global_position
		if to_target.length_squared() > 0.04:
			var cur_speed: float = velocity.length()
			var desired_dir: Vector3 = to_target.normalized()
			var new_dir: Vector3 = velocity.normalized().lerp(desired_dir, clampf(homing_strength * delta, 0.0, 1.0)).normalized()
			velocity = new_dir * cur_speed

	var next_pos: Vector3 = global_position + velocity * delta

	if is_inside_tree() and get_world_3d() != null:
		var space_state: PhysicsDirectSpaceState3D = get_world_3d().direct_space_state
		if space_state != null:
			var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(global_position, next_pos, 1 | 2)
			if shooter != null and is_instance_valid(shooter) and shooter is CollisionObject3D:
				query.exclude = [(shooter as CollisionObject3D).get_rid()]
			var hit: Dictionary = space_state.intersect_ray(query)
			if not hit.is_empty():
				var collider: Object = hit.get("collider", null)
				if collider is Node:
					_handle_hit_node(collider as Node)
					return

	global_position = next_pos

	if _ring_mesh_a != null:
		_ring_mesh_a.rotate_y(delta * 7.5)
		_ring_mesh_a.rotate_x(delta * 4.2)
	if _ring_mesh_b != null:
		_ring_mesh_b.rotate_z(delta * 8.0)
		_ring_mesh_b.rotate_y(delta * 5.0)

	if target_player != null and is_instance_valid(target_player):
		var d_sq: float = global_position.distance_squared_to(target_player.global_position + Vector3(0.0, 0.95, 0.0))
		if d_sq <= 0.72:
			_handle_hit_node(target_player)


func _on_body_entered(body: Node3D) -> void:
	if _has_detonated or body == null or body == shooter:
		return
	if body is TestDummyEnemy:
		return
	_handle_hit_node(body)


func _handle_hit_node(node: Node) -> void:
	if _has_detonated or node == shooter or node is TestDummyEnemy:
		return
	var is_player: bool = (
		node.name == "Player"
		or node.name == "FPSPlayer"
		or node.is_in_group("player")
		or node.find_child("PlayerLoadoutManager", true, false) != null
	)
	if is_player:
		var lm: PlayerLoadoutManager = node.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
		if lm == null and get_tree() != null and get_tree().root != null:
			lm = get_tree().root.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
		if lm != null:
			lm.apply_player_damage(damage)
		_detonate(true)
	else:
		_detonate(false)


func _detonate(_hit_player: bool) -> void:
	if _has_detonated:
		return
	_has_detonated = true
	if is_inside_tree() and get_parent() != null:
		_spawn_impact_burst()
	queue_free()


func _spawn_impact_burst() -> void:
	_ensure_shared_resources()
	var burst: MeshInstance3D = MeshInstance3D.new()
	burst.name = "ProjectileImpactBurst"
	burst.mesh = _shared_burst_sphere
	burst.material_override = _get_shared_ring_material(orb_color)
	burst.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	get_parent().add_child(burst)
	burst.global_position = global_position

	var tw: Tween = burst.create_tween()
	tw.tween_property(burst, "scale", Vector3(2.2, 2.2, 2.2), 0.16)
	tw.tween_callback(burst.queue_free)
