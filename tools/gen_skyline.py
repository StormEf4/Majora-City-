#!/usr/bin/env python3
"""
Procedural skyline generator for Majora City.

Generates mod/src/overlays/actors/ovl_Mc_Skyline/mc_skyline_data.inc.c:
  * two 32x32 I8 window textures (day and night),
  * N64 display lists for a handful of Art Deco tower archetypes,
  * the tower placement layouts used by the Mc_Skyline actor.

Everything here is generated from scratch, so the output contains no Nintendo assets.
Run it again after changing any parameter; the output is deterministic.

    python3 tools/gen_skyline.py            # regenerate
    python3 tools/gen_skyline.py --check    # fail if the committed file is out of date (used by tools/check.sh)
"""

import argparse
import math
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT_PATH = REPO / "mod/src/overlays/actors/ovl_Mc_Skyline/mc_skyline_data.inc.c"

# --------------------------------------------------------------------------------------------------------------------
# Scale reference: Link is ~50 units tall and a door is ~100 units. One building floor is 100 units, and one 32x32
# window texture tile covers 4x4 window bays = 400x400 units.
# --------------------------------------------------------------------------------------------------------------------
TEX_SIZE = 32
CELL_UNITS = 400  # world units covered by one texture tile, horizontally and vertically
TEXELS_PER_UNIT = TEX_SIZE / CELL_UNITS
ST_FIXED = 32  # S10.5 fixed point
SOLID_ST = 16  # half a texel into texel (0, 0), which is wall in both textures

VTX_BUFFER = 32  # F3DZEX2 vertex cache size

# Fake directional lighting baked into vertex colours (lighting is off for the skyline).
FACE_BRIGHTNESS = {"+z": 1.00, "+x": 0.84, "-x": 0.76, "-z": 0.66, "+y": 0.92}


# --------------------------------------------------------------------------------------------------------------------
# Textures
# --------------------------------------------------------------------------------------------------------------------


