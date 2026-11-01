extends SceneTree


func _init() -> void:
	print("[Build] Constructing res://scenes/prefabs/player/fps_player.tscn...")
	_build_fps_player()
	print("[Build] Saved res://scenes/prefabs/player/fps_player.tscn successfully.")
	quit(0)


func _set_owner_recursive(node: Node, root: Node) -> void:
	if node != root:
		node.owner = root
		if not node.scene_file_path.is_empty():
			return
	for child: Node in node.get_children():
		_set_owner_recursive(child, root)


func _build_fps_player() -> void:
	var fps_script: Script = load("res://scripts/player/fps_controller.gd") as Script
	var vm_script: Script = load("res://scripts/player/fps_viewmodel_controller.gd") as Script
	var hud_script: Script = load("res://scripts/player/fps_hud.gd") as Script
	var loadout_script: Script = load("res://scripts/player/player_loadout_manager.gd") as Script
	var left_glb: PackedScene = load("res://assets/models/weapons/viewmodel_left_lantern.glb") as PackedScene
	var right_glb: PackedScene = load("res://assets/models/weapons/viewmodel_right_revolver.glb") as PackedScene

	var player: CharacterBody3D = CharacterBody3D.new()
	player.name = "FPSPlayer"
	player.floor_stop_on_slope = true
	player.floor_constant_speed = true
	player.floor_block_on_wall = true
	player.floor_max_angle = deg_to_rad(52.0)
	player.floor_snap_length = 0.45
	player.set_script(fps_script)

	# 1. Collision Shape
	var col: CollisionShape3D = CollisionShape3D.new()
	col.name = "CollisionShape3D"
	var cap: CapsuleShape3D = CapsuleShape3D.new()
	cap.radius = 0.4
	cap.height = 1.8
	col.shape = cap
	col.position = Vector3(0.0, 0.9, 0.0)
	player.add_child(col)

	# 2. Head & Camera3D
	var head: Node3D = Node3D.new()
	head.name = "Head"
	head.position = Vector3(0.0, 1.6, 0.0)
	player.add_child(head)

	var cam: Camera3D = Camera3D.new()
	cam.name = "Camera3D"
	cam.current = true
	cam.fov = 75.0
	cam.near = 0.03
	head.add_child(cam)

	var int_ray: RayCast3D = RayCast3D.new()
	int_ray.name = "InteractionRayCast3D"
	int_ray.target_position = Vector3(0.0, 0.0, -3.8)
	int_ray.collision_mask = 1
	int_ray.collide_with_areas = true
	int_ray.enabled = true
	cam.add_child(int_ray)

	# 3. ViewmodelRig attached to Camera3D
	var vm_rig: Node3D = Node3D.new()
	vm_rig.name = "ViewmodelRig"
	vm_rig.set_script(vm_script)
	cam.add_child(vm_rig)

	# Subtle shadowless ViewmodelRimLight so the 100+ rivets, armor plates, and revolver mechanisms are crisply lit
	var rim_light: OmniLight3D = OmniLight3D.new()
	rim_light.name = "ViewmodelRimLight"
	rim_light.position = Vector3(0.08, 0.14, -0.22)
	rim_light.light_color = Color(0.88, 0.84, 0.95, 1.0)
	rim_light.light_energy = 0.4
	rim_light.light_specular = 0.35
	rim_light.omni_range = 1.2
	rim_light.omni_attenuation = 1.2
	rim_light.shadow_enabled = false
	vm_rig.add_child(rim_light)

	# Wall avoidance RayCast3D (1.1m forward)
	var wall_ray: RayCast3D = RayCast3D.new()
	wall_ray.name = "WallRayCast"
	wall_ray.target_position = Vector3(0.0, 0.0, -1.1)
	wall_ray.enabled = true
	vm_rig.add_child(wall_ray)

	# Hitscan RayCast3D (100.0m forward)
	var hit_ray: RayCast3D = RayCast3D.new()
	hit_ray.name = "HitscanRayCast"
	hit_ray.target_position = Vector3(0.0, 0.0, -100.0)
	hit_ray.enabled = true
	vm_rig.add_child(hit_ray)

	# Left Hand Pivot (holding swinging occult lantern)
	var left_pivot: Node3D = Node3D.new()
	left_pivot.name = "LeftHandPivot"
	left_pivot.position = Vector3(-0.31, -0.28, -0.42)
	vm_rig.add_child(left_pivot)

	if left_glb != null:
		var left_inst: Node3D = left_glb.instantiate() as Node3D
		left_inst.name = "LeftLanternModel"
		left_pivot.add_child(left_inst)

	# Dynamic Shadow-Casting Lantern OmniLight3D (automatically reparented into LanternPendulum's flame core at runtime)
	var lantern_light: OmniLight3D = OmniLight3D.new()
	lantern_light.name = "LanternLight"
	lantern_light.position = Vector3(0.0, -0.156, 0.0)
	lantern_light.light_color = Color(1.0, 0.68, 0.32, 1.0)
	lantern_light.light_energy = 2.35
	lantern_light.light_volumetric_fog_energy = 3.8
	lantern_light.light_specular = 0.22
	lantern_light.shadow_enabled = true
	lantern_light.shadow_bias = 0.03
	lantern_light.shadow_normal_bias = 1.2
	lantern_light.shadow_blur = 1.5
	lantern_light.distance_fade_enabled = false
	lantern_light.omni_range = 26.0
	lantern_light.omni_attenuation = 0.82
	left_pivot.add_child(lantern_light)

	# Right Hand Pivot (holding mechanical occult revolver)
	var right_pivot: Node3D = Node3D.new()
	right_pivot.name = "RightHandPivot"
	right_pivot.position = Vector3(0.24, -0.21, -0.40)
	vm_rig.add_child(right_pivot)

	if right_glb != null:
		var right_inst: Node3D = right_glb.instantiate() as Node3D
		right_inst.name = "RightRevolverModel"
		right_pivot.add_child(right_inst)

	# Muzzle Flash OmniLight3D at barrel tip local to RightHandPivot
	var muzzle_light: OmniLight3D = OmniLight3D.new()
	muzzle_light.name = "MuzzleFlashLight"
	muzzle_light.position = Vector3(0.0, 0.06, -0.55)
	muzzle_light.light_color = Color(1.0, 0.65, 0.25, 1.0)
	muzzle_light.light_energy = 3.2
	muzzle_light.omni_range = 8.0
	muzzle_light.visible = false
	right_pivot.add_child(muzzle_light)

	# Crisp Muzzle Spark Streaks at barrel tip local to RightHandPivot
	var muzzle_parts: GPUParticles3D = GPUParticles3D.new()
	muzzle_parts.name = "MuzzleParticles"
	muzzle_parts.position = Vector3(0.0, 0.06, -0.55)
	muzzle_parts.emitting = false
	muzzle_parts.one_shot = true
	muzzle_parts.explosiveness = 0.95
	muzzle_parts.lifetime = 0.08
	muzzle_parts.local_coords = true
	muzzle_parts.amount = 14

	var p_mat: ParticleProcessMaterial = ParticleProcessMaterial.new()
	p_mat.direction = Vector3(0.0, 0.0, -1.0)
	p_mat.spread = 22.0
	p_mat.initial_velocity_min = 12.0
	p_mat.initial_velocity_max = 18.0
	p_mat.gravity = Vector3.ZERO
	p_mat.particle_flag_align_y = false
	p_mat.color = Color(1.0, 0.78, 0.38, 1.0)
	muzzle_parts.process_material = p_mat

	var spark_box: BoxMesh = BoxMesh.new()
	spark_box.size = Vector3(0.008, 0.008, 0.04)
	var q_mat: StandardMaterial3D = StandardMaterial3D.new()
	q_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	q_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	q_mat.albedo_color = Color(1.0, 0.82, 0.42, 1.0)
	spark_box.material = q_mat
	muzzle_parts.draw_pass_1 = spark_box
	right_pivot.add_child(muzzle_parts)

	# Assign exported references on ViewmodelRig
	var vm_ctrl: FPSViewmodelController = vm_rig as FPSViewmodelController
	vm_ctrl.left_hand_pivot = left_pivot
	vm_ctrl.right_hand_pivot = right_pivot
	vm_ctrl.lantern_light = lantern_light
	vm_ctrl.muzzle_flash_light = muzzle_light
	vm_ctrl.muzzle_particles = muzzle_parts
	vm_ctrl.wall_raycast = wall_ray
	vm_ctrl.hitscan_raycast = hit_ray

	# 4. Minimalist Occult HUD & PlayerLoadoutManager
	var hud: CanvasLayer = CanvasLayer.new()
	hud.name = "HUD"
	hud.set_script(hud_script)
	player.add_child(hud)
	var hud_ctrl: FPSHUD = hud as FPSHUD
	hud_ctrl.viewmodel_controller = vm_ctrl

	if loadout_script != null:
		var loadout_mgr: Node = Node.new()
		loadout_mgr.name = "PlayerLoadoutManager"
		loadout_mgr.set_script(loadout_script)
		player.add_child(loadout_mgr)
		loadout_mgr.set("player_controller", player)
		loadout_mgr.set("viewmodel_controller", vm_ctrl)
		loadout_mgr.set("hud", hud_ctrl)
		loadout_mgr.set("interaction_raycast", int_ray)

	if ResourceLoader.exists("res://scenes/prefabs/environment/dust_motes_particles.tscn"):
		var dust_scn: PackedScene = load("res://scenes/prefabs/environment/dust_motes_particles.tscn") as PackedScene
		if dust_scn != null:
			var dust_inst: Node3D = dust_scn.instantiate() as Node3D
			if dust_inst != null:
				dust_inst.name = "DustMotesParticles"
				cam.add_child(dust_inst)

	# Set ownership strictly respecting Rule 6.1 (stop at scene_file_path != "")
	_set_owner_recursive(player, player)

	var packed: PackedScene = PackedScene.new()
	var err: Error = packed.pack(player)
	if err != OK:
		push_error("Failed to pack fps_player.tscn")
		return
	ResourceSaver.save(packed, "res://scenes/prefabs/player/fps_player.tscn")
	player.free()
