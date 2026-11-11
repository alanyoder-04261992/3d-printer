"""Simple double-action spring knife toy for the Flashforge AD5X (Nov 11 2026).

Run:  python3 make_knife.py      (needs: pip install manifold3d numpy)

A blunt plastic fidget toy, redrawn from scratch after the first spring knife jammed. Push
the knob on top forward 38 mm: the blade snaps out 59 mm and locks. Pull it back: it snaps
in and locks. Every part is printed, the screws too.

Why it is laid out like this
  * Everything moves in one layer between a base plate and a flat lid. There is no plate
    between the blade and the band (the first knife's thin middle plate pinched the blade).
  * Everything that slides has room: 0.45 mm at the sides, about 0.95 mm up and down in all.
    The blade is kept straight by one rib in the floor running in a groove under it.
  * Nothing springy rubs the blade except right at its two ends, where the latch clicks.
  * No TPU bumpers, pads or caps. The only TPU part is the band, and it is thicker.

How it works (x along the knife, the blade comes out at +x; y across it, the knob's bar is on +y)
  * One TPU band runs between two sleds that ride in a lane beside the blade. Sled F sits
    behind the blade's lug, sled B in front of it. Each sled rests against a riser on the
    knob's bar, so at rest the band pulls on the bar, not the blade.
  * Push the knob forward. The lug holds sled F back (the blade is latched), so riser B
    carries sled B forward and the band stretches. At the end of the push, cam A on the bar
    pushes the latch block in and lets the blade go. The band pulls sled F and the blade
    forward for 38 mm; the blade slides the last 22 mm on its own and the latch block
    clicks past the open catch. Then the lug runs into sled B, and the band stops it.
  * Pull the knob back and the same happens the other way: sled B is held by the lug,
    sled F is carried back, cam B lets the blade go.
  * The latch block slides in a slot in the blade's carrier, pushed out by a springy arm.
    It is a separate part, so the knock and the band's pull go into the carrier, never the arm.
    The two catches hang from the lid.

Parts (print files in this folder)
  handle base.stl, handle lid.stl   two plates, three screws
  blade.stl (blade loose.stl: its groove 0.15 wider each side, if the slide test says so)
  latch block.stl
  knob bar.stl, knob.stl (glue the knob into the bar through the lid's slot)
  sled F.stl, sled B.stl
  screw.stl (3)
  band thin.stl, band.stl, band thick.stl   TPU: print all three, fit the one that feels right

Axes for the assembled knife: z = 0 is the outside of the base plate. The blade's travel is c
(0 closed, TRAVEL open) and the knob's is s (0 back, THROW forward).
"""

import json
import math
import os
import struct
import sys
import zipfile
from xml.sax.saxutils import quoteattr

import numpy as np
import manifold3d as m3

M = m3.Manifold
HERE = os.path.dirname(os.path.abspath(__file__))


def layer(n):
    """Top of layer n from the face a part prints on (first layer 0.25, then 0.2)."""
    return 0.05 + 0.2 * n


# ---------------------------------------------------------------- the stroke
THROW = 38.0            # knob travel
TRAVEL = 60.0           # blade travel: 59 mm comes out
OVER = 1.2              # each hard stop is this far past where the latch clicks in
CREEP = 0.15            # the blade can move this far at each end before the latch holds it
KNOB_OVER = 0.4         # the knob can go this far past each end of its travel (its slot's ends)

# ---------------------------------------------------------------- heights
FLOOR = layer(10)       # 2.05 top of the base plate's floor
ZP = FLOOR + 0.45       # 2.50 every moving part is drawn here (it really rests on the floor)
PART_H = layer(19)      # 3.85 blade, latch block and knob bar
ZT = ZP + PART_H        # 6.35
Z1 = layer(34)          # 6.85 top of the base plate: 0.5 over every moving part
LID_T = layer(11)       # 2.25
HT = Z1 + LID_T         # 9.10 overall thickness
LOW = layer(9)          # 1.85 the lower layer (lug, sleds, band), from a part's bottom ...
UP = layer(12)          # 2.45 ... and the upper layer (latch tooth, catches, cams) from here up

# ---------------------------------------------------------------- blade and carrier (carrier coordinates: x from its back end)
CAR_L = 57.0
CAR_Y0, CAR_Y1 = -12.0, 11.0        # the carrier, 23 wide
CAR_Y1_UP = 10.0                    # its +y edge in the upper layer, where the cams pass over it
BLADE_W = 18.0
RIB_Y0, RIB_Y1 = -10.6, -9.6        # the floor's rib ...
RIB_TOP = layer(14)                 # ... 0.8 tall (2.85)
RIB_GAP = 0.3                       # the carrier's groove over it: 0.3 each side
RIB_GAP_LOOSE = 0.45                # blade loose
GROOVE_TOP = layer(5)               # 1.05 up into the carrier
FOOT = 0.15                         # first layers set back this far where a part slides on its first layer
SIDE = 0.45                         # side room round every moving part
C0 = 12.55                          # carrier's back end, closed
CHAN_Y0, CHAN_Y1 = CAR_Y0 - SIDE, CAR_Y1 + SIDE
MOUTH_HW = BLADE_W / 2 + SIDE       # 9.45

# the lug: in the lower layer, out past the carrier's +y side; it pushes the sleds
LUG_X0, LUG_L = 49.0, 8.0
LUG_Y1 = 15.0

