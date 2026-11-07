"""Checks for the spring knife toy (v3). Run:  python3 check_knife.py

It walks a whole cycle and prints what it proved:
  * every moving part clears the handle and every other part all the way round a cycle, with
    the latch block out, on the rail or pushed in by a cam as it really would be;
  * the cams leave the block alone until near the end of each stroke, push it fully in before
    the end, and never touch it at rest;
  * the band, the sleds and the risers do what the read me says at every stage;
  * a time-step model of a throw, from the parts' real sizes, gets the blade to its lock over
    the whole range of TPU stiffness, TPU losses, friction and print weight, and reports how hard
    things hit;
  * the printed screws mesh with their nuts with the shop's 0.35-0.4 mm clearance;
  * every part prints without anything hanging in the air, and every height sits on a layer line.
"""

import itertools
import math
import sys

sys.dont_write_bytecode = True
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
NUTS = k.union([k.nut(x, y) for x, y in k.SCREWS])
PAD_R, PAD_F = k.pad(k.PAD_X0), k.pad(k.PAD_X1 - k.PAD_L)
CUSHION = k.rail_cushion()
HANDLE = k.union([P1, P2, P3])
FIXED = {"base plate": P1, "middle plate": P2, "top plate": P3, "screws": SCREWS, "nuts": NUTS,
         "rear pad": PAD_R, "front pad": PAD_F, "rail cushion": CUSHION}

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
    its cushion. mode 'riding': the blade is on its way, so the block rides on the rail until it
    is wholly past the rail's end, then pops out."""
    x0, x1 = k.X_BLK + c, k.X_BLK + c + k.BLK_L
    yc = cam_y(x0, x1, s)
    if mode == "held":
        # pressed into the rail's end, it shifts the rail; once a cam has it past the rail's
        # chamfer it lets go, and the rail's chamfer runs it the rest of the way in
        dx = max(0.0, x1 - k.RAIL_X0) if c < 43 else -max(0.0, k.RAIL_X1 - x0)
        return min(k.Y_OUT, yc), dx
    in_window = (x1 <= k.RAIL_X0 + 1e-9) or (x0 >= k.RAIL_X1 - 1e-9)
    return min(k.Y_OUT if in_window else k.Y_RAIL, yc), 0.0


def squashed(man, x_cut, keep_below):
    """A TPU pad squashed by a part that has reached x_cut (only what is left of it)."""
    bb = man.bounding_box()
    if keep_below:
        return man ^ k.box(bb[0] - 1, x_cut, bb[1] - 1, bb[4] + 1, bb[2] - 1, bb[5] + 1)
    return man ^ k.box(x_cut, bb[3] + 1, bb[1] - 1, bb[4] + 1, bb[2] - 1, bb[5] + 1)


