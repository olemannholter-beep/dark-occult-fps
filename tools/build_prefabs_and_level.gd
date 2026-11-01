extends SceneTree


func _init() -> void:
	print("[Build] Starting prefab and town_overworld.tscn generation...")
	DirAccess.make_dir_recursive_absolute("res://scenes/prefabs/environment")
	DirAccess.make_dir_recursive_absolute("res://scenes/prefabs/architecture")
	DirAccess.make_dir_recursive_absolute("res://scenes/prefabs/hub")
	DirAccess.make_dir_recursive_absolute("res://scenes/prefabs/props")
	DirAccess.make_dir_recursive_absolute("res://scenes/prefabs/enemies")
	DirAccess.make_dir_recursive_absolute("res://scenes/prefabs/ossuary_variety")
	DirAccess.make_dir_recursive_absolute("res://scenes/prefabs/dungeon")
	DirAccess.make_dir_recursive_absolute("res://scenes/prefabs/armor")
	DirAccess.make_dir_recursive_absolute("res://scenes/levels")

	_build_all_prefabs()
	_build_town_overworld()
	print("[Build] Completed all prefabs and town_overworld.tscn successfully.")
	quit(0)


func _collect_meshes(node: Node, out_meshes: Array[MeshInstance3D]) -> void:
	if node is MeshInstance3D:
		out_meshes.append(node as MeshInstance3D)
	for child: Node in node.get_children():
		_collect_meshes(child, out_meshes)


func _set_owner_recursive(node: Node, root: Node) -> void:
	if node != root:
		node.owner = root
		if not node.scene_file_path.is_empty():
			return
		# Never serialize HUD's procedural runtime children into fps_player.tscn
		if node.name == "HUD":
			return
	for child: Node in node.get_children():
		_set_owner_recursive(child, root)


func _save_packed_scene(root: Node3D, save_path: String) -> void:
	var packed: PackedScene = PackedScene.new()
	var err: Error = packed.pack(root)
	if err != OK:
		push_error("Failed to pack scene: " + save_path)
		return
	var save_err: Error = ResourceSaver.save(packed, save_path)
	if save_err != OK:
		push_error("Failed to save scene: " + save_path)
	else:
		print("[Scene] Saved " + save_path)
	root.free()


func _extract_relative_transform(child: Node3D, ancestor: Node3D) -> Transform3D:
	var xform: Transform3D = Transform3D.IDENTITY
	var curr: Node = child
	while curr != null and curr != ancestor:
		if curr is Node3D:
			xform = (curr as Node3D).transform * xform
		curr = curr.get_parent()
	return xform


func _configure_omni_distance_fade(light: OmniLight3D, enable_shadows: bool) -> void:
	light.shadow_enabled = enable_shadows
	light.distance_fade_enabled = true
	light.distance_fade_begin = 16.0
	light.distance_fade_shadow = 12.0
	light.distance_fade_length = 6.0


func _build_simplified_terrain_shape() -> ConcavePolygonShape3D:
	var step: float = 2.5
	var grid_steps: int = 48
	var half_span: float = 60.0
	var faces: PackedVector3Array = PackedVector3Array()

	for ix: int in range(grid_steps):
		var x0: float = -half_span + float(ix) * step
		var x1: float = x0 + step
		for iz: int in range(grid_steps):
			var z0: float = -half_span + float(iz) * step
			var z1: float = z0 + step
			var cx: float = (x0 + x1) * 0.5
			var cz: float = (z0 + z1) * 0.5
			# Keep expanded Cruciform Cathedral & basement stairwell cutout open (X in [-13.8, 13.8], Z in [-57.8, -22.0])
			if absf(cx) < 14.0 and cz >= -58.0 and cz <= -21.8:
				continue

			var v00: Vector3 = Vector3(x0, _get_terrain_height(x0, z0), z0)
			var v10: Vector3 = Vector3(x1, _get_terrain_height(x1, z0), z0)
			var v01: Vector3 = Vector3(x0, _get_terrain_height(x0, z1), z1)
			var v11: Vector3 = Vector3(x1, _get_terrain_height(x1, z1), z1)

			faces.append(v00)
			faces.append(v10)
			faces.append(v11)

			faces.append(v00)
			faces.append(v11)
			faces.append(v01)

	var shape: ConcavePolygonShape3D = ConcavePolygonShape3D.new()
	shape.set_faces(faces)
	shape.backface_collision = true
	return shape


func _create_trimesh_prefab(
	glb_path: String,
	prefab_path: String,
	root_name: String,
	double_sided_shadows: bool,
	lod_distance: float,
	extra_stairs_ramp: bool = false,
	extra_plinth_ramp: bool = false,
	extra_altar_light: bool = false,
	surface_type: String = "stone",
	custom_light_color: Color = Color(0.0, 0.0, 0.0, 0.0),
	custom_light_pos: Vector3 = Vector3.ZERO,
	custom_light_energy: float = 1.4,
	custom_light_range: float = 11.0,
	collision_mode: String = "box_prop"
) -> void:
	var glb_scene: PackedScene = load(glb_path) as PackedScene
	if glb_scene == null:
		push_error("Could not load GLB: " + glb_path)
		return

	var root: Node3D = Node3D.new()
	root.name = root_name
	if not surface_type.is_empty():
		root.set_meta("surface_type", surface_type)

	var model_inst: Node3D = glb_scene.instantiate() as Node3D
	var meshes: Array[MeshInstance3D] = []
	_collect_meshes(model_inst, meshes)

	var static_body: StaticBody3D = null
	if collision_mode != "none":
		static_body = StaticBody3D.new()
		static_body.name = "StaticBody3D"
		static_body.collision_layer = 1
		static_body.collision_mask = 1
		if not surface_type.is_empty():
			static_body.set_meta("surface_type", surface_type)
		root.add_child(static_body)

	var is_no_shadow_mesh: bool = (
		root_name == "CryptContainmentHull"
		or root_name == "FloorStone4x4"
		or root_name == "TerrainTown"
		or root_name == "ClutterRubbleBonesPile"
		or root_name == "ClutterMeltedCandleCluster"
	)
	var is_clutter_fade: bool = (
		root_name.begins_with("Clutter")
	)

	var combined_aabb: AABB = AABB()
	var has_aabb: bool = false

	for old_mi: MeshInstance3D in meshes:
		var mi: MeshInstance3D = MeshInstance3D.new()
		mi.name = old_mi.name
		mi.mesh = old_mi.mesh
		mi.transform = _extract_relative_transform(old_mi, model_inst)

		if is_no_shadow_mesh:
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		elif double_sided_shadows:
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED
		else:
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON

		mi.visibility_range_end = lod_distance
		if is_clutter_fade:
			mi.visibility_range_end = 34.0
			mi.visibility_range_end_margin = 3.5
			mi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
		elif lod_distance > 0.0:
			mi.visibility_range_end_margin = 4.0
			mi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
		else:
			mi.visibility_range_end_margin = 0.0
			mi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED

		if mi.mesh != null:
			var m_aabb: AABB = mi.transform * mi.mesh.get_aabb()
			if not has_aabb:
				combined_aabb = m_aabb
				has_aabb = true
			else:
				combined_aabb = combined_aabb.merge(m_aabb)

			for s_idx: int in range(mi.mesh.get_surface_count()):
				var orig_mat: Material = mi.mesh.surface_get_material(s_idx)
				var mat_name: String = orig_mat.resource_name if orig_mat != null else ""
				if mat_name.is_empty():
					mat_name = mi.name
				var grim_mat: Material = GrimdarkMaterialLibrary.get_material_for_name(mat_name)
				if grim_mat != null:
					mi.set_surface_override_material(s_idx, grim_mat)
				elif orig_mat is StandardMaterial3D:
					var em_mat: StandardMaterial3D = (orig_mat as StandardMaterial3D).duplicate() as StandardMaterial3D
					em_mat.vertex_color_use_as_albedo = true
					em_mat.normal_enabled = false
					var lower_mname: String = mat_name.to_lower()
					if lower_mname.contains("runes") or lower_mname.contains("flame") or lower_mname.contains("candle"):
						em_mat.emission_enabled = true
						em_mat.emission_energy_multiplier = 3.5
					mi.set_surface_override_material(s_idx, em_mat)

		root.add_child(mi)

	model_inst.free()

	# Phase 2: Fast Primitive BoxShape3D / CylinderShape3D Colliders (Zero 30,000-triangle Trimeshes!)
	if static_body != null and not extra_stairs_ramp:
		if collision_mode == "box_floor_4x4":
			var fl_col: CollisionShape3D = CollisionShape3D.new()
			fl_col.name = "FloorBoxCollider"
			var fl_box: BoxShape3D = BoxShape3D.new()
			fl_box.size = Vector3(4.0, 0.36, 4.0)
			fl_col.shape = fl_box
			fl_col.position = Vector3(0.0, -0.18, 0.0)
			static_body.add_child(fl_col)
		elif collision_mode == "box_ceiling_4x4":
			var cl_col: CollisionShape3D = CollisionShape3D.new()
			cl_col.name = "CeilingBoxCollider"
			var cl_box: BoxShape3D = BoxShape3D.new()
			cl_box.size = Vector3(4.20, 0.45, 4.20)
			cl_col.shape = cl_box
			cl_col.position = Vector3(0.0, 0.22, 0.0)
			static_body.add_child(cl_col)
		elif collision_mode == "box_wall_4x4":
			var wl_col: CollisionShape3D = CollisionShape3D.new()
			wl_col.name = "WallBoxCollider"
			var wl_box: BoxShape3D = BoxShape3D.new()
			wl_box.size = Vector3(4.20, 4.05, 0.48)
			wl_col.shape = wl_box
			wl_col.position = Vector3(0.0, 2.025, 0.0)
			static_body.add_child(wl_col)
		elif collision_mode == "box_wall_door_4x4":
			# Compound 3-box collider leaving the central 2.4m x 3.4m arch doorway 100% open to walk through
			for side_s: float in [-1.0, 1.0]:
				var pier_col: CollisionShape3D = CollisionShape3D.new()
				pier_col.name = "DoorPierCollider_" + ("L" if side_s < 0.0 else "R")
				var pier_box: BoxShape3D = BoxShape3D.new()
				pier_box.size = Vector3(0.90, 4.05, 0.48)
				pier_col.shape = pier_box
				pier_col.position = Vector3(side_s * 1.65, 2.025, 0.0)
				static_body.add_child(pier_col)
			var lintel_col: CollisionShape3D = CollisionShape3D.new()
			lintel_col.name = "DoorLintelCollider"
			var lintel_box: BoxShape3D = BoxShape3D.new()
			lintel_box.size = Vector3(2.40, 0.65, 0.48)
			lintel_col.shape = lintel_box
			lintel_col.position = Vector3(0.0, 3.725, 0.0)
			static_body.add_child(lintel_col)
		elif collision_mode == "cyl_pillar":
			var pil_col: CollisionShape3D = CollisionShape3D.new()
			pil_col.name = "PillarCylinderCollider"
			var pil_cyl: CylinderShape3D = CylinderShape3D.new()
			pil_cyl.radius = 0.45
			pil_cyl.height = 4.0
			pil_col.shape = pil_cyl
			pil_col.position = Vector3(0.0, 2.0, 0.0)
			static_body.add_child(pil_col)
		elif collision_mode == "cyl_tree":
			var tr_col: CollisionShape3D = CollisionShape3D.new()
			tr_col.name = "TreeTrunkCollider"
			var tr_cyl: CylinderShape3D = CylinderShape3D.new()
			tr_cyl.radius = 0.45
			tr_cyl.height = 5.5
			tr_col.shape = tr_cyl
			tr_col.position = Vector3(0.0, 2.75, 0.0)
			static_body.add_child(tr_col)
		elif collision_mode == "box_house":
			var hs_col: CollisionShape3D = CollisionShape3D.new()
			hs_col.name = "HouseBoxCollider"
			var hs_box: BoxShape3D = BoxShape3D.new()
			hs_box.size = Vector3(8.2, 8.5, 10.2)
			hs_col.shape = hs_box
			hs_col.position = Vector3(0.0, 3.0, 0.0)
			static_body.add_child(hs_col)
		elif collision_mode == "box_church_plinth":
			# Forecourt foundation plinth slab under Z in [-22, -12] (local Z in [-2, +8] relative to plinth at Z = -20)
			var s_slab: CollisionShape3D = CollisionShape3D.new()
			s_slab.name = "PlinthForecourtSlab"
			var s_box: BoxShape3D = BoxShape3D.new()
			s_box.size = Vector3(12.2, 3.0, 10.0)
			s_slab.shape = s_box
			s_slab.position = Vector3(0.0, -1.5, 3.2)
			static_body.add_child(s_slab)
		elif collision_mode == "box_crates":
			var cr_col: CollisionShape3D = CollisionShape3D.new()
			cr_col.name = "CratesBoxCollider"
			var cr_box: BoxShape3D = BoxShape3D.new()
			cr_box.size = Vector3(1.48, 0.96, 1.10)
			cr_col.shape = cr_box
			cr_col.position = Vector3(-0.08, 0.48, 0.04)
			static_body.add_child(cr_col)
		elif collision_mode == "box_bridge_4x4":
			var br_deck: CollisionShape3D = CollisionShape3D.new()
			br_deck.name = "BridgeDeckCollider"
			var br_box: BoxShape3D = BoxShape3D.new()
			br_box.size = Vector3(2.20, 0.36, 4.04)
			br_deck.shape = br_box
			br_deck.position = Vector3(0.0, -0.18, 0.0)
			static_body.add_child(br_deck)
			for side_s: float in [-1.0, 1.0]:
				var curb_col: CollisionShape3D = CollisionShape3D.new()
				curb_col.name = "BridgeCurbCollider_" + ("L" if side_s < 0.0 else "R")
				var curb_box: BoxShape3D = BoxShape3D.new()
				curb_box.size = Vector3(0.24, 0.85, 4.00)
				curb_col.shape = curb_box
				curb_col.position = Vector3(side_s * 1.02, 0.42, 0.0)
				static_body.add_child(curb_col)
		elif collision_mode == "box_railing_4m":
			var rl_col: CollisionShape3D = CollisionShape3D.new()
			rl_col.name = "RailingBoxCollider"
			var rl_box: BoxShape3D = BoxShape3D.new()
			rl_box.size = Vector3(4.02, 1.15, 0.36)
			rl_col.shape = rl_box
			rl_col.position = Vector3(0.0, 0.575, 0.0)
			static_body.add_child(rl_col)
		elif collision_mode == "box_buttress_arch_4x4":
			for side_s: float in [-1.0, 1.0]:
				var bp_col: CollisionShape3D = CollisionShape3D.new()
				bp_col.name = "ButtressPierCollider_" + ("L" if side_s < 0.0 else "R")
				var bp_box: BoxShape3D = BoxShape3D.new()
				bp_box.size = Vector3(0.76, 4.00, 0.84)
				bp_col.shape = bp_box
				bp_col.position = Vector3(side_s * 1.62, 2.0, 0.0)
				static_body.add_child(bp_col)
			var bl_col: CollisionShape3D = CollisionShape3D.new()
			bl_col.name = "ButtressArchLintelCollider"
			var bl_box: BoxShape3D = BoxShape3D.new()
			bl_box.size = Vector3(2.50, 0.65, 0.84)
			bl_col.shape = bl_box
			bl_col.position = Vector3(0.0, 3.675, 0.0)
			static_body.add_child(bl_col)
		elif collision_mode == "terrain_simplified":
			var ter_col: CollisionShape3D = CollisionShape3D.new()
			ter_col.name = "SimplifiedTerrainCollider"
			ter_col.shape = _build_simplified_terrain_shape()
			static_body.add_child(ter_col)
		elif has_aabb:
			var pr_col: CollisionShape3D = CollisionShape3D.new()
			pr_col.name = "PrimitiveBoxCollider"
			var pr_box: BoxShape3D = BoxShape3D.new()
			pr_box.size = Vector3(
				maxf(0.25, combined_aabb.size.x),
				maxf(0.25, combined_aabb.size.y),
				maxf(0.25, combined_aabb.size.z)
			)
			pr_col.shape = pr_box
			pr_col.position = combined_aabb.get_center()
			static_body.add_child(pr_col)

	# For stairs_stone_4x4, use a single ultra-smooth sloped ConvexPolygonShape3D ramp plane + flat top landing lip
	# (spans local Y = -4.0 at Z = -2.0 up to local Y = +0.02 at Z = +2.0, which is 4.02m rise over the 4.0m run,
	#  plus a 0.38m top landing lip overlapping the upper floor tile edge with ZERO vertical step seam!)
	if extra_stairs_ramp and static_body != null:
		var ramp_col: CollisionShape3D = CollisionShape3D.new()
		ramp_col.name = "StairRampCollider"
		var ramp_prism: ConvexPolygonShape3D = ConvexPolygonShape3D.new()
		var hw: float = 1.88
		var pts: PackedVector3Array = PackedVector3Array([
			# Bottom landing lip flush with lower floor (Y = -4.00)
			Vector3(-hw, -4.00, -2.30), Vector3(hw, -4.00, -2.30),
			Vector3(-hw, -4.32, -2.30), Vector3(hw, -4.32, -2.30),
			Vector3(-hw, -4.00, -1.96), Vector3(hw, -4.00, -1.96),
			Vector3(-hw, -4.35, -1.96), Vector3(hw, -4.35, -1.96),
			# Top of sloped ramp reaching Y = +0.02m (4.02m above bottom floor) at top edge
			Vector3(-hw, 0.02, 1.94), Vector3(hw, 0.02, 1.94),
			Vector3(-hw, -0.36, 1.94), Vector3(hw, -0.36, 1.94),
			# Flat 0.38m top landing lip overlapping upper floor tile edge (Z = +1.94 .. +2.35)
			Vector3(-hw, 0.015, 2.35), Vector3(hw, 0.015, 2.35),
			Vector3(-hw, -0.36, 2.35), Vector3(hw, -0.36, 2.35),
			# Smooth feather edge onto upper floor at Z = +2.48
			Vector3(-hw, 0.00, 2.48), Vector3(hw, 0.00, 2.48),
			Vector3(-hw, -0.36, 2.48), Vector3(hw, -0.36, 2.48)
		])
		ramp_prism.points = pts
		ramp_col.shape = ramp_prism
		static_body.add_child(ramp_col)

		var top_lip_col: CollisionShape3D = CollisionShape3D.new()
		top_lip_col.name = "StairTopLandingLip"
		var top_lip_box: BoxShape3D = BoxShape3D.new()
		top_lip_box.size = Vector3(3.76, 0.34, 0.42)
		top_lip_col.shape = top_lip_box
		top_lip_col.position = Vector3(0.0, -0.155, 2.15)
		static_body.add_child(top_lip_col)

	# For church_foundation_plinth, add a smooth sloped ramp over the front steps so player glides up effortlessly
	if extra_plinth_ramp and static_body != null:
		var front_ramp: CollisionShape3D = CollisionShape3D.new()
		front_ramp.name = "FrontStepsSmoothRamp"
		var f_box: BoxShape3D = BoxShape3D.new()
		f_box.size = Vector3(4.20, 0.30, 2.35)
		front_ramp.shape = f_box
		front_ramp.position = Vector3(0.0, -0.51, 9.58)
		front_ramp.rotation.x = deg_to_rad(23.2)
		static_body.add_child(front_ramp)

	# For crypt_altar, add an eerie occult crimson-amber OmniLight3D above the sacrificial basin
	if extra_altar_light:
		var flicker_script: Script = load("res://scripts/environment/torch_flicker.gd") as Script
		var altar_light: OmniLight3D = OmniLight3D.new()
		altar_light.name = "AltarOccultLight"
		altar_light.position = Vector3(0.0, 1.65, 0.0)
		altar_light.light_color = Color(1.0, 0.28, 0.12, 1.0)
		altar_light.light_energy = 1.35
		altar_light.light_volumetric_fog_energy = 3.8
		altar_light.omni_range = 10.0
		altar_light.omni_attenuation = 1.3
		altar_light.light_specular = 0.20
		_configure_omni_distance_fade(altar_light, false)
		if flicker_script != null:
			altar_light.set_script(flicker_script)
		root.add_child(altar_light)

	if custom_light_color.a > 0.01:
		var c_light: OmniLight3D = OmniLight3D.new()
		c_light.name = "CenterpieceGlowLight"
		c_light.position = custom_light_pos
		c_light.light_color = custom_light_color
		c_light.light_energy = custom_light_energy
		c_light.light_volumetric_fog_energy = 4.0
		c_light.omni_range = custom_light_range
		c_light.omni_attenuation = 1.25
		c_light.light_specular = 0.22
		_configure_omni_distance_fade(c_light, false)
		root.add_child(c_light)

	_set_owner_recursive(root, root)
	_save_packed_scene(root, prefab_path)


func _create_wall_lantern_prefab() -> void:
	var glb_scene: PackedScene = load("res://assets/models/church_kit/wall_lantern_sconce.glb") as PackedScene
	if glb_scene == null:
		push_error("Could not load GLB: wall_lantern_sconce.glb")
		return

	var root: Node3D = Node3D.new()
	root.name = "WallLanternSconce"

	var model_inst: Node3D = glb_scene.instantiate() as Node3D
	var meshes: Array[MeshInstance3D] = []
	_collect_meshes(model_inst, meshes)

	for old_mi: MeshInstance3D in meshes:
		var mi: MeshInstance3D = MeshInstance3D.new()
		mi.name = old_mi.name
		mi.mesh = old_mi.mesh
		mi.transform = _extract_relative_transform(old_mi, model_inst)

		var mname: String = mi.name.to_lower()
		var is_non_shadow: bool = mname.contains("glass") or mname.contains("flame") or mname.contains("wax")
		if is_non_shadow:
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		else:
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED

		if mi.mesh != null:
			for s_idx: int in range(mi.mesh.get_surface_count()):
				var orig_mat: Material = mi.mesh.surface_get_material(s_idx)
				var mat_name: String = orig_mat.resource_name if orig_mat != null else ""
				if mat_name.to_lower().contains("glass") or mat_name.to_lower().contains("flame"):
					mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				if mat_name.is_empty():
					mat_name = mi.name

				# Clean warm amber emission energy = 1.6
				if (mname.contains("flame") or mat_name.to_lower().contains("flame")) and orig_mat is StandardMaterial3D:
					var em_mat: StandardMaterial3D = (orig_mat as StandardMaterial3D).duplicate() as StandardMaterial3D
					em_mat.emission_enabled = true
					em_mat.emission_energy_multiplier = 1.6
					mi.set_surface_override_material(s_idx, em_mat)
				else:
					var grim_mat: Material = GrimdarkMaterialLibrary.get_material_for_name(mat_name)
					if grim_mat != null:
						mi.set_surface_override_material(s_idx, grim_mat)

		mi.visibility_range_end = 34.0
		mi.visibility_range_end_margin = 3.5
		mi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
		root.add_child(mi)

	model_inst.free()

	var flicker_script: Script = load("res://scripts/environment/torch_flicker.gd") as Script
	var light: OmniLight3D = OmniLight3D.new()
	light.name = "LanternOmniLight"
	light.position = Vector3(0.0, -0.15, -0.38)
	light.light_color = Color(1.0, 0.68, 0.32, 1.0)
	light.light_energy = 1.35
	light.light_volumetric_fog_energy = 3.8
	light.omni_range = 12.0
	light.omni_attenuation = 1.3
	light.light_specular = 0.20
	_configure_omni_distance_fade(light, false)
	if flicker_script != null:
		light.set_script(flicker_script)
	root.add_child(light)

	var fire_wav: AudioStreamWAV = load("res://assets/audio/sfx/torch_fire_loop.wav") as AudioStreamWAV
	if fire_wav != null:
		fire_wav.loop_mode = AudioStreamWAV.LOOP_FORWARD
		fire_wav.loop_begin = 0
		fire_wav.loop_end = int(fire_wav.data.size() / 2)
		var crackle: AudioStreamPlayer3D = AudioStreamPlayer3D.new()
		crackle.name = "FireCrackle3D"
		crackle.position = Vector3(0.0, -0.15, -0.38)
		crackle.stream = fire_wav
		crackle.unit_size = 2.5
		crackle.max_distance = 10.0
		crackle.max_polyphony = 2
		crackle.volume_db = -10.0
		crackle.autoplay = true
		root.add_child(crackle)

	_set_owner_recursive(root, root)
	_save_packed_scene(root, "res://scenes/prefabs/architecture/wall_lantern_sconce.tscn")


