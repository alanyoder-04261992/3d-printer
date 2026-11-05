"""Checks the garage model fits together before anything is printed.

Run:  python3 check_garage.py      (needs: pip install manifold3d numpy shapely; about 4 to 7 minutes)
Each line says what it proved, with the numbers it measured. Anything that fails is marked FAIL,
and the script ends with exit code 1. The groups follow the four new models' shared order: 1
pieces and bed, 2 snap joints, 3 walls print, 4 corners, 5 gables and vents, 6 the roll-up (the
lift-out curtain, spec_rollup.md L.6: the part, its seat, how it holds, its lift window, taking it
out and putting it back, as drawn and as printed), 7 the steel door, 8 roof, 9 skids, 10 plates,
11 fit test, 12 sizes against the shop numbers.
"""

import itertools
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

import manifold3d as m3
import numpy as np
import shapely
from shapely.geometry import Polygon as SPoly, box as sbox

import make_garage as s

M = m3.Manifold

BED = 220.0
fails = 0


def report(ok, words):
    global fails
    fails += 0 if ok else 1
    print(("ok   " if ok else "FAIL ") + words)


def group(title):
    print()
    print(title)


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


def print_part(piece, mat, region):
    """The part of a piece inside region (garage coords), where it lies in the piece's print."""
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
    return max((z1 for z0, z1 in layers(h + 1) if (z0 + z1) / 2 < h), default=0.0)


def printed_in_shed(piece, mat, region):
    """as_printed() of the part of a piece inside region (garage coords), printed lying the way
    mat lays it on the bed, and put back where it goes in the garage."""
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


def bridges_across(piece, ang, z_from, step=0.2, limit=20, reach=None):
    """The bridges of every layer over z_from laid the way a fixed bridge direction lays them: straight lines at ang
    degrees on the bed (0 along X), each held at both ends. Returns (the worst layer's area hanging out more than 45
    degrees that such lines of limit (20) mm or less don't hold, mm2; the longest such line, mm). reach: how far a
    layer may stand out past the one under it and still be held (None: 45 degrees; 0: anything not printed under it)."""
    bb = piece.bounding_box()
    worst, longest, prev, z_prev = 0.0, 0.0, None, 0.0
    for z0, z1 in layers(bb[5]):
        zm = (z0 + z1) / 2
        cs = piece.slice(zm)
        if prev is not None and zm > z_from:
            sup = prev.offset(1.1 * (zm - z_prev) if reach is None else reach, RND)
            free = cs - sup
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


def longest_strand(piece, z_from, step=0.2):
    """Over every layer above z_from, the longest straight run, in any direction (every degree), across what hangs out
    more than 45 degrees: whichever way the slicer lays its bridges there, none crosses more than this over nothing."""
    bb = piece.bounding_box()
    best, prev, z_prev = 0.0, None, 0.0
    for z0, z1 in layers(bb[5]):
        zm = (z0 + z1) / 2
        cs = piece.slice(zm)
        if prev is not None and zm > z_from:
            free = cs - prev.offset(1.1 * (zm - z_prev), RND)
            if free.area() >= 0.01:
                for ang in range(180):
                    f = free.rotate(-ang)
                    b = f.bounds()
                    for runs in scan(f, np.arange(b[1] + step / 2, b[3], step)):
                        if len(runs):
                            best = max(best, float(np.max(runs[:, 1] - runs[:, 0])))
        prev, z_prev = cs, zm
    return best


def slot_strand(piece, r=0.3, step=0.2):
    """Over every layer, the longest straight run, in any direction (every degree), along a gap in the layer under it
    narrower than 2 r (0.6 mm): a slot like a floor sheet seam. A 45 degree overhang reaches across it from both sides,
    so the proofs above don't see it, but the slicer bridges it, and may lay the bridge along it. Slivers under 0.05 mm
    wide on average (where the closing meets a stepped edge) are not slots and are left out."""
    bb = piece.bounding_box()
    best, prev = 0.0, None
    for z0, z1 in layers(bb[5]):
        cs = piece.slice((z0 + z1) / 2)
        if prev is not None:
            gaps = [g for g in (cs ^ (prev.offset(r, RND).offset(-r, RND) - prev)).decompose()
                    if g.area() >= 0.05 * max(g.bounds()[2] - g.bounds()[0], g.bounds()[3] - g.bounds()[1])]
            if gaps and sum(g.area() for g in gaps) >= 0.01:
                gap = m3.CrossSection.batch_boolean(gaps, m3.OpType.Add)
                for ang in range(180):
                    f = gap.rotate(-ang)
                    b = f.bounds()
                    for runs in scan(f, np.arange(b[1] + step / 2, b[3], step)):
                        if len(runs):
                            best = max(best, float(np.max(runs[:, 1] - runs[:, 0])))
        prev = cs
    return best


def groove_run(piece, ang, region, step=0.2):
    """On a floor's second layer, the one over its seams and grooves: the longest stretch of what hangs free of its
    first (all the first doesn't hold, allow 0) inside region (what a modifier reaches: its solid, or the piece inside
    its outline, as its section there) that one straight line at ang degrees on the bed (0 along X) runs over, held at
    its ends or not, mm. A box lays its bridges across its groove, the short way, when this is shorter at its own angle
    than at right angles to it (the cabins' check, the same lines)."""
    (a0, a1), (b0, b1) = layers(1.0)[:2]
    zm = (b0 + b1) / 2
    free = (piece.slice(zm) - piece.slice((a0 + a1) / 2)) ^ region.slice(zm)
    if free.area() < 1e-4:
        return 0.0
    f = free.rotate(-ang)
    b = f.bounds()
    return max([x1 - x0 for fi in scan(f, np.arange(b[1] + step / 2, b[3], step)) for x0, x1 in fi] + [0.0])


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


def sweep(piece, others, path):
    """The worst overlap of piece with others at each step of a path of moves."""
    return max(overlap(piece.translate(t), others) for t in path)


def on_line(h):
    """Is h on a layer line of a print (0.25, then every 0.2)?"""
    k = (h - 0.25) / 0.2
    return h > 0 and abs(k - round(k)) < 1e-9 / 0.2


def least_web(cs, lo=0.2, hi=3.0, tol=2e-3):
    """The narrowest bit of a section: the widest w for which opening it (in by w/2 and back out,
    square corners kept) takes off less than tol mm2."""
    for _ in range(16):
        mid = (lo + hi) / 2
        gone = (cs - cs.offset(-mid / 2, MIT, 2).offset(mid / 2, MIT, 2)).area()
        lo, hi = (mid, hi) if gone < tol else (lo, mid)
    return lo


def square(u0, u1, v0, v1):
    return m3.CrossSection.square([u1 - u0, v1 - v0]).translate([u0, v0])


def mesh_pts(m):
    return np.asarray(m.to_mesh().vert_properties)[:, :3]


C0 = s.L / 2 - s.WT              # the roll-up end's inside face is at y = -C0; u = -y - C0 out from it
T_SEC = np.array([[0, -1, 0, -C0], [0, 0, 1, 0], [-1, 0, 0, 0]], dtype=float)    # (x, y, z) -> (u, z, -x)
T_BED = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, -C0]], dtype=float)     # (x, y, z) -> (x, z, u)
BED_BACK = np.array([[1, 0, 0, 0], [0, 0, -1, -C0], [0, 1, 0, 0]], dtype=float)  # its inverse
FLOOR_BED = np.array([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, s.ZF]], dtype=float)   # the floor upside down (self-inverse)


p = s.build()
body, roof, door, fl = p["body"], p["roof"], p["door"], p["floor"]
WALLS = list(s.WALL_CUTS)
LONGS, ENDS = list(s.LONG_WALLS), list(s.END_WALLS)
zone = s.trim_zone()
flat = {n: s.wall_parts(p, n, zone) for n in WALLS}
angle_flat = s.angle_prints()
angles = {c: s.corner_angle(*c) for c in s.CORNERS}
skids = s.skid_parts()
PL = s.plates(p)
inch = 1 / s.S


def corner_name(sx, sy):
    return f"({'+' if sx > 0 else '-'},{'+' if sy > 0 else '-'})"


# ======================================================================== 1
group("1. Pieces and bed")
fit_items = [(f"fit test {pn}: {obj}", parts[0][1]) for pn, items in PL["1 fit test.3mf"] for obj, parts, *_ in items]
for name, part, expect in ([("floor", s.to_print(s.FLOOR_TO_PRINT, [fl])[0], 1)] +
                           [(n, s.union(flat[n]), 1) for n in WALLS] +
                           [("roof half", s.roof_to_print(roof), 1)] +
                           [("corner angle " + corner_name(*c), a, 1) for c, a in zip(s.CORNERS, angle_flat)] +
                           [("door", s.to_print(s.DOOR_TO_PRINT, [door])[0], 1), ("skids.stl", p["skids"], 4)] +
                           [("roll-up curtain", s.to_print(s.CURTAIN_TO_PRINT, [p["curtain"]])[0], 1)] +
                           [(n, m, 1) for n, m in fit_items]):
    bb = part.bounding_box()
    size = (bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2])
    pieces = len(part.decompose())
    report(pieces == expect and max(size[0], size[1]) <= BED and size[2] <= BED,
           f"{name}: {pieces} solid piece(s) (expected {expect}), {size[0]:.2f} x {size[1]:.2f} x {size[2]:.2f} mm, "
           f"fits the {BED:.0f} mm bed")
pieces = [fl] + [p[n] for n in WALLS]
v = abs(body.volume() - sum(x.volume() for x in pieces))
report(v < 0.01, f"floor and four walls add up to the whole body ({v:.5f} mm3 left over)")
worst = max(overlap(a, b) for i, a in enumerate(pieces) for b in pieces[i + 1:])
report(worst < 0.001, f"no two of them overlap ({worst:.5f} mm3)")
wall_set = s.union([p[n] for n in WALLS])
v = max(overlap(fl.translate([dx, dy, 0]), wall_set) for dx, dy in ((0.14, 0), (-0.14, 0), (0, 0.14), (0, -0.14)))
report(v < 0.0001, f"the walls sit round the floor with {s.FIT} mm round every post and prong and {s.FLOOR_CLR} mm "
                   f"inside the skirts (the floor moved 0.14 mm any way still clears: {v:.5f} mm3)")
# the roll-up curtain seated in its doorway: without its four bumps it overlaps nothing; with them it overlaps by
# their preload, the springs' business (group 6)
_bumps = s.union([s.spring_regions()["finger bumps"], s.spring_regions()["tab bumps"]])
v_nob, v_b = overlap(p["curtain"] - _bumps, body), overlap(p["curtain"], body)
report(v_nob < 0.001 and v_b > 1.0,
       f"the roll-up curtain seated in its doorway, its four spring bumps taken out, overlaps nothing of the body "
       f"({v_nob:.5f} mm3); with them in, {v_b:.2f} mm3, the bumps' preload (spec 2.36)")
# the .stl files as written (32-bit corners): no collapsed triangle, every edge shared by an even number of triangles
STLS = ["floor.stl", "door side.stl", "plain side.stl", "roll-up end.stl", "back end.stl", "roll-up curtain.stl",
        "roof half.stl", "corner angle.stl", "door.stl", "skids.stl", "fit test.stl"]
stl_bad, stl_rows = 0, []
for fn_ in STLS:
    path_ = os.path.join(s.HERE, fn_)
    if not os.path.exists(path_):
        stl_bad += 1
        stl_rows.append(f"{fn_} missing")
        continue
    raw = open(path_, "rb").read()
    n_t = int.from_bytes(raw[80:84], "little")
    rec = np.frombuffer(raw[84:84 + 50 * n_t], dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("x", "<u2")])
    vv, inv_ = np.unique(rec["v"].reshape(-1, 3), axis=0, return_inverse=True)
    tt = inv_.ravel().reshape(-1, 3)
    collapsed = int(np.sum((tt[:, 0] == tt[:, 1]) | (tt[:, 1] == tt[:, 2]) | (tt[:, 0] == tt[:, 2])))
    ed = np.sort(np.concatenate([tt[:, [0, 1]], tt[:, [1, 2]], tt[:, [2, 0]]]), axis=1)
    _, cnt_ = np.unique(ed, axis=0, return_counts=True)
    odd, many = int(np.sum(cnt_ % 2)), int(np.sum(cnt_ > 2))
    stl_bad += collapsed + odd
    if collapsed or odd or many:
        stl_rows.append(f"{fn_} {collapsed} collapsed, {odd} open edges, {many} edges where two bodies touch")
report(stl_bad == 0, f"the {len(STLS)} .stl files, read back as written (32-bit corners): no collapsed triangles and no "
                     f"open edges" + (" (" + "; ".join(stl_rows) + ")" if stl_rows else ""))
def stl_section_area(tri, h):
    """The area of the section at height h of a closed surface given as triangles (n, 3, 3), straight from
    its triangles: each one that crosses h gives a segment, turned the way its outward normal says, and the
    segments' signed area is summed. Nothing is merged or repaired, so it reads a file the way it is."""
    z = tri[:, :, 2] - h
    up = z > 0
    k = up.sum(axis=1)
    sel = (k == 1) | (k == 2)
    T, Z, U = tri[sel], z[sel], up[sel]
    if len(T) == 0:
        return 0.0
    nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    cr, qs = [], []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        c = U[:, i] != U[:, j]
        f = Z[:, i] / np.where(c, Z[:, i] - Z[:, j], 1.0)
        cr.append(c)
        qs.append(T[:, i] + (T[:, j] - T[:, i]) * f[:, None])
    cr, qs = np.stack(cr, axis=1), np.stack(qs, axis=1)
    idx = np.argsort(~cr, axis=1, kind="stable")[:, :2]
    a_ = qs[np.arange(len(T)), idx[:, 0]][:, :2]
    b_ = qs[np.arange(len(T)), idx[:, 1]][:, :2]
    flip = ((b_ - a_) * np.stack([-nrm[:, 1], nrm[:, 0]], axis=1)).sum(axis=1) < 0
    a2, b2 = np.where(flip[:, None], b_, a_), np.where(flip[:, None], a_, b_)
    return float(0.5 * np.sum(a2[:, 0] * b2[:, 1] - b2[:, 0] * a2[:, 1]))


# each .stl holds the very part it is written from (final audit, Nov 4 2026: simplify() before writing had turned two of
# the door side's casing boards into ramps, 21 mm3, with no open edge to show it, and on the Lofted Barn Garage cut wedges
# out of its long walls' studs): its triangles as written summed to a volume, and cut at the middle of every print layer,
# against the part; and each lies inside the bed as one object, its lowest corner on it, the way the read me offers it
STL_FROM = s.stl_parts(p, PL)
dv_worst, da_worst, da_at, stl_rows, bed_worst, bed_rows, stl_ext = 0.0, 0.0, "", [], 0.0, [], {}
for fn_ in STLS:
    path_ = os.path.join(s.HERE, fn_)
    if not os.path.exists(path_) or fn_ not in STL_FROM:
        dv_worst = math.inf
        stl_rows.append(f"{fn_} missing")
        bed_rows.append(f"{fn_} missing")
        continue
    raw = open(path_, "rb").read()
    n_t = int.from_bytes(raw[80:84], "little")
    tri_ = np.frombuffer(raw[84:84 + 50 * n_t], dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("x", "<u2")])["v"]
    tri_ = tri_.astype(float)
    part_ = STL_FROM[fn_]
    dv = abs(np.einsum("ij,ij->i", tri_[:, 0], np.cross(tri_[:, 1], tri_[:, 2])).sum() / 6 - part_.volume())
    da, at_ = 0.0, 0.0
    for z0_, z1_ in layers(part_.bounding_box()[5]):
        h_ = (z0_ + z1_) / 2 + 1e-4
        d_ = abs(stl_section_area(tri_, h_) - part_.slice(h_).area())
        if d_ > da:
            da, at_ = d_, h_
    if dv > 0.02 or da > 0.01:
        stl_rows.append(f"{fn_}: {dv:.3f} mm3 off, {da:.3f} mm2 off at z {at_:.2f}")
    if da > da_worst:
        da_at = f"{fn_} at z {at_:.2f}"
    dv_worst, da_worst = max(dv_worst, dv), max(da_worst, da)
    lo_, hi_ = tri_.reshape(-1, 3).min(axis=0), tri_.reshape(-1, 3).max(axis=0)
    ext = hi_ - lo_
    stl_ext[fn_] = " x ".join(f"{e:.2f}" for e in ext)
    bed_worst = max(bed_worst, ext[0], ext[1], ext[2])
    if max(ext[0], ext[1], ext[2]) > BED or abs(lo_[2]) > 1e-4:
        bed_rows.append(f"{fn_} {stl_ext[fn_]} mm, lowest corner at z {lo_[2]:.3f}")
report(dv_worst <= 0.02 and da_worst <= 0.01,
       f"each of the {len(STLS)} .stl files holds the part it is written from, read back as written: its volume within "
       f"{dv_worst:.4f} mm3 (at most 0.02) and every print layer's section within {da_worst:.4f} mm2 (at most 0.01; "
       f"{da_at}), so a plate set up from the .stl files prints the same pieces as the .3mf files"
       + (" (" + "; ".join(stl_rows) + ")" if stl_rows else ""))
report(not bed_rows, f"each .stl file fits the {BED:.0f} mm bed as it opens, as one object, its lowest corner on "
                     f"the bed (largest size {bed_worst:.2f} mm; corner angle.stl, all four angles, "
                     f"{stl_ext.get('corner angle.stl', 'missing')} mm)"
       + (" (off the bed: " + "; ".join(bed_rows) + ")" if bed_rows else ""))


# ======================================================================== 2
group("2. Snap joints")


def toward(name, d):
    """Move d mm out from the middle of the garage, square to the wall."""
    axis, sign = s.WALL_SIDE[name]
    t = [0.0, 0.0, 0.0]
    t[axis] = sign * d
    return t


def along(name, d):
    t = [0.0, 0.0, 0.0]
    t[1 - s.WALL_SIDE[name][0]] = d
    return t


barb_room = []
for n in WALLS:
    for ac in s.prong_spots(n):
        (a0, a1), _ = s.prong_spans(ac)
        barb_room.append(s.wall_box(n, a0 - s.FIT, a1 + s.FIT, -s.FIT, s.BARB, -1, s.ZF + 1))
fl_open = fl - s.union(barb_room)
ends = s.union([p[n] for n in ENDS])
DROPS = [0.1 * k for k in range(1, 11)] + [1 + 0.5 * k for k in range(1, 59)] + [30 + 2 * k for k in range(1, 56)]
door0 = door.transform(s.door_to_shed(0))
door90 = door.transform(s.door_to_shed(90))
for n in ENDS + LONGS:
    w = p[n]
    v = overlap(w.translate([0, 0, -0.1]), fl)
    report(v > 1, f"{n} stands on the floor (lowered 0.1 mm it runs into it: {v:.1f} mm3)")
    v = overlap(w.translate([0, 0, 0.3]), fl)
    report(v > 0.05, f"{n}: its {len(s.prong_spots(n))} prongs' barbs hold it down (lifted 0.3 mm they meet their "
                     f"ledges: {v:.2f} mm3)")
    vi, vo = overlap(w.translate(toward(n, -0.3)), fl), overlap(w.translate(toward(n, 0.3)), fl)
    va = min(overlap(w.translate(along(n, d)), fl) for d in (0.3, -0.3))
    report(min(vi, vo, va) > 0.05, f"{n}: the floor holds its foot in ({vi:.1f}), out ({vo:.1f}) and along ({va:.1f} "
                                   f"mm3 when moved 0.3 mm)")
    others = fl_open if n in ENDS else s.union([fl_open, ends])
    worst = sweep(w, others, [[0, 0, dz] for dz in DROPS])
    extra = ""
    if n == "door side":
        worst = max(worst, sweep(door0, others, [[0, 0, dz] for dz in DROPS]),
                    sweep(door90, others, [[0, 0, dz] for dz in DROPS]))
        extra = ", with its door hung, shut or swung in to 90 degrees"
    report(worst < 0.001, f"{n} goes on straight down from {DROPS[-1]:.0f} mm "
                          f"up{' between the end walls' if n in LONGS else ' onto the bare floor'}{extra}, nothing in "
                          f"the way but the barbs ({worst:.5f} mm3)")
v = max(overlap(door0, s.union([fl] + [p[n] for n in WALLS])), overlap(door90, s.union([fl] + [p[n] for n in WALLS])))
report(v < 0.01, f"seated, the hung door touches nothing, shut or swung in to 90 degrees ({v:.5f} mm3)")
leg = s.LEG_ROOT - (s.LEDGE_Z - s.FIT)
strain = 1.5 * s.PRONG_T * s.CATCH / leg ** 2
room = s.SLOT_U - (s.BARB + s.PRONG_T + s.CATCH)
report(strain < 0.02 and room >= 0.25 - 1e-9,
       f"each prong leg bends {s.CATCH:.2f} mm to let its barb through: {strain * 100:.2f}% strain on a {leg:.2f} mm "
       f"leg {s.PRONG_T} mm thick (PLA takes about 2%), with {room:.2f} mm to spare in its slot")
for n in WALLS:
    region = s.union([s.wall_box(n, s.prong_slot(ac)[0] - 1, s.prong_slot(ac)[1] + 1, -1, s.SD, -1, s.ZF + 1)
                      for ac in s.prong_spots(n)])
    pw = printed_in_shed(p[n], s.WALL_TO_PRINT[n], region)
    pf = printed_in_shed(fl, s.FLOOR_TO_PRINT, region)
    rest = overlap(pw, pf)
    held = overlap(pw.translate([0, 0, 0.3]), pf)
    res = []
    for ac in s.prong_spots(n):
        (a0, a1), _ = s.prong_spans(ac)

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
        top = (pw ^ s.wall_box(n, a0 + 0.5, a1 - 0.5, -1, s.BARB - s.FIT - 0.05, -1, s.ZF - 1)).bounding_box()[5]
        ledge = (pf ^ s.wall_box(n, a0 + 0.5, a1 - 0.5, 0.05, s.BARB - s.FIT - 0.05, -1, s.ZF)).bounding_box()[2]
        res.append((catch, catch - play, ledge - top))
    out_catch = min(r[1] for r in res)
    gaps = [r[2] for r in res]
    report(rest < 0.01 and held > 0.05 and out_catch >= 0.29 and min(gaps) > 0 and max(gaps) < 0.45,
           f"{n} as printed: each barb reaches {min(r[0] for r in res):.2f} mm under its ledge ({out_catch:.2f} with "
           f"the foot pushed out against its stop), with {min(gaps):.2f} to {max(gaps):.2f} mm over it to spring in; "
           f"lifted 0.3 mm the printed barbs catch ({held:.2f} mm3), and seated nothing rubs ({rest:.4f} mm3)")
# every leg free from the barb up to LEG_ROOT: nothing of the wall within 0.15 of its four faces
# (the relief round it is 0.2), and the plate or the curtain really is there just past the relief
for n in WALLS:
    worst, ring_min, leg_min = 0.0, 1e9, 1e9
    for ac in s.prong_spots(n):
        (a0, a1), _ = s.prong_spans(ac)
        z0, z1 = s.ZF - 0.5 + 0.01, s.LEG_ROOT - 0.01
        legb = s.wall_box(n, a0, a1, s.BARB, s.BARB + s.PRONG_T, z0 - 1, z1 + 1)
        near = s.wall_box(n, a0 - 0.15, a1 + 0.15, s.BARB - 0.15, s.BARB + s.PRONG_T + 0.15, z0, z1) - legb
        worst = max(worst, overlap(p[n], near))
        ring = (s.wall_box(n, a0 - 0.35, a1 + 0.35, s.BARB - 0.35, s.BARB + s.PRONG_T + 0.35, s.ZF + 0.05, z1)
                - s.wall_box(n, a0 - 0.25, a1 + 0.25, s.BARB - 0.25, s.BARB + s.PRONG_T + 0.25, s.ZF - 1, z1 + 1))
        ring_min = min(ring_min, overlap(p[n], ring) / ring.volume())
        lb = s.wall_box(n, a0, a1, s.BARB, s.BARB + s.PRONG_T, z0, z1)
        leg_min = min(leg_min, overlap(p[n], lb) / lb.volume())
    report(worst < 1e-4 and ring_min > 0.95 and leg_min > 0.999,
           f"{n}: each of its {len(s.prong_spots(n))} legs is free to LEG_ROOT ({s.LEG_ROOT - s.ZF:.1f} over the floor "
           f"top): nothing within 0.15 of its faces from ZF - 0.5 up ({worst:.6f} mm3), the leg whole "
           f"({leg_min * 100:.1f}%), and the bottom plate solid just past the relief ({ring_min * 100:.0f}%)")
# the floor between its cuts, on sections at z 0.5, 3 and 6 (under the sheet seams): between two cuts
# (or a cut and the floor's edge) at least 0.6, and from a cut to a joist cavity at least 0.42
xf, yf = s.W / 2 - s.TS - s.FLOOR_CLR, s.L / 2 - s.TS - s.FLOOR_CLR
whole = s.box(-xf, xf, -yf, yf, 0, s.ZF)
cut_all = s.union(s.floor_cuts())
webs_c, webs_j = [], []
for z in (0.5, 3.0, 6.0):
    webs_c.append(least_web((whole - cut_all).slice(z)))
    webs_j.append(least_web(fl.slice(z)))
report(min(webs_c) >= 0.6 and min(webs_j) >= 0.42,
       f"the floor keeps at least {min(webs_c):.2f} mm between any two of its cuts (notches, prong and stop slots, "
       f"corner cuts, skid peg holes) and {min(webs_j):.2f} mm from a cut to a joist cavity, on sections at z 0.5, 3 "
       f"and 6 ({', '.join(f'{a:.2f}/{b:.2f}' for a, b in zip(webs_c, webs_j))})")
joists = [(j - s.SW / 2, j + s.SW / 2) for j in s.joist_ys()]
bad = [(n, ac) for n in LONGS for ac in s.prong_spots(n)
       if any(s.prong_slot(ac)[1] > j0 and s.prong_slot(ac)[0] < j1 for j0, j1 in joists)]
bad += [(n, ac) for n in ENDS for ac in s.prong_spots(n) if s.L / 2 - s.WT + s.BARB - s.FIT < joists[-1][1]]
gap_j = min(min(abs(j0 - s.prong_slot(ac)[1]), abs(s.prong_slot(ac)[0] - j1))
            for n in LONGS for ac in s.prong_spots(n) for j0, j1 in joists)
report(not bad, f"every prong slot is between floor joists ({gap_j:.2f} mm at the closest along the long walls; "
                f"the end walls' slots are in the end bands, past the last joist)")
# the roll-up end (spec_rollup.md E.5, F): its two prongs moved under the jambs, legs rooted in the bottom plate with
# a line of plate kept between each relief and the doorway; no posts under the jambs now (their slots are there);
# the curtain posts at the middle, 16 and 35 in each way, each in a notch 0.2 round; the floor's webs round them
ru_ = p["roll-up end"]


def runs_on_ru(piece, u, z, x0=-46.0, x1=46.0, d=0.02):
    """[(x0, x1)] of a piece along the roll-up end's line at (u, z), low x first."""
    return sorted((b[0], b[3]) for b in (q.bounding_box() for q in
                                         (piece ^ s.ru_box(x0, x1, u - d, u + d, z - d, z + d)).decompose()))


plate_left, webs, no_jamb = [], [], 0.0
for sg in (1, -1):
    rr = runs_on_ru(ru_, 1.58, (s.ZF + s.LEG_ROOT) / 2, *sorted([sg * 33.0, sg * 37.0]))
    edge = [r for r in rr if abs(abs(r[0] if sg > 0 else r[1]) - s.RU_W / 2) < 0.01]
    plate_left.append((edge[0][1] - edge[0][0]) if edge else 0.0)
    fr = runs_on_ru(fl, 0.804, 1.5, *sorted([sg * 18.0, sg * 46.0]))

    def run_at(x, fr=fr):
        hit = [b - a for a, b in fr if a <= x <= b]
        return hit[0] if hit else 0.0
    webs.append((run_at(sg * 23.2), run_at(sg * 30.0), run_at(sg * 40.2)))
    no_jamb += overlap(ru_, s.ru_box(*sorted([sg * 33.9, sg * 34.45]), 0, s.SD, 0, s.ZF - 0.6))
    fslab = runs_on_ru(fl, 1.0, 3.0, *sorted([sg * 33.9, sg * 34.45]))
    no_jamb += 0.0 if (len(fslab) == 1 and fslab[0][1] - fslab[0][0] > 0.54) else 1.0
posts_w = [((a + b) / 2, b - a) for a, b in runs_on_ru(ru_, 2.0, 3.0, -30, 30)]
fr2 = runs_on_ru(fl, 2.0, 3.0, -30, 30)
notches_f = [((a[1] + b[0]) / 2, b[0] - a[1]) for a, b in zip(fr2, fr2[1:])]
targets = sorted(s.CURTAIN_POSTS)
posts_ok = (len(posts_w) == 5 and len(notches_f) == 5
            and all(abs(c - t) < 1e-3 and abs(w - s.SW) < 1e-3 for (c, w), t in zip(posts_w, targets))
            and all(abs(c - t) < 1e-3 and abs(w - s.SW - 2 * s.FIT) < 1e-3 for (c, w), t in zip(notches_f, targets)))
report(min(plate_left) >= 0.42 and min(min(w) for w in webs) >= 0.6 and no_jamb < 1e-9 and posts_ok
       and list(s.PRONGS["roll-up end"]) == [-36.2, 36.2],
       f"the roll-up end's two prongs are under the jambs at x {', '.join(f'{a:+.1f}' for a in s.prong_spots('roll-up end'))}, "
       f"each leg's relief keeping {min(plate_left):.3f} mm of bottom plate beside the doorway (at least a 0.42 line); no "
       f"post under either jamb, the floor whole there; posts under the curtain at "
       f"{', '.join(f'{c:+.3f}' for c, _ in posts_w)} ({', '.join(f'{c * inch:+.0f}' for c, _ in posts_w)} in), each "
       f"{posts_w[0][1]:.3f} wide in a {notches_f[0][1]:.3f} notch; the floor's webs from each post notch at 35 in to the "
       f"inner skid's peg hole {min(w[0] for w in webs):.2f}, from it to the prong slot {min(w[1] for w in webs):.2f}, and "
       f"from the slot to the end stud's notch {min(w[2] for w in webs):.2f} mm (spec 1.60, 9.08, 1.41; at least 0.6)")


# ======================================================================== 3
group("3. Walls print")
for n in WALLS:
    siding, trim_p = flat[n]
    whole = s.union(flat[n])
    bb = whole.bounding_box()
    foot = whole.trim_by_plane([0, 0, -1], -0.2)
    fbb = foot.bounding_box()
    report(fbb[3] - fbb[0] > (bb[3] - bb[0]) - 2 * (s.WT + s.PROUD) - 0.1 and fbb[4] - fbb[1] > 0.9 * (bb[4] - bb[1]),
           f"{n} lies flat on its framing ({foot.volume() / 0.2:.0f} mm2 on the bed, "
           f"{fbb[3] - fbb[0]:.1f} of {bb[3] - bb[0]:.1f} long)")
    worst, longest = worst_overhang(whole)
    report(worst < 5, f"{n} has nothing steeper than 45 degrees that isn't a bridge of 20 mm or less, nothing starting "
                      f"in mid-air ({worst:.2f} mm2 worst layer; bridges up to {longest:.1f} mm)")
    thin = max((c - c.offset(-0.2, RND).offset(0.2, RND)).area() for c in (whole.slice(0.125), whole.slice(0.35)))
    report(thin < 2, f"{n}: no knife edges on the bed ({thin:.2f} mm2 thinner than a line in the first two layers)")
    above = (siding ^ s.box(-BED, 2 * BED, -BED, 2 * BED, s.WT + 1e-4, BED)).volume()
    top = printed_top(s.WT)
    if n == "plain side":
        report(trim_p.volume() < 1e-6 and above < 1e-6,
               f"{n}: no trim at all ({trim_p.volume():.4f} mm3 in filament 2), all one colour, its siding's top layer "
               f"at {top:.2f} mm")
    else:
        tb = trim_p.bounding_box()
        lo, hi = printed_top(tb[2] + 1e-6) if tb[2] > 0.25 else 0, printed_top(tb[5])
        report(trim_p.volume() > 0 and abs(tb[5] - (s.WT + s.PROUD)) < 0.01 and tb[2] > s.WT - 1e-6 and above < 1e-6
               and abs(lo - 5.05) < 1e-6 and abs(hi - 5.65) < 1e-6,
               f"{n}: trim is {trim_p.volume() / 1000:.3f} cm3, drawn {tb[2]:.3f} to {tb[5]:.3f} mm, printed {lo:.2f} "
               f"to {hi:.2f}; nothing in filament 1 above the siding's face ({above:.5f} mm3; its top layer prints at "
               f"{top:.2f}), so the plate changes colour once")
