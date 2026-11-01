# AI Agent Guidelines (`AGENTS.md`) — Universal Godot 4.7 Standard

All AI coding agents working in this repository MUST strictly adhere to the following rules. This project targets **Godot 4.7** (`config/features=PackedStringArray("4.7", ...)`).

---

## 1. Strict Godot 4.7 Static Typing

Every GDScript (`.gd`) file must use explicit static typing throughout:

* **Variables & Constants:** Always specify explicit types (`var speed: float = 200.0`, `const MAX_HP: int = 100`) or use type inference (`:=`) only when the right-hand side type is unambiguous and literal/constructor-based. Avoid untyped `var`.
* **Typed Arrays & Dictionaries:** Always parameterize collections (`var items: Array[ItemData] = []`, `var scores: Dictionary[String, int] = {}`).
* **Function Signatures:** Every function—including virtual callbacks (`_ready() -> void`, `_process(delta: float) -> void`, `_physics_process(delta: float) -> void`, `_input(event: InputEvent) -> void`)—must declare explicit parameter types and a return type (`-> void` or `-> ReturnType`).
* **Node References:** Always type `@onready` and `@export` node variables (e.g., `@onready var sprite: Sprite2D = $Sprite2D`, `@export var target: Node3D`).
* **`Variant` Warning:** Never rely on implicit `Variant` inference for arithmetic, indexing, or method return values. Cast explicitly with `as Type` when retrieving values from untyped sources (e.g., JSON, generic dictionaries).

```gdscript
# CORRECT
class_name PlayerController
extends CharacterBody3D

@export var move_speed: float = 8.0
@onready var anim_player: AnimationPlayer = $AnimationPlayer

func _physics_process(delta: float) -> void:
	var input_dir: Vector2 = Input.get_vector("move_left", "move_right", "move_up", "move_down")
	velocity.x = input_dir.x * move_speed
	velocity.z = input_dir.y * move_speed
	move_and_slide()
```

---

## 2. Zero Godot 3.x Legacy Syntax

Godot 3.x APIs, keywords, and syntax are strictly forbidden. Always use Godot 4.x equivalents:

| Forbidden (Godot 3.x) | Required (Godot 4.x) |
| :--- | :--- |
| `export var x = 1` | `@export var x: int = 1` |
| `onready var n = $Node` | `@onready var n: Node = $Node` |
| `tool` | `@tool` (at top of file) |
| `yield(obj, "signal")` | `await obj.signal_name` |
| `connect("sig", self, "_on_sig")` | `sig.connect(_on_sig)` |
| `emit_signal("sig", arg)` | `sig.emit(arg)` |
| `instance()` (on `PackedScene`) | `instantiate()` |
| `KinematicBody2D` / `KinematicBody` | `CharacterBody2D` / `CharacterBody3D` |
| `Spatial` | `Node3D` |
| `Position2D` / `Position3D` | `Marker2D` / `Marker3D` |
| `AnimatedSprite` | `AnimatedSprite2D` / `AnimatedSprite3D` |
| `RayCast2D.cast_to` | `RayCast2D.target_position` |
| `move_and_slide(velocity, Vector2.UP)` | Set `velocity` property, then call `move_and_slide()` with 0 args |
| `change_scene("res://...")` | `get_tree().change_scene_to_file("res://...")` |
| `File.new()` / `Directory.new()` | `FileAccess.open(...)` / `DirAccess.open(...)` |
| `OS.get_ticks_msec()` | `Time.get_ticks_msec()` |
| `Tween` node | `create_tween()` |
| `funcref(obj, "method")` | `Callable(obj, "method")` or `obj.method` |
| `.empty()` on Array/String/Dict | `.is_empty()` |
| `deg2rad()` / `rad2deg()` / `lerp()` | `deg_to_rad()` / `rad_to_deg()` / `lerpf()` |
| `rand_range(a, b)` | `randf_range(a, b)` / `randi_range(a, b)` |

---

## 3. Code-Based Signal Connections Only

