# Handoff Report — Survey Explorer 1 (Requirements R1 & R2)

**Task**: Survey Investigation of Requirement R1 (Shared Environment & Rig Micro-Voxel Palette) and Requirement R2 (Wave 1A: Church Sanctuary & Hub Stations).  
**Author**: Survey Explorer 1  
**Working Directory**: `c:\Users\olema\Downloads\alpha branch\.agents\teamwork\teamwork_explorer_survey_1`  
**Date / Timestamp**: 2026-11-01T02:25:00Z  

---

## 1. Observation

### 1.1 Inspected Files & Key Line Numbers
The following files and components were examined in detail:
1. `tools/blender_micro_voxel_kit.py` (lines 1–702):
   - `make_micro_voxel_materials(set_idx)` (lines 7–39): 4 armor PBR materials (`Set{i}_Mat_Iron`, `Mat_Leather`, `Mat_Brass`, `Mat_RuneGlow`).
   - `MicroVoxelBuilder` (lines 42–350): Character armor builder with 26-neighborhood cavity AO, directional face shading, deterministic hash jitter, face culling, and `loop[color_layer] = col_rgba`.
   - `make_weapon_pbr_material(...)` (lines 353–390): Weapon PBR material generator with `ShaderNodeVertexColor("Col")` linked to `Base Color` of `Principled BSDF`, storing base RGB in `mat["_base_rgb"]`.
   - `create_weapon_voxel_palette()` (lines 393–439): 12 weapon materials.
   - `WeaponVoxelBuilder` (lines 441–702): Hero viewmodel builder with `fill_box`, `carve_box`, `fill_cylinder_x/y/z`, 26-neighborhood cavity AO, and per-loop vertex color baking `col = base_rgb * (height_grad * ao * shade_bias * dir_shade + jitter)`.
2. `scripts/environment/material_library.gd` (lines 1–465):
   - `GrimdarkMaterialLibrary`: Static material cache and factory creating `StandardMaterial3D` instances with `vertex_color_use_as_albedo = true`, `normal_enabled = false`, and `cull_mode = CULL_DISABLED` (or `CULL_BACK`).
   - `get_material_for_name(mat_name: String) -> Material` (lines 396–465): Keyword-based router resolving 23 materials.
3. `tools/blender_build_church_crypt_kit.py` (lines 1–4062):
   - Contains previous monolithic asset generator functions:
     - `build_floor_stone_4x4` (line 330)
     - `build_wall_stone_solid` (line 159)
     - `build_wall_stone_window` (line 247)
     - `build_wall_stone_arch_door` (line 185)
     - `build_roof_gothic_vault_4x4` (line 350)
     - `build_stairs_stone_4x4` (line 422)
     - `build_church_foundation_plinth` (line 685)
     - `build_church_front_gable_rose` (line 781)
     - `build_church_pitched_roof_12x16` (line 895)
     - `build_church_bell_tower_spire` (line 959)
     - `build_church_buttress` (line 1070)
     - `build_wall_lantern_sconce` (line 1103)
     - `build_hub_weapon_workbench` (line 2730)
     - `build_hub_armor_reliquary_stand` (line 2886)
     - `build_hub_sanctuary_upgrade_font` (line 3030)
     - `build_occult_rift_portal` (line 3652)
4. `tools/build_prefabs_and_level.gd` (lines 110–1430):
   - Prefab creation functions: `_create_trimesh_prefab` and `_create_hub_station_prefab`.
   - Maps GLB models to Godot `.tscn` prefabs with fast primitive box/cylinder colliders (e.g. `"box_church_plinth"`, `"box_wall_4x4"`, `"box_floor_4x4"`, `"box_ceiling_4x4"`, `"box_wall_door_4x4"`, `extra_stairs_ramp`).
   - Re-assigns materials via `GrimdarkMaterialLibrary.get_material_for_name(mat_name)` in lines 200–214.
5. `scripts/interaction/occult_portal.gd` (lines 1–100):
   - Line 48: `_vortex_mesh = find_child("PortalVortexMesh", true, false) as MeshInstance3D`.
   - Strictly expects a child node named `"PortalVortexMesh"` in `occult_rift_portal.glb`.
6. `scenes/levels/town_overworld.tscn`:
   - Placement of `GothicChurch` at world `(0, 4.0, 0)`.
   - `ChurchFoundationPlinth` placed inside `GothicChurch` at `(0, 0, -20)` -> World coordinates `(0, 4.0, -20.0)`.
   - `HubWeaponWorkbench` at `(-10.5, 0, -36)`, rotation 90 deg.
   - `HubArmorReliquaryStand` at `(10.5, 0, -36)`, rotation -90 deg.
   - `HubSanctuaryUpgradeFont` at `(-6.5, 0, -42)`, rotation 0 deg.
   - 8 `OccultRiftPortal` instances placed in `CryptPortalNexusZone` for biomes 1 to 8.

---

