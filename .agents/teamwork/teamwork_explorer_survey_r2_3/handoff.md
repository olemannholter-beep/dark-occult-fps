# Survey Report — Feature 5 (Weapon Recoil), Feature 6 (Micro-Voxel Enemies & Loot), and Feature 7 (CLI Verification)

**Author**: Survey Explorer 3 (`teamwork_explorer_survey_r2_3`)  
**Mission**: Investigate and produce surgical implementation specifications for Features 5, 6, and 7 adhering strictly to `AGENTS.md` (Godot 4.7 static typing, <= 250 line surgical edits, zero `uid://` fabrication).

---

## 1. Observation

### 1.1 Feature 5: Procedural Weapon Recoil in `fps_viewmodel_controller.gd`
- **File**: `c:\Users\olema\Downloads\alpha branch\scripts\player\fps_viewmodel_controller.gd` (Total Lines: 2299).
- **Line 8**: `@export var right_hand_pivot: Node3D` is the container node holding `WeaponRevolver`, `WeaponShotgun`, and `WeaponStakeDriver`.
- **Lines 123–133**: Spring recoil member variables:
  ```gdscript
  var recoil_pos: Vector3 = Vector3.ZERO
  var recoil_vel: Vector3 = Vector3.ZERO
  var recoil_rot: Vector3 = Vector3.ZERO
  var recoil_rot_vel: Vector3 = Vector3.ZERO

  var recoil_offset_pos: Vector3 = Vector3.ZERO
  var recoil_offset_rot: Vector3 = Vector3.ZERO
  var left_recoil_offset_pos: Vector3 = Vector3.ZERO
  var left_recoil_vel: Vector3 = Vector3.ZERO
  ```
  Neither `_weapon_mount_recoil_pos`, `_weapon_mount_recoil_rot`, nor `_weapon_recoil_tween` currently exist.
- **Lines 926–933**: `add_recoil_impulse(pos_impulse, rot_impulse)` applies additive impulse to `recoil_pos` / `recoil_rot` and steps the 6-DOF spring solver.
- **Lines 996–1002**: `_apply_hand_transforms()` sets `right_hand_pivot.position` and `rotation`:
  ```gdscript
  func _apply_hand_transforms() -> void:
      recoil_offset_pos = recoil_pos
      recoil_offset_rot = recoil_rot
      if right_hand_pivot != null:
          right_hand_pivot.position = right_base_pos + sway_pos + bob_pos + recoil_pos + _tuck_offset
          right_hand_pivot.rotation = right_base_rot + sway_rot + bob_rot + recoil_rot + Vector3(_tuck_rot_x, 0.0, 0.0)
  ```
  `right_hand_pivot` currently lacks any dedicated mount recoil offset.
- **Lines 1516–1518** (`_fire_revolver()`):
  ```gdscript
  var pos_kick: Vector3 = Vector3(_non_zero_signed_range(0.004, 0.015), 0.035, 0.085) * recoil_mult
  add_recoil_impulse(pos_kick, Vector3(pitch_kick, yaw_kick, roll_kick))
  ```
- **Lines 1585–1587** (`_fire_shotgun()`):
  ```gdscript
  var pos_kick: Vector3 = Vector3(_non_zero_signed_range(0.008, 0.025), 0.055, 0.14) * recoil_mult
  add_recoil_impulse(pos_kick, Vector3(pitch_kick, yaw_kick, roll_kick))
  ```
- **Lines 1731–1733** (`_fire_stakedriver()`):
  ```gdscript
  var pos_kick: Vector3 = Vector3(_non_zero_signed_range(0.005, 0.018), 0.04, 0.13) * recoil_mult
  add_recoil_impulse(pos_kick, Vector3(pitch_kick, yaw_kick, roll_kick))
  ```

---

### 1.2 Feature 6: Micro-Voxelization of Enemies & Loot Flasks

