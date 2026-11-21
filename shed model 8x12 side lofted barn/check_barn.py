"""Checks the barn model fits together before anything is printed.

Run:  python3 check_barn.py
Each line says what it proved. Anything that fails is marked FAIL.
"""

import itertools
import math
import os
import subprocess
import sys
import types

import manifold3d as m3
import numpy as np

import make_barn as s

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


def print_part(piece, mat, region):
    """The part of a piece inside region (barn coords), where it lies in the piece's print."""
    R = np.column_stack([np.array(mat, dtype=float), np.zeros(3)])
    bb = piece.transform(R).bounding_box()
    return (piece ^ region).transform(R).translate([-bb[0], -bb[1], -bb[2]])


def floating(piece):
    """Layer by layer as the slicer lays a piece down (as_printed: anything thinner than a line
    dropped), the worst area with nothing under it within 45 degrees. A strip too thin to print
    under something wider shows up here as the wider part starting in mid-air."""
    worst, prev, z_prev = 0.0, None, 0.0
    for z0, z1 in layers(piece.bounding_box()[5]):
        zm = (z0 + z1) / 2
        cs = piece.slice(zm).offset(-0.21, RND).offset(0.21, RND)
        if prev is not None:
            worst = max(worst, (cs - prev.offset(1.1 * (zm - z_prev), RND)).area())
        prev, z_prev = cs, zm
    return worst


def printed_top(h):
    """Where a face at height h in a part's print position ends up: the top of the last layer
    whose middle is under it."""
    return max(z1 for z0, z1 in layers(h + 1) if (z0 + z1) / 2 < h)


def printed_in_shed(piece, mat, region):
    """as_printed() of the part of a piece inside region (barn coords), printed lying the way
    mat lays it on the bed, and put back where it goes in the barn."""
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


def overhangs(cs, prev, step=0.2, reach=0.22):
    """What of this layer hangs past the layer under it by more than 45 degrees (more than reach,
    a little over the height between them) and isn't a bridge. A bit of layer counts as a bridge
    if, in some direction, it runs across from something printed on the layer below to something
    else printed on the layer below (held at both ends), no more than 20 mm. Returns (left over
    section, longest bridge in mm)."""
    sup = prev.offset(reach, RND)
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


def worst_overhang(piece):
    """Layer by layer, the worst area that hangs out more than 45 degrees and isn't a bridge
    held at both ends of 20 mm or less. Something that starts in mid-air counts too. Returns
    (worst mm2, longest bridge mm)."""
    bb = piece.bounding_box()
    worst, longest, prev, z_prev = 0.0, 0.0, None, 0.0
    for z0, z1 in layers(bb[5]):
        cs = piece.slice((z0 + z1) / 2)
        if prev is not None:
            left, span = overhangs(cs, prev, reach=1.1 * ((z0 + z1) / 2 - z_prev))
            longest = max(longest, span)
            worst = max(worst, left.area())
        prev, z_prev = cs, (z0 + z1) / 2
    return worst, longest


p = s.build()
body, upper, lower, door, trim = p["body"], p["upper"], p["lower"], p["door"], p["door_trim"]
door_all = door + trim
WALLS = list(s.WALL_CUTS)
LONGS, ENDS = ["door wall", "back wall"], ["end wall 1", "end wall 2"]
zone = s.trim_zone()
flat = {name: s.to_print(s.WALL_TO_PRINT[name], s.two_colour(p[name], zone)) for name in WALLS}
up_flat = s.panel_to_print(upper, s.UPPER_A, s.UPPER_B)
lo_flat = s.panel_to_print(lower, s.LOWER_A, s.LOWER_B)
loft_flat = s.to_print(s.LOFT_TO_PRINT, [p["loft"]])[0]

# 1. every printed piece is one solid piece and fits the bed
angle_flat = s.corner_prints(s.corner_angle)
cap_flat = s.corner_prints(s.corner_cap)
for name, part in ([("floor", p["floor"])] + [(n, s.union(flat[n])) for n in WALLS] +
                   [("upper roof", up_flat), ("lower roof", lo_flat), ("loft", loft_flat), ("door", door_all),
                    ("skids", p["skids"]), ("fit test", p["fit"])] +
                   [("corner angle, " + n, m) for n, m in angle_flat] + [("corner cap, " + n, m) for n, m in cap_flat]):
    bb = part.bounding_box()
    size = (bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2])
    pieces = len(part.decompose())
    expect = {"skids": 2, "fit test": 8}.get(name, 1)
    report(pieces == expect, f"{name}: {pieces} solid piece(s), expected {expect}")
    report(max(size[0], size[1]) <= BED and size[2] <= BED,
           f"{name}: {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm fits the {BED:.0f} mm bed")

# 1b. the walls and floor are the whole body, cut apart cleanly
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
# its barbs hold it down. The corners are tied by the glued corner angles (section 7).
def toward(name, d):
    """Move d mm out from the middle of the barn, square to the wall."""
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
ends = s.union([p[n] for n in ENDS])
longs = s.union([p[n] for n in LONGS])
lofts = [s.loft(1), s.loft(-1)]
loft_set = s.union(lofts)
DROPS = [0.1 * k for k in range(1, 11)] + [1 + 0.5 * k for k in range(1, 279)]   # every 0.5 mm to 140 mm


def sweep(piece, others, path):
    """The worst overlap of piece with others at each step of a path of moves."""
    return max(overlap(piece.translate(t), others) for t in path)


for n in LONGS + ENDS:
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
    # lowered on from above in the read me's order: the long walls onto the bare floor, then
    # (after the lofts) the end walls past the long walls' mitred ends
    others = fl_open if n in LONGS else s.union([fl_open, longs, loft_set])
    worst = sweep(w, others, [[0, 0, dz] for dz in DROPS])
    report(worst < 0.001, f"{n} goes on straight down from 140 mm up"
                          f"{', past the lofts and the long walls mitred ends' if n in ENDS else ''}, "
                          f"nothing in the way but the barbs ({worst:.4f} mm3)")
leg = s.LEG_ROOT - (s.LEDGE_Z - s.FIT)
strain = 1.5 * s.PRONG_T * s.CATCH / leg ** 2
room = s.SLOT_U - (s.BARB + s.PRONG_T + s.CATCH)
report(strain < 0.02 and room >= s.FIT - 0.001,
       f"each prong leg bends {s.CATCH:.2f} mm to let its barb through: {strain * 100:.1f}% strain on a "
       f"{leg:.1f} mm leg {s.PRONG_T} mm thick (PLA takes about 2%), with {room:.2f} mm to spare in its slot")
