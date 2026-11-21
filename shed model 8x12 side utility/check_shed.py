"""Checks the shed model fits together before anything is printed.

Run:  python3 check_shed.py
Each line says what it proved. Anything that fails is marked FAIL.
"""

import math
import sys

import manifold3d as m3
import numpy as np

import make_shed as s

M = m3.Manifold

BED = 220.0
fails = 0


def report(ok, words):
    global fails
    fails += 0 if ok else 1
    print(("ok   " if ok else "FAIL ") + words)


def overlap(a, b):
    return (a ^ b).volume()


RND = m3.JoinType.Round
MIT = m3.JoinType.Miter


def layers(top):
    """The slicer's layers: 0.25 mm first, then 0.2."""
    out, z = [(0.0, 0.25)], 0.25
    while z < top:
        out.append((z, z + 0.2))
        z += 0.2
    return out


def as_printed(m):
    """Roughly what the slicer lays down for a piece in print position: each layer is the
    section at its middle with anything narrower than a 0.42 mm line rounded off, stood up the
    layer's height. A feature that only exists in the CAD shape goes missing here."""
    top = m.bounding_box()[5]
    out = []
    for z0, z1 in layers(top):
        cs = m.slice((z0 + z1) / 2).offset(-0.21, RND).offset(0.21, RND)
        if cs.area() > 0:
            out.append(M.extrude(cs, z1 - z0).translate([0, 0, z0]))
    return s.union(out)


def printed_in_shed(piece, mat, region):
    """as_printed() of the part of a piece inside region (shed coords), printed lying the way
    mat lays it on the bed, and put back where it goes in the shed."""
    R = np.column_stack([np.array(mat, dtype=float), np.zeros(3)])
    bb = piece.transform(R).bounding_box()
    part = (piece ^ region).transform(R).translate([-bb[0], -bb[1], -bb[2]])
    back = np.column_stack([np.array(mat, dtype=float).T, np.zeros(3)])
    return as_printed(part).translate([bb[0], bb[1], bb[2]]).transform(back)


def scan(cs, ys):
    """Where each line y = const crosses a section: an array of (x0, x1) per line."""
    edges = []
    for poly in cs.to_polygons():
        pts = np.asarray(poly)
        edges.append(np.column_stack([pts, np.roll(pts, -1, axis=0)]))
    if not edges:
        return [np.zeros((0, 2)) for _ in ys]
    E = np.vstack(edges)
    out = []
    for y in ys:
        hit = ((E[:, 1] <= y) & (E[:, 3] > y)) | ((E[:, 3] <= y) & (E[:, 1] > y))
        e = E[hit]
        xs = np.sort(e[:, 0] + (y - e[:, 1]) * (e[:, 2] - e[:, 0]) / (e[:, 3] - e[:, 1]))
        out.append(xs.reshape(-1, 2))
    return out


def overhangs(cs, prev, step=0.2):
    """What of this layer hangs past the layer under it by more than 45 degrees and isn't a
    bridge. A bit of layer counts as a bridge if, in some direction, it runs across from
    something printed on the layer below to something else printed on the layer below (held at
    both ends), no more than 20 mm. Returns (left over section, longest bridge in mm)."""
    sup = prev.offset(0.22, RND)
    free = cs - sup
    if free.area() < 0.01:
        return free, 0.0
    held = cs ^ sup
    bridged, longest = [], 0.0
    for ang in (0, 45, 90, 135):
        f, h = free.rotate(ang), held.rotate(ang)
        b = f.bounds()
        ys = np.arange(b[1] + step / 2, b[3], step)
        rects = []
        for y, fi, hi in zip(ys, scan(f, ys), scan(h, ys)):
            for x0, x1 in fi:
                left = np.any(np.abs(hi[:, 1] - x0) < 0.05)
                right = np.any(np.abs(hi[:, 0] - x1) < 0.05)
                if left and right and x1 - x0 <= 20:
                    rects.append([(x0, y - step / 2), (x1, y - step / 2), (x1, y + step / 2), (x0, y + step / 2)])
                    longest = max(longest, x1 - x0)
        if rects:
            bridged.append(m3.CrossSection(rects, m3.FillRule.Positive).rotate(-ang))
    if bridged:
        free = free - m3.CrossSection.batch_boolean(bridged, m3.OpType.Add).offset(0.05, RND)
    return free, longest


p = s.build()
body, roof, door, trim = p["body"], p["roof"], p["door"], p["door_trim"]
door_all = door + trim

WALLS = list(s.WALL_CUTS)
zone = s.trim_zone()
flat = {name: s.wall_parts(p, name, zone) for name in WALLS}
angle_flat = s.angle_prints()


def corner_name(sx, sy):
    return f"({'+' if sx > 0 else '-'},{'+' if sy > 0 else '-'})"


# 1. every printed piece is one solid piece and fits the bed
for name, part in ([("floor", p["floor"])] + [(n, s.union(flat[n])) for n in WALLS] +
                   [("roof half", s.roof_to_print(roof))] +
                   [("corner angle " + corner_name(sx, sy), a) for (sx, sy), a in zip(s.CORNERS, angle_flat)] +
                   [("door", door_all), ("skids", p["skids"]), ("fit test new corner", p["fit corner"]),
                    ("fit test door and roof peg", p["fit"])]):
    bb = part.bounding_box()
    size = (bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2])
    pieces = len(part.decompose())
    expect = {"skids": 2, "fit test new corner": 4, "fit test door and roof peg": 4}.get(name, 1)
    report(pieces == expect, f"{name}: {pieces} solid piece(s), expected {expect}")
    report(max(size[0], size[1]) <= BED and size[2] <= BED,
           f"{name}: {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm fits the {BED:.0f} mm bed")

