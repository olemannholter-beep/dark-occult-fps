class_name FPSController
extends CharacterBody3D

@export var move_speed: float = 5.5
@export var acceleration: float = 12.0
@export var deceleration: float = 16.0
@export var air_deceleration: float = 2.2
@export var jump_velocity: float = 4.8
@export var mouse_sensitivity: float = 0.0022
@export var bob_frequency: float = 1.65
@export var bob_amplitude: float = 0.010
@export var max_step_height: float = 0.36
@export var step_stride_distance: float = 2.6

# Phase 3: Bloodborne-Style "Hunter's Quickstep Dash" parameters
@export var dash_duration: float = 0.22
@export var dash_cooldown: float = 0.65
@export var dash_speed: float = 19.5
@export var dash_speed_multiplier: float = 3.55
@export var base_dash_cooldown: float = 0.65

@onready var head: Node3D = $Head
@onready var camera: Camera3D = $Head/Camera3D

var _bob_time: float = 0.0
var _default_camera_pos: Vector3 = Vector3.ZERO
var _default_camera_fov: float = 75.0
var _gravity: float = 9.8

# Phase 1.1: Smooth Perlin-Noise Trauma Camera Shake (FastNoiseLite)
var trauma_noise: FastNoiseLite = FastNoiseLite.new()
var noise_time: float = 0.37
var camera_trauma: float = 0.0
var max_pitch_shake: float = deg_to_rad(7.5)
var max_yaw_shake: float = deg_to_rad(5.5)
var max_roll_shake: float = deg_to_rad(6.5)
var cam_shake_rot_offset: Vector3 = Vector3.ZERO
var cam_punch_rot: Vector3 = Vector3.ZERO
var cam_punch_vel: Vector3 = Vector3.ZERO

# Phase 1.2: Subconscious Camera Animations (Jump Take-Off, Heavy Landing, Strafe Tilt, Sprint Wave)
var cam_anim_pos_offset: Vector3 = Vector3.ZERO
var cam_anim_pos_vel: Vector3 = Vector3.ZERO
var cam_anim_rot_offset: Vector3 = Vector3.ZERO
var cam_anim_rot_vel: Vector3 = Vector3.ZERO
var prev_vertical_velocity: float = 0.0
var was_on_floor: bool = true
var is_jumping: bool = false
var _strafe_tilt_z: float = 0.0

# Phase 3.2: Omnidirectional Hunter's Quickstep Dash & I-Frames
var dash_cooldown_timer: float = 0.0
var dash_cooldown_remaining: float = 0.0
var dash_active_timer: float = 0.0
var dash_iframe_timer: float = 0.0
var is_dashing: bool = false
var is_dashing_iframes: bool = false
var dash_charges_remaining: int = 1
var dash_dir: Vector3 = Vector3.ZERO
var _dash_direction: Vector3 = Vector3.ZERO
var _dash_cam_dip_y: float = 0.0
var _dash_cam_tilt_rot: Vector3 = Vector3.ZERO
var _dash_fov_offset: float = 0.0
var _dash_sfx_player: AudioStreamPlayer = null
var _sfx_quickstep_dash: AudioStream = null

# Footstep audio & surface detection
var surface_raycast: RayCast3D = null
var _footstep_raycast: RayCast3D = null
var FootstepAudioPlayer: AudioStreamPlayer = null
var _footstep_player: AudioStreamPlayer = null
var step_cooldown_timer: float = 0.0
var _step_distance_accum: float = 0.0
var _last_step_index: int = -1
var footstep_count: int = 0
var _rng: RandomNumberGenerator = RandomNumberGenerator.new()
var _footstep_banks: Dictionary[String, Array] = {}
var _fp_body: FirstPersonBodyController = null


func _init() -> void:
	floor_max_angle = deg_to_rad(54.0)
	floor_snap_length = 0.65
	floor_stop_on_slope = true
	floor_constant_speed = true
	floor_block_on_wall = true
	safe_margin = 0.04
	_init_perlin_trauma_noise()
	if _fp_body == null:
		_fp_body = FirstPersonBodyController.new()
		add_child(_fp_body)


func _init_perlin_trauma_noise() -> void:
	if trauma_noise == null:
		trauma_noise = FastNoiseLite.new()
	trauma_noise.noise_type = FastNoiseLite.TYPE_PERLIN
	trauma_noise.seed = 1337
	trauma_noise.frequency = 1.0


