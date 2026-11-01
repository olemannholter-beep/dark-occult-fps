class_name ReliquaryChest
extends Node3D

@export var chest_title: String = "Ancient Reliquary Chest"
@export var chest_biome_id: int = 1
@export var guaranteed_relic_id: int = 1
@export var depth_scale: float = 1.0
@export var reward_scale: float:
	get:
		return depth_scale
	set(value):
		depth_scale = value
@export var is_opened: bool = false
@export var is_completion_chest: bool = false

var _lid_node: Node3D = null
var _lid_anim_timer: float = 0.0
var _sfx_player: AudioStreamPlayer3D = null

static var _shared_sfx_loaded: bool = false
static var _shared_sfx_open: AudioStream = null
static var _shared_ember_box: BoxMesh = null
static var _shared_ember_mat: StandardMaterial3D = null


static func _ensure_shared_chest_resources() -> void:
	if not _shared_sfx_loaded:
		_shared_sfx_loaded = true
		if ResourceLoader.exists("res://assets/audio/sfx/reliquary_chest_open.wav"):
			_shared_sfx_open = load("res://assets/audio/sfx/reliquary_chest_open.wav") as AudioStream
	if _shared_ember_box == null:
		_shared_ember_box = BoxMesh.new()
		_shared_ember_box.size = Vector3(0.055, 0.055, 0.055)
	if _shared_ember_mat == null:
		_shared_ember_mat = StandardMaterial3D.new()
		_shared_ember_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		_shared_ember_mat.albedo_color = Color(1.0, 0.84, 0.32, 1.0)


func _ready() -> void:
	_ensure_shared_chest_resources()
	_resolve_lid_node()
	_setup_audio()


func _resolve_lid_node() -> void:
	for child: Node in get_children():
		if child is Node3D and child.name.to_lower().contains("lid"):
			_lid_node = child as Node3D
			return
	var deep: Node = find_child("*Lid*", true, false)
	if deep is Node3D:
		_lid_node = deep as Node3D


func _setup_audio() -> void:
	_sfx_player = AudioStreamPlayer3D.new()
	_sfx_player.name = "ChestSFXPlayer3D"
	_sfx_player.unit_size = 4.0
	_sfx_player.max_distance = 18.0
	add_child(_sfx_player)


func get_prompt_text(_loadout: PlayerLoadoutManager = null) -> String:
	if is_opened:
		return "%s\n[ EMPTY — RELIQUARY SEAL BROKEN ]" % chest_title
	if is_completion_chest:
		return "%s\n[E] UNSEAL EXPEDITION COMPLETION RELIQUARY CACHE" % chest_title
	return "%s\n[E] UNSEAL RELIQUARY CHEST" % chest_title


func interact(loadout: PlayerLoadoutManager = null) -> void:
	if is_opened:
		return
	open_chest(loadout)


func open_chest(loadout: PlayerLoadoutManager = null) -> Array[LootDropPickup]:
	var spawned: Array[LootDropPickup] = []
	if is_opened:
		return spawned

	is_opened = true
	_lid_anim_timer = 0.01

	if _sfx_player != null and _shared_sfx_open != null and is_inside_tree():
		_sfx_player.stream = _shared_sfx_open
		_sfx_player.play()

	var eff_biome: int = clampi(maxi(chest_biome_id, guaranteed_relic_id), 1, 8)
	var silver_grant: int = 85 + eff_biome * 28 if is_completion_chest else (35 + eff_biome * 12)
	var bone_ash_grant: int = 24 + eff_biome * 8 if is_completion_chest else (12 + eff_biome * 4)
	var iron_grant: int = maxi(2, int(eff_biome / 2) + 2) if is_completion_chest else (1 if eff_biome >= 2 else 0)
	var cores_grant: int = (2 if eff_biome >= 5 else 1) if is_completion_chest else (1 if eff_biome >= 4 else 0)
	var xp_grant: int = 90 + eff_biome * 25 if is_completion_chest else (45 + eff_biome * 15)

	# Grant Crafting Resources, XP, Healing, and Relic in a SINGLE batched call (emitting loadout_changed only ONCE!)
	if loadout != null:
		loadout.grant_chest_rewards_batch(
			silver_grant,
			bone_ash_grant,
			iron_grant,
			cores_grant,
			xp_grant,
			guaranteed_relic_id,
			eff_biome,
			is_completion_chest,
			is_completion_chest
		)

	var parent_node: Node = get_parent() if get_parent() != null else self
	var origin: Vector3 = (global_position if is_inside_tree() else position) + Vector3(0.0, 0.55, 0.0)

	# Spawn lightweight visual-only burst of rising golden ember cubes that self-free after 0.8s (0 physics, 0 OmniLight3D)
	if is_inside_tree():
		_spawn_golden_ember_burst(parent_node, origin)

	# Spawn the 4 lightweight zero-light LootDropPickup crystals (shared static meshes & unshaded materials)
	var d1: LootDropPickup = LootDropPickup.spawn_loot_drop(
		parent_node,
		origin + Vector3(-0.26, 0.0, 0.14),
		"xp_essence",
		0,
		depth_scale,
		eff_biome
	)
	d1.xp_amount = 55
	d1.essence_amount = 45
	spawned.append(d1)

	var d2: LootDropPickup = LootDropPickup.spawn_loot_drop(
		parent_node,
		origin + Vector3(0.26, 0.0, 0.14),
		"bone_ash",
		0,
		depth_scale,
		eff_biome
	)
	spawned.append(d2)

	var third_cat: String = "cursed_iron" if eff_biome >= 2 else "elixir"
	if eff_biome >= 4 and is_completion_chest:
		third_cat = "soul_cores"
	var d3: LootDropPickup = LootDropPickup.spawn_loot_drop(
		parent_node,
		origin + Vector3(0.0, 0.0, 0.30),
		third_cat,
		0,
		depth_scale,
		eff_biome
	)
	spawned.append(d3)

	var d4: LootDropPickup = LootDropPickup.spawn_loot_drop(
		parent_node,
		origin + Vector3(0.0, 0.12, -0.16),
		"relic",
		guaranteed_relic_id,
		depth_scale,
		eff_biome
	)
	spawned.append(d4)

	return spawned


func _spawn_golden_ember_burst(parent_node: Node, origin: Vector3) -> void:
	_ensure_shared_chest_resources()
	var burst_root: Node3D = Node3D.new()
	burst_root.name = "ChestGoldenEmberBurst"
	parent_node.add_child(burst_root)
	burst_root.global_position = origin

	for i: int in range(8):
		var ang: float = float(i) * (TAU / 8.0)
		var ember: MeshInstance3D = MeshInstance3D.new()
		ember.name = "Ember_%d" % i
		ember.mesh = _shared_ember_box
		ember.material_override = _shared_ember_mat
		ember.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		ember.position = Vector3(cos(ang) * 0.18, float(i % 3) * 0.06, sin(ang) * 0.18)
		burst_root.add_child(ember)

	var tw: Tween = burst_root.create_tween()
	tw.tween_property(burst_root, "position:y", burst_root.position.y + 0.85, 0.78)
	tw.parallel().tween_property(burst_root, "scale", Vector3(0.25, 0.25, 0.25), 0.78)
	tw.tween_callback(burst_root.queue_free)


func _process(delta: float) -> void:
	if _lid_anim_timer > 0.0 and _lid_anim_timer < 1.0:
		_lid_anim_timer = minf(1.0, _lid_anim_timer + delta * 2.4)
		if _lid_node != null:
			_lid_node.rotation.x = lerpf(0.0, deg_to_rad(-98.0), _lid_anim_timer)
