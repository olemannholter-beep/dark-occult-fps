class_name GothicMapSystem
extends Control

const STATE_HIDDEN: int = 0
const STATE_SHROUDED_EDGE: int = 1
const STATE_DISCOVERED: int = 2

const CELL_SIZE: float = 4.0
const DUNGEON_ORIGIN: Vector3 = Vector3(0.0, -500.0, 0.0)

const MINIMAP_SIZE: Vector2 = Vector2(190.0, 190.0)
const MINIMAP_MARGIN: Vector2 = Vector2(24.0, 24.0)
const MINIMAP_SCALE: float = 7.5

const FULL_MAP_SIZE: Vector2 = Vector2(1100.0, 760.0)
const SIDEBAR_WIDTH: float = 290.0

var discovered_cells: Dictionary[Vector3i, int] = {}
var shrouded_adjacent_cells: Dictionary[Vector3i, int] = {}
var discovered_room_indices: Dictionary[int, bool] = {}

var is_full_map_open: bool = false
var map_zoom: float = 8.5
var map_pan_offset: Vector2 = Vector2.ZERO

var _player: Node3D = null
var _dungeon_gen: ProceduralDungeonGenerator = null
var _discovery_timer: float = 0.0
var _pulse_time: float = 0.0
var _is_dragging_map: bool = false
var _last_player_pos: Vector3 = Vector3(99999.0, 99999.0, 99999.0)

var _hub_occupied_cells: Dictionary[Vector3i, bool] = {}
var _hub_stair_cells: Dictionary[Vector3i, int] = {}
var _hub_portal_positions: Array[Vector3] = []
var _hub_chest_positions: Array[Vector3] = []
var _hub_discovered_cells: Dictionary[Vector3i, int] = {}
var _hub_shrouded_cells: Dictionary[Vector3i, int] = {}


func _ready() -> void:
	name = "GothicMapSystem"
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build_static_hub_map_cells()
	_resolve_references()
	if _player != null:
		discover_at_world_position(_get_node_world_pos(_player))


func _get_node_world_pos(node: Node3D) -> Vector3:
	if node == null or not is_instance_valid(node):
		return Vector3.ZERO
	return node.global_position if node.is_inside_tree() else node.position


func _get_top_ancestor() -> Node:
	var cur: Node = self
	while cur.get_parent() != null:
		cur = cur.get_parent()
	return cur


func _build_static_hub_map_cells() -> void:
	_hub_occupied_cells.clear()
	_hub_stair_cells.clear()
	_hub_portal_positions.clear()
	_hub_chest_positions.clear()

	# 1. Town Valley Road (Z from +28m down to +8m, X in [-4m..+4m], gy = 0)
	for gz: int in range(2, 8):
		for gx: int in range(-1, 2):
			_hub_occupied_cells[Vector3i(gx, 0, gz)] = true

	# 2. Sanctuary Church Nave Workshop (Z from +8m to -16m, X in [-4m..+4m], gy = 0)
	for gz: int in range(-4, 3):
		for gx: int in range(-1, 2):
			_hub_occupied_cells[Vector3i(gx, 0, gz)] = true

	# Church basement descending stairs (gx = 0, gz = -5)
	_hub_occupied_cells[Vector3i(0, 0, -5)] = true
	_hub_stair_cells[Vector3i(0, 0, -5)] = 0

	# 3. Chamber 1 — Antechamber of Bones (X in [-4..+4], Z in [-24..-32], gy = 0)
	for gz: int in [-6, -7, -8]:
		for gx: int in [-1, 0, 1]:
			_hub_occupied_cells[Vector3i(gx, 0, gz)] = true

	# 4. Chamber 2 — Hall of Sarcophagi (West wing: gx in [-3..-6], gz in [-6..-9], gy = 0)
	_hub_occupied_cells[Vector3i(-2, 0, -7)] = true
	for gz: int in [-6, -7, -8, -9]:
		for gx: int in [-6, -5, -4, -3]:
			_hub_occupied_cells[Vector3i(gx, 0, gz)] = true

	# 5. Chamber 3 — Forbidden Library (North-West: gx in [-5..-3], gz in [-11..-14], gy = 0)
	_hub_occupied_cells[Vector3i(-4, 0, -10)] = true
	for gz: int in [-14, -13, -12, -11]:
		for gx: int in [-5, -4, -3]:
			_hub_occupied_cells[Vector3i(gx, 0, gz)] = true

	# 6. Chamber 4 — Inquisitor's Gaol (East wing: gx in [3..6], gz in [-6..-8], gy = 0)
	_hub_occupied_cells[Vector3i(2, 0, -7)] = true
	for gz: int in [-8, -7, -6]:
		for gx: int in [3, 4, 5, 6]:
			_hub_occupied_cells[Vector3i(gx, 0, gz)] = true

	# 7. Chamber 5 — Alchemical Plague Cistern (South-East lower: gx in [3..6], gz in [-10..-13], gy = -1)
	_hub_occupied_cells[Vector3i(4, -1, -9)] = true
	_hub_stair_cells[Vector3i(4, -1, -9)] = 0
	for gz: int in [-13, -12, -11, -10]:
		for gx: int in [3, 4, 5, 6]:
			_hub_occupied_cells[Vector3i(gx, -1, gz)] = true

	# 8. Chamber 6 — Weeping Saint Cenotaph (Center lower: gx in [-1..1], gz in [-10..-13], gy = -1)
	_hub_occupied_cells[Vector3i(0, -1, -9)] = true
	_hub_stair_cells[Vector3i(0, -1, -9)] = 0
	for gz: int in [-13, -12, -11, -10]:
		for gx: int in [-1, 0, 1]:
			_hub_occupied_cells[Vector3i(gx, -1, gz)] = true

	# 9. Chamber 7 — Sunken Bell Vault (Deep West: gx in [-6..-3], gz in [-16..-19], gy = -2)
	_hub_occupied_cells[Vector3i(-2, -1, -12)] = true
	_hub_occupied_cells[Vector3i(-3, -1, -12)] = true
	_hub_occupied_cells[Vector3i(-3, -1, -13)] = true
	_hub_occupied_cells[Vector3i(-3, -1, -14)] = true
	_hub_occupied_cells[Vector3i(-3, -2, -15)] = true
	_hub_stair_cells[Vector3i(-3, -2, -15)] = 0
	for gz: int in [-19, -18, -17, -16]:
		for gx: int in [-6, -5, -4, -3]:
			_hub_occupied_cells[Vector3i(gx, -2, gz)] = true

	# 10. Chamber 8 — Abyssal Blood Sanctum (Deep Center: gx in [-2..2], gz in [-16..-20], gy = -2)
	_hub_occupied_cells[Vector3i(0, -2, -14)] = true
	_hub_stair_cells[Vector3i(0, -2, -14)] = 0
	_hub_occupied_cells[Vector3i(0, -2, -15)] = true
	for gz: int in [-20, -19, -18, -17, -16]:
		for gx: int in [-2, -1, 0, 1, 2]:
			_hub_occupied_cells[Vector3i(gx, -2, gz)] = true

	_hub_portal_positions = [
		Vector3(4.1, 0.0, -24.2),
		Vector3(-24.2, 0.0, -30.0),
		Vector3(-16.0, 0.0, -56.6),
		Vector3(24.2, 0.0, -28.0),
		Vector3(18.0, -4.0, -52.4),
		Vector3(0.0, -4.0, -50.8),
		Vector3(-18.0, -8.0, -76.2),
		Vector3(0.0, -8.0, -80.2)
	]


