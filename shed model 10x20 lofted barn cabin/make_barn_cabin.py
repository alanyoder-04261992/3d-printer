"""10x20 Lofted Barn Cabin, 1:32 scale, for the Flashforge AD5X.

Run:  python make_barn_cabin.py      (needs: pip install manifold3d numpy)

Makes the print files in this folder:
  1 fit test.3mf    to try first: plate 1 the porch joints (a corner of the deck, a short post, a
                    corner of the porch frame, the foot of the porch gable and the end of a
                    railing), plate 2 a short front corner, the in-swing doorway and door, and a
                    roof peg
  2 all plates.3mf  everything, one plate per print, the trim, roof, corner angles and porch frame
                    already set to filament 2, the floor, skids, lofts, posts and railings to 3
  floor.stl         floor frame, floor sheets and the porch deck in one, printed upside down; the
                    walls snap onto it
  right side.stl    the long wall on the right seen from the porch (+x), with its window, framing,
                    trim; prints lying flat, inside face down, so the trim is the top few layers
  left side.stl     the other long wall (-x), its window in the same place, the same way
  front wall.stl    the wall under the porch with the door right of centre and one window left of it
  back wall.stl     the back end with its gable, vent, framing and the roof pegs
  porch gable.stl   the front gable over the porch, with the faux loft window, vent and roof pegs
  porch frame.stl   the black ring at the top of the porch: header band, wrap bands, rear beam
  porch ceiling.stl the white panel that drops into the porch frame
  porch post.stl    print THREE. The porch posts (a corner post each side and one left of centre),
                    a tenon at each end.
  side railing.stl  print TWO. The railings down the porch's sides.
  front railing.stl print ONE. The railing across the front from the left corner post to the
                    middle post, under the window; the right bay, in front of the door, is the way in.
  upper roof.stl    print TWO. The shallow top half of each side of the barn roof.
  lower roof.stl    print TWO. The steep bottom half of each side; the upper one laps over it.
  loft.stl          print TWO. The loft floor behind the front wall and at the back.
  corner angle.stl  the two black corner angles for the back corners, one of each hand
  door.stl          the 36 in 11-lite door with its hinge pins, all white; hinged on the right seen
                    from the porch, it swings in
  skids.stl         the two 4x6 skids the floor sits on
  fit test.stl      all the fit-test pieces

It is the 8x12 Side Lofted Barn model (../shed model 8x12 side lofted barn/make_barn.py), the
same snap joints, mitred back corners with glued black angles, loft and four-sheet barn roof,
built as the shop-standard Lofted Barn Cabin, 10x20 (Alan, Nov 3 2026: "Do the cabin and loft
cabin 10x20"). Its twin is the 10x20 Cabin model: the porch, the front corners and the 11-lite
door are built the same way (the porch posts are shorter here, for the lower wall, and the door
2.1 in shorter, under Alan's flat header). The walls are Alan's 79 1/2 in lofted wall and the door
his 73 1/2 in under two flat 2x4s (Nov 4 2026, "Loft wall height is 79.5" and "73 1/2 in door, flat
boards"). The other sizes are the 3D designer's for style LBC (library/manufacturers/
standard.json): a barn roof 54 in over the top plate at the roof line, a 4 ft porch across the
front inside the 20 ft, a 4 ft loft at each end of the 16 ft room. Nothing else about this style
is confirmed by Alan yet (it has no built block), so the shop rule keeps Barnwright's roof and the
rest. The framing is Alan's, as taught on the 10x16 Side Lofted Barn and drawn by
the barn model (open question 13 in the read me). The doors, windows, gable window and porch posts
are where Alan's own standard puts them (Nov 3 2026, "go on yoder-storage-barns.com to see
standard layout": designer-standards.js on the site, his copy-this-build codes, Aug 2026): the
11-lite door 1.74 ft right of the porch wall's middle, one window 2.57 ft left of it, a window in
the middle of each long wall, one middle porch post 0.3 ft left of centre with the front railing
under the window and the way in in front of the door, and the faux loft window in the porch gable
(the octagon is a $200 option, not standard).

Every number below is tagged: CONFIRMED (Alan's, with where he said it), BARNWRIGHT (the
designer's number, not confirmed by Alan), DERIVED (worked out, from what), ASSUMED (our choice,
and why). A rule Alan confirmed on another building is ASSUMED here ("carried over").

Axes for the assembled cabin: x across the 10 ft width (+x the right side, on your right
standing in front of the porch looking at the door), y along the 20 ft, the porch at -y and the
back wall at +y, z
up. z = 0 is the bottom of the floor joists (where the body sits on the skids). Every number is
millimetres on the model.
"""

import math
import os
import struct

import numpy as np
import manifold3d as m3

M = m3.Manifold
HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "10x20 Lofted Barn Cabin 1:32"

# ---------------------------------------------------------------- scale
S = 25.4 / 32          # mm on the model per real inch. DERIVED from Alan's rule (Nov 3 2026, "Move
                       # to higher scale so it fits"): the largest common scale at which every piece
                       # prints whole on the 220 bed (at 1:24 the roof sheets would be 260 mm)
FT = 12 * S

# ---------------------------------------------------------------- the building
W = 10 * FT            # 95.25  width. CONFIRMED (Alan, Nov 3 2026)
L = 20 * FT            # 190.5  length, porch included. CONFIRMED size; porch inside it BARNWRIGHT
PORCH = 4 * FT         # 38.1   porch depth across the front. BARNWRIGHT (parts/porch.js)
YF = -(L / 2 - PORCH)  # -57.15 the front wall's siding face: it stands 4 ft back under the porch
YM = (YF + L / 2) / 2  # 19.05  the middle of the room along y

# the wall and floor section, held at the base models' millimetres (F4): proven in print (Nov
# 2026); at true scale the floor's edge would stand only 2.4 mm out from the wall's inside face
# and the prong slot would break out of it. ASSUMED (held).
TS = 1.4               # siding thickness (thicker than scale so it prints solid)
SD = 3.5 * 25.4 / 24   # 3.704 stud depth, held at the base models' 1:24 size
SW = 1.5 * S           # 1.191 stud, joist and plate width in the wall plane: true 1 1/2 in. DERIVED
WT = TS + SD           # 5.104 whole wall
RIM = 5.0              # solid band round the edge of the floor, under the walls
JOIST_H = 5.5 * 25.4 / 24   # 5.821 held, the base models' 2x6 joists
DECK = 1.0             # floor sheets
ZF = JOIST_H + DECK    # 6.821 top of the floor
FLOOR_CLR = 0.4        # gap between the floor's edge and the siding that hangs down over it
WALL_H = 79.5 * S      # 63.103 floor to top of the upper plate: Alan's lofted wall, 75 in studs on one
                       # 1 1/2 in bottom plate under two 1 1/2 in top plates. CONFIRMED (Alan, Nov 4 2026,
                       # "Loft wall height is 79.5", open question 1; the 8x12 Side Lofted Barn's wall). The
                       # designer's style LBC wallH is 6.9 ft, 82.8 in
ZWT = ZF + WALL_H      # 69.924 top of the walls

# the barn roof, as the 3D designer draws the shop-standard LBC at 10 ft wide (construction.json
# roof.shapes.gambrel): the knee 0.38 of the width out from the middle, 0.32 of the width up at the
# knee and 0.13 more to the peak, 54 in over the top plate in all (53.54 in to the truss peak under
# the 7/16 in deck). BARNWRIGHT (open question 2: not Alan's 48 in Lofted Barn truss). This line
# is the underside of the roof sheets.
KNEE_X = 3.8 * FT                   # 36.195
LOWER_RISE = 3.2 * FT               # 30.48  wall top to knee
UPPER_RISE = 1.3 * FT               # 12.383 knee to peak
ZKN = ZWT + LOWER_RISE
ZPK = ZKN + UPPER_RISE
LOW_M = LOWER_RISE / (W / 2 - KNEE_X)   # the steep lower slope, 32/12. DERIVED
UP_M = UPPER_RISE / KNEE_X              # the shallow upper slope, 4.1/12. DERIVED
GABLE = [(-W / 2, 0), (W / 2, 0), (W / 2, ZWT), (KNEE_X, ZKN), (0, ZPK), (-KNEE_X, ZKN), (-W / 2, ZWT)]
EAVE_S = 0.42 * FT     # the lower sheets run on this far down the slope past the wall top. BARNWRIGHT
END_OH = 0.10 * FT     # the lower sheets reach this far past each gable. BARNWRIGHT
RAKE_STEP = 0.135 * FT # and the upper sheets this much further (designer's RAKE_STEP). BARNWRIGHT

PLATE_TOP = 3.0 * S    # 2.381 top plate and upper plate. BARNWRIGHT (construction.json walls)
PLATE_BOT = 1.6        # bottom plate, held for the prong leg (F4). ASSUMED (held)
HEADER = 5.0 * S       # Alan's 5 in loft header (two 2x4s on edge on a flat 2x4) right under the
                       # top plates, over each window. ASSUMED (carried over, CONFIRMED on the Side
                       # Lofted Barn, Alan Nov 2 2026 "The way you have it is right")
FLAT_HEADER = 3.0 * S  # over the door, Alan's two flat 2x4s, "for a taller door" (BUILDING-TERMS.md
                       # doorway framing): on the 73 1/2 in door's 72 in kings, 72 + 3 = 75 in, the full stud,
                       # so the header is right under the top plates with nothing between. CONFIRMED (Alan,
                       # Nov 4 2026, "73 1/2 in door, flat boards", open question 12)
GABLE_BOARD = 5.5 * S  # 2x6 on edge on top of the gable's upper plate. ASSUMED (carried over,
                       # CONFIRMED on the 10x16 Side Lofted Barn)
BACKING_Z = 11 * S     # gable backing, back wall only: its bottom 11 in over the upper plate,
BACKING_H = 3.5 * S    # 3 1/2 in high. ASSUMED (carried over)
GABLE_STUD_W = 3.5 * S # gable studs, wide face out, 24 in apart from the outside of the end wall.
GABLE_STUD_XS = [-36 * S, -12 * S, 12 * S, 36 * S]   # ASSUMED (carried over)
CHORD = 3.5 * S        # the end truss's four chords, one 2x4 deep under the roof line (F4: drawn
                       # their true depth, not SD). ASSUMED (Alan's truss lesson)
COLLAR_H = 3.5 * S     # a collar tie across the knees and a king post above it. BARNWRIGHT (as the
KING_W = 3.5 * S       # designer draws barn trusses; flagged in the read me)
GROOVE_OC = 8 * S      # siding grooves 8 in apart (as the base models)
GROOVE_W, GROOVE_D = 0.5, 0.35
TRIM = 3.5 * S         # 1x4 trim boards, 3 1/2 in. CONFIRMED (standard.json construction.openings
                       # .trim._source, Alan Oct 12 2026)
PROUD = 0.6            # how far trim stands off the siding (the top 3 layers)
EMBED = 0.4            # trim and window parts reach this far into the siding, so they join it
RAKE_W = 2.0           # the rake board showing under the roof edge round each gable
BAND_Z = ZWT + 0.40 * (ZPK - ZWT)   # the gable band across the back wall only. BARNWRIGHT
VENT_FLOOR = 4.25 - WT # the gable vents' louvres sit in a recess this deep in the siding (0.854): in
                       # the walls' print (inside face down, 0.25 mm first layer, then 0.2) its floor
                       # is the layer line at 4.25, over 3 layers of siding
VENT_BACK_GAP = 0.45   # each louvre stops this far under the next at the back (F6; the barn's code
                       # had 0.1, which closes the gaps on the lower layers at this scale)
VENT_SLATS = 5         # the designer's count

# Alan's standard layout (Nov 3 2026, "go on yoder-storage-barns.com to see standard layout"): the
# site's designer-standards.js, "laid out BY ALAN in the designer itself (copy-this-build codes, Aug
# 2026)". It overrides the designer's stock spots the spec used. Positions are the designer's pos,
# feet from the wall's middle; +x is right, standing in front of the porch looking at the door.
STD_SOURCE = "designer-standards.js on yoder-storage-barns.com, Alan's copy-this-build codes, Aug 2026"
DOOR_X = 1.74 * FT     # +16.574 the door's middle, right of the porch wall's. CONFIRMED (STD_SOURCE,
                       # DOOR_X[10] = 1.74; live 10x20 d36lite F +1.74)

# door: the 36 in 11-Lite door (opening 36 x 73 1/2 in; door widths are rough openings) at DOOR_X in
# the front wall, swinging IN. BARNWRIGHT (items.d36lite, its liteSwap d36in, the 36 in In-Swing
# Door), 36 in wide as the builder draws it (the site's building page says 36 x 72 in, the builder
# 3 x 6.3 ft: CONFIRMED by Alan Nov 3 2026, "Keep builder sizes"). Its 75.6 in and a header don't fit
# under two top plates at Alan's 79 1/2 in wall (75 in of stud), so he was asked, and chose the 73 1/2
# in door under his two flat 2x4s on 72 in kings (Nov 4 2026, "73 1/2 in door, flat boards"; on the
# model's 1.6 mm bottom plate the kings are 71 1/2 in and the studs 74 1/2):
# CONFIRMED. Its leaf is drawn for that height by the designer's rules (door_leaf_plan()), so it is the
# Cabin's door 2.1 in shorter. Hinged on the +x jamb (on the right seen from the porch, next to the
# right side wall), swinging in toward that wall, the knob toward the middle of the wall: the Cabin's
# door, which Alan hinged on the right (Nov 4 2026, "hinges on the right side", the Cabin's question
# 16); the twins share the door. Open question 8; the designer hinges it on the left.
DOOR_OPEN_W = 36 * S   # 28.575
DOOR_OPEN_H = 73.5 * S # 58.341
JAMB = DOOR_OPEN_W / 2
DOOR_X0, DOOR_X1 = DOOR_X - JAMB, DOOR_X + JAMB   # +2.286..+30.861 the opening
HINGE = 1              # the jamb the door hangs on: +1 the +x jamb (Alan's), -1 the -x jamb (the designer's).
                       # The Cabin's door is the same door 2.1 in taller, hung the same way
LATCH_X = DOOR_X - HINGE * JAMB         # 2.286 the latch jamb, with the stop on it
DOOR_R = 1.0           # half the door's thickness; the hinge edge is rounded to this
DOOR_GAP = 0.35        # gap at hinge and latch edges
DOOR_AXIS_U = 1.6      # the hinge pin line, out from the front wall's INSIDE face (F7): the 2.7 pin
                       # holes then reach down only to u 0.25, the top of the first layer, so the
                       # wall's bed face stays whole. ASSUMED
PIN_X = DOOR_X + HINGE * (JAMB - DOOR_R - DOOR_GAP)   # +29.511
DOOR_W = 2 * (JAMB - DOOR_GAP) - DOOR_R # 26.875 pin line to latch edge
DOOR_BOTTOM_GAP = 0.3
DOOR_TOP_GAP = 0.6
DOOR_H = DOOR_OPEN_H - DOOR_BOTTOM_GAP - DOOR_TOP_GAP
PIN_D = 2.0
PIN_HOLE_D = 2.7       # 0.35 mm round the pin: holes print small (Alan, Oct 31 2026)
PIN_BOTTOM_LEN = 1.3   # rests on the bottom of a 1.0 deep hole
PIN_TOP_LEN = 2.0
HOLE_BOTTOM_DEPTH = 1.0
TRENCH_DEPTH = 0.7     # the slot the bottom pin slides in through; 0.3 shallower than the hole
HOLE_TOP_DEPTH = 2.2
STOP_SECTION = [(0.0, 2.45), (0.8, 3.25), (0.8, None), (0.0, None)]   # the door stop on the latch
                       # jamb, outside the door: (into the opening from the jamb face, u), None = WT.
                       # A 45 degree underside from the 2.45 layer line, 0.2 clear of the shut door's
                       # outside face at its latch edge, overlapping it 0.45 (F7)

# windows: the 2x3 window, 2.1 x 2.9 ft (BARNWRIGHT items.w23): ONE in the front wall, left of the
# door, and one in the middle of each long wall
WIN_W = 2.1 * FT       # 20.003
WIN_H = 2.9 * FT       # 27.623
WIN_TOP = WALL_H - PLATE_TOP - HEADER   # 56.753 (71 1/2 in) above the floor: Alan's lofted-wall rule,
                       # the 5 in loft header right under the top plates. ASSUMED (carried over; the designer
                       # puts it 5 in under the wall top, 74.5 in on this wall: open question 3)
