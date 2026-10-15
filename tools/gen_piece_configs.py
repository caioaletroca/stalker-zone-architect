"""Generate the piece configs, workshop recipes and the English string table.

Outputs:
    gamedata/configs/mod_system_bb_pieces.ltx
    gamedata/configs/text/eng/st_bb_pieces.xml
    gamedata/configs/items/settings/mod_craft_bb_pieces.ltx          (GAMMA)
    optional/vanilla-anomaly-crafting/gamedata/.../mod_craft_bb_pieces.ltx

Run from anywhere: python tools/gen_piece_configs.py
"""

import os

root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BS = "\\"
pieces = [
    # key, piece_type, snap_class, profile, icon(x,y), bbox_size, bbox_origin, size
    ("foundation", "foundation", "foundation", "foundation_standard", (5, 15), "2.44, 2.44, 0.16", "0.0, 0.1, 0.0", "2.5, 0.2, 2.5"),
    ("wall", "wall", "wall", "wall_standard", (11, 15), "2.44, 0.16, 2.94", "0.0, 1.5, 0.0", "2.5, 3.0, 0.2"),
    ("wall_doorway", "wall_door", "wall", "wall_standard", (8, 15), "2.44, 0.16, 2.94", "0.0, 1.5, 0.0", "2.5, 3.0, 0.2"),
    ("roof_flat", "roof_flat", "roof_flat", "roof_flat_standard", (5, 16), "2.44, 2.44, 0.16", "0.0, 0.1, 0.0", "2.5, 0.2, 2.5"),
]

HEADER = """; Base Building greybox pieces.
;
; Each piece is an inventory item (bb_item_*) that HF turns into a placed
; physic object (bb_*). Meshes come from tools/blender/build_greybox.py.
;
; bounding_box_size   = HF order: width (x), length (z), height (y).
;                       Inset 6cm so neighbouring pieces do not touch.
; bounding_box_origin = x, y, z centre of that box relative to the origin.
; bb_piece_size       = x, y, z extents (documentation / future use).
; bb_snap_class       = pieces with the same class share slots/occupancy.
; bb_socket_profile   = socket layout in bb_socket.script.
"""

TEMPLATE = """
[bb_item_{key}]:tch_junk
class                                   = II_ATTCH
kind                                    = i_tool
visual                                  = base_building{bs}bb_{key}.ogf

description                             = st_bb_{key}_descr
inv_name                                = st_bb_{key}
inv_name_short                          = st_bb_{key}

; Borrow EMHF decor icon sheet for the greybox stage
icons_texture                           = ui{bs}ui_decor
inv_grid_x                              = {ix}
inv_grid_y                              = {iy}
inv_grid_width                          = 3
inv_grid_height                         = 1

cost                                    = 100
inv_weight                              = 5

use1_functor                            = placeable_furniture.place_item
use1_action_functor                     = placeable_furniture.func_place_item

placeable_type                          = building_piece
placeable_section                       = bb_{key}

[bb_{key}]:physic_object
visual                                  = base_building{bs}bb_{key}.ogf
placeable_type                          = building_piece
base_rotation                           = 0

; HF's binder plus a spawn step that drops the engine's quantised physics
; snapshot (bb_binder / bb_physics)
script_binding                          = bb_binder.init
item_section                            = bb_item_{key}

; Anchor the root bone to the world so the physics engine never moves a
; placed piece (touching neighbours would otherwise push each other apart)
fixed_bones                             = link

bounding_box_size                       = {bsz}
bounding_box_origin                     = {borg}

bb_piece_type                           = {ptype}
bb_snap_class                           = {sclass}
bb_piece_size                           = {size}
bb_socket_profile                       = {prof}
"""

out = [HEADER]
for key, ptype, sclass, prof, (ix, iy), bsz, borg, size in pieces:
    out.append(TEMPLATE.format(key=key, bs=BS, ix=ix, iy=iy, bsz=bsz, borg=borg,
                               ptype=ptype, sclass=sclass, size=size, prof=prof))