func _create_standing_brazier_prefab() -> void:
	var glb_scene: PackedScene = load("res://assets/models/church_kit/standing_iron_brazier.glb") as PackedScene
	if glb_scene == null:
		push_error("Could not load GLB: standing_iron_brazier.glb")
		return

	var root: Node3D = Node3D.new()
	root.name = "StandingIronBrazier"

	var model_inst: Node3D = glb_scene.instantiate() as Node3D
	var meshes: Array[MeshInstance3D] = []
	_collect_meshes(model_inst, meshes)

	for old_mi: MeshInstance3D in meshes:
		var mi: MeshInstance3D = MeshInstance3D.new()
		mi.name = old_mi.name
		mi.mesh = old_mi.mesh
		mi.transform = _extract_relative_transform(old_mi, model_inst)

		var mname: String = mi.name.to_lower()
		var is_non_shadow: bool = mname.contains("glass") or mname.contains("flame") or mname.contains("wax") or mname.contains("ember")
		if is_non_shadow:
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		else:
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED

		if mi.mesh != null:
			for s_idx: int in range(mi.mesh.get_surface_count()):
				var orig_mat: Material = mi.mesh.surface_get_material(s_idx)
				var mat_name: String = orig_mat.resource_name if orig_mat != null else ""
				if mat_name.to_lower().contains("glass") or mat_name.to_lower().contains("flame") or mat_name.to_lower().contains("ember"):
					mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				if mat_name.is_empty():
					mat_name = mi.name

				# Clean warm embers emission energy = 3.5
				if (mname.contains("ember") or mat_name.to_lower().contains("ember")) and orig_mat is StandardMaterial3D:
					var em_mat: StandardMaterial3D = (orig_mat as StandardMaterial3D).duplicate() as StandardMaterial3D
					em_mat.emission_enabled = true
					em_mat.emission_energy_multiplier = 3.5
					mi.set_surface_override_material(s_idx, em_mat)
				else:
					var grim_mat: Material = GrimdarkMaterialLibrary.get_material_for_name(mat_name)
					if grim_mat != null:
						mi.set_surface_override_material(s_idx, grim_mat)

		mi.visibility_range_end = 34.0
		mi.visibility_range_end_margin = 3.5
		mi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
		root.add_child(mi)

	model_inst.free()

	var static_body: StaticBody3D = StaticBody3D.new()
	static_body.name = "StaticBody3D"
	var col: CollisionShape3D = CollisionShape3D.new()
	col.name = "BrazierCollider"
	var cyl: CylinderShape3D = CylinderShape3D.new()
	cyl.radius = 0.42
	cyl.height = 1.35
	col.shape = cyl
	col.position = Vector3(0.0, 0.675, 0.0)
	static_body.add_child(col)
	root.add_child(static_body)

	var flicker_script: Script = load("res://scripts/environment/torch_flicker.gd") as Script
	var light: OmniLight3D = OmniLight3D.new()
	light.name = "BrazierOmniLight"
	light.position = Vector3(0.0, 1.25, 0.0)
	light.light_color = Color(1.0, 0.52, 0.18, 1.0)
	light.light_energy = 1.35
	light.light_volumetric_fog_energy = 3.8
	light.omni_range = 12.0
	light.omni_attenuation = 1.3
	light.light_specular = 0.20
	_configure_omni_distance_fade(light, false)
	if flicker_script != null:
		light.set_script(flicker_script)
	root.add_child(light)

	var fire_wav: AudioStreamWAV = load("res://assets/audio/sfx/torch_fire_loop.wav") as AudioStreamWAV
	if fire_wav != null:
		fire_wav.loop_mode = AudioStreamWAV.LOOP_FORWARD
		fire_wav.loop_begin = 0
		fire_wav.loop_end = int(fire_wav.data.size() / 2)
		var crackle: AudioStreamPlayer3D = AudioStreamPlayer3D.new()
		crackle.name = "FireCrackle3D"
		crackle.position = Vector3(0.0, 1.25, 0.0)
		crackle.stream = fire_wav
		crackle.unit_size = 2.5
		crackle.max_distance = 10.0
		crackle.max_polyphony = 2
		crackle.volume_db = -10.0
		crackle.autoplay = true
		root.add_child(crackle)

	_set_owner_recursive(root, root)
	_save_packed_scene(root, "res://scenes/prefabs/architecture/standing_iron_brazier.tscn")


func _create_dust_motes_prefab() -> void:
	var particles: GPUParticles3D = GPUParticles3D.new()
	particles.name = "DustMotesParticles"
	particles.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	particles.amount = 140
	particles.lifetime = 9.0
	particles.preprocess = 2.0
	particles.visibility_aabb = AABB(Vector3(-7.0, -2.5, -7.0), Vector3(14.0, 5.0, 14.0))

	var p_mat: ParticleProcessMaterial = ParticleProcessMaterial.new()
	p_mat.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	p_mat.emission_box_extents = Vector3(7.0, 2.5, 7.0)
	p_mat.direction = Vector3(0.2, -1.0, 0.15)
	p_mat.spread = 65.0
	p_mat.initial_velocity_min = 0.04
	p_mat.initial_velocity_max = 0.14
	p_mat.gravity = Vector3(0.0, -0.02, 0.0)
	p_mat.scale_min = 0.6
	p_mat.scale_max = 1.4
	p_mat.color = Color(0.95, 0.86, 0.68, 0.42)
	particles.process_material = p_mat

	var s_mat: StandardMaterial3D = StandardMaterial3D.new()
	s_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	s_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	s_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	s_mat.vertex_color_use_as_albedo = true
	s_mat.albedo_color = Color(0.95, 0.86, 0.68, 0.38)
	s_mat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	s_mat.billboard_keep_scale = true

	var quad: QuadMesh = QuadMesh.new()
	quad.size = Vector2(0.022, 0.022)
	quad.material = s_mat
	particles.draw_pass_1 = quad

	_save_packed_scene(particles, "res://scenes/prefabs/architecture/dust_motes_particles.tscn")


func _create_target_dummy_plaque_prefab() -> void:
	var glb_scene: PackedScene = load("res://assets/models/church_kit/crypt_ritual_obelisk.glb") as PackedScene
	if glb_scene == null:
		push_error("Could not load GLB for TargetDummyPlaque: crypt_ritual_obelisk.glb")
		return

	var plaque_script: Script = load("res://scripts/interaction/target_dummy_plaque.gd") as Script
	var root: StaticBody3D = StaticBody3D.new()
	root.name = "TargetDummyPlaque"
	root.collision_layer = 1
	root.collision_mask = 1
	root.set_meta("surface_type", "stone")
	if plaque_script != null:
		root.set_script(plaque_script)

	var model_inst: Node3D = glb_scene.instantiate() as Node3D
	var meshes: Array[MeshInstance3D] = []
	_collect_meshes(model_inst, meshes)

	for old_mi: MeshInstance3D in meshes:
		var mi: MeshInstance3D = MeshInstance3D.new()
		mi.name = old_mi.name
		mi.mesh = old_mi.mesh
		var xform: Transform3D = _extract_relative_transform(old_mi, model_inst)
		xform.basis = xform.basis.scaled(Vector3(0.58, 0.58, 0.58))
		xform.origin *= 0.58
		mi.transform = xform
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		mi.visibility_range_end = 38.0
		mi.visibility_range_end_margin = 4.0

		if mi.mesh != null:
			for s_idx: int in range(mi.mesh.get_surface_count()):
				var orig_mat: Material = mi.mesh.surface_get_material(s_idx)
				var mat_name: String = orig_mat.resource_name if orig_mat != null else ""
				if mat_name.is_empty():
					mat_name = mi.name
				var grim_mat: Material = GrimdarkMaterialLibrary.get_material_for_name(mat_name)
				if grim_mat != null:
					mi.set_surface_override_material(s_idx, grim_mat)
				elif orig_mat is StandardMaterial3D:
					var em_mat: StandardMaterial3D = (orig_mat as StandardMaterial3D).duplicate() as StandardMaterial3D
					em_mat.vertex_color_use_as_albedo = true
					em_mat.normal_enabled = false
					mi.set_surface_override_material(s_idx, em_mat)

		root.add_child(mi)

	model_inst.free()

	var box_col: CollisionShape3D = CollisionShape3D.new()
	box_col.name = "PlaqueBoxCollider"
	var b_shape: BoxShape3D = BoxShape3D.new()
	b_shape.size = Vector3(1.10, 2.35, 1.10)
	box_col.shape = b_shape
	box_col.position = Vector3(0.0, 1.175, 0.0)
	root.add_child(box_col)

	_set_owner_recursive(root, root)
	_save_packed_scene(root, "res://scenes/prefabs/hub/target_dummy_plaque.tscn")


func _sync_fps_player_lantern_prefab() -> void:
	var p_scn: PackedScene = load("res://scenes/prefabs/player/fps_player.tscn") as PackedScene
	if p_scn == null:
		return
	var player_inst: Node3D = p_scn.instantiate() as Node3D
	if player_inst == null:
		return
	player_inst.scene_file_path = ""
	var seen_fp_body: bool = false
	for ch: Node in player_inst.get_children():
		if ch.name.begins_with("FirstPersonBodyController"):
			if seen_fp_body:
				player_inst.remove_child(ch)
				ch.free()
			else:
				seen_fp_body = true
	if player_inst is CharacterBody3D:
		var cb: CharacterBody3D = player_inst as CharacterBody3D
		cb.collision_layer = 1 | 2
		cb.collision_mask = 1
		cb.floor_max_angle = deg_to_rad(52.0)
		cb.floor_snap_length = 0.35
	var hs_ray: RayCast3D = player_inst.find_child("HitscanRayCast", true, false) as RayCast3D
	if hs_ray != null:
		hs_ray.collision_mask = 1 | 4
	var int_ray: RayCast3D = player_inst.find_child("InteractionRayCast3D", true, false) as RayCast3D
	if int_ray != null:
		int_ray.target_position = Vector3(0.0, 0.0, -3.8)
		int_ray.collide_with_areas = true
	var hud_node: Node = player_inst.find_child("HUD", true, false)
	if hud_node != null:
		for child: Node in hud_node.get_children():
			hud_node.remove_child(child)
			child.free()
	var vm_rig: Node3D = player_inst.find_child("ViewmodelRig", true, false) as Node3D
	if vm_rig != null:
		vm_rig.set("lantern_base_range", 26.0)
		vm_rig.set("lantern_raised_range", 34.0)
		vm_rig.set("lantern_base_energy", 2.35)
		vm_rig.set("lantern_attenuation", 0.82)
	var l_light: OmniLight3D = player_inst.find_child("LanternLight", true, false) as OmniLight3D
	if l_light != null:
		l_light.light_energy = 2.35
		l_light.omni_range = 26.0
		l_light.omni_attenuation = 0.82
		l_light.distance_fade_enabled = false
		l_light.shadow_enabled = true
	_set_owner_recursive(player_inst, player_inst)
	_save_packed_scene(player_inst, "res://scenes/prefabs/player/fps_player.tscn")


func _create_armor_gauntlet_prefabs() -> void:
	var gauntlets: Array[Dictionary] = [
		{
			"glb": "res://assets/models/armor/gauntlet_01_leather_stalker.glb",
			"tscn": "res://scenes/prefabs/armor/gauntlet_01_leather_stalker.tscn",
			"name": "Gauntlet01LeatherStalker"
		},
		{
			"glb": "res://assets/models/armor/gauntlet_02_inquisitor_brigandine.glb",
			"tscn": "res://scenes/prefabs/armor/gauntlet_02_inquisitor_brigandine.tscn",
			"name": "Gauntlet02InquisitorBrigandine"
		},
		{
			"glb": "res://assets/models/armor/gauntlet_03_juggernaut_plate.glb",
			"tscn": "res://scenes/prefabs/armor/gauntlet_03_juggernaut_plate.tscn",
			"name": "Gauntlet03JuggernautPlate"
		},
		{
			"glb": "res://assets/models/armor/gauntlet_04_abyssal_reliquary.glb",
			"tscn": "res://scenes/prefabs/armor/gauntlet_04_abyssal_reliquary.tscn",
			"name": "Gauntlet04AbyssalReliquary"
		}
	]

	for g_info: Dictionary in gauntlets:
		var glb_path: String = String(g_info["glb"])
		var tscn_path: String = String(g_info["tscn"])
		var r_name: String = String(g_info["name"])
		if not ResourceLoader.exists(glb_path):
			push_error("Missing armor gauntlet GLB: " + glb_path)
			continue
		var glb_scn: PackedScene = load(glb_path) as PackedScene
		if glb_scn == null:
			continue
		var root: Node3D = Node3D.new()
		root.name = r_name
		var model_inst: Node3D = glb_scn.instantiate() as Node3D
		var meshes: Array[MeshInstance3D] = []
		_collect_meshes(model_inst, meshes)
		for old_mi: MeshInstance3D in meshes:
			var mi: MeshInstance3D = MeshInstance3D.new()
			mi.name = old_mi.name
			mi.mesh = old_mi.mesh
			mi.transform = _extract_relative_transform(old_mi, model_inst)
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			if mi.mesh != null:
				for s_idx: int in range(mi.mesh.get_surface_count()):
					var orig_mat: Material = mi.mesh.surface_get_material(s_idx)
					var mat_name: String = orig_mat.resource_name if orig_mat != null else ""
					var grim_mat: Material = GrimdarkMaterialLibrary.get_material_for_name(mat_name)
					if grim_mat != null:
						mi.set_surface_override_material(s_idx, grim_mat)
					elif orig_mat is StandardMaterial3D:
						var dup_mat: StandardMaterial3D = (orig_mat as StandardMaterial3D).duplicate() as StandardMaterial3D
						dup_mat.vertex_color_use_as_albedo = true
						dup_mat.normal_enabled = false
						mi.set_surface_override_material(s_idx, dup_mat)
			root.add_child(mi)
		model_inst.free()
		_set_owner_recursive(root, root)
		_save_packed_scene(root, tscn_path)


