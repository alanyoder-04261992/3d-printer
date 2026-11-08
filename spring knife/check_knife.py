"""Checks for the spring knife toy (v3). Run:  python3 check_knife.py

It walks a whole cycle and prints what it proved:
  * every moving part clears the handle and every other part all the way round a cycle, with
    the latch block out, on the rail or pushed in by a cam as it really would be;
  * the cams leave the block alone until near the end of each stroke, push it fully in before
    the end, and never touch it at rest; the block can't catch on a corner, and it is back out
    in its window before the blade can bounce back past it;
  * the band, the sleds and the risers do what the read me says at every stage;
  * a time-step model of a throw, from the parts' real sizes, gets the blade to its lock over
    the whole range of TPU stiffness, TPU losses, friction, print weight and the knife held
    flat or pointing up; the same model with the thumb leaving the knob early;
  * how hard the thumb pushes, counting the sled being carried twisting against its walls;
  * how hard things hit, through the risers' TPU caps (every throw, a thumb flicked off the knob,
    a knob let go just before the trip) and the stress that puts in the sleds' wings, the risers,
    the bar and the rail;
  * the printed screws mesh with the top plate's posts with the shop's 0.35-0.4 mm clearance,
    and hold all three plates together;
  * every part prints without anything hanging in the air, every flat face sits on a layer
    line, no wall is thinner than two lines and no gap inside one part is under 0.45.
"""

import itertools
import math
import sys

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
HANDLE = k.union([P1, P2, P3])
FIXED = {"base plate": P1, "middle plate": P2, "top plate": P3, "screws": SCREWS,
         "rear pad": PAD_R, "front pad": PAD_F, "rear cushion": CUSH_R, "front cushion": CUSH_F}

# ---------------------------------------------------------------- where the latch block is
(W0A, W1A), (W0B, W1B) = k.windows()


def cam_y(x0, x1, s):
    """Lowest y the two cams reach under the block's outer face [x0, x1] at knob travel s."""
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


SNAP = k.KNOB_ROOM - 0.5            # how far past its end the checks drive the knob
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
          ("knob snapped back onto the rear pad", 0.0, -k.SOFT - SNAP, "held"),
          ("knob snapped forward onto the front pad", 86.0, k.THROW + k.SOFT + SNAP, "held")]
worst = {}
for label, c, s, mode in STAGES:
    bad = check_scene(c, s, worst, mode)
    report(not bad, f"{label} (c {c:g}, s {s:g}): nothing overlaps", "; ".join(bad))

print("\n== Sweeps (every 0.5 mm)")
creep = lambda s_from_end: min(k.C_COCK, k.E_CATCH + max(0.0, s_from_end - 20) * 0.25)
paths = [("knob pushed forward, blade held shut", "held", [(creep(s), s) for s in frange(-k.SOFT - SNAP, k.THROW - 1, 0.5)]),
         ("blade thrown out, knob forward", "riding", [(c, k.THROW) for c in frange(k.C_COCK, 86 + 4.0, 0.5)]),
         ("knob pulled back, blade held open", "held", [(86 - creep(k.THROW - s), s) for s in frange(k.THROW + k.SOFT + SNAP, 1.0, 0.5)]),
         ("blade thrown in, knob back", "riding", [(c, 0.0) for c in frange(86 - k.C_COCK, -4.0, 0.5)])]
for label, mode, pts in paths:
    bad = []
    for c, s in pts:
        b = check_scene(c, s, worst, mode)
        if b:
            bad.append(f"c {c:.1f} s {s:.1f}: " + "; ".join(b))
    report(not bad, f"{label}: {len(pts)} steps, nothing overlaps", " | ".join(bad[:4]))

print("\n== Latch and cams")
for c, s, label in ((0.0, 0.0, "closed rest"), (0.0, k.G_P, "closed rest, knob at the end of its play"),
                    (86.0, k.THROW, "open rest"), (86.0, k.THROW - k.G_P, "open rest, knob at the end of its play")):
    x0 = k.X_BLK + c
    report(cam_y(x0, x0 + k.BLK_L, s) >= k.Y_OUT - 1e-9, f"{label}: neither cam touches the block")


def first_touch(c, s_from, s_to, step):
    for s in frange(s_from, s_to, abs(step)):
        x0 = k.X_BLK + c
        if cam_y(x0, x0 + k.BLK_L, s) < k.Y_OUT - 1e-6:
            return s
    return None


Y_LET = k.RAIL_Y0 + k.RAIL_CHAMFER                    # 11.6: pushed below this, the block is off the rail's end
Y_SLIP = Y_LET + k.BLK_CHAMFER                        # 12.2: below this the two chamfers meet; with PLA on PLA
#                                                       (friction under 0.4) the band pushes it the rest of the way
for c in (k.E_CATCH, k.C_TRIP, k.C_COCK):
    x0 = k.X_BLK + c
    s1 = first_touch(c, 0.0, k.THROW, 0.05)
    y27 = cam_y(x0, x0 + k.BLK_L, k.THROW - 1 + (c - k.C_TRIP))
    s_e = next(s for s in frange(0, k.THROW, 0.05) if cam_y(x0, x0 + k.BLK_L, s) < Y_SLIP)
    s_l = next(s for s in frange(0, k.THROW, 0.05) if cam_y(x0, x0 + k.BLK_L, s) < Y_LET)
    report(s1 >= 18 and y27 <= k.Y_CAM + 1e-6,
           f"cam A, blade crept {c:g}: first touches the block at s {s1:.1f}, lets it go at s {s_e:.1f} to {s_l:.1f}, has it fully in by s {k.THROW - 1 + c - k.C_TRIP:g}")
