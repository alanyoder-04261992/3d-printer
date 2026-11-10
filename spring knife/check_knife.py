"""Checks for the spring knife toy (v3). Run:  python3 check_knife.py

It walks a whole cycle and prints what it proved:
  * every moving part clears the handle and every other part all the way round a cycle, with
    the latch block out, on the rail or pushed in by a cam as it really would be, and with the
    knob bar and the block out at the end of the bar's play; and it goes together in the read me's
    order, each part let straight down without meeting anything;
  * the cams, against the block's real chamfered outline leaning as its load turns it, leave
    it alone until near the end of each stroke, let it go well before the knob reaches its pad
    with the bar and the rail anywhere in their play, push it fully in before the end, and never
    touch it at rest; the block can't catch on a corner; and a time-step model of it popping out
    (bouncing off the bar, held by friction while the pad stops the blade) has it biting the
    open catch before the blade bounces back there;
  * the latch arm, which bends twice every stroke, stays under 0.65 % (10,000 cycles of PLA)
    along it and at its root, on the cam and on the far ramp's kick, and the blade is no weaker
    round it than where it leaves the handle;
  * the band, the sleds and the risers do what the read me says at every stage;
  * a time-step model of a throw, from the parts' real sizes, gets the blade to its lock over
    the whole range of TPU stiffness, TPU losses, friction, print weight and the knife held
    flat or tilted up the worst way; the same model with the thumb leaving the knob early;
  * how hard the thumb pushes, counting the sled being carried twisting against its walls and the
    walls that hold the knob slider sideways rubbing as the push (or the return push) turns it and
    the thumb presses the knob in;
  * which band to fit: the stretch of the normal band hung from a half-litre bottle, worked out from the throw
    model's own band over TPU 10-30 MPa, and each band proven over every stretch the read me fits it at, fresh
    and aged (held stretched for months), and the window the band you fit must stretch in;
  * how hard things hit: a sled on its riser's TPU cap (every throw, a thumb flicked off the knob,
    a knob let go just before the trip), the knob and the thumb behind it landing on the knob's own
    TPU stop every throw, a let-go knob landing on it too, and the two knocks that are PLA on PLA
    (the lug picking up the parked sled, the latch block meeting the rail's end); and the stress all
    that puts in the sleds' wings, the risers' roots, the bar (bending in z on the room the plates
    really give it, with the plates where drawn and as far off as their pegs let them), the knob's
    saddle, lips and carriage, the guards the stops stand against, and the rail; the knob bar bending
    sideways, flat in its lane, as the knob's push and return push, its stops and the sleds landing on the
    risers' caps turn it, on eight versions (its carriage's fit as drawn and looser, the plates where drawn,
    off away from the blade and turned about either peg; their D-shaped peg holes keep them off the blade's
    side), with what the carriage's two ends raise it to from a plan FE of their real shape (itself checked
    against Peterson's stepped bar), the slider bent that way still clearing everything, with the thumb held
    on the knob too, riser B in its slot and the rib the knob's carriage rides; the knob stops' stiffness
    from a plane-stress model of their real shape; everything PLA that bends on every throw under 19.5 MPa;
  * the printed screws mesh with the top plate's posts with the shop's 0.35-0.4 mm clearance,
    and hold all three plates together; the posts stand in round pockets 0.4 all round; the
    gauge nuts, marked by 1, 2 and 3 cut-off corners, take the screws;
  * every part prints without anything hanging in the air, the carriage's roof bridge holds both its ends,
    every flat face sits on a layer line, no wall is thinner than two lines and no gap inside one part is
    under 0.45;
  * the three project files, read back, hold what make_knife.py means: each part on its own
    plate's bed, clear of the others, with its filament and its own settings (every TPU part
    solid), the knob's carriage roof bridged straight across by a modifier, and the fit test's latch
    block prints its top layers as slowly as on the knife's plate; the fit test's carriage piece slides
    on its rib piece as the knife's carriage does; each file holds what the read me lists, and no brim
    lies under a part.
"""

import itertools
import json
import math
import os
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode = True
import numpy as np        # noqa: E402
import manifold3d as m3   # noqa: E402
import make_knife as k    # noqa: E402

FAILS = []


def report(ok, what, detail=""):
    print(("ok   " if ok else "FAIL ") + what + (f"  [{detail}]" if detail else ""))
    if not ok:
        FAILS.append(what)


def overlap(a, b):
    return (a ^ b).volume()


TOL = 0.01      # mm3: faces that only touch

# ---------------------------------------------------------------- fixed parts
P1, P2, P3 = k.plate1(), k.plate2(), k.plate3()
SCREWS = k.union([k.screw(x, y) for x, y in k.SCREWS])
PAD_R, PAD_F = k.pad(k.PAD_X0), k.pad(k.PAD_X1 - k.PAD_L)
CUSH_R, CUSH_F = k.cushion("R"), k.cushion("F")
STOP_R, STOP_F = k.knob_stop("R"), k.knob_stop("F")
HANDLE = k.union([P1, P2, P3])
FIXED = {"base plate": P1, "middle plate": P2, "top plate": P3, "screws": SCREWS,
         "rear pad": PAD_R, "front pad": PAD_F, "rear cushion": CUSH_R, "front cushion": CUSH_F,
         "rear knob stop": STOP_R, "front knob stop": STOP_F}

# ---------------------------------------------------------------- where the latch block is
(W0A, W1A), (W0B, W1B) = k.windows()


def cam_y(x0, x1, s):
    """Lowest y the two cams reach under the block's outer face [x0, x1] at knob travel s, the
    face taken as square-edged: that puts the block at least as far in as it really goes, the
    worst case for the arm and its room in the overlap checks. When the cams really let the
    block go is worked out from its chamfered, leaning outline (cam_room, let_go)."""
    y = k.Y_OUT
    for top, back in ((k.CAM_A_TOP + s, True), (k.CAM_B_TOP + s, False)):
        if back:
            lo, hi = top - k.CAM_FLAT, top + k.RAMP
            prof = lambda x, t=top: k.Y_CAM if x <= t else k.Y_CAM + (x - t) / k.RAMP * (k.Y_OUT - k.Y_CAM)
        else:
            lo, hi = top - k.RAMP, top + k.CAM_FLAT
            prof = lambda x, t=top: k.Y_CAM if x >= t else k.Y_CAM + (t - x) / k.RAMP * (k.Y_OUT - k.Y_CAM)
        a, b = max(x0, lo), min(x1, hi)
        if a <= b:
            for x in (a, b, min(max(top, a), b)):
                y = min(y, prof(x))
    return y


def latch_state(c, s, mode):
    """(block's outer face y, rail shift) for blade c, knob s. mode 'held': the block is latched
    in a window (out, unless a cam is in) and, pressed into the rail's end, shifts the rail on
    its cushions. mode 'riding': the blade is on its way, so the block rides on the rail until
    it is wholly past the rail's end, then pops out."""
    x0, x1 = k.X_BLK + c, k.X_BLK + c + k.BLK_L
    yc = cam_y(x0, x1, s)
    if mode == "held":
        dx = max(0.0, x1 - k.RAIL_X0) if c < 43 else -max(0.0, k.RAIL_X1 - x0)
        return min(k.Y_OUT, yc), dx
    return min(k.Y_OUT, yc, rail_limit(x0, x1)), 0.0


def rail_limit(x0, x1, dx=0.0, n=48):
    """Furthest out the block's outer face can be with the block over [x0, x1]: its chamfered
    corners against the catches' flats and ramps."""
    y = 99.0
    ch = k.BLK_CHAMFER
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        r = k.rail_y(x, dx)
        if r is not None:
            y = min(y, r + max(0.0, ch - (x - x0), ch - (x1 - x)))
    return y


def squashed(man, x_cut, keep_below):
    """A TPU part squashed by a part that has reached x_cut (only what is left of it)."""
    bb = man.bounding_box()
    if keep_below:
        return man ^ k.box(bb[0] - 1, x_cut, bb[1] - 1, bb[4] + 1, bb[2] - 1, bb[5] + 1)
    return man ^ k.box(x_cut, bb[3] + 1, bb[1] - 1, bb[4] + 1, bb[2] - 1, bb[5] + 1)


def scene(c, s, mode):
    y, dx = latch_state(c, s, mode)
    pf, pb = k.sled_positions(c, s)
    fixed = dict(FIXED)
    if pf - k.SLED_LEN < k.PAD_X0 + k.PAD_L:
        fixed["rear pad"] = squashed(PAD_R, pf - k.SLED_LEN, True)
    if pb + k.SLED_LEN > k.PAD_X1 - k.PAD_L:
        fixed["front pad"] = squashed(PAD_F, pb + k.SLED_LEN, False)
    if dx > 0.1:
        fixed["front cushion"] = squashed(CUSH_F, k.SPINE_X1 + dx, False)
    elif dx < -0.1:
        fixed["rear cushion"] = squashed(CUSH_R, k.SPINE_X0 + dx, True)
    if k.STEM_X0 + s < k.stop_face_x()[0]:
        fixed["rear knob stop"] = squashed(STOP_R, k.STEM_X0 + s, True)
    if k.STEM_X1 + s > k.stop_face_x()[1]:
        fixed["front knob stop"] = squashed(STOP_F, k.STEM_X1 + s, False)
    parts = {"blade": k.carrier(c, k.arm_deflect_for(y)), "latch block": k.latch_block(c, y),
             "knob slider": k.knob_bar(s) + k.riser_cap("F", s) + k.riser_cap("B", s),
             "sled F": k.sled(pf, "F"), "sled B": k.sled(pb, "B"),
             "band": k.band_fitted(c, s), "rail": k.rail(dx)}
    return parts, fixed


def check_scene(c, s, worst, mode="held"):
    parts, fixed = scene(c, s, mode)
    names = list(parts)
    bad = []
    for i, a in enumerate(names):
        for fn, fm in fixed.items():
            v = overlap(parts[a], fm)
            if v > TOL:
                bad.append(f"{a}/{fn} {v:.3f}")
            worst[(a, fn)] = max(worst.get((a, fn), 0), v)
        for b in names[i + 1:]:
            v = overlap(parts[a], parts[b])
            if v > TOL:
                bad.append(f"{a}/{b} {v:.3f}")
            worst[(a, b)] = max(worst.get((a, b), 0), v)
    return bad


def frange(a, b, step):
    n = max(1, int(round(abs(b - a) / step)))
    return [a + (b - a) * i / n for i in range(n + 1)]


S_LO, S_HI = -k.KNOB_SOFT - k.STOP_SQ, k.THROW + k.KNOB_SOFT + k.STOP_SQ   # the knob as far as it may squash a stop
#                                   (the knob-landing checks prove it never comes near): the checks drive it this far
print("== The cycle, stage by stage")
STAGES = [("closed, knob back", 0.0, 0.0, "held"), ("closed, knob pulled past its end", 0.0, -k.SOFT, "held"),
          ("cocking, knob 10 mm", k.E_CATCH, 10.0, "held"), ("cocking, knob 22 mm", k.E_CATCH, 22.0, "held"),
          ("cocked, blade crept", k.C_COCK, 26.0, "held"), ("cam A has the block in", k.C_COCK, k.THROW - 1, "held"),
          ("thrown, blade 10 mm out", 10.0, k.THROW, "riding"), ("coasting", 50.0, k.THROW, "riding"),
          ("arriving", 86.0, k.THROW, "riding"), ("overrun into the pad", 86.0 + 3.0, k.THROW + k.SOFT, "riding"),
          ("open, knob forward", 86.0, k.THROW, "held"), ("pulling back 10 mm", 86.0 - k.E_CATCH, k.THROW - 10, "held"),
          ("cocked back", 86.0 - k.C_COCK, 2.0, "held"), ("cam B has the block in", 86.0 - k.C_COCK, 1.0, "held"),
          ("thrown back", 70.0, 0.0, "riding"), ("coasting back", 30.0, 0.0, "riding"),
          ("overrun into the rear pad", -3.0, -k.SOFT, "riding"),
          (f"knob snapped back, {k.STOP_SQ:.1f} into its rear stop", 0.0, S_LO, "held"),
          (f"knob snapped forward, {k.STOP_SQ:.1f} into its front stop", 86.0, S_HI, "held"),
          ("a stop left out: the knob back until its carriage meets its slot's end", 0.0, -k.KNOB_ROOM, "held"),
          ("a stop left out: the knob forward until its carriage meets its slot's end", 86.0, k.THROW + k.KNOB_ROOM, "held")]
worst = {}
for label, c, s, mode in STAGES:
    bad = check_scene(c, s, worst, mode)
    report(not bad, f"{label} (c {c:g}, s {s:g}): nothing overlaps", "; ".join(bad))

print("\n== Sweeps (every 0.5 mm)")
creep = lambda s_from_end: min(k.C_COCK, k.E_CATCH + max(0.0, s_from_end - 20) * 0.25)
paths = [("knob pushed forward, blade held shut", "held", [(creep(s), s) for s in frange(S_LO, k.THROW - 1, 0.5)]),
         ("blade thrown out, knob forward", "riding", [(c, k.THROW) for c in frange(k.C_COCK, 86 + 4.0, 0.5)]),
         ("knob pulled back, blade held open", "held", [(86 - creep(k.THROW - s), s) for s in frange(S_HI, 1.0, 0.5)]),
         ("blade thrown in, knob back", "riding", [(c, 0.0) for c in frange(86 - k.C_COCK, -4.0, 0.5)])]
for label, mode, pts in paths:
    bad = []
    for c, s in pts:
        b = check_scene(c, s, worst, mode)
        if b:
            bad.append(f"c {c:.1f} s {s:.1f}: " + "; ".join(b))
    report(not bad, f"{label}: {len(pts)} steps, nothing overlaps", " | ".join(bad[:4]))
# the arm pushes the block out against the bar, and nothing pushes the bar back in, so the bar can
# sit at the outer end of its play and the block out after it
Y_HI = k.Y_OUT + k.BAR_OUT
pts = frange(-(k.W_FAR - 0.5), 86 + k.W_FAR - 0.5, 0.5)
bad = [f"c {c:.1f}: {overlap(k.latch_block(c, Y_HI), P1):.3f}" for c in pts if overlap(k.latch_block(c, Y_HI), P1) > TOL]
report(not bad, f"bar out at the end of its play: the block, out after it to y {Y_HI:.2f}, clears the base plate anywhere along its "
                f"travel and overrun ({len(pts)} steps; its path and windows are cut to {k.WIN_Y1:.2f})", " | ".join(bad[:4]))
bad = []
for s in (S_LO, 0.0, k.THROW, S_HI):
    for dy in (-min(k.BAR_IN, k.GUIDE_FOOT, k.LANE_IN), k.GUIDE_LEG):   # in until a cam meets its lane's wall (riser B's slot
        #                                                        and the carriage's foot allow more), or out until the
        #                                                        carriage's leg meets its rib
        knob = (k.knob_bar(s) + k.riser_cap("F", s) + k.riser_cap("B", s)).translate([0, dy, 0])
        for fn in ("base plate", "middle plate", "top plate"):
            v = overlap(knob, FIXED[fn])
            if v > TOL:
                bad.append(f"s {s:g} {dy:+g} {fn} {v:.3f}")
        for dx in (-k.RAIL_MOVE, 0.0, k.RAIL_MOVE):
            v = overlap(knob, k.rail(dx))
            if v > TOL:
                bad.append(f"s {s:g} {dy:+g} rail shifted {dx:g} {v:.3f}")
        c_ = 0.0 if s < k.THROW / 2 else 86.0
        parts_, _ = scene(c_, s, "held")
        for nm in ("sled F", "sled B", "band"):
            v = overlap(knob, parts_[nm])
            if v > TOL:
                bad.append(f"s {s:g} {dy:+g} {nm} {v:.3f}")
report(not bad, f"and the knob slider, in or out at the ends of its play ({min(k.BAR_IN, k.GUIDE_FOOT, k.LANE_IN):g} in until a cam "
                f"meets its lane's wall, {k.GUIDE_LEG:g} out until its carriage's leg meets its rib), clears the handle, the rail and the sleds and band at both ends of its travel (the sideways check below "
                f"bends and turns it too)", " | ".join(bad))
# the latched block's top stands over the bar, beside the risers; on every cocking stroke a cap passes
# it. Drawn 0.1 proud on its inner face and its bottom (TPU prints a little fat), with the block lifted
# to the middle plate, the cap must still clear it
LIFT = k.Z1 - k.BLK_Z1
bad, n_cap = [], 0
for which, c_of, ss in (("F", creep, frange(0.0, k.THROW - 1, 0.5)),
                        ("B", lambda s: 86 - creep(k.THROW - s), frange(k.THROW, 1.0, 0.5))):
    for s in ss:
        c = c_of(s)
        cap = k.riser_cap(which, s)
        proud = cap + cap.translate([0, -0.1, 0]) + cap.translate([0, 0, -0.1])
        blk = k.latch_block(c, k.Y_OUT)
        v = max(overlap(proud, blk), overlap(proud, blk.translate([0, 0, LIFT])))
        n_cap += 1
        if v > TOL:
            bad.append(f"cap {which} s {s:.1f}: {v:.3f}")
report(not bad, f"the riser caps, standing on their risers' soles and feet (z {k.SOLE_TOP:.2f} and up), pass the latched block's top "
                f"(z {k.BLK_Z1:.2f}, {k.BLK_Z1 + LIFT:.2f} lifted to the middle plate) on every cocking stroke ({n_cap} steps, each cap "
                f"drawn 0.1 proud)", " | ".join(bad[:4]))


def drop_clear(part, below, step=0.2):
    """part lowered straight down from where it is clear of below to where it is drawn, in steps of a layer: the most it
    overlaps anything below on the way (mm3), and the height it was let down from."""
    bb, bl = part.bounding_box(), below.bounding_box()
    h = max(0.0, bl[5] - bb[2]) + 0.4
    region = below ^ k.box(bb[0] - 0.1, bb[3] + 0.1, bb[1] - 0.1, bb[4] + 0.1, bb[2] - 0.1, bb[5] + h + 0.1)
    worst = 0.0
    for i in range(int(round(h / step)) + 1):
        worst = max(worst, overlap(part.translate([0, 0, h - i * step]), region))
    return worst, h


# putting it together, as the read me has it: the knob slider, its riser caps on, let straight down into the base plate
# with the rail, its cushions and the knob stops in (its carriage over the rib, the knob out through the slot between the
# stops); the blade laid into its channel past it; the middle plate lowered over them all, the lug and the risers, caps and
# all, up through its slots; the pads, sleds and band put in; and the top plate lowered on. Nothing meets anything on the way
_s0 = k.THROW / 2                                           # the knob part way along, between its stops, as it goes in
_y0 = latch_state(0.0, _s0, "held")[0]
_slider = k.knob_bar(_s0) + k.riser_cap("F", _s0) + k.riser_cap("B", _s0)
_base = k.union([P1, CUSH_R, CUSH_F, k.rail(0.0), STOP_R, STOP_F])
_blade = k.carrier(0.0, k.arm_deflect_for(_y0)) + k.latch_block(0.0, _y0)
_pf, _pb = k.sled_positions(0.0, _s0)
_band_level = k.union([PAD_R, PAD_F, k.sled(_pf, "F"), k.sled(_pb, "B"), k.band_fitted(0.0, _s0)])
_seat = max(0.0, -k.PEG_FLAT)                               # the flats in the D-shaped peg holes push each plate this far out
steps_ = [("the knob slider into the base plate", _slider, _base),
          ("the blade into its channel past it", k.carrier(0.0, k.arm_deflect_for(_y0)), _base + _slider),
          ("the middle plate over them", P2.translate([0, _seat, 0]), _base + _slider + _blade),
          ("the top plate on", P3.translate([0, 2 * _seat, 0]), _base + _slider + _blade + P2.translate([0, _seat, 0]) + _band_level)]
got_ = [(what, *drop_clear(part, below)) for what, part, below in steps_]
report(all(v <= TOL for _, v, _ in got_),
       "putting it together: " + "; ".join(f"{what}, straight down from {h:.1f} mm up, meets nothing ({v:.3f} mm3)"
                                         for what, v, h in got_),
       "in the read me's order; the latch block goes in after the blade, along the bar's face with its arm pressed in")

print("\n== Latch and cams")


def block_turn(y_out):
    """Largest turn (radians) of the block in its slot with its outer face at y_out, from its
    real chamfered outline: only what is inside the carrier (y under 11.0) meets the walls."""
    poly = m3.CrossSection([k.block_poly(y_out)])
    inside = m3.CrossSection.square([40, 30]).translate([0, k.CAR_W / 2 - 30])
    room = k.BLK_L + 2 * k.BLK_SLOT
    lo, hi = 0.0, 0.6
    for _ in range(40):
        th = (lo + hi) / 2
        xc = k.BLK_X0 + k.BLK_L / 2
        b = (poly.translate([-xc, -k.CAR_W / 2]).rotate(math.degrees(th)).translate([xc, k.CAR_W / 2]) ^ inside).bounds()
        lo, hi = (th, hi) if b[2] - b[0] <= room else (lo, th)
    return lo


Y_LET = k.RAIL_Y0 + k.RAIL_CHAMFER                    # 11.45: the catch's corner; once the flat top of the block's
#                                                       bearing face is pushed below it, the two chamfers meet and,
#                                                       with PLA on PLA (friction under 0.4), the band pushes the
#                                                       block the rest of the way in
SLOPE_CAM = math.tan(math.radians(k.CAM_ANGLE))
RAIL_OUT = k.GROOVE_Y1 - k.SPINE_Y1                   # 0.25: the rail can sit this far out in its groove ...
RAIL_IN = 0.1                                         # ... and this far in, onto its catches' pockets' walls
bar_in = k.BAR_Y0 - k.RISER_SLOT_Y0                   # the thumb pressing the knob inward pushes the bar in this far,
#                                                       until the risers meet their slots' walls, and the block with it
LEANS = {}


def lean(y_out):
    """block_turn, remembered: it is slow."""
    key = round(y_out, 5)
    if key not in LEANS:
        LEANS[key] = block_turn(y_out)
    return LEANS[key]


def outline(c, y_out, th=0.0):
    """The block's real outline (block_poly, chamfers and all) at blade c, outer face at y_out,
    turned th (radians) in its slot about the slot's mouth: th > 0 turns its front end out, the
    way the closed latch's load turns it (the rail's end pushes its front face back above the
    slot, the slot's back wall pushes it on lower down); the open latch turns it the other way."""
    xc, yc = k.BLK_X0 + k.BLK_L / 2, k.CAR_W / 2
    co, si = math.cos(th), math.sin(th)
    return [(k.C0 + c + xc + (x - xc) * co - (y - yc) * si, yc + (x - xc) * si + (y - yc) * co)
            for x, y in k.block_poly(y_out)]


def touch_s(pts, cam, bar=0.0):
    """Knob travel s at which cam A (coming from behind) or cam B (from in front) first meets
    the outline pts with its 20 degree ramp, the bar shifted bar out."""
    lo = k.Y_CAM + bar
    if cam == "A":
        return min(x - k.CAM_A_TOP - (y - lo) / SLOPE_CAM for x, y in pts if y >= lo)
    return max(x - k.CAM_B_TOP + (y - lo) / SLOPE_CAM for x, y in pts if y >= lo)


def cam_face(x, s, bar=0.0):
    """y of the cams' faces at x, knob at s, bar shifted bar out: the lower of the two, or None."""
    ys = []
    a, b = k.CAM_A_TOP + s, k.CAM_B_TOP + s
    if a - k.CAM_FLAT <= x <= a + k.RAMP:
        ys.append(k.Y_CAM + bar + max(0.0, x - a) * SLOPE_CAM)
    if b - k.RAMP <= x <= b + k.CAM_FLAT:
        ys.append(k.Y_CAM + bar + max(0.0, b - x) * SLOPE_CAM)
    return min(ys) if ys else None


def top_y(pts, x):
    """Top of the convex outline pts at x, or None."""
    ys = []
    for (xa, ya), (xb, yb) in zip(pts, pts[1:] + pts[:1]):
        if min(xa, xb) - 1e-9 <= x <= max(xa, xb) + 1e-9:
            ys.append(ya if abs(xb - xa) < 1e-12 else ya + (yb - ya) * (x - xa) / (xb - xa))
            if abs(xb - xa) < 1e-12:
                ys.append(yb)
    return max(ys) if ys else None


def cam_room(c, s, bar=0.0, sgn=0):
    """Furthest out the block's outer face (block_poly's y_out) can be at blade c, knob s, with
    its real outline against the cams' faces, the bar shifted bar out; sgn +1 or -1: turned as
    the closed or the open latch's load turns it (0: square in its slot)."""
    y = k.Y_OUT + bar
    for _ in range(6):
        pts = outline(c, y, sgn * lean(y))
        a, b = k.CAM_A_TOP + s, k.CAM_B_TOP + s
        xs = [x for x, _ in pts] + [a - k.CAM_FLAT, a, a + k.RAMP, b - k.RAMP, b, b + k.CAM_FLAT]
        lo_x, hi_x = min(p[0] for p in pts), max(p[0] for p in pts)
        drop = 0.0
        for x in xs:
            if lo_x <= x <= hi_x:
                f, t = cam_face(x, s, bar), top_y(pts, x)
                if f is not None and t is not None:
                    drop = max(drop, t - f)
        if drop < 1e-7:
            break
        y -= drop
    return y


def let_go(c, cam, rail=0.0, bar=0.0):
    """Knob travel s at which a cam has pushed the leaning block in so far that the flat top of
    the face bearing on the catch (its front face for cam A, its back face for cam B) is down to
    the catch's corner, Y_LET with the rail shifted rail out, the bar shifted bar out."""
    i, sgn = (4, 1) if cam == "A" else (7, -1)
    lo, hi = k.Y_CAM - 1.0, k.Y_OUT + bar
    for _ in range(30):
        y = (lo + hi) / 2
        lo, hi = (lo, y) if outline(c, y, sgn * lean(y))[i][1] > Y_LET + rail else (y, hi)
    return touch_s(outline(c, lo, sgn * lean(lo)), cam, bar)


def rest_outline(c, bar, sgn):
    """The block out in a window, turned as its latch's load turns it, its highest corner on the bar."""
    y = k.Y_OUT + bar
    for _ in range(8):
        y -= max(p[1] for p in outline(c, y, sgn * lean(y))) - (k.Y_OUT + bar)
    return outline(c, y, sgn * lean(y))


def first_touch(c, cam):
    """Earliest the cam meets the block out in its window: square or leaning, bar drawn or out."""
    sgn = 1 if cam == "A" else -1
    ss = [touch_s(pts, cam, bar) for bar in (-bar_in, 0.0, k.BAR_OUT)
          for pts in (outline(c, k.Y_OUT + bar), rest_outline(c, bar, sgn))]
    return min(ss) if cam == "A" else max(ss)


VARIANTS = [(r, b) for r in (RAIL_OUT, 0.0, -RAIL_IN) for b in (-bar_in, 0.0, k.BAR_OUT)]   # the bar pushed in by the
#                                                       thumb lets the block go earliest, out at the end of its play latest
for c, s, label in ((0.0, 0.0, "closed rest"), (0.0, k.G_P, "closed rest, knob at the end of its play"),
                    (86.0, k.THROW, "open rest"), (86.0, k.THROW - k.G_P, "open rest, knob at the end of its play")):
    gap_a, gap_b = first_touch(c, "A") - s, s - first_touch(c, "B")
    report(min(gap_a, gap_b) > 0, f"{label}: neither cam touches the block (the nearer is {min(gap_a, gap_b):.1f} mm of knob away)")
S_STOP_F, S_STOP_R = k.stop_face_x()[1] - k.STEM_X1, k.stop_face_x()[0] - k.STEM_X0   # where the knob meets its stops
LETGO = {}
for c in (k.E_CATCH, k.C_TRIP, k.C_COCK):
    s1 = first_touch(c, "A")
    lets = [let_go(c, "A", r, b) for r, b in VARIANTS]
    LETGO[c] = lets
    s_full = next((s for s in frange(max(lets), k.THROW + 2, 0.01)
                   if max(cam_room(c, s, b) - b for b in (0.0, k.BAR_OUT)) <= k.Y_CAM + 1e-6), 99.0)
    report(s1 >= 18 and S_STOP_F - max(lets) >= 1.5 and s_full <= k.THROW,
           f"cam A, blade crept {c:g}: first touches the block at s {s1:.1f}, lets it go at s {min(lets):.1f} to {max(lets):.2f} "
           f"({S_STOP_F - max(lets):.2f} before the knob meets its stop), has it fully in by s {s_full:.1f}",
           f"rail out 0.25 to in 0.1, bar pushed in {bar_in:.1f} by the thumb, where drawn or out 0.25, the block leaning as "
           f"its load turns it")
for c in (86 - k.E_CATCH, 86 - k.C_TRIP, 86 - k.C_COCK):
    s1 = first_touch(c, "B")
    lets = [let_go(c, "B", r, b) for r, b in VARIANTS]
    s_full = next((s for s in frange(min(lets), -2, 0.01)
                   if max(cam_room(c, s, b) - b for b in (0.0, k.BAR_OUT)) <= k.Y_CAM + 1e-6), -99.0)
    report(s1 <= k.THROW - 18 and min(lets) - S_STOP_R >= 1.5 and s_full >= 0,
           f"cam B, blade crept {86 - c:g}: first touches the block at s {s1:.1f}, lets it go at s {max(lets):.1f} to {min(lets):.2f} "
           f"({min(lets) - S_STOP_R:.2f} before the knob meets its stop), has it fully in by s {s_full:.1f}")

th_rail = block_turn(k.Y_RAIL)
rise = k.BLK_L * math.sin(th_rail)
corner = k.Y_RAIL + rise - k.BLK_CHAMFER
report(corner < Y_LET, f"a block leaving its window can turn {math.degrees(th_rail):.1f} degrees in its slot; its chamfered trailing corner stays at y {corner:.2f}, inside the rail's {Y_LET:.2f}")
# out in a window the block rests on the bar, and the arm pushes it out after the bar to the outer end of the bar's play:
# there least of it is left in its slot, so it turns furthest
leans_out = [(y, block_turn(y), math.sin(block_turn(y)) * (y - k.CAR_W / 2)) for y in (k.Y_OUT, k.Y_OUT + k.BAR_OUT)]
_, th_out, lean_out = max(leans_out, key=lambda r: r[2])
report(lean_out < k.BLK_CHAMFER,
       f"out in a window, with the bar where drawn or out at the end of its play ({k.BAR_OUT}), it can turn at most "
       f"{math.degrees(th_out):.1f} degrees and leans at most {lean_out:.2f} at its face, less than its {k.BLK_CHAMFER} chamfers",
       f"{leans_out[0][2]:.2f} with the bar where drawn; {k.BLK_D:.2f} deep, {k.Y_OUT + k.BAR_OUT - k.BLK_D:.2f} to "
       f"{k.CAR_W / 2:.2f} of it in its slot with the bar out")
ok = True
for c in frange(k.E_CATCH, k.RAIL_X0 - k.X_BLK, 0.05):
    x0, x1 = k.X_BLK + c, k.X_BLK + c + k.BLK_L
    held = max(cam_room(c, k.THROW - 1, b) for b in (0.0, k.BAR_OUT)) <= k.Y_RAIL + 1e-6 or (x1 - k.RAIL_X0) >= 1.0
    ok = ok and held
report(ok, "on the way out, from the trip until the block is past the rail's end, cam A or 1 mm of rail holds it in")
ok = True
for c in frange(86 - k.E_CATCH, k.RAIL_X1 - k.X_BLK - k.BLK_L, 0.05):
    x0, x1 = k.X_BLK + c, k.X_BLK + c + k.BLK_L
    held = max(cam_room(c, 1.0, b) for b in (0.0, k.BAR_OUT)) <= k.Y_RAIL + 1e-6 or (k.RAIL_X1 - x0) >= 1.0
    ok = ok and held
report(ok, "on the way in, the same with cam B")
eng = min(k.Y_OUT - k.BLK_CHAMFER, k.SPINE_Y0) - Y_LET
rail_out = k.SPINE_Y0 - k.GROOVE_Y0                 # the block riding a catch pushes the rail out this far
bite = k.Y_OUT - bar_in - k.BLK_CHAMFER - (Y_LET + rail_out)
high = k.RAIL_TOP - (k.BLK_Z0 + (k.Z1 - k.BLK_Z1))   # the block lifted to the middle plate
report(bite >= 0.75 and high >= 1.4, f"at worst (bar pushed in, rail pushed out, block lifted) it still bites {bite:.2f} deep over {high:.2f} of height")
report(eng >= 1.0 and k.RAIL_TOP - k.BLK_Z0 >= 1.5,
       f"latched, the block bears {eng:.2f} mm deep on the rail's end, over {k.RAIL_TOP - k.BLK_Z0:.2f} mm of height")
E_PLA, G_PLA = 3500.0, 1300.0
EPS_FATIGUE = 0.0065        # the most a PLA part may bend on every stroke. Printed PLA bent back and forth (Ezeh and
#                             Susmel 2019) lasts about 10,000 cycles at about 20 MPa, 0.65 % at E 3.0 GPa, and the latch
#                             arm bends twice on every stroke (the cam pushes it in, then the far ramp kicks it), so the
#                             1 % it was held to before (PLA takes that a few times) gave it a few thousand at most
N_EVERY = 97                        # how many every-throw stresses the knocks below list (a guard against losing one)
FATIGUE_MPA = EPS_FATIGUE * 3000.0  # 19.5 MPa: what every PLA part that bends on every throw is held to. It is the median
#                             life at 10,000 cycles (printed at 0 degrees, bent both ways, Ezeh and Susmel 2019: they had
#                             10.4 MPa at 2 million cycles, slope 7.7, 20.7 at 10,000; a test at 20.2 lasted 10,935). Half of
#                             such parts would crack by then, so it is a pass line, not a safe design value: the 90 %
#                             survival curve gives 11-16 MPa. 15 or less is better
LETGO_MPA = 30.0            # a rare knock, the knob let go just before the trip: the design curve gives 0.61 of PLA's
#                             strength at 100 cycles and 0.40 at 1,000 (26 and 17 MPa for their 43 MPa PLA), so 30 holds for
#                             about 100 let-gos; 25 or less is the aim
arm_L = k.arm_L()
S_ARM, _, _, FLEX_ARM = k.arm_bend()
k_arm = E_PLA / FLEX_ARM                            # N/mm at the middle of its nose, from the arm's real taper
T_ARM = np.array([k.arm_t(k.ARM_ROOT - s_) for s_ in S_ARM])
EPS_ARM = 6 * k_arm * (arm_L - S_ARM) / (E_PLA * k.CAR_T * T_ARM ** 2)   # strain on its faces per mm its nose moves
r_t = k.ARM_RELIEF / T_ARM[0]
kt = 1 + 0.5 / math.sqrt(r_t)                       # a round-ended slot at a cantilever's root


def arm_strain(d):
    """The arm bent d at its nose: (its largest strain along it, away from the root's stress raiser; its strain at the
    root, with kt; how far from the root the first is)."""
    i = int(np.argmax(EPS_ARM[1:])) + 1
    return EPS_ARM[i] * d, EPS_ARM[0] * kt * d, S_ARM[i]


d_max = k.arm_deflect_for(k.Y_CAM - bar_in)         # the cam has the block in, the thumb pressing the bar in
st_along, st_root, s_at = arm_strain(d_max)
F_RAIL = k_arm * k.arm_deflect_for(k.Y_RAIL)
report(max(st_along, st_root) <= EPS_FATIGUE and k.arm_deflect_for(k.Y_OUT + k.BAR_OUT) > 0.02,
       f"latch arm: {k_arm:.2f} N/mm; the cam, the bar pushed in {bar_in:.1f}, bends it at most {d_max:.2f} mm: {st_along * 100:.2f} % "
       f"along it ({s_at:.1f} from its root), {st_root * 100:.2f} % at its round-ended root (limit {EPS_FATIGUE * 100:.2f} %: "
       f"10,000 cycles of PLA); with the bar out at the end of its play it still pushes the block on it, bent "
       f"{k.arm_deflect_for(k.Y_OUT + k.BAR_OUT):.2f}",
       f"{k.ARM_T_ROOT:.2f} thick at its root (flared {k.ARM_FLARE:.2f} more over the last {k.ARM_FLARE_L:g}), {k.ARM_T:.2f} at its nose, "
       f"{arm_L:.1f} long, round ends {k.ARM_RELIEF} (kt {kt:.2f}); presses the block on the rail with {F_RAIL:.2f} N, out in a "
       f"window with {k_arm * k.arm_deflect_for(k.Y_OUT):.2f} N")
