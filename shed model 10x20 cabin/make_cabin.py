"""10x20 Cabin, 1:32 scale, for the Flashforge AD5X.

Run:  python make_cabin.py      (needs: pip install manifold3d numpy)

Makes the print files in this folder:
  1 fit test.3mf     two plates to try first: the porch joints (a corner of the deck, a short
                     post, a corner of the porch frame, the foot of the porch gable, the end of a
                     railing), then the front left corner, the in-swing doorway and door, and a roof peg
  2 all plates.3mf   everything, four plates, each part already on its filament (1 white siding,
                     2 black trim, roof, corner angles and porch frame, 3 brown floor, skids,
                     posts and railings)
  floor.stl          the room floor and the porch deck in one, printed upside down; the walls
                     snap onto it
  right side.stl     the right-hand side wall (seen from the porch) with its window in the middle; it
                     prints lying flat, inside face down, so the casing is the top three layers
  left side.stl      the left-hand side wall, its window in the middle too (the right side's mirror image)
  back wall.stl      the back gable end with its vent, gable band and two roof pegs
  front wall.stl     the wall under the porch, 4 ft back from the front edge, with the 11-lite
                     door's doorway right of the middle and one window left of it
  porch gable.stl    the front gable end over the porch, with its vent; it sits on the porch frame
  porch frame.stl    the black header band and side bands round the top of the porch, one frame
  porch ceiling.stl  the white panel that drops into the porch frame
  porch post.stl     print THREE. Brown 4x4 posts with a tenon at each end: one at each front corner
                     and one just left of the middle
  side railing.stl   print TWO. Down each side of the porch
  front railing.stl  print ONE. Across the front from the left corner post to the middle post, under
                     the window; the bay to the right of the middle post, in front of the door, is the way in
  roof half.stl      print TWO. Each half lifts straight off its two pegs.
  corner angle.stl   the two black L angles glued over the back corners, one of each hand
  door.stl           36 in 11-lite door, hinged on the right seen from the porch, swings in, all white
  skids.stl          the two 4x6 skids
  fit test.stl       every fit-test piece, one colour, laid out to fit the bed in one print

Sizes are the 3D designer's for the Cabin (library/manufacturers/standard.json, style C, and the
golden c-10x20 layout). Alan has confirmed only a few shop numbers for a cabin (styles.C has no
`built` block), so every size is BARNWRIGHT unless its comment says otherwise: 10 ft x 20 ft with a
4 ft front porch inside the 20 ft, 0.45 ft of rake, louvred vents in both gables, two 4x6 skids. The
walls and roof are Alan's (CONFIRMED, Alan Nov 4 2026: "Cabin 93.5 , roof pitch 5/12", read me
questions 1 and 2): his 93 1/2 in utility wall (89 in studs, one bottom plate and two top plates) and
his 5/12 roof with a 4 in level eave, as make_garage.py and make_shed.py build them, where the
designer draws 7.4 ft (88.8 in) walls and a roof rising 0.27 of the width (6.48/12) with 0.42 ft of
eave along the slope. Where the doors, windows, porch posts and front railing go is Alan's standard
layout (CONFIRMED: designer-standards.js on yoder-storage-barns.com, his copy-this-build codes, Aug 2026;
Alan Nov 3 2026 "go on yoder-storage-barns.com to see standard layout"): the 36 in 11-lite door
1.74 ft right of the front wall's middle, one 2x3 window 2.57 ft left of the middle, a 2x3 window in the
middle of each side wall, a porch post at each front corner and one 0.3 ft left of the middle, and
one front railing from the left corner post to the middle post, under the window; the bay right of
the middle post, in front of the door, is the way in. Tags on each number: CONFIRMED (Alan's, with
the source), BARNWRIGHT (the designer's raw number), DERIVED (worked out, from what), ASSUMED (our
choice, and why).

Axes for the assembled cabin: x across the 10 ft width, +x is the right side (on your right as you
stand in front of the porch looking at the door; the designer's wall R); y along the
20 ft length, +y toward the back wall, the porch at the -y end; z up, z = 0 at the bottom of the
floor joists. This matches the designer's frame (designer x -> x, designer z -> -y, designer y ->
z), so the designer's wall R is +x and its F wall is at -y. Every number is millimetres on the
model unless it says in or ft.
"""

import math
import os
import struct

import numpy as np
import manifold3d as m3

M = m3.Manifold
HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "10x20 Cabin 1:32"

# ---------------------------------------------------------------- scale
S = 25.4 / 32          # mm on the model per real inch (1:32). DERIVED: the largest common scale at
                       # which every cabin piece prints whole on the 220 mm bed (Alan Nov 3 2026: "Move
                       # to higher scale so it fits")
FT = 12 * S            # 9.525

# ---------------------------------------------------------------- the building
W = 10 * FT            # 95.25   width. Alan Nov 3 2026 ("Do the cabin and loft cabin 10x20")
L = 20 * FT            # 190.5   length, porch included
PITCH = 5 / 12         # CONFIRMED (Alan Nov 4 2026: "roof pitch 5/12", read me question 2; as make_garage.py and
                       # make_shed.py). The designer's roof.shapes.gable.rise {w: 0.27} would be 6.48/12
ALPHA = math.atan(PITCH)
RISE = (W / 2) * PITCH # 19.844  roof rise above the wall top (25 in). DERIVED
EAVE = 4 * S           # 3.175 level overhang past the long walls. CONFIRMED (Alan Nov 4 2026, read me question 2:
                       # his 4 in level eave, as make_garage.py and make_shed.py); the designer's eaveOverhang is
                       # 0.42 ft along the slope
RAKE = 0.45 * FT       # 4.286 past each gable. BARNWRIGHT rakeOverhang
PORCH = 4 * FT         # 38.1 front wall's face to the floor's front edge. BARNWRIGHT frame.js PORCH_DEPTH_FT
YF = -(L / 2 - PORCH)  # -57.15 the front wall's outside (siding) face. DERIVED

# the wall and floor section is held at the base models' millimetres (F4): at true scale the snap
# slot would break out of the floor's edge and the thinner snaps are unproven
TS = 1.4               # siding thickness, held (prints solid)
SD = 3.5 * 25.4 / 24   # 3.704 stud depth, held at the 1:24 size (4.7 in at 1:32)
SW = 1.5 * S           # 1.191 stud and joist width, true (a 2x is 1 1/2 in)
WT = TS + SD           # 5.104 whole wall
RIM = 5.0              # solid band round the edge of the floor, under the walls
JOIST_H = 5.5 * 25.4 / 24   # 5.821 held, so the snaps are exactly the shed's
DECK = 1.0             # floor sheets
ZF = JOIST_H + DECK    # 6.821 top of the floor
FLOOR_CLR = 0.4        # gap between the floor's edge and the siding that hangs down over it
WALL_H = 93.5 * S      # 74.216 floor to top of the top plates: 89 in studs, one bottom plate and two top plates.
                       # CONFIRMED (Alan Nov 4 2026: "Cabin 93.5", read me question 1; his utility wall, as
                       # make_garage.py and make_shed.py). The designer's styles.C.wallH is 7.4 ft (88.8 in)
ZWT = ZF + WALL_H      # 81.037 top of the walls
ZPK = ZWT + RISE       # 100.881 peak of the roof underside

PLATE_TOP = 3.0 * S    # double top plate, true
PLATE_BOT = 1.6        # bottom plate, held: room for the prong leg's root inside it
CHORD = 3.5 * S        # 2.778 end-truss chords (2x4), true depth in the wall plane (F4)
DOOR_HEADER = 5.0 * S  # 3.969 Alan's usual loft header, two 2x4s on edge on a flat 2x4. CONFIRMED
                       # (docs/BUILDING-TERMS.md "Usual loft header"); it fits under the plates here
WIN_HEADER = 5.5 * S   # 4.366 2x6 doubled. BARNWRIGHT construction.json walls.header
OC = 16 * S            # 12.7 studs and joists 16 in apart. BARNWRIGHT walls.spacingIn
GROOVE_OC = 8 * S      # siding grooves 8 in apart (T1-11)
GROOVE_W, GROOVE_D = 0.5, 0.35
TRIM = 3.5 * S         # 2.778 1x4 trim boards. CONFIRMED construction.openings.trim (Alan, Oct 12 2026)
PROUD = 0.6            # how far trim stands off the siding
EMBED = 0.4            # trim and window parts reach this far into the siding, so they join it
VENT_W, VENT_H = 1.12 * FT, 0.76 * FT   # 10.668 x 7.239 gable vent. BARNWRIGHT gable-vent.js
VENT_DROP = 0.92 * FT  # its centre under the peak of the roof line. BARNWRIGHT
VENT_LOUVRES = 5       # the designer's count
VENT_DEPTH = WT - 4.25 # the louvres sit in a recess this deep: its floor on the 4.25 layer line with
                       # 3 layers of siding under it, nothing out past the siding (Alan, Nov 3 2026)
VENT_SLAT = 0.45       # height of each louvre's front edge, at the siding face
VENT_BACK_GAP = 0.45   # each louvre leaves this under the next at the back (F6; the shed's 0.3 would
                       # print the first gap shut at these sizes)
VENT_Z0 = ZPK - VENT_DROP - VENT_H / 2  # 88.498 bottom of the vent's rough opening
BAND = 2.0             # the floor's solid band under the front wall reaches this far either side of
                       # it. ASSUMED: room for the closed pockets with 1.8 of floor round them

# door: 36 in 11-lite door (d36lite), in-swing, opening 36 x 75.6 in. Size BARNWRIGHT items.d36lite.
# Hinged on the +x jamb (on the right seen from the porch, next to the right side wall) and swinging
# in toward that wall, the knob toward the middle of the wall. CONFIRMED (Alan Nov 4 2026: "hinges on
# the right side", read me question 16); the designer hinges it on the left
DOOR_OPEN_W = 36 * S   # 28.575
DOOR_OPEN_H = 75.6 * S # 60.007
JAMB = DOOR_OPEN_W / 2
DOOR_X = 1.74 * FT     # 16.574 its centre, right of the front wall's middle. CONFIRMED (designer-standards.js
                       # DOOR_X {10: 1.74}, Alan's copy-this-build codes, Aug 2026): opening x 2.286..30.861
HINGE = 1              # the jamb the door hangs on: +1 the +x jamb (Alan's), -1 the -x jamb (the designer's).
                       # The Lofted Barn Cabin's door is the same door 2.1 in shorter, hung the same way
LATCH_X = DOOR_X - HINGE * JAMB         # 2.286 the latch jamb, with the stop on it
DOOR_R = 1.0           # half the door's thickness; the hinge edge is rounded to this
DOOR_T = 2 * DOOR_R
DOOR_GAP = 0.35        # gap at hinge and latch edges
DOOR_AXIS_U = 1.6      # hinge pin line out from the front wall's INSIDE face (F7, ASSUMED): the 2.7
                       # holes then reach down only to u 0.25, the top of the first layer, so the
                       # wall's bed face stays whole
AXIS_X = DOOR_X + HINGE * (JAMB - DOOR_R - DOOR_GAP)   # 29.511
AXIS_Y = YF + WT - DOOR_AXIS_U          # -53.646
DOOR_W = 2 * (JAMB - DOOR_GAP) - DOOR_R # 26.875 pin line to latch edge
DOOR_BOTTOM_GAP = 0.3
DOOR_TOP_GAP = 0.6
DOOR_H = DOOR_OPEN_H - DOOR_BOTTOM_GAP - DOOR_TOP_GAP
PIN_D = 2.0
PIN_HOLE_D = 2.7       # 0.35 mm round the pin: holes print small (Alan, Oct 31 2026)
PIN_BOTTOM_LEN = 1.3   # rests on the bottom of a 1.0 deep hole
PIN_TOP_LEN = 2.0
HOLE_BOTTOM_DEPTH = 1.0
HOLE_TOP_DEPTH = 2.2
TRENCH_DEPTH = 0.7     # the slot the bottom pin slides in through from the inside; 0.3 shallower than the hole
STOP = [(0, 2.45), (0.8, 3.25), (0.8, WT), (0, WT)]   # the stop on the latch jamb, outside the door, as
                       # (in from the jamb face, u): a 45 degree underside from the 2.45 layer line,
                       # 0.2 clear of the shut door's face at its latch edge, lapping it 0.45
# the leaf, in door print coords (X from the pin line, Y up from the door's bottom). DERIVED from
# parts/openings/door-lite.js: glass 2.24 ft wide from 0.42 of the opening height up, its arch top
# 0.55 ft under the head; 3 x 2 lites under the spring line and 4 in the fan
LITE_HALF = 1.12 * FT                                   # 10.668 half the glass width, the arch radius
LITE_X = (DOOR_W - DOOR_R) / 2                          # 12.9375 the middle of the leaf
LITE_Y0 = 0.42 * DOOR_OPEN_H - DOOR_BOTTOM_GAP          # 24.903
LITE_Y1 = DOOR_OPEN_H - 0.55 * FT - LITE_HALF - DOOR_BOTTOM_GAP   # 43.801 the arch's spring line
MUNTIN_W, MUNTIN_T = 0.8, 1.6
PANELS = [(0.30 * FT - DOOR_BOTTOM_GAP, 1.12 * FT - DOOR_BOTTOM_GAP),
          (1.36 * FT - DOOR_BOTTOM_GAP, 0.42 * DOOR_OPEN_H - 0.24 * FT - DOOR_BOTTOM_GAP)]
PANEL_HALF = 1.0 * FT  # two raised panels 2 ft wide, outlined by a groove
PANEL_GROOVE_W, PANEL_GROOVE_D = 0.6, 0.4
KNOB_X = DOOR_W - 2.2  # 2.2 in from the latch edge so it stands on solid door (designer 0.30 ft)
KNOB_Y = 0.44 * DOOR_OPEN_H - DOOR_BOTTOM_GAP
KNOB_D, KNOB_H = 1.0, 1.2

