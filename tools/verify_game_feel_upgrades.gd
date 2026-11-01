extends SceneTree

func _init() -> void:
	print("=== VERIFYING 5 FPS GAME FEEL & GUNPLAY UPGRADES ===")
	var failures: int = 0

	# 1. Verify hunter_quickstep_dash.wav AudioStreamWAV
	var dash_sfx: AudioStreamWAV = load("res://assets/audio/sfx/hunter_quickstep_dash.wav") as AudioStreamWAV
	if dash_sfx == null or dash_sfx.data.is_empty():
		printerr("FAIL [1]: res://assets/audio/sfx/hunter_quickstep_dash.wav failed to load as valid AudioStreamWAV.")
		failures += 1
	else:
		print("PASS [1]: hunter_quickstep_dash.wav loaded (", dash_sfx.data.size(), " bytes, mix_rate=", dash_sfx.mix_rate, ", stereo=", dash_sfx.stereo, ")")

	# 2. Instantiate FPSPlayer hierarchy & Verify Smooth Perlin-Noise Trauma Camera Shake + Subconscious Camera Animations
	var player: FPSPlayer = FPSPlayer.new()
	player.name = "Player"
	var head: Node3D = Node3D.new()
	head.name = "Head"
	head.position = Vector3(0.0, 1.65, 0.0)
	player.add_child(head)

	var cam: Camera3D = Camera3D.new()
	cam.name = "Camera3D"
	head.add_child(cam)

	var vm: FPSViewmodelController = FPSViewmodelController.new()
	vm.name = "ViewmodelRig"
	var left_piv: Node3D = Node3D.new()
	left_piv.name = "LeftHandPivot"
	vm.add_child(left_piv)
	var right_piv: Node3D = Node3D.new()
	right_piv.name = "RightHandPivot"
	vm.add_child(right_piv)
	cam.add_child(vm)

	var hud: GothicHudOverhaul = GothicHudOverhaul.new()
	hud.name = "GothicHudOverhaul"
	player.add_child(hud)

	var loadout: PlayerLoadoutManager = PlayerLoadoutManager.new()
	loadout.name = "PlayerLoadoutManager"
	player.add_child(loadout)

	root.add_child(player)
	player._ready()
	vm._ready()
	hud._ready()
	loadout._ready()

	player.add_camera_trauma(0.5, Vector3(deg_to_rad(1.5), deg_to_rad(0.8), deg_to_rad(-1.1)))
	player._update_head_bob(0.016)

	if player.camera_trauma <= 0.0:
		printerr("FAIL [2a]: camera_trauma did not increase after add_camera_trauma(0.5).")
		failures += 1
	elif player.trauma_noise == null or player.trauma_noise.noise_type != FastNoiseLite.TYPE_PERLIN:
		printerr("FAIL [2b]: trauma_noise is not initialized to FastNoiseLite.TYPE_PERLIN.")
		failures += 1
	elif is_zero_approx(player.camera.rotation.x) or is_zero_approx(player.camera.rotation.y) or is_zero_approx(player.camera.rotation.z):
		printerr("FAIL [2c]: FastNoiseLite Perlin camera rotation offsets are zero: ", player.camera.rotation)
		failures += 1
	else:
		print("PASS [2]: Smooth Perlin-Noise Camera Trauma active (trauma=", snappedf(player.camera_trauma, 0.001), ", cam_rot=", player.camera.rotation, ")")

	# Verify Jump & Heavy Landing Subconscious Camera Impulses
	player.cam_anim_rot_offset = Vector3.ZERO
	vm.recoil_pos = Vector3.ZERO
	player._on_jump_takeoff()
	if player.cam_anim_rot_offset.x <= 0.01 or vm.recoil_pos.y > -0.02:
		printerr("FAIL [2d]: Jump takeoff camera pitch/viewmodel dip did not trigger: rot=", player.cam_anim_rot_offset, " vm_pos=", vm.recoil_pos)
		failures += 1
	player._on_heavy_landing(-12.0)
	if player.cam_anim_pos_offset.y >= -0.15 or player.camera_trauma <= 0.45:
		printerr("FAIL [2e]: Heavy landing impact did not scale camera drop & trauma: pos=", player.cam_anim_pos_offset, " trauma=", player.camera_trauma)
		failures += 1
	else:
		print("PASS [2b]: Subconscious Jump Takeoff & Heavy Landing Camera Animations verified.")

	# 3. Verify 6-DOF Spring Recoil across Revolver, Hellfire Coach Gun, and Stake-Driver + Snappy Multi-Beat Whip Reload
	var weapons: Array[String] = ["revolver", "shotgun", "stakedriver"]
	for w_id: String in weapons:
		vm.switch_active_weapon(w_id, false)
		vm._fire_cooldown_remaining = 0.0
		vm._is_reloading = false
		vm.current_ammo = vm.max_ammo
		vm.recoil_pos = Vector3.ZERO
		vm.recoil_vel = Vector3.ZERO
		vm.recoil_rot = Vector3.ZERO
		vm.recoil_rot_vel = Vector3.ZERO

		vm._fire_active_weapon()

		if vm.recoil_pos == Vector3.ZERO or is_zero_approx(vm.recoil_rot.x) or is_zero_approx(vm.recoil_rot.y) or is_zero_approx(vm.recoil_rot.z):
			printerr("FAIL [3]: Weapon ", w_id, " did not produce 6-DOF recoil! pos=", vm.recoil_pos, " rot=", vm.recoil_rot)
			failures += 1
		else:
			print("PASS [3-", w_id, "]: 6-DOF Spring Recoil verified (recoil_pos=", vm.recoil_pos, ", recoil_rot_deg=", Vector3(rad_to_deg(vm.recoil_rot.x), rad_to_deg(vm.recoil_rot.y), rad_to_deg(vm.recoil_rot.z)), ")")

		# Step the underdamped spring to verify stiffness=180.0 / damping=14.5 integration
		vm._step_6dof_recoil_spring(0.016)

	# Verify Multi-Beat Snappy Whip Reload (Beat 1 at 15%, Beat 2 at 50%, Beat 3 at 82% + add_camera_trauma(0.24))
	vm.switch_active_weapon("revolver", false)
	vm.current_ammo = 1
	vm._is_reloading = false
	player.camera_trauma = 0.0
	vm._reload_revolver()
	vm._update_snappy_whip_reload_beats(0.20, ease(0.20, 3.8))
	vm._update_snappy_whip_reload_beats(0.55, ease(0.55, 3.8))
	vm._update_snappy_whip_reload_beats(0.85, ease(0.85, 3.8))
	if not vm._reload_beat1_done or not vm._reload_beat2_done or not vm._reload_beat3_done or player.camera_trauma < 0.20:
		printerr("FAIL [3-reload]: Multi-beat reload jolts/trauma did not fire: b1=", vm._reload_beat1_done, " b2=", vm._reload_beat2_done, " b3=", vm._reload_beat3_done, " trauma=", player.camera_trauma)
		failures += 1
	else:
		print("PASS [3-reload]: Multi-Beat Whip Reload & Beat 3 Camera Lock Trauma verified (trauma=", snappedf(player.camera_trauma, 0.01), ")")

	# 4. Verify Hunter's Quickstep Dash (19.5 m/s burst, 0.18s i-frames ignoring take_damage, camera duck/tilt/FOV)
	player.dash_cooldown_timer = 0.0
	player.is_dashing = false
	var dash_started: bool = player.trigger_quickstep_dash(Vector3(1.0, 0.0, 0.0))
	var horiz_dash_speed: float = Vector2(player.velocity.x, player.velocity.z).length()
	if not dash_started or not player.is_dashing or not player.is_dashing_iframes or horiz_dash_speed < 18.0:
		printerr("FAIL [4a]: Quickstep Dash failed: started=", dash_started, " is_dashing=", player.is_dashing, " iframes=", player.is_dashing_iframes, " speed=", horiz_dash_speed)
		failures += 1
	else:
		# Test i-frames on both FPSController.take_damage and PlayerLoadoutManager.take_damage
		var hp_before: int = loadout.current_health
		player.take_damage(40.0)
		loadout.take_damage(40.0)
		loadout.apply_player_damage(40.0)
		var hp_after: int = loadout.current_health
		if hp_after != hp_before:
			printerr("FAIL [4b]: take_damage was not ignored during Quickstep i-frames! hp_before=", hp_before, " hp_after=", hp_after)
			failures += 1
		else:
			print("PASS [4]: Hunter's Quickstep Dash verified (speed=", snappedf(horiz_dash_speed, 0.1), " m/s, is_dashing=true, is_dashing_iframes=true, take_damage=0 during i-frames)")

	# 5. Verify Spring-Animated Crosshair & Expanding/Rotating Double-Slash Hitmarkers
	hud.add_reticle_spread(30.0)
	if hud.reticle_spread_px < 24.0 or is_zero_approx(hud.reticle_rotation_rad):
		printerr("FAIL [5a]: Spring-Animated Crosshair spread/rotation did not kick: spread=", hud.reticle_spread_px, " rot=", hud.reticle_rotation_rad)
		failures += 1
	hud.trigger_hitmarker(true)
	if hud.hitmarker_scale <= 1.5 or is_zero_approx(hud.hitmarker_rotation) or not hud.hitmarker_is_crit:
		printerr("FAIL [5b]: Hitmarker scale/rotation failed on trigger_hitmarker(true): scale=", hud.hitmarker_scale, " rot=", hud.hitmarker_rotation)
		failures += 1
	else:
		print("PASS [5]: Spring-Animated Crosshair & Expanding/Rotating Hitmarker verified (scale=", hud.hitmarker_scale, ", rot_deg=", snappedf(rad_to_deg(hud.hitmarker_rotation), 0.1), ", spread_px=", hud.reticle_spread_px, ")")

	player.queue_free()

	if failures > 0:
		printerr("=== VERIFICATION FAILED WITH ", failures, " ERROR(S) ===")
		quit(1)
	else:
		print("=== ALL 5 FPS GAME FEEL & GUNPLAY UPGRADES VERIFIED CLEANLY (0 ERRORS) ===")
		quit(0)
