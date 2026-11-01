extends SceneTree

var _level_inst: Node3D = null
var _frames_waited: int = 0


func _init() -> void:
	var level_scene: PackedScene = load("res://scenes/levels/town_overworld.tscn") as PackedScene
	if level_scene == null:
		push_error("[WatertightAudit] Failed to load res://scenes/levels/town_overworld.tscn")
		quit(1)
		return

	_level_inst = level_scene.instantiate() as Node3D
	root.add_child(_level_inst)


func _physics_process(_delta: float) -> bool:
	_frames_waited += 1
	if _frames_waited < 5:
		return false

	_run_watertight_audit()
	return true


func _build_26_directions() -> Array[Vector3]:
	var dirs: Array[Vector3] = []
	for dx: int in [-1, 0, 1]:
		for dy: int in [-1, 0, 1]:
			for dz: int in [-1, 0, 1]:
				if dx == 0 and dy == 0 and dz == 0:
					continue
				var v: Vector3 = Vector3(float(dx), float(dy), float(dz)).normalized()
				dirs.append(v)
	return dirs


func _collect_rids_under(node: Node, out_rids: Array[RID]) -> void:
	if node is CollisionObject3D:
		var col_obj: CollisionObject3D = node as CollisionObject3D
		out_rids.append(col_obj.get_rid())
	for child: Node in node.get_children():
		_collect_rids_under(child, out_rids)


func _get_collider_path(collider: Object) -> String:
	if collider is Node:
		var n: Node = collider as Node
		return str(_level_inst.get_path_to(n))
	return str(collider)


