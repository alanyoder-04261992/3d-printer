"""Checks the cabin model fits together before anything is printed.

Run:  python check_cabin.py          (python check_cabin.py 6 7 runs only those groups)
Each line says what it proved, with the numbers it measured. Anything that fails is marked FAIL,
and the script ends with exit code 1. The groups follow the four new models' shared order:
1 pieces and bed, 2 snap joints, 3 walls print, 4 corners, 5 gables and vents, 6 porch, 7 door,
8 roof, 9 skids, 10 plates, 11 fit test, 12 sizes at full size.
"""

import importlib
import inspect
import itertools
import math
import os
import shutil
import sys
import tempfile
import zipfile

import manifold3d as m3
import numpy as np

import make_cabin as s

M = m3.Manifold

BED = 220.0
fails = 0


def report(ok, words):
    global fails
    fails += 0 if ok else 1
    print(("ok   " if ok else "FAIL ") + words)


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


def sweep(piece, others, path):
    """The worst overlap of piece with others at each step of a path of moves."""
    return max(overlap(piece.translate(t), others) for t in path)


# ---------------------------------------------------------------- the cabin's own measuring helpers
def gap_move(a, b, d, hi=3.0, tol=1e-6):
    """How far a moves along the unit vector d before it meets b (mm3 over tol), to 0.001 mm; hi if
    it never does within hi."""
    d = np.asarray(d, dtype=float)
    if overlap(a.translate(list(d * hi)), b) <= tol:
        return hi
    lo_, hi_ = 0.0, hi
    for _ in range(14):
        mid = (lo_ + hi_) / 2
        if overlap(a.translate(list(d * mid)), b) > tol:
            hi_ = mid
        else:
            lo_ = mid
    return lo_


def cs_gap(a, b, d, hi=2.0):
    """The same for two cross-sections: how far a moves along d (2D) before it meets b."""
    if (a.translate([d[0] * hi, d[1] * hi]) ^ b).area() < 1e-9:
        return hi
    lo_, hi_ = 0.0, hi
    for _ in range(16):
        mid = (lo_ + hi_) / 2
        if (a.translate([d[0] * mid, d[1] * mid]) ^ b).area() > 1e-9:
            hi_ = mid
        else:
            lo_ = mid
    return lo_


def rect(x0, x1, y0, y1):
    return m3.CrossSection.square([x1 - x0, y1 - y0]).translate([x0, y0])


DIRS4 = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def gaps4(a, b):
    """cs_gap() of a against b in +x, -x, +y, -y."""
    return [cs_gap(a, b, d) for d in DIRS4]


def on_layer(v):
    """Is a height on a layer line of the slicer (0.25 then every 0.2)?"""
    k = (v - 0.25) / 0.2
    return v > 0 and abs(k - round(k)) < 1e-6


RUN = {int(a) for a in sys.argv[1:]} or set(range(1, 13))


def group(n, title):
    if n in RUN:
        print(f"\n{n}. {title}")
        return True
    return False


p = s.build()
body, roof, door = p["body"], p["roof"], p["door"]
fl = p["floor"]
WALLS = s.WALLS
SIDES = list(s.SIDES)
zone = s.trim_zone()
flat = {n: s.wall_parts(p, n, zone) for n in WALLS}
gable, frame, ceiling = p["porch gable"], p["porch frame"], p["porch ceiling"]
posts = {(sx, xc): s.post(sx, xc) for sx, xc in s.post_spots()}
post_set = s.union(list(posts.values()))
rails = {"side railing +x": s.side_railing(1), "side railing -x": s.side_railing(-1),
         "front railing": s.front_railing()}
rail_set = s.union(list(rails.values()))
door_shut = door.transform(s.door_to_cabin(0))
walls_set = s.union([p[n] for n in WALLS])
front = p["front wall"]
right = roof
left = roof.mirror([1, 0, 0])
roofs = s.union([right, left])
inch = 1 / s.S


def corner_name(sx, sy):
    return f"({'+' if sx > 0 else '-'},{'+' if sy > 0 else '-'})"


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


_rest = {}


def roof_rest(hn, gn):
    """How a roof half ("right" or "left") rests on a gable ("back" or "porch"), all the way along, not
    only touching it somewhere: lowered 0.02 mm, the volume it meets the gable's top by in all, the least
    in any 1 mm of the slope from the ridge out to 45 mm (past that the back wall's mitre narrows its top
    to nothing at the corner), and the x of the middle of that mm. 0.02 mm3 in a mm is 1 mm2 of bearing
    there. Worked out once and kept, so groups 6 and 8 each prove it when run on their own."""
    if (hn, gn) not in _rest:
        half, sx = (right, 1) if hn == "right" else (left, -1)
        g = p["back wall"] if gn == "back" else gable
        t = g ^ half.translate([0, 0, -0.02])
        per = [overlap(t, s.box(min(sx * x, sx * (x + 1)), max(sx * x, sx * (x + 1)), -s.L, s.L, -1, 300))
               for x in range(45)]
        _rest[(hn, gn)] = (t.volume(), min(per), sx * (per.index(min(per)) + 0.5))
    return _rest[(hn, gn)]


# the floor with room for the barbs to pass, as if each leg were bent out of the way: what is
# left in the way of a wall coming down is only the snap itself
barb_room = []
for n in WALLS:
    for ac in s.prong_spots(n):
        (a0, a1), _ = s.prong_spans(ac)
        barb_room.append(s.wall_box(n, a0 - s.FIT, a1 + s.FIT, -s.FIT, s.BARB, -1, s.ZF + 1))
fl_open = fl - s.union(barb_room)
DROPS = [0.1 * k for k in range(1, 11)] + [1 + 0.5 * k for k in range(1, 279)]   # every 0.5 mm to 140 mm


# =============================================================================================
if group(1, "pieces and bed"):
    fit_pl = s.fit_plates(p)
    plist = ([("floor", s.to_print(s.FLOOR_TO_PRINT, [fl])[0])] + [(n, s.union(flat[n])) for n in WALLS] +
             [("porch gable", s.to_print(s.WALL_TO_PRINT["porch gable"], [gable])[0]),
              ("porch frame", s.to_print(s.FRAME_TO_PRINT, [frame])[0]),
              ("porch ceiling", s.to_print(s.CEILING_TO_PRINT, [ceiling])[0]),
              ("porch post", s.to_print(s.POST_TO_PRINT, [p["post"]])[0]),
              ("side railing", s.to_print(s.SIDE_RAIL_TO_PRINT, [p["side railing"]])[0]),
              ("front railing", s.to_print(s.FRONT_RAIL_TO_PRINT, [p["front railing"]])[0]),
              ("roof half", s.roof_to_print(roof))] +
             [("corner angle " + corner_name(sx, sy), a) for (sx, sy), a in zip(s.CORNERS, s.angle_prints())] +
             [("door", s.on_bed(door)), ("skids", p["skids"])] +
             [("fit test plate %d (%s)" % (i + 1, pn), s.union([m.translate([x, y, 0]) for _, [(_, m, _)], (x, y), *_ in items]))
              for i, (pn, items) in enumerate(fit_pl)] +
             [("fit test.stl", s.union([m for _, m in s.fit_test_stl(p)]))])
    for name, part in plist:
        bb = part.bounding_box()
        size = (bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2])
        pieces = len(part.decompose())
        expect = {"skids": 2, "fit test.stl": sum(len(items) for _, items in fit_pl)}.get(name, 1)
        if name.startswith("fit test plate"):
            expect = len(fit_pl[int(name.split()[3]) - 1][1])
        report(pieces == expect, f"{name}: {pieces} solid piece(s), expected {expect}")
        report(max(size[0], size[1]) <= BED and size[2] <= BED,
               f"{name}: {size[0]:.1f} x {size[1]:.1f} x {size[2]:.2f} mm fits the {BED:.0f} mm bed whole")
    fts = [m for _, m in s.fit_test_stl(p)]
    ftb = [m.bounding_box() for m in fts]
    ft_gap = BED
    for a_, b_ in itertools.combinations(range(len(fts)), 2):
        A_, B_ = ftb[a_], ftb[b_]
        d = math.hypot(max(B_[0] - A_[3], A_[0] - B_[3], 0), max(B_[1] - A_[4], A_[1] - B_[4], 0))
        ft_gap = min(ft_gap, d if d >= 6 else fts[a_].min_gap(fts[b_], 6.5))
    report(ft_gap >= 6 - 1e-6, f"fit test.stl lays all {len(fts)} fit-test pieces on one bed, at least {ft_gap:.2f} mm "
                               f"apart (6 needed)")

    # 2. the walls and floor are the whole body, cut apart cleanly
    pieces = [fl] + [p[n] for n in WALLS]
    v = abs(body.volume() - sum(x.volume() for x in pieces))
    report(v < 0.01, f"floor and four walls add up to the whole body ({v:.4f} mm3 left over)")
    worst = max(overlap(a, b) for i, a in enumerate(pieces) for b in pieces[i + 1:])
    report(worst < 0.001, f"no two of them overlap ({worst:.4f} mm3)")
    # 3. the whole cabin put together, every part where it goes: no two parts overlap anywhere
    sk_in = [s.skid().transform(m_) for m_ in s.skids_to_cabin()]
    asm = {"floor": fl, **{n: p[n] for n in WALLS}, "door (shut)": door_shut, "porch gable": gable,
           "porch frame": frame, "porch ceiling": ceiling,
           **{f"post at x {sx * xc:+.2f}": pt for (sx, xc), pt in posts.items()}, **rails,
           **{"corner angle " + corner_name(sx, sy): s.corner_angle(sx, sy) for sx, sy in s.CORNERS},
           "right roof half": right, "left roof half": left, "skid -x": sk_in[0], "skid +x": sk_in[1]}
    asm_bb = {k: v.bounding_box() for k, v in asm.items()}
    clashes, worst, pairs = [], 0.0, 0
    for a_, b_ in itertools.combinations(list(asm), 2):
        A_, B_ = asm_bb[a_], asm_bb[b_]
        if any(A_[i] > B_[i + 3] or B_[i] > A_[i + 3] for i in range(3)):
            continue
        pairs += 1
        v = overlap(asm[a_], asm[b_])
        worst = max(worst, v)
        if v >= 1e-4:
            clashes.append(f"{a_} into {b_} {v:.4f} mm3")
    report(not clashes, f"the whole cabin put together ({len(asm)} parts: floor, walls, door shut, porch gable, frame, "
                        f"ceiling, posts, railings, corner angles, roof halves, skids): no two overlap ({pairs} pairs "
                        f"near each other, worst {worst:.6f} mm3, 0.0001 allowed)"
                        + (": " + "; ".join(clashes) if clashes else ""))
    v = 0
    for dx, dy in ((0.14, 0), (-0.14, 0), (0, 0.14), (0, -0.14)):
        v = max(v, overlap(fl.translate([dx, dy, 0]), walls_set))
    report(v < 0.0001, f"the walls sit round the floor with {s.FIT} mm round every post, prong and end block and "
                       f"{s.FLOOR_CLR} mm inside the skirts (moved 0.14 mm it still clears: {v:.4f} mm3)")
    # the front wall's closed pockets, measured on a section through them: 0.3 along the wall, 0.2
    # across, and the end blocks 0.2 in their open corner notches
    z = 3.0
    fcs, wcs = fl.slice(z), front.slice(z)
    worst_along, worst_across, n_p = 9.0, 9.0, 0
    for a0, a1 in s.post_spans("front wall"):
        post_cs = wcs ^ rect(a0 - 0.1, a1 + 0.1, s.YF - 1, s.YF + s.WT + 1)
        g = gaps4(post_cs, fcs ^ rect(a0 - 3, a1 + 3, s.YF - 4, s.YF + s.WT + 4))
        worst_along, worst_across = min(worst_along, g[0], g[1]), min(worst_across, g[2], g[3])
        okp = abs(g[0] - s.POCKET_ALONG) < 0.005 and abs(g[1] - s.POCKET_ALONG) < 0.005 and \
            abs(g[2] - s.FIT) < 0.005 and abs(g[3] - s.FIT) < 0.005
        n_p += okp
    n_fp = len(s.post_spans("front wall"))
    report(n_p == n_fp,
           f"the front wall's {n_fp - 1} posts and its door sill sit in closed pockets {worst_along:.3f} mm clear along "
           f"the wall and {worst_across:.3f} across ({n_p} of the {n_fp} pockets exactly so)")
    # the floor round those pockets, measured: solid from the bottom up to the seams and board grooves
    # (0.25 under the top) for 0.6 past each end, and for how far either side across the wall before
    # the joist cavities (spec 4.11: the band y -59.150..-50.046 leaves 1.8 each side)
    thick, ends_missing = [], 0.0
    for a0, a1 in s.post_spans("front wall"):
        e0, e1 = a0 - s.POCKET_ALONG - 0.6, a1 + s.POCKET_ALONG + 0.6
        for side in (-1, 1):
            def missing(g):
                u0, u1 = (-s.FIT - g, -s.FIT) if side < 0 else (s.WT + s.FIT, s.WT + s.FIT + g)
                return (s.wall_box("front wall", e0, e1, u0, u1, 0, s.ZF - 0.25) - fl).volume()
            lo_, hi_ = 0.0, 3.0
            if missing(hi_) < 1e-4:
                lo_ = hi_
            else:
                for _ in range(14):
                    mid = (lo_ + hi_) / 2
                    lo_, hi_ = (mid, hi_) if missing(mid) < 1e-4 else (lo_, mid)
            thick.append(lo_)
        pocket = s.wall_box("front wall", a0 - s.POCKET_ALONG, a1 + s.POCKET_ALONG, -s.FIT, s.WT + s.FIT, 0, s.ZF - 0.25)
        ends = s.wall_box("front wall", e0, e1, -s.FIT, s.WT + s.FIT, 0, s.ZF - 0.25) - pocket
        ends_missing = max(ends_missing, (ends - fl).volume())
    report(min(thick) >= 1.8 - 0.005 and ends_missing < 1e-4,
           f"round each of those {n_fp} pockets the floor is solid 0.6 mm past its ends ({ends_missing:.5f} mm3 missing) "
           f"and {min(thick):.3f} to {max(thick):.3f} mm either side across the wall to the joist cavities (1.8 needed), "
           f"up to the top's seams and grooves")
    eg = []
    for sx in (1, -1):
        blk = wcs ^ rect(-s.W, s.W, s.YF - 1, s.YF + s.WT + 1) ^ (rect(42, 48, -60, -50) if sx > 0 else rect(-48, -42, -60, -50))
        g = gaps4(blk, fcs)
        eg += [g[1] if sx > 0 else g[0], g[3]]
    report(all(abs(g - s.FIT) < 0.005 for g in eg),
           f"each end block goes down through its corner notch {min(eg):.3f} to {max(eg):.3f} mm clear on the inside and "
           f"the front (open on the outside)")


