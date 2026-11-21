"""8x12 Side Lofted Barn, 1:24 scale, for the Flashforge AD5X.

Run:  python3 make_barn.py      (needs: pip install manifold3d numpy)

Makes the print files in this folder:
  1 fit test.3mf    to try first: plate 1 one short corner of the barn and a stub of its corner
                    angle, plate 2 a doorway, door and roof peg
  2 all plates.3mf  everything, one plate per print, the trim, roof and corner angles already set
                    to filament 2, the floor, skids and lofts to filament 3
  3 corner caps for printed walls.3mf   only for walls printed before Nov 3 2026 (with corner
                    hooks and printed corner boards): four black caps glued over the old boards
  corner angle.stl  the four black corner angles, two of each hand, glued on the corners
  corner cap.stl    the four caps in 3 corner caps for printed walls.3mf
  floor.stl         floor frame and floor sheets, printed upside down; the walls snap onto it
  door wall.stl     the long wall with the door and windows, framing, trim; prints lying
                    flat, inside face down, so the trim is the top few layers
  back wall.stl     the other long wall, the same way
  end wall.stl      print TWO. Barn end with its gable, vent, framing and the roof pegs.
  upper roof.stl    print TWO. The shallow top half of each side of the barn roof.
  lower roof.stl    print TWO. The steep bottom half of each side; the upper one laps over it.
  loft.stl          print TWO. The loft floor at each end, on its joists.
  door.stl          48 in wooden door with its trim, handle and hinge pins, one piece, all
                    one colour; in 2 all plates.3mf its trim is on filament 2
  skids.stl         the two 4x6 skids the floor frame sits on
  fit test.stl      a small doorway, door, roof peg and one short corner of the barn with its
                    stub of corner angle

It is the 8x12 Side Utility model (../shed model 8x12 side utility/make_shed.py), the same
snap joints, door, floor and skids, built as a Side Lofted Barn. Sizes are the shop standard
from the 3D designer (library/manufacturers/standard.json, style SLB, 8x12): 6 ft 7 1/2 in
walls (75 in studs and three 2x4 plates), a barn roof 43 3/4 in from the top of the upper
plate to the peak of the trusses, with its knee 3.04 ft out from the middle, 0.42 ft of eave
down the steep slope and 1.2 in past each end (the upper sheets 1.6 in more), a 4 ft loft at
each end, and the 48 in wooden door (48 1/4 x 71 1/2 in opening) centred on the long side
between two 2x3 windows. The framing follows what Alan taught the designer about this barn
(docs/examples/10x16-side-loft.md there): studs 16 in apart with a double stud every 4 ft,
a 5 in loft header (two 2x4s on edge on a flat one) right under the top plate over the door
and each window, a flat window plate under each window, a 2x6 gable board on each end wall's
upper plate, gable studs 24 in apart from the outside of the end wall, and gable backing
across the gable 11 in above the upper plate.

Axes for the assembled barn: x across the 8 ft width (door wall at +x), y along the
12 ft length, z up. z = 0 is the bottom of the floor joists (where the body sits on the
skids). Every number is millimetres on the model.
"""

import math
import os
import struct

import numpy as np
import manifold3d as m3

M = m3.Manifold
HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "8x12 Side Lofted Barn 1:24"

# ---------------------------------------------------------------- scale
S = 25.4 / 24          # mm on the model per real inch (1:24)
FT = 12 * S

# ---------------------------------------------------------------- the building
W = 8 * FT             # 101.6  width (the barn ends)
L = 12 * FT            # 152.4  length (door side)

TS = 1.4               # siding thickness (thicker than scale so it prints solid)
SD = 3.5 * S           # stud depth (a 2x4 is 3 1/2 in)
SW = 1.6               # stud width (a 2x4 is 1 1/2 in)
WT = TS + SD           # whole wall
RIM = 5.0              # solid band round the edge of the floor, under the walls
JOIST_H = 5.5 * S      # 2x6 joists
DECK = 1.0             # floor sheets
ZF = JOIST_H + DECK    # top of the floor
FLOOR_CLR = 0.4        # gap between the floor's edge and the siding that hangs down over it
WALL_H = 79.5 * S      # floor to top of the upper plate: 75 in studs and three 1 1/2 in plates
ZWT = ZF + WALL_H      # top of the walls

# the barn roof, as the 3D designer draws the shop standard at 8 ft wide (model/roof-shapes.js
# roofProfile with peakIn 43 3/4): the knee 0.38 of the width out from the middle, the roof line
# 2.620 ft up at the knee and 3.684 ft at the peak (44.2 in: the trusses' peak, 43 3/4 in, plus
# the 7/16 in roof deck on them). This line is the underside of the roof sheets.
KNEE_X = 3.04 * FT                  # 38.6
LOWER_RISE = 2.62006174600141 * FT  # 33.27 wall top to knee
UPPER_RISE = 1.064400084313073 * FT # 13.52 knee to peak
ZKN = ZWT + LOWER_RISE
ZPK = ZKN + UPPER_RISE
LOW_M = LOWER_RISE / (W / 2 - KNEE_X)   # the steep lower slope, about 33/12
UP_M = UPPER_RISE / KNEE_X              # the shallow upper slope, about 4.2/12
GABLE = [(-W / 2, 0), (W / 2, 0), (W / 2, ZWT), (KNEE_X, ZKN), (0, ZPK), (-KNEE_X, ZKN), (-W / 2, ZWT)]
EAVE_S = 0.42 * FT     # the lower sheets run on this far down the slope past the wall top
END_OH = 0.10 * FT     # the lower sheets reach this far past each barn end
RAKE_STEP = 0.135 * FT # and the upper sheets this much further (designer's RAKE_STEP)

PLATE_TOP = 3.0 * S    # top plate and upper plate
PLATE_BOT = SW         # bottom plate
HEADER = 5.0 * S       # loft header: two 2x4s on edge on a flat 2x4, touching the top plate
GABLE_BOARD = 5.5 * S  # 2x6 on edge on top of the end wall's upper plate
BACKING_Z = 11 * S     # gable backing: its bottom 11 in above the upper plate, 3 1/2 in high
BACKING_H = 3.5 * S
GABLE_STUD_W = 3.5 * S # gable studs, wide face out, 24 in apart from the outside of the end wall
GABLE_STUD_XS = [-24 * S, 0.0, 24 * S]
COLLAR_H = 3.5 * S     # the end truss: a collar tie across the knees and a king post above it
KING_W = 3.5 * S
GROOVE_OC = 8 * S      # siding grooves 8 in apart
GROOVE_W, GROOVE_D = 0.5, 0.35
TRIM = 3.5 * S         # 1x4 trim boards
PROUD = 0.6            # how far trim stands off the siding
EMBED = 0.4            # trim and window parts reach this far into the siding, so they join it
RAKE_W = 2.0           # the rake board showing under the roof edge round each barn end
BAND_Z = ZWT + 0.40 * (ZPK - ZWT)   # the gable band across each end at the loft line
VENT_FLOOR = 4.25 - WT # the gable vent's louvres sit in a recess this deep in the siding (0.85): in
                       # the end walls' print (inside face down, 0.25 mm first layer, then 0.2) its
                       # floor is the layer line at 4.25, over 3 of the siding's 7 layers (3.65 to
                       # 4.25; the first of them bridges the framing)

# door: 48 in wooden door, opening 48 1/4 x 71 1/2 in (the loft header's underside), hinged on
# the left from outside (-y)
DOOR_OPEN_W = 48.25 * S
DOOR_OPEN_H = 71.5 * S
JAMB = DOOR_OPEN_W / 2
DOOR_R = 1.0           # half the door's thickness; the hinge edge is rounded to this
DOOR_GAP = 0.35        # gap at hinge and latch edges
AXIS_X = W / 2 - 1.8   # hinge pin line, 1.8 mm in from the siding face
AXIS_Y = -JAMB + DOOR_R + DOOR_GAP
DOOR_W = (JAMB - DOOR_GAP) - AXIS_Y      # pin line to latch edge
DOOR_BOTTOM_GAP = 0.3
DOOR_TOP_GAP = 0.6
DOOR_H = DOOR_OPEN_H - DOOR_BOTTOM_GAP - DOOR_TOP_GAP
PIN_D = 2.0
PIN_HOLE_D = 2.7      # 0.35 mm round the pin: holes print small (Alan, Oct 31 2026)
PIN_BOTTOM_LEN = 1.3   # rests on the bottom of a 1.0 deep hole
PIN_TOP_LEN = 2.0
HOLE_BOTTOM_DEPTH = 1.0
TRENCH_DEPTH = 0.7     # the slot the bottom pin slides in through; 0.3 shallower than the hole
HOLE_TOP_DEPTH = 2.2
DOOR_SLAB = 1.4        # panel thickness; trim brings it to 2.0

# windows: 2x3 window, 2.1 x 2.9 ft, each centred between the door opening and the end of the
# wall (as on the Side Utility model, Alan, Oct 31 2026). In a lofted wall the window header
# touches the top plate (Alan), so the window's top is level with the door's. Alan confirmed
# this over the 3D designer's 5 in under the wall top (Nov 2 2026: "The way you have it is right").
WIN_W = 2.1 * FT
WIN_H = 2.9 * FT
WIN_TOP = DOOR_OPEN_H
WIN_YC = (JAMB + L / 2) / 2

# roof sheets
ROOF_T = 2.0
RIB_OC = 9 * S
TAIL = 4 * S           # the upper sheet runs on 4 in past the knee, lapping over the lower one
LAP_GAP = 0.45         # gap between that tail and the top of the lower sheet: as printed, the lower
                       # sheet's tilted peg slots step in layers and it rests up to about 0.3 mm higher
                       # than drawn (second review, Nov 2 2026), so the tail still clears it
PEG_D, PEG_UP = 2.2, 1.0
PEG_HOLE_D, PEG_HOLE_UP = 3.0, 1.4   # 0.4 mm round the peg
PEG_X = KNEE_X / 2     # the upper sheets' pegs, halfway up the shallow slope
# the lower sheets' pegs stand straight up too, from the middle of each steep edge, so a lower
# sheet only lifts off straight up, and the upper sheet's tail is in the way of that. (Square to
# the slope, the sheet's bottom could swing out and it fell off with the barn tipped 20 degrees;
# review, Nov 2 2026.) Each hole sits its clearance further out than its peg, so the sheet rests
# on the pegs where it is drawn instead of sliding down its slope by the clearance.
LOWER_HOLE_SHIFT = (PEG_HOLE_D - PEG_D) / 2
PEG_Y = L / 2 - WT + PEG_D / 2   # against the end walls' inside face, so each peg prints lying on the bed

# loft: a floor of 2x6 joists 16 in apart and a deck, 4 ft in from the outside of each end wall,
# on the long walls' top plates (designer: styles.SLB.loft, depth assumed; part-loft)
LOFT_DEPTH = 4 * FT
LOFT_JOIST = 5.5 * S
LOFT_DECK = 1.0
LOFT_Z = ZWT - 0.15    # bottom of the loft joists: the top of the long walls
LOFT_CLR = 0.4         # clear of the steep roof sheets, square to them
LOFT_END = 0.4         # gap between a loft and the end wall: a loft can slide 0.1 toward it on its
                       # lugs (0.2 before the notch fills, Nov 3 2026)
LUG_U, LUG_D = 1.8, 1.8   # a lug under two of the joists at each wall drops into a notch in the top
                       # plate; 1.8 deep, so it stays in even with the loft lifted up against the roof
