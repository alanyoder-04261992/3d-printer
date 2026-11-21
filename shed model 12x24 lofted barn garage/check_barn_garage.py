"""Checks the 12x24 Lofted Barn Garage model fits together and prints before anything is printed.

Run:  python check_barn_garage.py
Each line says what it proved, with the numbers it measured. Anything that fails is marked FAIL,
and the script then exits 1. The groups are in the four new models' order: 1 pieces and bed,
2 snap joints, 3 walls print, 4 corners, 5 gables and vents, 6 roll-up and lofts, 7 door, 8 roof,
9 skids, 10 plates, 11 fit test, 12 sizes at full size against the shop numbers.

The roll-up's lift-out curtain (lift-out addendum, Nov 3 2026) is checked in group 6 on (u, z) sections of the real
parts at 141 stations along the doorway (the curtain moves only in u and z, so each section is exact for its x), as
drawn, as printed (each part cut into its print layers and grown in the bed plane: the wall 0.1 a side, holes print
small, the curtain 0.05; and one more station in every interval between the printed layers' corners round the jamb
stops, about 190 in all) and at four other print growths; and in 3D where a section can't say (the printed seats,
the sideways hold). The roll-up door is the same part, with the same proofs, as the 12x24 Garage's (reconciled Nov 4
2026). It takes about 12 minutes on a busy machine.
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
from shapely.geometry import Polygon, LineString, box as sbox
from shapely.ops import unary_union

import make_barn_garage as s

M = m3.Manifold

BED = 220.0
fails = 0

# Alan's standard layout (the addendum of Nov 3 2026, from designer-standards.js on yoder-storage-barns.com,
# his copy-this-build codes), typed in from it in the model's mm, NOT read from the generator: the walk door
# on the door side at the roll-up end, its edge 4 ft in from the corner (centre 6.5 ft from the middle), and
# the window centred between the walk door and the back (3.5 ft from the middle)
STD_DOOR_YC, STD_DOOR = -55.033, (-67.733, -42.333)
STD_WIN_YC = 29.633


def report(ok, words):
    global fails
    fails += 0 if ok else 1
    print(("ok   " if ok else "FAIL ") + words)


def group(title):
    print()
    print("== " + title)


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
    """The part of a piece inside region (garage coords), where it lies in the piece's print."""
    R = np.column_stack([np.array(mat, dtype=float), np.zeros(3)])
    bb = piece.transform(R).bounding_box()
    return (piece ^ region).transform(R).translate([-bb[0], -bb[1], -bb[2]])


def floating(piece):
    """Layer by layer as the slicer lays a piece down (as_printed: anything thinner than a line
    dropped), the worst area with nothing under it within 45 degrees."""
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


def overhangs(cs, prev, step=0.2, reach=0.22, limit=20):
    """What of this layer hangs past the layer under it by more than 45 degrees and isn't a
    bridge held at both ends of limit (20) mm or less. Returns (left over section, longest bridge in
    mm: the longest straight line held at both ends, in any of four directions)."""
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
                if left and right and x1 - x0 <= limit:
                    rects.append([(x0, y - step / 2), (x1, y - step / 2), (x1, y + step / 2), (x0, y + step / 2)])
                    longest = max(longest, x1 - x0)
        if rects:
            bridged.append(m3.CrossSection(rects, m3.FillRule.Positive).rotate(-ang))
    if bridged:
        free = free - m3.CrossSection.batch_boolean(bridged, m3.OpType.Add).offset(0.05, RND)
    return free, longest


def worst_overhang(piece):
    """Layer by layer, the worst area that hangs out more than 45 degrees and isn't a bridge
    held at both ends of 20 mm or less. Returns (worst mm2, longest bridge mm)."""
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


def bridge_needed(piece):
    """worst_overhang(), and also the longest bridge the print really needs: on each layer the
    shortest limit that leaves no more hanging than 20 mm does. The longest line held at both ends
    is often a diagonal across a bay that is bridged straight across in far less. Returns (worst
    mm2, longest line held at both ends mm, longest bridge needed mm)."""
    bb = piece.bounding_box()
    worst, longest, prev, z_prev, found = 0.0, 0.0, None, 0.0, []
    for z0, z1 in layers(bb[5]):
        zm = (z0 + z1) / 2
        cs = piece.slice(zm)
        if prev is not None:
            reach = 1.1 * (zm - z_prev)
            left, span = overhangs(cs, prev, reach=reach)
            longest, worst = max(longest, span), max(worst, left.area())
            if span > 0:
                found.append((span, left.area(), cs, prev, reach))
        prev, z_prev = cs, zm
    need = 0.0
    for span, a20, cs, pv, reach in sorted(found, key=lambda f: -f[0]):
        if span <= need:
            break
        if overhangs(cs, pv, reach=reach, limit=need)[0].area() <= a20 + 0.01:
            continue
        lo, hi = need, span
        while hi - lo > 0.05:
            mid = (lo + hi) / 2
            if overhangs(cs, pv, reach=reach, limit=mid)[0].area() <= a20 + 0.01:
                hi = mid
            else:
                lo = mid
        need = hi
    return worst, longest, need


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


def sweep(piece, others, path):
    """The worst overlap of piece with others at each step of a path of moves."""
    return max(overlap(piece.translate(t), others) for t in path)


def runs(piece, region, axis):
    """The stretches of material of piece inside region along one axis (0 x, 1 y, 2 z):
    [(start, end)], from the pieces it falls into."""
    out = []
    for c in (piece ^ region).decompose():
        if c.volume() > 1e-6:
            bb = c.bounding_box()
            out.append((bb[axis], bb[axis + 3]))
    return sorted(out)


def u_of(name, v):
    """u (out from the inside face) of a garage coordinate v along the wall's normal."""
    axis, sign = s.WALL_SIDE[name]
    half = (s.W / 2, s.L / 2)[axis]
    return sign * v - (half - s.WT)


def u_range(name, man):
    bb = man.bounding_box()
    axis, sign = s.WALL_SIDE[name]
    a, b = u_of(name, bb[axis]), u_of(name, bb[axis + 3])
    return min(a, b), max(a, b)


# ------------------------------------------------------------------------ the lift-out curtain's motion
# The curtain only moves in (u, z) (out from the roll-up end's inside face, and up), so its motion is
# checked on (u, z) sections of the real parts at stations x along the wall, each exact for everything
# at its x. "As printed" sections: each part cut into its print layers (u up, 0.25 then 0.2 a layer) and
# grown in the bed plane (x and z): the wall by GW a side (holes print small), the curtain by GC; the floor
# and loft, which print upside down with u in their bed plane, grown GW in u and x.

U0_RU = s.L / 2 - s.WT
TO_UZ = np.array([[0, -1, 0, -U0_RU], [0, 0, 1, 0], [-1, 0, 0, 0]], dtype=float)   # garage -> (u, z, -x)
EMPTY = Polygon()


def sections(man, xs):
    """The (u, z) sections of a manifold at each x in xs, as shapely geometries."""
    m = man.transform(TO_UZ)
    out = {}
    for x in xs:
        g = EMPTY
        for loop in m.slice(-x).to_polygons():
            if len(loop) >= 3:
                g = g.symmetric_difference(Polygon(loop))
        out[x] = g if g.is_valid else g.buffer(0)
    return out


def ulayers(top):
    e = [0.0, 0.25]
    while e[-1] < top - 1e-9:
        e.append(round(e[-1] + 0.2, 6))
    return e


def layered(poly, grow):
    """A section as it prints: at each layer (u) the z-intervals at the layer's middle held over the layer,
    each grown by grow in z."""
    if poly.is_empty:
        return poly
    u0, z0, u1, z1 = poly.bounds
    e = ulayers(u1)
    out = []
    for a, b in zip(e[:-1], e[1:]):
        m = (a + b) / 2
        if m < u0 or m > u1:
            continue
        ln = LineString([(m, z0 - 1), (m, z1 + 1)]).intersection(poly)
        for sg in getattr(ln, "geoms", [ln]):
            if sg.is_empty or sg.geom_type != "LineString" or sg.length < 1e-6:
                continue
            zs = [c[1] for c in sg.coords]
            out.append(sbox(a, min(zs) - grow, b, max(zs) + grow))
    return unary_union(out) if out else EMPTY


def udilate(poly, g):
    if poly.is_empty or g <= 0:
        return poly
    return unary_union([shapely.affinity.translate(poly, -g, 0), poly, shapely.affinity.translate(poly, g, 0)])


def grown_sections(man, xs, g):
    """Sections at each x, unioned over x - g, x, x + g (the bed-plane growth along the wall)."""
    if g <= 0:
        return sections(man, xs)
    allx = sorted(set([x + d for x in xs for d in (-g, 0.0, g)]))
    sec = sections(man, allx)
    return {x: unary_union([sec[x - g], sec[x], sec[x + g]]) for x in xs}


def rot(deg, cu, cz):
    a = math.radians(deg)
    c, sn = math.cos(a), math.sin(a)
    return np.array([[c, -sn, cu - c * cu + sn * cz], [sn, c, cz - sn * cu - c * cz], [0, 0, 1.0]])


def shift(du, dz):
    return np.array([[1, 0, du], [0, 1, dz], [0, 0, 1.0]])


def pose_mat(pre=(0.0, 0.0), L=0.0, th=0.0, pu=None, pz=None, phi=0.0, du=0.0, dz=0.0):
    """seat pre, lift L, swing th (degrees, + = bottom out) about (pu, pz) (default the front of the curtain
    at the mouth, lifted), then a lean phi (degrees, + = top in) about its bottom-front corner, then a
    shift (du, dz)."""
    M = shift(pre[0], pre[1] + L)
    pu = s.RU_FACE if pu is None else pu
    pz = s.MOUTH + L + pre[1] if pz is None else pz
    if th:
        M = rot(th, pu, pz) @ M
    if phi:
        c = M @ np.array([s.BOT_U, s.ZF + s.G_BOT, 1.0])
        M = rot(phi, c[0], c[1]) @ M
    return shift(du, dz) @ M


def moved_secs(arr, M):
    return shapely.transform(arr, lambda c: c @ M[:2, :2].T + M[:2, 2])


class Case:
    """Sections of the curtain (rigid body and its springs) and of what it can meet, at the stations."""

    def __init__(self, label, cur, wall, others, xs, gw=0.0, gc=0.0, printed=False):
        self.label, self.xs, self.printed, self.gw, self.gc = label, list(xs), printed, gw, gc
        regs = s.curtain_regions()
        spring = s.union([b for v in regs.values() for b in v])
        pieces = {"rig": cur - spring}
        for k, key in (("finger strip", "fs"), ("finger bump", "fb"), ("tab plate", "tp"), ("tab bump", "tb")):
            pieces[key] = cur ^ s.union(regs[k])
        g_c, g_w = (gc, gw) if printed else (0.0, 0.0)
        self.c = {}
        for key, man in pieces.items():
            sec = grown_sections(man, self.xs, g_c)
            self.c[key] = np.array([layered(sec[x], g_c) if printed else sec[x] for x in self.xs], dtype=object)
        wsec = grown_sections(wall, self.xs, g_w)
        reach = sbox(-4, -3, 32, s.MOUTH + s.REB_H + 3.5)          # all the curtain can reach (it stays under 65.1)
        self.wall = np.array([(layered(wsec[x], g_w) if printed else wsec[x]).intersection(reach) for x in self.xs],
                             dtype=object)
        reb = sbox(-0.5, s.PAD_Z - 0.6, s.REB_U - 0.001, 400)          # each pad and the head over it
        self.pads = np.array([w.intersection(reb) if s.PAD_X0 - g_w - 0.02 <= abs(x) <= s.PAD_X1 + g_w + 0.02 else EMPTY
                              for x, w in zip(self.xs, self.wall)], dtype=object)
        self.other = {}
        for name, man, kind in others:
            sec = grown_sections(man, self.xs, g_w if kind == "bed" else 0.0)
            self.other[name] = np.array([(udilate(sec[x], g_w) if kind == "bed" else sec[x]).intersection(reach)
                                         for x in self.xs], dtype=object)
        self.obst = np.array([unary_union([self.wall[i]] + [o[i] for o in self.other.values()]) for i in range(len(self.xs))],
                             dtype=object)
        self.nopad = np.array([o.difference(p) if not p.is_empty else o for o, p in zip(self.obst, self.pads)], dtype=object)
        self.side = np.array([1 if x > 0 else -1 for x in self.xs])
        shapely.prepare(self.obst)

    def _idx(self):
        if not hasattr(self, "ix"):
            self.ix = {k: np.nonzero(~shapely.is_empty(self.c[k]))[0] for k in ("fb", "tb", "fs", "tp")}
            self.pad_bot = {i: self.pads[i].bounds[1] if not self.pads[i].is_empty else np.inf for i in range(len(self.xs))}
            reb = sbox(-0.5, s.PAD_Z - 0.6, s.REB_U - 0.001, s.MOUTH + s.REB_H - 0.001)
            self.pad_u = {i: self.pads[i].intersection(reb).bounds[0:3:2] if not self.pads[i].is_empty else (0, 0)
                          for i in range(len(self.xs))}
            self.fb_top = {i: self.c["fb"][i].bounds for i in self.ix["fb"]}
        return self.ix

    def _touch(self, arr, idx, M):
        """The worst overlap of arr[idx], moved by M, with what it can meet."""
        if not len(idx):
            return 0.0
        m = moved_secs(arr[idx], M)
        hit = shapely.intersects(self.obst[idx], m)
        return float(np.max(shapely.area(shapely.intersection(m[hit], self.obst[idx][hit])))) if hit.any() else 0.0

    def ev(self, gaps=False, **pose):
        """At a pose: rigid overlap (worst station, mm2), least rigid gap, the most finger bend (z) and tab bend
        (u), the finger bumps' least u overlap with their pads (fpad: the bump's top edge under the pad's bottom
        face; fpa: how far bump and pad cross at all), a tab bump's most overlap with the wall (mm2),
        the springs' strips and bumps touching anything once each is moved by its side's own bend (mm2), and the
        highest z of any of the curtain."""
        ix = self._idx()
        M = pose_mat(**pose)
        r = moved_secs(self.c["rig"], M)
        hit = shapely.intersects(self.obst, r)
        ov = float(np.max(shapely.area(shapely.intersection(r[hit], self.obst[hit])))) if hit.any() else 0.0
        out = {"ov": ov}
        if gaps:
            d = shapely.distance(r, self.obst)
            out["gap"] = float(np.nanmin(np.where(np.isfinite(d), d, np.nan)))
        fbend, tbend = {1: 0.0, -1: 0.0}, {1: 0.0, -1: 0.0}
        fpad, tb_ov, fpa = [], 0.0, []
        i_fb = ix["fb"]
        if len(i_fb):
            fb = moved_secs(self.c["fb"][i_fb], M)
            ip = shapely.intersection(fb, self.pads[i_fb])
            ar = shapely.area(ip)
            fbb, ipb = shapely.bounds(fb), shapely.bounds(ip)
            for j, i in enumerate(i_fb):
                if ar[j] > 1e-7:
                    fbend[self.side[i]] = max(fbend[self.side[i]], fbb[j, 3] - self.pad_bot[i])
                if self.pads[i].is_empty:          # the bump runs on past its pad (pads 16.0..16.7, the bump to 17.6)
                    continue
                # how far the bump's top edge is under its pad, in u (it meets the pad's bottom face there)
                u0b, _, u1b, ztb = self.fb_top[i]
                ua = (M @ np.array([u0b, ztb, 1.0]))[0]
                ub = (M @ np.array([u1b, ztb, 1.0]))[0]
                pu0, pu1 = self.pad_u[i]
                fpad.append(max(0.0, min(max(ua, ub), pu1) - max(min(ua, ub), pu0)))
                fpa.append(ipb[j, 2] - ipb[j, 0] if ar[j] > 1e-7 else 0.0)   # how far the bump and pad cross, in u
        i_tb = ix["tb"]
        tbm = None
        if len(i_tb):
            tbm = moved_secs(self.c["tb"][i_tb], M)
            it = shapely.intersection(tbm, self.wall[i_tb])
            ar = shapely.area(it)
            itb = shapely.bounds(it)
            for j, i in enumerate(i_tb):
                if ar[j] > 1e-7:
                    tb_ov = max(tb_ov, ar[j])
                    tbend[self.side[i]] = max(tbend[self.side[i]], itb[j, 2] - itb[j, 0])
        strip = 0.0
        for sg in (1, -1):
            Mf, Mt = shift(0, -fbend[sg]) @ M, shift(-tbend[sg], 0) @ M
            for key, Mk in (("fs", Mf), ("fb", Mf), ("tp", Mt), ("tb", Mt)):
                idx = ix[key][self.side[ix[key]] == sg]
                strip = max(strip, self._touch(self.c[key], idx, Mk))
        zt = [np.nanmax(shapely.bounds(r)[:, 3])]
        if len(i_fb):
            zt.append(np.nanmax(fbb[:, 3]))
        if tbm is not None:
            zt.append(np.nanmax(shapely.bounds(tbm)[:, 3]))
        out.update(fpa=min(fpa) if fpa else 0.0, fbend=max(fbend.values()), tbend=max(tbend.values()),
                   fpad=min(fpad) if fpad else 0.0,
                   tb_ov=tb_ov, strip=strip, ztop=float(max(zt)))
        return out

    def ov(self, **pose):
        r = moved_secs(self.c["rig"], pose_mat(**pose))
        hit = shapely.intersects(self.obst, r)
        if not hit.any():
            return 0.0
        return float(np.max(shapely.area(shapely.intersection(r[hit], self.obst[hit]))))

    def named_gaps(self, poses, names):
        """The least gap from the rigid curtain to each named obstacle over the poses: names {name: fn(i, x) ->
        geometry or None}."""
        best = {}
        geo = {n: np.array([fn(i, x) or EMPTY for i, x in enumerate(self.xs)], dtype=object) for n, fn in names.items()}
        for p in poses:
            r = moved_secs(self.c["rig"], pose_mat(**p))
            for n, arr in geo.items():
                ok = ~shapely.is_empty(arr) & ~shapely.is_empty(r)
                if ok.any():
                    d = shapely.distance(r[ok], arr[ok])
                    best[n] = min(best.get(n, 99.0), float(np.min(d)))
        return best

    def unbent_bump_gap(self, poses, arr):
        best = 99.0
        for p in poses:
            b = moved_secs(self.c["fb"], pose_mat(**p))
            ok = ~shapely.is_empty(b) & ~shapely.is_empty(arr)
            if ok.any():
                best = min(best, float(np.min(shapely.distance(b[ok], arr[ok]))))
        return best


# ---- searches on a Case (the addendum's motions)
def settle_seat(cs, reach=0.8, step=0.025):
    """Where the springs push it: down (fingers, weight) and in (tabs), no rigid overlap, du + dz least, over
    du and dz each from -reach to +reach."""
    best = None
    n = int(round(reach / step))
    for i in range(-n, n + 1):
        du = i * step
        if cs.ov(pre=(du, reach)) > 1e-5:
            continue
        lo, hi = -n, n                              # feasible is upward closed in dz over this range
        if cs.ov(pre=(du, -reach)) < 1e-5:
            hi = -n
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if cs.ov(pre=(du, mid * step)) < 1e-5:
                hi = mid
            else:
                lo = mid
        sc = du + hi * step
        if best is None or sc < best[0] - 1e-9:
            best = (sc, du, hi * step)
    return (best[1], best[2]) if best else None


def rigid_stop(cs, pre, step=0.025):
    L = 0.0
    while cs.ov(pre=pre, L=L + step) < 1e-4 and L < 3:
        L += step
    return round(L, 3)


def removal_poses(lift, th, pre, n=10, pu=None, pz=None, du0=0.0):
    """H.3: lift, (slide du0), swing th about (pu, pz) (default the front at the mouth), drop TONGUE_UP +
    BUMP_H + lift + 0.6, out 15."""
    pz = s.MOUTH + lift + pre[1] if pz is None else pz
    pu = s.RU_FACE if pu is None else pu
    drop = s.TONGUE_UP + s.BUMP_H + lift + 0.6
    ps = [dict(pre=pre, L=lift * k / n) for k in range(1, n + 1)]
    ps += [dict(pre=pre, L=lift, du=du0 * k / n) for k in range(1, n + 1)] if du0 else []
    ps += [dict(pre=pre, L=lift, th=th * k / n, pu=pu, pz=pz, du=du0) for k in range(1, n + 1)]
    ps += [dict(pre=pre, L=lift, th=th, pu=pu, pz=pz, du=du0, dz=-drop * k / n) for k in range(1, n + 1)]
    ps += [dict(pre=pre, L=lift, th=th, pu=pu, pz=pz, du=du0 + 15 * k / n, dz=-drop) for k in range(1, n + 1)]
    return ps


def path_worst(cs, poses):
    w = {"ov": 0.0, "fbend": 0.0, "tbend": 0.0, "strip": 0.0, "ztop": -99.0}
    for p in poses:
        e = cs.ev(**p)
        for k in w:
            w[k] = max(w[k], e[k])
    return w


def path_clear(cs, poses):
    for p in poses:
        if cs.ov(**p) > 1e-4:
            return False
    return True


def least_lift(cs, pre, stop, th=7.0):
    for k in range(2, 61):
        l = round(k * 0.05, 3)
        if l > stop + 1e-9:
            return None
        if path_clear(cs, removal_poses(l, th, pre)):
            return l
    return None


MOTIONS = {
    "tongue top held": lambda l, pre: dict(pu=0.5 + pre[0], pz=s.Z_TT + l + pre[1], du0=0.0),
    "slid out to the rebate front, pivot on its lip": lambda l, pre: dict(pu=s.REB_U, pz=s.MOUTH,
                                                                          du0=s.REB_U - 0.05 - s.TONGUE_T - pre[0]),
    "mid-depth pivot": lambda l, pre: dict(pu=2.5, pz=s.MOUTH + l + pre[1], du0=0.0),
}


def first_contact(cs, pre, l, pu, pz, du0=0.0, tmax=12.0, step=0.5):
    t = step
    while t <= tmax + 1e-9:
        if cs.ov(pre=pre, L=l, th=t, pu=pu, pz=pz, du=du0) > 1e-4:
            return t
        t += step
    return None


def motion_ok(cs, pre, l, name, swings=(4, 5, 6, 7, 8, 9, 10, 11)):
    """(first contact degrees, the least swing under it that lets it out, or None)."""
    m = MOTIONS[name](l, pre)
    if m["du0"] and cs.ov(pre=pre, L=l, du=m["du0"]) > 1e-4:
        return None, None
    tc = first_contact(cs, pre, l, m["pu"], m["pz"], m["du0"]) or 12.5
    for th in swings:
        if th >= tc:
            break
        if path_clear(cs, removal_poses(l, th, pre, n=8, pu=m["pu"], pz=m["pz"], du0=m["du0"])):
            return tc, th
    return tc, None


def zmove_tab_rise(cs, poses, start=None):
    """Along a move in z, how much a tab bump's overlap with the wall grows from one step to the next (mm2):
    a bump can only be loaded by a move in u (both parts print as stairs: met in z by a flat face it cannot
    bend), so any growth here means a bump is pushed in z."""
    seq = ([start] if start else []) + list(poses)
    a = [cs.ev(**q)["tb_ov"] for q in seq]
    return max([0.0] + [b - c for c, b in zip(a, a[1:])])


def tongue_back_u(pre, th, phi):
    """Where the tongue's back (u 0) is at the mouth's height after the insertion's swing and lean."""
    M = pose_mat(pre=pre, th=th, pz=s.MOUTH + pre[1], phi=phi)
    a, b = M @ np.array([0.0, s.MOUTH - 3, 1]), M @ np.array([0.0, s.MOUTH + 3, 1])
    return a[0] + (b[0] - a[0]) * (s.MOUTH - a[1]) / (b[1] - a[1])


def finger_u_push(cs, M):
    """At pose M, how far (in u) any finger bump or strip reaches into a pad that it meets from behind, wholly above the
    pad's bottom: a push in u, which bends the finger back toward the room (0 if none)."""
    ix = cs._idx()
    i_p = np.array([i for i in sorted(set(ix["fb"]) | set(ix["fs"])) if not cs.pads[i].is_empty], dtype=int)
    if not len(i_p):
        return 0.0
    pad_bot = np.array([cs.pad_bot[i] for i in i_p])
    most = 0.0
    for key in ("fb", "fs"):
        inter = shapely.intersection(moved_secs(cs.c[key][i_p], M), cs.pads[i_p])
        on = shapely.area(inter) > 1e-7
        if on.any():
            ib = shapely.bounds(inter)
            behind = on & (ib[:, 1] > pad_bot + 0.01)
            if behind.any():
                most = max(most, float((ib[behind, 2] - ib[behind, 0]).max()))
    return most


def insertion(cs, pre, th, phi, lifts, need=None):
    """H.5: held swung th about the front at the mouth and leaned phi more about the bottom-front corner,
    below the head (the tongue and bumps under the mouth), moved in; pushed straight up until it stops (no
    tab bump may touch the wall while it rises; where one first does is its catch); then for each lift in lifts
    (or lifts(top)): let down to it, the top let out and the bottom swung in one after the other, and together,
    then let go to the seat. Leaned in too far (the finger bumps under their pads by less than 0.2 at the top),
    step 4 as the read me says: let down about a millimetre (not under need), the top let out and the bottom
    pushed in; does something rigid stop the top coming out, or does the top come out pushing the finger bumps
    back from behind their pads (a push in u, which the fingers, thin that way, give to)? Returns a dict."""
    pz = s.MOUTH + pre[1]
    drop = s.TONGUE_UP + s.BUMP_H + 0.6
    res = {"blocked_in": 0.0, "tb_rise": 0.0, "catch": None, "lean": tongue_back_u(pre, th, phi)}
    for k in range(11):
        e = cs.ev(pre=pre, th=th, pz=pz, phi=phi, du=15 * (1 - k / 10), dz=-drop)
        res["blocked_in"] = max(res["blocked_in"], e["ov"])
        res["tb_rise"] = max(res["tb_rise"], e["tb_ov"])
    if res["blocked_in"] > 1e-4:
        res["result"] = "blocked coming in"
        return res
    dz = -drop
    for stepz in (0.2, 0.05, 0.02):
        while dz < 4.0:
            e = cs.ev(pre=pre, th=th, pz=pz, phi=phi, dz=dz + stepz)
            if e["ov"] > 1e-4:
                break
            if e["tb_ov"] > 1e-6 and res["catch"] is None:
                c_ = (dz + stepz, e["fbend"])          # where a tab bump first meets the head (to 0.02), the fingers' bend
                for k in range(1, 11):
                    ek = cs.ev(pre=pre, th=th, pz=pz, phi=phi, dz=dz + stepz - 0.2 + 0.02 * k)
                    if ek["tb_ov"] > 1e-6:
                        c_ = (dz + stepz - 0.2 + 0.02 * k, ek["fbend"])
                        break
                res["catch"] = c_
            res["tb_rise"] = max(res["tb_rise"], e["tb_ov"])
            dz += stepz
    top = cs.ev(pre=pre, th=th, pz=pz, phi=phi, dz=dz)
    res.update(top=dz, fpad=top["fpad"], fpa=top["fpa"], fbend_top=top["fbend"], ztop=top["ztop"])
    if res["tb_rise"] > 1e-6:
        res["result"] = "catches"
        return res
    if top["fpad"] < 0.2:
        L = round(dz - 1.0, 3) if need is None else max(round(dz - 1.0, 3), need)
        seq = [("z", [dict(th=th, phi=phi, dz=dz + (L - dz) * k / 8) for k in range(1, 9)]),
               ("turn", [dict(th=th, phi=phi * (1 - k / 8), dz=L) for k in range(1, 9)]),
               ("turn", [dict(th=th * (1 - k / 10), phi=0.0, dz=L) for k in range(1, 11)])]
        ub = 0.0
        for kind, qs in seq:
            for q in qs:
                if cs.ov(pre=pre, pz=pz, **q) > 1e-4:
                    res.update(result="leaned too far: the top won't come out", u_bend=ub)
                    return res
                if kind == "turn":
                    ub = max(ub, finger_u_push(cs, pose_mat(pre=pre, pz=pz, **q)))
        res.update(result="leaned too far: its springs go in behind their pads" if ub > 0 else
                   "leaned too far: a finger bump is not under its pad", u_bend=ub)
        return res
    rows = []
    for L in (lifts(dz) if callable(lifts) else lifts):
        down = [dict(th=th, phi=phi, dz=dz + (L - dz) * k / 8) for k in range(1, 9)]
        lower = [dict(dz=L * (1 - k / 10)) for k in range(1, 11)]
        seqs = {"one after the other": [down, [dict(th=th, phi=phi * (1 - k / 8), dz=L) for k in range(1, 9)],
                                        [dict(th=th * (1 - k / 10), phi=0.0, dz=L) for k in range(1, 11)], lower],
                "together": [down, [dict(th=th * (1 - k / 14), phi=phi * (1 - k / 14), dz=L) for k in range(1, 15)], lower]}
        for nm, segs in seqs.items():
            full = [dict(pre=pre, pz=pz, **q) for seg in segs for q in seg]
            w = path_worst(cs, full)
            start = dict(pre=pre, pz=pz, th=th, phi=phi, dz=dz)
            w["tz"] = zmove_tab_rise(cs, [dict(pre=pre, pz=pz, **q) for q in down], start)
            w["tz"] = max(w["tz"], zmove_tab_rise(cs, [dict(pre=pre, pz=pz, **q) for q in lower],
                                                  dict(pre=pre, pz=pz, **segs[-2][-1])))
            rows.append((L, nm, w))
    res["rows"] = rows
    res["result"] = "works" if all(w["ov"] < 1e-4 for _, _, w in rows) else "blocked going in"
    return res


