"""Double-action spring knife toy for the Flashforge AD5X, designed from scratch (v3).

Run:  python3 make_knife.py      (needs: pip install manifold3d numpy)

A blunt plastic fidget toy. Push the knob on the side 28 mm forward: the blade snaps out
86 mm and locks. Pull it back: the blade snaps in and locks. Every part is printed, the
screws and nuts too.

How it works
  * One TPU band runs between two small sleds that ride over the blade: sled F behind the
    blade's lug, sled B in front of it. The band goes straight through a slot in the lug.
  * Each sled rests against a post (riser) on the knob's bar. At rest the band is only just
    taut and pulls on nothing: the blade is held by its latch alone.
  * Push the knob forward. Sled F is stopped by the lug, so the band stretches while the bar
    carries sled B forward. Near the end of the stroke cam A on the bar pushes the latch
    block in and lets the blade go. The band throws sled F and the blade forward until
    sled F comes back against its riser; the blade coasts on, stops on sled B (which
    leans on a TPU pad) and its latch block drops into the open window.
  * Pull the knob back and the same happens the other way round: sled B is stopped by the
    lug, sled F is carried back, cam B lets the blade go.
  * The latch block is a separate PLA block that slides in a slot in the carrier, pushed
    out by a springy arm. Its load goes into the carrier, never the arm. It catches on the
    ends of a PLA rail in the base plate. The rail sits on a TPU cushion, which takes the
    knock when the blade bounces back off its pad.

Parts (print files in this folder)
  handle 1 base.stl, handle 2 middle.stl, handle 3 top.stl   three plates, four screws
  blade.stl          blade and carrier with the lug and the latch arm
  latch block.stl    rail.stl    sled F.stl    sled B.stl
  knob slider.stl    the bar with its two cams, two risers and the knob
  screw.stl (4), nut.stl (4), nut loose.stl (if the fit test says so)
  band.stl, pad.stl (2), rail cushion.stl     TPU; band strong.stl for a soft TPU, band soft.stl for a stiff one
  1 fit test.3mf        a screw and three nuts: find the nut fit first
  2 knife plates.3mf    Flash Studio project: handle and small parts (black), blade and knob slider (white)
  3 TPU parts.3mf       band, pads and cushion; pick your TPU filament before slicing

Axes for the assembled knife: x along it (the blade comes out at +x), y across it (the knob is
on +y), z through it (z = 0 is the outside of the base plate). The blade's travel is c (0 closed,
86 open) and the knob's is s (0 back, 28 forward).
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
Z1 = layer(35)                      # 7.05  base plate / middle plate
Z_FLOOR = Z1 + layer(3)             # 7.70  top of the middle plate's floor: the sleds ride on it
Z2 = Z1 + layer(15)                 # 10.10 middle plate / top plate
HT = Z2 + layer(11)                 # 12.35 overall thickness

# ---------------------------------------------------------------- blade and carrier
CAR_L, CAR_W, CAR_T = 55.0, 22.0, layer(21)    # carrier 55 x 22 x 4.25
BLADE_L, BLADE_W = 99.0, 18.0     # its round tip ends 4.9 short of BLADE_L
CAR_Z0 = WALL_T + 0.275             # 2.525: 0.275 over the channel floor
CAR_Z1 = CAR_Z0 + CAR_T             # 6.775: 0.275 under the middle plate
GAP = 0.3                           # sliding gap at the sides
CHAN_Y = CAR_W / 2 + GAP            # 11.3
SLOT_Y = BLADE_W / 2 + GAP          # 9.3
C0 = 22.0                           # carrier's back end, closed
TRAVEL = 86.0                       # blade travel: 79 mm comes out
OVERRUN = 5.0                       # room for the blade past each end (pads squash)
REAR_IN = C0 - OVERRUN              # 17 channel's back end
FRONT_IN = C0 + CAR_L + TRAVEL + OVERRUN - 0.5    # 167.5 channel's front end

# the lug: stands up from the carrier into the band level; the band runs through its slot
LUG_X0, LUG_L = 12.0, 8.0           # on the carrier
LUG_HW = 5.2                        # half width
LUG_TOP = CAR_Z0 + layer(36)        # 9.775
BAND_SLOT = 1.05                    # half width of the slot the band runs in
BAND_SLOT_Z = CAR_Z0 + layer(27)    # 7.975 floor of that slot
X_L0 = C0 + LUG_X0                  # 34: lug's back face, closed

# latch: a separate block in a slot through the carrier's +y side, pushed out by an arm
BLK_X0, BLK_L, BLK_D = 22.5, 4.0, 4.5
BLK_CHAMFER = 0.5                   # on its two outer corners: the trailing corner can't catch
BLK_SLOT = 0.25                     # play each side of the block in its slot
X_BLK = C0 + BLK_X0                 # 44.5: block's back face, closed
ARM_ROOT = 52.0                     # the arm's root on the carrier (x)
ARM_Y0, ARM_T = 4.8, 1.2            # the arm, as printed (free)
NOSE_TOP = 13.45 - BLK_D + 0.5      # 9.45: the arm's nose reaches here when free (0.5 past the block's out place)

# block's outer face (y): out in a window it rests on the knob bar; on the rail; pushed by a cam
Y_OUT, Y_RAIL, Y_CAM = 13.45, CHAN_Y, 11.05

# rail: the latch wall between the two windows; it floats on a TPU cushion
RAIL_Y0, RAIL_Y1 = CHAN_Y, CHAN_Y + layer(8)   # 11.3 to 12.95 (printed lying on its inner face)
RAIL_Z0, RAIL_TOP = layer(5), layer(22)        # 1.05 to 4.45
RAIL_CHAMFER = 0.3                  # on the inner corner of each catching end
E_CATCH = 0.5                       # the block sits this far from the rail end at rest
RAIL_X0 = X_BLK + BLK_L + E_CATCH   # 49: closed catch (the block's front face bears here)
RAIL_X1 = X_BLK + TRAVEL - E_CATCH  # 130: open catch (the block's back face bears here)
TAB_X0 = (RAIL_X0 + RAIL_X1) / 2 - 2.0         # the rail's tab, in the cushion
TAB_Y1 = RAIL_Y0 + layer(17)        # 14.75
CUSH_L = 8.0                        # each side of the tab
W_FAR = 5.0                         # far end of each window: past the block's overrun
RAIL_MOVE = 3.2                     # the rail can move this far each way in its groove
WIN_Y1 = Y_OUT + 0.15               # windows are cut out to here

# knob bar: in a lane beside the channel, above the rail
BAR_Y0, BAR_Y1 = Y_OUT, 15.8
LANE_Y0, LANE_Y1 = RAIL_Y1, 16.05
BAR_Z0 = RAIL_TOP + 0.2             # 4.65 (bar prints on this face)
BAR_Z1 = BAR_Z0 + layer(10)         # 6.70
THROW = 28.0                        # knob travel
SOFT = 0.5                          # the knob can go this far past each end before a sled meets its pad
G_P = 0.5                           # a parked sled sits this far from the lug
RISER_L = 10.0
RISER_TOP = BAR_Z0 + layer(25)      # 9.70
RAMP = (Y_OUT - Y_CAM) / math.tan(math.radians(22))   # 5.2: 22 degree cam ramps
CAM_FLAT = 2.0
C_TRIP = 1.1                        # the blade creeps this far while cocked: 0.5 to the rail, 0.6 into its cushion
C_COCK = 2.0                        # and never more than this
STEM_X0, STEM_X1 = 84.0, 98.0
KNOB_TOP = BAR_Z0 + layer(36)       # 11.90

# band level: two sleds, one band, two pads
SLED_H = layer(10)                  # 2.05
SLED_Z0, SLED_Z1 = Z_FLOOR, Z_FLOOR + SLED_H   # 7.70 to 9.75
SLED_LEN, SLED_HW, WING_L = 15.0, 7.8, 6.0
POST_D, EYE_PLAY = 3.0, 0.4
POST_BACK = 10.5                    # the band's post is this far from the sled's lug face
POCKET_Z = SLED_Z0 + layer(2)       # 8.15 the band sits on this
CAV_Y0, CAV_Y1 = -SLED_HW - 0.3, LANE_Y1       # band level cavity
R_B = LUG_L + TRAVEL + G_P - THROW  # 66.5: sled B's lug face from the lug's back face (closed), knob back
PAD_L, PAD_HW = 7.0, 4.0
PAD_X0 = X_L0 - G_P - SOFT - SLED_LEN - PAD_L  # 11: rear pad, sled F's soft stop
PAD_X1 = X_L0 + R_B + THROW + SOFT + SLED_LEN + PAD_L   # 157: front pad, sled B's soft stop
BAND = (layer(5), 1.05)             # height and width: 1.05 x 1.05
BAND_STRONG = (layer(6), 1.45)      # 1.25 x 1.45, for a soft TPU
BAND_SOFT = (layer(4), 1.05)        # 0.85 x 1.05, for a stiff TPU
BAND_W = BAND[0]
BAND_RELAXED = R_B + G_P + 2 * POST_BACK - 4.0  # 84 eye to eye: taut by 4 mm when parked

# printed screws: M6-ish, 2 mm pitch, nuts in the top two plates
SCREWS = [(6.0, 13.0), (6.0, -13.0), (172.0, 13.0), (172.0, -13.0)]
THREAD_MAJ, THREAD_MIN, PITCH = 6.0, 4.4, 2.0
THREAD_PLAY = 0.38                  # nut thread bigger all round ...
GROOVE_WIDEN = 0.15                 # ... and its groove 0.15 wider on each flank
SCREW_HOLE = 6.8
HEAD_D, HEAD_H = 8.0, layer(7)      # 1.45 tall, so it stays under the channel floor; 8.0 so its
                                    # counterbore stays inside the bottom chamfer at the corners
COUNTERBORE = HEAD_D + 0.8
NUT_AF, NUT_H = 8.6, layer(20)      # 4.05 thick
NUT_POCKET_AF = 9.0
PEGS = [(14.0, -15.0), (166.0, -15.0)]
PEG_D, PEG_H, PEG_HOLE_D, PEG_HOLE_H = 3.0, 1.0, 3.8, layer(6)   # 0.4 all round (holes print small)

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
def thread_r(u, r_min, r_maj, widen=0.0):
    """Radius of the thread profile at u (share of a turn, 0..1). widen moves each flank of a
    nut's groove this far along the axis (the groove is the wide part of the nut's hole, at r_maj)."""
    w = widen / PITCH
    flat_min = 0.3 / PITCH - 2 * w         # the nut's thread crest (r_min) gets narrower ...
    flat_maj = 0.3 / PITCH + 2 * w         # ... and its groove (r_maj) wider
    flank = (1 - flat_min - flat_maj) / 2
    shift = 0.3 / PITCH / 2 - flat_min / 2  # keep the groove centred where the screw's crest is
    u = (u - shift) % 1.0
    if u < flat_min:
        return r_min
    if u < flat_min + flank:
        return r_min + (r_maj - r_min) * (u - flat_min) / flank
    if u < flat_min + flank + flat_maj:
        return r_maj
    return r_maj - (r_maj - r_min) * (u - flat_min - flank - flat_maj) / flank


def thread(x, y, z0, z1, r_min, r_maj, widen=0.0):
    """A right-hand thread between z0 and z1, phased by absolute z so a screw and its nut made
    separately mesh where they meet."""
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
    """Screw as fitted: head in the base plate's counterbore, tip just under the top face."""
    head = cyl_z(x, y, 0, HEAD_H, HEAD_D, 64) - box(x - HEAD_D, x + HEAD_D, y - 0.7, y + 0.7, -1, layer(3))
    tip = layer(61)                       # 12.25, 0.1 under the top face
    shank = thread(x, y, HEAD_H - 0.01, tip - 0.6, THREAD_MIN / 2, THREAD_MAJ / 2)
    point = M.cylinder(0.6, THREAD_MAJ / 2 - 0.1, THREAD_MIN / 2, 48).translate([x, y, tip - 0.6]) \
        ^ thread(x, y, tip - 0.6, tip, THREAD_MIN / 2, THREAD_MAJ / 2)
    return union([head, shank, point, cyl_z(x, y, HEAD_H - 0.01, tip, THREAD_MIN - 0.01)])


