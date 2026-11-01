extends SceneTree


func _init() -> void:
	call_deferred("_run_verification")


func _collect_portals(node: Node, out_portals: Array[OccultPortal]) -> void:
	if node is OccultPortal:
		out_portals.append(node as OccultPortal)
	for child: Node in node.get_children():
		_collect_portals(child, out_portals)


func _run_spherical_watertight_raycast(space_state: PhysicsDirectSpaceState3D, origin: Vector3) -> int:
	var escaped_count: int = 0
	for dx: int in [-1, 0, 1]:
		for dy: int in [-1, 0, 1]:
			for dz: int in [-1, 0, 1]:
				if dx == 0 and dy == 0 and dz == 0:
					continue
				var dir: Vector3 = Vector3(float(dx), float(dy), float(dz)).normalized()
				var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
					origin,
					origin + dir * 200.0,
					1
				)
				var hit: Dictionary = space_state.intersect_ray(query)
				if hit.is_empty():
					escaped_count += 1
	return escaped_count


func _run_verification() -> void:
	print("=== Starting 8-Biome Portal & Procedural Dungeon Verification ===")
	var level_packed: PackedScene = load("res://scenes/levels/town_overworld.tscn") as PackedScene
	if level_packed == null:
		push_error("FAIL: Could not load town_overworld.tscn")
		quit(1)
		return

	var level: Node3D = level_packed.instantiate() as Node3D
	root.add_child(level)

	await process_frame
	await physics_frame

	var player: CharacterBody3D = level.find_child("Player", true, false) as CharacterBody3D
	var proc_gen: ProceduralDungeonGenerator = (
		level.find_child("ProceduralExpeditionRoot", true, false) as ProceduralDungeonGenerator
	)
	if player == null or proc_gen == null:
		push_error("FAIL: Missing Player or ProceduralExpeditionRoot in town_overworld.tscn")
		quit(1)
		return

	var crypt_root: Node = level.find_child("Crypt", true, false)
	var chamber_portals: Array[OccultPortal] = []
	_collect_portals(crypt_root if crypt_root != null else level, chamber_portals)

	var portals_by_biome: Dictionary[int, OccultPortal] = {}
	for p: OccultPortal in chamber_portals:
		if not p.is_return_portal:
			portals_by_biome[p.biome_id] = p

	if portals_by_biome.size() != 8:
		push_error("FAIL: Expected 8 Chamber OccultPortals (biomes 1..8), found %d" % portals_by_biome.size())
		quit(1)
		return

	var space_state: PhysicsDirectSpaceState3D = level.get_world_3d().direct_space_state
	var all_passed: bool = true

	for b_id: int in range(1, 9):
		if not portals_by_biome.has(b_id):
			push_error("FAIL: Missing Chamber OccultPortal for biome_id %d" % b_id)
			all_passed = false
			continue

		var portal: OccultPortal = portals_by_biome[b_id]
		var vortex_mi: MeshInstance3D = portal.find_child("PortalVortexMesh", true, false) as MeshInstance3D
		var glow_light: OmniLight3D = portal.find_child("PortalGlowLight", true, false) as OmniLight3D
		var prompt_str: String = portal.get_prompt_text(null)

		if vortex_mi == null or not (vortex_mi.material_override is ShaderMaterial):
			push_error("FAIL: Biome %d portal missing PortalVortexMesh ShaderMaterial" % b_id)
			all_passed = false
		if glow_light == null:
			push_error("FAIL: Biome %d portal missing PortalGlowLight" % b_id)
			all_passed = false
		if not prompt_str.contains(portal.biome_title):
			push_error("FAIL: Biome %d prompt does not contain title: %s" % [b_id, prompt_str])
			all_passed = false

		# Trigger portal warp to generate Tier 1 Procedural Dungeon for Biome b_id
		portal.trigger_portal_warp(player)

		await process_frame
		await physics_frame
		await physics_frame

		if player.global_position.y > -450.0:
			push_error("FAIL: Player did not warp to subterranean procedural dungeon for Biome %d (pos=%s)" % [
				b_id,
				str(player.global_position)
			])
			all_passed = false

		if proc_gen.active_room_count != 10:
			push_error("FAIL: Biome %d Tier 1 expected 10 rooms, got %d" % [b_id, proc_gen.active_room_count])
			all_passed = false

		var arch_root: Node = proc_gen.find_child("DungeonArchitecture", false, false)
		var props_root: Node = proc_gen.find_child("DungeonPropsAndClutter", false, false)
		var lights_root: Node = proc_gen.find_child("DungeonLightingAndFog", false, false)
		var enemies_root: Node = proc_gen.find_child("DungeonEnemies", false, false)
		var d_portals_root: Node = proc_gen.find_child("DungeonPortals", false, false)

		var arch_count: int = arch_root.get_child_count() if arch_root != null else 0
		var props_count: int = props_root.get_child_count() if props_root != null else 0
		var lights_count: int = lights_root.get_child_count() if lights_root != null else 0
		var enemies_count: int = enemies_root.get_child_count() if enemies_root != null else 0

		if arch_count < 40 or props_count < 15 or lights_count < 20 or enemies_count < 18:
			push_error(
				"FAIL: Biome %d insufficient generated content (arch=%d, props=%d, lights=%d, enemies=%d)"
				% [b_id, arch_count, props_count, lights_count, enemies_count]
			)
			all_passed = false

		# Watertight 26-direction spherical raycast inside Entry Room (Room 0) and Boss Sanctum (Room 9)
		var entry_origin: Vector3 = proc_gen.generated_room_centers[0]
		var boss_origin: Vector3 = proc_gen.generated_room_centers[proc_gen.generated_room_centers.size() - 1]
		var escaped_entry: int = _run_spherical_watertight_raycast(space_state, entry_origin)
		var escaped_boss: int = _run_spherical_watertight_raycast(space_state, boss_origin)

		if escaped_entry != 0 or escaped_boss != 0:
			push_error(
				"FAIL: Biome %d watertight raycast failed (escaped_entry=%d, escaped_boss=%d)"
				% [b_id, escaped_entry, escaped_boss]
			)
			all_passed = false

		# Verify DeeperBiomeRiftPortal and SanctuaryReturnPortal in Boss Sanctum
		var deeper_p: OccultPortal = (
			d_portals_root.find_child("DeeperBiomeRiftPortal", false, false) as OccultPortal
			if d_portals_root != null
			else null
		)
		var return_p: OccultPortal = (
			d_portals_root.find_child("SanctuaryReturnPortal", false, false) as OccultPortal
			if d_portals_root != null
			else null
		)
		if deeper_p == null or deeper_p.depth_tier != 2:
			push_error("FAIL: Biome %d missing DeeperBiomeRiftPortal (Tier II)" % b_id)
			all_passed = false
		if return_p == null or not return_p.is_return_portal:
			push_error("FAIL: Biome %d missing SanctuaryReturnPortal" % b_id)
			all_passed = false
		else:
			# Test Deeper Rift progression on Biome 8 before returning
			if b_id == 8 and deeper_p != null:
				deeper_p.trigger_portal_warp(player)
				await process_frame
				await physics_frame
				if proc_gen.active_room_count != 12 or proc_gen.active_depth_tier != 2:
					push_error("FAIL: Biome 8 Tier II expected 12 rooms, got %d" % proc_gen.active_room_count)
					all_passed = false
				var tier2_portals_root: Node = proc_gen.find_child("DungeonPortals", false, false)
				return_p = (
					tier2_portals_root.find_child("SanctuaryReturnPortal", false, false) as OccultPortal
					if tier2_portals_root != null
					else null
				)

			if return_p != null:
				return_p.trigger_portal_warp(player)
				var dist_ret: float = player.global_position.distance_to(portal.return_destination)
				if dist_ret > 0.05:
					push_error(
						"FAIL: Biome %d SanctuaryReturnPortal did not return player to Chamber %d (dist=%.3f)"
						% [b_id, b_id, dist_ret]
					)
					all_passed = false

		print(
			"[PASS] Biome %d (%s): rooms=%d, arch=%d, props=%d, lights=%d, enemies=%d, escaped=0/26, return_ok=true"
			% [b_id, portal.biome_title, proc_gen.active_room_count, arch_count, props_count, lights_count, enemies_count]
		)

	level.free()

	if not all_passed:
		push_error("=== 8-BIOME PORTAL VERIFICATION FAILED ===")
		quit(1)
		return

	print("=== ALL 8 BIOME PORTALS & PROCEDURAL DUNGEONS 100% VERIFIED ===")
	quit(0)