#### A. Enemy Builder: `tools/blender_build_voxel_enemies.py` (Total Lines: 1261)
- **Lines 130–205**: The procedural primitives use smooth curves:
  - `make_cyl()` at line 140: `bpy.ops.mesh.primitive_cylinder_add(vertices=verts, ...)`
  - `make_cone()` at line 164: `bpy.ops.mesh.primitive_cone_add(vertices=verts, ...)`
  - `make_torus()` at line 180: `bpy.ops.mesh.primitive_torus_add(major_segments=14, minor_segments=8, ...)`
  - `make_sphere()` at line 199: `bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, ...)`
- **Lines 242–287**: `join_into_hierarchy_node()` takes `parts: list[bpy.types.Object]`, applies transforms, executes `bpy.ops.object.join()`, shifts origin to `pivot_world`, and runs `bake_3tone_gothic_vertex_colors(joined)`.
- **Experimental Test Result (Blender 5.4.0 Alpha)**:
  - Applying `REMESH` (`mode='BLOCKS'`) on a joined multi-material object **resets all polygon material indices to 0** (`Mat indices: {0}`).
  - Applying `REMESH` (`mode='BLOCKS'`) on each primitive **before** joining retains each primitive's unique material, and subsequent `bpy.ops.object.join()` correctly merges material slots and preserves all polygon material assignments (`Joined mat indices: {0, 1, 2}`).
  - Bounding box scaling test: on an object of dimension `L = 0.10m` to `0.30m`, calculating `octree_depth = max(3, min(7, int(math.ceil(math.log2(L / 0.010)))))` produces exactly 8mm–12mm cubic micro-voxels without ballooning polygon counts.
- **Lines 766–809** (`build_enemy_01_ossuary_executioner()`): Generates `enemy_01_ossuary_executioner.glb`. Uses `make_sphere` for pauldron skulls/eyes, `make_cyl`, `make_sphere`, and `make_cone` on cleaver hilts, pommels, and saw teeth.
- **Lines 871–918** (`build_enemy_03_reliquary_hexweaver()`): Generates `enemy_03_reliquary_hexweaver.glb`. Uses `make_cyl` for scroll tubes, `make_torus` for brass astrolabe rings, `make_sphere` for floating grimoire orbs and staff core, `make_cone` for scholar cowl peak.

#### B. Loot Town Builder: `tools/blender_build_voxel_town_and_loot.py` (Total Lines: 1545)
- **Lines 1063–1130** (`build_loot_alchemical_elixir()`): Uses `_add_bm_beveled_box` directly into `bm`. It produces a beveled core, but can be updated to follow structured 8mm–10mm micro-voxel concentric tiered steps (`Base`, `FlaskBelly`, `Shoulder`, `NeckCollar`, `LipCork`) with flat shading and baked cavity vertex colors.

#### C. Fallback Pickup Mesh: `scripts/items/loot_drop_pickup.gd` (Total Lines: 355)
- **Line 27**: `static var _shared_crystal_mesh: SphereMesh = null`
- **Lines 39–45**:
  ```gdscript
  if _shared_crystal_mesh == null:
      # Low-segment faceted octahedron/crystal (radial_segments=6, rings=2 -> crisp faceted gem, 0.26m tall)
      _shared_crystal_mesh = SphereMesh.new()
      _shared_crystal_mesh.radius = 0.11
      _shared_crystal_mesh.height = 0.26
      _shared_crystal_mesh.radial_segments = 6
      _shared_crystal_mesh.rings = 2
  ```
  Uses `SphereMesh`, which violates the zero-smooth-primitive rule for micro-voxel loot.

---

### 1.3 Feature 7: CLI Verification Commands
- **Local Godot 4.7.2 Console Binary**:
  `c:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe`
- **Verification Run (Baseline)**:
  ```powershell
  & "c:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --path . --check-only -s res://scripts/player/fps_viewmodel_controller.gd
  & "c:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --path . --check-only -s res://scripts/items/loot_drop_pickup.gd
  ```
  **Result**: Both exited with code `0`.
- **Local Blender 5.4 Binary**:
  `C:\Users\olema\Downloads\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender.exe`

---

## 2. Logic Chain

