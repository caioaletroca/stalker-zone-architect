PROJECT: Modular Base Building for S.T.A.L.K.E.R. Anomaly / GAMMA
TARGET: Anomaly 1.5.x / current GAMMA-compatible Hideout Furniture ecosystem
LANGUAGE: Lua + Anomaly/X-Ray configuration files
DEPENDENCY: Hideout Furniture (HF)
OPTIONAL INTEGRATIONS LATER: Homestead, Custom Base Safe Havens

============================================================
1. PROJECT GOAL
============================================================

Implement a modular player base-building system on top of Hideout Furniture.

The desired experience is inspired by Palworld / ARK / Fallout 4:

1. Player places an initial foundation/floor piece.
2. That piece establishes a local building coordinate system.
3. Additional foundations/floors snap to compatible edges.
4. Walls snap to floor/foundation edges.
5. Doorway/window walls behave as wall variants.
6. Upper floors/ceilings/roofs snap to compatible structural sockets.
7. Pieces remain normal persistent Hideout Furniture objects.
8. Existing HF placement/collision/persistence functionality should be reused wherever possible.

DO NOT attempt dynamic NPC navigation/navmesh in the initial implementation.

DO NOT implement settlement simulation initially.

DO NOT rewrite the HF placement engine.

The first milestone should be a functional grey-box structural building system.

============================================================
2. EXISTING SYSTEM
============================================================

The supplied ZONA source contains the relevant HF modules:

Gameplay Hideout Mod 00 Main
Gameplay Hideout Mod 001 Dependencies
Gameplay Hideout Mod 004 Homestead Module
Gameplay Hideout Mod 005 Expanded Furniture
Gameplay Hideout Mod 006 Even More Expanded Furniture

Study these before making architectural changes.

HF already appears to provide:

- camera/ray based placement
- surface position detection
- surface normal detection
- quaternion rotations
- arbitrary object rotation
- per-object bounding boxes
- transformed bounding boxes
- placement collision checking
- visual placement preview
- object creation
- persistent furniture/object management
- pickup/removal
- object metadata
- furniture type registration
- post-placement callbacks

Relevant scripts discovered during initial investigation include:

placeable_furniture.script
hf_obj_manager.script
hf_furniture_types.script

There are also supporting geometry/rotation systems such as:

demonized_geometry_ray
aol_rotation

Verify exact names/APIs from source before relying on them.

IMPORTANT:
Treat the existing HF implementation as authoritative.
Do not duplicate functionality already available there.

============================================================
3. EXISTING HF PLACEMENT FLOW
============================================================

The current placement system approximately performs:

camera ray
    |
    v
surface position + surface normal
    |
    v
calculate object rotation/quaternion
    |
    v
transform bounding box
    |
    v
collision validation
    |
    v
placement preview
    |
    v
create object
    |
    v
HF object manager / persistence
    |
    v
placement callback

Relevant code observed includes behavior conceptually similar to:

local v = demonized_geometry_ray.get_surface_normal(cam_pos, cam_dir)

local q0 = aol_rotation.get_rotation_between(u, v)

bbox.rotation = q
bbox:SetWorldOrigin(pos)
bbox:UpdateBBox()
bbox:CheckForCollisions()

Do NOT replace this pipeline.

Instead, insert structural snapping between HF calculating a candidate
transform and HF validating/finalizing placement.

Conceptually:

HF candidate transform
        |
        v
is structural piece?
      /   \
    no     yes
    |       |
 normal     search structural sockets
 HF         |
 flow       v
        compatible socket nearby?
             /       \
           no         yes
           |           |
        normal      replace candidate
        HF          transform with
        transform   snapped transform
                         |
                         v
                  HF collision check
                         |
                         v
                     placement

============================================================
4. EXTENSION MECHANISM
============================================================

HF has a placeable_type/furniture-type extension mechanism.

Existing behavior appears conceptually similar to:

local placeable_type =
    ini_sys:r_string_ex(placeable_section, "placeable_type")
    or "prop"

local type_functor =
    hf_furniture_types.get_func(placeable_type)

Existing registrations include things conceptually similar to:

add_type("light", init_light)
add_type("stash", init_stash)

Investigate whether our system can cleanly register:

add_type("building_piece", init_building_piece)

Prefer this over modifying every HF prop or hard-coding section names.

Potential config:

[bb_wall_wood]:physic_object

visual = dynamics\base_building\wall_wood.ogf

placeable_type = building_piece

