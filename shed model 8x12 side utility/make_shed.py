"""8x12 Side Utility shed, 1:24 scale, for the Flashforge AD5X.

Run:  python3 make_shed.py      (needs: pip install manifold3d numpy)

Makes the print files in this folder:
  1 fit test.3mf  two plates to try first: one short corner of the shed with a stub of corner
                  angle, then a doorway, door and roof peg
  2 all plates.3mf  everything, one plate per print, the trim, roof and corner angles already set
                  to filament 2, the floor and skids to filament 3
  floor.stl       floor frame and floor sheets, printed upside down; the walls snap onto it
  door wall.stl   the long wall with the door and windows, framing, trim; prints lying
                  flat, inside face down, so the trim is the top few layers
  back wall.stl   the other long wall, the same way; it has no trim
  end wall.stl    print TWO. Gable end with its vent, framing and the roof pegs.
                  (walls print flat so the trim can be a second colour, Alan Nov 1 2026)
  roof half.stl   print TWO. Each half lifts straight off its two pegs.
  corner angle.stl  the four black L angles glued over the corners, two of each hand
  door.stl        48 in wooden door with its trim, handle and hinge pins, one piece, all
                  one colour; in 2 all plates.3mf its trim is on filament 2
  skids.stl       the two 4x6 skids the floor frame sits on
  fit test.stl    the short corner, angle stub, small doorway, door and roof peg, all on one
                  plate in one colour

Sizes are the shop standard from the 3D designer (library/manufacturers/standard.json,
style SU): 8 ft x 12 ft, 7 ft 9 1/2 in walls, 5/12 roof, 4 in eaves, 48 in wooden door
(48 1/4 x 76 1/2 in opening) centred on the long side, a 2x3 window centred between the
door and each end wall.

Axes for the assembled shed: x across the 8 ft width (door wall at +x), y along the
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

# ---------------------------------------------------------------- scale
S = 25.4 / 24          # mm on the model per real inch (1:24)
FT = 12 * S

# ---------------------------------------------------------------- the building
W = 8 * FT             # 101.6  width (gable ends)
L = 12 * FT            # 152.4  length (door side)
PITCH = 5 / 12
ALPHA = math.atan(PITCH)
EAVE = 4 * S           # level overhang past the long walls
RAKE = 0.45 * FT       # overhang past the gable ends

TS = 1.4               # siding thickness (thicker than scale so it prints solid)
SD = 3.5 * S           # stud depth (a 2x4 is 3 1/2 in)
SW = 1.6               # stud width (a 2x4 is 1 1/2 in)
WT = TS + SD           # whole wall
RIM = 5.0              # solid band round the edge of the floor, under the walls
JOIST_H = 5.5 * S      # 2x6 joists
DECK = 1.0             # floor sheets
ZF = JOIST_H + DECK    # top of the floor
FLOOR_CLR = 0.4        # gap between the floor's edge and the siding that hangs down over it; the
                       # siding prints as bridges between posts there and may sag toward the floor,
                       # and its first layer starts 0.05 nearer than drawn (at a layer line)
WALL_H = 93.5 * S      # floor to top of the top plate
ZWT = ZF + WALL_H      # top of the walls
ZPK = ZWT + (W / 2) * PITCH   # peak of the roof underside

PLATE_TOP = 3.0 * S    # double top plate
PLATE_BOT = SW         # bottom plate
HEADER = 5.5 * S       # 2x6 headers
GROOVE_OC = 8 * S      # siding grooves 8 in apart
GROOVE_W, GROOVE_D = 0.5, 0.35
TRIM = 3.5 * S         # 1x4 trim boards
PROUD = 0.6            # how far trim stands off the siding
EMBED = 0.4            # trim and window parts reach this far into the siding, so they join it
VENT_DEPTH = WT - 4.25 # the gable vent's louvres sit in a recess this deep in the siding: its floor
                       # is on the 4.25 layer line of the end wall's print, with 3 layers of siding
                       # under it (3.65 to 4.25), and nothing of the vent stands out past the siding
                       # (Alan, Nov 3 2026: keep it white, it needn't stick out)
VENT_SLAT = 0.45       # height of each louvre's front edge, at the siding face; a line wide in the print

# door: 48 in wooden door, opening 48 1/4 x 76 1/2 in, hinged on the left from outside (-y)
DOOR_OPEN_W = 48.25 * S
DOOR_OPEN_H = 76.5 * S
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

# windows: 2x3 window, 2.1 x 2.9 ft, sill 2.9 ft above the floor, each centred between the door
# opening and the end of the wall (Alan, Oct 31 2026); the corner angle reaches TRIM along the
# wall from the corner, the same as a casing's width, so it is also centred between the door
# casing and the corner angle
WIN_W = 2.1 * FT
WIN_H = 2.9 * FT
WIN_SILL = 2.9 * FT
WIN_YC = (JAMB + L / 2) / 2

# roof
ROOF_T = 2.0
RIB_OC = 9 * S
PEG_D, PEG_UP = 2.2, 1.0
PEG_HOLE_D, PEG_HOLE_UP = 3.0, 1.4   # 0.4 mm round the peg
PEG_X = W / 4
PEG_Y = L / 2 - WT / 2

# skids: 4x6 laid on edge, inside face 30 in in from the outside of the wall
SKID_W = 3.5 * S
SKID_H = 5.5 * S
SKID_X = W / 2 - 28.25 * S
NOTCH = 0.6
NOTCH_CLEAR = 0.6      # 0.3 mm each side of a joist
SKID_PEG_D, SKID_PEG_UP = 2.0, 2.5   # a peg at each end of a skid pushes into the floor

# snap joints, no glue (Alan, Nov 1 2026). Each wall stands on top of the floor with its siding
# hanging down over the floor's edge. Under every stud a post drops into a notch in the floor's
# edge, and a few prongs click into slots in the floor. A prong is a springy leg that bends in
# and out of the wall, with a barb on its foot that catches under a ledge at the bottom of the
# slot, and beside it a stiff stop that keeps the wall's foot from moving out. The walls print
# inside face down, so the barb is built up from the bed in layers: a barb drawn the other way,
# in the bed plane, came out narrower than a line and the slicer rounded it off (review, Nov 1
# 2026). The long walls go on last; the corner angles then tie the corners together.
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
SLOT_U = STOP_U + 0.15 # the slot's outside wall: the foot moves out 0.15 at most, so the barb
                       # still hooks 0.3 under its ledge, and the bent leg has 0.25 to spare
LEG_ROOT = ZF + 1.2    # the leg is freed from the bottom plate up to here (a slot round it in
                       # the plate), so it is 6.6 mm long and bends 1.2 %, not 1.8 % from a
                       # square corner at the plate's face (second review, Nov 2 2026)
BARB_RELIEF = 0.1      # the barb's top is this much lower on its first layer, for first-layer
                       # squish, which the slicer doesn't compensate on such a small island
MITRE_GAP = 0.1        # relief between mitred ends, so they slide past each other going on

# corner angles (Alan, Nov 3 2026). On the barn the corner hooks' 1.0 x 1.2 mm tips snapped and
# the corners stood open a little, so the hooks are gone and the corners are glued instead. Each
# corner gets a separate black L angle, printed on the roof plate, that sits in a shallow recess
# in both walls' outside faces next to the corner, covers the mitre and is glued to both walls.
# It takes the place of the two printed corner boards.
POCKET_D = 0.4         # depth of the recess: two layers of the wall's print (its siding's top layer
                       # is at 5.05 and the recess floor at 4.65)
POCKET_CLR = 0.15      # gap round the angle's edges in the recess
CORNER_CHAMFER = 1.15  # a 45 degree chamfer off the walls' outer corner, square to the mitre, this
                       # far each way from where the two recess floors meet, so neither wall ends in
                       # a knife edge at its recess floor
ANGLE_T = 1.05         # thickness of each leg, 5 layers (0.25 + 4 x 0.2); it stands 0.65 proud
ANGLE_FILLET = 0.8     # 45 degree fillet in its inside corner, 0.25 clear of the chamfer as drawn. As
                       # printed both are stepped by the layers and the recess floors come out 0.054
                       # deeper (4.65), so a 1.0 fillet ran into the end wall's steps and held the
                       # angle 0.05 off its floor; at 0.8 its steps miss the walls' by 0.04 or more
                       # (review, Nov 3 2026)
ANGLE_UP = 0.25 + 20 * 0.2   # width of the end-face leg, which stands up in the print: 21 layers.
                       # The long-face leg is TRIM + 0.65 = 4.35 wide; drawn that wide the standing
                       # leg would print 22 layers (4.45) and nearly close its gap in the recess
ANGLE_ROOF = 0.2       # its top is this far under the roof, square to the roof


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


def prism(poly, ax0, ax1, h, d):
    """Polygon in two shed axes (ax0, ax1), extruded d along the third axis h from h=0.
    Built as a right-handed map whatever the axes are."""
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
    return ZWT + (W / 2 - abs(x)) * PITCH


def under_roof(side, offset):
    """Keep what is on or under a plane parallel to one roof half's underside.
    side +1 for the +x half, -1 for the -x half; offset in mm measured square to the roof."""
    n = math.sqrt(1 + PITCH ** 2)
    normal = [-side * PITCH / n, 0, -1 / n]
    c = (ZWT + PITCH * W / 2) / n
    return normal, -(c + offset)


def layout(start, end, oc):
    out, k = [], 1
    while start + k * oc < end - 0.01:
        out.append(start + k * oc)
        k += 1
    return out


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
        spans = [(a - SW / 2, a + SW / 2) for a in layout(-L / 2, L / 2, 16 * S)]
        if name == "door wall":
            d = JAMB + 2 * SW
            spans = [s for s in spans if s[1] < -d or s[0] > d] + [(-d, d)]
        return spans
    xe = W / 2 - WT - SW / 2
    return [(a - SW / 2, a + SW / 2) for a in layout(-W / 2, W / 2, 16 * S) + [-xe, xe]]


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
    the door, the floor joists and the skids."""
    if WALL_SIDE[name][0] == 0:
        st = layout(-L / 2, L / 2, 16 * S)
        a = (st[-2] + st[-1]) / 2
        return [-a, a] + ([0.0] if name == "back wall" else [])
    a = (layout(-W / 2, W / 2, 16 * S)[-1] + W / 2 - WT - SW / 2) / 2
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
    slot for each prong (room for the leg to bend out as the barb goes down, the ledge with the
    undercut the barb springs into, and a closer fit round the stop), the corners where the
    corner posts go down, and a hole in each end band for a skid peg."""
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
    wins = [(yc - WIN_W / 2, yc + WIN_W / 2, ZF + WIN_SILL, ZF + WIN_SILL + WIN_H) for yc in (-WIN_YC, WIN_YC)]
    return door, wins


def long_wall_framing(side, with_openings):
    """Studs, plates, kings, jacks, headers, sills and cripples on a long wall."""
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
        k0, k1 = y0 - 2 * SW, y1 + 2 * SW
        framed.append((k0, k1, y0, y1, z0, z1))
        for a, b in ((y0 - 2 * SW, y0 - SW), (y1 + SW, y1 + 2 * SW)):        # kings
            parts.append(box(xi, xo, a, b, stud_z0, stud_z1))
        for a, b in ((y0 - SW, y0), (y1, y1 + SW)):                          # jacks
            parts.append(box(xi, xo, a, b, stud_z0, z1))
        parts.append(box(xi, xo, y0 - SW, y1 + SW, z1, z1 + HEADER))         # header
        if z0 > ZF + 1:                                                     # window: rough sill
            parts.append(box(xi, xo, y0, y1, z0 - SW, z0))
    for yc in layout(-L / 2, L / 2, 16 * S):
        a, b = yc - SW / 2, yc + SW / 2
        hit = [f for f in framed if b > f[0] and a < f[1]]
        if not hit:
            parts.append(box(xi, xo, a, b, stud_z0, stud_z1))
            continue
        k0, k1, y0, y1, z0, z1 = hit[0]
        if a >= y0 and b <= y1:                                            # cripples
            parts.append(box(xi, xo, a, b, z1 + HEADER, stud_z1))
            if z0 > ZF + 1:
                parts.append(box(xi, xo, a, b, stud_z0, z0 - SW))
    return parts


def end_wall_framing(side):
    """Plates, studs and the end truss's top chords on a gable end."""
    yi, yo = (L / 2 - WT, L / 2 - TS) if side > 0 else (-L / 2 + TS, -L / 2 + WT)
    xin = W / 2 - TS
    parts = [box(-xin, xin, yi, yo, ZF, ZF + PLATE_BOT),
             box(-xin, xin, yi, yo, ZWT - PLATE_TOP, ZWT)]
    # end studs stand just inside the long walls, so the mitred end of the gable wall rests on
    # a stud's width on the bed rather than a knife edge
    xe = W / 2 - WT - SW / 2
    for xc in [-xe, xe] + layout(-W / 2, W / 2, 16 * S):
        parts.append(box(xc - SW / 2, xc + SW / 2, yi, yo, ZF + PLATE_BOT, ZPK))
    # top chords: a band one 2x4 deep under the roof line. The walls print flat, so it runs
    # the full stud depth (it used to be chamfered underneath to print standing up).
    chord_v = SD / math.cos(ALPHA)
    band = prism_xz([(-W / 2, ZWT - chord_v), (0, ZPK - chord_v), (W / 2, ZWT - chord_v),
                     (W / 2, ZWT), (0, ZPK), (-W / 2, ZWT)],
                    yi - (0.2 if side < 0 else 0), yo + (0.2 if side > 0 else 0))   # 0.2 into the siding so they join
    parts.append(band)
    gable_shape = prism_xz([(-W / 2, 0), (W / 2, 0), (W / 2, ZWT), (0, ZPK), (-W / 2, ZWT)], -L, L)
    return union(parts) ^ gable_shape