x_tops = []
for y in (k.Y_OUT + k.BAR_OUT, k.Y_OUT, k.Y_RAIL, k.Y_CAM, k.Y_CAM - bar_in):
    xs = [x for x, _ in k.nose_poly(k.arm_deflect_for(y))]
    x_tops.append((min(xs), max(xs)))
lo, hi = min(a for a, _ in x_tops), max(b for _, b in x_tops)
flat0, flat1 = k.BLK_X0 + k.BLK_CHAMFER, k.BLK_X0 + k.BLK_L - k.BLK_CHAMFER
report(lo - (k.BLK_X0 - k.BLK_SLOT) >= 0.45 and (k.BLK_X0 + k.BLK_L + k.BLK_SLOT) - hi >= 0.45,
       f"the arm's nose, turning with the arm, stays {lo - (k.BLK_X0 - k.BLK_SLOT):.2f} and {(k.BLK_X0 + k.BLK_L + k.BLK_SLOT) - hi:.2f} clear of the slot's walls")
# the blade open and pushed at its tip, flat (its weak way): it pivots on the mouth and its carrier's back end bears on the
# channel, so the bending in it grows from nothing at its back end to the most where it leaves the handle. Round the arm and
# the block's slot it must be no weaker than there: what carries the bending is the blade's width across, less the free arm
X_MOUTH = k.HL - k.C0 - k.TRAVEL                    # 70: the blade's own x at the mouth, open
CS_BLADE = k.carrier().slice((k.CAR_Z0 + k.CAR_Z1) / 2)


def blade_width(x):
    """The width (y) that carries the open blade's bending at its own x: across it, less the free arm and its nose."""
    w = (CS_BLADE ^ m3.CrossSection.square([0.05, 60]).translate([k.C0 + x - 0.025, -30])).area() / 0.05
    if k.NOSE_C - k.NOSE_HW < x < k.ARM_ROOT:
        w -= k.arm_t(x)
    if abs(x - k.NOSE_C) < k.NOSE_HW:
        w -= k.NOSE_TOP - (k.ARM_Y0 + k.ARM_T)
    return w


BLADE_R = [(x / X_MOUTH * k.BLADE_W / blade_width(x), x) for x in frange(k.BLK_X0 - 1.0, k.ARM_ROOT + k.ARM_RELIEF + 1.0, 0.1)]
r_bl, x_bl = max(BLADE_R)
report(r_bl <= 1.0 and abs(blade_width(X_MOUTH - 0.5) - k.BLADE_W) < 0.01,
       f"the blade, open and pushed flat at its tip, is no weaker round the latch arm and the block's slot than where it leaves the "
       f"handle: at worst {r_bl:.2f} of the stress there, at its x {x_bl:.1f} ({blade_width(x_bl):.1f} of it carrying, "
       f"{x_bl / X_MOUTH:.2f} of the bending)", f"{k.BLADE_W:g} wide at the mouth, its x {X_MOUTH:g}")

print("\n== Band and sleds")
L_park = k.band_length(0.0, 0.0)
L_open = k.band_length(86.0, k.THROW)
L_max = k.band_length(k.E_CATCH, k.THROW - 1)
report(abs(L_park - L_open) < 1e-9 and abs(L_park - k.BAND_RELAXED - k.BAND_PRELOAD) < 1e-9,
       f"at rest, shut or open, the band is {L_park:.1f} eye to eye, {k.BAND_PRELOAD:g} mm over its printed {k.BAND_RELAXED:.1f}: it pulls on nothing but its sleds")
strain_b = (L_max - k.BAND_RELAXED) / k.BAND_RELAXED
report(strain_b < 0.45, f"fully cocked it is {L_max:.1f}: {strain_b * 100:.0f} % stretch")
for c, s, label in ((0.0, 0.0, "shut"), (86.0, k.THROW, "open")):
    pf, pb = k.sled_positions(c, s)
    gf, gb = (k.X_L0 + c) - pf, pb - (k.X_L0 + k.LUG_L + c)
    report(abs(gf - k.G_P) < 1e-9 if c == 0 else abs(gb - k.G_P) < 1e-9,
           f"{label}: sled F {gf:.1f} behind the lug, sled B {gb:.1f} in front of it, both on their risers")
pf, pb = k.sled_positions(k.E_CATCH, 15.0)
report(abs(pf - (k.X_L0 + k.E_CATCH)) < 1e-9, "cocking: sled F stays on the lug while the bar carries sled B forward")
pf, pb = k.sled_positions(86.0 - k.E_CATCH, 13.0)
report(abs(pb - (k.X_L0 + k.LUG_L + 86 - k.E_CATCH)) < 1e-9, "cocking back: sled B stays on the lug while the bar carries sled F back")
S_TRIP = min(LETGO[k.C_TRIP])          # earliest let-go, the blade crept to the rail and into its cushions
S_TRIP_LATE = max(LETGO[k.C_TRIP])     # latest (the band's stretch at the trip is the same however far it crept)
powered = S_TRIP - k.G_P - k.C_TRIP
report(powered > 20, f"the band throws the blade at least {powered:.1f} mm (more if the thumb keeps going after the trip), then it coasts the rest free of it")


# ---------------------------------------------------------------- mass properties
RHO = 1.24e-3                                    # g/mm3, PLA


def mass_props(man):
    """Volume (mm3), centre (x, y) and the second moment about z through the centre (mm5)."""
    mesh = man.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].astype(float)
    t = np.asarray(mesh.tri_verts)
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    vol6 = np.einsum("ij,ij->i", a, np.cross(b, c))
    V = vol6.sum() / 6
    cen = ((a + b + c) * vol6[:, None]).sum(0) / 24 / V
    def second(i):
        s = a[:, i] + b[:, i] + c[:, i]
        return (vol6 / 120 * (a[:, i] ** 2 + b[:, i] ** 2 + c[:, i] ** 2 + s ** 2)).sum()
    izz = second(0) + second(1) - V * (cen[0] ** 2 + cen[1] ** 2)
    return V, cen, izz


V_SLED, CEN_SLED, IZZ_SLED = mass_props(k.sled(0.0, "F"))
m_blade_solid = (k.carrier().volume() + k.latch_block().volume()) * RHO
m_bar = k.knob_bar().volume() * RHO
m_sled = V_SLED * RHO
m_knob = (k.knob_bar() ^ k.box(k.STEM_X0 - 1, k.STEM_X1 + 1, k.KNOB_Y0 - 0.01, 40, -1, 20)).volume() * RHO
r2_sled = IZZ_SLED / V_SLED
y_hit = (k.BAR_Y0 + k.RISER_Y1) / 2
m_turn = m_sled / (1 + (y_hit - CEN_SLED[1]) ** 2 / r2_sled)   # what the wing feels of the sled when a riser hits it
A_band = k.BAND[0] * k.BAND[1]
K_CUSH_AREA = (k.SPINE_Y1 - k.SPINE_Y0) * (k.CUSH_TOP - k.RAIL_Z0)
CUSH_FREE = k.CUSH_L - k.CUSH_HELD
G_ACC = 9.81e-3                                  # N per g
FC_MISC = 0.1                                    # N: the band and sled F rubbing, the carrier on its floor


def k_cush(E_tpu):
    """A rail cushion (N/mm): its 8 mm free of the groove's grip squashed end on."""
    return E_tpu * K_CUSH_AREA / CUSH_FREE


# where the block is, and how hard the arm presses it, all along a throw (the in-throw is its mirror)
C_GRID = [k.C_TRIP + 0.05 * i for i in range(int((87.5 - k.C_TRIP) / 0.05) + 1)]
Y_GRID = [latch_state(c, k.THROW, "riding")[0] for c in C_GRID]
N_GRID = [k_arm * k.arm_deflect_for(y) for y in Y_GRID]
SLOPE = [0.0] + [max(0.0, (Y_GRID[i - 1] - Y_GRID[i]) / 0.05) for i in range(1, len(C_GRID))]


def tilt(mu):
    """The worst way to hold the knife for a throw, tilted up th from flat: the weight pulls a part back
    along the channel (sin th) and presses the rest on a wall (cos th, rubbing mu of it). Their sum is
    largest at tan th = 1 / mu (68 degrees at 0.4), sqrt(1 + mu^2) of the weight. Returns (that share,
    sin th). This used to count the weight in full both ways at once, (1 + mu) of it, 1.4 at 0.4: held
    straight up the blade doesn't press on a wall at all, so that was 0.32 of the blade's weight, 0.044
    N, too much."""
    th = math.atan(1 / mu)
    return math.sin(th) + mu * math.cos(th), math.sin(th)


def friction(c, mu, fill, up=False):
    """Friction on the blade at c while it runs (N): the arm presses the block on a catch, a cam
    or the knob bar and the carrier on the far channel wall; where a ramp pushes the block in,
    the ramp's push; and the blade's weight: held flat, rubbing on the floor; up: the knife tilted
    up the worst way (tilt)."""
    i = min(max(int(round((c - C_GRID[0]) / 0.05)), 0), len(C_GRID) - 1)
    N, sl = N_GRID[i], SLOPE[i]
    m_b = m_blade_solid * fill
    push = N * math.tan(math.atan(sl) + math.atan(mu)) if sl > 0 else mu * N
    return FC_MISC + mu * N + push + m_b * G_ACC * (tilt(mu)[0] if up else mu)


def k_pad(E_tpu):
    return E_tpu * (2 * k.PAD_HW * k.SLED_H) / k.PAD_L


AGED = (0.8, 0.9)                   # an aged band: held stretched 14 % for good, TPU relaxes and takes a set (its pull at rest
#                                     x 0.8) and softens a little with use (its stiffness x 0.9)


def throw(E_tpu, h, mu, fill, up=False, band=k.BAND, dt=2e-6, mu_push=0.046, follow=False, aged=False):
    """One throw from the trip. E_tpu MPa; h TPU loss on unloading; mu PLA on PLA; fill:
    printed weight over solid; up: knife tilted up the worst way (tilt). follow: the thumb has pushed
    the knob on to where its sled meets its pad, 0.1 into its stop (the knob-landing checks have it
    squash its stop far more than that: the most the band can give), else it stopped where the block
    let go (the least). aged: the band as it is after months fitted (AGED).
    Returns a dict."""
    kb = E_tpu * band[0] * band[1] / k.BAND_RELAXED * (AGED[1] if aged else 1.0)
    pre = k.BAND_PRELOAD * (AGED[0] if aged else 1.0)
    m = (m_blade_solid + m_sled) * fill / 1000      # kg: sled F rides along while the band pulls
    sled_up = m_sled * fill * G_ACC * tilt(mu)[1] if up else 0.0   # and, tilted up, its weight pulls it back
    c0 = k.C_TRIP
    stroke = ((k.THROW + k.SOFT if follow else S_TRIP) - k.G_P) - c0
    x, v = 0.0, 0.0
    while x < stroke:
        T = (1 - h) * kb * (pre + stroke - x)
        F = T - friction(c0 + x, mu, fill, up) - mu_push * T - sled_up
        if F <= 0 and v <= 1e-9:
            return {"reached": False, "stop": c0 + x}
        v += F / m * 1000 * dt
        x += v * dt
    m_b = m_blade_solid * fill / 1000
    E = 0.5 * m_b * (v / 1000) ** 2 * 1000           # mJ; sled F stops on its riser
    c, E_c, used = c0 + stroke, E, 0.0
    c_lock = (k.RAIL_X1 - k.X_BLK) + 0.3
    while c < 86 + k.G_P:
        w = friction(c, mu, fill, up) * 0.05
        if c < c_lock and E_c - w <= 0:
            return {"reached": False, "stop": c}
        E_c -= w
        c += 0.05
    E_arr = max(E_c, 0.0)
    Fc = friction(86.0, mu, fill, up)
    kp = k_pad(E_tpu)
    m_s = m_sled * fill
    E_arr_pad = E_arr * m_b * 1000 / (m_b * 1000 + m_s)          # the lug picks up sled B on the way
    squash = math.sqrt(2 * E_arr_pad / kp)
    E_reb = max(0.45 * E_arr_pad - Fc * (squash + k.G_P + k.SOFT + k.E_CATCH), 0.0)   # TPU gives back about 45 %
    k_c = k_cush(E_tpu)
    d_cush = math.sqrt(2 * E_reb / k_c)
    v_arr = math.sqrt(2 * E_arr / 1000 / m_b) if E_arr > 0 else 0.0
    return {"reached": True, "E_throw": E, "v_release": v / 1000, "E_arrive": E_arr, "squash": squash, "F_pad": kp * squash,
            "overrun": k.G_P + k.SOFT + squash, "E_rebound": E_reb, "d_cush": d_cush, "F_cush": k_c * d_cush,
            "v": v_arr, "Fc": Fc, "m_b": m_b * 1000, "kp": kp}


print("\n== A throw, step by step (the in-stroke is its mirror)")
mid = (k.RAIL_X0 + k.RAIL_X1) / 2 - k.X_BLK
print(f"     masses, printed solid: blade {m_blade_solid:.1f} g, knob slider {m_bar:.2f} g, each sled {m_sled:.2f} g; friction "
      f"{friction(mid, 0.2, 0.8):.2f}-{friction(mid, 0.4, 1.0, True):.2f} N between the catches, {friction(k.C_TRIP + 3, 0.2, 0.8):.2f}-"
      f"{friction(k.C_TRIP + 3, 0.4, 1.0, True):.2f} N on a catch (PLA on PLA 0.2-0.4, flat or tilted up)")
report(min(Y_GRID[int((mid - k.C_TRIP) / 0.05) - 100:int((mid - k.C_TRIP) / 0.05) + 100]) >= k.Y_OUT - 1e-9,
       f"between the catches the block is out against the knob bar, pressed with only {k_arm * k.arm_deflect_for(k.Y_OUT):.2f} N; "
       f"on a catch with {F_RAIL:.2f} N")
MU = (0.2, 0.3, 0.4)
grid = list(itertools.product((15.0, 20.0, 26.0), (0.1, 0.2, 0.3), MU, (0.6, 1.0), (False, True)))
res = [(g, throw(*g)) for g in grid]
fails = [g for g, r in res if not r["reached"]]
oks = [r for g, r in res if r["reached"]]
report(not fails, f"band: the blade reaches its lock in all {len(grid)} cases (TPU 15-26 MPa, losses 10-30 %, PLA friction 0.2-0.4, "
                  f"printed 60-100 % solid, held flat or tilted up the worst way)",
       "misses: " + ", ".join(f"E{g[0]:.0f} h{g[1]} mu{g[2]} fill{g[3]}{' up' if g[4] else ''}" for g in fails))
grid_s = list(itertools.product((10.0, 12.5, 15.0), (0.1, 0.2, 0.3), MU, (0.6, 1.0), (False, True)))
rs = [(g, throw(*g, band=k.BAND_STRONG)) for g in grid_s]
report(all(r["reached"] for _, r in rs), f"strong band: the same with a soft TPU (10-15 MPa), {len(grid_s)} cases",
       ", ".join(str(g) for g, r in rs if not r["reached"]))
oks += [r for _, r in rs if r["reached"]]
grid_soft = list(itertools.product((26.0, 30.0), (0.1, 0.2, 0.3), MU, (0.6, 1.0), (False, True)))
rs = [(g, throw(*g, band=k.BAND_SOFT)) for g in grid_soft]
report(all(r["reached"] for _, r in rs), f"soft band: the same with a stiff TPU (26-30 MPa), {len(grid_soft)} cases",
       ", ".join(str(g) for g, r in rs if not r["reached"]))
oks += [r for _, r in rs if r["reached"]]


def crit_extra(E_tpu, h, band=k.BAND, aged=False):
    """Extra friction (N) on top of the worst case (PLA 0.4, solid, tilted up the worst way) a throw can still take."""
    lo, hi = 0.0, 5.0
    global FC_MISC
    base = FC_MISC
    for _ in range(30):
        mid = (lo + hi) / 2
        FC_MISC = base + mid
        ok_ = throw(E_tpu, h, 0.4, 1.0, True, band, aged=aged)["reached"]
        lo, hi = (mid, hi) if ok_ else (lo, mid)
    FC_MISC = base
    return lo


report(crit_extra(15, 0.3) > 0.1, f"margin: on top of the worst friction, a throw can still take {crit_extra(20, 0.15):.2f} N more nominal, "
                                  f"{crit_extra(15, 0.3):.2f} N with a soft, lossy TPU, {crit_extra(10, 0.3, k.BAND_STRONG):.2f} N with the strong band in a very soft one")
nom = throw(20.0, 0.15, 0.3, 0.9)
print(f"     nominal throw: {nom['E_throw']:.0f} mJ when the band lets go; arrives at {nom['v']:.1f} m/s with {nom['E_arrive']:.0f} mJ, "
      f"squashes the pad {nom['squash']:.1f} mm ({nom['F_pad']:.0f} N), bounces back into the rail with {nom['E_rebound']:.0f} mJ "
      f"({nom['d_cush']:.1f} mm of cushion, {nom['F_cush']:.0f} N)")
oks = [throw(*g, follow=True) for g in grid] + [throw(*g, band=k.BAND_STRONG, follow=True) for g in grid_s] + \
    [throw(*g, band=k.BAND_SOFT, follow=True) for g in grid_soft]          # the knocks: the thumb pushed on to the end
oks = [r for r in oks if r["reached"]]
print(f"     with the thumb pushing the knob on to its end the band gives up to {max(r['E_throw'] for r in oks):.0f} mJ; "
      f"the arrivals below count that")
over = max(r["overrun"] for r in oks)
report(over + 0.5 <= k.W_FAR, f"hardest arrival: overrun {over:.1f} mm; the far end of each window is {k.W_FAR:.1f} mm on")
pad_sq = max(r["squash"] for r in oks)
free = k.PAD_L - k.PAD_IN
report(pad_sq / k.PAD_L < 0.4 and pad_sq < free - 0.5,
       f"pads squash at most {pad_sq:.1f} of {k.PAD_L} mm ({max(r['F_pad'] for r in oks):.0f} N); {free:.1f} of each stands out of its pocket")
cu = max(r["d_cush"] for r in oks)
report(cu / CUSH_FREE < 0.45 and cu < k.RAIL_MOVE - 0.2, f"rail cushions squash at most {cu:.1f} of the {CUSH_FREE:.0f} mm free of their grip "
       f"({max(r['F_cush'] for r in oks):.0f} N on the block); the catches can move {k.RAIL_MOVE}")

# the block has to pop back out over the open catch's end, and bite it, before the blade bounces
# back there off its pad
X_A = np.linspace(k.NOSE_C - k.NOSE_HW, k.ARM_ROOT, 601)
_q = np.array([k.arm_t(x) * k.arm_dy(x, 1.0) ** 2 for x in X_A])
m_arm = RHO * k.CAR_T * float(((_q[1:] + _q[:-1]) / 2 * np.diff(X_A)).sum())   # the arm, each bit counted by its share of
#                                                                   the nose's movement squared (Rayleigh's way: 0.24 of a
#                                                                   plain arm's mass to the nose), its tip past the nose too
M_BLK = k.latch_block().volume() * RHO
M_NOSE = k.prism(k.nose_poly(0.0), k.CAR_Z0, k.CAR_Z1).volume() * RHO
m_pop = M_BLK + M_NOSE + m_arm                                    # g: what the arm throws out, the block, its nose and
#                                                                   the arm
w_arm = math.sqrt(k_arm * 1000 / (m_pop / 1000))                  # rad/s
d_rail = k.arm_deflect_for(k.Y_RAIL)
Y_TAB = np.arange(10.0, 15.5, 0.01)
D_TAB = np.array([k.arm_deflect_for(y) for y in Y_TAB])
D_FLAT = k.SEG_FLAT + k.BLK_L - k.BLK_CHAMFER                     # from the far ramp's foot until the block's back face
#                                                                   is past the catch's end


def pop_bites(arrivals, kick, es=(0.3, 0.5), mus=MU, unload=0.6, dt=0.0005):
    """A time-step model of the block popping out into the open window, for every arrival and
    every case: restitution off the knob bar 0.3 or 0.5, PLA friction 0.2-0.4, the rail where
    drawn or pushed out 0.25 by the riding block (the block starts on its face and has to bite
    past its corner), the bar where drawn, pushed in 0.3 by the thumb or out 0.25. From the
    moment the block's back face passes the catch's end (t = 0) to the moment the blade is back
    there: the lug meets sled B (a knock: the carrier's speed drops, its slot wall presses the
    block), sled B runs on to its pad, and the pad stops them in a half sine (peak v2 x
    sqrt(kp / (m_b + m_s)), 0.6 of that while it unloads), all the while pressing the block on
    its slot's front wall, so friction holds it against the arm; then they come back at 0.6 of
    v2. The block bounces off the bar. kick: it starts swinging from the far ramp's throw (moving
    in at the blade's speed x tan 22, bouncing on the catch's flat until its back face is past
    the end), else from rest on the flat. Units mm, ms, g, N. Returns the bites (mm) at the
    return, one per case."""
    rows = []
    for r in arrivals:
        for e, mu, ry, yb in itertools.product(es, mus, (0.0, RAIL_OUT), (k.Y_OUT - bar_in, k.Y_OUT, k.Y_OUT + k.BAR_OUT)):
            rows.append((r["v"], r["m_b"], r["kp"], e, mu, ry, yb))
    v, m_b, kp, e, mu, ry, yb = (np.array(col) for col in zip(*rows))
    m_s = m_sled
    v2 = v * m_b / (m_b + m_s)
    t1 = (k.E_CATCH + k.G_P) / v
    t2 = t1 + k.SOFT / v2
    om = np.sqrt(kp / (m_b + m_s))                  # rad/ms: (N/mm) / g = 1e6 / s2
    t_pad = math.pi / om
    t3 = t2 + t_pad
    t_win = t3 + (k.SOFT + k.G_P + k.E_CATCH) / np.maximum(0.6 * v2, 1e-3)
    y_flat = k.RAIL_Y0 + ry
    y, vy = y_flat.copy(), np.zeros_like(v)
    if kick:
        vy = -v * 1.05 * math.tan(math.radians(k.SEG_RAMP))
        t_end, t = D_FLAT / (v * 1.05), 0.0
        while t < t_end.max():
            on = t < t_end
            vn = vy + k_arm * np.interp(y, Y_TAB, D_TAB) / m_pop * dt
            yn = y + vn * dt
            hit = yn >= y_flat
            vn = np.where(hit & (vn > 0), -e * vn, vn)
            yn = np.where(hit, y_flat, yn)
            vy, y = np.where(on, vn, vy), np.where(on, yn, y)
            t += dt
    knocked = np.zeros(len(v), bool)
    dv_knock = mu * M_BLK * (v - v2) / m_pop
    t = 0.0
    while t < t_win.max():
        on = t < t_win
        F = k_arm * np.interp(y, Y_TAB, D_TAB)
        ph = om * (t - t2)
        acc = np.where((t >= t2) & (t < t3), v2 * om * np.sin(np.clip(ph, 0, math.pi)), 0.0)
        acc = np.where(t >= t2 + t_pad / 2, unload * acc, acc)
        fr = mu * M_BLK * acc
        moving = np.abs(vy) > 1e-6
        sgn = np.where(moving, np.sign(vy), 1.0)
        vn = vy + (F - sgn * fr) / m_pop * dt
        vn = np.where((~moving & (F <= fr)) | (moving & (vn * vy < 0) & (F <= fr)), 0.0, vn)
        kn = ~knocked & (t >= t1)
        vn = np.where(kn, np.sign(vn) * np.maximum(np.abs(vn) - dv_knock, 0.0), vn)
        knocked |= kn
        yn = y + vn * dt
        hit = yn >= yb
        vn = np.where(hit, -e * vn, vn)
        yn = np.where(hit, yb, yn)
        vy, y = np.where(on, vn, vy), np.where(on, yn, y)
        t += dt
    return y - k.BLK_CHAMFER - (Y_LET + ry), rows


bites, per_throw = [], {}
for kick in (False, True):
    b, rows = pop_bites(oks, kick)
    bites += list(b)
    n_case = len(rows) // len(oks)
    for i in range(len(oks)):
        per_throw[i] = min(per_throw.get(i, 99.0), float(b[i * n_case:(i + 1) * n_case].min()))
worst_bite = min(bites)
under = sum(1 for x in per_throw.values() if x < 0.75)
F_hard, h_bite = max(r["F_cush"] for r in oks), k.RAIL_TOP - k.BLK_Z0
report(worst_bite >= 0.45, f"the block pops back out and bites the open catch {worst_bite:.2f} deep at worst when the blade comes back off its pad, "
       f"over {len(bites)} cases of the {len(oks)} arrivals; {under} of the {len(oks)} throws come back under 0.75 in their worst case "
       f"(limit 0.45: the hardest bounce, {F_hard:.0f} N, over {worst_bite:.2f} x {h_bite:.2f} mm of catch is {F_hard / (worst_bite * h_bite):.0f} MPa)",
       "a time-step model: the bar bouncing it back (restitution 0.3-0.5), the pad's stop pressing it on its slot's wall "
       "(PLA 0.2-0.4), the rail where drawn or out 0.25, the bar where drawn, in 0.3 or out 0.25, from rest or swinging from the far ramp")
SOLID_OKS = [r for r in oks if r["m_b"] >= 0.9 * m_blade_solid]   # the moving parts print solid
v_far = max(r["v"] for r in SOLID_OKS) * 1.05                       # the blade meets the far ramp a little before it arrives
v_in = v_far * math.tan(math.radians(k.SEG_RAMP))                   # m/s = mm/ms: the ramp throws the block in this fast
d_kick = math.sqrt(d_rail ** 2 + (v_in / (w_arm / 1000)) ** 2)     # the arm's spring takes that speed
room = k.arm_room() + k.ARM_GAP
kick_along, kick_root, kick_at = arm_strain(d_kick)
report(d_kick <= room - 0.05 and max(kick_along, kick_root) <= EPS_FATIGUE,
       f"the far ramp throws the block in at up to {v_in:.1f} m/s; the arm then bends {d_kick:.2f} mm ({kick_along * 100:.2f} % along it, "
       f"{kick_root * 100:.2f} % at its root; limit {EPS_FATIGUE * 100:.2f} %), inside the {room:.2f} mm of room under it",
       f"the arm's spring takes the block's speed: {k_arm:.2f} N/mm against {m_pop * 1000:.0f} mg (block {M_BLK * 1000:.0f}, nose "
       f"{M_NOSE * 1000:.0f}, arm {m_arm * 1000:.0f})")

def plate_along(edges, X):
    """The base plate's material along the line x = X, as (y0, y1) pieces, from one slice's edges."""
    xa, ya, xb, yb = edges.T
    m = ((xa <= X) & (xb > X)) | ((xb <= X) & (xa > X))
    y = np.sort(ya[m] + (yb[m] - ya[m]) * (X - xa[m]) / (xb[m] - xa[m]))
    return zip(y[0::2], y[1::2])


def along_y(man, z, x):
    """The pieces (y0, y1) of man's slice at height z along the line x."""
    return list(plate_along(slice_edges(man.slice(z)), x))


def along_all(edges, Xs):
    """plate_along for every X in Xs at once: [(lo, hi) pieces] for each."""
    xa, ya, xb, yb = edges.T[:, :, None]
    m = ((xa <= Xs) & (xb > Xs)) | ((xb <= Xs) & (xa > Xs))
    with np.errstate(divide="ignore", invalid="ignore"):
        y = np.where(m, ya + (yb - ya) * (Xs - xa) / np.where(xb == xa, 1.0, xb - xa), np.inf)
    y = np.sort(y, axis=0)
    out = []
    for j in range(len(Xs)):
        c = y[:, j][np.isfinite(y[:, j])]
        out.append(list(zip(c[0::2], c[1::2])))
    return out


def beam_k(L, EI):
    return EI / L ** 3 * np.array([[12, 6 * L, -12, 6 * L], [6 * L, 4 * L * L, -6 * L, 2 * L * L],
                                   [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L * L, -6 * L, 4 * L * L]])


def beam_kg(L):
    """The P-delta stiffness of an element under a unit push along it."""
    return 1 / (30 * L) * np.array([[36, 3 * L, -36, 3 * L], [3 * L, 4 * L * L, -3 * L, -L * L],
                                    [-36, -3 * L, 36, -3 * L], [3 * L, -L * L, -3 * L, 4 * L * L]])


# ---- the knob bar sideways. The thumb pushes the knob 7.3 mm out to the side of the bar's line, and a knob stop pushes
# it back 6.5 mm out, so every push and every landing also turns the knob slider flat on its lane, about z. The knob's
# carriage (the knob, the roof and the bar's inner leg, 38 long) takes that turn on its rib, a sliding fit each side over
# its whole length, and the plain bar each side of it, free in the knob's slot, bends only as far as the carriage still
# turns in its play and bows under the push through it. Worked out as a beam lying flat, x along it and y across, on
# contacts read off the three plates' slices all up the slider's height (the TPU knob stops left out: squashed TPU holds
# nothing sideways), with the slider's real section and mass along it
YAW_H = 0.5
YAW_ZS = np.arange(k.BAR_Z0 + 0.1, k.KNOB_TOP, 0.2)
YAW_XS = np.arange(k.bar_x(0)[0], k.bar_x(0)[1] + 1e-9, YAW_H)
YAW_XM = (YAW_XS[:-1] + YAW_XS[1:]) / 2
Y_AXIS = (k.BAR_Y0 + k.BAR_Y1) / 2                   # the plain bar's line: forces are taken about it
W_BAR = k.BAR_Y1 - k.BAR_Y0
I_PLAIN = (k.BAR_Z1 - k.BAR_Z0) * W_BAR ** 3 / 12      # the plain bar, flat (mm4)


def yaw_sections():
    """Area, y of the middle and the second moment about z (mm4) of the knob slider's section at each element."""
    r = k.knob_bar().transform(k.ON_FRONT_FACE)        # (x, y, z) -> (-z, y, x)
    out = []
    for x in YAW_XM:
        A = Sy = Syy = 0.0
        for poly in r.slice(x).to_polygons():
            p = np.asarray(poly)
            q = np.roll(p, -1, axis=0)
            cr = p[:, 0] * q[:, 1] - q[:, 0] * p[:, 1]
            A += cr.sum() / 2
            Sy += ((p[:, 1] + q[:, 1]) * cr).sum() / 6
            Syy += ((p[:, 1] ** 2 + p[:, 1] * q[:, 1] + q[:, 1] ** 2) * cr).sum() / 12
        out.append((A, Sy / A, Syy - Sy ** 2 / A))
    return np.array(out)


YAW_SEC = yaw_sections()
YAW_PLAIN = np.abs(YAW_SEC[:, 2] - I_PLAIN) < 0.05 * I_PLAIN


# where the bar meets each end of the knob's carriage, a plan FE of the real shape gives what the sideways bending is raised
# to there (corner_fe, in the sideways section below): the bar widening into the carriage and the roof's cut-back ends
CORNER_YAW = None


def slice_edges(cs):
    e = [np.hstack([np.asarray(p), np.roll(np.asarray(p), -1, axis=0)]) for p in cs.to_polygons()]
    return np.vstack(e) if e else np.zeros((0, 4))


YAW_GEOM = {"drawn": ({z: slice_edges(HANDLE.slice(z)) for z in YAW_ZS}, {z: slice_edges(k.knob_bar().slice(z)) for z in YAW_ZS},
                      0.0, 0.0, 0.0)}     # each way the slider can be built and sit: (the plates' slices, the slider's, the
#                                           slider's bodily shift across, the carriage's extra play each side, the plates' offset)
YAW_GAPS = {}


def yaw_gaps(s, geom="drawn"):
    """How far each node of the knob slider at knob travel s can move in (-y) and out (+y) before it meets a plate,
    on any layer of its height: (nodes' x, in, out); the slider and the plates as geom has them."""
    if (geom, s) not in YAW_GAPS:
        walls_d, me_d = YAW_GEOM[geom][:2]
        xs = YAW_XS + s
        gin, gout = np.full(len(xs), 99.0), np.full(len(xs), 99.0)
        Xq = np.clip(xs, xs[0] + 0.02, xs[-1] - 0.02)
        for z in YAW_ZS:
            mine_, walls_ = along_all(me_d[z], Xq - s), along_all(walls_d[z], Xq)   # the slider is the same at any s,
            for i in range(len(xs)):                                                 # moved along by s
                for a, b in mine_[i]:
                    for c, d in walls_[i]:
                        if d <= a + 1e-6:
                            gin[i] = min(gin[i], a - d)
                        elif c >= b - 1e-6:
                            gout[i] = min(gout[i], c - b)
                        else:
                            gin[i] = gout[i] = -1.0
        YAW_GAPS[(geom, s)] = (xs, gin, gout)
    return YAW_GAPS[(geom, s)]


def yaw_stress(s, loads, side=(), masses=(), steps=16, own_axis=True, geom="drawn"):
    """The knob slider at knob travel s, lying flat in its lane, under loads [(x, y, N along x)] (the thumb, a stop, the
    caps, the cam) and side pushes [(x, N along y)], with its own inertia at its real mass and height, and masses
    [(x, y, g)] riding on it (sled B on riser B's cap in a let-go) slowing with it. The load put on in steps, each solved
    by semi-smooth Newton, as rail_stress does. The contacts don't rub, so the slider's energy is convex and has one
    answer whatever the path: only the full load must be solved to |R| < 1e-7 of the largest push (a first small step that
    starts on a wall can cycle a while). Solved once, where the slider is drawn: moving the whole slider across its play
    first only slides it bodily (every gap in and out changes by the same amount), which gives the same answer, and a thumb
    really pressing the knob in, worked out as a force, only lowers the stress (the ordinary push 20.4 MPa with no press,
    16.7 at 3 N, 8 at 10 N; the landings change by under 1 %), so pressing in is left out. Returns (the largest sideways
    bending stress, MPa, on the plain bar's faces, with its x; the stress along each element, MPa; converged; the most a
    run of the carriage's nodes pushes its rib, N; every wall's push across added up, N; and each node's push on a wall,
    [(x, N)], + outward; how far each node moves across, + outward). geom: which of YAW_GEOM it is worked out in; a node
    that starts inside a wall there makes the answer not converged. Also returns which elements are the plain bar's at the
    carriage's two square ends (the element each side), where a stress raiser like a riser's square foot in z sits."""
    xs, gin, gout = yaw_gaps(s, geom)
    n = len(xs)
    A, yc, I = YAW_SEC[:, 0], YAW_SEC[:, 1], YAW_SEC[:, 2]
    m_el = RHO * A * YAW_H
    ax = sum(F for _, _, F in loads) / (m_el.sum() + sum(m for _, _, m in masses))
    loads = list(loads) + [(x, y, -m * ax) for x, y, m in masses]
    KE = [beam_k(YAW_H, E_PLA * I[e]) for e in range(n - 1)]
    K = np.zeros((2 * n, 2 * n))
    for e in range(n - 1):
        K[2 * e:2 * e + 4, 2 * e:2 * e + 4] += KE[e]
    f_all = np.zeros(2 * n)
    for x, y, F in loads:
        f_all[2 * int(np.argmin(np.abs(xs - x))) + 1] += -(y - Y_AXIS) * F
    for x, F in side:
        f_all[2 * int(np.argmin(np.abs(xs - x)))] += F
    for e in range(n - 1):                                 # each element's inertia, at its own middle
        f_all[2 * e + 1] += (yc[e] - Y_AXIS) * m_el[e] * ax / 2
        f_all[2 * e + 3] += (yc[e] - Y_AXIS) * m_el[e] * ax / 2
    # the push along the slider runs along each part's own middle: where the knob's carriage is wider than the bar, its
    # middle is out from the bar's line, and the push through it bends it only by how far the push is from that middle.
    # The moments above are taken about the bar's line, so each element gets back the push along it times how far its
    # middle is out (zero on the plain bar)
    fx = np.zeros(n)
    for x, y, F in loads:
        fx[int(np.argmin(np.abs(xs - x)))] += F
    fx[:-1] -= m_el * ax / 2
    fx[1:] -= m_el * ax / 2
    N_el = -np.cumsum(fx)[:-1]                             # pull along each element (tension +)
    if own_axis:
        f_all[1:-2:2] -= (yc - Y_AXIS) * N_el
        f_all[3::2] += (yc - Y_AXIS) * N_el
    kc, k_reg, vi = 2e4, 1e-4, np.arange(0, 2 * n, 2)
    tol = 1e-7 * max(1.0, max(abs(F) for _, _, F in loads))

    def resid(u, f):
        v = u[0::2]
        R = K @ u - f
        R[vi] += kc * (np.maximum(0.0, v - gout) - np.maximum(0.0, -gin - v)) + k_reg * v
        return R, (v - gout >= -1e-12) | (-gin - v >= -1e-12)

    u = np.zeros(2 * n)
    for st in range(1, steps + 1):
        f = f_all * st / steps
        R, act = resid(u, f)
        for _ in range(200):
            if np.linalg.norm(R) < tol:
                break
            H = K.copy()
            H[vi, vi] += kc * act + k_reg
            du = -np.linalg.solve(H, R)
            a = 1.0
            while True:
                Rn, actn = resid(u + a * du, f)
                if np.linalg.norm(Rn) < np.linalg.norm(R) or a < 2.0 ** -16:
                    break
                a /= 2
            u, R, act = u + a * du, Rn, actn
    ok_ = np.linalg.norm(R) < tol and min(gin.min(), gout.min()) >= 0.0
    M = np.array([(lambda fe: (-fe[1], fe[3]))(KE[e] @ u[2 * e:2 * e + 4]) for e in range(n - 1)])
    x0c, x1c = k.STEM_X0 + s, k.STEM_X1 + s
    ends = ((YAW_XM + s > x0c - YAW_H) & (YAW_XM + s < x0c)) | ((YAW_XM + s > x1c) & (YAW_XM + s < x1c + YAW_H))
    sig = np.where(YAW_PLAIN, np.abs(M).max(axis=1) * (W_BAR / 2) / I, 0.0)
    i = int(np.argmax(sig))
    # what the carriage pushes on its rib with: each run of nodes in touch, out (its leg on the rib's inner face) or in
    # (the knob's foot on the rib's outer face)
    v = u[0::2]
    on = (xs >= k.STEM_X0 + s - 0.01) & (xs <= k.STEM_X1 + s + 0.01)
    rib = 0.0
    for f_ in (kc * np.maximum(0.0, v - gout) * on, kc * np.maximum(0.0, -gin - v) * on):
        run_ = 0.0
        for fj in list(f_) + [0.0]:
            run_ = run_ + fj if fj > 0 else 0.0
            rib = max(rib, run_)
    walls = float((kc * (np.maximum(0.0, v - gout) + np.maximum(0.0, -gin - v))).sum())   # every wall's push across, N
    w_n = kc * (np.maximum(0.0, v - gout) - np.maximum(0.0, -gin - v))
    return (float(sig[i]), float(YAW_XM[i] + s), sig, bool(ok_), rib, walls,
            [(float(xs[j]), float(w_n[j])) for j in np.nonzero(np.abs(w_n) > 1e-6)[0]], v, YAW_PLAIN & ends, np.abs(M).max(axis=1))


