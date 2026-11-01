class_name FPSViewmodelController
extends Node3D

signal ammo_changed(current: int, max_val: int)
signal spell_cast(spell_index: int, spell_name: String)

@export var left_hand_pivot: Node3D
@export var right_hand_pivot: Node3D
@export var lantern_light: OmniLight3D
@export var muzzle_flash_light: OmniLight3D
@export var muzzle_particles: GPUParticles3D
@export var wall_raycast: RayCast3D
@export var hitscan_raycast: RayCast3D

# Handheld Lantern Glow & Falloff Reach (Inspector Tweakable)
@export_range(10.0, 60.0, 0.5) var lantern_base_range: float = 26.0
@export_range(14.0, 75.0, 0.5) var lantern_raised_range: float = 34.0
@export_range(0.5, 5.0, 0.05) var lantern_base_energy: float = 2.35
@export_range(0.3, 2.0, 0.05) var lantern_attenuation: float = 0.82

var loadout_manager: PlayerLoadoutManager = null

# Walk/Sprint Figure-8 Bob parameters (subtle, grounded stride)
@export var bob_freq: float = 7.2
@export var bob_horiz_amp: float = 0.008
@export var bob_vert_amp: float = 0.010
@export var bob_roll_deg: float = 1.0

# Mouse Sway parameters
@export var max_sway: float = 0.032
@export var rot_sway_deg: float = 4.0
@export var sway_smooth: float = 12.0
@export var strafe_tilt_deg: float = 1.2
@export var wall_tuck_distance: float = 1.1

# Pendulum physics parameters (±20 deg swing)
@export var pendulum_spring: float = 28.0
@export var pendulum_damping: float = 3.2
@export var pendulum_accel_sensitivity: float = 0.18
@export var max_pendulum_angle_deg: float = 20.0

# Combat & 6-DOF Underdamped Spring Recoil parameters
@export var max_ammo: int = 6
@export var fire_cooldown: float = 0.28
@export var recoil_recovery_duration: float = 0.22
@export var stiffness: float = 180.0
@export var damping: float = 14.5

var active_weapon_id: String = "revolver"
var ammo_by_weapon: Dictionary[String, int] = {
	"revolver": 6,
	"shotgun": 2,
	"stakedriver": 4
}
var max_ammo_by_weapon: Dictionary[String, int] = {
	"revolver": 6,
	"shotgun": 2,
	"stakedriver": 4
}

var current_ammo: int = 6
var shots_fired_total: int = 0
var _fire_cooldown_remaining: float = 0.0
var _is_reloading: bool = false
var _reload_timer: float = 0.0
var _reload_duration_total: float = 0.75
var _reload_beat1_done: bool = false
var _reload_beat2_done: bool = false
var _reload_beat3_done: bool = false
var _shotgun_close_sfx_played: bool = false
var _is_lantern_raised: bool = false
var _was_lantern_raised: bool = false

# Active Left-Hand Lantern Occult Abilities ([F] to cast, [G] to cycle)
var active_spell_index: int = 0
var base_ability_cooldown: float = 6.0
var ability_cooldown_remaining: float = 0.0
var _spell_flare_timer: float = 0.0
var _spell_flare_color: Color = Color(1.0, 0.72, 0.28, 1.0)
var _ability_sfx_player: AudioStreamPlayer = null
var _weapon_sfx_player: AudioStreamPlayer = null
var _weapon_sfx_secondary: AudioStreamPlayer = null
var _sfx_pyre_blast: AudioStream = null
var _sfx_soul_chains: AudioStream = null
var _sfx_blood_nova: AudioStream = null
var _sfx_revolver_fire: AudioStreamRandomizer = null
var _sfx_revolver_cock: AudioStreamRandomizer = null
var _sfx_revolver_reload: AudioStreamRandomizer = null
var _sfx_revolver_dry_fire: AudioStreamRandomizer = null
var _sfx_shotgun_fire: AudioStreamRandomizer = null
var _sfx_shotgun_break: AudioStreamRandomizer = null
var _sfx_shotgun_close: AudioStreamRandomizer = null
var _sfx_stakedriver_fire: AudioStreamRandomizer = null
var _sfx_stakedriver_cleave: AudioStream = null
var _sfx_weapon_swap: AudioStream = null
var _sfx_locked_clink: AudioStream = null

# Dynamic Ambient Sidechain Ducking (-9.0 dB restored over 0.45s on gunfire)
var _ambient_soundscape: AmbientSoundscapeController = null
var _ambient_duck_timer: float = 0.0
var _ambient_duck_duration: float = 0.45
var _ambient_duck_offset_db: float = 0.0

# Base rest transforms for LeftHandPivot and RightHandPivot
var left_base_pos: Vector3 = Vector3(-0.31, -0.28, -0.42)
var left_base_rot: Vector3 = Vector3.ZERO
var right_base_pos: Vector3 = Vector3(0.24, -0.21, -0.40)
var right_base_rot: Vector3 = Vector3.ZERO
var left_raised_pos: Vector3 = Vector3(-0.24, -0.18, -0.36)

# Additive sway, walk-bob, and recoil offsets integrated directly in _process(delta)
var sway_pos: Vector3 = Vector3.ZERO
var sway_rot: Vector3 = Vector3.ZERO
var _sway_target_pos: Vector3 = Vector3.ZERO
var _sway_target_rot: Vector3 = Vector3.ZERO

var bob_phase: float = 0.0
var bob_pos: Vector3 = Vector3.ZERO
var bob_rot: Vector3 = Vector3.ZERO
var left_bob_pos: Vector3 = Vector3.ZERO
var left_bob_rot: Vector3 = Vector3.ZERO

# Phase 2.1: 6-DOF Underdamped Spring Recoil (Position + Rotation + Velocities)
var recoil_pos: Vector3 = Vector3.ZERO
var recoil_vel: Vector3 = Vector3.ZERO
var recoil_rot: Vector3 = Vector3.ZERO
var recoil_rot_vel: Vector3 = Vector3.ZERO

var recoil_offset_pos: Vector3 = Vector3.ZERO
var recoil_offset_rot: Vector3 = Vector3.ZERO
var left_recoil_offset_pos: Vector3 = Vector3.ZERO
var left_recoil_vel: Vector3 = Vector3.ZERO

var _weapon_mount_recoil_pos: Vector3 = Vector3.ZERO
var _weapon_mount_recoil_rot: Vector3 = Vector3.ZERO
var _weapon_recoil_tween: Tween = null

var _tuck_offset: Vector3 = Vector3.ZERO
var _tuck_rot_x: float = 0.0
var _rng: RandomNumberGenerator = RandomNumberGenerator.new()

# Internal tracking & node references
var _player: CharacterBody3D = null
var _idle_timer: float = 0.0

# Pendulum simulation state
var _pendulum_angle_x: float = 0.0
var _pendulum_angle_z: float = 0.0
var _pendulum_vel_x: float = 0.0
var _pendulum_vel_z: float = 0.0
var _last_player_vel: Vector3 = Vector3.ZERO
var _last_cam_basis: Basis = Basis.IDENTITY
var _has_last_cam_basis: bool = false

# Sub-components in GLB viewmodels
var _lantern_pendulum: Node3D = null
var weapon_revolver: Node3D = null
var weapon_shotgun: Node3D = null
var weapon_stakedriver: Node3D = null

var _revolver_cylinder: Node3D = null
var _revolver_hammer: Node3D = null
var _revolver_trigger: Node3D = null
var _revolver_side_gear: Node3D = null
var _revolver_ejector_rod: Node3D = null
var _muzzle_anchor: Node3D = null

var _shotgun_barrel_assembly: Node3D = null
var _shotgun_shell_left: Node3D = null
var _shotgun_shell_right: Node3D = null
var _shotgun_hammer_left: Node3D = null
var _shotgun_hammer_right: Node3D = null
var _shotgun_top_lever: Node3D = null
var _shotgun_shell_left_default_z: float = 0.0
var _shotgun_shell_right_default_z: float = 0.0

var _driver_stake_ram: Node3D = null
var _driver_flywheel: Node3D = null
var _driver_loading_crank: Node3D = null
var _driver_ram_default_z: float = 0.0
var _driver_ram_timer: float = 0.0
var _driver_flywheel_target_angle: float = 0.0
var _driver_crank_target_angle: float = 0.0

var left_arm_gauntlet: Node3D = null
var right_arm_gauntlet: Node3D = null
var equipped_armor_index: int = 0
var active_gauntlet_instance: Node3D = null
var active_right_gauntlet_instance: Node3D = null
var active_gauntlet_model_path: String = ""

const ARMOR_GAUNTLET_PREFABS: Array[String] = [
	"res://scenes/prefabs/armor/gauntlet_01_leather_stalker.tscn",
	"res://scenes/prefabs/armor/gauntlet_02_inquisitor_brigandine.tscn",
	"res://scenes/prefabs/armor/gauntlet_03_juggernaut_plate.tscn",
	"res://scenes/prefabs/armor/gauntlet_04_abyssal_reliquary.tscn"
]

const ARMOR_GAUNTLET_GLBS: Array[String] = [
	"res://assets/models/armor/gauntlet_01_leather_stalker.glb",
	"res://assets/models/armor/gauntlet_02_inquisitor_brigandine.glb",
	"res://assets/models/armor/gauntlet_03_juggernaut_plate.glb",
	"res://assets/models/armor/gauntlet_04_abyssal_reliquary.glb"
]

var _revolver_rune_materials: Array[StandardMaterial3D] = []
var _gauntlet_plate_materials: Array[StandardMaterial3D] = []
var _gauntlet_leather_materials: Array[StandardMaterial3D] = []
var _gauntlet_trim_materials: Array[StandardMaterial3D] = []

var reload_speed_mult: float = 1.0
var recoil_mult: float = 1.0
var lantern_range_bonus: float = 0.0
var lantern_energy_bonus: float = 0.0
var active_rune_color: Color = Color(1.0, 0.14, 0.28, 1.0)
var active_armor_plate_color: Color = Color(0.18, 0.19, 0.21, 1.0)
var _active_plate_metallic: float = 0.86
var _active_plate_roughness: float = 0.36
var _active_trim_color: Color = Color(0.55, 0.43, 0.24, 1.0)
var _active_leather_color: Color = Color(0.16, 0.10, 0.08, 1.0)
var _has_custom_armor_tier: bool = false

var cylinder_target_angle: float = 0.0
var _gear_target_angle: float = 0.0
var _ejector_default_z: float = 0.0
var _hammer_snap_timer: float = 0.0
var _trigger_snap_timer: float = 0.0
var _ejector_snap_timer: float = 0.0
var _muzzle_flash_timer: float = 0.0


func _ready() -> void:
	current_ammo = max_ammo
	ammo_changed.emit(current_ammo, max_ammo)

	_resolve_nodes_and_subcomponents()
	_setup_ability_audio()
	_bind_loadout_gauntlet_sync()

	if left_hand_pivot != null:
		left_hand_pivot.position = left_base_pos
		left_hand_pivot.rotation = left_base_rot
	if right_hand_pivot != null:
		right_hand_pivot.position = right_base_pos
		right_hand_pivot.rotation = right_base_rot

	_last_cam_basis = global_transform.basis if is_inside_tree() else transform.basis
	_has_last_cam_basis = true


func _wrap_weapon_stream_randomizer(path: String) -> AudioStreamRandomizer:
	if not ResourceLoader.exists(path):
		return null
	var base_stream: AudioStream = load(path) as AudioStream
	if base_stream == null:
		return null
	var rnd: AudioStreamRandomizer = AudioStreamRandomizer.new()
	rnd.random_pitch = 1.04
	rnd.random_volume_offset_db = 1.0
	rnd.add_stream(0, base_stream, 1.0)
	return rnd


func _setup_ability_audio() -> void:
	if _ability_sfx_player == null:
		_ability_sfx_player = AudioStreamPlayer.new()
		_ability_sfx_player.name = "LanternAbilitySFX"
		_ability_sfx_player.volume_db = -1.5
		add_child(_ability_sfx_player)
	if _weapon_sfx_player == null:
		_weapon_sfx_player = AudioStreamPlayer.new()
		_weapon_sfx_player.name = "RightWeaponSFX"
		_weapon_sfx_player.volume_db = -1.0
		add_child(_weapon_sfx_player)
	if _weapon_sfx_secondary == null:
		_weapon_sfx_secondary = AudioStreamPlayer.new()
		_weapon_sfx_secondary.name = "RightWeaponSFXSecondary"
		_weapon_sfx_secondary.volume_db = -1.5
		add_child(_weapon_sfx_secondary)

	if ResourceLoader.exists("res://assets/audio/sfx/ability_lantern_pyre_blast.wav"):
		_sfx_pyre_blast = load("res://assets/audio/sfx/ability_lantern_pyre_blast.wav") as AudioStream
	if ResourceLoader.exists("res://assets/audio/sfx/ability_lantern_soul_chains.wav"):
		_sfx_soul_chains = load("res://assets/audio/sfx/ability_lantern_soul_chains.wav") as AudioStream
	if ResourceLoader.exists("res://assets/audio/sfx/ability_lantern_blood_nova.wav"):
		_sfx_blood_nova = load("res://assets/audio/sfx/ability_lantern_blood_nova.wav") as AudioStream

	# Wrap all 8 Visceral Stereo Weapon AudioStreams in AudioStreamRandomizer (random_pitch = 1.04, random_volume_offset_db = 1.0)
	_sfx_revolver_fire = _wrap_weapon_stream_randomizer("res://assets/audio/sfx/revolver_fire.wav")
	_sfx_revolver_cock = _wrap_weapon_stream_randomizer("res://assets/audio/sfx/revolver_cock_click.wav")
	_sfx_revolver_reload = _wrap_weapon_stream_randomizer("res://assets/audio/sfx/revolver_reload.wav")
	_sfx_revolver_dry_fire = _wrap_weapon_stream_randomizer("res://assets/audio/sfx/revolver_dry_fire.wav")
	_sfx_shotgun_fire = _wrap_weapon_stream_randomizer("res://assets/audio/sfx/shotgun_fire_boom.wav")
	_sfx_shotgun_break = _wrap_weapon_stream_randomizer("res://assets/audio/sfx/shotgun_break_open.wav")
	_sfx_shotgun_close = _wrap_weapon_stream_randomizer("res://assets/audio/sfx/shotgun_shell_load_close.wav")
	_sfx_stakedriver_fire = _wrap_weapon_stream_randomizer("res://assets/audio/sfx/stakedriver_fire_pneumatic.wav")

	if ResourceLoader.exists("res://assets/audio/sfx/stakedriver_melee_cleave.wav"):
		_sfx_stakedriver_cleave = load("res://assets/audio/sfx/stakedriver_melee_cleave.wav") as AudioStream
	if ResourceLoader.exists("res://assets/audio/sfx/weapon_swap_holster.wav"):
		_sfx_weapon_swap = load("res://assets/audio/sfx/weapon_swap_holster.wav") as AudioStream
	if ResourceLoader.exists("res://assets/audio/sfx/ui_armor_equip_clank.wav"):
		_sfx_locked_clink = load("res://assets/audio/sfx/ui_armor_equip_clank.wav") as AudioStream