def window_unit(yc):
    """Double-hung 2x3 window inside its opening on the +x wall: two sashes and their muntins,
    no glass, so you can see in (Alan, Oct 31 2026). The sash frames reach 0.2 mm into the
    jambs so they join the wall."""
    y0, y1 = yc - WIN_W / 2, yc + WIN_W / 2
    z0, z1 = ZF + WIN_SILL, ZF + WIN_SILL + WIN_H
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
    """(parts, recess): louvred vent centred under the ridge, 0.92 ft below it, 1.12 x 0.76 ft.
    Its frame is flush with the siding and its louvres stand in a recess in the siding, so
    nothing of it stands out past the siding and the end wall only changes colour once, for the
    gable band (Alan, Nov 3 2026)."""
    vw, vh = 1.12 * FT, 0.76 * FT
    zc = ZPK - 0.92 * FT
    yf = side * L / 2
    def slab(x0, x1, z0, z1, d0, d1):
        """A slab d0 to d1 out from the siding face."""
        ya, yb = sorted([yf + side * d0, yf + side * d1])
        return box(x0, x1, ya, yb, z0, z1)
    fr = 1.0
    x0, x1, z0, z1 = -vw / 2, vw / 2, zc - vh / 2, zc + vh / 2
    recess = slab(x0 + fr, x1 - fr, z0 + fr, z1 - fr, -VENT_DEPTH, 1)
    parts = [slab(x0, x1, z0, z1, -EMBED, 0) - recess]         # the frame, flush; covers the siding grooves
    # five louvre slats: wedges standing on the recess floor, flat underneath, sloping back to
    # the floor at the top. Their front edges come up to the siding face and no further, and they
    # narrow toward it, so in the print (outside up) nothing overhangs. The bottom one sits on the
    # frame, and each leaves 0.3 under the next at the back, so on every layer the gaps between
    # them are wider than a line (0.46 on the first) and print open (review, Nov 3 2026).
    inner_h = vh - 2 * fr
    for i in range(5):
        zb = z0 + fr + inner_h * i / 5
        zt = zb + inner_h / 5 - 0.3
        yb = yf - side * (VENT_DEPTH + 0.1)                     # 0.1 into the floor, so they join it
        poly = [(yb, zb), (yf, zb), (yf, zb + VENT_SLAT), (yb, zt)]
        parts.append(prism(poly, 1, 2, 0, x1 - x0 - 2 * fr + 0.2).translate([x0 + fr - 0.1, 0, 0]))
    return parts, recess