# where the thumb pushes the knob: it rests in the saddle at the knob's middle, between two ridges standing LIP proud,
# and pushes the front ridge to push the knob forward, the rear one to pull it back; its line across is the ridges' middle
K_OUT = k.KNOB_Y0 + k.KNOB_T                           # the knob's outer face: the ridges and the end lips stand on it
Y_K = K_OUT + k.LIP / 2
X_THUMB_F, X_THUMB_R = k.saddle_x()                    # the middle of the ridge the thumb pushes, each way, at s = 0
(f0_, f1_), (b0_, b1_) = k.riser_x()


print("\n== The thumb")
A_TWIST = k.BAR_Y0                         # the riser pushes the wing's inner corner, the band pulls on y = 0
W_TWIST = k.RISER_Y1 - k.SLED_HW


def twist(mu):
    """How much harder a riser has to push a sled than the band pulls it: the sled turns until
    two corners bear on the walls, SLED_LEN apart, and they rub."""
    return 1 / (1 - 2 * mu * A_TWIST / (k.SLED_LEN + mu * W_TWIST))


RUB = {}


def side_rub(E_tpu, mu, band, Fr, F_cam, F_lat, base, press=0.0, back=False):
    """What the walls that hold the knob slider sideways rub away at the trip (N). The thumb pushes the knob 7 mm out to
    the side of the bar's line, riser B's cap and cam A push back nearer it, so the push turns the slider flat in its lane
    and the walls take that turn: the rib under the knob's carriage at its two ends, the lane's wall behind the bar, the
    risers' slots. The slider slides along each wall it presses, so each rubs mu of its push. Worked out with yaw_stress at
    the latest let-go, the thumb pushing the saddle's front ridge with what it needs (base) and this rubbing on top, the
    rubbing held back on the bar's line, until it settles (to 0.005 N). The cam's own push across (F_lat), and its
    rubbing on the lane's wall right behind it, are in the latch's term already ((tan + mu) in thumb_at_trip): there only
    what the wall pushes beyond it is counted. press: the thumb also presses the knob in by this share of its push, to
    hold the ridge (it stands only LIP proud): that bears on the rib and the risers' slots, and they rub mu of it too.
    back: the return push instead, at its own trip (the slider is not its own mirror: riser F stands 13.6 behind the
    carriage, riser B in its front, and cam B is at the far end): the thumb pulls the rear ridge, riser F's cap pushes sled F
    and cam B the block. Returns (rubbing, yaw_stress's answer, settled and converged)."""
    key = (round(E_tpu, 6), mu, band, press, back)
    if key not in RUB:
        s_ = k.THROW - S_TRIP_LATE if back else S_TRIP_LATE
        x_cam = (k.CAM_B_TOP if back else k.CAM_A_TOP) + s_
        rub, done = 0.0, False
        for _ in range(60):
            if back:
                r = yaw_stress(s_, [(X_THUMB_R + s_, Y_K, -(base + rub)), (f0_ + s_, y_hit, Fr), (x_cam, k.Y_CAM, F_cam),
                                    (f0_ + s_, Y_AXIS, rub)], [(x_cam, F_lat)] + ([(X_THUMB_R + s_, -press * (base + rub))]
                                                                                 if press else []))
            else:
                r = yaw_stress(s_, [(X_THUMB_F + s_, Y_K, base + rub), (b1_ + s_, y_hit, -Fr), (x_cam, k.Y_CAM, -F_cam),
                                    (b1_ + s_, Y_AXIS, -rub)], [(x_cam, F_lat)] + ([(X_THUMB_F + s_, -press * (base + rub))]
                                                                                  if press else []))
            near = sum(abs(w) for x, w in r[6] if abs(x - x_cam) <= 3.0)
            new = mu * (sum(abs(w) for x, w in r[6] if abs(x - x_cam) > 3.0) + max(0.0, near - F_lat))
            done = abs(new - rub) < 0.005
            rub = new
            if done:
                break
        RUB[key] = (rub, r, done and r[3])
    return RUB[key]


def thumb_at_trip(E_tpu, mu, band=k.BAND, rub=True, press=0.0):
    """(band pull, riser push, cam push, total) at the trip. The cam's 22 degree face also
    pushes the block forward into the rail's end, which adds to the rubbing it has to beat. The total counts what the
    walls holding the knob slider sideways rub away (side_rub); rub False leaves that out, which is what drives the knob
    on (those walls rub the rest away again). press: the thumb pressing the knob in as well (side_rub). The rubbing is the
    worse of the push and the return push, each at its own trip."""
    kb = E_tpu * band[0] * band[1] / k.BAND_RELAXED
    Fb = kb * (k.BAND_PRELOAD + S_TRIP_LATE - k.G_P - k.C_TRIP)
    tn = math.tan(math.radians(k.CAM_ANGLE) + math.atan(mu))
    F_lat = (2 * mu * Fb + k_arm * k.arm_deflect_for(k.Y_CAM)) / (1 - mu * tn)
    F_cam = F_lat * (tn + mu)
    tot = Fb * twist(mu) + F_cam + 0.3
    if rub:
        tot += max(side_rub(E_tpu, mu, band, Fb * twist(mu), F_cam, F_lat, tot, press, back)[0] for back in (False, True))
    return Fb, Fb * twist(mu), F_cam, tot


PRESS = 0.3                                # the thumb presses the knob in by this share of its push, to hold a ridge that stands
#                                            only LIP proud: its rubbing on the rib and the risers' slots is counted in the push
rows = []
for E_tpu, band, name in ((20.0, k.BAND, "band"), (26.0, k.BAND_SOFT, "soft band"), (30.0, k.BAND_SOFT, "soft band"),
                          (12.0, k.BAND_STRONG, "strong band")):
    for mu in MU:
        rows.append((name, E_tpu, mu) + thumb_at_trip(E_tpu, mu, band, press=PRESS))
for name, E_tpu, mu, Fb, Fr, Fcam, tot in rows:
    if mu in (0.3, 0.4):
        print(f"     thumb at the trip, {name}, TPU {E_tpu:.0f} MPa, PLA friction {mu}: band {Fb:.1f} N, riser {Fr:.1f} N (sled twisting "
              f"x{twist(mu):.2f}) + latch {Fcam:.1f} N + bar 0.3 N + the walls holding the slider sideways, the thumb pressing in "
              f"{PRESS:g} of its push, {tot - (Fr + Fcam + 0.3):.1f} N = {tot:.1f} N")
hi_ = max(r[-1] for r in rows)
w_row = max(rows, key=lambda r: r[-1])
W_RUB = w_row[-1] - (w_row[4] + w_row[5] + 0.3)
RUBS = [r[-1] - (r[4] + r[5] + 0.3) for r in rows]
NOMINAL_THUMB = thumb_at_trip(20.0, 0.3, press=PRESS)[-1]
THUMB_MAX = 33.0                           # N: the most the thumb may need at the trip, with any band in a TPU it is fitted to
TH_26 = max(thumb_at_trip(26.0, mu, k.BAND, press=PRESS)[-1] for mu in MU)    # the normal band in a TPU it is never fitted to
rub_ok = all(v[2] for v in RUB.values())
report(NOMINAL_THUMB < 20 and hi_ < THUMB_MAX and rub_ok,
       f"thumb at the trip, counting the walls that hold the slider sideways and the thumb pressing the knob in {PRESS:g} of its "
       f"push: {NOMINAL_THUMB:.1f} N nominal, {min(r[-1] for r in rows):.1f}-{hi_:.1f} N over friction 0.2-0.4 and the three bands in "
       f"TPUs they are fitted to (limit {THUMB_MAX:g}; the sled twists x{twist(0.2):.2f}-{twist(0.4):.2f}; the walls rub "
       f"{min(RUBS):.1f}-{max(RUBS):.1f} N); the hang test below proves each band at the stiffest TPU it is fitted to"
       + ("" if rub_ok else "; a sideways solve DID NOT SETTLE"),
       f"at worst {w_row[0]} in {w_row[1]:g} MPa TPU, friction {w_row[2]}: {w_row[-1] - W_RUB:.1f} N without the walls' "
       f"rubbing; the band fitted {k.BAND_PRELOAD:g} mm over its printed length. The normal band in 26 MPa TPU, which the hang "
       f"test never fits (it fits band soft there), would need {TH_26:.1f} N")

print("\n== Which band: the hang test")
# TPU's stiffness varies a lot from brand to brand, so the band is picked by a test, not a guess: hook a normal band's two
# eyes over two thin round things (3 mm or a little under, like the sleds' posts), hang a full half-litre bottle of water
# from the lower one (about 0.5 kg with its bottle: HANG_N) and measure how far the band stretches, to the nearest mm.
# That is the throw model's own band: its pull is E x its section x its stretch / its printed length eye to eye, as
# throw() and thumb_at_trip() have it, loaded and held still, so without the loss TPU shows as it unloads. The read me
# fits band strong at HANG_STRONG or more, band soft at HANG_SOFT or less, the band in between, and says to ask outside
# HANG_MIN to HANG_MAX. A reading can be 1 mm out (two marks on a ruler), so each band is proven over every stretch it
# can be fitted at, 1 mm past its readings each way: it gets the blade to its lock in every case of the throw grids, at
# the softest TPU that stretch means; the thumb needs under THUMB_MAX at the stiffest; and the band is never stiffer than
# the stiffest band-and-TPU the throws and the knocks were worked out for (the band in 26 MPa TPU)
MISREAD = 1.0
HANG_CASES = list(itertools.product((0.1, 0.2, 0.3), MU, (0.6, 1.0), (False, True)))    # as the throw grids have them
kb_of = lambda E, band: E * band[0] * band[1] / k.BAND_RELAXED                          # N/mm, as throw() has it
stretch_of = lambda E: k.HANG_N / kb_of(E, k.BAND)                                       # mm, the normal band
tpu_of = lambda st: k.HANG_N / (st * k.BAND[0] * k.BAND[1] / k.BAND_RELAXED)             # MPa, from the stretch
GRIDS = {"band strong": (k.BAND_STRONG, [g[0] for g in grid_s]), "the band": (k.BAND, [g[0] for g in grid]),
         "band soft": (k.BAND_SOFT, [g[0] for g in grid_soft])}
KB_TESTED = max(kb_of(E, band) for band, Es in GRIDS.values() for E in Es)


def band_for(reading):
    """The band the read me says to fit for a stretch read to the nearest mm, or None: ask first."""
    r = math.floor(reading + 0.5)
    if r < k.HANG_MIN or r > k.HANG_MAX:
        return None
    return "band strong" if r >= k.HANG_STRONG else "band soft" if r <= k.HANG_SOFT else "the band"


print(f"     the normal band, {k.BAND[0]:.2f} x {k.BAND[1]:.2f}, {k.BAND_RELAXED:.1f} eye to eye, under {k.HANG_N:g} N:")
for E in (10.0, 12.5, 15.0, 17.5, 20.0, 22.5, 26.0, 28.0, 30.0):
    st = stretch_of(E)
    tested = [name for name, (_, Es) in GRIDS.items() if min(Es) <= E <= max(Es)]
    print(f"       TPU {E:4.1f} MPa: stretches {st:4.1f} mm, read as {math.floor(st + 0.5):2d}: fit {band_for(st) or 'nothing yet: ask'}"
          f"  (the throw grids work {' and '.join(tested)} in it)")
fits, bad, HANG_STIFF, AGED_ROWS, KB_FITTED = [], [], [], [], []
for name, (band, Es) in GRIDS.items():
    reads = [r for r in range(int(k.HANG_MIN), int(k.HANG_MAX) + 1) if band_for(r) == name]
    st_lo, st_hi = min(reads) - MISREAD, max(reads) + MISREAD          # the stretches it can be fitted at
    E_soft, E_stiff = tpu_of(st_hi), tpu_of(st_lo)
    HANG_STIFF.append((E_stiff, band))                                 # the sideways check pushes these too
    KB_FITTED += [kb_of(E_soft, band), kb_of(E_stiff, band)]
    misses = [g for g in HANG_CASES for E in (E_soft, E_stiff) if not throw(E, *g, band=band)["reached"]]
    # and aged: months fitted, the band's rest pull down to AGED[0] and its stiffness to AGED[1], at the softest TPU it is fitted to
    aged = [g for g in HANG_CASES if not throw(E_soft, *g, band=band, aged=True)["reached"]]
    AGED_ROWS.append((name, len(aged), E_soft))
    th_max = max(thumb_at_trip(E_stiff, mu, band, press=PRESS)[-1] for mu in MU)
    fits.append(f"{name} read {min(reads)}-{max(reads)} mm, so stretched {st_lo:g}-{st_hi:g}: TPU {E_soft:.1f}-{E_stiff:.1f} MPa, "
                f"locks in all {2 * len(HANG_CASES)} throws ({len(HANG_CASES) - len(aged)} of {len(HANG_CASES)} aged), thumb up to "
                f"{th_max:.1f} N, {kb_of(E_stiff, band):.3f} N/mm at most")
    if misses or aged or th_max >= THUMB_MAX or kb_of(E_stiff, band) > KB_TESTED + 1e-9:
        bad.append(f"{name}: {len(misses)} misses, {len(aged)} aged misses, thumb {th_max:.1f}, {kb_of(E_stiff, band):.3f} N/mm")
    if name == "the band" and not (min(Es) - 0.05 <= E_soft and E_stiff <= max(Es) + 0.05):
        bad.append(f"the band is fitted at {E_soft:.1f}-{E_stiff:.1f} MPa, outside its throw grid's {min(Es):g}-{max(Es):g}")
report(not bad, f"hang test: a reading of {k.HANG_STRONG:g} mm or more fits band strong, {k.HANG_SOFT:g} or less band soft, "
                f"{k.HANG_SOFT + 1:g}-{k.HANG_STRONG - 1:g} the band; each works over every stretch it is fitted at, the reading 1 mm out "
                f"either way: " + "; ".join(fits),
       "; ".join(bad) if bad else f"the normal band's fitted TPU sits inside its throw grid's {min(GRIDS['the band'][1]):g}-"
       f"{max(GRIDS['the band'][1]):g} MPa (15 MPa stretches it {stretch_of(15.0):.1f} mm, 26 MPa {stretch_of(26.0):.1f}); none is stiffer "
       f"than the band in 26 MPa TPU ({KB_TESTED:.3f} N/mm), the stiffest the throws and knocks were worked out for; under "
       f"{k.HANG_MIN:g} or over {k.HANG_MAX:g} mm the read me says to ask")
# the band you are about to fit, hung the same way after it is stretched 10 times (TPU softens the first few times it goes
# further than before): it must stretch between what the stiffest band the knocks were worked out for (KB_TESTED) and the
# softest one the hang test proves stretch. The read me's numbers are typed in make_knife (HANG_FIT_LO, HANG_FIT_HI)
fit_lo, fit_hi = k.HANG_N / KB_TESTED, k.HANG_N / min(KB_FITTED)
report(k.HANG_FIT_LO >= fit_lo - 0.5 and k.HANG_FIT_HI <= fit_hi + 0.5 and k.HANG_CONDITION >= 1.45 * k.BAND_RELAXED,
       f"the band you fit, whichever kind, hung from the bottle must stretch {k.HANG_FIT_LO:g} to {k.HANG_FIT_HI:g} mm (the read me): "
       f"{fit_lo:.1f} is the stiffest band the throws and knocks were worked out for ({KB_TESTED:.3f} N/mm), {fit_hi:.1f} the softest "
       f"band the hang test proves ({min(KB_FITTED):.3f} N/mm); stretched 10 times to {k.HANG_CONDITION:g} mm eye to eye first "
       f"({k.HANG_CONDITION / k.BAND_RELAXED:.2f} times its length, past the {1 + strain_b:.2f} it reaches fully cocked)")
_aged_fresh = crit_extra(15, 0.3)
_aged_margin = crit_extra(15, 0.3, aged=True)
report(all(n == 0 for _, n, _ in AGED_ROWS),
       f"an aged band (fitted for months, held stretched {k.BAND_PRELOAD / k.BAND_RELAXED * 100:.0f} %: its rest pull down to "
       f"{AGED[0]:g} and its stiffness to {AGED[1]:g}) still locks in every hang-test throw at the softest TPU each band is fitted "
       f"to (" + ", ".join(f"{name} at {E:.1f} MPa" for name, _, E in AGED_ROWS) + f"); at the worst corner it has "
       f"{_aged_margin:.3f} N of extra friction to spare, against {_aged_fresh:.2f} fresh: when the throw gets weak, fit a spare",
       "; ".join(f"{name}: {n} misses" for name, n, _ in AGED_ROWS))
# why the spring is a stretched TPU band and not a printed PLA clock spring: a bent strip stores sigma^2 / 6E per mm3 (its
# stress grows from nothing at its middle), and PLA bent on every throw must stay under the fatigue strain, at 3.0 GPa; a
# stretched band stores E strain^2 / 2 all through, and this one stretches strain_b fully cocked
u_pla = (EPS_FATIGUE * 3000.0) ** 2 / (6 * 3000.0)
u_tpu = [E * strain_b ** 2 / 2 for E in (10.0, 30.0)]
print(f"     a printed PLA clock spring held to {EPS_FATIGUE * 100:.2f} % stores {u_pla:.3f} mJ per mm3; this band, stretched "
      f"{strain_b * 100:.0f} % fully cocked, {u_tpu[0]:.2f}-{u_tpu[1]:.2f} in 10-30 MPa TPU: {u_tpu[0] / u_pla:.0f} to {u_tpu[1] / u_pla:.0f} "
      f"times as much")


def thumb_off(when, E_tpu, h, mu, fill, band=k.BAND, m_thumb=10.0, dt=2e-4):
    """The thumb leaves the knob: when 'never', 'trip' (at the moment of the trip) or 'land'
    (as the knob lands on its pad). Units mm, g, ms, N. While on, it pushes with the trip force,
    against the band pulling sled B back and the riser pushing it twisting against its walls
    (T x twist), and the knob jumps on to its stop (the knob-landing checks work out that landing)
    and stays; once off, the band pulls the bar back, less what the twisting sled rubs away
    (T / twist). The blade is only pushed by sled F, so when riser F meets sled F the blade goes
    on alone and coasts. Returns (locks, ms from the trip to the thumb leaving, m/s at which
    riser F meets sled F, the knob's landing: its speed, the band's pull and the thumb's push)."""
    kb = E_tpu * band[0] * band[1] / k.BAND_RELAXED
    m_b, m_s, m_br = m_blade_solid * fill, m_sled * fill, m_bar * fill
    F_th = thumb_at_trip(E_tpu, mu, band, rub=False)[-1]   # what drives the knob on: the thumb pushes the walls' rubbing too
    F_rub = thumb_at_trip(E_tpu, mu, band)[-1] - F_th
    s_end = S_STOP_F
    c, v, s, vs, t = k.C_TRIP, 0.0, S_TRIP, 0.0, 0.0
    on, landed, t_left = when != "trip", False, (0.0 if when == "trip" else None)
    land_at = None
    while True:
        T = (1 - h) * kb * ((k.R_B + s + 2 * k.POST_BACK) - c - k.BAND_RELAXED)
        a = (T * (1 - 0.046) - friction(c, mu, fill)) / (m_b + m_s)
        if landed and on:
            vs = 0.0
        else:
            F_bar = (F_th - T * twist(mu) if on else -T / twist(mu)) - 0.2 * (1 if vs > 0 else -1)
            vs += F_bar / (m_br + m_s + (m_thumb if on else 0.0)) * dt
            s += vs * dt
            if s >= s_end and on:
                land_at = {"v": vs, "T": T, "F_th": F_th, "rub": F_rub, "c": c, "t": t}
                s, vs, landed = s_end, 0.0, True
                if when == "land":
                    on, t_left = False, t
        v += a * dt
        c += v * dt
        t += dt
        if v <= 0:
            return False, t_left, 0.0, land_at
        if c >= s - k.G_P:
            break
    v_close = v - vs
    E_b = 0.5 * m_b * v * v
    while c < (k.RAIL_X1 - k.X_BLK) + 0.3:
        E_b -= friction(c, mu, fill) * 0.05
        if E_b <= 0:
            return False, t_left, v_close, land_at
        c += 0.05
    return True, t_left, v_close, land_at


cases = list(itertools.product((15.0, 20.0, 26.0), (0.1, 0.3), MU, (0.6, 1.0)))
solid_cases = [i for i, g in enumerate(cases) if g[3] == 1.0]
never = [thumb_off("never", *g) for g in cases]
stay = sum(r[0] for r in never)
at_trip = sum(thumb_off("trip", *g)[0] for g in cases)
land = [thumb_off("land", *g) for g in cases]
t_land = [r[1] for r in land if r[1] is not None] or [0.0]
report(stay == len(cases), f"thumb kept on the knob until the blade has gone: locks in {stay} of {len(cases)} cases")
print(f"     thumb flicked off the knob as it lands ({min(t_land):.1f}-{max(t_land):.1f} ms after the trip): locks in "
      f"{sum(r[0] for r in land)} of {len(cases)}; thumb off at the very moment of the trip: {at_trip} of {len(cases)}. "
      f"A blade that stops part way out is pushed back by hand")

print("\n== Knocks")
# every throw: sled F runs into riser F at the blade's speed when the band lets go
k_wing_b = 3 * E_PLA * (k.SLED_H * k.WING_L ** 3 / 12) / (y_hit - k.SLED_HW) ** 3
k_wing_s = (5 / 6) * G_PLA * k.SLED_H * k.WING_L / (y_hit - k.SLED_HW)
k_wing = 1 / (1 / k_wing_b + 1 / k_wing_s + 1 / 20000)
WING_MPA = 1.3 * (y_hit - k.SLED_HW) / (k.SLED_H * k.WING_L ** 2 / 6)   # MPa per N at the wing's root
w_r = k.RISER_Y1 - k.BAR_Y0
ZC = (k.BAR_Z0 + k.BAR_Z1) / 2                    # the bar's axis
E_R = (k.SLED_Z0 + k.SLED_Z1) / 2 - ZC            # a wing pushes a riser this far over the bar's axis ...
E_K = (k.KNOB_TOP + k.BAR_Z0) / 2 - ZC            # ... and the thumb the knob
M_THUMB = 10.0                                    # g: the thumb moving with the knob (as thumb_off has it)
H_CAP = min(k.RISER_TOP, k.SLED_Z1) - k.SLED_Z0   # the height a wing meets a cap over
A_TONGUE, A_SIDES = k.TONGUE_W * H_CAP, (w_r - k.TONGUE_W) * H_CAP   # the cap's block in front of the tongue, its legs
SPLIT = (A_TONGUE / k.CAP_T) / (A_TONGUE / k.CAP_T + A_SIDES / k.CAP_L)   # share of a cap's push on the tongue's face
A_PAD = 2 * k.PAD_HW * k.SLED_H


def polys_moments(cs):
    """Area (mm2) and the middle (x, y) of a cross-section."""
    A, sx, sy = 0.0, 0.0, 0.0
    for poly in cs.to_polygons():
        p_ = np.asarray(poly)
        q_ = np.roll(p_, -1, axis=0)
        cr = p_[:, 0] * q_[:, 1] - q_[:, 0] * p_[:, 1]
        A += cr.sum() / 2
        sx += ((p_[:, 0] + q_[:, 0]) * cr).sum() / 6
        sy += ((p_[:, 1] + q_[:, 1]) * cr).sum() / 6
    return A, sx / A, sy / A


def stop_contact(x_face, stop, x_stop):
    """What of the knob slider meets a knob stop's face: the slider's real section just inside its end
    face at x_face, cut to the stop's real section just inside its face at x_stop (its recess and all); its area (mm2)
    and its middle (y, z)."""
    sec = k.knob_bar().transform(k.ON_FRONT_FACE).slice(x_face)        # (x, y, z) -> (-z, y, x)
    face = stop.transform(k.ON_FRONT_FACE).slice(x_stop)
    A, mz, my = polys_moments(sec ^ face)
    return A, my, -mz


_SR, _SF = k.stop_face_x()
CONTACT = [stop_contact(k.STEM_X0 + k.END_CUT + 0.05, STOP_R, _SR - 0.05), stop_contact(k.STEM_X1 - k.END_CUT - 0.05, STOP_F,
                                                                                        _SF + 0.05)]   # past the knob's low end cut
A_STOP = min(a for a, _, _ in CONTACT)                 # the knob's end face (lips and stem's end with it) on a stop
Y_S, E_S = CONTACT[0][1], CONTACT[0][2] - ZC           # the middle of that face: a stop pushes the knob this far over
#                                                        the bar's axis (E_K for the thumb), at this y
LIP_CS = m3.CrossSection.square([40, 10]).translate([-30, K_OUT])
_a, _, _my = polys_moments(k.knob_bar().transform(k.ON_FRONT_FACE).slice(k.STEM_X0 + 0.05) ^ LIP_CS ^
                           STOP_R.transform(k.ON_FRONT_FACE).slice(_SR - 0.05))
LIP_SHARE, LIP_ARM = _a / A_STOP, _my - K_OUT           # a stop's even push on a lip's own end: its share, and how far
#                                                        out from the lip's root it pushes
_V, _cen, _ = mass_props(k.knob_bar() ^ k.box(k.STEM_X0 - 1, k.STEM_X1 + 1, k.KNOB_Y0, 40, -1, 20))
M_KNOB, Y_KNOB, E_KNOB = _V * RHO, _cen[1], _cen[2] - ZC   # the knob outside its stem, and where its weight is
def roof_crossing():
    """How long the carriage's roof is where it crosses the rib's channel, at its shortest: read off the slider at the
    middle of each of the roof's printed layers (they are cut back layer by layer), along every line across the channel
    (the knob's end cuts take 0.5 off each end of its outer part)."""
    xm = (k.STEM_X0 + k.STEM_X1) / 2
    out = []
    for _, z0_, z1_ in k.roof_layers():
        cs = k.knob_bar().slice((z0_ + z1_) / 2)
        for y in np.arange(k.LEG_Y1 + 0.05, k.KNOB_FOOT_Y0 - 0.04, 0.1):
            strip = m3.CrossSection.square([400, 0.02]).translate([-100, y - 0.01])
            for p_ in (cs ^ strip).decompose():
                b_ = p_.bounds()
                if b_[0] <= xm <= b_[2]:
                    out.append(b_[2] - b_[0])
    return min(out)


STEM_B, STEM_T = roof_crossing(), k.STEM_TOP - k.ROOF_Z0   # what joins the bar and the knob: the carriage's roof over its
#                                                        rib, its thinnest part, 37 x 1.2 where it crosses the channel
E_STEM = (k.ROOF_Z0 + k.STEM_TOP) / 2 - ZC             # its middle over the bar's axis
LANE_CS = P1.slice(k.LANE_Z0 - 0.05)              # the base plate just under the lane's floor
OVER = (k.Z1 - k.BAR_Z1) + (k.BAR_Z0 - k.LANE_Z0)  # how far the bar, lying on its floor, can lift to the middle plate


def tpu(E, A, L, d, stiffen=False):
    """Force (N) to squash a TPU block (face A mm2, length L) by d: linear, or stiffening as rubber
    does, F = E/3 A (1/lam^2 - lam) with lam = 1 - d/L (the same stiffness while the squash is small)."""
    d = np.maximum(d, 0.0)
    if not stiffen:
        return E * A / L * d
    lam = np.maximum(1 - d / L, 0.05)
    return E / 3 * A * (1 / lam ** 2 - lam)


def cap_force(E, d, stiffen=False):
    """A riser's TPU cap squashed d: the block in front of the tongue and the legs beside it."""
    return tpu(E, A_TONGUE, k.CAP_T, d, stiffen) + tpu(E, A_SIDES, k.CAP_L, d, stiffen)


def k_cap(E_tpu):
    """A riser's TPU cap (N/mm) while its squash is small."""
    return E_tpu * (A_TONGUE / k.CAP_T + A_SIDES / k.CAP_L)


M_OTHER = m_bar + m_sled                    # the bar and the other sled, no thumb
M_RED = m_turn * M_OTHER / (m_turn + M_OTHER)


def hit(v, E_tpu):
    """A sled's wing meeting a riser's cap at v m/s: (force N, cap squash mm)."""
    k_s = 1 / (1 / k_cap(E_tpu) + 1 / k_wing)
    F = v * math.sqrt(k_s * M_RED)
    return F, F / k_cap(E_tpu)


def letgo_speed(E_tpu, h, mu, band=k.BAND):
    """The knob let go just before the trip: how fast riser F meets sled F (m/s), the band's
    pull less its TPU loss and the twisting sled's rubbing driving the bar and sled B back."""
    kb = E_tpu * band[0] * band[1] / k.BAND_RELAXED
    E_bar, s = 0.0, S_TRIP_LATE
    while s > k.C_TRIP + k.G_P:
        T = (1 - h) * kb * (s - k.C_TRIP - k.G_P + k.BAND_PRELOAD)
        E_bar += (T / twist(mu) - 0.2) * 0.01
        s -= 0.01
    return math.sqrt(2 * max(E_bar, 0.0) / M_OTHER)


def stop_fe(recess, h=0.1, nu=0.45, stuck=True):
    """A knob stop in plan as a plane-stress model of square elements h on a side (selective reduced integration, TPU's nu):
    STOP_L long, its back on its guard, the knob's flat end pushing the outer part of its face that the knob meets (from
    END_Y + 0.05 out), its inner part cut back `recess`; both faces stuck (the stiffest) or sliding. Returns its stiffness over
    E A / L, A what the knob meets."""
    L, y0 = k.STOP_L, k.STOP_Y0
    W, WC = k.STOP_Y1 - y0, k.STOP_Y1 - (k.END_Y + 0.05)
    nx, ny = int(round(L / h)), int(round(W / h))
    hx, hy = L / nx, W / ny
    nid = lambda i, j: j * (nx + 1) + i
    lam, mu_ = nu / (1 - nu ** 2), 1 / (2 * (1 + nu))
    Dd, Dv = mu_ * np.diag([2.0, 2.0, 1.0]), lam * np.array([[1.0, 1, 0], [1, 1, 0], [0, 0, 0]])

    def Bm(xi, eta):
        dN = 0.25 * np.array([[-(1 - eta), (1 - eta), (1 + eta), -(1 + eta)], [-(1 - xi), -(1 + xi), (1 + xi), (1 - xi)]])
        dN[0] *= 2 / hx
        dN[1] *= 2 / hy
        B = np.zeros((3, 8))
        B[0, 0::2], B[1, 1::2], B[2, 0::2], B[2, 1::2] = dN[0], dN[1], dN[1], dN[0]
        return B
    g = 1 / math.sqrt(3)
    Ke = sum(Bm(a, b).T @ Dd @ Bm(a, b) * hx * hy / 4 for a in (-g, g) for b in (-g, g)) + Bm(0, 0).T @ Dv @ Bm(0, 0) * hx * hy
    n_ = (nx + 1) * (ny + 1)
    K, used = np.zeros((2 * n_, 2 * n_)), np.zeros(n_, bool)
    for j in range(ny):
        for i in range(nx):
            if (i + 0.5) * hx > L - recess and (j + 0.5) * hy < W - WC:
                continue
            ns_ = [nid(i, j), nid(i + 1, j), nid(i + 1, j + 1), nid(i, j + 1)]
            used[ns_] = True
            d_ = np.array([[2 * q, 2 * q + 1] for q in ns_]).ravel()
            K[np.ix_(d_, d_)] += Ke
    fix = {}
    for q in np.nonzero(~used)[0]:
        fix[2 * q], fix[2 * q + 1] = 0.0, 0.0
    for j in range(ny + 1):
        fix[2 * nid(0, j)] = 0.0
        if stuck:
            fix[2 * nid(0, j) + 1] = 0.0
        if j * hy >= W - WC - 1e-9:
            fix[2 * nid(nx, j)] = -1.0
            if stuck:
                fix[2 * nid(nx, j) + 1] = 0.0
    if not stuck:
        fix[2 * nid(0, ny) + 1] = 0.0
    fd = np.array(sorted(fix))
    fv = np.array([fix[d] for d in fd])
    fr = np.setdiff1d(np.arange(2 * n_), fd)
    u = np.zeros(2 * n_)
    u[fd] = fv
    u[fr] = np.linalg.solve(K[np.ix_(fr, fr)], -K[np.ix_(fr, fd)] @ fv)
    R = K @ u
    return -sum(R[2 * nid(nx, j)] for j in range(ny + 1) if j * hy >= W - WC - 1e-9) / (WC / L)


STOP_FE = {(rec_, st_): stop_fe(rec_, stuck=st_) for rec_ in (0.0, k.STOP_RECESS) for st_ in (False, True)}
STOP_FACTORS = (1.0, math.ceil((STOP_FE[(k.STOP_RECESS, True)] + 0.1) * 20) / 20)
#                             a knob stop's stiffness over E A / L, A only what the knob meets: a TPU block pushed on part of
#                             its face is stiffer than that, as its unpushed part is dragged along. Every landing is worked
#                             out at both ends of the range: 1, and the plane-stress model of the stop's real plan (its recess
#                             and all) with its faces stuck, 0.1 more for the unpushed strip at its foot and the model
report(STOP_FE[(k.STOP_RECESS, True)] < STOP_FE[(0.0, True)] and STOP_FACTORS[1] >= STOP_FE[(k.STOP_RECESS, True)] + 0.1 - 1e-9,
       f"the knob stops' stiffness: a plane-stress model of a stop pushed on the outer {k.STOP_Y1 - k.END_Y - 0.05:.2f} of its "
       f"{k.STOP_Y1 - k.STOP_Y0:.1f} wide face gives {STOP_FE[(0.0, False)]:.2f}-{STOP_FE[(0.0, True)]:.2f} times E A / L with the face flat, "
       f"{STOP_FE[(k.STOP_RECESS, False)]:.2f}-{STOP_FE[(k.STOP_RECESS, True)]:.2f} with its inner part recessed {k.STOP_RECESS} (faces "
       f"sliding to stuck); every landing is worked out with the stop {STOP_FACTORS[0]:g} and {STOP_FACTORS[1]:g} times as stiff",
       "square elements 0.1 on a side, TPU's Poisson's ratio 0.45, the stop's back on its guard")
