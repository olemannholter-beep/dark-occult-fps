# Technical Survey Report: Requirements R5, R6, and Verification Pipeline
**Subagent**: Survey Explorer 3  
**Working Directory**: `c:\Users\olema\Downloads\alpha branch\.agents\teamwork\teamwork_explorer_survey_3`  
**Target Waves**: Wave 1D (Town Overworld, Stepped Terrain & Loot), Wave 1E (All 11 Enemies & Bosses), Verification & Pipeline

---

## 1. Observation

### 1.1 Scope R5: Wave 1D Existing Scripts & Model Enumeration
- **Existing Generator Scripts**:
  - `tools/blender_build_terrain.py`: Generates `assets/models/terrain_town.glb` (120m × 120m grid, size 60.0 half-extent, lines 109–111).
  - `tools/blender_build_town.py`: Generates `church_kit/town_street_lamp_iron.glb`, `church_kit/town_graveyard_wall_fence_6m.glb`, `church_kit/town_gravestone_cluster.glb`, `church_kit/town_road_curb_8m.glb` (lines 496–499), and calls `build_house_variant` for `house_abandoned_a.glb` and `house_abandoned_b.glb` (lines 475–492).
  - `tools/blender_build_abandoned_house.py`: Defines `build_house_variant`. In line 98–105, plinth depth was 2.5m (`(width_x + 0.4, depth_y + 0.4, 2.5)` at `(0.0, 0.0, -1.25)`).
  - `tools/blender_build_foliage.py`: Generates `assets/models/grass_clump_wild.glb` (9 curved blades, lines 28–117) and `assets/models/dead_tree_gnarled.glb` (5.5m tall trunk, lines 189–318).
  - `tools/blender_build_loot_and_spells.py`: Generates 4 items in `assets/models/items/`: `loot_blood_echo_cluster.glb` (lines 145–240), `loot_occult_relic_talisman.glb` (lines 243–353), `loot_alchemical_elixir.glb` (lines 356–459), and `prop_gothic_reliquary_chest.glb` (lines 462–648).
- **Model Enumeration in R5 (13 Target GLBs)**:
  1. `res://assets/models/church_kit/town_gravestone_cluster.glb`
  2. `res://assets/models/church_kit/town_graveyard_wall_fence_6m.glb`
  3. `res://assets/models/church_kit/town_road_curb_8m.glb`
  4. `res://assets/models/church_kit/town_street_lamp_iron.glb`
  5. `res://assets/models/house_abandoned_a.glb`
  6. `res://assets/models/house_abandoned_b.glb`
  7. `res://assets/models/dead_tree_gnarled.glb`
  8. `res://assets/models/grass_clump_wild.glb`
  9. `res://assets/models/terrain_town.glb`
  10. `res://assets/models/items/loot_alchemical_elixir.glb`
  11. `res://assets/models/items/loot_blood_echo_cluster.glb`
  12. `res://assets/models/items/loot_occult_relic_talisman.glb`
  13. `res://assets/models/items/prop_gothic_reliquary_chest.glb`
  *(Note: Wave 1D title lists "15 models"; exactly 13 `.glb` filenames are specified in the request and exist in the filesystem. The chest contains 2 distinct mesh parts: `ChestBase` and `ChestLid`).*

### 1.2 `terrain_town.glb` Geometry, Heights & Cutout Specifications
- **Dimensions**: 120m (X) × 120m (Z) centered at (0, 0) in Godot world coordinates (`create_grid(bm, x_segments=160, y_segments=160, size=60.0)`).
- **Heights (`compute_terrain_height` in `tools/blender_build_terrain.py`:38–98)**:
  - Valley road: gz = +38 (Y ≈ 0.15m) ramping North to gz = -10.5m (Y = 3.20m).
  - House A footprint pad: centered at (gx = -16.0, gz = +14.0), flattened at Y = 0.85m (inner radius 5.5m, blend margin 11.5m).
  - House B footprint pad: centered at (gx = +16.0, gz = +8.0), flattened at Y = 1.15m (inner radius 5.5m, blend margin 11.5m).
  - Church hilltop plateau: front plaza gz in [-12.0, -8.5] at Y = 3.20m; cathedral/crypt plateau gx in [-15.0, +15.0], gz in [-59.0, -12.0] flattened at Y = 3.55m.
  - Subterranean roof clearance: vertices outside Church Nave with gz <= -47.5m and gx in [-30.0, +30.0] are clamped to `min_roof_cover = 3.55 + z_blend * (4.35 - 3.55)` (Y >= 4.35m) so the terrain underside never intersects crypt ceilings.
