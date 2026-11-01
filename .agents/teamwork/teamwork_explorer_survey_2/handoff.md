# Survey Explorer 2 Handoff Report: Wave 1B (R3) & Wave 1C (R4) Architecture & Voxel Conversion

## 1. Observation

### 1.1 Existing Scripts, Asset Locations, and Tooling
Direct inspection of the repository codebase reveals the following existing scripts, materials, and model assets:

1. **Source Builder Scripts**:
   - `tools/blender_build_church_crypt_kit.py` (4,062 lines): Contains the procedural definitions for all 21 models of Wave 1B:
     - `build_crypt_corridor_vault_4x4` (line 1481)
     - `build_crypt_wall_ossuary_4x4` (line 1271)
     - `build_crypt_archway_portcullis_4x4` (line 1386)
     - `build_crypt_pillar` (line 496)
     - `build_crypt_containment_hull` (line 2653)
     - `build_crypt_iron_gate_cell_4x4` (line 1561)
     - `build_crypt_drowned_cistern_4x4` (line 2317)
     - `build_crypt_rotting_bookshelf_4x4` (line 1958)
     - `build_crypt_altar` (line 607)
     - `build_crypt_sarcophagus_ornate` (line 1651)
     - `build_crypt_lectern_grimoire` (line 2048)
     - `build_crypt_hanging_cage` (line 1762)
     - `build_crypt_plague_cauldron` (line 2184)
     - `build_crypt_weeping_statue_pedestal` (line 2398)
     - `build_crypt_sunken_bell_crater` (line 2509)
     - `build_crypt_ritual_obelisk` (line 1863)
     - `build_standing_iron_brazier` (line 1164)
     - `build_clutter_rubble_bones_pile` (line 3223)
     - `build_clutter_melted_candle_cluster` (line 3353)
     - `build_clutter_ceiling_chains_roots` (line 3442)
     - `build_clutter_wooden_crates_barrels` (line 3532)
   - `tools/blender_build_ossuary_variety_kit.py` (661 lines): Contains procedural definitions for all 6 models in `assets/models/ossuary_variety/`:
     - `build_ossuary_stone_bridge_4x4` (line 178)
     - `build_ossuary_balcony_railing_4m` (line 263)
     - `build_ossuary_buttress_arch_4x4` (line 328)
     - `build_ossuary_bone_chandelier` (line 407)
     - `build_ossuary_spine_reliquary_monolith` (line 494)
     - `build_ossuary_burial_niche_divider_4x4` (line 577)
   - `tools/blender_build_biomes_2_to_4.py` (1,133 lines): Contains procedural definitions for all 9 models in `assets/models/dungeon/`:
     - `build_necropolis_wall_armory_4x4` (line 336)
     - `build_necropolis_iron_maiden_monolith` (line 461)
     - `build_necropolis_hanging_war_brazier` (line 573)
     - `build_reliquary_wall_grimoire_4x4` (line 629)
     - `build_reliquary_astral_orrery_monolith` (line 734)
     - `build_reliquary_chandelier_astrolabe` (line 851)
     - `build_abattoir_wall_furnace_4x4` (line 906)
     - `build_abattoir_blood_press_monolith` (line 964)
     - `build_abattoir_hanging_hook_rack` (line 1055)
   - `tools/blender_micro_voxel_kit.py` (702 lines): Contains `MicroVoxelBuilder` and `WeaponVoxelBuilder` classes implementing 6-neighbor face culling, 26-neighborhood Ambient Occlusion (`ao = 1.0 - (occ_neighbors / 26.0) * 0.28`), directional face shading (Z+ 1.06, Z- 0.80, X+- 0.94, Y+- 0.96), height gradients, and vertex color baking (`Col`).
   - `scripts/environment/material_library.gd` (465 lines): Authoritative definition of 22 PBR standard materials (`StandardMaterial3D`) with `vertex_color_use_as_albedo = true` and `normal_enabled = false`.

2. **Model Asset Verification on Filesystem**:
   - All 21 target models in `res://assets/models/church_kit/` exist on disk.
   - All 6 target models in `res://assets/models/ossuary_variety/` exist on disk.
   - All 9 target models in `res://assets/models/dungeon/` exist on disk.
   - Total models in scope: 36 `.glb` files.

3. **Executable Paths**:
   - Blender 5.4.0: `C:\Users\olema\Downloads\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender.exe` (Verified: `Test-Path` returned True).
   - Godot Console: `C:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe` (Verified).

---

### 1.2 Wave 1B: Crypt, Catacombs & Clutter Props (21 Models) Catalog & Specifications

