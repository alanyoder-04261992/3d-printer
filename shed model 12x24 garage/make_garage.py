"""12x24 Garage, 1:36 scale, for the Flashforge AD5X.

Run:  python3 make_garage.py      (needs: pip install manifold3d numpy)

Makes the print files in this folder:
  1 fit test.3mf    to try first: plate 1 a full-height half roll-up doorway with its half roll-up
                    door, alone, which go in and out like the real ones; plate 2 the corner where the
                    plain side meets the roll-up end, short, with its bit of floor and stubs of corner
                    angle and outer skid, and a short in-swing doorway, its door and a roof peg
  2 all plates.3mf  everything, one plate per print, the trim, roof and corner angles already set
                    to filament 2, the floor and skids to filament 3
  floor.stl         floor frame and floor sheets, printed upside down; the walls snap onto it
  door side.stl     the long wall with the steel door (near the roll-up end) and the window,
                    framing, trim; prints lying flat, inside face down, so the trim is the top
                    few layers
  plain side.stl    the other long wall, the same way; it has no trim
  roll-up end.stl   the gable end with the 8 ft roll-up doorway, its vent and roof pegs
  roll-up curtain.stl  the roll-up door: a white curtain with a black latch plate and a black lift
                    handle at the bottom middle. It hangs in the doorway on springs and lifts out
                    the front by its handle, with the roof on (Alan, Nov 3 2026)
  back end.stl      the other gable end, with its vent and roof pegs
  roof half.stl     print TWO. Each half lifts straight off its three pegs.
  corner angle.stl  the four black L angles glued over the corners, two of each hand
  door.stl          the white six-panel steel door with its knob and hinge pins; it swings in
  skids.stl         the four 4x6 skids the floor frame sits on: two notched inner ones, two
                    flat-topped outer ones
  fit test.stl      both fit test plates, all one colour

Sizes are the shop standard from the 3D designer (library/manufacturers/standard.json, style
G) with Alan's own numbers where he gave them: 12x24 at the actual 134 in (11 ft 2 in) width,
7 ft 9 1/2 in walls (89 in studs and three plates), 5/12 roof, 4 in eaves measured level, an
8 x 6.4 ft roll-up centred on one end, louvred vents in both gables, four 4x6 skids. The door
side is laid out by Alan's standard (designer-standards.js on yoder-storage-barns.com, Nov 3
2026): the 36 in in-swing steel door on the roll-up end of the long wall, its near edge 4 ft in
from the corner (centre 6.5 ft from the middle), and the 2.1 x 2.9 ft window centred between the
door and the back end (3.5 ft from the middle). The wall and floor section is the base models'
(shed and barn, 1:24), held at the same millimetres: the snap joint, the corner angles and the
layer lines are the ones proven in print (Nov 2026).

Axes for the assembled garage: x across the 134 in width (the door side at +x), y along the
24 ft length (the roll-up end at -y, the back end at +y), z up. z = 0 is the bottom of the
floor joists (where the body sits on the skids). Every number is millimetres on the model.
"""

import math
import os
import struct

import numpy as np
import manifold3d as m3

M = m3.Manifold
HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "12x24 Garage 1:36"

# Tags on the numbers: CONFIRMED (Alan's), BARNWRIGHT (the 3D designer's, not yet confirmed by
# Alan), DERIVED (worked out; from what), ASSUMED (our choice; why).

# ---------------------------------------------------------------- scale
S = 25.4 / 36          # mm on the model per real inch (1:36; at 1:32 the 24 ft would be 228.6 mm)
FT = 12 * S

# ---------------------------------------------------------------- the building
W = 134 * S            # 94.544  CONFIRMED: the 12-wide is 134 in (11 ft 2 in) actual (Alan, Sep 30 2026)
L = 24 * FT            # 203.2   CONFIRMED: 12x24 (Alan, Nov 3 2026)
PITCH = 5 / 12         # CONFIRMED (styles.G.built, Oct 11 2026)
ALPHA = math.atan(PITCH)
EAVE = 4 * S           # CONFIRMED: 4 in level overhang past the long walls
RAKE = 0.45 * FT       # BARNWRIGHT: 5.4 in past each gable end

TS = 1.4               # siding (held, F4: thicker than scale so it prints solid)
SD = 3.5 * 25.4 / 24   # 3.704 stud depth, held at the base models' 1:24 millimetres (F4)
SW = 1.5 * S           # 1.058 stud, joist and plate width in the wall plane, true to scale
WT = TS + SD           # 5.104 whole wall
RIM = 5.0              # solid band round the edge of the floor, under the walls (held)
JOIST_H = 5.5 * 25.4 / 24   # 5.821 floor joist depth, held (F4)
DECK = 1.0             # floor sheets
ZF = JOIST_H + DECK    # 6.821 top of the floor
FLOOR_CLR = 0.4        # gap between the floor's edge and the siding that hangs down over it
WALL_H = 93.5 * S      # CONFIRMED: floor to top of the top plates, 89 in studs + three plates
ZWT = ZF + WALL_H      # 72.790 top of the walls
ZPK = ZWT + (W / 2) * PITCH   # 92.487 peak of the roof underside (DERIVED: 27.92 in over the plates)

PLATE_TOP = 3.0 * S    # double top plate, true
PLATE_BOT = 1.6        # bottom plate, held (its own number now, no longer SW; F4)
HEADER = 5.0 * S       # CONFIRMED: Alan's usual 5 in loft header over the steel door
CHORD = 5.5 * S        # CONFIRMED: 2x6 truss chords on a building wider than 10 ft (Oct 1 2026)
GROOVE_OC = 8 * S      # siding grooves 8 in apart
GROOVE_W, GROOVE_D = 0.5, 0.35
TRIM = 3.5 * S         # CONFIRMED: 1x4 trim boards round every opening (Oct 12 2026)
PROUD = 0.6            # how far trim stands off the siding (layers: 5.05 to 5.65)
EMBED = 0.4            # trim and window parts reach this far into the siding, so they join it
VENT_DEPTH = WT - 4.25 # the gable vent's louvres sit in a recess this deep in the siding: its floor
                       # is on the 4.25 layer line with 3 layers of siding under it (Alan, Nov 3
                       # 2026: flush, nothing out past the siding)
VENT_SLAT = 0.45       # height of each louvre's front edge, at the siding face
VENT_LOUVRES = 4       # DERIVED: 4 at 1:36 (the designer draws 5; with 5 the slats print under a line)
VENT_BACK_GAP = 0.45   # each louvre leaves this under the next at the back (F6; the shed had 0.3)

# steel door d36in (BARNWRIGHT: 36 x 75.6 in, always white, in-swing, knob on the right from outside
# so hinged on the left, -y). Where: CONFIRMED, Alan's standard (designer-standards.js on
# yoder-storage-barns.com, his copy-this-build codes, Aug 2026; read Nov 3 2026): on the roll-up
# end of the door side, its near edge 4 ft in from the corner, pos -(L/2 - 5.5) = -6.5 ft
DOOR_YC = -(L / 2 - 5.5 * FT)   # -55.033 (the spec's +7.6 ft was the designer's stock layout)
DOOR_OPEN_W = 36 * S
DOOR_OPEN_H = 75.6 * S
DOOR_Y0, DOOR_Y1 = DOOR_YC - DOOR_OPEN_W / 2, DOOR_YC + DOOR_OPEN_W / 2
DOOR_R = 1.0           # half the door's thickness; the hinge edge is rounded to this (held)
DOOR_T = 2 * DOOR_R
DOOR_GAP = 0.35        # gap at hinge and latch edges
DOOR_AXIS_U = 1.6      # hinge pin line out from the wall's INSIDE face (F7): the 2.7 holes reach down
                       # to u 0.25, the top of the first layer, so the wall's bed face stays whole
AXIS_X = W / 2 - WT + DOOR_AXIS_U
AXIS_Y = DOOR_Y0 + DOOR_R + DOOR_GAP
DOOR_W = (DOOR_Y1 - DOOR_GAP) - AXIS_Y   # pin line to latch edge
DOOR_BOTTOM_GAP = 0.3
DOOR_TOP_GAP = 0.6
DOOR_H = DOOR_OPEN_H - DOOR_BOTTOM_GAP - DOOR_TOP_GAP
PIN_D = 2.0
PIN_HOLE_D = 2.7       # 0.35 mm round the pin: holes print small (Alan, Oct 31 2026)
PIN_BOTTOM_LEN = 1.3   # rests on the bottom of a 1.0 deep hole
PIN_TOP_LEN = 2.0
HOLE_BOTTOM_DEPTH = 1.0
TRENCH_DEPTH = 0.7     # the slot the bottom pin swings out along, from the wall's inside face
HOLE_TOP_DEPTH = 2.2
# the stop on the latch jamb, outside the door, in (distance into the opening from the jamb face,
# u): a 45 degree underside from the 2.45 layer line, 0.2 clear of the shut door's outside face at
# its latch edge, overlapping it 0.45 (F7)
STOP_POLY = [(0.0, 2.45), (0.8, 3.25), (0.8, WT), (0.0, WT)]
PANEL_COLS = ((0.170, 0.435), (0.565, 0.830))   # BARNWRIGHT door-steel.js, of the opening width
PANEL_ROWS = ((0.064, 0.300), (0.369, 0.758), (0.822, 0.945))   # and of its height, from the floor
PANEL_GROOVE_W, PANEL_GROOVE_D = 0.5, 0.4
KNOB_D, KNOB_H = 1.8, 1.2
KNOB_IN = 0.32 * FT    # BARNWRIGHT: knob 0.32 ft in from the latch edge
KNOB_UP = 0.44         # at 0.44 of the door's height

# window w23 (BARNWRIGHT: 2.1 x 2.9 ft clear opening); top 76.5 in above the floor, under Alan's
# utility window plate (DERIVED: 90.5 - 12.5 - 1.5; open question 6). Where: CONFIRMED, Alan's
# standard (designer-standards.js, as the door): centred between the steel door and the back end,
# pos +3.5 ft on the door side
WIN_YC = 3.5 * FT      # +29.633 (the spec's -7.6 ft was the stock layout)
WIN_W = 2.1 * FT
WIN_H = 2.9 * FT
WIN_TOP = 76.5 * S
WIN_Y0, WIN_Y1 = WIN_YC - WIN_W / 2, WIN_YC + WIN_W / 2
WIN_Z0, WIN_Z1 = ZF + WIN_TOP - WIN_H, ZF + WIN_TOP
WIN_PLATE = 1.5 * S    # CONFIRMED: one flat 2x4 window plate, its top 12.5 in under the top plates

# roll-up ru8 (BARNWRIGHT: 8 x 6.4 ft, centred on the roll-up end, sill at the floor), framed by
# Alan's garage-door arrangement: king studs to the top plates, no header (CONFIRMED). Its curtain
# is a separate white part that lifts out the front by a handle at the bottom middle (CONFIRMED,
# Alan Nov 3 2026: "Do 4 the lift out add a handle in the bottom middle to lift it up"; he picked
# the front lift-out the same day). The numbers are spec_rollup.md's final ones, shared with the
# Lofted Barn Garage. Below, u is out from the roll-up end's inside face (0 the inside face, WT the
# siding face; both the end wall and the curtain print with u up), x along the wall (+x the latch
# side, right from outside), z up from the joists' bottoms.
RU_W = 8 * FT          # 67.733
RU_H = 6.4 * FT        # 54.187
MOUTH = ZF + RU_H      # 61.008 the opening's top
RU_FACE = 4.85         # the slats' face, a layer line, 0.36 in behind the siding (the shut spec's)
SLAT_PITCH = 2.25 * S  # BARNWRIGHT: 2 1/4 in slats
SLAT_START = 0.22 * FT # the first slat's bottom
SLATS = 32
SLAT_GROOVE_W, SLAT_GROOVE_D = 0.5, 0.4   # held at a line wide; the groove floor prints on 4.45
RU_CLR_X = 0.30        # ASSUMED: the curtain's side gap to each jamb (PRINTER-BRAIN: 0.25-0.3 = easy fit)
CUR_HALF = RU_W / 2 - RU_CLR_X   # 33.567 DERIVED: the curtain 95.15 in wide overall
CUR_CHAMF = 1.25       # ASSUMED: 45 degree chamfer on its two back edges, which bear on the jamb stops
CHAMF_TOP = 56.0       # ASSUMED: the chamfers end here; square above, so the springs' root blocks stand
                       # on their whole footprint (6 over STOP_TOP)
CUR_STOP_GAP = 0.05    # ASSUMED (spec_rollup.md's STOP_GAP; renamed here, the prongs have their own STOP_GAP):
                       # drawn gap from each chamfer to its jamb stop; the tabs close it
STOP_X0 = CUR_HALF - CUR_CHAMF + CUR_STOP_GAP   # 32.367 DERIVED: each jamb stop's slope starts here at u 0
STOP_TOP = 50.0        # ASSUMED: the stops end low enough that the top can lean in going back in
STOP_RELIEF_X, STOP_RELIEF_U = 0.45, 0.25   # ASSUMED (found building it, Nov 3 2026, widened after review, and set
                       # to the Lofted Barn Garage's RU_STOP_FOOT 0.45 when the two were reconciled, Nov 4 2026): each
                       # stop's first layer (to its 0.25 line) stands back square 0.45 from the slope's foot, 0.1 behind
                       # the second layer's edge, so the printed curtain's first layer clears it at every print accuracy
                       # tried, with 0.125 to spare even pushed sideways, and seats as spec_rollup.md H.1 says
SHADE = 2.2            # ASSUMED: the dark slit under the head, 3.1 in (the designer's shade band is
                       # 0.18 ft = 1.524, BARNWRIGHT; open question 17): room to rise and tip under the head
Z_FT = MOUTH - SHADE   # 58.808 DERIVED: the slatted body's top
CH_TOP = 1.0           # ASSUMED: 45 degree bevel on the body's top front edge, in the slit
TONGUE_T, TONGUE_UP = 1.05, 1.8   # ASSUMED: the tongue along the curtain's back, u 0..1.05 (5 layers), 1.8 over
Z_TT = MOUTH + TONGUE_UP          # 62.808 DERIVED: the tongue's top   the opening top (2.55 in)
REB_U, REB_H = 1.65, 3.4          # ASSUMED: the rebate in the head's inside face, u 0..1.65 (a layer line, 0.6
                                  # in front of the tongue), z MOUTH..64.408; its top is the rigid lift stop
RIB_XS, RIB_W, RIB_CLR = (0.0, -14.5, 14.5), 1.2, 0.3   # ASSUMED: three ribs across the rebate hold its
                                  # ceiling's bridges; the tongue is notched RIB_CLR round them