# the roll-up end round its doorway, as it prints (spec_rollup.md E.8, L.3): the latch plate is on the curtain now
# (group 6); the rebate's ceiling and the skirt are bridges of 20 mm or less between what holds them on the layer
# under them; the lip's 45 degree wedge steps at most 0.2 a layer and is joined to the skirt on every layer; the jamb
# stops step back at most 0.2 a layer and end at STOP_TOP
ewT = p["roll-up end"].transform(T_BED)
latch_in_wall = overlap(p["roll-up end"], s.ru_box(s.LATCH_X - s.LATCH_W / 2, s.LATCH_X + s.LATCH_W / 2, s.SD, s.WT + 1,
                                                    s.LATCH_Z - s.LATCH_H / 2, s.LATCH_Z + s.LATCH_H / 2))


def gaps_along(cs, z, lo, hi):
    """The gaps between the runs of a section along the line z, between lo and hi."""
    rr = [r for r in scan(cs, [z])[0] if r[1] > lo and r[0] < hi]
    return [b_[0] - a_[1] for a_, b_ in zip(rr, rr[1:])]


reb_spans = gaps_along(ewT.slice(s.REB_U - 0.1), s.MOUTH + 1.0, -s.RU_W / 2 - 1, s.RU_W / 2 + 1)
reb_pads = gaps_along(ewT.slice(s.REB_U - 0.1), s.PAD_Z + 0.5, -s.RU_W / 2 - 1, s.RU_W / 2 + 1)
skirt_spans = gaps_along(ewT.slice(s.SD - 0.15), 3.0, -42.0, 42.0)
lip_tops = []
for zl0, zl1 in layers(s.WT):
    if zl0 < s.LIP_U0 - 1e-9 or (zl0 + zl1) / 2 > s.WT:
        continue
    iv = scan(ewT.slice((zl0 + zl1) / 2).rotate(-90), [-5.0])[0]
    run = [r for r in iv if r[0] <= s.ZF - 0.5 <= r[1]]
    lip_tops.append(run[0][1] if run else -1.0)
lip_steps = [b_ - a_ for a_, b_ in zip(lip_tops, lip_tops[1:])]
stop_in = []
for zl0, zl1 in layers(1.6):
    iv = scan(ewT.slice((zl0 + zl1) / 2), [30.0])[0]
    run = [r for r in iv if r[0] <= s.RU_W / 2 + 0.5 <= r[1]]
    stop_in.append(run[0][0] if run else 99.0)
iv = scan(ewT.slice(0.125).rotate(-90), [-(s.STOP_X0 + s.STOP_RELIEF_X + 0.3)])[0]
stop_top = max(r[1] for r in iv if r[0] < s.ZF + 1)
stop_steps = [b_ - a_ for a_, b_ in zip(stop_in, stop_in[1:])]
foot_back = stop_in[0] - stop_in[1]         # the first layer's edge behind the second layer's
foot_ok = abs(foot_back - (s.STOP_RELIEF_X - 0.35)) < 0.01 and foot_back <= 0.2
report(latch_in_wall < 1e-9 and max(reb_spans) <= 20 and max(skirt_spans) <= 20 and min(lip_steps) >= -1e-9
       and max(lip_steps) <= 0.2 + 1e-6 and min(lip_tops) > s.ZF and foot_ok and min(stop_steps[1:]) >= -1e-9
       and max(stop_steps[1:]) <= 0.2 + 1e-6 and abs(stop_top - s.STOP_TOP) < 1e-6,
       f"roll-up end: no latch plate in the wall now ({latch_in_wall:.5f} mm3; it is on the curtain); the rebate's "
       f"ceiling on the {s.REB_U:.2f} layer spans {', '.join(f'{g_:.2f}' for g_ in reb_spans)} mm between its ribs and "
       f"jambs ({', '.join(f'{g_:.2f}' for g_ in reb_pads)} at the pads), the skirt {max(skirt_spans):.2f} at the most "
       f"between posts (at most 20); the lip's wedge, joined to the skirt on each of its layers, tops out at "
       f"{', '.join(f'{t_ - s.ZF:.2f}' for t_ in lip_tops)} over the floor top, at most {max(lip_steps):.2f} a layer; the "
       f"jamb stops, their first layer set back {foot_back:+.3f} from the second layer's edge ({s.STOP_RELIEF_X:.2f} from "
       f"the 45 degree face), so it can't meet the door's first layer, step back {min(stop_steps[1:]):.2f} to "
       f"{max(stop_steps[1:]):.2f} a layer from the second layer up (at most 0.2) and end at z {stop_top:.2f}")
# the siding beside the door side's casings: no groove within GROOVE_W of a side board's outer edge, read off the
# siding just under its face. The -56 in groove, 1/2 in past the steel door's latch-side casing, would run 0.1 mm
# from its edge, so it is filled beside the board and runs on above it and in the skirt (the Lofted Barn Garage's fix)
groove_side = []
for edge_, out_, cz0_, cz1_ in s.casing_sides():
    ya_, yb_ = sorted([edge_ - out_ * 1.0, edge_ + out_ * 12.0])
    rr_ = sorted((q.bounding_box()[1], q.bounding_box()[4]) for q in
                 (p["door side"] ^ s.box(s.W / 2 - 0.3, s.W / 2 - 0.05, ya_, yb_, (cz0_ + cz1_) / 2,
                                         (cz0_ + cz1_) / 2 + 0.2)).decompose())
    hold_ = [r for r in rr_ if r[0] - 1e-6 <= edge_ <= r[1] + 1e-6]
    groove_side.append(out_ * ((hold_[0][1] if out_ > 0 else hold_[0][0]) - edge_) if hold_ else -1.0)
yg_ = -56 * s.S


def groove_gaps(z):
    """The gaps in the door side's siding just under its face round the -56 in groove, at height z."""
    rr = sorted((q.bounding_box()[1], q.bounding_box()[4]) for q in
                (p["door side"] ^ s.box(s.W / 2 - 0.3, s.W / 2 - 0.05, yg_ - 2, yg_ + 2, z, z + 0.2)).decompose())
    return [(a_[1], b_[0]) for a_, b_ in zip(rr, rr[1:])]


g_mid, g_top, g_low = groove_gaps(s.ZF + 20), groove_gaps(s.ZF + s.DOOR_OPEN_H + s.TRIM + 1), groove_gaps(s.ZF - 3)
ok_g = not g_mid and all(len(g_) == 1 and abs(g_[0][0] - (yg_ - s.GROOVE_W / 2)) < 1e-3
                         and abs(g_[0][1] - (yg_ + s.GROOVE_W / 2)) < 1e-3 for g_ in (g_top, g_low))
report(min(groove_side) >= s.GROOVE_W and ok_g and len(s.groove_fills()) == 1,
       f"the siding beside the door side's casings is clean: from the outer edge of each side board to the nearest "
       f"groove {', '.join(f'{g_:.2f}' for g_ in groove_side)} mm (the steel door's hinge and latch sides, the window's "
       f"two), none under {s.GROOVE_W} mm; the -56 in groove, 1/2 in past the latch-side casing, is filled beside it "
       f"({len(g_mid)} gaps there 20 mm up) and runs on {s.GROOVE_W:.2f} wide above the casing ({len(g_top)} gap) and in "
       f"the skirt under the floor top ({len(g_low)} gap)")
for n in LONGS:
    sx = s.WALL_SIDE[n][1]
    above = p[n].trim_by_plane([0, 0, 1], s.ZWT + 0.001)        # the corners' tops stop exactly at ZWT
    drawn = s.mid_pegs()[0 if sx > 0 else 1].trim_by_plane([0, 0, 1], s.ZWT + 0.001)
    ab = above.bounding_box()
    report(len(above.decompose()) == 1 and 0.9 * drawn.volume() <= above.volume() <= drawn.volume() + 0.01
           and abs(ab[1]) < 1.2 and abs(ab[4]) < 1.2,
           f"{n}: nothing above the wall plates but its mid-length roof peg, and that whole ({above.volume():.2f} of "
           f"{drawn.volume():.2f} mm3 drawn, y {ab[1]:.2f} to {ab[4]:.2f})")
v = max(overlap(p[n], s.box(-BED, BED, -20, 20, -1, BED)) for n in ENDS)
report(v == 0, f"neither end wall has anything within 20 mm of y = 0 ({v:.5f} mm3), so the "
               f"mid pegs stay with the long walls")
# the six roof pegs lie on the bed in their walls' prints. A peg stands only 1 to 3 mm past the wall,
# too little for the overhang proof above to see one that starts in mid-air, so each is found here:
# what of its wall is above the roof's underside (the plates' top on a long wall) round the peg
peg_lows = []
for n in WALLS:
    R = np.column_stack([np.array(s.WALL_TO_PRINT[n], dtype=float), np.zeros(3)])
    base = p[n].transform(R).bounding_box()[2]                     # the wall's bed in its print
    if n in LONGS:
        sx = s.WALL_SIDE[n][1]
        spots = [(p[n].trim_by_plane([0, 0, 1], s.ZWT + 0.001), sx * s.MID_PEG_X, 0.0)]
    else:
        sy = s.WALL_SIDE[n][1]
        spots = []
        for sx in (1, -1):
            nrm, off = s.under_roof(sx, 0.001)
            spots.append((p[n].trim_by_plane([-c for c in nrm], -off), sx * s.PEG_X, sy * s.PEG_Y))
    for above, x, y in spots:
        pb = (above ^ s.cyl_z(x, y, 0, s.BIG, s.PEG_D + 0.2)).transform(R).bounding_box()
        peg_lows.append((pb[2] - base, pb[5] - pb[2]))
lows, tall = [q[0] for q in peg_lows], [q[1] for q in peg_lows]
report(len(peg_lows) == 6 and max(abs(q) for q in lows) < 1e-6 and all(abs(t - s.PEG_D) < 0.01 for t in tall),
       f"the {len(peg_lows)} roof pegs (two on each gable, one on each long wall's plates) lie on the bed in their "
       f"walls' prints: their lowest points {min(lows):.3f} to {max(lows):.3f} mm off the bed, each {min(tall):.2f} to "
       f"{max(tall):.2f} across, so none starts in mid-air")
lines = {"recess floor WT - POCKET_D": (s.WT - s.POCKET_D, 4.65), "siding face WT": (s.WT, 5.05),
         "trim WT + PROUD": (s.WT + s.PROUD, 5.65), "curtain's latch plate": (s.RAIL_FACE + s.LATCH_T, 5.45)}
ok = all(abs(printed_top(h) - want) < 1e-9 for h, want in lines.values())
exact = {"vent floor 4.25": s.WT - s.VENT_DEPTH, "STOP_U": s.STOP_U, "BARB": s.BARB,
         "BARB + PRONG_T": s.BARB + s.PRONG_T, "curtain face": s.RU_FACE, "slat grooves": s.RU_FACE - s.SLAT_GROOVE_D,
         "REB_U": s.REB_U, "LIP_U0": s.LIP_U0, "BOT_U": s.BOT_U, "TAB_T": s.TAB_T, "TAB_BUMP_U": s.TAB_BUMP_U,
         "BUMP_U": s.BUMP_U, "TONGUE_T": s.TONGUE_T, "RAIL_FACE": s.RAIL_FACE, "POST_EXT_U": s.POST_EXT_U,
         "STOP_RELIEF_U": s.STOP_RELIEF_U, "HDL_U1": s.HDL_U1, "HDL_U2": s.HDL_U2,
         "stop 2.45": s.STOP_POLY[0][1], "stop 3.25": s.STOP_POLY[1][1], "ANGLE_UP": s.ANGLE_UP, "ANGLE_T": s.ANGLE_T,
         "LEDGE_Z, floor upside down": s.ZF - s.LEDGE_Z}
ok = ok and all(on_line(h) for h in exact.values())
report(ok, "layer lines: " + ", ".join(f"{k} prints {printed_top(h):.2f}" for k, (h, _) in lines.items())
       + "; on a line: " + ", ".join(f"{k} {h:.2f}" for k, h in exact.items()))
# with Alan's standard layout the steel door's hinge-side edge is at -96 in, right on a layout mark,
# so that mark's stud lands 3/4 in on the door's king stud (the spec's +112 in no longer hits the
# door, which moved); the end walls' three are the spec's
SPEC_DROPPED = [("door side", -96, 0.75 * s.S), ("roll-up end", -51, 0.53), ("roll-up end", 61, None),
                ("back end", -61, None)]
got = sorted((w, m, ov) for w, m, _, ov in s.DROPPED_MARKS)
want = sorted(SPEC_DROPPED, key=lambda t: (t[0], t[1]))
same = len(got) == len(want) and all(g[0] == w_[0] and g[1] == w_[1] and (w_[2] is None or abs(g[2] - w_[2]) < 0.006)
                                     for g, w_ in zip(got, want))
report(same, "DROPPED_MARKS is these four (door side -96 in on the steel door's king stud, 3/4 in; the end walls' "
             "three as the spec): " + "; ".join(
    f"{w} {m:+d} in on {what} ({ov:.2f} mm = {ov * inch:.2f} in)" for w, m, what, ov in s.DROPPED_MARKS))
# the floor prints face down with nothing hanging over; the roof half flat on its underside
ff = s.to_print(s.FLOOR_TO_PRINT, [fl])[0]
fbb = ff.bounding_box()
foot = ff.slice(0.125).area()
worst, prev = 0.0, None
for z in [0.125] + [0.35 + 0.2 * k for k in range(int(fbb[5] / 0.2))]:
    if z > fbb[5]:
        break
    cs = ff.slice(z)
    if prev is not None:
        worst = max(worst, (cs - prev.offset(0.22, MIT, 10)).area())
    prev = cs
report(foot > 0.95 * (fbb[3] - fbb[0]) * (fbb[4] - fbb[1]) - 400 and worst < 0.5,
       f"the floor prints face down ({foot:.0f} mm2 on the bed) with nothing hanging "
       f"over ({worst:.3f} mm2 worst layer)")
rf_flat = s.roof_to_print(roof)
rbb = rf_flat.bounding_box()
worst, longest = worst_overhang(rf_flat)
report(rf_flat.slice(0.125).area() > 0.9 * (rbb[3] - rbb[0]) * (rbb[4] - rbb[1]) and worst < 5,
       f"the roof half prints flat on its underside ({rf_flat.slice(0.125).area():.0f} mm2 on the bed), nothing "
       f"steeper than 45 degrees but its peg holes' roofs ({worst:.2f} mm2 worst layer, "
       f"bridges up to {longest:.1f} mm)")


# ======================================================================== 4
group("4. Corners")


def to_corner(sx, sy):
    """Matrix from garage coords to a corner's own (u, v, z) (the inverse of corner_frame)."""
    return np.array([[sx, 0, 0, -s.W / 2], [0, sy, 0, -s.L / 2], [0, 0, 1, 0]], dtype=float)


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


ra, rb = s.angle_reach()
trim_all = s.union(s.trims())
zs = (1.0, s.ZF, 30.0, 60.0, s.ZWT - 1, s.ZWT + 1)
c0, c1 = s.POCKET_D + s.CORNER_CHAMFER, ra + s.POCKET_CLR
report(abs(c0 - 1.55) < 1e-9 and abs(c1 - 3.15) < 1e-9 and abs(ra - 3.0) < 1e-9 and abs(rb - 3.0) < 1e-9,
       f"each recess floor runs {c0:.2f} to {c1:.2f} mm from the corner ({c1 - c0:.2f} wide); the angle reaches "
       f"{ra:.2f} along the long wall and {rb:.2f} along the end wall, so it sits on {ra - c0:.2f} mm of each floor")
for (sx, sy), a in angles.items():
    cn = corner_name(sx, sy)
    ln, en = s.corner_walls(sx, sy)
    lw_, ew_ = p[ln], p[en]
    pair = s.union([lw_, ew_])
    v0 = max(overlap(a, lw_), overlap(a, ew_))
    in_l = overlap(a.translate([-sx * 0.005, 0, 0]), lw_)
    in_e = overlap(a.translate([0, -sy * 0.005, 0]), ew_)
    slab = s.box(-s.BIG, s.BIG, -s.BIG, s.BIG, 35, 37)
    wl = overlap(a.translate([-sx * 0.005, 0, 0]) ^ slab, lw_) / 0.005 / 2
    we = overlap(a.translate([0, -sy * 0.005, 0]) ^ slab, ew_) / 0.005 / 2
    report(v0 < 0.001 and in_l > 0.5 and in_e > 0.5 and wl >= 1.40 and we >= 1.40,
           f"corner angle {cn} sits in the recesses of the {ln} and {en}: into neither ({v0:.5f} mm3), on both recess "
           f"floors (pushed 0.005 mm in it meets them: {in_l:.2f} and {in_e:.2f} mm3), on "
           f"{wl:.3f} and {we:.3f} mm of glue land")
    c = (s.CORNER_CHAMFER - s.ANGLE_FILLET) / math.sqrt(2)
    near = reach_area(a, pair, sx, sy, zs, 0.09)
    fil = reach_area(a, pair, sx, sy, zs, c + 0.02)
    report(c >= 0.09 and near < 1e-4 and fil > 0.001,
           f"corner angle {cn} touches the walls only on the recess floors: nothing else within 0.09 mm ({near:.6f} "
           f"mm2 on sections at z 1, ZF, 30, 60, ZWT - 1, ZWT + 1); the fillet is {c:.3f} mm off the chamfer, and at "
           f"{c + 0.02:.3f} it reaches it ({fil:.4f} mm2)")
    worst = 0.0
    for nn, other in ((ln, ew_), (en, lw_)):
        for d in (0.15, -0.15):
            worst = max(worst, overlap(a.translate(toward(nn, d)), other))
    t_in = s.POCKET_CLR + 0.1
    tight = overlap(a.translate(toward(ln, -t_in)), ew_)
    report(worst < 0.001 and tight > 0.001,
           f"corner angle {cn} still misses the other wall with either wall's foot 0.15 mm in or out ({worst:.5f} mm3; "
           f"at {t_in:.2f} mm in it would meet it, {tight:.3f} mm3)")
    T = to_corner(sx, sy)
    at = a.transform(T)
    cover_l, cover_e = 99.0, 99.0
    for z in (0.3, s.ZF, 40.0, s.ZWT - 0.6):
        sec = at.slice(z)
        lp_, ep_ = sec ^ square(-s.POCKET_D, 1, -30, 1), sec ^ square(-30, 1, -s.POCKET_D, 1)
        cover_l = min(cover_l, -lp_.bounds()[1] if lp_.area() > 0 else 0)
        cover_e = min(cover_e, -ep_.bounds()[0] if ep_.area() > 0 else 0)
    seam_v = (lw_.transform(T).slice(40.0) ^ square(-3, 1, -3, 1)).bounds()[3]
    seam_u = (ew_.transform(T).slice(40.0) ^ square(-3, 1, -3, 1)).bounds()[2]
    face = (at ^ s.box(s.ANGLE_T - s.POCKET_D - 0.01, 1, -30, 1, -1, 400)).bounding_box()
    report(cover_l >= 2.95 and cover_e >= 2.95 and cover_l + seam_v >= 1.0 and cover_e + seam_u >= 1.0
           and abs(at.bounding_box()[2]) < 1e-9 and face[5] > s.ZWT - s.PLATE_TOP,
           f"corner angle {cn} covers the corner by {cover_l:.2f} mm along the long wall and {cover_e:.2f} mm along "
           f"the end wall from the siding's outer corner ({cover_l + seam_v:.2f} and {cover_e + seam_u:.2f} mm past "
           f"the joint at the chamfer), from its foot (z 0, level with the skirts) to "
           f"{face[5]:.2f} mm, over the plates")
    rf = roof if sx > 0 else roof.mirror([1, 0, 0])
    nrm = [sx * math.sin(s.ALPHA), 0, math.cos(s.ALPHA)]
    v19 = overlap(a, rf.translate([-0.19 * q for q in nrm]))
    v21 = overlap(a, rf.translate([-0.21 * q for q in nrm]))
    vlow = overlap(a, rf.translate([0, 0, -0.15]))
    report(overlap(a, rf) == 0 and v19 < 1e-5 and vlow < 1e-5 and v21 > 1e-3,
           f"corner angle {cn} is 0.2 mm under the roof, square to it (moved 0.19 toward it it clears, at 0.21 it "
           f"meets it: {v21:.4f} mm3), and clears the roof 0.15 mm lower")
    v = max(overlap(a.translate(d), trim_all) for d in directions(0.1))
    report(v < 1e-5, f"corner angle {cn} is at least 0.1 mm from the gable band and all other trim ({v:.6f} mm3 moved "
                     f"0.1 mm any way)")
pa = [s.on_bed(a) for a in angle_flat]
same = max((pa[0] - pa[3]).volume(), (pa[3] - pa[0]).volume(), (pa[1] - pa[2]).volume(), (pa[2] - pa[1]).volume())
mir = s.on_bed(pa[0].mirror([1, 0, 0]))
hand = max((mir - pa[1]).volume(), (pa[1] - mir).volume())
report(same < 0.001 and hand < 0.001 and (pa[0] - pa[1]).volume() > 1,
       f"the 4 angles are two mirror pairs: (+,+) prints the same as (-,-) and (+,-) as (-,+) ({same:.5f} mm3 apart), "
       f"each pair the other's mirror image ({hand:.5f})")
for (sx, sy), a in zip(s.CORNERS, angle_flat):
    bb = a.bounding_box()
    worst, _ = worst_overhang(a)
    loose = floating(a)
    nl = len(layers(bb[5] - 0.001))
    report(worst < 0.01 and loose < 0.02 and abs(bb[5] - s.ANGLE_UP) < 1e-6 and nl == 18
           and a.slice(0.125).area() > 0.95 * bb[4] * (bb[3] - 0.05),
           f"corner angle {corner_name(sx, sy)} prints on its long-face leg's outside face "
           f"({a.slice(0.125).area():.0f} mm2 on the plate), {bb[5]:.2f} mm tall ({nl} layers), {bb[4]:.2f} long, "
           f"nothing hanging over or starting in mid-air ({worst:.4f} and {loose:.4f} mm2)")
for sx, sy in s.CORNERS:
    ln, en = s.corner_walls(sx, sy)
    region = s.box(-12, 2, -12, 2, 30, 60).transform(s.corner_frame(sx, sy))
    T = to_corner(sx, sy)
    pl_ = printed_in_shed(p[ln], s.WALL_TO_PRINT[ln], region).transform(T)
    pe = printed_in_shed(p[en], s.WALL_TO_PRINT[en], region).transform(T)
    pa_ = printed_in_shed(angles[(sx, sy)], s.angle_to_print(sx), region).transform(T)
    floor_u = (pl_ ^ s.box(-3, 1, -3.05, -1.70, 40, 50)).bounding_box()[3]
    floor_v = (pe ^ s.box(-3.05, -1.70, -3, 1, 40, 50)).bounding_box()[4]
    du = floor_u - (pa_ ^ s.box(-1, 1, -2.90, -1.70, 40, 50)).bounding_box()[0]
    dv = floor_v - (pa_ ^ s.box(-2.90, -1.70, -1, 1, 40, 50)).bounding_box()[1]
    seated = pa_.translate([du, dv, 0])
    v = overlap(seated, s.union([pl_, pe]))
    on_l, on_e = overlap(seated.translate([-0.01, 0, 0]), pl_), overlap(seated.translate([0, -0.01, 0]), pe)
    away = square(-3, -0.6, -3, -0.6)
    ws, fs = s.union([pl_, pe]).slice(45.0) ^ away, seated.slice(45.0) ^ away
    lo, hi = 0.0, 0.5
    for _ in range(14):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if (fs.offset(mid, RND) ^ ws).area() > 1e-7 else (mid, hi)
    report(v < 1e-4 and on_l > 0.05 and on_e > 0.05 and lo >= 0.03,
           f"corner angle {corner_name(sx, sy)} as printed: pushed {-du:.3f} and {-dv:.3f} mm in, onto both printed "
           f"recess floors (u {floor_u:.3f}, v {floor_v:.3f}), it runs into neither wall ({max(v, 0):.5f} mm3 over 30 "
           f"mm; on them {on_l:.2f} and {on_e:.2f}); its fillet's steps stay {lo:.3f} mm clear of the walls' steps")
strips = []
for n in WALLS:
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
        floor_z, face_z = probe(-3.05, -1.70), probe(-6.5, -4.5)
        wl = p[n].transform(T)
        sharp = 180.0
        for z in (3.0, 30.0, 60.0, s.ZWT - 1):
            for poly in (wl.slice(z) ^ square(-3, 1, -3, 1)).to_polygons():
                P = np.asarray(poly)
                for i in range(len(P)):
                    a_, b_, c_ = P[i - 1], P[i], P[(i + 1) % len(P)]
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
        # the siding left between the recess's edge and the nearest groove along this face
        half = (s.W / 2, s.L / 2)[1 - axis]
        grooves = s.layout(-half, half, s.GROOVE_OC)
        g = min(half - abs(x) for x in grooves if (x > 0) == ((sx, sy)[1 - axis] > 0)) - s.GROOVE_W / 2
        strip = g - ((ra if axis == 0 else rb) + s.POCKET_CLR)
        strips.append(strip)
        report(abs(floor_z - 4.65) < 1e-6 and abs(face_z - 5.05) < 1e-6 and sharp >= 89.9 and thin < 0.01
               and strip >= 0.6,
               f"{n} at corner {corner_name(sx, sy)}: as printed the recess floor is at {floor_z:.2f} mm and the "
               f"siding round it at {face_z:.2f}; the sharpest corner of the wall there is {sharp:.0f} degrees; "
               f"{thin:.4f} mm2 a layer thinner than a line; {strip:.2f} mm of siding between "
               f"the recess and the first groove")
report(abs(min(strips) - 0.83) < 0.01, f"the narrowest strip of siding between a recess and a "
                                       f"groove is {min(strips):.2f} mm")


# ======================================================================== 5
group("5. Gables and vents")
for n in ENDS:
    side = s.WALL_SIDE[n][1]
    parts, recess = s.gable_vent(side)
    rbb = recess.bounding_box()
    region = s.box(rbb[0] - 1, rbb[3] + 1, -s.BIG, s.BIG, rbb[2] - 1, rbb[5] + 1)
    R = np.column_stack([np.array(s.WALL_TO_PRINT[n], dtype=float), np.zeros(3)])
    wb = p[n].transform(R).bounding_box()

    def to_bed(m):
        return m.transform(R).translate([-wb[0], -wb[1], -wb[2]])
    pp = to_bed(p[n] ^ region)
    fb = to_bed(recess ^ s.box(-s.BIG, s.BIG, -s.L / 2, s.L / 2, -s.BIG, s.BIG)).bounding_box()
    hole = square(fb[0], fb[3], fb[1], fb[4])
    xm = (fb[0] + fb[3]) / 2
    under = all((hole - pp.slice((z0 + z1) / 2)).area() < 1e-6 for z0, z1 in layers(4.25 - 0.001) if z0 >= 3.65 - 1e-9)
    n_under = sum(1 for z0, z1 in layers(4.25 - 0.001) if z0 >= 3.65 - 1e-9)
    gap_w, slat_w, counts = [], [], []
    for z0, z1 in layers(5.05 - 0.001):
        if z0 < 4.25 - 1e-9:
            continue
        sec = pp.slice((z0 + z1) / 2) ^ hole
        gaps = scan((hole - sec).rotate(90), [xm])[0]
        slats = scan(sec.rotate(90), [xm])[0]
        gap_w += [b - a for a, b in gaps]
        slat_w += [b - a for a, b in slats]
        counts.append(len(slats))
    top = (pp ^ s.box(fb[0], fb[3], fb[1], fb[4], s.WT + 1e-6, 50)).volume()     # the siding face prints at 5.05
    report(abs(s.WT - s.VENT_DEPTH - 4.25) < 1e-9 and under and n_under == 3 and set(counts) == {s.VENT_LOUVRES}
           and min(gap_w) >= 0.42 and min(slat_w) >= 0.42 and top < 1e-9,
           f"{n}'s vent: the recess floor is on the 4.25 layer line with {n_under} full layers of siding under it; "
           f"{counts[0]} louvres; on the recess's 4 layers the gaps are {min(gap_w):.2f} to {max(gap_w):.2f} mm and "
           f"the louvres {min(slat_w):.2f} to {max(slat_w):.2f} mm, all at least a 0.42 line; nothing "
           f"of it above 5.05 ({top:.6f} mm3)")
    # the vent's framing: a king each side reaching the top chords, the sill under it, no stud between
    zb = s.VENT_ZC - s.VENT_H / 2
    chord_under = s.zline(s.VENT_W / 2 + s.SW) - s.CHORD_V          # the top chords' underside over the kings
    fill = []
    for kx in (1, -1):
        xa, xb = sorted([kx * s.VENT_W / 2, kx * (s.VENT_W / 2 + s.SW)])
        kb = s.wall_box(n, xa + 0.01, xb - 0.01, 0.5, 1.5, s.ZWT + s.CHORD + 0.01, chord_under + 0.05)
        fill.append(overlap(p[n], kb) / kb.volume())
    sb = s.wall_box(n, -s.VENT_W / 2 + 0.1, s.VENT_W / 2 - 0.1, 0.5, 1.5, zb - s.SW + 0.05, zb - 0.05)
    sill = overlap(p[n], sb) / sb.volume()
    between = overlap(p[n], s.wall_box(n, -s.VENT_W / 2 + 0.05, s.VENT_W / 2 - 0.05, 0.5, 1.5, zb + 0.05,
                                       s.zline(s.VENT_W / 2) - s.CHORD_V - 0.05))
    report(min(fill) > 0.999 and sill > 0.999 and between < 1e-6,
           f"{n}'s vent framing: kings at x +-{s.VENT_W / 2:.3f}..{s.VENT_W / 2 + s.SW:.3f} solid from the bottom "
           f"chord up into the top chords ({min(fill) * 100:.1f}%, chords' underside {chord_under:.2f}); the flat sill "
           f"fills {zb - s.SW:.3f}..{zb:.3f} ({sill * 100:.1f}%); nothing between the "
           f"kings above it ({between:.6f} mm3)")
    plan = s.gable_stud_plan(n)
    short = [a for a, z0, z1 in plan if z1 - z0 < s.GABLE_STUD_MIN]
    missing = [round(a * inch) for a, kind, _, _ in s.mark_plan(n)
               if kind != "dropped" and all(abs(a - q[0]) > 1e-6 for q in plan)]
    report(not short and sorted(abs(m) for m in missing) == ([45] if n == "roll-up end" else [45, 51]),
           f"{n}'s gable studs: {len(plan)} on its marks, from {min(z1 - z0 for _, z0, z1 in plan):.2f} to "
           f"{max(z1 - z0 for _, z0, z1 in plan):.2f} mm tall; the marks at {', '.join(f'{m:+d}' for m in missing)} in "
           f"have no room (under {s.GABLE_STUD_MIN:.2f}) and are left out")