func _resolve_references() -> void:
	var top_root: Node = _get_top_ancestor()
	if _player == null or not is_instance_valid(_player):
		if is_inside_tree() and get_tree() != null:
			var p_node: Node = get_tree().get_first_node_in_group("player")
			if p_node is Node3D:
				_player = p_node as Node3D
		if _player == null and get_parent() != null and get_parent().get_parent() is Node3D:
			var cand: Node3D = get_parent().get_parent() as Node3D
			if cand is CharacterBody3D or cand.name.contains("Player"):
				_player = cand
		if _player == null and top_root != null:
			var found_p: Node = top_root.find_child("Player", true, false)
			if found_p is Node3D:
				_player = found_p as Node3D

	if _dungeon_gen == null or not is_instance_valid(_dungeon_gen):
		if is_inside_tree() and get_tree() != null and get_tree().root != null:
			var found_gen: Node = get_tree().root.find_child("ProceduralExpeditionRoot", true, false)
			if found_gen is ProceduralDungeonGenerator:
				_dungeon_gen = found_gen as ProceduralDungeonGenerator
		if _dungeon_gen == null and top_root != null:
			var found_gen2: Node = top_root.find_child("ProceduralExpeditionRoot", true, false)
			if found_gen2 is ProceduralDungeonGenerator:
				_dungeon_gen = found_gen2 as ProceduralDungeonGenerator


func set_player_and_generator(player_node: Node3D, gen_node: ProceduralDungeonGenerator) -> void:
	if player_node != null:
		_player = player_node
	if gen_node != null:
		_dungeon_gen = gen_node


func reset_fog_of_war_for_new_dungeon(spawn_world_pos: Vector3 = Vector3.ZERO) -> void:
	_resolve_references()
	discovered_cells.clear()
	shrouded_adjacent_cells.clear()
	discovered_room_indices.clear()
	map_pan_offset = Vector2.ZERO

	var start_pos: Vector3 = spawn_world_pos
	if start_pos == Vector3.ZERO:
		if _dungeon_gen != null and not _dungeon_gen.generated_room_centers.is_empty():
			start_pos = _dungeon_gen.generated_room_centers[0]
		elif _player != null and is_instance_valid(_player):
			start_pos = _get_node_world_pos(_player)
		else:
			start_pos = DUNGEON_ORIGIN

	discover_at_world_position(start_pos)
	queue_redraw()


func update_fog_of_war() -> void:
	_resolve_references()
	if _player != null and is_instance_valid(_player):
		discover_at_world_position(_get_node_world_pos(_player))


func discover_at_world_position(world_pos: Vector3) -> void:
	_resolve_references()
	_last_player_pos = world_pos

	var in_dungeon: bool = (world_pos.y <= -100.0)
	if not in_dungeon and _dungeon_gen != null and _dungeon_gen.active_room_count > 0 and discovered_cells.is_empty():
		# If called right as dungeon generated with a dungeon coordinate
		if world_pos.y <= -100.0:
			in_dungeon = true

	if in_dungeon and _dungeon_gen != null:
		var map_data: Dictionary = _dungeon_gen.get_dungeon_map_data()
		var occupied: Dictionary = map_data.get("occupied_cells", {}) as Dictionary
		var room_cells_map: Dictionary = map_data.get("room_cells_by_index", {}) as Dictionary
		if occupied.is_empty():
			return

		var p_cell: Vector3i = _world_to_dungeon_cell(world_pos)

		# 1. Reveal cells within 14.0m (<= 3.5 grid cells) on same or adjacent vertical elevation
		for cell_var: Variant in occupied.keys():
			if not (cell_var is Vector3i):
				continue
			var cell: Vector3i = cell_var as Vector3i
			if absi(cell.y - p_cell.y) <= 1:
				var dx_m: float = float(cell.x - p_cell.x) * CELL_SIZE
				var dz_m: float = float(cell.z - p_cell.z) * CELL_SIZE
				if sqrt(dx_m * dx_m + dz_m * dz_m) <= 14.0:
					discovered_cells[cell] = STATE_DISCOVERED

		# 2. Flood-fill any room whose threshold the player has entered
		for r_idx_var: Variant in room_cells_map.keys():
			var r_idx: int = int(r_idx_var)
			var r_cells: Array = room_cells_map[r_idx_var] as Array
			var entered_room: bool = false
			for rc_var: Variant in r_cells:
				if rc_var is Vector3i:
					var rc: Vector3i = rc_var as Vector3i
					if rc == p_cell or (absi(rc.x - p_cell.x) <= 1 and absi(rc.z - p_cell.z) <= 1 and absi(rc.y - p_cell.y) <= 1):
						entered_room = true
						break
			if entered_room:
				discovered_room_indices[r_idx] = true
				for rc_var2: Variant in r_cells:
					if rc_var2 is Vector3i:
						discovered_cells[rc_var2 as Vector3i] = STATE_DISCOVERED

		# Guarantee starting room (Room 0) is charted if discovered_cells is still empty
		if discovered_cells.is_empty() and room_cells_map.has(0):
			discovered_room_indices[0] = true
			var r0_cells: Array = room_cells_map[0] as Array
			for rc0_var: Variant in r0_cells:
				if rc0_var is Vector3i:
					discovered_cells[rc0_var as Vector3i] = STATE_DISCOVERED

		# 3. Rebuild shrouded frontier edge (1-2 cells past discovered doorways/corridors)
		shrouded_adjacent_cells.clear()
		var dirs: Array[Vector3i] = [
			Vector3i(1, 0, 0),
			Vector3i(-1, 0, 0),
			Vector3i(0, 0, 1),
			Vector3i(0, 0, -1),
			Vector3i(0, 1, 0),
			Vector3i(0, -1, 0)
		]
		for d_cell: Vector3i in discovered_cells.keys():
			for dir: Vector3i in dirs:
				for step: int in [1, 2]:
					var n_cell: Vector3i = d_cell + dir * step
					if not occupied.has(n_cell):
						break
					if not discovered_cells.has(n_cell):
						shrouded_adjacent_cells[n_cell] = STATE_SHROUDED_EDGE
	else:
		# Hub Safe-Harbour discovery
		var h_cell: Vector3i = _world_to_hub_cell(world_pos)
		for cell_var: Variant in _hub_occupied_cells.keys():
			if not (cell_var is Vector3i):
				continue
			var cell: Vector3i = cell_var as Vector3i
			if absi(cell.y - h_cell.y) <= 1:
				var dx_m: float = float(cell.x - h_cell.x) * CELL_SIZE
				var dz_m: float = float(cell.z - h_cell.z) * CELL_SIZE
				if sqrt(dx_m * dx_m + dz_m * dz_m) <= 18.0:
					_hub_discovered_cells[cell] = STATE_DISCOVERED

		_hub_shrouded_cells.clear()
		var h_dirs: Array[Vector3i] = [
			Vector3i(1, 0, 0),
			Vector3i(-1, 0, 0),
			Vector3i(0, 0, 1),
			Vector3i(0, 0, -1)
		]
		for d_cell: Vector3i in _hub_discovered_cells.keys():
			for dir: Vector3i in h_dirs:
				for step: int in [1, 2]:
					var n_cell: Vector3i = d_cell + dir * step
					if not _hub_occupied_cells.has(n_cell):
						break
					if not _hub_discovered_cells.has(n_cell):
						_hub_shrouded_cells[n_cell] = STATE_SHROUDED_EDGE


