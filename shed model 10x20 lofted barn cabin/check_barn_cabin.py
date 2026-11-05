"""Checks the Lofted Barn Cabin model fits together before anything is printed.

Run:  python check_barn_cabin.py
Each line says what it proved, with the numbers it measured. Anything that fails is marked FAIL,
and the run ends with exit code 1. The groups are in the order the four new models share (F12):
1 pieces and bed, 2 snap joints, 3 walls print, 4 corners, 5 gables and vents, 6 the porch and
the lofts, 7 door, 8 roof, 9 skids, 10 plates, 11 fit test, 12 sizes at full size, the last of them
Alan's standard layout measured off the parts against the addendum's own numbers (STD below, typed
in here from the addendum, not read from make_barn_cabin.py, so a moved constant there fails). Alan's answers
(ALAN) and the model's held bottom plate (PLATE_BOT_MM) are typed in the same way.
"""

import importlib
import inspect
import itertools
import math
import os
import re
import shutil
import sys
import tempfile
import zipfile

import manifold3d as m3
import numpy as np

import make_barn_cabin as s

M = m3.Manifold

BED = 220.0
fails = 0
# Alan's standard layout (Nov 3 2026, "go on yoder-storage-barns.com to see standard layout";
# designer-standards.js, his copy-this-build codes, Aug 2026), live 10x20 state: d36lite F +1.74,
# w23 F -2.57, w23 R 0, w23 L 0, ppost F -0.3, fake F 0. Feet from each wall's middle, +x right
# seen from the porch; the long walls' middle is 2 ft behind the building's (frame.js cx = -pd/2).
# Sizes from the live catalog: d36lite 3 x 6.3 ft, w23 2.1 x 2.9 ft, fake 2.6 x 1.9 ft (frame 0.3,
# corner triangles min(0.5, 0.55 x 1.0, 0.75 x 0.65)), corner posts 0.28 ft in and 0.2 ft back
STD = {"door": 1.74, "front window": -2.57, "side window": 0.0, "side middle": 2.0, "middle post": -0.3,
       "corner post in": 0.28, "post back": 0.2, "door w": 3.0, "door h": 6.3, "win w": 2.1, "win h": 2.9,
       "faux w": 2.6, "faux h": 1.9, "faux bar": 0.3, "faux tri": 0.4875, "faux over wall top": 1.57,
       "rail post gap mm": 0.2, "rail oc": 0.44}
# Alan's answers, Nov 4 2026, inches, typed in here: "Loft wall height is 79.5" (his lofted wall, 75 in studs on one
# 1 1/2 in bottom plate under two 1 1/2 in top plates), and of the three doorways asked, "73 1/2 in door, flat
# boards": the builder's 36 in door 73 1/2 in tall from the floor under his two flat 2x4s (3 in) on 72 in kings
# standing on the bottom plate, so the header is right under the top plates. Over each window his 5 in loft header
# right under the top plates (carried over from the Side Lofted Barn)
ALAN = {"wall h": 79.5, "stud": 75.0, "plate": 1.5, "door h": 73.5, "king": 72.0, "flat header": 3.0, "loft header": 5.0}
# the model's bottom plate, held at 1.6 mm (2.02 in, not Alan's 1 1/2 in) for the snaps' legs (spec F4), typed in here
# and not read from make_barn_cabin.py, so a moved PLATE_BOT there fails: the read me's 2 in bottom plate, 74 1/2 in
# studs and 71 1/2 in door kings are measured against it (the header test and group 12)
PLATE_BOT_MM = 1.6  # mm


def report(ok, words):
    global fails
    fails += 0 if ok else 1
    print(("ok   " if ok else "FAIL ") + words)


def group(title):
    print()
    print("== " + title)


def overlap(a, b):
    return (a ^ b).volume()


def centroid(m):
    """(centre of mass, volume) of a solid piece, from its mesh."""
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    t = np.asarray(mesh.tri_verts)
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    vol = np.einsum("ij,ij->i", a, np.cross(b, c)) / 6
    return ((a + b + c) / 4 * vol[:, None]).sum(axis=0) / vol.sum(), vol.sum()


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
    layer's height. A feature that only exists in the CAD shape goes missing here. If nothing is
    left (none of the piece where it was looked for, or all of it thinner than a line), that is a
    FAIL here and the piece comes back empty, rather than the run stopping with an error."""
    top = m.bounding_box()[5]
    out = []
    for z0, z1 in layers(top):
        cs = m.slice((z0 + z1) / 2).offset(-0.21, RND).offset(0.21, RND)
        if cs.area() > 0:
            out.append(M.extrude(cs, z1 - z0).translate([0, 0, z0]))
    if not out:
        report(False, "a piece checked as printed comes out empty: none of it is where it should be, or all of it is "
                      "thinner than a 0.42 mm line, so the check after this has nothing of it to measure")
        return M()
    return s.union(out)


def print_part(piece, mat, region):
    """The part of a piece inside region (cabin coords), where it lies in the piece's print."""
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
    """as_printed() of the part of a piece inside region (cabin coords), printed lying the way
    mat lays it on the bed, and put back where it goes in the cabin."""
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


def bridges_across(piece, ang, z_from, step=0.2, limit=20, region=None, allow=1.1):
    """The bridges of every layer over z_from laid the way a fixed bridge direction lays them: straight lines at ang
    degrees on the bed (0 along X), each held at both ends by something printed on the layer below. Only what hangs
    free inside region counts (a modifier's solid, as its section at each layer; a CrossSection on the bed; None,
    the whole layer). What hangs free is what reaches more than allow (1.1) times the height from the layer below
    past it (45 degrees); with allow 0, all the layer below doesn't hold, the way the slicer finds its bridges (the
    floor's 0.4 mm seams). Returns (the worst layer's area hanging free that such lines of limit (20) mm or less
    don't hold, mm2; the longest such line, mm). The garages' (check_garage.py), with region and allow."""
    bb = piece.bounding_box()
    worst, longest, prev, z_prev = 0.0, 0.0, None, 0.0
    for z0, z1 in layers(bb[5]):
        zm = (z0 + z1) / 2
        cs = piece.slice(zm)
        if prev is not None and zm > z_from:
            sup = prev.offset(allow * (zm - z_prev), RND) if allow else prev
            reg = region.slice(zm) if isinstance(region, M) else region
            free = cs - sup if reg is None else (cs - sup) ^ reg
            if free.area() >= 0.01:
                f, h = free.rotate(-ang), (cs ^ sup).rotate(-ang)
                b = f.bounds()
                ys = np.arange(b[1] + step / 2, b[3], step)
                rects = []
                for y, fi, hi in zip(ys, scan(f, ys), scan(h, ys)):
                    for x0, x1 in fi:
                        if (np.any(np.abs(hi[:, 1] - x0) < 0.05) and np.any(np.abs(hi[:, 0] - x1) < 0.05)
                                and x1 - x0 <= limit):
                            rects.append([(x0, y - step / 2), (x1, y - step / 2), (x1, y + step / 2), (x0, y + step / 2)])
                            longest = max(longest, x1 - x0)
                left = f - m3.CrossSection(rects, m3.FillRule.Positive).offset(0.05, RND) if rects else f
                worst = max(worst, left.area())
        prev, z_prev = cs, zm
    return worst, longest


def bridges_any_way(piece, z_from, outside=None, step=0.2, allow=1.1):
    """Where nothing sets the bridge direction the slicer picks it, and not the same way every time, so it must be
    short every way: the longest straight line at any angle (1 degree apart) held at both ends by something printed
    on the layer below, through what of each layer over z_from hangs free (as bridges_across(), allow) outside
    outside (the modifiers' solids, as their section at each layer; a CrossSection on the bed; None, nothing). A line
    may also end on outside's edge, where the slicer's own lines meet a modifier's: so a strip it leaves running into
    a modifier counts too. Returns (that length, mm; (layer, angle) it is at); it stops at the first angle that finds
    one over 20 mm."""
    bb = piece.bounding_box()
    longest, at, prev, z_prev = 0.0, None, None, 0.0
    for z0, z1 in layers(bb[5]):
        zm = (z0 + z1) / 2
        cs = piece.slice(zm)
        if prev is not None and zm > z_from:
            sup = prev.offset(allow * (zm - z_prev), RND) if allow else prev
            out = outside.slice(zm) if isinstance(outside, M) else outside
            free = cs - sup if out is None else cs - sup - out
            if free.area() >= 0.01:
                hold = cs ^ sup if out is None else (cs ^ sup) + (cs ^ out)
                for ang in range(180):
                    f, h = free.rotate(-ang), hold.rotate(-ang)
                    b = f.bounds()
                    ys = np.arange(b[1] + step / 2, b[3], step)
                    for y, fi, hi in zip(ys, scan(f, ys), scan(h, ys)):
                        for x0, x1 in fi:
                            if (x1 - x0 > longest and np.any(np.abs(hi[:, 1] - x0) < 0.05)
                                    and np.any(np.abs(hi[:, 0] - x1) < 0.05)):
                                longest, at = x1 - x0, (zm, ang)
                    if longest > 20:
                        return longest, at
        prev, z_prev = cs, zm
    return longest, at


def groove_run(piece, ang, region, step=0.2):
    """On a floor's second layer, the one over its seams and grooves: the longest stretch of what hangs free of its
    first (all the first doesn't hold, allow 0) inside region (a modifier's solid, as its section there) that one
    straight line at ang degrees on the bed (0 along X) runs over, held at its ends or not, mm. A box lays its bridges
    across its groove, the short way, when this is shorter at its own angle than at right angles to it."""
    (a0, a1), (b0, b1) = layers(1.0)[:2]
    zm = (b0 + b1) / 2
    free = (piece.slice(zm) - piece.slice((a0 + a1) / 2)) ^ region.slice(zm)
    if free.area() < 1e-4:
        return 0.0
    f = free.rotate(-ang)
    b = f.bounds()
    return max([x1 - x0 for fi in scan(f, np.arange(b[1] + step / 2, b[3], step)) for x0, x1 in fi] + [0.0])


def free_patches(piece, outside=None):
    """Where nothing sets the bridge direction on a piece cut from the floor the slicer picks it, and a groove there can
    run out into a hole or off an edge, where a strand along it is held at one end only (the room's outer seams end in
    the prong slots, the deck's grooves at its front edge): bridges_any_way, which counts lines held at both ends,
    misses that. So here every patch of every layer that hangs free (all the layer below doesn't hold, allow 0) outside
    outside (the modifiers' solids, as their section at each layer; None, nothing) is measured across its longest way,
    between its two corners farthest apart: no strand over it, at any angle, held at both ends, one or neither, hangs
    free for longer. Slivers thinner than 0.02 mm (a slice's rounding) are left out. Returns (the longest, mm; the
    layer it is on, or None)."""
    longest, at, prev = 0.0, None, None
    for z0, z1 in layers(piece.bounding_box()[5]):
        zm = (z0 + z1) / 2
        cs = piece.slice(zm)
        if prev is not None:
            free = (cs - prev if outside is None else cs - prev - outside.slice(zm)).offset(-0.01, RND).offset(0.01, RND)
            for poly in free.to_polygons():
                q = np.asarray(poly)
                d = float(np.sqrt(((q[:, None, :] - q[None, :, :]) ** 2).sum(-1)).max()) if len(q) > 1 else 0.0
                if d > longest:
                    longest, at = d, zm
        prev = cs
    return longest, at


def plan_gap(a, b, z, most=1.0):
    """The gap in plan between a and b, cut at height z: how far a's section can grow before it
    meets b's (sideways only, not to the floor of a socket)."""
    ca, cb = a.slice(z), b.slice(z)
    lo, hi = 0.0, most
    if (ca ^ cb).area() > 1e-9:
        return 0.0
    for _ in range(24):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if (ca.offset(mid, m3.JoinType.Miter, 10) ^ cb).area() > 1e-9 else (mid, hi)
    return lo


def sweep(piece, others, path):
    """The worst overlap of piece with others at each step of a path of moves."""
    return max(overlap(piece.translate(t), others) for t in path)


def bbox(m):
    return m.bounding_box()


def free_move(part, other, d, step=0.01, most=3.0):
    """How far part moves along d (a unit vector) before it touches other."""
    t = 0.0
    while t < most and overlap(part.translate(list((t + step) * np.asarray(d, dtype=float))), other) < 1e-5:
        t += step
    return t


REST = 0.02            # how far a "rests on it" proof moves a part into what it rests on: far less than a layer
REST_MM2 = 1.0         # and the bearing it must find in every window of it, mm2 (REST * 1 mm2 = 0.02 mm3)


def rest_vols(part, base, windows, d=(0, 0, -1)):
    """How part rests on base all the way along, not only touching it somewhere (PRINTER-BRAIN, "A 'rests on it' proof
    must drop the part far less than a layer"; the 10x20 Cabin's roof_rest): moved REST along d (a unit vector, into
    base), the volume it meets base by inside each window (a box), in the windows' order. A part standing more than
    REST off anywhere meets nothing in the windows there. REST * REST_MM2 (0.02 mm3) in a window is 1 mm2 of bearing."""
    t = base ^ part.translate(list(REST * np.asarray(d, dtype=float)))
    return [overlap(t, w) for w in windows]


def rest_share(part, base, windows, face_z, min_face=REST_MM2):
    """As rest_vols, lowered: in each window (a box) where base's top face at face_z (the REST under it) has min_face
    mm2 or more, the share of that face part meets. [(window index, share)]; the face is worked out from base alone,
    so a part standing off where base is there to rest on meets none of it."""
    face = base ^ s.box(-s.BIG, s.BIG, -s.BIG, s.BIG, face_z - REST, face_z)
    cover = [overlap(face, w_) / REST for w_ in windows]
    met = rest_vols(part, base, windows)
    return [(k_, m_ / (REST * c_)) for k_, (m_, c_) in enumerate(zip(met, cover)) if c_ >= min_face]


def least_rest(vols, where):
    """(the least of vols, where it is: where[its index]) for a report; (inf, None) for none."""
    if not vols:
        return float("inf"), None
    k = int(np.argmin(vols))
    return vols[k], where[k]


# ---------------------------------------------------------------- the model
p = s.build()
pieces = {n: p[n] for n in s.WALL_CUTS}
WALLS = list(s.WALL_CUTS)
SIDES = list(s.SIDES)
fl = p["floor"]
body = p["body"]
F, B = p["front wall"], p["back wall"]
gable, frame, ceiling = p["porch gable"], p["porch frame"], p["porch ceiling"]
posts, rails = p["posts"], p["railings"]
upper, lower, door = p["upper"], p["lower"], p["door"]
zone = s.trim_zone()
pp = s.print_parts(p)
lofts = [s.loft(1), s.loft(-1)]
loft_set = s.union(lofts)
posts_all, rails_all = s.union(posts), s.union(rails)
door_shut = door.transform(s.door_to_shed(0))
sheets = {"right-side upper sheet": upper, "left-side upper sheet": upper.mirror([1, 0, 0]),
          "right-side lower sheet": lower, "left-side lower sheet": lower.mirror([1, 0, 0])}
roof_all = s.union(list(sheets.values()))
DROPS = [0.1 * k for k in range(1, 11)] + [1 + 0.5 * k for k in range(1, 279)]   # every 0.5 mm to 140 mm

# ================================================================ 1
group("1. pieces and bed")
angle_flat = pp["corner angles"]
fit_all = s.fit_test(pieces, fl)
n_fit = len(s.porch_joint_prints()) + len(s.fit_plate_2(pieces, fl))
for name, part, expect in ([("floor", pp["floor"], 1)] + [(n, s.union(pp[n]), 1) for n in WALLS + ["porch gable"]] +
                           [(n, pp[n], 1) for n in ("porch frame", "porch ceiling", "porch post", "side railing",
                                                    "front railing", "upper roof", "lower roof", "loft", "door", "skid")] +
                           [("skids", p["skids"], 2), ("fit test", fit_all, n_fit)] +
                           [("corner angle, " + n, m, 1) for n, m in angle_flat]):
    bb = part.bounding_box()
    size = (bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2])
    n = len(part.decompose())
    report(n == expect and max(size[0], size[1]) <= BED and size[2] <= BED,
           f"{name}: {n} solid piece(s) (expected {expect}), {size[0]:.2f} x {size[1]:.2f} x {size[2]:.2f} mm, "
           f"fits the {BED:.0f} mm bed whole")

parts5 = [fl] + [p[n] for n in WALLS]
v = abs(body.volume() - sum(x.volume() for x in parts5))
report(v < 0.01, f"floor and four walls add up to the whole body ({v:.4f} mm3 left over)")
worst = max(overlap(a, b) for a, b in itertools.combinations(parts5, 2))
report(worst < 0.001, f"no two of them overlap ({worst:.4f} mm3)")
wall_set = s.union([p[n] for n in WALLS])
v = max(overlap(fl.translate([dx, dy, 0]), wall_set) for dx, dy in ((0.14, 0), (-0.14, 0), (0, 0.14), (0, -0.14)))
report(v < 0.0001, f"the walls sit round the floor with {s.FIT} mm round every post, prong and end block and "
                   f"{s.FLOOR_CLR} mm inside the skirts (moved 0.14 mm it still clears: {v:.4f} mm3)")
# the front wall's closed pockets: 0.3 along the wall round each post and the sill, 0.2 across
ok, words = True, []
for a0, a1 in s.post_spans("front wall"):
    post = F ^ s.wall_box("front wall", a0 - 0.05, a1 + 0.05, -0.5, s.WT + 0.5, -1, s.ZF - 0.01)
    al = [overlap(post.translate([d, 0, 0]), fl) for d in (0.29, -0.29, 0.31, -0.31)]
    ac = [overlap(post.translate([0, d, 0]), fl) for d in (0.19, -0.19, 0.21, -0.21)]
    good = max(al[:2]) < 1e-6 and min(al[2:]) > 1e-4 and max(ac[:2]) < 1e-6 and min(ac[2:]) > 1e-4
    ok &= good
    words.append(f"{a0:.2f}..{a1:.2f}")
report(ok, f"the front wall's posts and door sill sit in closed pockets, free moved 0.29 along and 0.19 across, "
           f"touching moved 0.31 along or 0.21 across ({', '.join(words)})")
for sx in (1, -1):
    blk = F ^ s.box(*sorted([sx * (s.W / 2 - s.WT - 0.01), sx * (s.W / 2 + 1)]), s.YF - 1, s.YF + s.WT, -1, s.ZF - 0.01)
    free = max(overlap(blk.translate(t), fl) for t in ([-sx * 0.19, 0, 0], [0, -0.19, 0]))
    hit = min(overlap(blk.translate(t), fl) for t in ([-sx * 0.21, 0, 0], [0, -0.21, 0]))
    report(blk.bounding_box()[2] < 1e-6 and free < 1e-6 and hit > 1e-4,
           f"the front wall's {'+' if sx > 0 else '-'}x end block goes down to z {blk.bounding_box()[2]:.2f} in its corner "
           f"notch, 0.2 clear inward and toward the porch (moved 0.19: {free:.4f}, 0.21: {hit:.3f} mm3), open outside")

# ================================================================ 2
group("2. snap joints")


def toward(name, d):
    """Move d mm out from the middle of the cabin, square to the wall."""
    axis, sign = s.WALL_SIDE[name]
    t = [0.0, 0.0, 0.0]
    t[axis] = sign * d
    return t


def along(name, d):
    t = [0.0, 0.0, 0.0]
    t[1 - s.WALL_SIDE[name][0]] = d
    return t


# the floor with room for the barbs to pass, as if each leg were bent out of the way: what is
# left in the way of a wall coming down is only the snap itself
barb_room = []
for n in WALLS:
    for ac, sd in s.PRONGS[n]:
        (a0, a1), _ = s.prong_spans(ac, sd)
        barb_room.append(s.wall_box(n, a0 - s.FIT, a1 + s.FIT, -s.FIT, s.BARB, -1, s.ZF + 1))
fl_open = fl - s.union(barb_room)
sides_set = s.union([p[n] for n in SIDES])
order_others = {"front wall": fl_open,
                "right side": s.union([fl_open, F, door_shut]),
                "left side": s.union([fl_open, F, door_shut]),
                "back wall": s.union([fl_open, F, door_shut, sides_set, loft_set])}


def wall_rest(n, w):
    """How wall n (w, the wall itself) stands on the floor all along it: lowered REST, in every 1 mm along the wall
    where the floor's top is under its foot (the bottom plate, u 0.05 to SD - 0.05; on the front wall, which has no
    skirt and stands on the deck, its whole thickness), at least 1 mm2 of it (not in a notch, pocket or slot), the
    share of that floor it meets. Returns (the least share, where along the wall, how many mm looked at)."""
    axis = s.WALL_SIDE[n][0]
    u1 = (s.WT if n == "front wall" else s.SD) - 0.05
    bb = w.bounding_box()
    lo, hi = bb[1 - axis], bb[4 - axis]
    wins = [s.wall_box(n, a, a + 1.0, 0.05, u1, s.ZF - 1, s.ZF + 1) for a in np.arange(lo, hi - 0.5, 1.0)]
    face = fl ^ s.wall_box(n, lo - 1, hi + 1, 0.05, u1, s.ZF - REST, s.ZF + 1)
    cover = [overlap(face, b_) / REST for b_ in wins]
    met = rest_vols(w, fl, wins)
    share = [m_ / (REST * c_) for m_, c_ in zip(met, cover) if c_ >= REST_MM2]
    where = [lo + k + 0.5 for k, c_ in enumerate(cover) if c_ >= REST_MM2]
    least, at = least_rest(share, where)
    return least, at, len(share)


for n in ["front wall"] + SIDES + ["back wall"]:
    w = p[n] if n != "front wall" else s.union([F, door_shut])
    # it stands on the floor all along, not only somewhere (the 0.1 mm drop this was would pass a wall standing up
    # to 0.1 off, or off at one end): lowered 0.02 it meets at least half the floor's top under its foot in every mm
    least, at, k_ = wall_rest(n, p[n])
    report(least >= 0.5 and k_ > 40,
           f"{n} stands on the floor all along it: lowered {REST} mm it meets the floor's top under its foot in each of the "
           f"{k_} mm along it where the floor is there (not a notch, pocket or slot), at least {least * 100:.0f}% of it "
           f"there (the least {at:.1f} along it)")
    v = overlap(w.translate([0, 0, 0.3]), fl)
    report(v > 0.05, f"{n}: its {len(s.PRONGS[n])} prongs' barbs hold it down (lifted 0.3 mm they meet their ledges: "
                     f"{v:.2f} mm3)")
    vi, vo = overlap(w.translate(toward(n, -0.3)), fl), overlap(w.translate(toward(n, 0.3)), fl)
    va = min(overlap(w.translate(along(n, d)), fl) for d in (0.3, -0.3))
    report(min(vi, vo, va) > 0.05, f"{n}: the floor holds its foot in ({vi:.1f}), out ({vo:.1f}) and along ({va:.1f} mm3 "
                                   f"when moved 0.3 mm)")
    worst = sweep(w, order_others[n], [[0, 0, dz] for dz in DROPS])
    what = {"front wall": " with its door hung and shut, onto the bare floor",
            "right side": ", its front end past the front wall's end block", "left side": ", past the front wall's end block",
            "back wall": ", past the lofts and the side walls' mitres"}[n]
    report(worst < 0.001, f"{n} goes on straight down from 140 mm up{what}, nothing in the way but the barbs "
                          f"({worst:.4f} mm3)")
leg = s.LEG_ROOT - (s.LEDGE_Z - s.FIT)
strain = 1.5 * s.PRONG_T * s.CATCH / leg ** 2
room = s.SLOT_U - (s.BARB + s.PRONG_T + s.CATCH)
report(strain < 0.013 and room >= s.FIT - 0.001,
       f"each prong leg bends {s.CATCH:.2f} mm to let its barb through: {strain * 100:.2f}% strain on a {leg:.2f} mm leg "
       f"{s.PRONG_T} mm thick (PLA takes about 2%), with {room:.2f} mm to spare in its slot")
for n in WALLS:
    spans = [s.prong_spans(ac, sd) for ac, sd in s.PRONGS[n]]
    region = s.union([s.wall_box(n, min(l[0], st[0]) - 1, max(l[1], st[1]) + 1, -1, s.SD, -1, s.ZF + 1) for l, st in spans])
    pw = printed_in_shed(p[n], s.WALL_TO_PRINT[n], region)
    pf = printed_in_shed(fl, s.FLOOR_TO_PRINT, region)
    rest = overlap(pw, pf)
    held = overlap(pw.translate([0, 0, 0.3]), pf)
    (a0, a1), _ = spans[-1]

    def u_of(man):
        axis, sign = s.WALL_SIDE[n]
        bb = man.bounding_box()
        half = s.WALL_FACE[n]
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
           f"{n} as printed: each barb reaches {catch:.2f} mm under its ledge ({out_catch:.2f} with the foot pushed out "
           f"against its stops), with {ledge - top:.2f} mm over it to spring in; lifted 0.3 mm the printed barbs catch "
           f"({held:.2f} mm3), and seated nothing rubs ({rest:.3f} mm3)")
# the floor left between neighbouring cuts along each wall's line, measured on the floor itself
flng = s.floor(grooves=False)
sec = flng.slice(s.ZF - 0.5)
sk = [s.skid().transform(mt) for mt in s.skids_to_shed()]
for n, expect in (("right side", 2.26), ("left side", 2.26), ("front wall", 0.93), ("back wall", 0.73)):
    axis, sign = s.WALL_SIDE[n]
    strip = s.wall_box(n, -s.BIG, s.BIG, 1.0, 1.02, -1, 1)
    sbb = strip.bounding_box()
    line = sec ^ m3.CrossSection.square([sbb[3] - sbb[0], sbb[4] - sbb[1]]).translate([sbb[0], sbb[1]])
    spans = sorted((b.bounds()[1 - axis], b.bounds()[3 - axis]) for b in line.decompose())
    inner = [b - a for (a, b) in spans[1:-1]]
    least = min(inner)
    near_skid, between = 1e9, True
    for ac, sd in s.PRONGS[n]:
        (a0, a1), (b0, b1) = s.prong_spans(ac, sd)
        slot = s.wall_box(n, min(a0, b0) - s.FIT, max(a1, b1) + s.FIT, -s.FIT, s.SLOT_U, -1, s.ZF + 1)
        near_skid = min([near_skid] + [slot.min_gap(k, 50) for k in sk])
        for j in s.joist_ys():
            if axis == 0 and overlap(slot, s.box(-s.W, s.W, j - s.SW / 2, j + s.SW / 2, -1, s.ZF)) > 0:
                between = False
    report(least >= 0.6 and abs(least - expect) < 0.02 and near_skid >= 1.0 and between,
           f"{n}: the floor between neighbouring cuts along it is {least:.2f} mm at the least (spec {expect}), every "
           f"prong slot {min(near_skid, 99):.2f} mm or more from a skid and between joists")
# a side wall standing on its own: where its weight is, against the outside edge of the floor it
# tips over, and how far it leans before its posts stop it
H = s.ZWT - s.ZF


def tilt(piece, name, deg):
    """A side wall tipped out deg degrees about the outside top edge of the floor under it."""
    sx = s.WALL_SIDE[name][1]
    xp, zp = sx * (s.W / 2 - s.TS - s.FLOOR_CLR), s.ZF
    a = math.radians(deg) * sx
    c, sn = math.cos(a), math.sin(a)
    R = np.array([[c, 0, sn], [0, 1, 0], [-sn, 0, c]])
    t = np.array([xp, 0, zp]) - R @ np.array([xp, 0, zp])
    return piece.transform(np.column_stack([R, t]))