# ======================================================================== 6
group("6. The roll-up: the lift-out curtain (spec_rollup.md L.6)")
# The curtain is its own part. It hangs on the threshold lip's 45 degree wedge, stands behind the two
# jamb stops, and its tongue rises into the rebate over the doorway, where two spring fingers press it
# down and two tabs press its top in. It comes out the front: lifted until it stops, let down a hair,
# its bottom swung out, dropped and pulled away (spec H.3); it goes back in leaned (H.5). Its motion has
# no x part, so a (u, z) section of it and its doorway at a station x along the wall is exact for
# everything at that x. The proofs below cut the real parts into sections at stations through every
# notch, rib, pad, bump, tab, post, the latch, the handle and the chamfers, as drawn and as printed. As
# printed, each part is cut into its print layers (0.25, then 0.2; the end wall and the curtain lying
# u up, the floor upside down) and grown in its bed plane: the wall GW a side (holes print small) and
# the curtain GC. The growth cases are wall / curtain 0 / 0, 0.1 / 0.1, 0.15 / 0.1 and 0.2 / 0.05 (H.2).
n = s.RU
ew = p[n]
cur = p["curtain"]
cur_w, cur_b = s.curtain_parts()
H_ = s.RU_W / 2
GW, GC = 0.1, 0.05
GROWTHS = [(0.0, 0.0), (0.1, 0.1), (0.15, 0.1), (0.2, 0.05)]
TOL = 1e-4                       # mm2 of rigid overlap in a section that is a contact (spec L.6.4)


def to_shapely(cs):
    """A CrossSection as a shapely (Multi)Polygon."""
    polys = []
    for comp in cs.decompose():
        rings = [np.asarray(r) for r in comp.to_polygons() if len(r) >= 3]
        sa = [0.5 * np.sum(r[:, 0] * np.roll(r[:, 1], -1) - np.roll(r[:, 0], -1) * r[:, 1]) for r in rings]
        outer = [r for r, a in zip(rings, sa) if a > 0]
        if outer:
            polys.append(SPoly(outer[0], [r for r, a in zip(rings, sa) if a < 0]))
    if not polys:
        return SPoly()
    return polys[0] if len(polys) == 1 else shapely.union_all(polys)


def drawn_sections(m, xs):
    """The (u, z) sections of a part at stations xs, as drawn."""
    mt = m.transform(T_SEC)
    return [to_shapely(mt.slice(-x)) for x in xs]


def layer_sections(mt, grow, ranges=None):
    """[(a, b, section)] of a part in its print position (its layers along z), each grown in the bed plane."""
    bb = mt.bounding_box()
    out = []
    for a, b in layers(bb[5]):
        mid = (a + b) / 2
        if mid < bb[2]:
            continue
        cs = mt.slice(mid)
        if not cs.is_empty():
            out.append((a, b, cs.offset(grow, MIT, 2) if grow > 0 else cs))
    return out


def printed_sections(m, grow, xs):
    """The (u, z) sections of a part that prints lying u up (the end wall, the curtain) at stations xs, as
    printed: each layer is the part's section at the layer's middle, grown `grow` a side in the bed plane,
    held over the layer."""
    rects = [[] for _ in xs]
    for a, b, cs in layer_sections(m.transform(T_BED), grow):
        for i, iv in enumerate(scan(cs.rotate(-90), [-x for x in xs])):
            rects[i] += [(a, z0, b, z1) for z0, z1 in iv]
    return [shapely.union_all(shapely.box(*np.array(r).T)) if r else SPoly() for r in rects]


def printed_floor_sections(f, grow, xs):
    """The same for the floor's edge, which prints upside down: its layers run along z."""
    rects = [[] for _ in xs]
    for a, b, cs in layer_sections(f.transform(FLOOR_BED), grow):
        for i, iv in enumerate(scan(cs.rotate(-90), [-x for x in xs])):   # bed y is -y: intervals in -y
            rects[i] += [(y0 - C0, s.ZF - b, y1 - C0, s.ZF - a) for y0, y1 in iv]
    return [shapely.union_all(shapely.box(*np.array(r).T)) if r else SPoly() for r in rects]


def printed_solid(m, grow, floor_part=False):
    """A part as printed, in 3D, put back in garage coords: its layers, each grown in the bed plane."""
    mat, back = (FLOOR_BED, FLOOR_BED) if floor_part else (T_BED, BED_BACK)
    slabs = [M.extrude(cs, b - a).translate([0, 0, a]) for a, b, cs in layer_sections(m.transform(mat), grow)]
    return s.union(slabs).transform(back)


def A_shift(du, dz):
    return np.array([[1, 0, du], [0, 1, dz], [0, 0, 1.0]])


def A_rot(deg, pu, pz):
    """Turn deg about (pu, pz); + swings the curtain's bottom out (toward +u) about a point above it."""
    t = math.radians(deg)
    R = np.array([[math.cos(t), -math.sin(t), 0], [math.sin(t), math.cos(t), 0], [0, 0, 1.0]])
    return A_shift(pu, pz) @ R @ A_shift(-pu, -pz)


def removal_pose(seat, lift=0.0, th=0.0, pivot=None, du=0.0, dz=0.0, du0=0.0):
    """From the seat, lifted, slid out du0, swung th about pivot (the front of the curtain at the mouth
    unless given), then moved (du, dz)."""
    A = A_shift(seat[0] + du0, seat[1] + lift)
    if th:
        pu, pz = pivot if pivot else (s.RU_FACE, s.MOUTH + lift + seat[1])
        A = A_rot(th, pu, pz) @ A
    return A_shift(du, dz) @ A


def insertion_pose(seat, th, phi, du=0.0, dz=0.0):
    """Spec H.5: from the seat, the bottom swung out th about the front at the mouth, the top leaned in
    a further phi about the bottom's front corner, then moved (du, dz)."""
    A = A_rot(th, s.RU_FACE, s.MOUTH + seat[1]) @ A_shift(*seat)
    if phi:
        cu, cz, _ = A @ [s.BOT_U, s.ZF + s.G_BOT, 1.0]
        A = A_rot(phi, cu, cz) @ A
    return A_shift(du, dz) @ A


def pose_3d(A):
    """A (u, z) pose as a garage-coords matrix (u = -y - C0)."""
    (a11, a12, b1), (a21, a22, b2) = A[0], A[1]
    return np.array([[1, 0, 0, 0], [0, a11, -a12, a11 * C0 - b1 - C0], [0, -a21, a22, -a21 * C0 + b2]], dtype=float)


def apply(A, geoms, shifts=None):
    """Geometries moved by A, then each by its own (du, dz) in shifts."""
    if not len(geoms):
        return geoms
    M2, t = A[:2, :2].T, A[:2, 2]
    if shifts is None:
        return shapely.transform(geoms, lambda c: c @ M2 + t)
    rep = np.repeat(np.asarray(shifts, dtype=float), shapely.get_num_coordinates(geoms), axis=0)
    return shapely.transform(geoms, lambda c: c @ M2 + t + rep)


def profile(xi, a):
    """A cantilever's deflection at xi from its root over its deflection at the load, a from the root."""
    xi = np.asarray(xi, dtype=float)
    return np.where(xi <= a, xi ** 2 * (3 * a - xi) / (2 * a ** 3), 1 + 1.5 * (xi - a) / a)


FING_A = s.FING_ROOT - (s.BUMP_X0 + s.BUMP_X1) / 2          # 15.6, the bump from the finger's root
TAB_A = s.TAB_ROOT - (s.TAB_BUMP_X0 + s.TAB_BUMP_X1) / 2   # 9.0, the tab's bump from its root
PAD_REGION = s.union([s.ru_box(*s.xspan(sg, s.PAD_X0 - 0.3, s.PAD_X1 + 0.3), -0.5, s.REB_U - 0.001, s.PAD_Z - 0.4,
                               s.MOUTH + s.REB_H + 0.005) for sg in (1, -1)])
LO_W, HI_W = 15.0, 53.0          # the doorway's bottom band (z < 15), top band (z > 53), middle (stops only)
BAND = 9.9                       # the curtain moves less than this in z in every pose tried: asserted


def stations(edges, lo, hi, fine=()):
    """Stations x: geom2's 77 (spec L.6) within lo..hi, 0.05 either side of every edge given, and the
    fine samples."""
    base = [0.0, 0.3, 1.2, 2.5, 3.6, 5.0, 5.4, 7.0, 9.0, 10.2, 11.289, 12.5, 13.0, 14.0, 14.5, 15.0, 15.5, 15.6,
            16.25, 16.6, 17.0, 17.3, 17.7, 18.4, 20.0, 22.0, 24.0, 24.694, 26.0, 28.0, s.LATCH_X, 30.0, 31.5, 32.2,
            32.5, 32.9, 33.2, 33.45, 33.55]
    xs = base + [-x for x in base if x > 0] + [e + d for e in edges for d in (-0.05, 0.05)] + list(fine)
    return sorted({round(x, 4) for x in xs if lo - 1e-9 <= x <= hi + 1e-9})


def edges_of(sign_set=(1, -1), xc_handle=0.0):
    """The x of every edge of the curtain's and the doorway's features (both sides unless told)."""
    e = []
    for xp in s.CURTAIN_POSTS:
        e += [xp + d for d in (-s.SW / 2, s.SW / 2, -s.SW / 2 - s.POST_NOTCH_CLR, s.SW / 2 + s.POST_NOTCH_CLR)]
    for xr in s.RIB_XS:
        e += [xr + d for d in (-s.RIB_W / 2, s.RIB_W / 2, -s.RIB_W / 2 - s.RIB_CLR, s.RIB_W / 2 + s.RIB_CLR)]
    for sg in sign_set:
        e += [sg * a for a in (s.TAB_TIP - s.TAB_GAP, s.TAB_TIP, s.TAB_BUMP_X1, s.TAB_ROOT, s.FING_TIP - 0.1, s.FING_TIP,
                               s.BUMP_X0, s.PAD_X0, s.PAD_X1, s.BUMP_X1, s.FING_ROOT - s.FING_RADIUS, s.FING_ROOT,
                               s.CUR_HALF - s.CUR_CHAMF, s.STOP_X0, s.STOP_X0 + s.STOP_RELIEF_U,
                               s.STOP_X0 + s.STOP_RELIEF_X, s.CUR_HALF, H_)]
    for d in (s.HDL_HALF - s.HDL_LEG, s.HDL_HALF, s.HDL_HALF + s.HDL_FILLET[0]):
        e += [xc_handle - d, xc_handle + d]
    e += [s.LATCH_X + d for d in (-s.LATCH_W / 2, -s.LATCH_W / 2 + s.LATCH_CUT, -s.LATCH_SLOT_W / 2,
                                  s.LATCH_SLOT_W / 2, s.LATCH_W / 2 - s.LATCH_CUT, s.LATCH_W / 2)]
    return e


class Rig:
    """A curtain in a roll-up doorway, cut into (u, z) sections at stations x, each kept once however many
    stations share it: the curtain's rigid part and its springs (the finger strips and their bumps, the
    tab plates and their bumps, cut out of the real part by s.spring_regions()), the doorway (the end
    wall and the floor's edge) and the pads over the finger bumps; as drawn, or as printed with the wall
    grown gw a side and the curtain gc."""

    def __init__(self, curtain_part, wall, floor_part, xs, printed, gw=GW, gc=GC, label=""):
        self.label, self.printed, self.gw, self.gc = label, printed, gw, gc

        def sec(m, grow):
            return printed_sections(m, grow, xs) if printed else drawn_sections(m, xs)
        reg = s.spring_regions()
        parts = {"R": curtain_part - s.union(list(reg.values())), "F": curtain_part ^ reg["fingers"],
                 "FB": curtain_part ^ reg["finger bumps"], "T": curtain_part ^ reg["tabs"],
                 "TB": curtain_part ^ reg["tab bumps"]}
        S_ = {k: sec(v, gc) for k, v in parts.items()}
        wl = sec(wall, gw)
        fl_ = ((printed_floor_sections(floor_part, gw, xs) if printed else drawn_sections(floor_part, xs))
               if floor_part is not None else [SPoly()] * len(xs))
        S_["W"] = [shapely.union(a, b) for a, b in zip(wl, fl_)]
        S_["P"] = sec(wall ^ PAD_REGION, gw)
        seen, keep = set(), []
        for i in range(len(xs)):
            k = tuple(shapely.to_wkb(shapely.normalize(shapely.set_precision(S_[q][i], 1e-6)))
                      for q in ("R", "F", "FB", "T", "TB", "W", "P"))
            if k not in seen:
                seen.add(k)
                keep.append(i)
        self.n_all, self.xs = len(xs), np.array([xs[i] for i in keep])
        for q, v in S_.items():
            setattr(self, q, np.array([v[i] for i in keep], dtype=object))
        lo, hi = sbox(-99, -99, 99, LO_W), sbox(-99, HI_W, 99, 299)
        self.W_lo, self.W_hi = shapely.intersection(self.W, lo), shapely.intersection(self.W, hi)
        self.W_mid = shapely.intersection(self.W, sbox(-99, LO_W, 99, HI_W))
        self.mid = np.nonzero(~shapely.is_empty(self.W_mid))[0]
        self.R_lo = shapely.intersection(self.R, sbox(-99, -99, 99, LO_W + BAND))
        self.R_hi = shapely.intersection(self.R, sbox(-99, HI_W - BAND, 99, 299))
        for g in (self.W_lo, self.W_hi, self.W_mid, self.W, self.P):
            shapely.prepare(g)
        ax = np.abs(self.xs)
        self.fs = np.nonzero(~shapely.is_empty(self.F) | ~shapely.is_empty(self.FB))[0]
        self.ps = np.array([i for i in self.fs if not self.FB[i].is_empty and not self.P[i].is_empty], dtype=int)
        self.ts = np.nonzero(~shapely.is_empty(self.T) | ~shapely.is_empty(self.TB))[0]
        self.f_prof = profile(s.FING_ROOT - ax[self.fs], FING_A)
        self.t_prof = profile(s.TAB_ROOT - ax[self.ts], TAB_A)
        self.p_prof = profile(s.FING_ROOT - ax[self.ps], FING_A)
        self.sign = np.sign(self.xs)
        self.band_ok = True

    def _check_band(self, A):
        pts = np.array([[0, 7], [9, 7], [0, 66], [9, 66], [-2, 30], [9, 30]], dtype=float)
        dz = np.abs(pts @ A[:2, :2].T + A[:2, 2] - pts)[:, 1].max()
        if dz > BAND:
            self.band_ok = False

    def rigid_by_station(self, A):
        """The rigid curtain's overlap (mm2) with the doorway at each station at pose A."""
        self._check_band(A)
        out = np.zeros(len(self.xs))
        for Rq, Wq, idx in ((self.R_lo, self.W_lo, None), (self.R_hi, self.W_hi, None), (self.R, self.W_mid, self.mid)):
            if idx is not None:
                if not len(idx):
                    continue
                Rq, Wq = Rq[idx], Wq[idx]
            Rm = apply(A, Rq)
            hit = np.nonzero(shapely.intersects(Wq, Rm))[0]
            if len(hit):
                a = shapely.area(shapely.intersection(Rm[hit], Wq[hit]))
                out[hit if idx is None else idx[hit]] += a
        return out

    def rigid(self, A):
        return self.rigid_by_station(A).max()

    def springs(self, A):
        """At pose A: the finger bumps' bend down (the most, at the pads: bump top less pad bottom), how far
        each finger bump is under its pad in u (the least: the u overlap of the moved bump's top edge with the
        pad's u range, for a bent finger drops its bump straight down, so what bears on the pad is the bump's
        top face), each tab bump's overlap with the wall (area, and its depth in u: the tab's bend in), and what
        the strips and bumps touch once each spring is moved by its own bend (spec L.6.2), mm2."""
        r = dict(fbend=0.0, fpad=None, tb_ov=np.zeros(len(self.ts)), tb_u=np.zeros(len(self.ts)), strip=0.0)
        delta = {1: 0.0, -1: 0.0}
        if len(self.ps):
            FBm = apply(A, self.FB[self.ps])
            inter = shapely.intersection(FBm, self.P[self.ps])
            on = shapely.area(inter) > 1e-7
            b = np.where(on, shapely.bounds(FBm)[:, 3] - shapely.bounds(self.P[self.ps])[:, 1], 0.0)
            fbb0 = shapely.bounds(self.FB[self.ps])
            pb0 = shapely.bounds(self.P[self.ps])
            ua = fbb0[:, 0] * A[0, 0] + fbb0[:, 3] * A[0, 1] + A[0, 2]
            ub = fbb0[:, 2] * A[0, 0] + fbb0[:, 3] * A[0, 1] + A[0, 2]
            pu1 = np.minimum(pb0[:, 2], s.REB_U - 0.001)
            r["fpad"] = float(np.maximum(0.0, np.minimum(np.maximum(ua, ub), pu1)
                                         - np.maximum(np.minimum(ua, ub), pb0[:, 0])).min())
            ib = shapely.bounds(inter)               # the older measure: the u extent of where bump and pad overlap
            r["fpad_area"] = float(np.where(on, ib[:, 2] - ib[:, 0], 0.0).min())
            r["fbend"] = float(b.max())
            for sg in (1, -1):
                m_ = self.sign[self.ps] == sg
                if m_.any():
                    delta[sg] = float((b[m_] / self.p_prof[m_]).max())
        if len(self.fs):
            d = np.array([delta[int(sg)] for sg in self.sign[self.fs]]) * self.f_prof
            sh = np.column_stack([np.zeros(len(d)), -d])
            for G in (self.F, self.FB):
                Gm = apply(A, G[self.fs], sh)
                r["strip"] = max(r["strip"], shapely.area(shapely.intersection(Gm, self.W_hi[self.fs])).max())
        if len(self.ts):
            TBm = apply(A, self.TB[self.ts])
            inter = shapely.intersection(TBm, self.W_hi[self.ts])
            r["tb_ov"] = shapely.area(inter)
            ib = shapely.bounds(inter)
            r["tb_u"] = np.where(r["tb_ov"] > 1e-7, ib[:, 2] - ib[:, 0], 0.0)
            dt = {sg: 0.0 for sg in (1, -1)}
            for sg in (1, -1):
                m_ = (self.sign[self.ts] == sg) & (r["tb_u"] > 0)
                if m_.any():
                    dt[sg] = float((r["tb_u"][m_] / self.t_prof[m_]).max())
            d = np.array([dt[int(sg)] for sg in self.sign[self.ts]]) * self.t_prof
            sh = np.column_stack([-d, np.zeros(len(d))])
            for G in (self.T, self.TB):
                Gm = apply(A, G[self.ts], sh)
                r["strip"] = max(r["strip"], shapely.area(shapely.intersection(Gm, self.W_hi[self.ts])).max())
        return r

    def top_z(self, A):
        """The highest point of the curtain at pose A."""
        return max(np.nanmax(shapely.bounds(apply(A, getattr(self, q)))[:, 3]) for q in ("R", "F", "FB", "T", "TB"))


def run(rig, phases, want_springs=True, stop_on_contact=False):
    """Walk a path of phases [(kind, [poses])]: kind "z" for a move in z (a tab bump that is clear at the
    phase's start must stay clear, and one that is loaded may not be pushed further in: a bump can only be
    loaded by a move in u, spec D.4), else "u" or "turn". Returns the worst rigid overlap, the most finger
    bend, the most tab bend, the most strip contact, the most a tab bump was loaded by a move in z (u), and
    the pose index of the worst overlap."""
    worst, fb, tb, sp, zload, where, k = 0.0, 0.0, 0.0, 0.0, 0.0, None, 0
    tb_now = None
    for kind, poses in phases:
        if want_springs and tb_now is None and len(rig.ts):
            tb_now = rig.springs(poses[0])["tb_u"]
        start = tb_now
        for A in poses:
            ov = rig.rigid(A)
            if ov > worst:
                worst, where = ov, k
            k += 1
            if stop_on_contact and ov > TOL:
                return worst, fb, tb, sp, zload, where
            if want_springs:
                r = rig.springs(A)
                fb, sp = max(fb, r["fbend"]), max(sp, r["strip"])
                tb = max(tb, r["tb_u"].max() if len(r["tb_u"]) else 0.0)
                if kind == "z" and start is not None and len(r["tb_u"]):
                    zload = max(zload, (r["tb_u"] - start).max())
                tb_now = r["tb_u"]
    return worst, fb, tb, sp, zload, where


def removal_phases(seat, lift, th, n=10, pivot=None, du0=0.0):
    """Spec H.3: lift, (slide out du0), swing th, drop TONGUE_UP + BUMP_H + lift + 0.6, pull out 15."""
    drop = s.TONGUE_UP + s.BUMP_H + lift + 0.6
    ph = [("z", [removal_pose(seat, lift * k / n) for k in range(0, n + 1)])]
    if du0:
        ph.append(("u", [removal_pose(seat, lift, du0=du0 * k / n) for k in range(1, n + 1)]))
    ph.append(("turn", [removal_pose(seat, lift, th * k / n, pivot, du0=du0) for k in range(1, n + 1)]))
    ph.append(("z", [removal_pose(seat, lift, th, pivot, du0=du0, dz=-drop * k / n) for k in range(1, n + 1)]))
    ph.append(("u", [removal_pose(seat, lift, th, pivot, du0=du0, du=15 * k / n, dz=-drop) for k in range(1, n + 1)]))
    return ph


def path_clear(rig, seat, lift, th, n=10, pivot=None, du0=0.0):
    return run(rig, removal_phases(seat, lift, th, n, pivot, du0), want_springs=False, stop_on_contact=True)[0] <= TOL


def settle(rig, step=0.025, reach=0.8):
    """The seat the springs push the curtain to (spec L.6.3): down and in as far as its rigid parts let it,
    on a grid reaching `reach` each way; of equal (du + dz), the one furthest in. For each du the least clear
    dz is found by halving: over this range going up only ever clears the bottom."""
    k = round(reach / step)
    best = None
    for i in range(-k, k + 1):
        du = i * step
        if rig.rigid(A_shift(du, k * step)) > 1e-5:
            continue
        lo, hi = -k, k
        if rig.rigid(A_shift(du, lo * step)) <= 1e-5:
            hi = lo
        while hi - lo > 1:
            mid = (lo + hi) // 2
            lo, hi = (lo, mid) if rig.rigid(A_shift(du, mid * step)) <= 1e-5 else (mid, hi)
        sc = du + hi * step
        if best is None or sc < best[0] - 1e-9:
            best = (sc, du, hi * step)
    return (best[1], best[2]) if best else (0.0, 0.0)


def rigid_stop(rig, seat, step=0.025):
    """Lifted straight up from the seat until a rigid part meets something: the tongue's top the rebate's."""
    L = 0.0
    while rig.rigid(removal_pose(seat, L + step)) <= TOL and L < 3:
        L += step
    return round(L, 3)


def least_lift(rig, seat, stop):
    """The least lift (0.05 steps) from which it comes out by H.3 at 7 degrees, 10 steps a phase."""
    for k in range(2, 80):
        lf = round(0.05 * k, 3)
        if lf > stop + 1e-9:
            return None
        if path_clear(rig, seat, lf, 7.0):
            return lf
    return None


def first_contact(rig, seat, lift, pivot, du0=0.0, tmax=12.0):
    """The first swing (0.5 steps) at which the rigid curtain meets something, or 12.5 for none to 12."""
    t = 0.5
    while t <= tmax + 1e-9:
        if rig.rigid(removal_pose(seat, lift, t, pivot, du0=du0)) > TOL:
            return t
        t += 0.5
    return 12.5


MOTIONS = {"tongue top held": lambda sd, lf: (dict(pivot=(0.5 + sd[0], s.Z_TT + lf + sd[1]))),
           "slid out, on the rebate's lip": lambda sd, lf: dict(pivot=(s.REB_U, s.MOUTH),
                                                               du0=s.REB_U - 0.05 - s.TONGUE_T - sd[0]),
           "mid-depth": lambda sd, lf: dict(pivot=(2.5, s.MOUTH + lf + sd[1]))}


def motion(rig, seat, lift, kw):
    """A hand motion at a lift: the first-contact swing, and the least swing (4 to 11) under it that
    lets the curtain out (None if none)."""
    if kw.get("du0") and rig.rigid(removal_pose(seat, lift, du0=kw["du0"])) > TOL:
        return 0.0, None
    tc = first_contact(rig, seat, lift, kw["pivot"], kw.get("du0", 0.0))
    for th in (4, 5, 6, 7, 8, 9, 10, 11):
        if th >= tc:
            break
        if path_clear(rig, seat, lift, th, 8, kw["pivot"], kw.get("du0", 0.0)):
            return tc, th
    return tc, None


def tongue_back_u(A):
    """Where the tongue's back (u 0, seated) crosses the mouth's height at pose A: the lean (spec H.5)."""
    (u0, z0), (u1, z1) = [A[:2, :2] @ q + A[:2, 2] for q in (np.array([0.0, s.MOUTH - 3]), np.array([0.0, s.MOUTH + 3]))]
    return u0 + (u1 - u0) * (s.MOUTH - z0) / (z1 - z0)


def finger_u_push(rig, A):
    """At pose A, how far (in u) any finger bump or strip reaches into a pad that it meets from behind, wholly
    above the pad's bottom: a push in u, which bends the finger back toward the room (0 if none)."""
    if not len(rig.ps):
        return 0.0
    pad_bot = shapely.bounds(rig.P[rig.ps])[:, 1]
    most = 0.0
    for G_ in (rig.FB, rig.F):
        inter = shapely.intersection(apply(A, G_[rig.ps]), rig.P[rig.ps])
        on = shapely.area(inter) > 1e-7
        if on.any():
            ib = shapely.bounds(inter)
            behind = on & (ib[:, 1] > pad_bot + 0.01)
            if behind.any():
                most = max(most, float((ib[behind, 2] - ib[behind, 0]).max()))
    return most


def insertion(rig, seat, stop, need, th, phi):
    """Spec H.5 and L.6.9 at one swing and lean: in under the head (the tongue and bumps below the mouth),
    up until it stops, let down 1.0 (and 0.9, 1.1) and to every lift in the window, the top let out and
    the bottom swung in one after the other, and (let down about a millimetre, as the read-me says, and
    above the least lift: at the least lift itself the two together graze the lip, spec H.5) together,
    then lowered to the seat. Returns a dict: what happened, the lean (the tongue's back at the mouth),
    the lift it stopped at, how far the finger bumps were under their pads, the worst rigid overlap, the
    most finger bend, the most a tab bump was loaded by a move in z."""
    need = stop if need is None else need          # no lift lets it out: 6.6 has failed; go on from the stop
    drop = s.TONGUE_UP + s.BUMP_H + 0.6
    lean = tongue_back_u(insertion_pose(seat, th, phi))
    out = dict(lean=lean, top=None, fpad=None, worst=0.0, fbend=0.0, zload=0.0, strip=0.0, tb=0.0)
    come = [insertion_pose(seat, th, phi, du=15 * (1 - k / 10), dz=-drop) for k in range(11)]
    if max(rig.rigid(A) for A in come) > TOL:
        out["what"] = "blocked coming in under the head"
        return out
    dz, rise_tb, catch = -drop, 0.0, None
    for stepz in (0.1, 0.02):
        while dz < 4.0:
            A = insertion_pose(seat, th, phi, dz=dz + stepz)
            if rig.rigid(A) > TOL:
                break
            r = rig.springs(A)
            if r["tb_ov"].max() > 1e-6 and catch is None:
                catch = (dz + stepz, r["fbend"])           # where a tab bump first meets the head, the fingers' bend,
                for j_ in range(1, round(stepz / 0.02)):   # refined to 0.02 (as the Lofted Barn Garage's)
                    rj_ = rig.springs(insertion_pose(seat, th, phi, dz=dz + 0.02 * j_))
                    if rj_["tb_ov"].max() > 1e-6:
                        catch = (dz + 0.02 * j_, rj_["fbend"])
                        break
            rise_tb = max(rise_tb, r["tb_ov"].max())
            dz += stepz
    top = dz
    r = rig.springs(insertion_pose(seat, th, phi, dz=top))
    out.update(top=top, fpad=r["fpad"] if r["fpad"] is not None else 0.0, fbend=r["fbend"], fbend_top=r["fbend"],
               fpad_area=r.get("fpad_area", 0.0), catch=catch)
    if rise_tb > 1e-6:
        out["what"] = "catches: a tab bump meets the head going up"
        return out
    if out["fpad"] < 0.2:
        # leaned in too far: the finger bumps come up beside their pads, behind them. Step 4 as the read-me says (let
        # down about a millimetre, the top let out and the bottom pushed in, let go): does something rigid stop the
        # top coming out, or does the top come out pushing the finger bumps back from behind their pads (a push in u,
        # which the fingers, thin that way, give to)?
        L = max(round(top - 1.0, 3), need)
        seq = [("z", [insertion_pose(seat, th, phi, dz=top + (L - top) * k / 8) for k in range(1, 9)]),
               ("turn", [insertion_pose(seat, th, phi * (1 - k / 8), dz=L) for k in range(1, 9)]),
               ("turn", [insertion_pose(seat, th * (1 - k / 10), 0.0, dz=L) for k in range(1, 11)])]
        ub = 0.0
        for kind, poses in seq:
            for A in poses:
                if rig.rigid(A) > TOL:
                    out.update(what="leaned too far: the top won't come out", u_bend=ub)
                    return out
                if kind == "turn":
                    ub = max(ub, finger_u_push(rig, A))
        out.update(what="leaned too far: its springs go in behind their pads" if ub > 0 else
                   "leaned too far: a finger bump is not under its pad", u_bend=ub)
        return out
    lifts = sorted({round(top - 1.0, 3), round(top - 0.9, 3), round(top - 1.1, 3), need,
                    round((need + stop) / 2, 3), round(stop - 0.15, 3), stop})
    worst, fb, zl, sp, tb = 0.0, r["fbend"], 0.0, r["strip"], 0.0
    for L in lifts:
        if L < need - 1e-9 or L > top:
            continue
        seq = [("z", [insertion_pose(seat, th, phi, dz=top + (L - top) * k / 8) for k in range(1, 9)]),
               ("turn", [insertion_pose(seat, th, phi * (1 - k / 8), dz=L) for k in range(1, 9)]),
               ("turn", [insertion_pose(seat, th * (1 - k / 10), 0.0, dz=L) for k in range(1, 11)]),
               ("z", [insertion_pose(seat, 0.0, 0.0, dz=L * (1 - k / 10)) for k in range(1, 11)])]
        paths = [seq]
        if top - 1.1 - 1e-9 <= L <= top - 0.9 + 1e-9 and L >= need + 0.05 - 1e-9:   # "let it down about a millimetre"
            paths.append([seq[0], ("turn", [insertion_pose(seat, th * (1 - k / 14), phi * (1 - k / 14), dz=L)
                                            for k in range(1, 15)]), seq[3]])
        for ph in paths:
            w_, f_, t_, s_, z_, _ = run(rig, ph)
            worst, fb, tb, sp, zl = max(worst, w_), max(fb, f_), max(tb, t_), max(sp, s_), max(zl, z_)
    out.update(worst=worst, fbend=fb, zload=zl, strip=sp, tb=tb)
    out["what"] = "works" if worst <= TOL else "rigid contact after the top"
    return out


def jamb_stations(curtain_part, wall, gw, gc, zones):
    """As printed, the (u, z) section at x changes only where an outline of some layer of the curtain or of the
    wall (each grown in its bed plane) has a corner at that x. Within the x zones given (round the jamb stops,
    whose first layers and the curtain's chamfered back edges are where a band narrower than the stations'
    spacing could hold it off its seat), and under the stops' top, a station in the middle of every interval
    between two such corners: so there the printed rig misses nothing."""
    xs = set()
    for m, grow in ((curtain_part, gc), (wall, gw)):
        for _, _, cs in layer_sections(m.transform(T_BED), grow):
            for poly in cs.to_polygons():
                q = np.asarray(poly)
                q = q[q[:, 1] < s.STOP_TOP + 1.0]
                xs |= {round(float(x), 5) for x in q[:, 0] if any(a <= x <= b for a, b in zones)}
    xs = sorted(xs)
    return [round((a + b) / 2, 5) for a, b in zip(xs, xs[1:]) if b - a > 2e-5]


JAMB_ZONES = [(-H_ - 0.35, -s.STOP_X0 + 0.35), (s.STOP_X0 - 0.35, H_ + 0.35)]


def build_rig(curtain_part, wall, floor_part, xs, printed, gw=GW, gc=GC, label="", zones=None):
    if printed:
        xs = sorted(set(xs) | set(jamb_stations(curtain_part, wall, gw, gc, JAMB_ZONES if zones is None else zones)))
    return Rig(curtain_part, wall, floor_part, xs, printed, gw, gc, label)