def trims():
    """Gable bands, door and window casings (raised so they can be painted). The corner boards
    are the separate corner angles now (Alan, Nov 3 2026)."""
    p = []
    # gable band: it stops at the recess for the corner angle, so it butts into the angle's edge
    # with POCKET_CLR between, like a frieze board between corner boards. The recess itself cuts
    # it off, the same cut as the wall's, so the band's end and the recess's always match (worked
    # out apart they came out 1e-14 apart at some gaps and left a white scrap)
    for sy in (1, -1):
        ya, yb = sorted([sy * (L / 2 - EMBED), sy * (L / 2 + PROUD)])
        p.append(box(-W / 2, W / 2, ya, yb, ZWT - TRIM, ZWT) - union([corner_recess(sx, sy) for sx in (1, -1)]))
    xo, xi = W / 2, W / 2 - EMBED
    # door casing: two sides and one head board
    ztop = ZF + DOOR_OPEN_H
    p.append(box(xi, xo + PROUD, -JAMB - TRIM, -JAMB, ZF, ztop + TRIM))
    p.append(box(xi, xo + PROUD, JAMB, JAMB + TRIM, ZF, ztop + TRIM))
    p.append(box(xi, xo + PROUD, -JAMB - TRIM, JAMB + TRIM, ztop, ztop + TRIM))
    # window casings: the same 1x4 board on all four sides (no sill nose; Alan, Oct 31 2026)
    for yc in (-WIN_YC, WIN_YC):
        y0, y1 = yc - WIN_W / 2, yc + WIN_W / 2
        z0, z1 = ZF + WIN_SILL, ZF + WIN_SILL + WIN_H
        p.append(box(xi, xo + PROUD, y0 - TRIM, y0, z0 - TRIM, z1 + TRIM))
        p.append(box(xi, xo + PROUD, y1, y1 + TRIM, z0 - TRIM, z1 + TRIM))
        p.append(box(xi, xo + PROUD, y0 - TRIM, y1 + TRIM, z1, z1 + TRIM))
        p.append(box(xi, xo + PROUD, y0 - TRIM, y1 + TRIM, z0 - TRIM, z0))
    return p


