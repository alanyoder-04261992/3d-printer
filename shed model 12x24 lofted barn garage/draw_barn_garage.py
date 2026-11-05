"""Draws 'how it goes together.png' from the model (needs: pip install manifold3d numpy pillow).

Run:  python draw_barn_garage.py
"""

import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import make_barn_garage as s

SIDING, TRIM, ROOF = (168, 166, 160), (34, 34, 34), (52, 52, 54)
FLOOR, SKID, LOFT = (184, 160, 116), (104, 86, 60), (196, 172, 128)
DOOR = (214, 212, 206)
CURTAIN = (226, 224, 218)


def curtain_moved(m, theta=0.0, du=0.0, dz=0.0, lift=0.0):
    """The roll-up curtain m (garage coords, seated) lifted, swung theta degrees bottom-out about its front
    at the mouth, then moved du out from the wall and dz up, as it comes out (garage coords)."""
    u0 = s.L / 2 - s.WT                                  # u (out from the inside face) = -y - u0
    a = math.radians(theta)
    pu, pz = s.RU_FACE, s.MOUTH + lift
    c, sn = math.cos(a), math.sin(a)
    # (u, z) -> (c (u - pu) - sn (z - pz) + pu + du, sn (u - pu) + c (z - pz) + pz + dz), with u = -y - u0
    M = np.array([[1, 0, 0, 0],
                  [0, c, sn, 0],
                  [0, -sn, c, 0]], dtype=float)
    yu = -(pu + u0)
    t = np.array([0, yu - (c * yu + sn * pz) - du, pz - (-sn * yu + c * pz) + dz])
    M[:, 3] = t
    return m.translate([0, 0, lift]).transform(M)


def camera(az=-35.0, el=26.0):
    """A view looking down at the garage from in front of the door side (+x) and the roll-up end (-y)."""
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
        if len(t) == 0:
            continue
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


def to_screen(pt, size, scale, centre, cam=None):
    """Where a point in garage coords lands in a render() of this size, scale and centre."""
    cam = camera() if cam is None else cam
    P = (np.asarray(pt, dtype=float) - np.asarray(centre)) @ cam.T
    return size[0] / 2 + P[0] * scale, size[1] / 2 - P[1] * scale


def wall_items(p, zone, name, move=(0, 0, 0)):
    siding, trim = s.two_colour(p[name], zone)
    return [(siding.translate(move), SIDING), (trim.translate(move), TRIM)]


def font(size, bold=False):
    for path in (f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
                 "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def tag(d, xy, n, f):
    """A numbered circle at xy."""
    x, y = xy
    r = 17
    d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 214, 64), outline="black", width=2)
    d.text((x, y), str(n), fill="black", font=f, anchor="mm")


