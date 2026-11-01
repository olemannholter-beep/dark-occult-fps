class_name AmbientSoundscapeController
extends Node3D

@export var player_node: Node3D
@export var crossfade_speed: float = 3.2

var _wind_player: AudioStreamPlayer = null
var _church_draft_player: AudioStreamPlayer = null
var _crypt_drone_player: AudioStreamPlayer = null
var _bell_player_3d: AudioStreamPlayer3D = null
var _drip_player_3d: AudioStreamPlayer3D = null

var _bell_timer: float = 14.0
var _drip_timer: float = 4.5
var _rng: RandomNumberGenerator = RandomNumberGenerator.new()

var gunfire_duck_timer: float = 0.0
var gunfire_duck_duration: float = 0.45
var gunfire_duck_offset_db: float = 0.0


func trigger_gunfire_duck(duck_db: float = -9.0, duration: float = 0.45) -> void:
	gunfire_duck_duration = maxf(0.05, duration)
	gunfire_duck_timer = gunfire_duck_duration
	gunfire_duck_offset_db = duck_db
	if _wind_player != null:
		_wind_player.volume_db -= absf(duck_db)
	if _church_draft_player != null:
		_church_draft_player.volume_db -= absf(duck_db)
	if _crypt_drone_player != null:
		_crypt_drone_player.volume_db -= absf(duck_db)



func _ready() -> void:
	_rng.randomize()
	_ensure_crypt_reverb_bus()
	_discover_player()
	_setup_audio_players()


func _ensure_crypt_reverb_bus() -> void:
	var bus_idx: int = AudioServer.get_bus_index("CryptReverb")
	if bus_idx == -1:
		bus_idx = AudioServer.bus_count
		AudioServer.add_bus(bus_idx)
		AudioServer.set_bus_name(bus_idx, "CryptReverb")
		AudioServer.set_bus_send(bus_idx, "Master")

		var reverb: AudioEffectReverb = AudioEffectReverb.new()
		reverb.room_size = 0.86
		reverb.damping = 0.35
		reverb.spread = 0.90
		reverb.wet = 0.48
		reverb.dry = 0.72
		AudioServer.add_bus_effect(bus_idx, reverb)


func _discover_player() -> void:
	if player_node != null and is_instance_valid(player_node):
		return
	if get_tree() != null:
		var grp_node: Node = get_tree().get_first_node_in_group("player")
		if grp_node is Node3D:
			player_node = grp_node as Node3D
			return
		var root_node: Node = get_tree().current_scene if get_tree().current_scene != null else get_tree().root
		if root_node != null:
			var found_fps: Node = root_node.find_child("FPSPlayer", true, false)
			if found_fps is Node3D:
				player_node = found_fps as Node3D
				return
			var found_p: Node = root_node.find_child("Player", true, false)
			if found_p is Node3D:
				player_node = found_p as Node3D
				return


func _configure_loop_stream(path: String) -> AudioStreamWAV:
	var stream: AudioStreamWAV = load(path) as AudioStreamWAV
	if stream != null:
		stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
		stream.loop_begin = 0
		var bytes_per_sample: int = 2 if stream.format == AudioStreamWAV.FORMAT_16_BITS else 1
		var channels: int = 2 if stream.stereo else 1
		var divisor: int = max(1, bytes_per_sample * channels)
		stream.loop_end = int(stream.data.size() / divisor)
	return stream