p = s.build()
body, upper, lower, door = p["body"], p["upper"], p["lower"], p["door"]
WALLS = list(s.WALL_CUTS)
LONGS, ENDS = ["plain side", "door side"], ["roll-up end", "back end"]
zone = s.trim_zone()
flat = {name: s.to_print(s.WALL_TO_PRINT[name], s.two_colour(p[name], zone)) for name in WALLS}
up_flat = s.panel_to_print(upper, s.UPPER_A, s.UPPER_B)
lo_flat = s.panel_to_print(lower, s.LOWER_A, s.LOWER_B)
loft_flat = s.to_print(s.LOFT_TO_PRINT, [p["loft"]])[0]
fl = p["floor"]
door_shut = door.transform(s.door_to_shed(0))
lofts = [s.loft(1), s.loft(-1)]
loft_set = s.union(lofts)
longs = s.union([p[n] for n in LONGS])
walls_all = s.union([p[n] for n in WALLS])
skids_placed = s.placed_skids()
angle_flat = s.corner_prints()
ct = s.corner_test({n: p[n] for n in WALLS}, fl)
ct_parts = s.corner_test_parts({n: p[n] for n in WALLS}, fl)
dt_parts = s.door_test_parts()
cu_parts = s.curtain_test_parts({n: p[n] for n in WALLS})
ru = "roll-up end"
cur_flat = s.union(list(s.curtain_print(p)))
spring_boxes = s.curtain_regions()
bumps = s.union(spring_boxes["finger bump"] + spring_boxes["tab bump"])

# ======================================================================== 1
group("1 pieces and bed")
for name, part, expect in ([("floor", fl, 1)] + [(n, s.union(flat[n]), 1) for n in WALLS] +
                           [("upper roof", up_flat, 1), ("lower roof", lo_flat, 1), ("loft", loft_flat, 1),
                            ("steel door", s.on_bed(door), 1), ("inner skid", s.skid(), 1),
                            ("outer skid", s.outer_skid(), 1), ("skids.stl", p["skids"], 4)] +
                           [("corner angle, " + n, m, 1) for n, m in angle_flat] +
                           [("roll-up curtain", cur_flat, 1)] +
                           [("fit test " + n, m, 1) for n, m in ct_parts + dt_parts + cu_parts] +
                           [("fit test.stl", p["fit"], 11)]):
    bb = part.bounding_box()
    size = (bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2])
    pieces = len(part.decompose())
    report(pieces == expect and max(size[0], size[1]) <= BED and size[2] <= BED,
           f"{name}: {pieces} solid piece(s) (expected {expect}), {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm, "
           f"fits the {BED:.0f} mm bed")
pieces = [fl] + [p[n] for n in WALLS]
v = abs(body.volume() - sum(x.volume() for x in pieces))
worst = max(overlap(a, b) for i, a in enumerate(pieces) for b in pieces[i + 1:])
report(v < 0.01 and worst < 0.001, f"the floor and four walls add up to the whole body ({v:.4f} mm3 left over) and no "
                                   f"two of them overlap ({worst:.4f} mm3; the roll-up's jamb stops start on the floor top)")
v_nb, v_b = overlap(p["curtain"] - bumps, body), overlap(p["curtain"], body)
report(v_nb < 0.001 and v_b > 0.5,
       f"the roll-up curtain seated as drawn, its four spring bumps taken out, overlaps nothing of the body ({v_nb:.5f} mm3); "
       f"with them in it overlaps by {v_b:.2f} mm3, the springs' preload (proved in group 6)")
v = max(overlap(fl.translate([dx, dy, 0]), walls_all) for dx, dy in ((0.14, 0), (-0.14, 0), (0, 0.14), (0, -0.14)))
report(v < 0.0001, f"the walls sit round the floor with {s.FIT} mm round every post and prong and {s.FLOOR_CLR} mm "
                   f"inside the skirts (the floor moved 0.14 mm any way still clears them: {v:.4f} mm3)")
# the .stl files as written (32-bit corners): no collapsed triangle, every edge shared by an even number of triangles
STLS = ["floor.stl", "door side.stl", "plain side.stl", "roll-up end.stl", "back end.stl", "upper roof.stl",
        "lower roof.stl", "loft.stl", "door.stl", "skids.stl", "fit test.stl", "corner angle.stl", "roll-up curtain.stl"]
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


# each .stl holds the very part it is written from (final audit, Nov 4 2026: simplify() before writing had cut wedges
# out of 12 of the door side's studs and its steel door's head casing, 293 mm3, and 26 mm3 out of the plain side's
# studs, with no open edge to show it): its triangles as written summed to a volume, and cut at the middle of every
# print layer, against the part; and each lies inside the bed as one object, its lowest corner on it, the way the read
# me offers it (the 12x24 Garage's corner angle.stl had been 313 mm long)
STL_FROM = s.stl_parts(p)
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
group("2 snap joints")


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


# the floor with room for the barbs to pass, as if each leg were bent out of the way: what is
# left in the way of a wall coming down is only the snap itself
barb_room = []
for n in WALLS:
    for ac in s.prong_spots(n):
        (a0, a1), _ = s.prong_spans(ac)
        barb_room.append(s.wall_box(n, a0 - s.FIT, a1 + s.FIT, -s.FIT, s.BARB, -1, s.ZF + 1))
fl_open = fl - s.union(barb_room)
DROPS = [0.1 * k for k in range(1, 11)] + [1 + 0.5 * k for k in range(1, 279)]   # every 0.5 mm to 140 mm
n_barbs = 0
for n in LONGS + ENDS:
    w = p[n]
    n_barbs += len(s.prong_spots(n))
    v = overlap(w.translate([0, 0, -0.1]), fl)
    vh = overlap(w.translate([0, 0, 0.3]), fl)
    vi, vo = overlap(w.translate(toward(n, -0.3)), fl), overlap(w.translate(toward(n, 0.3)), fl)
    va = min(overlap(w.translate(along(n, d)), fl) for d in (0.3, -0.3))
    report(v > 1 and vh > 0.05 and min(vi, vo, va) > 0.05,
           f"{n} stands on the floor (lowered 0.1 mm: {v:.1f} mm3), its {len(s.prong_spots(n))} barbs hold it down (lifted "
           f"0.3 mm they meet their ledges: {vh:.2f} mm3), and the floor holds its foot in ({vi:.1f}), out ({vo:.1f}) "
           f"and along ({va:.1f} mm3 moved 0.3 mm)")
    # lowered on in the read me's order: the plain side onto the bare floor, the door side with its
    # door hung and shut, then (after the lofts) the end walls past the lofts, the long walls'
    # mitres and the door
    if n == "plain side":
        moving, others, what = w, fl_open, "onto the bare floor"
    elif n == "door side":
        moving, others, what = w + door_shut, s.union([fl_open, p["plain side"]]), "with its door hung and shut"
    else:
        moving, others = w, s.union([fl_open, longs, loft_set, door_shut])
        what = "past the lofts, the long walls' mitres and the door"
    worst = sweep(moving, others, [[0, 0, dz] for dz in DROPS])
    report(worst < 0.001, f"{n} goes on straight down from 140 mm up {what}, nothing in the way but the barbs "
                          f"({worst:.4f} mm3)")
report(n_barbs == 12, f"{n_barbs} barbs in all (4 on each long wall, 2 on each end wall)")
leg = s.LEG_ROOT - (s.LEDGE_Z - s.FIT)
strain = 1.5 * s.PRONG_T * s.CATCH / leg ** 2
room = s.SLOT_U - (s.BARB + s.PRONG_T + s.CATCH)
report(strain < 0.02 and room >= s.FIT - 0.001,
       f"each prong leg bends {s.CATCH:.2f} mm to let its barb through: {strain * 100:.1f}% strain on a {leg:.2f} mm leg "
       f"{s.PRONG_T} mm thick (PLA takes about 2%), with {room:.2f} mm to spare in its slot")
# every leg free to LEG_ROOT: the leg's length above is only true if nothing fills the relief round
# its top (the reliefs are cut last, after the roll-up's stops, lip and post extensions are added)
for n in WALLS:
    worst_free, legs_ok = 0.0, True
    for ac in s.prong_spots(n):
        (a0, a1), _ = s.prong_spans(ac)
        legb = s.wall_box(n, a0, a1, s.BARB, s.BARB + s.PRONG_T, s.ZF - 0.5 + 0.01, s.LEG_ROOT - 0.01)
        ring = s.wall_box(n, a0 - 0.15, a1 + 0.15, s.BARB - 0.15, s.BARB + s.PRONG_T + 0.15,
                          s.ZF - 0.5 + 0.01, s.LEG_ROOT - 0.01) - legb
        worst_free = max(worst_free, overlap(p[n], ring))
        legs_ok &= abs(overlap(p[n], legb) - legb.volume()) < 1e-3
    report(worst_free < 1e-4 and legs_ok,
           f"{n}: each of its {len(s.prong_spots(n))} legs is there and free to LEG_ROOT: nothing within 0.15 mm of its "
           f"four faces from {s.ZF - 0.5:.2f} to {s.LEG_ROOT:.2f} ({worst_free:.6f} mm3)")
# the same snap as it will print: walls lying inside face down and the floor upside down, in
# 0.25/0.2 mm layers, with anything thinner than a line rounded off (as_printed)
for n in WALLS:
    region = s.union([s.wall_box(n, min(s.prong_spans(ac)[0][0], s.prong_spans(ac)[1][0]) - 1,
                                 max(s.prong_spans(ac)[0][1], s.prong_spans(ac)[1][1]) + 1, -1, s.SD, -1, s.ZF + 1)
                      for ac in s.prong_spots(n)])
    pw = printed_in_shed(p[n], s.WALL_TO_PRINT[n], region)
    pf = printed_in_shed(fl, s.FLOOR_TO_PRINT, region)
    rest = overlap(pw, pf)
    held = overlap(pw.translate([0, 0, 0.3]), pf)
    catches = []
    for ac in s.prong_spots(n):
        (a0, a1), _ = s.prong_spans(ac)
        zc = s.LEDGE_Z - s.FIT
        barb = pw ^ s.wall_box(n, a0 + 0.5, a1 - 0.5, -1, s.BARB - 0.05, zc - 0.15, zc - 0.05)
        wall_in = pf ^ s.wall_box(n, a0 + 0.5, a1 - 0.5, -0.5, s.BARB + 0.5, s.LEDGE_Z + 0.4, s.LEDGE_Z + 0.6)
        catch = u_range(n, wall_in)[1] - u_range(n, barb)[0]
        top = (pw ^ s.wall_box(n, a0 + 0.5, a1 - 0.5, -1, s.BARB - s.FIT - 0.05, -1, s.ZF - 1)).bounding_box()[5]
        ledge = (pf ^ s.wall_box(n, a0 + 0.5, a1 - 0.5, 0.05, s.BARB - s.FIT - 0.05, -1, s.ZF)).bounding_box()[2]
        catches.append((catch, ledge - top))
    play = s.SLOT_U - (round((s.STOP_U - 0.25) / 0.2) * 0.2 + 0.25)
    cmin = min(c for c, _ in catches)
    out_catch = cmin - play
    springs = [g for _, g in catches]
    report(rest < 0.01 and held > 0.05 and out_catch >= 0.29 and all(0 < g < 0.45 for g in springs),
           f"{n} as printed: each barb reaches at least {cmin:.2f} mm under its ledge ({out_catch:.2f} with the foot pushed "
           f"out against its stops), with {min(springs):.2f} to {max(springs):.2f} mm over it to spring in; lifted 0.3 mm "
           f"the printed barbs catch ({held:.2f} mm3), and seated nothing rubs ({rest:.3f} mm3)")
# the floor between neighbouring cuts, and from a cut to a joist cavity
c = s.FIT
cut_groups = []
for n in WALLS:
    for a0, a1 in s.post_spans(n):
        cut_groups.append((f"{n} post at {(a0 + a1) / 2 / s.S:.1f} in", s.wall_box(n, a0 - c, a1 + c, -c, s.WT + 1, -1, s.ZF + 1)))
    for ac in s.prong_spots(n):
        (a0, a1), (b0, b1) = s.prong_spans(ac)
        cut_groups.append((f"{n} prong at {ac / s.S:.1f} in",
                           s.union([s.wall_box(n, a0 - c, a1 + c, s.BARB - c, s.SLOT_U, -1, s.ZF + 1),
                                    s.wall_box(n, a0 - c, a1 + c, -c, s.BARB - c + 0.01, -1, s.LEDGE_Z),
                                    s.wall_box(n, b0 - c, b1 + c, -c, s.SLOT_U, -1, s.ZF + 1)])))
cc = s.corner_cuts()
for i in range(0, len(cc), 2):
    cut_groups.append((f"corner cut {i // 2 + 1}", cc[i] + cc[i + 1]))
for i, h in enumerate(s.skid_holes()):
    cut_groups.append((f"skid hole {i + 1} ({'inner' if i % 2 == 0 else 'outer'})", h))
web, web_pair, merged_bad = 99.0, "", []
for (na, a), (nb, b) in itertools.combinations(cut_groups, 2):
    A, B = a.bounding_box(), b.bounding_box()
    if max(B[0] - A[3], A[0] - B[3], B[1] - A[4], A[1] - B[4]) > 2.0:
        continue
    g = a.min_gap(b, 2.0)
    if g < 1e-9:
        if not (na.startswith("corner") or nb.startswith("corner")):
            merged_bad.append((na, nb))
    elif g < web:
        web, web_pair = g, f"{na} / {nb}"
report(web >= 0.6 and not merged_bad,
       f"the floor keeps at least {web:.2f} mm between neighbouring cuts (narrowest: {web_pair}); no two cuts run into each "
       f"other but the corner cuts and the end studs' notches in them{(' (merged: %s)' % merged_bad) if merged_bad else ''}")
pockets = s.union(s.floor_pockets())
cav = min(((cg.min_gap(pockets, 1.0), nm) for nm, cg in cut_groups), key=lambda t: t[0])
outer_web = min(h.min_gap(pockets, 1.0) for i, h in enumerate(s.skid_holes()) if i % 2 == 1)
report(cav[0] >= 0.42, f"and at least {cav[0]:.2f} mm from a cut to a joist cavity ({cav[1]}); the outer skids' peg holes "
                       f"keep {outer_web:.2f} mm")
# the roll-up end (lift-out addendum): its two prongs under the jambs, rooted in the bottom plate, a line of plate
# left between each relief and the doorway, no posts under the jambs, the curtain posts at 0, 16 and 35 in
ru_spots = s.prong_spots(ru)
beside = []
for sg_ in (1, -1):
    rr_ = runs(p[ru], s.wall_box(ru, *sorted([sg_ * 33.0, sg_ * 35.2]), 1.55, 1.6, s.ZF + 0.6, s.ZF + 0.65), 0)
    beside.append(min([(b_ - a_) for a_, b_ in rr_ if a_ - 1e-6 <= sg_ * 34.2 <= b_ + 1e-6] or [0.0]))
jamb_post = max(overlap(p[ru], s.wall_box(ru, *sorted([sg_ * 33.9, sg_ * 34.45]), 0.0, s.SD, 0.0, s.ZF - 0.6)) for sg_ in (1, -1))
posts_ru = sorted(round((a_ + b_) / 2 / s.S, 1) for a_, b_ in s.post_spans(ru))
notch_ok = True
for c_ in s.CURTAIN_POSTS:
    inner_ = s.wall_box(ru, c_ - s.SW / 2 - s.FIT + 0.01, c_ + s.SW / 2 + s.FIT - 0.01, -s.FIT + 0.01, 1.0, 1, s.ZF - 1)
    outer_ = s.wall_box(ru, c_ - s.SW / 2 - s.FIT - 0.3, c_ - s.SW / 2 - s.FIT - 0.05, 0.0, 1.0, 1, s.ZF - 1)
    notch_ok &= overlap(fl, inner_) < 1e-6 and overlap(fl, outer_) > 0.05
slot_ = {sg_: s.union([s.wall_box(ru, *sorted([sg_ * 34.5, sg_ * 37.9]), s.BARB - s.FIT, s.SLOT_U, -1, s.ZF + 1),
                       s.wall_box(ru, *sorted([sg_ * 37.9, sg_ * 39.5]), -s.FIT, s.SLOT_U, -1, s.ZF + 1)]) for sg_ in (1, -1)}
cut_of = dict(cut_groups)
end_notch = [cg for nm_, cg in cut_groups if nm_.startswith(f"{ru} post at") and abs(abs(float(nm_.split()[4])) - 59.0) < 0.1]
post35 = [cg for nm_, cg in cut_groups if nm_.startswith(f"{ru} post at") and abs(abs(float(nm_.split()[4])) - 35.0) < 0.1]
slots_ru = [cg for nm_, cg in cut_groups if nm_.startswith(f"{ru} prong at")]
pegs_in = [h_ for i_, h_ in enumerate(s.skid_holes()) if i_ % 2 == 0 and h_.bounding_box()[1] < 0]
w_end = min(a_.min_gap(b_, 3.0) for a_ in slots_ru for b_ in end_notch)
w_post = min(a_.min_gap(b_, 12.0) for a_ in slots_ru for b_ in post35)
w_peg = min(a_.min_gap(b_, 3.0) for a_ in post35 for b_ in pegs_in)
band_ = all(sb_.bounding_box()[1] >= -(s.L / 2 - s.TS - s.FLOOR_CLR) - 1e-6 and
            sb_.bounding_box()[4] <= -(s.L / 2 - s.TS - s.FLOOR_CLR - s.RIM) + 1e-6 for sb_ in slots_ru)
cav_ru = min(sb_.min_gap(pockets, 2.0) for sb_ in slots_ru)
report(sorted(ru_spots) == [-36.2, 36.2] and min(beside) >= 0.42 and jamb_post < 1e-6 and notch_ok
       and posts_ru == [-59.0, -35.0, -16.0, 0.0, 16.0, 35.0, 59.0] and min(w_end, w_post, w_peg) >= 0.6 and band_
       and cav_ru >= 0.42,
       f"roll-up end: its two prongs at x {ru_spots[0]:+.1f} and {ru_spots[1]:+.1f} are under the doorway's jambs, rooted in "
       f"the bottom plate, leaving {min(beside):.3f} mm of plate between each relief and the doorway (at least 0.42); no "
       f"posts under the jambs ({jamb_post:.6f} mm3); its posts at {posts_ru} in (the curtain posts at 0, 16 and 35 in), "
       f"each in its own notch with {s.FIT} round; the floor keeps {w_end:.2f} mm from each new slot to the end stud's notch, "
       f"{w_post:.2f} to the post notch at 35 in and {w_peg:.2f} from that notch to the inner skid's peg hole (at least "
       f"0.6); both slots are in the floor's end band, {cav_ru:.2f} mm from the nearest joist cavity")


def tilt(piece, name, deg):
    """A long wall tipped out deg degrees about the outside top edge of the floor under it."""
    sx = s.WALL_SIDE[name][1]
    xp, zp = sx * (s.W / 2 - s.TS - s.FLOOR_CLR), s.ZF
    a = math.radians(deg) * sx
    cs_, sn = math.cos(a), math.sin(a)
    R = np.array([[cs_, 0, sn], [0, 1, 0], [-sn, 0, cs_]])
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
    a, b, c3 = vv[tt[:, 0]], vv[tt[:, 1]], vv[tt[:, 2]]
    vol6 = np.einsum("ij,ij->i", a, np.cross(b, c3))
    com = ((a + b + c3) * vol6[:, None]).sum(0) / (4 * vol6.sum())
    u_com = sx * com[0] - (s.W / 2 - s.WT)
    u_edge = s.SD - s.FLOOR_CLR
    deg = 0.0
    while deg < 6 and overlap(tilt(w, n, deg + 0.05), fl) < 1e-3:
        deg += 0.05
    lean = math.radians(deg) * H
    tip = w.volume() * (u_com - u_edge)               # its own weight tipping it out (mm3 x mm)
    hold = sum(l.volume() for l in lofts) / 2 * u_edge   # each loft's end lifted at the plate's inside edge
    if tip <= 0:
        report(True, f"{n} stands upright by itself: its weight is {u_com:.2f} mm out from its inside face, inside "
                     f"the floor's edge at {u_edge:.2f} (it could lean {deg:.2f} degrees, {lean:.2f} mm at the top)")
    else:
        report(hold > 2 * tip,
               f"{n} would lean out {deg:.2f} degrees, {lean:.2f} mm at the top, by itself (its weight is {u_com:.3f} mm "
               f"out from its inside face, past the floor's edge at {u_edge:.3f}: {w.volume():.0f} mm3); with the lofts on "
               f"its top plate it stays upright once pushed straight: tipping it lifts their ends, {hold:.0f} against its "
               f"own {tip:.0f} (mm3 x mm), {hold / tip:.2f} to 1 (the barn's rule: over 2 to 1)")
    v = overlap(tilt(w, n, 0.3), loft_set)
    report(v > 0.01, f"{n}: with the lofts on, tipped 0.3 degrees out its top plates and notches meet the lofts' joists "
                     f"and lugs ({v:.3f} mm3), so it can't tip without lifting them")
# the other way: a long wall pushed in a little at the top. The end wall's bottom must meet the
# bevel on the long wall's mitre, which pushes it back out, not land flat on the mitre's top corner.
ew = p["back end"]
z_top = s.ZWT - 0.15
ok_in = True
for lean_mm in (0.2, 0.3, 0.5):
    a = -math.atan(lean_mm / H)
    xp, zp = s.W / 2 - s.WT, s.ZF
    R = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    lw_i = p["door side"].transform(np.column_stack([R, np.array([xp, 0, zp]) - R @ np.array([xp, 0, zp])]))
    lo, hi = 0.0, 100.0
    if overlap(ew, lw_i) < 1e-4:
        continue
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if overlap(ew.translate([0, 0, mid]), lw_i) > 1e-4 else (lo, mid)
    for cpt in (ew.translate([0, 0, hi - 0.02]) ^ lw_i).decompose():
        tb = cpt.bounding_box()
        if cpt.volume() > 1e-5 and not (z_top - s.MITRE_BEVEL - 0.1 < tb[2] and tb[5] < z_top - 0.05):
            ok_in = False
report(ok_in, f"with a long wall pushed in up to 0.5 mm at the top, a coming-down end wall first meets the "
              f"{s.MITRE_BEVEL} mm bevel on the long wall's mitre, which pushes it back out, not the mitre's flat top")


# ======================================================================== 3
group("3 walls print")
for n in WALLS:
    siding, trim_p = flat[n]
    whole = s.union(flat[n])
    bb = whole.bounding_box()
    foot = whole.trim_by_plane([0, 0, -1], -0.2)
    fbb = foot.bounding_box()
    report(fbb[3] - fbb[0] > (bb[3] - bb[0]) - 2 * (s.WT + s.PROUD) - 0.1 and fbb[4] - fbb[1] > 0.9 * (bb[4] - bb[1]),
           f"{n} lies flat on its framing ({foot.volume() / 0.2:.0f} mm2 on the bed)")
    worst, longest, need = bridge_needed(whole)
    report(worst < 5 and need <= 20,
           f"{n} has nothing steeper than 45 degrees that isn't a bridge of 20 mm or less ({worst:.2f} mm2 "
           f"worst layer; the longest bridge it needs is {need:.1f} mm, the longest line held at both ends {longest:.1f})")
    thin = max((cs - cs.offset(-0.2, RND).offset(0.2, RND)).area() for cs in (whole.slice(0.125), whole.slice(0.35)))
    report(thin < 2, f"{n}: no knife edges on the bed ({thin:.2f} mm2 thinner than a line in the first two layers)")
    above = (siding ^ s.box(-BED, 2 * BED, -BED, 2 * BED, s.WT + 1e-4, BED)).volume()
    top = printed_top(s.WT)
    if n == "plain side":
        report(trim_p.volume() < 1e-6 and above < 1e-6,
               f"{n}: no trim at all ({trim_p.volume():.4f} mm3 in filament 2), all white, its siding's top layer at {top:.2f}")
    else:
        tb = trim_p.bounding_box()
        report(trim_p.volume() > 0 and abs(tb[5] - (s.WT + s.PROUD)) < 0.01 and tb[2] > s.WT - 0.01 and above < 1e-6,
               f"{n}: trim is {trim_p.volume() / 1000:.2f} cm3, all of it in the top {s.PROUD} mm ({tb[2]:.2f} to {tb[5]:.2f}, "
               f"printing {printed_top(tb[2]):.2f} to {printed_top(tb[5]):.2f}), and nothing white above the "
               f"siding's top layer ({top:.2f}): one colour change ({above:.6f} mm3 white above it)")
    if n in LONGS:
        v = p[n].trim_by_plane([0, 0, 1], s.ZWT + 0.001).volume()
        report(v == 0, f"{n}: nothing above the wall plates (the barn ends carry all of the gable)")
        # slivers in the first layers: where each end joist's notch stops short of the mitre, and
        # where the edge joists' notches bottom on the studs, or on the door side the front loft's over
        # the door's hinge-side king stud and the end of its header
        sliver = 0.0
        sx = s.WALL_SIDE[n][1]
        xi = s.W / 2 - s.WT
        xa, xb = sorted([sx * (xi - 0.5), sx * (xi + s.SD)])
        regions = []
        for sy in (1, -1):
            y_end = s.loft_joist_ys()[0] + s.SW / 2 + s.FIT
            ya, yb = sorted([sy * (y_end - 1.5), sy * (s.L / 2 + 1)])
            regions.append(("end", s.box(xa, xb, ya, yb, s.LOFT_Z - s.LUG_D - 1.5, s.ZWT + 1)))
            ye = sy * s.loft_joist_ys()[-1]
            regions.append(("edge", s.box(xa, xb, ye - 2, ye + 2, s.LOFT_Z - s.LUG_D - 1.5, s.ZWT + 1)))
        for kind, reg in regions:
            part = print_part(p[n], s.WALL_TO_PRINT[n], reg)
            zs = (0.125, 0.35) if kind == "end" else [(z0 + z1) / 2 for z0, z1 in layers(s.SD)]
            for z in zs:
                cs = part.slice(z)
                sliver = max([sliver] + [bt.area() for bt in (cs - cs.offset(-0.21, RND).offset(0.21, RND)).decompose()])
        front = ", the front one over the door's hinge-side king stud" if n == "door side" else ""
        report(sliver < 0.15, f"{n}: at each loft notch (the end joists' near the mitres, the edge joists' over the studs"
                              f"{front}) nothing prints under a line wide but rounded corners ({sliver:.3f} mm2 at most)")
# the roll-up end round its doorway, now the curtain lifts out (lift-out addendum): the latch plate is on the curtain,
# not the wall; the rebate's ceiling, the lip's wedge and the jamb stops print as designed
lr = s.face_prism(ru, s.latch_outline(0.3), -1, s.WT + 2)
report(overlap(p[ru], lr) < 1e-6 and overlap(zone, lr) < 1e-6,
       f"{ru}: the roll-up's latch plate is no longer in the wall (nothing of the wall or its trim where it was: "
       f"{overlap(p[ru], lr):.6f} mm3); it is on the lift-out curtain (group 6)")
ru_whole = s.union(flat[ru])
ox_ = -(p[ru].transform(np.column_stack([np.array(s.WALL_TO_PRINT[ru], dtype=float), np.zeros(3)])).bounding_box()[0])
crop = ru_whole ^ s.box(ox_ - s.RU_W / 2 - 3, ox_ + s.RU_W / 2 + 3, s.MOUTH - 3, s.MOUTH + s.REB_H + 3, -1, s.REB_U + 0.5)
c_worst, c_long, c_need = bridge_needed(crop)
lip_tops, lip_join = [], True
stop_edge, stop_top = [], 0.0
for z0_, z1_ in layers(s.WT):
    zm_ = (z0_ + z1_) / 2
    sec_ = ru_whole.slice(zm_)
    if s.LIP_U0 < zm_ < s.WT:
        col_ = sec_ ^ m3.CrossSection.square([0.02, s.ZF + 3]).translate([ox_ + 5.0 - 0.01, 0])
        rr_ = sorted((q.bounds()[1], q.bounds()[3]) for q in col_.decompose() if q.area() > 1e-7)
        hold_ = [r_ for r_ in rr_ if r_[0] <= s.ZF - 0.05 <= r_[1]]
        lip_join &= len(hold_) == 1
        lip_tops.append(hold_[0][1] if hold_ else 0.0)
    if zm_ < s.RU_W / 2 + 0.01 - s.RU_STOP_X0:
        row_ = sec_ ^ m3.CrossSection.square([4.0, 0.02]).translate([ox_ + 31.0, 30.0])
        xs_ = [q.bounds()[0] - ox_ for q in row_.decompose() if q.area() > 1e-7]
        stop_edge.append(min(xs_) if xs_ else 99.0)