# windows: 2x3 window, 2.1 x 2.9 ft, tops level with the shop-door height 76 1/2 in. BARNWRIGHT
# items.w23 and construction.json openings.windowTop.other levelWithDoor
WIN_W = 2.1 * FT
WIN_H = 2.9 * FT
WIN_TOP = 76.5 * S     # above the floor
FRONT_WIN_X = -2.57 * FT   # -24.479 the front wall's one window, left of the door. CONFIRMED (designer-standards.js
                           # WIN_X {10: -2.57}, Aug 2026): opening x -34.481..-14.478
SIDE_WIN_Y = 2 * FT    # 19.05 a window in the middle of each side wall (the 16 ft room's middle). CONFIRMED
                       # (designer-standards.js windows R 0 and L 0, Aug 2026)

# roof
ROOF_T = 2.0
RIB_OC = 9 * S
PEG_D, PEG_UP = 2.2, 1.0
PEG_HOLE_D, PEG_HOLE_UP = 3.0, 1.4   # 0.4 mm round the peg
PEG_X = W / 4
PEG_Y = L / 2 - WT + PEG_D / 2       # 91.246 against each gable's inside face, so the pegs print
                                     # lying on the bed (the barn's placement)

# skids: two 4x6 on edge, inside face 30 in in from the outside wall. ASSUMED: carried over from
# Alan's 10x16 lesson (CONFIRMED there, Sep 27 2026); the designer's table puts the centre 30 in in
SKID_W = 3.5 * S
SKID_H = 5.5 * S
SKID_X = W / 2 - 28.25 * S
NOTCH = 0.6
NOTCH_CLEAR = 0.6      # 0.3 mm each side of a joist
SKID_PEG_D, SKID_PEG_UP = 2.0, 2.5   # a peg at each end pushes up into the floor's end band
SKID_MARK = 0.8        # the skids' front ends have both vertical corners cut off this much at 45
                       # degrees: they don't fit turned round

# snap joints, exactly the shed's (F4). Each wall stands on top of the floor; under every stud a
# post drops into a notch in the floor, and a few prongs click into slots. A prong is a springy leg
# with a barb on its foot that catches under a ledge at the bottom of its slot, and beside it a
# stiff stop that keeps the wall's foot from moving out.
FIT = 0.2              # gap round every post, prong and peg (0.2 a side is snug)
POCKET_ALONG = 0.3     # the front wall's closed post and sill pockets: 0.3 along the wall, 0.2 across.
                       # PRINTER-BRAIN "0.25-0.3 = easy fit": their mouths are first-layer faces all round
PRONG_W = 3.0          # the leg's width along the wall
PRONG_T = 0.8          # its thickness, the way it bends (4 layers)
BARB = 0.65            # the barb stands this far in from the leg, down to the bed (3 layers)
CATCH = BARB - FIT     # how far it hooks under the ledge
BARB_LAND = 0.6        # straight face between the barb's flat top and its 45 degree lead-in
LEDGE_Z = ZF - 5.25    # 1.571 the ledge, on a layer line of the upside-down floor
STOP_W, STOP_GAP, STOP_H = 1.2, 0.4, 3.0
STOP_U = 2.05          # how deep the stop is, on a layer line of the wall's print
SLOT_U = STOP_U + 0.15 # the slot's outside wall
LEG_ROOT = ZF + 1.2    # the leg is freed from the bottom plate up to here: 6.65 mm long, 1.2 % strain
BARB_RELIEF = 0.1      # the barb's top is this much lower on its first layer, for first-layer squish
MITRE_GAP = 0.1        # relief between mitred ends, and the glue gap at the front corners
SILL_UP = 0.3          # the door sill's foot stops this far above the floor's underside, inside its pocket:
                       # with the door at +1.74 ft the sill runs over the +x skid, and flush at z 0 it stood
                       # on that skid's front-band notch, so a sill printed a hair long would lift the front
                       # wall off the deck there. Nothing needs it lower: the bottom pin's hole reaches
                       # ZF - 1.0. ASSUMED, the Lofted Barn Cabin's fix (review Nov 3 2026)
# where each wall's prongs are along it (leg centres; the stop goes toward the nearer end). In stud
# bays, clear of the skids and between the floor joists. DERIVED (spec 4.10); the front wall's +x one
# moved from 34.125 (its slot would run into the moved door's sill pocket, which ends at 33.543) to
# 37.1, its slot 35.4..40.4 centred between that pocket and the +x corner notch (42.321). DERIVED
PRONGS = {"right side": (76.2, 25.4, -38.1), "left side": (76.2, 25.4, -38.1),
          "back wall": (29.8, -34.35), "front wall": (-29.8, 37.1)}

# corner angles at the two back corners (F5). The front wall stands back under the porch, where
# the designer draws no corner board; its corners are glued butt joints hidden in a siding groove.
POCKET_D = 0.4         # the recess: 2 layers of the wall's print (siding top layer 5.05, floor 4.65)
POCKET_CLR = 0.15      # gap round the angle's edges in the recess
CORNER_CHAMFER = 1.15  # the walls' outer corner cut off at 45 degrees under the angle
ANGLE_T = 1.05         # each leg, 5 layers thick; it stands 0.65 proud
ANGLE_P = ANGLE_T - POCKET_D
ANGLE_FILLET = 0.8     # 45 degree fillet in its inside corner
ANGLE_REACH = 3.0      # how far it covers the long wall's face from the corner (F5): 1.45 mm of each
                       # recess floor to glue on. ASSUMED, a bit wider than a 3 1/2 in board (3.8 in)
ANGLE_UP = 0.25 + 17 * 0.2   # 3.65 the end-face leg's width, which stands up in the print: 18 layers
ANGLE_ROOF = 0.2       # its top is this far under the roof, square to the roof

# the porch (parts/porch.js, porch-deck-frame.js). Three posts on the deck carry a black frame (the
# header band across the front and the wrap bands down both sides, in one ring), a white ceiling
# drops into the frame, and the porch gable sits on the frame's front beam.
POST = 0.25 + 15 * 0.2 # 3.25 post section, 16 layers. BARNWRIGHT drawn 0.34 ft, held to a layer line
POST_XS = (W / 2 - 0.28 * FT,)          # 44.958 a corner post each side. BARNWRIGHT
MID_POST_X = -0.3 * FT # -2.858 the one middle post, left of the middle. CONFIRMED (designer-standards.js
                       # POST_X {10: -0.3}, Aug 2026; it replaces the designer's two at +-2 ft)
POST_Y = -(L / 2 - 0.2 * FT)            # -93.345 0.2 ft back from the front edge. BARNWRIGHT
FRAME_H = 0.25 + 13 * 0.2               # 2.85 the header band, 14 layers (BARNWRIGHT 0.29 ft = 2.76)
FRAME_Z0 = ZWT - FRAME_H                # 78.186 bottom of the frame, top of the posts
FRAME_FRONT = -(L / 2 + PROUD)          # -95.85 the front beam's face, 0.6 proud of the porch gable
FRAME_IN = -(L / 2 - WT) + 1.0          # -89.146 its inner face, 1.0 behind the gable's inside face
SIDE_BEAM_END = YF - 0.2                # -57.35 the side beams stop 0.2 in front of the front wall
REAR_BEAM = (YF - PROUD - 0.2 - 1.6, YF - PROUD - 0.2)   # -59.55..-57.95: 1.6 deep, 0.2 off the casings
LIP_W, LIP_H = 1.2, 0.25 + 2 * 0.2      # the ceiling's lip inside the frame, 3 layers
TENON_L, TENON_W, TENON_T = 1.0, 1.6, 0.25 + 7 * 0.2   # each post's tenons, flush with one face
TENON_CLR = 0.35       # round every tenon and peg in its socket: holes print small (PRINTER-BRAIN)
SOCKET_D = 0.25 + 5 * 0.2   # 1.25 socket depth, a layer line
GPEG_W, GPEG_T, GPEG_L = 1.6, 1.65, 1.5   # the porch gable's two square pegs into the frame
GPEG_SOCKET = 1.6      # their sockets' depth in the frame
CEIL_T = 0.25 + 4 * 0.2    # 1.05 porch ceiling, 5 layers
CEIL_CLR = 0.2
# railings (porch.js railX/railZ), heights above the deck in ft: bottom rail, balusters from, top
# rail from, cap from, top. BARNWRIGHT; the gap under the cap is filled so the cap is carried
RAIL_FT = (0.24, 0.38, 2.56, 2.78, 2.88)
RAIL_D = 0.25 + 5 * 0.2    # 1.25 rails and balusters, 6 layers
CAP_D = 2.85               # the cap, 14 layers, overhanging toward the porch so the rails lie on the bed
BAL_W = 0.12 * FT          # 1.143 2x2 balusters
BAL_OC = 0.44 * FT         # 4.191 on centre, the designer's count, centred in each panel (ASSUMED)
RAIL_END_CLR = 0.2         # each railing's end stops this far off a post
RAIL_PEG = SOCKET_D - 0.05 # 1.2 the end balusters' pegs, 0.05 short of their holes' floor for the glue
                           # (PRINTER-BRAIN "Let a peg bottom in its hole"; the Lofted Barn Cabin's railings
                           # are the same part). A peg is the baluster's own section, so nothing else holds
                           # the panel up: pressed home a railing drops only those 0.05 (a 1.0 peg, the
                           # spec's, would let it sink 0.25 below its drawn height). ASSUMED (review Nov 3 2026)
RAIL_C = W / 2 - 0.2 * FT  # 45.72 the side runs' centre line. BARNWRIGHT
RAIL_OUT = RAIL_C + RAIL_D / 2   # 46.345 their outside face
SIDE_RAIL = (POST_Y + POST / 2 + RAIL_END_CLR, YF - 0.25 * FT)        # y -91.52..-59.531
# the one front railing, from the -x corner post to the middle post, under the window; the right bay
# (middle post to the +x corner post, x -1.233..43.333) is the way in, open. CONFIRMED (designer-standards.js)
FRONT_RAIL = (-(POST_XS[0] - POST / 2 - RAIL_END_CLR), MID_POST_X - POST / 2 - RAIL_END_CLR)   # x -43.133..-4.683
FRONT_RAIL_OUT = POST_Y - RAIL_D / 2   # -93.97 its outside face


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
    """Polygon in two cabin axes (ax0, ax1), extruded d along the third axis h from h=0.
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
    """The roof's underside over x."""
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


def on_bed(man):
    bb = man.bounding_box()
    return man.translate([-bb[0], -bb[1], -bb[2]])


def to_print(mat, parts):
    """Rotate parts together by mat and put them on the bed as one."""
    m = np.column_stack([np.array(mat, dtype=float), np.zeros(3)])
    out = [p.transform(m) for p in parts]
    bb = union(out).bounding_box()
    return [p.translate([-bb[0], -bb[1], -bb[2]]) for p in out]


# ---------------------------------------------------------------- walls: names, planes, marks
# each wall as (axis it faces along, side): along a wall is y for the side walls, x for the others
# (the long walls are named as seen from in front of the porch: both have a window now, so "window
# side" / "plain side" no longer tell them apart. Alan's standard layout, Nov 3 2026)
WALL_SIDE = {"right side": (0, 1), "left side": (0, -1), "back wall": (1, 1), "front wall": (1, -1)}
SIDES = ("right side", "left side")
# each wall's outside face, its distance from the middle; the porch gable is built on the same plane
# as a gable end at the front edge
WALL_FACE = {"right side": W / 2, "left side": W / 2, "back wall": L / 2, "front wall": L / 2 - PORCH,
             "porch gable": L / 2}
WALLS = list(WALL_SIDE)
YJ0 = YF + WT + MITRE_GAP     # -51.946 where each side wall starts, 0.1 behind the front wall's inside face
YJ = YF + WT + MITRE_GAP / 2  # the front joint's middle; the side walls' grooves are laid from here
WALL_MID = {"right side": (YF + L / 2) / 2, "left side": (YF + L / 2) / 2, "front wall": 0.0, "back wall": 0.0}


def plane(name):
    return WALL_SIDE.get(name, (1, -1)) + (WALL_FACE[name],)


def wall_box(name, a0, a1, u0, u1, z0, z1):
    """A box on one wall: a along the wall, u out from its inside face, z up."""
    axis, sign, half = plane(name)
    n0, n1 = sorted([sign * (half - WT + u0), sign * (half - WT + u1)])
    return box(n0, n1, a0, a1, z0, z1) if axis == 0 else box(a0, a1, n0, n1, z0, z1)


def wall_section(name, poly, a0, a1):
    """A polygon in (u out from the wall's inside face, z), from a0 to a1 along the wall."""
    axis, sign, half = plane(name)
    pts = [(sign * (half - WT + u), z) for u, z in poly]
    t = [0.0, 0.0, 0.0]
    t[1 - axis] = a0
    return prism(pts, axis, 2, 1 - axis, a1 - a0).translate(t)


def marks(name):
    """The 16 in layout marks along a wall, from the corner its run starts at (wall-frame.js): the
    front wall from its -x corner, the back wall from its +x corner, the side walls from the back
    corner (16 ft is twelve 16 in spaces, so either end gives the same marks)."""
    if name in ("front wall", "porch gable"):           # the porch gable's studs stand on the front wall's marks
        return layout(-W / 2, W / 2, OC)
    if name == "back wall":
        return [-a for a in layout(-W / 2, W / 2, OC)]
    return [L / 2 - OC * k for k in range(1, 30) if L / 2 - OC * k > YJ0 + SW]


def joist_ys():
    """The floor joists, 16 in apart from the back; the one under the front wall is inside the
    solid band there, so it is left out."""
    return [L / 2 - OC * k for k in range(1, 15) if not YF - BAND <= L / 2 - OC * k <= YF + WT + BAND]