# the latch block: slides across the carrier in a T-slot near its front, pushed out by an arm
TX0, TL = 39.0, 8.0                 # the block's stem (and its tooth), carrier x: long, so the cams' ramps can be gentle
HEAD_EXTRA = 1.2                    # the head is this much longer each end, so it can't come out
HEAD_Y0, HEAD_Y1 = 7.6, 9.2         # the head, block out (it rests against the lips at HEAD_Y1)
STEM_Y1 = 12.3                      # the stem's outer face in the lower layer
TOOTH_Y1 = 13.4                     # the tooth's outer face (upper layer)
TOOTH_CH = 0.5                      # its outer corners chamfered this much
BLK_PLAY = 0.25                     # the block's play in its slot, each side (two parts, sliding)
CHAMBER_Y0 = 3.0                    # the head's chamber reaches in to here
ARM_L, ARM_T = 23.0, 1.1            # the springy arm: from its root to where it presses the head's middle
ARM_PRELOAD = 0.4                   # drawn this far out past the head, so it still pushes with the block out
ARM_GAP = 0.5                       # the gap round the arm (inside one print)

# ---------------------------------------------------------------- catches (on the lid) and cams (on the knob bar)
CATCH_Y0 = 11.75                    # the catches' inner face
CATCH_Y1 = 14.6
CATCH_FLAT, CATCH_RAMP = 3.0, 4.0
CATCH_RAMP_Y = 14.25                # the ramp starts out here (past the tooth, wherever it is)
CATCH_Z0 = HT - layer(20)           # 5.05: they hang from the lid down to here
CAM_Y = 10.9                        # the cams' face: pushes the tooth in past the catch's inner face
CAM_OUT = 14.1                      # the ramp starts out here
CAM_RAMP, CAM_FLAT = 5.9, 2.0
CAM_LEAD = 0.9                      # at the end of the push, the cam's flat reaches this far past the tooth's flat face
CAM_T = layer(6)                    # 1.45: the cams are in the bar's top 1.45 (it prints top face down)

# ---------------------------------------------------------------- sleds, risers, band
SLED_L, SLED_BEAR = 26.0, 22.0      # each sled, and where the band's head bears, from its lug face
SLED_Y0, SLED_Y1 = 13.8, 19.8
SLED_H = LOW                        # 1.85
# each sled has two short dovetail keys under it, one at each end, that run in a dovetail channel in the floor:
# they keep the sled straight and stop it lifting (held upside down) into the cams and catches
KEY_LEN = 6.0
KEY_NECK = (15.3, 17.7)             # the key's neck, 2.4 wide, from the sled's bottom down to ...
KEY_NECK_Z = 1.85                   # ... here (absolute, as drawn), then it widens at 45 degrees ...
KEY_Z0 = ZP + LOW - layer(16)       # ... to its bottom (1.10; the sled prints top face down)
CHAN_NECK = (15.0, 18.0)            # the channel's neck through the floor: 0.3 each side
CHAN_NECK_Z = 1.85                  # the lips' undersides start here and slope out at 45 degrees, 0.3 from the keys' ...
CHAN_Z0 = layer(2)                  # ... to the channel's floor (0.45)
KEY_INSERT = 7.0                    # each sled drops in this far behind the furthest back it goes, where the lips are left out
BAND_Y = 16.5                       # the band's middle
BAND_W = 1.2                        # its width; three heights to pick from
BANDS = {"band thin": layer(5), "band": layer(6), "band thick": layer(7)}   # 1.05, 1.25, 1.45 tall
BAND_SLOT = 0.15                    # room each side of the band in the sleds' slots
BAND_Z = 0.2                        # the band sits this far up in the sled
HEAD_L, HEAD_W = 2.5, 3.0           # the band's heads
HEAD_ROOM = 0.15
BAND_PRELOAD = 3.0                  # the band is fitted 3 mm over its printed length
RISER_L = 6.0
RISER_Y0 = 18.0
G_P = 0.3                           # a parked sled sits this far from the lug

# ---------------------------------------------------------------- knob bar
BAR_Y0, BAR_Y1 = 21.1, 24.9
BAR_KEY = (22.2, 23.8)
BAR_KEY_D = 0.6
BAR_GAP = 0.3                       # the bar's key in its groove: 0.3 each side
LANE_Y1 = BAR_Y1 + SIDE             # 25.35
STEM_X = 54.0                       # the knob's stem on the bar, from the bar's (closed) carrier position
STEM_L, STEM_W = 12.0, 2.0
SOCKET_W = STEM_W + 0.15
SOCKET_D = layer(12)                # 2.45
KNOB_L, KNOB_W, KNOB_H = 18.0, 9.0, layer(14)   # 2.85 tall
KNOB_GAP = 0.5                      # knob over the lid

# ---------------------------------------------------------------- handle
WALL = 2.4
HW_Y0, HW_Y1 = CHAN_Y0 - WALL, LANE_Y1 + WALL     # -14.85 .. 27.75
CORNER_R = 5.0
CHAMFER = layer(3)
SCREW_HOLE = 6.8
THREAD_MAJ, THREAD_MIN, PITCH = 6.0, 4.4, 2.0
THREAD_PLAY = 0.38
GROOVE_WIDEN = 0.15
HEAD_D, HEAD_H = 8.0, layer(7)      # screw head 1.45 tall, in a counterbore under the floor
COUNTERBORE = HEAD_D + 0.8
COIN_W, COIN_D = 2.0, layer(4)
BOSS_D = 8.9                        # the lid's threaded posts ...
POST_POCKET_D = 9.7                 # ... stand in round pockets in the base plate, 0.4 all round
BOSS_Z0 = HT - layer(34)            # 2.25: they reach down to 0.2 over the floor
THREAD_TOP = HT - layer(3)          # 8.45
SCREW_TIP = layer(41)               # 8.25, 0.2 under the post's top skin
LID_DRIFT = (POST_POCKET_D - BOSS_D) / 2   # 0.4: the lid can sit this far off across
THUMB_U_R, THUMB_U_D = 7.0, 18.0    # a U cut out of the lid's front end over the blade, 14 wide and 18 deep:
#                                     press the blade back in with a finger if it ever needs it