func _trigger_gunfire_ambient_duck() -> void:
	_ambient_duck_duration = 0.45
	_ambient_duck_timer = _ambient_duck_duration
	_ambient_duck_offset_db = -9.0
	if not is_inside_tree():
		return
	if _ambient_soundscape == null or not is_instance_valid(_ambient_soundscape):
		var root_node: Node = get_tree().current_scene if get_tree() != null else null
		if root_node == null and _player != null and _player.get_parent() != null:
			root_node = _player.get_parent()
		if root_node == null and get_tree() != null:
			root_node = get_tree().root
		if root_node != null:
			_ambient_soundscape = root_node.find_child("AmbientSoundscape", true, false) as AmbientSoundscapeController
	if _ambient_soundscape != null and is_instance_valid(_ambient_soundscape):
		_ambient_soundscape.trigger_gunfire_duck(-9.0, 0.45)


func _update_ambient_ducking(delta: float) -> void:
	if _ambient_duck_timer > 0.0:
		_ambient_duck_timer = maxf(0.0, _ambient_duck_timer - delta)
		_ambient_duck_offset_db = lerpf(0.0, -9.0, _ambient_duck_timer / maxf(_ambient_duck_duration, 0.05))
	else:
		_ambient_duck_offset_db = 0.0


func _play_weapon_sfx(primary_stream: AudioStream, secondary_stream: AudioStream = null) -> void:
	if _weapon_sfx_player != null and primary_stream != null and is_inside_tree():
		_weapon_sfx_player.stream = primary_stream
		_weapon_sfx_player.play()
	if _weapon_sfx_secondary != null and secondary_stream != null and is_inside_tree():
		_weapon_sfx_secondary.stream = secondary_stream
		_weapon_sfx_secondary.play()


func get_active_weapon_display_name() -> String:
	match active_weapon_id:
		"shotgun":
			return "Hellfire Coach Gun"
		"stakedriver":
			return "Pneumatic Stake-Driver"
		_:
			return "Occult Revolver"


func _notify_locked_forge_required() -> void:
	_play_weapon_sfx(_sfx_locked_clink if _sfx_locked_clink != null else _sfx_weapon_swap)
	if loadout_manager == null and _player != null:
		loadout_manager = _player.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	if loadout_manager != null:
		loadout_manager.notify_locked_forge_required()


func try_select_weapon_slot(weapon_idx: int) -> bool:
	var slot_idx: int = posmod(weapon_idx, 3)
	if loadout_manager == null and _player != null:
		loadout_manager = _player.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	if loadout_manager != null:
		if not loadout_manager.is_weapon_unlocked(slot_idx):
			_notify_locked_forge_required()
			return false
		return loadout_manager.equip_weapon(slot_idx)
	var fallback_id: String = "revolver"
	if slot_idx == 1:
		fallback_id = "shotgun"
	elif slot_idx == 2:
		fallback_id = "stakedriver"
	switch_active_weapon(fallback_id, true)
	return true


func switch_weapon(weapon_idx: int) -> bool:
	return try_select_weapon_slot(weapon_idx)


func switch_active_weapon(weapon_id: String, play_swap_anim: bool = true) -> void:
	if weapon_revolver == null or weapon_shotgun == null or weapon_stakedriver == null:
		_resolve_nodes_and_subcomponents()

	if loadout_manager == null and _player != null:
		loadout_manager = _player.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	if loadout_manager != null and not loadout_manager.is_weapon_unlocked(weapon_id):
		_notify_locked_forge_required()
		return

	ammo_by_weapon[active_weapon_id] = current_ammo
	active_weapon_id = weapon_id
	_is_reloading = false
	_reload_timer = 0.0
	_reload_beat1_done = false
	_reload_beat2_done = false
	_reload_beat3_done = false
	_shotgun_close_sfx_played = false

	if not max_ammo_by_weapon.has(active_weapon_id):
		max_ammo_by_weapon[active_weapon_id] = 6
	if not ammo_by_weapon.has(active_weapon_id):
		ammo_by_weapon[active_weapon_id] = max_ammo_by_weapon[active_weapon_id]

	max_ammo = max_ammo_by_weapon[active_weapon_id]
	current_ammo = ammo_by_weapon[active_weapon_id]

	if weapon_revolver != null:
		weapon_revolver.visible = (active_weapon_id == "revolver")
	if weapon_shotgun != null:
		weapon_shotgun.visible = (active_weapon_id == "shotgun")
	if weapon_stakedriver != null:
		weapon_stakedriver.visible = (active_weapon_id == "stakedriver")

	if _shotgun_barrel_assembly != null:
		_shotgun_barrel_assembly.rotation.x = 0.0

	if play_swap_anim:
		recoil_rot.x = deg_to_rad(-38.0)
		recoil_rot.z = deg_to_rad(14.0)
		recoil_pos.y = -0.18
		recoil_rot_vel = Vector3(4.5, 0.0, -3.2)
		recoil_vel = Vector3(0.0, 0.85, 0.0)
		recoil_offset_rot = recoil_rot
		recoil_offset_pos = recoil_pos
		_add_player_camera_trauma(0.14, Vector3(deg_to_rad(-1.2), 0.0, deg_to_rad(1.4)))
		_play_weapon_sfx(_sfx_weapon_swap)
		_apply_hand_transforms()

	ammo_changed.emit(current_ammo, max_ammo)


func is_lantern_raised() -> bool:
	return _is_lantern_raised


func get_active_spell_name() -> String:
	match active_spell_index:
		0:
			return "Searing Pyre"
		1:
			return "Shackles of the Penitent"
		2:
			return "Aegis of the Reliquary"
		_:
			return "Searing Pyre"


func _resolve_nodes_and_subcomponents() -> void:
	# 1. Resolve CharacterBody3D player root reliably via owner, parent chain, or group
	if owner is CharacterBody3D:
		_player = owner as CharacterBody3D
	if _player == null:
		var curr: Node = get_parent()
		while curr != null:
			if curr is CharacterBody3D:
				_player = curr as CharacterBody3D
				break
			curr = curr.get_parent()
	if _player == null and get_tree() != null:
		var grp_node: Node = get_tree().get_first_node_in_group("player")
		if grp_node is CharacterBody3D:
			_player = grp_node as CharacterBody3D

	if _player != null and loadout_manager == null:
		loadout_manager = _player.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager

	# 2. Guarantee LeftHandPivot, RightHandPivot, lights, and raycasts are bound
	if left_hand_pivot == null:
		left_hand_pivot = get_node_or_null("LeftHandPivot") as Node3D
		if left_hand_pivot == null:
			left_hand_pivot = find_child("LeftHandPivot", true, false) as Node3D

	if right_hand_pivot == null:
		right_hand_pivot = get_node_or_null("RightHandPivot") as Node3D
		if right_hand_pivot == null:
			right_hand_pivot = find_child("RightHandPivot", true, false) as Node3D

	if lantern_light == null:
		lantern_light = find_child("LanternLight", true, false) as OmniLight3D
	if muzzle_flash_light == null:
		muzzle_flash_light = find_child("MuzzleFlashLight", true, false) as OmniLight3D
	if muzzle_particles == null:
		muzzle_particles = find_child("MuzzleParticles", true, false) as GPUParticles3D
	if wall_raycast == null:
		wall_raycast = find_child("WallRayCast", true, false) as RayCast3D
	if hitscan_raycast == null:
		hitscan_raycast = find_child("HitscanRayCast", true, false) as RayCast3D

	# Prevent WallRayCast and HitscanRayCast from self-colliding with the player's own CapsuleShape3D
	if hitscan_raycast != null:
		hitscan_raycast.collision_mask = 1 | 4
	if _player != null:
		if wall_raycast != null:
			wall_raycast.add_exception(_player)
		if hitscan_raycast != null:
			hitscan_raycast.add_exception(_player)

	_revolver_rune_materials.clear()
	_gauntlet_plate_materials.clear()
	_gauntlet_leather_materials.clear()
	_gauntlet_trim_materials.clear()

	# 3. Resolve LeftHandPivot & LanternPendulum, and parent LanternLight directly inside LanternPendulum
	if left_hand_pivot != null:
		left_arm_gauntlet = left_hand_pivot.find_child("LeftArmGauntlet", true, false) as Node3D
		_lantern_pendulum = left_hand_pivot.find_child("LanternPendulum", true, false) as Node3D
		if _lantern_pendulum == null:
			_lantern_pendulum = _find_child_recursive(left_hand_pivot, "LanternPendulum")

		# Detach LanternPendulum from legacy LeftArmGauntlet so swapping 3D armor gauntlet meshes never hides the lantern!
		if _lantern_pendulum != null and _lantern_pendulum.get_parent() != left_hand_pivot:
			var pend_local_pos: Vector3 = _lantern_pendulum.position
			_lantern_pendulum.owner = null
			if _lantern_pendulum.get_parent() != null:
				_lantern_pendulum.get_parent().remove_child(_lantern_pendulum)
			left_hand_pivot.add_child(_lantern_pendulum)
			_lantern_pendulum.position = pend_local_pos

		if left_arm_gauntlet != null:
			left_arm_gauntlet.visible = false

		if active_gauntlet_instance == null or not is_instance_valid(active_gauntlet_instance):
			equip_armor_gauntlet(equipped_armor_index, false)

		_configure_viewmodel_meshes_recursive(left_hand_pivot, true)
		if _lantern_pendulum != null and lantern_light != null:
			if lantern_light.get_parent() != _lantern_pendulum:
				lantern_light.owner = null
				if lantern_light.get_parent() != null:
					lantern_light.get_parent().remove_child(lantern_light)
				_lantern_pendulum.add_child(lantern_light)
			lantern_light.position = Vector3(0.0, -0.156, 0.0)

	if lantern_light != null:
		lantern_light.shadow_enabled = true
		lantern_light.shadow_bias = 0.03
		lantern_light.shadow_normal_bias = 1.2
		lantern_light.shadow_blur = 1.5
		lantern_light.distance_fade_enabled = false
		lantern_light.omni_attenuation = lantern_attenuation
		lantern_light.light_energy = lantern_base_energy + lantern_energy_bonus
		lantern_light.omni_range = lantern_base_range + lantern_range_bonus
		lantern_light.light_volumetric_fog_energy = 3.8

	# 4. Resolve RightHandPivot & Multi-Weapon nodes (WeaponRevolver, WeaponShotgun, WeaponStakeDriver)
	if right_hand_pivot != null:
		weapon_revolver = right_hand_pivot.get_node_or_null("WeaponRevolver") as Node3D
		if weapon_revolver == null:
			var legacy_rev: Node3D = right_hand_pivot.get_node_or_null("RightRevolverModel") as Node3D
			if legacy_rev != null:
				legacy_rev.name = "WeaponRevolver"
				weapon_revolver = legacy_rev
		if weapon_revolver == null and ResourceLoader.exists("res://assets/models/weapons/viewmodel_right_revolver.glb"):
			var rev_scn: PackedScene = load("res://assets/models/weapons/viewmodel_right_revolver.glb") as PackedScene
			if rev_scn != null:
				weapon_revolver = rev_scn.instantiate() as Node3D
				weapon_revolver.name = "WeaponRevolver"
				right_hand_pivot.add_child(weapon_revolver)

		weapon_shotgun = right_hand_pivot.get_node_or_null("WeaponShotgun") as Node3D
		if weapon_shotgun == null and ResourceLoader.exists("res://assets/models/weapons/viewmodel_right_shotgun.glb"):
			var sg_scn: PackedScene = load("res://assets/models/weapons/viewmodel_right_shotgun.glb") as PackedScene
			if sg_scn != null:
				weapon_shotgun = sg_scn.instantiate() as Node3D
				weapon_shotgun.name = "WeaponShotgun"
				weapon_shotgun.visible = false
				right_hand_pivot.add_child(weapon_shotgun)

		weapon_stakedriver = right_hand_pivot.get_node_or_null("WeaponStakeDriver") as Node3D
		if weapon_stakedriver == null and ResourceLoader.exists("res://assets/models/weapons/viewmodel_right_stakedriver.glb"):
			var sd_scn: PackedScene = load("res://assets/models/weapons/viewmodel_right_stakedriver.glb") as PackedScene
			if sd_scn != null:
				weapon_stakedriver = sd_scn.instantiate() as Node3D
				weapon_stakedriver.name = "WeaponStakeDriver"
				weapon_stakedriver.visible = false
				right_hand_pivot.add_child(weapon_stakedriver)

		if weapon_revolver != null:
			weapon_revolver.visible = (active_weapon_id == "revolver")
			right_arm_gauntlet = weapon_revolver.find_child("RightArmGauntlet", true, false) as Node3D
			if right_arm_gauntlet == null:
				right_arm_gauntlet = weapon_revolver.find_child("RevolverFrame", true, false) as Node3D
			_revolver_cylinder = weapon_revolver.find_child("Cylinder", true, false) as Node3D
			_revolver_hammer = weapon_revolver.find_child("Hammer", true, false) as Node3D
			_revolver_trigger = weapon_revolver.find_child("Trigger", true, false) as Node3D
			_revolver_side_gear = weapon_revolver.find_child("SideGearWheel", true, false) as Node3D
			_revolver_ejector_rod = weapon_revolver.find_child("EjectorRod", true, false) as Node3D
			_muzzle_anchor = weapon_revolver.find_child("MuzzleAnchor", true, false) as Node3D
			if _revolver_ejector_rod != null:
				_ejector_default_z = _revolver_ejector_rod.position.z

		if weapon_shotgun != null:
			weapon_shotgun.visible = (active_weapon_id == "shotgun")
			_shotgun_barrel_assembly = weapon_shotgun.find_child("BarrelAssembly", true, false) as Node3D
			_shotgun_shell_left = weapon_shotgun.find_child("ShellLeft", true, false) as Node3D
			_shotgun_shell_right = weapon_shotgun.find_child("ShellRight", true, false) as Node3D
			_shotgun_hammer_left = weapon_shotgun.find_child("HammerLeft", true, false) as Node3D
			_shotgun_hammer_right = weapon_shotgun.find_child("HammerRight", true, false) as Node3D
			_shotgun_top_lever = weapon_shotgun.find_child("TopLever", true, false) as Node3D
			if _shotgun_shell_left != null:
				_shotgun_shell_left_default_z = _shotgun_shell_left.position.z
			if _shotgun_shell_right != null:
				_shotgun_shell_right_default_z = _shotgun_shell_right.position.z

		if weapon_stakedriver != null:
			weapon_stakedriver.visible = (active_weapon_id == "stakedriver")
			_driver_stake_ram = weapon_stakedriver.find_child("StakeRam", true, false) as Node3D
			_driver_flywheel = weapon_stakedriver.find_child("FlywheelGear", true, false) as Node3D
			_driver_loading_crank = weapon_stakedriver.find_child("LoadingCrank", true, false) as Node3D
			if _driver_stake_ram != null:
				_driver_ram_default_z = _driver_stake_ram.position.z

		_configure_viewmodel_meshes_recursive(right_hand_pivot, false)

		if muzzle_flash_light != null:
			if muzzle_flash_light.get_parent() != right_hand_pivot:
				muzzle_flash_light.owner = null
				if muzzle_flash_light.get_parent() != null:
					muzzle_flash_light.get_parent().remove_child(muzzle_flash_light)
				right_hand_pivot.add_child(muzzle_flash_light)
			muzzle_flash_light.position = Vector3(0.0, 0.06, -0.55)
			muzzle_flash_light.visible = false

		if muzzle_particles != null:
			if muzzle_particles.get_parent() != right_hand_pivot:
				muzzle_particles.owner = null
				if muzzle_particles.get_parent() != null:
					muzzle_particles.get_parent().remove_child(muzzle_particles)
				right_hand_pivot.add_child(muzzle_particles)
			_configure_muzzle_particles(muzzle_particles)