def nut(x=0.0, y=0.0, play=THREAD_PLAY, notches=0):
    """Nut as fitted, flush with the top face. notches marks a fit-test nut."""
    z0 = HT - NUT_H
    body = extrude(hexagon(NUT_AF).translate([x, y]), z0, HT)
    hole = thread(x, y, z0 - 0.5, HT + 0.5, THREAD_MIN / 2 + play, THREAD_MAJ / 2 + play, GROOVE_WIDEN)
    cuts = [hole]
    r_flat = NUT_AF / 2
    for i in range(notches):
        cuts.append(box(x + r_flat - 0.5, x + r_flat + 1, y - 2.0 + 1.6 * i, y - 1.2 + 1.6 * i, z0 - 1, HT + 1))
    return body - union(cuts)


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


def windows():
    """(x0, x1) of the closed and open windows in the latch wall."""
    return (X_BLK - W_FAR, RAIL_X0), (RAIL_X1, X_BLK + TRAVEL + BLK_L + W_FAR)


def rail_groove():
    return box(RAIL_X0 - RAIL_MOVE, RAIL_X1 + RAIL_MOVE, RAIL_Y0 - 0.1, RAIL_Y1 + 0.2, RAIL_Z0, RAIL_TOP + 1)


def cushion_pocket():
    return box(TAB_X0 - CUSH_L - 0.15, TAB_X0 + 4.0 + CUSH_L + 0.15, RAIL_Y1, TAB_Y1 + 0.4, RAIL_Z0, RAIL_TOP + 1)


