class_name ProceduralDungeonGenerator
extends Node3D

const CELL_SIZE: float = 4.0
const DUNGEON_ORIGIN: Vector3 = Vector3(0.0, -500.0, 0.0)

var active_biome_id: int = 0
var active_depth_tier: int = 1
var active_seed: int = 0
var active_room_count: int = 0
var generated_room_centers: Array[Vector3] = []

var last_vista_id: int = 0
var last_vista_name: String = ""
var last_mood_mutator_id: int = 0
var last_mood_mutator_name: String = ""
var last_mood_mutator_color: Color = Color(1.0, 0.65, 0.28, 1.0)
var last_spawned_archetypes: Array[String] = []
var last_spawned_prop_patterns: Array[int] = []

var reserved_prop_cells: Dictionary[Vector3i, String] = {}
var last_occupied_cells: Dictionary[Vector3i, bool] = {}
var last_stair_cells: Dictionary[Vector3i, int] = {}
var last_bridge_cells: Dictionary[Vector3i, float] = {}
var last_balcony_floor_cells: Dictionary[Vector3i, bool] = {}
var last_chest_positions: Array[Vector3] = []
var last_portal_positions: Array[Vector3] = []
var last_room_cells_by_index: Dictionary[int, Array] = {}
var _spawned_centerpiece_positions: Array[Vector3] = []
var _spawned_stair_world_positions: Array[Vector3] = []

var room_containers: Array[Node3D] = []
var room_aabbs: Array[AABB] = []
var room_neighbors: Dictionary[int, Array] = {}
var cell_to_room_index: Dictionary[Vector3i, int] = {}
var active_room_idx: int = 0
var last_total_wall_faces: int = 0
var last_solid_wall_faces: int = 0
var last_ossuary_wall_faces: int = 0
var _cull_timer: float = 0.0
var _player_ref: Node3D = null

var _prefab_cache: Dictionary[String, PackedScene] = {}
var _sealer_mat: StandardMaterial3D = null


class RoomSpec extends RefCounted:
	var room_index: int = 0
	var gx: int = 0
	var gy: int = 0
	var gz: int = 0
	var width_cells: int = 3
	var length_cells: int = 3
	var height_cells: int = 1
	var is_entry: bool = false
	var is_boss_sanctum: bool = false
	var archetype_name: String = "STANDARD"
	var prop_pattern_id: int = 1
	var has_safe_center_override: bool = false
	var safe_center_world: Vector3 = Vector3.ZERO
	var has_spawn_override: bool = false
	var spawn_world_override: Vector3 = Vector3.ZERO

	func center_world(origin: Vector3) -> Vector3:
		if has_safe_center_override:
			return safe_center_world
		var cx: float = origin.x + (float(gx) + float(width_cells - 1) * 0.5) * CELL_SIZE
		var cy: float = origin.y + float(gy) * CELL_SIZE
		var cz: float = origin.z + (float(gz) + float(length_cells - 1) * 0.5) * CELL_SIZE
		return Vector3(cx, cy, cz)

	func geom_center_world(origin: Vector3) -> Vector3:
		var cx: float = origin.x + (float(gx) + float(width_cells - 1) * 0.5) * CELL_SIZE
		var cy: float = origin.y + float(gy) * CELL_SIZE
		var cz: float = origin.z + (float(gz) + float(length_cells - 1) * 0.5) * CELL_SIZE
		return Vector3(cx, cy, cz)


func _ready() -> void:
	_init_sealer_material()


func _process(delta: float) -> void:
	if room_containers.is_empty():
		return
	_cull_timer += delta
	if _cull_timer < 0.12:
		return
	_cull_timer = 0.0

	if _player_ref == null or not is_instance_valid(_player_ref):
		if is_inside_tree() and get_tree() != null and get_tree().root != null:
			_player_ref = get_tree().root.find_child("Player", true, false) as Node3D
			if _player_ref == null:
				_player_ref = get_tree().root.find_child("FPSPlayer", true, false) as Node3D
		elif get_parent() != null:
			_player_ref = get_parent().find_child("Player", true, false) as Node3D
			if _player_ref == null:
				_player_ref = get_parent().find_child("FPSPlayer", true, false) as Node3D

	if _player_ref != null and is_instance_valid(_player_ref):
		var p_pos: Vector3 = _player_ref.global_position if _player_ref.is_inside_tree() else _player_ref.position
		if p_pos.y <= -100.0:
			_update_active_room_culling(p_pos)


func update_active_room_culling(observer_pos: Vector3 = Vector3.INF) -> void:
	_update_active_room_culling(observer_pos)


func _update_active_room_culling(observer_pos: Vector3 = Vector3.INF) -> void:
	if room_containers.is_empty():
		return
	var query_pos: Vector3 = observer_pos
	if query_pos == Vector3.INF:
		if _player_ref != null and is_instance_valid(_player_ref):
			query_pos = _player_ref.global_position if _player_ref.is_inside_tree() else _player_ref.position
		elif not generated_room_centers.is_empty():
			query_pos = generated_room_centers[0]
		else:
			query_pos = DUNGEON_ORIGIN

	var best_idx: int = 0
	var best_dist: float = 99999999.0
	var found_inside_aabb: bool = false
	for i: int in range(room_containers.size()):
		if i < room_aabbs.size():
			var expanded_aabb: AABB = room_aabbs[i].grow(2.2)
			if expanded_aabb.has_point(query_pos):
				var c_dist: float = room_aabbs[i].get_center().distance_to(query_pos)
				if not found_inside_aabb or c_dist < best_dist:
					found_inside_aabb = true
					best_dist = c_dist
					best_idx = i
		if not found_inside_aabb and i < generated_room_centers.size():
			var d: float = generated_room_centers[i].distance_to(query_pos)
			if d < best_dist:
				best_dist = d
				best_idx = i

	active_room_idx = best_idx
	var one_hop_neighbors: Array = room_neighbors.get(active_room_idx, [])

	for i: int in range(room_containers.size()):
		var r_cont: Node3D = room_containers[i]
		if r_cont == null or not is_instance_valid(r_cont):
			continue
		var keep_active: bool = (i == active_room_idx) or one_hop_neighbors.has(i) or (absi(i - active_room_idx) <= 1)
		if r_cont.visible != keep_active:
			r_cont.visible = keep_active
		var target_mode: Node.ProcessMode = Node.PROCESS_MODE_INHERIT if keep_active else Node.PROCESS_MODE_DISABLED
		if r_cont.process_mode != target_mode:
			r_cont.process_mode = target_mode


func _build_room_containers_and_aabbs(
	rooms: Array[RoomSpec],
	occupied_cells: Dictionary[Vector3i, bool]
) -> void:
	room_containers.clear()
	room_aabbs.clear()
	room_neighbors.clear()
	cell_to_room_index.clear()

	var total_rooms: int = rooms.size()
	for r_idx: int in range(total_rooms):
		var r_cont: Node3D = Node3D.new()
		r_cont.name = "RoomContainer_%d" % r_idx
		add_child(r_cont)
		room_containers.append(r_cont)

		var neighbors: Array[int] = []
		if r_idx > 0:
			neighbors.append(r_idx - 1)
		if r_idx < total_rooms - 1:
			neighbors.append(r_idx + 1)
		room_neighbors[r_idx] = neighbors
		r_cont.set_meta("neighbor_room_indices", neighbors)

		if last_room_cells_by_index.has(r_idx):
			var r_cells: Array = last_room_cells_by_index[r_idx]
			for c_var: Variant in r_cells:
				var c_vec: Vector3i = c_var as Vector3i
				cell_to_room_index[c_vec] = r_idx

	# Assign any remaining occupied cells (connecting corridors/stairs) to the nearest room
	for cell: Vector3i in occupied_cells.keys():
		if cell_to_room_index.has(cell):
			continue
		var c_world: Vector3 = _cell_to_world(cell)
		var nearest_r: int = 0
		var nearest_d: float = 99999999.0
		for r_idx: int in range(total_rooms):
			var rc: Vector3 = rooms[r_idx].geom_center_world(DUNGEON_ORIGIN)
			var d: float = c_world.distance_to(rc)
			if d < nearest_d:
				nearest_d = d
				nearest_r = r_idx
		cell_to_room_index[cell] = nearest_r

	# Compute per-room world AABB covering all cells assigned to RoomContainer_i
	for r_idx: int in range(total_rooms):
		var spec: RoomSpec = rooms[r_idx]
		var min_v: Vector3 = DUNGEON_ORIGIN + Vector3(
			float(spec.gx) * CELL_SIZE - 2.5,
			float(spec.gy - 1) * CELL_SIZE - 1.0,
			float(spec.gz) * CELL_SIZE - 2.5
		)
		var max_v: Vector3 = DUNGEON_ORIGIN + Vector3(
			float(spec.gx + spec.width_cells) * CELL_SIZE + 2.5,
			float(spec.gy + spec.height_cells + 1) * CELL_SIZE + 1.0,
			float(spec.gz + spec.length_cells) * CELL_SIZE + 2.5
		)
		var r_aabb: AABB = AABB(min_v, max_v - min_v)
		room_aabbs.append(r_aabb)
		room_containers[r_idx].set_meta("room_aabb", r_aabb)


func _get_room_container(r_idx: int) -> Node3D:
	if r_idx >= 0 and r_idx < room_containers.size():
		return room_containers[r_idx]
	return self


func _enforce_all_room_container_limits() -> void:
	for r_idx: int in range(room_containers.size()):
		var r_cont: Node3D = room_containers[r_idx]
		if r_cont == null or not is_instance_valid(r_cont):
			continue
		var lights: Array[OmniLight3D] = []
		_collect_room_omni_lights_recursive(r_cont, lights)
		for l_i: int in range(lights.size()):
			var light: OmniLight3D = lights[l_i]
			if l_i < 2:
				light.shadow_enabled = false
				light.omni_range = 14.0
				light.distance_fade_enabled = true
				light.distance_fade_begin = 22.0
				light.distance_fade_length = 6.0
			else:
				if light.get_parent() != null:
					light.get_parent().remove_child(light)
				light.free()


func _collect_room_omni_lights_recursive(node: Node, out_lights: Array[OmniLight3D]) -> void:
	if node is OmniLight3D:
		out_lights.append(node as OmniLight3D)
	for child: Node in node.get_children():
		_collect_room_omni_lights_recursive(child, out_lights)


func _init_sealer_material() -> void:
	if _sealer_mat == null:
		var base_mat: Material = GrimdarkMaterialLibrary.get_material_for_name("DarkFlagstone")
		if base_mat is StandardMaterial3D:
			_sealer_mat = (base_mat as StandardMaterial3D).duplicate() as StandardMaterial3D
		else:
			_sealer_mat = StandardMaterial3D.new()
			_sealer_mat.albedo_color = Color(0.10, 0.09, 0.11, 1.0)
			_sealer_mat.roughness = 0.92
		_sealer_mat.cull_mode = BaseMaterial3D.CULL_DISABLED


func _get_prefab(res_path: String) -> PackedScene:
	if _prefab_cache.has(res_path):
		return _prefab_cache[res_path]
	if ResourceLoader.exists(res_path):
		var scene: PackedScene = load(res_path) as PackedScene
		if scene != null:
			_prefab_cache[res_path] = scene
			return scene
	return null


func _spawn_prefab(
	parent: Node3D,
	res_path: String,
	node_name: String,
	pos: Vector3,
	rot_deg: Vector3 = Vector3.ZERO,
	scale_vec: Vector3 = Vector3.ONE
) -> Node3D:
	var scene: PackedScene = _get_prefab(res_path)
	if scene == null:
		return null
	var inst: Node3D = scene.instantiate() as Node3D
	if inst == null:
		return null
	inst.name = node_name
	inst.position = pos
	inst.rotation_degrees = rot_deg
	inst.scale = scale_vec
	parent.add_child(inst)
	return inst


func _get_biome_theme_config(biome_id: int) -> Dictionary[String, Variant]:
	return get_biome_profile(biome_id)