def main():
    p = s.build()
    zone = s.trim_zone()
    skids = [(k, SKID) for _, k in s.placed_skids()]
    up, lo = p["upper"], p["lower"]
    angles = {(sx, sy): s.corner_angle(sx, sy) for sx, sy in s.CORNERS}
    door = p["door"]
    cw, cb = p["curtain white"], p["curtain black"]
    # left: pulled apart upward in the order it goes together: the skids under the floor, the long
    # walls on it (the door hung in the door side, swung open), the lofts over their places, the
    # roll-up end and the back end over theirs, a corner angle held out from its corner, and last the
    # roll-up door held out in front of its doorway, top leaned in, ready to go up
    LOFT_UP, RU_UP, BACK_UP, SKID_DOWN = 22, 34, 62, 22
    left = [(k.translate([0, 0, -SKID_DOWN]), c) for k, c in skids] + [(p["floor"], FLOOR)]
    left += wall_items(p, zone, "plain side") + wall_items(p, zone, "door side")
    left += [(door.transform(s.door_to_shed(35)), DOOR)]
    left += [(s.loft(1).translate([0, 0, LOFT_UP]), LOFT), (s.loft(-1).translate([0, 0, LOFT_UP]), LOFT)]
    left += wall_items(p, zone, "roll-up end", (0, 0, RU_UP)) + wall_items(p, zone, "back end", (0, 0, BACK_UP))
    left += [(angles[(1, -1)].translate([12, -12, 0]), TRIM)]
    CUR_OUT = 16
    left += [(curtain_moved(m, 7, CUR_OUT, RU_UP - 3.0), col) for m, col in ((cw, CURTAIN), (cb, TRIM))]
    # right: the whole garage on its skids with an angle on each corner, the roof sheets on the
    # door side lifted off straight up, and the roll-up door part way out: lifted by its handle until it
    # stopped, its bottom swung out and let drop so its top has come out under the trim
    right = skids + [(p["floor"], FLOOR), (s.loft(-1), LOFT), (s.loft(1), LOFT)]
    for n in s.WALL_CUTS:
        right += wall_items(p, zone, n)
    right += [(door.transform(s.door_to_shed(0)), DOOR)]
    right += [(curtain_moved(m, 8, 3.0, -(s.TONGUE_UP + s.BUMP_H + 1.2 + 0.6), lift=1.2), col)
              for m, col in ((cw, CURTAIN), (cb, TRIM))]
    right += [(a, TRIM) for a in angles.values()]
    right += [(up.mirror([1, 0, 0]), ROOF), (lo.mirror([1, 0, 0]), ROOF),
              (lo.translate([0, 0, 26]), ROOF), (up.translate([0, 0, 52]), ROOF)]
    size, scale = (820, 900), 3.0
    c_left, c_right = (0, 0, 62), (0, 0, 66)
    a = render(left, size=size, scale=scale, centre=c_left)
    b = render(right, size=size, scale=scale, centre=c_right)
    out = Image.new("RGB", (1640, 1295), "white")
    top = 395
    out.paste(a, (0, top))
    out.paste(b, (820, top))
    # inset, top right: the roll-up doorway close up from in front, the door part way out by its handle
    ins = [(p["floor"], FLOOR)] + wall_items(p, zone, "roll-up end")
    ins += [(curtain_moved(m, 8, 3.0, -(s.TONGUE_UP + s.BUMP_H + 1.2 + 0.6), lift=1.2), col)
            for m, col in ((cw, CURTAIN), (cb, TRIM))]
    isz, isc, ic, icam = (600, 360), 3.5, (4, -s.L / 2, 36), camera(-58, 16)
    out.paste(render(ins, size=isz, scale=isc, centre=ic, cam=icam), (1030, 30))
    d = ImageDraw.Draw(out)
    f_tag = font(20, True)
    hx, hy = to_screen((0, -s.L / 2 - 3 - 8, s.RAIL_Z0 - 3.5), isz, isc, ic, icam)
    d.line([(1030 + hx - 70, 30 + hy + 26), (1030 + hx - 6, 30 + hy + 4)], fill="black", width=2)
    d.text((1030 + hx - 130, 30 + hy + 18), "handle", fill="black", font=font(18, True))
    d.text((1040, 8), "The roll-up door coming out: lifted by its handle till it stops, let down a hair,", fill="black",
           font=font(16))
    d.text((1040, 392), "bottom pulled out and let drop, so its top comes out under the trim.", fill="black", font=font(16))

    def at(pt, offset=(0, 0), right_view=False):
        x, y = to_screen(pt, size, scale, c_right if right_view else c_left)
        return x + offset[0] + (820 if right_view else 0), y + offset[1] + top
    W, L, ZF, ZWT = s.W, s.L, s.ZF, s.ZWT
    tag(d, at((W / 2 + 4, s.DOOR_YC + 6, ZF + 30)), 1, f_tag)                       # door
    tag(d, at((-W / 4, -L / 2 + 4, ZF), (-6, 14)), 2, f_tag)                        # floor
    tag(d, at((-W / 2, 40, ZWT - 8)), 3, f_tag)                                     # plain side
    tag(d, at((W / 2, 72, ZWT - 22), (14, 0)), 4, f_tag)                            # door side, behind the window
    tag(d, at((W / 2 - 8, L / 2 - 14, ZWT + LOFT_UP + 6), (22, -6)), 5, f_tag)       # lofts
    tag(d, at((-W / 4, -L / 2, ZWT + RU_UP + 20), (-24, 0)), 6, f_tag)              # roll-up end
    tag(d, at((W / 4, L / 2, ZWT + BACK_UP + 22), (0, -10)), 7, f_tag)              # back end
    tag(d, at((W / 2 + 12, -L / 2 - 12, 35), (24, 0)), 9, f_tag)                    # corner angle
    tag(d, at((W / 2 - 8, 60, -SKID_DOWN - 3), (10, 22)), 10, f_tag)               # skids
    tag(d, at((W / 2, 0, s.ZKN + 52), (30, -10), right_view=True), 11, f_tag)        # roof
    tag(d, at((-W / 4 - 6, -L / 2 - CUR_OUT, ZF + RU_UP + 12), (-26, 0)), 12, f_tag)   # roll-up door
    tag(d, at((0, -L / 2 - 6, ZF + 2), (0, 26), right_view=True), 12, f_tag)          # roll-up door, coming out
    d.text((40, 22), "How it goes together", fill="black", font=font(30, True))
    lines = ["1  Door: hang it in the loose door side from the inside (top pin up in the head, push up, swing the bottom",
             "    pin out along the slot in the sill, drop it in). Leave it there: once the wall is on the floor it can't come off.",
             "2  Floor face up on the table (skids after the angles).    3  Plain side, then  4  door side: press straight down",
             "    over each of their four prongs until each clicks.",
             "5  Lofts: push the plain side straight and lower a loft in at each end, its lugs into the notches in the top plates.",
             "6  Roll-up end, then  7  back end: straight down past the lofts; press over each of their two prongs until it clicks.",
             "8  Band the corners (not drawn).   9  Glue on the corner angles, foot on the table, the higher leg on the end wall.",
             "10  Skids: inner (notched) under the joists, outer (flat) under the long edges, notched edge out. Never glue the outer two.",
             "11  Roof: lower sheets onto the pegs on the steep edges, then upper sheets, their tails over the lower sheets.",
             "12  Roll-up door, last, from outside, roof on or off: hold it by its handle, its bottom about 6 mm (1/4 in)",
             "    out and its top leaning in a little more; push it up under the trim till it stops, let it down about 1 mm,",
             "    push the bottom in over the white threshold and let go. Lifted a bit and let go, it must snap back down.",
             "    To take it out (right): lift it by the handle till it stops, down a hair, bottom toward you, drop."]
    for i, line in enumerate(lines):
        d.text((40, 70 + i * 27), line, fill="black", font=font(19))
    out.save(os.path.join(s.HERE, "how it goes together.png"), optimize=True)


if __name__ == "__main__":
    main()
