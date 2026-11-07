"""Checks the spring knife works before anything is printed.

Run:  python3 check_knife.py
Each line says what it proved. Anything that fails is marked FAIL.
"""

import math
import sys

import make_knife as k

fails = 0


def report(ok, words):
    global fails
    fails += 0 if ok else 1
    print(("ok   " if ok else "FAIL ") + words)


def overlap(a, b):
    return (a ^ b).volume()


bottom, top = k.handle_bottom(), k.handle_top()
handle = bottom + top
T = k.TRAVEL

# 1. every printed piece is one solid piece and fits the bed
parts = k.print_parts()
for name, man in parts.items():
    bb = man.bounding_box()
    n = len(man.decompose())
    report(n == 1, f"{name}: one solid piece")
    report(bb[3] - bb[0] <= 210 and bb[4] - bb[1] <= 210, f"{name}: {bb[3]-bb[0]:.1f} x {bb[4]-bb[1]:.1f} mm fits the bed")
report(abs(overlap(bottom, top)) < 1e-6, "the two handle halves meet without overlapping")

# 2. heights on layer lines, measured from the face each part prints on
def on_grid(z):
    return abs((z - 0.05) / 0.2 - round((z - 0.05) / 0.2)) < 1e-6

heights = {
    "half thickness": k.SPLIT, "outer walls": k.WALL_T, "channel floor": k.CHAN_Z0,
    "band cavity top": k.CAV_Z1, "post tops": k.POST_TOP, "chamfer": k.CHAMFER,
    "carrier thickness": k.CAR_T, "tooth (from carrier bottom)": k.TOOTH_Z0 - k.CAR_Z0,
    "tab bottom (from top face)": k.HT - k.TAB_Z0, "tab top (from top face)": k.HT - k.TAB_Z1,
    "slit top (from top face)": k.HT - k.SLIT_TOP, "nub (from top face)": k.HT - k.NUB_Z0,
    "nub top (from top face)": k.HT - k.NUB_Z1, "window top (from top face)": k.HT - k.WIN_Z1,
    "screw head pocket": k.HEAD_DEPTH, "roller": k.ROLLER_H, "band": k.BAND_H,
}
bad = [n for n, z in heights.items() if not on_grid(z)]
report(not bad, "every height sits on a layer line (0.25 first layer, then 0.2)" + (f": off: {bad}" if bad else ""))

# 3. the carrier and blade slide all the way without touching the handle (tooth aside)
worst = 0.0
for i in range(0, 87):
    body, _ = k.carrier_parts(min(i, T))
    worst = max(worst, overlap(handle, body))
report(worst < 1e-6, f"blade and carrier slide the whole {T:.0f} mm without rubbing the handle")
body0, _ = k.carrier_parts(-0.5)
report(overlap(handle, body0) > 0.01, "the back of the channel stops the carrier just past closed")
bodyT, _ = k.carrier_parts(T + 0.5)
report(overlap(handle, bodyT) > 0.01, "the carrier's shoulders stop against the front wall when open")

# 4. the latch tooth sits in a window when closed and when open, and holds
for at, words in ((0, "closed"), (T, "open")):
    _, tooth = k.carrier_parts(at)
    report(overlap(handle, tooth) < 1e-6, f"{words}: the tooth sits in its window")
_, t = k.carrier_parts(0.5)
report(overlap(handle, t) > 0.01, "closed: the tooth stops the bands pulling the blade out")
_, t = k.carrier_parts(T - 0.5)
report(overlap(handle, t) > 0.01, "open: the tooth stops the blade being pushed back in")

# between the windows the wall pushes the tooth in; the arm must have room to bend that far
deepest = 0.0
for i in range(1, 86):
    _, tooth = k.carrier_parts(i)
    hit = handle ^ tooth
    if hit.volume() > 1e-6:
        deepest = max(deepest, k.CAR_W / 2 + k.TOOTH_OUT - hit.bounding_box()[1])
report(deepest <= k.ARM_GAP - 0.1, f"between the windows the arm bends in {deepest:.2f} mm, with {k.ARM_GAP} mm of room")
arm_strain = 3 * k.ARM_T * deepest / (2 * (k.ARM_X1 - k.ARM_X0) ** 2)
report(arm_strain < 0.02, f"the latch arm bends {arm_strain * 100:.2f} % (PLA keeps under 2 %)")