func get_biome_profile(biome_id: int) -> Dictionary[String, Variant]:
	var clamped_id: int = clampi(biome_id, 1, 8)
	var profile: Dictionary[String, Variant] = {
		"biome_id": clamped_id,
		"title": "The Endless Ossuary",
		"light_color": Color(1.0, 0.65, 0.28, 1.0),
		"fog_color": Color(0.28, 0.16, 0.08, 1.0),
		"fog_density": 0.024,
		"ossuary_wall_ratio": 0.33,
		"cistern_floor_ratio": 0.0,
		"double_height_rooms": true,
		"vertical_step_downs": true,
		"accent_wall": "res://scenes/prefabs/architecture/crypt_wall_ossuary_4x4.tscn",
		"hero_monolith": "res://scenes/prefabs/ossuary_variety/ossuary_spine_reliquary_monolith.tscn",
		"chandelier": "res://scenes/prefabs/ossuary_variety/ossuary_bone_chandelier.tscn",
		"buttress_arch": "res://scenes/prefabs/ossuary_variety/ossuary_buttress_arch_4x4.tscn",
		"divider": "res://scenes/prefabs/ossuary_variety/ossuary_burial_niche_divider_4x4.tscn",
		"centerpiece_prefab": "res://scenes/prefabs/architecture/crypt_hanging_cage.tscn",
		"secondary_centerpiece": "res://scenes/prefabs/architecture/standing_iron_brazier.tscn",
		"clutter_primary": "res://scenes/prefabs/architecture/clutter_rubble_bones_pile.tscn",
		"clutter_secondary": "res://scenes/prefabs/architecture/clutter_melted_candle_cluster.tscn",
		"enemy_primary": "res://scenes/prefabs/enemies/enemy_01_ossuary_executioner.tscn",
		"enemy_secondary": "res://scenes/prefabs/enemies/enemy_02_necropolis_praetorian.tscn",
		"ranged_archetype": "RANGED_BONE_ARBALEST"
	}

	match clamped_id:
		1:
			profile["title"] = "The Endless Ossuary"
			profile["light_color"] = Color(1.0, 0.65, 0.28, 1.0)
			profile["fog_color"] = Color(0.32, 0.19, 0.09, 1.0)
			profile["ossuary_wall_ratio"] = 0.33
			profile["accent_wall"] = "res://scenes/prefabs/architecture/crypt_wall_ossuary_4x4.tscn"
			profile["hero_monolith"] = "res://scenes/prefabs/ossuary_variety/ossuary_spine_reliquary_monolith.tscn"
			profile["chandelier"] = "res://scenes/prefabs/ossuary_variety/ossuary_bone_chandelier.tscn"
			profile["buttress_arch"] = "res://scenes/prefabs/ossuary_variety/ossuary_buttress_arch_4x4.tscn"
			profile["divider"] = "res://scenes/prefabs/ossuary_variety/ossuary_burial_niche_divider_4x4.tscn"
			profile["centerpiece_prefab"] = "res://scenes/prefabs/architecture/crypt_hanging_cage.tscn"
			profile["secondary_centerpiece"] = "res://scenes/prefabs/architecture/standing_iron_brazier.tscn"
			profile["clutter_primary"] = "res://scenes/prefabs/architecture/clutter_rubble_bones_pile.tscn"
			profile["clutter_secondary"] = "res://scenes/prefabs/architecture/clutter_melted_candle_cluster.tscn"
			profile["enemy_primary"] = "res://scenes/prefabs/enemies/enemy_01_ossuary_executioner.tscn"
			profile["enemy_secondary"] = "res://scenes/prefabs/enemies/enemy_02_necropolis_praetorian.tscn"
			profile["ranged_archetype"] = "RANGED_BONE_ARBALEST"
		2:
			profile["title"] = "The Royal Necropolis"
			profile["light_color"] = Color(1.0, 0.75, 0.35, 1.0)
			profile["fog_color"] = Color(0.36, 0.25, 0.10, 1.0)
			profile["ossuary_wall_ratio"] = 0.33
			profile["accent_wall"] = "res://scenes/prefabs/dungeon/necropolis_wall_armory_4x4.tscn"
			profile["hero_monolith"] = "res://scenes/prefabs/dungeon/necropolis_iron_maiden_monolith.tscn"
			profile["chandelier"] = "res://scenes/prefabs/dungeon/necropolis_hanging_war_brazier.tscn"
			profile["buttress_arch"] = "res://scenes/prefabs/architecture/crypt_archway_portcullis_4x4.tscn"
			profile["divider"] = "res://scenes/prefabs/architecture/crypt_iron_gate_cell_4x4.tscn"
			profile["centerpiece_prefab"] = "res://scenes/prefabs/dungeon/necropolis_iron_maiden_monolith.tscn"
			profile["secondary_centerpiece"] = "res://scenes/prefabs/architecture/standing_iron_brazier.tscn"
			profile["clutter_primary"] = "res://scenes/prefabs/architecture/clutter_rubble_bones_pile.tscn"
			profile["clutter_secondary"] = "res://scenes/prefabs/architecture/clutter_melted_candle_cluster.tscn"
			profile["enemy_primary"] = "res://scenes/prefabs/enemies/enemy_02_necropolis_praetorian.tscn"
			profile["enemy_secondary"] = "res://scenes/prefabs/enemies/enemy_01_ossuary_executioner.tscn"
			profile["ranged_archetype"] = "RANGED_BONE_ARBALEST"
		3:
			profile["title"] = "The Infinite Reliquary"
			profile["light_color"] = Color(0.82, 0.40, 1.0, 1.0)
			profile["fog_color"] = Color(0.28, 0.11, 0.38, 1.0)
			profile["ossuary_wall_ratio"] = 0.33
			profile["accent_wall"] = "res://scenes/prefabs/dungeon/reliquary_wall_grimoire_4x4.tscn"
			profile["hero_monolith"] = "res://scenes/prefabs/dungeon/reliquary_astral_orrery_monolith.tscn"
			profile["chandelier"] = "res://scenes/prefabs/dungeon/reliquary_chandelier_astrolabe.tscn"
			profile["buttress_arch"] = "res://scenes/prefabs/ossuary_variety/ossuary_buttress_arch_4x4.tscn"
			profile["divider"] = "res://scenes/prefabs/architecture/crypt_rotting_bookshelf_4x4.tscn"
			profile["centerpiece_prefab"] = "res://scenes/prefabs/dungeon/reliquary_astral_orrery_monolith.tscn"
			profile["secondary_centerpiece"] = "res://scenes/prefabs/architecture/crypt_rotting_bookshelf_4x4.tscn"
			profile["clutter_primary"] = "res://scenes/prefabs/architecture/clutter_wooden_crates_barrels.tscn"
			profile["clutter_secondary"] = "res://scenes/prefabs/architecture/clutter_melted_candle_cluster.tscn"
			profile["enemy_primary"] = "res://scenes/prefabs/enemies/enemy_03_reliquary_hexweaver.tscn"
			profile["enemy_secondary"] = "res://scenes/prefabs/enemies/enemy_06_weeping_banshee.tscn"
			profile["ranged_archetype"] = "RANGED_SPREAD_HEXER"
		4:
			profile["title"] = "The Inquisitor's Labyrinth"
			profile["light_color"] = Color(0.95, 0.38, 0.22, 1.0)
			profile["fog_color"] = Color(0.26, 0.12, 0.10, 1.0)
			profile["ossuary_wall_ratio"] = 0.33
			profile["accent_wall"] = "res://scenes/prefabs/dungeon/abattoir_wall_furnace_4x4.tscn"
			profile["hero_monolith"] = "res://scenes/prefabs/dungeon/abattoir_blood_press_monolith.tscn"
			profile["chandelier"] = "res://scenes/prefabs/dungeon/abattoir_hanging_hook_rack.tscn"
			profile["buttress_arch"] = "res://scenes/prefabs/architecture/crypt_archway_portcullis_4x4.tscn"
			profile["divider"] = "res://scenes/prefabs/architecture/crypt_iron_gate_cell_4x4.tscn"
			profile["centerpiece_prefab"] = "res://scenes/prefabs/dungeon/abattoir_blood_press_monolith.tscn"
			profile["secondary_centerpiece"] = "res://scenes/prefabs/architecture/crypt_iron_gate_cell_4x4.tscn"
			profile["clutter_primary"] = "res://scenes/prefabs/architecture/clutter_ceiling_chains_roots.tscn"
			profile["clutter_secondary"] = "res://scenes/prefabs/architecture/clutter_rubble_bones_pile.tscn"
			profile["enemy_primary"] = "res://scenes/prefabs/enemies/enemy_04_inquisitor_rackmaster.tscn"
			profile["enemy_secondary"] = "res://scenes/prefabs/enemies/enemy_01_ossuary_executioner.tscn"
			profile["ranged_archetype"] = "RANGED_PLAGUE_MORTAR"
		5:
			profile["title"] = "The Blighted Cisterns"
			profile["light_color"] = Color(0.42, 0.95, 0.32, 1.0)
			profile["fog_color"] = Color(0.12, 0.38, 0.10, 1.0)
			profile["fog_density"] = 0.035
			profile["ossuary_wall_ratio"] = 0.33
			profile["cistern_floor_ratio"] = 0.45
			profile["accent_wall"] = "res://scenes/prefabs/dungeon/abattoir_wall_furnace_4x4.tscn"
			profile["hero_monolith"] = "res://scenes/prefabs/dungeon/abattoir_blood_press_monolith.tscn"
			profile["chandelier"] = "res://scenes/prefabs/dungeon/abattoir_hanging_hook_rack.tscn"
			profile["centerpiece_prefab"] = "res://scenes/prefabs/architecture/crypt_plague_cauldron.tscn"
			profile["secondary_centerpiece"] = "res://scenes/prefabs/architecture/clutter_wooden_crates_barrels.tscn"
			profile["clutter_primary"] = "res://scenes/prefabs/architecture/clutter_wooden_crates_barrels.tscn"
			profile["clutter_secondary"] = "res://scenes/prefabs/architecture/clutter_rubble_bones_pile.tscn"
			profile["enemy_primary"] = "res://scenes/prefabs/enemies/enemy_05_plague_bloater.tscn"
			profile["enemy_secondary"] = "res://scenes/prefabs/enemies/enemy_03_reliquary_hexweaver.tscn"
			profile["ranged_archetype"] = "RANGED_PLAGUE_MORTAR"
		6:
			profile["title"] = "The Halls of the Weeping Saint"
			profile["light_color"] = Color(0.32, 0.68, 1.0, 1.0)
			profile["fog_color"] = Color(0.10, 0.25, 0.42, 1.0)
			profile["fog_density"] = 0.030
			profile["ossuary_wall_ratio"] = 0.33
			profile["cistern_floor_ratio"] = 0.40
			profile["accent_wall"] = "res://scenes/prefabs/dungeon/reliquary_wall_grimoire_4x4.tscn"
			profile["hero_monolith"] = "res://scenes/prefabs/dungeon/reliquary_astral_orrery_monolith.tscn"
			profile["chandelier"] = "res://scenes/prefabs/dungeon/reliquary_chandelier_astrolabe.tscn"
			profile["centerpiece_prefab"] = "res://scenes/prefabs/architecture/crypt_weeping_statue_pedestal.tscn"
			profile["secondary_centerpiece"] = "res://scenes/prefabs/architecture/clutter_melted_candle_cluster.tscn"
			profile["clutter_primary"] = "res://scenes/prefabs/architecture/clutter_melted_candle_cluster.tscn"
			profile["clutter_secondary"] = "res://scenes/prefabs/architecture/clutter_rubble_bones_pile.tscn"
			profile["enemy_primary"] = "res://scenes/prefabs/enemies/enemy_06_weeping_banshee.tscn"
			profile["enemy_secondary"] = "res://scenes/prefabs/enemies/enemy_02_necropolis_praetorian.tscn"
			profile["ranged_archetype"] = "RANGED_CANTOR_SWARM"
		7:
			profile["title"] = "The Shattered Bell Chasms"
			profile["light_color"] = Color(1.0, 0.42, 0.15, 1.0)
			profile["fog_color"] = Color(0.38, 0.14, 0.05, 1.0)
			profile["ossuary_wall_ratio"] = 0.33
			profile["double_height_rooms"] = true
			profile["vertical_step_downs"] = true
			profile["accent_wall"] = "res://scenes/prefabs/dungeon/necropolis_wall_armory_4x4.tscn"
			profile["hero_monolith"] = "res://scenes/prefabs/dungeon/necropolis_iron_maiden_monolith.tscn"
			profile["chandelier"] = "res://scenes/prefabs/dungeon/necropolis_hanging_war_brazier.tscn"
			profile["centerpiece_prefab"] = "res://scenes/prefabs/architecture/crypt_sunken_bell_crater.tscn"
			profile["secondary_centerpiece"] = "res://scenes/prefabs/architecture/standing_iron_brazier.tscn"
			profile["clutter_primary"] = "res://scenes/prefabs/architecture/clutter_ceiling_chains_roots.tscn"
			profile["clutter_secondary"] = "res://scenes/prefabs/architecture/clutter_rubble_bones_pile.tscn"
			profile["enemy_primary"] = "res://scenes/prefabs/enemies/enemy_07_bell_juggernaut.tscn"
			profile["enemy_secondary"] = "res://scenes/prefabs/enemies/enemy_04_inquisitor_rackmaster.tscn"
			profile["ranged_archetype"] = "RANGED_CANTOR_SWARM"
		8:
			profile["title"] = "The Abyssal Blood Wastes"
			profile["light_color"] = Color(1.0, 0.14, 0.18, 1.0)
			profile["fog_color"] = Color(0.42, 0.04, 0.06, 1.0)
			profile["fog_density"] = 0.036
			profile["ossuary_wall_ratio"] = 0.33
			profile["double_height_rooms"] = true
			profile["accent_wall"] = "res://scenes/prefabs/dungeon/abattoir_wall_furnace_4x4.tscn"
			profile["hero_monolith"] = "res://scenes/prefabs/dungeon/abattoir_blood_press_monolith.tscn"
			profile["chandelier"] = "res://scenes/prefabs/dungeon/abattoir_hanging_hook_rack.tscn"
			profile["centerpiece_prefab"] = "res://scenes/prefabs/architecture/crypt_ritual_obelisk.tscn"
			profile["secondary_centerpiece"] = "res://scenes/prefabs/architecture/crypt_altar.tscn"
			profile["clutter_primary"] = "res://scenes/prefabs/architecture/clutter_rubble_bones_pile.tscn"
			profile["clutter_secondary"] = "res://scenes/prefabs/architecture/clutter_melted_candle_cluster.tscn"
			profile["enemy_primary"] = "res://scenes/prefabs/enemies/enemy_08_abyssal_archon.tscn"
			profile["enemy_secondary"] = "res://scenes/prefabs/enemies/enemy_01_ossuary_executioner.tscn"
			profile["ranged_archetype"] = "RANGED_SPREAD_HEXER"

	return profile


func clear_generated_dungeon() -> void:
	for child: Node in get_children():
		remove_child(child)
		child.free()
	generated_room_centers.clear()
	last_spawned_archetypes.clear()
	last_spawned_prop_patterns.clear()
	reserved_prop_cells.clear()
	last_occupied_cells.clear()
	last_stair_cells.clear()
	last_bridge_cells.clear()
	last_balcony_floor_cells.clear()
	last_chest_positions.clear()
	last_portal_positions.clear()
	last_room_cells_by_index.clear()
	_spawned_centerpiece_positions.clear()
	_spawned_stair_world_positions.clear()
	room_containers.clear()
	room_aabbs.clear()
	room_neighbors.clear()
	cell_to_room_index.clear()
	active_room_idx = 0
	last_total_wall_faces = 0
	last_solid_wall_faces = 0
	last_ossuary_wall_faces = 0
	active_room_count = 0


func get_dungeon_map_data() -> Dictionary:
	return {
		"biome_id": active_biome_id,
		"depth_tier": active_depth_tier,
		"room_count": active_room_count,
		"vista_name": last_vista_name,
		"mood_mutator_name": last_mood_mutator_name,
		"mood_mutator_color": last_mood_mutator_color,
		"occupied_cells": last_occupied_cells,
		"stair_cells": last_stair_cells,
		"bridge_cells": last_bridge_cells,
		"balcony_floor_cells": last_balcony_floor_cells,
		"chest_positions": last_chest_positions,
		"portal_positions": last_portal_positions,
		"room_cells_by_index": last_room_cells_by_index,
		"room_centers": generated_room_centers
	}


func _notify_map_system_new_dungeon(spawn_pos: Vector3) -> void:
	if not is_inside_tree() or get_tree() == null or get_tree().root == null:
		return
	var map_node: Node = get_tree().root.find_child("GothicMapSystem", true, false)
	if map_node != null and map_node.has_method("reset_fog_of_war_for_new_dungeon"):
		map_node.call("reset_fog_of_war_for_new_dungeon", spawn_pos)


