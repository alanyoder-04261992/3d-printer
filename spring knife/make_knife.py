"""Double-action spring knife toy for the Flashforge AD5X, designed from scratch.

Run:  python3 make_knife.py      (needs: pip install manifold3d numpy)

A blunt plastic fidget toy. Slide the knob on the side forward: two printed TPU bands
stretch, and at the end of the stroke the blade is let go and snaps out until it locks open.
Slide the knob back: the bands stretch the other way and the blade snaps back in. Every part
is printed, the screws and nuts too.

How it works
  * Band F (top level) runs from the blade's pin forward round a front roller, back round a
    rear roller and forward to the knob's pin. Band B (lower level) is its mirror. Slide the
    knob forward and band F stretches while the blade is held; slide it back and band B does.
  * The blade is held by a tooth on a springy arm, sitting in a window in the handle wall:
    one window for closed, one for open.
  * A pushrod lies beside the blade. The knob's shuttle moves it 12 mm at each end of its
    stroke, and a bump on the pushrod rides over the tooth, pushes it out of its window and
    lets the blade go. The bumps rest beside the windows, so the tooth can drop back in.

Parts (print files in this folder)
  handle 1 base.stl ... handle 4 top.stl   four plates, stacked and held by four screws
  blade.stl                                blade and carrier, with the latch arm
  slider.stl                               shuttle with its knob, printed upside down
  pushrod.stl                              the release bar with its two bumps
  pin long.stl, pin short.stl              blade pin and knob pin, pressed in
  roller.stl (print 4), screw.stl (4), nut.stl (4)
  band.stl (print 2, TPU), band soft.stl   a gentler pair
  1 knife plates.3mf    Flash Studio project: handle, small parts (black), blade and slider (white)
  2 bands (TPU).3mf     the two bands; pick your TPU filament before slicing

Axes for the assembled knife: x along it (the blade comes out at +x), y across it (the knob is
on +y), z through it (z = 0 is the outside of the base plate). Drawn closed: blade at c = 0,
knob at s = 5, pushrod at p = 0.
"""

import math
import os
import struct
import zipfile
from xml.sax.saxutils import quoteattr

import numpy as np
import manifold3d as m3

M = m3.Manifold
HERE = os.path.dirname(os.path.abspath(__file__))


def layer(n):
    """Top of layer n from the face a part prints on (first layer 0.25, then 0.2)."""
    return 0.05 + 0.2 * n


# ---------------------------------------------------------------- handle plates
HL, HW = 178.0, 38.0
CORNER_R = 6.0
CHAMFER = layer(7)                  # 1.45 round the two outside faces
WALL_T = layer(11)                  # 2.25 bottom and top walls
Z1 = layer(23)                      # 4.65  base plate / channel plate (through the middle of the blade)
Z2 = Z1 + layer(15)                 # 7.70  channel plate / band deck
Z3 = Z2 + layer(22)                 # 12.15 band deck / top plate
HT = Z3 + layer(27)                 # 17.60

# ---------------------------------------------------------------- blade and carrier
CAR_L, CAR_W, CAR_T = 55.0, 22.0, layer(21)    # carrier 55 x 22 x 4.25
BLADE_L, BLADE_W = 90.0, 18.0
CAR_Z0 = WALL_T + 0.275             # 2.525: 0.275 over the channel floor
GAP = 0.3                           # sliding gap at the sides
CHAN_Y = CAR_W / 2 + GAP            # 11.3
SLOT_Y = BLADE_W / 2 + GAP          # 9.3
CHAN_TOP = Z1 + layer(12)           # 7.10: channel ceiling, 0.325 over the carrier
FLOOR_TOP = Z2                      # the channel plate's floor, 0.6 thick, under the bands
FRONT_IN = 166.0
C0 = 25.0                           # carrier's back end, closed
REAR_STOP = C0 - 0.4
TRAVEL = FRONT_IN - CAR_L - C0      # 86

# latch: an arm cut from the carrier's +y side, a tooth that drops into a window
ARM_X0, ARM_X1 = 14.0, 40.0         # free end at ARM_X0
ARM_T, ARM_GAP = 1.6, 1.4
TOOTH_L, TOOTH_OUT = 4.0, 1.3       # tooth reaches 1.0 into the wall
WIN_PAD = 0.3

# pushrod: lies in the channel plate beside the blade; bumps push the tooth in
PUSH_Z0 = Z1 + 0.1                  # 4.75
PUSH_H = layer(11)                  # 2.25: under the floor, which bridges over it to the backing wall
BUMP_H = layer(10)                  # 2.05: bumps cover the tooth's top half (4.65 to 6.775)
BUMP_IN = CAR_W / 2 + 0.1           # 11.10: a bump pushes the tooth this far in
PUSH_Y0, PUSH_Y1 = 12.45, 13.85     # pushrod body
LIP_Y = 12.35                       # inner edge of the pushrod's lane
WALL_Y0, WALL_Y1 = PUSH_Y1 + 0.1, PUSH_Y1 + 0.8   # backing wall: the tooth can't push the pushrod away
                                    # more than 0.1 mm; gaps in it at the ends let the dogs through
