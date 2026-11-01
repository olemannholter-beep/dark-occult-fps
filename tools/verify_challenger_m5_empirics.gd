extends SceneTree

# ==============================================================================
# EMPIRICAL CHALLENGER TEST SUITE — MILESTONE 5
# Verification of Body Shadows, Recoil, Portal Overlay, and Micro-Voxels
# ==============================================================================

var total_assertions_run: int = 0
var total_failures: int = 0


func _init() -> void:
	call_deferred("_execute_all_empirical_tests")


func _execute_all_empirical_tests() -> void:
	print("\n================================================================================")
	print(">>> EMPIRICAL CHALLENGER TEST SUITE: RUNNING HEADLESS ORACLE TESTS <<<")
	print("================================================================================\n")

	await _test_1_first_person_body_shadow_only()
	await _test_2_fps_viewmodel_recoil()
	await _test_3_occult_portal_reentrancy_and_overlay()
	await _test_4_micro_voxel_assets()
	await _test_5_loot_drop_pickup_fallback()

	print("\n================================================================================")
	print(">>> EMPIRICAL TEST SUITE SUMMARY <<<")
	print("Total Assertions Passed: %d" % total_assertions_run)
	print("Total Failures: %d" % total_failures)
	if total_failures == 0:
		print(">>> FINAL VERDICT: ALL TESTS PASSED CLEANLY (VERDICT: APPROVE) <<<")
		print("================================================================================\n")
		quit(0)
	else:
		print(">>> FINAL VERDICT: FAILURES DETECTED (VERDICT: REQUEST_CHANGES) <<<")
		print("================================================================================\n")
		quit(1)


func _assert_true(condition: bool, message: String) -> void:
	total_assertions_run += 1
	if not condition:
		total_failures += 1
		push_error("[FAIL] %s" % message)
		print("  [FAIL] %s" % message)
	else:
		print("  [PASS] %s" % message)


# ------------------------------------------------------------------------------
# TEST 1: FirstPersonBodyController Shadow-Only Geometry
# ------------------------------------------------------------------------------
func _test_1_first_person_body_shadow_only() -> void:
	print("--- TEST 1: FirstPersonBodyController Shadow-Only Geometry ---")
	var body: FirstPersonBodyController = FirstPersonBodyController.new()
	var test_parent: Node3D = Node3D.new()
	var lm: PlayerLoadoutManager = PlayerLoadoutManager.new()
	lm.name = "PlayerLoadoutManager"
	test_parent.add_child(lm)
	test_parent.add_child(body)
	root.add_child(test_parent)

	body._ready()

	# 1. Assert all child GeometryInstance3D nodes have SHADOW_CASTING_SETTING_SHADOWS_ONLY (3)
	var geoms: Array[Node] = body.find_children("*", "GeometryInstance3D", true, false)
	_assert_true(geoms.size() >= 3, "FirstPersonBodyController has >= 3 GeometryInstance3D nodes (found %d)" % geoms.size())

	var all_shadows_only_ready: bool = true
	var bad_node_names: Array[String] = []
	for n: Node in geoms:
		var gi: GeometryInstance3D = n as GeometryInstance3D
		if gi.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY:
			all_shadows_only_ready = false
			bad_node_names.append("%s (cast_shadow=%d)" % [gi.name, gi.cast_shadow])

	_assert_true(all_shadows_only_ready, "All GeometryInstance3D on _ready() have SHADOWS_ONLY (bad: %s)" % str(bad_node_names))

	# 2. Test cycling through all 4 armor sets (0..3) with refresh_armor_appearance()
	for set_idx: int in range(4):
		lm.equip_armor_slot("CHEST", set_idx)
		lm.equip_armor_slot("LEGS", set_idx)
		lm.equip_armor_slot("FEET", set_idx)
		body.refresh_armor_appearance()

		var set_geoms: Array[Node] = body.find_children("*", "GeometryInstance3D", true, false)
		var set_shadows_only: bool = true
		for n: Node in set_geoms:
			var gi: GeometryInstance3D = n as GeometryInstance3D
			if gi.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY:
				set_shadows_only = false
				break
		_assert_true(set_shadows_only, "Armor Set %d maintains SHADOWS_ONLY on all %d meshes" % [set_idx, set_geoms.size()])

	# 3. Test _apply_first_person_shadow_only directly on newly spawned dynamic geometry
	var dynamic_mesh: MeshInstance3D = MeshInstance3D.new()
	dynamic_mesh.name = "DynamicTestMesh"
	dynamic_mesh.mesh = BoxMesh.new()
	dynamic_mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	body.torso_node.add_child(dynamic_mesh)
	body._apply_first_person_shadow_only(body)
	_assert_true(dynamic_mesh.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY, "Dynamic mesh converted to SHADOWS_ONLY via _apply_first_person_shadow_only()")

	test_parent.queue_free()
	print("  Finished Test 1.\n")


