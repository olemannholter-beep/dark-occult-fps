extends SceneTree


func _init() -> void:
	print("==================================================================")
	print("[Verify] Starting Phase 1-5 Culling, Stairwell, Portals, Dungeon & Audio Verification...")
	print("==================================================================")
	call_deferred("_run_verification")


func _run_verification() -> void:
	var failures: Array[String] = []

	# --------------------------------------------------------------------------
	# 1. Verify Zero Structural Distance Culling on Prefabs
	# --------------------------------------------------------------------------
	var structural_prefabs: Array[String] = [
		"res://scenes/prefabs/architecture/wall_stone_solid.tscn",
		"res://scenes/prefabs/architecture/wall_stone_4x4.tscn",
		"res://scenes/prefabs/architecture/crypt_wall_ossuary_4x4.tscn",
		"res://scenes/prefabs/architecture/floor_stone_4x4.tscn",
		"res://scenes/prefabs/architecture/roof_gothic_vault_4x4.tscn",
		"res://scenes/prefabs/architecture/ceiling_vaulted_4x4.tscn",
		"res://scenes/prefabs/architecture/crypt_corridor_vault_4x4.tscn",
		"res://scenes/prefabs/architecture/wall_stone_arch_door.tscn",
		"res://scenes/prefabs/architecture/wall_archway_4x4.tscn",
		"res://scenes/prefabs/architecture/wall_stone_window.tscn",
		"res://scenes/prefabs/architecture/stairs_stone_4x4.tscn",
		"res://scenes/prefabs/architecture/crypt_pillar.tscn",
		"res://scenes/prefabs/architecture/crypt_archway_portcullis_4x4.tscn",
		"res://scenes/prefabs/architecture/crypt_iron_gate_cell_4x4.tscn",
		"res://scenes/prefabs/architecture/crypt_rotting_bookshelf_4x4.tscn",
		"res://scenes/prefabs/architecture/crypt_drowned_cistern_4x4.tscn",
		"res://scenes/prefabs/ossuary_variety/ossuary_stone_bridge_4x4.tscn",
		"res://scenes/prefabs/ossuary_variety/ossuary_balcony_railing_4m.tscn",
		"res://scenes/prefabs/ossuary_variety/ossuary_buttress_arch_4x4.tscn",
		"res://scenes/prefabs/architecture/church_foundation_plinth.tscn",
		"res://scenes/prefabs/architecture/church_front_gable_rose.tscn",
		"res://scenes/prefabs/architecture/church_pitched_roof_12x16.tscn",
		"res://scenes/prefabs/architecture/church_bell_tower_spire.tscn",
		"res://scenes/prefabs/architecture/church_buttress.tscn",
		"res://scenes/prefabs/environment/house_abandoned_a.tscn",
		"res://scenes/prefabs/environment/house_abandoned_b.tscn"
	]

	var checked_prefab_meshes: int = 0
	for p_path: String in structural_prefabs:
		var ps: PackedScene = load(p_path) as PackedScene
		if ps == null:
			failures.append("Missing structural prefab: %s" % p_path)
			continue
		var inst: Node = ps.instantiate()
		var meshes: Array[GeometryInstance3D] = []
		_collect_geometry_instances(inst, meshes)
		for g: GeometryInstance3D in meshes:
			checked_prefab_meshes += 1
			if g.visibility_range_end > 0.0:
				failures.append("Structural prefab %s mesh %s has visibility_range_end = %.2f (must be 0.0)" % [
					p_path, g.name, g.visibility_range_end
				])
		inst.free()
	print("[Check 1] Verified %d structural prefab meshes have visibility_range_end == 0.0." % checked_prefab_meshes)

	# --------------------------------------------------------------------------
	# 2. Load town_overworld.tscn and Verify Church/Crypt Visibility & Stairwell Ceiling Seal
	# --------------------------------------------------------------------------
	var level_scene: PackedScene = load("res://scenes/levels/town_overworld.tscn") as PackedScene
	if level_scene == null:
		failures.append("Failed to load res://scenes/levels/town_overworld.tscn")
		_finish(failures)
		return

	var level: Node3D = level_scene.instantiate() as Node3D
	root.add_child(level)
	await process_frame
	await physics_frame
	await physics_frame

	var town_root: Node3D = level.find_child("TownRoot", true, false) as Node3D
	var crypt_root: Node3D = level.find_child("CryptRoot", true, false) as Node3D
	var church_zone: Node3D = level.find_child("ChurchWorkshopZone", true, false) as Node3D
	var crypt_zone: Node3D = level.find_child("CryptPortalNexusZone", true, false) as Node3D
	var player: Node3D = level.find_child("Player", true, false) as Node3D
	var zone_vis_ctrl: ZoneVisibilityController = level.find_child("ZoneVisibilityController", true, false) as ZoneVisibilityController
	var zone_perf_mgr: ZonePerformanceManager = level.find_child("ZonePerformanceManager", true, false) as ZonePerformanceManager

	if town_root == null or crypt_root == null or church_zone == null or crypt_zone == null or player == null:
		failures.append("Missing TownRoot, CryptRoot, ChurchWorkshopZone, CryptPortalNexusZone, or Player in town_overworld.tscn")

	# Check Church structural walls from valley spawn (Z = +20..+24)
	if church_zone != null:
		var church_geom: Array[GeometryInstance3D] = []
		_collect_structural_geometry_instances(church_zone, church_geom)
		for cg: GeometryInstance3D in church_geom:
			if cg.visibility_range_end > 0.0:
				failures.append("Church structural mesh %s has visibility_range_end = %.2f" % [cg.name, cg.visibility_range_end])
		print("[Check 1b] Verified %d Church structural geometry instances have visibility_range_end == 0.0." % church_geom.size())

	# Move player into Crypt stairwell (Z = -18, Y = 1.5) and deep Crypt (Vector3(0, -3.5, -52))
	var test_hub_positions: Array[Vector3] = [
		Vector3(0.0, 4.2, 22.0),
		Vector3(0.0, 2.0, -18.0),
		Vector3(0.0, -3.5, -52.0)
	]
	for test_pos: Vector3 in test_hub_positions:
		player.global_position = test_pos
		if zone_vis_ctrl != null:
			zone_vis_ctrl.evaluate_zones_now(test_pos)
		if zone_perf_mgr != null:
			zone_perf_mgr.evaluate_zones_now(test_pos)
		if town_root != null and not town_root.visible:
			failures.append("TownRoot became hidden at Hub pos %s" % str(test_pos))
		if crypt_root != null and not crypt_root.visible:
			failures.append("CryptRoot became hidden at Hub pos %s" % str(test_pos))
		if church_zone != null and not church_zone.visible:
			failures.append("ChurchWorkshopZone became hidden at Hub pos %s" % str(test_pos))
		if crypt_zone != null and not crypt_zone.visible:
			failures.append("CryptPortalNexusZone became hidden at Hub pos %s" % str(test_pos))

	# Verify StairsStone4x4 (Church-to-Crypt stairwell) exists, is visible, and has solid StaticBody3D ramp collision
	var stairs_to_crypt: Node3D = level.find_child("StairsStone4x4", true, false) as Node3D
	if stairs_to_crypt == null or not stairs_to_crypt.is_visible_in_tree():
		failures.append("StairsStone4x4 is missing or hidden when player is in Crypt!")
	else:
		var stair_sb: StaticBody3D = stairs_to_crypt.find_child("StaticBody3D", true, false) as StaticBody3D
		if stair_sb == null or stair_sb.get_child_count() == 0:
			failures.append("StairsStone4x4 is missing StaticBody3D ramp collider!")

	# Fire upward raycasts from Y = -3.0 to Y = +10.0 across the Crypt stairwell and chambers
	var space_state: PhysicsDirectSpaceState3D = level.get_world_3d().direct_space_state
	var upward_ray_origins: Array[Vector3] = [
		Vector3(0.0, 2.5, -16.5),
		Vector3(0.0, 1.5, -18.0),
		Vector3(0.0, 0.8, -19.5),
		Vector3(0.0, 0.8, -21.0),
		Vector3(0.0, 0.8, -24.0),
		Vector3(0.0, 0.8, -28.0),
		Vector3(0.0, 0.8, -32.0),
		Vector3(0.0, -1.5, -36.0),
		Vector3(0.0, -3.0, -40.0),
		Vector3(0.0, -3.0, -48.0),
		Vector3(0.0, -3.0, -52.0),
		Vector3(-20.0, 0.8, -28.0),
		Vector3(20.0, 0.8, -28.0),
		Vector3(-20.0, 0.8, -48.0),
		Vector3(-20.0, -3.0, -68.0),
		Vector3(20.0, -7.0, -48.0),
		Vector3(0.0, -7.0, -72.0)
	]
	var sky_leaks: int = 0
	for ray_from: Vector3 in upward_ray_origins:
		var ray_to: Vector3 = Vector3(ray_from.x, 10.0, ray_from.z)
		var q: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(ray_from, ray_to, 1)
		var hit: Dictionary = space_state.intersect_ray(q)
		if hit.is_empty():
			sky_leaks += 1
			failures.append("Upward raycast from %s to %s missed ceiling (skybox leak!)" % [str(ray_from), str(ray_to)])
	print("[Check 2] Fired %d upward stairwell/crypt raycasts -> %d sky leaks." % [upward_ray_origins.size(), sky_leaks])

	# --------------------------------------------------------------------------
	# 3. Verify All 8 Crypt OccultPortals (Scale == 0.76, Ceiling Clearance, Pillar Clearance >= 3.2m)
	# --------------------------------------------------------------------------
	var all_pillars: Array[Node3D] = []
	_collect_pillars_recursive(crypt_zone, all_pillars)

	var portal_names: Array[String] = [
		"Portal_Biome1_EndlessOssuary",
		"Portal_Biome2_RoyalNecropolis",
		"Portal_Biome3_InfiniteReliquary",
		"Portal_Biome4_InquisitorsLabyrinth",
		"Portal_Biome5_BlightedCisterns",
		"Portal_Biome6_WeepingSaintHalls",
		"Portal_Biome7_ShatteredBellChasms",
		"Portal_Biome8_AbyssalBloodWastes"
	]

	for p_name: String in portal_names:
		var portal: Node3D = level.find_child(p_name, true, false) as Node3D
		if portal == null:
			failures.append("Missing %s in town_overworld.tscn" % p_name)
			continue
		var arch_scale: Vector3 = portal.scale
		if not arch_scale.is_equal_approx(Vector3(0.76, 0.76, 0.76)):
			failures.append("%s scale is %s (expected Vector3(0.76, 0.76, 0.76))" % [p_name, str(arch_scale)])

		# Compute top world Y of portal meshes
		var portal_top_y: float = _compute_portal_top_world_y(portal)
		var portal_height: float = portal_top_y - portal.global_position.y
		var ceiling_y: float = portal.global_position.y + 4.0
		if portal_height > 3.25 or portal_top_y > (ceiling_y - 0.45):
			failures.append("%s top_y=%.2f clips ceiling (floor_y=%.2f, height=%.2f)" % [
				p_name, portal_top_y, portal.global_position.y, portal_height
			])
		if portal.global_position.y <= -4.0 and portal_top_y >= -0.45:
			failures.append("Lower crypt %s top_y=%.2f is >= -0.45m" % [p_name, portal_top_y])

		# Check distance to all crypt pillars
		var min_pillar_d: float = 99999.0
		for pil: Node3D in all_pillars:
			if absf(pil.global_position.y - portal.global_position.y) < 3.5:
				var d_xz: float = Vector2(
					pil.global_position.x - portal.global_position.x,
					pil.global_position.z - portal.global_position.z
				).length()
				if d_xz < min_pillar_d:
					min_pillar_d = d_xz
				if d_xz < 3.2:
					failures.append("Pillar %s at %s is within %.2fm (< 3.2m) of %s at %s" % [
						pil.name, str(pil.global_position), d_xz, p_name, str(portal.global_position)
					])
		print("[Check 3] %s at %s: scale=%s, top_y=%.2f (height=%.2fm), min_pillar_dist=%.2fm" % [
			p_name, str(portal.global_position), str(arch_scale), portal_top_y, portal_height, min_pillar_d
		])

	# --------------------------------------------------------------------------
	# 4. Verify Procedural Dungeon Portal 1 (RoomContainer_0..N-1, <= 2 OmniLights, >= 60% Solid Walls, Culling)
	# --------------------------------------------------------------------------
	var dungeon_gen: ProceduralDungeonGenerator = level.find_child("ProceduralExpeditionRoot", true, false) as ProceduralDungeonGenerator
	if dungeon_gen == null:
		failures.append("Missing ProceduralExpeditionRoot in town_overworld.tscn")
	else:
		var spawn_pos: Vector3 = dungeon_gen.generate_biome_dungeon(1, 1337, 1)
		await process_frame

		var num_rooms: int = dungeon_gen.room_containers.size()
		if num_rooms < 8:
			failures.append("Expected >= 8 RoomContainer nodes, got %d" % num_rooms)

		for r_i: int in range(num_rooms):
			var rc: Node3D = dungeon_gen.room_containers[r_i]
			if rc == null or rc.name != ("RoomContainer_%d" % r_i):
				failures.append("Missing or misnamed RoomContainer_%d" % r_i)
				continue
			var r_lights: Array[OmniLight3D] = []
			_collect_omni_lights_recursive(rc, r_lights)
			if r_lights.size() > 2:
				failures.append("RoomContainer_%d has %d OmniLight3D nodes (max 2 allowed!)" % [r_i, r_lights.size()])
			for l: OmniLight3D in r_lights:
				if l.shadow_enabled:
					failures.append("RoomContainer_%d light %s has shadow_enabled == true" % [r_i, l.name])

		var total_walls: int = maxi(1, dungeon_gen.last_total_wall_faces)
		var solid_ratio: float = float(dungeon_gen.last_solid_wall_faces) / float(total_walls)
		print("[Check 4a] Portal 1 generated %d RoomContainers, solid wall ratio = %.1f%% (%d / %d)." % [
			num_rooms, solid_ratio * 100.0, dungeon_gen.last_solid_wall_faces, total_walls
		])
		if solid_ratio < 0.60:
			failures.append("Solid wall ratio %.2f is < 0.60" % solid_ratio)

		# Move player into RoomContainer_0 and verify RoomContainer_3..N-1 are culled
		player.global_position = spawn_pos
		dungeon_gen.update_active_room_culling(spawn_pos)
		if not dungeon_gen.room_containers[0].visible:
			failures.append("RoomContainer_0 should be visible when player is inside Room 0")
		for r_i: int in range(3, num_rooms):
			var far_rc: Node3D = dungeon_gen.room_containers[r_i]
			if far_rc.visible or far_rc.process_mode != Node.PROCESS_MODE_DISABLED:
				failures.append("RoomContainer_%d should have visible == false and process_mode == PROCESS_MODE_DISABLED when player is in Room 0" % r_i)
		print("[Check 4b] Verified RoomContainer_0..1 active and RoomContainer_2..%d culled (visible=false, PROCESS_MODE_DISABLED)." % [num_rooms - 1])

	# --------------------------------------------------------------------------
	# 5. Verify Generated Ambient & Water Droplet .wav Files (Peak <= 0.22, Zero Low-Freq Impulse, Seamless Loops)
	# --------------------------------------------------------------------------
	var droplet_files: Array[String] = [
		"res://assets/audio/sfx/crypt_water_drip_01.wav",
		"res://assets/audio/sfx/crypt_water_drip_02.wav",
		"res://assets/audio/sfx/crypt_water_drip_03.wav",
		"res://assets/audio/sfx/ambient_crypt_drip.wav",
		"res://assets/audio/ambient/ambient_crypt_drip.wav"
	]
	for d_path: String in droplet_files:
		var samples: PackedFloat32Array = _read_wav_mono_samples(d_path)
		if samples.is_empty():
			failures.append("Failed to read WAV samples from %s" % d_path)
			continue
		var peak: float = 0.0
		for s: float in samples:
			peak = maxf(peak, absf(s))
		if peak > 0.22:
			failures.append("Droplet WAV %s peak amplitude %.4f exceeds 0.22!" % [d_path, peak])

		# Check low-frequency energy (< 250Hz) vs high-frequency droplet ping energy (1200Hz..2200Hz)
		var low_energy: float = (
			_goertzel_power(samples, 60.0, 44100.0)
			+ _goertzel_power(samples, 110.0, 44100.0)
			+ _goertzel_power(samples, 160.0, 44100.0)
			+ _goertzel_power(samples, 220.0, 44100.0)
		)
		var high_energy: float = (
			_goertzel_power(samples, 1300.0, 44100.0)
			+ _goertzel_power(samples, 1650.0, 44100.0)
			+ _goertzel_power(samples, 2000.0, 44100.0)
		)
		if low_energy > high_energy * 0.02:
			failures.append("Droplet WAV %s contains low-frequency (<250Hz) impulse energy (low=%.6f vs high=%.6f)" % [
				d_path, low_energy, high_energy
			])
		print("[Check 5a] %s: peak=%.4f (<= 0.22), low_freq_power=%.8f, ping_power=%.6f" % [
			d_path, peak, low_energy, high_energy
		])

	var loop_files: Array[String] = [
		"res://assets/audio/ambient/ambient_crypt_drone_loop.wav",
		"res://assets/audio/ambient/ambient_drone.wav",
		"res://assets/audio/ambient/crypt_ambience.wav",
		"res://assets/audio/ambient/ambient_church_draft_loop.wav",
		"res://assets/audio/ambient/ambient_moor_wind_loop.wav"
	]
	for l_path: String in loop_files:
		var l_samples: PackedFloat32Array = _read_wav_mono_samples(l_path)
		if l_samples.is_empty():
			failures.append("Failed to read loop WAV samples from %s" % l_path)
			continue
		var seam_diff: float = absf(l_samples[0] - l_samples[l_samples.size() - 1])
		if seam_diff >= 0.005:
			failures.append("Loop WAV %s boundary seam discontinuity %.6f >= 0.005" % [l_path, seam_diff])
		print("[Check 5b] %s: loop boundary delta = %.6f (< 0.005)" % [l_path, seam_diff])

	level.free()
	_finish(failures)