FING_ROOT, FING_TIP = 32.3, 15.4  # ASSUMED: each spring finger, from its root near the jamb in to its free end
FING_H = 1.26                     # ASSUMED: 3 lines tall
FING_SLOT = 2.74                  # ASSUMED: the slot under it, from the finger down to the body's top (Z_TT - FING_H
                                  # - Z_FT); more cuts into the body's top (the tuning table's spring row)
FING_RADIUS = 0.5                 # ASSUMED: in both root corners of the slot
BUMP_X0, BUMP_X1, BUMP_H, BUMP_U = 15.8, 17.6, 0.6, 1.25   # ASSUMED: the bump on each finger, 3 lines tall,
                                  # u 0..1.25, one layer deeper than the tongue
PAD_X0, PAD_X1, PRELOAD = 16.0, 16.7, 0.55   # ASSUMED: a pad over each bump presses its finger down 0.55. Its
                                  # root-side edge is at the bump's middle (changed after review from spec_rollup.md's
                                  # 17.4): the bent finger slopes about 12 degrees at the stop, so the flat pad bears on
                                  # the bump only along that edge, and there it is 15.6 from the finger's root, where the
                                  # spec's finger numbers (rate, strain, tip) were worked out
PAD_Z = Z_TT + BUMP_H - PRELOAD   # 62.858 DERIVED: the pads' bottom
TAB_TIP, TAB_ROOT, TAB_GAP = 3.0, 12.6, 0.6   # ASSUMED: each top tab from its free end to its root (9.6 long),
                                  # and the gap at its free end
TAB_T, TAB_W, TAB_SLOT = 0.65, 2.2, 0.6   # ASSUMED: the tab's plate u 0..0.65 (the curtain's first 3 layers),
                                  # z 60.608..62.808, a 0.6 slot under it
TAB_BUMP_X0, TAB_BUMP_X1, TAB_BUMP_U, TAB_BUMP_TOP = 3.0, 4.2, 1.85, 0.8   # ASSUMED: the tab's bump, u 0.65..1.85,
                                  # 0.2 into the rebate front (set by layers); its flat top 0.8 tall
LIP_H, LIP_U0 = 0.666, 3.65       # ASSUMED: the white threshold lip, 0.94 in (the diamond plate is 0.055 ft =
                                  # 0.466, BARNWRIGHT; open question 16); its 45 degree wedge's foot on a layer line
G_BOT, WEDGE_GAP = 0.2, 0.05      # ASSUMED: the curtain's bottom 0.2 over the floor top; drawn gap to the wedge
BOT_U = 4.25                      # ASSUMED: the bottom zone's front face (a layer line)
RAIL_Z0 = ZF + LIP_H + 0.2        # 7.687 DERIVED: the bottom rail's bottom, 0.2 over the lip
RAIL_TOP = ZF + 0.225 * FT        # 8.726 BARNWRIGHT: the rail's top 0.225 ft up
RAIL_FACE = 5.05                  # the rail stands 0.2 proud of the slats (the shut spec's)
# posts under the curtain, into notches in the floor's end band: the middle, 16 in and 35 in each way
# (ASSUMED, the same on both garages; the skirt between them and the end-stud posts spans 15.9 mm at
# most). They carry on POST_EXT_U deep up to the lip's top; the curtain is notched round them
CURTAIN_POSTS = (0.0, -16 * S, 16 * S, -35 * S, 35 * S)
POST_EXT_U = 4.65
POST_NOTCH_CLR = 0.3
# the lift handle, black, at the bottom middle of the rail (place CONFIRMED, Alan; size ASSUMED, open
# question 15): 16 in wide, legs 3.0 wide, 2.8 in tall; about 2.7 times a real one so a fingernail goes
# behind it. Legs u 5.05..6.65 (the nail gap), grip 6.65..8.25. A stepped 45 degree fillet round each
# leg on the 5.05, 5.25 and 5.45 layers (22 N at 10 MPa on every layer)
HDL_HALF, HDL_LEG, HDL_HT = 8 * S, 3.0, 2.0
HDL_U1, HDL_U2 = 6.65, 8.25
HDL_Z0 = RAIL_Z0
HDL_FILLET = (0.3, 0.2, 0.1)
HDL_BOSS_HALF = HDL_HALF + HDL_FILLET[0]          # 5.944 DERIVED: the handle's white boss, the rail carried up over the
HDL_BOSS_TOP = RAIL_Z0 + HDL_HT + HDL_FILLET[0]   # 9.987 first slat under the handle and its fillet
CUR_WEIGHT_G = 11.68   # the curtain's weight, from the addendum's review test slice (11.55 g white, 0.13 g black).
                       # DERIVED (used for the holds); sliced again Nov 3 2026: 11.54 + 0.13 g
STUB_WEIGHT_G = 6.30   # the fit test's half door, sliced alone (Nov 3 2026: 6.19 g + 0.12 g): a little over half the
                       # real door, as its handle is full size. DERIVED (used for its hold)
LATCH_W, LATCH_H, LATCH_CUT = 0.72 * FT, 0.38 * FT, 0.075 * FT
LATCH_SLOT_W, LATCH_SLOT_H = 0.32 * FT, 0.09 * FT
LATCH_X = RU_W / 2 - 0.62 * FT   # BARNWRIGHT: 0.62 ft in from the right edge seen from outside (+x)
LATCH_Z = ZF + 0.42 * RU_H       # at 0.42 of the height
LATCH_T = 0.4          # the black plate on the curtain: 2 layers, 5.05 to 5.45 as printed

# roof
ROOF_T = 2.0
RIB_OC = 9 * S         # ribs 9 in apart (33 of them)
CAP_T = 1.8            # ridge cap thickness (held)
CAP_RUN = 5.2 * S      # how far it runs down each slope (5.2 in, as the base's)
PEG_D, PEG_UP = 2.2, 1.0
PEG_HOLE_D, PEG_HOLE_UP = 3.0, 1.4   # 0.4 mm round the peg and over it
PEG_X = W / 4          # the gable pegs, on the top chords
PEG_Y = L / 2 - WT + PEG_D / 2   # against the end walls' inside face, so each peg prints lying on the bed
MID_PEG_X = W / 2 - WT + PEG_D / 2   # a peg on each long wall's top plates at mid-length
MID_PEG_ROOT = 0.65    # how far it reaches down into the top plates
ROOF_PEGS = [(PEG_X, PEG_Y), (PEG_X, -PEG_Y), (MID_PEG_X, 0.0)]   # for the +x half

# skids: treated 4x6 on edge, four, centres 8 and 37 in in from each side (BARNWRIGHT skid table)
SKID_W = 3.5 * S
SKID_H = 5.5 * S
NOTCH = 0.6
NOTCH_CLEAR = 0.6      # 0.3 mm each side of a joist
SKID_X = W / 2 - 37 * S          # 21.167 the inner pair, under the joist pockets
OUTER_SKID_X = W / 2 - 8 * S     # 41.628 the outer pair, under the long-side rim band
OUTER_SKID_H = SKID_H - NOTCH    # flat-topped at z = 0, so all four bottoms are level
SKID_PEG_D, SKID_PEG_UP = 2.0, 2.5   # a peg at each end of an inner skid pushes into the end band
OUTER_PEG_D = 1.6                # two pegs per outer skid into the long-side rim band
OUTER_PEG_HOLE_D, OUTER_PEG_HOLE_UP = 2.0, 2.8
OUTER_PEG_X = 41.95              # DERIVED: 0.32 outward of the skid's centre, so its hole keeps
                                 # 0.48 of floor to the joist pocket
OUTER_RELIEF = 0.3               # under each long-wall prong, so its barb and leg never touch
OUTER_RELIEF_U = -0.4            # from 0.4 inside the long wall's inside face outward

# snap joints, no glue (Alan, Nov 1 2026), the base models' exactly (F4). Each wall stands on top
# of the floor with its siding hanging down over the floor's edge. Under every stud a post drops
# into a notch in the floor's edge, and a few prongs click into slots in the floor. A prong is a
# springy leg with a barb on its foot that catches under a ledge at the bottom of the slot, and
# beside it a stiff stop that keeps the wall's foot from moving out. The barb is built up from the
# bed in layers. The end walls go on first, the long walls last.
FIT = 0.2              # gap round every post, prong and peg (0.2 a side is snug)
PRONG_W = 3.0          # the leg's width along the wall
PRONG_T = 0.8          # its thickness, the way it bends (4 layers)
BARB = 0.65            # the barb stands this far in from the leg, down to the bed (3 layers)
CATCH = BARB - FIT     # how far it hooks under the ledge
BARB_LAND = 0.6        # straight face between the barb's flat top and its 45 degree lead-in
LEDGE_Z = ZF - 5.25    # the ledge, on the 5.25 layer line of the upside-down floor
STOP_W, STOP_GAP, STOP_H = 1.2, 0.4, 3.0   # the stop: width, gap from the leg, how far down it goes
STOP_U = 2.05          # how deep the stop is, on a layer line of the wall's print
SLOT_U = STOP_U + 0.15 # the slot's outside wall
LEG_ROOT = ZF + 1.2    # the leg is freed from the bottom plate (or the curtain) up to here: 6.65 long
BARB_RELIEF = 0.1      # the barb's top is this much lower on its first layer, for first-layer squish
MITRE_GAP = 0.1        # relief between mitred ends, so they slide past each other going on
# where the prongs are (DERIVED, spec 4.1): between studs and between floor joists, clear of the
# door's sill post, the window, the curtain posts and the skids' pegs. On each long wall one bay in
# from each end and one in the bay 0 to 16 in (its stop toward +y); on the roll-up end under the
# jambs, 51.3 in each way, the legs rooted in the bottom plate beside the doorway (ASSUMED,
# spec_rollup.md E.5: under the lift-out curtain nothing may hang); on the back end in the -x corner
# bay and, the +x corner bay being only 4.2 mm between notches, in the next one. With the door at
# -6.5 ft (Alan's standard) the door side's three still fit: -120 in is between the -128 and -112 in
# studs, its slot 12.9 mm from the door's sill-post notch; +120 in now between the 112 and 128 in
# studs, as on the plain side.
PRONGS = {"door side": (-120 * S, 8 * S, 120 * S),
          "plain side": (-120 * S, 8 * S, 120 * S),
          "roll-up end": (-36.2, 36.2),
          "back end": (-36.519, 29.544)}

# corner angles (Alan, Nov 3 2026), the base models' with F5's reach. Each mitred corner gets a
# separate black L angle, printed on the roof plate, glued into a shallow recess in both walls.
POCKET_D = 0.4         # depth of the recess: two layers of the wall's print (4.65 to 5.05)
POCKET_CLR = 0.15      # gap round the angle's edges in the recess
CORNER_CHAMFER = 1.15  # a 45 degree chamfer off the walls' outer corner, square to the mitre
ANGLE_T = 1.05         # thickness of each leg, 5 layers; it stands 0.65 proud
ANGLE_P = ANGLE_T - POCKET_D
ANGLE_FILLET = 0.8     # 45 degree fillet in its inside corner, 0.25 clear of the chamfer as drawn
ANGLE_REACH = 3.0      # ASSUMED (F5): 3.0 along the long wall (4.25 in), wider than the 2.47 trim so
                       # it sits on 1.45 mm of each recess floor instead of 0.9 (open question 9)