bb_piece_type = wall
bb_piece_size = 1,1,1
bb_socket_profile = wall_standard

bounding_box_size = ...
bounding_box_origin = ...

Exact config syntax should be designed after inspecting how HF reads
custom config values.

============================================================
5. CORE ARCHITECTURE
============================================================

Create a small independent module namespace.

Suggested files:

scripts/
    bb_core.script
    bb_registry.script
    bb_piece.script
    bb_socket.script
    bb_snap.script
    bb_structure.script
    bb_debug.script

configs/
    base_building/
        pieces.ltx
        sockets.ltx

Do not prematurely split files if X-Ray/Anomaly scripting conventions
make a smaller number of scripts preferable.

Responsibilities:

bb_core
    initialization and HF integration

bb_registry
    definition/lookup of structural piece types

bb_piece
    runtime representation of a structural object

bb_socket
    socket definitions and compatibility

bb_snap
    candidate search and snap transform calculations

bb_structure
    optional building/group metadata and structural relationships

bb_debug
    visualization/logging/debug commands

============================================================
6. STRUCTURAL PIECE MODEL
============================================================

A structural piece should conceptually contain:

BuildingPiece {
    object_id
    section
    type

    world_position
    world_rotation

    structure_id

    grid_x
    grid_y
    grid_z

    orientation

    sockets[]
}

Possible piece types:

FOUNDATION
FLOOR
WALL
WALL_DOOR
WALL_WINDOW
ROOF_FLAT
ROOF_SLOPE
PILLAR
STAIRS

Do not implement all initially.

MVP:

FOUNDATION
WALL
ROOF_FLAT

Then:

FLOOR
WALL_DOOR

============================================================
7. BUILDING COORDINATE SYSTEM
============================================================

DO NOT create a global map grid.

Each independent structure has its own local coordinate system.

The first foundation establishes:

structure.origin
structure.rotation
structure.cell_size

For example:

cell_size = 2.5 meters

Local integer coordinates:

(-1,1) (0,1) (1,1)
(-1,0) (0,0) (1,0)
(-1,-1)(0,-1)(1,-1)

World position should be derived approximately as:

world =
    structure.origin
    + structure.rotation * (grid_coordinate * cell_size)

Use the actual vector/quaternion helpers available in HF/X-Ray.

Avoid manually implementing quaternion mathematics if HF already
provides suitable helpers.

IMPORTANT:
The initial foundation is FREE-PLACED using normal HF placement.

Its final position and orientation establish the structure transform.

Subsequent pieces snap relative to existing structural pieces.

============================================================
8. SOCKET SYSTEM
============================================================

Prefer sockets over directly reasoning about grid neighbors.

A foundation could expose:

NORTH
SOUTH
EAST
WEST

and possibly:

TOP

A wall could expose:

LEFT
RIGHT
TOP
BOTTOM

A roof/floor could expose:

NORTH
SOUTH
EAST
WEST
BOTTOM

A socket contains approximately:

Socket {
    owner_piece_id

    local_position
    local_rotation

    socket_type
    accepts[]

    occupied
}

Example:

foundation.edge_north
    accepts = foundation_edge, wall_bottom

wall.bottom
    accepts = foundation_edge, floor_edge

wall.top
    accepts = roof_edge, wall_bottom

Compatibility must be explicit.

Do not simply snap any socket to any socket.

============================================================
9. WHY SOCKETS
============================================================

The system should eventually support differently shaped assets.

For example:

standard wall
doorway wall
window wall
half wall
metal wall
wood wall

They can share identical socket layouts.

The placement system therefore does not care about visual appearance.

wall_wood
wall_metal
wall_door_wood
wall_door_metal

can all expose:

LEFT
RIGHT
TOP
BOTTOM

This keeps gameplay topology separate from meshes.

============================================================
10. SNAP SEARCH
============================================================

Initial implementation can be deliberately simple.

When placing a building piece:

1. Obtain HF's candidate placement transform.
2. Search nearby registered structural objects.
3. Generate their available sockets.
4. Filter sockets by compatibility with the currently held piece.
5. Calculate distance between candidate placement and each valid socket.
6. Select nearest compatible socket within SNAP_RADIUS.
7. Calculate required world transform.
8. Feed snapped transform back into HF.
9. Allow HF bounding-box collision validation to run normally.
10. Render placement preview using the resulting transform.

Initial SNAP_RADIUS can be approximately:

0.5 - 1.0 meters

Make configurable.

============================================================
11. PERFORMANCE
============================================================