# 1b. the walls and floor are the whole body, cut apart cleanly, and print well lying flat
pieces = [p["floor"]] + [p[n] for n in WALLS]
v = abs(body.volume() - sum(x.volume() for x in pieces))
report(v < 0.01, f"floor and four walls add up to the whole body ({v:.4f} mm3 left over)")
worst = max(overlap(a, b) for i, a in enumerate(pieces) for b in pieces[i + 1:])
report(worst < 0.001, f"no two of them overlap ({worst:.4f} mm3)")
wall_set = s.union([p[n] for n in WALLS])
v = 0
for dx, dy in ((0.14, 0), (-0.14, 0), (0, 0.14), (0, -0.14)):
    v = max(v, overlap(p["floor"].translate([dx, dy, 0]), wall_set))
report(v < 0.0001, f"the walls sit round the floor with {s.FIT} mm round every post and prong and "
                   f"{s.FLOOR_CLR} mm inside the skirts (moved 0.14 mm it still clears: {v:.4f} mm3)")


# 1a. the snap joints. Each wall stands on the floor, the floor holds it in, out and along, and
# its barbs hold it down. (The corner angles tie the corners together; see 1c.)
def toward(name, d):
    """Move d mm out from the middle of the shed, square to the wall."""
    axis, sign = s.WALL_SIDE[name]
    t = [0.0, 0.0, 0.0]
    t[axis] = sign * d
    return t


def along(name, d):
    t = [0.0, 0.0, 0.0]
    t[1 - s.WALL_SIDE[name][0]] = d
    return t


fl = p["floor"]
# the floor with room for the barbs to pass, as if each leg were bent out of the way: what is
# left in the way of a wall coming down is only the snap itself
barb_room = []
for n in WALLS:
    for ac in s.prong_spots(n):
        (a0, a1), _ = s.prong_spans(ac)
        barb_room.append(s.wall_box(n, a0 - s.FIT, a1 + s.FIT, -s.FIT, s.BARB, -1, s.ZF + 1))
fl_open = fl - s.union(barb_room)
ends = s.union([p["end wall 1"], p["end wall 2"]])
for n in WALLS:
    w = p[n]
    v = overlap(w.translate([0, 0, -0.1]), fl)
    report(v > 1, f"{n} stands on the floor (lowered 0.1 mm it runs into it: {v:.1f} mm3)")
    v = overlap(w.translate([0, 0, 0.3]), fl)
    report(v > 0.05, f"{n}: its {len(s.prong_spots(n))} prongs' barbs hold it down (lifted 0.3 mm they "
                     f"meet their ledges: {v:.2f} mm3)")
    vi, vo = overlap(w.translate(toward(n, -0.3)), fl), overlap(w.translate(toward(n, 0.3)), fl)
    va = min(overlap(w.translate(along(n, d)), fl) for d in (0.3, -0.3))
    report(min(vi, vo, va) > 0.05, f"{n}: the floor holds its foot in ({vi:.1f}), out ({vo:.1f}) and "
                                   f"along ({va:.1f} mm3 when moved 0.3 mm)")
    # lowered on from above: the end walls first onto the bare floor, then the long walls
    # between them
    worst = 0
    for dz in (0.25, 0.5, 1, 2, 3, 4, 6, 8, 12, 20, 40, 80, 140):
        moved = w.translate([0, 0, dz])
        worst = max(worst, overlap(moved, fl_open))
        if n in ("door wall", "back wall"):
            worst = max(worst, overlap(moved, ends))
    report(worst < 0.001, f"{n} goes on straight down from above"
                          f"{' between the end walls' if n in ('door wall', 'back wall') else ''}, "
                          f"nothing in the way but the barbs ({worst:.4f} mm3)")
leg = s.LEG_ROOT - (s.LEDGE_Z - s.FIT)
strain = 1.5 * s.PRONG_T * s.CATCH / leg ** 2
room = s.SLOT_U - (s.BARB + s.PRONG_T + s.CATCH)
report(strain < 0.02 and room >= s.FIT - 0.001,
       f"each prong leg bends {s.CATCH:.2f} mm to let its barb through: {strain * 100:.1f}% strain on a "
       f"{leg:.1f} mm leg {s.PRONG_T} mm thick (PLA takes about 2%), with {room:.2f} mm to spare in its slot")