def bar_x(s=0.0):
    """x range of the bar's body at knob travel s."""
    return CAM_A_TOP - CAM_FLAT + s, CAM_B_TOP + CAM_FLAT + s


def knob_slot_x():
    return STEM_X0 - SOFT - 3.5 - 0.3, STEM_X1 + THROW + SOFT + 3.5 + 0.3


def plate1():
    """Base plate: bottom wall, the blade's channel, the latch wall with its two windows, the
    rail's groove and its cushion pocket, the knob bar's lane and the knob's slot."""
    p = slab(0, Z1, chamfer_bottom=True)
    lx0, lx1 = bar_x(-SOFT - 3.5)[0] - 0.3, bar_x(THROW + SOFT + 3.5)[1] + 0.3
    kx0, kx1 = knob_slot_x()
    cuts = [box(REAR_IN, FRONT_IN, -CHAN_Y, CHAN_Y, WALL_T, Z1 + 1),                  # channel
            box(FRONT_IN - 1, HL + 1, -SLOT_Y, SLOT_Y, WALL_T, Z1 + 1),               # blade slot
            box(lx0, lx1, Y_CAM - 0.25, LANE_Y1, RAIL_TOP, Z1 + 1),                    # cams' and bar's lane
            box(kx0, kx1, LANE_Y1 - 0.1, HW / 2 + 1, BAR_Z0 - 0.2, Z1 + 1),           # knob slot
            rail_groove(), cushion_pocket()]
    cuts += [box(w0, w1, CHAN_Y - 0.01, WIN_Y1, WALL_T, RAIL_TOP + 1) for w0, w1 in windows()]
    cuts += [cyl_z(x, y, -1, HEAD_H, COUNTERBORE, 64) for x, y in SCREWS]
    # the front screw holes meet the blade slot: no thin sliver between them
    cuts += [box(172.0 - SCREW_HOLE / 2, 172.0 + SCREW_HOLE / 2, -13.0, 13.0, WALL_T, Z1 + 1) ^
             union([cyl_z(172.0, yy, WALL_T - 1, Z1 + 2, SCREW_HOLE) for yy in (13.0, -13.0)]
                   + [box(172.0 - SCREW_HOLE / 2, 172.0 + SCREW_HOLE / 2, -SLOT_Y - 0.5, SLOT_Y + 0.5, WALL_T, Z1 + 1)])]
    p = p - union(cuts) - screw_holes(0, Z1)
    return p + pegs(Z1)


