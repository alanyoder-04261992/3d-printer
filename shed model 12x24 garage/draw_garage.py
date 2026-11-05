"""Draws 'how it goes together.png' from the model (needs: pip install manifold3d numpy pillow).

Run:  python3 draw_garage.py
"""

import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import make_garage as s

SIDING, TRIM, ROOF = (168, 166, 160), (34, 34, 34), (52, 52, 54)
FLOOR, SKID, DOOR = (184, 160, 116), (104, 86, 60), (214, 212, 206)


def camera(az=-35.0, el=28.0):
    """A view looking down at the garage from in front of the door side (+x) and the roll-up end
    (-y), the way the designer's G.jpg shows it."""
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


def to_screen(pt, size, scale, centre, cam=None):
    """Where a point in garage coords lands in a render() of that size, scale and centre."""
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


def tag(d, xy, text, f):
    """A step number in a circle."""
    x, y = xy
    r = 15
    d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 214, 64), outline="black", width=2)
    d.text((x, y), text, fill="black", font=f, anchor="mm")


def main():
    p = s.build()
    zone = s.trim_zone()
    angles = {(sx, sy): s.corner_angle(sx, sy) for sx, sy in s.CORNERS}
    roof = p["roof"]
    door = p["door"]
    size, scale, centre = (900, 1000), 2.85, (0, 0, 80)
    # left: on the table without its skids, both end walls and the plain side on, the door side
    # with its door hung held up above its place, and a corner angle held out from its corner. No
    # angle is on yet: they go on once all four walls are (step 8)
    lift = (0, 0, 125)
    left = [(p["floor"], FLOOR)]
    left += wall_items(p, zone, "roll-up end") + wall_items(p, zone, "back end") + wall_items(p, zone, "plain side")
    left += wall_items(p, zone, "door side", lift)
    left += [(door.transform(s.door_to_shed(0)).translate(lift), DOOR)]
    left += [(angles[(1, -1)].translate([24, -24, 14]), TRIM)]
    # right: the whole garage on its four skids with an angle on each corner, the door swung in
    # (40 degrees, so it shows through the doorway; much further it hides behind the wall by its
    # hinge), the door-side roof half lifted off straight up, and the roll-up door on its way in or
    # out: lifted, its bottom swung out and pulled away from the doorway, its black handle at the
    # bottom middle
    right = [(sk, SKID) for sk in s.skid_parts()] + [(p["floor"], FLOOR)]
    for n in s.WALL_CUTS:
        right += wall_items(p, zone, n)
    right += [(door.transform(s.door_to_shed(40)), DOOR)]
    right += [(a, TRIM) for a in angles.values()]
    right += [(roof.mirror([1, 0, 0]), ROOF), (roof.translate([0, 0, 45]), ROOF)]
    cur_pose = s.curtain_to_shed(lift=1.0, swing=10.0, out=16.0, drop=4.0)
    cur_w, cur_b = s.curtain_parts()
    right += [(cur_w.transform(cur_pose), DOOR), (cur_b.transform(cur_pose), TRIM)]
    tag11 = cur_pose @ np.array([-24.0, s.ru_y(s.RU_FACE + 2), 34.0, 1.0])
    W, L, ZWT = s.W, s.L, s.ZWT
    # tag 5 on the plain side's inside face, 30 mm under its top, well below the lifted door side
    tags = [[((W / 2 + 2, s.DOOR_YC, s.ZF + 34 + lift[2]), "1"), ((W / 2 - 14, -L / 2 + 45, 1), "2"),
             ((-41, -L / 2 - 2, s.ZF + 40), "3"), ((-6, L / 2, ZWT + 6), "4"), ((-W / 2 + s.WT, 15, ZWT - 30), "5"),
             ((W / 2 + 2, -30, ZWT - 14 + lift[2]), "6"), ((W / 2 + 28, -L / 2 - 28, 50), "8")],
            [((W / 2 - 4, -L / 2 + 30, -6), "9"), ((W / 2 + 2, 30, ZWT + 45 + 6), "10"), (tuple(tag11[:3]), "11")]]
    panels, spots = [], []
    for items, marks in ((left, tags[0]), (right, tags[1])):
        img = render(items, size=size, scale=scale, centre=centre)
        px = [to_screen(pt, size, scale, centre) for pt, _ in marks]
        arr = np.asarray(img)
        ys, xs = np.nonzero((arr < 250).any(axis=2))
        x0 = max(0, min(xs.min(), min(x for x, _ in px) - 20) - 10)
        y0 = max(0, min(ys.min(), min(y for _, y in px) - 20) - 10)
        x1 = min(size[0], max(xs.max(), max(x for x, _ in px) + 20) + 10)
        y1 = min(size[1], max(ys.max(), max(y for _, y in px) + 20) + 10)
        panels.append(img.crop((int(x0), int(y0), int(x1), int(y1))))
        spots.append([((x - int(x0), y - int(y0)), text) for (x, y), (_, text) in zip(px, marks)])
    top = 470
    gap = 40
    width = max(1640, 40 + panels[0].width + gap + panels[1].width + 40)
    out = Image.new("RGB", (width, top + max(pn.height for pn in panels) + 30), "white")
    xs_ = [40, 40 + panels[0].width + gap]
    d = ImageDraw.Draw(out)
    f_tag = font(18, True)
    for pn, xo, sp in zip(panels, xs_, spots):
        out.paste(pn, (xo, top))
        for (x, y), text in sp:
            tag(d, (x + xo, y + top), text, f_tag)
    d.text((40, 24), "How it goes together", fill="black", font=font(30, True))
    # close-up, top right: the roll-up doorway from in front, the door lifted by its handle and coming out
    cam = camera(-62.0, 12.0)
    csize, cscale, ccentre = (620, 430), 4.4, (0, -s.L / 2 - 6, 36)
    near = s.box(-s.W / 2 - 2, s.W / 2 + 2, -s.L / 2 - 5, -s.L / 2 + 30, -5, s.ZWT + 1)
    ru_sid, ru_trim = s.two_colour(p["roll-up end"], zone)
    close = [(ru_sid ^ near, SIDING), (ru_trim ^ near, TRIM), (p["floor"] ^ near, FLOOR)]
    up_pose = s.curtain_to_shed(lift=1.0, swing=9.0, out=9.0, drop=4.4)
    close += [(cur_w.transform(up_pose), DOOR), (cur_b.transform(up_pose), TRIM)]
    img_c = render(close, size=csize, scale=cscale, centre=ccentre, cam=cam)
    handle_pt = up_pose @ np.array([0.0, s.ru_y(s.HDL_U2), s.HDL_Z0 + s.HDL_HT / 2, 1.0])
    hx, hy = to_screen(handle_pt[:3], csize, cscale, ccentre, cam)
    arr = np.asarray(img_c)
    ys_, xs_ = np.nonzero((arr < 250).any(axis=2))
    box_c = (max(0, xs_.min() - 8), max(0, ys_.min() - 8), min(csize[0], xs_.max() + 8), min(csize[1], ys_.max() + 8))
    img_c = img_c.crop(box_c)
    cx0 = out.width - img_c.width - 30
    out.paste(img_c, (cx0, 40))
    d.rectangle([cx0 - 6, 34, cx0 + img_c.width + 6, 40 + img_c.height + 6], outline=(150, 150, 150), width=1)
    tag(d, (cx0 + hx - box_c[0] - 30, 40 + hy - box_c[1] + 26), "11", f_tag)
    d.line([(cx0 + hx - box_c[0] - 16, 40 + hy - box_c[1] + 18), (cx0 + hx - box_c[0] - 2, 40 + hy - box_c[1] + 4)],
           fill="black", width=2)
    cap = "11  The roll-up door coming out, lifted by its black handle"
    d.text((out.width - 30 - d.textlength(cap, font=font(16)), 40 + img_c.height + 12), cap, fill="black", font=font(16))
    lines = ["1  Hang the door in the loose door side first: top pin up into the head, push up, swing the bottom",
             "    out along the slot in the sill, drop it in. Once the wall is on the floor the door can't come off.",
             "2  Floor face up on the table (skids after the angles).",
             "3  Roll-up end over the end with five short notches across the middle of its edge; press over its two prongs,",
             "    under the sides of the doorway, till each clicks. The roll-up door goes in last (11).",
             "4  Back end over the other end the same way.",
             "5  Plain side straight down between the end walls; press over each of its three prongs.",
             "6  Door side, door hung, straight down the same way, pressing on the wall, not the door.",
             "7  Two rubber bands round the walls pull the corners shut.",
             "8  A black corner angle into the recesses at each corner, dry first, then glued one at a time; bands off once set.",
             "9  Skids: lift the garage onto the four skids, their pegs into the holes in the floor. Never glue the outer two.",
             "10 Roof: each half onto its three pegs (two on the gables, one in the middle of the long wall).",
             "11 Roll-up door, last, from outside, roof on or off: hold it by its handle, its bottom about 6 mm (1/4 in) out and",
             "    its top leaning in a little more; push it up under the trim till it stops, let it down about 1 mm, push the bottom",
             "    in over the white threshold and let go. Lifted a bit and let go, it must snap back down. Out: lift it by the",
             "    handle till it stops, down a hair, bottom toward you, drop."]
    for i, line in enumerate(lines):
        d.text((40, 70 + i * 23), line, fill="black", font=font(18))
    out.save(os.path.join(s.HERE, "how it goes together.png"), optimize=True)


if __name__ == "__main__":
    main()