def openings(name):
    """(a0, a1, z0, z1, header depth) of every opening in a wall."""
    sill, top = ZF + WIN_TOP - WIN_H, ZF + WIN_TOP
    if name == "front wall":
        return [(DOOR_X - JAMB, DOOR_X + JAMB, ZF, ZF + DOOR_OPEN_H, DOOR_HEADER),
                (FRONT_WIN_X - WIN_W / 2, FRONT_WIN_X + WIN_W / 2, sill, top, WIN_HEADER)]
    if name in SIDES:
        return [(SIDE_WIN_Y - WIN_W / 2, SIDE_WIN_Y + WIN_W / 2, sill, top, WIN_HEADER)]
    return []


def wall_run(name):
    """Where a wall's plates run along it."""
    if name == "front wall":
        return -(W / 2 - WT), W / 2 - WT
    if name == "back wall":
        return -(W / 2 - TS), W / 2 - TS
    return YJ0, L / 2 - WT


def wall_top(name):
    """Top of a wall's top plates: the front wall stands 0.15 under the roof line, so its plates
    sit 0.15 lower; the side walls are cut 0.15 under the roof by roof_clearance(), as the shed's."""
    return ZWT - 0.15 if name == "front wall" else ZWT


def end_members(name):
    """(a0, a1, what) of the framing at each end of a wall, which a layout stud may land on."""
    if name in SIDES:
        return [(YJ0, YJ0 + SW, "front end stud"), (L / 2 - WT - SW, L / 2 - TS, "back corner post")]
    if name == "front wall":
        return [(-W / 2, -(W / 2 - WT), "-x end block"), (W / 2 - WT, W / 2, "+x end block")]
    xe = W / 2 - WT
    return [(-xe, -xe + SW, "-x end stud"), (xe - SW, xe, "+x end stud")]


def framing_plan(name):
    """The framing of a side wall or the front wall, as numbers: [(a0, a1, z0, z1, what)] along the
    wall, and [(mark, what it hit, overlap)] for each layout mark dropped because its stud would land
    on other framing (F8). Round each opening, by Alan's doorway rules (CONFIRMED shop terms,
    docs/BUILDING-TERMS.md): his king stud (the short stud under the header; the shed's code called
    it the jack) and a full-height stud outside it, each side, both on the bottom plate; the header
    across both kings; studs on the marks above the header to the top plate; under a window a flat
    rough sill with cripples on the marks. A side that would be the end of the wall gets no studs (in
    Alan's standard layout every opening has room for its own each side)."""
    lo, hi = wall_run(name)
    top = wall_top(name)
    z0, z1 = ZF + PLATE_BOT, top - PLATE_TOP
    members = [(lo, hi, ZF, ZF + PLATE_BOT, "bottom plate"), (lo, hi, z1, top, "top plates")]
    solid = list(end_members(name))
    ops = openings(name)
    ax = "x" if name == "front wall" else "y"
    for (a0, a1, oz0, oz1, hh) in ops:
        what = "door's" if oz0 < ZF + 1 else "window's"
        for (k0, k1), (f0, f1), side in (((a0 - SW, a0), (a0 - 2 * SW, a0 - SW), "-"),
                                          ((a1, a1 + SW), (a1 + SW, a1 + 2 * SW), "+")):
            if k0 >= lo - 1e-9 and k1 <= hi + 1e-9:
                members.append((k0, k1, z0, oz1, "king stud"))
                solid.append((k0, k1, f"the {what} {side}{ax} king stud"))
            if f0 >= lo - 1e-9 and f1 <= hi + 1e-9:
                members.append((f0, f1, z0, z1, "full stud"))
                solid.append((f0, f1, f"the {what} {side}{ax} full stud"))
        members.append((max(a0 - SW, lo), min(a1 + SW, hi), oz1, oz1 + hh, "header"))
        if oz0 > ZF + 1:
            members.append((a0, min(a1, hi), oz0 - SW, oz0, "rough sill"))
    dropped = []
    for a in marks(name):
        s0, s1 = a - SW / 2, a + SW / 2
        hit = [(min(s1, b1) - max(s0, b0), what) for b0, b1, what in solid if min(s1, b1) - max(s0, b0) > 1e-9]
        if hit:
            ov, what = max(hit)
            dropped.append((a, what, ov))
            continue
        op = [o for o in ops if s0 >= o[0] - 1e-9 and s1 <= o[1] + 1e-9]
        if op:
            a0, a1, oz0, oz1, hh = op[0]
            if z1 - (oz1 + hh) > 0.01:
                members.append((s0, s1, oz1 + hh, z1, "cripple"))
            if oz0 > ZF + 1:
                members.append((s0, s1, z0, oz0 - SW, "cripple"))
        else:
            members.append((s0, s1, z0, z1, "stud"))
    return members, dropped


def vent_kings():
    """(a0, a1) of the king studs either side of a gable vent (parts/gable-frame.js)."""
    return [(-VENT_W / 2 - SW, -VENT_W / 2), (VENT_W / 2, VENT_W / 2 + SW)]


def gable_plan(name):
    """The studs of the back wall or the porch gable as [(xc, top or None, what)] and the marks
    dropped. top None runs the stud up into the top chord; the stud behind the vent stops under its
    sill. The back wall's end studs stand just inside the side walls."""
    solid = [(a0, a1, "a vent king") for a0, a1 in vent_kings()]
    studs = []
    if name == "back wall":
        xe = W / 2 - WT - SW / 2
        studs = [(-xe, None, "end stud"), (xe, None, "end stud")]
        solid += [(a0, a1, "the " + w) for a0, a1, w in end_members(name)]
    dropped = []
    for a in marks(name):
        s0, s1 = a - SW / 2, a + SW / 2
        hit = [(min(s1, b1) - max(s0, b0), what) for b0, b1, what in solid if min(s1, b1) - max(s0, b0) > 1e-9]
        if hit:
            ov, what = max(hit)
            dropped.append((a, what, ov))
        elif abs(a) + SW / 2 < VENT_W / 2 + 1e-9:
            studs.append((a, VENT_Z0 - SW, "cripple under the vent sill"))
        else:
            studs.append((a, None, "stud"))
    return studs, dropped


def dropped_marks():
    """DROPPED_MARKS (F8): (wall, mark in inches from the wall's middle, what it hit, overlap mm)."""
    out = []
    for name in WALLS:
        d = gable_plan(name)[1] if name == "back wall" else framing_plan(name)[1]
        out += [(name, round((a - WALL_MID[name]) / S, 2), what, round(ov, 3)) for a, what, ov in d]
    return out


DROPPED_MARKS = dropped_marks()


# ---------------------------------------------------------------- snaps
def sill_span():
    """(start, end) of the front wall's door sill along x: the door's framing, a king and a full stud
    each side of the opening, -0.096..33.243."""
    return DOOR_X - JAMB - 2 * SW, DOOR_X + JAMB + 2 * SW


def post_spans(name):
    """(start, end) along the wall of each post under it, from z = 0 up into the bottom plate: one
    under every layout mark (also where the mark's stud was dropped), the back wall's end studs, and
    under the front wall the door sill across the whole door framing (its top is the threshold).
    The front wall has none within 1 mm of an end block (the block goes down itself)."""
    m = marks(name)
    if name == "front wall":
        d0, d1 = sill_span()
        spans = [(a - SW / 2, a + SW / 2) for a in m
                 if (a + SW / 2 < d0 or a - SW / 2 > d1) and (W / 2 - WT) - (abs(a) + SW / 2) >= 1.0]
        return spans + [(d0, d1)]
    if name == "back wall":
        ends = [(a0, a1) for a0, a1, _ in end_members(name)]
        spans = [(a - SW / 2, a + SW / 2) for a in m]
        return [sp for sp in spans if not any(min(sp[1], b1) > max(sp[0], b0) for b0, b1 in ends)] + ends
    return [(a - SW / 2, a + SW / 2) for a in m]


def prong_spots(name):
    return list(PRONGS[name])


def prong_spans(ac):
    """(leg, stop): where the leg and the stop of the prong at ac are along the wall. The stop
    is on the side toward the nearer end."""
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
    """What a wall has below the top of the floor besides its siding: the posts and prongs. The
    front wall stands on the deck with no skirt, so its posts and sill are the wall's full depth; the
    sill's foot stops SILL_UP above the floor's underside, clear of the skid it crosses."""
    u1 = WT if name == "front wall" else SD + EMBED
    sill = sill_span() if name == "front wall" else None
    parts = [wall_box(name, a0, a1, 0, u1, SILL_UP if (a0, a1) == sill else 0, ZF + 0.3)
             for a0, a1 in post_spans(name)]
    for ac in prong_spots(name):
        parts += prong(name, ac)
    return parts


# ---------------------------------------------------------------- porch numbers
def post_spots():
    """(sx, |centre x|) of the three posts: the +x and -x corner posts and the middle post (sx is the
    side its tenons face: the middle post is left of the middle, so -x)."""
    sm = 1 if MID_POST_X > 0 else -1
    return [(sx, xc) for xc in POST_XS for sx in (1, -1)] + [(sm, abs(MID_POST_X))]


def tenon_box(sx, xc, z0, z1, grow=0.0):
    """A post's tenon footprint (flush with the post's outer face in x) from z0 to z1, grown by grow."""
    xo = sx * (xc + POST / 2)
    xa, xb = sorted([xo, xo - sx * TENON_T])
    return box(xa - grow, xb + grow, POST_Y - TENON_W / 2 - grow, POST_Y + TENON_W / 2 + grow, z0, z1)


def baluster_count(length):
    """The designer's count: the first 0.26 ft in, then every 0.44 ft while 0.10 ft from the end."""
    n, x = 0, 0.26 * FT
    while x < length - 0.10 * FT:
        n += 1
        x += BAL_OC
    return n


def baluster_xs(length):
    """Baluster centres along a panel, the designer's count, centred (ASSUMED: so the left and right
    side panels are the same part; the one front panel is spaced the same way)."""
    n = baluster_count(length)
    first = (length - (n - 1) * BAL_OC) / 2
    return [first + i * BAL_OC for i in range(n)]


SIDE_RAIL_LEN = SIDE_RAIL[1] - SIDE_RAIL[0]
FRONT_RAIL_LEN = FRONT_RAIL[1] - FRONT_RAIL[0]


def rail_pegs():
    """(x0, x1, y0, y1) of the six railing pegs (each panel's end balusters run on down into the
    deck): two under each side railing and two under the one front railing."""
    out = []
    for sx in (1, -1):
        for b in (baluster_xs(SIDE_RAIL_LEN)[0], baluster_xs(SIDE_RAIL_LEN)[-1]):
            y = SIDE_RAIL[0] + b
            xa, xb = sorted([sx * RAIL_OUT, sx * (RAIL_OUT - RAIL_D)])
            out.append((xa, xb, y - BAL_W / 2, y + BAL_W / 2))
    for b in (baluster_xs(FRONT_RAIL_LEN)[0], baluster_xs(FRONT_RAIL_LEN)[-1]):
        out.append((FRONT_RAIL[0] + b - BAL_W / 2, FRONT_RAIL[0] + b + BAL_W / 2, FRONT_RAIL_OUT, FRONT_RAIL_OUT + RAIL_D))
    return out


# ---------------------------------------------------------------- floor
def floor_cuts():
    """The pockets, slots and holes in the floor: a notch round each post (closed round the front
    wall's posts and sill, which stand in the deck: 0.3 along the wall, 0.2 across), a slot for each
    prong (room for the leg to bend out, the ledge with its undercut, a closer fit round the stop),
    the back corners where the corner posts go down, the front corners where the front wall's end
    blocks and the side walls' front posts go down, a hole in each end band for each skid peg, the
    post sockets and the railing peg holes."""
    c = FIT
    cuts = []
    for name in WALLS:
        front = name == "front wall"
        along = POCKET_ALONG if front else c
        u_out = WT + c if front else WT + 1
        for a0, a1 in post_spans(name):
            cuts.append(wall_box(name, a0 - along, a1 + along, -c, u_out, -1, ZF + 1))
        for ac in prong_spots(name):
            (a0, a1), (b0, b1) = prong_spans(ac)
            cuts += [wall_box(name, a0 - c, a1 + c, BARB - c, SLOT_U, -1, ZF + 1),
                     wall_box(name, a0 - c, a1 + c, -c, BARB - c + 0.01, -1, LEDGE_Z),
                     wall_box(name, b0 - c, b1 + c, -c, SLOT_U, -1, ZF + 1)]
    for sx in (1, -1):
        for dx, dy in ((0, SW), (SW, 0)):              # side wall's corner post, back wall's end stud
            xa, xb = sorted([sx * (W / 2 - WT - dx - c), sx * W])
            cuts.append(box(xa, xb, L / 2 - WT - dy - c, L, -1, ZF + 1))
        xa, xb = sorted([sx * (W / 2 - WT - c), sx * W])   # end block and the side wall's front post
        cuts.append(box(xa, xb, YF - c, YJ0 + SW + c, -1, ZF + 1))
        for y in (L / 2 - TS - FLOOR_CLR - RIM / 2, -(L / 2 - RIM / 2)):
            cuts.append(cyl_z(sx * SKID_X, y, -1, SKID_PEG_UP + 0.3, SKID_PEG_D + 2 * c))
    for x0, x1, y0, y1 in deck_holes():
        cuts.append(box(x0, x1, y0, y1, ZF - SOCKET_D, ZF + 1))
    return cuts


def deck_holes():
    """(x0, x1, y0, y1) of the holes in the porch deck as cut: the three post sockets and the six
    railing peg holes, each TENON_CLR bigger all round than what goes in it."""
    g = TENON_CLR
    out = []
    for sx, xc in post_spots():
        bb = tenon_box(sx, xc, 0, 1, g).bounding_box()
        out.append((bb[0], bb[3], bb[1], bb[4]))
    out += [(x0 - g, x1 + g, y0 - g, y1 + g) for x0, x1, y0, y1 in rail_pegs()]
    return out


DECK_KEEP = 0.6        # the deck-board grooves stop this far short of the deck's holes and the front wall's
                       # pockets (ASSUMED: laid from -x at the designer's 5 3/4 in, grooves can pass a few
                       # tenths of a mm from a socket, a railing's hole or a pocket's corner, leaving deck
                       # thinner than a line on the floor's first layer)