def roof_clearance():
    """Everything outside the wall planes that the roof halves sit over, plus 0.15 mm."""
    out = []
    for sx in (1, -1):
        x_in, x_out = W / 2, W / 2 + 10
        poly = [(x_in, ZWT - 0.15), (x_out, ZWT - 0.15 - (x_out - x_in) * PITCH), (x_out, 300), (x_in, 300)]
        if sx < 0:
            poly = [(-x, z) for (x, z) in reversed(poly)]
        out.append(prism_xz(poly, -L, L))
    # the long walls stop 0.15 under the roof so it bears on the gable ends only
    for sx in (1, -1):
        xa, xb = sorted([sx * (W / 2 - WT - 0.01), sx * (W / 2 + 1)])
        out.append(box(xa, xb, -(L / 2 - WT), L / 2 - WT, ZWT - 0.15, 300))
    return out


def floor():
    """Floor frame and floor sheets. The walls stand on it with their siding hanging down over
    its edge, FLOOR_CLR clear of it. It prints upside down, floor face on the bed."""
    xf, yf = W / 2 - TS - FLOOR_CLR, L / 2 - TS - FLOOR_CLR
    cuts = []
    edges = [-(yf - RIM)] + [e for j in joist_ys() for e in (j - SW / 2, j + SW / 2)] + [yf - RIM]
    for a, b in zip(edges[0::2], edges[1::2]):
        cuts.append(box(-xf + RIM, xf - RIM, a, b, -1, ZF - DECK))
    # floor sheet seams (4x8 sheets, staggered), inside the walls
    xi, yi = W / 2 - WT, L / 2 - WT
    for x0, x1, ys in ((-xi, 0, [-24 * S, 24 * S]), (0, xi, [-48 * S, 0, 48 * S])):
        for y in ys:
            cuts.append(box(x0, x1, y - 0.2, y + 0.2, ZF - 0.25, ZF + 0.01))
    cuts.append(box(-0.2, 0.2, -yi, yi, ZF - 0.25, ZF + 0.01))
    return box(-xf, xf, -yf, yf, 0, ZF) - union(cuts + floor_cuts())


FLOOR_TO_PRINT = [[1, 0, 0], [0, -1, 0], [0, 0, -1]]     # upside down


def walls():
    """All four walls in one, assembled; split_walls() cuts them apart for printing."""
    gable = [(-W / 2, 0), (W / 2, 0), (W / 2, ZWT), (0, ZPK), (-W / 2, ZWT)]
    shell = prism_xz(gable, -L / 2, L / 2)
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
    vents = [gable_vent(1), gable_vent(-1)]
    b = b - union(op_cuts + [recess for _, recess in vents])
    b = union([b] + window_unit(-WIN_YC) + window_unit(WIN_YC) + [q for parts, _ in vents for q in parts])

    # door stop inside the latch jamb, so the door only swings out. It runs back to the inside
    # face of the framing so the wall prints flat.
    door_inner = AXIS_X - DOOR_R
    b = b + box(W / 2 - WT, door_inner - 0.2, JAMB - 0.8, JAMB + 0.2, ZF, ZF + DOOR_OPEN_H)
    # hinge pin holes and the slot the bottom pin slides in through
    holes = [cyl_z(AXIS_X, AXIS_Y, ZF - HOLE_BOTTOM_DEPTH, ZF + 1, PIN_HOLE_D),
             cyl_z(AXIS_X, AXIS_Y, ZF + DOOR_OPEN_H - 1, ZF + DOOR_OPEN_H + HOLE_TOP_DEPTH, PIN_HOLE_D),
             box(AXIS_X, W / 2 + 2, AXIS_Y - PIN_HOLE_D / 2, AXIS_Y + PIN_HOLE_D / 2, ZF - TRENCH_DEPTH, ZF + 1)]
    b = b - union(holes)
    b = b - union(roof_clearance())

    # roof pegs on the gable top chords
    pegs = []
    for sx in (1, -1):
        for sy in (1, -1):
            x = sx * PEG_X
            peg = cyl_z(x, sy * PEG_Y, zline(x) - 3, zline(x) + 3, PEG_D)
            nrm, off = under_roof(sx, PEG_UP)
            pegs.append(peg.trim_by_plane(nrm, off))
    b = b + union(pegs)
    # nothing above the wall plates over the long walls' mitred ends, so a long wall can be
    # lowered into place between the gable ends (it takes a sliver off each eave corner)
    for sx in (1, -1):
        b = b - mitred(0, sx).trim_by_plane([0, 0, 1], ZWT)
    # the recess for each corner angle, and the chamfer off the corner under it
    return b - union([corner_recess(sx, sy) for sx, sy in CORNERS])