* **No `.tscn` Signal Connections:** Never add `[connection signal=...]` blocks inside `.tscn` scene files.
* **Connect in GDScript:** All signals must be connected in code (typically inside `_ready() -> void`) using Godot 4.x first-class `Signal` and `Callable` syntax.
* **Disconnect When Needed:** Use `signal_name.is_connected(callable)` / `signal_name.disconnect(callable)` or flags like `CONNECT_ONE_SHOT` when managing dynamic lifecycles.

```gdscript
# CORRECT
func _ready() -> void:
	start_button.pressed.connect(_on_start_button_pressed)
	health_component.died.connect(_on_died, CONNECT_ONE_SHOT)

func _on_start_button_pressed() -> void:
	pass

func _on_died() -> void:
	pass
```

```gdscript
# FORBIDDEN
connect("pressed", self, "_on_pressed")
start_button.connect("pressed", _on_start_button_pressed) # Avoid string-based signal names
```

---

## 4. Never Guess or Fabricate `uid://` Strings in `.tscn` / `.tres` Files

* **Ban on Invented UIDs:** Never fabricate, increment, or guess `uid="uid://..."` values in `.tscn`, `.tres`, or `.import` files. Invalid or colliding UIDs corrupt Godot's resource cache (`uid_cache.bin`).
* **Omit UIDs When Creating/Editing Text Resources:**
  * In `[gd_scene ...]` or `[gd_resource ...]` headers for newly created files, **omit the `uid` attribute entirely** (e.g., `[gd_scene load_steps=2 format=3]`). Godot will generate and assign a valid UID automatically when the project is opened or imported.
  * In `[ext_resource ...]` entries, reference resources strictly by `type`, `path="res://..."`, and `id="..."` unless you have **read the exact `uid://` string directly** from the target file's header or `.uid` / `.import` file in the workspace.

```ini
# CORRECT (when creating a new .tscn or adding an ext_resource without a known UID)
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/player.gd" id="1_player"]

[node name="Player" type="CharacterBody3D"]
script = ExtResource("1_player")
```

---

## 5. Mandatory Headless CLI Verification After Every Script Edit

After **every** creation or modification of a `.gd` script (or related `.tscn` / `project.godot` file), you **MUST** verify the script/project using the Godot CLI in headless check-only mode before concluding your task or moving on:

```bash
# Check a specific modified script:
godot --headless --check-only -s res://path/to/script.gd

# Or run from project root to validate project-wide context alongside the script:
godot --headless --path . --check-only -s res://path/to/script.gd
```

* **Zero Tolerance for Parse/Type Errors:** If `--check-only` outputs any parse errors, static typing errors, or missing identifier errors, fix them immediately and re-run verification until it exits cleanly (`exit code 0`).
* **First-Time Import / Class Cache:** If a new `class_name` or resource was added and `--check-only` cannot resolve it yet, run a headless import pass first:
  ```bash
  godot --headless --import
  ```
  Then re-run `godot --headless --check-only -s res://path/to/script.gd`.

---

## 6. Hybrid Modular Editor + AI World-Building Workflow

To ensure the user can always visually inspect, select, and manually drag-and-drop level objects inside the Godot Editor (`2D` or `3D` Viewport) while keeping scene files lightweight and 100% compatible with AI code updates, all level and world generation MUST follow these rules:

1. **Default to Persistent Scene Nodes Over Invisible Runtime-Only Spawning**:
   * Do NOT build levels solely via runtime-only `_ready()` code that leaves the Godot Editor viewport empty.
   * Whenever generating level geometry, landmarks, props, lighting, or environment zones, persist them into the active level `.tscn` file (via `@tool` scripts or headless bake utilities) and recursively set `node.owner = scene_root` so every object appears in the Godot Editor's Scene Tree and Viewport for manual placement.
   * **CRITICAL `PackedScene` Ownership Rule (`node.scene_file_path` Check):** When recursively assigning `node.owner = scene_root` before packing a `.tscn` file, **STOP recursion at any node that is an instantiated sub-scene (`node.scene_file_path != ""`)**! Set `instanced_node.owner = scene_root` on the root of the `.glb` or `.tscn` instance itself, and NEVER overwrite `.owner` on its internal children, or Godot will serialize duplicate nested nodes and trigger `incoming node's name clashes` warnings.