def deck_groove(x):
    """The deck-board groove centred on x, from the front edge back to the front wall's pockets. It is
    left out within DECK_KEEP of every post socket and railing peg hole (on to the front edge where
    that would leave less than 1 mm of groove in front of the hole), and stops DECK_KEEP short of a
    front-wall pocket or corner notch it would pass beside without running into it."""
    g0, g1 = x - 0.2, x + 0.2
    groove = box(g0, g1, -L / 2 - 1, YF - FIT, ZF - 0.25, ZF + 0.01)
    keep = []                                           # y ranges where the groove is left out, its full width
    for x0, x1, y0, y1 in deck_holes():
        if max(x0 - g1, g0 - x1) < DECK_KEEP:
            ya = y0 - DECK_KEEP if y0 - DECK_KEEP - (-L / 2) >= 1.0 else -L / 2 - 2
            keep.append(box(g0 - 1, g1 + 1, ya, y1 + DECK_KEEP, -5, ZF + 5))
    pockets = [(a0 - POCKET_ALONG, a1 + POCKET_ALONG) for a0, a1 in post_spans("front wall")]
    pockets += [(W / 2 - WT - FIT, W), (-W, -(W / 2 - WT - FIT))]           # the corner notches
    for x0, x1 in pockets:
        if 0 < max(x0 - g1, g0 - x1) < DECK_KEEP:
            keep.append(box(g0 - 1, g1 + 1, YF - FIT - DECK_KEEP, YF + 1, -5, ZF + 5))
    return groove - union(keep) if keep else groove


def floor():
    """The room floor and the porch deck in one piece. The walls stand on it with their siding
    hanging down over its edge, FLOOR_CLR clear of it; the front wall stands on the deck, its posts
    and sill in closed pockets. It prints upside down, floor face on the bed."""
    xr, yb, yd = W / 2 - TS - FLOOR_CLR, L / 2 - TS - FLOOR_CLR, YF - FIT
    b0, b1 = YF - BAND, YF + WT + BAND                  # the solid band under the front wall
    shape = union([box(-xr, xr, yd, yb, 0, ZF), box(-W / 2, W / 2, -L / 2, yd, 0, ZF)])
    cuts = []
    room = [j for j in joist_ys() if j > b1]
    porch = [j for j in joist_ys() if j < b0]
    for (xc, edges) in ((xr - RIM, [b1] + [e for j in sorted(room) for e in (j - SW / 2, j + SW / 2)] + [yb - RIM]),
                        (W / 2 - RIM, [-L / 2 + RIM] + [e for j in sorted(porch) for e in (j - SW / 2, j + SW / 2)] + [b0])):
        for a, b in zip(edges[0::2], edges[1::2]):
            cuts.append(box(-xc, xc, a, b, -1, ZF - DECK))
    cuts += [box(x0, x1, y0, y1, ZF - 0.25, ZF + 0.01) for x0, x1, y0, y1 in floor_seams()]
    # porch deck boards, 5 1/2 in with 1/4 in gaps, running front to back (porch-deck-frame.js); a few
    # grooves stop short of the deck's holes (deck_groove)
    for x in deck_groove_xs():
        cuts.append(deck_groove(x))
    return shape - union(cuts + floor_cuts())


def floor_seams():
    """The floor sheet seams in the room, (x0, x1, y0, y1) each, 0.4 wide: 4x8 sheets in rows 4 ft across from
    the -x side, staggered 4 ft."""
    xi, yi0, yi1 = W / 2 - WT, YF + WT, L / 2 - WT
    rows = [-W / 2] + layout(-W / 2, W / 2, 4 * FT) + [W / 2]
    out = []
    for i, (x0, x1) in enumerate(zip(rows, rows[1:])):
        if i:
            out.append((x0 - 0.2, x0 + 0.2, yi0, yi1))
        for k in range(0, 6):
            y = L / 2 - (4 * FT if i % 2 else 0) - 8 * FT * k
            if yi0 < y < yi1:
                out.append((max(x0, -xi), min(x1, xi), y - 0.2, y + 0.2))
    return out


def deck_groove_xs():
    """The deck-board grooves' centres: 5 1/2 in boards with 1/4 in gaps, laid from the -x side."""
    return [x for x in (-W / 2 + k * 5.75 * S - 0.125 * S for k in range(1, 30)) if x < W / 2 - 0.5]


FLOOR_TO_PRINT = [[1, 0, 0], [0, -1, 0], [0, 0, -1]]     # upside down


# ---------------------------------------------------------------- framing
def wall_framing(name):
    """Plates, studs, Alan's king studs and the full studs beside them, headers, rough sills and
    cripples on a side wall or the front wall, from framing_plan()."""
    return [wall_box(name, a0, a1, 0, SD, z0, z1) for a0, a1, z0, z1, _ in framing_plan(name)[0]]


def gable_shape():
    return prism_xz([(-W / 2, 0), (W / 2, 0), (W / 2, ZWT), (0, ZPK), (-W / 2, ZWT)], -L, L)


def top_chord(y0, y1):
    """The end truss's top chords: a band CHORD deep (square to the roof line) under it."""
    cv = CHORD / math.cos(ALPHA)
    return prism_xz([(-W / 2, ZWT - cv), (0, ZPK - cv), (W / 2, ZWT - cv), (W / 2, ZWT), (0, ZPK), (-W / 2, ZWT)], y0, y1)


def vent_framing(y0, y1, base):
    """Round a gable vent (parts/gable-frame.js frames every gable vent): a king either side from
    base up into the top chord, and a flat sill under it. No header: the top chord's underside is
    already below the vent's top at the kings, so the chord spans it, as the designer draws it."""
    parts = [box(a0, a1, y0, y1, base, ZPK) for a0, a1 in vent_kings()]
    parts.append(box(-VENT_W / 2, VENT_W / 2, y0, y1, VENT_Z0 - SW, VENT_Z0))
    return parts


def back_wall_framing():
    """Plates, studs, the end truss's top chords and the framing round the vent on the back gable.
    Its studs run from the bottom plate through the top plate up into the top chord, as the shed's
    end walls; the one behind the vent stops under the vent's sill."""
    yi, yo = L / 2 - WT, L / 2 - TS
    xin = W / 2 - TS
    parts = [box(-xin, xin, yi, yo, ZF, ZF + PLATE_BOT), box(-xin, xin, yi, yo, ZWT - PLATE_TOP, ZWT)]
    for xc, top, _ in gable_plan("back wall")[0]:
        parts.append(box(xc - SW / 2, xc + SW / 2, yi, yo, ZF + PLATE_BOT, ZPK if top is None else top))
    parts.append(top_chord(yi, yo + 0.2))                       # 0.2 into the siding so they join
    parts += vent_framing(yi, yo, ZWT)
    return union(parts) ^ gable_shape()


def porch_gable_framing():
    """The porch gable's framing: the bottom chord on the porch frame, studs on the front wall's
    marks up to the top chord (any shorter than 0.05 ft left out, the designer's tall() rule), the
    top chords and the framing round the vent, all inside the gable's triangle."""
    y0, y1 = -(L / 2 - TS), -(L / 2 - WT)              # from the siding to the inside face
    tri = prism_xz([(-W / 2, ZWT), (W / 2, ZWT), (0, ZPK)], -L, L)
    base = ZWT + CHORD
    cv = CHORD / math.cos(ALPHA)
    parts = [box(-W / 2, W / 2, y0, y1, ZWT, base)]
    for xc, top, _ in gable_plan("porch gable")[0]:
        if top is None and zline(xc) - cv - base < 0.05 * FT:
            continue
        parts.append(box(xc - SW / 2, xc + SW / 2, y0, y1, base, ZPK if top is None else top))
    parts.append(top_chord(y0 - 0.2, y1))                      # 0.2 into the siding so they join
    parts += vent_framing(y0, y1, base)
    return union(parts) ^ tri


def gable_vent(side):
    """(parts, recess): louvred vent centred under the ridge, 0.92 ft below it, 1.12 x 0.76 ft.
    Its frame is flush with the siding and its louvres stand in a recess in the siding, so
    nothing of it stands out past the siding (Alan, Nov 3 2026)."""
    zc = ZPK - VENT_DROP
    yf = side * L / 2

    def slab(x0, x1, z0, z1, d0, d1):
        """A slab d0 to d1 out from the siding face."""
        ya, yb = sorted([yf + side * d0, yf + side * d1])
        return box(x0, x1, ya, yb, z0, z1)
    fr = 1.0
    x0, x1, z0, z1 = -VENT_W / 2, VENT_W / 2, zc - VENT_H / 2, zc + VENT_H / 2
    recess = slab(x0 + fr, x1 - fr, z0 + fr, z1 - fr, -VENT_DEPTH, 1)
    parts = [slab(x0, x1, z0, z1, -EMBED, 0) - recess]         # the frame, flush; covers the siding grooves
    # louvres: wedges standing on the recess floor, flat underneath, sloping back to the floor at the
    # top, their front edges up to the siding face and no further. Each leaves VENT_BACK_GAP under the
    # next at the back, so on every layer the gaps between them are wider than a line.
    inner_h = VENT_H - 2 * fr
    for i in range(VENT_LOUVRES):
        zb = z0 + fr + inner_h * i / VENT_LOUVRES
        zt = zb + inner_h / VENT_LOUVRES - VENT_BACK_GAP
        yb = yf - side * (VENT_DEPTH + 0.1)                     # 0.1 into the floor, so they join it
        poly = [(yb, zb), (yf, zb), (yf, zb + VENT_SLAT), (yb, zt)]
        parts.append(prism(poly, 1, 2, 0, x1 - x0 - 2 * fr + 0.2).translate([x0 + fr - 0.1, 0, 0]))
    return parts, recess


def window_unit(name, ac, z0, z1):
    """Double-hung 2x3 window inside its opening: two sashes and their muntins, no glass, so you
    can see in (Alan, Oct 31 2026). Backs flush with the inside face so the wall prints flat; the
    upper sash sits back. The sash frames reach 0.2 mm into the jambs so they join the wall."""
    a0, a1 = ac - WIN_W / 2, ac + WIN_W / 2
    zm = (z0 + z1) / 2
    ring, k, mw = 1.2, 0.2, 0.8
    parts = []
    for (za, zb, uf) in ((zm, z1, WT - 0.45), (z0, zm, WT - 0.15)):
        lo = za - (k if za == z0 else 0)
        hi = zb + (k if zb == z1 else 0)
        parts += [wall_box(name, a0 - k, a1 + k, 0, uf, lo, za + ring), wall_box(name, a0 - k, a1 + k, 0, uf, zb - ring, hi),
                  wall_box(name, a0 - k, a0 + ring, 0, uf, lo, hi), wall_box(name, a1 - ring, a1 + k, 0, uf, lo, hi),
                  wall_box(name, ac - mw / 2, ac + mw / 2, 0, uf - 0.15, za, zb),                  # muntins
                  wall_box(name, a0, a1, 0, uf - 0.15, (za + zb) / 2 - mw / 2, (za + zb) / 2 + mw / 2)]
    return parts


def casing(name, a0, a1, z0, z1, door=False):
    """The 1x4 boards round an opening: two sides and a head, and a bottom board under a window (no
    sill nose; Alan, Oct 31 2026). From EMBED inside the siding face to PROUD out of it."""
    u0, u1 = WT - EMBED, WT + PROUD
    b = [wall_box(name, a0 - TRIM, a0, u0, u1, z0 if door else z0 - TRIM, z1 + TRIM),
         wall_box(name, a1, a1 + TRIM, u0, u1, z0 if door else z0 - TRIM, z1 + TRIM),
         wall_box(name, a0 - TRIM, a1 + TRIM, u0, u1, z1, z1 + TRIM)]
    if not door:
        b.append(wall_box(name, a0 - TRIM, a1 + TRIM, u0, u1, z0 - TRIM, z0))
    return b


def trims():
    """The trim that stands proud of the siding and prints in filament 2: the back gable band (none
    at the porch end: the designer's gableBandY is null on a front porch), each side wall's window
    casing, and the front wall's door casing and window casing. The corner boards at the back are
    the separate corner angles."""
    # gable band: it stops at the recess for each corner angle (the recess cuts it, the same cut as
    # the wall's, so the band's end and the recess always match)
    p = [box(-W / 2, W / 2, L / 2 - EMBED, L / 2 + PROUD, ZWT - TRIM, ZWT) - union([corner_recess(sx, 1) for sx in (1, -1)])]
    for name in SIDES + ("front wall",):
        for a0, a1, z0, z1, _ in openings(name):
            p += casing(name, a0, a1, z0, z1, door=z0 < ZF + 1)
    return p


def door_stop(jamb, z0, z1):
    """The stop on the latch jamb (at x = jamb, the opening on its HINGE side) of a doorway in the front
    wall's plane, outside the door, from z0 to z1: STOP's section, reaching 0.2 into the jamb so it
    joins it."""
    yi = YF + WT
    pts = ([(jamb - HINGE * 0.2, yi - STOP[0][1])] + [(jamb + HINGE * xp, yi - u) for xp, u in STOP]
           + [(jamb - HINGE * 0.2, yi - STOP[-1][1])])
    return prism(pts, 0, 1, 2, z1 - z0).translate([0, 0, z0])


def door_holes(ax, zf, oh):
    """The hinge pin holes of a doorway in the front wall's plane (axis at ax, AXIS_Y; sill top zf,
    opening oh tall) and the trench the bottom pin slides in through from the wall's inside face."""
    return [cyl_z(ax, AXIS_Y, zf - HOLE_BOTTOM_DEPTH, zf + 1, PIN_HOLE_D),
            cyl_z(ax, AXIS_Y, zf + oh - 1, zf + oh + HOLE_TOP_DEPTH, PIN_HOLE_D),
            box(ax - PIN_HOLE_D / 2, ax + PIN_HOLE_D / 2, AXIS_Y, YF + WT + 1, zf - TRENCH_DEPTH, zf + 1)]