# the doorway round the opening (the curtain never rises above 65.1, nor goes past the jambs), and the
# floor's edge under it
wall_near = ew ^ s.box(-H_ - 5, H_ + 5, -s.BIG, s.BIG, -1, s.MOUTH + 8)
floor_near = fl ^ s.box(-H_ - 5, H_ + 5, -s.L / 2 - 1, -(s.L / 2 - 15), -1, s.ZF + 1)
XS = stations(edges_of(), -s.CUR_HALF - 0.1, s.CUR_HALF + 0.1,
              fine=[sg * (32.25 + 0.1 * k) for sg in (1, -1) for k in range(14)])
rigs = {"drawn": build_rig(cur, wall_near, floor_near, XS, False, label="drawn"),
        "printed": build_rig(cur, wall_near, floor_near, XS, True, label="printed")}
for gw_, gc_ in GROWTHS:
    rigs[(gw_, gc_)] = build_rig(cur, wall_near, floor_near, XS, True, gw_, gc_, label=f"{gw_} / {gc_}")
rd, rp = rigs["drawn"], rigs["printed"]
print(f"     ({len(XS)} stations from -{s.CUR_HALF + 0.1:.2f} to {s.CUR_HALF + 0.1:.2f}, and as printed one more in every "
      f"interval between the printed layers' corners round the jamb stops ({rp.n_all - len(XS)} more at 0.1 / 0.05); "
      f"{len(rd.xs)} different sections drawn, {len(rp.xs)} as printed)")

# ---- 6.1 the part
cp_w, cp_b = s.to_print(s.CURTAIN_TO_PRINT, [cur_w, cur_b])
cpart = cp_w + cp_b
cb = cpart.bounding_box()
X0, Z0 = -s.CUR_HALF, s.ZF + s.G_BOT          # garage x and z at the print's X = 0 and Y = 0


def pc(x, z):
    """Garage x and z to the curtain's print X and Y."""
    return x - X0, z - Z0


csize = (cb[3] - cb[0], cb[4] - cb[1], cb[5] - cb[2])
back = cpart.slice(0.125).area()
report(len(cpart.decompose()) == 1 and abs(csize[0] - 67.13) < 0.01 and abs(csize[1] - 56.39) < 0.01
       and abs(csize[2] - 8.25) < 0.01 and abs(cb[2]) < 1e-9
       and back > 0.9 * 2 * s.CUR_HALF * (s.Z_TT - Z0),
       f"the curtain is one solid, {csize[0]:.2f} x {csize[1]:.2f} x {csize[2]:.2f} mm on the bed (spec 67.13 x 56.39 x "
       f"8.25), its back face on the bed ({back:.0f} mm2 on the first layer)")
wb_, bb_ = cp_w.bounding_box(), cp_b.bounding_box()
in_latch = s.ru_box(s.LATCH_X - s.LATCH_W / 2 - 0.1, s.LATCH_X + s.LATCH_W / 2 + 0.1, -1, 10, s.LATCH_Z - 3, s.LATCH_Z + 3)
lp = cur_b ^ in_latch
hd = cur_b - in_latch
want_lp = (s.latch_outline().area() - s.LATCH_SLOT_W * s.LATCH_SLOT_H) * s.LATCH_T
lpp = s.to_print(s.CURTAIN_TO_PRINT, [cur, lp])[1]
hdp = s.to_print(s.CURTAIN_TO_PRINT, [cur, hd])[1]
lpb, hdb = lpp.bounding_box(), hdp.bounding_box()
leg_w, leg_h = [], []
for zm in (5.15, 5.35, 5.55, 5.75):
    legs_ = [c.bounds() for c in hdp.slice(zm).decompose()]
    leg_w.append(min(b[2] - b[0] for b in legs_) if legs_ else 0.0)
    leg_h.append(min(b[3] - b[1] for b in legs_) if legs_ else 0.0)
want_w = [s.HDL_LEG + 2 * f_ for f_ in s.HDL_FILLET] + [s.HDL_LEG]      # the legs and their stepped fillet, from the
want_h = [s.HDL_HT + f_ for f_ in s.HDL_FILLET] + [s.HDL_HT]            # constants (so a tuned HDL_LEG is checked)
slot_rect = square(pc(s.LATCH_X - s.LATCH_SLOT_W / 2 + 0.05, 0)[0], pc(s.LATCH_X + s.LATCH_SLOT_W / 2 - 0.05, 0)[0],
                   pc(0, s.LATCH_Z - s.LATCH_SLOT_H / 2 + 0.05)[1], pc(0, s.LATCH_Z + s.LATCH_SLOT_H / 2 - 0.05)[1])
slot_white = (slot_rect - cp_w.slice(4.95)).area()
slot_black = (cp_b.slice(5.15) ^ slot_rect).area()
report(abs(printed_top(wb_[5]) - 5.05) < 1e-9 and abs(printed_top(bb_[2] + 1e-6) - 5.05) < 1e-9
       and abs(lp.volume() - want_lp) < 0.05 * want_lp and abs(printed_top(lpb[5]) - 5.45) < 1e-9
       and abs(printed_top(hdb[5]) - 8.25) < 1e-9 and np.allclose(leg_w, want_w, atol=0.005)
       and np.allclose(leg_h, want_h, atol=0.005) and slot_white < 1e-6 and slot_black < 1e-6,
       f"its white ends on the {printed_top(wb_[5]):.2f} layer and its black starts there: the latch plate black from "
       f"{printed_top(lpb[2] + 1e-6):.2f} to {printed_top(lpb[5]):.2f} ({lp.volume():.2f} mm3 against {want_lp:.2f} for its "
       f"outline less the slot, 0.4 thick), white under its slot ({slot_white:.6f} mm2 open, {slot_black:.6f} black in "
       f"it); the handle black to {printed_top(hdb[5]):.2f}, its legs "
       f"{', '.join(f'{w:.2f} x {h:.2f}' for w, h in zip(leg_w, leg_h))} on the 5.05, 5.25, 5.45 and 5.65 layers (the "
       f"stepped fillet; from HDL_LEG and HDL_FILLET: {', '.join(f'{w:.2f} x {h:.2f}' for w, h in zip(want_w, want_h))})")
thin_c, gap_c, over, others = 0.0, 0.0, [], []
prev = None
for a, b_, cs in layer_sections(cpart, 0.0):
    thin_c = max(thin_c, (cs - cs.offset(-0.21, MIT, 2).offset(0.21, MIT, 2)).area())
    gap_c = max(gap_c, (cs.offset(0.21, MIT, 2).offset(-0.21, MIT, 2) - cs).area())   # a gap under a line prints shut
    if prev is not None:
        for comp in (cs - prev.offset(0.2, MIT, 2)).decompose():
            if comp.area() >= 0.3:
                bx = comp.bounds()
                xg = (bx[0] + bx[2]) / 2 + X0
                kind = ("chamfer step" if abs(a - 0.25) < 1e-6 and abs(abs(xg) - (s.CUR_HALF - s.CUR_CHAMF / 2)) < 0.7
                        else "grip bridge" if abs(a - s.HDL_U1) < 1e-6 and bx[2] - bx[0] <= 2 * (s.HDL_HALF - s.HDL_LEG) + 0.01
                        else "other")
                (over if kind != "other" else others).append((kind, a, comp.area(), bx[2] - bx[0]))
    prev = cs
grip_b = [o for o in over if o[0] == "grip bridge"]
report(thin_c < 0.05 and gap_c < 0.05 and not others and len([o for o in over if o[0] == "chamfer step"]) == 2
       and len(grip_b) == 1,
       f"nothing of it on any layer is under a 0.42 line ({thin_c:.4f} mm2 at the most) and no gap under one "
       f"({gap_c:.4f}); the only things over air are "
       f"the first step of its two back chamfers ({', '.join(f'{o[2]:.2f}' for o in over if o[0] == 'chamfer step')} mm2) "
       f"and the grip's bridge on the {grip_b[0][1] if grip_b else 0:.2f} layer ({grip_b[0][3] if grip_b else 0:.2f} long "
       f"as sliced), no supports ({len(others)} other)")
# the slat grooves and the latch boss, on the 4.45..4.85 layers, along a line clear of the latch and handle
# and along the latch's own line: the closed grooves between solid slats (the top one opens into the bevel)
gw_s, n_g, sl_ = [], {}, 0.0
for zm in (4.55, 4.75):
    cs = cpart.slice(zm)
    rect = square(0.2, cb[3] - 0.2, pc(0, s.RAIL_TOP)[1] + 0.2, cb[4])
    grv = rect - cs
    sl_ = max(sl_, (grv - grv.offset(-0.21, MIT, 2).offset(0.21, MIT, 2)).area())
    for key, xg in (("clear", 12.0), ("latch", s.LATCH_X)):
        solid = scan(cs.rotate(-90), [-pc(xg, 0)[0]])[0]
        gaps = [(a2[1], b2[0]) for a2, b2 in zip(solid, solid[1:])]
        n_g[(key, zm)] = len(gaps)
        if key == "clear":
            gw_s += [b2 - a2 for a2, b2 in gaps]
# under the latch plate the grooves are filled square to the latch's whole rectangle, its corners too (the Lofted Barn
# Garage's line), so the plate's chamfered white boss has no corner over an open groove
latch_box = square(*[pc(s.LATCH_X + d, 0)[0] for d in (-s.LATCH_W / 2, s.LATCH_W / 2)],
                   *[pc(0, s.LATCH_Z + d)[1] for d in (-s.LATCH_H / 2, s.LATCH_H / 2)])
under_latch = max((latch_box - cpart.slice(zm)).area() for zm in (4.55, 4.75))
n_in = sum(1 for z_ in s.slat_lines() if s.LATCH_Z - s.LATCH_H / 2 <= z_ - s.SLAT_GROOVE_W / 2
           and z_ + s.SLAT_GROOVE_W / 2 <= s.LATCH_Z + s.LATCH_H / 2)            # the grooves wholly inside it
report(n_g[("clear", 4.55)] == s.SLATS - 2 and n_g[("clear", 4.75)] == s.SLATS - 2 and min(gw_s) >= 0.42
       and sl_ < 0.01 and under_latch < 1e-6 and n_g[("latch", 4.55)] == n_g[("latch", 4.75)] == s.SLATS - 2 - n_in,
       f"its slat grooves print open on the 4.45 and 4.65 layers: {n_g[('clear', 4.55)]} closed ones "
       f"{min(gw_s):.2f} to {max(gw_s):.2f} wide and the top one opening into the bevel ({sl_:.5f} mm2 narrower than a "
       f"line); under the latch plate they are filled square to its rectangle ({n_in} grooves; "
       f"{n_g[('latch', 4.55)]} cross the latch's line; {under_latch:.6f} mm2 of the rectangle open), so the plate's white "
       f"boss stands on solid fill, with no corner over an open groove")
l0 = cpart.slice(0.125)
xr_ = pc(s.CUR_HALF, 0)[0]
# where the back chamfers really end on the first layer: the lowest z from which the back edge is square
zq = np.arange(s.STOP_TOP - 5, s.Z_FT, 0.05)
edge_x = [r_[-1][1] if len(r_) else 0.0 for r_ in scan(l0, [pc(0, z_)[1] for z_ in zq])]
square_from = next((z_ for z_, e_ in zip(zq, edge_x) if abs(e_ - xr_) < 1e-6), s.Z_FT)
below = scan(l0, [pc(0, square_from - 0.1)[1]])[0]
miss_root = max((square(pc(a1, 0)[0], pc(a2, 0)[0], pc(0, square_from + 0.05)[1], pc(0, s.Z_TT - 0.01)[1]) - l0).area()
                for a1, a2 in ((s.FING_ROOT, s.CUR_HALF), (-s.CUR_HALF, -s.FING_ROOT)))
report(abs(below[-1][1] - (xr_ - s.CUR_CHAMF + 0.125)) < 0.06 and s.Z_FT - square_from >= 2.0
       and square_from - s.STOP_TOP >= 5.9 and miss_root < 1e-6,
       f"its back chamfers end at z {square_from:.2f} (measured on the first layer: the back edge "
       f"{xr_ - below[-1][1]:.3f} in from the side just under it, square from there up), {s.Z_FT - square_from:.2f} under "
       f"the body's top (at least 2: the fingers' root blocks, x +-{s.FING_ROOT}..{s.CUR_HALF:.3f}, stand on square body "
       f"over their whole footprint, {miss_root:.6f} mm2 missing) and {square_from - s.STOP_TOP:.2f} over the jamb stops' "
       f"top (spec 6, so the square corner stays clear of the stops on every path)")

# ---- 6.2 the seat, as drawn
I3 = np.eye(3)
sd0 = rd.springs(I3)
bot = (cur.bounding_box()[2] - s.ZF)
report(rd.rigid(I3) < 1e-6 and abs(sd0["fbend"] - s.PRELOAD) < 1e-6 and abs(sd0["tb_u"].max() - (s.TAB_BUMP_U - s.REB_U)) < 1e-6
       and sd0["strip"] < 1e-6 and abs(bot - s.G_BOT) < 1e-6,
       f"seated as drawn its rigid part touches nothing ({rd.rigid(I3):.6f} mm2 at the worst station), the finger bumps "
       f"stand {sd0['fbend']:.3f} into their pads and the tab bumps {sd0['tb_u'].max():.3f} into the rebate's front, each "
       f"spring's strip and bump, moved by its own bend, touch nothing ({sd0['strip']:.6f} mm2), and its bottom face is "
       f"{bot:.3f} over the floor top")

# ---- 6.3 where the springs settle it
seats = {k: settle(r_) for k, r_ in rigs.items()}
pre = {k: rigs[k].springs(removal_pose(seats[k])) for k in rigs}
rows = []
for k in rigs:
    rows.append(f"{rigs[k].label} {seats[k][0]:+.3f}, {seats[k][1]:+.3f} (finger {pre[k]['fbend']:.2f}, tab "
                f"{pre[k]['tb_u'].max():.2f})")
# the printed seats again in 3D, on the parts cut into their layers and grown (no stations): the rigid curtain at
# each seat touches nothing, and let down one search step it does
rigid_cur = cur - s.union(list(s.spring_regions().values()))
solid_w, solid_c = {}, {}
seat3d, seat3d_rows = 0.0, []
for k in rigs:
    if k == "drawn":
        continue
    gw_, gc_ = (GW, GC) if k == "printed" else k
    if gw_ not in solid_w:
        solid_w[gw_] = s.union([printed_solid(wall_near, gw_), printed_solid(floor_near, gw_, True)])
    if gc_ not in solid_c:
        solid_c[gc_] = printed_solid(rigid_cur, gc_)
    at = overlap(solid_c[gc_].transform(pose_3d(removal_pose(seats[k]))), solid_w[gw_])
    below = overlap(solid_c[gc_].transform(pose_3d(removal_pose(seats[k], dz=-0.025))), solid_w[gw_])
    seat3d = max(seat3d, at)
    seat3d_rows.append(f"{rigs[k].label} {at:.5f} ({below:.3f} let down 0.025)")
    seat3d = max(seat3d, 1.0 if below < 1e-3 else 0.0)
report(all(pre[k]["fbend"] > 0.1 and pre[k]["tb_u"].max() > 0.1 for k in rigs) and seat3d < 1e-3
       and pre["printed"]["strip"] < 1e-4,
       "settled (searched 0.8 each way; seat out and up from as drawn, then the finger and tab preloads): "
       + "; ".join(rows) + " (spec H.2: drawn -0.05, -0.10 (0.45, 0.15); printed +0.20, +0.30 (1.05, 0.40)); every "
       "preload over 0.1; in 3D, the rigid curtain as printed at each printed seat overlaps the doorway as printed by "
       + ", ".join(seat3d_rows) + " mm3 (under 0.001 at the seat); as printed, at its seat each spring's strip and bump, "
       f"moved by its own bend, touch nothing ({pre['printed']['strip']:.6f} mm2, under 0.0001; "
       + ", ".join(f"{rigs[k].label} {pre[k]['strip']:.6f}" for k in GROWTHS) + " at the growth cases)")

# ---- 6.4 held
held, held_min = [], 9.0
for k in ("drawn", "printed"):
    r_, sd = rigs[k], seats[k]
    vals = [r_.rigid(removal_pose(sd, lf, du=du, dz=dz)) for du, dz, lf in ((0.25, 0, 0), (-0.1, 0, 0), (0, -0.1, 0),
                                                                          (0.5, 0, 0.3))]
    held.append(f"{k}: out 0.25 {vals[0]:.3f}, in 0.1 {vals[1]:.3f}, down 0.1 {vals[2]:.3f}, out 0.5 lifted 0.3 {vals[3]:.3f}")
    held_min = min(held_min, min(vals))
# sideways, in 3D (the rigid curtain, the springs taken out): pushed either way in steps of 0.025, how far it goes
# before it meets anything (over 0.01 mm3), and what it meets: the jamb stops, the 45 degree faces behind its
# chamfered back edges, before its side gap to the jambs (0.30 drawn, 0.15 as printed, the wall and curtain grown)
# closes. Drawn they touch it already; as printed both are stairs, which leave a little play before they meet
STOPS_3D = s.union([s.ru_box(*s.xspan(sg, s.STOP_X0 - 0.2, H_ + 0.02), -0.1, H_ - s.STOP_X0 + 0.2, s.ZF - 0.02,
                             s.STOP_TOP + 0.02) for sg in (1, -1)])
side, side_rows = [], []
for k, wl_, cr_ in (("drawn", s.union([ew, fl]), rigid_cur), ("printed", solid_w[GW], solid_c[GC])):
    seated = cr_.transform(pose_3d(removal_pose(seats[k])))
    gap_ = s.RU_CLR_X - (0 if k == "drawn" else GW + GC)
    for sg in (1, -1):
        d_, v_stop, v_else = 0.0, 0.0, 0.0
        while d_ < gap_ + 0.1:
            d_ = round(d_ + 0.025, 3)
            moved = seated.translate([sg * d_, 0, 0])
            v_stop, v_else = overlap(moved, wl_ ^ STOPS_3D), overlap(moved, wl_ - STOPS_3D)
            if v_stop + v_else > 0.01:
                break
        side.append(d_ <= gap_ - 0.02 and v_stop > v_else)
        side_rows.append(f"{k} {'+' if sg > 0 else '-'}x: meets them at {d_:.3f} (its side gap {gap_:.2f}; "
                         f"{v_stop:.2f} mm3 into the stops, {v_else:.3f} into anything else)")
report(held_min > TOL and all(side),
       f"from its seat it is held: pushed it meets rigid parts ({'; '.join(held)} mm2 at the worst station); in 3D, "
       f"pushed sideways it meets the jamb stops before its side gap to the jambs closes: " + "; ".join(side_rows))
plays = []
for k in GROWTHS:
    r_, sd = rigs[k], seats[k]
    pl_ = 0.0
    for j in range(1, 60):
        if r_.rigid(A_rot(j * 0.01, 0.0, s.STOP_TOP + sd[1]) @ A_shift(*sd)) > 1e-5:
            break
        pl_ = j * 0.01
    plays.append((k, math.radians(pl_) * (s.STOP_TOP - (s.ZF + 0.5))))
pl_print = 0.0
for j in range(1, 60):
    if rp.rigid(A_rot(j * 0.01, 0.0, s.STOP_TOP + seats["printed"][1]) @ A_shift(*seats["printed"])) > 1e-5:
        break
    pl_print = math.radians(j * 0.01) * (s.STOP_TOP - (s.ZF + 0.5))
report(max(pl for _, pl in plays) <= 0.15 and pl_print <= 0.15,
       f"its bottom's free play, turned bottom out about the stops' top: {pl_print:.3f} as printed; "
       + ", ".join(f"{gw_} / {gc_}: {pl:.3f}" for (gw_, gc_), pl in plays)
       + " mm (spec D.5: 0 at 0.1 / 0.05, 0.14 at 0.1 / 0.1; at most 0.15)")

# ---- 6.5 the hand numbers, with the springs' real rates (spec G, D.3, D.4; hand2.py)
WEIGHT = s.CUR_WEIGHT_G * 9.81e-3         # N: the review's test slice, 11.55 g white and 0.13 g black
# The spring finger, as fe2d.py worked it out with the load 15.6 from its root (the bump's middle): 3.988 mm/N at
# E 3000, its tip 1.107 times as far as the load, 0.795 % strain per mm of bend at the root radius. Bent, the finger
# slopes (about 12 degrees at the stop), so the flat pad bears on the tilted bump only along the nearer-the-root
# edge of where they cross (the pad's, or the bump's), and the load is that far from the root, not at the bump's
# middle. A beam with a root spring fitted to fe2d.py's numbers at 15.6 gives the rate, the tip and the strain
# for the load anywhere along the bump.
FE_A, FE_COMP, FE_TIP, FE_EPS = 15.6, 3.988, 1.107, 0.795
EI_F = 3000.0 * s.TONGUE_T * s.FING_H ** 3 / 12          # N mm2, bending down (in the bed plane)
XI_T = s.FING_ROOT - s.FING_TIP                          # 16.9: its free end from the root
CR_F = (FE_COMP - FE_A ** 3 / (3 * EI_F)) / FE_A ** 2    # the root's own give, rad per N mm


def f_comp(a):
    return a ** 3 / (3 * EI_F) + CR_F * a ** 2


def f_tip_raw(a):
    return (a ** 3 / (3 * EI_F) + a ** 2 * (XI_T - a) / (2 * EI_F) + CR_F * a * XI_T) / f_comp(a)


def finger(a):
    """The finger loaded a from its root: (mm per N at E 3000, its tip over its bend there, % strain per mm)."""
    return (f_comp(a), FE_TIP * f_tip_raw(a) / f_tip_raw(FE_A),
            FE_EPS * (a / f_comp(a)) / (FE_A / f_comp(FE_A)))


def contact_a(gw, gc):
    """How far from the finger's root the pad bears on its tilted bump: at the root-side end of where the pad
    (grown gw) and the bump (grown gc) cross."""
    return s.FING_ROOT - min(s.PAD_X1 + gw, s.BUMP_X1 + gc)


A_D, A_P = contact_a(0.0, 0.0), contact_a(GW, GC)
FIN_D, FIN_P = finger(A_D), finger(A_P)
kf = {E: E / 3000.0 / FIN_D[0] for E in (2500.0, 3500.0)}
Lt = s.TAB_ROOT - (s.TAB_BUMP_X0 + s.TAB_BUMP_X1) / 2
It = s.TAB_W * s.TAB_T ** 3 / 12
kt = (3 * 2500.0 * It / Lt ** 3 * 0.60, 3 * 3500.0 * It / Lt ** 3 * 0.61)   # fe3d_tab.py: 0.60..0.61 of the clamped
zc = (s.RAIL_Z0 + s.Z_FT) / 2
zt_ = s.Z_TT - s.TAB_W / 2
zb_ = s.ZF + 0.45
face_down = WEIGHT * (zc - zb_) / (zt_ - zb_)
f_pre, t_pre = pre["drawn"]["fbend"], pre["drawn"]["tb_u"].max()
Ff = (2 * kf[2500.0] * f_pre, 2 * kf[3500.0] * f_pre)
Ft = (2 * kt[0] * t_pre, 2 * kt[1] * t_pre)
stops = {k: rigid_stop(rigs[k], seats[k]) for k in rigs}
fb_stop = rd.springs(removal_pose(seats["drawn"], stops["drawn"]))["fbend"]
report(Ff[0] / WEIGHT > 1.5 and Ft[0] / face_down > 1.5,
       f"held by its springs at the drawn preloads (fingers {kf[2500.0]:.3f}..{kf[3500.0]:.3f} N/mm each, the pad bearing "
       f"on the bump {A_D:.2f} from the finger's root, {A_P:.2f} as printed; tabs "
       f"{kt[0]:.3f}..{kt[1]:.3f}, for E 2500..3500): upside down the fingers' pair {Ff[0]:.3f}..{Ff[1]:.3f} N holds "
       f"{Ff[0] / WEIGHT:.2f}..{Ff[1] / WEIGHT:.2f} times its {WEIGHT:.4f} N weight; face down the tabs' pair "
       f"{Ft[0]:.3f}..{Ft[1]:.3f} N holds {Ft[0] / face_down:.2f}..{Ft[1] / face_down:.2f} times the {face_down:.4f} N "
       f"needed (spec G: 1.64..2.30 and 1.71..2.43; over 1.5)")
tab_bends = []
leg_layers = []
for k_, (u0_, f_) in enumerate(zip((5.05, 5.25, 5.45, 5.65), list(s.HDL_FILLET) + [0.0])):
    cs = hdp.slice(u0_ + 0.1)
    comp = [c.bounds() for c in cs.decompose() if c.bounds()[2] - c.bounds()[0] < 2 * s.HDL_HALF - 1]
    bb2 = comp[0] if comp else (0, 0, 0, 0)
    b2, h2 = bb2[2] - bb2[0], bb2[3] - bb2[1]
    leg_layers.append((u0_, b2, h2, 2 * 10.0 * b2 * h2 ** 2 / 6 / ((s.HDL_U1 + s.HDL_U2) / 2 - u0_)))
legs_c = sorted((c.bounds()[0] + c.bounds()[2]) / 2 for c in hdp.slice(5.75).decompose())
leg_c = legs_c[-1] - legs_c[0] if len(legs_c) == 2 else 0.0
gx = scan(hdp.slice(s.HDL_U1 + 0.1).rotate(-90), [-pc(0.0, 0)[0]])[0]
grip_h = (gx[0][1] - gx[0][0]) if len(gx) else 0.0
gu = [z0_ for z0_, z1_, cs_ in layer_sections(hdp, 0.0) if not (cs_ ^ square(pc(-0.5, 0)[0], pc(0.5, 0)[0], -1, 99)).is_empty()]
grip_t = (max(gu) + 0.2 - min(gu)) if gu else 0.0
F_grip = 4 * 45.0 * (grip_t * grip_h ** 2 / 6) / leg_c
F_break = min(min(q[3] for q in leg_layers), F_grip)
fb_stop_p = rp.springs(removal_pose(seats["printed"], stops["printed"]))["fbend"]
eps_stop = max(FIN_D[2] * fb_stop, FIN_P[2] * fb_stop_p)
report(F_break >= 20 and eps_stop < 2.0,
       f"the handle, measured off the part at 10 MPa across every layer: its legs "
       + ", ".join(f"{q[1]:.2f} x {q[2]:.2f} at {q[0]:.2f} {q[3]:.1f} N" for q in leg_layers)
       + f"; the grip {grip_t:.2f} x {grip_h:.2f} on {leg_c:.2f} leg centres {F_grip:.1f} N simply supported: it breaks at "
       f"{F_break:.1f} N (at least 20); the fingers' strain at the stop {FIN_D[2] * fb_stop:.2f} % drawn at a "
       f"{fb_stop:.2f} bend ({FIN_D[2]:.3f} % a mm, the pad {A_D:.2f} from the root), {FIN_P[2] * fb_stop_p:.2f} % as printed "
       f"at {fb_stop_p:.2f} ({FIN_P[2]:.3f}, {A_P:.2f}) (under 2 %)")
# not leaned in enough going back in (6.9), the door stops dead with its two tab bumps caught under the head's flat
# underside and the fingers not yet bent: a harder push goes through the tabs in their stiff, flat direction, the
# plate 0.65 by 2.2 bent edgewise, along its print lines (45 MPa), the load at the bump 9.0 from the root
tab_break = 45.0 * s.TAB_T * s.TAB_W ** 2 / 6 / TAB_A
lift_max = (2 * 3500.0 / 3000.0 / FIN_P[0] * fb_stop_p + WEIGHT
            + 0.3 * 2 * kt[1] * pre["printed"]["tb_u"].max())
report(tab_break >= lift_max,
       f"pushed up with its tab bumps caught under the head (not leaned in enough going back in), each tab breaks "
       f"edgewise at about {tab_break:.1f} N (45 MPa along its lines), {2 * tab_break:.1f} N for the two: "
       f"{2 * tab_break / lift_max:.1f} times the hardest lift to the stop ({lift_max:.2f} N as printed at E 3500, its "
       f"weight and the tabs' friction too; at least 2): the read-me says not to push harder when it stops dead")

# ---- 6.6 the lift window
needs = {}
for k in rigs:
    needs[k] = least_lift(rigs[k], seats[k], stops[k])
win = {k: (stops[k] - needs[k]) if needs[k] is not None else -1 for k in rigs}
tip = {}
for k in ("drawn", "printed"):
    r_, sd = rigs[k], seats[k]
    i_tip = int(np.argmin(np.abs(np.abs(r_.xs) - (s.FING_TIP + 0.05)) + 9 * shapely.is_empty(r_.F)))
    strip_low = r_.F[i_tip].bounds[1]          # the slot measured under the finger only (u -0.5..TONGUE_T)
    body_top = shapely.intersection(r_.R[i_tip], sbox(-0.5, 0, s.TONGUE_T - 0.01, strip_low - 0.01)).bounds[3]
    bend = r_.springs(removal_pose(sd, stops[k]))["fbend"]
    tip[k] = (strip_low - body_top, bend, (FIN_D if k == "drawn" else FIN_P)[1] * bend)
report(stops["drawn"] > 0 and stops["printed"] >= 1.0 and all(t[0] - t[2] >= 0.2 for t in tip.values()),
       f"lifted straight up it stops rigidly (the tongue's top on the rebate's) at {stops['drawn']:.3f} drawn and "
       f"{stops['printed']:.3f} as printed (spec 1.70, 1.10; at least 1.0 printed), "
       + ", ".join(f"{rigs[k].label} {stops[k]:.3f}" for k in GROWTHS)
       + f" at the growth cases (spec 1.65, 0.75, 0.65, 0.90); there the finger's tip ({FIN_D[1]:.3f} x its "
       f"{tip['drawn'][1]:.2f} bend where the pad bears = {tip['drawn'][2]:.2f} drawn, {FIN_P[1]:.3f} x "
       f"{tip['printed'][1]:.2f} = {tip['printed'][2]:.2f} printed) is {tip['drawn'][0] - tip['drawn'][2]:.2f} inside its "
       f"{tip['drawn'][0]:.2f} slot drawn and {tip['printed'][0] - tip['printed'][2]:.2f} inside the {tip['printed'][0]:.2f} "
       f"printed one (at least 0.2)")
not_empty = {k: max(rigs[k].rigid(removal_pose(seats[k], 0.3, a)) for a in (1, 2, 4, 6)) for k in ("drawn", "printed")}
report(needs["drawn"] is not None and needs["printed"] is not None and win["printed"] >= 0.4
       and all(win[k] >= 0.3 for k in GROWTHS) and min(not_empty.values()) > TOL,
       f"the least lift that lets it out (7 degrees about its front at the mouth, 10 steps a phase) is "
       f"{needs['drawn']} drawn and {needs['printed']} as printed (spec 0.80, 0.55), so the window under the stop is "
       f"{win['drawn']:.2f} and {win['printed']:.2f} (at least 0.4 printed), and "
       + ", ".join(f"{rigs[k].label} {win[k]:.2f}" for k in GROWTHS)
       + f" at the growth cases (at least 0.3); not empty: lifted 0.3 and swung 1 to 6 degrees it is blocked "
       f"({not_empty['drawn']:.3f} drawn, {not_empty['printed']:.3f} printed mm2)")