func _configure_muzzle_particles(parts: GPUParticles3D) -> void:
	parts.position = Vector3(0.0, 0.06, -0.55)
	parts.emitting = false
	parts.one_shot = true
	parts.explosiveness = 0.95
	parts.lifetime = 0.08
	parts.local_coords = true
	parts.amount = 14

	var p_mat: ParticleProcessMaterial = ParticleProcessMaterial.new()
	p_mat.direction = Vector3(0.0, 0.0, -1.0)
	p_mat.spread = 22.0
	p_mat.initial_velocity_min = 12.0
	p_mat.initial_velocity_max = 18.0
	p_mat.gravity = Vector3.ZERO
	p_mat.particle_flag_align_y = false
	p_mat.color = Color(1.0, 0.78, 0.38, 1.0)
	parts.process_material = p_mat

	var spark_box: BoxMesh = BoxMesh.new()
	spark_box.size = Vector3(0.008, 0.008, 0.04)
	var s_mat: StandardMaterial3D = StandardMaterial3D.new()
	s_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	s_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	s_mat.albedo_color = Color(1.0, 0.82, 0.42, 1.0)
	spark_box.material = s_mat
	parts.draw_pass_1 = spark_box


func _configure_viewmodel_meshes_recursive(node: Node, is_lantern: bool) -> void:
	if node is GeometryInstance3D:
		var geom: GeometryInstance3D = node as GeometryInstance3D
		geom.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if node is MeshInstance3D:
		var mi: MeshInstance3D = node as MeshInstance3D
		if mi.mesh != null:
			for s_idx: int in range(mi.mesh.get_surface_count()):
				var mat: Material = mi.mesh.surface_get_material(s_idx)
				if mat is StandardMaterial3D:
					var std_mat: StandardMaterial3D = (mat as StandardMaterial3D).duplicate() as StandardMaterial3D
					var mname: String = mat.resource_name.to_lower()
					std_mat.vertex_color_use_as_albedo = true
					if is_lantern and mname.contains("glass"):
						std_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
						std_mat.albedo_color = Color(1.0, 0.68, 0.28, 0.24)
						std_mat.roughness = 0.15
						std_mat.emission_enabled = true
						std_mat.emission = Color(1.0, 0.62, 0.22, 1.0)
						std_mat.emission_energy_multiplier = 0.6
					elif mname.contains("flamecore"):
						std_mat.albedo_color = Color.WHITE
						std_mat.emission_enabled = true
						std_mat.emission = Color(1.0, 0.78, 0.30, 1.0)
						std_mat.emission_energy_multiplier = 4.8
					elif mname.contains("flame"):
						std_mat.albedo_color = Color.WHITE
						std_mat.emission_enabled = true
						std_mat.emission = Color(1.0, 0.52, 0.16, 1.0)
						std_mat.emission_energy_multiplier = 2.4
					elif mname.contains("rune") or mname.contains("mat_runeglow"):
						std_mat.albedo_color = active_rune_color
						std_mat.emission_enabled = true
						std_mat.emission = active_rune_color
						std_mat.emission_energy_multiplier = 2.4
						if not is_lantern and not _revolver_rune_materials.has(std_mat):
							_revolver_rune_materials.append(std_mat)
					elif mname.contains("mat_iron"):
						std_mat.albedo_color = active_armor_plate_color if _has_custom_armor_tier else Color.html("#2c3038")
						std_mat.metallic = _active_plate_metallic if _has_custom_armor_tier else 0.82
						std_mat.roughness = _active_plate_roughness if _has_custom_armor_tier else 0.46
						if not _gauntlet_plate_materials.has(std_mat):
							_gauntlet_plate_materials.append(std_mat)
					elif mname.contains("mat_leather"):
						std_mat.albedo_color = _active_leather_color if _has_custom_armor_tier else Color.html("#32241e")
						std_mat.metallic = 0.08
						std_mat.roughness = 0.80
						if not _gauntlet_leather_materials.has(std_mat):
							_gauntlet_leather_materials.append(std_mat)
					elif mname.contains("mat_brass"):
						std_mat.albedo_color = _active_trim_color if _has_custom_armor_tier else Color.html("#7a5e30")
						std_mat.metallic = clampf(_active_plate_metallic + 0.04, 0.0, 0.88) if _has_custom_armor_tier else 0.80
						std_mat.roughness = clampf(_active_plate_roughness - 0.04, 0.38, 0.90) if _has_custom_armor_tier else 0.48
						if not _gauntlet_trim_materials.has(std_mat):
							_gauntlet_trim_materials.append(std_mat)
					else:
						# Weapon & Lantern surfaces have (base_rgb * ao * dir_shade) baked directly into COLOR_0
						std_mat.albedo_color = Color.WHITE
					mi.set_surface_override_material(s_idx, std_mat)
	for child: Node in node.get_children():
		_configure_viewmodel_meshes_recursive(child, is_lantern)


func _find_child_recursive(node: Node, target_name: String) -> Node3D:
	if node.name == target_name and node is Node3D:
		return node as Node3D
	for child: Node in node.get_children():
		var res: Node3D = _find_child_recursive(child, target_name)
		if res != null:
			return res
	return null


func _is_ui_menu_open() -> bool:
	if loadout_manager == null and _player != null:
		loadout_manager = _player.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	if loadout_manager != null and loadout_manager.hud != null:
		if loadout_manager.hud.character_menu != null and loadout_manager.hud.character_menu.is_menu_open:
			return true
		if loadout_manager.hud.map_system != null and loadout_manager.hud.map_system.is_full_map_open:
			return true
	if DisplayServer.get_name() != "headless" and Input.get_mouse_mode() != Input.MOUSE_MODE_CAPTURED:
		return true
	return false


func _input(event: InputEvent) -> void:
	if _is_ui_menu_open():
		return
	if event is InputEventKey:
		var kev: InputEventKey = event as InputEventKey
		if kev.pressed and not kev.echo:
			var kc: Key = kev.keycode if kev.keycode != KEY_NONE else kev.physical_keycode
			if kc == KEY_1:
				try_select_weapon_slot(0)
			elif kc == KEY_2:
				try_select_weapon_slot(1)
			elif kc == KEY_3:
				try_select_weapon_slot(2)
	elif event is InputEventMouseButton and Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED:
		var mbev: InputEventMouseButton = event as InputEventMouseButton
		if mbev.pressed:
			if mbev.button_index == MOUSE_BUTTON_WHEEL_UP:
				_cycle_weapon_wheel(-1)
			elif mbev.button_index == MOUSE_BUTTON_WHEEL_DOWN:
				_cycle_weapon_wheel(1)

	if event is InputEventMouseMotion and Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED:
		var motion: InputEventMouseMotion = event as InputEventMouseMotion
		var max_rot_rad: float = deg_to_rad(rot_sway_deg)
		_sway_target_pos.x = clampf(_sway_target_pos.x - motion.relative.x * 0.0014, -max_sway, max_sway)
		_sway_target_pos.y = clampf(_sway_target_pos.y + motion.relative.y * 0.0014, -max_sway, max_sway)
		_sway_target_rot.y = clampf(_sway_target_rot.y - motion.relative.x * 0.0032, -max_rot_rad, max_rot_rad)
		_sway_target_rot.x = clampf(_sway_target_rot.x - motion.relative.y * 0.0032, -max_rot_rad, max_rot_rad)

		# Feed direct camera-turn angular impulse into the lantern pendulum
		_pendulum_vel_z = clampf(_pendulum_vel_z - motion.relative.x * 0.075, -10.0, 10.0)
		_pendulum_vel_x = clampf(_pendulum_vel_x - motion.relative.y * 0.055, -10.0, 10.0)


func _cycle_weapon_wheel(dir: int) -> void:
	if loadout_manager == null and _player != null:
		loadout_manager = _player.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	if loadout_manager != null:
		loadout_manager.swap_weapon(dir)
	else:
		var curr_slot: int = 0
		if active_weapon_id == "shotgun":
			curr_slot = 1
		elif active_weapon_id == "stakedriver":
			curr_slot = 2
		try_select_weapon_slot(posmod(curr_slot + dir, 3))


func _process(delta: float) -> void:
	if _player == null or left_hand_pivot == null or right_hand_pivot == null:
		_resolve_nodes_and_subcomponents()

	if _fire_cooldown_remaining > 0.0:
		_fire_cooldown_remaining = maxf(0.0, _fire_cooldown_remaining - delta)

	if ability_cooldown_remaining > 0.0:
		ability_cooldown_remaining = maxf(0.0, ability_cooldown_remaining - delta)

	if _spell_flare_timer > 0.0:
		_spell_flare_timer = maxf(0.0, _spell_flare_timer - delta)

	if _muzzle_flash_timer > 0.0:
		_muzzle_flash_timer = maxf(0.0, _muzzle_flash_timer - delta)
		if muzzle_flash_light != null:
			muzzle_flash_light.light_energy = (_muzzle_flash_timer / 0.06) * 3.2
			if _muzzle_flash_timer <= 0.0:
				muzzle_flash_light.visible = false

	if _is_reloading:
		_reload_timer -= delta
		var reload_progress: float = 1.0 - clampf(_reload_timer / maxf(_reload_duration_total, 0.1), 0.0, 1.0)
		var whip_t: float = ease(clampf(reload_progress, 0.0, 1.0), 3.8)
		_update_snappy_whip_reload_beats(reload_progress, whip_t)

		if active_weapon_id == "shotgun" and not _shotgun_close_sfx_played and _reload_timer <= (_reload_duration_total * 0.25):
			_shotgun_close_sfx_played = true
			_play_weapon_sfx(_sfx_shotgun_close)
		if _reload_timer <= 0.0:
			current_ammo = max_ammo
			ammo_by_weapon[active_weapon_id] = current_ammo
			_is_reloading = false
			_reload_beat1_done = false
			_reload_beat2_done = false
			_reload_beat3_done = false
			_shotgun_close_sfx_played = false
			if _shotgun_barrel_assembly != null:
				_shotgun_barrel_assembly.rotation.x = 0.0
			if _shotgun_shell_left != null:
				_shotgun_shell_left.position.z = _shotgun_shell_left_default_z
			if _shotgun_shell_right != null:
				_shotgun_shell_right.position.z = _shotgun_shell_right_default_z
			ammo_changed.emit(current_ammo, max_ammo)

	_idle_timer += delta
	_update_ambient_ducking(delta)
	_handle_input_actions()
	_update_lantern_raise(delta)
	_update_sway_and_inertia(delta)
	_update_walk_bob_and_wall_tuck(delta)
	_update_pendulum_physics(delta)
	_update_revolver_mechanisms(delta)
	_update_shotgun_mechanisms(delta)
	_update_stakedriver_mechanisms(delta)

	# Integrate all additive offsets directly onto RightHandPivot and LeftHandPivot
	_apply_hand_transforms()

	# Phase 2.1: 6-DOF Underdamped Spring-Damper Solver (stiffness = 180.0, damping = 14.5)
	_step_6dof_recoil_spring(delta)