def body():
    """The assembled body: four walls and the floor."""
    return union(list(split_walls(walls()).values()) + [floor()])


# the four walls meet at 45 degree mitres through the inside and outside corners, so each
# wall carries only the trim on its own face and it all prints on top: the colour changes
# are the last few layers (Alan, Nov 1 2026). Each prints lying flat on the inside face of
# its framing, outside up; the mitred ends lean out at 45 degrees, which prints fine.
BIG = 500


def mitred(axis, sign):
    """The region one wall owns: outside its inside face, and on its side of the mitre at
    each end. axis 0 for a long wall, 1 for an end wall; sign which side of the shed."""
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
    """Above the top of the wall plates on one end of the shed. The bit of gable at each
    corner above the plates goes with the end wall, where it lies on the bed; on the long
    wall it was a sliver the slicer called floating."""
    return M.cube([2 * BIG] * 3, True).trim_by_plane([0, 0, 1], ZWT).trim_by_plane([0, sign, 0], 0)


WALL_CUTS = {
    "door wall": mitred(0, 1) - above_plate(1) - above_plate(-1),
    "back wall": mitred(0, -1) - above_plate(1) - above_plate(-1),
    "end wall 1": mitred(1, 1) + above_plate(1),
    "end wall 2": mitred(1, -1) + above_plate(-1),
}
# shed coords to print coords, inside face down (each a rotation, det +1)
WALL_TO_PRINT = {
    "door wall": [[0, 1, 0], [0, 0, 1], [1, 0, 0]],
    "back wall": [[0, -1, 0], [0, 0, 1], [-1, 0, 0]],
    "end wall 1": [[-1, 0, 0], [0, 0, 1], [0, 1, 0]],
    "end wall 2": [[1, 0, 0], [0, 0, 1], [0, -1, 0]],
}


def split_walls(w):
    """The four walls cut apart at the mitres. Where a cut lies on a face of the body (the long
    walls' corners stop at the plate top, where the end walls' share starts) it can leave a flat
    scrap with no volume; those are dropped."""
    return {name: union([c for c in (w ^ cut).decompose() if c.volume() > 1e-6]) for name, cut in WALL_CUTS.items()}


# ---------------------------------------------------------------- corner angles
CORNERS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]   # (sx, sy): the door wall is +x, end wall 1 is +y


def corner_walls(sx, sy):
    """(long wall, end wall) that meet at a corner."""
    return ("door wall" if sx > 0 else "back wall"), ("end wall 1" if sy > 0 else "end wall 2")


def corner_frame(sx, sy):
    """Matrix from a corner's own coords to shed coords: u out from the long wall's siding face,
    v out from the end wall's, z up, so u = v = 0 is the outer corner of the siding. For the
    (+,-) and (-,+) corners it is a mirror image."""
    return np.array([[sx, 0, 0, sx * W / 2], [0, sy, 0, sy * L / 2], [0, 0, 1, 0]], dtype=float)


def angle_reach():
    """How far the corner angle reaches from the outer corner of the siding along (the long
    wall, the end wall): TRIM on the long wall, and on the end wall what the standing leg's
    ANGLE_UP leaves past the long-face leg."""
    return TRIM, ANGLE_UP - (ANGLE_T - POCKET_D)


def corner_recess(sx, sy):
    """What comes out of both walls at one corner for its angle: a recess POCKET_D deep in each
    wall's outside face, reaching POCKET_CLR past the angle's edge, and the chamfer off the outer
    corner, square to the mitre. Both run from the bottom of the skirt up through the top of the
    wall: the angle's top is 0.2 under the roof, so a recess stopping 0.15 over it would leave a
    strip of wall 0.05 thick under the roof, too thin to print."""
    ra, rb = angle_reach()
    big = 20
    h = 1 / math.sqrt(2)
    cut = union([box(-POCKET_D, big, -(ra + POCKET_CLR), big, -1, 400),
                 box(-(rb + POCKET_CLR), big, -POCKET_D, big, -1, 400),
                 box(-big, big, -big, big, -1, 400).trim_by_plane([h, h, 0], -(2 * POCKET_D + CORNER_CHAMFER) * h)])
    return cut.transform(corner_frame(sx, sy))


def corner_angle(sx, sy):
    """The black L angle at one corner, in shed coords: two legs ANGLE_T thick with their inside
    faces on the recess floors, a 45 degree fillet in the inside corner, the foot level with the
    bottom of the skirts, and the top ANGLE_ROOF under the roof, square to it, right across both
    legs (the roof overhangs the gable ends by RAKE, so the end-face leg is under it too). Each
    leg's face covers its wall to angle_reach() and the other leg's thickness."""
    out = ANGLE_T - POCKET_D
    ra, rb = angle_reach()
    p, f = POCKET_D, POCKET_D + ANGLE_FILLET
    sec = [(out, out), (out, -ra), (-p, -ra), (-p, -f), (-f, -p), (-rb, -p), (-rb, out)]
    a = prism(sec, 0, 1, 2, ZPK).transform(corner_frame(sx, sy))
    return a.trim_by_plane(*under_roof(sx, -ANGLE_ROOF))