# the 2.0 knob's lips stand 0.5 nearer the handle, so a stop meets less of the knob's end face: it is shorter in step, so it is as
# stiff as the 3.5 stop on the 2.5 knob was (it met 14.04 mm2): E A / L kept (a softer stop lets the cap and pad take more)
STOP_AL_WAS = 14.04 / 3.5
report(abs(A_STOP / k.STOP_L / STOP_AL_WAS - 1) <= 0.02,
       f"each knob stop is as stiff as on the 2.5 knob: it meets {A_STOP:.2f} mm2 of the knob's end face and stands {k.STOP_L:g} "
       f"long, {A_STOP / k.STOP_L:.2f} mm of E A / L over E against {STOP_AL_WAS:.2f} then (the 3.5 stop on 14.04 mm2): "
       f"{100 * (A_STOP / k.STOP_L / STOP_AL_WAS - 1):+.1f} %", "held within 2 %; a softer stop turns the knob more")


def picks(pk, sf):
    """The cases a landing's peaks are worked out at: where the cap and where the stop push hardest, with the stop at each
    end of its stiffness range."""
    out = set()
    for f_ in STOP_FACTORS:
        idx = np.nonzero(np.asarray(sf) == f_)[0]
        out |= {int(idx[np.argmax(pk["Fc"][idx])]), int(idx[np.argmax(pk["Fs"][idx])])}
    return sorted(out)


def landing(E, m1, m2, v1, v2, F1, T2, mu, d0, gap_pad, gap_stop, stiffen=True, zeta=0.10, t_end=3.0, dt=1e-3,
            m_th=0.0, k_th=None, thumb=True, rub=0.0, sf=1.0):
    """Two masses landing on TPU, one case per array entry. m1 (g) is the knob slider with whatever
    rides on it, at v1 m/s, pushed on by F1 N (the thumb, or the band through sled B) less the bar's
    0.2 N of rubbing; m2 is the sled its riser's cap meets, at v2, pulled back by the band with T2 N,
    its corners rubbing on the walls as the cap pushes it off its line (twist). The cap starts
    squashed d0, the sled meets its pad gap_pad on and the knob meets its own TPU stop gap_stop on
    (each counted in its own travel). Each TPU part has a damping ratio zeta. A thumb: its m_th g
    held rigid on the knob (k_th None, then m1 holds it too), or pushing through its pad of k_th
    N/mm; thumb False: F1 is the band's pull through sled B, and nothing pushes the knob but its
    stop. sf: the knob stop's stiffness factor (STOP_FACTORS). Units mm, ms, g, N. Returns the peaks (Fst: the most the stem carries between the knob and
    the bar, the stop's push less the thumb's, and the knob's own weight; Mp and My: the most it
    turns the stem over (about y) and round (about z), N mm; Mlip: the most a thumb bends a lip at
    its root, less what the stop's even push on the lip's own end takes off it), and the forces (the
    thumb's on the knob too) at the moments the cap and the stop push hardest."""
    E, m1, m2, v1, v2, F1, T2, mu, d0, sf = np.broadcast_arrays(*(np.asarray(a, float) for a in (E, m1, m2, v1, v2, F1, T2, mu,
                                                                                                 d0, sf)))
    v1, v2 = v1.copy(), v2.copy()
    v0 = v1.copy()
    rub = 1 - 1 / twist(mu)
    m_stop = m1 + (m_th if k_th is not None else 0.0)
    cc = 2 * zeta * np.sqrt(k_cap(E) * m1 * m2 / (m1 + m2))
    cp = 2 * zeta * np.sqrt(k_pad(E) * m2)
    cs = 2 * zeta * np.sqrt(E * A_STOP * sf / k.STOP_L * m_stop)
    x0, x1, x2 = np.zeros_like(E), np.zeros_like(E), np.zeros_like(E)
    z = np.zeros_like(E)
    pk = {key: z.copy() for key in ("Fc", "Fs", "Fp", "Fk", "Fst", "Mp", "My", "Mlip", "Mridge", "dc", "ds", "dp", "x1")}
    at_c = {key: z.copy() for key in ("Fc", "Fs", "Fk", "x1")}
    at_s = {key: z.copy() for key in ("Fc", "Fs", "Fk", "x1")}
    t = 0.0
    while t < t_end:
        dc, dp, ds = d0 + x1 - x2, x2 - gap_pad, x1 - gap_stop
        Fc = np.where(dc > 0, np.maximum(cap_force(E, dc, stiffen) + cc * (v1 - v2), 0.0), 0.0)
        Fp = np.where(dp > 0, np.maximum(tpu(E, A_PAD, k.PAD_L, dp, stiffen) + cp * v2, 0.0), 0.0)
        Fs = np.where(ds > 0, np.maximum(tpu(E, A_STOP * sf, k.STOP_L, ds, stiffen) + cs * v1, 0.0), 0.0)
        if k_th is None:
            a1 = (F1 - 0.2 - Fc - Fs) / m1
            Fk = F1 + rub - m_th * a1                # the thumb held rigid pushes the knob this hard (and the walls
#                                                          holding it sideways rub away rub of it)
        else:
            Fk = np.maximum(F1 + rub + k_th * (x0 - x1), 0.0)
            a1 = (Fk - rub - 0.2 - Fc - Fs) / m1
            v0 = v0 + (F1 + rub - Fk) / m_th * dt
            x0 = x0 + v0 * dt
        new_c, new_s = Fc > pk["Fc"], Fs > pk["Fs"]
        for d_, sel in ((at_c, new_c), (at_s, new_s)):
            for key, val in (("Fc", Fc), ("Fs", Fs), ("Fk", Fk), ("x1", x1)):
                d_[key] = np.where(sel, val, d_[key])
        Fkn = Fk if thumb else 0.0                   # what pushes the knob itself
        Mlip = Fs * LIP_SHARE * LIP_ARM            # an end lip, under the stop's even push on its end
        Mridge = Fkn * k.LIP / 2                   # the saddle's ridge the thumb pushes
        Fst = np.abs(Fs - Fkn) + M_KNOB * np.abs(a1)
        Mp = np.abs(Fs * (E_S - E_STEM) - Fkn * (E_K - E_STEM)) + M_KNOB * np.abs(a1) * abs(E_KNOB - E_STEM)
        My = np.abs(Fs * (Y_S - k.BAR_Y1) - Fkn * (Y_K - k.BAR_Y1)) + M_KNOB * np.abs(a1) * (Y_KNOB - k.BAR_Y1)
        for key, val in (("Fc", Fc), ("Fs", Fs), ("Fp", Fp), ("Fk", Fk), ("Fst", Fst), ("Mp", Mp), ("My", My), ("Mlip", Mlip),
                         ("Mridge", Mridge),
                         ("dc", dc), ("ds", ds), ("dp", dp), ("x1", x1)):
            pk[key] = np.maximum(pk[key], val)
        v1 = v1 + a1 * dt
        v2 = v2 + (Fc * (1 - rub * np.tanh(v2 / 0.05)) - T2 - Fp) / m2 * dt
        x1, x2 = x1 + v1 * dt, x2 + v2 * dt
        t += dt
    return pk, at_c, at_s


# ---- the knob bar as a beam (the bar's stress) and as a 2D plane (a riser's root layer)
def section_I(rects):
    """Second moment (mm4) about its own middle of a section made of (width, z0, z1) rectangles."""
    A = sum(w * (z1 - z0) for w, z0, z1 in rects)
    zc = sum(w * (z1 - z0) * (z0 + z1) / 2 for w, z0, z1 in rects) / A
    return sum(w * (z1 - z0) ** 3 / 12 + w * (z1 - z0) * ((z0 + z1) / 2 - zc) ** 2 for w, z0, z1 in rects)


BAR_RECT = (k.BAR_Y1 - k.BAR_Y0, k.BAR_Z0, k.BAR_Z1)
I_BAR = section_I([BAR_RECT])
R_TONGUE = section_I([BAR_RECT, (w_r, k.BAR_Z1, k.SLED_Z0), (k.TONGUE_W, k.SLED_Z0, k.RISER_TOP)]) / I_BAR   # tongue on its foot
R_SOLE = section_I([BAR_RECT, (w_r, k.BAR_Z1, k.SOLE_TOP)]) / I_BAR                 # the sole, under the cap's block
R_BODY = section_I([BAR_RECT, (w_r, k.BAR_Z1, k.RISER_TOP)]) / I_BAR
BEAM_H = 0.5


def riser_pla(which, s):
    """A riser's PLA at knob travel s: the sole (under the cap's block, out to the riser's face), the
    tongue (on its foot) and the body, each (x0, x1), and the x of the tongue's face and the body's
    face that the cap pushes."""
    (f0, f1), (b0, b1) = k.riser_x()
    if which == "F":
        f, t, b = (f0 + s, f0 + k.CAP_T + 0.1 + s), (f0 + k.CAP_T + 0.1 + s, f0 + k.CAP_L + s), (f0 + k.CAP_L + s, f1 + s)
        return f, t, b, t[0], b[0]
    f, t, b = (b1 - k.CAP_T - 0.1 + s, b1 + s), (b1 - k.CAP_L + s, b1 - k.CAP_T - 0.1 + s), (b0 + s, b1 - k.CAP_L + s)
    return f, t, b, t[1], b[1]


def x_sections(man, xs):
    """Area (mm2), the height of its middle (z) and its second moment about that middle for bending in z (mm4) of man's
    cross-section at each x in xs."""
    r = man.transform(k.ON_FRONT_FACE)              # x becomes height: (x, y, z) -> (-z, y, x)
    A, Zm, Iz = [], [], []
    for x in xs:
        a_, az, azz = 0.0, 0.0, 0.0
        for poly in r.slice(x).to_polygons():
            p = np.asarray(poly)
            q = np.roll(p, -1, axis=0)
            cr = p[:, 0] * q[:, 1] - q[:, 0] * p[:, 1]
            a_ += cr.sum() / 2
            az += ((p[:, 0] + q[:, 0]) * cr).sum() / 6
            azz += ((p[:, 0] ** 2 + p[:, 0] * q[:, 0] + q[:, 0] ** 2) * cr).sum() / 12
        A.append(a_)
        Zm.append(-az / a_ if a_ > 0 else ZC)
        Iz.append(azz - az ** 2 / a_ if a_ > 0 else 0.0)
    return np.array(A), np.array(Zm), np.array(Iz)


_xs = np.arange(k.bar_x(0)[0], k.bar_x(0)[1] + 1e-9, BEAM_H)
SEC_A, SEC_Z, SEC_I = x_sections(k.knob_bar(), (_xs[:-1] + _xs[1:]) / 2)   # the slider's real mass along it, its height,
#                                                   and how stiff it really is in z: the bar, the risers, the carriage
# the knob slider's room in z, read off the plates: at each node along it, on planes across its width every 0.25, how far
# it can drop and lift before it meets a plate (the TPU stops and caps left out: squashed TPU holds nothing). The lane's
# floor, the middle plate's floor over the bar and the ledges beside the risers' slots, the rib under the carriage's roof:
# whatever the plates really offer. Also with the middle and top plates sitting off the base plate across, as far as
# their pegs' and screws' play lets them (0.4)
TO_Y = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0]], dtype=float)   # (x, y, z) -> (x, -z, y): slices at height y
PITCH_YS = np.arange(k.Y_CAM + 0.1, k.KNOB_Y0 + k.KNOB_T, 0.25)
PLATE_PLAY = (k.PEG_HOLE_D - k.PEG_D) / 2          # 0.35: how far the middle and top plates can sit off the base plate
#                                                     away from the blade (+y)
PEG_SPAN = k.PEGS[1][0] - k.PEGS[0][0]              # 150: the two pegs apart
PLATE_TURN = PLATE_PLAY / PEG_SPAN                  # the D-shaped holes let each peg's end sit anywhere in its 0.35, so the
#                                                     middle and top plates can also sit turned: about the rear peg with the
#                                                     front one 0.35 out, or the other way round


def pose_of(p):
    """A plates' pose as (dy, turn, x, y of the pivot): a plain number is a sideways shift."""
    return (float(p), 0.0, 0.0, 0.0) if not isinstance(p, tuple) else p


def place(man, p):
    """man (the middle or the top plate) sitting in pose p: turned about z through the pivot, then shifted across."""
    dy, th, px, py = pose_of(p)
    if th:
        man = man.translate([-px, -py, 0]).rotate([0, 0, math.degrees(th)]).translate([px, py, 0])
    return man.translate([0, dy, 0]) if dy else man


def pose_dy(p, x):
    """How far across the plates in pose p sit off where drawn, at x (+ away from the blade)."""
    dy, th, px, _ = pose_of(p)
    return dy + th * (np.asarray(x, dtype=float) - px)


def pose_name(p):
    dy, th, px, _ = pose_of(p)
    if th:
        return f"plates turned about the {'rear' if px < k.HL / 2 else 'front'} peg, the other {PLATE_PLAY:g} out"
    return f"plates {dy:+.2f}"


# ... and toward the blade (-y): each peg hole in the middle and top plates is a D, its flat on the knob side drawn touching
# the peg. Worked out as the plates print: each plate sliced at the middle of each of its own layers (the base and middle
# plates from their bottom faces, the top plate from its top face), every layer of the peg against every layer of the hole
# that shares some height with it, along lines across the peg every 0.05: how far the plate above can move toward -y (and
# +y, and along x) before its own layer meets the peg's. Then a print's PRINT_OFF on top (the flat could print that much out
# from where it is drawn: the round part printing small only pushes the plate away from the blade)
def layer_mids(z0, z1, from_z, down=False):
    """The middles of the printed layers between z0 and z1 of a part printing from from_z (up, or down from it)."""
    out, n = [], 1
    while True:
        a, b = (from_z + k.layer(n - 1) if n > 1 else from_z, from_z + k.layer(n)) if not down else \
            (from_z - k.layer(n), from_z - k.layer(n - 1) if n > 1 else from_z)
        lo, hi = min(a, b), max(a, b)
        if (not down and lo >= z1) or (down and hi <= z0):
            return out
        if hi > z0 and lo < z1:
            out.append((lo, hi, (lo + hi) / 2))
        n += 1


def peg_play(lower, lower_from, upper, upper_from, upper_down, z_face):
    """The play of `upper` on the pegs of `lower` at the plates' face z_face, as both print: (toward -y, toward +y, along x),
    the least over every pair of layers that share height and every line across each peg."""
    pin, pout, px = 9.0, 9.0, 9.0
    zl = layer_mids(z_face, z_face + k.PEG_H, lower_from)
    zu = layer_mids(z_face, z_face + k.PEG_H, upper_from, upper_down)
    for px_, py_ in k.PEGS:
        win = k.box(px_ - 3, px_ + 3, py_ - 3, py_ + 3, z_face - 1, z_face + 3)
        for a0, a1, am in zl:
            peg = (lower ^ win).slice(am)
            for b0, b1, bm in zu:
                if b1 <= a0 + 1e-9 or b0 >= a1 - 1e-9:
                    continue
                hole = (upper ^ win).slice(bm)
                pe, he = slice_edges(peg), slice_edges(hole)
                for X in np.arange(px_ - 1.45, px_ + 1.451, 0.05):
                    for c, d in plate_along(pe, X):
                        for e, f in plate_along(he, X):
                            if e + f > c + d:                    # the plate's wall on the knob side of the peg (a flat
                                pin = min(pin, e - d)            # drawn into the peg: less than 0)
                            else:
                                pout = min(pout, c - f)
                # along x: the same with the slices turned a quarter
                pe2, he2 = slice_edges(peg.rotate(-90)), slice_edges(hole.rotate(-90))
                for Y in np.arange(py_ - 1.45, py_ + 1.451, 0.05):
                    for c, d in plate_along(pe2, Y):          # rotate(-90) takes (x, y) to (y, -x)
                        for e, f in plate_along(he2, Y):
                            px = min(px, e - d if e + f > c + d else c - f)
    return pin, pout, px


PLAY_MB = peg_play(P1, 0.0, P2, k.Z1, False, k.Z1)               # the middle plate on the base plate's pegs
PLAY_TM = peg_play(P2, k.Z1, P3, k.HT, True, k.Z2)               # the top plate on the middle plate's pegs
PLATE_IN = round(max(0.0, max(PLAY_MB[0], PLAY_TM[0]) + k.PRINT_OFF), 6)   # how far a plate can sit off toward the blade
PLATE_SEAT = max(0.0, -min(PLAY_MB[0], PLAY_TM[0]))             # pressed on, each plate sits this far further out than drawn
report(PLATE_IN <= 1e-6 and PLATE_IN <= k.PLATE_IN + 1e-6 and PLATE_PLAY - 0.06 <= min(PLAY_MB[1], PLAY_TM[1]) <= PLATE_PLAY + 1e-6
       and min(PLAY_MB[2], PLAY_TM[2]) > 0.2,
       f"the middle and top plates sit on their pegs at most {PLATE_IN:.2f} off toward the blade: as printed, layer by layer, the "
       f"flat in each D-shaped peg hole meets its peg at {PLAY_MB[0]:+.2f} (middle plate) and {PLAY_TM[0]:+.2f} (top plate), so pressed "
       f"on each slides {PLATE_SEAT:.2f} away from the blade, and a print's {k.PRINT_OFF:g} the wrong way leaves "
       f"{max(PLAY_MB[0], PLAY_TM[0]) + k.PRINT_OFF:+.2f}; away from the blade the round part of the hole leaves "
       f"{min(PLAY_MB[1], PLAY_TM[1]):.2f} (the sideways checks' {PLATE_PLAY:g}), along x {min(PLAY_MB[2], PLAY_TM[2]):.2f}",
       f"held to 0, typed in: the plates never sit toward the blade; every layer of each peg against every layer of its hole that "
       f"shares height with it, on each plate's own layer grid, "
       f"along lines 0.05 apart; the middle plate's first layer set back {k.FOOT:g} at the flat, each peg's top layer "
       f"{k.PEG_LEAD:g} on its knob side")
_lx0, _lx1 = k.lane_x()
_box = k.box(_lx0 - 0.5, _lx1 + 0.5, k.Y_CAM - 1, k.KNOB_Y0 + k.KNOB_T + 1, -5, 30)
PITCH_WALLS = {}


def pitch_walls(p):
    """The plates' slices across the slider's width (TO_Y), the middle and top plates in pose p."""
    p = pose_of(p)
    if p not in PITCH_WALLS:
        PITCH_WALLS[p] = {y: slice_edges((k.union([P1, place(P2, p), place(P3, p)]) ^ _box).transform(TO_Y).slice(y))
                          for y in PITCH_YS}
    return PITCH_WALLS[p]


for _dy in (0.0, -PLATE_IN, -PLATE_PLAY, PLATE_PLAY):
    pitch_walls(_dy)
PITCH_ME = {y: slice_edges(k.knob_bar().transform(TO_Y).slice(y)) for y in PITCH_YS}
PITCH_GAPS = {}
BAR_SOLVES = []                                     # (s, converged) for every bar_stress solve


def pitch_gaps(s, xs, dy=0.0):
    """The knob slider at knob travel s, at each x in xs: how far it can drop, and lift, before it meets a plate (9:
    nothing there), the middle and top plates sitting dy off across (or in the pose dy, turned)."""
    key = (round(s, 6), len(xs), round(float(xs[0]) - s, 6), pose_of(dy))
    if key not in PITCH_GAPS:
        out = np.full((len(xs), 2), 9.0)
        Xq = np.clip(xs, xs[0] + 0.02, xs[-1] - 0.02)
        pw_ = pitch_walls(dy)
        for y in PITCH_YS:
            mine_, walls_ = along_all(PITCH_ME[y], Xq - s), along_all(pw_[y], Xq)
            for i in range(len(xs)):
                for a, b in mine_[i]:                      # the slider, from z -b up to z -a
                    for c, d in walls_[i]:
                        if d <= a + 1e-6:
                            out[i, 1] = min(out[i, 1], a - d)          # a plate over its top
                        elif c >= b - 1e-6:
                            out[i, 0] = min(out[i, 0], c - b)          # a plate under its bottom
                        else:
                            out[i, 0] = out[i, 1] = -1.0
        PITCH_GAPS[key] = out
    return PITCH_GAPS[key]


def contact_solve(K, f, dn, up, kc=2e4, k_reg=1e-4):
    """K u = f with stiff springs (kc) wherever a node's z (the even dofs) drops below -dn or lifts over up: the least of
    the slider's energy (its bending, the loads' work and the springs'), found by semi-smooth Newton with each step cut
    back until the energy falls enough (Armijo). The residual is no good to steer by here: the carriage is 10^4 times as
    stiff as the bar, and a step that lowers the residual can raise the energy and swap the same two contacts back and
    forth for ever. It starts resting on its floor, every node just touching: the push along it makes it want to turn
    bodily, which a slider with no node in touch can't resist, so the first steps keep it held and let go what lifts off.
    The whole load at once, and if that does not settle, in 16 steps, each from the last. Settled when the residual is
    under 1e-7 of the largest load, or a full step leaves the set of nodes in touch as it was and moves no node more than
    1e-9 mm (the energy is quadratic on each such set, so that step was exact). Returns (u, converged)."""
    vi = np.arange(0, len(f), 2)
    tol = 1e-7 * max(1.0, float(np.abs(f).max()))

    def parts(u, f_):
        w = u[0::2]
        over, under = np.maximum(0.0, w - up), np.maximum(0.0, -dn - w)
        Ku = K @ u
        R = Ku - f_
        R[vi] += kc * (over - under) + k_reg * w
        Pi = 0.5 * u @ Ku - f_ @ u + 0.5 * kc * (over @ over + under @ under) + 0.5 * k_reg * (w @ w)
        return R, Pi, (w - up > 0) | (-dn - w > 0)

    diag = np.arange(len(f))
    scale = float(np.abs(np.diag(K)).mean())

    def settle(u, f_, act):
        # the push along the slider (P-delta) makes turning it bodily cost a little energy less, so where few nodes touch
        # a Newton step can point uphill: then it is damped toward a plain downhill step (Levenberg) until it doesn't
        R, Pi, _ = parts(u, f_)
        lam = 0.0
        for _ in range(400):
            if np.linalg.norm(R) < tol:
                return u, act, True
            H = K.copy()
            H[vi, vi] += kc * act + k_reg
            while True:
                Hd = H.copy()
                Hd[diag, diag] += lam
                du = -np.linalg.solve(Hd, R)
                slope = R @ du
                if slope < 0 or lam > 1e6 * scale:
                    break
                lam = max(1e-9 * scale, 10 * lam)
            a = 1.0
            while True:
                Rn, Pin, actn = parts(u + a * du, f_)
                if Pin <= Pi + 1e-4 * a * slope or a < 2.0 ** -30:
                    break
                a /= 2
            exact = a == 1.0 and lam == 0.0 and np.array_equal(actn, act)
            moved = float(np.abs(a * du[0::2]).max())
            u, R, Pi, act_old, act = u + a * du, Rn, Pin, act, actn
            if exact or (np.array_equal(act, act_old) and moved < 1e-9 and lam == 0.0):
                return u, act, True
            lam = lam / 10 if a == 1.0 else max(1e-9 * scale, 10 * lam)
            if lam < 1e-12 * scale:
                lam = 0.0
        return u, act, False
    u0 = np.zeros(len(f))
    u0[0::2] = np.where(dn < 5, -dn, 0.0)
    act0 = (dn < 5)
    u, _, ok_ = settle(u0, f, act0)
    if ok_:
        return u, True
    u, act = u0, act0
    for st in range(1, 17):
        u, act, ok_ = settle(u, f * st / 16, act | (np.abs(u[0::2] + dn) < 1e-6))
    return u, ok_


def spread(loads, masses):
    """The acceleration (mm/ms2, along x) of the bar with `masses` [(where, g)] moving with it under
    `loads` [(where, N along x)], where is 'F' or 'B' (that riser's cap), 'knob', 'rear end' or
    'front end' (on the bar's axis)."""
    return sum(F for _, F in loads) / (RHO * SEC_A.sum() * BEAM_H + sum(m for _, m in masses))


def bar_stress(s, loads, masses=(), full=False, dy=0.0, dz=0.0):
    """The knob slider at knob travel s as a beam bending in z, as stiff along it as its real section (SEC_I: the bar,
    the risers, the carriage and its knob): loads and masses as spread() has them, each riser's push E_R over the bar's
    axis on the riser's PLA, the thumb's E_K over it on the knob, a knob stop's E_S over it ('stop'), its own mass at its
    real height. It lies on whatever the plates offer it in z, read off them (pitch_gaps), the middle and top plates
    sitting dy off across, and drawn dz higher than it is (its play in z: dz -0.2 rests it on its floor; the answer is the
    same, because shifting every gap alike only moves it bodily, and stab_z below proves that). The push along the bar
    also compresses (or stretches) it, N/A, and a compressed bar bends further as it bows. Largest tension (MPa) on the
    plain bar's top or bottom face, the top face at a riser's square foot x CORNER; and where it is. full: that tension
    along every element instead (0 off the plain bar), and the elements' x; full 'local': every element's tension on its own
    section (the bar's height over the element's own second moment and area); 'both': the two, and the x."""
    E = E_PLA
    b, hgt = k.BAR_Y1 - k.BAR_Y0, k.BAR_Z1 - k.BAR_Z0
    A0, I0, Z0 = b * hgt, I_BAR, b * hgt ** 2 / 6
    x0, x1 = k.bar_x(s)
    h = BEAM_H
    xs = np.arange(x0, x1 + 1e-9, h)
    n = len(xs)
    xm = (xs[:-1] + xs[1:]) / 2
    EI = E * SEC_I
    feet, pla = [], {}
    for which in "FB":
        (q0, q1), (t0, t1), (p0, p1), ft, fp = riser_pla(which, s)
        lo, hi = min(q0, t0, p0), max(q1, t1, p1)
        pla[which] = (lo, hi, ft, fp)
        feet += [lo, hi]
    st0, st1 = k.STEM_X0 + s, k.STEM_X1 + s
    m_el, e_el = RHO * SEC_A * h, SEC_Z - ZC
    ax = spread(loads, masses)
    fx, fm = np.zeros(n), np.zeros(n)                # along x, and the turning each puts on the bar

    def put(where, Fx):
        if where in pla:
            lo, hi, ft, fp = pla[where]
            sel = np.nonzero((xs >= lo - 1e-9) & (xs <= hi + 1e-9))[0]
            fx[int(np.argmin(np.abs(xs - ft)))] += SPLIT * Fx
            fx[int(np.argmin(np.abs(xs - fp)))] += (1 - SPLIT) * Fx
            fm[sel] += -E_R * Fx / len(sel)
        elif where in ("knob", "stop"):                # the thumb or a stop, on the knob
            sel = np.nonzero((xs >= st0) & (xs <= st1))[0]
            fx[sel] += Fx / len(sel)
            fm[sel] += -(E_K if where == "knob" else E_S) * Fx / len(sel)
        else:
            fx[0 if where == "rear end" else -1] += Fx
    for where, F in loads:
        put(where, F)
    for where, m in masses:
        put(where, -m * ax)
    for j in (0, 1):                                 # the bar's own inertia, at its real height
        fx[j:n - 1 + j] += -m_el * ax / 2
        fm[j:n - 1 + j] += e_el * m_el * ax / 2
    Nel = -np.cumsum(fx)[:-1]                        # pull along each element (tension +)
    K = np.zeros((2 * n, 2 * n))
    for i in range(n - 1):
        e, L, P = EI[i], h, -Nel[i]
        ke = e / L ** 3 * np.array([[12, 6 * L, -12, 6 * L], [6 * L, 4 * L * L, -6 * L, 2 * L * L],
                                    [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L * L, -6 * L, 4 * L * L]])
        kg = P / (30 * L) * np.array([[36, 3 * L, -36, 3 * L], [3 * L, 4 * L * L, -3 * L, -L * L],
                                      [-36, -3 * L, 36, -3 * L], [3 * L, -L * L, -3 * L, 4 * L * L]])
        d = [2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 3]
        K[np.ix_(d, d)] += ke - kg
    f = np.zeros(2 * n)
    f[1::2] = fm
    g = pitch_gaps(s, xs, dy)
    u, conv = contact_solve(K, f, g[:, 0] + dz, g[:, 1] - dz)
    BAR_SOLVES.append((s, conv))
    th = u[1::2]
    Mel = EI * (th[1:] - th[:-1]) / h
    plain = np.abs(SEC_I - I0) < 0.05 * I0
    at_foot = np.array([any(abs(x - ft) < h for ft in feet) for x in xm])
    top = (-Mel / Z0 + Nel / A0) * np.where(at_foot, CORNER, 1.0)
    bot = Mel / Z0 + Nel / A0
    # and on every element its own section: the bending on the bar's height (its top and bottom faces) over the element's
    # own second moment, and the push along it over its own area, wherever it is (the plain bar, the widening, the carriage)
    cz = (k.BAR_Z1 - k.BAR_Z0) / 2
    local = np.maximum(-Mel * cz / SEC_I, Mel * cz / SEC_I) + Nel / SEC_A
    if full == "local":
        return local, xm
    if full == "both":
        return np.where(plain, np.maximum(top, bot), 0.0), local, xm
    if full:
        return np.where(plain, np.maximum(top, bot), 0.0), xm
    sig = np.where(plain, np.maximum(top, bot), -np.inf)
    i = int(np.argmax(sig))
    return float(sig[i]), float(xm[i]), ("top" if top[i] >= bot[i] else "bottom")


FE_H, NU_PLA = 0.25, 0.35


def scan_widths(cs, xs):
    """Width in y of the cross-section cs along the line x, for each x in xs."""
    e = [np.hstack([np.asarray(p), np.roll(np.asarray(p), -1, axis=0)]) for p in cs.to_polygons()]
    out = np.zeros(len(xs))
    if not e:
        return out
    xa, ya, xb, yb = np.vstack(e).T
    for i, x in enumerate(xs):
        m = ((xa <= x) & (x < xb)) | ((xb <= x) & (x < xa))
        if m.any():
            y = np.sort(ya[m] + (yb[m] - ya[m]) * (x - xa[m]) / (xb[m] - xa[m]))
            out[i] = (y[1::2] - y[0::2]).sum()
    return out


def fe_build():
    """The knob slider as a flat plane-stress model in x-z, square elements FE_H on a side from the
    bar's bottom to the risers' tops, each as thick (in y) as the real part there: the bar with its
    cams and its stem (and the knob's part beside it), the risers' bodies, the full-width feet and
    the tongues; the TPU caps left out. The knob above the bar is left out too, but its mass is
    counted, at its height."""
    bar = k.knob_bar()
    x0, x1 = k.bar_x(0)
    h = FE_H
    nx, nz = int(round((x1 - x0) / h)), int(round((k.RISER_TOP - k.BAR_Z0) / h))
    jb = int(round((k.BAR_Z1 - k.BAR_Z0) / h))
    xc = x0 + (np.arange(nx) + 0.5) * h
    T = np.zeros((nx, nz))
    risers_only = m3.CrossSection.square([400, w_r + 0.02]).translate([-100, k.BAR_Y0 - 0.01])
    for j in range(nz):
        cs = bar.slice(k.BAR_Z0 + (j + 0.5) * h)
        T[:, j] = scan_widths(cs ^ risers_only if j >= jb else cs, xc)
    D = E_PLA / (1 - NU_PLA ** 2) * np.array([[1, NU_PLA, 0], [NU_PLA, 1, 0], [0, 0, (1 - NU_PLA) / 2]])

    def Bmat(xi, eta):
        dN = 0.25 * np.array([[-(1 - eta), (1 - eta), (1 + eta), -(1 + eta)],
                              [-(1 - xi), -(1 + xi), (1 + xi), (1 - xi)]]) * (2 / h)
        B = np.zeros((3, 8))
        B[0, 0::2], B[1, 1::2], B[2, 0::2], B[2, 1::2] = dN[0], dN[1], dN[1], dN[0]
        return B
    g = 1 / math.sqrt(3)
    Ke = sum(Bmat(a, b_).T @ D @ Bmat(a, b_) * (h / 2) ** 2 for a in (-g, g) for b_ in (-g, g))
    co = [0, 0, 1, 1, 1, 1, 0, 0]                    # each element dof's column (0: i, 1: i + 1) ...
    lo = [0, 1, 0, 1, 2, 3, 2, 3]                    # ... and its place in that column (from 2 j)
    ncol, nd = nx + 1, 2 * (nz + 1)
    Dg, Lg = np.zeros((ncol, nd, nd)), np.zeros((nx, nd, nd))
    I, J = np.nonzero(T > 0)
    t = T[I, J]
    for a in range(8):
        for b_ in range(8):
            if co[a] == co[b_]:
                np.add.at(Dg, (I + co[a], 2 * J + lo[a], 2 * J + lo[b_]), Ke[a, b_] * t)
            elif co[b_] == co[a] + 1:
                np.add.at(Lg, (I, 2 * J + lo[a], 2 * J + lo[b_]), Ke[a, b_] * t)
    Dg += np.eye(nd) * 1e-3                          # nodes with nothing round them, and the bar's slide along x
    mass = np.zeros((ncol, nz + 1))
    for di, dj in ((0, 0), (1, 0), (1, 1), (0, 1)):
        np.add.at(mass, (I + di, J + dj), RHO * t * h * h / 4)
    knob_up = k.knob_bar() ^ k.box(k.STEM_X0 - 1, k.STEM_X1 + 1, k.BAR_Y1 + 0.01, 40, k.BAR_Z1, 20)
    V_up, cen_up, _ = mass_props(knob_up)
    return dict(T=T, nx=nx, nz=nz, jb=jb, x0=x0, h=h, D=D, B0=Bmat(0.0, 0.0), Dg=Dg, Lg=Lg, mass=mass,
                m_up=m_bar - mass.sum(), m_up_real=V_up * RHO, e_up=cen_up[2] - ZC if V_up > 0 else E_K)