def lug_slot_x():
    return X_L0 - OVERRUN - 0.3, X_L0 + LUG_L + TRAVEL + OVERRUN + 0.3


def riser_sweep(x0, x1):
    return x0 - SOFT - 3.5 - 0.3, x1 + THROW + SOFT + 3.5 + 0.3


def riser_x():
    """(x0, x1) of riser F and riser B on the bar at s = 0."""
    f = (X_L0 - G_P, X_L0 - G_P + RISER_L)
    b = (X_L0 + R_B - RISER_L, X_L0 + R_B)
    return f, b


def plate2():
    """Middle plate: the floor over the channel (with the lug's slot and the risers' slots),
    and the band level above it, open at the top, where the sleds, the band and the pads go.
    Prints with its bottom face on the bed, so nothing bridges."""
    p = slab(Z1, Z2)
    (f0, f1), (b0, b1) = riser_x()
    cuts = [box(*lug_slot_x(), -LUG_HW - 0.3, LUG_HW + 0.3, Z1 - 1, Z_FLOOR + 1),
            box(*riser_sweep(f0, f1), LANE_Y0, LANE_Y1, Z1 - 1, Z_FLOOR + 1),
            box(*riser_sweep(b0, b1), LANE_Y0, LANE_Y1, Z1 - 1, Z_FLOOR + 1),
            # band level: the sleds' room, and the pads' pockets at the two ends
            box(PAD_X0 + PAD_L - 3.5, PAD_X1 - PAD_L + 3.5, CAV_Y0, CAV_Y1, Z_FLOOR, Z2 + 1),
            box(PAD_X0, PAD_X1, -PAD_HW - 1.0, PAD_HW + 1.0, Z_FLOOR, Z2 + 1),
            peg_holes(Z1), screw_holes(Z1, Z2)]
    cuts += [extrude(hexagon(NUT_POCKET_AF).translate([x, y]), HT - NUT_H, Z2 + 1) for x, y in SCREWS]
    p = p - union(cuts)
    return p + pegs(Z2)