ANGLE_UP = 0.25 + 17 * 0.2   # 3.65, the end-face leg, standing up in the print: 18 layers; it
                       # reaches 3.0 along the end wall
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
    """Polygon in two garage axes (ax0, ax1), extruded d along the third axis h from h=0.
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


def chamfered(cx, cz, w, h, c):
    """An outline w x h centred on (cx, cz) with its corners cut c at 45 degrees."""
    x0, x1, z0, z1 = cx - w / 2, cx + w / 2, cz - h / 2, cz + h / 2
    return [(x0 + c, z0), (x1 - c, z0), (x1, z0 + c), (x1, z1 - c), (x1 - c, z1), (x0 + c, z1),
            (x0, z1 - c), (x0, z0 + c)]


# ---------------------------------------------------------------- body
def joist_ys():
    """The floor joists between the solid bands at the ends, 16 in apart from the back end."""
    return layout(-L / 2, L / 2, 16 * S)


# each wall as (axis it faces along, side): along a wall is y for the long walls, x for the ends.
# Alan calls the long walls side walls and the short ones end walls (Sep 28 2026).
WALL_SIDE = {"door side": (0, 1), "plain side": (0, -1), "back end": (1, 1), "roll-up end": (1, -1)}
LONG_WALLS, END_WALLS = ("door side", "plain side"), ("back end", "roll-up end")


def wall_box(name, a0, a1, u0, u1, z0, z1):
    """A box on one wall: a along the wall, u out from its inside face, z up."""
    axis, sign = WALL_SIDE[name]
    half = (W / 2, L / 2)[axis]
    n0, n1 = sorted([sign * (half - WT + u0), sign * (half - WT + u1)])
    return box(n0, n1, a0, a1, z0, z1) if axis == 0 else box(a0, a1, n0, n1, z0, z1)


def wall_section(name, poly, a0, a1):
    """A polygon in (u out from the wall's inside face, z), from a0 to a1 along the wall."""
    axis, sign = WALL_SIDE[name]
    half = (W / 2, L / 2)[axis]
    pts = [(sign * (half - WT + u), z) for u, z in poly]
    t = [0.0, 0.0, 0.0]
    t[1 - axis] = a0
    return prism(pts, axis, 2, 1 - axis, a1 - a0).translate(t)


# ---------------------------------------------------------------- stud layout
def wall_marks(name):
    """The 16 in layout marks along a wall, as coordinates along it (BARNWRIGHT: from each wall's
    left end seen from outside: the door side from -y, the plain side from +y, which give the same
    marks as 288 = 18 x 16; the roll-up end from -x, the back end from +x)."""
    if WALL_SIDE[name][0] == 0:
        return layout(-L / 2, L / 2, 16 * S)
    xs = layout(-W / 2, W / 2, 16 * S)
    return xs if name == "roll-up end" else [-x for x in xs]


def framed_members(name):
    """[(a0, a1, what)] the framing beside each opening on a wall, along it: Alan's king stud (the
    short support under the header) and, outside it, the full-height stud, each side (F8)."""
    out = []
    if name == "door side":
        for y0, y1, what in ((DOOR_Y0, DOOR_Y1, "steel door"), (WIN_Y0, WIN_Y1, "window")):
            out += [(y0 - 2 * SW, y0 - SW, f"the {what}'s hinge-side full stud" if what == "steel door"
                     else f"the {what}'s -y full stud"),
                    (y0 - SW, y0, f"the {what}'s king stud"), (y1, y1 + SW, f"the {what}'s king stud"),
                    (y1 + SW, y1 + 2 * SW, f"the {what}'s latch-side full stud" if what == "steel door"
                     else f"the {what}'s +y full stud")]
    if name == "roll-up end":
        h = RU_W / 2
        out += [(-h - 2 * SW, -h - SW, "the roll-up's -x full stud"), (-h - SW, -h, "the roll-up's -x king stud"),
                (h, h + SW, "the roll-up's +x king stud"), (h + SW, h + 2 * SW, "the roll-up's +x full stud")]
    return out


def openings_on(name):
    """[(a0, a1, z0, z1, kind)] the openings in a wall."""
    if name == "door side":
        return [(DOOR_Y0, DOOR_Y1, ZF, ZF + DOOR_OPEN_H, "door"), (WIN_Y0, WIN_Y1, WIN_Z0, WIN_Z1, "window")]
    if name == "roll-up end":
        return [(-RU_W / 2, RU_W / 2, ZF, ZF + RU_H, "roll-up")]
    return []


def mark_plan(name):
    """[(a, kind, what, overlap)] for each layout mark on a wall. kind is "stud" (a full stud),
    "inside" (in an opening: a cripple over a header, studs over and under a window plate and
    sill, or nothing in the roll-up), or "dropped": its stud would overlap other framing (an end
    stud, the corner past it, an opening's studs), so the framing it hits stands there instead
    (F8; the shed-measurements skill: a collision needs a layout decision, not a hidden shift)."""
    out = []
    axis = WALL_SIDE[name][0]
    corner = W / 2 - WT - SW                                       # an end wall's end studs' inner faces
    for a in wall_marks(name):
        lo, hi = a - SW / 2, a + SW / 2
        if axis == 1 and (hi > corner or lo < -corner):            # on or past an end stud
            out.append((a, "dropped", "the corner (the end stud and the long wall)",
                        min(hi - lo, abs(a) + SW / 2 - corner)))
            continue
        hit = [(min(hi, b1) - max(lo, b0), what) for b0, b1, what in framed_members(name) if hi > b0 and lo < b1]
        if hit:
            ov, what = max(hit)
            out.append((a, "dropped", what, ov))
            continue
        inside = [o for o in openings_on(name) if lo >= o[0] and hi <= o[1]]
        out.append((a, "inside" if inside else "stud", inside[0][4] if inside else "", 0.0))
    return out


def dropped_marks():
    """DROPPED_MARKS: [(wall, mark in inches from the wall's middle, what it hit, overlap in mm)]."""
    return [(name, round(a / S), what, round(ov, 2)) for name in WALL_SIDE
            for a, kind, what, ov in mark_plan(name) if kind == "dropped"]


DROPPED_MARKS = dropped_marks()


def post_spans(name):
    """(start, end) along the wall of each post under it, from z = 0 up to the bottom plate: one
    under every stud on a layout mark, the door side's sill post under the whole door framing, and
    on the roll-up end under the curtain (CURTAIN_POSTS; the jambs have none, their prongs' slots
    are there). A post whose notch would cut into a skid peg's hole moves toward the middle of the
    wall until it keeps 1.3 mm of floor from the hole (the back end's -29 in stud: the skirt
    between its neighbours would otherwise be a 21.5 mm bridge)."""
    axis = WALL_SIDE[name][0]
    marks = [a for a, kind, _, _ in mark_plan(name) if kind in ("stud", "inside")]
    if axis == 0:
        spans = [(a - SW / 2, a + SW / 2) for a in marks]
        if name == "door side":
            d0, d1 = DOOR_Y0 - 2 * SW, DOOR_Y1 + 2 * SW
            spans = [s for s in spans if s[1] < d0 or s[0] > d1] + [(d0, d1)]
        return spans
    xe = W / 2 - WT - SW / 2
    spans = [(-xe - SW / 2, -xe + SW / 2), (xe - SW / 2, xe + SW / 2)]
    if name == "roll-up end":
        return spans + [(x - SW / 2, x + SW / 2) for x in sorted(CURTAIN_POSTS)]
    hole_r = (SKID_PEG_D + 2 * FIT) / 2
    for a in marks:
        for sx in (1, -1):
            hx = sx * SKID_X
            if abs(a - hx) < SW / 2 + FIT + hole_r + 0.6:
                a = hx - math.copysign(1, hx) * (hole_r + 1.3 + FIT + SW / 2)
        spans.append((a - SW / 2, a + SW / 2))
    return spans


def prong_spots(name):
    return list(PRONGS[name])


def prong_spans(ac):
    """(leg, stop): where the leg and the stop of the prong at ac are along the wall. The stop
    is on the side toward the nearer corner."""
    s = 1 if ac >= 0 else -1
    leg = (ac - PRONG_W / 2, ac + PRONG_W / 2)
    stop = sorted([ac + s * (PRONG_W / 2 + STOP_GAP), ac + s * (PRONG_W / 2 + STOP_GAP + STOP_W)])
    return leg, tuple(stop)


def prong_slot(ac):
    """(start, end) along the wall of the slot cut in the floor for the prong at ac."""
    (a0, a1), (b0, b1) = prong_spans(ac)
    return min(a0, b0) - FIT, max(a1, b1) + FIT


def prong(name, ac):
    """The prong at ac along a wall. The leg hangs from the bottom plate BARB off the wall's inside
    face; in the print it bridges from there to its barb, which stands on the bed. The barb's flat
    top catches under the ledge; below it a straight face and a 45 degree lead-in that pushes the
    leg out as it goes down the slot."""
    (a0, a1), (b0, b1) = prong_spans(ac)
    zc = LEDGE_Z - FIT                                  # flat top of the barb, under the ledge
    zl = zc - BARB_LAND - BARB                          # foot of the lead-in
    barb = [(BARB + 0.1, zc), (0.25, zc), (0.25, zc - BARB_RELIEF), (0, zc - BARB_RELIEF),
            (0, zc - BARB_LAND), (BARB, zl), (BARB + 0.1, zl)]
    return [wall_box(name, a0, a1, BARB, BARB + PRONG_T, zl - 0.05, LEG_ROOT + 0.01),
            wall_section(name, barb, a0, a1),
            wall_box(name, b0, b1, 0, STOP_U, ZF - STOP_H, ZF + 0.3)]


def prong_relief(name, ac):
    """The slot round the top of the prong's leg, 0.2 all round, so the leg bends from LEG_ROOT.
    It is inside the bottom plate: the inside face is whole."""
    (a0, a1), _ = prong_spans(ac)
    return (wall_box(name, a0 - 0.2, a1 + 0.2, BARB - 0.2, BARB + PRONG_T + 0.2, ZF - 0.5, LEG_ROOT)
            - wall_box(name, a0, a1, BARB, BARB + PRONG_T, ZF - 1, LEG_ROOT + 1))


def under_floor(name):
    """What a wall has below the top of the floor besides its siding: the posts and prongs."""
    parts = [wall_box(name, a0, a1, 0, SD + EMBED, 0, ZF + 0.3) for a0, a1 in post_spans(name)]
    for ac in prong_spots(name):
        parts += prong(name, ac)
    return parts


def outer_peg_spots():
    """(x, y) of the outer skids' pegs: in each long wall's end bay, between the post notch at the
    128 in mark and the floor's corner cut, 1.1 of floor each side."""
    y_in = joist_ys()[-1] + SW / 2 + FIT
    y_out = L / 2 - WT - SW - FIT
    y = (y_in + y_out) / 2
    return [(sx * OUTER_PEG_X, sy * y) for sx in (1, -1) for sy in (1, -1)]


def floor_cuts():
    """The notches, slots and holes in the floor: a notch round each post and the door sill, a
    slot for each prong (room for the leg to bend out as the barb goes down, the ledge with the
    undercut the barb springs into, and a closer fit round the stop), the corners where the
    corner posts go down, a hole in each end band for an inner skid's peg, and two in each long
    rim band for an outer skid's pegs. No groove for the door's pin (F7)."""
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
    for x, y in outer_peg_spots():
        cuts.append(cyl_z(x, y, -1, OUTER_PEG_HOLE_UP, OUTER_PEG_HOLE_D))
    return cuts


def long_wall_framing(name):
    """Plates, studs and the framing round the steel door and the window on a long wall, by
    Alan's doorway rules (F8): beside each opening a full-height stud and, inside it, his king
    stud under the header; the steel door's header his 5 in loft header, bearing 1 1/2 in on each
    king; over the window his flat window plate, its top 12 1/2 in under the top plates, and a
    rough sill under the opening; studs on the layout marks fill above both and under the sill."""
    yin = L / 2 - WT               # inside face of the end walls
    z0s, z1s = ZF + PLATE_BOT, ZWT - PLATE_TOP

    def fb(a0, a1, z0, z1):
        return wall_box(name, a0, a1, 0, SD, z0, z1)
    parts = [fb(-yin, yin, ZF, z0s), fb(-yin, yin, z1s, ZWT),
             fb(-yin, -yin + SW, z0s, z1s), fb(yin - SW, yin, z0s, z1s)]           # plates, end studs
    tops = {}
    for y0, y1, oz0, oz1, kind in openings_on(name):
        parts += [fb(y0 - 2 * SW, y0 - SW, z0s, z1s), fb(y1 + SW, y1 + 2 * SW, z0s, z1s),   # full studs
                  fb(y0 - SW, y0, z0s, oz1), fb(y1, y1 + SW, z0s, oz1)]                    # king studs
        if kind == "door":
            parts.append(fb(y0 - SW, y1 + SW, oz1, oz1 + HEADER))
            tops[kind] = (oz1 + HEADER, None)
        else:
            parts += [fb(y0 - SW, y1 + SW, oz1, oz1 + WIN_PLATE),                       # window plate
                      fb(y0, y1, oz0 - SW, oz0)]                                         # rough sill
            tops[kind] = (oz1 + WIN_PLATE, oz0 - SW)
    for a, kind, what, _ in mark_plan(name):
        lo, hi = a - SW / 2, a + SW / 2
        if kind == "stud":
            parts.append(fb(lo, hi, z0s, z1s))
        elif kind == "inside":
            over, under = tops[what]
            parts.append(fb(lo, hi, over, z1s))
            if under is not None:
                parts.append(fb(lo, hi, z0s, under))
    return parts


CHORD_V = CHORD / math.cos(ALPHA)   # the top chords' depth measured up and down
VENT_W, VENT_H = 1.12 * FT, 0.76 * FT   # BARNWRIGHT gable-vent.js
VENT_ZC = ZPK - 0.92 * FT               # centred 0.92 ft under the ridge
GABLE_STUD_MIN = 0.05 * FT              # gable studs shorter than this are left out


def gable_stud_plan(name):
    """[(x, bottom, top)] of each gable stud on an end wall's own marks, standing on the bottom
    chord and cut under the top chords (or at the vent's sill where it crosses the vent); one
    shorter than GABLE_STUD_MIN is left out."""
    out = []
    z_bot = ZWT + CHORD
    sill = VENT_ZC - VENT_H / 2 - SW
    for a, kind, _, _ in mark_plan(name):
        if kind == "dropped":
            continue
        lo, hi = a - SW / 2, a + SW / 2
        top = zline(max(abs(lo), abs(hi))) - CHORD_V
        if hi > -VENT_W / 2 - SW and lo < VENT_W / 2 + SW:
            top = sill
        if top - z_bot >= GABLE_STUD_MIN:
            out.append((a, z_bot, top))
    return out


def end_wall_framing(name):
    """An end wall: plates, end studs and studs on its own marks to the top plates (on the roll-up
    end, Alan's garage-door framing: king studs and full studs to the top plates, no header, the
    bottom plate stopping at the king studs); above it the end truss: the 2x6 bottom chord on
    edge on the top plates, gable studs on the same marks standing on it, a king each side of the
    vent and a flat sill under it, and the 2x6 top chords under the roof line. Everything runs the
    full stud depth, so the wall prints lying flat on it."""
    xin = W / 2 - TS
    z0s, z1s = ZF + PLATE_BOT, ZWT - PLATE_TOP

    def fb(a0, a1, z0, z1):
        return wall_box(name, a0, a1, 0, SD, z0, z1)
    parts = [fb(-xin, xin, z1s, ZWT)]
    if name == "roll-up end":
        h = RU_W / 2
        parts += [fb(-xin, -h, ZF, z0s), fb(h, xin, ZF, z0s),
                  fb(-h - 2 * SW, -h, z0s, z1s), fb(h, h + 2 * SW, z0s, z1s)]           # full + king studs
    else:
        parts.append(fb(-xin, xin, ZF, z0s))
    xe = W / 2 - WT - SW / 2           # end studs just inside the long walls, so each mitred end
    for xc in (-xe, xe):               # rests on a stud's width on the bed
        parts.append(fb(xc - SW / 2, xc + SW / 2, z0s, z1s))
    for a, kind, _, _ in mark_plan(name):
        if kind == "stud":
            parts.append(fb(a - SW / 2, a + SW / 2, z0s, z1s))
    # the end truss
    parts.append(fb(-xin, xin, ZWT, ZWT + CHORD))                                         # bottom chord
    for a, z0, z1 in gable_stud_plan(name):
        parts.append(fb(a - SW / 2, a + SW / 2, z0 - 0.01, z1 + 0.01))
    sill_z0 = VENT_ZC - VENT_H / 2 - SW
    for sx in (1, -1):                                                                     # vent kings
        xa, xb = sorted([sx * VENT_W / 2, sx * (VENT_W / 2 + SW)])
        parts.append(fb(xa, xb, ZWT + CHORD - 0.01, ZPK))
    parts.append(fb(-VENT_W / 2, VENT_W / 2, sill_z0, sill_z0 + SW))                      # vent sill
    side = WALL_SIDE[name][1]
    yi, yo = sorted([side * (L / 2 - WT), side * (L / 2 - TS)])
    band = prism_xz([(-W / 2, ZWT - CHORD_V), (0, ZPK - CHORD_V), (W / 2, ZWT - CHORD_V),
                     (W / 2, ZWT), (0, ZPK), (-W / 2, ZWT)],
                    yi - (0.2 if side < 0 else 0), yo + (0.2 if side > 0 else 0))   # 0.2 into the siding so they join
    parts.append(band)
    gable_shape = prism_xz([(-W / 2, 0), (W / 2, 0), (W / 2, ZWT), (0, ZPK), (-W / 2, ZWT)], -L, L)
    return union(parts) ^ gable_shape


def window_unit():
    """Double-hung window inside its opening on the door side: two sashes and their muntins, no
    glass, so you can see in (Alan, Oct 31 2026). The sash frames reach 0.2 mm into the jambs so
    they join the wall."""
    y0, y1, z0, z1, yc = WIN_Y0, WIN_Y1, WIN_Z0, WIN_Z1, WIN_YC
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


def slat_lines():
    """z of the line between each pair of the roll-up's slats (a groove on each)."""
    return [ZF + SLAT_START + k * SLAT_PITCH for k in range(1, SLATS)]


# ---------------------------------------------------------------- the roll-up's lift-out curtain
RU = "roll-up end"


def ru_y(u):
    """y of the plane u out from the roll-up end's inside face."""
    return -(L / 2 - WT + u)


def ru_box(x0, x1, u0, u1, z0, z1):
    """A box on the roll-up end: x along it, u out from its inside face, z up."""
    return wall_box(RU, x0, x1, u0, u1, z0, z1)


def ru_uz(poly, x0, x1):
    """A polygon in (u, z) on the roll-up end, from x0 to x1 along it."""
    return wall_section(RU, poly, x0, x1)


def ru_xu(poly, z0, z1):
    """A polygon in (x, u) on the roll-up end, from z0 to z1."""
    return prism([(x, ru_y(u)) for x, u in poly], 0, 1, 2, z1 - z0).translate([0, 0, z0])


def ru_xz(cs, u0, u1):
    """A cross-section in (x, z) on the roll-up end, from u0 to u1 out from its inside face."""
    return M.extrude(cs, u1 - u0).transform(np.array([[1, 0, 0, 0], [0, 0, -1, ru_y(u0)], [0, 1, 0, 0]], dtype=float))


def mirrored_pair(make):
    """make(sign) for the +x and the -x side."""
    return [make(1), make(-1)]


def xspan(sign, a, b):
    """The span a..b (0 < a < b) on the sign side of the middle, low to high."""
    return tuple(sorted([sign * a, sign * b]))


def drum_box():
    """The roll-up's drum box, framing between the king studs from the opening's top to the top
    plates (13.7 in, the door's coil box; ASSUMED), the full stud depth: the siding and head casing
    over the opening rest on it. The rebate for the curtain's tongue comes out of its bottom."""
    h = RU_W / 2
    return ru_box(-h - 0.2, h + 0.2, 0, SD, MOUTH - 0.01, ZWT - PLATE_TOP + 0.01)


def jamb_stops():
    """A 45 degree stop up the inside of each jamb, behind the curtain's chamfered back edges, from
    the floor top to STOP_TOP, 0.01 into the king stud so it joins it (spec_rollup.md E.4). Its foot
    on the bed, its first layer (to STOP_RELIEF_U), is cut back square STOP_RELIEF_X from the slope's
    foot, then steps out onto the slope, the second layer's edge 0.1 out from the first's (a 27 degree
    step): as printed, the stop's and the curtain's first layers
    (0.25 thick, where every other layer is 0.2) overlap in a band just inside the chamfer unless the
    stop stands back further than the two parts grow between them, and that overlap holds the printed
    curtain out a whole first layer and costs it 0.18 of its lift."""
    h = RU_W / 2 + 0.01
    fx, fu = STOP_RELIEF_X, STOP_RELIEF_U
    return mirrored_pair(lambda s: ru_xu([(s * (STOP_X0 + fx), 0), (s * h, 0), (s * h, h - STOP_X0), (s * (STOP_X0 + fu), fu),
                                          (s * (STOP_X0 + fx), fu)], ZF, STOP_TOP))


def threshold_lip():
    """The white threshold lip across the doorway, 0.94 in tall, its front the siding face. Its back
    is the 45 degree wedge the curtain hangs on, u = LIP_U0 + (z - ZF), carried on 0.01 under the floor
    top so the lip joins the skirt; it sits over the floor's edge gap and on the skirt, and every layer
    of it is joined to the skirt in its own layer."""
    h = RU_W / 2 + 0.01
    return ru_uz([(LIP_U0 - 0.01, ZF - 0.01), (WT, ZF - 0.01), (WT, ZF + LIP_H), (LIP_U0 + LIP_H, ZF + LIP_H)], -h, h)


def post_extensions():
    """Each curtain post carries on over the floor top to the lip's top, POST_EXT_U deep, into the
    lip, so the skirt's bridges between posts are anchored."""
    return [ru_box(x - SW / 2, x + SW / 2, 0, POST_EXT_U, ZF - 0.01, ZF + LIP_H) for x in CURTAIN_POSTS]


def rebate_cut():
    """The rebate in the head's inside face that the curtain's tongue rises into, open to the room."""
    h = RU_W / 2
    return ru_box(-h, h, -1, REB_U, MOUTH - 0.01, MOUTH + REB_H)


def rebate_adds():
    """The ribs across the rebate (they hold its ceiling's bridges) and the pads that hang from its
    ceiling over the spring fingers' bumps."""
    top = MOUTH + REB_H + 0.01
    ribs = [ru_box(x - RIB_W / 2, x + RIB_W / 2, 0, REB_U + 0.01, MOUTH, top) for x in RIB_XS]
    pads = mirrored_pair(lambda s: ru_box(*xspan(s, PAD_X0, PAD_X1), 0, REB_U + 0.01, PAD_Z, top))
    return ribs + pads


def latch_outline():
    return m3.CrossSection([chamfered(LATCH_X, LATCH_Z, LATCH_W, LATCH_H, LATCH_CUT)])


def finger_slot(sign):
    """The slot under a spring finger, in (x, z), FING_SLOT tall (down to the body's top at 2.74), its two root
    corners rounded."""
    x0, x1, z1, r = FING_TIP - 0.1, FING_ROOT, Z_TT - FING_H, FING_RADIUS
    z0 = z1 - FING_SLOT
    sq = m3.CrossSection.square([x1 - x0, z1 - z0]).translate([x0, z0])
    corners = m3.CrossSection.square([r, z1 - z0]).translate([x1 - r, z0])
    round_ = (m3.CrossSection.square([r, z1 - z0 - 2 * r]).translate([x1 - r, z0 + r])
              + m3.CrossSection.circle(r, 48).translate([x1 - r, z0 + r])
              + m3.CrossSection.circle(r, 48).translate([x1 - r, z1 - r]))
    cs = (sq - corners) + (round_ ^ corners)
    return ru_xz(cs if sign > 0 else cs.mirror([1, 0]), -1, TONGUE_T + 0.01)


def handle(xc=0.0):
    """The black lift handle centred at xc: two legs standing on the rail with their stepped fillet,
    and the grip across them (its first layer the curtain's only bridge)."""
    h, l, z0, z1 = HDL_HALF, HDL_LEG, HDL_Z0, HDL_Z0 + HDL_HT
    parts = [ru_box(xc - h, xc + h, HDL_U1, HDL_U2, z0, z1)]
    for s in (1, -1):
        xa, xb = sorted([xc + s * h, xc + s * (h - l)])
        parts.append(ru_box(xa, xb, RAIL_FACE - 0.01, HDL_U1 + 0.01, z0, z1))
        for k, f in enumerate(HDL_FILLET):
            parts.append(ru_box(xa - f, xb + f, RAIL_FACE - 0.01 + 0.2 * k, RAIL_FACE + 0.2 * (k + 1), z0, z1 + f))
    return union(parts)


def curtain_parts(handle_x=0.0):
    """The lift-out curtain seated in the doorway, in garage coords, as (white, black) (spec_rollup.md
    D). White: the slatted body from the inside face to RU_FACE, its back edges chamfered to
    CHAMF_TOP and its top front edge bevelled; the bottom zone whose 45 degree front edge hangs on
    the lip's wedge, notched over each post; the bottom rail; the tongue along its back with two
    spring fingers (each cut free by a slot under it, a bump on top) and two tabs (cut free through
    the layers, a bump on the front), notched round the ribs; the latch boss and the handle's boss.
    Black, from the 5.05 layer: the latch plate with its slot, and the lift handle centred at
    handle_x (None: no handle, as the fit test's half door is built before its handle goes on)."""
    h, c = CUR_HALF, CUR_CHAMF

    def back(u_top, z0, z1):
        return ru_xu([(-(h - c), 0), (h - c, 0), (h, c), (h, u_top), (-h, u_top), (-h, c)], z0, z1)
    zb = ZF + G_BOT
    body = (back(RU_FACE, RAIL_Z0 - 0.01, CHAMF_TOP + 0.01) + ru_box(-h, h, 0, RU_FACE, CHAMF_TOP, Z_FT)
            - ru_uz([(RU_FACE - CH_TOP - 0.01, Z_FT + 0.01), (RU_FACE + 0.01, Z_FT + 0.01),
                     (RU_FACE + 0.01, Z_FT - CH_TOP - 0.01)], -h - 1, h + 1))

    def wedge_z(u):                     # the curtain's 45 degree front-bottom edge, WEDGE_GAP over the wedge
        return ZF + WEDGE_GAP + (u - LIP_U0)
    uc0 = LIP_U0 + G_BOT - WEDGE_GAP    # 3.80: where it meets the bottom face
    bottom = back(BOT_U, zb, RAIL_Z0) - ru_uz([(uc0 - 0.01, wedge_z(uc0 - 0.01)), (BOT_U + 0.01, zb - 0.01),
                                              (BOT_U + 0.01, wedge_z(BOT_U + 0.01))], -h - 1, h + 1)
    tongue = ru_box(-h, h, 0, TONGUE_T, Z_FT - 0.01, Z_TT)
    rail = ru_box(-h, h, RU_FACE - 0.01, RAIL_FACE, RAIL_Z0, RAIL_TOP)
    parts = [body, bottom, tongue, rail]
    if handle_x is not None:            # the handle's white boss, the rail carried up over the first slat
        parts.append(ru_box(handle_x - HDL_BOSS_HALF, handle_x + HDL_BOSS_HALF, RU_FACE - 0.01, RAIL_FACE,
                            RAIL_Z0, HDL_BOSS_TOP))
    cuts = [ru_box(-h - 1, h + 1, RU_FACE - SLAT_GROOVE_D, RU_FACE + 1, z - SLAT_GROOVE_W / 2, z + SLAT_GROOVE_W / 2)
            for z in slat_lines()]
    cuts += [ru_box(x - RIB_W / 2 - RIB_CLR, x + RIB_W / 2 + RIB_CLR, -1, TONGUE_T + 0.01, Z_FT, Z_TT + 1)
             for x in RIB_XS]
    cuts += [ru_box(x - SW / 2 - POST_NOTCH_CLR, x + SW / 2 + POST_NOTCH_CLR, -1, BOT_U + 0.01, ZF - 1, RAIL_Z0)
             for x in CURTAIN_POSTS]
    zt0 = Z_TT - TAB_W
    for s in (1, -1):
        cuts.append(finger_slot(s))
        cuts += [ru_box(*xspan(s, TAB_TIP - TAB_GAP, TAB_ROOT), -1, TONGUE_T + 0.01, zt0 - TAB_SLOT, zt0),
                 ru_box(*xspan(s, TAB_TIP - TAB_GAP, TAB_TIP), -1, TONGUE_T + 0.01, zt0 - TAB_SLOT, Z_TT + 1),
                 ru_box(*xspan(s, TAB_TIP, TAB_ROOT), TAB_T, TONGUE_T + 0.01, zt0, Z_TT + 1)]
    white = union(parts) - union(cuts)
    r = (TAB_W - TAB_BUMP_TOP) / 2
    adds = mirrored_pair(lambda s: ru_box(*xspan(s, BUMP_X0, BUMP_X1), 0, BUMP_U, Z_TT - 0.01, Z_TT + BUMP_H))
    adds += mirrored_pair(lambda s: ru_uz([(TAB_T - 0.01, zt0), (TAB_BUMP_U, zt0 + r), (TAB_BUMP_U, Z_TT - r),
                                           (TAB_T - 0.01, Z_TT)], *xspan(s, TAB_BUMP_X0, TAB_BUMP_X1)))
    # the latch boss; under it the grooves stop square at the latch's rectangle, so no groove ends in
    # a taper under a line where the boss's corners are cut (the shut spec's way)
    adds.append(ru_xz(latch_outline(), RU_FACE - 0.01, RAIL_FACE))
    adds.append(ru_box(LATCH_X - LATCH_W / 2, LATCH_X + LATCH_W / 2, RU_FACE - SLAT_GROOVE_D - 0.01, RU_FACE,
                       LATCH_Z - LATCH_H / 2, LATCH_Z + LATCH_H / 2))
    white = union([white] + adds)
    slot = ru_box(LATCH_X - LATCH_SLOT_W / 2, LATCH_X + LATCH_SLOT_W / 2, -1, 10,
                  LATCH_Z - LATCH_SLOT_H / 2, LATCH_Z + LATCH_SLOT_H / 2)
    black = [ru_xz(latch_outline(), RAIL_FACE - 0.01, RAIL_FACE + LATCH_T) - slot]
    if handle_x is not None:
        black.append(handle(handle_x))
    black = union(black)
    return white - black, black


def curtain():
    """The whole curtain, seated, in garage coords."""
    return union(list(curtain_parts()))


def spring_regions():
    """Where the curtain's springs are, as boxes in garage coords: {name: region}. The curtain inside
    each is that spring (check_garage.py cuts them out of the real part to test its motion): the
    finger strips and their bumps, which bend down, and the tab plates and their bumps, which bend in."""
    zt0 = Z_TT - TAB_W
    return {"fingers": union(mirrored_pair(lambda s: ru_box(*xspan(s, FING_TIP, FING_ROOT), -0.01, TONGUE_T + 0.01,
                                                             Z_TT - FING_H, Z_TT))),
            "finger bumps": union(mirrored_pair(lambda s: ru_box(*xspan(s, BUMP_X0, BUMP_X1), -0.01, BUMP_U + 0.01,
                                                                 Z_TT - 0.02, Z_TT + BUMP_H + 0.01))),
            "tabs": union(mirrored_pair(lambda s: ru_box(*xspan(s, TAB_TIP, TAB_ROOT), -0.01, TAB_T, zt0, Z_TT))),
            "tab bumps": union(mirrored_pair(lambda s: ru_box(*xspan(s, TAB_BUMP_X0, TAB_BUMP_X1), TAB_T,
                                                              TAB_BUMP_U + 0.01, zt0, Z_TT)))}


CURTAIN_TO_PRINT = [[1, 0, 0], [0, 0, 1], [0, -1, 0]]   # on its back, slats and handle up (as the roll-up end)


def curtain_to_shed(lift=0.0, swing=0.0, out=0.0, drop=0.0):
    """Matrix moving the seated curtain the way it comes out (spec_rollup.md H.3): lifted, its bottom
    swung out `swing` degrees about its front at the opening's top, then moved out and down."""
    t = math.radians(swing)
    c0 = L / 2 - WT
    pu, pz = RU_FACE, MOUTH + lift
    # in (u, z): rotate about (pu, pz) after the lift, then shift (out, -drop); u = -y - c0
    a11, a12, a21, a22 = math.cos(t), -math.sin(t), math.sin(t), math.cos(t)
    b1 = pu - a11 * pu - a12 * pz + a12 * lift + out
    b2 = pz - a21 * pu - a22 * pz + a22 * lift - drop
    return np.array([[1, 0, 0, 0], [0, a11, -a12, a11 * c0 - b1 - c0], [0, -a21, a22, -a21 * c0 + b2]], dtype=float)


def gable_vent(side):
    """(parts, recess): louvred vent centred under the ridge, 0.92 ft below it, 1.12 x 0.76 ft.
    Its frame is flush with the siding and its louvres stand in a recess in the siding, so
    nothing of it stands out past the siding (Alan, Nov 3 2026)."""
    yf = side * L / 2

    def slab(x0, x1, z0, z1, d0, d1):
        """A slab d0 to d1 out from the siding face."""
        ya, yb = sorted([yf + side * d0, yf + side * d1])
        return box(x0, x1, ya, yb, z0, z1)
    fr = 1.0
    x0, x1, z0, z1 = -VENT_W / 2, VENT_W / 2, VENT_ZC - VENT_H / 2, VENT_ZC + VENT_H / 2
    recess = slab(x0 + fr, x1 - fr, z0 + fr, z1 - fr, -VENT_DEPTH, 1)
    parts = [slab(x0, x1, z0, z1, -EMBED, 0) - recess]         # the frame, flush; covers the siding grooves
    # the louvres: wedges standing on the recess floor, flat underneath, sloping back to the floor
    # at the top. Their front edges come up to the siding face and no further, and they narrow
    # toward it, so in the print (outside up) nothing overhangs. Each leaves VENT_BACK_GAP under the
    # next at the back, so on every layer the gaps between them are wider than a line.
    inner_h = VENT_H - 2 * fr
    for i in range(VENT_LOUVRES):
        zb = z0 + fr + inner_h * i / VENT_LOUVRES
        zt = zb + inner_h / VENT_LOUVRES - VENT_BACK_GAP
        yb = yf - side * (VENT_DEPTH + 0.1)                     # 0.1 into the floor, so they join it
        poly = [(yb, zb), (yf, zb), (yf, zb + VENT_SLAT), (yb, zt)]
        parts.append(prism(poly, 1, 2, 0, x1 - x0 - 2 * fr + 0.2).translate([x0 + fr - 0.1, 0, 0]))
    return parts, recess


def trims():
    """Gable bands, and the steel door's, window's and roll-up's casings (raised, in the trim
    colour). The corner boards are the separate corner angles; the latch plate is on the curtain."""
    p = []
    # gable band: it stops at the recess for the corner angle (the recess cuts it off, the same
    # cut as the wall's, so the band's end and the recess's always match)
    for sy in (1, -1):
        ya, yb = sorted([sy * (L / 2 - EMBED), sy * (L / 2 + PROUD)])
        p.append(box(-W / 2, W / 2, ya, yb, ZWT - TRIM, ZWT) - union([corner_recess(sx, sy) for sx in (1, -1)]))
    xo, xi = W / 2, W / 2 - EMBED
    # steel door casing: two sides and one head board
    ztop = ZF + DOOR_OPEN_H
    p.append(box(xi, xo + PROUD, DOOR_Y0 - TRIM, DOOR_Y0, ZF, ztop + TRIM))
    p.append(box(xi, xo + PROUD, DOOR_Y1, DOOR_Y1 + TRIM, ZF, ztop + TRIM))
    p.append(box(xi, xo + PROUD, DOOR_Y0 - TRIM, DOOR_Y1 + TRIM, ztop, ztop + TRIM))
    # window casing: the same 1x4 board on all four sides (no sill nose; Alan, Oct 31 2026)
    y0, y1, z0, z1 = WIN_Y0, WIN_Y1, WIN_Z0, WIN_Z1
    p.append(box(xi, xo + PROUD, y0 - TRIM, y0, z0 - TRIM, z1 + TRIM))
    p.append(box(xi, xo + PROUD, y1, y1 + TRIM, z0 - TRIM, z1 + TRIM))
    p.append(box(xi, xo + PROUD, y0 - TRIM, y1 + TRIM, z1, z1 + TRIM))
    p.append(box(xi, xo + PROUD, y0 - TRIM, y1 + TRIM, z0 - TRIM, z0))
    # roll-up casing: two sides and the head
    n, h, zt = "roll-up end", RU_W / 2, ZF + RU_H
    p.append(wall_box(n, -h - TRIM, -h, WT - EMBED, WT + PROUD, ZF, zt + TRIM))
    p.append(wall_box(n, h, h + TRIM, WT - EMBED, WT + PROUD, ZF, zt + TRIM))
    p.append(wall_box(n, -h - TRIM, h + TRIM, WT - EMBED, WT + PROUD, zt, zt + TRIM))
    return p


def casing_sides():
    """The side boards of the door side's casings: [(outer edge y, which way is out, z0, z1)]."""
    dz1 = ZF + DOOR_OPEN_H + TRIM
    return [(DOOR_Y0 - TRIM, -1, ZF, dz1), (DOOR_Y1 + TRIM, 1, ZF, dz1),
            (WIN_Y0 - TRIM, -1, WIN_Z0 - TRIM, WIN_Z1 + TRIM), (WIN_Y1 + TRIM, 1, WIN_Z0 - TRIM, WIN_Z1 + TRIM)]


def groove_fills():
    """A siding groove whose edge comes within GROOVE_W of the outside of a casing's side board is
    filled beside that board, from its bottom to its top, so it shows as if under the casing, as the
    grooves over the door do; above and below the board it runs on. With the door on the 4 ft mark
    this is the -56 in groove, 1/2 in past the latch-side casing (-56.5 in): the model's grooves are
    0.5 mm (18 mm at full size, wider than real ones), so it would leave a 0.1 mm strip of siding
    along the casing's edge, under a line (ASSUMED; the Lofted Barn Garage's fix, Nov 3 2026)."""
    out = []
    for edge, out_dir, z0, z1 in casing_sides():
        for y in layout(-L / 2, L / 2, GROOVE_OC):
            d = out_dir * (y - edge)                 # the groove's centre out from the casing's edge
            if -GROOVE_W / 2 < d < GROOVE_W * 1.5:   # it straddles the edge or its near edge is within GROOVE_W
                a0, a1 = sorted([edge - out_dir * 0.01, y + out_dir * (GROOVE_W / 2 + 0.01)])
                out.append(wall_box("door side", a0, a1, WT - GROOVE_D - 0.01, WT, z0, z1))
    return out


def opening_cuts():
    """The steel doorway, the window and the roll-up opening, through siding and framing."""
    return [wall_box("door side", DOOR_Y0, DOOR_Y1, -0.5, WT + 2, ZF, ZF + DOOR_OPEN_H),
            wall_box("door side", WIN_Y0, WIN_Y1, -0.5, WT + 2, WIN_Z0, WIN_Z1),
            wall_box("roll-up end", -RU_W / 2, RU_W / 2, -0.5, WT + 2, ZF, ZF + RU_H)]


def door_stop():
    """The stop on the steel door's latch jamb, outside the door, the full opening height
    (STOP_POLY), running 0.2 into the jamb so it joins it. It keeps the door from swinging out."""
    pts = [(DOOR_Y1 + 0.2, STOP_POLY[0][1])] + [(DOOR_Y1 - d, u) for d, u in STOP_POLY] + [(DOOR_Y1 + 0.2, WT)]
    pts = [(y, W / 2 - WT + u) for y, u in pts]
    return prism(pts, 1, 0, 2, DOOR_OPEN_H).translate([0, 0, ZF])


def hinge_cuts():
    """The steel door's pin holes, in the header and the sill post, and the trench the bottom pin
    swings out along from the wall's inside face (F7). There is no groove in the floor: the door
    is hung in the loose door side and is captive once that wall is on the floor."""
    return [cyl_z(AXIS_X, AXIS_Y, ZF - HOLE_BOTTOM_DEPTH, ZF + 1, PIN_HOLE_D),
            cyl_z(AXIS_X, AXIS_Y, ZF + DOOR_OPEN_H - 1, ZF + DOOR_OPEN_H + HOLE_TOP_DEPTH, PIN_HOLE_D),
            box(W / 2 - WT - 0.01, AXIS_X, AXIS_Y - PIN_HOLE_D / 2, AXIS_Y + PIN_HOLE_D / 2,
                ZF - TRENCH_DEPTH, ZF + 1)]


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


def gable_pegs():
    """The roof pegs on the gable top chords, against the end walls' inside face so each lies on
    the bed in the print, standing PEG_UP proud of the roof underside, square to it."""
    pegs = []
    for sx in (1, -1):
        for sy in (1, -1):
            x = sx * PEG_X
            peg = cyl_z(x, sy * PEG_Y, zline(x) - 3, zline(x) + 3, PEG_D)
            pegs.append(peg.trim_by_plane(*under_roof(sx, PEG_UP)))
    return pegs


def mid_pegs():
    """A roof peg on each long wall's top plates at mid-length, so the roof halves hold the middle
    of the 203 mm long walls straight too. It lies on the bed in the print (u 0 to 2.2)."""
    return [cyl_z(sx * MID_PEG_X, 0, ZWT - MID_PEG_ROOT, zline(MID_PEG_X) + 3, PEG_D)
            .trim_by_plane(*under_roof(sx, PEG_UP)) for sx in (1, -1)]


LONG_SEAMS = (-W / 2 + 48 * S, -W / 2 + 96 * S)   # the floor's two long sheet seams, where its three rows meet


def floor():
    """Floor frame and floor sheets. The walls stand on it with their siding hanging down over
    its edge, FLOOR_CLR clear of it. It prints upside down, floor face on the bed."""
    xf, yf = W / 2 - TS - FLOOR_CLR, L / 2 - TS - FLOOR_CLR
    cuts = []
    edges = [-(yf - RIM)] + [e for j in joist_ys() for e in (j - SW / 2, j + SW / 2)] + [yf - RIM]
    for a, b in zip(edges[0::2], edges[1::2]):
        cuts.append(box(-xf + RIM, xf - RIM, a, b, -1, ZF - DECK))
    # floor sheet seams, inside the walls: three rows across the width from -x, 48, 48 and 38 in;
    # rows 1 and 3 are three 8 ft sheets, row 2 a 4 ft, two 8 ft and a 4 ft (DERIVED, the
    # shed-measurements skill; row and stagger datums ASSUMED). Every seam lands on a joist.
    xi, yi = W / 2 - WT, L / 2 - WT
    r1, r2 = LONG_SEAMS
    for x0, x1, ys in ((-xi, r1, [-48 * S, 48 * S]), (r1, r2, [-96 * S, 0.0, 96 * S]), (r2, xi, [-48 * S, 48 * S])):
        for y in ys:
            cuts.append(box(x0, x1, y - 0.2, y + 0.2, ZF - 0.25, ZF + 0.01))
    for x in (r1, r2):
        cuts.append(box(x - 0.2, x + 0.2, -yi, yi, ZF - 0.25, ZF + 0.01))
    return box(-xf, xf, -yf, yf, 0, ZF) - union(cuts + floor_cuts())


FLOOR_TO_PRINT = [[1, 0, 0], [0, -1, 0], [0, 0, -1]]     # upside down


def peg_box(sx):
    """The space the long wall's mid peg takes above the wall top: WALL_CUTS gives it to the long
    wall (everything else above the plates goes with the end walls)."""
    xa, xb = sorted([sx * (W / 2 - WT - 0.01), sx * (W / 2 - TS)])
    return box(xa, xb, -(PEG_D / 2 + 0.3), PEG_D / 2 + 0.3, ZWT - 0.01, ZPK)


def walls():
    """All four walls in one, assembled; split_walls() cuts them apart for printing. The order is
    spec_rollup.md E.6's: the jamb stops, threshold lip and post extensions go in after the opening
    cuts, the rebate comes out after the roof clearance (its ribs and pads go back in), and the
    prong reliefs come out last, so every leg is free to LEG_ROOT."""
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

    # (1) siding, framing (the roll-up's drum box with it), posts and prongs, corner posts, trim and
    # the groove filled beside the steel door's latch-side casing
    framing = long_wall_framing("door side") + long_wall_framing("plain side")
    framing += [end_wall_framing("back end"), end_wall_framing("roll-up end"), drum_box()]
    for name in WALL_SIDE:
        framing += under_floor(name)
    for sx in (1, -1):              # corner posts, solid into the corner so each wall's mitred end is a solid
        for sy in (1, -1):          # 45 degree wedge; they go down through the floor's corners
            xa, xb = sorted([sx * (W / 2 - WT), sx * (W / 2 - TS)])
            ya, yb = sorted([sy * (L / 2 - TS), sy * (L / 2 - WT - SW)])
            framing.append(box(xa, xb, ya, yb, 0, ZWT))
    b = union([shell] + framing + trims() + groove_fills())
    # (2) the openings
    b = b - union(opening_cuts())
    # (3) the window, the vent frames, and in the roll-up doorway the jamb stops, the threshold lip
    # and the posts carried on over the floor top
    vents = [gable_vent(1), gable_vent(-1)]
    b = union([b] + window_unit() + [v[0][0] for v in vents] + jamb_stops() + [threshold_lip()] + post_extensions())
    # (4) the vents' recesses and louvres
    b = b - union([recess for _, recess in vents])
    b = union([b] + [q for parts, _ in vents for q in parts[1:]])
    # (5) the steel door's stop
    b = b + door_stop()
    # (6) the pin holes and trench, room for the roof, then the rebate over the roll-up doorway, with
    # its ribs and pads back in
    b = b - union(hinge_cuts() + roof_clearance())
    b = union([b - rebate_cut()] + rebate_adds())
    # (7) the reliefs round the prongs' legs, last
    b = b - union([prong_relief(name, ac) for name in WALL_SIDE for ac in prong_spots(name)])
    # (8) the roof pegs on the gables
    b = b + union(gable_pegs())
    # nothing above the wall plates over the long walls' mitred ends, so a long wall can be
    # lowered into place between the gable ends (it takes a sliver off each eave corner)
    for sx in (1, -1):
        b = b - mitred(0, sx).trim_by_plane([0, 0, 1], ZWT)
    # the long walls' mid pegs, after that cut or it would take them off at the wall top
    b = b + union(mid_pegs())
    # the recess for each corner angle, and the chamfer off the corner under it
    return b - union([corner_recess(sx, sy) for sx, sy in CORNERS])


def body():
    """The assembled body: four walls and the floor."""
    return union(list(split_walls(walls()).values()) + [floor()])


# the four walls meet at 45 degree mitres through the inside and outside corners, so each
# wall carries only the trim on its own face and it all prints on top (Alan, Nov 1 2026). Each
# prints lying flat on the inside face of its framing, outside up.
BIG = 500


def mitred(axis, sign):
    """The region one wall owns: outside its inside face, and on its side of the mitre at
    each end. axis 0 for a long wall, 1 for an end wall; sign which side of the garage."""
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
    """Above the top of the wall plates on one end of the garage. The gable corners above the
    plates go with the end walls, where they lie on the bed. It starts 0.001 over the plates' top,
    so the long walls' corner tops, which stop exactly there, don't leave a flat scrap on an end
    wall."""
    return M.cube([2 * BIG] * 3, True).trim_by_plane([0, 0, 1], ZWT + 0.001).trim_by_plane([0, sign, 0], 0)


WALL_CUTS = {
    "door side": mitred(0, 1) - above_plate(1) - above_plate(-1) + peg_box(1),
    "plain side": mitred(0, -1) - above_plate(1) - above_plate(-1) + peg_box(-1),
    "back end": mitred(1, 1) + above_plate(1) - peg_box(1) - peg_box(-1),
    "roll-up end": mitred(1, -1) + above_plate(-1) - peg_box(1) - peg_box(-1),
}
# garage coords to print coords, inside face down (each a rotation, det +1)
WALL_TO_PRINT = {
    "door side": [[0, 1, 0], [0, 0, 1], [1, 0, 0]],
    "plain side": [[0, -1, 0], [0, 0, 1], [-1, 0, 0]],
    "back end": [[-1, 0, 0], [0, 0, 1], [0, 1, 0]],
    "roll-up end": [[1, 0, 0], [0, 0, 1], [0, -1, 0]],
}


def split_walls(w):
    """The four walls cut apart at the mitres. Where a cut lies on a face of the body it can leave
    a flat scrap with no volume; those are dropped."""
    return {name: union([c for c in (w ^ cut).decompose() if c.volume() > 1e-6]) for name, cut in WALL_CUTS.items()}


# ---------------------------------------------------------------- corner angles
CORNERS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]   # (sx, sy): the door side is +x, the back end +y