for n in SIDES:          # both long walls: since the standard layout each has the same window
    sx = s.WALL_SIDE[n][1]
    w = p[n]
    mesh = w.to_mesh()
    vv = np.asarray(mesh.vert_properties)[:, :3]
    tt = np.asarray(mesh.tri_verts)
    a_, b_, c_ = vv[tt[:, 0]], vv[tt[:, 1]], vv[tt[:, 2]]
    vol6 = np.einsum("ij,ij->i", a_, np.cross(b_, c_))
    com = ((a_ + b_ + c_) * vol6[:, None]).sum(0) / (4 * vol6.sum())
    u_com = sx * com[0] - (s.W / 2 - s.WT)
    u_edge = s.SD - s.FLOOR_CLR
    deg = 0.0
    while deg < 6 and overlap(tilt(w, n, deg + 0.05), fl) < 1e-3:
        deg += 0.05
    lean = math.radians(deg) * H
    tip = w.volume() * (u_com - u_edge)
    hold = sum(l.volume() for l in lofts) / 2 * u_edge
    report(tip > 0 and hold > 2 * tip,
           f"{n} standing alone leans out {deg:.2f} degrees, about {lean:.1f} mm at the top (its weight is {u_com:.2f} mm "
           f"out from its inside face, past the floor's edge at {u_edge:.2f}); with both lofts on its top plates it stays "
           f"upright once pushed straight: tipping it lifts their ends, {hold:.0f} against its own {tip:.0f} (mm3 x mm)")
# the other way: a side wall pushed in a little at the top. The back wall's bottom must meet the
# bevel on the side wall's mitre, which pushes it back out, not land flat on the mitre's top corner
z_top = s.ZWT - 0.15
ok_in, met = True, 0
for lean_mm in (0.2, 0.3, 0.5):
    a = -math.atan(lean_mm / H)
    xp, zp = s.W / 2 - s.WT, s.ZF
    R = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    lw_i = p["right side"].transform(np.column_stack([R, np.array([xp, 0, zp]) - R @ np.array([xp, 0, zp])]))
    lo, hi = 0.0, 100.0
    if overlap(B, lw_i) < 1e-4:
        continue
    met += 1
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if overlap(B.translate([0, 0, mid]), lw_i) > 1e-4 else (lo, mid)
    for c in (B.translate([0, 0, hi - 0.02]) ^ lw_i).decompose():
        tb = c.bounding_box()
        if c.volume() > 1e-5 and not (z_top - s.MITRE_BEVEL - 0.1 < tb[2] and tb[5] < z_top - 0.05):
            ok_in = False
report(ok_in and met > 0, f"with a side wall pushed in up to 0.5 mm at the top, the back wall coming down first meets the "
                          f"{s.MITRE_BEVEL} mm bevel on the side wall's mitre ({met} of 3 leans touch it), never the "
                          f"mitre's flat top")

# ================================================================ 3
group("3. walls print")
# each wall, the porch gable, the floor and the loft as printed is its cabin piece turned, never mirrored:
# of the 24 ways to turn a piece square to the bed, one puts the cabin piece exactly onto the printed one.
# A mirrored print (the door left of the window as you look at the front wall's outside face) matches none
# of them (review Nov 3 2026). And every matrix that lays a piece on the bed is a rotation, det +1
ROTS = []
for perm_ in itertools.permutations(range(3)):
    for sg_ in itertools.product((1, -1), repeat=3):
        R_ = np.zeros((3, 3))
        for i_ in range(3):
            R_[i_, perm_[i_]] = sg_[i_]
        if np.linalg.det(R_) > 0:
            ROTS.append(R_)
turned_ok, turned_words = len(ROTS) == 24, []
for n, cab, prn in ([(n_, p[n_], s.union(pp[n_])) for n_ in WALLS + ["porch gable"]] +
                    [("floor", fl, pp["floor"]), ("loft", p["loft"], pp["loft"])]):
    pb_ = prn.bounding_box()
    best = None
    for R_ in ROTS:
        q_ = cab.transform(np.column_stack([R_, np.zeros(3)]))
        qb_ = q_.bounding_box()
        if max(abs((qb_[3 + k_] - qb_[k_]) - (pb_[3 + k_] - pb_[k_])) for k_ in range(3)) > 1e-4:
            continue
        q_ = q_.translate([pb_[0] - qb_[0], pb_[1] - qb_[1], pb_[2] - qb_[2]])
        d_ = q_.volume() + prn.volume() - 2 * overlap(q_, prn)
        best = d_ if best is None else min(best, d_)
    turned_ok &= best is not None and best < 0.01
    turned_words.append(f"{n} {best if best is not None else float('nan'):.4f}")
mats_ = ([("walls' " + k_, v_) for k_, v_ in s.WALL_TO_PRINT.items()] + [("porch gable", s.GABLE_TO_PRINT),
         ("floor", s.FLOOR_TO_PRINT), ("loft", s.LOFT_TO_PRINT)] + [(f"corner angle {k_:+d}", v_) for k_, v_ in s.CORNER_TO_PRINT.items()])
dets_ = [np.linalg.det(np.array(v_, dtype=float)) for _, v_ in mats_]
report(turned_ok and all(abs(d_ - 1) < 1e-9 for d_ in dets_),
       f"every wall, the porch gable, the floor and the loft print the right hand, turned not mirrored: a turn of the "
       f"cabin piece lies exactly on the printed one (mm3 apart: {', '.join(turned_words)}); all {len(mats_)} print "
       f"matrices are rotations (det {min(dets_):+.0f} to {max(dets_):+.0f})")
for n in WALLS + ["porch gable"]:
    siding, trim_p = pp[n]
    whole = s.union(pp[n])
    bb = whole.bounding_box()
    foot = whole.trim_by_plane([0, 0, -1], -0.2)
    fbb = foot.bounding_box()
    mitres = {"back wall": 2, "right side": 1, "left side": 1}.get(n, 0)
    allow = mitres * (s.WT + s.PROUD) + (2 * s.GROOVE_D if n == "front wall" else 0)   # its end blocks' chamfers
    report(fbb[3] - fbb[0] > (bb[3] - bb[0]) - allow - 0.1 and fbb[4] - fbb[1] > 0.9 * (bb[4] - bb[1]),
           f"{n} lies flat on its framing ({foot.volume() / 0.2:.0f} mm2 on the bed, {fbb[3] - fbb[0]:.1f} of "
           f"{bb[3] - bb[0]:.1f} mm long)")
    worst, longest = worst_overhang(whole)
    report(worst < 5, f"{n} has nothing steeper than 45 degrees that isn't a bridge of 20 mm or less ({worst:.2f} mm2 "
                      f"worst layer, bridges up to {longest:.1f} mm)")
    thin = max((c - c.offset(-0.2, RND).offset(0.2, RND)).area() for c in (whole.slice(0.125), whole.slice(0.35)))
    report(thin < 2, f"{n}: no knife edges on the bed ({thin:.2f} mm2 thinner than a line in the first two layers)")
    above = (siding ^ s.box(-BED, 2 * BED, -BED, 2 * BED, s.WT + 1e-4, BED)).volume()
    top = printed_top(s.WT)
    lost = abs(siding.volume() + (0 if trim_p.is_empty() else trim_p.volume()) - (p[n] if n in p else gable).volume())
    report(lost < 0.01 and siding.bounding_box()[5] <= s.WT + 1e-6,
           f"{n}: its siding-colour and trim-colour parts add up to the whole ({lost:.4f} mm3 lost), the siding part "
           f"{siding.bounding_box()[5]:.3f} mm tall")
    # every wall has trim now: both long walls a window casing since the standard layout
    tb = trim_p.bounding_box() if not trim_p.is_empty() else [0, 0, -1, 0, 0, -1]
    report(trim_p.volume() > 0 and abs(tb[5] - (s.WT + s.PROUD)) < 0.01 and tb[2] > s.WT - 0.01 and above < 1e-6,
           f"{n}: trim is {trim_p.volume():.1f} mm3, all of it in the top {s.PROUD} mm ({tb[2]:.2f} to {tb[5]:.2f} mm, "
           f"printing 5.05 to 5.65), and nothing in filament 1 above the siding's top layer ({top:.2f} mm)")
# the trim each wall must have: as many pieces as drawn, each with the volume of the boards' 0.6 proud.
# The casings' areas from the opening sizes (a door 3 ft wide and Alan's 73 1/2 in tall has two sides and a head,
# a 2.1 x 2.9 ft window four sides), one door and one window on the front wall, one window on each long wall
FT_ = s.FT
DOOR_H_FT = ALAN["door h"] / 12
door_cas = (STD["door w"] * FT_ + 2 * s.TRIM) * (DOOR_H_FT * FT_ + s.TRIM) - STD["door w"] * DOOR_H_FT * FT_ ** 2
win_cas = (STD["win w"] * FT_ + 2 * s.TRIM) * (STD["win h"] * FT_ + 2 * s.TRIM) - STD["win w"] * STD["win h"] * FT_ ** 2
expect_vol = {"front wall": (door_cas + win_cas) * s.PROUD, "right side": win_cas * s.PROUD, "left side": win_cas * s.PROUD}
faux_area = (STD["faux w"] * STD["faux h"] - (STD["faux w"] - 2 * STD["faux bar"]) * (STD["faux h"] - 2 * STD["faux bar"])
             + 4 * STD["faux tri"] ** 2 / 2) * FT_ ** 2
g2 = m3.CrossSection([s.GABLE])
above_cs = m3.CrossSection.square([4 * s.W, 400]).translate([-2 * s.W, s.ZWT])
rake_area = ((g2.offset(-0.1, m3.JoinType.Miter) - g2.offset(-2.1, m3.JoinType.Miter)) ^ above_cs).area()
band_area = (g2 ^ m3.CrossSection.square([s.W, s.TRIM]).translate([-s.W / 2, s.BAND_Z])).area()
band_cs = (g2 ^ m3.CrossSection.square([s.W, s.TRIM]).translate([-s.W / 2, s.BAND_Z]))
band_rake = (band_cs + ((g2.offset(-0.1, m3.JoinType.Miter) - g2.offset(-2.1, m3.JoinType.Miter)) ^ above_cs)).area()
expect_vol["back wall"] = band_rake * s.PROUD
expect_vol["porch gable"] = (rake_area + faux_area) * s.PROUD
expect_n = {"front wall": 2, "right side": 1, "left side": 1, "back wall": 1, "porch gable": 2}
what_n = {"front wall": "door casing, one window casing", "right side": "window casing", "left side": "window casing",
          "back wall": "band and rake board, which meet", "porch gable": "rake board, faux loft window"}
for n in ("front wall", "right side", "left side", "back wall", "porch gable"):
    trim_p = pp[n][1]
    k = len(trim_p.decompose())
    e = abs(trim_p.volume() / expect_vol[n] - 1)
    report(k == expect_n[n] and e < 0.01,
           f"{n}: filament 2 is {k} piece(s) (expected {expect_n[n]}: {what_n[n]}), "
           f"{trim_p.volume():.1f} mm3 against {expect_vol[n]:.1f} drawn ({e * 100:.2f}% off)")
for n in SIDES + ["front wall"]:
    v = p[n].trim_by_plane([0, 0, 1], s.ZWT - 0.15 + 0.001).volume()
    report(v < 1e-6, f"{n}: nothing above {s.ZWT - 0.15:.3f} (the gables carry the roof) ({v:.4f} mm3)")
# the loft notches: through the whole top plate, no sliver left, the floor the plates' underside or a stud top
zf_notch = s.LOFT_Z - s.LUG_D - s.FIT
worst_left, floors_ok, sliver, face_ok = 0.0, True, 0.0, True
for n in SIDES:
    sx = s.WALL_SIDE[n][1]
    for sy in (1, -1):
        for i in s.LUG_JOISTS:
            y = s.loft_y(s.loft_joist_ys()[i], sy)
            y0, y1 = y - s.SW / 2 - s.FIT, y + s.SW / 2 + s.FIT
            if sy < 0 and i == 0:
                y0 = s.YS
            y1f = y1 - (s.NOTCH_FILL + 0.02 if (sy > 0 and i == 0) else 0.01)     # the back loft's notch fill
            u_out = s.FRONT_NOTCH_U if (sy < 0 and i == 0) else s.LUG_U + s.FIT
            fp = s.wall_box(n, y0 + 0.01, y1f, -0.99, u_out - 0.01, zf_notch + 0.001, s.ZWT)
            if sy < 0 and i == 0:                     # and the wall starts again right there, outside it
                face_ok &= overlap(p[n], s.wall_box(n, y0 + 0.01, y1f, u_out + 0.01, u_out + 0.2, zf_notch + 0.01, s.ZWT - 0.16)) > 0.2
            worst_left = max(worst_left, overlap(p[n], fp))
            below = p[n] ^ s.wall_box(n, y0 + 0.01, y1f, 0.01, s.LUG_U + s.FIT - 0.01, zf_notch - 0.5, zf_notch + 0.001)
            if not below.is_empty() and abs(below.bounding_box()[5] - zf_notch) > 1e-4:
                floors_ok = False
            xi = s.W / 2 - s.WT
            xa, xb = sorted([sx * (xi - 0.5), sx * (xi + 2.5)])
            part = print_part(p[n], s.WALL_TO_PRINT[n], s.box(xa, xb, y0 - 1.5, y1 + 1.5, zf_notch - 1.5, s.ZWT + 1))
            for z in (0.125, 0.35):
                c = part.slice(z)
                sliver = max([sliver] + [b.area() for b in (c - c.offset(-0.21, RND).offset(0.21, RND)).decompose()])
front_room = s.FRONT_NOTCH_U - s.LUG_U
report(worst_left < 1e-6 and floors_ok and sliver < 0.15 and face_ok and abs(front_room - 0.45) < 1e-6,
       f"the 8 loft notches run right through the top plates to {zf_notch:.3f} (nothing left in them: {worst_left:.4f} "
       f"mm3), each floor the plates' underside or a stud top; in the first two layers nothing beside them is under a line "
       f"wide ({sliver:.3f} mm2 at most); the four for the front loft's end joist, which run out through the side walls' "
       f"front ends, are {s.FRONT_NOTCH_U:.2f} deep, {front_room:.2f} past their lug, so the plate printed over each "
       f"(held on two sides only) has a layer to sag")
# the standard layout's list, worked out by hand from the addendum's openings: each long wall's window
# (y 9.049..29.051) puts its full studs on the marks 16 in each side of the wall's middle; the front
# window (x -34.480..-14.478) puts its -x king on the mark 44 in left of the middle; the door (x
# 2.286..30.861) has the marks at +4, +20 and +36 in over it, where its header is right under the top plates
# (Alan's 79 1/2 in wall and 73 1/2 in door, Nov 4 2026), so they get no cripples, and none of them is dropped
SPEC_DROPPED = {("right side", -16.0, "full stud", 0.28), ("right side", 16.0, "full stud", 0.28),
                ("left side", -16.0, "full stud", 0.28), ("left side", 16.0, "full stud", 0.28),
                ("front wall", -44.0, "king stud", 1.04), ("back wall", 52.0, "end stud", 0.54)}
got = {(w_, i_, "full stud" if "full stud" in h_ else "king stud" if "king" in h_ else "end stud" if "end stud" in h_ else h_, o_)
       for w_, i_, h_, o_ in s.DROPPED_MARKS}
# and the framing: no stud box at a dropped mark, and where part of its span is left uncovered by the
# framing it hit, the wall is open bay there
empty, probed, in_layout = 0.0, 0, False
for w_, inch, what, ov in s.DROPPED_MARKS:
    a = s.WALL_MIDDLE[w_] + inch * s.S
    a0, a1 = a - s.SW / 2, a + s.SW / 2
    boxes = s.framing_layout(w_)[0]
    in_layout |= any(abs((b[0] + b[1]) / 2 - a) < 0.01 and abs(b[1] - b[0] - s.SW) < 1e-6 for b in boxes)
    zm = s.ZF + 22
    cover = sorted((max(b[0], a0), min(b[1], a1)) for b in boxes if b[4] < zm < b[5] and b[1] > a0 and b[0] < a1)
    free_, x = [], a0
    for c0, c1 in cover:
        if c0 > x + 0.05:
            free_.append((x, c0))
        x = max(x, c1)
    if a1 > x + 0.05:
        free_.append((x, a1))
    for f0, f1 in free_:
        probed += 1
        empty += overlap(p[w_], s.wall_box(w_, f0 + 0.02, f1 - 0.02, 0.5, s.SD - 0.5, zm - 2, zm + 2))
report(len(s.DROPPED_MARKS) == len(SPEC_DROPPED) and got == SPEC_DROPPED and not in_layout and empty < 1e-6,
       f"DROPPED_MARKS is the standard layout's list exactly ({'; '.join(f'{w_} {i_:+.0f} in on {h_}, {o_:.2f}' for w_, i_, h_, o_ in s.DROPPED_MARKS)}); "
       f"no stud is laid out at those marks, and the {probed} bits of their spans the framing they hit leaves are open "
       f"bay ({empty:.4f} mm3)")
# nothing in an opening: Alan's standard openings (STD, the addendum's numbers), each through its wall.
# No framing member (stud, king, plate, header, cripple, window plate) reaches into any of them; the
# wall piece has nothing in a window but its two sashes (drawn at the STD spot) and nothing in the
# doorway but the stop's 0.8 at the latch jamb; nothing else of the model is in the doorway but the
# door; under the doorway the front wall has only its sill (no post, prong or pocket of its own)
STD_OPEN = {"front wall": [(STD["front window"] * s.FT, STD["win w"] * s.FT, "window"),
                           (STD["door"] * s.FT, STD["door w"] * s.FT, "door")],
            "right side": [((STD["side middle"] + STD["side window"]) * s.FT, STD["win w"] * s.FT, "window")],
            "left side": [((STD["side middle"] + STD["side window"]) * s.FT, STD["win w"] * s.FT, "window")],
            "back wall": []}


def std_zs(kind):
    return ((s.ZF, s.ZF + DOOR_H_FT * s.FT) if kind == "door" else
            (s.ZF + s.WIN_TOP - STD["win h"] * s.FT, s.ZF + s.WIN_TOP))


in_frame, in_wall, words = 0.0, 0.0, []
for n, ops in STD_OPEN.items():
    boxes = s.framing_layout(n)[0]
    for c, w_, kind in ops:
        a0, a1 = c - w_ / 2, c + w_ / 2
        z0, z1 = std_zs(kind)
        for b in boxes:
            da = min(b[1], a1) - max(b[0], a0)
            dz = min(b[5], z1) - max(b[4], z0)
            if da > 1e-6 and dz > 1e-6:
                in_frame += da * dz
        # (the stop's 0.8 is on the latch jamb, the left one: Alan hinges the door on the right, Nov 4 2026)
        hole = s.wall_box(n, a0 + (0.81 if kind == "door" else 0.01), a1 - 0.01, -0.5, s.WT + s.PROUD + 0.5,
                          z0 + 0.01, z1 - 0.01)
        what = p[n] if kind == "door" else p[n] - s.union(s.window_unit(n, c))
        in_wall += overlap(what, hole)
        words.append(f"{n} {kind} {a0:.3f}..{a1:.3f}")
c, w_, _ = STD_OPEN["front wall"][1]
doorway = s.wall_box("front wall", c - w_ / 2 + 0.81, c + w_ / 2 - 0.01, -3, s.WT + 3, s.ZF + 0.01, s.ZF + DOOR_H_FT * s.FT - 0.01)
others_in = overlap(s.union([fl, B, gable, frame, ceiling, posts_all, rails_all, loft_set, roof_all] + [p[n_] for n_ in SIDES]), doorway)
door_in = overlap(door_shut, doorway)
sill_d = (c - w_ / 2 - 2 * s.SW, c + w_ / 2 + 2 * s.SW)
crossing = [sp for sp in s.post_spans("front wall") if sp[1] > c - w_ / 2 and sp[0] < c + w_ / 2]
prong_in = [ac for ac, sd in s.PRONGS["front wall"] for lo_, hi_ in s.prong_spans(ac, sd)
            if hi_ + s.FIT > sill_d[0] - s.POCKET_ALONG - 0.6 and lo_ - s.FIT < sill_d[1] + s.POCKET_ALONG + 0.6]
report(in_frame < 1e-9 and in_wall < 1e-3 and others_in < 1e-3 and door_in > 100 and len(crossing) == 1 and
       abs(crossing[0][0] - sill_d[0]) < 1e-6 and abs(crossing[0][1] - sill_d[1]) < 1e-6 and not prong_in,
       f"nothing in an opening ({'; '.join(words)}): no framing member reaches into one ({in_frame:.4f} mm2), the walls "
       f"have nothing in them but the windows' sashes and the door stop ({in_wall:.4f} mm3), nothing else of the model "
       f"is in the doorway ({others_in:.4f} mm3) but the door ({door_in:.0f} mm3); under the doorway only the sill "
       f"{crossing[0][0] if crossing else 0:.3f}..{crossing[0][1] if crossing else 0:.3f} (a king and a full stud each side), "
       f"and no prong within 0.6 of its pocket")
# the two long walls are framed alike, the left side's window exactly as the right side's, mirrored
fr_r, fr_l = s.framing_layout("right side")[0], s.framing_layout("left side")[0]
vr, vl = p["right side"].volume(), p["left side"].volume()
mir = abs(vr - overlap(p["right side"], p["left side"].mirror([1, 0, 0])))
report(fr_r == fr_l and abs(vr - vl) < 0.01 and mir < 0.01,
       f"the left side is the right side's mirror image, window, framing and all ({len(fr_l)} framing members the same, "
       f"{vl:.1f} and {vr:.1f} mm3, {mir:.4f} mm3 apart mirrored)")
# the headers over Alan's standard openings, from his rules and answers typed in here (spec F8, BUILDING-TERMS.md,
# ALAN), not from make_barn_cabin.py: over each 2x3 window his 5 in loft header right up under the two 1 1/2 in top
# plates of his 79 1/2 in wall (76 1/2 in), so from the window's top at 71 1/2 in, bearing 1 1/2 in on a king each
# side, and the flat window plate under the window; over the door his two flat 2x4s, 3 in, from the door's top
# (73 1/2 in) right up under the top plates too, on its two kings standing on the bottom plate (72 in on Alan's
# 1 1/2 in plate; on the model's 1.6 mm plate, PLATE_BOT_MM, they are 0.52 in shorter, and this proves it). Each is in the
# wall's framing list and solid in the wall itself (the door's header has the top pin's hole in it), and nothing is
# framed between the header and the top plates over the door: no cripple, no block
IN_ = s.S
under_plates = ALAN["wall h"] - 2 * ALAN["plate"]
kings_in = ALAN["door h"] - ALAN["plate"]
hdr_ok, hdr_words = True, []
for n, ops in STD_OPEN.items():
    boxes = s.framing_layout(n)[0]
    for c, w_, kind in ops:
        a0, a1 = c - w_ / 2, c + w_ / 2
        if kind == "window":
            top_, hdr_top, need = s.ZF + (under_plates - ALAN["loft header"]) * IN_, s.ZF + under_plates * IN_, 0.999
        else:
            top_, hdr_top, need = s.ZF + ALAN["door h"] * IN_, s.ZF + (ALAN["door h"] + ALAN["flat header"]) * IN_, 0.95
            hdr_ok &= abs(ALAN["door h"] + ALAN["flat header"] - under_plates) < 1e-9 and abs(kings_in - ALAN["king"]) < 1e-9
            over = [b for b in boxes if b[1] > a0 - 1.5 * IN_ + 1e-6 and b[0] < a1 + 1.5 * IN_ - 1e-6
                    and b[5] > hdr_top + 1e-6 and b[4] < s.ZF + under_plates * IN_ - 1e-6]
            hdr_ok &= not over
        want = [("header", a0 - 1.5 * IN_, a1 + 1.5 * IN_, top_, hdr_top, need),
                ("kings", a0 - 1.5 * IN_, a0, s.ZF + PLATE_BOT_MM, top_, 0.999),
                ("kings", a1, a1 + 1.5 * IN_, s.ZF + PLATE_BOT_MM, top_, 0.999)]
        if kind == "window":
            bot_ = top_ - STD["win h"] * s.FT
            want.append(("window plate", a0, a1, bot_ - 1.5 * IN_, bot_, 0.999))
        fr_, king_len = [], []
        for what, b0, b1, z0, z1, need_ in want:
            hits_ = [b for b in boxes if abs(b[0] - b0) < 1e-3 and abs(b[1] - b1) < 1e-3 and abs(b[4] - z0) < 1e-3
                     and abs(b[5] - z1) < 1e-3 and abs(b[2]) < 1e-6 and abs(b[3] - s.SD) < 1e-6]
            probe = s.wall_box(n, b0 + 0.01, b1 - 0.01, 0.01, s.SD - 0.01, z0 + 0.01, z1 - 0.01)
            frac = overlap(p[n], probe) / probe.volume()
            hdr_ok &= bool(hits_) and frac >= need_
            fr_.append(frac)
            if what == "kings" and hits_:
                king_len.append((hits_[0][5] - hits_[0][4]) / IN_)
        # the door's kings as the model has them: on its 1.6 mm bottom plate (PLATE_BOT_MM, 2.02 in, held for the
        # snaps' legs, not Alan's 1 1/2 in) up to his 73 1/2 in head, so 71.48 in, the read me's 71 1/2, 0.52 in
        # shorter than his 72: both of them, each that long in the framing list
        if kind == "door":
            want_king = ALAN["door h"] - PLATE_BOT_MM / IN_
            hdr_ok &= len(king_len) == 2 and all(abs(k_ - want_king) < 0.01 for k_ in king_len)
        kings_words = (f", {' and '.join(f'{k_:.2f}' for k_ in king_len)} in long (want {ALAN['door h'] - PLATE_BOT_MM / IN_:.2f}) "
                       f"on the model's {PLATE_BOT_MM / IN_:.2f} in ({PLATE_BOT_MM} mm) bottom plate (Alan's "
                       f"{ALAN['king']:.0f} on his {ALAN['plate']} in)" if kind == "door" and king_len else
                       f", {len(king_len)} of its kings in the framing list from the model's {PLATE_BOT_MM} mm bottom "
                       f"plate up to the head" if kind == "door" else "")
        hdr_words.append(f"{n} {kind}: header {(top_ - s.ZF) / IN_:.1f} to {(hdr_top - s.ZF) / IN_:.1f} in over "
                         f"{(a0 - 1.5 * IN_):.3f}..{(a1 + 1.5 * IN_):.3f} ({fr_[0] * 100:.1f}% solid), kings "
                         f"{min(fr_[1:3]) * 100:.1f}%" + kings_words
                         + (f", window plate {fr_[3] * 100:.1f}%" if kind == "window" else ""))
report(hdr_ok, f"Alan's headers over the standard openings, each in the framing list and solid in the wall: "
               f"{'; '.join(hdr_words)}")
# the floor and the lofts print upside down: their face is on the bed, and nothing hangs over
for name, ff in (("floor", pp["floor"]), ("loft", pp["loft"])):
    fbb = ff.bounding_box()
    foot = ff.slice(0.125).area()
    deck = ff.slice(0.6).area()                       # the deck under the grooves, as solid as it gets
    worst, longest = worst_overhang(ff)
    what = (f"the roofs of the post sockets and railing holes are bridges up to {longest:.1f} mm" if name == "floor" else
            f"its joists and lugs stand on the deck, no bridges")
    report(foot > 0.95 * deck and worst < 0.5,
           f"the {name} prints face down ({foot:.0f} mm2 on the bed of {deck:.0f} of deck), nothing hanging over that isn't a "
           f"bridge of 20 mm or less ({worst:.2f} mm2 worst layer; {what})")
for name in ("upper roof", "lower roof"):
    piece = pp[name]
    bb = piece.bounding_box()
    foot = piece.slice(0.125).area()
    worst, longest = worst_overhang(piece)
    report(foot > 0.9 * (bb[3] - bb[0]) * (bb[4] - bb[1]) and worst < 5,
           f"the {name} sheet prints flat on its underside ({foot:.0f} mm2 on the bed), nothing steeper than 45 degrees "
           f"but its peg holes' roofs ({worst:.1f} mm2 worst layer, bridges up to {longest:.1f} mm)")
