# Review & Adversarial Challenge Report — Milestone 5 (Reviewer 2)

**Author:** Reviewer 2 (`teamwork_reviewer_r2_2`)  
**Target Recipient:** Orchestrator (`7caaf02e-4314-4901-b634-7676eb41a540`)  
**Date:** 2026-11-01T16:15:00Z  
**Verdict:** **REQUEST_CHANGES**

---

## Review Summary

**Verdict**: **REQUEST_CHANGES**

An exhaustive independent adversarial review and verification across all Milestone 1–4 work products and 9 modified files was conducted. While Milestones 1, 2, and 4 exhibit high quality, strict typing, and verified physics unblocking, Milestone 3 introduces a **Critical Runtime Soft-Lock** during portal transitions, and an unresolved runtime exception persists in `scripts/world/procedural_dungeon_generator.gd`.

---

## 1. Observation

1. **Static Typing & CLI Compilation (`AGENTS.md` Rule 5)**:
   Executed `godot --headless --path . --check-only -s <script>` on all 7 GDScript files:
   - `res://scripts/player/first_person_body_controller.gd`: Exit code 0
   - `res://scripts/ui/gothic_hud_overhaul.gd`: Exit code 0
   - `res://scripts/world/procedural_dungeon_generator.gd`: Exit code 0
   - `res://tools/build_prefabs_and_level.gd`: Exit code 0
   - `res://scripts/interaction/occult_portal.gd`: Exit code 0
   - `res://scripts/player/fps_viewmodel_controller.gd`: Exit code 0
   - `res://scripts/items/loot_drop_pickup.gd`: Exit code 0

2. **First-Person Camera Clipping (`scripts/player/first_person_body_controller.gd`)**:
   - `_spawn_box` explicitly assigns `mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY`.
   - `_configure_fp_armor_meshes_recursive(n: Node)` assigns `(n as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY`.
   - `_apply_first_person_shadow_only(root_node: Node)` is called recursively at the end of `_ready()` and `refresh_armor_appearance()`.

3. **Top Compass Text Truncation (`scripts/ui/gothic_hud_overhaul.gd`)**:
   - Lines 506–510 measure string width via `font.get_string_size(full_header, HORIZONTAL_ALIGNMENT_CENTER, -1, 13).x` and dynamically compute `plaque_w = maxf(780.0, text_w + 48.0)`.

4. **Stairwell Physics & Headroom (`tools/build_prefabs_and_level.gd`, `town_overworld.tscn`)**:
   - Executed `tools/test_stairwell_walk.gd`: Player smoothly walked up valley road, descended Church-to-Crypt stairs to `(0.00, 4.04, -27.53)`, and ascended back up to `(0.00, 4.04, -17.91)`. All physics tests passed (exit code 0).
   - Executed `tools/verify_4_menus_stairs_and_lag.gd`: Verified stair ascent to `Y = +4.04m` without jumping and descent with 100% floor contact ratio. All 5 assertions passed (exit code 0).

5. **Weapon Recoil & Micro-Voxel Assets (`fps_viewmodel_controller.gd`, Blender Python scripts, `loot_drop_pickup.gd`)**:
   - `trigger_shoot_recoil(intensity)` applies `+0.055 * intensity` in Z, `+deg_to_rad(5.5 * intensity)` pitch, and tweens back in 0.14s (`TRANS_CUBIC`, `EASE_OUT`).
   - `tools/blender_build_voxel_enemies.py` remeshes primitives via `REMESH` mode `'BLOCKS'` with dynamic octree depth prior to joining, preserving materials and limbs.
   - `tools/blender_build_voxel_town_and_loot.py` uses deterministic BMesh face/vertex deletion for the stairwell cutout and concentric stepped boxes for the elixir.
   - `scripts/items/loot_drop_pickup.gd` builds a stepped micro-voxel box cluster via `SurfaceTool`, verified AABB height 0.45m (<= 0.90m).

6. **Adversarial Stress-Test Failure (`tools/verify_all_8_biome_portals.gd`)**:
   Executed `& godot --headless --path . -s res://tools/verify_all_8_biome_portals.gd`.
   Observed two failures:
   - **Failure A**:
     ```
     SCRIPT ERROR: Cannot call method 'is_inside_tree' on a previously freed instance.
        at: trigger_portal_warp (res://scripts/interaction/occult_portal.gd:304)
     ```
   - **Failure B**:
     ```
     SCRIPT ERROR: Invalid assignment of property or key 'reward_scale' with value of type 'float' on a base object of type 'StaticBody3D (ReliquaryChest)'.
        at: ProceduralDungeonGenerator._populate_ossuary_v2_room (res://scripts/world/procedural_dungeon_generator.gd:2331, 2379)
     ```