func _world_to_dungeon_cell(pos: Vector3) -> Vector3i:
	var rx: int = roundi((pos.x - DUNGEON_ORIGIN.x) / CELL_SIZE)
	var ry: int = floori((pos.y - DUNGEON_ORIGIN.y + 0.5) / CELL_SIZE)
	var rz: int = roundi((pos.z - DUNGEON_ORIGIN.z) / CELL_SIZE)
	return Vector3i(rx, ry, rz)


func _world_to_hub_cell(pos: Vector3) -> Vector3i:
	var rx: int = roundi(pos.x / CELL_SIZE)
	var ry: int = floori((pos.y + 0.5) / CELL_SIZE)
	var rz: int = roundi(pos.z / CELL_SIZE)
	return Vector3i(rx, ry, rz)


func toggle_full_map() -> void:
	set_full_map_open(not is_full_map_open)


func set_full_map_open(open: bool) -> void:
	is_full_map_open = open
	if is_full_map_open:
		map_pan_offset = Vector2.ZERO
		mouse_filter = Control.MOUSE_FILTER_STOP
		update_fog_of_war()
	else:
		_is_dragging_map = false
		mouse_filter = Control.MOUSE_FILTER_IGNORE
	queue_redraw()


func recenter_on_hunter() -> void:
	map_pan_offset = Vector2.ZERO
	queue_redraw()


func get_charted_room_count() -> int:
	if _dungeon_gen != null and _dungeon_gen.active_room_count > 0:
		return maxi(1, discovered_room_indices.size())
	return 1


func get_total_room_count() -> int:
	if _dungeon_gen != null and _dungeon_gen.active_room_count > 0:
		return _dungeon_gen.active_room_count
	return 9


func get_exploration_percentage() -> float:
	if _dungeon_gen != null and not _dungeon_gen.last_occupied_cells.is_empty():
		var total_c: int = maxi(1, _dungeon_gen.last_occupied_cells.size())
		return clampf((float(discovered_cells.size()) / float(total_c)) * 100.0, 0.0, 100.0)
	var total_h: int = maxi(1, _hub_occupied_cells.size())
	return clampf((float(_hub_discovered_cells.size()) / float(total_h)) * 100.0, 0.0, 100.0)


func _input(event: InputEvent) -> void:
	if event.is_action_pressed("toggle_map"):
		toggle_full_map()
		get_viewport().set_input_as_handled()
		return

	if event is InputEventKey:
		var k: InputEventKey = event as InputEventKey
		if k.pressed and not k.echo:
			if k.keycode == KEY_M or k.physical_keycode == KEY_M or k.keycode == KEY_TAB or k.physical_keycode == KEY_TAB:
				toggle_full_map()
				get_viewport().set_input_as_handled()
				return
			if is_full_map_open:
				if k.keycode == KEY_SPACE or k.physical_keycode == KEY_SPACE:
					recenter_on_hunter()
					get_viewport().set_input_as_handled()
					return
				elif k.keycode == KEY_EQUAL or k.keycode == KEY_KP_ADD:
					map_zoom = clampf(map_zoom + 1.5, 4.0, 18.0)
					queue_redraw()
					get_viewport().set_input_as_handled()
					return
				elif k.keycode == KEY_MINUS or k.keycode == KEY_KP_SUBTRACT:
					map_zoom = clampf(map_zoom - 1.5, 4.0, 18.0)
					queue_redraw()
					get_viewport().set_input_as_handled()
					return

	if is_full_map_open:
		if event is InputEventMouseButton:
			var mb: InputEventMouseButton = event as InputEventMouseButton
			if mb.button_index == MOUSE_BUTTON_WHEEL_UP and mb.pressed:
				map_zoom = clampf(map_zoom + 1.25, 4.0, 18.0)
				queue_redraw()
			elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN and mb.pressed:
				map_zoom = clampf(map_zoom - 1.25, 4.0, 18.0)
				queue_redraw()
			elif mb.button_index == MOUSE_BUTTON_LEFT:
				_is_dragging_map = mb.pressed
		elif event is InputEventMouseMotion and _is_dragging_map:
			var mm: InputEventMouseMotion = event as InputEventMouseMotion
			map_pan_offset += mm.relative
			queue_redraw()