# ---- 6.7 the removal path (spec H.3)
NAMED = {"lip (wedge)": s.ru_box(-H_ - 0.02, H_ + 0.02, s.LIP_U0 - 0.05, s.WT + 0.05, s.ZF - 0.02, s.ZF + s.LIP_H + 0.02),
         "jamb stops": s.union([s.ru_box(*s.xspan(sg, s.STOP_X0 - 0.2, H_ + 0.02), -0.1, H_ - s.STOP_X0 + 0.2,
                                         s.ZF - 0.02, s.STOP_TOP + 0.02) for sg in (1, -1)]),
         "head in front of the rebate": s.ru_box(-H_ - 0.02, H_ + 0.02, s.REB_U, s.WT - s.EMBED, s.MOUTH - 0.02, s.MOUTH + 10),
         "rebate top": s.ru_box(-H_, H_, -0.1, s.REB_U, s.MOUTH + s.REB_H - 0.02, s.MOUTH + 10),
         "ribs": s.union([s.ru_box(x - s.RIB_W / 2 - 0.05, x + s.RIB_W / 2 + 0.05, -0.1, s.REB_U, s.MOUTH - 0.02,
                                   s.MOUTH + s.REB_H) for x in s.RIB_XS]),
         "pads": PAD_REGION,
         "casing": s.ru_box(-H_ - s.TRIM - 0.1, H_ + s.TRIM + 0.1, s.WT - s.EMBED, s.WT + s.PROUD + 0.1, s.MOUTH - 0.02,
                            s.MOUTH + s.TRIM + 0.5),
         "posts": s.union([s.ru_box(x - s.SW / 2 - 0.05, x + s.SW / 2 + 0.05, -0.1, s.POST_EXT_U + 0.05, -1,
                                    s.ZF + s.LIP_H + 0.02) for x in s.CURTAIN_POSTS])}
NAMED["lip (wedge)"] = NAMED["lip (wedge)"] - NAMED["posts"]


def named_sections(rig, printed, gw=GW):
    out = {}
    for k, reg in NAMED.items():
        m_ = wall_near ^ reg
        out[k] = np.array(printed_sections(m_, gw, list(rig.xs)) if printed else drawn_sections(m_, list(rig.xs)), dtype=object)
    sk = wall_near ^ s.ru_box(-H_ - 3, H_ + 3, -30, s.WT + 0.05, -1, s.ZF - 0.02) - NAMED["posts"]
    a_ = printed_sections(sk, gw, list(rig.xs)) if printed else drawn_sections(sk, list(rig.xs))
    b_ = printed_floor_sections(floor_near, gw, list(rig.xs)) if printed else drawn_sections(floor_near, list(rig.xs))
    out["skirt and floor"] = np.array([shapely.union(x_, y_) for x_, y_ in zip(a_, b_)], dtype=object)
    return out


def least_gaps(rig, named, poses):
    least = {}
    for A in poses:
        Rm = apply(A, rig.R)
        for k, g in named.items():
            ok = ~shapely.is_empty(g)
            if ok.any():
                least[k] = min(least.get(k, 99.0), np.nanmin(shapely.distance(Rm[ok], g[ok])))
    return least


rm_rows, rm_ok = [], True
for k in ("drawn", "printed"):
    r_, sd = rigs[k], seats[k]
    nd_k = needs[k] if needs[k] is not None else stops[k]     # (6.6 has failed if there is no least lift)
    lifts = sorted({round(nd_k + 0.1 * j, 3) for j in range(0, 20) if nd_k + 0.1 * j <= stops[k] + 1e-9}
                   | {round(stops[k] - 0.15, 3), round(stops[k], 3)})
    w_all, f_all, t_all, s_all, z_all = 0.0, 0.0, 0.0, 0.0, 0.0
    for lf in lifts:
        for th in (6.0, 7.0, 8.0):
            w_, f_, t_, s_, z_, _ = run(r_, removal_phases(sd, lf, th))
            w_all, f_all, t_all, s_all, z_all = max(w_all, w_), max(f_all, f_), max(t_all, t_), max(s_all, s_), max(z_all, z_)
    fb_lim = r_.springs(removal_pose(sd, stops[k]))["fbend"]
    ok = w_all <= TOL and f_all <= fb_lim + 1e-6 and t_all <= 0.9 and s_all <= TOL and z_all <= 0.02
    rm_ok = rm_ok and ok
    rm_rows.append(f"{k}, lifts {lifts[0]:.2f} to {lifts[-1]:.2f} ({len(lifts)}): rigid {w_all:.5f} mm2, finger bend "
                   f"{f_all:.2f} (its stop's {fb_lim:.2f}), tab bend {t_all:.2f}, strips {s_all:.5f} mm2, a tab bump "
                   f"pushed in by a move in z {z_all:.3f}")
report(rm_ok, "it comes out by spec H.3 (lift, swing 6, 7 and 8 degrees about its front at the mouth, drop, out 15) "
              "at every lift from the least to the stop in 0.1 steps and the stop less 0.15, touching nothing rigid; "
       + "; ".join(rm_rows))
gap_rows = []
for k, lfs in (("drawn", (1.0, round(stops["drawn"] - 0.15, 3))), ("printed", (0.8, round(stops["printed"] - 0.15, 3)))):
    r_, sd = rigs[k], seats[k]
    nm = named_sections(r_, k == "printed")
    for lf in lfs:
        ph = removal_phases(sd, lf, 7.0)
        g = least_gaps(r_, nm, [A for _, poses in ph[1:] for A in poses])
        gap_rows.append(f"{k} L {lf:.2f}: " + ", ".join(f"{q} {v:.2f}" for q, v in g.items()))
report(True, "least gaps after the lift, swinging 7 degrees (spec H.3's table): " + "; ".join(gap_rows))

# ---- 6.8 the hand motions (the judges' must-fix)
hm_rows, hm_ok = [], True
for k in ["drawn", "printed"] + GROWTHS:
    r_, sd = rigs[k], seats[k]
    if k in ("drawn", "printed"):
        lifts = sorted({round(0.6 + 0.1 * j, 3) for j in range(0, 20) if 0.6 + 0.1 * j <= stops[k] - 0.1 + 1e-9}
                       | {round(stops[k] - 0.1, 3)})
    else:
        lifts = [round(stops[k] - 0.15, 3)]
    for name, fn in MOTIONS.items():
        row = []
        for lf in lifts:
            tc, need_ = motion(r_, sd, lf, fn(sd, lf))
            hm_ok = hm_ok and need_ is not None
            row.append(f"{lf:.2f}:{tc:g}/{need_}")
        hm_rows.append(f"{r_.label} {name} " + " ".join(row))
# and at each growth case the plain H.3 removal (the front pivot) at the stop less 0.15, swung 6, 7 and 8 degrees
rm15 = {k: max(run(rigs[k], removal_phases(seats[k], round(stops[k] - 0.15, 3), th), want_springs=False)[0]
               for th in (6.0, 7.0, 8.0)) for k in GROWTHS}
report(hm_ok and max(rm15.values()) <= TOL,
       "each hand motion lets it out with less swing than its first contact (lift: first contact / least swing "
       "that clears, degrees), at every lift from 0.6 to the stop less 0.1, drawn and printed, and at the stop "
       "less 0.15 at the growth cases: " + "; ".join(hm_rows) + "; and at the growth cases, lifted to the stop less "
       "0.15, the plain H.3 removal (swung 6, 7 and 8 degrees about its front at the mouth) touches nothing rigid: "
       + ", ".join(f"{rigs[k].label} {rm15[k]:.5f}" for k in GROWTHS) + " mm2")

# ---- 6.9 putting it in (spec H.5, review finding M1)
PHIS = [round(0.1 * j, 1) for j in range(15)]
ins = {}
for k in ("drawn", "printed"):
    r_, sd = rigs[k], seats[k]
    for th in (6.0, 7.0, 8.0):
        for phi in PHIS:
            ins[(k, th, phi)] = insertion(r_, sd, stops[k], needs[k], th, phi)


def band(res, k, th):
    good = [v["lean"] for (k_, t_, _), v in res.items() if k_ == k and t_ == th and v["what"] == "works"]
    return (max(good), min(good)) if good else (None, None)


# leaned in, the door reaches its rigid stop tipped 5 to 9 degrees, and its 1.25 deep finger bump meets the pad with
# its front corner first, up to 0.1 higher than square (1.25 x sin 9 degrees = 0.2, half of it at the bump's middle):
# so going in the finger may bend up to FB_TILT more than at the straight-up stop. Its strain and its tip in the
# printed slot are proved at the most it bends (spec H.5 said 2.15 at most; measured on the real sections, see below)
FB_TILT = 0.1
# taken at the top of every insertion pose that reaches a stop with a bump on its pad, works or past the band, and over
# the works poses' paths too; none works: fails below. Past the band a bump counts as on its pad if it is under it by 0.2
# or more by the u extent of where the two overlap (the older measure, so the marginal poses the top-edge measure moves
# out of the band are still counted). Leaned in further, the pad's back edge meets the bump's front corner or face (the
# top-edge overlap 0 to 0.08), which pushes the bump back more than down; its bump top less pad bottom there is proved
# under 2 % strain in the leaned-too-far line after 6.10
on_pad = lambda v: v["what"] == "works" or (v["what"].startswith("leaned too far") and v.get("fpad_area", 0.0) >= 0.2)
fb_rows = [(v["fbend_top"], key) for key, v in ins.items() if on_pad(v)]
fb_rows += [(v["fbend"], key) for key, v in ins.items() if v["what"] == "works"]
n_marg = sum(1 for v in ins.values() if v["what"] != "works" and on_pad(v))
fb_ins, fb_at = max(fb_rows, default=(99.0, ("none", 0.0, 0.0)))
fb_case = {k: max([b_ for b_, key in fb_rows if key[0] == k], default=99.0) for k in ("drawn", "printed")}
fb_stop_k = {"drawn": fb_stop, "printed": fb_stop_p}      # each case against its own straight-up stop (as the LBG's)
ins_ok, ins_rows = (all(fb_case[k] <= fb_stop_k[k] + FB_TILT for k in fb_case) and FIN_P[2] * fb_ins < 2.0
                    and tip["printed"][0] - FIN_P[1] * fb_ins >= 0.1), []


def band_all(res, k):
    """The lean band over every swing tried: (its top end, its far end)."""
    good = [v["lean"] for (k_, _, _), v in res.items() if k_ == k and v["what"] == "works"]
    return (max(good), min(good)) if good else (None, None)


ba_d, ba_p = band_all(ins, "drawn"), band_all(ins, "printed")
common_all = (min(ba_d[0], ba_p[0]) - max(ba_d[1], ba_p[1])) if None not in ba_d + ba_p else 0.0
ins_ok = ins_ok and common_all >= 0.4
after_top = sorted(f"{k_} {t_:g}/{p_:.1f}" for (k_, t_, p_), v in ins.items() if v["what"] == "rigid contact after the top")
ins_ok = ins_ok and not after_top             # no pose that went up is stopped rigidly on its way down and in
for th in (6.0, 7.0, 8.0):
    bd, bp = band(ins, "drawn", th), band(ins, "printed", th)
    common = (min(bd[0], bp[0]) - max(bd[1], bp[1])) if None not in bd + bp else 0.0
    no_lean = [ins[(k, th, 0.0)]["what"] for k in ("drawn", "printed")]
    bad = [v for (k_, t_, _), v in ins.items() if t_ == th and v["what"] == "works"
           and (v["zload"] > 0.02 or v["strip"] > TOL)]
    ins_ok = ins_ok and common >= 0.3 and all(w.startswith("catches") for w in no_lean) and not bad
    ins_rows.append(f"swung {th:g}: works with the tongue's back at the mouth {bd[0]:+.2f} to {bd[1]:+.2f} drawn and "
                    f"{bp[0]:+.2f} to {bp[1]:+.2f} printed ({common:.2f} common, at least 0.3); with no lean it "
                    f"{no_lean[0]} drawn, {no_lean[1]} printed" if None not in bd + bp else f"swung {th:g}: no lean works")
report(ins_ok, "it goes back in by spec H.5 (leaned in, pushed up until it stops, let down to every lift in the window "
               "and the top let out and the bottom pushed in one after the other, and let down about 1 mm and the two "
               "together; a finger bump is under its pad when the u overlap of its top edge, which bears on the pad, "
               "with the pad is 0.2 or more): "
       + "; ".join(ins_rows) + "; over the three swings it works from "
       + (f"{ba_d[0]:+.2f} to {ba_d[1]:+.2f} drawn and {ba_p[0]:+.2f} to {ba_p[1]:+.2f} printed" if None not in ba_d + ba_p
          else "nowhere") + f", {common_all:.2f} common (spec L.6.9: at least 0.4; spec: catches at -0.10 with no lean, "
       f"works -0.28 to -0.77 drawn, -0.28 to -0.85 printed); no tab bump is loaded by a move in z, every finger bump is "
       f"under its pad by 0.2 or more before the top comes out, nothing rigid touches (no pose stopped rigidly after "
       f"the top{': ' + ', '.join(after_top) if after_top else ''}); at the top of every pose that "
       f"reaches its stop with a bump on its pad, works or past the band ({n_marg} past it), the fingers bend at most "
       f"{fb_case['drawn']:.2f} drawn and {fb_case['printed']:.2f} printed (the most at {fb_at[0]} "
       f"{fb_at[1]:g}/{fb_at[2]:.1f}; {fb_case['drawn'] - fb_stop:+.2f} and {fb_case['printed'] - fb_stop_p:+.2f} on the "
       f"straight-up stop's {fb_stop:.2f} and {fb_stop_p:.2f}, at most {FB_TILT}: the bump "
       f"tipped with the door), {FIN_P[2] * fb_ins:.2f} % strain as printed (under 2 %), the tip "
       f"{tip['printed'][0] - FIN_P[1] * fb_ins:.2f} inside the printed slot (at least 0.1)")
# either side of the band. Not leaned in enough, it stops dead: the tab bumps caught under the head, short of where a
# leaned door stops and before the fingers bend, so with no spring to feel (pushed harder, the tabs take it edgewise,
# 6.5). Leaned in too far, the finger bumps come up behind their pads; at step 4 nothing rigid stops the top, which
# comes out pushing them back toward the room: the door then sits with no push down from its fingers and lifts with
# no spring. The fingers are thin that way (1.05), so that bend is mild; and nothing of the doorway stands behind the
# wall's inside face round the opening (the rebate is open to the room), so held there the bumps touch only the
# pads' backs and the door lifts out as usual, and is put back leaning less (the read-me's symptom and remedy)
EI_U = 3000.0 * s.FING_H * s.TONGUE_T ** 3 / 12
behind_wall = overlap(wall_near, s.ru_box(-H_ - 4, H_ + 4, -6, -0.001, s.ZF + 0.5, s.MOUTH + 8))
short_, catch_fb, over_rows, over_ok, ub_most = [], [], [], True, 0.0
ub_k, past_keys = {"drawn": 0.0, "printed": 0.0}, []
for k in ("drawn", "printed"):
    for th in (6.0, 7.0, 8.0):
        tops_ = [v["top"] for (k_, t_, _), v in ins.items() if k_ == k and t_ == th and v["what"] == "works"]
        hi_band, lo_band = band(ins, k, th)
        for phi in PHIS:
            v = ins[(k, th, phi)]
            # the shortfall only from poses leaned in less than the band's top end (under-leaned): past its far end a
            # tab bump can graze the rebate's ceiling as an over-leaned door rises high, which is a rigid stop
            if (v["what"].startswith("catches") and v["catch"] is not None and tops_
                    and hi_band is not None and v["lean"] > hi_band + 1e-9):
                short_.append(min(tops_) - v["catch"][0])
                catch_fb.append(v["catch"][1])
            if lo_band is not None and v["lean"] < lo_band - 1e-9:      # past the band's far end
                ok_ = (v["what"].startswith("leaned too far") or v["what"] == "blocked coming in under the head"
                       or v["what"].startswith("catches"))
                over_ok = over_ok and ok_
                ub_most = max(ub_most, v.get("u_bend", 0.0))
                ub_k[k] = max(ub_k[k], v.get("u_bend", 0.0))
                if v["top"] is not None:
                    past_keys.append((k, th, phi))
eps_u = 100 * 3 * (s.TONGUE_T / 2) * ub_most / A_D ** 2
f_u = 3 * EI_U / A_D ** 3 * ub_most
n_behind = sum(1 for v in ins.values() if v["what"].startswith("leaned too far: its springs"))
report(over_ok and eps_u < 2.0 and behind_wall < 1e-6 and short_ and min(short_) >= 1.5,
       f"either side of the lean band, what Alan feels: not leaned in enough it stops dead {min(short_, default=0):.1f} to "
       f"{max(short_, default=0):.1f} mm short of where a leaned door stops, the fingers bent {min(catch_fb, default=0):.2f} "
       f"to {max(catch_fb, default=0):.2f} there (no spring), the tab bumps caught under the head; leaned in too far, the "
       f"finger bumps "
       f"come up behind their pads ({n_behind} of the poses tried) and at step 4 nothing rigid stops the top, which "
       f"comes out pushing them back toward the room up to {ub_most:.2f} mm: it then sits with no push down from its "
       f"fingers and lifts with no spring. That bend is at most {eps_u:.2f} % strain and {f_u:.2f} N a finger (the "
       f"finger clamped at its root, which overstates both; under 2 %); nothing of the doorway stands behind the wall's "
       f"inside face round the opening ({behind_wall:.6f} mm3), so held there the bumps touch only the pads' backs and "
       f"it lifts out as usual. Every pose past the band either does that, or is stopped rigidly: leaned in much too "
       f"far it won't come all the way in under the head, its chamfered back edges on the jamb stops' tops "
       f"({sum(1 for v in ins.values() if v['what'] == 'blocked coming in under the head')} of the poses tried)")
for k in ("drawn", "printed"):
    rows = []
    for th in (6.0, 7.0, 8.0):
        for phi in PHIS:
            v = ins[(k, th, phi)]
            tag_ = {"works": "ok", "blocked coming in under the head": "blocked",
                    "leaned too far: its springs go in behind their pads": "behind pads",
                    "leaned too far: the top won't come out": "top held",
                    "leaned too far: a finger bump is not under its pad": "pad"}.get(v["what"], v["what"].split(":")[0])
            rows.append(f"{th:g}/{phi:.1f} {v['lean']:+.2f} {tag_}")
    report(True, f"insertion {k} (swing/lean, the tongue's back at the mouth, what happens): " + "; ".join(rows))

# ---- 6.10 roof, and the steel door and the hand that lifts it
poses_hi = []
for k in ("drawn", "printed"):
    r_, sd = rigs[k], seats[k]
    poses_hi += [(k, removal_pose(sd, stops[k]))]
    for (k_, th, phi), v in ins.items():
        if k_ == k and v["what"] == "works":
            poses_hi.append((k, insertion_pose(sd, th, phi, dz=v["top"])))
top_z = max(rigs[k].top_z(A) for k, A in poses_hi)
roof_both = s.union([roof, roof.mirror([1, 0, 0])])
roof_ov = max(overlap(cur.transform(pose_3d(A)), roof_both) for _, A in poses_hi)
roof_gap = min(cur.transform(pose_3d(A)).min_gap(roof_both, 20.0) for _, A in poses_hi[:3])
# and the poses leaned in past the band, at the top of their push: the rigid curtain's highest point, and at a 7 degree
# swing the rigid curtain (springs out) against the roof halves in 3D
past_top = {k: max([float(np.nanmax(shapely.bounds(apply(insertion_pose(seats[k], th, phi, dz=ins[(k, th, phi)]["top"]),
                                                         rigs[k].R))[:, 3])) for k_, th, phi in past_keys if k_ == k],
                   default=-99.0) for k in ("drawn", "printed")}
past_roof = max([overlap(rigid_cur.transform(pose_3d(insertion_pose(seats[k], th, phi, dz=ins[(k, th, phi)]["top"]))),
                         roof_both) for k, th, phi in past_keys if th == 7.0], default=0.0)
n_past7 = sum(1 for _, th, _ in past_keys if th == 7.0)
report(top_z <= 65.1 and roof_ov < 0.001 and all(rigs[k].band_ok for k in rigs) and max(past_top.values()) <= 65.1
       and past_roof < 0.001,
       f"nothing of the curtain rises over {top_z:.2f} (at most 65.1) in any pose of taking it out or putting it in, "
       f"and the roof halves are untouched ({roof_ov:.5f} mm3; {roof_gap:.1f} mm clear at the stop); leaned in past the "
       f"band, at the top of its push the rigid curtain rises to {past_top['drawn']:.2f} drawn and {past_top['printed']:.2f} "
       f"printed (at most 65.1), and at a 7 degree swing ({n_past7} poses) it overlaps the roof halves by {past_roof:.5f} "
       f"mm3 (under 0.001)")
# ---- 6.9 again: leaned in too far, the other half (the Lofted Barn Garage's line, without its loft). Past the band the
# finger bumps come up beside their pads, not under them, and the top still comes out: pushed home, each pad's back
# face bends its finger sideways (in u), which is no stop you feel. Seated so, the fingers hold nothing down, and what
# tells it is that, lifted a little and let go, it doesn't snap back down
Iu_ = s.FING_H * s.TONGUE_T ** 3 / 12
ku = (2500.0 * 3 * Iu_ / A_D ** 3 * 0.60, 3500.0 * 3 * Iu_ / A_D ** 3)   # sideways: the z rate's root factor (fe2d) to clamped
EPS_U = 1.5 * s.TONGUE_T / A_D ** 2 * 100                              # strain % per mm of sideways bend at the root, clamped
lt_ok, lt_rows, lt_vals = True, [], {}
for k in ("drawn", "printed"):
    r_, sd = rigs[k], seats[k]
    far_ = [(key, v) for key, v in ins.items() if key[0] == k and v["what"].startswith("leaned too far")]
    if not far_:
        lt_rows.append(f"{k}: no lean tried goes in too far without being stopped")
        continue
    us_far = [v["lean"] for _, v in far_]
    zb_max = max(v["fbend_top"] for _, v in far_)
    fin_ = FIN_D if k == "drawn" else FIN_P
    fbs_ = shapely.bounds(apply(removal_pose(sd), r_.FB[r_.ps]))           # the bumps at the seat
    D_ = float(np.max(fbs_[:, 2] - shapely.bounds(r_.P[r_.ps])[:, 0]))      # their front less the pads' back
    ub_ = max(D_, ub_k[k])
    F_ = (ku[0] * D_, ku[1] * D_)
    fpre_, tpre_ = pre[k]["fbend"], pre[k]["tb_u"].max()
    mis_net = WEIGHT - 0.2 * (2 * ku[0] * D_ + 2 * kt[0] * tpre_)          # let go, seated so: its weight against the least friction
    good_net = 2 * kf[2500.0] * (fpre_ + 1.0) + WEIGHT - 0.4 * 2 * kt[1] * tpre_   # seated right, 1 mm up: the least push down
    lt_vals[k] = (D_, mis_net, good_net)
    lt_ok = lt_ok and (EPS_U * ub_ < 2.0 and fin_[2] * zb_max < 2.0 and past_top[k] <= 65.1 and past_roof < 0.001
                       and good_net >= 5 * max(mis_net, 0.0) and good_net >= 0.3)
    a_k = A_D if k == "drawn" else A_P
    lt_rows.append(f"{k}, leaned so the tongue's back is {max(us_far):+.2f} to {min(us_far):+.2f} at the mouth: it goes up "
                   f"with nothing rigid in the way, the door itself to z {past_top[k]:.2f} and off the roof "
                   f"({past_roof:.5f} mm3 at 7 degrees), each finger bent {zb_max:.2f} at most in z at the top "
                   f"({fin_[2] * zb_max:.2f} %, the pad bearing {a_k:.2f} from the root; its tip {fin_[1] * zb_max:.2f} in "
                   f"its {tip[k][0]:.2f} slot; more and it lands on the body top, a stop); pushed home each pad's back "
                   f"face bends its finger {D_:.2f} sideways ({ub_:.2f} with the push at step 4), {F_[0]:.2f} to "
                   f"{F_[1]:.2f} N (sideways rate {ku[0]:.3f} to {ku[1]:.3f} N/mm), {EPS_U * ub_:.2f} % strain: no stop "
                   f"you feel; seated so, let go 1 mm up it is pushed down {max(mis_net, 0.0):.3f} N at most (its weight "
                   f"less friction), seated right at least {good_net:.2f} N")
report(lt_ok, "roll-up door leaned in too far, past the band (H.5): " + "; ".join(lt_rows) + "; so the read me's check "
              "after putting it in: lift it a little by the handle and let go, it must snap back down (at least 5 times "
              "the push, and 0.3 N; under 2 % strain anywhere, nothing breaks; take it out the usual way and put it back "
              "leaning less)")
# the steel door now stands on the door side 4 ft from the roll-up end: the curtain at its farthest poses
# out and in, and a hand at its handle (a box 24 wide, from the table to 25 up, from the siding out 60),
# against the door shut and swung in to 100 degrees and its casing; and the hand against the door side
hand = s.ru_box(-12, 12, s.WT, s.WT + 60, 0, 25)
far = [removal_pose(seats["drawn"], stops["drawn"], 8.0, dz=-(s.TONGUE_UP + s.BUMP_H + stops["drawn"] + 0.6), du=15),
       removal_pose(seats["drawn"], stops["drawn"]), insertion_pose(seats["drawn"], 8.0, 1.4, dz=-2.0)]
casing_d = s.union(s.trims()) ^ s.box(s.W / 2 - 1, s.W / 2 + 2, s.DOOR_Y0 - s.TRIM - 0.1, s.DOOR_Y1 + s.TRIM + 0.1, 0, s.ZWT)
door_things = s.union([casing_d, door.transform(s.door_to_shed(0)), door.transform(s.door_to_shed(100))])
d_gap = min(cur.transform(pose_3d(A)).min_gap(door_things, 80.0) for A in far)
h_gap = hand.min_gap(door_things, 80.0)
h_side = hand.min_gap(p["door side"], 80.0)
report(d_gap > 10 and h_gap > 10 and h_side > 10,
       f"the moved steel door (y {s.DOOR_Y0:.3f}..{s.DOOR_Y1:.3f}), shut or swung in to 100 degrees, and its casing are "
       f"{d_gap:.1f} mm from the curtain at its farthest poses out and in and {h_gap:.1f} mm from a hand at its handle; "
       f"the door side is {h_side:.1f} mm from that hand (at least 10)")
# the room for a fingernail behind the grip, and for a fingertip under it (the Lofted Barn Garage's line), read off the
# curtain's print layers at the handle's middle and half way up the grip
xm_, ym_ = cb[0] + pc(0.0, 0)[0], cb[1] + pc(0, s.RAIL_Z0 + s.HDL_HT / 2)[1]
col_l = [(z0_, z1_, (cpart.slice((z0_ + z1_) / 2) ^ m3.CrossSection.square([0.02, 0.02]).translate([xm_ - 0.01, ym_ - 0.01]))
          .area() > 1e-6) for z0_, z1_ in layers(cb[5])]
i0_ = next((i_ for i_, c_ in enumerate(col_l) if not c_[2]), len(col_l))          # the first empty layer over the rail
i1_ = next((i_ for i_ in range(i0_, len(col_l)) if col_l[i_][2]), None)            # the grip's first layer
emp_ = col_l[i0_:i1_] if i1_ is not None else []
nail_d = sum(z1_ - z0_ for z0_, z1_, _ in emp_)
grip0 = col_l[i1_][0] if i1_ is not None else 0.0
rail0 = col_l[i0_][0] if i0_ < len(col_l) else 0.0


def gap_x(zm):
    """The empty run along x through the handle's middle on the curtain's layer at print height zm (mm)."""
    st_ = cpart.slice(zm) ^ m3.CrossSection.square([30, 0.02]).translate([xm_ - 15, ym_ - 0.01])
    xs_ = [q.bounds() for q in st_.decompose() if q.area() > 1e-7]
    return (min([b_[0] for b_ in xs_ if b_[0] >= xm_] + [xm_ + 15]) - max([b_[2] for b_ in xs_ if b_[2] <= xm_] + [xm_ - 15]))


w_top_, w_root_ = gap_x(s.HDL_U1 - 0.1), gap_x(s.RAIL_FACE + 0.1)
h_skid = s.RAIL_Z0 + s.SKID_H - s.NOTCH
under_ = s.ru_box(-s.HDL_HALF, s.HDL_HALF, s.WT + 0.02, s.HDL_U2, -(s.SKID_H - s.NOTCH), s.RAIL_Z0 - 0.02)
rest_ = s.union([body, roof_both, door0, p["angles"]] + skids)
under_v = overlap(s.union([rest_, cur]), under_)
# the room a hand needs in front of the doorway's bottom middle (the Lofted Barn Garage's line): 40 x 40 mm out from the
# casing face, from the table up to 35 mm, holds nothing but the curtain's black handle
hand40 = s.ru_box(-20, 20, s.WT + s.PROUD + 0.05, s.WT + 40, -(s.SKID_H - s.NOTCH), 35)
door_sw = s.union([door.transform(s.door_to_shed(dg)) for dg in (0, 45, 90)])
in_hand = overlap(s.union([rest_, door_sw]), hand40)
grip_in, white_in = overlap(cur_b, hand40), overlap(cur_w, hand40)
report(in_hand < 1e-6 and grip_in > 10 and white_in < 1e-6,
       f"the room a hand needs in front of the doorway's bottom middle (40 x 40 mm out from the casing face, from the "
       f"table up to 35 mm) holds nothing but the curtain's black handle ({grip_in:.1f} mm3 of it; {in_hand:.6f} mm3 of "
       f"anything else, the steel door shut or swung in 45 or 90 degrees, its casing, the corner angles, skids and roof "
       f"included)")
report(nail_d - 0.2 >= 1.2 and abs(grip0 - s.HDL_U1) < 1e-6 and abs(rail0 - s.RAIL_FACE) < 1e-6 and w_top_ >= 4.5
       and min(h_skid, s.RAIL_Z0) >= 7.0 and under_v < 1e-6,
       f"the roll-up door's handle has room for a fingernail behind its grip: as printed, {len(emp_)} empty layers "
       f"({nail_d:.2f} mm) between the rail's top at {rail0:.2f} and the grip's first layer at {grip0:.2f}, "
       f"{nail_d - 0.2:.2f} if that bridge sags 0.2 (at least 1.2), {w_top_:.2f} wide between the legs ({w_root_:.2f} on "
       f"the 5.05 layer, between the fillets; at least 4.5); and for a fingertip under it: nothing at all under the grip "
       f"in front of the siding ({under_v:.6f} mm3), {h_skid:.2f} mm down to the table on the skids and {s.RAIL_Z0:.2f} on "
       f"the fit test's half doorway, which stands on its skirt (at least 7)")

# ---- the roll-up end round the doorway (spec E)


def section_u(u):
    """The roll-up end's section on the plane u out from its inside face, in (x, z)."""
    return ew.transform(T_BED).slice(u)


open_door = max((square(-s.STOP_X0 + 0.05, s.STOP_X0 - 0.05, s.ZF + s.LIP_H + 0.01, s.MOUTH - 0.01) ^ section_u(u)).area()
                for u in (0.125, 2.0, 4.0, 4.95))
open_jamb = max((square(*s.xspan(sg, s.STOP_X0 - 0.05, H_ - 0.01), s.STOP_TOP + 0.01, s.MOUTH - 0.01) ^ section_u(0.125)).area()
                for sg in (1, -1))
report(open_door < 1e-6 and open_jamb < 1e-6,
       f"the doorway is empty: no curtain, rail, latch or shade is left in the wall ({open_door:.6f} mm2 of wall between "
       f"the stops over the lip at u 0.125, 2.0, 4.0 and 4.95; {open_jamb:.6f} beside the curtain over the stops)")
drum_front = (square(-H_, H_, s.MOUTH, s.ZWT - s.PLATE_TOP) - section_u(2.5)).area()
reb = square(-H_, H_, s.MOUTH, s.MOUTH + s.REB_H) ^ section_u(1.0)
want_reb = len(s.RIB_XS) * s.RIB_W * s.REB_H + 2 * (s.PAD_X1 - s.PAD_X0) * (s.MOUTH + s.REB_H - s.PAD_Z)
drum_over = (square(-H_, H_, s.MOUTH + s.REB_H, s.ZWT - s.PLATE_TOP) - section_u(1.0)).area()
report(drum_front < 0.01 and abs(reb.area() - want_reb) < 0.01 and len(reb.decompose()) == len(s.RIB_XS) + 2
       and drum_over < 0.01,
       f"the drum box fills from the opening's top ({s.MOUTH:.3f}) to the top plates' underside "
       f"({s.ZWT - s.PLATE_TOP:.3f}) between the king studs in front of the rebate ({drum_front:.5f} mm2 missing at u "
       f"2.5); the rebate, u 0..{s.REB_U} up to {s.MOUTH + s.REB_H:.3f}, holds only its {len(s.RIB_XS)} ribs and 2 pads "
       f"({reb.area():.3f} mm2 of them at u 1.0, against {want_reb:.3f}), and the box is whole over it "
       f"({drum_over:.5f} mm2 missing)")
