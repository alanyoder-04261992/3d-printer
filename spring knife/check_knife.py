"""Checks the double-action spring knife works before anything is printed.

Run:  python3 check_knife.py
Each line says what it proved. Anything that fails is marked FAIL.

The states it walks through, with c the blade's travel, s the knob's and p the pushrod's:
  closed, resting       c = 0,  s = 5,  p = 0
  knob pushed forward   c = 0,  s = 96, p = 12   (the bump lets the blade go near s = 84 to 96)
  open, resting         c = 86, s = 91, p = 12
  knob pulled back      c = 86, s = 0,  p = 0    (the bump lets the blade go near s = 12 to 0)
"""

import sys

import make_knife as k

fails = 0


def report(ok, words):
    global fails
    fails += 0 if ok else 1
    print(("ok   " if ok else "FAIL ") + words)


def overlap(a, b):
    return (a ^ b).volume()


T, P, SM, E = k.TRAVEL, k.P_MOVE, k.S_MAX, k.E_REST
plates = [k.plate1(), k.plate2(), k.plate3(), k.plate4()]
handle = k.union(plates)

# 1. every printed piece is one solid piece and fits the bed; the plates stack cleanly
for name, man in k.print_parts().items():
    bb = man.bounding_box()
    report(len(man.decompose()) == 1 and bb[3] - bb[0] <= 210 and bb[4] - bb[1] <= 210,
           f"{name}: one solid piece, {bb[3]-bb[0]:.1f} x {bb[4]-bb[1]:.1f} mm, fits the bed")
worst = max(overlap(plates[i], plates[j]) for i in range(4) for j in range(i + 1, 4))
report(worst < 0.01, f"the four handle plates stack, touching only face to face ({worst:.4f} mm3), pegs in their holes")

# 2. heights on layer lines, measured from the face each part prints on
def on_grid(z):
    return abs((z - 0.05) / 0.2 - round((z - 0.05) / 0.2)) < 1e-6

heights = {
    "base plate": k.Z1, "channel plate": k.Z2 - k.Z1, "band deck": k.Z3 - k.Z2, "top plate": k.HT - k.Z3,
    "walls": k.WALL_T, "chamfer": k.CHAMFER, "channel ceiling (channel plate)": k.CHAN_TOP - k.Z1,
    "band B level (band deck)": k.LEVEL_B[1] - k.Z2, "pin groove (top plate, from outside)": k.HT - k.LEVEL_F[1] - k.GROOVE,
    "carrier": k.CAR_T, "pushrod": k.PUSH_H, "backing wall top (channel plate)": k.CHAN_TOP - k.Z1, "bumps": k.BUMP_H, "roller": k.ROLLER_H, "band": k.BAND_H,
    "slider (from its top)": k.SHUT_TOP - k.SHUT_Z0, "slider upper part": k.SHUT_TOP - k.SHUT_UP_Z0,
    "slider middle": k.SHUT_TOP - k.SHUT_MID[0], "screw head": k.HEAD_H, "nut": k.NUT_H, "peg holes": k.PEG_HOLE_H,
}
bad = [n for n, z in heights.items() if not on_grid(z)]
report(not bad, "every height sits on a layer line" + (f": off: {bad}" if bad else ""))

# 3. the blade slides all the way, stops at both ends
worst = 0.0
for i in range(0, 87):
    body, _ = k.carrier_parts(min(i, T))
    worst = max(worst, overlap(handle, body))
report(worst < 1e-6, f"blade and carrier slide the whole {T:.0f} mm without rubbing the handle")
report(overlap(handle, k.carrier_parts(-0.5)[0]) > 0.01, "the back of the channel stops the blade just past closed")
report(overlap(handle, k.carrier_parts(T + 0.5)[0]) > 0.01, "the carrier's shoulders stop on the front wall when open")

# 4. the tooth locks it closed and open
for c, words in ((0, "closed"), (T, "open")):
    _, tooth = k.carrier_parts(c)
    report(overlap(handle, tooth) < 1e-6, f"{words}: the tooth sits in its window")
report(overlap(handle, k.carrier_parts(0.5)[1]) > 0.01, "closed: the tooth holds the blade in while band F is stretched")
report(overlap(handle, k.carrier_parts(T - 0.5)[1]) > 0.01, "open: the tooth holds the blade out while band B is stretched")