def window_texel(x, y):
    """Classify a texel of the 32x32 tile: 'wall', or ('window', bay_col, bay_row, v) with v in [0, 1) down the pane."""
    bx, by = x % 8, y % 8
    if bx < 2 or by < 3:
        return "wall"
    return ("window", x // 8, y // 8, (by - 3) / 5.0)


def make_textures():
    rng = random.Random(0x4D43)  # "MC"
    lit = {(c, r): rng.random() < 0.45 for c in range(4) for r in range(4)}
    warm = {(c, r): rng.randint(0, 40) for c in range(4) for r in range(4)}
    day, night = [], []
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            kind = window_texel(x, y)
            if kind == "wall":
                day.append(205)
                night.append(38)
            else:
                _, c, r, v = kind
                # Day: dark glass, lighter near the top where it reflects the sky.
                day.append(int(110 - 55 * v))
                # Night: some offices are lit, the rest are dark glass.
                night.append(255 - warm[(c, r)] if lit[(c, r)] else 22)
    # Texel (0, 0) must be wall in both: roofs and crowns sample it for a solid colour.
    assert window_texel(0, 0) == "wall"
    return day, night


def emit_u64_texture(name, texels):
    assert len(texels) == TEX_SIZE * TEX_SIZE
    words = []
    for i in range(0, len(texels), 8):
        chunk = texels[i : i + 8]
        words.append("0x" + "".join("%02X" % b for b in chunk))
    lines = ["static u64 %s[%d * %d / 8] = {" % (name, TEX_SIZE, TEX_SIZE)]
    for i in range(0, len(words), 4):
        lines.append("    " + ", ".join(words[i : i + 4]) + ",")
    lines.append("};")
    return "\n".join(lines)


# --------------------------------------------------------------------------------------------------------------------
# Geometry
# --------------------------------------------------------------------------------------------------------------------


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


class Mesh:
    """Collects polygons (quads/tris) with per-vertex colour and texture coordinates."""

    def __init__(self, height):
        self.polys = []  # list of list of (pos, st, shade)
        self.height = height

    def shade(self, face, y):
        # Darker at street level, brighter towards the top: reads as atmospheric depth from far away.
        k = FACE_BRIGHTNESS[face] * (0.72 + 0.28 * min(1.0, y / self.height))
        return max(0, min(255, int(round(255 * k))))

    def add_poly(self, corners, face, normal, textured):
        # Enforce counter-clockwise winding seen from outside (front faces survive G_CULL_BACK).
        n = cross(sub(corners[1], corners[0]), sub(corners[2], corners[0]))
        if dot(n, normal) < 0:
            corners = [corners[0]] + corners[:0:-1]
        n = cross(sub(corners[1], corners[0]), sub(corners[2], corners[0]))
        assert dot(n, normal) > 0, "bad winding"

        verts = []
        origin = corners[0]
        for p in corners:
            if textured:
                u = math.hypot(p[0] - origin[0], p[2] - origin[2])
                s = int(round(u * TEXELS_PER_UNIT * ST_FIXED))
                t = int(round(-p[1] * TEXELS_PER_UNIT * ST_FIXED))
            else:
                s = t = SOLID_ST
            assert -32768 <= s <= 32767 and -32768 <= t <= 32767
            verts.append((p, (s, t), self.shade(face, p[1])))
        self.polys.append(verts)

    def add_box(self, w, d, y0, y1):
        x0, x1, z0, z1 = -w / 2, w / 2, -d / 2, d / 2
        sides = [
            ("+z", (0, 0, 1), [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]),
            ("+x", (1, 0, 0), [(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)]),
            ("-z", (0, 0, -1), [(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)]),
            ("-x", (-1, 0, 0), [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)]),
        ]
        for face, normal, corners in sides:
            self.add_poly(corners, face, normal, textured=True)
        self.add_poly([(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)], "+y", (0, 1, 0), textured=False)

    def add_pyramid(self, w, d, y0, h):
        x0, x1, z0, z1 = -w / 2, w / 2, -d / 2, d / 2
        apex = (0, y0 + h, 0)
        sides = [
            ("+z", (0, 0.5, 1), [(x0, y0, z1), (x1, y0, z1), apex]),
            ("+x", (1, 0.5, 0), [(x1, y0, z1), (x1, y0, z0), apex]),
            ("-z", (0, 0.5, -1), [(x1, y0, z0), (x0, y0, z0), apex]),
            ("-x", (-1, 0.5, 0), [(x0, y0, z0), (x0, y0, z1), apex]),
        ]
        for face, normal, corners in sides:
            self.add_poly(corners, face, normal, textured=False)


def build_archetype(spec):
    """spec: dict with 'tiers' [(w, d, h)], optional 'crown' (w, d, h) and 'spire' (w, h)."""
    total = sum(t[2] for t in spec["tiers"])
    if "crown" in spec:
        total += spec["crown"][2]
    if "spire" in spec:
        total += spec["spire"][1]
    mesh = Mesh(total)
    y = 0
    for w, d, h in spec["tiers"]:
        mesh.add_box(w, d, y, y + h)
        y += h
    if "crown" in spec:
        w, d, h = spec["crown"]
        mesh.add_pyramid(w, d, y, h)
        y += h * 0.35  # spire sits partway up the crown
    if "spire" in spec:
        w, h = spec["spire"]
        mesh.add_pyramid(w, w, y, h)
    return mesh


# Tower archetypes. Heights are before per-instance scaling (scaleY 70%..130%).
ARCHETYPES = [
    ("Slab", {"tiers": [(600, 400, 3600)]}),
    ("Setback", {"tiers": [(700, 700, 2200), (520, 520, 1400), (340, 340, 900)], "spire": (70, 900)}),
    ("TwinStep", {"tiers": [(800, 500, 2600), (500, 320, 1200)]}),
    ("Needle", {"tiers": [(420, 420, 3600)], "crown": (420, 420, 700)}),
    ("Crown", {"tiers": [(600, 600, 2800), (460, 460, 400), (320, 320, 400)], "crown": (320, 320, 500), "spire": (36, 1000)}),
    ("Block", {"tiers": [(900, 700, 1400), (700, 500, 600)]}),
]