func generate_biome_dungeon(
	biome_id: int,
	seed_val: int,
	depth_tier: int = 1,
	return_dest: Vector3 = Vector3(0.0, 0.5, -26.0)
) -> Vector3:
	visible = true
	process_mode = Node.PROCESS_MODE_INHERIT
	_init_sealer_material()
	clear_generated_dungeon()

	var clamped_biome: int = clampi(biome_id, 1, 8)
	var clamped_tier: int = maxi(1, depth_tier)
	active_biome_id = clamped_biome
	active_depth_tier = clamped_tier
	active_seed = seed_val

	# Route All 8 Portals (Biomes 1..8) to the Unified V2 Macro Vertical Voxel Generator
	return generate_v2_vertical_dungeon(clamped_biome, seed_val, clamped_tier, return_dest)

	var profile: Dictionary[String, Variant] = get_biome_profile(clamped_biome)
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = int(seed_val) + clamped_biome * 7919 + clamped_tier * 104729

	var target_rooms: int = 8 + clamped_tier * 2
	var arch_root: Node3D = Node3D.new()
	arch_root.name = "DungeonArchitecture"
	add_child(arch_root)

	var props_root: Node3D = Node3D.new()
	props_root.name = "DungeonPropsAndClutter"
	add_child(props_root)

	var lights_root: Node3D = Node3D.new()
	lights_root.name = "DungeonLightingAndFog"
	add_child(lights_root)

	var enemies_root: Node3D = Node3D.new()
	enemies_root.name = "DungeonEnemies"
	add_child(enemies_root)

	var portals_root: Node3D = Node3D.new()
	portals_root.name = "DungeonPortals"
	add_child(portals_root)

	var occupied_cells: Dictionary[Vector3i, bool] = {}
	var stair_cells: Dictionary[Vector3i, int] = {}
	var rooms: Array[RoomSpec] = []

	var cur_gx: int = 0
	var cur_gy: int = 0
	var cur_gz: int = 0
	var double_h_default: bool = bool(profile["double_height_rooms"])
	var step_downs_enabled: bool = bool(profile["vertical_step_downs"])

	for r_idx: int in range(target_rooms):
		var spec: RoomSpec = RoomSpec.new()
		spec.room_index = r_idx
		spec.is_entry = (r_idx == 0)
		spec.is_boss_sanctum = (r_idx == target_rooms - 1)

		if spec.is_entry:
			spec.width_cells = 3
			spec.length_cells = 3
			spec.height_cells = 2 if double_h_default else 1
		elif spec.is_boss_sanctum:
			spec.width_cells = 5
			spec.length_cells = 5
			spec.height_cells = 2
		else:
			var size_roll: int = rng.randi_range(0, 2)
			if size_roll == 0:
				spec.width_cells = 2
				spec.length_cells = 2
			elif size_roll == 1:
				spec.width_cells = 3
				spec.length_cells = 3
			else:
				spec.width_cells = 4
				spec.length_cells = 4
			spec.height_cells = 2 if (double_h_default or (r_idx % 3 == 2)) else 1

		if r_idx == 0:
			spec.gx = 0
			spec.gy = 0
			spec.gz = 0
		else:
			var prev: RoomSpec = rooms[r_idx - 1]
			var corridor_cells: int = 3
			var drop_y: bool = step_downs_enabled and (r_idx % 2 == 1)
			var next_gy: int = prev.gy - (1 if drop_y else 0)
			# Alternate advancing North (-Z) with East/West dogleg shifts so corridors frame each room entrance
			var lateral_shift: int = 0
			if not drop_y and r_idx < target_rooms - 1:
				lateral_shift = 1 if (r_idx % 2 == 1) else -1

			var prev_mid_x: int = prev.gx + prev.width_cells / 2
			var new_gz: int = prev.gz - corridor_cells - spec.length_cells
			var new_gx: int = prev_mid_x + lateral_shift - (spec.width_cells / 2)

			spec.gx = new_gx
			spec.gy = next_gy
			spec.gz = new_gz

			# Carve corridor connecting prev room north edge (prev.gz) to spec south edge (spec.gz + spec.length_cells - 1)
			var corr_x: int = clampi(prev_mid_x, spec.gx, spec.gx + spec.width_cells - 1)
			for cx_fill: int in range(mini(prev_mid_x, corr_x), maxi(prev_mid_x, corr_x) + 1):
				occupied_cells[Vector3i(cx_fill, prev.gy, prev.gz - 1)] = true

			for step_idx: int in range(1, corridor_cells + 1):
				var cz: int = prev.gz - step_idx
				if drop_y and step_idx == 2:
					# Place staircase descending from prev.gy down to next_gy (-Z direction)
					var lower_cell: Vector3i = Vector3i(corr_x, next_gy, cz)
					var upper_cell: Vector3i = Vector3i(corr_x, prev.gy, cz)
					occupied_cells[lower_cell] = true
					occupied_cells[upper_cell] = true
					stair_cells[lower_cell] = 0
				else:
					var c_gy: int = prev.gy if (not drop_y or step_idx < 2) else next_gy
					occupied_cells[Vector3i(corr_x, c_gy, cz)] = true
					if double_h_default:
						occupied_cells[Vector3i(corr_x, c_gy + 1, cz)] = true

		# Register all cells inside RoomSpec
		var room_cell_list: Array[Vector3i] = []
		for dx: int in range(spec.width_cells):
			for dz: int in range(spec.length_cells):
				for dy: int in range(spec.height_cells):
					var r_cell: Vector3i = Vector3i(spec.gx + dx, spec.gy + dy, spec.gz + dz)
					occupied_cells[r_cell] = true
					room_cell_list.append(r_cell)
		last_room_cells_by_index[r_idx] = room_cell_list

		rooms.append(spec)
		generated_room_centers.append(spec.center_world(DUNGEON_ORIGIN) + Vector3(0.0, 1.5, 0.0))

	active_room_count = rooms.size()
	last_occupied_cells = occupied_cells.duplicate()
	last_stair_cells = stair_cells.duplicate()
	_build_room_containers_and_aabbs(rooms, occupied_cells)

	# 1. Execute Watertight 3D Voxel Sealer across all occupied_cells (grouped into RoomContainer_0..N-1)
	_seal_voxel_cells(arch_root, occupied_cells, stair_cells, profile, rng)

	# 2. Populate every room with Biome-Matched Architecture, Centerpieces, Clutter, Lighting, Fog, and Enemies
	for spec: RoomSpec in rooms:
		var r_cont: Node3D = _get_room_container(spec.room_index)
		_populate_room(
			spec,
			profile,
			r_cont,
			r_cont,
			r_cont,
			r_cont,
			r_cont,
			return_dest,
			rng
		)

	_enforce_all_room_container_limits()
	var entry_center: Vector3 = rooms[0].center_world(DUNGEON_ORIGIN)
	var final_spawn: Vector3 = Vector3(entry_center.x, entry_center.y + 0.55, entry_center.z)
	_update_active_room_culling(final_spawn)
	_notify_map_system_new_dungeon(final_spawn)
	return final_spawn


func _world_to_cell(pos: Vector3) -> Vector3i:
	var rx: int = roundi((pos.x - DUNGEON_ORIGIN.x) / CELL_SIZE)
	var ry: int = floori((pos.y - DUNGEON_ORIGIN.y + 0.5) / CELL_SIZE)
	var rz: int = roundi((pos.z - DUNGEON_ORIGIN.z) / CELL_SIZE)
	return Vector3i(rx, ry, rz)


func _cell_to_world(cell: Vector3i) -> Vector3:
	return DUNGEON_ORIGIN + Vector3(
		float(cell.x) * CELL_SIZE,
		float(cell.y) * CELL_SIZE,
		float(cell.z) * CELL_SIZE
	)


func _get_stair_bottom_entry_cell(stair_cell: Vector3i, rot_deg: int) -> Vector3i:
	var norm_rot: int = posmod(rot_deg, 360)
	if norm_rot == 180:
		return Vector3i(stair_cell.x, stair_cell.y, stair_cell.z + 1)
	elif norm_rot == 90:
		return Vector3i(stair_cell.x - 1, stair_cell.y, stair_cell.z)
	elif norm_rot == 270:
		return Vector3i(stair_cell.x + 1, stair_cell.y, stair_cell.z)
	return Vector3i(stair_cell.x, stair_cell.y, stair_cell.z - 1)


func _get_stair_top_landing_cell(stair_cell: Vector3i, rot_deg: int) -> Vector3i:
	var norm_rot: int = posmod(rot_deg, 360)
	if norm_rot == 180:
		return Vector3i(stair_cell.x, stair_cell.y + 1, stair_cell.z - 1)
	elif norm_rot == 90:
		return Vector3i(stair_cell.x + 1, stair_cell.y + 1, stair_cell.z)
	elif norm_rot == 270:
		return Vector3i(stair_cell.x - 1, stair_cell.y + 1, stair_cell.z)
	return Vector3i(stair_cell.x, stair_cell.y + 1, stair_cell.z + 1)


func _is_stair_passage_boundary(cell: Vector3i, face_dir: Vector3i, stair_cells: Dictionary[Vector3i, int]) -> bool:
	if stair_cells.has(cell):
		var rot_deg: int = stair_cells[cell]
		var b_entry: Vector3i = _get_stair_bottom_entry_cell(cell, rot_deg)
		var b_dir: Vector3i = b_entry - cell
		if face_dir == b_dir or face_dir == -b_dir:
			return true
	var below: Vector3i = Vector3i(cell.x, cell.y - 1, cell.z)
	if stair_cells.has(below):
		var rot_deg: int = stair_cells[below]
		var b_entry: Vector3i = _get_stair_bottom_entry_cell(below, rot_deg)
		var b_dir: Vector3i = b_entry - below
		if face_dir == b_dir or face_dir == -b_dir:
			return true
	return false


func _is_walkable_floor_cell(
	cell: Vector3i,
	occupied_cells: Dictionary[Vector3i, bool],
	bridge_cells: Dictionary[Vector3i, float],
	balcony_floor_cells: Dictionary[Vector3i, bool],
	stair_cells: Dictionary[Vector3i, int]
) -> bool:
	if not occupied_cells.has(cell):
		return false
	if stair_cells.has(cell):
		return false
	var below: Vector3i = Vector3i(cell.x, cell.y - 1, cell.z)
	if stair_cells.has(below):
		return false
	if not occupied_cells.has(below):
		return true
	if balcony_floor_cells.has(cell) or bridge_cells.has(cell):
		return true
	return false


func _is_near_any_stair_or_centerpiece(pos: Vector3, min_stair_dist: float, min_cp_dist: float) -> bool:
	for st_pos: Vector3 in _spawned_stair_world_positions:
		var d_xz: float = Vector2(pos.x - st_pos.x, pos.z - st_pos.z).length()
		if d_xz < min_stair_dist and absf(pos.y - st_pos.y) < 5.0:
			return true
	for cp_pos: Vector3 in _spawned_centerpiece_positions:
		var d_cp: float = Vector2(pos.x - cp_pos.x, pos.z - cp_pos.z).length()
		if d_cp < min_cp_dist and absf(pos.y - cp_pos.y) < 3.5:
			return true
	return false


func _find_safe_prop_world_pos(
	spec: RoomSpec,
	desired_pos: Vector3,
	is_centerpiece: bool,
	min_stair_dist: float = 4.0
) -> Vector3:
	var desired_cell: Vector3i = _world_to_cell(desired_pos)
	if (
		_is_walkable_floor_cell(desired_cell, last_occupied_cells, last_bridge_cells, last_balcony_floor_cells, last_stair_cells)
		and not reserved_prop_cells.has(desired_cell)
		and not _is_near_any_stair_or_centerpiece(desired_pos, min_stair_dist, 2.8 if is_centerpiece else 1.8)
	):
		if is_centerpiece:
			reserved_prop_cells[desired_cell] = "CENTERPIECE"
			_spawned_centerpiece_positions.append(desired_pos)
		return desired_pos

	# Search room cells for the closest valid unreserved walkable floor cell
	var best_pos: Vector3 = desired_pos
	var best_cell: Vector3i = desired_cell
	var best_dist: float = 999999.0
	var found: bool = false
	for dy: int in [-1, 0, 1]:
		for dx: int in range(spec.width_cells):
			for dz: int in range(spec.length_cells):
				var cand_cell: Vector3i = Vector3i(spec.gx + dx, spec.gy + dy, spec.gz + dz)
				if not _is_walkable_floor_cell(cand_cell, last_occupied_cells, last_bridge_cells, last_balcony_floor_cells, last_stair_cells):
					continue
				if reserved_prop_cells.has(cand_cell):
					continue
				var cand_pos: Vector3 = _cell_to_world(cand_cell)
				if _is_near_any_stair_or_centerpiece(cand_pos, min_stair_dist, 2.8 if is_centerpiece else 1.8):
					continue
				var d: float = cand_pos.distance_to(desired_pos)
				if d < best_dist:
					best_dist = d
					best_pos = cand_pos
					best_cell = cand_cell
					found = true

	if found and is_centerpiece:
		reserved_prop_cells[best_cell] = "CENTERPIECE"
		_spawned_centerpiece_positions.append(best_pos)
	return best_pos