col_ = ru_whole.slice(0.75) ^ m3.CrossSection.square([0.02, 80]).translate([ox_ + 33.6, 0])
stop_top = max([q.bounds()[3] for q in col_.decompose() if q.area() > 1e-7 and q.bounds()[3] < s.MOUTH - 1] + [0.0])
lip_grow = max(b_ - a_ for a_, b_ in zip(lip_tops, lip_tops[1:]))
stop_steps = [b_ - a_ for a_, b_ in zip(stop_edge[1:], stop_edge[2:])]           # from the second layer up: 45 degrees
stop_grow = max(stop_steps)
# the first layer's edge is set back RU_STOP_FOOT from the stop's edge (its 45 degree face would put it 0.125 out), so
# the second layer, 0.35 out, reaches past it
foot_ok = abs(stop_edge[0] - stop_edge[1] - (s.RU_STOP_FOOT - 0.35)) < 0.01 and abs(stop_edge[0] - stop_edge[1]) <= 0.2
on_grid = {k_: abs((v_ - 0.25) / 0.2 - round((v_ - 0.25) / 0.2)) < 1e-6 for k_, v_ in
           (("REB_U", s.REB_U), ("LIP_U0", s.LIP_U0), ("BOT_U", s.BOT_U), ("TAB_T", s.TAB_T), ("TAB_BUMP_U", s.TAB_BUMP_U),
            ("BUMP_U", s.BUMP_U), ("RU_FACE", s.RU_FACE))}
strip_r = runs(p[ru], s.wall_box(ru, 4.99, 5.01, 0.8, 0.82, s.MOUTH + 0.5, s.ZWT + 2), 2)
strip_p = runs(printed_in_shed(p[ru], s.WALL_TO_PRINT[ru], s.wall_box(ru, 3, 7, -1, s.SD + 1, s.MOUTH - 1, s.ZWT + 3)),
               s.wall_box(ru, 4.99, 5.01, 0.05, s.REB_U - 0.05, s.MOUTH + 0.5, s.ZWT + 2), 2)
strip_ok = (len(strip_r) == 1 and abs(strip_r[0][0] - (s.MOUTH + s.REB_H)) < 1e-6 and strip_r[0][1] > s.ZWT
            and len(strip_p) == 1 and strip_p[0][1] > s.ZWT)
report(c_worst < 5 and c_need <= 20 and lip_join and lip_grow <= 0.2 + 1e-6 and min(stop_steps) >= -1e-9
       and stop_grow <= 0.2 + 1e-6 and foot_ok
       and abs(stop_top - s.RU_STOP_TOP) < 1e-6 and all(on_grid.values()) and strip_ok and s.ZWT - s.MOUTH - s.REB_H >= 0.42,
       f"{ru} prints round the doorway: over the curtain's rebate the first layer of the head (the 1.65 layer) is a bridge "
       f"of {c_need:.1f} mm at most between the ribs, pads and jambs, held along the rebate's top (20 or less; {c_worst:.2f} "
       f"mm2 left over); the lip's wedge grows {lip_grow:.3f} a layer at most (exactly 45 degrees down to its foot: at most "
       f"0.2) and is joined to the skirt on every layer; "
       f"the jamb stops step back {min(stop_steps):.3f} to {stop_grow:.3f} a layer (45 degrees; at most 0.2, never out) "
       f"from their second layer up and end at z {stop_top:.2f}, their "
       f"first layer starting {stop_edge[0] - stop_edge[1]:+.3f} from the second's edge (its 0.25 is set back RU_STOP_FOOT "
       f"{s.RU_STOP_FOOT} from the 45 degree face, so it can't meet the curtain's first layer; the second layer reaches past it "
       f"by that much at most, under 45 degrees); REB_U, LIP_U0, BOT_U, TAB_T, TAB_BUMP_U, "
       f"BUMP_U and RU_FACE are all on the 0.25 + 0.2k layer lines; the {s.ZWT - s.MOUTH - s.REB_H:.3f} mm strip of top "
       f"plate over the rebate is solid into the gable board, as drawn and as printed (at least 0.42)")
fb_ = (p[ru] ^ zone ^ s.box(-25, -24, -s.L / 2 - 2, -s.L / 2 + 1, s.ZWT - 1, s.ZWT + 10)).bounding_box()
report(abs(fb_[2] - s.ZWT) < 1e-6 and abs(fb_[5] - (s.ZWT + s.TRIM)) < 1e-6,
       f"{ru}: the front band runs from the wall top ({fb_[2] - s.ZWT:+.4f}) up {fb_[5] - fb_[2]:.3f} mm")
# the layout studs that land on other framing are dropped and listed, not shifted
# (Alan's standard layout, Nov 3 2026: the door's edge is on the 4 ft mark, so the -96.75 in stud stands
# exactly where the door's hinge-side king stud is; the old door side +112 in collision is gone with the door)
EXPECT_DROPPED = {("door side", -96.75): 1.058, ("roll-up end", -51.0): 0.53, ("roll-up end", 61.0): None,
                  ("back end", 61.0): None}
for wname, mark, hit, ov in s.DROPPED_MARKS:
    print(f"     dropped layout mark: {wname}, {mark:+.2f} in from its middle: its stud would hit {hit}, "
          f"overlapping {ov:.2f} mm ({ov / s.S:.2f} in)")
got = {(w_, m_): ov for w_, m_, _, ov in s.DROPPED_MARKS}
same = set(got) == set(EXPECT_DROPPED) and all(e is None or abs(got[k] - e) < 0.01 for k, e in EXPECT_DROPPED.items())
gone = [overlap(p[ru], s.wall_box(ru, -36.45, -36.05, 0.5, 1.0, 30, 40)),
        overlap(p[ru], s.wall_box(ru, -36.45, -36.05, 1.7, 3.0, 1, 5))]   # (the prong at -36.2 is at u 0 to 1.65)
report(same and max(gone) < 1e-6,
       f"the dropped layout marks are exactly the four decided (door side -96.75, on the door's hinge-side king stud; "
       f"roll-up end -51 and +61; back end +61); no stud or post stands on the roll-up end's -51 ({max(gone):.6f} mm3 "
       f"where it would be), and the 61 in marks would stand inside the solid corner")


# the door side's framing for Alan's standard layout, worked out here from the addendum's numbers and the 16 in
# layout (a double stud at every 4 ft mark, from the roll-up end), and read off the wall in a column 0.5 to 1.0 mm
# out from its inside face, between its end studs, in inches from its middle
def layout_in():
    """Every layout stud along the 288 in wall: [(start, end)] in inches from its middle."""
    out = []
    for k in range(1, 18):
        a = 16 * k - 144
        out += [(a - 1.5, a), (a, a + 1.5)] if k % 3 == 0 else [(a - 0.75, a + 0.75)]
    return out


def merge(spans):
    out = []
    for a_, b_ in sorted(spans):
        if out and a_ <= out[-1][1] + 1e-6:
            out[-1] = (out[-1][0], max(b_, out[-1][1]))
        else:
            out.append((a_, b_))
    return out


def framing_runs(z):
    lim = s.L / 2 - s.WT - s.SW - 0.3
    reg = s.box(s.W / 2 - s.WT + 0.5, s.W / 2 - s.WT + 1.0, -lim, lim, z, z + 0.05)
    return [(a_ / s.S, b_ / s.S) for a_, b_ in runs(p["door side"], reg, 1)]


d0_in, d1_in = STD_DOOR[0] / s.S, STD_DOOR[1] / s.S                      # -96, -60
w0_in, w1_in = STD_WIN_YC / s.S - 12.6, STD_WIN_YC / s.S + 12.6        # 29.4, 54.6 (w23 is 25.2 in wide)
zones = [(d0_in - 3, d1_in + 3), (w0_in - 3, w1_in + 3)]                # each opening and its full + king studs
clear = [st for st in layout_in() if all(st[1] <= z0_ + 1e-3 or st[0] >= z1_ - 1e-3 for z0_, z1_ in zones)]
in_door = [st for st in layout_in() if st[0] >= d0_in - 1e-3 and st[1] <= d1_in + 1e-3]
in_win = [st for st in layout_in() if st[0] >= w0_in - 1e-3 and st[1] <= w1_in + 1e-3]
pairs = [(d0_in - 3, d0_in), (d1_in, d1_in + 3), (w0_in - 3, w0_in), (w1_in, w1_in + 3)]
z_low = s.ZF + 20                                                         # beside the door, under the window plate
z_hdr = (s.ZF + s.DOOR_OPEN_H + s.FLAT_HEADER + s.ZWT - s.PLATE_TOP) / 2   # over the door's header
want_low = merge(clear + pairs + in_win)
want_hdr = merge(clear + [(d0_in - 3, d0_in - 1.5), (d1_in + 1.5, d1_in + 3)] + in_door + [(w0_in - 3, w1_in + 3)])
ok_f = True
for z_, want_ in ((z_low, want_low), (z_hdr, want_hdr)):
    got_ = framing_runs(z_)
    ok_f &= len(got_) == len(want_) and all(abs(a_ - c_) < 0.02 and abs(b_ - d_) < 0.02
                                            for (a_, b_), (c_, d_) in zip(got_, want_))
hinge = [r for r in framing_runs(z_low) if abs(r[1] - d0_in) < 0.02]
report(ok_f and len(in_door) == 3 and len(in_win) == 3 and len(hinge) == 1,
       f"door side framed for the standard layout: {len(want_low)} runs of framing beside the openings and "
       f"{len(want_hdr)} over the door's header, each where the 16 in layout and the openings put it (0.02 in): the door's "
       f"full and king studs {hinge[0][0] if hinge else 0:.2f} to {d0_in:.2f} in and {d1_in:.2f} to {d1_in + 3:.2f}, so the "
       f"-96.75 in layout stud is its king stud; cripples over its header on the {len(in_door)} marks inside it "
       f"(-95.25, -80, -64) and none on -96.75; the window's at {w0_in - 3:.2f} to {w0_in:.2f} and {w1_in:.2f} to "
       f"{w1_in + 3:.2f} with {len(in_win)} studs under its plate (32, 47.25, 48.75); every other layout stud full height")
# nothing in the openings but what belongs there: in the door's, only the stop on its latch jamb; in the window's,
# only its sashes; nothing of the floor, the lofts, the other walls or the skids in either
dz0, dz1 = s.ZF + 0.01, s.ZF + s.DOOR_OPEN_H - 0.01
dbox = s.box(s.W / 2 - s.WT - 0.5, s.W / 2 + s.PROUD + 1, STD_DOOR[0] + 0.01, STD_DOOR[1] - 0.01, dz0, dz1)
wz0, wz1 = s.ZF + s.WIN_TOP - s.WIN_H, s.ZF + s.WIN_TOP
wbox = s.box(s.W / 2 - s.WT - 0.5, s.W / 2 + s.PROUD + 1, STD_WIN_YC - s.WIN_W / 2 + 0.01, STD_WIN_YC + s.WIN_W / 2 - 0.01,
             wz0 + 0.01, wz1 - 0.01)
rest = s.union([fl, loft_set] + [p[n] for n in WALLS if n != "door side"] + [k for _, k in skids_placed])
in_d = ((p["door side"] - s.door_stop()) ^ dbox).volume() + overlap(rest, dbox)
in_w = ((p["door side"] - s.union(s.window_unit(s.WIN_YC))) ^ wbox).volume() + overlap(rest, wbox)
stop_v = overlap(s.door_stop(), dbox)
sash_v = overlap(p["door side"], wbox)
report(in_d < 1e-3 and in_w < 1e-3 and stop_v > 1 and sash_v > 1,
       f"nothing in the openings but what belongs there: the door's (y {STD_DOOR[0]} to {STD_DOOR[1]}) holds only the "
       f"stop on its latch jamb ({stop_v:.1f} mm3), the window's only its sashes ({sash_v:.1f} mm3), nothing else of any "
       f"part ({in_d:.4f} and {in_w:.4f} mm3)")
# the siding beside the casings: no groove within GROOVE_W of a side board's outer edge, read off the siding just
# under its face. The -56 in groove, 1/2 in past the door's latch-side casing, would run 0.1 mm from its edge (review,
# Nov 3 2026), so it is filled beside the board and runs on above it and in the skirt under the floor top
side_gaps = []
for edge_, out_, cz0_, cz1_ in s.casing_sides():
    zc_ = (cz0_ + cz1_) / 2
    ya_, yb_ = sorted([edge_ - out_ * 1.0, edge_ + out_ * 12.0])
    rr_ = runs(p["door side"], s.box(s.W / 2 - 0.3, s.W / 2 - 0.05, ya_, yb_, zc_, zc_ + 0.2), 1)
    hold_ = [r for r in rr_ if r[0] - 1e-6 <= edge_ <= r[1] + 1e-6]
    side_gaps.append(out_ * ((hold_[0][1] if out_ > 0 else hold_[0][0]) - edge_) if hold_ else -1.0)
yg_ = -56 * s.S


def groove_gaps(z):
    """The gaps in the door side's siding just under its face round the -56 in groove, at height z."""
    rr = runs(p["door side"], s.box(s.W / 2 - 0.3, s.W / 2 - 0.05, yg_ - 2, yg_ + 2, z, z + 0.2), 1)
    return [(a_[1], b_[0]) for a_, b_ in zip(rr, rr[1:])]


g_mid, g_top, g_low = groove_gaps(s.ZF + 20), groove_gaps(s.ZF + s.DOOR_OPEN_H + s.TRIM + 1), groove_gaps(s.ZF - 3)
ok_g = not g_mid and all(len(g_) == 1 and abs(g_[0][0] - (yg_ - s.GROOVE_W / 2)) < 1e-3
                         and abs(g_[0][1] - (yg_ + s.GROOVE_W / 2)) < 1e-3 for g_ in (g_top, g_low))
report(min(side_gaps) >= s.GROOVE_W and ok_g and len(s.groove_fills()) == 1,
       f"the siding beside the door side's casings is clean: from the outer edge of each side board to the nearest "
       f"groove {', '.join(f'{g_:.2f}' for g_ in side_gaps)} mm (the door's hinge and latch sides, the window's two), "
       f"none under {s.GROOVE_W} mm; the -56 in groove, 1/2 in past the latch-side casing, is filled beside it "
       f"({len(g_mid)} gaps there 20 mm up) and runs on {s.GROOVE_W:.2f} wide above the casing ({len(g_top)} gap) and "
       f"in the skirt under the floor top ({len(g_low)} gap)")
# the prongs and posts under the door side stay clear of the openings: none under the doorway (its sill post
# runs the length of the door's framing), and the +40 in prong under the window hangs from the bottom plate
fz0_, fz1_ = (d0_in - 3) * s.S, (d1_in + 3) * s.S
pr_gap, under_win = 99.0, []
for ac in s.prong_spots("door side"):
    (a0, a1), (b0, b1) = s.prong_spans(ac)
    lo_, hi_ = min(a0, b0), max(a1, b1)
    pr_gap = min(pr_gap, max(fz0_ - hi_, lo_ - fz1_))
    if hi_ > (w0_in - 3) * s.S and lo_ < (w1_in + 3) * s.S:
        under_win.append(ac / s.S)
sill_post = [sp for sp in s.post_spans("door side") if abs(sp[0] - fz0_) < 1e-3 and abs(sp[1] - fz1_) < 1e-3]
top_under = max(s.LEG_ROOT, s.ZF + 0.3)
report(pr_gap >= 1.0 and len(sill_post) == 1 and top_under < wz0 - 20,
       f"door side: its prongs keep {pr_gap:.2f} mm or more from the door's framing along the wall, which has one sill post "
       f"under all of it ({sill_post[0][0] if sill_post else 0:.3f} to {sill_post[0][1] if sill_post else 0:.3f}); "
       + (f"the prong at {', '.join(f'{x:+.0f}' for x in under_win)} in is under the window, its leg rooted in the bottom "
          f"plate {wz0 - s.LEG_ROOT:.1f} mm under the sill" if under_win else "no prong is under the window")
       + f"; every post and prong stays under {top_under - s.ZF:.1f} mm over the floor top")

# ======================================================================== 4
group("4 corners")
U, V, Z = np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), np.array([0, 0, 1.0])
DIRS = [np.array(d, dtype=float) / np.linalg.norm(d) for d in itertools.product((-1, 0, 1), repeat=3) if any(d)]
around = s.cbox(-12, 4, -12, 4, -2, 200)                  # the walls near a corner
sheets = {"door-side upper sheet": upper, "plain-side upper sheet": upper.mirror([1, 0, 0]),
          "door-side lower sheet": lower, "plain-side lower sheet": lower.mirror([1, 0, 0])}
roof_all = s.union(list(sheets.values()))
trim_all = s.union(s.trims())
swing = [door.transform(s.door_to_shed(deg)) for deg in range(0, 99, 7)]
RL, RE = s.angle_reach()
CL, CE = RL + s.POCKET_CLR, RE + s.POCKET_CLR            # how far each recess reaches from the corner
V_CH = -(2 * s.POCKET_D + s.CORNER_CHAMFER) + s.POCKET_D  # where the chamfer cuts each recess floor (-1.55)


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
    edge = min(overlap(a.translate(-0.2 * V), lw), overlap(a.translate(-0.2 * U), ew))
    up_ = overlap(a.translate(0.2 * Z), s.union([lw, ew]))
    # how wide each leg's contact with its recess floor is: pressed 0.05 in, the overlap's extent
    cw_l = runs(a.translate(-0.01 * U) ^ lw, s.cbox(-1, 1, -10, 1, 30, 31), 1)
    cw_e = runs(a.translate(-0.01 * V) ^ ew, s.cbox(-10, 1, -1, 1, 30, 31), 0)
    wl = sum(b_ - a_ for a_, b_ in cw_l)
    we = sum(b_ - a_ for a_, b_ in cw_e)
    report(none < 1e-3 and seat > 1 and edge > 0.05 and up_ > 0.01 and min(wl, we) >= 1.40,
           f"corner angle, {where}: sits in both recesses touching neither wall ({none:.4f} mm3) but on the recess floors "
           f"({seat:.1f} mm3 pressed 0.05 mm in), {wl:.2f} and {we:.2f} mm of each floor under its legs; moved 0.2 mm "
           f"along either wall it meets the recess's edge ({edge:.2f}), and 0.2 mm up the recess's top ({up_:.2f} mm3)")
    worst = clear_moves(a, lw, ew, 0.09)
    fillet = (a ^ s.cbox(-1.5, -0.45, -1.5, -0.45, 10, 50)).min_gap(s.union([lw, ew]), 1.0)
    report(worst < 1e-4 and 0.2 <= fillet <= 0.3,
           f"corner angle, {where}: moved 0.09 mm any of 26 ways but into a recess floor it still touches neither wall "
           f"({worst:.5f} mm3), so it is about 0.1 clear all round; its fillet is {fillet:.3f} mm off the walls' chamfer")
    press = max(overlap(a.translate(t * e), s.union([lw, ew])) for e in (U, V, (U + V) / math.sqrt(2))
                for t in np.arange(0.02, 1.51, 0.02))
    report(press < 1e-4, f"corner angle, {where}: presses straight into its recesses from 1.5 mm out, square to either "
                         f"wall or into the corner, without catching on anything ({press:.5f} mm3)")
    moved = max(overlap(a.translate(d * n_a), w_b) for n_a, w_b in ((U, ew), (V, lw)) for d in (0.15, -0.15))
    report(moved < 1e-3, f"corner angle, {where}: with either wall sitting 0.15 mm out or in, the angle on its recess "
                         f"still touches nothing of the other wall ({moved:.4f} mm3)")
    face_l = (a ^ s.cbox(s.ANGLE_P - 0.01, 2, -10, 10, -1, 200)).bounding_box()
    face_e = (a ^ s.cbox(-10, 10, s.ANGLE_P - 0.01, 2, -1, 200)).bounding_box()
    cover_l, cover_e = s.L / 2 - face_l[1], s.W / 2 - face_e[0]
    foot = a.bounding_box()[2] - min(lw.bounding_box()[2], ew.bounding_box()[2])
    report(min(cover_l, cover_e) >= 2.95 and abs(foot) < 1e-6,
           f"corner angle, {where}: covers the mitre's outside edge by {cover_l:.2f} mm on the long wall's face and "
           f"{cover_e:.2f} on the end wall's, from its foot, level with the skirts, up to {face_l[5]:.2f} mm")
    roof_c = home(roof_all)
    gap = a.min_gap(roof_c, 1.0)
    low = overlap(a, roof_c.translate([0, 0, -0.15]))
    gap_t = a.min_gap(home(trim_all), 1.0)
    gap_l = a.min_gap(home(loft_set), 5.0)
    gap_d = min(a.min_gap(home(d), 5.0) for d in swing)
    over = "the rake board" if sy > 0 else "the front band"
    report(gap >= 0.2 - 0.002 and low < 1e-4 and gap_t >= 0.15 - 0.002 and gap_l >= 0.1 and gap_d >= 0.1,
           f"corner angle, {where}: {gap:.3f} mm clear of the roof sheets, square to them (still clear with the roof 0.15 "
           f"mm lower: {low:.5f} mm3), {gap_t:.3f} under {over}, and clear of the lofts ({gap_l:.1f}) and the door "
           f"swinging ({gap_d:.1f} mm)")

# the same as printed: both walls and the angle each cut into their own print's layers, with anything
# thinner than a line rounded off. Pushed onto both printed recess floors the angle must still miss
# the walls, also with the band closing the 0.1 mitre gap. Probe windows come from the sizes: each
# recess floor runs from the chamfer (1.55 from the corner) to the recess's edge (3.15).
p_lo, p_hi = -(RL - 0.1), V_CH - 0.15
for sx, sy in s.CORNERS:
    lw_n, ew_n = s.corner_walls(sx, sy)
    where = "%s at %s" % (lw_n, ew_n)
    _, _, home = corner_set(sx, sy, p)
    region = home(s.cbox(-12, 2, -12, 2, 30, 60))
    pl = home(printed_in_shed(p[lw_n], s.WALL_TO_PRINT[lw_n], region))
    pe = home(printed_in_shed(p[ew_n], s.WALL_TO_PRINT[ew_n], region))
    pa = home(printed_in_shed(s.corner_angle(sx, sy), s.CORNER_TO_PRINT[sx], region))
    floor_u = (pl ^ s.cbox(-3, 1, p_lo, p_hi, 40, 50)).bounding_box()[3] - s.W / 2
    floor_v = (pe ^ s.cbox(p_lo, p_hi, -3, 1, 40, 50)).bounding_box()[4] - s.L / 2
    du = floor_u - ((pa ^ s.cbox(-1, 1, p_lo, p_hi, 40, 50)).bounding_box()[0] - s.W / 2)
    dv = floor_v - ((pa ^ s.cbox(p_lo, p_hi, -1, 1, 40, 50)).bounding_box()[1] - s.L / 2)
    seated = pa.translate([du, dv, 0])
    v = overlap(seated, s.union([pl, pe]))
    on = min(overlap(seated.translate(-0.01 * U), pl), overlap(seated.translate(-0.01 * V), pe))
    shut = 0.1 / math.sqrt(2)
    v_shut = overlap(seated.translate(-shut * V), s.union([pl, pe.translate(shut * (U - V))]))
    tip_e = seated.bounding_box()[0] - (pe ^ s.cbox(-(CE + 3), -(RE - 0.05), -0.3, 1, 40, 50)).bounding_box()[3]
    tip_l = seated.bounding_box()[1] - (pl ^ s.cbox(-0.3, 1, -(CL + 3), -(RL - 0.05), 40, 50)).bounding_box()[4]
    box2 = m3.CrossSection.square([2.4, 2.4]).translate([s.W / 2 - 3, s.L / 2 - 3])
    ws, fs = s.union([pl, pe]).slice(45.0) ^ box2, seated.slice(45.0) ^ box2
    lo, hi = 0.0, 0.5
    for _ in range(14):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if (fs.offset(mid, RND) ^ ws).area() > 1e-7 else (mid, hi)
    report(v < 1e-4 and on > 0.05 and v_shut < 1e-4 and min(tip_e, tip_l) >= 0.05 and lo >= 0.03,
           f"corner angle, {where}, as printed: pushed {-du:.3f} and {-dv:.3f} mm in onto both printed recess floors "
           f"({floor_u:.3f}, {floor_v:.3f}) it touches neither wall ({max(v, 0):.4f} mm3 over 30 mm), nor with the mitre "
           f"closed ({max(v_shut, 0):.4f}); {tip_l:.3f} mm left past the long-face leg and {tip_e:.3f} past the end-face "
           f"leg, and the fillet's steps {lo:.3f} mm off the chamfer's")
for name, part in angle_flat:
    bb = part.bounding_box()
    worst, _ = worst_overhang(part)
    loose = floating(part)
    foot = part.slice(0.125).area()
    report(worst < 0.01 and loose < 0.02 and abs(bb[5] - s.ANGLE_UP) < 1e-6 and abs(printed_top(bb[5]) - bb[5]) < 1e-6
           and round((bb[5] - 0.25) / 0.2) + 1 == 18 and foot > 0.9 * (bb[3] - bb[0]) * (RL + s.ANGLE_P),
           f"corner angle, {name}: prints lying on its long-face leg ({foot:.0f} mm2 on the bed), its other leg standing "
           f"{bb[5]:.2f} mm, 18 layers, on a layer line, nothing steeper than 45 degrees and nothing starting in mid-air "
           f"({worst:.3f} and {loose:.3f} mm2 worst layer)")
# the walls at each corner, as printed: the recess floor two layers under the siding's top layer, and
# no sliver thinner than a line where the chamfer meets the mitre, the recess and the nearest groove
narrowest = (99.0, "")
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
        if axis == 0:
            region = s.cbox(-2.2, 2, -9.5, 2, -2, s.ZWT)
            mat, out = s.WALL_TO_PRINT["door side"], s.W / 2
        else:
            region = s.cbox(-9.5, 2, -2.2, 2, -2, s.ZWT)
            mat, out = s.WALL_TO_PRINT["back end"], s.L / 2
        floors.append((piece ^ probe(-(CL - 0.3), V_CH - 0.3)).bounding_box()[3 + axis] - out + s.WT)
        faces.append((piece ^ probe(-(CL + 0.25), -(CL + 0.15))).bounding_box()[3 + axis] - out + s.WT)
        # the siding between the recess's edge and the nearest groove, on the face
        segs = runs(piece, s.cbox(-0.2, 1, -12, -0.5, 30, 31) if axis == 0 else s.cbox(-12, -0.5, -0.2, 1, 30, 31), 1 - axis)
        edge_ = (s.L / 2 if axis == 0 else s.W / 2) - CL                 # the recess's edge
        strip = [b_ - a_ for a_, b_ in segs if abs(b_ - edge_) < 1e-3][0]  # the siding running up to it
        if strip < narrowest[0]:
            narrowest = (strip, f"{n} at its {'+' if (sy if axis == 0 else sx) > 0 else '-'}"
                                f"{'y' if axis == 0 else 'x'} corner")
        R = np.column_stack([np.array(mat, dtype=float), [0, 0, -(out - s.WT)]])
        flat_c = (piece ^ region).transform(R)
        for z0, z1 in layers(s.WT):
            if (z0 + z1) / 2 < s.WT - 2.2:
                continue
            cs = flat_c.slice((z0 + z1) / 2)
            bits = cs - cs.offset(-0.21, RND).offset(0.21, RND)
            # with the zero-width hairlines the rounding leaves along straight edges taken out, so
            # separate rounded corners (0.022 mm2 each) aren't summed into one bit
            bits = bits.offset(-0.01, RND).offset(0.01, RND)
            thin = max([thin] + [b.area() for b in bits.decompose()])
            longest = max([longest] + [math.hypot(b.bounds()[2] - b.bounds()[0], b.bounds()[3] - b.bounds()[1])
                                       for b in bits.decompose() if b.area() > 1e-4])
    pf = {round(printed_top(h), 3) for h in floors}
    pw = {round(printed_top(h), 3) for h in faces}
    report(pf == {4.65} and pw == {5.05} and thin < 0.05 and longest < 0.6,
           f"{n}: as printed, each corner recess's floor is on the {min(pf):.2f} layer line and the siding's face on "
           f"{min(pw):.2f}, 2 layers; near the corners nothing is thinner than a line (biggest bit under a line wide "
           f"{thin:.3f} mm2, longest {longest:.2f} mm)")
report(narrowest[0] >= 0.8, f"the narrowest strip of siding between a corner recess and the nearest groove is "
                            f"{narrowest[0]:.2f} mm ({narrowest[1]}), over a line wide, and the check above shows it prints")