DO NOT prematurely implement spatial partitioning.

Base sizes will initially be small.

A linear search through structural pieces belonging to the nearby
structure is acceptable for MVP.

However:

Do NOT search every HF object globally if avoidable.

Maintain a registry such as:

structures[structure_id].pieces

If profiling eventually shows problems, introduce spatial hashing:

grid[cell_x][cell_y][cell_z]

later.

============================================================
12. FOUNDATION PLACEMENT
============================================================

The first foundation:

- uses standard HF free placement
- aligns to terrain using existing HF logic
- player selects desired rotation
- HF performs collision validation
- after confirmation:
    - generate structure_id
    - save origin
    - save orientation
    - register foundation at grid (0,0,0)

Additional foundations:

- detect compatible edge sockets
- snap to adjacent cells
- inherit structure_id
- calculate deterministic world position from structure transform

IMPORTANT DESIGN RULE:

Only the initial foundation follows terrain.

Once a structure exists:

STRUCTURE GEOMETRY TAKES PRIORITY OVER TERRAIN.

Do not individually conform adjacent foundations to terrain.

This guarantees planar construction.

============================================================
13. WALL PLACEMENT
============================================================

Walls attach to foundation/floor edge sockets.

Example:

+-------+
| FLOOR |
+-------+
    ^
north socket

When a wall is being positioned near that socket:

candidate wall
      |
      v
nearest compatible floor edge
      |
      v
wall.bottom -> floor.north
      |
      v
calculate wall position
      |
      v
calculate wall rotation
      |
      v
HF collision validation

Orientation must be deterministic.

Be careful about quaternion direction / 180-degree inversions.

Implement debug visualization/logging before trying to solve orientation
problems by trial-and-error.

============================================================
14. ROOF PLACEMENT
============================================================

For MVP, ONLY SUPPORT FLAT ROOFS.

Treat a flat roof similarly to a floor/ceiling tile.

Possible initial rule:

roof can attach to:

wall.top

or alternatively:

floor/structure cell at level +1

Do not implement sloped roofs initially.

Sloped roofs introduce:

pitch
ridge sockets
corner pieces
orientation variants
gable geometry

These belong to a later milestone.

============================================================
15. COLLISION
============================================================

Reuse HF collision validation.

Do NOT write a second collision engine.

Once bb_snap calculates:

position
rotation

apply them to HF's existing bounding box and allow:

bbox.rotation = ...
bbox:SetWorldOrigin(...)
bbox:UpdateBBox()
bbox:CheckForCollisions()

or whatever exact current implementation requires.

There may be an issue where connected pieces' bounding boxes touch
and HF considers them colliding.

If so:

FIRST determine whether touching boundaries are accepted.

If not, solve with one of:

- slightly inset bounding boxes
- structural neighbor collision exceptions
- tiny socket offsets

Prefer asset/config bounding-box adjustments over invasive changes
to HF collision code.

============================================================
16. PERSISTENCE
============================================================

DO NOT implement a parallel save system unless necessary.

Investigate hf_obj_manager first.

Determine how custom per-object data is persisted.

Need to store at minimum:

structure_id
piece_type
grid coordinate
orientation

Potential representation:

hf_data.bb = {
    structure_id = "...",
    piece_type = "wall",
    gx = 2,
    gy = 1,
    gz = 0,
    orientation = 1
}

Use existing HF serialization facilities if they support arbitrary
custom fields.

If arbitrary nested data cannot be serialized, store compact primitive
values in the mechanism HF already uses.

On game load:

1. HF restores physical furniture objects.
2. bb_core reconstructs structural registry from persistent metadata.
3. sockets are regenerated from piece definition + transform.

DO NOT persist sockets individually unless necessary.

Sockets should preferably be deterministic derived data.

============================================================
17. DELETION / PICKUP
============================================================

Reuse HF pickup/removal.

Hook the appropriate object removal callback.

When structural object disappears:

1. unregister piece
2. release occupied sockets
3. update structure
4. delete empty structure if no pieces remain

MVP does NOT need structural collapse.

Example:

removing foundation underneath wall

should NOT initially destroy wall.

Later versions may implement support rules.

============================================================
18. STRUCTURAL SUPPORT
============================================================

NOT MVP.

Eventually possible:

foundation = root support

floor:
    requires adjacent supported floor
    OR foundation underneath

wall:
    requires floor/foundation below

roof:
    requires wall/floor support

This can be represented as a graph.

