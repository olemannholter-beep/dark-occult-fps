# Dispatch for teamwork_worker_m1

## Mission: Milestone 1 — FPS Camera Clipping Fix

### Input Documents
- Authoritative User Request: `c:\Users\olema\Downloads\alpha branch\.agents\teamwork\ORIGINAL_REQUEST.md` (MUST READ FIRST)
- Survey 1 Report: `c:\Users\olema\Downloads\alpha branch\.agents\teamwork\teamwork_explorer_survey_r2_1\handoff.md`
- Implementation Plan: `C:\Users\olema\.gemini\antigravity\brain\3fdccabf-a502-4898-a4fc-87712a69f098\implementation_plan.md`

### Exclusive Write Ownership
You own ONLY:
- `c:\Users\olema\Downloads\alpha branch\scripts\player\first_person_body_controller.gd`
Do NOT modify any other files.

### Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

### Task Description
Implement the camera clipping fix in `first_person_body_controller.gd` following Survey 1 handoff:
1. Ensure all `MeshInstance3D` nodes in `first_person_body_controller.gd` are configured with `GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY`.
2. In `_spawn_box()`, explicitly set `mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY`.
3. In `_configure_fp_armor_meshes_recursive()`, set `(n as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY`.
4. Add helper method `_apply_first_person_shadow_only(root_node: Node) -> void` and invoke it at the end of `_ready()` and `refresh_armor_appearance()`.
5. Strictly adhere to Godot 4.7 static typing (`AGENTS.md` Rule 1) and surgical replacements <= 250 lines (`AGENTS.md` Rule 11.1).

### Verification Requirement
Run the Godot headless check:
`& "c:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --path . --check-only -s res://scripts/player/first_person_body_controller.gd`
Verify it exits with code 0.

Write your completion report to `c:\Users\olema\Downloads\alpha branch\.agents\teamwork\teamwork_worker_m1\handoff.md` and notify parent orchestrator via `send_message`.

## 2026-11-01T15:42:21Z
You are Worker M1 for Milestone 1 (FPS Camera Clipping Fix).
Your working directory is: c:\Users\olema\Downloads\alpha branch\.agents\teamwork\teamwork_worker_m1\
Read DISPATCH.md in your working directory and ORIGINAL_REQUEST.md at c:\Users\olema\Downloads\alpha branch\.agents\teamwork\ORIGINAL_REQUEST.md.
Also read the Survey 1 handoff report at c:\Users\olema\Downloads\alpha branch\.agents\teamwork\teamwork_explorer_survey_r2_1\handoff.md.

Implement the camera clipping fix in `scripts/player/first_person_body_controller.gd`.
Strictly adhere to Godot 4.7 static typing (AGENTS.md Rule 1) and surgical replacements <= 250 lines (AGENTS.md Rule 11.1).
Run the Godot headless check to verify exit code 0.
Write your completion report to `handoff.md` in your working directory and notify me via send_message.