2. **Zero Inline `SubResource` Bloat in Main Level Scenes**:
   * NEVER dump thousands of lines of procedural `SubResource` meshes, raw vertex arrays, or deeply nested node trees directly into a main level `.tscn` file.
   * Save reusable props, buildings, landmarks, enemies, and interactive objects as modular prefab scenes under `res://scenes/prefabs/` (or instantiate them from `res://assets/models/*.glb`) and organize instances under clean parent category containers in the main scene (e.g., `WorldGeometry/Structures`, `WorldGeometry/Props`, `WorldGeometry/Lighting`, `WorldGeometry/Volumes`).

3. **Strict Transform Preservation (Editor Owns Position; Code Owns Behavior)**:
   * **CRITICAL RULE:** If a node or prefab instance ALREADY exists in a `.tscn` scene, runtime scripts MUST **NEVER** overwrite, reset, or hardcode its `global_position`, `position`, `rotation`, or `scale` in `_ready()`!
   * Runtime scripts must **discover and bind** existing scene nodes in-place and apply dynamic behaviors, shaders, animations, or physics relative to the node's current Editor transform (e.g., reading a node's Editor-placed coordinates as its patrol origin, spawn point, or physics anchor).

4. **Adding New Content via AI (`@tool` Sync Pattern)**:
   * When asked to add new objects or landmarks via code, first check `has_node(...)` in the appropriate scene container so existing user-placed nodes are never duplicated or reset.
   * Support baking newly added procedural nodes into the `.tscn` file via an `@tool` Inspector toggle (`@export var sync_new_nodes_to_scene: bool = false`) or a headless bake pass so the user can immediately move and rotate the new objects in the Godot Editor.

5. **Single Source of Truth for Environment & Physics Surfaces**:
   * Never create duplicate `WorldEnvironment`, primary `DirectionalLight3D`, or overlapping ground/water meshes that fight each other at runtime.
   * When custom vertex displacement shaders (e.g., terrain or water waves) interact with CPU gameplay physics, maintain 100% mathematical synchronization between the GPU shader and CPU physics queries via shared parameters.

---

## 7. 3D Asset & Art Direction Pipeline (Headless Blender & Meshy MCP)

1. **Mandatory `.glb` Asset Pipeline (Blender or Meshy MCP)**:
   * NEVER use placeholder Godot primitive meshes (`BoxMesh`, `CylinderMesh`, `PrismMesh`, `SphereMesh`) or raw `.obj`/`.mtl` vertex scripts for final 3D props, vehicles, characters, buildings, or environment assets unless explicitly requested for greybox prototyping.
   * 3D assets must be sourced via either:
     * **Meshy MCP Server (`@meshy-ai/meshy-mcp-server`)**: Generated via `text-to-3d` / `image-to-3d` with PBR maps enabled (`enable_pbr = true`), saved into `res://assets/models/generated/`, and normalized to real-world meter heights + grounded at `Y = 0.0` with physics colliders via a reusable asset loader utility (`res://scripts/meshy_asset_loader.gd`).
     * **Headless Blender Python Scripts** (`tools/blender_build_<asset>.py`): Executed headlessly (`blender --background --python tools/blender_build_<asset>.py`) and exported as binary glTF 2.0 (`GLB`) into `res://assets/models/`.
       * **Default Local Blender Executable (if not on `PATH`)**: `C:\Users\olema\Downloads\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender.exe`.
   * Always follow every `.glb` export or download with `godot --headless --import` (or `godot --headless --editor --quit`) so Godot generates `.import` metadata before referencing the `.glb` in scenes or GDScript.