LUG_JOISTS = (0, -1)   # the end joist and the edge joist, the same distance from the loft's middle,
                       # so a loft goes in either way round
NOTCH_FILL = 0.3       # 45 degree fill in the corner end of each end joist's notch, at the wall's
                       # inside face (notch_fills()). The lug's corner comes within 0.07 of it;
                       # at 0.25 Flash Studio still warned about the sliver it is there to fill

# skids: 4x6 laid on edge, inside face 30 in in from the outside of the wall
SKID_W = 3.5 * S
SKID_H = 5.5 * S
SKID_X = W / 2 - 28.25 * S
NOTCH = 0.6
NOTCH_CLEAR = 0.6      # 0.3 mm each side of a joist
SKID_PEG_D, SKID_PEG_UP = 2.0, 2.5   # a peg at each end of a skid pushes into the floor

# snap joints, no glue: the same as the Side Utility model (Alan, Nov 1 2026). Each wall stands
# on top of the floor with its siding hanging down over the floor's edge. Under every stud a
# post drops into a notch in the floor's edge, and a few prongs click into slots in the floor.
# A prong is a springy leg that bends in and out of the wall, with a barb on its foot that
# catches under a ledge at the bottom of the slot, and beside it a stiff stop. The barb is built
# up from the bed in layers. On the barn the LONG walls go on first and the end walls last: an
# end wall's tall gable stands over its top corners, so a long wall could not come down past it.
FIT = 0.2              # gap round every post, prong and peg (0.2 a side is snug)
PRONG_W = 3.0          # the leg's width along the wall
PRONG_T = 0.8          # its thickness, the way it bends (4 layers)
BARB = 0.65            # the barb stands this far in from the leg, down to the bed (3 layers)
CATCH = BARB - FIT     # how far it hooks under the ledge
BARB_LAND = 0.6        # straight face between the barb's flat top and its 45 degree lead-in
LEDGE_Z = ZF - 5.25    # the ledge, 1.57 mm up from the bottom of the floor, on a layer line of
                       # the upside-down floor (first layer 0.25, then 0.2)
STOP_W, STOP_GAP, STOP_H = 1.2, 0.4, 3.0   # the stop: width, gap from the leg, how far down it goes
STOP_U = 2.05          # how deep the stop is, on a layer line of the wall's print
SLOT_U = STOP_U + 0.15 # the slot's outside wall
LEG_ROOT = ZF + 1.2    # the leg is freed from the bottom plate up to here
BARB_RELIEF = 0.1      # the barb's top is this much lower on its first layer, for first-layer squish
MITRE_GAP = 0.1        # relief between mitred ends, so they slide past each other going on
MITRE_BEVEL = 0.6      # a 45 degree bevel along the top of each long wall's mitre: an end wall
                       # coming down past a long wall pushed in a little at the top slides off it
                       # instead of landing flat on the mitre's sharp corner (review, Nov 2 2026)

# the corners: the printed hook tips snapped and the corners showed a gap, so there are no hooks
# and no printed corner boards now (Alan, Nov 3 2026). Once the walls are on, a band round them
# pulls the mitres shut and a black corner angle is glued into a recess in both walls at each
# corner. The angles print on their own in filament 2, with the roof.
POCKET_D = 0.4         # the recess: 2 layers of the walls' print (the wall top slices at 5.05,
                       # the recess floor at 4.65)
POCKET_CLR = 0.15      # the recess reaches TRIM + this along each wall from the corner, and this
                       # far over an angle's top
CORNER_CHAMFER = 1.15  # the walls' outside corner is cut off square to the mitre, this far past
                       # where the recess floors meet, so neither wall ends in a knife edge at the
                       # recess floor
ANGLE_T = 1.05         # each leg of an angle, 5 layers thick (0.25 + 4 x 0.2) as it lies on the bed
ANGLE_P = ANGLE_T - POCKET_D   # 0.65, how far an angle stands out of the siding
ANGLE_UP = 0.25 + 20 * 0.2     # 4.25, the end-face leg's width, which stands up in the print: 21
                       # layers. At TRIM + ANGLE_P (4.35) it printed 22 layers, 4.45, and with the
                       # recess floors printing 0.054 deeper than drawn its end met the end of the
                       # recess (review, Nov 3 2026). It covers 3.6 of the end wall.
ANGLE_FILLET = 0.8     # 45 degree fillet in an angle's inside corner, 0.25 clear of the chamfer as
                       # drawn. As printed both are stepped and the angle sits 0.054 deeper, and a
                       # 1.0 fillet ran into the end wall's steps; at 0.8 they miss by 0.04 (review)
ROOF_CLR = 0.2         # the walls' top edges and the angles keep this clear of the lower roof
                       # sheets, square to them
RAKE_CLR = 0.15        # an angle's end-face leg stops this far under the rake board
# caps for walls printed before Nov 3 2026, which have hooks and black corner boards printed on
# them: a black L glued over the old boards at each corner
CAP_T = 0.6            # leg thickness
CAP_CLR = 0.1          # each leg's inside face is this far off the old board's face
CAP_OVER = 0.2         # and it reaches this far past the old board's inner edge, so that edge is
                       # covered
CAP_RELIEF = 0.3       # a 45 degree relief this far into both legs beside its inside corner, and the
                       # corner itself cut back half that, so a blob on the old boards' corner or on
                       # either board's tip can't hold it off (review, Nov 3 2026)


# ---------------------------------------------------------------- helpers
def box(x0, x1, y0, y1, z0, z1):
    return M.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def union(parts):
    parts = [p for p in parts if p is not None]
    return M.batch_boolean(parts, m3.OpType.Add) if len(parts) > 1 else parts[0]


def cyl_z(x, y, z0, z1, d, seg=40):
    return M.cylinder(z1 - z0, d / 2, d / 2, seg).translate([x, y, z0])


def cyl_y(x, y0, y1, z, d, seg=48):
    """Cylinder along y from y0 to y1, centred on (x, z)."""
    c = M.cylinder(y1 - y0, d / 2, d / 2, seg)
    return c.transform(np.array([[1, 0, 0, x], [0, 0, 1, y0], [0, -1, 0, z]], dtype=float))


def cyl_along(p, u, t0, t1, d, seg=40):
    """Cylinder along the direction u = (ux, 0, uz) through the point p, from t0 to t1 along u."""
    phi = math.atan2(u[0], u[2])
    c, s = math.cos(phi), math.sin(phi)
    R = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    cy = M.cylinder(t1 - t0, d / 2, d / 2, seg).translate([0, 0, t0])
    return cy.transform(np.column_stack([R, np.array(p, dtype=float)]))


def prism(poly, ax0, ax1, h, d):
    """Polygon (or CrossSection) in two shed axes (ax0, ax1), extruded d along the third axis h
    from h=0. Built as a right-handed map whatever the axes are."""
    if isinstance(poly, m3.CrossSection):
        cs = poly
    else:
        cs = m3.CrossSection([poly])
        if cs.area() <= 0:
            cs = m3.CrossSection([list(reversed(poly))])
    mat = np.zeros((3, 4))
    mat[ax0, 0] = 1
    mat[ax1, 1] = 1
    mat[h, 2] = 1
    e = M.extrude(cs, d)
    if np.linalg.det(mat[:, :3]) < 0:            # flip the extrusion to stay right-handed
        mat[h, 2] = -1
        mat[h, 3] = d
    return e.transform(mat)


def prism_xz(poly, y0, y1):
    """Polygon in (x, z), extruded along y from y0 to y1."""
    return prism(poly, 0, 2, 1, y1 - y0).translate([0, y0, 0])


def zline(x):
    """Height of the roof line (the underside of the sheets) at x, carried on down the lower
    slope past the wall to the eave."""
    a = abs(x)
    if a <= KNEE_X:
        return ZPK - a * UP_M
    return ZWT + (W / 2 - a) * LOW_M


def unit(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)


def seg_line(seg, side):
    """(point on it, outward unit normal) of one roof slope's underside line in (x, z):
    seg "upper" or "lower", side +1 for the +x side, -1 for the -x side."""
    if seg == "upper":
        a, n = (0.0, ZPK), (UPPER_RISE, KNEE_X)
    else:
        a, n = (W / 2, ZWT), (LOWER_RISE, W / 2 - KNEE_X)
    n = unit(n)
    return np.array([side * a[0], a[1]]), np.array([side * n[0], n[1]])


def under_seg(seg, side, offset):
    """trim_by_plane arguments that keep what is on or under a plane parallel to one roof
    slope's underside, offset mm out from it (square to it)."""
    a, n = seg_line(seg, side)
    return [-n[0], 0.0, -n[1]], -(a @ n + offset)


def lower_mid(side):
    """Middle of the steep edge of each barn end, where the lower sheets' pegs are."""
    return np.array([side * (W / 2 + KNEE_X) / 2, (ZWT + ZKN) / 2])


def layout(start, end, oc):
    out, k = [], 1
    while start + k * oc < end - 0.01:
        out.append(start + k * oc)
        k += 1
    return out


def stud_marks(length):
    """Stud centres along a wall of this length, from its middle: 16 in apart from one end, and
    a double stud at every 4 ft mark, the mark falling between the touching pair (Alan, Sep 28
    2026)."""
    out, k = [], 1
    while k * 16 * S < length - 0.01:
        a = k * 16 * S
        out += [a - 0.75 * S, a + 0.75 * S] if k % 3 == 0 else [a]
        k += 1
    return [a - length / 2 for a in out]


LONG_STUDS = stud_marks(L)
END_STUDS = stud_marks(W)


# ---------------------------------------------------------------- body
def joist_ys():
    """The floor joists between the solid bands at the ends, 16 in apart."""
    return layout(-L / 2, L / 2, 16 * S)


# each wall as (axis it faces along, side): along a wall is y for the long walls, x for the ends
WALL_SIDE = {"door wall": (0, 1), "back wall": (0, -1), "end wall 1": (1, 1), "end wall 2": (1, -1)}


def wall_box(name, a0, a1, u0, u1, z0, z1):
    """A box on one wall: a along the wall, u out from its inside face, z up."""
    axis, sign = WALL_SIDE[name]
    half = (W / 2, L / 2)[axis]
    n0, n1 = sorted([sign * (half - WT + u0), sign * (half - WT + u1)])
    return box(n0, n1, a0, a1, z0, z1) if axis == 0 else box(a0, a1, n0, n1, z0, z1)


def post_spans(name):
    """(start, end) along the wall of each post under it, from z = 0 up to the bottom plate:
    one under every stud, and the door wall's sill under the whole door framing."""
    if WALL_SIDE[name][0] == 0:
        spans = [(a - SW / 2, a + SW / 2) for a in LONG_STUDS]
        if name == "door wall":
            d = JAMB + 2 * SW
            spans = [s for s in spans if s[1] < -d or s[0] > d] + [(-d, d)]
        return spans
    xe = W / 2 - WT - SW / 2
    return [(a - SW / 2, a + SW / 2) for a in END_STUDS + [-xe, xe]]


def wall_section(name, poly, a0, a1):
    """A polygon in (u out from the wall's inside face, z), from a0 to a1 along the wall."""
    axis, sign = WALL_SIDE[name]
    half = (W / 2, L / 2)[axis]
    pts = [(sign * (half - WT + u), z) for u, z in poly]
    t = [0.0, 0.0, 0.0]
    t[1 - axis] = a0
    return prism(pts, axis, 2, 1 - axis, a1 - a0).translate(t)