# ---------------------------------------------------------------- where things are
def lug_x():
    return C0 + LUG_X0                  # the lug's back face, closed


def r_b():
    """Riser B's front face with the knob back (sled B's back face sits on it)."""
    return lug_x() + LUG_L + TRAVEL + G_P - THROW


def cam_a_x(s):
    """Cam A: (back end, front end) with the knob at s. Its front is the ramp."""
    flat0 = C0 + TX0 + TOOTH_CH + CAM_LEAD - THROW + s
    return flat0 - CAM_FLAT, flat0 + CAM_RAMP


def cam_b_x(s):
    """Cam B: (back end, front end). Its back is the ramp."""
    flat1 = C0 + TX0 + TRAVEL + TL - TOOTH_CH - CAM_LEAD + s
    return flat1 - CAM_RAMP, flat1 + CAM_FLAT


def closed_catch_x():
    return C0 + TX0 + TL + CREEP        # its square back face


def open_catch_x():
    return C0 + TX0 + TRAVEL - CREEP    # its square front face


def bar_x(s=0.0):
    return cam_a_x(s)[0], cam_b_x(s)[1]


def sled_range():
    """Furthest back sled F's back end goes, and furthest forward sled B's front end."""
    return lug_x() - OVER - SLED_L, r_b() + THROW + (OVER - G_P) + SLED_L


def sled_insert():
    """Where each sled's back end sits when it is dropped in: KEY_INSERT behind the furthest back it goes."""
    f_back = sled_range()[0]                            # sled F's back end, furthest back
    b_back = r_b() - KNOB_OVER                          # sled B's back end, furthest back
    return f_back - KEY_INSERT, b_back - KEY_INSERT


def key_gaps():
    """Where the channel's lips are left out: under each key of a sled at its drop-in place, 0.5 longer each end."""
    out = []
    for x in sled_insert():
        for k0 in (x, x + SLED_L - KEY_LEN):
            out.append((k0 - 0.5, k0 + KEY_LEN + 0.5))
    return out


def channel_x():
    return C0 - OVER, C0 + CAR_L + TRAVEL + OVER


# screws: two behind everything, one in front of the lanes on the +y side
def screws():
    xf = bar_x(THROW + KNOB_OVER)[1] + SIDE + 0.8 + POST_POCKET_D / 2
    return [(5.7, -7.0), (5.7, 19.0), (xf, 15.1)]


def hl():
    return screws()[2][0] + POST_POCKET_D / 2 + 0.8


HL = hl()
BLADE_L = HL - 1.0 - C0 - CAR_L         # closed, its tip is 1 mm inside the mouth


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


def prism_yz(poly, x0, x1):
    """A prism along x from a (y, z) polygon."""
    p = prism([(z, y) for y, z in poly], x0, x1)          # built along z with (z, y) as (x, y) ...
    return p.transform(np.array([[0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0]], dtype=float))   # ... then turned


def rounded_rect(x0, x1, y0, y1, r):
    cs = m3.CrossSection.square([x1 - x0 - 2 * r, y1 - y0 - 2 * r]).translate([x0 + r, y0 + r])
    return cs.offset(r, m3.JoinType.Round, 2.0, 64)


# ---------------------------------------------------------------- threads (as the first spring knife's)
def thread_r(u, r_min, r_maj, widen=0.0):
    w = widen / PITCH
    flat_min = 0.3 / PITCH - 2 * w
    flat_maj = 0.3 / PITCH + 2 * w
    flank = (1 - flat_min - flat_maj) / 2
    shift = 0.3 / PITCH / 2 - flat_min / 2
    u = (u - shift) % 1.0
    if u < flat_min:
        return r_min
    if u < flat_min + flank:
        return r_min + (r_maj - r_min) * (u - flat_min) / flank
    if u < flat_min + flank + flat_maj:
        return r_maj
    return r_maj - (r_maj - r_min) * (u - flat_min - flank - flat_maj) / flank


def thread(x, y, z0, z1, r_min, r_maj, widen=0.0):
    n = 96
    pts = []
    for i in range(n):
        r = thread_r(i / n, r_min, r_maj, widen)
        a = 2 * math.pi * i / n
        pts.append((r * math.cos(a), r * math.sin(a)))
    cs = m3.CrossSection([pts]).rotate(360 * z0 / PITCH)
    h = z1 - z0
    t = M.extrude(cs, h, max(8, int(h / PITCH * 36)), 360 * h / PITCH)
    return t.translate([x, y, z0])


def screw(x=0.0, y=0.0):
    """Screw as fitted: head in the base plate's counterbore, tip in the lid's post."""
    head = cyl_z(x, y, 0, HEAD_H, HEAD_D, 64) - box(x - HEAD_D, x + HEAD_D, y - COIN_W / 2, y + COIN_W / 2, -1, COIN_D)
    tip = SCREW_TIP
    shank = thread(x, y, HEAD_H - 0.01, tip - 0.6, THREAD_MIN / 2, THREAD_MAJ / 2)
    point = M.cylinder(0.6, THREAD_MAJ / 2 - 0.1, THREAD_MIN / 2, 48).translate([x, y, tip - 0.6]) \
        ^ thread(x, y, tip - 0.6, tip, THREAD_MIN / 2, THREAD_MAJ / 2)
    return union([head, shank, point, cyl_z(x, y, HEAD_H - 0.01, tip, THREAD_MIN - 0.01)])


def lid_thread(x, y):
    return thread(x, y, BOSS_Z0 - 0.5, THREAD_TOP, THREAD_MIN / 2 + THREAD_PLAY, THREAD_MAJ / 2 + THREAD_PLAY, GROOVE_WIDEN)