def corner_walls(sx, sy):
    """(long wall, end wall) that meet at a corner."""
    return ("door side" if sx > 0 else "plain side"), ("back end" if sy > 0 else "roll-up end")


def corner_frame(sx, sy):
    """Matrix from a corner's own coords to garage coords: u out from the long wall's siding face,
    v out from the end wall's, z up, so u = v = 0 is the outer corner of the siding. For the
    (+,-) and (-,+) corners it is a mirror image."""
    return np.array([[sx, 0, 0, sx * W / 2], [0, sy, 0, sy * L / 2], [0, 0, 1, 0]], dtype=float)


def angle_reach():
    """How far the corner angle reaches from the outer corner of the siding along (the long wall,
    the end wall): ANGLE_REACH on the long wall, and on the end wall what the standing leg's
    ANGLE_UP leaves past the long-face leg (F5)."""
    return ANGLE_REACH, ANGLE_UP - (ANGLE_T - POCKET_D)


def corner_recess(sx, sy):
    """What comes out of both walls at one corner for its angle: a recess POCKET_D deep in each
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
    """The black L angle at one corner, in garage coords: two legs ANGLE_T thick with their inside
    faces on the recess floors, a 45 degree fillet in the inside corner, the foot level with the
    bottom of the skirts, and the top ANGLE_ROOF under the roof, square to it, right across both
    legs. Each leg's face covers its wall to angle_reach() and the other leg's thickness."""
    out = ANGLE_T - POCKET_D
    ra, rb = angle_reach()
    p, f = POCKET_D, POCKET_D + ANGLE_FILLET
    sec = [(out, out), (out, -ra), (-p, -ra), (-p, -f), (-f, -p), (-rb, -p), (-rb, out)]
    a = prism(sec, 0, 1, 2, ZPK).transform(corner_frame(sx, sy))
    return a.trim_by_plane(*under_roof(sx, -ANGLE_ROOF))


def angle_to_print(sx):
    """Garage coords to print coords for an angle on the sx side: lying on the long-face leg's
    outside face, its length along y, the end-face leg standing up. A rotation, det +1; the (+,-)
    and (-,+) angles come out as the mirror image of the others."""
    return [[0, -sx, 0], [0, 0, 1], [-sx, 0, 0]]


def angle_prints():
    """The four corner angles lying the way they print, in CORNERS order, each on the bed at the
    origin. (+,+) and (-,-) print the same; (+,-) and (-,+) are their mirror image."""
    return [to_print(angle_to_print(sx), [corner_angle(sx, sy)])[0] for sx, sy in CORNERS]


def trim_zone():
    """Everything standing proud of the siding that is trim (gable bands, casings). It prints in
    the second colour. The plain side has none. (The curtain's black is curtain_parts()'s.)"""
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
    from the ridge) to the +x half in garage coords."""
    d = np.array([math.cos(ALPHA), 0, -math.sin(ALPHA)])
    nrm = np.array([math.sin(ALPHA), 0, math.cos(ALPHA)])
    p0 = np.array([0, 0, ZPK])
    return np.column_stack([[0, 1, 0], nrm, d, p0])