RAMP, FLAT = 2.5, 1.0               # each bump: ramp, flat top, ramp
P_MOVE = 12.0                       # pushrod moves this far at each end of the knob's stroke

# shuttle and knob
E_REST = 5.0                        # knob pin sits 5 mm behind the blade pin at closed rest
S_MAX = TRAVEL + 2 * E_REST         # 96: knob travel
S_PIN_Y = 13.5                      # knob pin: band strands 3 run at this y
SHUT_BACK, SHUT_FRONT = 4.0, 10.0   # shuttle reaches this far behind and in front of its pin
SHUT_Y_LOW = WALL_Y1 + 0.1          # 14.75: shuttle's lower part, outside the backing wall
LOW_BACK, LOW_FRONT = 9.0, 25.0     # the lower part reaches past the wall's ends to the dogs
SHUT_Y_UP = 11.4                    # shuttle's upper part (over the pushrod)
SHUT_Y1 = 16.5
LANE_Y1 = 16.6                      # outer wall starts here
STEM_Z0, STEM_Z1 = 5.0, 7.5

# bands
PIN_D = 3.0                         # both pins, pressed into their parts (holes print small)
PIN_PLAY = 0.4                      # band eyes and slots: 0.4 all round
C_PIN_X, C_PIN_Y = 8.0, -0.5        # blade pin on the carrier
X_B, X_F = 18.0, 158.0              # rear and front rollers
Y_LO, Y_HI = 3.0, 10.0
ROLLER_D = 6.0
ROLLER_H = layer(13)                # 2.65
POST_D = 3.0
BAND_T, BAND_T_SOFT = 1.0, 0.8
BAND_H = layer(12)                  # 2.45
BAND_RELAXED = 205.0                # printed length, eye to eye
CAV_X0, CAV_X1 = 12.0, 164.0
CAV_Y0 = -4.0
LEVEL_B = (Z2, Z2 + layer(15))      # 7.70 to 10.75
LEVEL_F = (Z3, HT - WALL_T)         # 12.15 to 15.35
GROOVE = WALL_T - layer(8)          # pin groove in the top wall: 0.6 deep, leaving 1.65

# printed screws: M6-ish, 2 mm pitch, nuts in the top plate
SCREWS = [(6.0, 13.0), (6.0, -13.0), (172.0, 13.0), (172.0, -13.0)]
THREAD_MAJ, THREAD_MIN, PITCH = 6.0, 4.4, 2.0
THREAD_PLAY = 0.25                  # nut thread bigger all round
SCREW_HOLE = 6.8
HEAD_D, HEAD_H = 10.0, layer(15)    # 3.05
NUT_AF, NUT_H = 9.0, layer(20)      # 4.05 thick
NUT_POCKET_AF = 9.4
PEGS = [(14.0, -15.0), (166.0, -15.0)]
PEG_D, PEG_H, PEG_HOLE_D, PEG_HOLE_H = 3.0, 1.0, 3.3, layer(6)

FINGERS = [60.0, 84.0, 108.0]
FINGER_R, FINGER_DEPTH = 9.0, 1.6


# ---------------------------------------------------------------- helpers
def box(x0, x1, y0, y1, z0, z1):
    return M.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def union(parts):
    parts = [p for p in parts if p is not None]
    return M.batch_boolean(parts, m3.OpType.Add) if len(parts) > 1 else parts[0]


def cyl_z(x, y, z0, z1, d, seg=40):
    return M.cylinder(z1 - z0, d / 2, d / 2, seg).translate([x, y, z0])


def extrude(cs, z0, z1):
    return M.extrude(cs, z1 - z0).translate([0, 0, z0])


def prism(poly, z0, z1):
    cs = m3.CrossSection([poly])
    if cs.area() <= 0:
        cs = m3.CrossSection([list(reversed(poly))])
    return extrude(cs, z0, z1)


def rounded_rect(x0, x1, y0, y1, r):
    cs = m3.CrossSection.square([x1 - x0 - 2 * r, y1 - y0 - 2 * r]).translate([x0 + r, y0 + r])
    return cs.offset(r, m3.JoinType.Round, 2.0, 64)


def hexagon(af):
    r = af / math.sqrt(3)
    return m3.CrossSection([[(r * math.cos(math.radians(60 * i)), r * math.sin(math.radians(60 * i))) for i in range(6)]])