| # | Model Filename (`res://assets/models/church_kit/`) | Category | Dimensions (X, Y, Z in meters) | Wall Thickness / Bounds | Origin Anchor | Key Materials | Clearance / Collision Notes |
|---|---|---|---|---|---|---|---|
| 1 | `crypt_corridor_vault_4x4.glb` | Modular Architecture | 4.20m x 4.20m x 0.74m | 0.50m solid deck slab | Interface Z=0.0 (ribs hang down into -Z) | WeatheredAshlarStone, DarkFlagstone, WroughtIron, TarnishedBronze | Ceiling unit; ribs hang down 0.42m; flush with 4m wall top |
| 2 | `crypt_wall_ossuary_4x4.glb` | Modular Architecture | 4.20m x 0.54m x 4.05m | 0.52m–0.56m solid wall | Bottom-center (0,0,0) | WeatheredAshlarStone, DarkFlagstone, AgedBone, WroughtIron | Double-faced burial niches; Box collider (4.2, 4.05, 0.48) in prefab |
| 3 | `crypt_archway_portcullis_4x4.glb` | Modular Architecture | 4.20m x 0.54m x 4.05m | 0.54m jambs / plinths | Bottom-center (0,0,0) | WeatheredAshlarStone, DarkFlagstone, WroughtIron, TarnishedBronze | Walkable archway width 2.52m; portcullis spikes at Z >= 2.45m (> 2.2m player clearance) |
| 4 | `crypt_pillar.glb` | Modular Architecture | 0.96m x 0.96m x 4.00m | Octagonal plinth 0.96m | Bottom-center (0,0,0) | WeatheredAshlarStone, CarvedStoneTrim, WroughtIron | 12 stacked drum courses; 3 iron bands with rivets; fits 4m grid corridors |
| 5 | `crypt_containment_hull.glb` | Subterranean Isolation | 64.0m x 67.0m x 13.8m | Inverted bounding box | World Origin (0,0,0) under nave | DarkContainmentHullStone | Inward-pointing normals; wraps X:[-32,32], Y:[19,86], Z:[-10,3.8]; top stair opening |
| 6 | `crypt_iron_gate_cell_4x4.glb` | Modular Architecture | 4.20m x 0.50m x 4.05m | 0.48m dwarf & frame wall | Bottom-center (0,0,0) | WeatheredAshlarStone, DarkFlagstone, WroughtIron, TarnishedBronze | Central doorway width 1.48m, height 2.95m; gate swung open 54° for traversal |
| 7 | `crypt_drowned_cistern_4x4.glb` | Modular Architecture | 4.00m x 4.00m x 0.44m | 0.38m floor slab | Surface Z=0.0 (basin down to -0.26m) | WeatheredAshlarStone, DarkFlagstone, WroughtIron, DarkCisternWater | Recessed octagonal basin (r=1.32m); flush iron grates at Z=-0.02m; fully walkable |
| 8 | `crypt_rotting_bookshelf_4x4.glb` | Modular Architecture | 3.86m x 0.68m x 3.75m | 0.68m deep frame | Bottom-center (0,0,0) | RottedCharredTimber, WroughtIron, TarnishedBronze, AgedBone, GlowingOccultRune | 4 timber stiles; 5 shelves; tilted grimoires with glowing runes; skulls & scrolls |
| 9 | `crypt_altar.glb` | Focal Prop | 2.80m x 1.80m x 1.50m | 2-tier dais (2.8m, 2.4m) | Bottom-center (0,0,0) | WeatheredAshlarStone, DarkFlagstone, GlowingOccultRune, CandleWax, CandleFlameGlow | Carved sacrificial basin; front/top blood rune strips; 4 corner lit candles |
| 10 | `crypt_sarcophagus_ornate.glb` | Focal Prop | 1.56m x 2.68m x 1.45m | Plinth 1.56m x 2.68m | Bottom-center (0,0,0) | WeatheredAshlarStone, DarkFlagstone, AgedBone, TarnishedBronze, GlowingOccultRune | Hollow chest; rune bed with skull and ribs; heavy sculpted lid open 8° |
| 11 | `crypt_lectern_grimoire.glb` | Focal Prop | 1.20m x 1.20m x 1.85m | Base 1.20m octagonal | Bottom-center (0,0,0) | DarkFlagstone, WroughtIron, TarnishedBronze, AgedBone, GlowingOccultRune | Claw feet; iron shaft; open ancient leather grimoire with glowing occult sigils |
| 12 | `crypt_hanging_cage.glb` | Focal Prop | 0.80m x 0.80m x 2.93m | Cage r=0.38m; chain Z to 3.88m | Ground (0,0,0) / Ceiling anchor Z=3.88 | WroughtIron, TarnishedBronze, AgedBone | Rib-cage gibbet hanging Z=1.30m..2.55m; prisoner skeleton inside; 11 chain links |
| 13 | `crypt_plague_cauldron.glb` | Focal Prop | 2.40m x 2.40m x 2.95m | Furnace base r=1.20m | Bottom-center (0,0,0) | WeatheredAshlarStone, WroughtIron, TarnishedBronze, SicklyGreenBile | 2.2m cast-iron cauldron; boiling bile with 9 bubbles; 3 distillation pipes |
| 14 | `crypt_weeping_statue_pedestal.glb` | Focal Prop | 2.20m x 2.40m x 3.65m | Pedestal 2.2m x 2.4m | Bottom-center (0,0,0) | WeatheredAshlarStone, DarkFlagstone, WroughtIron, FrozenBlueSoul | 3.6m hooded robed figure; front offering basin; glowing pale-blue soul tear streams |
| 15 | `crypt_sunken_bell_crater.glb` | Focal Prop | 4.30m x 4.30m x 2.40m | Crater ring r=2.15m | Ground-center (0,0,0) | WeatheredAshlarStone, DarkFlagstone, TarnishedBronze, WroughtIron, AbyssalCrimson | 2.6m cracked cathedral bell tilted 25°; shattered rubble; glowing crimson fissure |
| 16 | `crypt_ritual_obelisk.glb` | Focal Prop | 1.90m x 1.90m x 3.82m | 3-step plinth (1.9m) | Bottom-center (0,0,0) | WeatheredAshlarStone, DarkFlagstone, WroughtIron, TarnishedBronze, AbyssalCrimson | Tapered octagonal shaft; 4 cardinal channels with AbyssalCrimson runes; 4 candle dishes |
| 17 | `standing_iron_brazier.glb` | Focal Prop | 0.84m x 0.84m x 1.35m | Tripod base r=0.42m | Bottom-center (0,0,0) | WroughtIron, CandleFlameGlow | Tripod legs; iron collar; fire basket bowl with upper rim torus; glowing embers |
| 18 | `clutter_ceiling_chains_roots.glb` | Clutter Asset | 1.80m x 1.80m x 2.10m | Hanging down Z: 0.0 to -2.10 | Ceiling anchor Z=0.0 | WroughtIron, RottedCharredTimber, DarkFlagstone | 5 ceiling plates with rivets; hanging chains with forged hooks; 10 gnarled tree roots |
| 19 | `clutter_melted_candle_cluster.glb` | Clutter Asset | 0.68m x 0.52m x 0.42m | Tray 0.68m x 0.52m | Bottom-center (0,0,0) | AgedBone / CandleWax, TarnishedBronze, WroughtIron, CandleFlameGlow | 24 wax pool lobes; 14 varied candles with drip rivulets, wicks and glowing flames |
| 20 | `clutter_rubble_bones_pile.glb` | Clutter Asset | 1.90m x 1.90m x 0.45m | Radial mound r=0.95m | Bottom-center (0,0,0) | WeatheredAshlarStone, DarkFlagstone, AgedBone, WroughtIron | 48 masonry blocks; 3 pillar drums; 8 geometric skulls; 20 bones; 18 chain links |
| 21 | `clutter_wooden_crates_barrels.glb` | Clutter Asset | 1.50m x 1.20m x 1.15m | Footprint 1.5m x 1.2m | Bottom-center (0,0,0) | RottedCharredTimber, WroughtIron, TarnishedBronze | 2 oak staved barrels with 4 iron hoops; 2 slatted munitions crates with corner brackets |

