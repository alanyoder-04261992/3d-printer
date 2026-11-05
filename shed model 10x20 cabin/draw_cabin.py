"""Draws 'how it goes together.png' from the model (needs: pip install manifold3d numpy pillow).

Run:  python draw_cabin.py
"""

import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import make_cabin as s

SIDING, TRIM, ROOF = (168, 166, 160), (34, 34, 34), (52, 52, 54)
FLOOR, SKID, PORCH = (184, 160, 116), (104, 86, 60), (150, 112, 64)
CEILING = (200, 198, 192)


def camera(az=-35.0, el=28.0):
    """A view looking down at the cabin from in front of the right side (+x) and the porch (-y)."""
    a, e = math.radians(az), math.radians(el)
    view = np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])   # toward the eye
    right = np.cross([0, 0, 1], view)
    right /= np.linalg.norm(right)
    up = np.cross(view, right)
    return np.vstack([right, up, view])


def render(items, size=(1100, 1000), scale=3.2, centre=(0, 0, 80), light=(0.4, -0.3, 0.85), cam=None, fog=0.0):
    """items: [(manifold, colour)]. Flat-shaded, z-buffered, orthographic. fog darkens a face the
    further back it is (by that much at 100 mm behind the centre), so what is seen through an opening
    stands back from what is in front of it."""
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
        shade = shade * (1 - fog * np.clip((100 - sz[t].mean(axis=1)) / 200, 0, 1))
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
    skids = [(s.skid().transform(m), SKID) for m in s.skids_to_cabin()]
    door = p["door"].transform(s.door_to_cabin(0))
    angles = {(sx, sy): s.corner_angle(sx, sy) for sx, sy in s.CORNERS}
    posts = [s.post(sx, xc) for sx, xc in s.post_spots()]
    rails = [s.side_railing(1), s.side_railing(-1), s.front_railing()]
    # left: on the table without its skids, in the read me's order: all four walls on with the door
    # hung, both back corner angles glued (steps 1-8), the railings in the deck (step 9), and above
    # them the three posts, the porch frame, the ceiling and the porch gable waiting to go on in turn
    # (steps 10-12)
    left = [(p["floor"], FLOOR), (door, SIDING)]
    for n in s.WALL_CUTS:
        left += wall_items(p, zone, n)
    left += [(a, TRIM) for a in angles.values()]
    left += [(r, PORCH) for r in rails] + [(q.translate([0, 0, 16]), PORCH) for q in posts]
    left += [(p["porch frame"].translate([0, 0, 30]), TRIM), (p["porch ceiling"].translate([0, 0, 42]), CEILING),
             (p["porch gable"].translate([0, 0, 54]), SIDING)]
    # right: the whole cabin on its skids, the right roof half lifted off straight up
    right = skids + [(p["floor"], FLOOR), (door, SIDING)]
    for n in s.WALL_CUTS:
        right += wall_items(p, zone, n)
    right += [(a, TRIM) for a in angles.values()]
    right += [(r, PORCH) for r in rails] + [(q, PORCH) for q in posts]
    right += [(p["porch frame"], TRIM), (p["porch ceiling"], CEILING), (p["porch gable"], SIDING)]
    right += [(p["roof"].mirror([1, 0, 0]), ROOF), (p["roof"].translate([0, 0, 62]), ROOF)]
    # top right: the finished cabin straight from the front, to show Alan's standard layout (Nov 3 2026):
    # the door right of the middle, one window left of it, the middle post and the one front railing on
    # the left, the way in open on the right. Level, not looking down: tilted even 4 degrees, the roof's
    # top faces, 199 mm long, stood up over the ridge as a dark block like a chimney. Level, the faces
    # all look the same, so it is shaded darker further back: the window's sashes and the door's lites
    # show against the room behind them
    front = right[:-1] + [(p["roof"], ROOF)]
    c = render(front, size=(480, 330), scale=2.75, centre=(0, 0, 50), light=(0.35, -0.8, 0.5), cam=camera(-90.0, 0.0),
               fog=0.4)
    a = render(left, size=(820, 760), scale=2.45, centre=(10, 0, 55))
    b = render(right, size=(820, 760), scale=2.45, centre=(0, 0, 70))
    # bottom: the door seen from above, swung open 90 degrees, to show which side it hangs on (Alan Nov 4
    # 2026, "hinges on the right side")
    cut = s.ZF + s.DOOR_OPEN_H / 2
    plan = [(p["floor"], FLOOR)] + [(m.trim_by_plane([0, 0, -1], -cut), c_) for n in s.WALL_CUTS
                                    for m, c_ in wall_items(p, zone, n)]
    plan += [(q.trim_by_plane([0, 0, -1], -cut), PORCH) for q in posts] + [(r, PORCH) for r in rails]
    plan += [(p["door"].transform(s.door_to_cabin(90)).trim_by_plane([0, 0, -1], -cut), (250, 250, 250))]
    e = door_plan(plan, s.door_to_cabin)
    out = Image.new("RGB", (1640, 1610), "white")
    out.paste(a, (0, 461))
    out.paste(b, (820, 461))
    out.paste(c, (1150, 58))
    out.paste(e, (40, 1215))
    d = ImageDraw.Draw(out)
    d.text((40, 1180), "The door seen from above, swung open (everything cut off at half its height)", fill="black",
           font=font(20, True))
    for i, line in enumerate(["You answered on Nov 4 2026: \"hinges on the right side\".",
                              "Seen from the porch, the door hangs on the right of its doorway,",
                              "next to the right side wall, and swings in toward that wall, about",
                              "102 degrees, until it touches the doorway's right-hand stud.",
                              "The knob and the stop strip are on the left, the latch side.",
                              "The dashed line is the path of the door's latch edge.",
                              "From inside, hanging it (step 1), its pins are on your left."]):
        d.text((560, 1240 + i * 30), line, fill="black", font=font(19))
    d.text((1160, 24), "From the front: your standard layout", fill="black", font=font(20, True))
    for i, line in enumerate(["Door 1.74 ft right of the middle, one window 2.57 ft left.",
                              "One middle post, 0.3 ft left of the middle; the front railing",
                              "runs under the window. The way in, on the right, is open.",
                              "Your Nov 4 answers: walls 93 1/2 in, roof 5/12, 4 in eaves."]):
        d.text((1160, 392 + i * 24), line, fill="black", font=font(17))
    d.text((60, 491), "Going together (skids and roof go on last)", fill="black", font=font(20, True))
    d.text((880, 491), "Finished, one roof half lifted off", fill="black", font=font(20, True))
    d.text((40, 24), "How it goes together", fill="black", font=font(30, True))
    lines = ["1  Hang the door in the loose front wall first, from the inside, its pins on your left: top pin up,",
             "    bottom pin along the slot, let it drop. Once the wall is on the floor the door can't come out.",
             "2  Floor face up on the table. The skids go on last.",
             "3  Back wall, then the front wall with its door: press each straight down until its prongs click.",
             "4  Side walls straight down between them, dry. Rubber bands round the walls; wick thin super glue into",
             "    the top half of the two front joints (none near the floor), then glue a black corner angle at each back corner.",
             "5  Railings into the deck (the front one in the left bay, under the window), glue in the peg holes. Stand the three",
             "    posts in their sockets, dry, tenons toward the left side, except the right corner post's: toward the right side.",
             "6  Glue on each post's top tenon; lower the porch frame onto the posts. Its back ends stand a hair",
             "    (0.2 mm) off the front wall: leave that gap and put a drop of glue in it.",
             "7  Ceiling into the frame, the face that was on the plate down. Porch gable onto the frame, glue on each peg.",
             "8  Lift the cabin onto the skids, cut-off ends at the porch. Roof halves onto the pegs, straight down."]
    for i, line in enumerate(lines):
        d.text((40, 74 + i * 31), line, fill="black", font=font(21))
    out.save(os.path.join(s.HERE, "how it goes together.png"), optimize=True)


if __name__ == "__main__":
    main()
