class_name TorchFlicker
extends OmniLight3D

@export var flicker_speed: float = 7.5
@export var energy_variation: float = 0.28
@export var position_jitter: float = 0.025

var _base_energy: float = 1.8
var _base_position: Vector3 = Vector3.ZERO
var _time_acc: float = 0.0
var _phase_offset: float = 0.0
var _crackle_player: AudioStreamPlayer3D = null


func _ready() -> void:
	_base_energy = light_energy
	_base_position = position
	_phase_offset = absf(global_position.x * 1.73 + global_position.z * 2.41 + global_position.y * 0.97)
	_setup_fire_crackle_offset()


func _setup_fire_crackle_offset() -> void:
	var parent_node: Node = get_parent()
	if parent_node == null:
		return
	var crackle: AudioStreamPlayer3D = parent_node.get_node_or_null("FireCrackle3D") as AudioStreamPlayer3D
	if crackle == null:
		return
	_crackle_player = crackle
	_crackle_player.max_polyphony = 2
	_crackle_player.max_distance = 10.0

	if crackle.stream is AudioStreamWAV:
		var wav: AudioStreamWAV = crackle.stream as AudioStreamWAV
		wav.loop_mode = AudioStreamWAV.LOOP_FORWARD
		wav.loop_begin = 0
		var bytes_per_sample: int = 2 if wav.format == AudioStreamWAV.FORMAT_16_BITS else 1
		var channels: int = 2 if wav.stereo else 1
		var divisor: int = max(1, bytes_per_sample * channels)
		wav.loop_end = int(wav.data.size() / divisor)
		var len_sec: float = maxf(0.1, wav.get_length())
		var start_offset: float = fmod(_phase_offset * 1.37, len_sec)
		crackle.play(start_offset)


func _process(delta: float) -> void:
	var vp: Viewport = get_viewport()
	if vp != null:
		var cam: Camera3D = vp.get_camera_3d()
		if cam != null:
			var dist_sq: float = global_position.distance_squared_to(cam.global_position)
			if dist_sq > 484.0:
				if _crackle_player != null and not _crackle_player.stream_paused:
					_crackle_player.stream_paused = true
				return
			elif _crackle_player != null and _crackle_player.stream_paused:
				_crackle_player.stream_paused = false

	_time_acc += delta * flicker_speed
	var t: float = _time_acc + _phase_offset
	var wave: float = (
		sin(t * 1.0) * 0.50
		+ sin(t * 2.37 + 1.2) * 0.30
		+ cos(t * 4.13 + 0.7) * 0.20
	)
	light_energy = maxf(0.15, _base_energy + wave * energy_variation)
	var offset_x: float = sin(t * 1.9) * position_jitter
	var offset_y: float = cos(t * 2.7) * position_jitter * 0.6
	var offset_z: float = cos(t * 1.4) * position_jitter
	position = _base_position + Vector3(offset_x, offset_y, offset_z)
