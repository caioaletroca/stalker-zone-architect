"""Dump the top-level chunk structure and header of an .ogf file.

Used to compare our exported greybox meshes against known-good EMHF assets.
"""

import struct
import sys

CHUNK_NAMES_V4 = {
    1: "HEADER",
    2: "TEXTURE",
    3: "VERTICES",
    4: "INDICES",
    6: "SWIDATA",
    7: "VCONTAINER",
    8: "ICONTAINER",
    9: "CHILDREN",
    10: "CHILDREN_L",
    11: "LODDEF2",
    12: "TREEDEF2",
    13: "S_BONE_NAMES",
    14: "S_MOTIONS_2",
    15: "S_SMPARAMS_1",
    16: "S_IKDATA_2",
    17: "S_USERDATA",
    18: "S_DESC",
    19: "S_MOTION_REFS_0",
    20: "SWICONTAINER",
    21: "GCONTAINER",
    22: "FASTPATH",
    23: "S_LODS",
    24: "S_MOTION_REFS_2",
}

MODEL_TYPES = {
    0x0: "NORMAL",
    0x1: "HIERRARHY",
    0x2: "PROGRESSIVE",
    0x3: "SKELETON_ANIM",
    0x4: "SKELETON_GEOMDEF_PM",
    0x5: "SKELETON_GEOMDEF_ST",
    0x6: "LOD",
    0x7: "TREE_ST",
    0x8: "PARTICLE_EFFECT",
    0x9: "PARTICLE_GROUP",
    0xA: "SKELETON_RIGID",
    0xB: "TREE_PM",
}


def read_chunks(data):
    chunks = []
    offset = 0
    while offset + 8 <= len(data):
        chunk_id, size = struct.unpack_from("<II", data, offset)
        body = data[offset + 8:offset + 8 + size]
        chunks.append((chunk_id, size, body))
        offset += 8 + size
    return chunks


def describe(path):
    with open(path, "rb") as handle:
        data = handle.read()

    print("=== {} ({} bytes) ===".format(path, len(data)))
    for chunk_id, size, body in read_chunks(data):
        masked = chunk_id & 0x7FFFFFFF
        name = CHUNK_NAMES_V4.get(masked, "?")
        print("  chunk {:>5} ({:<16}) size={}".format(masked, name, size))

        if masked == 1 and len(body) >= 4:
            version, model_type, shader_id = struct.unpack_from("<BBH", body, 0)
            print("      version      = {}".format(version))
            print("      model_type   = {} ({})".format(
                model_type, MODEL_TYPES.get(model_type, "?")
            ))
            print("      shader_id    = {}".format(shader_id))
            if len(body) >= 4 + 24:
                bb = struct.unpack_from("<6f", body, 4)
                print("      bbox_min     = ({:.3f}, {:.3f}, {:.3f})".format(*bb[0:3]))
                print("      bbox_max     = ({:.3f}, {:.3f}, {:.3f})".format(*bb[3:6]))
            if len(body) >= 4 + 24 + 16:
                bs = struct.unpack_from("<4f", body, 28)
                print("      bsphere_c    = ({:.3f}, {:.3f}, {:.3f})".format(*bs[0:3]))
                print("      bsphere_r    = {:.3f}".format(bs[3]))

        elif masked == 2:
            texts = body.split(b"\x00")
            print("      texture      = {!r}".format(texts[0].decode("latin-1")))
            if len(texts) > 1:
                print("      shader       = {!r}".format(texts[1].decode("latin-1")))


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        describe(arg)
        print()
