class_name GrimdarkMaterialLibrary
extends RefCounted

static var _material_cache: Dictionary[String, StandardMaterial3D] = {}


static func _create_matte_standard_material(
	albedo: Color,
	roughness_val: float,
	metallic_val: float = 0.0,
	specular_val: float = 0.15,
	use_vertex_color: bool = true
) -> StandardMaterial3D:
	var mat: StandardMaterial3D = StandardMaterial3D.new()
	mat.albedo_color = albedo
	mat.roughness = roughness_val
	mat.metallic = metallic_val
	mat.metallic_specular = specular_val
	mat.vertex_color_use_as_albedo = use_vertex_color
	mat.normal_enabled = false
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	return mat


static func get_dark_containment_hull_stone() -> StandardMaterial3D:
	const KEY: String = "dark_containment_hull_stone"
	if _material_cache.has(KEY):
		return _material_cache[KEY]

	var mat: StandardMaterial3D = _create_matte_standard_material(
		Color(0.06, 0.06, 0.08, 1.0),
		0.95,
		0.0,
		0.08,
		true
	)
	mat.cull_mode = BaseMaterial3D.CULL_BACK
	_material_cache[KEY] = mat
	return mat


static func get_weathered_ashlar_stone() -> StandardMaterial3D:
	const KEY: String = "weathered_ashlar_stone"
	if _material_cache.has(KEY):
		return _material_cache[KEY]

	var mat: StandardMaterial3D = _create_matte_standard_material(
		Color(0.32, 0.30, 0.28, 1.0),
		0.92,
		0.0,
		0.15,
		true
	)
	_material_cache[KEY] = mat
	return mat


static func get_rough_cobble_flagstone() -> StandardMaterial3D:
	const KEY: String = "rough_cobble_flagstone"
	if _material_cache.has(KEY):
		return _material_cache[KEY]

	var mat: StandardMaterial3D = _create_matte_standard_material(
		Color(0.24, 0.23, 0.22, 1.0),
		0.72,
		0.0,
		0.25,
		true
	)
	_material_cache[KEY] = mat
	return mat


static func get_carved_stone_trim() -> StandardMaterial3D:
	const KEY: String = "carved_stone_trim"
	if _material_cache.has(KEY):
		return _material_cache[KEY]

	var mat: StandardMaterial3D = _create_matte_standard_material(
		Color(0.36, 0.34, 0.32, 1.0),
		0.84,
		0.0,
		0.18,
		true
	)
	_material_cache[KEY] = mat
	return mat


static func get_candle_wax() -> StandardMaterial3D:
	const KEY: String = "candle_wax"
	if _material_cache.has(KEY):
		return _material_cache[KEY]

	var mat: StandardMaterial3D = _create_matte_standard_material(
		Color(0.76, 0.68, 0.50, 1.0),
		0.56,
		0.0,
		0.22,
		true
	)
	_material_cache[KEY] = mat
	return mat


static func get_candle_flame_glow() -> StandardMaterial3D:
	const KEY: String = "candle_flame_glow"
	if _material_cache.has(KEY):
		return _material_cache[KEY]

	var mat: StandardMaterial3D = _create_matte_standard_material(
		Color(1.0, 0.72, 0.24, 1.0),
		0.15,
		0.0,
		0.20,
		true
	)
	mat.emission_enabled = true
	mat.emission = Color(1.0, 0.65, 0.18, 1.0)
	mat.emission_energy_multiplier = 4.2
	_material_cache[KEY] = mat
	return mat


static func get_rotted_charred_timber() -> StandardMaterial3D:
	const KEY: String = "rotted_charred_timber"
	if _material_cache.has(KEY):
		return _material_cache[KEY]

	var mat: StandardMaterial3D = _create_matte_standard_material(
		Color(0.20, 0.14, 0.10, 1.0),
		0.88,
		0.0,
		0.15,
		true
	)
	_material_cache[KEY] = mat
	return mat


static func get_tarnished_wrought_iron() -> StandardMaterial3D:
	const KEY: String = "tarnished_wrought_iron"
	if _material_cache.has(KEY):
		return _material_cache[KEY]

	var mat: StandardMaterial3D = _create_matte_standard_material(
		Color(0.14, 0.14, 0.16, 1.0),
		0.48,
		0.85,
		0.45,
		true
	)
	_material_cache[KEY] = mat
	return mat


static func get_tarnished_bronze() -> StandardMaterial3D:
	const KEY: String = "tarnished_bronze"
	if _material_cache.has(KEY):
		return _material_cache[KEY]

	var mat: StandardMaterial3D = _create_matte_standard_material(
		Color(0.28, 0.23, 0.14, 1.0),
		0.46,
		0.85,
		0.45,
		true
	)
	_material_cache[KEY] = mat
	return mat


static func get_aged_bone() -> StandardMaterial3D:
	const KEY: String = "aged_bone"
	if _material_cache.has(KEY):
		return _material_cache[KEY]

	var mat: StandardMaterial3D = _create_matte_standard_material(
		Color(0.62, 0.57, 0.46, 1.0),
		0.88,
		0.0,
		0.15,
		true
	)
	_material_cache[KEY] = mat
	return mat