# ---------------------------------------------------------------- handle
def outline():
    return rounded_rect(0, HL, HW_Y0, HW_Y1, CORNER_R)


def slab(z0, z1, chamfer_bottom=False, chamfer_top=False):
    full = outline()
    inner = rounded_rect(CHAMFER, HL - CHAMFER, HW_Y0 + CHAMFER, HW_Y1 - CHAMFER, CORNER_R - CHAMFER)
    pts = lambda m_: np.asarray(m_.to_mesh().vert_properties)[:, :3]
    if chamfer_bottom:
        return M.hull_points(np.vstack([pts(extrude(inner, z0, z0 + 0.01)), pts(extrude(full, z0 + CHAMFER, z1))]))
    if chamfer_top:
        return M.hull_points(np.vstack([pts(extrude(full, z0, z1 - CHAMFER)), pts(extrude(inner, z1 - 0.01, z1))]))
    return extrude(full, z0, z1)


def cavity(x_end=None):
    """Everything cut out of the base plate above its floor."""
    cx0, cx1 = channel_x()
    sx0, sx1 = sled_range()
    bx0, bx1 = bar_x(-KNOB_OVER)[0], bar_x(THROW + KNOB_OVER)[1]
    top = Z1 + 1
    return union([
        box(cx0, cx1, CHAN_Y0, CHAN_Y1, FLOOR, top),                          # the blade's channel
        box(sx0 - 0.5, sx1 + 0.5, CAR_Y1, SLED_Y1 + SIDE + 0.75, FLOOR, top),   # the sleds' lane
        box(bx0 - SIDE, bx1 + SIDE, CAM_Y - 0.5, LANE_Y1, FLOOR, top),          # the knob bar's lane
        box(cx1 - 0.01, HL + 1, -MOUTH_HW, MOUTH_HW, FLOOR, top),             # the mouth
        key_channel(),
        box(bx0 - SIDE, bx1 + SIDE, BAR_KEY[0] - BAR_GAP, BAR_KEY[1] + BAR_GAP, layer(6), FLOOR + 0.01),
    ])


def key_channel():
    """The sleds' dovetail channel in the floor, with the lips left out where a sled's keys drop in."""
    x0, x1 = key_gaps()[0][0] - 0.01, sled_range()[1] + 0.5
    n0, n1 = CHAN_NECK
    w = CHAN_NECK_Z - CHAN_Z0
    prof = [(n0, FLOOR + 0.01), (n0, CHAN_NECK_Z), (n0 - w, CHAN_Z0), (n1 + w, CHAN_Z0), (n1, CHAN_NECK_Z),
            (n1, FLOOR + 0.01)]
    gaps = [box(g0, g1, n0 - w, n1 + w, CHAN_Z0, FLOOR + 0.01) for g0, g1 in key_gaps()]
    return union([prism_yz(prof, x0, x1)] + gaps)


def rib():
    cx0, cx1 = channel_x()
    return box(cx0, cx1, RIB_Y0, RIB_Y1, FLOOR - 0.01, RIB_TOP)


def base_plate():
    """Prints bottom face down."""
    p = slab(0, Z1, chamfer_bottom=True) - cavity()
    p = p + rib()
    cuts = []
    for x, y in screws():
        cuts += [cyl_z(x, y, -1, Z1 + 1, SCREW_HOLE), cyl_z(x, y, -1, HEAD_H, COUNTERBORE, 64),
                 cyl_z(x, y, FLOOR, Z1 + 1, POST_POCKET_D, 96)]
    return p - union(cuts)


def catch_polys():
    xc, xo = closed_catch_x(), open_catch_x()
    closed = [(xc, CATCH_Y0), (xc + CATCH_FLAT, CATCH_Y0), (xc + CATCH_FLAT + CATCH_RAMP, CATCH_RAMP_Y),
              (xc + CATCH_FLAT + CATCH_RAMP, CATCH_Y1), (xc, CATCH_Y1)]
    opened = [(xo, CATCH_Y0), (xo, CATCH_Y1), (xo - CATCH_FLAT - CATCH_RAMP, CATCH_Y1),
              (xo - CATCH_FLAT - CATCH_RAMP, CATCH_RAMP_Y), (xo - CATCH_FLAT, CATCH_Y0)]
    return closed, opened


def knob_slot():
    x0 = C0 + STEM_X - KNOB_OVER - SIDE
    x1 = C0 + STEM_X + STEM_L + THROW + KNOB_OVER + SIDE
    yc = (BAR_Y0 + BAR_Y1) / 2
    room = BAR_GAP + LID_DRIFT + 0.2                         # the bar's play, the lid's, and room
    return x0, x1, yc - STEM_W / 2 - room, yc + STEM_W / 2 + room


def lid(window=None):
    """Prints top face down, so the catches and the screw posts stand up off it."""
    p = slab(Z1, HT, chamfer_top=True)
    posts = union([cyl_z(x, y, BOSS_Z0, Z1 + 0.01, BOSS_D, 96) for x, y in screws()])
    catches = union([prism(poly, CATCH_Z0, Z1 + 0.01) for poly in catch_polys()])
    x0, x1, y0, y1 = knob_slot()
    u = union([box(HL - THUMB_U_D + THUMB_U_R, HL + 1, -THUMB_U_R, THUMB_U_R, Z1 - 1, HT + 1),
               cyl_z(HL - THUMB_U_D + THUMB_U_R, 0, Z1 - 1, HT + 1, 2 * THUMB_U_R, 64)])
    p = (p + posts + catches) - box(x0, x1, y0, y1, Z1 - 1, HT + 1) - u
    return p - union([lid_thread(x, y) for x, y in screws()])