# =============================================================================================
if group(2, "snap joints"):
    back, frontd = p["back wall"], s.union([front, door_shut])
    order = [("back wall", back, fl_open, "onto the bare floor"),
             ("front wall", frontd, s.union([fl_open, back]), "with its door hung in it, shut"),
             ("right side", p["right side"], s.union([fl_open, back, frontd]), "between the back wall and front wall"),
             ("left side", p["left side"], s.union([fl_open, back, frontd, p["right side"]]),
              "between the back wall and front wall")]
    for n, w, others, words in order:
        v = overlap(p[n].translate([0, 0, -0.1]), fl)
        report(v > 1, f"{n} stands on the floor (lowered 0.1 mm it runs into it: {v:.1f} mm3)")
        v = overlap(p[n].translate([0, 0, 0.3]), fl)
        report(v > 0.05, f"{n}: its {len(s.prong_spots(n))} prongs' barbs hold it down (lifted 0.3 mm they meet "
                         f"their ledges: {v:.2f} mm3)")
        vi, vo = overlap(p[n].translate(toward(n, -0.3)), fl), overlap(p[n].translate(toward(n, 0.3)), fl)
        va = min(overlap(p[n].translate(along(n, d)), fl) for d in (0.3, -0.3))
        report(min(vi, vo, va) > 0.05, f"{n}: the floor holds its foot in ({vi:.1f}), out ({vo:.1f}) and along "
                                       f"({va:.1f} mm3 when moved 0.3 mm)")
        worst = sweep(w, others, [[0, 0, dz] for dz in DROPS])
        report(worst < 0.001, f"{n} goes on straight down from 140 mm, {words}, nothing in the way but its barbs "
                              f"({worst:.4f} mm3)")
    leg = s.LEG_ROOT - (s.LEDGE_Z - s.FIT)
    strain = 1.5 * s.PRONG_T * s.CATCH / leg ** 2
    room = s.SLOT_U - (s.BARB + s.PRONG_T + s.CATCH)
    report(strain < 0.02 and room >= 0.25 - 0.001,
           f"each prong leg bends {s.CATCH:.2f} mm to let its barb through: {strain * 100:.1f}% strain on a {leg:.2f} mm "
           f"leg {s.PRONG_T} mm thick (PLA takes about 2%), with {room:.2f} mm to spare in its slot")
    # the same snap as it will print: walls lying inside face down and the floor upside down
    for n in WALLS:
        region = s.union([s.wall_box(n, min(s.prong_spans(ac)[0][0], s.prong_spans(ac)[1][0]) - 1,
                                     max(s.prong_spans(ac)[0][1], s.prong_spans(ac)[1][1]) + 1, -1, s.SD, -1, s.ZF + 1)
                          for ac in s.prong_spots(n)])
        pw = printed_in_shed(p[n], s.WALL_TO_PRINT[n], region)
        pf = printed_in_shed(fl, s.FLOOR_TO_PRINT, region)
        rest = overlap(pw, pf)
        held = overlap(pw.translate([0, 0, 0.3]), pf)
        (a0, a1), _ = s.prong_spans(s.prong_spots(n)[-1])

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
               f"{n} as printed: each barb reaches {catch:.2f} mm under its ledge ({out_catch:.2f} with the foot pushed "
               f"out against its stops), with {ledge - top:.2f} mm over it to spring in; lifted 0.3 mm the printed barbs "
               f"catch ({held:.2f} mm3), and seated nothing rubs ({rest:.3f} mm3)")

    # 4. floor left between neighbouring pockets and slots along each wall, measured on the floor itself:
    # a line along the wall 1.0 mm out from its inside face (through every post's pocket and every
    # prong's slot) at z 3.0 (over the ledges, under the deck). From the numbers, every pocket and slot
    # is a cut of its own (a post's notch may lie wholly inside a corner notch; a prong's leg and stop
    # slots are one) and no prong slot runs into a post's pocket. Then prong slots clear of the skids
    # and between the joists.
    expect_least = {"front wall": 0.930, "back wall": 1.030, "right side": 2.255, "left side": 2.255}
    sk_spans = [(sx * s.SKID_X - s.SKID_W / 2, sx * s.SKID_X + s.SKID_W / 2) for sx in (1, -1)]
    joists = [(j - s.SW / 2, j + s.SW / 2) for j in s.joist_ys()]
    fl3 = fl.slice(3.0)
    for n in WALLS:
        alongc = s.POCKET_ALONG if n == "front wall" else s.FIT
        post_sp = [(a0 - alongc, a1 + alongc) for a0, a1 in s.post_spans(n)]
        slots = []
        for ac in s.prong_spots(n):
            (a0, a1), (b0, b1) = s.prong_spans(ac)
            slots.append((min(a0, b0) - s.FIT, max(a1, b1) + s.FIT))
        clash = [(sl, sp) for sl in slots for sp in post_sp if min(sl[1], sp[1]) > max(sl[0], sp[0]) - 1e-9]
        spans = post_sp + slots
        if n == "front wall":
            spans += [(-s.W, -(s.W / 2 - s.WT - s.FIT)), (s.W / 2 - s.WT - s.FIT, s.W)]
            run = (-s.W / 2, s.W / 2)
        elif n in SIDES:
            spans += [(-s.W * 3, s.YJ0 + s.SW + s.FIT), (s.L / 2 - s.WT - s.SW - s.FIT, s.W * 3)]
            run = (s.YF, s.L / 2)
        else:
            spans += [(-s.W, -(s.W / 2 - s.WT - s.SW - s.FIT)), (s.W / 2 - s.WT - s.SW - s.FIT, s.W)]
            run = (-s.W / 2, s.W / 2)
        spans.sort()
        merged = [list(spans[0])]                      # only a span wholly inside another joins it
        for a, b in spans[1:]:
            m0, m1 = merged[-1]
            if a >= m0 - 1e-9 and b <= m1 + 1e-9:
                continue
            if a <= m0 + 1e-9 and b >= m1 - 1e-9:
                merged[-1] = [a, b]
                continue
            merged.append([a, b])
        least = min(b[0] - a[1] for a, b in zip(merged, merged[1:]))
        # measured: the floor's pieces along the line, within the wall's run
        axis, sign = s.WALL_SIDE[n]
        c_line = sign * (s.WALL_FACE[n] - s.WT + 1.0)
        if axis == 0:                                  # a side wall: the line x = c_line, along y
            got = [(-x1, -x0) for x0, x1 in scan(fl3.rotate(90), [c_line])[0]]
        else:
            got = [tuple(iv) for iv in scan(fl3, [c_line])[0]]
        got = sorted(iv for iv in got if iv[0] >= run[0] - 1e-6 and iv[1] <= run[1] + 1e-6)
        m_least = min(b - a for a, b in got)
        cuts_seen, cuts_meant = len(got) - 1, len(merged) - 2
        report(not clash and cuts_seen == cuts_meant and m_least >= 0.6 and abs(m_least - least) < 0.005
               and abs(m_least - expect_least[n]) < 0.002,
               f"{n}: measured along the floor, at least {m_least:.3f} mm of floor between neighbouring pockets and "
               f"slots (0.6 needed; {expect_least[n]} expected, {least:.3f} from the numbers); {cuts_seen} separate cuts "
               f"along it, {cuts_meant} meant" + (f"; a prong slot runs into a post's pocket at {clash}" if clash else
                                                 ", no prong slot running into a post's pocket"))
        if n in SIDES:
            jg = min(max(j0 - b1, a0 - j1) for a0, b1 in slots for j0, j1 in joists)
            sk = min(s.W / 2 - s.WT - abs(sx * s.SKID_X) - s.SKID_W / 2 for sx in (1,))
            report(jg > 0.5, f"{n}: its prong slots are between the floor joists ({jg:.2f} mm from the nearest) and "
                             f"{sk:.1f} mm from the skids")
        else:
            sk = min(max(k0 - b1, a0 - k1) for a0, b1 in slots for k0, k1 in sk_spans)
            band = (s.L / 2 - s.TS - s.FLOOR_CLR - s.RIM, s.L / 2 - s.TS - s.FLOOR_CLR) if n == "back wall" else \
                (s.YF - s.BAND, s.YF + s.WT + s.BAND)
            yslot = sorted([s.WALL_SIDE[n][1] * (s.WALL_FACE[n] - s.WT + u) for u in (-s.FIT, s.SLOT_U)])
            inband = band[0] < yslot[0] and yslot[1] < band[1]
            report(sk >= 1.0 and inband, f"{n}: its prong slots are {sk:.2f} mm from the nearest skid (1.0 needed) and "
                                         f"inside the floor's solid band ({yslot[0]:.2f} to {yslot[1]:.2f} in "
                                         f"{band[0]:.2f} to {band[1]:.2f})")
    # 5. the prongs against Alan's standard layout: none under the moved door or its sill (the only
    # opening that reaches the floor), and each in a stud bay, clear along the wall of every stud,
    # king, full stud, cripple and end member standing on the bottom plate over it
    door_a = (s.DOOR_X - s.JAMB - 2 * s.SW, s.DOOR_X + s.JAMB + 2 * s.SW)
    for n in WALLS:
        if n == "back wall":
            standing = [(xc - s.SW / 2, xc + s.SW / 2) for xc, _, _ in s.gable_plan(n)[0]]
        else:
            standing = [(a0, a1) for a0, a1, z0, _, what in s.framing_plan(n)[0]
                        if what not in ("bottom plate", "top plates", "header", "rough sill") and z0 < s.ZF + s.PLATE_BOT + 0.01]
        standing += [(a0, a1) for a0, a1, _ in s.end_members(n)]
        clear, under_door = 99.0, []
        for ac in s.prong_spots(n):
            (a0, a1), (b0, b1) = s.prong_spans(ac)
            lo_, hi_ = min(a0, b0), max(a1, b1)
            clear = min([clear] + [max(m0 - hi_, lo_ - m1) for m0, m1 in standing])
            if n == "front wall" and min(hi_, door_a[1]) > max(lo_, door_a[0]) - s.POCKET_ALONG - s.FIT:
                under_door.append(ac)
        report(clear > 0.05 and not under_door,
               f"{n}: each of its {len(s.prong_spots(n))} prongs (leg and stop) stands in a stud bay, at least {clear:.2f} mm "
               f"along the wall from the nearest member standing on the bottom plate"
               + (f"; none under the door or its sill (x {door_a[0]:.3f} to {door_a[1]:.3f}, the +x prong moved to "
                  f"{max(s.prong_spots(n)):.3f})" if n == "front wall" else "")
               + (f"; UNDER THE DOOR at {under_door}" if under_door else ""))


# =============================================================================================
if group(3, "walls print"):
    for n in WALLS:
        siding, trim = flat[n]
        whole = s.union(flat[n])
        bb = whole.bounding_box()
        foot = whole.trim_by_plane([0, 0, -1], -0.2)
        fbb = foot.bounding_box()
        report(fbb[3] - fbb[0] > (bb[3] - bb[0]) - 2 * (s.WT + s.PROUD) - 0.1 and fbb[4] - fbb[1] > 0.9 * (bb[4] - bb[1]),
               f"{n} lies flat on its framing ({foot.volume() / 0.2:.0f} mm2 on the bed)")
        worst, longest, prev = 0.0, 0.0, None
        for z0, z1 in layers(bb[5]):
            cs = whole.slice((z0 + z1) / 2)
            if prev is not None:
                left_, span = overhangs(cs, prev)
                longest = max(longest, span)
                worst = max(worst, left_.area())
            prev = cs
        report(worst < 5, f"{n} has nothing steeper than 45 degrees that isn't a bridge of 20 mm or less ({worst:.2f} "
                          f"mm2 worst layer, longest bridge {longest:.1f} mm)")
        thin = max((c - c.offset(-0.2, RND).offset(0.2, RND)).area() for c in (whole.slice(0.125), whole.slice(0.35)))
        report(thin < 2, f"{n}: no knife edges on the bed ({thin:.2f} mm2 thinner than a line in the first two layers)")
        tb, sb = trim.bounding_box(), siding.bounding_box()
        # every wall has trim now: both side walls carry a window casing (Alan's standard layout)
        report(not trim.is_empty() and abs(tb[5] - (s.WT + s.PROUD)) < 0.01 and tb[2] > s.WT - 0.01,
               f"{n}: trim is {trim.volume() / 1000:.3f} cm3, all of it the top {s.PROUD} mm ({tb[2]:.3f} to "
               f"{tb[5]:.3f} mm), so the colour only changes on the last layers")
        report(sb[5] <= s.WT + 1e-6, f"{n}: nothing in filament 1 stands above the siding's face ({sb[5]:.3f} mm; its "
                                     f"top layer prints at 5.05)")
        if n != "back wall":
            v = p[n].trim_by_plane([0, 0, 1], s.ZWT + 0.001).volume()
            report(v == 0, f"{n}: nothing above the wall plates (the gable corners go with the back wall)")
    # the trim parts are really there: count and volume against the drawn boards' proud part
    T, P = s.TRIM, s.PROUD

    def frame_area(w, h, door=False):
        return (w + 2 * T) * (h + (1 if door else 2) * T) - w * h
    ra = s.angle_reach()[0] + s.POCKET_CLR
    expect = {"front wall": (2, P * (frame_area(s.DOOR_OPEN_W, s.DOOR_OPEN_H, True) + frame_area(s.WIN_W, s.WIN_H))),
              "right side": (1, P * frame_area(s.WIN_W, s.WIN_H)),
              "left side": (1, P * frame_area(s.WIN_W, s.WIN_H)),
              "back wall": (1, P * (s.W - 2 * ra) * T)}
    for n, (cnt, vol) in expect.items():
        tr = s.two_colour(p[n], zone)[1]
        k = len(tr.decompose())
        report(k == cnt and abs(tr.volume() - vol) < 0.01 * vol,
               f"{n}: its filament-2 part is {k} piece(s) ({cnt} expected), {tr.volume():.1f} mm3 against the drawn "
               f"boards' {vol:.1f} mm3 proud of the face")
    vband = s.union(s.trims()) ^ s.box(-s.W, s.W, -s.L, -s.L / 2 + 1, -1, 400)
    report(vband.is_empty(), "trims() makes no gable band at the porch end (y = -L/2)")
    # Alan's standard layout (Nov 3 2026 addendum): each side wall's window drops the marks 16 in either
    # side of its middle onto its full studs; on the front wall the mark 44 in left of the middle lands
    # on the window's -x king stud (the old -28 and +20 drops are gone with the old openings); the
    # back wall's is unchanged. Worked out by hand from the openings: mark -34.925 (stud -35.520..
    # -34.330) on the king -35.671..-34.481, 1.040 mm
    spec_drops = {("right side", -16.0): (0.278, "full stud"), ("right side", 16.0): (0.278, "full stud"),
                  ("left side", -16.0): (0.278, "full stud"), ("left side", 16.0): (0.278, "full stud"),
                  ("front wall", -44.0): (1.040, "king stud"),
                  ("back wall", -52.0): (0.54, "end stud")}
    got = {(w, m): (ov, what) for w, m, what, ov in s.DROPPED_MARKS}
    same = set(got) == set(spec_drops) and all(abs(got[k][0] - spec_drops[k][0]) < 0.005 and spec_drops[k][1] in got[k][1]
                                               for k in got)
    for w, m, what, ov in s.DROPPED_MARKS:
        print(f"     dropped layout mark: {w}, {m:+.0f} in from its middle, on {what}, {ov:.3f} mm ({ov * inch:.2f} in)")
    report(same, f"DROPPED_MARKS is exactly the standard layout's six ({len(got)} listed)")
    # nothing in an opening: no framing member of a wall overlaps any of its openings (from the
    # numbers), and measured on the walls, nothing but the window sashes inside a window and nothing
    # but the latch-side stop inside the doorway, right through the wall
    in_op, n_op, sash_left, door_left, sash_gone, sash_vols = [], 0, 0.0, 0.0, 0.0, []
    for n in ["front wall"] + SIDES:
        ops = s.openings(n)
        n_op += len(ops)
        for a0, a1, z0, z1, what in s.framing_plan(n)[0]:
            for o0, o1, oz0, oz1, _ in ops:
                if what == "bottom plate" and oz0 < s.ZF + 1:
                    continue                    # cut across the doorway (F8); the measurement below proves it
                if min(a1, o1) - max(a0, o0) > 1e-6 and min(z1, oz1) - max(z0, oz0) > 1e-6:
                    in_op.append((n, what, round(a0, 3)))
        for o0, o1, oz0, oz1, _ in ops:
            hole = s.wall_box(n, o0 + 0.01, o1 - 0.01, -1, s.WT + 1, oz0 + 0.01, oz1 - 0.01)
            if oz0 < s.ZF + 1:  # all but the stop's 0.8 on the latch jamb, the left one (hinged on the right, Nov 4 2026)
                hole = s.wall_box(n, o0 + 0.8 + 0.01, o1 - 0.01, -1, s.WT + 1, oz0 + 0.01, oz1 - 0.01)
                door_left = max(door_left, (hole ^ p[n]).volume())
            else:
                sash = s.union(s.window_unit(n, (o0 + o1) / 2, oz0, oz1))
                sash_left = max(sash_left, ((hole ^ p[n]) - sash).volume())
                # and the whole sash is there: none of it missing from the wall, and a real sash's worth
                # of it in the opening (two sashes and their muntins are about 930 mm3; none at all would
                # also leave nothing else in the opening)
                sash_gone = max(sash_gone, ((sash ^ hole) - p[n]).volume())
                sash_vols.append((hole ^ p[n]).volume())
    report(not in_op and n_op == 4 and sash_left < 1e-4 and door_left < 1e-6 and sash_gone < 1e-4
           and len(sash_vols) == 3 and min(sash_vols) > 900,
           f"nothing in an opening: no stud, king, cripple, header, sill or plate overlaps any of the {n_op} openings "
           f"(the door and three windows) in the framing numbers" + (f" ({in_op})" if in_op else "")
           + f"; measured right through each wall, the windows hold only their sashes ({sash_left:.5f} mm3 else) and "
           f"the doorway nothing but its stop ({door_left:.6f} mm3); each window has its whole sash in it "
           f"({sash_gone:.5f} mm3 of sash missing; {', '.join(f'{v:.0f}' for v in sash_vols)} mm3 in the three "
           f"openings, more than 900)")
    # the floor prints face down, nothing hanging over
    ff = s.to_print(s.FLOOR_TO_PRINT, [fl])[0]
    fbb = ff.bounding_box()
    foot = ff.slice(0.125).area()
    report(foot > 0.9 * (fbb[3] - fbb[0]) * (fbb[4] - fbb[1]) - 400, f"the floor prints face down ({foot:.0f} mm2 on the bed)")
    # the post sockets and railing peg holes open on its face, so their ends are short bridges
    worst, longest = worst_overhang(ff)
    report(worst < 0.5, f"the floor has nothing hanging over that isn't a bridge of 20 mm or less ({worst:.2f} mm2 worst "
                        f"layer; the longest bridge, over a socket or a cavity, {longest:.1f} mm)")
    # its first two layers are the deck and floor face: nothing there narrower than a line (a strip
    # between a board groove and a hole, or a pinch where two cuts meet corner to corner). Rounding a
    # square corner off takes a little bit on its own; anything bigger is two cuts too close.
    def thin_bits(c):
        return [q.area() for q in (c - c.offset(-0.21, RND).offset(0.21, RND)).decompose()]
    lone = max(thin_bits(rect(0, 5, 0, 5)))
    bits = thin_bits(ff.slice(0.125)) + thin_bits(ff.slice(0.35))
    report(max(bits) <= 1.2 * lone,
           f"the floor's first two layers (the deck and floor face) have nothing narrower than a line but the rounding of "
           f"single square corners (largest bit {max(bits):.4f} mm2, a lone corner's {lone:.4f}; a strip between a board "
           f"groove and a hole was 0.54)")


# =============================================================================================
def to_corner(sx, sy):
    """Matrix from cabin coords to a corner's own (u, v, z): u out from the side wall's siding
    face, v out from the back wall's (the inverse of make_cabin.corner_frame)."""
    return np.array([[sx, 0, 0, -s.W / 2], [0, sy, 0, -s.L / 2], [0, 0, 1, 0]], dtype=float)


def square(u0, u1, v0, v1):
    return m3.CrossSection.square([u1 - u0, v1 - v0]).translate([u0, v0])


RA, RB = s.angle_reach()
C0 = s.POCKET_D + s.CORNER_CHAMFER           # 1.55: where each recess floor starts, from the corner
C1 = RA + s.POCKET_CLR                       # 3.15: where it ends
FLOOR_WIN = (-(C1 - 0.1), -(C0 + 0.15))      # [-3.05, -1.70]
ANGLE_WIN = (-(RA - 0.1), -(C0 + 0.15))      # [-2.90, -1.70]


def reach_area(a, wall_set, sx, sy, zs, r):
    """Area of wall within r of the angle, on horizontal sections at zs, leaving out the strips
    under the angle's inside faces, which sit on the recess floors by design."""
    floors = square(-s.POCKET_D - r - 0.01, -s.POCKET_D, -RA - r - 0.01, -C0 + 0.25) + \
        square(-RB - r - 0.01, -C0 + 0.25, -s.POCKET_D - r - 0.01, -s.POCKET_D)
    T = to_corner(sx, sy)
    at, wt = a.transform(T), wall_set.transform(T)
    return max(((at.slice(z).offset(r, RND) ^ wt.slice(z)) - floors).area() for z in zs)


def directions(d):
    out = []
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            for k in (-1, 0, 1):
                if i or j or k:
                    n = math.sqrt(i * i + j * j + k * k)
                    out.append([d * i / n, d * j / n, d * k / n])
    return out