---

### 1.3 Wave 1C: Ossuary Variety & Biomes 2–4 Dungeon Kits (15 Models) Catalog & Specifications

| # | Model Filename | Directory | Category | Dimensions (X, Y, Z) | Origin Anchor | Key Materials | Clearance / Mechanical Features |
|---|---|---|---|---|---|---|---|
| 1 | `ossuary_stone_bridge_4x4.glb` | `ossuary_variety/` | Modular Architecture | 2.20m W x 4.00m L x 2.45m H | Walkway deck Z=0.0 | WeatheredAshlarStone, DarkFlagstone, CarvedStoneTrim, WroughtIron, AgedBone | 2.2m wide walk-across deck; 32 flagstone cobbles; twin underslung ribs; 6 skull bollards & chain rails |
| 2 | `ossuary_balcony_railing_4m.glb` | `ossuary_variety/` | Modular Architecture | 4.04m W x 0.36m D x 1.35m H | Base center (0,0,0) | WeatheredAshlarStone, DarkFlagstone, CarvedStoneTrim, WroughtIron, AgedBone, CandleWax | Stepped base; 3 newel posts with iron spikes & skulls; 12 balusters; 18 iron pickets; 4 candles |
| 3 | `ossuary_buttress_arch_4x4.glb` | `ossuary_variety/` | Modular Architecture | 4.04m W x 0.96m D x 4.05m H | Bottom-center (0,0,0) | WeatheredAshlarStone, DarkFlagstone, CarvedStoneTrim, WroughtIron, AgedBone | Walk-through opening 2.52m wide, peak Z=3.82m; 5 tiered skull niches per pier; keystone skull |
| 4 | `ossuary_bone_chandelier.glb` | `ossuary_variety/` | Focal Prop / Centerpiece | 2.56m Diam x 2.40m H | Ceiling mount Z=2.40m | WroughtIron, TarnishedBrass, AgedBone, CandleWax, CandleFlameGlow | 2-tier wheel (r=1.25m, 0.72m); 24 skull candle stations; suspension chains; bottom drop finial |
| 5 | `ossuary_spine_reliquary_monolith.glb` | `ossuary_variety/` | Focal Prop / Monolith | 1.65m x 1.65m x 3.42m | Bottom-center (0,0,0) | WeatheredAshlarStone, DarkFlagstone, WroughtIron, AgedBone, TarnishedBrass, AbyssalCrimson | Stepped plinth; 18 fused vertebrae column; glowing crimson-amber soul core; 3 brass astrolabe rings |
| 6 | `ossuary_burial_niche_divider_4x4.glb` | `ossuary_variety/` | Modular Architecture | 3.28m W x 0.62m D x 2.95m H | Bottom-center (0,0,0) | WeatheredAshlarStone, DarkFlagstone, CarvedStoneTrim, WroughtIron, AgedBone, CandleWax | Maze divider wall; central barred window; 8 burial niche bays with 16 skull clusters; 6 candles |
| 7 | `necropolis_wall_armory_4x4.glb` | `dungeon/` | Modular Architecture | 4.00m W x 0.50m D x 4.00m H | Bottom-center (0,0,0) | WeatheredAshlarStone, CarvedStoneTrim, WroughtIron, TarnishedBrass, DarkTimber, CandleFlameGlow | 0.5m solid wall; 3 armored pilasters; 2 alcoves with portcullis bars; crossed halberds & tower shields |
| 8 | `necropolis_iron_maiden_monolith.glb` | `dungeon/` | Focal Prop / Monolith | 2.40m x 2.40m x 3.80m | Bottom-center (0,0,0) | WeatheredAshlarStone, CarvedStoneTrim, WroughtIron, TarnishedBrass, DarkTimber, CandleFlameGlow | Octagonal war-plinth; iron maiden body (Z=1.55 to 3.65); glowing visor slits; 4 greatswords; 4 braziers |
| 9 | `necropolis_hanging_war_brazier.glb` | `dungeon/` | Focal Prop / Centerpiece | 1.80m Diam x 1.75m H | Ceiling mount Z=0.0 | WroughtIron, TarnishedBrass, CandleFlameGlow | Hanging Z: 0.0 to -1.75m; outer war-cage ring; coal basket with glowing embers; 4 chains; 12 war-spikes |
| 10 | `reliquary_wall_grimoire_4x4.glb` | `dungeon/` | Modular Architecture | 4.00m W x 0.50m D x 4.00m H | Bottom-center (0,0,0) | WeatheredAshlarStone, CarvedStoneTrim, DarkTimber, TarnishedBrass, WroughtIron, AgedBone, GlowingOccultRune | 0.5m solid wall; 4 pilasters; 3 shelves; 36 chained occult grimoires; central astrolabe relief & runes |
| 11 | `reliquary_astral_orrery_monolith.glb` | `dungeon/` | Focal Prop / Monolith | 2.60m x 2.60m x 3.90m | Bottom-center (0,0,0) | WeatheredAshlarStone, CarvedStoneTrim, TarnishedBrass, WroughtIron, GlowingOccultRune | Stepped plinth; 6 multi-ringed astrolabes; central violet soul-pillar; 4 cradle buttresses; 40 ticks/orbs |
| 12 | `reliquary_chandelier_astrolabe.glb` | `dungeon/` | Focal Prop / Centerpiece | 2.00m Diam x 1.80m H | Ceiling rose Z=0.0 | TarnishedBrass, WroughtIron, GlowingOccultRune | Hanging Z: 0.0 to -1.80m; central spindle; 4 concentric/diagonal rings; 14 violet crystal prisms |
| 13 | `abattoir_wall_furnace_4x4.glb` | `dungeon/` | Modular Architecture | 4.00m W x 0.50m D x 4.00m H | Bottom-center (0,0,0) | WeatheredAshlarStone, WroughtIron, TarnishedBrass, AbyssalCrimson | 0.5m solid wall; 5 iron ribs; 4 glowing crimson furnace chambers; 4 cogwheels/gears; 4 meat-hook chains |
| 14 | `abattoir_blood_press_monolith.glb` | `dungeon/` | Focal Prop / Monolith | 2.50m x 2.50m x 3.80m | Bottom-center (0,0,0) | WeatheredAshlarStone, CarvedStoneTrim, WroughtIron, TarnishedBrass, AbyssalCrimson | Cast-iron base & platen; giant central screw-spindle (16 threads); 4 crimson vats; 4 gargoyle spouts |
| 15 | `abattoir_hanging_hook_rack.glb` | `dungeon/` | Focal Prop / Centerpiece | 1.80m Diam x 1.75m H | Ceiling mount Z=0.0 | WroughtIron, TarnishedBrass, AbyssalCrimson | Hanging Z: 0.0 to -1.75m; circular butcher wheel; central crimson ember cage; 10 hanging meat hooks |