func _process(delta: float) -> void:
	_pulse_time += delta
	_discovery_timer += delta

	if _player == null or not is_instance_valid(_player):
		_resolve_references()

	if _player != null and is_instance_valid(_player):
		var cur_p_pos: Vector3 = _get_node_world_pos(_player)
		var moved_dist: float = cur_p_pos.distance_to(_last_player_pos)
		if _discovery_timer >= 0.15 or moved_dist >= 1.5:
			_discovery_timer = 0.0
			discover_at_world_position(cur_p_pos)

	if is_full_map_open:
		var pan_dir: Vector2 = Vector2.ZERO
		if Input.is_key_pressed(KEY_LEFT) or Input.is_key_pressed(KEY_A):
			pan_dir.x += 1.0
		if Input.is_key_pressed(KEY_RIGHT) or Input.is_key_pressed(KEY_D):
			pan_dir.x -= 1.0
		if Input.is_key_pressed(KEY_UP) or Input.is_key_pressed(KEY_W):
			pan_dir.y += 1.0
		if Input.is_key_pressed(KEY_DOWN) or Input.is_key_pressed(KEY_S):
			pan_dir.y -= 1.0
		if pan_dir.length_squared() > 0.01:
			map_pan_offset += pan_dir.normalized() * 320.0 * delta

	queue_redraw()


func _draw() -> void:
	var vp_size: Vector2 = get_viewport_rect().size
	if vp_size.x < 100.0 or vp_size.y < 100.0:
		vp_size = Vector2(1920.0, 1080.0)

	_draw_corner_minimap(vp_size)
	if is_full_map_open:
		_draw_full_screen_cartography_map(vp_size)


func _draw_corner_minimap(vp_size: Vector2) -> void:
	var rect_pos: Vector2 = Vector2(vp_size.x - MINIMAP_SIZE.x - MINIMAP_MARGIN.x, MINIMAP_MARGIN.y)
	var mm_rect: Rect2 = Rect2(rect_pos, MINIMAP_SIZE)
	var center: Vector2 = mm_rect.position + mm_rect.size * 0.5

	# 1. Dark Obsidian Astrolabe Backdrop + Chamfered Brass Bezel
	draw_rect(mm_rect.grow(4.0), Color(0.08, 0.06, 0.05, 0.94), true)
	draw_rect(mm_rect, Color(0.03, 0.02, 0.04, 0.90), true)

	# Astrolabe Circular Radar Ring & Subtle Grid Lines
	draw_arc(center, 84.0, 0.0, TAU, 48, Color(0.45, 0.34, 0.18, 0.28), 1.2)
	draw_arc(center, 52.0, 0.0, TAU, 36, Color(0.45, 0.34, 0.18, 0.18), 1.0)
	draw_line(Vector2(mm_rect.position.x + 8.0, center.y), Vector2(mm_rect.end.x - 8.0, center.y), Color(0.45, 0.34, 0.18, 0.16), 1.0)
	draw_line(Vector2(center.x, mm_rect.position.y + 8.0), Vector2(center.x, mm_rect.end.y - 8.0), Color(0.45, 0.34, 0.18, 0.16), 1.0)

	# 2. Render Fog-of-War Voxel Cells & Icons inside Minimap Bounds
	var inner_clip: Rect2 = mm_rect.grow(-6.0)
	_draw_map_world_projection(inner_clip, center, MINIMAP_SCALE, false)

	# 3. Ornate Double-Ringed Tarnished Brass Frame & Corner Rivets
	draw_rect(mm_rect.grow(4.0), Color(0.72, 0.56, 0.28, 0.94), false, 2.0)
	draw_rect(mm_rect, Color(0.52, 0.38, 0.20, 0.88), false, 1.5)

	var corners: Array[Vector2] = [
		mm_rect.position + Vector2(5.0, 5.0),
		Vector2(mm_rect.end.x - 5.0, mm_rect.position.y + 5.0),
		Vector2(mm_rect.position.x + 5.0, mm_rect.end.y - 5.0),
		mm_rect.end - Vector2(5.0, 5.0)
	]
	for c_pt: Vector2 in corners:
		draw_circle(c_pt, 3.0, Color(0.85, 0.68, 0.34, 0.96))
		draw_circle(c_pt, 1.4, Color(0.22, 0.16, 0.08, 0.95))

	# 4. Cardinal Compass Spikes & Letters (N, S, E, W)
	var font: Font = ThemeDB.fallback_font
	if font != null:
		draw_string(font, Vector2(center.x - 5.0, mm_rect.position.y + 14.0), "N", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(1.0, 0.84, 0.38, 0.96))
		draw_string(font, Vector2(center.x - 4.0, mm_rect.end.y - 5.0), "S", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(0.78, 0.64, 0.38, 0.82))
		draw_string(font, Vector2(mm_rect. position.x + 6.0, center.y + 4.0), "W", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(0.78, 0.64, 0.38, 0.82))
		draw_string(font, Vector2(mm_rect.end.x - 15.0, center.y + 4.0), "E", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(0.78, 0.64, 0.38, 0.82))

		# Caption below radar
		var cap_rect: Rect2 = Rect2(mm_rect.position.x - 4.0, mm_rect.end.y + 6.0, mm_rect.size.x + 8.0, 22.0)
		draw_rect(cap_rect, Color(0.04, 0.03, 0.05, 0.86), true)
		draw_rect(cap_rect, Color(0.62, 0.48, 0.24, 0.80), false, 1.0)
		draw_string(
			font,
			Vector2(cap_rect.position.x + 14.0, cap_rect.position.y + 15.0),
			"[M / TAB] CARTOGRAPHY",
			HORIZONTAL_ALIGNMENT_LEFT,
			-1,
			11,
			Color(0.95, 0.82, 0.52, 0.94)
		)


