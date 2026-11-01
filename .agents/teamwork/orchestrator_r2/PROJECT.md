# Project: 5 Gameplay, Stairwell & Visual Fixes

## Architecture
- `scripts/player/`: First-person body shadow-only mode (`first_person_body_controller.gd`) and procedural weapon mount recoil (`fps_viewmodel_controller.gd`).
- `scripts/world/`: Procedural dungeon stair floor and wall unblocking (`procedural_dungeon_generator.gd`).
- `scripts/ui/`: Gothic HUD top biome banner width expansion (`gothic_hud_overhaul.gd`).
- `scripts/interaction/`: Full-screen gothic loading overlay with detached tween lifecycle (`occult_portal.gd`) and `ReliquaryChest` property compatibility (`reliquary_chest.gd`).
- `scripts/items/`: Micro-voxel multi-box crystal fallback for loot pickups (`loot_drop_pickup.gd`).
- `tools/`: Procedural micro-voxel enemies (`blender_build_voxel_enemies.py`), town terrain cutout & alchemical potion flask (`blender_build_voxel_town_and_loot.py`), and level prefab builder (`build_prefabs_and_level.gd`).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | First-Person Camera Clipping Fix | Set `SHADOW_CASTING_SETTING_SHADOWS_ONLY` on player body meshes to stop frustum clipping when looking down | M1 | User Request & Survey 1 |
| 2 | Stairwell Wall Blockage & Texture Fix | Fix stairwell shafts, BMesh cutout, remove blocking bulkhead walls/floors across all stairs | M2 & M4 | User Request & Survey 2 |
| 3 | Top Compass Label Truncation Fix | Dynamically expand compass banner width based on font text metrics (>= 780px) | M2 | User Request & Survey 2 |
| 4 | Loading Overlay on Rift Portal | Full-screen etched-slate transition UI + double frame await before synchronous dungeon generation | M3 | User Request & Survey 1 |
| 5 | Procedural Weapon Recoil | Punchy recoil kick (+0.055 Z, +5.5 deg pitch, 0.14s tween) on weapon mount | M4 | User Request & Survey 3 |
| 6 | Micro-Voxelize Enemies & Potions | Remesh blocks / micro-voxel aesthetic on Executioner, Hex-Weaver, alchemical flask, and loot drops | M4 | User Request & Survey 3 |
| 7 | Comprehensive Headless CLI & Stair Verification | Run `--check-only` on all modified scripts and verify all staircases are unblocked and walkable | M5 | User Request & Survey 1, 2, 3 |

## Milestones
| # | Name | Scope & File Ownership | Dependencies | Status |
|---|------|------------------------|-------------|--------|
| M0 | Survey Phase | Map codebases, identify exact line ranges for all 5 fixes | none | DONE |
| M1 | FPS Camera Clipping Fix | `scripts/player/first_person_body_controller.gd` | M0 | DONE |
| M2 | Stairwells & Compass | `scripts/ui/gothic_hud_overhaul.gd`, `scripts/world/procedural_dungeon_generator.gd`, `tools/build_prefabs_and_level.gd` | M0 | DONE |
| M3 | Rift Loading Screen | `scripts/interaction/occult_portal.gd` | M0 | DONE |
| M4 | Recoil, Voxel Enemies & Loot | `scripts/player/fps_viewmodel_controller.gd`, `tools/blender_build_voxel_enemies.py`, `tools/blender_build_voxel_town_and_loot.py`, `scripts/items/loot_drop_pickup.gd` | M0 | DONE |
| M5 | Comprehensive Verification & Audit | CLI verification, physics/stair check, forensic integrity audit | M1, M2, M3, M4 | DONE |

## Exclusive File Ownership Matrix
- **Worker M1**: `scripts/player/first_person_body_controller.gd`
- **Worker M2**: `scripts/ui/gothic_hud_overhaul.gd`, `scripts/world/procedural_dungeon_generator.gd`, `tools/build_prefabs_and_level.gd`
- **Worker M3**: `scripts/interaction/occult_portal.gd`
- **Worker M4**: `scripts/player/fps_viewmodel_controller.gd`, `tools/blender_build_voxel_enemies.py`, `tools/blender_build_voxel_town_and_loot.py`, `scripts/items/loot_drop_pickup.gd`
- **Worker Remediation**: `scripts/interaction/occult_portal.gd`, `scripts/interaction/reliquary_chest.gd`

## Interface Contracts
- `FirstPersonBodyController`: `_apply_first_person_shadow_only(root_node: Node) -> void` sets shadow-only mode without affecting third-person paper-doll mannequin in Character Menu.
- `OccultPortal`: `trigger_portal_warp()` adds transition `CanvasLayer` at `layer = 120`, awaits 2 frames (when not headless), runs generation, then fades out and frees overlay via `overlay_layer.create_tween()`.
- `FPSViewmodelController`: `trigger_shoot_recoil(intensity: float = 1.0) -> void` animates right-hand mount offset with tween back to zero over 0.14s.
- `ProceduralDungeonGenerator`: `_seal_voxel_cells()` guards against placing `ProcFloor`, `SealerSubFloor`, or `ColFloor` over cells in `stair_cells` or `stair_cells.has(below_cell)`.