2. **Minimum Geometric Detail, Modifier & Vertex Cavity Standards (Procedural Blender Scripts)**:
   Every `tools/blender_build_*.py` script MUST enforce a strict two-tier procedural geometry detail standard and vertex cavity shading:
   * **Tier 1 — Architectural & Environment Kit Pieces (`40–75+` distinct geometric sub-elements):**
     * **Ban on Slab/Block Silhouettes:** Never generate single-extrusion walls, roofs, or props. Construct architectural and environment assets from **40 to 75+ distinct geometric sub-elements**:
       * **Stone & Masonry:** Individual corner quoins, archway voussoir stones, recessed mortar joints, stepped base plinths, cornice moldings, and sill ledges.
       * **Timber & Roofs:** Exposed structural rafters, cross-bracing beams, corner iron brackets/rivets, and multi-layered roof slates or overlapping planks with subtle vertex sag/asymmetry.
       * **Metal & Fixtures:** 3D `CURVE` spline scroll-work, wrought-iron cages, hanging chains, and beveled trim.
     * **Mandatory Blender Vertex Cavity/AO Pass (`Dirty Vertex Colors`):** Before exporting architectural `.glb` meshes, bake a deterministic curvature/cavity + vertical ground-soot gradient into a byte/float Color Attribute (`Col` / `COLOR`) clamped strictly between `0.60` (crevices/ground base) and `1.00` (exposed stone faces) so physical 3D mortar grooves and corners have rich, hand-painted gothic depth without noisy textures.
   * **Tier 2 — First-Person Hero Viewmodels & Weapons (`90–140+` distinct geometric sub-elements across 3 detail frequencies):**
     * Must use parametric Python detail generators (`spawn_rivet_line`, `spawn_chain_links`, `spawn_articulated_finger`, `spawn_gothic_filigree`, `spawn_cartridge_assembly`) to generate primary forms, secondary mechanisms, and tertiary micro-details (rivets, screws, springs, chain links, scalloped armor lames, fluted ribs).
     * **Mandatory Pre-Export Hierarchy Joining (`bpy.ops.object.join`):** Join all static decorative sub-parts into their parent mechanical hierarchy node before `.glb` export so Godot gets 100+ physical 3D parts with minimal draw calls and a clean node tree!
   * **Mandatory Organic vs. Hard-Surface Routing:** Use procedural Blender Python strictly for architecture, terrain, weapons, and hard-surface props. For intricate organic sculptures (statues, gargoyles, skulls, monsters, corpses), ALWAYS route through the Meshy MCP Server (`text-to-3d` / `image-to-3d` with `enable_pbr = true`) rather than attempting to sculpt organic anatomy with math primitives.
   * **No Flat Boxes or Cylinders**: Structural edges must use `BEVEL` modifiers, `SUBSURF`, or multi-station `bmesh` lofting.
   * **Real Boolean Cavities (`BOOLEAN` `DIFFERENCE`)**: Windows, doors, archways, and structural cutouts must be physically carved out with recessed 3D frames rather than painted flat on textures.
   * **Natural Asymmetry & Micro-Detail**: Apply subtle vertex/lattice variation and 3D `CURVE` splines (cables, pipes, trim, bevels) so geometry never looks like sterile primitive blocks.
   * **Organic Displacement (`DISPLACE`)**: Rocks, cliffs, and organic meshes must use high-subdivision geometry driven by layered procedural displacement.