# the one-colour parts that print as they come off the plate: the porch posts and railings, the ceiling,
# the door and the skids. The door's rounded hinge edge starts a little under 45 degrees on the bed
# (a 1 mm radius along its whole height), so it is allowed 2 mm2; the others nothing
for name, allow in (("porch post", 0.01), ("side railing", 0.01), ("front railing", 0.01), ("porch ceiling", 0.01),
                    ("door", 2.0), ("skid", 0.01)):
    piece = pp[name]
    worst, longest = worst_overhang(piece)
    fl_ = floating(piece)
    foot = piece.slice(0.125).area()
    report(worst < allow and fl_ < max(allow, 0.01) and foot > 1.0,
           f"the {name} prints as laid out ({foot:.0f} mm2 on the bed), nothing steeper than 45 degrees that isn't a "
           f"bridge of 20 mm or less ({worst:.2f} mm2 worst layer{', at its rounded hinge edge' if name == 'door' else ''}, "
           f"bridges up to {longest:.1f} mm), and as the slicer lays it with lines under 0.42 dropped {fl_:.2f} mm2 "
           f"at worst past 45 degrees")

# ================================================================ 4
group("4. corners")
U, V, Z = np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), np.array([0, 0, 1.0])
DIRS = [np.array(d, dtype=float) / np.linalg.norm(d) for d in itertools.product((-1, 0, 1), repeat=3) if any(d)]
around = s.cbox(-12, 4, -12, 4, -2, 200)
trim_all = s.union(s.wall_trims())
swing = [door.transform(s.door_to_shed(deg)) for deg in range(0, 99, 7)]
REACH, REACH_E = s.angle_reach()
PR0, PR1 = -(REACH + s.POCKET_CLR) + 0.25, -1.75          # a band of recess floor, clear of the chamfer


def corner_set(sx, sy, walls):
    def home(m):
        return s.at_corner(m, sx, sy)
    long_n, end_n = s.corner_walls(sx, sy)
    return home(walls[long_n]) ^ around, home(walls[end_n]) ^ around, home


def clear_moves(part, lw, ew, d):
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
           f"corner angle, {where}: sits in both recesses touching neither wall ({none:.4f} mm3) but on the recess floors "
           f"({seat:.1f} mm3 pressed 0.05 mm in); moved 0.2 mm along the side wall or 0.3 mm along the back wall it meets "
           f"the recess's edge ({edge:.2f}), and 0.2 mm up the recess's top ({up:.2f} mm3)")
    worst = clear_moves(a, lw, ew, 0.09)
    fillet = (a ^ s.cbox(-1.5, -0.45, -1.5, -0.45, 10, 60)).min_gap(s.union([lw, ew]), 1.0)
    report(worst < 1e-4 and 0.2 <= fillet <= 0.3,
           f"corner angle, {where}: moved 0.09 mm any of 26 ways but into a recess floor it touches neither wall "
           f"({worst:.5f} mm3); its fillet is {fillet:.3f} mm off the walls' chamfer")
    press = max(overlap(a.translate(t * e), s.union([lw, ew])) for e in (U, V, (U + V) / math.sqrt(2))
                for t in np.arange(0.02, 1.51, 0.02))
    report(press < 1e-4, f"corner angle, {where}: presses straight into its recesses from 1.5 mm out, square to either "
                         f"wall or into the corner, without catching ({press:.5f} mm3)")
    moved = max(overlap(a.translate(d * n_a), w_b) for n_a, w_b in ((U, ew), (V, lw)) for d in (0.15, -0.15))
    report(moved < 1e-3, f"corner angle, {where}: with either wall sitting 0.15 mm out or in, the angle still touches "
                         f"nothing of the other wall ({moved:.4f} mm3)")
    face_l = (a ^ s.cbox(s.ANGLE_P - 0.01, 2, -10, 10, -1, 200)).bounding_box()
    face_e = (a ^ s.cbox(-10, 10, s.ANGLE_P - 0.01, 2, -1, 200)).bounding_box()
    cover_l, cover_e = s.L / 2 - face_l[1], s.W / 2 - face_e[0]
    foot = a.bounding_box()[2] - min(lw.bounding_box()[2], ew.bounding_box()[2])
    report(min(cover_l, cover_e) >= 2.95 and abs(foot) < 1e-6,
           f"corner angle, {where}: covers the mitre's outside edge by {cover_l:.2f} mm on the side wall's face and "
           f"{cover_e:.2f} on the back wall's ({cover_l / s.S:.2f} in), from its foot, level with the skirts, up to "
           f"{face_l[5]:.2f} mm")
    roof_c = home(roof_all)
    gap = a.min_gap(roof_c, 1.0)
    low = overlap(a, roof_c.translate([0, 0, -0.15]))
    report(gap >= s.ROOF_CLR - 0.002 and low < 1e-4,
           f"corner angle, {where}: {gap:.3f} mm clear of the roof sheets at the closest, square to them, and with the "
           f"roof 0.15 mm lower still clear ({low:.5f} mm3)")
    gap_t = a.min_gap(home(trim_all), 1.0)
    gap_l = a.min_gap(home(loft_set), 5.0)
    report(gap_t >= 0.1 and gap_l >= 0.1, f"corner angle, {where}: {gap_t:.2f} mm clear of the back wall's rake board over "
                                          f"it, and {gap_l:.1f} clear of the lofts")
for sx, sy in s.CORNERS:
    lw_n, ew_n = s.corner_walls(sx, sy)
    where = "%s at %s" % (lw_n, ew_n)
    _, _, home = corner_set(sx, sy, p)
    region = home(s.cbox(-12, 2, -12, 2, 30, 60))
    pl = home(printed_in_shed(p[lw_n], s.WALL_TO_PRINT[lw_n], region))
    pe = home(printed_in_shed(p[ew_n], s.WALL_TO_PRINT[ew_n], region))
    pa = home(printed_in_shed(s.corner_angle(sx, sy), s.CORNER_TO_PRINT[sx], region))
    floor_u = (pl ^ s.cbox(-3, 1, PR0, PR1, 40, 50)).bounding_box()[3] - s.W / 2
    floor_v = (pe ^ s.cbox(PR0, PR1, -3, 1, 40, 50)).bounding_box()[4] - s.L / 2
    du = floor_u - ((pa ^ s.cbox(-1, 1, PR0, PR1, 40, 50)).bounding_box()[0] - s.W / 2)
    dv = floor_v - ((pa ^ s.cbox(PR0, PR1, -1, 1, 40, 50)).bounding_box()[1] - s.L / 2)
    seated = pa.translate([du, dv, 0])
    v = overlap(seated, s.union([pl, pe]))
    on = min(overlap(seated.translate(-0.01 * U), pl), overlap(seated.translate(-0.01 * V), pe))
    shut = 0.1 / math.sqrt(2)
    v_shut = overlap(seated.translate(-shut * V), s.union([pl, pe.translate(shut * (U - V))]))
    tip_e = seated.bounding_box()[0] - (pe ^ s.cbox(-6, -REACH_E, -0.3, 1, 40, 50)).bounding_box()[3]
    tip_l = seated.bounding_box()[1] - (pl ^ s.cbox(-0.3, 1, -6, -REACH, 40, 50)).bounding_box()[4]
    box2 = m3.CrossSection.square([2.4, 2.4]).translate([s.W / 2 - 3, s.L / 2 - 3])
    ws, fs = s.union([pl, pe]).slice(45.0) ^ box2, seated.slice(45.0) ^ box2
    lo, hi = 0.0, 0.5
    for _ in range(14):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if (fs.offset(mid, RND) ^ ws).area() > 1e-7 else (mid, hi)
    report(v < 1e-4 and on > 0.05 and v_shut < 1e-4 and min(tip_e, tip_l) >= 0.05 and lo >= 0.03,
           f"corner angle, {where}, as printed: pushed {-du:.3f} and {-dv:.3f} mm in onto both printed recess floors it "
           f"touches neither wall ({max(v, 0):.4f} mm3 over 30 mm), nor with the mitre closed ({max(v_shut, 0):.4f}); "
           f"{tip_l:.3f} mm left past the side-face leg and {tip_e:.3f} past the back-face leg, and the fillet's steps "
           f"{lo:.3f} mm off the chamfer's")
for name, part in angle_flat:
    bb = part.bounding_box()
    worst, _ = worst_overhang(part)
    loose = floating(part)
    foot = part.slice(0.125).area()
    report(worst < 0.01 and loose < 0.02 and abs(bb[5] - s.ANGLE_UP) < 1e-6 and abs(printed_top(bb[5]) - bb[5]) < 1e-6
           and foot > 0.9 * (bb[3] - bb[0]) * (s.ANGLE_REACH + s.ANGLE_P),
           f"corner angle, {name}: prints lying on its long leg ({foot:.0f} mm2 on the bed), its other leg standing "
           f"{bb[5]:.2f} mm (18 layers, on a layer line), nothing steeper than 45 degrees and nothing in mid-air "
           f"({worst:.3f} and {loose:.3f} mm2 worst layer)")
a1_, a2_ = s.corner_angle(1, 1), s.corner_angle(-1, 1)
v = abs((a1_ ^ a2_.mirror([1, 0, 0])).volume() - a1_.volume())
report(v < 1e-3 and overlap(a1_, a2_.translate([s.W, 0, 0]).mirror([0, 0, 1]).translate([0, 0, 0])) >= 0,
       f"the two corner angles are mirror images ({v:.4f} mm3 apart mirrored), one of each hand")
for n in SIDES + ["back wall"]:
    axis, sign = s.WALL_SIDE[n]
    floors, faces, thin, longest = [], [], 0.0, 0.0
    for sx, sy in s.CORNERS:
        if axis == 0 and sx != sign:
            continue
        piece = s.at_corner(p[n], sx, sy)

        def probe(a0, a1):
            return s.cbox(-3, 2, a0, a1, 30, 31) if axis == 0 else s.cbox(a0, a1, -3, 2, 30, 31)
        if axis == 0:
            region = s.cbox(-2.2, 2, -9.5, 2, -2, s.ZWT)
            mat, out = s.WALL_TO_PRINT["right side"], s.W / 2
        else:
            region = s.cbox(-9.5, 2, -2.2, 2, -2, s.ZWT)
            mat, out = s.WALL_TO_PRINT["back wall"], s.L / 2
        floors.append((piece ^ probe(-2.9, -2.5)).bounding_box()[3 + axis] - out + s.WT)
        faces.append((piece ^ probe(-5.5, -5.0)).bounding_box()[3 + axis] - out + s.WT)
        R = np.column_stack([np.array(mat, dtype=float), [0, 0, -(out - s.WT)]])
        flat_c = (piece ^ region).transform(R)
        for z0, z1 in layers(s.WT):
            if (z0 + z1) / 2 < s.WT - 2.2:
                continue
            cs = flat_c.slice((z0 + z1) / 2)
            bits = cs - cs.offset(-0.21, RND).offset(0.21, RND)
            thin = max([thin] + [b.area() for b in bits.decompose()])
            longest = max([longest] + [math.hypot(b.bounds()[2] - b.bounds()[0], b.bounds()[3] - b.bounds()[1])
                                       for b in bits.offset(-0.01, RND).offset(0.01, RND).decompose() if b.area() > 1e-4])
    pf = {round(printed_top(h), 3) for h in floors}
    pw = {round(printed_top(h), 3) for h in faces}
    report(pf == {4.65} and pw == {5.05} and thin < 0.05 and longest < 0.6,
           f"{n}: as printed, each back corner recess's floor is on the {min(pf):.2f} layer line and the siding's face on "
           f"{min(pw):.2f}, 2 layers; near the corner nothing is thinner than a line (biggest bit {thin:.3f} mm2, longest "
           f"{longest:.2f} mm)")
# the front corners: glued butt joints hidden in a siding groove
for n in SIDES:
    sx = s.WALL_SIDE[n][1]
    w = p[n]
    gap = w.min_gap(F, 1.0)
    near = overlap(w.translate([0, -0.11, 0]), F)
    far = overlap(w.translate([0, -0.09, 0]), F)
    end = w ^ s.box(-s.W, s.W, s.YS - 0.01, s.YS + 0.05, -1, 200)
    eb = end.bounding_box()
    report(abs(gap - s.MITRE_GAP) < 1e-3 and near > 1 and far < 1e-6 and eb[2] < 1e-6 and eb[5] > s.ZWT - 0.16,
           f"{n}: its front end face is {gap:.3f} mm off the front wall's inside face, z {eb[2]:.2f} to {eb[5]:.2f} "
           f"(moved 0.11 toward it they meet, {near:.1f} mm3; 0.09, {far:.4f})")
    worst = sweep(w, F, [[0, 0, dz] for dz in DROPS])
    report(worst < 1e-6, f"{n} comes down past the front wall's end block without touching it ({worst:.5f} mm3)")
    ok, depth, widths = True, [], []
    zs_joint = (3.0, 30.0, 60.0, s.ZWT - 1.5)          # from the skirt to 1.5 under the wall top
    for z in zs_joint:
        cs = s.union([w, F]).slice(z)
        # the outermost point of each wall at the joint's two faces
        fw_ = (F.slice(z) ^ m3.CrossSection.square([6, 0.002]).translate([sx * s.W / 2 - (6 if sx > 0 else 0), s.YF + s.WT - 0.002]))
        sw_ = (w.slice(z) ^ m3.CrossSection.square([6, 0.002]).translate([sx * s.W / 2 - (6 if sx > 0 else 0), s.YS]))
        fo = sx * (fw_.bounds()[2] if sx > 0 else fw_.bounds()[0])
        so = sx * (sw_.bounds()[2] if sx > 0 else sw_.bounds()[0])
        depth.append(s.W / 2 - max(fo, so))
        face = cs ^ m3.CrossSection.square([0.02, 3]).translate([sx * s.W / 2 - (0.02 if sx > 0 else 0), s.YF + s.WT - 1.5])
        ys_ = sorted((b.bounds()[1], b.bounds()[3]) for b in face.decompose())
        widths.append(ys_[1][0] - ys_[0][1] if len(ys_) == 2 else -1)
    report(min(depth) >= 0.3 and all(abs(d - depth[0]) < 1e-3 for d in depth) and all(0.6 < x < 0.8 for x in widths),
           f"{n}: the front joint is in the bottom of a groove its full height, {min(depth):.2f} mm in from the side face "
           f"at z {', '.join(f'{z_:.0f}' for z_ in zs_joint[:-1])} and {zs_joint[-1]:.1f}, the groove {min(widths):.2f} to "
           f"{max(widths):.2f} mm wide at the face")
    # (up to 2.5 under the wall top, under the loft notch and the eave's cut)
    reg_s = s.box(*sorted([sx * (s.W / 2 - s.WT - 0.5), sx * (s.W / 2 + 1)]), s.YS - 0.1, -43.86, -1, s.ZWT - 2.5)
    reg_f = s.box(*sorted([sx * (s.W / 2 - s.WT), sx * (s.W / 2 + 1)]), s.YF - 1, s.YF + s.WT + 0.1, -1, s.ZWT - 2.5)
    o1 = worst_overhang(print_part(w, s.WALL_TO_PRINT[n], reg_s))[0]
    o2 = worst_overhang(print_part(F, s.WALL_TO_PRINT["front wall"], reg_f))[0]
    report(max(o1, o2) < 0.05, f"{n}: the groove's notch on the side wall and the chamfer on the front wall's end block "
                               f"print with nothing over 45 degrees ({o1:.3f} and {o2:.3f} mm2 worst layer)")

# ================================================================ 5
group("5. gables and vents")
vz0 = s.ZPK - 0.92 * s.FT - 0.76 * s.FT / 2
vz1 = vz0 + 0.76 * s.FT
for name, piece, sy, mat in (("back wall", B, 1, s.WALL_TO_PRINT["back wall"]), ("porch gable", gable, -1, s.GABLE_TO_PRINT)):
    yf = sy * s.L / 2
    # the recess floor, probed in the gap over the bottom slat (the slats are a fifth of the field,
    # inside the 1.0 frame, apart; the bottom one stands on the frame, its back 0.45 under the next)
    pitch = (0.76 * s.FT - 2.0) / 5
    probe = s.box(-2, 2, *sorted([yf - sy * 3, yf + sy * 3]), vz0 + 1.0 + pitch - 0.35, vz0 + 1.0 + pitch - 0.05)
    vfloor = s.WT - abs((piece ^ probe).bounding_box()[4 if sy > 0 else 1] - yf) if not (piece ^ probe).is_empty() else -1
    pr2 = s.box(-6, 6, *sorted([yf - sy * 3, yf + sy * 3]), vz0 + 1.3, vz1 - 1.3)
    front = (piece ^ pr2).bounding_box()
    vfront = s.WT - abs((front[4] if sy > 0 else front[1]) - yf)
    bridge = min(z0 for z0, z1 in layers(s.WT) if (z0 + z1) / 2 > s.SD)
    under = round((vfloor - bridge) / 0.2, 6)
    past = overlap(piece, s.box(-5.93, 5.93, *sorted([yf + sy * 0.001, yf + sy * 3]), vz0 - 0.6, vz1 + 0.6))
    # as printed: the louvre field, layer by layer, across the slats at three places along them. The
    # probe takes in 0.5 of the frame above and below the field (wide enough to print, so as_printed
    # keeps it), so the gap between the frame and the end slats is measured too, not only the gaps
    # between slats (audit Nov 3 2026: the barn's slats stood 0.25 off the frame, leaving end slots
    # 0.2 to 0.4 wide that the old probe, stopping at the field's edge, never saw)
    fz0, fz1 = vz0 + 1.0, vz1 - 1.0            # the louvre field
    rz0, rz1 = fz0 - 0.5, fz1 + 0.5            # the probe: 0.5 of frame each side of it
    region = s.box(-5.0, 5.0, *sorted([yf - sy * 3, yf + sy * 1]), rz0, rz1)
    part = printed_in_shed(piece, mat, region)
    widths, gaps, counts, top_gaps, ends = [], [], set(), [], True
    for z0, z1 in layers(s.WT):
        zm = (z0 + z1) / 2
        if zm < vfloor or z1 > printed_top(s.WT) + 1e-6:
            continue
        u_ = zm
        yy = yf - sy * (s.WT - u_)
        sec = (part ^ s.box(-5.0, 5.0, yy - 0.001, yy + 0.001, rz0, rz1))
        for xp in (-3.0, 0.0, 3.0):
            strip = sec ^ s.box(xp - 0.01, xp + 0.01, -s.L, s.L, -1, 200)
            ivs = sorted((b.bounding_box()[2], b.bounding_box()[5]) for b in strip.decompose() if b.volume() > 1e-12)
            # the frame is there below and above the field on every layer
            ends = ends and len(ivs) >= 2 and abs(ivs[0][0] - rz0) < 1e-3 and abs(ivs[-1][1] - rz1) < 1e-3
            # every gap, frame to slat and slat to frame included
            gaps += [ivs[k + 1][0] - ivs[k][1] for k in range(len(ivs) - 1)]
            if ivs:
                top_gaps.append(ivs[-1][0] - ivs[-2][1] if len(ivs) >= 2 else -1)
            # the slats: what stands in the field (the bottom one stands on the frame, so it is clipped off it)
            sl = [(max(a, fz0), min(b, fz1)) for a, b in ivs]
            sl = [(a, b) for a, b in sl if b - a > 1e-6]
            counts.add(len(sl))
            widths += [b - a for a, b in sl]
    report(abs(printed_top(vfloor + 1e-9) - vfloor) < 1e-6 and abs(vfloor - 4.25) < 1e-6 and under >= 3 and
           abs(vfront - s.WT) < 1e-6 and past < 1e-9,
           f"{name}'s vent: its louvres sit in a recess {s.WT - vfloor:.3f} mm into the siding, the floor on the {vfloor:.2f} "
           f"layer line over {under:.0f} layers of siding (from {bridge:.2f}); the slats and frame come up to the siding face "
           f"({vfront:.2f}) and nothing stands past it ({past:.5f} mm3)")
    widths, gaps, top_gaps = widths or [-1.0], gaps or [-1.0], top_gaps or [-1.0]
    report(ends and counts == {s.VENT_SLATS} and min(widths) >= 0.42 and min(gaps) >= 0.42,
           f"{name}'s vent as printed: {sorted(counts)} slats on every recess layer, the bottom one standing on the frame, "
           f"each slat {min(widths):.3f} to {max(widths):.3f} mm wide; every gap, the one under the top of the frame "
           f"({min(top_gaps):.3f} to {max(top_gaps):.3f}) included, {min(gaps):.3f} to {max(gaps):.3f} mm (a line is 0.42)")
# the faux loft window on the porch gable (STD: fake F 0, 2.6 x 1.9 ft, frame 0.3 ft, corner triangles
# 0.4875 ft, centre 1.57 ft over the wall top by the designer's gableRect rule), in place of the octagon
fx_, fh_ = STD["faux w"] * s.FT / 2, STD["faux h"] * s.FT / 2
fbar, ftri = STD["faux bar"] * s.FT, STD["faux tri"] * s.FT
fzc = s.ZWT + STD["faux over wall top"] * s.FT
faux_t = (gable ^ zone) ^ s.box(-fx_ - 1, fx_ + 1, -s.L / 2 - 2, -s.L / 2 + 1, fzc - fh_ - 1, fzc + fh_ + 1)
fb = faux_t.bounding_box()
f_vol = faux_area * s.PROUD
left_bar = (faux_t ^ s.box(-fx_ - 1, 0, -s.L, s.L, fzc - 0.01, fzc + 0.01)).bounding_box()
bottom_bar = (faux_t ^ s.box(-0.01, 0.01, -s.L, s.L, fzc - fh_ - 1, fzc)).bounding_box()
in_x, in_z = fx_ - fbar - ftri - 0.01, fh_ - fbar - 0.01
inner_trim = overlap(faux_t, s.box(-in_x, in_x, -s.L, s.L, fzc - in_z, fzc + in_z))
siding_box = s.box(-fx_ + 0.01, fx_ - 0.01, -s.L / 2 + s.GROOVE_D + 0.01, -s.L / 2 + s.TS - 0.01, fzc - fh_ + 0.01, fzc + fh_ - 0.01)
siding_whole = overlap(gable, siding_box) / siding_box.volume()
# its shape, drawn here from STD alone: the four bars, and in each inside corner a right triangle with
# its legs ftri along the two bars and its long side toward the middle, all in the 0.6 proud
ya_, yb_ = -s.L / 2 - s.PROUD, -s.L / 2
fz0, fz1 = fzc - fh_, fzc + fh_
ref_faux = s.union([s.box(-fx_, fx_, ya_, yb_, fz0, fz0 + fbar), s.box(-fx_, fx_, ya_, yb_, fz1 - fbar, fz1),
                    s.box(-fx_, -fx_ + fbar, ya_, yb_, fz0, fz1), s.box(fx_ - fbar, fx_, ya_, yb_, fz0, fz1)] +
                   [s.prism_xz([(cx_, cz_), (cx_ + sx_ * ftri, cz_), (cx_, cz_ + sz_ * ftri)], ya_, yb_)
                    for cx_, sx_ in ((-fx_ + fbar, 1), (fx_ - fbar, -1)) for cz_, sz_ in ((fz0 + fbar, 1), (fz1 - fbar, -1))])
faux_diff = faux_t.volume() + ref_faux.volume() - 2 * overlap(faux_t, ref_faux)
report(abs(fb[0] + fx_) < 0.01 and abs(fb[3] - fx_) < 0.01 and abs(fb[2] - (fzc - fh_)) < 0.01 and abs(fb[5] - (fzc + fh_)) < 0.01
       and abs(fb[1] - (-s.L / 2 - s.PROUD)) < 1e-6 and abs(fb[4] + s.L / 2) < 1e-6 and len(faux_t.decompose()) == 1
       and abs(faux_t.volume() / f_vol - 1) < 0.01 and abs(left_bar[3] - (-fx_ + fbar)) < 0.01
       and abs(bottom_bar[5] - (fzc - fh_ + fbar)) < 0.01 and inner_trim < 1e-6 and abs(siding_whole - 1) < 1e-6
       and faux_diff < 0.01,
       f"porch gable's faux loft window, centred: its trim x {fb[0]:.3f} to {fb[3]:.3f}, z {fb[2]:.3f} to {fb[5]:.3f} "
       f"({(fb[3] - fb[0]) / s.FT:.2f} x {(fb[5] - fb[2]) / s.FT:.2f} ft, centre {((fb[2] + fb[5]) / 2 - s.ZWT) / s.FT:.2f} ft over "
       f"the wall top), one piece of {faux_t.volume():.1f} mm3 against {f_vol:.1f} for the frame and four corner triangles, "
       f"the same shape as the four bars and four inside-corner right triangles drawn from STD ({faux_diff:.4f} mm3 "
       f"different), "
       f"bars {left_bar[3] + fx_:.3f} wide at the side and {bottom_bar[5] - fb[2]:.3f} at the bottom, all of it in the 0.6 "
       f"proud of the siding; inside it no trim ({inner_trim:.5f} mm3) and the siding whole, no opening "
       f"({siding_whole * 100:.2f}% solid)")
# round the faux window, as the porch gable lies on the bed (outside up), the siding's grooved top has no
# slot or strip narrower than a 0.42 line: a bar edge on a groove's middle line left half the groove
# showing beside it, 0.25 wide (review Nov 3 2026). Looked for by closing each section by half a line:
# what that fills is narrower than a line. Only the round fillets in square inside corners are allowed
faux_region = s.box(-fx_ - 1, fx_ + 1, -s.L, s.L, fz0 - 1, fz1 + 1)
faux_print = print_part(gable, s.GABLE_TO_PRINT, faux_region)
slot_worst, slot_where = 0.0, ""
for d_ in (0.05, 0.1, 0.2, 0.25, 0.3):
    z_ = s.WT - s.GROOVE_D + d_
    cs_ = faux_print.slice(z_)
    for g_ in (cs_.offset(0.21, RND).offset(-0.21, RND) - cs_).decompose():
        if g_.area() > slot_worst:
            gb_ = g_.bounds()
            slot_worst, slot_where = g_.area(), f"at print Z {z_:.2f}, X {gb_[0]:.2f} to {gb_[2]:.2f}"
report(slot_worst < 0.05,
       f"porch gable round the faux loft window, as printed: no slot or strip narrower than a line in the siding's grooves "
       f"(print Z {s.WT - s.GROOVE_D + 0.05:.2f} to {s.WT - s.GROOVE_D + 0.3:.2f}; largest bit a line can't reach "
       f"{slot_worst:.3f} mm2 {slot_where}, {'an inside-corner fillet' if slot_worst < 0.05 else 'a slot'}); the groove "
       f"halves beside the side bars are filled "
       f"({len(getattr(s, 'faux_groove_fills', list)())} strips)")