1. **Procedural Recoil Kick and Snap-Back**:
   - The user requested a snappy procedural recoil kick on right-hand FPS weapon mount whenever firing (`position.z += 0.055`, `rotation.x += deg_to_rad(5.5)`, snap back over `0.14s`).
   - In Godot's coordinate system, `-Z` is forward and `+Z` is toward the camera/player. Therefore, adding `+0.055` kicks the weapon directly back into the player's shoulder/chest.
   - Positive X rotation pitches the front of the weapon upward. `deg_to_rad(5.5)` creates an authentic muzzle rise.
   - Integrating `_weapon_mount_recoil_pos` and `_weapon_mount_recoil_rot` directly into `_apply_hand_transforms()` guarantees that all existing camera sway, walk-bob, wall tuck, and 6-DOF spring dynamics continue to function without interference.
   - Using a dedicated `Tween` that kills any existing tween (`if _weapon_recoil_tween != null and _weapon_recoil_tween.is_valid(): _weapon_recoil_tween.kill()`) and snaps back over `0.14s` with `TRANS_CUBIC` and `EASE_OUT` prevents additive drift during rapid firing.

2. **Micro-Voxelization of Enemies while Preserving Articulated Hierarchy**:
   - `OccultEnemyAI` dynamically resolves the 7+ hierarchy nodes (`Pelvis`, `Torso`, `Head`, `UpperArmL`, `ForearmL`, `UpperArmR`, `ForearmR`, `ThighL`, `ShinL`, `ThighR`, `ShinR`, `SecondaryProp`).
   - If we voxelize each primitive (`make_cyl`, `make_cone`, `make_torus`, `make_sphere`) via `REMESH` (`mode='BLOCKS'`) **before** `join_into_hierarchy_node()` joins them:
     - Each primitive retains its individual single material (`WroughtIron`, `AgedBone`, `TarnishedBronze`, `EmissiveAmberFlame`, `GlowingOccultRune`).
     - `bpy.ops.object.join()` then joins them cleanly with all material slots intact.
     - The hierarchy node pivots and parent-child transforms remain 100% unaltered.
     - Smooth cylinder/sphere curvature is eliminated, replaced by stepped 8mm–12mm micro-voxels.

3. **Elimination of `SphereMesh` in Loot Drops**:
   - `LootDropPickup` currently instantiates a `SphereMesh` for `_shared_crystal_mesh`.
   - Changing `_shared_crystal_mesh` type to `Mesh` and generating an `ArrayMesh` via `SurfaceTool` with stepped cubic boxes (`_add_micro_voxel_box`) produces a clean, sharp micro-voxel crystal/flask cluster with flat normals.
   - This complies with Rule 7.3 (STRICT BAN on smooth Godot primitive meshes for game props).

---

## 3. Caveats

1. **Blender Execution Locking**:
   - `blender_build_voxel_enemies.py` and `blender_build_voxel_town_and_loot.py` write to `res://assets/models/enemies/` and `res://assets/models/items/`. Headless Blender processes should not be executed concurrently if another agent is modifying the same output folders.
2. **Godot Headless Import Requirement**:
   - After updating `.glb` files via Blender, a headless Godot import pass (`godot --headless --quit-after 240 --path . --import`) must run before Godot scene checks can resolve the new mesh geometry.
3. **Tween Object Lifetime**:
   - In GDScript 4.7, calling `_weapon_recoil_tween.kill()` requires checking `_weapon_recoil_tween != null and _weapon_recoil_tween.is_valid()`.

---

## 4. Conclusion & Surgical Implementation Blueprint

### 4.1 Target 1: `res://scripts/player/fps_viewmodel_controller.gd`

#### Edit 1A: Declare recoil variables
- **Location**: Near line 133
- **Before**:
  ```gdscript
  var left_recoil_offset_pos: Vector3 = Vector3.ZERO
  var left_recoil_vel: Vector3 = Vector3.ZERO

  var _tuck_offset: Vector3 = Vector3.ZERO
  ```
- **After**:
  ```gdscript
  var left_recoil_offset_pos: Vector3 = Vector3.ZERO
  var left_recoil_vel: Vector3 = Vector3.ZERO

  var _weapon_mount_recoil_pos: Vector3 = Vector3.ZERO
  var _weapon_mount_recoil_rot: Vector3 = Vector3.ZERO
  var _weapon_recoil_tween: Tween = null

  var _tuck_offset: Vector3 = Vector3.ZERO
  ```