---

## 2. Logic Chain

1. **Rule 7 & 9 Architectural Requirements**:
   - The project mandates strict modular grid architecture for catacombs and dungeons based on a 4m x 4m x 4m standard (Rule 9.3).
   - Solid wall thickness must be at least 0.40m to 0.50m (Rule 9.4) to eliminate light bleeding from external `DirectionalLight3D` sources into dark catacombs and dungeon corridors.
   - Observations on `crypt_wall_ossuary_4x4` (0.54m), `crypt_archway_portcullis_4x4` (0.54m), `crypt_iron_gate_cell_4x4` (0.48m), `necropolis_wall_armory_4x4` (0.50m), `reliquary_wall_grimoire_4x4` (0.50m), and `abattoir_wall_furnace_4x4` (0.50m) confirm they all meet or exceed this requirement.
   - Therefore, the micro-voxel generator must preserve solid core wall backings with depth >= 0.48m across all modular wall units.

2. **Walkway Clearances & Player Navigation**:
   - Player character is a standard Godot CharacterBody3D (capsule height ~1.8m to 2.0m, radius ~0.4m to 0.5m).
   - In `crypt_archway_portcullis_4x4`, the arch opening is 2.52m wide and portcullis spikes end at Z = 2.45m.
   - In `crypt_iron_gate_cell_4x4`, the doorway is 1.48m wide and the gate is swung open 54° so the player walks unobstructed.
   - In `ossuary_buttress_arch_4x4`, the clear opening between piers is 2.52m wide with vault peak at Z = 3.82m.
   - In `ossuary_stone_bridge_4x4`, the walkway deck is 2.20m wide between crenellated curbs.
   - Therefore, voxelizing these structures must retain these exact minimum opening bounds to prevent player collisions from being blocked by stepped voxel corners.