# the same snap as it will print: walls lying inside face down and the floor upside down, in
# 0.25/0.2 mm layers, with anything thinner than a line rounded off (as_printed). The barb must
# still reach under the ledge, with the ledge just above it so it can spring in.
for n in WALLS:
    region = s.union([s.wall_box(n, s.prong_spans(ac)[0][0] - 1, s.prong_spans(ac)[1][1] + 1, -1, s.SD, -1, s.ZF + 1)
                      for ac in s.prong_spots(n)] +
                     [s.wall_box(n, s.prong_spans(ac)[1][0] - 1, s.prong_spans(ac)[0][1] + 1, -1, s.SD, -1, s.ZF + 1)
                      for ac in s.prong_spots(n)])
    pw = printed_in_shed(p[n], s.WALL_TO_PRINT[n], region)
    pf = printed_in_shed(fl, s.FLOOR_TO_PRINT, region)
    rest = overlap(pw, pf)
    held = overlap(pw.translate([0, 0, 0.3]), pf)
    # measure one barb: how far in it reaches past the slot's inside wall, and the gap over it
    (a0, a1), _ = s.prong_spans(s.prong_spots(n)[-1])
    def u_of(man):
        axis, sign = s.WALL_SIDE[n]
        bb = man.bounding_box()
        half = (s.W / 2, s.L / 2)[axis]
        lo, hi = (bb[axis], bb[axis + 3]) if sign > 0 else (-bb[axis + 3], -bb[axis])
        return lo - (half - s.WT), hi - (half - s.WT)
    zc = s.LEDGE_Z - s.FIT
    barb = pw ^ s.wall_box(n, a0 + 0.5, a1 - 0.5, -1, s.BARB - 0.05, zc - 0.15, zc - 0.05)
    wall_in = pf ^ s.wall_box(n, a0 + 0.5, a1 - 0.5, -0.5, s.BARB + 0.5, s.LEDGE_Z + 0.4, s.LEDGE_Z + 0.6)
    catch = u_of(wall_in)[1] - u_of(barb)[0]
    # with the foot pushed out against its stops: the stop prints to a layer line, the slot's
    # outside wall is where it's drawn
    play = s.SLOT_U - (round((s.STOP_U - 0.25) / 0.2) * 0.2 + 0.25)
    out_catch = catch - play
    top = (pw ^ s.wall_box(n, a0 + 0.5, a1 - 0.5, -1, s.BARB - s.FIT - 0.05, -1, s.ZF - 1)).bounding_box()[5]
    ledge = (pf ^ s.wall_box(n, a0 + 0.5, a1 - 0.5, 0.05, s.BARB - s.FIT - 0.05, -1, s.ZF)).bounding_box()[2]
    report(rest < 0.01 and held > 0.05 and out_catch >= 0.29 and 0 < ledge - top < 0.45,
           f"{n} as printed: each barb reaches {catch:.2f} mm under its ledge ({out_catch:.2f} with the foot "
           f"pushed out against its stops), with {ledge - top:.2f} mm over it to spring in; lifted 0.3 mm the "
           f"printed barbs catch ({held:.2f} mm3), and seated nothing rubs ({rest:.3f} mm3)")
for n in WALLS:
    siding, trim = flat[n]
    bb = s.union(flat[n]).bounding_box()
    # the bed face must run the whole inside face: the full length less the two mitres, and
    # nearly the full height of the wall
    foot = s.union(flat[n]).trim_by_plane([0, 0, -1], -0.2)
    fbb = foot.bounding_box()
    report(fbb[3] - fbb[0] > (bb[3] - bb[0]) - 2 * (s.WT + s.PROUD) - 0.1 and fbb[4] - fbb[1] > 0.9 * (bb[4] - bb[1]),
           f"{n} lies flat on its framing ({foot.volume() / 0.2:.0f} mm2 on the bed)")
    # layer by layer (slicer layers: 0.25 then 0.2), nothing may stick out more than 0.22 mm
    # past the layer under it (45 degrees) unless it is a bridge held at both ends, 20 mm or
    # less: the siding between studs, the skirt between posts, the plate over the slot round each
    # prong's leg, the prong legs. Allowed: under 5 mm2 a layer of small bits (the undersides of
    # the roof pegs).
    whole = s.union(flat[n])
    worst, longest, prev = 0.0, 0.0, None
    for z0, z1 in layers(bb[5]):
        cs = whole.slice((z0 + z1) / 2)
        if prev is not None:
            left, span = overhangs(cs, prev)                # every bridge counted is 20 mm or less
            longest = max(longest, span)
            worst = max(worst, left.area())
        prev = cs
    report(worst < 5,
           f"{n} has nothing steeper than 45 degrees that isn't a bridge of 20 mm or less ({worst:.1f} mm2 "
           f"worst layer)")
    # the first two layers must have nothing narrower than one 0.4 mm line (a knife edge on
    # the bed gets dropped or blobs into a joint)
    thin = max((c - c.offset(-0.2, RND).offset(0.2, RND)).area()
               for c in (whole.slice(0.125), whole.slice(0.35)))
    report(thin < 2, f"{n}: no knife edges on the bed ({thin:.2f} mm2 thinner than a line in the first two layers)")
    tb = trim.bounding_box()
    sb = siding.bounding_box()
    if n == "back wall":
        report(trim.volume() == 0, f"{n}: no filament-2 trim left on it (its corner boards are the corner angles "
                                   f"now), so it prints in one colour")
    else:
        report(trim.volume() > 0 and abs(tb[5] - (s.WT + s.PROUD)) < 0.01 and tb[2] > s.WT - 0.01,
               f"{n}: trim is {trim.volume() / 1000:.2f} cm3, all of it the top {s.PROUD} mm "
               f"({tb[2]:.2f} to {tb[5]:.2f} mm), so the colour only changes on the last layers")
    # nothing in filament 1 above the siding's face (5.10 drawn, its top layer prints 4.85 to
    # 5.05): the vent's louvres are recessed now, so the colour changes once
    report(sb[5] <= s.WT + 1e-6,
           f"{n}: nothing in filament 1 stands above the siding's face ({sb[5]:.3f} mm; its top layer prints at 5.05)")
    if n in ("door wall", "back wall"):
        v = p[n].trim_by_plane([0, 0, 1], s.ZWT + 0.001).volume()
        report(v == 0, f"{n}: nothing above the wall plates (the gable corners go with the end walls)")