func _build_all_prefabs() -> void:
	_create_armor_gauntlet_prefabs()
	_sync_fps_player_lantern_prefab()
	_create_dust_motes_prefab()
	_create_target_dummy_plaque_prefab()
	# Environment prefabs (Phase 2 & 4: simplified terrain collider, box colliders for houses, cyl for trees, 0.0 lod for exterior shell)
	_create_trimesh_prefab(
		"res://assets/models/terrain_town.glb",
		"res://scenes/prefabs/environment/terrain_town.tscn",
		"TerrainTown",
		false,
		0.0,
		false,
		false,
		false,
		"",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"terrain_simplified"
	)
	_create_trimesh_prefab(
		"res://assets/models/house_abandoned_a.glb",
		"res://scenes/prefabs/environment/house_abandoned_a.tscn",
		"HouseAbandonedA",
		true,
		0.0,
		false,
		false,
		false,
		"wood",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_house"
	)
	_create_trimesh_prefab(
		"res://assets/models/house_abandoned_b.glb",
		"res://scenes/prefabs/environment/house_abandoned_b.tscn",
		"HouseAbandonedB",
		true,
		0.0,
		false,
		false,
		false,
		"wood",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_house"
	)
	_create_trimesh_prefab(
		"res://assets/models/dead_tree_gnarled.glb",
		"res://scenes/prefabs/environment/dead_tree_gnarled.tscn",
		"DeadTreeGnarled",
		true,
		65.0,
		false,
		false,
		false,
		"wood",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"cyl_tree"
	)

	# Modular Church & Crypt Architecture prefabs (Phase 1.1: visibility_range_end = 0.0 on all structural architecture)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/wall_stone_solid.glb",
		"res://scenes/prefabs/architecture/wall_stone_solid.tscn",
		"WallStoneSolid",
		true,
		0.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_wall_4x4"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/wall_stone_solid.glb",
		"res://scenes/prefabs/architecture/wall_stone_4x4.tscn",
		"WallStone4x4",
		true,
		0.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_wall_4x4"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/wall_stone_arch_door.glb",
		"res://scenes/prefabs/architecture/wall_stone_arch_door.tscn",
		"WallStoneArchDoor",
		true,
		0.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_wall_door_4x4"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/wall_stone_arch_door.glb",
		"res://scenes/prefabs/architecture/wall_archway_4x4.tscn",
		"WallArchway4x4",
		true,
		0.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_wall_door_4x4"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/wall_stone_window.glb",
		"res://scenes/prefabs/architecture/wall_stone_window.tscn",
		"WallStoneWindow",
		true,
		0.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_wall_4x4"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/floor_stone_4x4.glb",
		"res://scenes/prefabs/architecture/floor_stone_4x4.tscn",
		"FloorStone4x4",
		false,
		0.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_floor_4x4"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/roof_gothic_vault_4x4.glb",
		"res://scenes/prefabs/architecture/roof_gothic_vault_4x4.tscn",
		"RoofGothicVault4x4",
		true,
		0.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_ceiling_4x4"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/roof_gothic_vault_4x4.glb",
		"res://scenes/prefabs/architecture/ceiling_vaulted_4x4.tscn",
		"CeilingVaulted4x4",
		true,
		0.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_ceiling_4x4"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/stairs_stone_4x4.glb",
		"res://scenes/prefabs/architecture/stairs_stone_4x4.tscn",
		"StairsStone4x4",
		true,
		0.0,
		true,
		false,
		false
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/crypt_pillar.glb",
		"res://scenes/prefabs/architecture/crypt_pillar.tscn",
		"CryptPillar",
		true,
		0.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"cyl_pillar"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/crypt_altar.glb",
		"res://scenes/prefabs/architecture/crypt_altar.tscn",
		"CryptAltar",
		true,
		34.0,
		false,
		false,
		true,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_prop"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/church_foundation_plinth.glb",
		"res://scenes/prefabs/architecture/church_foundation_plinth.tscn",
		"ChurchFoundationPlinth",
		true,
		0.0,
		false,
		true,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_church_plinth"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/church_front_gable_rose.glb",
		"res://scenes/prefabs/architecture/church_front_gable_rose.tscn",
		"ChurchFrontGableRose",
		true,
		0.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_prop"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/church_pitched_roof_12x16.glb",
		"res://scenes/prefabs/architecture/church_pitched_roof_12x16.tscn",
		"ChurchPitchedRoof12x16",
		true,
		0.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_prop"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/church_bell_tower_spire.glb",
		"res://scenes/prefabs/architecture/church_bell_tower_spire.tscn",
		"ChurchBellTowerSpire",
		true,
		0.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_prop"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/church_buttress.glb",
		"res://scenes/prefabs/architecture/church_buttress.tscn",
		"ChurchButtress",
		true,
		0.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_prop"
	)
	_create_wall_lantern_prefab()
	_create_standing_brazier_prefab()

	# Phase 1.1: Structural Catacomb Prefabs use lod_distance = 0.0; Decorative Centerpiece Props use 34.0
	_create_trimesh_prefab(
		"res://assets/models/church_kit/crypt_wall_ossuary_4x4.glb",
		"res://scenes/prefabs/architecture/crypt_wall_ossuary_4x4.tscn",
		"CryptWallOssuary4x4",
		true,
		0.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_wall_4x4"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/crypt_archway_portcullis_4x4.glb",
		"res://scenes/prefabs/architecture/crypt_archway_portcullis_4x4.tscn",
		"CryptArchwayPortcullis4x4",
		true,
		0.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_wall_door_4x4"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/crypt_corridor_vault_4x4.glb",
		"res://scenes/prefabs/architecture/crypt_corridor_vault_4x4.tscn",
		"CryptCorridorVault4x4",
		true,
		0.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_ceiling_4x4"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/crypt_iron_gate_cell_4x4.glb",
		"res://scenes/prefabs/architecture/crypt_iron_gate_cell_4x4.tscn",
		"CryptIronGateCell4x4",
		true,
		0.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_wall_door_4x4"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/crypt_sarcophagus_ornate.glb",
		"res://scenes/prefabs/architecture/crypt_sarcophagus_ornate.tscn",
		"CryptSarcophagusOrnate",
		true,
		34.0,
		false,
		false,
		false,
		"stone",
		Color(0.95, 0.55, 1.0, 1.0),
		Vector3(0.0, 0.95, 0.0),
		0.55,
		5.5,
		"box_prop"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/crypt_hanging_cage.glb",
		"res://scenes/prefabs/architecture/crypt_hanging_cage.tscn",
		"CryptHangingCage",
		true,
		34.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_prop"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/crypt_ritual_obelisk.glb",
		"res://scenes/prefabs/architecture/crypt_ritual_obelisk.tscn",
		"CryptRitualObelisk",
		true,
		34.0,
		false,
		false,
		false,
		"stone",
		Color(1.0, 0.15, 0.18, 1.0),
		Vector3(0.0, 2.15, 0.0),
		1.45,
		11.0,
		"box_prop"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/crypt_rotting_bookshelf_4x4.glb",
		"res://scenes/prefabs/architecture/crypt_rotting_bookshelf_4x4.tscn",
		"CryptRottingBookshelf4x4",
		true,
		0.0,
		false,
		false,
		false,
		"wood",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_wall_4x4"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/crypt_lectern_grimoire.glb",
		"res://scenes/prefabs/architecture/crypt_lectern_grimoire.tscn",
		"CryptLecternGrimoire",
		true,
		34.0,
		false,
		false,
		false,
		"stone",
		Color(0.85, 0.45, 1.0, 1.0),
		Vector3(0.0, 1.75, 0.0),
		1.65,
		10.0,
		"box_prop"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/crypt_plague_cauldron.glb",
		"res://scenes/prefabs/architecture/crypt_plague_cauldron.tscn",
		"CryptPlagueCauldron",
		true,
		34.0,
		false,
		false,
		false,
		"stone",
		Color(0.45, 0.95, 0.35, 1.0),
		Vector3(0.0, 1.95, 0.0),
		2.15,
		14.0,
		"box_prop"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/crypt_drowned_cistern_4x4.glb",
		"res://scenes/prefabs/architecture/crypt_drowned_cistern_4x4.tscn",
		"CryptDrownedCistern4x4",
		true,
		0.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_floor_4x4"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/crypt_weeping_statue_pedestal.glb",
		"res://scenes/prefabs/architecture/crypt_weeping_statue_pedestal.tscn",
		"CryptWeepingStatuePedestal",
		true,
		34.0,
		false,
		false,
		false,
		"stone",
		Color(0.35, 0.65, 1.0, 1.0),
		Vector3(0.0, 2.25, 0.55),
		1.95,
		13.0,
		"box_prop"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/crypt_sunken_bell_crater.glb",
		"res://scenes/prefabs/architecture/crypt_sunken_bell_crater.tscn",
		"CryptSunkenBellCrater",
		true,
		34.0,
		false,
		false,
		false,
		"stone",
		Color(1.0, 0.38, 0.12, 1.0),
		Vector3(0.0, 1.35, 0.55),
		1.95,
		14.0,
		"box_prop"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/crypt_containment_hull.glb",
		"res://scenes/prefabs/architecture/crypt_containment_hull.tscn",
		"CryptContainmentHull",
		false,
		0.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"none"
	)

	# Hunter's Sanctuary Hub Station Prefabs
	_create_hub_station_prefab(
		"res://assets/models/church_kit/hub_weapon_workbench.glb",
		"res://scenes/prefabs/hub/hub_weapon_workbench.tscn",
		"HubWeaponWorkbench",
		"weapon",
		"Gunsmith & Consecration Bench",
		Vector3(2.8, 2.2, 1.1),
		Vector3(0.0, 1.1, 0.0),
		Color(1.0, 0.72, 0.36, 1.0),
		Vector3(0.0, 1.85, 0.55),
		1.65,
		9.5
	)
	_create_hub_station_prefab(
		"res://assets/models/church_kit/hub_armor_reliquary_stand.glb",
		"res://scenes/prefabs/hub/hub_armor_reliquary_stand.tscn",
		"HubArmorReliquaryStand",
		"armor",
		"Inquisitor's Armor Reliquary",
		Vector3(2.2, 2.4, 1.0),
		Vector3(0.0, 1.2, 0.0),
		Color(0.88, 0.76, 0.48, 1.0),
		Vector3(0.0, 1.95, 0.55),
		1.60,
		9.5
	)
	_create_hub_station_prefab(
		"res://assets/models/church_kit/hub_sanctuary_upgrade_font.glb",
		"res://scenes/prefabs/hub/hub_sanctuary_upgrade_font.tscn",
		"HubSanctuaryUpgradeFont",
		"upgrade",
		"Consecrated Relic Basin & Crucible",
		Vector3(1.6, 1.85, 1.6),
		Vector3(0.0, 0.92, 0.0),
		Color(1.0, 0.78, 0.25, 1.0),
		Vector3(0.0, 1.65, 0.0),
		2.10,
		12.0
	)

	# High-Density Environmental Clutter Prefabs (Phase 1.1 & 3.3: visibility_range_end = 34.0, fade_self, zero OmniLight3D on candle clusters)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/clutter_rubble_bones_pile.glb",
		"res://scenes/prefabs/architecture/clutter_rubble_bones_pile.tscn",
		"ClutterRubbleBonesPile",
		false,
		34.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.0,
		5.0,
		"none"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/clutter_melted_candle_cluster.glb",
		"res://scenes/prefabs/architecture/clutter_melted_candle_cluster.tscn",
		"ClutterMeltedCandleCluster",
		false,
		34.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3(0.0, 0.42, 0.0),
		0.0,
		0.0,
		"none"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/clutter_ceiling_chains_roots.glb",
		"res://scenes/prefabs/architecture/clutter_ceiling_chains_roots.tscn",
		"ClutterCeilingChainsRoots",
		false,
		34.0,
		false,
		false,
		false,
		"wood",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.0,
		5.0,
		"none"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/clutter_wooden_crates_barrels.glb",
		"res://scenes/prefabs/architecture/clutter_wooden_crates_barrels.tscn",
		"ClutterWoodenCratesBarrels",
		true,
		34.0,
		false,
		false,
		false,
		"wood",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.0,
		5.0,
		"box_crates"
	)

	# Town Exterior Gothic Clutter & Roadside Prefabs (Phase 2 & 4)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/town_street_lamp_iron.glb",
		"res://scenes/prefabs/environment/town_street_lamp_iron.tscn",
		"TownStreetLampIron",
		true,
		45.0,
		false,
		false,
		false,
		"stone",
		Color(1.0, 0.68, 0.28, 1.0),
		Vector3(0.0, 2.74, 0.78),
		1.45,
		13.0,
		"box_prop"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/town_graveyard_wall_fence_6m.glb",
		"res://scenes/prefabs/environment/town_graveyard_wall_fence_6m.tscn",
		"TownGraveyardWallFence6m",
		true,
		45.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_prop"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/town_gravestone_cluster.glb",
		"res://scenes/prefabs/environment/town_gravestone_cluster.tscn",
		"TownGravestoneCluster",
		true,
		38.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_prop"
	)
	_create_trimesh_prefab(
		"res://assets/models/church_kit/town_road_curb_8m.glb",
		"res://scenes/prefabs/environment/town_road_curb_8m.tscn",
		"TownRoadCurb8m",
		false,
		45.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.0,
		5.0,
		"none"
	)

	# 8-Biome Occult Rift Portal & 8 Articulated Biome Enemy Prefabs
	_create_occult_rift_portal_prefab()
	_create_crypt_enemy_prefab(
		"res://assets/models/enemies/enemy_01_ossuary_executioner.glb",
		"res://scenes/prefabs/enemies/enemy_01_ossuary_executioner.tscn",
		"Enemy01OssuaryExecutioner",
		"Ossuary Executioner",
		95.0,
		"MELEE_RUSHER",
		1,
		0.0,
		5.4,
		2.45,
		22.0
	)
	_create_crypt_enemy_prefab(
		"res://assets/models/enemies/enemy_02_necropolis_praetorian.glb",
		"res://scenes/prefabs/enemies/enemy_02_necropolis_praetorian.tscn",
		"Enemy02NecropolisPraetorian",
		"Necropolis Praetorian",
		140.0,
		"SHIELD_GUARD",
		2,
		15.0,
		3.15,
		2.60,
		24.0
	)
	_create_crypt_enemy_prefab(
		"res://assets/models/enemies/enemy_03_reliquary_hexweaver.glb",
		"res://scenes/prefabs/enemies/enemy_03_reliquary_hexweaver.tscn",
		"Enemy03ReliquaryHexweaver",
		"Reliquary Hex-Weaver",
		90.0,
		"RANGED_CASTER",
		3,
		0.0,
		3.60,
		11.5,
		18.0
	)
	_create_crypt_enemy_prefab(
		"res://assets/models/enemies/enemy_04_inquisitor_rackmaster.glb",
		"res://scenes/prefabs/enemies/enemy_04_inquisitor_rackmaster.tscn",
		"Enemy04InquisitorRackmaster",
		"Inquisitor Rack-Master",
		155.0,
		"HEAVY_BRUTE",
		4,
		15.0,
		3.35,
		3.20,
		30.0
	)
	_create_crypt_enemy_prefab(
		"res://assets/models/enemies/enemy_05_plague_bloater.glb",
		"res://scenes/prefabs/enemies/enemy_05_plague_bloater.tscn",
		"Enemy05PlagueBloater",
		"Alchemical Plague Bloater",
		115.0,
		"RANGED_LOBBER_EXPLODER",
		5,
		5.0,
		2.95,
		11.0,
		20.0
	)
	_create_crypt_enemy_prefab(
		"res://assets/models/enemies/enemy_06_weeping_banshee.glb",
		"res://scenes/prefabs/enemies/enemy_06_weeping_banshee.tscn",
		"Enemy06WeepingBanshee",
		"Cenotaph Weeping Banshee",
		105.0,
		"BLINK_WRAITH",
		6,
		0.0,
		4.40,
		9.50,
		19.0
	)
	_create_crypt_enemy_prefab(
		"res://assets/models/enemies/enemy_07_bell_juggernaut.glb",
		"res://scenes/prefabs/enemies/enemy_07_bell_juggernaut.tscn",
		"Enemy07BellJuggernaut",
		"Sunken Bell Juggernaut",
		185.0,
		"SONIC_JUGGERNAUT",
		7,
		18.0,
		2.90,
		3.60,
		34.0
	)
	_create_crypt_enemy_prefab(
		"res://assets/models/enemies/enemy_08_abyssal_archon.glb",
		"res://scenes/prefabs/enemies/enemy_08_abyssal_archon.tscn",
		"Enemy08AbyssalArchon",
		"Abyssal Blood Archon",
		210.0,
		"ELITE_HYBRID_LORD",
		8,
		15.0,
		4.20,
		8.50,
		28.0
	)
	# Legacy aliases backed by the new 160+ part articulated rigs
	_create_crypt_enemy_prefab(
		"res://assets/models/enemies/enemy_01_ossuary_executioner.glb",
		"res://scenes/prefabs/enemies/enemy_ossuary_skeleton.tscn",
		"EnemyOssuarySkeleton",
		"Ossuary Skeleton",
		85.0,
		"MELEE_RUSHER",
		1,
		0.0,
		5.2,
		2.4,
		20.0
	)
	_create_crypt_enemy_prefab(
		"res://assets/models/enemies/enemy_04_inquisitor_rackmaster.glb",
		"res://scenes/prefabs/enemies/enemy_iron_penitent.tscn",
		"EnemyIronPenitent",
		"Iron Penitent",
		135.0,
		"HEAVY_BRUTE",
		4,
		15.0,
		3.35,
		3.1,
		28.0
	)
	_create_crypt_enemy_prefab(
		"res://assets/models/enemies/enemy_05_plague_bloater.glb",
		"res://scenes/prefabs/enemies/enemy_plague_acolyte.tscn",
		"EnemyPlagueAcolyte",
		"Plague Acolyte",
		110.0,
		"RANGED_LOBBER_EXPLODER",
		5,
		0.0,
		3.1,
		10.5,
		20.0
	)
	_create_reliquary_chest_prefab("res://scenes/prefabs/props/prop_gothic_reliquary_chest.tscn")
	_create_reliquary_chest_prefab("res://scenes/prefabs/hub/prop_gothic_reliquary_chest.tscn")

	# Biome 1 (The Endless Ossuary) Bespoke Variety Prefabs (structural = 0.0, decorative = 34.0)
	_create_trimesh_prefab(
		"res://assets/models/ossuary_variety/ossuary_stone_bridge_4x4.glb",
		"res://scenes/prefabs/ossuary_variety/ossuary_stone_bridge_4x4.tscn",
		"OssuaryStoneBridge4x4",
		true,
		0.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_bridge_4x4"
	)
	_create_trimesh_prefab(
		"res://assets/models/ossuary_variety/ossuary_balcony_railing_4m.glb",
		"res://scenes/prefabs/ossuary_variety/ossuary_balcony_railing_4m.tscn",
		"OssuaryBalconyRailing4m",
		true,
		0.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_railing_4m"
	)
	_create_trimesh_prefab(
		"res://assets/models/ossuary_variety/ossuary_buttress_arch_4x4.glb",
		"res://scenes/prefabs/ossuary_variety/ossuary_buttress_arch_4x4.tscn",
		"OssuaryButtressArch4x4",
		true,
		0.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_buttress_arch_4x4"
	)
	_create_trimesh_prefab(
		"res://assets/models/ossuary_variety/ossuary_bone_chandelier.glb",
		"res://scenes/prefabs/ossuary_variety/ossuary_bone_chandelier.tscn",
		"OssuaryBoneChandelier",
		false,
		34.0,
		false,
		false,
		false,
		"stone",
		Color(1.0, 0.66, 0.25, 1.0),
		Vector3(0.0, 0.55, 0.0),
		1.45,
		13.0,
		"none"
	)
	_create_trimesh_prefab(
		"res://assets/models/ossuary_variety/ossuary_spine_reliquary_monolith.glb",
		"res://scenes/prefabs/ossuary_variety/ossuary_spine_reliquary_monolith.tscn",
		"OssuarySpineReliquaryMonolith",
		true,
		34.0,
		false,
		false,
		false,
		"stone",
		Color(1.0, 0.32, 0.16, 1.0),
		Vector3(0.0, 1.95, 0.0),
		1.50,
		11.5,
		"box_prop"
	)
	_create_trimesh_prefab(
		"res://assets/models/ossuary_variety/ossuary_burial_niche_divider_4x4.glb",
		"res://scenes/prefabs/ossuary_variety/ossuary_burial_niche_divider_4x4.tscn",
		"OssuaryBurialNicheDivider4x4",
		true,
		34.0,
		false,
		false,
		false,
		"stone",
		Color(0.0, 0.0, 0.0, 0.0),
		Vector3.ZERO,
		1.4,
		11.0,
		"box_prop"
	)

	# Biomes 2, 3 & 4 Bespoke 3D Hero Architectural Kits (walls/monoliths = 0.0 lod, 0 OmniLight3D inside prefabs)
	var biome_2_to_4_kits: Array[Dictionary] = [
		{
			"glb": "res://assets/models/dungeon/necropolis_wall_armory_4x4.glb",
			"tscn": "res://scenes/prefabs/dungeon/necropolis_wall_armory_4x4.tscn",
			"name": "NecropolisWallArmory4x4",
			"lod": 0.0,
			"col": "box_wall_4x4"
		},
		{
			"glb": "res://assets/models/dungeon/necropolis_iron_maiden_monolith.glb",
			"tscn": "res://scenes/prefabs/dungeon/necropolis_iron_maiden_monolith.tscn",
			"name": "NecropolisIronMaidenMonolith",
			"lod": 0.0,
			"col": "box_prop"
		},
		{
			"glb": "res://assets/models/dungeon/necropolis_hanging_war_brazier.glb",
			"tscn": "res://scenes/prefabs/dungeon/necropolis_hanging_war_brazier.tscn",
			"name": "NecropolisHangingWarBrazier",
			"lod": 34.0,
			"col": "none"
		},
		{
			"glb": "res://assets/models/dungeon/reliquary_wall_grimoire_4x4.glb",
			"tscn": "res://scenes/prefabs/dungeon/reliquary_wall_grimoire_4x4.tscn",
			"name": "ReliquaryWallGrimoire4x4",
			"lod": 0.0,
			"col": "box_wall_4x4"
		},
		{
			"glb": "res://assets/models/dungeon/reliquary_astral_orrery_monolith.glb",
			"tscn": "res://scenes/prefabs/dungeon/reliquary_astral_orrery_monolith.tscn",
			"name": "ReliquaryAstralOrreryMonolith",
			"lod": 0.0,
			"col": "box_prop"
		},
		{
			"glb": "res://assets/models/dungeon/reliquary_chandelier_astrolabe.glb",
			"tscn": "res://scenes/prefabs/dungeon/reliquary_chandelier_astrolabe.tscn",
			"name": "ReliquaryChandelierAstrolabe",
			"lod": 34.0,
			"col": "none"
		},
		{
			"glb": "res://assets/models/dungeon/abattoir_wall_furnace_4x4.glb",
			"tscn": "res://scenes/prefabs/dungeon/abattoir_wall_furnace_4x4.tscn",
			"name": "AbattoirWallFurnace4x4",
			"lod": 0.0,
			"col": "box_wall_4x4"
		},
		{
			"glb": "res://assets/models/dungeon/abattoir_blood_press_monolith.glb",
			"tscn": "res://scenes/prefabs/dungeon/abattoir_blood_press_monolith.tscn",
			"name": "AbattoirBloodPressMonolith",
			"lod": 0.0,
			"col": "box_prop"
		},
		{
			"glb": "res://assets/models/dungeon/abattoir_hanging_hook_rack.glb",
			"tscn": "res://scenes/prefabs/dungeon/abattoir_hanging_hook_rack.tscn",
			"name": "AbattoirHangingHookRack",
			"lod": 34.0,
			"col": "none"
		}
	]
	for b_kit: Dictionary in biome_2_to_4_kits:
		_create_trimesh_prefab(
			String(b_kit["glb"]),
			String(b_kit["tscn"]),
			String(b_kit["name"]),
			true,
			float(b_kit["lod"]),
			false,
			false,
			false,
			"stone",
			Color(0.0, 0.0, 0.0, 0.0),
			Vector3.ZERO,
			0.0,
			0.0,
			String(b_kit["col"])
		)


func _create_reliquary_chest_prefab(prefab_path: String) -> void:
	var glb_scene: PackedScene = load("res://assets/models/items/prop_gothic_reliquary_chest.glb") as PackedScene
	if glb_scene == null:
		push_error("Could not load GLB: prop_gothic_reliquary_chest.glb")
		return

	var chest_script: Script = load("res://scripts/interaction/reliquary_chest.gd") as Script
	var root: StaticBody3D = StaticBody3D.new()
	root.name = "PropGothicReliquaryChest"
	root.collision_layer = 1
	root.collision_mask = 1
	root.set_meta("surface_type", "wood")
	if chest_script != null:
		root.set_script(chest_script)

	var model_inst: Node3D = glb_scene.instantiate() as Node3D
	var meshes: Array[MeshInstance3D] = []
	_collect_meshes(model_inst, meshes)

	for old_mi: MeshInstance3D in meshes:
		var mi: MeshInstance3D = MeshInstance3D.new()
		mi.name = old_mi.name
		mi.mesh = old_mi.mesh
		mi.transform = _extract_relative_transform(old_mi, model_inst)
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		mi.visibility_range_end = 24.0
		mi.visibility_range_end_margin = 3.0
		mi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF

		if mi.mesh != null:
			for s_idx: int in range(mi.mesh.get_surface_count()):
				var orig_mat: Material = mi.mesh.surface_get_material(s_idx)
				var mat_name: String = orig_mat.resource_name if orig_mat != null else ""
				if mat_name.is_empty():
					mat_name = mi.name
				var grim_mat: Material = GrimdarkMaterialLibrary.get_material_for_name(mat_name)
				if grim_mat != null:
					mi.set_surface_override_material(s_idx, grim_mat)
				elif orig_mat is StandardMaterial3D:
					var em_mat: StandardMaterial3D = (orig_mat as StandardMaterial3D).duplicate() as StandardMaterial3D
					em_mat.vertex_color_use_as_albedo = true
					em_mat.normal_enabled = false
					mi.set_surface_override_material(s_idx, em_mat)

		root.add_child(mi)

	model_inst.free()

	var box_col: CollisionShape3D = CollisionShape3D.new()
	box_col.name = "InteractionBoundsCollider"
	var b_shape: BoxShape3D = BoxShape3D.new()
	b_shape.size = Vector3(1.42, 0.96, 0.92)
	box_col.shape = b_shape
	box_col.position = Vector3(0.0, 0.48, 0.0)
	root.add_child(box_col)

	var chest_light: OmniLight3D = OmniLight3D.new()
	chest_light.name = "ChestGlowLight"
	chest_light.position = Vector3(0.0, 0.85, 0.25)
	chest_light.light_color = Color(1.0, 0.65, 0.24, 1.0)
	chest_light.light_energy = 1.45
	chest_light.omni_range = 6.5
	_configure_omni_distance_fade(chest_light, false)
	root.add_child(chest_light)

	_set_owner_recursive(root, root)
	_save_packed_scene(root, prefab_path)


func _create_occult_rift_portal_prefab() -> void:
	var glb_scene: PackedScene = load("res://assets/models/architecture/occult_rift_portal.glb") as PackedScene
	if glb_scene == null:
		push_error("Could not load GLB: occult_rift_portal.glb")
		return

	var portal_script: Script = load("res://scripts/interaction/occult_portal.gd") as Script
	var vortex_shader: Shader = load("res://shaders/portal_vortex.gdshader") as Shader

	var root: Node3D = Node3D.new()
	root.name = "OccultRiftPortal"
	if portal_script != null:
		root.set_script(portal_script)

	var model_inst: Node3D = glb_scene.instantiate() as Node3D
	var meshes: Array[MeshInstance3D] = []
	_collect_meshes(model_inst, meshes)

	var raw_max_y: float = 0.01
	for m_chk: MeshInstance3D in meshes:
		if m_chk.mesh != null:
			var rel_xf: Transform3D = _extract_relative_transform(m_chk, model_inst)
			var b: AABB = m_chk.get_aabb()
			for ix: int in [0, 1]:
				for iy: int in [0, 1]:
					for iz: int in [0, 1]:
						var pt_y: float = (rel_xf * (b.position + Vector3(b.size.x * float(ix), b.size.y * float(iy), b.size.z * float(iz)))).y
						raw_max_y = maxf(raw_max_y, pt_y)

	var norm_factor: float = 3.95 / maxf(raw_max_y, 3.95)
	var scale_xform: Transform3D = Transform3D(Basis.from_scale(Vector3(norm_factor, norm_factor, norm_factor)), Vector3.ZERO)
	root.scale = Vector3(0.76, 0.76, 0.76)

	for old_mi: MeshInstance3D in meshes:
		var mi: MeshInstance3D = MeshInstance3D.new()
		mi.name = old_mi.name
		mi.mesh = old_mi.mesh
		mi.transform = scale_xform * _extract_relative_transform(old_mi, model_inst)
		mi.visibility_range_end = 0.0
		mi.visibility_range_end_margin = 0.0

		if mi.name == "PortalVortexMesh" or mi.name.contains("Vortex"):
			mi.name = "PortalVortexMesh"
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			if vortex_shader != null:
				var smat: ShaderMaterial = ShaderMaterial.new()
				smat.shader = vortex_shader
				mi.material_override = smat
		else:
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
			if mi.mesh != null:
				for s_idx: int in range(mi.mesh.get_surface_count()):
					var orig_mat: Material = mi.mesh.surface_get_material(s_idx)
					var mat_name: String = orig_mat.resource_name if orig_mat != null else ""
					if mat_name.is_empty():
						mat_name = mi.name
					var grim_mat: Material = GrimdarkMaterialLibrary.get_material_for_name(mat_name)
					if grim_mat != null:
						mi.set_surface_override_material(s_idx, grim_mat)
					elif orig_mat is StandardMaterial3D:
						var em_mat: StandardMaterial3D = (orig_mat as StandardMaterial3D).duplicate() as StandardMaterial3D
						em_mat.vertex_color_use_as_albedo = true
						em_mat.normal_enabled = false
						mi.set_surface_override_material(s_idx, em_mat)

		root.add_child(mi)

	model_inst.free()

	# Add pillar frame colliders leaving the central archway completely walkable
	var frame_body: StaticBody3D = StaticBody3D.new()
	frame_body.name = "PortalFrameBody"
	frame_body.collision_layer = 1
	frame_body.collision_mask = 1
	frame_body.set_meta("surface_type", "stone")
	root.add_child(frame_body)

	for side_s: float in [-1.0, 1.0]:
		var pier_col: CollisionShape3D = CollisionShape3D.new()
		pier_col.name = "PortalPierCollider_" + ("L" if side_s < 0.0 else "R")
		var pier_box: BoxShape3D = BoxShape3D.new()
		pier_box.size = Vector3(0.58, 3.80, 0.80)
		pier_col.shape = pier_box
		pier_col.position = Vector3(side_s * 1.42, 1.90, 0.0)
		frame_body.add_child(pier_col)

	var trigger_area: Area3D = Area3D.new()
	trigger_area.name = "PortalTriggerArea"
	trigger_area.collision_layer = 1
	trigger_area.collision_mask = 1
	trigger_area.monitoring = true
	trigger_area.monitorable = true
	root.add_child(trigger_area)

	var trig_col: CollisionShape3D = CollisionShape3D.new()
	trig_col.name = "CollisionShape3D"
	var trig_box: BoxShape3D = BoxShape3D.new()
	trig_box.size = Vector3(2.1, 3.2, 0.95)
	trig_col.shape = trig_box
	trig_col.position = Vector3(0.0, 1.85, 0.0)
	trigger_area.add_child(trig_col)

	var glow_light: OmniLight3D = OmniLight3D.new()
	glow_light.name = "PortalGlowLight"
	glow_light.position = Vector3(0.0, 2.0, 0.0)
	glow_light.light_color = Color(1.0, 0.65, 0.28, 1.0)
	glow_light.light_energy = 2.35
	glow_light.omni_range = 10.5
	glow_light.omni_attenuation = 1.35
	_configure_omni_distance_fade(glow_light, false)
	root.add_child(glow_light)

	_set_owner_recursive(root, root)
	_save_packed_scene(root, "res://scenes/prefabs/hub/occult_rift_portal.tscn")


func _clone_enemy_hierarchy_recursive(src_node: Node, dst_parent: Node3D) -> void:
	if src_node is MeshInstance3D:
		var old_mi: MeshInstance3D = src_node as MeshInstance3D
		var mi: MeshInstance3D = MeshInstance3D.new()
		mi.name = old_mi.name
		mi.mesh = old_mi.mesh
		mi.transform = old_mi.transform
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		mi.visibility_range_end = 38.0
		mi.visibility_range_end_margin = 4.0

		if mi.mesh != null:
			for s_idx: int in range(mi.mesh.get_surface_count()):
				var orig_mat: Material = mi.mesh.surface_get_material(s_idx)
				var mat_name: String = orig_mat.resource_name if orig_mat != null else ""
				if mat_name.is_empty():
					mat_name = mi.name
				var grim_mat: Material = GrimdarkMaterialLibrary.get_material_for_name(mat_name)
				if grim_mat != null:
					mi.set_surface_override_material(s_idx, grim_mat)
				elif orig_mat is StandardMaterial3D:
					var em_mat: StandardMaterial3D = (orig_mat as StandardMaterial3D).duplicate() as StandardMaterial3D
					em_mat.vertex_color_use_as_albedo = true
					em_mat.normal_enabled = false
					mi.set_surface_override_material(s_idx, em_mat)

		dst_parent.add_child(mi)
		for child: Node in old_mi.get_children():
			_clone_enemy_hierarchy_recursive(child, mi)
	elif src_node is Node3D:
		var old_n3d: Node3D = src_node as Node3D
		var n3d: Node3D = Node3D.new()
		n3d.name = old_n3d.name
		n3d.transform = old_n3d.transform
		dst_parent.add_child(n3d)
		for child: Node in old_n3d.get_children():
			_clone_enemy_hierarchy_recursive(child, n3d)


func _create_crypt_enemy_prefab(
	glb_path: String,
	prefab_path: String,
	root_name: String,
	enemy_title: String,
	max_hp: float,
	archetype: String = "MELEE_RUSHER",
	biome_id: int = 1,
	armor_val: float = 0.0,
	spd: float = 4.2,
	atk_range: float = 2.45,
	atk_dmg: float = 22.0
) -> void:
	var glb_scene: PackedScene = load(glb_path) as PackedScene
	if glb_scene == null:
		push_error("Could not load Enemy GLB: " + glb_path)
		return

	var enemy_script: Script = load("res://scripts/enemies/crypt_enemy.gd") as Script
	var root: CharacterBody3D = CharacterBody3D.new()
	root.name = root_name
	root.collision_layer = 4
	root.collision_mask = 1 | 2
	root.floor_max_angle = deg_to_rad(52.0)
	root.floor_snap_length = 0.35
	if enemy_script != null:
		root.set_script(enemy_script)
		root.set("enemy_title", enemy_title)
		root.set("max_health", max_hp)
		root.set("current_health", max_hp)
		root.set("combat_archetype", archetype)
		root.set("biome_relic_id", biome_id)
		root.set("flat_armor", armor_val)
		root.set("move_speed", spd)
		root.set("attack_range", atk_range)
		root.set("attack_damage", atk_dmg)
		root.set("is_passive_dummy", false)

	var model_inst: Node3D = glb_scene.instantiate() as Node3D
	for child: Node in model_inst.get_children():
		_clone_enemy_hierarchy_recursive(child, root)
	model_inst.free()

	var cap_col: CollisionShape3D = CollisionShape3D.new()
	cap_col.name = "EnemyCapsuleCollider"
	var cap: CapsuleShape3D = CapsuleShape3D.new()
	cap.radius = 0.42
	cap.height = 1.85
	cap_col.shape = cap
	cap_col.position = Vector3(0.0, 0.95, 0.0)
	root.add_child(cap_col)

	_set_owner_recursive(root, root)
	_save_packed_scene(root, prefab_path)


