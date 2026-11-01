# Project: Micro-Voxel Model Conversion (Option A Full Parallel Blitz)

## Architecture
- **Art Direction**: Hyper-Detailed Ultra-Realistic Micro-Voxel style with 26-neighborhood cavity AO, directional face shading, and deterministic vertex color baking (`vertex_color_use_as_albedo = true`).
- **PBR Material System**: 23 unified environment materials in `create_environment_voxel_palette()` in `tools/blender_micro_voxel_kit.py` mirroring `GrimdarkMaterialLibrary.get_material_for_name()` in `scripts/environment/material_library.gd`.
- **Modular Kit Grids**: 4m × 4m × 4m architecture with 0.40m–0.56m solid wall thickness for light-bleed isolation (AGENTS.md Rule 9.4), doorway clearances >= 2.45m.
- **Stepped Micro-Voxel Terrain**: 120m × 120m terrain with stepped micro-voxel terracing (individual riser step height = 0.18m <= 0.20m, within player max_step_height = 0.36m), flattened building footprints (House A at Y=0.85m, House B at Y=1.15m, Church plateau at Y=3.55m), subterranean roof clearance Y >= 4.35m, and exact Boolean stairwell cutout at X=0, Z=-22 (bounds X:[-13.8, 13.8], Z:[-57.8, -22.0]).
- **Rigged & Animated Entities**:
  - Chests: `prop_gothic_reliquary_chest.glb` with `ChestBase` and `ChestLid` child node pivoted at (0.0, 0.58, 0.41) for interaction.
  - Enemies (all 11): Articulated node hierarchy (`Pelvis`, `Torso`, `Head`, `UpperArmL`/`ArmLeft`, `ForearmL`/`ShieldLeft`, `UpperArmR`/`ArmRight`, `ForearmR`/`WeaponRight`, `ThighL`, `ShinL`, `ThighR`, `ShinR`, `SecondaryProp`) facing Blender -Y (Godot -Z forward).
- **Execution Pipeline**:
  - Blender scripts run headlessly via local Blender 5.4.0 executable.
  - Headless Godot import pass runs once after all exports complete.
  - In-game frame captures via `tools/mcp_capture_frame.gd`.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Shared Environment Voxel Palette & Builder | 23 materials matching `GrimdarkMaterialLibrary` and `EnvironmentVoxelBuilder` helper in `tools/blender_micro_voxel_kit.py` | M0 | Survey R1 |