def roof_clearance():
    """What the roof halves sit over, plus 0.15 mm, cut from the four walls: outside the side walls'
    planes under the eaves, the side walls' tops (only between the back wall and the front wall, so
    nothing reaches into the porch) and the front wall's top. The roof bears on the gables only."""
    out = []
    for sx in (1, -1):
        x_in, x_out = W / 2, W / 2 + 10
        poly = [(x_in, ZWT - 0.15), (x_out, ZWT - 0.15 - (x_out - x_in) * PITCH), (x_out, 300), (x_in, 300)]
        if sx < 0:
            poly = [(-x, z) for (x, z) in reversed(poly)]
        out.append(prism_xz(poly, -L, L))
        xa, xb = sorted([sx * (W / 2 - WT - 0.01), sx * (W / 2 + 1)])
        out.append(box(xa, xb, YF + WT, L / 2 - WT, ZWT - 0.15, 300))
    out.append(box(-W / 2 - 1, W / 2 + 1, YF - 1, YF + WT, ZWT - 0.15, 300))
    return out


def roof_pegs(sy):
    """The two roof pegs on a gable's top chord (sy +1 the back wall, -1 the porch gable), standing
    straight up against its inside face, trimmed PEG_UP above the roof's underside."""
    pegs = []
    for sx in (1, -1):
        x = sx * PEG_X
        peg = cyl_z(x, sy * PEG_Y, zline(x) - 3, zline(x) + 3, PEG_D)
        pegs.append(peg.trim_by_plane(*under_roof(sx, PEG_UP)))
    return pegs


def side_grooves():
    """Where the side walls' siding grooves are: every 8 in from the front joint toward the back, so
    the joint itself sits in a groove."""
    return [YJ + k * GROOVE_OC for k in range(1, 40) if YJ + k * GROOVE_OC < L / 2 - 0.01]


def front_corner_cuts():
    """The groove the front joints hide in: a 0.25 x 0.35 notch down each side wall's front outer
    edge and a 0.35 x 0.35 chamfer down the front wall's end block's back outer edge (a square notch
    there would hang over the first layer in the front wall's print). Together about 0.7 wide at
    the face, with the 0.1 joint at the bottom, 0.35 in from the face."""
    out = []
    yi = YF + WT
    for sx in (1, -1):
        xa, xb = sorted([sx * (W / 2 - GROOVE_D), sx * (W / 2 + 1)])
        out.append(box(xa, xb, yi + 0.05, YJ0 + 0.25, -1, 400))
        pts = [(W / 2 - GROOVE_D, yi + 0.05), (W / 2 - GROOVE_D, yi), (W / 2 + 1, yi - GROOVE_D - 1), (W / 2 + 1, yi + 0.05)]
        ch = prism(pts, 0, 1, 2, 401).translate([0, 0, -1])
        out.append(ch if sx > 0 else ch.mirror([1, 0, 0]))
    return out


def walls():
    """All four walls in one, assembled; split_walls() cuts them apart for printing."""
    gable = [(-W / 2, 0), (W / 2, 0), (W / 2, ZWT), (0, ZPK), (-W / 2, ZWT)]
    shell = prism_xz(gable, YF, L / 2)
    # the siding only; below the floor's top it is the skirt that hangs over the floor's edge. The
    # front wall stands on the deck: no skirt (siding.js "except where a wall stands on a porch deck")
    cuts = [box(-W / 2 + TS, W / 2 - TS, YF + TS, L / 2 - TS, -1, 400),
            box(-W / 2 - 1, W / 2 + 1, YF - 1, YF + WT, -1, ZF)]
    for x in layout(-W / 2, W / 2, GROOVE_OC):
        cuts.append(box(x - GROOVE_W / 2, x + GROOVE_W / 2, L / 2 - GROOVE_D, L / 2 + 1, -1, ZPK + 1))
        cuts.append(box(x - GROOVE_W / 2, x + GROOVE_W / 2, YF - 1, YF + GROOVE_D, -1, ZPK + 1))
    for y in side_grooves():
        for sx in (1, -1):
            xa, xb = sorted([sx * (W / 2 - GROOVE_D), sx * (W / 2 + 1)])
            cuts.append(box(xa, xb, y - GROOVE_W / 2, y + GROOVE_W / 2, -1, ZWT + 1))
    shell = shell - union(cuts)

    framing = wall_framing("right side") + wall_framing("left side") + wall_framing("front wall")
    framing.append(back_wall_framing())
    for name in WALLS:
        framing += under_floor(name)
    for sx in (1, -1):
        # back corner posts, solid into the corner so each wall's mitred end is a solid 45 degree
        # wedge; they go down through the floor's corners
        xa, xb = sorted([sx * (W / 2 - WT), sx * (W / 2 - TS)])
        framing.append(box(xa, xb, L / 2 - WT - SW, L / 2 - TS, 0, ZWT))
        # the front wall's end blocks: it owns the whole front corner, down through the floor's notch
        xa, xb = sorted([sx * (W / 2 - WT), sx * W / 2])
        framing.append(box(xa, xb, YF, YF + WT, 0, ZWT))
        # each side wall's front end stud, with a post down into that notch
        xa, xb = sorted([sx * (W / 2 - WT), sx * (W / 2 - TS)])
        framing.append(box(xa, xb, YJ0, YJ0 + SW, 0, ZWT))
    b = union([shell] + framing + trims())
    b = b - union([prong_relief(name, ac) for name in WALLS for ac in prong_spots(name)])

    op_cuts = [wall_box(name, a0, a1, -0.5, WT + 2, z0, z1) for name in WALLS for a0, a1, z0, z1, _ in openings(name)]
    parts, recess = gable_vent(1)
    b = b - union(op_cuts + [recess])
    windows = [q for name in WALLS for a0, a1, z0, z1, _ in openings(name) if z0 > ZF + 1
               for q in window_unit(name, (a0 + a1) / 2, z0, z1)]
    b = union([b] + windows + parts + [door_stop(LATCH_X, ZF, ZF + DOOR_OPEN_H)])
    b = b - union(door_holes(AXIS_X, ZF, DOOR_OPEN_H))
    b = b - union(roof_clearance())
    b = b + union(roof_pegs(1))
    # nothing over the side walls' mitred back ends higher than the rest of their top, 0.15 under the
    # roof line, so a side wall can be lowered into place beside the back wall and the roof bears on
    # the gables only (the shed cut these at the plate top, where they touched the roof at the eave)
    for sx in (1, -1):
        b = b - mitred(0, sx).trim_by_plane([0, 0, 1], ZWT - 0.15)
    # the recess for each back corner angle and the chamfer under it, and the front corners' groove
    return b - union([corner_recess(sx, sy) for sx, sy in CORNERS] + front_corner_cuts())


def body():
    """The assembled body: four walls and the floor."""
    return union(list(split_walls(walls()).values()) + [floor()])


# the back corners meet at 45 degree mitres through the inside and outside corners, as the shed's,
# so each wall carries only the trim on its own face and it all prints on top. Each wall prints
# lying flat on the inside face of its framing, outside up.
BIG = 500


def mitred(axis, sign):
    """The region one wall owns at the back corners: outside its inside face, and on its side of the
    mitre at each corner. axis 0 for a side wall, 1 for the back wall; sign which side."""
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
    """Above the top of the wall plates on one end of the cabin. The gable's corners above the plates
    go with the back wall, where they lie on the bed."""
    return M.cube([2 * BIG] * 3, True).trim_by_plane([0, 0, 1], ZWT).trim_by_plane([0, sign, 0], 0)


def side_region(sx):
    """A side wall: its side of the back mitre, from 0.1 behind the front wall's inside face, below
    the wall top."""
    return mitred(0, sx).trim_by_plane([0, 1, 0], YJ0).trim_by_plane([0, 0, -1], -ZWT)


WALL_CUTS = {
    "right side": side_region(1),
    "left side": side_region(-1),
    "back wall": mitred(1, 1) + above_plate(1),
    "front wall": box(-BIG, BIG, YF - 2, YF + WT, -BIG, ZWT),
}
# cabin coords to print coords, inside face down (each a rotation, det +1)
WALL_TO_PRINT = {
    "right side": [[0, 1, 0], [0, 0, 1], [1, 0, 0]],
    "left side": [[0, -1, 0], [0, 0, 1], [-1, 0, 0]],
    "back wall": [[-1, 0, 0], [0, 0, 1], [0, 1, 0]],
    "front wall": [[1, 0, 0], [0, 0, 1], [0, -1, 0]],
    "porch gable": [[1, 0, 0], [0, 0, 1], [0, -1, 0]],
}


def split_walls(w):
    """The four walls cut apart. Where a cut lies on a face of the body it can leave a flat scrap
    with no volume; those are dropped."""
    return {name: union([c for c in (w ^ cut).decompose() if c.volume() > 1e-6]) for name, cut in WALL_CUTS.items()}


# ---------------------------------------------------------------- corner angles (back corners only)
CORNERS = [(1, 1), (-1, 1)]   # (sx, sy): the right side is +x, the back wall +y


def corner_walls(sx, sy):
    """(side wall, back wall) that meet at a back corner."""
    return ("right side" if sx > 0 else "left side"), "back wall"


def corner_frame(sx, sy):
    """Matrix from a corner's own coords to cabin coords: u out from the side wall's siding face,
    v out from the back wall's, z up, so u = v = 0 is the outer corner of the siding. For the -x
    corner it is a mirror image."""
    return np.array([[sx, 0, 0, sx * W / 2], [0, sy, 0, sy * L / 2], [0, 0, 1, 0]], dtype=float)


def angle_reach():
    """How far the corner angle reaches from the outer corner of the siding along (the side wall,
    the back wall): ANGLE_REACH on the side wall, and on the back wall what the standing leg's
    ANGLE_UP leaves past the side-face leg (F5: both 3.0)."""
    return ANGLE_REACH, ANGLE_UP - (ANGLE_T - POCKET_D)


def corner_recess(sx, sy):
    """What comes out of both walls at a corner for its angle: a recess POCKET_D deep in each
    wall's outside face, reaching POCKET_CLR past the angle's edge, and the chamfer off the outer
    corner, square to the mitre. Both run from the bottom of the skirt up through the top of the
    wall."""
    ra, rb = angle_reach()
    big = 20
    h = 1 / math.sqrt(2)
    cut = union([box(-POCKET_D, big, -(ra + POCKET_CLR), big, -1, 400),
                 box(-(rb + POCKET_CLR), big, -POCKET_D, big, -1, 400),
                 box(-big, big, -big, big, -1, 400).trim_by_plane([h, h, 0], -(2 * POCKET_D + CORNER_CHAMFER) * h)])
    return cut.transform(corner_frame(sx, sy))


def corner_angle(sx, sy):
    """The black L angle at a back corner, in cabin coords: two legs ANGLE_T thick with their inside
    faces on the recess floors, a 45 degree fillet in the inside corner, the foot level with the
    bottom of the skirts, and the top ANGLE_ROOF under the roof, square to it, across both legs."""
    out = ANGLE_T - POCKET_D
    ra, rb = angle_reach()
    p, f = POCKET_D, POCKET_D + ANGLE_FILLET
    sec = [(out, out), (out, -ra), (-p, -ra), (-p, -f), (-f, -p), (-rb, -p), (-rb, out)]
    a = prism(sec, 0, 1, 2, ZPK).transform(corner_frame(sx, sy))
    return a.trim_by_plane(*under_roof(sx, -ANGLE_ROOF))


def angle_to_print(sx):
    """Cabin coords to print coords for an angle on the sx side: lying on the side-face leg's
    outside face, its length along y, the back-face leg standing up. A rotation, det +1; the two
    angles come out as mirror images."""
    return [[0, -sx, 0], [0, 0, 1], [-sx, 0, 0]]


def angle_prints():
    """The two corner angles lying the way they print, in CORNERS order, each on the bed at the origin."""
    return [to_print(angle_to_print(sx), [corner_angle(sx, sy)])[0] for sx, sy in CORNERS]


def trim_zone():
    """Everything standing proud of the siding that is trim. It prints in the second colour. The
    real outline is taken off (the front wall's face is at YF, not -L/2: a box to -L/2 would swallow
    the front wall's casings and they would print white)."""
    return union(trims()) - box(-W / 2, W / 2, YF, L / 2, -1, 400)


def two_colour(piece, zone):
    """(siding colour, trim colour) parts of a piece."""
    return piece - zone, piece ^ zone


# ---------------------------------------------------------------- porch
def porch_frame_clearance():
    """Everything above the plane 0.15 mm (vertically) under each roof half's underside, over that
    half. It only bevels the frame's top outer edges past |x| = W / 2 - 0.15 / PITCH = 47.265."""
    out = []
    for s_ in (1, -1):
        poly = [(0, zline(0) - 0.15), (W / 2 + 10, ZWT - 0.15 - 10 * PITCH), (W / 2 + 10, 400), (0, 400)]
        if s_ < 0:
            poly = [(-x, z) for (x, z) in reversed(poly)]
        out.append(prism_xz(poly, -L, L))
    return out


def porch_frame(gable_peg_xs=(-PEG_X, PEG_X)):
    """The black frame round the top of the porch, one piece: the header band across the front (its
    face 0.6 proud of the porch gable, reaching 1.0 behind the gable's inside face), the wrap bands
    down both sides (flush with the side walls' siding, stopping 0.2 in front of the front wall), and
    a rear beam 0.2 in front of the front wall's casings; a lip inside all four for the ceiling, a
    socket from below for each post's top tenon and from above for each of the porch gable's pegs."""
    z0, z1 = FRAME_Z0, ZWT
    xi = W / 2 - WT
    r0, r1 = REAR_BEAM
    beams = [box(-W / 2, W / 2, FRAME_FRONT, FRAME_IN, z0, z1),
             box(xi, W / 2, FRAME_FRONT, SIDE_BEAM_END, z0, z1),
             box(-W / 2, -xi, FRAME_FRONT, SIDE_BEAM_END, z0, z1),
             box(-xi, xi, r0, r1, z0, z1)]
    lip = (box(-xi, xi, FRAME_IN, r0, z0, z0 + LIP_H)
           - box(-xi + LIP_W, xi - LIP_W, FRAME_IN + LIP_W, r0 - LIP_W, z0 - 1, z1 + 1))
    f = union(beams + [lip])
    cuts = [tenon_box(sx, xc, z0 - 1, z0 + SOCKET_D, TENON_CLR) for sx, xc in post_spots()]
    gi = -(L / 2 - WT)
    g = TENON_CLR
    for x in gable_peg_xs:
        cuts.append(box(x - GPEG_W / 2 - g, x + GPEG_W / 2 + g, gi - GPEG_T - g, gi + g, z1 - GPEG_SOCKET, z1 + 1))
    return f - union(cuts + porch_frame_clearance())