func _ready() -> void:
	_rng.randomize()
	_init_perlin_trauma_noise()
	_ensure_dash_input_bindings()
	add_to_group("player")
	collision_layer = 1 | 2
	collision_mask = 1
	_gravity = float(ProjectSettings.get_setting("physics/3d/default_gravity", 9.8))
	floor_max_angle = deg_to_rad(54.0)
	floor_snap_length = 0.65
	floor_stop_on_slope = true
	floor_constant_speed = true
	floor_block_on_wall = true
	safe_margin = 0.04

	if head == null:
		head = get_node_or_null("Head") as Node3D
	if camera == null and head != null:
		camera = head.get_node_or_null("Camera3D") as Camera3D
	if camera != null:
		_default_camera_pos = camera.position
		_default_camera_fov = camera.fov if camera.fov > 10.0 else 75.0

	if DisplayServer.get_name() != "headless":
		Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)

	_setup_footstep_system()
	_setup_dash_audio()
	var found_fp_body: FirstPersonBodyController = null
	for ch: Node in get_children():
		if ch is FirstPersonBodyController:
			if found_fp_body == null:
				found_fp_body = ch as FirstPersonBodyController
			else:
				remove_child(ch)
				ch.queue_free()
	_fp_body = found_fp_body
	if _fp_body == null:
		_fp_body = FirstPersonBodyController.new()
		add_child(_fp_body)
	if surface_raycast != null:
		surface_raycast.add_exception(self)
	was_on_floor = is_on_floor()


func _ensure_dash_input_bindings() -> void:
	if InputMap.has_action("jump"):
		InputMap.action_erase_events("jump")
	if not InputMap.has_action("hunter_dash"):
		InputMap.add_action("hunter_dash")
	# Bind dodge (hunter_dash) strictly to Spacebar (KEY_SPACE) and keep CTRL/SHIFT/ALT unbound
	var existing_events: Array[InputEvent] = InputMap.action_get_events("hunter_dash")
	for ev: InputEvent in existing_events:
		if ev is InputEventKey:
			var kev_existing: InputEventKey = ev as InputEventKey
			if kev_existing.physical_keycode != KEY_SPACE and kev_existing.keycode != KEY_SPACE:
				InputMap.action_erase_event("hunter_dash", ev)
	var dash_keys: Array[Key] = [KEY_SPACE]
	for k: Key in dash_keys:
		var has_k: bool = false
		for ev: InputEvent in InputMap.action_get_events("hunter_dash"):
			if ev is InputEventKey and ((ev as InputEventKey).physical_keycode == k or (ev as InputEventKey).keycode == k):
				has_k = true
				break
		if not has_k:
			var kev: InputEventKey = InputEventKey.new()
			kev.physical_keycode = k
			kev.keycode = k
			InputMap.action_add_event("hunter_dash", kev)


func _setup_dash_audio() -> void:
	if _dash_sfx_player == null:
		_dash_sfx_player = get_node_or_null("QuickstepDashAudioPlayer") as AudioStreamPlayer
	if _dash_sfx_player == null:
		_dash_sfx_player = AudioStreamPlayer.new()
		_dash_sfx_player.name = "QuickstepDashAudioPlayer"
		_dash_sfx_player.volume_db = -1.5
		_dash_sfx_player.bus = "Master"
		add_child(_dash_sfx_player)
	if ResourceLoader.exists("res://assets/audio/sfx/hunter_quickstep_dash.wav"):
		_sfx_quickstep_dash = load("res://assets/audio/sfx/hunter_quickstep_dash.wav") as AudioStream