part = print_part(ew, s.WALL_TO_PRINT[n],                      # out into the end studs, which hold the skirt
                  s.wall_box(n, -42.0, 42.0, -1, 10, -1, s.ZWT + 1))
worst, longest = worst_overhang(part)
report(worst < 5 and longest <= 20, f"round the doorway nothing is left hanging in the end wall's print ({worst:.2f} "
                                    f"mm2 worst layer), no bridge longer than {longest:.1f} mm")
kings_top = [(ew ^ s.wall_box(n, a0 + 0.05, a1 - 0.05, 0.5, 1.5, s.ZF + 10, s.ZWT)).bounding_box()[5]
             for a0, a1 in ((H_, H_ + s.SW), (-H_ - s.SW, -H_))]
report(all(abs(k - s.ZWT) < 1e-6 for k in kings_top),
       f"Alan's king studs beside the roll-up run up to the top plates (solid to {min(kings_top):.3f}), no header")


# ======================================================================== 7
group("7. Steel door")
ds = p["door side"]
closed = overlap(body, door0)
report(closed < 0.01, f"the steel door shut fits its opening ({closed:.5f} mm3)")
last_free, hit_at = 0, None
for deg in range(0, 121, 2):
    d = door.transform(s.door_to_shed(deg))
    v = overlap(body, d) + overlap(p["angles"], d)
    if v < 0.01 and hit_at is None:
        last_free = deg
    elif hit_at is None:
        hit_at = deg
lo, hi = float(last_free), float(hit_at if hit_at else 120)
for _ in range(12):
    mid = (lo + hi) / 2
    lo, hi = (mid, hi) if overlap(body, door.transform(s.door_to_shed(mid))) < 0.01 else (lo, mid)
report(last_free >= 90, f"it swings in from shut to {last_free} degrees in 2 degree steps clear of the body and the "
                        f"corner angles; it stops at about {lo:.1f} degrees, its face against "
                        f"the hinge-side king stud's corner")
v = overlap(body, door.transform(s.door_to_shed(-2)))
report(v > 0.05, f"at -2 degrees it meets the stop on the latch jamb, so it can't swing out ({v:.2f} mm3)")
hole_lo = s.DOOR_AXIS_U - s.PIN_HOLE_D / 2
# under the bottom hole the trench is open at the inside face by design (from the trench floor up),
# so its part below the trench floor is what must stay whole; the top hole all of it
low = (s.ZF - s.HOLE_BOTTOM_DEPTH + 0.02, s.ZF - s.TRENCH_DEPTH - 0.02)
foot_box = s.wall_box("door side", s.AXIS_Y - 1.35, s.AXIS_Y + 1.35, 0, hole_lo - 0.005, *low)
whole_low = abs(overlap(ds, foot_box) - foot_box.volume()) < 1e-4
top_box = s.wall_box("door side", s.AXIS_Y - 1.35, s.AXIS_Y + 1.35, 0, hole_lo - 0.005,
                     s.ZF + s.DOOR_OPEN_H + 0.1, s.ZF + s.DOOR_OPEN_H + 2.0)
whole_top = abs(overlap(ds, top_box) - top_box.volume()) < 1e-4
first = []
for zc, hz_ in (((low[0] + low[1]) / 2, (low[1] - low[0]) / 2), (s.ZF + s.DOOR_OPEN_H + 1.0, 0.9)):
    reg = s.wall_box("door side", s.AXIS_Y - 4, s.AXIS_Y + 4, -1, s.WT + 1, zc - 2, zc + 2)
    pp = print_part(ds, s.WALL_TO_PRINT["door side"], reg)
    bbp = pp.bounding_box()
    cs = pp.slice(0.125).offset(-0.21, RND).offset(0.21, RND)
    hole_c = square(bbp[0] + 4 - 1.35, bbp[0] + 4 + 1.35, bbp[1] + 2 - hz_, bbp[1] + 2 + hz_)
    first.append((hole_c - cs).area())
report(abs(hole_lo - 0.25) < 1e-9 and whole_low and whole_top and max(first) < 1e-4,
       f"its pin holes reach down only to u {hole_lo:.2f}, the top of the first layer: the wall is whole under both "
       f"(as printed the first layer covers them: {max(first):.6f} mm2 open)")


def hang(dm, base, top_z, H, inside, lift):
    """The door moved from base (its shut matrix) up by lift and tilted about the line along y
    through its top at the pin line, so the bottom pin's tip is inside mm in from the pin line."""
    m = base.copy()
    m[2, 3] += lift
    th = math.asin(max(-1.0, min(1.0, inside / H)))
    c, sn = math.cos(th), math.sin(th)
    R = np.array([[c, 0, sn], [0, 1, 0], [-sn, 0, c]])
    piv = np.array([base[0, 3] + s.DOOR_R, 0, top_z + lift])
    return dm.transform(np.column_stack([R @ m[:, :3], R @ (m[:, 3] - piv) + piv]))


SWING_OUT = [float(i) for i in np.arange(2.8, 0, -0.25)] + [0.0]


def hang_path(dm, base, top_z, H, wall, zf, head):
    """F7's way in: lifted 0.5, the bottom pin's centre 2.8 in from the pin line, swung out along the
    trench in 0.25 steps to the pin line, dropped 0.5. Returns (worst overlap with the wall, least
    margin of the pin over the trench floor, least margin of the door's top under the head), and
    the worst overlap of the same swing with no lift."""
    slab = dm ^ s.box(-s.BIG, s.BIG, -0.01, base_h(dm), -s.BIG, s.BIG)

    def lift_at(inside, want):
        """The lift pushed up to want, or as far as the head lets the tilted door go (0.01 short)."""
        return min(want, head - hang(slab, base, top_z, H, inside, 0.0).bounding_box()[5] - 0.01)
    path = [(i, lift_at(i, 0.5)) for i in SWING_OUT] + [(0.0, l) for l in (0.4, 0.3, 0.2, 0.1, 0.0)]
    worst, m_floor, m_head, lifts = 0.0, 9.0, 9.0, []
    for k, (inside, lift) in enumerate(path):
        d = hang(dm, base, top_z, H, inside, lift)
        worst = max(worst, overlap(d, wall))
        if k < len(SWING_OUT):
            lifts.append(lift)
            m_floor = min(m_floor, mesh_pts(d)[:, 2].min() - (zf - s.TRENCH_DEPTH))
            m_head = min(m_head, head - hang(slab, base, top_z, H, inside, lift).bounding_box()[5])
    nolift = max(overlap(hang(dm, base, top_z, H, i, 0.0), wall) for i in SWING_OUT)
    return worst, m_floor, m_head, nolift, min(lifts)


def base_h(dm):
    """A door's height, from its print coords (the top pin stands above it by PIN_TOP_LEN)."""
    return dm.bounding_box()[4] - s.PIN_TOP_LEN


door_slab_only = door ^ s.box(-s.BIG, s.BIG, -0.01, s.DOOR_H, -s.BIG, s.BIG)
base0 = s.door_to_shed(0)
top_z = s.ZF + s.DOOR_BOTTOM_GAP + s.DOOR_H
H = s.DOOR_H + s.PIN_BOTTOM_LEN
worst, m_floor, m_head, nolift, min_lift = hang_path(door, base0, top_z, H, ds, s.ZF, s.ZF + s.DOOR_OPEN_H)
lifted = overlap(ds, door.transform(np.column_stack([base0[:, :3], base0[:, 3] + [0, 0, 0.65]])))
report(worst < 0.01 and m_floor > 0.1 and m_head > 0.02 and abs(min_lift - 0.5) < 1e-9 and lifted > 0.01
       and nolift > 0.01,
       f"it hangs on the loose door side (no floor) by F7's way: top pin up into the head, lifted {min_lift:.2f}, the "
       f"bottom pin's centre 2.8 in from the pin line (tilt {math.degrees(math.asin(2.8 / H)):.2f} degrees), swung out "
       f"along the trench in 0.25 steps and dropped, every step clear ({worst:.5f} mm3), {m_floor:.3f} mm over the "
       f"trench floor and {m_head:.3f} under the header at the closest; not empty: lifted 0.65 it meets the head "
       f"({lifted:.3f} mm3), and swung with no lift its pin runs into the sill post ({nolift:.3f} mm3)")
# captive once the door side is on the floor: the floor is solid at the trench's mouth, and the pin
# only gets up over the floor top with the door tilted far into the room, its pin then deep over floor
notch = s.W / 2 - s.WT - s.FIT
mouth = s.box(notch - 3, notch - 0.01, s.AXIS_Y - s.PIN_HOLE_D / 2, s.AXIS_Y + s.PIN_HOLE_D / 2,
              s.ZF - 0.5, s.ZF - 0.01)
solid = abs(overlap(fl, mouth) - mouth.volume()) < 1e-4
pin_bot = door ^ s.box(-s.BIG, s.BIG, -s.BIG, 0.0, -s.BIG, s.BIG)
first_up = None
for k in range(0, 201):
    th = k * 0.1
    inside = H * math.sin(math.radians(th))
    slab0 = hang(door_slab_only, base0, top_z, H, inside, 0.0).bounding_box()[5]
    lift = min(0.8, (s.ZF + s.DOOR_OPEN_H) - slab0)
    pb = hang(pin_bot, base0, top_z, H, inside, lift).bounding_box()
    if pb[2] >= s.ZF and first_up is None:
        first_up = (th, notch - pb[0], lift)
report(solid and first_up is not None and first_up[1] >= 3.0,
       f"with the door side on the floor the door is captive: the floor is solid over the trench's mouth, and tilted "
       f"into the room as far as the head lets it rise, the bottom pin first clears the floor top at "
       f"{first_up[0]:.1f} degrees, with its far edge {first_up[1]:.2f} mm in over solid floor")
lat = s.DOOR_Y1 - s.DOOR_GAP
stop_u = ((ds ^ s.box(s.W / 2 - s.WT, s.W / 2, lat - 0.001, lat + 0.001, s.ZF + 20, s.ZF + 21)).bounding_box()[0]
          - (s.W / 2 - s.WT))
door_out = (s.AXIS_X - s.DOOR_R - (s.W / 2 - s.WT)) + printed_top(s.DOOR_T)
report(stop_u - door_out >= 0.15 - 2e-3,
       f"at its latch edge the door's outside face, at its printed thickness {printed_top(s.DOOR_T):.2f} (u "
       f"{door_out:.2f}), is {stop_u - door_out:.3f} mm under the stop's chamfer (u {stop_u:.3f})")
# its six panels where the designer's door-steel.js draws them (xs = dL + w * 0.170 ..., p = yb + h * fraction): fractions
# of the OPENING, across from its hinge-side jamb (-y) and up from the floor, typed in here, as the Lofted Barn Garage's
# checker has them (final audit, Nov 4 2026: its door had them as fractions of the slab, up to 0.55 mm off; the two doors
# are now the same solid). Read off the shut door 0.2 mm under its outside face, where each panel's groove shows as a ring
DS_COLS = (0.170, 0.435, 0.565, 0.830)
DS_ROWS = (0.064, 0.300, 0.369, 0.758, 0.822, 0.945)
DS_OPEN = (-67.733, -42.333)                # Alan's standard place for the 36 in opening (group 12)
DS_OPEN_H = 75.6 * 25.4 / 36                # the builder's 36 x 75.6 in door (Alan: "Keep builder sizes"), at 1:36
x_out = s.AXIS_X + s.DOOR_R                 # the shut door's outside face
cs_door = door0.transform(np.array([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0]], dtype=float)).slice(x_out - 0.2)
rings = []
for loop in cs_door.to_polygons():
    q_ = np.asarray(loop)
    if 0.5 * np.sum(q_[:, 0] * np.roll(q_[:, 1], -1) - np.roll(q_[:, 0], -1) * q_[:, 1]) < 0:   # a hole: a groove's outside
        rings.append((q_[:, 0].min(), q_[:, 0].max(), q_[:, 1].min(), q_[:, 1].max()))
ys_ = sorted({round(v_, 4) for r_ in rings for v_ in r_[:2]})
zs_ = sorted({round(v_, 4) for r_ in rings for v_ in r_[2:]})
want_y = [DS_OPEN[0] + c_ * (DS_OPEN[1] - DS_OPEN[0]) for c_ in DS_COLS]
want_z = [s.ZF + r_ * DS_OPEN_H for r_ in DS_ROWS]
p_err = (max([abs(a_ - b_) for a_, b_ in zip(ys_, want_y)] + [abs(a_ - b_) for a_, b_ in zip(zs_, want_z)])
         if len(ys_) == 4 and len(zs_) == 6 else math.inf)
report(len(rings) == 6 and p_err <= 0.01,
       f"steel door: its {len(rings)} panels are where the designer draws them, the grooves' outer edges at "
       f"{', '.join(f'{c_:.3f}' for c_ in DS_COLS)} of the 36 in opening from its hinge-side jamb and "
       f"{', '.join(f'{r_:.3f}' for r_ in DS_ROWS)} of its 75.6 in from the floor, within {p_err:.4f} mm (at most 0.01): "
       f"the Lofted Barn Garage's door")


# ======================================================================== 8
group("8. Roof")
right, left = roof, roof.mirror([1, 0, 0])
for name, half in (("door-side roof half", right), ("plain-side roof half", left)):
    v = overlap(body, half)
    report(v < 0.01, f"the {name} sits on the gable ends without cutting into the body ({v:.5f} mm3)")
report(overlap(right, left) < 0.001, "the two roof halves do not overlap at the ridge")
v = overlap(body, right.translate([0, 0, -0.3]))
report(v > 0.5, f"lowered 0.3 mm a roof half runs into the gable tops, so it is resting on them ({v:.1f} mm3)")
for dx, dy, words in ((0, 1.0, "along the garage"), (1.0, 0, "down the slope")):
    v = overlap(body, right.translate([dx, dy, 0.05]))
    report(v > 0.05, f"slid 1 mm {words}, a roof half is held by its pegs ({v:.2f} mm3)")
v = overlap(body, right.translate([0, 0, 2.0]))
report(v == 0, "lifted 2 mm straight up, a roof half is clear of the pegs")


def tilt(piece, name, d_top):
    """A long wall tipped about the outside top edge of the floor under it, its top d_top mm out."""
    sx = s.WALL_SIDE[name][1]
    xp, zp = sx * (s.W / 2 - s.TS - s.FLOOR_CLR), s.ZF
    a = math.atan(d_top / (s.ZWT - s.ZF)) * sx
    c, sn = math.cos(a), math.sin(a)
    R = np.array([[c, 0, sn], [0, 1, 0], [-sn, 0, c]])
    t = np.array([xp, 0, zp]) - R @ np.array([xp, 0, zp])
    return piece.transform(np.column_stack([R, t]))


for n in LONGS:
    sx = s.WALL_SIDE[n][1]
    half = right if sx > 0 else left
    peg = p[n] ^ s.box(-s.BIG, s.BIG, -2, 2, s.ZWT, s.BIG)
    gap = peg.min_gap(half, 2.0)
    pb = peg.bounding_box()
    hole_top = s.zline(s.MID_PEG_X) + s.PEG_HOLE_UP / math.cos(s.ALPHA)
    peg_top = s.zline(s.MID_PEG_X) + s.PEG_UP / math.cos(s.ALPHA)
    radial = (s.PEG_HOLE_D - s.PEG_D) / 2
    vo, vi = overlap(tilt(p[n], n, 0.5), half), overlap(tilt(p[n], n, -0.5), half)
    report(gap >= 0.3 - 1e-6 and radial >= 0.3 and hole_top - peg_top >= 0.3 and overlap(p[n], half) == 0
           and min(vo, vi) > 0.05,
           f"{n}: its mid peg is in the roof half's third hole, {gap:.3f} mm clear at the closest ({radial:.2f} round "
           f"it, {(hole_top - peg_top) * math.cos(s.ALPHA):.2f} over it square to the roof); with the wall's top 0.5 "
           f"mm out or in it meets the roof half ({vo:.2f} and {vi:.2f} mm3), so the roof holds its middle")


# ======================================================================== 9
group("9. Skids")
for i, (k, sk) in enumerate(zip(s.SKID_KINDS, skids)):
    v = overlap(body, sk)
    up = overlap(fl, sk.translate([0, 0, 0.3]))
    held = min(overlap(fl, sk.translate(t)) for t in ([0.3, 0, 0], [-0.3, 0, 0], [0, 0.3, 0], [0, -0.3, 0]))
    bb = sk.bounding_box()
    report(v < 0.01 and up > 1 and held > 0.05 and abs(bb[2] + s.OUTER_SKID_H) < 0.01,
           f"skid {i + 1} ({k}, x {bb[0]:.3f} to {bb[3]:.3f}): fits under the floor ({v:.5f} mm3), touches it (raised "
           f"0.3: {up:.1f} mm3), held by its pegs (moved 0.3 mm: {held:.2f} mm3), bottom at z {bb[2]:.3f}")
feet = [min(overlap(sk.translate([0, 0, 0.3]), fl ^ s.box(-s.BIG, s.BIG, j - s.SW / 2, j + s.SW / 2, 0, 1))
             for j in s.joist_ys()) for sk in skids[:2]]
seat = max(overlap(sk, fl ^ s.box(-s.BIG, s.BIG, -s.BIG, s.BIG, -1, 1)) for sk in skids[:2])
report(min(feet) > 0.01 and seat < 1e-4,
       f"the inner skids' notches sit on all {len(s.joist_ys())} joists: raised 0.3 each meets every joist's foot "
       f"({min(feet):.3f} mm3 at the least), and seated nothing is in the way ({seat:.5f} mm3)")
bots = [sk.bounding_box()[2] for sk in skids]
report(max(bots) - min(bots) < 0.01 and abs(bots[0] + 3.281) < 0.01,
       f"all four bottoms level at z {', '.join(f'{b:.3f}' for b in bots)} (spec -3.281)")
rim0, rim1 = s.W / 2 - s.TS - s.FLOOR_CLR - s.RIM, s.W / 2 - s.TS - s.FLOOR_CLR
for sk, sx in zip(skids[2:], (-1, 1)):
    bb = sk.bounding_box()
    xa, xb = abs(bb[0]) if sx < 0 else bb[0], abs(bb[3]) if sx < 0 else bb[3]
    lo_x, hi_x = min(xa, xb), max(xa, xb)
    body_top = (sk ^ s.box(-s.BIG, s.BIG, -80, 80, -5, 0.5)).bounding_box()[5]      # between its pegs
    flat_top = (sk ^ s.box(-s.BIG, s.BIG, -30, -12, -5, 0.5)).slice(-0.001).area()
    prong_bits = s.union([p[n] ^ s.wall_box(n, s.prong_slot(ac)[0], s.prong_slot(ac)[1], -0.5, s.SLOT_U, -1, s.ZF - 2)
                          for n in LONGS for ac in s.prong_spots(n)])
    clear = sk.min_gap(prong_bits, 1.0)
    report(rim0 - lo_x <= 0.08 and hi_x <= rim1 and abs(body_top) < 1e-6 and flat_top > 0.9 * 18 * s.SKID_W
           and clear >= 0.3 - 1e-6,
           f"the {'+' if sx > 0 else '-'}x outer skid, x {lo_x:.3f} to {hi_x:.3f}, lies under the rim band ({rim0:.3f} "
           f"to {rim1:.3f}) but for a {max(0, rim0 - lo_x):.3f} strip; its top flat at z {body_top:.3f}; it clears "
           f"every long-wall barb and leg by {clear:.3f} mm at its reliefs")
# each skid peg in its floor hole: the bases' snug push fit, 0.2 round it and 0.3 over its top (F9).
# The pegs are what of each skid stands over z 0.7 (an inner skid's body tops out at NOTCH, 0.6)
rad, over, kinds = [], [], set()
for k, sk in zip(s.SKID_KINDS, skids):
    for q in (sk ^ s.box(-s.BIG, s.BIG, -s.BIG, s.BIG, 0.7, 10)).decompose():
        qb = q.bounding_box()
        cx, cy = (qb[0] + qb[3]) / 2, (qb[1] + qb[4]) / 2
        wall_of_hole = fl ^ s.box(cx - 3, cx + 3, cy - 3, cy + 3, 0.7, qb[5] - 0.05)   # its side, not its roof
        rad.append(q.min_gap(wall_of_hole, 1.0))
        over.append((fl ^ s.box(cx - 0.3, cx + 0.3, cy - 0.3, cy + 0.3, 0, 20)).bounding_box()[2] - qb[5])
        kinds.add((k, round(qb[3] - qb[0], 2)))
report(len(rad) == 8 and 0.19 <= min(rad) and max(rad) <= 0.25 and min(over) >= 0.25,
       f"the skids' {len(rad)} pegs ({', '.join(f'{d:.1f} mm on the {k}' for k, d in sorted(kinds))}) sit in their "
       f"floor holes with {min(rad):.3f} to {max(rad):.3f} mm round each and {min(over):.2f} to {max(over):.2f} over "
       f"its top (F9: the bases' snug 0.2 push fit, 2.0 pegs in 2.4 holes and 1.6 in 2.0, 0.3 over the top)")


# ======================================================================== 10
group("10. Plates")
for fname, pls in PL.items():
    for i, (pname, items) in enumerate(pls):
        placed, fils, kinds, n_skid = [], set(), [], 0
        for obj, parts, (x, y), *own in items:
            n_skid += "skid" in obj
            whole = s.union([m for _, m, _ in parts])
            bb = whole.bounding_box()
            fils |= {f for _, _, f in parts}
            brim = float(own[0].get("brim_width", 0)) if own and own[0].get("brim_type") == "outer_only" else 0.0
            for q in whole.translate([x - bb[0], y - bb[1], -bb[2]]).decompose():
                placed.append(q)
                kinds.append((obj, brim))
        boxes = [q.bounding_box() for q in placed]
        inside = all(b[0] - k[1] >= -1e-6 and b[1] - k[1] >= -1e-6 and b[3] + k[1] <= BED + 1e-6
                     and b[4] + k[1] <= BED + 1e-6 for b, k in zip(boxes, kinds))
        gap, skid_gap, skid_other = BED, BED, BED
        for a_, b_ in itertools.combinations(range(len(placed)), 2):
            A_, B_ = boxes[a_], boxes[b_]
            d = math.hypot(max(B_[0] - A_[3], A_[0] - B_[3], 0), max(B_[1] - A_[4], A_[1] - B_[4], 0))
            if kinds[a_][0] != kinds[b_][0]:
                gap = min(gap, d if d >= 3 else placed[a_].min_gap(placed[b_], 3.5))
            sa, sb = "skid" in kinds[a_][0], "skid" in kinds[b_][0]
            if sa and sb:
                skid_gap = min(skid_gap, d)
            elif sa or sb:
                skid_other = min(skid_other, d)
        tower = all(b[3] <= 162 + 1e-6 or b[4] <= 192 + 1e-6 for b in boxes)
        ok = inside and gap >= 3 - 1e-6 and (len(fils) > 1 and tower or len(fils) == 1)
        words = f"{fname}, plate {i + 1} ({pname}): {len(items)} parts inside the bed"
        words += f" (brims too)" if any(k[1] for k in kinds) else ""
        words += f", at least {gap:.1f} mm apart" if len(items) > 1 else ""
        words += (f", filaments {sorted(fils)}, every part at x <= 162 or y <= 192, clear of the prime tower"
                  if len(fils) > 1 else f", filament {min(fils)} only, no prime tower")
        if n_skid > 1:
            ok = ok and skid_gap >= 10.5 and skid_other >= 6.0
            words += f"; skids {skid_gap:.1f} mm apart and {skid_other:.1f} from anything else"
        elif n_skid == 1:
            ok = ok and skid_other >= 6.0
            words += f"; the skid stub {skid_other:.1f} mm from anything else (at least 6.0, for its brim)"
        report(ok, words)
# each two-colour plate changes colour once: on every part nothing white over the 5.05 layer and nothing black
# under it; above 5.65 only the roll-up curtain's black handle prints, on its own, which costs nothing (spec I.3)
ch_rows, ch_ok = [], True
for fname, pls in PL.items():
    for i, (pname, items) in enumerate(pls):
        whites, blacks, tall = [], [], []
        for obj, parts, xy, *own in items:
            z_min = s.union([m for _, m, _ in parts]).bounding_box()[2]
            for part_name, m, f in parts:
                bb = m.bounding_box()
                (whites if f == 1 else blacks).append((bb[2] - z_min, bb[5] - z_min))
                if printed_top(bb[5] - z_min) > 5.65 + 1e-6:
                    tall.append(f"{obj} ({part_name}, filament {f}, to {printed_top(bb[5] - z_min):.2f})")
        if whites and blacks:
            w_top = printed_top(max(t for _, t in whites))
            b_low = min(printed_top(lo_ + 1e-6) for lo_, _ in blacks)
            ch_ok = ch_ok and w_top <= b_low + 1e-9 and abs(w_top - 5.05) < 1e-9
            ch_rows.append(f"plate {i + 1} ({pname}): white to the {w_top:.2f} layer, black from it; over 5.65 "
                           + (", ".join(tall) if tall else "nothing"))
            if pname.startswith("end walls"):
                ch_ok = ch_ok and len(tall) == 1 and "curtain" in tall[0] and "filament 2" in tall[0]
names3 = [pn for pn, _ in PL["2 all plates.3mf"]]
report(ch_ok and names3[2] == "end walls and roll-up curtain",
       f"plate 3 is named \"{names3[2]}\"; the two-colour plates change colour once: " + "; ".join(ch_rows))
# fit plate 1 shows how the real handle prints: it holds only the half doorway and the half door, and above the walls'
# top layer (5.65) only the half door's handle prints there, as only the curtain's does on plate 3, its layers there the
# real curtain's handle, layer for layer (so they are as short and as quick)
fp1_name, fp1 = PL["1 fit test.3mf"][0]
names1, above1, half_p = [], [], None
for obj, parts, xy, *own in fp1:
    names1.append(obj)
    whole = s.union([m for _, m, _ in parts])
    z0_ = whole.bounding_box()[2]
    hi_ = whole ^ s.box(-BED, 2 * BED, -BED, 2 * BED, z0_ + s.WT + s.PROUD + 1e-4, BED)
    if hi_.volume() > 1e-6:
        hb1 = hi_.bounding_box()
        above1.append((obj, hb1[3] - hb1[0], hb1[5] - z0_))
    if obj == "half roll-up door":
        half_p = whole.translate([0, 0, -z0_])
real_p = s.to_print(s.CURTAIN_TO_PRINT, [cur])[0]
hl_diff = (max(abs(half_p.slice(zm).area() - real_p.slice(zm).area()) for zm in (5.75, 6.15, 6.55, 6.75, 7.15, 7.95, 8.15))
           if half_p is not None else 99.0)
report(fp1_name == "roll-up door" and sorted(names1) == sorted(s.FIT_DOOR_PAIR) and len(above1) == 1
       and above1[0][0] == "half roll-up door" and abs(above1[0][1] - 2 * s.HDL_HALF) < 0.01
       and abs(above1[0][2] - real_p.bounding_box()[5]) < 1e-6 and hl_diff < 1e-3,
       f"1 fit test.3mf, plate 1 is \"{fp1_name}\": only the {' and the '.join(names1)}, and above the walls' top layer "
       f"only the half door's handle ({above1[0][1] if above1 else 0:.2f} wide, up to {above1[0][2] if above1 else 0:.2f}), "
       f"its layers there the real curtain's ({hl_diff:.5f} mm2 apart at most on the 5.75 to 8.15 layers): so its legs and "
       f"grip print alone, as the real door's do on plate 3, and the fit test shows how the real handle comes out")
# the per-object settings, as written in the files
want_cfg = {}
for fname, pls in PL.items():
    for pname, items in pls:
        for obj, parts, xy, *own in items:
            want_cfg[(fname, obj)] = {k: v for k, v in (own[0] if own else {}).items() if k != "modifier"}
cfgs, models = {}, {}
for fname in PL:
    path = os.path.join(s.HERE, fname)
    if not os.path.exists(path):
        report(False, f"{fname} is not written yet: run make_garage.py")
        continue
    with zipfile.ZipFile(path) as z:
        cfg = z.read("Metadata/model_settings.config").decode("utf-8")
        has = "Metadata/project_settings.config" in z.namelist()
        settings = open(os.path.join(s.HERE, "flash studio settings.json"), "rb").read()
        same_settings = z.read("Metadata/project_settings.config") == settings
        cfgs[fname], models[fname] = cfg, z.read("3D/3dmodel.model").decode("utf-8")
    got_cfg = {}
    obj_re = (r'<object id="\d+"><metadata key="name" value="([^"]*)"/><metadata key="extruder" value="\d"/>'
              r'((?:<metadata key="[^"]*" value="[^"]*"/>)*)')
    for m in re.finditer(obj_re, cfg):
        got_cfg[(fname, m.group(1))] = dict(re.findall(r'<metadata key="([^"]*)" value="([^"]*)"/>', m.group(2)))
    file_want = {k: v for k, v in want_cfg.items() if k[0] == fname}
    all_p = fname.startswith("2")
    skids_ok = all(v == {"brim_type": "outer_only", "brim_width": "5"} for k, v in got_cfg.items()
                   if "skid" in k[1] and all_p)
    nob_ok = all(v == {"brim_type": "no_brim"} for k, v in got_cfg.items()
                 if ("roof" in k[1] or "angle" in k[1]) and all_p)
    others = all(v == {} for k, v in got_cfg.items()
                 if not any(w in k[1] for w in ("skid", "roof", "angle")) and all_p)
    n_sk = sum(1 for k in got_cfg if "skid" in k[1]) if fname.startswith("2") else 0
    fit_want = {"outer skid stub": {"brim_type": "outer_only", "brim_width": "5"}, "corner angle stub": {"brim_type": "no_brim"}}
    fit_ok = all_p or (all(v == fit_want.get(k[1], {}) for k, v in got_cfg.items())
                       and sorted(k[1] for k, v in got_cfg.items() if v) == sorted(fit_want))
    report(has and same_settings and got_cfg == file_want and skids_ok and nob_ok and others and fit_ok
           and (n_sk == 4 or not fname.startswith("2")),
           f"{fname}: carries the Flash Studio settings byte for byte; per-object settings as planned: "
           + (f"the {n_sk} skids outer_only / 5 mm brim, the roof halves and corner angles no_brim, nothing else"
              if fname.startswith("2") else "the outer skid stub outer_only / 5 mm brim and the corner angle stub no_brim, "
              "as the real skids and angles, nothing else"))
# the files in the folder, the ones Alan opens, are what the generator makes now (as on both cabins; floor review, Nov 4
# 2026): it is run as it is in a scratch folder, then every .stl it makes is compared byte for byte, everything inside
# both .3mf files (the zip's own dates aside), and no other .stl or .3mf may be in the folder. The proofs here take each
# piece's shape from the generator and its modifiers, settings and placement from the files: this shows the two are the
# same. A file left from an older run, or from a run that stopped partway, fails here
gen_name = os.path.basename(s.__file__)
gen_dir = tempfile.mkdtemp(prefix="garage_gen_")
gen_stale, gen_made = [], []
try:
    for f_ in (gen_name, "flash studio settings.json"):
        shutil.copy(os.path.join(s.HERE, f_), gen_dir)
    gen_run = subprocess.run([sys.executable, os.path.join(gen_dir, gen_name)], cwd=gen_dir, capture_output=True,
                             text=True)
    gen_made = sorted(f_ for f_ in os.listdir(gen_dir) if f_.lower().endswith((".stl", ".3mf")))
    for f_ in gen_made:
        real_, new_ = os.path.join(s.HERE, f_), os.path.join(gen_dir, f_)
        if not os.path.exists(real_):
            gen_stale.append(f_)
        elif f_.lower().endswith(".stl"):
            if open(real_, "rb").read() != open(new_, "rb").read():
                gen_stale.append(f_)
        else:
            with zipfile.ZipFile(real_) as zr_, zipfile.ZipFile(new_) as zn_:
                if zr_.namelist() != zn_.namelist() or any(zr_.read(n_) != zn_.read(n_) for n_ in zn_.namelist()):
                    gen_stale.append(f_)
    gen_stale += [f_ for f_ in sorted(os.listdir(s.HERE)) if f_.lower().endswith((".stl", ".3mf")) and f_ not in gen_made]