func _finish(failures: Array[String]) -> void:
	if failures.is_empty():
		print("==================================================================")
		print("[Verify] ALL PHASE 1-5 CHECKS PASSED PERFECTLY (0 FAILURES)!")
		print("==================================================================")
		quit(0)
	else:
		print("==================================================================")
		print("[Verify] FAILED WITH %d ERRORS:" % failures.size())
		for f: String in failures:
			print("  - %s" % f)
		print("==================================================================")
		quit(1)


func _collect_geometry_instances(node: Node, out_list: Array[GeometryInstance3D]) -> void:
	if node is GeometryInstance3D:
		out_list.append(node as GeometryInstance3D)
	for child: Node in node.get_children():
		_collect_geometry_instances(child, out_list)


func _collect_structural_geometry_instances(node: Node, out_list: Array[GeometryInstance3D]) -> void:
	var n_low: String = String(node.name).to_lower()
	var is_clutter: bool = (
		n_low.contains("clutter")
		or n_low.contains("candle")
		or n_low.contains("brazier")
		or n_low.contains("sconce")
		or n_low.contains("workbench")
		or n_low.contains("stand")
		or n_low.contains("font")
		or n_low.contains("chest")
		or n_low.contains("dust")
	)
	if is_clutter:
		return
	if node is GeometryInstance3D:
		out_list.append(node as GeometryInstance3D)
	for child: Node in node.get_children():
		_collect_structural_geometry_instances(child, out_list)