- **Stairwell Cutout (lines 190–209)**:
  - Carved via `BOOLEAN DIFFERENCE` cutter `CryptTerrainCutter` sized width X = 27.6m, length Y = 35.8m, height Z = 20.0m centered at Godot gx = 0.0, gz = -39.9 (Blender bx = 0.0, by = +39.9, bz = 2.0).
  - Godot bounds: X in [-13.8, +13.8], Z in [-57.8, -22.0]. The south face of this cutout opens at Z = -22.0, directly revealing the stairwell entrance.
- **Step Height Constraint**:
  - `scripts/player/fps_controller.gd`:12 explicitly declares `@export var max_step_height: float = 0.36`.
  - Any vertical step > 0.36m halts player walking movement. Micro-voxel terrain terracing requires individual step heights <= 0.20m (e.g., 0.16m–0.20m quantization).

### 1.3 Scope R6: Wave 1E Enemy Hierarchy & Articulation
- **11 Enemy Target Models in `res://assets/models/enemies/`**:
  1. `enemy_ossuary_skeleton.glb` (241,424 bytes)
  2. `enemy_plague_acolyte.glb` (241,444 bytes)
  3. `enemy_iron_penitent.glb` (241,444 bytes)
  4. `enemy_01_ossuary_executioner.glb` (702,472 bytes)
  5. `enemy_02_necropolis_praetorian.glb` (718,476 bytes)
  6. `enemy_03_reliquary_hexweaver.glb` (639,584 bytes)
  7. `enemy_04_inquisitor_rackmaster.glb` (775,216 bytes)
  8. `enemy_05_plague_bloater.glb` (700,916 bytes)
  9. `enemy_06_weeping_banshee.glb` (648,936 bytes)
  10. `enemy_07_bell_juggernaut.glb` (730,912 bytes)
  11. `enemy_08_abyssal_archon.glb` (732,696 bytes)
- **AI Runtime Node Binding (`scripts/enemies/occult_enemy_ai.gd`:385–405)**:
  - `pelvis_node = find_child("Pelvis", true, false) as Node3D`
  - `thigh_l_node = find_child("ThighL", true, false) as Node3D`
  - `shin_l_node = find_child("ShinL", true, false) as Node3D`
  - `thigh_r_node = find_child("ThighR", true, false) as Node3D`
  - `shin_r_node = find_child("ShinR", true, false) as Node3D`
  - `torso_node = find_child("Torso", true, false) as Node3D`
  - `head_node = find_child("Head", true, false) as Node3D`
  - `upper_arm_l_node = find_child("UpperArmL", true, false) as Node3D` (fallback `"LeftArm"`)
  - `forearm_l_node = find_child("ForearmL", true, false) as Node3D`
  - `upper_arm_r_node = find_child("UpperArmR", true, false) as Node3D` (fallback `"RightArm"`)
  - `forearm_r_node = find_child("ForearmR", true, false) as Node3D`
  - `secondary_prop_node = find_child("SecondaryProp", true, false) as Node3D`