if group(4, "corners"):
    angles = {c: s.corner_angle(*c) for c in s.CORNERS}
    trim_all = s.union(s.trims())
    zs = (1.0, s.ZF, 40.0, 70.0, s.ZWT - 1, s.ZWT + 1)
    for (sx, sy), a in angles.items():
        cn = corner_name(sx, sy)
        ln, en = s.corner_walls(sx, sy)
        lw_, ew_ = p[ln], p[en]
        pair = s.union([lw_, ew_])
        v0 = max(overlap(a, lw_), overlap(a, ew_))
        in_l = a.translate([-sx * 0.005, 0, 0]) ^ lw_
        in_e = a.translate([0, -sy * 0.005, 0]) ^ ew_
        T = to_corner(sx, sy)
        wl = in_l.transform(T).bounding_box()
        we = in_e.transform(T).bounding_box()
        cw_l, cw_e = wl[4] - wl[1], we[3] - we[0]
        report(v0 < 0.001 and in_l.volume() > 0.3 and in_e.volume() > 0.3 and cw_l >= 1.40 and cw_e >= 1.40,
               f"corner angle {cn} sits in the recesses of the {ln} and {en}: into neither ({v0:.4f} mm3), on both recess "
               f"floors, its contact {cw_l:.3f} mm wide on the {ln} and {cw_e:.3f} on the {en} (1.40 needed, 1.45 expected)")
        c = (s.CORNER_CHAMFER - s.ANGLE_FILLET) / math.sqrt(2)
        near = reach_area(a, pair, sx, sy, zs, 0.09)
        fil = reach_area(a, pair, sx, sy, zs, c + 0.02)
        report(c >= 0.09 and near < 1e-4 and fil > 0.001,
               f"corner angle {cn} touches the walls only on the recess floors: nothing else within 0.09 mm ({near:.5f} "
               f"mm2; the fillet is {c:.3f} mm off the chamfer, and at {c + 0.02:.3f} it reaches it, {fil:.3f} mm2)")
        worst = 0.0
        for n, other in ((ln, ew_), (en, lw_)):
            for d in (0.15, -0.15):
                worst = max(worst, overlap(a.translate(toward(n, d)), other))
        t_in = s.POCKET_CLR + 0.1
        tight = overlap(a.translate(toward(ln, -t_in)), ew_)
        report(worst < 0.001 and tight > 0.001,
               f"corner angle {cn} still misses the other wall with either wall's foot 0.15 mm in or out ({worst:.4f} "
               f"mm3; at {t_in:.2f} mm in it would meet it, {tight:.3f} mm3)")
        at = a.transform(T)
        cover_l, cover_e = 99.0, 99.0
        for z in (0.3, s.ZF, 50.0, s.ZWT - 0.6):
            sec = at.slice(z)
            lp, ep = sec ^ square(-s.POCKET_D, 1, -30, 1), sec ^ square(-30, 1, -s.POCKET_D, 1)
            cover_l = min(cover_l, -lp.bounds()[1] if lp.area() > 0 else 0)
            cover_e = min(cover_e, -ep.bounds()[0] if ep.area() > 0 else 0)
        face = (at ^ s.box(s.ANGLE_T - s.POCKET_D - 0.01, 1, -30, 1, -1, 400)).bounding_box()
        report(cover_l >= 2.95 and cover_e >= 2.95 and at.bounding_box()[2] == 0,
               f"corner angle {cn} covers {cover_l:.2f} mm of the {ln}'s face and {cover_e:.2f} mm of the {en}'s from the "
               f"siding's outer corner (2.95 needed), from its foot (level with the bottom of the skirts) to "
               f"{s.ZWT - face[5]:.2f} mm under the top of the wall plates")
        rf = right if sx > 0 else left
        nrm = [sx * math.sin(s.ALPHA), 0, math.cos(s.ALPHA)]
        v19 = overlap(a, rf.translate([-0.19 * q for q in nrm]))
        v21 = overlap(a, rf.translate([-0.21 * q for q in nrm]))
        vlow = overlap(a, rf.translate([0, 0, -0.15]))
        report(overlap(a, rf) == 0 and v19 < 1e-5 and vlow < 1e-5 and v21 > 1e-3,
               f"corner angle {cn} is 0.2 mm under the roof, square to it (the roof moved 0.19 mm toward it still clears, "
               f"at 0.21 it meets it: {v21:.3f} mm3), and still clears the roof 0.15 mm lower")
        v = max(overlap(a.translate(d), trim_all) for d in directions(0.1))
        report(v < 1e-5, f"corner angle {cn} is at least 0.1 mm from the gable band and all other trim ({v:.5f} mm3 moved "
                         f"0.1 mm any way)")
    pa = [s.on_bed(a) for a in s.angle_prints()]
    mir = s.on_bed(pa[0].mirror([1, 0, 0]))
    hand = max((mir - pa[1]).volume(), (pa[1] - mir).volume())
    report(hand < 0.001 and (pa[0] - pa[1]).volume() > 1,
           "the two angles are mirror images of each other (one of each hand)")
    for (sx, sy), a in zip(s.CORNERS, s.angle_prints()):
        bb = a.bounding_box()
        worst, prev = 0.0, None
        for z0, z1 in layers(bb[5]):
            cs = a.slice((z0 + z1) / 2)
            if prev is not None:
                worst = max(worst, (cs - prev.offset(0.22, RND)).area())
            prev = cs
        nl = len(layers(bb[5] - 0.001))
        report(worst < 0.001 and abs(bb[5] - s.ANGLE_UP) < 1e-6 and nl == 18 and a.slice(0.125).area() > 0.95 * bb[4] * (bb[3] - 0.05),
               f"corner angle {corner_name(sx, sy)} prints on its side-face leg's outside face ({a.slice(0.125).area():.0f} "
               f"mm2 on the plate), its standing leg {bb[5]:.2f} mm tall ({nl} layers), nothing hanging past the layer "
               f"under it ({worst:.4f} mm2)")
    for sx, sy in s.CORNERS:
        ln, en = s.corner_walls(sx, sy)
        region = s.box(-12, 2, -12, 2, 30, 60).transform(s.corner_frame(sx, sy))
        T = to_corner(sx, sy)
        pl = printed_in_shed(p[ln], s.WALL_TO_PRINT[ln], region).transform(T)
        pe = printed_in_shed(p[en], s.WALL_TO_PRINT[en], region).transform(T)
        pa_ = printed_in_shed(angles[(sx, sy)], s.angle_to_print(sx), region).transform(T)
        floor_u = (pl ^ s.box(-3, 1, *FLOOR_WIN, 40, 50)).bounding_box()[3]
        floor_v = (pe ^ s.box(*FLOOR_WIN, -3, 1, 40, 50)).bounding_box()[4]
        du = floor_u - (pa_ ^ s.box(-1, 1, *ANGLE_WIN, 40, 50)).bounding_box()[0]
        dv = floor_v - (pa_ ^ s.box(*ANGLE_WIN, -1, 1, 40, 50)).bounding_box()[1]
        seated = pa_.translate([du, dv, 0])
        v = overlap(seated, s.union([pl, pe]))
        on_l, on_e = overlap(seated.translate([-0.01, 0, 0]), pl), overlap(seated.translate([0, -0.01, 0]), pe)
        away = square(-3, -0.6, -3, -0.6)
        ws, fs = s.union([pl, pe]).slice(45.0) ^ away, seated.slice(45.0) ^ away
        lo, hi = 0.0, 0.5
        for _ in range(14):
            mid = (lo + hi) / 2
            lo, hi = (lo, mid) if (fs.offset(mid, RND) ^ ws).area() > 1e-7 else (mid, hi)
        report(v < 1e-4 and on_l > 0.05 and on_e > 0.05 and lo >= 0.03,
               f"corner angle {corner_name(sx, sy)} as printed: pushed {-du:.3f} and {-dv:.3f} mm in, onto both printed "
               f"recess floors ({floor_u:.3f}, {floor_v:.3f}), it runs into neither wall ({max(v, 0):.4f} mm3 over 30 mm); "
               f"its fillet's steps stay {lo:.3f} mm clear of the walls' steps")
    for n in SIDES + ["back wall"]:
        axis, sign = s.WALL_SIDE[n]
        for sx, sy in s.CORNERS:
            if (sx, sy)[axis] != sign:
                continue
            T = to_corner(sx, sy)
            Ti = s.corner_frame(sx, sy)
            region = s.box(-12, 2, -12, 2, 15, 35).transform(Ti)
            pw = printed_in_shed(p[n], s.WALL_TO_PRINT[n], region).transform(T)
            k = axis

            def probe(a0, a1):
                b = [-3, 1, -3, 1, 20, 30]
                b[2 * (1 - k)], b[2 * (1 - k) + 1] = a0, a1
                return (pw ^ s.box(*b)).bounding_box()[3 + k] + s.WT
            floor_z, face_z = probe(*FLOOR_WIN), probe(-6.5, -4.5)
            wl = p[n].transform(T)
            sharp = 180.0
            for z in (3.0, 30.0, 60.0, s.ZWT - 1):
                for poly in (wl.slice(z) ^ square(-3, 1, -3, 1)).to_polygons():
                    P_ = np.asarray(poly)
                    for i in range(len(P_)):
                        a_, b_, c_ = P_[i - 1], P_[i], P_[(i + 1) % len(P_)]
                        if min(b_) < -2.9 or max(b_) > 0.9:
                            continue
                        e1, e2 = a_ - b_, c_ - b_
                        turn = (b_ - a_)[0] * (c_ - b_)[1] - (b_ - a_)[1] * (c_ - b_)[0]
                        if turn > 1e-9:
                            cosang = np.dot(e1, e2) / np.linalg.norm(e1) / np.linalg.norm(e2)
                            sharp = min(sharp, math.degrees(math.acos(max(-1, min(1, cosang)))))
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
                   f"round it at {face_z:.2f} ({nd} layers deep); the sharpest corner of the wall there is {sharp:.0f} "
                   f"degrees; at most {thin:.3f} mm2 a layer thinner than a line out to the nearest groove")

    # 7. the front corners: glued butt joints in a siding groove
    for sx in (1, -1):
        sn = "right side" if sx > 0 else "left side"
        sw = p[sn]
        v10 = overlap(sw.translate([0, -0.101, 0]), front)
        v09 = overlap(sw.translate([0, -0.09, 0]), front)
        sbb = (sw ^ s.box(-s.W, s.W, -s.L, s.YJ0 + 0.5, -1, 400)).bounding_box()      # its front end
        report(v09 < 1e-6 and v10 > 0.1 and abs(sbb[1] - s.YJ0) < 1e-6 and sbb[2] == 0 and abs(sbb[5] - (s.ZWT - 0.15)) < 1e-6,
               f"{sn}'s front end is a plane {s.MITRE_GAP} mm behind the front wall's inside face from z {sbb[2]:.2f} to "
               f"{sbb[5]:.3f} (moved 0.1 toward it they meet, {v10:.2f} mm3; at 0.09 they don't, {v09:.5f})")
        worst = sweep(sw, front, [[0, 0, dz] for dz in DROPS])
        report(worst < 1e-6, f"{sn} goes down past the front wall's end block without touching it ({worst:.6f} mm3)")
        deep = 99.0
        for z in (1.0, s.ZF + 1, 30.0, 60.0, s.ZWT - 1):
            fr = front.slice(z) ^ rect(-s.W, s.W, s.YF + s.WT - 0.02, s.YF + s.WT)
            sd = sw.slice(z) ^ rect(-s.W, s.W, s.YJ0, s.YJ0 + 0.02)
            xo = max(sx * fr.bounds()[0], sx * fr.bounds()[2]) if fr.area() > 0 else 0
            xs = max(sx * sd.bounds()[0], sx * sd.bounds()[2]) if sd.area() > 0 else 0
            deep = min(deep, s.W / 2 - max(xo, xs))
        report(deep >= 0.3, f"the {'+' if sx > 0 else '-'}x front joint lies at the bottom of a groove {deep:.3f} mm in from "
                            f"the side face over its full height (0.3 needed)")
        # the end block and the side wall's front end stud, with the siding over them (cut any wider
        # and the siding of the next bay would look like it hangs in the air)
        region = s.box(*sorted([sx * (s.W / 2 - s.WT - 0.01), sx * (s.W / 2 + 1)]), s.YF - 1, s.YJ0 + s.SW, 20, 40)
        wf = print_part(front, s.WALL_TO_PRINT["front wall"], region)
        ws_ = print_part(sw, s.WALL_TO_PRINT[sn], region)
        of, _ = worst_overhang(wf)
        os_, _ = worst_overhang(ws_)
        report(of < 0.01 and os_ < 0.01, f"the groove's chamfer on the front wall and notch on the {sn} print with nothing "
                                         f"over 45 degrees ({of:.4f} and {os_:.4f} mm2)")
        blk = front ^ s.box(*sorted([sx * (s.W / 2 - s.WT - 0.01), sx * (s.W / 2 + 1)]), s.YF - 1, s.YF + s.WT + 1, -1, s.ZF + 0.5)
        g_in = gap_move(blk, fl, [-sx, 0, 0], 1.0)
        g_fr = gap_move(blk, fl, [0, -1, 0], 1.0)
        report(blk.bounding_box()[2] == 0 and abs(g_in - 0.2) < 0.003 and abs(g_fr - 0.2) < 0.003,
               f"the {'+' if sx > 0 else '-'}x end block reaches z = {blk.bounding_box()[2]:.2f} in its floor notch, "
               f"{g_in:.3f} mm clear inside and {g_fr:.3f} at the front")


# =============================================================================================
if group(5, "gables and vents"):
    for n, side, piece, mat in (("back wall", 1, p["back wall"], s.WALL_TO_PRINT["back wall"]),
                                ("porch gable", -1, gable, s.WALL_TO_PRINT["porch gable"])):
        rbb = s.gable_vent(side)[1].bounding_box()
        region = s.box(rbb[0] - 1, rbb[3] + 1, -s.BIG, s.BIG, rbb[2] - 1, rbb[5] + 1)
        pw = printed_in_shed(piece, mat, region)
        field = s.box(rbb[0] + 0.3, rbb[3] - 0.3, -s.BIG, s.BIG, rbb[2] + 0.3, rbb[5] - 0.3)
        area = (rbb[3] - rbb[0] - 0.6) * (rbb[5] - rbb[2] - 0.6)
        fill = {}
        for z0, z1 in layers(5.3):
            if z0 >= 3.6:
                ya, yb = sorted([side * (s.L / 2 - s.WT + z0), side * (s.L / 2 - s.WT + z1)])
                fill[round(z0, 2)] = (pw ^ field ^ s.box(-s.BIG, s.BIG, ya, yb, -s.BIG, s.BIG)).volume() / (area * (z1 - z0))
        under = [fill[z] for z in (3.65, 3.85, 4.05)]
        louvres = [fill[z] for z in (4.25, 4.45, 4.65, 4.85)]
        R = np.column_stack([np.array(mat, dtype=float), np.zeros(3)])
        wb = piece.transform(R).bounding_box()

        def to_bed(m):
            return m.transform(R).translate([-wb[0], -wb[1], -wb[2]])
        pp = to_bed(piece ^ region)
        fb = to_bed(s.gable_vent(side)[1] ^ s.box(-s.BIG, s.BIG, -s.L / 2, s.L / 2, -s.BIG, s.BIG)).bounding_box()
        hole = square(fb[0], fb[3], fb[1], fb[4])
        shut, narrow, slat, nar_l = 0.0, 99.0, 99.0, []
        for z0, z1 in layers(5.05 - 0.001):
            if z0 >= 4.25 - 1e-9:
                sec = pp.slice((z0 + z1) / 2)
                gaps = hole - sec
                slats = hole ^ sec
                shut = max(shut, (gaps - gaps.offset(-0.21, MIT, 2).offset(0.21, MIT, 2)).area())
                xm = (fb[0] + fb[3]) / 2
                gl = [x1 - x0 for x0, x1 in scan(gaps.rotate(90), [xm])[0]]
                sl = [x1 - x0 for x0, x1 in scan(slats.rotate(90), [xm])[0]]
                if gl:
                    narrow = min(narrow, min(gl))
                if sl:
                    slat = min(slat, min(sl))
                nar_l.append(min(gl) if gl else 0)
        report(abs(s.WT - s.VENT_DEPTH - 4.25) < 1e-9 and min(under) > 0.999 and 0.2 < min(louvres) and max(louvres) < 0.95
               and all(a >= b for a, b in zip(louvres, louvres[1:])) and fill[5.05] < 1e-9 and shut < 0.01
               and narrow >= 0.42 and slat >= 0.42,
               f"{n}'s vent: the louvres' recess floor is on the 4.25 layer line with 3 full layers of siding under it; "
               f"the louvres fill {', '.join(f'{f * 100:.0f}' for f in louvres)} % of the 4 layers above it, narrowing to the "
               f"face; on every layer the gaps are {narrow:.3f} mm or wider (by layer {', '.join(f'{g:.3f}' for g in nar_l)}) "
               f"and the louvres {slat:.3f} or wider (0.42 needed); nothing prints above the siding's top layer")
        # the framing round the vent, on a section through the framing layer (u = SD / 2)
        yf = side * (s.L / 2 - s.WT + s.SD / 2)
        cut = piece ^ s.box(-s.W, s.W, min(yf, yf + side * 0.02), max(yf, yf + side * 0.02), -1, 200)
        kx = s.VENT_W / 2
        cv = s.CHORD / math.cos(s.ALPHA)
        between = cut ^ s.box(-kx + 0.05, kx - 0.05, -s.L, s.L, s.VENT_Z0 + 0.05, s.zline(kx) - cv - 0.05)
        kings = []
        for sgn in (1, -1):
            kb = (cut ^ s.box(*sorted([sgn * 2, sgn * 8]), -s.L, s.L, s.VENT_Z0 + 0.5, s.VENT_Z0 + 1.5)).bounding_box()
            kb2 = (cut ^ s.box(*sorted([sgn * (kx + 0.3), sgn * (kx + 0.9)]), -s.L, s.L, -1, 200)).bounding_box()
            kings.append((min(abs(kb[0]), abs(kb[3])), max(abs(kb[0]), abs(kb[3])), kb2[5]))
        sill = (cut ^ s.box(-0.3, 0.3, -s.L, s.L, s.VENT_Z0 - 3, s.VENT_Z0 + 0.5)).bounding_box()
        sbox = s.box(-kx + 0.01, kx - 0.01, -s.L, s.L, s.VENT_Z0 - s.SW + 0.01, s.VENT_Z0 - 0.01) ^             s.box(-s.W, s.W, *sorted([yf, yf + side * 0.02]), -1, 200)
        sill_gap = (sbox - cut).volume()                      # the sill fills the whole width between the kings
        mark = 3.175 if side < 0 else -3.175
        crip = (cut ^ s.box(mark - 0.3, mark + 0.3, -s.L, s.L, -1, s.VENT_Z0 - s.SW - 0.001)).bounding_box()
        crip_bottom = s.ZWT + s.CHORD if side < 0 else s.ZF + s.PLATE_BOT
        crip_top_gap = (cut ^ s.box(mark - 0.3, mark + 0.3, -s.L, s.L, s.VENT_Z0 - s.SW + 0.01, s.VENT_Z0 - 0.01)).volume()
        fr_bb = (s.back_wall_framing() if side > 0 else s.porch_gable_framing()).bounding_box()
        u_max = max(abs(fr_bb[1]), abs(fr_bb[4])) - (s.L / 2 - s.WT)
        crip_ok = abs(crip[5] - (s.VENT_Z0 - s.SW - 0.001)) < 1e-6 and (crip[2] <= crip_bottom + 1e-6)
        kings_ok = all(abs(k0 - kx) < 1e-6 and abs(k1 - (kx + s.SW)) < 1e-6 and k2 >= s.zline(kx + s.SW) - cv for k0, k1, k2 in kings)
        report(between.is_empty() and kings_ok and abs(sill[2] - (s.VENT_Z0 - s.SW)) < 1e-6 and abs(sill[5] - s.VENT_Z0) < 1e-6
               and sill_gap < 1e-9 and crip_ok and u_max <= s.SD + 0.2 + 1e-6,
               f"{n}: round the vent no stud or header between the kings; kings {kings[0][0]:.3f} to {kings[0][1]:.3f} mm "
               f"each side of the middle ({(kings[0][1] - kings[0][0]) * inch:.2f} in wide) reaching into the top chord "
               f"(to z {min(k[2] for k in kings):.2f}); a flat sill z {sill[2]:.3f} to {sill[5]:.3f} right across between them; one cripple under it on "
               f"the mark at x {mark:+.3f} from {'the bottom chord' if side < 0 else 'the bottom plate'} up to the sill; the framing reaches u {u_max:.3f} at most "
               f"(the top chord 0.2 into the siding)")