3. **Subterranean Light-Isolation (`crypt_containment_hull.glb`)**:
   - Observation: `crypt_containment_hull.glb` is an inverted shell covering X:[-32m, +32m], Y:[19m, 86m], Z:[-10m, +3.8m] with inward-facing normals and a top stair cutout aligned to the church nave floor (X:[-5.8m, +5.8m], Y:[19m, 27.8m]).
   - Rebuilding this model with high-resolution micro-voxels across 64m would create an astronomical voxel volume (billions of empty queries).
   - Logic: The containment hull is a structural occlusion shell. It should be built from coarse stepped slabs (e.g. 0.20m thickness) with inward face normals using `dark_containment_hull_stone`, preserving its exact bounding box and church nave cutout.

4. **Multi-Tier Voxel Sizing for Visual Detail and Performance**:
   - Viewmodel weapons use `voxel_size = 0.004m` (4mm).
   - Gauntlets and character mannequins use `voxel_size = 0.009m–0.018m` (9mm–18mm).
   - If large 4m x 4m walls used 4mm voxels, each wall would contain 1,000 x 1,000 x 120 = 120 million voxels (memory exhaustion).
   - Using `voxel_size = 0.04m` (4cm) for 4m modular walls produces 100 x 100 x 12 = 120,000 potential voxels, yielding ~8,000–18,000 surface quads after 6-neighbor internal face culling. This gives crisp micro-voxel stepping while loading in milliseconds in Blender and Godot.
   - Medium focal props (monoliths, altars, cauldrons, iron maiden, orrery, blood press) benefit from `voxel_size = 0.025m` (2.5cm) for sculpted details.
   - Small clutter assets (candle clusters, bone piles, crates, chains) benefit from `voxel_size = 0.015m–0.02m` (1.5cm–2.0cm) to render candles, skulls, and chain links with distinct micro-voxel silhouettes.

5. **Disjoint Model Sets & Safe Parallel Execution**:
   - The 21 models of Wave 1B are isolated to `tools/blender_build_voxel_crypt_kit.py` writing to `res://assets/models/church_kit/`.
   - The 15 models of Wave 1C are isolated to `tools/blender_build_voxel_dungeons_biomes.py` writing to `res://assets/models/ossuary_variety/` and `res://assets/models/dungeon/`.
   - Because their output paths and target scripts are 100% disjoint, both Blender Python scripts can run simultaneously in parallel without race conditions or file locking conflicts.


---

## 3. Caveats

1. **Dependency on Palette Extension (R1)**:
   - Wave 1B and Wave 1C implementation scripts (`tools/blender_build_voxel_crypt_kit.py` and `tools/blender_build_voxel_dungeons_biomes.py`) depend on `create_environment_voxel_palette()` being available in `tools/blender_micro_voxel_kit.py` (Requirement R1, scoped to Survey 1 / Palette Implementer).
   - If executed prior to R1 completion, the scripts can fall back to an internal material factory matching the exact `GrimdarkMaterialLibrary` PBR standards documented in Section 1.1.

2. **Godot Prefab Colliders vs In-Place GLB Mesh Replacement**:
   - The architectural prefabs in `scenes/prefabs/architecture/` (e.g. `crypt_wall_ossuary_4x4.tscn`) contain existing `StaticBody3D` nodes with manually placed `BoxShape3D` or `ConcavePolygonShape3D` colliders.
   - Overwriting `.glb` files in-place will update the visual meshes immediately upon headless import; however, if any bounding dimensions deviate by more than ±0.05m, collision shapes in `.tscn` files may need minor alignment passes. The designs in Section 4 strictly preserve original bounding boxes to prevent this.

3. **Ceiling Anchors vs Ground Placement Conventions**:
   - Models hanging from ceilings (`crypt_hanging_cage`, `clutter_ceiling_chains_roots`, `ossuary_bone_chandelier`, `necropolis_hanging_war_brazier`, `reliquary_chandelier_astrolabe`, `abattoir_hanging_hook_rack`) have their origin at the ceiling contact point (Z=0.0 in Blender, hanging down along -Z).
   - In contrast, ground-based props and walls have their origin at (X=0, Y=0, Z=0) at bottom-center. This origin difference must be rigorously maintained so instanced prefabs do not invert or spawn below floors.

4. **Headless Godot Execution Serialization**:
   - Multiple agents must NEVER run `godot --headless` simultaneously to avoid corrupting `uid_cache.bin` or `.godot/imported/` caches. All Blender exports must finish before the headless Godot import pass is initiated.

---

## 4. Conclusion & Detailed Script Specifications

### 4.1 Script Design Specification: `tools/blender_build_voxel_crypt_kit.py` (Wave 1B)

