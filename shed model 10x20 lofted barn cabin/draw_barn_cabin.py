"""Draws 'how it goes together.png' from the model (needs: pip install manifold3d numpy pillow).

Run:  python draw_barn_cabin.py
"""

import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import make_barn_cabin as s

SIDING, TRIM, ROOF = (168, 166, 160), (34, 34, 34), (52, 52, 54)
FLOOR, SKID, LOFT = (184, 160, 116), (104, 86, 60), (196, 172, 128)
PORCH = (150, 112, 70)           # the brown posts and railings


def camera(az=-35.0, el=28.0):
    """A view looking down at the cabin from in front of its porch (-y) and its right side (+x);
    az -125 looks from in front of the porch and its left side (-x), az -70 more from the front."""
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
        if man.is_empty():
            continue
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


def porch_items(p, zone, lift=(0, 0, 0, 0, 0)):
    """The porch parts, each raised its own amount: posts, frame, ceiling, porch gable (the
    railings are glued to the deck)."""
    dp, df, dc, dg = lift[:4]
    out = [(r, PORCH) for r in p["railings"]]
    out += [(q.translate([0, 0, dp]), PORCH) for q in p["posts"]]
    out += [(p["porch frame"].translate([0, 0, df]), TRIM), (p["porch ceiling"].translate([0, 0, dc]), SIDING)]
    sid, trm = s.two_colour(p["porch gable"], zone)
    out += [(sid.translate([0, 0, dg]), SIDING), (trm.translate([0, 0, dg]), TRIM)]
    return out


def door_plan(items, door_to, swing=90, scale=4.5, box=(-30.0, 75.0, -97.0, -15.0)):
    """The front of the building seen from straight above, every part cut off at half the door's height
    (items, already cut), with the door's swing drawn over it as a dashed arc: the path of its latch
    edge from shut to swung in swing degrees about its hinge pins. Alan Nov 4 2026, "hinges on the right
    side": they are at the doorway's right-hand jamb as seen from the porch, and the door swings in
    toward the right side wall. The Cabin and the Lofted Barn Cabin share this door and this drawing."""
    x0, x1, y0, y1 = box
    w, h = int((x1 - x0) * scale), int((y1 - y0) * scale)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    im = render(items, size=(w, h), scale=scale, centre=(cx, cy, 0), light=(0.3, -0.4, 0.85), cam=camera(-90.0, 89.9))
    d = ImageDraw.Draw(im)
    px = lambda q: (w / 2 + (q[0] - cx) * scale, h / 2 - (q[1] - cy) * scale)
    pin = door_to(0) @ np.array([0.0, 0.0, s.DOOR_R, 1.0])
    edge = [door_to(swing * j / 24) @ np.array([-s.HINGE * s.DOOR_W, 0.0, s.DOOR_R, 1.0]) for j in range(25)]
    for k in range(0, 24, 2):
        d.line([px(edge[k]), px(edge[k + 1])], fill=(0, 0, 0), width=2)
    for text, q in (("room", (-24, -30)), ("porch", (-24, -78)), ("right", (s.W / 2 + 3, -38)),
                    ("side wall", (s.W / 2 + 3, -43))):
        d.text(px(q), text, fill="black", font=font(16))
    hx, hy = px(pin)
    d.text((hx - 24, hy + 16), "hinges", fill="black", font=font(16))
    return im