# ---------------------------------------------------------------- threads
def thread(x, y, z0, z1, r_min, r_maj):
    """A right-hand thread between z0 and z1, phased by absolute z so a screw and its nut
    made separately mesh where they meet."""
    pts, n = [], 72
    flat = 0.3 / PITCH                     # crest and root flats, as a share of a turn
    flank = (1 - 2 * flat) / 2
    for i in range(n):
        u = i / n
        if u < flat:
            r = r_min
        elif u < flat + flank:
            r = r_min + (r_maj - r_min) * (u - flat) / flank
        elif u < 2 * flat + flank:
            r = r_maj
        else:
            r = r_maj - (r_maj - r_min) * (u - 2 * flat - flank) / flank
        a = 2 * math.pi * u
        pts.append((r * math.cos(a), r * math.sin(a)))
    cs = m3.CrossSection([pts]).rotate(360 * z0 / PITCH)
    h = z1 - z0
    t = M.extrude(cs, h, max(8, int(h / PITCH * 36)), 360 * h / PITCH)
    return t.translate([x, y, z0])


def screw(x=0.0, y=0.0):
    """Screw as fitted: head in the base plate's counterbore, tip just under the top face."""
    head = cyl_z(x, y, 0, HEAD_H, HEAD_D, 64) - box(x - HEAD_D, x + HEAD_D, y - 0.7, y + 0.7, -1, layer(6))
    tip = HT - 0.15
    shank = thread(x, y, HEAD_H - 0.01, tip - 0.6, THREAD_MIN / 2, THREAD_MAJ / 2)
    point = M.cylinder(0.6, THREAD_MAJ / 2 - 0.1, THREAD_MIN / 2, 48).translate([x, y, tip - 0.6]) \
        ^ thread(x, y, tip - 0.6, tip, THREAD_MIN / 2, THREAD_MAJ / 2)
    return union([head, shank, point, cyl_z(x, y, HEAD_H - 0.01, tip, THREAD_MIN - 0.01)])


def nut(x=0.0, y=0.0):
    """Nut as fitted, flush with the top face."""
    z0 = HT - NUT_H
    body = extrude(hexagon(NUT_AF).translate([x, y]), z0, HT)
    hole = thread(x, y, z0 - 0.5, HT + 0.5, THREAD_MIN / 2 + THREAD_PLAY, THREAD_MAJ / 2 + THREAD_PLAY)
    return body - hole


# ---------------------------------------------------------------- the handle
def outline():
    return rounded_rect(0, HL, -HW / 2, HW / 2, CORNER_R)


def slab(z0, z1, chamfer_bottom=False, chamfer_top=False):
    full = outline()
    inner = rounded_rect(CHAMFER, HL - CHAMFER, -HW / 2 + CHAMFER, HW / 2 - CHAMFER, CORNER_R - CHAMFER)
    if chamfer_bottom:
        s = M.hull_points(np.vstack([np.asarray(extrude(inner, z0, z0 + 0.01).to_mesh().vert_properties)[:, :3],
                                     np.asarray(extrude(full, z0 + CHAMFER, z1).to_mesh().vert_properties)[:, :3]]))
    elif chamfer_top:
        s = M.hull_points(np.vstack([np.asarray(extrude(full, z0, z1 - CHAMFER).to_mesh().vert_properties)[:, :3],
                                     np.asarray(extrude(inner, z1 - 0.01, z1).to_mesh().vert_properties)[:, :3]]))
    else:
        s = extrude(full, z0, z1)
    fingers = union([cyl_z(x, -HW / 2 - FINGER_R + FINGER_DEPTH, z0 - 1, z1 + 1, 2 * FINGER_R, 64) for x in FINGERS])
    return s - fingers


def screw_holes(z0, z1):
    return union([cyl_z(x, y, z0 - 1, z1 + 1, SCREW_HOLE) for x, y in SCREWS])


def pegs(z):
    return union([cyl_z(x, y, z, z + PEG_H, PEG_D) for x, y in PEGS])


def peg_holes(z):
    return union([cyl_z(x, y, z - 0.01, z + PEG_HOLE_H, PEG_HOLE_D) for x, y in PEGS])


def window_x(open_):
    x = C0 + (TRAVEL if open_ else 0) + ARM_X0
    return x - WIN_PAD, x + TOOTH_L + WIN_PAD


def channel(z0, z1):
    return union([box(REAR_STOP, FRONT_IN, -CHAN_Y, CHAN_Y, z0, z1),
                  box(FRONT_IN - 1, HL + 1, -SLOT_Y, SLOT_Y, z0, z1)])


def plate1():
    """Base plate: bottom wall, the lower half of the channel, the two latch windows,
    the screw heads' counterbores."""
    p = slab(0, Z1, chamfer_bottom=True) - channel(WALL_T, Z1 + 1)
    cuts = [box(w0, w1, CHAN_Y - 0.5, CAR_W / 2 + TOOTH_OUT + 0.3, WALL_T, Z1 + 1) for w0, w1 in (window_x(False), window_x(True))]
    cuts += [cyl_z(x, y, -1, HEAD_H, HEAD_D + 0.4, 64) for x, y in SCREWS]
    p = p - union(cuts) - screw_holes(0, Z1)
    return p + pegs(Z1)