def prong_spots(name):
    """Where the prongs are along each wall: on the long walls one stud bay in from each corner,
    and the middle of the back wall; on the end walls in the bay next to each corner. Clear of
    the door, the studs, the floor joists and the skids."""
    if WALL_SIDE[name][0] == 0:
        st = layout(-L / 2, L / 2, 16 * S)
        a = (st[-2] + st[-1]) / 2
        return [-a, a] + ([0.0] if name == "back wall" else [])
    a = (END_STUDS[-1] + W / 2 - WT - SW / 2) / 2
    return [-a, a]


def prong_spans(ac):
    """(leg, stop): where the leg and the stop of the prong at ac are along the wall. The stop
    is on the side toward the nearer corner, so the two end walls are alike."""
    s = 1 if ac >= 0 else -1
    leg = (ac - PRONG_W / 2, ac + PRONG_W / 2)
    stop = sorted([ac + s * (PRONG_W / 2 + STOP_GAP), ac + s * (PRONG_W / 2 + STOP_GAP + STOP_W)])
    return leg, tuple(stop)


def prong(name, ac):
    """The prong at ac along a wall. The leg hangs from the bottom plate BARB off the wall's
    inside face; in the print it bridges from the plate to its barb, which stands on the bed.
    The barb's flat top catches under the ledge; below it a straight face and a 45 degree
    lead-in that pushes the leg out as it goes down the slot."""
    (a0, a1), (b0, b1) = prong_spans(ac)
    zc = LEDGE_Z - FIT                                  # flat top of the barb, under the ledge
    zl = zc - BARB_LAND - BARB                          # foot of the lead-in
    barb = [(BARB + 0.1, zc), (0.25, zc), (0.25, zc - BARB_RELIEF), (0, zc - BARB_RELIEF),
            (0, zc - BARB_LAND), (BARB, zl), (BARB + 0.1, zl)]
    return [wall_box(name, a0, a1, BARB, BARB + PRONG_T, zl - 0.05, LEG_ROOT + 0.01),
            wall_section(name, barb, a0, a1),
            wall_box(name, b0, b1, 0, STOP_U, ZF - STOP_H, ZF + 0.3)]


def prong_relief(name, ac):
    """The slot in the bottom plate round the top of the prong's leg, 0.2 all round, so the
    leg bends from LEG_ROOT. It is inside the plate: its inside face is whole."""
    (a0, a1), _ = prong_spans(ac)
    return (wall_box(name, a0 - 0.2, a1 + 0.2, BARB - 0.2, BARB + PRONG_T + 0.2, ZF - 0.5, LEG_ROOT)
            - wall_box(name, a0, a1, BARB, BARB + PRONG_T, ZF - 1, LEG_ROOT + 1))


def under_floor(name):
    """What a wall has below the top of the floor besides its siding: the posts and prongs."""
    parts = [wall_box(name, a0, a1, 0, SD + EMBED, 0, ZF + 0.3) for a0, a1 in post_spans(name)]
    for ac in prong_spots(name):
        parts += prong(name, ac)
    return parts


def floor_cuts():
    """The notches, slots and holes in the floor: a notch round each post and the door sill, a
    slot for each prong, the corners where the corner posts go down, and a hole in each end band
    for a skid peg."""
    c = FIT
    cuts = []
    for name in WALL_SIDE:
        for a0, a1 in post_spans(name):
            cuts.append(wall_box(name, a0 - c, a1 + c, -c, WT + 1, -1, ZF + 1))
        for ac in prong_spots(name):
            (a0, a1), (b0, b1) = prong_spans(ac)
            cuts += [wall_box(name, a0 - c, a1 + c, BARB - c, SLOT_U, -1, ZF + 1),
                     wall_box(name, a0 - c, a1 + c, -c, BARB - c + 0.01, -1, LEDGE_Z),
                     wall_box(name, b0 - c, b1 + c, -c, SLOT_U, -1, ZF + 1)]
    for sx in (1, -1):
        for sy in (1, -1):
            for dx, dy in ((0, SW), (SW, 0)):              # long wall's corner post, end wall's end stud
                xa, xb = sorted([sx * (W / 2 - WT - dx - c), sx * W])
                ya, yb = sorted([sy * (L / 2 - WT - dy - c), sy * L])
                cuts.append(box(xa, xb, ya, yb, -1, ZF + 1))
            cuts.append(cyl_z(sx * SKID_X, sy * (L / 2 - TS - FLOOR_CLR - RIM / 2), -1, SKID_PEG_UP + 0.3,
                              SKID_PEG_D + 2 * c))
    return cuts


def openings():
    """(y0, y1, z0, z1) of every opening in the +x wall."""
    door = (-JAMB, JAMB, ZF, ZF + DOOR_OPEN_H)
    wins = [(yc - WIN_W / 2, yc + WIN_W / 2, ZF + WIN_TOP - WIN_H, ZF + WIN_TOP) for yc in (-WIN_YC, WIN_YC)]
    return door, wins


def long_wall_framing(side, with_openings):
    """Studs, plates and the framing round the door and windows on a long wall. Alan's words:
    beside each opening a full-height stud, and against it the king stud that carries the loft
    header; the header touches the top plate; under a window the flat window plate, on studs
    that keep to the wall's layout."""
    xi, xo = (W / 2 - WT, W / 2 - TS) if side > 0 else (-W / 2 + TS, -W / 2 + WT)
    yin = L / 2 - WT               # inside face of the end walls
    parts = [box(xi, xo, -yin, yin, ZF, ZF + PLATE_BOT),
             box(xi, xo, -yin, yin, ZWT - PLATE_TOP, ZWT)]
    stud_z0, stud_z1 = ZF + PLATE_BOT, ZWT - PLATE_TOP
    ops = []
    if with_openings:
        door, wins = openings()
        ops = [door] + wins
    # end studs (corners)
    parts.append(box(xi, xo, -yin, -yin + SW, stud_z0, stud_z1))
    parts.append(box(xi, xo, yin - SW, yin, stud_z0, stud_z1))
    framed = []
    for (y0, y1, z0, z1) in ops:
        framed.append((y0 - 2 * SW, y1 + 2 * SW, y0, y1, z0, z1))
        for a, b in ((y0 - 2 * SW, y0 - SW), (y1 + SW, y1 + 2 * SW)):        # full-height studs
            parts.append(box(xi, xo, a, b, stud_z0, stud_z1))
        for a, b in ((y0 - SW, y0), (y1, y1 + SW)):                          # king studs
            parts.append(box(xi, xo, a, b, stud_z0, z1))
        parts.append(box(xi, xo, y0 - SW, y1 + SW, z1, min(z1 + HEADER, stud_z1)))   # loft header
        if z0 > ZF + 1:                                                     # window plate
            parts.append(box(xi, xo, y0, y1, z0 - SW, z0))
    for yc in LONG_STUDS:
        a, b = yc - SW / 2, yc + SW / 2
        hit = [f for f in framed if b > f[0] and a < f[1]]
        if not hit:
            parts.append(box(xi, xo, a, b, stud_z0, stud_z1))
            continue
        k0, k1, y0, y1, z0, z1 = hit[0]
        if a >= y0 and b <= y1:
            if stud_z1 - (z1 + HEADER) > 0.05:                               # over the header
                parts.append(box(xi, xo, a, b, z1 + HEADER, stud_z1))
            if z0 > ZF + 1:                                                 # under the window plate
                parts.append(box(xi, xo, a, b, stud_z0, z0 - SW))
    return parts


def knee_inner():
    """The inside corner of the end truss's chords at the knee: where the collar tie's top is."""
    k = np.array([KNEE_X, ZKN])
    dl = unit((W / 2 - KNEE_X, -LOWER_RISE))
    du = unit((-KNEE_X, UPPER_RISE))
    half = math.acos(float(dl @ du)) / 2
    return k + SD / math.sin(half) * unit(dl + du)


COLLAR_TOP = float(knee_inner()[1])


def gable_cs():
    return m3.CrossSection([GABLE])


def end_wall_framing(side):
    """An end wall: plates and studs to the top of the wall; above it the 2x6 gable board on the
    upper plate, the end truss's four chords under the roof line with a collar tie across the
    knees and a king post above it, gable studs 24 in apart standing on the gable board, and
    gable backing across the gable 11 in above the upper plate. Everything runs the full stud
    depth, so the wall prints lying flat on it."""
    yi, yo = (L / 2 - WT, L / 2 - TS) if side > 0 else (-L / 2 + TS, -L / 2 + WT)
    xin = W / 2 - TS
    parts = [box(-xin, xin, yi, yo, ZF, ZF + PLATE_BOT),
             box(-xin, xin, yi, yo, ZWT - PLATE_TOP, ZWT)]
    # end studs stand just inside the long walls, so the mitred end of the end wall rests on
    # a stud's width on the bed rather than a knife edge
    xe = W / 2 - WT - SW / 2
    for xc in [-xe, xe] + END_STUDS:
        parts.append(box(xc - SW / 2, xc + SW / 2, yi, yo, ZF + PLATE_BOT, ZWT - PLATE_TOP))
    gb = W / 2 - 1 * S                       # the gable board stops 1 in short of each end
    parts.append(box(-gb, gb, yi, yo, ZWT, ZWT + GABLE_BOARD))
    parts.append(box(-W / 2, W / 2, yi, yo, ZWT + BACKING_Z, ZWT + BACKING_Z + BACKING_H))
    parts.append(box(-W / 2, W / 2, yi, yo, COLLAR_TOP - COLLAR_H, COLLAR_TOP))
    for xc in GABLE_STUD_XS:
        parts.append(box(xc - GABLE_STUD_W / 2, xc + GABLE_STUD_W / 2, yi, yo,
                         ZWT + GABLE_BOARD, COLLAR_TOP - COLLAR_H))
    parts.append(box(-KING_W / 2, KING_W / 2, yi, yo, COLLAR_TOP, ZPK))
    # the chords: a band one 2x4 deep under the roof line, above the wall plates; 0.2 into the
    # siding so they join it
    g = gable_cs()
    band = (g - g.offset(-SD, m3.JoinType.Miter)) ^ m3.CrossSection.square([2 * W, 400]).translate([-W, ZWT])
    parts.append(prism_xz(band, yi - (0.2 if side < 0 else 0), yo + (0.2 if side > 0 else 0)))
    gable_shape = prism_xz(GABLE, -L, L)
    return union(parts) ^ gable_shape


def window_unit(yc):
    """Double-hung 2x3 window inside its opening on the +x wall: two sashes and their muntins,
    no glass, so you can see in (Alan, Oct 31 2026). The sash frames reach 0.2 mm into the
    jambs so they join the wall."""
    y0, y1 = yc - WIN_W / 2, yc + WIN_W / 2
    z0, z1 = ZF + WIN_TOP - WIN_H, ZF + WIN_TOP
    zm = (z0 + z1) / 2
    xb = W / 2 - WT                   # back of the sashes, flush with the framing, so the wall prints flat
    ring, k, mw = 1.2, 0.2, 0.8
    parts = []
    for (za, zb, xf) in ((zm, z1, W / 2 - 0.45), (z0, zm, W / 2 - 0.15)):    # upper sash sits back
        lo = za - (k if za == z0 else 0)
        hi = zb + (k if zb == z1 else 0)
        parts += [box(xb, xf, y0 - k, y1 + k, lo, za + ring), box(xb, xf, y0 - k, y1 + k, zb - ring, hi),
                  box(xb, xf, y0 - k, y0 + ring, lo, hi), box(xb, xf, y1 - ring, y1 + k, lo, hi),
                  box(xb, xf - 0.15, yc - mw / 2, yc + mw / 2, za, zb),                  # muntins
                  box(xb, xf - 0.15, y0, y1, (za + zb) / 2 - mw / 2, (za + zb) / 2 + mw / 2)]
    return parts