gpz = s.gable_parts(-1)
gpb_ = s.gable_parts(1)
col = gpz["collar"]
col_reach = min(overlap(col, gpz["chords"] ^ s.box(*sorted([sx_ * 30, sx_ * s.W]), -s.L, s.L, 0, 200)) for sx_ in (1, -1))
cb, kp = col.bounding_box(), gpz["king post"].bounding_box()
studs_ = sorted(round((q.bounding_box()[0] + q.bounding_box()[3]) / 2 / s.S, 2) for q in gpz["gable studs"].decompose())
sb_ = gpz["gable studs"].bounding_box()
foot_print = s.box(-fx_, fx_, -s.L, s.L, fzc - fh_, fzc + fh_)
framed = sum(overlap(v_, foot_print) for k_, v_ in gpz.items() if k_ != "gable studs")
behind = overlap(gpz["gable studs"], foot_print)
want_behind = 2 * s.GABLE_STUD_W * 2 * fh_ * s.SD
# the heights worked out by hand from the wall top, 69.924 on Alan's 79 1/2 in wall (Nov 4 2026; 2.619 under the
# 82.8 in wall's 72.543): the collar tie 95.422 to 98.200 (its top the end truss's inside corner at the knee), the
# back wall's band 87.069 to 89.847 (0.40 of the way from the wall top to the peak, 3 1/2 in high), its backing
# 78.655 to 81.433 (11 in over the plate, 3 1/2 in high)
COLLAR_Z, BAND_ZS, BACKING_ZS = (95.422, 98.200), (87.069, 89.847), (78.655, 81.433)
report(set(gpz) == set(gpb_) - {"backing"} and col_reach > 0.1 and abs(cb[2] - COLLAR_Z[0]) < 0.01 and abs(cb[5] - COLLAR_Z[1]) < 0.01
       and abs(kp[2] - cb[5]) < 1e-6 and studs_ == [-36.0, -12.0, 12.0, 36.0] and abs(sb_[5] - cb[2]) < 1e-6
       and abs(sb_[2] - (s.ZWT + s.GABLE_BOARD)) < 1e-6 and framed < 1e-6 and abs(behind - want_behind) < 0.01,
       f"porch gable's framing, from its parts: the back wall's without the backing ({', '.join(sorted(gpz))}), the "
       f"collar full width into both lower chords, {cb[2]:.3f} to {cb[5]:.3f}, the king post on it, gable studs at "
       f"{', '.join(f'{x_:+.0f}' for x_ in studs_)} in from the gable board to the collar; nothing framed for the faux "
       f"window ({framed:.5f} mm3 of board, collar, chords or king post behind it), only the two 12 in gable studs pass "
       f"behind it ({behind:.1f} mm3 of {want_behind:.1f}); no octagon box")
gpb = gpb_
b_trim = (B ^ zone)
bnd = (b_trim ^ s.box(-25, 25, -s.L, s.L, 82, 97)).bounding_box()
bk = gpb["backing"].bounding_box()
cl = gpb["collar"]
full = min(overlap(cl, gpb["chords"] ^ s.box(*sorted([sx_ * 30, sx_ * s.W]), -s.L, s.L, 0, 200)) for sx_ in (1, -1))
report(abs(bnd[2] - BAND_ZS[0]) < 0.01 and abs(bnd[5] - BAND_ZS[1]) < 0.01 and abs(bk[2] - BACKING_ZS[0]) < 0.01 and
       abs(bk[5] - BACKING_ZS[1]) < 0.01 and full > 0.1 and abs(cl.bounding_box()[2] - COLLAR_Z[0]) < 0.01,
       f"back wall: gable band z {bnd[2]:.3f} to {bnd[5]:.3f}, backing {bk[2]:.3f} to {bk[5]:.3f}, the collar full width "
       f"into both lower chords, {cl.bounding_box()[2]:.3f} to {cl.bounding_box()[5]:.3f}")

# ================================================================ 6
group("6a. the porch")
walls_all = s.union([p[n] for n in WALLS])
for i, (post, (x0, x1, y0, y1)) in enumerate(zip(posts, s.post_tenons())):
    bot = post ^ s.box(-s.W, s.W, -s.L, s.L, -1, s.ZF)
    topt = post ^ s.box(-s.W, s.W, -s.L, s.L, s.FRAME_Z, 200)
    side = {}
    for nm, ten, other in (("deck", bot, fl), ("frame", topt, frame)):
        free = max(overlap(ten.translate(t), other) for t in ([0.34, 0, 0], [-0.34, 0, 0], [0, 0.34, 0], [0, -0.34, 0]))
        hit = min(overlap(ten.translate(t), other) for t in ([0.36, 0, 0], [-0.36, 0, 0], [0, 0.36, 0], [0, -0.36, 0]))
        side[nm] = (free < 1e-6 and hit > 1e-5 and overlap(ten, other) < 1e-6)
    # as printed: the post lying on its tenon face, the floor upside down, the frame bottom down
    cols, o = s.post_to_cabin(i)
    pa = s.place(as_printed(s.porch_post()), cols, o)
    reg_d = s.box(x0 - 2, x1 + 2, y0 - 2, y1 + 2, s.ZF - 2, s.ZF + 0.5)
    reg_f = s.box(x0 - 2, x1 + 2, y0 - 2, y1 + 2, s.FRAME_Z - 0.5, s.FRAME_Z + 2)
    pd = printed_in_shed(fl, s.FLOOR_TO_PRINT, reg_d)
    pfr = printed_in_shed(frame, [[1, 0, 0], [0, 1, 0], [0, 0, 1]], reg_f)
    g_d = (pa ^ reg_d).min_gap(pd, 1.0)
    g_f = (pa ^ reg_f).min_gap(pfr, 1.0)
    side_gap_d = plan_gap(pa ^ reg_d, pd, s.ZF - 0.5)
    side_gap_f = plan_gap(pa ^ reg_f, pfr, s.FRAME_Z + 0.5)
    report(side["deck"] and side["frame"] and min(side_gap_d, side_gap_f) >= 0.25,
           f"porch post {i + 1} (x {s.POST_XS[i]:+.3f}): each tenon in its deck socket and its frame socket, 0.35 round as "
           f"drawn (free moved 0.34, touching 0.36), {side_gap_d:.3f} and {side_gap_f:.3f} round as both printed")
# each post's foot bears on the deck and the frame on each post's top, every one of them, not only somewhere (the
# 0.1 mm drops this was, against all the posts at once, would pass a frame standing 0.1 off one post or more):
# lowered REST each post meets the deck by REST_MM2 of bearing or more, and the frame each post
post_feet = [s.box(*(lambda b_: (b_[0] - 0.5, b_[3] + 0.5, b_[1] - 0.5, b_[4] + 0.5))(pst.bounding_box()), s.ZF - 1, s.ZF + 1)
             for pst in posts]
post_tops = [s.box(*(lambda b_: (b_[0] - 0.5, b_[3] + 0.5, b_[1] - 0.5, b_[4] + 0.5))(pst.bounding_box()),
                   s.FRAME_Z - 1, s.FRAME_Z + 1) for pst in posts]
on_deck = [rest_vols(pst, fl, [w_])[0] for pst, w_ in zip(posts, post_feet)]
on_posts = rest_vols(frame, posts_all, post_tops)
v_up = overlap(frame.translate([0, 0, 0.1]), posts_all)
report(min(on_deck) >= REST * REST_MM2 and min(on_posts) >= REST * REST_MM2 and v_up < 1e-6 and len(on_posts) == 3,
       f"the posts' end faces bear on the deck, each of the {len(posts)} (lowered {REST} mm each meets it by "
       f"{min(on_deck):.3f} mm3 or more), and the frame bears on every post's top (lowered {REST} it meets each by "
       f"{min(on_posts):.3f} or more, {REST * REST_MM2:.2f} needed; raised 0.1 it is free, {v_up:.4f})")
# every socket and hole at least 0.6 from an edge, a cavity or another hole: the part round it is solid
worst_s = 0.0
for part, socks in ((fl, s.post_sockets(s.ZF, False) + s.railing_holes()),          # the real floor, deck grooves and all
                    (frame, s.post_sockets(s.FRAME_Z, True) + s.gable_peg_sockets())):
    pb = part.bounding_box()
    for sock in socks:
        sb = (sock ^ s.box(pb[0], pb[3], pb[1], pb[4], pb[2], pb[5])).bounding_box()
        R_ = s.box(sb[0] - 0.6, sb[3] + 0.6, sb[1] - 0.6, sb[4] + 0.6, max(sb[2] - 0.6, pb[2]), min(sb[5] + 0.6, pb[5]))
        missing = R_.volume() - (R_ ^ part).volume() - (R_ ^ sock).volume()
        worst_s = max(worst_s, missing)
# and as it prints, face down: round each of them the first layer (the deck-board grooves' depth) has
# nothing thinner than a line, which the slicer would drop
R_fl = np.column_stack([np.array(s.FLOOR_TO_PRINT, dtype=float), np.zeros(3)])
hb = fl.transform(R_fl).bounding_box()
near_holes = s.union([h.transform(R_fl) for h in s.post_sockets(s.ZF, False) + s.railing_holes()]).translate(
    [-hb[0], -hb[1], -hb[2]]).slice(0.125).offset(0.7, RND)
c1 = pp["floor"].slice(0.125)
lost_first = ((c1 - c1.offset(-0.21, RND).offset(0.21, RND)) ^ near_holes).area()
report(worst_s < 1e-3 and lost_first < 0.05,
       f"every post socket, railing peg hole and gable peg socket has solid floor or frame for 0.6 mm all round it, no "
       f"edge, cavity, deck-board groove or other hole nearer ({worst_s:.4f} mm3 missing); round the deck's sockets and "
       f"holes the floor's first layer prints whole ({lost_first:.3f} mm2 under a line wide)")
# the porch frame
xi = s.W / 2 - s.WT
side_beams = frame ^ (s.box(xi - 0.01, s.W, -s.L, s.L, 0, 200) + s.box(-s.W, -xi + 0.01, -s.L, s.L, 0, 200))
g_sb = side_beams.min_gap(F, 1.0)
rear = frame ^ s.box(-xi + 0.5, xi - 0.5, s.YF - 3, s.YF, 0, 200)
cas = F ^ zone
g_rear = rear.min_gap(F ^ s.box(-s.W, s.W, -s.L, s.L, s.FRAME_Z - 3, 200), 2.0)
dy_rear = s.YF - s.PROUD - rear.bounding_box()[4]
# since the standard layout no casing reaches under the side beams (the window's outer board ends at
# x -37.26, the door's at +33.64): how far in from the side beams the casings stop. The window's casing is under
# the frame's bottom. The door's head casing is not since Alan's answers (Nov 4 2026): over his 73 1/2 in door its
# top is at 77 in, on his 79 1/2 in wall the frame's bottom at 75.9 in, so its top stands behind the rear beam, 0.2
# clear of it (g_rear), the beam in front of it from end to end and from under its top to over it (it was 0.087
# under the frame on the 82.8 in wall; open question 16 in the read me)
cbb = cas.bounding_box()
side_clear = xi - max(abs(cbb[0]), abs(cbb[3]))
cas_pcs = sorted((q.bounding_box() for q in cas.decompose()), key=lambda b_: b_[0])
win_top_c, door_cb = cas_pcs[0][5], cas_pcs[-1]                       # the window's casing (left), the door's (right)
under_fr = s.FRAME_Z - win_top_c
door_over = door_cb[5] - s.FRAME_Z
# the rear beam itself in front of the casing's top, all along it: solid frame from the frame's bottom to over the
# casing's top, over the casing's whole length, through the beam's depth (its lip and its bounding box are not
# enough: cut short at x 20 the beam's lip still ran on past the casing)
yrb_ = s.YF - s.PROUD - s.FIT
in_front = s.box(door_cb[0], door_cb[3], yrb_ - s.REAR_D + 0.01, yrb_ - 0.01, s.FRAME_Z + 0.01, door_cb[5] + 0.1)
front_solid = overlap(frame, in_front) / in_front.volume()
door_hidden = (len(cas_pcs) == 2 and door_cb[0] < s.DOOR_X0 < door_cb[3] and abs(front_solid - 1) < 1e-6
               and s.FRAME_Z < door_cb[5] < s.ZWT - 0.5)
g_roof = frame.min_gap(roof_all, 1.0)
mid = frame ^ s.box(43.5, 44.5, -80, -70, 0, 200)
g_walls = frame.min_gap(walls_all, 1.0)
report(abs(g_sb - s.FIT) < 1e-3 and abs(dy_rear - 0.2) < 1e-3 and g_rear > 0.2 - 1e-3 and side_clear >= 0.2 and under_fr > 0 and
       door_hidden and g_roof >= s.ROOF_CLR - 0.002 and abs(mid.bounding_box()[5] - mid.bounding_box()[2] - s.FRAME_H) < 1e-6 and
       abs(frame.bounding_box()[5] - frame.bounding_box()[2] - s.FRAME_H) < 1e-6 and g_walls >= 0.2 - 1e-3,
       f"porch frame: its side beams' ends {g_sb:.3f} mm off the front wall's face (glued), the rear beam {dy_rear:.3f} in "
       f"front of the casings' faces ({g_rear:.3f} at the closest); the casings stop {side_clear:.3f} mm in from the side "
       f"beams (x {cbb[0]:.3f} to {cbb[3]:.3f}); the window's casing's top {under_fr:.3f} under the frame, the door's head "
       f"casing's {door_over:.3f} over the frame's bottom ({door_over / s.S:.1f} in), behind the rear beam, which is solid "
       f"in front of it all along, x {door_cb[0]:.2f} to {door_cb[3]:.2f}, up to over its top ({front_solid * 100:.2f}%); "
       f"{g_roof:.3f} under the lower sheets, the full {s.FRAME_H} tall but at the bevel, {g_walls:.3f} from every wall")
fp = pp["porch frame"]
worst, longest = worst_overhang(fp)
lip = fp ^ s.box(s.W / 2 + (xi - s.LIP_W) + 0.1, s.W / 2 + xi - 0.1, 10, 20, -1, 10)
lb = lip.bounding_box()
report(worst < 0.01 and abs(fp.bounding_box()[5] - 2.85) < 1e-6 and abs(lb[5] - s.LIP_H) < 1e-6,
       f"porch frame prints bottom down: {fp.bounding_box()[5]:.2f} tall, the lip {lb[5]:.2f}, nothing hanging over "
       f"({worst:.3f} mm2 worst layer, the sockets' roofs bridges up to {longest:.1f} mm)")
standing = s.union([fl, walls_all, rails_all, posts_all, door_shut])
worst = sweep(frame, standing, [[0, 0, dz] for dz in np.arange(0.0, 80.01, 0.5)])
report(worst < 1e-3, f"porch frame lowered from 80 mm onto the {len(posts)} posts standing in their sockets, with the railings and "
                     f"walls on, touches nothing until the sockets take the tenons ({worst:.4f} mm3)")
# the ceiling rests on the lip all round and the porch gable on the frame's front beam all along, not only somewhere
# (these were 0.1 mm drops, against the whole frame): lowered REST, the ceiling meets the lip in every 2 mm along each
# of its four edges (its edge laps the lip LIP_W - FIT, 1.0 wide, so 2 mm of it is 2 mm2 of bearing, 1 needed), and
# the gable meets the beam in every 1 mm across it, from 1 mm in from each end (past that the frame's top is cut under
# the steep roof sheets)
cb_ = ceiling.bounding_box()
ce_wins, ce_where = [], []
for x_ in np.arange(cb_[0], cb_[3] - 1.0, 2.0):
    for y_, nm_ in ((cb_[1], "front"), (cb_[4] - 3, "back")):
        ce_wins.append(s.box(x_, x_ + 2, y_, y_ + 3, s.FRAME_Z - 1, s.FRAME_Z + 3))
        ce_where.append(f"{nm_} edge x {x_ + 1:+.1f}")
for y_ in np.arange(cb_[1] + 3, cb_[4] - 4.0, 2.0):
    for x_, nm_ in ((cb_[0], "left"), (cb_[3] - 3, "right")):
        ce_wins.append(s.box(x_, x_ + 3, y_, y_ + 2, s.FRAME_Z - 1, s.FRAME_Z + 3))
        ce_where.append(f"{nm_} edge y {y_ + 1:.1f}")
ce_least, ce_at = least_rest(rest_vols(ceiling, frame, ce_wins), ce_where)
gaps = ceiling.min_gap(frame ^ s.box(-s.W, s.W, -s.L, s.L, s.FRAME_Z + s.LIP_H + 0.01, 200), 1.0)
worst = sweep(ceiling, s.union([frame, gable, walls_all, loft_set]), [[0, 0, dz] for dz in np.arange(0.0, 60.01, 0.5)])
report(ce_least >= REST * REST_MM2 and len(ce_wins) > 100 and abs(gaps - s.FIT) < 1e-3 and worst < 1e-3,
       f"porch ceiling rests on the lip all round: lowered {REST} mm it meets it in each of {len(ce_wins)} 2 mm stretches "
       f"along its four edges, by {ce_least:.3f} mm3 or more ({ce_at}; {REST * REST_MM2:.2f} needed); it is "
       f"{gaps:.3f} mm off the four beams, and lifts straight out past the porch gable ({worst:.4f} mm3)")
g_wins = [s.box(x_, x_ + 1, -s.L / 2 - 1, -s.L / 2 + s.WT + 1, s.ZWT - 1, s.ZWT + 1)
          for x_ in np.arange(-s.W / 2 + 1, s.W / 2 - 1.5, 1.0)]
g_least, g_at = least_rest(rest_vols(gable, frame, g_wins), [x_ + 0.5 for x_ in np.arange(-s.W / 2 + 1, s.W / 2 - 1.5, 1.0)])
v = g_least
pegs = gable ^ s.box(-s.W, s.W, -s.L, s.L, 0, s.ZWT - 0.001)
free = max(overlap(pegs.translate(t), frame) for t in ([0.34, 0, 0], [-0.34, 0, 0], [0, 0.34, 0], [0, -0.34, 0]))
hit = min(overlap(pegs.translate(t), frame) for t in ([0.36, 0, 0], [-0.36, 0, 0], [0, 0.36, 0], [0, -0.36, 0]))
reg = s.union([s.box(sx_ * s.GABLE_PEG_X - 3, sx_ * s.GABLE_PEG_X + 3, -s.L / 2 - 1, -s.L / 2 + s.WT + 2, s.ZWT - 2.5, s.ZWT + 0.5)
               for sx_ in (1, -1)])
pg_p = printed_in_shed(gable, s.GABLE_TO_PRINT, reg) ^ s.box(-s.W, s.W, -s.L, s.L, 0, s.ZWT - 0.05)
pf_p = printed_in_shed(frame, [[1, 0, 0], [0, 1, 0], [0, 0, 1]], reg)
g_pr = plan_gap(pg_p, pf_p, s.ZWT - 0.75)
sface = (gable ^ s.box(15, 30, -s.L, s.L, 80, 100)).bounding_box()[1]
pegs_b = [q.bounding_box() for q in s.union(s.roof_pegs(1)).decompose()]
pegs_f = [q.bounding_box() for q in s.union(s.roof_pegs(-1)).decompose()]
same = max(min(abs(a[5] - b[5]) + abs(abs(a[1] + a[4]) / 2 - abs(b[1] + b[4]) / 2) + abs(a[0] - b[0]) for b in pegs_f)
           for a in pegs_b)
report(v >= REST * REST_MM2 and len(g_wins) > 80 and free < 1e-6 and hit > 1e-5 and g_pr >= 0.25 and abs(sface + s.L / 2) < 1e-6
       and same < 0.01,
       f"porch gable rests on the frame all along: lowered {REST} mm it meets the front beam's top in each of the "
       f"{len(g_wins)} mm across it, by {v:.3f} mm3 or more (at x {g_at:+.1f}; {REST * REST_MM2:.2f} needed); its two pegs "
       f"in their sockets 0.35 round (free moved "
       f"0.34, touching 0.36), {g_pr:.3f} as printed; its siding face at y {sface:.3f}; its roof pegs at the same height "
       f"and distance from the middle as the back wall's ({same:.4f})")
fl_rail = s.union([fl, walls_all])
for k, (rail, (kind, cols, o)) in enumerate(zip(rails, s.railing_places())):
    peg = rail ^ s.box(-s.W, s.W, -s.L, s.L, -1, s.ZF)
    free = max(overlap(peg.translate(t), fl) for t in ([0.34, 0, 0], [-0.34, 0, 0], [0, 0.34, 0], [0, -0.34, 0]))
    hit = min(overlap(peg.translate(t), fl) for t in ([0.36, 0, 0], [-0.36, 0, 0], [0, 0.36, 0], [0, -0.36, 0]))
    n_, length_ = (s.SIDE_RAIL_N, s.SIDE_RAIL_LEN) if kind == "side" else (s.FRONT_RAIL_N, s.FRONT_RAIL_LEN)
    xm = (length_ - (n_ - 1) * s.BAL_OC) / 2 + s.BAL_OC / 2       # between the first two balusters
    pt = np.array(o, dtype=float) + xm * np.array(cols[0], dtype=float)
    br = (rail ^ s.box(pt[0] - 0.3, pt[0] + 0.3, pt[1] - 0.3, pt[1] + 0.3, -1, 200)).bounding_box()[2] - s.ZF
    g_post = rail.min_gap(posts_all, 1.0)
    g_F = s.YF - rail.bounding_box()[4]
    worst = sweep(rail, fl_rail, [[0, 0, dz] for dz in np.arange(80.0, -0.01, -0.5)])
    # pressed home it stands on its pegs, which bottom in their holes 0.05 under where it is drawn (the pegs
    # are 0.05 shorter than the holes are deep): lowered 0.04 it is free, 0.06 it meets them, at the pegs only
    seat_free = overlap(rail.translate([0, 0, -0.04]), fl)
    seat_hit = overlap(rail.translate([0, 0, -0.06]), fl)
    on_pegs = overlap(rail.translate([0, 0, -0.06]), fl) - overlap(peg.translate([0, 0, -0.06]), fl)
    report(free < 1e-6 and hit > 1e-5 and abs(br - s.RAIL_B0) < 0.01 and abs(g_post - s.RAIL_POST_GAP) < 1e-3 and
           (kind == "front" or abs(g_F - 0.25 * s.FT) < 0.01) and worst < 1e-3 and seat_free < 1e-6 and
           seat_hit > 1e-4 and abs(on_pegs) < 1e-6,
           f"{kind} railing {k + 1}: its pegs in their holes 0.35 round, the bottom rail {br:.3f} over the deck, its ends "
           f"{g_post:.3f} off the posts{'' if kind == 'front' else f' and {g_F:.3f} off the front wall face'}; lowered "
           f"from 80 mm onto the bare porch it touches nothing, its pegs going down into their holes ({worst:.4f} mm3); "
           f"drawn, its pegs' ends stand {s.SOCKET_D - s.RAIL_PEG:.2f} over the holes' floor, so pressed home it stands on its "
           f"pegs that much under its drawn height, nothing else touching (lowered 0.04: {seat_free:.4f}, 0.06: "
           f"{seat_hit:.4f} mm3, all of it at the pegs)")
# the porch's front, Alan's standard (STD): a corner post each side and ONE middle post 0.3 ft left of
# centre; ONE front railing, from the left corner post to the middle post, under the window; the right
# bay, the wider one, is the way in, open, in front of the door
pc = sorted(((q.bounding_box()[0] + q.bounding_box()[3]) / 2, (q.bounding_box()[1] + q.bounding_box()[4]) / 2) for q in posts)
want_px = [-(5 - STD["corner post in"]) * s.FT, STD["middle post"] * s.FT, (5 - STD["corner post in"]) * s.FT]
want_py = -(10 - STD["post back"]) * s.FT
posts_ok = len(pc) == 3 and all(abs(a_[0] - b_) < 0.01 and abs(a_[1] - want_py) < 0.01 for a_, b_ in zip(pc, want_px))
fronts = [r_ for r_ in rails if r_.bounding_box()[4] < s.YF - 30]
rb = fronts[0].bounding_box() if fronts else [0] * 6
rx0 = want_px[0] + s.POST / 2 + STD["rail post gap mm"]
rx1 = want_px[1] - s.POST / 2 - STD["rail post gap mm"]
bal = fronts[0].slice(s.ZF + 15).decompose() if fronts else []
bxs = sorted((q.bounds()[0] + q.bounds()[2]) / 2 for q in bal)
oc_ = [b_ - a_ for a_, b_ in zip(bxs, bxs[1:])]
ends_ = (bxs[0] - rb[0], rb[3] - bxs[-1]) if bxs else (0, 9)
# the designer's count (parts/porch.js railX): from 0.26 ft in, every 0.44 ft while short of the end by
# 0.10, on its run from 0.16 ft off each post's middle
run0, run1 = -(5 - STD["corner post in"]) + 0.16, STD["middle post"] - 0.16
n_des, xb_ = 0, run0 + 0.26
while xb_ < run1 - 0.10:
    n_des, xb_ = n_des + 1, xb_ + STD["rail oc"]
report(posts_ok and len(fronts) == 1 and abs(rb[0] - rx0) < 0.01 and abs(rb[3] - rx1) < 0.01 and len(bxs) == n_des
       and all(abs(d_ - STD["rail oc"] * s.FT) < 0.01 for d_ in oc_) and abs(ends_[0] - ends_[1]) < 0.01,
       f"the porch posts stand at x {', '.join(f'{a_[0]:+.3f}' for a_ in pc)}, y {pc[1][1] if pc else 0:.3f} (STD: corner posts "
       f"0.28 ft in, the one middle post {STD['middle post']} ft); {len(fronts)} front railing, x {rb[0]:.3f} to {rb[3]:.3f}, "
       f"{STD['rail post gap mm']} off the left corner post and the middle post, under the window; {len(bxs)} balusters "
       f"(the designer's count {n_des}) {STD['rail oc']} ft apart, {ends_[0]:.3f} and {ends_[1]:.3f} in from its ends")
by0, by1 = pc[1][0] + s.POST / 2, pc[2][0] - s.POST / 2           # the right bay, between the post faces
bay = s.box(by0 + 0.01, by1 - 0.01, -s.L / 2 - 1, s.YF - s.PROUD - 0.01, s.ZF + 0.01, s.FRAME_Z - 0.01)
in_bay = overlap(s.union([rails_all, posts_all, frame, gable, ceiling, walls_all, door_shut, loft_set]), bay)
deck_bay = s.box(by0 + 0.01, by1 - 0.01, -s.L / 2 + 0.01, s.YF - s.FIT - 0.01, s.ZF - s.DECK + 0.01, s.ZF - 0.3)
deck_whole = overlap(fl, deck_bay) / deck_bay.volume()
left_bay = pc[1][0] - s.POST / 2 - (pc[0][0] + s.POST / 2)
dx0, dx1 = (STD["door"] - STD["door w"] / 2) * s.FT, (STD["door"] + STD["door w"] / 2) * s.FT
report(in_bay < 1e-3 and abs(deck_whole - 1) < 1e-6 and by1 - by0 > left_bay and by0 < dx0 and dx1 < by1 and by1 - by0 >= 34.8,
       f"the way in is the right bay, {by1 - by0:.2f} mm clear between the middle post and the right corner post "
       f"({(by1 - by0) / s.S:.1f} in; the railed left bay is {left_bay:.2f}), in front of the door (x {dx0:.3f} to {dx1:.3f}): "
       f"from the front edge back to the front wall's casings nothing stands in it up to the frame ({in_bay:.4f} mm3) and "
       f"its deck is whole, no hole or socket ({deck_whole * 100:.2f}% solid under the board grooves)")
unit_ = s.union([walls_all, frame, posts_all, gable, door_shut])
base = s.union([fl_open, rails_all])
worst = max(overlap(unit_.translate([0, 0, dz]), base) for dz in (3.0, 10.0, 80.0))
report(worst < 1e-3, f"the walls, porch frame, posts, porch gable and door lift off together, moved up 3, 10 and 80 mm "
                     f"touching nothing on the floor or the railings but the barbs ({worst:.4f} mm3)")

group("6b. the lofts")
lbb = lofts[0].bounding_box()
yc = (lbb[1] + lbb[4]) / 2
f_and_sides = s.union([F, sides_set])


def loft_rest(lf, ys):
    """How a loft (lf) rests on the side walls' top plates, under every joist at both walls, not only somewhere (this
    was a 0.1 mm drop against the whole body, which would pass a loft standing 0.1 off a wall, or off one of them):
    lowered REST, under each of its joists (at ys) at each wall, from the plates' inside face out to the loft's end,
    the share of the plates' top there it meets. A joist with a lug bears only outside its notch, 0.72 mm (0.47 for
    the front loft's end joist), so 0.3 mm2 of plate is enough to look at. Returns (the least share, where, how many
    joist ends have plate under them, how many joist ends)."""
    xl = s.loft_half_width()
    wins, where = [], []
    for y_ in ys:
        for sx_ in (1, -1):
            xa, xb = sorted([sx_ * (s.W / 2 - s.WT - 0.5), sx_ * xl])
            wins.append(s.box(xa, xb, y_ - s.SW / 2, y_ + s.SW / 2, s.LOFT_Z - 3, s.LOFT_Z + 1))
            where.append(f"the joist at y {y_:.2f} on the {'right' if sx_ > 0 else 'left'} side")
    sh = rest_share(lf, body, wins, s.LOFT_Z, min_face=0.3)
    least, at = least_rest([v_ for _, v_ in sh], [where[k_] for k_, _ in sh])
    return least, at, len(sh), len(wins)