### 1.2 Telemetry Table: All 16 Target `.glb` Models
The 16 existing `.glb` files in `assets/models/church_kit/` and `assets/models/architecture/` were inspected headlessly via Blender 5.4.0 Alpha. Telemetry is recorded verbatim below:

| # | Target Model File Path | Object Nodes in GLB | Verts / Faces | Bounding Box Min [X, Y, Z] | Bounding Box Max [X, Y, Z] | Dimensions Size [X, Y, Z] | Material Names in GLB |
|---|------------------------|---------------------|---------------|----------------------------|----------------------------|---------------------------|-----------------------|
| 1 | `assets/models/church_kit/floor_stone_4x4.glb` | `['floor_stone_4x4']` | 14,592 / 6,688 | `[-2.000, -2.000, -0.370]` | `[2.000, 2.000, 0.005]` | `[4.000, 4.000, 0.375]` | `['CarvedStoneTrim', 'DarkFlagstoneSlab', 'WornFlagstoneTile']` |
| 2 | `assets/models/church_kit/wall_stone_solid.glb` | `['wall_stone_solid']` | 28,512 / 13,068 | `[-2.140, -0.320, 0.000]` | `[2.140, 0.320, 4.050]` | `[4.280, 0.640, 4.050]` | `['WroughtIron', 'CarvedStoneTrim', 'DarkFlagstone', 'GothicAshlarStone']` |
| 3 | `assets/models/church_kit/wall_stone_window.glb` | `['wall_stone_window']` | 29,664 / 13,840 | `[-2.140, -0.320, 0.000]` | `[2.140, 0.320, 4.050]` | `[4.280, 0.640, 4.050]` | `['OccultStainedGlass', 'DarkFlagstone', 'WroughtIron', 'GothicAshlarStone', 'CarvedStoneTrim']` |
| 4 | `assets/models/church_kit/wall_stone_arch_door.glb` | `['wall_stone_arch_door']` | 17,352 / 8,160 | `[-2.140, -0.320, 0.000]` | `[2.140, 0.320, 4.050]` | `[4.280, 0.640, 4.050]` | `['WroughtIron', 'CarvedStoneTrim', 'DarkFlagstone', 'GothicAshlarStone']` |
| 5 | `assets/models/church_kit/roof_gothic_vault_4x4.glb` | `['roof_gothic_vault_4x4']` | 15,840 / 7,260 | `[-2.090, -2.090, -0.350]` | `[2.090, 2.090, 0.660]` | `[4.180, 4.180, 1.010]` | `['RottedTimber', 'CarvedVaultRib', 'WroughtIron', 'GothicVaultStone', 'ExteriorRoofSlate']` |
| 6 | `assets/models/church_kit/stairs_stone_4x4.glb` | `['stairs_stone_4x4']` | 18,432 / 8,448 | `[-2.020, -2.023, -4.400]` | `[2.020, 2.023, 0.450]` | `[4.040, 4.045, 4.850]` | `['WroughtIron', 'DarkFlagstone', 'CarvedStoneStringer', 'WornFlagstoneStep']` |
| 7 | `assets/models/church_kit/wall_lantern_sconce.glb` | `['wall_lantern_sconce']` | 3,276 / 1,596 | `[-0.139, 0.000, -0.330]` | `[0.139, 0.540, 0.140]` | `[0.277, 0.540, 0.470]` | `['WroughtIron', 'LanternEmissiveFlame', 'LanternFrostedGlass']` |
| 8 | `assets/models/church_kit/church_foundation_plinth.glb` | `['church_foundation_plinth']` | 1,764 / 896 | `[-6.350, -10.525, -2.500]` | `[6.350, 12.600, 0.255]` | `[12.700, 23.125, 2.755]` | `['ChurchStepStone', 'ChurchFoundationStone']` |
| 9 | `assets/models/church_kit/church_front_gable_rose.glb` | `['church_front_gable_rose']` | 3,450 / 1,828 | `[-6.387, -0.320, -0.087]` | `[6.387, 0.320, 6.675]` | `[12.773, 0.640, 6.762]` | `['CarvedStoneTrim', 'RoseStainedGlass', 'GothicAshlarStone']` |
| 10 | `assets/models/church_kit/church_pitched_roof_12x16.glb` | `['church_pitched_roof_12x16']` | 5,400 / 2,700 | `[-6.522, -8.520, -0.340]` | `[6.522, 8.520, 7.175]` | `[13.043, 17.040, 7.515]` | `['CarvedStoneTrim', 'DarkSlateRoof']` |
| 11 | `assets/models/church_kit/church_bell_tower_spire.glb` | `['church_bell_tower_spire']` | 5,672 / 2,966 | `[-2.430, -2.430, 0.000]` | `[2.430, 2.430, 18.500]` | `[4.860, 4.860, 18.500]` | `['WroughtIron', 'TarnishedBronze', 'GothicAshlarStone', 'CarvedStoneTrim', 'DarkSlateRoof']` |
| 12 | `assets/models/church_kit/church_buttress.glb` | `['church_buttress']` | 1,096 / 546 | `[-0.620, -0.035, 0.000]` | `[0.620, 1.914, 9.045]` | `[1.240, 1.948, 9.045]` | `['CarvedStoneTrim', 'GothicAshlarStone']` |
| 13 | `assets/models/church_kit/hub_weapon_workbench.glb` | `['hub_weapon_workbench']` | 15,456 / 7,916 | `[-1.440, -0.580, 0.000]` | `[1.440, 0.580, 2.220]` | `[2.880, 1.160, 2.220]` | `['OccultSilver', 'RottedTimber', 'DarkFlagstone', 'WroughtIron', 'AgedBone', 'FrozenBlueSoul', 'GlowingOccultRune', 'TarnishedBronze']` |
| 14 | `assets/models/church_kit/hub_armor_reliquary_stand.glb` | `['hub_armor_reliquary_stand']` | 10,048 / 5,060 | `[-1.100, -0.510, 0.000]` | `[1.100, 0.510, 2.422]` | `[2.200, 1.020, 2.422]` | `['OccultSilver', 'RottedTimber', 'EmissiveConsecratedGold', 'DarkFlagstone', 'WroughtIron', 'AgedBone', 'TarnishedBronze']` |
| 15 | `assets/models/church_kit/hub_sanctuary_upgrade_font.glb` | `['hub_sanctuary_upgrade_font']` | 10,864 / 5,624 | `[-0.800, -0.800, 0.000]` | `[0.800, 0.800, 1.878]` | `[1.600, 1.600, 1.878]` | `['WeatheredStone', 'EmissiveConsecratedGold', 'DarkFlagstone', 'WroughtIron', 'TarnishedBronze']` |
| 16 | `assets/models/architecture/occult_rift_portal.glb` | `['OccultRiftArchway', 'PortalVortexMesh']` | 19,709 / 9,316 | `[-1.800, -0.620, 0.000]` | `[1.800, 0.620, 4.300]` | `[3.600, 1.240, 4.300]` | `['WeatheredStone', 'DarkFlagstone', 'WroughtIron', 'GlowingOccultRune', 'CarvedStoneTrim', 'PortalVortexSurface']` |