func _setup_footstep_system() -> void:
	# 1. Downward RayCast3D matching StaticBody3D collision layer 1
	surface_raycast = get_node_or_null("FootstepRayCast") as RayCast3D
	if surface_raycast == null:
		surface_raycast = RayCast3D.new()
		surface_raycast.name = "FootstepRayCast"
		add_child(surface_raycast)
	surface_raycast.position = Vector3(0.0, 0.5, 0.0)
	surface_raycast.target_position = Vector3(0.0, -1.6, 0.0)
	surface_raycast.collision_mask = 1
	surface_raycast.enabled = true
	surface_raycast.add_exception(self)
	_footstep_raycast = surface_raycast

	# 2. Natural-level Footstep AudioStreamPlayer at -8.0 dB
	FootstepAudioPlayer = get_node_or_null("FootstepAudioPlayer") as AudioStreamPlayer
	if FootstepAudioPlayer == null:
		FootstepAudioPlayer = get_node_or_null("FootstepPlayer") as AudioStreamPlayer
	if FootstepAudioPlayer == null:
		FootstepAudioPlayer = AudioStreamPlayer.new()
		FootstepAudioPlayer.name = "FootstepAudioPlayer"
		add_child(FootstepAudioPlayer)
	FootstepAudioPlayer.volume_db = -8.0
	FootstepAudioPlayer.bus = "Master"
	_footstep_player = FootstepAudioPlayer

	# 3. Load surface footstep banks (stone, gravel, grass, wood)
	var surfaces: Array[String] = ["stone", "gravel", "grass", "wood"]
	for surf: String in surfaces:
		var streams: Array[AudioStream] = []
		for i: int in range(1, 5):
			var path: String = "res://assets/audio/sfx/footstep_%s_0%d.wav" % [surf, i]
			var s: AudioStream = load(path) as AudioStream
			if s != null:
				streams.append(s)
		_footstep_banks[surf] = streams


func add_camera_trauma(amount: float, directional_punch: Vector3 = Vector3.ZERO) -> void:
	_init_perlin_trauma_noise()
	camera_trauma = clampf(camera_trauma + maxf(0.0, amount), 0.0, 1.0)
	if directional_punch.length_squared() > 0.000001:
		cam_punch_rot += directional_punch
		cam_punch_vel += directional_punch * 6.5
	# Sample immediately so Camera3D rotation reflects the trauma on the exact frame it is added
	noise_time += 0.19
	_sample_and_apply_camera_shake(0.0)


func _sample_and_apply_camera_shake(delta: float) -> void:
	if camera == null:
		if head == null:
			head = get_node_or_null("Head") as Node3D
		if head != null:
			camera = head.get_node_or_null("Camera3D") as Camera3D
	if camera == null:
		return

	if delta > 0.0:
		noise_time += delta * 22.0
		camera_trauma = maxf(0.0, camera_trauma - delta * 2.1)

		# Spring-damper decay for directional camera punch
		var punch_stiffness: float = 165.0
		var punch_damping: float = 15.0
		cam_punch_vel += (-punch_stiffness * cam_punch_rot - punch_damping * cam_punch_vel) * delta
		cam_punch_rot += cam_punch_vel * delta

		# Spring-damper for subconscious camera animation offsets (jump/land)
		var anim_stiffness: float = 120.0
		var anim_damping: float = 13.5
		cam_anim_pos_vel += (-anim_stiffness * cam_anim_pos_offset - anim_damping * cam_anim_pos_vel) * delta
		cam_anim_pos_offset += cam_anim_pos_vel * delta
		cam_anim_rot_vel += (-anim_stiffness * cam_anim_rot_offset - anim_damping * cam_anim_rot_vel) * delta
		cam_anim_rot_offset += cam_anim_rot_vel * delta

	var shake: float = camera_trauma * camera_trauma
	if shake > 0.000001:
		var nx: float = trauma_noise.get_noise_1d(noise_time)
		var ny: float = trauma_noise.get_noise_1d(noise_time + 100.0)
		var nz: float = trauma_noise.get_noise_1d(noise_time + 200.0)
		# Guarantee non-zero sample if noise happens to cross a zero-node at exact noise_time
		if absf(nx) < 0.001 and absf(ny) < 0.001 and absf(nz) < 0.001:
			nx = trauma_noise.get_noise_1d(noise_time + 0.31)
			ny = trauma_noise.get_noise_1d(noise_time + 100.47)
			nz = trauma_noise.get_noise_1d(noise_time + 200.63)
		cam_shake_rot_offset = Vector3(
			nx * max_pitch_shake * shake,
			ny * max_yaw_shake * shake,
			nz * max_roll_shake * shake
		)
	else:
		cam_shake_rot_offset = Vector3.ZERO

	var horizontal_speed: float = Vector2(velocity.x, velocity.z).length()
	var sprint_rot: Vector3 = Vector3.ZERO
	if is_on_floor() and horizontal_speed > 0.25:
		var sprint_factor: float = clampf(horizontal_speed / maxf(move_speed, 1.0), 0.3, 1.2)
		sprint_rot = Vector3(
			sin(_bob_time * 2.0) * deg_to_rad(0.12) * sprint_factor,
			0.0,
			cos(_bob_time) * deg_to_rad(0.18) * sprint_factor
		)

	camera.rotation = (
		cam_shake_rot_offset
		+ cam_punch_rot
		+ cam_anim_rot_offset
		+ _dash_cam_tilt_rot
		+ sprint_rot
		+ Vector3(0.0, 0.0, _strafe_tilt_z)
	)
	camera.fov = _default_camera_fov + _dash_fov_offset