same = (s.union(flat["end wall 1"]) ^ s.union(flat["end wall 2"])).volume()
v1 = s.union(flat["end wall 1"]).volume()
report(abs(same - v1) < 0.01, "the two end walls print the same, so end wall.stl serves for both")
# the floor prints upside down: its face is on the bed, and nothing hangs over more than 45
# degrees (the joists, bands and slots all stand straight up from it)
ff = s.to_print(s.FLOOR_TO_PRINT, [fl])[0]
fbb = ff.bounding_box()
foot = ff.slice(0.125).area()
report(foot > 0.95 * (fbb[3] - fbb[0]) * (fbb[4] - fbb[1]) - 400,
       f"the floor prints face down ({foot:.0f} mm2 on the bed)")
worst, prev = 0.0, None
for z in [0.125] + [0.35 + 0.2 * k for k in range(int(fbb[5] / 0.2))]:
    if z > fbb[5]:
        break
    cs = ff.slice(z)
    if prev is not None:
        worst = max(worst, (cs - prev.offset(0.22, m3.JoinType.Miter, 10)).area())
    prev = cs
report(worst < 0.5, f"the floor has nothing hanging over ({worst:.2f} mm2 worst layer)")

# 1c. the corner angles (Alan, Nov 3 2026): a black L at each corner, glued into a recess in
# both walls. It must sit on both recess floors and touch nothing else, cover the mitre, and
# clear the roof, the other trim and the door.
def to_corner(sx, sy):
    """Matrix from shed coords to a corner's own (u, v, z): u out from the long wall's siding
    face, v out from the end wall's (the inverse of make_shed.corner_frame)."""
    return np.array([[sx, 0, 0, -s.W / 2], [0, sy, 0, -s.L / 2], [0, 0, 1, 0]], dtype=float)


def square(u0, u1, v0, v1):
    return m3.CrossSection.square([u1 - u0, v1 - v0]).translate([u0, v0])


def reach_area(a, wall_set, sx, sy, zs, r):
    """Area of wall within r of the angle, on horizontal sections at zs, leaving out the strips
    under the angle's inside faces, which sit on the recess floors by design."""
    ra, rb = s.angle_reach()
    floors = square(-s.POCKET_D - r - 0.01, -s.POCKET_D, -ra - r - 0.01, -1.3) + \
        square(-rb - r - 0.01, -1.3, -s.POCKET_D - r - 0.01, -s.POCKET_D)
    T = to_corner(sx, sy)
    at, wt = a.transform(T), wall_set.transform(T)
    return max(((at.slice(z).offset(r, RND) ^ wt.slice(z)) - floors).area() for z in zs)


def directions(d):
    """The 26 moves of d mm to the corners, edges and faces of a cube."""
    out = []
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            for k in (-1, 0, 1):
                if i or j or k:
                    n = math.sqrt(i * i + j * j + k * k)
                    out.append([d * i / n, d * j / n, d * k / n])
    return out