def emit_archetype(index, name, mesh):
    vtx_name = "sMcSkyline%sVtx" % name
    dl_name = "sMcSkyline%sDL" % name
    vtx_lines, dl_lines = [], []
    batch, batch_start = [], 0
    vcount = 0

    def flush():
        nonlocal batch, batch_start
        if not batch:
            return
        n = sum(len(p) for p in batch)
        dl_lines.append("    gsSPVertex(&%s[%d], %d, 0)," % (vtx_name, batch_start, n))
        tris, base = [], 0
        for poly in batch:
            if len(poly) == 4:
                tris += [(base, base + 1, base + 2), (base, base + 2, base + 3)]
            else:
                tris.append((base, base + 1, base + 2))
            base += len(poly)
        for i in range(0, len(tris) - 1, 2):
            a, b = tris[i], tris[i + 1]
            dl_lines.append("    gsSP2Triangles(%d, %d, %d, 0, %d, %d, %d, 0)," % (a + b))
        if len(tris) % 2:
            dl_lines.append("    gsSP1Triangle(%d, %d, %d, 0)," % tris[-1])
        batch_start += n
        batch = []

    for poly in mesh.polys:
        if sum(len(p) for p in batch) + len(poly) > VTX_BUFFER:
            flush()
        batch.append(poly)
        for (x, y, z), (s, t), c in poly:
            vtx_lines.append(
                "    VTX(%d, %d, %d, %d, %d, %d, %d, %d, 255),"
                % (round(x), round(y), round(z), s, t, c, c, c)
            )
            vcount += 1
    flush()
    dl_lines.append("    gsSPEndDisplayList(),")

    tri_count = sum(2 if len(p) == 4 else 1 for p in mesh.polys)
    out = []
    out.append("// Archetype %d: %s (%d vertices, %d triangles)" % (index, name, vcount, tri_count))
    out.append("static Vtx %s[] = {" % vtx_name)
    out += vtx_lines
    out.append("};")
    out.append("")
    out.append("static Gfx %s[] = {" % dl_name)
    out += dl_lines
    out.append("};")
    return "\n".join(out), dl_name, tri_count


# --------------------------------------------------------------------------------------------------------------------
# Layouts
# --------------------------------------------------------------------------------------------------------------------

TONES = 6  # must match sMcSkylineTones[] in z_mc_skyline.c

# Footprint limits are for the whole tower, not just its centre, so a tower can never cross the ring it belongs to.
LAYOUTS = [
    {
        # Termina Field: a dense downtown inside the Clock Town walls, clear of the Clock Tower itself.
        # Slim archetypes only; the walled town is only ~2500 units across.
        "name": "Field",
        "seed": 0xF1E1D,
        "count": 10,
        "footprint": (260, 1200),  # inner: Clock Tower clearance, outer: inside the walls
        "archetypes": ["Slab", "Setback", "Needle", "Crown"],
        "scale_xz": (55, 75),  # slim "pencil towers"
        "scale_y": (90, 165),
        "gap": 20,
    },
    {
        # Old Town scenes: a ring of towers outside the walls, seen over the rooftops.
        "name": "Town",
        "seed": 0x7043,
        "count": 24,
        "footprint": (2600, 5600),
        "archetypes": [name for name, _ in ARCHETYPES],
        "scale_xz": (85, 115),
        "scale_y": (90, 140),
        "gap": 120,
    },
]


def footprint_radius(spec):
    """Horizontal radius that contains the archetype at 100% scale."""
    parts = list(spec["tiers"]) + ([spec["crown"]] if "crown" in spec else [])
    return max(math.hypot(w / 2, d / 2) for w, d, _ in parts)