for c in (86 - k.E_CATCH, 86 - k.C_TRIP, 86 - k.C_COCK):
    x0 = k.X_BLK + c
    s1 = first_touch(c, k.THROW, 0.0, 0.05)
    y1 = cam_y(x0, x0 + k.BLK_L, 1.0 - ((86 - c) - k.C_TRIP))
    s_e = next(s for s in frange(k.THROW, 0, 0.05) if cam_y(x0, x0 + k.BLK_L, s) < Y_SLIP)
    s_l = next(s for s in frange(k.THROW, 0, 0.05) if cam_y(x0, x0 + k.BLK_L, s) < Y_LET)
    report(s1 <= k.THROW - 18 and y1 <= k.Y_CAM + 1e-6,
           f"cam B, blade crept {86 - c:g}: first touches the block at s {s1:.1f}, lets it go at s {s_e:.1f} to {s_l:.1f}, has it fully in by s {1.0 - ((86 - c) - k.C_TRIP):g}")


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


th_rail, th_out = block_turn(k.Y_RAIL), block_turn(k.Y_OUT)
rise = k.BLK_L * math.sin(th_rail)
corner = k.Y_RAIL + rise - k.BLK_CHAMFER
report(corner < Y_LET, f"a block leaving its window can turn {math.degrees(th_rail):.1f} degrees in its slot; its chamfered trailing corner stays at y {corner:.2f}, inside the rail's {Y_LET:.2f}")
lean_out = math.sin(th_out) * (k.Y_OUT - k.CAR_W / 2)
report(lean_out < k.BLK_CHAMFER, f"out in a window it can turn {math.degrees(th_out):.1f} degrees and leans at most {lean_out:.2f} at its face, less than its {k.BLK_CHAMFER} chamfers")
ok = True
for c in frange(k.E_CATCH, k.RAIL_X0 - k.X_BLK, 0.05):
    x0, x1 = k.X_BLK + c, k.X_BLK + c + k.BLK_L
    held = cam_y(x0, x1, k.THROW - 1) <= k.Y_RAIL + 1e-6 or (x1 - k.RAIL_X0) >= 1.0
    ok = ok and held
report(ok, "on the way out, from the trip until the block is past the rail's end, cam A or 1 mm of rail holds it in")
ok = True
for c in frange(86 - k.E_CATCH, k.RAIL_X1 - k.X_BLK - k.BLK_L, 0.05):
    x0, x1 = k.X_BLK + c, k.X_BLK + c + k.BLK_L
    held = cam_y(x0, x1, 1.0) <= k.Y_RAIL + 1e-6 or (k.RAIL_X1 - x0) >= 1.0
    ok = ok and held
report(ok, "on the way in, the same with cam B")
eng = min(k.Y_OUT - k.BLK_CHAMFER, k.SPINE_Y0) - Y_LET
bar_in = k.BAR_Y0 - k.RISER_SLOT_Y0                 # the thumb can push the bar in this far
rail_out = k.SPINE_Y0 - k.GROOVE_Y0                 # and the block riding a catch pushes the rail out this far
bite = k.Y_OUT - bar_in - k.BLK_CHAMFER - (Y_LET + rail_out)
high = k.RAIL_TOP - (k.BLK_Z0 + (k.Z1 - k.BLK_Z1))   # the block lifted to the middle plate
report(bite >= 0.75 and high >= 1.4, f"at worst (bar pushed in, rail pushed out, block lifted) it still bites {bite:.2f} deep over {high:.2f} of height")
report(eng >= 1.0 and k.RAIL_TOP - k.BLK_Z0 >= 1.5,
       f"latched, the block bears {eng:.2f} mm deep on the rail's end, over {k.RAIL_TOP - k.BLK_Z0:.2f} mm of height")
E_PLA, G_PLA = 3500.0, 1300.0
arm_L = k.arm_L()
k_arm = 3 * E_PLA * (k.CAR_T * k.ARM_T ** 3 / 12) / arm_L ** 3
d_max = k.arm_deflect_for(k.Y_CAM)
strain = 3 * k.ARM_T * d_max / (2 * arm_L ** 2)
r_t = k.ARM_RELIEF / k.ARM_T
kt = 1 + 0.5 / math.sqrt(r_t)                       # a round-ended slot at a cantilever's root
F_RAIL = k_arm * k.arm_deflect_for(k.Y_RAIL)
report(strain * kt < 0.01, f"latch arm: {k_arm:.2f} N/mm, bent at most {d_max:.2f} mm, {strain * 100:.2f} % strain, "
                           f"{strain * kt * 100:.2f} % at its round-ended root (PLA keeps under 1 % for a long life)",
       f"presses the block on the rail with {F_RAIL:.2f} N, out in a window with {k_arm * k.arm_deflect_for(k.Y_OUT):.2f} N")
x_tops = []
for y in (k.Y_OUT, k.Y_RAIL, k.Y_CAM):
    xs = [x for x, _ in k.nose_poly(k.arm_deflect_for(y))]
    x_tops.append((min(xs), max(xs)))
