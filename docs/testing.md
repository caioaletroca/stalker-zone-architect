# In-game test guide

## Setup (once)

1. Run `deploy.ps1` (it links `gamedata/` into `C:\GAMMA\mods\STALKER Zone Architect - Base Building`). This is already done on this machine, so edits in the repo are live in game.
2. In MO2, profile **G.A.M.M.A**: make sure **STALKER Zone Architect - Base Building** is ticked and sits above (higher priority than) *Hideout Furniture* and *Even More Hideout Furnitures*.
3. Launch Anomaly from MO2 with **debug mode** on (tick "Debug mode" in the Anomaly launcher, or add `-dbg` to the executable arguments). You need it to spawn items.
4. Start a new game or load a save. Stand somewhere open and flat for the first run.

Log file: `C:\Anomaly\appdata\logs\xray_<user>.log`. Every line from this mod starts with `base_building[`.

## Spawning pieces

Open the debug menu, go to the item spawner, search for `bb_item`, and spawn several of each:

| Item section | Piece | Colour |
|---|---|---|
| `bb_item_foundation` | Foundation 2.5 × 2.5 m | green |
| `bb_item_wall` | Wall 2.5 × 3 m | blue |
| `bb_item_wall_doorway` | Doorway wall | orange |
| `bb_item_roof_flat` | Flat roof 2.5 × 2.5 m | red |

To place an item, use it from the inventory (HF's *Place* action). Use (F) confirms, Esc cancels, Tab toggles HF collision, Caps Lock toggles surface alignment. Snapping works in both alignment modes.

## Test 1: game loads and pieces render

- [ ] The game reaches the main menu and loads a save without crashing.
- [ ] Log contains `base_building[core]: bb_core starting (v0.3.1)` and `Installed HF preview, collision and creation hooks`.
- [ ] Place one foundation. It shows as a flat **green** slab. You can walk on it without falling through, and it doesn't slide or fall over.

If it crashes, send me the end of the log (the part after `FATAL ERROR` / `stack trace`).

## Test 2: foundations snap

1. Hold a second foundation and aim at the ground just past the middle of one edge of the first.
2. [ ] The preview box jumps flush against that edge and matches the first slab's rotation, even if you turned while holding it.
3. Place it. [ ] Log: `Placed obj_id=… attached to obj_id=… socket=east|west|north|south`.
4. Build a 2 × 2 square. [ ] Every slab is level with the first one, even on a slope.
5. [ ] Aim at an edge that already has a neighbour: there's no snap there (occupied), and the log says `no snap`.

## Test 3: walls

1. Hold a wall and aim at the top of a foundation, close to an edge.
2. [ ] The wall snaps upright onto the edge line, running along it. Try all four edges.
3. [ ] Aim at the side of a placed wall: the next wall continues the line.
4. [ ] Aim at an edge shared by two foundations: only one wall can go there.
5. Place a **doorway wall** the same way. [ ] It snaps like a wall, and you can walk through the opening.

## Test 4: roof

1. Enclose a foundation with 3 walls and 1 doorway wall.
2. Hold a roof and aim at the top of a wall from **inside** the room.
3. [ ] The roof snaps over the room, on the side you're standing on.
4. [ ] Aim at the edge of a placed roof: another roof panel snaps next to it.
5. [ ] A wall aimed at a roof edge snaps on top of it (second storey).

## Test 5: save / reload / pickup

1. Save, quit to the main menu, and load the save.
2. [ ] Log: `Rebuilt registry, pieces=N`, where N is the number of pieces you placed.
3. [ ] New walls and roofs still snap to the old pieces.
4. Pick up one wall (HF interaction on the piece). [ ] That edge accepts a wall again.
5. Leave the level and come back. [ ] Snapping still works, and pieces from another map never snap here.

## Things to note while recording

- If a piece looks rotated 90° or sits on the wrong side, note which piece, which socket name the log printed, and roughly how the first foundation was rotated.
- Building pieces always stand level (only their heading follows the camera), even in HF's surface-align mode. On a slope a foundation cuts into the ground on the uphill side. That's intended: structures don't tilt with terrain.
- Building pieces skip HF's collision check on purpose, so level slabs can cut into slopes and snapped pieces can touch their neighbours. To get the normal check back, set `IGNORE_COLLISION = false` in `bb_snap.script`.
- Every time a piece comes online the log prints `base_building[physics]: net_spawn obj_id=... snapshot=dropped|none`. Right after placing it's `none`; after a reload or a far trip it should be `dropped`, meaning the engine's compressed physics snapshot was removed so the piece spawned on its exact transform.
- Every `Registered obj_id=...` log line prints the saved transform (`pos`, `angle_deg`) and the live server transform (`live`, `live_angle_deg`). The first and third angle values should be 0, and saved and live values should match.
- Snap range is 1.5 m around the aimed socket (`SNAP_RADIUS` in `bb_snap.script`).
