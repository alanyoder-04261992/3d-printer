"""Checks the shed model fits together before anything is printed.

Run:  python3 check_shed.py
Each line says what it proved. Anything that fails is marked FAIL.
"""

import math
import sys

import numpy as np

import make_shed as s

BED = 220.0
fails = 0


def report(ok, words):
    global fails
    fails += 0 if ok else 1
    print(("ok   " if ok else "FAIL ") + words)


def overlap(a, b):
    return (a ^ b).volume()


p = s.build()
body, roof, door, trim = p["body"], p["roof"], p["door"], p["door_trim"]
door_all = door + trim

# 1. every printed piece is one solid piece and fits the bed
for name, part in (("body", body), ("roof half", s.roof_to_print(roof)), ("door", door_all),
                   ("skids", p["skids"]), ("fit test", p["fit"])):
    bb = part.bounding_box()
    size = (bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2])
    pieces = len(part.decompose())
    expect = {"skids": 2, "fit test": 4}.get(name, 1)
    report(pieces == expect, f"{name}: {pieces} solid piece(s), expected {expect}")
    report(max(size[0], size[1]) <= BED and size[2] <= BED,
           f"{name}: {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm fits the {BED:.0f} mm bed")

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

# 6. heights at full size, as a sanity check against the shop numbers
inch = 1 / s.S
report(abs(s.WALL_H * inch - 93.5) < 0.01, f"walls {s.WALL_H * inch:.1f} in floor to plate top (shop: 93 1/2 in)")
report(abs((s.ZPK - s.ZWT) / (s.W / 2) - 5 / 12) < 1e-9, "roof is 5/12")
report(abs(s.DOOR_OPEN_W * inch - 48.25) < 0.01 and abs(s.DOOR_OPEN_H * inch - 76.5) < 0.01,
       "door opening 48 1/4 x 76 1/2 in")

print()
print("all checks passed" if fails == 0 else f"{fails} check(s) failed")
sys.exit(1 if fails else 0)
