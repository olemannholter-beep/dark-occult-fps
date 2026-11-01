# Milestone 5 Empirical Challenger Report: Stairwells & HUD Compass Banner

**Author:** Empirical Challenger 1 (`teamwork_challenger_r2_1`)  
**Target Recipient:** Orchestrator (`7caaf02e-4314-4901-b634-7676eb41a540`)  
**Scope:** Milestone 5 (Empirical Verification of Feature 2: Stairwells across Church, Crypt, Catacombs, Procedural Dungeons & Feature 3: Compass Banner)  
**Verdict:** **APPROVE**

---

## 1. Observation

All tests were written and executed directly via the official Godot 4.7.2 headless console executable:  
`c:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe --headless --path . -s res://tools/test_milestone5_empirical.gd`

### 1.1 Scene Hierarchy Audit (`scenes/levels/town_overworld.tscn`)
Execution of node search queries across `town_overworld.tscn`:
- `StairwellWallSouth`: **ABSENT** (`find_child` returned `null`)
- `StairwellNorthBulkheadWall`: **ABSENT** (`find_child` returned `null`)
- `AutoSealFloor_0_0_-5`: **ABSENT** (`find_child` returned `null`)
- `StairwellCollarCeilNorth`: **ABSENT** (`find_child` returned `null`)
- `Ch7WallSouthHighStairBulkhead`: **ABSENT** (`find_child` returned `null`)
- `Ch8WallSouthHighCenter`: **ABSENT** (`find_child` returned `null`)
- `StairsStone4x4`: Present at global pos `(0.0, 4.0, -50.0)`
- `StairsCh1ToCh6`: Present at global pos `(0.0, 0.0, -64.0)`
- `StairsCh4ToCh5`: Present at global pos `(24.0, 0.0, -64.0)`
- `StairsCh6ToCh7`: Present at global pos `(-12.0, -4.0, -88.0)`
- `StairsCh6ToCh8`: Present at global pos `(0.0, -4.0, -84.0)`
- `Ch5PortcullisSouthStairs`: Instance of `res://scenes/prefabs/architecture/wall_stone_arch_door.tscn`
- `Ch6PortcullisSouth`: Instance of `res://scenes/prefabs/architecture/wall_stone_arch_door.tscn`
- `Ch7PortcullisSouthStairs`: Instance of `res://scenes/prefabs/architecture/wall_stone_arch_door.tscn`
- `Ch8PortcullisSouthEntrance`: Instance of `res://scenes/prefabs/architecture/wall_stone_arch_door.tscn`

### 1.2 Physical CharacterBody3D Descent and Ascent (`StairsStone4x4`)
Physical simulation trace of player walking North (`-Z`) down `StairsStone4x4` from Church Nave into Crypt Chamber 1, then walking South (`+Z`) back up:
```
  [StairDescent] step=10 pos=(0.00, 4.15, -44.60) on_floor=false vel_y=-1.63
  [StairDescent] step=20 pos=(0.00, 4.02, -44.91) on_floor=true vel_y=0.00
  [StairDescent] step=30 pos=(0.00, 4.02, -45.53) on_floor=true vel_y=0.00
  [StairDescent] step=40 pos=(0.00, 4.02, -46.48) on_floor=true vel_y=0.00
  [StairDescent] step=50 pos=(0.00, 4.05, -47.61) on_floor=true vel_y=0.00
  [StairDescent] step=60 pos=(0.00, 3.65, -48.67) on_floor=true vel_y=0.00
  [StairDescent] step=70 pos=(0.00, 2.88, -49.48) on_floor=true vel_y=0.00
  [StairDescent] step=80 pos=(0.00, 2.10, -50.30) on_floor=true vel_y=0.00
  [StairDescent] step=90 pos=(0.00, 1.33, -51.11) on_floor=true vel_y=0.00
  [StairDescent] step=100 pos=(0.00, 0.56, -51.93) on_floor=true vel_y=0.00
  [StairDescent] step=110 pos=(0.00, 0.02, -52.83) on_floor=true vel_y=0.00
  [StairDescent] step=120 pos=(0.00, 0.04, -53.96) on_floor=true vel_y=0.00
  [PASS] Player successfully descended Church-to-Crypt stairs! Final pos=(0.00, 0.04, -54.07), on_floor=true
  [PASS] Player Y descended to Crypt level (Y=0.04 <= 1.0)!

  [StairAscent] step=80 pos=(0.00, 0.04, -52.54) on_floor=true
  [StairAscent] step=90 pos=(0.00, 0.75, -51.72) on_floor=true
  [StairAscent] step=100 pos=(0.00, 1.50, -50.93) on_floor=true
  [StairAscent] step=110 pos=(0.00, 2.25, -50.14) on_floor=true
  [StairAscent] step=120 pos=(0.00, 3.00, -49.34) on_floor=true
  [StairAscent] step=130 pos=(0.00, 3.75, -48.55) on_floor=true
  [StairAscent] step=140 pos=(0.00, 3.94, -48.35) on_floor=true
  [StairAscent] step=150 pos=(0.00, 4.06, -47.95) on_floor=true
  [StairAscent] step=160 pos=(0.00, 4.03, -47.17) on_floor=true
  [StairAscent] step=170 pos=(0.00, 4.09, -46.10) on_floor=true
  [StairAscent] step=180 pos=(0.00, 4.04, -44.97) on_floor=true
  [PASS] Player smoothly ascended stairs back into Church Nave! Final pos=(0.00, 4.04, -44.97)
```