func _setup_audio_players() -> void:
	# 1. Exterior Moorland Wind Loop (capped at -18.0 dB outside)
	_wind_player = get_node_or_null("WindPlayer") as AudioStreamPlayer
	if _wind_player == null:
		_wind_player = AudioStreamPlayer.new()
		_wind_player.name = "WindPlayer"
		add_child(_wind_player)
	_wind_player.stream = _configure_loop_stream("res://assets/audio/ambient/ambient_moor_wind_loop.wav")
	_wind_player.volume_db = -18.0
	_wind_player.bus = "Master"
	if _wind_player.stream != null and not _wind_player.playing:
		_wind_player.play()

	# 2. Cathedral Nave Draft Loop
	_church_draft_player = get_node_or_null("ChurchDraftPlayer") as AudioStreamPlayer
	if _church_draft_player == null:
		_church_draft_player = AudioStreamPlayer.new()
		_church_draft_player.name = "ChurchDraftPlayer"
		add_child(_church_draft_player)
	_church_draft_player.stream = _configure_loop_stream("res://assets/audio/ambient/ambient_church_draft_loop.wav")
	_church_draft_player.volume_db = -36.0
	_church_draft_player.bus = "Master"
	if _church_draft_player.stream != null and not _church_draft_player.playing:
		_church_draft_player.play()

	# 3. Underground Crypt Drone Loop
	_crypt_drone_player = get_node_or_null("CryptDronePlayer") as AudioStreamPlayer
	if _crypt_drone_player == null:
		_crypt_drone_player = AudioStreamPlayer.new()
		_crypt_drone_player.name = "CryptDronePlayer"
		add_child(_crypt_drone_player)
	_crypt_drone_player.stream = _configure_loop_stream("res://assets/audio/ambient/ambient_crypt_drone_loop.wav")
	_crypt_drone_player.volume_db = -60.0
	_crypt_drone_player.bus = "CryptReverb"
	if _crypt_drone_player.stream != null and not _crypt_drone_player.playing:
		_crypt_drone_player.play()

	# 4. 3D Bell Tower Toll Player inside church_bell_tower_spire
	_bell_player_3d = get_node_or_null("BellPlayer3D") as AudioStreamPlayer3D
	if _bell_player_3d == null:
		_bell_player_3d = AudioStreamPlayer3D.new()
		_bell_player_3d.name = "BellPlayer3D"
		add_child(_bell_player_3d)
	_bell_player_3d.position = Vector3(0.0, 22.0, -14.0)
	_bell_player_3d.stream = load("res://assets/audio/sfx/cathedral_bell_distant.wav") as AudioStream
	_bell_player_3d.unit_size = 18.0
	_bell_player_3d.max_distance = 120.0
	_bell_player_3d.volume_db = -4.0
	_bell_player_3d.bus = "Master"

	# 5. 3D Crypt Water Drip & Stone Settle Randomizer Player
	_drip_player_3d = get_node_or_null("DripPlayer3D") as AudioStreamPlayer3D
	if _drip_player_3d == null:
		_drip_player_3d = AudioStreamPlayer3D.new()
		_drip_player_3d.name = "DripPlayer3D"
		add_child(_drip_player_3d)

	var randomizer: AudioStreamRandomizer = AudioStreamRandomizer.new()
	randomizer.random_pitch = 1.08
	randomizer.random_volume_offset_db = 1.0
	var drip_paths: Array[String] = [
		"res://assets/audio/sfx/crypt_water_drip_01.wav",
		"res://assets/audio/sfx/crypt_water_drip_02.wav",
		"res://assets/audio/sfx/crypt_water_drip_03.wav",
	]
	var weights: Array[float] = [1.0, 1.0, 1.0]
	for i: int in range(drip_paths.size()):
		var s: AudioStream = load(drip_paths[i]) as AudioStream
		if s != null:
			randomizer.add_stream(i, s, weights[i])

	_drip_player_3d.stream = randomizer
	_drip_player_3d.unit_size = 5.0
	_drip_player_3d.max_distance = 24.0
	_drip_player_3d.volume_db = -11.0
	_drip_player_3d.bus = "CryptReverb"


func _process(delta: float) -> void:
	if player_node == null or not is_instance_valid(player_node):
		_discover_player()

	var p_pos: Vector3 = Vector3.ZERO
	if player_node != null and is_instance_valid(player_node):
		p_pos = player_node.global_position
	elif get_viewport() != null and get_viewport().get_camera_3d() != null:
		p_pos = get_viewport().get_camera_3d().global_position
	else:
		return

	_update_zone_crossfades(p_pos, delta)
	_update_stingers(p_pos, delta)


