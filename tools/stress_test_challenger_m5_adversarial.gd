extends SceneTree

# ==============================================================================
# ADVERSARIAL STRESS TEST HARNESS — MILESTONE 5
# Pushing Edge Cases, Concurrency, Rapid-Fire, and Loadout Swapping
# ==============================================================================

var total_assertions: int = 0
var total_failures: int = 0


func _init() -> void:
	call_deferred("_run_adversarial_stress_tests")


func _run_adversarial_stress_tests() -> void:
	print("\n================================================================================")
	print(">>> ADVERSARIAL STRESS TEST HARNESS: RUNNING EXTREME BOUNDARY TESTS <<<")
	print("================================================================================\n")

	await _stress_test_body_shadow_extreme_loadouts()
	await _stress_test_viewmodel_ultra_rapid_fire()
	await _stress_test_portal_hammering()
	await _stress_test_loot_mass_instantiation()

	print("\n================================================================================")
	print(">>> ADVERSARIAL STRESS TEST SUMMARY <<<")
	print("Total Stress Assertions: %d" % total_assertions)
	print("Total Failures: %d" % total_failures)
	if total_failures == 0:
		print(">>> ALL ADVERSARIAL STRESS TESTS SURVIVED WITH ZERO CORRUPTIONS! <<<")
		print("================================================================================\n")
		quit(0)
	else:
		print(">>> STRESS TEST FAILURES DETECTED! <<<")
		print("================================================================================\n")
		quit(1)


func _assert_true(cond: bool, msg: String) -> void:
	total_assertions += 1
	if not cond:
		total_failures += 1
		push_error("[STRESS_FAIL] %s" % msg)
		print("  [STRESS_FAIL] %s" % msg)
	else:
		print("  [STRESS_PASS] %s" % msg)


# ------------------------------------------------------------------------------
# 1. Body Controller: 100 rapid armor switches, negative indices, null loadout
# ------------------------------------------------------------------------------
func _stress_test_body_shadow_extreme_loadouts() -> void:
	print("--- 1. Stress Testing FirstPersonBodyController Loadouts ---")
	var body: FirstPersonBodyController = FirstPersonBodyController.new()
	var parent: Node3D = Node3D.new()
	var lm: PlayerLoadoutManager = PlayerLoadoutManager.new()
	lm.name = "PlayerLoadoutManager"
	parent.add_child(lm)
	parent.add_child(body)
	root.add_child(parent)
	body._ready()

	# 100 random armor set changes in rapid succession
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = 12345
	var all_remained_shadows_only: bool = true

	for i: int in range(100):
		var c: int = rng.randi_range(-10, 10)
		var l: int = rng.randi_range(-10, 10)
		var f: int = rng.randi_range(-10, 10)
		lm.equip_armor_slot("CHEST", c)
		lm.equip_armor_slot("LEGS", l)
		lm.equip_armor_slot("FEET", f)
		body.refresh_armor_appearance()

		var geoms: Array[Node] = body.find_children("*", "GeometryInstance3D", true, false)
		for n: Node in geoms:
			var gi: GeometryInstance3D = n as GeometryInstance3D
			if gi.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY:
				all_remained_shadows_only = false
				break

	_assert_true(all_remained_shadows_only, "100 rapid random armor swaps maintained SHADOWS_ONLY on 100% of meshes")

	# Test motion update with extreme angles (-90 to +90 degrees)
	for pitch_deg: float in [-90.0, -85.0, -45.0, 0.0, 45.0, 85.0, 90.0]:
		body.update_body_motion(0.016, Vector3(0.0, 0.0, -8.0), 0.0, deg_to_rad(pitch_deg), true, false)
		_assert_true(body.position.is_finite(), "Body position finite at pitch %.1f deg" % pitch_deg)
		_assert_true(body.rotation.is_finite(), "Body rotation finite at pitch %.1f deg" % pitch_deg)

	parent.queue_free()
	print("  Finished Body Controller Stress Test.\n")


