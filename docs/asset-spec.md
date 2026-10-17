# Asset guide for 3D artists

**Zone Architect** is a snap-together base-building mod for S.T.A.L.K.E.R. Anomaly / GAMMA. Think Palworld or Fallout 4 settlements: you place a foundation, and walls, doorways and roofs snap onto it. The building system already works in game, but every piece is a flat-coloured box.

We're looking for artists to turn those boxes into real Zone-style building sets ("tilesets"): scrap wood, corrugated metal, Soviet concrete and so on.

This guide covers what a piece has to be so it snaps and works in game. Everything else is up to you.

---

## 1. What to make

A tileset is one set of these four pieces in a shared style:

| Piece | Size (W × D × H) | Notes |
|---|---|---|
| Foundation | 2.5 × 2.5 × 0.2 m | Floor slab. Players walk on the top face. |
| Wall | 2.5 × 0.2 × 3.0 m | Plain wall. |
| Doorway wall | 2.5 × 0.2 × 3.0 m | Same as the wall, with a **1.2 m wide × 2.2 m tall** opening in the centre, starting at the floor. |
| Flat roof | 2.5 × 2.5 × 0.2 m | Ceiling/roof slab. Also used as a floor for a second storey. |

Later sets may add window walls, half walls, stairs and sloped roofs, but these four are the first goal.

```
Foundation / roof (top view)        Wall (front view)       Doorway wall (front view)

+-----------------+                 +-----------------+      +-----------------+
|                 |                 |                 |      |      |    |     |
|                 |  2.5 m          |                 | 3.0 m|      |    |     | 3.0 m
|        +        |                 |                 |      |      |    |     |
|     (origin)    |                 |                 |      |      |    |     |
+-----------------+                 +--------+--------+      +------+----+-----+
      2.5 m                                  ^ origin              <1.2m> (2.2 m tall)
                                          2.5 m                    2.5 m
```

The flat-coloured greybox pieces are in [`assets/blender/bb_greybox.blend`](../assets/blender/bb_greybox.blend). Open it and model over them. That's the easiest way to get the sizes right.

## 2. Hard requirements (needed for snapping and physics)

These are the rules the game depends on. If one is off, pieces won't line up, players will fall through floors, or the game can crash.

### Size and origin
- **Keep the outer dimensions exact** where pieces meet: wall ends, slab edges, wall bottoms and tops. Snapping places pieces exactly 2.5 m apart and stacks walls exactly 3.0 m high.
- **Origin at the bottom centre** of the piece (the middle of the footprint, at floor level).
- **Wall thickness is a 0.2 m core**, centred on the origin. Surface detail (planks, ribs, trims) may stick out up to about **5 cm** on each face. Keep the ends of the wall flat so neighbouring walls meet cleanly.
- **Blender axes:** X = width, Y = depth, Z = up (Blender Z becomes the game's up axis on export). Walls run along X.
- **Scale 1:1** (1 Blender unit = 1 m), with all transforms applied.

### Rig and collision
Each piece is a physics object in the game, so it has to be exported as a skeleton with collision boxes, even though it never moves:
- **One armature** as the root object, with the mesh objects parented to it (Armature modifier, every vertex 100% weighted).
- **The root bone must be named `link`.** The game anchors this bone to the world.
- **One collision box per solid part**, each on its own bone (set on the bone with blender-xray's shape tools: Shape = Box):
  - Foundation, wall and roof: one box, on `link`.
  - Doorway wall: three boxes (left post, right post, top lintel) so players can walk through the opening. Extra bones are children of `link`.
- **Collision boxes match the block-out size**, shrunk by about 5 mm per side so touching neighbours don't overlap. Detail on your mesh doesn't need collision.
- **Bone settings:** joint type **Rigid**, game material `default_object`, mass about 1000 in total. Copy them from the greybox file.

### Materials and textures
- **One material per mesh object.** That's a limit of the X-Ray exporter. A piece can have several mesh objects if you need several materials.
- **Shader** (blender-xray material panel): `models\model`, compile shader `default`.
- **Texture path:** the exporter uses the name of the image texture node as the game texture path, e.g. `base_building\wood_shack_wall`. Use the folder `base_building\` plus a descriptive name.
- **Reuse textures from the game wherever you can.** Anomaly ships lots of tileable wood, metal, brick and concrete textures. Referencing them by their game path costs nothing, matches the game's look, and needs no extra files.
- **New textures:** deliver `.dds` (diffuse; a normal map if you have one) plus your source files (PNG/TGA/PSD). **Don't write `.thm` files by hand.** A malformed `.thm` crashes the game at start-up. We'll generate them with the official tools.
- **Texture source:** your own work, or CC0 (e.g. Poly Haven, ambientCG). Nothing ripped from other games.

## 3. Guidelines (flexible)
- **Style:** Zone-built and weathered. Salvaged boards, rusty sheet metal, cracked concrete, makeshift repairs. Look at the hideouts and shacks in Anomaly.
- **Triangles:** about 500–3,000 per piece. Bases can have dozens of pieces on screen at once.
- **Textures:** 1024² is usually plenty; 2048² for a shared atlas across the whole set.
- **Tiling:** pieces repeat side by side, so avoid unique details (a sign, a big stain) in exactly the same spot on every wall. Keep those for optional variants.
- **Inside and outside:** walls are seen from both sides; roofs from below as a ceiling and from above.
- **LODs:** not needed for now.

## 4. Tools and export
- **Blender** (4.x/5.x) with the [blender-xray](https://github.com/PavelBlend/blender-xray) addon.
- **Export:** select the armature, then *File → Export → X-Ray → Game Object (.ogf)*, format **CS/CoP**. You get one `.ogf` per piece. Name files after the set, e.g. `bb_shack_wall.ogf`.
- **Not comfortable with the rig or export?** That's fine. Send the `.blend` with the modelled and UV'd meshes at the right size and origin, and we'll do the rig, collision and export. The rules in section 2 still matter for the mesh itself.
- **Testing it yourself (optional):** put the `.ogf` in `gamedata/meshes/base_building/`, point a piece's `visual =` line in `gamedata/configs/mod_system_bb_pieces.ltx` at it, and follow [docs/testing.md](testing.md).

## 5. What to deliver
- [ ] The `.blend` source file(s).
- [ ] An exported `.ogf` per piece, or a note asking us to export.
- [ ] Textures: `.dds` plus sources, or a list of the game texture paths you used.
- [ ] One or two screenshots or renders of the set.
- [ ] The name you'd like to be credited as.

## 6. Credit and license
You'll be credited by name in the mod page and README. The code and assets in the repository are released under the [MIT license](../LICENSE); by contributing, you agree your assets go out under the same license. If you need a different license (for example CC BY), say so before you start and we'll sort it out.

## Questions
Open an issue on the [GitHub repo](https://github.com/caioaletroca/stalker-zone-architect/issues) or reply to the Reddit post. Happy to answer anything, from scale questions to "does this look Zone enough".