FRONT_WIN_X = -2.57 * FT   # -24.479 the front window's middle. CONFIRMED (STD_SOURCE, WIN_X[10] =
                       # -2.57; live w23 F -2.57)
SIDE_WIN_Y = 2 * FT    # 19.05 both long walls' window, at pos 0 on each (CONFIRMED, STD_SOURCE: w23 R 0
                       # and w23 L 0); a long wall's middle is 2 ft behind the building's (BARNWRIGHT
                       # frame.js wallDefs cx = -pd/2)

# the faux loft window on the porch gable, in place of the octagon (Alan: "the octagon gable window
# is a $200 OPTION, not standard"; STD_SOURCE: LBC adds fake F 0). A trim frame with a triangle in
# each inside corner and no glass, the siding showing through; nothing framed behind it (the
# part-gable-frame skill: "trim nailed to the siding, not an opening"). Sizes BARNWRIGHT (live
# catalog fake 2.6 x 1.9 ft; parts/openings/gable-window.js), as the Lofted Barn Garage's
FAUX_W, FAUX_H = 2.6 * FT, 1.9 * FT   # 24.765 x 18.098
FAUX_ZC = ZWT + max(0.62 + 0.95, 0.34 * (ZPK - ZWT) / FT) * FT   # 84.878, 1.57 ft over the wall
                       # top (model/layout.js gableRect). BARNWRIGHT rule, DERIVED with this roof
FAUX_BAR = 0.3 * FT    # 2.858 the frame's width. BARNWRIGHT
FAUX_TRI = min(0.5, 0.55 * 1.0, 0.75 * 0.65) * FT   # 4.643 the corner triangles' legs:
                       # min(0.5, 0.55 x half the inside width, 0.75 x half the inside height). BARNWRIGHT

# loft: a floor of 2x6 joists 16 in apart and a deck, 4 ft deep, on the side walls' top plates,
# one behind the front wall (4 ft from its face) and one at the back. BARNWRIGHT (standard.json
# loft ends F and B, depthFt 4 "assumed: true"; parts/roof-frame.js loftZones; open question 6)
LOFT_DEPTH = 4 * FT
LOFT_JOIST = 5.5 * S
LOFT_DECK = 1.0
LOFT_Z = ZWT - 0.15    # bottom of the loft joists: the top of the side walls
LOFT_CLR = 0.4         # clear of the steep roof sheets, square to them
LOFT_END = 0.4         # gap between a loft and the end wall
FIT = 0.2              # gap round every post, prong and peg (0.2 a side is snug)
LUG_U = 1.8            # a lug under two of the joists at each wall drops into a notch in the top
LUG_D = PLATE_TOP - 0.15 - FIT   # 2.031: the notch runs right through the top plates, so no
                       # sliver of plate is left under it (spec 4.9)
LUG_JOISTS = (0, -1)   # the end joist and the edge joist, the same distance from the loft's middle,
                       # so a loft goes in either way round
FRONT_NOTCH_U = LUG_U + FIT + 0.25   # 2.25: the front loft's end-joist notches run out through the
                       # side walls' front ends, so the plate over each prints held on two sides only
                       # (a corner overhang, not a bridge); one layer more over the lug leaves room for
                       # it to sag (review Nov 3 2026). The edge joist's lug still holds the wall at 0.2.
                       # ASSUMED
NOTCH_FILL = 0.3       # 45 degree fill in the corner end of the back loft's end-joist notches

# skids: 4x6 laid on edge, the inside face 30 in in from the outside wall. ASSUMED (carried over from
# Alan's 10x16 lesson, CONFIRMED there Sep 27 2026; the designer's table puts the centre 30 in in:
# open question 9)
SKID_W = 3.5 * S
SKID_H = 5.5 * S
SKID_X = W / 2 - 28.25 * S # 25.202
SKID_MARK = 0.8        # the front end's two upright corners are cut off this much at 45 degrees
NOTCH = 0.6
NOTCH_CLEAR = 0.6      # 0.3 mm each side of a joist
SKID_PEG_D, SKID_PEG_UP = 2.0, 2.5   # a peg at each end of a skid pushes into the floor

# floor framing: 2x6 joists 16 in apart across the width, the room's from the back end, the porch's
# from the front end joist under the front wall. BARNWRIGHT (construction.json floor)
F_BAND = (YF - 2.0, YF + WT + 2.0)   # the solid band under the front wall, its pockets inside it
DECK_BOARD, DECK_GAP = 5.5 * S, 0.25 * S   # porch deck boards along the length. BARNWRIGHT

# snap joints, no glue: the same as the base models (Alan, Nov 1 2026; F4). Each wall stands on
# top of the floor. The side walls and the back wall have their siding hanging down over the
# floor's edge; the front wall stands on the deck. Under every stud a post drops into a notch (or,
# under the front wall, a closed pocket) in the floor, and a few prongs click into slots in the
# floor. A prong is a springy leg that bends in and out of the wall, with a barb on its foot that
# catches under a ledge at the bottom of the slot, and beside it a stiff stop.
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
MITRE_GAP = 0.1        # relief between mitred ends; at the front corners the gap the glue wicks into
MITRE_BEVEL = 0.6      # a 45 degree bevel along the top of each side wall's mitre at the back
SILL_UP = 0.3          # the door sill's foot stops this far above the floor's underside, inside its
                       # pocket: with the door at +1.74 ft the sill runs over the +x skid, and flush at
                       # z 0 it stood on that skid's front-band notch, so a sill printed a hair long
                       # would lift the front wall off the deck there (review Nov 3 2026). Nothing
                       # needs it lower: the bottom pin's hole reaches ZF - 1.0. ASSUMED (a model detail)
POCKET_ALONG = 0.3     # the front wall's closed pockets: 0.3 along the wall round each post, FIT across
# the prongs: (where along the wall, which way its stop is). Each in a stud bay, between floor
# joists, at least 1.0 from a skid; the stop toward the nearer corner. ASSUMED (spec 4.11). The front
# wall's +x prong moved from 34.125, now under the moved door's sill, to the middle of the floor
# left between the sill's pocket and the corner notch (standard layout, Nov 3 2026). ASSUMED
PRONGS = {"right side": [(76.2, 1), (0.0, 1), (-38.1, -1)],
          "left side": [(76.2, 1), (0.0, 1), (-38.1, -1)],
          "front wall": [(-29.8, -1), (37.1, 1)],
          "back wall": [(-30.1, -1), (35.0, 1)]}

# the corners. At the back the barn's: 45 degree mitres, pulled shut by a band, with a black L
# angle glued into a recess in both walls (Alan, Nov 3 2026, on the barn). At the front the walls
# stand back under the porch, where the designer draws no corner board: the front wall runs through
# to the corner, each side wall butts against its inside face 0.1 off, and the joint is glued and
# hidden in a siding groove (open question 5).
POCKET_D = 0.4         # the recess: 2 layers of the walls' print (siding top at 5.05, floor 4.65)
POCKET_CLR = 0.15      # the recess reaches the angle's reach + this from the corner, and this far
                       # over an angle's top
CORNER_CHAMFER = 1.15  # the walls' outside corner is cut off square to the mitre, this far past
                       # where the recess floors meet
ANGLE_T = 1.05         # each leg of an angle, 5 layers thick as it lies on the bed
ANGLE_P = ANGLE_T - POCKET_D   # 0.65, how far an angle stands out of the siding
ANGLE_REACH = 3.0      # the long-face leg covers this much of the side wall (F5: as wide as scale
                       # trim it would sit on only 1.2 mm of glue land; open question 11). ASSUMED
ANGLE_UP = 0.25 + 17 * 0.2     # 3.65, the end-face leg's width, standing up in the print: 18 layers,
                       # 3.0 of it on the back wall
ANGLE_FILLET = 0.8     # 45 degree fillet in an angle's inside corner (barn, review Nov 3 2026)
ROOF_CLR = 0.2         # the walls' top edges, the angles and the porch frame keep this clear of the
                       # lower roof sheets, square to them
RAKE_CLR = 0.15        # an angle's end-face leg stops this far under the rake board
JOINT_NOTCH = 0.25     # the front corner groove: the side wall's front outer edge notched this
                       # along by GROOVE_D deep, the front wall's end block chamfered GROOVE_D at 45
                       # degrees; with the 0.1 joint they read as one groove about 0.7 wide

# the porch (the Cabin's parts at this wall height). Corner posts BARNWRIGHT (parts/porch.js); the
# one middle post CONFIRMED (STD_SOURCE: "a single porch post left of center -- so the railing runs
# under the window and the entry opens in front of the door"); the held sizes are print sizes on
# layer lines (spec 4.3 to 4.7). ASSUMED (held)
FRAME_H = 2.85         # the porch frame, 14 layers (the designer's band is 0.29 ft, 2.76)
FRAME_Z = ZWT - FRAME_H    # 67.074 its bottom
LIP_W, LIP_H = 1.2, 0.65   # the lip round the inside the ceiling rests on (3 layers)
CEIL_T = 1.05          # the ceiling panel, 5 layers
REAR_D = 1.6           # the rear beam's depth
POST = 3.25            # the 4x4 posts (true 3.24), 16 layers lying flat
POST_XS = [-(W / 2 - 0.28 * FT), -0.3 * FT, W / 2 - 0.28 * FT]   # -44.958, -2.858, +44.958: the
                       # corner posts BARNWRIGHT, the middle one CONFIRMED (STD_SOURCE, POST_X[10] = -0.3;
                       # live ppost F -0.3), at the old middle posts' y and section
POST_Y = -(L / 2 - 0.2 * FT)                                          # -93.345 BARNWRIGHT
TENON_W, TENON_T, TENON_L = 1.6, 1.65, 1.0   # a tenon at each end, flush with the face it prints on
SOCKET_D = 1.25        # the sockets for tenons and pegs, 1.25 deep
TENON_CLR = 0.35       # round every tenon and peg in its socket: holes print small
POST_BODY = FRAME_Z - ZF   # 60.253
GABLE_PEG_X = 30 * S   # the porch gable's two square pegs down into the frame
GPEG_W, GPEG_T, GPEG_L = 1.6, 1.65, 1.5
GPEG_SOCKET = 1.6      # their sockets, from the frame's top
RAIL_IN = 0.2 * FT     # the railings' middle line, this far in from the deck's edge. BARNWRIGHT
RAIL_B0, RAIL_B1 = 0.24 * FT, 0.38 * FT    # bottom rail, above the deck. BARNWRIGHT
BAL, BAL_OC = 0.12 * FT, 0.44 * FT         # 2x2 balusters and their spacing. BARNWRIGHT
RAIL_T0 = 2.56 * FT    # the top rail, filled up to the cap so the cap is carried along its length
CAP0, CAP1 = 2.78 * FT, 2.88 * FT          # the cap, 34.56 in to its top. BARNWRIGHT
RAIL_D, CAP_D = 1.25, 2.85                 # rails and balusters 6 layers deep, the cap 14,
                       # overhanging toward the porch (the designer centres it). ASSUMED
RAIL_PEG = SOCKET_D - 0.05   # 1.2: the end balusters run on into the deck as pegs, 0.05 shorter than
                       # their 1.25 holes are deep (PRINTER-BRAIN, "Let a peg bottom in its hole"), room
                       # for glue. Nothing else of a railing reaches the deck, so pressed right home its
                       # pegs bottom and it stands 0.05 under its drawn height (cap 34.50 in, drawn
                       # 34.56). ASSUMED (review Nov 3 2026: at 1.0 every railing dropped 0.25 to wherever
                       # its glue held it). The Cabin's pegs are 1.25 (make_cabin.py RAIL_PEG = SOCKET_D),
                       # bottomed as drawn; the holes are the same, so the railings still swap
RAIL_POST_GAP = 0.2    # each railing's ends stand this far off the posts (not glued)
SIDE_RAIL_BACK = YF - 0.25 * FT   # the side railings start 0.25 ft in front of the front wall. BARNWRIGHT
                       # (parts/porch.js: the side runs from 0.25 ft in front of F to the corner post)
HOLE_LAND = 0.6        # solid deck kept round every post socket and railing peg hole: the deck-board
                       # grooves stop this far (and 0.05 more) short of them. ASSUMED (spec 8, 6a)


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
    """Polygon (or CrossSection) in two cabin axes (ax0, ax1), extruded d along the third axis h
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


def place(part, cols, origin):
    """part moved by the rotation whose columns are where its X, Y and Z go, then to origin. The
    rotation must be one (det +1), not a mirror."""
    R = np.column_stack([np.array(c, dtype=float) for c in cols])
    assert abs(np.linalg.det(R) - 1) < 1e-9, "not a rotation"
    return part.transform(np.column_stack([R, np.array(origin, dtype=float)]))


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
    """Middle of the steep edge of each gable, where the lower sheets' pegs are."""
    return np.array([side * (W / 2 + KNEE_X) / 2, (ZWT + ZKN) / 2])


def layout(start, end, oc):
    out, k = [], 1
    while start + k * oc < end - 0.01:
        out.append(start + k * oc)
        k += 1
    return out


def stud_marks(length):
    """Stud centres along a wall of this length, measured from the end the layout starts at: 16
    in apart, and a double stud at every 4 ft mark, the mark falling between the touching pair
    (Alan, Sep 28 2026, ASSUMED here: carried over)."""
    out, k = [], 1
    while k * 16 * S < length - 0.01:
        a = k * 16 * S
        out += [a - 0.75 * S, a + 0.75 * S] if k % 3 == 0 else [a]
        k += 1
    return out


SIDE_MARKS = [L / 2 - a for a in stud_marks(L / 2 - YF)]   # y, the side walls' layout from the back corner
END_MARKS = [-W / 2 + a for a in stud_marks(W)]            # x, the end walls' layout from the -x corner


# ---------------------------------------------------------------- body
def joist_ys():
    """The floor joists, 16 in apart: the room's from the back end, the porch's from the front
    wall's band toward the front edge."""
    room = [y for y in (L / 2 - k * 16 * S for k in range(1, 40)) if y > F_BAND[1] + SW]
    porch = [y for y in (YF - k * 16 * S for k in range(1, 10)) if y > -L / 2 + RIM + SW]
    return room + porch


# each wall as (axis it faces along, side), and how far its siding face is from the middle. The long
# walls are named as seen from in front of the porch: both have a window now, so "window side" and
# "plain side" no longer tell them apart (standard layout, Nov 3 2026)
WALL_SIDE = {"right side": (0, 1), "left side": (0, -1), "back wall": (1, 1), "front wall": (1, -1)}
WALL_FACE = {"right side": W / 2, "left side": W / 2, "back wall": L / 2, "front wall": L / 2 - PORCH}
SIDES = ("right side", "left side")
YS = YF + WT + MITRE_GAP   # -51.946 where the side walls start, 0.1 behind the front wall
YJ = YF + WT + MITRE_GAP / 2   # the front joint's plane, in the bottom of a siding groove
WALL_MIDDLE = {"right side": YM, "left side": YM, "back wall": 0.0, "front wall": 0.0}


def wall_box(name, a0, a1, u0, u1, z0, z1):
    """A box on one wall: a along the wall (y for the side walls, x for the end walls), u out
    from its inside face, z up."""
    axis, sign = WALL_SIDE[name]
    half = WALL_FACE[name]
    n0, n1 = sorted([sign * (half - WT + u0), sign * (half - WT + u1)])
    return box(n0, n1, a0, a1, z0, z1) if axis == 0 else box(a0, a1, n0, n1, z0, z1)


def wall_section(name, poly, a0, a1):
    """A polygon in (u out from the wall's inside face, z), from a0 to a1 along the wall."""
    axis, sign = WALL_SIDE[name]
    half = WALL_FACE[name]
    pts = [(sign * (half - WT + u), z) for u, z in poly]
    t = [0.0, 0.0, 0.0]
    t[1 - axis] = a0
    return prism(pts, axis, 2, 1 - axis, a1 - a0).translate(t)


def openings(name):
    """(a0, a1, z0, z1, kind) of every opening in a wall, a along it."""
    def win(c):
        return (c - WIN_W / 2, c + WIN_W / 2, ZF + WIN_TOP - WIN_H, ZF + WIN_TOP, "window")
    if name == "front wall":
        return [win(FRONT_WIN_X), (DOOR_X0, DOOR_X1, ZF, ZF + DOOR_OPEN_H, "door")]
    if name in SIDES:
        return [win(SIDE_WIN_Y)]
    return []