#### Edit 1B: Add `trigger_shoot_recoil()` method
- **Location**: After `add_recoil_impulse` (around line 933)
- **Insert**:
  ```gdscript
  func trigger_shoot_recoil(intensity: float = 1.0) -> void:
  	if _weapon_recoil_tween != null and _weapon_recoil_tween.is_valid():
  		_weapon_recoil_tween.kill()

  	_weapon_mount_recoil_pos = Vector3(0.0, 0.0, 0.055 * intensity)
  	_weapon_mount_recoil_rot = Vector3(deg_to_rad(5.5 * intensity), 0.0, 0.0)
  	_apply_hand_transforms()

  	_weapon_recoil_tween = create_tween()
  	_weapon_recoil_tween.set_parallel(true)
  	_weapon_recoil_tween.tween_property(self, "_weapon_mount_recoil_pos", Vector3.ZERO, 0.14).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
  	_weapon_recoil_tween.tween_property(self, "_weapon_mount_recoil_rot", Vector3.ZERO, 0.14).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
  ```

#### Edit 1C: Apply offset in `_apply_hand_transforms()`
- **Location**: Around lines 996–1002
- **Before**:
  ```gdscript
  func _apply_hand_transforms() -> void:
  	recoil_offset_pos = recoil_pos
  	recoil_offset_rot = recoil_rot
  	if right_hand_pivot != null:
  		right_hand_pivot.position = right_base_pos + sway_pos + bob_pos + recoil_pos + _tuck_offset
  		right_hand_pivot.rotation = right_base_rot + sway_rot + bob_rot + recoil_rot + Vector3(_tuck_rot_x, 0.0, 0.0)
  ```
- **After**:
  ```gdscript
  func _apply_hand_transforms() -> void:
  	recoil_offset_pos = recoil_pos
  	recoil_offset_rot = recoil_rot
  	if right_hand_pivot != null:
  		right_hand_pivot.position = right_base_pos + sway_pos + bob_pos + recoil_pos + _tuck_offset + _weapon_mount_recoil_pos
  		right_hand_pivot.rotation = right_base_rot + sway_rot + bob_rot + recoil_rot + Vector3(_tuck_rot_x, 0.0, 0.0) + _weapon_mount_recoil_rot
  ```

#### Edit 1D: Trigger recoil in weapon fire functions
- In `_fire_revolver()` (line 1517):
  ```gdscript
  	add_recoil_impulse(pos_kick, Vector3(pitch_kick, yaw_kick, roll_kick))
  	trigger_shoot_recoil(1.0)
  ```
- In `_fire_shotgun()` (line 1586):
  ```gdscript
  	add_recoil_impulse(pos_kick, Vector3(pitch_kick, yaw_kick, roll_kick))
  	trigger_shoot_recoil(1.35)
  ```
- In `_fire_stakedriver()` (line 1732):
  ```gdscript
  	add_recoil_impulse(pos_kick, Vector3(pitch_kick, yaw_kick, roll_kick))
  	trigger_shoot_recoil(1.2)
  ```

---

### 4.2 Target 2: `res://tools/blender_build_voxel_enemies.py`