---

### 1.3 Key Architectural Model Deep Dives

#### A. `church_foundation_plinth.glb` (Critical Foundation & Stairwell Cutout)
From `tools/blender_build_church_crypt_kit.py` lines 685–778:
- **Plinth World Anchor**: Gothic Church sits at world `(0.0, 4.0, -20.0)`.
- **Plinth Local Dimensions**:
  - Width (X): `[-6.35, +6.35]` (total span 12.70m)
  - Depth (Blender Y): `[-8.35, +12.60]` (total span 20.95m, center Y = +2.125m)
  - Height (Blender Z): `[-2.50, 0.0]` (2.50m deep foundation, top surface at Z = 0.0)
- **Cutout 1 (Upper Stairwell & Crypt Opening)**:
  - Local X in `[-4.5, +4.5]`, local Blender Y in `[-0.5, +12.5]` (corresponds to Godot world X in `[-4.5, +4.5]`, world Z in `[-32.5, -19.5]`).
  - This opening MUST BE KEPT 100% UNBLOCKED so the stairwell (`stairs_stone_4x4`) and descending player can pass into the crypt basement.
- **Cutout 2 (Subterranean Chamber Clearance)**:
  - Local X in `[-7.0, +7.0]`, Blender Y in `[+1.8, +14.0]`, Blender Z in `[-3.0, -0.50]` (Godot world Y in `[1.0, 3.50]`).
  - Ensures the underground chamber and East/West gates are clear.
- **Front Entrance Steps**:
  - Located on the South side at Blender Y from `-8.25` extending to `-10.35` (Godot local Z = +8.0 to +10.4).
  - 5 steps with `step_run = 0.42m`, `step_rise = 0.18m`, `step_width = 4.20m`.
  - Top step at local Z = 0.0m; bottom step landing at local Z = -0.88m (embedding into the plaza at world Y = 3.12m).
  - Flanking stone cheek walls / parapets at X = `±2.35m`, width = `0.52m`, height = `2.75m`.

#### B. `occult_rift_portal.glb` (Child Node Hierarchy)
From `tools/blender_build_church_crypt_kit.py` lines 3652–3890 and `scripts/interaction/occult_portal.gd`:
- **Node Hierarchy**:
  - Root parent mesh: `OccultRiftArchway` (3.6m wide x 1.24m deep x 4.30m tall)
  - Child mesh: `PortalVortexMesh` (parented directly to `OccultRiftArchway`)
- **PortalVortexMesh Parameters**:
  - Size: 2.20m wide x 3.20m tall, centered at Blender Z = 1.88m (Y = 0.0).
  - UVs: Explicit [0..1] quad UV mapping on layer `"UVMap"`.
  - Material: `PortalVortexSurface`.