def push_x():
    """x range of the pushrod's lane and the shuttle's lower lane."""
    return DOG_REAR[0] - 0.2, DOG_FRONT[1] + P_MOVE + 0.4


def wall_x():
    """The backing wall runs between the dogs' gaps."""
    return DOG_REAR[1] + P_MOVE + 0.4, DOG_FRONT[0] - 0.4


def plate2():
    """Channel plate: the upper half of the channel, its floor (with a slot for the blade pin),
    the pushrod's lane and the room its bumps work in, the shuttle's lower lane, the knob slot,
    and the two posts for band B's rollers."""
    p = slab(Z1, Z2)
    lx0, lx1 = push_x()
    pin_x0, pin_x1 = C0 + C_PIN_X - 1.9, C0 + TRAVEL + C_PIN_X + 1.9
    s_x0, s_x1 = 28.0 - 1 - 0.2, 28.0 + S_MAX + 7 + 0.2
    wx0, wx1 = wall_x()
    cuts = [channel(Z1 - 1, CHAN_TOP),
            box(lx0, lx1, CAR_W / 2, PUSH_Y0, Z1 - 1, CHAN_TOP),                 # where the bumps work
            box(lx0, lx1, LIP_Y, WALL_Y0, Z1 - 1, CHAN_TOP),                     # pushrod lane, floor over it
            box(lx0, wx0, WALL_Y0 - 0.01, WALL_Y1 + 0.01, Z1 - 1, CHAN_TOP),     # dog gaps either end of the wall
            box(wx1, lx1, WALL_Y0 - 0.01, WALL_Y1 + 0.01, Z1 - 1, CHAN_TOP),
            box(lx0, lx1, WALL_Y1, LANE_Y1, Z1 - 1, Z2 + 1),                     # shuttle's lower lane
            box(s_x0, s_x1, LANE_Y1 - 0.1, HW / 2 + 1, Z1 - 1, Z2 + 1),          # knob slot
            box(pin_x0, pin_x1, C_PIN_Y - PIN_D / 2 - PIN_PLAY, C_PIN_Y + PIN_D / 2 + PIN_PLAY, CHAN_TOP - 1, Z2 + 1),
            peg_holes(Z1), screw_holes(Z1, Z2)]
    p = p - union(cuts)
    posts = [post(X_B, Y_LO, Z2, LEVEL_B[1] - 0.25), post(X_F, Y_HI, Z2, LEVEL_B[1] - 0.25)]
    return p + union(posts) + pegs(Z2)


def post(x, y, z0, z1):
    tip = layer(4)
    return cyl_z(x, y, z0 - 0.5, z1 - tip, POST_D) + M.cylinder(tip, POST_D / 2, POST_D / 4, 40).translate([x, y, z1 - tip])


def cavity(z0, z1):
    return box(CAV_X0, CAV_X1, CAV_Y0, LANE_Y1, z0, z1)


def plate3():
    """Band deck: band B's level, and over it the divider band F sits on, with the lane for the
    shuttle down the +y side and the two posts for band F's rollers."""
    p = slab(Z2, Z3)
    pin_x0, pin_x1 = C0 + C_PIN_X - 1.9, C0 + TRAVEL + C_PIN_X + 1.9
    cuts = [cavity(Z2 - 1, LEVEL_B[1]),
            box(CAV_X0, CAV_X1, CHAN_Y, LANE_Y1, Z2 - 1, Z3 + 1),                  # shuttle lane
            box(pin_x0, pin_x1, C_PIN_Y - PIN_D / 2 - PIN_PLAY, C_PIN_Y + PIN_D / 2 + PIN_PLAY, Z2, Z3 + 1),
            peg_holes(Z2), screw_holes(Z2, Z3)]
    p = p - union(cuts)
    posts = [post(X_B, Y_HI, Z3, LEVEL_F[1] - 0.2), post(X_F, Y_LO, Z3, LEVEL_F[1] - 0.2)]
    return p + union(posts) + pegs(Z3)


def plate4():
    """Top plate: band F's level, the top wall with a groove the blade pin's top runs in, and
    hex pockets for the nuts."""
    p = slab(Z3, HT, chamfer_top=True)
    pin_x0, pin_x1 = C0 + C_PIN_X - 1.9, C0 + TRAVEL + C_PIN_X + 1.9
    cuts = [cavity(Z3 - 1, LEVEL_F[1]),
            box(pin_x0, pin_x1, C_PIN_Y - PIN_D / 2 - PIN_PLAY, C_PIN_Y + PIN_D / 2 + PIN_PLAY, LEVEL_F[1] - 0.1, LEVEL_F[1] + GROOVE),
            peg_holes(Z3), screw_holes(Z3, HT)]
    cuts += [extrude(hexagon(NUT_POCKET_AF).translate([x, y]), HT - NUT_H, HT + 1) for x, y in SCREWS]
    return p - union(cuts)