for i, lf in enumerate(lofts):
    nm = ("back", "front")[i]
    sy_ = (1, -1)[i]
    v = overlap(body, lf) + overlap(roof_all, lf)
    report(v < 0.01, f"the {nm} loft fits between the walls and under the roof ({v:.4f} mm3)")
    l_ys = [s.loft_y(y_, sy_) for y_ in s.loft_joist_ys()]
    least, at, k_, n_ = loft_rest(lf, l_ys)
    report(least >= 0.5 and k_ == n_ == 2 * len(l_ys),
           f"the {nm} loft rests on the side walls' top plates under every joist: lowered {REST} mm, each of its "
           f"{len(l_ys)} joists meets the plate at both walls, at least {least * 100:.0f}% of the plate's top under it "
           f"(the least {at}; {k_} of {n_} joist ends over plate)")
    moves = {"+x": [0.3, 0, 0], "-x": [-0.3, 0, 0], "+y": [0, 0.3, 0], "-y": [0, -0.3, 0]}
    vals = {k: overlap(body, lf.translate(t)) for k, t in moves.items()}
    if i == 0:
        report(min(vals.values()) > 0.05, f"the {nm} loft can't slide 0.3 mm any way: its lugs sit in the plates' notches "
                                          f"({', '.join(f'{k} {v_:.2f}' for k, v_ in vals.items())} mm3)")
    else:
        to_f = free_move(lf, body, [0, -1, 0], 0.01, 2.0)
        to_blk = free_move(lf, F, [0, -1, 0], 0.01, 2.0)
        report(min(vals["+x"], vals["-x"], vals["+y"]) > 0.05 and to_f <= 0.41 and to_blk <= 0.41,
               f"the {nm} loft can't slide 0.3 mm sideways or back ({vals['+x']:.2f}, {vals['-x']:.2f}, {vals['+y']:.2f} "
               f"mm3); toward the front wall its edge joist's lugs stop it after {to_f:.2f} mm, and the front wall's end "
               f"blocks are {to_blk:.2f} mm off its end joist's lugs")
    worst = sweep(lf, f_and_sides, [[0, 0, dz] for dz in np.arange(0.1, 60.01, 0.1)])
    c_ = (lf.bounding_box()[1] + lf.bounding_box()[4]) / 2
    turned = lf.translate([0, -c_, 0]).rotate([0, 0, 180]).translate([0, c_, 0])
    v1 = overlap(body, turned)
    t_least, t_at, t_k, t_n = loft_rest(turned, [2 * c_ - y_ for y_ in l_ys])
    report(worst < 1e-3 and v1 < 0.01 and t_least >= 0.5 and t_k == t_n == 2 * len(l_ys),
           f"the {nm} loft drops in from 60 mm between the side walls, after the front wall ({worst:.4f} mm3), and goes in "
           f"either way round: turned it fits ({v1:.4f} mm3) and rests the same way, under every joist at both walls "
           f"(lowered {REST}, at least {t_least * 100:.0f}% of the plate under each, the least {t_at})")
    rise = 0.0
    while rise < 3 and overlap(roof_all, lf.translate([0, 0, rise + 0.02])) < 1e-4:
        rise += 0.02
    report(rise < s.LUG_D - 0.3, f"with the roof on, the {nm} loft can rise only {rise:.2f} mm before it meets the roof, "
                                 f"under {s.LUG_D - 0.3:.3f}, so its {s.LUG_D:.3f} mm lugs stay in their notches")
lf = lofts[0]
slide = free_move(lf, sides_set, [0, 1, 0], 0.02, 2.0)
worst = sweep(B, lf.translate([0, slide, 0]), [[0, 0, dz] for dz in DROPS] + [[0, 0, 0]])
gap_end = (s.L / 2 - s.WT) - (lbb[4] + slide)
report(worst < 1e-3 and gap_end >= 0.15,
       f"the back loft slides {slide:.2f} mm toward the back at most, and even there the back wall comes down past it with "
       f"{gap_end:.2f} mm to spare ({worst:.4f} mm3)")
lp = pp["loft"]
worst, _ = worst_overhang(lp)
report(worst < 0.01, f"each loft's lugs print on top with nothing hanging over ({worst:.3f} mm2 worst layer)")

# ---------------------------------------------------------------- the twins' door
# The 10x20 Cabin and the 10x20 Lofted Barn Cabin hang the same 11-lite door in the same doorway, and their fit tests
# the same short door (PRINTER-BRAIN: twin models share parts, so prove the two doors are the same solid). Since Alan's
# answers for the Lofted Barn Cabin (Nov 4 2026, "Loft wall height is 79.5" and "73 1/2 in door, flat boards") its
# door is 73 1/2 in tall and the Cabin's still 75.6: the same door but for its height, each drawn for its own doorway
# by the designer's rules (parts/openings/door-lite.js). Their generators make them with their own code (door_leaf
# and door_to_cabin in make_cabin.py, door_part and door_to_shed in make_barn_cabin.py), so each checker loads its
# twin's generator from the folder beside its own and compares: the door whose function takes a height (door_part)
# built at the other's height through that parameter, hung by its own matrix, against the other's own door hung by
# its own; the two doors as built, over their bottoms and, each from its own top, over their tops; the fit tests'
# doors and doorways; the two front walls round the doorway from under the sill up to under the lower of the two
# heads, and round each top pin hole from its own head; and the floors there. The two checkers hold the same code.
TWINS = {"make_cabin": ("shed model 10x20 lofted barn cabin", "make_barn_cabin", "Lofted Barn Cabin"),
         "make_barn_cabin": ("shed model 10x20 cabin", "make_cabin", "Cabin")}
TWIN_ANGLES = (-2, 0, 45, 90, 102)
TWIN_BAND = 20.0       # the two doors as built match over their bottom 20 mm (the bottom pin, the lower raised panel
                       # and the upper one's foot: under its top, 21.9 on the shorter door) and over their top 20 mm,
                       # from each door's own top (the arch, the rail over it and the top pin: over the cross muntin,
                       # 23.9 under the top on the shorter door)


def twin_generator():
    """(the twin's generator, None), imported from its folder beside this one without leaving a __pycache__ there,
    or (None, why not)."""
    folder, name, _ = TWINS[s.__name__]
    path = os.path.join(os.path.dirname(s.HERE), folder)
    if not os.path.isfile(os.path.join(path, name + ".py")):
        return None, f"{name}.py isn't in {path}"
    keep = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    sys.path.insert(0, path)
    try:
        return importlib.import_module(name), None
    except Exception as e:          # a twin that won't load is a FAIL, not a stop
        return None, f"{name}.py won't load ({type(e).__name__}: {e})"
    finally:
        sys.path.remove(path)
        sys.dont_write_bytecode = keep


def twin_door(g):
    """A generator's door function (door_part, or door_leaf), the matrix that hangs its door swung in theta degrees,
    its fit test's door and doorway, its front wall and its floor."""
    leaf = g.door_leaf if hasattr(g, "door_leaf") else g.door_part
    hang = g.door_to_cabin if hasattr(g, "door_to_cabin") else g.door_to_shed
    fit = g.fit_doorway()
    walls = g.split_walls(g.walls()) if hasattr(g, "split_walls") else g.wall_pieces(g.walls())
    return leaf, hang, g.fit_door(), fit[0] if isinstance(fit, tuple) else fit, walls["front wall"], g.floor()


def door_at(g, leaf, h):
    """g's door (leaf, its door function) built h tall through that function's own height parameter, or None if it
    takes none (make_cabin.py's door_leaf draws only the Cabin's own door, so it is built only at its own height)."""
    if "h" in inspect.signature(leaf).parameters:
        return leaf(h=h)
    return leaf() if abs(h - g.DOOR_H) < 1e-9 else None


def differ(a, b):
    """The volume where two solids differ."""
    return (a - b).volume() + (b - a).volume()


def twin_check(jl, jr):
    """This model's door, fit-test door and doorway, and its front wall and floor round the doorway (its jambs at x
    jl and jr), against the twin's, the same but for the door's height."""
    twin, why = twin_generator()
    _, name, title = TWINS[s.__name__]
    if twin is None:
        report(False, f"the door can't be compared with the {title}'s, its twin: {why}")
        return
    try:
        mine, theirs = twin_door(s), twin_door(twin)
        # the door that takes a height, built at the other's: (its generator's name, the height, the difference
        # hung at each angle) for each way round that can be built (at least one must be)
        built = []
        for (ga, ta), (gb, tb) in (((s, mine), (twin, theirs)), ((twin, theirs), (s, mine))):
            da = door_at(ga, ta[0], gb.DOOR_H)
            if da is not None and abs(ga.DOOR_H - gb.DOOR_H) > 1e-9:
                db = door_at(gb, tb[0], gb.DOOR_H)
                built.append((ga.__name__, "this model's" if gb is s else f"the {title}'s", gb.DOOR_OPEN_H / gb.S,
                              [differ(da.transform(ta[1](th)), db.transform(tb[1](th))) for th in TWIN_ANGLES]))
        own_m, own_t = door_at(s, mine[0], s.DOOR_H), door_at(twin, theirs[0], twin.DOOR_H)
    except Exception as e:          # a twin whose door can't be made is a FAIL, not a stop
        report(False, f"the door can't be compared with the {title}'s, its twin: {type(e).__name__}: {e}")
        return
    same_h = abs(s.DOOR_H - twin.DOOR_H) < 1e-9
    if same_h:                      # the same height: the two doors themselves, hung
        built = [(s.__name__, f"the {title}'s", s.DOOR_OPEN_H / s.S,
                  [differ(own_m.transform(mine[1](th)), own_t.transform(theirs[1](th))) for th in TWIN_ANGLES])]
    hung = max([d_ for *_, ds_ in built for d_ in ds_] or [float("inf")])
    # the two doors as built, each at its own height: the same over their bottom TWIN_BAND, and over their top
    # TWIN_BAND (the top pin's 2.0 and 1 more over it) measured from each one's own top
    def band(d, h, top):
        return (d ^ s.box(-50, 50, -5, TWIN_BAND, -5, 5) if not top else
                (d ^ s.box(-50, 50, h - TWIN_BAND, h + 5, -5, 5)).translate([0, -h, 0]))
    low_d = differ(band(own_m, s.DOOR_H, False), band(own_t, twin.DOOR_H, False))
    top_d = differ(band(own_m, s.DOOR_H, True), band(own_t, twin.DOOR_H, True))
    fit_d, fit_w = differ(mine[2], theirs[2]), differ(mine[3], theirs[3])
    # the front wall from under its sill up to under the lower of the two heads (higher up, each has its own door
    # head and header), out to 2 mm past each jamb, which takes in both king studs, the stop, the bottom pin hole and
    # the trench; then round each top pin hole, from 1 mm under its own head (the hole's foot) to 0.6 over the hole,
    # each wall measured from its own head (the kings' and the stop's tops, the head casing, the header round the
    # hole); and the floor there, from the porch's front edge to 15 mm into the room: the sill's pocket, the trench's
    # end, the seam
    head_m, head_t = s.ZF + s.DOOR_OPEN_H, twin.ZF + twin.DOOR_OPEN_H
    low_top = min(head_m, head_t)
    reg = s.box(jl - 2, jr + 2, -s.L, s.L, -20, low_top)
    wall_d = differ(mine[4] ^ reg, theirs[4] ^ reg)

    def round_hole(w, head):
        return (w ^ s.box(jl - 2, jr + 2, -s.L, s.L, head - 1, head + s.HOLE_TOP_DEPTH + 0.6)).translate([0, 0, -head])
    hole_d = differ(round_hole(mine[4], head_m), round_hole(theirs[4], head_t))
    reg_f = s.box(jl - 2, jr + 2, -s.L, s.YF + s.WT + 15, -20, s.ZF + 1)
    floor_d = differ(mine[5] ^ reg_f, theirs[5] ^ reg_f)
    hb = built[0] if built else (name, f"the {title}'s", 0.0, [])
    report(bool(built) and hung < 1e-4 and low_d < 1e-4 and top_d < 1e-4 and fit_d < 1e-4 and fit_w < 1e-4 and wall_d < 1e-4
           and hole_d < 1e-4 and floor_d < 1e-4,
           f"the door is the {title}'s, its twin's (made with its own code by {name}.py, in the folder beside this one), "
           f"but for its height: this one's doorway {s.DOOR_OPEN_H / s.S:.1f} in tall, the {title}'s "
           f"{twin.DOOR_OPEN_H / twin.S:.1f}. "
           + (f"The two doors themselves, hung at {', '.join(map(str, TWIN_ANGLES))} degrees, differ by {hung:.4f} mm3 "
              f"at most" if same_h else
              f"Built {hb[2]:.1f} in tall by {hb[0]}.py's own door function, through its height parameter (the "
              f"designer's rules), and hung by its own matrix at {', '.join(map(str, TWIN_ANGLES))} degrees, the door "
              f"differs from {hb[1]} own door by {hung:.4f} mm3 at most")
           + f" (0.0001 allowed, as for each comparison here: the two codes use the same formulas, so only float rounding "
           f"is left, under a millionth of a mm3); as built, the two "
           f"doors differ by {low_d:.4f} over their bottom {TWIN_BAND:.0f} mm and by {top_d:.4f} over their top "
           f"{TWIN_BAND:.0f}, each from its own top; the fit tests' doors by {fit_d:.4f} and their doorways by "
           f"{fit_w:.4f}; the front walls round the doorway, from under the sill to under the lower head (z "
           f"{low_top:.3f}) and 2 mm past each jamb, by {wall_d:.4f}, and round the top pin hole, from 1 under each "
           f"one's own head to 0.6 over the hole, by {hole_d:.4f}; and the floors there by {floor_d:.4f} mm3")


# ================================================================ 7
group("7. door")
# Alan Nov 4 2026, "hinges on the right side" (the Cabin's question 16; the twins share the door): the door
# hangs on the doorway's right-hand jamb as seen from the porch (+x, next to the right side wall), the knob
# toward the middle of the wall, the stop on the left-hand (latch) jamb, and swung in it turns toward the
# right side wall. Measured off the parts, not taken from HINGE
LEFT_HINGED_SWING = 101.9   # how far the door swung in hinged on the left (check Nov 4 2026, before Alan's answer)
jl, jr = (STD["door"] - STD["door w"] / 2) * s.FT, (STD["door"] + STD["door w"] / 2) * s.FT   # the doorway, 2.286..30.861
pin_b = (door_shut ^ s.box(-s.W, s.W, -s.L, s.L, -5, s.ZF)).bounding_box()          # the bottom pin, under the threshold
pin_x = (pin_b[0] + pin_b[3]) / 2
sill_hole = (s.box(jl, jr, s.PIN_Y - 0.05, s.PIN_Y + 0.05, s.ZF - 0.9, s.ZF - 0.8) - F).bounding_box()
head_hole = (s.box(jl, jr, s.PIN_Y - 0.05, s.PIN_Y + 0.05, s.ZF + s.DOOR_OPEN_H + 1.0, s.ZF + s.DOOR_OPEN_H + 1.1)
             - F).bounding_box()
knob_b = (door_shut ^ s.box(-s.W, s.W, -s.L, s.PIN_Y - s.DOOR_R - 0.05, -5, 200)).bounding_box()   # out past its face
knob_x = (knob_b[0] + knob_b[3]) / 2
stop_b = (F ^ s.box(jl + 0.01, jr - 0.01, -s.L, s.L, s.ZF + 20, s.ZF + 21)).bounding_box()        # all that is in the doorway
swung = door.transform(s.door_to_shed(45)).bounding_box()
hand_ok = (abs(pin_x - (jr - s.DOOR_GAP - s.DOOR_R)) < 1e-3 and abs((sill_hole[0] + sill_hole[3]) / 2 - pin_x) < 0.01
           and abs((head_hole[0] + head_hole[3]) / 2 - pin_x) < 0.01 and pin_x > STD["door"] * s.FT
           and abs(knob_x - (jl + s.DOOR_GAP + 2.2)) < 1e-3 and abs(stop_b[0] - (jl + 0.01)) < 1e-3
           and abs(stop_b[3] - (jl + 0.8)) < 1e-3 and swung[4] > s.YF + s.WT + 15 and swung[0] > jl + 5)
report(hand_ok, f"the door hangs on the right as seen from the porch (Alan Nov 4 2026, \"hinges on the right side\", for the "
                f"Cabin's door, which this is): its bottom pin at x {pin_x:.3f}, {jr - pin_x:.2f} mm in from the doorway's "
                f"right-hand jamb (x {jr:.3f}, next to the right side wall), with both pin holes over it (x "
                f"{(sill_hole[0] + sill_hole[3]) / 2:.3f} and {(head_hole[0] + head_hole[3]) / 2:.3f}); its knob on the outside "
                f"{knob_x - jl:.2f} mm from the left-hand (latch) jamb (x {jl:.3f}), toward the middle of the wall, and the stop "
                f"on that jamb only, reaching x {stop_b[3]:.3f}; swung in 45 degrees it reaches {swung[4] - (s.YF + s.WT):.1f} mm "
                f"into the room on the right-hand side of the doorway, {swung[0] - jl:.1f} mm from the latch jamb at its nearest")
# the leaf drawn for Alan's 73 1/2 in doorway (Nov 4 2026) by the designer's rules, typed in here from
# parts/openings/door-lite.js, not taken from make_barn_cabin.py: the glass from 0.42 of the height up, its arch's top
# 0.55 ft under the head and its radius half the glass's 2.24 ft, the cross muntin halfway up the glass's straight
# part; the lower raised panel 0.30 to 1.12 ft up, the upper from 1.36 ft to 0.24 ft under the glass; the knob 0.44 of
# the height up. Measured off the door hung shut, in inches over the floor: along a line up the leaf's middle (the
# glass and the panels' grooves, 0.2 under its outside face), and one 5 mm toward the hinge from it through the
# muntins (0.5 off the inside face), and the knob
DH_IN = ALAN["door h"]
want_leaf = {"glass bottom": 0.42 * DH_IN, "arch top": DH_IN - 0.55 * 12, "spring line": DH_IN - 0.55 * 12 - 1.12 * 12,
             "panels": [(0.30 * 12, 1.12 * 12), (1.36 * 12, 0.42 * DH_IN - 0.24 * 12)], "knob": 0.44 * DH_IN}
want_leaf["cross muntin"] = (want_leaf["glass bottom"] + want_leaf["spring line"]) / 2


def runs_up(m, x, y):
    """The (bottom, top) of each piece of m along a thin line straight up at (x, y), in inches over the floor."""
    b_ = m ^ s.box(x - 0.02, x + 0.02, y - 0.02, y + 0.02, -10, 200)
    return sorted(((q.bounding_box()[2] - s.ZF) / s.S, (q.bounding_box()[5] - s.ZF) / s.S) for q in b_.decompose()
                  if q.volume() > 1e-9)


mid_x = s.DOOR_X                                        # the leaf's middle (between the pin line and the latch edge)
r_out = runs_up(door_shut, mid_x, s.PIN_Y - s.DOOR_R + 0.2)
gaps_out = [(a_[1], b_[0]) for a_, b_ in zip(r_out, r_out[1:])]
r_mun = runs_up(door_shut, mid_x + s.HINGE * 5.0, s.PIN_Y + s.DOOR_R - 0.5)
mun_mid = [(a_ + b_) / 2 for a_, b_ in r_mun[1:-1]]
knob_bb = (door_shut ^ s.box(-s.W, s.W, -s.L, s.PIN_Y - s.DOOR_R - 0.05, -5, 200)).bounding_box()
knob_in = ((knob_bb[2] + knob_bb[5]) / 2 - s.ZF) / s.S
got_panels = [(gaps_out[0][0], gaps_out[1][1]), (gaps_out[2][0], gaps_out[3][1])] if len(gaps_out) == 5 else []
leaf_ok = (len(gaps_out) == 5 and abs(gaps_out[4][0] - want_leaf["glass bottom"]) < 0.02
           and abs(gaps_out[4][1] - want_leaf["arch top"]) < 0.02
           and all(abs(a_ - c_) < 0.02 and abs(b_ - d_) < 0.02 for (a_, b_), (c_, d_) in zip(got_panels, want_leaf["panels"]))
           and len(mun_mid) == 3 and abs(mun_mid[0] - want_leaf["cross muntin"]) < 0.02
           and abs(mun_mid[1] - want_leaf["spring line"]) < 0.02 and abs(knob_in - want_leaf["knob"]) < 0.02)
report(leaf_ok,
       f"the door's leaf is the designer's 11-lite drawn for its {DH_IN} in doorway (door-lite.js, typed in here): the glass "
       f"from {gaps_out[4][0] if len(gaps_out) == 5 else 0:.2f} in over the floor (0.42 of the height, "
       f"{want_leaf['glass bottom']:.2f}) up to the arch's top at {gaps_out[4][1] if len(gaps_out) == 5 else 0:.2f} (0.55 ft "
       f"under the head, {want_leaf['arch top']:.2f}), the cross muntin at {mun_mid[0] if mun_mid else 0:.2f} and the "
       f"spring bar at {mun_mid[1] if len(mun_mid) > 1 else 0:.2f} ({want_leaf['cross muntin']:.2f}, "
       f"{want_leaf['spring line']:.2f}); the raised panels "
       + ", ".join(f"{a_:.2f} to {b_:.2f}" for a_, b_ in got_panels)
       + f" in ({', '.join(f'{a_:.2f} to {b_:.2f}' for a_, b_ in want_leaf['panels'])}); the knob {knob_in:.2f} in up "
       f"(0.44 of the height, {want_leaf['knob']:.2f}). So it is the Cabin's 75.6 in door 2.1 in shorter: the arch, the "
       f"rail over it and the lower panel the same, the glass starting {0.42 * (75.6 - DH_IN):.2f} in lower, its six "
       f"lower lites {0.58 * (75.6 - DH_IN):.2f} in shorter, the upper panel {0.42 * (75.6 - DH_IN):.2f} shorter, the knob "
       f"{0.44 * (75.6 - DH_IN):.2f} lower")
# the door swung against everything else in the finished cabin: the walls and floor (the right side wall and
# its window casing included), both corner angles, both lofts and their joists, the porch frame, ceiling,
# gable, posts and railings, and the four roof sheets
angles_on = s.union([s.corner_angle(sx, sy) for sx, sy in s.CORNERS])
obstacles = s.union([body, frame, loft_set, gable, ceiling, posts_all, rails_all, roof_all, angles_on])
v0 = overlap(body, door_shut)
last_free, stop_deg = 0, None
for deg in range(0, 131, 2):
    v = overlap(obstacles, door.transform(s.door_to_shed(deg)))
    if v < 0.01:
        last_free = deg
    else:
        stop_deg = deg
        break
lo, hi = float(last_free), float(stop_deg if stop_deg else 130)
for _ in range(20):
    mid = (lo + hi) / 2
    lo, hi = (mid, hi) if overlap(obstacles, door.transform(s.door_to_shed(mid))) < 0.01 else (lo, mid)
vm2 = overlap(body, door.transform(s.door_to_shed(-2)))
hit = s.union([q for q in (obstacles ^ door.transform(s.door_to_shed(hi))).decompose()      # (not the flat touches
               if q.volume() > 1e-6]).bounding_box()                                        # of the pin)
king = [b for b in s.framing_layout("front wall")[0] if abs(b[0] - jr) < 1e-6 and abs(b[1] - (jr + s.SW)) < 1e-6]
at_king = bool(king) and jr - 0.01 < hit[0] and hit[3] < jr + s.SW + 0.01 and hit[1] > s.YF + s.TS - 0.01
open_ = door.transform(s.door_to_shed(lo)).bounding_box()
report(v0 < 0.01, f"the door shut fits its opening ({v0:.4f} mm3)")
report(last_free >= 90 and lo >= LEFT_HINGED_SWING - 0.05 and at_king and open_[3] > s.PIN_X + s.DOOR_R + 3,
       f"it swings in freely to {last_free} degrees in 2 degree steps (it stops at {lo:.1f}, at least the "
       f"{LEFT_HINGED_SWING} it swung hinged on the left, its face against the hinge-side king stud, x {hit[0]:.3f} to "
       f"{hit[3]:.3f}), toward the right side wall (its latch edge out to x {open_[3]:.2f}, "
       f"{s.W / 2 - s.WT - open_[3]:.1f} mm short of that wall's studs), clear of the floor, the right side wall and its "
       f"window casing, the casings, both corner angles, the porch, the roof sheets, both lofts and every joist and stud")
report(vm2 > 0.05, f"at -2 degrees it meets the stop outside its latch edge ({vm2:.2f} mm3), so it can't swing out")
# the pin holes and the front wall's bed face
Fp = s.to_print(s.WALL_TO_PRINT["front wall"], [F])[0]
holes_u = s.DOOR_AXIS_U - s.PIN_HOLE_D / 2
R3 = np.column_stack([np.array(s.WALL_TO_PRINT["front wall"], dtype=float), np.zeros(3)])
fbb = F.transform(R3).bounding_box()
hole_top = s.cyl_z(s.PIN_X, s.PIN_Y, s.ZF + s.DOOR_OPEN_H - 1, s.ZF + s.DOOR_OPEN_H + s.HOLE_TOP_DEPTH, s.PIN_HOLE_D)
over = hole_top.transform(R3).translate([-fbb[0], -fbb[1], -fbb[2]])
ob_ = over.bounding_box()
first = as_printed(Fp ^ s.box(ob_[0] - 2, ob_[3] + 2, ob_[1] - 0.5, ob_[4], -1, 0.25))
lay = first.slice(0.125) ^ m3.CrossSection.square([ob_[3] - ob_[0], ob_[4] - ob_[1] - 1.0]).translate([ob_[0], ob_[1] + 1.0])
want = (ob_[3] - ob_[0]) * (ob_[4] - ob_[1] - 1.0)
report(abs(holes_u - 0.25) < 1e-6 and abs(lay.area() - want) < 0.01,
       f"the pin holes reach down only to u {holes_u:.2f}, the top of the first layer, and as printed the front wall's first "
       f"layer is whole over the top hole ({lay.area():.2f} of {want:.2f} mm2)")
# round the top hole: since Alan's 79 1/2 in wall and 73 1/2 in door (Nov 4 2026) the flat header is right under the
# top plates, so the hole, 2.2 up into the 2.38 header, has 0.18 of header and then the plates over it (on the 82.8 in
# wall a hinge block filled the open bay over the header there, which left only a 0.18 web). The wall must be solid
# for 0.6 round the hole, from its inside face to 0.6 past the hole's far side, from the door's head up to the wall
# top, nothing missing but the hole itself; and in the framing list, over the doorway, only the header (from the head
# right up to the top plates, past the hole 0.6 each side) and the top plates: no cripple, no block
head_z = s.ZF + s.DOOR_OPEN_H
h_top = head_z + s.HOLE_TOP_DEPTH
r_ = s.PIN_HOLE_D / 2
u_far = s.DOOR_AXIS_U + r_ + 0.6
round_hole = s.box(s.PIN_X - r_ - 0.6, s.PIN_X + r_ + 0.6, s.YF + s.WT - u_far, s.YF + s.WT, head_z, s.ZWT - 0.16) - hole_top
filled = overlap(F, round_hole) / round_hole.volume()
fl_boxes = s.framing_layout("front wall")[0]
over_door = sorted([b for b in fl_boxes if b[0] < s.DOOR_X1 - 1e-6 and b[1] > s.DOOR_X0 + 1e-6 and b[5] > head_z + 1e-6],
                   key=lambda b_: b_[4])