static func get_glowing_occult_rune() -> StandardMaterial3D:
	const KEY: String = "glowing_occult_rune"
	if _material_cache.has(KEY):
		return _material_cache[KEY]

	var mat: StandardMaterial3D = _create_matte_standard_material(
		Color(0.48, 0.20, 0.62, 1.0),
		0.36,
		0.0,
		0.15,
		true
	)
	mat.emission_enabled = true
	mat.emission = Color(0.68, 0.26, 0.88, 1.0)
	mat.emission_energy_multiplier = 0.85
	_material_cache[KEY] = mat
	return mat


static func get_sickly_green_bile() -> StandardMaterial3D:
	const KEY: String = "sickly_green_bile"
	if _material_cache.has(KEY):
		return _material_cache[KEY]

	var mat: StandardMaterial3D = _create_matte_standard_material(
		Color(0.42, 0.90, 0.30, 1.0),
		0.24,
		0.0,
		0.25,
		true
	)
	mat.emission_enabled = true
	mat.emission = Color(0.45, 0.95, 0.35, 1.0)
	mat.emission_energy_multiplier = 2.4
	_material_cache[KEY] = mat
	return mat


static func get_frozen_blue_soul() -> StandardMaterial3D:
	const KEY: String = "frozen_blue_soul"
	if _material_cache.has(KEY):
		return _material_cache[KEY]

	var mat: StandardMaterial3D = _create_matte_standard_material(
		Color(0.35, 0.70, 1.0, 1.0),
		0.26,
		0.0,
		0.25,
		true
	)
	mat.emission_enabled = true
	mat.emission = Color(0.35, 0.65, 1.0, 1.0)
	mat.emission_energy_multiplier = 2.6
	_material_cache[KEY] = mat
	return mat


static func get_abyssal_crimson() -> StandardMaterial3D:
	const KEY: String = "abyssal_crimson"
	if _material_cache.has(KEY):
		return _material_cache[KEY]

	var mat: StandardMaterial3D = _create_matte_standard_material(
		Color(0.95, 0.12, 0.15, 1.0),
		0.28,
		0.0,
		0.20,
		true
	)
	mat.emission_enabled = true
	mat.emission = Color(1.0, 0.15, 0.18, 1.0)
	mat.emission_energy_multiplier = 3.0
	_material_cache[KEY] = mat
	return mat


static func get_dark_cistern_water() -> StandardMaterial3D:
	const KEY: String = "dark_cistern_water"
	if _material_cache.has(KEY):
		return _material_cache[KEY]

	var mat: StandardMaterial3D = _create_matte_standard_material(
		Color(0.05, 0.09, 0.12, 1.0),
		0.14,
		0.15,
		0.65,
		true
	)
	_material_cache[KEY] = mat
	return mat


static func get_consecrated_gold_liquid() -> StandardMaterial3D:
	const KEY: String = "consecrated_gold_liquid"
	if _material_cache.has(KEY):
		return _material_cache[KEY]

	var mat: StandardMaterial3D = _create_matte_standard_material(
		Color(1.0, 0.78, 0.24, 1.0),
		0.20,
		0.35,
		0.45,
		true
	)
	mat.emission_enabled = true
	mat.emission = Color(1.0, 0.72, 0.18, 1.0)
	mat.emission_energy_multiplier = 2.8
	_material_cache[KEY] = mat
	return mat


static func get_occult_silver() -> StandardMaterial3D:
	const KEY: String = "occult_silver"
	if _material_cache.has(KEY):
		return _material_cache[KEY]

	var mat: StandardMaterial3D = _create_matte_standard_material(
		Color(0.58, 0.60, 0.64, 1.0),
		0.36,
		0.88,
		0.45,
		true
	)
	_material_cache[KEY] = mat
	return mat


static func get_dark_slate_roof() -> StandardMaterial3D:
	const KEY: String = "dark_slate_roof"
	if _material_cache.has(KEY):
		return _material_cache[KEY]

	var mat: StandardMaterial3D = _create_matte_standard_material(
		Color(0.18, 0.19, 0.22, 1.0),
		0.89,
		0.0,
		0.15,
		true
	)
	_material_cache[KEY] = mat
	return mat


static func get_dirty_plaster() -> StandardMaterial3D:
	const KEY: String = "dirty_plaster"
	if _material_cache.has(KEY):
		return _material_cache[KEY]

	var mat: StandardMaterial3D = _create_matte_standard_material(
		Color(0.38, 0.35, 0.31, 1.0),
		0.93,
		0.0,
		0.12,
		true
	)
	_material_cache[KEY] = mat
	return mat


static func get_terrain_moor_grass() -> StandardMaterial3D:
	const KEY: String = "terrain_moor_grass"
	if _material_cache.has(KEY):
		return _material_cache[KEY]

	var mat: StandardMaterial3D = _create_matte_standard_material(
		Color(0.15, 0.17, 0.12, 1.0),
		0.94,
		0.0,
		0.12,
		true
	)
	_material_cache[KEY] = mat
	return mat