func trigger_quickstep_dash(custom_dir: Vector3 = Vector3.ZERO) -> bool:
	if dash_cooldown_timer > 0.0:
		return false

	var lm: PlayerLoadoutManager = _get_loadout_manager()
	var vm: FPSViewmodelController = _get_viewmodel_controller()
	var hud_node: GothicHudOverhaul = _get_hud()

	var resolved_dir: Vector3 = custom_dir
	if resolved_dir.length_squared() <= 0.001:
		var input_dir: Vector2 = Input.get_vector("move_left", "move_right", "move_forward", "move_back")
		if input_dir.length_squared() > 0.001:
			resolved_dir = (global_transform.basis * Vector3(input_dir.x, 0.0, input_dir.y)).normalized()
		else:
			# Bloodborne Backstep along -global_transform.basis.z * -1.0 (+Z local backward)
			resolved_dir = (-global_transform.basis.z * -1.0)
			resolved_dir.y = 0.0
			if resolved_dir.length_squared() > 0.001:
				resolved_dir = resolved_dir.normalized()
			else:
				resolved_dir = Vector3(0.0, 0.0, 1.0)
	else:
		resolved_dir.y = 0.0
		resolved_dir = resolved_dir.normalized()

	dash_dir = resolved_dir
	_dash_direction = resolved_dir
	is_dashing = true
	dash_active_timer = dash_duration

	var cd_mult: float = lm.dash_cooldown_mult if lm != null else 1.0
	if lm != null and lm.quicksilver_rank > 1:
		cd_mult *= maxf(0.55, 1.0 - float(lm.quicksilver_rank - 1) * 0.04)
	dash_cooldown_timer = dash_cooldown * cd_mult
	dash_cooldown_remaining = dash_cooldown_timer

	var iframe_dur: float = 0.18
	if lm != null and lm.dash_iframe_duration > 0.18:
		iframe_dur = lm.dash_iframe_duration
	dash_iframe_timer = iframe_dur
	is_dashing_iframes = true

	# Explosive horizontal burst to dash_speed (19.5 m/s)
	velocity.x = dash_dir.x * dash_speed
	velocity.z = dash_dir.z * dash_speed

	# Camera Knee-Duck (-0.24m), Directional Dutch-Tilt (±6.5 deg side-step or -3.5 deg forward/backstep), and +7.5 deg FOV pulse
	var cur_basis: Basis = global_transform.basis if is_inside_tree() else transform.basis
	var local_dash: Vector3 = cur_basis.inverse() * dash_dir
	var roll_tilt: float = -local_dash.x * deg_to_rad(6.5)
	var pitch_tilt: float = -deg_to_rad(3.5) if absf(local_dash.z) >= absf(local_dash.x) else -deg_to_rad(1.5)
	_dash_cam_dip_y = -0.24
	_dash_cam_tilt_rot = Vector3(pitch_tilt, 0.0, roll_tilt)
	_dash_fov_offset = 7.5

	add_camera_trauma(0.18, Vector3(pitch_tilt * 0.4, 0.0, roll_tilt * 0.4))

	if _dash_sfx_player == null or _sfx_quickstep_dash == null:
		_setup_dash_audio()
	if _dash_sfx_player != null and _sfx_quickstep_dash != null:
		_dash_sfx_player.stream = _sfx_quickstep_dash
		if is_inside_tree():
			_dash_sfx_player.play()

	if vm != null:
		vm.on_quickstep_dash(dash_dir)
	if hud_node != null:
		hud_node.add_reticle_spread(16.0)

	# Immediately update camera transform so knee-dip, tilt, and FOV pulse are active right away
	if camera != null:
		camera.position = _default_camera_pos + Vector3(0.0, _dash_cam_dip_y, 0.0) + cam_anim_pos_offset
	_sample_and_apply_camera_shake(0.0)
	return true


