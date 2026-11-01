extends SceneTree

var _level_inst: Node3D = null
var _player: FPSController = null
var _phase: int = 0
var _step_count: int = 0
var _max_upward_vel_y_on_road: float = 0.0
var _road_airborne_frames: int = 0


func _init() -> void:
	var level_scene: PackedScene = load("res://scenes/levels/town_overworld.tscn") as PackedScene
	if level_scene == null:
		push_error("[Test] Failed to load town_overworld.tscn")
		quit(1)
		return

	_level_inst = level_scene.instantiate() as Node3D
	root.add_child(_level_inst)

	_player = _level_inst.get_node_or_null("Player") as FPSController
	if _player == null:
		push_error("[Test] Could not find Player node in town_overworld.tscn")
		quit(1)
		return

	_player.position = Vector3(0.0, 0.65, 24.0)
	_player.velocity = Vector3.ZERO
	print("[Test] Starting Phase 0: Settling player on valley road at (0.0, 0.65, 24.0)...")


func _physics_process(_delta: float) -> bool:
	if _player == null:
		return true

	_step_count += 1

	# Phase 0: Settle onto valley road (20 physics frames)
	if _phase == 0:
		if _step_count >= 20:
			print("[Test] Settled on road at pos=", _player.global_position, " on_floor=", _player.is_on_floor())
			_phase = 1
			_step_count = 0
			Input.action_press("move_forward")
			print("[Test] Starting Phase 1: Walking North (-Z) up hilly valley road & church steps (Z = 24.0 -> -15.0)...")
		return false

	# Phase 1: Walk North (-Z) from Z = 24.0 into the church at Z = -15.0
	if _phase == 1:
		if _step_count > 5:
			if _player.velocity.y > _max_upward_vel_y_on_road:
				_max_upward_vel_y_on_road = _player.velocity.y
			if not _player.is_on_floor():
				_road_airborne_frames += 1
		if _step_count % 60 == 0:
			print(
				"[RoadWalk] step=%d pos=(%.2f, %.2f, %.2f) on_floor=%s vel_y=%.3f"
				% [_step_count, _player.global_position.x, _player.global_position.y, _player.global_position.z, str(_player.is_on_floor()), _player.velocity.y]
			)
		_log_wall_collisions("RoadWalk")

		if _player.global_position.z <= -15.0 or _step_count >= 520:
			Input.action_release("move_forward")
			print(
				"[Test] Finished Phase 1 at pos=(%.2f, %.2f, %.2f), max_upward_vel_y=%.4f, airborne_frames=%d"
				% [_player.global_position.x, _player.global_position.y, _player.global_position.z, _max_upward_vel_y_on_road, _road_airborne_frames]
			)
			if _player.global_position.z > -14.0:
				push_error("[FAIL] Player failed to reach church interior from valley road!")
				_log_all_collisions("RoadWalkFail")
				quit(1)
				return true
			# Start Phase 2: Spawn at (0.0, 4.2, -16.0) as specified and walk North (-Z) down the stairwell into the crypt
			_phase = 2
			_step_count = 0
			_player.global_position = Vector3(0.0, 4.2, -16.0)
			_player.velocity = Vector3.ZERO
			print("[Test] Starting Phase 2: Spawning at (0.0, 4.2, -16.0) and walking North (-Z) down stairwell into Crypt Basement...")
		return false

	# Phase 2: Walk North (-Z) from (0.0, 4.2, -16.0) down stairwell (Z = -20.0 -> -24.0) into Crypt Basement (Z <= -27.5, Y ~ 0.0)
	if _phase == 2:
		if _step_count == 10:
			Input.action_press("move_forward")

		if _step_count % 20 == 0:
			print(
				"[StairDescent] step=%d pos=(%.2f, %.2f, %.2f) on_floor=%s vel=(%.2f, %.2f, %.2f)"
				% [
					_step_count,
					_player.global_position.x,
					_player.global_position.y,
					_player.global_position.z,
					str(_player.is_on_floor()),
					_player.velocity.x,
					_player.velocity.y,
					_player.velocity.z
				]
			)
		_log_wall_collisions("StairDescent")

		if _player.global_position.z <= -27.5:
			Input.action_release("move_forward")
			print(
				"[PASS] Player smoothly descended stairwell into Crypt Basement! Final pos=(%.2f, %.2f, %.2f), on_floor=%s"
				% [_player.global_position.x, _player.global_position.y, _player.global_position.z, str(_player.is_on_floor())]
			)
			_phase = 3
			_step_count = 0
			Input.action_press("move_back")
			print("[Test] Starting Phase 3: Walking South (+Z) back up the crypt stairs into the church nave...")
			return false

		if _step_count >= 260:
			Input.action_release("move_forward")
			push_error(
				"[FAIL] Player got stuck descending stairwell at pos=(%.2f, %.2f, %.2f)!"
				% [_player.global_position.x, _player.global_position.y, _player.global_position.z]
			)
			_log_all_collisions("StuckDiagnostics")
			quit(1)
			return true

		return false

	# Phase 3: Walk South (+Z) back up the stairs from Z = -27.5 to Z >= -18.0 (Y ~ 4.0)
	if _phase == 3:
		if _step_count % 25 == 0:
			print(
				"[StairAscent] step=%d pos=(%.2f, %.2f, %.2f) on_floor=%s"
				% [_step_count, _player.global_position.x, _player.global_position.y, _player.global_position.z, str(_player.is_on_floor())]
			)
		_log_wall_collisions("StairAscent")

		if _player.global_position.z >= -18.0 and _player.global_position.y >= 3.85:
			Input.action_release("move_back")
			print(
				"[PASS] Player smoothly ascended crypt stairs back into Church Nave! Final pos=(%.2f, %.2f, %.2f)"
				% [_player.global_position.x, _player.global_position.y, _player.global_position.z]
			)
			print("[ALL PHYSICS TESTS PASSED]")
			quit(0)
			return true

		if _step_count >= 260:
			Input.action_release("move_back")
			push_error(
				"[FAIL] Player got stuck ascending stairwell at pos=(%.2f, %.2f, %.2f)!"
				% [_player.global_position.x, _player.global_position.y, _player.global_position.z]
			)
			_log_all_collisions("AscentStuckDiagnostics")
			quit(1)
			return true

	return false