def roof_half():
    """The +x roof half in garage coords (the -x half is its mirror image): the sheet with its
    ribs and ridge cap, a hole under each gable peg and one over the long wall's mid peg."""
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
    ys = [k * RIB_OC for k in range(-30, 31) if abs(k * RIB_OC) <= ly - 2]
    for y in ys:
        ribs.append(M.extrude(rib.translate([y, 0]), 70).translate([0, 0, -5]))
    extras.append(union(ribs).transform(mat))
    cap = M.cube([2 * ly, CAP_T, CAP_RUN + 5]).translate([-ly, ROOF_T - 0.1, -5])     # ridge cap
    extras.append(cap.transform(mat))
    r = union([slab] + extras)
    r = r.trim_by_plane([1, 0, 0], 0.1)                                     # ridge gap 0.1 per half
    r = r.trim_by_plane([-1, 0, 0], -xe)                                    # eave (fascia) cut
    r = r.trim_by_plane([0, 1, 0], -ly).trim_by_plane([0, -1, 0], -ly)
    holes = []
    for x, y in ROOF_PEGS:
        h = cyl_z(x, y, zline(x) - 5, zline(x) + 5, PEG_HOLE_D)
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
def steel_door(w, h, panels, knob_x, knob_y):
    """A door in print coords: X across it from the pin line, Y up it from its bottom, Z through
    it (Z = 0 the inside face, on the bed). The slab with its hinge edge rounded and a pin at the
    top and bottom, panels outlined by grooves on the outside face, and the knob. All white."""
    slab = box(0, w, 0, h, 0, DOOR_T)
    edge = cyl_y(0, 0, h, DOOR_R, DOOR_T)                                  # rounded hinge edge
    pin_top = cyl_y(0, h - 0.5, h + PIN_TOP_LEN, DOOR_R, PIN_D, 40)
    pin_bot = cyl_y(0, -PIN_BOTTOM_LEN, 0.5, DOOR_R, PIN_D, 40)
    d = union([slab, edge, pin_top, pin_bot])
    g, z0 = PANEL_GROOVE_W, DOOR_T - PANEL_GROOVE_D
    grooves = [box(x0, x1, y0, y1, z0, DOOR_T + 1) - box(x0 + g, x1 - g, y0 + g, y1 - g, z0 - 1, DOOR_T + 2)
               for x0, x1, y0, y1 in panels]
    d = d - union(grooves)
    return d + cyl_z(knob_x, knob_y, DOOR_T - 0.01, DOOR_T + KNOB_H, KNOB_D)