def gable_vent(side):
    """Louvred vent centred under the ridge, 0.92 ft below it, 1.12 x 0.76 ft, in the siding colour
    and none of it out past the siding (Alan, Nov 3 2026: white, but it needn't stand out), so the
    end walls change colour only once. Returns (frame, cuts, slats): the frame is flush with the
    siding, filling its grooves, with a groove round it; inside the frame the louvre field is
    recessed to VENT_FLOOR, and five slats stand in it, wedges that narrow from the recess floor
    up to their front edges at the siding face, so nothing overhangs in the print."""
    vw, vh = 1.12 * FT, 0.76 * FT
    zc = ZPK - 0.92 * FT
    yf = side * L / 2

    def slab(x0, x1, z0, z1, d0, d1):
        """A box from d0 to d1 mm out from the siding face."""
        ya, yb = sorted([yf + side * d0, yf + side * d1])
        return box(x0, x1, ya, yb, z0, z1)
    fr, g = 1.0, GROOVE_W
    x0, x1, z0, z1 = -vw / 2, vw / 2, zc - vh / 2, zc + vh / 2
    frame = slab(x0, x1, z0, z1, -EMBED, 0.0)
    cuts = [slab(x0 - g, x1 + g, z0 - g, z1 + g, -GROOVE_D, 1) - slab(x0, x1, z0, z1, -1, 2),   # groove round it
            slab(x0 + fr, x1 - fr, z0 + fr, z1 - fr, VENT_FLOOR, 1)]                        # the louvre field
    # five louvre slats: wedges, flat underneath, sloping back down into the recess at the top;
    # each front edge is 0.4 tall at the siding face, so it still prints a line wide on the top layer
    inner_h = vh - 2 * fr
    slats = []
    for i in range(5):
        zb = z0 + fr + inner_h * i / 5 + 0.25
        zt = zb + inner_h / 5 - 0.1
        poly = [(yf + side * (VENT_FLOOR - 0.05), zb), (yf, zb), (yf, zb + 0.4), (yf + side * (VENT_FLOOR - 0.05), zt)]
        slats.append(prism(poly, 1, 2, 0, x1 - x0 - 2 * fr).translate([x0 + fr, 0, 0]))
    return frame, cuts, slats


def trims():
    """The gable band at the loft line, the rake board round each barn end under the roof, door
    and window casings (raised so they can be painted). The corners have no boards printed on the
    walls: the corner angles are separate (corner_angle(), Alan, Nov 3 2026)."""
    p = []
    g = gable_cs()
    above = m3.CrossSection.square([4 * W, 400]).translate([-2 * W, ZWT])
    rake = (g.offset(-0.1, m3.JoinType.Miter) - g.offset(-(0.1 + RAKE_W), m3.JoinType.Miter)) ^ above
    gable_shape = prism_xz(GABLE, -L, L)
    for sy in (1, -1):
        ya, yb = sorted([sy * (L / 2 - EMBED), sy * (L / 2 + PROUD)])
        p.append(box(-W / 2, W / 2, ya, yb, BAND_Z, BAND_Z + TRIM) ^ gable_shape)   # gable band
        p.append(prism_xz(rake, ya, yb))                                            # rake board
    xo, xi = W / 2, W / 2 - EMBED
    # door casing: two sides and one head board
    ztop = ZF + DOOR_OPEN_H
    p.append(box(xi, xo + PROUD, -JAMB - TRIM, -JAMB, ZF, ztop + TRIM))
    p.append(box(xi, xo + PROUD, JAMB, JAMB + TRIM, ZF, ztop + TRIM))
    p.append(box(xi, xo + PROUD, -JAMB - TRIM, JAMB + TRIM, ztop, ztop + TRIM))
    # window casings: the same 1x4 board on all four sides (no sill nose; Alan, Oct 31 2026)
    for yc in (-WIN_YC, WIN_YC):
        y0, y1 = yc - WIN_W / 2, yc + WIN_W / 2
        z0, z1 = ZF + WIN_TOP - WIN_H, ZF + WIN_TOP
        p.append(box(xi, xo + PROUD, y0 - TRIM, y0, z0 - TRIM, z1 + TRIM))
        p.append(box(xi, xo + PROUD, y1, y1 + TRIM, z0 - TRIM, z1 + TRIM))
        p.append(box(xi, xo + PROUD, y0 - TRIM, y1 + TRIM, z1, z1 + TRIM))
        p.append(box(xi, xo + PROUD, y0 - TRIM, y1 + TRIM, z0 - TRIM, z0))
    return p


def eave_line(u):
    """Height of the line ROOF_CLR under the steep lower roof sheets, square to them, u mm out
    from the long walls' siding face (in from it where u < 0). The lower sheets reach END_OH past
    each barn end, so it holds over both faces of each corner."""
    return ZWT - u * LOW_M - ROOF_CLR * math.sqrt(1 + LOW_M ** 2)


def roof_clearance():
    """What comes out of the walls for the roof: the long walls stop 0.15 under the wall top, so
    the roof bears on the barn ends only, and everything at or outside the long walls keeps
    ROOF_CLR clear of the steep lower sheets, square to them (the siding's top edge). The corner
    angles and caps keep to the same line (corner_top())."""
    out = []
    for sx in (1, -1):
        a0, a1 = W / 2 - WT - 1, W / 2 + 12
        poly = [(a0, eave_line(a0 - W / 2)), (a1, eave_line(a1 - W / 2)), (a1, 400), (a0, 400)]
        if sx < 0:
            poly = [(-x, z) for (x, z) in reversed(poly)]
        above = prism_xz(poly, -L, L)
        xa, xb = sorted([sx * W / 2, sx * (W / 2 + 12)])
        out.append(above ^ box(xa, xb, -L, L, -1, 400))                   # outside the wall plane
        xa, xb = sorted([sx * (W / 2 - WT - 0.01), sx * (W / 2 + 12)])
        out.append(above ^ box(xa, xb, -L, L, -1, ZWT))                   # the long walls' top edge
        xa, xb = sorted([sx * (W / 2 - WT - 0.01), sx * (W / 2 + 1)])
        out.append(box(xa, xb, -(L / 2 - WT), L / 2 - WT, ZWT - 0.15, 400))
        for sy in (1, -1):                                                 # the long walls' corners too,
            ya, yb = sorted([sy * (L / 2 - WT), sy * (L / 2 + 1)])          # under the end walls' tops
            out.append(box(xa, xb, ya, yb, ZWT - 0.15, ZWT + 0.01) ^ mitred(0, sx))
    return out


def loft_joist_ys():
    """The loft joists at the +y end, from the end wall in: one against the end wall's framing,
    then 16 in apart, and one on the loft's edge."""
    first = L / 2 - WT - LOFT_END - SW / 2
    edge = L / 2 - LOFT_DEPTH + SW / 2
    ys = [first]
    while ys[-1] - 16 * S > edge + SW:
        ys.append(ys[-1] - 16 * S)
    return ys + [edge]


def loft_half_width():
    """How far out from the middle the loft reaches: LOFT_CLR clear of the steep roof sheets,
    square to them, at the top of its deck."""
    top = LOFT_Z + LOFT_JOIST + LOFT_DECK - ZWT
    return W / 2 - (top + LOFT_CLR * math.sqrt(1 + LOW_M ** 2)) / LOW_M


def loft_notches():
    """The notches in the long walls' top plates the loft lugs drop into."""
    out = []
    for sy in (1, -1):
        ys = loft_joist_ys()
        for i in LUG_JOISTS:
            y = sy * ys[i]
            for sx in (1, -1):
                xa, xb = sorted([sx * (W / 2 - WT - 1), sx * (W / 2 - WT + LUG_U + FIT)])
                out.append(box(xa, xb, y - SW / 2 - FIT, y + SW / 2 + FIT, LOFT_Z - LUG_D - FIT, ZWT + 1))
    return out


def notch_fills():
    """A 45 degree fill, NOTCH_FILL each way, in the corner end of the notch for each loft's end
    joist, along the long wall's inside face. With the corner hooks gone (Nov 3 2026) the top
    plate runs on past that notch to the mitre, and where it starts on the bed it was a sliver
    about 0.25 wide that Flash Studio warned about as a floating region; the fill makes it wide
    enough to print. In the print it only widens the first layer."""
    out = []
    y_end = loft_joist_ys()[0] + SW / 2 + FIT
    z0 = LOFT_Z - LUG_D - FIT - 0.01
    for sx in (1, -1):
        for sy in (1, -1):
            xi = sx * (W / 2 - WT)
            tri = [(xi, sy * y_end), (xi, sy * (y_end - NOTCH_FILL)), (xi + sx * NOTCH_FILL, sy * y_end)]
            out.append(prism(tri, 0, 1, 2, ZWT - 0.15 - z0).translate([0, 0, z0]))
    return out


def loft(sy=1):
    """One loft, at the +y end (sy=1) or the -y end: the deck on its joists, which rest on the
    long walls' top plates, with a lug under two of the joists at each wall that drops into a
    notch in the plate, so it can't slide."""
    ys = loft_joist_ys()
    xl = loft_half_width()
    zt = LOFT_Z + LOFT_JOIST
    parts = [box(-xl, xl, L / 2 - LOFT_DEPTH, L / 2 - WT - LOFT_END, zt, zt + LOFT_DECK)]
    for y in ys:
        parts.append(box(-xl, xl, y - SW / 2, y + SW / 2, LOFT_Z, zt + 0.01))
    for i in LUG_JOISTS:
        for sx in (1, -1):
            xa, xb = sorted([sx * (W / 2 - WT + FIT), sx * (W / 2 - WT + LUG_U)])
            parts.append(box(xa, xb, ys[i] - SW / 2, ys[i] + SW / 2, LOFT_Z - LUG_D, LOFT_Z + 0.01))
    f = union(parts)
    return f if sy > 0 else f.mirror([0, 1, 0])


LOFT_TO_PRINT = [[1, 0, 0], [0, -1, 0], [0, 0, -1]]     # upside down, deck on the bed


def floor():
    """Floor frame and floor sheets. The walls stand on it with their siding hanging down over
    its edge, FLOOR_CLR clear of it. It prints upside down, floor face on the bed."""
    xf, yf = W / 2 - TS - FLOOR_CLR, L / 2 - TS - FLOOR_CLR
    cuts = []
    edges = [-(yf - RIM)] + [e for j in joist_ys() for e in (j - SW / 2, j + SW / 2)] + [yf - RIM]
    for a, b in zip(edges[0::2], edges[1::2]):
        cuts.append(box(-xf + RIM, xf - RIM, a, b, -1, ZF - DECK))
    # floor sheet seams: two rows of 4x8 sheets across the width, each row an 8 ft and a 4 ft
    # sheet, the seams staggered (Alan, Sep 27 2026), inside the walls
    xi, yi = W / 2 - WT, L / 2 - WT
    for x0, x1, ys in ((-xi, 0, [24 * S]), (0, xi, [-24 * S])):
        for y in ys:
            cuts.append(box(x0, x1, y - 0.2, y + 0.2, ZF - 0.25, ZF + 0.01))
    cuts.append(box(-0.2, 0.2, -yi, yi, ZF - 0.25, ZF + 0.01))
    return box(-xf, xf, -yf, yf, 0, ZF) - union(cuts + floor_cuts())