func _update_snappy_whip_reload_beats(progress: float, _whip_t: float) -> void:
	# Beat 1 (Break Open / Cylinder Swing-Out at 15% reload progress)
	if progress >= 0.15 and not _reload_beat1_done:
		_reload_beat1_done = true
		recoil_rot.z = deg_to_rad(38.0)
		recoil_rot.x = -deg_to_rad(18.0)
		recoil_pos.x -= 0.03
		recoil_vel.x -= 0.35
		recoil_rot_vel.z += 4.2
		_sync_recoil_aliases()
		_add_player_camera_trauma(0.12, Vector3(-deg_to_rad(1.4), 0.0, deg_to_rad(2.2)))

	# Beat 2 (Shell Eject / Chamber Load at 50% reload progress)
	if progress >= 0.50 and not _reload_beat2_done:
		_reload_beat2_done = true
		recoil_pos.y -= 0.06
		recoil_vel.y += 0.48
		recoil_rot_vel.x += 2.8
		_sync_recoil_aliases()
		_add_player_camera_trauma(0.10, Vector3(-deg_to_rad(1.1), 0.0, 0.0))

	# Beat 3 (Breech / Cylinder Slam Shut at 82% reload progress)
	if progress >= 0.82 and not _reload_beat3_done:
		_reload_beat3_done = true
		recoil_rot.z = 0.0
		recoil_rot.x = 0.0
		recoil_rot_vel.z -= 8.5
		recoil_vel.x += 0.4
		_sync_recoil_aliases()
		_add_player_camera_trauma(0.24, Vector3(deg_to_rad(1.8), 0.0, -deg_to_rad(3.2)))


func _step_6dof_recoil_spring(delta: float) -> void:
	var dt: float = minf(delta, 0.05)
	var target_rot: Vector3 = Vector3.ZERO
	if _is_reloading:
		var progress: float = 1.0 - clampf(_reload_timer / maxf(_reload_duration_total, 0.1), 0.0, 1.0)
		if progress < 0.82:
			var whip_blend: float = ease(clampf(progress / 0.82, 0.0, 1.0), 3.8)
			var base_reload_rot: Vector3 = Vector3(-deg_to_rad(18.0), 0.0, deg_to_rad(38.0))
			if active_weapon_id == "shotgun":
				base_reload_rot = Vector3(-deg_to_rad(16.0), 0.0, deg_to_rad(28.0))
			elif active_weapon_id == "stakedriver":
				base_reload_rot = Vector3(-deg_to_rad(14.0), 0.0, deg_to_rad(32.0))
			target_rot = base_reload_rot.lerp(base_reload_rot * 1.08, whip_blend)

	# 6-DOF Positional Spring
	var pos_force: Vector3 = -stiffness * recoil_pos - damping * recoil_vel
	recoil_vel += pos_force * dt
	recoil_pos += recoil_vel * dt

	# 6-DOF Rotational Spring
	var rot_disp: Vector3 = recoil_rot - target_rot
	var rot_force: Vector3 = -stiffness * rot_disp - damping * recoil_rot_vel
	recoil_rot_vel += rot_force * dt
	recoil_rot += recoil_rot_vel * dt

	# Left hand recoil spring
	var left_force: Vector3 = -stiffness * left_recoil_offset_pos - damping * left_recoil_vel
	left_recoil_vel += left_force * dt
	left_recoil_offset_pos += left_recoil_vel * dt

	_sync_recoil_aliases()


func _sync_recoil_aliases() -> void:
	recoil_offset_pos = recoil_pos
	recoil_offset_rot = recoil_rot


func add_recoil_impulse(pos_impulse: Vector3, rot_impulse: Vector3) -> void:
	recoil_pos += pos_impulse
	recoil_vel += pos_impulse * 6.0
	recoil_rot += rot_impulse
	recoil_rot_vel += rot_impulse * 5.5
	_sync_recoil_aliases()
	_apply_hand_transforms()


func trigger_shoot_recoil(intensity: float = 1.0) -> void:
	if _weapon_recoil_tween != null and _weapon_recoil_tween.is_valid():
		_weapon_recoil_tween.kill()

	_weapon_mount_recoil_pos = Vector3(0.0, 0.0, 0.055 * intensity)
	_weapon_mount_recoil_rot = Vector3(deg_to_rad(5.5 * intensity), 0.0, 0.0)
	_apply_hand_transforms()

	_weapon_recoil_tween = create_tween()
	_weapon_recoil_tween.set_parallel(true)
	_weapon_recoil_tween.tween_property(self, "_weapon_mount_recoil_pos", Vector3.ZERO, 0.14).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	_weapon_recoil_tween.tween_property(self, "_weapon_mount_recoil_rot", Vector3.ZERO, 0.14).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)


func _non_zero_signed_range(min_abs: float, max_abs: float) -> float:
	var mag: float = _rng.randf_range(min_abs, max_abs)
	var sgn: float = 1.0 if _rng.randf() >= 0.5 else -1.0
	return mag * sgn


func _add_player_camera_trauma(amount: float, directional_punch: Vector3 = Vector3.ZERO) -> void:
	if _player == null:
		_resolve_nodes_and_subcomponents()
	if _player is FPSController:
		(_player as FPSController).add_camera_trauma(amount, directional_punch)


func on_quickstep_dash(dash_dir: Vector3) -> void:
	# Tuck active weapon inward across the chest (recoil_rot.z += 0.35, recoil_pos.y -= 0.05)
	recoil_rot.z += 0.35
	recoil_pos.y -= 0.05
	recoil_rot_vel.z += 2.2
	recoil_vel.y -= 0.35
	_sync_recoil_aliases()

	# Whip left-hand Lantern pendulum opposite to the dash vector
	var cur_basis: Basis = global_transform.basis if is_inside_tree() else transform.basis
	var local_dash: Vector3 = cur_basis.inverse() * dash_dir
	_pendulum_vel_x = clampf(_pendulum_vel_x + local_dash.z * 7.5, -12.0, 12.0)
	_pendulum_vel_z = clampf(_pendulum_vel_z - local_dash.x * 8.5, -12.0, 12.0)
	left_recoil_offset_pos += Vector3(-local_dash.x * 0.04, -0.035, 0.03)

	# Temporarily flare LanternLight with a ghostly blue-gold quickstep trail pulse
	_spell_flare_timer = maxf(_spell_flare_timer, 0.24)
	_spell_flare_color = Color(0.58, 0.88, 1.0, 1.0)
	if lantern_light != null:
		lantern_light.light_color = _spell_flare_color
		lantern_light.light_energy = maxf(lantern_light.light_energy, 5.2)

	# Quicksilver Tier II (quick_2): performing a Quickstep Dash mid-reload completes the reload
	if _is_reloading and loadout_manager != null and loadout_manager.is_skill_unlocked("quick_2"):
		_reload_timer = 0.02

	_apply_hand_transforms()


func on_jump_takeoff() -> void:
	recoil_pos.y -= 0.04
	recoil_vel.y -= 0.25
	left_recoil_offset_pos.y -= 0.04
	_pendulum_vel_x += 2.4
	_sync_recoil_aliases()
	_apply_hand_transforms()


func on_landing_impact(impact: float) -> void:
	recoil_pos.y -= 0.065 * impact
	recoil_vel.y -= 0.55 * impact
	recoil_rot.x -= deg_to_rad(6.0) * impact
	left_recoil_offset_pos.y -= 0.055 * impact
	_pendulum_vel_x -= 4.2 * impact
	_sync_recoil_aliases()
	_apply_hand_transforms()


func _apply_hand_transforms() -> void:
	recoil_offset_pos = recoil_pos
	recoil_offset_rot = recoil_rot
	if right_hand_pivot != null:
		right_hand_pivot.position = right_base_pos + sway_pos + bob_pos + recoil_pos + _tuck_offset + _weapon_mount_recoil_pos
		right_hand_pivot.rotation = right_base_rot + sway_rot + bob_rot + recoil_rot + Vector3(_tuck_rot_x, 0.0, 0.0) + _weapon_mount_recoil_rot

	if left_hand_pivot != null:
		var active_left_base: Vector3 = left_raised_pos if _is_lantern_raised else left_base_pos
		left_hand_pivot.position = active_left_base + sway_pos + left_bob_pos + left_recoil_offset_pos + _tuck_offset
		left_hand_pivot.rotation = left_base_rot + sway_rot + left_bob_rot + Vector3(_tuck_rot_x, 0.0, 0.0)


func _handle_input_actions() -> void:
	if _is_ui_menu_open():
		_was_lantern_raised = false
		_is_lantern_raised = false
		return

	if Input.is_action_just_pressed("fire"):
		_fire_active_weapon()

	if Input.is_action_just_pressed("reload"):
		_reload_active_weapon()

	if Input.is_action_just_pressed("cast_ability"):
		cast_active_lantern_ability()

	if Input.is_action_just_pressed("cycle_ability"):
		cycle_lantern_ability()

	var now_raised: bool = Input.is_action_pressed("lantern_raise")
	if now_raised and not _was_lantern_raised:
		_add_player_camera_trauma(0.14, Vector3(deg_to_rad(1.0), 0.0, deg_to_rad(-1.2)))
	_was_lantern_raised = now_raised
	_is_lantern_raised = now_raised


func cycle_lantern_ability(step: int = 1) -> void:
	if loadout_manager == null and _player != null:
		loadout_manager = _player.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	var dir_step: int = 1 if step >= 0 else -1
	if loadout_manager != null:
		for i: int in range(1, 4):
			var cand_idx: int = posmod(active_spell_index + dir_step * i, 3)
			if loadout_manager.is_spell_unlocked(cand_idx):
				if cand_idx != active_spell_index:
					active_spell_index = cand_idx
					loadout_manager.equipped_spell_index = active_spell_index
					left_recoil_offset_pos += Vector3(0.04, 0.03, -0.05)
					_pendulum_vel_z += 3.2
					_apply_hand_transforms()
				else:
					_notify_locked_forge_required()
				return
		_notify_locked_forge_required()
		return
	active_spell_index = posmod(active_spell_index + step, 3)
	left_recoil_offset_pos += Vector3(0.04, 0.03, -0.05)
	_pendulum_vel_z += 3.2
	_apply_hand_transforms()


func cast_active_lantern_ability() -> bool:
	if ability_cooldown_remaining > 0.0:
		return false

	if _player == null or left_hand_pivot == null:
		_resolve_nodes_and_subcomponents()

	var cd_mult: float = loadout_manager.ability_cooldown_mult if loadout_manager != null else 1.0
	var eldritch_mult: float = loadout_manager.eldritch_damage_mult if loadout_manager != null else 1.0
	var rad_bonus: float = loadout_manager.eldritch_radius_bonus if loadout_manager != null else 0.0

	ability_cooldown_remaining = base_ability_cooldown * cd_mult

	# 1. Left-Hand Lantern Cast Animation: thrust forward, flare lantern light to 8.0, and add +0.32 camera trauma
	left_recoil_offset_pos += Vector3(0.12, 0.08, -0.18)
	_pendulum_vel_x -= 6.5
	_spell_flare_timer = 0.45
	_add_player_camera_trauma(0.32, Vector3(deg_to_rad(2.4), 0.0, deg_to_rad(-1.8)))
	_apply_hand_transforms()

	var spell_range: float = 10.0 + rad_bonus
	var spell_dmg: float = 55.0 * eldritch_mult
	var spell_col: Color = Color(1.0, 0.62, 0.16, 1.0)
	var sfx_stream: AudioStream = _sfx_pyre_blast

	match active_spell_index:
		0:
			# 1. Soul-Pyre Blast (Unlocked Lv. 1 | Blazing Gold-Orange)
			spell_range = 10.0 + rad_bonus
			spell_dmg = 55.0 * eldritch_mult
			spell_col = Color(1.0, 0.62, 0.16, 1.0)
			sfx_stream = _sfx_pyre_blast
		1:
			# 2. Shackles of the Penitent (Unlocked Lv. 2 | Spectral Ice-Blue)
			spell_range = 12.0 + rad_bonus
			spell_dmg = 40.0 * eldritch_mult
			spell_col = Color(0.28, 0.78, 1.0, 1.0)
			sfx_stream = _sfx_soul_chains
		2:
			# 3. Abyssal Blood Nova (Unlocked Lv. 3 | Crimson-Violet)
			spell_range = 9.0 + rad_bonus
			spell_dmg = 75.0 * eldritch_mult
			spell_col = Color(0.95, 0.14, 0.36, 1.0)
			sfx_stream = _sfx_blood_nova

	_spell_flare_color = spell_col
	if lantern_light != null:
		lantern_light.light_color = spell_col
		lantern_light.light_energy = 8.0
		lantern_light.omni_range = maxf(lantern_raised_range, lantern_base_range + 6.0) + lantern_range_bonus
		lantern_light.omni_attenuation = lantern_attenuation
		lantern_light.distance_fade_enabled = false

	if _ability_sfx_player != null and sfx_stream != null and is_inside_tree():
		_ability_sfx_player.stream = sfx_stream
		_ability_sfx_player.play()

	var cast_origin: Vector3 = _player.global_position if _player != null else global_position
	_spawn_spell_shockwave_vfx(cast_origin + Vector3(0.0, 0.85, 0.0), spell_range, spell_col)

	var enemies: Array[TestDummyEnemy] = _collect_all_enemies()
	var total_damage_dealt: float = 0.0
	for enemy: TestDummyEnemy in enemies:
		if enemy == null or not is_instance_valid(enemy):
			continue
		var dist: float = cast_origin.distance_to(enemy.global_position)
		if dist <= spell_range:
			enemy.apply_damage(spell_dmg)
			total_damage_dealt += spell_dmg
			if active_spell_index == 0 and is_instance_valid(enemy):
				enemy.apply_burn_dot(15.0 * eldritch_mult, 4.0)
			elif active_spell_index == 1 and is_instance_valid(enemy):
				enemy.apply_shackle_debuff(4.0)

	if active_spell_index == 2 and total_damage_dealt > 0.0 and loadout_manager != null:
		var leech_amt: int = maxi(1, roundi(total_damage_dealt * 0.35))
		loadout_manager.current_health = mini(loadout_manager.max_health, loadout_manager.current_health + leech_amt)
		loadout_manager.current_armor = mini(loadout_manager.max_armor, loadout_manager.current_armor + leech_amt)
		loadout_manager._refresh_hud()

	spell_cast.emit(active_spell_index, get_active_spell_name())
	return true