func _seal_voxel_cells(
	arch_root: Node3D,
	occupied_cells: Dictionary[Vector3i, bool],
	stair_cells: Dictionary[Vector3i, int],
	profile: Dictionary[String, Variant],
	rng: RandomNumberGenerator,
	bridge_cells: Dictionary[Vector3i, float] = {},
	balcony_floor_cells: Dictionary[Vector3i, bool] = {}
) -> void:
	var ossuary_ratio: float = float(profile["ossuary_wall_ratio"])
	var cistern_ratio: float = float(profile["cistern_floor_ratio"])

	var floor_slab_mesh: BoxMesh = BoxMesh.new()
	floor_slab_mesh.size = Vector3(4.16, 0.24, 4.16)

	var roof_slab_mesh: BoxMesh = BoxMesh.new()
	roof_slab_mesh.size = Vector3(4.24, 0.28, 4.24)

	var wall_back_ns_mesh: BoxMesh = BoxMesh.new()
	wall_back_ns_mesh.size = Vector3(4.24, 4.24, 0.24)

	var wall_back_ew_mesh: BoxMesh = BoxMesh.new()
	wall_back_ew_mesh.size = Vector3(0.24, 4.24, 4.24)

	var floor_box_shape: BoxShape3D = BoxShape3D.new()
	floor_box_shape.size = Vector3(4.02, 0.28, 4.02)

	var roof_box_shape: BoxShape3D = BoxShape3D.new()
	roof_box_shape.size = Vector3(4.28, 0.28, 4.28)

	var wall_ns_shape: BoxShape3D = BoxShape3D.new()
	wall_ns_shape.size = Vector3(4.28, 4.28, 0.28)

	var wall_ew_shape: BoxShape3D = BoxShape3D.new()
	wall_ew_shape.size = Vector3(0.28, 4.28, 4.28)

	var room_sealer_bodies: Dictionary[int, StaticBody3D] = {}
	if not room_containers.is_empty():
		for r_i: int in range(room_containers.size()):
			var sb: StaticBody3D = StaticBody3D.new()
			sb.name = "RoomSealerStaticBody_%d" % r_i
			sb.collision_layer = 1
			sb.collision_mask = 1
			sb.process_mode = Node.PROCESS_MODE_ALWAYS
			room_containers[r_i].add_child(sb)
			room_sealer_bodies[r_i] = sb
	else:
		var fallback_sb: StaticBody3D = StaticBody3D.new()
		fallback_sb.name = "DungeonSealerStaticBody"
		fallback_sb.collision_layer = 1
		fallback_sb.collision_mask = 1
		fallback_sb.process_mode = Node.PROCESS_MODE_ALWAYS
		arch_root.add_child(fallback_sb)
		room_sealer_bodies[0] = fallback_sb

	var cell_idx: int = 0
	for cell: Vector3i in occupied_cells.keys():
		cell_idx += 1
		var owner_r_idx: int = int(cell_to_room_index.get(cell, 0))
		var cell_arch_parent: Node3D = _get_room_container(owner_r_idx) if not room_containers.is_empty() else arch_root
		var sealer_body: StaticBody3D = room_sealer_bodies.get(owner_r_idx, room_sealer_bodies.get(0, null))
		var world_pos: Vector3 = DUNGEON_ORIGIN + Vector3(
			float(cell.x) * CELL_SIZE,
			float(cell.y) * CELL_SIZE,
			float(cell.z) * CELL_SIZE
		)

		# Spawn staircase if this cell is a stair lower cell (stairs_stone_4x4 top is at local Y=0, bottom at local Y=-4)
		if stair_cells.has(cell):
			var stair_world_pos: Vector3 = world_pos + Vector3(0.0, CELL_SIZE, 0.0)
			_spawn_prefab(
				cell_arch_parent,
				"res://scenes/prefabs/architecture/stairs_stone_4x4.tscn",
				"ProcStairs_%d" % cell_idx,
				stair_world_pos,
				Vector3(0.0, float(stair_cells[cell]), 0.0)
			)
			_spawned_stair_world_positions.append(world_pos)

		# Spawn bespoke Ossuary stone bridge if this upper cell spans a sunken chasm
		if bridge_cells.has(cell):
			_spawn_prefab(
				cell_arch_parent,
				"res://scenes/prefabs/ossuary_variety/ossuary_stone_bridge_4x4.tscn",
				"ProcBridge_%d" % cell_idx,
				world_pos,
				Vector3(0.0, bridge_cells[cell], 0.0)
			)

		# BOTTOM FACE (-Y neighbor empty, OR explicit mezzanine/balcony cell)
		var below_cell: Vector3i = Vector3i(cell.x, cell.y - 1, cell.z)
		var is_outer_bottom: bool = not occupied_cells.has(below_cell)
		var is_balcony_floor: bool = balcony_floor_cells.has(cell) and not bridge_cells.has(cell)
		if (is_outer_bottom or is_balcony_floor) and not stair_cells.has(cell) and not stair_cells.has(below_cell):
			var use_cistern: bool = false
			if is_outer_bottom and cistern_ratio > 0.0 and not stair_cells.has(cell):
				# Keep center walkway dry (cell.x != 0) or alternate checkerboard
				if absi(cell.x) >= 1 and ((cell.x + cell.z) % 2 == 0):
					use_cistern = rng.randf() < (cistern_ratio * 1.35)
			var floor_path: String = (
				"res://scenes/prefabs/architecture/crypt_drowned_cistern_4x4.tscn"
				if use_cistern
				else "res://scenes/prefabs/architecture/floor_stone_4x4.tscn"
			)
			_spawn_prefab(cell_arch_parent, floor_path, "ProcFloor_%d" % cell_idx, world_pos)

			# Watertight sub-floor backing slab + static collider on both bottommost floors and elevated balconies
			var sub_floor_pos: Vector3 = world_pos + Vector3(0.0, -0.35 if use_cistern else -0.14, 0.0)
			var sub_floor: MeshInstance3D = MeshInstance3D.new()
			sub_floor.name = "SealerSubFloor_%d" % cell_idx
			sub_floor.mesh = floor_slab_mesh
			sub_floor.material_override = _sealer_mat
			sub_floor.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			sub_floor.visibility_range_end = 0.0
			sub_floor.position = sub_floor_pos
			cell_arch_parent.add_child(sub_floor)

			var col_f: CollisionShape3D = CollisionShape3D.new()
			col_f.name = "ColFloor_%d" % cell_idx
			col_f.shape = floor_box_shape
			col_f.position = sub_floor_pos
			sealer_body.add_child(col_f)

			# Complete 4-Sided Balcony Railings Around Sunken Pits & Mezzanines across All 8 Biomes
			if active_biome_id >= 1 and active_biome_id <= 8 and not stair_cells.has(cell) and not stair_cells.has(below_cell):
				var card_dirs: Array[Vector3i] = [
					Vector3i(0, 0, -1),
					Vector3i(0, 0, 1),
					Vector3i(-1, 0, 0),
					Vector3i(1, 0, 0)
				]
				var card_rots: Array[float] = [0.0, 180.0, 90.0, -90.0]
				var card_offs: Array[Vector3] = [
					Vector3(0.0, 0.0, -1.85),
					Vector3(0.0, 0.0, 1.85),
					Vector3(-1.85, 0.0, 0.0),
					Vector3(1.85, 0.0, 0.0)
				]
				for d_i: int in range(4):
					var dir_v: Vector3i = card_dirs[d_i]
					var n_cell: Vector3i = cell + dir_v
					var below_n: Vector3i = Vector3i(n_cell.x, n_cell.y - 1, n_cell.z)
					# Check if n_cell is an open drop-off cell into a carved pit/lower floor
					if (
						occupied_cells.has(n_cell)
						and occupied_cells.has(below_n)
						and not balcony_floor_cells.has(n_cell)
						and not bridge_cells.has(n_cell)
					):
						# Skip railing if below_n has a staircase whose top landing connects onto `cell`
						var connects_stair_top: bool = false
						if stair_cells.has(below_n):
							var top_land: Vector3i = _get_stair_top_landing_cell(below_n, stair_cells[below_n])
							if top_land == cell:
								connects_stair_top = true
						if not connects_stair_top:
							_spawn_prefab(
								cell_arch_parent,
								"res://scenes/prefabs/ossuary_variety/ossuary_balcony_railing_4m.tscn",
								"ProcBalconyRailing_%d_%d" % [cell_idx, d_i],
								world_pos + card_offs[d_i],
								Vector3(0.0, card_rots[d_i], 0.0)
							)

		# TOP FACE (+Y neighbor empty)
		var above_cell: Vector3i = Vector3i(cell.x, cell.y + 1, cell.z)
		if not occupied_cells.has(above_cell):
			_spawn_prefab(
				cell_arch_parent,
				"res://scenes/prefabs/architecture/crypt_corridor_vault_4x4.tscn",
				"ProcVault_%d" % cell_idx,
				world_pos + Vector3(0.0, 4.0, 0.0)
			)
			var roof_pos: Vector3 = world_pos + Vector3(0.0, 4.08, 0.0)
			var roof_cap: MeshInstance3D = MeshInstance3D.new()
			roof_cap.name = "SealerRoofCap_%d" % cell_idx
			roof_cap.mesh = roof_slab_mesh
			roof_cap.material_override = _sealer_mat
			roof_cap.visibility_range_end = 0.0
			roof_cap.position = roof_pos
			cell_arch_parent.add_child(roof_cap)

			var col_r: CollisionShape3D = CollisionShape3D.new()
			col_r.name = "ColRoof_%d" % cell_idx
			col_r.shape = roof_box_shape
			col_r.position = roof_pos
			sealer_body.add_child(col_r)

		# Phase 3.2: 1-in-3 Accent Wall Rule on Base Level (posmod(cell.x + cell.z, 3) == 0 and is_outer_bottom)
		# Upper-level walls (gy + 1) and the remaining 66% of base walls use clean wall_stone_solid
		var accent_wall_path: String = String(profile.get("accent_wall", "res://scenes/prefabs/architecture/crypt_wall_ossuary_4x4.tscn"))
		var use_accent_ossuary: bool = is_outer_bottom and (posmod(cell.x + cell.z, 3) == 0)
		var _unused_ossuary_ratio: float = ossuary_ratio

		# NORTH FACE (-Z neighbor empty)
		if not occupied_cells.has(Vector3i(cell.x, cell.y, cell.z - 1)) and not _is_stair_passage_boundary(cell, Vector3i(0, 0, -1), stair_cells):
			var wall_n: String = (
				accent_wall_path
				if use_accent_ossuary
				else "res://scenes/prefabs/architecture/wall_stone_solid.tscn"
			)
			last_total_wall_faces += 1
			if use_accent_ossuary:
				last_ossuary_wall_faces += 1
			else:
				last_solid_wall_faces += 1
			_spawn_prefab(
				cell_arch_parent,
				wall_n,
				"ProcWallN_%d" % cell_idx,
				world_pos + Vector3(0.0, 0.0, -2.0),
				Vector3.ZERO
			)
			var pos_n: Vector3 = world_pos + Vector3(0.0, 2.0, -2.18)
			var back_n: MeshInstance3D = MeshInstance3D.new()
			back_n.name = "SealerWallN_%d" % cell_idx
			back_n.mesh = wall_back_ns_mesh
			back_n.material_override = _sealer_mat
			back_n.visibility_range_end = 0.0
			back_n.position = pos_n
			cell_arch_parent.add_child(back_n)

			var col_n: CollisionShape3D = CollisionShape3D.new()
			col_n.name = "ColWallN_%d" % cell_idx
			col_n.shape = wall_ns_shape
			col_n.position = pos_n
			sealer_body.add_child(col_n)

		# SOUTH FACE (+Z neighbor empty)
		if not occupied_cells.has(Vector3i(cell.x, cell.y, cell.z + 1)) and not _is_stair_passage_boundary(cell, Vector3i(0, 0, 1), stair_cells):
			var wall_s: String = (
				accent_wall_path
				if use_accent_ossuary
				else "res://scenes/prefabs/architecture/wall_stone_solid.tscn"
			)
			last_total_wall_faces += 1
			if use_accent_ossuary:
				last_ossuary_wall_faces += 1
			else:
				last_solid_wall_faces += 1
			_spawn_prefab(
				cell_arch_parent,
				wall_s,
				"ProcWallS_%d" % cell_idx,
				world_pos + Vector3(0.0, 0.0, 2.0),
				Vector3(0.0, 180.0, 0.0)
			)
			var pos_s: Vector3 = world_pos + Vector3(0.0, 2.0, 2.18)
			var back_s: MeshInstance3D = MeshInstance3D.new()
			back_s.name = "SealerWallS_%d" % cell_idx
			back_s.mesh = wall_back_ns_mesh
			back_s.material_override = _sealer_mat
			back_s.visibility_range_end = 0.0
			back_s.position = pos_s
			cell_arch_parent.add_child(back_s)

			var col_s: CollisionShape3D = CollisionShape3D.new()
			col_s.name = "ColWallS_%d" % cell_idx
			col_s.shape = wall_ns_shape
			col_s.position = pos_s
			sealer_body.add_child(col_s)

		# WEST FACE (-X neighbor empty)
		if not occupied_cells.has(Vector3i(cell.x - 1, cell.y, cell.z)) and not _is_stair_passage_boundary(cell, Vector3i(-1, 0, 0), stair_cells):
			var wall_w: String = (
				accent_wall_path
				if use_accent_ossuary
				else "res://scenes/prefabs/architecture/wall_stone_solid.tscn"
			)
			last_total_wall_faces += 1
			if use_accent_ossuary:
				last_ossuary_wall_faces += 1
			else:
				last_solid_wall_faces += 1
			_spawn_prefab(
				cell_arch_parent,
				wall_w,
				"ProcWallW_%d" % cell_idx,
				world_pos + Vector3(-2.0, 0.0, 0.0),
				Vector3(0.0, 90.0, 0.0)
			)
			var pos_w: Vector3 = world_pos + Vector3(-2.18, 2.0, 0.0)
			var back_w: MeshInstance3D = MeshInstance3D.new()
			back_w.name = "SealerWallW_%d" % cell_idx
			back_w.mesh = wall_back_ew_mesh
			back_w.material_override = _sealer_mat
			back_w.visibility_range_end = 0.0
			back_w.position = pos_w
			cell_arch_parent.add_child(back_w)

			var col_w: CollisionShape3D = CollisionShape3D.new()
			col_w.name = "ColWallW_%d" % cell_idx
			col_w.shape = wall_ew_shape
			col_w.position = pos_w
			sealer_body.add_child(col_w)

		# EAST FACE (+X neighbor empty)
		if not occupied_cells.has(Vector3i(cell.x + 1, cell.y, cell.z)) and not _is_stair_passage_boundary(cell, Vector3i(1, 0, 0), stair_cells):
			var wall_e: String = (
				accent_wall_path
				if use_accent_ossuary
				else "res://scenes/prefabs/architecture/wall_stone_solid.tscn"
			)
			last_total_wall_faces += 1
			if use_accent_ossuary:
				last_ossuary_wall_faces += 1
			else:
				last_solid_wall_faces += 1
			_spawn_prefab(
				cell_arch_parent,
				wall_e,
				"ProcWallE_%d" % cell_idx,
				world_pos + Vector3(2.0, 0.0, 0.0),
				Vector3(0.0, -90.0, 0.0)
			)
			var pos_e: Vector3 = world_pos + Vector3(2.18, 2.0, 0.0)
			var back_e: MeshInstance3D = MeshInstance3D.new()
			back_e.name = "SealerWallE_%d" % cell_idx
			back_e.mesh = wall_back_ew_mesh
			back_e.material_override = _sealer_mat
			back_e.visibility_range_end = 0.0
			back_e.position = pos_e
			cell_arch_parent.add_child(back_e)

			var col_e: CollisionShape3D = CollisionShape3D.new()
			col_e.name = "ColWallE_%d" % cell_idx
			col_e.shape = wall_ew_shape
			col_e.position = pos_e
			sealer_body.add_child(col_e)


