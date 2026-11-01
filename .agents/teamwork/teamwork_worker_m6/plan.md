# Worker M6 Plan: Headless Godot Import & Visual Telemetry Verification

1. Run headless Godot CLI import pass:
   `& "C:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --quit-after 240 --path . --import`
2. Verify exit code 0 and all 78 GLB assets imported.
3. Run in-game frame captures across presets (`overview`, `church`, `crypt`, `boss`):
   `& "C:\Users\olema\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --path . -s res://tools/mcp_capture_frame.gd -- --view=overview --frames=45`
4. Inspect `.mcp_captures/scene_state.json` and `.mcp_captures/latest_frame.png`.
5. Verify physics raycasts: stairwell unblocked, church doorway clear, crypt archway clear.
6. Document in `handoff.md` and report to orchestrator.