func _draw_full_screen_cartography_map(vp_size: Vector2) -> void:
	# 1. Translucent Obsidian Screen Backdrop
	draw_rect(Rect2(Vector2.ZERO, vp_size), Color(0.015, 0.01, 0.025, 0.84), true)

	var modal_pos: Vector2 = (vp_size - FULL_MAP_SIZE) * 0.5
	var modal_rect: Rect2 = Rect2(modal_pos, FULL_MAP_SIZE)

	# 2. Ornate Gothic Cartographer's Frame
	draw_rect(modal_rect.grow(6.0), Color(0.08, 0.05, 0.06, 0.98), true)
	draw_rect(modal_rect, Color(0.04, 0.03, 0.05, 0.96), true)
	draw_rect(modal_rect.grow(6.0), Color(0.78, 0.60, 0.28, 0.96), false, 2.5)
	draw_rect(modal_rect, Color(0.52, 0.38, 0.20, 0.90), false, 1.5)

	var map_canvas_rect: Rect2 = Rect2(
		modal_rect.position.x + 16.0,
		modal_rect.position.y + 58.0,
		modal_rect.size.x - SIDEBAR_WIDTH - 36.0,
		modal_rect.size.y - 108.0
	)
	var sidebar_rect: Rect2 = Rect2(
		map_canvas_rect.end.x + 14.0,
		modal_rect.position.y + 58.0,
		SIDEBAR_WIDTH,
		modal_rect.size.y - 108.0
	)

	# Map Canvas Parchment-Obsidian Background & Subtle Coordinate Grid
	draw_rect(map_canvas_rect, Color(0.025, 0.02, 0.035, 0.96), true)
	var grid_step: float = CELL_SIZE * map_zoom
	if grid_step >= 12.0:
		var gx_start: float = fmod(map_pan_offset.x, grid_step)
		var x_cur: float = map_canvas_rect.position.x + gx_start
		while x_cur < map_canvas_rect.end.x:
			if x_cur > map_canvas_rect.position.x:
				draw_line(Vector2(x_cur, map_canvas_rect.position.y), Vector2(x_cur, map_canvas_rect.end.y), Color(0.35, 0.28, 0.18, 0.10), 1.0)
			x_cur += grid_step
		var gy_start: float = fmod(map_pan_offset.y, grid_step)
		var y_cur: float = map_canvas_rect.position.y + gy_start
		while y_cur < map_canvas_rect.end.y:
			if y_cur > map_canvas_rect.position.y:
				draw_line(Vector2(map_canvas_rect.position.x, y_cur), Vector2(map_canvas_rect.end.x, y_cur), Color(0.35, 0.28, 0.18, 0.10), 1.0)
			y_cur += grid_step

	# 3. Project Discovered & Shrouded Cells onto Full Map Canvas
	var canvas_center: Vector2 = map_canvas_rect.position + map_canvas_rect.size * 0.5 + map_pan_offset
	_draw_map_world_projection(map_canvas_rect.grow(-4.0), canvas_center, map_zoom, true)
	draw_rect(map_canvas_rect, Color(0.68, 0.52, 0.26, 0.90), false, 1.5)

	# 4. Top Header Banner & Bottom Controls Bar
	var font: Font = ThemeDB.fallback_font
	if font != null:
		draw_string(
			font,
			Vector2(modal_rect.position.x + 26.0, modal_rect.position.y + 38.0),
			"❖  CARTOGRAPHER'S EXPEDITION ATLAS  —  FOG OF WAR SURVEY  ❖",
			HORIZONTAL_ALIGNMENT_LEFT,
			-1,
			20,
			Color(1.0, 0.86, 0.46, 0.98)
		)
		draw_string(
			font,
			Vector2(modal_rect.end.x - 245.0, modal_rect.position.y + 36.0),
			"[M / TAB] Close Atlas",
			HORIZONTAL_ALIGNMENT_LEFT,
			-1,
			14,
			Color(0.86, 0.74, 0.50, 0.92)
		)
		draw_string(
			font,
			Vector2(map_canvas_rect.position.x + 12.0, modal_rect.end.y - 18.0),
			"[W,A,S,D / Drag] Pan Map    |    [Mouse Wheel / +/-] Zoom (%.1fx)    |    [SPACE] Re-Center on Hunter" % map_zoom,
			HORIZONTAL_ALIGNMENT_LEFT,
			-1,
			13,
			Color(0.88, 0.78, 0.56, 0.92)
		)

	# 5. Expedition Summary & Legend Sidebar
	_draw_cartography_sidebar(sidebar_rect)