def plate3():
    """Top plate: the lid over the band level, and the nut pockets."""
    p = slab(Z2, HT, chamfer_top=True)
    cuts = [peg_holes(Z2), screw_holes(Z2, HT)]
    cuts += [extrude(hexagon(NUT_POCKET_AF).translate([x, y]), Z2 - 1, HT + 1) for x, y in SCREWS]
    return p - union(cuts)


# ---------------------------------------------------------------- blade, latch block, rail
def blade_outline():
    x0, x1 = CAR_L - 3, CAR_L + BLADE_L
    w = BLADE_W / 2
    pts = [(x0, -w), (CAR_L + 44, -w)]
    for i in range(1, 21):
        t = i / 20
        pts.append((CAR_L + 44 + t * (x1 - CAR_L - 44), -w + (w + 1.5) * t ** 1.8))
    for i in range(1, 21):
        t = 1 - i / 20
        pts.append((CAR_L + 66 + t * (x1 - CAR_L - 66), w - (w - 1.5) * t ** 1.4))
    pts.append((x0, w))
    cs = m3.CrossSection([pts])
    return cs.offset(-2.5, m3.JoinType.Round, 2.0, 32).offset(2.5, m3.JoinType.Round, 2.0, 32)


def arm_gap_poly(deflect):
    """The room under the arm (toward -y) for it to bend in, from root to tip, plus 0.3."""
    L = ARM_ROOT - (BLK_X0 + BLK_L / 2)
    pts = []
    for i in range(0, 21):
        xi = i / 20
        x = ARM_ROOT - xi * (ARM_ROOT - (BLK_X0 - 0.3))
        d = min(1.0, (ARM_ROOT - x) / L)
        dy = deflect * d * d * (3 - d) / 2 + 0.3
        pts.append((x, ARM_Y0 - dy))
    pts += [(BLK_X0 - 0.3, ARM_Y0 + 0.01), (ARM_ROOT, ARM_Y0 + 0.01)]
    return pts


def carrier(c=0.0, arm_deflect=0.0):
    """Blade, carrier, lug and latch arm (the arm drawn bent by arm_deflect toward -y)."""
    z0, z1 = CAR_Z0, CAR_Z1
    body = box(0, CAR_L, -CAR_W / 2, CAR_W / 2, z0, z1) + extrude(blade_outline(), z0, z1)
    deflect_max = NOSE_TOP - (Y_CAM - BLK_D) + 0.1
    cuts = [
        prism(arm_gap_poly(deflect_max), z0 - 1, z1 + 1),                                   # room to bend
        box(BLK_X0 - 0.3, ARM_ROOT, ARM_Y0 - 0.01, ARM_Y0 + ARM_T + 0.3, z0 - 1, z1 + 1),  # the arm, and the gap over it
        box(BLK_X0 - BLK_SLOT, BLK_X0 + BLK_L + BLK_SLOT, ARM_Y0 + ARM_T, CAR_W / 2 + 1, z0 - 1, z1 + 1),  # block slot
        extrude(m3.CrossSection.square([48, 2.6]).translate([CAR_L + 8, 1.6])
                .offset(0.6, m3.JoinType.Round, 2.0, 16), z1 - 0.8, z1 + 1),
    ]
    body = body - union(cuts)
    # the arm and its nose, bent if asked (a straight-line approximation of the bend)
    L = ARM_ROOT - (BLK_X0 + BLK_L / 2)
    arm_pts_top, arm_pts_bot = [], []
    for i in range(0, 21):
        x = ARM_ROOT - i / 20 * (ARM_ROOT - (BLK_X0 + 0.1))
        d = min(1.0, (ARM_ROOT - x) / L)
        dy = arm_deflect * d * d * (3 - d) / 2
        arm_pts_top.append((x, ARM_Y0 + ARM_T - dy))
        arm_pts_bot.append((x, ARM_Y0 - dy))
    arm = prism(arm_pts_top + list(reversed(arm_pts_bot)), z0, z1)
    nose = box(BLK_X0 + 0.1, BLK_X0 + BLK_L - 0.1, ARM_Y0 + ARM_T - 0.01 - arm_deflect, NOSE_TOP - arm_deflect, z0, z1)
    root = box(ARM_ROOT - 0.01, ARM_ROOT + 3.0, ARM_Y0, ARM_Y0 + ARM_T, z0, z1)
    lug = box(LUG_X0, LUG_X0 + LUG_L, -LUG_HW, LUG_HW, z1 - 0.01, LUG_TOP) \
        - box(LUG_X0 - 1, LUG_X0 + LUG_L + 1, -BAND_SLOT, BAND_SLOT, BAND_SLOT_Z, LUG_TOP + 1)
    return union([body, arm, nose, root, lug]).translate([C0 + c, 0, 0])