def door_panels():
    """The six panels, (X0, X1, Y0, Y1) in door coords, at the designer's fractions of the
    opening, from the hinge-side jamb and from the floor."""
    return [(DOOR_Y0 + c0 * DOOR_OPEN_W - AXIS_Y, DOOR_Y0 + c1 * DOOR_OPEN_W - AXIS_Y,
             r0 * DOOR_OPEN_H - DOOR_BOTTOM_GAP, r1 * DOOR_OPEN_H - DOOR_BOTTOM_GAP)
            for c0, c1 in PANEL_COLS for r0, r1 in PANEL_ROWS]


def door_parts():
    """The steel door in print coords (see steel_door), all filament 1, no knob on the inside."""
    return steel_door(DOOR_W, DOOR_H, door_panels(), DOOR_W - KNOB_IN, KNOB_UP * DOOR_H)


def hinge_matrix(ax_x, ax_y, z0, theta_deg):
    """Matrix from door print coords to garage coords, for a door whose pin line is at (ax_x,
    ax_y) and bottom at z0, swung theta degrees: positive swings the latch edge in (toward -x)."""
    base = np.array([[0, 0, 1, ax_x - DOOR_R], [1, 0, 0, ax_y], [0, 1, 0, z0]], dtype=float)
    th = math.radians(theta_deg)
    rot = np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]])
    pivot = np.array([ax_x, ax_y, 0])
    R = rot @ base[:, :3]
    t = rot @ (base[:, 3] - pivot) + pivot
    return np.column_stack([R, t])


def door_to_shed(theta_deg=0.0):
    """Matrix from door print coords to garage coords, swung in theta degrees."""
    return hinge_matrix(AXIS_X, AXIS_Y, ZF + DOOR_BOTTOM_GAP, theta_deg)


DOOR_TO_PRINT = [[0, 1, 0], [-1, 0, 0], [0, 0, 1]]    # the door laid along X on its plate


# ---------------------------------------------------------------- skids
def skid():
    """An inner skid lying along X, notched where the joists, the floor's end bands and the end
    walls' siding sit on it, with a peg at each end that pushes up into the end band."""
    s = box(0, L, 0, SKID_W, 0, SKID_H)
    cuts = []
    for jy in joist_ys():
        y = jy + L / 2
        cuts.append(box(y - SW / 2 - NOTCH_CLEAR / 2, y + SW / 2 + NOTCH_CLEAR / 2, -1, SKID_W + 1,
                        SKID_H - NOTCH, SKID_H + 1))
    end = TS + FLOOR_CLR + RIM + 0.3
    cuts.append(box(-1, end, -1, SKID_W + 1, SKID_H - NOTCH, SKID_H + 1))
    cuts.append(box(L - end, L + 1, -1, SKID_W + 1, SKID_H - NOTCH, SKID_H + 1))
    s = s - union(cuts)
    pegs = [cyl_z(X, SKID_W / 2, SKID_H - NOTCH - 0.01, SKID_H - NOTCH + SKID_PEG_UP, SKID_PEG_D)
            for X in (TS + FLOOR_CLR + RIM / 2, L - (TS + FLOOR_CLR + RIM / 2))]
    return s + union(pegs)


def outer_skid():
    """An outer skid lying along X, its outer face at Y = 0: flat-topped, OUTER_SKID_H tall, so its
    bottom is level with the inner skids', under the long-side rim band and the long wall's posts.
    A relief OUTER_RELIEF deep under each long-wall prong (and where one would be on the other long
    wall, so one part fits either side, turned end for end), and two pegs that push up into the
    rim band."""
    s = box(0, L, 0, SKID_W, 0, OUTER_SKID_H)
    w = OUTER_SKID_X + SKID_W / 2 - (W / 2 - WT + OUTER_RELIEF_U)
    cuts = []
    for ac in sorted({a for n in LONG_WALLS for a0 in PRONGS[n] for a in (a0, -a0)}):
        a0, a1 = prong_slot(ac)
        cuts.append(box(a0 - 1.0 + L / 2, a1 + 1.0 + L / 2, -1, w, OUTER_SKID_H - OUTER_RELIEF, OUTER_SKID_H + 1))
    s = s - union(cuts)
    py = SKID_W / 2 - (OUTER_PEG_X - OUTER_SKID_X)
    pegs = [cyl_z(y + L / 2, py, OUTER_SKID_H - 0.01, OUTER_SKID_H + SKID_PEG_UP, OUTER_PEG_D)
            for _, y in outer_peg_spots()[:2]]
    return s + union(pegs)


SKID_KINDS = ("inner", "inner", "outer", "outer")


def skids_to_shed():
    """Matrices placing the four skids under the floor frame, in SKID_KINDS order (-x, +x each):
    the inner ones' joists down in their notches, the outer ones flat under the rim band, all
    four bottoms at z = -(SKID_H - NOTCH). The -x outer skid is the +x one turned end for end."""
    zo = -(SKID_H - NOTCH)
    out = [np.array([[0, -1, 0, sx * SKID_X + SKID_W / 2], [1, 0, 0, -L / 2], [0, 0, 1, zo]], dtype=float)
           for sx in (-1, 1)]
    out.append(np.array([[0, 1, 0, -(OUTER_SKID_X + SKID_W / 2)], [-1, 0, 0, L / 2], [0, 0, 1, zo]], dtype=float))
    out.append(np.array([[0, -1, 0, OUTER_SKID_X + SKID_W / 2], [1, 0, 0, -L / 2], [0, 0, 1, zo]], dtype=float))
    return out


def skid_parts():
    """The four skids in garage coords, in SKID_KINDS order."""
    return [(skid() if k == "inner" else outer_skid()).transform(m) for k, m in zip(SKID_KINDS, skids_to_shed())]


def skids():
    """All four skids side by side for printing (outer, inner, inner, outer)."""
    parts = [outer_skid(), skid(), skid(), outer_skid()]
    return union([s.translate([0, i * (SKID_W + 12), 0]) for i, s in enumerate(parts)])


# ---------------------------------------------------------------- fit test
FIT_LONG, FIT_END = "plain side", "roll-up end"   # the corner the fit test copies (-x, -y)
FIT_STUB = 20.0                                    # its stub of corner angle, from the foot
FIT_SKID_STUB = 23.0                               # its stub of outer skid, from the end
FIT_END_X = -23.0                                  # the bit of floor runs from the corner past the -35 in curtain
                                                   # post's notch, which keeps 0.97 of floor to the cut