func _draw_cartography_sidebar(sb_rect: Rect2) -> void:
	draw_rect(sb_rect, Color(0.05, 0.035, 0.05, 0.96), true)
	draw_rect(sb_rect, Color(0.68, 0.52, 0.26, 0.90), false, 1.5)

	var font: Font = ThemeDB.fallback_font
	if font == null:
		return

	var x0: float = sb_rect.position.x + 16.0
	var y_cur: float = sb_rect.position.y + 28.0

	var p_pos: Vector3 = _get_node_world_pos(_player)
	var in_dungeon: bool = (p_pos.y <= -100.0) or (_dungeon_gen != null and _dungeon_gen.active_room_count > 0 and not discovered_cells.is_empty() and p_pos.y <= -100.0)

	var zone_title: String = "SANCTUARY OVERWORLD & CRYPT HUB"
	var sub_mutator: String = "Safe Harbour Consecrated Ground"
	var depth_str: String = "Sanctuary Hub"
	var chests_total: int = _hub_chest_positions.size()
	var chests_found: int = 0
	var portals_found: int = 0

	if in_dungeon and _dungeon_gen != null:
		var prof: Dictionary = _dungeon_gen.get_biome_profile(_dungeon_gen.active_biome_id)
		zone_title = String(prof.get("title", "The Endless Ossuary")).to_upper()
		sub_mutator = _dungeon_gen.last_mood_mutator_name if not _dungeon_gen.last_mood_mutator_name.is_empty() else "Ancient Catacombs"
		depth_str = "Depth Tier %d  |  Vista: %s" % [_dungeon_gen.active_depth_tier, _dungeon_gen.last_vista_name if not _dungeon_gen.last_vista_name.is_empty() else "Standard"]
		chests_total = _dungeon_gen.last_chest_positions.size()
		for c_pos: Vector3 in _dungeon_gen.last_chest_positions:
			if discovered_cells.has(_world_to_dungeon_cell(c_pos)):
				chests_found += 1
		for pt_pos: Vector3 in _dungeon_gen.last_portal_positions:
			if discovered_cells.has(_world_to_dungeon_cell(pt_pos)):
				portals_found += 1
	else:
		for pt_h: Vector3 in _hub_portal_positions:
			if _hub_discovered_cells.has(_world_to_hub_cell(pt_h)):
				portals_found += 1

	draw_string(font, Vector2(x0, y_cur), "ACTIVE EXPEDITION ZONE", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(0.75, 0.62, 0.38, 0.90))
	y_cur += 20.0
	draw_string(font, Vector2(x0, y_cur), zone_title, HORIZONTAL_ALIGNMENT_LEFT, sb_rect.size.x - 28.0, 15, Color(1.0, 0.86, 0.44, 0.98))
	y_cur += 20.0
	draw_string(font, Vector2(x0, y_cur), sub_mutator, HORIZONTAL_ALIGNMENT_LEFT, sb_rect.size.x - 28.0, 13, Color(0.90, 0.58, 0.32, 0.95))
	y_cur += 18.0
	draw_string(font, Vector2(x0, y_cur), depth_str, HORIZONTAL_ALIGNMENT_LEFT, sb_rect.size.x - 28.0, 12, Color(0.76, 0.72, 0.64, 0.88))
	y_cur += 24.0

	# Exploration Progress Bar
	var charted_rooms: int = get_charted_room_count()
	var total_rooms: int = get_total_room_count()
	var pct: float = get_exploration_percentage()
	draw_string(
		font,
		Vector2(x0, y_cur),
		"CHAMBERS CHARTED: %d / %d (%.0f%%)" % [charted_rooms, total_rooms, pct],
		HORIZONTAL_ALIGNMENT_LEFT,
		-1,
		13,
		Color(0.96, 0.88, 0.66, 0.96)
	)
	y_cur += 10.0
	var bar_rect: Rect2 = Rect2(x0, y_cur, sb_rect.size.x - 32.0, 14.0)
	draw_rect(bar_rect, Color(0.10, 0.08, 0.12, 0.95), true)
	var fill_w: float = (bar_rect.size.x - 2.0) * clampf(pct / 100.0, 0.04, 1.0)
	draw_rect(Rect2(bar_rect.position.x + 1.0, bar_rect.position.y + 1.0, fill_w, bar_rect.size.y - 2.0), Color(0.84, 0.64, 0.24, 0.95), true)
	draw_rect(bar_rect, Color(0.68, 0.52, 0.26, 0.90), false, 1.0)
	y_cur += 30.0

	# Discovered POIs
	draw_string(font, Vector2(x0, y_cur), "RELIQUARY CHESTS:  %d / %d Charted" % [chests_found, chests_total], HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color(1.0, 0.84, 0.32, 0.95))
	y_cur += 20.0
	draw_string(font, Vector2(x0, y_cur), "OCCULT RIFT PORTALS:  %d Charted" % portals_found, HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color(0.88, 0.56, 1.0, 0.95))
	y_cur += 26.0

	draw_line(Vector2(x0, y_cur), Vector2(sb_rect.end.x - 16.0, y_cur), Color(0.55, 0.42, 0.22, 0.65), 1.0)
	y_cur += 22.0

	# Map Legend
	draw_string(font, Vector2(x0, y_cur), "CARTOGRAPHY LEGEND", HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color(1.0, 0.86, 0.46, 0.96))
	y_cur += 24.0

	var legend_items: Array[Dictionary] = [
		{"col": Color(1.0, 0.92, 0.62, 1.0), "sym": "▲", "label": "Hunter Position & Lantern Cone"},
		{"col": Color(0.32, 0.27, 0.22, 0.95), "sym": "■", "label": "Charted Chamber (Same Level)"},
		{"col": Color(0.46, 0.38, 0.26, 0.95), "sym": "■", "label": "Elevated Balcony / Mezzanine (+Y)"},
		{"col": Color(0.18, 0.22, 0.32, 0.95), "sym": "■", "label": "Sunken Bone Pit / Chasm (-Y)"},
		{"col": Color(0.45, 0.38, 0.52, 0.65), "sym": "?", "label": "Uncharted Doorway Frontier"},
		{"col": Color(0.55, 0.85, 0.95, 0.98), "sym": "▲▼", "label": "Stone Stairwell (Ascend / Descend)"},
		{"col": Color(0.82, 0.68, 0.42, 0.98), "sym": "═", "label": "Arched Ossuary Chasm Bridge"},
		{"col": Color(1.0, 0.84, 0.25, 1.0), "sym": "◆", "label": "Gothic Reliquary Loot Chest"},
		{"col": Color(0.88, 0.42, 1.0, 1.0), "sym": "◎", "label": "Dimensional Occult Rift Portal"},
		{"col": Color(1.0, 0.20, 0.24, 0.96), "sym": "●", "label": "Hostile Catacomb Threat (Nearby)"}
	]

	for item: Dictionary in legend_items:
		var ic_col: Color = item["col"] as Color
		var sym_s: String = String(item["sym"])
		var lbl_s: String = String(item["label"])
		draw_string(font, Vector2(x0 + 2.0, y_cur), sym_s, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, ic_col)
		draw_string(font, Vector2(x0 + 28.0, y_cur), lbl_s, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(0.88, 0.82, 0.72, 0.92))
		y_cur += 24.0


