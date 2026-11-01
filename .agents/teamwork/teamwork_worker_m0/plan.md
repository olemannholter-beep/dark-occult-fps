# Worker M0 Plan: Shared Environment & Rig Micro-Voxel Palette Extension

Target File: `tools/blender_micro_voxel_kit.py`
Scope: Requirement R1
1. Implement `make_environment_pbr_material` with vertex color ('Col') input to Base Color, PBR parameters, alpha and emission.
2. Implement `create_environment_voxel_palette()` with 23 materials matching `GrimdarkMaterialLibrary` in `scripts/environment/material_library.gd`.
3. Implement `EnvironmentVoxelBuilder` with coordinate transformation (Blender Z-up, export_yup=True), 26-neighborhood cavity AO, directional face shading, hash jitter, and 6-neighbor internal face culling.
4. Verify with Blender Python test invocation.