def fe_solve(FE, s, loads, masses=()):
    """fe_build's model at knob travel s under loads and masses as spread() has them, lying on its
    lane's floor (where there is one) and lifting at most OVER to the middle plate. Returns the
    elements' stresses (MPa: along x, along z)."""
    h, nx, nz, jb, x0 = FE["h"], FE["nx"], FE["nz"], FE["jb"], FE["x0"]
    ncol, nd = nx + 1, 2 * (nz + 1)
    xs = x0 + s + h * np.arange(ncol)
    ax = spread(loads, masses)
    b = np.zeros((ncol, nd))
    b[:, 0::2] -= FE["mass"] * ax                    # the bar's own inertia
    rows = range(int(round((k.SLED_Z0 - k.BAR_Z0) / h)), nz + 1)   # where a wing's push meets a riser
    st = np.nonzero((xs >= k.STEM_X0 + s) & (xs <= k.STEM_X1 + s))[0]
    za, zb = k.BAR_Z1 - ZC, k.BAR_Z0 - ZC

    def at_height(cols, Fx, e):
        """Fx at height e over the bar's axis, on the bar's top and bottom nodes of cols."""
        b[cols, 2 * jb] += Fx * (e - zb) / (za - zb) / len(cols)
        b[cols, 0] += Fx * (za - e) / (za - zb) / len(cols)

    def put(where, Fx):
        if where in ("F", "B"):
            _, _, _, ft, fp = riser_pla(where, s)
            for xf, share in ((ft, SPLIT), (fp, 1 - SPLIT)):
                i = int(np.argmin(np.abs(xs - xf)))
                for j in rows:
                    b[i, 2 * j] += Fx * share / len(rows)
        elif where in ("knob", "stop"):
            at_height(st, Fx, E_K if where == "knob" else E_S)
        else:
            i = 0 if where == "rear end" else nx
            for j in range(jb + 1):
                b[i, 2 * j] += Fx / (jb + 1)
    for where, F in loads:
        put(where, F)
    for where, m in masses:
        put(where, -m * ax)
    at_height(st, -FE["m_up"] * ax, FE["e_up"])      # the knob above the bar
    floor = np.array([(LANE_CS ^ m3.CrossSection.square([h, k.BAR_Y1 - k.BAR_Y0]).translate([x - h / 2, k.BAR_Y0])).area()
                      > 0.05 * h for x in xs])
    kc = 2e4 * h
    act_f, act_c = floor.copy(), np.zeros(ncol, bool)
    for _ in range(60):
        D = FE["Dg"].copy()
        D[act_f, 1, 1] += kc
        D[act_c, 2 * jb + 1, 2 * jb + 1] += kc
        bb = b.copy()
        bb[act_c, 2 * jb + 1] += kc * OVER
        Dp, bp, Lg = np.zeros_like(D), np.zeros_like(bb), FE["Lg"]
        Dp[0], bp[0] = D[0], bb[0]
        for c in range(1, ncol):
            Dp[c] = D[c] - Lg[c - 1].T @ np.linalg.solve(Dp[c - 1], Lg[c - 1])
            bp[c] = bb[c] - Lg[c - 1].T @ np.linalg.solve(Dp[c - 1], bp[c - 1])
        u = np.zeros((ncol, nd))
        u[-1] = np.linalg.solve(Dp[-1], bp[-1])
        for c in range(ncol - 2, -1, -1):
            u[c] = np.linalg.solve(Dp[c], bp[c] - Lg[c] @ u[c + 1])
        wb, wt = u[:, 1], u[:, 2 * jb + 1]
        nf = floor & (wb < 1e-12)
        nc = wt > OVER - 1e-12
        if np.array_equal(nf, act_f) and np.array_equal(nc, act_c):
            break
        act_f, act_c = nf, nc
    i_, j_ = np.meshgrid(np.arange(nx), np.arange(nz), indexing="ij")
    ue = np.stack([u[i_, 2 * j_], u[i_, 2 * j_ + 1], u[i_ + 1, 2 * j_], u[i_ + 1, 2 * j_ + 1],
                   u[i_ + 1, 2 * j_ + 2], u[i_ + 1, 2 * j_ + 3], u[i_, 2 * j_ + 2], u[i_, 2 * j_ + 3]], axis=-1)
    sg = ue @ (FE["D"] @ FE["B0"]).T
    return sg[..., 0], sg[..., 1]


FE = fe_build()


def root_pull(s, which, loads, masses=()):
    """The pull (MPa) across a riser's root layers on its cap's side: where the foot stands on the
    bar, over the tongue's length and over the foot and the sole together, and where the tongue
    stands on the foot; each the pull and the bending of that layer over that length (the riser
    loaded on its cap's side, so that end pulls)."""
    sx, sz = fe_solve(FE, s, loads, masses)
    h, T = FE["h"], FE["T"]
    xc = FE["x0"] + s + (np.arange(FE["nx"]) + 0.5) * h
    (q0, q1), (t0, t1), _, _, _ = riser_pla(which, s)
    worst = 0.0
    for z_int, (a, b) in ((k.BAR_Z1, (t0, t1)), (k.BAR_Z1, (min(q0, t0), max(q1, t1))), (k.SLED_Z0, (t0, t1))):
        j = int(round((z_int - k.BAR_Z0) / h))
        sel = np.nonzero((xc > a) & (xc < b) & (T[:, j] > 0))[0]
        t, sgz, x = T[sel, j], sz[sel, j], xc[sel]
        L, tw = len(sel) * h, t.mean()
        Nf, Mf = np.sum(sgz * t * h), np.sum(sgz * t * h * (x - x.mean()))
        worst = max(worst, Nf / (tw * L) + abs(Mf) / (tw * L * L / 6))
    return worst


_xm0 = (_xs[:-1] + _xs[1:]) / 2
_rs = np.zeros(len(_xm0), bool)
for (_a, _b) in k.riser_x():
    _rs |= (_xm0 > _a) & (_xm0 < _b)
_cs = (_xm0 > k.STEM_X0 + 1) & (_xm0 < k.STEM_X1 - 1) & ~_rs
CORNER = 1.3                                # the bar's stress at a riser's square foot
LIM_ROOT = 12.0                             # MPa across a printed layer
report(abs(RHO * SEC_A.sum() * BEAM_H - m_bar) < 0.02 * m_bar and abs(FE["m_up"] - FE["m_up_real"]) < 0.03 * m_bar and
       abs(CONTACT[0][0] - CONTACT[1][0]) < 0.01 and abs(CONTACT[0][2] - CONTACT[1][2]) < 0.01,
       f"the knob slider's models: the beam's mass along it from its real shape ({RHO * SEC_A.sum() * BEAM_H:.2f} g of {m_bar:.2f}); "
       f"in z, read off its real shape, the risers up to {max(SEC_I[_rs]) / I_BAR:.0f} times as stiff as the plain bar, the carriage "
       f"{min(SEC_I[_cs]) / I_BAR:.0f} to {max(SEC_I[_cs]) / I_BAR:.0f} times; the flat model, {FE['nx']} x {FE['nz']} elements of {FE_H} mm, holds {FE['mass'].sum():.2f} g and the knob "
       f"above it {FE['m_up_real']:.2f} g; a knob stop meets {A_STOP:.1f} mm2 of the knob's end face (both ends alike), its middle "
       f"{E_S:.2f} over the bar's axis (the thumb's {E_K:.2f}) and at y {Y_S:.2f} (the thumb's {Y_K:.2f})")

# the stops' faces are recessed inside the knob's outer part, so however far the knob squashes a stop (up to STOP_SQ) it meets
# only that outer part: the overlap of the knob pushed d into its stop, read off the parts, grows as A_STOP x d
sq_rows = []
for d in (0.3, 0.8, k.STOP_SQ):
    for st_, s_ in ((STOP_R, S_STOP_R - d), (STOP_F, S_STOP_F + d)):
        sq_rows.append((d, overlap(k.knob_bar(s_), st_) / (A_STOP * d)))
report(all(0.95 <= r_ <= 1.01 for _, r_ in sq_rows),
       f"each knob stop meets only the knob's outer part, however far it squashes: pushed {', '.join(f'{d:.1f}' for d in (0.3, 0.8, k.STOP_SQ))} "
       f"into either stop the knob overlaps it {min(r_ for _, r_ in sq_rows):.3f}-{max(r_ for _, r_ in sq_rows):.3f} times "
       f"{A_STOP:.1f} mm2 x the squash (the area the landings use)", f"the stop's face recessed {k.STOP_RECESS} inside y "
       f"{k.END_Y + 0.05:.2f}; the knob's inner part is cut back {k.END_CUT}, so with a flat stop it would join from 0.5 in")
knocks = []
BAR_CASES = []                              # (what, limit, s, loads, masses, the bar's stress) for the plate-play check below
CAP_KNOCKS = []                             # (what, s, the cap's push, limit, the knob held on its front stop)
EVERY_THROW = []                            # (what, MPa): the PLA that bends on every throw, for the fatigue check below
v_every = max(max(never[i][2] for i in solid_cases), max(r["v_release"] for r in SOLID_OKS))   # parts printed solid
v_flick = max(land[i][2] for i in solid_cases)
v_let = max(letgo_speed(E, h, mu, b) for E, b in ((15.0, k.BAND), (20.0, k.BAND), (26.0, k.BAND), (30.0, k.BAND_SOFT),
                                                     (10.0, k.BAND_STRONG), (15.0, k.BAND_STRONG)) for h in (0.1, 0.3) for mu in MU)
for label, v, lim in (("every throw (thumb kept on)", v_every, 20), ("thumb flicked off as the knob lands", v_flick, 30),
                      ("knob let go just before the trip", v_let, 30)):
    F, sq = max(hit(v, E) for E in (15.0, 20.0, 26.0, 30.0))
    sq = max(hit(v, E)[1] for E in (15.0, 20.0, 26.0, 30.0))
    if "every" in label:        # the thumb holds the knob forward, on its front stop
        s_, loads, masses = S_STOP_F, [("F", F), ("stop", -F)], []
    else:                       # the bar running back, sled B riding on it
        s_, loads, masses = -k.SOFT, [("F", F)], [("B", m_sled)]
    b_s, b_x, _ = bar_stress(s_, loads, masses)
    BAR_CASES.append((label, lim, s_, loads, masses, b_s))
    rp = root_pull(s_, "F", loads, masses)
    CAP_KNOCKS.append((label, s_, F, lim, "every" in label))   # for the sideways check below
    ok = F * WING_MPA <= lim and rp <= LIM_ROOT and b_s <= lim and sq <= 0.55 * k.CAP_T
    if "every" in label:
        EVERY_THROW.extend([("a sled's wing landing on its riser", F * WING_MPA), ("the riser's root layers then", rp),
                            ("the knob's bar then", b_s)])
    report(ok, f"{label}: sled meets its riser's TPU cap at up to {v:.1f} m/s: {F:.0f} N, squashing it {sq:.1f} "
               f"of {k.CAP_T}; {F * WING_MPA:.1f} MPa at the wing's root, {rp:.1f} across the riser's root layers, "
               f"{b_s:.1f} in the bar (x {b_x:.0f}) (limits {lim}, {LIM_ROOT:.0f}, {lim})")

# every throw the thumb drives the knob on to its stop: the knob, with the thumb's 10 g moving with it, lands on the
# stop square on, at the height of the thumb's push; 0.1 later the sled its riser carries meets its pad through the
# riser's cap, still pushed by the riser while the band pulls the sled back. TPU stiffens as rubber does: at the half
# squashes here a straight line is far too soft (the let-go landing below uses the same curve; the quick hits above
# stay linear, which is kinder to their squash limits)
BANDS = ((15.0, k.BAND), (20.0, k.BAND), (26.0, k.BAND), (26.0, k.BAND_SOFT), (30.0, k.BAND_SOFT),
         (10.0, k.BAND_STRONG), (15.0, k.BAND_STRONG))
rows = []
for E_tpu, band in BANDS:
    for h, mu, fill in itertools.product((0.1, 0.3), MU, (0.6, 1.0)):
        la = thumb_off("never", E_tpu, h, mu, fill, band)[3]
        if la is not None:
            rows.append((E_tpu, m_bar * fill, m_sled * fill, la["v"], la["F_th"], la["T"], mu, la["rub"]))
E_a, m1_a, m2_a, v_a, F1_a, T_a, mu_a, R_a = (np.array(col) for col in zip(*rows))
lo_, hi_ = np.zeros_like(E_a), np.full_like(E_a, k.CAP_T)
for _ in range(50):                                     # the cap squashed by the riser's push before the landing
    mid_ = (lo_ + hi_) / 2
    big = cap_force(E_a, mid_, True) > T_a * twist(mu_a)
    lo_, hi_ = np.where(big, lo_, mid_), np.where(big, mid_, hi_)
d0_a = lo_
N_LAND = len(E_a)                                       # each case with the stop at both ends of its stiffness range
E_a, m1_a, m2_a, v_a, F1_a, T_a, mu_a, R_a, d0_a = (np.tile(a_, len(STOP_FACTORS)) for a_ in
                                                    (E_a, m1_a, m2_a, v_a, F1_a, T_a, mu_a, R_a, d0_a))
SF_a = np.repeat(STOP_FACTORS, N_LAND)
GAP_PAD = k.SOFT - k.KNOB_SOFT                           # 0.1: the knob meets its stop, then its sled meets its pad


def knob_landing(k_th=None):
    """The knob landings (the thumb held rigid, or on its pad of k_th N/mm), and the bar's and the
    risers' worst, worked out at the moments the cap and the stop push hardest, both ways round: on
    the forward stroke the front stop and riser B's cap stop it, on the return the rear stop and
    riser F's cap."""
    m1 = m1_a + (M_THUMB if k_th is None else 0.0)
    pk, at_c, at_s = landing(E_a, m1, m2_a, v_a, v_a, F1_a, T_a, mu_a, d0_a, GAP_PAD, 0.0, True, m_th=M_THUMB, k_th=k_th,
                             rub=R_a, sf=SF_a)
    res = []
    for at in (at_c, at_s):
        for i in picks(pk, SF_a):
            Fc, Fs, Fk, x1, rb = at["Fc"][i], at["Fs"][i], at["Fk"][i], at["x1"][i], R_a[i]
            for s_, which, loads in ((S_STOP_F + x1, "B", [("B", -Fc), ("stop", -Fs), ("knob", Fk), ("rear end", -rb)]),
                                     (S_STOP_R - x1, "F", [("F", Fc), ("stop", Fs), ("knob", -Fk), ("rear end", rb)])):
                res.append((bar_stress(s_, loads), root_pull(s_, which, loads), which))
                BAR_CASES.append((f"knob landing, {'thumb held rigid' if k_th is None else 'thumb on its pad'}", 20, s_, loads, (),
                                  res[-1][0][0]))
    return pk, max(res, key=lambda r: r[0][0]), max(r[1] for r in res)


# the knob, its stem and the guards under the most a landing puts on them. The knob slider prints standing on its
# bottom face, the handle plates flat, so every one of these is in a layer: limit 20 for every throw, 30 for a rare knock
H_LIP = k.KNOB_TOP - k.END_Z                           # a lip's root, above the cut at the knob's end (all of it, to be safe)
ALPHA_STEM = (1 - 0.63 * STEM_T / STEM_B) / 3           # a flat bar turned about its long middle: tau = T / (alpha b t2)


def stem_mpa(pk):
    """What joins the bar and the knob, at its thinnest: the carriage's roof over its rib (STEM_B long, STEM_T thick),
    from what the landing put through it: the force it carries (Fst) as shear, the turn over (Mp, about y) as torsion,
    both in its layers, and the turn round (My, about z) as bending in its layers; the biggest principal stress with all
    three at their worst together. And the torsion's shear alone: at the roof's two ends it runs across the layers. The
    knob's own weight is added to the stops' and the thumb's turn, as landing() has it, though it mostly works against
    the stop's."""
    tau_t = pk["Mp"].max() / (ALPHA_STEM * STEM_B * STEM_T ** 2)
    tau = tau_t + 1.5 * pk["Fst"].max() / (STEM_B * STEM_T)
    sig = pk["My"].max() / (STEM_T * STEM_B ** 2 / 6)
    return sig / 2 + math.hypot(sig / 2, tau), tau, sig, tau_t


def lip_mpa(pk):
    """An end lip at its root (in a layer), bent by the stop's even push on its end (the thumb pushes the saddle's ridges
    now, not the lips)."""
    return 6 * max(pk["Mlip"].max(), 0.0) / (H_LIP * k.LIP_L ** 2)


H_RIDGE = k.KNOB_TOP - k.BAR_Z0                        # the saddle's ridges stand the knob's whole height


def ridge_mpa(pk):
    """The saddle's ridge the thumb pushes, at its root (in a layer)."""
    return 6 * pk["Mridge"].max() / (H_RIDGE * k.SADDLE_L ** 2)


# a stop's back bears on its guard's face (all three plates) except over the T's mouth; each plate's part of a guard is
# a short cantilever off the handle's side; in the base plate the T-slot's shoulders in front of the head's pocket are
# each held along one side only, 0.9 out to the mouth, 1.2 thick
YC_STOP = (k.STOP_Y0 + k.STOP_Y1) / 2
MOUTH = (k.T_NECK_W + 2 * k.T_GRIP) * (k.Z1 - k.STOP_Z0)
A_BACK = (k.STOP_Y1 - k.STOP_Y0) * k.STOP_H - MOUTH
GUARD_ROOT = k.GUARD_TOP + (k.GUARD_Y1 - k.HW / 2)    # each guard's length where it meets the handle's side
SHOULDER = ((k.T_HEAD_W / 2 - k.T_GRIP) - (k.T_NECK_W / 2 + k.T_GRIP), k.T_NECK_L - 0.1)
PLATES = (("base", k.STOP_Z0, k.Z1, k.Z1 - k.CHAMFER), ("middle", k.Z1, k.Z2, k.Z2 - k.Z1),
          ("top", k.Z2, k.STOP_Z0 + k.STOP_H, k.HT - k.Z2 - k.CHAMFER))


def guard_mpa(Fs):
    """At the stop's push Fs: the bearing on the guard's face, the worst plate's guard at its root, and the shoulders."""
    p_ = Fs / A_BACK
    roots = {}
    for name, za, zb, t in PLATES:
        A = (k.STOP_Y1 - k.STOP_Y0) * (zb - za) - (MOUTH if name == "base" else 0.0)
        roots[name] = p_ * A * (YC_STOP - k.HW / 2) / (t * GUARD_ROOT ** 2 / 6)
    w, t = SHOULDER
    return p_, roots, 3 * p_ * (w / t) ** 2


def knob_parts(pk, lim, label):
    """Report the knob's lips and stem and the guards under a landing's worst."""
    s1, tau, sig, tau_t = stem_mpa(pk)
    lip, ridge = lip_mpa(pk), ridge_mpa(pk)
    bear, roots, sh = guard_mpa(pk["Fs"].max())
    worst = max(roots, key=roots.get)
    report(max(s1, lip, ridge, roots[worst], sh) <= lim and bear <= lim and tau_t <= LIM_ROOT,
           f"  {label}: the carriage's roof carries up to {pk['Fst'].max():.0f} N ({tau:.1f} MPa of shear in its layers, {sig:.1f} of bending, "
           f"{s1:.1f} at worst together; its twist's {tau_t:.1f} across its layers at its ends, limit {LIM_ROOT:.0f}), the saddle's "
           f"ridge {ridge:.1f} at its root (the thumb up to {pk['Fk'].max():.0f} N on it), an end lip {lip:.1f} under the stop; the stop "
           f"({pk['Fs'].max():.0f} N) bears {bear:.1f} MPa on its guard, bends the {worst} plate's guard {roots[worst]:.1f} at its root "
           f"and the T-slot's shoulders {sh:.1f} (limit {lim})",
           f"the carriage's roof {STEM_B:.0f} x {STEM_T:.2f} and {k.KNOB_FOOT_Y0 - k.LEG_Y1:.1f} across its rib; the saddle's ridges {k.SADDLE_L} long, {H_RIDGE:.2f} tall, {k.LIP} proud, {k.SADDLE:g} apart; an end lip {k.LIP_L} long, {H_LIP:.2f} tall; "
           f"each guard {GUARD_ROOT:.1f} long at the handle's side, the stop's middle {YC_STOP - k.HW / 2:.2f} out from it")
    if lim == 20:                               # every throw
        EVERY_THROW.extend([("the carriage's roof", s1), ("its twist across the roof's layers", tau_t), ("a lip of the knob", lip),
                            ("the saddle's ridge", ridge),
                            ("a guard's root", roots[worst]), ("the T-slot's shoulders", sh), ("a stop bearing on its guard", bear)])
    return max(s1, lip, ridge, roots[worst], sh, bear)


for k_th, name in ((None, "the thumb's 10 g held rigid on the knob"), (15.0, "the thumb on a 15 N/mm pad")):
    pk, ((b_w, b_x, b_f), _, b_which), rp_w = knob_landing(k_th)
    s_go = S_STOP_F + pk["x1"].max()
    report(len(rows) == len(BANDS) * 12 and pk["ds"].max() <= k.STOP_SQ and pk["dc"].max() <= 0.55 * k.CAP_T and
           pk["dp"].max() <= free - 0.5 and s_go <= S_HI,
           f"knob landing, every throw, {name}: the thumb drives the knob on to its stop at up to {v_a.max():.1f} m/s, still pushing "
           f"{F1_a.max():.0f} N; the stop squashes up to {pk['ds'].max():.2f} of its {k.STOP_L:g} ({pk['Fs'].max():.0f} N, limit "
           f"{k.STOP_SQ:.1f}), the riser's cap {pk['dc'].max():.2f} of {k.CAP_T} ({pk['Fc'].max():.0f} N), the pad {pk['dp'].max():.1f}; "
           f"the knob goes on to s {s_go:.2f} at most",
           f"{len(rows)} cases: the three bands in their TPUs, losses 10-30 %, PLA friction 0.2-0.4, printed 60-100 % solid; each "
           f"with the stop {' and '.join(f'{f_:g}' for f_ in STOP_FACTORS)} times as stiff as E A / L; damping ratio 0.10; the knob "
           f"meets its stop {GAP_PAD:.1f} before its sled meets its pad")
    EVERY_THROW.extend([("a wing, the knob landing", pk["Fc"].max() * WING_MPA), ("a riser's root layers, the knob landing", rp_w),
                        ("the knob's bar, the knob landing", b_w)])
    report(pk["Fc"].max() * WING_MPA <= 20 and rp_w <= LIM_ROOT and b_w <= 20,
           f"  that is {pk['Fc'].max() * WING_MPA:.1f} MPa at the wing's root, {rp_w:.1f} across the riser's root layers, {b_w:.1f} in the "
           f"bar (the {b_f} face at x {b_x:.0f}, landing on riser {b_which}'s side; the thumb's push on the knob up to "
           f"{pk['Fk'].max():.0f} N, {E_K:.2f} over the bar's axis, the stop's {E_S:.2f}; limits 20, {LIM_ROOT:.0f}, 20 for every throw)",
           "the bar and the riser roots worked out at the moments the cap and the stop push hardest, both ways round")
    knob_parts(pk, 20, "and the knob")

# the knob let go just before the trip: the band throws the bar and sled B back, riser F's cap picks up sled F, and
# 1.4 on the knob meets its rear stop, 0.1 before sled F meets the rear pad
rows = []
for E_tpu, band in BANDS:
    kb = E_tpu * band[0] * band[1] / k.BAND_RELAXED
    for h, mu in itertools.product((0.1, 0.3), MU):
        T = (1 - h) * kb * k.BAND_PRELOAD
        rows.append((E_tpu, letgo_speed(E_tpu, h, mu, band), T / twist(mu), T, mu))
E_l, v_l, F1_l, T_l, mu_l = (np.tile(np.array(col), len(STOP_FACTORS)) for col in zip(*rows))
SF_l = np.repeat(STOP_FACTORS, len(rows))
gap_pad = k.C_TRIP + k.G_P + k.SOFT
gap_stop = k.C_TRIP + k.G_P + k.KNOB_SOFT
pk_l, at_cl, at_sl = landing(E_l, M_OTHER, m_sled, v_l, 0.0, F1_l, T_l, mu_l, 0.0, gap_pad, gap_stop, True, thumb=False, sf=SF_l)
E_in = 0.5 * M_OTHER * v_l ** 2
report(pk_l["dc"].max() <= 0.6 * k.CAP_T and pk_l["dp"].max() <= free - 0.5 and pk_l["ds"].max() <= 0.6 * k.STOP_L,
       f"  it lands with up to {E_in.max():.0f} mJ: riser F's cap picks up sled F at {v_l.max():.1f} m/s and squashes up to "
       f"{pk_l['dc'].max():.2f} of {k.CAP_T} ({pk_l['Fc'].max():.0f} N, limit {0.6 * k.CAP_T:.2f}), the rear pad {pk_l['dp'].max():.1f} "
       f"({free:.1f} of it out of its pocket), the knob's rear stop {pk_l['ds'].max():.2f} of {k.STOP_L:g} ({pk_l['Fs'].max():.0f} N, "
       f"limit {0.6 * k.STOP_L:.1f}); the knob goes on {pk_l['x1'].max() - gap_stop:.2f} past where it meets its stop",
       "two masses, the bar with sled B and then sled F, TPU stiffening as rubber does, damping ratio 0.10")
res = []
for at in (at_cl, at_sl):
    for i in picks(pk_l, SF_l):
        s_ = k.C_TRIP + k.G_P - at["x1"][i]
        loads, masses = [("F", at["Fc"][i]), ("stop", at["Fs"][i]), ("B", -T_l[i])], [("B", m_sled)]
        res.append((bar_stress(s_, loads, masses), root_pull(s_, "F", loads, masses)))
        BAR_CASES.append(("let-go landing", 30, s_, loads, masses, res[-1][0][0]))
        # and its mirror: the knob let go just before the return trip lands on its front stop, riser B's cap picking up
        # sled B, sled F riding on riser F (the slider is not its own mirror)
        s_ = k.THROW - (k.C_TRIP + k.G_P) + at["x1"][i]
        loads, masses = [("B", -at["Fc"][i]), ("stop", -at["Fs"][i]), ("F", T_l[i])], [("F", m_sled)]
        res.append((bar_stress(s_, loads, masses), root_pull(s_, "B", loads, masses)))
        BAR_CASES.append(("let-go landing, before the return trip", 30, s_, loads, masses, res[-1][0][0]))
(b_l, b_lx, b_lf), _ = max(res, key=lambda r: r[0][0])
rp_l = max(r[1] for r in res)
report(pk_l["Fc"].max() * WING_MPA <= 30 and rp_l <= LIM_ROOT and b_l <= 30,
       f"  that is {pk_l['Fc'].max() * WING_MPA:.1f} MPa at the wing's root, {rp_l:.1f} across the riser's root layers, "
       f"{b_l:.1f} in the bar (the {b_lf} face at x {b_lx:.0f}) (limits 30, {LIM_ROOT:.0f} and 30 for this rare knock), on the rear "
       f"stop or, let go before the return trip, on the front one")
knob_parts(pk_l, 30, "and the knob (nothing pushes it but its stop)")
# bar_stress works the slider out where it is drawn. Moved bodily in its play in z, resting on its lane's floor (0.2 down) or
# lifted to the middle plate (0.35 up), every gap changes alike and the answer is the same: the hardest knocks prove it. The
# middle and top plates can sit up to PLATE_PLAY off the base plate across (their pegs' and screws' play), which moves the
# ledges that hold the bar down beside the risers' slots: the knocks again with them that far off, each way
_z_drop = float(np.min(pitch_gaps(0.0, np.arange(k.bar_x(0)[0], k.bar_x(0)[1] + 1e-9, BEAM_H))[:, 0]))
_z_lift = k.Z1 - k.BAR_Z1
stab_z = []
for what, lim, s_, loads, masses, b0 in sorted(BAR_CASES, key=lambda q: -q[5] / q[1])[:3]:
    stab_z.append(max(abs(bar_stress(s_, loads, masses, dz=dz)[0] - b0) for dz in (-_z_drop, _z_lift)))
off = []
for what, lim, s_, loads, masses, b0 in BAR_CASES:
    off.append((what, lim, max(bar_stress(s_, loads, masses, dy=dy)[0] for dy in (-PLATE_PLAY, PLATE_PLAY)), b0))
w_off = max(off, key=lambda q: q[2] / q[1])
n_conv = sum(c for _, c in BAR_SOLVES)
report(n_conv == len(BAR_SOLVES) and max(stab_z) < 0.05 and all(b <= lim for _, lim, b, _ in off),
       f"the knob slider bending in z, on the room the plates really give it: {n_conv} of {len(BAR_SOLVES)} solves so far converged; resting "
       f"on its floor ({_z_drop:.2f} down), as drawn and lifted to the middle plate ({_z_lift:.2f} up) it bends the same (within "
       f"{max(stab_z):.3f} MPa); with the middle and top plates {PLATE_PLAY:g} off across either way, the hardest is {w_off[2]:.1f} MPa "
       f"({w_off[0]}, {w_off[3]:.1f} with them where drawn; limit {w_off[1]}); turned about either peg they sit between those all "
       f"along (and the sideways rows below work the turned plates out as they are)",
       "; ".join(f"{what} {b:.1f}/{lim}" for what, lim, b, _ in off[:12]))
for what, lim, b, _ in off:
    if lim == 20:
        EVERY_THROW.append((f"the knob's bar, {what}, the plates {PLATE_PLAY:g} off", b))


# ---- the rail as a beam lying between the base plate's walls: pushed end on by the latch block at one
# catch, held by the cushion at the far end of its spine, leaning on whatever walls its play runs out on
RAIL_ZS = [k.RAIL_Z0 + 0.1 + 0.2 * i for i in range(int(round((k.RAIL_TOP - k.RAIL_Z0) / 0.2)))]   # the middle of each
#                                                   layer the rail stands over, where the base plate's walls can meet it
RAIL_WALLS = [np.vstack([np.hstack([np.asarray(p), np.roll(np.asarray(p), -1, axis=0)]) for p in P1.slice(z).to_polygons()])
              for z in RAIL_ZS]
CUSH_GAP = k.cushion("F").bounding_box()[0] - k.SPINE_X1   # 0.1: the rail moves this far before it meets a cushion


def rail_mesh():
    """Nodes along the rail about 0.5 apart, with the catches' ends on nodes; the rail's inner and
    outer faces at each node; and each element's faces, read off the rail's real shape."""
    seg = lambda a, b: np.linspace(a, b, max(1, int(round((b - a) / 0.5))) + 1)
    xs = np.unique(np.concatenate([seg(k.SPINE_X0, k.RAIL_X0), seg(k.RAIL_X0, k.RAIL_X1), seg(k.RAIL_X1, k.SPINE_X1)]))
    cs = k.rail().slice((k.RAIL_Z0 + k.RAIL_TOP) / 2)
    faces = lambda x: (lambda b: (b[1], b[3]))((cs ^ m3.CrossSection.square([0.05, 30]).translate([x - 0.025, 0])).bounds())
    node = np.array([faces(min(max(x, k.SPINE_X0 + 0.03), k.SPINE_X1 - 0.03)) for x in xs])
    el = np.array([faces(x) for x in (xs[:-1] + xs[1:]) / 2])
    return xs, node[:, 0], node[:, 1], el[:, 0], el[:, 1]


RAIL_XS, RAIL_NLO, RAIL_NHI, RAIL_ELO, RAIL_EHI = rail_mesh()


def rail_gaps(shift):
    """How far each node of the rail, shifted `shift` along its groove, can move in (toward the
    channel) and out before it meets the base plate, read off the plate's slices through the rail's
    height. -1 where the plate is where the rail is."""
    gin, gout = np.full(len(RAIL_XS), 99.0), np.full(len(RAIL_XS), 99.0)
    for i, x in enumerate(RAIL_XS):
        lo, hi = RAIL_NLO[i], RAIL_NHI[i]
        for edges in RAIL_WALLS:
            for a, b in plate_along(edges, x + shift):
                if b <= lo + 0.02:
                    gin[i] = min(gin[i], lo - b)
                elif a >= hi - 0.02:
                    gout[i] = min(gout[i], a - hi)
                else:
                    gin[i] = gout[i] = -1.0
    return gin, gout


def rail_stress(F, closed=True, shift=0.0, method="newton", steps=16):
    """The rail as a beam pushed along its length at a catch's end by F N, at Y_LET (the catch's
    corner, where a leaning block bears), and held by the far cushion on the middle of the spine's
    end, the rail shifted `shift` along its groove (into that cushion). Each step in the rail's
    centre line along the way turns the push into a bend; the rail leans on the base plate's walls,
    read off the plate itself, wherever its play there runs out (stiff springs, kc), and the push
    bends it more as it bows (P-delta).
    method 'newton': F is put on in `steps` equal steps, the P-delta growing with it, and each step
    is solved by semi-smooth Newton, H = K + kc on the walls in contact, the step halved until the
    residual falls, until |R| < 1e-7 F. A first pass at the first step's load leaves the P-delta
    out: until two walls hold it the rail floats, and pushed end on a floating strut is unstable
    sideways, so Newton would set off the wrong way. Where a node runs into a wall the step did not
    know about, the wall's spring outgrows the fall in the residual for any step longer than about
    1e-5 of it; the smallest step is then taken anyway, which brings that wall into the next one.
    method 'active set': the old loop (the whole load at once, contacts switched on and off until
    they stop changing), which converges only at low loads; for a cross-check.
    Returns a dict: converged, the largest compression and tension (MPa), each with its x (the
    rail's own, unshifted) and face ('inner', the catches' side, or 'outer')."""
    xs, elo, ehi = RAIL_XS, RAIL_ELO, RAIL_EHI
    n = len(xs)
    L, xm = np.diff(xs), (xs[:-1] + xs[1:]) / 2
    t = k.RAIL_TOP - k.RAIL_Z0
    w, yc = ehi - elo, (ehi + elo) / 2
    x_load = k.RAIL_X0 if closed else k.RAIL_X1
    il = int(np.argmin(np.abs(xs - x_load)))
    pushed = (xm > x_load) if closed else (xm < x_load)
    KE = [beam_k(L[e], E_PLA * t * w[e] ** 3 / 12) for e in range(n - 1)]
    Kb, Kg = np.zeros((2 * n, 2 * n)), np.zeros((2 * n, 2 * n))
    for e in range(n - 1):
        d = slice(2 * e, 2 * e + 4)
        Kb[d, d] += KE[e]
        if pushed[e]:
            Kg[d, d] += beam_kg(L[e])
    y_end = (k.SPINE_Y0 + k.SPINE_Y1) / 2               # the cushion pushes on the middle of the spine's end
    m0 = np.zeros(2 * n)                                 # the turning the push puts on each node, per N
    if closed:
        m0[2 * il + 1] += yc[il] - Y_LET
        for j in range(il + 1, n - 1):
            m0[2 * j + 1] += yc[j] - yc[j - 1]
        m0[2 * (n - 1) + 1] += y_end - yc[n - 2]
    else:
        m0[2 * il + 1] += Y_LET - yc[il - 1]
        for j in range(1, il):
            m0[2 * j + 1] += yc[j] - yc[j - 1]
        m0[1] += yc[0] - y_end
    gin, gout = rail_gaps(shift)
    kc, k_reg, vi = 2e4, 1e-3, np.arange(0, 2 * n, 2)     # k_reg: a hair of spring, so a rail touching nothing is solvable

    def resid(u, K, f):
        v = u[0::2]
        R = K @ u - f
        R[vi] += kc * (np.maximum(0.0, v - gout) - np.maximum(0.0, -gin - v)) + k_reg * v
        return R, (v - gout >= -1e-12) | (-gin - v >= -1e-12)

    u, converged = np.zeros(2 * n), True
    if method == "active set":
        K, f = Kb - F * Kg, F * m0
        act_lo, act_hi = np.zeros(n, bool), np.zeros(n, bool)
        converged = False
        for _ in range(200):
            H = K.copy()
            H[vi, vi] += kc * (act_lo | act_hi) + k_reg
            rhs = f.copy()
            rhs[vi] += kc * (gout * act_hi - gin * act_lo)
            u = np.linalg.solve(H, rhs)
            v = u[0::2]
            n_lo, n_hi = (v < -gin) | (act_lo & (v < -gin + 1e-6)), (v > gout) | (act_hi & (v > gout - 1e-6))
            if (n_lo == act_lo).all() and (n_hi == act_hi).all():
                converged = True
                break
            act_lo, act_hi = n_lo, n_hi
    else:
        for st in range(steps + 1):
            lam = max(st, 1) / steps
            K, f = (Kb if st == 0 else Kb - lam * F * Kg), lam * F * m0
            R, act = resid(u, K, f)
            for _ in range(200):
                if np.linalg.norm(R) < 1e-7 * F:
                    break
                H = K.copy()
                H[vi, vi] += kc * act + k_reg
                du = -np.linalg.solve(H, R)
                a = 1.0
                while True:
                    Rn, actn = resid(u + a * du, K, f)
                    if np.linalg.norm(Rn) < np.linalg.norm(R) or a < 2.0 ** -16:
                        break
                    a /= 2
                u, R, act = u + a * du, Rn, actn
            if st > 0:
                converged = converged and np.linalg.norm(R) < 1e-7 * F
    # the bending moment at each element's two ends (its real shape between the nodes), M = EI v''
    M = np.array([(lambda fe: (-fe[1], fe[3]))(KE[e] @ u[2 * e:2 * e + 4]) for e in range(n - 1)])
    Mx = M[np.arange(n - 1), np.argmax(np.abs(M), axis=1)]
    A, Z = t * w, t * w ** 2 / 6
    comp, ten = np.abs(Mx) / Z + F * pushed / A, np.abs(Mx) / Z - F * pushed / A
    ic, it = int(np.argmax(comp)), int(np.argmax(ten))
    # M > 0 bends the inner face in tension, the outer in compression
    return {"converged": converged, "comp": float(comp[ic]), "x_comp": float(xm[ic]), "face_comp": "outer" if Mx[ic] > 0 else "inner",
            "ten": float(ten[it]), "x_ten": float(xm[it]), "face_ten": "inner" if Mx[it] > 0 else "outer"}