- **Godot Dependency**:
  - `OccultPortal` script in `scripts/interaction/occult_portal.gd` calls `find_child("PortalVortexMesh", true, false)` to bind the dynamic portal shader `res://shaders/portal_vortex.gdshader` and apply per-biome `portal_tint`. Preserving this child node is mandatory.

---

### 1.4 Material Library Mapping (R1 Palette Specification)
The 23 environment materials defined across `scripts/environment/material_library.gd` and `ORIGINAL_REQUEST.md` map to the following exact PBR parameters:

| Material Name | Base Color (sRGB) | Roughness | Metallic | Specular | Emission RGB & Strength | Alpha | Godot Library Method / Keyword |
|---------------|-------------------|-----------|----------|----------|-------------------------|-------|-------------------------------|
| `WeatheredAshlarStone` | `(0.32, 0.30, 0.28, 1.0)` | 0.92 | 0.00 | 0.15 | None | 1.0 | `get_weathered_ashlar_stone()` (default) |
| `RoughCobbleFlagstone` | `(0.24, 0.23, 0.22, 1.0)` | 0.72 | 0.00 | 0.25 | None | 1.0 | `get_rough_cobble_flagstone()` ("flagstone") |
| `CarvedStoneTrim` | `(0.36, 0.34, 0.32, 1.0)` | 0.84 | 0.00 | 0.18 | None | 1.0 | `get_carved_stone_trim()` ("trim") |
| `DarkSlateRoof` | `(0.18, 0.19, 0.22, 1.0)` | 0.89 | 0.00 | 0.15 | None | 1.0 | `get_dark_slate_roof()` ("roof", "slate") |
| `DirtyPlaster` | `(0.38, 0.35, 0.31, 1.0)` | 0.93 | 0.00 | 0.12 | None | 1.0 | `get_dirty_plaster()` ("plaster") |
| `RottedCharredTimber` | `(0.20, 0.14, 0.10, 1.0)` | 0.88 | 0.00 | 0.15 | None | 1.0 | `get_rotted_charred_timber()` ("timber") |
| `TarnishedWroughtIron` | `(0.14, 0.14, 0.16, 1.0)` | 0.48 | 0.85 | 0.45 | None | 1.0 | `get_tarnished_wrought_iron()` ("iron") |
| `TarnishedBronze` | `(0.28, 0.23, 0.14, 1.0)` | 0.46 | 0.85 | 0.45 | None | 1.0 | `get_tarnished_bronze()` ("bronze") |
| `AgedBone` | `(0.62, 0.57, 0.46, 1.0)` | 0.88 | 0.00 | 0.15 | None | 1.0 | `get_aged_bone()` ("agedbone") |
| `CandleWax` | `(0.76, 0.68, 0.50, 1.0)` | 0.56 | 0.00 | 0.22 | None | 1.0 | `get_candle_wax()` ("candlewax") |
| `CandleFlameGlow` | `(1.00, 0.72, 0.24, 1.0)` | 0.15 | 0.00 | 0.20 | `(1.0, 0.65, 0.18)` @ 4.2 | 1.0 | `get_candle_flame_glow()` ("candleflame") |
| `LeadGlassWindow` | `(0.18, 0.22, 0.25, 0.75)` | 0.20 | 0.10 | 0.30 | None | 0.75 | `null` (Preserved in GLB) ("leadglass") |
| `GlowingOccultRune` | `(0.92, 0.50, 1.00, 1.0)` | 0.30 | 0.00 | 0.15 | `(0.88, 0.42, 1.0)` @ 2.6 | 1.0 | `get_glowing_occult_rune()` ("glowingoccultrune") |
| `SicklyGreenBile` | `(0.42, 0.90, 0.30, 1.0)` | 0.24 | 0.00 | 0.25 | `(0.45, 0.95, 0.35)` @ 2.4 | 1.0 | `get_sickly_green_bile()` ("sicklygreenbile") |
| `FrozenBlueSoul` | `(0.35, 0.70, 1.00, 1.0)` | 0.26 | 0.00 | 0.25 | `(0.35, 0.65, 1.0)` @ 2.6 | 1.0 | `get_frozen_blue_soul()` ("frozenbluesoul") |
| `AbyssalCrimson` | `(0.95, 0.12, 0.15, 1.0)` | 0.28 | 0.00 | 0.20 | `(1.0, 0.15, 0.18)` @ 3.0 | 1.0 | `get_abyssal_crimson()` ("abyssalcrimson") |
| `DarkCisternWater` | `(0.05, 0.09, 0.12, 1.0)` | 0.14 | 0.15 | 0.65 | None | 1.0 | `get_dark_cistern_water()` ("cisternwater") |
| `DarkContainmentHullStone` | `(0.06, 0.06, 0.08, 1.0)` | 0.95 | 0.00 | 0.08 | None | 1.0 | `get_dark_containment_hull_stone()` ("containmenthull") |
| `TerrainMoorGrass` | `(0.15, 0.17, 0.12, 1.0)` | 0.94 | 0.00 | 0.12 | None | 1.0 | `get_terrain_moor_grass()` ("moorgrass") |
| `TerrainMudPath` | `(0.18, 0.15, 0.12, 1.0)` | 0.91 | 0.00 | 0.15 | None | 1.0 | `get_terrain_mud_path()` ("mudpath") |
| `TerrainCliffStone` | `(0.24, 0.23, 0.24, 1.0)` | 0.92 | 0.00 | 0.15 | None | 1.0 | `get_terrain_cliff_stone()` ("cliff") |
| `OccultSilver` | `(0.58, 0.60, 0.64, 1.0)` | 0.36 | 0.88 | 0.45 | None | 1.0 | `get_occult_silver()` ("occultsilver") |
| `ConsecratedGold` | `(1.00, 0.78, 0.24, 1.0)` | 0.20 | 0.35 | 0.45 | `(1.0, 0.72, 0.18)` @ 2.8 | 1.0 | `get_consecrated_gold_liquid()` ("consecratedgold") |

