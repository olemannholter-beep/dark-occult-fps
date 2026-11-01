class_name LootDropPickup
extends Area3D

@export var drop_category: String = "xp_essence"
@export var xp_amount: int = 35
@export var essence_amount: int = 25
@export var heal_amount: int = 35
@export var armor_amount: int = 25
@export var relic_id: int = 1
@export var resource_key: String = ""
@export var resource_amount: int = 0
@export var biome_tier: int = 1

var _bob_time: float = 0.0
var _pop_timer: float = 0.0
var _pop_start: Vector3 = Vector3.ZERO
var _pop_target: Vector3 = Vector3.ZERO
var _is_popping: bool = false
var _collected: bool = false

var _visual_root: Node3D = null
var _core_mesh: MeshInstance3D = null
var _ring_mesh: MeshInstance3D = null
var _wisp_mesh: MeshInstance3D = null

static var _shared_col_shape: SphereShape3D = null
static var _shared_crystal_mesh: Mesh = null
static var _shared_ring_torus: TorusMesh = null
static var _shared_wisp_prism: PrismMesh = null
static var _shared_core_mats: Dictionary[String, StandardMaterial3D] = {}
static var _shared_ring_mats: Dictionary[String, StandardMaterial3D] = {}
static var _shared_wisp_mats: Dictionary[String, StandardMaterial3D] = {}


static func _ensure_shared_loot_resources() -> void:
	if _shared_col_shape == null:
		_shared_col_shape = SphereShape3D.new()
		_shared_col_shape.radius = 0.95
	if _shared_crystal_mesh == null:
		# Crisp stepped micro-voxel crystal/flask cluster (replaces legacy SphereMesh)
		var st: SurfaceTool = SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		_add_micro_voxel_box(st, Vector3(0.0, 0.0, 0.0), Vector3(0.16, 0.16, 0.16))
		_add_micro_voxel_box(st, Vector3(0.0, -0.07, 0.0), Vector3(0.11, 0.06, 0.11))
		_add_micro_voxel_box(st, Vector3(0.0, 0.07, 0.0), Vector3(0.11, 0.06, 0.11))
		_add_micro_voxel_box(st, Vector3(0.0, 0.12, 0.0), Vector3(0.06, 0.05, 0.06))
		_shared_crystal_mesh = st.commit()
	if _shared_ring_torus == null:
		_shared_ring_torus = TorusMesh.new()
		_shared_ring_torus.inner_radius = 0.14
		_shared_ring_torus.outer_radius = 0.18
		_shared_ring_torus.rings = 12
		_shared_ring_torus.ring_segments = 6
	if _shared_wisp_prism == null:
		# Tiny 0.42m translucent diamond wisp (total visual AABB height <= 0.65m, zero giant white cones!)
		_shared_wisp_prism = PrismMesh.new()
		_shared_wisp_prism.size = Vector3(0.08, 0.42, 0.08)


static func _add_micro_voxel_box(st: SurfaceTool, center: Vector3, size: Vector3) -> void:
	var h: Vector3 = size * 0.5
	var min_p: Vector3 = center - h
	var max_p: Vector3 = center + h
	var faces: Array[PackedVector3Array] = [
		PackedVector3Array([Vector3(0, 0, 1), Vector3(min_p.x, min_p.y, max_p.z), Vector3(max_p.x, min_p.y, max_p.z), Vector3(max_p.x, max_p.y, max_p.z), Vector3(min_p.x, max_p.y, max_p.z)]),
		PackedVector3Array([Vector3(0, 0, -1), Vector3(max_p.x, min_p.y, min_p.z), Vector3(min_p.x, min_p.y, min_p.z), Vector3(min_p.x, max_p.y, min_p.z), Vector3(max_p.x, max_p.y, min_p.z)]),
		PackedVector3Array([Vector3(1, 0, 0), Vector3(max_p.x, min_p.y, max_p.z), Vector3(max_p.x, min_p.y, min_p.z), Vector3(max_p.x, max_p.y, min_p.z), Vector3(max_p.x, max_p.y, max_p.z)]),
		PackedVector3Array([Vector3(-1, 0, 0), Vector3(min_p.x, min_p.y, min_p.z), Vector3(min_p.x, min_p.y, max_p.z), Vector3(min_p.x, max_p.y, max_p.z), Vector3(min_p.x, max_p.y, min_p.z)]),
		PackedVector3Array([Vector3(0, 1, 0), Vector3(min_p.x, max_p.y, max_p.z), Vector3(max_p.x, max_p.y, max_p.z), Vector3(max_p.x, max_p.y, min_p.z), Vector3(min_p.x, max_p.y, min_p.z)]),
		PackedVector3Array([Vector3(0, -1, 0), Vector3(min_p.x, min_p.y, min_p.z), Vector3(max_p.x, min_p.y, min_p.z), Vector3(max_p.x, min_p.y, min_p.z), Vector3(min_p.x, min_p.y, max_p.z)]),
	]
	for f: PackedVector3Array in faces:
		st.set_normal(f[0])
		st.add_vertex(f[1])
		st.add_vertex(f[2])
		st.add_vertex(f[3])
		st.add_vertex(f[1])
		st.add_vertex(f[3])
		st.add_vertex(f[4])