DO NOT implement physics-based structural simulation.

If support mechanics are added, use discrete graph traversal.

============================================================
19. EXISTING EMHF ASSETS
============================================================

The supplied EMHF package already contains useful structural objects.

Observed meshes include:

wall.ogf
wall_metal.ogf
wall02.ogf
wall02_metal.ogf

wall_doorway.ogf
wall_doorway_metal.ogf

door_wood_100x190.ogf
door_wood_115x215.ogf
door_wood_145x220.ogf
door_metal_150x250.ogf
door_old_176x300.ogf

Observed wall dimensions/descriptions include approximately:

5 x 3 m wood wall
5 x 3 m metal wall

2 x 3 m wood wall
2 x 3 m metal wall

5 x 3 m doorway wall
5 x 3 m metal doorway wall

Existing configs use HF bounding boxes, e.g. conceptually:

bounding_box_size = ...
bounding_box_origin = ...

Inspect actual configuration.

DO NOT modify original EMHF assets/configs for the first prototype.

Create new bb_* sections inheriting or referencing them where possible.

============================================================
20. ASSET STRATEGY
============================================================

Programming should initially use GREYBOX / EXISTING meshes.

Do not block development on final artwork.

Required prototype pieces:

foundation
wall
flat roof

If necessary, temporarily reuse visually incorrect meshes.

The goal is to prove:

foundation placement
    ->
adjacent snap
    ->
wall snap
    ->
roof snap
    ->
save
    ->
reload
    ->
pickup/remove

Only after this works should final modular assets be produced.

Eventually standardize an asset unit.

Possible:

5m horizontal module
3m vertical module

This may be preferable because EMHF already contains 5x3m walls.

Investigate actual mesh dimensions before choosing 2.5m or 5m.

DO NOT hard-code 2.5m simply because it appeared in early design
discussion.

Choose dimensions based on existing usable assets.

============================================================
21. IMPORTANT DESIGN CHANGE FROM EARLY DISCUSSION
============================================================

Earlier discussion assumed a 2.5m grid.

After inspecting EMHF, DO NOT consider that decided.

Existing EMHF walls appear to use dimensions such as:

5x3m
2x3m

Therefore investigate whether the natural building module should be:

horizontal unit = 1m
major floor module = 5m
vertical level = 3m

or another compatible system.

The grid coordinate system and socket system should NOT require all
meshes to occupy exactly one grid cell.

A piece may occupy:

5 x 1 x 3

while another occupies:

2 x 1 x 3

depending on chosen logical unit.

Sockets are therefore more important than assuming every piece is 1x1.

============================================================
22. DOORS
============================================================

Treat doorway wall and door as separate concepts.

Structural system owns:

wall_doorway

HF / existing door implementation owns:

interactive door

Do NOT initially integrate door animation/interaction into structural
code.

First milestone can place doorway wall only.

Later:

wall_doorway
      +
compatible HF door object

Potentially automatically spawn or snap door to doorway socket.

============================================================
23. HOMESTEAD INTEGRATION
============================================================

NOT MVP.

Once structural construction is stable:

investigate Homestead's workbench/settlement boundary.

Possible integration:

Base Core / Homestead Workbench
       |
       +-- structure origin
       +-- building radius
       +-- Homestead settlement
       +-- construction management

But structural building should NOT require Homestead.

Architecture should be:

Hideout Furniture
        |
 Base Building
        |
   optional
 Homestead integration

not:

Homestead
   |
Base Building

============================================================
24. CUSTOM BASE SAFE HAVENS
============================================================

NOT MVP.

Potential later integration:

placing a Base Core could optionally establish:

- structural building origin
- Safe Haven area
- PDA marker
- save-enabled zone

Do not make this dependency mandatory.

============================================================
25. NPC NAVIGATION
============================================================

OUT OF SCOPE.

Do not attempt:

dynamic navmesh
dynamic smart terrain
AI understanding custom stairs
AI room navigation

NPCs may collide with structural geometry normally.

Homestead NPC behavior can remain independent of the constructed
interior.

============================================================
26. DEBUGGING REQUIREMENTS
============================================================

Building systems are extremely difficult to debug without visualization.

Implement bb_debug early.

At minimum provide logging for:

current piece type
candidate position
candidate rotation
nearest structural piece
nearest socket
socket type
socket distance
snap accepted/rejected
structure_id
grid coordinate

If possible, expose debug visualization for sockets.