func _create_hub_station_prefab(
	glb_path: String,
	prefab_path: String,
	root_name: String,
	st_type: String,
	st_title: String,
	box_size: Vector3,
	box_center: Vector3,
	light_color: Color,
	light_pos: Vector3,
	light_energy: float,
	light_range: float
) -> void:
	var glb_scene: PackedScene = load(glb_path) as PackedScene
	if glb_scene == null:
		push_error("Could not load HubStation GLB: " + glb_path)
		return

	var station_script: Script = load("res://scripts/interaction/hub_station.gd") as Script
	var root: StaticBody3D = StaticBody3D.new()
	root.name = root_name
	root.collision_layer = 1
	root.collision_mask = 1
	root.set_meta("surface_type", "stone")
	if station_script != null:
		root.set_script(station_script)
		root.set("station_type", st_type)
		root.set("station_title", st_title)

	var model_inst: Node3D = glb_scene.instantiate() as Node3D
	var meshes: Array[MeshInstance3D] = []
	_collect_meshes(model_inst, meshes)

	for old_mi: MeshInstance3D in meshes:
		var mi: MeshInstance3D = MeshInstance3D.new()
		mi.name = old_mi.name
		mi.mesh = old_mi.mesh
		mi.transform = _extract_relative_transform(old_mi, model_inst)
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		mi.visibility_range_end = 38.0
		mi.visibility_range_end_margin = 4.0

		if mi.mesh != null:
			for s_idx: int in range(mi.mesh.get_surface_count()):
				var orig_mat: Material = mi.mesh.surface_get_material(s_idx)
				var mat_name: String = orig_mat.resource_name if orig_mat != null else ""
				if mat_name.is_empty():
					mat_name = mi.name
				var grim_mat: Material = GrimdarkMaterialLibrary.get_material_for_name(mat_name)
				if grim_mat != null:
					mi.set_surface_override_material(s_idx, grim_mat)
				elif orig_mat is StandardMaterial3D:
					var em_mat: StandardMaterial3D = (orig_mat as StandardMaterial3D).duplicate() as StandardMaterial3D
					em_mat.vertex_color_use_as_albedo = true
					em_mat.normal_enabled = false
					mi.set_surface_override_material(s_idx, em_mat)

		root.add_child(mi)

	model_inst.free()

	# Add a dedicated interaction & physics bounding BoxShape3D on the HubStation root
	var bound_col: CollisionShape3D = CollisionShape3D.new()
	bound_col.name = "InteractionBoundsCollider"
	var b_shape: BoxShape3D = BoxShape3D.new()
	b_shape.size = box_size
	bound_col.shape = b_shape
	bound_col.position = box_center
	root.add_child(bound_col)

	var spot_light: OmniLight3D = OmniLight3D.new()
	spot_light.name = "HubStationSpotlight"
	spot_light.position = light_pos
	spot_light.light_color = light_color
	spot_light.light_energy = light_energy
	spot_light.light_volumetric_fog_energy = 3.8
	spot_light.omni_range = light_range
	spot_light.omni_attenuation = 1.25
	spot_light.light_specular = 0.24
	_configure_omni_distance_fade(spot_light, false)
	root.add_child(spot_light)

	_set_owner_recursive(root, root)
	_save_packed_scene(root, prefab_path)


func _cell_from_world(pos: Vector3) -> Vector3i:
	return Vector3i(roundi(pos.x / 4.0), roundi(pos.y / 4.0), roundi(pos.z / 4.0))


func _wall_grid_key(pos: Vector3) -> String:
	return "%d_%d_%d" % [roundi(pos.x * 2.0), roundi(pos.y * 2.0), roundi(pos.z * 2.0)]


func _register_crypt_room_cell(
	occupied_cells: Dictionary[Vector3i, String],
	gx: int,
	gy: int,
	gz: int,
	group_id: String
) -> void:
	occupied_cells[Vector3i(gx, gy, gz)] = group_id


func _register_crypt_staircase_cells(
	occupied_cells: Dictionary[Vector3i, String],
	gx: int,
	gy_upper: int,
	gz: int,
	group_id: String
) -> void:
	occupied_cells[Vector3i(gx, gy_upper - 1, gz)] = group_id
	occupied_cells[Vector3i(gx, gy_upper, gz)] = group_id


func _spawn_crypt_floor(
	scene_root: Node3D,
	parent: Node3D,
	scene: PackedScene,
	inst_name: String,
	pos: Vector3,
	placed_floors: Dictionary[Vector3i, Node3D]
) -> Node3D:
	var inst: Node3D = _spawn_prefab(scene_root, parent, scene, inst_name, pos)
	inst.scale = Vector3(1.015, 1.0, 1.015)
	placed_floors[_cell_from_world(pos)] = inst
	return inst


func _spawn_crypt_ceiling(
	scene_root: Node3D,
	parent: Node3D,
	scene: PackedScene,
	inst_name: String,
	cell_pos: Vector3,
	placed_ceilings: Dictionary[Vector3i, Node3D]
) -> Node3D:
	var ceil_pos: Vector3 = Vector3(cell_pos.x, cell_pos.y + 3.86, cell_pos.z)
	var inst: Node3D = _spawn_prefab(scene_root, parent, scene, inst_name, ceil_pos)
	inst.scale = Vector3(1.015, 1.0, 1.015)
	placed_ceilings[_cell_from_world(cell_pos)] = inst
	return inst


func _spawn_crypt_wall(
	scene_root: Node3D,
	parent: Node3D,
	scene: PackedScene,
	inst_name: String,
	pos: Vector3,
	rot_y_deg: float,
	placed_walls: Dictionary[String, Node3D]
) -> Node3D:
	var w_key: String = _wall_grid_key(pos)
	if placed_walls.has(w_key):
		return placed_walls[w_key]
	var inst: Node3D = _spawn_prefab(scene_root, parent, scene, inst_name, pos, rot_y_deg)
	placed_walls[w_key] = inst
	return inst


func _seal_crypt_grid_boundaries(
	scene_root: Node3D,
	sealer_container: Node3D,
	p_floor: PackedScene,
	p_vault_corr: PackedScene,
	p_wall_solid: PackedScene,
	occupied_cells: Dictionary[Vector3i, String],
	placed_floors: Dictionary[Vector3i, Node3D],
	placed_ceilings: Dictionary[Vector3i, Node3D],
	placed_walls: Dictionary[String, Node3D],
	open_passages: Dictionary[String, bool]
) -> void:
	var auto_floors: int = 0
	var auto_ceilings: int = 0
	var auto_walls: int = 0

	var dir_offsets: Array[Vector3i] = [
		Vector3i(0, 0, -1),
		Vector3i(0, 0, 1),
		Vector3i(-1, 0, 0),
		Vector3i(1, 0, 0)
	]
	var face_offsets: Array[Vector3] = [
		Vector3(0.0, 0.0, -2.0),
		Vector3(0.0, 0.0, 2.0),
		Vector3(-2.0, 0.0, 0.0),
		Vector3(2.0, 0.0, 0.0)
	]
	var face_rots: Array[float] = [0.0, 0.0, 90.0, 90.0]
	var face_tags: Array[String] = ["N", "S", "W", "E"]

	for cell: Vector3i in occupied_cells.keys():
		var group_id: String = occupied_cells[cell]
		var cell_world: Vector3 = Vector3(float(cell.x) * 4.0, float(cell.y) * 4.0, float(cell.z) * 4.0)

		# 1. Bottom Face (-Y): Seal if below_cell does not belong to the same vertical room/stairwell group
		var is_stair_cell: bool = group_id.begins_with("stair_") or (cell == Vector3i(0, 0, -5))
		var below_cell: Vector3i = Vector3i(cell.x, cell.y - 1, cell.z)
		if not is_stair_cell and occupied_cells.get(below_cell, "") != group_id and not placed_floors.has(cell):
			_spawn_crypt_floor(
				scene_root,
				sealer_container,
				p_floor,
				"AutoSealFloor_%d_%d_%d" % [cell.x, cell.y, cell.z],
				cell_world,
				placed_floors
			)
			auto_floors += 1

		# 2. Top Face (+Y): Seal if above_cell does not belong to the same vertical room/stairwell group
		# (Except the single church nave stair collar cells (0, 0, -5) and (0, 0, -6) which open into the Church at Z in [-24, -20])
		var above_cell: Vector3i = Vector3i(cell.x, cell.y + 1, cell.z)
		var is_nave_stair_opening: bool = (cell == Vector3i(0, 0, -5) or cell == Vector3i(0, 0, -6))
		if not is_nave_stair_opening and occupied_cells.get(above_cell, "") != group_id and not placed_ceilings.has(cell):
			_spawn_crypt_ceiling(
				scene_root,
				sealer_container,
				p_vault_corr,
				"AutoSealCeil_%d_%d_%d" % [cell.x, cell.y, cell.z],
				cell_world,
				placed_ceilings
			)
			auto_ceilings += 1

		# 3. North / South / West / East Faces (±X, ±Z)
		for d_idx: int in range(4):
			var n_cell: Vector3i = cell + dir_offsets[d_idx]
			var n_group: String = occupied_cells.get(n_cell, "")
			if n_group == group_id:
				continue

			var w_pos: Vector3 = cell_world + face_offsets[d_idx]
			var w_key: String = _wall_grid_key(w_pos)
			var rot_y: float = face_rots[d_idx]

			if n_group.is_empty():
				if open_passages.has(w_key):
					continue
				# Exterior boundary face: MUST be sealed by a solid wall (never open or portcullis)
				if placed_walls.has(w_key):
					var existing_w: Node3D = placed_walls[w_key]
					if existing_w != null and existing_w.name.contains("Portcullis"):
						existing_w.get_parent().remove_child(existing_w)
						existing_w.free()
						placed_walls.erase(w_key)
				if not placed_walls.has(w_key):
					_spawn_crypt_wall(
						scene_root,
						sealer_container,
						p_wall_solid,
						"AutoSealWallExt_%s_%d_%d_%d" % [face_tags[d_idx], cell.x, cell.y, cell.z],
						w_pos,
						rot_y,
						placed_walls
					)
					auto_walls += 1
			else:
				# Internal boundary between two different room/corridor/stairwell groups:
				# Seal with a solid bulkhead/divider wall unless an explicit portcullis or open passage is registered
				if not placed_walls.has(w_key) and not open_passages.has(w_key):
					_spawn_crypt_wall(
						scene_root,
						sealer_container,
						p_wall_solid,
						"AutoSealBulkhead_%s_%d_%d_%d" % [face_tags[d_idx], cell.x, cell.y, cell.z],
						w_pos,
						rot_y,
						placed_walls
					)
					auto_walls += 1

	print(
		"[CryptSealer] Sealed %d occupied cells -> added %d floors, %d ceilings, %d bulkhead/perimeter walls"
		% [occupied_cells.size(), auto_floors, auto_ceilings, auto_walls]
	)


func _spawn_prefab(
	scene_root: Node3D,
	parent: Node3D,
	scene: PackedScene,
	inst_name: String,
	pos: Vector3,
	rot_y_deg: float = 0.0
) -> Node3D:
	var inst: Node3D = scene.instantiate() as Node3D
	inst.name = inst_name
	inst.position = pos
	if absf(rot_y_deg) > 0.001:
		inst.rotation.y = deg_to_rad(rot_y_deg)
	parent.add_child(inst)
	# Set owner ONLY on the prefab instance root so it serializes as a clean ExtResource instance!
	inst.owner = scene_root
	return inst


func _add_chamber_light(
	scene_root: Node3D,
	parent: Node3D,
	light_name: String,
	pos: Vector3,
	col: Color,
	energy: float,
	range_val: float,
	shadows: bool = false,
	fog_energy: float = 4.2
) -> OmniLight3D:
	var light: OmniLight3D = OmniLight3D.new()
	light.name = light_name
	light.position = pos
	light.light_color = col
	light.light_energy = energy
	light.light_volumetric_fog_energy = fog_energy
	light.omni_range = range_val
	light.omni_attenuation = 1.25
	light.light_specular = 0.22
	_configure_omni_distance_fade(light, shadows)
	parent.add_child(light)
	light.owner = scene_root
	return light


func _smoothstep(edge0: float, edge1: float, x: float) -> float:
	if is_equal_approx(edge0, edge1):
		return 0.0
	var t: float = clampf((x - edge0) / (edge1 - edge0), 0.0, 1.0)
	return t * t * (3.0 - 2.0 * t)


func _get_terrain_height(gx: float, gz: float) -> float:
	var hills: float = (
		1.45 * sin(gx * 0.05) * cos(gz * 0.045)
		+ 0.95 * cos((gx + 15.0) * 0.08) * sin((gz - 8.0) * 0.075)
		+ 0.25 * sin(gx * 0.14 + gz * 0.13)
	)
	var edge_ridge: float = 0.0030 * (gx * gx)
	var north_slope: float = _smoothstep(20.0, -22.0, gz) * 3.4 + _smoothstep(-20.0, -38.0, gz) * 1.6
	var base_h: float = maxf(0.0, 0.55 + hills * 0.60 + edge_ridge + north_slope)

	var road_z_factor: float = _smoothstep(48.0, 34.0, gz) * _smoothstep(-14.5, -9.0, gz)
	var road_x_dist: float = absf(gx - 1.2 * sin(gz * 0.09))
	var road_mask: float = (1.0 - _smoothstep(4.5, 11.5, road_x_dist)) * road_z_factor
	var road_progress: float = _smoothstep(26.0, -10.2, gz)
	var road_h: float = 0.15 + road_progress * (3.20 - 0.15)

	var dist_ha: float = Vector2((gx - (-16.0)) / 1.1, (gz - 14.0) / 1.2).length()
	var mask_ha: float = 1.0 - _smoothstep(5.5, 11.5, dist_ha)
	var h_ha: float = 0.85

	var dist_hb: float = Vector2((gx - 16.0) / 1.1, (gz - 8.0) / 1.2).length()
	var mask_hb: float = 1.0 - _smoothstep(5.5, 11.5, dist_hb)
	var h_hb: float = 1.15

	var box_dx: float = maxf(0.0, absf(gx) - 15.0)
	var box_dz: float = maxf(0.0, gz - (-9.0)) if gz > -22.0 else maxf(0.0, (-59.0) - gz)
	var dist_church: float = Vector2(box_dx, box_dz).length()
	var mask_church: float = 1.0 - _smoothstep(0.5, 10.5, dist_church)
	var church_ramp: float = _smoothstep(-9.5, -12.2, gz)
	var h_church: float = 3.20 + church_ramp * (3.55 - 3.20)

	var h: float = base_h
	h = h * (1.0 - road_mask) + road_h * road_mask
	h = h * (1.0 - mask_ha) + h_ha * mask_ha
	h = h * (1.0 - mask_hb) + h_hb * mask_hb
	h = h * (1.0 - mask_church) + h_church * mask_church
	if gz <= -47.5:
		h = maxf(h, 4.35)
	return h


func _get_terrain_normal(gx: float, gz: float) -> Vector3:
	var eps: float = 0.15
	var hl: float = _get_terrain_height(gx - eps, gz)
	var hr: float = _get_terrain_height(gx + eps, gz)
	var hd: float = _get_terrain_height(gx, gz - eps)
	var hu: float = _get_terrain_height(gx, gz + eps)
	var norm: Vector3 = Vector3(hl - hr, 2.0 * eps, hd - hu).normalized()
	return norm


