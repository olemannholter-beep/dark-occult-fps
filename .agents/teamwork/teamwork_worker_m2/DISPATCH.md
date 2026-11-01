# Dispatch for teamwork_worker_m2

## Mission: Milestone 2 — Stairwell Unblocking, Prefabs & HUD Compass Banner

### Input Documents
- Authoritative User Request: `c:\Users\olema\Downloads\alpha branch\.agents\teamwork\ORIGINAL_REQUEST.md` (MUST READ FIRST)
- Survey 2 Report: `c:\Users\olema\Downloads\alpha branch\.agents\teamwork\teamwork_explorer_survey_r2_2\handoff.md`
- Implementation Plan: `C:\Users\olema\.gemini\antigravity\brain\3fdccabf-a502-4898-a4fc-87712a69f098\implementation_plan.md`

### Exclusive Write Ownership
You own ONLY:
- `c:\Users\olema\Downloads\alpha branch\scripts\ui\gothic_hud_overhaul.gd`
- `c:\Users\olema\Downloads\alpha branch\scripts\world\procedural_dungeon_generator.gd`
- `c:\Users\olema\Downloads\alpha branch\tools\build_prefabs_and_level.gd`
- Output baked scene: `c:\Users\olema\Downloads\alpha branch\scenes\levels\town_overworld.tscn`
Do NOT modify any other files.

### Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

### Task Description
Implement the fixes following Survey 2 handoff:
1. In `scripts/ui/gothic_hud_overhaul.gd`:
   - In `_draw_top_biome_plaque()`, dynamically calculate text width via `font.get_string_size(full_header, ...).x` and set `plaque_w = maxf(780.0, text_w + 48.0)` so "SUBTERRANEAN CATACOMB SANCTUMS : EIGHT PORTAL CHAMBERS (SAFE HARBOUR)" is never truncated.
2. In `scripts/world/procedural_dungeon_generator.gd`:
   - In `_seal_voxel_cells()` around line 901: prevent spawning `ProcFloor_%d` and `SealerSubFloor_%d` over stairs: `if (is_outer_bottom or is_balcony_floor) and not stair_cells.has(cell) and not stair_cells.has(below_cell):`.
   - Add `_is_stair_passage_boundary()` helper and skip placing `ProcWallN`, `ProcWallS`, `ProcWallW`, `ProcWallE` across stair entry and exit faces.
   - In `_carve_ossuary_v2_room()` for `OSSUARY_L_CATACOMB`: carve both `gy` and `gy + 1` (`for dy in range(h):`) so corridor stairs don't hit a 4m bulkhead.
3. In `tools/build_prefabs_and_level.gd`:
   - In Church Nave stairwell (lines 3014–3024): remove `StairwellWallSouth` and `StairwellNorthBulkheadWall`, register `stair_church_crypt`, and add stair passage entries in `open_passages`.
   - In `_seal_crypt_grid_boundaries()`: ensure stair cells (`is_stair_cell`) never spawn `AutoSealFloor`, and respect `open_passages` so `AutoSealWallExt_*` never walls off stairwells.
   - Replace low portcullis meshes (`Ch6PortcullisSouth`, `Ch5PortcullisSouthStairs`, `Ch7PortcullisSouthStairs`, `Ch8PortcullisSouthEntrance`) with `wall_stone_arch_door.tscn`, and remove overhead solid bulkheads (`Ch7WallSouthHighStairBulkhead`, `Ch8WallSouthHighCenter`).
   - Run the level bake pass (`tools/build_prefabs_and_level.gd`) to regenerate `town_overworld.tscn`.
4. Strictly adhere to Godot 4.7 static typing (`AGENTS.md` Rule 1) and surgical replacements <= 250 lines (`AGENTS.md` Rule 11.1).

### Verification Requirement
Run the Godot headless check:
`& "c:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --path . --check-only -s res://scripts/ui/gothic_hud_overhaul.gd`
`& "c:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --path . --check-only -s res://scripts/world/procedural_dungeon_generator.gd`
`& "c:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --path . --check-only -s res://tools/build_prefabs_and_level.gd`
`& "c:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --path . -s res://tools/build_prefabs_and_level.gd`
Verify all checks exit with code 0.

Write your completion report to `c:\Users\olema\Downloads\alpha branch\.agents\teamwork\teamwork_worker_m2\handoff.md` and notify parent orchestrator via `send_message`.