zt_ = s.ZWT - s.PLATE_TOP
hdr_ = over_door[0] if over_door else (0,) * 6
hdr_right = (len(over_door) == 2 and abs(hdr_[4] - head_z) < 1e-6 and abs(hdr_[5] - zt_) < 1e-6
             and hdr_[0] <= s.PIN_X - r_ - 0.6 and hdr_[1] >= s.PIN_X + r_ + 0.6
             and abs(over_door[1][4] - zt_) < 1e-6 and abs(over_door[1][5] - s.ZWT) < 1e-6)
report(abs(filled - 1) < 1e-6 and hdr_right,
       f"round the top pin hole (its top {h_top:.3f}, {zt_ - h_top:.2f} under the flat header's top, which is the top "
       f"plates' underside, {zt_:.3f}): over the doorway only the header, {(hdr_[4] - s.ZF) / s.S:.1f} to "
       f"{(hdr_[5] - s.ZF) / s.S:.1f} in, x {hdr_[0]:.3f} to {hdr_[1]:.3f}, and the top plates, no cripple or block "
       f"({len(over_door)} members); the wall is solid for 0.6 round the hole, from the inside face to u {u_far:.2f}, "
       f"from the head up to the wall top ({filled * 100:.2f}%)")


def hang_matrix(d, lift):
    """The door lifted lift with its top pin in the head hole and its bottom swung d into the room
    (the bottom pin's tip d inside the pin line), tilted about the top pin at the door's top."""
    m = s.door_to_shed(0)
    m[2, 3] += lift
    h = s.DOOR_H + s.PIN_BOTTOM_LEN
    a = math.asin(d / h)
    c, sn = math.cos(a), math.sin(a)
    Rx = np.array([[1, 0, 0], [0, c, -sn], [0, sn, c]])
    piv = np.array([0, s.PIN_Y, s.ZF + s.DOOR_BOTTOM_GAP + s.DOOR_H + lift])
    return np.column_stack([Rx @ m[:, :3], Rx @ (m[:, 3] - piv) + piv]), math.degrees(a)


F_loose = F                                      # the front wall off the floor: no floor in the way
worst, tilts = 0.0, []
for d in np.arange(2.8, -0.001, -0.25):
    mt, a = hang_matrix(max(d, 0.0), 0.5)
    tilts.append(a)
    worst = max(worst, overlap(F_loose, door.transform(mt)))
for lift in np.arange(0.5, -0.001, -0.05):
    mt, _ = hang_matrix(0.0, lift)
    worst = max(worst, overlap(F_loose, door.transform(mt)))
mt, _ = hang_matrix(2.8, 0.5)
pin_tip = s.cyl_y(0, -s.PIN_BOTTOM_LEN, -s.PIN_BOTTOM_LEN + 0.01, s.DOOR_R, s.PIN_D).transform(mt).bounding_box()
start_clear = pin_tip[1] - (s.YF + s.WT)
low = s.cyl_y(0, -s.PIN_BOTTOM_LEN, 0, s.DOOR_R, s.PIN_D)
margin_tr = min((low.transform(hang_matrix(dd, 0.5)[0]).bounding_box()[2] - (s.ZF - s.TRENCH_DEPTH))
                for dd in np.arange(2.6, -0.001, -0.25))
margin_hd = s.ZF + s.DOOR_OPEN_H - (door.transform(hang_matrix(2.8, 0.5)[0]) ^ s.box(-s.W, s.W, s.PIN_Y - 3, s.L, 0, 200) -
                                    s.cyl_z(s.PIN_X, s.PIN_Y, 0, 200, s.PIN_HOLE_D)).bounding_box()[5]
report(worst < 0.05 and start_clear >= 0.19 and margin_tr > 0 and margin_hd > 0,
       f"in the loose front wall the door hangs from the inside: top pin up in the head hole, lifted 0.5, the bottom pin "
       f"{start_clear:.2f} mm inside the wall's inside face (tilt {max(tilts):.2f} degrees), swung out along the trench in "
       f"0.25 steps and dropped, worst overlap {worst:.4f} mm3; the pin's tip {margin_tr:.2f} over the trench floor and the "
       f"door {margin_hd:.3f} under the head")
mt = s.door_to_shed(0)
mt[2, 3] += 0.55
v1 = overlap(F, door.transform(mt))
mt2, _ = hang_matrix(2.8, 0.55)
v2 = overlap(F ^ s.box(-s.W, s.W, -s.L, s.L, s.ZF + 30, 200), door.transform(mt2))
report(v1 < 0.01 and v2 < 0.01, f"lifted 0.55 mm the door still clears the head of the opening ({v1:.4f} mm3), also with "
                                f"its top inside corner raised by the tilt ({v2:.4f} mm3)")
# captive: with the front wall on the floor the pin can't get out over the floor
px = s.PIN_X
tx0, tx1, ty0 = px - s.PIN_HOLE_D / 2, px + s.PIN_HOLE_D / 2, s.YF + s.WT + s.FIT
solid_top = overlap(fl, s.box(tx0, tx1, ty0, ty0 + 10, s.ZF - 0.3, s.ZF))
# hung on the right, the trench's width takes in the floor sheet seam 8 ft from the left side (x 28.575), which
# runs into the room from the pocket under the pin's left edge. A seam is 0.4 wide and 0.25 deep, a fifth of the
# 2.0 pin, so the pin's flat foot spans it; and tilted toward the room the pin's lowest point is on the line
# under its centre, which stays clear of the seam even with the pin 0.35 to one side in its hole. So the deck
# there is whole but for exactly the seams, and each keeps clear of that line
seams = [sm for sm in s.floor_seams() if sm[1] > tx0 and sm[0] < tx1 and sm[3] > ty0 and sm[2] < ty0 + 10]
seam_cut = [s.box(max(sm[0], tx0), min(sm[1], tx1), max(sm[2], ty0), min(sm[3], ty0 + 10), s.ZF - 0.25, s.ZF) for sm in seams]
seam_v = sum(b_.volume() for b_ in seam_cut)
off_seam = (s.box(tx0, tx1, ty0, ty0 + 10, s.ZF - 0.3, s.ZF) - fl - s.union(seam_cut)).volume() if seams else 0.0
seam_clear = min([max(sm[0] - (px + 0.35), (px - 0.35) - sm[1]) for sm in seams] or [99.0])
seam_w = max([sm[1] - sm[0] for sm in seams] or [0.0])
seam_ok = off_seam < 1e-6 and seam_w <= s.PIN_D / 5 + 1e-9 and seam_clear > 0.1
want = s.PIN_HOLE_D * 10 * 0.3 - seam_v
best = None
head = s.ZF + s.DOOR_OPEN_H
for t100 in range(0, 2001, 5):
    th = math.radians(t100 / 100)
    for ddy in np.arange(-0.35, 0.351, 0.05):
        lift = min(head - (s.ZF + s.DOOR_BOTTOM_GAP + s.DOOR_H) - 1.0 * math.sin(th), 0.8)
        hp = s.DOOR_H + s.PIN_BOTTOM_LEN
        yc_ = s.PIN_Y + ddy + hp * math.sin(th)
        zc_ = s.ZF + s.DOOR_BOTTOM_GAP + s.DOOR_H + lift - hp * math.cos(th)
        zlow = zc_ - 1.0 * math.sin(th)
        far = yc_ + 1.0 * math.cos(th)
        if zlow >= s.ZF - 1e-9 and (best is None or far < best[0]):
            best = (far, t100 / 100)
inside_floor = best[0] - (s.YF + s.WT + s.FIT)
# (8.0 needed on the 75.6 in door, which measured 8.1; the 73 1/2 in door (Nov 4 2026) is 1.67 mm shorter, and tilting
# it until its bottom pin rises to the deck's top swings the pin in about the square root of its length less far,
# 8.1 x sqrt(58.74 / 60.41) = 7.99, so 7.9 is needed now: the pin, 2.0 across, is still wholly over solid floor, its
# near edge 5.9 or more inside the pocket wall, when it could first ride up onto the deck. The Cabin's checker
# needs 5 for its door)
report(abs(solid_top - want) < 1e-6 and seam_ok and inside_floor >= 7.9,
       f"with the front wall on the floor the door is captive: the deck is whole over the trench's width inside the pocket "
       f"wall ({solid_top:.3f} of {want:.3f} mm3) but for {len(seams)} floor sheet seam"
       + (f" (x {', '.join(f'{(sm[0] + sm[1]) / 2:.3f}' for sm in seams)}, {seam_w:.1f} mm wide, {seam_v:.3f} mm3 of it, "
          f"{seam_clear:.3f} mm clear of the line under the pin's centre with the pin 0.35 to either side)" if seams else "s")
       + f", and tilted 0 to 20 degrees toward the room its bottom pin rises to the deck's top only with its far edge "
       f"{inside_floor:.1f} mm inside solid floor (at {best[1]:.1f} degrees)")
twin_check(jl, jr)

# ================================================================ 8
group("8. roof")
porch_set = s.union([gable, frame, posts_all, rails_all, ceiling])
everything = s.union([body, porch_set])
for name, sh in sheets.items():
    v = overlap(everything, sh)
    report(v < 0.01, f"the {name} sits on the two gables without cutting into the body or the porch ({v:.4f} mm3)")
names = list(sheets)
worst = max(overlap(sheets[a], sheets[b]) for a, b in itertools.combinations(names, 2))
report(worst < 0.001, f"no roof sheet overlaps another, at the ridge or where they lap ({worst:.4f} mm3)")
_, nu = s.seg_line("upper", 1)
_, nl = s.seg_line("lower", 1)
dl = np.array([nl[1], -nl[0]])
du = np.array([nu[1], -nu[0]])
N3 = np.array([nl[0], 0, nl[1]])
gables = s.union([B ^ s.box(-s.W, s.W, 0, s.L, s.ZWT - 1, 200), gable])
inside = s.union([body, loft_set, porch_set])


def sheet_rest(name, gn):
    """How a roof sheet (name, in sheets) rests on a gable (gn "back" or "porch") all the way along its slope, not only
    touching it somewhere (the 10x20 Cabin's roof_rest; this was an upper sheet lowered 0.3 mm and a lower one pushed
    0.3 in, which would pass a sheet standing up to 0.3 off one gable, or off all of it but one end): moved REST
    square to its slope, into the roof line, the volume it meets the gable's top by (its roof pegs left out: they
    stand up through the sheet's holes) in every 1 mm of x along the slope it lies on, the upper sheets from the
    ridge gap (x 0.1) out to the knee, the lower from the knee out to the side walls' inside face (past that the
    gable's top is cut ROOF_CLR under the steep sheets at the corner). Returns (the least, the x of the middle of
    that mm, how many mm)."""
    sx_ = 1 if name.startswith("right") else -1
    seg_ = "upper" if "upper" in name else "lower"
    _, n_ = s.seg_line(seg_, sx_)
    g_, sy_ = (B, 1) if gn == "back" else (gable, -1)
    base_ = g_ - s.union(s.roof_pegs(sy_))
    a0, a1 = (0.1, s.KNEE_X) if seg_ == "upper" else (s.KNEE_X, s.W / 2 - s.WT)
    xs_ = [a0 + k_ for k_ in range(int(a1 - a0))]
    yb_ = (s.L / 2 - s.WT - 1, s.L / 2 + 1) if sy_ > 0 else (-s.L / 2 - 1, -s.L / 2 + s.WT + 1)
    wins = [s.box(*sorted([sx_ * x_, sx_ * (x_ + 1)]), *yb_, -1, 300) for x_ in xs_]
    vols = rest_vols(sheets[name], base_, wins, d=(-n_[0], 0, -n_[1]))
    least, at = least_rest(vols, [sx_ * (x_ + 0.5) for x_ in xs_])
    return least, at, len(wins)


rests_ = {(nm_, gn_): sheet_rest(nm_, gn_) for nm_ in sheets for gn_ in ("back", "porch")}
worst_up = min((v_ for v_ in rests_.items() if "upper" in v_[0][0]), key=lambda kv_: kv_[1][0])
worst_lo = min((v_ for v_ in rests_.items() if "lower" in v_[0][0]), key=lambda kv_: kv_[1][0])
report(worst_up[1][0] >= REST * REST_MM2 and worst_up[1][2] >= 30,
       f"each upper sheet rests on BOTH gables all along: moved {REST} mm square to its slope, each meets each gable's top "
       f"in every 1 mm from the ridge out to the knee ({worst_up[1][2]} mm), by {worst_up[1][0]:.3f} mm3 or more (the least "
       f"the {worst_up[0][0]} on the {worst_up[0][1]} gable at x {worst_up[1][1]:+.1f}; {REST * REST_MM2:.2f} needed, "
       f"1 mm2 of bearing)")
report(worst_lo[1][0] >= REST * REST_MM2 and worst_lo[1][2] >= 6,
       f"each lower sheet rests on both gables' steep edges all along: moved {REST} mm square to its slope, each meets "
       f"each gable's top in every 1 mm from the knee out to the side walls' inside face ({worst_lo[1][2]} mm), by "
       f"{worst_lo[1][0]:.3f} mm3 or more (the least the {worst_lo[0][0]} on the {worst_lo[0][1]} gable at x "
       f"{worst_lo[1][1]:+.1f})")
lift = 0.05 * np.array([nu[0], 0, nu[1]])
va = overlap(gables, upper.translate(lift + [0, 1.0, 0]))
vd = overlap(gables, upper.translate(lift + [du[0], 0, du[1]]))
report(min(va, vd) > 0.05, f"slid 1 mm along the cabin ({va:.2f}) or down its slope ({vd:.2f} mm3), an upper sheet is "
                           f"held by its pegs")
lift = np.array([0, 0, 0.05])
va = overlap(gables, lower.translate(lift + [0, 1.0, 0]))
vd = overlap(gables, lower.translate(lift + 0.3 * np.array([dl[0], 0, dl[1]])))
vo = overlap(gables, lower.translate(0.3 * N3))
topp = np.array([s.LOWER_A[0], 0, s.LOWER_A[1]])
a = math.radians(-2)
R = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
vs_ = overlap(gables, lower.transform(np.column_stack([R, topp - R @ topp])))
report(min(va, vd, vo, vs_) > 0.05,
       f"a lower sheet is held by its pegs when slid 1 mm along ({va:.2f}), 0.3 mm down its slope ({vd:.2f}) or 0.3 mm "
       f"straight out ({vo:.2f}), or with its bottom swung out 2 degrees ({vs_:.2f} mm3)")
worst = sweep(lower, inside, [[0, 0, dz] for dz in np.arange(0, 20.01, 0.1)])
report(worst < 1e-3, f"a lower sheet goes on and lifts off straight up, touching nothing from 20 mm up, the lofts, porch "
                     f"frame and posts in place ({worst:.4f} mm3)")
h = 0.0
while h < 3 and overlap(upper, lower.translate([0, 0, h + 0.02])) < 1e-4:
    h += 0.02
held = overlap(gables, lower.translate([0, 0, h]).translate(0.3 * np.array([dl[0], 0, dl[1]])))
report(h < 1.0 and held > 0.05, f"with the upper sheet on, its tail is in the way of the lower sheet's only way off: lifted "
                                f"{h:.2f} mm the lower sheet meets it, still down on its pegs ({held:.2f} mm3), so it is locked on")


def printed_sheet(piece, a, b):
    mat = s.panel_frame(a, b)
    R, p0 = mat[:, :3], mat[:, 3]
    swap = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], dtype=float)
    A = swap @ R.T
    t = -A @ p0
    flat = piece.transform(np.column_stack([A, t]))
    bb = flat.bounding_box()
    back = as_printed(flat.translate([-bb[0], -bb[1], -bb[2]])).translate([bb[0], bb[1], bb[2]])
    return back.transform(np.column_stack([A.T, -A.T @ t]))


low_p = printed_sheet(lower, s.LOWER_A, s.LOWER_B)
up_dir = -np.array([dl[0], 0, dl[1]])
rise = 0.0
while rise < 2 and overlap(gables, low_p.translate(rise * up_dir)) > 1e-3:
    rise += 0.02
gap = 0.0
while gap < 2 and overlap(upper, low_p.translate((rise + gap + 0.02) * up_dir)) < 1e-4:
    gap += 0.02
report(gap >= 0.1, f"as printed, a lower sheet rests {rise:.2f} mm further up its slope than drawn, and the upper sheet's "
                   f"tail still clears it by {gap:.2f} mm, so the upper sheet sits on the gables")
roof_low = s.union([lower, lower.mirror([1, 0, 0])])
worst = sweep(upper, s.union([inside, roof_low]), [[0, 0, dz] for dz in np.arange(0.1, 20.01, 0.1)])
report(worst < 1e-3, f"an upper sheet goes on and lifts off straight up, touching nothing from 20 mm up with the lower "
                     f"sheets, lofts and porch in place ({worst:.4f} mm3)")
g_side = min(sh.min_gap(sides_set, 1.0) for sh in sheets.values())
g_F = min(sh.min_gap(F, 1.0) for sh in sheets.values())
g_fr = min(sh.min_gap(frame, 1.0) for sh in sheets.values())
report(min(g_side, g_F, g_fr) >= s.ROOF_CLR - 0.002,
       f"every sheet keeps {s.ROOF_CLR} clear of the side walls ({g_side:.3f}), the front wall's top corners ({g_F:.3f}) "
       f"and the porch frame ({g_fr:.3f})")

# ================================================================ 9
group("9. skids")
# the floor sits on each skid at every joist and band it crosses, not only somewhere (these were raised 0.3 mm, which
# would pass a skid standing up to 0.3 under the floor, or under all of it but one joist): raised REST, each skid
# meets the floor's underside (and the back wall's skirt over its back notch) under every joist, both end bands and
# the front wall's band, by REST_MM2 of bearing or more in each
yb_back = s.L / 2 - s.TS - s.FLOOR_CLR
sk_spans = ([(j_ - s.SW / 2, j_ + s.SW / 2, f"joist y {j_:.2f}") for j_ in sorted(s.joist_ys())]
            + [(-s.L / 2, -s.L / 2 + s.RIM, "front band"), (yb_back - s.RIM, s.L / 2, "back band and skirt"),
               (s.F_BAND[0], s.F_BAND[1], "the front wall's band")])
for i, k in enumerate(sk):
    v = overlap(body, k)
    kb_ = k.bounding_box()
    sk_wins = [s.box(kb_[0] - 0.5, kb_[3] + 0.5, y0_, y1_, -1, 1) for y0_, y1_, _ in sk_spans]
    up_, up_at = least_rest(rest_vols(k, body, sk_wins, d=(0, 0, 1)), [w_ for _, _, w_ in sk_spans])
    hold = min(overlap(fl, k.translate(t)) for t in ([0.3, 0, 0], [-0.3, 0, 0], [0, 0.3, 0], [0, -0.3, 0]))
    xc_ = (k.bounding_box()[0] + k.bounding_box()[3]) / 2
    turned = k.translate([-xc_, 0, 0]).rotate([0, 0, 180]).translate([xc_, 0, 0])
    wrong = overlap(fl, turned)
    report(v < 0.01 and up_ >= REST * REST_MM2 and len(sk_wins) == len(s.joist_ys()) + 3 and hold > 0.05 and wrong > 1,
           f"skid {i + 1}: fits under the floor ({v:.4f} mm3); the floor sits on it at all {len(sk_wins)} places it crosses "
           f"(raised {REST} mm it meets each of the {len(s.joist_ys())} joists, both end bands and the front wall's band "
           f"by {up_:.3f} mm3 or more, the least at the {up_at}); held by its pegs (moved 0.3: {hold:.2f}); turned end "
           f"for end it does not fit ({wrong:.1f} mm3 into the floor)")
# the front wall rests on the deck, not on a skid: since the door moved to +1.74 ft its sill crosses the +x
# skid, and its foot stops 0.3 up in its pocket, so a sill printed a hair long can't lift the wall off the
# deck there (review Nov 3 2026). Raised 0.29 the skids still touch none of it
fw_sk = [overlap(F, k.translate([0, 0, 0.29])) for k in sk]
sill_over = [i + 1 for i, k in enumerate(sk) if overlap(F ^ s.box(-s.W, s.W, s.YF - 1, s.YF + s.WT + 1, -1, s.ZF),
                                                       k.translate([0, 0, 5])) > 1e-3]
report(max(fw_sk) < 1e-6,
       f"the front wall touches neither skid (raised 0.29: {', '.join(f'{v_:.4f}' for v_ in fw_sk)} mm3): the door sill "
       f"runs over skid {', '.join(map(str, sill_over)) or 'none'} with its foot {getattr(s, 'SILL_UP', 0.0)} up in its pocket, so only the "
       f"floor's band bears there")
mark = s.skid_mark()
peg = s.cyl_z(s.RIM / 2, s.SKID_W / 2, s.SKID_H - s.NOTCH, s.SKID_H - s.NOTCH + s.SKID_PEG_UP, s.SKID_PEG_D)
gm = mark.min_gap(peg, 5.0)
sk1 = s.skid()
report(gm >= 0.5 and overlap(sk1, mark) < 1e-6 and sk1.bounding_box()[0] < 1e-9,
       f"the skids' front end is marked, both upright corners cut off {s.SKID_MARK} mm at 45 degrees, {gm:.2f} mm clear of the "
       f"front peg")

# ================================================================ 10
group("10. plates")
pl_all = s.plates(p)
for fname, pls in pl_all.items():
    for i, (pname, items) in enumerate(pls):
        placed, fils, by_obj = [], set(), []
        for obj, parts, (x, y), *own in items:
            whole = s.union([m for _, m, _ in parts])
            bb = whole.bounding_box()
            fils |= {f for _, _, f in parts}
            mv = [x - bb[0], y - bb[1], -bb[2]]
            these = whole.translate(mv).decompose()
            placed += these
            by_obj.append((obj, parts, mv, own[0] if own else {}))
        boxes = [q.bounding_box() for q in placed]
        inside = all(b[0] >= -1e-6 and b[1] >= -1e-6 and b[3] <= BED + 1e-6 and b[4] <= BED + 1e-6 for b in boxes)
        gap = BED
        for a_, b_ in itertools.combinations(range(len(placed)), 2):
            A_, B_ = boxes[a_], boxes[b_]
            d = math.hypot(max(B_[0] - A_[3], A_[0] - B_[3], 0), max(B_[1] - A_[4], A_[1] - B_[4], 0))
            gap = min(gap, d if d >= 3 else placed[a_].min_gap(placed[b_], 3.5))
        tower = all(b[3] <= 162 + 1e-6 or b[4] <= 192 + 1e-6 for b in boxes)
        words = (f"{len(placed)} parts inside the bed, at least {gap:.1f} mm apart, " if len(placed) > 1 else
                 "1 part, inside the bed, ")
        ok = inside and gap >= 3 - 1e-6
        if fname.startswith("2") and i in (0, 2):
            # one colour change: filament 2 only in the top 0.6 of its piece, nothing in filament 1 above 5.05
            top1, ok2 = 0.0, True
            f2_walls = set()
            for obj, parts, mv, own in by_obj:
                whole = s.union([m for _, m, _ in parts])
                ztop = whole.bounding_box()[5]
                for pn, m, f in parts:
                    if f == 1:
                        top1 = max(top1, printed_top(m.bounding_box()[5]) if not m.is_empty() else 0)
                    elif f == 2:
                        f2_walls.add(obj)
                        ok2 &= m.bounding_box()[2] >= ztop - s.PROUD - 1e-6
            need = {"right side", "left side"} if i == 0 else {"front wall", "back wall", "porch gable"}
            ok = ok and tower and fils == {1, 2} and ok2 and top1 <= 5.05 + 1e-6 and need <= f2_walls
            words += (f"the prime tower's corner clear (every part at x <= 162 or y <= 192), filaments 1 and 2, filament 2 "
                      f"only in the top {s.PROUD} of its piece on {', '.join(sorted(f2_walls))}, filament 1 to "
                      f"{top1:.2f} at most: one colour change")
        elif fname.startswith("2"):
            ok = ok and len(fils) == 1
            words += f"filament {min(fils)} only, no prime tower"
            if i == 3:
                skids_ = [q for (obj, parts, mv, own) in by_obj if obj.startswith("skid")
                          for q in [s.union([m for _, m, _ in parts]).translate(mv)]]
                others_ = [s.union([m for _, m, _ in parts]).translate(mv) for (obj, parts, mv, own) in by_obj
                           if not obj.startswith("skid")]
                g_ss = skids_[0].min_gap(skids_[1], 20)
                g_so = min(k.min_gap(o, 20) for k in skids_ for o in others_)
                ok = ok and g_ss >= 10.5 and g_so >= 6.0
                words += f"; the skids {g_ss:.2f} mm apart and {g_so:.2f} from any other part, so their brims stay apart"
        else:
            ok = ok and len(fils) == 1
            words += f"filament {min(fils)} only"
        report(ok, f"{fname}, plate {i + 1} ({pname}): " + words)
# the files in the folder, the ones Alan opens, are what make_barn_cabin.py makes now: make_barn_cabin.py run as it
# is in a scratch folder (a run of its own, so its pieces are worked out in the same order and the files come out the
# same to the byte), then every .stl it makes compared byte for byte, no other .stl in the folder, and everything
# inside both .3mf files the same (the zip's own dates aside). A file left from an older run, or a run that stopped
# partway, fails here; the bridge proof below reads the modifiers from these files. (The 10x20 Cabin's checker's.)
here = s.HERE
gen = tempfile.mkdtemp(prefix="barn_cabin_gen_")
stale, made = [], []
try:
    for f_ in ("make_barn_cabin.py", "flash studio settings.json"):
        shutil.copy(os.path.join(here, f_), gen)
    import subprocess
    run = subprocess.run([sys.executable, os.path.join(gen, "make_barn_cabin.py")], cwd=gen, capture_output=True,
                         text=True)
    made = sorted(f_ for f_ in os.listdir(gen) if f_.lower().endswith((".stl", ".3mf")))
    for fname in made:
        real, new = os.path.join(here, fname), os.path.join(gen, fname)
        if not os.path.exists(real):
            stale.append(fname)
        elif fname.lower().endswith(".stl"):
            if open(real, "rb").read() != open(new, "rb").read():
                stale.append(fname)
        else:
            with zipfile.ZipFile(real) as zr, zipfile.ZipFile(new) as zn:
                if zr.namelist() != zn.namelist() or any(zr.read(m_) != zn.read(m_) for m_ in zn.namelist()):
                    stale.append(fname)
    stale += [f_ for f_ in sorted(os.listdir(here)) if f_.lower().endswith((".stl", ".3mf")) and f_ not in made]
finally:
    shutil.rmtree(gen, ignore_errors=True)
n_stl = sum(1 for f_ in made if f_.lower().endswith(".stl"))
report(run.returncode == 0 and n_stl == 18 and len(made) == 20 and not stale,
       f"the files in the folder are what make_barn_cabin.py makes now: its {n_stl} .stl files byte for byte, no other "
       f".stl or .3mf, and everything inside both .3mf files"
       + (f" (run make_barn_cabin.py: {', '.join(stale)} out of date or not made by it)" if stale else "")
       + ("" if run.returncode == 0 else f" (make_barn_cabin.py stopped: {run.stderr.strip()[-300:]})"))
# the per-object settings, read back from the written file
with zipfile.ZipFile(os.path.join(s.HERE, "2 all plates.3mf")) as z:
    cfg = z.read("Metadata/model_settings.config").decode("utf-8")
    proj = z.read("Metadata/project_settings.config")
objs = re.findall(r'<object id="\d+">(.*?)</object>', cfg, re.S)
setting = {}
for o in objs:
    nm = re.search(r'key="name" value="([^"]*)"', o).group(1)
    setting[nm] = dict(re.findall(r'<metadata key="(brim_type|brim_width)" value="([^"]*)"/>', o))