# the same snap as it will print: walls lying inside face down and the floor upside down, in
# 0.25/0.2 mm layers, with anything thinner than a line rounded off (as_printed)
for n in WALLS:
    region = s.union([s.wall_box(n, s.prong_spans(ac)[0][0] - 1, s.prong_spans(ac)[1][1] + 1, -1, s.SD, -1, s.ZF + 1)
                      for ac in s.prong_spots(n)] +
                     [s.wall_box(n, s.prong_spans(ac)[1][0] - 1, s.prong_spans(ac)[0][1] + 1, -1, s.SD, -1, s.ZF + 1)
                      for ac in s.prong_spots(n)])
    pw = printed_in_shed(p[n], s.WALL_TO_PRINT[n], region)
    pf = printed_in_shed(fl, s.FLOOR_TO_PRINT, region)
    rest = overlap(pw, pf)
    held = overlap(pw.translate([0, 0, 0.3]), pf)
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
    play = s.SLOT_U - (round((s.STOP_U - 0.25) / 0.2) * 0.2 + 0.25)
    out_catch = catch - play
    top = (pw ^ s.wall_box(n, a0 + 0.5, a1 - 0.5, -1, s.BARB - s.FIT - 0.05, -1, s.ZF - 1)).bounding_box()[5]
    ledge = (pf ^ s.wall_box(n, a0 + 0.5, a1 - 0.5, 0.05, s.BARB - s.FIT - 0.05, -1, s.ZF)).bounding_box()[2]
    report(rest < 0.01 and held > 0.05 and out_catch >= 0.29 and 0 < ledge - top < 0.45,
           f"{n} as printed: each barb reaches {catch:.2f} mm under its ledge ({out_catch:.2f} with the foot "
           f"pushed out against its stops), with {ledge - top:.2f} mm over it to spring in; lifted 0.3 mm the "
           f"printed barbs catch ({held:.2f} mm3), and seated nothing rubs ({rest:.3f} mm3)")
def tilt(piece, name, deg):
    """A long wall tipped out deg degrees about the outside top edge of the floor under it."""
    sx = s.WALL_SIDE[name][1]
    xp, zp = sx * (s.W / 2 - s.TS - s.FLOOR_CLR), s.ZF
    a = math.radians(deg) * sx
    c, sn = math.cos(a), math.sin(a)
    R = np.array([[c, 0, sn], [0, 1, 0], [-sn, 0, c]])
    t = np.array([xp, 0, zp]) - R @ np.array([xp, 0, zp])
    return piece.transform(np.column_stack([R, t]))


H = s.ZWT - s.ZF
# a long wall standing on its own: where its weight is, against the outside edge of the floor it
# tips over, and how far it leans before its posts stop it
for n in LONGS:
    sx = s.WALL_SIDE[n][1]
    w = p[n]
    mesh = w.to_mesh()
    vv = np.asarray(mesh.vert_properties)[:, :3]
    tt = np.asarray(mesh.tri_verts)
    a, b, c = vv[tt[:, 0]], vv[tt[:, 1]], vv[tt[:, 2]]
    vol6 = np.einsum("ij,ij->i", a, np.cross(b, c))
    com = ((a + b + c) * vol6[:, None]).sum(0) / (4 * vol6.sum())
    u_com = sx * com[0] - (s.W / 2 - s.WT)
    u_edge = s.SD - s.FLOOR_CLR
    deg = 0.0
    while deg < 6 and overlap(tilt(w, n, deg + 0.05), fl) < 1e-3:
        deg += 0.05
    lean = math.radians(deg) * H
    tip = w.volume() * (u_com - u_edge)               # its own weight tipping it out (mm3 x mm)
    hold = sum(l.volume() for l in lofts) / 2 * u_edge   # each loft's end lifted at the plate's inside edge;
                                                       # it pivots on the other wall, so half its weight
    if tip <= 0:
        report(True, f"{n} stands upright by itself: its weight is {u_com:.2f} mm out from its inside face, "
                     f"inside the floor's edge at {u_edge:.2f}")
    else:
        report(hold > 2 * tip,
               f"{n} would lean out about {lean:.1f} mm at the top by itself (its weight is {u_com:.2f} mm out from its "
               f"inside face, past the floor's edge at {u_edge:.2f}); with the lofts on its top plate it stays upright "
               f"once pushed straight: tipping it lifts their ends, {hold:.0f} against its own {tip:.0f} (mm3 x mm). "
               f"So the lofts go in before the end walls, and the band holds the corners shut while the angles are glued")
# the other way: a long wall pushed in a little at the top (the lofts leave it about 0.2 mm). The
# end wall's bottom must meet the bevel on the long wall's mitre, which pushes it back out, not
# land flat on the mitre's top corner.
ew = p["end wall 1"]
z_top = s.ZWT - 0.15
ok_in = True
for lean_mm in (0.2, 0.3, 0.5):
    a = -math.atan(lean_mm / H)
    xp, zp = s.W / 2 - s.WT, s.ZF                  # tipped in about the bottom plate's inside edge
    R = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    lw_i = p["door wall"].transform(np.column_stack([R, np.array([xp, 0, zp]) - R @ np.array([xp, 0, zp])]))
    lo, hi = 0.0, 100.0
    if overlap(ew, lw_i) < 1e-4:
        continue
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if overlap(ew.translate([0, 0, mid]), lw_i) > 1e-4 else (lo, mid)
    for c in (ew.translate([0, 0, hi - 0.02]) ^ lw_i).decompose():
        tb = c.bounding_box()
        if c.volume() > 1e-5 and not (z_top - s.MITRE_BEVEL - 0.1 < tb[2] and tb[5] < z_top - 0.05):
            ok_in = False
report(ok_in, f"with a long wall pushed in up to 0.5 mm at the top, a coming-down end wall first meets the "
              f"{s.MITRE_BEVEL} mm bevel on the long wall's mitre, which pushes it back out, not the mitre's flat top")


