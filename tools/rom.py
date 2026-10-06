#!/usr/bin/env python3
"""
Identify and prepare a Majora's Mask ROM for building Majora City.

    python3 tools/rom.py identify <rom>             explain what this file is and whether it can be used
    python3 tools/rom.py prepare <rom> <out.z64>    write a clean big-endian copy for the build; prints its MD5

<rom> may be a .z64, .n64 or .v64 dump, or a .zip containing one. Exit status: 0 usable, 2 not usable, 1 error.
Only the Python standard library is used.
"""

import hashlib
import os
import sys
import tempfile
import zipfile

# The N64 cartridge, as dumped. Same value as the decomp's baseroms/n64-us/checksum-compressed.md5.
USA_MD5 = "2a0a8acb61538235bc1094d297fb6556"

KNOWN_MD5 = {
    USA_MD5: "usable",
    # The decomp's decompressed US ROM: what some tools produce from the cartridge dump.
    "f46493eaa0628827dbd6ad3ecd8d65d6": "decompressed",
    # Japanese 1.1 (decomp baseroms/n64-jp-1.1)
    "c38a7f6f6b61862ea383a75cdf888279": "japan",
    "2052c9070d3101fc0a73daf48c834d16": "japan",
}

ROM_EXTENSIONS = (".z64", ".n64", ".v64")
N64_MAGIC = {
    b"\x80\x37\x12\x40": "z64",
    b"\x37\x80\x40\x12": "v64",
    b"\x40\x12\x37\x80": "n64",
}


class RomError(Exception):
    """A problem the user can fix (wrong file, wrong version...)."""


def to_z64(data):
    kind = N64_MAGIC.get(bytes(data[:4]))
    if kind == "v64":
        b = bytearray(data)
        b[0::2], b[1::2] = data[1::2], data[0::2]
        return bytes(b)
    if kind == "n64":
        b = bytearray(data)
        b[0::4], b[1::4], b[2::4], b[3::4] = data[3::4], data[2::4], data[1::4], data[0::4]
        return bytes(b)
    return bytes(data)


def read_rom(path):
    """Read a ROM file, or the ROM inside a .zip. Returns (bytes, description of where it came from)."""
    if not os.path.isfile(path):
        raise RomError("File not found: %s" % path)
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist() if n.lower().endswith(ROM_EXTENSIONS)]
            if not names:
                raise RomError("%s is a .zip, but there is no .z64/.n64/.v64 file inside it." % os.path.basename(path))
            if len(names) > 1:
                raise RomError(
                    "%s contains several ROMs (%s). Unzip it and pick the Majora's Mask (USA) one."
                    % (os.path.basename(path), ", ".join(names))
                )
            return z.read(names[0]), "%s (inside %s)" % (names[0], os.path.basename(path))
    with open(path, "rb") as f:
        return f.read(), os.path.basename(path)


def accepted_md5s():
    extra = os.environ.get("MC_TEST_ACCEPT_MD5", "")  # automated tests only (tools/test_cli.sh)
    return {USA_MD5} | {m.strip().lower() for m in extra.split(",") if m.strip()}


def identify(data):
    """Returns (usable, message, z64_bytes, md5)."""
    if bytes(data[:4]) not in N64_MAGIC:
        return False, "This doesn't look like an N64 ROM.", None, None

    z64 = to_z64(data)
    md5 = hashlib.md5(z64).hexdigest()
    name = z64[0x20:0x34].decode("ascii", "replace").strip("\x00 ").strip()
    code = z64[0x3B:0x3F].decode("ascii", "replace")
    region = code[3:4]

    if md5 in accepted_md5s():
        return True, "The Legend of Zelda: Majora's Mask (USA). This is the right ROM.", z64, md5

    verdict = KNOWN_MD5.get(md5)
    is_mm = code[:3] == "NZS" or "MAJORA" in name.upper()
    if verdict == "decompressed":
        msg = (
            "This is the USA version, but it has been decompressed by another tool. Majora City patches are made "
            "against the original cartridge dump, so please use your original, untouched dump."
        )
    elif verdict == "japan" or (is_mm and region == "J"):
        msg = "This is the Japanese version of Majora's Mask. Majora City needs the USA version."
    elif is_mm and region == "P":
        msg = "This is the European version of Majora's Mask. Majora City needs the USA version."
    elif is_mm and region == "E":
        msg = (
            "This is a USA Majora's Mask ROM, but it isn't identical to the original cartridge. It may be modified "
            "(a randomizer or another hack, or a ROM that was already patched), a bad dump, or extracted from the "
            "GameCube or Virtual Console releases. Majora City needs a clean dump of the N64 cartridge."
        )
    elif is_mm:
        msg = "This is a version of Majora's Mask Majora City doesn't support (game code %s). Use the USA version." % code
    else:
        msg = "This isn't a Majora's Mask ROM (its internal name is '%s')." % (name or "unknown")

    msg += "\n  MD5 of this file: %s\n  MD5 needed:       %s" % (md5, USA_MD5)
    return False, msg, z64, md5


def write_atomic(path, data):
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".rom-")
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


def main(argv):
    if len(argv) < 3 or argv[1] not in ("identify", "prepare") or (argv[1] == "prepare" and len(argv) != 4):
        print(__doc__.strip(), file=sys.stderr)
        return 1
    try:
        data, where = read_rom(argv[2])
    except RomError as e:
        print(str(e), file=sys.stderr)
        return 2
    except (OSError, zipfile.BadZipFile) as e:
        print("Couldn't read %s: %s" % (argv[2], e), file=sys.stderr)
        return 1

    usable, message, z64, md5 = identify(data)
    if not usable:
        print("%s:\n  %s" % (where, message.replace("\n", "\n")), file=sys.stderr)
        return 2

    if argv[1] == "identify":
        print("%s: %s" % (where, message))
        return 0

    write_atomic(argv[3], z64)
    print(md5)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