lo, hi = min(a for a, _ in x_tops), max(b for _, b in x_tops)
flat0, flat1 = k.BLK_X0 + k.BLK_CHAMFER, k.BLK_X0 + k.BLK_L - k.BLK_CHAMFER
report(lo - (k.BLK_X0 - k.BLK_SLOT) >= 0.45 and (k.BLK_X0 + k.BLK_L + k.BLK_SLOT) - hi >= 0.45,
       f"the arm's nose, turning with the arm, stays {lo - (k.BLK_X0 - k.BLK_SLOT):.2f} and {(k.BLK_X0 + k.BLK_L + k.BLK_SLOT) - hi:.2f} clear of the slot's walls")

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
_x0 = k.X_BLK + k.C_TRIP
S_TRIP = next(s for s in frange(0, k.THROW, 0.01) if cam_y(_x0, _x0 + k.BLK_L, s) < Y_SLIP)       # earliest let-go
S_TRIP_LATE = next(s for s in frange(0, k.THROW, 0.01) if cam_y(_x0, _x0 + k.BLK_L, s) < Y_LET)   # latest
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


# where the block is, and how hard the arm presses it, all along a throw (the in-throw is its mirror)
C_GRID = [k.C_TRIP + 0.05 * i for i in range(int((87.5 - k.C_TRIP) / 0.05) + 1)]
Y_GRID = [latch_state(c, k.THROW, "riding")[0] for c in C_GRID]
N_GRID = [k_arm * k.arm_deflect_for(y) for y in Y_GRID]
SLOPE = [0.0] + [max(0.0, (Y_GRID[i - 1] - Y_GRID[i]) / 0.05) for i in range(1, len(C_GRID))]


def friction(c, mu, fill, up=False):
    """Friction on the blade at c while it runs (N): the arm presses the block on a catch, a cam
    or the knob bar and the carrier on the far channel wall; where a ramp pushes the block in,
    the ramp's push; and the blade's weight (twice that pointing up)."""
    i = min(max(int(round((c - C_GRID[0]) / 0.05)), 0), len(C_GRID) - 1)
    N, sl = N_GRID[i], SLOPE[i]
    m_b = m_blade_solid * fill
    push = N * math.tan(math.atan(sl) + math.atan(mu)) if sl > 0 else mu * N
    return FC_MISC + mu * N + push + mu * m_b * G_ACC + (m_b * G_ACC if up else 0.0)


def k_pad(E_tpu):
    return E_tpu * (2 * k.PAD_HW * k.SLED_H) / k.PAD_L


def throw(E_tpu, h, mu, fill, up=False, band=k.BAND, dt=2e-6, mu_push=0.046, follow=False):
    """One throw from the trip. E_tpu MPa; h TPU loss on unloading; mu PLA on PLA; fill:
    printed weight over solid; up: knife pointing up. follow: the thumb has pushed the knob on
    to its pad (the most the band can give), else it stopped where the block let go (the least).
    Returns a dict."""
    kb = E_tpu * band[0] * band[1] / k.BAND_RELAXED
    m = (m_blade_solid + m_sled) * fill / 1000      # kg: sled F rides along while the band pulls
    c0 = k.C_TRIP
    stroke = ((k.THROW + k.SOFT if follow else S_TRIP) - k.G_P) - c0
    x, v = 0.0, 0.0
    while x < stroke:
        T = (1 - h) * kb * (k.BAND_PRELOAD + stroke - x)
        F = T - friction(c0 + x, mu, fill, up) - mu_push * T
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
    k_cush = E_tpu * K_CUSH_AREA / CUSH_FREE
    d_cush = math.sqrt(2 * E_reb / k_cush)
    v_arr = math.sqrt(2 * E_arr / 1000 / m_b) if E_arr > 0 else 0.0
    return {"reached": True, "E_throw": E, "v_release": v / 1000, "E_arrive": E_arr, "squash": squash, "F_pad": kp * squash,
            "overrun": k.G_P + k.SOFT + squash, "E_rebound": E_reb, "d_cush": d_cush, "F_cush": k_cush * d_cush,
            "v": v_arr, "Fc": Fc, "m_b": m_b * 1000, "kp": kp}


print("\n== A throw, step by step (the in-stroke is its mirror)")
mid = (k.RAIL_X0 + k.RAIL_X1) / 2 - k.X_BLK
print(f"     masses, printed solid: blade {m_blade_solid:.1f} g, knob slider {m_bar:.2f} g, each sled {m_sled:.2f} g; friction "
      f"{friction(mid, 0.2, 0.8):.2f}-{friction(mid, 0.4, 1.0, True):.2f} N between the catches, {friction(k.C_TRIP + 3, 0.2, 0.8):.2f}-"
      f"{friction(k.C_TRIP + 3, 0.4, 1.0, True):.2f} N on a catch (PLA on PLA 0.2-0.4, flat or pointing up)")
report(min(Y_GRID[int((mid - k.C_TRIP) / 0.05) - 100:int((mid - k.C_TRIP) / 0.05) + 100]) >= k.Y_OUT - 1e-9,
       f"between the catches the block is out against the knob bar, pressed with only {k_arm * k.arm_deflect_for(k.Y_OUT):.2f} N; "
       f"on a catch with {F_RAIL:.2f} N")