# =============================================================================================
if group(6, "porch"):
    zd, zt = s.ZF - 0.5, s.FRAME_Z0 + 0.5
    dsl, fsl = fl.slice(zd), frame.slice(zt)
    worst_d, worst_f, wp = 9.0, 9.0, 9.0
    no_post = []       # a socket with no tenon in it at all would read as 2 mm clear, so it is named and fails
    for (sx, xc), pt in posts.items():
        g1 = gaps4(pt.slice(zd), dsl ^ rect(sx * xc - 5, sx * xc + 5, s.POST_Y - 5, s.POST_Y + 5))
        g2 = gaps4(pt.slice(zt), fsl ^ rect(sx * xc - 5, sx * xc + 5, s.POST_Y - 5, s.POST_Y + 5))
        worst_d, worst_f = min(worst_d, *g1), min(worst_f, *g2)
        no_post += [f"the {w} socket at x {sx * xc:+.2f}" for w, cs_ in (("deck", pt.slice(zd)), ("frame", pt.slice(zt)))
                    if cs_.is_empty()]
        if sx > 0:
            reg = s.tenon_box(sx, xc, s.ZF - 3, s.ZF + 3, 2.0)
            pp_ = printed_in_shed(pt, s.POST_TO_PRINT, reg)
            pf_ = printed_in_shed(fl, s.FLOOR_TO_PRINT, reg)
            ga = gaps4(pp_.slice(zd), pf_.slice(zd))
            reg2 = s.tenon_box(sx, xc, s.FRAME_Z0 - 3, s.FRAME_Z0 + 3, 2.0)
            pp2 = printed_in_shed(pt, s.POST_TO_PRINT, reg2)
            pfr = printed_in_shed(frame, s.FRAME_TO_PRINT, reg2)
            gb = gaps4(pp2.slice(zt), pfr.slice(zt))
            wp = min(wp, *ga, *gb)
            no_post += [f"the {w} socket at x {sx * xc:+.2f} as printed" for w, cs_ in (("deck", pp_.slice(zd)),
                                                                                       ("frame", pp2.slice(zt)))
                        if cs_.is_empty()]
    report(abs(worst_d - s.TENON_CLR) < 0.003 and abs(worst_f - s.TENON_CLR) < 0.003 and wp >= 0.25 and not no_post,
           f"each post's tenons sit in their deck and frame sockets {worst_d:.3f} and {worst_f:.3f} mm clear all round as "
           f"drawn, and at least {wp:.3f} as both are printed (0.25 needed)"
           + (f"; but no post reaches into {', '.join(no_post)}" if no_post else ""))
    v_dn = min(overlap(frame.translate([0, 0, -0.1]), pt) for pt in posts.values())
    v_up = overlap(frame.translate([0, 0, 0.1]), post_set)
    v_ft = min(overlap(pt.translate([0, 0, -0.1]), fl) for pt in posts.values())
    report(v_dn > 0.1 and v_up < 1e-6 and v_ft > 0.1,
           f"the posts' end faces bear on the deck and the frame (frame lowered 0.1 mm meets every post, least "
           f"{v_dn:.2f} mm3; raised 0.1 it is free; each post lowered 0.1 meets the deck, least {v_ft:.2f} mm3)")
    ppr = s.to_print(s.POST_TO_PRINT, [p["post"]])[0]
    pb = ppr.bounding_box()
    tb = (ppr ^ s.box(-1, 0.9, -10, 10, -1, 10)).bounding_box()
    report(abs(pb[4] - s.POST) < 1e-6 and abs(pb[5] - s.POST) < 1e-6 and on_layer(pb[5]) and abs(tb[5] - s.TENON_T) < 1e-6,
           f"each post is {pb[4]:.2f} x {pb[5]:.2f} mm square ({len(layers(pb[5] - 0.001))} layers), its tenons "
           f"{tb[5]:.2f} mm thick on the face it prints on")
    # every socket in solid floor or beam: grown 0.6 round (and 0.6 below), nothing but floor or beam; in
    # the deck right up to its face, so no board groove passes within 0.6 of a socket's or hole's mouth
    worst = 0.0
    holes = [s.tenon_box(sx, xc, s.ZF - s.SOCKET_D, s.ZF + 1, s.TENON_CLR) for sx, xc in s.post_spots()]
    holes += [s.box(x0 - s.TENON_CLR, x1 + s.TENON_CLR, y0 - s.TENON_CLR, y1 + s.TENON_CLR, s.ZF - s.SOCKET_D, s.ZF + 1)
              for x0, x1, y0, y1 in s.rail_pegs()]
    for h in holes:
        bb = h.bounding_box()
        g = s.box(bb[0] - 0.6, bb[3] + 0.6, bb[1] - 0.6, bb[4] + 0.6, bb[2] - 0.6, s.ZF)
        worst = max(worst, (g - fl - h).volume())
    fholes = [s.tenon_box(sx, xc, s.FRAME_Z0 - 1, s.FRAME_Z0 + s.SOCKET_D, s.TENON_CLR) for sx, xc in s.post_spots()]
    gi = -(s.L / 2 - s.WT)
    fholes += [s.box(x - s.GPEG_W / 2 - s.TENON_CLR, x + s.GPEG_W / 2 + s.TENON_CLR, gi - s.GPEG_T - s.TENON_CLR,
                     gi + s.TENON_CLR, s.ZWT - s.GPEG_SOCKET, s.ZWT + 1) for x in (-s.PEG_X, s.PEG_X)]
    worst_f = 0.0
    for h in fholes:
        bb = h.bounding_box()
        g = s.box(bb[0] - 0.6, bb[3] + 0.6, bb[1] - 0.6, bb[4] + 0.6, max(bb[2] - 0.6, s.FRAME_Z0), min(bb[5] + 0.6, s.ZWT - 0.4))
        worst_f = max(worst_f, (g - frame - h).volume())
    report(worst < 1e-4 and worst_f < 1e-4,
           f"every socket and peg hole has at least 0.6 mm of solid floor or beam round it: {len(holes)} in the deck, up "
           f"to its face, so no board groove comes within 0.6 of one ({worst:.5f} mm3 missing), {len(fholes)} in the "
           f"frame ({worst_f:.5f})")

    # 10. the porch frame
    report(len(posts) == 3 and min(overlap(frame.translate([0, 0, -0.1]), pt) for pt in posts.values()) > 0.1,
           f"the porch frame rests on all {len(posts)} posts (3 meant: a corner post each side and the middle post)")
    side_beams = frame ^ s.box(-s.W, s.W, s.REAR_BEAM[1] + 0.01, s.L, -1, 200)
    rear = frame ^ s.box(-s.W / 2 + s.WT + 0.1, s.W / 2 - s.WT - 0.1, s.REAR_BEAM[0] - 0.01, s.REAR_BEAM[1] + 0.01, -1, 200)
    g_side = gap_move(side_beams, front, [0, 1, 0], 1.0)
    g_rear = s.two_colour(front, zone)[1].bounding_box()[1] - rear.bounding_box()[4]     # in plan: it is above them
    report(abs(g_side - 0.2) < 0.003 and abs(g_rear - 0.2) < 0.003,
           f"the side beams' back ends stand {g_side:.3f} mm off the front wall's face and the rear beam {g_rear:.3f} mm off "
           f"its casings in plan (it stands above them)")
    v14 = overlap(frame, roofs.translate([0, 0, -0.145]))
    v17 = overlap(frame, roofs.translate([0, 0, -0.17]))
    report(overlap(frame, roofs) == 0 and v14 < 1e-6 and v17 > 1e-5,
           f"the porch frame stays 0.15 mm under the roof (roof lowered 0.145 mm still clears it, {v14:.6f} mm3; at "
           f"0.17 it meets the bevel, {v17:.5f})")
    # the bevel starts where the plane 0.15 mm under the roof's underside comes down to the frame's top: 47.35 under
    # the designer's 6.48/12, 47.265 under Alan's 5/12 (Nov 4 2026). Inside it the frame's top section is the same as
    # its section 0.5 mm down (over the posts' sockets and the lip, both under the gable pegs' sockets), so nothing is
    # cut off its top there; past it the top is cut away
    xb = s.W / 2 - 0.15 / s.PITCH
    hi_cs, lo_cs = frame.slice(s.ZWT - 0.005), frame.slice(s.ZWT - 0.5)
    inner = rect(-xb + 0.005, xb - 0.005, -s.L, s.L)
    outer = rect(xb + 0.05, s.W, -s.L, s.L) + rect(-s.W, -xb - 0.05, -s.L, s.L)
    d_in = ((lo_cs ^ inner) - hi_cs).area() + ((hi_cs ^ inner) - lo_cs).area()
    bev = ((lo_cs ^ outer) - hi_cs).area()
    sb_ = (frame ^ s.box(42.6, xb - 0.005, -80, -70, -1, 300)).bounding_box()
    out_ = (frame ^ s.box(47.4, 48, -80, -70, -1, 300)).bounding_box()
    full = sb_[5] - sb_[2]
    report(d_in < 1e-6 and bev > 0.5 and abs(full - s.FRAME_H) < 1e-6 and out_[5] < s.ZWT - 0.01,
           f"the frame is its full {full:.2f} mm everywhere inside |x| {xb:.3f}, where the plane 0.15 mm under the roof "
           f"meets its top (side beams included: no cut from the side walls' roof clearance; its top section and the one "
           f"0.5 mm down differ there by {d_in:.6f} mm2), bevelled only past it ({bev:.1f} mm2 off its top section; top "
           f"{out_[5]:.3f} at |x| 47.4 to 48)")
    v = sweep(frame, walls_set, [[0, d, 0] for d in (0.19,)])
    v2 = overlap(frame.translate([0, 0.21, 0]), front)
    report(v < 1e-6 and v2 > 1e-4, f"the frame is 0.2 mm clear of the front wall's end blocks and the side walls (moved "
                                   f"0.19 toward them, {v:.6f} mm3; at 0.21 it meets them)")
    fp = s.to_print(s.FRAME_TO_PRINT, [frame])[0]
    wo, _ = worst_overhang(fp)
    lip = (frame ^ s.box(-1, 1, s.FRAME_IN + 0.2, s.FRAME_IN + 0.6, -1, 200)).bounding_box()
    fb_ = fp.bounding_box()
    report(wo < 0.01 and abs(fb_[5] - s.FRAME_H) < 1e-6 and len(layers(fb_[5] - 0.001)) == 14 and abs(lip[5] - lip[2] - 0.65) < 1e-6,
           f"the frame prints bottom down with nothing hanging over ({wo:.4f} mm2), {fb_[5]:.2f} mm tall "
           f"({len(layers(fb_[5] - 0.001))} layers), the lip {lip[5] - lip[2]:.2f} mm ({len(layers(lip[5] - lip[2] - 0.001))} "
           f"layers) on the bed")
    stage = s.union([fl, walls_set, door_shut, post_set, rail_set])
    worst = sweep(frame, stage, [[0, 0, dz] for dz in [0.05] + DROPS if dz <= 80])
    v = overlap(frame.translate([0, 0, -0.1]), stage)
    report(worst < 1e-6 and v > 0.1, f"lowered from 80 mm onto the three posts standing in their sockets, with the railings "
                                     f"in, the frame touches nothing until it sits on them ({worst:.6f} mm3; lowered 0.1 "
                                     f"more it meets them)")

    # 11. the ceiling: 0.2 off the four beams and on 1.0 of lip under each edge (spec 4.5)
    v_dn = overlap(ceiling.translate([0, 0, -0.1]), frame)
    g = [gap_move(ceiling, frame, d, 1.0) for d in ([1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0])]
    lift = sweep(ceiling, s.union([frame, gable]), [[0, 0, dz] for dz in DROPS if dz <= 80])
    cb = ceiling.bounding_box()
    bear = frame.slice(s.FRAME_Z0 + s.LIP_H - 0.05) ^ ceiling.slice(cb[2] + 0.05)
    widths, lines_ok = [], True
    for f_ in (0.05, 0.5, 0.95):                       # lines across the +-x edges, then across the front and back
        iv = scan(bear, [cb[1] + f_ * (cb[4] - cb[1])])[0]
        lines_ok &= len(iv) == 2
        widths += [b - a for a, b in iv]
    for f_ in (0.05, 0.3, 0.5, 0.7, 0.95):
        iv = scan(bear.rotate(90), [cb[0] + f_ * (cb[3] - cb[0])])[0]
        lines_ok &= len(iv) == 2
        widths += [b - a for a, b in iv]
    report(v_dn > 0.1 and all(abs(x - 0.2) < 0.003 for x in g) and lift < 1e-6 and lines_ok and min(widths) >= 0.95,
           f"the ceiling rests on the lip (lowered 0.1 mm it meets it), {min(g):.3f} to {max(g):.3f} mm off the four beams "
           f"(0.2 meant), bears on {min(widths):.3f} to {max(widths):.3f} mm of lip under its edges (1.0 meant, 0.95 "
           f"needed), and lifts straight out ({lift:.6f} mm3)")

    # 12. the porch gable
    v_dn = overlap(gable.translate([0, 0, -0.1]), frame)
    zp = s.ZWT - 0.8
    gs = []
    for x in (-s.PEG_X, s.PEG_X):
        gpeg = gable.slice(zp) ^ rect(x - 3, x + 3, -s.L, s.L)
        gs += gaps4(gpeg, frame.slice(zp) ^ rect(x - 4, x + 4, -s.L, s.L))
    reg = s.box(s.PEG_X - 3, s.PEG_X + 3, -s.L / 2 - 1, -s.L / 2 + s.WT + 2, s.ZWT - 2, s.ZWT + 1)
    pg = printed_in_shed(gable, s.WALL_TO_PRINT["porch gable"], reg)
    pfr = printed_in_shed(frame, s.FRAME_TO_PRINT, reg)
    gp = gaps4(pg.slice(zp), pfr.slice(zp))
    gpr = s.to_print(s.WALL_TO_PRINT["porch gable"], [gable])[0]
    pegs_low = (gpr ^ s.box(-1, 200, -1, 1.5, -1, 10)).bounding_box()
    wo, _ = worst_overhang(gpr)
    report(v_dn > 0.1 and all(abs(x - s.TENON_CLR) < 0.003 for x in gs) and min(gp) >= 0.25 and
           abs(gable.bounding_box()[1] + s.L / 2) < 1e-9 and pegs_low[2] == 0 and wo < 5,
           f"the porch gable rests on the frame (lowered 0.1 mm it meets it), its pegs {min(gs):.3f} to {max(gs):.3f} mm "
           f"clear in their sockets ({min(gp):.3f} as printed), its siding face at y {gable.bounding_box()[1]:.2f}, and it "
           f"prints flat with its pegs on the bed ({wo:.2f} mm2 worst overhang)")
    # the roof rests on the porch gable all along the slope, by the same measure as group 8's, so this group
    # proves it on its own. (The old line lowered the roof 0.3 mm, and passed a porch gable standing 0.25 mm
    # under the roof everywhere but at the peak, or 0.03 mm under it all over.)
    on_pg = {hn: roof_rest(hn, "porch") for hn in ("right", "left")}
    pg_least = min(on_pg.values(), key=lambda r_: r_[1])
    pg_by_peg = ", beside a peg's hole" if abs(abs(pg_least[2]) - s.PEG_X) < 2 else ""
    report(pg_least[1] >= 0.02,
           f"lowered 0.02 mm, each roof half meets the porch gable's top in every 1 mm of the slope from the ridge out "
           f"to 45 mm, so the roof rests on it all along (least {pg_least[1]:.3f} mm3 in a mm, at x "
           f"{pg_least[2]:+.1f}{pg_by_peg}; 0.02 needed; in all {on_pg['right'][0]:.2f} under the right half and "
           f"{on_pg['left'][0]:.2f} under the left)")

    # 13. the railings
    zr = s.ZF - 0.5
    rg = []
    for name, r in rails.items():
        rg += gaps4(r.slice(zr), fl.slice(zr) ^ rect(-s.W, s.W, -s.L, s.YF - 1))
    srail = rails["side railing +x"]
    frail = rails["front railing"]
    bot = (srail ^ s.box(-s.W, s.W, -80, -79, s.ZF, 200)).bounding_box()[2] - s.ZF
    e_side = gap_move(srail, post_set, [0, -1, 0], 1.0)
    e_f1, e_f2 = gap_move(frail, post_set, [1, 0, 0], 1.0), gap_move(frail, post_set, [-1, 0, 0], 1.0)
    e_wall = gap_move(srail, front, [0, 1, 0], 4.0)
    everything = s.union([body, frame, gable, ceiling, post_set, door_shut])
    touch = max(overlap(r, everything) for r in rails.values())
    others = max(overlap(a, b) for a, b in itertools.combinations(list(rails.values()), 2))
    report(all(abs(x - s.TENON_CLR) < 0.003 for x in rg) and abs(bot - 0.24 * s.FT) < 1e-6 and abs(e_side - 0.2) < 0.003
           and abs(e_f1 - 0.2) < 0.003 and abs(e_f2 - 0.2) < 0.003 and abs(e_wall - 2.381) < 0.003 and touch < 1e-6
           and others < 1e-6 and len(rails) == 3 and len(s.rail_pegs()) == 6,
           f"the {len(rails)} railings' {len(s.rail_pegs())} pegs sit {min(rg):.3f} to {max(rg):.3f} mm clear in their holes; the bottom "
           f"rail is {bot:.3f} mm above the deck; the ends stand {e_side:.3f} (side), {e_f1:.3f} and {e_f2:.3f} (front) mm "
           f"off the posts and the side panels {e_wall:.3f} mm off the front wall; they touch nothing else ({touch:.6f})")
    # Alan's standard layout, measured off the parts: the one front railing runs from the -x corner
    # post to the middle post, under the front window; the bay from the middle post to the +x corner
    # post is the way in: nothing in it from the deck to the frame and from the front edge back to the
    # front wall's casings, deck under it, and the doorway inside it
    pb = sorted([pt.bounding_box() for pt in posts.values()], key=lambda b: b[0])
    rb_ = frail.bounding_box()
    sid = [b for b in scan(front.slice(s.ZF + 50), [s.YF + 0.42])[0]]   # the siding line (u WT - 0.42, over the sashes) through the window
    sid_gaps = [(a[1], b[0]) for a, b in zip(sid, sid[1:])]
    win_gap = min(sid_gaps, key=lambda g: g[0])
    sid20 = scan(front.slice(s.ZF + 20), [s.YF + 0.42])[0]                       # under the window: only the door
    door_gaps = [(a[1], b[0]) for a, b in zip(sid20, sid20[1:])]
    fr20 = scan(front.slice(s.ZF + 20), [s.YF + s.WT - 1.0])[0]                  # u 1.0, inside the stop: the jambs
    door_gap = max(((a[1], b[0]) for a, b in zip(fr20, fr20[1:])), key=lambda g: g[1] - g[0])
    bay = (pb[1][3], pb[2][0])
    clear_box = s.box(bay[0] + 0.01, bay[1] - 0.01, -s.L / 2 - 1, s.YF - s.PROUD - 0.01, s.ZF + 0.01, s.FRAME_Z0 - 0.01)
    in_bay = overlap(clear_box, s.union([body, frame, gable, ceiling, post_set, rail_set, door_shut, roofs]))
    deck_box = s.box(bay[0] + 0.01, bay[1] - 0.01, -s.L / 2, s.YF - s.FIT - 0.01, s.ZF - 0.5, s.ZF)
    deck_fill = overlap(deck_box, fl) / deck_box.volume()
    rail_ok = (pb[0][3] < rb_[0] < rb_[3] < pb[1][0] and rb_[0] < win_gap[0] and win_gap[1] < rb_[3]
               and len(door_gaps) == 1 and bay[0] < door_gap[0] and door_gap[1] < bay[1])
    report(len(pb) == 3 and rail_ok and in_bay < 1e-6 and deck_fill > 0.9 and bay[1] - bay[0] > s.DOOR_OPEN_W + 10,
           f"the one front railing runs x {rb_[0]:.3f} to {rb_[3]:.3f}, between the -x corner post and the middle post, "
           f"under the front window (x {win_gap[0]:.3f} to {win_gap[1]:.3f}); the way in is the bay from the middle post to "
           f"the +x corner post, x {bay[0]:.3f} to {bay[1]:.3f}, {bay[1] - bay[0]:.2f} mm ({(bay[1] - bay[0]) * inch:.1f} in) "
           f"clear, with nothing in it from the deck to the frame and from the front edge to the casings ({in_bay:.6f} mm3), "
           f"deck under it ({deck_fill * 100:.0f} % of its top 0.5 mm, the board grooves the rest), and the doorway "
           f"(x {door_gap[0]:.3f} to {door_gap[1]:.3f}) inside it")
    for name, r, mat in (("side railing", srail, s.SIDE_RAIL_TO_PRINT), ("front railing", frail, s.FRONT_RAIL_TO_PRINT)):
        rp = s.to_print(mat, [r])[0]
        wo, _ = worst_overhang(rp)
        bb = rp.bounding_box()
        report(wo < 0.01 and abs(bb[5] - s.CAP_D) < 1e-6,
               f"the {name} prints on its outside face, {bb[5]:.2f} mm tall, with nothing hanging over ({wo:.4f} mm2)")
    bare = s.union([fl, walls_set, door_shut])
    worst = max(sweep(r, bare, [[0, 0, dz] for dz in [0.05] + DROPS if dz <= 80]) for r in rails.values())
    v = min(overlap(r.translate([0, 0, -0.1]), fl) for r in rails.values())
    report(worst < 1e-6 and v > 0.01, f"each railing lowered straight down from 80 mm onto the bare porch touches nothing "
                                      f"until its pegs are in their holes ({worst:.6f} mm3; lowered 0.1 more it sits on "
                                      f"the deck)")
    # the pegs stop 0.05 short of their holes' floor for the glue (PRINTER-BRAIN "Let a peg bottom in its hole",
    # the Lofted Barn Cabin's railings): lowered 0.04 a railing still clears the deck, at 0.06 its pegs meet the
    # holes' floor, so pressed home it drops 0.05 and no more (review Nov 3 2026)
    v04 = max(overlap(r.translate([0, 0, -0.04]), fl) for r in rails.values())
    v06 = min(overlap(r.translate([0, 0, -0.06]), fl) for r in rails.values())
    peg_foot = min(r.bounding_box()[2] for r in rails.values()) - (s.ZF - s.SOCKET_D)
    report(v04 < 1e-6 and v06 > 1e-3 and abs(peg_foot - 0.05) < 1e-6,
           f"each railing's pegs stop {peg_foot:.3f} mm short of their holes' floor (lowered 0.04 it still clears the "
           f"deck, {v04:.6f} mm3; at 0.06 its pegs meet the floor, least {v06:.4f}), so pressed home in its glue a "
           f"railing drops 0.05 mm and no more")

    # 14. lift-off: the walls, frame, posts, porch gable, ceiling and door come up off the floor as one
    unit = s.union([walls_set, frame, post_set, gable, ceiling, door_shut])
    v = max(overlap(unit.translate([0, 0, dz]), s.union([fl_open, rail_set])) for dz in (3, 10, 80))
    vp = sweep(post_set, s.union([fl, rail_set]), [[0, 0, dz] for dz in DROPS if dz <= 80])
    report(v < 1e-6 and vp < 1e-6,
           f"the walls, porch frame, posts, porch gable, ceiling and door lift off the floor together (up 3, 10 and 80 mm "
           f"they touch nothing but the barbs: {v:.6f} mm3), the post feet sliding out past the railings; the same move "
           f"down is how the posts go in past the glued railings ({vp:.6f})")