def rail_where(x, closed):
    """Where along the rail x is, in words."""
    u = x - k.RAIL_X0 if closed else k.RAIL_X1 - x
    which = "closed" if closed else "open"
    for upto, part in ((k.SEG_FLAT, "flat"), (k.SEG_FLAT + k.RAMP_L, "ramp"), (k.SEG_L, "taper")):
        if 0 <= u <= upto:
            return f"the {which} catch's {part}, {u:.1f} from its end"
    return "the spine"


F_cock, E_cock = max((thumb_at_trip(E, 0.3, b)[0], E) for E, b in ((20.0, k.BAND), (26.0, k.BAND), (30.0, k.BAND_SOFT),
                                                                    (15.0, k.BAND_STRONG)))
r_nom = throw(20.0, 0.15, 0.3, 0.9, follow=True)
r_hard = max(oks, key=lambda r: r["F_cush"])
RAIL_CASES = [("cocked", F_cock, CUSH_GAP + F_cock / k_cush(E_cock), 20),
              ("a nominal bounce", r_nom["F_cush"], CUSH_GAP + r_nom["d_cush"], 20),
              ("the hardest bounce", r_hard["F_cush"], CUSH_GAP + r_hard["d_cush"], 30)]
n_conv = 0
for label, F, sh, lim in RAIL_CASES:
    rs = [(rail_stress(F, True, sh), True), (rail_stress(F, False, -sh), False)]
    n_conv += sum(bool(r["converged"]) for r, _ in rs)
    conv = all(r["converged"] for r, _ in rs)
    rc, cc = max(rs, key=lambda q: q[0]["comp"])
    rt, _ = max(rs, key=lambda q: q[0]["ten"])
    if lim == 20:                               # cocked, and a normal bounce: every throw
        EVERY_THROW.extend([(f"the rail, {label}, compression", rc["comp"]), (f"the rail, {label}, tension", rt["ten"])])
    report(conv and rc["comp"] <= lim and rt["ten"] <= lim,
           f"rail, {label}: {F:.0f} N on a catch's end, the rail shifted {sh:.1f} into its cushion: at most {rc['comp']:.1f} MPa of compression "
           f"(its {rc['face_comp']} face at x {rc['x_comp']:.1f}, {rail_where(rc['x_comp'], cc)}) and {rt['ten']:.1f} of tension "
           f"(its {rt['face_ten']} face at x {rt['x_ten']:.1f}) (limit {lim})" + ("" if conv else "; the solve DID NOT CONVERGE"),
           f"either catch, the push at y {Y_LET:.2f}, the walls read off the base plate at the rail's shift "
           f"({CUSH_GAP:.1f} + F / k_cush), the load put on in 16 steps, each solved to |R| < 1e-7 F")
ra, rn = rail_stress(F_cock, True, RAIL_CASES[0][2], "active set"), rail_stress(F_cock, True, RAIL_CASES[0][2])
report(n_conv == 2 * len(RAIL_CASES) and ra["converged"] and abs(ra["comp"] - rn["comp"]) < 0.01 and abs(ra["ten"] - rn["ten"]) < 0.01,
       f"rail model: all {2 * len(RAIL_CASES)} stepped Newton solves converge in every step; at the cocked load, where the old active-set "
       f"loop (the whole load at once) still converges, it gives the same {ra['comp']:.2f} and {ra['ten']:.2f} MPa ({rn['comp']:.2f} and "
       f"{rn['ten']:.2f} stepped)", "above about 20 N that loop cycles between contacts and returns whatever it tried last, "
       "which is what the old rail check printed")
def yaw_case(s, loads, side=(), z_loads=None, z_masses=(), masses=()):
    """yaw_stress (solved once: see there) and bar_stress's bending on the lane's floor for the same loads, added at each
    element: (the sideways stress and its x; the worst corner of the plain bar, both together; converged; the rib's push;
    every wall's push; each node's push)."""
    sig, x, sig_el, conv, rib, walls, wl = yaw_stress(s, loads, side, masses)
    zs, zx = bar_stress(s, z_loads, z_masses, full=True)
    both = float(np.max(np.where(YAW_PLAIN, np.interp(YAW_XM + s, zx, zs) + sig_el, -np.inf)))
    return sig, x, both, conv, rib, walls, wl


print("\n== The knob bar sideways")
# Every row below is worked out on every version of the slider and the plates: the slider as drawn, and with its carriage's
# play on the rib CARRIAGE_PLAY wider each side (a print comes out that much off, and the crowned ends wear); each with the
# middle and top plates where drawn, as far toward the blade as their D-shaped peg holes let them (PLATE_IN) and as far away
# from it as the holes' round part lets them (PLATE_PLAY), and turned about either peg with the other one's end PLATE_PLAY out
# (the risers' slots are in the middle plate, the rib, the lane and the cams' walls in the base plate). Where the plates sit off,
# the slider is first moved bodily across, as their slots push it (and turned a little if that is not enough), until nothing
# starts inside a wall. Every row is held to its limit on every version, and so is what the carriage's two ends raise the bar's
# sideways bending to (corner_mpa, with corner_fe's factors and the bending in z on each element's own section)
CARRIAGE_PLAY = 0.05


def plan_thickness(man, xa_, nx, y0, ny, h, sub=4):
    """A part in plan as a map of square elements h on a side, nx along x from xa_ and ny across from y0: each element as thick
    (z) as the part is tall there (its slices every 0.05, sampled sub x sub times in each element, so a curved edge is no
    staircase). Returns (thickness, whether the element is uniform: no edge or step runs through it, the elements' x, y)."""
    xc, yc = xa_ + (np.arange(nx) + 0.5) * h, y0 + (np.arange(ny) + 0.5) * h
    o = (np.arange(sub) + 0.5) / sub - 0.5
    xf, yf = (xc[:, None] + o[None, :] * h).ravel(), (yc[:, None] + o[None, :] * h).ravel()
    Tf = np.zeros((len(xf), len(yf)))
    bb = man.bounding_box()
    for z in np.arange(bb[2] + 0.025, bb[5], 0.05):
        ed = slice_edges(man.slice(z))
        if not len(ed):
            continue
        xa, ya, xb, yb = ed.T
        for j, Y in enumerate(yf):
            m = ((ya <= Y) & (yb > Y)) | ((yb <= Y) & (ya > Y))
            if m.any():
                xs_ = np.sort(xa[m] + (xb[m] - xa[m]) * (Y - ya[m]) / (yb[m] - ya[m]))
                for a, b in zip(xs_[0::2], xs_[1::2]):
                    Tf[(xf >= a) & (xf < b), j] += 0.05
    T4 = Tf.reshape(nx, sub, ny, sub)
    return T4.mean(axis=(1, 3)), (T4.max(axis=(1, 3)) - T4.min(axis=(1, 3))) < 1e-6, xc, yc


def plan_solve(T, h, sgn, face):
    """A plate in plan stress, each square element h on a side as thick as T says (Q4, PLA): a pure sideways moment of
    1000 N mm carried in at one end (sgn +1: the first column of elements, else the last), as a straight-line push across
    that column's own section, the other end held. Returns (the largest principal stress, either sign, in each element, (nx,
    ny); the loaded section's middle across, as an element y index offset; the nominal M c / I there, c to the further of
    face's two faces (y, from the first element row's edge))."""
    import scipy.sparse as sp_
    import scipy.sparse.linalg as spl_
    nx, ny = T.shape
    D_ = E_PLA / (1 - NU_PLA ** 2) * np.array([[1, NU_PLA, 0], [NU_PLA, 1, 0], [0, 0, (1 - NU_PLA) / 2]])
    g = 1 / math.sqrt(3)

    def Bm(xi, eta):
        dN = 0.25 * np.array([[-(1 - eta), (1 - eta), (1 + eta), -(1 + eta)], [-(1 - xi), -(1 + xi), (1 + xi), (1 - xi)]]) * (2 / h)
        B = np.zeros((3, 8))
        B[0, 0::2], B[1, 1::2], B[2, 0::2], B[2, 1::2] = dN[0], dN[1], dN[1], dN[0]
        return B
    Ke = sum(Bm(a, b).T @ D_ @ Bm(a, b) * (h / 2) ** 2 for a in (-g, g) for b in (-g, g))
    nid = lambda i, j: j * (nx + 1) + i
    I, J = np.nonzero(T > 1e-6)
    nodes = np.stack([nid(I, J), nid(I + 1, J), nid(I + 1, J + 1), nid(I, J + 1)], axis=1)
    dofs = np.stack([2 * nodes, 2 * nodes + 1], axis=2).reshape(len(I), 8)
    N = (nx + 1) * (ny + 1)
    K = sp_.csr_matrix(((T[I, J][:, None, None] * Ke[None]).reshape(len(I), 64).ravel(),
                        (np.repeat(dofs, 8, axis=1).ravel(), np.tile(dofs, (1, 8)).ravel())), shape=(2 * N, 2 * N))
    used = np.zeros(N, bool)
    used[nodes.ravel()] = True
    i_ld, i_held = (0, nx) if sgn > 0 else (nx, 0)
    yrel = (np.arange(ny) + 0.5) * h
    jb = np.nonzero(T[0 if sgn > 0 else nx - 1, :] > 1e-6)[0]
    tb = T[0 if sgn > 0 else nx - 1, jb]
    ycb = (tb * yrel[jb]).sum() / tb.sum()
    Ib = (tb * h * (yrel[jb] - ycb) ** 2).sum() + (tb * h ** 3 / 12).sum()
    f = np.zeros(2 * N)
    for jj, t in zip(jb, tb):
        for jn in (jj, jj + 1):
            f[2 * nid(i_ld, jn)] += -sgn * 1000.0 * (jn * h - ycb) / Ib * t * h / 2
    jc = np.nonzero(T[nx - 1 if sgn > 0 else 0, :] > 1e-6)[0]
    fixed = set()
    for q in set([nid(i_held, j) for j in jc] + [nid(i_held, j + 1) for j in jc]) | set(np.nonzero(~used)[0].tolist()):
        fixed |= {2 * q, 2 * q + 1}
    free = np.setdiff1d(np.arange(2 * N), np.array(sorted(fixed)))
    u = np.zeros(2 * N)
    u[free] = spl_.spsolve(K[free][:, free].tocsc(), f[free])
    S = (D_ @ (Bm(0, 0) @ u[dofs].T)).T
    r_ = np.sqrt(((S[:, 0] - S[:, 1]) / 2) ** 2 + S[:, 2] ** 2)
    P = np.zeros(T.shape)
    P[I, J] = np.maximum(np.abs((S[:, 0] + S[:, 1]) / 2 + r_), np.abs((S[:, 0] + S[:, 1]) / 2 - r_))
    nom = 1000.0 * max(ycb - face[0], face[1] - ycb) / Ib
    return P, ycb, nom


def corner_fe(end, h, sub=4, L_bar=10.0, L_car=12.0, y1=23.5, reach=4.0):
    """The knob slider round one end of its carriage ('back' or 'front') as a flat plane-stress model in plan (plan_thickness,
    plan_solve): square elements h on a side, each as thick as the real slider is tall there, under a pure sideways bending
    moment carried in along the bar from L_bar out, the carriage held L_car in. The largest principal stress in an element no
    edge or step runs through, within reach of the end face on the bar's outer half, over the plain bar's M c / I: (the bar,
    up to the inner leg's face; the roof over the rib's channel, out to the knob; the plain bar away from the end)."""
    man = k.knob_bar()
    x_e, sgn = (k.STEM_X0, 1) if end == "back" else (k.STEM_X1, -1)
    xa_, xb_ = (x_e - L_bar, x_e + L_car) if sgn > 0 else (x_e - L_car, x_e + L_bar)
    y0 = k.BAR_Y0
    nx, ny = int(round((xb_ - xa_) / h)), int(round((y1 - y0) / h))
    T, FULL, xc, yc = plan_thickness(man, xa_, nx, y0, ny, h, sub)
    P, ycb, nom = plan_solve(T, h, sgn, (0.0, k.BAR_Y1 - y0))
    ycb += y0
    X, Y = np.meshgrid(xc, yc, indexing="ij")
    near = (np.abs(X - x_e) <= reach) & (Y > ycb) & FULL & (T > 1e-6)
    bar_ = near & (Y <= k.LEG_Y1 + 1e-9)
    roof_ = near & (Y > k.LEG_Y1 + 1e-9) & (Y < k.KNOB_Y0)
    far_ = (np.abs(X - (x_e - sgn * 0.6 * L_bar)) < h) & (Y < k.BAR_Y1) & (Y > k.BAR_Y1 - 1.5 * h) & (T > 1e-6)
    return (float(P[bar_].max() / nom), float(P[roof_].max() / nom) if roof_.any() else 0.0, float(P[far_].max() / nom))


def peterson(h, r_d, d=None, ratio=2.0, sub=4):
    """The plan FE's self-test: a stepped flat bar in bending (Peterson's chart), d wide stepping up to ratio x d with a fillet
    r_d x d each side, through the same plate solver and the same reading (the largest principal stress in an element no
    edge runs through, within 3 of the step) as corner_fe: the factor over the narrow bar's M c / I."""
    d = d or (k.BAR_Y1 - k.BAR_Y0)
    D_, r = ratio * d, r_d * d
    xa, xj, xb = 0.0, 12.0, 26.0             # each part over twice as long as the wide part is wide (the chart's L/D)
    ym = D_ / 2 + 1.0
    ya = ym - D_ / 2 - 0.5
    nx, ny = int(round((xb - xa) / h)), int(round((D_ + 1.0) / h))
    T, lo, hi = np.zeros((nx, ny)), np.ones((nx, ny)), np.zeros((nx, ny))
    for a in range(sub):
        for b in range(sub):
            X, Y = np.meshgrid(xa + (np.arange(nx) + (a + 0.5) / sub) * h, ya + (np.arange(ny) + (b + 0.5) / sub) * h, indexing="ij")
            m = ((X < xj) & (np.abs(Y - ym) <= d / 2)) | ((X >= xj) & (np.abs(Y - ym) <= D_ / 2))
            for sg in (1, -1):
                m |= (X >= xj - r) & (X < xj) & (sg * (Y - ym) >= d / 2) & (sg * (Y - ym) <= d / 2 + r) & \
                    ((X - (xj - r)) ** 2 + (Y - ym - sg * (d / 2 + r)) ** 2 >= r * r)
            T += m / sub ** 2
            lo, hi = np.minimum(lo, m), np.maximum(hi, m)
    FULL = (hi - lo) < 1e-6
    P, _, nom = plan_solve(T, h, 1, (ym - d / 2 - ya, ym + d / 2 - ya))
    xc = xa + (np.arange(nx) + 0.5) * h
    near = (np.abs(xc[:, None] - xj) < 3.0) & (T > 1e-6) & FULL
    return float(P[near].max() / nom)


CORNER_H = (0.025, 0.0167)
# the plan FE's self-test first: Peterson's stepped flat bar in bending (D/d 2, the plain bar's width, fillets r/d 0.1 and
# 0.2), through the same solver and read the same way, against Peterson's chart as Pilkey fits it (Roark's Formulas, Table
# 6-1, opposite shoulder fillets in a stepped flat bar, in-plane bending). The finer mesh must come within 8 %, and so must the
# factor the carriage's ends are given (the finer mesh pushed on by its last rise: the coarse mesh reads low)
def peterson_chart(r_d, ratio=2.0):
    """Kt of a stepped flat bar in in-plane bending, opposite shoulder fillets r/d, D/d = ratio (Pilkey's fit to Peterson's
    chart, typed in from Roark's Table 6-1)."""
    hr, t = (ratio - 1) / 2 / r_d, (ratio - 1) / ratio
    q = math.sqrt(hr)
    if hr <= 2.0:
        c = (1.006 + 0.967 * q + 0.013 * hr, -0.270 - 2.372 * q + 0.708 * hr, 0.662 + 1.157 * q - 0.908 * hr,
             -0.405 + 0.249 * q - 0.200 * hr)
    else:
        c = (1.058 + 1.002 * q - 0.038 * hr, -3.652 + 1.639 * q - 0.436 * hr, 6.170 - 5.687 * q + 1.175 * hr,
             -2.558 + 3.046 * q - 0.701 * hr)
    return c[0] + c[1] * t + c[2] * t ** 2 + c[3] * t ** 3


PETERSON = {rd_: (peterson_chart(rd_), [peterson(h_, rd_) for h_ in CORNER_H]) for rd_ in (0.1, 0.2)}
_pet_x = {rd_: v[1][1] + max(0.0, v[1][1] - v[1][0]) for rd_, v in PETERSON.items()}
report(all(abs(v[1][1] / v[0] - 1) <= 0.08 and abs(_pet_x[rd_] / v[0] - 1) <= 0.08 for rd_, v in PETERSON.items()),
       "the plan FE checked against Peterson's chart: a flat bar stepping from 3.35 to twice as wide in bending, through the same "
       "solver and read the same way (the largest principal stress in an element no edge runs through, within 3 of the step): "
       + "; ".join(f"fillet r/d {rd_:g}: {v[1][0]:.3f} and {v[1][1]:.3f} (meshes {CORNER_H[0]} and {CORNER_H[1]}), {_pet_x[rd_]:.3f} "
                   f"pushed on by its last rise, against the chart's {v[0]:.2f} ({100 * (v[1][1] / v[0] - 1):+.1f} % and "
                   f"{100 * (_pet_x[rd_] / v[0] - 1):+.1f} %)" for rd_, v in PETERSON.items()),
       "the finer mesh and the factor taken from it each within 8 % of the chart (Pilkey's fit, Roark's Formulas Table 6-1); "
       "the coarse mesh reads low, so a factor is never taken from it alone")
_kt = {end: [corner_fe(end, h_) for h_ in CORNER_H] for end in ("back", "front")}
# each factor taken at the finer mesh and pushed on by what the last refinement added (a weak corner keeps rising slowly)
CORNER_KT = {end: tuple(v[1][i] + max(0.0, v[1][i] - v[0][i]) for i in (0, 1)) for end, v in _kt.items()}
_kt_far = min(v[1][2] for v in _kt.values())
report(all(max(abs(v[1][i] - v[0][i]) for i in (0, 1)) < 0.08 for v in _kt.values()) and 0.97 < _kt_far < 1.01,
       f"the carriage's two ends in a plan FE of their real shape: the bar's sideways bending is raised there to "
       + "; ".join(f"{end} end: the bar x{CORNER_KT[end][0]:.3f}, the roof x{CORNER_KT[end][1]:.3f}" for end in CORNER_KT)
       + f" (meshes {CORNER_H[0]} and {CORNER_H[1]}: " + "; ".join(f"{end} {v[0][0]:.3f}/{v[1][0]:.3f} and {v[0][1]:.3f}/{v[1][1]:.3f}"
                                                                for end, v in _kt.items())
       + f"; each pushed on by its last rise; the two meshes must agree within 0.08 either way); the plain bar away from them "
         f"{_kt_far:.3f} (beam theory 1)",
       f"plane stress, each element as thick as the slider is tall there (slices every 0.05, sampled 4 x 4 in each element); "
       f"the bar widens over {k.END_TAPER[0]:g} behind the back end and {k.END_TAPER[1]:g} in front of the front end (to "
       f"{k.FRONT_TAPER_TOP:.2f} there, the lane's wall {k.LANE_Y1:.2f} past the knob's slot), the roof's ends cut back "
       f"{'/'.join(f'{c_:g}' for c_ in sorted(set(k.ROOF_CUTS)))} on its {len(k.ROOF_CUTS)} layers with quarter-ellipses; a square "
       f"end would not converge (3.7 at 0.025 and rising)")


XM_TURN = (k.STEM_X0 + k.STEM_X1) / 2                 # a slider started turned turns about its carriage's middle


def slider_slices(play, shift, turn=0.0):
    """The slider's slices for the sideways model with its carriage's play on its rib `play` wider each side, moved `shift`
    across and turned `turn` (rad) about the carriage's middle."""
    lg, kf = k.LEG_Y1, k.KNOB_FOOT_Y0
    k.LEG_Y1, k.KNOB_FOOT_Y0 = lg - play, kf + play
    try:
        man = k.knob_bar()
    finally:
        k.LEG_Y1, k.KNOB_FOOT_Y0 = lg, kf
    man = man.warp_batch(lambda p_: np.column_stack([p_[:, 0], p_[:, 1] + shift + turn * (p_[:, 0] - XM_TURN), p_[:, 2]]))
    return {z: slice_edges(man.slice(z)) for z in YAW_ZS}


def start_v(g_):
    """Where version g_'s slider starts, across, at each node of YAW_XS (its bodily shift and turn)."""
    sh_, turn_ = YAW_GEOM[g_][2], YAW_GEOM[g_][5]
    return sh_ + turn_ * (YAW_XS - XM_TURN)


# eight versions: the carriage's fit as drawn and CARRIAGE_PLAY looser, each with the middle and top plates where drawn (the
# D-shaped holes' flats on their pegs: never toward the blade, PLATE_IN), PLATE_PLAY away from the blade, and turned about either
# peg with the other one's end PLATE_PLAY out (the D-shaped holes let each peg sit anywhere in its 0.35). Where the plates sit
# off, the slider is first moved bodily across, as their slots push it, and if that is not enough turned a little about its
# carriage's middle, until nothing starts inside a wall
S_SEEN = (S_LO, 0.0, S_TRIP_LATE, k.THROW - S_TRIP_LATE, k.THROW, S_HI)
POSES = list(dict.fromkeys([pose_of(0.0), pose_of(-PLATE_IN if PLATE_IN > 0 else 0.0), pose_of(PLATE_PLAY),
                            (0.0, PLATE_TURN, k.PEGS[0][0], k.PEGS[0][1]), (0.0, -PLATE_TURN, k.PEGS[1][0], k.PEGS[1][1])]))
YAW_GEOM["drawn"] = YAW_GEOM["drawn"][:4] + (pose_of(0.0), 0.0)
geom_bad = []
for play_ in (0.0, CARRIAGE_PLAY):
    for pose_ in POSES:
        key_ = f"play +{play_:g}, {pose_name(pose_)}"
        if play_ == 0 and pose_ == pose_of(0.0):
            continue
        walls_ = YAW_GEOM["drawn"][0] if pose_ == pose_of(0.0) else \
            {z: slice_edges(k.union([P1, place(P2, pose_), place(P3, pose_)]).slice(z)) for z in YAW_ZS}
        sg_ = -1.0 if float(np.mean(pose_dy(pose_, YAW_XS))) < 0 else 1.0
        found = False
        for turn_ in (0.0, 5e-4, -5e-4, 1e-3, -1e-3, 2e-3, -2e-3):
            for sh_ in [0.0] + [sg_ * a_ for a_ in (0.05, 0.1, 0.11, 0.12, 0.15, 0.2, 0.25)]:
                YAW_GEOM[key_] = (walls_, slider_slices(play_, sh_, turn_), sh_, play_, pose_, turn_)
                for s_ in S_SEEN:
                    YAW_GAPS.pop((key_, s_), None)
                if all(min(yaw_gaps(s_, key_)[1].min(), yaw_gaps(s_, key_)[2].min()) >= 0.002 for s_ in S_SEEN):
                    found = True
                    break
            if found:
                break
        if not found:
            geom_bad.append(key_)
GEOMS = list(YAW_GEOM)
ENFORCED = list(GEOMS)                 # every version, each held to every limit
report(not geom_bad and len(GEOMS) == 8, f"the sideways model's {len(GEOMS)} versions: " + "; ".join(
    f"{g_}" + (f" (the slider started {YAW_GEOM[g_][2]:+.2f} across" + (f" and turned {YAW_GEOM[g_][5] * 1000:+.1f} mrad"
                                                                          if YAW_GEOM[g_][5] else "") + ", as the plates' slots push it)"
               if YAW_GEOM[g_][2] or YAW_GEOM[g_][5] else "")
    for g_ in GEOMS) + ": in each the slider sits clear of every wall at both ends of its travel and at both trips",
       "no clear place for: " + ", ".join(geom_bad))
# no pinch: whatever the plates' offset, the slider has room between the base plate's guides (the rib, the lane's walls)
# and the middle plate's (the risers' slots): the play left at the tightest of the versions
pinch = min(min(yaw_gaps(s_, g_)[1].min() + yaw_gaps(s_, g_)[2].min() for s_ in S_SEEN) for g_ in GEOMS)
report(pinch >= 0.1, f"nothing pinches the slider across, the plates anywhere in their play: at least {pinch:.2f} of play in and "
                     f"out together at its tightest node", "the base plate's rib and lane against the middle plate's riser slots")
# how far the thumb can press the slider in, bodily, from where it is drawn: the least room in at any node, on every version at
# every knob travel the model sees, less how far out the version starts it (at its furthest-in node). The latch checks take the
# bar pushed in BAR_IN; nothing may let it go further
press, press_at = -9.0, ""
for g_ in GEOMS:
    for s_ in S_SEEN:
        xs_, gin_, _ = yaw_gaps(s_, g_)
        i_ = int(np.argmin(gin_))
        p_ = float(gin_[i_] - np.min(start_v(g_)))
        if p_ > press:
            press, press_at = p_, f"{g_}, s {s_:.1f}, x {xs_[i_] - s_:.1f} (its room in {gin_[i_]:.2f} where it starts)"
press_v = {g_: max(float(yaw_gaps(s_, g_)[1].min() - np.min(start_v(g_))) for s_ in S_SEEN) for g_ in GEOMS}
report(press <= k.BAR_IN + 1e-6,
       f"the thumb can press the knob slider in bodily at most {press:.2f} from where it is drawn ({press_at}), the latch checks' "
       f"BAR_IN {k.BAR_IN:g}: " + "; ".join(f"{g_} {v_:.2f}" for g_, v_ in press_v.items()),
       "the least room in at any node, on every version, at both ends of the knob's travel and at both trips, less how far out "
       "that version starts the slider")


yaw_rows = []
# every push: the thumb at the trip, at the latest let-go (the band most stretched), the bar pushing sled B through riser
# B's cap and the block through cam A, which also pushes the bar out, and the walls rubbing what side_rub has them rub:
# nominal, and the hardest push any band in any TPU it is fitted to needs (the thumb check's and the hang test's). The return
# push is not the push's mirror (riser F stands behind the carriage, riser B in its front): it is worked out at its own trip
pushes = [(20.0, k.BAND, 0.3), max([(E_, b_, m_) for E_, b_ in ((20.0, k.BAND), (26.0, k.BAND), (30.0, k.BAND_SOFT),
                                                                 (12.0, k.BAND_STRONG)) + tuple(HANG_STIFF) for m_ in MU],
                                   key=lambda q: thumb_at_trip(q[0], q[2], q[1])[-1])]


def corner_mpa(s, r, zz, zl):
    """At each end of the carriage: the bar's sideways moment where it widens into the carriage (the largest on the bar's side of
    the end face, over the widening and half an element more), as a stress on the plain bar (M c / I) raised by the plan FE's
    factor for the bar, plus the bending in z nearby (the larger of the plain bar's zz and every element's own section's, zl,
    half an element further each way); and the same moment raised by the factor for the roof's cut-back end, plus the
    carriage's own bending in z over its first ROOF_CUT. The largest of these, and which."""
    xm, c_I = YAW_XM + s, (W_BAR / 2) / I_PLAIN
    out = (0.0, "")
    for end, x_e, lo, hi, car in (("back", k.STEM_X0 + s, -max(k.END_TAPER[0], 0.5) - 0.5, -0.25, (0.0, k.ROOF_CUT)),
                                  ("front", k.STEM_X1 + s, 0.25, max(k.END_TAPER[1], 0.5) + 0.5, (-k.ROOF_CUT, 0.0))):
        sel = (xm >= x_e + lo) & (xm <= x_e + hi)
        Mn = float(r[9][sel].max())
        zone = (xm >= x_e + lo - 0.5) & (xm <= x_e + hi + 0.5)
        zn = max(float(np.max(zz[zone])), float(np.max(zl[zone])))
        on_car = (xm >= x_e + car[0]) & (xm <= x_e + car[1])
        zr = float(np.max(np.abs(zl[on_car])))
        kb, kr = CORNER_KT[end]
        for v_, what in ((zn + kb * Mn * c_I, f"the bar at the carriage's {end} end"),
                         (zr + kr * Mn * c_I, f"the roof at the {end} end")):
            if v_ > out[0]:
                out = (v_, what)
    return out


def with_floor(s, r, z_loads, z_masses=(), dy=0.0):
    """yaw_stress's answer r and bar_stress's bending on the lane's floor for the same loads, the plates dy off (or in the pose
    dy), added at each element of the plain bar: the worst corner; and at the carriage's two ends what corner_mpa finds."""
    zs, zl_, zx = bar_stress(s, z_loads, z_masses, full="both", dy=dy)
    zz = np.interp(YAW_XM + s, zx, zs)
    zl = np.interp(YAW_XM + s, zx, zl_)
    return float(np.max(np.where(YAW_PLAIN, zz + r[2], -np.inf))), corner_mpa(s, r, zz, zl)


def push_case(E_tpu, mu, band, back):
    """The push (or the return push) at its trip as a case: (s, loads, side pushes, z loads, the thumb's push, the walls'
    rubbing)."""
    kb = E_tpu * band[0] * band[1] / k.BAND_RELAXED
    Fb = kb * (k.BAND_PRELOAD + S_TRIP_LATE - k.G_P - k.C_TRIP)
    tn = math.tan(math.radians(k.CAM_ANGLE) + math.atan(mu))
    F_lat = (2 * mu * Fb + k_arm * k.arm_deflect_for(k.Y_CAM)) / (1 - mu * tn)
    F_cam = F_lat * (tn + mu)
    Fr = Fb * twist(mu)
    base = Fr + F_cam + 0.3
    rub = side_rub(E_tpu, mu, band, Fr, F_cam, F_lat, base, 0.0, back)[0]
    if back:
        s_ = k.THROW - S_TRIP_LATE
        x_cam = k.CAM_B_TOP + s_
        return (s_, [(X_THUMB_R + s_, Y_K, -(base + rub)), (f0_ + s_, y_hit, Fr), (x_cam, k.Y_CAM, F_cam), (f0_ + s_, Y_AXIS, rub)],
                [(x_cam, F_lat)], [("knob", -(base + rub)), ("F", Fr), ("front end", F_cam + rub)], base + rub, rub)
    s_ = S_TRIP_LATE
    x_cam = k.CAM_A_TOP + s_
    return (s_, [(X_THUMB_F + s_, Y_K, base + rub), (b1_ + s_, y_hit, -Fr), (x_cam, k.Y_CAM, -F_cam), (b1_ + s_, Y_AXIS, -rub)],
            [(x_cam, F_lat)], [("knob", base + rub), ("B", -Fr), ("rear end", -F_cam - rub)], base + rub, rub)


def add_row(what, cases, lim):
    """A row of yaw_rows: each case (s, loads, side pushes, masses riding on the slider, z loads, z masses, where the blade
    is [(c, the latch's mode)]) worked out on every version of the slider and the plates."""
    res = []
    for ci, (s_, loads, side, masses, zl, zm, blade) in enumerate(cases):
        for g_ in GEOMS:
            r = yaw_stress(s_, loads, side, masses, geom=g_)
            b_, (bc_, bw_) = with_floor(s_, r, zl, zm, YAW_GEOM[g_][4])
            res.append(dict(case=ci, geom=g_, s=s_, r=r, both=b_, corner=bc_, corner_at=bw_, blade=blade, loads=loads, side=side,
                            masses=masses))
    yaw_rows.append(dict(what=what, lim=lim, res=res))


for E_tpu, band, mu in pushes:
    for back in (False, True):
        s_, loads, side, zl, Fth, rub = push_case(E_tpu, mu, band, back)
        add_row(f"every {'return ' if back else ''}push, the thumb {Fth:.1f} N at the trip ({Fth - rub:.1f} and {rub:.1f} the walls "
                f"rub; TPU {E_tpu:g}, friction {mu})", [(s_, loads, side, (), zl, (), [((86 - k.C_COCK) if back else k.C_COCK, "held")])],
                FATIGUE_MPA)


# the model takes each element's turning about its own middle: a push straight through the carriage along its own middle,
# 100 N each end, must bow it almost not at all (taken about the bar's line, as before, it bows it)
_s = k.THROW / 2
_on = (YAW_XM >= k.STEM_X0 + 1) & (YAW_XM <= k.STEM_X1 - 1)
_yc = float(np.mean(YAW_SEC[_on, 1]))
_tl = [(k.STEM_X0 + _s + 0.3, _yc, 100.0), (k.STEM_X1 + _s - 0.3, _yc, -100.0)]
_bow = lambda r_: float(np.ptp(np.diff(r_[7][(YAW_XS >= k.STEM_X0 + 1) & (YAW_XS <= k.STEM_X1 - 1)])))
_b1, _b0 = _bow(yaw_stress(_s, _tl)), _bow(yaw_stress(_s, _tl, own_axis=False))
report(_b1 < 0.05 * _b0,
       f"the sideways model bends each part about its own middle: 100 N pushed through the carriage along its middle bends it "
       f"{_b1 * 1000:.2f} um across a node, against {_b0 * 1000:.2f} um taken about the bar's line",
       f"the carriage's middle at y {_yc:.2f}, {_yc - Y_AXIS:.2f} out from the bar's line")


# where the blade is at each kind of knock: a knob landing comes a few ms after the trip, the blade thrown on (riding) up to
# about where sled F meets its riser; the let-go knob lands with the blade still latched
THROWN_F = [(k.C_COCK, "riding"), (k.C_TRIP + powered, "riding")]
THROWN_B = [(86 - k.C_COCK, "riding"), (86 - k.C_TRIP - powered, "riding")]


# the knob landings, at the moments the cap and the stop push hardest, as knob_landing has them, both ways round: the thumb
# on the saddle's front ridge pushing on (the walls' rubbing on top, held back on the bar's line), the stop at the knob's
# end, the riser's cap at the sled; the stop at both ends of its stiffness range
for k_th, name in ((None, "the thumb held rigid"), (15.0, "the thumb on its pad")):
    m1 = m1_a + (M_THUMB if k_th is None else 0.0)
    pk, at_c, at_s = landing(E_a, m1, m2_a, v_a, v_a, F1_a, T_a, mu_a, d0_a, GAP_PAD, 0.0, True, m_th=M_THUMB, k_th=k_th,
                             rub=R_a, sf=SF_a)
    cases = []
    for at in (at_c, at_s):
        for i in picks(pk, SF_a):
            Fc, Fs, Fk, x1, rb = at["Fc"][i], at["Fs"][i], at["Fk"][i], at["x1"][i], R_a[i]
            s_ = S_STOP_F + x1
            cases.append((s_, [(X_THUMB_F + s_, Y_K, Fk), (k.STEM_X1 + s_, Y_S, -Fs), (b1_ + s_, y_hit, -Fc), (b1_ + s_, Y_AXIS, -rb)],
                          (), (), [("B", -Fc), ("stop", -Fs), ("knob", Fk), ("rear end", -rb)], (), THROWN_F))
            s_ = S_STOP_R - x1
            cases.append((s_, [(X_THUMB_R + s_, Y_K, -Fk), (k.STEM_X0 + s_, Y_S, Fs), (f0_ + s_, y_hit, Fc), (f0_ + s_, Y_AXIS, rb)],
                          (), (), [("F", Fc), ("stop", Fs), ("knob", -Fk), ("rear end", rb)], (), THROWN_B))
    add_row(f"the knob landing every throw, {name}", cases, FATIGUE_MPA)
# the let-go knob on its rear stop, nothing behind it, riser F's cap picking up sled F, sled B riding on riser B's cap; and its
# mirror, the knob let go just before the return trip, on its front stop, riser B's cap picking up sled B, sled F riding
cases = []
for at in (at_cl, at_sl):
    for i in picks(pk_l, SF_l):
        Fs, Fc, T_ = at["Fs"][i], at["Fc"][i], T_l[i]
        s_ = k.C_TRIP + k.G_P - at["x1"][i]
        cases.append((s_, [(k.STEM_X0 + s_, Y_S, Fs), (f0_ + s_, y_hit, Fc), (b1_ + s_, y_hit, -T_)], (), [(b1_ + s_, y_hit, m_sled)],
                      [("F", Fc), ("stop", Fs), ("B", -T_)], [("B", m_sled)], [(k.C_COCK, "held")]))
        s_ = k.THROW - (k.C_TRIP + k.G_P) + at["x1"][i]
        cases.append((s_, [(k.STEM_X1 + s_, Y_S, -Fs), (b1_ + s_, y_hit, -Fc), (f0_ + s_, y_hit, T_)], (), [(f0_ + s_, y_hit, m_sled)],
                      [("B", -Fc), ("stop", -Fs), ("F", T_)], [("F", m_sled)], [(86 - k.C_COCK, "held")]))
