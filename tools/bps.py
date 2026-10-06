#!/usr/bin/env python3
"""
BPS patch creator / applier for distributing Majora City.

We never distribute the game. Players apply a .bps patch to their own US 1.0 dump. This tool needs only the
Python standard library.

    python3 tools/bps.py create  <original.z64> <modified.z64> <out.bps> [--metadata TEXT]
    python3 tools/bps.py apply   <original.z64> <patch.bps> <out.z64>
    python3 tools/bps.py info    <patch.bps>
    python3 tools/bps.py selftest

Input ROMs in byte-swapped (.v64) or little-endian (.n64) order are converted to big-endian (.z64) first, so
a patch made from a .z64 applies to any dump of the same ROM.

The encoder is a greedy delta matcher: it emits SourceRead for bytes unchanged in place, SourceCopy for data
that moved (common in compressed ROMs, where one change shifts every later file), and TargetRead for new
bytes. Patches it makes apply with any BPS tool (Flips, beat, RomPatcher.js), and this applier reads patches
made by those tools.
"""

import argparse
import os
import random
import sys
import zlib

N64_MAGIC = {
    b"\x80\x37\x12\x40": "z64",
    b"\x37\x80\x40\x12": "v64",
    b"\x40\x12\x37\x80": "n64",
}

BLOCK = 32  # match granularity for the source index


def to_z64(data):
    """Return `data` in big-endian (.z64) byte order if it looks like an N64 ROM in another order."""
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


# --------------------------------------------------------------------------------------------------------------------
# Encoding helpers
# --------------------------------------------------------------------------------------------------------------------


def write_number(out, n):
    while True:
        x = n & 0x7F
        n >>= 7
        if n == 0:
            out.append(0x80 | x)
            return
        out.append(x)
        n -= 1


def read_number(data, pos):
    result, shift = 0, 1
    while True:
        x = data[pos]
        pos += 1
        result += (x & 0x7F) * shift
        if x & 0x80:
            return result, pos
        shift <<= 7
        result += shift


SOURCE_READ, TARGET_READ, SOURCE_COPY, TARGET_COPY = range(4)


def match_length(a, a_pos, b, b_pos, limit):
    """Length of the common prefix of a[a_pos:] and b[b_pos:], at most `limit`."""
    n, step = 0, 64
    while n < limit:
        k = min(step, limit - n)
        if a[a_pos + n : a_pos + n + k] == b[b_pos + n : b_pos + n + k]:
            n += k
            step = min(step * 2, 1 << 20)
            continue
        # Binary search the first mismatch inside this chunk: prefix `lo` matches, prefix `hi` doesn't.
        lo, hi = 0, k
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if a[a_pos + n : a_pos + n + mid] == b[b_pos + n : b_pos + n + mid]:
                lo = mid
            else:
                hi = mid
        return n + lo
    return n


def create(source, target, metadata=b""):
    source, target = to_z64(source), to_z64(target)
    out = bytearray(b"BPS1")
    write_number(out, len(source))
    write_number(out, len(target))
    write_number(out, len(metadata))
    out.extend(metadata)

    index = {}
    for off in range(0, len(source) - BLOCK + 1, BLOCK):
        index.setdefault(source[off : off + BLOCK], off)

    state = {"src_rel": 0}

    def emit_literal(start, end):
        if end > start:
            write_number(out, ((end - start - 1) << 2) | TARGET_READ)
            out.extend(target[start:end])

    def emit_copy(t_pos, s_pos, length):
        if s_pos == t_pos:
            write_number(out, ((length - 1) << 2) | SOURCE_READ)
            return
        write_number(out, ((length - 1) << 2) | SOURCE_COPY)
        delta = s_pos - state["src_rel"]
        write_number(out, (abs(delta) << 1) | (1 if delta < 0 else 0))
        state["src_rel"] = s_pos + length

    pos, literal_start = 0, 0
    tlen, slen = len(target), len(source)
    while pos < tlen:
        best_s, best_len = -1, 0

        # Fast path: unchanged in place.
        if pos + 8 <= min(slen, tlen) and source[pos : pos + 8] == target[pos : pos + 8]:
            best_s, best_len = pos, match_length(source, pos, target, pos, min(slen, tlen) - pos)

        # Moved data: look up the block starting here in the source index.
        if best_len < BLOCK and pos + BLOCK <= tlen:
            s = index.get(target[pos : pos + BLOCK])
            if s is not None:
                n = match_length(source, s, target, pos, min(slen - s, tlen - pos))
                if n > best_len:
                    best_s, best_len = s, n

        if best_len == 0:
            pos += 1
            continue

        # Extend the match backwards into the pending literal run.
        back = 0
        while (
            pos - back > literal_start
            and best_s - back > 0
            and source[best_s - back - 1] == target[pos - back - 1]
        ):
            back += 1
        emit_literal(literal_start, pos - back)
        emit_copy(pos - back, best_s - back, best_len + back)
        pos += best_len
        literal_start = pos

    emit_literal(literal_start, tlen)

    out.extend(zlib.crc32(source).to_bytes(4, "little"))
    out.extend(zlib.crc32(target).to_bytes(4, "little"))
    out.extend(zlib.crc32(out).to_bytes(4, "little"))
    return bytes(out)