# =============================================================================================
def tilt_matrix(theta, off, lift, mat0):
    """mat0 (door print coords to cabin) lifted by lift and tilted about the line along x through
    the top of the door at its pin line, so the bottom swings off toward the room (+y) by off at
    the bottom pin's tip."""
    m = mat0.copy()
    m[2, 3] += lift
    H = s.DOOR_H + s.PIN_BOTTOM_LEN
    ph = math.asin(off / H) if theta is None else theta
    c, sn = math.cos(ph), math.sin(ph)
    R = np.array([[1, 0, 0], [0, c, -sn], [0, sn, c]])
    piv = np.array([0, s.AXIS_Y, m[2, 3] + s.DOOR_H])
    return np.column_stack([R @ m[:, :3], R @ (m[:, 3] - piv) + piv]), ph


def hang_path(leaf, wall, mat0, H_door, zf, oh):
    """F7's hanging path in open air: top pin up in the head hole, the door lifted 0.5, its bottom
    pin's centre 2.8 inside the pin line, swung out along the trench in 0.25 steps and dropped.
    Returns (worst overlap, margin over the trench floor, margin under the head, start tilt)."""
    H = H_door + s.PIN_BOTTOM_LEN
    worst, start = 0.0, None
    lowest, highest = 99.0, -99.0
    offs = [2.8 - 0.25 * k for k in range(12)] + [0.0]
    for off in offs:
        m = mat0.copy()
        m[2, 3] += 0.5
        ph = math.asin(off / H)
        c, sn = math.cos(ph), math.sin(ph)
        R = np.array([[1, 0, 0], [0, c, -sn], [0, sn, c]])
        piv = np.array([0, s.AXIS_Y, m[2, 3] + H_door])
        mm = np.column_stack([R @ m[:, :3], R @ (m[:, 3] - piv) + piv])
        d = leaf.transform(mm)
        worst = max(worst, overlap(d, wall))
        pin = (leaf ^ s.box(-2, 2, -5, 0, -5, 5)).transform(mm)
        top = (leaf ^ s.box(-100, 100, H_door - 0.3, H_door + 0.01, -5, 5)).transform(mm)
        lowest = min(lowest, pin.bounding_box()[2] - (zf - s.TRENCH_DEPTH))
        highest = max(highest, top.bounding_box()[5] - (zf + oh))
        if start is None:
            start = math.degrees(ph)
    m = mat0.copy()
    m[2, 3] += 0.5
    worst = max(worst, overlap(leaf.transform(m), wall))
    return worst, lowest, -highest, start


LEFT_HINGED_SWING = 101.9   # how far the door swung in hinged on the left (check Nov 4 2026, before Alan's answer)


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


if group(7, "door"):
    # Alan Nov 4 2026, "hinges on the right side": the door hangs on the doorway's right-hand jamb as seen
    # from the porch (+x, next to the right side wall), the knob toward the middle of the wall, the stop
    # on the left-hand (latch) jamb, and swung in it turns toward the right side wall. Measured off the
    # parts, not taken from HINGE
    jl, jr = s.DOOR_X - s.JAMB, s.DOOR_X + s.JAMB                       # the doorway, x 2.286 to 30.861
    pin_b = (door_shut ^ s.box(-s.W, s.W, -s.L, s.L, -5, s.ZF)).bounding_box()      # the bottom pin, under the threshold
    pin_x = (pin_b[0] + pin_b[3]) / 2
    sill_hole = (s.box(jl, jr, s.AXIS_Y - 0.05, s.AXIS_Y + 0.05, s.ZF - 0.9, s.ZF - 0.8) - front).bounding_box()
    head_hole = (s.box(jl, jr, s.AXIS_Y - 0.05, s.AXIS_Y + 0.05, s.ZF + s.DOOR_OPEN_H + 1.0, s.ZF + s.DOOR_OPEN_H + 1.1)
                 - front).bounding_box()
    knob_b = (door_shut ^ s.box(-s.W, s.W, -s.L, s.AXIS_Y - s.DOOR_R - 0.05, -5, 200)).bounding_box()   # out past its face
    knob_x = (knob_b[0] + knob_b[3]) / 2
    stop_b = (front ^ s.box(jl + 0.01, jr - 0.01, -s.L, s.L, s.ZF + 20, s.ZF + 21)).bounding_box()     # all that is in the doorway
    swung = door.transform(s.door_to_cabin(45)).bounding_box()
    hand_ok = (abs(pin_x - (jr - s.DOOR_GAP - s.DOOR_R)) < 1e-3 and abs((sill_hole[0] + sill_hole[3]) / 2 - pin_x) < 0.01
               and abs((head_hole[0] + head_hole[3]) / 2 - pin_x) < 0.01 and pin_x > s.DOOR_X
               and abs(knob_x - (jl + s.DOOR_GAP + 2.2)) < 1e-3 and abs(stop_b[0] - (jl + 0.01)) < 1e-3
               and abs(stop_b[3] - (jl + 0.8)) < 1e-3 and swung[4] > s.YF + s.WT + 15 and swung[0] > jl + 5)
    report(hand_ok, f"the door hangs on the right as seen from the porch (Alan Nov 4 2026, \"hinges on the right side\"): its "
                    f"bottom pin at x {pin_x:.3f}, {jr - pin_x:.2f} mm in from the doorway's right-hand jamb (x {jr:.3f}, next "
                    f"to the right side wall), with both pin holes over it (x {(sill_hole[0] + sill_hole[3]) / 2:.3f} and "
                    f"{(head_hole[0] + head_hole[3]) / 2:.3f}); its knob on the outside {knob_x - jl:.2f} mm from the left-hand "
                    f"(latch) jamb (x {jl:.3f}), toward the middle of the wall, and the stop on that jamb only, reaching x "
                    f"{stop_b[3]:.3f}; swung in 45 degrees it reaches {swung[4] - (s.YF + s.WT):.1f} mm into the room on the "
                    f"right-hand side of the doorway, {swung[0] - jl:.1f} mm from the latch jamb at its nearest")
    # the door swung against everything else in the finished cabin: the walls and floor (the right side wall
    # and its window casing included), both corner angles, the porch frame, ceiling, gable, posts and
    # railings and both roof halves
    angles_on = s.union([s.corner_angle(sx, sy) for sx, sy in s.CORNERS])
    obstacles = s.union([body, frame, gable, ceiling, post_set, rail_set, roofs, angles_on])
    closed = overlap(body, door_shut)
    report(closed < 0.01, f"shut, the door fits its opening ({closed:.4f} mm3)")
    last_free = 0
    for deg in range(0, 121, 2):
        v = overlap(obstacles, door.transform(s.door_to_cabin(deg)))
        if v < 0.01:
            last_free = deg
        else:
            break
    lo_, hi_ = float(last_free), float(last_free + 2)
    for _ in range(10):
        mid = (lo_ + hi_) / 2
        if overlap(obstacles, door.transform(s.door_to_cabin(mid))) < 0.01:
            lo_ = mid
        else:
            hi_ = mid
    hit = s.union([q for q in (obstacles ^ door.transform(s.door_to_cabin(hi_))).decompose()   # (not the flat
                   if q.volume() > 1e-6]).bounding_box()                                      # touches of the pin)
    king = [m for m in s.framing_plan("front wall")[0] if m[4] == "king stud" and m[0] > jr - 1e-6 and m[0] < jr + 1e-6]
    at_king = bool(king) and king[0][0] - 0.01 < hit[0] and hit[3] < king[0][1] + 0.01 and hit[1] > s.YF + s.TS - 0.01
    open_ = door.transform(s.door_to_cabin(lo_)).bounding_box()
    report(lo_ >= 90 and lo_ >= LEFT_HINGED_SWING - 0.05 and at_king and open_[3] > s.AXIS_X + s.DOOR_R + 3,
           f"the door swings in freely to {lo_:.1f} degrees (90 needed, and at least the {LEFT_HINGED_SWING} it swung hinged "
           f"on the left), clear of the floor, the right side wall and its window casing, both corner angles, the porch and "
           f"the roof, toward the right side wall (its latch edge out to x {open_[3]:.2f}, {s.W / 2 - s.WT - open_[3]:.1f} mm "
           f"short of that wall's studs), where it meets the hinge-side king stud (x {hit[0]:.3f} to {hit[3]:.3f})")
    v = overlap(front, door.transform(s.door_to_cabin(-2)))
    report(v > 0.05, f"at -2 degrees (outward) it meets the stop on the latch side ({v:.2f} mm3), so it can't swing out")
    # the pin holes stop short of the inside face (lowest at u 0.25), and the wall's first layer is
    # whole over them
    lows = []
    for zc in (s.ZF - 0.85, s.ZF + s.DOOR_OPEN_H + 1.0):
        col = front ^ s.box(s.AXIS_X - 0.05, s.AXIS_X + 0.05, s.YF - 1, s.YF + s.WT + 1, zc - 0.05, zc + 0.05)
        parts_ = sorted(col.decompose(), key=lambda q: -q.bounding_box()[4])
        lows.append(s.YF + s.WT - parts_[0].bounding_box()[1])
    fpr = s.to_print(s.WALL_TO_PRINT["front wall"], [front])[0]
    R = np.column_stack([np.array(s.WALL_TO_PRINT["front wall"], dtype=float), np.zeros(3)])
    wbb = front.transform(R).bounding_box()
    holes_ok = True
    miss = 0.0
    for z0, z1 in ((s.ZF - s.HOLE_BOTTOM_DEPTH, s.ZF - s.TRENCH_DEPTH), (s.ZF + s.DOOR_OPEN_H, s.ZF + s.DOOR_OPEN_H + s.HOLE_TOP_DEPTH)):
        fp = rect(s.AXIS_X - s.PIN_HOLE_D / 2 - wbb[0], s.AXIS_X + s.PIN_HOLE_D / 2 - wbb[0], z0 - wbb[1], z1 - wbb[1])
        first = as_printed(fpr ^ s.box(-1, 300, -1, 300, -1, 0.6)).slice(0.125)
        miss = max(miss, (fp - first).area())
    report(all(abs(l_ - 0.25) < 0.01 for l_ in lows) and miss < 1e-4,
           f"the hinge pin holes stop {lows[0]:.3f} and {lows[1]:.3f} mm short of the front wall's inside face (u 0.25), "
           f"and as printed the first layer is whole over both ({miss:.5f} mm2 missing)")
    worst, m_floor, m_head, start = hang_path(door, front, s.door_to_cabin(0), s.DOOR_H, s.ZF, s.DOOR_OPEN_H)
    report(worst < 0.05 and m_floor > 0.1 and m_head > 0.0,
           f"in the loose front wall the door hangs from the inside: top pin up, lifted 0.5 mm, bottom pin 2.8 mm inside "
           f"the pin line (tilt {start:.2f} degrees), swung out along the trench in 0.25 mm steps and dropped, worst "
           f"{worst:.4f} mm3 (0.05 allowed), {m_floor:.3f} mm over the trench floor and {m_head:.3f} under the head")
    m = s.door_to_cabin(0)
    m[2, 3] += 0.55
    v = overlap(front, door.transform(m))
    report(v < 0.01, f"lifted 0.55 mm straight up the door still clears the head ({v:.4f} mm3)")
    # captive once the wall is on the floor
    tr = s.box(s.AXIS_X - s.PIN_HOLE_D / 2, s.AXIS_X + s.PIN_HOLE_D / 2, s.YF + s.WT + s.FIT + 0.001, -43.0,
               s.ZF - s.TRENCH_DEPTH, s.ZF)
    missing = (tr - fl).volume()
    # hung on the right, the trench's width takes in the floor sheet seam 8 ft from the left side (x 28.575),
    # which runs into the room from the pocket under the pin's left edge. A seam is 0.4 wide and 0.25 deep, a
    # fifth of the 2.0 pin, so the pin's flat foot spans it; and tilted toward the room the pin's lowest point
    # is on the line under its centre, which stays clear of the seam even with the pin 0.35 to one side in its
    # hole. So what is cut there must be exactly the seams, and each must keep clear of that line
    tx0, tx1, ty0 = s.AXIS_X - s.PIN_HOLE_D / 2, s.AXIS_X + s.PIN_HOLE_D / 2, s.YF + s.WT + s.FIT + 0.001
    seams = [sm for sm in s.floor_seams() if sm[1] > tx0 and sm[0] < tx1 and sm[3] > ty0 and sm[2] < -43.0]
    seam_cut = [s.box(max(sm[0], tx0), min(sm[1], tx1), max(sm[2], ty0), min(sm[3], -43.0), s.ZF - 0.25, s.ZF)
                for sm in seams]
    seam_v = sum(b.volume() for b in seam_cut)
    off_seam = (tr - fl - s.union(seam_cut)).volume() if seams else missing
    pin_line = (s.AXIS_X - 0.35, s.AXIS_X + 0.35)
    seam_clear = min([max(sm[0] - pin_line[1], pin_line[0] - sm[1]) for sm in seams] or [99.0])
    seam_w = max([sm[1] - sm[0] for sm in seams] or [0.0])
    where = (f": the seam at x {', '.join(f'{(sm[0] + sm[1]) / 2:.3f}' for sm in seams)}, {seam_w:.1f} mm wide, "
             f"{missing:.4f} mm3, {seam_clear:.3f} mm clear of the line under the pin's centre with the pin 0.35 to "
             f"either side" if seams else "")
    report(off_seam < 1e-6 and abs(missing - seam_v) < 1e-6 and seam_w <= s.PIN_D / 5 + 1e-9 and seam_clear > 0.1,
           f"the floor is solid at the top of the deck over the trench's width from the pocket wall (y "
           f"{s.YF + s.WT + s.FIT:.3f}) into the room but for its sheet seams ({off_seam:.6f} mm3 cut besides; "
           f"{len(seams)} seam{where}): no groove for the pin")
    H = s.DOOR_H + s.PIN_BOTTOM_LEN
    lo_, hi_ = 0.0, 2.0
    for _ in range(14):
        mid = (lo_ + hi_) / 2
        mm, _ = tilt_matrix(None, mid, s.DOOR_TOP_GAP - 0.05, s.door_to_cabin(0))
        if overlap(door.transform(mm), fl) > 1e-6:
            hi_ = mid
        else:
            lo_ = mid
    mm, _ = tilt_matrix(None, hi_, s.DOOR_TOP_GAP - 0.05, s.door_to_cabin(0))
    pin_bot = (door ^ s.box(-2, 2, -5, 0, -5, 5)).transform(mm).bounding_box()[2]
    report(hi_ <= 0.8 + 0.01 and pin_bot < s.ZF,
           f"with the wall on the floor, the bottom pin pushed toward the room (lifted 0.55, the most the head allows) "
           f"meets the floor's pocket wall when its centre has moved {hi_:.3f} mm (0.8 at most), its bottom then "
           f"{s.ZF - pin_bot:.3f} mm under the floor top")
    # the reviewer's sweep (cabgar c_fix door2.py): every tilt toward the room 0 to 20 degrees, lift up
    # to what the head allows, top pin sliding 0.35 either way in its hole
    top_c = (s.AXIS_Y, s.ZF + s.DOOR_BOTTOM_GAP + s.DOOR_H)
    head = s.ZF + s.DOOR_OPEN_H
    best = None
    for ddy10 in range(-35, 36):
        ddy = ddy10 / 100
        for t100 in range(0, 2001, 2):
            th = math.radians(t100 / 100)
            lift = min((head - top_c[1]) - 1.0 * math.sin(th), 0.8)
            yc = top_c[0] + ddy + H * math.sin(th)
            zc = top_c[1] + lift - H * math.cos(th)
            zlow = zc - 1.0 * math.sin(th)
            trailing = yc + 1.0 * math.cos(th)
            if zlow >= s.ZF - 1e-9 and (best is None or trailing < best[0]):
                best = (trailing, t100 / 100)
    report(best is not None and best[0] >= -43.81 - 0.01 and best[0] > s.YF + s.WT + s.FIT + 5,
           f"captive: tilted toward the room anywhere from 0 to 20 degrees, the bottom pin's underside clears the floor "
           f"top only with its far edge at y {best[0]:.2f} or more (tilt {best[1]:.1f} degrees), "
           f"{best[0] - (s.YF + s.WT + s.FIT):.1f} mm inside the floor's pocket wall, so it can't get there")
    twin_check(jl, jr)