def main():
    p = s.build()
    zone = s.trim_zone()
    skids = [(s.skid().transform(m), SKID) for m in s.skids_to_shed()]
    up, lo = p["upper"], p["lower"]
    door = (p["door"].transform(s.door_to_shed(0)), SIDING)
    angles = {(sx, sy): s.corner_angle(sx, sy) for sx, sy in s.CORNERS}
    # left, seen from the front left so the left side's window shows: on the table without its skids,
    # the front wall on with its door, the left side on, the right side coming down, the lofts held
    # above it (they rest on both side walls' top plates, so they go in after the right side: drawn
    # lower than it, they looked as if they went in first, audit Nov 3 2026), the back wall held up
    # above its place and one back angle held out from its corner; the porch's parts lifted up over
    # the deck
    left = [(p["floor"], FLOOR), door, (s.loft(-1).translate([0, 0, 44]), LOFT), (s.loft(1).translate([0, 0, 44]), LOFT)]
    left += wall_items(p, zone, "front wall") + wall_items(p, zone, "left side")
    left += wall_items(p, zone, "right side", (0, 0, 20)) + wall_items(p, zone, "back wall", (0, 0, 70))
    left += [(angles[(-1, 1)].translate([-9, 9, 70]), TRIM)]
    left += porch_items(p, zone, (12, 30, 44, 58))
    # right, seen from the front right: the whole cabin on its skids, the roof sheets on the right side
    # lifted off straight up
    right = skids + [(p["floor"], FLOOR), (s.loft(-1), LOFT), (s.loft(1), LOFT), door]
    for n in s.WALL_CUTS:
        right += wall_items(p, zone, n)
    right += [(a, TRIM) for a in angles.values()] + porch_items(p, zone)
    right += [(up.mirror([1, 0, 0]), ROOF), (lo.mirror([1, 0, 0]), ROOF),
              (lo.translate([0, 0, 24]), ROOF), (up.translate([0, 0, 52]), ROOF)]
    a = render(left, size=(820, 800), scale=2.8, centre=(0, 0, 70), cam=camera(-125.0, 24.0), light=(-0.4, -0.3, 0.85))
    b = render(right, size=(820, 800), scale=2.8, centre=(0, 0, 70), cam=camera(-70.0, 18.0))
    # bottom: the door seen from above, swung open 90 degrees, to show which side it hangs on (Alan Nov 4
    # 2026, "hinges on the right side", for the Cabin's door, which this is)
    cut = s.ZF + s.DOOR_OPEN_H / 2
    plan = [(p["floor"], FLOOR)] + [(m.trim_by_plane([0, 0, -1], -cut), c_) for n in s.WALL_CUTS
                                    for m, c_ in wall_items(p, zone, n)]
    plan += [(q.trim_by_plane([0, 0, -1], -cut), PORCH) for q in p["posts"]] + [(r, PORCH) for r in p["railings"]]
    plan += [(p["door"].transform(s.door_to_shed(90)).trim_by_plane([0, 0, -1], -cut), (250, 250, 250))]
    e = door_plan(plan, s.door_to_shed)
    out = Image.new("RGB", (1640, 1640), "white")
    out.paste(a, (0, 450))
    out.paste(b, (820, 450))
    out.paste(e, (40, 1245))
    d = ImageDraw.Draw(out)
    d.text((40, 1210), "The door seen from above, swung open (everything cut off at half its height)", fill="black",
           font=font(20, True))
    for i, line in enumerate(["You answered on Nov 4 2026, for the Cabin: \"hinges on the right side\".",
                              "The two models share the door, so it hangs the same way here.",
                              "Seen from the porch, the door hangs on the right of its doorway,",
                              "next to the right side wall, and swings in toward that wall, about",
                              "102 degrees, until it touches the doorway's right-hand stud.",
                              "The knob and the stop strip are on the left, the latch side.",
                              "The dashed line is the path of the door's latch edge.",
                              "From inside, hanging it (step 1), its pins are on your left."]):
        d.text((560, 1270 + i * 30), line, fill="black", font=font(19))
    d.text((40, 24), "How it goes together", fill="black", font=font(30, True))
    d.text((40, 428), "Going together, seen from the front left", fill=(90, 90, 90), font=font(19, True))
    d.text((860, 428), "Finished, seen from the front right (right roof sheets lifted off)", fill=(90, 90, 90),
           font=font(19, True))
    lines = ["1  Door first, into the loose front wall from the inside, its pins on your left: top pin up into the head,",
             "    swing the bottom in along the little slot in the threshold, drop it. It stays in for good.",
             "2  Floor face up on the table. Front wall onto the line of pockets 4 ft back from the front edge,",
             "    door side out, its two end columns into the corner notches. Press over its 2 prongs until they click.",
             "3  Left side, then right side: straight down behind the front wall's end columns until their prongs click.",
             "4  Push both side walls straight, then the lofts: one just behind the front wall, one at the back, lugs into the notches.",
             "5  Back wall straight down past the back loft. Two rubber bands round the walls.",
             "6  Front corners: front loft out, wick thin super glue into the top half of each hairline joint (none",
             "    near the floor), front loft back in. Back corners: glue a black angle in each, then take the bands off.",
             "7  Porch: railings glued into the deck first (one down each side, one across the left bay under the window;",
             "    the right bay, in front of the door, is the way in), then the three posts dry in their sockets, the frame",
             "    glued onto the posts' tops and the front wall, the ceiling dropped in, the porch gable on its two pegs.",
             "8  Skids under the floor, front ends (corners cut off) under the porch. Roof: lower sheets, then upper."]
    for i, line in enumerate(lines):
        d.text((40, 74 + i * 26), line, fill="black", font=font(19))
    out.save(os.path.join(s.HERE, "how it goes together.png"), optimize=True)


if __name__ == "__main__":
    main()