add_row("a let-go knob landing on its rear stop, or on its front stop before the return trip", cases, LETGO_MPA)
# a sled landing on its riser's TPU cap, as the knocks above have it: every throw sled F meets riser F's cap with the knob
# held on its front stop; with the thumb flicked off, or the knob let go before the trip, the bar is running back with
# sled B riding on it when riser F's cap picks up sled F
for what, s_, F, lim, held in CAP_KNOCKS:
    if held:
        cs_ = (s_, [(f0_ + s_, y_hit, F), (k.STEM_X1 + s_, Y_S, -F)], (), (), [("F", F), ("stop", -F)], (), THROWN_F)
    else:
        cs_ = (s_, [(f0_ + s_, y_hit, F)], (), [(b1_ + s_, y_hit, m_sled)], [("F", F)], [("B", m_sled)], [(k.C_COCK, "held")] + THROWN_F)
    add_row(f"a sled landing on its riser's cap, {what}", [cs_], FATIGUE_MPA if held else LETGO_MPA)
for row in yaw_rows:
    res, lim = row["res"], row["lim"]
    enf = [q for q in res if q["geom"] in ENFORCED]
    w_ = max(enf, key=lambda q: q["both"])
    sg_ = max(enf, key=lambda q: q["r"][0])
    drawn_ = max(q["both"] for q in res if q["geom"] == "drawn")
    conv = all(q["r"][3] for q in res)
    row["worst"] = w_
    wc_ = max(enf, key=lambda q: q["corner"])
    print("PROBE", row["what"][:60], " | ".join(f"{g_}: {max(q['both'] for q in res if q['geom'] == g_):.2f}/"
                                                 f"{max(q['corner'] for q in res if q['geom'] == g_):.2f}" for g_ in GEOMS))
    if lim < 25:
        EVERY_THROW.append((f"the knob's bar sideways, {row['what']}", w_["both"]))
        EVERY_THROW.append((f"the knob's carriage's ends sideways, {row['what']}", wc_["corner"]))
    report(conv and w_["both"] <= lim and wc_["corner"] <= lim,
           f"{row['what']}: the knob bar bends at most {sg_['r'][0]:.1f} MPa sideways (x {sg_['r'][1]:.0f}, {sg_['geom']}); with its "
           f"bending on its lane's floor, {w_['both']:.1f} at its worst corner ({w_['geom']}; {drawn_:.1f} as drawn); where it meets the "
           f"carriage, {wc_['corner']:.1f} ({wc_['corner_at']}, {wc_['geom']}) (limit {lim:g})"
           + ("" if conv else "; a solve DID NOT CONVERGE"),
           f"{len(res)} solves: {len(res) // len(GEOMS)} cases on {len(GEOMS)} versions; the knob's carriage "
           f"{k.STEM_X1 - k.STEM_X0:.0f} long, {k.GUIDE_LEG:g} and {k.GUIDE_FOOT:g} to its rib ({CARRIAGE_PLAY:g} more each side as "
           f"printed worst); the middle and top plates where drawn, {PLATE_IN:.2f} toward the blade, {PLATE_PLAY:g} away from it and "
           f"turned about either peg; the carriage's ends as corner_fe has them, with the bending in z on each element's own section; "
           f"the thumb's line {Y_K - Y_AXIS:.2f} out from the bar's, a stop's {Y_S - Y_AXIS:.2f}")
n_bar = sum(c for _, c in BAR_SOLVES)
report(n_bar == len(BAR_SOLVES), f"every bending solve in z so far converged ({n_bar} of {len(BAR_SOLVES)})")


# the slider as the sideways solves leave it: each row's worst case on each version, bent and turned in its play as the solve
# found it, must still clear the handle (its plates where that version has them), the rail and the sleds and band where they
# are then, and the blade, both centred in its channel and on its far wall, where the latch arm presses the carrier, 0.1
# clear there. And how much of the room it was given it uses: the plain bar's RIB_Y0 - BAR_Y1 to the rib, riser F's room in
# its slot
def bent_slider(s, v, play=0.0):
    xs = YAW_XS + s
    lg, kf = k.LEG_Y1, k.KNOB_FOOT_Y0
    k.LEG_Y1, k.KNOB_FOOT_Y0 = lg - play, kf + play                  # the version's own carriage
    try:
        man = (k.knob_bar(s) + k.riser_cap("F", s) + k.riser_cap("B", s)).refine_to_length(0.5)
    finally:
        k.LEG_Y1, k.KNOB_FOOT_Y0 = lg, kf
    return man.warp_batch(lambda p_: np.column_stack([p_[:, 0], p_[:, 1] + np.interp(p_[:, 0], xs, v), p_[:, 2]]))


FAR = k.CHAN_Y - k.CAR_W / 2                          # how far the carrier can sit off its channel's middle, on its far wall
CAR_MARGIN = 0.1


def clear_of(man, s_, c, mode, dy, everything=True):
    """What the bent slider man, at knob travel s_, overlaps with the blade at c in mode, the plates dy off (or in the pose dy,
    turned): [(name, mm3)]."""
    parts, fixed = scene(c, s_, mode)
    out = []
    bl = parts["blade"]
    others = [("blade", man, bl), ("blade on its far wall, 0.1 clear", man.translate([0, -CAR_MARGIN, 0]), bl.translate([0, -FAR, 0]))]
    if everything:
        others += [(n_, man, parts[n_]) for n_ in ("sled F", "sled B", "band", "rail")]
        others += [("base plate", man, fixed["base plate"]), ("middle plate", man, place(fixed["middle plate"], dy)),
                   ("top plate", man, place(fixed["top plate"], dy))]
    for n_, a_, b_ in others:
        vol = overlap(a_, b_)
        if vol > TOL:
            out.append((n_, vol))
    return out


bad, room_bar, room_F, n_bent = [], {}, {}, 0
plain_x = lambda s_: (YAW_XS + s_ >= k.knob_slot_x()[0]) & (YAW_XS + s_ <= k.knob_slot_x()[1]) & \
    ((YAW_XS + s_ < k.STEM_X0 + s_) | (YAW_XS + s_ > k.STEM_X1 + s_)) & \
    ((YAW_XS + s_ < b0_ + s_) | (YAW_XS + s_ > b1_ + s_)) & ((YAW_XS + s_ < f0_ + s_) | (YAW_XS + s_ > f1_ + s_))
on_F = (YAW_XS >= f0_) & (YAW_XS <= f1_)
F_ROOM = k.RISER_F_SLOT_Y1 + k.RISER_F_ROOM - k.RISER_F_Y1
for row in yaw_rows:
    for g_ in GEOMS:
        q = max((q for q in row["res"] if q["geom"] == g_), key=lambda q: q["both"])
        pl_, dy_ = YAW_GEOM[g_][3], YAW_GEOM[g_][4]
        v = q["r"][7] + start_v(g_)
        s_ = q["s"]
        room_bar[g_] = min(room_bar.get(g_, 9.0), (k.RIB_Y0 - k.BAR_Y1) - float(np.max(np.where(plain_x(s_), v, -9.0))))
        room_F[g_] = min(room_F.get(g_, 9.0), float(np.min(F_ROOM + pose_dy(dy_, YAW_XS[on_F] + s_) - v[on_F])))
        man = bent_slider(s_, v, pl_)
        for c, mode in q["blade"]:
            n_bent += 1
            for n_, vol in clear_of(man, s_, c, mode, dy_):
                bad.append(f"{row['what'].split(',')[0]}, {g_}, c {c:g}: {n_} {vol:.3f}")
# with the thumb kept on the knob at an end of its travel, as the read me says, while the blade arrives there, the knob's push
# and its stop's turn the slider, and its far cam swings in over the arriving carrier: the thumb at 5, 16 and 32 N with no press
# in, the knob 0.1 into its stop, the stiffest band's pull at rest on both risers' caps; the blade over the last 20 mm of its
# throw, its overrun and its rest
T_REST = KB_TESTED * k.BAND_PRELOAD
held_bad, n_held = [], 0
for Fk in (5.0, 16.0, 32.0):
    for fwd in (True, False):
        s_ = S_STOP_F + 0.1 if fwd else S_STOP_R - 0.1
        if fwd:
            loads = [(X_THUMB_F + s_, Y_K, Fk), (k.STEM_X1 + s_, Y_S, -Fk), (f0_ + s_, y_hit, T_REST), (b1_ + s_, y_hit, -T_REST)]
            cs_ = [(c, "riding" if c < 86 else "held") for c in (66.0, 72.0, 77.0, 80.0, 82.0, 84.0, 85.0, 86.0, 87.5, 89.0)]
        else:
            loads = [(X_THUMB_R + s_, Y_K, -Fk), (k.STEM_X0 + s_, Y_S, Fk), (f0_ + s_, y_hit, T_REST), (b1_ + s_, y_hit, -T_REST)]
            cs_ = [(c, "riding" if c > 0 else "held") for c in (20.0, 14.0, 9.0, 6.0, 4.0, 2.0, 1.0, 0.0, -1.5, -3.0)]
        for g_ in GEOMS:
            r = yaw_stress(s_, loads, geom=g_)
            pl_, dy_ = YAW_GEOM[g_][3], YAW_GEOM[g_][4]
            man = bent_slider(s_, r[7] + start_v(g_), pl_)
            for c, mode in cs_:
                n_held += 1
                for n_, vol in clear_of(man, s_, c, mode, dy_, everything=False):
                    held_bad.append(f"thumb {Fk:g} N {'front' if fwd else 'rear'}, {g_}, c {c:g}: "
                                                                      f"{n_} {vol:.3f}")
            if not r[3]:
                held_bad.append(f"thumb {Fk:g} N {'front' if fwd else 'rear'}, {g_}: DID NOT CONVERGE")
report(not bad and not held_bad and min(room_bar[g_] for g_ in ENFORCED) > -0.005 and min(room_F[g_] for g_ in ENFORCED) > -0.005,
       f"bent and turned as the sideways solves leave it, the slider clears the handle, the rail, the blade (centred, and on its "
       f"far wall with {CAR_MARGIN} to spare), the sleds and the band in all {n_bent} cases, the blade where it is at each; and with the "
       f"thumb held on the knob at either end while the blade arrives (5-32 N, {n_held} cases); the plain bar stays "
       f"{min(room_bar.values()):.2f} clear of the rib at worst ({room_bar['drawn']:.2f} as drawn, of its {k.RIB_Y0 - k.BAR_Y1:.2f}), "
       f"riser F {min(room_F[g_] for g_ in ENFORCED):.2f} clear of its slot's outer wall ({room_F['drawn']:.2f} as drawn, of its "
       f"{F_ROOM:.2f}); all {len(GEOMS)} versions: the plates where drawn, {PLATE_IN:.2f} toward the blade, {PLATE_PLAY:g} away from it "
       f"and turned about either peg",
       " | ".join((bad + held_bad)[:4]))
# riser B stands in the knob's carriage, and its slot in the middle plate's floor can take some of the turn too. At its
# front, under its TPU cap, all of riser B's PLA in that slot is the top of its sole, SOLE_TOP - Z1 tall: whatever its slot
# pushes there bears on that little height (the yaw model reads the slot's walls but not the area they bear on)
SOLE_IN = k.SOLE_TOP - k.Z1
rb_rows = []
for row in yaw_rows:
    worst_ = (0.0, 0.0, "")
    for q in (q for q in row["res"] if q["geom"] in ENFORCED):
        s_, wl = q["s"], q["r"][6]
        xb0, xb1 = b0_ + s_, b1_ + s_
        front = sum(abs(w) for x, w in wl if xb1 - k.CAP_T - 0.11 - 0.01 <= x <= xb1 + 0.01)
        body = sum(abs(w) for x, w in wl if xb0 - 0.01 <= x < xb1 - k.CAP_T - 0.11 - 0.01)
        if front >= worst_[0]:
            worst_ = (front, max(worst_[1], body), q["geom"])
        else:
            worst_ = (worst_[0], max(worst_[1], body), worst_[2])
    front, body, g_ = worst_
    rb_rows.append((row["what"], front, body, front / (SOLE_IN * (k.CAP_T + 0.11)) if front > 0 else 0.0, row["lim"], g_))
w_rb = max(rb_rows, key=lambda q: q[3])
report(all(bear <= lim for _, _, _, bear, lim, _ in rb_rows),
       f"riser B in its slot: its front, where only the sole's top {SOLE_IN:.2f} is PLA in the slot, is pushed up to {w_rb[1]:.1f} N "
       f"({w_rb[0]}, {w_rb[5]}: {w_rb[3]:.1f} MPa on it, limit {w_rb[4]:g}); its body behind the cap up to "
       f"{max(q[2] for q in rb_rows):.1f} N", "; ".join(f"{what.split(',')[0]}: {fr:.1f} and {bd:.1f} N" for what, fr, bd, _, _, _ in rb_rows))
for what, fr, bd, bear, lim, _ in rb_rows:
    if lim < 25:
        EVERY_THROW.append((f"riser B's sole bearing in its slot, {what}", bear))
# the rib the carriage rides takes what turns the knob: each end of the carriage pushes it, the inner leg on its inner face
# or the knob's foot on its outer face, over the height they share. That height is read off the slider (its guide faces start
# above their set-back first layer) with the slider lifted to the middle plate, the least it can be. The rib stands on the side
# wall below, so it bends at its root across its printed layers (limit LIM_ROOT); the push spreads at 45 degrees down to the
# root. Each guide face's end is crowned in plan (k.GUIDE_CROWN, radius k.GUIDE_R), so the end bears on the flat rib as a
# rounded edge would: Hertz's line contact, p = sqrt(q E / (2 pi (1 - nu^2) R)), q the push per mm of height. And the crown
# must be big enough for the carriage's turn: the end bears where the crown's slope matches the turn, R x turn into the crown,
# which with the contact's half-width must stay inside its lead, and the turn under half the crown's end slope
RIB_T = k.HW / 2 - k.RIB_Y0
_zs = np.arange(k.BAR_Z0 + 0.01, k.RIB_TOP, 0.01)
_xm = (k.STEM_X0 + k.STEM_X1) / 2
Z_FACE = next(z for z in _zs if abs(max(b for a, b in along_y(k.knob_bar(), z, _xm) if b < k.RIB_Y0 + 0.5) - k.LEG_Y1) < 0.005)
Z_LIFT = k.Z1 - k.BAR_Z1                                       # the slider lifted to the middle plate
RIB_H = k.RIB_TOP - (Z_FACE + Z_LIFT)                          # the height the carriage meets the rib over, at the least
RIB_A = ((Z_FACE + Z_LIFT) + k.RIB_TOP) / 2 - k.LANE_Z0        # the push's middle over the rib's root, at the most
RIB_B = YAW_H + 2 * RIB_A                                      # what of the rib's length takes it at the root
E_STAR = E_PLA / (2 * (1 - NU_PLA ** 2))
hertz = lambda F_: math.sqrt((F_ / RIB_H) * E_PLA / (2 * math.pi * (1 - NU_PLA ** 2) * k.GUIDE_R))
half_w = lambda F_: math.sqrt(4 * (F_ / RIB_H) * k.GUIDE_R / (math.pi * E_STAR))
rib_rows, turns = [], []
for row in yaw_rows:
    F_r = max(q["r"][4] for q in row["res"] if q["geom"] in ENFORCED)
    rib_rows.append((row["what"], F_r, 6 * F_r * RIB_A / (RIB_B * RIB_T ** 2), hertz(F_r), row["lim"]))
    for q in (q for q in row["res"] if q["geom"] in ENFORCED):
        v, s_ = q["r"][7], q["s"]
        turn = abs(float(np.interp(k.STEM_X1 + s_, YAW_XS + s_, v) - np.interp(k.STEM_X0 + s_, YAW_XS + s_, v))) / (k.STEM_X1 - k.STEM_X0)
        turns.append((turn, k.GUIDE_R * turn + half_w(max(q["r"][4], 1e-6)), row["what"], q["geom"]))
w_rib = max(rib_rows, key=lambda q: q[1])
w_turn = max(turns)
w_into = max(turns, key=lambda q: q[1])
for what, F_r, bend, bear, lim in rib_rows:
    if lim < 25:
        EVERY_THROW.extend([(f"the carriage's rib at its root, {what}", bend),
                            (f"the carriage's crowned end bearing on its rib, {what}", bear)])
ok_rib = all(bend <= (LIM_ROOT if lim < 25 else 1.5 * LIM_ROOT) and bear <= lim for _, _, bend, bear, lim in rib_rows)
report(ok_rib, f"the carriage's rib: the hardest push on it {w_rib[1]:.1f} N ({w_rib[0]}): {w_rib[2]:.1f} MPa across its root layers "
               f"(limit {LIM_ROOT:.0f} every throw, {1.5 * LIM_ROOT:.0f} for a rare knock), {w_rib[3]:.1f} MPa where the carriage's "
               f"crowned end bears on it (limit {w_rib[4]:g}), over {RIB_H:.2f} of height; "
               + "; ".join(f"{what.split(',')[0]}: {F_r:.1f} N, {bend:.1f} and {bear:.1f}" for what, F_r, bend, bear, _ in rib_rows),
       f"the rib {RIB_T:.1f} wide and {k.RIB_TOP - k.LANE_Z0:.1f} tall; the carriage's guide faces start at z {Z_FACE:.2f}, over their "
       f"set-back first layer, and lifted {Z_LIFT:.2f} to the middle plate they meet the rib over only {RIB_H:.2f} ({k.RIB_TOP - Z_FACE:.2f} "
       f"as drawn), {RIB_A:.2f} over its root; the push spread over {RIB_B:.1f} of its length; each guide face crowned "
       f"{k.GUIDE_CROWN} over its last {k.GUIDE_LEAD:g} mm (radius {k.GUIDE_R:.0f})")
_lead_f = k.GUIDE_LEAD_FRONT - k.front_crown_trim()            # the front leg's crown left after the roof's cut-back
report(_lead_f >= k.GUIDE_LEAD, f"the inner leg's crown at the carriage's front end, {k.GUIDE_LEAD_FRONT:g} long on the same radius, keeps "
       f"{_lead_f:.2f} of it after the roof's cut-back takes the last {k.front_crown_trim():.2f} (the crowns' lead {k.GUIDE_LEAD:g})")
report(w_turn[0] <= 0.5 * k.GUIDE_LEAD / k.GUIDE_R and w_into[1] <= k.GUIDE_LEAD,
       f"the carriage's crowned ends suit its turn: it turns at most {w_turn[0] * 1000:.1f} mrad ({w_turn[2].split(',')[0]}, {w_turn[3]}), "
       f"under half the crowns' end slope ({k.GUIDE_LEAD / k.GUIDE_R * 1000:.0f} mrad), and bears at most {w_into[1]:.2f} into a crown's "
       f"{k.GUIDE_LEAD:g} mm lead (the turn times the radius, and the contact's half-width)")
# two knocks are PLA on PLA: at the far end of every throw the lug picks up the parked sled, and the
# blade bouncing back off its pad brings the latch block on to the rail's catch, before the rail rides
# into its TPU cushion. The light sled and rail take up the jump in speed, so the struck faces see
# about rho c v (the stress wave of a sudden stop, as if on a wall that does not give), not the
# blade's whole weight
RHO_C = math.sqrt(E_PLA * RHO)                       # MPa per m/s
v_pick = max(r["v"] for r in SOLID_OKS)
v_back = max(math.sqrt(2 * r["E_rebound"] / r["m_b"]) for r in oks)
report(RHO_C * v_pick <= 20 and RHO_C * v_back <= 20,
       f"PLA on PLA: the lug picks up the parked sled at up to {v_pick:.1f} m/s ({RHO_C * v_pick:.1f} MPa at the struck faces), "
       f"and the latch block meets the rail's catch at up to {v_back:.1f} m/s ({RHO_C * v_back:.1f} MPa) before the rail rides into "
       f"its cushion (limit 20)", f"rho c v: {RHO_C:.2f} MPa per m/s for PLA")
EVERY_THROW.extend([("the lug picking up the parked sled", RHO_C * v_pick), ("the block meeting the rail's catch", RHO_C * v_back)])
# the same fatigue limit as the latch arm's for every PLA part that bends on every throw: those carry a load, so their
# stress is what counts, 0.65 % of PLA's 3.0 GPa, 19.5 MPa (FATIGUE_MPA), a little under the 20 their own checks allow
w_name, w_mpa = max(EVERY_THROW, key=lambda r: r[1])
report(w_mpa <= FATIGUE_MPA and len(EVERY_THROW) == N_EVERY,
       f"fatigue: everything PLA that bends on every throw stays under {FATIGUE_MPA:.1f} MPa ({EPS_FATIGUE * 100:.2f} % at 3.0 GPa, "
       f"10,000 cycles): at most {w_mpa:.1f}, {w_name}; the latch arm, bent rather than loaded, at most "
       f"{max(st_along, st_root, kick_along, kick_root) * 100:.2f} % ({max(st_along, st_root, kick_along, kick_root) * E_PLA:.1f} MPa "
       f"at the checker's 3.5 GPa)", f"{len(EVERY_THROW)} stresses from the knocks above: wings, riser roots, the bar, the knob's "
       f"carriage's roof and lips, the guards, the rail cocked and on a normal bounce, the knob bar sideways, the carriage's rib, "
       f"the two PLA-on-PLA knocks")

print("\n== Printed screws")
N = 1200
pts_s = [(-(i / N) * k.PITCH * 2, k.thread_r((i / N * 2) % 1, k.THREAD_MIN / 2, k.THREAD_MAJ / 2)) for i in range(N + 1)]
pts_n = [(-(i / N) * k.PITCH * 2, k.thread_r((i / N * 2) % 1, k.THREAD_MIN / 2 + k.THREAD_PLAY, k.THREAD_MAJ / 2 + k.THREAD_PLAY, k.GROOVE_WIDEN))
         for i in range(N + 1)]
gap = min(math.hypot(a[0] - b[0], a[1] - b[1]) for a in pts_s[200:1000:2] for b in pts_n[::2])
report(gap >= 0.35, f"screw to nut, square to the thread: {gap:.2f} mm all round (the brain's pin rule: 0.35-0.4)")
report(all(overlap(k.screw(x, y), P3) < TOL for x, y in k.SCREWS), "each screw turns in its post's thread in the top plate")
report(overlap(SCREWS, P3.translate([0, 0, 1.0])) > 0.5 and overlap(SCREWS, (P2 + P3).translate([0, 0, 1.0])) > 0.5,
       "and holds the plates: lifted 1 mm, the top plate (alone or with the middle plate) runs into the screws",
       f"{overlap(SCREWS, P3.translate([0, 0, 1.0])):.1f} mm3 into the four screws")
P3_LOOSE = k.plate3(k.LOOSE_PLAY)
lifted_loose = overlap(SCREWS, P3_LOOSE.translate([0, 0, 1.0]))
report(all(overlap(k.screw(x, y), P3_LOOSE) < TOL for x, y in k.SCREWS) and lifted_loose > 0.5,
       f"the same with handle 3 top loose: the screws turn in its posts, and lifted 1 mm it runs {lifted_loose:.1f} mm3 into them")
report(k.BOSS_Z0 - k.Z1 >= 0.2 and overlap(P2, P3.translate([0, PLATE_SEAT, 0])) < TOL,   # seated on its pegs' flats
       f"the posts stop {k.BOSS_Z0 - k.Z1:.2f} above the base plate, so tightening pulls all three plates together")
GAUGES = [k.nut(play=pl, corners=i + 1) for i, pl in enumerate(k.FIT_PLAYS)]   # as main() makes them, at the posts' height
held = [overlap(k.screw(), n.translate([0, 0, 1.0])) for n in GAUGES]
report(overlap(k.screw(), k.nut()) < TOL and all(overlap(k.screw(), n) < TOL for n in GAUGES) and min(held) > 0.5,
       f"the fit test's three gauge nuts have the posts' thread (plays {', '.join(f'{p:.2f}' for p in k.FIT_PLAYS)}): the screw turns in "
       f"each and, lifted 1 mm, each runs {min(held):.1f} mm3 or more into it")


def corner_flats(man):
    """The flats a gauge nut's cut-off corners leave on its outline, half way up: the edges 1.5 to
    2.6 long (a whole side is 4.97, one beside a cut 4.27), once the slice's straight runs are joined."""
    p = max((np.asarray(q) for q in man.slice(k.NUT_H / 2).to_polygons()), key=lambda q: np.ptp(q[:, 0]))
    keep = []
    for i in range(len(p)):
        a, b = p[i] - p[i - 1], p[(i + 1) % len(p)] - p[i]
        if abs(a[0] * b[1] - a[1] * b[0]) > 1e-3 * np.hypot(*a) * np.hypot(*b):     # a corner, not a straight run
            keep.append(p[i])
    q = np.array(keep)
    lens = np.hypot(*(np.roll(q, -1, axis=0) - q).T)
    return lens[(lens > 1.5) & (lens < 2.6)]


flats = [corner_flats(man) for _, man in k.fit_nuts()]
nut_wall = k.NUT_AF / math.sqrt(3) - k.NUT_CUT - (k.THREAD_MAJ / 2 + max(k.FIT_PLAYS))
report([len(f) for f in flats] == [1, 2, 3] and nut_wall >= 0.8,
       f"the gauge nuts are marked by 1, 2 and 3 corners cut off ({', '.join(name for name, _ in k.fit_nuts())}), each a flat "
       f"{min(min(f) for f in flats):.2f} wide that you can see and count; {nut_wall:.2f} or more of wall is left over the thread")
eng = k.THREAD_MAJ / 2 - (k.THREAD_MIN / 2 + k.THREAD_PLAY)
engaged = k.SCREW_TIP - 0.6 - k.BOSS_Z0
report(eng >= 0.4 and engaged >= 3.3, f"threads overlap {eng:.2f} mm radially, over {engaged:.2f} mm of each post")
report(overlap(SCREWS, P1 + P2) < TOL and k.THREAD_TOP - k.SCREW_TIP >= 0.2,
       f"screws clear the base and middle plates, and their tips stop {k.THREAD_TOP - k.SCREW_TIP:.2f} short of the thread's end")
report(k.COIN_W >= 1.9 and k.COIN_D >= 0.8, f"coin slot {k.COIN_W} wide and {k.COIN_D:.2f} deep: a penny (1.52) or a quarter (1.75) fits")

print("\n== Clearances (PRINTER-BRAIN: 0.2 snug, 0.25-0.3 sliding, holes 0.35-0.4 all round)")
rows = [("carrier in its channel, sides", k.CHAN_Y - k.CAR_W / 2, 0.25), ("carrier, top and bottom", k.CAR_Z0 - k.WALL_T, 0.25),
        ("latch block in its slot", k.BLK_SLOT, 0.25), ("risers in their slots", k.BAR_Y0 - k.RISER_SLOT_Y0, 0.3),
        ("knob bar to its lane's outside wall", k.LANE_Y1 - k.BAR_Y1, 0.25),
        ("the lane's outside wall is cut back to the rib's line behind the knob's slot only from x %.1f, this far past where the "
         "latch block can be, crept and cocked, when it rests on the bar or a cam pushes it" % k.LANE_RELIEF_X0,
         k.LANE_RELIEF_X0 - (k.X_BLK + k.C_COCK + k.BLK_L), 0.5),
        ("latch block, out against the bar at the end of its play, to its path's outside wall", k.WIN_Y1 - (k.Y_OUT + k.BAR_OUT), 0.05),
        ("latch block to the channel floor and the middle plate", min(k.BLK_Z0 - k.WALL_T, k.Z1 - k.BLK_Z1), 0.2),
        ("knob bar, under and over", min(k.BAR_Z0 - k.LANE_Z0, k.Z1 - k.BAR_Z1), 0.2),
        ("knob bar over the rail", k.BAR_Z0 - k.RAIL_TOP, 0.3), ("knob bar over the cushions", k.BAR_Z0 - k.CUSH_TOP, 0.4),
        ("cams past the carrier's cut-back side, bar pushed in all the way", k.Y_CAM - k.CAR_CUT_Y - (k.BAR_Y0 - k.RISER_SLOT_Y0), 0.1),
        ("and ahead of the block's slot, where the carrier is cut back further (a cam swings in over it when the thumb is held on "
         "the knob at an end: the sideways check proves it clear)", k.Y_CAM - k.CAR_CUT_Y2 - (k.BAR_Y0 - k.RISER_SLOT_Y0), 0.4),
        ("that deeper cut starts at the block slot's front wall, not inside the slot (behind it the slot's walls keep 10.6)",
         k.CAR_CUT_X2 - (k.BLK_X0 + k.BLK_L + k.BLK_SLOT), 0.0),
        ("knob to the handle's side, above the base plate (a middle or top plate set a little off can't pinch it)", k.KNOB_Y0 - k.HW / 2, 0.5),
        ("the carriage's roof over its rib, as drawn", k.ROOF_Z0 - k.RIB_TOP, 0.2),
        ("and with the bar resting on its floor (the roof may then rest on the rib's top under the slider's own weight, which is "
         "harmless)", k.ROOF_Z0 - k.RIB_TOP - (k.BAR_Z0 - k.LANE_Z0), 0.0),
        ("the plain bar to the rib (room to follow the carriage's turn; the sideways check finds what it needs)", k.RIB_Y0 - k.BAR_Y1, 0.45),
        ("the middle plate's ledge over the bar, beside riser F's wider slot (with the middle plate as far off across as its pegs let "
         "it, 0.2 or more still left)", k.BAR_Y1 - (k.RISER_F_SLOT_Y1 + k.RISER_F_ROOM), PLATE_PLAY + 0.2),
        ("and beside riser B's slot, 0.1 wider outward too", k.BAR_Y1 - (k.RISER_SLOT_Y1 + k.RISER_B_ROOM), PLATE_PLAY + 0.2),
        ("sleds in the band level, sides", min(-k.SLED_HW - k.CAV_Y0, k.CAV_Y1 - k.RISER_Y1), 0.25),
        ("lug in its floor slot", 0.7, 0.4), ("band in the lug's slot (strong band)", k.BAND_SLOT - k.BAND_STRONG[1] / 2, 0.3),
        ("band eye on its post", k.EYE_PLAY, 0.35), ("screw holes", (k.SCREW_HOLE - k.THREAD_MAJ) / 2, 0.35),
        ("screw head in its counterbore", (k.COUNTERBORE - k.HEAD_D) / 2, 0.35),
        ("rail cushions to the spine's ends", 0.1, 0.1), ("rail spine in its groove", k.SPINE_Y0 - k.GROOVE_Y0, 0.25),
        ("top plate's round posts in the middle plate's round pockets, all round (a peg in a hole)",
         (k.POST_POCKET_D - k.BOSS_D) / 2, 0.35),
        ("top plate's posts, wall over the thread's groove (the loose lid's)", k.BOSS_D / 2 - (k.THREAD_MAJ / 2 + k.LOOSE_PLAY), 0.8),
        ("web between the risers' slots in the middle plate's floor",
         k.riser_sweep(*k.riser_x()[1])[0] - k.riser_sweep(*k.riser_x()[0])[1], 1.2),
        ("the knob meets its stops this far past each end of its travel (and 0.1 before its sled meets its pad)",
         min(k.STEM_X0 - k.stop_face_x()[0], k.stop_face_x()[1] - (k.STEM_X1 + k.THROW)), 0.15),
        ("with a stop left out, the carriage meets its slot's end this far past a stop squashed as far as the checks drive it",
         k.KNOB_ROOM - k.KNOB_SOFT - k.STOP_SQ, 0.3),
        ("and then the lane's ends run on past the bar's ends", min(k.bar_x(-k.KNOB_ROOM)[0] - k.lane_x()[0],
                                                                     k.lane_x()[1] - k.bar_x(k.THROW + k.KNOB_ROOM)[1]), 0.25),
        ("and the risers' slots past the risers", min(min(r0 - k.KNOB_ROOM - k.riser_sweep(r0, r1)[0],
                                                         k.riser_sweep(r0, r1)[1] - (r1 + k.THROW + k.KNOB_ROOM)) for r0, r1 in k.riser_x()), 0.25),
        ("and the knob is still clear of its guards' faces", min(k.STEM_X0 - k.KNOB_ROOM - k.guard_face_x()[0],
                                                               k.guard_face_x()[1] - (k.STEM_X1 + k.THROW + k.KNOB_ROOM)), 0.5),
        ("knob stops off the handle's side", k.STOP_Y0 - k.HW / 2, 0.1),
        ("knob stops' faces recessed past the most they may squash (it must stay over STOP_SQ + 0.2)", k.STOP_RECESS - k.STOP_SQ, 0.2),
        ("knob stops under the knob's top and inside its lips' outer face", min(k.KNOB_TOP - (k.STOP_Z0 + k.STOP_H), k.LIP_Y1 - k.STOP_Y1), 0.2),
        ("knob stops' T over the slot's floor and under the middle plate", k.Z1 - (k.STOP_Z0 + k.T_H), 0.15),
        ("web from the lane's back end to its screw hole", k.lane_x()[0] - (k.SCREWS[0][0] + k.SCREW_HOLE / 2), 0.8),
        ("web from the lane's front end to its screw hole", (k.SCREWS[2][0] - k.SCREW_HOLE / 2) - k.lane_x()[1], 0.8)]
for what, v, need in rows:
    report(v >= need - 1e-9, f"{what}: {v:.2f}", f"needs {need:g}")
# the pegs in their D-shaped holes, read off the plates layer by layer (peg_play): the brain's 0.35 all round is for the hole's
# round part; its flat is a locating face, drawn into the peg; and across, what is left for a hole printing small
_round = (k.PEG_HOLE_D - k.PEG_D) / 2
_flat = max(PLAY_MB[0], PLAY_TM[0])
_travel = min(PLAY_MB[0] + PLAY_MB[1], PLAY_TM[0] + PLAY_TM[1])
report(_round >= 0.35 - 1e-9 and min(PLAY_MB[1], PLAY_TM[1]) >= 0.35 - 0.06 and _flat <= 0.0 and _travel > 0.0,
       f"pegs in their D-shaped holes: the round part {_round:.2f} all round (needs 0.35, the brain's rule for a peg in a hole; "
       f"{min(PLAY_MB[1], PLAY_TM[1]):.2f} as printed); the flat {_flat:+.2f}, drawn into its peg by design, a locating face; across, "
       f"{_travel:.2f} of travel is left for a hole printing small before a plate will not go on",
       "the peg test on the fit plate shows it first")



# the carriage on its rib, read off the parts themselves: each guide face's room to the rib, on the first layer (set back
# FOOT, as it spreads about 0.1 on the bed) and above it, all along the carriage between its crowned ends; for the knife's
# slider and the fit test's carriage piece
cg_bad, cg = [], {}
for nm, man in (("slider", k.knob_bar()), ("carriage piece", k.carriage_test())):
    lo_ = k.TEST_X0 if nm != "slider" else k.STEM_X0
    hi_ = k.TEST_X1 if nm != "slider" else k.STEM_X1
    for x in np.arange(lo_ + k.GUIDE_LEAD + 1.0, hi_ - k.GUIDE_LEAD - 0.9, 2.0):
        gg = []
        for zz in (k.BAR_Z0 + 0.1, k.BAR_Z0 + 0.35, k.RIB_TOP - 0.1):
            pieces = along_y(man, zz, x)
            leg = max(b for a, b in pieces if b < k.RIB_Y0 + 0.5)
            foot = min(a for a, b in pieces if a > k.RIB_Y0)
            gg.append((k.RIB_Y0 - leg, foot - k.HW / 2))
        (f_in, f_out), (a_in, a_out), (t_in, t_out) = gg
        cg.setdefault(nm, []).append((f_in, f_out, min(a_in, t_in), min(a_out, t_out), max(a_in, t_in), max(a_out, t_out)))
        if (min(a_in + a_out, t_in + t_out) < 2 * 0.25 - 1e-6 or f_in < max(a_in, t_in) + 0.1 - 1e-6 or
                f_out < max(a_out, t_out) + 0.1 - 1e-6 or max(a_in, t_in) > k.BAR_OUT - 0.1 + 1e-6 or
                min(a_out, t_out) < k.BAR_IN - 1e-6):
            cg_bad.append(f"{nm} x {x:.0f}: first layer {f_in:.2f}/{f_out:.2f}, above {a_in:.2f}/{a_out:.2f} and {t_in:.2f}/{t_out:.2f}")