# =============================================================================================
if group(8, "roof"):
    held = s.union([body, gable])
    for name, half in (("right roof half", right), ("left roof half", left)):
        v = overlap(held, half)
        report(v < 0.01, f"{name} sits on the back gable and the porch gable without cutting into either ({v:.4f} mm3)")
    report(overlap(right, left) < 0.001, "the two roof halves do not overlap at the ridge")
    # resting on both gables all the way along, not only touching them somewhere: lowered 0.02 mm, each roof half
    # must meet each gable's top in every 1 mm of the slope from the ridge out to 45 mm, by 0.02 mm3 or more, 1 mm2
    # of bearing in each mm (roof_rest). (The old test lowered it 0.3 mm, and passed a gable standing 0.25 mm under
    # the roof everywhere but at the peak.)
    rest = {(hn, gn): roof_rest(hn, gn) for hn in ("right", "left") for gn in ("back", "porch")}
    least = min(rest.values(), key=lambda r_: r_[1])
    by_peg = ", beside a peg's hole" if abs(abs(least[2]) - s.PEG_X) < 2 else ""
    report(least[1] >= 0.02,
           f"lowered 0.02 mm, each roof half meets both gables' tops in every 1 mm of the slope from the ridge out to 45 mm, "
           f"so it rests on them all along (least {least[1]:.3f} mm3 in a mm, at x {least[2]:+.1f}{by_peg}; 0.02 "
           f"needed; in all, the right half {rest[('right', 'back')][0]:.2f} on the back gable and "
           f"{rest[('right', 'porch')][0]:.2f} on the porch gable, the left half {rest[('left', 'back')][0]:.2f} and "
           f"{rest[('left', 'porch')][0]:.2f} mm3)")
    for dx, dy, words in ((0, 1.0, "toward the back"), (0, -1.0, "toward the porch"), (1.0, 0, "down the slope")):
        v = overlap(held, right.translate([dx, dy, 0.05]))
        report(v > 0.05, f"slid 1 mm {words}, a roof half is held by its pegs ({v:.2f} mm3)")
    v = overlap(held, right.translate([0, 0, 2.0]))
    report(v == 0, "lifted 2 mm straight up, a roof half is clear of the pegs")
    low = s.union([p["right side"], p["left side"], front, frame])
    v14 = overlap(low, roofs.translate([0, 0, -0.145]))
    v17 = overlap(s.union([p["right side"], p["left side"]]), roofs.translate([0, 0, -0.17]))
    report(v14 < 1e-6 and v17 > 1e-5, f"the side walls, the front wall and the porch frame stay at least 0.15 mm under the roof "
                       f"(lowered 0.145 mm it still clears them: {v14:.6f} mm3; at 0.17 it meets the side walls, {v17:.4f})")


# =============================================================================================
if group(9, "skids"):
    sk = [s.skid().transform(mat) for mat in s.skids_to_cabin()]
    for i, k in enumerate(sk):
        v = overlap(body, k)
        report(v < 0.01, f"skid {i + 1} fits under the floor, the front-wall band in its notch ({v:.4f} mm3)")
        v = overlap(body, k.translate([0, 0, 0.3]))
        report(v > 1, f"skid {i + 1} is really touching the joists ({v:.1f} mm3 when raised 0.3)")
        v = min(overlap(fl, k.translate(t)) for t in ([0.3, 0, 0], [-0.3, 0, 0], [0, 0.3, 0], [0, -0.3, 0]))
        report(v > 0.05, f"skid {i + 1} is held in place by its pegs in the floor ({v:.2f} mm3 when moved 0.3 mm)")
    worst = 1e9
    for sx in (-1, 1):
        cx = sx * s.SKID_X
        rev = np.array([[0, 1, 0, cx - s.SKID_W / 2], [-1, 0, 0, s.L / 2], [0, 0, 1, -(s.SKID_H - s.NOTCH)]], dtype=float)
        worst = min(worst, overlap(fl, s.skid().transform(rev)))
    report(worst > 1, f"turned end for end a skid doesn't fit: it runs {worst:.1f} mm3 into the floor (more than 1)")
    # the front wall rests on the deck, not on a skid: the door sill crosses the +x skid, and its foot stops
    # SILL_UP up in its pocket, so a sill printed a hair long can't lift the wall off the deck there (the Lofted
    # Barn Cabin's fix, review Nov 3 2026). Raised 0.29 the skids still touch none of the front wall
    fw_sk = [overlap(front, k.translate([0, 0, 0.29])) for k in sk]
    sill_a = s.sill_span()
    sill_over = [i + 1 for i, k in enumerate(sk) if min(k.bounding_box()[3], sill_a[1]) > max(k.bounding_box()[0], sill_a[0])]
    sill_foot = (front ^ s.box(sill_a[0] + 0.01, sill_a[1] - 0.01, s.YF - 1, s.YF + s.WT + 1, -1, 3)).bounding_box()[2]
    report(max(fw_sk) < 1e-6 and abs(sill_foot - s.SILL_UP) < 1e-6 and sill_over,
           f"the front wall touches neither skid (raised 0.29: {', '.join(f'{v_:.4f}' for v_ in fw_sk)} mm3): the door "
           f"sill runs over skid {', '.join(map(str, sill_over))} with its foot {sill_foot:.2f} mm up in its pocket, so "
           f"only the floor's band bears there")
    # the front end's mark, measured on the skid: both vertical corners gone (a 0.3 mm probe in each
    # finds nothing), and the cut's legs along the end face and along each side face 0.8 (spec 4.12),
    # at two heights, so it is square to the bed
    k = s.skid()
    peg = (k ^ s.box(0, 6, -1, 5, s.SKID_H - s.NOTCH + 0.5, 20)).bounding_box()
    corners = [overlap(k, s.box(-1, 0.3, y0, y0 + 0.3, -1, 20)) for y0 in (0.0, s.SKID_W - 0.3)]
    legs = []
    for z in (1.0, s.SKID_H - s.NOTCH - 0.5):
        end = (k ^ s.box(-1, 0.001, -1, s.SKID_W + 1, z, z + 0.1)).bounding_box()
        y0_ = (k ^ s.box(-1, 5, -1, 0.001, z, z + 0.1)).bounding_box()
        y1_ = (k ^ s.box(-1, 5, s.SKID_W - 0.001, s.SKID_W + 1, z, z + 0.1)).bounding_box()
        legs += [end[1], s.SKID_W - end[4], y0_[0], y1_[0]]
    report(max(corners) < 1e-6 and all(abs(lg - 0.8) < 0.01 for lg in legs) and peg[0] - max(legs) >= 0.5,
           f"each skid's front end is marked: both corners cut off, the cut {min(legs):.2f} to {max(legs):.2f} mm along the "
           f"end and each side (0.8 meant, 45 degrees), {peg[0] - max(legs):.2f} mm clear of the front peg (0.5 needed)")


# =============================================================================================
if group(10, "plates"):
    tmp = tempfile.mkdtemp(prefix="cabin_check_")
    here = s.HERE
    try:
        shutil.copy(os.path.join(here, "flash studio settings.json"), tmp)
        s.HERE = tmp
        s.write_3mf("1 fit test.3mf", s.fit_plates(p))
        s.write_3mf("2 all plates.3mf", s.all_plates(p, flat))
        with zipfile.ZipFile(os.path.join(tmp, "2 all plates.3mf")) as z:
            cfg = z.read("Metadata/model_settings.config").decode()
            same_settings = z.read("Metadata/project_settings.config") == open(os.path.join(here, "flash studio settings.json"), "rb").read()
    finally:
        s.HERE = here
        shutil.rmtree(tmp, ignore_errors=True)
    # the files in the folder, the ones Alan opens, are what make_cabin.py makes now: make_cabin.py run as
    # it is in a scratch folder (a run of its own, so its pieces are worked out in the same order and the
    # files come out the same to the byte), then every .stl it makes compared byte for byte, no other .stl
    # in the folder, and everything inside both .3mf files the same (the zip's own dates aside). A file
    # left from an older run, or a run that stopped partway, fails here.
    gen = tempfile.mkdtemp(prefix="cabin_gen_")
    stale, made = [], []
    try:
        for f in ("make_cabin.py", "flash studio settings.json"):
            shutil.copy(os.path.join(here, f), gen)
        import subprocess
        run = subprocess.run([sys.executable, os.path.join(gen, "make_cabin.py")], cwd=gen, capture_output=True, text=True)
        made = sorted(f for f in os.listdir(gen) if f.lower().endswith((".stl", ".3mf")))
        for fname in made:
            real, new = os.path.join(here, fname), os.path.join(gen, fname)
            if not os.path.exists(real):
                stale.append(fname)
            elif fname.lower().endswith(".stl"):
                if open(real, "rb").read() != open(new, "rb").read():
                    stale.append(fname)
            else:
                with zipfile.ZipFile(real) as zr, zipfile.ZipFile(new) as zn:
                    if zr.namelist() != zn.namelist() or any(zr.read(m) != zn.read(m) for m in zn.namelist()):
                        stale.append(fname)
        stale += [f for f in sorted(os.listdir(here)) if f.lower().endswith((".stl", ".3mf")) and f not in made]
    finally:
        shutil.rmtree(gen, ignore_errors=True)
    n_stl = sum(1 for f in made if f.lower().endswith(".stl"))
    report(run.returncode == 0 and n_stl == 16 and len(made) == 18 and not stale,
           f"the files in the folder are what make_cabin.py makes now: its {n_stl} .stl files byte for byte, no other "
           f".stl or .3mf, and everything inside both .3mf files"
           + (f" (run make_cabin.py: {', '.join(stale)} out of date or not made by it)" if stale else "")
           + ("" if run.returncode == 0 else f" (make_cabin.py stopped: {run.stderr.strip()[-300:]})"))
    import re
    objs = re.findall(r'<object id="\d+"><metadata key="name" value="([^"]*)"/>(.*?)<part', cfg)
    brim = {name: dict(re.findall(r'<metadata key="([^"]*)" value="([^"]*)"/>', rest)) for name, rest in objs}
    sk_ok = all(brim[n].get("brim_type") == "outer_only" and brim[n].get("brim_width") == "5" for n in brim if n.startswith("skid"))
    nb = [n for n in brim if n.startswith(("porch post", "side railing", "front railing", "porch frame", "roof half", "corner angle"))]
    nb_ok = len(nb) == 3 + 2 + 1 + 1 + 2 + 2 and all(brim[n].get("brim_type") == "no_brim" for n in nb)
    rest_ok = all("brim_type" not in brim[n] for n in brim if n not in nb and not n.startswith("skid"))
    report(sk_ok and nb_ok and rest_ok and same_settings,
           f"in 2 all plates.3mf's model_settings.config the two skids carry outer_only / 5 mm brims, the {len(nb)} posts, "
           f"railings, porch frame, roof halves and angles no_brim, nothing else a brim setting; its project settings are "
           f"flash studio settings.json byte for byte")
    for fname, plates in (("1 fit test.3mf", s.fit_plates(p)), ("2 all plates.3mf", s.all_plates(p, flat))):
        for i, (pname, items) in enumerate(plates):
            placed, fils, names = [], set(), []
            colour_ok, f2_tops, f1_top = True, [], 0.0
            for obj, parts, (x, y), *own in items:
                whole = s.union([m for _, m, _ in parts])
                bb = whole.bounding_box()
                fils |= {f for _, _, f in parts}
                for q in whole.translate([x - bb[0], y - bb[1], -bb[2]]).decompose():
                    placed.append(q)
                    names.append(obj)
                top = bb[5] - bb[2]
                for part_name, m, f in parts:
                    mb = m.bounding_box()
                    if f == 2 and len(parts) > 1:
                        colour_ok &= mb[2] - bb[2] >= top - s.PROUD - 1e-6
                        f2_tops.append(obj)
                    if f == 1:
                        f1_top = max(f1_top, mb[5] - bb[2])
            boxes = [q.bounding_box() for q in placed]
            inside = all(b[0] >= -1e-6 and b[1] >= -1e-6 and b[3] <= BED + 1e-6 and b[4] <= BED + 1e-6 for b in boxes)
            gap, sk_gap, sk_other = BED, BED, BED
            for a_, b_ in itertools.combinations(range(len(placed)), 2):
                A_, B_ = boxes[a_], boxes[b_]
                d = math.hypot(max(B_[0] - A_[3], A_[0] - B_[3], 0), max(B_[1] - A_[4], A_[1] - B_[4], 0))
                d = d if d >= 3 else placed[a_].min_gap(placed[b_], 3.5)
                gap = min(gap, d)
                ska, skb = names[a_].startswith("skid"), names[b_].startswith("skid")
                if ska and skb:
                    sk_gap = min(sk_gap, d)
                elif ska or skb:
                    sk_other = min(sk_other, d)
            two = len(fils) > 1
            tower = all(b[3] <= 162 + 1e-6 or b[4] <= 192 + 1e-6 for b in boxes)
            words = (f"{fname}, plate {i + 1} ({pname}): {len(placed)} parts inside the bed, at least {gap:.2f} mm apart, "
                     + (f"filaments {sorted(fils)}, every part at x <= 162 or y <= 192 (prime tower)" if two
                        else f"filament {min(fils)} only, no prime tower"))
            ok = inside and gap >= 3 - 1e-6 and (not two or tower)
            if sk_gap < BED:
                ok &= sk_gap >= 10.5 and sk_other >= 6.0
                words += f"; the skids {sk_gap:.2f} mm apart and {sk_other:.2f} from anything else"
            if fname.startswith("2"):
                if i in (1, 3):
                    ok &= not two
                else:
                    ok &= two and colour_ok and f1_top <= s.WT + 1e-6
                    need = {"right side", "left side", "door"} if i == 0 else {"back wall", "front wall"}
                    ok &= need <= {o for o, _, _, *_ in items} and set(f2_tops) == (need - {"door"})
                    words += (f"; filament 2 only in the top {s.PROUD} mm of {', '.join(sorted(set(f2_tops)))}, nothing in "
                              f"filament 1 above {f1_top:.3f} mm, so one colour change")
            report(ok, words)
    # which pieces carry a bridge modifier (make_cabin.py, ACROSS_STUDS): the four walls, whose bays laid lengthwise
    # are 66 mm (the right side and the front wall were, in slices of Nov 3 and 4 2026), and the fit test's short walls
    # and doorway, as their real walls; the short front wall's stops on the cripple at x -22.225, as past it, at its cut,
    # the siding would be held at one end only. The porch gable has none: its bays are 15 mm or less every way. The
    # floor carries seven (across_seams), one over each of its six seams, along X at 90 and along Y at 180, and one
    # over the deck's grooves; the fit test's bits of floor none, their grooves are short every way. Every piece that
    # prints lying like a wall is proven, LIKE_WALLS, and every piece cut from the floor, LIKE_FLOORS.
    A, S_ = "bridges across the studs", "bridges across the seams"
    WANT_MODS = {"2 all plates.3mf": {"right side": [A], "left side": [A], "back wall": [A], "front wall": [A],
                                      "floor": [S_] * 7},
                 "1 fit test.3mf": {"short front wall": [A], "short side wall": [A], "doorway": [A]}}
    LIKE_WALLS = {"2 all plates.3mf": ["right side", "left side", "back wall", "front wall", "porch gable"],
                  "1 fit test.3mf": ["short front wall", "short side wall", "doorway", "gable foot", "peg block"]}
    LIKE_FLOORS = {"2 all plates.3mf": ["floor"], "1 fit test.3mf": ["deck corner", "bit of floor"]}
    PL = {"1 fit test.3mf": s.fit_plates(p), "2 all plates.3mf": s.all_plates(p, flat)}
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