def merge_spans(spans):
    out = []
    for a0, a1 in sorted(spans):
        if out and a0 <= out[-1][1] + 1e-6:
            out[-1] = (out[-1][0], max(out[-1][1], a1))
        else:
            out.append((a0, a1))
    return out


def framing_layout(name):
    """The studs, plates, headers and window plates of one wall as boxes (a0, a1, u0, u1, z0,
    z1), and the layout marks that land on other framing. Alan's doorway rules (CONFIRMED shop
    terms, BUILDING-TERMS.md): beside each opening a full-height stud and, inside it, the king
    stud, the SHORT support under the header; the header bears 1 1/2 in on each king; studs on
    the layout marks fill above the header to the top plate. Over the door his two flat 2x4s,
    over a window his 5 in loft header right under the top plates, and under a window the flat
    window plate on studs that keep the 16 in layout (carried over, ASSUMED). A layout mark whose
    stud would overlap other framing is dropped and the framing it hits stands there (the
    shed-measurements skill: an unresolved collision needs a layout decision, not a hidden shift);
    returned as (wall, mark in inches from the wall's middle, what it hit, overlap mm). Marks
    inside an opening become cripples or window-plate studs."""
    zb, zt = ZF + PLATE_BOT, ZWT - PLATE_TOP
    out, members = [], []
    if name in SIDES:
        lo, hi, marks = YS, L / 2 - WT, SIDE_MARKS
        members += [(YS, YS + SW, "the front end stud"), (hi - SW, hi, "the back end stud")]
        out += [(YS, YS + SW, 0, SD, 0, ZWT), (hi - SW, hi, 0, SD, zb, zt)]
    elif name == "back wall":
        lo, hi, marks = -(W / 2 - TS), W / 2 - TS, END_MARKS
        xe = W / 2 - WT
        members += [(-xe, -xe + SW, "the -x end stud"), (xe - SW, xe, "the +x end stud")]
        out += [(-xe, -xe + SW, 0, SD, zb, zt), (xe - SW, xe, 0, SD, zb, zt)]
    else:
        lo, hi, marks = -(W / 2 - WT), W / 2 - WT, END_MARKS
        members += [(-W / 2, lo, "the -x end block"), (hi, W / 2, "the +x end block")]
    ops = openings(name)
    x = lo                                  # the bottom plate, cut out across a doorway (the sill is under it)
    for a0, a1 in sorted((o[0], o[1]) for o in ops if o[4] == "door"):
        out.append((x, a0, 0, SD, ZF, zb))
        x = a1
    out += [(x, hi, 0, SD, ZF, zb), (lo, hi, 0, SD, zt, ZWT)]            # and the top plates
    for a0, a1, z0, z1, kind in ops:
        label = "door's" if kind == "door" else "window's"
        sides = []
        for s, edge in ((-1, a0), (1, a1)):
            full = sorted([edge + s * SW, edge + 2 * s * SW])
            if any(full[1] > m0 + 1e-6 and full[0] < m1 - 1e-6 for m0, m1, _ in members if "end" in _):
                continue                                                  # the end block is that jamb
            sides.append(s)
            king = sorted([edge, edge + s * SW])
            out += [(full[0], full[1], 0, SD, zb, zt), (king[0], king[1], 0, SD, zb, z1)]
            members += [(full[0], full[1], f"the {label} {'+' if s > 0 else '-'}x full stud"
                         if name == "front wall" else f"the {label} full stud"),
                        (king[0], king[1], f"the {label} king stud")]
        h0 = a0 - SW if -1 in sides else max(a0, lo)
        h1 = a1 + SW if 1 in sides else min(a1, hi)
        top = z1 + (FLAT_HEADER if kind == "door" else HEADER)
        out.append((h0, h1, 0, SD, z1, min(top, zt)))                      # header
        if kind == "window":
            out.append((max(a0, lo), min(a1, hi), 0, SD, z0 - SW, z0))      # window plate
    dropped = []
    for a in marks:
        s0, s1 = a - SW / 2, a + SW / 2
        inside = [o for o in ops if s0 >= o[0] - 1e-6 and s1 <= o[1] + 1e-6]
        if inside:
            a0, a1, z0, z1, kind = inside[0]
            top = z1 + (FLAT_HEADER if kind == "door" else HEADER)
            if zt - top > 0.05:
                out.append((s0, s1, 0, SD, top, zt))                       # cripple over the header
            if kind == "window":
                out.append((s0, s1, 0, SD, zb, z0 - SW))                   # under the window plate
            continue
        hits = [(min(s1, m1) - max(s0, m0), what) for m0, m1, what in members if min(s1, m1) - max(s0, m0) > 1e-6]
        if hits:
            ov, what = max(hits)
            dropped.append((name, round((a - WALL_MIDDLE[name]) / S, 2), what, round(ov, 2)))
            continue
        out.append((s0, s1, 0, SD, zb, zt))
    # (Over the door no hinge block now: on the 82.8 in wall the bay over the flat header was filled from the
    # hinge-side full stud to 0.6 past the top pin's hole, which went 2.2 into the 2.38 header and left a 0.18 web
    # under the open bay. At Alan's 79 1/2 in wall the header is right under the top plates (Nov 4 2026), so the
    # hole's 0.18 of header has the plates on it and the wall is solid over it up to the top.)
    merged = []                     # a double's two studs touch: one box, so no face is left between them
    for b in sorted(out, key=lambda b: (b[2:], b[0])):
        if merged and merged[-1][2:] == b[2:] and b[0] <= merged[-1][1] + 1e-6:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b[1])) + b[2:]
        else:
            merged.append(b)
    return merged, dropped


DROPPED_MARKS = [d for n in WALL_SIDE for d in framing_layout(n)[1]]


def wall_framing(name):
    return [wall_box(name, *b) for b in framing_layout(name)[0]]


def sill_span():
    """(start, end) of the front wall's door sill along x: the doorway's framing, a king and a full
    stud each side of the opening."""
    return DOOR_X0 - 2 * SW, DOOR_X1 + 2 * SW


def post_spans(name):
    """(start, end) along the wall of each post under it, from z = 0 up to the bottom plate: one
    under every layout mark (a double's width under a double), even where the mark's stud was
    dropped, since the bottom plate runs on under it. The side walls also have one under their
    front end stud. The front wall has the door sill under the doorway's framing instead, none
    within 1.0 of an end block (a pocket there would leave a sliver of floor before the corner
    notch), and its end blocks go down into the corner notches."""
    if name in SIDES:
        spans = [(a - SW / 2, a + SW / 2) for a in SIDE_MARKS] + [(YS, YS + SW)]
    elif name == "back wall":
        xe = W / 2 - WT - SW / 2
        spans = [(a - SW / 2, a + SW / 2) for a in END_MARKS + [-xe, xe]]
    else:
        d0, d1 = sill_span()
        spans = [(d0, d1)]
        for a in END_MARKS:
            s0, s1 = a - SW / 2, a + SW / 2
            if s1 > d0 and s0 < d1:
                continue
            if min(abs((W / 2 - WT) - s1), abs(s0 + (W / 2 - WT))) < 1.0:
                continue
            spans.append((s0, s1))
    return merge_spans(spans)


def prong_spans(ac, sd):
    """(leg, stop): where the leg and the stop of the prong at ac are along the wall; the stop
    is on side sd of the leg."""
    leg = (ac - PRONG_W / 2, ac + PRONG_W / 2)
    stop = sorted([ac + sd * (PRONG_W / 2 + STOP_GAP), ac + sd * (PRONG_W / 2 + STOP_GAP + STOP_W)])
    return leg, tuple(stop)


def prong(name, ac, sd):
    """The prong at ac along a wall. The leg hangs from the bottom plate BARB off the wall's
    inside face; in the print it bridges from the plate to its barb, which stands on the bed.
    The barb's flat top catches under the ledge; below it a straight face and a 45 degree
    lead-in that pushes the leg out as it goes down the slot."""
    (a0, a1), (b0, b1) = prong_spans(ac, sd)
    zc = LEDGE_Z - FIT                                  # flat top of the barb, under the ledge
    zl = zc - BARB_LAND - BARB                          # foot of the lead-in
    barb = [(BARB + 0.1, zc), (0.25, zc), (0.25, zc - BARB_RELIEF), (0, zc - BARB_RELIEF),
            (0, zc - BARB_LAND), (BARB, zl), (BARB + 0.1, zl)]
    return [wall_box(name, a0, a1, BARB, BARB + PRONG_T, zl - 0.05, LEG_ROOT + 0.01),
            wall_section(name, barb, a0, a1),
            wall_box(name, b0, b1, 0, STOP_U, ZF - STOP_H, ZF + 0.3)]


def prong_relief(name, ac, sd):
    """The slot in the bottom plate round the top of the prong's leg, 0.2 all round, so the
    leg bends from LEG_ROOT. It is inside the plate: its inside face is whole."""
    (a0, a1), _ = prong_spans(ac, sd)
    return (wall_box(name, a0 - 0.2, a1 + 0.2, BARB - 0.2, BARB + PRONG_T + 0.2, ZF - 0.5, LEG_ROOT)
            - wall_box(name, a0, a1, BARB, BARB + PRONG_T, ZF - 1, LEG_ROOT + 1))


def under_floor(name):
    """What a wall has below the top of the floor besides its siding: the posts and prongs. The
    front wall has no skirt, so its posts and its door sill are the wall's whole thickness; the
    sill's top is the threshold, flush with the deck, and its foot SILL_UP above the floor's
    underside, clear of the skid it crosses."""
    if name == "front wall":
        sill = sill_span()
        parts = [wall_box(name, a0, a1, 0, WT, SILL_UP if (a0, a1) == sill else 0, ZF + (0 if (a0, a1) == sill else 0.3))
                 for a0, a1 in post_spans(name)]
    else:
        parts = [wall_box(name, a0, a1, 0, SD + EMBED, 0, ZF + 0.3) for a0, a1 in post_spans(name)]
    for ac, sd in PRONGS[name]:
        parts += prong(name, ac, sd)
    return parts


def post_tenons():
    """(x0, x1, y0, y1) of each porch post's tenon: 1.6 wide, 1.65 thick, flush with the post's
    face toward the outside of the building in x."""
    out = []
    for xc in POST_XS:
        s = 1 if xc > 0 else -1
        xo = xc + s * POST / 2
        x0, x1 = sorted([xo, xo - s * TENON_T])
        out.append((x0, x1, POST_Y - TENON_W / 2, POST_Y + TENON_W / 2))
    return out


def post_sockets(z_face, up):
    """The sockets the posts' tenons go in, TENON_CLR bigger all round, SOCKET_D deep: down from
    the deck's top (up=False) or up from the porch frame's bottom (up=True)."""
    c = TENON_CLR
    z0, z1 = (z_face - 1, z_face + SOCKET_D) if up else (z_face - SOCKET_D, z_face + 1)
    return [box(x0 - c, x1 + c, y0 - c, y1 + c, z0, z1) for x0, x1, y0, y1 in post_tenons()]


def floor_cuts():
    """The notches, pockets, slots and holes in the floor: a notch round each post of the side
    walls and the back wall; a closed pocket round each post and the door sill of the front wall;
    a slot for each prong; the corners where the back corner posts, the front wall's end blocks
    and the side walls' front end posts go down; a hole in each end band for a skid peg; the
    sockets for the porch posts and the holes for the railings' pegs."""
    c = FIT
    cuts = []
    for name in WALL_SIDE:
        for a0, a1 in post_spans(name):
            if name == "front wall":
                cuts.append(wall_box(name, a0 - POCKET_ALONG, a1 + POCKET_ALONG, -c, WT + c, -1, ZF + 1))
            else:
                cuts.append(wall_box(name, a0 - c, a1 + c, -c, WT + 1, -1, ZF + 1))
        for ac, sd in PRONGS[name]:
            (a0, a1), (b0, b1) = prong_spans(ac, sd)
            cuts += [wall_box(name, a0 - c, a1 + c, BARB - c, SLOT_U, -1, ZF + 1),
                     wall_box(name, a0 - c, a1 + c, -c, BARB - c + 0.01, -1, LEDGE_Z),
                     wall_box(name, b0 - c, b1 + c, -c, SLOT_U, -1, ZF + 1)]
    for sx in (1, -1):
        for dx, dy in ((0, SW), (SW, 0)):                  # back: side wall's corner post, back wall's end stud
            xa, xb = sorted([sx * (W / 2 - WT - dx - c), sx * W])
            cuts.append(box(xa, xb, L / 2 - WT - dy - c, L, -1, ZF + 1))
        xa, xb = sorted([sx * (W / 2 - WT - c), sx * W])  # front: the end block and the side wall's end post
        cuts.append(box(xa, xb, YF - c, YS + SW + c, -1, ZF + 1))
        for y in (L / 2 - TS - FLOOR_CLR - RIM / 2, -L / 2 + RIM / 2):
            cuts.append(cyl_z(sx * SKID_X, y, -1, SKID_PEG_UP + 0.3, SKID_PEG_D + 2 * c))
    return cuts + post_sockets(ZF, False) + railing_holes()


def floor(grooves=True):
    """Floor frame, floor sheets and the porch deck in one. The side walls and the back wall stand
    on it with their siding hanging down over its edge, FLOOR_CLR clear of it; the front wall
    stands on it 4 ft back from the front edge, its posts in closed pockets. It prints upside down,
    floor face on the bed. grooves=False leaves out the sheet seams and deck-board grooves (for the
    checker)."""
    xr, yb = W / 2 - TS - FLOOR_CLR, L / 2 - TS - FLOOR_CLR
    yp = YF - FIT                                     # where the room part meets the porch deck
    f = union([box(-xr, xr, yp, yb, 0, ZF), box(-W / 2, W / 2, -L / 2, yp + 1, 0, ZF)])
    cuts = []
    js = sorted(joist_ys())
    room = [F_BAND[1]] + [e for j in js if j > YF for e in (j - SW / 2, j + SW / 2)] + [yb - RIM]
    for a, b in zip(room[0::2], room[1::2]):
        cuts.append(box(-xr + RIM, xr - RIM, a, b, -1, ZF - DECK))
    porch = [-L / 2 + RIM] + [e for j in js if j < YF for e in (j - SW / 2, j + SW / 2)] + [F_BAND[0]]
    for a, b in zip(porch[0::2], porch[1::2]):
        cuts.append(box(-W / 2 + RIM, W / 2 - RIM, a, b, -1, ZF - DECK))
    if grooves:
        cuts += floor_grooves()
    return f - union(cuts + floor_cuts())


def floor_grooves():
    """The floor's top face: the room's 4x8 sheet seams, rows of 4, 4 and 2 ft across from the -x
    side (Alan's flooring layout, shed-measurements skill; the datum ASSUMED), the outer rows'
    seam across at the middle of the room and the middle row's staggered 4 ft, all on joists; and
    the porch deck's 5 1/2 in boards along the length with 1/4 in gaps (BARNWRIGHT). Each groove
    is 0.4 wide and 0.25 deep, the floor's first layer as it prints. A deck groove that passes
    within HOLE_LAND of a post socket or railing peg hole stops HOLE_LAND + 0.05 short of it on
    both sides (run on, three of them left a strip of deck 0.16 to 0.56 wide beside a hole, and
    the 0.16 and 0.27 ones are under a line wide), and one that would leave a stub under 0.5 at
    the deck's front edge stops at the edge."""
    zz = (ZF - 0.25, ZF + 0.01)
    g = [box(x0, x1, y0, y1, *zz) for x0, x1, y0, y1 in floor_seams()]
    holes = [h.bounding_box() for h in railing_holes() + post_sockets(ZF, False)]
    k = 1
    while -W / 2 + k * (DECK_BOARD + DECK_GAP) < W / 2 - 1:
        x = -W / 2 + k * (DECK_BOARD + DECK_GAP) - DECK_GAP / 2
        g0, g1 = x - 0.2, x + 0.2
        ya, yb = -L / 2 - 1, YF - FIT
        stops = sorted((h[1] - HOLE_LAND - 0.05, h[4] + HOLE_LAND + 0.05) for h in holes
                       if g1 > h[0] - HOLE_LAND and g0 < h[3] + HOLE_LAND)
        y = ya
        for s0, s1 in stops:
            if s0 - y > 0.5 + (-L / 2 - ya if y == ya else 0):
                g.append(box(g0, g1, y, s0, *zz))
            y = max(y, s1)
        g.append(box(g0, g1, y, yb, *zz))
        k += 1
    return g