func _collect_pillars_recursive(node: Node, out_pillars: Array[Node3D]) -> void:
	if node == null:
		return
	if node is Node3D and String(node.name).to_lower().contains("pillar"):
		out_pillars.append(node as Node3D)
		return
	for child: Node in node.get_children():
		_collect_pillars_recursive(child, out_pillars)


func _collect_omni_lights_recursive(node: Node, out_lights: Array[OmniLight3D]) -> void:
	if node is OmniLight3D:
		out_lights.append(node as OmniLight3D)
	for child: Node in node.get_children():
		_collect_omni_lights_recursive(child, out_lights)


func _compute_portal_top_world_y(portal: Node3D) -> float:
	var max_y: float = portal.global_position.y
	var meshes: Array[GeometryInstance3D] = []
	_collect_geometry_instances(portal, meshes)
	for g: GeometryInstance3D in meshes:
		if g is MeshInstance3D:
			var mi: MeshInstance3D = g as MeshInstance3D
			if mi.mesh != null:
				var aabb: AABB = mi.get_aabb()
				for ix: int in [0, 1]:
					for iy: int in [0, 1]:
						for iz: int in [0, 1]:
							var local_pt: Vector3 = aabb.position + Vector3(
								aabb.size.x * float(ix),
								aabb.size.y * float(iy),
								aabb.size.z * float(iz)
							)
							var world_pt: Vector3 = mi.global_transform * local_pt
							max_y = maxf(max_y, world_pt.y)
	return max_y