for n in WALLS:
    siding, trim_p = flat[n]
    whole = s.union(flat[n])
    bb = whole.bounding_box()
    # the bed face must run the whole inside face: the full length less the two mitres, and
    # nearly the full height of the wall
    foot = whole.trim_by_plane([0, 0, -1], -0.2)
    fbb = foot.bounding_box()
    report(fbb[3] - fbb[0] > (bb[3] - bb[0]) - 2 * (s.WT + s.PROUD) - 0.1 and fbb[4] - fbb[1] > 0.9 * (bb[4] - bb[1]),
           f"{n} lies flat on its framing ({foot.volume() / 0.2:.0f} mm2 on the bed)")
    # layer by layer, nothing may stick out more than 0.22 mm past the layer under it (45
    # degrees) unless it is a bridge held at both ends, 20 mm or less. Allowed: under 5 mm2 a
    # layer of small bits (the undersides of the roof pegs).
    worst, longest = worst_overhang(whole)
    report(worst < 5, f"{n} has nothing steeper than 45 degrees that isn't a bridge of 20 mm or less "
                      f"({worst:.1f} mm2 worst layer)")
    thin = max((c - c.offset(-0.2, RND).offset(0.2, RND)).area()
               for c in (whole.slice(0.125), whole.slice(0.35)))
    report(thin < 2, f"{n}: no knife edges on the bed ({thin:.2f} mm2 thinner than a line in the first two layers)")
    # the siding colour stops at the siding's face (its top layer prints to 5.05) and the trim is
    # all above it, so each plate changes colour once; the back wall has no trim left at all
    above = (siding ^ s.box(-BED, 2 * BED, -BED, 2 * BED, s.WT + 1e-4, BED)).volume()
    top = printed_top(s.WT)
    if n == "back wall":
        report(trim_p.volume() < 1e-6 and above < 1e-6,
               f"{n}: no trim at all ({trim_p.volume():.4f} mm3 in filament 2), all one colour, its siding's top "
               f"layer at {top:.2f} mm")
    else:
        tb = trim_p.bounding_box()
        report(trim_p.volume() > 0 and abs(tb[5] - (s.WT + s.PROUD)) < 0.01 and tb[2] > s.WT - 0.01
               and above < 1e-6,
               f"{n}: trim is {trim_p.volume() / 1000:.2f} cm3, all of it the top {s.PROUD} mm ({tb[2]:.2f} to "
               f"{tb[5]:.2f} mm), and nothing in the siding colour above the siding's top layer ({top:.2f} mm), "
               f"so the colour changes once")
    if n in LONGS:
        v = p[n].trim_by_plane([0, 0, 1], s.ZWT + 0.001).volume()
        report(v == 0, f"{n}: nothing above the wall plates (the barn ends carry all of the gable)")
        # between the end joist's notch and the mitre the top plate starts on the bed as a strip.
        # Without the notch fills it was under a line wide (0.4 mm2 of it), and Flash Studio warned
        # about it as a floating region (Nov 3 2026)
        sliver = 0.0
        for sy in (1, -1):
            sx = s.WALL_SIDE[n][1]
            xi, y_end = s.W / 2 - s.WT, s.loft_joist_ys()[0] + s.SW / 2 + s.FIT
            xa, xb = sorted([sx * (xi - 0.5), sx * (xi + 1.0)])
            ya, yb = sorted([sy * (y_end - 1.5), sy * (s.L / 2 + 1)])
            part = print_part(p[n], s.WALL_TO_PRINT[n], s.box(xa, xb, ya, yb, s.LOFT_Z - s.LUG_D - 1.5, s.ZWT + 1))
            for z in (0.125, 0.35):
                c = part.slice(z)
                sliver = max([sliver] + [b.area() for b in (c - c.offset(-0.21, RND).offset(0.21, RND)).decompose()])
        report(sliver < 0.15, f"{n}: where each end joist's notch stops short of the mitre, the first two layers have "
                              f"nothing under a line wide but rounded corners ({sliver:.3f} mm2 at most)")
same = (s.union(flat["end wall 1"]) ^ s.union(flat["end wall 2"])).volume()
v1 = s.union(flat["end wall 1"]).volume()
report(abs(same - v1) < 0.01, "the two end walls print the same, so end wall.stl serves for both")
# the floor and the lofts print upside down: their face is on the bed, and nothing hangs over
# more than 45 degrees (the joists, bands, lugs and slots all stand straight up from it)
for name, piece, mat in (("floor", fl, s.FLOOR_TO_PRINT), ("loft", p["loft"], s.LOFT_TO_PRINT)):
    ff = s.to_print(mat, [piece])[0]
    fbb = ff.bounding_box()
    foot = ff.slice(0.125).area()
    report(foot > 0.95 * (fbb[3] - fbb[0]) * (fbb[4] - fbb[1]) - 400,
           f"the {name} prints face down ({foot:.0f} mm2 on the bed)")
    worst, prev = 0.0, None
    for z in [0.125] + [0.35 + 0.2 * k for k in range(int(fbb[5] / 0.2))]:
        if z > fbb[5]:
            break
        cs = ff.slice(z)
        if prev is not None:
            worst = max(worst, (cs - prev.offset(0.22, m3.JoinType.Miter, 10)).area())
        prev = cs
    report(worst < 0.5, f"the {name} has nothing hanging over ({worst:.2f} mm2 worst layer)")
# the roof sheets print flat, underside down, ribs up
for name, piece in (("upper roof", up_flat), ("lower roof", lo_flat)):
    bb = piece.bounding_box()
    foot = piece.slice(0.125).area()
    worst, longest = worst_overhang(piece)
    report(foot > 0.9 * (bb[3] - bb[0]) * (bb[4] - bb[1]) and worst < 5,
           f"the {name} sheet prints flat on its underside ({foot:.0f} mm2 on the bed), nothing steeper than "
           f"45 degrees but its peg holes' roofs ({worst:.1f} mm2 worst layer, bridges up to {longest:.1f} mm)")

# the short corner in the fit test goes together the same way, long wall first, then end wall, and
# its stub of corner angle presses into the recesses
lw, ew, cf, stub = s.corner_test({n: p[n] for n in WALLS}, fl)
fsx, fsy = s.WALL_SIDE[s.FIT_LONG][1], s.WALL_SIDE[s.FIT_END][1]
fu, fv = np.array([fsx, 0.0, 0.0]), np.array([0.0, fsy, 0.0])
none = max(overlap(a, b) for a, b in itertools.combinations([lw, ew, cf, stub], 2))
held = min(overlap(lw.translate([0, 0, 0.3]), cf), overlap(ew.translate([0, 0, 0.3]), cf))
seat = min(overlap(stub.translate(-0.05 * fu), lw), overlap(stub.translate(-0.05 * fv), ew))
edge = min(overlap(stub.translate(-0.2 * fv), lw), overlap(stub.translate(-0.3 * fu), ew))
report(none < 0.001 and held > 0.05 and seat > 0.5 and edge > 0.02,
       f"the fit test's short corner snaps onto its bit of floor (lifted 0.3 mm its barbs catch: {held:.2f} mm3), "
       f"and its {s.FIT_STUB:.0f} mm stub of corner angle sits in both recesses touching nothing ({none:.4f} mm3), "
       f"on their floors ({seat:.1f} mm3 pressed 0.05 mm in) and between their edges ({edge:.2f} mm3 moved 0.2 mm "
       f"along the long wall or 0.3 mm along the end wall)")
worst = max(worst_overhang(part)[0] for _, part in s.corner_test_parts({n: p[n] for n in WALLS}, fl))
report(worst < 5, f"the fit test's new corner pieces print with nothing steeper than 45 degrees that isn't a bridge "
                  f"of 20 mm or less, and nothing starting in mid-air ({worst:.1f} mm2 worst layer)")

# 2. the roof: four sheets, each held on the barn ends by its pegs
sheets = {"door-side upper sheet": upper, "back upper sheet": upper.mirror([1, 0, 0]),
          "door-side lower sheet": lower, "back lower sheet": lower.mirror([1, 0, 0])}
for name, sh in sheets.items():
    v = overlap(body, sh)
    report(v < 0.01, f"the {name} sits on the barn ends without cutting into the body ({v:.4f} mm3)")
