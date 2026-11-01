extends SceneTree

var _level_inst: Node3D = null
var _player: FPSController = null
var _vm_ctrl: FPSViewmodelController = null
var _right_pivot: Node3D = null
var _left_pivot: Node3D = null
var _pendulum: Node3D = null
var _cylinder: Node3D = null
var _hammer: Node3D = null

var _frame: int = 0
var _walk_start_right_pos: Vector3 = Vector3.ZERO
var _walk_start_right_rot: Vector3 = Vector3.ZERO
var _walk_start_left_pos: Vector3 = Vector3.ZERO
var _walk_start_pendulum_rot: Vector3 = Vector3.ZERO

var _max_walk_only_pos_delta: float = 0.0
var _max_walk_only_rot_delta: float = 0.0
var _max_left_walk_pos_delta: float = 0.0
var _max_pendulum_rot_delta: float = 0.0

var _pre_fire_rot_x_deg: float = 0.0
var _post_fire_rot_x_deg: float = 0.0
var _fire_spike_deg: float = 0.0
var _pre_fire_pos: Vector3 = Vector3.ZERO
var _post_fire_pos: Vector3 = Vector3.ZERO
var _pre_fire_cyl_rot_z: float = 0.0
var _hammer_cocked_deg: float = 0.0

var _footsteps_at_walk_start: int = 0
var _footsteps_after_1s: int = 0


func _init() -> void:
	print("=== [Verify] Loading res://scenes/levels/town_overworld.tscn ===")
	var level_scene: PackedScene = load("res://scenes/levels/town_overworld.tscn") as PackedScene
	if level_scene == null:
		push_error("[FAIL] Could not load res://scenes/levels/town_overworld.tscn")
		quit(1)
		return

	_level_inst = level_scene.instantiate() as Node3D
	root.add_child(_level_inst)

	_player = _level_inst.get_node_or_null("Player") as FPSController
	if _player == null:
		push_error("[FAIL] Player node not found in town_overworld.tscn")
		quit(1)
		return

	_vm_ctrl = _player.find_child("ViewmodelRig", true, false) as FPSViewmodelController
	if _vm_ctrl == null:
		push_error("[FAIL] ViewmodelRig (FPSViewmodelController) not found on Player")
		quit(1)
		return

	_player.position = Vector3(0.0, 0.22, 24.0)
	_player.velocity = Vector3.ZERO


func _fail_and_quit(msg: String) -> bool:
	push_error(msg)
	if _level_inst != null:
		_level_inst.free()
	quit(1)
	return true