func start_quickstep_dash(custom_dir: Vector3 = Vector3.ZERO) -> bool:
	return trigger_quickstep_dash(custom_dir)


func perform_quickstep_dash(custom_dir: Vector3 = Vector3.ZERO) -> bool:
	return trigger_quickstep_dash(custom_dir)


func take_damage(raw_damage: float) -> void:
	if is_dashing_iframes or dash_iframe_timer > 0.0:
		return
	var lm: PlayerLoadoutManager = _get_loadout_manager()
	if lm != null:
		lm.apply_player_damage(raw_damage)
	else:
		add_camera_trauma(0.45, Vector3(deg_to_rad(4.2), 0.0, deg_to_rad(2.5)))


func take_player_damage(raw_damage: float) -> void:
	take_damage(raw_damage)


func apply_player_damage(raw_damage: float) -> void:
	take_damage(raw_damage)


func _get_loadout_manager() -> PlayerLoadoutManager:
	return get_node_or_null("PlayerLoadoutManager") as PlayerLoadoutManager


func _get_viewmodel_controller() -> FPSViewmodelController:
	if camera != null:
		var vm: FPSViewmodelController = camera.get_node_or_null("ViewmodelRig") as FPSViewmodelController
		if vm != null:
			return vm
	return find_child("ViewmodelRig", true, false) as FPSViewmodelController


func _get_hud() -> GothicHudOverhaul:
	return get_node_or_null("HUD") as GothicHudOverhaul


func _is_ui_menu_open() -> bool:
	var hud_node: GothicHudOverhaul = _get_hud()
	if hud_node != null:
		if hud_node.character_menu != null and hud_node.character_menu.is_menu_open:
			return true
		if hud_node.map_system != null and hud_node.map_system.is_full_map_open:
			return true
	return false


func _unhandled_input(event: InputEvent) -> void:
	if _is_ui_menu_open():
		return
	if event.is_action_pressed("mouse_capture_toggle"):
		if Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED:
			Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
		else:
			Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)
		return

	if event.is_action_pressed("fullscreen_toggle"):
		var current_mode: DisplayServer.WindowMode = DisplayServer.window_get_mode()
		if current_mode == DisplayServer.WINDOW_MODE_FULLSCREEN or current_mode == DisplayServer.WINDOW_MODE_EXCLUSIVE_FULLSCREEN:
			DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
		else:
			DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
		return

	if event.is_action_pressed("hunter_dash"):
		trigger_quickstep_dash()
		return

	if event is InputEventMouseMotion and Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED:
		var mouse_event: InputEventMouseMotion = event as InputEventMouseMotion
		rotate_y(-mouse_event.relative.x * mouse_sensitivity)
		if head != null:
			head.rotate_x(-mouse_event.relative.y * mouse_sensitivity)
			head.rotation.x = clampf(head.rotation.x, deg_to_rad(-85.0), deg_to_rad(85.0))


func _process(delta: float) -> void:
	_sample_and_apply_camera_shake(delta)