FLOOR_TO_PRINT = [[1, 0, 0], [0, -1, 0], [0, 0, -1]]     # upside down


def roof_pegs():
    """The pegs on the barn ends the roof sheets sit on: a peg standing straight up halfway up
    each slope of each barn end, standing PEG_UP proud of the roof line, square to it."""
    pegs = []
    for sx in (1, -1):
        nu, ou = under_seg("upper", sx, PEG_UP)
        nl, ol = under_seg("lower", sx, PEG_UP)
        m = lower_mid(sx)
        for sy in (1, -1):
            x = sx * PEG_X
            pegs.append(cyl_z(x, sy * PEG_Y, zline(x) - 3, zline(x) + 3, PEG_D).trim_by_plane(nu, ou))
            pegs.append(cyl_z(m[0], sy * PEG_Y, m[1] - 4, m[1] + 8, PEG_D).trim_by_plane(nl, ol))
    return pegs


def walls():
    """All four walls in one, assembled; split_walls() cuts them apart for printing."""
    shell = prism_xz(GABLE, -L / 2, L / 2)
    # the siding only; below the floor's top it is the skirt that hangs over the floor's edge
    cuts = [box(-W / 2 + TS, W / 2 - TS, -L / 2 + TS, L / 2 - TS, -1, 400)]
    # siding grooves
    for y in layout(-L / 2, L / 2, GROOVE_OC):
        for sx in (1, -1):
            xa, xb = sorted([sx * (W / 2 - GROOVE_D), sx * (W / 2 + 1)])
            cuts.append(box(xa, xb, y - GROOVE_W / 2, y + GROOVE_W / 2, -1, ZWT + 1))
    for x in layout(-W / 2, W / 2, GROOVE_OC):
        for sy in (1, -1):
            ya, yb = sorted([sy * (L / 2 - GROOVE_D), sy * (L / 2 + 1)])
            cuts.append(box(x - GROOVE_W / 2, x + GROOVE_W / 2, ya, yb, -1, ZPK + 1))
    shell = shell - union(cuts)

    framing = long_wall_framing(+1, True) + long_wall_framing(-1, False)
    framing += [end_wall_framing(+1), end_wall_framing(-1)]
    for name in WALL_SIDE:
        framing += under_floor(name)
    for sx in (1, -1):              # corner posts, solid into the corner so each wall's mitred end is a solid
        for sy in (1, -1):          # 45 degree wedge; they go down through the floor's corners
            xa, xb = sorted([sx * (W / 2 - WT), sx * (W / 2 - TS)])
            ya, yb = sorted([sy * (L / 2 - TS), sy * (L / 2 - WT - SW)])
            framing.append(box(xa, xb, ya, yb, 0, ZWT))
    b = union([shell] + framing + trims())
    b = b - union([prong_relief(name, ac) for name in WALL_SIDE for ac in prong_spots(name)])

    door, wins = openings()
    op_cuts = []
    for (y0, y1, z0, z1) in [door] + wins:
        op_cuts.append(box(W / 2 - WT - 0.5, W / 2 + 2, y0, y1, z0, z1))
    b = b - union(op_cuts)
    vents = [gable_vent(1), gable_vent(-1)]
    b = union([b] + window_unit(-WIN_YC) + window_unit(WIN_YC) + [v[0] for v in vents])
    b = union([b - union([c for v in vents for c in v[1]])] + [sl for v in vents for sl in v[2]])

    # door stop inside the latch jamb, so the door only swings out. It runs back to the inside
    # face of the framing so the wall prints flat.
    door_inner = AXIS_X - DOOR_R
    b = b + box(W / 2 - WT, door_inner - 0.2, JAMB - 0.8, JAMB + 0.2, ZF, ZF + DOOR_OPEN_H)
    # hinge pin holes and the slot the bottom pin slides in through
    holes = [cyl_z(AXIS_X, AXIS_Y, ZF - HOLE_BOTTOM_DEPTH, ZF + 1, PIN_HOLE_D),
             cyl_z(AXIS_X, AXIS_Y, ZF + DOOR_OPEN_H - 1, ZF + DOOR_OPEN_H + HOLE_TOP_DEPTH, PIN_HOLE_D),
             box(AXIS_X, W / 2 + 2, AXIS_Y - PIN_HOLE_D / 2, AXIS_Y + PIN_HOLE_D / 2, ZF - TRENCH_DEPTH, ZF + 1)]
    b = b - union(holes + roof_clearance() + loft_notches())
    return b + union(roof_pegs() + notch_fills())


def body():
    """The assembled body: four walls and the floor."""
    return union(list(wall_pieces(walls()).values()) + [floor()])


# the four walls meet at 45 degree mitres through the inside and outside corners, so each
# wall carries only the trim on its own face and it all prints on top (Alan, Nov 1 2026). Each
# prints lying flat on the inside face of its framing, outside up. At each outside corner both
# walls have a recess for a corner angle glued on after (Alan, Nov 3 2026).
BIG = 500


def mitred(axis, sign):
    """The region one wall owns: outside its inside face, and on its side of the mitre at
    each end. axis 0 for a long wall, 1 for an end wall; sign which side of the barn."""
    half = (W / 2, L / 2)
    a, b = axis, 1 - axis
    n = [0.0, 0.0, 0.0]
    n[a] = sign
    r = M.cube([2 * BIG] * 3, True).trim_by_plane(n, half[a] - WT)
    for end in (1, -1):
        n = [0.0, 0.0, 0.0]
        n[a], n[b] = sign / math.sqrt(2), -end / math.sqrt(2)
        r = r.trim_by_plane(n, (half[a] - half[b]) / math.sqrt(2) + MITRE_GAP / 2)
    return r


def above_plate(sign):
    """Above the top of the wall plates on one end of the barn: all of it goes with the end
    wall, where it lies on the bed."""
    return M.cube([2 * BIG] * 3, True).trim_by_plane([0, 0, 1], ZWT).trim_by_plane([0, sign, 0], 0)


WALL_CUTS = {
    "door wall": mitred(0, 1) - above_plate(1) - above_plate(-1),
    "back wall": mitred(0, -1) - above_plate(1) - above_plate(-1),
    "end wall 1": mitred(1, 1) + above_plate(1),
    "end wall 2": mitred(1, -1) + above_plate(-1),
}
# barn coords to print coords, inside face down (each a rotation, det +1)
WALL_TO_PRINT = {
    "door wall": [[0, 1, 0], [0, 0, 1], [1, 0, 0]],
    "back wall": [[0, -1, 0], [0, 0, 1], [-1, 0, 0]],
    "end wall 1": [[-1, 0, 0], [0, 0, 1], [0, 1, 0]],
    "end wall 2": [[1, 0, 0], [0, 0, 1], [0, -1, 0]],
}


def split_walls(w):
    return {name: w ^ cut for name, cut in WALL_CUTS.items()}


def cbox(u0, u1, v0, v1, z0, z1):
    """A box at the (+x, +y) corner: u out from the long wall's siding face, v out from the end
    wall's, z up. The outside corner of the siding is u = v = 0."""
    return box(W / 2 + u0, W / 2 + u1, L / 2 + v0, L / 2 + v1, z0, z1)


def at_corner(m, sx, sy):
    """A part made at the (+x, +y) corner, moved to the corner on side sx of the width and sy of
    the length: mirrored, so each corner gets its own hand. The (+, +) and (-, -) corners take
    the same part turned round, and so do (+, -) and (-, +)."""
    m = m if sx > 0 else m.mirror([1, 0, 0])
    return m if sy > 0 else m.mirror([0, 1, 0])


def corner_top(m, out, cap, lift=0.0):
    """m, at the (+x, +y) corner, with its top cut off: a 45 degree slope rising inward from the
    line ROOF_CLR under the lower roof sheets (eave_line()) at m's outside face, out mm past the
    long wall's siding, so the steep roof stays clear of all of it and it still prints lying on
    that face; and nothing above cap. lift raises the slope and the cap."""
    c = eave_line(out) + out + W / 2 + lift                      # the slope: x + z = c
    r = m.trim_by_plane([-1 / math.sqrt(2), 0, -1 / math.sqrt(2)], -c / math.sqrt(2))
    return r ^ box(-BIG, BIG, -BIG, BIG, -BIG, cap + lift)


def corner_angle(sx=1, sy=1):
    """The black L glued on a corner (Alan, Nov 3 2026), made at (+x, +y) and moved to (sx, sy):
    a leg on each wall's face, ANGLE_T thick, its inside face on the floor of the recess in the
    wall and ANGLE_P of it out of the siding, with a 45 degree fillet in its inside corner. The
    long-face leg covers TRIM of the long wall and the end of the other leg; the end-face leg is
    ANGLE_UP wide, a whole number of layers as it stands in the print, and covers 3.6 of the end
    wall. Its foot is level with the bottom of the skirts. Its top keeps ROOF_CLR under the lower
    roof sheets (they reach past the barn ends, so the end-face leg is under one too), and the
    end-face leg stops RAKE_CLR under the rake board. It prints lying on the long-face leg's
    outside face, the end-face leg standing up."""
    d, f, e = POCKET_D, ANGLE_FILLET, 0.2
    x, y = W / 2 - d, L / 2 - d                                   # the inside corner of the legs
    # the fillet reaches e into the legs, so it joins them
    fillet = prism([(x - f, y + e), (x - f, y), (x, y - f), (x + e, y - f), (x + e, y + e)], 0, 1, 2, ZWT)
    a = union([cbox(-d, ANGLE_P, -TRIM, ANGLE_P, 0, ZWT), cbox(ANGLE_P - ANGLE_UP, ANGLE_P, -d, ANGLE_P, 0, ZWT),
               fillet])
    return at_corner(corner_top(a, ANGLE_P, ZWT - RAKE_CLR), sx, sy)


def corner_recess(sx=1, sy=1):
    """What comes out of the walls at a corner for its angle, made at (+x, +y) and moved to (sx,
    sy): a recess POCKET_D deep in each wall's face, reaching TRIM + POCKET_CLR along it from the
    corner, from under the skirts up to POCKET_CLR over the angle's top (open at the top where the
    wall stops lower); and the walls' outside corner cut off at 45 degrees, square to the mitre,
    CORNER_CHAMFER past where the recess floors meet. The long wall's recess has a level top
    POCKET_CLR over the angle's highest point there, its inside top edge, so the angle presses
    straight in under it; sloped like the angle's top, it hung over that edge (review, Nov 3
    2026). The chamfer runs on up past the recess to the top of the corner, so it never stops
    against the bevel on a long wall's mitre in a sliver thinner than a line. Neither goes higher
    than the top of the wall plates, where the rake board starts."""
    c, d = TRIM + POCKET_CLR, POCKET_D
    k = -(2 * d + CORNER_CHAMFER)                                 # the chamfer: u + v > k
    h = 1 / math.sqrt(2)
    chamfer = cbox(-4, 2, -4, 2, -1, ZWT).trim_by_plane([h, h, 0], (k + W / 2 + L / 2) * h)
    top = eave_line(ANGLE_P) + ANGLE_P + d + POCKET_CLR           # POCKET_CLR over the angle's inside top edge
    end_recess = corner_top(cbox(-c, 2, -d, 2, -1, ZWT), ANGLE_P, ZWT - POCKET_CLR, lift=POCKET_CLR)
    return at_corner(union([cbox(-d, 2, -c, 2, -1, top), end_recess, chamfer]), sx, sy)