names = list(sheets)
worst = max(overlap(sheets[a], sheets[b]) for i, a in enumerate(names) for b in names[i + 1:])
report(worst < 0.001, f"no roof sheet overlaps another, at the ridge or where they lap ({worst:.4f} mm3)")
_, nu = s.seg_line("upper", 1)
_, nl = s.seg_line("lower", 1)
dl = np.array([nl[1], -nl[0]])                   # down the lower slope
du = np.array([nu[1], -nu[0]])                   # down the upper slope
N3 = np.array([nl[0], 0, nl[1]])
inside = s.union([body, loft_set])
v = overlap(body, upper.translate([0, 0, -0.3]))
report(v > 0.5, f"lowered 0.3 mm an upper sheet runs into the barn ends, so it is resting on them ({v:.1f} mm3)")
v = overlap(body, lower.translate(-0.3 * N3))
report(v > 0.5, f"pushed 0.3 mm in, square to its slope, a lower sheet runs into the barn ends' steep edges "
                f"({v:.1f} mm3)")
lift = 0.05 * np.array([nu[0], 0, nu[1]])
va = overlap(body, upper.translate(lift + [0, 1.0, 0]))
vd = overlap(body, upper.translate(lift + [du[0], 0, du[1]]))
report(min(va, vd) > 0.05, f"slid 1 mm along the barn ({va:.2f}) or down its slope ({vd:.2f} mm3), an upper sheet is "
                           f"held by its pegs")
# the lower sheet with the upper sheet off: its pegs leave it only one way off, straight up.
# Along the barn, down its slope, straight out, or its bottom swung out about its top, the pegs
# stop it, and it rests on them where it is drawn rather than sliding down by their clearance.
lift = np.array([0, 0, 0.05])
va = overlap(body, lower.translate(lift + [0, 1.0, 0]))
vd = overlap(body, lower.translate(lift + 0.3 * np.array([dl[0], 0, dl[1]])))
vo = overlap(body, lower.translate(0.3 * N3))
top = np.array([s.LOWER_A[0], 0, s.LOWER_A[1]])
a = math.radians(-2)                              # bottom out: a turn about the top edge
R = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
vs_ = overlap(body, lower.transform(np.column_stack([R, top - R @ top])))
report(min(va, vd, vo, vs_) > 0.05,
       f"a lower sheet is held by its pegs when slid 1 mm along the barn ({va:.2f}), 0.3 mm down its slope ({vd:.2f}) "
       f"or 0.3 mm straight out ({vo:.2f}), or with its bottom swung out 2 degrees ({vs_:.2f} mm3)")
worst = sweep(lower, inside, [[0, 0, dz] for dz in np.arange(0, 20.01, 0.1)])
report(worst < 1e-3, f"a lower sheet goes on and lifts off straight up, touching nothing from 20 mm up "
                     f"({worst:.4f} mm3)")
h = 0.0
while h < 3 and overlap(upper, lower.translate([0, 0, h + 0.02])) < 1e-4:
    h += 0.02
held = overlap(body, lower.translate([0, 0, h]).translate(0.3 * np.array([dl[0], 0, dl[1]])))
report(h < 1.0 and held > 0.05, f"with the upper sheet on, its tail is in the way of the lower sheet's only way off: "
                                f"lifted {h:.2f} mm the lower sheet meets it, still down on its pegs "
                                f"({held:.2f} mm3 when slid 0.3 mm down its slope there), so it is locked on")


def printed_sheet(piece, a, b):
    """as_printed() of a +x roof sheet laid flat the way panel_to_print lays it, put back on the barn."""
    mat = s.panel_frame(a, b)
    R, p0 = mat[:, :3], mat[:, 3]
    swap = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], dtype=float)
    A = swap @ R.T
    t = -A @ p0
    flat = piece.transform(np.column_stack([A, t]))
    bb = flat.bounding_box()
    back = as_printed(flat.translate([-bb[0], -bb[1], -bb[2]])).translate([bb[0], bb[1], bb[2]])
    return back.transform(np.column_stack([A.T, -A.T @ t]))


# as printed, the lower sheet's tilted slots step in layers, so it rests a little higher up its
# slope than drawn; the upper sheet's tail must still clear it
low_p = printed_sheet(lower, s.LOWER_A, s.LOWER_B)
up_dir = -np.array([dl[0], 0, dl[1]])
rise = 0.0
while rise < 2 and overlap(body, low_p.translate((rise) * up_dir)) > 1e-3:
    rise += 0.02
gap = 0.0
while gap < 2 and overlap(upper, low_p.translate((rise + gap + 0.02) * up_dir)) < 1e-4:
    gap += 0.02
report(gap >= 0.1, f"as printed, a lower sheet rests {rise:.2f} mm further up its slope than drawn, and the upper "
                   f"sheet's tail still clears it by {gap:.2f} mm more, so the upper sheet sits on the barn ends")
roof_low = s.union([lower, lower.mirror([1, 0, 0])])
worst = sweep(upper, s.union([inside, roof_low]), [[0, 0, dz] for dz in np.arange(0.1, 20.01, 0.1)])
report(worst < 1e-3, f"an upper sheet goes on and lifts off straight up, touching nothing from 20 mm up with the "
                     f"lower sheets and lofts in place ({worst:.4f} mm3)")

# 3. the lofts rest on the long walls' top plates, under the roof
roof_all = s.union(list(sheets.values()))
lbb = lofts[0].bounding_box()
yc = (lbb[1] + lbb[4]) / 2                                   # the middle of a loft, along the barn
for i, lf in enumerate(lofts):
    v = overlap(body, lf) + overlap(roof_all, lf)
    report(v < 0.01, f"loft {i + 1} fits between the walls and under the roof ({v:.4f} mm3)")
    v = overlap(body, lf.translate([0, 0, -0.1]))
    report(v > 0.5, f"loft {i + 1} rests on the long walls' top plates ({v:.1f} mm3 when lowered 0.1 mm)")
    v = min(overlap(body, lf.translate(t)) for t in ([0.3, 0, 0], [-0.3, 0, 0], [0, 0.3, 0], [0, -0.3, 0]))
    report(v > 0.05, f"loft {i + 1} can't slide: its lugs sit in notches in the plates ({v:.2f} mm3 when moved 0.3 mm)")
    worst = sweep(lf, longs, [[0, 0, dz] for dz in np.arange(0.1, 60.01, 0.1)])
    report(worst < 1e-3, f"loft {i + 1} drops in from above between the long walls before the end walls go on, and "
                         f"lifts straight out with the roof off ({worst:.4f} mm3)")
lf = lofts[0]
turned = lf.translate([0, -yc, 0]).rotate([0, 0, 180]).translate([0, yc, 0])
v = overlap(body, turned)
v2 = overlap(body, turned.translate([0, 0, -0.1]))
report(v < 0.01 and v2 > 0.5, f"a loft goes in either way round: turned end for end it fits the same notches "
                              f"({v:.4f} mm3 in place, {v2:.1f} mm3 lowered 0.1 mm)")
rise = 0.0
while rise < 3 and overlap(roof_all, lf.translate([0, 0, rise + 0.02])) < 1e-4:
    rise += 0.02
report(rise < s.LUG_D - 0.3, f"with the roof on, a loft can only rise {rise:.2f} mm before it meets the roof, so its "
                             f"{s.LUG_D} mm lugs stay {s.LUG_D - rise:.2f} mm down in their notches")
