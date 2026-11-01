class_name SanctuaryForgeStation
extends StaticBody3D

@export var station_type: String = "weapon"
@export var station_title: String = "The Gunsmith's Arsenal Forge"

var current_tier_index: int = 0
var _sfx_player: AudioStreamPlayer3D = null
var _sfx_clank: AudioStream = null
var _sfx_chime: AudioStream = null


func _ready() -> void:
	collision_layer = 1
	collision_mask = 1
	set_meta("surface_type", "stone")
	if ResourceLoader.exists("res://assets/audio/sfx/ui_armor_equip_clank.wav"):
		_sfx_clank = load("res://assets/audio/sfx/ui_armor_equip_clank.wav") as AudioStream
	if ResourceLoader.exists("res://assets/audio/sfx/ui_skill_consecrate_chime.wav"):
		_sfx_chime = load("res://assets/audio/sfx/ui_skill_consecrate_chime.wav") as AudioStream
	_sfx_player = AudioStreamPlayer3D.new()
	_sfx_player.name = "ForgeStationAudio3D"
	_sfx_player.unit_size = 6.0
	_sfx_player.max_distance = 18.0
	add_child(_sfx_player)


func get_prompt_text(_loadout: Node = null) -> String:
	match station_type:
		"weapon":
			return "%s\n[E] OPEN ARSENAL FORGE (CRAFT WEAPONS & RITE MODS)" % station_title
		"armor":
			return "%s\n[E] OPEN ARMORY RELIQUARY (FORGE GAUNTLETS & VESTMENTS)" % station_title
		"upgrade":
			return "%s\n[E] COMMUNE WITH ASTROLABE (LANTERN SPELLS, HEAL & SKILL TREE)" % station_title
		_:
			return "%s\n[E] OPEN SANCTUARY FORGE" % station_title


func interact(loadout_or_player: Node = null) -> void:
	if loadout_or_player == null:
		return
	var loadout: Node = loadout_or_player
	if not (loadout is PlayerLoadoutManager) and loadout_or_player.has_node("PlayerLoadoutManager"):
		loadout = loadout_or_player.get_node("PlayerLoadoutManager")

	if station_type == "upgrade":
		if loadout.has_method("restore_full_vitality_and_armor"):
			loadout.call("restore_full_vitality_and_armor")
		if _sfx_player != null and _sfx_chime != null and is_inside_tree():
			_sfx_player.stream = _sfx_chime
			_sfx_player.pitch_scale = 1.0
			_sfx_player.play()
	else:
		if _sfx_player != null and _sfx_clank != null and is_inside_tree():
			_sfx_player.stream = _sfx_clank
			_sfx_player.pitch_scale = 0.96 if station_type == "weapon" else 1.04
			_sfx_player.play()

	var char_menu: GothicCharacterMenu = _find_character_menu(loadout)
	if char_menu != null:
		_close_legacy_overlays_and_prompts(loadout, char_menu)
		char_menu.open_at_forge_station(station_type)


func cycle_option(loadout: Node) -> void:
	interact(loadout)


func _close_legacy_overlays_and_prompts(loadout: Node, active_menu: GothicCharacterMenu) -> void:
	if loadout is PlayerLoadoutManager:
		var lm: PlayerLoadoutManager = loadout as PlayerLoadoutManager
		if lm.hud != null:
			lm.hud.set_interaction_prompt("", false)
			if lm.hud.map_system != null and lm.hud.map_system.is_full_map_open:
				lm.hud.map_system.is_full_map_open = false
				lm.hud.map_system.queue_redraw()
			for child: Node in lm.hud.get_children():
				if child is GothicCharacterMenu and child != active_menu:
					lm.hud.remove_child(child)
					child.queue_free()
				elif child.name.begins_with("LegacyStation") or child.name.begins_with("StationPopup"):
					lm.hud.remove_child(child)
					child.queue_free()


func _find_character_menu(loadout: Node) -> GothicCharacterMenu:
	if loadout is PlayerLoadoutManager:
		var lm: PlayerLoadoutManager = loadout as PlayerLoadoutManager
		if lm.hud != null and lm.hud.character_menu != null:
			return lm.hud.character_menu
	var p: Node = loadout.get_parent() if (loadout is PlayerLoadoutManager) else loadout
	if p != null:
		for mname: String in ["GothicCharacterMenu", "CharacterMenu"]:
			var menu: GothicCharacterMenu = p.find_child(mname, true, false) as GothicCharacterMenu
			if menu != null:
				return menu
	if get_tree() != null and get_tree().current_scene != null:
		for mname: String in ["GothicCharacterMenu", "CharacterMenu"]:
			var scene_menu: GothicCharacterMenu = get_tree().current_scene.find_child(mname, true, false) as GothicCharacterMenu
			if scene_menu != null:
				return scene_menu
	if get_tree() != null and get_tree().root != null:
		for mname: String in ["GothicCharacterMenu", "CharacterMenu"]:
			var root_menu: GothicCharacterMenu = get_tree().root.find_child(mname, true, false) as GothicCharacterMenu
			if root_menu != null:
				return root_menu
	return null