#### Purpose & Scope
Rebuilds all 21 models in `res://assets/models/church_kit/` in the Hyper-Detailed Ultra-Realistic Micro-Voxel art style:
- 8 Modular Crypt Kit pieces
- 9 Crypt Focal Props
- 4 Clutter Assets

#### Architecture & Class Structure
```python
"""
tools/blender_build_voxel_crypt_kit.py
Builds 21 Hyper-Detailed Ultra-Realistic Micro-Voxel Crypt, Catacomb & Clutter Assets.
"""
import math
import os
import sys
import bpy
import bmesh
from mathutils import Vector, Euler

# Import micro-voxel kit and environment palette
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blender_micro_voxel_kit import (
    create_environment_voxel_palette,
    # or fallback environment palette generator
)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_DIR = os.path.join(PROJECT_ROOT, "assets", "models", "church_kit")

class EnvironmentVoxelBuilder:
    """
    Parametric Micro-Voxel Builder with world-coordinate grid mapping,
    manifold face culling, 26-neighbor Ambient Occlusion, and directional shading.
    Coordinate mapping (Blender Z-up, export_yup=True):
      - wx = ox + ix * voxel_size (+X)
      - wy = oy + iy * voxel_size (+Y in Blender -> -Z in Godot)
      - wz = oz + iz * voxel_size (+Z in Blender -> +Y in Godot)
    """
    def __init__(self, name: str, voxel_size: float = 0.04, origin: tuple[float, float, float] = (0.0, 0.0, 0.0), palette=None):
        self.name = name
        self.voxel_size = voxel_size
        self.origin = origin
        self.palette = palette or {}
        self.voxels = {}  # (ix, iy, iz) -> (mat_key, shade_bias, tint_b)

    # Core voxel ops: set_voxel, set_world, fill_world_box, carve_world_box,
    # fill_world_cylinder_z, fill_world_cylinder_y, fill_world_cylinder_x,
    # carve_pointed_arch_y, add_3d_chain, add_candle, add_skull,
    # and build_mesh_object(parent_obj=None)
```

#### Voxel Resolution Strategy
- **4m Modular Architecture Pieces (`voxel_size = 0.04m`)**:
  - `build_voxel_crypt_corridor_vault_4x4()`: 4.2m x 4.2m x 0.5m vault deck; coffered ceiling recesses; transverse/longitudinal ribs; stepped corbels; central keystone boss with bronze ring.
  - `build_voxel_crypt_wall_ossuary_4x4()`: 4.2m x 0.54m x 4.05m wall; base plinths and cornices; 2 tiers of pointed-arch burial niches carved via boolean/voxel difference; layered femur bundles and geometric skull clusters in AgedBone; retaining iron bars.
  - `build_voxel_crypt_archway_portcullis_4x4()`: 4.2m x 0.54m x 4.05m wall; wide pointed archway (width 2.52m, peak Z=3.60m); partially raised portcullis with bottom spikes at Z=2.48m; winch chains and brackets.
  - `build_voxel_crypt_pillar()`: Base 0.96m x 0.96m, height 4.0m; core shaft with 4 engaged colonnettes; 12 stacked drum courses; 3 iron bands with rivets at Z=1.15m, 2.00m, 2.85m; foliated capital.
  - `build_voxel_crypt_containment_hull()`: Inverted occlusion shell (X in [-32, 32], Y in [19, 86], Z in [-10, 3.8]); 0.20m slab voxel step; inward face normals; top nave opening (X:[-5.8, 5.8], Y:[19, 27.8]); `dark_containment_hull_stone`.
  - `build_voxel_crypt_iron_gate_cell_4x4()`: 4.2m x 0.50m x 4.05m wall; central doorway (width 1.48m, height 2.95m); swung-open iron gate (rotated 54°); barred left/right window openings above dwarf walls.
  - `build_voxel_crypt_drowned_cistern_4x4()`: 4.0m x 4.0m floor slab; recessed octagonal basin (r=1.32m, depth 0.26m); submerged steps; dark cistern water disk at Z=-0.12m; wrought-iron drainage grates at Z=-0.02m.
  - `build_voxel_crypt_rotting_bookshelf_4x4()`: 3.86m x 0.68m x 3.75m shelving; 4 timber stiles; 5 shelves; trefoil header; tilted grimoires with glowing runes; skulls and scroll rolls.

- **Focal Props (`voxel_size = 0.025m`)**:
  - `build_voxel_crypt_altar()`: 2-tier dais (2.8m, 2.4m); altar block with sacrificial basin; front/top blood rune strips; 4 corner lit candles with dripping wax.
  - `build_voxel_crypt_sarcophagus_ornate()`: 2-tier plinth (1.56m x 2.68m); hollow tomb body; blind arch recesses; rune bed with skull and ribs; sculpted lid cracked open 8°.
  - `build_voxel_crypt_lectern_grimoire()`: Octagonal stone plinth with iron claw feet; fluted shaft; reading cradle with spread wings; open leather grimoire with glowing occult sigils.
  - `build_voxel_crypt_hanging_cage()`: Origin at Z=3.88m (ceiling plate); 11 chain links; cage hoops (r=0.38m); prisoner skeleton inside; bottom drop spike.
  - `build_voxel_crypt_plague_cauldron()`: Stone furnace ring; 2.2m cast-iron cauldron; boiling SicklyGreenBile with 9 bubbles; 3 distillation pipes with flanges and collector dome.
  - `build_voxel_crypt_weeping_statue_pedestal()`: Stepped cenotaph base; 3.6m hooded robed figure; offering basin; streaming pale-blue FrozenBlueSoul tear streaks.
  - `build_voxel_crypt_sunken_bell_crater()`: Shattered rubble crater (r=2.15m); 2.6m tarnished-bronze bell tilted 25°; jagged crack with glowing crimson core; broken timber yoke.
  - `build_voxel_crypt_ritual_obelisk()`: 3-step plinth (1.9m); tapered octagonal shaft; 4 cardinal rune channels with AbyssalCrimson glow; 4 corner candle dishes with bone candles.
  - `build_voxel_standing_iron_brazier()`: Tripod legs (base r=0.42m); iron collar ring; fire basket bowl; glowing amber embers mound.