# ======================================================================== 5
group("5 gables and vents")
for n in ENDS:
    side = s.WALL_SIDE[n][1]
    piece = p[n]
    vz0 = s.ZPK - s.VENT_DROP - s.VENT_H / 2
    ya, yb = sorted([side * (s.L / 2 - 3), side * (s.L / 2 + 3)])
    pitch_ = (s.VENT_H - 2 * 1.0) / s.VENT_SLATS
    zg_ = vz0 + 1.0 + pitch_ - s.VENT_BACK_GAP / 2           # the middle of the gap over the bottom louvre, at the back
    vfloor = u_range(n, piece ^ s.box(-2, 2, ya, yb, zg_ - 0.15, zg_ + 0.15))[1]
    vfront = u_range(n, piece ^ s.box(-3, 3, ya, yb, vz0 + 1.3, vz0 + 6.0))[1]
    bridge = min(z0 for z0, z1 in layers(s.WT) if (z0 + z1) / 2 > s.SD)
    under = round((vfloor - bridge) / 0.2, 6)
    report(abs(printed_top(vfloor + 1e-9) - vfloor) < 1e-6 and under >= 3 and abs(vfront - s.WT) < 1e-6,
           f"{n}: the gable vent's louvres sit in a recess {s.WT - vfloor:.2f} mm into the siding, its floor on the "
           f"{vfloor:.2f} layer line over {under:.0f} layers of siding (from {bridge:.2f}); the slats' fronts and the frame "
           f"come up to the siding face ({vfront:.3f}) and no further")
    # as printed: on every layer of the recess, every free slat and every gap over a line, the gaps
    # next to the frame's bars too (the probe takes in 0.5 of each bar); the bottom louvre stands on
    # the lower bar on purpose, so it is the first run with that bar
    fr = 1.0
    fx0, fx1 = -s.VENT_W / 2 + fr, s.VENT_W / 2 - fr
    fz0, fz1 = vz0 + fr, vz0 + s.VENT_H - fr
    reg = s.box(fx0, fx1, ya, yb, fz0 - 0.5, fz1 + 0.5)
    part = print_part(piece, s.WALL_TO_PRINT[n], reg)
    R = np.array(s.WALL_TO_PRINT[n], dtype=float)
    bbw = piece.transform(np.column_stack([R, np.zeros(3)])).bounding_box()
    # print y is garage z for the end walls; the vent's middle (garage x = 0) is at print x -bbw[0]
    xm = -bbw[0]
    lines, ok_v, nslats = [], True, set()
    for zm in (4.95, 4.75, 4.55, 4.35):
        cs = part.slice(zm).offset(-0.21, RND).offset(0.21, RND)
        segs = scan(cs.rotate(90), [xm])[0]           # turned 90: lines of constant print x
        ys_ = sorted((-b_, -a_) for a_, b_ in segs)
        widths = [b_ - a_ for a_, b_ in ys_]
        gaps = [ys_[i + 1][0] - ys_[i][1] for i in range(len(ys_) - 1)]
        # the runs, bottom to top: the lower bar (with the bottom louvre on it if it is wider than
        # the bar's 0.5), the free slats, the upper bar
        free_ = widths[1:-1]
        sill = len(widths) >= 2 and widths[0] > 0.5 + 0.2
        louvres = len(free_) + (1 if sill else 0)
        nslats.add(louvres)
        ok_v &= (len(widths) >= 3 and louvres == s.VENT_SLATS and min(free_) >= 0.42 and min(gaps) >= 0.42
                 and abs(widths[-1] - 0.5) < 0.01)
        lines.append(f"{zm:.2f}: free slats {min(free_):.2f}-{max(free_):.2f}, gaps {min(gaps):.2f}-{max(gaps):.2f} "
                     f"({gaps[0]:.2f} over the bottom louvre, {gaps[-1]:.2f} under the frame)"
                     if len(widths) >= 3 else f"{zm:.2f}: {len(widths)} runs")
    report(ok_v, f"{n}: as printed, {s.VENT_SLATS} louvres on every layer of the recess, the bottom one standing on the "
                 f"frame and {s.VENT_SLATS - 1} free; every free slat and every gap, the one under the frame's top bar "
                 f"too, over a 0.42 line (" + "; ".join(lines) + ")")
    # the gable framing, read off the wall in a column 0.5 to 1.0 mm out from its inside face
    yi0, yi1 = sorted([side * (s.L / 2 - s.WT + 0.5), side * (s.L / 2 - s.WT + 1.0)])

    def col(x, z0, z1, w=0.1):
        return [(a_ - s.ZWT, b_ - s.ZWT) for a_, b_ in runs(piece, s.box(x - w / 2, x + w / 2, yi0, yi1, z0, z1), 2)]
    c1 = col(-5.0, s.ZWT, s.COLLAR_TOP - s.COLLAR_H - 0.3)
    board = c1[0] if c1 else (0, 0)
    backing = [r for r in c1[1:]]
    gz = s.ZWT + s.GABLE_BOARD + 1.0
    studs = [((a_ + b_) / 2, b_ - a_) for a_, b_ in runs(piece, s.box(-42, 42, yi0, yi1, gz, gz + 0.1), 0)]
    collar = col(10.0, s.ZWT + 12, s.ZWT + 30)
    king = runs(piece, s.box(-6, 6, yi0, yi1, s.COLLAR_TOP + 3, s.COLLAR_TOP + 3.1), 0)
    ch = col(15.0, s.COLLAR_TOP + 0.5, s.ZPK + 1, w=0.002)
    chord = (ch[-1][1] - ch[-1][0]) / math.sqrt(1 + s.UP_M ** 2) if ch else 0
    want_studs = [x for x in s.GABLE_STUD_XS]
    got_studs = [x for x, w_ in studs if abs(w_ - s.GABLE_STUD_W) < 0.01]
    ok_g = (abs(board[0]) < 1e-6 and abs(board[1] - s.GABLE_BOARD) < 1e-6
            and len(got_studs) == 5 and all(abs(a_ - b_) < 1e-6 for a_, b_ in zip(sorted(got_studs), want_studs))
            and len(collar) == 1 and abs(collar[0][1] - (s.COLLAR_TOP - s.ZWT)) < 1e-6
            and abs(collar[0][1] - collar[0][0] - s.COLLAR_H) < 1e-6
            and len(king) == 1 and abs(king[0][1] - king[0][0] - s.KING_W) < 1e-6 and abs(chord - s.CHORD) < 0.01)
    if n == "back end":
        ok_g &= len(backing) == 1 and abs(backing[0][0] - s.BACKING_Z) < 1e-6 and abs(backing[0][1] - backing[0][0] - s.BACKING_H) < 1e-6
        btxt = f"backing {backing[0][0]:.3f} to {backing[0][1]:.3f} over the wall top" if backing else "NO backing"
    else:
        ok_g &= not backing
        btxt = "no backing (it has the faux loft window)" if not backing else f"backing at {backing}"
    report(ok_g, f"{n}: gable board {board[1] - board[0]:.3f} tall on the upper plate, gable studs "
                 f"{s.GABLE_STUD_W:.3f} wide at " + ", ".join(f"{x / s.S:.0f}" for x in sorted(got_studs)) +
                 f" in, collar tie {collar[0][1] - collar[0][0] if collar else 0:.3f} with its top {collar[0][1] if collar else 0:.3f} "
                 f"over the wall top, king post {king[0][1] - king[0][0] if king else 0:.3f} wide, chords {chord:.3f} deep "
                 f"(CHORD {s.CHORD:.3f}), {btxt}")
# the faux loft window: trim only, all in the trim layers, its frame and corner triangles
fx = s.FAUX_W / 2
fz0, fz1 = s.FAUX_ZC - s.FAUX_H / 2, s.FAUX_ZC + s.FAUX_H / 2
fwin = p[ru] ^ zone ^ s.box(-fx - 0.01, fx + 0.01, -s.L / 2 - 2, -s.L / 2 + 1, fz0 - 0.01, fz1 + 0.01)
ib = s.FAUX_BAR
want = (s.FAUX_W * s.FAUX_H - (s.FAUX_W - 2 * ib) * (s.FAUX_H - 2 * ib) + 4 * s.FAUX_TRI ** 2 / 2) * s.PROUD
uu = u_range(ru, fwin)
inner_white = overlap(p[ru] - zone, s.box(-fx + ib + s.FAUX_TRI, fx - ib - s.FAUX_TRI, -s.L / 2 - 1, -s.L / 2 + 0.3,
                                           fz0 + ib + 1, fz1 - ib - 1))
report(abs(fwin.volume() - want) < 0.03 * want and abs(uu[0] - s.WT) < 1e-3 and abs(uu[1] - s.WT - s.PROUD) < 1e-3
       and inner_white > 1,
       f"{ru}: the faux loft window is {fwin.volume():.1f} mm3 of black (frame and four corner triangles: {want:.1f}), "
       f"all from {uu[0]:.3f} to {uu[1]:.3f} (the trim layers), with the white siding showing inside it")


# ======================================================================== 6
group("6 roll-up and lofts")
cas = p[ru] ^ zone
z20 = s.ZF + 20
segs = runs(cas, s.box(-40, 40, -s.L / 2 - 1, -s.L / 2, z20, z20 + 0.1), 0)
inner = [b_ for a_, b_ in segs if b_ < 0]
outer = [a_ for a_, b_ in segs if a_ > 0]
ru_w = (min(outer) - max(inner)) if inner and outer else 0
head = runs(cas, s.box(-1, 1, -s.L / 2 - 1, -s.L / 2, s.ZF, s.ZWT), 2)
ru_h = head[0][0] - s.ZF if head else 0
report(abs(ru_w / s.S - 96) < 0.01 and abs(ru_h / s.S - 76.8) < 0.01 and abs((min(outer) + max(inner)) / 2) < 1e-6,
       f"the roll-up opening is {ru_w / s.S:.2f} x {ru_h / s.S:.2f} in between its casings, centred on the roll-up end "
       f"(designer ru8: 96 x 76.8 in)")
# the head over the doorway: the coil box behind the siding up to the top plates, solid but for the curtain's rebate,
# and in the rebate only its three ribs and two pads (lift-out addendum E.3)
coil_r = s.rbox(-s.RU_W / 2 + 0.01, s.RU_W / 2 - 0.01, s.REB_U + 0.01, s.SD - 0.01, s.MOUTH + 0.01, s.ZWT - s.PLATE_TOP - 0.01)
reb_r = s.rbox(-s.RU_W / 2 + 0.01, s.RU_W / 2 - 0.01, 0.01, s.REB_U - 0.01, s.MOUTH + 0.01, s.MOUTH + s.REB_H - 0.01)
want_rp = sum((rp_ ^ reb_r).volume() for rp_ in s.rebate_ribs_pads())
cv_, rv_ = overlap(p[ru], coil_r), overlap(p[ru], reb_r)
report(abs(cv_ - coil_r.volume()) < 0.01 and abs(rv_ - want_rp) < 0.01,
       f"the coil box and the siding over the doorway are solid in front of the curtain's rebate up to the top plate "
       f"({cv_:.1f} of {coil_r.volume():.1f} mm3), so nothing bridges the 68 mm opening; in the rebate (u 0 to {s.REB_U}, "
       f"{s.REB_H} tall) there is only its three ribs and two pads ({rv_:.2f} mm3 of {want_rp:.2f})")
_, ru_bridge = worst_overhang(ru_whole ^ s.box(0, BED, 0, 75, -1, 10))
report(ru_bridge <= 20, f"in the roll-up end's print the longest bridge in its lower 75 mm is {ru_bridge:.1f} mm (20 or less: the skirt between"
                        f" the posts under the doorway and the rebate's ceiling, measured on its longest line held at both "
                        f"ends)")
# the doorway is empty (the Garage's line): no curtain, rail, latch or shade left in the end wall between the stops over
# the lip, read off its sections on four planes u, and none beside the curtain over the stops
ruT_ = p[ru].transform(np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, -U0_RU]], dtype=float))   # (x, z, u): u up


def sq_xz(x0, x1, z0, z1):
    return m3.CrossSection.square([x1 - x0, z1 - z0]).translate([x0, z0])


open_door = max((sq_xz(-s.RU_STOP_X0 + 0.05, s.RU_STOP_X0 - 0.05, s.ZF + s.LIP_H + 0.01, s.MOUTH - 0.01) ^ ruT_.slice(u_)).area()
                for u_ in (0.125, 2.0, 4.0, 4.95))
open_jamb = max((sq_xz(*sorted([sg * (s.RU_STOP_X0 - 0.05), sg * (s.RU_W / 2 - 0.01)]), s.RU_STOP_TOP + 0.01, s.MOUTH - 0.01)
                 ^ ruT_.slice(0.125)).area() for sg in (1, -1))
report(open_door < 1e-6 and open_jamb < 1e-6,
       f"the doorway is empty: no curtain, rail, latch or shade is left in the wall ({open_door:.6f} mm2 of wall between "
       f"the stops over the lip at u 0.125, 2.0, 4.0 and 4.95; {open_jamb:.6f} beside the curtain over the stops)")
kings_top = [(p[ru] ^ s.wall_box(ru, a0_ + 0.05, a1_ - 0.05, 0.5, 1.5, s.ZF + 10, s.ZWT)).bounding_box()[5]
             for a0_, a1_ in ((s.RU_W / 2, s.RU_W / 2 + s.SW), (-s.RU_W / 2 - s.SW, -s.RU_W / 2))]
report(all(abs(k_ - s.ZWT) < 1e-6 for k_ in kings_top),
       f"Alan's king studs beside the roll-up run up to the top plates (solid to {min(kings_top):.3f}), no header")

# ---------------------------------------------------------------- the lift-out roll-up curtain (addendum L.6)
def pose_3d(M):
    """A (u, z) pose matrix as a garage transform (x stays): u = -y - U0_RU."""
    a, b, e = M[0]
    c, d, f = M[1]
    return np.array([[1, 0, 0, 0], [0, a, -b, a * U0_RU - e - U0_RU], [0, -c, d, -c * U0_RU + f]], dtype=float)


TAB_ROOT_K = (0.60, 0.61)                            # tab rate / clamped cantilever (fe3d_tab.py)
WEIGHT = s.CUR_WEIGHT_G * 9.81e-3                    # N: the curtain sliced alone
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


A_D, A_P = contact_a(0.0, 0.0), contact_a(0.1, 0.05)
FIN_D, FIN_P = finger(A_D), finger(A_P)
Lb_ = A_D                                                       # root to where the pad bears, 15.6
Iu_ = s.FING_H * s.TONGUE_T ** 3 / 12
EI_U = 3000.0 * Iu_
ku = (2500.0 * 3 * Iu_ / Lb_ ** 3 * 0.60, 3500.0 * 3 * Iu_ / Lb_ ** 3)   # sideways: the z rate's root factor (fe2d) to clamped
EPS_U = 1.5 * s.TONGUE_T / Lb_ ** 2 * 100                         # strain % per mm of sideways bend at the root, clamped
STATIONS = sorted(set([0.0, 0.3, 13.0, 14.5, 15.6, 16.6, 17.3, 1.2, 2.5, 3.6, 5.0, 5.4, 7.0, 9.0, 10.2, 11.289, 12.5, 14.0,
                       15.0, 15.5, 16.25, 17.0, 17.7, 18.4, 20.0, 22.0, 24.0, 24.694, 26.0, 28.0, round(s.LATCH_X, 3), 30.0,
                       31.5, 32.2, 32.5, 32.9, 33.2, 33.45, 33.55]))
# the addendum's 77 (every notch, rib, pad, bump, tab, post, the latch, the handle, the chamfer zone), two in the side
# gaps, 0.05 either side of each pad's edges, and every 0.05 from 32.25 to 33.85, where the jamb stops meet the curtain's
# back chamfers: as printed, a layer of a 45 degree stop meets the curtain's own layer only in a band 0.1 wide along x,
# which the 77 can miss (review, Nov 3 2026: they missed the two 0.25 first layers' band at x 32.39..32.49); 141 in all.
# As printed, each case adds a station in every interval between its printed layers' corners round the jamb stops
# (jamb_stations()), so there it misses nothing
STATIONS = sorted(set(STATIONS + [33.65, 33.8] + [round(32.25 + 0.05 * k_, 2) for k_ in range(33)]
                      + [15.95, 16.05, 16.65, 16.75]))
STATIONS = STATIONS + [-x for x in STATIONS if x > 0]
GROWTHS = [(0.0, 0.0), (0.1, 0.1), (0.15, 0.1), (0.2, 0.05)]
ru_piece = p[ru]
front_loft = lofts[1]
lo_others = [("floor", fl, "bed"), ("front loft", front_loft, "bed"), ("roof", roof_all, "none")]
H_ = s.RU_W / 2
JAMB_ZONES = [(-H_ - 0.35, -s.RU_STOP_X0 + 0.35), (s.RU_STOP_X0 - 0.35, H_ + 0.35)]
TO_XZU = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, -U0_RU]], dtype=float)    # garage -> (x, z, u), u up as they print
XZU_BACK = np.array([[1, 0, 0, 0], [0, 0, -1, -U0_RU], [0, 1, 0, 0]], dtype=float)
FLOOR_UP = np.array([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, s.ZF]], dtype=float)   # the floor upside down, its top on
                                                                                    # the bed (its own inverse)


def jamb_stations(cur, wall, gw, gc, zones):
    """As printed, a part's (u, z) section at x is the union of its sections at x - g, x and x + g, each cut into its
    print layers (u up), so it changes only where some layer's outline, sliced at the layer's middle, has a corner at
    x - g, x or x + g. Within the x zones given (round the jamb stops, whose first layers and the curtain's chamfered back
    edges are where a band narrower than the stations' spacing could hold it off its seat) and under the stops' top, a
    station in the middle of every interval between two such places of the curtain (grown gc) or the wall (grown gw):
    so there the printed sections miss nothing."""
    xs = set()
    lo, hi = min(a for a, b in zones) - 1, max(b for a, b in zones) + 1
    for m, g in ((cur, gc), (wall, gw)):
        mt = (m ^ s.box(lo, hi, -s.L, s.L, -1, s.RU_STOP_TOP + 2)).transform(TO_XZU)
        bb = mt.bounding_box()
        e = ulayers(bb[5])
        for a, b in zip(e[:-1], e[1:]):
            mid = (a + b) / 2
            if mid < bb[2] or mid > bb[5]:
                continue
            for poly in mt.slice(mid).simplify(1e-6).to_polygons():      # (no in-line points: real corners only)
                q = np.asarray(poly)
                for x in q[q[:, 1] < s.RU_STOP_TOP + 1.0][:, 0]:
                    for d in ((-g, 0.0, g) if g > 0 else (0.0,)):
                        if any(a_ <= x + d <= b_ for a_, b_ in zones):
                            xs.add(round(float(x + d), 5))
    xs = sorted(xs)
    return [round((a + b) / 2, 5) for a, b in zip(xs, xs[1:]) if b - a > 2e-5]


def printed_xs(cur, wall, gw, gc, base=None, zones=JAMB_ZONES):
    return sorted(set(STATIONS if base is None else base) | set(jamb_stations(cur, wall, gw, gc, zones)))


def printed_solid(m, grow, floor_part=False):
    """A part as printed, in 3D, put back in garage coords: its print layers (0.25, then 0.2), each its section at the
    layer's middle grown `grow` a side in the bed plane, held over the layer. The end wall and the curtain print u up,
    the floor upside down."""
    mat, back = (FLOOR_UP, FLOOR_UP) if floor_part else (TO_XZU, XZU_BACK)
    mt = m.transform(mat)
    bb = mt.bounding_box()
    slabs = []
    for a, b in layers(bb[5]):
        mid = (a + b) / 2
        if mid < bb[2]:
            continue
        cs_ = mt.slice(mid)
        if cs_.is_empty():
            continue
        if grow > 0:
            cs_ = cs_.offset(grow, m3.JoinType.Miter, 2.0)
        slabs.append(M.extrude(cs_, b - a).translate([0, 0, a]))
    return s.union(slabs).transform(back)


wall_near = ru_piece ^ s.box(-H_ - 5, H_ + 5, -s.L / 2 - 10, -s.L / 2 + 20, -1, s.MOUTH + 8)
floor_near = fl ^ s.box(-H_ - 5, H_ + 5, -s.L / 2 - 1, -(s.L / 2 - 15), -1, s.ZF + 1)
rig_only = p["curtain"] - s.union([b_ for v_ in s.curtain_regions().values() for b_ in v_])


def named_obstacles(cs):
    W, F = cs.wall, cs.other["floor"]
    post = lambda x: any(abs(abs(x) - abs(c)) < s.SW / 2 + 0.3 for c in s.CURTAIN_POSTS)
    rib = lambda x: any(abs(abs(x) - abs(r)) < s.RIB_W / 2 + 0.2 for r in s.RIB_XS)
    pad = lambda x: s.PAD_X0 - 0.2 <= abs(x) <= s.PAD_X1 + 0.2
    ZF, MO = s.ZF, s.MOUTH
    return {
        "lip (wedge)": lambda i, x: None if post(x) else W[i].intersection(sbox(3.55, ZF - 0.3, s.WT + 0.05, ZF + s.LIP_H + 0.15)),
        "jamb stops": lambda i, x: W[i].intersection(sbox(-0.1, ZF - 0.2, 1.7, s.RU_STOP_TOP + 0.3)) if abs(x) > 32.0 else None,
        "head in front of the rebate": lambda i, x: W[i].intersection(sbox(s.REB_U - 0.25, MO - 0.25, s.WT - s.EMBED - 0.01, MO + 12)),
        "rebate top": lambda i, x: None if rib(x) or pad(x) else W[i].intersection(sbox(-0.5, MO + s.REB_H - 0.25, s.REB_U - 0.25, MO + 12)),
        "ribs": lambda i, x: W[i].intersection(sbox(-0.5, MO - 0.25, s.REB_U, MO + s.REB_H - 0.25)) if rib(x) else None,
        "pads": lambda i, x: cs.pads[i].intersection(sbox(-0.5, 0, s.REB_U, MO + s.REB_H - 0.25)) if pad(x) else None,
        "casing": lambda i, x: W[i].intersection(sbox(s.WT - s.EMBED - 0.01, MO - 0.25, s.WT + s.PROUD + 0.2, MO + s.TRIM + 0.3)),
        "skirt and floor": lambda i, x: unary_union([F[i], W[i].intersection(sbox(s.SD - 0.3, -1, s.WT + 0.2, ZF - 0.05))]),
        "posts": lambda i, x: W[i].intersection(sbox(-0.5, -1, s.LIP_U0 - 0.05, ZF + s.LIP_H + 0.15)) if post(x) else None,
        "front loft (rigid curtain)": lambda i, x: cs.other["front loft"][i],
    }


def study(cs, full=False):
    """Seat, preloads, pushes, stop, least lift, window, bottom play; with full, the removal paths too."""
    r = {"cs": cs}
    pre = settle_seat(cs)
    r["noseat"] = pre is None                   # nowhere in reach is free of rigid overlap
    pre = pre or (0.0, 0.0)
    r["pre"] = pre
    e = cs.ev(pre=pre)
    r["fpre"], r["tpre"], r["strip"] = e["fbend"], e["tbend"], e["strip"]
    r["push"] = {k: cs.ov(pre=(pre[0] + v[0], pre[1] + v[1]), L=v[2])
                 for k, v in (("out 0.25", (0.25, 0, 0)), ("in 0.1", (-0.1, 0, 0)), ("down 0.1", (0, -0.1, 0)),
                              ("out 0.5 lifted 0.3", (0.5, 0, 0.3)))}
    L = rigid_stop(cs, pre)
    r["stop"] = L
    es = cs.ev(pre=pre, L=L)
    r["fbend_stop"] = es["fbend"]
    need = least_lift(cs, pre, L)
    while need is not None and need < L and not path_clear(cs, removal_poses(need, 7.0, pre)):
        need = round(need + 0.05, 3)
    r["need"] = need if need is not None else round(L + 0.5, 3)     # (no lift lets it out: the window fails)
    r["window"] = L - r["need"]
    r["empty"] = max(cs.ov(pre=pre, L=0.3, th=a) for a in (1, 2, 4, 6))
    play = 0.0
    for k in range(1, 60):
        if cs.ov(pre=pre, th=k * 0.01, pu=0.0, pz=s.RU_STOP_TOP + pre[1]) > 1e-5:
            break
        play = k * 0.01
    r["play"] = math.radians(play) * (s.RU_STOP_TOP - (s.ZF + 0.5))
    lift_m = round(L - 0.15, 3)
    r["m15"] = {name: motion_ok(cs, pre, lift_m, name) for name in MOTIONS}
    r["rm15"] = max(path_worst(cs, removal_poses(lift_m, th, pre))["ov"] for th in (6.0, 7.0, 8.0))
    return r


# ---- the cases: drawn, as printed (holes 0.1 small, the curtain 0.05 big), and the growth cases
cases = {}
xs_pr = {g_: printed_xs(p["curtain"], ru_piece, *g_) for g_ in [(0.1, 0.05)] + GROWTHS}
cases["drawn"] = study(Case("drawn", p["curtain"], ru_piece, lo_others, STATIONS), full=True)
cases["printed"] = study(Case("printed", p["curtain"], ru_piece, lo_others, xs_pr[(0.1, 0.05)], 0.1, 0.05, True), full=True)
for gw_, gc_ in GROWTHS:
    cases[(gw_, gc_)] = study(Case(f"{gw_}/{gc_}", p["curtain"], ru_piece, lo_others, xs_pr[(gw_, gc_)], gw_, gc_, True))
D, P = cases["drawn"], cases["printed"]
print(f"     ({len(STATIONS)} stations as drawn; as printed one more in every interval between the printed layers' corners "
      f"round the jamb stops: " + ", ".join(f"{k_[0]}/{k_[1]} {len(v_)}" for k_, v_ in xs_pr.items()) + ")")

# ---- 6.1 the part
cw, cb = s.curtain_print(p)
cpr = cw + cb
cbb = cpr.bounding_box()
csz = (cbb[3] - cbb[0], cbb[4] - cbb[1], cbb[5] - cbb[2])
want_sz = (2 * s.CUR_HALF, s.Z_TT + s.BUMP_H - (s.ZF + s.G_BOT), s.HDL_U2)
report(len(cpr.decompose()) == 1 and all(abs(a_ - b_) < 0.01 for a_, b_ in zip(csz, want_sz)) and abs(cbb[2]) < 1e-9,
       f"roll-up curtain: one solid, {csz[0]:.2f} x {csz[1]:.2f} x {csz[2]:.2f} on the bed (expected {want_sz[0]:.2f} x "
       f"{want_sz[1]:.2f} x {want_sz[2]:.2f}), lying on its back face at z {cbb[2]:.3f}")
wtop, bbot, btop = cw.bounding_box()[5], cb.bounding_box()[2], cb.bounding_box()[5]
lpr = s.to_print(s.WALL_TO_PRINT[ru], [p["curtain black"] ^ s.face_prism(ru, s.latch_outline(0.01), s.RAIL_FACE - 0.1,
                                                                           s.RAIL_FACE + 1)])[0]
want_l = (m3.CrossSection([s.latch_outline()]).area() - m3.CrossSection([s.latch_slot()]).area()) * s.LATCH_T
lpu = u_range(ru, p["curtain black"] ^ s.face_prism(ru, s.latch_outline(0.01), s.RAIL_FACE - 0.1, s.RAIL_FACE + 1))
slot_white = overlap(p["curtain white"], s.face_prism(ru, s.latch_slot(), s.RAIL_FACE - 0.05, s.RAIL_FACE + 1))
legs = []
for uu in (5.15, 5.35, 5.55, 5.75):
    sec_ = cb.slice(uu)
    hx0 = cbb[0] + s.CUR_HALF + s.HDL_HALF - s.HDL_LEG      # the +x leg in print x
    leg_ = sec_ ^ m3.CrossSection.square([s.HDL_LEG + 1.0, 10]).translate([hx0 - 0.5, -1])
    lb_ = leg_.bounds()
    legs.append((round(lb_[2] - lb_[0], 3), round(lb_[3] - (s.RAIL_Z0 - s.ZF - s.G_BOT), 3)))
report(abs(wtop - 5.05) < 1e-6 and abs(bbot - 5.04) < 1e-6 and abs(btop - s.HDL_U2) < 1e-6
       and (cw ^ s.box(-BED, 2 * BED, -BED, 2 * BED, 5.05 + 1e-4, BED)).volume() < 1e-6
       and abs(lpr.volume() - want_l) < 0.05 * want_l and abs(printed_top(lpu[1]) - 5.45) < 1e-6 and slot_white > 0.05
       and legs == [(round(s.HDL_LEG + 2 * f_, 3), round(s.HDL_HT + f_, 3)) for f_ in list(s.HDL_FILLET) + [0.0]],   # the legs and their fillet
       f"roll-up curtain colours: white up to {wtop:.3f} (the 5.05 layer), black from {bbot:.3f}; the black latch plate "
       f"{lpr.volume():.2f} mm3 against {want_l:.2f} for its outline less the slot x {s.LATCH_T} (u {lpu[0]:.2f} to "
       f"{lpu[1]:.2f}, prints 5.05 to {printed_top(lpu[1]):.2f}), white boss in its slot; the handle to {btop:.2f}, each leg "
       f"{', '.join(f'{a_:.1f} x {b_:.1f}' for a_, b_ in legs)} on the 5.05, 5.25, 5.45 and 5.65 layers (its stepped "
       f"fillet), nothing white over 5.05")
thin_c, gap_c, free_rows, grip_bridge = 0.0, 0.0, [], 0.0
prev_, zp_ = None, 0.0
for z0_, z1_ in layers(cbb[5]):
    zm_ = (z0_ + z1_) / 2
    sec_ = cpr.slice(zm_)
    thin_c = max([thin_c] + [q.area() for q in (sec_ - sec_.offset(-0.21, RND).offset(0.21, RND)).decompose()])
    gap_c = max([gap_c] + [q.area() for q in (sec_.offset(0.21, RND).offset(-0.21, RND) - sec_).decompose()])
    if prev_ is not None:
        fr_ = sec_ - prev_.offset(1.1 * (zm_ - zp_), RND)
        for q in fr_.decompose():
            if q.area() > 0.05:
                bq = q.bounds()
                free_rows.append((round(z0_, 2), round(q.area(), 2), round(bq[0] - cbb[0] - s.CUR_HALF, 2),
                                  round(bq[2] - cbb[0] - s.CUR_HALF, 2)))
        if abs(z0_ - s.HDL_U1) < 1e-6:
            grip_bridge = overhangs(sec_, prev_, reach=1.1 * (zm_ - zp_))[1]
    prev_, zp_ = sec_, zm_