func _populate_room(
	spec: RoomSpec,
	profile: Dictionary[String, Variant],
	arch_root: Node3D,
	props_root: Node3D,
	lights_root: Node3D,
	enemies_root: Node3D,
	portals_root: Node3D,
	return_dest: Vector3,
	rng: RandomNumberGenerator
) -> void:
	var r_idx: int = spec.room_index
	var center: Vector3 = spec.center_world(DUNGEON_ORIGIN)
	var half_w: float = float(spec.width_cells) * CELL_SIZE * 0.5
	var half_l: float = float(spec.length_cells) * CELL_SIZE * 0.5
	var b_id: int = int(profile["biome_id"])
	var light_col: Color = profile["light_color"] as Color
	var fog_col: Color = profile["fog_color"] as Color

	# 1. Corner / Colonnade Crypt Pillars (double-stacked in double-height rooms)
	if spec.width_cells >= 3:
		var p_off_x: float = half_w - 2.2
		var p_off_z: float = half_l - 2.2
		var pillar_corners: Array[Vector3] = [
			Vector3(center.x - p_off_x, center.y, center.z - p_off_z),
			Vector3(center.x + p_off_x, center.y, center.z - p_off_z),
			Vector3(center.x - p_off_x, center.y, center.z + p_off_z),
			Vector3(center.x + p_off_x, center.y, center.z + p_off_z)
		]
		for c_i: int in range(pillar_corners.size()):
			var p_pos: Vector3 = pillar_corners[c_i]
			_spawn_prefab(
				arch_root,
				"res://scenes/prefabs/architecture/crypt_pillar.tscn",
				"Room%d_Pillar_%d" % [r_idx, c_i],
				p_pos
			)
			if spec.height_cells >= 2:
				_spawn_prefab(
					arch_root,
					"res://scenes/prefabs/architecture/crypt_pillar.tscn",
					"Room%d_UpperPillar_%d" % [r_idx, c_i],
					p_pos + Vector3(0.0, 4.0, 0.0)
				)

	# 2. Biome-Specific Centerpieces & Secondary Architectural Props
	var cp_path: String = String(profile["centerpiece_prefab"])
	var sec_path: String = String(profile["secondary_centerpiece"])

	if not spec.is_entry and not spec.is_boss_sanctum:
		var cp_pos: Vector3 = center + Vector3(0.0, 2.2 if cp_path.ends_with("hanging_cage.tscn") else 0.0, 0.0)
		_spawn_prefab(
			props_root,
			cp_path,
			"Room%d_Centerpiece" % r_idx,
			cp_pos,
			Vector3(0.0, float(rng.randi_range(0, 3) * 90), 0.0)
		)
		_spawn_prefab(
			props_root,
			sec_path,
			"Room%d_SecondaryProp_A" % r_idx,
			center + Vector3(-half_w + 2.4, 0.0, 0.0),
			Vector3(0.0, 90.0, 0.0)
		)
		_spawn_prefab(
			props_root,
			sec_path,
			"Room%d_SecondaryProp_B" % r_idx,
			center + Vector3(half_w - 2.4, 0.0, 0.0),
			Vector3(0.0, -90.0, 0.0)
		)
		if b_id == 4:
			# Inquisitor's Labyrinth portcullis threshold
			_spawn_prefab(
				arch_root,
				"res://scenes/prefabs/architecture/crypt_archway_portcullis_4x4.tscn",
				"Room%d_Portcullis" % r_idx,
				center + Vector3(0.0, 0.0, half_l - 1.8)
			)
		elif b_id == 8:
			# Abyssal Blood Wastes flanking sarcophagi
			_spawn_prefab(
				props_root,
				"res://scenes/prefabs/architecture/crypt_sarcophagus_ornate.tscn",
				"Room%d_AbyssSarc" % r_idx,
				center + Vector3(-2.6, 0.0, -1.8),
				Vector3(0.0, 25.0, 0.0)
			)
	elif spec.is_boss_sanctum:
		# Grand Boss Sanctum centerpiece + flanking braziers + Dual Portals
		var boss_cp_pos: Vector3 = center + Vector3(0.0, 2.4 if cp_path.ends_with("hanging_cage.tscn") else 0.0, 1.5)
		_spawn_prefab(props_root, cp_path, "Room%d_BossCenterpiece" % r_idx, boss_cp_pos)
		_spawn_prefab(
			props_root,
			"res://scenes/prefabs/architecture/standing_iron_brazier.tscn",
			"Room%d_BossBrazierL" % r_idx,
			center + Vector3(-3.8, 0.0, -2.5)
		)
		_spawn_prefab(
			props_root,
			"res://scenes/prefabs/architecture/standing_iron_brazier.tscn",
			"Room%d_BossBrazierR" % r_idx,
			center + Vector3(3.8, 0.0, -2.5)
		)

		# Spawn Deeper Biome Rift Portal (Left-North) and Sanctuary Return Portal (Right-North)
		var deeper_portal_node: Node3D = _spawn_prefab(
			portals_root,
			"res://scenes/prefabs/hub/occult_rift_portal.tscn",
			"DeeperBiomeRiftPortal",
			center + Vector3(-3.2, 0.0, -half_l + 2.4),
			Vector3(0.0, 15.0, 0.0)
		)
		if deeper_portal_node is OccultPortal:
			last_portal_positions.append(deeper_portal_node.position)
			(deeper_portal_node as OccultPortal).configure_portal(
				b_id,
				String(profile["title"]),
				light_col,
				false,
				return_dest,
				active_depth_tier + 1
			)

		var return_portal_node: Node3D = _spawn_prefab(
			portals_root,
			"res://scenes/prefabs/hub/occult_rift_portal.tscn",
			"SanctuaryReturnPortal",
			center + Vector3(3.2, 0.0, -half_l + 2.4),
			Vector3(0.0, -15.0, 0.0)
		)
		if return_portal_node is OccultPortal:
			last_portal_positions.append(return_portal_node.position)
			(return_portal_node as OccultPortal).configure_portal(
				b_id,
				String(profile["title"]),
				 Color(0.95, 0.85, 0.52, 1.0),
				true,
				return_dest,
				active_depth_tier
			)

	# 3. Overhauled Environmental Clutter Props & DustMotesParticles
	var cl_a: String = String(profile["clutter_primary"])
	var cl_b: String = String(profile["clutter_secondary"])
	var cl_y_a: float = 3.85 if cl_a.ends_with("ceiling_chains_roots.tscn") else 0.0
	var cl_y_b: float = 3.85 if cl_b.ends_with("ceiling_chains_roots.tscn") else 0.0

	_spawn_prefab(
		props_root,
		cl_a,
		"Room%d_ClutterA" % r_idx,
		center + Vector3(-half_w + 1.5, cl_y_a, -half_l + 1.5),
		Vector3(0.0, rng.randf_range(0.0, 360.0), 0.0)
	)
	_spawn_prefab(
		props_root,
		cl_b,
		"Room%d_ClutterB" % r_idx,
		center + Vector3(half_w - 1.5, cl_y_b, half_l - 1.5),
		Vector3(0.0, rng.randf_range(0.0, 360.0), 0.0)
	)

	# 4. Biome-Tinted OmniLight3D + Local FogVolume + DustMotesParticles
	var omni: OmniLight3D = OmniLight3D.new()
	omni.name = "Room%d_BiomeLight" % r_idx
	omni.position = center + Vector3(0.0, 3.0, 0.0)
	omni.light_color = light_col
	omni.light_energy = 2.15 if spec.is_boss_sanctum else 1.65
	omni.omni_range = 14.0
	omni.omni_attenuation = 1.35
	omni.shadow_enabled = false
	omni.distance_fade_enabled = true
	omni.distance_fade_begin = 22.0
	omni.distance_fade_shadow = 12.0
	omni.distance_fade_length = 6.0
	lights_root.add_child(omni)

	var fog_vol: FogVolume = FogVolume.new()
	fog_vol.name = "Room%d_BiomeFogVolume" % r_idx
	fog_vol.position = center + Vector3(0.0, 1.8, 0.0)
	fog_vol.size = Vector3(half_w * 1.9, float(spec.height_cells) * 3.6, half_l * 1.9)
	var fog_mat: FogMaterial = FogMaterial.new()
	fog_mat.density = float(profile["fog_density"])
	fog_mat.albedo = fog_col
	fog_mat.emission = Color(light_col.r * 0.22, light_col.g * 0.22, light_col.b * 0.22, 1.0)
	fog_vol.material = fog_mat
	lights_root.add_child(fog_vol)

	var dust: GPUParticles3D = _create_biome_dust_motes(
		"Room%d_DustMotesParticles" % r_idx,
		center + Vector3(0.0, 2.0, 0.0),
		light_col
	)
	lights_root.add_child(dust)

	# 5. Spawn 1-2 Gothic Reliquary Chests per procedural dungeon (Mid-Dungeon + Finale Boss Sanctum)
	var reward_mult: float = 1.0 + float(maxi(1, active_depth_tier) - 1) * 0.30
	if spec.is_boss_sanctum or r_idx == maxi(1, active_room_count / 2):
		var chest_offset: Vector3 = Vector3(0.0, 0.0, -0.8) if spec.is_boss_sanctum else Vector3(half_w - 2.2, 0.0, -half_l + 2.2)
		var chest_node: Node3D = _spawn_prefab(
			props_root,
			"res://scenes/prefabs/props/prop_gothic_reliquary_chest.tscn",
			"Room%d_ReliquaryChest" % r_idx,
			center + chest_offset,
			Vector3.ZERO
		)
		if chest_node is ReliquaryChest:
			last_chest_positions.append(chest_node.position)
			var r_chest: ReliquaryChest = chest_node as ReliquaryChest
			r_chest.guaranteed_relic_id = b_id
			r_chest.reward_scale = reward_mult

	# 6. Spawn 2-4 Active Biome Enemies in every combat room (80% signature biome enemy + 20% support)
	#    plus a 1.25x-scale 2.2x-HP Elite Biome Champion guarding the Finale Sanctum room!
	if not spec.is_entry:
		var enemy_count: int = 3 if spec.is_boss_sanctum else rng.randi_range(2, 4)
		var ep_a: String = String(profile["enemy_primary"])
		var ep_b: String = String(profile["enemy_secondary"])
		for e_i: int in range(enemy_count):
			var angle: float = float(e_i) * (TAU / float(enemy_count)) + 0.45
			var dist: float = minf(half_w, half_l) * 0.48
			var e_pos: Vector3 = center + Vector3(cos(angle) * dist, 0.0, sin(angle) * dist)
			var use_signature: bool = (e_i == 0) or (rng.randf() < 0.80)
			var e_path: String = ep_a if use_signature else ep_b
			var spawned_enemy: Node3D = _spawn_prefab(
				enemies_root,
				e_path,
				"Room%d_Enemy_%d" % [r_idx, e_i],
				e_pos,
				Vector3(0.0, rad_to_deg(-angle), 0.0)
			)
			if spawned_enemy is OccultEnemyAI:
				var ai_enemy: OccultEnemyAI = spawned_enemy as OccultEnemyAI
				ai_enemy.is_passive_dummy = false
				ai_enemy.apply_depth_scaling(active_depth_tier, b_id)
			elif spawned_enemy is TestDummyEnemy:
				var td_enemy: TestDummyEnemy = spawned_enemy as TestDummyEnemy
				td_enemy.apply_depth_scaling(active_depth_tier, b_id)

		if spec.is_boss_sanctum:
			var champ_pos: Vector3 = center + Vector3(0.0, 0.0, 0.65)
			var champ_node: Node3D = _spawn_prefab(
				enemies_root,
				ep_a,
				"Room%d_EliteBiomeChampion" % r_idx,
				champ_pos,
				Vector3.ZERO,
				Vector3(1.25, 1.25, 1.25)
			)
			if champ_node is OccultEnemyAI:
				var champ_ai: OccultEnemyAI = champ_node as OccultEnemyAI
				champ_ai.is_passive_dummy = false
				champ_ai.apply_depth_scaling(active_depth_tier, b_id)
				champ_ai.configure_as_elite_champion()
			elif champ_node is TestDummyEnemy:
				var champ_td: TestDummyEnemy = champ_node as TestDummyEnemy
				champ_td.apply_depth_scaling(active_depth_tier, b_id)
				champ_td.max_health = roundf(champ_td.max_health * 2.2)
				champ_td.current_health = champ_td.max_health
				champ_td.guaranteed_relic_drop = true


func _create_biome_dust_motes(node_name: String, pos: Vector3, tint: Color) -> GPUParticles3D:
	var particles: GPUParticles3D = GPUParticles3D.new()
	particles.name = node_name
	particles.position = pos
	particles.amount = 36
	particles.lifetime = 6.0
	particles.preprocess = 1.5
	particles.visibility_aabb = AABB(Vector3(-6.0, -3.0, -6.0), Vector3(12.0, 6.0, 12.0))

	var p_mat: ParticleProcessMaterial = ParticleProcessMaterial.new()
	p_mat.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	p_mat.emission_box_extents = Vector3(4.2, 1.8, 4.2)
	p_mat.gravity = Vector3(0.0, 0.02, 0.0)
	p_mat.initial_velocity_min = 0.03
	p_mat.initial_velocity_max = 0.10
	p_mat.scale_min = 0.5
	p_mat.scale_max = 1.2
	particles.process_material = p_mat

	var quad: QuadMesh = QuadMesh.new()
	quad.size = Vector2(0.03, 0.03)
	var m_mat: StandardMaterial3D = StandardMaterial3D.new()
	m_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m_mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	m_mat.albedo_color = Color(tint.r, tint.g, tint.b, 0.42)
	quad.material = m_mat
	particles.draw_pass_1 = quad
	return particles


# ==============================================================================
# PORTAL 1 ("THE ENDLESS OSSUARY") DEEP PROCEDURAL DIVERSITY V2 VERTICAL SLICE
# ==============================================================================

func _shuffle_string_array(arr: Array[String], rng: RandomNumberGenerator) -> void:
	for i: int in range(arr.size() - 1, 0, -1):
		var j: int = rng.randi_range(0, i)
		var tmp: String = arr[i]
		arr[i] = arr[j]
		arr[j] = tmp


func _shuffle_int_array(arr: Array[int], rng: RandomNumberGenerator) -> void:
	for i: int in range(arr.size() - 1, 0, -1):
		var j: int = rng.randi_range(0, i)
		var tmp: int = arr[i]
		arr[i] = arr[j]
		arr[j] = tmp


func generate_ossuary_v2_dungeon(
	seed_val: int,
	depth_tier: int = 1,
	return_dest: Vector3 = Vector3(0.0, 0.5, -26.0)
) -> Vector3:
	return generate_v2_vertical_dungeon(1, seed_val, depth_tier, return_dest)


