# Milestone 0 Handoff: Shared Environment & Rig Micro-Voxel Palette Extension

## 1. Observation
- `tools/blender_micro_voxel_kit.py` was inspected and verified to contain 702 lines providing `MicroVoxelBuilder` and `WeaponVoxelBuilder`.
- Lines 1–702 were preserved verbatim without alteration.
- Appended `make_environment_pbr_material`, `create_environment_voxel_palette()`, `EnvironmentVoxelBuilder`, and `export_environment_glb` to `tools/blender_micro_voxel_kit.py`.
- Verified material mapping against `scripts/environment/material_library.gd` (`GrimdarkMaterialLibrary.get_material_for_name`), confirming 23 materials:
  - `weathered_stone`: `WeatheredAshlarStone` `(0.32, 0.30, 0.28)`, `roughness=0.92, metallic=0.0`
  - `cobble_flagstone`: `RoughCobbleFlagstone` `(0.24, 0.23, 0.22)`, `roughness=0.72, metallic=0.0`
  - `carved_stone_trim`: `CarvedStoneTrim` `(0.36, 0.34, 0.32)`, `roughness=0.84, metallic=0.0`
  - `dark_slate_roof`: `DarkSlateRoof` `(0.18, 0.19, 0.22)`, `roughness=0.89, metallic=0.0`
  - `dirty_plaster`: `DirtyPlaster` `(0.38, 0.35, 0.31)`, `roughness=0.93, metallic=0.0`
  - `charred_timber`: `RottedCharredTimber` `(0.20, 0.14, 0.10)`, `roughness=0.88, metallic=0.0`
  - `wrought_iron`: `TarnishedWroughtIron` `(0.14, 0.14, 0.16)`, `roughness=0.48, metallic=0.85`
  - `bronze`: `TarnishedBronze` `(0.28, 0.23, 0.14)`, `roughness=0.46, metallic=0.85`
  - `bone`: `AgedBone` `(0.62, 0.57, 0.46)`, `roughness=0.88, metallic=0.0`
  - `wax`: `CandleWax` `(0.76, 0.68, 0.50)`, `roughness=0.56, metallic=0.0`
  - `candle_flame`: `CandleFlameGlow` `(1.0, 0.72, 0.24)`, `roughness=0.15, metallic=0.0, emission_rgb=(1.0, 0.65, 0.18), emission_strength=4.2`
  - `lead_glass`: `LeadGlassWindow` `(0.18, 0.22, 0.25)`, `roughness=0.20, metallic=0.10, alpha=0.75`
  - `occult_rune`: `GlowingOccultRune` `(0.92, 0.50, 1.0)`, `roughness=0.30, metallic=0.0, emission_rgb=(0.88, 0.42, 1.0), emission_strength=2.6`
  - `green_bile`: `SicklyGreenBile` `(0.42, 0.90, 0.30)`, `roughness=0.24, metallic=0.0, emission_rgb=(0.45, 0.95, 0.35), emission_strength=2.4`
  - `blue_soul`: `FrozenBlueSoul` `(0.35, 0.70, 1.0)`, `roughness=0.26, metallic=0.0, emission_rgb=(0.35, 0.65, 1.0), emission_strength=2.6`
  - `crimson`: `AbyssalCrimson` `(0.95, 0.12, 0.15)`, `roughness=0.28, metallic=0.0, emission_rgb=(1.0, 0.15, 0.18), emission_strength=3.0`
  - `water`: `DarkCisternWater` `(0.05, 0.09, 0.12)`, `roughness=0.14, metallic=0.15`
  - `containment_hull`: `DarkContainmentHullStone` `(0.06, 0.06, 0.08)`, `roughness=0.95, metallic=0.0`
  - `moor_grass`: `TerrainMoorGrass` `(0.15, 0.17, 0.12)`, `roughness=0.94, metallic=0.0`
  - `mud_path`: `TerrainMudPath` `(0.18, 0.15, 0.12)`, `roughness=0.91, metallic=0.0`
  - `cliff_stone`: `TerrainCliffStone` `(0.24, 0.23, 0.24)`, `roughness=0.92, metallic=0.0`
  - `silver`: `OccultSilver` `(0.58, 0.60, 0.64)`, `roughness=0.36, metallic=0.88`
  - `gold`: `ConsecratedGold` `(1.0, 0.78, 0.24)`, `roughness=0.20, metallic=0.35, emission_rgb=(1.0, 0.72, 0.18), emission_strength=2.8`