def floor_seams():
    """The room's 4x8 sheet seams (floor_grooves), (x0, x1, y0, y1) each, 0.4 wide."""
    xi, y0, y1 = W / 2 - WT, YF + WT, L / 2 - WT
    xa, xb = -W / 2 + 4 * FT, -W / 2 + 8 * FT
    out = [(x - 0.2, x + 0.2, y0, y1) for x in (xa, xb)]
    for x0, x1, ys in ((-xi, xa, [YM]), (xb, xi, [YM]), (xa, xb, [YM - 4 * FT, YM + 4 * FT])):
        out += [(x0, x1, y - 0.2, y + 0.2) for y in ys]
    return out


FLOOR_TO_PRINT = [[1, 0, 0], [0, -1, 0], [0, 0, -1]]     # upside down


def window_unit(name, ac):
    """Double-hung 2x3 window inside its opening: two sashes and their muntins, no glass, so you
    can see in (Alan, Oct 31 2026). The sash frames reach 0.2 mm into the jambs so they join the
    wall; their backs are flush with the framing, so the wall prints flat."""
    a0, a1 = ac - WIN_W / 2, ac + WIN_W / 2
    z0, z1 = ZF + WIN_TOP - WIN_H, ZF + WIN_TOP
    zm = (z0 + z1) / 2
    ring, k, mw = 1.2, 0.2, 0.8
    parts = []
    for (za, zb, uf) in ((zm, z1, WT - 0.45), (z0, zm, WT - 0.15)):    # upper sash sits back
        lo = za - (k if za == z0 else 0)
        hi = zb + (k if zb == z1 else 0)
        parts += [wall_box(name, a0 - k, a1 + k, 0, uf, lo, za + ring), wall_box(name, a0 - k, a1 + k, 0, uf, zb - ring, hi),
                  wall_box(name, a0 - k, a0 + ring, 0, uf, lo, hi), wall_box(name, a1 - ring, a1 + k, 0, uf, lo, hi),
                  wall_box(name, ac - mw / 2, ac + mw / 2, 0, uf - 0.15, za, zb),                  # muntins
                  wall_box(name, a0, a1, 0, uf - 0.15, (za + zb) / 2 - mw / 2, (za + zb) / 2 + mw / 2)]
    return parts


def knee_inner():
    """The inside corner of the end truss's chords at the knee: where the collar tie's top is."""
    k = np.array([KNEE_X, ZKN])
    dl = unit((W / 2 - KNEE_X, -LOWER_RISE))
    du = unit((-KNEE_X, UPPER_RISE))
    half = math.acos(float(dl @ du)) / 2
    return k + CHORD / math.sin(half) * unit(dl + du)


COLLAR_TOP = float(knee_inner()[1])
COLLAR_MID = COLLAR_TOP - COLLAR_H / 2   # the collar tie's middle: each gable's bridge modifiers change direction
                                         # here, across the studs under it, up the gable over it (ACROSS_STUDS)


def gable_cs():
    return m3.CrossSection([GABLE])


def gable_parts(side):
    """The framing of a gable above the wall plates, as named parts (the checker looks at them
    before they are joined): side +1 the back wall, -1 the porch gable. The 2x6 gable board on the
    upper plate (on the porch gable, on the porch frame), 1 in short of each end; the end truss's
    four chords one 2x4 deep under the roof line; the collar tie across the knees, the king post
    over it, gable studs 24 in apart standing on the gable board; and on the back wall only the
    gable backing 11 in over the plate. The porch gable has the faux loft window, trim nailed to the
    siding with nothing framed behind it, and no backing ("A fake window also omits backing":
    part-gable-frame skill), so its framing is the back wall's without the backing (the octagon's
    window box went with the octagon, standard layout Nov 3 2026). Everything runs the full stud
    depth, so each wall prints lying flat on it."""
    yi, yo = sorted([side * (L / 2 - WT), side * (L / 2 - TS)])

    def gb(x0, x1, z0, z1):
        return box(x0, x1, yi, yo, z0, z1)
    p = {}
    g = W / 2 - 1 * S
    p["gable board"] = gb(-g, g, ZWT, ZWT + GABLE_BOARD)
    cs = gable_cs()
    band = (cs - cs.offset(-CHORD, m3.JoinType.Miter)) ^ m3.CrossSection.square([2 * W, 400]).translate([-W, ZWT])
    p["chords"] = prism_xz(band, yi - (0.2 if side < 0 else 0), yo + (0.2 if side > 0 else 0))
    sw = GABLE_STUD_W
    if side > 0:
        p["backing"] = gb(-W / 2, W / 2, ZWT + BACKING_Z, ZWT + BACKING_Z + BACKING_H)
    p["collar"] = gb(-W / 2, W / 2, COLLAR_TOP - COLLAR_H, COLLAR_TOP)
    p["gable studs"] = union([gb(xc - sw / 2, xc + sw / 2, ZWT + GABLE_BOARD, COLLAR_TOP - COLLAR_H)
                              for xc in GABLE_STUD_XS])
    p["king post"] = gb(-KING_W / 2, KING_W / 2, COLLAR_TOP, ZPK)
    shape = prism_xz(GABLE, -L, L)
    return {k: v ^ shape for k, v in p.items()}


def gable_vent(side):
    """Louvred vent centred under the ridge, 0.92 ft below it, 1.12 x 0.76 ft (BARNWRIGHT,
    parts/gable-vent.js), in the siding colour and none of it out past the siding (Alan, Nov 3
    2026), so the walls change colour only once. Returns (frame, cuts, slats): the frame is flush
    with the siding, filling its grooves, with a groove round it; inside the frame the louvre
    field is recessed to VENT_FLOOR, and the slats stand in it, wedges that narrow from the recess
    floor up to their front edges at the siding face, so nothing overhangs in the print. Each
    stops VENT_BACK_GAP under the next at the back, and the top one that far under the frame. The
    bottom one stands on the frame, as on the Cabin (make_cabin.py): the barn's code lifted every
    slat 0.25 off the frame, which left a slot 0.25 wide under the bottom slat and 0.2 to 0.4 over
    the top one, under a line wide, so it closed up or printed ragged (audit Nov 3 2026)."""
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
    inner_h = vh - 2 * fr
    slats = []
    for i in range(VENT_SLATS):
        zb = z0 + fr + inner_h * i / VENT_SLATS
        zt = zb + inner_h / VENT_SLATS - VENT_BACK_GAP
        poly = [(yf + side * (VENT_FLOOR - 0.05), zb), (yf, zb), (yf, zb + 0.4), (yf + side * (VENT_FLOOR - 0.05), zt)]
        slats.append(prism(poly, 1, 2, 0, x1 - x0 - 2 * fr).translate([x0 + fr, 0, 0]))
    return frame, cuts, slats


def rake_board(side):
    """The rake board round a gable under the roof edge (filament 2)."""
    g = gable_cs()
    above = m3.CrossSection.square([4 * W, 400]).translate([-2 * W, ZWT])
    rake = (g.offset(-0.1, m3.JoinType.Miter) - g.offset(-(0.1 + RAKE_W), m3.JoinType.Miter)) ^ above
    ya, yb = sorted([side * (L / 2 - EMBED), side * (L / 2 + PROUD)])
    return prism_xz(rake, ya, yb)


def casings(name):
    """The door and window casings on a wall: 1x4 boards (TRIM wide) on all four sides of a
    window, the two sides and the head of the door, with a continuous head joint and no stacked
    porch band (Alan's cabin correction, Oct 12 2026), plain, no head flare or sill nose (CONFIRMED
    for the shed and barn models, Oct 31 2026; ASSUMED here)."""
    p = []
    for a0, a1, z0, z1, kind in openings(name):
        def b(c0, c1, d0, d1):
            return wall_box(name, c0, c1, WT - EMBED, WT + PROUD, d0, d1)
        p += [b(a0 - TRIM, a0, z0 - (TRIM if kind == "window" else 0), z1 + TRIM),
              b(a1, a1 + TRIM, z0 - (TRIM if kind == "window" else 0), z1 + TRIM),
              b(a0 - TRIM, a1 + TRIM, z1, z1 + TRIM)]
        if kind == "window":
            p.append(b(a0 - TRIM, a1 + TRIM, z0 - TRIM, z0))
    return p


def wall_trims():
    """The walls' trim: the back wall's gable band at the loft line and its rake board, the
    front wall's door and window casings, each long wall's window casing (raised so they can be
    painted, filament 2). The back corners have no boards printed on the walls: the corner angles
    are separate (corner_angle(), Alan, Nov 3 2026, on the barn)."""
    ya, yb = L / 2 - EMBED, L / 2 + PROUD
    p = [box(-W / 2, W / 2, ya, yb, BAND_Z, BAND_Z + TRIM) ^ prism_xz(GABLE, -L, L), rake_board(1)]
    return p + casings("front wall") + casings("right side") + casings("left side")


def faux_window():
    """The faux loft window on the porch gable, centred on it: a frame FAUX_BAR wide and a triangle
    in each inside corner (FAUX_TRI legs along the inside edges), EMBED into the siding and PROUD
    out of it, in the trim colour; no glass and no opening, the siding shows through it (the
    designer's faux-loft draw, parts/openings/gable-window.js; drawn as the Lofted Barn Garage's)."""
    ya, yb = -L / 2 - PROUD, -L / 2 + EMBED
    x0, x1 = -FAUX_W / 2, FAUX_W / 2
    z0, z1 = FAUX_ZC - FAUX_H / 2, FAUX_ZC + FAUX_H / 2
    b, t, e = FAUX_BAR, FAUX_TRI, 0.1                       # e: into the bars, so each triangle joins them
    p = [box(x0, x1, ya, yb, z0, z0 + b), box(x0, x1, ya, yb, z1 - b, z1),
         box(x0, x0 + b, ya, yb, z0, z1), box(x1 - b, x1, ya, yb, z0, z1)]
    for cx, cz, sx, sz in ((x0 + b, z0 + b, 1, 1), (x1 - b, z0 + b, -1, 1), (x0 + b, z1 - b, 1, -1), (x1 - b, z1 - b, -1, -1)):
        tri = [(cx - sx * e, cz - sz * e), (cx + sx * t, cz - sz * e), (cx + sx * t, cz), (cx, cz + sz * t),
               (cx - sx * e, cz + sz * t)]
        p.append(prism_xz(tri, ya, yb))
    return p


LINE_W = 0.42          # one printed line: a slot or strip narrower than this doesn't print cleanly


def faux_groove_fills():
    """Where a siding groove runs along the edge of one of the faux window's side bars, half under
    the bar, the half left showing beside it is a slot narrower than a line (with the window
    centred, its inner edges fall on the grooves at +-12 in: a 0.25 slot each side, review Nov 3
    2026). Each such strip is filled flush with the siding over the window's height, so the bar
    sits on flat siding there; the grooves wholly inside the frame stay. Siding colour (inside the
    outline)."""
    out = []
    z0, z1 = FAUX_ZC - FAUX_H / 2, FAUX_ZC + FAUX_H / 2
    for sx in (1, -1):
        b0, b1 = sorted([sx * (FAUX_W / 2 - FAUX_BAR), sx * FAUX_W / 2])     # the side bar's span in x
        for x in layout(-W / 2, W / 2, GROOVE_OC):
            g0, g1 = x - GROOVE_W / 2, x + GROOVE_W / 2
            for a0, a1 in ((g0, min(g1, b0)), (max(g0, b1), g1)):            # what shows each side of the bar
                if g0 < b1 and g1 > b0 and 1e-6 < a1 - a0 < LINE_W:
                    out.append(box(a0 - 0.01, a1 + 0.01, -L / 2, -L / 2 + GROOVE_D + 0.01, z0, z1))
    return out


def porch_gable_trims():
    """The porch gable's rake board and the faux loft window (no gable band: the designer draws
    none on a porch-F front)."""
    return [rake_board(-1)] + faux_window()


def trims():
    return wall_trims() + porch_gable_trims()


def eave_line(u):
    """Height of the line ROOF_CLR under the steep lower roof sheets, square to them, u mm out
    from the side walls' siding face (in from it where u < 0). The lower sheets reach END_OH past
    each gable, so it holds over both faces of each corner."""
    return ZWT - u * LOW_M - ROOF_CLR * math.sqrt(1 + LOW_M ** 2)


def eave_prism(sx, y0, y1):
    """Everything above eave_line() on side sx, from W/2 - WT - 1 out, from y0 to y1."""
    a0, a1 = W / 2 - WT - 1, W / 2 + 12
    poly = [(a0, eave_line(a0 - W / 2)), (a1, eave_line(a1 - W / 2)), (a1, 400), (a0, 400)]
    if sx < 0:
        poly = [(-x, z) for (x, z) in reversed(poly)]
    return prism_xz(poly, y0, y1)


def roof_clearance():
    """What comes out of the walls for the roof: the side walls and the front wall stop 0.15
    under the wall top, so the roof bears on the gables only, and everything at or outside the
    side walls keeps ROOF_CLR clear of the steep lower sheets, square to them (the siding's top
    edge, the front wall's end blocks, the back wall's corners). The corner angles keep to the
    same line (corner_top()), and the porch frame too (porch_frame_clearance())."""
    out = []
    for sx in (1, -1):
        above = eave_prism(sx, -L, L)
        xa, xb = sorted([sx * W / 2, sx * (W / 2 + 12)])
        out.append(above ^ box(xa, xb, -L, L, -1, 400))                   # outside the wall plane
        xa, xb = sorted([sx * (W / 2 - WT - 0.01), sx * (W / 2 + 12)])
        out.append(above ^ box(xa, xb, -L, L, -1, ZWT))                   # the walls' top outer edge
        xa, xb = sorted([sx * (W / 2 - WT - 0.01), sx * (W / 2 + 1)])
        out.append(box(xa, xb, YF + WT, L / 2 - WT, ZWT - 0.15, 400))      # the side walls' top
        ya, yb = L / 2 - WT, L / 2 + 1                                     # and their back corners,
        out.append(box(xa, xb, ya, yb, ZWT - 0.15, ZWT + 0.01) ^ mitred(0, sx))   # under the back wall's top
    out.append(box(-W / 2 - 1, W / 2 + 1, YF - 2, YF + WT, ZWT - 0.15, 400))   # the front wall's top
    return out


def loft_joist_ys():
    """The back loft's joists, from the back wall in: one against its framing, then 16 in apart,
    and one on the loft's edge."""
    first = L / 2 - WT - LOFT_END - SW / 2
    edge = L / 2 - LOFT_DEPTH + SW / 2
    ys = [first]
    while ys[-1] - 16 * S > edge + SW:
        ys.append(ys[-1] - 16 * S)
    return ys + [edge]


def loft_y(y, sy):
    """y at the back loft (sy=1) moved to the front loft (sy=-1): mirrored about the room's middle."""
    return y if sy > 0 else 2 * YM - y


def loft_half_width():
    """How far out from the middle the loft reaches: LOFT_CLR clear of the steep roof sheets,
    square to them, at the top of its deck."""
    top = LOFT_Z + LOFT_JOIST + LOFT_DECK - ZWT
    return W / 2 - (top + LOFT_CLR * math.sqrt(1 + LOW_M ** 2)) / LOW_M


def loft_notches():
    """The notches in the side walls' top plates the loft lugs drop into: FIT round the lug, from
    the walls' top down to the plates' underside exactly. The front loft's end joist would leave
    0.1 of plate before the side walls' front end, so its notches run out through the end face,
    and are FRONT_NOTCH_U deep (a layer more) for the plate over them to sag."""
    out = []
    for sy in (1, -1):
        for i in LUG_JOISTS:
            y = loft_y(loft_joist_ys()[i], sy)
            y0, y1 = y - SW / 2 - FIT, y + SW / 2 + FIT
            u_out = LUG_U + FIT
            if sy < 0 and i == 0:
                y0 = YF + WT + 0.01
                u_out = FRONT_NOTCH_U
            for sx in (1, -1):
                xa, xb = sorted([sx * (W / 2 - WT - 1), sx * (W / 2 - WT + u_out)])
                out.append(box(xa, xb, y0, y1, LOFT_Z - LUG_D - FIT, ZWT + 1))
    return out