# ------------------------------------------------------------------------------
# TEST 2: FPSViewmodelController Mount Recoil Kick & Snap-back
# ------------------------------------------------------------------------------
func _test_2_fps_viewmodel_recoil() -> void:
	print("--- TEST 2: FPSViewmodelController Mount Recoil Kick & Recovery ---")
	var vm: FPSViewmodelController = FPSViewmodelController.new()
	var r_hand: Node3D = Node3D.new()
	r_hand.name = "RightHandPivot"
	var l_hand: Node3D = Node3D.new()
	l_hand.name = "LeftHandPivot"
	vm.add_child(r_hand)
	vm.add_child(l_hand)
	vm.right_hand_pivot = r_hand
	vm.left_hand_pivot = l_hand
	root.add_child(vm)
	vm._ready()

	# 1. Assert initial recoil is zero
	_assert_true(vm._weapon_mount_recoil_pos == Vector3.ZERO, "Initial _weapon_mount_recoil_pos is Vector3.ZERO")
	_assert_true(vm._weapon_mount_recoil_rot == Vector3.ZERO, "Initial _weapon_mount_recoil_rot is Vector3.ZERO")

	# 2. Trigger recoil with intensity 1.0
	vm.trigger_shoot_recoil(1.0)
	_assert_true(absf(vm._weapon_mount_recoil_pos.z - 0.055) < 0.0001, "Recoil kick +Z is 0.055 (actual: %.4f)" % vm._weapon_mount_recoil_pos.z)
	_assert_true(absf(vm._weapon_mount_recoil_rot.x - deg_to_rad(5.5)) < 0.0001, "Recoil pitch +X is deg_to_rad(5.5) (actual: %.4f)" % vm._weapon_mount_recoil_rot.x)

	# 3. Assert hand transforms updated
	_assert_true(r_hand.position.z > vm.right_base_pos.z + 0.050, "Right hand pivot displaced towards camera by recoil")
	_assert_true(r_hand.rotation.x > vm.right_base_rot.x + deg_to_rad(5.0), "Right hand pivot pitched upward by recoil")

	# 4. Stress test: Rapid-fire spam (10 consecutive triggers) must NOT cause additive drift
	for i: int in range(10):
		vm.trigger_shoot_recoil(1.0)

	_assert_true(absf(vm._weapon_mount_recoil_pos.z - 0.055) < 0.0001, "Rapid-fire does NOT accumulate additive position drift (pos.z = %.4f)" % vm._weapon_mount_recoil_pos.z)
	_assert_true(absf(vm._weapon_mount_recoil_rot.x - deg_to_rad(5.5)) < 0.0001, "Rapid-fire does NOT accumulate additive pitch drift (rot.x = %.4f)" % vm._weapon_mount_recoil_rot.x)

	# 5. Recovery test: Wait 0.22s (tween duration is 0.14s)
	await create_timer(0.22).timeout
	vm._apply_hand_transforms()

	_assert_true(vm._weapon_mount_recoil_pos.length() < 0.0001, "Recoil position returns cleanly to Vector3.ZERO after tween (len: %.6f)" % vm._weapon_mount_recoil_pos.length())
	_assert_true(vm._weapon_mount_recoil_rot.length() < 0.0001, "Recoil rotation returns cleanly to Vector3.ZERO after tween (len: %.6f)" % vm._weapon_mount_recoil_rot.length())
	_assert_true(absf(r_hand.position.z - vm.right_base_pos.z) < 0.001, "Right hand pivot position returns to base position")
	_assert_true(absf(r_hand.rotation.x - vm.right_base_rot.x) < 0.001, "Right hand pivot rotation returns to base rotation")

	vm.queue_free()
	print("  Finished Test 2.\n")


