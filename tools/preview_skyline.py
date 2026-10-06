#!/usr/bin/env python3
"""
Software preview of the generated skyline (no ROM or emulator needed).

Grey walls and a Clock Tower are drawn as rough stand-ins for context; they are not game data.

Parses the *generated C* (mod/src/overlays/actors/ovl_Mc_Skyline/mc_skyline_data.inc.c), rebuilds the triangles
from the gsSPVertex / gsSP2Triangles commands, and rasterises them with back-face culling, the window textures,
vertex shading, per-tower tones and distance fog, roughly as the N64 would. It doubles as a test of the display
lists: wrong winding, bad texture coordinates or broken vertex batches all show up in the picture.

    python3 tools/preview_skyline.py                     # docs/images/skyline_field_dawn.png and friends
    python3 tools/preview_skyline.py --layout Town --time night --out /tmp/town.png

Requires numpy and Pillow.
"""

import argparse
import math
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "mod/src/overlays/actors/ovl_Mc_Skyline/mc_skyline_data.inc.c"
ACTOR = REPO / "mod/src/overlays/actors/ovl_Mc_Skyline/z_mc_skyline.c"


# --------------------------------------------------------------------------------------------------------------------
# Parse the generated C
# --------------------------------------------------------------------------------------------------------------------


def parse_data(text):
    tex = {}
    for name, body in re.findall(r"static u64 (\w+)\[[^\]]*\] = \{(.*?)\};", text, re.S):
        words = re.findall(r"0x([0-9A-F]{16})", body)
        tex[name] = np.frombuffer(bytes.fromhex("".join(words)), dtype=np.uint8).reshape(32, 32)

    vtx = {}
    for name, body in re.findall(r"static Vtx (\w+)\[\] = \{(.*?)\};", text, re.S):
        vtx[name] = [tuple(int(v) for v in m) for m in re.findall(r"VTX\(([^)]*)\)", body) for m in [m.split(",")]]

    dls = {}
    for name, body in re.findall(r"static Gfx (\w+)\[\] = \{(.*?)\};", text, re.S):
        tris, cache = [], [None] * 32
        for line in body.strip().splitlines():
            line = line.strip()
            m = re.match(r"gsSPVertex\(&(\w+)\[(\d+)\], (\d+), (\d+)\)", line)
            if m:
                src, start, n, v0 = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
                assert n + v0 <= 32, "vertex batch overflows the 32-entry cache"
                for i in range(n):
                    cache[v0 + i] = vtx[src][start + i]
                continue
            m = re.match(r"gsSP2Triangles\((.*)\),", line)
            if m:
                a = [int(v) for v in m.group(1).split(",")]
                tris += [[cache[a[0]], cache[a[1]], cache[a[2]]], [cache[a[4]], cache[a[5]], cache[a[6]]]]
                continue
            m = re.match(r"gsSP1Triangle\((.*)\),", line)
            if m:
                a = [int(v) for v in m.group(1).split(",")]
                tris.append([cache[a[0]], cache[a[1]], cache[a[2]]])
        assert all(v is not None for t in tris for v in t), "%s uses an unloaded vertex" % name
        dls[name] = tris

    order = re.search(r"sMcSkylineArchetypeDLs\[\] = \{(.*?)\};", text, re.S).group(1)
    archetypes = [dls[n] for n in re.findall(r"(\w+),", order)]

    layouts = {}
    for name, body in re.findall(r"static McSkylineTower sMcSkylineLayout(\w+)\[\] = \{(.*?)\};", text, re.S):
        rows = re.findall(r"\{ ([^}]*) \}", body)
        layouts[name] = [tuple(int(v, 0) for v in r.split(",")) for r in rows]
    return tex, archetypes, layouts


def parse_tones(text):
    body = re.search(r"sMcSkylineTones\[\] = \{(.*?)\};", text, re.S).group(1)
    return [tuple(int(v) for v in m) for m in re.findall(r"\{ (\d+), (\d+), (\d+) \}", body)]


# --------------------------------------------------------------------------------------------------------------------
# Tiny rasteriser
# --------------------------------------------------------------------------------------------------------------------


class Camera:
    def __init__(self, eye, at, fov_deg, w, h):
        self.eye = np.array(eye, float)
        fwd = np.array(at, float) - self.eye
        fwd /= np.linalg.norm(fwd)
        right = np.cross(fwd, [0, 1, 0])
        right /= np.linalg.norm(right)
        up = np.cross(right, fwd)
        self.basis = np.stack([right, up, fwd])
        self.f = (h / 2) / math.tan(math.radians(fov_deg) / 2)
        self.w, self.h = w, h

    def project(self, p):
        c = self.basis @ (np.asarray(p, float) - self.eye)
        return c[0] * self.f / c[2] + self.w / 2, -c[1] * self.f / c[2] + self.h / 2, c[2]


NEAR = 10.0