want_skid = all(setting[n] == {"brim_type": "outer_only", "brim_width": "5"} for n in setting if n.startswith("skid"))
nb = [n for n in setting if re.match(r"(corner angle|upper roof|lower roof|porch post|side railing|front railing|porch frame)", n)]
want_nb = all(setting[n].get("brim_type") == "no_brim" for n in nb) and len(nb) == 2 + 4 + 3 + 3 + 1   # 3 posts, 3 railings
rest_ = [n for n in setting if n not in nb and not n.startswith("skid") and setting[n]]
same_settings = proj == open(os.path.join(s.HERE, "flash studio settings.json"), "rb").read()
report(want_skid and want_nb and not rest_ and same_settings,
       f"2 all plates.3mf's model settings: the skids carry outer_only / 5 mm brims, the {len(nb)} angles, roof sheets, "
       f"posts, railings and porch frame no_brim, nothing else its own brim; the project settings are flash studio "
       f"settings.json byte for byte")
# which pieces carry a bridge modifier (make_barn_cabin.py, ACROSS_STUDS): the four walls and the porch gable, whose
# bays laid lengthwise are 61 mm (21 mm in the porch gable's lower panel; the front wall was, 62 mm, in a slice of Nov 3
# 2026), and the fit test's short walls, doorway and gable foot, as their real walls. On the back wall and the porch
# gable it stops on the collar tie, as over it the triangles each side of the king post are 31 mm across, and a second
# one bridges them up the gable (UP_THE_GABLE, 90), 11 mm at most. The floor carries seven (across_seams), one over
# each of its six seams, along X at 90 and along Y at 180, and one over the deck's grooves; the fit test's bits of
# floor none, their grooves are short every way. Every piece that prints lying like a wall is proven, LIKE_WALLS, and
# every piece cut from the floor, LIKE_FLOORS.
A, U, S_ = "bridges across the studs", "bridges up the gable", "bridges across the seams"
WANT_MODS = {"2 all plates.3mf": {"right side": [A], "left side": [A], "back wall": [A, U], "front wall": [A],
                                  "porch gable": [A, U], "floor": [S_] * 7},
             "1 fit test.3mf": {"short front wall": [A], "short right side": [A], "doorway": [A], "gable foot": [A]}}
LIKE_WALLS = {"2 all plates.3mf": ["right side", "left side", "back wall", "front wall", "porch gable"],
              "1 fit test.3mf": ["short front wall", "short right side", "doorway", "gable foot", "roof peg block"]}
LIKE_FLOORS = {"2 all plates.3mf": ["floor"], "1 fit test.3mf": ["deck corner", "bit of floor"]}
PL = pl_all
# the per-object settings, as written in both files: each object's own, exactly as planned (its bridge modifiers
# aside: they are parts, proven below), each part on its planned filament, and the project settings byte for byte
cfg_bad = []
for fname, pls in PL.items():
    with zipfile.ZipFile(os.path.join(s.HERE, fname)) as z:
        cfg_ = z.read("Metadata/model_settings.config").decode("utf-8")
        proj_ = z.read("Metadata/project_settings.config")
    if proj_ != open(os.path.join(s.HERE, "flash studio settings.json"), "rb").read():
        cfg_bad.append((fname, "project settings"))
    want_ = {obj: ([(pn, str(f)) for pn, _, f in parts],
                   {k: v for k, v in (own[0] if own else {}).items() if k != "modifier"})
             for _, items in pls for obj, parts, xy, *own in items}
    got_ = {}
    for oname, head_, body_ in re.findall(r'<object id="\d+"><metadata key="name" value="([^"]*)"/>'
                                          r'((?:<metadata key="[^"]*" value="[^"]*"/>)*)(.*?)</object>', cfg_):
        own_ = dict(re.findall(r'<metadata key="([^"]*)" value="([^"]*)"/>', head_))
        normal_ = [dict(re.findall(r'<metadata key="([^"]*)" value="([^"]*)"/>', pb_))
                   for pb_ in re.findall(r'<part id="\d+" subtype="normal_part">(.*?)</part>', body_)]
        first_ok = bool(normal_) and own_.pop("extruder", None) == normal_[0].get("extruder")
        got_[oname] = ([(d.get("name"), d.get("extruder")) for d in normal_ if set(d) == {"name", "extruder"}], own_)
        if not first_ok or len(got_[oname][0]) != len(normal_):
            cfg_bad.append((fname, oname, "object or part metadata"))
    if got_ != want_:
        cfg_bad.append((fname, sorted(k for k in set(got_) | set(want_) if got_.get(k) != want_.get(k))))
report(not cfg_bad,
       "in both .3mf files, as written: every object's own settings are exactly the planned ones (the skids' outer_only "
       "/ 5 mm brims, the no_brims, nothing else; the bridge modifiers are parts, below), each part on its planned "
       "filament, and the project settings are flash studio settings.json byte for byte"
       + (f" (wrong: {cfg_bad})" if cfg_bad else ""))
# the bridge direction (Nov 4 2026): the walls lie flat, framing down, so the siding's first layer (3.65 to 3.85) is a
# bridge over every stud bay, about 11 mm across between the studs and 60 mm or more along them. Flash Studio picks the
# direction itself, and not the same way every time: slices of the 10x20 Cabin laid its right side's and front wall's
# bays lengthwise, 66 mm strands, and of the Lofted Barn Cabin its front wall's, 62 mm, where other slices of the same
# files had them across. As on both garages, each wall now carries a modifier over its siding that sets bridge_angle
# (External bridge infill direction) 180, which Flash Studio reads as 0 degrees, along the bed's X: across the studs;
# where that would leave siding held at one end only it stops on framing (the 10x20 Cabin's short front wall, on the
# cripple its cut passes; the Lofted Barn Cabin's gables, on the collar tie, with a second box over it setting 90,
# along Y: up the gable). The floor prints face down, so its seams and deck-board grooves (0.4 wide, its first layer
# deep) are bridged on its second layer; Flash Studio bridged the room's seams as one, along X, in strands up to 39 mm
# along the seams that run along X, so the floor carries a box over each seam and one over the deck, on that layer
# only, setting the bridges across it. Read from the files as written: the modifiers, what they set, and each one as the solid it is
# (Flash Studio applies its shape, not its bounding box), its section at each layer; then each one's layers bridged
# the way it sets them, inside it, and what no modifier reaches, on every piece that prints lying like a wall or is cut
# from the floor, shown short every way (there the slicer picks). A wall's starts between the framing's last
# overhanging layer and the siding's first, so the layers under it (the prong legs' first layer, the plate over each
# leg's root, the door stop's ends, the loft notches) are bridged the slicer's way, as before; the floor's are over its
# first layer's middle and under its third's. The floor's seams are narrower than the 45 degree reach, so there what
# hangs free is all the layer below doesn't hold (allow 0), as the slicer finds them. Each floor box must lay its
# bridges across its groove the short way (groove_run: a box set along its seam leaves the whole groove to the slicer,
# which on a short seam is under 5 mm2 and passed), and what the boxes leave on a piece cut from the floor is measured
# patch by patch across its longest way (free_patches), not by lines held at both ends: a groove can run out into a
# hole or off an edge, where its strands are held at one end only (Nov 4 2026, a box cut 24 mm short at a prong slot
# passed as 17.2 mm). The other cabin's checker proves the same.
MOD_ANGLE = {"bridges across the studs": ("180",), "bridges up the gable": ("90",), "bridges across the seams": ("90", "180")}


def angle_set(setting):
    """The angle a modifier's setting lays its bridges at: bridge_angle as a number, or 0 where it is missing or not a
    number (each of which fails below, as anything but exactly its planned angle does), so a bad setting is a FAIL,
    not a stop."""
    try:
        a_ = float(setting.get("bridge_angle", "0"))
    except ValueError:
        return 0.0
    return a_ % 180 if math.isfinite(a_) else 0.0


