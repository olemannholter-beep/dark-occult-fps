class_name FPSPlayer
extends FPSController


func _init() -> void:
	super._init()
	floor_max_angle = deg_to_rad(54.0)
	floor_snap_length = 0.65
	floor_stop_on_slope = true
	floor_constant_speed = true
	floor_block_on_wall = true
	safe_margin = 0.04


func _ready() -> void:
	super._ready()
	floor_max_angle = deg_to_rad(54.0)
	floor_snap_length = 0.65
	floor_stop_on_slope = true
	floor_constant_speed = true
	floor_block_on_wall = true
	safe_margin = 0.04
	if _fp_body == null:
		_fp_body = FirstPersonBodyController.new()
		add_child(_fp_body)


func _physics_process(delta: float) -> void:
	super._physics_process(delta)
	if _fp_body != null and is_instance_valid(_fp_body):
		var cam_pitch: float = head.rotation.x if head != null else 0.0
		_fp_body.update_body_motion(delta, velocity, rotation.y, cam_pitch, is_on_floor(), is_dashing)
