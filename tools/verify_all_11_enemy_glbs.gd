extends SceneTree

const ENEMY_MODELS: Array[String] = [
	"enemy_ossuary_skeleton.glb",
	"enemy_plague_acolyte.glb",
	"enemy_iron_penitent.glb",
	"enemy_01_ossuary_executioner.glb",
	"enemy_02_necropolis_praetorian.glb",
	"enemy_03_reliquary_hexweaver.glb",
	"enemy_04_inquisitor_rackmaster.glb",
	"enemy_05_plague_bloater.glb",
	"enemy_06_weeping_banshee.glb",
	"enemy_07_bell_juggernaut.glb",
	"enemy_08_abyssal_archon.glb"
]

const REQUIRED_NODES: Array[String] = [
	"Pelvis",
	"ThighL",
	"ShinL",
	"ThighR",
	"ShinR",
	"Torso",
	"Head",
	"UpperArmL",
	"ForearmL",
	"UpperArmR",
	"ForearmR",
	"SecondaryProp"
]


func _init() -> void:
	call_deferred("_run_verification")


func _get_all_mesh_instances(node: Node, out_list: Array[MeshInstance3D]) -> void:
	if node is MeshInstance3D:
		out_list.append(node as MeshInstance3D)
	for child: Node in node.get_children():
		_get_all_mesh_instances(child, out_list)


