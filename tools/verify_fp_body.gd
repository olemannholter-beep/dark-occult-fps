extends SceneTree


func _init() -> void:
	var player: FPSPlayer = FPSPlayer.new()
	var head_node: Node3D = Node3D.new()
	head_node.name = "Head"
	var cam_node: Camera3D = Camera3D.new()
	cam_node.name = "Camera3D"
	head_node.add_child(cam_node)
	player.add_child(head_node)
	var loadout: PlayerLoadoutManager = PlayerLoadoutManager.new()
	loadout.name = "PlayerLoadoutManager"
	player.add_child(loadout)
	root.add_child(player)
	player._fp_body._bind_loadout_manager()
	player._fp_body.refresh_armor_appearance()

	assert(player._fp_body != null and is_instance_valid(player._fp_body), "FPSPlayer._fp_body must be instantiated")
	assert(player._fp_body.torso_node != null and player._fp_body.torso_node.name == "TorsoNode", "TorsoNode must exist")
	assert(player._fp_body.left_leg_pivot != null and player._fp_body.right_leg_pivot != null, "LeftLegPivot and RightLegPivot must exist")
	assert(player._fp_body.left_boot_pivot != null and player._fp_body.right_boot_pivot != null, "BootPivot nodes must exist")
	assert(player._fp_body.head_shadow_mesh != null and player._fp_body.head_shadow_mesh.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY, "HeadShadowMesh must use SHADOW_CASTING_SETTING_SHADOWS_ONLY")

	# Test stride animation when moving and looking down
	player._fp_body.update_body_motion(0.05, Vector3(0.0, 0.0, -6.0), 0.0, -0.75, true, false)
	assert(absf(player._fp_body.left_leg_pivot.rotation.x) > 0.001, "LeftLegPivot must swing during walking stride")
	assert(player._fp_body.position.z < -0.14, "Looking down must slide body forward smoothly")

	# Test live equipment slot sync
	loadout.equip_armor_slot("FEET", 1)
	assert(player._fp_body.equipped_feet_set == 1, "FirstPersonBodyController must live-sync FEET slot to set 1")

	print("VERIFY_FP_BODY: ALL ASSERTIONS PASSED")
	quit(0)
