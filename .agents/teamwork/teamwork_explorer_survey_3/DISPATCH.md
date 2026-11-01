## 2026-11-01T02:13:52Z
You are Survey Explorer 3 for the Micro-Voxel Conversion Project.
Your working directory is: c:\Users\olema\Downloads\alpha branch\.agents\teamwork\teamwork_explorer_survey_3
You MUST read c:\Users\olema\Downloads\alpha branch\.agents\teamwork\ORIGINAL_REQUEST.md before starting work.
Your scope is Requirements R5, R6, and Verification:
1. R5: Wave 1D: Town Overworld, Stepped Micro-Voxel Terrain & Loot (15 models):
   - Inspect existing scripts: `tools/blender_build_terrain.py`, `tools/blender_build_town.py`, `tools/blender_build_loot_and_spells.py`, etc.
   - Enumerate 4 models in `res://assets/models/church_kit/`: `town_gravestone_cluster.glb`, `town_graveyard_wall_fence_6m.glb`, `town_road_curb_8m.glb`, `town_street_lamp_iron.glb`.
   - Enumerate 5 models in `res://assets/models/`: `house_abandoned_a.glb` and `house_abandoned_b.glb` (both requiring 3.0m foundation plinths), `dead_tree_gnarled.glb`, `grass_clump_wild.glb`, and `terrain_town.glb`.
   - For `terrain_town.glb`, verify exact dimensions, heights, stairwell cutout at X=0, Z=-22, flattened building footprints, and stepped micro-voxel specification (step heights <= 0.20m, max_step_height = 0.36m).
   - Enumerate 4 models in `res://assets/models/items/`: `loot_alchemical_elixir.glb`, `loot_blood_echo_cluster.glb`, `loot_occult_relic_talisman.glb`, and `prop_gothic_reliquary_chest.glb` (preserving distinct `ChestBase` and `ChestLid` nodes for opening animation).
   - Document script design for `tools/blender_build_voxel_town_and_loot.py`.
2. R6: Wave 1E: All 11 Enemies & Bosses (11 models):
   - Inspect `tools/blender_build_enemies.py`, `scripts/enemies/`, and model assets in `res://assets/models/enemies/`.
   - Enumerate all 11 enemy models: `enemy_ossuary_skeleton.glb`, `enemy_plague_acolyte.glb`, `enemy_iron_penitent.glb`, `enemy_01_ossuary_executioner.glb`, `enemy_02_necropolis_praetorian.glb`, `enemy_03_reliquary_hexweaver.glb`, `enemy_04_inquisitor_rackmaster.glb`, `enemy_05_plague_bloater.glb`, `enemy_06_weeping_banshee.glb`, `enemy_07_bell_juggernaut.glb`, `enemy_08_abyssal_archon.glb`.
   - Verify exact node hierarchy requirements: `Torso`, `Head`, `ArmLeft`, `ArmRight`, `LegLeft`, `LegRight`, `WeaponRight`, `ShieldLeft` and ensure animation pivots/transforms match game AI expectations.
   - Document script design for `tools/blender_build_voxel_enemies.py`.
3. Verification & Pipeline:
   - Check Godot headless import command, collision generation expectations, and visual frame capture tool `tools/mcp_capture_frame.gd`.
   - Identify blender executable location and CLI parameters (`blender --background --python ...`).
Document all findings, exact requirements, dependencies, and recommended implementation strategy in `c:\Users\olema\Downloads\alpha branch\.agents\teamwork\teamwork_explorer_survey_3\handoff.md`. Include a heartbeat in `progress.md`. Send completion message when done.