slide = 0.0
while slide < 2 and overlap(longs, lf.translate([0, slide + 0.02, 0])) < 1e-4:
    slide += 0.02
worst = sweep(p["end wall 1"], lf.translate([0, slide, 0]), [[0, 0, dz] for dz in DROPS] + [[0, 0, 0]])
gap_end = (s.L / 2 - s.WT) - (lbb[4] + slide)
report(worst < 1e-3 and gap_end >= 0.15,
       f"a loft slides {slide:.2f} mm toward its end at most, and even there an end wall comes down past it with "
       f"{gap_end:.2f} mm to spare ({worst:.4f} mm3)")

# 4. the door swings out to about 90 degrees and no further, and not inward
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

# 5. the door goes in: top pin up in its hole, bottom tilted out, then swung in along the slot
lift = s.DOOR_TOP_GAP - 0.05
top_z = s.ZF + s.DOOR_BOTTOM_GAP + s.DOOR_H
worst = 0
for frac in np.linspace(0, 1, 21):
    out = 3.5 * (1 - frac)                      # how far the bottom is outside at this step
    ang = math.atan2(out, s.DOOR_H)
    m = s.door_to_shed(0)
    m[2, 3] += lift
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

# 6. the skids fit under the floor frame with the joists down in their notches
sk = [s.skid().transform(mat) for mat in s.skids_to_shed()]
for i, k in enumerate(sk):
    v = overlap(body, k)
    report(v < 0.01, f"skid {i + 1} fits under the floor ({v:.4f} mm3)")
    v = overlap(body, k.translate([0, 0, 0.3]))
    report(v > 1, f"skid {i + 1} is really touching the joists ({v:.1f} mm3 when raised 0.3)")
    v = min(overlap(fl, k.translate(t)) for t in ([0.3, 0, 0], [-0.3, 0, 0], [0, 0.3, 0], [0, -0.3, 0]))
    report(v > 0.05, f"skid {i + 1} is held in place by its pegs in the floor ({v:.2f} mm3 when moved 0.3 mm)")

# 7. the corners: once all four walls are on, a band pulls the mitres shut and a black angle is
# glued into a recess in both walls at each corner. Each corner is checked mirrored back to the
# (+x, +y) corner, where u (x) is out from the long wall's siding face and v (y) out from the end
# wall's.
U, V, Z = np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), np.array([0, 0, 1.0])
DIRS = [np.array(d, dtype=float) / np.linalg.norm(d) for d in itertools.product((-1, 0, 1), repeat=3) if any(d)]
around = s.cbox(-12, 4, -12, 4, -2, 200)                  # the walls near a corner
roof_all = s.union(list(sheets.values()))
trim_all = s.union(s.trims())
swing = [door_all.transform(s.door_to_shed(deg)) for deg in range(0, 99, 7)]


def corner_set(sx, sy, walls):
    """The two walls at a corner, cut down to around it and mirrored back to the (+x, +y) corner,
    and a function that mirrors anything else back the same way."""
    def home(m):
        return s.at_corner(m, sx, sy)
    long_n, end_n = s.corner_walls(sx, sy)
    return home(walls[long_n]) ^ around, home(walls[end_n]) ^ around, home


def clear_moves(part, lw, ew, d):
    """The worst overlap with either wall of part moved d mm in each of 26 ways, leaving out the
    moves that press it into a wall it rests on (into the long wall is -u, into the end wall -v)."""
    return max([overlap(part.translate(d * e), lw) for e in DIRS if e @ U >= 0] +
               [overlap(part.translate(d * e), ew) for e in DIRS if e @ V >= 0])


for sx, sy in s.CORNERS:
    lw, ew, home = corner_set(sx, sy, p)
    a = home(s.corner_angle(sx, sy))
    where = "%s at %s" % s.corner_walls(sx, sy)
    none = overlap(a, lw) + overlap(a, ew)
    seat = min(overlap(a.translate(-0.05 * U), lw), overlap(a.translate(-0.05 * V), ew))
    edge = min(overlap(a.translate(-0.2 * V), lw), overlap(a.translate(-0.3 * U), ew))
    up = overlap(a.translate(0.2 * Z), s.union([lw, ew]))
    report(none < 1e-3 and seat > 1 and edge > 0.05 and up > 0.01,
           f"corner angle, {where}: sits in both recesses, touching neither wall ({none:.4f} mm3) but on the recess "
           f"floors ({seat:.1f} mm3 pressed 0.05 mm in); moved 0.2 mm along the long wall or 0.3 mm along the end "
           f"wall it meets the recess's edge ({edge:.2f}), and 0.2 mm up the recess's top ({up:.2f} mm3)")
    worst = clear_moves(a, lw, ew, 0.09)
    fillet = (a ^ s.cbox(-1.5, -0.45, -1.5, -0.45, 10, 80)).min_gap(s.union([lw, ew]), 1.0)
    report(worst < 1e-4 and 0.2 <= fillet <= 0.3,
           f"corner angle, {where}: moved 0.09 mm any of 26 ways but into a recess floor it still touches neither "
           f"wall ({worst:.5f} mm3), so it is about 0.1 clear all round; its fillet is {fillet:.3f} mm off the "
           f"walls' chamfer, room for both to print in steps")
    # pressed in from 1.5 mm out, straight in to the long wall, to the end wall, or into the corner,
    # with its foot on the table, it touches nothing on the way
    press = max(overlap(a.translate(t * e), s.union([lw, ew])) for e in (U, V, (U + V) / math.sqrt(2))
                for t in np.arange(0.02, 1.51, 0.02))
    report(press < 1e-4, f"corner angle, {where}: presses straight into its recesses from 1.5 mm out, square to "
                         f"either wall or into the corner, without catching on anything ({press:.5f} mm3)")
    moved = max(overlap(a.translate(d * n_a), w_b) for n_a, w_b in ((U, ew), (V, lw)) for d in (0.15, -0.15))
    report(moved < 1e-3, f"corner angle, {where}: with either wall sitting 0.15 mm out or in, the angle on its "
                         f"recess still touches nothing of the other wall ({moved:.4f} mm3)")
    face_l = (a ^ s.cbox(s.ANGLE_P - 0.01, 2, -10, 10, -1, 200)).bounding_box()
    face_e = (a ^ s.cbox(-10, 10, s.ANGLE_P - 0.01, 2, -1, 200)).bounding_box()
    cover_l, cover_e = s.L / 2 - face_l[1], s.W / 2 - face_e[0]
    foot = a.bounding_box()[2] - min(lw.bounding_box()[2], ew.bounding_box()[2])
    siding_top = (lw ^ s.cbox(-0.1, 0, -3, -2, -1, 200)).bounding_box()[5]
    report(min(cover_l, cover_e) >= 3 and abs(foot) < 1e-6,
           f"corner angle, {where}: covers the mitre's outside edge by {cover_l:.2f} mm on the long wall's face and "
           f"{cover_e:.2f} mm on the end wall's, from its foot, level with the skirts, up to {face_l[5]:.2f} mm "
           f"(the long wall's siding beside it goes on to {siding_top:.2f}, under the eave)")
    roof_c = home(roof_all)
    gap = a.min_gap(roof_c, 1.0)
    low = overlap(a, roof_c.translate([0, 0, -0.15]))
    report(gap >= 0.2 - 0.002 and low < 1e-4,
           f"corner angle, {where}: {gap:.3f} mm clear of the roof sheets at the closest, square to them, and with "
           f"the roof 0.15 mm lower still clear ({low:.5f} mm3)")
    gap_t = a.min_gap(home(trim_all), 1.0)
    gap_l = a.min_gap(home(loft_set), 5.0)
    gap_d = min(a.min_gap(home(d), 5.0) for d in swing)
    report(gap_t >= 0.1 and gap_l >= 0.1 and gap_d >= 0.1,
           f"corner angle, {where}: {gap_t:.2f} mm clear of the other trim (the rake board over it), and clear of "
           f"the lofts ({gap_l:.1f}) and of the door swinging out to 98 degrees ({gap_d:.1f} mm)")