func _physics_process(delta: float) -> void:
	if dash_cooldown_timer > 0.0:
		dash_cooldown_timer = maxf(0.0, dash_cooldown_timer - delta)
		dash_cooldown_remaining = dash_cooldown_timer

	if dash_iframe_timer > 0.0:
		dash_iframe_timer = maxf(0.0, dash_iframe_timer - delta)
		is_dashing_iframes = dash_iframe_timer > 0.0
	else:
		is_dashing_iframes = false

	var menu_open: bool = _is_ui_menu_open()

	if not menu_open and Input.is_action_just_pressed("hunter_dash") and dash_cooldown_timer <= 0.0:
		trigger_quickstep_dash()

	var on_floor_before: bool = is_on_floor()
	var jumping: bool = false
	is_jumping = false
	if not on_floor_before:
		prev_vertical_velocity = velocity.y
		velocity.y -= _gravity * delta
	elif velocity.y > 0.0:
		velocity.y = 0.0

	var input_dir: Vector2 = Vector2.ZERO if menu_open else Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var move_dir: Vector3 = (global_transform.basis * Vector3(input_dir.x, 0.0, input_dir.y)).normalized()

	# Subtle Strafe Tilt opposite to horizontal input (-input_dir.x * deg_to_rad(0.85))
	var target_strafe_tilt: float = -input_dir.x * deg_to_rad(0.85)
	_strafe_tilt_z = lerpf(_strafe_tilt_z, target_strafe_tilt, clampf(delta * 10.0, 0.0, 1.0))

	if is_dashing:
		dash_active_timer -= delta
		var dash_elapsed: float = dash_duration - maxf(0.0, dash_active_timer)
		if dash_elapsed <= 0.14:
			# First 0.14s: maintain explosive 19.5 m/s quickstep burst
			velocity.x = dash_dir.x * dash_speed
			velocity.z = dash_dir.z * dash_speed
		else:
			# Final 0.08s: smooth exponential friction brake exp(-delta * 16.0)
			var brake: float = exp(-delta * 16.0)
			velocity.x *= brake
			velocity.z *= brake

		# Animate Camera Knee-Duck, Dutch-Tilt & FOV Pulse over the 0.22s dash
		var dash_t: float = clampf(dash_elapsed / maxf(dash_duration, 0.01), 0.0, 1.0)
		var env_curve: float = sin(dash_t * PI)
		var local_d: Vector3 = global_transform.basis.inverse() * dash_dir
		var r_tilt: float = -local_d.x * deg_to_rad(6.5) * env_curve
		var p_tilt: float = (-deg_to_rad(3.5) if absf(local_d.z) >= absf(local_d.x) else -deg_to_rad(1.5)) * env_curve
		_dash_cam_dip_y = -0.24 * env_curve
		_dash_cam_tilt_rot = Vector3(p_tilt, 0.0, r_tilt)
		_dash_fov_offset = 7.5 * env_curve

		if dash_active_timer <= 0.0:
			is_dashing = false
			dash_active_timer = 0.0
			_dash_cam_dip_y = 0.0
			_dash_cam_tilt_rot = Vector3.ZERO
			_dash_fov_offset = 0.0
	else:
		_dash_cam_dip_y = lerpf(_dash_cam_dip_y, 0.0, clampf(delta * 16.0, 0.0, 1.0))
		_dash_cam_tilt_rot = _dash_cam_tilt_rot.lerp(Vector3.ZERO, clampf(delta * 16.0, 0.0, 1.0))
		_dash_fov_offset = lerpf(_dash_fov_offset, 0.0, clampf(delta * 16.0, 0.0, 1.0))

		if is_on_floor():
			var current_accel: float = acceleration if move_dir.length_squared() > 0.001 else deceleration
			velocity.x = move_toward(velocity.x, move_dir.x * move_speed, current_accel * delta)
			velocity.z = move_toward(velocity.z, move_dir.z * move_speed, current_accel * delta)
		else:
			# Phase 3.3: Airborne Momentum Preservation (low air-drag when jumping out of Quickstep or off balconies)
			var horiz_vel: Vector2 = Vector2(velocity.x, velocity.z)
			var preserved_speed: float = maxf(move_speed, horiz_vel.length())
			if move_dir.length_squared() > 0.001:
				var air_target: Vector2 = Vector2(move_dir.x, move_dir.z) * preserved_speed
				horiz_vel = horiz_vel.move_toward(air_target, acceleration * 0.55 * delta)
			else:
				horiz_vel = horiz_vel.move_toward(Vector2.ZERO, air_deceleration * delta)
			velocity.x = horiz_vel.x
			velocity.z = horiz_vel.y

	move_and_slide()

	if (was_on_floor or on_floor_before) and not is_jumping and velocity.y <= 0.0:
		apply_floor_snap()

	if (is_on_floor() or on_floor_before) and not is_jumping:
		var has_move_intent: bool = input_dir.length() > 0.1 or Vector2(velocity.x, velocity.z).length() > 0.15
		if has_move_intent:
			_apply_stair_step_up_assist(move_dir)

	var on_floor_after: bool = is_on_floor()
	if not was_on_floor and on_floor_after:
		_on_heavy_landing(prev_vertical_velocity)
		prev_vertical_velocity = 0.0
	was_on_floor = on_floor_after

	# Keep velocity.y <= 0.0 while grounded unless jumping so sloped terrain never launches the player
	if on_floor_after and not jumping and velocity.y > 0.0:
		velocity.y = 0.0

	_update_head_bob(delta)
	_update_footsteps(delta)
	if _fp_body != null and is_instance_valid(_fp_body):
		var cam_pitch: float = head.rotation.x if head != null else 0.0
		_fp_body.update_body_motion(delta, velocity, rotation.y, cam_pitch, is_on_floor(), is_dashing)