---

## 2. Logic Chain

1. **Premise 1 (Material Library Compatibility)**: In `tools/build_prefabs_and_level.gd` (lines 200–214), whenever a `.glb` mesh is wrapped into a `.tscn` prefab, Godot checks `GrimdarkMaterialLibrary.get_material_for_name(mat_name)`. If the GLB uses material names matching this library, Godot replaces the surface material with the single-source-of-truth material with `vertex_color_use_as_albedo = true`, `normal_enabled = false`, and `cull_mode = CULL_DISABLED`. Therefore, creating `create_environment_voxel_palette()` in `tools/blender_micro_voxel_kit.py` with these exact 23 names guarantees 100% shader and material parity.
2. **Premise 2 (Micro-Voxel Shading & Baked Cavity)**: In `blender_micro_voxel_kit.py`, both `MicroVoxelBuilder` and `WeaponVoxelBuilder` wire `ShaderNodeVertexColor("Col")` into `Base Color`. During mesh extraction, `build_bmesh()` calculates:
   - 26-neighborhood cavity ambient occlusion: `ao = 1.0 - (occ_neighbors / 26.0) * 0.28`.
   - Directional face shading across the 6 orthogonal voxel quad faces (top face highlighted at 1.06, underside shadowed at 0.78–0.80).
   - Deterministic per-voxel hash jitter (±4%).
   - Internal face culling (never generating quads between adjacent filled voxels).
   Therefore, an `EnvironmentVoxelBuilder` adopting this same pipeline will produce identical hyper-detailed micro-voxel surfaces across all architectural and hub assets.
3. **Premise 3 (Voxel Size Scaling for Environment)**: Weapons use 4mm (0.004m) voxels because they are held 0.5m from the first-person camera. Armor uses 9mm–18mm voxels. Large environment pieces (such as 4m walls, 12m gables, and 20m plinths) require a voxel size tailored to scale:
   - For Hub Stations and Props (workbench, armor rack, upgrade font, sconce): `voxel_size = 0.02m` to `0.025m` (20mm–25mm). This gives 80–120 voxels across a 2.5m station, resulting in crisp details (cartridge blocks, vice handles, helmet visors, runes) while keeping polygon count under 12,000 tris and GLB size under 1 MB.
   - For 4m Modular Architecture Kit (walls, floors, vaults, stairs): `voxel_size = 0.04m` to `0.05m` (40mm–50mm). This gives an 80x80 grid for 4m faces and 10–12 voxel layers across 0.48m thick walls, providing rich masonry stepped relief while maintaining 60+ FPS performance.
   - For Massive Church Exterior Shell (12m x 20m plinth, 18m spire): `voxel_size = 0.08m` to `0.10m` (80mm–100mm). This ensures memory efficiency and fast Blender execution.
4. **Premise 4 (Preservation of Bounding & Colliders)**: `town_overworld.tscn` positions `GothicChurch` at `(0, 4.0, 0)` and `ChurchFoundationPlinth` at `(0, 0, -20)`. The prefabs in `scenes/prefabs/architecture/` use primitive box and ramp colliders generated from `build_prefabs_and_level.gd`. Rebuilding the 16 `.glb` files with exact bounds and origin points ensures that no colliders, physics bodies, or scenes need to be recreated or adjusted.
5. **Premise 5 (Node Structure of `occult_rift_portal.glb`)**: The Godot script `OccultPortal` specifically accesses `PortalVortexMesh` as a child node. Therefore, `tools/blender_build_voxel_church_and_hub.py` must export `occult_rift_portal.glb` with two nodes (`OccultRiftArchway` parent and `PortalVortexMesh` child), rather than joining them into a single monolithic mesh.

---