def angle_to_print(sx):
    """Shed coords to print coords for an angle on the sx side: lying on the long-face leg's
    outside face (on the textured plate), its length along y, the end-face leg standing up. A
    rotation, det +1; the (+,-) and (-,+) angles come out as the mirror image of the others."""
    return [[0, -sx, 0], [0, 0, 1], [-sx, 0, 0]]


def angle_prints():
    """The four corner angles lying the way they print, in CORNERS order, each on the bed at the
    origin. (+,+) and (-,-) print the same; (+,-) and (-,+) are their mirror image."""
    return [to_print(angle_to_print(sx), [corner_angle(sx, sy)])[0] for sx, sy in CORNERS]


def angle_stub():
    """The bottom 20 mm of the (+,+) corner's angle, for the fit test."""
    return corner_angle(1, 1) ^ box(-BIG, BIG, -BIG, BIG, -1, 20)


def trim_zone():
    """Everything standing proud of the siding that is trim (gable bands, door and window
    casings). It prints in the second colour. The back wall has none."""
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
def roof_frame():
    """Matrix taking local roof coords (X=y, Y=n up from the underside, Z=s down the slope
    from the ridge) to the +x half in shed coords."""
    d = np.array([math.cos(ALPHA), 0, -math.sin(ALPHA)])
    nrm = np.array([math.sin(ALPHA), 0, math.cos(ALPHA)])
    p0 = np.array([0, 0, ZPK])
    return np.column_stack([[0, 1, 0], nrm, d, p0])


def roof_half():
    """The +x roof half in shed coords (the -x half is its mirror image)."""
    xe = W / 2 + EAVE
    tv = ROOF_T / math.cos(ALPHA)
    ly = L / 2 + RAKE
    def under(x):                                # underside of the +x half, any x
        return ZPK - x * PITCH
    slab = prism_xz([(-1, under(-1)), (xe, under(xe)), (xe, under(xe) + tv), (-1, under(-1) + tv)], -ly, ly)
    mat = roof_frame()
    extras = []
    rib = m3.CrossSection([[(-0.7, ROOF_T - 0.05), (0.7, ROOF_T - 0.05), (0.3, ROOF_T + 0.6), (-0.3, ROOF_T + 0.6)]])
    ribs = []
    ys = [k * RIB_OC for k in range(-20, 21) if abs(k * RIB_OC) <= ly - 2]
    for y in ys:
        ribs.append(M.extrude(rib.translate([y, 0]), 70).translate([0, 0, -5]))
    extras.append(union(ribs).transform(mat))
    cap = M.cube([2 * ly, 1.2 + 0.6, 5.5 + 5]).translate([-ly, ROOF_T - 0.1, -5])     # ridge cap
    extras.append(cap.transform(mat))
    r = union([slab] + extras)
    r = r.trim_by_plane([1, 0, 0], 0.1)                                     # ridge gap 0.1 per half
    r = r.trim_by_plane([-1, 0, 0], -xe)                                    # eave (fascia) cut
    r = r.trim_by_plane([0, 1, 0], -ly).trim_by_plane([0, -1, 0], -ly)
    holes = []
    for sy in (1, -1):
        h = cyl_z(PEG_X, sy * PEG_Y, zline(PEG_X) - 5, zline(PEG_X) + 5, PEG_HOLE_D)
        nrm, off = under_roof(1, PEG_HOLE_UP)
        holes.append(h.trim_by_plane(nrm, off))
    return r - union(holes)


def roof_to_print(r):
    """Lay a +x roof half on the bed, underside down."""
    mat = roof_frame()
    R = mat[:, :3]
    p0 = mat[:, 3]
    # local = R^T (p - p0) gives (y, n, s); print as (X=-y? no) X=s, Y=y, Z=n
    Rt = R.T
    to_local = np.column_stack([Rt, -Rt @ p0])                            # (y, n, s)
    swap = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], dtype=float)        # (s, y, n), det +1
    full = np.column_stack([swap @ to_local[:, :3], swap @ to_local[:, 3]])
    p = r.transform(full)
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
    up0, up1 = ym + tw / 2, DOOR_H - tw
    black += [tri(xl, lo0, xl + leg, lo0, xl, lo0 + leg), tri(xr, lo0, xr, lo0 + leg, xr - leg, lo0),
              tri(xl, lo1, xl, lo1 - leg, xl + leg, lo1), tri(xr, lo1, xr - leg, lo1, xr, lo1 - leg),
              tri(xl, up1, xl, up1 - leg, xl + leg, up1), tri(xr, up1, xr - leg, up1, xr, up1 - leg)]
    # pull handle, 0.44 ft in from the latch edge: a D-shaped pull standing 2.6 mm off the panel,
    # with a 1.8 mm gap under the grip to hook a fingernail in (Alan, Nov 1 2026). The grip
    # bridges 4.6 mm between its two posts.
    hx, hy = DOOR_W - 0.44 * FT, 0.45 * DOOR_H
    hw, hl, post, grip = 1.4, 3.5, 1.2, 0.8
    top = z1 + 2.0
    black += [box(hx - hw / 2, hx + hw / 2, hy - hl, hy - hl + post, z0, top),
              box(hx - hw / 2, hx + hw / 2, hy + hl - post, hy + hl, z0, top),
              box(hx - hw / 2, hx + hw / 2, hy - hl, hy + hl, top - grip, top)]
    black = union(black) - white
    return white, black