---

## 2. Logic Chain

1. **Soft-Lock in `scripts/interaction/occult_portal.gd`**:
   - In `OccultPortal.trigger_portal_warp(player: Node3D)`, the script instantiates a full-screen `CanvasLayer` (`layer = 120`, `mouse_filter = MOUSE_FILTER_STOP`) as a child of `get_tree().root`.
   - When warp is triggered from a portal inside a procedural dungeon (e.g., `DeeperBiomeRiftPortal` or `SanctuaryReturnPortal`), calling `gen.call("generate_biome_dungeon", ...)` synchronously frees the existing dungeon container and all its children, including `self` (the portal instance).
   - Once generation finishes, execution resumes at line 301 in `occult_portal.gd`. Because `self` is already freed:
     - Accessing `_is_generating_rift = false` executes on a deleted instance.
     - Line 304 `if is_inside_tree() and root_ctrl != null:` throws a runtime script error: `Cannot call method 'is_inside_tree' on a previously freed instance`.
     - Line 305 `var tw: Tween = create_tween()` binds the tween to `self`, which is invalid/dead.
     - As a direct consequence, `overlay_layer` is **never faded out and never freed**. It remains permanently attached to `get_tree().root`, completely obscuring the screen with dark slate (`Color(0.03, 0.03, 0.04, 0.96)`) and blocking all mouse input. The player is permanently soft-locked.
   - Mitigation: `overlay_layer` must manage its own lifecycle independently of `self` (e.g. creating the tween on `overlay_layer` itself via `overlay_layer.create_tween()`), and any access to `self` after dungeon generation must be guarded by `if is_instance_valid(self):`.

2. **Property Name Mismatch on `ReliquaryChest`**:
   - In `scripts/world/procedural_dungeon_generator.gd` (lines 1368, 2331, 2379), procedural room generation assigns `rc.reward_scale = reward_sc` and `b_rc.reward_scale = ...`.
   - In `scripts/interaction/reliquary_chest.gd` (line 7), the exported property is declared as `@export var depth_scale: float = 1.0`. The identifier `reward_scale` does not exist on `ReliquaryChest`.
   - Because GDScript is dynamically dispatched on `call` / property assignment on `ReliquaryChest`, assigning `reward_scale` aborts room population with `Invalid assignment of property or key 'reward_scale'`.
   - This prevents proper room population (chests, enemies, and props fail to complete), triggering assertions in `verify_all_8_biome_portals.gd`.
   - Mitigation: Either add `var reward_scale: float: get: return depth_scale, set(v): depth_scale = v` to `ReliquaryChest`, or change the assignment in `procedural_dungeon_generator.gd` to `depth_scale`.

---

## 3. Findings

### [Critical] Finding 1: Soft-Lock on Dungeon Portal Warp (Orphaned Overlay & Crash on Freed Portal)

- **What**: `OccultPortal.trigger_portal_warp()` crashes with `Cannot call method 'is_inside_tree' on a previously freed instance` and permanently leaves the full-screen dark loading overlay on screen.
- **Where**: `scripts/interaction/occult_portal.gd:301–315`
- **Why**: When warping from a portal situated within the procedural dungeon (such as `DeeperBiomeRiftPortal` or `SanctuaryReturnPortal`), generating the next dungeon frees the old dungeon hierarchy containing `self`. Calling `self.is_inside_tree()`, modifying `_is_generating_rift`, or calling `create_tween()` on `self` fails. The overlay at `layer = 120` with `MOUSE_FILTER_STOP` is never dismissed.
- **Suggestion**:
  ```gdscript
  if overlay_layer != null and is_instance_valid(overlay_layer):
      var tw: Tween = overlay_layer.create_tween()
      if tw != null and root_ctrl != null and is_instance_valid(root_ctrl):
          tw.tween_property(root_ctrl, "modulate:a", 0.0, 0.35)
          tw.finished.connect(func() -> void:
              if is_instance_valid(overlay_layer):
                  overlay_layer.queue_free()
          )
      else:
          overlay_layer.queue_free()

  if is_instance_valid(self):
      _is_generating_rift = false
  ```

### [Major] Finding 2: Property Mismatch on `ReliquaryChest` Aborts Room Population

