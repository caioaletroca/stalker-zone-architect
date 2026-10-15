# STALKER Zone Architect: Base Building

Modular, snapping base building (foundations, walls, doorways, flat roofs) for S.T.A.L.K.E.R. Anomaly / GAMMA, built as an add-on to **Hideout Furniture** (HF 2.3.2). The design and roadmap are in [docs/handoff.md](docs/handoff.md). To test it in game, follow [docs/testing.md](docs/testing.md).

## Layout

| Path | What |
|---|---|
| `gamedata/scripts/bb_*.script` | Mod code (see below) |
| `gamedata/configs/mod_system_bb_pieces.ltx` | Piece item/object sections |
| `gamedata/meshes/base_building/` | Exported greybox OGFs (generated) |
| `gamedata/textures/base_building/` | Solid-colour DDS textures (generated) |
| `assets/blender/bb_greybox.blend` | Blender source scene (generated) |
| `tools/blender/build_greybox.py` | Builds the .blend and exports the OGFs |
| `tools/make_dds.py` | Writes the solid-colour DDS textures |
| `tools/gen_piece_configs.py` | Generates the piece .ltx sections and string table |
| `tools/sim_snap.py` | Offline check of the snap/rotation maths |
| `tools/ogf_info.py` | Dumps OGF chunk headers |
| `references/` | Original HF / EMHF mods (git-ignored, reading only) |

## Scripts

- `bb_core`: registers the `building_piece` HF type and the callbacks, and rebuilds the registry on load
- `bb_hf_compat`: **every** HF hook lives here (start_placing_item, bbox SetWorldOrigin/CheckForCollisions, create_object). The mod no longer overrides any HF file.
- `bb_physics`: drops the engine's quantised physics snapshot before a piece spawns, so pieces don't twist on reload
- `bb_registry`: placed pieces by id and by structure
- `bb_piece`: reads `bb_*` config keys and stores data in HF's per-object storage
- `bb_socket`: module dimensions and socket/slot layouts
- `bb_piece`: also holds the engine-convention heading maths (`setXYZ`/`setHPB`); pieces are always level
- `bb_snap`: nearest free compatible slot, occupancy, snapped transform
- `bb_debug`: logging (`base_building[...]` in the game log)

## Rebuilding assets

You need Blender 5.x with the [blender-xray](https://github.com/PavelBlend/blender-xray) addon installed.

```bash
"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --factory-startup -P tools/blender/build_greybox.py
python tools/make_dds.py
```

Each piece is exported as a rigid skeleton (one armature with a box-shaped collision bone per part), because HF spawns placeables as `physic_object`. Artists replacing a greybox should keep the same origin (bottom centre), the same dimensions, and an armature with collision shapes.