- **Rig Hierarchy & Pivot Coordinates (facing Blender -Y -> Godot -Z forward)**:
  - `Pelvis` (root at 0, 0, 0.95 -> Godot 0, 0.95, 0)
    - `Torso` (Blender 0, 0, 1.05 -> Godot local 0, 0.10, 0)
      - `Head` (Blender 0, 0, 1.58 -> Godot local 0, 0.53, 0)
      - `UpperArmL` (Blender -0.30, 0, 1.46 -> Godot local -0.30, 0.41, 0)
        - `ForearmL` (Blender -0.30, -0.04, 1.21 -> Godot local 0, -0.25, -0.04; carries `ShieldLeft` / offhand)
      - `UpperArmR` (Blender 0.30, 0, 1.46 -> Godot local 0.30, 0.41, 0)
        - `ForearmR` (Blender 0.30, -0.04, 1.21 -> Godot local 0, -0.25, -0.04; carries `WeaponRight`)
      - `SecondaryProp` (Blender 0, 0, 1.38 -> Godot local 0, 0.33, 0)
    - `ThighL` (Blender -0.14, 0, 0.88 -> Godot local -0.14, -0.07, 0)
      - `ShinL` (Blender -0.14, 0, 0.50 -> Godot local 0, -0.38, 0)
    - `ThighR` (Blender 0.14, 0, 0.88 -> Godot local 0.14, -0.07, 0)
      - `ShinR` (Blender 0.14, 0, 0.50 -> Godot local 0, -0.38, 0)

### 1.4 Verification & Pipeline Tools
- **Blender Executable**: `C:\Users\olema\Downloads\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender.exe` (confirmed present via `Test-Path`).
- **Godot Console Executable**: `C:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe`.
- **Import Command**: `& "C:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --quit-after 240 --path . --import`.
- **Frame Capture & Physics Telemetry**: `tools/mcp_capture_frame.gd` validates:
  1. Stairwell ray at (0.0, 5.2, -21.8) down to (0.0, 0.5, -21.8) ensuring the terrain cutout is unblocked.
  2. Church doorway ray at Y=5.2 from Z=-10.5 to Z=-13.5 (`church_doorway_clear`).
  3. Crypt archway ray at Y=1.2 from Z=-23.2 to Z=-25.5 (`crypt_archway_clear`).
  4. Crypt floor support ray at (0.0, 2.0, -27.5) down to (0.0, -1.0, -27.5) (`crypt_floor_y`).

---

## 2. Logic Chain

### 2.1 Wave 1D Script Architecture (`tools/blender_build_voxel_town_and_loot.py`)
1. **Model Scope Reconciliation**:
   - The original request titled Wave 1D as "(15 models)", but explicitly names 13 `.glb` models across `church_kit/` (4), root `assets/models/` (5), and `items/` (4).
   - In Godot, `prop_gothic_reliquary_chest.glb` consists of 2 distinct node entities (`ChestBase` and `ChestLid`), bringing the entity count to 14.
   - All 13 `.glb` targets must be generated by `tools/blender_build_voxel_town_and_loot.py` cleanly overwriting existing assets.

2. **Stepped Micro-Voxel Terrain Generation**:
   - To achieve the grimdark micro-voxel aesthetic while satisfying the player's 0.36m step limit (`max_step_height = 0.36`), terrain elevation must not use continuous smooth slopes or tall vertical cliffs.
   - The height function $hy = compute\_terrain\_height(gx, gz)$ calculates base elevation.
   - Micro-voxel quantization: $hy_{stepped} = round(hy / 0.18) \times 0.18$ ensures each terrace riser is exactly 0.18m (<= 0.20m), well within Godot's 0.36m step-up collision threshold so the FPS controller glides over steps without jumping.
   - Road path: gz from +38 down to -10.5m must be preserved as flattened 0.18m micro-voxel terracing.
   - Building pads: House A (gx = -16, gz = +14) at Y = 0.85m and House B (gx = +16, gz = +8) at Y = 1.15m must have zero steps within their 5.5m inner radii.
   - Hilltop church plateau: gx in [-15, +15], gz in [-59, -12] must be perfectly flat at Y = 3.55m.
   - Stairwell cutout: A `BOOLEAN DIFFERENCE` box cutter of size 27.6m (X) × 35.8m (Y) × 20.0m (Z) must be applied at gx = 0.0, gz = -39.9, cutting through the terrain at Z = -22.0 to keep the descending stairwell and crypt completely open to physics raycasts.