# the same as printed: both walls and the angle each cut into their own print's layers, with anything
# thinner than a line rounded off. The recess floors print on the 4.65 layer, 0.054 deeper than
# drawn, so the angle sits that much further in; the chamfer and the fillet both come out stepped,
# the end wall's steps across the angle's. Pushed onto both printed floors the angle must still miss
# the walls, also with the band closing the 0.1 mitre gap (the end wall 0.07 along each face).
for sx, sy in s.CORNERS:
    lw_n, ew_n = s.corner_walls(sx, sy)
    where = "%s at %s" % (lw_n, ew_n)
    _, _, home = corner_set(sx, sy, p)
    region = home(s.cbox(-12, 2, -12, 2, 30, 60))
    pl = home(printed_in_shed(p[lw_n], s.WALL_TO_PRINT[lw_n], region))
    pe = home(printed_in_shed(p[ew_n], s.WALL_TO_PRINT[ew_n], region))
    pa = home(printed_in_shed(s.corner_angle(sx, sy), s.CORNER_TO_PRINT[sx], region))
    floor_u = (pl ^ s.cbox(-3, 1, -3.3, -2, 40, 50)).bounding_box()[3] - s.W / 2
    floor_v = (pe ^ s.cbox(-3.3, -2, -3, 1, 40, 50)).bounding_box()[4] - s.L / 2
    du = floor_u - ((pa ^ s.cbox(-1, 1, -3.3, -2, 40, 50)).bounding_box()[0] - s.W / 2)
    dv = floor_v - ((pa ^ s.cbox(-3.3, -2, -1, 1, 40, 50)).bounding_box()[1] - s.L / 2)
    seated = pa.translate([du, dv, 0])
    v = overlap(seated, s.union([pl, pe]))
    on = min(overlap(seated.translate(-0.01 * U), pl), overlap(seated.translate(-0.01 * V), pe))
    shut = 0.1 / math.sqrt(2)
    v_shut = overlap(seated.translate(-shut * V), s.union([pl, pe.translate(shut * (U - V))]))
    tip_e = seated.bounding_box()[0] - (pe ^ s.cbox(-6, -3, -0.3, 1, 40, 50)).bounding_box()[3]
    tip_l = seated.bounding_box()[1] - (pl ^ s.cbox(-0.3, 1, -6, -3, 40, 50)).bounding_box()[4]
    # how close the fillet's steps come to the walls' steps, on a section away from the recess floors
    box2 = m3.CrossSection.square([2.4, 2.4]).translate([s.W / 2 - 3, s.L / 2 - 3])
    ws, fs = s.union([pl, pe]).slice(45.0) ^ box2, seated.slice(45.0) ^ box2
    lo, hi = 0.0, 0.5
    for _ in range(14):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if (fs.offset(mid, RND) ^ ws).area() > 1e-7 else (mid, hi)
    report(v < 1e-4 and on > 0.05 and v_shut < 1e-4 and min(tip_e, tip_l) >= 0.05 and lo >= 0.03,
           f"corner angle, {where}, as printed: pushed {-du:.3f} and {-dv:.3f} mm in onto both printed recess floors "
           f"({floor_u:.3f}, {floor_v:.3f}) it touches neither wall ({max(v, 0):.4f} mm3 over 30 mm), nor with the mitre "
           f"closed ({max(v_shut, 0):.4f}); {tip_l:.3f} mm left past the long-face leg and {tip_e:.3f} past the "
           f"end-face leg, and the fillet's steps {lo:.3f} mm off the chamfer's")

for name, part in angle_flat:
    bb = part.bounding_box()
    worst, _ = worst_overhang(part)
    loose = floating(part)
    foot = part.slice(0.125).area()
    report(worst < 0.01 and loose < 0.02 and abs(bb[5] - s.ANGLE_UP) < 1e-6 and abs(printed_top(bb[5]) - bb[5]) < 1e-6
           and foot > 0.9 * (bb[3] - bb[0]) * (s.TRIM + s.ANGLE_P),
           f"corner angle, {name}: prints lying on its long-face leg ({foot:.0f} mm2 on the bed), its other leg "
           f"standing {bb[5]:.2f} mm, on a layer line, nothing steeper than 45 degrees and nothing starting in "
           f"mid-air, even with anything thinner than a line left out ({worst:.3f} and {loose:.3f} mm2 worst layer)")

# the walls at each corner, as printed: the recess floor two layers under the siding's top layer,
# and no sliver thinner than a line where the chamfer meets the mitre, the recess and the nearest
# siding groove
for n in WALLS:
    axis, sign = s.WALL_SIDE[n]
    floors, faces, thin, longest = [], [], 0.0, 0.0
    for sx, sy in s.CORNERS:
        if (axis == 0 and sx != sign) or (axis == 1 and sy != sign):
            continue
        piece = s.at_corner(p[n], sx, sy)

        def probe(a0, a1):
            """A short column through the wall's face 30 mm up, a0 to a1 along it from the corner."""
            return s.cbox(-3, 2, a0, a1, 30, 31) if axis == 0 else s.cbox(a0, a1, -3, 2, 30, 31)
        # the outer 2.2 mm of the wall (siding, chamfer, recess), out to just past the nearest
        # groove, from under the skirt to the top of the wall plates
        if axis == 0:                                            # long wall: u is x
            region = s.cbox(-2.2, 2, -9.5, 2, -2, s.ZWT)
            mat, out = s.WALL_TO_PRINT["door wall"], s.W / 2
        else:                                                    # end wall: v is y
            region = s.cbox(-9.5, 2, -2.2, 2, -2, s.ZWT)
            mat, out = s.WALL_TO_PRINT["end wall 1"], s.L / 2
        floors.append((piece ^ probe(-3, -2.5)).bounding_box()[3 + axis] - out + s.WT)
        faces.append((piece ^ probe(-6.5, -6)).bounding_box()[3 + axis] - out + s.WT)
        R = np.column_stack([np.array(mat, dtype=float), [0, 0, -(out - s.WT)]])
        flat_c = (piece ^ region).transform(R)
        for z0, z1 in layers(s.WT):
            if (z0 + z1) / 2 < s.WT - 2.2:
                continue
            cs = flat_c.slice((z0 + z1) / 2)
            bits = cs - cs.offset(-0.21, RND).offset(0.21, RND)
            thin = max([thin] + [b.area() for b in bits.decompose()])
            # how long each bit is, with the hairlines the rounding leaves along straight edges taken out
            longest = max([longest] + [math.hypot(b.bounds()[2] - b.bounds()[0], b.bounds()[3] - b.bounds()[1])
                                       for b in bits.offset(-0.01, RND).offset(0.01, RND).decompose()
                                       if b.area() > 1e-4])
    pf = {round(printed_top(h), 3) for h in floors}
    pw = {round(printed_top(h), 3) for h in faces}
    report(pf == {4.65} and pw == {5.05} and thin < 0.05 and longest < 0.6,
           f"{n}: as printed, each corner recess's floor is on the {min(pf):.2f} layer line and the siding's face "
           f"on {min(pw):.2f}, 2 layers; near the corners nothing is thinner than a line (the biggest bit under a "
           f"line wide in any layer is {thin:.3f} mm2 and the longest {longest:.2f} mm, corners rounded off)")