# ---------------------------------------------------------------- blade, carrier and latch block
def blade_outline():
    """The carrier and blade in plan, carrier coordinates."""
    x0, x1 = CAR_L - 3, CAR_L + BLADE_L
    w = BLADE_W / 2
    pts = [(x0, -w), (x1 - 40, -w)]
    for i in range(1, 21):
        t = i / 20
        pts.append((x1 - 40 + t * 40, -w + (w + 1.5) * t ** 1.8))
    for i in range(1, 21):
        t = 1 - i / 20
        pts.append((x1 - 22 + t * 22, w - (w - 1.5) * t ** 1.4))
    pts.append((x0, w))
    cs = m3.CrossSection([pts])
    return cs.offset(-2.5, m3.JoinType.Round, 2.0, 32).offset(2.5, m3.JoinType.Round, 2.0, 32)


def carrier(c=0.0, rib_gap=RIB_GAP, with_arm=True):
    """Blade, carrier, lug and the latch block's slot and arm, at blade travel c (prints bottom face down)."""
    z0, z1 = ZP, ZT
    zl = ZP + LOW
    zu = ZP + UP
    body = union([
        extrude(blade_outline(), z0, z1),
        box(0, CAR_L, CAR_Y0, CAR_Y1, z0, zl),                 # the carrier: full width in the lower layer ...
        box(0, CAR_L, CAR_Y0, CAR_Y1_UP, zl - 0.01, z1),        # ... cut back on +y above it (the cams pass)
        box(LUG_X0, LUG_X0 + LUG_L, CAR_Y1 - 0.01, LUG_Y1, z0, zl),   # the lug
    ])
    # the groove over the floor's rib, its first layer set back
    g0, g1 = RIB_Y0 - rib_gap, RIB_Y1 + rib_gap
    cuts = [box(-1, CAR_L + 1, g0, g1, z0 - 1, z0 + GROOVE_TOP),
            box(-1, CAR_L + 1, g0 - FOOT, g1 + FOOT, z0 - 1, z0 + layer(0))]
    # the latch block's T-slot: the stem's slot out through the edge, the head's chamber inside it
    sx0, sx1 = TX0 - BLK_PLAY, TX0 + TL + BLK_PLAY
    hx0, hx1 = TX0 - HEAD_EXTRA - BLK_PLAY, TX0 + TL + HEAD_EXTRA + BLK_PLAY
    cuts += [box(sx0, sx1, HEAD_Y1 - 0.01, CAR_Y1 + 5, z0 - 1, z1 + 1),
             box(hx0, hx1, CHAMBER_Y0, HEAD_Y1, z0 - 1, z1 + 1)]
    # the arm's slot, from its root to the chamber
    ax_tip = TX0 + TL / 2
    ax_root = ax_tip - ARM_L
    arm_y1 = HEAD_Y0 + ARM_PRELOAD
    arm_y0 = arm_y1 - ARM_T
    cuts += [box(ax_root, hx0 + 0.01, CHAMBER_Y0, arm_y1 + ARM_GAP, z0 - 1, z1 + 1),
             cyl_z(ax_root, (CHAMBER_Y0 + arm_y0) / 2, z0 - 1, z1 + 1, arm_y0 - CHAMBER_Y0, 32)]
    car = body - union(cuts)
    if with_arm:
        car = car + box(ax_root - 0.5, ax_tip, arm_y0, arm_y1, z0, z1)
    return car.translate([C0 + c, 0, 0])


def block_poly_low(push=0.0):
    """The latch block in plan (absolute y, carrier x), lower layer: head and stem."""
    return [(TX0 - HEAD_EXTRA, HEAD_Y0 - push), (TX0 + TL + HEAD_EXTRA, HEAD_Y0 - push),
            (TX0 + TL + HEAD_EXTRA, HEAD_Y1 - push), (TX0 + TL, HEAD_Y1 - push),
            (TX0 + TL, STEM_Y1 - push), (TX0, STEM_Y1 - push), (TX0, HEAD_Y1 - push),
            (TX0 - HEAD_EXTRA, HEAD_Y1 - push)]


def tooth_points(push=0.0):
    """The tooth's outer face in plan (carrier x, y), chamfered corners included."""
    return [(TX0, TOOTH_Y1 - TOOTH_CH - push), (TX0 + TOOTH_CH, TOOTH_Y1 - push),
            (TX0 + TL - TOOTH_CH, TOOTH_Y1 - push), (TX0 + TL, TOOTH_Y1 - TOOTH_CH - push)]


def latch_block(c=0.0, push=0.0):
    """The latch block, pushed in by push from its out position. Prints bottom face down; the tooth over its
    stem is held up by a 45 degree chamfer."""
    z0, z1 = ZP, ZT
    zu = ZP + UP
    low = prism(block_poly_low(push), z0, z1)
    tooth_out = TOOTH_Y1 - push
    st = STEM_Y1 - push
    drop = tooth_out - st                                   # 1.1: the chamfer under the tooth
    prof = [(HEAD_Y1 - push - 0.01, z0), (st, z0), (st, zu - drop), (tooth_out, zu), (tooth_out, z1),
            (HEAD_Y1 - push - 0.01, z1)]
    tooth = prism_yz(prof, TX0, TX0 + TL)
    # chamfer the tooth's outer corners in plan
    ch = TOOTH_CH
    trim = [prism([(TX0 - 1, tooth_out - ch - 1), (TX0 + ch + 1, tooth_out + 1), (TX0 - 1, tooth_out + 1)], z0 - 1, z1 + 1),
            prism([(TX0 + TL + 1, tooth_out - ch - 1), (TX0 + TL + 1, tooth_out + 1), (TX0 + TL - ch - 1, tooth_out + 1)],
                  z0 - 1, z1 + 1)]
    return (union([low, tooth]) - union(trim)).translate([C0 + c, 0, 0])


