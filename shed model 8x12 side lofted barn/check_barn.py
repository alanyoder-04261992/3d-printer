"""Checks the barn model fits together before anything is printed.

Run:  python3 check_barn.py
Each line says what it proved. Anything that fails is marked FAIL.
"""

import math
import sys

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


def worst_overhang(piece, flap=None):
    """Layer by layer, the worst area that hangs out more than 45 degrees and isn't a bridge
    held at both ends of 20 mm or less, apart from what flap(section piece, bounds) allows.
    Returns (worst mm2, largest allowed flap mm2, longest bridge mm)."""
    bb = piece.bounding_box()
    worst, flaps, longest, prev = 0.0, 0.0, 0.0, None
    for z0, z1 in layers(bb[5]):
        cs = piece.slice((z0 + z1) / 2)
        if prev is not None:
            left, span = overhangs(cs, prev)
            longest = max(longest, span)
            rest = 0.0
            for bit in left.decompose():
                if flap is not None and flap(bit, bb):
                    flaps = max(flaps, bit.area())
                else:
                    rest += bit.area()
            worst = max(worst, rest)
        prev = cs
    return worst, flaps, longest


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
for name, part in ([("floor", p["floor"])] + [(n, s.union(flat[n])) for n in WALLS] +
                   [("upper roof", up_flat), ("lower roof", lo_flat), ("loft", loft_flat), ("door", door_all),
                    ("skids", p["skids"]), ("fit test", p["fit"])]):
    bb = part.bounding_box()
    size = (bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2])
    pieces = len(part.decompose())
    expect = {"skids": 2, "fit test": 7}.get(name, 1)
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


