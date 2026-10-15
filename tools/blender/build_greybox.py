"""Build the base-building greybox pieces and export them as X-Ray OGF.

Run headless (no UI needed):

    blender -b --factory-startup -P tools/blender/build_greybox.py

Requires the blender-xray addon (io_scene_xray) installed for that Blender.

Outputs:
    assets/blender/bb_greybox.blend          editable source scene
    gamedata/meshes/base_building/<piece>.ogf

Why an armature?
    HF spawns every placeable as a `physic_object`. The engine builds the
    physics shell from the model's bones, so the OGF must be a skeleton
    (SKELETON_RIGID) with at least one bone carrying a collision shape.
    A plain static mesh (model_type NORMAL) cannot be used as a
    physic_object visual. EMHF's walls use the same layout: one armature
    root, a bone named "link" with a box shape, meshes weighted 100% to it.

Coordinates:
    Blender is Z-up, X-Ray is Y-up. The exporter maps
    blender (x, y, z) -> xray (x, z, y).
    So in Blender: X = width, Y = depth (X-Ray forward), Z = height.
    Every piece has its origin at the bottom centre.

Keep the dimensions below in sync with gamedata/scripts/bb_socket.script.
"""

import os
import sys

import addon_utils
import bmesh
import bpy
import mathutils

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MESH_DIR = os.path.join(ROOT, "gamedata", "meshes", "base_building")
BLEND_PATH = os.path.join(ROOT, "assets", "blender", "bb_greybox.blend")

# Shared module dimensions (metres)
CELL = 2.5          # foundation / roof footprint and wall width
WALL_H = 3.0        # wall height (one storey)
SLAB_T = 0.2        # foundation / roof thickness
WALL_T = 0.2        # wall thickness
DOOR_W = 1.2        # doorway opening width
DOOR_H = 2.2        # doorway opening height

HALF = CELL / 2.0

# Each part: (name, (min_x, min_y, min_z), (max_x, max_y, max_z)) in Blender coords.
# Every part gets its own bone + box collision shape.
PIECES = {
    "bb_foundation": {
        "color": (26, 140, 38),
        "parts": [("link", (-HALF, -HALF, 0.0), (HALF, HALF, SLAB_T))],
    },
    "bb_roof_flat": {
        "color": (166, 31, 31),
        "parts": [("link", (-HALF, -HALF, 0.0), (HALF, HALF, SLAB_T))],
    },
    "bb_wall": {
        "color": (26, 77, 179),
        "parts": [("link", (-HALF, -WALL_T / 2, 0.0), (HALF, WALL_T / 2, WALL_H))],
    },
    "bb_wall_doorway": {
        "color": (230, 150, 20),
        "parts": [
            ("link",  (-HALF, -WALL_T / 2, 0.0), (-DOOR_W / 2, WALL_T / 2, WALL_H)),
            ("right", (DOOR_W / 2, -WALL_T / 2, 0.0), (HALF, WALL_T / 2, WALL_H)),
            ("top",   (-DOOR_W / 2, -WALL_T / 2, DOOR_H), (DOOR_W / 2, WALL_T / 2, WALL_H)),
        ],
    },
}

MASS = 1000.0
# Physics boxes are shrunk by this much per side so touching neighbours
# never overlap (overlapping bodies get pushed apart by the physics engine)
PHYSICS_INSET = 0.005
GAMEMTL = "default_object"


def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ok, _ = addon_utils.check("io_scene_xray")
    if not ok:
        addon_utils.enable("io_scene_xray", default_set=True)
    ok, loaded = addon_utils.check("io_scene_xray")
    if not loaded:
        raise RuntimeError("blender-xray addon (io_scene_xray) is not installed")


def make_material(piece_name, rgb):
    tex_name = "base_building\\" + piece_name
    lin = [srgb_to_linear(c) for c in rgb] + [1.0]

    image = bpy.data.images.new(tex_name, 4, 4)
    image.generated_color = lin

    mat = bpy.data.materials.new(tex_name)
    mat.use_nodes = True
    mat.diffuse_color = lin
    nodes = mat.node_tree.nodes
    tex = nodes.new("ShaderNodeTexImage")
    tex.name = tex_name      # exporter uses the node name as texture path
    tex.label = tex_name
    tex.image = image
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nodes.active = tex

    mat.xray.eshader = "models\\model"
    mat.xray.cshader = "default"
    mat.xray.gamemtl = GAMEMTL
    return mat