# ---------------------------------------------------------------- knob bar, knob, sleds, band
def cam_polys(s):
    a0, a1 = cam_a_x(s)
    b0, b1 = cam_b_x(s)
    cam_a = [(a0, CAM_Y), (a1 - CAM_RAMP, CAM_Y), (a1, CAM_OUT), (a1, BAR_Y0 + 0.01), (a0, BAR_Y0 + 0.01)]
    cam_b = [(b0, CAM_OUT), (b0 + CAM_RAMP, CAM_Y), (b1, CAM_Y), (b1, BAR_Y0 + 0.01), (b0, BAR_Y0 + 0.01)]
    return cam_a, cam_b


def risers_x(s):
    xf = lug_x() - G_P + s
    xb = r_b() + s
    return (xf, xf + RISER_L), (xb - RISER_L, xb)


def knob_bar(s=0.0, dy=0.0):
    """The bar with its two risers, two cams and the knob's socket. Prints top face down."""
    x0, x1 = bar_x(s)
    body = box(x0, x1, BAR_Y0, BAR_Y1, ZP, ZT)
    key = box(x0, x1, BAR_KEY[0], BAR_KEY[1], ZP - BAR_KEY_D, ZP + 0.01)
    (f0, f1), (b0, b1) = risers_x(s)
    risers = [box(f0, f1, RISER_Y0, BAR_Y0 + 0.01, ZP, ZT), box(b0, b1, RISER_Y0, BAR_Y0 + 0.01, ZP, ZT)]
    cams = [prism(p, ZT - CAM_T, ZT) for p in cam_polys(s)]
    sx = C0 + STEM_X + s
    yc = (BAR_Y0 + BAR_Y1) / 2
    socket = box(sx - 0.075, sx + STEM_L + 0.075, yc - SOCKET_W / 2, yc + SOCKET_W / 2, ZT - SOCKET_D, ZT + 1)
    return (union([body, key] + risers + cams) - socket).translate([0, dy, 0])


def knob(s=0.0, dy=0.0):
    """Knob: a grip on top of the lid, its stem down through the lid's slot into the bar. Prints upside down."""
    sx = C0 + STEM_X + s
    yc = (BAR_Y0 + BAR_Y1) / 2
    zc = HT + KNOB_GAP
    stem = box(sx, sx + STEM_L, yc - STEM_W / 2, yc + STEM_W / 2, ZT - SOCKET_D + 0.1, zc + 0.01)
    cx0 = sx + STEM_L / 2 - KNOB_L / 2
    grip = extrude(rounded_rect(cx0, cx0 + KNOB_L, yc - KNOB_W / 2, yc + KNOB_W / 2, 2.0), zc, zc + KNOB_H)
    grooves = union([box(cx0 + 3.1 + 3 * i, cx0 + 3.9 + 3 * i, yc - KNOB_W / 2 + 1.0, yc + KNOB_W / 2 - 1.0,
                         zc + KNOB_H - layer(3), zc + KNOB_H + 1) for i in range(5)])   # grooves, so its top prints flat
    return (union([stem, grip]) - grooves).translate([0, dy, 0])


def sled(face_x, kind, dy=0.0):
    """Sled F (its lug face is its front) or sled B (lug face at its back). face_x: that face's x."""
    if kind == "F":
        x0, x1 = face_x - SLED_L, face_x
        bear = face_x - SLED_BEAR
        pocket = (bear - HEAD_L - 2 * HEAD_ROOM, bear)
        slot = (bear - 0.01, face_x + 1)
    else:
        x0, x1 = face_x, face_x + SLED_L
        bear = face_x + SLED_BEAR
        pocket = (bear, bear + HEAD_L + 2 * HEAD_ROOM)
        slot = (face_x - 1, bear + 0.01)
    z0, z1 = ZP, ZP + SLED_H
    body = box(x0, x1, SLED_Y0, SLED_Y1, z0, z1)
    # a dovetail key under each end (the sled prints top face down, so the keys widen upward as printed)
    k0, k1 = KEY_NECK
    w = KEY_NECK_Z - KEY_Z0
    kp = [(k0, z0 + 0.01), (k0, KEY_NECK_Z), (k0 - w, KEY_Z0), (k1 + w, KEY_Z0), (k1, KEY_NECK_Z), (k1, z0 + 0.01)]
    key = union([prism_yz(kp, x0, x0 + KEY_LEN), prism_yz(kp, x1 - KEY_LEN, x1)])
    zb = z0 + BAND_Z
    cuts = [box(slot[0], slot[1], BAND_Y - BAND_W / 2 - BAND_SLOT, BAND_Y + BAND_W / 2 + BAND_SLOT, zb, z1 + 1),
            box(pocket[0], pocket[1], BAND_Y - HEAD_W / 2 - HEAD_ROOM, BAND_Y + HEAD_W / 2 + HEAD_ROOM, zb, z1 + 1)]
    return ((body + key) - union(cuts)).translate([0, dy, 0])


def sled_faces(c, s):
    """Sled F's front face and sled B's back face for blade travel c and knob travel s: each sled is pulled
    by the band toward the other until its riser or the lug stops it."""
    f = min(lug_x() + c, lug_x() - G_P + s)
    b = max(lug_x() + LUG_L + c, r_b() + s)
    return f, b


def band_length(c, s):
    f, b = sled_faces(c, s)
    return (b + SLED_BEAR) - (f - SLED_BEAR)


BAND_PRINTED = band_length(0.0, 0.0) - BAND_PRELOAD     # between the heads' inner faces