def notch_fills():
    """A 45 degree fill, NOTCH_FILL each way, in the corner end of the notch for the back loft's
    end joist, along the side wall's inside face (the barn's, at the mitred end): the top plate
    runs on past that notch to the mitre, and where it starts on the bed it was a sliver Flash
    Studio warned about as a floating region (Nov 3 2026); the fill makes it wide enough."""
    out = []
    y_end = loft_joist_ys()[0] + SW / 2 + FIT
    z0 = LOFT_Z - LUG_D - FIT - 0.01
    for sx in (1, -1):
        xi = sx * (W / 2 - WT)
        tri = [(xi, y_end), (xi, y_end - NOTCH_FILL), (xi + sx * NOTCH_FILL, y_end)]
        out.append(prism(tri, 0, 1, 2, ZWT - 0.15 - z0).translate([0, 0, z0]))
    return out


def loft(sy=1):
    """One loft, at the back (sy=1) or behind the front wall (sy=-1): the deck on its joists, which
    rest on the side walls' top plates, with a lug under two of the joists at each wall that drops
    into a notch in the plates, so it can't slide. The two are the same part."""
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
    return f if sy > 0 else f.mirror([0, 1, 0]).translate([0, 2 * YM, 0])


LOFT_TO_PRINT = [[1, 0, 0], [0, -1, 0], [0, 0, -1]]     # upside down, deck on the bed


def roof_pegs(sy):
    """The pegs on a gable the roof sheets sit on: a peg standing straight up halfway up each
    slope, PEG_UP proud of the roof line, square to it; sy +1 the back wall, -1 the porch gable."""
    pegs = []
    for sx in (1, -1):
        nu, ou = under_seg("upper", sx, PEG_UP)
        nl, ol = under_seg("lower", sx, PEG_UP)
        m = lower_mid(sx)
        x = sx * PEG_X
        pegs.append(cyl_z(x, sy * PEG_Y, zline(x) - 3, zline(x) + 3, PEG_D).trim_by_plane(nu, ou))
        pegs.append(cyl_z(m[0], sy * PEG_Y, m[1] - 4, m[1] + 8, PEG_D).trim_by_plane(nl, ol))
    return pegs


def front_joint_cuts():
    """The front corners' joint hidden in a siding groove: each side wall's front outer edge
    notched JOINT_NOTCH along by GROOVE_D deep, its full height, and the front wall's end block
    chamfered GROOVE_D at 45 degrees along its back outer edge (a square notch there would hang
    0.35 over the first layer in the front wall's print)."""
    out = []
    for sx in (1, -1):
        xa, xb = sorted([sx * (W / 2 - GROOVE_D), sx * (W / 2 + 1)])
        out.append(box(xa, xb, YF + WT + 0.01, YS + JOINT_NOTCH, -1, ZWT + 1))
        xo, yo, d = sx * W / 2, YF + WT, GROOVE_D
        poly = [(xo - sx * d, yo + 0.05), (xo + sx, yo + 0.05), (xo + sx, yo - d - 1), (xo - sx * d, yo)]
        out.append(prism(poly, 0, 1, 2, ZWT + 2).translate([0, 0, -1]))
    return out


def door_stop():
    """The stop on the latch jamb (LATCH_X, the opening on its HINGE side), outside the in-swing door,
    the full opening height (F7)."""
    pts = [(-0.05, 2.45), (0.0, 2.45)] + [(d, WT if u is None else u) for d, u in STOP_SECTION[1:]] + [(-0.05, WT)]
    poly = [(LATCH_X + HINGE * d, YF + WT - u) for d, u in pts]
    return prism(poly, 0, 1, 2, DOOR_OPEN_H).translate([0, 0, ZF])


PIN_Y = YF + WT - DOOR_AXIS_U   # -53.646 the hinge pin line


def door_holes():
    """The hinge pin holes (the top one in the flat header, the bottom one in the sill) and the
    trench the bottom pin slides in through, out through the sill's inside face. No groove in
    the floor: the door is hung in the loose front wall and is captive once that wall is on."""
    return [cyl_z(PIN_X, PIN_Y, ZF - HOLE_BOTTOM_DEPTH, ZF + 1, PIN_HOLE_D),
            cyl_z(PIN_X, PIN_Y, ZF + DOOR_OPEN_H - 1, ZF + DOOR_OPEN_H + HOLE_TOP_DEPTH, PIN_HOLE_D),
            box(PIN_X - PIN_HOLE_D / 2, PIN_X + PIN_HOLE_D / 2, PIN_Y, YF + WT + 1, ZF - TRENCH_DEPTH, ZF + 1)]


def walls():
    """All four walls in one, assembled; wall_pieces() cuts them apart for printing. The porch
    gable, frame, ceiling, posts and railings are parts of their own."""
    shell = union([box(-W / 2, W / 2, YF, L / 2, 0, ZWT), prism_xz(GABLE, 0, L / 2)])
    # the siding only; below the floor's top it is the skirt that hangs over the floor's edge,
    # except on the front wall, which stands on the deck
    cuts = [box(-W / 2 + TS, W / 2 - TS, YF + TS, L / 2 - TS, -1, 400),
            box(-W, W, YF - 1, YF + TS + 0.01, -1, ZF)]
    # siding grooves: the side walls' every 8 in from the front joint, which is itself in one
    y = YJ + GROOVE_OC
    while y < L / 2 - 0.01:
        for sx in (1, -1):
            xa, xb = sorted([sx * (W / 2 - GROOVE_D), sx * (W / 2 + 1)])
            cuts.append(box(xa, xb, y - GROOVE_W / 2, y + GROOVE_W / 2, -1, ZWT + 1))
        y += GROOVE_OC
    for x in layout(-W / 2, W / 2, GROOVE_OC):
        cuts.append(box(x - GROOVE_W / 2, x + GROOVE_W / 2, YF - 1, YF + GROOVE_D, -1, ZWT + 1))
        cuts.append(box(x - GROOVE_W / 2, x + GROOVE_W / 2, L / 2 - GROOVE_D, L / 2 + 1, -1, ZPK + 1))
    shell = shell - union(cuts)

    framing = []
    for name in WALL_SIDE:
        framing += wall_framing(name) + under_floor(name)
    framing += list(gable_parts(1).values())
    for sx in (1, -1):              # the front wall's end blocks: solid columns that own the front corners
        xa, xb = sorted([sx * (W / 2 - WT), sx * W / 2])
        framing.append(box(xa, xb, YF, YF + WT, 0, ZWT))
        xa, xb = sorted([sx * (W / 2 - WT), sx * (W / 2 - TS)])   # the back corner posts, solid into the
        framing.append(box(xa, xb, L / 2 - WT - SW, L / 2 - TS, 0, ZWT))   # corner: each mitred end a wedge
    b = union([shell] + framing + wall_trims())
    b = b - union([prong_relief(name, ac, sd) for name in WALL_SIDE for ac, sd in PRONGS[name]])

    op_cuts = [wall_box(name, a0, a1, -0.5, WT + 2, z0, z1)
               for name in WALL_SIDE for a0, a1, z0, z1, _ in openings(name)]
    b = b - union(op_cuts + front_joint_cuts())       # after the framing: the end blocks are framing
    units = [p for name in WALL_SIDE for a0, a1, z0, z1, kind in openings(name) if kind == "window"
             for p in window_unit(name, (a0 + a1) / 2)]
    vent = gable_vent(1)
    b = union([b] + units + [vent[0]])
    b = union([b - union(vent[1])] + vent[2])
    b = b + door_stop()
    b = b - union(door_holes() + roof_clearance() + loft_notches())
    return b + union(roof_pegs(1) + notch_fills())


def body():
    """The assembled body: four walls and the floor."""
    return union(list(wall_pieces(walls()).values()) + [floor()])


# the back corners: the barn's 45 degree mitres through the inside and outside corners, so each
# wall carries only the trim on its own face and it all prints on top (Alan, Nov 1 2026, on the
# shed). Each wall prints lying flat on the inside face of its framing, outside up.
BIG = 500


def mitred(axis, sign):
    """The region one wall owns at the back: outside its inside face, and on its side of the mitre
    at each end. axis 0 for a side wall, 1 for the back wall; sign which side."""
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
    """Above the top of the wall plates at one end: all of it goes with that end's gable."""
    return M.cube([2 * BIG] * 3, True).trim_by_plane([0, 0, 1], ZWT).trim_by_plane([0, sign, 0], 0)


def half_space(n, d):
    return M.cube([2 * BIG] * 3, True).trim_by_plane(n, d)


WALL_CUTS = {
    "right side": (mitred(0, 1) ^ half_space([0, 1, 0], YS)) - half_space([0, 0, 1], ZWT - 0.15),
    "left side": (mitred(0, -1) ^ half_space([0, 1, 0], YS)) - half_space([0, 0, 1], ZWT - 0.15),
    "back wall": mitred(1, 1) + above_plate(1),
    "front wall": box(-BIG, BIG, YF - 2, YF + WT, -BIG, ZWT - 0.15),
}
# cabin coords to print coords, inside face down (each a rotation, det +1)
WALL_TO_PRINT = {
    "right side": [[0, 1, 0], [0, 0, 1], [1, 0, 0]],
    "left side": [[0, -1, 0], [0, 0, 1], [-1, 0, 0]],
    "back wall": [[-1, 0, 0], [0, 0, 1], [0, 1, 0]],
    "front wall": [[1, 0, 0], [0, 0, 1], [0, -1, 0]],
}
GABLE_TO_PRINT = WALL_TO_PRINT["front wall"]


def split_walls(w):
    return {name: w ^ cut for name, cut in WALL_CUTS.items()}


def cbox(u0, u1, v0, v1, z0, z1):
    """A box at the (+x, +y) corner: u out from the side wall's siding face, v out from the back
    wall's, z up. The outside corner of the siding is u = v = 0."""
    return box(W / 2 + u0, W / 2 + u1, L / 2 + v0, L / 2 + v1, z0, z1)


def at_corner(m, sx, sy=1):
    """A part made at the (+x, +y) corner, moved to the corner on side sx: mirrored, so each back
    corner gets its own hand."""
    m = m if sx > 0 else m.mirror([1, 0, 0])
    return m if sy > 0 else m.mirror([0, 1, 0])


def corner_top(m, out, cap, lift=0.0):
    """m, at the (+x, +y) corner, with its top cut off: a 45 degree slope rising inward from the
    line ROOF_CLR under the lower roof sheets (eave_line()) at m's outside face, out mm past the
    side wall's siding, so the steep roof stays clear of all of it and it still prints lying on
    that face; and nothing above cap. lift raises the slope and the cap."""
    c = eave_line(out) + out + W / 2 + lift                      # the slope: x + z = c
    r = m.trim_by_plane([-1 / math.sqrt(2), 0, -1 / math.sqrt(2)], -c / math.sqrt(2))
    return r ^ box(-BIG, BIG, -BIG, BIG, -BIG, cap + lift)


def angle_reach():
    """How far a corner angle covers the side wall's face and the back wall's from the corner."""
    return ANGLE_REACH, ANGLE_UP - (ANGLE_T - POCKET_D)


def corner_angle(sx=1, sy=1):
    """The black L glued on a back corner (Alan, Nov 3 2026, on the barn), made at (+x, +y) and
    moved to side sx: a leg on each wall's face, ANGLE_T thick, its inside face on the floor of the
    recess in the wall and ANGLE_P of it out of the siding, with a 45 degree fillet in its inside
    corner. Each leg covers ANGLE_REACH of its wall (F5). The back-face leg is ANGLE_UP wide, a
    whole number of layers as it stands in the print. Its foot is level with the bottom of the
    skirts. Its top keeps ROOF_CLR under the lower roof sheets (they reach past the gables, so the
    back-face leg is under one too), and the back-face leg stops RAKE_CLR under the rake board. It
    prints lying on the long-face leg's outside face, the other leg standing up."""
    d, f, e = POCKET_D, ANGLE_FILLET, 0.2
    x, y = W / 2 - d, L / 2 - d                                   # the inside corner of the legs
    fillet = prism([(x - f, y + e), (x - f, y), (x, y - f), (x + e, y - f), (x + e, y + e)], 0, 1, 2, ZWT)
    a = union([cbox(-d, ANGLE_P, -ANGLE_REACH, ANGLE_P, 0, ZWT), cbox(ANGLE_P - ANGLE_UP, ANGLE_P, -d, ANGLE_P, 0, ZWT),
               fillet])
    return at_corner(corner_top(a, ANGLE_P, ZWT - RAKE_CLR), sx, sy)


def corner_recess(sx=1, sy=1):
    """What comes out of the walls at a back corner for its angle, made at (+x, +y) and moved to
    side sx: a recess POCKET_D deep in each wall's face, reaching the angle's reach + POCKET_CLR
    along it from the corner, from under the skirts up to POCKET_CLR over the angle's top; and the
    walls' outside corner cut off at 45 degrees, square to the mitre, CORNER_CHAMFER past where
    the recess floors meet. The side wall's recess has a level top POCKET_CLR over the angle's
    highest point there, so the angle presses straight in under it (barn review, Nov 3 2026).
    Neither goes higher than the top of the wall plates, where the rake board starts."""
    rl, re = angle_reach()
    cl, ce, d = rl + POCKET_CLR, re + POCKET_CLR, POCKET_D
    k = -(2 * d + CORNER_CHAMFER)                                 # the chamfer: u + v > k
    h = 1 / math.sqrt(2)
    chamfer = cbox(-4, 2, -4, 2, -1, ZWT).trim_by_plane([h, h, 0], (k + W / 2 + L / 2) * h)
    top = eave_line(ANGLE_P) + ANGLE_P + d + POCKET_CLR           # POCKET_CLR over the angle's inside top edge
    end_recess = corner_top(cbox(-ce, 2, -d, 2, -1, ZWT), ANGLE_P, ZWT - POCKET_CLR, lift=POCKET_CLR)
    return at_corner(union([cbox(-d, 2, -cl, 2, -1, top), end_recess, chamfer]), sx, sy)


CORNERS = [(1, 1), (-1, 1)]      # the back corners only: the front ones are glued butt joints
# a corner angle from cabin coords to print coords: lying on the long-face leg's outside face, its
# foot at the left, the other leg standing up (each a rotation, det +1)
CORNER_TO_PRINT = {1: [[0, 0, 1], [0, 1, 0], [-1, 0, 0]], -1: [[0, 0, 1], [0, -1, 0], [1, 0, 0]]}


def corner_walls(sx, sy=1):
    """(side wall, back wall) that meet at the back corner on side sx."""
    return ("right side" if sx > 0 else "left side"), "back wall"


def corner_prints():
    """The two corner angles, each lying the way it prints: [(name, part)]."""
    return [("%s at %s" % corner_walls(sx, sy), to_print(CORNER_TO_PRINT[sx], [corner_angle(sx, sy)])[0])
            for sx, sy in CORNERS]


def mitre_bevels(sx):
    """The bevel along the top edge of the side wall's back mitre (side sx): in the upright plane
    square to the mitre, a 45 degree triangle MITRE_BEVEL each way off the corner, so the back wall
    coming down past a side wall pushed in a little slides off it (barn review, Nov 2 2026)."""
    z_top = ZWT - 0.15
    sy = 1
    n = np.array([sx, -sy, 0.0]) / math.sqrt(2)            # into the side wall, square to the mitre
    t = np.array([sx, sy, 0.0]) / math.sqrt(2)             # along the mitre
    p0 = np.array([sx * (W / 2 - WT), sy * (L / 2 - WT), 0.0]) + n * MITRE_GAP / 2
    cs = m3.CrossSection([[(-0.5, z_top - MITRE_BEVEL - 0.5), (MITRE_BEVEL, z_top), (MITRE_BEVEL, z_top + 1),
                           (-0.5, z_top + 1)]])
    run = 2 * WT * math.sqrt(2) + 4
    ez = t if np.linalg.det(np.column_stack([n, [0, 0, 1], t])) > 0 else -t
    mat = np.column_stack([n, [0, 0, 1], ez, p0 - ez * run / 2])
    return [M.extrude(cs, run).transform(mat)]