3. **Mandatory PBR Material, SSAO & Collider Standards (STRICT BAN on Procedural Noise Shaders)**:
   * **STRICT BAN on Procedural Noise Shaders & `NoiseTexture2D` on Architecture/Props:**
     * **CRITICAL RULE:** **NEVER** attach `NoiseTexture2D`, procedural Voronoi/FBM shaders (`triplanar_grimdark_pbr.gdshader`), or `dFdx`/`dFdy` normal math to architectural walls, floors, pillars, houses, or metal props (which cause leopard-print/camo artifacts).
     * Instead, use **clean, solid matte `StandardMaterial3D` multi-slot materials** (`vertex_color_use_as_albedo = true`, `roughness = 0.88–0.94`, `metallic = 0.0`, `specular = 0.15`, `normal_enabled = false` for stone/wood; `metallic = 0.85`, `roughness = 0.48–0.50`, `normal_enabled = false` for wrought iron) paired with **`WorldEnvironment` SSAO** (`ssao_enabled = true`).
   * Every 3D asset must use multi-slot `Principled BSDF` / `StandardMaterial3D` PBR materials with intentional `Base Color`, `Metallic`, `Roughness`, and `Emission` values suited to the game's art direction.
   * When instantiating `.glb` assets into prefabs or scenes, automatically generate appropriate static/convex/trimesh collision shapes (`StaticBody3D` / `CollisionShape3D`) and configure `visibility_range_end` (LOD/distance culling) to maintain 60+ FPS performance.
   * **Hollow / Walkable Meshes MUST Use Concave/Trimesh or Composite Box Colliders:** Never assign a single `ConvexPolygonShape3D` to a terrain chunk, room, doorway frame, archway, or building with a walkable interior, as convex hulls shrink-wrap openings and block the player. Always generate `ConcavePolygonShape3D` (trimesh) or compound `BoxShape3D` colliders for architectural pieces and terrain.

---

## 8. Visual & Scene Inspection via Godot MCP Bridge

Whenever a visual, lighting, shader, UI, or layout change is made, agents should verify the result visually using the project's capture and inspection tools rather than guessing:

* **MCP Server (`godot-inspector` in `.mcp.json` / `tools/godot_mcp_server.py`, if present)**:
  * `godot_capture_screenshot(view_mode, frames)`: Renders the live scene for `frames` frames (default `45`) and writes a screenshot to `res://.mcp_captures/latest_frame.png` alongside telemetry in `res://.mcp_captures/scene_state.json`. Inspect the image directly using file/image reading tools.
  * `godot_inspect_scene_tree(scene_path)`: Instantiates and dumps the node hierarchy, attached scripts, transforms, and exported properties of any `.tscn` scene.
  * `godot_check_scripts(script_paths)`: Runs `godot --headless --path . --check-only -s <script>` across modified scripts and returns structured diagnostics.
* **Direct CLI Frame Capture (`tools/mcp_capture_frame.gd`, if present)**:
  * Run `godot --path . -s res://tools/mcp_capture_frame.gd -- --view=<preset> --frames=45` to render and inspect in-game camera views headlessly or in a test window.

---

## 9. 3D Terrain, Walkable Interiors & Subterranean Level Architecture

All 3D overworld maps, towns, walkable buildings, basements, and underground catacombs MUST obey the following structural rules:

1. **Procedural Blender Terrain with Flattening Zones & Boolean Cutouts (`tools/blender_build_terrain.py`)**:
   * Overworld terrain with hills and valleys must be generated as chunked `.glb` meshes in Blender using subdivided grids and layered `DISPLACE` modifiers (never GPU-only vertex displacement shaders without matching CPU heightmap collision).
   * **Building Footprint Flattening:** Terrain scripts must define explicit vertex weight / flattening zones where major structures or town plazas sit so doors and stairs align predictably.
   * **Subterranean Cutouts (`BOOLEAN DIFFERENCE`):** Whenever a building has a walkable basement, cellar, or catacomb entrance descending below the terrain surface, the terrain Blender script MUST physically carve out the basement footprint using a `BOOLEAN` `DIFFERENCE` modifier so the terrain's `ConcavePolygonShape3D` collider does not block the stairwell.

2. **Mandatory Foundation Plinths for Sloped Terrain Buildings**:
   * Every exterior building or church prefab placed on uneven or hilly terrain must be modeled with a **2.0m to 3.0m stone foundation plinth / cellar base** extending below its local floor level (`Y = 0.0` down to `Y = -3.0`), plus entrance steps leading up to the doorway.
   * This ensures that when buildings are positioned on hillsides in the Godot Editor (following Rule 6.3), corners never float in mid-air.