finally:
    shutil.rmtree(gen_dir, ignore_errors=True)
gen_n_stl = sum(1 for f_ in gen_made if f_.lower().endswith(".stl"))
report(gen_run.returncode == 0 and gen_n_stl > 0 and not gen_stale
       and [f_ for f_ in gen_made if f_.lower().endswith(".3mf")] == ["1 fit test.3mf", "2 all plates.3mf"],
       f"the files in the folder are what {gen_name} makes now: its {gen_n_stl} .stl files byte for byte, everything "
       f"inside both .3mf files, and no other .stl or .3mf; so the shapes the proofs here take from {gen_name} are the "
       f"shapes in the files"
       + (f" (run {gen_name}: {', '.join(gen_stale)} out of date or not made by it)" if gen_stale else "")
       + ("" if gen_run.returncode == 0 else f" ({gen_name} stopped: {gen_run.stderr.strip()[-300:]})"))
# the bridge direction (final audit, bridge audit and bridge review, Nov 4 2026): left to itself Flash Studio picks each
# wall's siding bridge direction afresh, and the same file has come out both ways: the fit test's half doorway's two end
# bays lengthwise, 62 mm strands, every time, and in one slice the door side's bays along the whole wall. Every wall's
# bays are as long the other way, so every wall, and every fit-test piece cut from one, carries modifiers over its
# siding that set bridge_angle (External bridge infill direction): 180, which Flash Studio reads as 0 degrees, along the
# bed's X, across the studs, or, over a barn end's collar tie, 90, along Y, up the gable. Read from the files as
# written: the modifiers, each as the solid it is (Flash Studio applies its shape, not the box round its corners: it
# must be a closed solid filling that box), what they set (exactly the plan, and a number other than 0: Flash Studio
# takes any 0, "0.0" and "-0" too, as no direction and picks its own), where they reach; together they cover the whole
# piece, one over another nowhere; every piece lies on its plate unturned (the directions are the bed's, so a turned
# piece would bridge another way: floor review, Nov 4 2026); then each one's part of the piece, its bridges laid that
# way, and the layers under them left to the slicer (the prong legs' first layer, the rebate's ceiling, the door side's
# headers: bridged as on the walls that print as proven). The floor's sheet seams are its first layer, slots 0.4 mm
# wide. A 45 degree overhang reaches across one from both sides, so those proofs don't see them, but Flash Studio
# bridges the layer over them, and laid it along the long seams, strands 195 mm long, each over a slot for up to 69 mm
# (bridge review, floor review). So the floor carries modifiers over that layer alone, the only one of the floor over
# anything not printed under it: across the long seams on a strip over each, across the short ones elsewhere; laid that
# way, counting everything not printed on the layer under it, each line crosses its seam. Nothing else carries one,
# nothing else hangs out over SIDING_BRIDGE_Z more than 20 mm across in any direction, and nothing else has a slot like
# a seam longer than 20 mm on any layer, so no way the slicer lays it makes a longer strand. The Lofted Barn Garage's
# checker proves the same
WANT_MODS = {"2 all plates.3mf": ["door side", "plain side", "roll-up end", "back end", "floor"],
             "1 fit test.3mf": ["half roll-up doorway", "short plain side", "short roll-up end"]}
# what each modifier sets, by its name: exactly the generator's plan
MOD_PLAN = {"bridges across the studs": s.ACROSS_STUDS, "bridges up the gable": s.UP_THE_GABLE,
            "bridges across the long seams": s.ACROSS_LONG_SEAMS, "bridges across the short seams": s.ACROSS_SHORT_SEAMS}
WALL_MODS = ("bridges across the studs", "bridges up the gable")
FLOOR_MODS = ("bridges across the long seams", "bridges across the short seams")


def sets_direction(setting):
    """Does a modifier's setting give Flash Studio a bridge direction: bridge_angle a number other than 0 ("0.0", "-0"
    and the like are 0 too, no direction: Flash Studio picks its own)."""
    try:
        return float(setting.get("bridge_angle", "")) != 0
    except ValueError:
        return False