angles = {c: s.corner_angle(*c) for c in s.CORNERS}
ra, rb = s.angle_reach()
trim_all = s.union(s.trims())
zs = (1.0, s.ZF, 40.0, 80.0, s.ZWT - 1, s.ZWT + 1)
for (sx, sy), a in angles.items():
    cn = corner_name(sx, sy)
    ln, en = s.corner_walls(sx, sy)
    lw_, ew_ = p[ln], p[en]
    pair = s.union([lw_, ew_])
    # seated: into neither wall, and pushed only 0.005 mm into either recess floor it meets it all
    # along (about 1.1 mm3 when it is right on it), so it is down on both floors, not just near them
    v0 = max(overlap(a, lw_), overlap(a, ew_))
    in_l = overlap(a.translate([-sx * 0.005, 0, 0]), lw_)
    in_e = overlap(a.translate([0, -sy * 0.005, 0]), ew_)
    report(v0 < 0.001 and in_l > 0.5 and in_e > 0.5,
           f"corner angle {cn} sits in the recesses of the {ln} and {en}: into neither ({v0:.4f} mm3), on both "
           f"recess floors (pushed 0.005 mm in it meets them: {in_l:.2f} and {in_e:.2f} mm3)")
    # clear by 0.09 everywhere but the recess floors: the fillet is c off the chamfer, square to it,
    # worked out from the constants, and the legs' edges POCKET_CLR from the ends of the recesses.
    # So the test isn't empty, at c + 0.02 the fillet must reach the chamfer
    c = (s.CORNER_CHAMFER - s.ANGLE_FILLET) / math.sqrt(2)
    near = reach_area(a, pair, sx, sy, zs, 0.09)
    fil = reach_area(a, pair, sx, sy, zs, c + 0.02)
    report(c >= 0.09 and near < 1e-4 and fil > 0.001,
           f"corner angle {cn} touches the walls only on the recess floors: nothing else within 0.09 mm "
           f"({near:.5f} mm2 on sections from the foot to above the plates; the fillet is {c:.3f} mm off the "
           f"chamfer, and at {c + 0.02:.3f} mm it reaches it, {fil:.3f} mm2)")
    # either wall's foot 0.15 mm in or out, the angle on its recess floor going with it
    worst = 0.0
    for n, other in ((ln, ew_), (en, lw_)):
        for d in (0.15, -0.15):
            worst = max(worst, overlap(a.translate(toward(n, d)), other))
    t_in = s.POCKET_CLR + 0.1
    tight = overlap(a.translate(toward(ln, -t_in)), ew_)
    report(worst < 0.001 and tight > 0.001,
           f"corner angle {cn} still misses the other wall with either wall's foot 0.15 mm in or out "
           f"({worst:.4f} mm3; at {t_in:.2f} mm in it would meet it, {tight:.3f} mm3)")
    # covers the corner on both faces, from the foot up: measured from the siding's outer corner
    # (u = v = 0), and past the joint where the mitre meets the chamfer, which is what shows
    T = to_corner(sx, sy)
    at = a.transform(T)
    cover_l, cover_e = 99.0, 99.0
    for z in (0.3, s.ZF, 50.0, s.ZWT - 0.6):
        sec = at.slice(z)
        lp, ep = sec ^ square(-s.POCKET_D, 1, -30, 1), sec ^ square(-30, 1, -s.POCKET_D, 1)
        cover_l = min(cover_l, -lp.bounds()[1] if lp.area() > 0 else 0)
        cover_e = min(cover_e, -ep.bounds()[0] if ep.area() > 0 else 0)
    seam_v = (lw_.transform(T).slice(50.0) ^ square(-3, 1, -3, 1)).bounds()[3]   # the long wall's last bit
    seam_u = (ew_.transform(T).slice(50.0) ^ square(-3, 1, -3, 1)).bounds()[2]   # the end wall's
    face = (at ^ s.box(s.ANGLE_T - s.POCKET_D - 0.01, 1, -30, 1, -1, 400)).bounding_box()
    report(cover_l >= 3 and cover_e >= 3 and at.bounding_box()[2] == 0,
           f"corner angle {cn} covers the corner by {cover_l:.2f} mm along the long wall and {cover_e:.2f} mm along "
           f"the end wall from the siding's outer corner ({cover_l + seam_v:.2f} and {cover_e + seam_u:.2f} mm past the "
           f"joint at the chamfer), from its foot (level with the bottom of the skirts) to {s.ZWT - face[5]:.2f} mm "
           f"under the top of the wall plates")
    # the roof: 0.2 under it, square to it; still clear with the roof 0.15 mm lower
    rf = roof if sx > 0 else roof.mirror([1, 0, 0])
    nrm = [sx * math.sin(s.ALPHA), 0, math.cos(s.ALPHA)]
    v19 = overlap(a, rf.translate([-0.19 * c for c in nrm]))
    v21 = overlap(a, rf.translate([-0.21 * c for c in nrm]))
    vlow = overlap(a, rf.translate([0, 0, -0.15]))
    report(overlap(a, rf) == 0 and v19 < 1e-5 and vlow < 1e-5 and v21 > 1e-3,
           f"corner angle {cn} is 0.2 mm under the roof, square to it, across both legs (the roof moved 0.19 mm "
           f"toward it still clears, at 0.21 it meets it: {v21:.3f} mm3), and still clears the roof 0.15 mm lower")
    # the other trim (the gable band ends 0.15 short of it)
    v = max(overlap(a.translate(d), trim_all) for d in directions(0.1))
    report(v < 1e-5, f"corner angle {cn} is at least 0.1 mm from all the other trim ({v:.5f} mm3 moved 0.1 mm any way)")
v = max(overlap(door_all.transform(s.door_to_shed(deg)), p["angles"]) for deg in range(0, 100, 2))
report(v == 0, f"the door swings clear of the corner angles from shut to 98 degrees ({v:.4f} mm3)")
pa = [s.on_bed(a) for a in angle_flat]
same = max((pa[0] - pa[3]).volume(), (pa[3] - pa[0]).volume(), (pa[1] - pa[2]).volume(), (pa[2] - pa[1]).volume())
mir = s.on_bed(pa[0].mirror([1, 0, 0]))
hand = max((mir - pa[1]).volume(), (pa[1] - mir).volume())
report(same < 0.001 and hand < 0.001 and (pa[0] - pa[1]).volume() > 1,
       f"the angles are two mirror pairs: (+,+) prints the same as (-,-) and (+,-) as (-,+), each pair the "
       f"other's mirror image")
# printed lying on the long-face leg's outside face: nothing over 45 degrees, nothing in mid-air
for (sx, sy), a in list(zip(s.CORNERS, angle_flat))[:2]:
    bb = a.bounding_box()
    worst, prev = 0.0, None
    for z0, z1 in layers(bb[5]):
        cs = a.slice((z0 + z1) / 2)
        if prev is not None:
            worst = max(worst, (cs - prev.offset(0.22, RND)).area())
        prev = cs
    nl = len(layers(bb[5] - 0.001))
    report(worst < 0.001 and abs(bb[5] - s.ANGLE_UP) < 1e-9 and a.slice(0.125).area() > 0.95 * bb[4] * (bb[3] - 0.05),
           f"corner angle {corner_name(sx, sy)} prints on its long-face leg's outside face "
           f"({a.slice(0.125).area():.0f} mm2 on the plate), {bb[5]:.2f} mm tall ({nl} layers), with nothing hanging "
           f"past the layer under it ({worst:.4f} mm2)")