## 3. Caveats

1. **Blender Execution Time**: Generating 16 micro-voxel models with 26-neighborhood cavity AO across millions of candidate voxels can take 15–45 seconds per complex asset. The script `tools/blender_build_voxel_church_and_hub.py` should implement CLI arguments (e.g. `--model=<name>` or `--all`) to allow building individual models or the full wave in one pass.
2. **GLB Export Attribute Flags**: In Blender 5.4.0 Alpha, `export_attributes=True` and `export_yup=True` are required. `export_all_vertex_colors=True` should also be passed for backward compatibility so the vertex color layer `"Col"` exports as standard `COLOR_0` in glTF.
3. **No Project Code Modification During Survey**: As an explorer subagent, all source code and assets were inspected in read-only mode. No modifications were made outside `.agents/teamwork/teamwork_explorer_survey_1/`.

---

## 4. Conclusion & Recommended Implementation Strategy

### 4.1 Requirement R1 Blueprint: Additions to `tools/blender_micro_voxel_kit.py`
Add the following functions and classes to `tools/blender_micro_voxel_kit.py`:

```python
def make_environment_pbr_material(
    name: str,
    base_rgb: tuple[float, float, float],
    roughness: float = 0.88,
    metallic: float = 0.0,
    emission_rgb: tuple[float, float, float] | None = None,
    emission_strength: float = 0.0,
    alpha: float = 1.0,
) -> bpy.types.Material:
    """Creates a standard environment PBR material with Vertex Color ('Col') driving Base Color."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat["_base_rgb"] = (float(base_rgb[0]), float(base_rgb[1]), float(base_rgb[2]))
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new(type="ShaderNodeOutputMaterial")
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    vcol = nodes.new(type="ShaderNodeVertexColor")
    vcol.layer_name = "Col"

    links.new(vcol.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic

    if alpha < 1.0 and "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = alpha
        if hasattr(mat, "blend_method"):
            mat.blend_method = 'BLEND'

    if emission_rgb is not None and emission_strength > 0.0:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*emission_rgb, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = emission_strength

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def create_environment_voxel_palette() -> dict[str, bpy.types.Material]:
    """Returns the unified 23-material Gothic environment palette."""
    return {
        "weathered_stone": make_environment_pbr_material("WeatheredAshlarStone", (0.32, 0.30, 0.28), roughness=0.92, metallic=0.0),
        "cobble_flagstone": make_environment_pbr_material("RoughCobbleFlagstone", (0.24, 0.23, 0.22), roughness=0.72, metallic=0.0),
        "carved_stone_trim": make_environment_pbr_material("CarvedStoneTrim", (0.36, 0.34, 0.32), roughness=0.84, metallic=0.0),
        "dark_slate_roof": make_environment_pbr_material("DarkSlateRoof", (0.18, 0.19, 0.22), roughness=0.89, metallic=0.0),
        "dirty_plaster": make_environment_pbr_material("DirtyPlaster", (0.38, 0.35, 0.31), roughness=0.93, metallic=0.0),
        "charred_timber": make_environment_pbr_material("RottedCharredTimber", (0.20, 0.14, 0.10), roughness=0.88, metallic=0.0),
        "wrought_iron": make_environment_pbr_material("TarnishedWroughtIron", (0.14, 0.14, 0.16), roughness=0.48, metallic=0.85),
        "bronze": make_environment_pbr_material("TarnishedBronze", (0.28, 0.23, 0.14), roughness=0.46, metallic=0.85),
        "bone": make_environment_pbr_material("AgedBone", (0.62, 0.57, 0.46), roughness=0.88, metallic=0.0),
        "wax": make_environment_pbr_material("CandleWax", (0.76, 0.68, 0.50), roughness=0.56, metallic=0.0),
        "candle_flame": make_environment_pbr_material("CandleFlameGlow", (1.0, 0.72, 0.24), roughness=0.15, metallic=0.0, emission_rgb=(1.0, 0.65, 0.18), emission_strength=4.2),
        "lead_glass": make_environment_pbr_material("LeadGlassWindow", (0.18, 0.22, 0.25), roughness=0.20, metallic=0.10, alpha=0.75),
        "occult_rune": make_environment_pbr_material("GlowingOccultRune", (0.92, 0.50, 1.0), roughness=0.30, metallic=0.0, emission_rgb=(0.88, 0.42, 1.0), emission_strength=2.6),
        "green_bile": make_environment_pbr_material("SicklyGreenBile", (0.42, 0.90, 0.30), roughness=0.24, metallic=0.0, emission_rgb=(0.45, 0.95, 0.35), emission_strength=2.4),
        "blue_soul": make_environment_pbr_material("FrozenBlueSoul", (0.35, 0.70, 1.0), roughness=0.26, metallic=0.0, emission_rgb=(0.35, 0.65, 1.0), emission_strength=2.6),
        "crimson": make_environment_pbr_material("AbyssalCrimson", (0.95, 0.12, 0.15), roughness=0.28, metallic=0.0, emission_rgb=(1.0, 0.15, 0.18), emission_strength=3.0),
        "water": make_environment_pbr_material("DarkCisternWater", (0.05, 0.09, 0.12), roughness=0.14, metallic=0.15),
        "containment_hull": make_environment_pbr_material("DarkContainmentHullStone", (0.06, 0.06, 0.08), roughness=0.95, metallic=0.0),
        "moor_grass": make_environment_pbr_material("TerrainMoorGrass", (0.15, 0.17, 0.12), roughness=0.94, metallic=0.0),
        "mud_path": make_environment_pbr_material("TerrainMudPath", (0.18, 0.15, 0.12), roughness=0.91, metallic=0.0),
        "cliff_stone": make_environment_pbr_material("TerrainCliffStone", (0.24, 0.23, 0.24), roughness=0.92, metallic=0.0),
        "silver": make_environment_pbr_material("OccultSilver", (0.58, 0.60, 0.64), roughness=0.36, metallic=0.88),
        "gold": make_environment_pbr_material("ConsecratedGold", (1.0, 0.78, 0.24), roughness=0.20, metallic=0.35, emission_rgb=(1.0, 0.72, 0.18), emission_strength=2.8),
    }


class EnvironmentVoxelBuilder:
    """
    Blender World-Space Micro-Voxel Builder for Environment & Architecture.
    Blender Coordinate Convention:
      - `ix` = X in Blender (Right/Left)
      - `iy` = Y in Blender (North/South)
      - `iz` = Z in Blender (Up/Down)
    When exported with `export_yup=True`:
      - Blender +X -> Godot +X
      - Blender +Z -> Godot +Y (Up)
      - Blender -Y -> Godot +Z (Forward/South)
    """
    def __init__(self, name: str, voxel_size: float = 0.04, palette: dict[str, bpy.types.Material] | None = None) -> None:
        self.name: str = name
        self.voxel_size: float = voxel_size
        self.palette: dict[str, bpy.types.Material] = palette if palette is not None else {}
        self.voxels: dict[tuple[int, int, int], tuple[str, float]] = {}

    def set_world(self, wx: float, wy: float, wz: float, mat_key: str, shade_bias: float = 1.0) -> None:
        s = self.voxel_size
        self.voxels[(int(round(wx / s)), int(round(wy / s)), int(round(wz / s)))] = (mat_key, float(shade_bias))

    def fill_world_box(self, x0: float, x1: float, y0: float, y1: float, z0: float, z1: float, mat_key: str, shade_bias: float = 1.0) -> None:
        s = self.voxel_size
        ix0, ix1 = int(round(min(x0, x1) / s)), int(round(max(x0, x1) / s))
        iy0, iy1 = int(round(min(y0, y1) / s)), int(round(max(y0, y1) / s))
        iz0, iz1 = int(round(min(z0, z1) / s)), int(round(max(z0, z1) / s))
        for ix in range(ix0, ix1 + 1):
            for iy in range(iy0, iy1 + 1):
                for iz in range(iz0, iz1 + 1):
                    self.voxels[(ix, iy, iz)] = (mat_key, float(shade_bias))

    def carve_world_box(self, x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> None:
        s = self.voxel_size
        ix0, ix1 = int(round(min(x0, x1) / s)), int(round(max(x0, x1) / s))
        iy0, iy1 = int(round(min(y0, y1) / s)), int(round(max(y0, y1) / s))
        iz0, iz1 = int(round(min(z0, z1) / s)), int(round(max(z0, z1) / s))
        for ix in range(ix0, ix1 + 1):
            for iy in range(iy0, iy1 + 1):
                for iz in range(iz0, iz1 + 1):
                    self.voxels.pop((ix, iy, iz), None)

    def fill_pointed_arch(self, cx: float, cy: float, base_z: float, spring_z: float, peak_z: float, span_w: float, depth_y: float, wall_thick: float, mat_key: str) -> None:
        # Procedural Gothic pointed arch voxel filler
        ...
```