# ---------------------------------------------------------------- blade, pins, rollers
def blade_outline():
    x0, x1 = CAR_L - 3, CAR_L + BLADE_L
    w = BLADE_W / 2
    pts = [(x0, -w), (CAR_L + 40, -w)]
    for i in range(1, 21):
        t = i / 20
        pts.append((CAR_L + 40 + t * (x1 - CAR_L - 40), -w + (w + 1.5) * t ** 1.8))
    for i in range(1, 21):
        t = 1 - i / 20
        pts.append((CAR_L + 62 + t * (x1 - CAR_L - 62), w - (w - 1.5) * t ** 1.4))
    pts.append((x0, w))
    cs = m3.CrossSection([pts])
    return cs.offset(-2.5, m3.JoinType.Round, 2.0, 32).offset(2.5, m3.JoinType.Round, 2.0, 32)


def carrier_parts(c=0.0):
    """(body, tooth) with the blade c mm toward open."""
    z0, z1 = CAR_Z0, CAR_Z0 + CAR_T
    body = box(0, CAR_L, -CAR_W / 2, CAR_W / 2, z0, z1) + extrude(blade_outline(), z0, z1)
    y_arm = CAR_W / 2 - ARM_T
    body = body - union([
        box(ARM_X0 - 1.4, ARM_X1, y_arm - ARM_GAP, y_arm, z0 - 1, z1 + 1),
        box(ARM_X0 - 1.4, ARM_X0, y_arm - ARM_GAP, CAR_W / 2 + 1, z0 - 1, z1 + 1),
        cyl_z(C_PIN_X, C_PIN_Y, z0 - 1, z1 + 1, PIN_D),
        extrude(m3.CrossSection.square([44, 2.6]).translate([CAR_L + 8, 1.6])
                .offset(0.6, m3.JoinType.Round, 2.0, 16), z1 - 0.8, z1 + 1),
    ])
    tooth = box(ARM_X0, ARM_X0 + TOOTH_L, CAR_W / 2 - 0.2, CAR_W / 2 + TOOTH_OUT, z0, z1)
    return body.translate([C0 + c, 0, 0]), tooth.translate([C0 + c, 0, 0])


def carrier(c=0.0):
    b, t = carrier_parts(c)
    return b + t


C_PIN_TOP = LEVEL_F[1] + GROOVE - 0.1


def blade_pin(c=0.0):
    return cyl_z(C0 + c + C_PIN_X, C_PIN_Y, CAR_Z0, C_PIN_TOP, PIN_D)


def rollers():
    def one(x, y, z0):
        return cyl_z(x, y, z0, z0 + ROLLER_H, ROLLER_D, 48) - cyl_z(x, y, z0 - 1, z0 + 4, POST_D + 2 * PIN_PLAY)
    return union([one(X_B, Y_LO, LEVEL_B[0]), one(X_F, Y_HI, LEVEL_B[0]),
                  one(X_B, Y_HI, LEVEL_F[0]), one(X_F, Y_LO, LEVEL_F[0])])


# ---------------------------------------------------------------- pushrod and shuttle
def bump(x0, y_in, z0, z1):
    pts = [(x0, PUSH_Y0 + 0.01), (x0 + RAMP, y_in), (x0 + RAMP + FLAT, y_in), (x0 + 2 * RAMP + FLAT, PUSH_Y0 + 0.01)]
    return prism(pts, z0, z1)


BUMP_C_X = window_x(False)[0] + WIN_PAD - 0.6 - (2 * RAMP + FLAT)    # 32.4: rests behind the closed tooth
BUMP_O_X = window_x(True)[0] + WIN_PAD - 0.6 - (2 * RAMP + FLAT)     # 118.4: rests behind the open tooth
# the shuttle's lower part meets the rear dog at s = P_MOVE and the front dog at s = S_MAX - P_MOVE
DOG_REAR = (28.0 - LOW_BACK + P_MOVE - P_MOVE - 4.0, 28.0 - LOW_BACK)                      # 15 to 19
DOG_FRONT = (28.0 + S_MAX - P_MOVE + LOW_FRONT, 28.0 + S_MAX - P_MOVE + LOW_FRONT + 4.0)   # 137 to 141


def pushrod(p=0.0):
    """Pushrod at p (0 = back, P_MOVE = forward)."""
    z0, z1 = PUSH_Z0, PUSH_Z0 + PUSH_H
    body = box(DOG_REAR[0], DOG_FRONT[1], PUSH_Y0, PUSH_Y1, z0, z1)
    dogs = [box(DOG_REAR[0], DOG_REAR[1], PUSH_Y1 - 0.1, SHUT_Y_LOW + 1.0, z0, z1),
            box(DOG_FRONT[0], DOG_FRONT[1], PUSH_Y1 - 0.1, SHUT_Y_LOW + 1.0, z0, z1)]
    bumps = [bump(BUMP_C_X, BUMP_IN, z0, z0 + BUMP_H), bump(BUMP_O_X, BUMP_IN, z0, z0 + BUMP_H)]
    return union([body] + dogs + bumps).translate([p, 0, 0])


