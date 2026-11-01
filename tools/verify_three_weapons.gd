extends SceneTree


func _init() -> void:
	call_deferred("_run_verification")


func _run_verification() -> void:
	print("[VerifyWeapons] Starting 3-weapon arsenal verification...")

	var level_scn: PackedScene = load("res://scenes/levels/town_overworld.tscn") as PackedScene
	if level_scn == null:
		push_error("[VerifyWeapons] FAIL: Could not load town_overworld.tscn")
		quit(1)
		return

	var level: Node3D = level_scn.instantiate() as Node3D
	root.add_child(level)
	await process_frame
	await process_frame

	var player: FPSController = level.find_child("Player", true, false) as FPSController
	if player == null:
		player = level.find_child("FPSPlayer", true, false) as FPSController
	var vm: FPSViewmodelController = level.find_child("ViewmodelRig", true, false) as FPSViewmodelController
	var lm: PlayerLoadoutManager = level.find_child("PlayerLoadoutManager", true, false) as PlayerLoadoutManager
	var hud: FPSHUD = level.find_child("HUD", true, false) as FPSHUD

	if player == null or vm == null or lm == null or hud == null:
		push_error("[VerifyWeapons] FAIL: Missing FPSPlayer, ViewmodelRig, PlayerLoadoutManager, or HUD")
		quit(1)
		return

	# 1. Verify all 3 weapon models exist under RightHandPivot
	var w_rev: Node3D = vm.weapon_revolver
	var w_sg: Node3D = vm.weapon_shotgun
	var w_sd: Node3D = vm.weapon_stakedriver

	if w_rev == null or w_sg == null or w_sd == null:
		push_error("[VerifyWeapons] FAIL: Missing WeaponRevolver, WeaponShotgun, or WeaponStakeDriver under RightHandPivot")
		quit(1)
		return

	if not w_rev.visible or w_sg.visible or w_sd.visible or vm.max_ammo != 6:
		push_error("[VerifyWeapons] FAIL: Default weapon state is not Revolver (6/6)")
		quit(1)
		return
	print("[VerifyWeapons] PASS 1A: All 3 weapon models present under RightHandPivot; default is WeaponRevolver (6/6)")

	# 2. Verify swap_weapon cycles through Revolver (6) -> Coach Gun (2) -> Stake-Driver (4) -> Revolver (6)
	lm.swap_weapon(1)
	if lm.active_weapon_id != "shotgun" or not w_sg.visible or w_rev.visible or w_sd.visible or vm.max_ammo != 2:
		push_error("[VerifyWeapons] FAIL: Swapping to shotgun failed (active=%s, max_ammo=%d)" % [lm.active_weapon_id, vm.max_ammo])
		quit(1)
		return
	print("[VerifyWeapons] PASS 1B: Swapped to Hellfire Coach Gun (visible=true, max_ammo=2)")

	lm.swap_weapon(1)
	if lm.active_weapon_id != "stakedriver" or not w_sd.visible or w_rev.visible or w_sg.visible or vm.max_ammo != 4:
		push_error("[VerifyWeapons] FAIL: Swapping to stakedriver failed (active=%s, max_ammo=%d)" % [lm.active_weapon_id, vm.max_ammo])
		quit(1)
		return
	print("[VerifyWeapons] PASS 1C: Swapped to Pneumatic Stake-Driver (visible=true, max_ammo=4)")

	lm.swap_weapon(1)
	if lm.active_weapon_id != "revolver" or not w_rev.visible or vm.max_ammo != 6:
		push_error("[VerifyWeapons] FAIL: Swapping back to revolver failed")
		quit(1)
		return
	print("[VerifyWeapons] PASS 1D: Cycled back to Occult Revolver (6/6)")

	# 3. Verify Hellfire Coach Gun firing (8 pellets spread, knockback) and Break-Action Reload
	lm.equip_weapon("shotgun")
	var dummy_sg: TestDummyEnemy = TestDummyEnemy.new()
	dummy_sg.name = "ShotgunTestDummy"
	dummy_sg.max_health = 500.0
	dummy_sg.current_health = 500.0
	level.add_child(dummy_sg)
	dummy_sg.global_position = player.global_position + Vector3(0.0, 0.0, -3.0)
	var before_pos: Vector3 = dummy_sg.position

	var sg_dealt: float = vm.fire_at_enemy_target(dummy_sg)
	var moved_dist: float = dummy_sg.position.distance_to(before_pos)
	if sg_dealt < 120.0 or moved_dist < 0.25:
		push_error("[VerifyWeapons] FAIL: Coach Gun point-blank 8-pellet damage or knockback insufficient (dealt=%.1f, moved=%.2f)" % [sg_dealt, moved_dist])
		quit(1)
		return
	print("[VerifyWeapons] PASS 2A: Coach Gun dealt %.1f damage across 8 pellets and knocked enemy back %.2fm" % [sg_dealt, moved_dist])

	# Trigger break-action reload and check BarrelAssembly rotation
	vm._reload_shotgun()
	vm._update_shotgun_mechanisms(0.05)
	if vm._shotgun_barrel_assembly == null or absf(vm._shotgun_barrel_assembly.rotation.x) <= 0.30:
		push_error("[VerifyWeapons] FAIL: Coach Gun BarrelAssembly did not rotate open on reload")
		quit(1)
		return
	print("[VerifyWeapons] PASS 2B: Coach Gun break-action reload rotated BarrelAssembly to %.2f rad" % vm._shotgun_barrel_assembly.rotation.x)

	# Finish reload
	vm._process(1.2)

	# 4. Verify Pneumatic Stake-Driver mechanical parts & 100% Flat Armor Penetration against Iron Penitent
	var penitent_scn: PackedScene = load("res://scenes/prefabs/enemies/enemy_iron_penitent.tscn") as PackedScene
	var penitent_rev: TestDummyEnemy = penitent_scn.instantiate() as TestDummyEnemy
	penitent_rev.max_health = 300.0
	penitent_rev.current_health = 300.0
	level.add_child(penitent_rev)
	penitent_rev.global_position = player.global_position + Vector3(0.0, 0.0, -6.0)
	await process_frame

	if penitent_rev.flat_armor < 10.0:
		push_error("[VerifyWeapons] FAIL: Iron Penitent flat_armor not configured (flat_armor=%.1f)" % penitent_rev.flat_armor)
		quit(1)
		return

	# Fire Revolver body-shot against armored Iron Penitent (38 base - 15 flat armor = 23 damage)
	lm.equip_weapon("revolver")
	var hp_before_rev: float = penitent_rev.current_health
	vm.fire_at_enemy_target(penitent_rev, false, false)
	var rev_effective_loss: float = hp_before_rev - penitent_rev.current_health

	# Now equip Stake-Driver and fire at Iron Penitent at 6.0m (65 armor-piercing damage, ignoring 15 flat armor!)
	lm.equip_weapon("stakedriver")
	var fw_before: float = vm._driver_flywheel.rotation.x if vm._driver_flywheel != null else 0.0
	var ram_z_default: float = vm._driver_ram_default_z
	var hp_before_sd: float = penitent_rev.current_health
	vm.fire_at_enemy_target(penitent_rev, false, false)
	var sd_effective_loss: float = hp_before_sd - penitent_rev.current_health
	var ram_z_fired: float = vm._driver_stake_ram.position.z if vm._driver_stake_ram != null else 0.0
	vm._update_stakedriver_mechanisms(0.05)
	var fw_after: float = vm._driver_flywheel.rotation.x if vm._driver_flywheel != null else 0.0

	if rev_effective_loss >= 38.0 or sd_effective_loss < 65.0:
		push_error(
			"[VerifyWeapons] FAIL: Armor penetration test failed (Revolver loss=%.1f, Stake-Driver loss=%.1f)"
			% [rev_effective_loss, sd_effective_loss]
		)
		quit(1)
		return
	if absf(ram_z_fired - ram_z_default) < 0.05 or absf(fw_after - fw_before) < 0.10:
		push_error("[VerifyWeapons] FAIL: StakeRam or FlywheelGear did not animate on Stake-Driver fire")
		quit(1)
		return
	print(
		"[VerifyWeapons] PASS 3: Stake-Driver bypassed Iron Penitent flat armor (%.1f full AP DMG vs %.1f reduced Revolver DMG) and animated StakeRam/FlywheelGear"
		% [sd_effective_loss, rev_effective_loss]
	)

	# 5. Verify Gunsmith Workbench consecration updates GlowingOccultRune materials across all 3 weapon models
	lm.cycle_weapon_mod(1)
	if vm._revolver_rune_materials.size() < 3:
		push_error("[VerifyWeapons] FAIL: Expected rune materials across all 3 weapons, found %d" % vm._revolver_rune_materials.size())
		quit(1)
		return
	print("[VerifyWeapons] PASS 4: Gunsmith Workbench consecrated %d rune material surfaces across all 3 weapons" % vm._revolver_rune_materials.size())

	# 6. Verify all 8 Visceral Stereo Weapon .wav files load as 2-Channel Stereo and wrap cleanly in AudioStreamRandomizer
	var expected_stereo_wavs: Array[String] = [
		"res://assets/audio/sfx/revolver_fire.wav",
		"res://assets/audio/sfx/revolver_cock_click.wav",
		"res://assets/audio/sfx/revolver_reload.wav",
		"res://assets/audio/sfx/revolver_dry_fire.wav",
		"res://assets/audio/sfx/shotgun_fire_boom.wav",
		"res://assets/audio/sfx/shotgun_break_open.wav",
		"res://assets/audio/sfx/shotgun_shell_load_close.wav",
		"res://assets/audio/sfx/stakedriver_fire_pneumatic.wav",
	]
	for wav_path: String in expected_stereo_wavs:
		var wav_stream: AudioStreamWAV = load(wav_path) as AudioStreamWAV
		if wav_stream == null or not wav_stream.stereo:
			push_error("[VerifyWeapons] FAIL: %s did not load as a 2-channel stereo AudioStreamWAV" % wav_path)
			quit(1)
			return

	var randomizers: Array[AudioStreamRandomizer] = [
		vm._sfx_revolver_fire,
		vm._sfx_revolver_cock,
		vm._sfx_revolver_reload,
		vm._sfx_revolver_dry_fire,
		vm._sfx_shotgun_fire,
		vm._sfx_shotgun_break,
		vm._sfx_shotgun_close,
		vm._sfx_stakedriver_fire,
	]
	for rnd: AudioStreamRandomizer in randomizers:
		if rnd == null or rnd.streams_count < 1:
			push_error("[VerifyWeapons] FAIL: Missing AudioStreamRandomizer wrapper on FPSViewmodelController")
			quit(1)
			return
		if absf(rnd.random_pitch - 1.04) > 0.001 or absf(rnd.random_volume_offset_db - 1.0) > 0.001:
			push_error("[VerifyWeapons] FAIL: AudioStreamRandomizer pitch/volume mismatch (pitch=%.3f, vol_db=%.2f)" % [rnd.random_pitch, rnd.random_volume_offset_db])
			quit(1)
			return
		vm._play_weapon_sfx(rnd)

	# Verify -9.0 dB Dynamic Ambient Sidechain Ducking on gunfire and smooth 0.45s recovery
	vm._trigger_gunfire_ambient_duck()
	if absf(vm._ambient_duck_offset_db - (-9.0)) > 0.01 or absf(vm._ambient_duck_timer - 0.45) > 0.01:
		push_error("[VerifyWeapons] FAIL: Gunfire ambient sidechain ducking did not set -9.0 dB / 0.45s")
		quit(1)
		return
	vm._update_ambient_ducking(0.45)
	if absf(vm._ambient_duck_offset_db) > 0.01:
		push_error("[VerifyWeapons] FAIL: Gunfire ambient sidechain ducking did not restore to 0.0 dB after 0.45s")
		quit(1)
		return
	print("[VerifyWeapons] PASS 5: All 8 Visceral Stereo (nchannels=2) weapon .wav files verified in AudioStreamRandomizer (pitch=1.04, vol=1.0dB) with -9.0dB / 0.45s ambient ducking")

	print("[VerifyWeapons] ALL 3-WEAPON ARSENAL CHECKS PASSED!")
	root.remove_child(level)
	level.free()
	quit(0)