#### Edit 2A: Add `remesh_to_micro_voxels()` and update primitives
- **Location**: Replace lines 128–206 in `tools/blender_build_voxel_enemies.py`.
- **Implementation**:
  ```python
  def remesh_to_micro_voxels(obj: bpy.types.Object, voxel_size: float = 0.010) -> bpy.types.Object:
      """Converts smooth primitives to crisp 8mm-12mm micro-voxel blocks with flat shading."""
      bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
      dim_max = max(obj.dimensions)
      if dim_max < 0.008:
          return obj
      n_blocks = max(2, int(round(dim_max / voxel_size)))
      depth = max(3, min(7, int(math.ceil(math.log2(n_blocks)))))
      rem = obj.modifiers.new(name="MicroVoxelBlocks", type='REMESH')
      rem.mode = 'BLOCKS'
      rem.octree_depth = depth
      rem.scale = 0.90
      rem.use_remove_disconnected = False
      rem.use_smooth_shade = False
      bpy.context.view_layer.objects.active = obj
      obj.select_set(True)
      bpy.ops.object.modifier_apply(modifier=rem.name)
      return obj


  def make_cyl(
      name: str,
      loc: tuple[float, float, float],
      radius: float,
      depth: float,
      mat: bpy.types.Material,
      rot: tuple[float, float, float] = (0.0, 0.0, 0.0),
      verts: int = 12,
      bevel: float = 0.006,
  ) -> bpy.types.Object:
      bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=loc, rotation=rot)
      obj = bpy.context.active_object
      obj.name = name
      obj.data.materials.append(mat)
      remesh_to_micro_voxels(obj, voxel_size=0.010)
      return obj


  def make_cone(
      name: str,
      loc: tuple[float, float, float],
      r1: float,
      r2: float,
      depth: float,
      mat: bpy.types.Material,
      rot: tuple[float, float, float] = (0.0, 0.0, 0.0),
      verts: int = 10,
  ) -> bpy.types.Object:
      bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=depth, location=loc, rotation=rot)
      obj = bpy.context.active_object
      obj.name = name
      obj.data.materials.append(mat)
      remesh_to_micro_voxels(obj, voxel_size=0.010)
      return obj


  def make_torus(
      name: str,
      loc: tuple[float, float, float],
      major_r: float,
      minor_r: float,
      mat: bpy.types.Material,
      rot: tuple[float, float, float] = (0.0, 0.0, 0.0),
  ) -> bpy.types.Object:
      bpy.ops.mesh.primitive_torus_add(
          major_segments=14, minor_segments=8,
          major_radius=major_r, minor_radius=minor_r,
          location=loc, rotation=rot,
      )
      obj = bpy.context.active_object
      obj.name = name
      obj.data.materials.append(mat)
      remesh_to_micro_voxels(obj, voxel_size=0.010)
      return obj


  def make_sphere(
      name: str,
      loc: tuple[float, float, float],
      radius: float,
      mat: bpy.types.Material,
      scale_xyz: tuple[float, float, float] = (1.0, 1.0, 1.0),
  ) -> bpy.types.Object:
      bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=radius, location=loc)
      obj = bpy.context.active_object
      obj.name = name
      obj.scale = scale_xyz
      bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
      obj.data.materials.append(mat)
      remesh_to_micro_voxels(obj, voxel_size=0.010)
      return obj
  ```

---

### 4.3 Target 3: `res://scripts/items/loot_drop_pickup.gd`

#### Edit 3A: Replace `SphereMesh` declaration with `Mesh`
- **Location**: Line 27
- **Before**:
  ```gdscript
  static var _shared_crystal_mesh: SphereMesh = null
  ```
- **After**:
  ```gdscript
  static var _shared_crystal_mesh: Mesh = null
  ```

#### Edit 3B: Replace `SphereMesh` instantiation with `SurfaceTool` micro-voxel cluster
- **Location**: Lines 39–45
- **Before**:
  ```gdscript
  	if _shared_crystal_mesh == null:
  		# Low-segment faceted octahedron/crystal (radial_segments=6, rings=2 -> crisp faceted gem, 0.26m tall)
  		_shared_crystal_mesh = SphereMesh.new()
  		_shared_crystal_mesh.radius = 0.11
  		_shared_crystal_mesh.height = 0.26
  		_shared_crystal_mesh.radial_segments = 6
  		_shared_crystal_mesh.rings = 2
  ```
- **After**:
  ```gdscript
  	if _shared_crystal_mesh == null:
  		# Crisp stepped micro-voxel crystal/flask cluster (replaces legacy SphereMesh)
  		var st: SurfaceTool = SurfaceTool.new()
  		st.begin(Mesh.PRIMITIVE_TRIANGLES)
  		_add_micro_voxel_box(st, Vector3(0.0, 0.0, 0.0), Vector3(0.16, 0.16, 0.16))
  		_add_micro_voxel_box(st, Vector3(0.0, -0.07, 0.0), Vector3(0.11, 0.06, 0.11))
  		_add_micro_voxel_box(st, Vector3(0.0, 0.07, 0.0), Vector3(0.11, 0.06, 0.11))
  		_add_micro_voxel_box(st, Vector3(0.0, 0.12, 0.0), Vector3(0.06, 0.05, 0.06))
  		_shared_crystal_mesh = st.commit()
  ```