# ------------------------------------------------------------------------------
# TEST 3: OccultPortal Re-Entrancy Guard & Layer 120 Loading Overlay
# ------------------------------------------------------------------------------
func _test_3_occult_portal_reentrancy_and_overlay() -> void:
	print("--- TEST 3: OccultPortal Re-Entrancy & Loading Overlay ---")
	var portal: OccultPortal = OccultPortal.new()
	portal.biome_id = 1
	portal.biome_title = "The Endless Ossuary"
	portal.is_return_portal = false
	root.add_child(portal)
	portal._ready()

	var dummy_player: CharacterBody3D = CharacterBody3D.new()
	dummy_player.name = "DummyPlayer"
	root.add_child(dummy_player)

	# 1. Assert initial state
	_assert_true(portal._is_generating_rift == false, "Initial portal._is_generating_rift is false")

	# 2. Assert re-entrancy protection
	portal._is_generating_rift = true
	var child_count_before: int = root.get_child_count()
	portal.trigger_portal_warp(dummy_player)
	var child_count_after: int = root.get_child_count()
	_assert_true(child_count_before == child_count_after, "Re-entrancy guard blocks concurrent trigger_portal_warp execution")

	portal._is_generating_rift = false

	# 3. Trigger warp and verify loading overlay creation and configuration
	portal.trigger_portal_warp(dummy_player)

	# Look for RiftLoadingOverlayLayer in root
	var overlay: CanvasLayer = root.find_child("RiftLoadingOverlayLayer", true, false) as CanvasLayer
	_assert_true(overlay != null and is_instance_valid(overlay), "RiftLoadingOverlayLayer spawned on root during rift generation")
	if overlay != null:
		_assert_true(overlay.layer == 120, "RiftLoadingOverlayLayer has layer == 120 (actual: %d)" % overlay.layer)

		var root_ctrl: Control = overlay.find_child("RiftLoadingOverlayRoot", true, false) as Control
		_assert_true(root_ctrl != null and root_ctrl.mouse_filter == Control.MOUSE_FILTER_STOP, "Loading overlay root has MOUSE_FILTER_STOP")

		var backdrop: ColorRect = overlay.find_child("Backdrop", true, false) as ColorRect
		_assert_true(backdrop != null and backdrop.color.is_equal_approx(Color(0.03, 0.03, 0.04, 0.96)), "Backdrop ColorRect has Color(0.03, 0.03, 0.04, 0.96)")

		var title_lbl: Label = overlay.find_child("TitleLabel", true, false) as Label
		_assert_true(title_lbl != null and title_lbl.text == "DESCENDING INTO THE ENDLESS OSSUARY...", "TitleLabel has text: 'DESCENDING INTO THE ENDLESS OSSUARY...'")

		var sub_lbl: Label = overlay.find_child("SubtitleLabel", true, false) as Label
		_assert_true(sub_lbl != null and sub_lbl.text.contains("CARVING SUBTERRANEAN VOXEL SANCTUMS"), "SubtitleLabel contains 'CARVING SUBTERRANEAN VOXEL SANCTUMS'")

	# 4. Wait for fade-out tween and teardown (0.35s + margin)
	await create_timer(0.45).timeout
	var overlay_after: CanvasLayer = root.find_child("RiftLoadingOverlayLayer", true, false) as CanvasLayer
	_assert_true(overlay_after == null, "RiftLoadingOverlayLayer is freed after fade-out tween")

	# 5. Verify return portal mode (does not spawn overlay, resets velocity, moves player)
	portal.is_return_portal = true
	portal.return_destination = Vector3(10.0, 2.0, -15.0)
	dummy_player.velocity = Vector3(5.0, 0.0, 5.0)
	portal.trigger_portal_warp(dummy_player)

	_assert_true(dummy_player.global_position.is_equal_approx(Vector3(10.0, 2.0, -15.0)), "Return portal teleports player to return_destination")
	_assert_true(dummy_player.velocity == Vector3.ZERO, "Return portal zeroes player velocity")
	_assert_true(portal._is_generating_rift == false, "Return portal does not set _is_generating_rift")

	dummy_player.queue_free()
	portal.queue_free()
	print("  Finished Test 3.\n")