3. **House Foundation Plinths & Architecture**:
   - Observation 1.1 shows the existing `build_house_variant` had a 2.5m plinth.
   - AGENTS.md Rule 9.2 and Requirement R5 mandate a **3.0m deep foundation plinth** (Z = -3.0m to Z = 0.0m) plus stepped entrance steps so buildings never float when placed on uneven hillside contours.
   - `house_abandoned_a.glb` (width 7.6m, depth 9.2m, no annex) and `house_abandoned_b.glb` (width 8.4m, depth 7.8m, with side annex) will use `MicroVoxelBuilder` with `Mat_PlinthStone`, `Mat_CharredTimber`, `Mat_SlateRoof`, and `Mat_Plaster`.

4. **Interactive Chest Hierarchy**:
   - In `tools/blender_build_loot_and_spells.py`:462–648, `prop_gothic_reliquary_chest.glb` requires `ChestBase` as parent and `ChestLid` as child.
   - The hinge is at Blender Y = +0.41, Z = 0.58. In Godot coordinates, the hinge position is `(0.0, 0.58, 0.41)`.
   - When the player interacts with the chest, rotating `ChestLid.rotation.x` by -100° swings the lid open backwards without clipping through the base.
   - Both `ChestBase` and `ChestLid` must be generated with micro-voxel masonry, wrought-iron straps, bronze corner paws, and skull escutcheon.

5. **Loot Drops & Street Kit**:
   - `loot_blood_echo_cluster.glb`: 0.015m micro-voxels, central faceted crimson crystal core (`AbyssalCrimson` emissive), dual rotating bronze astrolabe rings.
   - `loot_occult_relic_talisman.glb`: 0.012m micro-voxels, octagonal wrought-iron frame, 16 sunburst spikes, double-sided bone skull relief, glowing occult rune center, hanging 3D chain tassels.
   - `loot_alchemical_elixir.glb`: 0.015m micro-voxels, ribbed flask ribs, glowing emerald/gold core (`SicklyGreenBile`), brass harness cage, leather straps, cork stopper.
   - `town_street_lamp_iron.glb`: 3.8m tall, deep embedded plinth (Z = -0.80m to +0.58m), fluted column, swan-neck cantilever arm, hexagonal lantern cage with glowing amber mantle core.
   - `town_graveyard_wall_fence_6m.glb`: 6m wide, embedded plinth base (Z = -1.20m to +0.15m), 4-course dwarf wall, 2 end piers with pyramid finials, 20 wrought-iron spear finials.
   - `town_road_curb_8m.glb`: 8m long curb, 32 beveled curb stones (Z = -0.55m to +0.22m), drainage cobbles, 4 bollards with sagging chains.
   - `town_gravestone_cluster.glb`: Celtic cross, pointed lancet headstone, ledger slab, obelisk, border cobbles, plot chain posts.
   - `dead_tree_gnarled.glb`: 5.5m tall gnarled trunk, 3 main branching claws, root flares, rough charred bark micro-voxel texture.
   - `grass_clump_wild.glb`: 9 curved grass blades (0.45m–0.66m) with windswept tilt.

### 2.2 Wave 1E Enemy Rig Architecture (`tools/blender_build_voxel_enemies.py`)
1. **Articulated Rig Compatibility**:
   - Observations in 1.3 show `OccultEnemyAI._resolve_articulated_nodes()` binds exact nodes: `Pelvis`, `ThighL`, `ShinL`, `ThighR`, `ShinR`, `Torso`, `Head`, `UpperArmL`, `ForearmL`, `UpperArmR`, `ForearmR`, and `SecondaryProp`.
   - Procedural locomotion, windup coil, attack whip, and stagger flinch directly manipulate `rotation` and `position` on these exact nodes.
   - If limb nodes were merged into a single static mesh, all 11 enemy types in Godot would freeze as statues without procedural animations.
   - Therefore, `tools/blender_build_voxel_enemies.py` must construct each enemy using distinct `MicroVoxelBuilder` sub-assemblies joined into this exact 12-to-14 pivot hierarchy.

