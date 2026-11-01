class_name TargetDummyPlaque
extends StaticBody3D

@export var plaque_title: String = "Sanctuary Target Plaque"
var total_damage_logged: float = 0.0
var last_hit_damage: float = 0.0
var _readout_label: Label3D = null


func _ready() -> void:
	set_meta("surface_type", "stone")
	_ensure_readout_label()


func _ensure_readout_label() -> void:
	var existing: Label3D = get_node_or_null("PlaqueReadoutLabel") as Label3D
	if existing != null:
		_readout_label = existing
		return
	_readout_label = Label3D.new()
	_readout_label.name = "PlaqueReadoutLabel"
	_readout_label.position = Vector3(0.0, 2.35, 0.0)
	_readout_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_readout_label.font_size = 28
	_readout_label.outline_size = 8
	_readout_label.modulate = Color(1.0, 0.84, 0.42, 0.92)
	_readout_label.text = "%s\n[Ready for Ballistics Test]" % plaque_title
	add_child(_readout_label)


func take_damage(
	amount: float,
	_armor_piercing: bool = false,
	hit_pos: Vector3 = Vector3.ZERO,
	_hit_normal: Vector3 = Vector3.UP,
	_weapon_mod: String = ""
) -> float:
	if amount <= 0.0:
		return 0.0
	last_hit_damage = amount
	total_damage_logged += amount
	_ensure_readout_label()
	if _readout_label != null:
		_readout_label.text = "%s\nLast Hit: %.0f DMG  |  Total: %.0f DMG" % [
			plaque_title,
			last_hit_damage,
			total_damage_logged
		]
	_spawn_floating_damage_number(amount, hit_pos)
	return amount


func apply_damage(amount: float, armor_piercing: bool = false) -> float:
	return take_damage(amount, armor_piercing, global_position + Vector3(0.0, 1.4, 0.0))


func _spawn_floating_damage_number(amount: float, hit_pos: Vector3) -> void:
	if not is_inside_tree():
		return
	var pop_lbl: Label3D = Label3D.new()
	pop_lbl.name = "FloatingDamageNumber"
	pop_lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	pop_lbl.no_depth_test = true
	pop_lbl.font_size = 36
	pop_lbl.outline_size = 10
	pop_lbl.modulate = Color(1.0, 0.36, 0.22, 1.0)
	pop_lbl.text = "-%d" % roundi(amount)
	add_child(pop_lbl)
	var local_start: Vector3 = Vector3(
		randf_range(-0.28, 0.28),
		1.55 + randf_range(-0.12, 0.22),
		0.35
	)
	if hit_pos != Vector3.ZERO:
		local_start = to_local(hit_pos) + Vector3(randf_range(-0.18, 0.18), 0.25, 0.0)
	pop_lbl.position = local_start

	var tw: Tween = pop_lbl.create_tween()
	tw.tween_property(pop_lbl, "position", local_start + Vector3(0.0, 0.65, 0.0), 0.55)
	tw.parallel().tween_property(pop_lbl, "modulate:a", 0.0, 0.55)
	tw.tween_callback(pop_lbl.queue_free)