def make_layout(layout):
    rng = random.Random(layout["seed"])
    names = [name for name, _ in ARCHETYPES]
    allowed = [names.index(n) for n in layout["archetypes"]]
    lo, hi = layout["footprint"]
    towers = []
    attempts = 0
    while len(towers) < layout["count"]:
        attempts += 1
        assert attempts < 200000, "layout %s too dense" % layout["name"]
        archetype = rng.choice(allowed)
        scale_xz = rng.randint(*layout["scale_xz"])
        fp = footprint_radius(ARCHETYPES[archetype][1]) * scale_xz / 100.0
        if lo + fp > hi - fp:
            continue
        angle = rng.randrange(0, 0x10000)
        # Uniform over the annulus area that keeps the whole footprint in bounds.
        radius = math.sqrt(rng.uniform((lo + fp) ** 2, (hi - fp) ** 2))
        a = angle / 0x10000 * 2 * math.pi
        x, z = math.sin(a) * radius, math.cos(a) * radius
        if any(math.hypot(x - tx, z - tz) < fp + tfp + layout["gap"] for tx, tz, tfp, _ in towers):
            continue
        # Face roughly toward the centre, snapped to 1/16 turns so the city reads as planned.
        yaw = (angle + 0x8000 + rng.choice([0, 0, 0x1000, -0x1000])) & 0xFFFF
        yaw = (yaw // 0x1000) * 0x1000
        tone = rng.randrange(TONES)
        scale_y = rng.randint(*layout["scale_y"])
        towers.append((x, z, fp, (angle, int(radius), yaw, archetype, tone, scale_xz, scale_y)))
    # Order doesn't matter for opaque geometry; sort by angle for readable output.
    return sorted((t[3] for t in towers), key=lambda t: t[0])


def emit_layout(name, towers):
    lines = ["static McSkylineTower sMcSkylineLayout%s[] = {" % name]
    lines.append("    // angle, radius, yaw, archetype, tone, scaleXZ%, scaleY%")
    for angle, radius, yaw, arch, tone, sxz, sy in towers:
        lines.append(
            "    { 0x%04X, %d, 0x%04X, %d, %d, %d, %d },"
            % (angle & 0xFFFF, radius, yaw & 0xFFFF, arch, tone, sxz, sy)
        )
    lines.append("};")
    return "\n".join(lines)


# --------------------------------------------------------------------------------------------------------------------


def generate():
    out = []
    out.append("/**")
    out.append(" * GENERATED by tools/gen_skyline.py. Do not edit by hand; change the generator and re-run it.")
    out.append(" * Procedural geometry and textures only: no Nintendo assets.")
    out.append(" */")
    out.append("")
    day, night = make_textures()
    out.append(emit_u64_texture("sMcSkylineWindowDayTex", day))
    out.append("")
    out.append(emit_u64_texture("sMcSkylineWindowNightTex", night))
    out.append("")

    dl_names = []
    tri_counts = []
    for i, (name, spec) in enumerate(ARCHETYPES):
        text, dl_name, tris = emit_archetype(i, name, build_archetype(spec))
        out.append(text)
        out.append("")
        dl_names.append(dl_name)
        tri_counts.append(tris)

    out.append("static Gfx* sMcSkylineArchetypeDLs[] = {")
    for dl in dl_names:
        out.append("    %s," % dl)
    out.append("};")
    out.append("")

    summary = []
    for layout in LAYOUTS:
        name = layout["name"]
        towers = make_layout(layout)
        out.append(emit_layout(name, towers))
        out.append("")
        tris = sum(tri_counts[t[3]] for t in towers)
        summary.append("%s: %d towers, %d triangles" % (name, len(towers), tris))

    out.append("// Budget: " + "; ".join(summary))
    return "\n".join(out) + "\n", summary


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="exit 1 if the generated file is out of date")
    args = parser.parse_args()

    text, summary = generate()
    if args.check:
        current = OUT_PATH.read_text() if OUT_PATH.exists() else ""
        if current != text:
            print("%s is out of date; run tools/gen_skyline.py" % OUT_PATH.relative_to(REPO), file=sys.stderr)
            return 1
        print("skyline data up to date (%s)" % "; ".join(summary))
        return 0

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(text)
    print("wrote %s (%s)" % (OUT_PATH.relative_to(REPO), "; ".join(summary)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