### 1.3 Catacomb Headroom & Clearance Raycast Probes
Vertical raycast probes sampled across 5 stations along each stairwell incline:
- `StairsCh1ToCh6`: Minimum vertical headroom clearance: **3.80m** (`[PASS]`)
- `StairsCh4ToCh5`: Minimum vertical headroom clearance: **3.80m** (`[PASS]`)
- `StairsCh6ToCh7`: Minimum vertical headroom clearance: **3.80m** (`[PASS]`)
- `StairsCh6ToCh8`: Minimum vertical headroom clearance: **3.80m** (`[PASS]`)

### 1.4 Procedural Dungeon Generator Assertions Across 8 Biomes & Multiple Seeds
Stress test generating dungeons for Biomes 1 through 8 across seeds 42, 101, 777:
- Evaluated **139** procedural staircases (`ProcStairs_*`).
- Checked all floor instances (`ProcFloor_*`, `SealerSubFloor_*`, `ColFloor_*`):
  - In stair lower cells (`st_cell`): **0** floor slabs instantiated.
  - In stair upper headroom cells (`st_cell + Vector3i(0, 1, 0)`): **0** floor slabs instantiated.
- Checked boundary protection (`_is_stair_passage_boundary`):
  - Bottom entry and top landing faces: **100% protected** against solid walls (`ProcWall*`, `SealerWall*`, `ColWall*`).
- **Incidental Finding (Defect in `_populate_ossuary_v2_room`)**:
  Lines 2331 and 2379 of `scripts/world/procedural_dungeon_generator.gd` throw:
  `SCRIPT ERROR: Invalid assignment of property or key 'reward_scale' with value of type 'float' on a base object of type 'StaticBody3D (ReliquaryChest)'`.
  `ReliquaryChest` defines `@export var depth_scale: float`, not `reward_scale`. (This does not affect stairwell generation, which finishes earlier in `_seal_voxel_cells`).

### 1.5 Gothic HUD Overhaul Top Biome Plaque Text Measurement
Testing font measurement at font size 13 with `maxf(780.0, text_w + 48.0)`:
- 79-char string `"── ❖ SUBTERRANEAN CATACOMB SANCTUMS : EIGHT PORTAL CHAMBERS (SAFE HARBOUR) ❖ ──"`:
  - Text pixel width: `596.00px`
  - Plaque width: `780.00px`
  - Total horizontal padding: `184.00px` (`92.00px` each side)
  - `[PASS]` Text fits with full clearance; zero truncation.
- 58-char string `"── ❖ SANCTUARY OF THE ASHEN CHAPEL : SAFE HARBOUR HUB ❖ ──"`:
  - Text pixel width: `424.00px`, Plaque width: `780.00px`, Padding: `356.00px`. `[PASS]`
- 55-char string `"── ❖ THE ENDLESS OSSUARY : DEPTH TIER 5 EXPEDITION ❖ ──"`:
  - Text pixel width: `381.00px`, Plaque width: `780.00px`, Padding: `399.00px`. `[PASS]`

---

## 2. Logic Chain

1. **Adversarial Discovery on Prior Test `test_stairwell_walk.gd`:**  
   Prior test `test_stairwell_walk.gd` spawned the player at `Z = -16.0` and walked to `Z = -27.5`, remaining at `Y = 4.04` the entire time. Because `GothicChurch` is at `(0, 4, 0)` and `StairsStone4x4` is placed at `(0, 0, -50)`, the actual staircase is located at World `Z = -48.0 .. -52.0` (descending from `Y = 4.0` down to `Y = 0.0`). The prior test was walking on the flat church nave floor 20 meters away from the stairs without touching them.

2. **Empirical Verification of Real Coordinates:**  
   When correctly positioned at `Z = -44.5` (in front of `ChurchFloor_StairEntrySouth` at `Z = -46.0`), the player walks North and smoothly descends from `Y = 4.15` down to `Y = 0.04` at `Z = -54.07`, maintaining `on_floor = true` with zero blocking collisions. Reversing direction walks South back up the steps to `Y = 4.04` at `Z = -44.97`. This definitively confirms the Church Nave stairwell is open, unobstructed, and physically traversable in both directions.

3. **Absence of Blocking Geometry:**  
   Direct inspection confirms `StairwellWallSouth` and `StairwellNorthBulkheadWall` are completely deleted. In their place, high-vaulted corridors (`StairwellUpperVault` at `Y = 8.0`) and open passages connect Church to Crypt. Furthermore, all 4 Catacomb stairwells use `wall_stone_arch_door.tscn` (open archway) with a lintel height of `3.725m`, yielding `3.80m` vertical clearance along the stairs.