def add_box(bm, vmin, vmax):
    center = [(a + b) / 2 for a, b in zip(vmin, vmax)]
    size = [b - a for a, b in zip(vmin, vmax)]
    mat = mathutils.Matrix.Translation(center) @ mathutils.Matrix.Diagonal(size + [1.0])
    bmesh.ops.create_cube(bm, size=1.0, matrix=mat, calc_uvs=True)


def build_piece(piece_name, spec, collection):
    # Armature (root object)
    arm_data = bpy.data.armatures.new(piece_name)
    arm_obj = bpy.data.objects.new(piece_name, arm_data)
    collection.objects.link(arm_obj)
    arm_obj.xray.isroot = True
    arm_obj.xray.flags = 1      # dynamic
    arm_obj.xray.export_path = "base_building"

    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    root_bone = None
    for bone_name, vmin, vmax in spec["parts"]:
        center = mathutils.Vector([(a + b) / 2 for a, b in zip(vmin, vmax)])
        eb = arm_data.edit_bones.new(bone_name)
        eb.head = center
        eb.tail = center + mathutils.Vector((0, 0, 0.1))
        if root_bone is None:
            root_bone = eb
        else:
            eb.parent = root_bone
    bpy.ops.object.mode_set(mode="POSE")

    # Bone physics: rigid joints, one box shape per part
    from io_scene_xray.ops.edit_helpers import bone_shape
    for bone_name, vmin, vmax in spec["parts"]:
        bone = arm_data.bones[bone_name]
        x = bone.xray
        x.gamemtl = GAMEMTL
        x.shape.type = "1"          # box
        x.ikjoint.type = "0"        # rigid
        x.mass.value = MASS / len(spec["parts"])
        center = [(a + b) / 2 for a, b in zip(vmin, vmax)]
        half = [(b - a) / 2 - PHYSICS_INSET for a, b in zip(vmin, vmax)]
        shape_matrix = mathutils.Matrix.Translation(center) @ mathutils.Matrix.Diagonal(half + [1.0])
        bone_shape.apply_shape(bone, shape_matrix)
    bpy.ops.object.mode_set(mode="OBJECT")

    # Mesh: one object per piece (exporter allows one material per object)
    mesh = bpy.data.meshes.new(piece_name + "_mesh")
    mesh_obj = bpy.data.objects.new(piece_name + "_mesh", mesh)
    collection.objects.link(mesh_obj)

    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")     # create_cube(calc_uvs) fills the active layer
    part_ranges = []
    for bone_name, vmin, vmax in spec["parts"]:
        start = len(bm.verts)
        add_box(bm, vmin, vmax)
        part_ranges.append((bone_name, start, len(bm.verts)))
    bm.to_mesh(mesh)
    bm.free()

    mesh.materials.append(make_material(piece_name, spec["color"]))
    for bone_name, start, end in part_ranges:
        vg = mesh_obj.vertex_groups.new(name=bone_name)
        vg.add(list(range(start, end)), 1.0, "REPLACE")

    mesh_obj.parent = arm_obj
    mod = mesh_obj.modifiers.new("Armature", "ARMATURE")
    mod.object = arm_obj
    return arm_obj


def export_piece(arm_obj):
    from io_scene_xray.formats.ogf.exp import main as ogf_main
    from io_scene_xray.formats.ogf.exp import ops as ogf_ops
    from io_scene_xray.utils import stats

    # export_file is normally wrapped by the operator, which sets this up
    stats.statistics = stats.Statistics()

    ctx = ogf_ops.ExportOgfContext()
    ctx.texname_from_path = False
    ctx.fmt_ver = "cscop"
    ctx.hq_export = False
    ctx.export_motions = False

    os.makedirs(MESH_DIR, exist_ok=True)
    path = os.path.join(MESH_DIR, arm_obj.name + ".ogf")
    ogf_main.export_file(arm_obj, path, ctx)
    print("exported", path)


def main():
    reset_scene()
    scene = bpy.context.scene
    collection = scene.collection

    roots = []
    offset = 0.0
    for piece_name, spec in PIECES.items():
        arm_obj = build_piece(piece_name, spec, collection)
        roots.append(arm_obj)

    # Export at the origin, then lay pieces out side by side for the .blend
    for arm_obj in roots:
        export_piece(arm_obj)
    for arm_obj in roots:
        arm_obj.location.x = offset
        offset += CELL + 1.0

    os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("saved", BLEND_PATH)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)