def corner_cap(sx=1, sy=1):
    """For walls printed before Nov 3 2026, which have black corner boards printed on them (PROUD
    out of the siding, TRIM wide from the corner, meeting at the mitre) and hooks: a black L
    glued over the old boards at a corner, made at (+x, +y) and moved to (sx, sy). Each leg is
    CAP_T thick, its inside face CAP_CLR off the old board's face, and reaches CAP_OVER past the
    old board's inner edge. Beside its inside corner a 45 degree relief, CAP_RELIEF each way, is
    cut into both legs, and the corner itself is cut back CAP_RELIEF / 2, which leaves room for
    a blob on the old boards' corner or on either board's tip. (Cut back the full CAP_RELIEF, the
    corner left a strip under the standing leg too thin to print, and Flash Studio warned of
    floating regions.) Its foot is level with the bottom of the skirts, its top keeps ROOF_CLR
    under the lower roof sheets (lower than an angle's, as it stands further out) and the end-face
    leg stops RAKE_CLR under the old rake board. It prints like the angles."""
    a = PROUD + CAP_CLR
    b, c, r = a + CAP_T, TRIM + CAP_OVER, CAP_RELIEF
    legs = union([cbox(a, b, -c, b, 0, ZWT), cbox(-c, b, a, b, 0, ZWT)])
    x, y = W / 2 + a, L / 2 + a                                   # the inside corner
    relief = prism([(x - r, y), (x, y - r), (x + r, y), (x + r / 2, y), (x, y + r / 2), (x, y + r)],
                   0, 1, 2, ZWT + 2).translate([0, 0, -1])
    return at_corner(corner_top(legs - relief, b, ZWT - RAKE_CLR), sx, sy)


CORNERS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
# a corner angle or cap from barn coords to print coords: lying on the long-face leg's outside
# face, its foot at the left, the end-face leg standing up (each a rotation, det +1)
CORNER_TO_PRINT = {1: [[0, 0, 1], [0, 1, 0], [-1, 0, 0]], -1: [[0, 0, 1], [0, -1, 0], [1, 0, 0]]}


def corner_walls(sx, sy):
    """(long wall, end wall) that meet at the corner on side sx, sy."""
    return ("door wall" if sx > 0 else "back wall"), ("end wall 1" if sy > 0 else "end wall 2")


def corner_prints(make):
    """The four corner angles (make=corner_angle) or caps (make=corner_cap), each lying the way
    it prints: [(name, part)]."""
    return [("%s at %s" % corner_walls(sx, sy), to_print(CORNER_TO_PRINT[sx], [make(sx, sy)])[0])
            for sx, sy in CORNERS]


def mitre_bevels(sx):
    """The bevel along the top edge of the long wall's mitre at each end (side sx): in the upright
    plane square to the mitre, a 45 degree triangle MITRE_BEVEL each way off the corner."""
    out = []
    z_top = ZWT - 0.15
    for sy in (1, -1):
        n = np.array([sx, -sy, 0.0]) / math.sqrt(2)            # into the long wall, square to the mitre
        t = np.array([sx, sy, 0.0]) / math.sqrt(2)             # along the mitre
        p0 = np.array([sx * (W / 2 - WT), sy * (L / 2 - WT), 0.0]) + n * MITRE_GAP / 2
        cs = m3.CrossSection([[(-0.5, z_top - MITRE_BEVEL - 0.5), (MITRE_BEVEL, z_top), (MITRE_BEVEL, z_top + 1),
                               (-0.5, z_top + 1)]])
        run = 2 * WT * math.sqrt(2) + 4
        ez = t if np.linalg.det(np.column_stack([n, [0, 0, 1], t])) > 0 else -t
        mat = np.column_stack([n, [0, 0, 1], ez, p0 - ez * run / 2])
        out.append(M.extrude(cs, run).transform(mat))
    return out


def wall_pieces(w):
    """The four walls cut apart at the mitres, with the recesses for the corner angles cut in
    every corner and the bevels on the long walls' mitres."""
    pieces = split_walls(w)
    recesses = union([corner_recess(sx, sy) for sx, sy in CORNERS])
    for name in pieces:
        cuts = [recesses] + (mitre_bevels(WALL_SIDE[name][1]) if WALL_SIDE[name][0] == 0 else [])
        pieces[name] = pieces[name] - union(cuts)
    return pieces


def trim_zone():
    """Everything standing proud of the siding that is trim (gable band, rake board, door and
    window casings). It prints in the second colour."""
    return union(trims()) - box(-W / 2, W / 2, -L / 2, L / 2, -1, 400)


def two_colour(piece, zone):
    """(siding colour, trim colour) parts of a piece."""
    return piece - zone, piece ^ zone


def to_print(mat, parts):
    """Rotate parts together by mat and put them on the bed as one."""
    m = np.column_stack([np.array(mat, dtype=float), np.zeros(3)])
    out = [p.transform(m) for p in parts]
    bb = union(out).bounding_box()
    return [p.translate([-bb[0], -bb[1], -bb[2]]) for p in out]


# ---------------------------------------------------------------- roof
def panel_frame(a, b):
    """Matrix taking a roof sheet's own coords (X = y along the barn, Y = up from its underside,
    Z = down the slope from a) to barn coords, for the slope from a to b in (x, z)."""
    a = np.asarray(a, dtype=float)
    d = unit(np.asarray(b, dtype=float) - a)
    nrm = np.array([-d[1], d[0]])                  # out of the roof, for a +x slope
    return np.column_stack([[0, 1, 0], [nrm[0], 0, nrm[1]], [d[0], 0, d[1]], [a[0], 0, a[1]]])


def ribbed_sheet(ly, z0, z1, cap=False):
    """A flat sheet in its own coords, ribs every 9 in running down it."""
    parts = [box(-ly, ly, 0, ROOF_T, z0, z1)]
    rib = m3.CrossSection([[(-0.7, ROOF_T - 0.05), (0.7, ROOF_T - 0.05), (0.3, ROOF_T + 0.6), (-0.3, ROOF_T + 0.6)]])
    for k in range(-20, 21):
        y = k * RIB_OC
        if abs(y) <= ly - 2:
            parts.append(M.extrude(rib.translate([y, 0]), z1 - z0).translate([0, 0, z0]))
    if cap:
        parts.append(box(-ly, ly, ROOF_T - 0.1, ROOF_T + 1.7, z0, 5.5))    # ridge cap
    return union(parts)


UPPER_A, UPPER_B = (0.0, ZPK), (KNEE_X, ZKN)
EAVE_END = tuple(np.array([W / 2, ZWT]) + EAVE_S * unit((W / 2 - KNEE_X, -LOWER_RISE)))
LOWER_A, LOWER_B = (KNEE_X, ZKN), EAVE_END


def upper_panel():
    """The +x upper roof sheet in barn coords (the -x one is its mirror image): ridge to knee,
    and its tail on past the knee over the lower sheet, with the ridge cap along its top. It
    sits on the barn ends, held by a peg at each end."""
    mat = panel_frame(UPPER_A, UPPER_B)
    lu = math.dist(UPPER_A, UPPER_B)
    ly = L / 2 + END_OH + RAKE_STEP
    r = ribbed_sheet(ly, -5, lu + TAIL, cap=True).transform(mat)
    r = r.trim_by_plane([1, 0, 0], 0.1)                                     # ridge gap 0.1 per side
    nrm, off = under_seg("upper", 1, PEG_HOLE_UP)
    holes = [cyl_z(PEG_X, sy * PEG_Y, zline(PEG_X) - 5, zline(PEG_X) + 5, PEG_HOLE_D).trim_by_plane(nrm, off)
             for sy in (1, -1)]
    return r - union(holes)


def lower_panel():
    """The +x lower roof sheet in barn coords: knee to eave, its top cut to the line of the upper
    sheet, which laps over it. It sits on the steep edges of the barn ends, on a peg standing up
    at each end, so it only comes off straight up, and the upper sheet's tail is in the way of
    that."""
    mat = panel_frame(LOWER_A, LOWER_B)
    ll = math.dist(LOWER_A, LOWER_B)
    ly = L / 2 + END_OH
    r = ribbed_sheet(ly, -6, ll).transform(mat)
    nrm, off = under_seg("upper", 1, -LAP_GAP)
    r = r.trim_by_plane(nrm, off)
    m = lower_mid(1)
    nh, oh = under_seg("lower", 1, PEG_HOLE_UP)
    holes = [cyl_z(m[0] + LOWER_HOLE_SHIFT, sy * PEG_Y, m[1] - 8, m[1] + 8, PEG_HOLE_D).trim_by_plane(nh, oh)
             for sy in (1, -1)]
    return r - union(holes)


def panel_to_print(r, a, b):
    """Lay a +x roof sheet on the bed, underside down: X down the slope, Y along the barn."""
    mat = panel_frame(a, b)
    R, p0 = mat[:, :3], mat[:, 3]
    to_local = np.column_stack([R.T, -R.T @ p0])                          # (y, n, s)
    swap = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], dtype=float)        # (s, y, n), det +1
    p = r.transform(np.column_stack([swap @ to_local[:, :3], swap @ to_local[:, 3]]))
    bb = p.bounding_box()
    return p.translate([-bb[0], -bb[1], -bb[2]])


# ---------------------------------------------------------------- door
def door_parts():
    """Door in print coords: X across the door from the pin line, Y up the door from its
    bottom, Z through it (Z=0 is the inside face, on the bed). Returns (white, black)."""
    t = 2 * DOOR_R
    slab = box(0, DOOR_W, 0, DOOR_H, 0, DOOR_SLAB)
    edge = cyl_y(0, 0, DOOR_H, DOOR_R, 2 * DOOR_R)                         # rounded hinge edge
    hinge_fill = box(0, 1.0, 0, DOOR_H, 0, t)
    pin_top = cyl_y(0, DOOR_H - 0.5, DOOR_H + PIN_TOP_LEN, DOOR_R, PIN_D, 40)
    pin_bot = cyl_y(0, -PIN_BOTTOM_LEN, 0.5, DOOR_R, PIN_D, 40)
    white = union([slab, edge, hinge_fill, pin_top, pin_bot])
    # siding grooves on the panels, lined up with the wall's
    grooves = []
    for y in layout(-L / 2, L / 2, GROOVE_OC):
        u = y - AXIS_Y
        if 4 < u < DOOR_W - 4:
            grooves.append(box(u - GROOVE_W / 2, u + GROOVE_W / 2, -1, DOOR_H + 1, DOOR_SLAB - 0.3, DOOR_SLAB + 1))
    white = white - union(grooves)

    z0, z1 = DOOR_SLAB, t
    tw = TRIM
    black = [box(0, tw, 0, DOOR_H, z0, z1), box(DOOR_W - tw, DOOR_W, 0, DOOR_H, z0, z1),
             box(0, DOOR_W, DOOR_H - tw, DOOR_H, z0, z1), box(0, DOOR_W, 0, tw, z0, z1)]
    ym = 0.52 * DOOR_H
    black.append(box(0, DOOR_W, ym - tw / 2, ym + tw / 2, z0, z1))

    def tri(ax, ay, bx, by, cx, cy):
        return prism([(ax, ay), (bx, by), (cx, cy)], 0, 1, 2, z1 - z0).translate([0, 0, z0])
    leg = 7.0
    xl, xr = tw, DOOR_W - tw
    lo0, lo1 = tw, ym - tw / 2
    up1 = DOOR_H - tw
    black += [tri(xl, lo0, xl + leg, lo0, xl, lo0 + leg), tri(xr, lo0, xr, lo0 + leg, xr - leg, lo0),
              tri(xl, lo1, xl, lo1 - leg, xl + leg, lo1), tri(xr, lo1, xr - leg, lo1, xr, lo1 - leg),
              tri(xl, up1, xl, up1 - leg, xl + leg, up1), tri(xr, up1, xr - leg, up1, xr, up1 - leg)]
    # pull handle, 0.44 ft in from the latch edge: a D-shaped pull standing 2.6 mm off the panel,
    # with a 1.8 mm gap under the grip to hook a fingernail in (Alan, Nov 1 2026)
    hx, hy = DOOR_W - 0.44 * FT, 0.45 * DOOR_H
    hw, hl, post, grip = 1.4, 3.5, 1.2, 0.8
    top = z1 + 2.0
    black += [box(hx - hw / 2, hx + hw / 2, hy - hl, hy - hl + post, z0, top),
              box(hx - hw / 2, hx + hw / 2, hy + hl - post, hy + hl, z0, top),
              box(hx - hw / 2, hx + hw / 2, hy - hl, hy + hl, top - grip, top)]
    black = union(black) - white
    return white, black