- **What**: Procedural dungeon generation throws runtime errors when populating rooms with chests.
- **Where**: `scripts/world/procedural_dungeon_generator.gd:1368, 2331, 2379` vs `scripts/interaction/reliquary_chest.gd:7`
- **Why**: `procedural_dungeon_generator.gd` attempts to set `r_chest.reward_scale`, but `ReliquaryChest` defines `depth_scale`.
- **Suggestion**: Add a getter/setter property alias `var reward_scale: float` to `scripts/interaction/reliquary_chest.gd` pointing to `depth_scale`, or update `procedural_dungeon_generator.gd` to use `depth_scale`.

---

## 4. Verified Claims

- Headless CLI check-only passes clean on all 7 scripts (`exit code 0`) → **PASS**
- Body meshes set to `SHADOW_CASTING_SETTING_SHADOWS_ONLY` in `first_person_body_controller.gd` → **PASS**
- Dynamic HUD compass width >= 780px in `gothic_hud_overhaul.gd` → **PASS**
- Church-to-Crypt stairs unblocked and walkable in `town_overworld.tscn` (tested via `test_stairwell_walk.gd`) → **PASS**
- Low portcullises replaced with open archways and bulkheads removed in `build_prefabs_and_level.gd` → **PASS**
- Floor slab exclusion on stairs verified in `procedural_dungeon_generator.gd` → **PASS**
- Weapon mount procedural recoil (+0.055m Z, +5.5 deg pitch, 0.14s tween) in `fps_viewmodel_controller.gd` → **PASS**
- Voxel enemy primitive remeshing in `blender_build_voxel_enemies.py` → **PASS**
- Deterministic BMesh terrain cutout and stepped micro-voxel elixir in `blender_build_voxel_town_and_loot.py` → **PASS**
- SurfaceTool micro-voxel box cluster for loot pickup in `loot_drop_pickup.gd` → **PASS**
- Deeper portal and return portal warp execution across biomes without soft-lock → **FAIL (Finding 1 & 2)**

---

## 5. Adversarial Challenge & Stress Tests

| Stress Scenario | Expected Behavior | Actual Behavior | Result |
| :--- | :--- | :--- | :--- |
| Player walks down central Church-to-Crypt stairwell | Continuous floor contact, no blocking walls | Smooth descent to `Z = -27.53`, ascent to `Z = -17.91` | **PASS** |
| Player walks up & down isolated `stairs_stone_4x4` | Ascends to `Y = 4.04m` without jumping; >= 80% floor contact on descent | Reached `Y = 4.04m`; 100% floor contact on descent | **PASS** |
| Rapid weapon firing recoil stacking | No additive position/rotation drift; snappiness | Kills active tween before re-triggering; returns to `Vector3.ZERO` | **PASS** |
| Player interacts with Deeper Rift Portal inside dungeon | Loading overlay displays, dungeon generates, overlay fades out | `self` is freed during dungeon regeneration; script crashes on `is_inside_tree()`; overlay remains permanently stuck | **FAIL** |
| Room chest population in procedural dungeon | Chest spawned with scaled rewards | `reward_scale` property error aborts room population | **FAIL** |

---

## 6. Integrity Audit

- **Hardcoded test results**: None found.
- **Dummy or facade implementations**: None found. Real geometric and algorithmic solutions implemented across all files.
- **Shortcuts bypassing tasks**: None.
- **Fabricated verification logs**: None. Worker M3 transparently recorded the `reward_scale` error in their caveats section.
- **Self-certifying work without genuine verification**: None.

---

## 7. Caveats

- Per strict Reviewer role constraints, implementation code was not modified by this agent.
- `town_overworld.tscn` and `test_stairwell_walk.gd` are 100% verified and free of regressions. The remaining fixes in `occult_portal.gd` and `reliquary_chest.gd` / `procedural_dungeon_generator.gd` are surgical (each < 15 lines).

---

## 8. Conclusion

**Verdict: REQUEST_CHANGES**

Milestones 1, 2, and 4 are well-executed, strictly typed, and independently verified. However, **Milestone 3 cannot be approved in its current state** due to the critical soft-lock in `scripts/interaction/occult_portal.gd` when transitioning through in-dungeon portals, as well as the chest property mismatch in `scripts/world/procedural_dungeon_generator.gd`.

---

## 9. Verification Method

To independently reproduce the findings:
```powershell
& "c:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --path . -s res://tools/verify_all_8_biome_portals.gd
```
*Observed Failure*: Script crashes on line 304 of `occult_portal.gd` (`Cannot call method 'is_inside_tree' on a previously freed instance`) and line 2331/2379 of `procedural_dungeon_generator.gd` (`Invalid assignment of property or key 'reward_scale' on ReliquaryChest`).