4. **Procedural Dungeon Robustness:**  
   In `procedural_dungeon_generator.gd`, line 918 explicitly guards against placing floors when `stair_cells.has(cell)` or `stair_cells.has(below_cell)`. Across 139 generated staircases in 8 biomes, zero floor slabs were spawned over stairs or in the headroom cell above stairs.

5. **Compass Banner Dynamic Sizing:**  
   The 79-character Subterranean Catacomb Sanctums banner string measures `596.00px` wide. Because `plaque_w = maxf(780.0, text_w + 48.0)` clamps to a minimum of `780.0px`, the banner provides `184.00px` of horizontal margin. Centered drawing via `(vp.x - plaque_w) * 0.5` ensures the banner and text remain perfectly centered across all resolutions without text truncation.

---

## 3. Caveats

1. **Incidental Bug Discovered in Procedural Dungeon Generator:**  
   During testing across 8 biomes, lines 2331 and 2379 in `scripts/world/procedural_dungeon_generator.gd` threw runtime script errors: `rc.reward_scale = reward_sc`. In `ReliquaryChest`, the exported variable is `depth_scale`, not `reward_scale`. As an empirical reviewer, per instruction, I did not modify implementation code, but flag this for Worker M3 / M6 / Auditor to update `rc.depth_scale = reward_sc`.
2. **AI / NPC NavMesh:**  
   This evaluation verified player physics collision (`CharacterBody3D`) and vertical raycasts. Dynamic enemy navigation meshes (`NavigationRegion3D` rebaking) across the stairs were not part of this milestone scope.

---

## 4. Conclusion

All empirical requirements of Milestone 5 are fully satisfied:
- Church Nave stairwell is 100% open and bidirectional physical traversal is verified.
- Blocking nodes `StairwellWallSouth`, `StairwellNorthBulkheadWall`, `AutoSealFloor_0_0_-5`, and bulkheads are absent.
- All 4 Catacomb stairwells feature open archways with >= 3.8m vertical headroom.
- Procedural dungeon staircases have zero illegal floor slabs or blocking bulkheads.
- Top compass plaque dynamically scales with 184px margin for 80-char strings.

**Verdict: APPROVE**

---

## 5. Verification Method

To independently reproduce all empirical results:
```powershell
& "c:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --path . -s res://tools/test_milestone5_empirical.gd
```
**Expected Output:** Exits with code 0, reporting `TOTAL PASSED: 25`, `TOTAL FAILED: 0`, and `[FINAL VERDICT: APPROVE]`.

---

## Challenge Summary

**Overall risk assessment**: LOW

## Challenges

### [Medium] Prior Stairwell Walk Test Tested Wrong Coordinates
- **Assumption challenged**: Prior worker logs claimed `test_stairwell_walk.gd` passed stairwell traversal.
- **Attack scenario**: Inspected coordinates: the prior test spawned at `Z = -16.0` and walked to `Z = -27.5` (flat nave floor), while the stairs are at `Z = -48.0 .. -52.0`.
- **Mitigation**: Wrote and executed `tools/test_milestone5_empirical.gd` spawning at `Z = -44.5` and walking through `Z = -48.0 .. -54.0`. Player smoothly descended from `Y = 4.15` to `Y = 0.04`, then ascended back up to `Y = 4.04`.

### [Low] Incidental ReliquaryChest Property Mismatch in `procedural_dungeon_generator.gd`
- **Assumption challenged**: Full procedural generation runs without script errors.
- **Attack scenario**: Lines 2331 and 2379 attempt to assign `rc.reward_scale = reward_sc`, but `ReliquaryChest` exports `depth_scale`.
- **Mitigation**: Documented in Caveats for resolution; does not impede stairwell floor exclusion.

## Stress Test Results

| Test Scenario | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Forbidden Nodes Audit | All 6 blocking nodes absent | All 6 absent | PASS |
| Required Stairs Audit | All 5 stair prefabs present | All 5 present with correct global transforms | PASS |
| Archway Prefabs Audit | All 4 Catacomb stair entries use archway | All 4 use `wall_stone_arch_door.tscn` | PASS |
| Church-to-Crypt Descent | Player Y drops 4.0m -> 0.0m | Y drops from 4.15 to 0.04 at Z=-54.07, on_floor=true | PASS |
| Crypt-to-Church Ascent | Player Y rises 0.0m -> 4.0m | Y rises from 0.04 to 4.04 at Z=-44.97, on_floor=true | PASS |
| Catacomb Headroom Probes | Vertical clearance >= 2.6m | All 4 stairwells have 3.80m vertical clearance | PASS |
| Procedural Dungeon Floors | 0 floor slabs on stair cells | 0 floor slabs across 139 staircases in 8 biomes | PASS |
| Procedural Wall Boundaries | Stair entry/exit faces open | 100% boundary faces protected | PASS |
| HUD Compass Banner Sizing | 80-char string fits without truncation | 596px text in 780px plaque (+184px padding) | PASS |