def latch_block(c=0.0, y_out=Y_OUT):
    """The latch block with its outer face at y_out; its two outer corners chamfered."""
    x0, x1, y1 = BLK_X0, BLK_X0 + BLK_L, y_out
    pts = [(x0, y1 - BLK_D), (x1, y1 - BLK_D), (x1, y1 - BLK_CHAMFER), (x1 - BLK_CHAMFER, y1),
           (x0 + BLK_CHAMFER, y1), (x0, y1 - BLK_CHAMFER)]
    return prism(pts, CAR_Z0, CAR_Z1).translate([C0 + c, 0, 0])


def arm_deflect_for(y_out):
    return NOSE_TOP - (y_out - BLK_D)


def rail(dx=0.0):
    """The rail (latch wall between the windows), shifted dx by its cushion."""
    r = box(RAIL_X0, RAIL_X1, RAIL_Y0, RAIL_Y1, RAIL_Z0, RAIL_TOP)
    tab = box(TAB_X0, TAB_X0 + 4.0, RAIL_Y1 - 0.01, TAB_Y1, RAIL_Z0 + layer(2) + 0.05, RAIL_TOP)
    cham = union([prism([(x, RAIL_Y0 - 0.01), (x + s * RAIL_CHAMFER, RAIL_Y0 - 0.01), (x, RAIL_Y0 + RAIL_CHAMFER)],
                        RAIL_Z0 - 1, RAIL_TOP + 1) for x, s in ((RAIL_X0 - 0.01, 1), (RAIL_X1 + 0.01, -1))])
    return (r - cham + tab).translate([dx, 0, 0])


def rail_cushion():
    """TPU cushion: two pads either side of the rail's tab, joined under it."""
    x0 = TAB_X0 - CUSH_L - 0.1
    y0, y1 = RAIL_Y1 + 0.3, TAB_Y1 + 0.2       # clear of the rail's side, which may lean out 0.2
    top = RAIL_Z0 + layer(16)                  # 4.30, under the bar lane's floor
    pads = union([box(x0, TAB_X0 - 0.1, y0, y1, RAIL_Z0, top),
                  box(TAB_X0 + 4.1, TAB_X0 + 4.1 + CUSH_L, y0, y1, RAIL_Z0, top),
                  box(x0, TAB_X0 + 4.1 + CUSH_L, y0, y1, RAIL_Z0, RAIL_Z0 + layer(2))])
    return pads


# ---------------------------------------------------------------- knob bar and sleds
def cam(x_top, rises_back, z0, z1):
    """A cam on the bar's inner face: a 22 degree ramp up to Y_CAM at x_top, then a flat.
    rises_back: the ramp rises toward -x (cam A, which meets the block from behind)."""
    s = 1 if rises_back else -1
    pts = [(x_top + s * RAMP, Y_OUT + 0.01), (x_top, Y_CAM), (x_top - s * CAM_FLAT, Y_CAM), (x_top - s * CAM_FLAT, Y_OUT + 0.01)]
    return prism(pts, z0, z1)


