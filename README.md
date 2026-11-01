# Dark Occult FPS

A gothic dark-fantasy first-person shooter and subterranean dungeon crawler built with **Godot 4.7** (`Forward+`) and a 100% procedural **Blender 5.4 Python 3D asset pipeline**.

---

## Features

### 1. Sanctuary Hub & Subterranean Catacombs (`town_overworld.tscn`)
- **Town Overworld & Ashen Chapel:** Explore a windswept gothic town, graveyard, and the walkable **Sanctuary of the Ashen Chapel** hub (`res://scenes/levels/town_overworld.tscn`).
- **Sanctuary Crafting & Progression Stations:**
  - **Weapon Workbench (`HubWeaponWorkbench`):** Upgrade and cycle occult weapon modifications across your arsenal.
  - **Armor Reliquary Stand (`HubArmorReliquaryStand`):** Unlock and equip 5-slot gothic armor sets.
  - **Sanctuary Upgrade Font & Target Dummy Plaque:** Test damage output and inspect combat telemetry in real time.
- **Eight Subterranean Catacomb Sanctums (`B1–B8`):** Descend from the Church Nave into the Crypt Basement and eight interconnected underground portal chambers housing the Occult Rift Portals.

### 2. Vertical Procedural Dungeon Generator (`ProceduralDungeonGenerator`)
- **Modular `4m × 4m × 4m` 3D Grid Architecture:** Generates multi-story vertical dungeons (`res://scripts/world/procedural_dungeon_generator.gd`) with full headroom clearance, multi-tier staircases, bridges, balconies, and vaulted ceilings.
- **Eight Distinct Occult Biomes:**
  1. **B1 — The Endless Ossuary**
  2. **B2 — The Iron Necropolis**
  3. **B3 — Reliquary of the Astral Heretic**
  4. **B4 — The Inquisitor's Rack**
  5. **B5 — The Plague Cisterns**
  6. **B6 — Cathedral of the Weeping Saint**
  7. **B7 — The Sunken Bell Foundry**
  8. **B8 — The Abyssal Sanctum**
- **Monumental Entry Vistas & Mood Mutators:** Includes *The Grand OssuaryPit*, *The Sunken Reliquary Nave*, and *The High Overlook Stairhall*, paired with dynamic lighting/fog mood mutators (*Blood Moon Eclipse*, *Plague Miasma*, *Abyssal Void*, *Ashen Ember*) and room-graph frustum/distance culling (`60+ FPS`).

### 3. First-Person Arsenal, Viewmodels & Occult Magic
- **Articulated 3D First-Person Viewmodel Rig (`FPSViewmodelController`):** Procedural weapon sway, recoil kinematics, reload animations, and armor-tier-aware gauntlets.
- **Three Distinct Weapons with Mod Tiers:**
  - **Flintlock Pistol** (Standard / Twin-Hammer / Abyssal Barrel)
  - **Hellfire Double-Barrel Shotgun** (Sawed-Off / Choke-Bore / Brimstone Bayonet)
  - **Pneumatic Stake Driver** (Heavy Iron Spike / Heated Coil / Reliquary Harpoon)
- **Occult Blood & Sigil Abilities:** Cast offensive and ward abilities alongside off-hand lantern illumination.

### 4. Gothic Character Menu, 3D Paperdoll & Automap (`GothicHudOverhaul`)
- **Interactive 3D Hunter Paperdoll (`HunterPaperdollRig`):** Inspect your equipped 5-slot armor pieces (*HEAD*, *CHEST*, *HANDS*, *LEGS*, *FEET*) across four full armor tiers:
  - *Set 1: Leather Stalker*
  - *Set 2: Inquisitor Brigandine*
  - *Set 3: Juggernaut Plate*
  - *Set 4: Abyssal Reliquary*
- **Blood & Occult Skill Tree:** Unlock passive and active combat nodes.
- **Real-Time Dungeon Automap (`GothicMapSystem`):** Tracks explored rooms, elevation layers, chests, and boss sanctums.

---

## Controls

| Action | Primary Binding | Secondary / Notes |
| :--- | :--- | :--- |
| **Move** | `W`, `A`, `S`, `D` | First-person character movement |
| **Fire Weapon** | `Left Mouse Button` | Primary ranged/melee attack |
| **Raise Lantern** | `Right Mouse Button` | Illuminates dark crypts & dungeons |
| **Reload** | `R` | Reload active firearm / stake driver |
| **Swap Weapon** | `Q` / `Mouse Wheel` | Cycle between Pistol, Shotgun, and Stake Driver |
| **Interact** | `E` | Use workbenches, chests, plaques, and rift portals |
| **Cast Occult Ability** | `F` | Cast currently selected occult spell |
| **Cycle Ability** | `G` | Switch active occult spell |
| **Character & Forge Menu** | `Tab` / `I` | Open Paperdoll, Inventory, Forge & Skill Tree |
| **Dungeon Automap** | `M` | Toggle dungeon map overlay |
| **Fullscreen Toggle** | `F11` | Toggle borderless fullscreen |
| **Release / Capture Mouse** | `Esc` | Toggle mouse cursor capture |

---

## Project Structure

```text
├── assets/
│   ├── audio/               # Ambient soundscapes and combat SFX
│   └── models/              # Procedural Blender-generated .glb architecture, weapons, armor & enemies
├── scenes/
│   ├── levels/
│   │   └── town_overworld.tscn          # Main playable scene (Town, Church Hub, Crypts & Dungeon Host)
│   └── prefabs/
│       ├── architecture/                # Modular 4m x 4m gothic stone/timber/crypt kit prefabs
│       ├── armor/                       # First-person & paperdoll gauntlet/armor prefabs
│       ├── dungeon/                     # Biome-specific monoliths, furnaces, braziers & walls
│       ├── enemies/                     # 8 biome bosses/elites + crypt enemies
│       ├── environment/                 # Terrain, houses, dead trees, fences & street lamps
│       ├── hub/                         # Workbenches, reliquary stands, portals & chests
│       └── player/                      # First-person player controller & viewmodel rig
├── scripts/
│   ├── enemies/             # Enemy AI, projectiles & combat state machines
│   ├── environment/         # Material library, torch flicker & ambient soundscape controllers
│   ├── interaction/         # Hub stations, portals, chests & target dummy plaques
│   ├── items/               # Loot drop pickups
│   ├── player/              # FPS movement, viewmodel kinematics, loadout & HUD scripts
│   ├── ui/                  # Gothic HUD overhaul, character menu, paperdoll rig & automap
│   └── world/               # ProceduralDungeonGenerator & zone performance/visibility managers
├── shaders/                 # Custom sky, portal vortex, volumetric fog & vellum UI shaders
└── tools/                   # Headless Blender Python builders (blender_build_*.py) & CLI test suites
```

---

## Running & Verifying the Project

### Requirements
- **Godot Engine 4.7+** (Standard GDScript build with `Forward+` Vulkan rendering)
- **Blender 5.4+** *(optional, only required when regenerating `.glb` models from `tools/blender_build_*.py`)*

### Opening in Godot Editor
```bash
godot --path . --editor
```

### Running the Game Directly
```bash
godot --path .
```

### Headless CLI Verification & Empirical Test Suite
```bash
# Check static typing & script compilation on any script:
godot --headless --path . --check-only -s res://scripts/world/procedural_dungeon_generator.gd

# Run the Milestone 5 empirical stairwell, physics & procedural dungeon verification suite:
godot --headless --path . -s res://tools/test_milestone5_empirical.gd
```
