"""Generate solid-colour DXT1 .dds textures for the base-building greybox pieces.

Solid colours compress trivially: every 4x4 block stores the same colour twice
with an all-zero index table, so no real DXT encoder is required.

No .thm files are produced. An earlier revision emitted hand-reconstructed
descriptors, which crashed the engine at startup:

    Expression : F->find_chunk(THM_CHUNK_TYPE)
    Function   : CTextureDescrMngr::LoadTHM

The engine parses every .thm under gamedata/textures/ during boot and asserts
on a malformed descriptor chunk. Anomaly loads a bare .dds without one, which
is all these greybox prototypes need. If .thm files become necessary, generate
them with the X-Ray SDK instead of by hand.
"""

import argparse
import os
import struct

DDSD_CAPS = 0x1
DDSD_HEIGHT = 0x2
DDSD_WIDTH = 0x4
DDSD_PIXELFORMAT = 0x1000
DDSD_MIPMAPCOUNT = 0x20000
DDSD_LINEARSIZE = 0x80000

DDPF_FOURCC = 0x4

DDSCAPS_TEXTURE = 0x1000
DDSCAPS_MIPMAP = 0x400000
DDSCAPS_COMPLEX = 0x8

PIECES = {
    "bb_foundation": (26, 140, 38),
    "bb_wall": (26, 77, 179),
    "bb_roof_flat": (166, 31, 31),
}


def rgb565(r, g, b):
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)


def dxt1_block(colour):
    """A 4x4 DXT1 block filled with a single colour."""
    c = rgb565(*colour)
    return struct.pack("<HHI", c, c, 0)


def mip_sizes(width, height):
    sizes = []
    while width >= 1 and height >= 1:
        sizes.append((width, height))
        if width == 1 and height == 1:
            break
        width = max(1, width // 2)
        height = max(1, height // 2)
    return sizes


def build_dds(colour, width=64, height=64):
    levels = mip_sizes(width, height)
    blocks_w = max(1, (width + 3) // 4)
    blocks_h = max(1, (height + 3) // 4)
    linear_size = blocks_w * blocks_h * 8

    flags = (
        DDSD_CAPS
        | DDSD_HEIGHT
        | DDSD_WIDTH
        | DDSD_PIXELFORMAT
        | DDSD_MIPMAPCOUNT
        | DDSD_LINEARSIZE
    )
    caps = DDSCAPS_TEXTURE | DDSCAPS_MIPMAP | DDSCAPS_COMPLEX

    header = bytearray()
    header += b"DDS "
    header += struct.pack("<I", 124)
    header += struct.pack("<I", flags)
    header += struct.pack("<I", height)
    header += struct.pack("<I", width)
    header += struct.pack("<I", linear_size)
    header += struct.pack("<I", 0)
    header += struct.pack("<I", len(levels))
    header += b"\x00" * 44
    header += struct.pack("<I", 32)
    header += struct.pack("<I", DDPF_FOURCC)
    header += b"DXT1"
    header += struct.pack("<IIIII", 0, 0, 0, 0, 0)
    header += struct.pack("<I", caps)
    header += struct.pack("<IIII", 0, 0, 0, 0)

    assert len(header) == 128, len(header)

    body = bytearray()
    block = dxt1_block(colour)
    for lw, lh in levels:
        bw = max(1, (lw + 3) // 4)
        bh = max(1, (lh + 3) // 4)
        body += block * (bw * bh)

    return bytes(header) + bytes(body)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        default=os.path.join("gamedata", "textures", "base_building"),
        help="output directory for .dds files",
    )
    parser.add_argument("--size", type=int, default=64)
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    for name, colour in PIECES.items():
        dds_path = os.path.join(args.out, name + ".dds")

        with open(dds_path, "wb") as handle:
            handle.write(build_dds(colour, args.size, args.size))

        print("wrote {} ({} bytes)".format(dds_path, os.path.getsize(dds_path)))


if __name__ == "__main__":
    main()