Example:

          X roof socket
          |
     +----X----+
     |         |
  X--|  WALL   |--X
     |         |
     +----X----+
          |
          X bottom socket

If drawing debug geometry is difficult in X-Ray, temporary visible
HF objects or verbose logging are acceptable.

============================================================
27. FIRST DEVELOPMENT MILESTONE
============================================================

DO NOT start by building the full architecture.

Build the smallest possible vertical slice.

MILESTONE 0:

A. Create one custom structural wall section.

B. Register it as building_piece.

C. Confirm it still behaves exactly like normal HF furniture.

D. Add one hard-coded socket to it.

E. While placing a second copy:
   - detect first wall
   - detect socket
   - snap second wall next to first

F. Confirm HF collision preview still works.

G. Save game.

H. Reload game.

I. Confirm first wall can still be found as a structural piece.

J. Snap a third wall to the reloaded structure.

THIS IS THE FIRST PROOF OF CONCEPT.

Do not build foundations before this works.

============================================================
28. SECOND MILESTONE
============================================================

Create foundation prototype.

Requirements:

- first foundation free placement
- structure_id creation
- origin/orientation creation
- four edge sockets
- second foundation snaps to first
- third foundation snaps to either
- duplicate occupancy rejected

Test:

[F]

then:

[F][F]

then:

[F][F]
[F][F]

Then test after save/reload.

============================================================
29. THIRD MILESTONE
============================================================

Wall support.

Foundation exposes wall sockets.

Result:

W---W
|   |
| F |
|   |
W---W

Player should be able to select wall and snap it to any free foundation
edge.

Verify all four rotations.

============================================================
30. FOURTH MILESTONE
============================================================

Flat roof.

Build:

       ROOF
    +-------+
    |       |
    +-------+
    | WALL  |
    |       |
    +-------+
    | FOUND |
    +-------+

At this point the project has proven actual enclosed building
construction.

Only now begin improving UX/assets.

============================================================
31. TEST MATRIX
============================================================

For every structural type test:

PLACE
- free placement where applicable
- valid snap
- invalid snap
- occupied socket
- collision
- rotation

REMOVE
- remove last placed
- remove middle piece
- replace removed piece

SAVE
- save
- quit
- reload
- add piece to existing structure

LEVEL
- leave map
- return
- verify registry reconstruction

MULTIPLE STRUCTURES
- build structure A
- move away
- build structure B
- ensure sockets never cross structure incorrectly

TERRAIN
- flat terrain
- mild slope
- large slope
- near existing world geometry

============================================================
32. CODING RULES
============================================================

1. Read existing HF code before implementing equivalent behavior.

2. Prefer extension/hooks over editing HF source.

3. Keep Base Building installable as a separate addon.

4. Prefix global/module/config identifiers with bb_ to avoid collisions.

5. Avoid monkey-patching HF unless no supported extension point exists.

6. If HF must be patched, isolate patch into one compatibility script.

7. Document every dependency on HF internals.

8. Do not optimize prematurely.

9. Do not implement NPC navigation.

10. Do not create final assets until snapping prototype works.

11. Do not assume early architectural guesses are correct:
    inspect the supplied code.

12. Preserve compatibility with normal HF furniture.

============================================================
33. SUCCESS CRITERIA FOR MVP
============================================================

The MVP is complete when a player can:

1. Craft/spawn a foundation.
2. Place it freely.
3. Snap additional foundations to it.
4. Snap walls to foundation edges.
5. Place a doorway wall.
6. Snap flat roof/floor pieces above walls.
7. Decorate the resulting building using ordinary HF furniture.
8. Remove individual structural pieces.
9. Save the game.
10. Reload.
11. Continue building from the existing structure.

No NPC support is required.

No structural collapse is required.

No sloped roofs are required.

No Homestead integration is required.

No Safe Haven integration is required.

============================================================
34. FIRST TASK FOR OPENCODE
============================================================

DO NOT immediately write implementation code.

First inspect the supplied Hideout Furniture source and produce:

1. exact placement call graph
2. exact object creation call
3. exact persistence mechanism
4. exact furniture-type registration API
5. exact placement-preview transform path
6. exact bounding-box collision path
7. available placement callbacks/hooks
8. removal/pickup callbacks
9. serialization limitations for custom metadata
10. safest injection point for snap transform

For each answer cite:

- filename
- function name
- relevant code

Then propose the MINIMAL patch/addon architecture needed to implement
Milestone 0:

"two structural walls snapping together."

Do not implement Milestone 1+ until Milestone 0 is working in-game.