| 2 | Modular Church Architecture Kit | 7 models in `assets/models/church_kit/` (floor, solid wall, window, arch door, vault, stairs, lantern sconce) | M1 | Survey R2 |
| 3 | Church Exterior Shell & Plinth | 5 models in `assets/models/church_kit/` (plinth with stairwell opening and entrance steps, front gable rose, pitched roof, spire, buttress) | M1 | Survey R2 |
| 4 | Church Hub Stations & Occult Portal | 4 models (workbench, armor reliquary, upgrade font in `church_kit/`, `occult_rift_portal.glb` with child vortex mesh in `architecture/`) | M1 | Survey R2 |
| 5 | Modular Crypt & Catacombs Kit | 8 models in `assets/models/church_kit/` (corridor vault, ossuary wall, portcullis arch, pillar, containment hull, iron gate cell, drowned cistern, rotting bookshelf) | M2 | Survey R3 |
| 6 | Crypt Focal Props & Clutter | 13 models in `assets/models/church_kit/` (altar, sarcophagus, lectern, hanging cage, cauldron, weeping statue, sunken bell, obelisk, brazier, chains/roots, candle cluster, bone pile, crates/barrels) | M2 | Survey R3 |
| 7 | Ossuary Variety Dungeon Kit | 6 models in `assets/models/ossuary_variety/` (bridge, balcony railing, buttress arch, bone chandelier, spine reliquary, burial niche divider) | M3 | Survey R4 |
| 8 | Biomes 2-4 Dungeon Kit | 9 models in `assets/models/dungeon/` (Necropolis armory wall, iron maiden, war brazier; Reliquary grimoire wall, orrery, chandelier astrolabe; Abattoir furnace wall, blood press, hook rack) | M3 | Survey R4 |
| 9 | Town Overworld & Foliage Models | 8 models (gravestone cluster, graveyard wall, road curb, street lamp in `church_kit/`; house A and house B with 3m plinths, dead tree, wild grass in `assets/models/`) | M4 | Survey R5 |
| 10 | Stepped Micro-Voxel Terrain | `terrain_town.glb` in `assets/models/` with 0.18m steps, building footprints, and stairwell cutout at X=0, Z=-22 | M4 | Survey R5 |
| 11 | Loot Drops & Reliquary Chest | 4 models in `assets/models/items/` (blood echo, talisman, elixir, chest with `ChestBase` and `ChestLid`) | M4 | Survey R5 |
| 12 | Standard Enemies (3 models) | `enemy_ossuary_skeleton.glb`, `enemy_plague_acolyte.glb`, `enemy_iron_penitent.glb` with articulated limb hierarchies | M5 | Survey R6 |
| 13 | Biome Bosses & Elites (8 models) | `enemy_01` through `enemy_08` with articulated limb hierarchies and signature weapons/props | M5 | Survey R6 |
| 14 | Headless Godot Import Pass | `godot --headless --quit-after 240 --path . --import` cleanly updating `.godot/imported/` | M6 | Survey Pipeline |
| 15 | Visual Frame Captures & Verification | In-game verification via `tools/mcp_capture_frame.gd` and physics raycast checks | M6 | Survey Pipeline |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M0 | Shared Voxel Palette & Helper Extension | Extend `tools/blender_micro_voxel_kit.py` with 23 materials and `EnvironmentVoxelBuilder` | none | DONE |
| M1 | Wave 1A: Church Sanctuary & Hub Stations | 16 models via `tools/blender_build_voxel_church_and_hub.py` | M0 | DONE |
| M2 | Wave 1B: Crypt, Catacombs & Clutter | 21 models via `tools/blender_build_voxel_crypt_kit.py` | M0 | DONE |
| M3 | Wave 1C: Ossuary Variety & Biomes 2-4 | 15 models via `tools/blender_build_voxel_dungeons_biomes.py` | M0 | DONE |
| M4 | Wave 1D: Town Overworld, Stepped Terrain & Loot | 13 models via `tools/blender_build_voxel_town_and_loot.py` | M0 | DONE |
| M5 | Wave 1E: All 11 Enemies & Bosses | 11 models via `tools/blender_build_voxel_enemies.py` | M0 | DONE |
| M6 | Integration, Headless Godot Import & Verification | Run Godot import pass, frame capture tests, and multi-agent audit | M1, M2, M3, M4, M5 | DONE |

## Interface Contracts
### `blender_micro_voxel_kit.py` ↔ Builder Scripts
- `create_environment_voxel_palette() -> dict[str, bpy.types.Material]`:
  Keys: `weathered_stone`, `cobble_flagstone`, `carved_stone_trim`, `dark_slate_roof`, `dirty_plaster`, `charred_timber`, `wrought_iron`, `bronze`, `bone`, `wax`, `candle_flame`, `lead_glass`, `occult_rune`, `green_bile`, `blue_soul`, `crimson`, `water`, `containment_hull`, `moor_grass`, `mud_path`, `cliff_stone`, `silver`, `gold`.
- `EnvironmentVoxelBuilder`:
  Methods: `set_world(wx, wy, wz, mat_key, shade_bias=1.0)`, `fill_world_box(x0, x1, y0, y1, z0, z1, mat_key, shade_bias=1.0)`, `carve_world_box(x0, x1, y0, y1, z0, z1)`, `fill_world_cylinder_z(...)`, `build_mesh_object(...)`.
  Coordinates: Blender Z-Up, `export_yup=True` (maps Blender +X -> Godot +X, Blender +Z -> Godot +Y, Blender -Y -> Godot +Z).

## Code Layout
- `tools/blender_micro_voxel_kit.py`: Shared voxel library and material palette
- `tools/blender_build_voxel_church_and_hub.py`: Wave 1A generator (16 models)
- `tools/blender_build_voxel_crypt_kit.py`: Wave 1B generator (21 models)
- `tools/blender_build_voxel_dungeons_biomes.py`: Wave 1C generator (15 models)
- `tools/blender_build_voxel_town_and_loot.py`: Wave 1D generator (13 models / 14 entities)
- `tools/blender_build_voxel_enemies.py`: Wave 1E generator (11 models)
- `assets/models/church_kit/`: Modular church & crypt kit models
- `assets/models/architecture/`: `occult_rift_portal.glb`
- `assets/models/ossuary_variety/`: Ossuary bridge, railing, chandelier, etc.
- `assets/models/dungeon/`: Necropolis, Reliquary, Abattoir dungeon models
- `assets/models/`: Houses, foliage, `terrain_town.glb`
- `assets/models/items/`: Loot drops, `prop_gothic_reliquary_chest.glb`
- `assets/models/enemies/`: 11 enemy and boss models