FIT_WALL_X = -(35 * S - GROOVE_W / 2) - 0.1        # -24.544: the short roll-up end stops over that post (x -25.223
                                                   # ..-24.165), so its skirt ends on it (cut at -23.0 it would hang
                                                   # 1.2 mm past it with nothing under it), and inside the siding's
                                                   # -35 in groove, so its top layer ends at the groove, not in a
                                                   # strip of siding thinner than a line
FIT_XM = -RU_W / 4                                 # -16.933: the half doorway's middle, where the half door's
                                                   # handle goes and about which its jamb is mirrored
FIT_FRAME_X0 = -(59 * S + GROOVE_W / 2) + 0.03     # -41.848: the half doorway is the real roll-up end from inside
                                                   # the siding's -59 in groove, which keeps 0.74 of its end stud,
                                                   # to the doorway's middle (cut at the end stud's far side, -42.2,
                                                   # its top layer kept a 0.32 strip of siding past the groove)
FIT_STUB_X1 = -RU_CLR_X                            # the half door is the real curtain's -x half, to x -0.3


def corner_test(pieces, f):
    """The corner where the plain side meets the roll-up end, made short: the bottom 8 mm of each
    wall above the floor joined to its top 10 mm under the wall top, on that corner of the floor,
    a stub of its corner angle and one of the outer skid under it. The roll-up end runs in to
    over the post at -35 in, inside that post's siding groove: its end stud, the jamb studs, the
    prong under the jamb rooted in the bottom plate, the jamb stop, the threshold lip, most of that
    post and the casing; its
    rebate is filled here (the half doorway tests it: in this piece it would be a 9.7 mm overhang
    held on one edge). The plain side is cut 0.1 inside the siding's -112 in groove, over the -112 in
    stud's post (0.68 of the stud kept), with its prong, so its top layer ends at the groove, not in a
    strip of siding thinner than a line. The bit of floor runs to x = -23.0, past that post's notch,
    and along the plain side to the -112 in stud's far side, so it is 22.47 mm along the roll-up end's
    edge and 21.31 mm along the plain side's, with the outer skid's peg hole under the plain side's
    edge. Returns (long wall, end wall, floor, angle stub, skid stub) in garage coords."""
    z_lo, z_hi = ZF + 8, ZWT - 10
    y_cut = -(112 * S - SW / 2)                     # -78.493: the bit of floor, to the -112 in stud's far side
    y_wall = -(112 * S - GROOVE_W / 2) - 0.1        # -78.872: the short plain side, 0.1 inside the -112 in groove

    def short(piece, xa, xb, ya, yb):
        keep = box(xa, xb, ya, yb, -5, ZWT)
        lo = piece ^ keep ^ box(-BIG, BIG, -BIG, BIG, -5, z_lo)
        hi = piece ^ keep ^ box(-BIG, BIG, -BIG, BIG, z_hi, ZWT)
        return lo + hi.translate([0, 0, z_lo - z_hi])
    stub = corner_angle(-1, -1) ^ box(-BIG, BIG, -BIG, BIG, -1, FIT_STUB)
    sk = skid_parts()[2] ^ box(-BIG, BIG, -L / 2 - 1, -L / 2 + FIT_SKID_STUB, -BIG, BIG)
    end = pieces[FIT_END] + ru_box(-RU_W / 2 - 0.01, FIT_END_X, 0, REB_U + 0.01, MOUTH - 0.01, MOUTH + REB_H + 0.01)
    return (short(pieces[FIT_LONG], -W / 2 - 2, -(W / 2 - 10), -L / 2 - 2, y_wall),
            short(end, -W / 2 - 2, FIT_WALL_X, -L / 2 - 2, -(L / 2 - 10)),
            f ^ box(-W / 2, FIT_END_X, -L / 2, y_cut, -5, 400), stub, sk)


def curtain_frame(pieces):
    """The fit test's half doorway (spec_rollup.md J.2), cut from the real roll-up end: from inside
    the siding groove over its -x end stud to the doorway's middle, from the skirt's bottom to the wall top (its jamb
    and prong, the stop, the lip and its wedge, the posts at -35 and -16 in and half the middle one,
    the rebate with its rib at -14.5 and half the middle rib, a pad, the drum box and the casing),
    closed at x 0 by the same jamb strip mirrored about the half doorway's middle, with its stop. So
    the rebate's ceiling spans 13.3 and 18.8 as on the real one, and the opening is exactly half as
    wide. It stands on its own skirt and posts: the curtain hangs on the wall, not the floor."""
    ew = pieces[RU]
    real = ew ^ box(FIT_FRAME_X0, 0, -BIG, BIG, -1, ZWT)
    jamb = (ew ^ box(FIT_FRAME_X0, -(STOP_X0 - 0.1), -BIG, BIG, -1, ZWT)).mirror([1, 0, 0]).translate([2 * FIT_XM, 0, 0])
    return real + jamb


def curtain_stub():
    """The fit test's half door (spec_rollup.md J.3), cut from the real curtain: its -x half to
    x -0.3, the full height, with its +x end's back edge chamfered as the real ends are, and the
    full-size handle centred on it at FIT_XM, so it hangs on half the springs with half the weight
    and moves exactly as the real door does. (white, black)."""
    keep = box(-CUR_HALF - 1, FIT_STUB_X1, -BIG, BIG, -BIG, BIG)
    x1, c = FIT_STUB_X1, CUR_CHAMF
    chamfer = ru_xu([(x1 - c - 0.01, -0.01), (x1 + 0.01, -0.01), (x1 + 0.01, c + 0.01)], ZF - 1, CHAMF_TOP)
    return tuple((part ^ keep) - chamfer for part in curtain_parts(handle_x=FIT_XM))


def corner_test_parts(pieces, f):
    """The fit test's roll-up pieces, each lying the way it prints: [(name, part)]: the short corner and
    its stubs from corner_test(), the half roll-up doorway and the half roll-up door. plates() puts the
    half doorway and half door alone on fit plate 1, and the corner on plate 2 (FIT_DOOR_PAIR)."""
    lw, ew, fl, stub, sk = corner_test(pieces, f)
    return [("short plain side", to_print(WALL_TO_PRINT[FIT_LONG], [lw])[0]),
            ("short roll-up end", to_print(WALL_TO_PRINT[FIT_END], [ew])[0]),
            ("bit of floor", to_print(FLOOR_TO_PRINT, [fl])[0]),
            ("corner angle stub", to_print(angle_to_print(-1), [stub])[0]),
            ("outer skid stub", to_print([[1, 0, 0], [0, 1, 0], [0, 0, 1]], [sk])[0]),
            ("half roll-up doorway", to_print(WALL_TO_PRINT[RU], [curtain_frame(pieces)])[0]),
            ("half roll-up door", to_print(CURTAIN_TO_PRINT, [union(list(curtain_stub()))])[0])]


FIT_OW, FIT_OH, FIT_ZF = 14.0, 24.0, 3.0           # the short doorway's opening and its sill block
FIT_AX_X = W / 2 - WT + DOOR_AXIS_U
FIT_AX_Y = -FIT_OW / 2 + DOOR_R + DOOR_GAP
FIT_DW = (FIT_OW / 2 - DOOR_GAP) - FIT_AX_Y
FIT_DH = FIT_OH - DOOR_BOTTOM_GAP - DOOR_TOP_GAP


def fit_doorway():
    """The short doorway in garage coords (as if on the door side, centred on y = 0): the real
    section, u 0 to WT, the real stop, pin holes and trench, standing on its own 3 mm sill block
    with no floor (the real door is hung in the loose wall)."""
    jamb, oh, zf = FIT_OW / 2, FIT_OH, FIT_ZF
    x0 = W / 2 - WT
    f = union([box(x0, W / 2, -jamb - 6, jamb + 6, 0, zf), box(x0, W / 2, -jamb - 6, -jamb, zf, zf + oh + 6),
               box(x0, W / 2, jamb, jamb + 6, zf, zf + oh + 6),
               box(x0, W / 2, -jamb - 6, jamb + 6, zf + oh, zf + oh + 6)])
    pts = [(jamb + 0.2, STOP_POLY[0][1])] + [(jamb - d, u) for d, u in STOP_POLY] + [(jamb + 0.2, WT)]
    f = f + prism([(y, x0 + u) for y, u in pts], 1, 0, 2, oh).translate([0, 0, zf])
    return f - union([cyl_z(FIT_AX_X, FIT_AX_Y, zf - HOLE_BOTTOM_DEPTH, zf + 1, PIN_HOLE_D),
                      cyl_z(FIT_AX_X, FIT_AX_Y, zf + oh - 1, zf + oh + HOLE_TOP_DEPTH, PIN_HOLE_D),
                      box(x0 - 0.01, FIT_AX_X, FIT_AX_Y - PIN_HOLE_D / 2, FIT_AX_Y + PIN_HOLE_D / 2,
                          zf - TRENCH_DEPTH, zf + 1)])


def fit_door():
    """The short door in print coords: the real slab, hinge edge and pins, one panel and the knob."""
    return steel_door(FIT_DW, FIT_DH, [(1.5, FIT_DW - 4.5, 3.0, FIT_DH - 3.0)], FIT_DW - KNOB_IN, KNOB_UP * FIT_DH)


def fit_door_to_shed(theta_deg=0.0):
    return hinge_matrix(FIT_AX_X, FIT_AX_Y, FIT_ZF + DOOR_BOTTOM_GAP, theta_deg)


def peg_block():
    """A block lying like an end wall with a roof peg lying on the bed, as the real ones do."""
    return box(-6, 6, 0, 6, 0, WT) + cyl_y(0, 5, 6 + PEG_UP, PEG_D / 2, PEG_D)


def peg_coupon():
    """A bit of roof with a peg hole."""
    return box(-6, 6, -6, 6, 0, ROOF_T) - cyl_z(0, 0, -1, PEG_HOLE_UP, PEG_HOLE_D)


def fit_test_parts():
    """Fit test plate 2, each lying the way it prints: [(name, part)]."""
    return [("short doorway", to_print(WALL_TO_PRINT["door side"], [fit_doorway()])[0]),
            ("short door", on_bed(fit_door())),
            ("roof peg block", on_bed(peg_block())),
            ("bit of roof", on_bed(peg_coupon()))]