# 1a. the snap joints. Each wall stands on the floor, the floor holds it in, out and along,
# its barbs hold it down, and the corner hooks tie the tops together.
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
    # lowered on from above: the long walls first onto the bare floor, then the end walls
    # with the long walls standing
    worst = 0
    for dz in (0.25, 0.5, 1, 2, 3, 4, 6, 8, 12, 20, 40, 80, 140):
        moved = w.translate([0, 0, dz])
        worst = max(worst, overlap(moved, fl_open))
        if n in ENDS:
            worst = max(worst, overlap(moved, longs))
    report(worst < 0.001, f"{n} goes on straight down from above"
                          f"{' over the long walls corners' if n in ENDS else ''}, "
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
# the corner hooks: on the barn the end walls go on last, and the hook on each of their top
# corners reaches over the long wall's corner
for n in LONGS:
    v = overlap(p[n].translate([0, 0, 0.3]), ends)
    report(v > 0.05, f"{n} can't lift out from under the end walls' corner hooks ({v:.2f} mm3 at 0.3 mm)")
    v = overlap(p[n].translate(toward(n, 0.3)), ends)
    report(v > 0.05, f"{n} can't lean out away from the hook tips at the top corners ({v:.2f} mm3 at 0.3 mm)")
for n in ENDS:
    v = overlap(p[n].translate(toward(n, 0.3)), longs)
    report(v > 0.05, f"{n} can't lean out of the long walls' corners at the top ({v:.2f} mm3 at 0.3 mm)")
# a long wall leans out a little at the top until the end walls are on. Lowering an end wall,
# the tip of its corner hook must land on the slope in front of its pocket (which pushes the
# long wall upright) and not on a flat top. Each lean is tried as the long wall moved straight out.
corner = s.box(s.W / 2 - 14, s.W / 2 + 2, s.L / 2 - 12, s.L / 2 + 2, s.ZWT - 12, s.ZWT + 12)
lw_c, ew_c = p["door wall"] ^ corner, p["end wall 1"] ^ corner
za = s.ZWT + 0.02 - s.HOOK_ARM
worst_lean = 0.0
e = s.HOOK_REACH - s.HOOK_TIP_W - s.FIT                  # the pocket's near side, into the long wall
x_lo = s.W / 2 - s.WT + e - s.HOOK_GUIDE - 0.05         # where the slope starts
for lean_mm in (0.25, 0.5, 1.0, 1.5, 2.0):
    lw_l = lw_c.translate([lean_mm, 0, 0])
    dz = 8.0
    while dz > 0 and overlap(ew_c.translate([0, 0, dz - 0.05]), lw_l) < 1e-4:
        dz -= 0.05
    touches = [c for c in (ew_c.translate([0, 0, dz - 0.05]) ^ lw_l).decompose() if c.volume() > 1e-4]
    ok = dz <= 0.05 or all(
        tb[1] >= s.L / 2 - s.WT - s.FIT - 0.05 and tb[4] <= s.L / 2 - s.WT + s.HOOK_T + s.FIT + 0.05
        and tb[0] - lean_mm >= x_lo and tb[5] <= za - s.FIT + 0.05
        for tb in (c.bounding_box() for c in touches))
    if not ok:
        break
    worst_lean = lean_mm
report(worst_lean >= 2.0, f"with a long wall leaning out up to {worst_lean} mm at the top, the end wall's hook tip lands "
                          f"on the slope in front of its pocket and pulls the long wall upright")


def long_flap(bit, bb):
    """The flap of siding over each corner hook, at the top of each end of a long wall."""
    c = bit.bounds()
    return (abs(abs((c[0] + c[2]) / 2 - (bb[3] - bb[0]) / 2) - s.L / 2) < 6 and c[3] > bb[4] - 25
            and bit.area() < 25)


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
    # layer of small bits (the undersides of the roof pegs), and on the long walls the flap of
    # siding over each corner hook.
    worst, flaps, longest = worst_overhang(whole, long_flap if n in LONGS else None)
    report(worst < 5,
           f"{n} has nothing steeper than 45 degrees that isn't a bridge of 20 mm or less ({worst:.1f} mm2 "
           f"worst layer" + (f"; the siding flap over each corner hook {flaps:.0f} mm2" if flaps else "") + ")")
    thin = max((c - c.offset(-0.2, RND).offset(0.2, RND)).area()
               for c in (whole.slice(0.125), whole.slice(0.35)))
    report(thin < 2, f"{n}: no knife edges on the bed ({thin:.2f} mm2 thinner than a line in the first two layers)")
    tb = trim_p.bounding_box()
    sb = siding.bounding_box()
    report(trim_p.volume() > 0 and abs(tb[5] - (s.WT + s.PROUD)) < 0.01 and tb[2] > s.WT - 0.01
           and sb[5] < tb[5] + 0.01,
           f"{n}: trim is {trim_p.volume() / 1000:.2f} cm3, all of it the top {s.PROUD} mm "
           f"({tb[2]:.2f} to {tb[5]:.2f} mm, siding colour no higher), so the colour only changes "
           f"on the last layers")
    if n in LONGS:
        v = p[n].trim_by_plane([0, 0, 1], s.ZWT + 0.001).volume()
        report(v == 0, f"{n}: nothing above the wall plates (the barn ends carry all of the gable)")
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
    worst, _, longest = worst_overhang(piece)
    report(foot > 0.9 * (bb[3] - bb[0]) * (bb[4] - bb[1]) and worst < 5,
           f"the {name} sheet prints flat on its underside ({foot:.0f} mm2 on the bed), nothing steeper than "
           f"45 degrees but its peg holes' roofs ({worst:.1f} mm2 worst layer, bridges up to {longest:.1f} mm)")

# the short corner in the fit test goes together the same way: long wall first, then end wall
lw, ew, cf = s.corner_test({n: p[n] for n in WALLS}, fl)
out_x = -1 if s.FIT_LONG == "back wall" else 1
ok = (overlap(lw, ew) < 0.001 and overlap(lw, cf) < 0.001 and overlap(ew, cf) < 0.001
      and overlap(lw.translate([0, 0, 0.3]), cf) > 0.05 and overlap(ew.translate([0, 0, 0.3]), cf) > 0.05
      and overlap(lw.translate([0, 0, 0.3]), ew) > 0.05 and overlap(ew.translate([0, 0.3, 0]), lw) > 0.05
      and overlap(lw.translate([0.3 * out_x, 0, 0]), ew) > 0.05)
report(ok, "the fit test's short corner snaps onto its bit of floor and hooks together like the real ones")

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
v = overlap(body, upper.translate([0, 0, -0.3]))
report(v > 0.5, f"lowered 0.3 mm an upper sheet runs into the barn ends, so it is resting on them ({v:.1f} mm3)")
v = overlap(body, lower.translate([-0.3 * nl[0], 0, -0.3 * nl[1]]))
report(v > 0.5, f"pushed 0.3 mm in, square to its slope, a lower sheet runs into the barn ends' steep edges "
                f"({v:.1f} mm3)")
for sh, n, d, words in ((upper, nu, du, "upper"), (lower, nl, dl, "lower")):
    lift = 0.05 * np.array([n[0], 0, n[1]])
    va = overlap(body, sh.translate(lift + [0, 1.0, 0]))
    vd = overlap(body, sh.translate(lift + [d[0], 0, d[1]]))
    report(min(va, vd) > 0.05, f"slid 1 mm along the barn ({va:.2f}) or down its slope ({vd:.2f} mm3), "
                               f"an {words} sheet is held by its pegs")
v = overlap(body, upper.translate([0, 0, 2.0])) + overlap(lower, upper.translate([0, 0, 2.0]))
report(v == 0, "lifted 2 mm straight up, an upper sheet is clear of the pegs and the lower sheet")
v = overlap(body, lower.translate([2 * nl[0], 0, 2 * nl[1]]))
report(v == 0, "pulled 2 mm out square to its slope, a lower sheet comes off its pegs")
v = overlap(upper, lower.translate([0.3 * nl[0], 0, 0.3 * nl[1]]))
report(v > 0.05, f"with the upper sheet on, its tail laps over the top of the lower sheet and keeps it in "
                 f"({v:.2f} mm3 when the lower sheet moves out 0.3 mm)")

# 3. the lofts rest on the long walls' top plates, under the roof
lofts = [s.loft(1), s.loft(-1)]
roof_all = s.union(list(sheets.values()))
for i, lf in enumerate(lofts):
    v = overlap(body, lf) + overlap(roof_all, lf)
    report(v < 0.01, f"loft {i + 1} fits between the walls and under the roof ({v:.4f} mm3)")
    v = overlap(body, lf.translate([0, 0, -0.1]))
    report(v > 0.5, f"loft {i + 1} rests on the long walls' top plates ({v:.1f} mm3 when lowered 0.1 mm)")
    v = min(overlap(body, lf.translate(t)) for t in ([0.3, 0, 0], [-0.3, 0, 0], [0, 0.3, 0], [0, -0.3, 0]))
    report(v > 0.05, f"loft {i + 1} can't slide: its lugs sit in notches in the plates ({v:.2f} mm3 when moved 0.3 mm)")
    v = overlap(body, lf.translate([0, 0, 2.0]))
    report(v == 0, f"loft {i + 1} lifts straight out with the roof off")

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

# 7. sizes at full size, as a check against the shop numbers
inch = 1 / s.S
report(abs(s.WALL_H * inch - 79.5) < 0.01, f"walls {s.WALL_H * inch:.1f} in floor to the top of the upper plate (shop: 79 1/2 in)")
line_peak = (s.ZPK - s.ZWT) * inch
truss_peak = line_peak - 0.4375 / math.cos(math.atan(s.UP_M))
report(abs(truss_peak - 43.75) < 0.01,
       f"barn roof {truss_peak:.2f} in from the top of the upper plate to the peak of the trusses (shop: 43 3/4 in at "
       f"8 ft wide), {line_peak:.2f} in to the top of the roof deck, as the 3D designer draws it")
eave = (s.EAVE_END[0] - s.W / 2) * inch
report(abs(eave - 1.734) < 0.01, f"eave {eave:.2f} in out from the wall, measured level (designer: 1.73 in)")
report(abs(s.DOOR_OPEN_W * inch - 48.25) < 0.01 and abs(s.DOOR_OPEN_H * inch - 71.5) < 0.01,
       "door opening 48 1/4 x 71 1/2 in, its head the loft header under the top plate")
hdr = (s.ZWT - s.PLATE_TOP - s.HEADER - s.ZF) * inch
report(abs(hdr - 71.5) < 0.01 and abs(s.WIN_TOP - s.DOOR_OPEN_H) < 1e-9,
       f"the loft header's underside is {hdr:.1f} in above the floor, the top of the door and of both windows")

print()
print("all checks passed" if fails == 0 else f"{fails} check(s) failed")
sys.exit(1 if fails else 0)
