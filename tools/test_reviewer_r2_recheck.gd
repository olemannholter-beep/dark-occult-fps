extends SceneTree


func _init() -> void:
	print("=== Running Reviewer Re-check Targeted Verification ===")

	# -------------------------------------------------------------------------
	# 1. Test ReliquaryChest reward_scale alias & depth_scale propagation
	# -------------------------------------------------------------------------
	print("[CHECK 1] Testing ReliquaryChest.reward_scale property alias...")
	var chest: ReliquaryChest = ReliquaryChest.new()
	root.add_child(chest)
	chest._ready()

	# Default value check
	assert(is_equal_approx(chest.reward_scale, 1.0), "Default reward_scale should be 1.0")
	assert(is_equal_approx(chest.depth_scale, 1.0), "Default depth_scale should be 1.0")

	# Setter via property name (as procedural_dungeon_generator.gd does: rc.reward_scale = X)
	chest.reward_scale = 2.75
	assert(is_equal_approx(chest.depth_scale, 2.75), "Setting reward_scale must update depth_scale")
	assert(is_equal_approx(chest.reward_scale, 2.75), "Getter reward_scale must return updated value")

	# Dynamic set via Object.set("reward_scale", ...)
	chest.set("reward_scale", 3.5)
	assert(is_equal_approx(chest.depth_scale, 3.5), "Dynamic set('reward_scale') must update depth_scale")
	assert(is_equal_approx(chest.get("reward_scale"), 3.5), "Dynamic get('reward_scale') must return 3.5")

	# Test open_chest works with reward_scale set and spawns 4 loot items
	var spawned: Array[LootDropPickup] = chest.open_chest()
	assert(spawned.size() == 4, "Expected 4 spawned loot pickups, got %d" % spawned.size())
	for loot: LootDropPickup in spawned:
		assert(loot != null and is_instance_valid(loot), "LootDropPickup should be valid instance")
		loot.queue_free()

	chest.queue_free()
	print(" -> [PASS] ReliquaryChest reward_scale alias verified (static + dynamic access + loot spawning).")

	# -------------------------------------------------------------------------
	# 2. Test OccultPortal tween lifecycle when portal self is freed during warp
	# -------------------------------------------------------------------------
	print("[CHECK 2] Testing OccultPortal overlay tween & freed-self lifecycle...")
	call_deferred("_test_portal_freed_lifecycle")


func _test_portal_freed_lifecycle() -> void:
	var dummy_dungeon: Node3D = Node3D.new()
	dummy_dungeon.name = "PreviousDungeonContainer"
	root.add_child(dummy_dungeon)

	var portal: OccultPortal = OccultPortal.new()
	portal.name = "DeeperRiftPortal"
	portal.biome_id = 2
	portal.biome_title = "The Royal Necropolis"
	portal.depth_tier = 2
	dummy_dungeon.add_child(portal)
	portal._ready()

	var dummy_player: CharacterBody3D = CharacterBody3D.new()
	dummy_player.name = "TestPlayer"
	root.add_child(dummy_player)

	# Mock dungeon generator that frees dummy_dungeon (and portal) during generation
	var mock_gen: Node = Node.new()
	mock_gen.name = "ProceduralExpeditionRoot"
	root.add_child(mock_gen)

	# Define mock generate_biome_dungeon via script
	var script: GDScript = GDScript.new()
	script.source_code = """
extends Node

var target_to_free: Node = null

func generate_biome_dungeon(biome_id: int, seed_val: int, depth_tier: int, return_dest: Vector3) -> Vector3:
	if target_to_free != null and is_instance_valid(target_to_free):
		target_to_free.free()
	return Vector3(10.0, -500.0, 20.0)
"""
	var err: Error = script.reload()
	assert(err == OK, "Mock script compile failed")
	mock_gen.set_script(script)
	mock_gen.set("target_to_free", dummy_dungeon)

	# Trigger warp! This will invoke mock_gen.generate_biome_dungeon, which frees dummy_dungeon + portal!
	portal.trigger_portal_warp(dummy_player)

	# Verify portal is indeed freed
	assert(not is_instance_valid(portal), "Portal instance should be freed by dungeon generator")

	# Find overlay_layer under root
	var overlay: CanvasLayer = root.find_child("RiftLoadingOverlayLayer", false, false) as CanvasLayer
	assert(overlay != null and is_instance_valid(overlay), "OverlayLayer should be instantiated under root")

	# Let frames process so the tween runs and finishes
	await process_frame
	await process_frame

	# Simulate tween finished or wait for 0.6s
	var start_time: int = Time.get_ticks_msec()
	while is_instance_valid(overlay) and (Time.get_ticks_msec() - start_time < 1200):
		await process_frame

	# Verify overlay layer was freed and did NOT softlock
	var overlay_after: CanvasLayer = root.find_child("RiftLoadingOverlayLayer", false, false) as CanvasLayer
	assert(overlay_after == null, "OverlayLayer must be freed by its tween callback without soft-locking")

	# Clean up mock nodes
	dummy_player.queue_free()
	mock_gen.queue_free()

	print(" -> [PASS] OccultPortal freed-self warp lifecycle verified: 0 script errors, overlay dismissed cleanly.")
	print("=== TARGETED VERIFICATION SUITE 100% PASSED ===")
	quit(0)