static func _get_shared_core_mat(col: Color) -> StandardMaterial3D:
	var key: String = "%.2f_%.2f_%.2f" % [col.r, col.g, col.b]
	if _shared_core_mats.has(key):
		return _shared_core_mats[key]
	var mat: StandardMaterial3D = StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = Color(
		clampf(col.r * 1.15, 0.0, 1.0),
		clampf(col.g * 1.15, 0.0, 1.0),
		clampf(col.b * 1.15, 0.0, 1.0),
		1.0
	)
	_shared_core_mats[key] = mat
	return mat


static func _get_shared_ring_mat(col: Color) -> StandardMaterial3D:
	var key: String = "%.2f_%.2f_%.2f" % [col.r, col.g, col.b]
	if _shared_ring_mats.has(key):
		return _shared_ring_mats[key]
	var mat: StandardMaterial3D = StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = Color(
		lerpf(0.82, col.r, 0.45),
		lerpf(0.66, col.g, 0.45),
		lerpf(0.32, col.b, 0.45),
		1.0
	)
	_shared_ring_mats[key] = mat
	return mat


static func _get_shared_wisp_mat(col: Color) -> StandardMaterial3D:
	var key: String = "%.2f_%.2f_%.2f" % [col.r, col.g, col.b]
	if _shared_wisp_mats.has(key):
		return _shared_wisp_mats[key]
	var mat: StandardMaterial3D = StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.albedo_color = Color(col.r, col.g, col.b, 0.25)
	_shared_wisp_mats[key] = mat
	return mat


static func get_relic_catalog() -> Dictionary[int, Dictionary]:
	return {
		1: {
			"name": "Sigil of the Ossuary King",
			"desc": "+15% Physical Bullet Damage & +10% Reload Speed",
			"color": Color(1.0, 0.78, 0.28, 1.0)
		},
		2: {
			"name": "Phial of Saint Germain",
			"desc": "+25 Max Vitality & +20% Healing from Alchemical Elixirs",
			"color": Color(0.25, 0.95, 0.52, 1.0)
		},
		3: {
			"name": "Eye of the Pale Astral",
			"desc": "+3.5m Eldritch Lantern Radius & -20% Spell Cooldown",
			"color": Color(0.76, 0.38, 1.0, 1.0)
		},
		4: {
			"name": "Cursed Quicksilver Spur",
			"desc": "+12% Hunter Sprint Speed & -15% Quickstep Dash Cooldown",
			"color": Color(0.35, 0.88, 1.0, 1.0)
		},
		5: {
			"name": "Inquisitor's Iron Seal",
			"desc": "+30 Max Armor Plating & +15% Damage Reduction",
			"color": Color(0.75, 0.82, 0.96, 1.0)
		},
		6: {
			"name": "Brimstone Censer Core",
			"desc": "+25% Elemental / DoT Burn & Corrosive Bile Damage",
			"color": Color(1.0, 0.42, 0.16, 1.0)
		},
		7: {
			"name": "Banshee's Tuning Fork",
			"desc": "+20% Headshot Weakspot Critical Multiplier",
			"color": Color(0.95, 0.45, 0.88, 1.0)
		},
		8: {
			"name": "Abyssal Blood Chalice",
			"desc": "Restore +8 HP on Every Occult Enemy Slain",
			"color": Color(0.98, 0.18, 0.28, 1.0)
		}
	}