#### Edit 3C: Add `_add_micro_voxel_box` helper method
- **Location**: Near line 57
- **Insert**:
  ```gdscript
  static func _add_micro_voxel_box(st: SurfaceTool, center: Vector3, size: Vector3) -> void:
  	var h: Vector3 = size * 0.5
  	var min_p: Vector3 = center - h
  	var max_p: Vector3 = center + h
  	var faces: Array = [
  		[Vector3(0, 0, 1), Vector3(min_p.x, min_p.y, max_p.z), Vector3(max_p.x, min_p.y, max_p.z), Vector3(max_p.x, max_p.y, max_p.z), Vector3(min_p.x, max_p.y, max_p.z)],
  		[Vector3(0, 0, -1), Vector3(max_p.x, min_p.y, min_p.z), Vector3(min_p.x, min_p.y, min_p.z), Vector3(min_p.x, max_p.y, min_p.z), Vector3(max_p.x, max_p.y, min_p.z)],
  		[Vector3(1, 0, 0), Vector3(max_p.x, min_p.y, max_p.z), Vector3(max_p.x, min_p.y, min_p.z), Vector3(max_p.x, max_p.y, min_p.z), Vector3(max_p.x, max_p.y, max_p.z)],
  		[Vector3(-1, 0, 0), Vector3(min_p.x, min_p.y, min_p.z), Vector3(min_p.x, min_p.y, max_p.z), Vector3(min_p.x, max_p.y, max_p.z), Vector3(min_p.x, max_p.y, min_p.z)],
  		[Vector3(0, 1, 0), Vector3(min_p.x, max_p.y, max_p.z), Vector3(max_p.x, max_p.y, max_p.z), Vector3(max_p.x, max_p.y, min_p.z), Vector3(min_p.x, max_p.y, min_p.z)],
  		[Vector3(0, -1, 0), Vector3(min_p.x, min_p.y, min_p.z), Vector3(max_p.x, min_p.y, min_p.z), Vector3(max_p.x, max_p.y, min_p.z), Vector3(min_p.x, min_p.y, max_p.z)],
  	]
  	for f: Array in faces:
  		var norm: Vector3 = f[0] as Vector3
  		st.set_normal(norm)
  		var v0: Vector3 = f[1] as Vector3
  		var v1: Vector3 = f[2] as Vector3
  		var v2: Vector3 = f[3] as Vector3
  		var v3: Vector3 = f[4] as Vector3
  		st.add_vertex(v0)
  		st.add_vertex(v1)
  		st.add_vertex(v2)
  		st.add_vertex(v0)
  		st.add_vertex(v2)
  		st.add_vertex(v3)
  ```

---

## 5. Verification Method

### 5.1 Independent CLI Verification Commands
The implementing agent can verify the changes by running these exact commands in PowerShell:

```powershell
# 1. Verify static typing and compilation on modified GDScript files:
& "c:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --path . --check-only -s res://scripts/player/fps_viewmodel_controller.gd
& "c:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --path . --check-only -s res://scripts/items/loot_drop_pickup.gd

# 2. Re-export micro-voxel enemies via Headless Blender:
& "C:\Users\olema\Downloads\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender.exe" --background --python tools/blender_build_voxel_enemies.py

# 3. Re-export alchemical elixir loot via Headless Blender:
& "C:\Users\olema\Downloads\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender.exe" --background --python tools/blender_build_voxel_town_and_loot.py

# 4. Run Godot headless asset re-import pass:
& "c:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --quit-after 240 --path . --import
```

### 5.2 Success Criteria
- `--check-only` exits with code `0` on all modified `.gd` files with zero parse or type errors.
- Blender generates `enemy_01_ossuary_executioner.glb`, `enemy_03_reliquary_hexweaver.glb`, and `loot_alchemical_elixir.glb` without smooth primitives, preserving articulated limb hierarchies and multi-material slots.
- Loot pickup geometry displays a stepped micro-voxel crystal cluster instead of a `SphereMesh`.