func _log_wall_collisions(tag: String) -> void:
	var count: int = _player.get_slide_collision_count()
	for i: int in range(count):
		var col: KinematicCollision3D = _player.get_slide_collision(i)
		if col == null:
			continue
		var n: Vector3 = col.get_normal()
		if n.y < 0.55:
			var collider_obj: Object = col.get_collider()
			var col_name: String = "Unknown"
			if collider_obj is Node:
				var col_node: Node = collider_obj as Node
				var parent_node: Node = col_node.get_parent()
				col_name = (parent_node.name + "/" + col_node.name) if parent_node != null else col_node.name
			print(
				"  [%s BLOCKING COLLISION] collider=%s pos=(%.2f, %.2f, %.2f) normal=(%.2f, %.2f, %.2f)"
				% [tag, col_name, col.get_position().x, col.get_position().y, col.get_position().z, n.x, n.y, n.z]
			)


func _log_all_collisions(tag: String) -> void:
	var count: int = _player.get_slide_collision_count()
	for i: int in range(count):
		var col: KinematicCollision3D = _player.get_slide_collision(i)
		if col == null:
			continue
		var n: Vector3 = col.get_normal()
		var collider_obj: Object = col.get_collider()
		var col_name: String = "Unknown"
		if collider_obj is Node:
			var col_node: Node = collider_obj as Node
			var parent_node: Node = col_node.get_parent()
			col_name = (parent_node.name + "/" + col_node.name) if parent_node != null else col_node.name
		print(
			"  [%s COLLISION %d] collider=%s pos=(%.2f, %.2f, %.2f) normal=(%.2f, %.2f, %.2f)"
			% [tag, i, col_name, col.get_position().x, col.get_position().y, col.get_position().z, n.x, n.y, n.z]
		)