def door_to_shed(theta_deg=0.0):
    """Matrix from door print coords to barn coords, swung open theta degrees."""
    base = np.array([[0, 0, 1, AXIS_X - DOOR_R], [1, 0, 0, AXIS_Y], [0, 1, 0, ZF + DOOR_BOTTOM_GAP]], dtype=float)
    th = math.radians(-theta_deg)                                          # outward = latch edge to +x
    rot = np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]])
    pivot = np.array([AXIS_X, AXIS_Y, 0])
    R = rot @ base[:, :3]
    t = rot @ (base[:, 3] - pivot) + pivot
    return np.column_stack([R, t])


# ---------------------------------------------------------------- skids
def skid():
    """One skid lying along X, notched where the joists, the floor's end bands and the end
    walls' siding sit on it, with a peg at each end that pushes up into the end band."""
    s = box(0, L, 0, SKID_W, 0, SKID_H)
    cuts = []
    for jy in joist_ys():
        y = jy + L / 2
        cuts.append(box(y - SW / 2 - NOTCH_CLEAR / 2, y + SW / 2 + NOTCH_CLEAR / 2, -1, SKID_W + 1, SKID_H - NOTCH, SKID_H + 1))
    end = TS + FLOOR_CLR + RIM + 0.3
    cuts.append(box(-1, end, -1, SKID_W + 1, SKID_H - NOTCH, SKID_H + 1))
    cuts.append(box(L - end, L + 1, -1, SKID_W + 1, SKID_H - NOTCH, SKID_H + 1))
    s = s - union(cuts)
    pegs = [cyl_z(X, SKID_W / 2, SKID_H - NOTCH - 0.01, SKID_H - NOTCH + SKID_PEG_UP, SKID_PEG_D)
            for X in (TS + FLOOR_CLR + RIM / 2, L - (TS + FLOOR_CLR + RIM / 2))]
    return s + union(pegs)


def skids():
    """Both skids side by side for printing."""
    s = skid()
    return s + s.translate([0, SKID_W + 6, 0])


def skids_to_shed():
    """Matrices placing skid() under the floor frame, joists down in the notches."""
    return [np.array([[0, -1, 0, sx * SKID_X + SKID_W / 2], [1, 0, 0, -L / 2], [0, 0, 1, -(SKID_H - NOTCH)]], dtype=float)
            for sx in (-1, 1)]


# ---------------------------------------------------------------- fit test
FIT_LONG, FIT_END = "back wall", "end wall 1"     # the corner the fit test copies (no window over it)
FIT_STUB = 20.0                                   # length of its stub of corner angle, from the foot


def corner_test(pieces, f):
    """The corner where the back wall meets end wall 1, made short: the bottom 8 mm of each
    wall above the floor joined to its top 10 mm below the wall top, on that corner of the
    floor (the end wall's gable left off), and the bottom FIT_STUB of that corner's angle. The
    walls have a real prong, posts, skirt and the recesses and chamfer for the angle. Each wall
    is cut along the far side of a stud, so the siding at the cut is held. Returns (long wall,
    end wall, floor, angle stub) in barn coords."""
    z_lo, z_hi = ZF + 8, ZWT - 10
    y0 = layout(-L / 2, L / 2, 16 * S)[-2] - SW / 2
    x0 = END_STUDS[-1] - SW / 2

    def short(piece, xa, xb, ya, yb):
        keep = box(xa, xb, ya, yb, -5, ZWT)
        lo = piece ^ keep ^ box(-BIG, BIG, -BIG, BIG, -5, z_lo)
        hi = piece ^ keep ^ box(-BIG, BIG, -BIG, BIG, z_hi, ZWT)
        return lo + hi.translate([0, 0, z_lo - z_hi])
    stub = corner_angle(WALL_SIDE[FIT_LONG][1], WALL_SIDE[FIT_END][1]) ^ box(-BIG, BIG, -BIG, BIG, -1, FIT_STUB)
    return (short(pieces[FIT_LONG], -W / 2 - 2, -(W / 2 - 10), y0, L / 2 + 2),
            short(pieces[FIT_END], -W / 2 - 2, -x0, L / 2 - 10, L / 2 + 2),
            f ^ box(-W / 2, -x0, y0, L / 2, -5, 400), stub)


def corner_test_parts(pieces, f):
    """The short corner and its angle stub from corner_test(), each lying the way it prints:
    [(name, part)]."""
    lw, ew, fl, stub = corner_test(pieces, f)
    return [("short long wall", to_print(WALL_TO_PRINT[FIT_LONG], [lw])[0]),
            ("short end wall", to_print(WALL_TO_PRINT[FIT_END], [ew])[0]),
            ("bit of floor", to_print(FLOOR_TO_PRINT, [fl])[0]),
            ("corner angle stub", to_print(CORNER_TO_PRINT[WALL_SIDE[FIT_LONG][1]], [stub])[0])]


def fit_test(pieces=None, whole_floor=None):
    """A short doorway with the same pin holes, slot and stop, a short door with the same
    pins, and a block with a roof peg next to a roof coupon with the peg hole. The doorway and
    the peg block print lying flat, inside face down, the way the door wall and the end walls
    do. With the walls and floor given, the short corner and its angle stub from
    corner_test_parts() go in a row behind them."""
    ow, oh = 14.0, 24.0
    jamb = ow / 2
    ax_x, ax_y = W / 2 - 1.8, -jamb + DOOR_R + DOOR_GAP
    x0 = W / 2 - WT                                   # inside face, as thick as the wall
    base = box(x0, W / 2, -jamb - 6, jamb + 6, 0, 3.0)
    frame = [base, box(x0, W / 2, -jamb - 6, -jamb, 3.0, 3.0 + oh + 6),
             box(x0, W / 2, jamb, jamb + 6, 3.0, 3.0 + oh + 6),
             box(x0, W / 2, -jamb - 6, jamb + 6, 3.0 + oh, 3.0 + oh + 6)]
    f = union(frame)
    zf = 3.0
    inner = ax_x - DOOR_R
    f = f + box(x0, inner - 0.2, jamb - 0.8, jamb + 0.2, zf, zf + oh)
    f = f - union([cyl_z(ax_x, ax_y, zf - HOLE_BOTTOM_DEPTH, zf + 1, PIN_HOLE_D),
                   cyl_z(ax_x, ax_y, zf + oh - 1, zf + oh + HOLE_TOP_DEPTH, PIN_HOLE_D),
                   box(ax_x, W / 2 + 2, ax_y - PIN_HOLE_D / 2, ax_y + PIN_HOLE_D / 2, zf - TRENCH_DEPTH, zf + 1)])
    f = on_bed(f.transform(np.column_stack([np.array(WALL_TO_PRINT["door wall"], dtype=float), np.zeros(3)])))
    fw = f.bounding_box()[3]
    # small door with the same pin and edge
    dw = (jamb - DOOR_GAP) - ax_y
    dh = oh - DOOR_BOTTOM_GAP - DOOR_TOP_GAP
    d = union([box(0, dw, 0, dh, 0, 2 * DOOR_R),
               cyl_y(0, 0, dh, DOOR_R, 2 * DOOR_R),
               cyl_y(0, dh - 0.5, dh + PIN_TOP_LEN, DOOR_R, PIN_D, 40),
               cyl_y(0, -PIN_BOTTOM_LEN, 0.5, DOOR_R, PIN_D, 40)])
    d = d.translate([fw + 6, 3 + PIN_BOTTOM_LEN, 0])
    # roof peg on a block lying like an end wall, so the peg sticks out sideways lying on the
    # bed, as the end walls' pegs do; stand it up to try the coupon on it
    bx = fw + 6 + d.bounding_box()[3] - d.bounding_box()[0] + 12
    blk = box(-6, 6, 0, 6, 0, WT) + cyl_y(0, 5, 6 + PEG_UP, PEG_D / 2, PEG_D)
    blk = blk.translate([bx, 3, 0])
    cpn = box(-6, 6, -6, 6, 0, ROOF_T) - cyl_z(0, 0, -1, PEG_HOLE_UP, PEG_HOLE_D)
    cpn = cpn.translate([bx, 22, 0])
    row = [f, d, blk, cpn]
    if pieces is not None:
        y = union(row).bounding_box()[4] + 6
        x = 0
        for _, pp in corner_test_parts(pieces, whole_floor):
            row.append(pp.translate([x, y, 0]))
            x += pp.bounding_box()[3] + 6
    return union(row)


# ---------------------------------------------------------------- files
def write_stl(man, name):
    mesh = man.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].astype(np.float32)
    t = np.asarray(mesh.tri_verts)
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    n = np.cross(b - a, c - a)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    n = n / np.where(ln == 0, 1, ln)
    path = os.path.join(HERE, name)
    with open(path, "wb") as f:
        f.write(NAME.encode().ljust(80, b" "))
        f.write(struct.pack("<I", len(t)))
        rec = np.zeros(len(t), dtype=[("n", "<f4", 3), ("a", "<f4", 3), ("b", "<f4", 3), ("c", "<f4", 3), ("x", "<u2")])
        rec["n"], rec["a"], rec["b"], rec["c"] = n, a, b, c
        f.write(rec.tobytes())
    return path