def porch_ceiling():
    """The white porch ceiling: a loose plate on the frame's lip, 0.2 clear of the four beams."""
    xi = W / 2 - WT - CEIL_CLR
    return box(-xi, xi, FRAME_IN + CEIL_CLR, REAR_BEAM[0] - CEIL_CLR, FRAME_Z0 + LIP_H, FRAME_Z0 + LIP_H + CEIL_T)


def porch_gable(peg_xs=(-PEG_X, PEG_X)):
    """The front gable end over the porch: siding with grooves, its framing, the vent, two square
    pegs down into the porch frame and two roof pegs up into the roof halves. It stands on the
    frame's front beam, its siding face at the front edge."""
    tri = [(-W / 2, ZWT), (W / 2, ZWT), (0, ZPK)]
    siding = prism_xz(tri, -L / 2, -(L / 2 - TS))
    siding = siding - union([box(x - GROOVE_W / 2, x + GROOVE_W / 2, -L / 2 - 1, -L / 2 + GROOVE_D, ZWT - 1, ZPK + 1)
                             for x in layout(-W / 2, W / 2, GROOVE_OC)])
    parts, recess = gable_vent(-1)
    g = union([siding, porch_gable_framing()]) - recess
    gi = -(L / 2 - WT)
    pegs = [box(x - GPEG_W / 2, x + GPEG_W / 2, gi - GPEG_T, gi, ZWT - GPEG_L, ZWT + 0.3) for x in peg_xs]
    return union([g] + parts + pegs + roof_pegs(-1))


def post_local(body_len):
    """A porch post standing on the deck at the origin: its body from z = 0 to body_len, a tenon
    below and above, flush with its +x face (the face it prints on), centred the other way."""
    h = POST / 2
    return union([box(-h, h, -h, h, 0, body_len),
                  box(h - TENON_T, h, -TENON_W / 2, TENON_W / 2, -TENON_L, 0.01),
                  box(h - TENON_T, h, -TENON_W / 2, TENON_W / 2, body_len - 0.01, body_len + TENON_L)])


def post(sx, xc):
    """A porch post in place, its tenons toward the outside of the cabin in x; the -x posts are the
    same part turned round."""
    p = post_local(FRAME_Z0 - ZF).translate([xc, POST_Y, ZF])
    return p if sx > 0 else p.mirror([1, 0, 0])


POST_TO_PRINT = [[0, 0, 1], [0, 1, 0], [-1, 0, 0]]     # a +x post lying on its tenon face


def railing_local(length):
    """A railing panel: X along it, Y in from its outside face, Z up from the deck top. A bottom
    rail, balusters, a top rail and the cap (overhanging toward the porch); the two end balusters
    run on down into the deck as pegs."""
    zb0, zb1, zt0, zc0, zc1 = [f * FT for f in RAIL_FT]
    xs = baluster_xs(length)
    parts = [box(0, length, 0, RAIL_D, zb0, zb1), box(0, length, 0, RAIL_D, zt0, zc0),
             box(0, length, 0, CAP_D, zc0, zc1)]
    for i, xc in enumerate(xs):
        lo = -RAIL_PEG if i in (0, len(xs) - 1) else zb0
        parts.append(box(xc - BAL_W / 2, xc + BAL_W / 2, 0, RAIL_D, lo, zc0))
    return union(parts)


def side_railing(sx=1):
    """A side railing in place, down the sx side of the porch."""
    m = np.array([[0, -1, 0, RAIL_OUT], [1, 0, 0, SIDE_RAIL[0]], [0, 0, 1, ZF]], dtype=float)
    r = railing_local(SIDE_RAIL_LEN).transform(m)
    return r if sx > 0 else r.mirror([1, 0, 0])


def front_railing():
    """The one front railing in place, from the -x corner post to the middle post."""
    return railing_local(FRONT_RAIL_LEN).translate([FRONT_RAIL[0], FRONT_RAIL_OUT, ZF])


SIDE_RAIL_TO_PRINT = [[0, -1, 0], [0, 0, 1], [-1, 0, 0]]   # the +x side railing on its outside face
FRONT_RAIL_TO_PRINT = [[-1, 0, 0], [0, 0, 1], [0, 1, 0]]   # the front railing on its outside face
FRAME_TO_PRINT = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]         # bottom face down
CEILING_TO_PRINT = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]       # the face seen from below on the bed


# ---------------------------------------------------------------- roof
def roof_frame():
    """Matrix taking local roof coords (X=y, Y=n up from the underside, Z=s down the slope
    from the ridge) to the +x half in cabin coords."""
    d = np.array([math.cos(ALPHA), 0, -math.sin(ALPHA)])
    nrm = np.array([math.sin(ALPHA), 0, math.cos(ALPHA)])
    p0 = np.array([0, 0, ZPK])
    return np.column_stack([[0, 1, 0], nrm, d, p0])


def roof_half():
    """The +x roof half in cabin coords (the -x half is its mirror image), from the ridge to the
    eave, past both gables by the rake. It rests on the back gable and the porch gable."""
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
        holes.append(h.trim_by_plane(*under_roof(1, PEG_HOLE_UP)))
    return r - union(holes)


def roof_to_print(r):
    """Lay a +x roof half on the bed, underside down."""
    mat = roof_frame()
    R = mat[:, :3]
    p0 = mat[:, 3]
    Rt = R.T
    to_local = np.column_stack([Rt, -Rt @ p0])                            # (y, n, s)
    swap = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], dtype=float)        # (s, y, n), det +1
    full = np.column_stack([swap @ to_local[:, :3], swap @ to_local[:, 3]])
    p = r.transform(full)
    bb = p.bounding_box()
    return p.translate([-bb[0], -bb[1], -bb[2]])


# ---------------------------------------------------------------- door
def door_hand(d):
    """A door drawn with its latch edge toward +X from the pin line, made the door for the HINGE jamb:
    hung on the +x jamb it is that door's mirror image, the latch toward -X, so in door print coords X
    always runs the cabin's way along the front wall with the door shut (door_matrix)."""
    return d.mirror([1, 0, 0]) if HINGE > 0 else d


def door_leaf():
    """The 11-lite door in print coords: X across the door from the pin line (the latch edge toward
    -HINGE), Y up the door from its bottom, Z through it (Z=0 the inside face, on the bed). All white:
    the lite hole with its muntins (from the bed up 1.6, 0.4 under the outside face), two raised panels
    outlined by grooves in the outside face, and a knob on the outside face only."""
    t = DOOR_T
    leaf = union([box(0, DOOR_W, 0, DOOR_H, 0, t), cyl_y(0, 0, DOOR_H, DOOR_R, 2 * DOOR_R),
                  cyl_y(0, DOOR_H - 0.5, DOOR_H + PIN_TOP_LEN, DOOR_R, PIN_D, 40),
                  cyl_y(0, -PIN_BOTTOM_LEN, 0.5, DOOR_R, PIN_D, 40)])
    xc = LITE_X
    hole = union([box(xc - LITE_HALF, xc + LITE_HALF, LITE_Y0, LITE_Y1, -1, t + 1),
                  cyl_z(xc, LITE_Y1, -1, t + 1, 2 * LITE_HALF, 96)])
    grooves = []
    for y0, y1 in PANELS:
        x0, x1 = xc - PANEL_HALF, xc + PANEL_HALF
        g = PANEL_GROOVE_W
        grooves.append(box(x0, x1, y0, y1, t - PANEL_GROOVE_D, t + 1) - box(x0 + g, x1 - g, y0 + g, y1 - g, t - 1, t + 2))
    leaf = leaf - union([hole] + grooves)
    mw, k = MUNTIN_W, 0.2                                  # muntins reach 0.2 into the leaf to join it
    ym = (LITE_Y0 + LITE_Y1) / 2
    mun = [box(xc + s_ * LITE_HALF / 3 - mw / 2, xc + s_ * LITE_HALF / 3 + mw / 2, LITE_Y0 - k, LITE_Y1, 0, MUNTIN_T)
           for s_ in (-1, 1)]
    mun += [box(xc - LITE_HALF - k, xc + LITE_HALF + k, y - mw / 2, y + mw / 2, 0, MUNTIN_T) for y in (ym, LITE_Y1)]
    for ang in (45, 90, 135):                              # the fan's three spokes
        mun.append(box(0, LITE_HALF + k, -mw / 2, mw / 2, 0, MUNTIN_T).rotate([0, 0, ang]).translate([xc, LITE_Y1, 0]))
    knob = cyl_z(KNOB_X, KNOB_Y, t - 0.01, t + KNOB_H, KNOB_D, 32)
    return door_hand(union([leaf, knob] + [q ^ box(xc - LITE_HALF - k, xc + LITE_HALF + k, LITE_Y0 - k,
                                                   LITE_Y1 + LITE_HALF + k, -1, t) for q in mun]))


def door_matrix(theta_deg=0.0, ax=AXIS_X, zf=ZF):
    """Matrix from door print coords to cabin coords, hinge axis at (ax, AXIS_Y), the door's bottom
    DOOR_BOTTOM_GAP over zf, swung in theta degrees (its latch edge toward +y, into the room: hung on
    the +x jamb it turns clockwise seen from above, toward the right side wall)."""
    base = np.array([[1, 0, 0, ax], [0, 0, -1, AXIS_Y + DOOR_R], [0, 1, 0, zf + DOOR_BOTTOM_GAP]], dtype=float)
    th = math.radians(-HINGE * theta_deg)
    rot = np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]])
    pivot = np.array([ax, AXIS_Y, 0])
    R = rot @ base[:, :3]
    t = rot @ (base[:, 3] - pivot) + pivot
    return np.column_stack([R, t])


def door_to_cabin(theta_deg=0.0):
    return door_matrix(theta_deg)


# ---------------------------------------------------------------- skids
def skid():
    """One skid lying along X, X = 0 its front end: notched where the joists, the floor's bands and
    the back wall's skirt sit on it, with a peg at each end that pushes up into the end band. The
    front end has both vertical corners cut off: the skid isn't the same end for end."""
    s = box(0, L, 0, SKID_W, 0, SKID_H)
    top = (SKID_H - NOTCH, SKID_H + 1)
    cuts = []
    for jy in joist_ys():
        X = jy + L / 2
        cuts.append(box(X - SW / 2 - NOTCH_CLEAR / 2, X + SW / 2 + NOTCH_CLEAR / 2, -1, SKID_W + 1, *top))
    back = TS + FLOOR_CLR + RIM + 0.3
    cuts.append(box(-1, RIM + 0.3, -1, SKID_W + 1, *top))                    # front band, no skirt at the porch
    cuts.append(box(L - back, L + 1, -1, SKID_W + 1, *top))                  # back band and skirt
    cuts.append(box(YF - BAND + L / 2 - 0.3, YF + WT + BAND + L / 2 + 0.3, -1, SKID_W + 1, *top))   # front-wall band
    m = SKID_MARK
    cuts.append(prism([(-1, -1), (m + 1, -1), (-1, m + 1)], 0, 1, 2, SKID_H + 2).translate([0, 0, -1]))
    cuts.append(prism([(-1, SKID_W + 1), (-1, SKID_W - m - 1), (m + 1, SKID_W + 1)], 0, 1, 2, SKID_H + 2).translate([0, 0, -1]))
    s = s - union(cuts)
    pegs = [cyl_z(X, SKID_W / 2, SKID_H - NOTCH - 0.01, SKID_H - NOTCH + SKID_PEG_UP, SKID_PEG_D)
            for X in (RIM / 2, L - (TS + FLOOR_CLR + RIM / 2))]
    return s + union(pegs)


def skids():
    """Both skids side by side for the .stl, far enough apart that their brims don't meet."""
    s = skid()
    return s + s.translate([0, SKID_W + 12, 0])


def skids_to_cabin():
    """Matrices placing skid() under the floor, joists down in the notches, front ends at the porch."""
    return [np.array([[0, -1, 0, sx * SKID_X + SKID_W / 2], [1, 0, 0, -L / 2], [0, 0, 1, -(SKID_H - NOTCH)]], dtype=float)
            for sx in (-1, 1)]


SKID_TO_PLATE = [[0, -1, 0], [1, 0, 0], [0, 0, 1]]       # along y on the plate


# ---------------------------------------------------------------- fit test
FIT_X0 = 33.0          # the deck corner and the railing end are cut from x 33.0 to the +x side
FIT_Y1 = -84.0         # and from the front to y -84.0
FIT_FRAME_X0 = 41.0    # the frame corner from x 41.0 to the +x side and from the front to y -88.5, so it
FIT_FRAME_Y1 = -88.5   # balances on the one short post by itself, the gable foot on it too: cut at 33.0
                       # and -84.0 its weight was 2 mm outside the post's top and it fell off (review Nov 3
                       # 2026). DERIVED: its centre of mass over the post's top, 0.5 mm in from every edge
FIT_PEG_X = 42.8       # the porch gable's peg and its frame socket are moved here for the test, 0.65 mm of
                       # frame left to the cut and 0.63 to the post's socket