def band_print(h):
    strand = m3.CrossSection.square([BAND_PRINTED, BAND_W]).translate([0, -BAND_W / 2])
    heads = [m3.CrossSection.square([HEAD_L, HEAD_W]).translate([-HEAD_L, -HEAD_W / 2]),
             m3.CrossSection.square([HEAD_L, HEAD_W]).translate([BAND_PRINTED, -HEAD_W / 2])]
    cs = m3.CrossSection.batch_boolean([strand] + heads, m3.OpType.Add)
    cs = cs.offset(0.8, m3.JoinType.Round, 2.0, 32).offset(-0.8, m3.JoinType.Round, 2.0, 32)   # round where they meet
    return extrude(cs, 0, h)


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
        f.write(b"Simple spring knife toy".ljust(80, b" "))
        f.write(struct.pack("<I", len(tri)))
        rec = np.zeros(len(tri), dtype=[("n", "<f4", 3), ("a", "<f4", 3), ("b", "<f4", 3), ("c", "<f4", 3), ("x", "<u2")])
        rec["n"], rec["a"], rec["b"], rec["c"] = n, a, b, c
        f.write(rec.tobytes())


def project_settings(filaments=None, tpu_filament=None, process=None):
    """Flash Studio's project settings (flash studio settings.json), with changes named in
    different_settings_to_system so Flash Studio keeps them (PRINTER-BRAIN)."""
    with open(os.path.join(HERE, "flash studio settings.json")) as f:
        d = json.load(f)
    diff = d["different_settings_to_system"]
    for key, v in (process or {}).items():
        d[key] = v
    if process:
        diff[0] = ";".join(sorted(set(filter(None, diff[0].split(";"))) | set(process)))
    for n, changes in (filaments or {}).items():
        for key, v in changes.items():
            d[key][n - 1] = v
        diff[n] = ";".join(sorted(set(filter(None, diff[n].split(";"))) | set(changes)))
    if tpu_filament:
        with open(os.path.join(HERE, "flash studio TPU filament.json")) as f:
            tpu = {k_: v for k_, v in json.load(f).items() if not k_.startswith("_")}
        for key, v in tpu.items():
            d[key][tpu_filament - 1] = v
    return json.dumps(d, indent=4) + "\n"


def write_3mf(name, plates, settings=None):
    """A Flash Studio project (the first spring knife's writer). plates: [(plate name, items)];
    items: (object name, manifold, filament, (x, y) of its lower-left corner on the plate[, own settings])."""
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
            own = dict(own[0]) if own else {}
            bb = man.bounding_box()
            mid = np.array([(bb[0] + bb[3]) / 2, (bb[1] + bb[4]) / 2, (bb[2] + bb[5]) / 2])
            mesh = man.to_mesh()
            v = np.asarray(mesh.vert_properties)[:, :3] - mid
            tri = np.asarray(mesh.tri_verts)
            vs = "".join(f'<vertex x="{a:.4f}" y="{b:.4f}" z="{c:.4f}"/>' for a, b, c in v)
            ts = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tri)
            res.append(f'<object id="{oid}" name={quoteattr(obj_name)} type="model"><mesh>'
                       f'<vertices>{vs}</vertices><triangles>{ts}</triangles></mesh></object>')
            top = oid + 1
            res.append(f'<object id="{top}" name={quoteattr(obj_name)} type="model"><components>'
                       f'<component objectid="{oid}"/></components></object>')
            cfg.append(f'<object id="{top}"><metadata key="name" value={quoteattr(obj_name)}/>'
                       f'<metadata key="extruder" value="{filament}"/>'
                       + "".join(f'<metadata key="{key}" value={quoteattr(v)}/>' for key, v in own.items())
                       + f'<part id="{oid}" subtype="normal_part"><metadata key="name" value={quoteattr(obj_name)}/>'
                       f'<metadata key="extruder" value="{filament}"/></part></object>')
            build.append(f'<item objectid="{top}" transform="1 0 0 0 1 0 0 0 1 '
                         f'{ox + x + mid[0] - bb[0]:.4f} {oy + y + mid[1] - bb[1]:.4f} {mid[2] - bb[2]:.4f}"/>')
            plate_cfg.append(f'<model_instance><metadata key="object_id" value="{top}"/>'
                             f'<metadata key="instance_id" value="0"/></model_instance>')
            oid = top + 1
        plate_cfg.append('</plate>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             '<metadata name="Title">Simple spring knife toy</metadata>'
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
        z.writestr("Metadata/project_settings.config", settings or project_settings())
        z.writestr("Metadata/model_settings.config",
                   '<?xml version="1.0" encoding="UTF-8"?>\n<config>' + "".join(cfg + plate_cfg) + '</config>')


def on_bed(man):
    bb = man.bounding_box()
    return man.translate([-bb[0], -bb[1], -bb[2]])


FLIP = np.array([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0]], dtype=float)   # turned over about x

# ---------------------------------------------------------------- slide test: the back of the knife, cut short
TEST_X1 = C0 + CAR_L + 6.0           # the test pieces end here (the carrier slides out of the cut end)


def test_cut(man):
    return man ^ box(-1, TEST_X1, HW_Y0 - 1, HW_Y1 + 1, -1, HT + 2)


def slide_test_base():
    """The base plate's back end with the channel, the rib and both rear screws, cut off past the carrier."""
    return test_cut(base_plate())


def slide_test_lid():
    """The lid's back end with the closed catch, and a window over the latch block so a toothpick can push it in."""
    win = box(C0 + TX0 - 1.0, C0 + TX0 + TL - 0.5, TOOTH_Y1 + 0.2, TOOTH_Y1 + 2.4, Z1 - 1, HT + 1)
    return test_cut(lid()) - win


# print settings (PRINTER-BRAIN, strong parts)
STRONG_PLA = {"nozzle_temperature": "230", "nozzle_temperature_initial_layer": "230", "fan_min_speed": "45",
              "fan_max_speed": "45", "additional_cooling_fan_speed": "0", "filament_flow_ratio": "1.02"}