def write_3mf(name, plates):
    """A plain 3MF project for Orca. plates: [(plate name, items), ...], each a plate in Orca in
    that order. items: (object name, [(part name, manifold, filament), ...], (x, y)) placed with
    its lower-left corner at x, y on its plate. An object with two parts opens in Orca as one
    object, each part already set to its filament (1 siding, 2 trim and roof, 3 floor, skids
    and lofts)."""
    import zipfile
    from xml.sax.saxutils import quoteattr

    # Orca lays plates out in a grid, a fifth of a bed apart, as many columns as the square
    # root of the plate count rounded up; objects carry that plate's offset
    root = math.sqrt(len(plates))
    cols = round(root) + (1 if root > round(root) else 0)
    stride = 220 * 1.2
    res, build, cfg, plate_cfg, oid = [], [], [], [], 1
    for i, (plate_name, items) in enumerate(plates):
        ox, oy = (i % cols) * stride, -(i // cols) * stride
        plate_cfg.append(f'<plate><metadata key="plater_id" value="{i + 1}"/>'
                         f'<metadata key="plater_name" value={quoteattr(plate_name)}/>'
                         f'<metadata key="locked" value="false"/>')
        for obj_name, parts, (x, y) in items:
            bb = union([m for _, m, _ in parts]).bounding_box()
            # store each object's shape centred on its own middle and place that middle on the
            # plate, the way Flash Studio saves its own projects
            mid = np.array([(bb[0] + bb[3]) / 2, (bb[1] + bb[4]) / 2, (bb[2] + bb[5]) / 2])
            comp_ids = []
            cfg.append(f'<object id="{oid + len(parts)}"><metadata key="name" value={quoteattr(obj_name)}/>'
                       f'<metadata key="extruder" value="{parts[0][2]}"/>')
            for part_name, man, filament in parts:
                cfg.append(f'<part id="{oid}" subtype="normal_part"><metadata key="name" value={quoteattr(part_name)}/>'
                           f'<metadata key="extruder" value="{filament}"/></part>')
                mesh = man.to_mesh()
                v = np.asarray(mesh.vert_properties)[:, :3] - mid
                t = np.asarray(mesh.tri_verts)
                vs = "".join(f'<vertex x="{a:.4f}" y="{b:.4f}" z="{c:.4f}"/>' for a, b, c in v)
                ts = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in t)
                res.append(f'<object id="{oid}" name={quoteattr(part_name)} type="model"><mesh>'
                           f'<vertices>{vs}</vertices><triangles>{ts}</triangles></mesh></object>')
                comp_ids.append(oid)
                oid += 1
            comps = "".join(f'<component objectid="{c}"/>' for c in comp_ids)
            res.append(f'<object id="{oid}" name={quoteattr(obj_name)} type="model"><components>{comps}</components></object>')
            build.append(f'<item objectid="{oid}" transform="1 0 0 0 1 0 0 0 1 '
                         f'{ox + x + mid[0] - bb[0]:.4f} {oy + y + mid[1] - bb[1]:.4f} {mid[2] - bb[2]:.4f}"/>')
            cfg.append('</object>')
            plate_cfg.append(f'<model_instance><metadata key="object_id" value="{oid}"/>'
                             f'<metadata key="instance_id" value="0"/></model_instance>')
            oid += 1
        plate_cfg.append('</plate>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<metadata name="Title">{NAME}</metadata>'
             # Flash Studio opens a file as a project, plates and parts where they were put and each
             # part on its filament, only if it carries project settings (flash studio settings.json,
             # saved from Flash Studio: AD5X 0.4, 0.20mm Standard, Arachne, filaments 1 white,
             # 2 black, 3 brown) and these version tags. Without them it centres everything on
             # plate 1 and puts every part on filament 1 (Nov 2 2026). It says the file is from a
             # newer version: click OK.
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


def build():
    parts = {}
    f = floor()
    pieces = wall_pieces(walls())
    parts["body"] = union(list(pieces.values()) + [f])
    parts["floor"] = f
    parts.update(pieces)
    parts["upper"] = upper_panel()
    parts["lower"] = lower_panel()
    parts["loft"] = loft(1)
    white, black = door_parts()
    parts["door"], parts["door_trim"] = white, black
    parts["skids"] = skids()
    parts["fit"] = fit_test(pieces, f)
    return parts


def wall_parts(p, name, zone):
    """(siding, trim) of a wall, lying flat on the bed."""
    return to_print(WALL_TO_PRINT[name], two_colour(p[name], zone))


def size(m):
    """Width and depth of a part on the bed."""
    bb = m.bounding_box()
    return bb[3] - bb[0], bb[4] - bb[1]


def stacked(parts, gap=6.0):
    """[(name, part)] one behind the other along y, gap apart, as one part (for an .stl)."""
    out, y = [], 0.0
    for _, m in parts:
        out.append(m.translate([0, y, 0]))
        y += size(m)[1] + gap
    return union(out)


def plates(p):
    """The plates of each Orca project, from build()'s parts, as write_3mf() takes them:
    {file name: [(plate name, items)]}.

    2 all plates.3mf has a plate for each print, in the Side Utility's order: both long walls,
    the roof and the corner angles, the door, both end walls, then the floor, skids and lofts.
    Filament 1 is the siding colour (white), filament 2 the trim, roof and corner angles (black),
    filament 3 the floor, skids and lofts (brown, Alan Nov 2 2026). The prime tower goes at x 165,
    y 195 on every plate, so the two-colour plates keep that corner clear."""
    zone = trim_zone()
    walls_p = {name: wall_parts(p, name, zone) for name in WALL_CUTS}
    fl = to_print(FLOOR_TO_PRINT, [p["floor"]])[0]
    lf = to_print(LOFT_TO_PRINT, [p["loft"]])[0]
    up = panel_to_print(p["upper"], UPPER_A, UPPER_B)
    lo = panel_to_print(p["lower"], LOWER_A, LOWER_B)
    skid_p = skid().transform(np.array([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0]], dtype=float))
    loft_p = lf.transform(np.array([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0]], dtype=float))
    door = p["door"] + p["door_trim"]

    def wall_item(name, x, y):
        siding, trim = walls_p[name]                 # the back wall has no trim now
        return (name, [("siding", siding, 1)] + ([] if trim.is_empty() else [("trim", trim, 2)]), (x, y))

    def row(parts, filament, y=None):
        """[(name, part)] side by side along x, 6 mm apart, the row centred on the bed."""
        x = (220 - sum(size(m)[0] for _, m in parts) - 6 * (len(parts) - 1)) / 2
        out = []
        for name, m in parts:
            out.append((name, [(name, m, filament)], (x, (220 - size(m)[1]) / 2 if y is None else y)))
            x += size(m)[0] + 6
        return out

    def column(parts, filament):
        """[(name, part)] one behind the other along y, 6 mm apart, centred on the bed."""
        y = (220 - sum(size(m)[1] for _, m in parts) - 6 * (len(parts) - 1)) / 2
        out = []
        for name, m in parts:
            out.append((name, [(name, m, filament)], ((220 - size(m)[0]) / 2, y)))
            y += size(m)[1] + 6
        return out

    # the fit test: what is new on its own plate, the rest as it was
    fit = fit_test()
    tw, th = size(fit)
    fit_test_3mf = [("new corner", row(corner_test_parts({n: p[n] for n in WALL_CUTS}, p["floor"]), 1)),
                    ("fit test", [("fit test", [("fit test", fit, 1)], ((220 - tw) / 2, (220 - th) / 2))])]

    lh = size(union(walls_p["door wall"]))[1]
    y0 = (220 - 2 * lh - 3) / 2
    ew = size(union(walls_p["end wall 1"]))[0]
    dw, dh = size(door)
    uw, uh = size(up)
    lw_, lh_ = size(lo)
    rx = (220 - (2 * uw + 2 * lw_ + 3 * 4)) / 2
    # the corner angles: two end to end in the strip in front of the roof sheets, two behind them
    angles = [("corner angle, " + n, m) for n, m in corner_prints(corner_angle)]
    ay = ((220 - uh) / 2 - size(angles[0][1])[1]) / 2
    fw, fh = size(fl)
    sw_, sh_ = size(skid_p)
    lfw, lfh = size(loft_p)
    fx = (220 - (fw + 2 * sw_ + lfw + 18)) / 2
    all_plates = [
        ("long walls", [wall_item("door wall", 3, y0), wall_item("back wall", 3, y0 + lh + 3)]),
        ("roof and corner angles",                                                             # filament 2
         [("upper roof 1", [("upper roof", up, 2)], (rx, (220 - uh) / 2)),
          ("upper roof 2", [("upper roof", up, 2)], (rx + uw + 4, (220 - uh) / 2)),
          ("lower roof 1", [("lower roof", lo, 2)], (rx + 2 * uw + 8, (220 - lh_) / 2)),
          ("lower roof 2", [("lower roof", lo, 2)], (rx + 2 * uw + lw_ + 12, (220 - lh_) / 2))]
         + row(angles[:2], 2, ay) + row(angles[2:], 2, 220 - ay - size(angles[0][1])[1])),
        ("door", [("door", [("door", p["door"], 1), ("door trim", p["door_trim"], 2)],
                   ((220 - dw) / 2, (190 - dh) / 2))]),
        ("end walls", [wall_item("end wall 1", (220 - 2 * ew - 6) / 2, 4),
                       wall_item("end wall 2", (220 + 6) / 2, 4)]),
        ("floor, skids and lofts", [
            ("floor", [("floor", fl, 3)], (fx, (220 - fh) / 2)),                   # brown
            ("skid 1", [("skid", skid_p, 3)], (fx + fw + 6, (220 - sh_) / 2)),
            ("skid 2", [("skid", skid_p, 3)], (fx + fw + sw_ + 12, (220 - sh_) / 2)),
            ("loft 1", [("loft", loft_p, 3)], (fx + fw + 2 * sw_ + 18, (220 - 2 * lfh - 6) / 2)),
            ("loft 2", [("loft", loft_p, 3)], (fx + fw + 2 * sw_ + 18, (220 + 6) / 2))]),
    ]
    caps = [("corner cap, " + n, m) for n, m in corner_prints(corner_cap)]
    return {"1 fit test.3mf": fit_test_3mf,
            "2 all plates.3mf": all_plates,
            "3 corner caps for printed walls.3mf": [("corner caps", column(caps, 2))]}


def main():
    p = build()
    zone = trim_zone()
    walls_p = {name: wall_parts(p, name, zone) for name in WALL_CUTS}
    fl = to_print(FLOOR_TO_PRINT, [p["floor"]])[0]
    lf = to_print(LOFT_TO_PRINT, [p["loft"]])[0]
    up = panel_to_print(p["upper"], UPPER_A, UPPER_B)
    lo = panel_to_print(p["lower"], LOWER_A, LOWER_B)
    write_stl(fl, "floor.stl")
    write_stl(union(walls_p["door wall"]), "door wall.stl")
    write_stl(union(walls_p["back wall"]), "back wall.stl")
    write_stl(union(walls_p["end wall 1"]), "end wall.stl")
    write_stl(up, "upper roof.stl")
    write_stl(lo, "lower roof.stl")
    write_stl(lf, "loft.stl")
    write_stl(p["door"] + p["door_trim"], "door.stl")
    write_stl(p["skids"], "skids.stl")
    write_stl(on_bed(p["fit"]), "fit test.stl")
    write_stl(stacked(corner_prints(corner_angle)), "corner angle.stl")
    write_stl(stacked(corner_prints(corner_cap)), "corner cap.stl")
    for name, pl in plates(p).items():
        write_3mf(name, pl)
    for name, (siding, trim) in walls_p.items():
        bb = union([siding, trim]).bounding_box()
        print(f"{name:10s} flat {bb[3]-bb[0]:7.1f} x {bb[4]-bb[1]:7.1f} x {bb[5]-bb[2]:6.1f} mm  " +
              ("no trim" if trim.is_empty() else
               f"trim {trim.volume()/1000:5.2f} cm3, from {trim.bounding_box()[2]:.2f} mm up"))
    corners = [("angle flat", corner_prints(corner_angle)[0][1]), ("cap flat", corner_prints(corner_cap)[0][1])]
    for k, v in list(p.items()) + [("upper flat", up), ("lower flat", lo), ("loft flat", lf)] + corners:
        bb = v.bounding_box()
        print(f"{k:10s} {bb[3]-bb[0]:7.1f} x {bb[4]-bb[1]:7.1f} x {bb[5]-bb[2]:6.1f} mm  "
              f"{v.volume()/1000:6.1f} cm3  {v.num_tri()} triangles")


if __name__ == "__main__":
    main()