func generate_v2_vertical_dungeon(
	biome_id: int,
	seed_val: int,
	depth_tier: int = 1,
	return_dest: Vector3 = Vector3(0.0, 0.5, -26.0)
) -> Vector3:
	var clamped_biome: int = clampi(biome_id, 1, 8)
	active_biome_id = clamped_biome
	active_depth_tier = maxi(1, depth_tier)
	active_seed = seed_val

	var profile: Dictionary[String, Variant] = get_biome_profile(clamped_biome)
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = int(seed_val) * 1664525 + active_depth_tier * 1013904223 + (clamped_biome - 1) * 7919

	# Roll 1 of 3 Mood Mutators (Biome 1 uses its 3 signature Ossuary mutators; Biomes 2-8 modulate lighting/fog around their bespoke theme)
	var mutator_idx: int = posmod(absi(seed_val) + active_depth_tier, 3)
	last_mood_mutator_id = mutator_idx
	var light_energy_mult: float = 1.0
	var extra_reliquary_chest: bool = (mutator_idx == 2)

	if clamped_biome == 1:
		if mutator_idx == 0:
			last_mood_mutator_name = "The Torchlit Ossuary"
			last_mood_mutator_color = Color(1.0, 0.65, 0.28, 1.0)
			profile["light_color"] = last_mood_mutator_color
			profile["fog_color"] = Color(0.18, 0.13, 0.08, 1.0)
			profile["fog_density"] = 0.014
			profile["cistern_floor_ratio"] = 0.0
			profile["enemy_primary"] = "res://scenes/prefabs/enemies/enemy_01_ossuary_executioner.tscn"
			profile["enemy_secondary"] = "res://scenes/prefabs/enemies/enemy_03_reliquary_hexweaver.tscn"
			light_energy_mult = 1.0
		elif mutator_idx == 1:
			last_mood_mutator_name = "The Drowned Bone-Cisterns"
			last_mood_mutator_color = Color(0.65, 0.92, 0.45, 1.0)
			profile["light_color"] = last_mood_mutator_color
			profile["fog_color"] = Color(0.10, 0.17, 0.08, 1.0)
			profile["fog_density"] = 0.022
			profile["cistern_floor_ratio"] = 0.40
			profile["enemy_primary"] = "res://scenes/prefabs/enemies/enemy_01_ossuary_executioner.tscn"
			profile["enemy_secondary"] = "res://scenes/prefabs/enemies/enemy_05_plague_bloater.tscn"
			light_energy_mult = 1.0
		else:
			last_mood_mutator_name = "The Stygian Blood-Catacombs"
			last_mood_mutator_color = Color(1.0, 0.25, 0.18, 1.0)
			profile["light_color"] = last_mood_mutator_color
			profile["fog_color"] = Color(0.18, 0.05, 0.05, 1.0)
			profile["fog_density"] = 0.020
			profile["cistern_floor_ratio"] = 0.0
			profile["enemy_primary"] = "res://scenes/prefabs/enemies/enemy_01_ossuary_executioner.tscn"
			profile["enemy_secondary"] = "res://scenes/prefabs/enemies/enemy_03_reliquary_hexweaver.tscn"
			light_energy_mult = 0.60
			extra_reliquary_chest = true
	else:
		last_mood_mutator_name = String(profile["title"])
		last_mood_mutator_color = profile["light_color"] as Color
		light_energy_mult = 0.85 if mutator_idx == 2 else 1.0

	# Select Starting Spawn Room (Room 0) from 4 Opening Vistas
	var vista_idx: int = posmod(absi(seed_val), 4)
	last_vista_id = vista_idx
	var vista_archetype: String = ""
	if vista_idx == 0:
		last_vista_name = "The High Overlook StairHall"
		vista_archetype = "VISTA_HIGH_OVERLOOK_STAIRHALL"
	elif vista_idx == 1:
		last_vista_name = "The Chasm Bridge Crossing"
		vista_archetype = "VISTA_CHASM_BRIDGE_CROSSING"
	elif vista_idx == 2:
		last_vista_name = "The Cruciform Bone Basilica"
		vista_archetype = "VISTA_CRUCIFORM_BONE_BASILICA"
	else:
		last_vista_name = "The Cloister Ring Walk"
		vista_archetype = "VISTA_CLOISTER_RING_WALK"

	var target_rooms: int = 8 + depth_tier * 2
	var arch_root: Node3D = Node3D.new()
	arch_root.name = "DungeonArchitecture"
	add_child(arch_root)

	var props_root: Node3D = Node3D.new()
	props_root.name = "DungeonPropsAndClutter"
	add_child(props_root)

	var lights_root: Node3D = Node3D.new()
	lights_root.name = "DungeonLightingAndFog"
	add_child(lights_root)

	var enemies_root: Node3D = Node3D.new()
	enemies_root.name = "DungeonEnemies"
	add_child(enemies_root)

	var portals_root: Node3D = Node3D.new()
	portals_root.name = "DungeonPortals"
	add_child(portals_root)

	var occupied_cells: Dictionary[Vector3i, bool] = {}
	var stair_cells: Dictionary[Vector3i, int] = {}
	var bridge_cells: Dictionary[Vector3i, float] = {}
	var balcony_floor_cells: Dictionary[Vector3i, bool] = {}
	var rooms: Array[RoomSpec] = []

	# Build Shuffled Archetype Deck (7 Body Archetypes + Finale OSSUARY_SANCTUM_ROTUNDA = 8 Archetypes)
	var base_archetypes: Array[String] = [
		"OSSUARY_CROSS_NAVE",
		"OSSUARY_CHASM_BRIDGE",
		"OSSUARY_SUNKEN_PIT_ARENA",
		"OSSUARY_CLOISTER_RING",
		"OSSUARY_L_CATACOMB",
		"OSSUARY_PILLARED_GALLERY",
		"OSSUARY_MAZE_VAULT"
	]
	var archetype_deck: Array[String] = base_archetypes.duplicate()
	_shuffle_string_array(archetype_deck, rng)

	# Build Shuffled Prop-Layout Pattern Deck (Patterns 1..5)
	var base_patterns: Array[int] = [1, 2, 3, 4, 5]
	var pattern_deck: Array[int] = base_patterns.duplicate()
	_shuffle_int_array(pattern_deck, rng)

	var prev_archetype: String = vista_archetype

	for r_idx: int in range(target_rooms):
		var spec: RoomSpec = RoomSpec.new()
		spec.room_index = r_idx
		spec.is_entry = (r_idx == 0)
		spec.is_boss_sanctum = (r_idx == target_rooms - 1)

		if pattern_deck.is_empty():
			pattern_deck = base_patterns.duplicate()
			_shuffle_int_array(pattern_deck, rng)
		spec.prop_pattern_id = pattern_deck.pop_back()
		last_spawned_prop_patterns.append(spec.prop_pattern_id)

		if spec.is_entry:
			spec.archetype_name = vista_archetype
		elif spec.is_boss_sanctum:
			spec.archetype_name = "OSSUARY_SANCTUM_ROTUNDA"
		else:
			if archetype_deck.is_empty():
				archetype_deck = base_archetypes.duplicate()
				_shuffle_string_array(archetype_deck, rng)
				if archetype_deck[archetype_deck.size() - 1] == prev_archetype and archetype_deck.size() > 1:
					var swap_s: String = archetype_deck[0]
					archetype_deck[0] = archetype_deck[archetype_deck.size() - 1]
					archetype_deck[archetype_deck.size() - 1] = swap_s
			spec.archetype_name = archetype_deck.pop_back()
			prev_archetype = spec.archetype_name

		last_spawned_archetypes.append(spec.archetype_name)

		# Assign Footprint Dimensions per Archetype
		match spec.archetype_name:
			"VISTA_HIGH_OVERLOOK_STAIRHALL":
				spec.width_cells = 3
				spec.length_cells = 4
				spec.height_cells = 2
			"VISTA_CHASM_BRIDGE_CROSSING", "OSSUARY_CHASM_BRIDGE":
				spec.width_cells = 3
				spec.length_cells = 4
				spec.height_cells = 2
			"VISTA_CRUCIFORM_BONE_BASILICA", "OSSUARY_CROSS_NAVE", "OSSUARY_SANCTUM_ROTUNDA":
				spec.width_cells = 5
				spec.length_cells = 5
				spec.height_cells = 2
			"VISTA_CLOISTER_RING_WALK", "OSSUARY_CLOISTER_RING":
				spec.width_cells = 4
				spec.length_cells = 4
				spec.height_cells = 1
			"OSSUARY_SUNKEN_PIT_ARENA":
				spec.width_cells = 5
				spec.length_cells = 5
				spec.height_cells = 2
			"OSSUARY_L_CATACOMB":
				spec.width_cells = 4
				spec.length_cells = 4
				spec.height_cells = 1
			"OSSUARY_PILLARED_GALLERY":
				spec.width_cells = 3
				spec.length_cells = 5
				spec.height_cells = 2
			"OSSUARY_MAZE_VAULT":
				spec.width_cells = 4
				spec.length_cells = 4
				spec.height_cells = 1
			_:
				spec.width_cells = 3
				spec.length_cells = 3
				spec.height_cells = 1

		if r_idx == 0:
			spec.gx = 0
			spec.gy = 0
			spec.gz = 0
		else:
			var prev: RoomSpec = rooms[r_idx - 1]
			var corridor_cells: int = 3
			var drop_y: bool = (r_idx % 3 == 2)
			var next_gy: int = prev.gy - (1 if drop_y else 0)
			var lateral_shift: int = 0
			if not drop_y and r_idx < target_rooms - 1:
				lateral_shift = 1 if (r_idx % 2 == 1) else -1

			var prev_exit_x: int = prev.gx + (1 if prev.archetype_name == "OSSUARY_L_CATACOMB" else prev.width_cells / 2)
			var new_gz: int = prev.gz - corridor_cells - spec.length_cells
			var entry_local_dx: int = 2 if spec.archetype_name == "OSSUARY_L_CATACOMB" else (spec.width_cells / 2)
			var new_gx: int = prev_exit_x + lateral_shift - entry_local_dx

			spec.gx = new_gx
			spec.gy = next_gy
			spec.gz = new_gz

			# Reserve prev room North doorway cell & 1 cell inside prev room
			reserved_prop_cells[Vector3i(prev_exit_x, prev.gy, prev.gz)] = "DOORWAY_CLEAR"
			reserved_prop_cells[Vector3i(prev_exit_x, prev.gy, prev.gz + 1)] = "DOORWAY_CLEAR"

			var corr_x: int = spec.gx + entry_local_dx
			# Reserve spec room South doorway cell & 1 cell inside spec room
			reserved_prop_cells[Vector3i(corr_x, next_gy, spec.gz + spec.length_cells - 1)] = "DOORWAY_CLEAR"
			reserved_prop_cells[Vector3i(corr_x, next_gy, spec.gz + spec.length_cells - 2)] = "DOORWAY_CLEAR"

			for cx_fill: int in range(mini(prev_exit_x, corr_x), maxi(prev_exit_x, corr_x) + 1):
				occupied_cells[Vector3i(cx_fill, prev.gy, prev.gz - 1)] = true
				occupied_cells[Vector3i(cx_fill, prev.gy + 1, prev.gz - 1)] = true
				reserved_prop_cells[Vector3i(cx_fill, prev.gy, prev.gz - 1)] = "DOORWAY_CLEAR"

			for step_idx: int in range(1, corridor_cells + 1):
				var cz: int = prev.gz - step_idx
				if drop_y and step_idx == 2:
					var lower_cell: Vector3i = Vector3i(corr_x, next_gy, cz)
					var upper_cell: Vector3i = Vector3i(corr_x, prev.gy, cz)
					occupied_cells[lower_cell] = true
					occupied_cells[upper_cell] = true
					stair_cells[lower_cell] = 0
				else:
					var c_gy: int = prev.gy if (not drop_y or step_idx < 2) else next_gy
					occupied_cells[Vector3i(corr_x, c_gy, cz)] = true
					occupied_cells[Vector3i(corr_x, c_gy + 1, cz)] = true
					reserved_prop_cells[Vector3i(corr_x, c_gy, cz)] = "DOORWAY_CLEAR"

		# Carve Archetype-Specific Voxel Cells, Bridges, Balconies, and Stairs
		var before_keys: Dictionary = occupied_cells.duplicate()
		_carve_ossuary_v2_room(
			spec,
			occupied_cells,
			stair_cells,
			bridge_cells,
			balcony_floor_cells
		)
		var v2_room_cells: Array[Vector3i] = []
		for c_key: Vector3i in occupied_cells.keys():
			if not before_keys.has(c_key):
				v2_room_cells.append(c_key)
		last_room_cells_by_index[r_idx] = v2_room_cells

		rooms.append(spec)
		generated_room_centers.append(spec.center_world(DUNGEON_ORIGIN) + Vector3(0.0, 1.5, 0.0))

	active_room_count = rooms.size()

	# Populate stair & bridge reservations and cache voxel dictionaries for inspection
	for st_cell: Vector3i in stair_cells.keys():
		var st_rot: int = stair_cells[st_cell]
		reserved_prop_cells[st_cell] = "STAIR_CLEAR"
		reserved_prop_cells[Vector3i(st_cell.x, st_cell.y + 1, st_cell.z)] = "STAIR_CLEAR"
		var b_entry: Vector3i = _get_stair_bottom_entry_cell(st_cell, st_rot)
		var t_land: Vector3i = _get_stair_top_landing_cell(st_cell, st_rot)
		reserved_prop_cells[b_entry] = "STAIR_CLEAR"
		reserved_prop_cells[t_land] = "STAIR_CLEAR"
		reserved_prop_cells[Vector3i(t_land.x, t_land.y - 1, t_land.z)] = "STAIR_CLEAR"

	for br_cell: Vector3i in bridge_cells.keys():
		reserved_prop_cells[br_cell] = "BRIDGE"
		reserved_prop_cells[Vector3i(br_cell.x, br_cell.y - 1, br_cell.z)] = "BRIDGE"

	last_occupied_cells = occupied_cells.duplicate()
	last_stair_cells = stair_cells.duplicate()
	last_bridge_cells = bridge_cells.duplicate()
	last_balcony_floor_cells = balcony_floor_cells.duplicate()
	_build_room_containers_and_aabbs(rooms, occupied_cells)

	# 1. Execute Watertight 3D Voxel Boundary Sealer supporting Bridges & Sunken Pits
	_seal_voxel_cells(
		arch_root,
		occupied_cells,
		stair_cells,
		profile,
		rng,
		bridge_cells,
		balcony_floor_cells
	)

	# 2. Populate every room with Archetype Architecture, 5 Prop Patterns, Mutator Lighting & Enemies
	for spec: RoomSpec in rooms:
		var r_cont: Node3D = _get_room_container(spec.room_index)
		_populate_ossuary_v2_room(
			spec,
			profile,
			r_cont,
			r_cont,
			r_cont,
			r_cont,
			portals_root,
			return_dest,
			light_energy_mult,
			extra_reliquary_chest,
			rng
		)

	_enforce_all_room_container_limits()
	var v2_spawn: Vector3 = Vector3.ZERO
	if rooms[0].has_spawn_override:
		v2_spawn = rooms[0].spawn_world_override
	else:
		var entry_center: Vector3 = rooms[0].center_world(DUNGEON_ORIGIN)
		v2_spawn = Vector3(entry_center.x, entry_center.y + 0.55, entry_center.z)
	_update_active_room_culling(v2_spawn)
	_notify_map_system_new_dungeon(v2_spawn)
	return v2_spawn


func _carve_ossuary_v2_room(
	spec: RoomSpec,
	occupied_cells: Dictionary[Vector3i, bool],
	stair_cells: Dictionary[Vector3i, int],
	bridge_cells: Dictionary[Vector3i, float],
	balcony_floor_cells: Dictionary[Vector3i, bool]
) -> void:
	var gx: int = spec.gx
	var gy: int = spec.gy
	var gz: int = spec.gz
	var w: int = spec.width_cells
	var l: int = spec.length_cells
	var h: int = spec.height_cells

	match spec.archetype_name:
		"VISTA_HIGH_OVERLOOK_STAIRHALL":
			# 3x4 double-height hall (gy and gy+1); south row dz=3 is elevated mezzanine (gy+1) with twin stairs at dx=0,2
			for dx: int in range(w):
				for dz: int in range(l):
					occupied_cells[Vector3i(gx + dx, gy, gz + dz)] = true
					occupied_cells[Vector3i(gx + dx, gy + 1, gz + dz)] = true
			for dx_m: int in range(w):
				balcony_floor_cells[Vector3i(gx + dx_m, gy + 1, gz + 3)] = true
			stair_cells[Vector3i(gx + 0, gy, gz + 2)] = 0
			stair_cells[Vector3i(gx + 2, gy, gz + 2)] = 0
			var sp_cell: Vector3i = Vector3i(gx + 1, gy + 1, gz + 3)
			spec.has_spawn_override = true
			spec.spawn_world_override = DUNGEON_ORIGIN + Vector3(
				float(sp_cell.x) * CELL_SIZE,
				float(sp_cell.y) * CELL_SIZE + 0.55,
				float(sp_cell.z) * CELL_SIZE
			)
			spec.has_safe_center_override = true
			spec.safe_center_world = DUNGEON_ORIGIN + Vector3(
				float(gx + 1) * CELL_SIZE,
				float(gy) * CELL_SIZE,
				float(gz + 1) * CELL_SIZE
			)

		"VISTA_CHASM_BRIDGE_CROSSING", "OSSUARY_CHASM_BRIDGE":
			# 3x4 chasm room: carved at gy, gy+1, and sunken bone pit at gy-1 for middle rows dz in {1, 2}
			for dx: int in range(w):
				for dz: int in range(l):
					occupied_cells[Vector3i(gx + dx, gy, gz + dz)] = true
					occupied_cells[Vector3i(gx + dx, gy + 1, gz + dz)] = true
					if dz == 1 or dz == 2:
						occupied_cells[Vector3i(gx + dx, gy - 1, gz + dz)] = true
			# Central 1x2 bridge span at (gx + 1, gy, gz + 1..2)
			bridge_cells[Vector3i(gx + 1, gy, gz + 1)] = 0.0
			bridge_cells[Vector3i(gx + 1, gy, gz + 2)] = 0.0
			# Staircase in sunken pit (dx = 0, dz = 1) with rot_deg = 180:
			# bottom foot opens South into pit (dx = 0, gy - 1, dz = 2), top landing connects North onto balcony (dx = 0, gy, dz = 0)
			stair_cells[Vector3i(gx + 0, gy - 1, gz + 1)] = 180
			spec.has_safe_center_override = true
			spec.safe_center_world = DUNGEON_ORIGIN + Vector3(
				float(gx + 2) * CELL_SIZE,
				float(gy - 1) * CELL_SIZE,
				float(gz + 2) * CELL_SIZE
			)
			if spec.is_entry:
				spec.has_spawn_override = true
				spec.spawn_world_override = DUNGEON_ORIGIN + Vector3(
					float(gx + 1) * CELL_SIZE,
					float(gy) * CELL_SIZE + 0.55,
					float(gz + 3) * CELL_SIZE
				)

		"VISTA_CRUCIFORM_BONE_BASILICA", "OSSUARY_CROSS_NAVE", "OSSUARY_SANCTUM_ROTUNDA":
			# 5x5 Cruciform / Octagonal footprint (4 corner cells left uncarved) + double-height dome
			for dx: int in range(w):
				for dz: int in range(l):
					var is_corner: bool = (dx == 0 or dx == w - 1) and (dz == 0 or dz == l - 1)
					if is_corner:
						continue
					occupied_cells[Vector3i(gx + dx, gy, gz + dz)] = true
					occupied_cells[Vector3i(gx + dx, gy + 1, gz + dz)] = true
			if spec.is_entry:
				spec.has_spawn_override = true
				spec.spawn_world_override = DUNGEON_ORIGIN + Vector3(
					float(gx + 2) * CELL_SIZE,
					float(gy) * CELL_SIZE + 0.55,
					float(gz + 4) * CELL_SIZE
				)

		"VISTA_CLOISTER_RING_WALK", "OSSUARY_CLOISTER_RING":
			# 4x4 Donut/Cloister room: center 2x2 cells (dx in 1..2, dz in 1..2) left un-carved as solid core!
			for dx: int in range(w):
				for dz: int in range(l):
					var is_center_core: bool = (dx >= 1 and dx <= 2) and (dz >= 1 and dz <= 2)
					if is_center_core:
						continue
					occupied_cells[Vector3i(gx + dx, gy, gz + dz)] = true
					occupied_cells[Vector3i(gx + dx, gy + 1, gz + dz)] = true
			spec.has_safe_center_override = true
			spec.safe_center_world = DUNGEON_ORIGIN + Vector3(
				float(gx + 1) * CELL_SIZE,
				float(gy) * CELL_SIZE,
				float(gz + 3) * CELL_SIZE
			)
			if spec.is_entry:
				spec.has_spawn_override = true
				spec.spawn_world_override = DUNGEON_ORIGIN + Vector3(
					float(gx + 1) * CELL_SIZE,
					float(gy) * CELL_SIZE + 0.55,
					float(gz + 3) * CELL_SIZE
				)

		"OSSUARY_SUNKEN_PIT_ARENA":
			# 5x5 Sunken Amphitheater room: outer 1-cell ring (16 cells) is upper balcony walkway at gy,
			# inner 3x3 (9 cells: dx in 1..3, dz in 1..3) drops 4m down to sunken pit floor at gy - 1.
			for dx: int in range(w):
				for dz: int in range(l):
					occupied_cells[Vector3i(gx + dx, gy, gz + dz)] = true
					occupied_cells[Vector3i(gx + dx, gy + 1, gz + dz)] = true
					var is_inner_pit: bool = (dx >= 1 and dx <= 3) and (dz >= 1 and dz <= 3)
					if is_inner_pit:
						occupied_cells[Vector3i(gx + dx, gy - 1, gz + dz)] = true
					else:
						balcony_floor_cells[Vector3i(gx + dx, gy, gz + dz)] = true
			# 1 single staircase along North edge of 3x3 pit at (gx + 2, gy - 1, gz + 1) with rot_deg = 180:
			# bottom foot opens South into pit center (gx + 2, gy - 1, gz + 2) and top landing connects North onto (gx + 2, gy, gz + 0)
			stair_cells[Vector3i(gx + 2, gy - 1, gz + 1)] = 180
			spec.has_safe_center_override = true
			spec.safe_center_world = DUNGEON_ORIGIN + Vector3(
				float(gx + 2) * CELL_SIZE,
				float(gy - 1) * CELL_SIZE,
				float(gz + 2) * CELL_SIZE
			)

		"OSSUARY_L_CATACOMB":
			# 4x4 footprint with top-right 2x2 quadrant (dx in 2..3, dz in 0..1) left un-carved -> 90-degree L-bend
			for dx: int in range(w):
				for dz: int in range(l):
					var is_uncarved_quadrant: bool = (dx >= 2 and dz <= 1)
					if is_uncarved_quadrant:
						continue
					for dy: int in range(h):
						occupied_cells[Vector3i(gx + dx, gy + dy, gz + dz)] = true
			spec.has_safe_center_override = true
			spec.safe_center_world = DUNGEON_ORIGIN + Vector3(
				float(gx + 1) * CELL_SIZE,
				float(gy) * CELL_SIZE,
				float(gz + 2) * CELL_SIZE
			)

		_:
			for dx: int in range(w):
				for dz: int in range(l):
					for dy: int in range(h):
						occupied_cells[Vector3i(gx + dx, gy + dy, gz + dz)] = true