chamf_rows = [r_ for r_ in free_rows if abs(r_[0] - 0.25) < 1e-6 and min(abs(r_[2]), abs(r_[3])) > 32.0]
grip_rows = [r_ for r_ in free_rows if abs(r_[0] - s.HDL_U1) < 1e-6 and max(abs(r_[2]), abs(r_[3])) <= s.HDL_HALF]
report(thin_c < 0.15 and gap_c < 0.15 and len(chamf_rows) + len(grip_rows) == len(free_rows) and len(grip_rows) == 1
       and 0 < grip_bridge <= 20,
       f"roll-up curtain prints: on every layer nothing under a 0.42 line ({thin_c:.3f} mm2 at most) and no gap under one "
       f"({gap_c:.3f}); over air only the two back chamfers, which grow at 45 degrees ({sum(r_[1] for r_ in chamf_rows):.2f} "
       f"mm2 past that), and the grip's first layer, a {grip_bridge:.1f} mm bridge over the nail gap ({grip_rows[0][1] if grip_rows else 0:.2f} "
       f"mm2){'' if len(chamf_rows) + len(grip_rows) == len(free_rows) else ' (also: %s)' % free_rows}")
# the slat grooves, on the two layers they are cut in, read along lines down the curtain
lx0, lx1 = s.LATCH_X - s.LATCH_W / 2, s.LATCH_X + s.LATCH_W / 2
gz0, gz1 = s.slat_zs()[0] - 0.4, s.slat_zs()[-1] + 0.4
xs_scan = [round(x_, 3) for x_ in np.arange(-33.3, 33.31, 0.37)] + [round(x_, 4) for x_ in np.arange(lx0 - 0.3073, lx1 + 0.3, 0.02)]   # (never on an edge)
min_gap_g, bad_scan = 9.0, []
lz0, lz1 = s.LATCH_Z - s.LATCH_H / 2, s.LATCH_Z + s.LATCH_H / 2
inside_ = [z_ for z_ in s.slat_zs() if lz0 <= z_ - s.RU_GROOVE_W / 2 and z_ + s.RU_GROOVE_W / 2 <= lz1]   # filled under it
latch_rect = m3.CrossSection.square([s.LATCH_W, s.LATCH_H]).translate(
    [lx0 + s.CUR_HALF + cbb[0], lz0 - (s.ZF + s.G_BOT) + cbb[1]])
open_under = max((latch_rect - cpr.slice(um_)).area() for um_ in (4.55, 4.75))
for um_ in (4.55, 4.75):
    sec_ = cpr.slice(um_)
    for x_ in xs_scan:
        px_ = x_ + s.CUR_HALF + cbb[0]
        cut_ = sec_ ^ m3.CrossSection.square([0.004, 80]).translate([px_ - 0.002, -1])
        ys_ = sorted((q.bounds()[1], q.bounds()[3]) for q in cut_.decompose() if q.area() > 1e-6)
        gaps_ = [(b_[0] - a_[1]) for a_, b_ in zip(ys_, ys_[1:])
                 if gz0 - s.ZF - s.G_BOT < a_[1] < gz1 - s.ZF - s.G_BOT]
        filled = sum(1 for z_ in inside_ if abs(x_ - s.LATCH_X) <= s.LATCH_W / 2)
        filled += sum(1 for z_ in s.slat_zs() if z_ + s.RU_GROOVE_W / 2 > s.Z_FT - (um_ - (s.RU_FACE - s.CH_TOP)))
        if gaps_:
            min_gap_g = min(min_gap_g, min(gaps_))
        if len(gaps_) != 31 - filled:
            bad_scan.append((um_, x_, len(gaps_), 31 - filled))
report(min_gap_g >= 0.42 and not bad_scan and open_under < 1e-6,
       f"roll-up curtain: on the 4.55 and 4.75 layers every slat groove is {min_gap_g:.3f} mm wide or more (a line is 0.42), "
       f"31 of them across the curtain (the top one runs out into the bevel on these layers, as drawn); under the latch "
       f"plate the grooves are filled square to its rectangle ({len(inside_)} grooves, read along {2 * len(xs_scan)} lines; "
       f"{open_under:.6f} mm2 of the rectangle open), so the plate's white boss stands on solid fill, with no corner over "
       f"an open groove, and no groove is left part width{'' if not bad_scan else ' (wrong count at %s)' % bad_scan[:4]}")
under_ = p["curtain"].slice(s.CHAMF_TOP - 0.1)
over_ = p["curtain"].slice(s.CHAMF_TOP + 0.1)
corner_pt = m3.CrossSection.square([0.3, 0.3]).translate([s.CUR_HALF - 0.31, -(s.L / 2 - s.WT) - 0.31])
root_top = p["curtain"].slice(s.Z_FT + 0.05) ^ m3.CrossSection.square([s.CUR_HALF - s.FING_ROOT, 2]).translate(
    [s.FING_ROOT, -(s.L / 2 - s.WT) - 1.5])
root_bot = p["curtain"].slice(s.Z_FT - 0.05)
unsup = (root_top - root_bot).area()
report((under_ ^ corner_pt).area() < 1e-6 and (over_ ^ corner_pt).area() > 0.08 and unsup < 1e-4 and root_top.area() > 1.2
       and s.Z_FT - s.CHAMF_TOP >= 2.0 and s.CHAMF_TOP - s.RU_STOP_TOP >= 5.9,
       f"roll-up curtain: its back chamfers stop at CHAMF_TOP {s.CHAMF_TOP} (the back corner is cut 0.1 under it, square "
       f"0.1 over it), {s.Z_FT - s.CHAMF_TOP:.2f} under the body's top (at least 2), so each finger's root block "
       f"({root_top.area():.2f} mm2) stands on the square body top over its whole footprint ({unsup:.4f} mm2 not over it), "
       f"and {s.CHAMF_TOP - s.RU_STOP_TOP:.2f} over the jamb stops' top (the addendum's 6, so the square corner stays clear "
       f"of the stops on every path)")

# ---- 6.2 seat, drawn
cs_d, cs_p = D["cs"], P["cs"]
e0 = cs_d.ev(gaps=True)
zbot = p["curtain"].bounding_box()[2]
ep = cs_p.ev(pre=P["pre"])
report(e0["ov"] < 1e-6 and abs(e0["fbend"] - s.PRELOAD) < 1e-6 and abs(e0["tbend"] - (s.TAB_BUMP_U - s.REB_U)) < 1e-6
       and e0["strip"] < 1e-6 and ep["strip"] < 1e-4 and abs(zbot - s.ZF - s.G_BOT) < 1e-6,
       f"roll-up curtain seated as drawn: no rigid overlap ({e0['ov']:.6f} mm2 at any of {len(STATIONS)} stations ("
       f"{len(cs_p.xs)} as printed), least "
       f"gap {e0['gap']:.3f}); the finger bumps {e0['fbend']:.2f} into their pads, the tab bumps {e0['tbend']:.2f} into the "
       f"rebate's front face; each spring moved by its own bend touches nothing ({e0['strip']:.6f} drawn, {ep['strip']:.6f} "
       f"mm2 as printed at its seat); its bottom face {zbot - s.ZF:.3f} over the floor top")

# ---- 6.3 settle, 6.4 held
rows_, ok_ = [], True
for k_, r_ in cases.items():
    nm_ = k_ if isinstance(k_, str) else f"{k_[0]}/{k_[1]}"
    ok_ &= r_["fpre"] > 0.1 and r_["tpre"] > 0.1 and not r_["noseat"]
    rows_.append(f"{nm_}: {r_['pre'][0]:+.3f} out, {r_['pre'][1]:+.3f} up, preloads {r_['fpre']:.2f} / {r_['tpre']:.2f}")
# the printed seats again in 3D, on the parts cut into their layers and grown (no stations): the rigid curtain at each
# seat touches nothing of the end wall and floor, and let down one search step (0.025) it does
solid_w, solid_c = {}, {}
seat3d, seat3d_rows = 0.0, []
for k_, r_ in cases.items():
    if k_ == "drawn":
        continue
    gw_, gc_ = (0.1, 0.05) if k_ == "printed" else k_
    if gw_ not in solid_w:
        solid_w[gw_] = s.union([printed_solid(wall_near, gw_), printed_solid(floor_near, gw_, True)])
    if gc_ not in solid_c:
        solid_c[gc_] = printed_solid(rig_only, gc_)
    at_ = overlap(solid_c[gc_].transform(pose_3d(pose_mat(pre=r_["pre"]))), solid_w[gw_])
    below_ = overlap(solid_c[gc_].transform(pose_3d(pose_mat(pre=(r_["pre"][0], r_["pre"][1] - 0.025)))), solid_w[gw_])
    seat3d = max(seat3d, at_, 1.0 if below_ <= 1e-3 else 0.0)
    seat3d_rows.append(f"{k_ if isinstance(k_, str) else f'{k_[0]}/{k_[1]}'} {at_:.5f} ({below_:.3f} let down 0.025)")
report(ok_ and seat3d < 1e-3,
       "roll-up curtain settles where the springs push it (down and in, no rigid overlap, searched 0.8 each way): "
       + "; ".join(rows_) + " (finger / tab, both over 0.1); in 3D, the rigid curtain as printed at each printed seat "
       "overlaps the end wall and floor as printed by " + ", ".join(seat3d_rows) + " mm3 (under 0.001 at the seat, over "
       "it let down)")
ok_, rows_ = True, []
for nm_ in ("drawn", "printed"):
    r_ = cases[nm_]
    ok_ &= all(v_ > 1e-4 for v_ in r_["push"].values())
    rows_.append(f"{nm_}: " + ", ".join(f"{a_} {b_:.4f}" for a_, b_ in r_["push"].items()))
# sideways, in 3D (the rigid curtain, the springs taken out): pushed either way in steps of 0.025, how far it goes
# before it meets anything (over 0.01 mm3), and what it meets: the jamb stops, the 45 degree faces behind its
# chamfered back edges, before its side gap to the jambs (0.30 drawn, 0.15 as printed, the wall and curtain grown)
# closes. Drawn they touch it already; as printed both are stairs, which leave a little play before they meet
STOPS_3D = s.union([s.rbox(*sorted([sg * (s.RU_STOP_X0 - 0.2), sg * (H_ + 0.02)]), -0.1, H_ - s.RU_STOP_X0 + 0.2,
                           s.ZF - 0.02, s.RU_STOP_TOP + 0.02) for sg in (1, -1)])
side_ok, side_rows = True, []
for nm_, wl_, cr_, pre_ in (("drawn", s.union([wall_near, floor_near]), rig_only, D["pre"]),
                            ("printed", solid_w[0.1], solid_c[0.05], P["pre"])):
    seated_ = cr_.transform(pose_3d(pose_mat(pre=pre_)))
    gap_ = s.RU_CLR_X - (0 if nm_ == "drawn" else 0.1 + 0.05)
    for sg in (1, -1):
        d_, v_stop, v_else = 0.0, 0.0, 0.0
        while d_ < gap_ + 0.1:
            d_ = round(d_ + 0.025, 3)
            moved_ = seated_.translate([sg * d_, 0, 0])
            v_stop, v_else = overlap(moved_, wl_ ^ STOPS_3D), overlap(moved_, wl_ - STOPS_3D)
            if v_stop + v_else > 0.01:
                break
        side_ok &= d_ <= gap_ - 0.02 and v_stop > v_else
        side_rows.append(f"{nm_} {'+' if sg > 0 else '-'}x: meets them at {d_:.3f} (its side gap {gap_:.2f}; "
                         f"{v_stop:.2f} mm3 into the stops, {v_else:.3f} into anything else)")
plays = {(k_ if isinstance(k_, str) else f"{k_[0]}/{k_[1]}"): r_["play"] for k_, r_ in cases.items()}
report(ok_ and side_ok and max(plays.values()) <= 0.15,
       f"roll-up curtain held from its seat: pushed, each blocked by rigid parts (mm2 in a section): " + "; ".join(rows_)
       + "; in 3D, pushed sideways it meets the jamb stops before its side gap to the jambs closes: " + "; ".join(side_rows)
       + "; the bottom's free play turned out about the stops' top: " + ", ".join(f"{a_} {b_:.3f}" for a_, b_ in plays.items())
       + " mm (at most 0.15)")

# ---- 6.5 hand numbers
kf = {E_: E_ / 3000.0 / FIN_D[0] for E_ in (2500.0, 3500.0)}
Lt = s.TAB_ROOT - (s.TAB_BUMP_X0 + s.TAB_BUMP_X1) / 2
It = s.TAB_W * s.TAB_T ** 3 / 12
kt = (3 * 2500.0 * It / Lt ** 3 * TAB_ROOT_K[0], 3 * 3500.0 * It / Lt ** 3 * TAB_ROOT_K[1])
zc_ = (s.RAIL_Z0 + s.Z_FT) / 2
zt_ = s.Z_TT - s.TAB_W / 2
zb_ = s.ZF + 0.45
need_t = WEIGHT * (zc_ - zb_) / (zt_ - zb_)
ff = [2 * kf[E_] * D["fpre"] for E_ in (2500.0, 3500.0)]
ft = [2 * kt[0] * D["tpre"], 2 * kt[1] * D["tpre"]]
eps_stop = (FIN_D[2] * D["fbend_stop"], FIN_P[2] * P["fbend_stop"])
hl, hz, uc_ = s.HDL_LEG, s.HDL_HT, (s.HDL_U1 + s.HDL_U2) / 2
legF = [2 * 10.0 * (hl + 2 * f_) * (hz + f_) ** 2 / 6 / (uc_ - (s.RAIL_FACE + 0.2 * k_))
        for k_, f_ in enumerate(list(s.HDL_FILLET) + [0.0])]
gripF = 4 * 45 * (s.HDL_U2 - s.HDL_U1) * hz ** 2 / 6 / (2 * (s.HDL_HALF - hl / 2))
breakF = min(min(legF), gripF)
report(min(ff) > 1.5 * WEIGHT and min(ft) > 1.5 * need_t and max(eps_stop) < 2.0 and breakF >= 20,
       f"roll-up curtain holds ({s.CUR_WEIGHT_G} g, {WEIGHT:.4f} N), with the springs' real rates (fingers {FIN_D[0]:.3f} mm/N at "
       f"E 3000, the pad bearing on the tilted bump {A_D:.2f} from the finger's root, {A_P:.2f} as printed, k "
       f"{kf[2500.0]:.3f} to {kf[3500.0]:.3f}; tabs {TAB_ROOT_K[0]} of a clamped cantilever, k {kt[0]:.3f} to "
       f"{kt[1]:.3f} N/mm): upside down the fingers' {D['fpre']:.2f} drawn preload gives {ff[0]:.3f} to {ff[1]:.3f} N, "
       f"{ff[0] / WEIGHT:.2f} to {ff[1] / WEIGHT:.2f} times its weight (over 1.5); face down the tabs' {D['tpre']:.2f} gives "
       f"{ft[0]:.3f} to {ft[1]:.3f} N, {ft[0] / need_t:.2f} to {ft[1] / need_t:.2f} times the {need_t:.4f} N needed (over "
       f"1.5); finger strain at the rigid stop {eps_stop[0]:.2f} % drawn at a {D['fbend_stop']:.2f} bend ({FIN_D[2]:.3f} % a "
       f"mm), {eps_stop[1]:.2f} % as printed at {P['fbend_stop']:.2f} ({FIN_P[2]:.3f}) (under 2 %); the handle breaks "
       f"at about {breakF:.1f} N at 10 MPa across every layer (legs {', '.join(f'{x_:.1f}' for x_ in legF)} N on the 5.05 to "
       f"5.65 layers, grip {gripF:.1f} N), at least 20")
# not leaned in enough going back in (6.9), the door stops dead with its two tab bumps caught under the head's flat
# underside and the fingers not yet bent: a harder push goes through the tabs in their stiff, flat direction, the
# plate 0.65 by 2.2 bent edgewise, along its print lines (45 MPa), the load at the bump 9.0 from the root
tab_break = 45.0 * s.TAB_T * s.TAB_W ** 2 / 6 / Lt
lift_max = 2 * 3500.0 / 3000.0 / FIN_P[0] * P["fbend_stop"] + WEIGHT + 0.3 * 2 * kt[1] * P["tpre"]
report(tab_break >= lift_max,
       f"roll-up curtain pushed up with its tab bumps caught under the head (not leaned in enough going back in): each tab "
       f"breaks edgewise at about {tab_break:.1f} N (45 MPa along its lines), {2 * tab_break:.1f} N for the two: "
       f"{2 * tab_break / lift_max:.1f} times the hardest lift to the stop ({lift_max:.2f} N as printed at E 3500, its "
       f"weight and the tabs' friction too; at least 2): the read me says not to push harder when it stops dead")

# ---- 6.6 the lift window
# the room under the finger's tip: the slot from the finger strip's underside down to the rigid curtain under the
# finger itself (u 0 to TONGUE_T - 0.01, not the body in front of it), at x 20
i20p, i20d = cs_p.xs.index(20.0), cs_d.xs.index(20.0)
fsb = cs_p.c["fs"][i20p].bounds[1]
slot_p = fsb - cs_p.c["rig"][i20p].intersection(sbox(0, 0, s.TONGUE_T - 0.01, fsb - 0.01)).bounds[3]
fsb_d = cs_d.c["fs"][i20d].bounds[1]
slot_d = fsb_d - cs_d.c["rig"][i20d].intersection(sbox(0, 0, s.TONGUE_T - 0.01, fsb_d - 0.01)).bounds[3]
tip_d, tip_p = FIN_D[1] * D["fbend_stop"], FIN_P[1] * P["fbend_stop"]
grow_rows = [f"{k_[0]}/{k_[1]}: stop {r_['stop']:.2f}, least {r_['need']}, window {r_['window']:.2f}"
             for k_, r_ in cases.items() if not isinstance(k_, str)]
report(P["stop"] >= 1.0 and slot_d - tip_d >= 0.2 and slot_p - tip_p >= 0.2 and P["window"] >= 0.4
       and all(r_["window"] >= 0.3 for k_, r_ in cases.items()) and D["empty"] > 1e-4 and P["empty"] > 1e-4,
       f"roll-up curtain's lift: straight up it meets the rigid stop (its tongue's top on the rebate's top) at "
       f"{D['stop']:.2f} drawn and {P['stop']:.2f} as printed (at least 1.0); the finger bends {D['fbend_stop']:.2f} there "
       f"({P['fbend_stop']:.2f} printed), its tip ({FIN_D[1]:.3f} and {FIN_P[1]:.3f} times the bend where the pad bears) "
       f"{tip_d:.2f} in its {slot_d:.2f} slot drawn and {tip_p:.2f} in {slot_p:.2f} printed ({slot_d - tip_d:.2f} and "
       f"{slot_p - tip_p:.2f} spare, at least 0.2); the least lift that lets it out is {D['need']} drawn, {P['need']} printed, "
       f"so the window is {D['window']:.2f} and {P['window']:.2f} (at least 0.4 printed); " + "; ".join(grow_rows)
       + f" (each at least 0.3); not empty: lifted 0.3 and swung out 1 to 6 degrees it is blocked ({D['empty']:.3f} and "
       f"{P['empty']:.3f} mm2)")

# ---- 6.7 removal
ztop_all = -99.0
for nm_, r_ in (("drawn", D), ("printed", P)):
    cs_, pre_ = r_["cs"], r_["pre"]
    lifts_ = sorted(set([round(x_, 3) for x_ in np.arange(r_["need"], r_["stop"] + 1e-9, 0.1)] + [round(r_["stop"] - 0.15, 3),
                                                                                                    r_["stop"]]))
    worst = {"ov": 0.0, "fbend": 0.0, "tbend": 0.0, "strip": 0.0, "ztop": -99.0}
    tz_up = 0.0
    loft_r, loft_b = 99.0, 99.0
    for l_ in lifts_:
        for th_ in (6.0, 7.0, 8.0):
            ps_ = removal_poses(l_, th_, pre_)
            w_ = path_worst(cs_, ps_)
            for k_ in worst:
                worst[k_] = max(worst[k_], w_[k_])
            tz_up = max(tz_up, zmove_tab_rise(cs_, ps_[:10]), zmove_tab_rise(cs_, ps_[20:30]))
            g_ = cs_.named_gaps(ps_, {"loft": lambda i, x: cs_.other["front loft"][i]})
            loft_r = min(loft_r, g_.get("loft", 99.0))
            loft_b = min(loft_b, cs_.unbent_bump_gap(ps_, cs_.other["front loft"]))
    ztop_all = max(ztop_all, worst["ztop"])
    r_["tbend_path"] = worst["tbend"]
    report(worst["ov"] < 1e-4 and worst["fbend"] <= r_["fbend_stop"] + 1e-6 and worst["tbend"] <= 0.9 and worst["strip"] < 1e-4
           and tz_up < 1e-4 and loft_r >= 0.3 and loft_b >= 0.3,
           f"roll-up curtain comes out, {nm_}: lifted to each of {', '.join(f'{x_:.2f}' for x_ in lifts_)} (the least to the "
           f"stop, and the stop less 0.15), swung 6, 7 and 8 degrees about its front at the mouth, dropped TONGUE_UP + BUMP_H "
           f"+ the lift + 0.6 and pulled 15 out: no rigid overlap ({worst['ov']:.5f} mm2), the finger bent {worst['fbend']:.2f} at "
           f"most (at the stop {r_['fbend_stop']:.2f}), the tabs {worst['tbend']:.2f} (at most 0.9), the springs touching nothing "
           f"else ({worst['strip']:.5f}), no tab bump pushed in z ({tz_up:.5f}); the front loft {loft_r:.2f} from the rigid "
           f"curtain and {loft_b:.2f} from the unbent finger bumps at the closest (at least 0.3)")
    for l_ in sorted(set([1.0 if nm_ == "drawn" else 0.8, r_["need"], round(r_["stop"] - 0.15, 3)])):
        g_ = cs_.named_gaps(removal_poses(l_, 7.0, pre_)[10:], named_obstacles(cs_))
        g_["front loft (unbent finger bump)"] = cs_.unbent_bump_gap(removal_poses(l_, 7.0, pre_)[10:], cs_.other["front loft"])
        print(f"     least gaps after a {l_:.2f} lift, {nm_}: " + ", ".join(f"{a_} {b_:.2f}" for a_, b_ in g_.items()))

# ---- 6.8 the motions a hand makes
for nm_, r_ in (("drawn", D), ("printed", P)):
    cs_, pre_ = r_["cs"], r_["pre"]
    ls_ = [round(x_, 3) for x_ in np.arange(0.6, r_["stop"] - 0.1 + 1e-9, 0.1)] + [round(r_["stop"] - 0.1, 3)]
    ok_, rows_ = True, []
    for name in MOTIONS:
        row_ = []
        for l_ in sorted(set(ls_)):
            tc_, th_ = motion_ok(cs_, pre_, l_, name)
            ok_ &= th_ is not None
            row_.append(f"{l_:.2f}:{tc_}/{th_}")
        rows_.append(f"{name} " + " ".join(row_))
    report(ok_, f"roll-up curtain, the motions a hand makes, {nm_} (lift: first contact degrees / least swing that lets "
                f"it out): " + "; ".join(rows_))
ok_ = all(th_ is not None for k_, r_ in cases.items() if not isinstance(k_, str) for tc_, th_ in r_["m15"].values())
ok_ &= all(r_["rm15"] < 1e-4 for r_ in cases.values())
report(ok_, "roll-up curtain at the stop less 0.15 at every print growth: " + "; ".join(
    f"{k_[0]}/{k_[1]} lift {r_['stop'] - 0.15:.2f}: " + ", ".join(f"{a_.split(',')[0]} {b_[0]}/{b_[1]}" for a_, b_ in r_["m15"].items())
    + f", front pivot {r_['rm15']:.4f} mm2" for k_, r_ in cases.items() if not isinstance(k_, str)))

# ---- 6.9 putting it in
PHIS = [round(0.1 * k_, 1) for k_ in range(15)]
SWINGS = (6.0, 7.0, 8.0)
# leaned in, the door reaches its rigid stop tipped 5 to 9 degrees, and its 1.25 deep finger bump meets the pad with
# its front corner first, up to 0.1 higher than square (1.25 x sin 9 degrees = 0.2, half of it at the bump's middle):
# so going in the finger may bend up to FB_TILT more than at the straight-up stop. Its strain and its tip in the
# printed slot are proved at the most it bends, over the top of every pose that reaches a stop with a bump on its pad:
# every pose that goes in, and every one past the band whose bumps and pads still cross by 0.2 or more in u (the
# marginal poses the top-edge measure puts past the band). Further in, the bumps cross only the pads' back corners,
# and are pushed back from behind (the leaned-too-far lines below)
FB_TILT = 0.1
TAGS = {"works": "works", "catches": "catches", "blocked coming in": "blocked", "blocked going in": "BLOCKED",
        "leaned too far: its springs go in behind their pads": "behind-pads",
        "leaned too far: the top won't come out": "top-held",
        "leaned too far: a finger bump is not under its pad": "pad"}


def insert_all(r_, swings=SWINGS):
    """H.5 at every swing and lean tried, for a study r_: each with every lift in the window (the least + 0.1 to the stop
    less 0.15, by 0.2, and the stop less 0.15) and let down about a millimetre (not under the least + 0.05)."""
    cs_, pre_, need_, stop_ = r_["cs"], r_["pre"], r_["need"], r_["stop"]
    base_ = sorted(set([round(x_, 3) for x_ in np.arange(need_ + 0.1, stop_ - 0.15 + 1e-9, 0.2)] + [round(stop_ - 0.15, 3)]))

    def lifts_(top_):
        return base_ + [round(min(max(top_ - 1.0, need_ + 0.05), stop_ - 0.15), 3)]
    return {(th_, phi_): insertion(cs_, pre_, th_, phi_, lifts_, need=need_) for th_ in swings for phi_ in PHIS}


def band_of(res_, th=None):
    """The leans (the tongue's back at the mouth) that put it in, (least in, most in), at one swing or all."""
    w_ = [q_["lean"] for (t_, _), q_ in res_.items() if q_["result"] == "works" and (th is None or t_ == th)]
    return (max(w_), min(w_)) if w_ else (None, None)


bands, ins_bend = {}, {}
for nm_, r_ in (("drawn", D), ("printed", P)):
    res_ = insert_all(r_)
    r_["ins"] = res_
    bad_ = [k_ for k_, q_ in res_.items() if q_["result"] == "blocked going in"]
    fbmax_, zt_, tz_, st_ = 0.0, -99.0, 0.0, 0.0
    for k_, q_ in res_.items():
        if q_["result"] == "works":
            for L_, how_, w_ in q_["rows"]:
                fbmax_, zt_ = max(fbmax_, w_["fbend"]), max(zt_, w_["ztop"])
                tz_, st_ = max(tz_, w_.get("tz", 0.0)), max(st_, w_["strip"])
            zt_ = max(zt_, q_["ztop"])
        if q_["result"] == "works" or (q_["result"].startswith("leaned too far") and q_["fpa"] >= 0.2):
            fbmax_ = max(fbmax_, q_["fbend_top"])
    ins_bend[nm_] = fbmax_
    band_ = band_of(res_)
    bands[nm_] = band_
    ztop_all = max(ztop_all, zt_)
    noload = [res_[(th_, 0.0)]["result"] for th_ in SWINGS]
    for th_ in SWINGS:
        row_ = " ".join(f"{phi_}:{res_[(th_, phi_)]['lean']:+.2f}:{TAGS.get(res_[(th_, phi_)]['result'], '?')}" for phi_ in PHIS)
        print(f"     putting it in, {nm_}, swung {th_:.0f} degrees (lean: tongue back u at the mouth: result): {row_}")
    report(not bad_ and all(w_ == "catches" for w_ in noload) and band_[0] is not None and tz_ < 1e-4 and st_ < 1e-4,
           f"roll-up curtain goes back in, {nm_} (H.5: swung 6 to 8 degrees, the top leaned in a further 0 to 1.4 degrees, "
           f"pushed up until it stops, let down about 1 mm and to every lift in the window, the top let out and the bottom "
           f"swung in, one after the other and together, let go): with no lean it catches at every swing (a tab bump meets "
           f"the head's underside on the way up); leaned so the tongue's back is {band_[0] or 0:+.2f} to {band_[1] or 0:+.2f} at "
           f"the mouth it goes in with no rigid overlap, no tab bump touched by a move in z ({tz_:.5f} mm2), the springs "
           f"touching nothing else ({st_:.5f}), the finger bumps under their pads by 0.2 or more before the top comes out; "
           f"leaned further the finger bumps miss their pads{'' if not bad_ else ' (blocked: %s)' % bad_}")
fb_ins = max(ins_bend.values())
report(ins_bend["drawn"] <= D["fbend_stop"] + FB_TILT and ins_bend["printed"] <= P["fbend_stop"] + FB_TILT
       and FIN_P[2] * fb_ins < 2.0 and slot_p - FIN_P[1] * fb_ins >= 0.1,
       f"roll-up curtain going back in, over the top of every pose that reaches its stop with a bump on its pad (it goes "
       f"in, or past the band with bump and pad crossing by 0.2 or more): the fingers bend at most {ins_bend['drawn']:.2f} drawn and {ins_bend['printed']:.2f} "
       f"printed ({ins_bend['drawn'] - D['fbend_stop']:+.2f} and {ins_bend['printed'] - P['fbend_stop']:+.2f} on the "
       f"straight-up stop's {D['fbend_stop']:.2f} and {P['fbend_stop']:.2f}, at most {FB_TILT}: the bump tipped with the "
       f"door), {FIN_P[2] * fb_ins:.2f} % strain as printed (under 2 %), the tip {slot_p - FIN_P[1] * fb_ins:.2f} inside "
       f"the {slot_p:.2f} printed slot (at least 0.1)")