SHUT_TOP = LEVEL_F[1] - 0.1                  # 15.25
SHUT_UP_Z0 = SHUT_TOP - layer(37)            # 7.80: upper part, on layer lines from its top
SHUT_MID = (SHUT_TOP - layer(22), SHUT_TOP - layer(15))   # 10.80 to 12.20: solid round the pin
SHUT_Z0 = SHUT_TOP - layer(52)               # 4.80


def slider_pin_x(s):
    return 28.0 + s


def shuttle(s=0.0):
    """Shuttle and knob, one piece, with the knob pin's hole. s is the knob's travel."""
    px = slider_pin_x(0)
    x0, x1 = px - SHUT_BACK, px + SHUT_FRONT
    lower = box(px - LOW_BACK, px + LOW_FRONT, SHUT_Y_LOW, SHUT_Y1, SHUT_Z0, SHUT_UP_Z0 + 0.01)
    upper = box(x0, x1, SHUT_Y_UP, SHUT_Y1, SHUT_UP_Z0, SHUT_TOP)
    stem = box(px - 1, px + 7, SHUT_Y1 - 0.1, HW / 2 + 0.4, STEM_Z0, STEM_Z1)
    knob_z0 = SHUT_TOP - layer(58)               # 3.65, so the knob prints down to the bed
    knob = box(px - 3, px + 9, HW / 2 + 0.3, HW / 2 + 3.3, knob_z0, SHUT_TOP)
    ridges = union([box(px - 3 + 1.5 + 2.5 * i, px - 3 + 2.5 + 2.5 * i, HW / 2 + 2.8, HW / 2 + 3.4, knob_z0 - 1, SHUT_TOP + 1)
                    for i in range(4)])
    sh = union([lower, upper, stem, knob]) - ridges
    eye_r = PIN_D / 2 + PIN_PLAY + BAND_T + 0.3       # round the band's eye
    strand = (S_PIN_Y - BAND_T / 2 - PIN_PLAY, S_PIN_Y + BAND_T / 2 + PIN_PLAY)
    cuts = [cyl_z(px, S_PIN_Y, SHUT_Z0 - 1, SHUT_TOP + 1, PIN_D),
            # band B's eye and strand at the lower level, the strand leaving forward
            cyl_z(px, S_PIN_Y, LEVEL_B[0] - 1, SHUT_MID[0], 2 * eye_r),
            box(px, x1 + 1, strand[0], strand[1], LEVEL_B[0] - 1, SHUT_MID[0]),
            # band F's eye and strand at the upper level, the strand leaving backward
            cyl_z(px, S_PIN_Y, SHUT_MID[1], SHUT_TOP + 1, 2 * eye_r),
            box(x0 - 1, px, strand[0], strand[1], SHUT_MID[1], SHUT_TOP + 1)]
    return (sh - union(cuts)).translate([s, 0, 0])


def slider_pin(s=0.0):
    return cyl_z(slider_pin_x(s), S_PIN_Y, SHUT_UP_Z0, SHUT_TOP, PIN_D)


def knob_slot_x():
    return slider_pin_x(0) - 1 - 0.2, slider_pin_x(S_MAX) + 7 + 0.2


# ---------------------------------------------------------------- bands
def band_fitted(kind, c, s, t=BAND_T):
    """Band F or B stretched in place, blade at c, knob at s."""
    r = ROLLER_D / 2 + t / 2
    cx, sx = C0 + c + C_PIN_X, slider_pin_x(s)
    y1, y2, y3 = C_PIN_Y, C_PIN_Y + 2 * r, C_PIN_Y + 4 * r
    if kind == "F":
        z0 = LEVEL_F[0] + 0.1
        segs = [(cx, X_F, y1), (X_B, X_F, y2), (X_B, sx, y3)]
        turns = [(X_F, (y1 + y2) / 2, +1), (X_B, (y2 + y3) / 2, -1)]
    else:
        z0 = LEVEL_B[0] + 0.1
        segs = [(X_B, cx, y1), (X_B, X_F, y2), (sx, X_F, y3)]
        turns = [(X_B, (y1 + y2) / 2, -1), (X_F, (y2 + y3) / 2, +1)]
    return extrude(band_shape(segs, turns, [(cx, y1), (sx, y3)], t), z0, z0 + BAND_H)


def band_shape(segs, turns, eyes, t):
    r = ROLLER_D / 2 + t / 2
    eye_in = PIN_D + 2 * PIN_PLAY
    sq = m3.CrossSection.square
    parts = [sq([abs(x1 - x0) + 0.02, t]).translate([min(x0, x1) - 0.01, y - t / 2]) for x0, x1, y in segs]
    for x, y, side in turns:
        ring = m3.CrossSection.circle(r + t / 2, 64) - m3.CrossSection.circle(r - t / 2, 64)
        half = sq([20, 20]).translate([0 if side > 0 else -20, -10])
        parts.append((ring ^ half).translate([x, y]))
    parts += [m3.CrossSection.circle(eye_in / 2 + t, 32).translate(e) for e in eyes]
    cs = m3.CrossSection.batch_boolean(parts, m3.OpType.Add)
    return cs - m3.CrossSection.batch_boolean([m3.CrossSection.circle(eye_in / 2, 32).translate(e) for e in eyes], m3.OpType.Add)