def solid(m):
    """m without the empty shells (no volume) a boolean can leave where two faces meet exactly."""
    keep = [q for q in m.decompose() if q.volume() > 1e-3]
    return union(keep) if keep else m


def wall_pieces(w):
    """The four walls cut apart, with the recesses for the corner angles cut in the back corners
    and the bevels on the side walls' back mitres."""
    pieces = split_walls(w)
    recesses = union([corner_recess(sx, sy) for sx, sy in CORNERS])
    for name in pieces:
        cuts = [recesses] + (mitre_bevels(WALL_SIDE[name][1]) if name in SIDES else [])
        pieces[name] = solid(pieces[name] - union(cuts))
    return pieces


def outline():
    """The cabin's real outline: the room from the front wall's siding face to the back wall's, and
    the porch gable's slab. Everything of a wall or the porch gable outside it is trim. (A box from
    -L/2 to L/2 would contain the front wall's casings and strip them: they would print white.)"""
    return box(-W / 2, W / 2, YF, L / 2, -1, 400) + box(-W / 2, W / 2, -L / 2, -L / 2 + WT, -1, 400)


def trim_zone():
    """Everything standing proud of the siding that is trim (gable band, rake boards, door and
    window casings, the faux loft window). It prints in the second colour."""
    return union(trims()) - outline()


def two_colour(piece, zone):
    """(siding colour, trim colour) parts of a piece: what is inside the outline, and what of the
    trim zone stands out past it. (Taking the zone away instead leaves faces of no thickness up at
    the trim's height, which made the siding look 5.7 mm tall.)"""
    return solid(piece ^ outline()), solid(piece ^ zone)


def to_print(mat, parts):
    """Rotate parts together by mat and put them on the bed as one. mat must be a rotation (det
    +1): a mirror would print the part the wrong hand, the door on the other side of the front
    wall (review Nov 3 2026)."""
    assert abs(np.linalg.det(np.array(mat, dtype=float)) - 1) < 1e-9, "not a rotation"
    m = np.column_stack([np.array(mat, dtype=float), np.zeros(3)])
    out = [p.transform(m) for p in parts]
    bb = union(out).bounding_box()
    return [p.translate([-bb[0], -bb[1], -bb[2]]) for p in out]


# ---------------------------------------------------------------- porch
def porch_gable(peg_x=GABLE_PEG_X):
    """The front gable over the porch, at y = -L/2, standing on the porch frame's front beam at
    the wall top: the barn's end wall above the plates with the faux loft window, no band, no
    backing (spec 4.6, standard layout Nov 3 2026). Siding TS outside, framing SD inside; siding
    grooves every 8 in from x = -W/2; the rake board round the roof edges; the faux loft window
    on the siding, centred, nothing cut behind it; the vent as the back wall's. Two square pegs
    point down into the frame; the roof pegs as the back wall's."""
    yi = -L / 2 + WT
    above = box(-W, W, -L, L, ZWT, 400)
    shell = prism_xz(GABLE, -L / 2, -L / 2 + TS) ^ above
    shell = shell - union([box(x - GROOVE_W / 2, x + GROOVE_W / 2, -L / 2 - 1, -L / 2 + GROOVE_D, ZWT - 1, ZPK + 1)
                           for x in layout(-W / 2, W / 2, GROOVE_OC)])
    b = union([shell] + faux_groove_fills() + list(gable_parts(-1).values()) + porch_gable_trims())
    vent = gable_vent(-1)
    b = union([b] + [vent[0]])
    b = union([b - union(vent[1])] + vent[2])
    pegs = [box(sx * peg_x - GPEG_W / 2, sx * peg_x + GPEG_W / 2, yi - GPEG_T, yi, ZWT - GPEG_L, ZWT + 0.01)
            for sx in (1, -1)]
    return b + union(pegs + roof_pegs(-1))


def gable_peg_sockets(peg_x=GABLE_PEG_X):
    """The porch gable's peg sockets in the frame's front beam, from its top, TENON_CLR round."""
    yi, c = -L / 2 + WT, TENON_CLR
    return [box(sx * peg_x - GPEG_W / 2 - c, sx * peg_x + GPEG_W / 2 + c, yi - GPEG_T - c, yi + c,
                ZWT - GPEG_SOCKET, ZWT + 1) for sx in (1, -1)]


def porch_frame_clearance():
    """The porch frame's outer top edges (the side beams' and the front beam's ends) cut to
    ROOF_CLR under the steep lower sheets, square to them, as roof_clearance() cuts the side walls'
    top edges. Its own, not roof_clearance(), whose side-wall box would cut the side beams down."""
    return [eave_prism(sx, -L, YF) for sx in (1, -1)]


def porch_frame(peg_x=GABLE_PEG_X):
    """The black ring at the top of the porch (spec 4.4), 2.85 tall: the front beam (the header
    band) 0.6 proud of the porch gable and reaching 1.0 behind its inside face; the side beams
    (the wrap bands) flush with the side walls' siding plane, their back ends FIT in front of the
    front wall's face, where they are glued; the rear beam, FIT in front of the door's and window's
    casings, carrying the ceiling's back edge; a lip LIP_W wide round the inside for the ceiling;
    the three post sockets from the bottom and the porch gable's two peg sockets from the top. It is
    the stiff ring that keeps the porch square."""
    z0, z1 = FRAME_Z, ZWT
    yfr, yfb = -L / 2 - PROUD, -L / 2 + WT + 1.0
    xi = W / 2 - WT
    yrb = YF - PROUD - FIT
    yrf = yrb - REAR_D
    beams = [box(-W / 2, W / 2, yfr, yfb, z0, z1), box(-W / 2, -xi, yfr, YF - FIT, z0, z1),
             box(xi, W / 2, yfr, YF - FIT, z0, z1), box(-xi - 0.01, xi + 0.01, yrf, yrb, z0, z1)]
    lip = (box(-xi - 0.01, xi + 0.01, yfb - 0.01, yrf + 0.01, z0, z0 + LIP_H)
           - box(-xi + LIP_W, xi - LIP_W, yfb + LIP_W, yrf - LIP_W, z0 - 1, z1 + 1))
    f = union(beams + [lip])
    return f - union(post_sockets(z0, True) + gable_peg_sockets(peg_x) + porch_frame_clearance())


def porch_ceiling():
    """The white panel over the porch, resting loose on the frame's lip, FIT clear of the four
    beams (designer: 0.01 ft above the band's bottom). It drops in before the porch gable and lifts
    out with the roof off. It prints as it lies, the face seen from below on the bed."""
    xi = W / 2 - WT - FIT
    yfb = -L / 2 + WT + 1.0 + FIT
    yrf = YF - PROUD - FIT - REAR_D - FIT
    return box(-xi, xi, yfb, yrf, FRAME_Z + LIP_H, FRAME_Z + LIP_H + CEIL_T)


def porch_post(body=POST_BODY):
    """A porch post in print coords: X along it from the bottom tenon's end, lying on the face its
    tenons are flush with (Z = 0), Y across. Body POST square, a tenon at each end TENON_L long,
    TENON_W wide (centred) and TENON_T thick."""
    t0, t1 = (POST - TENON_W) / 2, (POST + TENON_W) / 2
    return union([box(TENON_L, TENON_L + body, 0, POST, 0, POST),
                  box(0, TENON_L + 0.01, t0, t1, 0, TENON_T),
                  box(TENON_L + body - 0.01, 2 * TENON_L + body, t0, t1, 0, TENON_T)])


def post_to_cabin(i, z_bottom=ZF):
    """Matrix columns and origin placing porch_post() as post i, its body standing on z_bottom,
    the tenon face toward the outside of the building in x (the -x posts are the same part turned
    180 degrees about z)."""
    xc = POST_XS[i]
    if xc > 0:
        return [(0, 0, 1), (0, 1, 0), (-1, 0, 0)], (xc + POST / 2, POST_Y - POST / 2, z_bottom - TENON_L)
    return [(0, 0, 1), (0, -1, 0), (1, 0, 0)], (xc - POST / 2, POST_Y + POST / 2, z_bottom - TENON_L)


def porch_posts(body=POST_BODY):
    return [place(porch_post(body), *post_to_cabin(i)) for i in range(len(POST_XS))]


def railing(n, length):
    """A railing panel in its own coords: X along it, Y up from the deck's top, Z in from its
    outside face. The bottom rail, n 2x2 balusters BAL_OC apart centred in the panel, the top rail
    filled up to the cap, the cap CAP_D deep overhanging toward the porch; the two end balusters
    run on down to the deck and RAIL_PEG into it as pegs."""
    first = (length - (n - 1) * BAL_OC) / 2
    parts = [box(0, length, RAIL_B0, RAIL_B1, 0, RAIL_D), box(0, length, RAIL_T0, CAP0 + 0.01, 0, RAIL_D),
             box(0, length, CAP0, CAP1, 0, CAP_D)]
    for k in range(n):
        x = first + k * BAL_OC
        y0 = -RAIL_PEG if k in (0, n - 1) else RAIL_B1 - 0.01
        parts.append(box(x - BAL / 2, x + BAL / 2, y0, RAIL_T0 + 0.01, 0, RAIL_D))
    return union(parts)


SIDE_RAIL_LEN = SIDE_RAIL_BACK - (POST_Y + POST / 2 + RAIL_POST_GAP)   # 31.989
# the one front railing, from the left (-x) corner post to the middle post, under the window; the
# right bay (middle post to the +x corner post, the wider one) is the way in, in front of the door
# (STD_SOURCE; the designer leaves the widest gap open, parts/porch.js porchFront)
FRONT_RAIL_X0 = POST_XS[0] + POST / 2 + RAIL_POST_GAP          # -43.133
FRONT_RAIL_X1 = POST_XS[1] - POST / 2 - RAIL_POST_GAP          # -4.683
FRONT_RAIL_LEN = FRONT_RAIL_X1 - FRONT_RAIL_X0                 # 38.451
SIDE_RAIL_N, FRONT_RAIL_N = 7, 9   # the designer's counts at 0.44 ft (porch.js railX: from 0.26 in,
                       # every 0.44 while short of the end by 0.10), centred in the panel. DERIVED


def railing_places():
    """[(kind, columns, origin)] placing the three railings: the two side ones (31.99 long, 7
    balusters) down the porch's sides from the corner posts back toward the front wall, the one
    front railing (38.45 long, 9 balusters, the longest) across the left bay between the -x corner
    post and the middle post; the right bay is the way in. Each panel's middle line RAIL_IN in from
    the deck's edge, its cap toward the middle of the porch."""
    xs = W / 2 - RAIL_IN + RAIL_D / 2       # the side railings' outside face, +-46.345
    yf = -(L / 2 - RAIL_IN) - RAIL_D / 2    # the front railing's outside face, -93.970
    return [("side", [(0, -1, 0), (0, 0, 1), (-1, 0, 0)], (xs, SIDE_RAIL_BACK, ZF)),
            ("side", [(0, 1, 0), (0, 0, 1), (1, 0, 0)], (-xs, SIDE_RAIL_BACK - SIDE_RAIL_LEN, ZF)),
            ("front", [(-1, 0, 0), (0, 0, 1), (0, 1, 0)], (FRONT_RAIL_X1, yf, ZF))]


def railing_part(kind):
    return railing(SIDE_RAIL_N, SIDE_RAIL_LEN) if kind == "side" else railing(FRONT_RAIL_N, FRONT_RAIL_LEN)


def railings():
    return [place(railing_part(k), cols, o) for k, cols, o in railing_places()]


def railing_holes():
    """The holes in the deck for the railings' end-baluster pegs, TENON_CLR round, SOCKET_D deep."""
    out = []
    for kind, cols, o in railing_places():
        n, length = (SIDE_RAIL_N, SIDE_RAIL_LEN) if kind == "side" else (FRONT_RAIL_N, FRONT_RAIL_LEN)
        first = (length - (n - 1) * BAL_OC) / 2
        for x in (first, length - first):
            peg = place(box(x - BAL / 2, x + BAL / 2, -RAIL_PEG, 0, 0, RAIL_D), cols, o).bounding_box()
            c = TENON_CLR
            out.append(box(peg[0] - c, peg[3] + c, peg[1] - c, peg[4] + c, ZF - SOCKET_D, ZF + 1))
    return out


# ---------------------------------------------------------------- roof
def panel_frame(a, b):
    """Matrix taking a roof sheet's own coords (X = y along the cabin, Y = up from its underside,
    Z = down the slope from a) to cabin coords, for the slope from a to b in (x, z)."""
    a = np.asarray(a, dtype=float)
    d = unit(np.asarray(b, dtype=float) - a)
    nrm = np.array([-d[1], d[0]])                  # out of the roof, for a +x slope
    return np.column_stack([[0, 1, 0], [nrm[0], 0, nrm[1]], [d[0], 0, d[1]], [a[0], 0, a[1]]])


ROOF_T = 2.0
RIB_OC = 9 * S
TAIL = 4 * S           # the upper sheet runs on 4 in past the knee, lapping over the lower one
LAP_GAP = 0.45         # gap between that tail and the top of the lower sheet (barn, Nov 2 2026)
PEG_D, PEG_UP = 2.2, 1.0
PEG_HOLE_D, PEG_HOLE_UP = 3.0, 1.4   # 0.4 mm round the peg
PEG_X = KNEE_X / 2     # the upper sheets' pegs, halfway up the shallow slope
LOWER_HOLE_SHIFT = (PEG_HOLE_D - PEG_D) / 2   # each lower hole its clearance further out than its peg
PEG_Y = L / 2 - WT + PEG_D / 2   # against the gables' inside face, so each peg prints lying on the bed


def ribbed_sheet(ly, z0, z1, cap=False):
    """A flat sheet in its own coords, ribs every 9 in running down it."""
    parts = [box(-ly, ly, 0, ROOF_T, z0, z1)]
    rib = m3.CrossSection([[(-0.7, ROOF_T - 0.05), (0.7, ROOF_T - 0.05), (0.3, ROOF_T + 0.6), (-0.3, ROOF_T + 0.6)]])
    for k in range(-30, 31):
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
    """The +x upper roof sheet in cabin coords (the -x one is its mirror image): ridge to knee,
    and its tail on past the knee over the lower sheet, with the ridge cap along its top. It
    sits on the two gables, held by a peg at each end."""
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
    """The +x lower roof sheet in cabin coords: knee to eave, its top cut to the line of the upper
    sheet, which laps over it. It sits on the steep edges of the gables, on a peg standing up at
    each end, so it only comes off straight up, and the upper sheet's tail is in the way of that."""
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
    """Lay a +x roof sheet on the bed, underside down: X down the slope, Y along the cabin."""
    mat = panel_frame(a, b)
    R, p0 = mat[:, :3], mat[:, 3]
    to_local = np.column_stack([R.T, -R.T @ p0])                          # (y, n, s)
    swap = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], dtype=float)        # (s, y, n), det +1
    p = r.transform(np.column_stack([swap @ to_local[:, :3], swap @ to_local[:, 3]]))
    bb = p.bounding_box()
    return p.translate([-bb[0], -bb[1], -bb[2]])


# ---------------------------------------------------------------- door
LITE_HW = 1.12 * FT    # 10.668 the lite's half width and the arch's radius (DERIVED from
                       # parts/openings/door-lite.js: the glass is the leaf less 0.76 ft)
LITE_MULL = LITE_HW / 3   # 3.556 the two upright muntins, either side of the middle (door-lite.js gw/6)
PANEL_HALF = 1.0 * FT  # the raised panels 2 ft wide (door-lite.js: the leaf less 1.0 ft)
KNOB_IN, KNOB_D, KNOB_H = 2.2, 1.0, 1.2   # the knob 2.2 in from the latch edge so it stands on solid door
                       # (the designer's 0.30 ft would put it over the glass), its diameter and height