2. **Dual Naming & Alias Preservation**:
   - Requirement R6 lists: `Torso`, `Head`, `ArmLeft`, `ArmRight`, `LegLeft`, `LegRight`, `WeaponRight`, `ShieldLeft`.
   - GDScript lines 399–404 show `upper_arm_l_node` falls back to `find_child("LeftArm")` and `upper_arm_r_node` falls back to `find_child("RightArm")`.
   - To satisfy both the AI runtime solver and the explicit requirement:
     - Root: `Pelvis`
       - `ThighL` (alias/parent of `ShinL`)
       - `ThighR` (alias/parent of `ShinR`)
       - `Torso`
         - `Head`
         - `UpperArmL` (or `ArmLeft`), holding child node `ForearmL` (or `ShieldLeft` for praetorian/banshee/archon)
         - `UpperArmR` (or `ArmRight`), holding child node `ForearmR` (or `WeaponRight` carrying the cleaver/halberd/staff/flail/hammer/glaive)
         - `SecondaryProp` (trophy chains, floating grimoires, gibbet hoops, dorsal bile tank, stone wings, bell shell, floating obelisks).

3. **Facing & Transform Inversion Math**:
   - Blender coordinate system: +X Right, +Y Forward, +Z Up.
   - Godot glTF import: glTF 2.0 maps Blender +Y to Godot +Z (South).
   - In Godot, -Z is Forward (North).
   - To make enemies face Godot -Z forward, enemy sub-parts must point toward **Blender -Y**!
   - `join_into_hierarchy_node()` in `tools/blender_build_enemies.py`:248–293 correctly handles pivot translation and face normal recalculation:
     - `py_gltf = -py`
     - Translates vertices by `(-px, -py_gltf, -pz)` so the node's local origin matches its anatomical pivot point.

4. **11 Enemy Archetype Profiles**:
   - `enemy_ossuary_skeleton.glb`: Bone skeleton, exposed ribcage, glowing amber eye sockets, dual notched bone cleavers.
   - `enemy_plague_acolyte.glb`: Tattered cultist robe panels, bird-beak plague mask, toxic censer flail.
   - `enemy_iron_penitent.glb`: Spiked iron cage helmet, chained breastplate, morningstar flail.
   - `enemy_01_ossuary_executioner.glb`: Heavy executioner pauldron skulls, dual notched bone-cleavers (`CleaverL`, `CleaverR`), chest trophy chains.
   - `enemy_02_necropolis_praetorian.glb`: Gothic plate & bronze cuirass, plumed helmet, Royal Sun-Crest Halo, massive stone sarcophagus-lid greatshield (`ShieldSlab`) on ForearmL, royal halberd on ForearmR.
   - `enemy_03_reliquary_hexweaver.glb`: Weathered leather robes, scholar cowl, brass astrolabe halo + 3 orbiting open grimoires (`GrimoireCover`, `GrimoirePages`, `GrimoireOrb`), glowing hex staff.
   - `enemy_04_inquisitor_rackmaster.glb`: Gibbet cage helmet, torturer's catch-hook on ForearmL, heavy 10-spiked flail morningstar on ForearmR.
   - `enemy_05_plague_bloater.glb`: Pressurized dorsal toxic bile tank (`BileTankCore`), brass bird-beak mask with goggles, left-arm sprayer nozzle, right-arm censer.
   - `enemy_06_weeping_banshee.glb`: Weathered stone & silvered steel, sculpted stone wings with frozen soul feathers, tear streaks on face, spectral claw talons on both hands, chained soul lantern secondary prop.
   - `enemy_07_bell_juggernaut.glb`: Cracked tarnished-bronze cathedral bell shell encasing torso with glowing amber fractures, internal pendulum clapper, giant bell-clapper warhammer on ForearmR.
   - `enemy_08_abyssal_archon.glb`: Obsidian plate, 6 floating ritual obelisk shards, 6-horned blood knight helm, blood sigil shield on ForearmL, twin-bladed blood glaive on ForearmR.

---

## 3. Caveats

1. **Model Count in Wave 1D**:
   - The user prompt states "Wave 1D (15 models)", but explicitly names 13 `.glb` models.
   - Inspecting all directories confirms there are no additional missing `.glb` files in `assets/models/items/`, `church_kit/`, or root `assets/models/`.
   - The interactive chest entity comprises 2 distinct mesh components (`ChestBase` and `ChestLid`).
   - Implementers should generate the exact 13 named `.glb` files.