- **Clutter Assets (`voxel_size = 0.015m`)**:
  - `build_voxel_clutter_ceiling_chains_roots()`: Origin at Z=0.0; 5 ceiling plates; interlocking chain links descending to -2.10m with meat hooks; 10 gnarled tree roots.
  - `build_voxel_clutter_melted_candle_cluster()`: Iron/bronze tray; 24 wax pool lobes; 14 varied candles with drip rivulets and glowing flames.
  - `build_voxel_clutter_rubble_bones_pile()`: 48 fallen masonry blocks; 3 pillar drums; 8 skulls; 20 femur/tibia bones; 18 chain links.
  - `build_voxel_clutter_wooden_crates_barrels()`: 2 staved barrels with 4 iron hoops; 2 slatted crates with iron corner brackets and rivets.

---

### 4.2 Script Design Specification: `tools/blender_build_voxel_dungeons_biomes.py` (Wave 1C)

#### Purpose & Scope
Rebuilds all 15 models across Biomes 2–4 in the Hyper-Detailed Ultra-Realistic Micro-Voxel art style:
- 6 Ossuary Variety pieces in `res://assets/models/ossuary_variety/`
- 9 Dungeon Kit pieces in `res://assets/models/dungeon/`

#### Target Model Sets & Output Directories
```python
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OSSUARY_DIR = os.path.join(PROJECT_ROOT, "assets", "models", "ossuary_variety")
DUNGEON_DIR = os.path.join(PROJECT_ROOT, "assets", "models", "dungeon")
```

#### Model Specifications & Resolutions
- **Ossuary Variety Pieces (`voxel_size = 0.03m–0.04m`)**:
  1. `build_voxel_ossuary_stone_bridge_4x4()`: 2.2m W x 4.0m L deck; walkway at Z=0.0; 32 flagstone cobbles; twin underslung ribbed arches; 6 skull bollards and chain side-rails.
  2. `build_voxel_ossuary_balcony_railing_4m()`: 4.04m W x 0.36m D x 1.35m H; 3 newel posts with iron spikes and skulls; 12 balusters with lancet arch links; 18 iron pickets; 4 candles.
  3. `build_voxel_ossuary_buttress_arch_4x4()`: 4.04m W x 0.96m D x 4.05m H; central walk-through opening 2.52m wide; 5 tiered skull niches per pier; keystone horned skull; hanging chains.
  4. `build_voxel_ossuary_bone_chandelier()`: Ceiling mount Z=2.40m; 2-tier wheel (r=1.25m, 0.72m); 24 skull candle stations with glowing flames; suspension chains; drop finial.
  5. `build_voxel_ossuary_spine_reliquary_monolith()`: 1.65m x 1.65m x 3.42m; 18 fused vertebrae column; blazing crimson-amber soul core; 3 orbiting brass astrolabe rings; 4 horned skulls.
  6. `build_voxel_ossuary_burial_niche_divider_4x4()`: 3.28m W x 0.62m D x 2.95m H; central barred window; 8 burial niche bays with 16 skull clusters; 6 candles.

- **Biome 2: The Iron Necropolis (`voxel_size = 0.03m–0.04m`)**:
  7. `build_voxel_necropolis_wall_armory_4x4()`: 4.0m x 0.5m x 4.0m solid wall; 3 armored pilasters with brass rivets; 2 alcoves with portcullis bars and amber forge slits; crossed halberds and tower shields.
  8. `build_voxel_necropolis_iron_maiden_monolith()`: 2.4m x 2.4m x 3.8m; octagonal war-plinth; iron maiden torso and helm with glowing visor slits; 4 greatswords; 4 forge braziers; 4 chains.
  9. `build_voxel_necropolis_hanging_war_brazier()`: Origin at Z=0.0; hanging down to -1.75m; war-cage ring; coal basket with glowing embers; 4 chains; 12 perimeter war-spikes and flame pods.

- **Biome 3: The Astral Reliquary (`voxel_size = 0.03m–0.04m`)**:
  10. `build_voxel_reliquary_wall_grimoire_4x4()`: 4.0m x 0.5m x 4.0m solid wall; 4 pilasters; 3 shelves; 36 chained occult tomes; central astrolabe relief with violet rune inlays; 12 scroll rolls.
  11. `build_voxel_reliquary_astral_orrery_monolith()`: 2.6m x 2.6m x 3.9m; stepped plinth; 6 concentric and tilted brass astrolabe rings; central violet soul-pillar; 4 cradle buttresses; 40 degree ticks and planetary orbs.
  12. `build_voxel_reliquary_chandelier_astrolabe()`: Origin at Z=0.0; hanging down to -1.80m; central spindle; 4 concentric/diagonal brass rings; central violet crystal pendulum; 14 crystal prisms.