lo_c, hi_c = max(bands["drawn"][1] or 0, bands["printed"][1] or 0), min(bands["drawn"][0] or -9, bands["printed"][0] or -9)
per_sw = {}
for th_ in SWINGS:
    bd_, bp_ = band_of(D["ins"], th_), band_of(P["ins"], th_)
    per_sw[th_] = (bd_, bp_, (min(bd_[0], bp_[0]) - max(bd_[1], bp_[1])) if None not in bd_ + bp_ else 0.0)
report(hi_c - lo_c >= 0.4 and all(v_[2] >= 0.3 for v_ in per_sw.values()),
       f"roll-up curtain: the lean that puts it in, common to drawn and printed over the swings tried, is {hi_c:+.2f} to "
       f"{lo_c:+.2f} (tongue's back at the mouth), {hi_c - lo_c:.2f} wide (at least 0.4); at each swing: " + "; ".join(
           f"{th_:g} degrees {v_[0][0] or 0:+.2f} to {v_[0][1] or 0:+.2f} drawn, {v_[1][0] or 0:+.2f} to {v_[1][1] or 0:+.2f} "
           f"printed, {v_[2]:.2f} common" for th_, v_ in per_sw.items()) + " (each at least 0.3)")
# either side of the band. Not leaned in enough, it stops dead: the tab bumps caught under the head, short of where a
# leaned door stops and before the fingers bend, so with no spring to feel (pushed harder, the tabs take it edgewise,
# 6.5). Only poses leaned less than the band's top end count here: past the band's far end a tab bump can graze the
# rebate's ceiling as the door rises high, and that counts as stopped rigidly. Leaned in too far, the finger bumps come
# up behind their pads; at step 4 nothing rigid stops the top, which comes out pushing them back toward the room: the
# door then sits with no push down from its fingers and lifts with no spring. The fingers are thin that way (1.05), so
# that bend is mild; and nothing of the end wall stands behind its inside face round the opening (the rebate is open to
# the room), so held there the bumps touch only the pads' backs and the door lifts out as usual, and is put back leaning
# less (the read me's symptom and remedy; the loft has its own line below)
behind_wall = overlap(ru_piece, s.rbox(-H_ - 4, H_ + 4, -6, -0.001, s.ZF + 0.5, s.MOUTH + 8))
short_, catch_fb, over_ok, ub_most, n_behind, n_past = [], [], True, 0.0, 0, 0
for nm_, r_ in (("drawn", D), ("printed", P)):
    for th_ in SWINGS:
        bt_ = band_of(r_["ins"], th_)
        tops_ = [q_["top"] for (t_, _), q_ in r_["ins"].items() if t_ == th_ and q_["result"] == "works"]
        for phi_ in PHIS:
            q_ = r_["ins"][(th_, phi_)]
            if (q_["result"] == "catches" and q_["catch"] is not None and tops_ and bt_[0] is not None
                    and q_["lean"] > bt_[0] + 1e-9):
                short_.append(min(tops_) - q_["catch"][0])
                catch_fb.append(q_["catch"][1])
            if bt_[1] is not None and q_["lean"] < bt_[1] - 1e-9:      # past the band's far end
                n_past += 1
                over_ok &= q_["result"].startswith("leaned too far") or q_["result"] in ("blocked coming in", "catches")
                ub_most = max(ub_most, q_.get("u_bend", 0.0))
                n_behind += q_["result"] == "leaned too far: its springs go in behind their pads"
eps_u = EPS_U * ub_most
f_u = 3 * EI_U / A_D ** 3 * ub_most
n_blocked = sum(1 for r_ in (D, P) for q_ in r_["ins"].values() if q_["result"] == "blocked coming in")
report(over_ok and eps_u < 2.0 and behind_wall < 1e-6 and bool(short_) and min(short_ or [0]) >= 1.5,
       f"either side of the lean band, what Alan feels: not leaned in enough it stops dead {min(short_ or [0]):.1f} to "
       f"{max(short_ or [0]):.1f} mm short of where a leaned door stops, the fingers bent {min(catch_fb or [0]):.2f} to "
       f"{max(catch_fb or [0]):.2f} there (no spring), the tab bumps caught under the head; leaned in too far, the finger "
       f"bumps come up behind their pads ({n_behind} of the {n_past} poses past the band) and at step 4 nothing rigid "
       f"stops the top, which comes out pushing them back toward the room up to {ub_most:.2f} mm: it then sits with no "
       f"push down from its fingers and lifts with no spring. That bend is at most {eps_u:.2f} % strain and {f_u:.2f} N a "
       f"finger (the finger clamped at its root, which overstates both; under 2 %); nothing of the end wall stands behind "
       f"its inside face round the opening ({behind_wall:.6f} mm3), so held there the bumps touch only the pads' backs and "
       f"it lifts out as usual. Every pose past the band either does that, or is stopped rigidly: leaned in much too far "
       f"it won't come all the way in under the head, its chamfered back edges on the jamb stops' tops ({n_blocked} of the "
       f"poses tried)")

# ---- 6.10 roof and loft
hi_poses = [(D, dict(pre=D["pre"], L=D["stop"]))] + [(P, dict(pre=P["pre"], L=P["stop"]))]
for r_ in (D, P):
    for (th_, phi_), q_ in r_["ins"].items():
        if q_["result"] == "works":
            hi_poses.append((r_, dict(pre=r_["pre"], th=th_, pz=s.MOUTH + r_["pre"][1], phi=phi_, dz=q_["top"])))
roofed = s.union([front_loft, roof_all])
v3 = max(overlap(p["curtain"].transform(pose_3d(pose_mat(**q_))), roofed) for _, q_ in hi_poses)
report(ztop_all <= 65.1 and v3 < 0.001,
       f"roll-up curtain under the roof: nothing of it rises over z {ztop_all:.2f} taking it out or putting it in (at most "
       f"65.1), with the roof on; at its {len(hi_poses)} highest poses the whole curtain, springs unbent, overlaps the front "
       f"loft and roof sheets by {v3:.5f} mm3 (under 0.001)")

# ---- 6.9 again: leaned in too far. Past the band the finger bumps come up beside their pads, not under them, and the top
# still comes out: each pad's back face bends its finger sideways (in u), which the sections can't count as a spring. A
# finger strip is only 1.44 times stiffer in z than in u (review, Nov 3 2026), so that is not a stop you feel. Seated so,
# the fingers hold nothing down, and what tells it is that, lifted a little and let go, it doesn't snap back down
ok_, rows_ = True, []
for nm_, r_ in (("drawn", D), ("printed", P)):
    cs_, pre_ = r_["cs"], r_["pre"]
    fin_ = FIN_D if nm_ == "drawn" else FIN_P
    ix_ = cs_._idx()["fb"]
    far_ = [(k_, q_) for k_, q_ in r_["ins"].items() if q_["result"].startswith("leaned too far")]
    if not far_:
        rows_.append(f"{nm_}: no lean tried goes in too far without being stopped coming in")
        continue
    us_far = [q_["lean"] for _, q_ in far_]
    rig_top, bump_top, loft_d, low_bot, zb_max, rig3, ub_ = -99.0, -99.0, 0.0, 99.0, 0.0, 0.0, 0.0
    for (th_, phi_), q_ in far_:
        pz_ = s.MOUTH + pre_[1]
        M_ = pose_mat(pre=pre_, th=th_, pz=pz_, phi=phi_, dz=q_["top"])
        rig_top = max(rig_top, float(np.nanmax(shapely.bounds(moved_secs(cs_.c["rig"], M_))[:, 3])))
        fbm_ = moved_secs(cs_.c["fb"][ix_], M_)
        bump_top = max(bump_top, float(np.nanmax(shapely.bounds(fbm_)[:, 3])))
        for g_ in shapely.intersection(fbm_, cs_.other["front loft"][ix_]):
            if not g_.is_empty and g_.area > 1e-7:
                loft_d = max(loft_d, g_.bounds[3] - g_.bounds[1])
        zb_max = max(zb_max, q_["fbend_top"])
        ub_ = max(ub_, q_.get("u_bend", 0.0))
        Md_ = pose_mat(pre=pre_, th=th_, pz=pz_, phi=phi_, dz=q_["top"] - 1.0)
        low_bot = min(low_bot, float(np.nanmin(shapely.bounds(moved_secs(cs_.c["fb"][ix_], Md_))[:, 1])))
        if th_ == 7.0:
            rig3 = max(rig3, overlap(rig_only.transform(pose_3d(M_)), roofed))
    fbs_ = shapely.bounds(moved_secs(cs_.c["fb"][ix_], pose_mat(pre=pre_)))
    D_ = max(fbs_[j_, 2] - cs_.pad_u[i_][0] for j_, i_ in enumerate(ix_) if not cs_.pads[i_].is_empty)
    Du_ = max(D_, ub_)                                            # the sideways bend: seated, or on the way out (step 4)
    F_ = (ku[0] * D_, ku[1] * D_)
    ft_ = (2 * kt[0] * r_["tpre"], 2 * kt[1] * r_["tpre"])
    mis_net = WEIGHT - 0.2 * (2 * F_[0] + ft_[0])                 # let go, seated so: its weight against the least friction
    good_net = 2 * kf[2500.0] * (r_["fpre"] + 1.0) + WEIGHT - 0.4 * ft_[1]   # seated right, 1 mm up: the least push down
    slot_ = slot_d if nm_ == "drawn" else slot_p
    ok_ &= (rig_top <= 65.1 and rig3 < 0.001 and loft_d <= 0.3 and fin_[2] * zb_max < 2.0 and EPS_U * Du_ < 2.0
            and good_net >= 5 * max(mis_net, 0.0) and good_net >= 0.3)
    rows_.append(f"{nm_}, leaned so the tongue's back is {max(us_far):+.2f} to {min(us_far):+.2f} at the mouth: it goes up "
                 f"with nothing rigid in the way, the door itself to z {rig_top:.2f} and off the loft and roof ({rig3:.5f} mm3), its "
                 f"springy finger bumps to {bump_top:.2f}, into the loft's end joist {loft_d:.2f} at most (they bend; at most "
                 f"0.3), each finger bent {zb_max:.2f} at most in z ({fin_[2] * zb_max:.2f} %, its tip {fin_[1] * zb_max:.2f} in "
                 f"its {slot_:.2f} slot; more and it lands on the body top, a stop); let down 1 mm the bumps' bottoms are at "
                 f"z {low_bot:.2f}, over the pads' bottom {s.PAD_Z:.3f}, so pushed home each pad's back face bends its finger "
                 f"{D_:.2f} sideways ({ub_:.2f} on the way out), {F_[0]:.2f} to {F_[1]:.2f} N (sideways rate {ku[0]:.3f} to "
                 f"{ku[1]:.3f} N/mm), {EPS_U * Du_:.2f} % strain: no stop you feel; seated so, let go 1 mm up it is pushed down "
                 f"{max(mis_net, 0.0):.3f} N at most (its weight less friction), seated right at least {good_net:.2f} N")
report(ok_, "roll-up curtain leaned in too far, past the band (H.5): " + "; ".join(rows_) + "; so the read me's test after "
            "putting it in: lift it a little by the handle and let go, it must snap back down (under 2 % strain anywhere, "
            "nothing breaks; take it out the usual way and put it back leaning less)")

# ---- the moved steel door and its casing, and the hand that lifts the curtain (standard layout: the walk door is
# on the door side next to the roll-up end, its edge 4 ft in from the corner)
far_ = removal_poses(D["need"], 8.0, D["pre"])[-1]
cur_far = p["curtain"].transform(pose_3d(pose_mat(**far_)))
cur_top = p["curtain"].transform(pose_3d(pose_mat(pre=D["pre"], L=D["stop"])))
door_sw = [door.transform(s.door_to_shed(dg)) for dg in (0, 45, 90)]
casing_ds = p["door side"] ^ zone
g_door = min(c_.min_gap(d_, 40.0) for c_ in (p["curtain"], cur_far, cur_top) for d_ in door_sw + [casing_ds])
hand = s.rbox(-20, 20, s.WT + s.PROUD + 0.05, s.WT + 40, -(s.SKID_H - s.NOTCH), 35)
rest_ = s.union([body, roof_all, loft_set] + door_sw + [k_ for _, k_ in skids_placed] +
                [s.corner_angle(sx_, sy_) for sx_, sy_ in s.CORNERS])
in_hand = overlap(rest_, hand)
grip_in = overlap(p["curtain black"], hand)
white_in = overlap(p["curtain white"], hand)
g_hand = min(hand.min_gap(d_, 40.0) for d_ in door_sw + [casing_ds])
report(g_door >= 10 and in_hand < 1e-6 and grip_in > 10 and white_in < 1e-6 and g_hand >= 10,
       f"roll-up curtain and the moved steel door: seated, at its stop and pulled out, the curtain keeps {g_door:.1f} mm or "
       f"more from the steel door (shut, or swung in 45 or 90 degrees) and its casing; the room a hand needs in front of the "
       f"doorway's bottom middle (40 x 40 mm out from the casing face, from the table up to 35 mm) holds nothing but the "
       f"curtain's black handle ({grip_in:.1f} mm3 of it; {in_hand:.6f} mm3 of anything else, the door, its casing, the "
       f"corner angles, skids and roof included), and it is {g_hand:.1f} mm from the door and its casing")
# the room for a fingernail behind the grip, and for a fingertip under it (review, Nov 3 2026: nothing measured it), read
# off the curtain's print layers at the handle's middle and half way up the grip
xm_ = cbb[0] + s.CUR_HALF
ym_ = cbb[1] + s.RAIL_Z0 + s.HDL_HT / 2 - (s.ZF + s.G_BOT)
col_l = [(z0_, z1_, (cpr.slice((z0_ + z1_) / 2) ^ m3.CrossSection.square([0.02, 0.02]).translate([xm_ - 0.01, ym_ - 0.01]))
          .area() > 1e-6) for z0_, z1_ in layers(cbb[5])]
i0_ = next((i_ for i_, c_ in enumerate(col_l) if not c_[2]), len(col_l))          # the first empty layer over the rail
i1_ = next((i_ for i_ in range(i0_, len(col_l)) if col_l[i_][2]), None)            # the grip's first layer
emp_ = col_l[i0_:i1_] if i1_ is not None else []
nail_d = sum(z1_ - z0_ for z0_, z1_, _ in emp_)
grip0 = col_l[i1_][0] if i1_ is not None else 0.0
rail0 = col_l[i0_][0] if i0_ < len(col_l) else 0.0


def gap_x(zm):
    """The empty run along x through the handle's middle on the layer at print height zm (mm)."""
    st_ = cpr.slice(zm) ^ m3.CrossSection.square([30, 0.02]).translate([xm_ - 15, ym_ - 0.01])
    xs_ = [q.bounds() for q in st_.decompose() if q.area() > 1e-7]
    return (min([b_[0] for b_ in xs_ if b_[0] >= xm_] + [xm_ + 15]) - max([b_[2] for b_ in xs_ if b_[2] <= xm_] + [xm_ - 15]))


w_top_, w_root_ = gap_x(s.HDL_U1 - 0.1), gap_x(s.RAIL_FACE + 0.1)
h_skid = s.RAIL_Z0 + s.SKID_H - s.NOTCH
under_ = s.rbox(-s.HDL_HALF, s.HDL_HALF, s.WT + 0.02, s.HDL_U2, -(s.SKID_H - s.NOTCH), s.RAIL_Z0 - 0.02)
under_v = overlap(s.union([rest_, p["curtain"]]), under_)
report(nail_d - 0.2 >= 1.2 and abs(grip0 - s.HDL_U1) < 1e-6 and abs(rail0 - s.RAIL_FACE) < 1e-6 and w_top_ >= 4.5
       and min(h_skid, s.RAIL_Z0) >= 7.0 and under_v < 1e-6,
       f"roll-up curtain's handle has room for a fingernail behind its grip: as printed, {len(emp_)} empty layers "
       f"({nail_d:.2f} mm) between the rail's top at {rail0:.2f} and the grip's first layer at {grip0:.2f}, {nail_d - 0.2:.2f} if that bridge sags "
       f"0.2 (at least 1.2), {w_top_:.2f} wide between the legs ({w_root_:.2f} on the 5.05 layer, between the fillets; at "
       f"least 4.5); and for a fingertip under it: nothing at all under the grip in front of the siding ({under_v:.6f} mm3), "
       f"{h_skid:.2f} mm down to the table on the skids and {s.RAIL_Z0:.2f} on the fit test's half doorway, which stands on its "
       f"skirt (at least 7)")

# the floor and the lofts print upside down: their face is on the bed, and nothing hangs over more
# than 45 degrees (the joists, bands, lugs and slots all stand straight up from it)
for name, piece, mat in (("floor", fl, s.FLOOR_TO_PRINT), ("loft", p["loft"], s.LOFT_TO_PRINT)):
    ff = s.to_print(mat, [piece])[0]
    fbb = ff.bounding_box()
    foot = ff.slice(0.125).area()
    worst, prev = 0.0, None
    for z in [0.125] + [0.35 + 0.2 * k for k in range(int(fbb[5] / 0.2))]:
        if z > fbb[5]:
            break
        cs = ff.slice(z)
        if prev is not None:
            worst = max(worst, (cs - prev.offset(0.22, m3.JoinType.Miter, 10)).area())
        prev = cs
    report(foot > 0.95 * (fbb[3] - fbb[0]) * (fbb[4] - fbb[1]) - 400 and worst < 0.5,
           f"the {name} prints face down ({foot:.0f} mm2 on the bed), nothing hanging over ({worst:.3f} mm2 worst layer)"
           + ("; each lug stands straight up off its joist" if name == "loft" else ""))
lbb = lofts[0].bounding_box()
yc = (lbb[1] + lbb[4]) / 2
for i, lf in enumerate(lofts):
    v = overlap(body, lf) + overlap(roof_all, lf) + overlap(door_shut, lf)
    v2 = overlap(body, lf.translate([0, 0, -0.1]))
    v3 = min(overlap(body, lf.translate(t)) for t in ([0.3, 0, 0], [-0.3, 0, 0], [0, 0.3, 0], [0, -0.3, 0]))
    worst = sweep(lf, s.union([longs, door_shut]), [[0, 0, dz] for dz in np.arange(0.1, 60.01, 0.1)])
    report(v < 0.01 and v2 > 0.5 and v3 > 0.05 and worst < 1e-3,
           f"loft {i + 1} fits between the walls and under the roof ({v:.4f} mm3), rests on the long walls' top plates "
           f"({v2:.1f} mm3 lowered 0.1), can't slide ({v3:.2f} mm3 moved 0.3 mm any way: its lugs in the notches), and "
           f"drops in from 60 mm with both long walls on and the door hung, touching nothing ({worst:.4f} mm3)")
lf = lofts[0]
turned = lf.translate([0, -yc, 0]).rotate([0, 0, 180]).translate([0, yc, 0])
v = overlap(body, turned)
v2 = overlap(body, turned.translate([0, 0, -0.1]))
report(v < 0.01 and v2 > 0.5, f"a loft goes in either way round: turned end for end it fits the same notches "
                              f"({v:.4f} mm3 in place, {v2:.1f} mm3 lowered 0.1 mm)")
rise = 0.0
while rise < 3 and overlap(roof_all, lf.translate([0, 0, rise + 0.02])) < 1e-4:
    rise += 0.02
report(rise < s.LUG_D - 0.3, f"with the roof on, a loft can only rise {rise:.2f} mm before it meets the roof, under "
                             f"LUG_D - 0.3 = {s.LUG_D - 0.3:.3f}, so its {s.LUG_D:.3f} mm lugs stay in their notches")
for i, (lf_, en) in enumerate(((lofts[0], "back end"), (lofts[1], "roll-up end"))):
    sgn = 1 if i == 0 else -1
    slide = 0.0
    while slide < 2 and overlap(longs, lf_.translate([0, sgn * (slide + 0.02), 0])) < 1e-4:
        slide += 0.02
    worst = sweep(p[en], lf_.translate([0, sgn * slide, 0]), [[0, 0, dz] for dz in DROPS] + [[0, 0, 0]])
    b_ = lf_.bounding_box()
    gap_end = (s.L / 2 - s.WT) - (b_[4] if sgn > 0 else -b_[1]) - slide
    report(worst < 1e-3 and gap_end >= 0.15,
           f"loft {i + 1} slides {slide:.2f} mm toward its end at most, and even there the {en} comes down past it with "
           f"{gap_end:.2f} mm to spare ({worst:.4f} mm3)")
# the front loft at the moved door (the addendum: the door's header and kings against the front loft's notches
# and lugs): both are 4 ft in from the roll-up end, so the loft's deck stops right where the doorway starts, and its
# edge joist's lug on the door side drops into a notch in the top plates over the door's hinge-side king stud. The notch stops at the top plates' underside, so the door's header and full
# stud under it stay whole, and the lug stays clear of the header, the top pin and its hole
lug_parts = (lofts[1] ^ s.box(s.W / 2 - s.WT, s.W / 2, -s.L / 2, 0, -1, s.LOFT_Z - 0.01)).decompose()
hf0, hk1 = STD_DOOR[0] - 2 * s.SW, STD_DOOR[0]                             # hinge side: full stud, then king stud
over = [c for c in lug_parts if c.volume() > 1e-3 and c.bounding_box()[1] < hk1 + 0.5 and c.bounding_box()[4] > hf0]
lb_ = over[0].bounding_box() if len(over) == 1 else [0] * 6
hdr_top = s.ZF + s.DOOR_OPEN_H + s.FLAT_HEADER
hole_top = s.ZF + s.DOOR_OPEN_H + s.HOLE_TOP_DEPTH
sz1_ = s.ZWT - s.PLATE_TOP
n0_, n1_ = lb_[1] - s.FIT, lb_[4] + s.FIT                                  # the notch along the wall
xi_, ds_ = s.W / 2 - s.WT, p["door side"]
hdr_r = s.box(xi_ + 0.05, xi_ + s.SD - 0.05, max(n0_, hf0 + s.SW), min(n1_, hk1 - 0.05), hdr_top - 0.5,   # over the
              hdr_top - 0.05)                                       # king stud, short of the top pin's hole
ful_r = s.box(xi_ + 0.05, xi_ + s.SD - 0.05, n0_, hf0 + s.SW - 0.05, sz1_ - 1.0, sz1_ - 0.05)   # (STD_DOOR is to 0.001)
whole_ = min(overlap(ds_, hdr_r) / hdr_r.volume(), overlap(ds_, ful_r) / ful_r.volume())
gap_l = over[0].min_gap(ds_, 1.0) if over else 0
loft_edge = lofts[1].bounding_box()[4]                                    # both 4 ft in from the roll-up end
report(len(over) == 1 and lb_[1] < hk1 and lb_[4] > hk1 - s.SW and lb_[2] - hdr_top >= 0.5 and lb_[2] - hole_top >= 0.5
       and lb_[2] > sz1_ and whole_ > 0.999 and gap_l >= 0.15 and abs(loft_edge - hk1) < 1e-3,
       f"the front loft ends where the door begins (its edge at {loft_edge:.3f}, the doorway's hinge edge at {hk1:.3f}): "
       f"its edge joist's lug on the door side ({lb_[1]:.3f} to {lb_[4]:.3f}) stands over the "
       f"door's hinge-side king stud ({hk1 - s.SW:.3f} to {hk1:.3f}), its bottom {lb_[2] - hdr_top:.2f} mm over the door's "
       f"header, {lb_[2] - hole_top:.2f} over the top pin's hole and {lb_[2] - sz1_:.2f} over the top plates' underside, "
       f"{gap_l:.2f} mm clear of the wall; its notch leaves the header and full stud under it whole ({whole_ * 100:.1f}%)")


# ======================================================================== 7
group("7 steel door")


def door_checks(label, dr, wall, to_shed, extra, full_name):
    """Shut fit, swing in, the stop, and the hang for a door dr (print coords) in wall."""
    closed = overlap(wall, dr.transform(to_shed(0)))
    last_free, hit_at = 0.0, None
    around_ = s.union([wall] + extra)
    for deg in np.arange(0.0, 130.01, 0.5):
        vv_ = overlap(around_, dr.transform(to_shed(deg)))
        if vv_ < 0.01:
            last_free = deg
        else:
            hit_at = deg
            break
    vstop = overlap(wall, dr.transform(to_shed(-2)))
    report(closed < 0.01 and last_free >= 90 and vstop > 0.05,
           f"{label}: shut it fits its opening ({closed:.4f} mm3), swings IN freely to {last_free:.1f} degrees"
           f"{f' (at {hit_at:.1f} it meets {full_name})' if hit_at is not None else ''}, and swung 2 degrees out it "
           f"meets the stop on the latch jamb ({vstop:.2f} mm3)")
    return last_free


def hang_checks(label, dr, wall, mat0, top_z, need_lift=None):
    """The hanging path on the loose wall (no floor): top pin up the head hole, the door pushed up, its
    bottom pin's centre 2.8 inside the pin line, swung out along the trench in 0.25 mm steps to the
    pin line and dropped. Tried pushed up 0.2 to 0.7 in 0.025 steps: the lifts at which every step is
    clear say how far to push it up. Not empty: lifted 0.65 it meets the head, and the same swing not
    lifted runs the pin into the sill under the trench floor."""
    piv = top_z                                         # the top pin pivots at the head
    h = piv - (mat0[2, 3] - s.PIN_BOTTOM_LEN / 2)       # down to the bottom pin's middle
    steps = list(np.arange(2.8, 0.0, -0.25)) + [0.0]

    def worst_on(lift):
        w_ = max(overlap(wall, dr.transform(s.hang_pose(mat0, lift, d, piv, h))) for d in steps)
        return max([w_] + [overlap(wall, dr.transform(s.hang_pose(mat0, l, 0.0, piv, h)))
                           for l in np.arange(lift - 0.05, -0.001, -0.05)])
    lifts = [round(l, 3) for l in np.arange(0.2, 0.7001, 0.025)]
    good = [l for l in lifts if worst_on(l) < 0.01]
    lo_, hi_ = (min(good), max(good)) if good else (0.0, 0.0)
    whole = bool(good) and good == [l for l in lifts if lo_ - 1e-9 <= l <= hi_ + 1e-9]
    use = need_lift if need_lift is not None else round(math.floor((lo_ + hi_) / 2 / 0.025 + 0.5) * 0.025, 3)
    pin = s.cyl_y(0, -s.PIN_BOTTOM_LEN, 0.5, s.DOOR_R, s.PIN_D, 40)
    dh = mat0[2, 3]
    slab = dr ^ s.box(-10, 60, -0.01, top_z - dh - s.DOOR_TOP_GAP + 0.001, -10, 10)   # the door less its top pin
    floor_t = dh - s.DOOR_BOTTOM_GAP - s.TRENCH_DEPTH
    trench_m = min(pin.transform(s.hang_pose(mat0, use, d, piv, h)).bounding_box()[2] - floor_t for d in steps)
    head_m = min(piv - slab.transform(s.hang_pose(mat0, use, d, piv, h)).bounding_box()[5] for d in steps)
    tilt0 = math.degrees(math.asin(2.8 / h))
    head = overlap(wall, dr.transform(s.hang_pose(mat0, 0.65, 0.0, piv, h)))
    nolift = max(overlap(wall, dr.transform(s.hang_pose(mat0, 0.0, d, piv, h))) for d in (2.8, 2.05, 1.3))
    report(whole and any(abs(use - l) < 1e-6 for l in good) and hi_ - lo_ >= 0.1 - 1e-9 and head > 0.01 and nolift > 0.01,
           f"{label}: hangs on the loose wall, no floor: pushed up {use:.3f}, its bottom pin's middle 2.8 inside the pin "
           f"line (tilted {tilt0:.2f} degrees), swung out along the trench in 0.25 mm steps and dropped, every step clear, "
           f"{trench_m:.2f} mm over the trench floor and {head_m:.2f} under the head at the closest; any push from "
           f"{lo_:.3f} to {hi_:.3f} mm works; not empty: lifted 0.65 it meets the head ({head:.2f} mm3), and the same swing "
           f"not lifted runs the pin into the sill under the trench floor ({nolift:.2f} mm3)")
    return h


ds = p["door side"]
inside_stuff = [fl, loft_set, s.union([p[n] for n in ("plain side", "roll-up end", "back end")])]
door_checks("steel door", door, ds, s.door_to_shed, inside_stuff, "the hinge-side king stud's inside corner")
v = overlap(s.union(inside_stuff + [ds]), s.union([door.transform(s.door_to_shed(dg)) for dg in range(0, 91, 3)]))
report(v < 0.01, f"steel door: swinging in to 90 degrees it clears the floor, the front loft's edge over its hinge, the rest of the door "
                 f"side and the other walls ({v:.4f} mm3)")