# 5. the pushrod: slides in its lane, its bumps rest clear of the windows, and it frees the tooth
worst = max(overlap(handle, k.pushrod(p)) for p in [i * 0.5 for i in range(25)])
report(worst < 1e-6, "the pushrod slides its 12 mm without touching the handle")
worst = max(overlap(k.carrier_parts(c)[0], k.pushrod(p)) for c in (0, T) for p in (0, 3, 6, 9, 12))
report(worst < 1e-6, "the pushrod's bumps pass the carrier without rubbing it")


def push_needed(tooth, rod):
    """How far the tooth has to be pushed in (y) to clear the rod: the bump's push."""
    lo, hi = 0.0, 3.0
    if overlap(tooth, rod) < 1e-9:
        return 0.0
    for _ in range(30):
        mid = (lo + hi) / 2
        if overlap(tooth.translate([0, -mid, 0]), rod) < 1e-9:
            hi = mid
        else:
            lo = mid
    return hi


lock = k.CAR_W / 2 + k.TOOTH_OUT - k.CHAN_Y          # how deep the tooth sits in the wall
for c, rest, end, words in ((0, 0, P, "forward"), (T, P, 0, "backward")):
    _, tooth = k.carrier_parts(c)
    pushes = [(p, push_needed(tooth, k.pushrod(p))) for p in [i * 0.25 for i in range(49)]]
    best_p, best = max(pushes, key=lambda x: x[1])
    report(push_needed(tooth, k.pushrod(rest)) == 0 and push_needed(tooth, k.pushrod(end)) == 0,
           f"{words}: with the pushrod at rest either side, the bump leaves the tooth alone")
    report(best >= lock + 0.1,
           f"{words}: crossing over, the bump pushes the tooth {best:.2f} mm in, {best - lock:.2f} mm clear of the wall")
    moved = tooth.translate([1.0 if c == 0 else -1.0, -best, 0])
    report(overlap(handle, moved) < 1e-6, f"{words}: pushed in, the blade is free to go")
    # the tooth pushes back: the pushrod gives until the backing wall stops it
    play = k.WALL_Y0 - k.PUSH_Y1
    shoved = k.pushrod(best_p).translate([0, play + 0.02, 0])
    report(overlap(handle, shoved) > 0.001, f"{words}: the backing wall stops the pushrod within {play:.2f} mm")
    worst_case = push_needed(tooth, k.pushrod(best_p).translate([0, play, 0]))
    report(worst_case >= lock + 0.05,
           f"{words}: even pushed back against that wall, the bump frees the tooth by {worst_case - lock:.2f} mm")
deepest = 0.0
for c in range(1, int(T)):
    _, tooth = k.carrier_parts(c)
    deepest = max(deepest, push_needed(tooth, handle), push_needed(tooth, k.pushrod(0)), push_needed(tooth, k.pushrod(P)))
report(deepest <= k.ARM_GAP - 0.1, f"the latch arm bends at most {deepest:.2f} mm, with {k.ARM_GAP} mm of room")
strain = 3 * k.ARM_T * max(deepest, 1.15) / (2 * (k.ARM_X1 - k.ARM_X0) ** 2)
report(strain < 0.02, f"the latch arm bends {strain * 100:.2f} % (PLA keeps under 2 %)")

# 6. the slider: runs its 96 mm in its lane, stops at the ends of the knob slot, drives the pushrod
worst = max(overlap(handle, k.shuttle(s)) for s in range(0, 97, 2))
report(worst < 1e-6, f"the slider runs its {SM:.0f} mm without touching the handle")
report(overlap(handle, k.shuttle(-0.5)) > 0.01 and overlap(handle, k.shuttle(SM + 0.5)) > 0.01,
       "the knob stops at both ends of its slot")
fwd = [(s, min(max(s - (SM - P), 0), P)) for s in range(0, 97, 2)]
back = [(s, min(max(s, 0), P)) for s in range(96, -1, -2)]
worst = max(overlap(k.shuttle(s), k.pushrod(p)) for s, p in fwd + back)
report(worst < 1e-6, "going forward and back, the slider and the pushrod never jam")
report(overlap(k.shuttle(SM - P + 0.5), k.pushrod(0)) > 0.01, "near the front of its stroke the slider pushes the pushrod forward")
report(overlap(k.shuttle(P - 0.5), k.pushrod(P)) > 0.01, "near the back of its stroke the slider pulls the pushrod back")
worst = max(overlap(k.shuttle(s), k.carrier(c)) for s in range(0, 97, 8) for c in (0, 43, T))
report(worst < 1e-6, "the slider and the blade pass each other")