# =============================================================================================
if group(11, "fit test"):
    named = dict(p["fit porch"])
    deck = fl ^ s.box(s.FIT_X0, s.W, -s.L, s.FIT_Y1, -5, 50)
    framec = s.porch_frame((s.FIT_PEG_X,)) ^ s.box(s.FIT_FRAME_X0, s.W, -s.L, s.FIT_FRAME_Y1, 0, 200)
    footc = s.porch_gable((s.FIT_PEG_X,)) ^ s.box(s.FIT_FOOT_X0, s.FIT_FOOT_X1, -s.L, 0, s.ZWT - 3, s.ZWT + s.FIT_GABLE_H)
    railc = s.side_railing(1) ^ s.box(0, s.W, -s.L, s.SIDE_RAIL[0] + s.FIT_RAIL, -5, 100)
    real_frame = frame ^ s.box(s.FIT_FRAME_X0, s.W, -s.L, s.FIT_FRAME_Y1, 0, 200)
    vols = [(named["deck corner"].volume(), deck.volume()), (named["frame corner"].volume(), framec.volume()),
            (named["gable foot"].volume(), footc.volume()), (named["railing end"].volume(), railc.volume())]
    same = all(abs(a - b) < 1e-3 for a, b in vols)
    # the moved peg socket is the only change from the real frame corner
    sock = s.box(s.FIT_PEG_X - 1.15, s.FIT_PEG_X + 1.15, -92.146, -89.796, s.ZWT - s.GPEG_SOCKET, s.ZWT)
    diff = abs((real_frame - framec).volume() - sock.volume())
    report(same and diff < 0.01, f"the porch pieces are cut from the real floor, frame, porch gable and railing "
                                 f"(volumes match to {max(abs(a - b) for a, b in vols):.4f} mm3; the frame corner differs "
                                 f"only by its moved peg socket)")
    # and no cut leaves a strip thinner than a line: every island of every layer of every fit-test piece
    # (plates 1 and 2, each lying as it prints) is a 0.42 line wide somewhere, so opening it by half a line
    # leaves something (check Nov 3 2026, as the Lofted Barn Cabin's: the gable foot cut at x 41.0, 0.025
    # short of the siding groove at 41.275, left a strip of siding 0.025 wide at its end in its top layers,
    # which the slicer drops). A layer over a piece's top is empty: it has no islands and is skipped
    thin_n, thin_on, thin_at = 0, [], ""
    for nm, part in p["fit porch"] + p["fit front"]:
        for z0, z1 in layers(part.bounding_box()[5]):
            for isl in part.slice((z0 + z1) / 2).decompose():
                if isl.area() > 1e-9 and isl.offset(-0.21, RND).area() < 1e-6:
                    thin_n += 1
                    if nm not in thin_on:
                        b_ = isl.bounds()
                        thin_on.append(nm)
                        thin_at += (f"; on the {nm} at print z {(z0 + z1) / 2:.2f}, {b_[2] - b_[0]:.3f} x "
                                    f"{b_[3] - b_[1]:.2f} mm at print x {b_[0]:.3f}")
    g_mid = -s.W / 2 + round((s.FIT_FOOT_X0 + s.W / 2) / s.GROOVE_OC) * s.GROOVE_OC
    report(thin_n == 0, f"no fit-test piece's cut leaves a strip thinner than a line: every island of every layer of "
                        f"the {len(p['fit porch']) + len(p['fit front'])} pieces on plates 1 and 2 is 0.42 wide somewhere "
                        f"({thin_n} thinner{thin_at}); the gable foot is cut from x {s.FIT_FOOT_X0:.3f}, "
                        f"{s.FIT_FOOT_X0 - g_mid:+.3f} from the middle of the siding groove at {g_mid:.3f}")
    # put them together in cabin coords: the short post in the corner socket, the frame corner on it,
    # the gable foot on the frame, the railing end in its hole
    sx, xc = 1, s.POST_XS[0]
    stp = s.post_local(s.FIT_POST_BODY).translate([xc, s.POST_Y, s.ZF])
    drop = s.FRAME_Z0 - (s.ZF + s.FIT_POST_BODY)
    fc, gf = framec.translate([0, 0, -drop]), footc.translate([0, 0, -drop])
    prs = [("post in the deck", stp, deck), ("frame on the post", fc, stp), ("gable foot on the frame", gf, fc),
           ("railing end in the deck", railc, deck)]
    seated = max(overlap(a, b) for _, a, b in prs)
    moved = min(min(overlap(a.translate(t), b) for t in ([0.4, 0, 0], [-0.4, 0, 0], [0, 0.4, 0], [0, -0.4, 0]))
                for _, a, b in prs)
    rests = min(overlap(a.translate([0, 0, -0.1]), b) for _, a, b in prs[:3])
    report(seated < 1e-6 and moved > 1e-4 and rests > 1e-3,
           f"together they seat with 0.35 mm round each tenon and peg ({seated:.6f} mm3) and meet their socket walls when "
           f"moved 0.4 mm any way (least {moved:.4f} mm3); post, frame and gable foot rest on each other")
    # and they stand by themselves: the frame corner sits on the one short post's top with nothing else
    # under it, so its centre of mass, and with the gable foot on it theirs, must be over the post's top
    # (review Nov 3 2026: cut at x 33.0 it was 2 mm outside and fell off). 0.4 mm in from every edge
    ptop = (stp ^ s.box(-s.W, s.W, -s.L, s.L, stp.bounding_box()[5] - s.TENON_L - 0.05, stp.bounding_box()[5] - s.TENON_L - 0.01)).bounding_box()
    c_f, v_f = centroid(fc)
    c_g, v_g = centroid(gf)
    c_fg = (c_f * v_f + c_g * v_g) / (v_f + v_g)

    def inside(c):
        return min(c[0] - ptop[0], ptop[3] - c[0], c[1] - ptop[1], ptop[4] - c[1])
    # every socket in the frame corner keeps 0.6 mm of frame round it, the moved peg socket too
    gi = -(s.L / 2 - s.WT)
    fsock = [s.tenon_box(sx, xc, s.FRAME_Z0 - 1, s.FRAME_Z0 + s.SOCKET_D, s.TENON_CLR),
             s.box(s.FIT_PEG_X - s.GPEG_W / 2 - s.TENON_CLR, s.FIT_PEG_X + s.GPEG_W / 2 + s.TENON_CLR, gi - s.GPEG_T - s.TENON_CLR,
                   gi + s.TENON_CLR, s.ZWT - s.GPEG_SOCKET, s.ZWT + 1)]
    wall_missing = 0.0
    for h in fsock:
        bb = h.bounding_box()
        g = s.box(bb[0] - 0.6, bb[3] + 0.6, bb[1] - 0.6, bb[4] + 0.6, max(bb[2] - 0.6, s.FRAME_Z0), min(bb[5] + 0.6, s.ZWT - 0.4))
        wall_missing = max(wall_missing, (g - framec - h).volume())
    report(inside(c_f) >= 0.4 and inside(c_fg) >= 0.4 and wall_missing < 1e-4,
           f"the frame corner stands on the short post by itself: its centre of mass is over the post's top "
           f"(x {ptop[0]:.3f} to {ptop[3]:.3f}, y {ptop[1]:.3f} to {ptop[4]:.3f}), {inside(c_f):.2f} mm in from the nearest "
           f"edge, and with the gable foot on it {inside(c_fg):.2f} (0.4 needed); its two sockets keep 0.6 mm of frame "
           f"round them ({wall_missing:.5f} mm3 missing)")
    fw, sw, fc2 = s.front_corner_test({n: p[n] for n in WALLS}, fl)
    ok = (overlap(fw, sw) < 1e-6 and overlap(fw, fc2) < 1e-6 and overlap(sw, fc2) < 1e-6
          and overlap(fw.translate([0, 0, 0.3]), fc2) > 0.05 and overlap(sw.translate([0, 0, 0.3]), fc2) > 0.05)
    jd = []
    for z in (1.0, s.ZF + 4):                          # the -x corner (re-cut from the standard layout)
        fr = fw.slice(z) ^ rect(-s.W, s.W, s.YF + s.WT - 0.02, s.YF + s.WT)
        sd = sw.slice(z) ^ rect(-s.W, s.W, s.YJ0, s.YJ0 + 0.02)
        jd.append(s.W / 2 + min(fr.bounds()[0], sd.bounds()[0]))
    fwb = fw.bounding_box()
    pk = [sp for sp in s.post_spans("front wall") if fwb[0] <= sp[0] and sp[1] <= fwb[3]]
    pr = [ac for ac in s.prong_spots("front wall") if fwb[0] <= ac <= fwb[3]]
    ok &= fwb[3] < s.DOOR_X - s.JAMB - 2 * s.SW and fwb[0] < -s.W / 2 + 0.01 and len(pk) == 2 and len(pr) == 1
    report(ok and min(jd) >= 0.3, f"the short front corner (the -x one, front wall x {fwb[0]:.3f} to {fwb[3]:.3f}, clear of "
                                  f"the door) goes together like the real one: no overlaps, both walls held down by their "
                                  f"barbs lifted 0.3 mm, the joint {min(jd):.3f} mm in at the groove's bottom; it carries "
                                  f"{len(pk)} closed post pockets (x {', '.join(f'{(a + b) / 2:.3f}' for a, b in pk)}) and "
                                  f"the -x prong")
    dw = s.fit_doorway()
    fd = s.fit_door()
    dh = s.FIT_OPEN_H - s.DOOR_BOTTOM_GAP - s.DOOR_TOP_GAP
    mat0 = s.door_matrix(0, s.FIT_AXIS_X, s.FIT_SILL)
    worst, m_floor, m_head, start = hang_path(fd, dw, mat0, dh, s.FIT_SILL, s.FIT_OPEN_H)
    swing = max(overlap(dw, fd.transform(s.door_matrix(d, s.FIT_AXIS_X, s.FIT_SILL))) for d in range(0, 91, 3))
    stop = overlap(dw, fd.transform(s.door_matrix(-2, s.FIT_AXIS_X, s.FIT_SILL)))
    # and it is hung the same hand as the real door: its pin the same 1.35 in from its doorway's right-hand jamb,
    # its stop on the left-hand jamb, and swung 45 degrees it is in the right-hand side of its doorway
    fj = s.FIT_OPEN_W / 2
    fpb = (fd.transform(mat0) ^ s.box(-s.W, s.W, -s.L, s.L, -5, s.FIT_SILL)).bounding_box()
    fsb = (dw ^ s.box(-fj + 0.01, fj - 0.01, -s.L, s.L, s.FIT_SILL + 10, s.FIT_SILL + 11)).bounding_box()
    f45 = fd.transform(s.door_matrix(45, s.FIT_AXIS_X, s.FIT_SILL)).bounding_box()
    real_in = (s.DOOR_X + s.JAMB) - s.AXIS_X
    fit_in = fj - (fpb[0] + fpb[3]) / 2
    same_hand = (abs(fit_in - real_in) < 1e-3 and abs(fsb[0] - (-fj + 0.01)) < 1e-3 and abs(fsb[3] - (-fj + 0.8)) < 1e-3
                 and f45[0] > -fj + 2 and f45[4] > s.YF + s.WT + 5)
    report(same_hand, f"the fit test's short door hangs the same hand as the real one: its pin {fit_in:.2f} mm in from its "
                      f"doorway's right-hand jamb (the real one's {real_in:.2f}), its stop on the left-hand jamb (x "
                      f"{fsb[0] - 0.01:.2f} to {fsb[3]:.2f}), and swung in 45 degrees it is in the right-hand side of its doorway "
                      f"({f45[0] + fj:.1f} mm from the left-hand jamb at its nearest)")
    report(worst < 0.05 and swing < 0.01 and stop > 0.02,
           f"the fit test's door hangs in its doorway by the same path ({worst:.4f} mm3 worst, 0.05 allowed; {m_floor:.3f} "
           f"over the trench floor; the short door tilts {start:.1f} degrees for the same 2.8 mm, so its top corner comes "
           f"{-m_head:.3f} mm into the head at the start, a rub the top pin's 0.35 play takes up), swings in to 90 degrees "
           f"({swing:.4f} mm3) and meets the stop at -2 ({stop:.3f} mm3)" if m_head < 0 else
           f"the fit test's door hangs in its doorway by the same path ({worst:.4f} mm3 worst, {m_floor:.3f} over the "
           f"trench floor, {m_head:.3f} under the head), swings in to 90 degrees ({swing:.4f} mm3) and meets the stop at "
           f"-2 ({stop:.3f} mm3)")
    blk, cpn = s.peg_block()
    pegpart = blk ^ s.box(-50, 50, 6.01, 50, -1, 50)
    clr = (s.PEG_HOLE_D - s.PEG_D) / 2
    report(pegpart.bounding_box()[2] == 0 and blk.bounding_box()[2] == 0 and abs(clr - 0.4) < 1e-9,
           f"the roof peg lies on the bed (lowest point z = {pegpart.bounding_box()[2]:.2f}) and the coupon's hole goes over "
           f"it with {clr:.2f} mm round")


# =============================================================================================
def extent(piece, region, axis):
    bb = (piece ^ region).bounding_box()
    return bb[axis], bb[axis + 3]


# Alan's standard layout for the 10 ft gable-porch cabin, as the addendum (Nov 3 2026) gives it from
# designer-standards.js on yoder-storage-barns.com: positions in ft from the wall's middle, + to the
# right as seen from in front of the porch. Written out here, not taken from make_cabin.py, so a wrong
# constant there fails the checks below.
STD_DOOR_FT = 1.74          # d36lite F +1.74
STD_FRONT_WIN_FT = -2.57    # w23 F -2.57 (one window)
STD_SIDE_WIN_FT = 0.0       # w23 R 0 and w23 L 0: the middle of each side wall's 16 ft
STD_POSTS_FT = (-(5 - 0.28), -0.3, 5 - 0.28)   # the corner posts (unchanged) and ppost F -0.3
# Alan's answers to read me questions 1 and 2 (Nov 4 2026, "Cabin 93.5 , roof pitch 5/12"), written out here too, as on
# the 12x24 Garage and the 8x12 Side Utility: his 93 1/2 in utility wall, 89 in studs on one 1 1/2 in bottom plate under
# two 1 1/2 in top plates, and his 5/12 roof with a 4 in eave measured level. (The designer draws the cabin's walls 88.8
# in, its roof rising 0.27 x 10 ft, 6.48/12, with 0.42 ft of eave along the slope.) The rake stays the designer's
ALAN_WALL_IN, ALAN_STUD_IN, ALAN_PLATE_IN = 93.5, 89.0, 1.5
ALAN_PITCH, ALAN_EAVE_IN = 5 / 12, 4.0
# the bottom plate the model holds at 1.6 mm for the snaps' legs (spec F4), typed in here, not read from make_cabin.py:
# the read me turns it into inches (a 2 in plate, so 88 1/2 in studs, the front wall's about 88 5/16), and a check
# against the generator's own PLATE_BOT would pass any plate while the read me's numbers went wrong
PLATE_BOT_MM = 1.6
WIDTH_IN = 10 * 12


def column(n, a, u=1.0):
    """The pieces of wall n in a 0.1 mm square column u in from its inside face (1.0: through its framing), at a along
    it, as [(bottom, top)] from the bottom up."""
    axis, sign = s.WALL_SIDE[n]
    c = sign * (s.WALL_FACE[n] - s.WT + u)
    reg = (s.box(c - 0.05, c + 0.05, a - 0.05, a + 0.05, -1, 300) if axis == 0 else
           s.box(a - 0.05, a + 0.05, c - 0.05, c + 0.05, -1, 300))
    return sorted((q.bounding_box()[2], q.bounding_box()[5]) for q in (p[n] ^ reg).decompose() if q.volume() > 1e-9)