def door_leaf_plan(open_h, w=DOOR_W):
    """The 11-lite leaf drawn for a doorway open_h tall, in door print coords (X from the pin line, the latch edge
    toward +X before door_hand(), Y up from the door's bottom, DOOR_BOTTOM_GAP over the floor), by the designer's rules
    (parts/openings/door-lite.js, every number Barnwright's): the glass from 0.42 of the opening's height up to the
    arch's spring line, the arch's top 0.55 ft under the head; the lower raised panel 0.30 to 1.12 ft up, the upper
    from 1.36 ft up to 0.24 ft under the glass; the knob 0.44 of the height up. So the glass starts lower in a shorter
    door, its six lites under the spring bar get shorter, and so do the upper panel and the knob's height, while the
    arch, the rail over it and the lower panel stay. DERIVED; the 10x20 Cabin's 75.6 in door is the same rules
    (make_cabin.py LITE_Y0..KNOB_Y). Returns (y0, y1, rail, [(x0, x1, y0, y1)] panels, (x, y) knob): the glass's
    bottom, the spring line, the cross muntin, the panels and the knob."""
    g = DOOR_BOTTOM_GAP
    xc = (w - DOOR_R) / 2                                                 # the leaf's middle
    y0 = 0.42 * open_h - g
    y1 = open_h - 0.55 * FT - LITE_HW - g
    panels = [(xc - PANEL_HALF, xc + PANEL_HALF, 0.30 * FT - g, 1.12 * FT - g),
              (xc - PANEL_HALF, xc + PANEL_HALF, 1.36 * FT - g, 0.42 * open_h - 0.24 * FT - g)]
    return y0, y1, (y0 + y1) / 2, panels, (w - KNOB_IN, 0.44 * open_h - g)


LITE_Y0, LITE_Y1, LITE_RAIL, PANELS, KNOB = door_leaf_plan(DOOR_OPEN_H)   # 24.203, 42.134, 33.168; the knob 25.370 up


def door_hand(d):
    """A door drawn with its latch edge toward +X from the pin line, made the door for the HINGE jamb:
    hung on the +x jamb it is that door's mirror image, the latch toward -X, so in door print coords X
    always runs the cabin's way along the front wall with the door shut (door_matrix)."""
    return d.mirror([1, 0, 0]) if HINGE > 0 else d


def door_part(w=DOOR_W, h=DOOR_H, lite=True):
    """The door in print coords: X across the door from the pin line (the latch edge toward -HINGE),
    Y up the door from its bottom, Z through it (Z=0 is the inside face, on the bed); door_hand()
    draws it with the latch toward +X and hands it. The 36 in 11-lite door, all white:
    the lites in a rectangle with an arched top (6 below the spring bar, 4 in the fan), muntins
    0.8 wide standing 1.6 from the bed, two raised panels outlined by grooves in the outside face,
    and the knob on the outside face only, all drawn for a doorway h + the top and bottom gaps tall
    (door_leaf_plan()), so h=DOOR_H is this cabin's door and the Cabin's DOOR_H the Cabin's (the
    twins' checkers compare them so). lite=False gives a plain short door for the fit test."""
    lite_y0, lite_y1, lite_rail, panels, (kx, ky) = door_leaf_plan(h + DOOR_BOTTOM_GAP + DOOR_TOP_GAP, w)
    t = 2 * DOOR_R
    slab = box(0, w, 0, h, 0, t)
    edge = cyl_y(0, 0, h, DOOR_R, 2 * DOOR_R)                              # rounded hinge edge
    pin_top = cyl_y(0, h - 0.5, h + PIN_TOP_LEN, DOOR_R, PIN_D, 40)
    pin_bot = cyl_y(0, -PIN_BOTTOM_LEN, 0.5, DOOR_R, PIN_D, 40)
    d = union([slab, edge, pin_top, pin_bot])
    if not lite:
        return door_hand(d)
    xc = (w - DOOR_R) / 2                                                 # the leaf's middle, 12.94
    hole_cs = (m3.CrossSection.square([2 * LITE_HW, lite_y1 - lite_y0]).translate([xc - LITE_HW, lite_y0])
               + m3.CrossSection.circle(LITE_HW, 96).translate([xc, lite_y1]))
    hole_cs = hole_cs ^ m3.CrossSection.square([2 * LITE_HW, 200]).translate([xc - LITE_HW, lite_y0])
    hole = M.extrude(hole_cs, t + 2).translate([0, 0, -1])
    mw, mt = 0.8, 1.6
    bars = [box(xc + s * LITE_MULL - mw / 2, xc + s * LITE_MULL + mw / 2, lite_y0 - 0.5, lite_y1, 0, mt) for s in (1, -1)]
    bars += [box(xc - LITE_HW - 0.5, xc + LITE_HW + 0.5, y - mw / 2, y + mw / 2, 0, mt) for y in (lite_rail, lite_y1)]
    for ang in (45, 90, 135):
        a = math.radians(ang)
        spoke = box(0, LITE_HW + 0.5, -mw / 2, mw / 2, 0, mt)
        bars.append(spoke.transform(np.array([[math.cos(a), -math.sin(a), 0, xc], [math.sin(a), math.cos(a), 0, lite_y1],
                                              [0, 0, 1, 0]], dtype=float)))
    d = d - hole
    d = d + (union(bars) ^ M.extrude(hole_cs.offset(0.3, m3.JoinType.Miter), t).translate([0, 0, 0]))
    grooves = []
    for x0, x1, y0, y1 in panels:
        grooves.append(box(x0, x1, y0, y1, t - 0.4, t + 1) - box(x0 + 0.6, x1 - 0.6, y0 + 0.6, y1 - 0.6, t - 1, t + 2))
    d = d - union(grooves)
    return door_hand(d + cyl_z(kx, ky, t - 0.01, t + KNOB_H, KNOB_D, 32))


def door_matrix(theta_deg, pin_x, pin_y, z0):
    """Matrix from door print coords to cabin coords, the door's bottom at z0, its pin line at
    (pin_x, pin_y), swung theta degrees IN (the latch edge toward +y, into the room: hung on the +x
    jamb it turns clockwise seen from above, toward the right side wall)."""
    base = np.array([[1, 0, 0, pin_x], [0, 0, -1, pin_y + DOOR_R], [0, 1, 0, z0]], dtype=float)
    th = math.radians(-HINGE * theta_deg)
    rot = np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]])
    pivot = np.array([pin_x, pin_y, 0])
    return np.column_stack([rot @ base[:, :3], rot @ (base[:, 3] - pivot) + pivot])


def door_to_shed(theta_deg=0.0):
    """Matrix from door print coords to cabin coords, swung theta degrees in."""
    return door_matrix(theta_deg, PIN_X, PIN_Y, ZF + DOOR_BOTTOM_GAP)


# ---------------------------------------------------------------- skids
def skid():
    """One skid lying along X (X = 0 the front end), notched where the joists, the floor's end
    bands, the front wall's band and the back wall's siding sit on it, with a peg at each end that
    pushes up into the end band. It is not the same end for end, so its front end has both upright
    corners cut off at 45 degrees."""
    s = box(0, L, 0, SKID_W, 0, SKID_H)
    cuts = []
    for jy in joist_ys():
        y = jy + L / 2
        cuts.append(box(y - SW / 2 - NOTCH_CLEAR / 2, y + SW / 2 + NOTCH_CLEAR / 2, -1, SKID_W + 1, SKID_H - NOTCH, SKID_H + 1))
    back = TS + FLOOR_CLR + RIM + 0.3
    cuts.append(box(L - back, L + 1, -1, SKID_W + 1, SKID_H - NOTCH, SKID_H + 1))
    cuts.append(box(-1, RIM + 0.3, -1, SKID_W + 1, SKID_H - NOTCH, SKID_H + 1))
    cuts.append(box(F_BAND[0] - 0.3 + L / 2, F_BAND[1] + 0.3 + L / 2, -1, SKID_W + 1, SKID_H - NOTCH, SKID_H + 1))
    m = SKID_MARK
    for poly in ([(-1, -1), (m + 1, -1), (-1, m + 1)], [(-1, SKID_W + 1), (-1, SKID_W - m - 1), (m + 1, SKID_W + 1)]):
        cuts.append(prism(poly, 0, 1, 2, SKID_H + 2).translate([0, 0, -1]))
    s = s - union(cuts)
    pegs = [cyl_z(X, SKID_W / 2, SKID_H - NOTCH - 0.01, SKID_H - NOTCH + SKID_PEG_UP, SKID_PEG_D)
            for X in (RIM / 2, L - (TS + FLOOR_CLR + RIM / 2))]
    return s + union(pegs)


def skid_mark():
    """What the front-end mark takes off a skid (for the checker)."""
    m = SKID_MARK
    return union([prism(poly, 0, 1, 2, SKID_H).translate([0, 0, 0]) for poly in
                  ([(0, 0), (m, 0), (0, m)], [(0, SKID_W), (0, SKID_W - m), (m, SKID_W)])])


def skids():
    """Both skids side by side for printing."""
    s = skid()
    return s + s.translate([0, SKID_W + SKID_GAP, 0])   # as on the plate, so their 5 mm brims don't merge


def skids_to_shed():
    """Matrices placing skid() under the floor frame, joists down in the notches, front ends
    under the porch."""
    return [np.array([[0, -1, 0, sx * SKID_X + SKID_W / 2], [1, 0, 0, -L / 2], [0, 0, 1, -(SKID_H - NOTCH)]], dtype=float)
            for sx in (-1, 1)]


# ---------------------------------------------------------------- fit test
FIT_X0, FIT_Y1 = 33.0, -84.0     # the deck corner: x from here out, y from the front to here
FIT_FRAME_X0 = 41.0              # the frame corner from x 41.0 out and from the front to y -88.5, so it
FIT_FRAME_Y1 = -88.5             # balances on the one short post by itself, the gable foot on it too: cut
                                 # at 33.0 and -84.0 as the deck, its weight was 2.1 mm outside the post's
                                 # top (3.5 with the gable foot on) and it fell off (review Nov 3 2026, as
                                 # the Cabin's). DERIVED: the checker proves its centre of mass is over the
                                 # post's top, at least 0.4 mm in from every edge, alone and with the foot
FIT_PEG_X = 42.8                 # the porch gable's peg and its frame socket are moved here for the test
                                 # (37.0 before), 0.65 mm of frame left to the cut and 0.63 to the post's socket
FIT_FOOT_X0 = -W / 2 + 14 * GROOVE_OC   # 41.275, the gable foot is cut from the middle of the siding groove
                                 # here: cut at FIT_FRAME_X0 with the frame corner, 0.025 short of that groove,
                                 # it left a strip of siding 0.025 wide at the cut, thinner than a line (check
                                 # Nov 3 2026). Its end stands 0.275 in from the frame corner's. DERIVED
FIT_FOOT_X1 = FIT_PEG_X + 3.0    # 45.8, the gable foot is cut from FIT_FOOT_X0 to here, 1.0 longer than the
                                 # Cabin's: this foot is the solid gable board with the rake board's end on it,
                                 # and cut the Cabin's way (FIT_FRAME_X0 to FIT_PEG_X + 2.0) it weighed 88.8 mm3
                                 # to the Cabin's 52.9 and held the pair's centre of mass only 0.43 in from the
                                 # post top's edge, 0.08 more than the tenon's 0.35 play; cut from FIT_FOOT_X0
                                 # to here, 0.66. It stops short of x 46.0, where the steep gable edge comes
                                 # down to the foot's top, so the foot stays a plain block. DERIVED
FIT_POST_BODY = 12.0             # the short post's body
FIT_DZ = -(POST_BODY - FIT_POST_BODY)   # the frame corner and gable foot come down this much with it
FIT_RAIL = 9.0                   # the front 9 mm of a side railing
FIT_FOOT = GABLE_BOARD           # the gable foot's height: the gable board's top, so no siding hangs past it
                                 # in the print (cut at the spec's 5.0 it left 0.63 of siding over nothing)


def porch_joint_test():
    """Plate 1 of the fit test, the porch joints, cut from the real parts with the real joints,
    in cabin coords and fitted together (the frame corner and gable foot brought down onto the
    short post): {name: (part, matrix to print)}. The deck's front-right corner with its corner
    post socket and the side railing's front peg hole (since the standard layout the right bay is
    the way in, so no front railing hole is there: the front railing's holes are the same joint);
    a short post with both tenons; the porch frame's front-right corner, cut smaller than the deck
    corner so it balances on the short post (FIT_FRAME_X0, FIT_FRAME_Y1), with its post socket, lip
    and a porch-gable peg socket moved out to FIT_PEG_X beside the post; the foot of the porch
    gable, from FIT_FOOT_X0 to FIT_FOOT_X1, with its peg moved the same; the front end of a side
    railing with its peg baluster and the next."""
    up = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    deck = floor() ^ box(FIT_X0, W / 2 + 1, -L / 2 - 1, FIT_Y1, -1, ZF + 1)
    i = POST_XS.index(max(POST_XS))                      # the +x corner post
    cols, o = post_to_cabin(i)
    post = place(porch_post(FIT_POST_BODY), cols, o)
    fr = porch_frame(FIT_PEG_X) ^ box(FIT_FRAME_X0, W / 2 + 1, -L / 2 - 2, FIT_FRAME_Y1, 0, 200)
    gf = porch_gable(FIT_PEG_X) ^ box(FIT_FOOT_X0, FIT_FOOT_X1, -L / 2 - 2, -L / 2 + WT + 2, ZWT - 5, ZWT + FIT_FOOT)
    kind, rcols, ro = railing_places()[0]
    rail = place(railing_part(kind) ^ box(SIDE_RAIL_LEN - FIT_RAIL, SIDE_RAIL_LEN + 1, -5, 40, -1, 5), rcols, ro)
    return {"deck corner": (deck, FLOOR_TO_PRINT),
            "short post": (post, None),
            "frame corner": (fr.translate([0, 0, FIT_DZ]), up),
            "gable foot": (gf.translate([0, 0, FIT_DZ]), GABLE_TO_PRINT),
            "railing end": (rail, None)}


def porch_joint_prints():
    """The porch joints each lying the way it prints: [(name, part)]."""
    out = []
    for name, (part, mat) in porch_joint_test().items():
        if name == "short post":
            out.append((name, on_bed(porch_post(FIT_POST_BODY))))
        elif name == "railing end":
            r = railing_part("side") ^ box(SIDE_RAIL_LEN - FIT_RAIL, SIDE_RAIL_LEN + 1, -5, 40, -1, 5)
            out.append((name, on_bed(r)))
        else:
            out.append((name, to_print(mat, [part])[0]))
    return out


# where the short front corner's pieces are cut: each along the far side of a stud, so the siding at the
# cut is held (as the barn's corner_test); cut mid-bay at the spec's x 26.0 and y -33.0, the siding hung
# out past the stud and Flash Studio warned of a floating cantilever (Nov 3 2026). Since the standard
# layout the door is where the +x window was, so the front wall is cut at the door's +x full stud, past
# the opening, and the corner keeps the end of the door sill in its closed pocket and the +x prong
FIT_FRONT_X0 = DOOR_X1 + SW      # 32.052, the near face of the door's +x full stud
FIT_FLOOR_X0 = FIT_FRONT_X0 - 2.0   # 30.052, the floor piece starts a little before it
FIT_SIDE_Y1 = -31.75 + SW / 2    # -31.155, the far face of the side wall's stud at -31.75
FIT_FLOOR_Y1 = -29.5             # the floor piece runs on past that stud's notch


def front_corner_test(pieces, f):
    """Plate 2's short front corner, as the barn's corner_test: the front wall from the door's +x
    full stud to its +x end and the right side from its front end to its stud at -40 in, each its
    bottom 8 mm above the floor joined to its top 10 mm under the wall top, on that corner of the
    floor, x FIT_FLOOR_X0 on and y -60.0 to -29.5 (end-block notch, the end of the door sill's closed
    pocket, the right side's notches and prong slot, the front wall's +x prong slot, a strip of
    porch deck). Returns (front wall, side wall, floor) in cabin coords."""
    z_lo, z_hi = ZF + 8, ZWT - 10

    def short(piece, region):
        lo = piece ^ region ^ box(-BIG, BIG, -BIG, BIG, -5, z_lo)
        hi = piece ^ region ^ box(-BIG, BIG, -BIG, BIG, z_hi, ZWT)
        return lo + hi.translate([0, 0, z_lo - z_hi])
    fw = short(pieces["front wall"], box(FIT_FRONT_X0, W / 2 + 2, YF - 2, YF + WT + 0.05, -5, ZWT))
    sw = short(pieces["right side"], box(W / 2 - WT - 2, W / 2 + 2, YS - 0.05, FIT_SIDE_Y1, -5, ZWT))
    fl = f ^ box(FIT_FLOOR_X0, W / 2, -60.0, FIT_FLOOR_Y1, -5, 400)
    return fw, sw, fl


