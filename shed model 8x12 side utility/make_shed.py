"""8x12 Side Utility shed, 1:24 scale, for the Flashforge AD5X.

Run:  python3 make_shed.py      (needs: pip install manifold3d numpy)

Makes the print files in this folder:
  body.stl        floor frame, floor, walls with framing inside, windows, trim
  roof half.stl   print TWO. Each half lifts straight off its two pegs.
  door.stl        48 in wooden door (white part) with its hinge pins
  door trim.stl   the door's black trim and handle (same position as door.stl)
  skids.stl       the two 4x6 skids the floor frame sits on
  fit test.stl    a small doorway, door and roof peg to check the fit first

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
RIM = 2.0              # floor rim board inside the siding skirt
JOIST_H = 5.5 * S      # 2x6 joists
DECK = 1.0             # floor sheets
ZF = JOIST_H + DECK    # top of the floor
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
PIN_HOLE_D = 2.45
PIN_BOTTOM_LEN = 1.3   # rests on the bottom of a 1.0 deep hole
PIN_TOP_LEN = 2.0
HOLE_BOTTOM_DEPTH = 1.0
TRENCH_DEPTH = 0.7     # the slot the bottom pin slides in through; 0.3 shallower than the hole
HOLE_TOP_DEPTH = 2.2
DOOR_SLAB = 1.4        # panel thickness; trim brings it to 2.0

# windows: 2x3 window, 2.1 x 2.9 ft, sill 2.9 ft above the floor, each centred between the door
# opening and the end of the wall (Alan, Oct 31 2026); the casings and corner boards are the
# same width, so it is also centred between the door casing and the corner board
WIN_W = 2.1 * FT
WIN_H = 2.9 * FT
WIN_SILL = 2.9 * FT
WIN_YC = (JAMB + L / 2) / 2

# roof
ROOF_T = 2.0
RIB_OC = 9 * S
PEG_D, PEG_UP = 2.2, 1.0
PEG_HOLE_D, PEG_HOLE_UP = 2.7, 1.4
PEG_X = W / 4
PEG_Y = L / 2 - WT / 2

# skids: 4x6 laid on edge, inside face 30 in in from the outside of the wall
SKID_W = 3.5 * S
SKID_H = 5.5 * S
SKID_X = W / 2 - 28.25 * S
NOTCH = 0.6
NOTCH_CLEAR = 0.3


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
    end = L / 2 - TS - SW / 2
    inner = layout(-L / 2, L / 2, 16 * S)
    return [-end] + inner + [end]


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
    for xc in [-xin + SW / 2, xin - SW / 2] + layout(-W / 2, W / 2, 16 * S):
        parts.append(box(xc - SW / 2, xc + SW / 2, yi, yo, ZF + PLATE_BOT, ZPK))
    # top chords: a band one 2x4 deep under the roof line, chamfered 45 deg underneath so it
    # prints without supports. Depth into the room grows with height above the chord's underside:
    # keep  depth <= z - (roof line - chord)
    chord_v = SD / math.cos(ALPHA)
    band = prism_xz([(-W / 2, ZWT - chord_v), (0, ZPK - chord_v), (W / 2, ZWT - chord_v),
                     (W / 2, ZWT), (0, ZPK), (-W / 2, ZWT)],
                    yi - (0.2 if side < 0 else 0), yo + (0.2 if side > 0 else 0))   # 0.2 into the siding so they join
    face = yo if side > 0 else yi                # inside face of the gable siding
    for hx in (+1, -1):
        half = band.trim_by_plane([hx, 0, 0], 0)
        normal = np.array([hx * PITCH, side, 1.0])
        offset = ZWT + PITCH * W / 2 - chord_v + side * face
        ln = np.linalg.norm(normal)
        parts.append(half.trim_by_plane((normal / ln).tolist(), offset / ln))
    gable_shape = prism_xz([(-W / 2, 0), (W / 2, 0), (W / 2, ZWT), (0, ZPK), (-W / 2, ZWT)], -L, L)
    return union(parts) ^ gable_shape


def window_unit(yc):
    """Double-hung 2x3 window inside its opening on the +x wall: glass, two sashes, muntins."""
    y0, y1 = yc - WIN_W / 2, yc + WIN_W / 2
    z0, z1 = ZF + WIN_SILL, ZF + WIN_SILL + WIN_H
    zm = (z0 + z1) / 2
    xg0, xg1 = W / 2 - TS, W / 2 - 0.8
    parts = [box(xg0, xg1, y0 - 0.2, y1 + 0.2, z0 - 0.2, z1 + 0.2)]       # glass, keyed into the jambs
    ring = 1.2
    for (za, zb, xf) in ((zm, z1, W / 2 - 0.45), (z0, zm, W / 2 - 0.15)):    # upper sash sits back
        parts += [box(xg1, xf, y0, y1, za, za + ring), box(xg1, xf, y0, y1, zb - ring, zb),
                  box(xg1, xf, y0, y0 + ring, za, zb), box(xg1, xf, y1 - ring, y1, za, zb),
                  box(xg1, xf - 0.15, yc - 0.3, yc + 0.3, za, zb),                       # muntins
                  box(xg1, xf - 0.15, y0, y1, (za + zb) / 2 - 0.3, (za + zb) / 2 + 0.3)]
    return parts


def gable_vent(side):
    """Louvred vent centred under the ridge, 0.92 ft below it, 1.12 x 0.76 ft."""
    vw, vh = 1.12 * FT, 0.76 * FT
    zc = ZPK - 0.92 * FT
    yf = side * L / 2
    def slab(x0, x1, z0, z1, d):
        ya, yb = sorted([yf - side * EMBED, yf + side * d])
        return box(x0, x1, ya, yb, z0, z1)
    fr = 1.0
    x0, x1, z0, z1 = -vw / 2, vw / 2, zc - vh / 2, zc + vh / 2
    parts = [slab(x0, x1, z0, z1, 0.0)]                       # flat back, covers the siding grooves
    parts += [slab(x0, x1, z0, z0 + fr, 0.5), slab(x0, x1, z1 - fr, z1, 0.5),
              slab(x0, x0 + fr, z0, z1, 0.5), slab(x1 - fr, x1, z0, z1, 0.5)]
    # five louvre slats: wedges, flat underneath, sloping back to the siding at the top
    inner_h = vh - 2 * fr
    for i in range(5):
        zb = z0 + fr + inner_h * i / 5 + 0.25
        zt = zb + inner_h / 5 - 0.1
        poly = [(yf - side * EMBED, zb), (yf + side * 0.7, zb), (yf + side * 0.7, zb + 0.2), (yf - side * EMBED, zt)]
        parts.append(prism(poly, 1, 2, 0, x1 - x0 - 2 * fr).translate([x0 + fr, 0, 0]))
    return parts


def trims():
    """Corner boards, gable bands, door and window casings (raised so they can be painted)."""
    p = []
    for sx in (1, -1):
        for sy in (1, -1):
            xa, xb = sorted([sx * (W / 2 - EMBED), sx * (W / 2 + PROUD)])
            ya, yb = sorted([sy * (L / 2 - TRIM), sy * (L / 2 + PROUD)])
            p.append(box(xa, xb, ya, yb, 0, ZWT))                        # on the long wall face
            xa2, xb2 = sorted([sx * (W / 2 - TRIM), sx * (W / 2 + PROUD)])
            ya2, yb2 = sorted([sy * (L / 2 - EMBED), sy * (L / 2 + PROUD)])
            p.append(box(xa2, xb2, ya2, yb2, 0, ZWT))                    # on the end face
    for sy in (1, -1):
        ya, yb = sorted([sy * (L / 2 - EMBED), sy * (L / 2 + PROUD)])
        p.append(box(-W / 2 - PROUD, W / 2 + PROUD, ya, yb, ZWT - TRIM, ZWT))   # gable band
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


def body():
    gable = [(-W / 2, 0), (W / 2, 0), (W / 2, ZWT), (0, ZPK), (-W / 2, ZWT)]
    shell = prism_xz(gable, -L / 2, L / 2)
    cuts = [box(-W / 2 + TS, W / 2 - TS, -L / 2 + TS, L / 2 - TS, ZF, 400)]
    js = joist_ys()
    for a, b in zip(js[:-1], js[1:]):
        cuts.append(box(-W / 2 + TS + RIM, W / 2 - TS - RIM, a + SW / 2, b - SW / 2, -1, ZF - DECK))
    # siding grooves
    for y in layout(-L / 2, L / 2, GROOVE_OC):
        for sx in (1, -1):
            xa, xb = sorted([sx * (W / 2 - GROOVE_D), sx * (W / 2 + 1)])
            cuts.append(box(xa, xb, y - GROOVE_W / 2, y + GROOVE_W / 2, -1, ZWT + 1))
    for x in layout(-W / 2, W / 2, GROOVE_OC):
        for sy in (1, -1):
            ya, yb = sorted([sy * (L / 2 - GROOVE_D), sy * (L / 2 + 1)])
            cuts.append(box(x - GROOVE_W / 2, x + GROOVE_W / 2, ya, yb, -1, ZPK + 1))
    # floor sheet seams (4x8 sheets, staggered)
    for x0, x1, ys in ((-W / 2 + TS, 0, [-24 * S, 24 * S]), (0, W / 2 - TS, [-48 * S, 0, 48 * S])):
        for y in ys:
            cuts.append(box(x0, x1, y - 0.2, y + 0.2, ZF - 0.25, ZF + 0.01))
    cuts.append(box(-0.2, 0.2, -L / 2 + TS, L / 2 - TS, ZF - 0.25, ZF + 0.01))
    shell = shell - union(cuts)

    framing = long_wall_framing(+1, True) + long_wall_framing(-1, False)
    framing += [end_wall_framing(+1), end_wall_framing(-1)]
    for sx in (1, -1):              # 3-stud corner posts
        for sy in (1, -1):
            xa, xb = sorted([sx * (W / 2 - WT), sx * (W / 2 - TS)])
            ya, yb = sorted([sy * (L / 2 - WT), sy * (L / 2 - WT - SW)])
            framing.append(box(xa, xb, ya, yb, ZF, ZWT))
    b = union([shell] + framing + trims())

    door, wins = openings()
    op_cuts = []
    for (y0, y1, z0, z1) in [door] + wins:
        op_cuts.append(box(W / 2 - WT - 0.5, W / 2 + 2, y0, y1, z0, z1))
    b = b - union(op_cuts)
    b = union([b] + window_unit(-WIN_YC) + window_unit(WIN_YC) + gable_vent(1) + gable_vent(-1))

    # door stop inside the latch jamb, so the door only swings out
    door_inner = AXIS_X - DOOR_R
    b = b + box(door_inner - 1.4, door_inner - 0.2, JAMB - 0.8, JAMB + 0.2, ZF, ZF + DOOR_OPEN_H)
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
    return b + union(pegs)


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
    # handle, 0.44 ft in from the latch edge
    hx = DOOR_W - 0.44 * FT
    black.append(box(hx - 0.5, hx + 0.5, 0.45 * DOOR_H - 3.5, 0.45 * DOOR_H + 3.5, z0, z1 + 0.8))
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
    """One skid lying along X, notched where the joists and the end skirts sit on it."""
    s = box(0, L, 0, SKID_W, 0, SKID_H)
    cuts = []
    for jy in joist_ys():
        y = jy + L / 2
        cuts.append(box(y - SW / 2 - NOTCH_CLEAR / 2, y + SW / 2 + NOTCH_CLEAR / 2, -1, SKID_W + 1, SKID_H - NOTCH, SKID_H + 1))
    cuts.append(box(-1, TS + 0.3, -1, SKID_W + 1, SKID_H - NOTCH, SKID_H + 1))
    cuts.append(box(L - TS - 0.3, L + 1, -1, SKID_W + 1, SKID_H - NOTCH, SKID_H + 1))
    return s - union(cuts)


def skids():
    """Both skids side by side for printing."""
    s = skid()
    return s + s.translate([0, SKID_W + 6, 0])


def skids_to_shed():
    """Matrices placing skid() under the floor frame, joists down in the notches."""
    return [np.array([[0, -1, 0, sx * SKID_X + SKID_W / 2], [1, 0, 0, -L / 2], [0, 0, 1, -(SKID_H - NOTCH)]], dtype=float)
            for sx in (-1, 1)]


# ---------------------------------------------------------------- fit test
def fit_test():
    """A short doorway with the same pin holes, slot and stop, a short door with the same
    pins, and a sloped block with a roof peg next to a roof coupon with the peg hole."""
    ow, oh = 14.0, 24.0
    jamb = ow / 2
    ax_x, ax_y = W / 2 - 1.8, -jamb + DOOR_R + DOOR_GAP
    base = box(W / 2 - 8, W / 2, -jamb - 6, jamb + 6, 0, 3.0)
    frame = [base, box(W / 2 - 8, W / 2, -jamb - 6, -jamb, 3.0, 3.0 + oh + 6),
             box(W / 2 - 8, W / 2, jamb, jamb + 6, 3.0, 3.0 + oh + 6),
             box(W / 2 - 8, W / 2, -jamb - 6, jamb + 6, 3.0 + oh, 3.0 + oh + 6)]
    f = union(frame)
    zf = 3.0
    inner = ax_x - DOOR_R
    f = f + box(inner - 1.4, inner - 0.2, jamb - 0.8, jamb + 0.2, zf, zf + oh)
    f = f - union([cyl_z(ax_x, ax_y, zf - HOLE_BOTTOM_DEPTH, zf + 1, PIN_HOLE_D),
                   cyl_z(ax_x, ax_y, zf + oh - 1, zf + oh + HOLE_TOP_DEPTH, PIN_HOLE_D),
                   box(ax_x, W / 2 + 2, ax_y - PIN_HOLE_D / 2, ax_y + PIN_HOLE_D / 2, zf - TRENCH_DEPTH, zf + 1)])
    f = f.translate([-(W / 2 - 8), jamb + 6, 0])
    # small door with the same pin and edge
    dw = (jamb - DOOR_GAP) - ax_y
    dh = oh - DOOR_BOTTOM_GAP - DOOR_TOP_GAP
    d = union([box(0, dw, 0, dh, 0, 2 * DOOR_R),
               cyl_y(0, 0, dh, DOOR_R, 2 * DOOR_R),
               cyl_y(0, dh - 0.5, dh + PIN_TOP_LEN, DOOR_R, PIN_D, 40),
               cyl_y(0, -PIN_BOTTOM_LEN, 0.5, DOOR_R, PIN_D, 40)])
    d = d.translate([16, 3, 0])
    # roof peg on a small block, and a roof coupon with its hole
    blk = box(-6, 6, -6, 6, 0, 4) + cyl_z(0, 0, 3, 4 + PEG_UP, PEG_D)
    blk = blk.translate([42, 8, 0])
    cpn = box(-6, 6, -6, 6, 0, ROOF_T) - cyl_z(0, 0, -1, PEG_HOLE_UP, PEG_HOLE_D)
    cpn = cpn.translate([42, 24, 0])
    return union([f, d, blk, cpn])


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


def write_3mf(name, items):
    """A plain 3MF project for Orca. items: (object name, [(part name, manifold), ...], (x, y))
    placed with its lower-left corner at x, y on the bed. An object with two parts opens in
    Orca as one object, so each part can be given its own filament."""
    import zipfile
    from xml.sax.saxutils import quoteattr

    res, build, oid = [], [], 1
    for obj_name, parts, (x, y) in items:
        bb = union([m for _, m in parts]).bounding_box()
        comp_ids = []
        for part_name, man in parts:
            mesh = man.to_mesh()
            v = np.asarray(mesh.vert_properties)[:, :3]
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
                     f'{x - bb[0]:.4f} {y - bb[1]:.4f} {-bb[2]:.4f}"/>')
        oid += 1
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             '<metadata name="Title">8x12 Side Utility 1:24</metadata>'
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


def on_bed(man):
    bb = man.bounding_box()
    return man.translate([-bb[0], -bb[1], -bb[2]])


def build():
    parts = {}
    parts["body"] = body()
    roof = roof_half()
    parts["roof"] = roof
    white, black = door_parts()
    parts["door"], parts["door_trim"] = white, black
    parts["skids"] = skids()
    parts["fit"] = fit_test()
    return parts


def main():
    p = build()
    body_bb = p["body"].bounding_box()
    write_stl(p["body"].translate([-body_bb[0], -body_bb[1], 0]), "body.stl")
    write_stl(roof_to_print(p["roof"]), "roof half.stl")
    write_stl(p["door"], "door.stl")
    write_stl(p["door_trim"], "door trim.stl")
    write_stl(p["skids"], "skids.stl")
    write_stl(on_bed(p["fit"]), "fit test.stl")

    # Orca projects, one per plate, laid out on the 220 x 220 bed
    roof_p = roof_to_print(p["roof"])
    skid_p = skid().transform(np.array([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0]], dtype=float))
    fit = on_bed(p["fit"])
    fbb = fit.bounding_box()
    write_3mf("1 fit test.3mf", [("fit test", [("fit test", fit)], (110 - fbb[3] / 2, 110 - fbb[4] / 2))])
    write_3mf("2 body.3mf", [("body", [("body", p["body"])], (110 - W / 2, 110 - L / 2))])
    rw = roof_p.bounding_box()[3]
    x0 = (220 - (2 * rw + DOOR_W + 1 + 2 * SKID_W + 4 * 6)) / 2
    y0 = (220 - (L + 2 * RAKE)) / 2
    write_3mf("3 roof, door and skids.3mf", [
        ("roof half 1", [("roof half", roof_p)], (x0, y0)),
        ("roof half 2", [("roof half", roof_p)], (x0 + rw + 6, y0)),
        ("door", [("door", p["door"]), ("door trim", p["door_trim"])], (x0 + 2 * rw + 12, y0)),
        ("skid 1", [("skid", skid_p)], (x0 + 2 * rw + DOOR_W + 1 + 18, y0)),
        ("skid 2", [("skid", skid_p)], (x0 + 2 * rw + DOOR_W + 1 + SKID_W + 24, y0)),
    ])
    for k, v in p.items():
        bb = v.bounding_box()
        print(f"{k:10s} {bb[3]-bb[0]:7.1f} x {bb[4]-bb[1]:7.1f} x {bb[5]-bb[2]:6.1f} mm  "
              f"{v.volume()/1000:6.1f} cm3  {v.num_tri()} triangles")


if __name__ == "__main__":
    main()