func _populate_ossuary_v2_room(
	spec: RoomSpec,
	profile: Dictionary[String, Variant],
	arch_root: Node3D,
	props_root: Node3D,
	lights_root: Node3D,
	enemies_root: Node3D,
	portals_root: Node3D,
	return_dest: Vector3,
	light_energy_mult: float,
	extra_reliquary_chest: bool,
	rng: RandomNumberGenerator
) -> void:
	var r_idx: int = spec.room_index
	var b_id: int = int(profile.get("biome_id", 1))
	var geom_center: Vector3 = spec.geom_center_world(DUNGEON_ORIGIN)
	var safe_center: Vector3 = spec.center_world(DUNGEON_ORIGIN)
	var half_w: float = float(spec.width_cells) * CELL_SIZE * 0.5
	var half_l: float = float(spec.length_cells) * CELL_SIZE * 0.5
	var light_col: Color = profile["light_color"] as Color
	var fog_col: Color = profile["fog_color"] as Color
	var top_gy: int = spec.gy + spec.height_cells - 1
	var ceiling_chandelier_y: float = DUNGEON_ORIGIN.y + float(top_gy + 1) * CELL_SIZE - 1.15

	var chandelier_prefab: String = String(profile.get("chandelier", "res://scenes/prefabs/ossuary_variety/ossuary_bone_chandelier.tscn"))
	var monolith_prefab: String = String(profile.get("hero_monolith", "res://scenes/prefabs/ossuary_variety/ossuary_spine_reliquary_monolith.tscn"))
	var buttress_arch_prefab: String = String(profile.get("buttress_arch", "res://scenes/prefabs/ossuary_variety/ossuary_buttress_arch_4x4.tscn"))
	var divider_prefab: String = String(profile.get("divider", "res://scenes/prefabs/ossuary_variety/ossuary_burial_niche_divider_4x4.tscn"))

	# --------------------------------------------------------------------------
	# 1. Archetype-Specific Structural & Bespoke Biome Hero Kit Features
	# --------------------------------------------------------------------------
	match spec.archetype_name:
		"VISTA_HIGH_OVERLOOK_STAIRHALL":
			_spawn_prefab(
				arch_root,
				chandelier_prefab,
				"Room%d_OverlookChandelier" % r_idx,
				Vector3(geom_center.x, ceiling_chandelier_y, geom_center.z - 1.5)
			)

		"VISTA_CHASM_BRIDGE_CROSSING", "OSSUARY_CHASM_BRIDGE":
			# Bone piles & monolith in sunken gy-1 pit on East side (dx=2, dz=2), 8m clear of West stair (dx=0, dz=1)
			var pit_pos: Vector3 = DUNGEON_ORIGIN + Vector3(
				float(spec.gx + 2) * CELL_SIZE,
				float(spec.gy - 1) * CELL_SIZE,
				float(spec.gz + 2) * CELL_SIZE
			)
			var safe_pit_mono: Vector3 = _find_safe_prop_world_pos(spec, pit_pos, true, 4.0)
			_spawn_prefab(
				props_root,
				monolith_prefab,
				"Room%d_ChasmPitMonolith" % r_idx,
				safe_pit_mono
			)
			var bone_pos: Vector3 = _find_safe_prop_world_pos(spec, pit_pos + Vector3(0.0, 0.0, -4.0), false, 4.0)
			_spawn_prefab(
				props_root,
				"res://scenes/prefabs/architecture/clutter_rubble_bones_pile.tscn",
				"Room%d_ChasmBonePile" % r_idx,
				bone_pos
			)

		"VISTA_CRUCIFORM_BONE_BASILICA", "OSSUARY_CROSS_NAVE":
			# Hanging Chandelier in double-height crossing + 4 Crossing Pillars + Buttress Arch
			_spawn_prefab(
				arch_root,
				chandelier_prefab,
				"Room%d_BasilicaChandelier" % r_idx,
				Vector3(geom_center.x, ceiling_chandelier_y, geom_center.z)
			)
			_spawn_prefab(
				arch_root,
				buttress_arch_prefab,
				"Room%d_BasilicaNaveRib" % r_idx,
				geom_center + Vector3(0.0, 0.0, -4.0)
			)
			for corner_i: int in range(4):
				var sx: float = -3.6 if (corner_i % 2 == 0) else 3.6
				var sz: float = -3.6 if (corner_i < 2) else 3.6
				_spawn_prefab(
					arch_root,
					"res://scenes/prefabs/architecture/crypt_pillar.tscn",
					"Room%d_CrossPillar_%d" % [r_idx, corner_i],
					geom_center + Vector3(sx, 0.0, sz)
				)
				_spawn_prefab(
					arch_root,
					"res://scenes/prefabs/architecture/crypt_pillar.tscn",
					"Room%d_CrossUpperPillar_%d" % [r_idx, corner_i],
					geom_center + Vector3(sx, 4.0, sz)
				)

		"VISTA_CLOISTER_RING_WALK", "OSSUARY_CLOISTER_RING":
			# Buttress arches framing the West and East galleries around the solid 2x2 skull core
			var west_rib_pos: Vector3 = DUNGEON_ORIGIN + Vector3(
				float(spec.gx + 0) * CELL_SIZE,
				float(spec.gy) * CELL_SIZE,
				float(spec.gz + 1) * CELL_SIZE + 2.0
			)
			var east_rib_pos: Vector3 = DUNGEON_ORIGIN + Vector3(
				float(spec.gx + 3) * CELL_SIZE,
				float(spec.gy) * CELL_SIZE,
				float(spec.gz + 1) * CELL_SIZE + 2.0
			)
			_spawn_prefab(
				arch_root,
				buttress_arch_prefab,
				"Room%d_CloisterRibW" % r_idx,
				west_rib_pos
			)
			_spawn_prefab(
				arch_root,
				buttress_arch_prefab,
				"Room%d_CloisterRibE" % r_idx,
				east_rib_pos
			)

		"OSSUARY_SUNKEN_PIT_ARENA":
			# Towering Hero Monolith in pit center (gx + 2, gy - 1, gz + 2), 4.0m south of staircase at (gx + 2, gy - 1, gz + 1)
			var pit_center_cell: Vector3i = Vector3i(spec.gx + 2, spec.gy - 1, spec.gz + 2)
			var pit_center_pos: Vector3 = _cell_to_world(pit_center_cell)
			reserved_prop_cells[pit_center_cell] = "CENTERPIECE"
			_spawned_centerpiece_positions.append(pit_center_pos)
			_spawn_prefab(
				props_root,
				monolith_prefab,
				"Room%d_PitArenaMonolith" % r_idx,
				pit_center_pos
			)

		"OSSUARY_L_CATACOMB":
			# Asymmetric L-corner fortified with Divider half-walls and crates
			var div_pos: Vector3 = _find_safe_prop_world_pos(spec, safe_center + Vector3(-1.5, 0.0, 1.2), true, 4.0)
			_spawn_prefab(
				arch_root,
				divider_prefab,
				"Room%d_LCatacombDivider" % r_idx,
				div_pos,
				Vector3(0.0, 35.0, 0.0)
			)
			var crate_pos: Vector3 = _find_safe_prop_world_pos(spec, safe_center + Vector3(-3.0, 0.0, -2.0), false, 4.0)
			_spawn_prefab(
				props_root,
				"res://scenes/prefabs/architecture/clutter_wooden_crates_barrels.tscn",
				"Room%d_LCatacombCrates" % r_idx,
				crate_pos
			)

		"OSSUARY_PILLARED_GALLERY":
			# Elongated 3x5 processional gallery with repeating Buttress Arch vaulted ribs every 4m
			for rib_i: int in range(3):
				var rib_z: float = float(spec.gz + 1 + rib_i) * CELL_SIZE
				var rib_pos: Vector3 = DUNGEON_ORIGIN + Vector3(
					float(spec.gx + 1) * CELL_SIZE,
					float(spec.gy) * CELL_SIZE,
					rib_z
				)
				_spawn_prefab(
					arch_root,
					buttress_arch_prefab,
					"Room%d_GalleryRib_%d" % [r_idx, rib_i],
					rib_pos
				)

		"OSSUARY_MAZE_VAULT":
			# Partitioned Close-Quarters Crypt with staggered Dividers and Iron Gate cells
			var m_pos_a: Vector3 = _find_safe_prop_world_pos(spec, geom_center + Vector3(-1.8, 0.0, -1.6), true, 4.0)
			var m_pos_b: Vector3 = _find_safe_prop_world_pos(spec, geom_center + Vector3(1.8, 0.0, 1.6), true, 4.0)
			_spawn_prefab(
				arch_root,
				divider_prefab,
				"Room%d_MazeDividerA" % r_idx,
				m_pos_a
			)
			_spawn_prefab(
				arch_root,
				divider_prefab,
				"Room%d_MazeDividerB" % r_idx,
				m_pos_b
			)
			var gate_pos: Vector3 = _find_safe_prop_world_pos(spec, geom_center + Vector3(-3.2, 0.0, 2.0), false, 4.0)
			_spawn_prefab(
				arch_root,
				"res://scenes/prefabs/architecture/crypt_iron_gate_cell_4x4.tscn",
				"Room%d_MazeIronGate" % r_idx,
				gate_pos,
				Vector3(0.0, 90.0, 0.0)
			)

		"OSSUARY_SANCTUM_ROTUNDA":
			# Finale Boss & Extraction Chamber: Hanging Chandeliers, Twin Hero Monoliths, Chest & Dual Portals
			_spawn_prefab(
				arch_root,
				chandelier_prefab,
				"Room%d_RotundaChandelierMain" % r_idx,
				Vector3(geom_center.x, ceiling_chandelier_y, geom_center.z)
			)
			var mono_l: Vector3 = _find_safe_prop_world_pos(spec, geom_center + Vector3(-4.0, 0.0, 0.0), true, 4.0)
			var mono_r: Vector3 = _find_safe_prop_world_pos(spec, geom_center + Vector3(4.0, 0.0, 0.0), true, 4.0)
			_spawn_prefab(
				props_root,
				monolith_prefab,
				"Room%d_RotundaMonolithL" % r_idx,
				mono_l
			)
			_spawn_prefab(
				props_root,
				monolith_prefab,
				"Room%d_RotundaMonolithR" % r_idx,
				mono_r
			)
			_spawn_prefab(
				props_root,
				"res://scenes/prefabs/architecture/standing_iron_brazier.tscn",
				"Room%d_BossBrazierL" % r_idx,
				geom_center + Vector3(-3.6, 0.0, -2.6)
			)
			_spawn_prefab(
				props_root,
				"res://scenes/prefabs/architecture/standing_iron_brazier.tscn",
				"Room%d_BossBrazierR" % r_idx,
				geom_center + Vector3(3.6, 0.0, -2.6)
			)

			var deeper_portal_node: Node3D = _spawn_prefab(
				portals_root,
				"res://scenes/prefabs/hub/occult_rift_portal.tscn",
				"DeeperBiomeRiftPortal",
				geom_center + Vector3(-3.2, 0.0, -half_l + 2.4),
				Vector3(0.0, 15.0, 0.0)
			)
			if deeper_portal_node is OccultPortal:
				last_portal_positions.append(deeper_portal_node.position)
				(deeper_portal_node as OccultPortal).configure_portal(
					b_id,
					String(profile["title"]),
					light_col,
					false,
					return_dest,
					active_depth_tier + 1
				)

			var return_portal_node: Node3D = _spawn_prefab(
				portals_root,
				"res://scenes/prefabs/hub/occult_rift_portal.tscn",
				"SanctuaryReturnPortal",
				geom_center + Vector3(3.2, 0.0, -half_l + 2.4),
				Vector3(0.0, -15.0, 0.0)
			)
			if return_portal_node is OccultPortal:
				last_portal_positions.append(return_portal_node.position)
				(return_portal_node as OccultPortal).configure_portal(
					b_id,
					String(profile["title"]),
					Color(0.95, 0.85, 0.52, 1.0),
					true,
					return_dest,
					active_depth_tier
				)

	# --------------------------------------------------------------------------
	# 2. 5 Distinct Interior Prop-Layout Patterns per Room (Reservation-Aware)
	# --------------------------------------------------------------------------
	if not spec.is_entry and not spec.is_boss_sanctum:
		match spec.prop_pattern_id:
			1:
				# Pattern 1 (Ribbed Colonnade): buttress_arch + side standing_iron_brazier rows
				var arch_pos: Vector3 = _find_safe_prop_world_pos(spec, safe_center + Vector3(0.0, 0.0, -1.8), false, 4.0)
				_spawn_prefab(
					arch_root,
					buttress_arch_prefab,
					"Room%d_Pat1_ButtressArch" % r_idx,
					arch_pos
				)
				var b_l: Vector3 = _find_safe_prop_world_pos(spec, safe_center + Vector3(-4.0, 0.0, 0.0), false, 4.0)
				var b_r: Vector3 = _find_safe_prop_world_pos(spec, safe_center + Vector3(4.0, 0.0, 0.0), false, 4.0)
				_spawn_prefab(
					props_root,
					"res://scenes/prefabs/architecture/standing_iron_brazier.tscn",
					"Room%d_Pat1_BrazierL" % r_idx,
					b_l
				)
				_spawn_prefab(
					props_root,
					"res://scenes/prefabs/architecture/standing_iron_brazier.tscn",
					"Room%d_Pat1_BrazierR" % r_idx,
					b_r
				)
			2:
				# Pattern 2 (Tactical Niche Maze): Staggered divider + crates + bone pile
				var div2_pos: Vector3 = _find_safe_prop_world_pos(spec, safe_center + Vector3(4.0, 0.0, 0.0), true, 4.0)
				_spawn_prefab(
					arch_root,
					divider_prefab,
					"Room%d_Pat2_NicheDivider" % r_idx,
					div2_pos,
					Vector3(0.0, 90.0, 0.0)
				)
				var cr2_pos: Vector3 = _find_safe_prop_world_pos(spec, safe_center + Vector3(-4.0, 0.0, 0.0), false, 4.0)
				_spawn_prefab(
					props_root,
					"res://scenes/prefabs/architecture/clutter_wooden_crates_barrels.tscn",
					"Room%d_Pat2_Crates" % r_idx,
					cr2_pos
				)
				var bn2_pos: Vector3 = _find_safe_prop_world_pos(spec, safe_center + Vector3(0.0, 0.0, 4.0), false, 4.0)
				_spawn_prefab(
					props_root,
					"res://scenes/prefabs/architecture/clutter_rubble_bones_pile.tscn",
					"Room%d_Pat2_Bones" % r_idx,
					bn2_pos
				)
			3:
				# Pattern 3 (Hero Monolith Shrine): monolith_prefab + 4 candle clusters + hanging cage
				if spec.archetype_name != "OSSUARY_SUNKEN_PIT_ARENA" and spec.archetype_name != "OSSUARY_CHASM_BRIDGE":
					var mono3_pos: Vector3 = _find_safe_prop_world_pos(spec, safe_center + Vector3(-4.0, 0.0, 0.0), true, 4.0)
					_spawn_prefab(
						props_root,
						monolith_prefab,
						"Room%d_Pat3_SpineMonolith" % r_idx,
						mono3_pos
					)
					for c_i: int in range(4):
						var c_ang: float = float(c_i) * (TAU * 0.25)
						_spawn_prefab(
							props_root,
							"res://scenes/prefabs/architecture/clutter_melted_candle_cluster.tscn",
							"Room%d_Pat3_Candles_%d" % [r_idx, c_i],
							mono3_pos + Vector3(cos(c_ang) * 1.35, 0.0, sin(c_ang) * 1.35)
						)
				_spawn_prefab(
					props_root,
					"res://scenes/prefabs/architecture/crypt_hanging_cage.tscn",
					"Room%d_Pat3_HangingCage" % r_idx,
					Vector3(safe_center.x + 2.0, ceiling_chandelier_y - 0.8, safe_center.z)
				)
			4:
				# Pattern 4 (Chandelier Vault): Overhead chandelier_prefab + perimeter crypt_sarcophagus_ornate tombs
				_spawn_prefab(
					arch_root,
					chandelier_prefab,
					"Room%d_Pat4_Chandelier" % r_idx,
					Vector3(geom_center.x, ceiling_chandelier_y, geom_center.z)
				)
				var sarc_a: Vector3 = _find_safe_prop_world_pos(spec, safe_center + Vector3(-4.0, 0.0, 0.0), true, 4.0)
				_spawn_prefab(
					props_root,
					"res://scenes/prefabs/architecture/crypt_sarcophagus_ornate.tscn",
					"Room%d_Pat4_SarcophagusA" % r_idx,
					sarc_a,
					Vector3(0.0, 90.0, 0.0)
				)
				var sarc_b: Vector3 = _find_safe_prop_world_pos(spec, safe_center + Vector3(4.0, 0.0, 0.0), true, 4.0)
				if sarc_b.distance_to(sarc_a) > 2.5:
					_spawn_prefab(
						props_root,
						"res://scenes/prefabs/architecture/crypt_sarcophagus_ornate.tscn",
						"Room%d_Pat4_SarcophagusB" % r_idx,
						sarc_b,
						Vector3(0.0, -90.0, 0.0)
					)
			_:
				# Pattern 5 (Asymmetric Plunder Alcove): Corner Reliquary Chest guarded by bone barricades & ceiling chains
				var reward_sc: float = 1.0 + float(maxi(1, active_depth_tier) - 1) * 0.30
				var chest_pos: Vector3 = _find_safe_prop_world_pos(spec, safe_center + Vector3(-4.0, 0.0, -4.0), true, 4.0)
				var p_chest: Node3D = _spawn_prefab(
					props_root,
					"res://scenes/prefabs/props/prop_gothic_reliquary_chest.tscn",
					"Room%d_Pat5_PlunderChest" % r_idx,
					chest_pos,
					Vector3(0.0, 35.0, 0.0)
				)
				if p_chest is ReliquaryChest:
					last_chest_positions.append(p_chest.position)
					var rc: ReliquaryChest = p_chest as ReliquaryChest
					rc.guaranteed_relic_id = b_id
					rc.chest_biome_id = b_id
					rc.is_completion_chest = false
					rc.reward_scale = reward_sc
				var bar_pos: Vector3 = _find_safe_prop_world_pos(spec, chest_pos + Vector3(1.4, 0.0, 1.2), false, 4.0)
				_spawn_prefab(
					props_root,
					"res://scenes/prefabs/architecture/clutter_rubble_bones_pile.tscn",
					"Room%d_Pat5_BoneBarricade" % r_idx,
					bar_pos
				)
				_spawn_prefab(
					props_root,
					"res://scenes/prefabs/architecture/clutter_ceiling_chains_roots.tscn",
					"Room%d_Pat5_CeilingChains" % r_idx,
					Vector3(chest_pos.x, ceiling_chandelier_y + 0.25, chest_pos.z)
				)

	# Stygian Blood-Catacombs Mutator extra chains & extra Reliquary Chest
	if extra_reliquary_chest and r_idx == 2:
		var bonus_pos: Vector3 = _find_safe_prop_world_pos(spec, safe_center + Vector3(4.0, 0.0, 0.0), true, 4.0)
		var bonus_chest: Node3D = _spawn_prefab(
			props_root,
			"res://scenes/prefabs/props/prop_gothic_reliquary_chest.tscn",
			"Room%d_MutatorBonusChest" % r_idx,
			bonus_pos
		)
		if bonus_chest is ReliquaryChest:
			last_chest_positions.append(bonus_chest.position)
			var b_bonus: ReliquaryChest = bonus_chest as ReliquaryChest
			b_bonus.guaranteed_relic_id = b_id
			b_bonus.chest_biome_id = b_id
			b_bonus.is_completion_chest = false

	# Guaranteed Boss Sanctum Grand Completion Reliquary Chest
	if spec.is_boss_sanctum:
		var boss_chest_pos: Vector3 = _find_safe_prop_world_pos(spec, geom_center + Vector3(0.0, 0.0, -4.0), true, 4.0)
		var boss_chest: Node3D = _spawn_prefab(
			props_root,
			"res://scenes/prefabs/props/prop_gothic_reliquary_chest.tscn",
			"Room%d_ReliquaryChest" % r_idx,
			boss_chest_pos,
			Vector3.ZERO,
			Vector3(1.35, 1.35, 1.35)
		)
		if boss_chest is ReliquaryChest:
			last_chest_positions.append(boss_chest.position)
			var b_rc: ReliquaryChest = boss_chest as ReliquaryChest
			b_rc.guaranteed_relic_id = b_id
			b_rc.chest_biome_id = b_id
			b_rc.is_completion_chest = true
			b_rc.reward_scale = 1.0 + float(maxi(1, active_depth_tier) - 1) * 0.30

	# --------------------------------------------------------------------------
	# 3. Mood-Mutator OmniLight3D + Local FogVolume + DustMotesParticles
	# --------------------------------------------------------------------------
	var omni: OmniLight3D = OmniLight3D.new()
	omni.name = "Room%d_BiomeLight" % r_idx
	omni.position = safe_center + Vector3(0.0, 3.0, 0.0)
	omni.light_color = light_col
	omni.light_energy = (2.15 if spec.is_boss_sanctum else 1.65) * light_energy_mult
	omni.omni_range = 14.0
	omni.omni_attenuation = 1.35
	omni.shadow_enabled = false
	omni.distance_fade_enabled = true
	omni.distance_fade_begin = 22.0
	omni.distance_fade_shadow = 12.0
	omni.distance_fade_length = 6.0
	lights_root.add_child(omni)

	var fog_vol: FogVolume = FogVolume.new()
	fog_vol.name = "Room%d_BiomeFogVolume" % r_idx
	fog_vol.position = geom_center + Vector3(0.0, 1.8, 0.0)
	fog_vol.size = Vector3(half_w * 1.9, float(spec.height_cells) * 3.6, half_l * 1.9)
	var fog_mat: FogMaterial = FogMaterial.new()
	fog_mat.density = float(profile["fog_density"])
	fog_mat.albedo = fog_col
	fog_mat.emission = Color(light_col.r * 0.22, light_col.g * 0.22, light_col.b * 0.22, 1.0)
	fog_vol.material = fog_mat
	lights_root.add_child(fog_vol)

	var dust: GPUParticles3D = _create_biome_dust_motes(
		"Room%d_DustMotesParticles" % r_idx,
		safe_center + Vector3(0.0, 2.0, 0.0),
		light_col
	)
	lights_root.add_child(dust)

	# --------------------------------------------------------------------------
	# 4. Active Biome Combat Enemies, 4 Ranged Crossfire Variants & Anointed Champions
	# --------------------------------------------------------------------------
	if not spec.is_entry:
		# Collect all unreserved walkable floor cells in this room >= 3.8m from any stair or centerpiece
		var valid_enemy_cells: Array[Vector3i] = []
		for dy_e: int in [-1, 0, 1]:
			for dx_e: int in range(spec.width_cells):
				for dz_e: int in range(spec.length_cells):
					var c_cell: Vector3i = Vector3i(spec.gx + dx_e, spec.gy + dy_e, spec.gz + dz_e)
					if not _is_walkable_floor_cell(c_cell, last_occupied_cells, last_bridge_cells, last_balcony_floor_cells, last_stair_cells):
						continue
					if reserved_prop_cells.has(c_cell):
						continue
					var c_pos: Vector3 = _cell_to_world(c_cell)
					if _is_near_any_stair_or_centerpiece(c_pos, 3.8, 3.8):
						continue
					valid_enemy_cells.append(c_cell)

		var enemy_count: int = 3 if spec.is_boss_sanctum else rng.randi_range(2, 4)
		var ep_a: String = String(profile["enemy_primary"])
		var ep_b: String = String(profile["enemy_secondary"])
		var ranged_arch: String = String(profile.get("ranged_archetype", "RANGED_BONE_ARBALEST"))
		var champ_chance: float = clampf(float(b_id - 1) * 0.07, 0.05, 0.50)

		for e_i: int in range(enemy_count):
			var angle: float = float(e_i) * (TAU / float(enemy_count)) + 0.45
			var e_pos: Vector3 = safe_center + Vector3(cos(angle) * 3.8, 0.0, sin(angle) * 3.8)
			if not valid_enemy_cells.is_empty():
				var pick_idx: int = (e_i * 3) % valid_enemy_cells.size()
				var chosen_cell: Vector3i = valid_enemy_cells[pick_idx]
				e_pos = _cell_to_world(chosen_cell) + Vector3(cos(angle) * 0.45, 0.0, sin(angle) * 0.45)
			var use_signature: bool = (e_i == 0) or (rng.randf() < 0.70)
			var e_path: String = ep_a if use_signature else ep_b
			var spawned_enemy: Node3D = _spawn_prefab(
				enemies_root,
				e_path,
				"Room%d_Enemy_%d" % [r_idx, e_i],
				e_pos,
				Vector3(0.0, rad_to_deg(-angle), 0.0)
			)
			if spawned_enemy is OccultEnemyAI:
				var ai_enemy: OccultEnemyAI = spawned_enemy as OccultEnemyAI
				ai_enemy.is_passive_dummy = false
				if e_i == enemy_count - 1 and enemy_count >= 2:
					ai_enemy.combat_archetype = ranged_arch
					ai_enemy._cached_base_stats = false
				ai_enemy.apply_depth_scaling(active_depth_tier, b_id)
				var is_champ: bool = rng.randf() < champ_chance
				ai_enemy.configure_for_biome_tier(b_id, is_champ)
			elif spawned_enemy is TestDummyEnemy:
				var td_enemy: TestDummyEnemy = spawned_enemy as TestDummyEnemy
				td_enemy.apply_depth_scaling(active_depth_tier, b_id)

		if spec.is_boss_sanctum:
			var champ_pos: Vector3 = geom_center + Vector3(0.0, 0.0, 4.0)
			if not valid_enemy_cells.is_empty():
				champ_pos = _cell_to_world(valid_enemy_cells[valid_enemy_cells.size() - 1])
			var champ_node: Node3D = _spawn_prefab(
				enemies_root,
				ep_a,
				"Room%d_EliteBiomeChampion" % r_idx,
				champ_pos,
				Vector3.ZERO,
				Vector3(1.22, 1.22, 1.22)
			)
			if champ_node is OccultEnemyAI:
				var champ_ai: OccultEnemyAI = champ_node as OccultEnemyAI
				champ_ai.is_passive_dummy = false
				champ_ai.apply_depth_scaling(active_depth_tier, b_id)
				champ_ai.configure_for_biome_tier(b_id, true)
			elif champ_node is TestDummyEnemy:
				var champ_td: TestDummyEnemy = champ_node as TestDummyEnemy
				champ_td.apply_depth_scaling(active_depth_tier, b_id)
				champ_td.max_health = roundf(champ_td.max_health * 2.2)
				champ_td.current_health = champ_td.max_health
				champ_td.guaranteed_relic_drop = true