lay_ = [(z0_ + z1_) / 2 for z0_, z1_ in layers(1.0)]          # the middles of the floor's first three layers
mod_bad, mod_rows = [], []
for fname, pls in PL.items():
    with zipfile.ZipFile(os.path.join(s.HERE, fname)) as z:
        cfg_ = z.read("Metadata/model_settings.config").decode("utf-8")
        model_ = z.read("3D/3dmodel.model").decode("utf-8")
    meshes = {oid_: (np.array(re.findall(r'<vertex x="([-\d.]+)" y="([-\d.]+)" z="([-\d.]+)"/>', vs_), dtype=float),
                     np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"/>', ts_), dtype=np.int64))
              for oid_, vs_, ts_ in re.findall(r'<object id="(\d+)" name="[^"]*" type="model"><mesh><vertices>(.*?)'
                                               r'</vertices><triangles>(.*?)</triangles>', model_)}
    items_ = {it_[0]: it_ for _, its_ in pls for it_ in its_}
    # every object lies on its plate unturned: its build item only moves it, and its parts carry no transform of their
    # own (the directions are the bed's, so a piece turned or mirrored on its plate would bridge another way: the
    # garages' floor review, Nov 4 2026; both garages' checkers prove the same)
    build_ = re.findall(r'<item [^>]*>', model_)
    turned_ = [i_ for i_ in build_
               if not re.fullmatch(r'<item objectid="\d+" transform="1 0 0 0 1 0 0 0 1(?: [-\d.]+){3}"/>', i_)]
    turned_ += re.findall(r'<component [^>]*transform=[^>]*>', model_)
    if turned_ or not build_:
        mod_bad.append((fname, "turned on the plate", turned_[:3]))
    for oname, head_ in re.findall(r'<object id="\d+"><metadata key="name" value="([^"]*)"/>(.*?)(?:<part|</object>)',
                                   cfg_):
        if "bridge" in head_:
            mod_bad.append((fname, oname, "an object-level bridge setting"))
    found = {}
    for oname, body_ in re.findall(r'<object id="\d+"><metadata key="name" value="([^"]*)"/>(.*?)</object>', cfg_):
        vols_ = re.findall(r'<part id="(\d+)" subtype="([a-z_]+)">(.*?)</part>', body_)
        if any("bridge" in pb_ for _, st_, pb_ in vols_ if st_ != "modifier_part"):
            mod_bad.append((fname, oname, "a part with a bridge setting"))
        mods_ = [(pid_, dict(re.findall(r'<metadata key="([^"]+)" value="([^"]*)"/>', pb_))) for pid_, st_, pb_ in vols_
                 if st_ == "modifier_part"]
        if mods_:
            found[oname] = sorted(kv_.get("name", "") for _, kv_ in mods_)
        floor_ = oname in LIKE_FLOORS[fname]
        if not mods_ and oname not in LIKE_WALLS[fname] and not floor_:
            continue
        normal_ = np.vstack([meshes[pid_][0] for pid_, st_, _ in vols_ if st_ == "normal_part"])
        lo_n, hi_n = normal_.min(axis=0), normal_.max(axis=0)
        size_ = hi_n - lo_n
        piece_ = s.on_bed(s.union([m for _, m, _ in items_[oname][1]]))
        # each modifier as the solid it is, where it lies on the piece: a closed mesh, or it fails
        solids_ = []
        for pid_, kv_ in mods_:
            v_, t_ = meshes.get(pid_, (np.zeros((0, 3)), np.zeros((0, 3), dtype=np.int64)))
            sol_ = None
            if len(v_) and len(t_):
                try:
                    sol_ = M(m3.Mesh(vert_properties=np.asarray(v_ - lo_n, dtype=np.float32),
                                     tri_verts=np.asarray(t_, dtype=np.uint32)))
                except Exception:
                    sol_ = None
            if sol_ is None or sol_.status() != m3.Error.NoError or sol_.volume() < 1e-3:
                mod_bad.append((fname, oname, kv_, "an empty modifier" if not len(v_) else "not a closed solid"))
                continue
            solids_.append((kv_, sol_))
        clash_ = max([(a_ ^ b_).volume() for (_, a_), (_, b_) in itertools.combinations(solids_, 2)] + [0.0])
        reach_ = M.batch_boolean([b_ for _, b_ in solids_], m3.OpType.Add) if solids_ else None
        words_ = []
        if floor_:
            # the floor's, on its second layer only, each laying the bridges across its seam or the deck's grooves the
            # short way: a line at its angle runs over less of the groove inside it than one at right angles (where a
            # seam along X runs into one along Y, its last SEAM_BAND is in that one's box, bridged along it there:
            # the longest such run, 2.2 mm)
            n_ang, worst_left, worst_long, worst_cross, least_along = {}, 0.0, 0.0, 0.0, None
            for kv_, sol_ in solids_:
                bb_ = sol_.bounding_box()
                setting = {k_: v_ for k_, v_ in kv_.items() if k_ != "name"}
                ang_ = angle_set(setting)
                left_, long_ = bridges_across(piece_, ang_, 0.0, region=sol_, allow=0)
                cross_, along_ = groove_run(piece_, ang_, sol_), groove_run(piece_, ang_ + 90, sol_)
                ok_ = (kv_.get("name") == "bridges across the seams" and list(setting) == ["bridge_angle"]
                       and setting["bridge_angle"] in MOD_ANGLE["bridges across the seams"]
                       and lay_[0] < bb_[2] < lay_[1] < bb_[5] < lay_[2] and left_ < 5 and long_ <= 20
                       and cross_ < along_)
                if not ok_:
                    mod_bad.append((fname, oname, kv_, "z %.3f to %.3f" % (bb_[2], bb_[5]), "%.2f mm2 left" % left_,
                                    "%.1f mm" % long_, "a line over its groove %.2f mm, at right angles %.2f"
                                    % (cross_, along_)))
                n_ang[str(setting.get("bridge_angle"))] = n_ang.get(str(setting.get("bridge_angle")), 0) + 1
                worst_left, worst_long = max(worst_left, left_), max(worst_long, long_)
                worst_cross = max(worst_cross, cross_)
                least_along = along_ if least_along is None else min(least_along, along_)
                words_.append((bb_[2], bb_[5]))
            rest_, at_ = free_patches(piece_, reach_)
            if clash_ > 1e-6 or rest_ > 20:
                mod_bad.append((fname, oname, "boxes overlap" if clash_ > 1e-6 else "",
                                "left to the slicer: a patch %.1f mm across" % rest_
                                + (" on the %.2f layer" % at_ if at_ is not None else "")))
            mod_rows.append(f"{oname}: " + (f"{len(solids_)} \"bridges across the seams\" ("
                                            + ", ".join(f"{n_} at {a_}" for a_, n_ in sorted(n_ang.items()))
                                            + f") on its second layer only (z {min(a for a, b in words_):.2f} to "
                                            f"{max(b for a, b in words_):.2f}), each across its groove the short way (a "
                                            f"line over it {worst_cross:.1f} mm at most, at right angles "
                                            f"{least_along:.1f} or more), their bridges {worst_long:.1f} mm at most "
                                            f"({worst_left:.2f} mm2 left)" if solids_ else "no modifier")
                            + f"; left to the slicer, every patch hanging free {rest_:.1f} mm across at most, every "
                              f"layer, whatever holds a strand's ends")
            continue
        # the layers that hang over anything: the framing's are under the siding's first layer, the one holding SD
        over_, prev_, zp_ = [], None, 0.0
        for z0_, z1_ in layers(piece_.bounding_box()[5]):
            zm_ = (z0_ + z1_) / 2
            cs_ = piece_.slice(zm_)
            if prev_ is not None and (cs_ - prev_.offset(1.1 * (zm_ - zp_), RND)).area() > 0.05:
                over_.append(zm_)
            prev_, zp_ = cs_, zm_
        siding_first = [(z0_ + z1_) / 2 for z0_, z1_ in layers(s.SD + 1) if z0_ < s.SD <= z1_][0]
        framing_top = max([z_ for z_ in over_ if z_ < siding_first] + [0.0])
        z_froms = []
        for kv_, sol_ in solids_:
            bb_ = sol_.bounding_box()
            z_from = bb_[2]
            z_froms.append(z_from)
            setting = {k_: v_ for k_, v_ in kv_.items() if k_ != "name"}
            ang_ = angle_set(setting)
            left_, long_ = bridges_across(piece_, ang_, z_from, region=sol_)
            ok_ = (kv_.get("name") in ("bridges across the studs", "bridges up the gable") and list(setting) == ["bridge_angle"]
                   and setting["bridge_angle"] in MOD_ANGLE[kv_.get("name")] and bb_[5] >= size_[2]
                   and framing_top < z_from < siding_first and left_ < 5 and long_ <= 20)
            if not ok_:
                mod_bad.append((fname, oname, kv_, "from z %.3f" % z_from, "top %.2f over" % (bb_[5] - size_[2]),
                                "framing to %.2f" % framing_top, "%.2f mm2 left" % left_, "%.1f mm" % long_))
            ends_ = [f"from y {bb_[1]:.2f}" if bb_[1] > 0 else "", f"to x {bb_[3]:.2f}" if bb_[3] < size_[0] else "",
                     f"to y {bb_[4]:.2f}" if bb_[4] < size_[1] else ""]
            words_.append(f"\"{kv_.get('name')}\" {setting.get('bridge_angle')} over "
                          + (" ".join(e_ for e_ in ends_ if e_) or "all of it")
                          + f", its bridges {long_:.1f} mm at most ({left_:.2f} mm2 left)")
        z_rest = min(z_froms) if z_froms else s.SIDING_BRIDGE_Z
        rest_, at_ = bridges_any_way(piece_, z_rest, reach_)
        if clash_ > 1e-6 or rest_ > 20 or not framing_top < z_rest < siding_first:
            mod_bad.append((fname, oname, "boxes overlap" if clash_ > 1e-6 else "", "left to the slicer: %.1f mm" % rest_
                            + (" on the %.2f layer at %d degrees" % at_ if at_ else "")))
        mod_rows.append(f"{oname}: " + ("; ".join(words_) if words_ else "no modifier")
                        + f", from z {z_rest:.2f} (" + (f"its framing to the {framing_top:.2f} layer" if framing_top
                                                         else "nothing overhanging under it")
                        + f", siding from the {siding_first:.2f} layer)"
                        + (f"; left to the slicer, {rest_:.1f} mm at most any way" if rest_ or not words_ else ""))
    if found != {k_: sorted(v_) for k_, v_ in WANT_MODS[fname].items()}:
        mod_bad.append((fname, "modifiers on", found))
report(not mod_bad,
       "the bridge direction, in the files as written: every piece lies on its plate unturned (its build item only "
       "moves it, its parts carry no transform of their own); the modifiers are on exactly the planned pieces, each a "
       "closed solid, read as the shape it is; the walls' over the siding only, setting External bridge infill "
       "direction across the studs (up the gable over a collar tie), the floor's over its second layer only, across "
       "each seam and the deck's grooves the short way, each setting nothing but bridge_angle, exactly as planned; "
       "their bridges laid that way are 20 mm or less, held at both ends; what no modifier reaches bridges 20 mm or "
       "less whichever way the slicer picks (on a piece cut from the floor, every patch it leaves hanging free is 20 "
       "mm or less across): " + "; ".join(mod_rows)
       + (f" (wrong: {mod_bad})" if mod_bad else ""))

# ================================================================ 11
group("11. fit test")
pj = s.porch_joint_test()


def same_section(a, b, z, region=None):
    """|area(a's section at z) - area(b's)|, both cut to region (a CrossSection) if given."""
    ca, cb = a.slice(z), b.slice(z)
    if region is not None:
        ca, cb = ca ^ region, cb ^ region
    return abs(ca.area() - cb.area()), ca.area()


sq = lambda x0, x1, y0, y1: m3.CrossSection.square([x1 - x0, y1 - y0]).translate([x0, y0])
d1, a1 = same_section(pj["deck corner"][0], fl, s.ZF - 0.5, sq(s.FIT_X0 + 0.01, s.W, -s.L, s.FIT_Y1 - 0.01))
cp_i = s.POST_XS.index(max(s.POST_XS))                  # the +x corner post
d2, a2 = same_section(pj["short post"][0], posts[cp_i], s.ZF - 0.5)
d2b, _ = same_section(pj["short post"][0].translate([0, 0, -s.FIT_DZ]), posts[cp_i], s.FRAME_Z + 0.5)
d3, a3 = same_section(pj["frame corner"][0].translate([0, 0, -s.FIT_DZ]), frame, s.FRAME_Z + 0.5,
                      sq(s.FIT_FRAME_X0 + 0.01, s.W, -s.L, s.FIT_FRAME_Y1 - 0.01))
d4, a4 = same_section(pj["gable foot"][0].translate([0, 0, -s.FIT_DZ]), gable, s.ZWT + 2,
                      sq(s.FIT_FOOT_X0 + 0.01, s.FIT_FOOT_X1 - 0.01, -s.L, s.L))
d5, a5 = same_section(pj["railing end"][0], rails[0], s.ZF + 10, sq(-s.W, s.W, -s.L, -91.52 + s.FIT_RAIL - 0.01))
fw_, sw_, fl_ = s.front_corner_test(pieces, fl)
d6, a6 = same_section(fw_, F, s.ZF + 4, sq(s.FIT_FRONT_X0 + 0.01, s.W, -s.L, s.L))
d7, a7 = same_section(fw_.translate([0, 0, (s.ZWT - 10) - (s.ZF + 8)]), F, s.ZWT - 5, sq(s.FIT_FRONT_X0 + 0.01, s.W, -s.L, s.L))
d8, a8 = same_section(sw_, p["right side"], s.ZF + 4, sq(-s.W, s.W, -s.L, s.FIT_SIDE_Y1 - 0.01))
d9, a9 = same_section(fl_, fl, s.ZF - 0.5, sq(s.FIT_FLOOR_X0 + 0.01, s.W, -60.0 + 0.01, s.FIT_FLOOR_Y1 - 0.01))
dw, (fpx, fpy), fzf = s.fit_doorway()
sh_ = s.DOOR_X0 + s.FIT_OW / 2                         # the latch jamb's offset (the left one), short doorway to real
d10, a10 = same_section(dw.translate([sh_, 0, s.ZF - fzf]), F, s.ZF + 10, sq(s.DOOR_X0 + 0.01, s.DOOR_X0 + 0.79, s.YF - 0.5, s.YF + s.WT))
d11, a11 = same_section(dw.translate([s.PIN_X - fpx, 0, s.ZF - fzf]), F, s.ZF - 0.35,
                        sq(s.PIN_X - 2.5, s.PIN_X + 2.5, s.YF + s.WT - 3, s.YF + s.WT))
worst_d = max(d1, d2, d2b, d3, d4, d5, d6, d7, d8, d9, d10, d11)
report(worst_d < 0.01 and min(a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11) > 0.5,
       f"every fit-test piece is cut from the real part: its sections match the real part's at the same place (deck corner, "
       f"post ends, frame corner, gable foot, railing end, both short walls low and high, floor, the doorway's stop and "
       f"its pin hole and trench; worst {worst_d:.4f} mm2 apart)")
worst_f, which = 0.0, ""
for nm, part in s.porch_joint_prints() + s.fit_plate_2(pieces, fl):
    w_, _ = worst_overhang(part)
    if w_ >= worst_f:
        worst_f, which = w_, nm
report(worst_f < 5, f"every fit-test piece prints with nothing steeper than 45 degrees that isn't a bridge of 20 mm or "
                    f"less, each cut along a stud ({worst_f:.2f} mm2 worst layer, on the {which})")
# and no cut leaves a strip thinner than a line: every island of every layer of every fit-test piece is a
# line (0.42) wide somewhere (check Nov 3 2026: the gable foot cut at x 41.0, 0.025 short of a siding groove,
# left a strip of siding 0.025 wide at its end, which the slicer drops)
thin_n, thin_on = 0, []
for nm, part in s.porch_joint_prints() + s.fit_plate_2(pieces, fl):
    for z0, z1 in layers(part.bounding_box()[5]):
        for isl in part.slice((z0 + z1) / 2).decompose():
            if isl.area() > 1e-9 and isl.offset(-0.21, RND).area() < 1e-6:   # (a layer over the top is empty)
                thin_n += 1
                thin_on += [] if nm in thin_on else [nm]
report(thin_n == 0, f"no fit-test piece's cut leaves a strip thinner than a line: every island of every layer is 0.42 "
                    f"wide somewhere ({thin_n} thinner{', on the ' + ', '.join(thin_on) if thin_on else ''})")
none = max(overlap(a_, b_) for a_, b_ in itertools.combinations([fw_, sw_, fl_], 2))
held = min(overlap(fw_.translate([0, 0, 0.3]), fl_), overlap(sw_.translate([0, 0, 0.3]), fl_))
gap_j = sw_.min_gap(fw_, 1.0)
cs_ = s.union([fw_, sw_]).slice(s.ZF + 4)
face = cs_ ^ sq(s.W / 2 - 0.02, s.W / 2, s.YF + s.WT - 1.5, s.YF + s.WT + 1.5)
ys_ = sorted((b.bounds()[1], b.bounds()[3]) for b in face.decompose())
gw = ys_[1][0] - ys_[0][1] if len(ys_) == 2 else -1
report(none < 0.001 and held > 0.05 and abs(gap_j - s.MITRE_GAP) < 1e-3 and 0.6 < gw < 0.8,
       f"the short front corner goes together like the real one: nothing overlaps ({none:.4f} mm3), both walls held down "
       f"(lifted 0.3: {held:.2f} mm3), the joint {gap_j:.3f} mm in the bottom of a {gw:.2f} mm groove")
deck, post_, frc, gft, rle = (pj[k][0] for k in ("deck corner", "short post", "frame corner", "gable foot", "railing end"))
pairs = [("post in the deck", post_ ^ s.box(-s.W, s.W, -s.L, s.L, -1, s.ZF), deck),
         ("post in the frame corner", post_ ^ s.box(-s.W, s.W, -s.L, s.L, s.FRAME_Z + s.FIT_DZ, 200), frc),
         ("gable foot's peg in the frame corner", gft ^ s.box(-s.W, s.W, -s.L, s.L, -1, s.ZWT + s.FIT_DZ - 0.001), frc),
         ("railing end's peg in the deck", rle ^ s.box(-s.W, s.W, -s.L, s.L, -1, s.ZF), deck)]
ok, words = True, []
for nm, a_, b_ in pairs:
    v0_ = overlap(a_, b_)
    free = max(overlap(a_.translate(t), b_) for t in ([0.34, 0, 0], [-0.34, 0, 0], [0, 0.34, 0], [0, -0.34, 0]))
    hit = min(overlap(a_.translate(t), b_) for t in ([0.4, 0, 0], [-0.4, 0, 0], [0, 0.4, 0], [0, -0.4, 0]))
    ok &= v0_ < 1e-6 and free < 1e-6 and hit > 1e-5
    words.append(f"{nm} {hit:.2f}")
# the frame corner sits on the short post's top and the gable foot on the frame corner all along it (these were
# 0.1 mm drops): lowered REST the frame corner meets the post's top, and the gable foot the frame corner's top in every
# 1 mm along it, by REST_MM2 of bearing or more
pt_b = post_.bounding_box()
on_post = rest_vols(frc, post_, [s.box(pt_b[0] - 0.5, pt_b[3] + 0.5, pt_b[1] - 0.5, pt_b[4] + 0.5, -1, 200)])[0]
gf_b = gft.bounding_box()
gf_xs = list(np.arange(gf_b[0], gf_b[3] - 0.999, 1.0))
gf_least, gf_at = least_rest(rest_vols(gft, frc, [s.box(x_, x_ + 1, -s.L, s.L, -1, 200) for x_ in gf_xs]),
                             [x_ + 0.5 for x_ in gf_xs])
seat = on_post >= REST * REST_MM2 and gf_least >= REST * REST_MM2 and len(gf_xs) >= 4
report(ok and seat, f"the porch joints seat with 0.35 round (free moved 0.34) and meet their walls moved 0.4 ("
                    f"{', '.join(words)} mm3); lowered {REST} mm the frame corner meets the short post's top "
                    f"({on_post:.3f} mm3) and the gable foot the frame corner's in each of the {len(gf_xs)} mm along it "
                    f"({gf_least:.3f} or more, at x {gf_at:.1f}; {REST * REST_MM2:.2f} needed)")
# and they stand by themselves: the frame corner sits on the one short post's top with nothing else
# under it, so its centre of mass, and with the gable foot on it theirs, must be over the post's top
# (review Nov 3 2026, as the Cabin's: cut at x 33.0 and y -84.0 as the deck it was 2.1 mm outside, 3.5
# with the gable foot on, and fell off). 0.4 mm in from every edge, more than the tenon's 0.35 play
pz_ = post_.bounding_box()[5] - s.TENON_L              # the post body's top, where the frame corner sits
ptop = (post_ ^ s.box(-s.W, s.W, -s.L, s.L, pz_ - 0.05, pz_ - 0.01)).bounding_box()
c_f, v_f = centroid(frc)
c_g, v_g = centroid(gft)
c_fg = (c_f * v_f + c_g * v_g) / (v_f + v_g)


def in_top(c):
    return min(c[0] - ptop[0], ptop[3] - c[0], c[1] - ptop[1], ptop[4] - c[1])


# every socket in the frame corner keeps 0.6 mm of frame round it, the moved peg socket too: each written
# out here from the joint sizes (the +x corner post's tenon flush with its outside face, the gable's peg
# at FIT_PEG_X against the gable's inside face), grown 0.6 each way, all of it frame or socket
frc0 = frc.translate([0, 0, -s.FIT_DZ])                # back up at the real frame's height
c_, xo, yi_ = s.TENON_CLR, s.POST_XS[cp_i] + s.POST / 2, -s.L / 2 + s.WT
fsock = [s.box(xo - s.TENON_T - c_, xo + c_, s.POST_Y - s.TENON_W / 2 - c_, s.POST_Y + s.TENON_W / 2 + c_,
               s.FRAME_Z - 1, s.FRAME_Z + s.SOCKET_D),
         s.box(s.FIT_PEG_X - s.GPEG_W / 2 - c_, s.FIT_PEG_X + s.GPEG_W / 2 + c_, yi_ - s.GPEG_T - c_, yi_ + c_,
               s.ZWT - s.GPEG_SOCKET, s.ZWT + 1)]
wall_missing = 0.0
for h in fsock:
    bb = h.bounding_box()
    g = s.box(bb[0] - 0.6, bb[3] + 0.6, bb[1] - 0.6, bb[4] + 0.6, max(bb[2] - 0.6, s.FRAME_Z), min(bb[5] + 0.6, s.ZWT - 0.4))
    wall_missing = max(wall_missing, (g - frc0 - h).volume())
# and the moved peg socket is the frame corner's only change from the real frame's corner
real_fc = frame ^ s.box(s.FIT_FRAME_X0, s.W, -s.L, s.FIT_FRAME_Y1, 0, 200)
moved_only = abs((real_fc - frc0).volume() - (real_fc ^ fsock[1]).volume()) + (frc0 - real_fc).volume()
report(in_top(c_f) >= 0.4 and in_top(c_fg) >= 0.4 and wall_missing < 1e-4 and moved_only < 0.01,
       f"the frame corner stands on the short post by itself: its centre of mass is over the post's top (x "
       f"{ptop[0]:.3f} to {ptop[3]:.3f}, y {ptop[1]:.3f} to {ptop[4]:.3f}), {in_top(c_f):.2f} mm in from the nearest edge, "
       f"and with the gable foot on it {in_top(c_fg):.2f} (0.4 needed, more than the tenon's 0.35 play); its two sockets "
       f"keep 0.6 mm of frame round them ({wall_missing:.5f} mm3 missing), and the peg socket moved to x {s.FIT_PEG_X:.1f} "
       f"is its only change from the real frame's corner ({moved_only:.4f} mm3 off)")
fd = s.fit_door()


def fit_mat(deg):
    return s.door_matrix(deg, fpx, fpy, fzf + s.DOOR_BOTTOM_GAP)


v0_ = overlap(dw, fd.transform(fit_mat(0)))
free90 = max(overlap(dw, fd.transform(fit_mat(dg))) for dg in range(0, 91, 2))
vstop = overlap(dw, fd.transform(fit_mat(-2)))
fh = s.FIT_OH - s.DOOR_BOTTOM_GAP - s.DOOR_TOP_GAP
# and it is hung the same hand as the real door: its pin the same 1.35 in from its doorway's right-hand jamb,
# its stop on the left-hand jamb, and swung 45 degrees it is in the right-hand side of its doorway
fj = s.FIT_OW / 2
fpb = (fd.transform(fit_mat(0)) ^ s.box(-s.W, s.W, -s.L, s.L, -5, fzf)).bounding_box()
fsb = (dw ^ s.box(-fj + 0.01, fj - 0.01, -s.L, s.L, fzf + 10, fzf + 11)).bounding_box()
f45 = fd.transform(fit_mat(45)).bounding_box()
real_in = s.DOOR_X1 - s.PIN_X
fit_in = fj - (fpb[0] + fpb[3]) / 2
report(abs(fit_in - real_in) < 1e-3 and abs(fsb[0] - (-fj + 0.01)) < 1e-3 and abs(fsb[3] - (-fj + 0.8)) < 1e-3
       and f45[0] > -fj + 2 and f45[4] > s.YF + s.WT + 5,
       f"the fit test's short door hangs the same hand as the real one: its pin {fit_in:.2f} mm in from its doorway's "
       f"right-hand jamb (the real one's {real_in:.2f}), its stop on the left-hand jamb (x {fsb[0] - 0.01:.2f} to "
       f"{fsb[3]:.2f}), and swung in 45 degrees it is in the right-hand side of its doorway ({f45[0] + fj:.1f} mm from the "
       f"left-hand jamb at its nearest)")


def fit_hang(d, lift):
    """The short door hung as the real one: lifted lift, its bottom swung d in, tilted about its top."""
    hh = fh + s.PIN_BOTTOM_LEN
    a = math.asin(d / hh)
    m_ = fit_mat(0)
    m_[2, 3] += lift
    c, sn = math.cos(a), math.sin(a)
    Rx = np.array([[1, 0, 0], [0, c, -sn], [0, sn, c]])
    piv = np.array([0, fpy, fzf + s.DOOR_BOTTOM_GAP + fh + lift])
    return np.column_stack([Rx @ m_[:, :3], Rx @ (m_[:, 3] - piv) + piv]), math.degrees(a)


def fit_margins(lift):
    """(the bottom pin's lowest point over the trench floor along the swing, the door's top under the
    head at the start of the swing, where it tilts most)."""
    tr = min(low.transform(fit_hang(dd, lift)[0]).bounding_box()[2] - (fzf - s.TRENCH_DEPTH)
             for dd in np.arange(2.6, -0.001, -0.25))
    top_ = (fd.transform(fit_hang(2.8, lift)[0]) ^ s.box(-s.W, s.W, fpy - 3, s.L, 0, 200) -
            s.cyl_z(fpx, fpy, 0, 200, s.PIN_HOLE_D)).bounding_box()[5]
    return tr, fzf + s.FIT_OH - top_


# the short door tilts more than the real one for the same swing, so it has less room under the head:
# pushed up until its top meets the head, how high it goes, and how high the pin must go to clear the trench
lo_, hi_ = 0.0, 1.0
for _ in range(30):
    mid = (lo_ + hi_) / 2
    lo_, hi_ = (mid, hi_) if fit_margins(mid)[1] > 0 else (lo_, mid)
lift_max = lo_
lift_min = 0.5 - fit_margins(0.5)[0]
lift_fit = (lift_min + lift_max) / 2
worst, fit_tilt = 0.0, 0.0
for d in np.arange(2.8, -0.001, -0.25):
    mt_, a_ = fit_hang(max(d, 0.0), lift_fit)
    fit_tilt = max(fit_tilt, a_)
    worst = max(worst, overlap(dw, fd.transform(mt_)))
for lift in np.arange(lift_fit, -0.001, -0.05):
    worst = max(worst, overlap(dw, fd.transform(fit_hang(0.0, lift)[0])))
m_tr, m_hd = fit_margins(lift_fit)
report(v0_ < 0.01 and free90 < 0.01 and vstop > 0.05 and worst < 0.01 and m_tr > 0.05 and m_hd > 0.05,
       f"the fit test's doorway: its door goes in by the same path, tilted {fit_tilt:.2f} degrees (pushed up until its top "
       f"meets the head it rises {lift_max:.3f}, and its bottom pin clears the trench floor from {lift_min:.3f}; hung "
       f"lifted {lift_fit:.3f}, the pin's tip {m_tr:.3f} over the trench floor and the door {m_hd:.3f} under the head, "
       f"worst overlap {worst:.4f} mm3), swings in to 90 degrees ({free90:.4f}) and meets the stop at -2 ({vstop:.2f} mm3)")
blk, cpn = s.roof_peg_test()
pegp = blk ^ s.box(-1, 30, 5.99, 20, -1, 10)                 # the peg, out past the block's edge
pc = pegp.bounding_box()
# stand the peg up and set the coupon over it: its hole goes over with 0.4 round
peg_up = s.cyl_z(0, 0, 0, s.PEG_UP, s.PEG_D, 64)
cp0 = cpn.translate([-6, -6, 0])
v_on = overlap(peg_up, cp0)
v_39 = max(overlap(peg_up, cp0.translate(t)) for t in ([0.39, 0, 0], [0, 0.39, 0], [-0.39, 0, 0]))
v_41 = min(overlap(peg_up, cp0.translate(t)) for t in ([0.41, 0, 0], [0, 0.41, 0], [-0.41, 0, 0]))
report(abs(pc[2]) < 1e-9 and v_on < 1e-9 and v_39 < 1e-9 and v_41 > 1e-6,
       f"the roof peg lies on the bed (its lowest point z {pc[2]:.2f} on the plate) and the coupon goes over it with 0.4 "
       f"round (free moved 0.39, touching 0.41)")

# ================================================================ 12
group("12. sizes at full size")
inch = 1 / s.S
floor_top = fl.bounding_box()[5]
GABLE_BOARD_IN = 5.5        # Alan's 2x6 gable board, on edge on the back wall's upper plate (his 10x16 lesson), typed in


def column(n, a, u=1.0):
    """The pieces of wall n in a 0.1 mm square column u in from its inside face (1.0: through its framing), at a along
    it, as [(bottom, top)] from the bottom up."""
    axis, sign = s.WALL_SIDE[n]
    c = sign * (s.WALL_FACE[n] - s.WT + u)
    reg = (s.box(c - 0.05, c + 0.05, a - 0.05, a + 0.05, -1, 300) if axis == 0 else
           s.box(a - 0.05, a + 0.05, c - 0.05, c + 0.05, -1, 300))
    return sorted((q.bounding_box()[2], q.bounding_box()[5]) for q in (p[n] ^ reg).decompose() if q.volume() > 1e-9)


# the walls (question 1), measured as they are on the model, not taken from WALL_H: each sliced through its framing
# 1 mm in from its inside face in the middle of a stud bay, so the bottom plate, then nothing up to the top plates (the
# long walls at y 50.8, between the marks at 44.45 and 56.555; the front wall at x -4.2, between the double at
# -10.716..-8.334 and the door's full stud at -0.095; the back wall at x 21.5, between its studs at 15.875 and 27.98 and
# its 12 and 36 in gable studs). The back wall
# carries the roof: its top plates and Alan's 2x6 gable board on them are one piece there, so its plates' top is the
# board's top less the board. The long walls and the front wall stop 0.15 mm under the roof (WALL_CUTS), so the roof
# bears on the gables only: their top plates are cut 0.15 thinner. The model's bottom plate is held at 1.6 mm for the
# snaps' legs (PLATE_BOT_MM, typed in: 2.02 in, not Alan's 1 1/2), with the top plates' underside still at his
# 76 1/2 in, so its studs are 74.48 in, the read me's 74 1/2, 0.52 in shorter than his 75; both measured here against
# the typed numbers. A long wall's stud at y 44.45 runs in one piece from its post in the floor up through both plates
gap_in = 0.15 * inch
cols = [column(n, a_) for n, a_ in (("right side", 50.8), ("left side", 50.8), ("front wall", -4.2), ("back wall", 21.5))]
stud_col = column("right side", 44.45)
whole = all(len(c_) == 2 for c_ in cols[:3]) and len(cols[3]) > 2
under = [(c_[1][0] - floor_top) * inch if len(c_) > 1 else 0.0 for c_ in cols]
tops = [(c_[1][1] - floor_top) * inch if len(c_) > 1 else 0.0 for c_ in cols]
tops[3] -= GABLE_BOARD_IN                                        # the back wall's plates' top, under the board
plates = [t - u_ for t, u_ in zip(tops, under)]
bot_in = [(c_[0][1] - c_[0][0]) * inch if c_ else 0.0 for c_ in cols]
model_stud = [u_ - (c_[0][1] - floor_top) * inch if c_ else 0.0 for u_, c_ in zip(under, cols)]
high = [(p[n].bounding_box()[5] - floor_top) * inch for n in ("right side", "left side", "front wall")]
no_higher = all(len(c_) > 1 and abs(h_ - (c_[1][1] - floor_top) * inch) < 1e-6 for h_, c_ in zip(high, cols))
under_in = ALAN["wall h"] - 2 * ALAN["plate"]                   # 76 1/2 in: the top plates' underside
want_top = [ALAN["wall h"] - gap_in] * 3 + [ALAN["wall h"]]
report(whole and no_higher and all(abs(u_ - under_in) < 0.01 for u_ in under)
       and all(abs(t - w) < 0.01 for t, w in zip(tops, want_top))
       and all(abs(c_[0][0] - floor_top) < 1e-6 and abs(b_ - PLATE_BOT_MM * inch) < 1e-6 for c_, b_ in zip(cols, bot_in))
       and all(abs(m_ - (under_in - PLATE_BOT_MM * inch)) < 0.01 for m_ in model_stud)
       and len(stud_col) == 1 and stud_col[0][0] < floor_top and abs(stud_col[0][1] - cols[0][1][1]) < 1e-6
       and abs(ALAN["stud"] + 3 * ALAN["plate"] - ALAN["wall h"]) < 1e-9,
       f"walls from the floor deck to the top of the top plates, measured: the back wall {tops[3]:.2f} in (Alan's "
       f"lofted wall, Nov 4 2026, \"Loft wall height is 79.5\"; the designer's 6.9 ft is 82.8), its plates {under[3]:.2f} "
       f"to {tops[3]:.2f} in, {plates[3]:.2f} deep, under his {GABLE_BOARD_IN} in gable board (its top {tops[3] + GABLE_BOARD_IN:.2f}). "
       f"The right side, left side and front wall {tops[0]:.2f}, {tops[1]:.2f} and {tops[2]:.2f} in, {gap_in:.2f} in "
       f"(0.15 mm) less, where they stop under the roof so it bears on the gables only: their top plates "
       f"{under[0]:.2f} to {tops[0]:.2f} in, cut to {min(plates[:3]):.2f} deep; nothing of those three walls higher "
       f"(their highest points {', '.join(f'{h_:.2f}' for h_ in high)} in). Alan's {ALAN['stud']:.0f} in studs on a "
       f"{ALAN['plate']} in bottom plate under two: the model's bottom plate is {min(bot_in):.2f} to {max(bot_in):.2f} in "
       f"({min(bot_in) / inch:.3f} to {max(bot_in) / inch:.3f} mm; {PLATE_BOT_MM} mm typed in, held for the snaps' legs), "
       f"so its studs are {min(model_stud):.2f} to {max(model_stud):.2f} in (want "
       f"{under_in - PLATE_BOT_MM * inch:.2f}), a stud running in one piece from the floor through both plates")
wall_top = floor_top + tops[3] / inch                           # the back wall's plates' top: the roof's line starts here
peak = B.bounding_box()[5]
line_peak = (peak - wall_top) * inch
truss_peak = line_peak - 0.4375 / math.cos(math.atan(s.UP_M))
report(abs(line_peak - 54.0) < 0.01 and abs(truss_peak - 53.54) < 0.01 and abs(truss_peak - 48) > 1,
       f"barn roof {line_peak:.2f} in over the top plate at the roof line, {truss_peak:.2f} in to the truss peak (BARNWRIGHT "
       f"54 / 53.54; not the Lofted Barn's 48)")
mv = np.asarray(lower.to_mesh().vert_properties)[:, :3]
eave_pt = mv[np.argmin(mv[:, 2])]
eave = (eave_pt[0] - s.W / 2) * inch
report(abs(eave - 1.77) < 0.01, f"eave {eave:.2f} in out from the siding, measured level (BARNWRIGHT 0.42 ft down the slope)")
porch_d = (F.bounding_box()[1] + s.PROUD - (-s.L / 2)) * inch
pbb = [q.bounding_box() for q in posts]
cpb = max(pbb, key=lambda b_: b_[0])                            # the +x corner post
mpb = min(pbb, key=lambda b_: abs(b_[0] + b_[3]))               # the middle post
cp_side = (s.W / 2 - (cpb[0] + cpb[3]) / 2) / s.FT
cp_front = ((cpb[1] + cpb[4]) / 2 + s.L / 2) / s.FT
mid_x = (mpb[0] + mpb[3]) / 2 * inch
rail_top = (rails[0].bounding_box()[5] - floor_top) * inch
report(abs(porch_d - 48) < 0.01 and abs(cp_side - 0.28) < 1e-3 and abs(cp_front - 0.2) < 1e-3
       and abs(mid_x - STD["middle post"] * 12) < 0.01 and len(posts) == 3 and abs(rail_top - 34.56) < 0.01,
       f"porch {porch_d:.2f} in from the front edge to the front wall's face; corner posts {cp_side:.3f} ft in from each side "
       f"and {cp_front:.3f} ft from the front, the one middle post {mid_x:+.2f} in from the middle; railing {rail_top:.2f} in "
       f"tall (BARNWRIGHT 48, 0.28, 0.2, 34.56; the middle post STD {STD['middle post'] * 12:+.1f} in)")


def wall_gaps(n, z, u0, u1, min_w):
    """The openings through wall n at height z, as (start, end) along it: the gaps longer than
    min_w between the wall's solid in a thin strip u0..u1 out from its inside face."""
    axis = s.WALL_SIDE[n][0]
    strip = s.wall_box(n, -s.BIG, s.BIG, u0, u1, z - 0.01, z + 0.01)
    ivs = sorted((q.bounding_box()[1 - axis], q.bounding_box()[4 - axis]) for q in (p[n] ^ strip).decompose()
                 if q.volume() > 1e-9)
    out, last = [], None
    for a_, b_ in ivs:
        if last is not None and a_ - last > min_w:
            out.append((last, a_))
        last = b_ if last is None else max(last, b_)
    return out


def z_gap(n, a, min_h=5.0):
    """The opening's bottom and top at a along wall n, in the same strip of siding."""
    strip = s.wall_box(n, a - 0.01, a + 0.01, s.WT - 0.08, s.WT - 0.02, -1, s.ZWT)
    ivs = sorted((q.bounding_box()[2], q.bounding_box()[5]) for q in (p[n] ^ strip).decompose() if q.volume() > 1e-9)
    gaps_ = [(b0[1], b1[0]) for b0, b1 in zip(ivs, ivs[1:]) if b1[0] - b0[1] > min_h]
    return gaps_[0] if len(gaps_) == 1 else (0.0, 0.0)


SID = (s.WT - 0.08, s.WT - 0.02)                 # just under the siding's face: grooves (0.5) are filtered out
low = {n: wall_gaps(n, s.ZF + 20, *SID, 5.0) for n in WALLS}          # under the windows: the door only
mid_ = {n: wall_gaps(n, s.ZF + 45, *SID, 5.0) for n in WALLS}         # through the windows and the door
dfr = wall_gaps("front wall", s.ZF + 20, 1.0, 1.1, 20.0)             # in the framing, under the stop's 2.45
door_c = STD["door"] * s.FT
win_c = STD["front window"] * s.FT
side_c = (STD["side middle"] + STD["side window"]) * s.FT
ok_d = (len(low["front wall"]) == 1 and len(dfr) == 1 and abs((dfr[0][0] + dfr[0][1]) / 2 - door_c) < 0.01
        and abs((dfr[0][1] - dfr[0][0]) * inch - 36) < 0.01 and abs(low["front wall"][0][1] - dfr[0][1]) < 1e-3
        and abs(low["front wall"][0][0] - (dfr[0][0] + 0.8)) < 1e-3)      # the stop on the left jamb: hinged on the right
fw_mid = [g_ for g_ in mid_["front wall"] if not (g_[0] < door_c < g_[1])]
ok_w = len(mid_["front wall"]) == 2 and len(fw_mid) == 1 and abs((fw_mid[0][0] + fw_mid[0][1]) / 2 - win_c) < 0.01
ok_s = all(len(mid_[n]) == 1 and not low[n] and abs((mid_[n][0][0] + mid_[n][0][1]) / 2 - side_c) < 0.01 for n in SIDES)
ok_b = not low["back wall"] and not mid_["back wall"]
door_z = z_gap("front wall", door_c)
wz = {n: z_gap(n, c_) for n, c_ in (("front wall", win_c), ("right side", side_c), ("left side", side_c))}
wws = [(g_[0][1] - g_[0][0]) * inch for g_ in (fw_mid, mid_["right side"], mid_["left side"]) if g_]
win_top_in = ALAN["wall h"] - 2 * ALAN["plate"] - ALAN["loft header"]         # 71 1/2, under the loft header
ok_h = (abs((door_z[1] - floor_top) * inch - ALAN["door h"]) < 0.01 and abs(door_z[0] - floor_top) < 1e-6 and len(wws) == 3
        and all(abs(w_ - 25.2) < 0.01 for w_ in wws)
        and all(abs((b_ - a_) * inch - 34.8) < 0.01 and abs((b_ - floor_top) * inch - win_top_in) < 0.01 for a_, b_ in wz.values()))
dcx = (dfr[0][0] + dfr[0][1]) / 2 if dfr else 0
wcx = (fw_mid[0][0] + fw_mid[0][1]) / 2 if fw_mid else 0
scy = [(mid_[n][0][0] + mid_[n][0][1]) / 2 if mid_[n] else 0 for n in SIDES]
report(ok_d and ok_w and ok_s and ok_b and ok_h,
       f"Alan's standard layout, measured through the walls: the door opening {(dfr[0][1] - dfr[0][0]) * inch if dfr else 0:.2f} x "
       f"{(door_z[1] - floor_top) * inch:.2f} in, its middle {dcx / s.FT:+.3f} ft from the porch wall's (STD {STD['door']:+}), the "
       f"one front window's {wcx / s.FT:+.3f} ft (STD {STD['front window']:+}); a window in each long wall, its middle "
       f"{(scy[0] - s.YM) / s.FT:+.3f} and {(scy[1] - s.YM) / s.FT:+.3f} ft from the wall's (STD 0), no door in either; nothing "
       f"through the back wall; windows {', '.join(f'{w_:.2f}' for w_ in wws)} x 34.80 in, tops {win_top_in:.2f} in up (the "
       f"designer's {ALAN['wall h'] - 5:.1f}, 5 in under the wall top: open question 3); the door {ALAN['door h']} in tall, "
       f"Alan's (Nov 4 2026, \"73 1/2 in door, flat boards\"; the builder's 6.3 ft is 75.6)")
lb0, lb1 = lofts[1].bounding_box(), lofts[0].bounding_box()
lf_f = (lb0[4] - s.YF) * inch
lf_b = (s.L / 2 - lb1[1]) * inch
faux_w_in, faux_h_in = (fb[3] - fb[0]) * inch, (fb[5] - fb[2]) * inch
faux_c = ((fb[2] + fb[5]) / 2 - s.ZWT) * inch
vent_frame = s.gable_vent(1)[0].bounding_box()
vw, vh = (vent_frame[3] - vent_frame[0]) * inch, (vent_frame[5] - vent_frame[2]) * inch
v_under = (peak - (vent_frame[2] + vent_frame[5]) / 2) * inch
bnd_in = (bnd[2] - s.ZWT) * inch
report(abs(lf_f - 48) < 0.01 and abs(lf_b - 48) < 0.01 and abs(faux_w_in - 31.2) < 0.01 and abs(faux_h_in - 22.8) < 0.01
       and abs(faux_c - 18.84) < 0.01 and abs(fb[0] + fb[3]) < 0.01
       and abs(vw - 13.44) < 0.01 and abs(vh - 9.12) < 0.01 and abs(v_under - 11.04) < 0.01 and abs(bnd_in - 21.6) < 0.01,
       f"lofts {lf_f:.2f} in from the front wall's face and {lf_b:.2f} in from the back wall's outside; faux loft window "
       f"{faux_w_in:.2f} x {faux_h_in:.2f} in, centred {faux_c:.2f} in over the wall top and {(fb[0] + fb[3]) / 2:+.3f} mm off "
       f"the middle; vents {vw:.2f} x {vh:.2f} in, "
       f"{v_under:.2f} in under the ridge; the back wall's band {bnd_in:.2f} in over the wall top (all BARNWRIGHT)")
skx = (sk[1].bounding_box()[0] + sk[1].bounding_box()[3]) / 2
sk_in = (s.W / 2 - sk[1].bounding_box()[0]) * inch
sk_c = (s.W / 2 - skx) * inch
studs = sorted(s.SIDE_MARKS)
oc = (s.SIDE_MARKS[0] - s.SIDE_MARKS[1]) * inch
js = sorted(s.joist_ys())
joc = min(b - a for a, b in zip(js, js[1:])) * inch
report(abs(sk_in - 30) < 0.01 and abs(oc - 16) < 0.01 and abs(joc - 16) < 0.01 and abs(s.SW * inch - 1.5) < 1e-9 and
       abs(s.TRIM * inch - 3.5) < 1e-9 and abs(s.ANGLE_REACH * inch - 3.78) < 0.01 and abs(s.FLAT_HEADER * inch - 3) < 1e-9
       and abs(s.HEADER * inch - 5) < 1e-9,
       f"skid inside faces {sk_in:.2f} in from the outside walls, centres {sk_c:.2f} in in (the designer's table: 30 to the "
       f"centre); studs and joists {oc:.0f} and {joc:.0f} in, studs {s.SW * inch:.1f} in wide; trim {s.TRIM * inch:.1f} in; "
       f"corner angles {s.ANGLE_REACH * inch:.2f} in on each face ({s.ANGLE_REACH} mm); door header {s.FLAT_HEADER * inch:.0f} "
       f"in, window headers {s.HEADER * inch:.0f} in")
lines = {"frame": (pp["porch frame"].bounding_box()[5], 2.85), "lip": (lb[5], 0.65),
         "post": (pp["porch post"].bounding_box()[5], 3.25), "tenon": (s.TENON_T, 1.65), "sockets": (s.SOCKET_D, 1.25),
         "railing": (s.RAIL_D, 1.25), "cap": (pp["side railing"].bounding_box()[5], 2.85),
         "ceiling": (pp["porch ceiling"].bounding_box()[5], 1.05), "peg": (s.GPEG_T, 1.65),
         "angle": (angle_flat[0][1].bounding_box()[5], 3.65), "recess": (printed_top(s.WT - s.POCKET_D), 4.65),
         "vent floor": (s.WT + s.VENT_FLOOR, 4.25), "door stop": (s.STOP_SECTION[0][1], 2.45),
         "pin holes' lowest": (holes_u, 0.25)}
bad = [k for k, (v_, e_) in lines.items() if abs(v_ - e_) > 1e-6 or abs(printed_top(v_ + 1e-9) - v_) > 1e-6]
report(not bad, "every print height is on a layer line (0.25 then 0.2): " +
       ", ".join(f"{k} {v_:.2f}" for k, (v_, e_) in lines.items()) + (f"; off: {bad}" if bad else ""))

print()
print("all checks passed" if fails == 0 else f"{fails} check(s) failed")
sys.exit(1 if fails else 0)