FIT_FOOT_X0 = -W / 2 + 14 * GROOVE_OC   # 41.275, the gable foot is cut from the middle of the siding groove
                       # here: cut at FIT_FRAME_X0 with the frame corner, 0.025 short of that groove (it starts
                       # at 41.025), it left a strip of siding 0.025 wide at the cut in its top layers, thinner
                       # than a 0.42 line, which the slicer drops (check Nov 3 2026, as the Lofted Barn
                       # Cabin's). Its end stands 0.275 in from the frame corner's. DERIVED
FIT_FOOT_X1 = FIT_PEG_X + 2.0   # the gable foot is cut from FIT_FOOT_X0 to here
FIT_POST_BODY = 12.0
FIT_GABLE_H = 5.0
FIT_RAIL = 9.0


def porch_fit_pieces(f):
    """(name, piece in its print position) for the fit test's first plate, the porch joints: the
    deck's front +x corner, a short post, the porch frame's front +x corner, the porch gable's foot
    (from FIT_FOOT_X0 to FIT_FOOT_X1) and the front end of a side railing, each cut from the real
    part with its real joints."""
    deck = f ^ box(FIT_X0, W, -L, FIT_Y1, -5, 50)
    pst = post_local(FIT_POST_BODY)
    frame = porch_frame((FIT_PEG_X,)) ^ box(FIT_FRAME_X0, W, -L, FIT_FRAME_Y1, 0, 200)
    foot = porch_gable((FIT_PEG_X,)) ^ box(FIT_FOOT_X0, FIT_FOOT_X1, -L, 0, ZWT - 3, ZWT + FIT_GABLE_H)
    rail = side_railing(1) ^ box(0, W, -L, SIDE_RAIL[0] + FIT_RAIL, -5, 100)
    return [("deck corner", to_print(FLOOR_TO_PRINT, [deck])[0]),
            ("short post", to_print(POST_TO_PRINT, [pst])[0]),
            ("frame corner", to_print(FRAME_TO_PRINT, [frame])[0]),
            ("gable foot", to_print(WALL_TO_PRINT["porch gable"], [foot])[0]),
            ("railing end", to_print(SIDE_RAIL_TO_PRINT, [rail])[0])]


FIT_CORNER_X0 = -20.5  # the short front corner is the -x one (the +x one is in the moved door now): the front
                       # wall from its -x end to x -20.5, 1.13 past the cripple at -22.225 under the window and
                       # 0.83 past that post's pocket. DERIVED (re-cut for Alan's standard layout, Nov 3 2026)
FIT_CORNER_Y1 = L / 2 - 10 * OC + SW / 2   # -31.155 the left side from its front end to the far side of the
                       # stud at y -31.75, so the cut end of its skirt is held by a post (spec -33.0: there the
                       # skirt hung free at the cut and Flash Studio called it a floating cantilever)
FIT_LO, FIT_HI = 8.0, 6.0   # each wall's bottom 8 mm above the floor joined to its top 6 mm
FIT_CORNER_STUD = -W / 2 + 2 * OC   # -22.225, the cripple (on the 32 in mark) that the cut at FIT_CORNER_X0 passes,
                       # under the window and over its header: the short front wall's bridge modifier stops on its
                       # middle, as across the studs the strip past it would be held at one end only (ACROSS_STUDS)


def front_corner_test(pieces, f):
    """The front -x corner made short: the front wall from its -x end to x -20.5 and the left side
    from its front end to the far side of the stud at y -31.75, each its bottom 8 mm above the floor
    joined to its top 6 mm, on the floor under them (the end block's notch, the closed pockets of the
    posts at x -34.925 and -22.225, the side wall's pockets and prong slot, the front wall's -x prong
    slot, a strip of deck). Returns (front wall, side wall, floor) in cabin coords."""
    def short(piece, keep, top):
        z_lo, z_hi = ZF + FIT_LO, top - FIT_HI
        lo = piece ^ keep ^ box(-BIG, BIG, -BIG, BIG, -5, z_lo)
        hi = piece ^ keep ^ box(-BIG, BIG, -BIG, BIG, z_hi, 400)
        return lo + hi.translate([0, 0, z_lo - z_hi])
    fw = short(pieces["front wall"], box(-W, FIT_CORNER_X0, -BIG, BIG, -5, 400), ZWT - 0.15)
    sw = short(pieces["left side"], box(-W, 0, -BIG, FIT_CORNER_Y1, -5, 400), ZWT - 0.15)
    fl = f ^ box(-W, FIT_CORNER_X0, -60.0, FIT_CORNER_Y1, -5, 400)           # the floor under them
    return fw, sw, fl


FIT_OPEN_W, FIT_OPEN_H, FIT_SILL = 14.0, 24.0, 3.0
FIT_AXIS_X = HINGE * (FIT_OPEN_W / 2 - DOOR_R - DOOR_GAP)   # 5.65, on the same jamb as the real door's


def fit_doorway():
    """A short in-swing doorway in the front wall's plane: the 14 x 24 opening on its own 3 mm sill
    block (no floor: the real door is hung in the loose wall), hinged on the same side as the real
    one, the axis 1.6 from the inside face, the outside stop and the trench out to the inside face,
    exactly as the real ones."""
    jamb, zf, oh = FIT_OPEN_W / 2, FIT_SILL, FIT_OPEN_H
    n = "front wall"
    frame = [wall_box(n, -jamb - 6, jamb + 6, 0, WT, 0, zf), wall_box(n, -jamb - 6, -jamb, 0, WT, zf, zf + oh + 6),
             wall_box(n, jamb, jamb + 6, 0, WT, zf, zf + oh + 6), wall_box(n, -jamb - 6, jamb + 6, 0, WT, zf + oh, zf + oh + 6)]
    f = union(frame + [door_stop(-HINGE * jamb, zf, zf + oh)])
    return f - union(door_holes(FIT_AXIS_X, zf, oh))


def fit_door():
    """The short door for fit_doorway(), in door print coords, with the same pins and hinge edge."""
    dw = FIT_OPEN_W - 2 * DOOR_GAP - DOOR_R
    dh = FIT_OPEN_H - DOOR_BOTTOM_GAP - DOOR_TOP_GAP
    return door_hand(union([box(0, dw, 0, dh, 0, DOOR_T), cyl_y(0, 0, dh, DOOR_R, 2 * DOOR_R),
                            cyl_y(0, dh - 0.5, dh + PIN_TOP_LEN, DOOR_R, PIN_D, 40),
                            cyl_y(0, -PIN_BOTTOM_LEN, 0.5, DOOR_R, PIN_D, 40)]))


def peg_block():
    """make_barn.fit_test()'s roof peg on a block lying like a gable, so the peg lies on the bed, and
    the bit of roof with its hole. Returns (block, coupon) in print position."""
    blk = box(-6, 6, 0, 6, 0, WT) + cyl_y(0, 5, 6 + PEG_UP, PEG_D / 2, PEG_D)
    cpn = box(-6, 6, -6, 6, 0, ROOF_T) - cyl_z(0, 0, -1, PEG_HOLE_UP, PEG_HOLE_D)
    return on_bed(blk), on_bed(cpn)


def front_fit_pieces(pieces, f):
    """(name, piece in its print position) for the fit test's second plate."""
    fw, sw, fl = front_corner_test(pieces, f)
    blk, cpn = peg_block()
    return [("short front wall", to_print(WALL_TO_PRINT["front wall"], [fw])[0]),
            ("short side wall", to_print(WALL_TO_PRINT["left side"], [sw])[0]),
            ("bit of floor", to_print(FLOOR_TO_PRINT, [fl])[0]),
            ("doorway", to_print(WALL_TO_PRINT["front wall"], [fit_doorway()])[0]),
            ("short door", on_bed(fit_door())),
            ("peg block", blk), ("roof coupon", cpn)]


def row_up(named, gap=6.0, width=200.0):
    """Lay pieces out in rows from the front left, gap apart, rows no wider than width.
    Returns [(name, piece, (x, y))]."""
    out, x, y, h = [], 0.0, 0.0, 0.0
    for name, m in named:
        bb = m.bounding_box()
        w_, d_ = bb[3] - bb[0], bb[4] - bb[1]
        if x > 0 and x + w_ > width:
            x, y, h = 0.0, y + h + gap, 0.0
        out.append((name, m, (x, y)))
        x += w_ + gap
        h = max(h, d_)
    return out


def fit_plates(p):
    """The two plates of 1 fit test.3mf, each laid out in the middle of the bed, one filament. The short walls and
    the doorway carry their real walls' bridge modifier (ACROSS_STUDS), the short front wall's stopping on the
    cripple at FIT_CORNER_STUD (its print x: the short front wall starts at the front wall's -x end, x = -W/2)."""
    own = {"short front wall": lambda m: across_studs(m, x_to=FIT_CORNER_STUD + W / 2),
           "short side wall": across_studs, "doorway": across_studs}
    plates = []
    for pname, named in (("porch joints", p["fit porch"]), ("front corner, door and roof peg", p["fit front"])):
        laid = row_up(named, 6.0, 190.0)
        bw = max(x + m.bounding_box()[3] for _, m, (x, y) in laid)
        bh = max(y + m.bounding_box()[4] for _, m, (x, y) in laid)
        ox, oy = (220 - bw) / 2, (220 - bh) / 2
        plates.append((pname, [(n, [(n, m, 1)], (ox + x, oy + y)) + ((own[n](m),) if n in own else ())
                               for n, m, (x, y) in laid]))
    return plates