# the same as printed: the walls and the angle each cut into their own print's layers, with anything
# thinner than a line rounded off. The recess floors print on the 4.65 layer, 0.054 deeper than
# drawn, and the chamfer and the fillet both come out stepped, the end wall's steps across the
# angle's. Pushed onto both printed floors the angle must still miss the chamfer.
for sx, sy in s.CORNERS:
    ln, en = s.corner_walls(sx, sy)
    region = s.box(-12, 2, -12, 2, 30, 60).transform(s.corner_frame(sx, sy))
    T = to_corner(sx, sy)
    pl = printed_in_shed(p[ln], s.WALL_TO_PRINT[ln], region).transform(T)
    pe = printed_in_shed(p[en], s.WALL_TO_PRINT[en], region).transform(T)
    pa = printed_in_shed(angles[(sx, sy)], s.angle_to_print(sx), region).transform(T)
    floor_u = (pl ^ s.box(-3, 1, -3.3, -2.0, 40, 50)).bounding_box()[3]
    floor_v = (pe ^ s.box(-3.3, -2.0, -3, 1, 40, 50)).bounding_box()[4]
    du = floor_u - (pa ^ s.box(-1, 1, -3.3, -2.0, 40, 50)).bounding_box()[0]
    dv = floor_v - (pa ^ s.box(-3.3, -2.0, -1, 1, 40, 50)).bounding_box()[1]
    seated = pa.translate([du, dv, 0])
    v = overlap(seated, s.union([pl, pe]))
    on_l, on_e = overlap(seated.translate([-0.01, 0, 0]), pl), overlap(seated.translate([0, -0.01, 0]), pe)
    # how close the fillet's steps come to the walls' steps, on a section away from the recess floors.
    # The nearest are corners of steps, where the printed lines are rounded, so the real gap is wider;
    # a 0.85 fillet would have its steps touching the long wall's, and a 1.0 one runs into the end wall's
    away = square(-3, -0.6, -3, -0.6)
    ws, fs = s.union([pl, pe]).slice(45.0) ^ away, seated.slice(45.0) ^ away
    lo, hi = 0.0, 0.5
    for _ in range(14):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if (fs.offset(mid, RND) ^ ws).area() > 1e-7 else (mid, hi)
    report(v < 1e-4 and on_l > 0.05 and on_e > 0.05 and lo >= 0.03,
           f"corner angle {corner_name(sx, sy)} as printed: pushed {-du:.3f} and {-dv:.3f} mm in, onto both printed "
           f"recess floors ({floor_u:.3f}, {floor_v:.3f}), it runs "
           + (f"into neither wall ({max(v, 0):.4f} mm3 over 30 mm); " if v < 1e-4 else f"{v:.3f} mm3 into the walls over 30 mm; ")
           + f"its fillet's steps stay {lo:.3f} mm clear of the walls' steps")

# each wall's recesses, as printed: the floor on the 4.65 layer and the siding round it on 5.05,
# and no edge sharper than square where the chamfer meets the mitre and the recess floor
for n in WALLS:
    axis, sign = s.WALL_SIDE[n]
    for sx, sy in s.CORNERS:
        if (sx, sy)[axis] != sign:
            continue
        T = to_corner(sx, sy)
        Ti = s.corner_frame(sx, sy)
        region = s.box(-12, 2, -12, 2, 15, 35).transform(Ti)
        pw = printed_in_shed(p[n], s.WALL_TO_PRINT[n], region).transform(T)
        k = axis                                               # 0: depth is u, 1: depth is v
        def probe(a0, a1):
            b = [-3, 1, -3, 1, 20, 30]
            b[2 * (1 - k)], b[2 * (1 - k) + 1] = a0, a1
            return (pw ^ s.box(*b)).bounding_box()[3 + k] + s.WT
        floor_z, face_z = probe(-3.3, -2.0), probe(-6.5, -4.5)
        # square edges: the wall's horizontal section at the corner, the angle at each corner of it
        wl = p[n].transform(T)
        sharp = 180.0
        for z in (3.0, 30.0, 60.0, s.ZWT - 1):
            for poly in (wl.slice(z) ^ square(-3, 1, -3, 1)).to_polygons():
                P = np.asarray(poly)
                for i in range(len(P)):
                    a_, b_, c_ = P[i - 1], P[i], P[(i + 1) % len(P)]
                    if min(b_) < -2.9 or max(b_) > 0.9:            # the cut-off edge of the window
                        continue
                    e1, e2 = a_ - b_, c_ - b_
                    turn = (b_ - a_)[0] * (c_ - b_)[1] - (b_ - a_)[1] * (c_ - b_)[0]
                    if turn > 1e-9:                             # a convex corner of the wall
                        cosang = np.dot(e1, e2) / np.linalg.norm(e1) / np.linalg.norm(e2)
                        sharp = min(sharp, math.degrees(math.acos(max(-1, min(1, cosang)))))
        # slivers: anything thinner than a 0.42 line in the print's layers near the corner, out to the
        # nearest siding groove (a mitred opening, so it keeps square corners and finds only slivers)
        near = s.box(-1.45, 1, -10, 1, -1, 400) if k == 0 else s.box(-10, 1, -1.45, 1, -1, 400)
        part = (p[n] ^ near.transform(Ti))
        R = np.column_stack([np.array(s.WALL_TO_PRINT[n], dtype=float), np.zeros(3)])
        wb = p[n].transform(R).bounding_box()
        pp = part.transform(R).translate([-wb[0], -wb[1], -wb[2]])
        thin = max((c - c.offset(-0.21, MIT, 2).offset(0.21, MIT, 2)).area()
                   for c in (pp.slice((z0 + z1) / 2) for z0, z1 in layers(pp.bounding_box()[5])))
        nd = round((face_z - floor_z) / 0.2)
        report(abs(floor_z - 4.65) < 1e-6 and abs(face_z - 5.05) < 1e-6 and sharp >= 89.9 and thin < 0.01,
               f"{n} at corner {corner_name(sx, sy)}: as printed the recess floor is at {floor_z:.2f} mm and the siding "
               f"round it at {face_z:.2f} ({nd} layers deep); the sharpest corner of the wall there is {sharp:.0f} degrees "
               f"({'no knife edge' if sharp >= 89.9 else 'a knife edge'}); at most {thin:.3f} mm2 a layer thinner than "
               f"a line out to the nearest groove")