_all = [r_ for v_ in cg.values() for r_ in v_]
report(not cg_bad, "the knob's carriage on its rib, read off the slider and the fit test's carriage piece: its leg "
                   f"{min(r_[2] for r_ in _all):.2f} from the rib's inner face and the knob's foot {min(r_[3] for r_ in _all):.2f} from its "
                   f"outer face, {min(r_[2] + r_[3] for r_ in _all):.2f} of play across it in all (the brain's sliding fit, 0.25 a side: "
                   f"needs 0.5); drawn off the middle so the carriage's leg stops it going out {k.BAR_OUT - max(r_[4] for r_ in _all):.2f} "
                   f"before the bar reaches its lane's wall at a cam (needs 0.1), and the foot no nearer than riser B's {k.BAR_IN:g} going in; "
                   f"on the first layer each side set back {min(min(r_[0] - r_[4], r_[1] - r_[5]) for r_ in _all):.2f} further (it spreads "
                   f"about 0.1: needs 0.1)", "; ".join(cg_bad[:4]))
# the rib itself, read off the base plate: 1.4 wide at its inner face RIB_Y0, unbroken under the carriage wherever the carriage
# can be, from its back end with a stop left out to its front end with a stop left out
rib_lo, rib_hi = k.STEM_X0 - k.KNOB_ROOM, k.STEM_X1 + k.THROW + k.KNOB_ROOM
z_rib = (k.LANE_Z0 + k.RIB_TOP) / 2
ribx = []
for x in np.arange(rib_lo, rib_hi + 1e-9, 0.5):
    pc = [(a, b) for a, b in along_y(P1, z_rib, x) if a <= (k.RIB_Y0 + k.HW / 2) / 2 <= b]
    ribx.append(pc[0] if pc else (9.0, 9.0))
rib_ok = all(abs(a - k.RIB_Y0) < 0.01 and abs(b - a - 1.4) < 0.01 for a, b in ribx)
report(rib_ok, f"the rib the carriage rides, read off the base plate: 1.4 wide from y {k.RIB_Y0:g}, unbroken from x {rib_lo:.1f} to "
               f"{rib_hi:.1f}, wherever the carriage can be (a stop left out at either end)",
       "; ".join(f"x {rib_lo + 0.5 * i:.1f}: {a:.2f}-{b:.2f}" for i, (a, b) in enumerate(ribx) if not (abs(a - k.RIB_Y0) < 0.01 and
                                                                                                  abs(b - a - 1.4) < 0.01))[:300])
# the fit test's carriage piece on its rib piece, both where they are cut from: the same play as the knife's, each side and
# over the rib, resting on the floor as on a table
CT, RT = k.carriage_test(), k.rib_test()
side_ok = [overlap(CT.translate([0, sg * (g_ - 0.01), 0]), RT) <= TOL and overlap(CT.translate([0, sg * (g_ + 0.05), 0]), RT) > TOL
           for sg, g_ in ((-1, k.GUIDE_FOOT), (1, k.GUIDE_LEG))]
rest_ok = overlap(CT.translate([0, 0, -(k.BAR_Z0 - k.LANE_Z0) + 0.01]), RT) <= TOL
report(all(side_ok) and rest_ok and overlap(CT, RT) <= TOL,
       f"fit test: the carriage piece drops over the rib piece and slides along it with {k.GUIDE_LEG + k.GUIDE_FOOT:.2f} of play across "
       f"it, as the knife's carriage on its rib; resting on the floor its roof is {k.ROOF_Z0 - k.RIB_TOP - (k.BAR_Z0 - k.LANE_Z0):.2f} "
       f"over the rib", f"the carriage piece cut from the knife's slider and the rib from its base plate, {k.TEST_X1 - k.TEST_X0:g} long, "
       f"both ends of the piece crowned and its first layer set back as the slider's")
# the fit test's peg pieces, both where they are cut from: the lid on its base as the middle plate on the base plate's peg.
# Pressed on it sits PLATE_SEAT toward the knob side, clear of the peg; that way it slides as far as the knife's plates can, the
# other way not at all
PT_B, PT_L = k.peg_test_base(), k.peg_test_lid()
_trav = min(PLAY_MB[0] + PLAY_MB[1], PLAY_TM[0] + PLAY_TM[1])
pt_ok = [overlap(PT_L.translate([0, PLATE_SEAT + 0.001, 0]), PT_B) <= TOL,
         overlap(PT_L.translate([0, PLATE_SEAT + _trav - 0.02, 0]), PT_B) <= TOL,
         overlap(PT_L.translate([0, PLATE_SEAT + _trav + 0.05, 0]), PT_B) > TOL,
         overlap(PT_L.translate([0, PLATE_SEAT - 0.1, 0]), PT_B) > TOL]
report(all(pt_ok), f"fit test: the peg test's lid goes on its base as the middle plate goes on the base plate's peg: pressed on it "
                   f"sits {PLATE_SEAT:.2f} toward the knob side, clear of the peg, slides on {_trav:.2f} that way and not at all the "
                   f"other way (cut corner to cut corner)", f"both pieces cut from the plates themselves; {pt_ok}")


def edge_dist(p, c):
    """Distance from the point c to the closed polygon p's edges."""
    a, ab = p, np.roll(p, -1, axis=0) - p
    t = np.clip(((c - a) * ab).sum(1) / np.maximum((ab * ab).sum(1), 1e-12), 0.0, 1.0)
    return float(np.hypot(*(a + ab * t[:, None] - c).T).min())


def pocket_walls():
    """The thinnest wall round the middle plate's four post pockets on any layer, read off the
    plate's own slices: to the handle's outline, to the peg holes, and to everything else (the band
    level's cavity and pad pockets, the floor's slots). A pocket is round, so its wall to an edge is
    that edge's distance from the screw's centre less the pocket's radius."""
    r = k.POST_POCKET_D / 2
    worst = {"the handle's outline": 99.0, "the band level": 99.0, "the peg holes": 99.0}
    for i in range(int(round((k.Z2 - k.Z1) / 0.2))):
        polys = [np.asarray(p) for p in P2.slice(k.Z1 + 0.1 + 0.2 * i).to_polygons()]
        outer = max(range(len(polys)), key=lambda j: np.ptp(polys[j][:, 0]))      # as long as the handle
        for x, y in k.SCREWS:
            c = np.array([x, y])
            for j, p in enumerate(polys):
                if np.hypot(*(p - c).T).max() < r + 0.05:
                    continue                                                       # the pocket itself
                if j == outer:
                    key = "the handle's outline"
                elif min(math.hypot(*(p.mean(0) - np.array(q))) for q in k.PEGS) < 2.5:
                    key = "the peg holes"
                else:
                    key = "the band level"
                worst[key] = min(worst[key], edge_dist(p, c) - r)
    return worst


PW = pocket_walls()
report(min(PW.values()) >= 0.8, "the middle plate's round post pockets leave, on every layer, "
       + ", ".join(f"{v:.2f} to {key}" for key, v in PW.items()), "two lines: 0.8")
grips = [overlap(STOP_R, P1), overlap(STOP_F, P1)]
want = 2 * k.T_GRIP * k.T_HEAD_L * k.T_H
caught = [overlap(STOP_R.translate([0.3, 0, 0]), P1), overlap(STOP_F.translate([-0.3, 0, 0]), P1)]
report(all(abs(g - want) < 0.02 for g in grips) and overlap(STOP_R + STOP_F, P2 + P3) < TOL and min(caught) > 2 * want,
       f"each knob stop's T presses {k.T_GRIP} a side into its slot in the base plate's guard ({grips[0]:.2f} and {grips[1]:.2f} mm3 of "
       f"grip), and pulled 0.3 toward the knob its head runs into the slot's shoulders ({min(caught):.2f} mm3): it can't come out "
       f"with the middle plate on")
t_leg = (w_r - (k.TONGUE_W - 2 * k.CAP_GRIP)) / 2            # each leg of a cap, beside its tongue ...
h_leg = k.CAP_TOP - k.SLED_Z0                                # ... standing on the foot
grip = lambda E: 2 * 3 * E * (h_leg * t_leg ** 3 / 12) / k.TONGUE_L ** 3 * k.CAP_GRIP * 0.6   # the legs bent, TPU on PLA 0.6
report(grip(20.0) >= 0.04 and t_leg >= 0.8,
       f"each riser cap's legs ({t_leg:.2f} thick) press its tongue {k.CAP_GRIP} a side: {grip(20.0):.2f} N of grip in a normal TPU, "
       f"{grip(10.0):.2f} N in a very soft one; nothing rubs it on the way (the latched block passes it clear)")

print("\n== Printing")
pp = k.print_parts()
pp["latch test"] = k.on_bed(k.latch_test())
pp.update(k.fit_nuts())                     # the three gauge nuts, as the fit test prints them


def flat_heights(man):
    mesh = man.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    t = np.asarray(mesh.tri_verts)
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    n = np.cross(b - a, c - a)
    ln = np.linalg.norm(n, axis=1)
    flat = (np.abs(n[:, 2]) > 0.99999 * ln) & (ln > 1e-9)
    return sorted(set(np.round(a[flat, 2], 4)))


bad, count = [], 0
for name, man in pp.items():
    for z in flat_heights(man):
        count += 1
        nn = (z - 0.05) / 0.2
        if z > 1e-6 and (abs(nn - round(nn)) > 1e-3 or nn < 0.99):
            bad.append(f"{name} {z:.3f}")
report(not bad, f"every flat face of every part, as it prints, sits on a layer line ({count} heights)", ", ".join(bad[:12]))


def width(cs):
    """About how wide a thin piece is: 2 x area / perimeter."""
    per = 0.0
    for poly in cs.to_polygons():
        for i in range(len(poly)):
            (x0, y0), (x1, y1) = poly[i - 1], poly[i]
            per += math.hypot(x1 - x0, y1 - y0)
    return 2 * cs.area() / per if per else 0.0


def overhangs(man, reach=0.35):
    """For each layer: what no layer below holds within `reach` mm, as (z, area, widest piece)."""
    bb = man.bounding_box()
    out, prev = [], None
    z = bb[2] + 0.15
    while z < bb[5]:
        cs = man.slice(z)
        if prev is not None and cs.area() > 0:
            hang = cs - prev.offset(reach, m3.JoinType.Square)
            if hang.area() > 0.02:
                out.append((z - bb[2], hang.area(), max(width(p) for p in hang.decompose())))
        prev = cs
        z += 0.2
    return out


EXPECT_BRIDGE = {"handle 1 base": "the screw counterbores' ceilings, which Flash Studio is set to bridge",
                 "handle 2 middle": "the peg holes' ceilings", "peg test lid": "the peg hole's ceiling",
                 "screw": "the coin slot's ceiling"}
for name, man in pp.items():
    oh = overhangs(man)
    limit = 2.0 if name in EXPECT_BRIDGE else 1.6
    ok = all(w <= limit for _, _, w in oh)
    note = EXPECT_BRIDGE.get(name, "")
    msg = f"{name}: nothing hangs in the air" + (f" except short bridges up to {max(w for *_, w in oh):.1f} mm" if oh else "") + (f" ({note})" if note else "")
    report(ok, msg, "; ".join(f"z {z:.2f}: {a:.1f} mm2, {w:.1f} wide" for z, a, w in oh[:6]) if not ok else "")


def thin_pieces(cs, r, min_w=0.15, min_a=0.05):
    """Pieces of cs narrower than 2 r: what an opening of radius r takes away, leaving out the
    slivers it shaves off ordinary corners."""
    if cs.area() <= 0:
        return []
    opened = cs.offset(-r, m3.JoinType.Round, 2.0, 24).offset(r, m3.JoinType.Round, 2.0, 24)
    out = []
    for p in (cs - opened).decompose():
        a, w = p.area(), width(p)
        if a > min_a and w > min_w:
            bb = p.bounds()
            out.append((a, w, bb))
    return out


def walls(man, r=0.39):
    bb = man.bounding_box()
    found = []
    z = bb[2] + 0.15
    while z < bb[5]:
        for a, w, b in thin_pieces(man.slice(z), r):
            found.append(f"z {z - bb[2]:.2f} at x {(b[0] + b[2]) / 2:.1f} y {(b[1] + b[3]) / 2:.1f} ({w:.2f})")
        z += 0.2
    return found


for name in ("handle 1 base", "handle 2 middle", "handle 3 top", "handle 3 top loose", "blade", "sled F", "rail", "knob slider",
             "riser cap", "knob stop rear", "knob stop front", *(name for name, _ in k.fit_nuts())):
    found = walls(pp[name])
    report(not found, f"{name}: no wall thinner than two lines (0.8) on any layer", "; ".join(found[:5]))


def gaps(man, r=0.22):
    bb = man.bounding_box()
    found = []
    z = bb[2] + 0.15
    while z < bb[5]:
        cs = man.slice(z)
        b = cs.bounds()
        outer = m3.CrossSection.square([b[2] - b[0] + 2, b[3] - b[1] + 2]).translate([b[0] - 1, b[1] - 1])
        for a, w, bx in thin_pieces(outer - cs, r, 0.1, 0.03):
            found.append(f"z {z - bb[2]:.2f} at x {(bx[0] + bx[2]) / 2:.1f} y {(bx[1] + bx[3]) / 2:.1f} ({w:.2f})")
        z += 0.2
    return found


for name in ("blade", "latch test"):
    found = gaps(pp[name])
    report(not found, f"{name}: no gap inside it under 0.45 (the arm's gaps are 0.5), so no strand can weld the arm", "; ".join(found[:5]))

def x_width_at(cs, y, x_mid):
    """Width in x, along the line y, of the piece of cs that covers x_mid."""
    strip = m3.CrossSection.square([400, 0.1]).translate([-100, y - 0.05])
    for p in (cs ^ strip).decompose():
        b = p.bounds()
        if b[0] <= x_mid <= b[2]:
            return b[2] - b[0]
    return 0.0


z_first = k.CAR_Z0 + 0.1
x_mid = k.X_BLK + k.BLK_L / 2
car_cs = k.carrier().slice(z_first)
room = m3.CrossSection.square([80, 30]).translate([0, -15]) - car_cs
fl_gap = (x_width_at(room, 9.5, x_mid) - x_width_at(k.latch_block().slice(z_first), 9.5, x_mid)) / 2
report(fl_gap >= k.BLK_SLOT + 0.1, f"the block prints on its inner face and its slot's first layer is set back: {fl_gap:.2f} play each side "
                                    f"at the carrier's first layer (it spreads about 0.1 on the bed), {k.BLK_SLOT} above")

print("\n== Project files (read back from the three .3mf files make_knife.py wrote)")
PROJECTS = k.projects(pp)
NS3 = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
BED, STRIDE = 220.0, 220.0 * 1.2               # the AD5X's plate, and Flash Studio's plates laid out 20 % of a plate apart


def plate_origin(i, n):
    """Where Flash Studio puts plate i of n (BambuStudio's PartPlateList): round(sqrt n) columns,
    one more if sqrt n is above that, the first row at the top and the rows going down."""
    root = math.sqrt(n)
    cols = int(round(root)) + (1 if root > round(root) else 0)
    return (i % cols) * STRIDE, -(i // cols) * STRIDE


def read_3mf(name):
    """A project file as Flash Studio reads it: its version tags, its project settings, and its
    plates in order, each [(object name, the object's own settings, lowest and highest corner on the
    build plate, its turn, its modifier parts [(their settings, lowest and highest corner)])]."""
    with zipfile.ZipFile(os.path.join(k.HERE, name)) as z:
        model = ET.fromstring(z.read("3D/3dmodel.model"))
        cfg = ET.fromstring(z.read("Metadata/model_settings.config"))
        settings = json.loads(z.read("Metadata/project_settings.config"))
    tags = {m.get("name"): m.text for m in model.findall(NS3 + "metadata")}
    meshes, comps = {}, {}
    for obj in model.find(NS3 + "resources"):
        mesh, comp = obj.find(NS3 + "mesh"), obj.find(NS3 + "components")
        if mesh is not None:
            v = np.array([[float(e.get(a)) for a in "xyz"] for e in mesh.find(NS3 + "vertices")])
            meshes[obj.get("id")] = (v.min(0), v.max(0))
        if comp is not None:
            comps[obj.get("id")] = comp[0].get("objectid")
    build = {it.get("objectid"): [float(a) for a in it.get("transform").split()] for it in model.find(NS3 + "build")}
    own = {o.get("id"): {m.get("key"): m.get("value") for m in o.findall("metadata")} for o in cfg.findall("object")}
    mods = {o.get("id"): [({m.get("key"): m.get("value") for m in pt.findall("metadata")}, pt.get("id"))
                          for pt in o.findall("part") if pt.get("subtype") == "modifier_part"] for o in cfg.findall("object")}
    plates = []
    for pl in cfg.findall("plate"):
        md = {m.get("key"): m.get("value") for m in pl.findall("metadata")}
        objs = []
        for mi in pl.findall("model_instance"):
            oid = {m.get("key"): m.get("value") for m in mi.findall("metadata")}["object_id"]
            lo, hi = meshes[comps[oid]]
            t = np.array(build[oid])
            objs.append((own[oid]["name"], own[oid], lo + t[9:12], hi + t[9:12], t[:9],
                         [(md_, meshes[pid][0] + t[9:12], meshes[pid][1] + t[9:12]) for md_, pid in mods[oid]]))
        plates.append((md["plater_name"], objs))
    return tags, settings, plates


def brim(own):
    return float(own.get("brim_width", 0)) if own.get("brim_type") == "outer_only" else 0.0


TPU_FILE = PROJECTS[-1][0]
MODS_READ = []                              # (file, object, the modifier's settings, its corners from the object's lowest)
for fname, want, _ in PROJECTS:
    tags, settings, plates = read_3mf(fname)
    bad = []
    if (tags.get("Application"), tags.get("OrcaSlicer")) != ("BambuStudio-02.06.00.51", "2.4.2"):
        bad.append(f"version tags {tags}")
    if settings.get("printer_settings_id") != "Flashforge AD5X 0.4 nozzle" or "wall_generator" not in settings["different_settings_to_system"][0]:
        bad.append("project settings")
    if [p for p, _ in plates] != [p for p, _ in want]:
        bad.append(f"plates {[p for p, _ in plates]}")
    edge, apart, n_obj = 99.0, 99.0, 0
    for i, ((pname, objs), (_, items)) in enumerate(zip(plates, want)):
        ox, oy = plate_origin(i, len(want))
        if [o[0] for o in objs] != [it[0] for it in items]:
            bad.append(f"{pname}: objects {[o[0] for o in objs]}")
            continue
        foot = []
        for (name, own, lo, hi, turn, md), (_, man_, filament, _, *mine) in zip(objs, items):
            n_obj += 1
            mine = dict(mine[0]) if mine else {}
            want_mods = mine.pop("modifier", [])
            if len(md) != len(want_mods):
                bad.append(f"{name}: {len(md)} modifiers")
            for (st, mlo, mhi), (mname, mman, mset) in zip(md, want_mods):
                if st != {"name": mname, **mset}:
                    bad.append(f"{name}: modifier {st}")
                MODS_READ.append((fname, name, st, mlo - lo, mhi - lo, man_))
            if own != {"name": name, "extruder": str(filament), **mine}:
                bad.append(f"{name}: settings {own}")
            if abs(lo[2]) > 1e-3 or not np.allclose(turn, [1, 0, 0, 0, 1, 0, 0, 0, 1]):
                bad.append(f"{name}: not lying on the plate as made")
            fp = (lo[0] - ox, lo[1] - oy, hi[0] - ox, hi[1] - oy)
            e = min(fp[0], fp[1], BED - fp[2], BED - fp[3]) - brim(own)
            edge = min(edge, e)
            if e < 1.0:
                bad.append(f"{name}: {e:.1f} from plate {i + 1}'s edge")
            for other, ob in foot:
                g = math.hypot(max(fp[0] - other[2], other[0] - fp[2], 0.0), max(fp[1] - other[3], other[1] - fp[3], 0.0))
                need = 2.0 + max(brim(own), ob)
                apart = min(apart, g - max(brim(own), ob))
                if g < need:
                    bad.append(f"{name}: {g:.1f} from the next part on plate {i + 1} (needs {need:g})")
            foot.append((fp, brim(own)))
    report(not bad, f"{fname}: {len(plates)} plates where Flash Studio puts {len(want)} ({'; '.join(p for p, _ in plates)}), "
                    f"{n_obj} objects, each wholly on its own plate's {BED:.0f} mm bed, at least {edge:.1f} in from its edge and "
                    f"{apart:.1f} from the next part, past any brim; filaments and own settings as make_knife.py sets them",
           "; ".join(bad[:6]) if bad else "version tags and the AD5X project settings are there; parts 2 apart, 7 round a 5 mm brim")
    if fname == TPU_FILE:
        solid = [o[0] for _, objs in plates for o in objs if o[1].get("sparse_infill_density") == "100%"]
        report(settings["filament_type"][0] == "TPU" and len(solid) == n_obj,
               f"{fname}: filament 1 is {settings['filament_settings_id'][0]}, and all {len(solid)} TPU parts print solid "
               f"(sparse infill 100 %), as the checker models them")
    if fname == PROJECTS[0][0]:
        keys = ("outer_wall_speed", "inner_wall_speed", "internal_solid_infill_speed", "top_surface_speed", "gap_infill_speed")
        sp = {o[0]: [float(o[1].get(key, 999)) for key in keys] for _, objs in plates for o in objs}
        screws = [v for name, v in sp.items() if name.startswith("screw")]
        nuts = [v for name, v in sp.items() if name.startswith("nut")]
        report(len(screws) == 4 and len(nuts) == 3 and max(max(v) for v in screws + nuts) <= 60 and all(v[:2] == [40, 40] for v in nuts),
               f"{fname}: the printed screws print at {max(max(v) for v in screws):.0f} mm/s or slower (walls, solid infill, top and gaps), "
               f"as the brain's strong PLA says, and the gauge nuts' walls at {max(v[0] for v in nuts):.0f}, as the top plate's posts")

# what the read me says to print, typed in here (not read from make_knife): each file's plates, and on each the parts, by
# the start of their names, and how many
BOM = {"1 fit test.3mf": [{"screw": 4, "nut": 3, "rib test": 1, "peg test base": 1, "peg test lid": 1}, {"latch test": 1, "latch block": 1, "carriage test": 1}],
       "2 knife plates.3mf": [{"handle 1 base": 1, "handle 2 middle": 1, "handle 3 top": 1}, {"sled F": 1, "sled B": 1, "rail": 1},
                              {"blade": 1, "latch block": 1}, {"knob slider": 1}],
       "3 TPU parts.3mf": [{"band": 3, "pad": 2, "rail cushion": 2, "riser cap": 2, "knob stop rear": 1, "knob stop front": 1},
                           {"band strong": 3}, {"band soft": 3}]}
bom_bad = []
for fname, want, _ in PROJECTS:
    _, _, plates = read_3mf(fname)
    if len(plates) != len(BOM[fname]):
        bom_bad.append(f"{fname}: {len(plates)} plates")
        continue
    for (pname, objs), parts in zip(plates, BOM[fname]):
        names = [o[0] for o in objs]
        used = set()
        for pre_, n_ in parts.items():
            hits = [nm for nm in names if nm.startswith(pre_) and not any(nm.startswith(q) for q in parts if q != pre_
                                                                          and q.startswith(pre_))]
            used |= set(hits)
            if len(hits) != n_:
                bom_bad.append(f"{fname}, {pname}: {len(hits)} {pre_}")
        if set(names) - used:
            bom_bad.append(f"{fname}, {pname}: also {sorted(set(names) - used)}")
report(not bom_bad, "the three project files hold what the read me says to print: " + "; ".join(
    f"{fname} " + " / ".join(", ".join(f"{n_} {pre_}" for pre_, n_ in parts.items()) for parts in plates_)
    for fname, plates_ in BOM.items()), "; ".join(bom_bad))


def first_islands(man):
    """The first layer of a part lying on the bed, each island filled in (an outer-only brim skips holes)."""
    out = []
    for isl in man.slice(0.125).decompose():
        polys = isl.to_polygons()
        outer = max(polys, key=lambda q: abs(m3.CrossSection([q]).area()))
        cs = m3.CrossSection([outer])
        out.append(cs if cs.area() > 0 else m3.CrossSection([list(reversed(outer))]))
    return out


# a brim round each island of a part's first layer, as an outer-only brim is laid: it fills the gap between two islands of
# one part. Any brim under the part's own layers above (its shadow on the bed), in a strip wider than 1 mm, is a strip that
# has to be pulled out from under the part (a 0.4 band under a chamfered edge is fine). And the knob slider and the fit
# test's carriage piece, whose first layers are two islands either side of the rib's groove, must print with no brim at all
brim_bad, brim_n, no_brim = [], 0, {}
for fname, want, settings in PROJECTS:
    st_ = json.loads(settings)
    gap_ = float(st_.get("brim_object_gap", 0.1))
    for pname, items in want:
        for name, man_, filament, _, *own in items:
            own = dict(own[0]) if own else {}
            bt = own.get("brim_type", st_.get("brim_type", "auto_brim"))
            if name in ("knob slider", "carriage test"):
                no_brim[name] = (bt == "no_brim", len(first_islands(man_)))
            if bt != "outer_only":
                continue
            w_ = float(own.get("brim_width", st_.get("brim_width", 5)))
            isl = first_islands(man_)
            brim_ = m3.CrossSection.batch_boolean([c.offset(gap_ + w_, m3.JoinType.Round, 2.0, 16) for c in isl], m3.OpType.Add) - \
                m3.CrossSection.batch_boolean([c.offset(gap_, m3.JoinType.Round, 2.0, 16) for c in isl], m3.OpType.Add)
            bb_ = man_.bounding_box()
            shadow = (man_ ^ k.box(bb_[0] - 1, bb_[3] + 1, bb_[1] - 1, bb_[4] + 1, 0.3, bb_[5] + 1)).project()
            under = (brim_ ^ shadow).offset(-0.5, m3.JoinType.Square)
            brim_n += 1
            if under.area() > 0.01:
                brim_bad.append(f"{name} ({fname}): {(brim_ ^ shadow).area():.0f} mm2 of brim under it, in islands {len(isl)}")
report(not brim_bad and len(no_brim) == 2 and all(v[0] and v[1] == 2 for v in no_brim.values()),
       f"no part's brim lies under the part itself in a strip wider than 1 mm ({brim_n} parts with a 5 mm brim); the knob slider "
       f"and the fit test's carriage piece, whose first layers are {' and '.join(str(v[1]) for v in no_brim.values())} islands with "
       f"the rib's groove between them under the roof, print with no brim", "; ".join(brim_bad) + f" {no_brim}")

# the knob's carriage prints its roof as a 1.9 bridge over the rib's channel, 38 mm long: Flash Studio can lay a bridge the
# long way (PRINTER-BRAIN), so the slider and the fit test's carriage piece each carry a modifier over the roof's first
# layer that sets the bridge's direction straight across (a real angle: 0 means "pick it yourself"). Read back, each must
# cover the roof's whole bridge on its first layer, where it is (the first layer's overhang, read off the part as it lies on
# the bed), and nothing of the roof's second layer
roof_ok, roof_txt = [], []
for fname, name, st, mlo, mhi, man_ in MODS_READ:
    roof_z = k.ROOF_Z0 - k.BAR_Z0                       # the roof's underside over the bed
    ang = float(st.get("bridge_angle", 0))
    hang = man_.slice(roof_z + 0.1) - man_.slice(roof_z - 0.1).offset(0.35, m3.JoinType.Square)
    hb = hang.bounds()
    ref = (k.knob_bar() if name == "knob slider" else k.carriage_test()).bounding_box()
    x0_, x1_ = ((k.STEM_X0, k.STEM_X1) if name == "knob slider" else (k.TEST_X0, k.TEST_X1))
    covers = (mlo[2] < roof_z and roof_z + 0.2 <= mhi[2] < roof_z + 0.4 and hang.area() > 10
              and mlo[0] <= hb[0] and mhi[0] >= hb[2] and mlo[1] <= hb[1] and mhi[1] >= hb[3]
              and mlo[0] <= x0_ - ref[0] and mhi[0] >= x1_ - ref[0]
              and mlo[1] <= k.LEG_Y1 - ref[1] and mhi[1] >= k.KNOB_FOOT_Y0 - ref[1])
    roof_ok.append(ang != 0 and abs(ang - 90) < 1e-9 and covers)
    roof_txt.append(f"{name} ({fname}): {st.get('name')}, bridge direction {ang:g}, x {mlo[0]:.1f}-{mhi[0]:.1f} and y {mlo[1]:.1f}-"
                    f"{mhi[1]:.1f} over the roof's bridge at x {hb[0]:.1f}-{hb[2]:.1f}, y {hb[1]:.1f}-{hb[3]:.1f} ({hang.area():.0f} mm2), "
                    f"z {mlo[2]:.2f}-{mhi[2]:.2f} over the bed")
report(len(roof_ok) == 2 and all(roof_ok),
       f"the carriage's roof bridges the rib's channel ({k.KNOB_FOOT_Y0 - k.LEG_Y1:.1f} across, along the bed's y): the slider and the "
       f"fit test's carriage piece each carry a modifier on the roof's first layer setting the bridge straight across (90, "
       f"not 0); slice it 3 times from the command line before printing to see it holds",
       "; ".join(roof_txt))


def one_sided(man, z_lo, z_hi, win, ang, reach=0.35, dx=0.005):
    """Strands held at one end only: on each layer of man from z_lo to z_hi, what hangs (what no layer below holds within
    reach, as overhangs() has it), inside the plan window win (x0, y0, x1, y1); along the bridge's lines (ang 90: lines of
    constant x, 180: of constant y), every dx: each stretch of a line across a hanging piece that does not end on the layer
    below (offset reach) at both ends. Returns (the longest such stretch, where: (z over the bed, the line's x or y, its two
    ends)), and how many layers and lines were read."""
    turn = (lambda c: c.rotate(-90)) if abs(ang - 180) < 1e-9 else (lambda c: c)
    assert abs(ang - 90) < 1e-9 or abs(ang - 180) < 1e-9
    bb = man.bounding_box()
    box_ = m3.CrossSection.square([win[2] - win[0], win[3] - win[1]]).translate([win[0], win[1]])
    worst, n_l, n_x, prev, z = (0.0, None), 0, 0, None, bb[2] + 0.15
    while z < bb[5]:
        cs = man.slice(z)
        if prev is not None and z_lo <= z - bb[2] <= z_hi:
            n_l += 1
            sup = turn(prev.offset(reach, m3.JoinType.Square))
            hang = turn((cs - prev.offset(reach, m3.JoinType.Square)) ^ box_)
            for p_ in hang.decompose():
                ed = [np.hstack([np.asarray(q), np.roll(np.asarray(q), -1, axis=0)]) for q in p_.to_polygons()]
                if not ed:
                    continue
                xa, ya, xb, yb = np.vstack(ed).T
                b_ = p_.bounds()
                for X in np.arange(math.floor(b_[0] / dx) * dx + dx / 2, b_[2], dx):
                    m = ((xa <= X) & (X < xb)) | ((xb <= X) & (X < xa))
                    if not m.any():
                        continue
                    n_x += 1
                    ys = np.sort(ya[m] + (yb[m] - ya[m]) * (X - xa[m]) / (xb[m] - xa[m]))
                    for y0_, y1_ in zip(ys[0::2], ys[1::2]):
                        held = [(m3.CrossSection.square([0.004, 0.004]).translate([X - 0.002, yy + sg * 0.01 - 0.002]) ^ sup).area() > 0
                                for yy, sg in ((y0_, -1), (y1_, 1))]
                        if not all(held) and y1_ - y0_ > worst[0]:
                            worst = (float(y1_ - y0_), (round(z - bb[2], 2), round(float(X), 3), round(float(y0_), 3), round(float(y1_), 3)))
        prev = cs
        z += 0.2
    return worst, n_l, n_x


# the roof's first layer bridges the rib's channel from the inner leg to the knob's foot. Where its edge crosses the channel in
# mid-air (at its cut-back ends), its strands are held at one end only, and a strand like that droops: then the roof prints
# lower than drawn, into the 0.25 over the rib, and the plan FE reads its factors off an edge that is not there. For the slider
# and the fit test's carriage piece, on every layer the roof's bridge modifier covers, and on up the roof: along the modifier's
# own direction, every line across what hangs must end on the layer below at both ends, or be no longer than STRAND
STRAND = 0.4
strand_rows = []
for fname, name, st, mlo, mhi, man_ in MODS_READ:
    ang = float(st.get("bridge_angle", 0))
    roof_top = k.STEM_TOP - k.BAR_Z0
    (w_, at_), n_l, n_x = one_sided(man_, mlo[2], roof_top + 0.05, (mlo[0], mlo[1], mhi[0], mhi[1]), ang)
    strand_rows.append((name, w_, at_, n_l, n_x))
report(all(w_ <= STRAND for _, w_, _, _, _ in strand_rows) and len(strand_rows) == 2,
       "the roof's bridge holds both its ends: along the bridge's lines, the longest stretch held at one end only is "
       + "; ".join(f"{name} {w_:.2f}" + (f" (z {at_[0]:.2f}, at {at_[1]:.2f}, {at_[2]:.2f} to {at_[3]:.2f} on the bed)" if at_ else "")
                   for name, w_, at_, _, _ in strand_rows) + f" (limit {STRAND})",
       "; ".join(f"{name}: {n_l} layers, {n_x} lines 0.005 apart, held where the layer below reaches within 0.35"
                 for name, _, _, n_l, n_x in strand_rows))

# the fit test's latch block stands 1.4 over the test piece's carrier. The slicer slows a layer to take 8 s, but no slower than
# 20 mm/s; alone, those top layers would print in a second or two, hot and soft, so the fit test would not test the knife's block.
# With the lug beside them they take as long as on the knife's plate, where the blade's lug, the risers and the knob print beside them
FS = json.load(open(os.path.join(k.HERE, "flash studio settings.json")))
T_LAYER, V_MIN = float(FS["slow_down_layer_time"][0]), float(FS["slow_down_min_speed"][0])
V_MOVE, LINE = float(k.MOVING["outer_wall_speed"]), float(FS["inner_wall_line_width"])   # the wider line: the least line a layer takes


def layer_time(items, z):
    """About how long a plate of solid parts takes over its layer at z: its line at the parts' own
    speed, slowed to T_LAYER but no slower than V_MIN. Returns (seconds, mm2 of part)."""
    a = sum(it[1].slice(z).area() for it in items)
    L = a / LINE
    return max(L / V_MOVE, min(T_LAYER, L / V_MIN)), a


FIT2 = dict(PROJECTS[0][1])["latch test and the knob's carriage test (white)"]
KNIFE3 = dict(PROJECTS[1][1])["blade and latch block (white)"]
zs = [k.CAR_T + 0.1 + 0.2 * i for i in range(int(round((k.BLK_D - k.CAR_T) / 0.2)))]
ft, kt = [layer_time(FIT2, z) for z in zs], [layer_time(KNIFE3, z) for z in zs]
lone = [layer_time([it for it in FIT2 if it[0] == "latch block"], z) for z in zs]
report(all(abs(a[0] - b[0]) <= 0.1 * b[0] for a, b in zip(ft, kt)),
       f"fit test: the latch block's top {len(zs)} layers, above the test piece's carrier, print beside its lug: "
       f"{min(a for _, a in ft):.0f}-{max(a for _, a in ft):.0f} mm2 a layer, {min(t for t, _ in ft):.1f}-{max(t for t, _ in ft):.1f} s each, "
       f"as on the knife's plate ({min(a for _, a in kt):.0f}-{max(a for _, a in kt):.0f} mm2, {min(t for t, _ in kt):.1f}-{max(t for t, _ in kt):.1f} s); "
       f"alone they would take {min(t for t, _ in lone):.1f}-{max(t for t, _ in lone):.1f} s",
       f"the slicer slows a layer to {T_LAYER:g} s, no slower than {V_MIN:g} mm/s; these parts print at {V_MOVE:g}, in {LINE} lines")

print()
if FAILS:
    print(f"{len(FAILS)} check(s) FAILED:")
    for f in FAILS:
        print("  - " + f)
    sys.exit(1)
print("Every check passed.")