static func get_terrain_mud_path() -> StandardMaterial3D:
	const KEY: String = "terrain_mud_path"
	if _material_cache.has(KEY):
		return _material_cache[KEY]

	var mat: StandardMaterial3D = _create_matte_standard_material(
		Color(0.18, 0.15, 0.12, 1.0),
		0.91,
		0.0,
		0.15,
		true
	)
	_material_cache[KEY] = mat
	return mat


static func get_terrain_cliff_stone() -> StandardMaterial3D:
	const KEY: String = "terrain_cliff_stone"
	if _material_cache.has(KEY):
		return _material_cache[KEY]

	var mat: StandardMaterial3D = _create_matte_standard_material(
		Color(0.24, 0.23, 0.24, 1.0),
		0.92,
		0.0,
		0.15,
		true
	)
	_material_cache[KEY] = mat
	return mat


static func get_lead_glass_window() -> StandardMaterial3D:
	const KEY: String = "lead_glass_window"
	if _material_cache.has(KEY):
		return _material_cache[KEY]

	var mat: StandardMaterial3D = _create_matte_standard_material(
		Color(0.18, 0.22, 0.28, 0.85),
		0.22,
		0.15,
		0.35,
		true
	)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.emission_enabled = true
	mat.emission = Color(0.12, 0.16, 0.26, 1.0)
	mat.emission_energy_multiplier = 0.65
	_material_cache[KEY] = mat
	return mat


static func get_material_for_name(mat_name: String) -> Material:
	var lower_name: String = mat_name.to_lower()

	# 1. Catacomb emissive & specialty materials (with vertex_color_use_as_albedo = true, normal_enabled = false)
	if lower_name.contains("containmenthull"):
		return get_dark_containment_hull_stone()
	if lower_name.contains("glowingoccultrune") or lower_name.contains("violetrune") or lower_name.contains("runes"):
		return get_glowing_occult_rune()
	if lower_name.contains("sicklygreenbile") or lower_name.contains("bile"):
		return get_sickly_green_bile()
	if lower_name.contains("frozenbluesoul") or lower_name.contains("soul") or lower_name.contains("tear"):
		return get_frozen_blue_soul()
	if lower_name.contains("abyssalcrimson") or lower_name.contains("crimson"):
		return get_abyssal_crimson()
	if lower_name.contains("cisternwater") or lower_name.contains("water"):
		return get_dark_cistern_water()
	if lower_name.contains("agedbone") or lower_name.contains("bone") or lower_name.contains("skull"):
		return get_aged_bone()
	if lower_name.contains("consecratedgold") or lower_name.contains("gold"):
		return get_consecrated_gold_liquid()
	if lower_name.contains("occultsilver") or lower_name.contains("silver"):
		return get_occult_silver()
	if lower_name.contains("candleflame") or lower_name.contains("flameglow") or lower_name.contains("amberflame") or lower_name.contains("flame") or lower_name.contains("ember"):
		return get_candle_flame_glow()
	if lower_name.contains("candlewax") or lower_name.contains("wax") or lower_name.contains("candle"):
		return get_candle_wax()
	if lower_name.contains("carvedstonetrim") or lower_name.contains("trim"):
		return get_carved_stone_trim()
	if lower_name.contains("glass") or lower_name.contains("leadglass") or lower_name.contains("stained"):
		return get_lead_glass_window()

	# 3. Terrain specific
	if lower_name.contains("moor") or lower_name.contains("moorgrass"):
		return get_terrain_moor_grass()
	if lower_name.contains("mud") or lower_name.contains("mudpath") or lower_name.contains("road"):
		return get_terrain_mud_path()
	if lower_name.contains("cliff") or lower_name.contains("crag"):
		return get_terrain_cliff_stone()

	# 4. Slate Roof
	if lower_name.contains("roof") or lower_name.contains("slate"):
		return get_dark_slate_roof()

	# 5. Plaster
	if lower_name.contains("plaster") or lower_name.contains("daub"):
		return get_dirty_plaster()

	# 6. Timber, Planks, Bark
	if lower_name.contains("timber") or lower_name.contains("plank") or lower_name.contains("board") or lower_name.contains("wood") or lower_name.contains("bark"):
		return get_rotted_charred_timber()

	# 7. Metals (Iron / Bronze)
	if lower_name.contains("bronze") or lower_name.contains("brass") or lower_name.contains("bell"):
		return get_tarnished_bronze()
	if lower_name.contains("iron") or lower_name.contains("metal") or lower_name.contains("cage") or lower_name.contains("brazier") or lower_name.contains("sconce"):
		return get_tarnished_wrought_iron()

	# 8. Floors / Steps / Dais / Flagstones
	if lower_name.contains("flagstone") or lower_name.contains("step") or lower_name.contains("tile") or lower_name.contains("slab") or lower_name.contains("dais") or lower_name.contains("altar"):
		return get_rough_cobble_flagstone()

	# 9. Default stone masonry (walls, pillars, foundation plinth, trim)
	return get_weathered_ashlar_stone()