if group(12, "sizes against the designer's numbers, Alan's answers and his standard layout, at full size"):
    floor_top = fl.bounding_box()[5]
    # the walls (question 1), measured as they are on the model. The back wall carries the roof, so its plates' top is
    # your 93 1/2 in. The long walls and the front wall stop 0.15 mm under the roof line (group 8), so the roof bears on
    # the gables only: the long walls' top plates are cut 0.15 thinner (roof_clearance), and the front wall's two
    # plates are whole but sit 0.15 lower (wall_top), so its studs are 0.15 shorter. Each wall is sliced 1 mm in from
    # its inside face in the middle of a stud bay: the bottom plate, then nothing up to the top plates (the long walls
    # at y 50.8, between the marks at 44.45 and 57.15; the front wall at x -5, between the stud on the mark at -9.525
    # and the door's full stud; the back wall at x 19.05, between 15.875 and 22.225, under its gable). A long wall's
    # stud at y 44.45 runs in one piece from its post in the floor up through both plates
    gap_in = 0.15 * inch
    cols = [column(n, a_) for n, a_ in (("right side", s.L / 2 - 3.5 * s.OC), ("left side", s.L / 2 - 3.5 * s.OC),
                                        ("front wall", -5.0), ("back wall", 1.5 * s.OC))]
    stud_col, bw = column("right side", s.L / 2 - 4 * s.OC), cols[3]
    whole =all(len(c_) == k for c_, k in zip(cols, (2, 2, 2, 3)))
    tops = [(c_[1][1] - floor_top) * inch if len(c_) > 1 else 0.0 for c_ in cols]
    under = [(c_[1][0] - floor_top) * inch if len(c_) > 1 else 0.0 for c_ in cols]
    plates = [t - u_ for t, u_ in zip(tops, under)]
    model_stud = [(c_[1][0] - c_[0][1]) * inch if len(c_) > 1 else 0.0 for c_ in cols]
    high = [(p[n].bounding_box()[5] - floor_top) * inch for n in ("right side", "left side", "front wall")]
    no_higher = all(len(c_) > 1 and abs(h_ - (c_[1][1] - floor_top) * inch) < 1e-6 for h_, c_ in zip(high, cols))
    plate_in = ALAN_STUD_IN + ALAN_PLATE_IN                     # 90 1/2 in: the top plates' underside
    want = [(plate_in, ALAN_WALL_IN - gap_in)] * 2 + [(plate_in - gap_in, ALAN_WALL_IN - gap_in), (plate_in, ALAN_WALL_IN)]
    want_stud = [w[0] - PLATE_BOT_MM * inch for w in want]      # 88.48 in (88 1/2), the front wall's 88.30 (88 5/16)
    report(whole and no_higher and all(abs(u_ - w[0]) < 0.01 and abs(t - w[1]) < 0.01 for t, u_, w in zip(tops, under, want))
           and all(abs(c_[0][0] - floor_top) < 1e-6 and abs(c_[0][1] - (floor_top + PLATE_BOT_MM)) < 1e-6 for c_ in cols)
           and all(abs(m_ - w_) < 0.01 for m_, w_ in zip(model_stud, want_stud))
           and len(stud_col) == 1 and stud_col[0][0] < floor_top and abs(stud_col[0][1] - cols[0][1][1]) < 1e-6,
           f"walls from the floor to the top of the top plates: the back wall {tops[3]:.2f} in (your {ALAN_WALL_IN} in, "
           f"Nov 4 2026; the designer's 88.8 in), its top plates {under[3]:.2f} to {tops[3]:.2f} in, {plates[3]:.2f} deep. "
           f"The right side, left side and front wall {tops[0]:.2f}, {tops[1]:.2f} and {tops[2]:.2f} in, {gap_in:.2f} in "
           f"(0.15 mm) less, where they stop under the roof line so the roof bears on the gables only: the side walls' top "
           f"plates {under[0]:.2f} to {tops[0]:.2f} in, cut to {plates[0]:.2f} deep, the front wall's whole, {plates[2]:.2f} "
           f"deep, {gap_in:.2f} in lower, {under[2]:.2f} to {tops[2]:.2f}; nothing of those three walls higher (their "
           f"highest points {', '.join(f'{h_:.2f}' for h_ in high)} in). "
           f"{ALAN_STUD_IN:.0f} in studs on a {ALAN_PLATE_IN} in bottom plate: the model's bottom plate is held at "
           f"{PLATE_BOT_MM} mm (typed in; measured {cols[0][0][1] - cols[0][0][0] if cols and cols[0] else 0.0:.3f}), "
           f"{PLATE_BOT_MM * inch:.2f} in, so its studs are {model_stud[0]:.2f} in (the front wall's "
           f"{model_stud[2]:.2f}; wanted {want_stud[0]:.2f} and {want_stud[2]:.2f}), a stud running in one piece from the "
           f"floor through both plates")
    # the back gable band stays at the eave line (question 9's default): its top on the plates' top, measured on the
    # back wall's filament-2 part, which is the band
    band = s.two_colour(p["back wall"], zone)[1].bounding_box()
    band_in = ((band[5] - floor_top) * inch, (band[5] - band[2]) * inch)
    report(abs(band_in[0] - ALAN_WALL_IN) < 0.01 and len(bw) == 3 and abs(band[5] - bw[1][1]) < 1e-6
           and abs(band_in[1] - 3.5) < 0.01,
           f"the back gable band's top is {band_in[0]:.2f} in up, level with the top of the plates (the eave line, "
           f"question 9), {band_in[1]:.2f} in deep (a 1x4)")
    # the roof (question 2): the peak of both gables over the plates' top, the roof's underside measured on a roof half
    # 10 and 40 mm out from the ridge, and the eave measured level out from the long walls' siding face
    z_plates = bw[1][1] if len(bw) > 1 else s.ZWT     # (a wall that fails above has its FAIL there, not a stop here)
    peaks = [(m_.bounding_box()[5] - z_plates) * inch for m_ in (p["back wall"], gable)]
    under_z = [(right ^ s.box(x_ - 0.01, x_ + 0.01, 29.99, 30.01, -1, 300)).bounding_box()[2] for x_ in (10.0, 40.0)]
    pitch = (under_z[0] - under_z[1]) / 30.0
    rb = right.bounding_box()
    face = extent(p["right side"], s.box(s.W / 2 - 3, s.W / 2 + 3, s.L / 2 - 3.5 * s.OC - 0.1,
                                         s.L / 2 - 3.5 * s.OC + 0.1, 40, 40.2), 0)[1]
    eave = (rb[3] - face) * inch
    rake = (rb[4] - s.L / 2) / s.FT
    report(all(abs(r_ - ALAN_PITCH * WIDTH_IN / 2) < 0.01 for r_ in peaks) and abs(pitch - ALAN_PITCH) < 1e-4,
           f"roof {pitch * 12:.3f}/12 measured on a roof half's underside (your 5/12, Nov 4 2026; the designer's 6.48/12): "
           f"both gables peak {', '.join(f'{r_:.2f}' for r_ in peaks)} in over the plates ({ALAN_PITCH * WIDTH_IN / 2:.0f} "
           f"in, 5/12 of half the 10 ft)")
    report(abs(eave - ALAN_EAVE_IN) < 0.01 and abs(rake - 0.45) < 1e-4,
           f"eave {eave:.2f} in out from the side walls' siding, measured level (your 4 in, Nov 4 2026; the designer's "
           f"0.42 ft along the slope), rake {rake:.3f} ft past each gable (the designer's 0.45)")
    face = extent(front, s.box(-6.1, -5.9, -60, -50, 49.9, 50.1), 1)[0]      # plain siding between window and door
    porch = (face - fl.bounding_box()[1]) * inch
    report(abs(porch - 48) < 0.01, f"the front wall's face is {porch:.2f} in back from the floor's front edge (4 ft porch)")
    # the doorway, found on the front wall itself: at u 1.0 and 20 mm up, the widest gap between its
    # framing is the doorway (the stud bays are all under 12 mm)
    yu = s.YF + s.WT - 1.0
    fr20 = scan(front.slice(s.ZF + 20), [yu])[0]
    gl, gr = max(((a[1], b[0]) for a, b in zip(fr20, fr20[1:])), key=lambda g: g[1] - g[0])
    dc = (gl + gr) / 2
    dtop = extent(front, s.box(dc - 0.1, dc + 0.1, yu - 0.05, yu + 0.05, s.ZF + 2, s.ZWT), 2)[0]
    hdr = [m for m in s.framing_plan("front wall")[0] if m[4] == "header" and m[2] < s.ZF + s.DOOR_OPEN_H + 0.01][0]
    kings = [m for m in s.framing_plan("front wall")[0] if m[4] == "king stud" and abs(m[0] - dc) < s.JAMB + 2]
    bear = [min(hdr[1], k[1]) - max(hdr[0], k[0]) for k in kings]
    hdepth = extent(front, s.box(dc - 5.1, dc - 4.9, yu - 0.05, yu + 0.05, dtop - 0.01, dtop + 6), 2)
    report(abs((gr - gl) * inch - 36) < 0.01 and abs((dtop - floor_top) * inch - 75.6) < 0.01
           and abs((hdepth[1] - hdepth[0]) * inch - 5.0) < 0.01 and len(bear) == 2 and all(abs(b * inch - 1.5) < 0.01 for b in bear)
           and abs(dc / s.FT - STD_DOOR_FT) < 1e-4,
           f"door opening {(gr - gl) * inch:.2f} x {(dtop - floor_top) * inch:.2f} in (36 x 75.6), its middle "
           f"{dc / s.FT:+.3f} ft from the front wall's middle, right of it (Alan's standard {STD_DOOR_FT:+.2f}; x {gl:.3f} to "
           f"{gr:.3f}); its header {(hdepth[1] - hdepth[0]) * inch:.2f} in deep (Alan's usual 5 in loft header), bearing "
           f"{', '.join(f'{b * inch:.2f}' for b in bear)} in on the king studs")
    # the windows, found on the walls round the standard layout's own centres
    wins = []
    yu = s.YF + 0.05            # just under the siding face: in front of the sashes, so the opening shows
    for n, a_c in (("front wall", STD_FRONT_WIN_FT * s.FT), ("right side", 2 * s.FT + STD_SIDE_WIN_FT * s.FT),
                   ("left side", 2 * s.FT + STD_SIDE_WIN_FT * s.FT)):
        if n == "front wall":
            reg_lo = s.box(a_c - 15, a_c - 0.1, yu - 0.05, yu + 0.05, s.ZF + 50, s.ZF + 50.2)
            reg_hi = s.box(a_c + 0.1, a_c + 15, yu - 0.05, yu + 0.05, s.ZF + 50, s.ZF + 50.2)
            a0, a1 = extent(p[n], reg_lo, 0)[1], extent(p[n], reg_hi, 0)[0]
            vz = s.box(a_c + 4.9, a_c + 5.1, yu - 0.05, yu + 0.05, s.ZF + 50, s.ZWT)
            vz2 = s.box(a_c + 4.9, a_c + 5.1, yu - 0.05, yu + 0.05, s.ZF, s.ZF + 50)
        else:
            xu = s.WALL_SIDE[n][1] * (s.W / 2 - 0.05)
            reg_lo = s.box(xu - 0.05, xu + 0.05, a_c - 15, a_c - 0.1, s.ZF + 50, s.ZF + 50.2)
            reg_hi = s.box(xu - 0.05, xu + 0.05, a_c + 0.1, a_c + 15, s.ZF + 50, s.ZF + 50.2)
            a0, a1 = extent(p[n], reg_lo, 1)[1], extent(p[n], reg_hi, 1)[0]
            vz = s.box(xu - 0.05, xu + 0.05, a_c + 4.9, a_c + 5.1, s.ZF + 50, s.ZWT)
            vz2 = s.box(xu - 0.05, xu + 0.05, a_c + 4.9, a_c + 5.1, s.ZF, s.ZF + 50)
        top = extent(p[n], vz, 2)[0]
        sill = extent(p[n], vz2, 2)[1]
        wins.append(((a1 - a0) * inch, (top - sill) * inch, (top - floor_top) * inch, (a0 + a1) / 2))
    # and no other window: the front wall's siding line through the windows' height has just two gaps
    # (the window and the doorway), each side wall's one
    n_gaps = []
    for n in ["front wall"] + SIDES:
        axis, sign = s.WALL_SIDE[n]
        c_ = sign * (s.WALL_FACE[n] - 0.42)      # in the siding, over the sashes, under the grooves
        cs = p[n].slice(s.ZF + 50)
        iv = scan(cs.rotate(90), [c_])[0] if axis == 0 else scan(cs, [c_])[0]
        n_gaps.append(sum(1 for a, b in zip(iv, iv[1:]) if b[0] - a[1] > 5))
    ok = all(abs(w - 25.2) < 0.01 and abs(h - 34.8) < 0.01 and abs(t - 76.5) < 0.01 for w, h, t, _ in wins)
    ok &= abs(wins[0][3] / s.FT - STD_FRONT_WIN_FT) < 1e-4
    ok &= all(abs((wins[i][3] - (s.YF + s.L / 2) / 2) / s.FT - STD_SIDE_WIN_FT) < 1e-4 for i in (1, 2))
    ok &= n_gaps == [2, 1, 1]
    report(ok, f"windows {wins[0][0]:.2f} x {wins[0][1]:.2f} in (25.2 x 34.8), tops {wins[0][2]:.2f} in up (76.5); the one "
               f"front window's middle {wins[0][3] / s.FT:+.3f} ft from the middle, left of the door (Alan's standard "
               f"{STD_FRONT_WIN_FT:+.2f}); one window on each side wall, the right side's "
               f"{(wins[1][3] - (s.YF + s.L / 2) / 2) / s.FT:+.3f} ft and the left side's "
               f"{(wins[2][3] - (s.YF + s.L / 2) / 2) / s.FT:+.3f} ft from the middle of the 16 ft wall (both 0); openings "
               f"in the siding at window height: front wall {n_gaps[0]}, right side {n_gaps[1]}, left side {n_gaps[2]} "
               f"(2, 1, 1)")
    # the framing round each window, sliced through the studs 1.0 mm in from the wall's inside face and
    # compared with a plan written out here from the shop's rules, not taken from make_cabin.py: Alan's
    # king stud beside each jamb from the bottom plate up to the head, a full stud outside it up to the
    # top plates, the designer's 2x6 doubled header (5.5 in) across the opening and both kings (so it
    # bears 1.5 in on each), a flat rough sill under the opening, and a cripple on each 16 in mark inside
    # the opening, under the sill and over the header. The band checked runs 0.5 mm past the full studs,
    # from the bottom plate's top to the top plates' underside; the opening itself (the sash) is left
    # out, and "nothing in an opening" in group 3 covers it.
    st, hdr = 1.5 * s.S, 5.5 * s.S                  # a 2x's width; the 2x6 doubled header's depth
    win_w, win_h, win_top = 25.2 * s.S, 34.8 * s.S, 76.5 * s.S
    zb = s.ZF + s.PLATE_BOT                         # the bottom plate's top
    framing_words, framing_ok = [], True
    for n, a_c in (("front wall", STD_FRONT_WIN_FT * s.FT), ("right side", 2 * s.FT + STD_SIDE_WIN_FT * s.FT),
                   ("left side", 2 * s.FT + STD_SIDE_WIN_FT * s.FT)):
        a0, a1 = a_c - win_w / 2, a_c + win_w / 2
        z1 = floor_top + win_top
        z0 = z1 - win_h
        ztp = s.wall_top(n) - 3.0 * s.S             # the double top plate's underside
        # the 16 in layout marks: the front wall's from its -x corner, a side wall's from the back
        mk = [-s.W / 2 + k * 16 * s.S for k in range(12)] if n == "front wall" else [s.L / 2 - k * 16 * s.S for k in range(20)]
        crip = [m for m in mk if m - st / 2 >= a0 - 1e-9 and m + st / 2 <= a1 + 1e-9]
        plan = [(a0 - st, a0, zb, z1), (a0 - 2 * st, a0 - st, zb, ztp),          # -side king, full stud
                (a1, a1 + st, zb, z1), (a1 + st, a1 + 2 * st, zb, ztp),          # +side king, full stud
                (a0 - st, a1 + st, z1, z1 + hdr),                                 # header on both kings
                (a0, a1, z0 - st, z0)]                                            # rough sill
        for m in crip:
            plan += [(m - st / 2, m + st / 2, zb, z0 - st), (m - st / 2, m + st / 2, z1 + hdr, ztp)]
        band = (s.wall_box(n, a0 - 2 * st - 0.5, a1 + 2 * st + 0.5, 0.9, 1.1, zb, ztp)
                - s.wall_box(n, a0, a1, 0, s.WT, z0, z1))
        want = s.union([s.wall_box(n, b0, b1, 0.9, 1.1, c0, c1) for b0, b1, c0, c1 in plan]) ^ band
        got_ = p[n] ^ band
        diff = (got_ - want).volume() + (want - got_).volume()
        # and measured on its own: the header's top over the -side king, the sill's underside 5 mm left of
        # the middle (off the muntin and the marks), and that the king stops under the header
        h_top = extent(p[n], s.wall_box(n, a0 - st / 2 - 0.05, a0 - st / 2 + 0.05, 0.95, 1.05, z1 - 1, ztp - 0.05), 2)[1]
        s_bot = extent(p[n], s.wall_box(n, a_c - 5.05, a_c - 4.95, 0.95, 1.05, zb + 0.05, z0 - 0.5), 2)[0]
        above = extent(p[n], s.wall_box(n, a0 - 2 * st - 0.4, a0 - 0.3, 0.95, 1.05, z1 + hdr + 0.2, z1 + hdr + 0.4),
                       1 - s.WALL_SIDE[n][0])
        k_ok = abs((above[1] - above[0]) - st) < 1e-6 and abs(above[0] - (a0 - 2 * st)) < 1e-6
        ok_n = diff < 1e-4 and abs((h_top - z1) - hdr) < 1e-6 and abs((z0 - s_bot) - st) < 1e-6 and k_ok and len(crip) == 1
        framing_ok &= ok_n
        framing_words.append(f"{n} ({a0:.3f} to {a1:.3f}): header {(h_top - z1) * inch:.2f} in deep, sill "
                             f"{(z0 - s_bot) * inch:.2f} in, over the header only the full stud "
                             f"{(above[1] - above[0]) * inch:.2f} in wide beside the opening, cripples on the mark "
                             f"at {', '.join(f'{m:.3f}' for m in crip)}; {diff:.6f} mm3 off the plan")
    report(framing_ok, "the framing round each window is the shop's (a 1.5 in king stud beside each jamb up to the head, "
                       "a 1.5 in full stud outside it up to the top plates, a 5.5 in 2x6 doubled header across the "
                       "opening bearing 1.5 in on each king, a 1.5 in rough sill, cripples on the 16 in marks inside the "
                       "opening above and below), sliced 1 mm in from the inside face: " + "; ".join(framing_words))
    pcb = sorted([pt.bounding_box() for pt in posts.values()], key=lambda b: b[0])
    pc = [(b[0] + b[3]) / 2 / s.FT for b in pcb]
    py = [((b[1] + b[4]) / 2 + s.L / 2) / s.FT for b in pcb]
    report(len(pc) == 3 and all(abs(a - b) < 1e-4 for a, b in zip(pc, STD_POSTS_FT)) and all(abs(y - 0.2) < 1e-6 for y in py),
           f"{len(pc)} posts, at {', '.join(f'{x:+.3f}' for x in pc)} ft from the middle (Alan's standard: a corner post "
           f"0.28 ft in from each side and one middle post at -0.30), all {py[0]:.2f} ft back from the front edge (0.2)")
    rt = (rail_set.bounding_box()[5] - s.ZF) / s.FT
    report(abs(rt - 2.88) < 1e-6, f"railings {rt:.2f} ft ({rt * 12:.1f} in) tall above the deck (2.88 ft)")
    vf = s.gable_vent(1)[0][0].bounding_box()
    vw_, vh_ = (vf[3] - vf[0]) / s.FT, (vf[5] - vf[2]) / s.FT
    vd = (s.ZPK - (vf[2] + vf[5]) / 2) / s.FT
    report(abs(vw_ - 1.12) < 1e-6 and abs(vh_ - 0.76) < 1e-6 and abs(vd - 0.92) < 1e-6,
           f"vents {vw_:.2f} x {vh_:.2f} ft, centred {vd:.2f} ft under the ridge (1.12 x 0.76, 0.92)")
    inside = (s.W / 2 - (s.SKID_X - s.SKID_W / 2)) * inch
    centre = (s.W / 2 - s.SKID_X) * inch
    report(abs(inside - 30) < 0.01, f"skid inside faces {inside:.2f} in in from the outside walls (ASSUMED, the 10x16 "
                                    f"lesson's 30 in); the designer's table puts the centre 30 in in, this model "
                                    f"{centre:.2f} in")
    sm = [b - a for a, b in zip(sorted(s.marks("front wall")), sorted(s.marks("front wall"))[1:])]
    sj = [a - b for a, b in zip(s.joist_ys(), s.joist_ys()[1:]) if a - b < 20]
    stud = (s.framing_plan("right side")[0][-1][1] - s.framing_plan("right side")[0][-1][0]) * inch
    report(all(abs(x * inch - 16) < 1e-6 for x in sm + sj) and abs(stud - 1.5) < 1e-6,
           f"stud and joist marks {sm[0] * inch:.1f} in apart, studs and joists {stud:.2f} in wide")
    report(abs(s.ANGLE_REACH * inch - 3.78) < 0.01, f"corner angles cover {s.ANGLE_REACH * inch:.2f} in of each wall "
                                                    f"({s.ANGLE_REACH} mm; open question 12)")
    # 20. layer lines
    lip = (frame ^ s.box(-1, 1, s.FRAME_IN + 0.2, s.FRAME_IN + 0.6, -1, 200)).bounding_box()
    sock = (fl ^ s.box(s.POST_XS[0] - 0.05, s.POST_XS[0] + 0.05, s.POST_Y - 0.05, s.POST_Y + 0.05, -1, 50)).bounding_box()
    srp = s.to_print(s.SIDE_RAIL_TO_PRINT, [p["side railing"]])[0]
    rail_d = (p["side railing"] ^ s.box(-s.W, s.W, -80, -79.9, s.ZF + 2.5, s.ZF + 3)).bounding_box()
    gpeg = (gable ^ s.box(s.PEG_X - 0.5, s.PEG_X + 0.5, -s.L, s.L, s.ZWT - 1.4, s.ZWT - 0.1)).bounding_box()
    vals = [("porch frame", s.to_print(s.FRAME_TO_PRINT, [frame])[0].bounding_box()[5]),
            ("ceiling lip", lip[5] - lip[2]),
            ("post", s.to_print(s.POST_TO_PRINT, [p["post"]])[0].bounding_box()[5]),
            ("tenon", s.TENON_T), ("deck socket", s.ZF - sock[5]), ("railing rails", rail_d[3] - rail_d[0]),
            ("railing cap", srp.bounding_box()[5]), ("ceiling", ceiling.bounding_box()[5] - ceiling.bounding_box()[2]),
            ("porch gable peg", gpeg[4] - gpeg[1]), ("corner angle", s.angle_prints()[0].bounding_box()[5]),
            ("recess floor as printed", printed_top(s.WT - s.POCKET_D)), ("vent floor", s.WT - s.VENT_DEPTH),
            ("prong stop", s.STOP_U), ("door stop's underside", s.STOP[0][1]),
            ("door pin holes' lowest point", s.DOOR_AXIS_U - s.PIN_HOLE_D / 2)]
    report(all(on_layer(v) for _, v in vals),
           "on layer lines: " + ", ".join(f"{n} {v:.2f}" for n, v in vals))

print()
print("all checks passed" if fails == 0 else f"{fails} check(s) failed")
sys.exit(1 if fails else 0)
