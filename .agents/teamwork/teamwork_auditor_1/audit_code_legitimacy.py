import ast
import os

WORKSPACE = r"c:\Users\olema\Downloads\alpha branch"
SCRIPTS = [
    "tools/blender_micro_voxel_kit.py",
    "tools/blender_build_voxel_church_and_hub.py",
    "tools/blender_build_voxel_crypt_kit.py",
    "tools/blender_build_voxel_dungeons_biomes.py",
    "tools/blender_build_voxel_town_and_loot.py",
    "tools/blender_build_voxel_enemies.py",
]

def audit_code_legitimacy():
    print("=" * 80)
    print("AUDIT 4: CODE QUALITY & LEGITIMACY AUDIT")
    print("=" * 80)

    for rel in SCRIPTS:
        full = os.path.join(WORKSPACE, rel)
        assert os.path.exists(full), f"Script {rel} missing!"
        with open(full, "r", encoding="utf-8") as f:
            code = f.read()

        lines = code.splitlines()
        tree = ast.parse(code, filename=rel)

        # Count functions, classes, imports
        func_defs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        class_defs = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]

        # Check for facade patterns: functions with only pass or return constant
        facades = []
        for fn in func_defs:
            if len(fn.body) == 1:
                stmt = fn.body[0]
                if isinstance(stmt, ast.Pass):
                    facades.append((fn.name, fn.lineno, "pass only"))
                elif isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Constant):
                    # Check if it's not a trivial helper
                    facades.append((fn.name, fn.lineno, f"returns constant {stmt.value.value}"))

        # Look for key micro-voxel features
        has_26_neighborhood = "26" in code or "neighbor" in code.lower()
        has_cavity_ao = "cavity" in code.lower() or "ao" in code.lower()
        has_face_shading = "face_shade" in code or "directional" in code.lower() or "1.06" in code
        has_vertex_colors = "color" in code.lower() or "vertex_color" in code.lower() or "col" in code.lower()
        has_palette = "palette" in code.lower() or "material" in code.lower()

        print(f"\n--- {rel} ---")
        print(f"Lines: {len(lines):,} | Classes: {len(class_defs)} | Functions: {len(func_defs)}")
        print(f"Features: 26-neighborhood={has_26_neighborhood}, Cavity AO={has_cavity_ao}, Face Shading={has_face_shading}, Vertex Colors={has_vertex_colors}, Palette={has_palette}")
        if facades:
            print(f"Potential facade functions ({len(facades)}): {facades}")
        else:
            print("Facade check: 0 dummy/empty functions found.")

if __name__ == "__main__":
    audit_code_legitimacy()