# ------------------------------------------------------------------------------
# TEST 4: Micro-Voxel Models (Hierarchy, Absence of Smooth Primitives, Materials)
# ------------------------------------------------------------------------------
func _test_4_micro_voxel_assets() -> void:
	print("--- TEST 4: Micro-Voxel 3D Assets Integrity ---")
	var target_models: Array[String] = [
		"res://assets/models/enemies/enemy_01_ossuary_executioner.glb",
		"res://assets/models/enemies/enemy_03_reliquary_hexweaver.glb",
		"res://assets/models/items/loot_alchemical_elixir.glb"
	]

	for path: String in target_models:
		var scn: PackedScene = load(path) as PackedScene
		_assert_true(scn != null, "Successfully loaded PackedScene: %s" % path)
		if scn == null:
			continue

		var inst: Node3D = scn.instantiate() as Node3D
		_assert_true(inst != null, "Instantiated root is Node3D: %s" % path)
		root.add_child(inst)

		var mesh_instances: Array[Node] = inst.find_children("*", "MeshInstance3D", true, false)
		_assert_true(mesh_instances.size() > 0, "%s has %d MeshInstance3D nodes" % [path.get_file(), mesh_instances.size()])

		var total_surfaces: int = 0
		var total_vertices: int = 0
		var axis_aligned_faces: int = 0
		var total_faces: int = 0
		var has_missing_material: bool = false
		var has_vertex_colors: bool = false

		for n: Node in mesh_instances:
			var mi: MeshInstance3D = n as MeshInstance3D
			var m: Mesh = mi.mesh
			if m == null:
				continue
			var sc: int = m.get_surface_count()
			total_surfaces += sc
			for s: int in range(sc):
				var mat: Material = mi.get_surface_override_material(s)
				if mat == null:
					mat = m.surface_get_material(s)
				if mat == null:
					has_missing_material = true

				var arrays: Array = m.surface_get_arrays(s)
				if arrays.size() > Mesh.ARRAY_COLOR and arrays[Mesh.ARRAY_COLOR] != null:
					has_vertex_colors = true

				if arrays.size() > Mesh.ARRAY_VERTEX and arrays[Mesh.ARRAY_VERTEX] != null:
					var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array
					total_vertices += verts.size()

					# Check triangle normals for micro-voxel / faceted box alignment
					var idx_arr: PackedInt32Array = arrays[Mesh.ARRAY_INDEX] as PackedInt32Array
					if idx_arr != null and idx_arr.size() >= 3:
						var t_count: int = idx_arr.size() / 3
						var step: int = maxi(1, t_count / 100)
						for t: int in range(0, t_count, step):
							var i0: int = idx_arr[t * 3]
							var i1: int = idx_arr[t * 3 + 1]
							var i2: int = idx_arr[t * 3 + 2]
							var v0: Vector3 = verts[i0]
							var v1: Vector3 = verts[i1]
							var v2: Vector3 = verts[i2]
							var fn: Vector3 = (v1 - v0).cross(v2 - v0).normalized()
							total_faces += 1
							var c0: float = absf(fn.x)
							var c1: float = absf(fn.y)
							var c2: float = absf(fn.z)
							var comps: Array[float] = [c0, c1, c2]
							comps.sort()
							# comps[2] is largest, comps[1] is middle, comps[0] is smallest
							# Cardinal axis-aligned: (1, 0, 0) -> comps[2] > 0.96
							# 45-deg planar diagonal/chamfer: (0.707, 0.707, 0) -> comps[2] > 0.67 and comps[1] > 0.67
							# Corner chamfer: (0.577, 0.577, 0.577) -> comps[0] > 0.54
							var is_faceted_box_normal: bool = (comps[2] > 0.96) or (comps[2] > 0.67 and comps[1] > 0.67) or (comps[0] > 0.54)
							if is_faceted_box_normal:
								axis_aligned_faces += 1

		_assert_true(not has_missing_material, "%s has valid material slot assignments across all surfaces" % path.get_file())
		_assert_true(has_vertex_colors, "%s has baked vertex cavity colors (Mesh.ARRAY_COLOR)" % path.get_file())

		if total_faces > 0:
			var faceted_ratio: float = float(axis_aligned_faces) / float(total_faces)
			print("    %s: %d total sampled faces, %d discrete faceted/box faces (ratio: %.2f%%)" % [
				path.get_file(), total_faces, axis_aligned_faces, faceted_ratio * 100.0
			])
			_assert_true(faceted_ratio >= 0.75, "%s has discrete faceted micro-voxel geometry (ratio: %.2f%% >= 75%%)" % [path.get_file(), faceted_ratio * 100.0])

		# For enemy models, verify articulated hierarchy nodes
		if path.contains("enemy_"):
			var req_nodes: Array[String] = ["Pelvis", "Torso", "Head", "UpperArmL", "ForearmL", "UpperArmR", "ForearmR", "ThighL", "ShinL", "ThighR", "ShinR", "SecondaryProp"]
			var missing_nodes: Array[String] = []
			for req: String in req_nodes:
				if inst.find_child(req, true, false) == null:
					missing_nodes.append(req)
			_assert_true(missing_nodes.is_empty(), "%s preserves all 12 articulated hierarchy nodes (missing: %s)" % [path.get_file(), str(missing_nodes)])

		inst.queue_free()

	print("  Finished Test 4.\n")