### 4.2 Requirement R2 Blueprint: `tools/blender_build_voxel_church_and_hub.py`
Structure `tools/blender_build_voxel_church_and_hub.py` as an independent script responsible for building the 16 models:
- **Modular Architecture Pieces (7 models in `assets/models/church_kit/`)**:
  - `floor_stone_4x4.glb`: Size `[4.0, 4.0, 0.375]`, top surface at Z=0.0. `cobble_flagstone` interior tiles, `carved_stone_trim` perimeter border, `weathered_stone` underside slab.
  - `wall_stone_solid.glb`: Size `[4.28, 0.64, 4.05]`, solid thickness 0.48m (with decorative buttress piers to 0.64m). `weathered_stone` ashlar courses, `carved_stone_trim` base plinth and cornice, `wrought_iron` structural ties.
  - `wall_stone_window.glb`: Size `[4.28, 0.64, 4.05]`, center lancet window carved with `lead_glass` stained glass pane.
  - `wall_stone_arch_door.glb`: Size `[4.28, 0.64, 4.05]`, walkable opening `X in [-1.2, +1.2], Z in [0.0, 3.45]` with pointed arch voussoirs.
  - `roof_gothic_vault_4x4.glb`: Size `[4.18, 4.18, 1.01]`, ceiling deck Z in `[0.0, 0.48]`, exterior slate cap Z in `[0.48, 0.66]`, chamfered diagonal vault ribs descending to Z=-0.35.
  - `stairs_stone_4x4.glb`: Size `[4.04, 4.045, 4.85]`, 16 stepped treads descending from top landing (Y=+2.0, Z=0.0) to bottom (Y=-2.0, Z=-4.0), matching the Godot `extra_stairs_ramp` collision volume.
  - `wall_lantern_sconce.glb`: Size `[0.28, 0.54, 0.47]`, wrought-iron mounting plate flush at Y=0.0, hexagonal lantern cage with `candle_flame` emissive core and `lead_glass` frosted panels.