def band_length(kind, c, s, t=BAND_T):
    r = ROLLER_D / 2 + t / 2
    cx, sx = C0 + c + C_PIN_X, slider_pin_x(s)
    if kind == "F":
        return (X_F - cx) + (X_F - X_B) + (sx - X_B) + 2 * math.pi * r
    return (cx - X_B) + (X_F - X_B) + (X_F - sx) + 2 * math.pi * r


def band_print(t):
    """A band as printed, relaxed: three equal strands in a flat S, eye to eye BAND_RELAXED."""
    r = ROLLER_D / 2 + t / 2
    a = (BAND_RELAXED - 2 * math.pi * r) / 3
    y1, y2, y3 = 0.0, 2 * r, 4 * r
    segs = [(0, a, y1), (0, a, y2), (0, a, y3)]
    turns = [(a, r, +1), (0, 3 * r, -1)]
    return extrude(band_shape(segs, turns, [(0, y1), (a, y3)], t), 0, BAND_H)


# ---------------------------------------------------------------- files
def write_stl(man, name):
    mesh = man.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].astype(np.float32)
    tri = np.asarray(mesh.tri_verts)
    a, b, c = v[tri[:, 0]], v[tri[:, 1]], v[tri[:, 2]]
    n = np.cross(b - a, c - a)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    n = n / np.where(ln == 0, 1, ln)
    with open(os.path.join(HERE, name), "wb") as f:
        f.write(b"Spring knife toy".ljust(80, b" "))
        f.write(struct.pack("<I", len(tri)))
        rec = np.zeros(len(tri), dtype=[("n", "<f4", 3), ("a", "<f4", 3), ("b", "<f4", 3), ("c", "<f4", 3), ("x", "<u2")])
        rec["n"], rec["a"], rec["b"], rec["c"] = n, a, b, c
        f.write(rec.tobytes())


def write_3mf(name, plates):
    """A Flash Studio project. plates: [(plate name, items), ...] in order; items: (object name,
    manifold, filament, (x, y) of its lower-left corner on that plate). It carries Flash
    Studio's project settings (flash studio settings.json: AD5X 0.4, 0.20mm Standard, Arachne,
    filaments 1 white, 2 black, 3 brown) and its version tags, or Flash Studio would pile every
    part on plate 1 and filament 1 (PRINTER-BRAIN). Same writer as the shed model's."""
    root = math.sqrt(len(plates))
    cols = round(root) + (1 if root > round(root) else 0)
    stride = 220 * 1.2
    res, build, cfg, plate_cfg, oid = [], [], [], [], 1
    for i, (plate_name, items) in enumerate(plates):
        ox, oy = (i % cols) * stride, -(i // cols) * stride
        plate_cfg.append(f'<plate><metadata key="plater_id" value="{i + 1}"/>'
                         f'<metadata key="plater_name" value={quoteattr(plate_name)}/>'
                         f'<metadata key="locked" value="false"/>')
        for obj_name, man, filament, (x, y), *own in items:
            bb = man.bounding_box()
            mid = np.array([(bb[0] + bb[3]) / 2, (bb[1] + bb[4]) / 2, (bb[2] + bb[5]) / 2])
            mesh = man.to_mesh()
            v = np.asarray(mesh.vert_properties)[:, :3] - mid
            tri = np.asarray(mesh.tri_verts)
            vs = "".join(f'<vertex x="{a:.4f}" y="{b:.4f}" z="{c:.4f}"/>' for a, b, c in v)
            ts = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tri)
            res.append(f'<object id="{oid}" name={quoteattr(obj_name)} type="model"><mesh>'
                       f'<vertices>{vs}</vertices><triangles>{ts}</triangles></mesh></object>')
            res.append(f'<object id="{oid + 1}" name={quoteattr(obj_name)} type="model">'
                       f'<components><component objectid="{oid}"/></components></object>')
            cfg.append(f'<object id="{oid + 1}"><metadata key="name" value={quoteattr(obj_name)}/>'
                       f'<metadata key="extruder" value="{filament}"/>'
                       + "".join(f'<metadata key="{key}" value={quoteattr(v)}/>' for key, v in (own[0] if own else {}).items())
                       + f'<part id="{oid}" subtype="normal_part"><metadata key="name" value={quoteattr(obj_name)}/>'
                       f'<metadata key="extruder" value="{filament}"/></part></object>')
            build.append(f'<item objectid="{oid + 1}" transform="1 0 0 0 1 0 0 0 1 '
                         f'{ox + x + mid[0] - bb[0]:.4f} {oy + y + mid[1] - bb[1]:.4f} {mid[2] - bb[2]:.4f}"/>')
            plate_cfg.append(f'<model_instance><metadata key="object_id" value="{oid + 1}"/>'
                             f'<metadata key="instance_id" value="0"/></model_instance>')
            oid += 2
        plate_cfg.append('</plate>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             '<metadata name="Title">Spring knife toy</metadata>'
             '<metadata name="Application">BambuStudio-02.06.00.51</metadata>'
             '<metadata name="OrcaSlicer">2.4.2</metadata>'
             '<metadata name="BambuStudio:3mfVersion">1</metadata>'
             f'<resources>{"".join(res)}</resources><build>{"".join(build)}</build></model>')
    types = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(os.path.join(HERE, name), "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", types)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)
        z.write(os.path.join(HERE, "flash studio settings.json"), "Metadata/project_settings.config")
        z.writestr("Metadata/model_settings.config",
                   '<?xml version="1.0" encoding="UTF-8"?>\n<config>' + "".join(cfg + plate_cfg) + '</config>')