func _build_town_overworld() -> void:
	var p_terrain: PackedScene = load("res://scenes/prefabs/environment/terrain_town.tscn") as PackedScene
	var p_house_a: PackedScene = load("res://scenes/prefabs/environment/house_abandoned_a.tscn") as PackedScene
	var p_house_b: PackedScene = load("res://scenes/prefabs/environment/house_abandoned_b.tscn") as PackedScene

	var p_wall_solid: PackedScene = load("res://scenes/prefabs/architecture/wall_stone_solid.tscn") as PackedScene
	var p_wall_door: PackedScene = load("res://scenes/prefabs/architecture/wall_stone_arch_door.tscn") as PackedScene
	var p_wall_win: PackedScene = load("res://scenes/prefabs/architecture/wall_stone_window.tscn") as PackedScene
	var p_floor: PackedScene = load("res://scenes/prefabs/architecture/floor_stone_4x4.tscn") as PackedScene
	var p_roof: PackedScene = load("res://scenes/prefabs/architecture/roof_gothic_vault_4x4.tscn") as PackedScene
	var p_stairs: PackedScene = load("res://scenes/prefabs/architecture/stairs_stone_4x4.tscn") as PackedScene
	var p_pillar: PackedScene = load("res://scenes/prefabs/architecture/crypt_pillar.tscn") as PackedScene
	var p_altar: PackedScene = load("res://scenes/prefabs/architecture/crypt_altar.tscn") as PackedScene
	var p_plinth: PackedScene = load("res://scenes/prefabs/architecture/church_foundation_plinth.tscn") as PackedScene
	var p_gable: PackedScene = load("res://scenes/prefabs/architecture/church_front_gable_rose.tscn") as PackedScene
	var p_roof_pitched: PackedScene = load("res://scenes/prefabs/architecture/church_pitched_roof_12x16.tscn") as PackedScene
	var p_tower: PackedScene = load("res://scenes/prefabs/architecture/church_bell_tower_spire.tscn") as PackedScene
	var p_buttress: PackedScene = load("res://scenes/prefabs/architecture/church_buttress.tscn") as PackedScene
	var p_lantern: PackedScene = load("res://scenes/prefabs/architecture/wall_lantern_sconce.tscn") as PackedScene
	var p_brazier: PackedScene = load("res://scenes/prefabs/architecture/standing_iron_brazier.tscn") as PackedScene
	var p_tree: PackedScene = load("res://scenes/prefabs/environment/dead_tree_gnarled.tscn") as PackedScene
	var p_player: PackedScene = load("res://scenes/prefabs/player/fps_player.tscn") as PackedScene

	# Modular Catacomb & 8-Chamber Centerpiece Prefabs
	var p_ossuary: PackedScene = load("res://scenes/prefabs/architecture/crypt_wall_ossuary_4x4.tscn") as PackedScene
	var p_portcullis: PackedScene = load("res://scenes/prefabs/architecture/crypt_archway_portcullis_4x4.tscn") as PackedScene
	var p_vault_corr: PackedScene = load("res://scenes/prefabs/architecture/crypt_corridor_vault_4x4.tscn") as PackedScene
	var p_cell_gate: PackedScene = load("res://scenes/prefabs/architecture/crypt_iron_gate_cell_4x4.tscn") as PackedScene
	var p_sarcophagus: PackedScene = load("res://scenes/prefabs/architecture/crypt_sarcophagus_ornate.tscn") as PackedScene
	var p_gibbet: PackedScene = load("res://scenes/prefabs/architecture/crypt_hanging_cage.tscn") as PackedScene
	var p_obelisk: PackedScene = load("res://scenes/prefabs/architecture/crypt_ritual_obelisk.tscn") as PackedScene
	var p_bookshelf: PackedScene = load("res://scenes/prefabs/architecture/crypt_rotting_bookshelf_4x4.tscn") as PackedScene
	var p_lectern: PackedScene = load("res://scenes/prefabs/architecture/crypt_lectern_grimoire.tscn") as PackedScene
	var p_cauldron: PackedScene = load("res://scenes/prefabs/architecture/crypt_plague_cauldron.tscn") as PackedScene
	var p_cistern: PackedScene = load("res://scenes/prefabs/architecture/crypt_drowned_cistern_4x4.tscn") as PackedScene
	var p_weeping_saint: PackedScene = load("res://scenes/prefabs/architecture/crypt_weeping_statue_pedestal.tscn") as PackedScene
	var p_sunken_bell: PackedScene = load("res://scenes/prefabs/architecture/crypt_sunken_bell_crater.tscn") as PackedScene
	var p_containment_hull: PackedScene = load("res://scenes/prefabs/architecture/crypt_containment_hull.tscn") as PackedScene

	# Hunter's Sanctuary Hub Station & Safe Harbour Prefabs
	var p_hub_workbench: PackedScene = load("res://scenes/prefabs/hub/hub_weapon_workbench.tscn") as PackedScene
	var p_hub_armor: PackedScene = load("res://scenes/prefabs/hub/hub_armor_reliquary_stand.tscn") as PackedScene
	var p_hub_font: PackedScene = load("res://scenes/prefabs/hub/hub_sanctuary_upgrade_font.tscn") as PackedScene
	var p_rift_portal: PackedScene = load("res://scenes/prefabs/hub/occult_rift_portal.tscn") as PackedScene
	var p_reliquary_chest: PackedScene = load("res://scenes/prefabs/props/prop_gothic_reliquary_chest.tscn") as PackedScene
	var p_target_plaque: PackedScene = load("res://scenes/prefabs/hub/target_dummy_plaque.tscn") as PackedScene

	# High-Density Clutter & Roadside Prefabs
	var p_rubble_bones: PackedScene = load("res://scenes/prefabs/architecture/clutter_rubble_bones_pile.tscn") as PackedScene
	var p_candles: PackedScene = load("res://scenes/prefabs/architecture/clutter_melted_candle_cluster.tscn") as PackedScene
	var p_chains_roots: PackedScene = load("res://scenes/prefabs/architecture/clutter_ceiling_chains_roots.tscn") as PackedScene
	var p_crates_barrels: PackedScene = load("res://scenes/prefabs/architecture/clutter_wooden_crates_barrels.tscn") as PackedScene
	var p_street_lamp: PackedScene = load("res://scenes/prefabs/environment/town_street_lamp_iron.tscn") as PackedScene
	var p_graveyard_fence: PackedScene = load("res://scenes/prefabs/environment/town_graveyard_wall_fence_6m.tscn") as PackedScene
	var p_gravestones: PackedScene = load("res://scenes/prefabs/environment/town_gravestone_cluster.tscn") as PackedScene
	var p_road_curb: PackedScene = load("res://scenes/prefabs/environment/town_road_curb_8m.tscn") as PackedScene
	var p_railing: PackedScene = load("res://scenes/prefabs/ossuary_variety/ossuary_balcony_railing_4m.tscn") as PackedScene

	var root: Node3D = Node3D.new()
	root.name = "TownOverworld"

	# 1. Single WorldEnvironment (Phase 5.1: SDFGI/SSIL disabled, Sky Ambient 0.65/0.45, Half-Res SSAO detail=0.25, SSR steps=12, VolFog length=28m)
	var world_env: WorldEnvironment = WorldEnvironment.new()
	world_env.name = "WorldEnvironment"
	var env: Environment = Environment.new()
	var sky: Sky = Sky.new()
	var sky_shader: Shader = load("res://shaders/occult_storm_sky.gdshader") as Shader
	var sky_mat: ShaderMaterial = ShaderMaterial.new()
	sky_mat.shader = sky_shader
	sky.sky_material = sky_mat
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_color = Color(0.08, 0.07, 0.12, 1.0)
	env.ambient_light_sky_contribution = 0.65
	env.ambient_light_energy = 0.45

	# Filmic Tonemapping & Color Grading
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_exposure = 1.05
	env.adjustment_enabled = true
	env.adjustment_contrast = 1.12
	env.adjustment_saturation = 0.92

	# Disable expensive real-time SDFGI & SSIL (Phase 5.1)
	env.sdfgi_enabled = false
	env.ssil_enabled = false

	# Tuned Cavity SSAO (half-size enabled in project.godot)
	env.ssao_enabled = true
	env.ssao_radius = 0.85
	env.ssao_intensity = 2.6
	env.ssao_detail = 0.25
	env.ssao_power = 1.5

	# Tuned Wet-Stone Screen-Space Reflections (SSR)
	env.ssr_enabled = true
	env.ssr_max_steps = 12

	env.glow_enabled = true
	env.glow_intensity = 0.4
	env.glow_bloom = 0.1
	env.volumetric_fog_enabled = true
	env.volumetric_fog_density = 0.008
	env.volumetric_fog_anisotropy = 0.55
	env.volumetric_fog_length = 28.0
	env.volumetric_fog_albedo = Color(0.12, 0.13, 0.18, 1.0)
	env.volumetric_fog_emission = Color(0.02, 0.015, 0.035, 1.0)
	world_env.environment = env
	root.add_child(world_env)
	world_env.owner = root

	# 1b. ZonePerformanceManager & ZoneVisibilityController (Phase 1.2: Never hide TownRoot or CryptRoot while in Hub)
	var zone_perf_script: Script = load("res://scripts/world/zone_performance_manager.gd") as Script
	if zone_perf_script != null:
		var zone_mgr: Node3D = Node3D.new()
		zone_mgr.name = "ZonePerformanceManager"
		zone_mgr.set_script(zone_perf_script)
		root.add_child(zone_mgr)
		zone_mgr.owner = root

	var zone_vis_script: Script = load("res://scripts/world/zone_visibility_controller.gd") as Script
	if zone_vis_script != null:
		var zone_vis: Node3D = Node3D.new()
		zone_vis.name = "ZoneVisibilityController"
		zone_vis.set_script(zone_vis_script)
		root.add_child(zone_vis)
		zone_vis.owner = root

	# 2. Clean WorldGeometry Hierarchy with TownRoot & CryptRoot (AGENTS.md Section 6.2 & Phase 1.2)
	var world_geom: Node3D = Node3D.new()
	world_geom.name = "WorldGeometry"
	root.add_child(world_geom)
	world_geom.owner = root

	var town_root_node: Node3D = Node3D.new()
	town_root_node.name = "TownRoot"
	world_geom.add_child(town_root_node)
	town_root_node.owner = root

	var crypt_root_node: Node3D = Node3D.new()
	crypt_root_node.name = "CryptRoot"
	world_geom.add_child(crypt_root_node)
	crypt_root_node.owner = root

	var town_ext_zone: Node3D = Node3D.new()
	town_ext_zone.name = "TownExteriorZone"
	town_root_node.add_child(town_ext_zone)
	town_ext_zone.owner = root

	var church_zone: Node3D = Node3D.new()
	church_zone.name = "ChurchWorkshopZone"
	town_root_node.add_child(church_zone)
	church_zone.owner = root

	var crypt_zone: Node3D = Node3D.new()
	crypt_zone.name = "CryptPortalNexusZone"
	crypt_root_node.add_child(crypt_zone)
	crypt_zone.owner = root

	var terrain_container: Node3D = Node3D.new()
	terrain_container.name = "Terrain"
	town_ext_zone.add_child(terrain_container)
	terrain_container.owner = root

	var structures_container: Node3D = Node3D.new()
	structures_container.name = "Structures"
	town_ext_zone.add_child(structures_container)
	structures_container.owner = root

	var props_container: Node3D = Node3D.new()
	props_container.name = "Props"
	town_ext_zone.add_child(props_container)
	props_container.owner = root

	var crypt_container: Node3D = Node3D.new()
	crypt_container.name = "CryptBasement"
	crypt_container.position = Vector3(0.0, 0.0, -28.0)
	crypt_zone.add_child(crypt_container)
	crypt_container.owner = root

	var lighting_container: Node3D = Node3D.new()
	lighting_container.name = "Lighting"
	world_geom.add_child(lighting_container)
	lighting_container.owner = root

	var fog_shader: Shader = load("res://shaders/rolling_volumetric_fog.gdshader") as Shader
	if fog_shader != null:
		var overworld_fog: FogVolume = FogVolume.new()
		overworld_fog.name = "OverworldRollingFogVolume"
		overworld_fog.size = Vector3(48.0, 10.0, 56.0)
		overworld_fog.position = Vector3(0.0, 3.5, -6.0)
		var ow_fog_mat: ShaderMaterial = ShaderMaterial.new()
		ow_fog_mat.shader = fog_shader
		ow_fog_mat.set_shader_parameter("base_density", 0.085)
		ow_fog_mat.set_shader_parameter("trough_density", 0.005)
		ow_fog_mat.set_shader_parameter("height_falloff", 0.32)
		ow_fog_mat.set_shader_parameter("base_height", 4.2)
		overworld_fog.material = ow_fog_mat
		town_ext_zone.add_child(overworld_fog)
		overworld_fog.owner = root

		var crypt_fog: FogVolume = FogVolume.new()
		crypt_fog.name = "CryptPoolingFogVolume"
		crypt_fog.size = Vector3(72.0, 16.0, 76.0)
		crypt_fog.position = Vector3(0.0, -3.0, -52.0)
		var cr_fog_mat: ShaderMaterial = ShaderMaterial.new()
		cr_fog_mat.shader = fog_shader
		cr_fog_mat.set_shader_parameter("base_density", 0.085)
		cr_fog_mat.set_shader_parameter("trough_density", 0.005)
		cr_fog_mat.set_shader_parameter("height_falloff", 0.55)
		cr_fog_mat.set_shader_parameter("base_height", 0.5)
		crypt_fog.material = cr_fog_mat
		crypt_zone.add_child(crypt_fog)
		crypt_fog.owner = root

	# 3. Terrain Instance & GPU-Instanced Swaying Grass (12,000 instances)
	_spawn_prefab(root, terrain_container, p_terrain, "TerrainTown", Vector3.ZERO)

	var grass_glb: PackedScene = load("res://assets/models/grass_clump_wild.glb") as PackedScene
	if grass_glb != null:
		var grass_inst: Node3D = grass_glb.instantiate() as Node3D
		var grass_meshes: Array[MeshInstance3D] = []
		_collect_meshes(grass_inst, grass_meshes)
		var grass_mesh: Mesh = grass_meshes[0].mesh if not grass_meshes.is_empty() else null
		grass_inst.free()

		if grass_mesh != null:
			var grass_shader: Shader = load("res://shaders/wind_grass.gdshader") as Shader
			var grass_mat: ShaderMaterial = ShaderMaterial.new()
			grass_mat.shader = grass_shader

			var grass_script: Script = load("res://scripts/environment/overworld_grass.gd") as Script
			var mm_inst: MultiMeshInstance3D = MultiMeshInstance3D.new()
			mm_inst.name = "OverworldGrass"
			if grass_script != null:
				mm_inst.set_script(grass_script)
			mm_inst.set("grass_mesh", grass_mesh)
			mm_inst.set("grass_material", grass_mat)
			mm_inst.set("instance_count_target", 12000)

			terrain_container.add_child(mm_inst)
			mm_inst.owner = root

			if mm_inst.has_method("generate_grass"):
				mm_inst.call("generate_grass")
			print("[Build] Configured OverworldGrass MultiMesh generator")

	# 4. Scatter Gnarled Dead Trees along the valley, behind houses, and framing church hill (outside Cathedral X in [-14, +14])
	var tree_coords: Array[Vector3] = [
		Vector3(-7.5, 0.0, 22.0),
		Vector3(7.2, 0.0, 18.5),
		Vector3(-8.5, 0.0, 6.0),
		Vector3(8.0, 0.0, 2.5),
		Vector3(-7.8, 0.0, -6.5),
		Vector3(-22.0, 0.0, 18.0),
		Vector3(-21.0, 0.0, 8.5),
		Vector3(22.5, 0.0, 14.0),
		Vector3(21.0, 0.0, 2.0),
		Vector3(-17.8, 0.0, -14.5),
		Vector3(17.8, 0.0, -14.5),
		Vector3(-18.2, 0.0, -25.5),
		Vector3(18.2, 0.0, -25.5)
	]
	for idx: int in range(tree_coords.size()):
		var tpos: Vector3 = tree_coords[idx]
		tpos.y = _get_terrain_height(tpos.x, tpos.z)
		var rot: float = float((idx * 67) % 360)
		_spawn_prefab(root, props_container, p_tree, "DeadTree_%d" % idx, tpos, rot)

	# 5. Two Abandoned Houses flanking the valley path (with 2.5m deep plinths embedded into hillsides)
	_spawn_prefab(root, structures_container, p_house_a, "HouseAbandonedA", Vector3(-16.0, 1.25, 14.0), 68.0)
	_spawn_prefab(root, structures_container, p_house_b, "HouseAbandonedB", Vector3(16.0, 1.55, 8.0), -68.0)

	# 6. Grand Cruciform Cathedral Sanctuary inside ChurchWorkshopZone on the hilltop plateau
	#    church.position = Vector3(0.0, 4.0, 0.0) so local X and Z match world X and Z!
	#    Spans 28m wide (X = -14.0m .. +14.0m), 36m long (Z = -22.0m .. -58.0m) + 12m x 10m Forecourt (Z = -12.0m .. -22.0m)
	var church: Node3D = Node3D.new()
	church.name = "GothicChurch"
	church.position = Vector3(0.0, 4.0, 0.0)
	church_zone.add_child(church)
	church.owner = root

	# Foundation plinth with front entrance steps at Z = -20.0 (front steps at Z = -12.0 .. -10.0)
	_spawn_prefab(root, church, p_plinth, "ChurchFoundationPlinth", Vector3(0.0, 0.0, -20.0))

	# Forecourt Floor tiles (X in {-4, 0, +4}, Z in {-14, -18, -22})
	for fc_x: float in [-4.0, 0.0, 4.0]:
		for fc_z: float in [-14.0, -18.0, -22.0]:
			_spawn_prefab(root, church, p_floor, "ForecourtFloor_%.0f_%.0f" % [fc_x + 4.0, absf(fc_z)], Vector3(fc_x, 0.0, fc_z))

	# South Outer Entrance Wall at Z = -12.0m & Forecourt Side Balustrades
	_spawn_prefab(root, church, p_wall_win, "ForecourtWallSouthLeft", Vector3(-4.0, 0.0, -12.0))
	_spawn_prefab(root, church, p_wall_door, "WallSouthEntranceArch", Vector3(0.0, 0.0, -12.0))
	_spawn_prefab(root, church, p_wall_win, "ForecourtWallSouthRight", Vector3(4.0, 0.0, -12.0))
	for fc_sz: float in [-14.0, -18.0]:
		_spawn_prefab(root, church, p_wall_win, "ForecourtWallWest_%.0f" % absf(fc_sz), Vector3(-6.0, 0.0, fc_sz), 90.0)
		_spawn_prefab(root, church, p_wall_win, "ForecourtWallEast_%.0f" % absf(fc_sz), Vector3(6.0, 0.0, fc_sz), 90.0)
		for fc_sx: float in [-4.0, 0.0, 4.0]:
			_spawn_prefab(root, church, p_roof, "ForecourtVault_%.0f_%.0f" % [fc_sx + 4.0, absf(fc_sz)], Vector3(fc_sx, 4.0, fc_sz))

	# Grand Cruciform Cathedral Floor (7x9 grid: X in {-12, -8, -4, 0, +4, +8, +12}, Z in {-24, -28, -32, -36, -40, -44, -48, -52, -56})
	# Only the single 4m x 4m stairwell footprint (X = 0.0, Z = -48.0 .. -52.0 around StairsStone4x4 at Z = -50.0) is open!
	var floor_xs: Array[float] = [-12.0, -8.0, -4.0, 0.0, 4.0, 8.0, 12.0]
	var floor_zs: Array[float] = [-24.0, -28.0, -32.0, -36.0, -40.0, -44.0, -48.0, -52.0, -56.0]
	for ix: int in range(floor_xs.size()):
		for iz: int in range(floor_zs.size()):
			var fx: float = floor_xs[ix]
			var fz: float = floor_zs[iz]
			# Double-height 8.0m Vaulted Cathedral Ceiling (local Y = 8.0 -> world Y = 12.0) covers every cell
			var rf_inst: Node3D = _spawn_prefab(root, church, p_roof, "ChurchRoofVault_%d_%d" % [ix, iz], Vector3(fx, 8.0, fz))
			rf_inst.scale = Vector3(1.015, 1.0, 1.015)
			if absf(fx) < 0.1 and (absf(fz - (-48.0)) < 0.1 or absf(fz - (-52.0)) < 0.1):
				continue
			var fl_inst: Node3D = _spawn_prefab(root, church, p_floor, "ChurchFloor_%d_%d" % [ix, iz], Vector3(fx, 0.0, fz))
			fl_inst.scale = Vector3(1.015, 1.0, 1.015)

	# Explicitly seal the 4m x 4m floor tile directly South (in front) of the Church-to-Crypt staircase top step!
	# StairsStone4x4 is centered at Z = -50.0 (spanning Z = -48.0 to -52.0), so placing a floor_stone_4x4 tile at Z = -46.0
	# covers Z = -44.0 to -48.0 flush with the top step at Z = -48.0 with ZERO gap!
	var stair_south_floor: Node3D = _spawn_prefab(root, church, p_floor, "ChurchFloor_StairEntrySouth", Vector3(0.0, 0.0, -46.0))
	stair_south_floor.scale = Vector3(1.015, 1.0, 1.0)

	# Crypt Stairwell at (X = 0.0, Y = 0.0, Z = -50.0) descending North from Z = -48.0 (Y = 4.0) down to Z = -52.0 (Y = 0.0)
	_spawn_prefab(root, church, p_stairs, "StairsStone4x4", Vector3(0.0, 0.0, -50.0))
	# Protective stone balustrades (ossuary_balcony_railing_4m) framing the West and East sides of the stairwell drop!
	if p_railing != null:
		_spawn_prefab(root, church, p_railing, "StairwellBalustrade_W1", Vector3(-2.1, 0.0, -48.0), 90.0)
		_spawn_prefab(root, church, p_railing, "StairwellBalustrade_W2", Vector3(-2.1, 0.0, -52.0), 90.0)
		_spawn_prefab(root, church, p_railing, "StairwellBalustrade_E1", Vector3(2.1, 0.0, -48.0), -90.0)
		_spawn_prefab(root, church, p_railing, "StairwellBalustrade_E2", Vector3(2.1, 0.0, -52.0), -90.0)

	# Double-Height (8.0m = 2 tiers at Y = 0.0 and Y = 4.0) Cathedral Perimeter Walls
	# South Cathedral Wall at Z = -22.0m (open in the center X = -4, 0, +4 where the Forecourt joins the Nave)
	for sx_idx: int in range(floor_xs.size()):
		var wx: float = floor_xs[sx_idx]
		for wy_tier: int in [0, 1]:
			var wy: float = float(wy_tier) * 4.0
			# South Wall at Z = -22.0m (outer wings X in {-12, -8, +8, +12}; upper tier also spans X in {-4, 0, +4})
			if absf(wx) >= 7.5 or wy_tier == 1:
				var sw_prefab: PackedScene = p_wall_win if (wy_tier == 1) else p_wall_solid
				_spawn_prefab(root, church, sw_prefab, "CathedralWallSouth_%d_T%d" % [sx_idx, wy_tier], Vector3(wx, wy, -22.0), 0.0)
			# North Apse Wall at Z = -58.0m
			var nw_prefab: PackedScene = p_wall_win if (absf(wx) <= 4.5 and wy_tier == 1) else p_wall_solid
			_spawn_prefab(root, church, nw_prefab, "CathedralWallNorth_%d_T%d" % [sx_idx, wy_tier], Vector3(wx, wy, -58.0), 0.0)

	# West & East Cathedral Side Walls at X = -14.0m and X = +14.0m
	for iz: int in range(floor_zs.size()):
		var wz: float = floor_zs[iz]
		for wy_tier: int in [0, 1]:
			var wy: float = float(wy_tier) * 4.0
			var side_prefab: PackedScene = p_wall_win if (iz % 2 == 1) else p_wall_solid
			_spawn_prefab(root, church, side_prefab, "WallWest_%d_T%d" % [iz, wy_tier], Vector3(-14.0, wy, wz), 90.0)
			_spawn_prefab(root, church, side_prefab, "WallEast_%d_T%d" % [iz, wy_tier], Vector3(14.0, wy, wz), 90.0)

	# Grand Double-Stacked Cathedral Columns at X = -8.5m and X = +8.5m (17.0m wide open central hall!)
	var nave_pillar_zs: Array[float] = [-26.0, -32.0, -40.0, -46.0, -52.0]
	for p_i: int in range(nave_pillar_zs.size()):
		var pz: float = nave_pillar_zs[p_i]
		for p_tier: int in [0, 1]:
			var py: float = float(p_tier) * 4.0
			_spawn_prefab(root, church, p_pillar, "NavePillar_W_%d_T%d" % [p_i, p_tier], Vector3(-8.5, py, pz))
			_spawn_prefab(root, church, p_pillar, "NavePillar_E_%d_T%d" % [p_i, p_tier], Vector3(8.5, py, pz))
		# Wall-mounted sconces on the inner faces of the Nave columns
		_spawn_prefab(root, church, p_lantern, "LanternPillarW_%d" % p_i, Vector3(-8.05, 2.6, pz), 90.0)
		_spawn_prefab(root, church, p_lantern, "LanternPillarE_%d" % p_i, Vector3(8.05, 2.6, pz), -90.0)

	# ==============================================================================================
	# 3 Dedicated, Spacious Workshop Alcoves (Zero clutter in the X in [-4.5, +4.5] Central Carpet!)
	# ==============================================================================================
	# 1. West Transept Wing (X = -10.5m, Z = -36.0m) — The Gunsmith's Arsenal Forge:
	_spawn_prefab(root, church, p_hub_workbench, "HubWeaponWorkbench", Vector3(-10.5, 0.0, -36.0), 90.0)
	_spawn_prefab(root, church, p_crates_barrels, "ForgeOrdnanceCrates_W1", Vector3(-12.2, 0.0, -33.2), 25.0)
	_spawn_prefab(root, church, p_crates_barrels, "ForgeOrdnanceCrates_W2", Vector3(-12.2, 0.0, -38.8), -20.0)
	_spawn_prefab(root, church, p_lantern, "ForgeSconce_W1", Vector3(-13.6, 2.5, -34.0), 90.0)
	_spawn_prefab(root, church, p_lantern, "ForgeSconce_W2", Vector3(-13.6, 2.5, -38.0), 90.0)
	if p_reliquary_chest != null:
		var sanct_chest: Node3D = _spawn_prefab(root, church, p_reliquary_chest, "SanctuaryReliquaryChest", Vector3(-11.5, 0.0, -32.0), 90.0)
		if sanct_chest != null:
			sanct_chest.set("guaranteed_relic_id", 7)

	# 2. East Transept Wing (X = +10.5m, Z = -36.0m) — The Order's Reliquary Armory:
	#    Elevated stone dais (visual only so player walks up effortlessly) + Armor Reliquary Stand + Heraldic Banners
	var armory_dais: Node3D = _spawn_prefab(root, church, p_floor, "ArmoryStoneDais", Vector3(10.5, 0.12, -36.0))
	if armory_dais != null and armory_dais.has_node("StaticBody3D"):
		var dais_sb: Node = armory_dais.get_node("StaticBody3D")
		armory_dais.remove_child(dais_sb)
		dais_sb.free()
	_spawn_prefab(root, church, p_hub_armor, "HubArmorReliquaryStand", Vector3(10.5, 0.0, -36.0), -90.0)
	_spawn_prefab(root, church, p_candles, "ArmoryVotiveCandles_E1", Vector3(11.8, 0.0, -33.5), 15.0)
	_spawn_prefab(root, church, p_candles, "ArmoryVotiveCandles_E2", Vector3(11.8, 0.0, -38.5), -15.0)
	_spawn_prefab(root, church, p_lantern, "ArmorySconce_E1", Vector3(13.6, 2.5, -34.0), -90.0)
	_spawn_prefab(root, church, p_lantern, "ArmorySconce_E2", Vector3(13.6, 2.5, -38.0), -90.0)

	# 3. Sanctuary Side Alcove (X = -6.5m, Z = -42.0m) — The Baptismal Font of Rites (Consecrated Relic Basin):
	#    Positioned in its side alcove completely out of the X = 0.0 central aisle leading to the Crypt Stairwell!
	_spawn_prefab(root, church, p_hub_font, "HubSanctuaryUpgradeFont", Vector3(-6.5, 0.0, -42.0))
	_spawn_prefab(root, church, p_altar, "SanctuaryNorthHighAltar", Vector3(0.0, 0.0, -55.8))

	# 4 Tall Corner Braziers tucked flush against the outer stone walls (X = ±12.5m)
	_spawn_prefab(root, church, p_brazier, "CornerBrazier_SW", Vector3(-12.5, 0.0, -24.5))
	_spawn_prefab(root, church, p_brazier, "CornerBrazier_SE", Vector3(12.5, 0.0, -24.5))
	_spawn_prefab(root, church, p_brazier, "CornerBrazier_NW", Vector3(-12.5, 0.0, -55.5))
	_spawn_prefab(root, church, p_brazier, "CornerBrazier_NE", Vector3(12.5, 0.0, -55.5))

	# Safe Harbour Courtyard Reliquary Chest & Inanimate TargetDummyPlaque (Zero enemies in town_overworld.tscn!)
	if p_reliquary_chest != null:
		var ow_chest_pos: Vector3 = Vector3(-4.8, _get_terrain_height(-4.8, -4.5), -4.5)
		var ow_chest: Node3D = _spawn_prefab(root, props_container, p_reliquary_chest, "OverworldTestReliquaryChest", ow_chest_pos, 35.0)
		if ow_chest != null:
			ow_chest.set("guaranteed_relic_id", 5)

	if p_target_plaque != null:
		var plaque_pos: Vector3 = Vector3(-5.5, _get_terrain_height(-5.5, -9.0), -9.0)
		_spawn_prefab(root, props_container, p_target_plaque, "TargetDummyPlaque", plaque_pos, 15.0)

	# 5b. Cathedral Roof, Rose Gable, Spire, and Buttresses
	_spawn_prefab(root, church, p_gable, "ChurchFrontGableRose", Vector3(0.0, 4.0, -12.0))
	_spawn_prefab(root, church, p_roof_pitched, "ChurchPitchedRoofForecourt", Vector3(0.0, 4.0, -18.0))
	_spawn_prefab(root, church, p_tower, "ChurchBellTowerSpire", Vector3(0.0, 4.0, -14.0))

	var buttress_zs: Array[float] = [-24.0, -32.0, -40.0, -48.0, -56.0]
	for bz_idx: int in range(buttress_zs.size()):
		var bz: float = buttress_zs[bz_idx]
		_spawn_prefab(root, church, p_buttress, "ButtressWest_%d" % bz_idx, Vector3(-14.0, 0.0, bz), -90.0)
		_spawn_prefab(root, church, p_buttress, "ButtressEast_%d" % bz_idx, Vector3(14.0, 0.0, bz), 90.0)
	_spawn_prefab(root, church, p_buttress, "ButtressNorth_L", Vector3(-8.0, 0.0, -58.0), 0.0)
	_spawn_prefab(root, church, p_buttress, "ButtressNorth_R", Vector3(8.0, 0.0, -58.0), 0.0)

	# 5c. Physical Exterior Lanterns & Braziers for Church Entrance
	_spawn_prefab(root, church, p_brazier, "BrazierStepsL", Vector3(-2.35, 0.15, -10.9))
	_spawn_prefab(root, church, p_brazier, "BrazierStepsR", Vector3(2.35, 0.15, -10.9))
	_spawn_prefab(root, church, p_lantern, "LanternSouthL", Vector3(-2.2, 2.4, -11.76), 180.0)
	_spawn_prefab(root, church, p_lantern, "LanternSouthR", Vector3(2.2, 2.4, -11.76), 180.0)

	# ==============================================================================================
	# 6. PHASE 3: Subterranean Gothic Labyrinth (8 Interconnected Atmospheric Chambers across Y=0, -4, -8m)
	#    with Deterministic 3D Grid Voxel / Cell Sealer (4m x 4m x 4m cells)
	# ==============================================================================================
	var occupied_cells: Dictionary[Vector3i, String] = {}
	var placed_floors: Dictionary[Vector3i, Node3D] = {}
	var placed_ceilings: Dictionary[Vector3i, Node3D] = {}
	var placed_walls: Dictionary[String, Node3D] = {}
	var open_passages: Dictionary[String, bool] = {}

	# ----------------------------------------------------------------------------------------------
	# CHAMBER 1 — The Antechamber of Bones (Central Entry Hub | 12m x 12m at Y = 0.0m, X in [-6m, +6m], Z in [-22m, -34m])
	# ----------------------------------------------------------------------------------------------
	var ch1: Node3D = Node3D.new()
	ch1.name = "Chamber1_AntechamberOfBones"
	crypt_container.add_child(ch1)
	ch1.owner = root

	# Register Church Nave Stairwell Entry cell (0, 0, -5) with unobstructed passage into Crypt
	_register_crypt_room_cell(occupied_cells, 0, 0, -5, "stair_church_crypt")
	open_passages[_wall_grid_key(Vector3(0.0, 0.0, -20.0))] = true
	open_passages[_wall_grid_key(Vector3(0.0, 0.0, -22.0))] = true
	open_passages[_wall_grid_key(Vector3(0.0, 4.0, -22.0))] = true
	open_passages[_wall_grid_key(Vector3(0.0, 4.0, -24.0))] = true

	_spawn_prefab(root, ch1, p_wall_solid, "StairwellWallWest", Vector3(-2.0, 0.0, -22.0), 90.0)
	_spawn_prefab(root, ch1, p_wall_solid, "StairwellWallEast", Vector3(2.0, 0.0, -22.0), 90.0)
	_spawn_prefab(root, ch1, p_vault_corr, "StairwellUpperVault", Vector3(0.0, 8.0, -22.0))
	_spawn_prefab(root, ch1, p_lantern, "LanternStairwell", Vector3(0.0, 2.4, -20.25), 0.0)

	var ch1_xs: Array[float] = [-4.0, 0.0, 4.0]
	var ch1_zs: Array[float] = [-24.0, -28.0, -32.0]
	for ix: int in range(ch1_xs.size()):
		for iz: int in range(ch1_zs.size()):
			var cx: float = ch1_xs[ix]
			var cz: float = ch1_zs[iz]
			var gx: int = roundi(cx / 4.0)
			var gz: int = roundi(cz / 4.0)
			_register_crypt_room_cell(occupied_cells, gx, 0, gz, "ch1")
			_spawn_crypt_floor(root, ch1, p_floor, "Ch1Floor_%d_%d" % [ix, iz], Vector3(cx, 0.0, cz), placed_floors)
			if not (gx == 0 and gz == -6):
				_spawn_crypt_ceiling(root, ch1, p_vault_corr, "Ch1Ceiling_%d_%d" % [ix, iz], Vector3(cx, 0.0, cz), placed_ceilings)

	# South Wall of Chamber 1 (Z = -22.0m, flanking the central stairwell)
	_spawn_crypt_wall(root, ch1, p_ossuary, "Ch1WallSouthW", Vector3(-4.0, 0.0, -22.0), 0.0, placed_walls)
	_spawn_crypt_wall(root, ch1, p_ossuary, "Ch1WallSouthE", Vector3(4.0, 0.0, -22.0), 0.0, placed_walls)

	# North Wall of Chamber 1 (Z = -34.0m): North Portcullis Gate at X = 0.0m + Flanking Ossuary Walls
	_spawn_crypt_wall(root, ch1, p_ossuary, "Ch1WallNorthW", Vector3(-4.0, 0.0, -34.0), 0.0, placed_walls)
	_spawn_crypt_wall(root, ch1, p_portcullis, "Ch1PortcullisNorth", Vector3(0.0, 0.0, -34.0), 0.0, placed_walls)
	_spawn_crypt_wall(root, ch1, p_ossuary, "Ch1WallNorthE", Vector3(4.0, 0.0, -34.0), 0.0, placed_walls)

	# West Wall of Chamber 1 (X = -6.0m): West Portcullis Gate (Z = -28m) + North-West Portcullis Gate (Z = -32m)
	_spawn_crypt_wall(root, ch1, p_ossuary, "Ch1WallWestS", Vector3(-6.0, 0.0, -24.0), 90.0, placed_walls)
	_spawn_crypt_wall(root, ch1, p_portcullis, "Ch1PortcullisWest", Vector3(-6.0, 0.0, -28.0), 90.0, placed_walls)
	_spawn_crypt_wall(root, ch1, p_portcullis, "Ch1PortcullisNorthWest", Vector3(-6.0, 0.0, -32.0), 90.0, placed_walls)

	# East Wall of Chamber 1 (X = +6.0m): East Portcullis Gate (Z = -28m) + Ossuary Walls
	_spawn_crypt_wall(root, ch1, p_ossuary, "Ch1WallEastS", Vector3(6.0, 0.0, -24.0), 90.0, placed_walls)
	_spawn_crypt_wall(root, ch1, p_portcullis, "Ch1PortcullisEast", Vector3(6.0, 0.0, -28.0), 90.0, placed_walls)
	_spawn_crypt_wall(root, ch1, p_ossuary, "Ch1WallEastN", Vector3(6.0, 0.0, -32.0), 90.0, placed_walls)

	# 4 Central Crypt Pillars & Warm Amber Torches/Braziers in Chamber 1 (> 3.6m clear of Portal 1 at (4.2, 0.0, -32.5))
	_spawn_prefab(root, ch1, p_pillar, "Ch1Pillar_SW", Vector3(-2.6, 0.0, -26.0))
	_spawn_prefab(root, ch1, p_pillar, "Ch1Pillar_SE", Vector3(2.2, 0.0, -26.0))
	_spawn_prefab(root, ch1, p_pillar, "Ch1Pillar_NW", Vector3(-2.6, 0.0, -30.5))
	_spawn_prefab(root, ch1, p_pillar, "Ch1Pillar_NE", Vector3(2.0, 0.0, -29.0))
	_spawn_prefab(root, ch1, p_brazier, "Ch1Brazier_NW", Vector3(-3.2, 0.0, -32.2))
	_spawn_prefab(root, ch1, p_brazier, "Ch1Brazier_NE", Vector3(1.6, 0.0, -32.5))
	_spawn_prefab(root, ch1, p_lantern, "Ch1Lantern_W", Vector3(-5.65, 2.3, -26.0), -90.0)
	_spawn_prefab(root, ch1, p_lantern, "Ch1Lantern_E", Vector3(5.65, 2.3, -26.0), 90.0)
	_add_chamber_light(root, ch1, "Ch1AmberHubLight", Vector3(0.0, 2.5, -28.5), Color(1.0, 0.65, 0.28, 1.0), 1.65, 14.0)

	# Vaulted Corridors connecting Chamber 1 West & North-West Gates (X = -6m..-10m) to Chamber 2
	for c_idx: int in range(2):
		var corr_z: float = -28.0 if c_idx == 0 else -32.0
		var corr_gz: int = roundi(corr_z / 4.0)
		_register_crypt_room_cell(occupied_cells, -2, 0, corr_gz, "corr_1_2_%d" % c_idx)
		_spawn_crypt_floor(root, ch1, p_floor, "CorrCh1To2Floor_%d" % c_idx, Vector3(-8.0, 0.0, corr_z), placed_floors)
		_spawn_crypt_ceiling(root, ch1, p_vault_corr, "CorrCh1To2Ceil_%d" % c_idx, Vector3(-8.0, 0.0, corr_z), placed_ceilings)
	_spawn_crypt_wall(root, ch1, p_ossuary, "CorrCh1To2WallS", Vector3(-8.0, 0.0, -26.0), 0.0, placed_walls)
	_spawn_crypt_wall(root, ch1, p_ossuary, "CorrCh1To2WallMid", Vector3(-8.0, 0.0, -30.0), 0.0, placed_walls)
	_spawn_crypt_wall(root, ch1, p_ossuary, "CorrCh1To2WallN", Vector3(-8.0, 0.0, -34.0), 0.0, placed_walls)

	# ----------------------------------------------------------------------------------------------
	# CHAMBER 2 — The Hall of Sarcophagi (West Royal Mausoleum | 16m x 16m at Y = 0.0m, X in [-10m, -26m], Z in [-22m, -38m])
	# ----------------------------------------------------------------------------------------------
	var ch2: Node3D = Node3D.new()
	ch2.name = "Chamber2_HallOfSarcophagi"
	crypt_container.add_child(ch2)
	ch2.owner = root

	var ch2_xs: Array[float] = [-12.0, -16.0, -20.0, -24.0]
	var ch2_zs: Array[float] = [-24.0, -28.0, -32.0, -36.0]
	for ix: int in range(ch2_xs.size()):
		for iz: int in range(ch2_zs.size()):
			var cx: float = ch2_xs[ix]
			var cz: float = ch2_zs[iz]
			_register_crypt_room_cell(occupied_cells, roundi(cx / 4.0), 0, roundi(cz / 4.0), "ch2")
			_spawn_crypt_floor(root, ch2, p_floor, "Ch2Floor_%d_%d" % [ix, iz], Vector3(cx, 0.0, cz), placed_floors)
			_spawn_crypt_ceiling(root, ch2, p_vault_corr, "Ch2Ceiling_%d_%d" % [ix, iz], Vector3(cx, 0.0, cz), placed_ceilings)

	# Perimeter Walls for Chamber 2
	for ix: int in range(ch2_xs.size()):
		var wx: float = ch2_xs[ix]
		_spawn_crypt_wall(root, ch2, p_ossuary, "Ch2WallSouth_%d" % ix, Vector3(wx, 0.0, -22.0), 0.0, placed_walls)
		if absf(wx - (-16.0)) < 0.1:
			_spawn_crypt_wall(root, ch2, p_portcullis, "Ch2PortcullisNorthToCh3", Vector3(wx, 0.0, -38.0), 0.0, placed_walls)
		else:
			_spawn_crypt_wall(root, ch2, p_ossuary, "Ch2WallNorth_%d" % ix, Vector3(wx, 0.0, -38.0), 0.0, placed_walls)

	for iz: int in range(ch2_zs.size()):
		var wz: float = ch2_zs[iz]
		_spawn_crypt_wall(root, ch2, p_ossuary, "Ch2WallWest_%d" % iz, Vector3(-26.0, 0.0, wz), 90.0, placed_walls)
		if absf(wz - (-28.0)) < 0.1 or absf(wz - (-32.0)) < 0.1:
			_spawn_crypt_wall(root, ch2, p_portcullis, "Ch2PortcullisEast_%d" % iz, Vector3(-10.0, 0.0, wz), 90.0, placed_walls)
		else:
			_spawn_crypt_wall(root, ch2, p_ossuary, "Ch2WallEast_%d" % iz, Vector3(-10.0, 0.0, wz), 90.0, placed_walls)

	# Grand colonnade of 6 heavy pillars + 6 elevated crypt_sarcophagus_ornate tombs + golden braziers (> 5.0m clear of Portal 2)
	var col_xs: Array[float] = [-13.5, -17.0, -20.5]
	for idx: int in range(col_xs.size()):
		var px: float = col_xs[idx]
		_spawn_prefab(root, ch2, p_pillar, "Ch2PillarSouth_%d" % idx, Vector3(px, 0.0, -26.5))
		_spawn_prefab(root, ch2, p_pillar, "Ch2PillarNorth_%d" % idx, Vector3(px, 0.0, -33.5))
		_spawn_prefab(root, ch2, p_sarcophagus, "Ch2SarcophagusSouth_%d" % idx, Vector3(px, 0.0, -24.2), 0.0)
		_spawn_prefab(root, ch2, p_sarcophagus, "Ch2SarcophagusNorth_%d" % idx, Vector3(px, 0.0, -35.8), 180.0)
		_spawn_prefab(root, ch2, p_brazier, "Ch2BrazierSouth_%d" % idx, Vector3(px + 1.4, 0.0, -26.2))
		_spawn_prefab(root, ch2, p_brazier, "Ch2BrazierNorth_%d" % idx, Vector3(px + 1.4, 0.0, -33.8))

	_add_chamber_light(root, ch2, "Ch2GoldenMausoleumLight", Vector3(-18.0, 2.6, -30.0), Color(1.0, 0.72, 0.28, 1.0), 1.75, 16.0)

	# 4m Portcullis Corridor connecting Chamber 2 (Z = -38m) North to Chamber 3 (Z = -42m) at X = -16.0m
	_register_crypt_room_cell(occupied_cells, -4, 0, -10, "corr_2_3")
	_spawn_crypt_floor(root, ch2, p_floor, "CorrCh2To3Floor", Vector3(-16.0, 0.0, -40.0), placed_floors)
	_spawn_crypt_ceiling(root, ch2, p_vault_corr, "CorrCh2To3Ceil", Vector3(-16.0, 0.0, -40.0), placed_ceilings)
	_spawn_crypt_wall(root, ch2, p_wall_solid, "CorrCh2To3WallW", Vector3(-18.0, 0.0, -40.0), 90.0, placed_walls)
	_spawn_crypt_wall(root, ch2, p_wall_solid, "CorrCh2To3WallE", Vector3(-14.0, 0.0, -40.0), 90.0, placed_walls)

	# ----------------------------------------------------------------------------------------------
	# CHAMBER 3 — The Whispering Reliquary & Forbidden Library (North-West Vault | 12m x 16m at Y = 0.0m, X in [-10m, -22m], Z in [-42m, -58m])
	# ----------------------------------------------------------------------------------------------
	var ch3: Node3D = Node3D.new()
	ch3.name = "Chamber3_ForbiddenLibrary"
	crypt_container.add_child(ch3)
	ch3.owner = root

	var ch3_xs: Array[float] = [-12.0, -16.0, -20.0]
	var ch3_zs: Array[float] = [-44.0, -48.0, -52.0, -56.0]
	for ix: int in range(ch3_xs.size()):
		for iz: int in range(ch3_zs.size()):
			var cx: float = ch3_xs[ix]
			var cz: float = ch3_zs[iz]
			_register_crypt_room_cell(occupied_cells, roundi(cx / 4.0), 0, roundi(cz / 4.0), "ch3")
			_spawn_crypt_floor(root, ch3, p_floor, "Ch3Floor_%d_%d" % [ix, iz], Vector3(cx, 0.0, cz), placed_floors)
			_spawn_crypt_ceiling(root, ch3, p_vault_corr, "Ch3Ceiling_%d_%d" % [ix, iz], Vector3(cx, 0.0, cz), placed_ceilings)

	for ix: int in range(ch3_xs.size()):
		var wx: float = ch3_xs[ix]
		if absf(wx - (-16.0)) < 0.1:
			_spawn_crypt_wall(root, ch3, p_portcullis, "Ch3PortcullisSouth", Vector3(wx, 0.0, -42.0), 0.0, placed_walls)
		else:
			_spawn_crypt_wall(root, ch3, p_wall_solid, "Ch3WallSouth_%d" % ix, Vector3(wx, 0.0, -42.0), 0.0, placed_walls)
		_spawn_crypt_wall(root, ch3, p_ossuary, "Ch3WallNorth_%d" % ix, Vector3(wx, 0.0, -58.0), 0.0, placed_walls)

	for iz: int in range(ch3_zs.size()):
		var wz: float = ch3_zs[iz]
		_spawn_crypt_wall(root, ch3, p_wall_solid, "Ch3WallWest_%d" % iz, Vector3(-22.0, 0.0, wz), 90.0, placed_walls)
		_spawn_crypt_wall(root, ch3, p_wall_solid, "Ch3WallEast_%d" % iz, Vector3(-10.0, 0.0, wz), 90.0, placed_walls)
		# Wall-to-wall towering crypt_rotting_bookshelf_4x4 units facing inward toward the aisle
		_spawn_prefab(root, ch3, p_bookshelf, "Ch3BookshelfWest_%d" % iz, Vector3(-21.35, 0.0, wz), 90.0)
		_spawn_prefab(root, ch3, p_bookshelf, "Ch3BookshelfEast_%d" % iz, Vector3(-10.65, 0.0, wz), -90.0)

	_spawn_prefab(root, ch3, p_bookshelf, "Ch3BookshelfNorthW", Vector3(-19.5, 0.0, -57.35), 0.0)
	_spawn_prefab(root, ch3, p_bookshelf, "Ch3BookshelfNorthE", Vector3(-12.5, 0.0, -57.35), 0.0)
	_spawn_prefab(root, ch3, p_pillar, "Ch3Pillar_SW", Vector3(-13.6, 0.0, -46.0))
	_spawn_prefab(root, ch3, p_pillar, "Ch3Pillar_SE", Vector3(-18.4, 0.0, -46.0))
	_spawn_prefab(root, ch3, p_pillar, "Ch3Pillar_NW", Vector3(-13.6, 0.0, -51.5))
	_spawn_prefab(root, ch3, p_pillar, "Ch3Pillar_NE", Vector3(-18.4, 0.0, -51.5))

	# Central reading tables flanking the library aisle + spotlighted crypt_lectern_grimoire on raised dais
	_spawn_prefab(root, ch3, p_altar, "Ch3ReadingTableWest", Vector3(-17.8, 0.0, -48.5), 90.0)
	_spawn_prefab(root, ch3, p_altar, "Ch3ReadingTableEast", Vector3(-14.2, 0.0, -48.5), -90.0)
	_spawn_prefab(root, ch3, p_floor, "Ch3LecternDais", Vector3(-16.0, 0.22, -51.0))
	_spawn_prefab(root, ch3, p_lectern, "Ch3LecternGrimoire", Vector3(-16.0, 0.22, -51.0), 180.0)
	_add_chamber_light(root, ch3, "Ch3VioletCandleLight_1", Vector3(-16.0, 2.5, -48.5), Color(0.85, 0.45, 1.0, 1.0), 1.85, 14.0)
	_add_chamber_light(root, ch3, "Ch3VioletCandleLight_2", Vector3(-16.0, 2.7, -54.0), Color(0.85, 0.45, 1.0, 1.0), 2.1, 14.0)

	# ----------------------------------------------------------------------------------------------
	# CHAMBER 4 — The Inquisitor's Gaol & Gibbet Cells (East Prison Wing | 16m x 12m at Y = 0.0m, X in [+10m, +26m], Z in [-22m, -34m])
	# ----------------------------------------------------------------------------------------------
	var ch4: Node3D = Node3D.new()
	ch4.name = "Chamber4_InquisitorsGaol"
	crypt_container.add_child(ch4)
	ch4.owner = root

	# Connecting 4m corridor from Chamber 1 East gate (X = +6m..+10m, Z = -28m)
	_register_crypt_room_cell(occupied_cells, 2, 0, -7, "corr_1_4")
	_spawn_crypt_floor(root, ch4, p_floor, "CorrCh1To4Floor", Vector3(8.0, 0.0, -28.0), placed_floors)
	_spawn_crypt_ceiling(root, ch4, p_vault_corr, "CorrCh1To4Ceil", Vector3(8.0, 0.0, -28.0), placed_ceilings)
	_spawn_crypt_wall(root, ch4, p_wall_solid, "CorrCh1To4WallS", Vector3(8.0, 0.0, -26.0), 0.0, placed_walls)
	_spawn_crypt_wall(root, ch4, p_wall_solid, "CorrCh1To4WallN", Vector3(8.0, 0.0, -30.0), 0.0, placed_walls)

	var ch4_xs: Array[float] = [12.0, 16.0, 20.0, 24.0]
	var ch4_zs: Array[float] = [-24.0, -28.0, -32.0]
	for ix: int in range(ch4_xs.size()):
		for iz: int in range(ch4_zs.size()):
			var cx: float = ch4_xs[ix]
			var cz: float = ch4_zs[iz]
			_register_crypt_room_cell(occupied_cells, roundi(cx / 4.0), 0, roundi(cz / 4.0), "ch4")
			_spawn_crypt_floor(root, ch4, p_floor, "Ch4Floor_%d_%d" % [ix, iz], Vector3(cx, 0.0, cz), placed_floors)
			_spawn_crypt_ceiling(root, ch4, p_vault_corr, "Ch4Ceiling_%d_%d" % [ix, iz], Vector3(cx, 0.0, cz), placed_ceilings)

	for ix: int in range(ch4_xs.size()):
		var wx: float = ch4_xs[ix]
		_spawn_crypt_wall(root, ch4, p_wall_solid, "Ch4WallSouth_%d" % ix, Vector3(wx, 0.0, -22.0), 0.0, placed_walls)
		if absf(wx - 24.0) < 0.1:
			_spawn_crypt_wall(root, ch4, p_portcullis, "Ch4PortcullisNorthToStairs", Vector3(wx, 0.0, -34.0), 0.0, placed_walls)
		else:
			_spawn_crypt_wall(root, ch4, p_wall_solid, "Ch4WallNorth_%d" % ix, Vector3(wx, 0.0, -34.0), 0.0, placed_walls)

	for iz: int in range(ch4_zs.size()):
		var wz: float = ch4_zs[iz]
		_spawn_crypt_wall(root, ch4, p_wall_solid, "Ch4WallEast_%d" % iz, Vector3(26.0, 0.0, wz), 90.0, placed_walls)
		if absf(wz - (-28.0)) < 0.1:
			_spawn_crypt_wall(root, ch4, p_portcullis, "Ch4PortcullisWest", Vector3(10.0, 0.0, wz), 90.0, placed_walls)
		else:
			_spawn_crypt_wall(root, ch4, p_wall_solid, "Ch4WallWest_%d" % iz, Vector3(10.0, 0.0, wz), 90.0, placed_walls)

	# 4 Prison Cells behind crypt_iron_gate_cell_4x4 bars flanking the Z = -28m central walkway
	_spawn_prefab(root, ch4, p_cell_gate, "Ch4CellGate_SW", Vector3(12.0, 0.0, -26.0))
	_spawn_prefab(root, ch4, p_cell_gate, "Ch4CellGate_SE", Vector3(20.0, 0.0, -26.0))
	_spawn_prefab(root, ch4, p_cell_gate, "Ch4CellGate_NW", Vector3(12.0, 0.0, -30.0), 180.0)
	_spawn_prefab(root, ch4, p_cell_gate, "Ch4CellGate_NE", Vector3(20.0, 0.0, -30.0), 180.0)
	_spawn_prefab(root, ch4, p_wall_solid, "Ch4CellDivider_S1", Vector3(14.0, 0.0, -24.0), 90.0)
	_spawn_prefab(root, ch4, p_wall_solid, "Ch4CellDivider_S2", Vector3(18.0, 0.0, -24.0), 90.0)
	_spawn_prefab(root, ch4, p_wall_solid, "Ch4CellDivider_N1", Vector3(14.0, 0.0, -32.0), 90.0)
	_spawn_prefab(root, ch4, p_wall_solid, "Ch4CellDivider_N2", Vector3(18.0, 0.0, -32.0), 90.0)

	# Suspended crypt_hanging_cage gibbets & sparse flickering sconces
	_spawn_prefab(root, ch4, p_gibbet, "Ch4Gibbet_1", Vector3(14.0, 0.0, -28.0))
	_spawn_prefab(root, ch4, p_gibbet, "Ch4Gibbet_2", Vector3(17.2, 0.0, -28.0), 35.0)
	_spawn_prefab(root, ch4, p_gibbet, "Ch4Gibbet_3", Vector3(20.2, 0.0, -28.0), -25.0)
	_spawn_prefab(root, ch4, p_gibbet, "Ch4Gibbet_CellSW", Vector3(12.0, 0.0, -24.0))
	_spawn_prefab(root, ch4, p_gibbet, "Ch4Gibbet_CellNE", Vector3(20.0, 0.0, -32.0))
	_spawn_prefab(root, ch4, p_lantern, "Ch4SparseSconce", Vector3(25.6, 2.3, -28.0), -90.0)

	# Staircase descending North from Chamber 4 (+24.0, 0.0, -34.0..-38.0) down to Chamber 5 (Y = -4.0m)
	# Register BOTH lower cell (6, -1, -9) and upper headroom cell (6, 0, -9)!
	_register_crypt_staircase_cells(occupied_cells, 6, 0, -9, "stair_4_5")
	_spawn_prefab(root, ch4, p_stairs, "StairsCh4ToCh5", Vector3(24.0, 0.0, -36.0))
	_spawn_crypt_ceiling(root, ch4, p_vault_corr, "StairsCh4ToCh5Ceil", Vector3(24.0, 0.0, -36.0), placed_ceilings)
	_spawn_crypt_wall(root, ch4, p_wall_solid, "StairsCh4ToCh5WallW_Upper", Vector3(22.0, 0.0, -36.0), 90.0, placed_walls)
	_spawn_crypt_wall(root, ch4, p_wall_solid, "StairsCh4ToCh5WallE_Upper", Vector3(26.0, 0.0, -36.0), 90.0, placed_walls)
	_spawn_crypt_wall(root, ch4, p_wall_solid, "StairsCh4ToCh5WallW_Lower", Vector3(22.0, -4.0, -36.0), 90.0, placed_walls)
	_spawn_crypt_wall(root, ch4, p_wall_solid, "StairsCh4ToCh5WallE_Lower", Vector3(26.0, -4.0, -36.0), 90.0, placed_walls)
	_spawn_prefab(root, ch4, p_lantern, "StairsCh4ToCh5Sconce", Vector3(24.0, 1.35, -37.65), 0.0)
	_add_chamber_light(root, ch4, "StairsCh4ToCh5BulkheadLight", Vector3(24.0, 0.85, -36.2), Color(1.0, 0.68, 0.32, 1.0), 1.65, 11.0)

	# ----------------------------------------------------------------------------------------------
	# CHAMBER 5 — The Alchemical Plague Cistern (North-East Rot Vault | 16m x 16m at Y = -4.0m, X in [+10m, +26m], Z in [-38m, -54m])
	# ----------------------------------------------------------------------------------------------
	var ch5: Node3D = Node3D.new()
	ch5.name = "Chamber5_AlchemicalPlagueCistern"
	crypt_container.add_child(ch5)
	ch5.owner = root

	var ch5_xs: Array[float] = [12.0, 16.0, 20.0, 24.0]
	var ch5_zs: Array[float] = [-40.0, -44.0, -48.0, -52.0]
	for ix: int in range(ch5_xs.size()):
		for iz: int in range(ch5_zs.size()):
			var cx: float = ch5_xs[ix]
			var cz: float = ch5_zs[iz]
			var is_cistern_tile: bool = (ix == 1 or ix == 2) and (iz == 1 or iz == 2)
			var tile_prefab: PackedScene = p_cistern if is_cistern_tile else p_floor
			_register_crypt_room_cell(occupied_cells, roundi(cx / 4.0), -1, roundi(cz / 4.0), "ch5")
			_spawn_crypt_floor(root, ch5, tile_prefab, "Ch5Floor_%d_%d" % [ix, iz], Vector3(cx, -4.0, cz), placed_floors)
			_spawn_crypt_ceiling(root, ch5, p_vault_corr, "Ch5Ceiling_%d_%d" % [ix, iz], Vector3(cx, -4.0, cz), placed_ceilings)

	for ix: int in range(ch5_xs.size()):
		var wx: float = ch5_xs[ix]
		if absf(wx - 24.0) < 0.1:
			_spawn_crypt_wall(root, ch5, p_wall_door, "Ch5PortcullisSouthStairs", Vector3(wx, -4.0, -38.0), 0.0, placed_walls)
		else:
			_spawn_crypt_wall(root, ch5, p_wall_solid, "Ch5WallSouth_%d" % ix, Vector3(wx, -4.0, -38.0), 0.0, placed_walls)
		_spawn_crypt_wall(root, ch5, p_ossuary, "Ch5WallNorth_%d" % ix, Vector3(wx, -4.0, -54.0), 0.0, placed_walls)

	for iz: int in range(ch5_zs.size()):
		var wz: float = ch5_zs[iz]
		_spawn_crypt_wall(root, ch5, p_wall_solid, "Ch5WallEast_%d" % iz, Vector3(26.0, -4.0, wz), 90.0, placed_walls)
		if absf(wz - (-44.0)) < 0.1:
			_spawn_crypt_wall(root, ch5, p_portcullis, "Ch5PortcullisWestToCh6", Vector3(10.0, -4.0, wz), 90.0, placed_walls)
		else:
			_spawn_crypt_wall(root, ch5, p_wall_solid, "Ch5WallWest_%d" % iz, Vector3(10.0, -4.0, wz), 90.0, placed_walls)

	# Central crypt_plague_cauldron furnace surrounded by the 4 drowned cistern basins + 4 columns
	_spawn_prefab(root, ch5, p_cauldron, "Ch5PlagueCauldron", Vector3(18.0, -4.0, -46.0))
	_spawn_prefab(root, ch5, p_pillar, "Ch5Pillar_SW", Vector3(13.5, -4.0, -41.5))
	_spawn_prefab(root, ch5, p_pillar, "Ch5Pillar_SE", Vector3(22.5, -4.0, -41.5))
	_spawn_prefab(root, ch5, p_pillar, "Ch5Pillar_NW", Vector3(13.5, -4.0, -50.5))
	_spawn_prefab(root, ch5, p_pillar, "Ch5Pillar_NE", Vector3(22.5, -4.0, -50.5))
	_add_chamber_light(root, ch5, "Ch5ToxicGreenLight_1", Vector3(18.0, -1.2, -46.0), Color(0.45, 0.95, 0.35, 1.0), 2.1, 16.0)
	_add_chamber_light(root, ch5, "Ch5ToxicGreenLight_2", Vector3(14.5, -2.2, -43.0), Color(0.45, 0.95, 0.35, 1.0), 1.1, 10.0)
	_add_chamber_light(root, ch5, "Ch5ToxicGreenLight_3", Vector3(21.5, -2.2, -49.0), Color(0.45, 0.95, 0.35, 1.0), 1.1, 10.0)

	# Connecting 4m corridor at Y = -4.0m between Chamber 5 (+10m) and Chamber 6 (+6m) at Z = -44.0m
	_register_crypt_room_cell(occupied_cells, 2, -1, -11, "corr_5_6")
	_spawn_crypt_floor(root, ch5, p_floor, "CorrCh5To6Floor", Vector3(8.0, -4.0, -44.0), placed_floors)
	_spawn_crypt_ceiling(root, ch5, p_vault_corr, "CorrCh5To6Ceil", Vector3(8.0, -4.0, -44.0), placed_ceilings)
	_spawn_crypt_wall(root, ch5, p_wall_solid, "CorrCh5To6WallS", Vector3(8.0, -4.0, -42.0), 0.0, placed_walls)
	_spawn_crypt_wall(root, ch5, p_wall_solid, "CorrCh5To6WallN", Vector3(8.0, -4.0, -46.0), 0.0, placed_walls)

	# ----------------------------------------------------------------------------------------------
	# CHAMBER 6 — The Cenotaph of the Weeping Saint (Central Lower Shrine | 12m x 16m at Y = -4.0m, X in [-6m, +6m], Z in [-38m, -54m])
	# ----------------------------------------------------------------------------------------------
	var ch6: Node3D = Node3D.new()
	ch6.name = "Chamber6_CenotaphOfTheWeepingSaint"
	crypt_container.add_child(ch6)
	ch6.owner = root

	# Central North processional stairs descending from Chamber 1 (Z = -34m..-38m, Y = 0.0m -> -4.0m)
	# Register BOTH lower cell (0, -1, -9) and upper headroom cell (0, 0, -9)!
	_register_crypt_staircase_cells(occupied_cells, 0, 0, -9, "stair_1_6")
	_spawn_prefab(root, ch6, p_stairs, "StairsCh1ToCh6", Vector3(0.0, 0.0, -36.0))
	_spawn_crypt_ceiling(root, ch6, p_vault_corr, "StairsCh1ToCh6Ceil", Vector3(0.0, 0.0, -36.0), placed_ceilings)
	_spawn_crypt_wall(root, ch6, p_wall_solid, "StairsCh1ToCh6WallW_Upper", Vector3(-2.0, 0.0, -36.0), 90.0, placed_walls)
	_spawn_crypt_wall(root, ch6, p_wall_solid, "StairsCh1ToCh6WallE_Upper", Vector3(2.0, 0.0, -36.0), 90.0, placed_walls)
	_spawn_crypt_wall(root, ch6, p_wall_solid, "StairsCh1ToCh6WallW_Lower", Vector3(-2.0, -4.0, -36.0), 90.0, placed_walls)
	_spawn_crypt_wall(root, ch6, p_wall_solid, "StairsCh1ToCh6WallE_Lower", Vector3(2.0, -4.0, -36.0), 90.0, placed_walls)
	_spawn_prefab(root, ch6, p_lantern, "StairsCh1ToCh6Sconce", Vector3(0.0, 1.35, -37.65), 0.0)
	_add_chamber_light(root, ch6, "StairsCh1ToCh6BulkheadLight", Vector3(0.0, 0.85, -36.2), Color(1.0, 0.68, 0.32, 1.0), 1.65, 11.0)

	var ch6_xs: Array[float] = [-4.0, 0.0, 4.0]
	var ch6_zs: Array[float] = [-40.0, -44.0, -48.0, -52.0]
	for ix: int in range(ch6_xs.size()):
		for iz: int in range(ch6_zs.size()):
			var cx: float = ch6_xs[ix]
			var cz: float = ch6_zs[iz]
			var is_mirror_pool: bool = (ix != 1) and (iz == 1 or iz == 2)
			var tile_p: PackedScene = p_cistern if is_mirror_pool else p_floor
			_register_crypt_room_cell(occupied_cells, roundi(cx / 4.0), -1, roundi(cz / 4.0), "ch6")
			_spawn_crypt_floor(root, ch6, tile_p, "Ch6Floor_%d_%d" % [ix, iz], Vector3(cx, -4.0, cz), placed_floors)
			_spawn_crypt_ceiling(root, ch6, p_vault_corr, "Ch6Ceiling_%d_%d" % [ix, iz], Vector3(cx, -4.0, cz), placed_ceilings)

	for ix: int in range(ch6_xs.size()):
		var wx: float = ch6_xs[ix]
		if absf(wx) < 0.1:
			_spawn_crypt_wall(root, ch6, p_wall_door, "Ch6PortcullisSouth", Vector3(wx, -4.0, -38.0), 0.0, placed_walls)
			_spawn_crypt_wall(root, ch6, p_portcullis, "Ch6PortcullisNorthToCh8", Vector3(wx, -4.0, -54.0), 0.0, placed_walls)
		else:
			_spawn_crypt_wall(root, ch6, p_ossuary, "Ch6WallSouth_%d" % ix, Vector3(wx, -4.0, -38.0), 0.0, placed_walls)
			_spawn_crypt_wall(root, ch6, p_ossuary, "Ch6WallNorth_%d" % ix, Vector3(wx, -4.0, -54.0), 0.0, placed_walls)

	for iz: int in range(ch6_zs.size()):
		var wz: float = ch6_zs[iz]
		if absf(wz - (-52.0)) < 0.1:
			_spawn_crypt_wall(root, ch6, p_portcullis, "Ch6PortcullisWestToCh7Stairs", Vector3(-6.0, -4.0, wz), 90.0, placed_walls)
		else:
			_spawn_crypt_wall(root, ch6, p_ossuary, "Ch6WallWest_%d" % iz, Vector3(-6.0, -4.0, wz), 90.0, placed_walls)

		if absf(wz - (-44.0)) < 0.1:
			_spawn_crypt_wall(root, ch6, p_portcullis, "Ch6PortcullisEastToCh5", Vector3(6.0, -4.0, wz), 90.0, placed_walls)
		else:
			_spawn_crypt_wall(root, ch6, p_ossuary, "Ch6WallEast_%d" % iz, Vector3(6.0, -4.0, wz), 90.0, placed_walls)

	# Centerpiece crypt_weeping_statue_pedestal + solemn reflection columns (> 4.6m clear of Portal 6 at (-4.5, -4.0, -44.0))
	_spawn_prefab(root, ch6, p_weeping_saint, "Ch6WeepingSaintStatue", Vector3(0.0, -4.0, -46.0), 0.0)
	_spawn_prefab(root, ch6, p_pillar, "Ch6PillarW_0", Vector3(-2.6, -4.0, -39.8))
	_spawn_prefab(root, ch6, p_pillar, "Ch6PillarW_1", Vector3(-2.6, -4.0, -49.2))
	for pz_idx: int in range(3):
		var pz: float = -41.0 - float(pz_idx) * 5.0
		_spawn_prefab(root, ch6, p_pillar, "Ch6PillarE_%d" % pz_idx, Vector3(2.6, -4.0, pz))

	_add_chamber_light(root, ch6, "Ch6SpectralBlueLight_1", Vector3(0.0, -1.2, -45.5), Color(0.35, 0.65, 1.0, 1.0), 2.15, 15.0)
	_add_chamber_light(root, ch6, "Ch6SpectralBlueLight_2", Vector3(-3.5, -2.0, -46.5), Color(0.35, 0.65, 1.0, 1.0), 1.15, 10.0)
	_add_chamber_light(root, ch6, "Ch6SpectralBlueLight_3", Vector3(3.5, -2.0, -46.5), Color(0.35, 0.65, 1.0, 1.0), 1.15, 10.0)

	# ----------------------------------------------------------------------------------------------
	# CHAMBER 7 — The Vault of the Sunken Bell (South-West Deep Chasm | 16m x 16m double-height at Y = -8.0m, X in [-26m, -10m], Z in [-62m, -78m])
	# ----------------------------------------------------------------------------------------------
	var ch7: Node3D = Node3D.new()
	ch7.name = "Chamber7_VaultOfTheSunkenBell"
	crypt_container.add_child(ch7)
	ch7.owner = root

	# West gallery & deep staircase descending from Chamber 6 (Y = -4.0m) down to Chamber 7 (Y = -8.0m)
	_register_crypt_room_cell(occupied_cells, -2, -1, -13, "corr_6_7")
	_spawn_crypt_floor(root, ch7, p_floor, "CorrCh6To7Floor_1", Vector3(-8.0, -4.0, -52.0), placed_floors)
	_spawn_crypt_ceiling(root, ch7, p_vault_corr, "CorrCh6To7Ceil_1", Vector3(-8.0, -4.0, -52.0), placed_ceilings)

	_register_crypt_room_cell(occupied_cells, -2, -1, -14, "corr_6_7")
	_spawn_crypt_floor(root, ch7, p_floor, "CorrCh6To7Floor_2", Vector3(-8.0, -4.0, -56.0), placed_floors)
	_spawn_crypt_ceiling(root, ch7, p_vault_corr, "CorrCh6To7Ceil_2", Vector3(-8.0, -4.0, -56.0), placed_ceilings)

	_register_crypt_room_cell(occupied_cells, -3, -1, -14, "corr_6_7")
	_spawn_crypt_floor(root, ch7, p_floor, "CorrCh6To7Floor_3", Vector3(-12.0, -4.0, -56.0), placed_floors)
	_spawn_crypt_ceiling(root, ch7, p_vault_corr, "CorrCh6To7Ceil_3", Vector3(-12.0, -4.0, -56.0), placed_ceilings)
	_spawn_crypt_wall(root, ch7, p_portcullis, "CorrCh6To7PortcullisStairs", Vector3(-12.0, -4.0, -58.0), 0.0, placed_walls)

	# Register BOTH lower cell (-3, -2, -15) and upper headroom cell (-3, -1, -15) for StairsCh6ToCh7!
	_register_crypt_staircase_cells(occupied_cells, -3, -1, -15, "stair_6_7")
	_spawn_prefab(root, ch7, p_stairs, "StairsCh6ToCh7", Vector3(-12.0, -4.0, -60.0))
	_spawn_crypt_ceiling(root, ch7, p_vault_corr, "StairsCh6ToCh7Ceil", Vector3(-12.0, -4.0, -60.0), placed_ceilings)
	_spawn_prefab(root, ch7, p_lantern, "StairsCh6ToCh7Sconce", Vector3(-12.0, -2.65, -61.65), 0.0)
	_add_chamber_light(root, ch7, "StairsCh6ToCh7BulkheadLight", Vector3(-12.0, -3.15, -60.2), Color(1.0, 0.62, 0.28, 1.0), 1.65, 11.0)

	var ch7_xs: Array[float] = [-12.0, -16.0, -20.0, -24.0]
	var ch7_zs: Array[float] = [-64.0, -68.0, -72.0, -76.0]
	for ix: int in range(ch7_xs.size()):
		for iz: int in range(ch7_zs.size()):
			var cx: float = ch7_xs[ix]
			var cz: float = ch7_zs[iz]
			var gx: int = roundi(cx / 4.0)
			var gz: int = roundi(cz / 4.0)
			# Double-height 8m chamber registers BOTH gy = -2 and gy = -1!
			_register_crypt_room_cell(occupied_cells, gx, -2, gz, "ch7")
			_register_crypt_room_cell(occupied_cells, gx, -1, gz, "ch7")
			_spawn_crypt_floor(root, ch7, p_floor, "Ch7Floor_%d_%d" % [ix, iz], Vector3(cx, -8.0, cz), placed_floors)
			_spawn_crypt_ceiling(root, ch7, p_vault_corr, "Ch7Ceiling_%d_%d" % [ix, iz], Vector3(cx, -4.0, cz), placed_ceilings)

	# 2-tier stacked perimeter walls (Y = -8.0m and Y = -4.0m) for double-height 8m chasm
	for ix: int in range(ch7_xs.size()):
		var wx: float = ch7_xs[ix]
		if absf(wx - (-12.0)) < 0.1:
			_spawn_crypt_wall(root, ch7, p_wall_door, "Ch7PortcullisSouthStairs", Vector3(wx, -8.0, -62.0), 0.0, placed_walls)
			open_passages[_wall_grid_key(Vector3(-12.0, -4.0, -62.0))] = true
		else:
			_spawn_crypt_wall(root, ch7, p_wall_solid, "Ch7WallSouthLow_%d" % ix, Vector3(wx, -8.0, -62.0), 0.0, placed_walls)
			_spawn_crypt_wall(root, ch7, p_wall_solid, "Ch7WallSouthHigh_%d" % ix, Vector3(wx, -4.0, -62.0), 0.0, placed_walls)
		_spawn_crypt_wall(root, ch7, p_ossuary, "Ch7WallNorthLow_%d" % ix, Vector3(wx, -8.0, -78.0), 0.0, placed_walls)
		_spawn_crypt_wall(root, ch7, p_wall_solid, "Ch7WallNorthHigh_%d" % ix, Vector3(wx, -4.0, -78.0), 0.0, placed_walls)

	for iz: int in range(ch7_zs.size()):
		var wz: float = ch7_zs[iz]
		_spawn_crypt_wall(root, ch7, p_ossuary, "Ch7WallWestLow_%d" % iz, Vector3(-26.0, -8.0, wz), 90.0, placed_walls)
		_spawn_crypt_wall(root, ch7, p_wall_solid, "Ch7WallWestHigh_%d" % iz, Vector3(-26.0, -4.0, wz), 90.0, placed_walls)
		if absf(wz - (-72.0)) < 0.1:
			_spawn_crypt_wall(root, ch7, p_portcullis, "Ch7PortcullisEastToCh8", Vector3(-10.0, -8.0, wz), 90.0, placed_walls)
			_spawn_crypt_wall(root, ch7, p_wall_solid, "Ch7WallEastHighPortal_%d" % iz, Vector3(-10.0, -4.0, wz), 90.0, placed_walls)
		else:
			_spawn_crypt_wall(root, ch7, p_wall_solid, "Ch7WallEastLow_%d" % iz, Vector3(-10.0, -8.0, wz), 90.0, placed_walls)
			_spawn_crypt_wall(root, ch7, p_wall_solid, "Ch7WallEastHigh_%d" % iz, Vector3(-10.0, -4.0, wz), 90.0, placed_walls)

	# Colossal sunken bell centerpiece in floor crater + hanging gibbets + double-stacked pillars
	_spawn_prefab(root, ch7, p_sunken_bell, "Ch7SunkenBellCrater", Vector3(-18.0, -8.0, -70.0), 20.0)
	var ch7_corners: Array[Vector2] = [
		Vector2(-14.0, -66.0),
		Vector2(-22.0, -66.0),
		Vector2(-14.0, -74.0),
		Vector2(-22.0, -74.0)
	]
	for c_idx: int in range(ch7_corners.size()):
		var pt: Vector2 = ch7_corners[c_idx]
		_spawn_prefab(root, ch7, p_pillar, "Ch7PillarLow_%d" % c_idx, Vector3(pt.x, -8.0, pt.y))
		_spawn_prefab(root, ch7, p_pillar, "Ch7PillarHigh_%d" % c_idx, Vector3(pt.x, -4.0, pt.y))
		_spawn_prefab(root, ch7, p_gibbet, "Ch7GibbetLow_%d" % c_idx, Vector3(pt.x * 0.5 + (-18.0) * 0.5, -6.5, pt.y))
		_spawn_prefab(root, ch7, p_gibbet, "Ch7GibbetHigh_%d" % c_idx, Vector3(pt.x * 0.5 + (-18.0) * 0.5, -3.5, pt.y))

	_spawn_prefab(root, ch7, p_brazier, "Ch7Brazier_1", Vector3(-15.2, -8.0, -68.0))
	_spawn_prefab(root, ch7, p_brazier, "Ch7Brazier_2", Vector3(-20.8, -8.0, -68.0))
	_add_chamber_light(root, ch7, "Ch7SmolderingEmberLight", Vector3(-18.0, -5.2, -69.5), Color(1.0, 0.42, 0.14, 1.0), 2.25, 18.0)

	# ----------------------------------------------------------------------------------------------
	# CHAMBER 8 — The Abyssal Blood Sanctum (Grand Finale Ritual Vault | 20m x 20m double-height 8m ceiling at Y = -8.0m, X in [-10m, +10m], Z in [-62m, -82m])
	# ----------------------------------------------------------------------------------------------
	var ch8: Node3D = Node3D.new()
	ch8.name = "Chamber8_AbyssalBloodSanctum"
	crypt_container.add_child(ch8)
	ch8.owner = root

	# Grand descending processional stair from Chamber 6 (Z = -54m..-62m, Y = -4.0m -> -8.0m)
	# Register BOTH lower cell (0, -2, -14) and upper headroom cell (0, -1, -14) for StairsCh6ToCh8,
	# plus single-height processional landing (0, -2, -15) so the sealer places the Upper Bulkhead Wall at (0, -4, -58)!
	_register_crypt_staircase_cells(occupied_cells, 0, -1, -14, "stair_6_8")
	_spawn_prefab(root, ch8, p_stairs, "StairsCh6ToCh8", Vector3(0.0, -4.0, -56.0))
	_spawn_crypt_ceiling(root, ch8, p_vault_corr, "StairsCh6ToCh8Ceil_1", Vector3(0.0, -4.0, -56.0), placed_ceilings)

	_register_crypt_room_cell(occupied_cells, 0, -2, -15, "landing_6_8")
	open_passages[_wall_grid_key(Vector3(0.0, -8.0, -58.0))] = true
	_spawn_crypt_floor(root, ch8, p_floor, "LandingCh6ToCh8Floor", Vector3(0.0, -8.0, -60.0), placed_floors)
	_spawn_crypt_ceiling(root, ch8, p_vault_corr, "LandingCh6ToCh8Ceil", Vector3(0.0, -8.0, -60.0), placed_ceilings)
	for sz: float in [-56.0, -60.0]:
		_spawn_crypt_wall(root, ch8, p_wall_solid, "ProcessionalWallW_Low_%.0f" % absf(sz), Vector3(-2.0, -8.0, sz), 90.0, placed_walls)
		_spawn_crypt_wall(root, ch8, p_wall_solid, "ProcessionalWallE_Low_%.0f" % absf(sz), Vector3(2.0, -8.0, sz), 90.0, placed_walls)
	_spawn_crypt_wall(root, ch8, p_wall_solid, "ProcessionalWallW_High_56", Vector3(-2.0, -4.0, -56.0), 90.0, placed_walls)
	_spawn_crypt_wall(root, ch8, p_wall_solid, "ProcessionalWallE_High_56", Vector3(2.0, -4.0, -56.0), 90.0, placed_walls)
	_spawn_prefab(root, ch8, p_lantern, "StairsCh6ToCh8Sconce", Vector3(0.0, -2.65, -57.65), 0.0)
	_add_chamber_light(root, ch8, "StairsCh6ToCh8BulkheadLight", Vector3(0.0, -3.15, -56.2), Color(1.0, 0.55, 0.25, 1.0), 1.65, 11.0)

	var ch8_xs: Array[float] = [-8.0, -4.0, 0.0, 4.0, 8.0]
	var ch8_zs: Array[float] = [-64.0, -68.0, -72.0, -76.0, -80.0]
	for ix: int in range(ch8_xs.size()):
		for iz: int in range(ch8_zs.size()):
			var cx: float = ch8_xs[ix]
			var cz: float = ch8_zs[iz]
			var gx: int = roundi(cx / 4.0)
			var gz: int = roundi(cz / 4.0)
			_register_crypt_room_cell(occupied_cells, gx, -2, gz, "ch8")
			_register_crypt_room_cell(occupied_cells, gx, -1, gz, "ch8")
			_spawn_crypt_floor(root, ch8, p_floor, "Ch8Floor_%d_%d" % [ix, iz], Vector3(cx, -8.0, cz), placed_floors)
			_spawn_crypt_ceiling(root, ch8, p_vault_corr, "Ch8Ceiling_%d_%d" % [ix, iz], Vector3(cx, -4.0, cz), placed_ceilings)

	# 2-tier stacked perimeter walls around the 20m x 20m Abyssal Blood Sanctum
	for ix: int in range(ch8_xs.size()):
		var wx: float = ch8_xs[ix]
		if absf(wx) < 0.1:
			_spawn_crypt_wall(root, ch8, p_wall_door, "Ch8PortcullisSouthEntrance", Vector3(wx, -8.0, -62.0), 0.0, placed_walls)
			open_passages[_wall_grid_key(Vector3(0.0, -4.0, -62.0))] = true
		else:
			_spawn_crypt_wall(root, ch8, p_ossuary, "Ch8WallSouthLow_%d" % ix, Vector3(wx, -8.0, -62.0), 0.0, placed_walls)
			_spawn_crypt_wall(root, ch8, p_wall_solid, "Ch8WallSouthHigh_%d" % ix, Vector3(wx, -4.0, -62.0), 0.0, placed_walls)
		_spawn_crypt_wall(root, ch8, p_ossuary, "Ch8WallNorthLow_%d" % ix, Vector3(wx, -8.0, -82.0), 0.0, placed_walls)
		_spawn_crypt_wall(root, ch8, p_ossuary, "Ch8WallNorthHigh_%d" % ix, Vector3(wx, -4.0, -82.0), 0.0, placed_walls)

	for iz: int in range(ch8_zs.size()):
		var wz: float = ch8_zs[iz]
		_spawn_crypt_wall(root, ch8, p_ossuary, "Ch8WallEastLow_%d" % iz, Vector3(10.0, -8.0, wz), 90.0, placed_walls)
		_spawn_crypt_wall(root, ch8, p_wall_solid, "Ch8WallEastHigh_%d" % iz, Vector3(10.0, -4.0, wz), 90.0, placed_walls)
		if absf(wz - (-72.0)) > 0.1:
			_spawn_crypt_wall(root, ch8, p_ossuary, "Ch8WallWestLow_%d" % iz, Vector3(-10.0, -8.0, wz), 90.0, placed_walls)
			_spawn_crypt_wall(root, ch8, p_wall_solid, "Ch8WallWestHigh_%d" % iz, Vector3(-10.0, -4.0, wz), 90.0, placed_walls)

	# Double-stacked 8m tall crypt_pillar colonnade + 4 towering crypt_ritual_obelisk monoliths
	for pz_idx: int in range(3):
		var pz: float = -66.0 - float(pz_idx) * 6.0
		for sx: float in [-5.8, 5.8]:
			var side_tag: String = "W" if sx < 0.0 else "E"
			_spawn_prefab(root, ch8, p_pillar, "Ch8PillarLow_%s_%d" % [side_tag, pz_idx], Vector3(sx, -8.0, pz))
			_spawn_prefab(root, ch8, p_pillar, "Ch8PillarHigh_%s_%d" % [side_tag, pz_idx], Vector3(sx, -4.0, pz))

	_spawn_prefab(root, ch8, p_obelisk, "Ch8RitualObelisk_SW", Vector3(-3.6, -8.0, -68.5))
	_spawn_prefab(root, ch8, p_obelisk, "Ch8RitualObelisk_SE", Vector3(3.6, -8.0, -68.5))
	_spawn_prefab(root, ch8, p_obelisk, "Ch8RitualObelisk_NW", Vector3(-3.6, -8.0, -76.5))
	_spawn_prefab(root, ch8, p_obelisk, "Ch8RitualObelisk_NE", Vector3(3.6, -8.0, -76.5))

	# Elevated crypt_altar centerpiece encircled by standing_iron_brazier fire pits
	_spawn_prefab(root, ch8, p_altar, "Ch8AbyssalGrandAltar", Vector3(0.0, -8.0, -74.0))
	var brazier_ring: Array[Vector3] = [
		Vector3(-2.4, -8.0, -71.5),
		Vector3(2.4, -8.0, -71.5),
		Vector3(-3.0, -8.0, -74.5),
		Vector3(3.0, -8.0, -74.5),
		Vector3(-2.4, -8.0, -76.5),
		Vector3(2.4, -8.0, -76.5)
	]
	for b_idx: int in range(brazier_ring.size()):
		_spawn_prefab(root, ch8, p_brazier, "Ch8SanctumBrazier_%d" % b_idx, brazier_ring[b_idx])

	_add_chamber_light(root, ch8, "Ch8AbyssalCrimsonLight_Center", Vector3(0.0, -4.2, -73.0), Color(1.0, 0.15, 0.18, 1.0), 2.45, 22.0)
	_add_chamber_light(root, ch8, "Ch8AbyssalCrimsonLight_South", Vector3(0.0, -5.5, -66.0), Color(1.0, 0.15, 0.18, 1.0), 1.65, 16.0)
	_add_chamber_light(root, ch8, "Ch8AbyssalCrimsonLight_North", Vector3(0.0, -5.5, -78.5), Color(1.0, 0.15, 0.18, 1.0), 1.65, 16.0)

	# ----------------------------------------------------------------------------------------------
	# 6b. Execute Deterministic 3D Grid Voxel / Cell Sealer & Dark Exterior Crypt Hull Backup
	# ----------------------------------------------------------------------------------------------
	var sealer_container: Node3D = Node3D.new()
	sealer_container.name = "CryptShellSealer"
	crypt_container.add_child(sealer_container)
	sealer_container.owner = root

	_seal_crypt_grid_boundaries(
		root,
		sealer_container,
		p_floor,
		p_vault_corr,
		p_wall_solid,
		occupied_cells,
		placed_floors,
		placed_ceilings,
		placed_walls,
		open_passages
	)

	if p_containment_hull != null:
		_spawn_prefab(root, sealer_container, p_containment_hull, "CryptExteriorContainmentHull", Vector3.ZERO)

	# Physical wall lanterns for the two abandoned houses
	_spawn_prefab(root, structures_container, p_lantern, "LanternHouseA", Vector3(-12.8, 2.5, 12.8), -22.0)
	_spawn_prefab(root, structures_container, p_lantern, "LanternHouseB", Vector3(12.8, 2.8, 7.2), 158.0)

	# ----------------------------------------------------------------------------------------------
	# 6c. PHASE 4: Town Exterior Roadside Curbs, Street Lamps, Graveyard Fences & Gravestones
	# ----------------------------------------------------------------------------------------------
	var curb_zs: Array[float] = [20.0, 12.0, 4.0, -4.0]
	for cz_i: int in range(curb_zs.size()):
		var cz: float = curb_zs[cz_i]
		var road_cx: float = 1.2 * sin(cz * 0.09)
		for side_s: float in [-1.0, 1.0]:
			var curb_x: float = road_cx + side_s * 4.5
			var curb_y: float = _get_terrain_height(curb_x, cz)
			var side_tag: String = "W" if side_s < 0.0 else "E"
			_spawn_prefab(root, props_container, p_road_curb, "TownRoadCurb_%s_%d" % [side_tag, cz_i], Vector3(curb_x, curb_y, cz), 0.0)

	var lamp_coords: Array[Vector3] = [
		Vector3(-5.2, 0.0, 21.0),
		Vector3(5.6, 0.0, 15.0),
		Vector3(-5.0, 0.0, 7.5),
		Vector3(5.4, 0.0, 0.5),
		Vector3(-5.2, 0.0, -7.5),
		Vector3(5.2, 0.0, -7.5)
	]
	for l_i: int in range(lamp_coords.size()):
		var lpos: Vector3 = lamp_coords[l_i]
		lpos.y = _get_terrain_height(lpos.x, lpos.z)
		var l_rot: float = 90.0 if lpos.x < 0.0 else -90.0
		_spawn_prefab(root, props_container, p_street_lamp, "TownStreetLamp_%d" % l_i, lpos, l_rot)

	var fence_placements: Array[Vector4] = [
		Vector4(-10.5, 0.0, -10.5, 0.0),
		Vector4(10.5, 0.0, -10.5, 0.0),
		Vector4(-16.5, 0.0, -15.5, 90.0),
		Vector4(16.5, 0.0, -15.5, -90.0),
		Vector4(-16.5, 0.0, -21.5, 90.0),
		Vector4(16.5, 0.0, -21.5, -90.0)
	]
	for f_i: int in range(fence_placements.size()):
		var fp: Vector4 = fence_placements[f_i]
		var fy: float = _get_terrain_height(fp.x, fp.z)
		_spawn_prefab(root, props_container, p_graveyard_fence, "TownGraveyardFence_%d" % f_i, Vector3(fp.x, fy, fp.z), fp.w)

	var grave_coords: Array[Vector3] = [
		Vector3(-15.5, 0.0, -16.8),
		Vector3(-15.5, 0.0, -21.8),
		Vector3(15.5, 0.0, -16.8),
		Vector3(15.5, 0.0, -21.8),
		Vector3(-9.5, 0.0, 11.5),
		Vector3(12.2, 0.0, 2.5)
	]
	for g_i: int in range(grave_coords.size()):
		var gpos: Vector3 = grave_coords[g_i]
		gpos.y = _get_terrain_height(gpos.x, gpos.z)
		_spawn_prefab(root, props_container, p_gravestones, "TownGravestoneCluster_%d" % g_i, gpos, float((g_i * 45) % 360))

	# ----------------------------------------------------------------------------------------------
	# 6d. PHASE 4: Automated Clutter Scattering Pass (Church Outer Wings + 8 Crypt Chambers)
	#     (Dust motes are handled by the single player-attached DustMotesParticles emitter on FPSPlayer)
	# ----------------------------------------------------------------------------------------------
	# Church Outer Wing Clutter (keeping central processional carpet X in [-8.0, +8.0] 100% clear)
	_spawn_prefab(root, church, p_candles, "NaveCandles_SW", Vector3(-11.8, 0.0, -24.8), 25.0)
	_spawn_prefab(root, church, p_candles, "NaveCandles_SE", Vector3(11.8, 0.0, -24.8), -35.0)
	_spawn_prefab(root, church, p_candles, "NaveCandles_NW", Vector3(-11.6, 0.0, -54.6), 15.0)
	_spawn_prefab(root, church, p_candles, "NaveCandles_NE", Vector3(11.6, 0.0, -54.6), -15.0)
	_spawn_prefab(root, church, p_rubble_bones, "NaveRubble_NW", Vector3(-12.9, 0.0, -48.8), 40.0)
	_spawn_prefab(root, church, p_rubble_bones, "NaveRubble_NE", Vector3(12.9, 0.0, -48.8), -50.0)

	# Chamber 1 (The Antechamber of Bones, Y = 0.0m)
	_spawn_prefab(root, ch1, p_rubble_bones, "Ch1ClutterRubble_SW", Vector3(-4.6, 0.0, -23.4), 15.0)
	_spawn_prefab(root, ch1, p_rubble_bones, "Ch1ClutterRubble_SE", Vector3(4.6, 0.0, -23.4), -35.0)
	_spawn_prefab(root, ch1, p_candles, "Ch1ClutterCandles_W", Vector3(-2.6, 0.0, -25.2), 0.0)
	_spawn_prefab(root, ch1, p_candles, "Ch1ClutterCandles_E", Vector3(2.6, 0.0, -25.2), 90.0)
	_spawn_prefab(root, ch1, p_crates_barrels, "Ch1ClutterCrates_NE", Vector3(4.7, 0.0, -24.4), -20.0)
	_spawn_prefab(root, ch1, p_chains_roots, "Ch1CeilingRoots_1", Vector3(-3.5, 3.85, -26.5), 30.0)
	_spawn_prefab(root, ch1, p_chains_roots, "Ch1CeilingRoots_2", Vector3(3.5, 3.85, -30.0), -45.0)

	# Chamber 2 (The Hall of Sarcophagi, Y = 0.0m)
	_spawn_prefab(root, ch2, p_rubble_bones, "Ch2ClutterRubble_1", Vector3(-11.4, 0.0, -23.4), 22.0)
	_spawn_prefab(root, ch2, p_rubble_bones, "Ch2ClutterRubble_2", Vector3(-24.4, 0.0, -36.4), 115.0)
	_spawn_prefab(root, ch2, p_candles, "Ch2ClutterCandles_1", Vector3(-15.5, 0.0, -25.2), 10.0)
	_spawn_prefab(root, ch2, p_candles, "Ch2ClutterCandles_2", Vector3(-20.5, 0.0, -34.8), -40.0)
	_spawn_prefab(root, ch2, p_chains_roots, "Ch2CeilingRoots_1", Vector3(-15.8, 3.85, -30.0), 0.0)
	_spawn_prefab(root, ch2, p_chains_roots, "Ch2CeilingRoots_2", Vector3(-21.2, 3.85, -30.0), 75.0)

	# Chamber 3 (The Whispering Reliquary & Forbidden Library, Y = 0.0m)
	_spawn_prefab(root, ch3, p_candles, "Ch3ClutterCandles_1", Vector3(-14.2, 0.0, -45.5), 0.0)
	_spawn_prefab(root, ch3, p_candles, "Ch3ClutterCandles_2", Vector3(-17.8, 0.0, -45.5), 45.0)
	_spawn_prefab(root, ch3, p_candles, "Ch3ClutterCandles_3", Vector3(-14.5, 0.0, -53.8), -30.0)
	_spawn_prefab(root, ch3, p_crates_barrels, "Ch3ClutterCrates_SW", Vector3(-20.2, 0.0, -43.4), 12.0)
	_spawn_prefab(root, ch3, p_rubble_bones, "Ch3ClutterRubble_SE", Vector3(-11.8, 0.0, -43.4), -25.0)
	_spawn_prefab(root, ch3, p_chains_roots, "Ch3CeilingRoots_1", Vector3(-16.0, 3.85, -47.0), 20.0)

	# Chamber 4 (The Inquisitor's Gaol & Gibbet Cells, Y = 0.0m)
	_spawn_prefab(root, ch4, p_rubble_bones, "Ch4ClutterRubble_1", Vector3(12.2, 0.0, -23.5), 0.0)
	_spawn_prefab(root, ch4, p_rubble_bones, "Ch4ClutterRubble_2", Vector3(20.2, 0.0, -32.5), 85.0)
	_spawn_prefab(root, ch4, p_crates_barrels, "Ch4ClutterCrates_E", Vector3(24.4, 0.0, -23.6), -45.0)
	_spawn_prefab(root, ch4, p_candles, "Ch4ClutterCandles_W", Vector3(11.4, 0.0, -26.5), 15.0)
	_spawn_prefab(root, ch4, p_chains_roots, "Ch4CeilingRoots_1", Vector3(16.0, 3.85, -28.0), 40.0)
	_spawn_prefab(root, ch4, p_chains_roots, "Ch4CeilingRoots_2", Vector3(22.0, 3.85, -28.0), -30.0)

	# Chamber 5 (The Alchemical Plague Cistern, Y = -4.0m)
	_spawn_prefab(root, ch5, p_crates_barrels, "Ch5ClutterCrates_NW", Vector3(11.6, -4.0, -52.2), 30.0)
	_spawn_prefab(root, ch5, p_crates_barrels, "Ch5ClutterCrates_SE", Vector3(24.4, -4.0, -41.5), -60.0)
	_spawn_prefab(root, ch5, p_rubble_bones, "Ch5ClutterRubble_NE", Vector3(24.2, -4.0, -52.4), 50.0)
	_spawn_prefab(root, ch5, p_candles, "Ch5ClutterCandles_1", Vector3(14.2, -4.0, -40.8), 0.0)
	_spawn_prefab(root, ch5, p_chains_roots, "Ch5CeilingRoots_1", Vector3(18.0, -0.15, -42.0), 15.0)
	_spawn_prefab(root, ch5, p_chains_roots, "Ch5CeilingRoots_2", Vector3(18.0, -0.15, -50.0), -65.0)

	# Chamber 6 (The Cenotaph of the Weeping Saint, Y = -4.0m)
	_spawn_prefab(root, ch6, p_candles, "Ch6ClutterCandles_1", Vector3(-1.6, -4.0, -45.2), 18.0)
	_spawn_prefab(root, ch6, p_candles, "Ch6ClutterCandles_2", Vector3(1.6, -4.0, -45.2), -18.0)
	_spawn_prefab(root, ch6, p_candles, "Ch6ClutterCandles_3", Vector3(-1.8, -4.0, -48.5), 40.0)
	_spawn_prefab(root, ch6, p_candles, "Ch6ClutterCandles_4", Vector3(1.8, -4.0, -48.5), -40.0)
	_spawn_prefab(root, ch6, p_rubble_bones, "Ch6ClutterRubble_SW", Vector3(-4.5, -4.0, -39.5), 10.0)
	_spawn_prefab(root, ch6, p_rubble_bones, "Ch6ClutterRubble_SE", Vector3(4.5, -4.0, -39.5), -25.0)
	_spawn_prefab(root, ch6, p_chains_roots, "Ch6CeilingRoots_1", Vector3(0.0, -0.15, -43.0), 0.0)

	# Chamber 7 (The Vault of the Sunken Bell, Y = -8.0m)
	_spawn_prefab(root, ch7, p_rubble_bones, "Ch7ClutterRubble_1", Vector3(-15.5, -8.0, -66.5), 15.0)
	_spawn_prefab(root, ch7, p_rubble_bones, "Ch7ClutterRubble_2", Vector3(-20.5, -8.0, -73.5), 110.0)
	_spawn_prefab(root, ch7, p_rubble_bones, "Ch7ClutterRubble_3", Vector3(-24.2, -8.0, -64.2), -45.0)
	_spawn_prefab(root, ch7, p_crates_barrels, "Ch7ClutterCrates_NW", Vector3(-24.4, -8.0, -76.2), 25.0)
	_spawn_prefab(root, ch7, p_candles, "Ch7ClutterCandles_1", Vector3(-14.8, -8.0, -71.5), 0.0)
	_spawn_prefab(root, ch7, p_chains_roots, "Ch7CeilingRoots_1", Vector3(-18.0, -0.15, -67.0), 30.0)
	_spawn_prefab(root, ch7, p_chains_roots, "Ch7CeilingRoots_2", Vector3(-18.0, -0.15, -73.0), -50.0)

	# Chamber 8 (The Abyssal Blood Sanctum, Y = -8.0m)
	_spawn_prefab(root, ch8, p_candles, "Ch8ClutterCandles_SW", Vector3(-4.2, -8.0, -69.5), 25.0)
	_spawn_prefab(root, ch8, p_candles, "Ch8ClutterCandles_SE", Vector3(4.2, -8.0, -69.5), -25.0)
	_spawn_prefab(root, ch8, p_candles, "Ch8ClutterCandles_NW", Vector3(-4.2, -8.0, -75.5), 45.0)
	_spawn_prefab(root, ch8, p_candles, "Ch8ClutterCandles_NE", Vector3(4.2, -8.0, -75.5), -45.0)
	_spawn_prefab(root, ch8, p_rubble_bones, "Ch8ClutterRubble_W", Vector3(-8.4, -8.0, -65.0), 15.0)
	_spawn_prefab(root, ch8, p_rubble_bones, "Ch8ClutterRubble_E", Vector3(8.4, -8.0, -65.0), -35.0)
	_spawn_prefab(root, ch8, p_rubble_bones, "Ch8ClutterRubble_N", Vector3(-7.8, -8.0, -80.4), 70.0)
	_spawn_prefab(root, ch8, p_crates_barrels, "Ch8ClutterCrates_NE", Vector3(8.2, -8.0, -80.2), -30.0)
	_spawn_prefab(root, ch8, p_chains_roots, "Ch8CeilingRoots_1", Vector3(-3.5, -0.15, -70.0), 0.0)
	_spawn_prefab(root, ch8, p_chains_roots, "Ch8CeilingRoots_2", Vector3(3.5, -0.15, -70.0), 90.0)
	_spawn_prefab(root, ch8, p_chains_roots, "Ch8CeilingRoots_3", Vector3(0.0, -0.15, -76.5), 45.0)

	# ----------------------------------------------------------------------------------------------
	# 6e. PHASE 2 & 4: 8 Symmetrically Centered, 0.76x-Scaled Occult Rift Portals (> 3.6m Pillar Clearance)
	#     & ProceduralExpeditionRoot (ProceduralDungeonGenerator at Y = -500.0m)
	# ----------------------------------------------------------------------------------------------
	var proc_gen_script: Script = load("res://scripts/world/procedural_dungeon_generator.gd") as Script
	var proc_root: Node3D = Node3D.new()
	proc_root.name = "ProceduralExpeditionRoot"
	if proc_gen_script != null:
		proc_root.set_script(proc_gen_script)
	root.add_child(proc_root)
	proc_root.owner = root

	_spawn_chamber_portal(
		root,
		ch1,
		p_rift_portal,
		"Portal_Biome1_EndlessOssuary",
		Vector3(4.2, 0.0, -32.5),
		0.0,
		1,
		"The Endless Ossuary",
		Color(1.0, 0.65, 0.28, 1.0),
		Vector3(4.0, 0.5, -57.5)
	)
	_spawn_chamber_portal(
		root,
		ch2,
		p_rift_portal,
		"Portal_Biome2_RoyalNecropolis",
		Vector3(-24.5, 0.0, -30.0),
		90.0,
		2,
		"The Royal Necropolis",
		Color(1.0, 0.75, 0.35, 1.0),
		Vector3(-20.5, 0.5, -58.0)
	)
	_spawn_chamber_portal(
		root,
		ch3,
		p_rift_portal,
		"Portal_Biome3_InfiniteReliquary",
		Vector3(-16.0, 0.0, -56.5),
		0.0,
		3,
		"The Infinite Reliquary",
		Color(0.82, 0.40, 1.0, 1.0),
		Vector3(-16.0, 0.5, -81.0)
	)
	_spawn_chamber_portal(
		root,
		ch4,
		p_rift_portal,
		"Portal_Biome4_InquisitorsLabyrinth",
		Vector3(24.5, 0.0, -28.0),
		-90.0,
		4,
		"The Inquisitor's Labyrinth",
		Color(0.75, 0.55, 0.40, 1.0),
		Vector3(21.0, 0.5, -56.0)
	)
	_spawn_chamber_portal(
		root,
		ch5,
		p_rift_portal,
		"Portal_Biome5_BlightedCisterns",
		Vector3(18.0, -4.0, -52.5),
		0.0,
		5,
		"The Blighted Cisterns",
		Color(0.42, 0.95, 0.32, 1.0),
		Vector3(18.0, -3.5, -77.0)
	)
	_spawn_chamber_portal(
		root,
		ch6,
		p_rift_portal,
		"Portal_Biome6_WeepingSaintHalls",
		Vector3(-4.5, -4.0, -44.0),
		90.0,
		6,
		"The Halls of the Weeping Saint",
		Color(0.32, 0.68, 1.0, 1.0),
		Vector3(-1.5, -3.5, -72.0)
	)
	_spawn_chamber_portal(
		root,
		ch7,
		p_rift_portal,
		"Portal_Biome7_ShatteredBellChasms",
		Vector3(-18.0, -8.0, -76.5),
		0.0,
		7,
		"The Shattered Bell Chasms",
		Color(1.0, 0.42, 0.15, 1.0),
		Vector3(-18.0, -7.5, -101.0)
	)
	_spawn_chamber_portal(
		root,
		ch8,
		p_rift_portal,
		"Portal_Biome8_AbyssalBloodWastes",
		Vector3(0.0, -8.0, -80.5),
		0.0,
		8,
		"The Abyssal Blood Wastes",
		Color(1.0, 0.14, 0.18, 1.0),
		Vector3(0.0, -7.5, -105.0)
	)

	# 7. Lighting: DirectionalLight3D Moonlight aligned with blood moon (Phase 5.1: 38m shadow distance, 2-split cascades)
	var moon: DirectionalLight3D = DirectionalLight3D.new()
	moon.name = "MoonDirectionalLight"
	moon.look_at_from_position(Vector3(12.0, 48.0, -87.0), Vector3.ZERO, Vector3.UP)
	moon.light_color = Color(0.72, 0.70, 0.88, 1.0)
	moon.light_energy = 0.65
	moon.shadow_enabled = true
	moon.directional_shadow_max_distance = 38.0
	moon.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
	lighting_container.add_child(moon)
	moon.owner = root

	# 8. First-Person Player instance on the valley path facing North (-Z) toward the hilltop church
	_spawn_prefab(root, root, p_player, "Player", Vector3(0.0, 0.65, 24.0))

	# 9. Dynamic 3-Zone Ambient Soundscape Controller
	var soundscape_script: Script = load("res://scripts/environment/ambient_soundscape_controller.gd") as Script
	if soundscape_script != null:
		var soundscape: Node3D = Node3D.new()
		soundscape.name = "AmbientSoundscape"
		soundscape.set_script(soundscape_script)
		root.add_child(soundscape)
		soundscape.owner = root

	_save_packed_scene(root, "res://scenes/levels/town_overworld.tscn")


func _spawn_chamber_portal(
	scene_root: Node3D,
	parent: Node3D,
	portal_scene: PackedScene,
	inst_name: String,
	pos: Vector3,
	rot_y_deg: float,
	b_id: int,
	b_title: String,
	tint: Color,
	ret_dest: Vector3
) -> Node3D:
	if portal_scene == null:
		return null
	var inst: Node3D = _spawn_prefab(scene_root, parent, portal_scene, inst_name, pos, rot_y_deg)
	if inst != null:
		inst.scale = Vector3(0.76, 0.76, 0.76)
		inst.set("biome_id", b_id)
		inst.set("biome_title", b_title)
		inst.set("portal_tint", tint)
		inst.set("is_return_portal", false)
		inst.set("return_destination", ret_dest)
		inst.set("depth_tier", 1)
	return inst