def read_info(patch):
    """Header fields and metadata of a patch, without applying it."""
    if patch[:4] != b"BPS1":
        raise ValueError("not a BPS patch")
    pos = 4
    source_size, pos = read_number(patch, pos)
    target_size, pos = read_number(patch, pos)
    meta_size, pos = read_number(patch, pos)
    return {
        "source_size": source_size,
        "target_size": target_size,
        "metadata": patch[pos : pos + meta_size].decode("utf-8", "replace"),
        "source_crc": int.from_bytes(patch[-12:-8], "little"),
        "target_crc": int.from_bytes(patch[-8:-4], "little"),
        "patch_ok": zlib.crc32(patch[:-4]) == int.from_bytes(patch[-4:], "little"),
    }


def apply(source, patch):
    source = to_z64(source)
    if patch[:4] != b"BPS1":
        raise ValueError("not a BPS patch")
    if zlib.crc32(patch[:-4]) != int.from_bytes(patch[-4:], "little"):
        raise ValueError("patch is corrupt (patch CRC mismatch)")
    if zlib.crc32(source) != int.from_bytes(patch[-12:-8], "little"):
        raise ValueError("this patch is for a different ROM (source CRC mismatch); use a US 1.0 dump")

    pos = 4
    source_size, pos = read_number(patch, pos)
    target_size, pos = read_number(patch, pos)
    meta_size, pos = read_number(patch, pos)
    pos += meta_size
    if source_size != len(source):
        raise ValueError("source size mismatch")

    target = bytearray(target_size)
    out = 0
    src_rel = tgt_rel = 0
    end = len(patch) - 12
    while pos < end:
        data, pos = read_number(patch, pos)
        cmd, length = data & 3, (data >> 2) + 1
        if cmd == SOURCE_READ:
            target[out : out + length] = source[out : out + length]
        elif cmd == TARGET_READ:
            target[out : out + length] = patch[pos : pos + length]
            pos += length
        else:
            data, pos = read_number(patch, pos)
            delta = -(data >> 1) if data & 1 else data >> 1
            if cmd == SOURCE_COPY:
                src_rel += delta
                target[out : out + length] = source[src_rel : src_rel + length]
                src_rel += length
            else:  # TARGET_COPY may overlap its own output, so copy byte by byte
                tgt_rel += delta
                for i in range(length):
                    target[out + i] = target[tgt_rel + i]
                tgt_rel += length
        out += length

    if out != target_size or zlib.crc32(target) != int.from_bytes(patch[-8:-4], "little"):
        raise ValueError("patched output is wrong (target CRC mismatch)")
    return bytes(target)


# --------------------------------------------------------------------------------------------------------------------