with open(os.path.join(root, "gamedata/configs/mod_system_bb_pieces.ltx"), "w", newline="\r\n") as f:
    f.write("".join(out))

names = {
    "foundation": ("Foundation (Prototype)", "Greybox structural foundation, 2.5 x 2.5 m. Place it freely; further foundations snap to its edges."),
    "wall": ("Wall (Prototype)", "Greybox structural wall, 2.5 m wide and 3 m tall. Snaps to foundation and roof edges and to other walls."),
    "wall_doorway": ("Doorway Wall (Prototype)", "Greybox wall with a 1.2 x 2.2 m opening. Snaps like a regular wall."),
    "roof_flat": ("Flat Roof (Prototype)", "Greybox flat roof / ceiling panel, 2.5 x 2.5 m. Snaps to wall tops and to other roof panels."),
}
x = ['<?xml version="1.0" encoding="windows-1251"?>', '<string_table>']
for k, (n, d) in names.items():
    x += ['', '\t<string id="st_bb_%s">' % k, '\t\t<text>%s</text>' % n, '\t</string>',
          '\t<string id="st_bb_%s_descr">' % k, '\t\t<text>%s</text>' % d, '\t</string>']
x += ['', '</string_table>', '']
with open(os.path.join(root, "gamedata/configs/text/eng/st_bb_pieces.xml"), "w", newline="\r\n", encoding="cp1251") as f:
    f.write("\n".join(x))

# ---------------------------------------------------------------------------
# Workshop recipes (craft first, then place, like the rest of HF/EMHF)
#
# craft.ltx line format:
#   x_<item_section> = <tool tier>, <recipe unlock>, part, count, part, count...
# Tool tier 1 = basic toolkit; recipe_basic_0 = known by default.
# Costs are scaled from EMHF's walls (5 m wood wall: 15 wood + 5 fasteners).
#
# Each tileset ships its own recipes in the native format, so a metal
# tileset simply lists metal parts for its own item sections.
# ---------------------------------------------------------------------------
RECIPES = [
    # key, tool tier, unlock, [(part, count), ...]
    ("foundation",   1, "recipe_basic_0", [("prt_i_wood", 8), ("prt_i_scrap", 4), ("prt_i_fasteners", 4)]),
    ("wall",         1, "recipe_basic_0", [("prt_i_wood", 8), ("prt_i_fasteners", 3)]),
    ("wall_doorway", 1, "recipe_basic_0", [("prt_i_wood", 7), ("prt_i_fasteners", 3)]),
    ("roof_flat",    1, "recipe_basic_0", [("prt_i_wood", 6), ("prt_i_scrap", 2), ("prt_i_fasteners", 3)]),
]

# Workshop tab per game: GAMMA's craft.ltx has a Furniture tab ([8]) holding
# HF/EMHF items; vanilla Anomaly has none, so EMHF uses Equipment ([2]).
CRAFT_TARGETS = [
    ("gamedata", "8", "G.A.M.M.A. (Furniture tab)"),
    ("optional/vanilla-anomaly-crafting/gamedata", "2", "vanilla Anomaly (Equipment tab)"),
]

for base, tab, label in CRAFT_TARGETS:
    lines = [
        "; Base Building workshop recipes for %s." % label,
        "; Generated by tools/gen_piece_configs.py - edit the RECIPES table there.",
        "![%s]" % tab,
    ]
    for key, tier, unlock, parts in RECIPES:
        cost = ",".join("%s,%d" % (part, count) for part, count in parts)
        lines.append("x_bb_item_%s = %d, %s, %s" % (key, tier, unlock, cost))
    path = os.path.join(root, base, "configs/items/settings/mod_craft_bb_pieces.ltx")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="\r\n") as f:
        f.write("\n".join(lines) + "\n")