# ------------------------------------------------------------------------------
# 2. Viewmodel Recoil: 200 rapid fire calls with chaotic intervals
# ------------------------------------------------------------------------------
func _stress_test_viewmodel_ultra_rapid_fire() -> void:
	print("--- 2. Stress Testing FPSViewmodelController Ultra Rapid Fire ---")
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

	# Fire 50 times in immediate loop with varying intensities
	var intensities: Array[float] = [0.5, 1.0, 1.35, 1.2, 2.0, 0.1]
	for i: int in range(50):
		var intens: float = intensities[i % intensities.size()]
		vm.trigger_shoot_recoil(intens)
		# Assert no NaN or Infinity
		_assert_true(vm._weapon_mount_recoil_pos.is_finite(), "Recoil pos finite during spam (%d)" % i)
		_assert_true(vm._weapon_mount_recoil_rot.is_finite(), "Recoil rot finite during spam (%d)" % i)
		# Assert pos.z never exceeds maximum single kick (0.055 * 2.0 = 0.11)
		_assert_true(vm._weapon_mount_recoil_pos.z <= 0.1101, "Recoil pos.z does NOT accumulate across spam (%d)" % i)

	# Wait for snap-back recovery
	await create_timer(0.25).timeout
	vm._apply_hand_transforms()

	_assert_true(vm._weapon_mount_recoil_pos.length() < 0.0001, "Full recovery to ZERO after 50-shot burst (pos len: %.8f)" % vm._weapon_mount_recoil_pos.length())
	_assert_true(vm._weapon_mount_recoil_rot.length() < 0.0001, "Full recovery to ZERO after 50-shot burst (rot len: %.8f)" % vm._weapon_mount_recoil_rot.length())

	vm.queue_free()
	print("  Finished Viewmodel Recoil Stress Test.\n")


# ------------------------------------------------------------------------------
# 3. OccultPortal: 50 concurrent warp calls hammering the portal
# ------------------------------------------------------------------------------
func _stress_test_portal_hammering() -> void:
	print("--- 3. Stress Testing OccultPortal Re-Entrancy Hammering ---")
	var portal: OccultPortal = OccultPortal.new()
	portal.biome_id = 1
	portal.biome_title = "The Endless Ossuary"
	portal.is_return_portal = false
	root.add_child(portal)
	portal._ready()

	var dummy_player: CharacterBody3D = CharacterBody3D.new()
	dummy_player.name = "DummyPlayerStress"
	root.add_child(dummy_player)

	# Hammer portal 50 times in a tight loop
	for i: int in range(50):
		portal.trigger_portal_warp(dummy_player)

	# Count how many overlays exist on root: MUST be exactly 1!
	var overlay_count: int = 0
	for ch: Node in root.get_children():
		if ch.name == "RiftLoadingOverlayLayer":
			overlay_count += 1

	_assert_true(overlay_count == 1, "Exactly 1 RiftLoadingOverlayLayer spawned despite 50 hammered calls (found %d)" % overlay_count)

	# Await cleanup
	await create_timer(0.45).timeout
	var overlays_after: int = 0
	for ch: Node in root.get_children():
		if ch.name == "RiftLoadingOverlayLayer":
			overlays_after += 1
	_assert_true(overlays_after == 0, "All overlays cleanly freed after tween (found %d)" % overlays_after)

	dummy_player.queue_free()
	portal.queue_free()
	print("  Finished Portal Stress Test.\n")


# ------------------------------------------------------------------------------
# 4. LootDropPickup: Spawning 100 loot drops simultaneously
# ------------------------------------------------------------------------------
func _stress_test_loot_mass_instantiation() -> void:
	print("--- 4. Stress Testing LootDropPickup Mass Instantiation ---")
	var drops: Array[LootDropPickup] = []
	var categories: Array[String] = ["xp_essence", "heal", "armor", "silver", "bone_ash", "eldritch_ichor", "relic"]

	for i: int in range(100):
		var p: LootDropPickup = LootDropPickup.new()
		p.drop_category = categories[i % categories.size()]
		root.add_child(p)
		drops.append(p)

	_assert_true(drops.size() == 100, "Successfully instantiated 100 LootDropPickup instances simultaneously")

	var all_share_single_mesh: bool = true
	var all_have_facets: bool = true
	for p: LootDropPickup in drops:
		var core: MeshInstance3D = p.find_child("FacetedCrystalCore", true, false) as MeshInstance3D
		if core == null or core.mesh != LootDropPickup._shared_crystal_mesh:
			all_share_single_mesh = false
		if core == null or core.mesh is SphereMesh:
			all_have_facets = false

	_assert_true(all_share_single_mesh, "All 100 loot drops share the exact same micro-voxel ArrayMesh instance in memory")
	_assert_true(all_have_facets, "Zero of the 100 loot drops instantiate or reference a SphereMesh")

	for p: LootDropPickup in drops:
		p.queue_free()

	print("  Finished Loot Mass Instantiation Stress Test.\n")