func _ready() -> void:
	add_to_group("loot_pickups")
	collision_layer = 0
	collision_mask = 1 | 2
	monitoring = true
	monitorable = false
	_bob_time = float(get_instance_id() % 1000) * 0.031
	_build_pickup_geometry()
	body_entered.connect(_on_body_entered)


func _build_pickup_geometry() -> void:
	_ensure_shared_loot_resources()

	var col_shape: CollisionShape3D = CollisionShape3D.new()
	col_shape.name = "PickupSphereCollider"
	col_shape.shape = _shared_col_shape
	col_shape.position = Vector3(0.0, 0.35, 0.0)
	add_child(col_shape)

	_visual_root = Node3D.new()
	_visual_root.name = "VisualRoot"
	_visual_root.position = Vector3(0.0, 0.35, 0.0)
	add_child(_visual_root)

	var orb_color: Color = _get_category_color()
	var core_mat: StandardMaterial3D = _get_shared_core_mat(orb_color)
	var ring_mat: StandardMaterial3D = _get_shared_ring_mat(orb_color)
	var wisp_mat: StandardMaterial3D = _get_shared_wisp_mat(orb_color)

	_core_mesh = MeshInstance3D.new()
	_core_mesh.name = "FacetedCrystalCore"
	_core_mesh.mesh = _shared_crystal_mesh
	_core_mesh.material_override = core_mat
	_core_mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_visual_root.add_child(_core_mesh)

	_ring_mesh = MeshInstance3D.new()
	_ring_mesh.name = "BrassHaloRing"
	_ring_mesh.mesh = _shared_ring_torus
	_ring_mesh.material_override = ring_mat
	_ring_mesh.rotation.x = deg_to_rad(62.0)
	_ring_mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_visual_root.add_child(_ring_mesh)

	_wisp_mesh = MeshInstance3D.new()
	_wisp_mesh.name = "DiamondWisp"
	_wisp_mesh.mesh = _shared_wisp_prism
	_wisp_mesh.material_override = wisp_mat
	_wisp_mesh.position = Vector3(0.0, 0.14, 0.0)
	_wisp_mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_visual_root.add_child(_wisp_mesh)


func _get_category_color() -> Color:
	if drop_category == "silver":
		return Color(0.82, 0.90, 1.0, 1.0)
	elif drop_category == "bone_ash":
		return Color(0.95, 0.86, 0.68, 1.0)
	elif drop_category == "cursed_iron":
		return Color(1.0, 0.52, 0.18, 1.0)
	elif drop_category == "soul_cores":
		return Color(0.84, 0.28, 1.0, 1.0)
	elif drop_category == "health":
		return Color(0.98, 0.22, 0.30, 1.0)
	elif drop_category == "ammo":
		return Color(0.96, 0.78, 0.28, 1.0)
	elif drop_category == "elixir":
		return Color(0.18, 0.96, 0.56, 1.0)
	elif drop_category == "relic":
		return PlayerLoadoutManager.get_relic_tier_beam_color(
			PlayerLoadoutManager.get_relic_tier_for_biome(biome_tier, false)
		)
	return Color(1.0, 0.22, 0.30, 1.0)


func launch_pop(start_pos: Vector3, target_pos: Vector3) -> void:
	_pop_start = start_pos
	_pop_target = target_pos
	_pop_timer = 0.0
	_is_popping = true
	if is_inside_tree():
		global_position = start_pos
	else:
		position = start_pos