# the gable vents: frame flush, louvres in a recess whose floor is on a layer line with 3 layers of
# siding under it, the louvres printing on every layer up to the siding's top one and no higher
for n, side in (("end wall 1", 1), ("end wall 2", -1)):
    rbb = s.gable_vent(side)[1].bounding_box()
    region = s.box(rbb[0] - 1, rbb[3] + 1, -s.BIG, s.BIG, rbb[2] - 1, rbb[5] + 1)
    pw = printed_in_shed(p[n], s.WALL_TO_PRINT[n], region)
    field = s.box(rbb[0] + 0.3, rbb[3] - 0.3, -s.BIG, s.BIG, rbb[2] + 0.3, rbb[5] - 0.3)
    area = (rbb[3] - rbb[0] - 0.6) * (rbb[5] - rbb[2] - 0.6)
    fill = {}
    for z0, z1 in layers(5.3):
        if z0 >= 3.6:
            ya, yb = sorted([side * (s.L / 2 - s.WT + z0), side * (s.L / 2 - s.WT + z1)])
            fill[round(z0, 2)] = (pw ^ field ^ s.box(-s.BIG, s.BIG, ya, yb, -s.BIG, s.BIG)).volume() / (area * (z1 - z0))
    under = [fill[z] for z in (3.65, 3.85, 4.05)]
    louvres = [fill[z] for z in (4.25, 4.45, 4.65, 4.85)]
    # the gaps between the louvres, on each layer's section the way the slicer cuts it: none
    # narrower than a 0.42 line, which would print shut (a mitred opening keeps square corners, so
    # only thin gaps go missing), and the narrowest one down the vent's middle
    R = np.column_stack([np.array(s.WALL_TO_PRINT[n], dtype=float), np.zeros(3)])
    wb = p[n].transform(R).bounding_box()
    def to_bed(m):
        return m.transform(R).translate([-wb[0], -wb[1], -wb[2]])
    pp = to_bed(p[n] ^ region)
    fb = to_bed(s.gable_vent(side)[1] ^ s.box(-s.BIG, s.BIG, -s.L / 2, s.L / 2, -s.BIG, s.BIG)).bounding_box()
    hole = square(fb[0], fb[3], fb[1], fb[4])
    shut, narrow = 0.0, 99.0
    for z0, z1 in layers(5.05 - 0.001):
        if z0 >= 4.25 - 1e-9:
            gaps = hole - pp.slice((z0 + z1) / 2)
            shut = max(shut, (gaps - gaps.offset(-0.21, MIT, 2).offset(0.21, MIT, 2)).area())
            for x0, x1 in scan(gaps.rotate(90), [(fb[0] + fb[3]) / 2])[0]:
                narrow = min(narrow, x1 - x0)
    report(abs(s.WT - s.VENT_DEPTH - 4.25) < 1e-9 and min(under) > 0.999 and 0.2 < min(louvres) and max(louvres) < 0.95
           and all(a >= b for a, b in zip(louvres, louvres[1:])) and fill[5.05] < 1e-9 and shut < 0.01,
           f"{n}'s vent: the louvres' recess floor is on the 4.25 layer line with 3 full layers of siding under it; "
           f"the louvres fill {', '.join(f'{f * 100:.0f}' for f in louvres)} % of the 4 layers above it, narrowing "
           f"toward the face, the gaps between them are {narrow:.2f} mm or wider ({shut:.3f} mm2 narrower than a "
           f"line), and nothing of the vent prints above the siding's top layer")

# the short corner in the fit test goes together the same way, and its 20 mm stub of angle sits
# in the recesses the way a whole one does
lw, ew, cf = s.corner_test({n: p[n] for n in WALLS}, fl)
stub = s.angle_stub()
ok = (overlap(lw, ew) < 0.001 and overlap(lw, cf) < 0.001 and overlap(ew, cf) < 0.001
      and overlap(lw.translate([0, 0, 0.3]), cf) > 0.05 and overlap(ew.translate([0, 0, 0.3]), cf) > 0.05
      and overlap(stub, s.union([lw, ew, cf])) < 0.001
      and overlap(stub.translate([-0.005, 0, 0]), lw) > 0.1 and overlap(stub.translate([0, -0.005, 0]), ew) > 0.1
      and reach_area(stub, s.union([lw, ew]), 1, 1, (1.0, 10.0, 19.0), 0.09) < 1e-4)
report(ok, "the fit test's short corner snaps onto its bit of floor like the real ones, and the stub of corner angle "
           "sits on both recess floors and touches nothing else")

# every plate: inside the bed, 3 mm or more between parts, and on the two-colour plates the prime
# tower's corner (x 165 to 200, y 195 up) kept clear by 3 mm
for fname, plates in (("1 fit test.3mf", s.fit_plates(p)), ("2 all plates.3mf", s.all_plates(p, flat))):
    for i, (pname, items) in enumerate(plates):
        boxes, fils = [], set()
        for name, parts, (x, y), *own in items:
            bb = s.union([m for _, m, _ in parts]).bounding_box()
            boxes.append((x, y, x + bb[3] - bb[0], y + bb[4] - bb[1]))
            fils |= {f for _, _, f in parts}
        def gap(b, c):
            return max(c[0] - b[2], b[0] - c[2], c[1] - b[3], b[1] - c[3])
        inside = all(b[0] >= 0 and b[1] >= 0 and b[2] <= BED and b[3] <= BED for b in boxes)
        apart = min((gap(b, c) for j, b in enumerate(boxes) for c in boxes[j + 1:]), default=BED)
        tower = min(gap(b, (165, 195, 200, BED + 50)) for b in boxes) if len(fils) > 1 else BED
        report(inside and apart >= 3 and tower >= 3,
               f"{fname} plate {i + 1} ({pname}): "
               + (f"{len(boxes)} parts on the bed, {apart:.1f} mm apart" if len(boxes) > 1 else "one part on the bed")
               + (f", {tower:.1f} mm from the prime tower" if len(fils) > 1 else ", one filament, no tower"))