def door_to_shed(theta_deg=0.0):
    """Matrix from door print coords to shed coords, swung open theta degrees."""
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
def corner_test(pieces, f):
    """The corner where the door wall meets end wall 1, made short: the bottom 8 mm of each
    wall above the floor joined to its top 10 mm, on that corner of the floor. It has a real
    prong, posts, skirt, and the recesses and chamfer for the corner angle. Each wall is cut
    along the far side of a stud, so the siding at the cut is held. Returns (long wall, end
    wall, floor) in shed coords."""
    z_lo, z_hi = ZF + 8, ZWT - 10
    y0 = layout(-L / 2, L / 2, 16 * S)[-2] - SW / 2
    x0 = layout(-W / 2, W / 2, 16 * S)[-1] - SW / 2
    def short(piece, x0, y0):
        keep = box(x0, W / 2 + 2, y0, L / 2 + 2, -5, 400)
        lo = piece ^ keep ^ box(-BIG, BIG, -BIG, BIG, -5, z_lo)
        hi = piece ^ keep ^ box(-BIG, BIG, -BIG, BIG, z_hi, 400)
        return lo + hi.translate([0, 0, z_lo - z_hi])
    return (short(pieces["door wall"], W / 2 - 10, y0),
            short(pieces["end wall 1"], x0, L / 2 - 10),
            f ^ box(x0, W / 2, y0, L / 2, -5, 400))


def fit_test():
    """A short doorway with the same pin holes, slot and stop, a short door with the same
    pins, and a block with a roof peg next to a roof coupon with the peg hole. The doorway and
    the peg block print lying flat, inside face down, the way the door wall and the end walls
    do, so the holes and the peg come out the way the real ones will."""
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
    # roof peg on a block lying like an end wall, so the peg sticks out sideways at mid
    # thickness; stand it up to try the coupon on it
    bx = fw + 6 + d.bounding_box()[3] - d.bounding_box()[0] + 12
    blk = box(-6, 6, 0, 6, 0, WT) + cyl_y(0, 5, 6 + PEG_UP, WT / 2, PEG_D)
    blk = blk.translate([bx, 3, 0])
    cpn = box(-6, 6, -6, 6, 0, ROOF_T) - cyl_z(0, 0, -1, PEG_HOLE_UP, PEG_HOLE_D)
    cpn = cpn.translate([bx, 22, 0])
    return union([f, d, blk, cpn])


def corner_fit_test(pieces, whole_floor):
    """The short corner from corner_test() in a row, each piece lying the way the real walls and
    floor print, and the bottom 20 mm of that corner's angle lying the way the angles print."""
    lw, ew, fl = corner_test(pieces, whole_floor)
    row, x = [], 0
    for part, mat in ((lw, WALL_TO_PRINT["door wall"]), (ew, WALL_TO_PRINT["end wall 1"]), (fl, FLOOR_TO_PRINT),
                      (angle_stub(), angle_to_print(1))):
        pp = to_print(mat, [part])[0]
        row.append(pp.translate([x, 0, 0]))
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
        f.write(b"8x12 Side Utility 1:24".ljust(80, b" "))
        f.write(struct.pack("<I", len(t)))
        rec = np.zeros(len(t), dtype=[("n", "<f4", 3), ("a", "<f4", 3), ("b", "<f4", 3), ("c", "<f4", 3), ("x", "<u2")])
        rec["n"], rec["a"], rec["b"], rec["c"] = n, a, b, c
        f.write(rec.tobytes())
    return path


def write_3mf(name, plates):
    """A plain 3MF project for Orca. plates: [(plate name, items), ...], each a plate in Orca in
    that order. items: (object name, [(part name, manifold, filament), ...], (x, y)) placed with
    its lower-left corner at x, y on its plate, and optionally a dict of that object's own
    settings after (x, y). An object with two parts opens in Orca as one object, each part
    already set to its filament (1 siding, 2 trim, roof and angles, 3 floor and skids)."""
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
        for obj_name, parts, (x, y), *own in items:
            bb = union([m for _, m, _ in parts]).bounding_box()
            # store each object's shape centred on its own middle and place that middle on the
            # plate, the way Flash Studio saves its own projects
            mid = np.array([(bb[0] + bb[3]) / 2, (bb[1] + bb[4]) / 2, (bb[2] + bb[5]) / 2])
            comp_ids = []
            cfg.append(f'<object id="{oid + len(parts)}"><metadata key="name" value={quoteattr(obj_name)}/>'
                       f'<metadata key="extruder" value="{parts[0][2]}"/>'
                       + "".join(f'<metadata key="{k}" value={quoteattr(v)}/>' for k, v in (own[0] if own else {}).items()))
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
             '<metadata name="Title">8x12 Side Utility 1:24</metadata>'
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
    pieces = split_walls(walls())
    parts["body"] = union(list(pieces.values()) + [f])
    parts["floor"] = f
    parts.update(pieces)
    parts["angles"] = union([corner_angle(sx, sy) for sx, sy in CORNERS])
    roof = roof_half()
    parts["roof"] = roof
    white, black = door_parts()
    parts["door"], parts["door_trim"] = white, black
    parts["skids"] = skids()
    parts["fit"] = fit_test()
    parts["fit corner"] = corner_fit_test(pieces, f)
    return parts


def wall_parts(p, name, zone):
    """(siding, trim) of a wall, lying flat on the bed."""
    return to_print(WALL_TO_PRINT[name], two_colour(p[name], zone))