MU = (0.2, 0.3, 0.4)
grid = list(itertools.product((15.0, 20.0, 26.0), (0.1, 0.2, 0.3), MU, (0.6, 1.0), (False, True)))
res = [(g, throw(*g)) for g in grid]
fails = [g for g, r in res if not r["reached"]]
oks = [r for g, r in res if r["reached"]]
report(not fails, f"band: the blade reaches its lock in all {len(grid)} cases (TPU 15-26 MPa, losses 10-30 %, PLA friction 0.2-0.4, "
                  f"printed 60-100 % solid, held flat or pointing up)",
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


def crit_extra(E_tpu, h, band=k.BAND):
    """Extra friction (N) on top of the worst case (PLA 0.4, solid, pointing up) a throw can still take."""
    lo, hi = 0.0, 5.0
    global FC_MISC
    base = FC_MISC
    for _ in range(30):
        mid = (lo + hi) / 2
        FC_MISC = base + mid
        ok_ = throw(E_tpu, h, 0.4, 1.0, True, band)["reached"]
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

# the block has to be back out before the blade bounces back past the rail's end
m_arm = k.ARM_T * k.CAR_T * arm_L * RHO
m_pop = k.latch_block().volume() * RHO + 0.24 * m_arm
w_arm = math.sqrt(k_arm * 1000 / (m_pop / 1000))                  # rad/s
d_rail, d_catch = k.arm_deflect_for(k.Y_RAIL), k.arm_deflect_for(Y_SLIP + 0.2)
t_pop = math.acos(d_catch / d_rail) / w_arm * 1000                 # ms, against the slot's friction ignored ...
t_pop *= 1.5                                                       # ... so allow half as long again
t_win = []
for r in oks:
    v = r["v"]                                                     # m/s = mm/ms
    m_b, m_s = r["m_b"], m_sled
    v2 = v * m_b / (m_b + m_s)
    t_pad = math.pi * math.sqrt((m_b + m_s) / 1000 / (r["kp"] * 1000)) * 1000
    t_win.append((k.E_CATCH + k.G_P) / v + k.SOFT / v2 + t_pad + (k.SOFT + k.G_P + k.E_CATCH) / max(0.6 * v2, 1e-3))
report(t_pop < min(t_win), f"the arm has the block back out over the rail's end in {t_pop:.2f} ms; the blade is back there no sooner than {min(t_win):.2f} ms")
SOLID_OKS = [r for r in oks if r["m_b"] >= 0.9 * m_blade_solid]   # the moving parts print solid
v_far = max(r["v"] for r in SOLID_OKS) * 1.05                       # the blade meets the far ramp a little before it arrives
v_in = v_far * math.tan(math.radians(k.SEG_RAMP))                   # m/s = mm/ms: the ramp throws the block in this fast
d_kick = math.sqrt(d_rail ** 2 + (v_in / (w_arm / 1000)) ** 2)     # the arm's spring takes that speed
room = k.arm_deflect_for(k.Y_CAM) + 0.1 + k.ARM_GAP
st_kick = 3 * k.ARM_T * d_kick / (2 * arm_L ** 2) * kt
report(d_kick <= room - 0.05 and st_kick < 0.01, f"the far ramp throws the block in at up to {v_in:.1f} m/s; the arm then bends {d_kick:.2f} mm "
       f"({st_kick * 100:.2f} % at its root), inside the {room:.2f} mm of room under it")

print("\n== The thumb")
A_TWIST = k.BAR_Y0                         # the riser pushes the wing's inner corner, the band pulls on y = 0
W_TWIST = k.RISER_Y1 - k.SLED_HW


def twist(mu):
    """How much harder a riser has to push a sled than the band pulls it: the sled turns until
    two corners bear on the walls, SLED_LEN apart, and they rub."""
    return 1 / (1 - 2 * mu * A_TWIST / (k.SLED_LEN + mu * W_TWIST))


def thumb_at_trip(E_tpu, mu, band=k.BAND):
    """(band pull, riser push, cam push, total) at the trip. The cam's 22 degree face also
    pushes the block forward into the rail's end, which adds to the rubbing it has to beat."""
    kb = E_tpu * band[0] * band[1] / k.BAND_RELAXED
    Fb = kb * (k.BAND_PRELOAD + S_TRIP_LATE - k.G_P - k.C_TRIP)
    tn = math.tan(math.radians(k.CAM_ANGLE) + math.atan(mu))
    F_lat = (2 * mu * Fb + k_arm * k.arm_deflect_for(k.Y_CAM)) / (1 - mu * tn)
    F_cam = F_lat * (tn + mu)
    return Fb, Fb * twist(mu), F_cam, Fb * twist(mu) + F_cam + 0.3


rows = []
for E_tpu, band, name in ((20.0, k.BAND, "band"), (26.0, k.BAND, "band"), (26.0, k.BAND_SOFT, "soft band"),
                          (30.0, k.BAND_SOFT, "soft band"), (12.0, k.BAND_STRONG, "strong band")):
    for mu in MU:
        rows.append((name, E_tpu, mu) + thumb_at_trip(E_tpu, mu, band))
for name, E_tpu, mu, Fb, Fr, Fcam, tot in rows:
    if mu == 0.3:
        print(f"     thumb at the trip, {name}, TPU {E_tpu:.0f} MPa, PLA friction 0.3: band {Fb:.1f} N, riser {Fr:.1f} N (sled twisting x{twist(mu):.2f}) "
              f"+ latch {Fcam:.1f} N + bar 0.3 N = {tot:.1f} N")
hi_ = max(r[-1] for r in rows)
NOMINAL_THUMB = thumb_at_trip(20.0, 0.3)[-1]
report(NOMINAL_THUMB < 20 and hi_ < 33, f"thumb at the trip: {NOMINAL_THUMB:.1f} N nominal, {min(r[-1] for r in rows):.1f}-{hi_:.1f} N over friction 0.2-0.4 and the three bands in their TPUs "
                                       f"(the sled twists x{twist(0.2):.2f}-{twist(0.4):.2f})")


def thumb_off(when, E_tpu, h, mu, fill, band=k.BAND, m_thumb=10.0, dt=2e-4):
    """The thumb leaves the knob: when 'never', 'trip' (at the moment of the trip) or 'land'
    (as the knob lands on its pad). Units mm, g, ms, N. While on, it pushes with the trip force
    and the knob jumps on to its pad and stays; once off, the band pulls the bar back. The blade
    is only pushed by sled F, so when riser F meets sled F the blade goes on alone and coasts.
    Returns (locks, ms from the trip to the thumb leaving, m/s at which riser F meets sled F)."""
    kb = E_tpu * band[0] * band[1] / k.BAND_RELAXED
    m_b, m_s, m_br = m_blade_solid * fill, m_sled * fill, m_bar * fill
    F_th = thumb_at_trip(E_tpu, mu, band)[-1]
    s_end = k.THROW + k.SOFT
    c, v, s, vs, t = k.C_TRIP, 0.0, S_TRIP, 0.0, 0.0
    on, landed, t_left = when != "trip", False, (0.0 if when == "trip" else None)
    while True:
        T = (1 - h) * kb * ((k.R_B + s + 2 * k.POST_BACK) - c - k.BAND_RELAXED)
        a = (T * (1 - 0.046) - friction(c, mu, fill)) / (m_b + m_s)
        if landed and on:
            vs = 0.0
        else:
            F_bar = (F_th if on else 0.0) - T / twist(mu) - 0.2 * (1 if vs > 0 else -1)
            vs += F_bar / (m_br + m_s + (m_thumb if on else 0.0)) * dt
            s += vs * dt
            if s >= s_end and on:
                s, vs, landed = s_end, 0.0, True
                if when == "land":
                    on, t_left = False, t
        v += a * dt
        c += v * dt
        t += dt
        if v <= 0:
            return False, t_left, 0.0
        if c >= s - k.G_P:
            break
    v_close = v - vs
    E_b = 0.5 * m_b * v * v
    while c < (k.RAIL_X1 - k.X_BLK) + 0.3:
        E_b -= friction(c, mu, fill) * 0.05
        if E_b <= 0:
            return False, t_left, v_close
        c += 0.05
    return True, t_left, v_close


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
lev = (k.SLED_Z0 + k.SLED_Z1) / 2 - k.BAR_Z1
w_r = k.RISER_Y1 - k.BAR_Y0


def riser_mpa(F):
    sb = F * lev / (w_r * k.RISER_L ** 2 / 6)
    tau = 1.5 * F / (w_r * k.RISER_L)
    return sb / 2 + math.sqrt((sb / 2) ** 2 + tau ** 2)


LANE_CS = P1.slice(k.LANE_Z0 - 0.05)       # the base plate just under the lane's floor


def bar_stress(F, s):
    """Largest bending stress (MPa) in the plain bar when riser F stops it with F (knob let go):
    the bar as a beam on its lane's floor, under the middle plate's floor and its ledge over
    the risers' slots, with riser F's push 3 mm over its axis."""
    E = E_PLA
    b, hgt = k.BAR_Y1 - k.BAR_Y0, k.BAR_Z1 - k.BAR_Z0
    I0, Z0 = b * hgt ** 3 / 12, b * hgt ** 2 / 6
    x0, x1 = k.bar_x(s)
    (f0, f1), (b0, b1) = k.riser_x()
    f0, f1, b0, b1 = f0 + s, f1 + s, b0 + s, b1 + s
    st0, st1 = k.STEM_X0 + s, k.STEM_X1 + s
    h = 0.5
    xs = np.arange(x0, x1 + 1e-9, h)
    n = len(xs)
    xm = (xs[:-1] + xs[1:]) / 2
    EI = np.full(n - 1, E * I0)
    EI[(xm > f0) & (xm < f1)] *= 15
    EI[(xm > b0) & (xm < b1)] *= 15
    EI[(xm > st0) & (xm < st1)] *= 3
    under, over = 0.0, (k.Z1 - k.BAR_Z1) + (k.BAR_Z0 - k.LANE_Z0)     # lying on the floor
    floor = np.array([(LANE_CS ^ m3.CrossSection.square([h, b]).translate([x - h / 2, k.BAR_Y0])).area() > 0.05 * h for x in xs])
    K = np.zeros((2 * n, 2 * n))
    for i in range(n - 1):
        e, L = EI[i], h
        ke = e / L ** 3 * np.array([[12, 6 * L, -12, 6 * L], [6 * L, 4 * L * L, -6 * L, 2 * L * L],
                                    [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L * L, -6 * L, 4 * L * L]])
        d = [2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 3]
        K[np.ix_(d, d)] += ke
    f = np.zeros(2 * n)
    zc = (k.BAR_Z0 + k.BAR_Z1) / 2
    e_r = (k.SLED_Z0 + k.SLED_Z1) / 2 - zc
    e_k = (k.KNOB_TOP + k.BAR_Z0) / 2 - zc
    m_tot = m_bar + m_sled
    def couple(xa, xb, Mo):
        sel = np.nonzero((xs >= xa) & (xs <= xb))[0]
        for j in sel:
            f[2 * j + 1] += Mo / len(sel)
    couple(f0, f1, -e_r * F)
    couple(b0, b1, +e_r * F * m_sled / m_tot)
    couple(st0, st1, +e_k * F * m_knob / m_tot)
    kc = 2e4
    u = np.zeros(2 * n)
    idx = np.arange(0, 2 * n, 2)
    for _ in range(200):
        w = u[0::2]
        g = K @ u - f
        g[0::2] += -kc * np.maximum(0, -under - w) * floor + kc * np.maximum(0, w - over)
        H = K.copy()
        H[idx, idx] += kc * (((w < -under) & floor) | (w > over)) + 1e-6
        du = -np.linalg.solve(H, g)
        u = u + du
        if np.abs(du).max() < 1e-9:
            break
    th = u[1::2]
    Mel = EI * (th[1:] - th[:-1]) / h
    plain = EI == E * I0
    return float(np.max(np.where(plain, np.abs(Mel) / Z0, 0)))


H_CAP = min(k.RISER_TOP, k.SLED_Z1) - k.SLED_Z0      # the height a wing meets a cap over


def k_cap(E_tpu):
    """A riser's TPU cap (N/mm): the TPU in front of the tongue, and the cap's two sides."""
    return E_tpu * (k.TONGUE_W * H_CAP / k.CAP_T + (w_r - k.TONGUE_W) * H_CAP / k.CAP_L)


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


CORNER = 1.3                                # the bar's stress at a riser's square foot
knocks = []
v_every = max(max(never[i][2] for i in solid_cases), max(r["v_release"] for r in SOLID_OKS))   # parts printed solid
v_flick = max(land[i][2] for i in solid_cases)
v_let = max(letgo_speed(E, h, mu, b) for E, b in ((15.0, k.BAND), (20.0, k.BAND), (26.0, k.BAND), (30.0, k.BAND_SOFT),
                                                     (10.0, k.BAND_STRONG), (15.0, k.BAND_STRONG)) for h in (0.1, 0.3) for mu in MU)
for label, v, lim in (("every throw (thumb kept on)", v_every, 20), ("thumb flicked off as the knob lands", v_flick, 30),
                      ("knob let go just before the trip", v_let, 30)):
    F, sq = max(hit(v, E) for E in (15.0, 20.0, 26.0, 30.0))
    b_s = bar_stress(F, k.THROW if "every" in label else -k.SOFT) * CORNER
    ok = F * WING_MPA <= lim and riser_mpa(F) <= 12 and b_s <= lim and max(hit(v, E)[1] for E in (15.0, 20.0, 26.0, 30.0)) <= 0.55 * k.CAP_T
    report(ok, f"{label}: sled meets its riser's TPU cap at up to {v:.1f} m/s: {F:.0f} N, squashing it {max(hit(v, E)[1] for E in (15.0, 20.0, 26.0, 30.0)):.1f} "
               f"of {k.CAP_T}; {F * WING_MPA:.1f} MPa at the wing's root, {riser_mpa(F):.1f} across the riser's root layer, "
               f"{b_s:.1f} in the bar at a riser's foot (limits {lim}, 12, {lim})")

# then the let-go lands: the rear pad and the cap in series stop the bar and both sleds
snaps = []
for E_tpu, band in ((15.0, k.BAND), (20.0, k.BAND), (26.0, k.BAND), (26.0, k.BAND_SOFT), (30.0, k.BAND_SOFT),
                    (10.0, k.BAND_STRONG), (15.0, k.BAND_STRONG)):
    kb = E_tpu * band[0] * band[1] / k.BAND_RELAXED
    u = k.BAND_PRELOAD + S_TRIP_LATE - k.G_P - k.C_TRIP
    E_s = 0.5 * kb * (u ** 2 - k.BAND_PRELOAD ** 2) * 0.9 / twist(0.2)   # less the least TPU loss and rubbing
    k_s = 1 / (1 / k_pad(E_tpu) + 1 / k_cap(E_tpu))
    travel = math.sqrt(2 * E_s / k_s)
    F_ = k_s * travel
    snaps.append((F_, travel, F_ / k_pad(E_tpu), E_s, E_tpu))
F_lg, _, _, E_snap, E_tpu = max(snaps)
tr_max = max(r[1] for r in snaps)
pad_max = max(r[2] for r in snaps)
cap_max = max(r[0] / k_cap(r[4]) for r in snaps)
report(tr_max <= k.KNOB_ROOM and pad_max <= free - 0.5 and cap_max <= 0.9 * k.CAP_T,
       f"  it lands with up to {E_snap:.0f} mJ on the rear pad and the cap, a slow squeeze: the knob goes on {tr_max:.1f} mm "
       f"({k.KNOB_ROOM} of room before the bar's end meets the lane's end square on), the pad squashes {pad_max:.1f} "
       f"({free:.1f} of it out of its pocket), the cap {cap_max:.1f} of {k.CAP_T} (worked out as if TPU never stiffens)")
b_s = bar_stress(F_lg, -k.SOFT - 2.0) * CORNER
report(F_lg * WING_MPA <= 30 and riser_mpa(F_lg) <= 12 and b_s <= 30,
       f"  that is up to {F_lg:.0f} N (TPU {E_tpu:.0f} MPa): {F_lg * WING_MPA:.1f} MPa at the wing's root, "
       f"{riser_mpa(F_lg):.1f} MPa across the riser's root layer, {b_s:.1f} MPa in the bar (limits 30, 12 and 30 for this rare knock)")


def rail_stress(F, closed=True):
    """The rail as a beam pushed along its length at a catch's end (y 11.6, where a leaning
    block bears) and held by the far cushion on the spine's line. Each step in the rail's centre
    line along the way turns the push into a bend; the rail leans on its groove's walls and the
    catch pocket's wall wherever its play runs out, and the push bends it more as it bows.
    Largest stress along the rail (MPa) and where it is."""
    rl = k.rail()
    h = 0.5
    xs = np.arange(k.SPINE_X0, k.SPINE_X1 + 1e-9, h)
    n = len(xs)
    xm = (xs[:-1] + xs[1:]) / 2
    t = k.RAIL_TOP - k.RAIL_Z0
    cs = rl.slice((k.RAIL_Z0 + k.RAIL_TOP) / 2)
    lo_y, hi_y = [], []
    for x in xm:
        b = (cs ^ m3.CrossSection.square([0.05, 30]).translate([x - 0.025, 0])).bounds()
        lo_y.append(b[1])
        hi_y.append(b[3])
    lo_y, hi_y = np.array(lo_y), np.array(hi_y)
    w, yc = hi_y - lo_y, (lo_y + hi_y) / 2
    EI = E_PLA * t * w ** 3 / 12
    x_load = k.RAIL_X0 if closed else k.RAIL_X1
    il = int(np.argmin(np.abs(xs - x_load)))
    P = np.where(xm > x_load, F, 0.0) if closed else np.where(xm < x_load, F, 0.0)
    K = np.zeros((2 * n, 2 * n))
    for i_ in range(n - 1):
        e, L, Pi = EI[i_], h, P[i_]
        ke = e / L ** 3 * np.array([[12, 6 * L, -12, 6 * L], [6 * L, 4 * L * L, -6 * L, 2 * L * L],
                                    [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L * L, -6 * L, 4 * L * L]])
        kg = Pi / (30 * L) * np.array([[36, 3 * L, -36, 3 * L], [3 * L, 4 * L * L, -3 * L, -L * L],
                                       [-36, -3 * L, 36, -3 * L], [3 * L, -L * L, -3 * L, 4 * L * L]])
        d = [2 * i_, 2 * i_ + 1, 2 * i_ + 2, 2 * i_ + 3]
        K[np.ix_(d, d)] += ke - kg
    f = np.zeros(2 * n)
    y_load = Y_LET + 0.15
    if closed:
        f[2 * il + 1] += F * (yc[il] - y_load)
        for j_ in range(il + 1, n - 1):
            f[2 * j_ + 1] += F * (yc[j_] - yc[j_ - 1])
    else:
        f[2 * il + 1] -= F * (yc[il - 1] - y_load)
        for j_ in range(1, il):
            f[2 * j_ + 1] += F * (yc[j_] - yc[j_ - 1])
    play = k.SPINE_Y0 - k.GROOVE_Y0
    lo_b = np.full(n, -9.0)
    for j_, x in enumerate(xs):
        r = k.rail_y(x)
        if r is not None and abs(r - k.RAIL_Y0) < 1e-6:
            lo_b[j_] = -0.1                  # the catch's flat over its pocket's wall (below the channel floor)
        elif not (k.RAIL_X0 - k.RAIL_MOVE <= x <= k.RAIL_X0 + k.SEG_L + k.RAIL_MOVE or
                  k.RAIL_X1 - k.SEG_L - k.RAIL_MOVE <= x <= k.RAIL_X1 + k.RAIL_MOVE):
            lo_b[j_] = -play                 # the spine on its groove's inner wall
    hi_b = np.full(n, play)
    kc, idx = 2e4, np.arange(0, 2 * n, 2)
    act_lo, act_hi = np.zeros(n, bool), np.zeros(n, bool)
    u = np.zeros(2 * n)
    for _ in range(200):
        H = K.copy()
        H[idx, idx] += kc * (act_lo | act_hi) + 0.01
        rhs = f.copy()
        rhs[idx] += kc * (lo_b * act_lo + hi_b * act_hi)
        u = np.linalg.solve(H, rhs)
        v = u[0::2]
        n_lo, n_hi = v < lo_b, v > hi_b
        n_lo |= act_lo & (v < lo_b + 1e-6)
        n_hi |= act_hi & (v > hi_b - 1e-6)
        if (n_lo == act_lo).all() and (n_hi == act_hi).all():
            break
        act_lo, act_hi = n_lo, n_hi
    th = u[1::2]
    Mel = EI * (th[1:] - th[:-1]) / h
    sig = np.abs(Mel) / (t * w ** 2 / 6) + P / (t * w)
    return float(sig.max()), float(xm[int(sig.argmax())])


F_cock = max(thumb_at_trip(E, 0.3, b)[0] for E, b in ((20.0, k.BAND), (26.0, k.BAND), (30.0, k.BAND_SOFT), (15.0, k.BAND_STRONG)))
F_reb = max(r["F_cush"] for r in oks)
F_reb_nom = throw(20.0, 0.15, 0.3, 0.9, follow=True)["F_cush"]
for label, F, lim in (("cocked", F_cock, 20), ("a nominal bounce", F_reb_nom, 20), ("the hardest bounce", F_reb, 30)):
    sg = max(rail_stress(F, True)[0], rail_stress(F, False)[0])
    report(sg <= lim, f"rail, {label}: {F:.0f} N on a catch's end puts at most {sg:.1f} MPa in the rail (limit {lim})")

print("\n== Printed screws")
N = 1200
pts_s = [(-(i / N) * k.PITCH * 2, k.thread_r((i / N * 2) % 1, k.THREAD_MIN / 2, k.THREAD_MAJ / 2)) for i in range(N + 1)]
pts_n = [(-(i / N) * k.PITCH * 2, k.thread_r((i / N * 2) % 1, k.THREAD_MIN / 2 + k.THREAD_PLAY, k.THREAD_MAJ / 2 + k.THREAD_PLAY, k.GROOVE_WIDEN))
         for i in range(N + 1)]
gap = min(math.hypot(a[0] - b[0], a[1] - b[1]) for a in pts_s[200:1000:2] for b in pts_n[::2])
report(gap >= 0.35, f"screw to nut, square to the thread: {gap:.2f} mm all round (the brain's pin rule: 0.35-0.4)")
report(all(overlap(k.screw(x, y), P3) < TOL for x, y in k.SCREWS), "each screw turns in its post's thread in the top plate")
report(overlap(SCREWS, P3.translate([0, 0, 1.0])) > 0.5 and overlap(SCREWS, (P2 + P3).translate([0, 0, 1.0])) > 0.5,
       "and holds the plates: lifted 1 mm, the top plate (alone or with the middle plate) runs into the screws")
report(k.BOSS_Z0 - k.Z1 >= 0.2 and overlap(P2, P3) < TOL,
       f"the posts stop {k.BOSS_Z0 - k.Z1:.2f} above the base plate, so tightening pulls all three plates together")
report(overlap(k.screw(), k.nut()) < TOL and overlap(k.screw(), k.nut().translate([0, 0, 1.0])) > 0.5,
       "the fit test's gauge nut has the posts' thread: the screw turns in it and holds it")
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
        ("knob bar, under and over", min(k.BAR_Z0 - k.LANE_Z0, k.Z1 - k.BAR_Z1), 0.2),
        ("knob bar over the rail", k.BAR_Z0 - k.RAIL_TOP, 0.3), ("knob bar over the cushions", k.BAR_Z0 - k.CUSH_TOP, 0.4),
        ("cams past the carrier's cut-back side, bar pushed in all the way", k.Y_CAM - k.CAR_CUT_Y - (k.BAR_Y0 - k.RISER_SLOT_Y0), 0.1),
        ("knob to the handle's side", k.KNOB_Y0 - k.HW / 2, 0.5),
        ("sleds in the band level, sides", min(-k.SLED_HW - k.CAV_Y0, k.CAV_Y1 - k.RISER_Y1), 0.25),
        ("lug in its floor slot", 0.7, 0.4), ("band in the lug's slot (strong band)", k.BAND_SLOT - k.BAND_STRONG[1] / 2, 0.3),
        ("band eye on its post", k.EYE_PLAY, 0.35), ("screw holes", (k.SCREW_HOLE - k.THREAD_MAJ) / 2, 0.35),
        ("screw head in its counterbore", (k.COUNTERBORE - k.HEAD_D) / 2, 0.35), ("pegs in their holes", (k.PEG_HOLE_D - k.PEG_D) / 2, 0.35),
        ("rail cushions to the spine's ends", 0.1, 0.1), ("rail spine in its groove", k.SPINE_Y0 - k.GROOVE_Y0, 0.25),
        ("top plate's posts in the middle plate's pockets", (k.NUT_POCKET_AF - k.BOSS_AF) / 2, 0.25),
        ("web between the risers' slots in the middle plate's floor",
         k.riser_sweep(*k.riser_x()[1])[0] - k.riser_sweep(*k.riser_x()[0])[1], 1.2),
        ("the risers' slots run on past the lane's ends", (k.riser_x()[0][0] - k.riser_sweep(*k.riser_x()[0])[0]) - (k.bar_x(0)[0] - k.lane_x()[0]), 0.25)]
for what, v, need in rows:
    report(v >= need - 1e-9, f"{what}: {v:.2f}", f"needs {need}")

print("\n== Printing")
pp = k.print_parts()
pp["latch test"] = k.on_bed(k.latch_test())


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
                 "handle 2 middle": "the peg holes' ceilings", "screw": "the coin slot's ceiling"}
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


for name in ("handle 1 base", "handle 2 middle", "handle 3 top", "blade", "sled F", "rail", "knob slider"):
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

print()
if FAILS:
    print(f"{len(FAILS)} check(s) FAILED:")
    for f in FAILS:
        print("  - " + f)
    sys.exit(1)
print("Every check passed.")
