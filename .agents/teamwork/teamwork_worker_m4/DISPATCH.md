## 2026-11-01T15:42:44Z
You are Worker M4 for Milestone 4 (Procedural Weapon Recoil, Micro-Voxel Enemies, Terrain Cutout & Loot).
Your working directory is: c:\Users\olema\Downloads\alpha branch\.agents\teamwork\teamwork_worker_m4\
Read DISPATCH.md in your working directory and ORIGINAL_REQUEST.md at c:\Users\olema\Downloads\alpha branch\.agents\teamwork\ORIGINAL_REQUEST.md.
Also read Survey 2 handoff report (for terrain cutout) and Survey 3 handoff report (for recoil, enemies, and loot).

Implement:
1. `scripts/player/fps_viewmodel_controller.gd`: `_weapon_mount_recoil_pos`, `_weapon_mount_recoil_rot`, `_weapon_recoil_tween`, `trigger_shoot_recoil(intensity)` applying kick and snapping back over 0.14s, applied in `_apply_hand_transforms()`.
2. `tools/blender_build_voxel_enemies.py`: apply `remesh_to_micro_voxels()` on primitives before joining to preserve materials and articulated limb hierarchy.
3. `tools/blender_build_voxel_town_and_loot.py`: deterministic BMesh face deletion for stairwell cutout in `build_terrain_town()`, and stepped micro-voxels in `build_loot_alchemical_elixir()`.
4. `scripts/items/loot_drop_pickup.gd`: replace `SphereMesh` with `SurfaceTool` stepped micro-voxel box cluster.
5. Re-run headless Blender exports and headless Godot import.

Strictly adhere to Godot 4.7 static typing (AGENTS.md Rule 1) and surgical replacements <= 250 lines (AGENTS.md Rule 11.1).
Run all CLI checks and verify exit code 0.
Write your completion report to `handoff.md` in your working directory and notify me via send_message.