mat0 = s.door_to_shed(0)
top_z = s.ZF + s.DOOR_OPEN_H
ds_near = ds ^ s.box(s.W / 2 - s.WT - 3, s.W / 2 + 1, s.DOOR_YC - s.JAMB - 4, s.DOOR_YC + s.JAMB + 4, -1, s.ZWT + 1)
h_door = hang_checks("steel door", door, ds_near, mat0, top_z, need_lift=0.5)
# the pin holes stay off the bed face, and the door side's first layer is whole over them
hb = s.door_holes()
low_u = min(u_range("door side", hh)[0] for hh in hb[:2])
reg = s.box(s.W / 2 - s.WT, s.W / 2 - s.WT + 0.3, s.AXIS_Y - 1.35, s.AXIS_Y + 1.35, s.ZF - 1.0, s.ZF - 0.7)
reg_t = s.box(s.W / 2 - s.WT, s.W / 2 - s.WT + 0.3, s.AXIS_Y - 1.35, s.AXIS_Y + 1.35,     # in the flat header (the
              s.ZF + s.DOOR_OPEN_H, s.ZF + s.DOOR_OPEN_H + s.FLAT_HEADER)                  # hole breaks 0.08 past it)
regs = reg + reg_t
big = s.box(s.W / 2 - s.WT - 1, s.W / 2 - s.WT + 0.3, s.AXIS_Y - 6, s.AXIS_Y + 6, s.ZF - 4, s.ZF + s.DOOR_OPEN_H + 4)
pr = printed_in_shed(ds, s.WALL_TO_PRINT["door side"], big)
first = s.box(s.W / 2 - s.WT, s.W / 2 - s.WT + 0.25, -s.L, s.L, -10, 200)
cov = overlap(pr ^ first, regs)
want = (regs ^ first).volume()
report(abs(low_u - 0.25) < 1e-6 and cov > 0.97 * want,
       f"steel door: its pin holes reach down only to u {low_u:.3f}, the top of the first layer, and as printed the door "
       f"side's first layer is whole over them ({cov:.3f} of {want:.3f} mm3; the trench opens to the room above "
       f"{s.ZF - s.TRENCH_DEPTH:.2f})")
# captive once the door side is on the floor: nothing cut in the floor over the trench's mouth, and to
# get its bottom pin up over the floor top the door would have to tip in until the pin is deep in the floor
mouth = s.box(s.W / 2 - s.WT - 3, s.W / 2 - s.WT - 0.25, s.AXIS_Y - 1.35, s.AXIS_Y + 1.35, s.ZF - 0.7, s.ZF - 0.01)
solid = overlap(fl, mouth) / mouth.volume()
lift_max = 0.0
while lift_max < 1 and overlap(ds, door.transform(s.hang_pose(mat0, lift_max + 0.01, 0, top_z, h_door))) < 1e-3:
    lift_max += 0.01
pin = s.cyl_y(0, -s.PIN_BOTTOM_LEN, 0.5, s.DOOR_R, s.PIN_D, 40)
first_up, far = None, None
for ang in np.arange(0, 20.01, 0.25):
    d = h_door * math.sin(math.radians(ang))
    pb = pin.transform(s.hang_pose(mat0, lift_max, d, top_z, h_door)).bounding_box()
    if pb[2] >= s.ZF:
        first_up, far = ang, (s.W / 2 - s.WT - s.FIT) - pb[3]
        break
report(solid > 0.999 and first_up is not None and far > 2,
       f"steel door: once the door side is on the floor it is captive: the floor is solid over the trench's mouth "
       f"({solid * 100:.1f}%), and lifted all it can go ({lift_max:.2f} mm) its bottom pin only gets up to the floor top "
       f"tipped {first_up:.2f} degrees toward the room, with its far edge {far:.2f} mm inside the floor's edge")
shut_u = u_range("door side", door_shut)
report(shut_u[1] < s.WT and shut_u[0] >= s.DOOR_AXIS_U - s.DOOR_R - 1e-6,
       f"steel door: shut, it stays inside the door side's thickness (u {shut_u[0]:.2f} to {shut_u[1]:.2f}, knob included), "
       f"nothing past the siding face at {s.WT:.3f}")
# its six panels where the designer's door-steel.js draws them (xs = dL + w * 0.170 ..., p = yb + h * fraction): fractions
# of the OPENING, across from its hinge-side jamb (-y) and up from the floor, typed in here, as the 12x24 Garage's door
# has them (final audit, Nov 4 2026: they were fractions of the slab, up to 0.55 mm off). Read off the shut door 0.2 mm
# under its outside face, where each panel's groove shows as a ring
DS_COLS = (0.170, 0.435, 0.565, 0.830)
DS_ROWS = (0.064, 0.300, 0.369, 0.758, 0.822, 0.945)
DS_OPEN_H = 75.6 * 25.4 / 36                # the builder's 36 x 75.6 in door (Alan: "Keep builder sizes"), at 1:36
x_out = s.AXIS_X + s.DOOR_R                 # the shut door's outside face
cs_door = door_shut.transform(np.array([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0]], dtype=float)).slice(x_out - 0.2)
rings = []
for loop in cs_door.to_polygons():
    q_ = np.asarray(loop)
    if 0.5 * np.sum(q_[:, 0] * np.roll(q_[:, 1], -1) - np.roll(q_[:, 0], -1) * q_[:, 1]) < 0:   # a hole: a groove's outside
        rings.append((q_[:, 0].min(), q_[:, 0].max(), q_[:, 1].min(), q_[:, 1].max()))
ys_ = sorted({round(v_, 4) for r_ in rings for v_ in r_[:2]})
zs_ = sorted({round(v_, 4) for r_ in rings for v_ in r_[2:]})
want_y = [STD_DOOR[0] + c_ * (STD_DOOR[1] - STD_DOOR[0]) for c_ in DS_COLS]
want_z = [s.ZF + r_ * DS_OPEN_H for r_ in DS_ROWS]
p_err = (max([abs(a_ - b_) for a_, b_ in zip(ys_, want_y)] + [abs(a_ - b_) for a_, b_ in zip(zs_, want_z)])
         if len(ys_) == 4 and len(zs_) == 6 else math.inf)
report(len(rings) == 6 and p_err <= 0.01,
       f"steel door: its {len(rings)} panels are where the designer draws them, the grooves' outer edges at "
       f"{', '.join(f'{c_:.3f}' for c_ in DS_COLS)} of the 36 in opening from its hinge-side jamb and "
       f"{', '.join(f'{r_:.3f}' for r_ in DS_ROWS)} of its 75.6 in from the floor, within {p_err:.4f} mm (at most 0.01): "
       f"the 12x24 Garage's door")
# the fit test's short doorway and door, as drawn and as printed
fd, fdw = s.fit_door(), s.fit_doorway()
fmat0 = s.fit_door_to_shed(0)
ftop = s.FIT_ZF + s.FIT_OH
door_checks("fit test door, as drawn", fd, fdw, s.fit_door_to_shed, [], "the hinge-side jamb")
hang_checks("fit test door, as drawn", fd, fdw, fmat0, ftop)
fdw_p = printed_in_shed(fdw, s.WALL_TO_PRINT["door side"], s.box(-BED, BED, -BED, BED, -BED, BED))
fbb = fd.bounding_box()
fd_p = as_printed(fd.translate([-fbb[0], -fbb[1], -fbb[2]])).translate([fbb[0], fbb[1], fbb[2]])
door_checks("fit test door, as printed", fd_p, fdw_p, s.fit_door_to_shed, [], "the hinge-side jamb")
hang_checks("fit test door, as printed", fd_p, fdw_p, fmat0, ftop)


# ======================================================================== 8
group("8 roof")
for name, sh in sheets.items():
    v = overlap(body, sh)
    report(v < 0.01, f"the {name} sits on the barn ends without cutting into the body ({v:.4f} mm3)")
names = list(sheets)
worst = max(overlap(sheets[a], sheets[b]) for i, a in enumerate(names) for b in names[i + 1:])
report(worst < 0.001, f"no roof sheet overlaps another, at the ridge or where they lap ({worst:.4f} mm3)")
_, nu = s.seg_line("upper", 1)
_, nl = s.seg_line("lower", 1)
dl = np.array([nl[1], -nl[0]])
du = np.array([nu[1], -nu[0]])
N3 = np.array([nl[0], 0, nl[1]])
inside = s.union([body, loft_set])
v = overlap(body, upper.translate([0, 0, -0.3]))
v2 = overlap(body, lower.translate(-0.3 * N3))
report(v > 0.5 and v2 > 0.5, f"lowered 0.3 mm an upper sheet runs into the barn ends ({v:.1f} mm3), and pushed 0.3 mm in "
                             f"square to its slope a lower sheet runs into their steep edges ({v2:.1f} mm3): they rest on them")
lift = 0.05 * np.array([nu[0], 0, nu[1]])
va = overlap(body, upper.translate(lift + [0, 1.0, 0]))
vd = overlap(body, upper.translate(lift + [du[0], 0, du[1]]))
report(min(va, vd) > 0.05, f"slid 1 mm along the garage ({va:.2f}) or down its slope ({vd:.2f} mm3), an upper sheet is "
                           f"held by its pegs")
lift = np.array([0, 0, 0.05])
va = overlap(body, lower.translate(lift + [0, 1.0, 0]))
vd = overlap(body, lower.translate(lift + 0.3 * np.array([dl[0], 0, dl[1]])))
vo = overlap(body, lower.translate(0.3 * N3))
top = np.array([s.LOWER_A[0], 0, s.LOWER_A[1]])
a = math.radians(-2)
R = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
vs_ = overlap(body, lower.transform(np.column_stack([R, top - R @ top])))
report(min(va, vd, vo, vs_) > 0.05,
       f"a lower sheet is held by its pegs when slid 1 mm along the garage ({va:.2f}), 0.3 mm down its slope ({vd:.2f}) "
       f"or 0.3 mm straight out ({vo:.2f}), or with its bottom swung out 2 degrees ({vs_:.2f} mm3)")
worst = sweep(lower, inside, [[0, 0, dz] for dz in np.arange(0, 20.01, 0.1)])
report(worst < 1e-3, f"a lower sheet goes on and lifts off straight up, touching nothing from 20 mm up ({worst:.4f} mm3)")
h = 0.0
while h < 3 and overlap(upper, lower.translate([0, 0, h + 0.02])) < 1e-4:
    h += 0.02
held = overlap(body, lower.translate([0, 0, h]).translate(0.3 * np.array([dl[0], 0, dl[1]])))
report(h < 1.0 and held > 0.05, f"with the upper sheet on, its tail is in the way of the lower sheet's only way off: lifted "
                                f"{h:.2f} mm the lower sheet meets it, still down on its pegs ({held:.2f} mm3), so it is locked on")


def printed_sheet(piece, a, b):
    """as_printed() of a +x roof sheet laid flat the way panel_to_print lays it, put back on the garage."""
    mat = s.panel_frame(a, b)
    R_, p0 = mat[:, :3], mat[:, 3]
    swap = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], dtype=float)
    A = swap @ R_.T
    t = -A @ p0
    fl_ = piece.transform(np.column_stack([A, t]))
    bb = fl_.bounding_box()
    back = as_printed(fl_.translate([-bb[0], -bb[1], -bb[2]])).translate([bb[0], bb[1], bb[2]])
    return back.transform(np.column_stack([A.T, -A.T @ t]))


low_p = printed_sheet(lower, s.LOWER_A, s.LOWER_B)
up_dir = -np.array([dl[0], 0, dl[1]])
rise = 0.0
while rise < 2 and overlap(body, low_p.translate(rise * up_dir)) > 1e-3:
    rise += 0.02
gap = 0.0
while gap < 2 and overlap(upper, low_p.translate((rise + gap + 0.02) * up_dir)) < 1e-4:
    gap += 0.02
report(gap >= 0.1, f"as printed, a lower sheet rests {rise:.2f} mm further up its slope than drawn, and the upper sheet's "
                   f"tail still clears it by {gap:.2f} mm more, so the upper sheet sits on the barn ends")
roof_low = s.union([lower, lower.mirror([1, 0, 0])])
worst = sweep(upper, s.union([inside, roof_low]), [[0, 0, dz] for dz in np.arange(0.1, 20.01, 0.1)])
report(worst < 1e-3, f"an upper sheet goes on and lifts off straight up, touching nothing from 20 mm up with the lower "
                     f"sheets and lofts in place ({worst:.4f} mm3)")
# how much an upper sheet sags between the barn ends under its own weight: 5wL^4/384EI, its own
# section at mid-length (PLA E about 3500 MPa, 1.24 g/cm3), against the 0.45 mm lap gap
cs_mid = up_flat.transform(np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0]], dtype=float)).slice(
    -up_flat.bounding_box()[4] / 2)
pts = [np.asarray(q) for q in cs_mid.to_polygons()]
area = cs_mid.area()
cz = sum(((q[:, 1] + np.roll(q[:, 1], -1)) * (q[:, 0] * np.roll(q[:, 1], -1) - np.roll(q[:, 0], -1) * q[:, 1])).sum()
         for q in pts) / (6 * area)
izz = sum(((q[:, 1] ** 2 + q[:, 1] * np.roll(q[:, 1], -1) + np.roll(q[:, 1], -1) ** 2) *
           (q[:, 0] * np.roll(q[:, 1], -1) - np.roll(q[:, 0], -1) * q[:, 1])).sum() for q in pts) / 12 - area * cz ** 2
w_lin = area * 1.24e-6 * 9.81 * math.cos(math.atan(s.UP_M))       # N per mm, square to the sheet
span = 2 * s.PEG_Y
sag = 5 * w_lin * span ** 4 / (384 * 3500 * abs(izz))
report(sag < s.LAP_GAP, f"an upper sheet ({area:.1f} mm2 section, I = {abs(izz):.1f} mm4) sags about {sag:.2f} mm between "
                        f"the barn ends ({span:.1f} mm) under its own weight, under the {s.LAP_GAP} mm lap gap")
low_pegs = []
gshape = s.prism_xz(s.GABLE, -s.L, s.L)
for n in ENDS:
    sy = s.WALL_SIDE[n][1]
    for sx in (1, -1):
        m_ = s.lower_mid(sx)
        for x, z0_, z1_ in ((sx * s.PEG_X, s.zline(s.PEG_X) - 3, s.zline(s.PEG_X) + 3), (m_[0], m_[1] - 4, m_[1] + 8)):
            reg = s.cyl_z(x, sy * s.PEG_Y, z0_, z1_, 2.4) - gshape        # the peg where it stands out of the gable
            low_pegs.append(print_part(p[n], s.WALL_TO_PRINT[n], reg).bounding_box()[2])
report(max(low_pegs) < 1e-6, f"every roof peg lies on the bed in its end wall's print (lowest points "
                             f"{max(low_pegs):.4f} mm up at most)")


# ======================================================================== 9
group("9 skids")
legs = s.union([p[n] ^ s.wall_box(n, s.prong_spans(ac)[0][0] - 0.05, s.prong_spans(ac)[0][1] + 0.05, -0.1,
                                  s.BARB + s.PRONG_T + 0.1, -1, s.ZF - 1) for n in LONGS for ac in s.prong_spots(n)])
lows = []
for name, k in skids_placed:
    v = overlap(body, k)
    vr = overlap(body, k.translate([0, 0, 0.3]))
    vh = min(overlap(fl, k.translate(t)) for t in ([0.3, 0, 0], [-0.3, 0, 0], [0, 0.3, 0], [0, -0.3, 0]))
    lows.append(k.bounding_box()[2])
    extra = ""
    ok = v < 0.01 and vr > 1 and vh > 0.05
    if name.startswith("outer"):
        g = k.min_gap(legs, 1.0)
        ok &= g >= 0.3
        extra = f"; it clears every barb and prong leg by {g:.2f} mm at its reliefs"
    report(ok, f"{name} fits under the floor ({v:.4f} mm3), touches it (raised 0.3: {vr:.1f} mm3), and is held by its pegs "
               f"({vh:.2f} mm3 moved 0.3 mm in x or y){extra}")
report(max(lows) - min(lows) < 0.01, f"all four skids' bottoms are level, {min(lows):.3f} to {max(lows):.3f} mm "
                                     f"(z 0 is the floor's underside), so the garage stands on all four")


# ======================================================================== 10
group("10 plates")
all_pl = s.plates(p)
cfgs, models = {}, {}
for fname, pls in all_pl.items():
    for i, (pname, items) in enumerate(pls):
        placed, fils, skid_i = [], set(), []
        for obj, parts_, (x, y), *own in items:
            whole = s.union([m for _, m, _ in parts_])
            bb = whole.bounding_box()
            fils |= {f for _, _, f in parts_}
            for q in whole.translate([x - bb[0], y - bb[1], -bb[2]]).decompose():
                if "skid" in obj:
                    skid_i.append(len(placed))
                placed.append(q)
        boxes = [q.bounding_box() for q in placed]
        inside_ = all(b[0] >= -1e-6 and b[1] >= -1e-6 and b[3] <= BED + 1e-6 and b[4] <= BED + 1e-6 for b in boxes)
        gap, s_s, s_o = BED, BED, BED
        for a_, b_ in itertools.combinations(range(len(placed)), 2):
            A_, B_ = boxes[a_], boxes[b_]
            d = math.hypot(max(B_[0] - A_[3], A_[0] - B_[3], 0), max(B_[1] - A_[4], A_[1] - B_[4], 0))
            d = d if d >= 11 else placed[a_].min_gap(placed[b_], 11.5)
            gap = min(gap, d)
            if a_ in skid_i and b_ in skid_i:
                s_s = min(s_s, d)
            elif a_ in skid_i or b_ in skid_i:
                s_o = min(s_o, d)
        tower = all(b[3] <= 162 + 1e-6 or b[4] <= 192 + 1e-6 for b in boxes)
        ok = inside_ and gap >= 3 - 1e-6 and (len(fils) < 2 or tower)
        if skid_i:
            ok &= s_o >= 6.0 and (s_s >= 10.5 or len(skid_i) < 2)
        if fname.startswith("1"):
            ok &= len(fils) == 1
        report(ok, f"{fname}, plate {i + 1} ({pname}): {len(placed)} parts inside the bed, at least {gap:.1f} mm apart, " +
               (f"skids {s_s:.1f} mm from each other and {s_o:.1f} from anything else, " if len(skid_i) > 1 else
                f"the skid stub {s_o:.1f} mm from anything else, " if skid_i else "") +
               (f"every part ending left of x 162 or below y 192 for the prime tower" if len(fils) > 1 else
                f"filament {min(fils)} only, no prime tower"))
    # what Flash Studio reads: each object's own settings in Metadata/model_settings.config, in the file as written
    path = os.path.join(s.HERE, fname)
    if not os.path.exists(path):
        report(False, f"{fname} is not written yet: run make_barn_garage.py")
        continue
    with zipfile.ZipFile(path) as z:
        cfg = z.read("Metadata/model_settings.config").decode()
        same_settings = z.read("Metadata/project_settings.config") == open(os.path.join(s.HERE, "flash studio settings.json"), "rb").read()
        cfgs[fname], models[fname] = cfg, z.read("3D/3dmodel.model").decode()
    objs = re.findall(r'<object id="\d+"><metadata key="name" value="([^"]*)"/>(.*?)<part', cfg)
    bad = []
    for oname, meta in objs:
        keys = dict(re.findall(r'<metadata key="(brim_[a-z_]+)" value="([^"]*)"/>', meta))
        if "skid" in oname:
            want = {"brim_type": "outer_only", "brim_width": "5"}
        elif "corner angle" in oname or "roof" in oname and "peg" not in oname and "coupon" not in oname:
            want = {"brim_type": "no_brim"}
        else:
            want = {}
        if keys != want:
            bad.append((oname, keys))
    nsk = sum(1 for o, _ in objs if "skid" in o)
    nnb = sum(1 for o, m_ in objs if 'value="no_brim"' in m_)
    owned = sorted(o for o, m_ in objs if re.search(r'<metadata key="(?!extruder)', m_))
    if fname.startswith("1"):
        bad += [] if owned == ["corner angle stub", "outer skid stub"] else [("objects with their own settings", owned)]
    report(not bad and same_settings and (nsk == 4 if fname.startswith("2") else nsk == 1),
           f"{fname}: in Metadata/model_settings.config the {nsk} skid object(s) carry brim_type outer_only and brim_width "
           f"5, the {nnb} corner angle and roof sheet object(s) no_brim, nothing else has a brim setting"
           f"{(' (wrong: %s)' % bad) if bad else ''}; the project settings are flash studio settings.json byte for byte")
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
# wall's siding bridge direction afresh, and the same file has come out both ways: the door side's siding along four
# stud bays beside the steel door, 55 mm strands, in about half of the slices, and the fit test's half doorway's two end
# bays every time. Every wall's bays are as long the other way, so every wall, and every fit-test piece cut from one,
# carries modifiers over its siding that set bridge_angle (External bridge infill direction): 180, which Flash Studio
# reads as 0 degrees, along the bed's X, across the studs, or, over a barn end's collar tie, 90, along Y, up the gable.
# Read from the files as written: the modifiers, each as the solid it is (Flash Studio applies its shape, not the box
# round its corners: it must be a closed solid filling that box), what they set (exactly the plan, and a number other
# than 0: Flash Studio takes any 0, "0.0" and "-0" too, as no direction and picks its own), where they reach; together
# they cover the whole piece, one over another nowhere; every piece lies on its plate unturned (the directions are the
# bed's, so a turned piece would bridge another way: floor review, Nov 4 2026); then each one's part of the piece, its
# bridges laid that way, and the layers under them left to the slicer (the prong legs' first layer, the rebate's
# ceiling, the door side's headers: bridged as on the walls that print as proven). The floor's sheet seams are its
# first layer, slots 0.4 mm wide. A 45 degree overhang reaches across one from both sides, so those proofs don't see
# them, but Flash Studio bridges the layer over them, and laid it along the long seams, 193 mm strands over the slot
# (bridge review). So the floor carries modifiers over that layer alone, the only one of the floor over anything not
# printed under it: across the long seams on a strip over each, across the short ones elsewhere; laid that way,
# counting everything not printed on the layer under it, each line crosses its seam. Nothing else carries one, nothing
# else hangs out over SIDING_BRIDGE_Z more than 20 mm across in any direction, and nothing else has a slot like a seam
# longer than 20 mm on any layer, so no way the slicer lays it makes a longer strand. The 12x24 Garage's checker proves
# the same
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
for fname, pls in all_pl.items():
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
# plate 3 (lift-out addendum I.2, I.3): both end walls and the roll-up curtain, one colour change: white only up to the
# 5.05 layer, black only from 5.04, and above the trim's top layer (5.65) only the curtain's black handle
pl3_name, pl3 = all_pl["2 all plates.3mf"][2]
w_top, b_bot, above = 0.0, 99.0, []
cur_item = [it_ for it_ in pl3 if it_[0] == "roll-up curtain"]
for obj, parts_, (x, y), *own in pl3:
    z0_ = s.union([m for _, m, _ in parts_]).bounding_box()[2]
    for pn_, m_, f_ in parts_:
        hi_ = lambda h_: (m_ ^ s.box(-BED, 2 * BED, -BED, 2 * BED, z0_ + h_, BED)).volume()
        if f_ == 1 and hi_(s.WT + 1e-4) > 1e-6:
            w_top = 99.0
        if f_ != 1 and (m_ ^ s.box(-BED, 2 * BED, -BED, 2 * BED, -BED, z0_ + 5.04 - 1e-4)).volume() > 1e-6:
            b_bot = 0.0
        if hi_(s.WT + s.PROUD + 1e-4) > 1e-6:
            above.append((obj, pn_, round(m_.bounding_box()[5] - z0_, 2)))
cbx = s.size(s.union([m for _, m, _ in cur_item[0][1]])) if cur_item else (0, 0)
cpos = cur_item[0][2] if cur_item else (0, 0)
report(pl3_name == "end walls and roll-up curtain" and w_top < 1 and b_bot > 1
       and above == [("roll-up curtain", "latch plate and handle", s.HDL_U2)] and len(cur_item) == 1,
       f"2 all plates.3mf, plate 3 is \"{pl3_name}\": the roll-up curtain lies on its back at ({cpos[0]:.1f}, {cpos[1]:.1f}), "
       f"its box to x {cpos[0] + cbx[0]:.2f}, y {cpos[1] + cbx[1]:.2f}; nothing white over the siding's top layer (the "
       f"walls' white to {s.WT:.3f}, the curtain's to {s.RAIL_FACE}, both the 5.05 layer) and no black under 5.04, so one "
       f"colour change; above the trim's top layer only {above}")
# fit test plate 1 (review, Nov 3 2026): the half doorway and half door alone, so nothing prints above the walls' top layer
# but the half door's handle, as on plate 3, and the fit test shows how plate 3's handle comes out
f1_name, f1 = all_pl["1 fit test.3mf"][0]
above1, names1 = [], []
for obj, parts_, (x, y), *own in f1:
    names1.append(obj)
    whole = s.union([m for _, m, _ in parts_])
    z0_ = whole.bounding_box()[2]
    hi_ = whole ^ s.box(-BED, 2 * BED, -BED, 2 * BED, z0_ + s.WT + s.PROUD + 1e-4, BED)
    if hi_.volume() > 1e-6:
        hb_ = hi_.bounding_box()
        above1.append((obj, round(hb_[3] - hb_[0], 3), round(hb_[5] - z0_, 2)))
half_p = dict(cu_parts)["half roll-up door"]
hl_diff = max(abs(half_p.slice(zm_).area() - cur_flat.slice(zm_).area()) for zm_ in (5.75, 6.15, 6.55, 6.75, 7.15, 7.95, 8.15))
report(f1_name == "roll-up door" and sorted(names1) == ["half roll-up door", "half roll-up doorway"] and len(above1) == 1
       and above1[0][0] == "half roll-up door" and abs(above1[0][1] - 2 * s.HDL_HALF) < 0.01 and hl_diff < 1e-3
       and abs(half_p.bounding_box()[5] - cur_flat.bounding_box()[5]) < 1e-6,
       f"1 fit test.3mf, plate 1 is \"{f1_name}\": only the {' and the '.join(names1)}, and above the walls' top layer only the "
       f"half door's handle ({above1[0][1] if above1 else 0:.2f} wide, up to {above1[0][2] if above1 else 0:.2f}), so its legs "
       f"and grip print alone from the 5.85 layer, as the real door's do on plate 3; and its handle's layers there are the "
       f"real one's ({hl_diff:.5f} mm2 apart at most on the 5.75 to 8.15 layers): so the fit test prints its handle as the "
       f"real one prints")


# ======================================================================== 11
group("11 fit test")
lw_, ew_, cf, stub, sk = ct
fsx, fsy = s.WALL_SIDE[s.FIT_LONG][1], s.WALL_SIDE[s.FIT_END][1]
fu, fv = np.array([fsx, 0.0, 0.0]), np.array([0.0, fsy, 0.0])
none = max(overlap(a_, b_) for a_, b_ in itertools.combinations([lw_, ew_, cf, stub, sk], 2))
held = min(overlap(lw_.translate([0, 0, 0.3]), cf), overlap(ew_.translate([0, 0, 0.3]), cf))
seat = min(overlap(stub.translate(-0.05 * fu), lw_), overlap(stub.translate(-0.05 * fv), ew_))
edge = min(overlap(stub.translate(-0.2 * fv), lw_), overlap(stub.translate(-0.2 * fu), ew_))
skh = min(overlap(cf, sk.translate(t)) for t in ([0.3, 0, 0], [-0.3, 0, 0], [0, 0.3, 0], [0, -0.3, 0]))
skt = overlap(cf, sk.translate([0, 0, 0.3]))
report(none < 0.001 and held > 0.05 and seat > 0.3 and edge > 0.02 and skh > 0.05 and skt > 0.5,
       f"the roll-up corner goes together like the real one: nothing overlaps ({none:.4f} mm3), lifted 0.3 mm both walls' "
       f"barbs catch ({held:.2f} mm3), the {s.FIT_STUB:.0f} mm angle stub sits on both recess floors ({seat:.2f} mm3 "
       f"pressed 0.05 in) between their edges ({edge:.2f}), and the outer skid stub sits flat under the floor (raised "
       f"0.3: {skt:.1f} mm3) held by its peg ({skh:.2f} mm3 moved 0.3)")
(a0, a1), _ = s.prong_spans(s.prong_spots(ru)[0])
legb = s.wall_box(ru, a0, a1, s.BARB, s.BARB + s.PRONG_T, s.ZF - 0.49, s.LEG_ROOT - 0.01)
ring = s.wall_box(ru, a0 - 0.15, a1 + 0.15, s.BARB - 0.15, s.BARB + s.PRONG_T + 0.15, s.ZF - 0.49, s.LEG_ROOT - 0.01) - legb
z_lo = s.ZF + 8
lo_same = [abs(overlap(piece_ ^ s.box(-BED, BED, -BED, BED, -5, z_lo), real) - (piece_ ^ s.box(-BED, BED, -BED, BED, -5, z_lo)).volume())
           for piece_, real in ((lw_, p[s.FIT_LONG]), (ew_, p[s.FIT_END]), (cf, fl))]