CAM_A_TOP = X_BLK + C_TRIP - (THROW - 1)           # cam A's top at s = 0: it reaches the block's back corner at s = 27
CAM_B_TOP = X_BLK + TRAVEL - C_TRIP + BLK_L - 1    # cam B's top at s = 0: it reaches the block's front corner at s = 1


def knob_bar(s=0.0):
    """Bar with cam A, cam B, riser F, riser B, the stem and the knob, at knob travel s."""
    x0, x1 = bar_x(0)
    z0, z1 = BAR_Z0, BAR_Z1
    parts = [box(x0, x1, BAR_Y0, BAR_Y1, z0, z1),
             cam(CAM_A_TOP, True, z0, z1), cam(CAM_B_TOP, False, z0, z1)]
    (f0, f1), (b0, b1) = riser_x()
    parts += [box(f0, f1, BAR_Y0, BAR_Y1, z1 - 0.01, RISER_TOP), box(b0, b1, BAR_Y0, BAR_Y1, z1 - 0.01, RISER_TOP)]
    parts += [box(STEM_X0, STEM_X1, BAR_Y1 - 0.01, HW / 2 + 0.4, z0, z1 - 0.2)]
    knob = box(STEM_X0, STEM_X1, HW / 2 + 0.3, HW / 2 + 3.3, z0, KNOB_TOP)
    ridges = union([box(STEM_X0 + 1.5 + 2.5 * i, STEM_X0 + 2.5 + 2.5 * i, HW / 2 + 2.8, HW / 2 + 3.4, z0 - 1, KNOB_TOP + 1)
                    for i in range(5)])
    parts.append(knob - ridges)
    return union(parts).translate([s, 0, 0])


def sled(front_face_x, kind):
    """Sled F (kind 'F': its lug face is its front, +x) or sled B (lug face at its back).
    front_face_x is the x of its lug face."""
    z0, z1 = SLED_Z0, SLED_Z1
    if kind == "F":
        x0, x1 = front_face_x - SLED_LEN, front_face_x
        post_x = front_face_x - POST_BACK
        wing = box(x1 - WING_L, x1, SLED_HW - 0.01, BAR_Y1, z0, z1)
        slot = box(post_x, x1 + 1, -BAND_SLOT, BAND_SLOT, POCKET_Z, z1 + 1)
    else:
        x0, x1 = front_face_x, front_face_x + SLED_LEN
        post_x = front_face_x + POST_BACK
        wing = box(x0, x0 + WING_L, SLED_HW - 0.01, BAR_Y1, z0, z1)
        slot = box(x0 - 1, post_x, -BAND_SLOT, BAND_SLOT, POCKET_Z, z1 + 1)
    eye_d = POST_D + 2 * EYE_PLAY + 2 * BAND_STRONG[1] + 0.6
    body = box(x0, x1, -SLED_HW, SLED_HW, z0, z1) + wing
    body = body - slot - cyl_z(post_x, 0, POCKET_Z, z1 + 1, eye_d, 48)
    return body + cyl_z(post_x, 0, POCKET_Z - 0.01, z1, POST_D, 32)


def sled_positions(c, s):
    """Lug faces of sled F and sled B (x), for blade c and knob s, both resting where the band
    pulls them: F against the lug or its riser, whichever is further back; B the other way."""
    p_f = min(X_L0 - G_P + s, X_L0 + c)
    p_b = max(X_L0 + R_B + s, X_L0 + LUG_L + c)
    return p_f, p_b


def pad(x0):
    return box(x0, x0 + PAD_L, -PAD_HW, PAD_HW, SLED_Z0, SLED_Z1)


# ---------------------------------------------------------------- band
def band_fitted(c, s, band=BAND):
    """The band stretched between the two sleds' posts."""
    p_f, p_b = sled_positions(c, s)
    xa, xb = p_f - POST_BACK, p_b + POST_BACK
    return extrude(band_shape(xa, xb, band[1]), POCKET_Z + 0.01, POCKET_Z + band[0])


def band_shape(xa, xb, w):
    ri = POST_D / 2 + EYE_PLAY
    ring = lambda x: (m3.CrossSection.circle(ri + w, 48) - m3.CrossSection.circle(ri, 48)).translate([x, 0])
    strand = m3.CrossSection.square([xb - xa - 2 * ri - w, w]).translate([xa + ri + w / 2, -w / 2])
    return m3.CrossSection.batch_boolean([ring(xa), ring(xb), strand], m3.OpType.Add)


def band_length(c, s):
    p_f, p_b = sled_positions(c, s)
    return (p_b + POST_BACK) - (p_f - POST_BACK)