# ------------------------------------------------------------------------------
# TEST 5: LootDropPickup Fallback Mesh (ArrayMesh Box Cluster, No SphereMesh)
# ------------------------------------------------------------------------------
func _test_5_loot_drop_pickup_fallback() -> void:
	print("--- TEST 5: LootDropPickup Fallback Micro-Voxel Mesh ---")
	LootDropPickup._ensure_shared_loot_resources()

	var shared_mesh: Mesh = LootDropPickup._shared_crystal_mesh
	_assert_true(shared_mesh != null, "_shared_crystal_mesh is instantiated")
	_assert_true(shared_mesh is ArrayMesh, "_shared_crystal_mesh is an ArrayMesh")
	_assert_true(not (shared_mesh is SphereMesh), "_shared_crystal_mesh is NOT a SphereMesh")

	if shared_mesh is ArrayMesh:
		var am: ArrayMesh = shared_mesh as ArrayMesh
		_assert_true(am.get_surface_count() == 1, "_shared_crystal_mesh has 1 surface")
		var arrays: Array = am.surface_get_arrays(0)
		var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array
		var norms: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL] as PackedVector3Array

		# 4 boxes * 6 faces * 6 vertices = 144 vertices
		_assert_true(verts.size() == 144, "Fallback mesh has 144 vertices (4 micro-voxel boxes * 36 verts) [actual: %d]" % verts.size())
		_assert_true(norms.size() == 144, "Fallback mesh has 144 normals [actual: %d]" % norms.size())

		var all_normals_cardinal: bool = true
		for n: Vector3 in norms:
			var max_c: float = maxf(absf(n.x), maxf(absf(n.y), absf(n.z)))
			if absf(max_c - 1.0) > 0.001 or absf(n.length() - 1.0) > 0.001:
				all_normals_cardinal = false
				break
		_assert_true(all_normals_cardinal, "100% of fallback mesh normals are strictly cardinal unit vectors (zero smooth normals)")

	# Instantiate LootDropPickup and verify runtime binding
	var pickup: LootDropPickup = LootDropPickup.new()
	root.add_child(pickup) # Calls _ready() automatically

	var core_mi: MeshInstance3D = pickup.find_child("FacetedCrystalCore", true, false) as MeshInstance3D
	_assert_true(core_mi != null, "LootDropPickup creates FacetedCrystalCore MeshInstance3D")
	if core_mi != null:
		_assert_true(core_mi.mesh == shared_mesh, "FacetedCrystalCore uses the micro-voxel ArrayMesh")
		_assert_true(not (core_mi.mesh is SphereMesh), "FacetedCrystalCore does NOT use SphereMesh")

	pickup.queue_free()
	print("  Finished Test 5.\n")