# 7. pins and rollers
worst = max(overlap(handle, k.blade_pin(c)) for c in range(0, 87, 2))
report(worst < 1e-6, "the blade pin rides its slots and the groove in the top wall the whole way")
worst = max(overlap(handle, k.slider_pin(s)) for s in range(0, 97, 4))
report(worst < 1e-6, "the knob pin rides along with the slider")
report(overlap(k.blade_pin(), k.carrier()) < 1e-6 and overlap(k.slider_pin(), k.shuttle()) < 1e-6,
       "both pins press into holes their own size (holes print small, so they grip)")
rollers = k.rollers()
report(overlap(handle, rollers) < 1e-6, "the four rollers sit on their posts without touching the handle")
worst = max(overlap(rollers, k.carrier(c) + k.blade_pin(c)) for c in range(0, 87, 4))
worst = max(worst, max(overlap(rollers, k.shuttle(s) + k.slider_pin(s)) for s in range(0, 97, 4)))
report(worst < 1e-6, "the blade, slider and pins pass the rollers")

# 8. the bands at the four points of a cycle
states = [(0, 5, 0, "closed, resting"), (0, SM, P, "knob forward, about to fire"),
          (T, SM - E, P, "open, resting"), (T, 0, 0, "knob back, about to fire")]
for c, s, p, words in states:
    bf, bb = k.band_fitted("F", c, s), k.band_fitted("B", c, s)
    hard = handle + k.carrier(c) + k.shuttle(s) + k.pushrod(p)
    v = overlap(hard, bf) + overlap(hard, bb) + overlap(bf, bb)
    report(v < 1e-6, f"{words}: both bands clear the handle, blade, slider and pushrod")
    v = overlap(rollers + k.blade_pin(c) + k.slider_pin(s), bf + bb)
    report(v < 0.05, f"{words}: the bands wrap the rollers and pins without cutting into them ({v:.4f} mm3 of facet slivers)")

lengths = {(kind, c, s): k.band_length(kind, c, s) for kind in "FB" for c, s, _, _ in states}
shortest, longest = min(lengths.values()), max(lengths.values())
report(shortest > k.BAND_RELAXED, f"the bands stay tight all round: shortest {shortest:.0f} mm against {k.BAND_RELAXED:.0f} printed")
report(longest / k.BAND_RELAXED - 1 < 1.0,
       f"they stretch {shortest / k.BAND_RELAXED * 100 - 100:.0f} % to {longest / k.BAND_RELAXED * 100 - 100:.0f} % (printed TPU stretches several times that)")
pull_at_fire = (k.slider_pin_x(SM - P + 3) - (k.C0 + k.C_PIN_X)) * 2
report(pull_at_fire > 150, f"when the blade is let go the knob pin is {pull_at_fire / 2:.0f} mm ahead of the blade pin, "
       f"so band F is stretched that much more than band B and the pull is forward")
eq = (SM - P + 3) - E
report(eq >= T - 6, f"let go near s = {SM - P + 3:.0f}, the blade is pulled to {eq:.0f} of its {T:.0f} mm, "
       f"and the last of the knob's stroke pulls it to the stop")

# 9. printed screws and nuts
for x, y in k.SCREWS:
    sc, nt = k.screw(x, y), k.nut(x, y)
    v1 = overlap(handle, sc)
    v2 = overlap(plates[3], nt)
    v3 = overlap(sc, nt)
    report(v1 < 1e-6 and v2 < 1e-6, f"screw at ({x:.0f}, {y:.0f}): clears every plate, nut sits in its pocket")
    report(v3 < 0.05 and overlap(sc, nt.translate([0, 0, -0.6])) > 0.5,
           f"screw at ({x:.0f}, {y:.0f}): threads mesh with the nut ({v3:.3f} mm3 of facet slivers) and lock it")

# 10. clearances follow PRINTER-BRAIN's rule
report(k.PIN_PLAY >= 0.35, f"band eyes, roller bores and pin slots: {k.PIN_PLAY} mm all round")
report(k.GAP >= 0.25, f"blade in the channel: {k.GAP} mm each side")
report(k.THREAD_PLAY >= 0.25 and k.SCREW_HOLE - k.THREAD_MAJ >= 0.7,
       f"nut threads {k.THREAD_PLAY} mm bigger all round; screw holes {k.SCREW_HOLE} mm for a {k.THREAD_MAJ:.0f} mm screw")

print()
print("all checks passed" if fails == 0 else f"{fails} check(s) failed")
sys.exit(1 if fails else 0)