mod_bad, mod_rows, free_rows, slot_max = [], [], [], 0.0
floor_bad, floor_rows, floor_z, floor_over = [], [], set(), []
for fname, pls in PL.items():
    if fname not in cfgs:
        mod_bad.append((fname, "not written"))
        continue
    cfg, model = cfgs[fname], models[fname]
    meshes = {oid_: (np.array(re.findall(r'<vertex x="([-\d.]+)" y="([-\d.]+)" z="([-\d.]+)"/>', vs_), dtype=float),
                     np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"/>', ts_), dtype=np.int64))
              for oid_, vs_, ts_ in re.findall(r'<object id="(\d+)" name="[^"]*" type="model"><mesh><vertices>(.*?)'
                                               r'</vertices><triangles>(.*?)</triangles>', model)}
    # every object lies on its plate unturned: its build item only moves it, and its parts carry no transform of their own
    items_ = re.findall(r'<item [^>]*>', model)
    turned_ = [i_ for i_ in items_
               if not re.fullmatch(r'<item objectid="\d+" transform="1 0 0 0 1 0 0 0 1(?: [-\d.]+){3}"/>', i_)]
    turned_ += re.findall(r'<component [^>]*transform=[^>]*>', model)
    if turned_ or not items_:
        mod_bad.append((fname, "turned on the plate", turned_[:3]))
    for oname, head_ in re.findall(r'<object id="\d+"><metadata key="name" value="([^"]*)"/>(.*?)(?:<part|</object>)', cfg):
        if "bridge" in head_:
            mod_bad.append((fname, oname, "an object-level bridge setting"))
    found = []
    for oname, body_ in re.findall(r'<object id="\d+"><metadata key="name" value="([^"]*)"/>(.*?)</object>', cfg):
        vols_ = re.findall(r'<part id="(\d+)" subtype="([a-z_]+)">(.*?)</part>', body_)
        if any("bridge" in pb_ for _, st_, pb_ in vols_ if st_ != "modifier_part"):
            mod_bad.append((fname, oname, "a part with a bridge setting"))
        mods_ = [(pid_, dict(re.findall(r'<metadata key="([^"]+)" value="([^"]*)"/>', pb_))) for pid_, st_, pb_ in vols_
                 if st_ == "modifier_part"]
        item_ = [it_ for _, its_ in pls for it_ in its_ if it_[0] == oname]
        piece_ = s.on_bed(s.union([m for _, m, _ in item_[0][1]]))
        if not mods_:
            # left to the slicer: no strand it could lay is longer than these
            strand_, slot_ = longest_strand(piece_, s.SIDING_BRIDGE_Z), slot_strand(piece_)
            if strand_ > 20:
                mod_bad.append((fname, oname, "no modifier, strands up to", round(strand_, 1)))
            if slot_ > 20:
                mod_bad.append((fname, oname, "no modifier, a slot it may bridge along up to", round(slot_, 1)))
            if strand_ > 0:
                free_rows.append(f"{oname} {strand_:.1f}")
            slot_max = max(slot_max, slot_)
            continue
        found.append(oname)
        floor_ = oname == "floor"
        normal_ = np.vstack([meshes[pid_][0] for pid_, st_, _ in vols_ if st_ == "normal_part"])
        lo_n = normal_.min(axis=0)
        top_n = normal_.max(axis=0) - lo_n              # the piece as it lies on the bed: (0, 0, 0) to top_n
        # the layers that hang over anything: a wall's framing's are under its siding's first layer, the one holding SD;
        # the floor's, counting anything not printed on the layer under it, its seams'
        over_, prev_, zp_ = [], None, 0.0
        for z0_, z1_ in layers(piece_.bounding_box()[5]):
            zm_ = (z0_ + z1_) / 2
            cs_ = piece_.slice(zm_)
            if prev_ is not None and (cs_ - prev_.offset(0.0 if floor_ else 1.1 * (zm_ - zp_), RND)).area() > 0.05:
                over_.append(round(zm_, 3))
            prev_, zp_ = cs_, zm_
        siding_first = round([(z0_ + z1_) / 2 for z0_, z1_ in layers(s.SD + 1) if z0_ < s.SD <= z1_][0], 3)
        framing_top = max([z_ for z_ in over_ if z_ < siding_first] + [0.0])
        boxes_ = []
        for pid_, kv_ in mods_:
            mv_, mt_ = meshes.get(pid_, (np.zeros((0, 3)), np.zeros((0, 3), dtype=np.int64)))
            if not len(mv_) or not len(mt_):
                (floor_bad if floor_ else mod_bad).append((fname, oname, kv_.get("name"), "an empty modifier"))
                continue
            lo_m, hi_m = mv_.min(axis=0) - lo_n, mv_.max(axis=0) - lo_n
            z_from, z_to = lo_m[2], hi_m[2]
            boxes_.append(sbox(lo_m[0], lo_m[1], hi_m[0], hi_m[1]))
            # the modifier as the solid it is (Flash Studio applies its shape): a closed solid filling the box round its
            # corners, so that box is what it covers
            box_v_, fill_ = float(np.prod(hi_m - lo_m)), 0.0
            try:
                sol_ = M(m3.Mesh(vert_properties=np.asarray(mv_ - lo_n, dtype=np.float32),
                                 tri_verts=np.asarray(mt_, dtype=np.uint32)))
                if sol_.status() == m3.Error.NoError and box_v_ > 0:
                    fill_ = sol_.volume() / box_v_
            except Exception:
                fill_ = 0.0
            setting = {k_: v_ for k_, v_ in kv_.items() if k_ != "name"}
            ang_ = float(setting["bridge_angle"]) % 180 if sets_direction(setting) else 0.0
            # its part of the piece: everything inside its outline on the bed, up to its top
            region_ = piece_ ^ M.cube([hi_m[0] - lo_m[0], hi_m[1] - lo_m[1], 500 + z_to]).translate([lo_m[0], lo_m[1], -500])
            left_, long_ = bridges_across(region_, ang_, z_from, reach=0.0 if floor_ else None)
            ok_ = (abs(fill_ - 1) < 1e-3 and kv_.get("name") in (FLOOR_MODS if floor_ else WALL_MODS)
                   and setting == MOD_PLAN.get(kv_.get("name")) and sets_direction(setting) and left_ < 5 and long_ <= 20)
            if floor_:
                # over the layers that hang and no other, laying its bridges across the seams under it the short way: a
                # line at its angle runs over less of them than one at right angles (groove_run, the cabins' check). The
                # area left over and the 20 mm limit alone passed a box set nearly along its seam: strips set at 92
                # degrees, each line lying over its long seam for 11.5 mm, held at both ends (parity review, Nov 4 2026)
                inside_ = [round((z0_ + z1_) / 2, 3) for z0_, z1_ in layers(top_n[2]) if z_from < (z0_ + z1_) / 2 < z_to]
                floor_z.add((round(z_from, 2), round(z_to, 2)))
                floor_over = over_
                cross_, along_ = groove_run(piece_, ang_, region_), groove_run(piece_, ang_ + 90, region_)
                if not (ok_ and over_ and inside_ == over_ and cross_ < along_):
                    floor_bad.append((kv_.get("name"), setting, "fills %.4f of its box" % fill_, round(z_from, 3),
                                      round(z_to, 3), inside_, over_, round(left_, 2), round(long_, 1),
                                      "a line over its seams %.2f mm, at right angles %.2f" % (cross_, along_)))
                floor_rows.append(f"{kv_.get('name')} (x {max(lo_m[0], 0):.2f} to {min(hi_m[0], top_n[0]):.2f} of "
                                  f"{top_n[0]:.2f}), {setting}: laid at {ang_:.0f} degrees its bridges are {long_:.1f} mm "
                                  f"at most ({left_:.2f} mm2 left over), a line that way over its seams {cross_:.1f} mm "
                                  f"at most, at right angles {along_:.1f}")
                continue
            if not (ok_ and z_to >= top_n[2] and framing_top < z_from < siding_first):
                mod_bad.append((fname, oname, kv_.get("name"), setting, "fills %.4f of its box" % fill_, round(z_from, 3),
                                round(z_to, 2), round(framing_top, 2), round(left_, 2), round(long_, 1)))
            mod_rows.append(f"{oname}" + (f" ({kv_.get('name')}, y {max(lo_m[1], 0):.2f} to {min(hi_m[1], top_n[1]):.2f} "
                                          f"of {top_n[1]:.2f})" if len(mods_) > 1 else "")
                            + f": from z {z_from:.2f} (over its framing's last overhanging layer, {framing_top:.2f}, "
                            f"under its siding's first, {siding_first:.2f}), {setting}; laid at {ang_:.0f} degrees its "
                            f"bridges are {long_:.1f} mm at most ({left_:.2f} mm2 left over)")
        # together over the whole piece, and one over another nowhere (two settings at once)
        whole_ = sbox(0, 0, top_n[0], top_n[1])
        short_ = whole_.difference(shapely.union_all(boxes_)).area
        twice_ = sum(a_.intersection(b_).area for a_, b_ in itertools.combinations(boxes_, 2))
        if short_ > 1e-6 or twice_ > 1e-6:
            (floor_bad if floor_ else mod_bad).append((fname, oname, "not covered mm2", round(short_, 4),
                                                      "covered twice mm2", round(twice_, 4)))
    if sorted(found) != sorted(WANT_MODS[fname]):
        mod_bad.append((fname, "modifiers on", found))
report(not mod_bad,
       f"the bridge direction: in the files as written every piece lies on its plate unturned, and the four walls and the "
       f"fit test's three pieces cut from them carry modifiers, each a closed solid filling its box, together over the "
       f"whole piece from under their siding up and one over another nowhere, each setting External bridge infill "
       f"direction exactly as planned, a number other than 0; " + "; ".join(mod_rows) + " (20 or less); the floor carries "
       f"its own (next line); nothing else has a bridge setting, over z {s.SIDING_BRIDGE_Z:.2f} nothing else hangs out "
       f"more than {max([0.0] + [float(r_.split()[-1]) for r_ in free_rows]):.1f} mm across in any direction "
       f"({', '.join(free_rows)}), and on no layer has anything else a slot like a floor seam longer than {slot_max:.1f} "
       f"mm, so no way the slicer lays it makes a longer strand; under their siding the walls bridge the way the slicer "
       f"picks, as proven"
       + (f" (wrong: {mod_bad})" if mod_bad else ""))
report(not floor_bad and len(floor_z) == 1 and len(floor_rows) == 2 * len(s.LONG_SEAMS) + 1,
       f"the floor's seams, its first layer, slots 0.4 mm wide: in the file as written the floor carries "
       f"{len(floor_rows)} modifiers, each a closed solid filling its box and set exactly as planned, over z "
       f"{', '.join('%.2f to %.2f' % z_ for z_ in sorted(floor_z))} and nowhere else, so over its "
       f"{', '.join('%.2f' % z_ for z_ in floor_over)} layer, the only one of the floor over anything not printed under "
       f"it, together over the whole floor and one over another nowhere: " + "; ".join(floor_rows)
       + ", counting everything not printed under it; each box lays its bridges across its seams the short way (a line "
         "at its angle runs over less of them than one at right angles), so every bridge there crosses a seam and none "
         "runs along one"
       + (f" (wrong: {floor_bad})" if floor_bad else ""))


# ======================================================================== 11
group("11. Fit test")
lw, ewc, cf, stub, skst = s.corner_test({n: p[n] for n in WALLS}, fl)
none = max(overlap(a, b) for a, b in itertools.combinations([lw, ewc, cf, stub, skst], 2))
held = min(overlap(lw.translate([0, 0, 0.3]), cf), overlap(ewc.translate([0, 0, 0.3]), cf))
ac = s.PRONGS[s.FIT_END][0]
(a0, a1), _ = s.prong_spans(ac)
z0, z1 = s.ZF - 0.5 + 0.01, s.LEG_ROOT - 0.01
legb = s.wall_box(s.FIT_END, a0, a1, s.BARB, s.BARB + s.PRONG_T, z0 - 1, z1 + 1)
near = s.wall_box(s.FIT_END, a0 - 0.15, a1 + 0.15, s.BARB - 0.15, s.BARB + s.PRONG_T + 0.15, z0, z1) - legb
free = overlap(ewc, near)
has_leg = overlap(ewc, s.wall_box(s.FIT_END, a0, a1, s.BARB, s.BARB + s.PRONG_T, z0, z1))
on_l = overlap(stub.translate([0.005, 0, 0]), lw)
on_e = overlap(stub.translate([0, 0.005, 0]), ewc)
touch = reach_area(stub, s.union([lw, ewc]), -1, -1, (1.0, 10.0, 19.0), 0.09)
sk_held = min(overlap(skst.translate(t), cf) for t in ([0.3, 0, 0], [-0.3, 0, 0], [0, 0.3, 0], [0, -0.3, 0]))
sk_up = overlap(skst.translate([0, 0, 0.3]), cf)
report(none < 0.001 and held > 0.05 and free < 1e-4 and has_leg > 1 and on_l > 0.05 and on_e > 0.05 and touch < 1e-4
       and sk_held > 0.05 and sk_up > 0.5,
       f"the roll-up corner goes together like the real one: nothing overlaps ({none:.5f} mm3); lifted 0.3 both walls' "
       f"barbs catch ({held:.2f} mm3); the prong under the jamb at {ac:+.1f}, rooted in the bottom plate, is free to "
       f"LEG_ROOT ({free:.6f} mm3 within 0.15 of its leg); the angle stub sits on both recess floors ({on_l:.3f}, "
       f"{on_e:.3f} mm3 pushed 0.005 in) touching nothing else ({touch:.6f} mm2); the skid stub's peg holds it in its "
       f"hole (moved 0.3: {sk_held:.2f} mm3) and it sits flat under the floor (raised 0.3: {sk_up:.1f} mm3)")
# the corner re-cut for the lift-out (spec_rollup.md J.1): the floor bit ends at x -23.0, past the post at -35 in,
# whose notch keeps at least 0.6 of floor to the cut; the short roll-up end over that post, so its skirt ends on the
# post, and inside the siding groove there (so its top layer ends at the groove); its rebate filled
cfb, ewb = cf.bounding_box(), ewc.bounding_box()
fr_ = sorted((q.bounding_box()[0], q.bounding_box()[3]) for q in
             (cf ^ s.ru_box(-60, 0, 0.98, 1.02, 2.98, 3.02)).decompose())
beyond = fr_[-1][1] - fr_[-1][0] if fr_ else 0.0
notch_c = (fr_[-2][1] + fr_[-1][0]) / 2 if len(fr_) > 1 else 0.0
z_shift = (s.ZWT - 10) - (s.ZF + 8)
fill_box = s.ru_box(-s.RU_W / 2 + 0.01, s.FIT_WALL_X - 0.01, 0.01, s.REB_U - 0.01, s.ZWT - 10 + 0.01 - z_shift,
                    s.MOUTH + s.REB_H - 0.01 - z_shift)
filled = overlap(ewc, fill_box) / fill_box.volume()
post_end = (ewc ^ s.ru_box(-30, 0, 0.5, 3.0, 0.5, 3.0)).bounding_box()[3]
post_x = (-35 * s.S - s.SW / 2, -35 * s.S + s.SW / 2)
report(abs(cfb[3] - s.FIT_END_X) < 1e-6 and abs(ewb[3] - s.FIT_WALL_X) < 1e-6 and abs(post_end - s.FIT_WALL_X) < 1e-6
       and post_x[0] + 0.42 <= s.FIT_WALL_X <= post_x[1]
       and beyond >= 0.6 and abs(notch_c - (-35 * s.S)) < 1e-3 and filled > 0.999,
       f"the corner's bit of floor ends at x {cfb[3]:.2f} ({cfb[3] - cfb[0]:.2f} along the roll-up end's edge and "
       f"{cfb[4] - cfb[1]:.2f} along the plain side's), past the post notch at {notch_c:.3f} (-35 in), which keeps "
       f"{beyond:.3f} mm of floor to the cut (at least 0.6); the short roll-up end ends at {ewb[3]:.3f}, over that post "
       f"(x {post_x[0]:.3f}..{post_x[1]:.3f}, cut there too: {post_end:.3f}), so its skirt ends on the post; its rebate is "
       f"filled ({filled * 100:.1f}%), the half doorway tests it")
# below the join each corner piece is exactly the real wall or floor (the Lofted Barn Garage's line)
z_lo_ = s.ZF + 8
low_box = s.box(-s.BIG, s.BIG, -s.BIG, s.BIG, -5, z_lo_)
lo_same = [abs(overlap(piece_ ^ low_box, real_) - (piece_ ^ low_box).volume())
           for piece_, real_ in ((lw, p[s.FIT_LONG]), (ewc, p[s.FIT_END]), (cf, fl))]


def runs_ax(piece, region, axis):
    """[(lo, hi)] along axis of the pieces of piece inside region."""
    return sorted((q.bounding_box()[axis], q.bounding_box()[axis + 3]) for q in (piece ^ region).decompose())


ends_ = runs_ax(lw, s.wall_box(s.FIT_LONG, -s.L / 2 - 1, -s.L / 2 + 40, 4.94, 4.96, s.ZF + 3, s.ZF + 3.1), 1)
end_w = min(b_ - a_ for a_, b_ in ends_) if ends_ else 0.0
lw_end = lw.bounding_box()[4]
report(max(lo_same) < 1e-3 and end_w >= 0.6 and abs(lw_end - (-(112 * s.S - s.GROOVE_W / 2) - 0.1)) < 1e-6,
       f"the corner's pieces are cut from the real parts: below the join each is exactly the real wall or floor "
       f"({max(lo_same):.5f} mm3 off); the short plain side ends at y {lw_end:.3f}, 0.1 inside its -112 in siding groove "
       f"over the stud's post, and on its siding's top layer the narrowest strip between grooves, the one at its cut end "
       f"included, is {end_w:.2f} mm, over a line wide, so nothing prints as a loose strand")
fit_pieces = s.corner_test_parts({n: p[n] for n in WALLS}, fl)
worst = max(worst_overhang(m)[0] for _, m in fit_pieces)
# where the fit test's walls are cut short (the short roll-up end at its doorway side, the half doorway at both
# ends), no layer is left with a strip thinner than a line: each cut is inside a siding groove, so the top layer ends
# at the groove
cut_thin, cut_rows = 0.0, []
for nm_, ends_ in (("short roll-up end", ("max",)), ("short plain side", ("min",)), ("half roll-up doorway", ("min", "max"))):
    m_ = dict(fit_pieces)[nm_]
    bbm = m_.bounding_box()
    worst_ = 0.0
    for z0_, z1_ in layers(bbm[5]):
        cs_ = m_.slice((z0_ + z1_) / 2)
        th_ = cs_ - cs_.offset(-0.21, MIT, 2).offset(0.21, MIT, 2)
        for e_ in ends_:
            xe = bbm[0] if e_ == "min" else bbm[3]
            strip_ = square(xe - 1.5, xe + 1.5, bbm[1] - 1, bbm[4] + 1)
            worst_ = max(worst_, (th_ ^ strip_).area())
    cut_thin = max(cut_thin, worst_)
    cut_rows.append(f"{nm_} {worst_:.4f}")
report(worst < 5 and cut_thin < 0.05,
       f"the fit test's roll-up pieces (the corner, its floor and stubs, the half doorway and the half door) print with "
       f"nothing steeper than 45 degrees that isn't a bridge, nothing starting in mid-air ({worst:.2f} mm2 worst layer); "
       f"within 1.5 mm of where the walls are cut short nothing on any layer is thinner than a line ("
       + ", ".join(cut_rows) + " mm2 at the most; the cuts are inside siding grooves at x "
       f"{s.FIT_WALL_X:.3f} and {s.FIT_FRAME_X0:.3f} and y {lw_end:.3f})")
# the half roll-up doorway and half roll-up door (spec_rollup.md J.2, J.3): cut from the real parts, and the half door
# in the half doorway moves exactly as the real door in the real doorway, drawn and printed
frame = s.curtain_frame({n: p[n] for n in WALLS})
stub_c = s.union(list(s.curtain_stub()))
XM = s.FIT_XM


def sym(a_, b_):
    return (a_ - b_).volume() + (b_ - a_).volume()


def mirror_xm(m_):
    return m_.mirror([1, 0, 0]).translate([2 * XM, 0, 0])


hz0 = s.ru_box(-s.HDL_HALF - 0.4, s.HDL_HALF + 0.4, s.RU_FACE - 0.011, 9.0, s.RAIL_Z0 - 0.02, s.HDL_Z0 + s.HDL_HT + 0.32)
hzm = hz0.translate([XM, 0, 0])
band_ = s.box(-s.CUR_HALF - 0.1, -1.6, -s.BIG, s.BIG, -s.BIG, s.BIG)
d_body = sym((stub_c - hz0 - hzm) ^ band_, (cur - hz0 - hzm) ^ band_)
d_hdl = sym(stub_c ^ hzm, (cur ^ hz0).translate([XM, 0, 0]))
zb_ = s.box(-s.BIG, s.BIG, -s.BIG, s.BIG, s.RAIL_Z0, s.Z_FT - 0.01)
d_end = sym(stub_c ^ s.box(-1.6, 0, -s.BIG, s.BIG, -s.BIG, s.BIG) ^ zb_,
            mirror_xm(cur ^ s.box(-s.CUR_HALF - 0.01, -s.CUR_HALF + 1.3, -s.BIG, s.BIG, -s.BIG, s.BIG) ^ zb_))
sb_ = stub_c.bounding_box()
low_ = s.box(-s.BIG, s.BIG, -s.BIG, s.BIG, -1, s.ZWT)
d_fr = sym(frame ^ s.box(s.FIT_FRAME_X0, -1.6, -s.BIG, s.BIG, -s.BIG, s.BIG),
           ew ^ s.box(s.FIT_FRAME_X0, -1.6, -s.BIG, s.BIG, -s.BIG, s.BIG) ^ low_)
d_jamb = sym(frame ^ s.box(0.01, 9.0, -s.BIG, s.BIG, -s.BIG, s.BIG),
             mirror_xm(ew ^ s.box(s.FIT_FRAME_X0, -s.RU_W / 2 - 0.01, -s.BIG, s.BIG, -s.BIG, s.BIG) ^ low_))
fbb = frame.bounding_box()
report(max(d_body, d_hdl, d_end, d_fr, d_jamb) < 1e-3 and abs(sb_[0] + s.CUR_HALF) < 1e-6 and abs(sb_[3] - s.FIT_STUB_X1) < 1e-6,
       f"the half door is the real curtain's -x half, x {sb_[0]:.3f} to {sb_[3]:.3f}, {sb_[5] - sb_[2]:.2f} tall: the "
       f"same as the real one off its handle ({d_body:.5f} mm3 apart), the real handle moved to its middle at x "
       f"{XM:.3f} ({d_hdl:.5f}), its +x end chamfered as the real -x end ({d_end:.5f}); the half doorway is the real "
       f"roll-up end from x {fbb[0]:.2f} to the middle, {fbb[5] - fbb[2]:.2f} tall ({d_fr:.5f} mm3 apart), closed by its "
       f"own jamb mirrored about x {XM:.3f}, to x {fbb[3]:.2f} ({d_jamb:.5f})")
frame_near = frame ^ s.box(-45, 10, -s.BIG, s.BIG, -1, s.MOUTH + 8)
XS_stub = stations(edges_of((-1,), XM) + [s.FIT_STUB_X1, s.FIT_STUB_X1 - s.CUR_CHAMF,
                                          -s.RU_W / 2 - (-s.STOP_X0 - s.STOP_RELIEF_X), -s.RU_W / 2 + s.STOP_X0],
                   -s.CUR_HALF - 0.1, s.FIT_STUB_X1 + 0.1, fine=[-0.35 - 0.1 * k for k in range(14)]
                   + [-(32.25 + 0.1 * k) for k in range(14)])
STUB_ZONES = [(-H_ - 0.35, -s.STOP_X0 + 0.35), (2 * XM + s.STOP_X0 - 0.35, 2 * XM + H_ + 0.35)]   # its jamb, mirrored
srigs = {k: build_rig(stub_c, frame_near, None, XS_stub, k == "printed", label=k, zones=STUB_ZONES)
         for k in ("drawn", "printed")}
same, rows_ = True, []
for k in ("drawn", "printed"):
    r_ = srigs[k]
    sd = settle(r_)
    st_ = rigid_stop(r_, sd)
    nd_ = least_lift(r_, sd, st_)
    w_all = 0.0
    lifts_ = sorted({round(nd_ + 0.1 * j, 3) for j in range(20) if nd_ is not None and nd_ + 0.1 * j <= st_ + 1e-9}
                    | {round(st_ - 0.15, 3)})
    for lf in lifts_:
        for th in (6.0, 7.0, 8.0):
            w_all = max(w_all, run(r_, removal_phases(sd, lf, th))[0])
    mot = [motion(r_, sd, round(st_ - 0.15, 3), fn(sd, round(st_ - 0.15, 3)))[1] for fn in MOTIONS.values()]
    bands_, nolean_ = [], []
    for th in (6.0, 7.0, 8.0):
        res = {(k, th, phi): insertion(r_, sd, st_, nd_, th, phi) for phi in PHIS}
        bs, br = band(res, k, th), band(ins, k, th)
        bands_.append((th, bs, br))
        nolean_.append(res[(k, th, 0.0)]["what"])
    pre_s = r_.springs(removal_pose(sd))
    fpre_s, tpre_s = pre_s["fbend"], pre_s["tb_u"].max()
    sw_ = s.STUB_WEIGHT_G / s.CUR_WEIGHT_G                          # its weight against the real door's
    hold_up = [kf[E_] * fpre_s / (sw_ * WEIGHT) for E_ in (2500.0, 3500.0)]   # one finger
    hold_fd = [k_ * tpre_s / (sw_ * face_down) for k_ in kt]                    # one tab
    held_ = k != "drawn" or (min(hold_up) > 1.5 and min(hold_fd) > 1.5)
    ok_ = (sd == seats[k] and abs(st_ - stops[k]) <= 0.025 + 1e-9 and nd_ is not None and needs[k] is not None
           and fpre_s > 0.1 and tpre_s > 0.1 and held_
           and abs(nd_ - needs[k]) <= 0.05 + 1e-9
           and w_all <= TOL and None not in mot and all(w_.startswith("catches") for w_ in nolean_)
           and all(None not in bs and None not in br and abs(bs[0] - br[0]) <= 0.1 + 1e-9 and abs(bs[1] - br[1]) <= 0.1 + 1e-9
                   for _, bs, br in bands_))
    same = same and ok_
    rows_.append(f"{k}: seat {sd[0]:+.3f}, {sd[1]:+.3f} (real {seats[k][0]:+.3f}, {seats[k][1]:+.3f}), preloads "
                 f"{fpre_s:.2f} / {tpre_s:.2f} (over 0.1), weighing {s.STUB_WEIGHT_G} g on one finger and one tab it holds "
                 f"{hold_up[0]:.2f} to {hold_up[1]:.2f} times its weight upside down and {hold_fd[0]:.2f} to "
                 f"{hold_fd[1]:.2f} times what it needs face down" + (" (over 1.5)" if k == "drawn" else "") + f", stop {st_:.3f} "
                 f"({stops[k]:.3f}), least lift {nd_} ({needs[k]}), out by H.3 at {len(lifts_)} lifts and 3 swings "
                 f"touching nothing rigid ({w_all:.5f} mm2), the hand motions at the stop less 0.15 clear at "
                 f"{', '.join(str(m_) for m_ in mot)} degrees, with no lean it "
                 + ("catches at 6, 7 and 8 degrees" if all(w_.startswith("catches") for w_ in nolean_) else f"does: {nolean_}")
                 + ", and goes in leaned "
                 + ", ".join(f"{th:g}: {bs[0]:+.2f} to {bs[1]:+.2f} ({br[0]:+.2f} to {br[1]:+.2f})"
                             if None not in bs + br else f"{th:g}: none" for th, bs, br in bands_))
report(same, "the half door in the half doorway moves as the real door in the real doorway, a little over half its "
             f"weight ({s.STUB_WEIGHT_G} g against {s.CUR_WEIGHT_G}: its handle is full size) on half its springs (its "
             f"numbers, then the real one's; {len(srigs['drawn'].xs)} different sections): " + "; ".join(rows_))
fd, fdoor = s.fit_doorway(), s.fit_door()
fbase = s.fit_door_to_shed(0)
ftop = s.FIT_ZF + s.DOOR_BOTTOM_GAP + s.FIT_DH
fH = s.FIT_DH + s.PIN_BOTTOM_LEN
fworst, ffloor, fhead, fnolift, flift = hang_path(fdoor, fbase, ftop, fH, fd, s.FIT_ZF, s.FIT_ZF + s.FIT_OH)
swing = max(overlap(fd, fdoor.transform(s.fit_door_to_shed(deg))) for deg in range(0, 92, 2))
stop = overlap(fd, fdoor.transform(s.fit_door_to_shed(-2)))
report(fworst < 0.01 and ffloor > 0.1 and fhead > 0.0 and fnolift > 0.01 and swing < 0.01 and stop > 0.05,
       f"the short doorway's door goes in by F7's way, pushed up as far as the head lets it ({flift:.2f} at the "
       f"steepest tilt, {math.degrees(math.asin(2.8 / fH)):.1f} degrees), every step clear ({fworst:.5f} mm3; "
       f"{ffloor:.3f} over the trench floor, {fhead:.3f} under the head; with no lift its pin runs into the sill "
       f"block, {fnolift:.3f} mm3), swings in to 90 degrees clear ({swing:.5f} mm3) and meets "
       f"the stop at -2 ({stop:.2f} mm3)")
blk, cpn = s.on_bed(s.peg_block()), s.peg_coupon()
peg_low = (blk ^ s.box(-s.BIG, s.BIG, 6.5, s.BIG, -1, s.BIG)).bounding_box()
peg_d = peg_low[5] - peg_low[2]
hole_d = 2 * max(np.hypot(*q[:2]) for q in mesh_pts((s.box(-1.6, 1.6, -1.6, 1.6, 0.1, 0.2) - cpn)))
report(abs(peg_low[2]) < 1e-9 and abs(peg_d - s.PEG_D) < 0.01 and (hole_d - peg_d) / 2 >= 0.39,
       f"the roof peg lies on the bed (its lowest point at z {peg_low[2]:.3f}), {peg_d:.2f} across, and goes into the "
       f"bit of roof's {hole_d:.2f} hole with {(hole_d - peg_d) / 2:.2f} round it")


# ======================================================================== 12
group("12. Shop numbers, at full size")
THRESHOLD_IN = 0.94      # the threshold's height over the floor, open question 16's default, typed in here (not read from
                         # the generator); with the tuning table's LIP_H 0.466 it goes to 0.66


def extent(piece, region, axis):
    bb = (piece ^ region).bounding_box()
    return bb[axis], bb[axis + 3]


floor_top = fl.bounding_box()[5]
ys_bare = -30.0                                           # a stretch of bare siding on both long walls
sx0 = extent(body, s.box(-60, 0, ys_bare - 0.1, ys_bare + 0.1, s.ZF + 20, s.ZF + 20.2), 0)[0]
sx1 = extent(body, s.box(0, 60, ys_bare - 0.1, ys_bare + 0.1, s.ZF + 20, s.ZF + 20.2), 0)[1]
sy0 = extent(body, s.box(-40.1, -39.9, -120, 0, s.ZF + 50, s.ZF + 50.2), 1)[0]
sy1 = extent(body, s.box(-40.1, -39.9, 0, 120, s.ZF + 50, s.ZF + 50.2), 1)[1]
report(abs((sx1 - sx0) * inch - 134) < 0.01 and abs((sy1 - sy0) * inch - 288) < 0.01,
       f"{(sx1 - sx0) * inch:.2f} x {(sy1 - sy0) * inch:.2f} in, siding to siding (shop: 134 "
       f"x 288 in, the 12-wide's actual)")
wall_top = extent(p["plain side"], s.box(-60, 0, 40, 41, 0, 200), 2)[1] + 0.15
report(abs((wall_top - floor_top) * inch - 93.5) < 0.01,
       f"walls {(wall_top - floor_top) * inch:.2f} in from the floor to the top of the top plates (shop: 93 1/2 in)")
peak = p["back end"].bounding_box()[5]
pitch = (peak - s.ZWT) / (s.W / 2)
report(abs(pitch * 12 - 5) < 0.01 and abs((peak - s.ZWT) * inch - 27.92) < 0.01,
       f"roof {pitch * 12:.3f}/12, its underside {(peak - s.ZWT) * inch:.2f} in over the plates at the ridge")
rb_ = roof.bounding_box()
eave = (rb_[3] - sx1) * inch
rake = (rb_[4] - sy1) * inch
report(abs(eave - 4.0) < 0.01 and abs(rake - 5.4) < 0.01,
       f"eave {eave:.2f} in out from the siding, measured level (shop: 4 in); rake "
       f"{rake:.2f} in past each gable (5.4 in)")
ru = p["roll-up end"]
yc = -s.L / 2 - 0.3                                       # in the casings, which edge each opening
g0 = extent(ru, s.box(-60, -0.1, yc - 0.1, yc + 0.1, s.ZF + 20, s.ZF + 20.2), 0)[1]
g1 = extent(ru, s.box(0.1, 60, yc - 0.1, yc + 0.1, s.ZF + 20, s.ZF + 20.2), 0)[0]
rtop = extent(ru, s.box(-1, 1, yc - 0.1, yc + 0.1, s.ZF + 30, s.ZWT), 2)[0]
kb_ = s.wall_box("roll-up end", g1 + 0.1, g1 + 0.9, 0.5, 1.5, s.ZF + s.PLATE_BOT + 0.01, s.ZWT - 0.01)
kfill = overlap(ru, kb_) / kb_.volume()
report(abs((g1 - g0) * inch - 96) < 0.01 and abs((rtop - floor_top) * inch - 76.8) < 0.01 and abs((g0 + g1) / 2) < 1e-6
       and abs((s.ZWT - s.PLATE_TOP - floor_top) * inch - 90.5) < 0.01 and kfill > 0.999,
       f"roll-up opening {(g1 - g0) * inch:.2f} x {(rtop - floor_top) * inch:.2f} in, centred ({(g0 + g1) / 2:.4f} mm "
       f"off), its king studs solid up into the top plates, whose underside is "
       f"{(s.ZWT - s.PLATE_TOP - floor_top) * inch:.2f} in up (shop: 96 x 76.8 in, kings to the plate at 90.5 in)")
xc = s.W / 2 + 0.3                                        # in the casings, where only trim stands


def runs(piece, z, x=xc):
    """[(y0, y1)] of the piece along the door side's line at (x, z), from -y to +y."""
    return sorted((b[1], b[4]) for b in (q.bounding_box() for q in
                                         (piece ^ s.box(x - 0.1, x + 0.1, -s.BIG, s.BIG, z, z + 0.2)).decompose()))


# the openings found off the casings, not from the generator's numbers: at 20 mm up only the steel
# door's two jamb boards stand proud (the window is higher), at 40 mm up its two and the window's two
low_runs, mid_runs = runs(ds, s.ZF + 20), runs(ds, s.ZF + 40)
d0, d1 = (low_runs[0][1], low_runs[1][0]) if len(low_runs) == 2 else (0.0, 0.0)
win_runs = [r for r in mid_runs if all(abs(r[0] - q[0]) > 0.01 for q in low_runs)]
w0, w1 = (win_runs[0][1], win_runs[1][0]) if len(win_runs) == 2 else (0.0, 0.0)
dc, wc = (d0 + d1) / 2, (w0 + w1) / 2
dtop = extent(ds, s.box(xc - 0.1, xc + 0.1, dc - 0.1, dc + 0.1, s.ZF + 30, s.ZWT), 2)[0]
report(len(low_runs) == 2 and abs((d1 - d0) * inch - 36) < 0.01 and abs((dtop - floor_top) * inch - 75.6) < 0.01
       and abs(dc * inch + 78) < 0.01 and abs((d0 - sy0) * inch - 48) < 0.01
       and abs(d0 + 67.733) < 0.001 and abs(d1 + 42.333) < 0.001 and abs(dc + 55.033) < 0.001,
       f"steel door opening {(d1 - d0) * inch:.2f} x {(dtop - floor_top) * inch:.2f} in, y {d0:.3f} to {d1:.3f} (centre "
       f"{dc:.3f}), {dc * inch / 12:+.2f} ft from the door side's middle, toward the "
       f"{'roll-up end' if dc < 0 else 'back end'}; its near edge "
       f"{(d0 - sy0) * inch / 12:.2f} ft in from the roll-up end's siding face (Alan's standard: 36 x 75.6 in, near "
       f"edge 4 ft from the corner, centre -6.5 ft = y -55.033, opening -67.733..-42.333)")
yw = w0 + 2.0                                             # beside the muntin, through the sashes' rings
wt = extent(ds, s.box(xc - 0.1, xc + 0.1, yw - 0.1, yw + 0.1, s.ZF + 45, s.ZWT), 2)[0]
wb_ = extent(ds, s.box(xc - 0.1, xc + 0.1, yw - 0.1, yw + 0.1, s.ZF, s.ZF + 45), 2)[1]
uw = s.W / 2 - s.WT + 1.0
wp = extent(ds, s.box(uw - 0.1, uw + 0.1, wc - 0.1, wc + 0.1, wt + 0.05, wt + 5), 2)[1]
report(len(win_runs) == 2 and len(mid_runs) == 4 and abs((w1 - w0) * inch - 25.2) < 0.01
       and abs((wt - wb_) * inch - 34.8) < 0.01 and abs((wt - floor_top) * inch - 76.5) < 0.01
       and abs(wc * inch - 42) < 0.01 and abs(wc - (d1 + sy1) / 2) < 0.001 and abs(wc - 29.633) < 0.001
       and abs((s.ZWT - s.PLATE_TOP - wp) * inch - 12.5) < 0.01,
       f"window opening {(w1 - w0) * inch:.2f} x {(wt - wb_) * inch:.2f} in, centred y {wc:.3f}, {wc * inch / 12:+.2f} "
       f"ft, toward the {'back end' if wc > 0 else 'roll-up end'}: {abs(wc - (d1 + sy1) / 2):.4f} mm off halfway "
       f"between the steel door's far edge "
       f"({d1:.3f}) and the back end's siding face ({sy1:.3f}); its top {(wt - floor_top) * inch:.2f} in up; the "
       f"window plate's top {(s.ZWT - s.PLATE_TOP - wp) * inch:.2f} in under the top plates (Alan's standard: centred "
       f"between the walk door and the back, +3.5 ft = y +29.633; shop: 25.2 x 34.8 in, top 76.5 in, plate 12.5 in under)")
hz = extent(ds, s.box(uw - 0.1, uw + 0.1, dc - 0.1, dc + 0.1, s.ZF + 30, s.ZWT - s.PLATE_TOP - 0.05), 2)
# over the header the full studs run on up to the top plates; between them and the first cripple it is
# open, so the full studs' inner faces there are where the header's ends are
zo = (hz[1] + s.ZWT - s.PLATE_TOP) / 2
e0 = extent(ds, s.box(uw - 0.1, uw + 0.1, d0 - 3, d0 + 2, zo, zo + 0.1), 1)[1]
e1 = extent(ds, s.box(uw - 0.1, uw + 0.1, d1 - 2, d1 + 3, zo, zo + 0.1), 1)[0]
kings_ok = all(abs(overlap(ds, kb) - kb.volume()) < 1e-4 for kb in
               (s.box(uw - 0.1, uw + 0.1, e0 + 0.01, d0 - 0.01, s.ZF + s.PLATE_BOT + 0.01, hz[1] - 0.01),
                s.box(uw - 0.1, uw + 0.1, d1 + 0.01, e1 - 0.01, s.ZF + s.PLATE_BOT + 0.01, hz[1] - 0.01)))
report(abs((hz[1] - hz[0]) * inch - 5.0) < 0.01 and abs((hz[0] - floor_top) * inch - 75.6) < 0.01 and kings_ok
       and abs((d0 - e0) * inch - 1.5) < 0.01 and abs((e1 - d1) * inch - 1.5) < 0.01,
       f"steel-door header {(hz[1] - hz[0]) * inch:.2f} in tall, on the doorway's top at "
       f"{(hz[0] - floor_top) * inch:.2f} in, bearing {(d0 - e0) * inch:.2f} and {(e1 - d1) * inch:.2f} "
       f"in on the king studs under its ends (shop: Alan's 5 in loft header, 1 1/2 in on each king)")
# the door side's framing round both openings, measured through the middle of its studs (u = SD/2) all
# along the wall between the end walls' inside faces, from the floor's top to the plates' top, and
# compared with the framing Alan's rules give for openings where the casings put them (F8, spec 4.4
# and 4.5). The 16 in marks are counted here off the roll-up end's siding face, not taken from the
# generator's mark plan: a mark whose stud would land on an opening's king or full stud is dropped, one
# inside the doorway is a cripple over the header, one inside the window a stud over the window plate
# and another under the rough sill, any other a full stud. Left out of the comparison: the window's
# opening, where its sashes are (the next proof), and the top pin hole in the header (group 7). Which
# marks are which is Alan's layout, so that is written out here too
sw, u_mid = 1.5 / inch, s.SD / 2
z_bp = floor_top + s.PLATE_BOT                            # the bottom plate's top (held, F4)
z_tp = floor_top + 90.5 / inch                            # the top plates' underside (shop: 90 1/2 in)
z_pt = floor_top + 93.5 / inch - 0.15                     # their top: the long walls stop 0.15 under the roof
y_in = sy1 - s.WT                                         # the end walls' inside faces, at -y_in and +y_in
h_top = dtop + 5.0 / inch                                 # the header's top
p_top, s_bot = wt + 1.5 / inch, wb_ - 1.5 / inch          # the window plate's top, the rough sill's bottom
bands = [(d0 - 2 * sw, d0), (d1, d1 + 2 * sw), (w0 - 2 * sw, w0), (w1, w1 + 2 * sw)]
plan = []
for k in range(1, 18):
    a = sy0 + 16 * k / inch
    lo, hi = a - sw / 2, a + sw / 2
    plan.append((a, "dropped" if any(hi > b0 + 1e-6 and lo < b1 - 1e-6 for b0, b1 in bands) else
                 "cripple" if lo >= d0 and hi <= d1 else "window" if lo >= w0 and hi <= w1 else "stud"))
frame = [(-y_in, d0, floor_top, z_bp), (d1, y_in, floor_top, z_bp), (-y_in, y_in, z_tp, z_pt),   # plates
         (-y_in, -y_in + sw, z_bp, z_tp), (y_in - sw, y_in, z_bp, z_tp),                       # end studs
         (d0 - 2 * sw, d0 - sw, z_bp, z_tp), (d1 + sw, d1 + 2 * sw, z_bp, z_tp),               # door: full studs,
         (d0 - sw, d0, z_bp, dtop), (d1, d1 + sw, z_bp, dtop), (d0 - sw, d1 + sw, dtop, h_top),   # kings, header
         (w0 - 2 * sw, w0 - sw, z_bp, z_tp), (w1 + sw, w1 + 2 * sw, z_bp, z_tp),               # window: full studs,
         (w0 - sw, w0, z_bp, wt), (w1, w1 + sw, z_bp, wt), (w0 - sw, w1 + sw, wt, p_top),        # kings, plate,
         (w0, w1, s_bot, wb_)]                                                                  # rough sill
for a, kind in plan:
    lo, hi = a - sw / 2, a + sw / 2
    frame += {"stud": [(lo, hi, z_bp, z_tp)], "cripple": [(lo, hi, h_top, z_tp)],
              "window": [(lo, hi, p_top, z_tp), (lo, hi, z_bp, s_bot)], "dropped": []}[kind]


def fslab(y0, y1, z0, z1):
    return s.wall_box("door side", y0, y1, u_mid - 0.05, u_mid + 0.05, z0, z1)


def where(m):
    """Where the real pieces of a difference are (the slivers a boolean leaves on shared faces left out)."""
    bbs = [q.bounding_box() for q in m.decompose() if q.volume() > 1e-6]
    return "".join(f" at y {b[1]:.3f}..{b[4]:.3f}, z {b[2]:.3f}..{b[5]:.3f}" for b in bbs[:3]) + (
        f" and {len(bbs) - 3} more" if len(bbs) > 3 else "")


r_pin = s.PIN_HOLE_D / 2 + 0.01
care = fslab(-y_in, y_in, floor_top, z_pt) - s.union(
    [fslab(w0, w1, wb_, wt), fslab(s.AXIS_Y - r_pin, s.AXIS_Y + r_pin, dtop - 0.01, dtop + s.HOLE_TOP_DEPTH + 0.01)])
want_f = s.union([fslab(*b) for b in frame]) ^ care
got_f = ds ^ care
extra_f, miss_f = got_f - want_f, want_f - got_f
mid_y = (sy0 + sy1) / 2
named = {kd: [round((a - mid_y) * inch) for a, k_ in plan if k_ == kd] for kd in ("dropped", "cripple", "window", "stud")}
report(extra_f.volume() < 1e-5 and miss_f.volume() < 1e-5 and named["dropped"] == [-96]
       and named["cripple"] == [-80, -64] and named["window"] == [32, 48] and len(named["stud"]) == 12,
       f"the door side's framing, measured through the middle of its studs (u {u_mid:.2f}) from y {-y_in:.3f} to "
       f"{y_in:.3f} and from the floor's top to the plates' top, is Alan's for the openings where the casings put them "
       f"({abs(extra_f.volume()):.6f} mm3 extra{where(extra_f)}, {abs(miss_f.volume()):.6f} mm3 missing{where(miss_f)}): of its "
       f"17 marks, 16 in apart from the roll-up end's siding face, "
       f"{', '.join(f'{m:+d}' for m in named['dropped'])} in dropped (its stud would be on the steel door's king), "
       f"{' and '.join(f'{m:+d}' for m in named['cripple'])} in cripples over the 5 in header, "
       f"{' and '.join(f'{m:+d}' for m in named['window'])} in studs over the window plate and under the rough sill, "
       f"the other {len(named['stud'])} full studs; each side of each opening a full stud and a king stud, the door's to "
       f"its header and the window's to its plate, which bears 1 1/2 in on both; the rough sill 1 1/2 in under the "
       f"window (Alan's layout: -96 dropped, -80 and -64 cripples, +32 and +48 over and under, 12 full studs)")
# nothing in the openings where they now are: through the doorway nothing of the body or the corner
# angles from the floor top to its head, out to where the stop's chamfer starts (u 2.45); from there
# out only the stop, 0.8 deep on the latch jamb; in the window nothing but its sashes
everything = s.union([body, p["angles"]])
u_stop, d_stop = s.STOP_POLY[0][1], s.STOP_POLY[1][0]
door_in = s.wall_box("door side", d0, d1, -0.01, u_stop - 0.05, floor_top + 0.01, dtop - 0.01)
door_out = s.wall_box("door side", d0, d1 - d_stop - 0.01, u_stop - 0.05, s.WT + s.PROUD + 0.5, floor_top + 0.01,
                      dtop - 0.01)
stop_box = s.wall_box("door side", d1 - d_stop + 0.01, d1, 3.3, s.WT - 0.01, floor_top + 0.01, dtop - 0.01)
v_in, v_out = overlap(everything, door_in), overlap(everything, door_out)
stop_fill = overlap(ds, stop_box) / stop_box.volume()
win_box = s.wall_box("door side", w0, w1, -0.01, s.WT + s.PROUD + 0.5, wb_ + 0.01, wt - 0.01)
sashes = s.union(s.window_unit()) ^ win_box
w_extra = ((everything ^ win_box) - sashes).volume()
w_sash = overlap(ds, sashes) / max(sashes.volume(), 1e-9)
report(v_in < 1e-6 and v_out < 1e-6 and stop_fill > 0.999 and w_extra < 1e-4 and w_sash > 0.999
       and sashes.volume() > 50,
       f"the openings are clear at their new places: nothing in the doorway y {d0:.3f}..{d1:.3f} from the floor top to "
       f"its head ({v_in:.6f} mm3 to u {u_stop:.2f}, {v_out:.6f} mm3 past it but for the stop, which fills its "
       f"{d_stop:.1f} mm on the latch jamb: {stop_fill * 100:.1f}%); in the window y {w0:.3f}..{w1:.3f} nothing but its "
       f"sashes ({w_extra:.6f} mm3 else; the sashes {sashes.volume():.1f} mm3, all there: {w_sash * 100:.1f}%)")
# the floor and the walls' feet keep clear of the moved openings: along the door side's rim band the
# floor's only cut under the doorway is the sill post's notch, the whole door framing wide, and the
# nearest other cut (a stud's notch or a prong's slot) is well off it; the mid-length roof peg and
# the corner recesses are clear of both casings
fl_runs = runs(fl, 3.0, x=s.W / 2 - s.WT + 1.0)
fl_gaps = [(a[1], b[0]) for a, b in zip(fl_runs, fl_runs[1:])]
under = [g for g in fl_gaps if g[1] > d0 and g[0] < d1]
sill_want = (d0 - 2 * s.SW - s.FIT, d1 + 2 * s.SW + s.FIT)
sill_ok = len(under) == 1 and abs(under[0][0] - sill_want[0]) < 0.001 and abs(under[0][1] - sill_want[1]) < 0.001
others_ = [g for g in fl_gaps if g not in under]
sill = under[0] if under else (0.0, 0.0)
near_lo = min((sill[0] - g[1] for g in others_ if g[1] <= sill[0]), default=0)
near_hi = min((g[0] - sill[1] for g in others_ if g[0] >= sill[1]), default=0)
slot_ok = all(not (sl[1] > d0 - 2 * s.SW and sl[0] < d1 + 2 * s.SW) and not (sl[1] > w0 and sl[0] < w1)
              for sl in (s.prong_slot(ac) for ac in s.prong_spots("door side")))
peg = (ds ^ s.box(-s.BIG, s.BIG, -s.BIG, s.BIG, s.ZWT + 0.01, s.BIG)).bounding_box()
casings = [(mid_runs[0][0], mid_runs[1][1]), (mid_runs[2][0], mid_runs[3][1])] if len(mid_runs) == 4 else [(0, 0)]
peg_gap = min(max(c[0] - peg[4], peg[1] - c[1]) for c in casings)
recess_y = s.L / 2 - (ra + s.POCKET_CLR)
recess_gap = min(min(c[0] + recess_y, recess_y - c[1]) for c in casings)
report(sill_ok and near_lo >= 3 and near_hi >= 3 and slot_ok and peg_gap >= 3 and recess_gap >= 3,
       f"under the doorway the floor has {len(under)} cut, the sill post's notch, y {sill[0]:.3f}..{sill[1]:.3f} (the "
       f"door framing and 0.2 round it); the nearest other cuts are {near_lo:.2f} mm off it toward the roll-up end "
       f"and {near_hi:.2f} toward the back; none of the door side's {len(s.prong_spots('door side'))} prongs "
       f"is under either opening; the mid-length roof peg (y {peg[1]:.2f}..{peg[4]:.2f}) is {peg_gap:.2f} mm from the "
       f"nearer casing and the corner recesses {recess_gap:.2f} mm from the nearer one")
covers = []
for (sx, sy), a in angles.items():
    at = a.transform(to_corner(sx, sy)).slice(40.0)
    covers += [-(at ^ square(-s.POCKET_D, 1, -30, 1)).bounds()[1], -(at ^ square(-30, 1, -s.POCKET_D, 1)).bounds()[0]]
report(all(abs(c * inch - 4.25) < 0.01 for c in covers),
       f"corner angles cover {min(covers) * inch:.2f} to {max(covers) * inch:.2f} in of each face (F5: 4.25 in, "
       f"against a 3 1/2 in corner board)")
cent = sorted(((sk.bounding_box()[0] + sk.bounding_box()[3]) / 2) for sk in skids)
fromside = sorted({round((s.W / 2 - abs(c)) * inch, 3) for c in cent})
report(len(cent) == 4 and fromside == [8.0, 37.0],
       f"4 skids, centres {', '.join(f'{(s.W / 2 - abs(c)) * inch:.2f}' for c in cent)} in in from their sides "
       f"(shop skid table: 8 and 37 in)")
# every layout mark the generator keeps has its member on it: a full stud (probed low on the wall) or, on
# the door side, a cripple over the header or a stud over the window plate (probed just under the top
# plates) and under the rough sill (probed low). The roll-up's own marks frame nothing in its opening
# (the roll-up's framing, not this proof's). The counts are Alan's layout, written out, so a mark the
# generator wrongly calls inside or dropped shows here: 36 full studs (door side 12, plain side 17, back
# end 7, roll-up end 0) and the door side's 4 over and under its openings
STUDS_WANT = {"door side": 12, "plain side": 17, "back end": 7, "roll-up end": 0}
studs_ok, nstud, ninside, nroll = True, {n: 0 for n in WALLS}, 0, 0
for n in WALLS:
    axis = s.WALL_SIDE[n][0]
    zlow = s.ZF + 20 if n != "door side" else s.ZF + 15
    for a, kind, what, _ in s.mark_plan(n):
        if kind == "dropped" or (kind == "inside" and what == "roll-up"):
            nroll += kind == "inside"
            continue
        zs = [zlow] if kind == "stud" else [s.ZWT - s.PLATE_TOP - 1.0] + ([zlow] if what == "window" else [])
        for zprobe in zs:
            reg = s.wall_box(n, a - 3, a + 3, 0.5, 1.5, zprobe, zprobe + 0.2)
            pieces_ = [c.bounding_box() for c in (p[n] ^ reg).decompose()]
            mids = [((b[1] + b[4]) / 2 if axis == 0 else (b[0] + b[3]) / 2) for b in pieces_]
            hit = [m for m in mids if abs(m - a) < 0.6]
            studs_ok = studs_ok and len(hit) == 1 and abs(hit[0] - a) < 0.01 * s.S
        if kind == "stud":
            nstud[n] += 1
        else:
            ninside += 1
first = {n: s.wall_marks(n)[0] for n in WALLS}
report(studs_ok and nstud == STUDS_WANT and ninside == 4 and abs((first["door side"] + s.L / 2) * inch - 16) < 0.01
       and abs((first["roll-up end"] + s.W / 2) * inch - 16) < 0.01
       and abs((s.W / 2 - first["back end"]) * inch - 16) < 0.01,
       f"{sum(nstud.values())} full studs stand on the 16 in marks ({', '.join(f'{n} {c}' for n, c in nstud.items())}; "
       f"Alan's layout: {', '.join(f'{n} {c}' for n, c in STUDS_WANT.items())}) and the door side's {ninside} cripples "
       f"and window studs on theirs (4), measured from each wall's left end seen from outside (door side from -y, "
       f"roll-up end from -x, back end from +x; the plain side's from +y fall on the same marks); the roll-up's "
       f"{nroll} marks are in its opening")
tw = []
for n, reg in (("door side", s.box(s.W / 2 + 0.3, s.W / 2 + 0.5, s.WIN_Y1 - 1, s.WIN_Y1 + 5, s.ZF + 40, s.ZF + 40.2)),
               ("door side", s.box(s.W / 2 + 0.3, s.W / 2 + 0.5, s.DOOR_Y1 - 1, s.DOOR_Y1 + 5, s.ZF + 30, s.ZF + 30.2)),
               ("roll-up end", s.box(s.RU_W / 2 - 1, s.RU_W / 2 + 5, -s.L / 2 - 0.5, -s.L / 2 - 0.3,
                                     s.ZF + 30, s.ZF + 30.2))):
    bb = (p[n] ^ reg).bounding_box()
    tw.append(((bb[4] - bb[1]) if n == "door side" else (bb[3] - bb[0])) * inch)
gb = (p["back end"] ^ s.box(-1, 1, s.L / 2 + 0.3, s.L / 2 + 0.5, 50, 90)).bounding_box()
tw.append((gb[5] - gb[2]) * inch)
report(all(abs(t - 3.5) < 0.01 for t in tw),
       f"trim boards {', '.join(f'{t:.2f}' for t in tw)} in wide (window and door casings, roll-up casing, gable band; "
       f"shop: 3 1/2 in)")
# the roll-up door's own numbers, measured off the parts (spec_rollup.md L.12): the curtain's width, the slats'
# pitch off its grooves, the handle's width and place, the threshold's height over the floor top, and the dark slit
# between the slats' top and the head over the doorway
cb_ = cur.bounding_box()
cur_w_in = (cb_[3] - cb_[0]) * inch
gl = cur ^ s.ru_box(11.9, 12.1, s.RU_FACE - 0.2, s.RU_FACE - 0.1, s.ZF, s.MOUTH)
sl_runs = sorted((q.bounding_box()[2], q.bounding_box()[5]) for q in gl.decompose())
groove_c = [(a_[1] + b_[0]) / 2 for a_, b_ in zip(sl_runs, sl_runs[1:])]
pitch_in = np.diff(groove_c) * inch
hb = (cur_b ^ s.ru_box(-20, 20, (s.HDL_U1 + s.HDL_U2) / 2 - 0.1, (s.HDL_U1 + s.HDL_U2) / 2 + 0.1, 0, 20)).bounding_box()
hdl_w_in, hdl_xc = (hb[3] - hb[0]) * inch, (hb[0] + hb[3]) / 2
lipb = (ew ^ s.ru_box(-5, 5, s.WT - 0.3, s.WT - 0.1, s.ZF - 1, s.ZF + 3)).bounding_box()
lip_in = (lipb[5] - s.ZF) * inch
body_top = (cur ^ s.ru_box(-5, 5, s.RU_FACE - 1.2, s.RU_FACE - 1.0, s.ZF, s.MOUTH)).bounding_box()[5]
head_bot = (ew ^ s.ru_box(-5, 5, s.RU_FACE - 1.2, s.RU_FACE - 1.0, s.ZF + 10, s.ZWT)).bounding_box()[2]
slit_in = (head_bot - body_top) * inch
report(abs(cur_w_in - 95.15) < 0.01 and len(pitch_in) == s.SLATS - 3 and np.allclose(pitch_in, 2.25, atol=0.005)
       and abs(hdl_w_in - 16.0) < 0.01 and abs(hdl_xc) < 1e-6 and abs(hb[2] - s.RAIL_Z0) < 1e-6
       and abs(lip_in - THRESHOLD_IN) < 0.01 and abs(slit_in - 3.12) < 0.01,
       f"the roll-up door {cur_w_in:.2f} in wide (spec 95.15: the 96 in opening less 0.43 in each side), its slats "
       f"{pitch_in.mean():.2f} in apart (off the {len(pitch_in) + 1} closed grooves; shop 2 1/4 in), its handle {hdl_w_in:.2f} in "
       f"wide at the bottom middle ({hdl_xc:.3f} mm off, on the bottom rail at {(hb[2] - s.ZF) * inch:.2f} in up; spec 16 "
       f"in), the threshold {lip_in:.2f} in over the floor (open question 16: {THRESHOLD_IN}), the dark slit under the head {slit_in:.2f} in (spec "
       f"3.12)")
# the gable band's height (open question 7): probed at x 39 to 41, clear of the roll-up's casing and the
# corner recesses, in front of the siding, where the band is all that stands proud
bands = []
for n in ENDS:
    sy = s.WALL_SIDE[n][1]
    ya, yb = sorted([sy * (s.L / 2 + 0.3), sy * (s.L / 2 + 0.5)])
    gb = (p[n] ^ s.box(39, 41, ya, yb, s.ZWT - 10, s.ZWT + 10)).bounding_box()
    bands.append(((gb[5] - gb[2]) * inch, (s.ZWT - gb[5]) * inch))
report(all(abs(d - 3.5) < 0.01 and abs(t) < 0.01 for d, t in bands),
       f"gable bands {', '.join(f'{d:.2f}' for d, _ in bands)} in deep, their tops "
       f"{', '.join(f'{t:.2f}' for _, t in bands)} in under the top of the wall plates (roll-up end, back end; open "
       f"question 7's default: level with the plates, as on the shed models)")

print()
print("all checks passed" if fails == 0 else f"{fails} check(s) failed")
sys.exit(1 if fails else 0)