3. **Modular Grid Architecture for Walkable Interiors & Catacombs (4m × 4m × 4m Standard)**:
   * Never generate an entire multi-room or multi-story walkable building/dungeon as a single monolithic mesh if it contains complex interior rooms.
   * Build walkable structures (such as the Church, Crypt Basement, and Catacombs) from a modular grid kit (`4m x 4m` footprint, `4m` height) exported as individual `.glb` prefabs (`wall_solid`, `wall_doorway`, `floor_tile`, `ceiling_vault`, `stairs_4x4`, `pillar`) under `res://scenes/prefabs/architecture/`.
   * Non-walkable background town buildings (facade shells) may be single solid `.glb` meshes with recessed `BOOLEAN` windows/doors to preserve 60+ FPS performance.

4. **Light-Bleeding & Subterranean Environment Isolation**:
   * Architectural walls, floors, and ceilings for walkable interiors and underground basements must have real geometric thickness (minimum `0.25m` to `0.5m` solid thickness) and shadow-casting enabled (`cast_shadow = SHADOW_CASTING_SETTING_DOUBLE_SIDED` where needed) to prevent exterior `DirectionalLight3D` sunlight/moonlight from leaking into dark basements and catacombs.

---

## 10. Strict Git Push Safety & Mandatory Verification Gate

* **Never Push Unprompted:** NEVER execute `git push` (or any command that pushes commits/tags/branches to a remote repository) unless the user has **explicitly** instructed you to push in their prompt.
* **Mandatory Verification Question Before Every Push:** Even when the user explicitly asks you to push to Git, you MUST **STOP** and ask a clear verification question first (using the `ask_question` tool or an explicit confirmation prompt stating the target remote, branch name, and summary of commits to be pushed) to make **ABSOLUTELY SURE** the user wants to push right now.
* **Wait for Explicit Confirmation:** Only execute `git push` after the user replies to that verification question with explicit confirmation. Never chain `git push` automatically after `git commit`.

---

## 11. Anti-Freeze & Large File Editing Safety Rules (Preventing `5m0s` Stream Idle Timeouts)

To permanently prevent AI agents from freezing, hitting the `5m0s` stream idle timeout, or getting stuck in an infinite retry loop on large files (`800–3,800+` lines):

1. **Strict Ban on Monolithic `write_file` Overwrites for Files > 400 Lines**:
   * **CRITICAL RULE:** **NEVER** call `write_file` (`Overwrite = true`) to rewrite an entire existing script or tool file that exceeds **400 lines** (such as `res://scripts/ui/gothic_character_menu.gd`, `res://tools/build_prefabs_and_level.gd`, `res://scripts/enemies/occult_enemy_ai.gd`, or `res://scripts/world/procedural_dungeon_generator.gd`).
   * Generating `2,000+` lines in a single tool call payload exceeds `8,000+` output tokens and stalls the model stream past the `5m0s` timeout.
   * **Always Use Surgical `edit_file` Replacements:** Modify existing large files strictly via targeted `edit_file` calls of **50–250 lines** at a time.
   * **When Creating a Brand-New Large File (> 400 Lines):** Write the initial skeleton (`<= 350` lines) with `write_file`, and then append remaining sections in chunks (`<= 350` lines per call) using `write_file` with `Append = true` or `edit_file`.

2. **Avoid Dumping Entire Multi-Thousand-Line Files into Context at Once**:
   * Before editing a large file, use `Select-String` / `grep` or targeted `read_file` line ranges (`StartLine` / `EndLine` of `150–400` lines) around the specific functions being modified rather than reading 3,000+ lines into the prompt context unless necessary.

3. **Subagent & Background Task Hygiene**:
   * Never leave finished subagents or background tasks dangling after their work is complete; terminate idle subagents via `manage_subagents(Action="kill_all")` once their task is verified.


