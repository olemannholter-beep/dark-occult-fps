## 2026-11-01T02:13:44Z
You are Survey Explorer 2 for the Micro-Voxel Conversion Project.
Your working directory is: c:\Users\olema\Downloads\alpha branch\.agents\teamwork\teamwork_explorer_survey_2
You MUST read c:\Users\olema\Downloads\alpha branch\.agents\teamwork\ORIGINAL_REQUEST.md before starting work.
Your scope is Requirements R3 and R4:
1. R3: Wave 1B: Crypt, Catacombs & Clutter Props (21 models):
   - Inspect existing scripts and assets: `tools/blender_build_crypt_kit.py`, `tools/blender_build_props.py`, etc.
   - Enumerate all 21 models in `res://assets/models/church_kit/`:
     - Modular crypt kit (8): `crypt_corridor_vault_4x4.glb`, `crypt_wall_ossuary_4x4.glb`, `crypt_archway_portcullis_4x4.glb`, `crypt_pillar.glb`, `crypt_containment_hull.glb`, `crypt_iron_gate_cell_4x4.glb`, `crypt_drowned_cistern_4x4.glb`, `crypt_rotting_bookshelf_4x4.glb`.
     - Crypt focal props (9): `crypt_altar.glb`, `crypt_sarcophagus_ornate.glb`, `crypt_lectern_grimoire.glb`, `crypt_hanging_cage.glb`, `crypt_plague_cauldron.glb`, `crypt_weeping_statue_pedestal.glb`, `crypt_sunken_bell_crater.glb`, `crypt_ritual_obelisk.glb`, `standing_iron_brazier.glb`.
     - Clutter assets (4): `clutter_ceiling_chains_roots.glb`, `clutter_melted_candle_cluster.glb`, `clutter_rubble_bones_pile.glb`, `clutter_wooden_crates_barrels.glb`.
   - Check 4m x 4m x 4m bounds, 0.4m-0.5m solid wall thickness for light-bleed isolation, origins, and collision/clearances.
   - Document script design for `tools/blender_build_voxel_crypt_kit.py`.
2. R4: Wave 1C: Ossuary Variety & Biomes 2–4 Dungeon Kits (15 models):
   - Inspect existing scripts/models: `tools/blender_build_ossuary_variety.py`, `tools/blender_build_dungeon_kit.py`, etc.
   - Enumerate the 6 models in `res://assets/models/ossuary_variety/`: `ossuary_balcony_railing_4m.glb`, `ossuary_bone_chandelier.glb`, `ossuary_burial_niche_divider_4x4.glb`, `ossuary_buttress_arch_4x4.glb`, `ossuary_spine_reliquary_monolith.glb`, `ossuary_stone_bridge_4x4.glb`.
   - Enumerate the 9 models in `res://assets/models/dungeon/`: `abattoir_blood_press_monolith.glb`, `abattoir_hanging_hook_rack.glb`, `abattoir_wall_furnace_4x4.glb`, `necropolis_hanging_war_brazier.glb`, `necropolis_iron_maiden_monolith.glb`, `necropolis_wall_armory_4x4.glb`, `reliquary_astral_orrery_monolith.glb`, `reliquary_chandelier_astrolabe.glb`, `reliquary_wall_grimoire_4x4.glb`.
   - Document bounds, modular connections, origins, materials, and script design for `tools/blender_build_voxel_dungeons_biomes.py`.
Document all findings, exact requirements, dependencies, and recommended implementation strategy in `c:\Users\olema\Downloads\alpha branch\.agents\teamwork\teamwork_explorer_survey_2\handoff.md`. Include a heartbeat in `progress.md`. Send completion message when done.