func _spawn_spell_shockwave_vfx(center_pos: Vector3, radius: float, col: Color) -> void:
	if not is_inside_tree() or get_tree() == null:
		return
	var scene_root: Node = get_tree().current_scene
	if scene_root == null and _player != null:
		scene_root = _player.get_parent()
	if scene_root == null:
		return

	var ring_mi: MeshInstance3D = MeshInstance3D.new()
	ring_mi.name = "LanternSpellShockwave"
	var torus: TorusMesh = TorusMesh.new()
	torus.inner_radius = maxf(0.4, radius * 0.32)
	torus.outer_radius = maxf(0.6, radius * 0.38)
	var r_mat: StandardMaterial3D = StandardMaterial3D.new()
	r_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	r_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	r_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	r_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	r_mat.albedo_color = Color(col.r, col.g, col.b, 0.72)
	torus.material = r_mat
	ring_mi.mesh = torus
	ring_mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	scene_root.add_child(ring_mi)
	ring_mi.global_position = center_pos

	var tw: Tween = ring_mi.create_tween()
	tw.tween_property(ring_mi, "scale", Vector3(2.4, 1.0, 2.4), 0.36)
	tw.parallel().tween_property(r_mat, "albedo_color:a", 0.0, 0.36)
	tw.tween_callback(ring_mi.queue_free)


func _collect_all_enemies() -> Array[TestDummyEnemy]:
	var result: Array[TestDummyEnemy] = []
	if not is_inside_tree():
		return result
	if get_tree() != null:
		for n: Node in get_tree().get_nodes_in_group("enemies"):
			if n is TestDummyEnemy:
				var ge: TestDummyEnemy = n as TestDummyEnemy
				if ge.is_alive() and not result.has(ge):
					result.append(ge)
	var root_search: Node = null
	if _player != null and _player.get_parent() != null:
		root_search = _player.get_parent()
	elif get_tree() != null:
		root_search = get_tree().root
	if root_search != null:
		_collect_enemies_recursive(root_search, result)
	return result


func _collect_enemies_recursive(node: Node, out_list: Array[TestDummyEnemy]) -> void:
	if node is TestDummyEnemy:
		var enemy: TestDummyEnemy = node as TestDummyEnemy
		if enemy.is_alive() and not out_list.has(enemy):
			out_list.append(enemy)
	for child: Node in node.get_children():
		_collect_enemies_recursive(child, out_list)


func _update_lantern_raise(delta: float) -> void:
	if lantern_light == null:
		return

	var base_range: float = lantern_raised_range if _is_lantern_raised else lantern_base_range
	var base_energy: float = (lantern_base_energy * 1.25) if _is_lantern_raised else lantern_base_energy
	var target_range: float = base_range + lantern_range_bonus
	var target_energy: float = base_energy + lantern_energy_bonus
	if _spell_flare_timer > 0.0:
		target_energy = 8.0
		target_range = maxf(target_range, lantern_raised_range + lantern_range_bonus)
		lantern_light.light_color = _spell_flare_color
	else:
		lantern_light.light_color = Color(1.0, 0.72, 0.36, 1.0)
	lantern_light.omni_range = lerpf(lantern_light.omni_range, target_range, clampf(delta * 8.0, 0.0, 1.0))
	lantern_light.light_energy = lerpf(lantern_light.light_energy, target_energy, clampf(delta * 8.0, 0.0, 1.0))
	lantern_light.omni_attenuation = lantern_attenuation
	lantern_light.distance_fade_enabled = false
	lantern_light.light_volumetric_fog_energy = 3.8
	lantern_light.shadow_enabled = true
	if _lantern_pendulum != null and lantern_light.get_parent() == _lantern_pendulum:
		lantern_light.position = Vector3(0.0, -0.156, 0.0)


func _update_sway_and_inertia(delta: float) -> void:
	if _has_last_cam_basis:
		var rel_basis: Basis = _last_cam_basis.inverse() * global_transform.basis
		var euler_delta: Vector3 = rel_basis.get_euler()
		var max_rot_rad: float = deg_to_rad(rot_sway_deg)
		if absf(euler_delta.y) > 0.0001 or absf(euler_delta.x) > 0.0001:
			_sway_target_pos.x = clampf(_sway_target_pos.x + euler_delta.y * 0.45, -max_sway, max_sway)
			_sway_target_pos.y = clampf(_sway_target_pos.y - euler_delta.x * 0.45, -max_sway, max_sway)
			_sway_target_rot.y = clampf(_sway_target_rot.y + euler_delta.y * 0.85, -max_rot_rad, max_rot_rad)
			_sway_target_rot.x = clampf(_sway_target_rot.x + euler_delta.x * 0.85, -max_rot_rad, max_rot_rad)
			_pendulum_vel_z = clampf(_pendulum_vel_z + euler_delta.y * 12.0, -10.0, 10.0)
			_pendulum_vel_x = clampf(_pendulum_vel_x - euler_delta.x * 10.0, -10.0, 10.0)
	_last_cam_basis = global_transform.basis if is_inside_tree() else transform.basis
	_has_last_cam_basis = true

	var decay_step: float = clampf(delta * 8.5, 0.0, 1.0)
	var follow_step: float = clampf(delta * sway_smooth, 0.0, 1.0)
	_sway_target_pos = _sway_target_pos.lerp(Vector3.ZERO, decay_step)
	_sway_target_rot = _sway_target_rot.lerp(Vector3.ZERO, decay_step)

	sway_pos = sway_pos.lerp(_sway_target_pos, follow_step)
	sway_rot.x = lerpf(sway_rot.x, _sway_target_rot.x, follow_step)
	sway_rot.y = lerpf(sway_rot.y, _sway_target_rot.y, follow_step)

	var strafe_input: float = Input.get_axis("move_left", "move_right")
	var target_tilt_z: float = -strafe_input * deg_to_rad(strafe_tilt_deg)
	sway_rot.z = lerpf(sway_rot.z, target_tilt_z, clampf(delta * 8.0, 0.0, 1.0))


func _update_walk_bob_and_wall_tuck(delta: float) -> void:
	var speed: float = _player.velocity.length() if _player != null else 0.0

	if speed > 0.2:
		var speed_scale: float = clampf(speed / 5.5, 0.45, 1.15)
		bob_phase += delta * bob_freq

		# Right hand subtle figure-8 bob
		var right_x: float = sin(bob_phase) * bob_horiz_amp * speed_scale
		var right_y: float = sin(bob_phase * 2.0) * bob_vert_amp * speed_scale
		var right_roll: float = sin(bob_phase) * deg_to_rad(bob_roll_deg) * speed_scale
		bob_pos = Vector3(right_x, right_y, 0.0)
		bob_rot = Vector3(sin(bob_phase * 2.0) * deg_to_rad(0.45) * speed_scale, 0.0, right_roll)

		# Left hand figure-8 bob (phase-shifted for natural alternating arm stride)
		var left_phase: float = bob_phase + PI * 0.5
		var left_x: float = sin(left_phase) * bob_horiz_amp * speed_scale
		var left_y: float = sin(left_phase * 2.0) * bob_vert_amp * speed_scale
		var left_roll: float = sin(left_phase) * deg_to_rad(bob_roll_deg) * speed_scale
		left_bob_pos = Vector3(left_x, left_y, 0.0)
		left_bob_rot = Vector3(sin(left_phase * 2.0) * deg_to_rad(0.40) * speed_scale, 0.0, left_roll)
	else:
		# Subtle idle breathing motion when standing still
		var idle_r: Vector3 = Vector3(sin(_idle_timer * 1.2) * 0.002, cos(_idle_timer * 2.2) * 0.0035, 0.0)
		var idle_l: Vector3 = Vector3(cos(_idle_timer * 1.1) * 0.002, sin(_idle_timer * 2.2) * 0.0035, 0.0)
		bob_pos = bob_pos.lerp(idle_r, clampf(delta * 8.0, 0.0, 1.0))
		bob_rot = bob_rot.lerp(Vector3.ZERO, clampf(delta * 8.0, 0.0, 1.0))
		left_bob_pos = left_bob_pos.lerp(idle_l, clampf(delta * 8.0, 0.0, 1.0))
		left_bob_rot = left_bob_rot.lerp(Vector3.ZERO, clampf(delta * 8.0, 0.0, 1.0))

	# Wall-Avoidance Tuck (ignoring self-collision with _player)
	_tuck_offset = Vector3.ZERO
	_tuck_rot_x = 0.0
	if wall_raycast != null and wall_raycast.is_colliding():
		var col_obj: Object = wall_raycast.get_collider()
		if col_obj != _player:
			var col_pt: Vector3 = wall_raycast.get_collision_point()
			var dist: float = global_position.distance_to(col_pt)
			var t: float = clampf(1.0 - (dist / wall_tuck_distance), 0.0, 1.0)
			_tuck_offset = Vector3(0.0, -0.07 * t, 0.14 * t)
			_tuck_rot_x = deg_to_rad(24.0 * t)


func _update_pendulum_physics(delta: float) -> void:
	if _lantern_pendulum == null:
		return

	var current_vel: Vector3 = _player.velocity if _player != null else Vector3.ZERO
	var player_accel: Vector3 = (current_vel - _last_player_vel) / maxf(delta, 0.001)
	_last_player_vel = current_vel

	var local_accel: Vector3 = global_transform.basis.inverse() * player_accel
	var local_vel: Vector3 = global_transform.basis.inverse() * current_vel
	var speed: float = current_vel.length()
	var speed_ratio: float = clampf(speed / 5.5, 0.0, 1.35)

	var force_x: float = local_accel.z * pendulum_accel_sensitivity + local_vel.z * 0.35
	var force_z: float = -local_accel.x * pendulum_accel_sensitivity - local_vel.x * 0.45 - sway_rot.y * 10.0

	if speed > 0.2:
		force_z += cos(bob_phase) * 14.0 * maxf(speed_ratio, 0.6)
		force_x += sin(bob_phase * 2.0) * 11.0 * maxf(speed_ratio, 0.6)
	else:
		force_z += sin(_idle_timer * 1.7) * 0.65
		force_x += cos(_idle_timer * 1.3) * 0.50

	if absf(local_accel.y) > 1.0:
		force_x += signf(local_accel.y) * 0.35

	var max_ang: float = deg_to_rad(max_pendulum_angle_deg)
	_pendulum_vel_x += (-pendulum_spring * _pendulum_angle_x - pendulum_damping * _pendulum_vel_x + force_x) * delta
	_pendulum_vel_z += (-pendulum_spring * _pendulum_angle_z - pendulum_damping * _pendulum_vel_z + force_z) * delta

	_pendulum_angle_x += _pendulum_vel_x * delta
	_pendulum_angle_z += _pendulum_vel_z * delta

	# Combine spring-damper inertia with direct walk-cadence swing so ±20° swing is unmistakably visible
	var cadence_x: float = sin(bob_phase) * deg_to_rad(12.0) * speed_ratio if speed > 0.2 else 0.0
	var cadence_z: float = cos(bob_phase) * deg_to_rad(15.0) * speed_ratio if speed > 0.2 else 0.0

	var final_x: float = clampf(_pendulum_angle_x + cadence_x, -max_ang, max_ang)
	var final_z: float = clampf(_pendulum_angle_z + cadence_z, -max_ang, max_ang)

	_lantern_pendulum.rotation = Vector3(final_x, 0.0, final_z)


func _update_revolver_mechanisms(delta: float) -> void:
	# 1. Cylinder 60-deg step rotation smoothly lerped every frame along longitudinal barrel axis
	if _revolver_cylinder != null:
		_revolver_cylinder.rotation.z = lerpf(
			_revolver_cylinder.rotation.z,
			cylinder_target_angle,
			clampf(delta * 18.0, 0.0, 1.0)
		)

	# 2. Side clockwork gear rotation
	if _revolver_side_gear != null:
		_revolver_side_gear.rotation.x = lerpf(
			_revolver_side_gear.rotation.x,
			_gear_target_angle,
			clampf(delta * 18.0, 0.0, 1.0)
		)

	# 3. Hammer snap backward (+28 deg) and forward (-14 deg)
	if _revolver_hammer != null:
		if _hammer_snap_timer > 0.0:
			_hammer_snap_timer = maxf(0.0, _hammer_snap_timer - delta)
			if _hammer_snap_timer > 0.07:
				_revolver_hammer.rotation.x = lerpf(_revolver_hammer.rotation.x, deg_to_rad(28.0), clampf(delta * 35.0, 0.0, 1.0))
			else:
				_revolver_hammer.rotation.x = lerpf(_revolver_hammer.rotation.x, deg_to_rad(-14.0), clampf(delta * 35.0, 0.0, 1.0))
		else:
			_revolver_hammer.rotation.x = lerpf(_revolver_hammer.rotation.x, 0.0, clampf(delta * 16.0, 0.0, 1.0))

	# 4. Trigger pull & return
	if _revolver_trigger != null:
		if _trigger_snap_timer > 0.0:
			_trigger_snap_timer = maxf(0.0, _trigger_snap_timer - delta)
			_revolver_trigger.rotation.x = lerpf(_revolver_trigger.rotation.x, deg_to_rad(-22.0), clampf(delta * 30.0, 0.0, 1.0))
		else:
			_revolver_trigger.rotation.x = lerpf(_revolver_trigger.rotation.x, 0.0, clampf(delta * 16.0, 0.0, 1.0))

	# 5. Ejector rod stroke
	if _revolver_ejector_rod != null:
		if _ejector_snap_timer > 0.0:
			_ejector_snap_timer = maxf(0.0, _ejector_snap_timer - delta)
			_revolver_ejector_rod.position.z = lerpf(_revolver_ejector_rod.position.z, _ejector_default_z + 0.016, clampf(delta * 28.0, 0.0, 1.0))
		else:
			_revolver_ejector_rod.position.z = lerpf(_revolver_ejector_rod.position.z, _ejector_default_z, clampf(delta * 16.0, 0.0, 1.0))