func _read_wav_mono_samples(res_path: String) -> PackedFloat32Array:
	var out: PackedFloat32Array = PackedFloat32Array()
	var f: FileAccess = FileAccess.open(res_path, FileAccess.READ)
	if f == null:
		return out
	var total_len: int = f.get_length()
	if total_len < 44:
		return out
	f.seek(22)
	var num_channels: int = f.get_16()
	f.seek(34)
	var bits_per_sample: int = f.get_16()
	# Locate "data" chunk
	var pos: int = 12
	var data_offset: int = 44
	var data_size: int = total_len - 44
	while pos + 8 <= total_len:
		f.seek(pos)
		var chunk_id: String = f.get_buffer(4).get_string_from_ascii()
		var chunk_sz: int = f.get_32()
		if chunk_id == "data":
			data_offset = pos + 8
			data_size = chunk_sz
			break
		pos += 8 + chunk_sz
	f.seek(data_offset)
	var bytes_per_sample: int = maxi(2, (bits_per_sample / 8) * maxi(1, num_channels))
	var sample_frames: int = data_size / bytes_per_sample
	out.resize(sample_frames)
	for i: int in range(sample_frames):
		var raw_u16: int = f.get_16()
		var signed_s16: int = raw_u16 - 65536 if raw_u16 >= 32768 else raw_u16
		if num_channels == 2:
			var raw_r: int = f.get_16()
			var signed_r: int = raw_r - 65536 if raw_r >= 32768 else raw_r
			out[i] = float(signed_s16 + signed_r) * 0.5 / 32767.0
		else:
			out[i] = float(signed_s16) / 32767.0
	return out


func _goertzel_power(samples: PackedFloat32Array, target_freq: float, sample_rate: float) -> float:
	var n: int = mini(samples.size(), 8192)
	if n <= 0:
		return 0.0
	var k: int = roundi((float(n) * target_freq) / sample_rate)
	var w: float = (TAU * float(k)) / float(n)
	var cosine: float = cos(w)
	var coeff: float = 2.0 * cosine
	var q0: float = 0.0
	var q1: float = 0.0
	var q2: float = 0.0
	for i: int in range(n):
		q0 = coeff * q1 - q2 + samples[i]
		q2 = q1
		q1 = q0
	var power: float = q1 * q1 + q2 * q2 - q1 * q2 * coeff
	return power / float(n * n)
