# Dispatch for teamwork_explorer_survey_r2_3

## Objective
Investigate Feature 5 (Procedural Weapon Recoil in `scripts/player/fps_viewmodel_controller.gd`), Feature 6 (Micro-Voxel enemies and potion flasks), and Feature 7 (Verification CLI commands).

## Inputs
- Authoritative User Request: `c:\Users\olema\Downloads\alpha branch\.agents\teamwork\ORIGINAL_REQUEST.md`
- Approved Plan: `C:\Users\olema\.gemini\antigravity\brain\3fdccabf-a502-4898-a4fc-87712a69f098\implementation_plan.md`
- Target Files:
  - `c:\Users\olema\Downloads\alpha branch\scripts\player\fps_viewmodel_controller.gd`
  - `c:\Users\olema\Downloads\alpha branch\tools\blender_build_voxel_enemies.py`
  - `c:\Users\olema\Downloads\alpha branch\tools\blender_build_voxel_town_and_loot.py`
  - `c:\Users\olema\Downloads\alpha branch\scripts\items\loot_drop_pickup.gd`

## Tasks
1. Read `ORIGINAL_REQUEST.md` first.
2. In `fps_viewmodel_controller.gd`, inspect `trigger_shoot_recoil(intensity: float = 1.0)` and `_apply_hand_transforms()`. Determine exact line numbers, variables (`_weapon_mount_recoil_pos`, `_weapon_mount_recoil_rot`, `_weapon_recoil_tween`), and recoil math.
3. In `blender_build_voxel_enemies.py`, inspect `build_ossuary_executioner` and `build_reliquary_hex_weaver`. Find where smooth primitives (`add_cyl`, `add_sphere`, `add_cone`) are used and how to apply `voxelize_object_hierarchy(root_obj, voxel_size=0.010)` while preserving the articulated limb hierarchy nodes.
4. In `blender_build_voxel_town_and_loot.py`, inspect `build_loot_alchemical_elixir()` to replace smooth sphere/cylinder primitives with stepped micro-voxels.
5. In `loot_drop_pickup.gd`, inspect `_build_procedural_fallback_mesh()` to replace `SphereMesh` fallback with micro-voxel stepped box geometry.
6. Check the exact Godot headless CLI `--check-only` commands and verification steps.
7. Output a detailed report to `.agents/teamwork/teamwork_explorer_survey_r2_3/handoff.md`.

## 2026-11-01T15:27:22Z
You are Survey Explorer 3 for the 5 Gameplay, Stairwell & Visual Fixes.
Your working directory is: c:\Users\olema\Downloads\alpha branch\.agents\teamwork\teamwork_explorer_survey_r2_3\
Read DISPATCH.md in your working directory and ORIGINAL_REQUEST.md at c:\Users\olema\Downloads\alpha branch\.agents\teamwork\ORIGINAL_REQUEST.md.
Also read C:\Users\olema\.gemini\antigravity\brain\3fdccabf-a502-4898-a4fc-87712a69f098\implementation_plan.md.

Focus on:
1. Feature 5: Procedural weapon recoil in `scripts/player/fps_viewmodel_controller.gd` (`trigger_shoot_recoil(intensity)`: kick `position.z += 0.055`, upward pitch `rotation.x += deg_to_rad(5.5)`, snap back over 0.14s).
2. Feature 6: Micro-Voxelization of enemies and potion flasks:
   - `tools/blender_build_voxel_enemies.py` (convert smooth primitives on Executioner & Hex-Weaver to 8mm–12mm micro-voxels while preserving articulated limbs)
   - `tools/blender_build_voxel_town_and_loot.py` (convert alchemical elixir flask to micro-voxels)
   - `scripts/items/loot_drop_pickup.gd` (replace `SphereMesh` fallback with micro-voxel multi-box)
3. Feature 7: CLI verification commands (`godot --headless --path . --check-only -s <script.gd>`).

Produce a complete, detailed handoff report in your working directory at `handoff.md` with:
- Exact line numbers and code snippets to modify
- Precise implementation details adhering to AGENTS.md (strict Godot 4.7 typing, no untyped variables, surgical edits <= 250 lines)
- Risk analysis and edge cases
When finished, notify me via send_message with a brief summary and the path to your handoff.md.