# the gable vent: none of it out past the siding; the louvres in a recess whose floor is on a
# layer line, with 3 layers of siding under it
vz0 = s.ZPK - 0.92 * s.FT - 0.76 * s.FT / 2
ew1 = p["end wall 1"]
vfloor = (ew1 ^ s.box(-2, 2, s.L / 2 - 3, s.L / 2 + 3, vz0 + 1.05, vz0 + 1.2)).bounding_box()[4] - s.L / 2 + s.WT
vfront = (ew1 ^ s.box(-6, 6, s.L / 2 - 3, s.L / 2 + 3, vz0 + 1.3, vz0 + 8.3)).bounding_box()[4] - s.L / 2 + s.WT
bridge = min(z0 for z0, z1 in layers(s.WT) if (z0 + z1) / 2 > s.SD)
under = round((vfloor - bridge) / 0.2, 6)
report(abs(printed_top(vfloor + 1e-9) - vfloor) < 1e-6 and under >= 3 and abs(vfront - s.WT) < 1e-6,
       f"the gable vent's louvres sit in a recess {s.WT - vfloor:.2f} mm into the siding, its floor on the {vfloor:.2f} "
       f"layer line over {under:.0f} layers of siding (from {bridge:.2f}, where it bridges the framing); the slats' "
       f"fronts and the frame come up to the siding face ({vfront:.2f} mm) and no further")

# 8. caps for the walls Alan printed before Nov 3 2026 (git HEAD then: hooks and black corner
# boards printed on the walls). Each cap must clear those walls, built in memory from that
# make_barn.py, by 0.1 everywhere, also with a wall 0.15 out or in, clear the roof, and cover the
# old mitre.
OLD = "b4510470b0737d2117aefb53347b6cf93cc71e17"


def old_model():
    """make_barn.py as it was at OLD, as a module, built in memory; or None and why not, if git
    can't give it (outside the repository, or no git on the PATH)."""
    try:
        src = subprocess.run(["git", "show", OLD + ":./make_barn.py"], cwd=s.HERE, capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError) as e:
        why = e.stderr.decode("utf-8", "replace").strip() if getattr(e, "stderr", None) else str(e)
        return None, why
    mod = types.ModuleType("make_barn_old")
    mod.__file__ = os.path.join(s.HERE, "make_barn.py")
    exec(compile(src.stdout.decode("utf-8"), "make_barn.py at " + OLD[:7], "exec"), mod.__dict__)
    return mod, ""


old, why = old_model()
if old is None:
    report(False, f"the old walls ({OLD[:7]}) can't be read from git, so the caps aren't checked against them: {why}")
else:
    old_p = old.wall_pieces(old.walls())
    report(hasattr(old, "corner_hooks") and (old_p["door wall"] ^ old.trim_zone()).volume() > 0,
           f"the old walls ({OLD[:7]}) built in memory, with their corner hooks and printed corner boards")
    tip = s.PROUD - s.MITRE_GAP / math.sqrt(2)              # each old board's tip, at the mitre
    for sx, sy in s.CORNERS:
        lw, ew, home = corner_set(sx, sy, old_p)
        c = home(s.corner_cap(sx, sy))
        where = "%s at %s" % s.corner_walls(sx, sy)
        gap = min(c.min_gap(lw, 1.0), c.min_gap(ew, 1.0))
        out_ = min(c.translate(0.15 * n_a).min_gap(w_b, 1.0) for n_a, w_b in ((U, ew), (V, lw)))
        in_ = min(c.translate(-0.15 * n_a).min_gap(w_b, 1.0) for n_a, w_b in ((U, ew), (V, lw)))
        report(gap >= 0.1 - 1e-6 and out_ >= 0.1 - 1e-6 and in_ > 0.01,
               f"corner cap, {where}: {gap:.3f} mm clear of the old walls and their boards at the closest, {out_:.3f} "
               f"with either wall's foot sitting 0.15 mm out and the cap on its board, and still clear ({in_:.3f}) "
               f"with a wall 0.15 mm in, where the other wall's board stands 0.08 proud of it")
        # a blob 0.3 mm across on the old boards' outside corner, or on either board's tip, must
        # not hold the cap off
        blob = max(overlap(c, s.cyl_z(s.W / 2 + u, s.L / 2 + v, 1, 85, 0.3))
                   for u, v in ((s.PROUD, s.PROUD), (s.PROUD, tip), (tip, s.PROUD)))
        report(blob < 1e-4, f"corner cap, {where}: its relief leaves room for a 0.3 mm blob on the old boards' "
                            f"corner or on either board's tip ({blob:.5f} mm3)")
        roof_c = home(roof_all)
        gap_r = c.min_gap(roof_c, 1.0)
        low = overlap(c, roof_c.translate([0, 0, -0.15]))
        rake = old.ZWT                                         # the old rake board's foot
        top_e = (c ^ s.cbox(-5, -1, -1, 3, 0, 200)).bounding_box()[5]
        report(gap_r >= 0.2 - 0.002 and low < 1e-4 and rake - top_e >= 0.1,
               f"corner cap, {where}: {gap_r:.3f} mm clear of the roof sheets, still clear with the roof 0.15 mm lower "
               f"({low:.5f} mm3), and its end-face leg {rake - top_e:.2f} mm under the old rake board")
        edge_l = (lw ^ s.cbox(s.PROUD - 0.05, 1, -6, 2, 40, 41)).bounding_box()
        edge_e = (ew ^ s.cbox(-6, 2, s.PROUD - 0.05, 1, 40, 41)).bounding_box()
        out_face = s.PROUD + s.CAP_CLR + s.CAP_T - 0.01
        face_l = (c ^ s.cbox(out_face, 2, -10, 10, -1, 200)).bounding_box()
        face_e = (c ^ s.cbox(-10, 10, out_face, 2, -1, 200)).bounding_box()
        over_l, over_e = edge_l[1] - face_l[1], edge_e[0] - face_e[0]          # past the old boards' inner edges
        cover_l, cover_e = edge_l[4] - face_l[1], edge_e[3] - face_e[0]        # from the old mitre's outside edge
        old_top = (lw ^ s.cbox(s.PROUD - 0.05, 1, -6, 2, 0, 200)).bounding_box()[5]
        report(min(over_l, over_e) >= 0.2 - 1e-6 and min(cover_l, cover_e) >= 3,
               f"corner cap, {where}: covers the old mitre's outside edge by {cover_l:.2f} mm on the long wall's face "
               f"and {cover_e:.2f} on the end wall's, {min(over_l, over_e):.2f} past each old board's inner edge, from "
               f"its foot to {face_l[5]:.2f} mm (the old boards' outside faces stop at {old_top:.2f}, under the eave)")
