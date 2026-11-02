"""Draws 'how it goes together.png' from the model (needs: pip install manifold3d numpy pillow).

Run:  python3 draw_barn.py
"""

import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import make_barn as s

SIDING, TRIM, ROOF = (168, 166, 160), (34, 34, 34), (52, 52, 54)
FLOOR, SKID, LOFT = (184, 160, 116), (104, 86, 60), (196, 172, 128)


def camera(az=-35.0, el=28.0):
    """A view looking down at the barn from in front of the door side (+x) and its +y end."""
    a, e = math.radians(az), math.radians(el)
    view = np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])   # toward the eye
    right = np.cross([0, 0, 1], view)
    right /= np.linalg.norm(right)
    up = np.cross(view, right)
    return np.vstack([right, up, view])


def render(items, size=(1100, 1000), scale=3.2, centre=(0, 0, 80), light=(0.4, -0.3, 0.85), cam=None):
    """items: [(manifold, colour)]. Flat-shaded, z-buffered, orthographic."""
    cam = camera() if cam is None else cam
    w, h = size
    img = np.full((h, w, 3), 255, dtype=np.float32)
    zbuf = np.full((h, w), -np.inf)
    L = np.asarray(light, dtype=float)
    L /= np.linalg.norm(L)
    for man, col in items:
        mesh = man.to_mesh()
        v = np.asarray(mesh.vert_properties)[:, :3] - np.asarray(centre)
        t = np.asarray(mesh.tri_verts)
        a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
        n = np.cross(b - a, c - a)
        ln = np.linalg.norm(n, axis=1)
        keep = ln > 1e-12
        n[keep] /= ln[keep, None]
        shade = 0.45 + 0.55 * np.clip(n @ L, 0, 1)
        P = v @ cam.T
        sx = w / 2 + P[:, 0] * scale
        sy = h / 2 - P[:, 1] * scale
        sz = P[:, 2]
        facing = (n @ cam[2]) > 0
        for i in np.nonzero(keep & facing)[0]:
            i0, i1, i2 = t[i]
            xs, ys, zs = sx[[i0, i1, i2]], sy[[i0, i1, i2]], sz[[i0, i1, i2]]
            x0, x1 = max(int(xs.min()), 0), min(int(xs.max()) + 1, w - 1)
            y0, y1 = max(int(ys.min()), 0), min(int(ys.max()) + 1, h - 1)
            if x1 < x0 or y1 < y0:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
            if abs(d) < 1e-9:
                continue
            l0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d
            l1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d
            l2 = 1 - l0 - l1
            inside = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
            if not inside.any():
                continue
            z = l0 * zs[0] + l1 * zs[1] + l2 * zs[2]
            sub = zbuf[y0:y1 + 1, x0:x1 + 1]
            win = inside & (z > sub)
            sub[win] = z[win]
            img[y0:y1 + 1, x0:x1 + 1][win] = np.array(col) * shade[i]
    return Image.fromarray(img.clip(0, 255).astype(np.uint8))


def wall_items(p, zone, name, move=(0, 0, 0)):
    siding, trim = s.two_colour(p[name], zone)
    return [(siding.translate(move), SIDING), (trim.translate(move), TRIM)]


def font(size, bold=False):
    for path in (f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
                 "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def main():
    p = s.build()
    zone = s.trim_zone()
    skids = [(s.skid().transform(m), SKID) for m in s.skids_to_shed()]
    up, lo = p["upper"], p["lower"]
    # left: the long walls and the lofts on them; the far end wall held up above its place
    left = skids + [(p["floor"], FLOOR), (s.loft(1), LOFT), (s.loft(-1), LOFT)]
    left += wall_items(p, zone, "back wall") + wall_items(p, zone, "door wall") + wall_items(p, zone, "end wall 2")
    left += wall_items(p, zone, "end wall 1", (0, 0, 70))
    # right: the whole barn, the roof sheets on the door side lifted off straight up
    right = skids + [(p["floor"], FLOOR), (s.loft(-1), LOFT), (s.loft(1), LOFT)]
    for n in s.WALL_CUTS:
        right += wall_items(p, zone, n)
    right += [(up.mirror([1, 0, 0]), ROOF), (lo.mirror([1, 0, 0]), ROOF),
              (lo.translate([0, 0, 24]), ROOF), (up.translate([0, 0, 52]), ROOF)]
    a = render(left, size=(820, 900), scale=2.9, centre=(0, 0, 95))
    b = render(right, size=(820, 900), scale=2.9, centre=(0, 0, 95))
    out = Image.new("RGB", (1640, 1180), "white")
    out.paste(a, (0, 270))
    out.paste(b, (820, 270))
    d = ImageDraw.Draw(out)
    d.text((40, 24), "How it goes together (no glue)", fill="black", font=font(30, True))
    lines = ["1  Skids push onto the floor's ends. Floor on its skids.",
             "2  Long walls: press each straight down onto the floor's long sides until its prongs click.",
             "3  Lofts: push the back wall straight and drop a loft in at each end, onto both long walls'",
             "    top plates; its lugs go in the notches. The lofts hold the long walls upright.",
             "4  End walls: lower straight down past the lofts, so the hooks on their top corners drop",
             "    into the long walls' corners; press until each prong clicks.",
             "5  Roof: lower sheets straight down onto the pegs on the steep edges, then upper sheets",
             "    onto the pegs halfway up, their tails lapping over the lower sheets."]
    for i, line in enumerate(lines):
        d.text((40, 74 + i * 25), line, fill="black", font=font(19))
    out.save(os.path.join(s.HERE, "how it goes together.png"), optimize=True)


if __name__ == "__main__":
    main()