func _physics_process(delta: float) -> void:
	if _collected:
		return

	if _is_popping:
		_pop_timer += delta
		var t: float = clampf(_pop_timer / 0.38, 0.0, 1.0)
		var horiz: Vector3 = _pop_start.lerp(_pop_target, t)
		var arc_y: float = sin(t * PI) * 0.95
		if is_inside_tree():
			global_position = horiz + Vector3(0.0, arc_y, 0.0)
		else:
			position = horiz + Vector3(0.0, arc_y, 0.0)
		if t >= 1.0:
			_is_popping = false

	_bob_time += delta * 2.8
	if _visual_root != null:
		_visual_root.position.y = 0.35 + sin(_bob_time) * 0.05
		_visual_root.rotation.y += delta * 2.1
	if _ring_mesh != null:
		_ring_mesh.rotation.z += delta * 2.6

	if is_inside_tree() and get_tree() != null:
		var player_node: Node3D = get_tree().get_first_node_in_group("player") as Node3D
		if player_node != null:
			var dist_sq: float = global_position.distance_squared_to(player_node.global_position)
			if dist_sq <= 2.40:
				collect_pickup(player_node)
			elif dist_sq <= 10.24 and not _is_popping:
				global_position = global_position.move_toward(player_node.global_position + Vector3(0.0, 0.4, 0.0), delta * 9.5)


func _on_body_entered(body: Node3D) -> void:
	if _collected or body == null:
		return
	if body.is_in_group("player") or body.name == "Player" or body.name == "FPSPlayer":
		collect_pickup(body)


func collect_pickup(collector: Node) -> bool:
	if _collected:
		return false
	var lm: PlayerLoadoutManager = collector.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	if lm == null and collector is PlayerLoadoutManager:
		lm = collector as PlayerLoadoutManager
	if lm == null and is_inside_tree() and get_tree().root != null:
		lm = get_tree().root.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	if lm == null:
		return false

	_collected = true
	lm.apply_loot_pickup(
		drop_category,
		xp_amount,
		essence_amount,
		heal_amount,
		armor_amount,
		relic_id,
		resource_key,
		resource_amount,
		biome_tier
	)
	if is_inside_tree():
		visible = false
		queue_free()
	return true


static func spawn_loot_drop(
	parent: Node,
	origin: Vector3,
	category: String,
	forced_relic_id: int = 0,
	depth_mult: float = 1.0,
	b_tier: int = 1
) -> LootDropPickup:
	var pickup: LootDropPickup = LootDropPickup.new()
	pickup.drop_category = category
	pickup.biome_tier = clampi(b_tier, 1, 8)
	var tier_mult: float = 1.0 + float(pickup.biome_tier - 1) * 0.25
	var combined_mult: float = maxf(depth_mult, tier_mult)
	pickup.xp_amount = roundi(35.0 * combined_mult)
	pickup.essence_amount = roundi(25.0 * combined_mult)
	pickup.heal_amount = 35
	pickup.armor_amount = 25

	if category == "silver":
		pickup.resource_key = "silver"
		pickup.resource_amount = roundi(randf_range(12.0, 22.0) * combined_mult)
		pickup.xp_amount = roundi(18.0 * combined_mult)
	elif category == "bone_ash":
		pickup.resource_key = "bone_ash"
		pickup.resource_amount = roundi(randf_range(5.0, 10.0) * combined_mult)
		pickup.xp_amount = roundi(22.0 * combined_mult)
	elif category == "cursed_iron":
		pickup.resource_key = "cursed_iron"
		pickup.resource_amount = maxi(1, roundi(randf_range(1.0, 2.0) * (1.0 + float(pickup.biome_tier - 1) * 0.18)))
		pickup.xp_amount = roundi(28.0 * combined_mult)
	elif category == "soul_cores":
		pickup.resource_key = "soul_cores"
		pickup.resource_amount = 1
		pickup.xp_amount = roundi(45.0 * combined_mult)
	elif category == "xp_essence":
		pickup.resource_key = "silver"
		pickup.resource_amount = roundi(14.0 * combined_mult)

	if forced_relic_id >= 1 and forced_relic_id <= 8:
		pickup.relic_id = forced_relic_id
	else:
		pickup.relic_id = ((pickup.biome_tier - 1) % 8) + 1
	pickup.name = "LootDrop_%s_%d" % [category, randi() % 10000]

	var angle: float = randf() * TAU
	var radius: float = randf_range(0.55, 1.35)
	var offset: Vector3 = Vector3(cos(angle) * radius, 0.0, sin(angle) * radius)
	parent.add_child(pickup)
	pickup.launch_pop(origin + Vector3(0.0, 0.35, 0.0), origin + offset)
	return pickup