func _draw_map_world_projection(clip_rect: Rect2, screen_center: Vector2, px_per_meter: float, is_full_map: bool) -> void:
	var p_pos: Vector3 = _get_node_world_pos(_player)
	var p_yaw: float = 0.0
	if _player != null and is_instance_valid(_player):
		p_yaw = _player.global_rotation.y if _player.is_inside_tree() else _player.rotation.y

	var in_dungeon: bool = (p_pos.y <= -100.0)
	if not in_dungeon and _dungeon_gen != null and _dungeon_gen.active_room_count > 0 and not discovered_cells.is_empty() and is_full_map and _last_player_pos.y <= -100.0:
		in_dungeon = true
		p_pos = _last_player_pos

	var active_occupied: Dictionary = _hub_occupied_cells
	var active_discovered: Dictionary = _hub_discovered_cells
	var active_shrouded: Dictionary = _hub_shrouded_cells
	var active_stairs: Dictionary = _hub_stair_cells
	var active_bridges: Dictionary = {}
	var active_chests: Array = _hub_chest_positions
	var active_portals: Array = _hub_portal_positions
	var origin_vec: Vector3 = Vector3.ZERO
	var player_cell: Vector3i = _world_to_hub_cell(p_pos)

	if in_dungeon and _dungeon_gen != null:
		var map_data: Dictionary = _dungeon_gen.get_dungeon_map_data()
		active_occupied = map_data.get("occupied_cells", {}) as Dictionary
		active_discovered = discovered_cells
		active_shrouded = shrouded_adjacent_cells
		active_stairs = map_data.get("stair_cells", {}) as Dictionary
		active_bridges = map_data.get("bridge_cells", {}) as Dictionary
		active_chests = map_data.get("chest_positions", []) as Array
		active_portals = map_data.get("portal_positions", []) as Array
		origin_vec = DUNGEON_ORIGIN
		player_cell = _world_to_dungeon_cell(p_pos)

	var cell_px: float = CELL_SIZE * px_per_meter
	var half_cell_px: float = cell_px * 0.5
	var font: Font = ThemeDB.fallback_font

	# 1. Draw Shrouded Frontier Cells (STATE_SHROUDED_EDGE = 1) at 22% opacity with '?'
	for s_var: Variant in active_shrouded.keys():
		if not (s_var is Vector3i):
			continue
		var s_cell: Vector3i = s_var as Vector3i
		if active_discovered.has(s_cell):
			continue
		var c_world: Vector3 = origin_vec + Vector3(float(s_cell.x) * CELL_SIZE, float(s_cell.y) * CELL_SIZE, float(s_cell.z) * CELL_SIZE)
		var sc_pt: Vector2 = screen_center + Vector2((c_world.x - p_pos.x) * px_per_meter, (c_world.z - p_pos.z) * px_per_meter)
		var cell_rect: Rect2 = Rect2(sc_pt.x - half_cell_px, sc_pt.y - half_cell_px, cell_px, cell_px)
		if not clip_rect.intersects(cell_rect):
			continue
		var clipped: Rect2 = clip_rect.intersection(cell_rect)
		draw_rect(clipped, Color(0.24, 0.19, 0.28, 0.22), true)
		draw_rect(clipped, Color(0.52, 0.42, 0.60, 0.28), false, 1.0)
		if font != null and cell_px >= 18.0 and clip_rect.has_point(sc_pt):
			draw_string(font, sc_pt + Vector2(-4.0, 5.0), "?", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(0.78, 0.66, 0.88, 0.48))

	# 2. Draw Discovered Cells (STATE_DISCOVERED = 2) sorted by elevation (lower first, then same, then upper)
	for pass_elev: int in [-1, 0, 1]:
		for d_var: Variant in active_discovered.keys():
			if not (d_var is Vector3i):
				continue
			var d_cell: Vector3i = d_var as Vector3i
			var rel_y: int = clampi(d_cell.y - player_cell.y, -1, 1)
			if rel_y != pass_elev:
				continue

			# If a lower cell is directly beneath an occupied same-level cell, only draw the lower cell if the upper cell isn't a solid floor
			var c_world: Vector3 = origin_vec + Vector3(float(d_cell.x) * CELL_SIZE, float(d_cell.y) * CELL_SIZE, float(d_cell.z) * CELL_SIZE)
			var sc_pt: Vector2 = screen_center + Vector2((c_world.x - p_pos.x) * px_per_meter, (c_world.z - p_pos.z) * px_per_meter)
			var cell_rect: Rect2 = Rect2(sc_pt.x - half_cell_px, sc_pt.y - half_cell_px, cell_px, cell_px)
			if not clip_rect.intersects(cell_rect):
				continue

			var fill_col: Color = Color(0.32, 0.27, 0.22, 0.90)
			var wall_col: Color = Color(0.82, 0.68, 0.42, 0.95)
			if rel_y < 0:
				fill_col = Color(0.16, 0.18, 0.24, 0.72)
				wall_col = Color(0.42, 0.48, 0.62, 0.75)
			elif rel_y > 0:
				fill_col = Color(0.46, 0.38, 0.26, 0.86)
				wall_col = Color(0.94, 0.80, 0.48, 0.95)

			var clipped: Rect2 = clip_rect.intersection(cell_rect)
			draw_rect(clipped, fill_col, true)

			# Draw perimeter walls where adjacent neighbor at same elevation is not occupied
			if clip_rect.encloses(cell_rect):
				var p_tl: Vector2 = cell_rect.position
				var p_tr: Vector2 = Vector2(cell_rect.end.x, cell_rect.position.y)
				var p_bl: Vector2 = Vector2(cell_rect.position.x, cell_rect.end.y)
				var p_br: Vector2 = cell_rect.end

				if not active_occupied.has(Vector3i(d_cell.x, d_cell.y, d_cell.z - 1)):
					draw_line(p_tl, p_tr, wall_col, 2.0)
				if not active_occupied.has(Vector3i(d_cell.x, d_cell.y, d_cell.z + 1)):
					draw_line(p_bl, p_br, wall_col, 2.0)
				if not active_occupied.has(Vector3i(d_cell.x - 1, d_cell.y, d_cell.z)):
					draw_line(p_tl, p_bl, wall_col, 2.0)
				if not active_occupied.has(Vector3i(d_cell.x + 1, d_cell.y, d_cell.z)):
					draw_line(p_tr, p_br, wall_col, 2.0)

			# Draw Stone Bridge rails if this cell is in active_bridges
			if active_bridges.has(d_cell) and clip_rect.has_point(sc_pt):
				var br_w: float = half_cell_px * 0.55
				draw_rect(Rect2(sc_pt.x - br_w, cell_rect.position.y, br_w * 2.0, cell_px), Color(0.52, 0.44, 0.32, 0.95), true)
				draw_line(Vector2(sc_pt.x - br_w, cell_rect.position.y), Vector2(sc_pt.x - br_w, cell_rect.end.y), Color(0.92, 0.78, 0.48, 1.0), 2.0)
				draw_line(Vector2(sc_pt.x + br_w, cell_rect.position.y), Vector2(sc_pt.x + br_w, cell_rect.end.y), Color(0.92, 0.78, 0.48, 1.0), 2.0)

			# Draw Staircase step-bars & directional chevron if this cell is in active_stairs
			if active_stairs.has(d_cell) and clip_rect.has_point(sc_pt):
				var st_col: Color = Color(0.55, 0.85, 0.95, 0.96)
				for s_i: int in range(-2, 3):
					var sy: float = sc_pt.y + float(s_i) * (cell_px * 0.14)
					draw_line(Vector2(sc_pt.x - half_cell_px * 0.65, sy), Vector2(sc_pt.x + half_cell_px * 0.65, sy), st_col, 1.5)
				if font != null and cell_px >= 16.0:
					draw_string(font, sc_pt + Vector2(-5.0, 4.0), "▲", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(0.75, 0.95, 1.0, 1.0))

	# 3. Draw Discovered Reliquary Chests (Golden Diamond '◆')
	for ch_var: Variant in active_chests:
		if not (ch_var is Vector3):
			continue
		var ch_pos: Vector3 = ch_var as Vector3
		var ch_cell: Vector3i = _world_to_dungeon_cell(ch_pos) if in_dungeon else _world_to_hub_cell(ch_pos)
		if not active_discovered.has(ch_cell):
			continue
		var ch_sc: Vector2 = screen_center + Vector2((ch_pos.x - p_pos.x) * px_per_meter, (ch_pos.z - p_pos.z) * px_per_meter)
		if not clip_rect.has_point(ch_sc):
			continue
		var d_rad: float = 5.5 if is_full_map else 4.5
		var diamond: PackedVector2Array = PackedVector2Array([
			ch_sc + Vector2(0.0, -d_rad),
			ch_sc + Vector2(d_rad, 0.0),
			ch_sc + Vector2(0.0, d_rad),
			ch_sc + Vector2(-d_rad, 0.0)
		])
		draw_colored_polygon(diamond, Color(1.0, 0.84, 0.22, 1.0))
		draw_polyline(diamond, Color(0.25, 0.16, 0.04, 1.0), 1.2)

	# 4. Draw Discovered Occult Portals (Spinning Violet/Gold Vortex Ring '◎')
	for pt_var: Variant in active_portals:
		if not (pt_var is Vector3):
			continue
		var pt_pos: Vector3 = pt_var as Vector3
		var pt_cell: Vector3i = _world_to_dungeon_cell(pt_pos) if in_dungeon else _world_to_hub_cell(pt_pos)
		if not active_discovered.has(pt_cell):
			continue
		var pt_sc: Vector2 = screen_center + Vector2((pt_pos.x - p_pos.x) * px_per_meter, (pt_pos.z - p_pos.z) * px_per_meter)
		if not clip_rect.has_point(pt_sc):
			continue
		var p_rad: float = 6.5 if is_full_map else 5.0
		draw_circle(pt_sc, p_rad, Color(0.24, 0.08, 0.34, 0.92))
		draw_arc(pt_sc, p_rad, _pulse_time * 2.5, _pulse_time * 2.5 + PI * 1.4, 16, Color(0.92, 0.48, 1.0, 1.0), 2.0)
		draw_circle(pt_sc, p_rad * 0.42, Color(1.0, 0.82, 0.42, 0.96))

	# 5. Draw Nearby Aggroed Enemies (within 16.0m of Hunter) as Pulsing Crimson Dots
	if is_inside_tree() and get_tree() != null:
		var pulse_alpha: float = 0.72 + 0.25 * sin(_pulse_time * 6.0)
		for en_node: Node in get_tree().get_nodes_in_group("enemies"):
			if not (en_node is Node3D) or not is_instance_valid(en_node):
				continue
			if en_node.has_method("is_alive") and not bool(en_node.call("is_alive")):
				continue
			var en_3d: Node3D = en_node as Node3D
			var en_pos: Vector3 = _get_node_world_pos(en_3d)
			var dist_e: float = en_pos.distance_to(p_pos)
			if dist_e <= 16.0:
				var en_sc: Vector2 = screen_center + Vector2((en_pos.x - p_pos.x) * px_per_meter, (en_pos.z - p_pos.z) * px_per_meter)
				if clip_rect.has_point(en_sc):
					draw_circle(en_sc, 4.0 if is_full_map else 3.2, Color(1.0, 0.16, 0.20, pulse_alpha))
					draw_circle(en_sc, 1.8, Color(1.0, 0.75, 0.75, pulse_alpha))

	# 6. Draw Hunter Position, 75-deg Translucent Lantern FOV Cone & Golden-Ivory Directional Chevron
	var player_sc: Vector2 = screen_center
	if clip_rect.has_point(player_sc):
		# In Godot 3D, forward (-Z) rotated by global_rotation.y has 2D top-down vector (-sin(yaw), -cos(yaw))
		var fwd_2d: Vector2 = Vector2(-sin(p_yaw), -cos(p_yaw)).normalized()
		var right_2d: Vector2 = Vector2(-fwd_2d.y, fwd_2d.x)

		# 75-degree Lantern FOV Cone
		var cone_len: float = 34.0 if is_full_map else 26.0
		var half_fov: float = deg_to_rad(37.5)
		var cone_pts: PackedVector2Array = PackedVector2Array([player_sc])
		for c_step: int in range(9):
			var ang: float = lerpf(-half_fov, half_fov, float(c_step) / 8.0)
			var ray_dir: Vector2 = fwd_2d.rotated(ang)
			cone_pts.append(player_sc + ray_dir * cone_len)
		draw_colored_polygon(cone_pts, Color(1.0, 0.82, 0.42, 0.16))

		# Directional Hunter Chevron
		var chev_size: float = 8.5 if is_full_map else 7.0
		var chev_pts: PackedVector2Array = PackedVector2Array([
			player_sc + fwd_2d * chev_size,
			player_sc - fwd_2d * (chev_size * 0.65) + right_2d * (chev_size * 0.65),
			player_sc - fwd_2d * (chev_size * 0.28),
			player_sc - fwd_2d * (chev_size * 0.65) - right_2d * (chev_size * 0.65)
		])
		draw_colored_polygon(chev_pts, Color(1.0, 0.94, 0.72, 1.0))
		draw_polyline(chev_pts, Color(0.18, 0.12, 0.05, 1.0), 1.5)