nb_ = runs(cf, s.box(-27.5, s.FIT_END_X + 0.5, -98.5, -98.0, 3.0, 3.1), 0)
past_ = [r_ for r_ in nb_ if r_[0] > s.CURTAIN_POSTS[0]]                 # the floor past the notch round the post
beside_ = past_[0][1] - past_[0][0] if past_ else 0.0
dz_ = (s.ZWT - 10) - (s.ZF + 8)
fill_r = s.rbox(-s.RU_W / 2 + 0.05, s.FIT_WALL_X - 0.05, 0.05, s.REB_U - 0.05, s.MOUTH - dz_ + 0.05, s.MOUTH + s.REB_H - dz_ - 0.05)
filled_ = overlap(ew_, fill_r) / fill_r.volume()
post_x = (s.CURTAIN_POSTS[0] - s.SW / 2, s.CURTAIN_POSTS[0] + s.SW / 2)
post_end = (ew_ ^ s.rbox(-30, 0, 0.5, 3.0, 0.5, 3.0)).bounding_box()[3]
report(overlap(ew_, ring) < 1e-4 and abs(overlap(ew_, legb) - legb.volume()) < 1e-3 and max(lo_same) < 1e-3
       and abs(cf.bounding_box()[3] - s.FIT_END_X) < 1e-6 and abs(ew_.bounding_box()[3] - s.FIT_WALL_X) < 1e-6
       and abs(post_end - s.FIT_WALL_X) < 1e-6 and post_x[0] + 0.42 <= s.FIT_WALL_X <= post_x[1]
       and beside_ >= 0.6 and filled_ > 0.999,
       f"its pieces are cut from the real parts (below the join each is exactly the real wall or floor: {max(lo_same):.5f} "
       f"mm3 off); the roll-up end's prong at {s.prong_spots(ru)[0]:+.1f} is rooted in the bottom plate and free to LEG_ROOT "
       f"({overlap(ew_, ring):.6f} mm3 round it); the corner piece ends at x {s.FIT_WALL_X:.3f}, over the post at -35 in "
       f"(x {post_x[0]:.3f} to {post_x[1]:.3f}; its post cut there too, {post_end:.3f}), so its skirt ends on the post, and "
       f"inside the siding groove there, and the bit of floor at x {s.FIT_END_X}, leaving "
       f"{beside_:.3f} mm of floor past the post notch at -35 in (at least 0.6); the corner piece's rebate is filled solid "
       f"({filled_ * 100:.1f}%; the half doorway tests the real one)")
# the short plain side's cut end: on the siding's top layer the narrowest strip of siding between grooves
ends_ = runs(lw_, s.wall_box(s.FIT_LONG, -s.L / 2 - 1, -s.L / 2 + 40, 4.94, 4.96, s.ZF + 3, s.ZF + 3.1), 1)
end_w = min(b_ - a_ for a_, b_ in ends_) if ends_ else 0.0
report(end_w >= 0.6, f"the short plain side's siding: on its top layer the narrowest strip between grooves, the one "
                     f"at its cut end included, is {end_w:.2f} mm, over a line wide, so nothing prints as a loose strand")
worst = max(worst_overhang(part)[0] for _, part in ct_parts + dt_parts + cu_parts)
report(worst < 5, f"every fit test piece prints with nothing steeper than 45 degrees that isn't a bridge of 20 mm or less "
                  f"({worst:.2f} mm2 worst layer)")
# where the fit test's walls are cut short (the short roll-up end at its doorway side, the short plain side at its far
# end, the half doorway at both ends), no layer is left with a strip thinner than a line: each cut is inside a siding
# groove, so the top layer ends at the groove
MIT_ = m3.JoinType.Miter
cut_thin, cut_rows = 0.0, []
for nm_, ends_ in (("short roll-up end", ("max",)), ("short plain side", ("min",)), ("half roll-up doorway", ("min", "max"))):
    m_ = dict(ct_parts + cu_parts)[nm_]
    bbm = m_.bounding_box()
    worst_ = 0.0
    for z0_, z1_ in layers(bbm[5]):
        cs_ = m_.slice((z0_ + z1_) / 2)
        th_ = cs_ - cs_.offset(-0.21, MIT_, 2.0).offset(0.21, MIT_, 2.0)
        for e_ in ends_:
            xe = bbm[0] if e_ == "min" else bbm[3]
            worst_ = max(worst_, (th_ ^ m3.CrossSection.square([3.0, bbm[4] - bbm[1] + 2]).translate([xe - 1.5, bbm[1] - 1])).area())
    cut_thin = max(cut_thin, worst_)
    cut_rows.append(f"{nm_} {worst_:.4f}")
report(cut_thin < 0.05,
       f"within 1.5 mm of where the fit test's walls are cut short nothing on any layer is thinner than a line ("
       + ", ".join(cut_rows) + f" mm2 at the most): the cuts are inside siding grooves, the short roll-up end at x "
       f"{s.FIT_WALL_X:.3f}, the short plain side at y {s.LONG_STUDS[1] + s.GROOVE_W / 2 - 0.1:.3f} and the half doorway at x "
       f"{s.FIT_FRAME_X0:.3f} (and its mirror)")
blk, cpn = dt_parts[2][1], dt_parts[3][1]
peg_low = (blk ^ s.box(-BED, BED, 6.01, BED, -1, BED)).bounding_box()[2]
# stand the block up, peg pointing up, and drop the coupon over it
upr = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0]], dtype=float)
bs = blk.transform(upr)
bb_ = bs.bounding_box()
pk = bs ^ s.box(-BED, BED, -BED, BED, bb_[5] - s.PEG_UP + 0.01, BED)
pkb = pk.bounding_box()
pcx, pcy = (pkb[0] + pkb[3]) / 2, (pkb[1] + pkb[4]) / 2
cb = cpn.bounding_box()
cpn_on = cpn.translate([pcx - (cb[0] + cb[3]) / 2, pcy - (cb[1] + cb[4]) / 2, bb_[5] - s.PEG_UP + 0.05])
clear = max(overlap(cpn_on.translate([0.39 * math.cos(t), 0.39 * math.sin(t), 0]), pk) for t in np.arange(0, 6.28, 0.5))
tight = min(overlap(cpn_on.translate([0.45 * math.cos(t), 0.45 * math.sin(t), 0]), pk) for t in np.arange(0, 6.28, 0.5))
report(peg_low < 1e-6 and clear < 1e-4 and tight > 1e-4,
       f"the roof peg lies on the bed in its block's print (lowest point {peg_low:.4f}), and the coupon goes over it with "
       f"0.4 mm round: moved 0.39 any way it still clears ({clear:.5f} mm3), 0.45 it meets the peg")
# the fit test's half door in its half doorway (lift-out addendum J): cut from the real parts, and it moves as the real
# door does, drawn and as printed
stw, stb = s.curtain_stub()
stub3 = stw + stb
frame3 = s.curtain_frame(p[ru])
real_cut = p[ru] ^ s.box(s.FIT_FRAME_X0 + 0.01, -0.01, -BED, BED, -1, s.ZWT - 0.01)
fr_same = abs(overlap(frame3, real_cut) - real_cut.volume())
mir_cut = s.mirror_x(p[ru] ^ s.box(s.FIT_FRAME_X0 + 0.01, -s.RU_W / 2 - 0.01, -BED, BED, -1, s.ZWT - 0.01), s.FIT_XM)
mi_same = abs(overlap(frame3, mir_cut) - mir_cut.volume())
R_ = s.box(-BED, s.FIT_STUB_END - s.CUR_CHAMF - 0.06, -BED, BED, -BED, BED) - s.union(
    [s.rbox(c_ - s.HDL_BOSS_HALF - 0.01, c_ + s.HDL_BOSS_HALF + 0.01, s.RU_FACE - 0.02, 9, -1, 200) for c_ in (0.0, s.FIT_XM)])
ra_, sa_ = p["curtain"] ^ R_, stub3 ^ R_
st_same = abs(sa_.volume() - ra_.volume()) + abs(overlap(sa_, ra_) - ra_.volume())
hb_ = stb.bounding_box()
sb3 = stub3.bounding_box()
op_ = runs(frame3, s.rbox(-40, 10, 1.9, 2.0, 30.0, 30.1), 0)                   # the half doorway's width, read off it
fr_open = op_[1][0] - op_[0][1] if len(op_) >= 2 else 0.0
report(fr_same < 1e-3 and mi_same < 1e-3 and st_same < 1e-3 and abs((hb_[0] + hb_[3]) / 2 - (sb3[0] + sb3[3]) / 2) < 1e-6
       and abs(sb3[3] - s.FIT_STUB_END) < 1e-6 and abs(fr_open - s.RU_W / 2) < 1e-3
       and abs(sb3[0] + s.CUR_HALF) < 1e-6 and abs((sb3[3] - sb3[0]) - (s.CUR_HALF - s.RU_CLR_X)) < 1e-6,
       f"fit test: the half doorway is the real roll-up end from x {s.FIT_FRAME_X0:.3f} to the doorway's middle ({fr_same:.5f} mm3 "
       f"off) closed by the real jamb strip mirrored about x {s.FIT_XM:.3f} ({mi_same:.5f} off); the half door is the real "
       f"curtain's -x half to x {s.FIT_STUB_END} ({st_same:.5f} off, away from its handle and its chamfered +x end), its handle "
       f"centred at x {(hb_[0] + hb_[3]) / 2:.3f}, its middle; the half doorway is {fr_open:.3f} wide (half the real "
       f"{s.RU_W:.3f}) and the half door {sb3[3] - sb3[0]:.3f}, so it has the real side gaps")
XS_STUB = sorted(set([x_ for x_ in STATIONS if -s.CUR_HALF <= x_ <= s.FIT_STUB_END]
                     + [-0.35, -0.5, -0.8, -1.0, -1.3, -1.5, -1.6]
                     + [round(-1.65 + 0.05 * k_, 2) for k_ in range(27)]          # the mirrored stop, every 0.05
                     + [round(s.FIT_XM + d_, 3) for d_ in (0, -1.2, 1.2, -2.5, 2.5, -3.6, 3.6, -5.0, 5.0, -5.4, 5.4)]))
STUB_ZONES = [(-H_ - 0.35, -s.RU_STOP_X0 + 0.35), (2 * s.FIT_XM + s.RU_STOP_X0 - 0.35, 2 * s.FIT_XM + H_ + 0.35)]   # its jamb, mirrored
table = s.box(-60, 20, -s.L / 2 - 40, -s.L / 2 + 10, -5, 0)
for nm_, gw_, gc_, pr_, real_ in (("drawn", 0.0, 0.0, False, D), ("printed", 0.1, 0.05, True, P)):
    xs_ = printed_xs(stub3, frame3, gw_, gc_, base=XS_STUB, zones=STUB_ZONES) if pr_ else XS_STUB
    cs_ = Case("stub " + nm_, stub3, frame3, [("table", table, "none")], xs_, gw_, gc_, pr_)
    q_ = study(cs_)
    pre_ = q_["pre"]
    lifts_ = sorted(set([round(q_["need"] + 0.1 * j_, 3) for j_ in range(20) if q_["need"] + 0.1 * j_ <= q_["stop"] + 1e-9]
                        + [round(q_["stop"] - 0.15, 3)]))
    rm_ = max(path_worst(cs_, removal_poses(l_, th_, pre_))["ov"] for l_ in lifts_ for th_ in SWINGS)
    ins_ = insert_all(q_)
    bands_ = [(th_, band_of(ins_, th_), band_of(real_["ins"], th_)) for th_ in SWINGS]
    seat_same = all(abs(a_ - b_) < 1e-9 for a_, b_ in zip(pre_, real_["pre"]))
    same_ = (seat_same and abs(q_["stop"] - real_["stop"]) <= 0.025 + 1e-9
             and abs(q_["need"] - real_["need"]) <= 0.05 + 1e-9
             and all(None not in bs_ + br_ and abs(bs_[0] - br_[0]) <= 0.1 + 1e-9 and abs(bs_[1] - br_[1]) <= 0.1 + 1e-9
                     for _, bs_, br_ in bands_)
             and all(ins_[(th_, 0.0)]["result"] == "catches" for th_ in SWINGS))
    sw_ = s.STUB_WEIGHT_G / s.CUR_WEIGHT_G                         # its weight against the real door's
    hold_up = [kf[E_] * q_["fpre"] / (sw_ * WEIGHT) for E_ in (2500.0, 3500.0)]     # one finger
    hold_fd = [k_ * q_["tpre"] / (sw_ * need_t) for k_ in kt]                       # one tab
    held_ = nm_ != "drawn" or (min(hold_up) > 1.5 and min(hold_fd) > 1.5)
    report(same_ and held_ and rm_ < 1e-4 and all(th_ is not None for tc_, th_ in q_["m15"].values()) and q_["fpre"] > 0.1
           and q_["tpre"] > 0.1,
           f"fit test, the half door in the half doorway, {nm_} ({len(xs_)} stations): seat {pre_[0]:+.3f} out {pre_[1]:+.3f} "
           f"up (the real door {real_['pre'][0]:+.3f}, {real_['pre'][1]:+.3f}{': the same' if seat_same else ''}), preloads {q_['fpre']:.2f} / "
           f"{q_['tpre']:.2f}, rigid stop {q_['stop']:.3f} ({real_['stop']:.3f}; within 0.025), least lift {q_['need']} "
           f"({real_['need']}; within 0.05); it comes out by H.3 at {len(lifts_)} lifts from its least to the stop and the "
           f"stop less 0.15, swung 6, 7 and 8 degrees ({rm_:.5f} mm2), and by the three hand motions at the stop less 0.15; "
           f"with no lean it catches, and it goes in leaned "
           + ", ".join(f"{th_:g}: {bs_[0] or 0:+.2f} to {bs_[1] or 0:+.2f} ({br_[0] or 0:+.2f} to {br_[1] or 0:+.2f})"
                       for th_, bs_, br_ in bands_)
           + f" (the real door's in brackets; within 0.1){': it moves as the real door does' if same_ else ''}; weighing {s.STUB_WEIGHT_G} g (a "
           f"little over half the real door's {s.CUR_WEIGHT_G}: its handle is full size) on one finger and one tab it holds "
           f"{hold_up[0]:.2f} to {hold_up[1]:.2f} times its weight upside down and {hold_fd[0]:.2f} to {hold_fd[1]:.2f} times "
           f"what it needs face down" + (" (over 1.5)" if nm_ == "drawn" else ""))



# ======================================================================== 12
group("12 sizes at full size against the shop numbers")
inch = 1 / s.S
THRESHOLD_IN = 0.94      # the threshold's height over the floor: open question 17's default, typed in, not read from the
                         # generator (with LIP_H 0.466, the tuning table's row, this goes to 0.66)


def extent(piece, region, axis):
    bb = (piece ^ region).bounding_box()
    return bb[axis], bb[axis + 3]


zm = s.ZF + 20
# on plain siding of both long walls, between two grooves, clear of the door and window wherever they go
x_hi = extent(p["door side"], s.box(40, 60, 87.4, 87.6, zm, zm + 0.2), 0)[1]
x_lo = extent(p["plain side"], s.box(-60, -40, 87.4, 87.6, zm, zm + 0.2), 0)[0]
y_lo = extent(p[ru], s.box(39.5, 39.7, -110, -90, zm, zm + 0.2), 1)[0]
y_hi = extent(p["back end"], s.box(0.5, 0.7, 90, 110, zm, zm + 0.2), 1)[1]
report(abs((x_hi - x_lo) * inch - 134) < 0.01 and abs((y_hi - y_lo) * inch - 288) < 0.01,
       f"outside of the siding {(x_hi - x_lo) * inch:.2f} x {(y_hi - y_lo) * inch:.2f} in (Alan's actual 12x24: 134 x 288 in)")
floor_top = fl.bounding_box()[5]
wall_top = p["door side"].bounding_box()[5] + 0.15
wall_in = (wall_top - floor_top) * inch
report(abs(wall_in - 82.8) < 0.01, f"walls {wall_in:.2f} in from the floor top to the top of the upper plate (designer "
                                   f"6.9 ft = 82.8 in, kept by Alan)")
peak = p["back end"].bounding_box()[5]
line_peak = (peak - wall_top) * inch
truss_peak = line_peak - 0.4375 / math.cos(math.atan(s.UP_M))
report(abs(truss_peak - 51.0) < 0.01 and abs(line_peak - 51.46) < 0.01,
       f"barn roof {truss_peak:.2f} in from the top of the upper plate to the peak of the trusses (Alan: 51 in at 12 ft "
       f"wide), {line_peak:.2f} in to the top of the roof deck")
mv = np.asarray(lower.to_mesh().vert_properties)[:, :3]
eave_pt = mv[np.argmin(mv[:, 2])]
eave = (eave_pt[0] - x_hi) * inch
report(abs(eave - 2.03) < 0.01, f"eave {eave:.2f} in out from the siding, measured level (designer: 0.42 ft down the "
                                f"slope = 2.03 in)")
report(abs(ru_w * inch - 96) < 0.01 and abs(ru_h * inch - 76.8) < 0.01,
       f"roll-up opening {ru_w * inch:.2f} x {ru_h * inch:.2f} in, centred on the roll-up end (designer ru8: 96 x 76.8 in)")
cbb_ = p["curtain"].bounding_box()
cur_w = (cbb_[3] - cbb_[0]) * inch
gz_ = runs(p["curtain"], s.rbox(-20.01, -19.99, s.RU_FACE - 0.2, s.RU_FACE - 0.1, s.ZF + 9, s.ZF + 14), 2)
slat_in = (gz_[2][0] - gz_[1][0]) * inch if len(gz_) >= 3 else 0
hbb_ = p["curtain black"] ^ s.rbox(-10, 10, s.HDL_U1 + 0.1, 9, -1, 30)
hb2 = hbb_.bounding_box()
hdl_in, hdl_ht = (hb2[3] - hb2[0]) * inch, (hb2[5] - hb2[2]) * inch
lip_r = runs(p[ru], s.rbox(4.99, 5.01, s.WT - 0.1, s.WT - 0.05, s.ZF - 0.005, s.ZF + 2), 2)
lip_in = (lip_r[0][1] - s.ZF) * inch if lip_r else 0
body_top = runs(p["curtain"], s.rbox(4.99, 5.01, 2.9, 3.0, s.ZF + 40, s.MOUTH + 1), 2)
slit_in = (s.MOUTH - body_top[-1][1]) * inch if body_top else 0
report(abs(cur_w - 95.15) < 0.01 and abs(slat_in - 2.25) < 0.01 and abs(hdl_in - 16.0) < 0.01 and abs((hb2[0] + hb2[3]) / 2) < 1e-6
       and abs(hb2[2] - s.RAIL_Z0) < 1e-6 and abs(lip_in - THRESHOLD_IN) < 0.01 and abs(slit_in - 3.12) < 0.01,
       f"roll-up door: curtain {cur_w:.2f} in wide, slats {slat_in:.2f} in, black lift handle {hdl_in:.2f} x {hdl_ht:.2f} in "
       f"at the bottom middle of its rail (centred at x {(hb2[0] + hb2[3]) / 2:+.3f}, its bottom on the rail's), threshold "
       f"{lip_in:.2f} in (open question 17: {THRESHOLD_IN} in), the dark slit under the head {slit_in:.2f} in (designer 2.2 "
       f"in, lift-out addendum)")
dsc = p["door side"] ^ zone
probe_x = (s.W / 2 + 0.1, s.W / 2 + 0.5)
# the casings along the whole door side, read off the black: at 20 mm up only the door's two side boards, at 40 mm
# up those and the window's two
segs = runs(dsc, s.box(*probe_x, -s.L / 2 + 4, s.L / 2 - 4, s.ZF + 20, s.ZF + 20.2), 1)
d_lo, d_hi = (segs[0][1], segs[1][0]) if len(segs) == 2 else (0.0, 0.0)
door_w = (d_hi - d_lo) * inch
door_c = ((d_hi + d_lo) / 2) / s.FT
door_in = (d_lo + s.L / 2) * inch                        # its -y edge from the outside of the roll-up end
dtop = (runs(dsc, s.box(*probe_x, door_c * s.FT - 0.1, door_c * s.FT + 0.1, s.ZF + 2, s.ZWT), 2) or [(0, 0)])[0][0]
door_h = (dtop - floor_top) * inch
hdr = runs(ds, s.box(s.W / 2 - s.WT + 0.5, s.W / 2 - s.WT + 1.0, door_c * s.FT - 0.1, door_c * s.FT + 0.1, s.ZF + 50,
                     s.ZWT), 2) or [(0, 0)]
hdr_in = (hdr[0][1] - hdr[0][0]) * inch
report(len(segs) == 2 and abs(d_lo - STD_DOOR[0]) < 1e-3 and abs(d_hi - STD_DOOR[1]) < 1e-3
       and abs(door_c * s.FT - STD_DOOR_YC) < 1e-3 and abs(door_c + 6.5) < 1e-3 and abs(door_in - 48) < 0.01
       and abs(door_w - 36) < 0.01 and abs(door_h - 75.6) < 0.01 and abs(hdr_in - 3.0) < 0.01
       and abs((hdr[0][0] - floor_top) * inch - 75.6) < 0.01,
       f"steel door opening {door_w:.2f} x {door_h:.2f} in (designer d36in: 36 x 75.6 in), y {d_lo:.3f} to {d_hi:.3f}, "
       f"centred {-door_c:.2f} ft from the middle toward the roll-up end, its edge {door_in:.2f} in from the outside of the "
       f"roll-up end (Alan's standard: on the roll-up end, edge 4 ft in from the corner, centre -55.033), its header "
       f"{hdr_in:.2f} in (two flat 2x4s) on its king studs")
segs = runs(dsc, s.box(*probe_x, -s.L / 2 + 4, s.L / 2 - 4, s.ZF + 40, s.ZF + 40.2), 1)
w_lo, w_hi = (segs[2][1], segs[3][0]) if len(segs) == 4 else (0.0, 0.0)
win_w = (w_hi - w_lo) * inch
win_c = ((w_hi + w_lo) / 2) / s.FT
half = (d_hi / s.FT + s.L / 2 / s.FT) / 2                # halfway between the door's back edge and the back
wz = runs(dsc, s.box(*probe_x, win_c * s.FT - 0.1, win_c * s.FT + 0.1, s.ZF + 2, s.ZWT), 2)
wz = wz if len(wz) >= 2 else [(0, 0), (0, 0)]
win_top = (wz[1][0] - floor_top) * inch
win_sill = (wz[0][1] - floor_top) * inch
z1w = s.ZF + s.WIN_TOP
lh = runs(ds, s.box(s.W / 2 - s.WT + 0.5, s.W / 2 - s.WT + 1.0, win_c * s.FT + 2.9, win_c * s.FT + 3.1, z1w + 0.25,
                    s.ZWT + 1), 2)
hdr_w = (s.ZWT - s.PLATE_TOP - z1w) * inch
report(len(segs) == 4 and abs(win_c * s.FT - STD_WIN_YC) < 1e-3 and abs(win_c - 3.5) < 1e-3 and abs(win_c - half) < 1e-3
       and abs(win_w - 25.2) < 0.01 and abs(win_top - win_sill - 34.8) < 0.01
       and abs(win_top - 74.8) < 0.01 and len(lh) == 1 and abs(lh[0][1] - (s.ZWT - 0.15)) < 1e-6 and abs(hdr_w - 5.0) < 0.01,
       f"window {win_w:.2f} x {win_top - win_sill:.2f} in (designer w23: 25.2 x 34.8 in), centred {win_c:.2f} ft from the "
       f"middle toward the back end, {win_c - d_hi / s.FT:.2f} ft from the door's back edge and {s.L / 2 / s.FT - win_c:.2f} "
       f"from the back (Alan's standard: centred between them, +29.633), its top {win_top:.2f} in up, framing solid from "
       f"there to the wall top: Alan's {hdr_w:.2f} in loft header right under the top plates (his lofted-wall rule)")
fw_ = runs(p[ru] ^ zone, s.box(-20, 20, -s.L / 2 - 1, -s.L / 2, s.FAUX_ZC - 0.05, s.FAUX_ZC + 0.05), 0)
fz_ = runs(p[ru] ^ zone, s.box(-0.05, 0.05, -s.L / 2 - 1, -s.L / 2, s.ZWT + 3, s.ZWT + 30), 2)
fwin_w = (fw_[-1][1] - fw_[0][0]) * inch
fwin_h = (fz_[-1][1] - fz_[0][0]) * inch
fwin_b = (fz_[0][0] - s.ZWT) * inch
report(abs(fwin_w - 31.2) < 0.01 and abs(fwin_h - 22.8) < 0.01 and abs(fwin_b - 7.44) < 0.01,
       f"faux loft window {fwin_w:.2f} x {fwin_h:.2f} in, its bottom {fwin_b:.2f} in over the wall top (designer: 31.2 x "
       f"22.8 in, 7.44 in)")
bb_b = runs(p["back end"] ^ zone, s.box(-10.1, -10, s.L / 2, s.L / 2 + 1, s.ZWT, s.ZWT + 25), 2)
band_b = [(a_ - s.ZWT) * inch for a_, b_ in bb_b]
band_f = (fb_[2] - s.ZWT) * inch
report(abs(band_f) < 0.01 and len(band_b) == 1 and abs(band_b[0] - 20.58) < 0.01,
       f"the roll-up end's band at the wall top ({band_f:+.2f} in), the back end's at {band_b[0] if band_b else 0:.2f} in "
       f"over it (designer: 0.40 of the roof line, 20.58 in)")
vz = s.ZPK - s.VENT_DROP
zgap = vz - s.VENT_H / 2 + 1.0 + (s.VENT_H - 2 * 1.0) / s.VENT_SLATS - s.VENT_BACK_GAP / 2   # a row through a gap
ok_vent, vtxt = True, []
for n in ENDS:
    side = s.WALL_SIDE[n][1]
    ya, yb = sorted([side * (s.L / 2 - 0.3), side * (s.L / 2 - 0.1)])
    # just under the siding face the vent's frame shows inside the 0.5 groove round it: across, through
    # a gap between louvres, as two 1 mm strips; up the middle, from the groove under it to the groove
    # over it (the bottom louvre stands on the frame's lower bar). Its outside edges are the vent's size
    gx = [r for r in runs(p[n], s.box(-8, 8, ya, yb, zgap - 0.05, zgap + 0.05), 0) if abs(r[1] - r[0] - 1.0) < 0.05]
    col_ = runs(p[n], s.box(-0.05, 0.05, ya, yb, vz - 6, vz + 6), 2)
    gz = [(col_[i][1], col_[i + 1][0]) for i in range(len(col_) - 1) if abs(col_[i + 1][0] - col_[i][1] - s.GROOVE_W) < 0.02]
    vw_ = (max(b_ for a_, b_ in gx) - min(a_ for a_, b_ in gx)) * inch if len(gx) == 2 else 0
    vh_ = (gz[1][0] - gz[0][1]) * inch if len(gz) == 2 else 0
    ok_vent &= abs((gz[1][0] + gz[0][1]) / 2 - vz) < 1e-6 if len(gz) == 2 else False
    top_ = (s.ZPK - (vz + s.VENT_H / 2)) * inch
    ok_vent &= abs(vw_ - 13.44) < 0.02 and abs(vh_ - 9.12) < 0.02
    vtxt.append(f"{n} {vw_:.2f} x {vh_:.2f} in")
report(ok_vent, f"vents " + ", ".join(vtxt) + f", centred {s.VENT_DROP * inch:.2f} in under the roof line's peak "
                f"(designer: 1.12 x 0.76 ft = 13.44 x 9.12 in, 0.92 ft = 11.04 in under it)")
gb_ = runs(p["back end"], s.box(-5.05, -4.95, s.L / 2 - s.WT + 0.5, s.L / 2 - s.WT + 1, s.ZWT, s.ZWT + 12), 2)
gs = [round(x / s.S, 2) for x in sorted(got_studs)]
report(abs((gb_[0][1] - gb_[0][0]) * inch - 5.5) < 0.01 and gs == [-43, -19, 5, 29, 53]
       and abs((gb_[1][0] - s.ZWT) * inch - 11) < 0.01 and len(gb_) == 2,
       f"gable board {(gb_[0][1] - gb_[0][0]) * inch:.2f} in (a 2x6 on edge, its ends inside the chords), gable studs at "
       f"{gs} in, backing {(gb_[1][0] - s.ZWT) * inch:.2f} in up on the back end only (Alan: 5 1/2, 24 in o.c., 11 in)")
cent = sorted(((k.bounding_box()[0] + k.bounding_box()[3]) / 2) for _, k in skids_placed)
fromside = [round((s.W / 2 - abs(x)) * inch, 2) for x in cent]
report(sorted(fromside) == [8.0, 8.0, 37.0, 37.0], f"skid centres {fromside} in in from the sides (designer: 8 and 37 in)")
loft_d = (s.L / 2 - lbb[1]) * inch
report(abs(loft_d - 48) < 0.01, f"lofts {loft_d:.2f} in deep from the outside of the end wall (designer: 4 ft)")
a = s.corner_angle(1, 1)
cov = [(s.L / 2 - (a ^ s.cbox(s.ANGLE_P - 0.01, 2, -10, 10, -1, 200)).bounding_box()[1]) * inch,
       (s.W / 2 - (a ^ s.cbox(-10, 10, s.ANGLE_P - 0.01, 2, -1, 200)).bounding_box()[0]) * inch]
report(min(cov) > 4.2 and max(cov) < 4.3, f"corner angles cover {cov[0]:.2f} in of the long wall and {cov[1]:.2f} in of the "
                                          f"end wall (a corner board is 3 1/2 in; open question 12)")
st = runs(p["plain side"], s.box(-s.W / 2 + s.WT - 1.0, -s.W / 2 + s.WT - 0.5, -14, -9, s.ZF + 30, s.ZF + 30.1), 1)
report(len(st) == 1 and abs((st[0][1] - st[0][0]) * inch - 1.5) < 0.01,
       f"studs {(st[0][1] - st[0][0]) * inch:.2f} in wide in the wall's plane (a 2x4 is 1 1/2 in)")

print()
print("all checks passed" if fails == 0 else f"{fails} check(s) failed")
sys.exit(1 if fails else 0)