# 5. pressing a button pushes the tooth clear, and the tab doesn't hit anything
y_tab = k.CHAN_Y + k.SKIN + k.POCKET
for ((ta, tb, free), (w0, w1)), words, at in zip(k.tabs(), ("rear (fire)", "front (close)"), (0, T)):
    lo, hi = min(ta, tb), max(ta, tb)
    y_skin = k.CHAN_Y + k.SKIN          # the tab and its nub are everything outside the skin
    tab_all = top ^ k.box(lo, hi, y_skin + 0.001, k.HW / 2 + 1, k.SPLIT, k.TAB_Z1 + 0.01)
    end = (hi - 7, hi) if free == hi else (lo, lo + 7)
    free_end = top ^ k.box(end[0], end[1], y_skin + 0.001, k.HW / 2 + 1, k.SPLIT, k.TAB_Z1 + 0.01)
    rest = top - tab_all
    pressed = free_end.translate([0, -k.PRESS, 0])
    report(overlap(rest, pressed) < 1e-6, f"{words} button presses in {k.PRESS} mm without hitting the wall behind it")
    nub_in = pressed.bounding_box()[1]
    _, tooth = k.carrier_parts(at)
    pushed = tooth.translate([0, -(k.CAR_W / 2 + k.TOOTH_OUT - nub_in), 0])
    moved = pushed.translate([0.8 if at == 0 else -0.8, 0, 0])
    report(nub_in < k.CHAN_Y and overlap(handle, moved) < 1e-6,
           f"{words} button pushes the tooth {k.CHAN_Y - nub_in:.2f} mm past the wall, so the blade moves")
    strain = 3 * (k.HW / 2 - y_tab) * k.PRESS / (2 * k.TAB_L ** 2)
    report(strain < 0.02, f"{words} button bends {strain * 100:.2f} % (under 2 %)")

# 6. pin, rollers and bands fit and stay clear all the way
worst = max(overlap(handle, k.pin(min(i, T))) for i in range(0, 87, 2))
report(worst < 1e-6, "the band pin rides in the band cavities the whole way")
report(overlap(handle, k.rollers()) < 1e-6, "the rollers sit on their posts without touching the handle")
worst = max(overlap(k.rollers(), k.carrier(i)) for i in range(0, 87, 2))
report(worst < 1e-6, "the blade and carrier pass under the rollers")
for at, words in ((0, "closed"), (T, "open")):
    v = overlap(handle, k.bands_fitted(at)) + overlap(k.carrier(at), k.bands_fitted(at))
    report(v < 1e-6, f"{words}: both bands fit their cavities without touching the handle or blade")
    # the band wraps tight on its roller, so the two round faces touch; their flat facets
    # (48 and 64 sides) leave slivers of a few ten-thousandths of a mm3
    v = overlap(k.pin(at), k.bands_fitted(at)) + overlap(k.rollers(), k.bands_fitted(at))
    report(v < 0.05, f"{words}: the bands wrap round the rollers and pin without cutting into them ({v:.4f} mm3 of facet slivers)")

# 7. clearances follow the rule: holes 0.35 to 0.4 mm bigger all round
play = k.HOLE_PLAY
report(0.35 <= play <= 0.4, f"pin hole, roller bores and band eyes are {play} mm bigger all round than what goes in them")
report(k.GAP >= 0.25, f"the carrier and blade have {k.GAP} mm each side in the channel and slot")
report(k.CHAN_Z0 < k.CAR_Z0 and k.CAR_Z0 - k.CHAN_Z0 >= 0.25,
       f"{k.CAR_Z0 - k.CHAN_Z0:.3f} mm above and below the carrier")

# 8. the bands: how far they stretch
for t, words in ((k.BAND_T, "band"), (k.BAND_T_FIRM, "firm band")):
    open_len = k.band_path(k.ANCHOR_X, k.CLOSED_X + T + k.PIN_X, t)
    shut_len = k.band_path(k.ANCHOR_X, k.CLOSED_X + k.PIN_X, t)
    s_open, s_shut = open_len / k.BAND_RELAXED - 1, shut_len / k.BAND_RELAXED - 1
    report(0 < s_open and s_shut < 0.8,
           f"{words}: stretched {s_open * 100:.0f} % when open (still pulling) and {s_shut * 100:.0f} % when closed (TPU takes several times that)")

print()
print("all checks passed" if fails == 0 else f"{fails} check(s) failed")
sys.exit(1 if fails else 0)