def on_bed(man):
    bb = man.bounding_box()
    return man.translate([-bb[0], -bb[1], -bb[2]])


FLIP = np.array([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0]], dtype=float)
LIE = np.array([[0, 0, 1, 0], [0, 1, 0, 0], [-1, 0, 0, 0]], dtype=float)       # a z pin lying along x


def lying_pin(length):
    """A pin lying down, with a 0.35 flat so it sits on the bed (2.65 tall)."""
    return cyl_z(0, 0, 0, length, PIN_D).transform(LIE) ^ box(-1, length + 1, -5, 5, PIN_D / 2 - layer(13), 5)


def print_parts():
    """Every part turned the way it prints, sitting on the bed."""
    return {
        "handle 1 base": on_bed(plate1()),
        "handle 2 channel": on_bed(plate2()),
        "handle 3 band deck": on_bed(plate3()),
        "handle 4 top": on_bed(plate4().transform(FLIP)),
        "blade": on_bed(carrier()),
        "slider": on_bed(shuttle().transform(FLIP)),
        "pushrod": on_bed(pushrod()),
        "pin long": on_bed(lying_pin(C_PIN_TOP - CAR_Z0)),
        "pin short": on_bed(lying_pin(SHUT_TOP - SHUT_UP_Z0)),
        "roller": on_bed(cyl_z(0, 0, 0, ROLLER_H, ROLLER_D, 48) - cyl_z(0, 0, -1, 4, POST_D + 2 * PIN_PLAY)),
        "screw": on_bed(screw()),
        "nut": on_bed(nut()),
        "band": on_bed(band_print(BAND_T)),
        "band soft": on_bed(band_print(BAND_T_SOFT)),
    }


def main():
    p = print_parts()
    for name, man in p.items():
        write_stl(man, name + ".stl")
    plates = [p["handle 1 base"], p["handle 2 channel"], p["handle 3 band deck"], p["handle 4 top"]]
    x0 = (220 - HL) / 2
    y = 22.0
    handle_items = []
    for name, part in zip(("handle 1 base", "handle 2 channel", "handle 3 band deck", "handle 4 top"), plates):
        handle_items.append((name, part, 2, (x0, y)))
        y += HW + 6
    solid = {"wall_loops": "6", "sparse_infill_density": "100%"}    # printed screws and nuts: solid
    small = [("pushrod", p["pushrod"], 2, (20, 30)), ("pin long", p["pin long"], 2, (20, 52)),
             ("pin short", p["pin short"], 2, (45, 52))]
    for i in range(4):
        small.append((f"roller {i + 1}", p["roller"], 2, (20 + 12 * i, 70)))
        small.append((f"screw {i + 1}", p["screw"], 2, (20 + 16 * i, 95), solid))
        small.append((f"nut {i + 1}", p["nut"], 2, (20 + 14 * i, 120), solid))
    bl, sl = p["blade"], p["slider"]
    write_3mf("1 knife plates.3mf", [
        ("handle (black)", handle_items),
        ("small parts (black)", small),
        ("blade and slider (white)", [("blade", bl, 1, ((220 - bl.bounding_box()[3]) / 2, 60)),
                                      ("slider", sl, 1, (90, 120))]),
    ])
    bp = p["band"]
    bw, bh = bp.bounding_box()[3], bp.bounding_box()[4]
    write_3mf("2 bands (TPU).3mf", [
        ("bands (TPU)", [("band 1", bp, 1, ((220 - bw) / 2, 110 - bh - 6)),
                         ("band 2", bp, 1, ((220 - bw) / 2, 116))]),
    ])
    for name, man in p.items():
        bb = man.bounding_box()
        print(f"{name:18s} {bb[3]-bb[0]:6.1f} x {bb[4]-bb[1]:6.1f} x {bb[5]-bb[2]:5.2f} mm  {man.volume()/1000:5.1f} cm3")


if __name__ == "__main__":
    main()
