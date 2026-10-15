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
| `tools/gen_piece_configs.py` | Generates the piece .ltx sections, recipes and string table |
| `tools/sim_snap.py` | Offline check of the snap/rotation maths |
| `tools/ogf_info.py` | Dumps OGF chunk headers |
| `gamedata/configs/items/settings/mod_craft_bb_pieces.ltx` | Workshop recipes for GAMMA (Furniture tab, generated) |
| `optional/vanilla-anomaly-crafting/` | Use instead of the GAMMA recipes on vanilla Anomaly (Equipment tab) |
| `references/` | Original HF / EMHF mods (git-ignored, reading only) |

## Scripts

- `bb_core`: registers the `building_piece` HF type and the callbacks, and rebuilds the registry on load
- `bb_hf_compat`: **every** HF hook lives here (start_placing_item, bbox SetWorldOrigin/CheckForCollisions, create_object). The mod no longer overrides any HF file.
- `bb_binder`: pieces' script binder (HF's binder subclass) that calls `bb_physics` on spawn
- `bb_physics`: drops the engine's quantised physics snapshot before a piece spawns, so pieces don't twist on reload
- `bb_registry`: placed pieces by id and by structure
- `bb_piece`: reads `bb_*` config keys, stores data in HF's per-object storage, and holds the engine-convention heading maths (`setXYZ`/`setHPB`); pieces are always level
- `bb_socket`: module dimensions and socket/slot layouts
- `bb_snap`: nearest free compatible slot, occupancy, snapped transform
- `bb_debug`: logging (`base_building[...]` in the game log)

## Rebuilding assets

You need Blender 5.x with the [blender-xray](https://github.com/PavelBlend/blender-xray) addon installed.

```bash
"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --factory-startup -P tools/blender/build_greybox.py
python tools/make_dds.py
```

Each piece is exported as a rigid skeleton (one armature with a box-shaped collision bone per part), because HF spawns placeables as `physic_object`. Artists replacing a greybox should keep the same origin (bottom centre), the same dimensions, and an armature with collision shapes.

## Crafting

Pieces are crafted at a workshop first and then placed, like all Hideout Furniture items. Costs live in the `RECIPES` table in `tools/gen_piece_configs.py`. Run it to regenerate both recipe files.

| Piece | Tools | Parts |
|---|---|---|
| Foundation | basic | 8 wood, 4 scrap, 4 fasteners |
| Wall | basic | 8 wood, 3 fasteners |
| Doorway wall | basic | 7 wood, 3 fasteners |
| Flat roof | basic | 6 wood, 2 scrap, 3 fasteners |

GAMMA lists them in the workshop's **Furniture** tab. On vanilla Anomaly (no Furniture tab), delete `gamedata/configs/items/settings/mod_craft_bb_pieces.ltx` and copy in `optional/vanilla-anomaly-crafting/gamedata` instead; the pieces then appear in the **Equipment** tab. Don't install both, or the pieces show up in two tabs.

Tilesets add their own recipes the same way: a `mod_craft_*.ltx` file that appends (`![8]`) lines for their own item sections.

## License

[MIT](LICENSE). This covers the code and assets in this repository only. Hideout Furniture, Even More Hideout Furniture and S.T.A.L.K.E.R. Anomaly / GAMMA are separate works by their own authors and are not included here; this mod requires them to be installed.