func _update_shotgun_mechanisms(delta: float) -> void:
	if _shotgun_barrel_assembly != null:
		if _is_reloading and active_weapon_id == "shotgun":
			var progress: float = 1.0 - clampf(_reload_timer / maxf(_reload_duration_total, 0.1), 0.0, 1.0)
			if progress < 0.78:
				_shotgun_barrel_assembly.rotation.x = lerpf(
					_shotgun_barrel_assembly.rotation.x,
					deg_to_rad(-42.0),
					clampf(delta * 20.0, 0.0, 1.0)
				)
			else:
				_shotgun_barrel_assembly.rotation.x = lerpf(
					_shotgun_barrel_assembly.rotation.x,
					0.0,
					clampf(delta * 24.0, 0.0, 1.0)
				)
			if _shotgun_top_lever != null:
				var lever_ang: float = deg_to_rad(28.0) if progress < 0.35 else 0.0
				_shotgun_top_lever.rotation.y = lerpf(_shotgun_top_lever.rotation.y, lever_ang, clampf(delta * 22.0, 0.0, 1.0))
			if _shotgun_shell_left != null and _shotgun_shell_right != null:
				var shell_offset: float = 0.0
				if progress < 0.42:
					shell_offset = lerpf(0.0, 0.11, clampf(progress / 0.42, 0.0, 1.0))
				elif progress < 0.78:
					shell_offset = lerpf(0.11, 0.0, clampf((progress - 0.42) / 0.36, 0.0, 1.0))
				_shotgun_shell_left.position.z = _shotgun_shell_left_default_z + shell_offset
				_shotgun_shell_right.position.z = _shotgun_shell_right_default_z + shell_offset
		else:
			_shotgun_barrel_assembly.rotation.x = lerpf(_shotgun_barrel_assembly.rotation.x, 0.0, clampf(delta * 18.0, 0.0, 1.0))
			if _shotgun_top_lever != null:
				_shotgun_top_lever.rotation.y = lerpf(_shotgun_top_lever.rotation.y, 0.0, clampf(delta * 18.0, 0.0, 1.0))
			if _shotgun_shell_left != null:
				_shotgun_shell_left.position.z = lerpf(_shotgun_shell_left.position.z, _shotgun_shell_left_default_z, clampf(delta * 18.0, 0.0, 1.0))
			if _shotgun_shell_right != null:
				_shotgun_shell_right.position.z = lerpf(_shotgun_shell_right.position.z, _shotgun_shell_right_default_z, clampf(delta * 18.0, 0.0, 1.0))

	if _shotgun_hammer_left != null and _shotgun_hammer_right != null:
		if _hammer_snap_timer > 0.0 and active_weapon_id == "shotgun":
			var target_hx: float = deg_to_rad(28.0) if _hammer_snap_timer > 0.07 else deg_to_rad(-16.0)
			_shotgun_hammer_left.rotation.x = lerpf(_shotgun_hammer_left.rotation.x, target_hx, clampf(delta * 35.0, 0.0, 1.0))
			_shotgun_hammer_right.rotation.x = lerpf(_shotgun_hammer_right.rotation.x, target_hx, clampf(delta * 35.0, 0.0, 1.0))
		else:
			_shotgun_hammer_left.rotation.x = lerpf(_shotgun_hammer_left.rotation.x, 0.0, clampf(delta * 16.0, 0.0, 1.0))
			_shotgun_hammer_right.rotation.x = lerpf(_shotgun_hammer_right.rotation.x, 0.0, clampf(delta * 16.0, 0.0, 1.0))


func _update_stakedriver_mechanisms(delta: float) -> void:
	if _driver_flywheel != null:
		_driver_flywheel.rotation.x = lerpf(
			_driver_flywheel.rotation.x,
			_driver_flywheel_target_angle,
			clampf(delta * 14.0, 0.0, 1.0)
		)

	if _driver_loading_crank != null:
		_driver_loading_crank.rotation.x = lerpf(
			_driver_loading_crank.rotation.x,
			_driver_crank_target_angle,
			clampf(delta * 14.0, 0.0, 1.0)
		)

	if _driver_stake_ram != null:
		if _driver_ram_timer > 0.0:
			_driver_ram_timer = maxf(0.0, _driver_ram_timer - delta)
			if _driver_ram_timer > 0.08:
				_driver_stake_ram.position.z = lerpf(
					_driver_stake_ram.position.z,
					_driver_ram_default_z - 0.18,
					clampf(delta * 42.0, 0.0, 1.0)
				)
			else:
				_driver_stake_ram.position.z = lerpf(
					_driver_stake_ram.position.z,
					_driver_ram_default_z,
					clampf(delta * 20.0, 0.0, 1.0)
				)
		else:
			_driver_stake_ram.position.z = lerpf(
				_driver_stake_ram.position.z,
				_driver_ram_default_z,
				clampf(delta * 16.0, 0.0, 1.0)
			)


func _fire_active_weapon() -> void:
	match active_weapon_id:
		"shotgun":
			_fire_shotgun()
		"stakedriver":
			_fire_stakedriver()
		_:
			_fire_revolver()


func _reload_active_weapon() -> void:
	match active_weapon_id:
		"shotgun":
			_reload_shotgun()
		"stakedriver":
			_reload_stakedriver()
		_:
			_reload_revolver()


func _fire_revolver() -> void:
	if _fire_cooldown_remaining > 0.0 or _is_reloading:
		return

	if current_ammo <= 0:
		_play_weapon_sfx(_sfx_revolver_dry_fire)
		_reload_revolver()
		return

	current_ammo -= 1
	ammo_by_weapon["revolver"] = current_ammo
	shots_fired_total += 1
	var rate_mult: float = loadout_manager.fire_rate_mult if loadout_manager != null else 1.0
	_fire_cooldown_remaining = 0.28 / maxf(rate_mult, 0.2)
	ammo_changed.emit(current_ammo, max_ammo)

	_play_weapon_sfx(_sfx_revolver_fire, _sfx_revolver_cock)
	_trigger_gunfire_ambient_duck()
	_notify_hud_reticle_spread(24.0)

	# 1. 6-DOF Underdamped Spring Recoil with Randomized Torque & Positional Kick
	var pitch_kick: float = deg_to_rad(_rng.randf_range(16.0, 22.0)) * recoil_mult
	var yaw_kick: float = deg_to_rad(_non_zero_signed_range(1.8, 5.5)) * recoil_mult
	var roll_kick: float = deg_to_rad(_non_zero_signed_range(2.5, 8.0)) * recoil_mult
	var pos_kick: Vector3 = Vector3(_non_zero_signed_range(0.004, 0.015), 0.035, 0.085) * recoil_mult
	add_recoil_impulse(pos_kick, Vector3(pitch_kick, yaw_kick, roll_kick))
	trigger_shoot_recoil(1.0)

	# Left hand lantern subtle reaction
	_pendulum_vel_x += 3.5
	left_recoil_offset_pos += Vector3(0.0, 0.012, 0.02)

	# 2. Mechanical targets: 60-deg Cylinder step, Hammer snap backward/forward, Trigger, Gear, Ejector
	cylinder_target_angle += deg_to_rad(60.0)
	_gear_target_angle -= deg_to_rad(90.0)
	_hammer_snap_timer = 0.14
	if _revolver_hammer != null:
		_revolver_hammer.rotation.x = deg_to_rad(28.0)
	_trigger_snap_timer = 0.14
	if _revolver_trigger != null:
		_revolver_trigger.rotation.x = deg_to_rad(-22.0)
	_ejector_snap_timer = 0.14
	if _revolver_ejector_rod != null:
		_revolver_ejector_rod.position.z = _ejector_default_z + 0.016

	# Immediately apply updated recoil transform so RightHandPivot spikes upward right away
	_apply_hand_transforms()

	# 3. Upward Camera Recoil Kick & Perlin Trauma Shake on Player
	_add_player_camera_trauma(0.38, Vector3(deg_to_rad(1.4), yaw_kick * 0.15, roll_kick * 0.15))
	if _player is FPSController:
		var fps_p: FPSController = _player as FPSController
		if fps_p.head != null:
			fps_p.head.rotation.x = clampf(
				fps_p.head.rotation.x + deg_to_rad(1.4),
				deg_to_rad(-85.0),
				deg_to_rad(85.0)
			)

	# 4. Crisp Muzzle Flash & Fast Spark Streaks at Barrel Tip (Vector3(0.0, 0.06, -0.55) local to RightHandPivot)
	if muzzle_flash_light != null:
		muzzle_flash_light.position = Vector3(0.0, 0.06, -0.55)
		muzzle_flash_light.visible = true
		muzzle_flash_light.light_energy = 3.2
		_muzzle_flash_timer = 0.06

	if muzzle_particles != null:
		muzzle_particles.position = Vector3(0.0, 0.06, -0.55)
		muzzle_particles.restart()
		muzzle_particles.emitting = true

	# 5. Hitscan RayCast & Impact Sparks
	_perform_hitscan()


func _fire_shotgun() -> void:
	if _fire_cooldown_remaining > 0.0 or _is_reloading:
		return

	if current_ammo <= 0:
		_reload_shotgun()
		return

	current_ammo -= 1
	ammo_by_weapon["shotgun"] = current_ammo
	shots_fired_total += 1
	var rate_mult: float = loadout_manager.fire_rate_mult if loadout_manager != null else 1.0
	_fire_cooldown_remaining = 0.52 / maxf(rate_mult, 0.2)
	ammo_changed.emit(current_ammo, max_ammo)

	# 1. Heavy 6-DOF Spring Recoil with Randomized Torque & Positional Kick
	var pitch_kick: float = deg_to_rad(_rng.randf_range(28.0, 35.0)) * recoil_mult
	var yaw_kick: float = deg_to_rad(_non_zero_signed_range(3.0, 9.0)) * recoil_mult
	var roll_kick: float = deg_to_rad(_non_zero_signed_range(4.0, 12.0)) * recoil_mult
	var pos_kick: Vector3 = Vector3(_non_zero_signed_range(0.008, 0.025), 0.055, 0.14) * recoil_mult
	add_recoil_impulse(pos_kick, Vector3(pitch_kick, yaw_kick, roll_kick))
	trigger_shoot_recoil(1.35)

	_pendulum_vel_x += 5.5
	left_recoil_offset_pos += Vector3(0.0, 0.02, 0.035)

	_hammer_snap_timer = 0.16
	if _shotgun_hammer_left != null:
		_shotgun_hammer_left.rotation.x = deg_to_rad(28.0)
	if _shotgun_hammer_right != null:
		_shotgun_hammer_right.rotation.x = deg_to_rad(28.0)

	_play_weapon_sfx(_sfx_shotgun_fire)
	_trigger_gunfire_ambient_duck()
	_notify_hud_reticle_spread(42.0)
	_apply_hand_transforms()

	_add_player_camera_trauma(0.68, Vector3(deg_to_rad(2.6), yaw_kick * 0.18, roll_kick * 0.18))
	if _player is FPSController:
		var fps_p: FPSController = _player as FPSController
		if fps_p.head != null:
			fps_p.head.rotation.x = clampf(
				fps_p.head.rotation.x + deg_to_rad(2.6),
				deg_to_rad(-85.0),
				deg_to_rad(85.0)
			)

	if muzzle_flash_light != null:
		muzzle_flash_light.position = Vector3(0.0, 0.07, -0.62)
		muzzle_flash_light.visible = true
		muzzle_flash_light.light_energy = 5.4
		_muzzle_flash_timer = 0.08

	if muzzle_particles != null:
		muzzle_particles.position = Vector3(0.0, 0.07, -0.62)
		muzzle_particles.restart()
		muzzle_particles.emitting = true

	_perform_shotgun_spread_hitscan()


func _perform_shotgun_spread_hitscan() -> void:
	if hitscan_raycast == null:
		return

	if _player != null:
		hitscan_raycast.add_exception(_player)

	var orig_target: Vector3 = hitscan_raycast.target_position
	var ray_len: float = maxf(orig_target.length(), 40.0)
	var spread_rad: float = deg_to_rad(5.5)

	var pellet_offsets: Array[Vector2] = [
		Vector2(0.0, 0.0),
		Vector2(spread_rad * 0.55, 0.0),
		Vector2(-spread_rad * 0.55, 0.0),
		Vector2(0.0, spread_rad * 0.55),
		Vector2(0.0, -spread_rad * 0.55),
		Vector2(spread_rad * 0.85, spread_rad * 0.75),
		Vector2(-spread_rad * 0.85, spread_rad * 0.75),
		Vector2(0.0, -spread_rad * 0.95)
	]

	var pellet_dmg: float = _get_pellet_damage()
	var knockback_enemies: Array[TestDummyEnemy] = []
	var forward_dir: Vector3 = -global_transform.basis.z.normalized()
	var hit_any_enemy: bool = false
	var crit_or_kill: bool = false

	for i: int in range(pellet_offsets.size()):
		var off: Vector2 = pellet_offsets[i]
		var dir_local: Vector3 = Vector3(sin(off.x), sin(off.y), -cos(off.x) * cos(off.y)).normalized()
		hitscan_raycast.target_position = dir_local * ray_len
		hitscan_raycast.force_raycast_update()
		if hitscan_raycast.is_colliding():
			var col_obj: Object = hitscan_raycast.get_collider()
			if col_obj == _player:
				continue
			var hit_pos: Vector3 = hitscan_raycast.get_collision_point()
			var hit_norm: Vector3 = hitscan_raycast.get_collision_normal()
			if i < 3:
				_spawn_impact_effect(hit_pos, hit_norm)
			if col_obj is Node:
				var hit_enemy: TestDummyEnemy = _find_enemy_from_node(col_obj as Node)
				if hit_enemy != null and is_instance_valid(hit_enemy):
					hit_any_enemy = true
					if (hit_pos.y - hit_enemy.global_position.y) >= 1.30:
						crit_or_kill = true
					hit_enemy.apply_damage(pellet_dmg, false)
					if not is_instance_valid(hit_enemy) or not hit_enemy.is_alive():
						crit_or_kill = true
					if is_instance_valid(hit_enemy) and not knockback_enemies.has(hit_enemy):
						knockback_enemies.append(hit_enemy)
				else:
					var hit_plaque: TargetDummyPlaque = _find_target_plaque_from_node(col_obj as Node)
					if hit_plaque != null:
						hit_plaque.take_damage(pellet_dmg, false, hit_pos, hit_norm)

	hitscan_raycast.target_position = orig_target

	if hit_any_enemy:
		_notify_hud_hitmarker(crit_or_kill)

	for kb_enemy: TestDummyEnemy in knockback_enemies:
		if kb_enemy != null and is_instance_valid(kb_enemy):
			kb_enemy.apply_knockback_stagger(forward_dir * 1.45, 0.45)
			if loadout_manager != null and loadout_manager.has_relic(5):
				kb_enemy.apply_bile_dot(12.0, 4.0)