def fit_plates(p):
    """The plates of 1 fit test.3mf for write_3mf(): first only what is new, the short corner
    and the angle stub (Alan, Nov 3 2026), then the doorway, door and roof peg as before. All
    one filament, each plate's pieces in the middle of the bed."""
    plates = []
    for name, man in (("new corner", p["fit corner"]), ("door and roof peg", p["fit"])):
        m = on_bed(man)
        bb = m.bounding_box()
        plates.append((name, [(name, [(name, m, 1)], (110 - bb[3] / 2, 110 - bb[4] / 2))]))
    return plates


def all_plates(p, walls_p):
    """The plates of 2 all plates.3mf for write_3mf(), one for each print, in Alan's order (Nov 1
    2026): both long walls, the roof and the four corner angles, the door, both end walls, the
    floor and skids. Filament 1 is the siding colour (white), filament 2 the trim, roof and
    angles (black), filament 3 the floor and skids (brown, Alan Nov 2 2026). The prime tower goes
    at x 165, y 195 on every plate, so the two-colour plates keep that corner clear."""
    def wall_item(name, x, y):
        siding, trim = walls_p[name]
        parts = [("siding", siding, 1)] + ([("trim", trim, 2)] if trim.volume() > 0 else [])   # the back wall has none
        return (name, parts, (x, y))

    roof_p = roof_to_print(p["roof"])
    skid_p = skid().transform(np.array([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0]], dtype=float))
    fl = to_print(FLOOR_TO_PRINT, [p["floor"]])[0]
    lh = union(walls_p["door wall"]).bounding_box()[4]
    y0 = (220 - 2 * lh - 3) / 2
    ew = union(walls_p["end wall 1"]).bounding_box()
    db = union([p["door"], p["door_trim"]]).bounding_box()
    # the roof halves 6 mm apart and the four angles beside them, 4 mm apart. The angles' outside
    # face is on the plate, so they get no brim: it would leave a lip along a board's edge
    rw = roof_p.bounding_box()[3]
    angles = angle_prints()
    ab = angles[0].bounding_box()
    rx = (220 - (2 * rw + 12 + 4 * ab[3] + 3 * 4)) / 2
    ry = (220 - (L + 2 * RAKE)) / 2
    ax = rx + 2 * rw + 12
    fb = fl.bounding_box()
    fx = (220 - (fb[3] + 2 * SKID_W + 12)) / 2
    return [
        ("long walls", [wall_item("door wall", 3, y0), wall_item("back wall", 3, y0 + lh + 3)]),
        ("roof and corner angles", [("roof half 1", [("roof half", roof_p, 2)], (rx, ry)),       # black, filament 2
                                    ("roof half 2", [("roof half", roof_p, 2)], (rx + rw + 6, ry))]
         + [("corner angle, %s at %s" % corner_walls(sx, sy), [("corner angle", a, 2)],
            (ax + i * (ab[3] + 4), (220 - ab[4]) / 2), {"brim_type": "no_brim"})
           for i, ((sx, sy), a) in enumerate(zip(CORNERS, angles))]),
        ("door", [("door", [("door", p["door"], 1), ("door trim", p["door_trim"], 2)],
                   ((220 - db[3]) / 2, (190 - db[4]) / 2))]),
        ("end walls", [wall_item("end wall 1", (220 - 2 * ew[3] - 6) / 2, 4),
                       wall_item("end wall 2", (220 + 6) / 2, 4)]),
        ("floor and skids", [("floor", [("floor", fl, 3)], (fx, (220 - fb[4]) / 2)),               # brown
                             ("skid 1", [("skid", skid_p, 3)], (fx + fb[3] + 6, (220 - L) / 2)),
                             ("skid 2", [("skid", skid_p, 3)], (fx + fb[3] + SKID_W + 12, (220 - L) / 2))]),
    ]


def main():
    p = build()
    zone = trim_zone()
    walls_p = {name: wall_parts(p, name, zone) for name in WALL_CUTS}
    fl = to_print(FLOOR_TO_PRINT, [p["floor"]])[0]
    write_stl(fl, "floor.stl")
    write_stl(union(walls_p["door wall"]), "door wall.stl")
    write_stl(union(walls_p["back wall"]), "back wall.stl")
    write_stl(union(walls_p["end wall 1"]), "end wall.stl")
    write_stl(roof_to_print(p["roof"]), "roof half.stl")
    angles = angle_prints()
    write_stl(union([a.translate([i * (a.bounding_box()[3] + 4), 0, 0]) for i, a in enumerate(angles)]),
              "corner angle.stl")
    door = p["door"] + p["door_trim"]
    write_stl(door, "door.stl")
    write_stl(p["skids"], "skids.stl")
    fit, corner = on_bed(p["fit"]), on_bed(p["fit corner"])
    write_stl(union([fit, corner.translate([0, fit.bounding_box()[4] + 6, 0])]), "fit test.stl")

    write_3mf("1 fit test.3mf", fit_plates(p))
    write_3mf("2 all plates.3mf", all_plates(p, walls_p))
    for name, (siding, trim) in walls_p.items():
        bb = union([siding, trim]).bounding_box()
        print(f"{name:10s} flat {bb[3]-bb[0]:7.1f} x {bb[4]-bb[1]:7.1f} x {bb[5]-bb[2]:6.1f} mm  "
              + (f"trim {trim.volume()/1000:5.2f} cm3, from {trim.bounding_box()[2]:.2f} mm up" if trim.volume() > 0
                 else "no trim"))
    for k, v in p.items():
        bb = v.bounding_box()
        print(f"{k:10s} {bb[3]-bb[0]:7.1f} x {bb[4]-bb[1]:7.1f} x {bb[5]-bb[2]:6.1f} mm  "
              f"{v.volume()/1000:6.1f} cm3  {v.num_tri()} triangles")


if __name__ == "__main__":
    main()