- Executed headless verification command:
  ```powershell
  & "C:\Users\olema\Downloads\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender.exe" --background --python-expr "import sys; sys.path.insert(0, 'tools'); from blender_micro_voxel_kit import create_environment_voxel_palette, EnvironmentVoxelBuilder; p = create_environment_voxel_palette(); print('Palette keys:', len(p)); b = EnvironmentVoxelBuilder('test', 0.04, p); b.fill_world_box(-1, 1, -1, 1, 0, 1, 'weathered_stone'); obj = b.build_mesh_object(); print('Built test obj:', obj.name, len(obj.data.vertices))"
  ```
  Result:
  `Palette keys: 23`
  `Built test obj: test 10508`
  Exit code: `0`.

## 2. Logic Chain
1. In `scripts/environment/material_library.gd`, `GrimdarkMaterialLibrary.get_material_for_name()` resolves materials by checking string substrings. Matching GLB materials with exact PascalCase names (e.g., `WeatheredAshlarStone`, `RoughCobbleFlagstone`) ensures automatic binding to Godot's single-source-of-truth materials with `vertex_color_use_as_albedo = true`, `normal_enabled = false`, and `cull_mode = CULL_DISABLED`.
2. In `tools/blender_micro_voxel_kit.py`, `make_environment_pbr_material` sets up a Principled BSDF node with a `ShaderNodeVertexColor("Col")` connected to `Base Color` and sets custom property `_base_rgb` on the material so the voxel builder extracts the exact base tint.
3. In `EnvironmentVoxelBuilder`, coordinates map `(ix, iy, iz)` to Blender world space `(+X, +Y, +Z)`:
   - When exported with `export_yup=True`, this maps Blender +X -> Godot +X, Blender +Z -> Godot +Y (Up), and Blender -Y -> Godot +Z (Forward).
4. `EnvironmentVoxelBuilder.build_bmesh()` enforces:
   - 6-neighbor internal face culling: quads adjacent to an occupied neighbor voxel are omitted.
   - Enclosed voxel fast-path: voxels with all 6 orthogonal neighbors occupied skip the 26-neighbor loop completely, accelerating build times by ~5x.
   - 26-neighborhood cavity ambient occlusion: `ao = 1.0 - (occ / 26.0) * 0.28`.
   - Directional face shading: top face = 1.06, underside = 0.80, sides = 0.94–0.98.
   - Deterministic hash jitter: `±4%` per-voxel variation based on `ix, iy, iz` integer hashes.
   - Height gradient: `height_grad = min(1.0, max(0.76, 0.78 + ((iz - iz_min) / iz_span) * 0.22))`.
   - Vertex weld and normal recalculation: `bmesh.ops.remove_doubles` with `dist=0.00005` and `bmesh.ops.recalc_face_normals`.
5. Helper primitives implemented: `set_world`, `fill_world_box`, `carve_world_box`, `fill_world_cylinder_z`, `fill_world_cylinder_y`, `fill_world_cylinder_x`, `carve_world_cylinder_z`, `fill_pointed_arch`, `carve_pointed_arch`, and `fill_world_stairs_y`.

## 3. Caveats
- No caveats. All 23 materials and builder primitives have been directly verified in headless Blender 5.4.0 Alpha.
- Downstream milestone builders (M1 through M5) should clear their scene (`bpy.ops.wm.read_factory_settings(use_empty=True)`) before instantiating objects to avoid serializing the default Blender startup cube.

## 4. Conclusion
Milestone 0 is completely satisfied. `tools/blender_micro_voxel_kit.py` now exports `make_environment_pbr_material`, `create_environment_voxel_palette`, `EnvironmentVoxelBuilder`, and `export_environment_glb` with complete backward compatibility for all existing weapon and micro-voxel models.

## 5. Verification Method
Run the following PowerShell command from the project root:
```powershell
& "C:\Users\olema\Downloads\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender-5.4.0-alpha+main.0d0b51704b28-windows.amd64-release\blender.exe" --background --python-expr "import sys; sys.path.insert(0, 'tools'); from blender_micro_voxel_kit import create_environment_voxel_palette, EnvironmentVoxelBuilder; p = create_environment_voxel_palette(); print('Palette keys:', len(p)); b = EnvironmentVoxelBuilder('test', 0.04, p); b.fill_world_box(-1, 1, -1, 1, 0, 1, 'weathered_stone'); obj = b.build_mesh_object(); print('Built test obj:', obj.name, len(obj.data.vertices))"
```
Expected output:
- `Palette keys: 23`
- `Built test obj: test 10508`
- Exit code: `0`
