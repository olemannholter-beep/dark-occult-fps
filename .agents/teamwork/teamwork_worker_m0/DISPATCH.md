## 2026-11-01T02:22:40Z
You are Worker M0 assigned to implement Milestone 0: Shared Environment & Rig Micro-Voxel Palette Extension.
Your working directory is: c:\Users\olema\Downloads\alpha branch\.agents\teamwork\teamwork_worker_m0
You MUST read c:\Users\olema\Downloads\alpha branch\.agents\teamwork\ORIGINAL_REQUEST.md before starting work.
Also read:
- c:\Users\olema\Downloads\alpha branch\.agents\teamwork\orchestrator\PROJECT.md
- c:\Users\olema\Downloads\alpha branch\.agents\teamwork\teamwork_explorer_survey_1\handoff.md (specifically Section 4.1 Blueprint)

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

CRITICAL SAFETY RULE:
`tools/blender_micro_voxel_kit.py` is currently ~702 lines. DO NOT overwrite the entire file with write_file! Use targeted edits or append mode to add the new functions and class without disturbing the existing `MicroVoxelBuilder` and `WeaponVoxelBuilder`.

Tasks:
1. File Ownership: You exclusively own `tools/blender_micro_voxel_kit.py`.
2. Implement `make_environment_pbr_material` matching PBR standards.
3. Implement `create_environment_voxel_palette()` with all 23 materials matching `GrimdarkMaterialLibrary.get_material_for_name()` in `scripts/environment/material_library.gd` (WeatheredAshlarStone, RoughCobbleFlagstone, CarvedStoneTrim, DarkSlateRoof, DirtyPlaster, RottedCharredTimber, TarnishedWroughtIron, TarnishedBronze, AgedBone, CandleWax, CandleFlameGlow, LeadGlassWindow, GlowingOccultRune, SicklyGreenBile, FrozenBlueSoul, AbyssalCrimson, DarkCisternWater, DarkContainmentHullStone, TerrainMoorGrass, TerrainMudPath, TerrainCliffStone, OccultSilver, ConsecratedGold).
4. Implement `EnvironmentVoxelBuilder` with coordinate transformation (Blender Z-up, export_yup=True), 26-neighborhood cavity AO (`ao = 1.0 - (occ / 26.0) * 0.28`), directional face shading, hash jitter (±4%), 6-neighbor internal face culling, and helper carving/filling methods (`set_world`, `fill_world_box`, `carve_world_box`, `fill_world_cylinder_z`, etc.).
5. Verify your implementation by running a headless Blender python command:
   `& "C:\Users\olema\Downloads\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender.exe" --background --python-expr "import sys; sys.path.insert(0, 'tools'); from blender_micro_voxel_kit import create_environment_voxel_palette, EnvironmentVoxelBuilder; p = create_environment_voxel_palette(); print('Palette keys:', len(p)); b = EnvironmentVoxelBuilder('test', 0.04, p); b.fill_world_box(-1, 1, -1, 1, 0, 1, 'weathered_stone'); obj = b.build_mesh_object(); print('Built test obj:', obj.name, len(obj.data.vertices))"`
6. Document verification commands and output in `handoff.md`. Send completion message when done.