func _update_zone_crossfades(p_pos: Vector3, delta: float) -> void:
	var target_wind_db: float = -18.0
	var target_church_db: float = -36.0
	var target_crypt_db: float = -60.0

	var in_church_zone: bool = (
		p_pos.x >= -14.5 and p_pos.x <= 14.5
		and p_pos.z <= -11.5
	)

	if p_pos.z <= -11.5 and p_pos.y < 3.2:
		# Zone 3 — Subterranean Gothic Labyrinth (Y = 0.0m -> Y = -4.0m -> Y = -8.0m):
		# Mute exterior wind to -60.0 dB and intensify deep crypt sub-bass drone with depth
		target_wind_db = -60.0
		var upper_t: float = clampf((3.2 - p_pos.y) / 3.2, 0.0, 1.0)
		var deep_t: float = clampf((0.0 - p_pos.y) / 8.0, 0.0, 1.0)
		target_church_db = lerpf(-18.0, -52.0, clampf(upper_t + deep_t * 0.5, 0.0, 1.0))
		if p_pos.y >= 0.0:
			target_crypt_db = lerpf(-16.0, -8.0, upper_t)
		else:
			# Intensify sub-bass drone from -8.0 dB at Y=0.0m -> -4.5 dB at Y=-4.0m -> -1.0 dB at Y=-8.0m
			target_crypt_db = lerpf(-8.0, -1.0, deep_t)
		if _crypt_drone_player != null:
			var target_pitch: float = lerpf(1.0, 0.85, deep_t)
			_crypt_drone_player.pitch_scale = lerpf(_crypt_drone_player.pitch_scale, target_pitch, clampf(delta * crossfade_speed, 0.0, 1.0))
	elif in_church_zone:
		# Zone 2 — Cathedral Nave (Z < -11.5, Y >= 3.2): drop wind to -36.0 dB
		target_wind_db = -36.0
		target_church_db = -14.0
		var stair_dist: float = Vector2(p_pos.x, p_pos.z - (-20.0)).length()
		var stair_prox: float = clampf(1.0 - (stair_dist / 9.5), 0.0, 1.0)
		target_crypt_db = lerpf(-45.0, -20.0, stair_prox)
	else:
		# Zone 1 — Exterior Overworld: cap exterior wind at -18.0 dB
		target_wind_db = -18.0
		target_church_db = -38.0
		target_crypt_db = -60.0

	if gunfire_duck_timer > 0.0:
		gunfire_duck_timer = maxf(0.0, gunfire_duck_timer - delta)
		gunfire_duck_offset_db = lerpf(0.0, -9.0, gunfire_duck_timer / maxf(gunfire_duck_duration, 0.05))
	else:
		gunfire_duck_offset_db = 0.0

	target_wind_db += gunfire_duck_offset_db
	target_church_db += gunfire_duck_offset_db
	target_crypt_db += gunfire_duck_offset_db

	var step: float = clampf(delta * crossfade_speed, 0.0, 1.0)
	if _wind_player != null:
		_wind_player.volume_db = lerpf(_wind_player.volume_db, target_wind_db, step)
	if _church_draft_player != null:
		_church_draft_player.volume_db = lerpf(_church_draft_player.volume_db, target_church_db, step)
	if _crypt_drone_player != null:
		_crypt_drone_player.volume_db = lerpf(_crypt_drone_player.volume_db, target_crypt_db, step)


func _update_stingers(p_pos: Vector3, delta: float) -> void:
	# 1. Distant Cathedral Bell Toll every 22.0 - 40.0s
	_bell_timer -= delta
	if _bell_timer <= 0.0:
		_bell_timer = _rng.randf_range(22.0, 40.0)
		if _bell_player_3d != null and _bell_player_3d.stream != null and p_pos.y >= 2.5:
			_bell_player_3d.pitch_scale = _rng.randf_range(0.96, 1.03)
			_bell_player_3d.play()

	# 2. Dynamic 3D Positional Water Drips & Masonry Groans within a 14m radius around the player across the subterranean labyrinth
	if p_pos.z < -11.5:
		_drip_timer -= delta
		if _drip_timer <= 0.0:
			_drip_timer = _rng.randf_range(3.0, 7.5)
			if _drip_player_3d != null and _drip_player_3d.stream != null:
				var angle: float = _rng.randf_range(0.0, TAU)
				var dist: float = _rng.randf_range(3.5, 14.0)
				_drip_player_3d.global_position = Vector3(
					p_pos.x + cos(angle) * dist,
					p_pos.y + _rng.randf_range(0.2, 3.2),
					p_pos.z + sin(angle) * dist
				)
				_drip_player_3d.play()
