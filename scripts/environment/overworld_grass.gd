@tool
class_name OverworldGrass
extends MultiMeshInstance3D

@export var grass_mesh: Mesh
@export var grass_material: Material
@export var instance_count_target: int = 12000
@export var seed_val: int = 1337
@export var regenerate_now: bool = false:
	set(val):
		if val:
			generate_grass()


func _ready() -> void:
	generate_grass()


func _smoothstep(edge0: float, edge1: float, x: float) -> float:
	if is_equal_approx(edge0, edge1):
		return 0.0
	var t: float = clampf((x - edge0) / (edge1 - edge0), 0.0, 1.0)
	return t * t * (3.0 - 2.0 * t)


func _get_terrain_height(gx: float, gz: float) -> float:
	var hills: float = (
		1.45 * sin(gx * 0.05) * cos(gz * 0.045)
		+ 0.95 * cos((gx + 15.0) * 0.08) * sin((gz - 8.0) * 0.075)
		+ 0.25 * sin(gx * 0.14 + gz * 0.13)
	)
	var edge_ridge: float = 0.0030 * (gx * gx)
	var north_slope: float = _smoothstep(20.0, -22.0, gz) * 3.4
	var base_h: float = maxf(0.0, 0.55 + hills * 0.60 + edge_ridge + north_slope)

	var road_z_factor: float = _smoothstep(48.0, 34.0, gz) * _smoothstep(-14.5, -9.0, gz)
	var road_x_dist: float = absf(gx - 1.2 * sin(gz * 0.09))
	var road_mask: float = (1.0 - _smoothstep(4.5, 11.5, road_x_dist)) * road_z_factor
	var road_progress: float = _smoothstep(26.0, -10.2, gz)
	var road_h: float = 0.15 + road_progress * (3.20 - 0.15)

	var dist_ha: float = Vector2((gx - (-16.0)) / 1.1, (gz - 14.0) / 1.2).length()
	var mask_ha: float = 1.0 - _smoothstep(5.5, 11.5, dist_ha)
	var h_ha: float = 0.85

	var dist_hb: float = Vector2((gx - 16.0) / 1.1, (gz - 8.0) / 1.2).length()
	var mask_hb: float = 1.0 - _smoothstep(5.5, 11.5, dist_hb)
	var h_hb: float = 1.15

	var box_dx: float = maxf(0.0, absf(gx) - 15.0)
	var box_dz: float = maxf(0.0, gz - (-9.0)) if gz > -22.0 else maxf(0.0, (-59.0) - gz)
	var dist_church: float = Vector2(box_dx, box_dz).length()
	var mask_church: float = 1.0 - _smoothstep(0.5, 10.5, dist_church)
	var church_ramp: float = _smoothstep(-9.5, -12.2, gz)
	var h_church: float = 3.20 + church_ramp * (3.55 - 3.20)

	var h: float = base_h
	h = h * (1.0 - road_mask) + road_h * road_mask
	h = h * (1.0 - mask_ha) + h_ha * mask_ha
	h = h * (1.0 - mask_hb) + h_hb * mask_hb
	h = h * (1.0 - mask_church) + h_church * mask_church
	return h


func _get_terrain_normal(gx: float, gz: float) -> Vector3:
	var eps: float = 0.15
	var hl: float = _get_terrain_height(gx - eps, gz)
	var hr: float = _get_terrain_height(gx + eps, gz)
	var hd: float = _get_terrain_height(gx, gz - eps)
	var hu: float = _get_terrain_height(gx, gz + eps)
	var norm: Vector3 = Vector3(hl - hr, 2.0 * eps, hd - hu).normalized()
	return norm


func generate_grass() -> void:
	if grass_mesh == null:
		var glb: PackedScene = load("res://assets/models/grass_clump_wild.glb") as PackedScene
		if glb != null:
			var inst: Node3D = glb.instantiate() as Node3D
			for child: Node in inst.get_children():
				if child is MeshInstance3D:
					grass_mesh = (child as MeshInstance3D).mesh
					break
			inst.free()

	if grass_mesh == null:
		return

	if grass_material == null:
		var sh: Shader = load("res://shaders/wind_grass.gdshader") as Shader
		if sh != null:
			var sm: ShaderMaterial = ShaderMaterial.new()
			sm.shader = sh
			grass_material = sm

	if multimesh == null:
		multimesh = MultiMesh.new()
	else:
		multimesh.instance_count = 0

	multimesh.transform_format = MultiMesh.TRANSFORM_3D
	multimesh.mesh = grass_mesh
	if grass_material != null:
		material_override = grass_material

	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	visibility_range_end = 55.0
	visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF

	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = seed_val

	multimesh.instance_count = instance_count_target

	# Prepare float buffer for Godot 4 MultiMesh (12 floats per instance: 3x4 matrix)
	var buf: PackedFloat32Array = PackedFloat32Array()
	buf.resize(instance_count_target * 12)

	var placed: int = 0
	var attempts: int = 0

	while placed < instance_count_target and attempts < 160000:
		attempts += 1
		var gx: float = rng.randf_range(-52.0, 52.0)
		var gz: float = rng.randf_range(-52.0, 48.0)

		# Exclusion 1: Muddy valley road (abs(gx) < 4.5 along path gz between -11.5 and 44.0)
		var road_x_dist: float = absf(gx - 1.2 * sin(gz * 0.09))
		if road_x_dist < 4.5 and gz >= -11.5 and gz <= 44.0:
			continue

		# Exclusion 2: Church building, transept wings & plaza footprint
		if absf(gx) < 15.2 and gz >= -59.5 and gz <= -11.0:
			continue

		# Exclusion 3: House A footprint (gx = -16.0, gz = 14.0)
		if Vector2(gx - (-16.0), gz - 14.0).length() < 6.8:
			continue

		# Exclusion 4: House B footprint (gx = 16.0, gz = 8.0)
		if Vector2(gx - 16.0, gz - 8.0).length() < 6.8:
			continue

		var hy: float = _get_terrain_height(gx, gz)
		var normal: Vector3 = _get_terrain_normal(gx, gz)

		var scale_val: float = rng.randf_range(0.75, 1.35)
		var rand_ang: float = rng.randf_range(0.0, TAU)
		var tangent: Vector3 = Vector3(cos(rand_ang), 0.0, sin(rand_ang))
		var binormal: Vector3 = normal.cross(tangent).normalized()
		tangent = binormal.cross(normal).normalized()

		var basis: Basis = Basis(tangent * scale_val, normal * scale_val, binormal * scale_val)
		var trans: Transform3D = Transform3D(basis, Vector3(gx, hy, gz))
		multimesh.set_instance_transform(placed, trans)

		# Populate buffer float array: [basis.x.x, basis.x.y, basis.x.z, origin.x, ...]
		var base_idx: int = placed * 12
		buf[base_idx + 0] = trans.basis.x.x
		buf[base_idx + 1] = trans.basis.x.y
		buf[base_idx + 2] = trans.basis.x.z
		buf[base_idx + 3] = trans.origin.x

		buf[base_idx + 4] = trans.basis.y.x
		buf[base_idx + 5] = trans.basis.y.y
		buf[base_idx + 6] = trans.basis.y.z
		buf[base_idx + 7] = trans.origin.y

		buf[base_idx + 8] = trans.basis.z.x
		buf[base_idx + 9] = trans.basis.z.y
		buf[base_idx + 10] = trans.basis.z.z
		buf[base_idx + 11] = trans.origin.z

		placed += 1

	if placed < instance_count_target:
		multimesh.instance_count = placed
		buf.resize(placed * 12)

	multimesh.buffer = buf