def front_corner_prints(pieces, f):
    fw, sw, fl = front_corner_test(pieces, f)
    return [("short front wall", to_print(WALL_TO_PRINT["front wall"], [fw])[0]),
            ("short right side", to_print(WALL_TO_PRINT["right side"], [sw])[0]),
            ("bit of floor", to_print(FLOOR_TO_PRINT, [fl])[0])]


FIT_OW, FIT_OH, FIT_ZF = 14.0, 24.0, 3.0


def fit_doorway():
    """The in-swing doorway made short (F10): a 14 x 24 opening in a piece of front wall standing
    on its own sill block, with NO floor (the real door is hung in the loose wall): the same pin
    line 1.6 from the inside face, the pin holes, the stop with its 45 degree underside from u 2.45
    and the trench out through the inside face, hinged on the same side as the real door. In cabin
    coords with the opening centred on x = 0. Returns (doorway, its pin line (x, y), the floor level z)."""
    ow, oh, zf = FIT_OW, FIT_OH, FIT_ZF
    jamb = ow / 2
    yo, yi = YF, YF + WT
    px, py = HINGE * (jamb - DOOR_R - DOOR_GAP), yi - DOOR_AXIS_U
    f = union([box(-jamb - 6, jamb + 6, yo, yi, 0, zf), box(-jamb - 6, -jamb, yo, yi, zf - 0.01, zf + oh + 6),
               box(jamb, jamb + 6, yo, yi, zf - 0.01, zf + oh + 6), box(-jamb - 6, jamb + 6, yo, yi, zf + oh, zf + oh + 6)])
    pts = [(-0.05, 2.45), (0.0, 2.45)] + [(d, WT if u is None else u) for d, u in STOP_SECTION[1:]] + [(-0.05, WT)]
    f = f + prism([(-HINGE * jamb + HINGE * d, yi - u) for d, u in pts], 0, 1, 2, oh).translate([0, 0, zf])
    f = f - union([cyl_z(px, py, zf - HOLE_BOTTOM_DEPTH, zf + 1, PIN_HOLE_D),
                   cyl_z(px, py, zf + oh - 1, zf + oh + HOLE_TOP_DEPTH, PIN_HOLE_D),
                   box(px - PIN_HOLE_D / 2, px + PIN_HOLE_D / 2, py, yi + 1, zf - TRENCH_DEPTH, zf + 1)])
    return f, (px, py), zf


def fit_door():
    """The short door for fit_doorway(): the same pins and hinge edge, plain, the same hand."""
    return door_part(FIT_OW - 2 * DOOR_GAP - DOOR_R, FIT_OH - DOOR_BOTTOM_GAP - DOOR_TOP_GAP, lite=False)


def roof_peg_test():
    """The barn's roof-peg block (the peg lying on the bed, as on the gables) and a roof coupon
    with the peg hole, each as it prints."""
    blk = box(-6, 6, 0, 6, 0, WT) + cyl_y(0, 5, 6 + PEG_UP, PEG_D / 2, PEG_D)
    cpn = box(-6, 6, -6, 6, 0, ROOF_T) - cyl_z(0, 0, -1, PEG_HOLE_UP, PEG_HOLE_D)
    return on_bed(blk), on_bed(cpn)


def fit_plate_2(pieces, f):
    """Plate 2's pieces each lying the way it prints: [(name, part)]."""
    dw, _, _ = fit_doorway()
    blk, cpn = roof_peg_test()
    return (front_corner_prints(pieces, f) +
            [("doorway", to_print(WALL_TO_PRINT["front wall"], [dw])[0]), ("short door", on_bed(fit_door())),
             ("roof peg block", blk), ("roof coupon", cpn)])


def fit_test(pieces, f):
    """All the fit-test pieces in one, plate 1's row behind plate 2's two rows (for fit test.stl)."""
    rows = [porch_joint_prints(), fit_plate_2(pieces, f)[:3], fit_plate_2(pieces, f)[3:]]
    out, y = [], 0.0
    for r in rows:
        x, h = 0.0, 0.0
        for _, m in r:
            out.append(m.translate([x, y, 0]))
            x += size(m)[0] + 4
            h = max(h, size(m)[1])
        y += h + 4
    return union(out)


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
    lofts, posts and railings). (The Side Utility's, with its per-object settings.) "modifier" in the settings,
    [(name, manifold, settings)] in the parts' coords, is written as modifier parts with those settings and no
    filament of their own (as the garages'); where the object lies on the plate comes from its parts alone."""
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
    parts["porch gable"] = porch_gable()
    parts["porch frame"] = porch_frame()
    parts["porch ceiling"] = porch_ceiling()
    parts["posts"] = porch_posts()
    parts["railings"] = railings()
    parts["upper"] = upper_panel()
    parts["lower"] = lower_panel()
    parts["loft"] = loft(1)
    parts["door"] = door_part()
    parts["skids"] = skids()
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


def turned(m):
    """A part turned 90 degrees on the bed (X becomes Y)."""
    return on_bed(m.transform(np.array([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0]], dtype=float)))


NO_BRIM = {"brim_type": "no_brim"}      # a brim lip would show on a visible edge; the long roof
                                        # sheets come near the bed's edge (F3)
SKID_BRIM = {"brim_type": "outer_only", "brim_width": "5"}   # long thin parts get a 5 mm brim
                                        # (PRINTER-BRAIN, bed adhesion)
BRIM_GAP, SKID_GAP = 6.15, 10.75        # every skid at least 6.0 from any other part and 10.5 from
                                        # the next skid, so the brims neither merge nor touch
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


def print_parts(p):
    """Every part lying the way it prints: {name: part or (siding, trim)}."""
    zone = trim_zone()
    out = {name: wall_parts(p, name, zone) for name in WALL_CUTS}
    out["porch gable"] = to_print(GABLE_TO_PRINT, two_colour(p["porch gable"], zone))
    out["floor"] = to_print(FLOOR_TO_PRINT, [p["floor"]])[0]
    out["loft"] = to_print(LOFT_TO_PRINT, [p["loft"]])[0]
    out["upper roof"] = panel_to_print(p["upper"], UPPER_A, UPPER_B)
    out["lower roof"] = panel_to_print(p["lower"], LOWER_A, LOWER_B)
    out["porch frame"] = on_bed(p["porch frame"])
    out["porch ceiling"] = on_bed(p["porch ceiling"])
    out["porch post"] = on_bed(porch_post())
    out["side railing"] = on_bed(railing_part("side"))
    out["front railing"] = on_bed(railing_part("front"))
    out["door"] = on_bed(p["door"])
    out["skid"] = on_bed(skid().transform(np.array([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0]], dtype=float)))
    out["corner angles"] = corner_prints()
    return out


def plates(p):
    """The plates of each Orca project, from build()'s parts, as write_3mf() takes them:
    {file name: [(plate name, items)]}.

    2 all plates.3mf has a plate for each print (F3): both side walls and the door; the roof, the
    porch frame and the corner angles; the end walls, the porch gable and the ceiling; then the
    floor, skids, lofts and the porch's brown parts. Filament 1 is the siding colour (white),
    filament 2 the trim, roof, corner angles and porch frame (black), filament 3 the floor, skids,
    lofts, posts and railings (brown, Alan Nov 2 2026). The prime tower goes at x 165, y 195 on a
    two-colour plate, so those plates keep every part at x <= 162 or y <= 192. The walls carry their bridge
    modifiers (across_studs) and the floor its seams' (across_seams)."""
    pp = print_parts(p)

    def wall_item(name, x, y, piece=None):
        """A wall with its bridge modifier (ACROSS_STUDS): on a gable it stops on the collar tie's middle, where
        it lies on the bed (from the wall's lowest point), and the triangles over it bridge up the gable."""
        siding, trim = pp[name] if piece is None else piece
        y_to = COLLAR_MID - p[name].bounding_box()[2] if name in ("back wall", "porch gable") else None
        return (name, [("siding", siding, 1)] + ([] if trim.is_empty() else [("trim", trim, 2)]), (x, y),
                across_studs(union([siding, trim]), y_to=y_to))

    def one(name, m, fil, x, y, own=None):
        return (name, [(name, m, fil)], (x, y)) + ((own,) if own else ())

    # plate 1: the side walls one behind the other, the door beside them
    lw, lh = size(union(pp["right side"]))
    y0 = (220 - 2 * lh - 3) / 2
    plate1 = [wall_item("right side", 3, y0), wall_item("left side", 3, y0 + lh + 3),
              one("door", pp["door"], 1, 3 + lw + 3, y0)]
    # plate 2: the four roof sheets turned along x, the porch frame and the angles in front of them
    up, lo = turned(pp["upper roof"]), turned(pp["lower roof"])
    uw, uh = size(up)
    _, lh2 = size(lo)
    rx = (220 - uw) / 2
    ys = [3.0, 3.0 + uh + 3, 3.0 + 2 * uh + 6, 3.0 + 2 * uh + lh2 + 9]
    fr = pp["porch frame"]
    fy = ys[3] + lh2 + 3
    fw, _ = size(fr)
    ang = pp["corner angles"]
    ah = size(ang[0][1])[1]
    plate2 = ([one("upper roof 1", up, 2, rx, ys[0], NO_BRIM), one("upper roof 2", up, 2, rx, ys[1], NO_BRIM),
               one("lower roof 1", lo, 2, rx, ys[2], NO_BRIM), one("lower roof 2", lo, 2, rx, ys[3], NO_BRIM),
               one("porch frame", fr, 2, 3, fy, NO_BRIM)] +
              [one("corner angle, " + n, m, 2, 3 + fw + 6, fy + k * (ah + 3), NO_BRIM) for k, (n, m) in enumerate(ang)])
    # plate 3: the back wall and the ceiling on the left, the front wall and porch gable on the right
    bw, bh = size(union(pp["back wall"]))
    x2 = 3 + W + 6
    _, fh = size(union(pp["front wall"]))
    plate3 = [wall_item("back wall", 3, 3), wall_item("front wall", x2, 3),
              wall_item("porch gable", x2, 3 + fh + 6), one("porch ceiling", pp["porch ceiling"], 1, 3, 3 + bh + 6)]
    # plate 4: the floor, the skids beside it (brims), the lofts turned, the posts and railings (three
    # posts and one front railing since the standard layout; the front railing under the side ones)
    fl = pp["floor"]
    flw, flh = size(fl)
    sk = pp["skid"]
    skw, skh = size(sk)
    lf = turned(pp["loft"])
    lfw, lfh = size(lf)
    sx1 = 3 + flw + BRIM_GAP
    sx2 = sx1 + skw + SKID_GAP
    lx = sx2 + skw + BRIM_GAP
    post = turned(pp["porch post"])
    pw_, _ = size(post)
    py = 3 + lfh + BRIM_GAP
    n_posts = len(POST_XS)
    rx1 = lx + n_posts * (pw_ + 3)
    sr, frl = pp["side railing"], pp["front railing"]
    srw, srh = size(sr)
    plate4 = ([one("floor", fl, 3, 3, (220 - flh) / 2),
               one("skid 1", sk, 3, sx1, (220 - skh) / 2, SKID_BRIM), one("skid 2", sk, 3, sx2, (220 - skh) / 2, SKID_BRIM),
               one("loft 1", lf, 3, lx, 3), one("loft 2", lf, 3, lx + lfw + 3, 3)] +
              [one("porch post %d" % (k + 1), post, 3, lx + k * (pw_ + 3), py, NO_BRIM) for k in range(n_posts)] +
              [one("side railing %d" % (k + 1), sr, 3, rx1, py + k * (srh + 3), NO_BRIM) for k in range(2)] +
              [one("front railing", frl, 3, rx1, py + 2 * (srh + 3), NO_BRIM)])
    all_plates = [("long walls and door", plate1),
                  ("roof, porch frame and corner angles", plate2),
                  ("end walls, porch gable and ceiling", plate3),
                  ("floor, skids, lofts and porch", plate4)]

    # the fit test's short walls, doorway and gable foot carry their real walls' bridge modifier (ACROSS_STUDS;
    # the gable foot is the porch gable's foot, under its collar tie)
    fit_own = {"short front wall": across_studs, "short right side": across_studs, "doorway": across_studs,
               "gable foot": across_studs}

    def with_own(name, m, item):
        return item + ((fit_own[name](m),) if name in fit_own else ())

    def row(parts, gap=6.0):
        """[(name, part)] side by side along x, gap apart, the row centred on the bed."""
        x = (220 - sum(size(m)[0] for _, m in parts) - gap * (len(parts) - 1)) / 2
        out = []
        for name, m in parts:
            out.append(with_own(name, m, (name, [(name, m, 1)], (x, (220 - size(m)[1]) / 2))))
            x += size(m)[0] + gap
        return out

    pieces = {n: p[n] for n in WALL_CUTS}
    p2 = fit_plate_2(pieces, p["floor"])
    corner, rest = p2[:3], p2[3:]
    cw = sum(size(m)[0] for _, m in corner) + 6 * (len(corner) - 1)
    ch = max(size(m)[1] for _, m in corner)
    items2, x = [], (220 - cw) / 2
    for name, m in corner:
        items2.append(with_own(name, m, (name, [(name, m, 1)], (x, 3))))
        x += size(m)[0] + 6
    rw = sum(size(m)[0] for _, m in rest) + 6 * (len(rest) - 1)
    x = (220 - rw) / 2
    for name, m in rest:
        items2.append(with_own(name, m, (name, [(name, m, 1)], (x, 3 + ch + 8))))
        x += size(m)[0] + 6
    fit_3mf = [("porch joints", row(porch_joint_prints())),
               ("front corner, door and roof peg", items2)]
    # the floor's seam modifiers last, after the fit test's pieces are cut: Manifold numbers every solid it makes,
    # and making the boxes first gave the fit test's bit of floor other triangles (the same solid)
    plate4[0] += (across_seams(p["floor"]),)
    return {"1 fit test.3mf": fit_3mf, "2 all plates.3mf": all_plates}


def main():
    p = build()
    pp = print_parts(p)
    write_stl(pp["floor"], "floor.stl")
    for name in WALL_CUTS:
        write_stl(union(pp[name]), name + ".stl")
    write_stl(union(pp["porch gable"]), "porch gable.stl")
    write_stl(pp["porch frame"], "porch frame.stl")
    write_stl(pp["porch ceiling"], "porch ceiling.stl")
    write_stl(pp["porch post"], "porch post.stl")
    write_stl(pp["side railing"], "side railing.stl")
    write_stl(pp["front railing"], "front railing.stl")
    write_stl(pp["upper roof"], "upper roof.stl")
    write_stl(pp["lower roof"], "lower roof.stl")
    write_stl(pp["loft"], "loft.stl")
    write_stl(pp["door"], "door.stl")
    write_stl(p["skids"], "skids.stl")
    write_stl(stacked(pp["corner angles"]), "corner angle.stl")
    write_stl(on_bed(fit_test({n: p[n] for n in WALL_CUTS}, p["floor"])), "fit test.stl")
    for name, pl in plates(p).items():
        write_3mf(name, pl)
    for name in list(WALL_CUTS) + ["porch gable"]:
        siding, trim = pp[name]
        bb = union([siding, trim]).bounding_box()
        print(f"{name:12s} flat {bb[3]-bb[0]:7.2f} x {bb[4]-bb[1]:7.2f} x {bb[5]-bb[2]:6.2f} mm  " +
              ("no trim" if trim.is_empty() else
               f"trim {trim.volume()/1000:5.3f} cm3, from {trim.bounding_box()[2]:.2f} mm up"))
    for k in ("floor", "loft", "upper roof", "lower roof", "porch frame", "porch ceiling", "porch post",
              "side railing", "front railing", "door", "skid"):
        v = pp[k]
        bb = v.bounding_box()
        print(f"{k:12s} {bb[3]-bb[0]:7.2f} x {bb[4]-bb[1]:7.2f} x {bb[5]-bb[2]:6.2f} mm  "
              f"{v.volume()/1000:6.2f} cm3  {v.num_tri()} triangles")
    bb = pp["corner angles"][0][1].bounding_box()
    print(f"{'angle':12s} {bb[3]-bb[0]:7.2f} x {bb[4]-bb[1]:7.2f} x {bb[5]-bb[2]:6.2f} mm")
    print("dropped layout marks:", DROPPED_MARKS)


if __name__ == "__main__":
    main()