# 2. the roof halves sit on the body and the pegs go in their holes
right = roof
left = roof.mirror([1, 0, 0])
for name, half in (("door-side roof half", right), ("back roof half", left)):
    v = overlap(body, half)
    report(v < 0.01, f"{name} sits on the gable ends without cutting into the body ({v:.4f} mm3)")
report(overlap(right, left) < 0.001, "the two roof halves do not overlap at the ridge")
# a roof half moved down 0.3 mm must hit the body (so it really rests on it)
v = overlap(body, right.translate([0, 0, -0.3]))
report(v > 0.5, f"lowered 0.3 mm a roof half runs into the gable tops, so it is resting on them ({v:.1f} mm3)")
# slid 1 mm along the length or down the slope, a peg must stop it
for dx, dy, words in ((0, 1.0, "along the building"), (1.0, 0, "down the slope")):
    v = overlap(body, right.translate([dx, dy, 0.05]))
    report(v > 0.05, f"slid 1 mm {words}, a roof half is held by its pegs ({v:.2f} mm3)")
# lifted straight up it comes free
v = overlap(body, right.translate([0, 0, 2.0]))
report(v == 0, "lifted 2 mm straight up, a roof half is clear of the pegs")

# 3. the door swings out to about 90 degrees and no further, and not inward
closed = None
last_free = 0
for deg in range(0, 121, 2):
    d = door_all.transform(s.door_to_shed(deg))
    v = overlap(body, d)
    if deg == 0:
        closed = v
    if v < 0.01:
        last_free = deg
    elif deg < 90:
        report(False, f"door hits the building at {deg} degrees ({v:.3f} mm3)")
        break
report(closed is not None and closed < 0.01, f"closed door fits the opening ({closed:.4f} mm3)")
report(last_free >= 90, f"door swings out freely to {last_free} degrees")
v = overlap(body, door_all.transform(s.door_to_shed(-2)))
report(v > 0.05, f"the stop inside the latch side keeps it from swinging in ({v:.2f} mm3 at -2 degrees)")

# 4. the door goes in: top pin up in its hole, bottom tilted out, then swung in along the slot
lift = s.DOOR_TOP_GAP - 0.05
top_z = s.ZF + s.DOOR_BOTTOM_GAP + s.DOOR_H
worst = 0
for frac in np.linspace(0, 1, 21):
    out = 3.5 * (1 - frac)                      # how far the bottom is outside at this step
    ang = math.atan2(out, s.DOOR_H)
    m = s.door_to_shed(0)
    m[2, 3] += lift
    # tilt about the line along y through the top pin's entry point
    c, sn = math.cos(ang), math.sin(ang)
    R = np.array([[c, 0, -sn], [0, 1, 0], [sn, 0, c]])
    piv = np.array([s.AXIS_X, 0, top_z + lift])
    R2 = R @ m[:, :3]
    t2 = R @ (m[:, 3] - piv) + piv
    v = overlap(body, door_all.transform(np.column_stack([R2, t2])))
    worst = max(worst, v)
report(worst < 0.05, f"door goes in tilted at the bottom and swings in along the floor slot (worst {worst:.3f} mm3)")
m = s.door_to_shed(0)
m[2, 3] += lift
v = overlap(body, door_all.transform(m))
report(v < 0.01, "lifted 0.55 mm the door still clears the head of the opening")

# 5. the skids fit under the floor frame with the joists down in their notches
sk = [s.skid().transform(mat) for mat in s.skids_to_shed()]
for i, k in enumerate(sk):
    v = overlap(body, k)
    report(v < 0.01, f"skid {i + 1} fits under the floor ({v:.4f} mm3)")
    v = overlap(body, k.translate([0, 0, 0.3]))
    report(v > 1, f"skid {i + 1} is really touching the joists ({v:.1f} mm3 when raised 0.3)")
    v = min(overlap(fl, k.translate(t)) for t in ([0.3, 0, 0], [-0.3, 0, 0], [0, 0.3, 0], [0, -0.3, 0]))
    report(v > 0.05, f"skid {i + 1} is held in place by its pegs in the floor ({v:.2f} mm3 when moved 0.3 mm)")

# 6. heights at full size, as a sanity check against the shop numbers
inch = 1 / s.S
report(abs(s.WALL_H * inch - 93.5) < 0.01, f"walls {s.WALL_H * inch:.1f} in floor to plate top (shop: 93 1/2 in)")
report(abs((s.ZPK - s.ZWT) / (s.W / 2) - 5 / 12) < 1e-9, "roof is 5/12")
report(abs(s.DOOR_OPEN_W * inch - 48.25) < 0.01 and abs(s.DOOR_OPEN_H * inch - 76.5) < 0.01,
       "door opening 48 1/4 x 76 1/2 in")

print()
print("all checks passed" if fails == 0 else f"{fails} check(s) failed")
sys.exit(1 if fails else 0)