func _apply_stair_step_up_assist(move_dir: Vector3 = Vector3.ZERO) -> void:
	if not is_inside_tree() or get_world_3d() == null:
		return
	var space_state: PhysicsDirectSpaceState3D = get_world_3d().direct_space_state
	if space_state == null:
		return

	var horiz_dir: Vector3 = Vector3(move_dir.x, 0.0, move_dir.z)
	if horiz_dir.length_squared() < 0.001:
		horiz_dir = Vector3(velocity.x, 0.0, velocity.z)
	if horiz_dir.length_squared() < 0.001:
		return
	horiz_dir = horiz_dir.normalized()

	var exclude_rids: Array[RID] = [get_rid()]
	var base_pos: Vector3 = global_position

	# Cast clear ray at knee height (Y + 0.55m) ahead by 0.58m
	var knee_from: Vector3 = base_pos + Vector3(0.0, 0.55, 0.0)
	var knee_to: Vector3 = knee_from + horiz_dir * 0.58
	var knee_query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(knee_from, knee_to, 1, exclude_rids)
	var knee_hit: Dictionary = space_state.intersect_ray(knee_query)
	if not knee_hit.is_empty():
		var k_norm: Vector3 = knee_hit.get("normal", Vector3.UP) as Vector3
		# If knee height hits a vertical wall (not a walkable slope), do not step up
		if k_norm.y < cos(floor_max_angle):
			return

	# Cast short horizontal rays at foot/ankle height (Y + 0.05m and Y + 0.28m and Y + 0.44m) ahead by 0.55m
	var ankle_blocked: bool = false
	for h_off: float in [0.05, 0.24, 0.44]:
		var ankle_from: Vector3 = base_pos + Vector3(0.0, h_off, 0.0)
		var ankle_to: Vector3 = ankle_from + horiz_dir * 0.55
		var ankle_query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(ankle_from, ankle_to, 1, exclude_rids)
		var ankle_hit: Dictionary = space_state.intersect_ray(ankle_query)
		if not ankle_hit.is_empty():
			var a_norm: Vector3 = ankle_hit.get("normal", Vector3.UP) as Vector3
			# Blocked by a lip or vertical riser (normal is steeper than floor_max_angle or player is on wall)
			if a_norm.y < 0.68 or is_on_wall():
				ankle_blocked = true
				break

	if ankle_blocked and (is_on_wall() or is_on_floor()):
		# Verify clear headroom before nudging up
		var head_from: Vector3 = base_pos + Vector3(0.0, 1.50, 0.0)
		var head_to: Vector3 = head_from + Vector3(0.0, 0.45, 0.0) + horiz_dir * 0.35
		var head_query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(head_from, head_to, 1, exclude_rids)
		if space_state.intersect_ray(head_query).is_empty():
			global_position.y += 0.38
			global_position += horiz_dir * 0.08
			apply_floor_snap()


func _on_jump_takeoff() -> void:
	# Jump Take-off Impulse: upward pitch (+2.8 deg), downward viewmodel dip (-0.04m), +0.10 trauma
	cam_anim_rot_offset.x += deg_to_rad(2.8)
	cam_anim_rot_vel.x += deg_to_rad(14.0)
	add_camera_trauma(0.10, Vector3(deg_to_rad(2.8), 0.0, 0.0))
	var vm: FPSViewmodelController = _get_viewmodel_controller()
	if vm != null:
		vm.on_jump_takeoff()


func _on_heavy_landing(fall_vel_y: float) -> void:
	var impact: float = clampf(absf(fall_vel_y) / 12.0, 0.2, 1.0)
	var roll_sign: float = 1.0 if _rng.randf() >= 0.5 else -1.0
	cam_anim_pos_offset.y -= 0.16 * impact
	cam_anim_pos_vel.y -= 0.85 * impact
	cam_anim_rot_offset.x -= deg_to_rad(5.5) * impact
	cam_anim_rot_offset.z += deg_to_rad(2.0) * impact * roll_sign
	add_camera_trauma(0.25 * impact, Vector3(-deg_to_rad(5.5) * impact, 0.0, deg_to_rad(2.0) * impact * roll_sign))
	var vm: FPSViewmodelController = _get_viewmodel_controller()
	if vm != null:
		vm.on_landing_impact(impact)