STRONG_PROCESS = {"default_acceleration": "3000", "outer_wall_acceleration": "3000",
                  "inner_wall_acceleration": "3000", "internal_solid_infill_acceleration": "3000",
                  "elefant_foot_compensation": "0.1"}
SLOW = {"outer_wall_speed": "60", "inner_wall_speed": "60", "internal_solid_infill_speed": "60",
        "top_surface_speed": "60", "gap_infill_speed": "60"}
SOLID = {"wall_loops": "6", "sparse_infill_density": "100%", **SLOW}
MOVING = {"wall_loops": "4", "sparse_infill_density": "100%", **SLOW}
LID_SET = {"wall_loops": "4", "outer_wall_speed": "40", "inner_wall_speed": "40"}
BRIM = {"brim_type": "outer_only", "brim_width": "5"}
NO_BRIM = {"brim_type": "no_brim"}
TPU_SOLID = {"sparse_infill_density": "100%"}


def print_parts():
    """Every part turned the way it prints, sitting on the bed."""
    return {
        "handle base": on_bed(base_plate()),
        "handle lid": on_bed(lid().transform(FLIP)),
        "blade": on_bed(carrier()),
        "blade loose": on_bed(carrier(rib_gap=RIB_GAP_LOOSE)),
        "latch block": on_bed(latch_block()),
        "knob bar": on_bed(knob_bar().transform(FLIP)),
        "knob": on_bed(knob().transform(FLIP)),
        "sled F": on_bed(sled(0.0, "F").transform(FLIP)),      # top face down: the keys widen upward as printed
        "sled B": on_bed(sled(0.0, "B").transform(FLIP)),
        "screw": on_bed(screw()),
        **{name: on_bed(band_print(h)) for name, h in BANDS.items()},
        "slide test base": on_bed(slide_test_base()),
        "slide test lid": on_bed(slide_test_lid().transform(FLIP)),
        "slide test blade": on_bed(carrier() ^ box(-1, C0 + CAR_L, -30, 30, -1, 20)),
        "slide test blade loose": on_bed(carrier(rib_gap=RIB_GAP_LOOSE) ^ box(-1, C0 + CAR_L, -30, 30, -1, 20)),
    }


def projects(p):
    strong = project_settings({1: STRONG_PLA, 2: STRONG_PLA}, process=STRONG_PROCESS)
    bw = lambda name: p[name].bounding_box()[4] - p[name].bounding_box()[1]
    test = [("slide test base", p["slide test base"], 2, (15, 20), BRIM),
            ("slide test lid", p["slide test lid"], 2, (15, 20 + bw("slide test base") + 12), {**BRIM, **LID_SET}),
            ("screw 1", p["screw"], 2, (110, 30), SOLID), ("screw 2", p["screw"], 2, (130, 30), SOLID),
            ("slide test blade", p["slide test blade"], 1, (100, 90), MOVING),
            ("slide test blade loose", p["slide test blade loose"], 1, (100, 130), MOVING),
            ("latch block", p["latch block"], 1, (180, 30), {**MOVING, **NO_BRIM})]
    x0 = (220 - HL) / 2
    handle = [("handle base", p["handle base"], 2, (x0, 20), BRIM),
              ("handle lid", p["handle lid"], 2, (x0, 20 + bw("handle base") + 12), {**BRIM, **LID_SET})]
    mid_x = lambda name: (220 - (p[name].bounding_box()[3] - p[name].bounding_box()[0])) / 2
    blade = [("blade", p["blade"], 1, (mid_x("blade"), 30), {**MOVING, **BRIM}),
             ("latch block", p["latch block"], 1, (30, 90), {**MOVING, **NO_BRIM}),
             ("latch block spare", p["latch block"], 1, (50, 90), {**MOVING, **NO_BRIM})]
    moving = [("knob bar", p["knob bar"], 1, (mid_x("knob bar"), 30), {**MOVING, **BRIM}),
              ("knob", p["knob"], 1, (30, 90), MOVING),
              ("sled F", p["sled F"], 2, (70, 90), MOVING), ("sled B", p["sled B"], 2, (70, 120), MOVING),
              ("screw 1", p["screw"], 2, (130, 90), SOLID), ("screw 2", p["screw"], 2, (150, 90), SOLID),
              ("screw 3", p["screw"], 2, (170, 90), SOLID)]
    seam = {"seam_position": "back", **TPU_SOLID}
    bands = [(name, p[name], 1, (mid_x(name), 80 + 20 * i), seam) for i, name in enumerate(BANDS)]
    return [
        ("1 slide test.3mf", [("slide test: back of the handle, blade pieces, latch block", test)], strong),
        ("2 knife plates.3mf", [("handle (black)", handle), ("blade and latch blocks (white)", blade),
                                ("knob bar, knob (white), sleds, screws (black)", moving)], strong),
        ("3 bands TPU.3mf", [("three bands: thin, normal, thick", bands)], project_settings(tpu_filament=1)),
    ]


def main():
    p = print_parts()
    for name, man in p.items():
        write_stl(man, name + ".stl")
    for name, plates, settings in projects(p):
        write_3mf(name, plates, settings)
    for name, man in p.items():
        bb = man.bounding_box()
        print(f"{name:24s} {bb[3]-bb[0]:6.1f} x {bb[4]-bb[1]:6.1f} x {bb[5]-bb[2]:5.2f} mm  {man.volume()/1000:5.2f} cm3")
    print(f"handle {HL:.1f} x {HW_Y1 - HW_Y0:.1f} x {HT:.2f} mm; blade {BLADE_L:.1f} long past the carrier, "
          f"{C0 + CAR_L + BLADE_L + TRAVEL - HL:.1f} out; band printed {BAND_PRINTED:.1f} between its heads")


if __name__ == "__main__":
    main()