for name, part in cap_flat:
    bb = part.bounding_box()
    worst, _ = worst_overhang(part)
    loose = floating(part)
    foot = part.slice(0.125).area()
    width = s.TRIM + s.CAP_OVER + s.PROUD + s.CAP_CLR + s.CAP_T
    report(worst < 0.01 and loose < 0.02 and foot > 0.9 * (bb[3] - bb[0]) * width,
           f"corner cap, {name}: prints lying on a leg ({foot:.0f} mm2 on the bed), the other standing {bb[5]:.2f} mm, "
           f"nothing steeper than 45 degrees and nothing starting in mid-air, even with anything thinner than a line "
           f"left out ({worst:.3f} and {loose:.3f} mm2 worst layer)")

# 9. the plates: every part inside the 220 x 220 bed and at least 3 mm from the next; on a plate
# with two filaments the prime tower's corner (x 165, y 195) is clear
for fname, pls in s.plates(p).items():
    for i, (pname, items) in enumerate(pls):
        placed, fils = [], set()
        for obj, parts, (x, y) in items:
            whole = s.union([m for _, m, _ in parts])
            bb = whole.bounding_box()
            fils |= {f for _, _, f in parts}
            placed += whole.translate([x - bb[0], y - bb[1], -bb[2]]).decompose()
        boxes = [q.bounding_box() for q in placed]
        inside = all(b[0] >= -1e-6 and b[1] >= -1e-6 and b[3] <= BED + 1e-6 and b[4] <= BED + 1e-6 for b in boxes)
        gap = BED
        for a_, b_ in itertools.combinations(range(len(placed)), 2):
            A_, B_ = boxes[a_], boxes[b_]
            d = math.hypot(max(B_[0] - A_[3], A_[0] - B_[3], 0), max(B_[1] - A_[4], A_[1] - B_[4], 0))
            gap = min(gap, d if d >= 3 else placed[a_].min_gap(placed[b_], 3.5))
        tower = all(b[3] <= 165 - 3 or b[4] <= 195 - 3 for b in boxes)
        report(inside and gap >= 3 - 1e-6 and (len(fils) < 2 or tower),
               f"{fname}, plate {i + 1} ({pname}): " +
               (f"{len(placed)} parts inside the bed, at least {gap:.1f} mm apart, " if len(placed) > 1 else
                "1 part, inside the bed, ") +
               ("the prime tower's corner clear" if len(fils) > 1 else f"filament {min(fils)} only, no prime tower"))

# 10. sizes measured off the parts, at full size, against the 3D designer's shop standard for the
# 8x12 Side Lofted Barn (library/manufacturers/standard.json styles.SLB, test/golden-shop): walls
# 79 1/2 in, barn roof 43 3/4 in from the top of the upper plate to the peak of the trusses (44.21
# in to the top of the 7/16 in roof deck), eave 1.73 in measured level, door opening 48 1/4 x
# 71 1/2 in; the window tops at the loft header under the top plate (Alan's lofted-wall rule).
inch = 1 / s.S


def extent(piece, region, axis):
    bb = (piece ^ region).bounding_box()
    return bb[axis], bb[axis + 3]


dw = p["door wall"]
floor_top = p["floor"].bounding_box()[5]
wall_top = dw.bounding_box()[5] + 0.15                    # the long walls stop 0.15 under the roof
siding_x = extent(dw, s.box(0, 60, -45.2, -45, s.ZF + 20, s.ZF + 20.2), 0)[1]   # bare siding
peak = p["end wall 1"].bounding_box()[5]
wall_in = (wall_top - floor_top) * inch
report(abs(wall_in - 79.5) < 0.01, f"walls {wall_in:.2f} in from the floor to the top of the upper plate (shop: 79 1/2 in)")
line_peak = (peak - wall_top) * inch
truss_peak = line_peak - 0.4375 / math.cos(math.atan(s.UP_M))
report(abs(truss_peak - 43.75) < 0.01,
       f"barn roof {truss_peak:.2f} in from the top of the upper plate to the peak of the trusses (shop: 43 3/4 in at "
       f"8 ft wide), {line_peak:.2f} in to the top of the roof deck")
mv = np.asarray(lower.to_mesh().vert_properties)[:, :3]
eave_pt = mv[np.argmin(mv[:, 2])]
eave = (eave_pt[0] - siding_x) * inch
report(abs(eave - 1.734) < 0.01, f"eave {eave:.2f} in out from the siding, measured level (designer: 1.73 in)")
probe_x = (siding_x + 0.1, siding_x + 0.5)                 # in the casings, which edge each opening
gap_lo = extent(body, s.box(*probe_x, -40, -0.1, s.ZF + 20, s.ZF + 20.2), 1)[1]
gap_hi = extent(body, s.box(*probe_x, 0.1, 40, s.ZF + 20, s.ZF + 20.2), 1)[0]
door_top = extent(body, s.box(*probe_x, -0.1, 0.1, s.ZF + 2, s.ZWT), 2)[0]
door_w, door_h = (gap_hi - gap_lo) * inch, (door_top - floor_top) * inch
report(abs(door_w - 48.25) < 0.01 and abs(door_h - 71.5) < 0.01,
       f"door opening {door_w:.2f} x {door_h:.2f} in (shop: 48 1/4 x 71 1/2 in)")
win_top = extent(body, s.box(*probe_x, s.WIN_YC + 4.9, s.WIN_YC + 5.1, s.ZF + 50, s.ZWT), 2)[0]
win_sill = extent(body, s.box(*probe_x, s.WIN_YC + 4.9, s.WIN_YC + 5.1, s.ZF, s.ZF + 50), 2)[1]
hdr = (s.ZWT - s.PLATE_TOP - s.HEADER - s.ZF) * inch
report(abs((win_top - floor_top) * inch - 71.5) < 0.01 and abs(hdr - 71.5) < 0.01,
       f"both windows {(win_top - win_sill) * inch:.1f} in tall with their tops {(win_top - floor_top) * inch:.2f} in up, "
       f"level with the door's, at the underside of the loft header (71.5 in)")

print()
print("all checks passed" if fails == 0 else f"{fails} check(s) failed")
sys.exit(1 if fails else 0)