- **Exterior Church Components (5 models in `assets/models/church_kit/`)**:
  - `church_foundation_plinth.glb`: Size `[12.70, 23.125, 2.755]`, depth Z in `[-2.50, 0.0]`. Preserves upper stairwell/crypt cutout (`X in [-4.5, +4.5], Y in [-0.5, +12.5]`), subterranean clearance (`X in [-7.0, +7.0], Y in [+1.8, +14.0]`), and 5 South entrance steps (descending to local Z=-0.88m, meeting world plaza Y=3.20m).
  - `church_front_gable_rose.glb`: Size `[12.77, 0.64, 6.76]`, 45-degree triangular gable with recessed circular Rose Window (radius 1.60m, center Z=3.10m) with 8 radial stone spokes and `lead_glass` / `occult_rune` disk.
  - `church_pitched_roof_12x16.glb`: Size `[13.04, 17.04, 7.51]`, 45-degree sloped roof with `dark_slate_roof` tiles, ridge cresting at Z=6.32m, and corbelled eaves.
  - `church_bell_tower_spire.glb`: Size `[4.86, 4.86, 18.50]`, 3 stages: Base Tower (0–5m), Belfry with lancet openings and `bronze` bell (5–10.5m), Octagonal Needle Spire (10.5–17m) with `wrought_iron` cross finial (17–18.5m).
  - `church_buttress.glb`: Size `[1.24, 1.95, 9.05]`, 3-stage stepped buttress with sloped weatherings.
- **Hub Stations (4 models)**:
  - `hub_weapon_workbench.glb` (`assets/models/church_kit/`): Size `[2.88, 1.16, 2.22]`, pegged `charred_timber` table with `wrought_iron` vice, barrel clamp, ammo crates, powder keg, open ledger, and blue-flame burner.
  - `hub_armor_reliquary_stand.glb` (`assets/models/church_kit/`): Size `[2.20, 1.02, 2.42]`, stepped `cobble_flagstone` and timber dais with iron mannequin frame, `silver` and `bronze` cuirass, 4-lame pauldrons, great-helm, and halo finial.
  - `hub_sanctuary_upgrade_font.glb` (`assets/models/church_kit/`): Size `[1.60, 1.60, 1.88]`, octagonal limestone pedestal, fluted bronze basin, and pool of `gold` liquid oil (`ConsecratedGold`).
  - `occult_rift_portal.glb` (`assets/models/architecture/`): Size `[3.60, 1.24, 4.30]`, blood-stone archway with parent node `OccultRiftArchway` and separate child plane `PortalVortexMesh` (2.2m x 3.2m, centered at Z=1.88m, UVs [0..1]).

---

## 5. Verification Method

To independently verify the survey findings and subsequent implementation:

1. **Verify Existing Models Telemetry**:
   ```powershell
   & "C:\Users\olema\Downloads\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender.exe" --background --python-expr "
   import bpy
   bpy.ops.import_scene.gltf(filepath='assets/models/church_kit/church_foundation_plinth.glb')
   print([o.name for o in bpy.context.scene.objects])
   "
   ```
2. **Verify Python Script Parse & Imports**:
   ```powershell
   & "C:\Users\olema\Downloads\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender.exe" --background --python tools/blender_build_voxel_church_and_hub.py
   ```
3. **Verify Headless Godot Asset Import**:
   ```powershell
   & "C:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --quit-after 240 --path . --import
   ```
   **Pass Condition**: Exit code 0, all 16 GLB imports cleanly generated in `.godot/imported/`.
4. **Visual Frame Capture**:
   ```powershell
   & "C:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --path . -s res://tools/mcp_capture_frame.gd -- --view=church --frames=45
   ```
   Inspect `res://.mcp_captures/latest_frame.png` to verify the micro-voxel rendering and lighting.