func _update_head_bob(delta: float) -> void:
	if camera == null:
		return
	var horizontal_speed: float = Vector2(velocity.x, velocity.z).length()
	var bob_offset: Vector3 = Vector3.ZERO
	if is_on_floor() and horizontal_speed > 0.25 and not is_dashing:
		_bob_time += delta * horizontal_speed * bob_frequency
		var offset_y: float = sin(_bob_time) * bob_amplitude
		var offset_x: float = cos(_bob_time * 0.5) * bob_amplitude * 0.5
		bob_offset = Vector3(offset_x, offset_y, 0.0)
	else:
		_bob_time = 0.0

	var target_cam_pos: Vector3 = _default_camera_pos + bob_offset + cam_anim_pos_offset + Vector3(0.0, _dash_cam_dip_y, 0.0)
	camera.position = camera.position.lerp(target_cam_pos, clampf(delta * 18.0, 0.0, 1.0))


func _update_footsteps(delta: float) -> void:
	if step_cooldown_timer > 0.0:
		step_cooldown_timer = maxf(0.0, step_cooldown_timer - delta)

	if not is_on_floor():
		return

	var horizontal_speed: float = Vector2(velocity.x, velocity.z).length()
	if horizontal_speed <= 0.35:
		_step_distance_accum = minf(_step_distance_accum, step_stride_distance * 0.5)
		return

	_step_distance_accum += horizontal_speed * delta
	var is_sprinting: bool = horizontal_speed > (move_speed * 1.15)
	var min_cooldown: float = 0.30 if is_sprinting else 0.44

	if _step_distance_accum >= step_stride_distance and step_cooldown_timer <= 0.0:
		_step_distance_accum = 0.0
		step_cooldown_timer = min_cooldown
		_play_footstep_sound()


func detect_surface() -> String:
	return _detect_floor_surface()


func get_current_surface() -> String:
	return _detect_floor_surface()


func _detect_floor_surface() -> String:
	var pos: Vector3 = global_position
	# Check downward RayCast3D collider hierarchy first
	if surface_raycast != null:
		surface_raycast.force_raycast_update()
		if surface_raycast.is_colliding():
			var col_obj: Object = surface_raycast.get_collider()
			if col_obj is Node and col_obj != self:
				var curr: Node = col_obj as Node
				while curr != null:
					if curr.has_meta("surface_type"):
						return str(curr.get_meta("surface_type"))
					var cname: String = curr.name.to_lower()
					if cname.contains("church") or cname.contains("crypt") or cname.contains("stair") or cname.contains("floor") or cname.contains("plinth"):
						return "stone"
					if cname.contains("house") or cname.contains("wood"):
						return "wood"
					curr = curr.get_parent()

	# Inside church or subterranean crypt (Z <= -11.5)
	if pos.z <= -11.5:
		return "stone"

	# Outside (Z > -11.5): valley road (abs(x) <= 4.2) is gravel; surrounding hills (abs(x) > 4.2) are grass
	if absf(pos.x) <= 4.2:
		return "gravel"
	return "grass"


func _play_footstep_sound() -> void:
	footstep_count += 1
	if _footstep_player == null:
		return
	var surface: String = _detect_floor_surface()
	var bank: Array = _footstep_banks.get(surface, []) as Array
	if bank.is_empty():
		return

	var idx: int = _rng.randi_range(0, bank.size() - 1)
	if bank.size() > 1 and idx == _last_step_index:
		idx = (idx + 1) % bank.size()
	_last_step_index = idx

	var stream: AudioStream = bank[idx] as AudioStream
	if stream == null:
		return

	var in_reverb_zone: bool = global_position.z <= -11.5 and (global_position.y < 3.2 or absf(global_position.x) <= 6.5)
	if in_reverb_zone and AudioServer.get_bus_index("CryptReverb") != -1:
		_footstep_player.bus = "CryptReverb"
	else:
		_footstep_player.bus = "Master"

	_footstep_player.volume_db = -8.0
	_footstep_player.pitch_scale = _rng.randf_range(0.94, 1.06)
	_footstep_player.stream = stream
	_footstep_player.play()
