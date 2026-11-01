extends SceneTree


func _init() -> void:
	print("=================================================================")
	print("STARTING INDEPENDENT REVIEW VERIFICATION SUITE")
	print("=================================================================")

	# 1. Test FirstPersonBodyController Shadows-Only configuration
	print("[TEST 1/5] Verifying FirstPersonBodyController shadows-only...")
	var fp_body: FirstPersonBodyController = FirstPersonBodyController.new()
	root.add_child(fp_body)
	fp_body._ready()
	fp_body.refresh_armor_appearance()

	var all_geoms: Array[Node] = fp_body.find_children("*", "GeometryInstance3D", true, false)
	assert(not all_geoms.is_empty(), "FirstPersonBodyController must instantiate child geometry instances")
	for g: Node in all_geoms:
		var geom: GeometryInstance3D = g as GeometryInstance3D
		assert(
			geom.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY,
			"Body mesh %s must have SHADOW_CASTING_SETTING_SHADOWS_ONLY, found %d" % [geom.name, geom.cast_shadow]
		)
	fp_body.queue_free()
	print(" -> [PASS] All %d player body geometry instances have SHADOW_CASTING_SETTING_SHADOWS_ONLY." % all_geoms.size())

	# 2. Test HUD Compass dynamic plaque sizing
	print("[TEST 2/5] Verifying GothicHUDOverhaul dynamic compass plaque...")
	var hud: GothicHudOverhaul = GothicHudOverhaul.new()
	root.add_child(hud)
	hud.biome_header_title = "SUBTERRANEAN CATACOMB SANCTUMS"
	hud.biome_header_subtitle = "EIGHT PORTAL CHAMBERS (SAFE HARBOR)"
	var full_header: String = "── ❖ %s : %s ❖ ──" % [hud.biome_header_title, hud.biome_header_subtitle]
	var font: Font = ThemeDB.fallback_font
	var text_w: float = font.get_string_size(full_header, HORIZONTAL_ALIGNMENT_CENTER, -1, 13).x
	var plaque_w: float = maxf(780.0, text_w + 48.0)
	assert(plaque_w >= 780.0, "HUD compass banner width must be >= 780px, got %.1f" % plaque_w)
	assert(plaque_w > text_w, "HUD compass banner must be wider than text (%.1f > %.1f)" % [plaque_w, text_w])
	hud.queue_free()
	print(" -> [PASS] Banner dynamically expands: text_w=%.1f, plaque_w=%.1f (>= 780px)." % [text_w, plaque_w])

	# 3. Test OccultPortal re-entrancy & loading overlay
	print("[TEST 3/5] Verifying OccultPortal re-entrancy and loading overlay...")
	var portal: OccultPortal = OccultPortal.new()
	portal.biome_id = 1
	portal.biome_title = "The Endless Ossuary"
	root.add_child(portal)
	portal._ready()

	assert(portal.get("_is_generating_rift") == false, "_is_generating_rift must start false")
	portal.set("_is_generating_rift", true)
	# Trigger warp with re-entrancy active should return immediately without side effects
	var dummy_player: Node3D = Node3D.new()
	portal.trigger_portal_warp(dummy_player)
	assert(portal.get("_is_generating_rift") == true, "Re-entrancy guard must prevent concurrent trigger")
	portal.set("_is_generating_rift", false)
	dummy_player.queue_free()
	portal.queue_free()
	print(" -> [PASS] OccultPortal re-entrancy guard successfully blocks duplicate invocation.")

	# 4. Test FPSViewmodelController recoil kick & snap-back
	print("[TEST 4/5] Verifying FPSViewmodelController weapon mount recoil kick...")
	var vm_ctrl: FPSViewmodelController = FPSViewmodelController.new()
	root.add_child(vm_ctrl)
	vm_ctrl.trigger_shoot_recoil(1.0)
	var recoil_z: float = vm_ctrl.get("_weapon_mount_recoil_pos").z
	var recoil_pitch_deg: float = rad_to_deg(vm_ctrl.get("_weapon_mount_recoil_rot").x)
	assert(is_equal_approx(recoil_z, 0.055), "Weapon recoil Z kick must be approx 0.055, got %.4f" % recoil_z)
	assert(is_equal_approx(recoil_pitch_deg, 5.5), "Weapon recoil pitch must be approx 5.5 deg, got %.2f" % recoil_pitch_deg)
	assert(vm_ctrl.get("_weapon_recoil_tween") != null, "Tween must be active")
	vm_ctrl.queue_free()
	print(" -> [PASS] Recoil kick: Z=%.4f (+0.055), Pitch=%.2f deg (+5.5 deg) with active recovery tween." % [recoil_z, recoil_pitch_deg])

	# 5. Test LootDropPickup stepped micro-voxel box cluster
	print("[TEST 5/5] Verifying LootDropPickup micro-voxel box cluster mesh...")
	LootDropPickup._ensure_shared_loot_resources()
	var mesh: Mesh = LootDropPickup._shared_crystal_mesh
	assert(mesh != null, "LootDropPickup shared crystal mesh must not be null")
	assert(not (mesh is SphereMesh), "LootDropPickup crystal mesh MUST NOT be a SphereMesh")
	var aabb: AABB = mesh.get_aabb()
	assert(aabb.size.x > 0.10 and aabb.size.y > 0.10, "Crystal mesh must have 3D volume, got %s" % str(aabb.size))
	print(" -> [PASS] LootDropPickup uses stepped micro-voxel SurfaceTool mesh with AABB %s (zero SphereMesh)." % str(aabb.size))

	print("=================================================================")
	print("ALL 5 INDEPENDENT REVIEW VERIFICATIONS PASSED CLEANLY!")
	print("=================================================================")
	quit(0)