func _run_watertight_audit() -> void:
	var space_state: PhysicsDirectSpaceState3D = root.world_3d.direct_space_state
	var dirs: Array[Vector3] = _build_26_directions()

	var base_exclude: Array[RID] = []
	var player_node: Node = _level_inst.get_node_or_null("Player")
	if player_node != null:
		_collect_rids_under(player_node, base_exclude)

	var hull_exclude: Array[RID] = base_exclude.duplicate()
	var hull_node: Node = _level_inst.get_node_or_null("WorldGeometry/CryptBasement/CryptShellSealer/CryptExteriorContainmentHull")
	if hull_node != null:
		_collect_rids_under(hull_node, hull_exclude)

	# Define comprehensive test probes across all 8 chambers, all corridors, and all staircases.
	# Each entry: { "name": String, "base_pos": Vector3, "heights": Array[float] }
	var probes: Array[Dictionary] = [
		# Chamber 1: Antechamber of Bones (Y = 0.0m, X in [-4, 4], Z in [-24, -32])
		{"name": "Chamber1_Center", "base_pos": Vector3(0.0, 0.0, -28.0)},
		{"name": "Chamber1_NW", "base_pos": Vector3(-3.0, 0.0, -31.0)},
		{"name": "Chamber1_NE", "base_pos": Vector3(3.0, 0.0, -31.0)},
		{"name": "Chamber1_SW", "base_pos": Vector3(-3.0, 0.0, -25.0)},
		{"name": "Chamber1_SE", "base_pos": Vector3(3.0, 0.0, -25.0)},

		# Corridor Ch1 -> Ch2 (West, Y = 0.0m)
		{"name": "Corridor_Ch1_To_Ch2", "base_pos": Vector3(-8.0, 0.0, -28.0)},

		# Chamber 2: Hall of Sarcophagi (Y = 0.0m, X in [-12, -24], Z in [-24, -36])
		{"name": "Chamber2_Center", "base_pos": Vector3(-18.0, 0.0, -30.0)},
		{"name": "Chamber2_NorthWest", "base_pos": Vector3(-23.0, 0.0, -35.0)},
		{"name": "Chamber2_SouthEast", "base_pos": Vector3(-13.0, 0.0, -25.0)},

		# Corridor Ch2 -> Ch3 (North-West, Y = 0.0m)
		{"name": "Corridor_Ch2_To_Ch3", "base_pos": Vector3(-16.0, 0.0, -40.0)},

		# Chamber 3: Whispering Reliquary & Library (Y = 0.0m, X in [-12, -20], Z in [-44, -56])
		{"name": "Chamber3_Center", "base_pos": Vector3(-16.0, 0.0, -50.0)},
		{"name": "Chamber3_NorthLectern", "base_pos": Vector3(-16.0, 0.0, -55.0)},
		{"name": "Chamber3_SouthEntry", "base_pos": Vector3(-16.0, 0.0, -45.0)},

		# Corridor Ch1 -> Ch4 (East, Y = 0.0m)
		{"name": "Corridor_Ch1_To_Ch4", "base_pos": Vector3(8.0, 0.0, -28.0)},

		# Chamber 4: Inquisitor's Gaol (Y = 0.0m, X in [12, 24], Z in [-24, -32])
		{"name": "Chamber4_CenterAisle", "base_pos": Vector3(18.0, 0.0, -28.0)},
		{"name": "Chamber4_NorthCell", "base_pos": Vector3(16.0, 0.0, -32.0)},
		{"name": "Chamber4_SouthCell", "base_pos": Vector3(16.0, 0.0, -24.0)},
		{"name": "Chamber4_EastEnd", "base_pos": Vector3(24.0, 0.0, -28.0)},

		# Staircase Ch4 -> Ch5 (midpoint X = 24.0, Z = -36.0, descending Y = 0.0 -> -4.0, midpoint Y = -2.0)
		{"name": "Stairs_Ch4_To_Ch5_LowerRef", "base_pos": Vector3(24.0, -4.0, -36.0)},
		{"name": "Stairs_Ch4_To_Ch5_MidSlope", "base_pos": Vector3(24.0, -2.0, -36.0)},
		{"name": "Corridor_Ch4_To_Ch5_Landing", "base_pos": Vector3(24.0, -4.0, -40.0)},

		# Chamber 5: Alchemical Plague Cistern (Y = -4.0m, X in [10, 26], Z in [-38, -54])
		{"name": "Chamber5_Center", "base_pos": Vector3(18.0, -4.0, -46.0)},
		{"name": "Chamber5_NW", "base_pos": Vector3(13.0, -4.0, -52.0)},
		{"name": "Chamber5_SE", "base_pos": Vector3(23.0, -4.0, -41.0)},

		# Staircase Ch1 -> Ch6 (midpoint X = 0.0, Z = -36.0, descending Y = 0.0 -> -4.0, midpoint Y = -2.0)
		{"name": "Stairs_Ch1_To_Ch6_LowerRef", "base_pos": Vector3(0.0, -4.0, -36.0)},
		{"name": "Stairs_Ch1_To_Ch6_MidSlope", "base_pos": Vector3(0.0, -2.0, -36.0)},
		{"name": "Corridor_Ch1_To_Ch6_Landing", "base_pos": Vector3(0.0, -4.0, -40.0)},

		# Chamber 6: Drowned Ossuary & Weeping Saint (Y = -4.0m, X in [-4, 4], Z in [-44, -52])
		{"name": "Chamber6_Center", "base_pos": Vector3(0.0, -4.0, -48.0)},
		{"name": "Chamber6_West", "base_pos": Vector3(-3.5, -4.0, -48.0)},
		{"name": "Chamber6_East", "base_pos": Vector3(3.5, -4.0, -48.0)},

		# West Gallery Corridor & Staircase Ch6 -> Ch7 (Y = -4.0m -> -8.0m)
		{"name": "Corridor_Ch6_To_Ch7_Gallery1", "base_pos": Vector3(-8.0, -4.0, -52.0)},
		{"name": "Corridor_Ch6_To_Ch7_Gallery2", "base_pos": Vector3(-8.0, -4.0, -56.0)},
		{"name": "Corridor_Ch6_To_Ch7_Turn", "base_pos": Vector3(-12.0, -4.0, -56.0)},
		{"name": "Stairs_Ch6_To_Ch7_LowerRef", "base_pos": Vector3(-12.0, -8.0, -60.0)},
		{"name": "Stairs_Ch6_To_Ch7_MidSlope", "base_pos": Vector3(-12.0, -6.0, -60.0)},

		# Chamber 7: Sunken Bell Pit (Y = -8.0m, X in [-20, -12], Z in [-64, -72])
		{"name": "Chamber7_Center", "base_pos": Vector3(-16.0, -8.0, -68.0)},
		{"name": "Chamber7_NW", "base_pos": Vector3(-19.5, -8.0, -71.5)},
		{"name": "Chamber7_SE", "base_pos": Vector3(-12.5, -8.0, -64.5)},

		# Staircase & Corridor Ch6 -> Ch8 (midpoint X = 0.0, Z = -56.0, descending Y = -4.0 -> -8.0, midpoint Y = -6.0)
		{"name": "Stairs_Ch6_To_Ch8_LowerRef", "base_pos": Vector3(0.0, -8.0, -56.0)},
		{"name": "Stairs_Ch6_To_Ch8_MidSlope", "base_pos": Vector3(0.0, -6.0, -56.0)},
		{"name": "Corridor_Ch6_To_Ch8_Landing", "base_pos": Vector3(0.0, -8.0, -60.0)},

		# Chamber 8: Abyssal Sanctum of the Obelisk (Y = -8.0m, X in [-8, 8], Z in [-64, -80])
		{"name": "Chamber8_Center", "base_pos": Vector3(0.0, -8.0, -72.0)},
		{"name": "Chamber8_NW", "base_pos": Vector3(-7.0, -8.0, -79.0)},
		{"name": "Chamber8_NE", "base_pos": Vector3(7.0, -8.0, -79.0)},
		{"name": "Chamber8_SW", "base_pos": Vector3(-7.0, -8.0, -65.0)},
		{"name": "Chamber8_SE", "base_pos": Vector3(7.0, -8.0, -65.0)},

		# Church Nave Stairwell to Crypt (midpoint X = 0.0, Z in [-23.5, -22.5], subterranean collar Y < 4.0m)
		{"name": "Stairs_Church_To_Crypt_LowerRef", "base_pos": Vector3(0.0, 0.0, -22.5)},
		{"name": "Stairs_Church_To_Crypt_LandingRef", "base_pos": Vector3(0.0, 0.2, -23.5)},
	]

	var heights: Array[float] = [1.7, 3.5]
	var total_rays: int = 0
	var escaped_rays_no_hull: int = 0
	var terrain_hits_no_hull: int = 0
	var escaped_rays_with_hull: int = 0
	var terrain_hits_with_hull: int = 0

	for probe: Dictionary in probes:
		var probe_name: String = probe["name"] as String
		var base_pos: Vector3 = probe["base_pos"] as Vector3
		for h: float in heights:
			var origin: Vector3 = base_pos + Vector3(0.0, h, 0.0)
			for dir: Vector3 in dirs:
				total_rays += 1
				var target: Vector3 = origin + dir * 60.0

				# 1. Query WITHOUT containment hull (pure 3D Grid Sealer test)
				var q_pure: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(origin, target)
				q_pure.exclude = hull_exclude
				q_pure.hit_back_faces = true
				var hit_pure: Dictionary = space_state.intersect_ray(q_pure)
				if hit_pure.is_empty():
					escaped_rays_no_hull += 1
					print(
						"[LEAK-PURE] %s (h=+%.1fm) origin=%s dir=%s ESCAPED TO SKY!"
						% [probe_name, h, str(origin), str(dir)]
					)
				else:
					var col_Obj: Object = hit_pure["collider"] as Object
					var col_path: String = _get_collider_path(col_Obj)
					if col_path.contains("TerrainTown"):
						terrain_hits_no_hull += 1
						print(
							"[TERRAIN-LEAK-PURE] %s (h=+%.1fm) origin=%s dir=%s hit %s at %s"
							% [probe_name, h, str(origin), str(dir), col_path, str(hit_pure["position"])]
						)

				# 2. Query WITH containment hull (full runtime level test)
				var q_full: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(origin, target)
				q_full.exclude = base_exclude
				q_full.hit_back_faces = true
				var hit_full: Dictionary = space_state.intersect_ray(q_full)
				if hit_full.is_empty():
					escaped_rays_with_hull += 1
					print(
						"[LEAK-FULL] %s (h=+%.1fm) origin=%s dir=%s ESCAPED TO SKY!"
						% [probe_name, h, str(origin), str(dir)]
					)
				else:
					var col_obj_full: Object = hit_full["collider"] as Object
					var col_path_full: String = _get_collider_path(col_obj_full)
					if col_path_full.contains("TerrainTown"):
						terrain_hits_with_hull += 1
						print(
							"[TERRAIN-LEAK-FULL] %s (h=+%.1fm) origin=%s dir=%s hit %s at %s"
							% [probe_name, h, str(origin), str(dir), col_path_full, str(hit_full["position"])]
						)

	print("==================================================================")
	print("[WatertightAudit] Total probes: %d (x2 heights = %d origins, x26 dirs = %d rays)" % [probes.size(), probes.size() * 2, total_rays])
	print("[WatertightAudit] Pure 3D Grid Shell (Hull Excluded): escaped=%d, terrain_hits=%d" % [escaped_rays_no_hull, terrain_hits_no_hull])
	print("[WatertightAudit] Full Crypt + Containment Hull:      escaped=%d, terrain_hits=%d" % [escaped_rays_with_hull, terrain_hits_with_hull])
	print("==================================================================")

	if escaped_rays_no_hull > 0 or terrain_hits_no_hull > 0 or escaped_rays_with_hull > 0 or terrain_hits_with_hull > 0:
		push_error("[WatertightAudit] FAILED: Detected leaks in underground crypt!")
		_level_inst.free()
		quit(1)
		return

	print("[WatertightAudit] PASSED 100%%: All %d spherical raycasts hit solid interior StaticBody3D surfaces!" % total_rays)
	_level_inst.free()
	quit(0)