def fit_test_stl(p):
    """Every fit-test piece for `fit test.stl`, laid so the lot fits the bed: the second plate's row
    at the front and the first plate's row 6 mm behind it. Returns [(name, piece placed)]."""
    out, y_next = [], 0.0
    for _, items in reversed(fit_plates(p)):
        placed = []
        for n, [(_, m, _)], (x, y), *own in items:
            bb = m.bounding_box()
            placed.append((n, m.translate([x - bb[0], y - bb[1], -bb[2]])))
        bb = union([m for _, m in placed]).bounding_box()
        out += [(n, m.translate([-bb[0], y_next - bb[1], 0])) for n, m in placed]
        y_next += bb[4] - bb[1] + 6.0
    return out


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
    its lower-left corner at x, y on its plate, and optionally a dict of that object's own
    settings after (x, y). An object with two parts opens in Orca as one object, each part
    already set to its filament (1 siding, 2 trim, roof, angles and porch frame, 3 floor, skids,
    posts and railings). "modifier" in the settings, [(name, manifold, settings)] in the parts' coords, is
    written as modifier parts with those settings and no filament of their own (as the garages'); where the
    object lies on the plate comes from its parts alone."""
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
            settings = dict(own[0]) if own else {}
            modifiers = settings.pop("modifier", [])
            bb = union([m for _, m, _ in parts]).bounding_box()
            # store each object's shape centred on its own middle and place that middle on the
            # plate, the way Flash Studio saves its own projects
            mid = np.array([(bb[0] + bb[3]) / 2, (bb[1] + bb[4]) / 2, (bb[2] + bb[5]) / 2])
            comp_ids = []
            vols = [(part_name, man, f'<part id="{{}}" subtype="normal_part"><metadata key="name" '
                     f'value={quoteattr(part_name)}/><metadata key="extruder" value="{filament}"/></part>')
                    for part_name, man, filament in parts]
            vols += [(mod_name, mod_man, f'<part id="{{}}" subtype="modifier_part"><metadata key="name" '
                      f'value={quoteattr(mod_name)}/>'
                      + "".join(f'<metadata key="{k}" value={quoteattr(v)}/>' for k, v in mod_settings.items())
                      + '</part>') for mod_name, mod_man, mod_settings in modifiers]
            cfg.append(f'<object id="{oid + len(vols)}"><metadata key="name" value={quoteattr(obj_name)}/>'
                       f'<metadata key="extruder" value="{parts[0][2]}"/>'
                       + "".join(f'<metadata key="{k}" value={quoteattr(v)}/>' for k, v in settings.items()))
            for part_name, man, part_cfg in vols:
                cfg.append(part_cfg.replace('<part id="{}"', f'<part id="{oid}"', 1))
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


def build():
    parts = {}
    f = floor()
    pieces = split_walls(walls())
    parts["body"] = union(list(pieces.values()) + [f])
    parts["floor"] = f
    parts.update(pieces)
    parts["porch gable"] = porch_gable()
    parts["porch frame"] = porch_frame()
    parts["porch ceiling"] = porch_ceiling()
    parts["post"] = post(1, POST_XS[0])
    parts["posts"] = union([post(sx, xc) for sx, xc in post_spots()])
    parts["side railing"] = side_railing(1)
    parts["front railing"] = front_railing()
    parts["railings"] = union([side_railing(sx) for sx in (1, -1)] + [front_railing()])
    parts["angles"] = union([corner_angle(sx, sy) for sx, sy in CORNERS])
    parts["roof"] = roof_half()
    parts["door"] = door_leaf()
    parts["skids"] = skids()
    parts["fit porch"] = porch_fit_pieces(f)
    parts["fit front"] = front_fit_pieces(pieces, f)
    return parts


def wall_parts(p, name, zone):
    """(siding, trim) of a wall, lying flat on the bed."""
    return to_print(WALL_TO_PRINT[name], two_colour(p[name], zone))


def size(m):
    bb = m.bounding_box()
    return bb[3] - bb[0], bb[4] - bb[1]


NO_BRIM = {"brim_type": "no_brim"}
SKID_BRIM = {"brim_type": "outer_only", "brim_width": "5"}
# The walls lie flat to print, framing down, so the siding's first layer (3.65 to 3.85, over the 3.704 stud depth)
# is a bridge over every stud bay: about 11 mm across between the studs, 60 mm or more along them between the
# plates. Flash Studio picks the direction itself, and not the same way every time: slices of the 10x20 Cabin laid
# its right side's and front wall's bays lengthwise, 66 mm strands, which sag, and of the Lofted Barn Cabin its
# front wall's, 62 mm, where other slices of the same files had them across (Nov 4 2026; the 12x24 Garage's final
# audit saw the same). So, as on both garages, each wall carries a modifier over its siding, from SIDING_BRIDGE_Z
# up, that sets External bridge infill direction 180, which Flash Studio reads as along the bed's X: across the
# studs (every wall lies along X on its plate). It starts over the framing, so the prong legs' first layer (0.65
# to 0.85), the plate over each leg's root (1.65 to 1.85), the door stop's ends (2.85 to 3.05) and the Lofted Barn
# Cabin's loft notches (2.05 to 2.45) keep the slicer's own direction, as before. Every wall that could bridge
# over 20 mm gets one, not only the ones seen to flip, and each fit-test piece if its real wall has one, so it
# prints the same way. Where across the studs would leave siding held at one end only, the box stops on framing
# and what it leaves is proven short every way (the checker's group 10): the 10x20 Cabin's short front wall's
# stops on the cripple its cut passes (FIT_CORNER_STUD); the Lofted Barn Cabin's gables stop theirs on the collar
# tie (COLLAR_MID), and over it a second box lays the triangles up the gable (UP_THE_GABLE, 90, along the king
# post: 11 mm at most, where across they are 31 mm). The 10x20 Cabin's porch gable needs none: its bays are 15 mm
# or less every way. Flash Studio lays a set direction along the bed whichever way a part is turned, so the walls
# must stay unturned on their plates (the read me says so). ASSUMED (as sliced)
ACROSS_STUDS = {"bridge_angle": "180"}
UP_THE_GABLE = {"bridge_angle": "90"}
SIDING_BRIDGE_Z = SD - 0.5           # 3.204: under the siding's first layer (3.65 to 3.85), over the 2.85 one
# The floor prints face down, so its sheet seams and deck-board grooves, 0.4 wide and its first layer deep, are
# bridged on its second layer (0.25 to 0.45). The room's seams all meet, and Flash Studio bridged them as one, the
# same way: along the bed's X, across the seams that run along Y but along the ones that run along X, in strands up
# to 39 mm (38.7 unsupported over the middle row's two, 32.2 and 13.1 over the outer rows'; every slice of both
# cabins, Nov 4 2026). So the floor carries a modifier box over each seam, on its second layer only (FLOOR_SEAM_Z),
# SEAM_BAND each side of it, setting its bridges straight across it: ALONG_Y (90) over a seam along the bed's X,
# ALONG_X (180) over one along Y, and one ALONG_X box over the deck's grooves (all along Y). A seam along X stops its
# box SEAM_BAND short of a seam along Y it meets, so no two boxes overlap; its last SEAM_BAND is in that seam's box,
# so bridged along it there (2.1 mm unsupported at most), and where two boxes meet a few tenths of a mm of the
# groove can be left open, which the third layer covers. Flash Studio splits the floor into regions round the
# boxes, so a little of its inner infill moves on a few higher layers too, nothing that shows; every other part on
# the plate prints exactly as before (slices of Nov 4 2026). The fit test's bits of floor need none: what they leave
# hanging free is short every way (11 mm at most, a deck-board groove across the deck corner). ASSUMED (as sliced)
ALONG_X, ALONG_Y = ACROSS_STUDS, UP_THE_GABLE   # bridge_angle 180 lays bridges along the bed's X, 90 along its Y
FLOOR_SEAM_Z = (0.2, 0.5)            # the floor's second layer (0.25 to 0.45) as it prints, over its first, under its third
SEAM_BAND = 2.0


def across_seams(fl):
    """The settings of the floor (fl, in cabin coords): a modifier box over each of its seams (floor_seams) and one
    over the deck's grooves, on its second layer only, where FLOOR_TO_PRINT lays it on the bed (see FLOOR_SEAM_Z)."""
    R = np.column_stack([np.array(FLOOR_TO_PRINT, dtype=float), np.zeros(3)])
    bb = fl.transform(R).bounding_box()
    top = fl.bounding_box()[5]
    z0, z1 = top - FLOOR_SEAM_Z[1], top - FLOOR_SEAM_Z[0]
    seams = floor_seams()
    along_y = [(x0 + x1) / 2 for x0, x1, y0, y1 in seams if y1 - y0 > x1 - x0]

    def end(x, out):
        """Where the box of a seam along X ends: SEAM_BAND past the seam's end (out, +1 or -1), or SEAM_BAND
        short of a seam along Y it meets there."""
        return x - out * SEAM_BAND if any(abs(x - xs) < 0.5 for xs in along_y) else x + out * SEAM_BAND

    boxes = []
    for x0, x1, y0, y1 in seams:
        if x1 - x0 > y1 - y0:
            yc = (y0 + y1) / 2
            boxes.append((box(end(x0, -1), end(x1, 1), yc - SEAM_BAND, yc + SEAM_BAND, z0, z1), ALONG_Y))
        else:
            xc = (x0 + x1) / 2
            boxes.append((box(xc - SEAM_BAND, xc + SEAM_BAND, y0 - SEAM_BAND, y1 + SEAM_BAND, z0, z1), ALONG_X))
    boxes.append((box(-W / 2 - 1, W / 2 + 1, -L / 2 - 1, YF - FIT + SEAM_BAND, z0, z1), ALONG_X))
    return {"modifier": [("bridges across the seams", m.transform(R).translate([-bb[0], -bb[1], -bb[2]]), kv)
                         for m, kv in boxes]}


def across_studs(part, x_to=None, y_to=None):
    """The object settings for a wall lying flat (part, on the bed, from its own corner): a modifier box over its
    siding layers, from SIDING_BRIDGE_Z to over its top and 1 mm past it all round, setting ACROSS_STUDS (see
    there). With x_to it stops there along the bed's X (on a stud); with y_to it stops there along Y (on a collar
    tie) and a second box, from there to 1 mm past the top, sets UP_THE_GABLE."""
    bb = part.bounding_box()
    x1 = bb[3] + 1 if x_to is None else x_to
    y1 = bb[4] + 1 if y_to is None else y_to
    mods = [("bridges across the studs", box(bb[0] - 1, x1, bb[1] - 1, y1, SIDING_BRIDGE_Z, bb[5] + 1), ACROSS_STUDS)]
    if y_to is not None:
        mods.append(("bridges up the gable", box(bb[0] - 1, bb[3] + 1, y_to, bb[4] + 1, SIDING_BRIDGE_Z, bb[5] + 1),
                     UP_THE_GABLE))
    return {"modifier": mods}


def all_plates(p, walls_p):
    """The plates of 2 all plates.3mf (F3), in order: the long walls and the door; the roof, porch
    frame and corner angles; the end walls, porch gable and ceiling; the floor, skids and porch.
    Filament 1 is white (siding, door, porch gable, ceiling), 2 black (trim, roof, angles, porch
    frame), 3 brown (floor, skids, posts, railings). The prime tower goes at x 165, y 195, so every
    part on the two-colour plates (1 and 3) ends at x 162 or y 192 or less. The skids get a 5 mm
    brim; the angles, roof halves, posts, railings and porch frame none (a brim's lip would show
    along a visible edge). Each wall carries its bridge modifier (ACROSS_STUDS); the porch gable needs none. The
    floor carries its seams' (across_seams)."""
    def wall_item(name, x, y):
        siding, trim = walls_p[name]
        parts = [("siding", siding, 1)] + ([] if trim.is_empty() else [("trim", trim, 2)])
        return (name, parts, (x, y), across_studs(union([siding, trim])))

    lw, lh = size(union(walls_p["right side"]))
    door = on_bed(p["door"])
    roof_p = roof_to_print(p["roof"])
    rw, rh = size(roof_p)
    frame_p = on_bed(to_print(FRAME_TO_PRINT, [p["porch frame"]])[0].transform(
        np.array([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0]], dtype=float)))
    fw_, fh_ = size(frame_p)
    angles = angle_prints()
    aw, ah = size(angles[0])
    bw_, bh_ = size(union(walls_p["back wall"]))
    frw, frh = size(union(walls_p["front wall"]))
    gable_p = to_print(WALL_TO_PRINT["porch gable"], [p["porch gable"]])[0]
    gw_, gh_ = size(gable_p)
    ceil_p = to_print(CEILING_TO_PRINT, [p["porch ceiling"]])[0]
    cw_, ch_ = size(ceil_p)
    fl = to_print(FLOOR_TO_PRINT, [p["floor"]])[0]
    flw, flh = size(fl)
    skid_p = on_bed(skid().transform(np.column_stack([np.array(SKID_TO_PLATE, dtype=float), np.zeros(3)])))
    sw_, sh_ = size(skid_p)
    post_p = on_bed(to_print(POST_TO_PRINT, [p["post"]])[0].transform(
        np.array([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0]], dtype=float)))
    pw_, ph_ = size(post_p)
    srail = to_print(SIDE_RAIL_TO_PRINT, [p["side railing"]])[0]
    frail = to_print(FRONT_RAIL_TO_PRINT, [p["front railing"]])[0]
    srh = size(srail)[1]

    y0 = (220 - 2 * lh - 3) / 2
    ry = (220 - rh) / 2
    fx = 3 + 2 * rw + 12
    ax = fx + fw_ + 6
    sk1 = 3 + flw + 6.15
    sk2 = sk1 + sw_ + 10.72
    px = sk2 + sw_ + 6.02
    n_posts = len(post_spots())
    rx = px + n_posts * pw_ + (n_posts - 1) * 3.0 + 3.0
    ry0 = (220 - 3 * srh - 2 * 3.07) / 2              # the three railings stacked, centred on the plate
    rys = [ry0 + i * (srh + 3.07) for i in range(3)]
    return [
        ("long walls and door", [wall_item("right side", 3, y0), wall_item("left side", 3, y0 + lh + 3),
                                 ("door", [("door", door, 1)], (3 + lw + 3, y0))]),
        ("roof, porch frame and corner angles",
         [("roof half 1", [("roof half", roof_p, 2)], (3, ry), NO_BRIM),
          ("roof half 2", [("roof half", roof_p, 2)], (3 + rw + 6, ry), NO_BRIM),
          ("porch frame", [("porch frame", frame_p, 2)], (fx, (220 - fh_) / 2), NO_BRIM)]
         + [("corner angle, %s at the back wall" % corner_walls(sx, sy)[0], [("corner angle", a, 2)],
             (ax + i * (aw + 4), (220 - ah) / 2), NO_BRIM) for i, ((sx, sy), a) in enumerate(zip(CORNERS, angles))]),
        ("end walls, porch gable and ceiling",
         [wall_item("back wall", 3, 3), wall_item("front wall", 104.25, 3),
          ("porch gable", [("porch gable", gable_p, 1)], (104.25, 3 + frh + 6)),
          ("porch ceiling", [("porch ceiling", ceil_p, 1)], (3, 3 + bh_ + 6))]),
        ("floor, skids and porch",
         [("floor", [("floor", fl, 3)], (3, (220 - flh) / 2), across_seams(p["floor"])),
          ("skid 1", [("skid", skid_p, 3)], (sk1, (220 - sh_) / 2), SKID_BRIM),
          ("skid 2", [("skid", skid_p, 3)], (sk2, (220 - sh_) / 2), SKID_BRIM)]
         + [("porch post %d" % (i + 1), [("porch post", post_p, 3)], (px + i * (pw_ + 3.0), (220 - ph_) / 2), NO_BRIM)
            for i in range(n_posts)]
         + [("side railing %d" % (i + 1), [("side railing", srail, 3)], (rx, rys[i]), NO_BRIM) for i in range(2)]
         + [("front railing", [("front railing", frail, 3)], (rx, rys[2]), NO_BRIM)]),
    ]


def main():
    p = build()
    zone = trim_zone()
    walls_p = {name: wall_parts(p, name, zone) for name in WALL_CUTS}
    write_stl(to_print(FLOOR_TO_PRINT, [p["floor"]])[0], "floor.stl")
    for name in WALLS:
        write_stl(union(walls_p[name]), name + ".stl")
    write_stl(to_print(WALL_TO_PRINT["porch gable"], [p["porch gable"]])[0], "porch gable.stl")
    write_stl(to_print(FRAME_TO_PRINT, [p["porch frame"]])[0], "porch frame.stl")
    write_stl(to_print(CEILING_TO_PRINT, [p["porch ceiling"]])[0], "porch ceiling.stl")
    write_stl(to_print(POST_TO_PRINT, [p["post"]])[0], "porch post.stl")
    write_stl(to_print(SIDE_RAIL_TO_PRINT, [p["side railing"]])[0], "side railing.stl")
    write_stl(to_print(FRONT_RAIL_TO_PRINT, [p["front railing"]])[0], "front railing.stl")
    write_stl(roof_to_print(p["roof"]), "roof half.stl")
    angles = angle_prints()
    write_stl(union([a.translate([i * (a.bounding_box()[3] + 4), 0, 0]) for i, a in enumerate(angles)]), "corner angle.stl")
    write_stl(on_bed(p["door"]), "door.stl")
    write_stl(p["skids"], "skids.stl")
    write_stl(on_bed(union([m for _, m in fit_test_stl(p)])), "fit test.stl")

    write_3mf("1 fit test.3mf", fit_plates(p))
    write_3mf("2 all plates.3mf", all_plates(p, walls_p))
    for name, (siding, trim) in walls_p.items():
        bb = union([siding, trim]).bounding_box()
        print(f"{name:12s} flat {bb[3]-bb[0]:7.1f} x {bb[4]-bb[1]:7.1f} x {bb[5]-bb[2]:6.2f} mm  "
              + (f"trim {trim.volume()/1000:5.2f} cm3, from {trim.bounding_box()[2]:.2f} mm up" if not trim.is_empty()
                 else "no trim"))
    for k, v in p.items():
        if isinstance(v, list):
            continue
        bb = v.bounding_box()
        print(f"{k:14s} {bb[3]-bb[0]:7.1f} x {bb[4]-bb[1]:7.1f} x {bb[5]-bb[2]:6.1f} mm  "
              f"{v.volume()/1000:6.1f} cm3  {v.num_tri()} triangles")
    for w, mark, what, ov in DROPPED_MARKS:
        print(f"dropped mark: {w}, {mark:+.0f} in from its middle, on {what} ({ov:.2f} mm)")


if __name__ == "__main__":
    main()