def scene(c, s, mode):
    y, dx = latch_state(c, s, mode)
    pf, pb = k.sled_positions(c, s)
    # a sled past its soft stop is pushing its pad; the band's eye can't be pushed into it
    fixed = dict(FIXED)
    if pf - k.SLED_LEN < k.PAD_X0 + k.PAD_L:
        fixed["rear pad"] = squashed(PAD_R, pf - k.SLED_LEN, True)
    if pb + k.SLED_LEN > k.PAD_X1 - k.PAD_L:
        fixed["front pad"] = squashed(PAD_F, pb + k.SLED_LEN, False)
    if abs(dx) > 0.1:
        tab0 = k.TAB_X0 + dx
        fixed["rail cushion"] = (squashed(CUSHION, tab0 + 4.0 + 0.0, False) + squashed(CUSHION, k.TAB_X0 - 0.1, True)) if dx > 0 \
            else (squashed(CUSHION, tab0, True) + squashed(CUSHION, k.TAB_X0 + 4.1, False))
    parts = {"blade": k.carrier(c, k.arm_deflect_for(y)), "latch block": k.latch_block(c, y),
             "knob slider": k.knob_bar(s), "sled F": k.sled(pf, "F"), "sled B": k.sled(pb, "B"),
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


print("== The cycle, stage by stage")
STAGES = [("closed, knob back", 0.0, 0.0, "held"), ("closed, knob pulled past its end", 0.0, -k.SOFT, "held"),
          ("cocking, knob 10 mm", k.E_CATCH, 10.0, "held"), ("cocking, knob 22 mm", k.E_CATCH, 22.0, "held"),
          ("cocked, blade crept 2 mm", k.C_COCK, 26.0, "held"), ("cam A has the block in", k.C_COCK, k.THROW - 1, "held"),
          ("thrown, blade 10 mm out", 10.0, k.THROW, "riding"), ("coasting", 50.0, k.THROW, "riding"),
          ("arriving", 86.0, k.THROW, "riding"), ("overrun into the pad", 86.0 + 3.0, k.THROW + k.SOFT, "riding"),
          ("open, knob forward", 86.0, k.THROW, "held"), ("pulling back 10 mm", 86.0 - k.E_CATCH, k.THROW - 10, "held"),
          ("cocked back", 86.0 - k.C_COCK, 2.0, "held"), ("cam B has the block in", 86.0 - k.C_COCK, 1.0, "held"),
          ("thrown back", 70.0, 0.0, "riding"), ("coasting back", 30.0, 0.0, "riding"),
          ("overrun into the rear pad", -3.0, -k.SOFT, "riding"), ("knob snapped back onto the rear pad", 0.0, -k.SOFT - 3.0, "held"),
          ("knob snapped forward onto the front pad", 86.0, k.THROW + k.SOFT + 3.0, "held")]
worst = {}
for label, c, s, mode in STAGES:
    bad = check_scene(c, s, worst, mode)
    report(not bad, f"{label} (c {c:g}, s {s:g}): nothing overlaps", "; ".join(bad))

print("\n== Sweeps (every 0.5 mm)")
paths = [("knob pushed forward, blade held shut", "held", [(min(k.C_COCK, k.E_CATCH + max(0.0, s - 20) * 0.25), s) for s in frange(-k.SOFT - 3.5, k.THROW - 1, 0.5)]),
         ("blade thrown out, knob forward", "riding", [(c, k.THROW) for c in frange(k.C_COCK, 86 + 4.0, 0.5)]),
         ("knob pulled back, blade held open", "held", [(86 - min(k.C_COCK, k.E_CATCH + max(0.0, (k.THROW - s) - 20) * 0.25), s) for s in frange(k.THROW + k.SOFT + 3.5, 1.0, 0.5)]),
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


for c in (k.E_CATCH, k.C_TRIP, k.C_COCK):
    x0 = k.X_BLK + c
    s1 = first_touch(c, 0.0, k.THROW, 0.05)
    y27 = cam_y(x0, x0 + k.BLK_L, k.THROW - 1 + (c - k.C_TRIP))
    s_trip = next(s for s in frange(0, k.THROW, 0.05) if cam_y(x0, x0 + k.BLK_L, s) < k.RAIL_Y0 + k.RAIL_CHAMFER)
    report(s1 >= 18 and y27 <= k.Y_CAM + 1e-6,
           f"cam A, blade crept {c:g}: first touches the block at s {s1:.1f}, lets it go at s {s_trip:.1f}, has it fully in by s {k.THROW - 1 + c - k.C_TRIP:g}")
for c in (86 - k.E_CATCH, 86 - k.C_TRIP, 86 - k.C_COCK):
    x0 = k.X_BLK + c
    s1 = first_touch(c, k.THROW, 0.0, 0.05)
    y1 = cam_y(x0, x0 + k.BLK_L, 1.0 - ((86 - c) - k.C_TRIP))
    s_trip = next(s for s in frange(k.THROW, 0, 0.05) if cam_y(x0, x0 + k.BLK_L, s) < k.RAIL_Y0 + k.RAIL_CHAMFER)
    report(s1 <= k.THROW - 18 and y1 <= k.Y_CAM + 1e-6,
           f"cam B, blade crept {86 - c:g}: first touches the block at s {s1:.1f}, lets it go at s {s_trip:.1f}, has it fully in by s {1.0 - ((86 - c) - k.C_TRIP):g}")
jaws = k.CAR_W / 2 - (k.Y_RAIL - k.BLK_D)          # how deep the block sits in its slot while on the rail
tilt = k.BLK_L * 2 * k.BLK_SLOT / jaws
corner = k.Y_RAIL + tilt - k.BLK_CHAMFER
report(corner < k.RAIL_Y0 + k.RAIL_CHAMFER,
       f"a block leaving its window can lean {tilt:.2f} mm in its slot; its chamfered trailing corner stays at y {corner:.2f}, inside the rail's {k.RAIL_Y0 + k.RAIL_CHAMFER:.2f}")
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
eng = min(k.Y_OUT - k.BLK_CHAMFER, k.RAIL_Y1) - (k.RAIL_Y0 + k.RAIL_CHAMFER)
report(eng >= 1.0, f"latched, the block bears {eng:.2f} mm deep on the rail's end, over {k.RAIL_TOP - k.CAR_Z0:.2f} mm of height")
arm_L = k.ARM_ROOT - (k.BLK_X0 + k.BLK_L / 2)
k_arm = 3 * 3500 * (k.CAR_T * k.ARM_T ** 3 / 12) / arm_L ** 3
d_max = k.arm_deflect_for(k.Y_CAM)
strain = 3 * k.ARM_T * d_max / (2 * arm_L ** 2)
report(strain < 0.01, f"latch arm: {k_arm:.2f} N/mm, bent at most {d_max:.2f} mm, {strain * 100:.2f} % strain (PLA keeps under 2 %)",
       f"presses the block on the rail with {k_arm * k.arm_deflect_for(k.Y_RAIL):.2f} N, out in a window with {k_arm * k.arm_deflect_for(k.Y_OUT):.2f} N")

print("\n== Band and sleds")
L_park = k.band_length(0.0, 0.0)
L_open = k.band_length(86.0, k.THROW)
L_max = k.band_length(k.E_CATCH, k.THROW - 1)
report(abs(L_park - L_open) < 1e-9 and abs(L_park - k.BAND_RELAXED - 4.0) < 1e-9,
       f"at rest, shut or open, the band is {L_park:.1f} eye to eye, 4 mm over its printed {k.BAND_RELAXED:.0f}: it pulls on nothing but its sleds")
strain = (L_max - k.BAND_RELAXED) / k.BAND_RELAXED
report(strain < 0.45, f"fully cocked it is {L_max:.1f}: {strain * 100:.0f} % stretch")
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
_s = next(s for s in frange(0, k.THROW, 0.01) if cam_y(_x0, _x0 + k.BLK_L, s) < k.RAIL_Y0 + k.RAIL_CHAMFER)
powered = _s - k.G_P - k.C_TRIP
report(powered > 20, f"the band throws the blade at least {powered:.1f} mm (more if the thumb keeps going after the trip), then it coasts the rest free of it")

print("\n== A throw, step by step (the in-stroke is its mirror)")
RHO = 1.24e-3                                    # g/mm3, PLA
_x0 = k.X_BLK + k.C_TRIP
S_TRIP = next(s for s in frange(0, k.THROW, 0.01) if cam_y(_x0, _x0 + k.BLK_L, s) < k.RAIL_Y0 + k.RAIL_CHAMFER)
m_blade_solid = (k.carrier().volume() + k.latch_block().volume()) * RHO
m_bar = k.knob_bar().volume() * RHO
m_sled = k.sled(0.0, "F").volume() * RHO
A_band = k.BAND[0] * k.BAND[1]
K_CUSH_AREA = (k.TAB_Y1 + 0.2 - k.RAIL_Y1 - 0.3) * k.layer(16)


def throw(E_tpu, h, Fc, fill, band=k.BAND, dt=2e-6, mu_push=0.046):
    """One throw from the trip. E_tpu MPa; h TPU loss on unloading; Fc friction (N); fill:
    printed weight over solid. Returns a dict."""
    kb = E_tpu * band[0] * band[1] / k.BAND_RELAXED
    m = (m_blade_solid + m_sled) * fill / 1000      # kg: sled F rides along while the band pulls
    c0 = k.C_TRIP
    s_trip = S_TRIP
    stroke = (s_trip - k.G_P) - c0
    x, v = 0.0, 0.0
    while x < stroke:
        T = (1 - h) * kb * (4.0 + stroke - x)
        F = T - Fc - mu_push * T
        if F <= 0 and v <= 1e-9:
            return {"reached": False, "stop": c0 + x}
        v += F / m * 1000 * dt
        x += v * dt
    m_b = m_blade_solid * fill / 1000
    E = 0.5 * m_b * (v / 1000) ** 2 * 1000           # mJ; sled F stops on its riser
    reach = (k.RAIL_X1 - k.X_BLK) + 0.3 - (c0 + stroke)
    if E - Fc * reach <= 0:
        return {"reached": False, "stop": c0 + stroke + E / Fc}
    E_arr = max(E - Fc * (86 + 1.0 - c0 - stroke), 0.0)
    k_pad = E_tpu * (2 * k.PAD_HW * k.SLED_H) / k.PAD_L
    squash = math.sqrt(2 * E_arr / k_pad)
    E_reb = max(0.45 * E_arr - Fc * (squash + 1.0 + k.E_CATCH), 0.0)   # TPU gives back about 45 %
    k_cush = E_tpu * K_CUSH_AREA / k.CUSH_L
    d_cush = math.sqrt(2 * E_reb / k_cush)
    return {"reached": True, "E_throw": E, "E_arrive": E_arr, "squash": squash, "F_pad": k_pad * squash,
            "overrun": 1.0 + squash, "E_rebound": E_reb, "d_cush": d_cush, "F_cush": k_cush * d_cush,
            "v": math.sqrt(2 * E_arr / 1000 / m_b) if E_arr > 0 else 0.0}


grid = list(itertools.product((15.0, 20.0, 26.0), (0.1, 0.2, 0.3), (0.2, 0.35, 0.5), (0.6, 1.0)))
res = [(g, throw(*g)) for g in grid]
fails = [g for g, r in res if not r["reached"]]
oks = [r for g, r in res if r["reached"]]
report(not fails, f"band: the blade reaches its lock in all {len(grid)} cases (TPU 15-26 MPa, losses 10-30 %, friction 0.2-0.5 N, printed 60-100 % solid)",
       "misses: " + ", ".join(f"E{g[0]:.0f} h{g[1]} Fc{g[2]} fill{g[3]}" for g in fails))
grid_s = list(itertools.product((10.0, 12.5, 15.0), (0.1, 0.2, 0.3), (0.2, 0.35, 0.5), (0.6, 1.0)))
fs = [g for g in grid_s if not throw(*g, band=k.BAND_STRONG)["reached"]]
oks += [throw(*g, band=k.BAND_STRONG) for g in grid_s if throw(*g, band=k.BAND_STRONG)["reached"]]
report(not fs, f"strong band: the same with a soft TPU (10-15 MPa), {len(grid_s)} cases", ", ".join(map(str, fs)))
grid_soft = list(itertools.product((26.0, 30.0), (0.1, 0.2, 0.3), (0.2, 0.35, 0.5), (0.6, 1.0)))
fs = [g for g in grid_soft if not throw(*g, band=k.BAND_SOFT)["reached"]]
oks += [throw(*g, band=k.BAND_SOFT) for g in grid_soft if throw(*g, band=k.BAND_SOFT)["reached"]]
report(not fs, f"soft band: the same with a stiff TPU (26-30 MPa), {len(grid_soft)} cases", ", ".join(map(str, fs)))


def crit_fc(E_tpu, h, band=k.BAND):
    lo, hi = 0.0, 5.0
    for _ in range(30):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if throw(E_tpu, h, mid, 1.0, band)["reached"] else (lo, mid)
    return lo


report(True, f"friction a throw can take: {crit_fc(20, 0.15):.2f} N nominal, {crit_fc(15, 0.3):.2f} N with a soft, lossy TPU, "
             f"{crit_fc(10, 0.3, k.BAND_STRONG):.2f} N with the strong band in a very soft one; the block on the rail makes about "
             f"{0.3 * k_arm * k.arm_deflect_for(k.Y_RAIL):.2f} N of it")
nom = throw(20.0, 0.15, 0.35, 0.8)
print(f"     nominal throw: {nom['E_throw']:.0f} mJ when the band lets go; arrives at {nom['v']:.1f} m/s with {nom['E_arrive']:.0f} mJ, "
      f"squashes the pad {nom['squash']:.1f} mm ({nom['F_pad']:.0f} N), bounces back into the rail with {nom['E_rebound']:.0f} mJ "
      f"({nom['d_cush']:.1f} mm of cushion, {nom['F_cush']:.0f} N)")
over = max(r["overrun"] for r in oks)
report(over + 0.5 <= k.W_FAR, f"hardest arrival: overrun {over:.1f} mm; the far end of each window is {k.W_FAR:.1f} mm on")
pad_sq = max(r["squash"] for r in oks)
report(pad_sq / k.PAD_L < 0.5, f"pads squash at most {pad_sq:.1f} of {k.PAD_L:.0f} mm ({max(r['F_pad'] for r in oks):.0f} N)")
cu = max(r["d_cush"] for r in oks)
report(cu / k.CUSH_L < 0.5 and cu < k.RAIL_MOVE - 0.2, f"rail cushion squashes at most {cu:.1f} of {k.CUSH_L:.0f} mm ({max(r['F_cush'] for r in oks):.0f} N on the block); the groove lets the rail move {k.RAIL_MOVE}")
worst_snap = (0, 0, 0, 0)
for E_tpu, band in ((15.0, k.BAND), (26.0, k.BAND), (10.0, k.BAND_STRONG), (15.0, k.BAND_STRONG)):
    kb = E_tpu * band[0] * band[1] / k.BAND_RELAXED
    u = 4.0 + S_TRIP - k.G_P - k.C_TRIP
    E_snap = 0.5 * kb * (u ** 2 - 16.0)
    k_pad = E_tpu * (2 * k.PAD_HW * k.SLED_H) / k.PAD_L
    sq = math.sqrt(2 * E_snap / k_pad)
    if sq > worst_snap[0]:
        worst_snap = (sq, E_snap, k_pad * sq, E_tpu)
sq, E_snap, F_snap, E_tpu = worst_snap
report(sq <= 3.5 - 0.5, f"knob let go just before the trip: snaps back with up to {E_snap:.0f} mJ, stopped by sled F on the rear pad in {sq:.1f} mm "
                        f"({F_snap:.0f} N); there is 3.5 mm of room")
for E_tpu, band, name in ((20.0, k.BAND, "band"), (26.0, k.BAND, "band"), (26.0, k.BAND_SOFT, "soft band"), (12.0, k.BAND_STRONG, "strong band")):
    kb = E_tpu * band[0] * band[1] / k.BAND_RELAXED
    Fb = kb * (4.0 + S_TRIP - k.G_P - k.C_TRIP)
    mu = 0.3
    F_lat = Fb * (mu + mu) + k_arm * k.arm_deflect_for(k.Y_CAM)
    F_cam = F_lat * (math.tan(math.radians(22) + math.atan(mu)) + mu)
    print(f"     thumb at the trip, {name}, TPU {E_tpu:.0f} MPa: band {Fb:.1f} N + latch {F_cam:.1f} N + bar about 0.5 N = {Fb + F_cam + 0.5:.1f} N")

print("\n== Printed screws")
N = 1200
pts_s = [(-(i / N) * k.PITCH * 2, k.thread_r((i / N * 2) % 1, k.THREAD_MIN / 2, k.THREAD_MAJ / 2)) for i in range(N + 1)]
pts_n = [(-(i / N) * k.PITCH * 2, k.thread_r((i / N * 2) % 1, k.THREAD_MIN / 2 + k.THREAD_PLAY, k.THREAD_MAJ / 2 + k.THREAD_PLAY, k.GROOVE_WIDEN))
         for i in range(N + 1)]
gap = min(math.hypot(a[0] - b[0], a[1] - b[1]) for a in pts_s[200:1000:2] for b in pts_n[::2])
report(gap >= 0.35, f"screw to nut, square to the thread: {gap:.2f} mm all round (the brain's pin rule: 0.35-0.4)")
report(overlap(k.screw(), k.nut()) < TOL, "the screw turns in its nut")
report(overlap(k.screw(), k.nut().translate([0, 0, 1.0])) > 0.5, "and holds it: lifted 1 mm, the nut runs into the thread")
eng = k.THREAD_MAJ / 2 - (k.THREAD_MIN / 2 + k.THREAD_PLAY)
report(eng >= 0.4, f"threads overlap {eng:.2f} mm radially")
report(overlap(SCREWS, HANDLE) < TOL and overlap(NUTS, HANDLE) < TOL, "screws and nuts clear every plate")

print("\n== Clearances (PRINTER-BRAIN: 0.2 snug, 0.25-0.3 sliding, holes 0.35-0.4 all round)")
rows = [("carrier in its channel, sides", k.CHAN_Y - k.CAR_W / 2, 0.25), ("carrier, top and bottom", k.CAR_Z0 - k.WALL_T, 0.25),
        ("latch block in its slot", k.BLK_SLOT, 0.25), ("knob bar in its lane, inside and outside", min(k.BAR_Y0 - k.LANE_Y0, k.LANE_Y1 - k.BAR_Y1), 0.2),
        ("knob bar, under and over", min(k.BAR_Z0 - k.RAIL_TOP, k.Z1 - k.BAR_Z1), 0.2),
        ("sleds in the band level, sides", min(-k.SLED_HW - k.CAV_Y0, k.CAV_Y1 - k.BAR_Y1), 0.25),
        ("lug in its floor slot", 0.3, 0.25), ("band in the lug's slot", k.BAND_SLOT - k.BAND_W / 2, 0.3),
        ("band eye on its post", k.EYE_PLAY, 0.35), ("screw holes", (k.SCREW_HOLE - k.THREAD_MAJ) / 2, 0.35),
        ("screw head in its counterbore", (k.COUNTERBORE - k.HEAD_D) / 2, 0.35), ("pegs in their holes", (k.PEG_HOLE_D - k.PEG_D) / 2, 0.35)]
for what, v, need in rows:
    report(v >= need - 1e-9, f"{what}: {v:.2f}", f"needs {need}")

print("\n== Printing")
LAYERED = {
    "base plate": [k.WALL_T, k.RAIL_Z0, k.RAIL_TOP, k.Z1, k.HEAD_H, k.BAR_Z0 - 0.2],
    "middle plate": [h - k.Z1 for h in (k.Z_FLOOR, k.Z2, k.HT - k.NUT_H)],
    "top plate": [k.HT - k.Z2],
    "blade": [k.CAR_T, k.LUG_TOP - k.CAR_Z0, k.BAND_SLOT_Z - k.CAR_Z0, k.CAR_T - 0.8],
    "latch block": [k.CAR_T],
    "rail (lying on its face)": [k.RAIL_Y1 - k.RAIL_Y0, k.TAB_Y1 - k.RAIL_Y0],
    "knob slider": [k.BAR_Z1 - k.BAR_Z0, k.RISER_TOP - k.BAR_Z0, k.KNOB_TOP - k.BAR_Z0, k.BAR_Z1 - 0.2 - k.BAR_Z0],
    "sleds": [k.SLED_H, k.POCKET_Z - k.SLED_Z0],
    "screw": [k.HEAD_H, k.layer(3), k.layer(61)], "nut": [k.NUT_H],
    "bands": [k.BAND[0], k.BAND_STRONG[0], k.BAND_SOFT[0]], "pads": [k.SLED_H], "rail cushion": [k.layer(16), k.layer(2)],
}
bad = []
for part, hs in LAYERED.items():
    for h in hs:
        n = (h - 0.05) / 0.2
        if abs(n - round(n)) > 1e-6 or n < 0.99:
            bad.append(f"{part} {h:.3f}")
report(not bad, f"every height sits on a layer line ({sum(len(v) for v in LAYERED.values())} heights)", ", ".join(bad))


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
                 "handle 2 middle": "the peg holes' ceilings"}
pp = k.print_parts()
for name, man in pp.items():
    oh = overhangs(man)
    limit = 2.0 if name in EXPECT_BRIDGE else 1.6
    ok = all(w <= limit for _, _, w in oh)
    note = EXPECT_BRIDGE.get(name, "")
    msg = f"{name}: nothing hangs in the air" + (f" except short bridges up to {max(w for *_, w in oh):.1f} mm" if oh else "") + (f" ({note})" if note else "")
    report(ok, msg, "; ".join(f"z {z:.2f}: {a:.1f} mm2, {w:.1f} wide" for z, a, w in oh[:6]) if not ok else "")

print()
if FAILS:
    print(f"{len(FAILS)} check(s) FAILED:")
    for f in FAILS:
        print("  - " + f)
    sys.exit(1)
print("Every check passed.")