def selftest():
    rng = random.Random(1234)
    cases = 0
    for trial in range(40):
        size = rng.choice([0, 1, 100, 5000, 70000])
        source = bytes(rng.getrandbits(8) for _ in range(size))
        target = bytearray(source)
        for _ in range(rng.randint(0, 6)):
            op = rng.choice(["modify", "insert", "delete", "move"])
            if op == "modify" and target:
                i = rng.randrange(len(target))
                target[i : i + rng.randint(1, 300)] = bytes(rng.getrandbits(8) for _ in range(rng.randint(1, 300)))
            elif op == "insert":
                i = rng.randint(0, len(target))
                target[i:i] = bytes(rng.getrandbits(8) for _ in range(rng.randint(1, 2000)))
            elif op == "delete" and target:
                i = rng.randrange(len(target))
                del target[i : i + rng.randint(1, 2000)]
            elif op == "move" and len(target) > 10:
                i = rng.randrange(len(target))
                chunk = target[i : i + rng.randint(1, 5000)]
                del target[i : i + len(chunk)]
                j = rng.randint(0, len(target))
                target[j:j] = chunk
        target = bytes(target)
        patch = create(source, target)
        assert apply(source, patch) == target, "round trip failed on trial %d" % trial
        if source == target and size:
            assert len(patch) < 64, "identical files should give a tiny patch"
        cases += 1

    # Byte-order normalisation: a patch made from a .z64 applies to a .v64 / .n64 dump of the same ROM.
    z64 = b"\x80\x37\x12\x40" + bytes(rng.getrandbits(8) for _ in range(4092))
    mod = z64[:2000] + b"MAJORA CITY" + z64[2000:]
    v64 = bytearray(z64)
    v64[0::2], v64[1::2] = z64[1::2], z64[0::2]
    n64 = bytearray(z64)
    n64[0::4], n64[1::4], n64[2::4], n64[3::4] = z64[3::4], z64[2::4], z64[1::4], z64[0::4]
    patch = create(z64, mod)
    assert apply(bytes(v64), patch) == mod
    assert apply(bytes(n64), patch) == mod

    # Metadata is carried in the header and doesn't disturb the patch.
    meta = "Majora City v0.0.0-test\ncommit 0000000".encode()
    patch = create(z64, mod, meta)
    assert apply(z64, patch) == mod
    assert read_info(patch)["metadata"] == meta.decode()

    # A shifted block (as in a recompressed ROM) must be encoded as copies, not literals.
    big = bytes(rng.getrandbits(8) for _ in range(200000))
    shifted = big[:1000] + b"\x00" * 64 + big[1000:]
    assert len(create(big, shifted)) < 200, "moved data should be copied from the source"

    print("bps selftest: %d round trips OK" % (cases + 4))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create")
    c.add_argument("original")
    c.add_argument("modified")
    c.add_argument("out")
    c.add_argument("--metadata", default="", help="text stored in the patch header (version, commit, ...)")
    a = sub.add_parser("apply")
    a.add_argument("original")
    a.add_argument("patch")
    a.add_argument("out")
    i = sub.add_parser("info")
    i.add_argument("patch")
    sub.add_parser("selftest")
    args = parser.parse_args()

    if args.cmd == "selftest":
        selftest()
        return 0

    if args.cmd == "info":
        with open(args.patch, "rb") as f:
            patch = f.read()
        try:
            info = read_info(patch)
        except ValueError as e:
            print("error: %s" % e, file=sys.stderr)
            return 1
        print(info["metadata"] or "(no metadata)")
        print("ROM size before: %d bytes, after: %d bytes" % (info["source_size"], info["target_size"]))
        print("Patch file %s" % ("OK" if info["patch_ok"] else "is CORRUPT"))
        return 0 if info["patch_ok"] else 1

    with open(args.original, "rb") as f:
        original = f.read()

    if args.cmd == "create":
        with open(args.modified, "rb") as f:
            modified = f.read()
        patch = create(original, modified, args.metadata.encode("utf-8"))
        assert apply(original, patch) == to_z64(modified), "internal error: patch does not round-trip"
        with open(args.out, "wb") as f:
            f.write(patch)
        print("wrote %s (%d KB)" % (args.out, (len(patch) + 1023) // 1024))
    else:
        with open(args.patch, "rb") as f:
            patch = f.read()
        try:
            result = apply(original, patch)
        except ValueError as e:
            print("error: %s" % e, file=sys.stderr)
            return 1
        with open(args.out, "wb") as f:
            f.write(result)
        print("wrote %s" % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