def clip_near(poly):
    """Sutherland-Hodgman clip of a camera-space polygon [(xyz, (s, t), shade)] against z >= NEAR."""
    out = []
    for i, a in enumerate(poly):
        b = poly[(i + 1) % len(poly)]
        a_in, b_in = a[0][2] >= NEAR, b[0][2] >= NEAR
        if a_in:
            out.append(a)
        if a_in != b_in:
            t = (NEAR - a[0][2]) / (b[0][2] - a[0][2])
            pos = a[0] + (b[0] - a[0]) * t
            st = (a[1][0] + (b[1][0] - a[1][0]) * t, a[1][1] + (b[1][1] - a[1][1]) * t)
            out.append((pos, st, a[2] + (b[2] - a[2]) * t))
    return out


def raster(cam, color, depth, tri, texture, tint, fog_color, fog_near, fog_far):
    cs = [(cam.basis @ (np.asarray(v[0], float) - cam.eye), v[1], v[2]) for v in tri]
    poly = clip_near(cs)
    for i in range(1, len(poly) - 1):
        raster_triangle(cam, color, depth, [poly[0], poly[i], poly[i + 1]], texture, tint, fog_color, fog_near, fog_far)


def raster_triangle(cam, color, depth, tri, texture, tint, fog_color, fog_near, fog_far):
    pts = [(c[0] * cam.f / c[2] + cam.w / 2, -c[1] * cam.f / c[2] + cam.h / 2, c[2]) for c, _, _ in tri]
    (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = pts
    area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
    # Screen y points down, so counter-clockwise world winding shows up as negative area here. Cull the rest.
    if area >= 0:
        return
    xmin, xmax = max(int(min(x0, x1, x2)), 0), min(int(max(x0, x1, x2)) + 1, cam.w)
    ymin, ymax = max(int(min(y0, y1, y2)), 0), min(int(max(y0, y1, y2)) + 1, cam.h)
    if xmin >= xmax or ymin >= ymax:
        return
    xs, ys = np.meshgrid(np.arange(xmin, xmax) + 0.5, np.arange(ymin, ymax) + 0.5)
    w0 = ((x1 - xs) * (y2 - ys) - (x2 - xs) * (y1 - ys)) / area
    w1 = ((x2 - xs) * (y0 - ys) - (x0 - xs) * (y2 - ys)) / area
    w2 = 1 - w0 - w1
    inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
    if not inside.any():
        return
    z = 1 / (w0 / z0 + w1 / z1 + w2 / z2)
    region = depth[ymin:ymax, xmin:xmax]
    mask = inside & (z < region)
    if not mask.any():
        return

    def interp(a, b, c):
        return (w0 * a / z0 + w1 * b / z1 + w2 * c / z2) * z

    s = interp(*[v[1][0] for v in tri]) / 32.0
    t = interp(*[v[1][1] for v in tri]) / 32.0
    shade = interp(*[v[2] for v in tri]) / 255.0
    texel = texture[np.floor(t).astype(int) % 32, np.floor(s).astype(int) % 32] / 255.0
    rgb = texel[..., None] * shade[..., None] * (np.array(tint) / 255.0)
    fog = np.clip((z - fog_near) / (fog_far - fog_near), 0, 1)[..., None]
    rgb = rgb * (1 - fog) + np.array(fog_color) / 255.0 * fog
    color[ymin:ymax, xmin:xmax][mask] = rgb[mask]
    region[mask] = z[mask]


def place(tri, tower, center, base_y):
    angle, radius, yaw, _, _, sxz, sy = tower
    a = angle / 0x10000 * 2 * math.pi
    cx, cz = center[0] + math.sin(a) * radius, center[1] + math.cos(a) * radius
    r = yaw / 0x10000 * 2 * math.pi
    cr, sr = math.cos(r), math.sin(r)
    out = []
    for (x, y, z, s, t, c, _, _, _) in tri:
        x, y, z = x * sxz / 100.0, y * sy / 100.0, z * sxz / 100.0
        # Matrix_RotateYS: x' = x cos + z sin, z' = -x sin + z cos
        out.append(((cx + x * cr + z * sr, base_y + y, cz - x * sr + z * cr), (s, t), c))
    return out


def standin_tris(layout_name):
    """
    Simple grey stand-ins for the Clock Town walls and Clock Tower, for context only. They are rough guesses at the
    real scene geometry (which lives in the ROM), drawn so the pictures read; they are not part of the hack.
    """
    tris = []

    def quad(a, b, c, d, shade):
        for tri in ([a, b, c], [a, c, d], [a, c, b], [a, d, c]):  # both sides
            tris.append([(p, (16, 16), shade) for p in tri])

    wall_r, wall_h, y0 = (1250, 520, -50) if layout_name == "Field" else (1900, 650, -50)
    if layout_name == "Town":
        # The Clock Tower stand-in would fill the frame from the plaza; walls are enough context there.
        tower = False
    else:
        tower = True
    segments = 40
    for i in range(segments):
        a0, a1 = 2 * math.pi * i / segments, 2 * math.pi * (i + 1) / segments
        p0 = (math.sin(a0) * wall_r, y0, math.cos(a0) * wall_r)
        p1 = (math.sin(a1) * wall_r, y0, math.cos(a1) * wall_r)
        quad(p0, p1, (p1[0], y0 + wall_h, p1[2]), (p0[0], y0 + wall_h, p0[2]), 190 if i % 2 else 175)

    if not tower:
        return tris
    w, h = 170, 1400
    corners = [(-w, -w), (w, -w), (w, w), (-w, w)]
    for i in range(4):
        (x0, z0), (x1, z1) = corners[i], corners[(i + 1) % 4]
        quad((x0, y0, z0), (x1, y0, z1), (x1, y0 + h, z1), (x0, y0 + h, z0), 150 + 25 * i)
    apex = (0, y0 + h + 450, 0)
    for i in range(4):
        (x0, z0), (x1, z1) = corners[i], corners[(i + 1) % 4]
        for tri in ([(x0, y0 + h, z0), (x1, y0 + h, z1), apex], [(x1, y0 + h, z1), (x0, y0 + h, z0), apex]):
            tris.append([(p, (16, 16), 140 + 20 * i) for p in tri])
    return tris


def ground_tris(extent=24000, tile=1500):
    """Depth-tested ground tiles, so tower bases sunk below street level stay hidden as they are in-game."""
    tris = []
    for x in range(-extent, extent, tile):
        for z in range(-extent, extent, tile):
            a, b, c, d = (x, 0, z + tile), (x + tile, 0, z + tile), (x + tile, 0, z), (x, 0, z)
            tris.append([(a, (16, 16), 255), (b, (16, 16), 255), (c, (16, 16), 255)])
            tris.append([(a, (16, 16), 255), (c, (16, 16), 255), (d, (16, 16), 255)])
    return tris


TIMES = {
    # sky top, sky horizon, tint, texture, fog colour
    "dawn": ((70, 80, 140), (250, 170, 120), (255, 200, 160), "Day", (230, 170, 140)),
    "day": ((80, 140, 220), (190, 215, 240), (255, 255, 255), "Day", (190, 210, 230)),
    "night": ((5, 8, 25), (30, 30, 70), (255, 225, 170), "Night", (25, 25, 55)),
}


def render(layout_name, time, out_path, width=960, height=540):
    text = DATA.read_text()
    tex, archetypes, layouts = parse_data(text)
    tones = parse_tones(ACTOR.read_text())
    sky_top, sky_hor, tint, tex_name, fog_color = TIMES[time]
    texture = tex["sMcSkylineWindow%sTex" % tex_name]

    color = np.zeros((height, width, 3))
    grad = np.linspace(0, 1, height)[:, None, None]
    color[:] = (np.array(sky_top) * (1 - grad) + np.array(sky_hor) * grad) / 255.0
    depth = np.full((height, width), np.inf)

    if layout_name == "Field":
        # Intro shot 1: low behind Epona on the road from the swamp, aimed past Link at the skyline.
        cam = Camera((0, 150, 9500), (0, 2300, 0), 50, width, height)
        fog_near, fog_far = 5000, 22000
        ground = (70, 95, 55)
        base_y = -200  # MC_SKYLINE_FIELD_SINK
    else:
        # Standing in South Clock Town plaza, looking north-east over the rooftops.
        cam = Camera((-200, 60, 900), (2600, 1700, 4200), 70, width, height)
        fog_near, fog_far = 3000, 10000
        ground = (120, 110, 100)
        base_y = -800  # MC_SKYLINE_TOWN_SINK

    # Ground plane: everything below the horizon line. Dark at night.
    gk = 0.25 if time == "night" else 1.0
    horizon = int(cam.project((cam.eye[0], cam.eye[1], cam.eye[2] - 1e7))[1])
    if 0 < horizon < height:
        color[horizon:] = np.array(ground) * gk / 255.0

    flat = np.full((32, 32), 255, np.uint8)
    for tri in ground_tris():
        raster(cam, color, depth, tri, flat, [int(c * gk) for c in ground], fog_color, fog_near, fog_far)

    stone = [int(210 * tint[i] / 255 * (0.25 if time == "night" else 1.0)) for i in range(3)]
    for tri in standin_tris(layout_name):
        raster(cam, color, depth, tri, tex["sMcSkylineWindowDayTex"], stone, fog_color, fog_near, fog_far)

    for tower in layouts[layout_name]:
        tone = tones[tower[4]]
        ttint = [tone[i] * tint[i] // 255 for i in range(3)]
        for tri in archetypes[tower[3]]:
            raster(cam, color, depth, place(tri, tower, (0, 0), base_y), texture, ttint, fog_color, fog_near, fog_far)

    img = Image.fromarray((np.clip(color, 0, 1) * 255).astype(np.uint8))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    print("wrote", out_path.relative_to(REPO) if out_path.is_relative_to(REPO) else out_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--layout", choices=["Field", "Town"])
    parser.add_argument("--time", choices=list(TIMES))
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    if args.layout or args.time or args.out:
        layout, time = args.layout or "Field", args.time or "dawn"
        render(layout, time, args.out or REPO / ("docs/images/skyline_%s_%s.png" % (layout.lower(), time)))
    else:
        for layout, time in [("Field", "dawn"), ("Field", "night"), ("Town", "day")]:
            render(layout, time, REPO / ("docs/images/skyline_%s_%s.png" % (layout.lower(), time)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