2. **Terrain Step vs Slope Physics**:
   - Smooth ramps allow sliding; sharp steps > 0.36m trigger wall collisions in Godot's `CharacterBody3D.move_and_slide()`.
   - The micro-voxel step height must be kept strictly <= 0.20m (recommended: 0.18m) so player locomotion remains 100% fluid.
   - The stairwell cutout bounds (`gx = 0.0, gz = -39.9`, X width 27.6m, Z length 35.8m, cutting at Z = -22.0) must NOT be altered or `tools/mcp_capture_frame.gd` physics verification will fail.

3. **Blender Execution & Memory Budget**:
   - Generating 11 high-detail micro-voxel articulated enemies (each containing 140–180 sub-components) in a single Python script can consume significant Blender memory if meshes are not freed.
   - Implementers must call `bm.free()` and `bpy.ops.wm.read_factory_settings(use_empty=True)` between models.

---

## 4. Conclusion

1. **Wave 1D (`tools/blender_build_voxel_town_and_loot.py`)**:
   - Implement as a standalone Python script generating all 13 models.
   - Terrain generation must implement 0.18m stepped micro-voxel terracing, enforce flattened footprints at House A (Y=0.85m), House B (Y=1.15m), and Church (Y=3.55m), clamp subterranean ceiling clearance (Y >= 4.35m outside nave), and execute the exact Boolean stairwell cutout at X=0, Z=-22.
   - Houses A and B must include 3.0m deep foundation plinths.
   - The reliquary chest must export separate `ChestBase` and `ChestLid` nodes pivoted at Blender Y=+0.41, Z=0.58.

2. **Wave 1E (`tools/blender_build_voxel_enemies.py`)**:
   - Implement as a standalone Python script generating all 11 enemy models.
   - Every enemy must export the 12-to-14 pivot articulated hierarchy (`Pelvis`, `ThighL`, `ShinL`, `ThighR`, `ShinR`, `Torso`, `Head`, `UpperArmL`, `ForearmL`, `UpperArmR`, `ForearmR`, `SecondaryProp`) facing Blender -Y (Godot -Z forward).
   - ForearmR carries the primary weapon; ForearmL carries the shield or offhand spell focus.

3. **Execution Safety**:
   - Blender scripts can run completely independently in parallel without interfering with each other.
   - Godot headless import must run strictly sequentially after Blender completes all GLB exports.

---

## 5. Verification Method

To independently verify all findings and confirm readiness:

1. **Verify Blender Executable**:
   ```powershell
   & "C:\Users\olema\Downloads\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender.exe" --version
   ```

2. **Verify Godot Headless CLI**:
   ```powershell
   & "C:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --version
   ```

3. **Verify Player Step Limit in GDScript**:
   Inspect line 12 of `scripts/player/fps_controller.gd`:
   ```powershell
   Get-Content "scripts/player/fps_controller.gd" | Select-String "max_step_height"
   ```
   *Expected output*: `@export var max_step_height: float = 0.36`.

4. **Verify Enemy AI Node Resolution in GDScript**:
   Inspect lines 385–405 of `scripts/enemies/occult_enemy_ai.gd`:
   ```powershell
   Get-Content "scripts/enemies/occult_enemy_ai.gd" | Select-String "find_child" | Select-Object -First 12
   ```

5. **Post-Implementation Verification (When Wave 1D & 1E are generated)**:
   - Run Blender builds:
     ```powershell
     & "C:\Users\olema\Downloads\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender.exe" --background --python tools/blender_build_voxel_town_and_loot.py
     & "C:\Users\olema\Downloads\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender.exe" --background --python tools/blender_build_voxel_enemies.py
     ```
   - Run Godot import pass:
     ```powershell
     & "C:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --quit-after 240 --path . --import
     ```
   - Run MCP Frame Capture and Physics Raycast Telemetry:
     ```powershell
     & "C:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --path . -s res://tools/mcp_capture_frame.gd -- --view=overview --frames=45
     ```
   - Invalidation conditions:
     - `stairwell_ray_hit_node` in `.mcp_captures/scene_state.json` reports anything other than unblocked/open stairwell.
     - `church_doorway_clear` or `crypt_archway_clear` is false.
     - Enemy models fail to animate in `scenes/levels/town_overworld.tscn`.