# ---------------------------------------------------------------- files
def write_stl(man, name):
    """A binary STL. An STL holds its corners as 32-bit floats, which rounds together corners that the
    booleans left a few millionths of a mm apart, and the triangles between them collapse. So the part's
    corners are rounded to 32 bits and merged, and any triangle left with two corners the same is dropped:
    the file is a closed surface with no collapsed triangles. The part is NOT simplified first: simplify()
    turned two of the door side's casing boards into ramps (21 mm3 gone) when the wall was joined from its
    siding and trim again, and on the Lofted Barn Garage's long walls it cut wedges out of the studs at any
    tolerance, even simplifying the part as one piece (final audit, Nov 4 2026). The triangles written are
    summed back to a volume, and if that isn't the part's, nothing is written; check_garage.py also reads each
    file back layer by layer against its part (stl_parts())."""
    mesh = man.to_mesh()
    v, inv = np.unique(np.asarray(mesh.vert_properties)[:, :3].astype(np.float32), axis=0, return_inverse=True)
    t = inv.ravel()[np.asarray(mesh.tri_verts)]
    t = t[(t[:, 0] != t[:, 1]) & (t[:, 1] != t[:, 2]) & (t[:, 0] != t[:, 2])]
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    vol = float(np.einsum("ij,ij->i", a.astype(float), np.cross(b.astype(float), c.astype(float))).sum() / 6)
    if abs(vol - man.volume()) > 0.01:
        raise ValueError(f"{name}: the triangles to be written hold {vol:.3f} mm3, the part {man.volume():.3f}")
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
    already set to its filament (1 siding, 2 trim, roof and angles, 3 floor and skids). A "modifier" in
    the settings, [(name, manifold, settings), ...] in the parts' coords, is written as modifier parts with those
    settings and no filament of their own; where the object lies on the plate comes from its parts alone."""
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
            vols = [(part_name, man, f'<part id="{{}}" subtype="normal_part"><metadata key="name" value={quoteattr(part_name)}/>'
                     f'<metadata key="extruder" value="{filament}"/></part>') for part_name, man, filament in parts]
            for mod_name, mod_man, mod_settings in modifiers:
                vols.append((mod_name, mod_man, f'<part id="{{}}" subtype="modifier_part"><metadata key="name" '
                             f'value={quoteattr(mod_name)}/>'
                             + "".join(f'<metadata key="{k}" value={quoteattr(v)}/>' for k, v in mod_settings.items())
                             + '</part>'))
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
             # saved from Flash Studio: AD5X 0.4, 0.20mm Standard, Arachne, elephant foot 0.1,
             # filaments 1 white, 2 black, 3 brown) and these version tags (Nov 2 2026). It says the
             # file is from a newer version: click OK.
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
    parts["curtain"] = curtain()
    parts["roof"] = roof_half()
    parts["door"] = door_parts()
    parts["skids"] = skids()
    return parts


def wall_parts(p, name, zone):
    """(siding, trim) of a wall, lying flat on the bed."""
    return to_print(WALL_TO_PRINT[name], two_colour(p[name], zone))


def size(m):
    """Width and depth of a part on the bed."""
    bb = m.bounding_box()
    return bb[3] - bb[0], bb[4] - bb[1]


def side_by_side(parts, gap=4.0):
    """[(name, part)] side by side along x, gap apart, as one part (for an .stl): the corner angles, each 73.8 mm
    long along y, as plate 2 lays them out (one behind the other along y they made a 313 mm row, off the bed)."""
    out, x = [], 0.0
    for _, m in parts:
        out.append(m.translate([x, 0, 0]))
        x += size(m)[0] + gap
    return union(out)


NO_BRIM = {"brim_type": "no_brim"}               # roof halves and corner angles: a brim lip would
                                                 # show on an edge, and the roof sheets nearly fill the bed
SKID_BRIM = {"brim_type": "outer_only", "brim_width": "5"}   # long thin parts get a 5 mm brim (PRINTER-BRAIN)
FIT_SKID_GAP = 6.2     # on fit plate 2, from the skid stub to any other part: its 5.1 mm brim (5 + the 0.1 brim gap)
                       # and a mm (the Lofted Barn Garage's SKID_GAP); the corner's row is spaced this and a mm more
FIT_DOOR_PAIR = ("half roll-up doorway", "half roll-up door")   # fit plate 1, alone
# Every wall, and every fit-test piece cut from one, lays its siding's first layer across the studs. Left to
# itself, Flash Studio picks the direction afresh each slice, and the same file doesn't always come out the same:
# it bridged the half doorway's two end bays lengthwise, 62 mm strands, every time, and once the door side's bays
# along the whole wall, 62 mm strands too, where other slices of the same file had them across (final audit, Nov 4
# 2026; the Lofted Barn Garage's door side did the same in about half of its slices). The plain side's and both end
# walls' bays are just as long the other way (62 mm), so the slices that happened to lay them across prove nothing
# (bridge audit, Nov 4 2026). So each wall carries a modifier over its siding, from SIDING_BRIDGE_Z up, that sets
# External bridge infill direction 180, which Flash Studio reads as along the bed's X: across the studs, 15.4 mm at
# most, the gables too. It starts over the framing, so the prong legs' first layer (0.65), the rebate's ceiling
# (1.65) and the door side's headers (2.95) keep the slicer's own direction, along the leg and between the ribs, as on
# the walls that print as proven. UP_THE_GABLE (90, along the bed's Y) is for a barn end, over its collar tie, where
# lines across the studs would be 31 mm: the Lofted Barn Garage's; these gables don't need it. The fit test's short
# plain side and short roll-up end carry it too, so the corner prints the way the real walls do: left to itself, the
# slicer laid the short plain side's siding along its bays. The modifier also moves a little hidden solid infill, not
# on every piece alike: on the 1.45 layer the plain side's two solid lines along each mitred end become one (the other
# walls' are unchanged), and on the fit test the short roll-up end's two along its mitre become one while the short
# plain side keeps both; and some lines along the siding's top edge move on its first layer (bridge review and floor
# review, Nov 4 2026). No face or fit changes. ASSUMED (as sliced)
ACROSS_STUDS = {"bridge_angle": "180"}
UP_THE_GABLE = {"bridge_angle": "90"}
SIDING_BRIDGE_Z = SD - 0.5           # 3.204: under the siding's first layer (3.65 to 3.85), over the 2.85 one


def across_studs(part, split=None):
    """The object settings for a wall lying flat (part, on the bed): modifier boxes over its siding layers, from
    SIDING_BRIDGE_Z to over its top and 1 mm past it all round. One sets ACROSS_STUDS (see there); given split (a y
    on the bed along the middle of a member running across the wall, a barn end's collar tie), it stops there and a
    second one over it sets UP_THE_GABLE."""
    bb = part.bounding_box()

    def mod(name, y0, y1, setting):
        return name, box(bb[0] - 1, bb[3] + 1, y0, y1, SIDING_BRIDGE_Z, bb[5] + 1), setting
    if split is None:
        return {"modifier": [mod("bridges across the studs", bb[1] - 1, bb[4] + 1, ACROSS_STUDS)]}
    return {"modifier": [mod("bridges across the studs", bb[1] - 1, split, ACROSS_STUDS),
                         mod("bridges up the gable", split, bb[4] + 1, UP_THE_GABLE)]}


# The floor prints face down, and its sheet seams (0.4 wide, 0.25 deep) are its first layer, so its second layer
# bridges every seam. Left to itself, Flash Studio laid those bridges along the two long seams, in every slice: nine
# strands 193 to 195 mm long, each a little slanted, so each lay over a 0.4 mm slot for up to 69 mm (vbridge2: 102.8
# mm off the first layer's lines) and sagged into it (bridge review and floor review, Nov 4 2026). Laid along the
# short seams instead, they would be 22 to 34 mm. So that one layer carries modifiers: FLOOR_STRIP either side of each
# long seam sets ACROSS_LONG_SEAMS, 180, along the bed's X, and the rest of the floor ACROSS_SHORT_SEAMS, 90, along
# its Y. Every line then crosses its seam: 0.4 mm, or 1.2 mm where a short seam runs into a long one. There the slicer
# fills the strip and the box beside it apart, and their lines stop a hair short of each other over the short seam: a
# spot of its bottom up to about 0.4 by 0.4 mm is left to the layer over it, a dip 0.2 mm deeper (10 of them, 1.1 mm2
# in all), too small to see (floor review). Nothing else on the floor hangs over anything, so no other bridge is set.
# The face under it prints as before. In the end bands, where the skid pegs' holes end, the slicer moves a few lines of
# solid infill on the 3.05 and 3.25 layers: less of the 3.25 layer is an internal bridge, so more of the 3.45 layer's
# solid lines cross gaps in the sparse infill (55 mm of such runs on these layers against 48 before, the longest 4.3
# mm against 5.5). On the 0.85, 1.05 and 4.05 layers it lays the same lines in another order (floor review). ASSUMED
# (as sliced)
FLOOR_LAYER = (0.25, 0.45)           # the floor's second layer, over its seams
FLOOR_STRIP = 1.0
ACROSS_LONG_SEAMS = {"bridge_angle": "180"}
ACROSS_SHORT_SEAMS = {"bridge_angle": "90"}


def across_seams(part, xs):
    """The object settings for the floor lying face down (part, on the bed): modifier boxes over FLOOR_LAYER only, 1 mm
    past it all round, side by side along x: FLOOR_STRIP either side of each long seam (xs, on the bed) sets
    ACROSS_LONG_SEAMS, and the rest ACROSS_SHORT_SEAMS (see there)."""
    bb = part.bounding_box()
    cuts = [bb[0] - 1] + [c for x in sorted(xs) for c in (x - FLOOR_STRIP, x + FLOOR_STRIP)] + [bb[3] + 1]
    return {"modifier": [("bridges across the long seams" if i % 2 else "bridges across the short seams",
                          box(a, b, bb[1] - 1, bb[4] + 1, *FLOOR_LAYER),
                          ACROSS_LONG_SEAMS if i % 2 else ACROSS_SHORT_SEAMS)
                         for i, (a, b) in enumerate(zip(cuts[:-1], cuts[1:]))]}


def plates(p):
    """The plates of each Orca project, from build()'s parts, as write_3mf() takes them:
    {file name: [(plate name, items)]}.

    2 all plates.3mf has a plate for each print (F3): both long walls and the door, the roof and
    the corner angles, both end walls and the roll-up curtain, then the floor and the four skids.
    Filament 1 is the siding colour (white), filament 2 the trim, roof and corner angles and the
    curtain's latch plate and handle (black), filament 3 the floor and skids (brown, Alan Nov 2
    2026). On the two-colour plates the prime tower goes at x 165, y 195, so every part there ends
    at x <= 162 or y <= 192."""
    zone = trim_zone()
    walls_p = {name: wall_parts(p, name, zone) for name in WALL_CUTS}
    fl = to_print(FLOOR_TO_PRINT, [p["floor"]])[0]
    fl_seams = across_seams(fl, [x - p["floor"].bounding_box()[0] for x in LONG_SEAMS])   # FLOOR_TO_PRINT keeps x
    door_p = to_print(DOOR_TO_PRINT, [p["door"]])[0]
    roof_p = roof_to_print(p["roof"])
    turn = np.array([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0]], dtype=float)
    inner_p, outer_p = on_bed(skid().transform(turn)), on_bed(outer_skid().transform(turn))

    def wall_item(name, x, y, split=None):
        """A wall lying flat at x, y, its siding bridged across the studs (across_studs, split as there)."""
        siding, trim = walls_p[name]                 # the plain side has no trim
        return (name, [("siding", siding, 1)] + ([] if trim.is_empty() else [("trim", trim, 2)]), (x, y),
                across_studs(union(walls_p[name]), split))

    def row(parts, filament, gap=6.0, own=None):
        """[(name, part)] side by side along x, gap apart, the row centred on the bed; own: {name: that object's
        own settings}."""
        x = (220 - sum(size(m)[0] for _, m in parts) - gap * (len(parts) - 1)) / 2
        out = []
        for name, m in parts:
            item = (name, [(name, m, filament)], (x, (220 - size(m)[1]) / 2))
            out.append(item + ((own[name],) if own and name in own else ()))
            x += size(m)[0] + gap
        return out

    # the fit test, one filament: plate 1 is the half doorway and half door alone, so, as on plate 3, nothing but the
    # door's handle prints above the walls' 5.65 layer (the bit of floor is 6.8 tall and the skid stub 5.8), its
    # layers as short and as quick, and the fit test shows how the real one comes out; plate 2 the roll-up corner in
    # front (its skid stub with the real skids' brim, its angle stub with none, as the real ones), the door and roof
    # peg behind it
    pieces = corner_test_parts({n: p[n] for n in WALL_CUTS}, p["floor"])
    cu = [q for q in pieces if q[0] in FIT_DOOR_PAIR]
    ct = [q for q in pieces if q[0] not in FIT_DOOR_PAIR]
    dt = fit_test_parts()
    own = {"outer skid stub": SKID_BRIM, "corner angle stub": NO_BRIM,
           **{n: across_studs(m) for n, m in ct if n in ("short plain side", "short roll-up end")}}
    fit1 = row(cu, 1, own={"half roll-up doorway": across_studs(dict(cu)["half roll-up doorway"])}, gap=8.0)
    da, db = max(size(m)[1] for _, m in ct), max(size(m)[1] for _, m in dt)
    y0 = (220 - da - 8 - db) / 2
    fit2 = [(n, ps, (x, y0 + (da - size(ps[0][1])[1]) / 2), *o)
            for n, ps, (x, _), *o in row(ct, 1, gap=FIT_SKID_GAP + 1, own=own)]
    fit2 += [(n, ps, (x, y0 + da + 8 + (db - size(ps[0][1])[1]) / 2), *o) for n, ps, (x, _), *o in row(dt, 1)]
    fit_3mf = [("roll-up door", fit1), ("roll-up corner, door and roof peg", fit2)]

    # plate 1: the door at the front, then the door side and the plain side, 3 mm apart
    dw, dh = size(door_p)
    lh = size(union(walls_p["door side"]))[1]
    y1 = 4 + dh + 4.3
    y2 = y1 + lh + 3
    # plate 2: the roof halves 6 mm apart and the four angles beside them, 4 mm apart, all centred
    rw, rl = size(roof_p)
    angles = angle_prints()
    aw, al = size(angles[0])
    rx = (220 - (2 * rw + 6 + 12 + 4 * aw + 3 * 4)) / 2
    ax = rx + 2 * rw + 6 + 12
    # plate 3: the end walls side by side, 6 mm apart, and the curtain 4 mm behind the roll-up end
    ew, eh = size(union(walls_p["roll-up end"]))
    cur_w, cur_b = to_print(CURTAIN_TO_PRINT, list(curtain_parts()))
    ex = (220 - 2 * ew - 6) / 2
    # plate 4: the floor and the four skids, 12 mm between them so their brims stay apart
    fw, fh = size(fl)
    sw_, sl = size(outer_p)
    fx = (220 - (fw + 12 + 4 * sw_ + 3 * 12)) / 2
    skx = [fx + fw + 12 + i * (sw_ + 12) for i in range(4)]
    names = ("outer skid 1", "inner skid 1", "inner skid 2", "outer skid 2")
    all_3mf = [
        ("long walls and door", [wall_item("door side", 3, y1), wall_item("plain side", 3, y2),
                                 ("door", [("door", door_p, 1)], (3, 4))]),
        ("roof and corner angles",                                                              # filament 2
         [("roof half 1", [("roof half", roof_p, 2)], (rx, (220 - rl) / 2), NO_BRIM),
          ("roof half 2", [("roof half", roof_p, 2)], (rx + rw + 6, (220 - rl) / 2), NO_BRIM)]
         + [("corner angle, %s at %s" % corner_walls(sx, sy), [("corner angle", a, 2)],
             (ax + i * (aw + 4), (220 - al) / 2), NO_BRIM)
            for i, ((sx, sy), a) in enumerate(zip(CORNERS, angles))]),
        ("end walls and roll-up curtain",
         [wall_item("roll-up end", ex, 4), wall_item("back end", (220 + 6) / 2, 4),
          ("roll-up curtain", [("curtain", cur_w, 1), ("latch plate and handle", cur_b, 2)], (ex, 4 + eh + 4))]),
        ("floor and skids", [("floor", [("floor", fl, 3)], (fx, (220 - fh) / 2), fl_seams)]       # brown
         + [(nm, [("skid", outer_p if nm.startswith("outer") else inner_p, 3)], (x, (220 - sl) / 2), SKID_BRIM)
            for nm, x in zip(names, skx)]),
    ]
    return {"1 fit test.3mf": fit_3mf, "2 all plates.3mf": all_3mf}


def stl_parts(p, pl=None):
    """{.stl file name: the part it is written from, lying as it prints}, from build()'s parts (pl: plates(p),
    if already made). Each wall is the whole wall, not its siding and trim joined again (the same place on the
    bed, and no edges where two bodies touch)."""
    pl = pl or plates(p)
    out = {"floor.stl": to_print(FLOOR_TO_PRINT, [p["floor"]])[0]}
    out.update({name + ".stl": to_print(WALL_TO_PRINT[name], [p[name]])[0] for name in WALL_CUTS})
    fit = [union([m.translate([x, y, 0]) for _, parts, (x, y), *own in items for _, m, _ in parts])
           for _, items in pl["1 fit test.3mf"]]
    out.update({"roof half.stl": roof_to_print(p["roof"]),
                "corner angle.stl": side_by_side([("", a) for a in angle_prints()]),
                "door.stl": to_print(DOOR_TO_PRINT, [p["door"]])[0],
                "roll-up curtain.stl": to_print(CURTAIN_TO_PRINT, [p["curtain"]])[0],
                "skids.stl": p["skids"], "fit test.stl": union([fit[0], fit[1].translate([0, 120, 0])])})
    return out


def main():
    p = build()
    zone = trim_zone()
    walls_p = {name: wall_parts(p, name, zone) for name in WALL_CUTS}
    pl = plates(p)
    for name, part in stl_parts(p, pl).items():
        write_stl(part, name)
    for name, plist in pl.items():
        write_3mf(name, plist)
    for name, (siding, trim) in walls_p.items():
        bb = union([siding, trim]).bounding_box()
        print(f"{name:12s} flat {bb[3]-bb[0]:7.1f} x {bb[4]-bb[1]:7.1f} x {bb[5]-bb[2]:6.1f} mm  "
              + ("no trim" if trim.is_empty()
                 else f"trim {trim.volume()/1000:5.2f} cm3, from {trim.bounding_box()[2]:.2f} mm up"))
    for k, v in p.items():
        bb = v.bounding_box()
        print(f"{k:12s} {bb[3]-bb[0]:7.1f} x {bb[4]-bb[1]:7.1f} x {bb[5]-bb[2]:6.1f} mm  "
              f"{v.volume()/1000:6.1f} cm3  {v.num_tri()} triangles")
    print("dropped marks:", DROPPED_MARKS)


if __name__ == "__main__":
    main()