def band_print(band):
    return extrude(band_shape(0.0, BAND_RELAXED, band[1]), 0, band[0])


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
    manifold, filament, (x, y) of its lower-left corner on that plate[, own settings]). It
    carries Flash Studio's project settings (flash studio settings.json: AD5X 0.4, 0.20mm
    Standard, Arachne, counterbores partly bridged, filaments 1 white, 2 black, 3 brown) and its
    version tags, or Flash Studio would pile every part on plate 1 and filament 1 (PRINTER-BRAIN).
    Same writer as the shed model's."""
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
ON_INNER_FACE = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0]], dtype=float)  # turned 90 degrees about x: lies on its y-min face


def print_parts():
    """Every part turned the way it prints, sitting on the bed."""
    return {
        "handle 1 base": on_bed(plate1()),
        "handle 2 middle": on_bed(plate2()),
        "handle 3 top": on_bed(plate3().transform(FLIP)),
        "blade": on_bed(carrier()),
        "latch block": on_bed(latch_block()),
        "rail": on_bed(rail().transform(ON_INNER_FACE)),
        "knob slider": on_bed(knob_bar()),
        "sled F": on_bed(sled(0.0, "F")),
        "sled B": on_bed(sled(0.0, "B")),
        "screw": on_bed(screw()),
        "nut": on_bed(nut()),
        "nut loose": on_bed(nut(play=THREAD_PLAY + 0.05, notches=3)),
        "band": on_bed(band_print(BAND)),
        "band strong": on_bed(band_print(BAND_STRONG)),
        "band soft": on_bed(band_print(BAND_SOFT)),
        "pad": on_bed(pad(0.0)),
        "rail cushion": on_bed(rail_cushion()),
    }


def main():
    p = print_parts()
    for name, man in p.items():
        write_stl(man, name + ".stl")
    solid = {"wall_loops": "6", "sparse_infill_density": "100%"}    # printed screws and nuts: solid
    # fit test: one screw and three nuts, a little tighter (1 notch), as printed (2) and looser (3)
    fit = [("screw", p["screw"], 2, (60, 90), solid)]
    for i, play in enumerate((THREAD_PLAY - 0.05, THREAD_PLAY, THREAD_PLAY + 0.05)):
        fit.append((f"nut {i + 1} notch", on_bed(nut(play=play, notches=i + 1)), 2, (90 + 16 * i, 90), solid))
    write_3mf("1 fit test.3mf", [("screw and nuts (black)", fit)])
    x0 = (220 - HL) / 2
    handle_items, y = [], 20.0
    for name in ("handle 1 base", "handle 2 middle", "handle 3 top"):
        handle_items.append((name, p[name], 2, (x0, y)))
        y += HW + 8
    small = [("sled F", p["sled F"], 2, (20, 30)), ("sled B", p["sled B"], 2, (50, 30)),
             ("rail", p["rail"], 2, (20, 70)), ("latch block", p["latch block"], 2, (110, 70))]
    for i in range(4):
        small.append((f"screw {i + 1}", p["screw"], 2, (20 + 16 * i, 100), solid))
        small.append((f"nut {i + 1}", p["nut"], 2, (20 + 14 * i, 125), solid))
    bl, kb = p["blade"], p["knob slider"]
    write_3mf("2 knife plates.3mf", [
        ("handle (black)", handle_items),
        ("small parts (black)", small),
        ("blade and knob slider (white)", [("blade", bl, 1, ((220 - bl.bounding_box()[3]) / 2, 50)),
                                           ("knob slider", kb, 1, ((220 - kb.bounding_box()[3]) / 2, 120))]),
    ])
    bp = p["band"]
    write_3mf("3 TPU parts.3mf", [
        ("TPU parts", [("band", bp, 1, ((220 - bp.bounding_box()[3]) / 2, 70)),
                       ("pad 1", p["pad"], 1, (60, 120)), ("pad 2", p["pad"], 1, (80, 120)),
                       ("rail cushion", p["rail cushion"], 1, (110, 120))]),
    ])
    for name, man in p.items():
        bb = man.bounding_box()
        print(f"{name:18s} {bb[3]-bb[0]:6.1f} x {bb[4]-bb[1]:6.1f} x {bb[5]-bb[2]:5.2f} mm  {man.volume()/1000:5.2f} cm3")


if __name__ == "__main__":
    main()
