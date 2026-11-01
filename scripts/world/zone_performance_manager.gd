class_name ZonePerformanceManager
extends Node3D

@export var check_interval: float = 0.10

var player_node: Node3D = null
var town_root: Node3D = null
var crypt_root: Node3D = null
var town_exterior_zone: Node3D = null
var church_workshop_zone: Node3D = null
var crypt_portal_nexus_zone: Node3D = null
var procedural_expedition_root: Node3D = null
var moon_light: DirectionalLight3D = null

var _timer: float = 0.0
var _active_zone: int = -1
var _crypt_chambers: Array[Node3D] = []
var _crypt_chamber_centers: Array[Vector3] = []


func _ready() -> void:
	_discover_nodes()
	if player_node != null and is_instance_valid(player_node):
		evaluate_zones_now(player_node.global_position)


func _discover_nodes() -> void:
	var scene_root: Node = get_parent()
	if scene_root == null:
		return
	if player_node == null or not is_instance_valid(player_node):
		player_node = scene_root.find_child("Player", true, false) as Node3D
		if player_node == null:
			player_node = scene_root.find_child("FPSPlayer", true, false) as Node3D
	if town_root == null:
		town_root = scene_root.find_child("TownRoot", true, false) as Node3D
	if crypt_root == null:
		crypt_root = scene_root.find_child("CryptRoot", true, false) as Node3D
	if town_exterior_zone == null:
		town_exterior_zone = scene_root.find_child("TownExteriorZone", true, false) as Node3D
	if church_workshop_zone == null:
		church_workshop_zone = scene_root.find_child("ChurchWorkshopZone", true, false) as Node3D
	if crypt_portal_nexus_zone == null:
		crypt_portal_nexus_zone = scene_root.find_child("CryptPortalNexusZone", true, false) as Node3D
	if procedural_expedition_root == null:
		procedural_expedition_root = scene_root.find_child("ProceduralExpeditionRoot", true, false) as Node3D
	if moon_light == null:
		moon_light = scene_root.find_child("MoonDirectionalLight", true, false) as DirectionalLight3D

	if _crypt_chambers.is_empty() and crypt_portal_nexus_zone != null:
		var chamber_defs: Array[Dictionary] = [
			{"name": "Chamber1_OssuaryHub", "center": Vector3(0.0, 0.0, -28.0)},
			{"name": "Chamber2_InquisitorHall", "center": Vector3(-20.0, 0.0, -28.0)},
			{"name": "Chamber3_ForbiddenLibrary", "center": Vector3(20.0, 0.0, -28.0)},
			{"name": "Chamber4_PlagueCistern", "center": Vector3(-20.0, 0.0, -48.0)},
			{"name": "Chamber5_BlightedCatacomb", "center": Vector3(-20.0, -4.0, -68.0)},
			{"name": "Chamber6_WeepingSaintHalls", "center": Vector3(0.0, -4.0, -48.0)},
			{"name": "Chamber7_SunkenBellTower", "center": Vector3(20.0, -8.0, -48.0)},
			{"name": "Chamber8_AbyssalSanctum", "center": Vector3(0.0, -8.0, -72.0)}
		]
		for def: Dictionary in chamber_defs:
			var ch_name: String = def["name"] as String
			var ch_node: Node3D = crypt_portal_nexus_zone.find_child(ch_name, true, false) as Node3D
			if ch_node != null:
				_crypt_chambers.append(ch_node)
				_crypt_chamber_centers.append(def["center"] as Vector3)


func _process(delta: float) -> void:
	_timer += delta
	if _timer < check_interval:
		return
	_timer = 0.0

	if player_node == null or not is_instance_valid(player_node):
		_discover_nodes()
		if player_node == null or not is_instance_valid(player_node):
			return

	evaluate_zones_now(player_node.global_position)


func evaluate_zones_now(pos: Vector3) -> void:
	_discover_nodes()

	# Phase 1.2: Never hide TownRoot or CryptRoot while the player is anywhere in the Hub (pos.y > -100.0).
	# Only hide TownRoot and CryptRoot when the player teleports into the Procedural Dungeon (pos.y <= -100.0).
	var in_hub: bool = pos.y > -100.0
	var in_dungeon: bool = not in_hub
	_active_zone = 0 if in_hub else 3

	_set_zone_active(town_root, in_hub)
	_set_zone_active(crypt_root, in_hub)
	_set_zone_active(town_exterior_zone, in_hub)
	_set_zone_active(church_workshop_zone, in_hub)
	_set_zone_active(crypt_portal_nexus_zone, in_hub)
	_set_zone_active(procedural_expedition_root, in_dungeon)

	for i: int in range(_crypt_chambers.size()):
		var ch: Node3D = _crypt_chambers[i]
		if ch != null and is_instance_valid(ch):
			if ch.visible != in_hub:
				ch.visible = in_hub
			var ch_mode: Node.ProcessMode = Node.PROCESS_MODE_INHERIT if in_hub else Node.PROCESS_MODE_DISABLED
			if ch.process_mode != ch_mode:
				ch.process_mode = ch_mode

	if moon_light != null and is_instance_valid(moon_light):
		moon_light.visible = in_hub
		moon_light.shadow_enabled = in_hub and (pos.y > -0.5 or pos.z > -19.5)


func _set_zone_active(zone: Node3D, active: bool) -> void:
	if zone == null or not is_instance_valid(zone):
		return
	if zone.visible != active:
		zone.visible = active
	var target_mode: Node.ProcessMode = Node.PROCESS_MODE_INHERIT if active else Node.PROCESS_MODE_DISABLED
	if zone.process_mode != target_mode:
		zone.process_mode = target_mode
