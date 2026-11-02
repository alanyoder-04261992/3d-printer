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
flat = {name: s.to_print(s.WALL_TO_PRINT[name], s.two_colour(p[name], zone)) for name in WALLS}

# 1. every printed piece is one solid piece and fits the bed
for name, part in ([("floor", p["floor"])] + [(n, s.union(flat[n])) for n in WALLS] +
                   [("roof half", s.roof_to_print(roof)), ("door", door_all),
                    ("skids", p["skids"]), ("fit test", p["fit"])]):
    bb = part.bounding_box()
    size = (bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2])
    pieces = len(part.decompose())
    expect = {"skids": 2, "fit test": 7}.get(name, 1)
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


# 1a. the snap joints. Each wall stands on the floor, the floor holds it in, out and along,
# its barbs hold it down, and the corner hooks tie the tops together.
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
longs = s.union([p["door wall"], p["back wall"]])
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
for n in ("end wall 1", "end wall 2"):
    v = overlap(p[n].translate([0, 0, 0.3]), longs)
    report(v > 0.05, f"{n} can't lift out from under the long walls' corner hooks ({v:.2f} mm3 at 0.3 mm)")
    v = overlap(p[n].translate(toward(n, 0.3)), longs)
    report(v > 0.05, f"{n} can't pull away from the hook tips at the top corners ({v:.2f} mm3 at 0.3 mm)")
# the end walls lean out a little at the top until the long walls are on. Lowering a long wall,
# the tip of its corner hook must land on the slope in front of its pocket (which pushes the end
# wall upright) and not on a flat top. Each lean is tried as the end wall moved straight out.
corner = s.box(s.W / 2 - 12, s.W / 2 + 2, s.L / 2 - 14, s.L / 2 + 2, s.ZWT - 12, s.ZWT + 12)
lw_c, ew_c = p["door wall"] ^ corner, p["end wall 1"] ^ corner
za = s.ZWT - 0.15 - s.HOOK_ARM
worst_lean = 0.0
e = s.HOOK_REACH - s.HOOK_TIP_W - s.FIT                  # the pocket's near side, into the end wall
y_lo = s.L / 2 - s.WT + e - s.HOOK_GUIDE - 0.05         # where the slope starts
for lean_mm in (0.25, 0.5, 1.0, 1.5, 2.0):
    ew_l = ew_c.translate([0, lean_mm, 0])
    dz = 8.0
    while dz > 0 and overlap(lw_c.translate([0, 0, dz - 0.05]), ew_l) < 1e-4:
        dz -= 0.05
    touches = [c for c in (lw_c.translate([0, 0, dz - 0.05]) ^ ew_l).decompose() if c.volume() > 1e-4]
    ok = dz <= 0.05 or all(
        tb[0] >= s.W / 2 - s.WT - s.FIT - 0.05 and tb[3] <= s.W / 2 - s.WT + s.HOOK_T + s.FIT + 0.05
        and tb[1] - lean_mm >= y_lo and tb[5] <= za - s.FIT + 0.05
        for tb in (c.bounding_box() for c in touches))
    if not ok:
        break
    worst_lean = lean_mm
report(worst_lean >= 2.0, f"with an end wall leaning out up to {worst_lean} mm at the top, the long wall's hook tip lands "
                          f"on the slope in front of its pocket and pulls the end wall upright")
for n in ("door wall", "back wall"):
    v = overlap(p[n].translate(toward(n, 0.3)), ends)
    report(v > 0.05, f"{n} can't lean out of the end walls' corners at the top ({v:.2f} mm3 at 0.3 mm)")
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
    # less: the siding between studs, the skirt between posts, the roofs of the pockets, the
    # prong legs. Allowed: under 5 mm2 a layer of small bits (the undersides of the roof pegs),
    # and on the end walls the flap of siding over each corner hook, kept 0.6 mm clear of it.
    whole = s.union(flat[n])
    worst, flaps, longest, prev = 0.0, 0.0, 0.0, None
    for z0, z1 in layers(bb[5]):
        cs = whole.slice((z0 + z1) / 2)
        if prev is not None:
            left, span = overhangs(cs, prev)                # every bridge counted is 20 mm or less
            longest = max(longest, span)
            rest = 0.0
            for piece in left.decompose():
                c = piece.bounds()
                corner = (n.startswith("end") and abs(abs((c[0] + c[2]) / 2 - (bb[3] - bb[0]) / 2) - s.W / 2) < 6
                          and c[3] > bb[4] - 25 and piece.area() < 25)
                if corner:
                    flaps = max(flaps, piece.area())
                else:
                    rest += piece.area()
            worst = max(worst, rest)
        prev = cs
    report(worst < 5,
           f"{n} has nothing steeper than 45 degrees that isn't a bridge of 20 mm or less ({worst:.1f} mm2 "
           f"worst layer" + (f"; the siding flap over each corner hook {flaps:.0f} mm2" if flaps else "") + ")")
    # the first two layers must have nothing narrower than one 0.4 mm line (a knife edge on
    # the bed gets dropped or blobs into a joint)
    thin = max((c - c.offset(-0.2, RND).offset(0.2, RND)).area()
               for c in (whole.slice(0.125), whole.slice(0.35)))
    report(thin < 2, f"{n}: no knife edges on the bed ({thin:.2f} mm2 thinner than a line in the first two layers)")
    tb = trim.bounding_box()
    sb = siding.bounding_box()
    report(trim.volume() > 0 and abs(tb[5] - (s.WT + s.PROUD)) < 0.01 and tb[2] > s.WT - 0.01
           and sb[5] < tb[5] + 0.01,
           f"{n}: trim is {trim.volume() / 1000:.2f} cm3, all of it the top {s.PROUD} mm "
           f"({tb[2]:.2f} to {tb[5]:.2f} mm, siding colour no higher), so the colour only changes "
           f"on the last layers")
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

# the short corner in the fit test goes together the same way
lw, ew, cf = s.corner_test({n: p[n] for n in WALLS}, fl)
ok = (overlap(lw, ew) < 0.001 and overlap(lw, cf) < 0.001 and overlap(ew, cf) < 0.001
      and overlap(lw.translate([0, 0, 0.3]), cf) > 0.05 and overlap(ew.translate([0, 0, 0.3]), cf) > 0.05
      and overlap(ew.translate([0, 0, 0.3]), lw) > 0.05 and overlap(ew.translate([0, 0.3, 0]), lw) > 0.05
      and overlap(lw.translate([0.3, 0, 0]), ew) > 0.05)
report(ok, "the fit test's short corner snaps onto its bit of floor and hooks together like the real ones")

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