func _run_verification() -> void:
	print("=== STARTING DIRECT EMPIRICAL AUDIT OF ALL 11 ENEMY .GLB FILES ===")
	var total_errors: int = 0
	var test_root: Node3D = Node3D.new()
	root.add_child(test_root)

	for model_name: String in ENEMY_MODELS:
		var glb_path: String = "res://assets/models/enemies/" + model_name
		print("\n--- Inspecting: %s ---" % model_name)

		var scn: PackedScene = load(glb_path) as PackedScene
		if scn == null:
			push_error("[FAIL] Could not load PackedScene: " + glb_path)
			total_errors += 1
			continue

		var inst: Node = scn.instantiate()
		var inst_3d: Node3D = inst as Node3D
		if inst_3d == null:
			push_error("[FAIL] Instantiated root is not Node3D: " + glb_path)
			total_errors += 1
			continue

		test_root.add_child(inst_3d)
		inst_3d.global_position = Vector3.ZERO
		inst_3d.global_rotation = Vector3.ZERO

		# 1. Verify All 12 Articulated Nodes Present
		var nodes_map: Dictionary[String, Node3D] = {}
		var missing_nodes: Array[String] = []
		for req: String in REQUIRED_NODES:
			var found: Node3D = inst_3d.find_child(req, true, false) as Node3D
			if found == null:
				missing_nodes.append(req)
			else:
				nodes_map[req] = found

		if not missing_nodes.is_empty():
			push_error("[FAIL] %s is missing nodes: %s" % [model_name, str(missing_nodes)])
			total_errors += 1
		else:
			print("  [OK] All 12 articulated nodes present.")

		# 2. Verify Absence of Zero-Vertex Nodes and Count Vertices
		var mesh_instances: Array[MeshInstance3D] = []
		_get_all_mesh_instances(inst_3d, mesh_instances)

		var zero_vert_nodes: Array[String] = []
		var total_verts: int = 0
		var total_surfaces: int = 0

		for mi: MeshInstance3D in mesh_instances:
			var mesh: Mesh = mi.mesh
			if mesh == null:
				zero_vert_nodes.append(mi.name + " (null mesh)")
				continue
			var s_count: int = mesh.get_surface_count()
			total_surfaces += s_count
			if s_count == 0:
				zero_vert_nodes.append(mi.name + " (0 surfaces)")
				continue

			var mi_verts: int = 0
			for s: int in range(s_count):
				var arrays: Array = mesh.surface_get_arrays(s)
				if arrays.size() > Mesh.ARRAY_VERTEX and arrays[Mesh.ARRAY_VERTEX] != null:
					var varr: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array
					mi_verts += varr.size()

			if mi_verts == 0:
				zero_vert_nodes.append(mi.name + " (0 verts)")
			total_verts += mi_verts

		if not zero_vert_nodes.is_empty():
			push_error("[FAIL] %s has zero-vertex nodes: %s" % [model_name, str(zero_vert_nodes)])
			total_errors += 1
		else:
			print("  [OK] Absence of zero-vertex nodes verified (total %d mesh instances, %d surfaces, %d vertices)." % [
				mesh_instances.size(),
				total_surfaces,
				total_verts
			])

		# 3. Verify Pivot Coordinates for Shoulders, Elbows, Hips, Knees
		if missing_nodes.is_empty():
			var uarm_l: Node3D = nodes_map["UpperArmL"]
			var farm_l: Node3D = nodes_map["ForearmL"]
			var uarm_r: Node3D = nodes_map["UpperArmR"]
			var farm_r: Node3D = nodes_map["ForearmR"]
			var thigh_l: Node3D = nodes_map["ThighL"]
			var shin_l: Node3D = nodes_map["ShinL"]
			var thigh_r: Node3D = nodes_map["ThighR"]
			var shin_r: Node3D = nodes_map["ShinR"]
			var pelvis: Node3D = nodes_map["Pelvis"]
			var torso: Node3D = nodes_map["Torso"]

			var pos_uarm_l: Vector3 = uarm_l.global_position
			var pos_farm_l: Vector3 = farm_l.global_position
			var pos_uarm_r: Vector3 = uarm_r.global_position
			var pos_farm_r: Vector3 = farm_r.global_position
			var pos_thigh_l: Vector3 = thigh_l.global_position
			var pos_shin_l: Vector3 = shin_l.global_position
			var pos_thigh_r: Vector3 = thigh_r.global_position
			var pos_shin_r: Vector3 = shin_r.global_position

			print("  Pivots (Global in Model Space):")
			print("    Shoulder L (UpperArmL): (%.3f, %.3f, %.3f) | R (UpperArmR): (%.3f, %.3f, %.3f)" % [
				pos_uarm_l.x, pos_uarm_l.y, pos_uarm_l.z,
				pos_uarm_r.x, pos_uarm_r.y, pos_uarm_r.z
			])
			print("    Elbow    L (ForearmL) : (%.3f, %.3f, %.3f) | R (ForearmR) : (%.3f, %.3f, %.3f)" % [
				pos_farm_l.x, pos_farm_l.y, pos_farm_l.z,
				pos_farm_r.x, pos_farm_r.y, pos_farm_r.z
			])
			print("    Hip      L (ThighL)   : (%.3f, %.3f, %.3f) | R (ThighR)   : (%.3f, %.3f, %.3f)" % [
				pos_thigh_l.x, pos_thigh_l.y, pos_thigh_l.z,
				pos_thigh_r.x, pos_thigh_r.y, pos_thigh_r.z
			])
			print("    Knee     L (ShinL)    : (%.3f, %.3f, %.3f) | R (ShinR)    : (%.3f, %.3f, %.3f)" % [
				pos_shin_l.x, pos_shin_l.y, pos_shin_l.z,
				pos_shin_r.x, pos_shin_r.y, pos_shin_r.z
			])

			# Anatomical Sanity Assertions:
			# Shoulders above Pelvis and Hips:
			if pos_uarm_l.y <= pelvis.global_position.y or pos_uarm_r.y <= pelvis.global_position.y:
				push_error("[FAIL] Shoulders are below pelvis in %s!" % model_name)
				total_errors += 1
			# Elbows below Shoulders:
			if pos_farm_l.y >= pos_uarm_l.y or pos_farm_r.y >= pos_uarm_r.y:
				push_error("[FAIL] Elbows are above shoulders in %s!" % model_name)
				total_errors += 1
			# Hips below Pelvis / Torso:
			if pos_thigh_l.y >= torso.global_position.y or pos_thigh_r.y >= torso.global_position.y:
				push_error("[FAIL] Hips are above torso in %s!" % model_name)
				total_errors += 1
			# Knees below Hips:
			if pos_shin_l.y >= pos_thigh_l.y or pos_shin_r.y >= pos_thigh_r.y:
				push_error("[FAIL] Knees are above hips in %s!" % model_name)
				total_errors += 1
			# Left/Right lateral symmetry checks (X coordinates opposite signs):
			if pos_uarm_l.x >= 0.0 or pos_uarm_r.x <= 0.0:
				push_error("[FAIL] Shoulders lateral symmetry inverted in %s!" % model_name)
				total_errors += 1
			if pos_thigh_l.x >= 0.0 or pos_thigh_r.x <= 0.0:
				push_error("[FAIL] Hips lateral symmetry inverted in %s!" % model_name)
				total_errors += 1

		# 4. Verify Facing Vector Dot Product > 0.99 Forward
		# Forward in Godot is Vector3(0, 0, -1).
		# Check basis of Pelvis and Torso nodes
		if nodes_map.has("Pelvis") and nodes_map.has("Torso"):
			var p_fwd: Vector3 = -nodes_map["Pelvis"].global_transform.basis.z.normalized()
			var t_fwd: Vector3 = -nodes_map["Torso"].global_transform.basis.z.normalized()
			var target_fwd: Vector3 = Vector3(0.0, 0.0, -1.0)
			var dot_pelvis: float = p_fwd.dot(target_fwd)
			var dot_torso: float = t_fwd.dot(target_fwd)

			print("  Facing Dots: Pelvis.fwd dot (0,0,-1) = %.4f | Torso.fwd dot (0,0,-1) = %.4f" % [
				dot_pelvis,
				dot_torso
			])

			if dot_pelvis < 0.99 or dot_torso < 0.99:
				push_error("[FAIL] Facing dot < 0.99 in %s (Pelvis=%.4f, Torso=%.4f)" % [
					model_name, dot_pelvis, dot_torso
				])
				total_errors += 1

		# Also check ForearmR / weapon mesh forward orientation relative to shoulder:
		if nodes_map.has("UpperArmR") and nodes_map.has("ForearmR"):
			var uarm_r: Node3D = nodes_map["UpperArmR"]
			var farm_r: Node3D = nodes_map["ForearmR"]
			var mi_weapon: MeshInstance3D = null
			for c: Node in farm_r.get_children():
				if c is MeshInstance3D and (c as MeshInstance3D).mesh != null:
					mi_weapon = c as MeshInstance3D
					break
			if mi_weapon == null and farm_r is MeshInstance3D:
				mi_weapon = farm_r as MeshInstance3D

			if mi_weapon != null and mi_weapon.mesh != null:
				var aabb_center: Vector3 = mi_weapon.global_transform * mi_weapon.mesh.get_aabb().get_center()
				var arm_vec_flat: Vector3 = Vector3(
					aabb_center.x - uarm_r.global_position.x,
					0.0,
					aabb_center.z - uarm_r.global_position.z
				).normalized()
				var weapon_fwd_dot: float = arm_vec_flat.dot(Vector3(0.0, 0.0, -1.0))
				print("    Weapon/ForearmR AABB forward dot vs (0,0,-1): %.4f" % weapon_fwd_dot)

		inst_3d.queue_free()

	print("\n=======================================================")
	if total_errors == 0:
		print("=== ALL 11 ENEMY .GLB AUDIT PASSED WITH 0 ERRORS! ===")
		quit(0)
	else:
		push_error("=== AUDIT FAILED WITH %d TOTAL ERRORS! ===" % total_errors)
		quit(1)