- **Biome 4: The Blood-Forged Abattoir (`voxel_size = 0.03m–0.04m`)**:
  13. `build_voxel_abattoir_wall_furnace_4x4()`: 4.0m x 0.5m x 4.0m solid wall; 5 iron ribs; 4 glowing crimson furnace chambers with grate bars; 4 cogwheels in upper frieze; 4 meat-hook chains.
  14. `build_voxel_abattoir_blood_press_monolith()`: 2.5m x 2.5m x 3.8m; heavy iron blood trough; central screw-spindle with 16 helical threads and turn-wheel; 4 crimson collection vats; 4 gargoyle spouts.
  15. `build_voxel_abattoir_hanging_hook_rack()`: Origin at Z=0.0; hanging down to -1.75m; circular butcher wheel; central crimson ember cage; 10 hanging meat hooks with drop rods and brass points.

---

## 5. Verification Method

To independently verify the architecture, geometry, and future model builds:

1. **Blender Export Verification**:
   Execute the two procedural voxel builders in headless mode using the local Blender 5.4.0 binary:
   ```powershell
   & "C:\Users\olema\Downloads\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender.exe" --background --python tools/blender_build_voxel_crypt_kit.py

   & "C:\Users\olema\Downloads\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender.exe" --background --python tools/blender_build_voxel_dungeons_biomes.py
   ```
   - Success condition: Both scripts exit with code 0 and log `[SUCCESS] Exported ...` across all 36 models.

2. **File Existence & Non-Zero File Size Verification**:
   ```powershell
   # Wave 1B (21 models):
   $churchKitModels = @(
       "crypt_corridor_vault_4x4.glb", "crypt_wall_ossuary_4x4.glb", "crypt_archway_portcullis_4x4.glb",
       "crypt_pillar.glb", "crypt_containment_hull.glb", "crypt_iron_gate_cell_4x4.glb",
       "crypt_drowned_cistern_4x4.glb", "crypt_rotting_bookshelf_4x4.glb", "crypt_altar.glb",
       "crypt_sarcophagus_ornate.glb", "crypt_lectern_grimoire.glb", "crypt_hanging_cage.glb",
       "crypt_plague_cauldron.glb", "crypt_weeping_statue_pedestal.glb", "crypt_sunken_bell_crater.glb",
       "crypt_ritual_obelisk.glb", "standing_iron_brazier.glb", "clutter_ceiling_chains_roots.glb",
       "clutter_melted_candle_cluster.glb", "clutter_rubble_bones_pile.glb", "clutter_wooden_crates_barrels.glb"
   )
   foreach ($m in $churchKitModels) {
       $p = "assets\models\church_kit\$m"
       if (!(Test-Path $p) -or (Get-Item $p).Length -lt 1000) { Write-Error "Missing or empty: $p" }
   }

   # Wave 1C (15 models):
   $ossuaryModels = @(
       "ossuary_balcony_railing_4m.glb", "ossuary_bone_chandelier.glb", "ossuary_burial_niche_divider_4x4.glb",
       "ossuary_buttress_arch_4x4.glb", "ossuary_spine_reliquary_monolith.glb", "ossuary_stone_bridge_4x4.glb"
   )
   foreach ($m in $ossuaryModels) {
       $p = "assets\models\ossuary_variety\$m"
       if (!(Test-Path $p) -or (Get-Item $p).Length -lt 1000) { Write-Error "Missing or empty: $p" }
   }

   $dungeonModels = @(
       "abattoir_blood_press_monolith.glb", "abattoir_hanging_hook_rack.glb", "abattoir_wall_furnace_4x4.glb",
       "necropolis_hanging_war_brazier.glb", "necropolis_iron_maiden_monolith.glb", "necropolis_wall_armory_4x4.glb",
       "reliquary_astral_orrery_monolith.glb", "reliquary_chandelier_astrolabe.glb", "reliquary_wall_grimoire_4x4.glb"
   )
   foreach ($m in $dungeonModels) {
       $p = "assets\models\dungeon\$m"
       if (!(Test-Path $p) -or (Get-Item $p).Length -lt 1000) { Write-Error "Missing or empty: $p" }
   }
   ```

3. **Headless Godot Import Pass Verification**:
   ```powershell
   & "C:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --quit-after 240 --path . --import
   ```
   - Success condition: Exits cleanly with code 0 and updates `.godot/imported/` without parse errors.

4. **Invalidation Conditions**:
   - Any model bounding box deviating from the 4.0m x 4.0m grid unit.
   - Any modular wall unit with solid wall thickness < 0.40m (violates Rule 9.4 light isolation).
   - Any doorway or archway opening clearance < 2.2m height (blocks player character movement).
   - Inward-pointing normal failure on `crypt_containment_hull.glb` (causes exterior light leaking into catacombs).
   - Missing or misaligned origins on ceiling fixtures vs ground props.