func _get_pellet_damage() -> float:
	if loadout_manager == null and _player != null:
		loadout_manager = _player.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	if loadout_manager != null:
		var bl_steps: int = maxi(0, loadout_manager.bloodlust_rank - 1)
		var bl_mult: float = 1.0 + float(bl_steps) * 0.12
		return roundf(16.0 * loadout_manager._consecration_damage_mult * bl_mult)
	return 16.0


func _fire_stakedriver() -> void:
	if _fire_cooldown_remaining > 0.0 or _is_reloading:
		return

	if current_ammo <= 0:
		_reload_stakedriver()
		return

	current_ammo -= 1
	ammo_by_weapon["stakedriver"] = current_ammo
	shots_fired_total += 1
	var rate_mult: float = loadout_manager.fire_rate_mult if loadout_manager != null else 1.0
	_fire_cooldown_remaining = 0.44 / maxf(rate_mult, 0.2)
	ammo_changed.emit(current_ammo, max_ammo)

	# 1. Mechanical StakeRam forward slam (-0.18m) & FlywheelGear 720-deg spin
	_driver_ram_timer = 0.20
	if _driver_stake_ram != null:
		_driver_stake_ram.position.z = _driver_ram_default_z - 0.18
	_driver_flywheel_target_angle += TAU * 2.0
	_driver_crank_target_angle += TAU

	# 6-DOF Underdamped Spring Recoil with Randomized Torque & Positional Kick
	var pitch_kick: float = deg_to_rad(_rng.randf_range(18.0, 24.0)) * recoil_mult
	var yaw_kick: float = deg_to_rad(_non_zero_signed_range(1.5, 4.5)) * recoil_mult
	var roll_kick: float = deg_to_rad(_non_zero_signed_range(3.0, 10.0)) * recoil_mult
	var pos_kick: Vector3 = Vector3(_non_zero_signed_range(0.005, 0.018), 0.04, 0.13) * recoil_mult
	add_recoil_impulse(pos_kick, Vector3(pitch_kick, yaw_kick, roll_kick))
	trigger_shoot_recoil(1.2)

	_pendulum_vel_x += 4.2
	left_recoil_offset_pos += Vector3(0.0, 0.015, 0.025)

	_play_weapon_sfx(_sfx_stakedriver_fire)
	_trigger_gunfire_ambient_duck()
	_notify_hud_reticle_spread(30.0)
	_apply_hand_transforms()
	_add_player_camera_trauma(0.52, Vector3(deg_to_rad(2.0), yaw_kick * 0.15, roll_kick * 0.15))

	if muzzle_flash_light != null:
		muzzle_flash_light.position = Vector3(0.0, 0.05, -0.58)
		muzzle_flash_light.visible = true
		muzzle_flash_light.light_energy = 3.8
		_muzzle_flash_timer = 0.06

	if muzzle_particles != null:
		muzzle_particles.position = Vector3(0.0, 0.05, -0.58)
		muzzle_particles.restart()
		muzzle_particles.emitting = true

	_perform_stakedriver_pierce_and_cleave()


func _perform_stakedriver_pierce_and_cleave() -> void:
	var stake_dmg: float = _get_stakedriver_pierce_damage()
	var cleave_dmg: float = _get_stakedriver_cleave_damage()
	var pierced_enemies: Array[TestDummyEnemy] = []
	var hit_any_enemy: bool = false
	var crit_or_kill: bool = false

	# 1. Up to 3 enemies pierced along raycast line with armor_piercing = true (ignores 100% flat armor)
	if hitscan_raycast != null:
		if _player != null:
			hitscan_raycast.add_exception(_player)
		for pierce_idx: int in range(3):
			hitscan_raycast.force_raycast_update()
			if not hitscan_raycast.is_colliding():
				break
			var col_obj: Object = hitscan_raycast.get_collider()
			if col_obj == _player:
				break
			var hit_pos: Vector3 = hitscan_raycast.get_collision_point()
			var hit_norm: Vector3 = hitscan_raycast.get_collision_normal()
			_spawn_impact_effect(hit_pos, hit_norm)
			if col_obj is Node:
				var hit_enemy: TestDummyEnemy = _find_enemy_from_node(col_obj as Node)
				if hit_enemy != null and is_instance_valid(hit_enemy) and not pierced_enemies.has(hit_enemy):
					if (hit_pos.y - hit_enemy.global_position.y) >= 1.30:
						crit_or_kill = true
					pierced_enemies.append(hit_enemy)
					hitscan_raycast.add_exception(hit_enemy)
				else:
					var hit_plaque: TargetDummyPlaque = _find_target_plaque_from_node(col_obj as Node)
					if hit_plaque != null:
						hit_plaque.take_damage(stake_dmg, true, hit_pos, hit_norm)
					break
			else:
				break

		for pe: TestDummyEnemy in pierced_enemies:
			if pe != null and is_instance_valid(pe):
				hit_any_enemy = true
				hitscan_raycast.remove_exception(pe)
				pe.apply_damage(stake_dmg, true)
				if not is_instance_valid(pe) or not pe.is_alive():
					crit_or_kill = true
				if is_instance_valid(pe) and loadout_manager != null and loadout_manager.has_relic(5):
					pe.apply_bile_dot(12.0, 4.0)

	# 2. Close-Range Ritual Cleaver Slash (within 2.6m in front of player)
	var player_pos: Vector3 = (_player.global_position if _player.is_inside_tree() else _player.position) if _player != null else (global_position if is_inside_tree() else position)
	var cur_basis: Basis = global_transform.basis if is_inside_tree() else transform.basis
	var forward_dir: Vector3 = -cur_basis.z.normalized()
	var cleaved_any: bool = false
	for enemy: TestDummyEnemy in _collect_all_enemies():
		if enemy == null or not is_instance_valid(enemy):
			continue
		var to_enemy: Vector3 = enemy.global_position - player_pos
		var dist: float = to_enemy.length()
		if dist <= 2.6:
			var flat_to: Vector3 = Vector3(to_enemy.x, 0.0, to_enemy.z).normalized()
			var flat_fwd: Vector3 = Vector3(forward_dir.x, 0.0, forward_dir.z).normalized()
			if dist <= 1.2 or flat_fwd.dot(flat_to) >= 0.25:
				enemy.apply_damage(cleave_dmg, true)
				hit_any_enemy = true
				if not is_instance_valid(enemy) or not enemy.is_alive():
					crit_or_kill = true
				cleaved_any = true
	if cleaved_any:
		_play_weapon_sfx(_sfx_stakedriver_fire, _sfx_stakedriver_cleave)
	if hit_any_enemy:
		_notify_hud_hitmarker(crit_or_kill)


func _get_stakedriver_pierce_damage() -> float:
	if loadout_manager == null and _player != null:
		loadout_manager = _player.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	if loadout_manager != null:
		var bl_steps: int = maxi(0, loadout_manager.bloodlust_rank - 1)
		var bl_mult: float = 1.0 + float(bl_steps) * 0.12
		return roundf(65.0 * loadout_manager._consecration_damage_mult * bl_mult)
	return 65.0


func _get_stakedriver_cleave_damage() -> float:
	if loadout_manager == null and _player != null:
		loadout_manager = _player.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	if loadout_manager != null:
		var bl_steps: int = maxi(0, loadout_manager.bloodlust_rank - 1)
		var bl_mult: float = 1.0 + float(bl_steps) * 0.12
		return roundf(45.0 * loadout_manager._consecration_damage_mult * bl_mult)
	return 45.0


func _perform_hitscan() -> void:
	if hitscan_raycast == null:
		return

	if _player != null:
		hitscan_raycast.add_exception(_player)
	hitscan_raycast.force_raycast_update()
	if hitscan_raycast.is_colliding():
		var col_obj: Object = hitscan_raycast.get_collider()
		if col_obj == _player:
			return
		var hit_pos: Vector3 = hitscan_raycast.get_collision_point()
		var hit_norm: Vector3 = hitscan_raycast.get_collision_normal()
		_spawn_impact_effect(hit_pos, hit_norm)

		if col_obj is Node:
			var hit_enemy: TestDummyEnemy = _find_enemy_from_node(col_obj as Node)
			if hit_enemy != null:
				var is_headshot: bool = (hit_pos.y - hit_enemy.global_position.y) >= 1.30
				var is_sixth_shot: bool = (current_ammo == 0) or (shots_fired_total % 6 == 0)
				_apply_revolver_hit_to_enemy(hit_enemy, hit_pos, is_headshot, is_sixth_shot)
			else:
				var hit_plaque: TargetDummyPlaque = _find_target_plaque_from_node(col_obj as Node)
				if hit_plaque != null:
					var base_dmg: float = loadout_manager.damage_per_shot if loadout_manager != null else 38.0
					hit_plaque.take_damage(base_dmg, false, hit_pos, hit_norm)


func _find_target_plaque_from_node(node: Node) -> TargetDummyPlaque:
	var curr: Node = node
	while curr != null:
		if curr is TargetDummyPlaque:
			return curr as TargetDummyPlaque
		curr = curr.get_parent()
	return null


func _find_enemy_from_node(node: Node) -> TestDummyEnemy:
	var curr: Node = node
	while curr != null:
		if curr is TestDummyEnemy:
			return curr as TestDummyEnemy
		curr = curr.get_parent()
	return null


func fire_at_enemy_target(enemy: TestDummyEnemy, is_headshot: bool = false, force_sixth_shot: bool = false) -> float:
	if enemy == null or not is_instance_valid(enemy):
		return 0.0
	if current_ammo <= 0:
		current_ammo = max_ammo
	current_ammo -= 1
	ammo_by_weapon[active_weapon_id] = current_ammo
	shots_fired_total += 1
	ammo_changed.emit(current_ammo, max_ammo)
	_trigger_gunfire_ambient_duck()

	if active_weapon_id == "shotgun":
		_play_weapon_sfx(_sfx_shotgun_fire)
		_hammer_snap_timer = 0.16
		var pellet_dmg: float = _get_pellet_damage()
		var total_dealt: float = 0.0
		for _p: int in range(8):
			if is_instance_valid(enemy) and enemy.is_alive():
				total_dealt += enemy.apply_damage(pellet_dmg, false)
		if is_instance_valid(enemy) and enemy.is_alive():
			var fwd: Vector3 = -global_transform.basis.z.normalized()
			if fwd.length_squared() < 0.01:
				fwd = Vector3(0.0, 0.0, -1.0)
			enemy.apply_knockback_stagger(fwd * 1.45, 0.45)
		return total_dealt
	elif active_weapon_id == "stakedriver":
		_play_weapon_sfx(_sfx_stakedriver_fire)
		_driver_ram_timer = 0.20
		if _driver_stake_ram != null:
			_driver_stake_ram.position.z = _driver_ram_default_z - 0.18
		_driver_flywheel_target_angle += TAU * 2.0
		_driver_crank_target_angle += TAU
		if _driver_flywheel != null:
			_driver_flywheel.rotation.x += deg_to_rad(45.0)
		var pierce_dmg: float = _get_stakedriver_pierce_damage()
		var dealt: float = enemy.apply_damage(pierce_dmg, true)
		var player_pos: Vector3 = _player.global_position if _player != null else global_position
		if is_instance_valid(enemy) and enemy.is_alive() and player_pos.distance_to(enemy.global_position) <= 2.6:
			dealt += enemy.apply_damage(_get_stakedriver_cleave_damage(), true)
		return dealt

	_play_weapon_sfx(_sfx_revolver_fire, _sfx_revolver_cock)
	var is_sixth: bool = force_sixth_shot or (current_ammo == 0) or (shots_fired_total % 6 == 0)
	return _apply_revolver_hit_to_enemy(enemy, enemy.global_position + Vector3(0.0, 1.2, 0.0), is_headshot, is_sixth)


func _apply_revolver_hit_to_enemy(
	enemy: TestDummyEnemy,
	hit_pos: Vector3,
	is_headshot: bool,
	is_sixth_shot: bool
) -> float:
	if enemy == null or not is_instance_valid(enemy):
		return 0.0

	if loadout_manager == null and _player != null:
		loadout_manager = _player.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager

	var base_dmg: float = loadout_manager.damage_per_shot if loadout_manager != null else 35.0
	var crit_mult: float = loadout_manager.crit_damage_mult if loadout_manager != null else 1.50
	var is_crit: bool = is_headshot or enemy.is_shackled()

	var final_dmg: float = base_dmg * (crit_mult if is_crit else 1.0)

	# Relic 1: Ossuary Skull Signet — Headshots/Crits refund 1 round to cylinder
	if is_crit and loadout_manager != null and loadout_manager.has_relic(1):
		current_ammo = mini(max_ammo, current_ammo + 1)
		ammo_changed.emit(current_ammo, max_ammo)

	# Relic 7: Sunken Bell Clapper — Every 6th shot (final round) unleashes a 2.2x AoE Sonic Bell Blast
	if is_sixth_shot and loadout_manager != null and loadout_manager.has_relic(7):
		final_dmg *= 2.2
		_spawn_spell_shockwave_vfx(hit_pos, 4.5, Color(1.0, 0.55, 0.18, 1.0))
		for other: TestDummyEnemy in _collect_all_enemies():
			if other != null and is_instance_valid(other) and other != enemy:
				if other.global_position.distance_to(hit_pos) <= 4.5:
					other.apply_damage(base_dmg * 1.2)

	enemy.apply_damage(final_dmg)
	var is_kill: bool = not is_instance_valid(enemy) or not enemy.is_alive()
	_notify_hud_hitmarker(is_crit or is_kill)

	# Relic 5: Plague Alchemist's Alembic — Inflict Corrosive Bile DoT (12 DMG/sec for 4.0s)
	if is_instance_valid(enemy) and loadout_manager != null and loadout_manager.has_relic(5):
		enemy.apply_bile_dot(12.0, 4.0)

	# Relic 6: Weeping Saint's Tear — Arc a Chain Frost Bolt to a second nearby enemy within 8.0m for 50% DMG
	if loadout_manager != null and loadout_manager.has_relic(6):
		var all_enemies: Array[TestDummyEnemy] = _collect_all_enemies()
		for other_e: TestDummyEnemy in all_enemies:
			if other_e != null and is_instance_valid(other_e) and other_e != enemy:
				if other_e.global_position.distance_to(hit_pos) <= 8.0:
					other_e.apply_damage(final_dmg * 0.50)
					break

	return final_dmg