func _physics_process(_delta: float) -> bool:
	_frame += 1

	# Frame 1: Resolve viewmodel sub-nodes & verify hierarchy/particle/light setup
	if _frame == 1:
		_right_pivot = _vm_ctrl.right_hand_pivot
		_left_pivot = _vm_ctrl.left_hand_pivot
		_pendulum = _left_pivot.find_child("LanternPendulum", true, false) as Node3D if _left_pivot != null else null
		_cylinder = _right_pivot.find_child("Cylinder", true, false) as Node3D if _right_pivot != null else null
		_hammer = _right_pivot.find_child("Hammer", true, false) as Node3D if _right_pivot != null else null

		if _right_pivot == null or _left_pivot == null or _pendulum == null:
			return _fail_and_quit("[FAIL] Missing RightHandPivot, LeftHandPivot, or LanternPendulum!")

		var l_light: OmniLight3D = _vm_ctrl.lantern_light
		if l_light == null or l_light.get_parent() != _pendulum:
			return _fail_and_quit("[FAIL] LanternLight is not a direct child of LanternPendulum!")
		if not l_light.shadow_enabled or l_light.light_energy < 2.5 or l_light.omni_range < 14.9:
			return _fail_and_quit("[FAIL] LanternLight settings invalid: energy=%.2f range=%.2f" % [l_light.light_energy, l_light.omni_range])

		var m_parts: GPUParticles3D = _vm_ctrl.muzzle_particles
		var m_light: OmniLight3D = _vm_ctrl.muzzle_flash_light
		if m_parts == null or m_parts.get_parent() != _right_pivot:
			return _fail_and_quit("[FAIL] MuzzleParticles is not a direct child of RightHandPivot!")
		if m_light == null or m_light.get_parent() != _right_pivot:
			return _fail_and_quit("[FAIL] MuzzleFlashLight is not a direct child of RightHandPivot!")
		if not m_parts.position.is_equal_approx(Vector3(0.0, 0.06, -0.55)):
			return _fail_and_quit("[FAIL] MuzzleParticles position is %s, expected (0, 0.06, -0.55)" % str(m_parts.position))
		if not m_parts.local_coords or not m_parts.one_shot or not is_equal_approx(m_parts.lifetime, 0.08):
			return _fail_and_quit("[FAIL] MuzzleParticles parameters invalid!")

		print("[PASS] Hierarchy Check: LanternLight inside LanternPendulum (energy=%.2f, range=%.1f), MuzzleParticles inside RightHandPivot at %s" % [
			l_light.light_energy,
			l_light.omni_range,
			str(m_parts.position)
		])

	# Frame 10: Player is settled on the valley road floor; begin simulated walking
	if _frame == 10:
		_walk_start_right_pos = _right_pivot.position
		_walk_start_right_rot = _right_pivot.rotation
		_walk_start_left_pos = _left_pivot.position
		_walk_start_pendulum_rot = _pendulum.rotation
		_footsteps_at_walk_start = _player.footstep_count
		Input.action_press("move_forward")
		print("=== [Verify] Starting simulated walk at frame 10 (pos=%s, on_floor=%s) ===" % [
			str(_player.global_position),
			str(_player.is_on_floor())
		])

	# Frames 11..24: Pure walking before firing — record walk-only viewmodel bob & pendulum swing
	if _frame >= 11 and _frame <= 24:
		var pos_diff: float = (_right_pivot.position - _walk_start_right_pos).length()
		var rot_diff: float = (_right_pivot.rotation - _walk_start_right_rot).length()
		var left_diff: float = (_left_pivot.position - _walk_start_left_pos).length()
		var pend_diff: float = (_pendulum.rotation - _walk_start_pendulum_rot).length()
		if pos_diff > _max_walk_only_pos_delta:
			_max_walk_only_pos_delta = pos_diff
		if rot_diff > _max_walk_only_rot_delta:
			_max_walk_only_rot_delta = rot_diff
		if left_diff > _max_left_walk_pos_delta:
			_max_left_walk_pos_delta = left_diff
		if pend_diff > _max_pendulum_rot_delta:
			_max_pendulum_rot_delta = pend_diff

	# Frame 25: Call _fire_revolver() while walking
	if _frame == 25:
		_pre_fire_rot_x_deg = rad_to_deg(_right_pivot.rotation.x)
		_pre_fire_pos = _right_pivot.position
		if _cylinder != null:
			_pre_fire_cyl_rot_z = _cylinder.rotation.z
		print("[Verify] Frame 25: Calling _fire_revolver() (pre-fire RightHandPivot.rotation.x = %.2f deg, pos = %s)" % [
			_pre_fire_rot_x_deg,
			str(_pre_fire_pos)
		])
		_vm_ctrl._fire_revolver()
		if _hammer != null:
			_hammer_cocked_deg = rad_to_deg(_hammer.rotation.x)

	# Frame 26 (the frame immediately after _fire_revolver() is called)
	if _frame == 26:
		_post_fire_rot_x_deg = rad_to_deg(_right_pivot.rotation.x)
		_post_fire_pos = _right_pivot.position
		_fire_spike_deg = _post_fire_rot_x_deg - _pre_fire_rot_x_deg
		print("[Verify] Frame 26 (1 frame after _fire_revolver): RightHandPivot.rotation.x = %.2f deg (spike = +%.2f deg), RightHandPivot.position = %s" % [
			_post_fire_rot_x_deg,
			_fire_spike_deg,
			str(_post_fire_pos)
		])

	# Continue tracking pendulum rotation through frame 40 (30 physics frames of walking: frames 10..40)
	if _frame >= 25 and _frame <= 40:
		var pend_diff2: float = (_pendulum.rotation - _walk_start_pendulum_rot).length()
		if pend_diff2 > _max_pendulum_rot_delta:
			_max_pendulum_rot_delta = pend_diff2

	# Frame 70: Complete 1.0 second (60 physics frames from frame 10 to frame 70) of grounded walking
	if _frame == 70:
		Input.action_release("move_forward")
		_footsteps_after_1s = _player.footstep_count - _footsteps_at_walk_start
		print("[Verify] 1.0s Grounded Walk Footstep Count = %d steps (FootstepAudioPlayer.volume_db = %.1f dB)" % [
			_footsteps_after_1s,
			_player.FootstepAudioPlayer.volume_db
		])

		# Run surface detection checks at the 3 required world coordinates
		_player.global_position = Vector3(0.0, 0.5, 5.0)
		var surf_gravel: String = _player.detect_surface()

		_player.global_position = Vector3(10.0, 1.0, 5.0)
		var surf_grass: String = _player.detect_surface()

		_player.global_position = Vector3(0.0, 4.2, -16.0)
		var surf_stone: String = _player.detect_surface()

		print("[Verify] Surface Detection: (0, 0.5, 5.0)->'%s', (10.0, 1.0, 5.0)->'%s', (0, 4.2, -16.0)->'%s'" % [
			surf_gravel,
			surf_grass,
			surf_stone
		])

		var cyl_delta_deg: float = rad_to_deg(absf(_cylinder.rotation.z - _pre_fire_cyl_rot_z)) if _cylinder != null else 0.0
		print("[Verify] Walk & Recoil Summary: walk_only_pos_delta=%.4fm, left_walk_pos_delta=%.4fm, walk_only_rot_delta=%.4frad (%.2f deg), fire_spike_deg=+%.2f deg, pendulum_rot_delta=%.4frad (%.2f deg), cylinder_rot_deg=%.2f deg, hammer_cock_deg=%.1f deg" % [
			_max_walk_only_pos_delta,
			_max_left_walk_pos_delta,
			_max_walk_only_rot_delta,
			rad_to_deg(_max_walk_only_rot_delta),
			_fire_spike_deg,
			_max_pendulum_rot_delta,
			rad_to_deg(_max_pendulum_rot_delta),
			cyl_delta_deg,
			_hammer_cocked_deg
		])

		# ASSERTION 1: RightHandPivot.position and RightHandPivot.rotation measurably change during walking AND spike upward by > 10 degrees on the frame after _fire_revolver()
		if _max_walk_only_pos_delta < 0.02 or _max_walk_only_rot_delta < 0.03:
			return _fail_and_quit("[FAIL] Assertion 1a failed: RightHandPivot did not measurably move during pure walking! pos_delta=%.4f rot_delta=%.4f" % [_max_walk_only_pos_delta, _max_walk_only_rot_delta])
		if _fire_spike_deg <= 10.0:
			return _fail_and_quit("[FAIL] Assertion 1b failed: RightHandPivot.rotation.x spike on frame after _fire_revolver() was %.2f deg (must be > 10.0 deg)!" % _fire_spike_deg)
		if cyl_delta_deg < 45.0:
			return _fail_and_quit("[FAIL] Assertion 1c failed: Revolver Cylinder did not rotate (~60 deg expected, got %.2f deg)!" % cyl_delta_deg)

		# ASSERTION 2: LanternPendulum.rotation changes dynamically during movement
		if _max_pendulum_rot_delta < 0.10:
			return _fail_and_quit("[FAIL] Assertion 2 failed: LanternPendulum.rotation did not change dynamically during movement! delta=%.4f rad" % _max_pendulum_rot_delta)

		# ASSERTION 3: Surface detector returns "gravel" at (0, 0.5, 5.0), "grass" at (10.0, 1.0, 5.0), and "stone" at (0, 4.2, -16.0)
		if surf_gravel != "gravel" or surf_grass != "grass" or surf_stone != "stone":
			return _fail_and_quit("[FAIL] Assertion 3 failed: Expected gravel/grass/stone, got %s/%s/%s" % [surf_gravel, surf_grass, surf_stone])

		# ASSERTION 4: Footstep count over 1.0 second of simulated walking is strictly <= 3 steps
		if _footsteps_after_1s > 3 or _footsteps_after_1s < 1:
			return _fail_and_quit("[FAIL] Assertion 4 failed: Footstep count over 1.0s was %d (must be between 1 and 3)!" % _footsteps_after_1s)

		print("=== [ALL 4 RUNTIME VERIFICATION ASSERTIONS PASSED] ===")
		_level_inst.free()
		quit(0)
		return true

	return false