func _spawn_impact_effect(pos: Vector3, normal: Vector3) -> void:
	var scene_root: Node = get_tree().current_scene if get_tree() != null else null
	if scene_root == null and _player != null and _player.get_parent() != null:
		scene_root = _player.get_parent()
	if scene_root == null and get_tree() != null:
		scene_root = get_tree().root
	if scene_root == null:
		return

	var impact: GPUParticles3D = GPUParticles3D.new()
	impact.emitting = false
	impact.one_shot = true
	impact.explosiveness = 0.95
	impact.lifetime = 0.08
	impact.amount = 10

	var mat: ParticleProcessMaterial = ParticleProcessMaterial.new()
	mat.direction = normal
	mat.spread = 35.0
	mat.initial_velocity_min = 12.0
	mat.initial_velocity_max = 18.0
	mat.gravity = Vector3(0.0, -9.8, 0.0)
	mat.particle_flag_align_y = true
	mat.color = Color(1.0, 0.75, 0.35, 1.0)
	impact.process_material = mat

	var spark_box: BoxMesh = BoxMesh.new()
	spark_box.size = Vector3(0.008, 0.04, 0.008)
	var std_mat: StandardMaterial3D = StandardMaterial3D.new()
	std_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	std_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	std_mat.albedo_color = Color(1.0, 0.80, 0.40, 1.0)
	spark_box.material = std_mat
	impact.draw_pass_1 = spark_box

	impact.position = pos + normal * 0.02
	scene_root.add_child(impact)
	impact.restart()
	impact.emitting = true

	var cleanup_timer: SceneTreeTimer = get_tree().create_timer(0.25)
	cleanup_timer.timeout.connect(func() -> void: if is_instance_valid(impact): impact.queue_free())


func _reload_revolver() -> void:
	if _is_reloading or current_ammo == max_ammo:
		return

	_is_reloading = true
	_reload_beat1_done = false
	_reload_beat2_done = false
	_reload_beat3_done = false
	_reload_duration_total = 0.75 / maxf(reload_speed_mult, 0.1)
	_reload_timer = _reload_duration_total
	cylinder_target_angle += TAU
	_gear_target_angle -= TAU
	_ejector_snap_timer = 0.35
	_play_weapon_sfx(_sfx_revolver_reload)

	_trigger_relic_reload_shockwave()


func _reload_shotgun() -> void:
	if _is_reloading or current_ammo == max_ammo:
		return

	_is_reloading = true
	_reload_beat1_done = false
	_reload_beat2_done = false
	_reload_beat3_done = false
	_shotgun_close_sfx_played = false
	_reload_duration_total = 0.90 / maxf(reload_speed_mult, 0.1)
	_reload_timer = _reload_duration_total
	if _shotgun_barrel_assembly != null:
		_shotgun_barrel_assembly.rotation.x = deg_to_rad(-42.0)
	if _shotgun_top_lever != null:
		_shotgun_top_lever.rotation.y = deg_to_rad(28.0)
	if _shotgun_shell_left != null:
		_shotgun_shell_left.position.z = _shotgun_shell_left_default_z + 0.08
	if _shotgun_shell_right != null:
		_shotgun_shell_right.position.z = _shotgun_shell_right_default_z + 0.08
	_play_weapon_sfx(_sfx_shotgun_break)
	_trigger_relic_reload_shockwave()


func _reload_stakedriver() -> void:
	if _is_reloading or current_ammo == max_ammo:
		return

	_is_reloading = true
	_reload_beat1_done = false
	_reload_beat2_done = false
	_reload_beat3_done = false
	_reload_duration_total = 0.85 / maxf(reload_speed_mult, 0.1)
	_reload_timer = _reload_duration_total
	_driver_flywheel_target_angle += TAU * 2.0
	_driver_crank_target_angle += TAU * 2.0
	_play_weapon_sfx(_sfx_shotgun_close)
	_trigger_relic_reload_shockwave()


func _trigger_relic_reload_shockwave() -> void:
	# Relic 2: Royal Necropolis Spur — Reloading unleashes a 4.0m golden shockwave damaging nearby enemies
	if loadout_manager != null and loadout_manager.has_relic(2):
		var origin: Vector3 = _player.global_position if _player != null else global_position
		_spawn_spell_shockwave_vfx(origin + Vector3(0.0, 0.85, 0.0), 4.0, Color(1.0, 0.82, 0.28, 1.0))
		for enemy: TestDummyEnemy in _collect_all_enemies():
			if enemy != null and is_instance_valid(enemy):
				if enemy.global_position.distance_to(origin) <= 4.0:
					enemy.apply_damage(35.0)


func apply_weapon_consecration(rune_color: Color, new_reload_mult: float, new_recoil_mult: float) -> void:
	if _revolver_rune_materials.is_empty():
		_resolve_nodes_and_subcomponents()

	active_rune_color = rune_color
	reload_speed_mult = new_reload_mult
	recoil_mult = new_recoil_mult

	for mat: StandardMaterial3D in _revolver_rune_materials:
		if mat != null:
			mat.emission_enabled = true
			mat.emission = rune_color
			mat.emission_energy_multiplier = 3.6
			mat.albedo_color = rune_color.darkened(0.3)

	# Trigger a tactile inspection spin & upward flourish on RightHandPivot
	cylinder_target_angle += TAU
	_gear_target_angle -= TAU
	_ejector_snap_timer = 0.30
	add_recoil_impulse(Vector3(0.0, 0.03, -0.02), Vector3(deg_to_rad(14.0), deg_to_rad(2.5), deg_to_rad(18.0)))
	_apply_hand_transforms()


func _notify_hud_reticle_spread(amount: float) -> void:
	if loadout_manager != null and loadout_manager.hud != null:
		loadout_manager.hud.add_reticle_spread(amount)


func _notify_hud_hitmarker(is_crit: bool) -> void:
	if loadout_manager != null and loadout_manager.hud != null:
		loadout_manager.hud.trigger_hitmarker(is_crit)


func _bind_loadout_gauntlet_sync() -> void:
	if loadout_manager == null and _player != null:
		loadout_manager = _player.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	if loadout_manager == null:
		var p: Node = get_parent()
		while p != null:
			var lm: PlayerLoadoutManager = p.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
			if lm != null:
				loadout_manager = lm
				break
			p = p.get_parent()
	if loadout_manager != null and is_instance_valid(loadout_manager):
		if loadout_manager.viewmodel_controller == null:
			loadout_manager.viewmodel_controller = self
		if not loadout_manager.loadout_changed.is_connected(_on_loadout_hands_changed):
			loadout_manager.loadout_changed.connect(_on_loadout_hands_changed)


func _on_loadout_hands_changed() -> void:
	if loadout_manager == null or not is_instance_valid(loadout_manager):
		return
	var hands_idx: int = loadout_manager.get_equipped_armor_slot("HANDS")
	if hands_idx != equipped_armor_index or active_gauntlet_instance == null:
		equip_armor_gauntlet(hands_idx, false)


func equip_armor_gauntlet(armor_index: int, play_flourish: bool = true) -> void:
	_bind_loadout_gauntlet_sync()
	var clamped_idx: int = posmod(armor_index, 4)
	equipped_armor_index = clamped_idx

	if left_hand_pivot == null:
		left_hand_pivot = get_node_or_null("LeftHandPivot") as Node3D
		if left_hand_pivot == null:
			left_hand_pivot = find_child("LeftHandPivot", true, false) as Node3D
	if right_hand_pivot == null:
		right_hand_pivot = get_node_or_null("RightHandPivot") as Node3D
		if right_hand_pivot == null:
			right_hand_pivot = find_child("RightHandPivot", true, false) as Node3D
	if left_hand_pivot == null:
		return

	# Ensure LanternPendulum is detached from legacy LeftArmGauntlet and stays visible
	if _lantern_pendulum == null:
		_lantern_pendulum = left_hand_pivot.find_child("LanternPendulum", true, false) as Node3D
	if _lantern_pendulum != null:
		if _lantern_pendulum.get_parent() != left_hand_pivot:
			var pend_pos: Vector3 = _lantern_pendulum.position
			_lantern_pendulum.owner = null
			if _lantern_pendulum.get_parent() != null:
				_lantern_pendulum.get_parent().remove_child(_lantern_pendulum)
			left_hand_pivot.add_child(_lantern_pendulum)
			_lantern_pendulum.position = pend_pos
		_lantern_pendulum.visible = true

	if left_arm_gauntlet == null:
		left_arm_gauntlet = left_hand_pivot.find_child("LeftArmGauntlet", true, false) as Node3D
	if left_arm_gauntlet != null:
		left_arm_gauntlet.visible = false

	for w_node: Node3D in [weapon_revolver, weapon_shotgun, weapon_stakedriver]:
		if w_node != null:
			var r_gaunt: Node3D = w_node.find_child("RightArmGauntlet", true, false) as Node3D
			if r_gaunt != null:
				r_gaunt.visible = false

	# Free previous active 3D gauntlet instances safely (and ensure no extra arm exists on RightHandPivot)
	for prev_g: Node3D in [active_gauntlet_instance, active_right_gauntlet_instance]:
		if prev_g != null and is_instance_valid(prev_g):
			prev_g.visible = false
			if prev_g.get_parent() != null:
				prev_g.get_parent().remove_child(prev_g)
			prev_g.queue_free()
	if right_hand_pivot != null:
		for ch: Node in right_hand_pivot.get_children():
			if ch.name.begins_with("ActiveRightArmorGauntlet") or ch.name.begins_with("ActiveArmorGauntlet"):
				ch.visible = false
				right_hand_pivot.remove_child(ch)
				ch.queue_free()
	active_gauntlet_instance = null
	active_right_gauntlet_instance = null

	var prefab_path: String = ARMOR_GAUNTLET_PREFABS[clamped_idx]
	var glb_path: String = ARMOR_GAUNTLET_GLBS[clamped_idx]
	active_gauntlet_model_path = glb_path
	var loaded_scene: PackedScene = null
	if ResourceLoader.exists(glb_path):
		loaded_scene = load(glb_path) as PackedScene
	if loaded_scene == null and ResourceLoader.exists(prefab_path):
		loaded_scene = load(prefab_path) as PackedScene

	if loaded_scene != null:
		var inst: Node3D = loaded_scene.instantiate() as Node3D
		if inst != null:
			inst.name = "ActiveArmorGauntlet_%d" % (clamped_idx + 1)
			inst.transform = Transform3D.IDENTITY
			inst.set_meta("source_model_path", glb_path)
			left_hand_pivot.set_meta("source_model_path", glb_path)
			left_hand_pivot.add_child(inst)
			active_gauntlet_instance = inst
			_configure_viewmodel_meshes_recursive(inst, false)

	if play_flourish:
		recoil_offset_pos += Vector3(0.0, -0.025, 0.03)
		left_recoil_offset_pos += Vector3(0.0, -0.025, 0.03)
		_pendulum_vel_z += 2.5
		_apply_hand_transforms()


func apply_armor_tier(plate_color: Color, plate_metallic: float, plate_roughness: float, trim_color: Color, leather_color: Color) -> void:
	active_armor_plate_color = plate_color
	_active_plate_metallic = plate_metallic
	_active_plate_roughness = plate_roughness
	_active_trim_color = trim_color
	_active_leather_color = leather_color
	_has_custom_armor_tier = true

	if _gauntlet_plate_materials.is_empty():
		_resolve_nodes_and_subcomponents()

	for mat: StandardMaterial3D in _gauntlet_plate_materials:
		if mat != null:
			mat.albedo_color = plate_color
			mat.metallic = plate_metallic
			mat.roughness = plate_roughness

	for mat: StandardMaterial3D in _gauntlet_trim_materials:
		if mat != null:
			mat.albedo_color = trim_color
			mat.metallic = clampf(plate_metallic + 0.08, 0.0, 0.96)
			mat.roughness = clampf(plate_roughness - 0.06, 0.20, 0.90)

	for mat: StandardMaterial3D in _gauntlet_leather_materials:
		if mat != null:
			mat.albedo_color = leather_color

	# Subtle gauntlet equip flourish on both hands
	recoil_offset_pos += Vector3(0.0, -0.025, 0.03)
	left_recoil_offset_pos += Vector3(0.0, -0.025, 0.03)
	_pendulum_vel_z += 2.5
	_apply_hand_transforms()


func apply_sanctuary_blessing(range_bonus: float, energy_bonus: float) -> void:
	lantern_range_bonus = range_bonus
	lantern_energy_bonus = energy_bonus
	current_ammo = max_ammo
	ammo_by_weapon["revolver"] = max_ammo_by_weapon["revolver"]
	ammo_by_weapon["shotgun"] = max_ammo_by_weapon["shotgun"]
	ammo_by_weapon["stakedriver"] = max_ammo_by_weapon["stakedriver"]
	_is_reloading = false
	ammo_changed.emit(current_ammo, max_ammo)

	if lantern_light == null:
		_resolve_nodes_and_subcomponents()
	if lantern_light != null:
		var base_range: float = lantern_raised_range if _is_lantern_raised else lantern_base_range
		var base_energy: float = (lantern_base_energy * 1.25) if _is_lantern_raised else lantern_base_energy
		lantern_light.omni_range = base_range + lantern_range_bonus
		lantern_light.light_energy = base_energy + lantern_energy_bonus
		lantern_light.omni_attenuation = lantern_attenuation
		lantern_light.distance_fade_enabled = false
