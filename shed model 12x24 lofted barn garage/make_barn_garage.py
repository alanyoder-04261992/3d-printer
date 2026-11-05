"""12x24 Lofted Barn Garage, 1:36 scale, for the Flashforge AD5X.

Run:  python make_barn_garage.py      (needs: pip install manifold3d numpy)

Makes the print files in this folder:
  1 fit test.3mf    to try first: plate 1 the roll-up door (a full-height half doorway with a half
                    roll-up door that lifts out just as the real one does, printing as plate 3 does);
                    plate 2 the roll-up corner (short pieces of the plain side and the roll-up end on a
                    bit of floor, a stub of corner angle and a stub of outer skid), a short in-swing
                    doorway and door, and a roof peg
  2 all plates.3mf  everything, one plate per print, the trim, roof and corner angles already set
                    to filament 2, the floor, skids and lofts to filament 3, the skids with a 5 mm brim
  floor.stl         floor frame and floor sheets, printed upside down; the walls snap onto it
  door side.stl     the long wall with the steel door and the window, framing, trim; prints lying
                    flat, inside face down, so the trim is the top few layers
  plain side.stl    the other long wall, the same way
  roll-up end.stl   the end wall with the 8 ft roll-up doorway, its gable, faux loft window and vent
  roll-up curtain.stl  the roll-up door: a separate curtain that lifts out by its handle, white with a
                    black latch plate and handle; prints on its back on the end walls' plate
  back end.stl      the other end wall, with its gable, gable backing and vent
  upper roof.stl    print TWO. The shallow top half of each side of the barn roof.
  lower roof.stl    print TWO. The steep bottom half of each side; the upper one laps over it.
  loft.stl          print TWO. The loft floor at each end, on its joists.
  door.stl          the 36 in steel door, all white, with its hinge pins; it swings in
  skids.stl         the four 4x6 skids: two inner ones notched for the joists, two outer ones flat
  corner angle.stl  the four black corner angles, two of each hand, glued on the corners
  fit test.stl      everything in 1 fit test.3mf, one colour

It is the 8x12 Side Lofted Barn model (../shed model 8x12 side lofted barn/make_barn.py), the same
snap joints, corner angles, lofts and four-sheet barn roof, built as the shop-standard 12x24
Lofted Barn Garage (designer style LBG): 6.9 ft walls, a barn roof 51 in from the top of the upper
plate to the peak of the trusses, a 4 ft loft at each end, an 8 ft roll-up door in one end, the
36 in steel door and a 2x3 window on the right-hand side where Alan's standard layout puts them (the
door near the roll-up end, the window toward the back), and four 4x6 skids. Its twin is the
12x24 Garage model, which has the very same roll-up door and steel door (the same solids); its floor and
outer skids are made the same way but differ under its own walls' prongs. The roll-up's
curtain lifts out the front by a handle at the bottom middle of its rail (Alan, Nov 3 2026), as the
lift-out addendum designs it; the steel door swings in on two pins.

Every number below carries a tag: CONFIRMED (Alan's, with where he said it), BARNWRIGHT (the 3D
designer's number, not confirmed by Alan), DERIVED (worked out; from what), ASSUMED (our choice;
why). The 3D designer is Alan's barnwrightsoftware project ("3d stand alone").

Axes for the assembled garage: x across the 134 in width (the door side at +x), y along the 24 ft
length (the roll-up end at -y), z up. z = 0 is the bottom of the floor joists (where the body sits
on the skids). Every number is millimetres on the model.
"""

import math
import os
import struct

import numpy as np
import manifold3d as m3

M = m3.Manifold
HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "12x24 Lofted Barn Garage 1:36"

# ---------------------------------------------------------------- scale
S = 25.4 / 36          # mm on the model per real inch (1:36): the largest common scale at which every
                       # piece prints whole on the 220 bed. CONFIRMED rule (Alan, Nov 3 2026: "Move to
                       # higher scale so it fits"); at 1:32 the 24 ft side would be 228.6 mm
FT = 12 * S

# ---------------------------------------------------------------- the building
W = 134 * S            # 94.544 width (the barn ends): a 12-wide is 134 in actual. CONFIRMED Alan Sep 30
                       # 2026 (shed-measurements skill); the 3D designer still draws 144 in (open question 1)
L = 288 * S            # 203.2 length, 24 ft. CONFIRMED Alan Nov 3 2026 ("garage and lift garage 12x24")

# held at the base models' millimetres, not scaled (the same in all four new shop-standard models, Nov 3
# 2026; ASSUMED): the snap joints, the corner recesses and the vent were proven in print at these sizes
# (Nov 2026), and at true scale the prong slot would break out of the floor's edge
TS = 1.4               # siding thickness (real 1/2 in would be 0.35; thicker so it prints solid)
SD = 3.5 * 25.4 / 24   # 3.704 stud depth, the 1:24 barn's (true 2.47): the floor's edge stands 3.30 under
                       # the wall, so the prong slot (out to 2.2) stays inside it. Studs look 5 1/4 in deep
WT = TS + SD           # whole wall, 5.104: every layer line the corners and vent were proven on stays put
JOIST_H = 5.5 * 25.4 / 24   # 5.821 floor joists, the barn's (true 3.88): the barb's ledge is 5.25 under the
                       # floor top with a 1.57 pocket under it
DECK = 1.0             # floor sheets (true 0.44)
ZF = JOIST_H + DECK    # top of the floor, 6.821
RIM = 5.0              # solid band round the edge of the floor, under the walls
FLOOR_CLR = 0.4        # gap between the floor's edge and the siding that hangs down over it
PLATE_BOT = 1.6        # bottom plate (true 1.06): the prong legs are freed up to LEG_ROOT inside it
# true to scale
SW = 1.5 * S           # 1.058 stud, plate and joist width in the wall plane, a 2x4's 1 1/2 in (2.5 printed
                       # lines, solid with Arachne). CONFIRMED 2x4 studs (Alan Sep 28 2026)
WALL_H = 82.8 * S      # 58.42 floor top to the top of the upper plate: 6.9 ft. BARNWRIGHT styles.LBG.wallH,
                       # kept by Alan (Oct 11 2026: "walls as they are")
ZWT = ZF + WALL_H      # top of the walls
STUD_CUT = 82.8 - 3 * 1.5   # 78.3 in of stud under three flat plates. DERIVED (open question 4); the
                       # model's studs are 77.5 in, as its bottom plate is held at 1.6 mm (2.3 in)


def gambrel(width_in, peak_in=51.0, deck_in=0.4375):
    """(knee x, lower rise, upper rise) in mm: the 3D designer's barn roof (model/roof-shapes.js
    roofProfile, library/construction.json roof.shapes.gambrel): the knee 0.38 of the width out
    from the middle, the two rises 0.32 and 0.13 of the width, both scaled together so the peak of
    the trusses (the roof line less the 7/16 in deck over the cosine of the upper slope) is peak_in
    over the top of the upper plate."""
    wft = width_in / 12
    rl, ru, kx = 0.32 * wft, 0.13 * wft, 0.38 * wft
    deck = deck_in / 12
    n = rl + ru

    def truss(h):
        return h - deck / math.cos(math.atan2(ru * h / n, kx))
    h = peak_in / 12
    for _ in range(12):
        h = peak_in / 12 + (h - truss(h))
    k = h / n
    return kx * FT, rl * k * FT, ru * k * FT


# the barn roof: the designer's bend (BARNWRIGHT) with Alan's 51 in from the top of the upper plate
# to the peak of the trusses at 12 ft wide (CONFIRMED, styles.LBG.built.barnPeak, Oct 11 2026),
# applied at the actual 134 in (DERIVED): knee 50.92 in out, rises 36.59 and 14.87 in. This line is
# the underside of the roof sheets (the top of the 7/16 in deck).
KNEE_X, LOWER_RISE, UPPER_RISE = gambrel(134)
ZKN = ZWT + LOWER_RISE
ZPK = ZKN + UPPER_RISE
LOW_M = LOWER_RISE / (W / 2 - KNEE_X)   # the steep lower slope, about 27/12
UP_M = UPPER_RISE / KNEE_X              # the shallow upper slope, about 3.5/12
GABLE = [(-W / 2, 0), (W / 2, 0), (W / 2, ZWT), (KNEE_X, ZKN), (0, ZPK), (-KNEE_X, ZKN), (-W / 2, ZWT)]
EAVE_S = 0.42 * FT     # the lower sheets run on this far down the slope past the wall top. BARNWRIGHT
END_OH = 0.10 * FT     # the lower sheets reach this far past each barn end. BARNWRIGHT
RAKE_STEP = 0.135 * FT # and the upper sheets this much further (designer's RAKE_STEP). BARNWRIGHT

PLATE_TOP = 3.0 * S    # top plate and upper plate, two flat 2x4s. CONFIRMED (three 1 1/2 in plates)
HEADER = 5.0 * S       # Alan's loft header: two 2x4s on edge on a flat 2x4, touching the top plate.
                       # CONFIRMED (his lofted-wall rule); here over the window only
FLAT_HEADER = 3.0 * S  # two flat 2x4s "for a taller door": over the steel door, where the 5 in header
                       # doesn't fit under the plates. CONFIRMED rule, applied here DERIVED (open question 3)
GABLE_BOARD = 5.5 * S  # 2x6 on edge on top of the end wall's upper plate. CONFIRMED (shed-measurements)
BACKING_Z = 11 * S     # gable backing: its bottom 11 in above the upper plate, 3 1/2 in high, only on
BACKING_H = 3.5 * S    # an end with no window or faux window: the back end only. CONFIRMED
GABLE_STUD_W = 3.5 * S # gable studs, wide face out, 24 in apart from the outside of the end wall. CONFIRMED;
GABLE_STUD_XS = [x * S for x in (-43, -19, 5, 29, 53)]   # hooked at the -x edge on both ends: ASSUMED (open question 7)
CHORD = 3.5 * S        # the end truss's chords, one 2x4 deep under the roof line, drawn their true depth.
                       # CONFIRMED (shed-measurements, "Fit the measured truss")
COLLAR_H = 3.5 * S     # a collar tie across the knees and a king post above it. BARNWRIGHT (the designer's
KING_W = 3.5 * S       # barn truss, as the barn model; open question 11)
GROOVE_OC = 8 * S      # siding grooves 8 in apart. BARNWRIGHT look, as the base models
GROOVE_W, GROOVE_D = 0.5, 0.35
TRIM = 3.5 * S         # 1x4 trim boards, actual 3 1/2 in. CONFIRMED (standard.json openings.trim, Oct 12 2026)
PROUD = 0.6            # how far trim stands off the siding: 3 layers. ASSUMED (print size, as the base)
EMBED = 0.4            # trim and window parts reach this far into the siding, so they join it
RAKE_W = 2.0           # the rake board showing under the roof edge round each barn end (print size)
BACK_BAND_Z = ZWT + 0.40 * (ZPK - ZWT)   # the back end's gable band at the loft line, 20.58 in up. BARNWRIGHT
FRONT_BAND_Z = ZWT     # the roll-up end's band (it has a gable window) at the wall top: BARNWRIGHT, but
                       # 1/4 in higher than the designer so it clears the corner recesses. ASSUMED (open
                       # question 10)
VENT_FLOOR = 4.25 - WT # the gable vent's louvres sit in a recess this deep in the siding (0.85): in the end
                       # walls' print (inside face down, 0.25 mm first layer, then 0.2) its floor is the
                       # layer line at 4.25, over 3 layers of siding. CONFIRMED flush (Alan, Nov 3 2026)
VENT_W, VENT_H = 1.12 * FT, 0.76 * FT   # louvred vent, both ends. BARNWRIGHT (parts/gable-vent.js)
VENT_DROP = 0.92 * FT  # its centre this far under the roof line's peak. BARNWRIGHT
VENT_SLATS = 4         # the designer draws five; with five the slats print under a line wide at 1:36. ASSUMED
VENT_BACK_GAP = 0.45   # each louvre leaves this much under the next (and the top one under the frame) at the
                       # back, so the gaps still print on the lower layers (the barn had 0.1, which closes
                       # them at 1:36). ASSUMED
FAUX_W, FAUX_H = 2.6 * FT, 1.9 * FT   # the faux loft window on the roll-up end's gable: trim only. BARNWRIGHT
FAUX_ZC = ZWT + max(0.62 + 0.95, 0.34 * (ZPK - ZWT) / FT) * FT   # its centre (gableRect). BARNWRIGHT rule
FAUX_BAR = 0.3 * FT    # frame width. BARNWRIGHT (parts/openings/gable-window.js)
FAUX_TRI = min(0.5, 0.55 * 1.0, 0.75 * 0.65) * FT   # the triangle in each inside corner. BARNWRIGHT

# the roll-up door (designer ru8: 8 ft wide, 6.4 ft tall, centred on the roll-up end). BARNWRIGHT;
# framed Alan's garage-door way, king studs up to the top plate and no header. CONFIRMED rule
RU_W = 96 * S          # 67.733 opening width
RU_H = 76.8 * S        # 54.187 opening height
MOUTH = ZF + RU_H      # 61.008 the opening's top. DERIVED
RU_FACE = 4.85         # the curtain's slat face out from the wall's inside face: a layer line one layer under
                       # the siding's printed face (5.05), 0.36 in behind the siding. DERIVED (the shut spec's)
RU_SLATS = 32          # slats 2 1/4 in (Alan's photograph, in the designer), from 0.22 ft up. BARNWRIGHT
RU_PITCH = 2.25 * S
RU_SLAT0 = 0.22 * FT
RU_GROOVE_W, RU_GROOVE_D = 0.5, 0.4   # a groove across the curtain under each slat, to the 4.45 layer line
LATCH_W, LATCH_H = 0.72 * FT, 0.38 * FT   # black latch plate with its corners off and a slot in it,
LATCH_CUT = 0.075 * FT                # 0.62 ft in from the right edge (from outside, +x) at 0.42 of the height.
LATCH_SLOT = (0.32 * FT, 0.09 * FT)   # BARNWRIGHT (parts/openings/roll-up.js)
LATCH_X = RU_W / 2 - 0.62 * FT
LATCH_Z = ZF + 0.42 * RU_H
LATCH_T = 0.4          # the plate: 2 layers of black
CURTAIN_POSTS = [x * S for x in (-35, -16, 0, 16, 35)]   # posts under the doorway into the floor's edge, the
                       # same on both garages (lift-out addendum). ASSUMED. With posts at 0 and 16 in only, the
                       # skirt under the doorway bridges 22 mm in the end wall's print (over the 20 mm rule), so
                       # 35 in each way too (clear of the inner skids' peg holes and the prongs)
BACK_END_EXTRA_POST = (13.75 + 27.5) / 2 * S   # a post with no stud over it, in the back end's bay beside the
                       # double at 28.25/29.75 in (which has no post: an inner skid's peg hole is under it), so
                       # the skirt's widest gap between posts is 16.1 mm (15.7 as the checker measures the
                       # bridge), not 21.5. ASSUMED

# the roll-up curtain lifts out (Alan, Nov 3 2026: "Do 4 the lift out add a handle in the bottom middle to lift
# it up", and "Front lift-out"). CONFIRMED: a separate white part with a black latch plate and a black lift
# handle at the bottom middle of its rail. It hangs on a 45 degree wedge on the white threshold lip, stands
# behind two 45 degree jamb stops, and a tongue along its top goes up into a rebate in the head's inside face,
# where two spring fingers press it down and two tabs press it in. Lift it by the handle until it stops, let it
# down a hair, swing the bottom out, let it drop and pull it away: out the front, roof on. The numbers are the
# lift-out addendum's final ones (Nov 3 2026), the same on both garages; u is out from the inside face
RU_CLR_X = 0.30        # the curtain's side gap to each jamb face (0.43 in), reads as the designer's dark guide
                       # strip. ASSUMED (PRINTER-BRAIN: 0.25-0.3 a side is an easy fit)
CUR_HALF = RU_W / 2 - RU_CLR_X   # 33.567: the curtain is 95.15 in wide. DERIVED
CUR_CHAMF = 1.25       # 45 degree chamfer on the curtain's two back vertical edges, where they bear on the jamb
CHAMF_TOP = 56.0       # stops, from its bottom to z 56; square above, so the fingers' root blocks stand on their
                       # whole footprint. ASSUMED
RU_STOP_GAP = 0.05     # drawn gap from each chamfer to its jamb stop; the tabs close it. ASSUMED
RU_STOP_X0 = CUR_HALF - CUR_CHAMF + RU_STOP_GAP   # 32.367 the jamb stops' edge on the inside face. DERIVED
RU_STOP_TOP = 50.0     # the jamb stops end here, low enough that the top can lean in as it goes back in. ASSUMED
RU_STOP_FOOT = 0.45    # each stop's first layer (0.25 thick, the others 0.2) starts this far out from the stop's edge,
                       # not on its 45 degree face: as printed the curtain's own 0.25 first layer would meet it when the
                       # springs push the door 0.2 out, and hold it 0.05 further out (review, Nov 3 2026). ASSUMED
SHADE = 2.2            # the dark slit between the slats' top and the head (3.1 in; designer 0.18 ft = 2.2 in):
                       # room for the slats to rise and tilt under the head. ASSUMED (open question 18)
Z_FT = MOUTH - SHADE   # 58.808 the slatted body's top. DERIVED
CH_TOP = 1.0           # 45 degree bevel on the body's top front edge, in the slit. ASSUMED
TONGUE_T = 1.05        # the tongue along the curtain's top, u 0..1.05 (5 layers), up to Z_TT. ASSUMED
TONGUE_UP = 1.8        # how far it rises over the opening's top (2.55 in). ASSUMED
Z_TT = MOUTH + TONGUE_UP   # 62.808. DERIVED
REB_U, REB_H = 1.65, 3.4   # the rebate in the head's inside face: u 0..1.65 (a layer line), z MOUTH..64.408,
                       # 0.6 in front of the tongue; its top is the rigid lift stop. ASSUMED
RIB_XS = (0.0, -14.5, 14.5)   # ribs across the rebate anchor its ceiling's bridges; the tongue is notched round
RIB_W, RIB_CLR = 1.2, 0.3     # them 1.8 wide. ASSUMED
FING_ROOT, FING_TIP = 32.3, 15.4   # each spring finger runs from its root near the jamb in to its free end at
                       # the rib notch. ASSUMED
FING_H = 1.26          # the finger strip, 3 lines tall. ASSUMED
FING_SLOT = 2.74       # the slot under it, from the finger down to the body's top (Z_TT - FING_H - Z_FT); more cuts
                       # into the body's top. ASSUMED
FING_R = 0.5           # radius in both root corners of the slot. ASSUMED
BUMP_X0, BUMP_X1 = 15.8, 17.6      # the bump on the finger's top near its tip, 3 lines high, one layer deeper
BUMP_H, BUMP_U = 0.6, 1.25         # than the tongue so it stays under its pad as the door goes in. ASSUMED
PAD_X0, PAD_X1 = 16.0, 16.7        # pads hanging from the rebate top. Each pad's root-side edge is at the bump's middle
                       # (changed after review from the addendum's 17.4): the bent finger slopes about 12 degrees at the
                       # stop, so the flat pad bears on the bump only along that edge, and there it is 15.6 from the
                       # finger's root, where the addendum's finger numbers (rate, strain, tip) were worked out. ASSUMED
PRELOAD = 0.55         # how far the pads press the bumps down, drawn: keeps the upside-down hold over 1.5 times the
                       # weight with the fingers' real rates. ASSUMED
PAD_Z = Z_TT + BUMP_H - PRELOAD    # 62.858 the pads' bottom. DERIVED
TAB_TIP, TAB_ROOT, TAB_GAP = 3.0, 12.6, 0.6   # the two tabs (u springs) from their free end to their root,
TAB_T, TAB_W, TAB_SLOT = 0.65, 2.2, 0.6       # 3 layers thick (the first three of its print), 2.2 tall, a slot
                       # under each and a gap at its free end. ASSUMED
TAB_BUMP_X0, TAB_BUMP_X1 = 3.0, 4.2   # the tab's bump: u 0.65..1.85 (6 layers), 0.2 into the rebate front,
TAB_BUMP_U, TAB_BUMP_TOP = 1.85, 0.8  # set by the layers; its flat top 0.8 tall. ASSUMED
LIP_H = 0.666          # the white threshold lip (0.94 in; the designer's diamond plate is 0.466). ASSUMED (open
                       # question 17)
LIP_U0 = 3.65          # the foot of the lip's 45 degree back face (the wedge), a layer line just behind the skirt.
                       # ASSUMED
G_BOT, WEDGE_GAP = 0.2, 0.05   # the curtain's bottom face over the floor top; drawn gap, chamfer to wedge. ASSUMED
BOT_U = 4.25           # the front face of the curtain's bottom zone, a layer line. ASSUMED
RAIL_Z0 = ZF + LIP_H + 0.2   # 7.687 the rail's bottom, 0.2 over the lip. DERIVED
RAIL_TOP = ZF + 0.225 * FT   # 8.726 the rail's top (1.47 in). BARNWRIGHT
RAIL_FACE = 5.05       # the rail stands 0.2 proud of the slats. DERIVED (the shut spec's)
POST_EXT_U = 4.65      # each curtain post carries on over the floor top, u 0..4.65, up to the lip's top. ASSUMED
POST_NOTCH_CLR = 0.3   # the curtain's bottom is notched 0.3 round each post. ASSUMED
HDL_HALF = 8 * S       # 5.644: the black lift handle at the bottom middle, 16 in wide; its legs 3.0 wide (4.25 in),
HDL_LEG, HDL_HT = 3.0, 2.0   # it 2.0 tall (2.8 in), about 2.7 times a real one so a fingernail lifts it. ASSUMED
                       # (open question 16); its place CONFIRMED (Alan's words)
HDL_U1, HDL_U2 = 6.65, 8.25   # legs u 5.05..6.65 (a 1.6 nail gap behind the grip), grip 6.65..8.25. ASSUMED
HDL_FILLET = (0.3, 0.2, 0.1)  # the legs' stepped root fillet, round their sides and top, on the 5.05, 5.25 and 5.45
                       # layers (all black). ASSUMED
HDL_BOSS_HALF = HDL_HALF + HDL_FILLET[0]            # 5.944: a white boss under the handle, as wide as the legs' first
HDL_BOSS_TOP = RAIL_Z0 + HDL_HT + HDL_FILLET[0]     # fillet step, the rail carried up to 9.987, 0.034 under groove 1. DERIVED
CUR_WEIGHT_G = 11.68   # the curtain's weight, from the addendum's review test slice (11.55 g white, 0.13 g black).
                       # DERIVED (used for the holds); sliced again Nov 3 2026: 11.54 + 0.13 g
STUB_WEIGHT_G = 6.30   # the fit test's half door, sliced alone (Nov 3 2026: 6.19 g + 0.12 g): a little over half the
                       # real door, as its handle is full size. DERIVED (used for its hold)

# Alan's standard layout for the garages (CONFIRMED: designer-standards.js on yoder-storage-barns.com, his
# copy-this-build codes, Aug 2026; read Nov 3 2026, Alan: "go on yoder-storage-barns.com to see standard
# layout"): the walk door on the same end as the roll-up, its edge 4 ft in from the corner, and the window
# centred between the walk door and the back. It replaces the designer's stock places (door 7.6 ft toward
# the back end, window 7.6 ft toward the roll-up end, model/loadouts.js)
# in-swing steel door: designer d36in (36 x 75.6 in), hinged on its -y edge (left from outside, the
# roll-up end's side). BARNWRIGHT. It swings IN on two pins.
DOOR_OPEN_W = 36 * S
DOOR_OPEN_H = 75.6 * S
DOOR_YC = -6.5 * FT    # -55.033: 6.5 ft from the middle toward the roll-up end (d36in pos -(L/2 - 5.5)), opening
                       # y -67.733..-42.333, its -y edge 48 in from the outside of the roll-up end, on the 4 ft
                       # layout mark. CONFIRMED (standard layout, above)
JAMB = DOOR_OPEN_W / 2
DOOR_R = 1.0           # half the door's thickness (2.0; real 1 3/4 in would be 1.23); the hinge edge is rounded
DOOR_GAP = 0.35        # gap at hinge and latch edges
DOOR_AXIS_U = 1.6      # hinge pin line out from the wall's INSIDE face: the 2.7 holes reach down to u 0.25,
                       # the top of the first layer, so the bed face stays whole, and the door swings in about
                       # 100 degrees (the four new models' in-swing door, Nov 3 2026). ASSUMED
AXIS_X = W / 2 - WT + DOOR_AXIS_U
AXIS_Y = DOOR_YC - JAMB + DOOR_R + DOOR_GAP
DOOR_W = (DOOR_YC + JAMB - DOOR_GAP) - AXIS_Y   # pin line to latch edge
DOOR_BOTTOM_GAP = 0.3
DOOR_TOP_GAP = 0.6
DOOR_H = DOOR_OPEN_H - DOOR_BOTTOM_GAP - DOOR_TOP_GAP
PIN_D = 2.0
PIN_HOLE_D = 2.7       # 0.35 mm round the pin: holes print small (Alan, Oct 31 2026)
PIN_BOTTOM_LEN = 1.3   # rests on the bottom of a 1.0 deep hole
PIN_TOP_LEN = 2.0
HOLE_BOTTOM_DEPTH = 1.0
TRENCH_DEPTH = 0.7     # the slot the bottom pin slides in through, from the room side; 0.3 shallower than the hole
HOLE_TOP_DEPTH = 2.2
STOP = [(0.0, 2.45), (0.8, 3.25), (0.8, WT), (0.0, WT)]   # the stop on the latch jamb, outside the shut door:
                       # (into the opening from the jamb face, u). 45 degree underside from the 2.45 layer
                       # line, 0.2 clear of the door's outside face at its latch edge, over it 0.45, so the
                       # door only swings in
PANEL_COLS = [(0.170, 0.435), (0.565, 0.830)]   # six raised panels, as fractions of the OPENING's width from its
PANEL_ROWS = [(0.064, 0.300), (0.369, 0.758), (0.822, 0.945)]   # hinge-side jamb and of its height from the floor,
                       # as door-steel.js draws them (dL + w * 0.170, yb + h * fraction). BARNWRIGHT. The same door as
                       # the 12x24 Garage's (final audit, Nov 4 2026: they were fractions of the slab, 0.2 to 0.55 off)
PANEL_GROOVE = (0.5, 0.4)   # each panel outlined by a groove this wide and deep
KNOB = (0.32 * FT, 0.44, 1.8, 1.2)   # in from the latch edge, up the door, diameter, standing off. BARNWRIGHT

# window: 2x3 (2.1 x 2.9 ft), designer w23. BARNWRIGHT size
WIN_W = 2.1 * FT
WIN_H = 2.9 * FT
WIN_TOP = 74.8 * S     # Alan's lofted-wall rule: the 5 in loft header right under the top plate. ASSUMED
                       # (carried over, CONFIRMED on the Side Lofted Barn, Nov 2 2026). The designer has
                       # 77.8 in; open question 2 (75.6 in would line up with the door)
WIN_YC = 3.5 * FT      # +29.633: 3.5 ft from the middle toward the back end, halfway between the walk door's
                       # back edge (-5 ft) and the back (+12 ft); opening y 20.743..38.523. CONFIRMED (standard
                       # layout, above: the R wall's w23 pos 3.5)

# roof sheets
ROOF_T = 2.0
RIB_OC = 9 * S
TAIL = 4 * S           # the upper sheet runs on 4 in past the knee, lapping over the lower one
LAP_GAP = 0.45         # gap between that tail and the top of the lower sheet (proven, Nov 2 2026)
PEG_D, PEG_UP = 2.2, 1.0
PEG_HOLE_D, PEG_HOLE_UP = 3.0, 1.4   # 0.4 mm round the peg
PEG_X = KNEE_X / 2     # the upper sheets' pegs, halfway up the shallow slope
LOWER_HOLE_SHIFT = (PEG_HOLE_D - PEG_D) / 2
PEG_Y = L / 2 - WT + PEG_D / 2   # against the end walls' inside face, so each peg prints lying on the bed

# snap joints, no glue: the same as the base models (Alan, Nov 1 2026), held in mm as above. Each wall
# stands on top of the floor with its siding hanging down over the floor's edge. Under every stud a
# post drops into a notch in the floor's edge, and a few prongs click into slots in the floor. A
# prong is a springy leg with a barb on its foot that catches under a ledge at the bottom of the
# slot, and beside it a stiff stop. The LONG walls go on first and the end walls last.
FIT = 0.2              # gap round every post, prong and peg (0.2 a side is snug)
PRONG_W = 3.0          # the leg's width along the wall
PRONG_T = 0.8          # its thickness, the way it bends (4 layers)
BARB = 0.65            # the barb stands this far in from the leg, down to the bed (3 layers)
CATCH = BARB - FIT     # how far it hooks under the ledge
BARB_LAND = 0.6        # straight face between the barb's flat top and its 45 degree lead-in
LEDGE_Z = ZF - 5.25    # the ledge, 1.57 mm up from the bottom of the floor, on a layer line of the
                       # upside-down floor (first layer 0.25, then 0.2)
STOP_W, STOP_GAP, STOP_H = 1.2, 0.4, 3.0   # the stop: width, gap from the leg, how far down it goes
STOP_U = 2.05          # how deep the stop is, on a layer line of the wall's print
SLOT_U = STOP_U + 0.15 # the slot's outside wall
LEG_ROOT = ZF + 1.2    # the leg is freed up to here, in the bottom plate
BARB_RELIEF = 0.1      # the barb's top is this much lower on its first layer, for first-layer squish
MITRE_GAP = 0.1        # relief between mitred ends, so they slide past each other going on
MITRE_BEVEL = 0.6      # a 45 degree bevel along the top of each long wall's mitre (review, Nov 2 2026)
# where the prongs are along each wall, from its middle (the stop is on the side toward the nearer
# corner). Long walls: bay centres between studs and between joists, clear of the door's sill and the
# outer skids' pegs, and the same on both long walls (each outer skid has a relief under them and is
# one part turned end for end). The door side's +40 in prong is under the window, hanging from the
# bottom plate, its leg rooted 27 mm under the sill. Roll-up end: under the doorway's jambs, x -36.2 and +36.2
# (51.3 in), legs rooted in the bottom plate, each between the curtain post at 35 in and the end stud (lift-out
# addendum). Back end: the bay next to the -x corner is only 4.6 mm, so one bay in there. ASSUMED
PRONG_SPOTS = {
    "door side": [a * S for a in (-120, -40, 40, 120)],
    "plain side": [a * S for a in (-120, -40, 40, 120)],
    "roll-up end": [-36.2, 36.2],
    "back end": [-(51 + 35) / 2 * S, (45 * S + W / 2 - WT - SW / 2) / 2],
}

# the corners: a band pulls the mitres shut and a black corner angle is glued into a recess in both
# walls at each corner (Alan, Nov 3 2026). Held in mm, the same in all four new models
POCKET_D = 0.4         # the recess: 2 layers of the walls' print (siding top 5.05, recess floor 4.65)
POCKET_CLR = 0.15      # the recess reaches each leg's reach + this along each wall, and this over its top
CORNER_CHAMFER = 1.15  # the walls' outside corner is cut off square to the mitre, this far past where the
                       # recess floors meet; it cuts each recess floor 1.55 from the corner
ANGLE_T = 1.05         # each leg of an angle, 5 layers thick
ANGLE_P = ANGLE_T - POCKET_D   # 0.65, how far an angle stands out of the siding
ANGLE_REACH = 3.0      # the long-face leg covers this much of the long wall from the corner: 1.45 mm of
                       # glue on its recess floor (at the scale trim width, 2.47, only 0.92). ASSUMED (open
                       # question 12: 4 1/4 in against a 3 1/2 in board)
ANGLE_UP = 0.25 + 17 * 0.2     # 3.65, the end-face leg's width, standing up in the print: 18 layers, on a
                       # layer line; it covers 3.0 of the end wall
ANGLE_FILLET = 0.8     # 45 degree fillet in an angle's inside corner (review, Nov 3 2026)
ROOF_CLR = 0.2         # the walls' top edges and the angles keep this clear of the lower roof sheets
RAKE_CLR = 0.15        # an angle's end-face leg stops this far under the rake board / front band

# loft: 2x6 joists 16 in apart and a deck, 4 ft in from the outside of each end wall, on the long walls'
# top plates. BARNWRIGHT, assumed in the designer too (styles.LBG.loft.assumed; open question 8)
LOFT_DEPTH = 4 * FT
LOFT_JOIST = 5.5 * S
LOFT_DECK = 1.0
LOFT_Z = ZWT - 0.15    # bottom of the loft joists: the top of the long walls
LOFT_CLR = 0.4         # clear of the steep roof sheets, square to them
LOFT_END = 0.4         # gap between a loft and the end wall
LUG_U = 1.8            # a lug under two of the joists at each wall drops into an open notch through the
LUG_D = PLATE_TOP - 0.15 - FIT   # whole top plate (1.767 deep), FIT round it (Nov 3 2026 reconciliation)
LUG_JOISTS = (0, -1)   # the end joist and the edge joist, the same distance from the loft's middle
NOTCH_FILL = 0.3       # 45 degree fill in the corner end of each end joist's notch (notch_fills())

# skids: four treated 4x6 on edge, centres 8 in and 37 in in from each side. BARNWRIGHT
# (construction.json skids.table {"12": [8, 37]}; open question 9)
SKID_W = 3.5 * S
SKID_H = 5.5 * S
SKID_IN_X = W / 2 - 37 * S    # 21.167: the inner pair, notched for the joists like the base models' skids
SKID_OUT_X = W / 2 - 8 * S    # 41.628: the outer pair, under the rim band, flat on top
NOTCH = 0.6
NOTCH_CLEAR = 0.6      # 0.3 mm each side of a joist
SKID_PEG_D, SKID_PEG_UP = 2.0, 2.5   # a peg at each end of an inner skid pushes into the floor's end band
OUTER_SKID_H = SKID_H - NOTCH        # 3.281: so all four skids' bottoms are level
OUTER_PEG_D, OUTER_PEG_UP = 1.6, 2.5 # two pegs on each outer skid push into the rim band
OUTER_HOLE_UP = 2.8
OUTER_PEG_X = SKID_OUT_X + 0.32      # 0.32 out on the skid, so its hole keeps a 0.48 web to the joist pocket
SKID_RELIEF = 0.3      # under each long-wall prong the outer skid is cut down this much
SKID_RELIEF_X = W / 2 - WT - 0.4     # from here outward, 0.4 inside the barbs
SKID_BRIM = {"brim_type": "outer_only", "brim_width": "5"}   # PRINTER-BRAIN: long thin parts get a 5 mm brim
NO_BRIM = {"brim_type": "no_brim"}   # corner angles and roof sheets: a brim lip would show
# Every wall, and every fit-test piece cut from one, lays its siding's first layer across the studs. Left to
# itself, Flash Studio picks the direction afresh each slice, and the same file doesn't always come out the same:
# it bridged the door side's four bays beside the steel door lengthwise, 55 mm strands, in about half of the slices,
# and the half doorway's two end bays every time (final audit, Nov 4 2026). The plain side's and both barn ends'
# bays are just as long the other way (54 mm), so the slices that happened to lay them across prove nothing (bridge
# audit, Nov 4 2026). So each wall carries a modifier over its siding, from SIDING_BRIDGE_Z up, that sets External
# bridge infill direction 180, which Flash Studio reads as along the bed's X: across the studs, 15.7 mm at most. On a
# barn end it stops at GABLE_SPLIT_Z, the middle of the collar tie: over it, lines across would run 31 mm from the
# king post to the chords, leaving 162 mm2 they can't hold, and left to itself the slicer could lay them 32 mm. A
# second modifier there sets UP_THE_GABLE, 90, along the bed's Y: from the collar tie up to the chords, 9.1 mm at
# most. They start over the framing, so the prong legs' first layer (0.65) and the rebate's ceiling (1.65) keep the
# slicer's own direction, along the leg and between the ribs, as on the walls that print as proven. The fit test's
# short plain side and short roll-up end carry it too, so the corner prints the way the real walls do: left to itself,
# the slicer laid the short plain side's siding along its bays. The modifier also moves a little hidden solid infill,
# not on every piece alike: on the 1.45 layer the plain side's two solid lines along each mitred end become one (the
# other walls' are unchanged), and on the fit test the short roll-up end's two along its mitre become one while the
# short plain side keeps both; and some lines along the siding's top edge move on its first layer (bridge review and
# floor review, Nov 4 2026). No face or fit changes. ASSUMED (as sliced)
ACROSS_STUDS = {"bridge_angle": "180"}
UP_THE_GABLE = {"bridge_angle": "90"}
SIDING_BRIDGE_Z = SD - 0.5           # 3.204: under the siding's first layer (3.65 to 3.85), over the 2.85 one


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
    """Polygon (or CrossSection) in two axes (ax0, ax1), extruded d along the third axis h from
    h=0. Built as a right-handed map whatever the axes are."""
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


def raw_marks(length):
    """Stud centres along a wall of this length, from its middle: 16 in apart from one end, and a
    double stud at every 4 ft mark, the mark falling between the touching pair (Alan, Sep 28 2026).
    Long walls are laid out from -y, end walls from -x, as the base models."""
    out, k = [], 1
    while k * 16 * S < length - 0.01:
        a = k * 16 * S
        out += [a - 0.75 * S, a + 0.75 * S] if k % 3 == 0 else [a]
        k += 1
    return [a - length / 2 for a in out]


def stud_marks(length):
    """The marks whose stud stays clear of the end studs by 0.2, so no stud is hidden inside the
    solid corner: at 134 in the mark 61 in toward +x runs into the corner and is left out
    (DROPPED_MARKS)."""
    lim = length / 2 - WT - SW - 0.2
    return [a for a in raw_marks(length) if abs(a) + SW / 2 < lim]


LONG_STUDS = stud_marks(L)
END_STUDS = stud_marks(W)


# ---------------------------------------------------------------- walls and their framing
# each wall as (axis it faces along, side): along a wall is y for the long walls, x for the ends.
# Alan calls the long walls side walls and the short ones end walls (Sep 28 2026).
WALL_SIDE = {"door side": (0, 1), "plain side": (0, -1), "back end": (1, 1), "roll-up end": (1, -1)}


def wall_box(name, a0, a1, u0, u1, z0, z1):
    """A box on one wall: a along the wall, u out from its inside face, z up."""
    axis, sign = WALL_SIDE[name]
    half = (W / 2, L / 2)[axis]
    n0, n1 = sorted([sign * (half - WT + u0), sign * (half - WT + u1)])
    return box(n0, n1, a0, a1, z0, z1) if axis == 0 else box(a0, a1, n0, n1, z0, z1)


def face_prism(name, poly, u0, u1):
    """A polygon in (a along the wall, z), from u0 to u1 out from the wall's inside face."""
    axis, sign = WALL_SIDE[name]
    half = (W / 2, L / 2)[axis]
    n0, n1 = sorted([sign * (half - WT + u0), sign * (half - WT + u1)])
    t = [0.0, 0.0, 0.0]
    t[axis] = n0
    return prism(poly, 1 - axis, 2, axis, n1 - n0).translate(t)


def wall_section(name, poly, a0, a1):
    """A polygon in (u out from the wall's inside face, z), from a0 to a1 along the wall."""
    axis, sign = WALL_SIDE[name]
    half = (W / 2, L / 2)[axis]
    pts = [(sign * (half - WT + u), z) for u, z in poly]
    t = [0.0, 0.0, 0.0]
    t[1 - axis] = a0
    return prism(pts, axis, 2, 1 - axis, a1 - a0).translate(t)


def openings(name):
    """The framed openings in a wall: [(kind, a0, a1, z0, z1)], a along the wall."""
    if name == "door side":
        return [("window", WIN_YC - WIN_W / 2, WIN_YC + WIN_W / 2, ZF + WIN_TOP - WIN_H, ZF + WIN_TOP),
                ("steel door", DOOR_YC - JAMB, DOOR_YC + JAMB, ZF, ZF + DOOR_OPEN_H)]
    if name == "roll-up end":
        return [("roll-up", -RU_W / 2, RU_W / 2, ZF, ZF + RU_H)]
    return []


# Alan's doorway rules (designer docs/BUILDING-TERMS.md, part-doorway-frame skill; CONFIRMED): a
# full-height stud and inside it his king stud each side; the window gets his 5 in loft header, the
# steel door two flat 2x4s, the roll-up no header (king studs to the top plate)
HEADERS = {"window": HEADER, "steel door": FLAT_HEADER, "roll-up": 0.0}
SIDE_WORDS = {"window": ("roll-up-end-side", "back-end-side"), "steel door": ("hinge-side", "latch-side"),
              "roll-up": ("left-hand (from outside)", "right-hand (from outside)")}
LONG_OF_END = {1: "door side", -1: "plain side"}


def mark_layout(name):
    """Every 16 in layout mark on a wall and what stands on it: [(mark, kind, detail)]. kind is
    "stud"; "inside" (inside an opening: a cripple over its header, a stud under a window plate, or
    nothing over the roll-up), detail the opening; or "dropped", detail (what its stud would hit,
    how far it would overlap it). The shed-measurements skill: an unresolved collision needs a
    layout decision, not a hidden shift, so each dropped mark is listed (open question 13). A stud
    standing exactly on an opening's stud (the door side's -96.75 in, on the door's hinge-side king
    stud: the door's edge is on the 4 ft mark) is dropped too: the framing it hits stands there (F8)."""
    axis = WALL_SIDE[name][0]
    length = (L, W)[axis]
    keep = stud_marks(length)
    out = []
    for m in raw_marks(length):
        a, b = m - SW / 2, m + SW / 2
        if not any(abs(m - k) < 1e-9 for k in keep):
            side = 1 if m > 0 else -1
            out.append((m, "dropped", (f"past the end stud, into the {LONG_OF_END[side]}'s corner",
                                       abs(m) + SW / 2 - (W / 2 - WT))))
            continue
        hit = None
        e = 1e-6                             # a stud edge on an opening's edge (the door's on the 4 ft mark)
        for op in openings(name):
            kind, a0, a1, z0, z1 = op
            if a >= a0 - e and b <= a1 + e:
                hit = ("inside", op)
                break
            studs = [((a0 - 2 * SW, a0 - SW), 0, "full"), ((a0 - SW, a0), 0, "king"),
                     ((a1, a1 + SW), 1, "king"), ((a1 + SW, a1 + 2 * SW), 1, "full")]
            best = max(studs, key=lambda s: min(b, s[0][1]) - max(a, s[0][0]))
            ov = min(b, best[0][1]) - max(a, best[0][0])
            if ov > e or (b > a0 + e and a < a1 - e):
                hit = ("dropped", (f"the {kind}'s {SIDE_WORDS[kind][best[1]]} {best[2]} stud", max(ov, 0.0)))
                break
        out.append((m, "stud", None) if hit is None else (m, hit[0], hit[1]))
    return out


# every layout mark left out, as (wall, mark in inches from the wall's middle (toward +x on the end
# walls, toward the back end on the long walls), what its stud would hit, overlap in mm)
DROPPED_MARKS = [(name, round(m / S, 2), det[0], round(det[1], 3))
                 for name in WALL_SIDE for m, kind, det in mark_layout(name) if kind == "dropped"]


def wall_framing(name):
    """Plates, end studs, layout studs and the framing round each opening, the full stud depth
    (u 0 to SD), so the wall prints lying flat on it. Alan's words: beside each opening a
    full-height stud, and against it the king stud that carries the header; studs on the layout
    marks fill above the header to the top plate; under a window the flat window plate, on studs
    that keep to the wall's layout; the bottom plate is cut across a doorway (by the opening)."""
    axis = WALL_SIDE[name][0]
    if axis == 0:
        run = L / 2 - WT                     # between the end walls' inside faces
        ends = [(-run, -run + SW), (run - SW, run)]
    else:
        run = W / 2 - TS                     # the end walls' plates run into the mitres
        xe = W / 2 - WT - SW / 2             # end studs just inside the long walls
        ends = [(-xe - SW / 2, -xe + SW / 2), (xe - SW / 2, xe + SW / 2)]
    sz0, sz1 = ZF + PLATE_BOT, ZWT - PLATE_TOP

    def fb(a0, a1, z0, z1):
        return wall_box(name, a0, a1, 0, SD, z0, z1)
    parts = [fb(-run, run, ZF, sz0), fb(-run, run, sz1, ZWT)] + [fb(a, b, sz0, sz1) for a, b in ends]
    for kind, a0, a1, z0, z1 in openings(name):
        hdr = HEADERS[kind]
        for a, b in ((a0 - 2 * SW, a0 - SW), (a1 + SW, a1 + 2 * SW)):            # full-height studs
            parts.append(fb(a, b, sz0, sz1))
        for a, b in ((a0 - SW, a0), (a1, a1 + SW)):                              # king studs
            parts.append(fb(a, b, sz0, z1 if hdr > 0 else sz1))
        if hdr > 0:
            parts.append(fb(a0 - SW, a1 + SW, z1, min(z1 + hdr, sz1)))           # header
        if z0 > ZF + 1:
            parts.append(fb(a0, a1, z0 - SW, z0))                                # window plate
    studs = []                                                                  # (a, b, z0, z1)
    for m, kind, det in mark_layout(name):
        a, b = m - SW / 2, m + SW / 2
        if kind == "stud":
            studs.append((a, b, sz0, sz1))
        elif kind == "inside":
            okind, a0, a1, z0, z1 = det
            hdr = HEADERS[okind]
            if hdr > 0 and sz1 - (z1 + hdr) > 0.05:                              # cripple over the header
                studs.append((a, b, z1 + hdr, sz1))
            if z0 > ZF + 1:                                                     # under the window plate
                studs.append((a, b, sz0, z0 - SW))
    # a double stud is a touching pair (1 1/2 in apart at 1 1/2 in thick): made as one box, so the
    # two don't meet on a bare face
    studs.sort(key=lambda s: (s[2], s[3], s[0]))
    merged = []
    for s in studs:
        last = merged[-1] if merged else None
        if last and abs(last[2] - s[2]) < 1e-9 and abs(last[3] - s[3]) < 1e-9 and abs(last[1] - s[0]) < 1e-6:
            merged[-1] = (last[0], s[1], s[2], s[3])
        else:
            merged.append(s)
    return parts + [fb(*s) for s in merged]


def post_spans(name):
    """(start, end) along the wall of each post under it, from z = 0 up to the bottom plate: one
    under every layout stud on a long wall, and the door side's sill under the whole steel door's
    framing; on the end walls one under each end stud, under the back end's layout studs but the
    double at 28.25/29.75 in (an inner skid's peg hole is there) and one in the bay beside it, and
    under the roll-up's doorway at CURTAIN_POSTS (none under its jambs: the prongs are there). Under the
    floor top the siding is a skirt that, in the wall's print, bridges from post to post, so no two posts
    are over 20 mm apart."""
    axis = WALL_SIDE[name][0]
    marks = [m for m, kind, _ in mark_layout(name) if kind != "dropped"]
    if axis == 0:
        spans = [(m - SW / 2, m + SW / 2) for m in marks]
        if name == "door side":
            d0, d1 = DOOR_YC - JAMB - 2 * SW, DOOR_YC + JAMB + 2 * SW
            spans = [s for s in spans if s[1] < d0 or s[0] > d1] + [(d0, d1)]
    else:
        xe = W / 2 - WT - SW / 2
        spans = [(-xe - SW / 2, -xe + SW / 2), (xe - SW / 2, xe + SW / 2)]
        if name == "roll-up end":
            spans += [(c - SW / 2, c + SW / 2) for c in CURTAIN_POSTS]
        else:
            skip = (28.25 * S, 29.75 * S)
            spans += [(m - SW / 2, m + SW / 2) for m in marks if not any(abs(m - k) < 1e-6 for k in skip)]
            spans.append((BACK_END_EXTRA_POST - SW / 2, BACK_END_EXTRA_POST + SW / 2))
    # a double stud's two posts touch: one post under the pair, so they don't meet on a bare face
    merged = []
    for a, b in sorted(spans):
        if merged and a <= merged[-1][1] + 1e-6:
            merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
        else:
            merged.append((a, b))
    return merged


def prong_spots(name):
    return PRONG_SPOTS[name]


def prong_spans(ac):
    """(leg, stop): where the leg and the stop of the prong at ac are along the wall. The stop
    is on the side toward the nearer corner."""
    s = 1 if ac >= 0 else -1
    leg = (ac - PRONG_W / 2, ac + PRONG_W / 2)
    stop = sorted([ac + s * (PRONG_W / 2 + STOP_GAP), ac + s * (PRONG_W / 2 + STOP_GAP + STOP_W)])
    return leg, tuple(stop)


def prong(name, ac):
    """The prong at ac along a wall. The leg hangs from the bottom plate
    BARB off the wall's inside face; in the print it bridges from there to its barb, which stands
    on the bed. The barb's flat top catches under the ledge; below it a straight face and a 45
    degree lead-in that pushes the leg out as it goes down the slot."""
    (a0, a1), (b0, b1) = prong_spans(ac)
    zc = LEDGE_Z - FIT                                  # flat top of the barb, under the ledge
    zl = zc - BARB_LAND - BARB                          # foot of the lead-in
    barb = [(BARB + 0.1, zc), (0.25, zc), (0.25, zc - BARB_RELIEF), (0, zc - BARB_RELIEF),
            (0, zc - BARB_LAND), (BARB, zl), (BARB + 0.1, zl)]
    return [wall_box(name, a0, a1, BARB, BARB + PRONG_T, zl - 0.05, LEG_ROOT + 0.01),
            wall_section(name, barb, a0, a1),
            wall_box(name, b0, b1, 0, STOP_U, ZF - STOP_H, ZF + 0.3)]


def prong_leg(name, ac):
    """The leg itself, from its foot to LEG_ROOT."""
    (a0, a1), _ = prong_spans(ac)
    zc = LEDGE_Z - FIT
    return wall_box(name, a0, a1, BARB, BARB + PRONG_T, zc - BARB_LAND - BARB - 0.05, LEG_ROOT)


def prong_relief(name, ac):
    """The slot round the top of the prong's leg, 0.2 all round, so the leg bends from LEG_ROOT.
    It is inside the bottom plate: its inside face is whole."""
    (a0, a1), _ = prong_spans(ac)
    return (wall_box(name, a0 - 0.2, a1 + 0.2, BARB - 0.2, BARB + PRONG_T + 0.2, ZF - 0.5, LEG_ROOT)
            - wall_box(name, a0, a1, BARB, BARB + PRONG_T, ZF - 1, LEG_ROOT + 1))


def under_floor(name):
    """What a wall has below the top of the floor besides its siding: the posts and prongs."""
    parts = [wall_box(name, a0, a1, 0, SD + EMBED, 0, ZF + 0.3) for a0, a1 in post_spans(name)]
    for ac in prong_spots(name):
        parts += prong(name, ac)
    return parts


# ---------------------------------------------------------------- floor
def joist_ys():
    """The floor joists between the solid bands at the ends, 16 in apart from -y."""
    return layout(-L / 2, L / 2, 16 * S)


def outer_peg_y():
    """Along the garage, where each outer skid's pegs are: in the end bay of the rim band, halfway
    between the notch for the post at the last layout stud and the floor's corner cut."""
    a = LONG_STUDS[-1] + SW / 2 + FIT
    b = L / 2 - WT - SW - FIT
    return (a + b) / 2


OUTER_PEG_Y = outer_peg_y()   # 93.14. DERIVED


def floor_cuts():
    """The notches, slots and holes in the floor: a notch round each post and the door sill, a
    slot for each prong, the corners where the corner posts go down, a hole in each end band for an
    inner skid's peg, and two in each long side's rim band for an outer skid's pegs."""
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
    cuts += corner_cuts() + skid_holes()
    return cuts


def corner_cuts():
    """Where the corner posts and the end walls' end studs go down through the floor's corners."""
    c, out = FIT, []
    for sx in (1, -1):
        for sy in (1, -1):
            for dx, dy in ((0, SW), (SW, 0)):              # long wall's corner post, end wall's end stud
                xa, xb = sorted([sx * (W / 2 - WT - dx - c), sx * W])
                ya, yb = sorted([sy * (L / 2 - WT - dy - c), sy * L])
                out.append(box(xa, xb, ya, yb, -1, ZF + 1))
    return out


def skid_holes():
    """The holes the skids' pegs push into: inner skids at each end band, outer skids in the rim band."""
    out = []
    for sx in (1, -1):
        for sy in (1, -1):
            out.append(cyl_z(sx * SKID_IN_X, sy * (L / 2 - TS - FLOOR_CLR - RIM / 2), -1, SKID_PEG_UP + 0.3,
                             SKID_PEG_D + 2 * FIT))
            out.append(cyl_z(sx * OUTER_PEG_X, sy * OUTER_PEG_Y, -1, OUTER_HOLE_UP, OUTER_PEG_D + 2 * FIT))
    return out


# the floor sheets: 4x8 sheets in rows 4 ft wide across the width, each next row started with a 4 ft
# piece (Alan, Sep 27 2026). At 134 x 288 in: rows 48, 48 and 38 in wide from -x; rows 1 and 3 three
# 8 ft sheets, row 2 a 4 ft, two 8 ft and a 4 ft. DERIVED
SHEET_ROWS = [((-67, -19), (-48, 48)), ((-19, 29), (-96, 0, 96)), ((29, 67), (-48, 48))]
LONG_SEAMS = (-19 * S, 29 * S)       # the floor's two long sheet seams, where its three rows meet


def floor_pockets():
    """The cavities between the joists, under the deck, inside the solid bands."""
    xf, yf = W / 2 - TS - FLOOR_CLR, L / 2 - TS - FLOOR_CLR
    edges = [-(yf - RIM)] + [e for j in joist_ys() for e in (j - SW / 2, j + SW / 2)] + [yf - RIM]
    return [box(-xf + RIM, xf - RIM, a, b, -1, ZF - DECK) for a, b in zip(edges[0::2], edges[1::2])]


def floor():
    """Floor frame and floor sheets. The walls stand on it with their siding hanging down over
    its edge, FLOOR_CLR clear of it. It prints upside down, floor face on the bed."""
    xf, yf = W / 2 - TS - FLOOR_CLR, L / 2 - TS - FLOOR_CLR
    cuts = floor_pockets()
    xi, yi = W / 2 - WT, L / 2 - WT
    for (x0, x1), ys in SHEET_ROWS:                     # seams 0.4 wide, 0.25 deep, inside the walls
        xa, xb = max(x0 * S, -xi), min(x1 * S, xi)
        for y in ys:
            cuts.append(box(xa, xb, y * S - 0.2, y * S + 0.2, ZF - 0.25, ZF + 0.01))
    for x in LONG_SEAMS:
        cuts.append(box(x - 0.2, x + 0.2, -yi, yi, ZF - 0.25, ZF + 0.01))
    return box(-xf, xf, -yf, yf, 0, ZF) - union(cuts + floor_cuts())


FLOOR_TO_PRINT = [[1, 0, 0], [0, -1, 0], [0, 0, -1]]     # upside down


# ---------------------------------------------------------------- gable ends
def knee_inner():
    """The inside corner of the end truss's chords at the knee: where the collar tie's top is."""
    k = np.array([KNEE_X, ZKN])
    dl = unit((W / 2 - KNEE_X, -LOWER_RISE))
    du = unit((-KNEE_X, UPPER_RISE))
    half = math.acos(float(dl @ du)) / 2
    return k + CHORD / math.sin(half) * unit(dl + du)


COLLAR_TOP = float(knee_inner()[1])   # 23.769 over the wall top. DERIVED
GABLE_SPLIT_Z = COLLAR_TOP - COLLAR_H / 2   # a barn end's two bridge modifiers meet here, along the middle of the
                                            # collar tie (see ACROSS_STUDS)


def gable_cs():
    return m3.CrossSection([GABLE])


def end_wall_framing(name):
    """An end wall: plates, studs and opening framing to the top of the wall; above it the 2x6
    gable board on the upper plate, the end truss's four chords under the roof line (CHORD deep)
    with a collar tie across the knees and a king post above it, gable studs 24 in apart standing
    on the gable board, and on the back end only gable backing across the gable 11 in above the
    upper plate (an end with a gable window or faux window has none: part-gable-frame skill).
    Everything runs the full stud depth, so the wall prints lying flat on it."""
    side = WALL_SIDE[name][1]
    yi, yo = (L / 2 - WT, L / 2 - TS) if side > 0 else (-L / 2 + TS, -L / 2 + WT)
    parts = wall_framing(name)
    gb = W / 2 - 1 * S                       # the gable board stops 1 in short of each end
    parts.append(box(-gb, gb, yi, yo, ZWT, ZWT + GABLE_BOARD))
    if name == "back end":
        parts.append(box(-W / 2, W / 2, yi, yo, ZWT + BACKING_Z, ZWT + BACKING_Z + BACKING_H))
    parts.append(box(-W / 2, W / 2, yi, yo, COLLAR_TOP - COLLAR_H, COLLAR_TOP))
    for xc in GABLE_STUD_XS:
        parts.append(box(xc - GABLE_STUD_W / 2, xc + GABLE_STUD_W / 2, yi, yo,
                         ZWT + GABLE_BOARD, COLLAR_TOP - COLLAR_H))
    parts.append(box(-KING_W / 2, KING_W / 2, yi, yo, COLLAR_TOP, ZPK))
    # the chords: a band one 2x4 deep under the roof line, above the wall plates; 0.2 into the
    # siding so they join it
    g = gable_cs()
    band = (g - g.offset(-CHORD, m3.JoinType.Miter)) ^ m3.CrossSection.square([2 * W, 400]).translate([-W, ZWT])
    parts.append(prism_xz(band, yi - (0.2 if side < 0 else 0), yo + (0.2 if side > 0 else 0)))
    gable_shape = prism_xz(GABLE, -L, L)
    return union(parts) ^ gable_shape


def window_unit(yc):
    """Double-hung 2x3 window inside its opening on the door side: two sashes and their muntins,
    no glass, so you can see in (Alan, Oct 31 2026). The sash frames reach 0.2 mm into the jambs
    so they join the wall."""
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
    and none of it out past the siding (Alan, Nov 3 2026), so the end walls change colour only
    once. Returns (frame, cuts, slats): the frame is flush with the siding, filling its grooves,
    with a groove round it; inside the frame the louvre field is recessed to VENT_FLOOR, and four
    slats stand in it, wedges that narrow from the recess floor up to their front edges at the
    siding face, so nothing overhangs in the print. The bottom one stands on the frame's lower bar
    (a gap there would be under a line wide); each leaves VENT_BACK_GAP under the next at the back,
    and the top one the same under the frame's upper bar, so the four gaps and the three free slats
    are over a line wide on every layer."""
    zc = ZPK - VENT_DROP
    yf = side * L / 2

    def slab(x0, x1, z0, z1, d0, d1):
        """A box from d0 to d1 mm out from the siding face."""
        ya, yb = sorted([yf + side * d0, yf + side * d1])
        return box(x0, x1, ya, yb, z0, z1)
    fr, g = 1.0, GROOVE_W
    x0, x1, z0, z1 = -VENT_W / 2, VENT_W / 2, zc - VENT_H / 2, zc + VENT_H / 2
    frame = slab(x0, x1, z0, z1, -EMBED, 0.0)
    cuts = [slab(x0 - g, x1 + g, z0 - g, z1 + g, -GROOVE_D, 1) - slab(x0, x1, z0, z1, -1, 2),   # groove round it
            slab(x0 + fr, x1 - fr, z0 + fr, z1 - fr, VENT_FLOOR, 1)]                        # the louvre field
    pitch = (VENT_H - 2 * fr) / VENT_SLATS
    slats = []
    for i in range(VENT_SLATS):
        zb = z0 + fr + pitch * i
        zt = zb + pitch - VENT_BACK_GAP
        poly = [(yf + side * (VENT_FLOOR - 0.05), zb), (yf, zb), (yf, zb + 0.4), (yf + side * (VENT_FLOOR - 0.05), zt)]
        slats.append(prism(poly, 1, 2, 0, x1 - x0 - 2 * fr).translate([x0 + fr, 0, 0]))
    return frame, cuts, slats


# ---------------------------------------------------------------- the roll-up door
RUE = "roll-up end"


def rbox(x0, x1, u0, u1, z0, z1):
    """A box on the roll-up end: x along it, u out from its inside face, z up."""
    return wall_box(RUE, x0, x1, u0, u1, z0, z1)


def plan_prism(poly, z0, z1):
    """A polygon in (x along the roll-up end, u out from its inside face), from z0 to z1."""
    return prism([(x, -(L / 2 - WT + u)) for x, u in poly], 0, 1, 2, z1 - z0).translate([0, 0, z0])


def mirror_x(m, xm):
    """m mirrored about the plane x = xm."""
    return m.translate([-xm, 0, 0]).mirror([1, 0, 0]).translate([xm, 0, 0])


def latch_outline(grow=0.0):
    """The roll-up's latch plate in (x, z): a rectangle with its corners cut off at 45 degrees."""
    x0, x1 = LATCH_X - LATCH_W / 2 - grow, LATCH_X + LATCH_W / 2 + grow
    z0, z1 = LATCH_Z - LATCH_H / 2 - grow, LATCH_Z + LATCH_H / 2 + grow
    c = LATCH_CUT
    return [(x0 + c, z0), (x1 - c, z0), (x1, z0 + c), (x1, z1 - c), (x1 - c, z1), (x0 + c, z1), (x0, z1 - c), (x0, z0 + c)]


def latch_slot():
    sw, sh = LATCH_SLOT
    return [(LATCH_X - sw / 2, LATCH_Z - sh / 2), (LATCH_X + sw / 2, LATCH_Z - sh / 2),
            (LATCH_X + sw / 2, LATCH_Z + sh / 2), (LATCH_X - sw / 2, LATCH_Z + sh / 2)]


def slat_zs():
    """The middles of the 31 slat grooves, one under each slat but the first (k = 1..31)."""
    return [ZF + RU_SLAT0 + k * RU_PITCH for k in range(1, RU_SLATS)]


def curtain_parts(handle_x=0.0):
    """The lift-out roll-up curtain, seated in its doorway as drawn, in garage coords: (white, black).

    White, up to RAIL_FACE: the slatted body from RAIL_Z0 to Z_FT (a groove under each slat, its top
    front edge bevelled CH_TOP into the dark slit), the bottom zone under it with its front-bottom edge cut
    at 45 degrees (it hangs on the lip's wedge, G_BOT over the floor) and notched round each curtain post,
    both back vertical edges chamfered CUR_CHAMF up to CHAMF_TOP (they bear on the jamb stops), the rail,
    the latch's boss and a boss under the handle; along its top the tongue, notched round the three ribs,
    with a spring finger in each outer segment (a strip over a slot down to the body's top, round root
    corners, a bump under its pad) and a tab in each inner segment (a plate three layers thick, its bump
    pressing on the rebate's front face). Under the latch plate the slat grooves are filled square to the
    latch's rectangle, and the plate's chamfered white boss stands on that fill, so no corner of it is over an
    open groove and no groove is left tapering. Black, from RAIL_FACE (0.01 into the
    white): the latch plate with its slot, and the lift handle at handle_x, two legs with their stepped root
    fillet and the grip. It prints on its back, so u is its print height: the black starts on the 5.05 layer
    and above 5.65 only the handle prints."""
    h, c = CUR_HALF, CUR_CHAMF
    zb = ZF + G_BOT

    def sec(u_top):
        return [(-(h - c), 0), (h - c, 0), (h, c), (h, u_top), (-h, u_top), (-h, c)]
    body = plan_prism(sec(RU_FACE), RAIL_Z0 - 0.01, CHAMF_TOP + 0.01) + rbox(-h, h, 0, RU_FACE, CHAMF_TOP, Z_FT)
    body = body - wall_section(RUE, [(RU_FACE - CH_TOP - 0.01, Z_FT + 0.01), (RU_FACE + 0.01, Z_FT + 0.01),
                                     (RU_FACE + 0.01, Z_FT - CH_TOP - 0.01)], -h - 1, h + 1)
    uc = LIP_U0 + G_BOT - WEDGE_GAP              # 3.80: the wedge edge meets the bottom face here
    bottom = plan_prism(sec(BOT_U), zb, RAIL_Z0) - wall_section(
        RUE, [(uc - 0.01, zb - 0.01), (BOT_U + 0.01, zb - 0.01), (BOT_U + 0.01, zb + BOT_U + 0.01 - uc)], -h - 1, h + 1)
    white = union([body, bottom, rbox(-h, h, 0, TONGUE_T, Z_FT - 0.01, Z_TT),
                   rbox(-h, h, RU_FACE - 0.01, RAIL_FACE, RAIL_Z0, RAIL_TOP),
                   rbox(handle_x - HDL_BOSS_HALF, handle_x + HDL_BOSS_HALF, RU_FACE - 0.01, RAIL_FACE, RAIL_Z0, HDL_BOSS_TOP)])
    cuts = [rbox(-h - 1, h + 1, RU_FACE - RU_GROOVE_D, RU_FACE + 1, z - RU_GROOVE_W / 2, z + RU_GROOVE_W / 2) for z in slat_zs()]
    cuts += [rbox(x - RIB_W / 2 - RIB_CLR, x + RIB_W / 2 + RIB_CLR, -1, TONGUE_T + 1, Z_FT, Z_TT + 1) for x in RIB_XS]
    cuts += [rbox(x - SW / 2 - POST_NOTCH_CLR, x + SW / 2 + POST_NOTCH_CLR, -1, BOT_U + 0.01, ZF - 1, RAIL_Z0)
             for x in CURTAIN_POSTS]
    r, zs = FING_R, Z_TT - FING_H                # the finger slot, FING_SLOT tall, its root corners rounded
    z0 = zs - FING_SLOT
    arc = [(FING_ROOT - r + r * math.cos(a), z0 + r + r * math.sin(a)) for a in np.linspace(-math.pi / 2, 0, 13)]
    arc += [(FING_ROOT - r + r * math.cos(a), zs - r + r * math.sin(a)) for a in np.linspace(0, math.pi / 2, 13)]
    # (12 facets to each quarter round, 7.5 degrees each, as the Garage's 48-sided circle: the same curtain)
    slot = face_prism(RUE, [(FING_TIP - 0.1, z0)] + arc + [(FING_TIP - 0.1, zs)], -1, TONGUE_T + 0.01)   # under the finger only
    zt0 = Z_TT - TAB_W                           # the tab plate's bottom
    tab = union([rbox(TAB_TIP - TAB_GAP, TAB_ROOT, -1, TONGUE_T + 1, zt0 - TAB_SLOT, zt0),
                 rbox(TAB_TIP - TAB_GAP, TAB_TIP, -1, TONGUE_T + 1, zt0 - TAB_SLOT, Z_TT + 1),
                 rbox(TAB_TIP, TAB_ROOT, TAB_T, TONGUE_T + 1, zt0, Z_TT + 1)])
    cuts += [slot, mirror_x(slot, 0), tab, mirror_x(tab, 0)]
    white = white - union(cuts)
    rr = (TAB_W - TAB_BUMP_TOP) / 2
    fbump = rbox(BUMP_X0, BUMP_X1, 0, BUMP_U, Z_TT - 0.01, Z_TT + BUMP_H)
    tbump = wall_section(RUE, [(TAB_T - 0.01, zt0), (TAB_BUMP_U, zt0 + rr), (TAB_BUMP_U, Z_TT - rr), (TAB_T - 0.01, Z_TT)],
                         TAB_BUMP_X0, TAB_BUMP_X1)
    adds = [fbump, mirror_x(fbump, 0), tbump, mirror_x(tbump, 0)]
    boss = face_prism(RUE, latch_outline(), RU_FACE - 0.01, RAIL_FACE) + rbox(
        LATCH_X - LATCH_W / 2, LATCH_X + LATCH_W / 2, RU_FACE - RU_GROOVE_D - 0.01, RU_FACE,
        LATCH_Z - LATCH_H / 2, LATCH_Z + LATCH_H / 2)    # the grooves filled square to the latch's rectangle under it
    plate = (face_prism(RUE, latch_outline(), RAIL_FACE - 0.01, RAIL_FACE + LATCH_T)
             - face_prism(RUE, latch_slot(), RAIL_FACE - 0.5, RAIL_FACE + 1))
    blk = [plate, rbox(handle_x - HDL_HALF, handle_x + HDL_HALF, HDL_U1, HDL_U2, RAIL_Z0, RAIL_Z0 + HDL_HT)]
    for sg in (1, -1):
        xa, xb = sorted([handle_x + sg * (HDL_HALF - HDL_LEG), handle_x + sg * HDL_HALF])
        blk.append(rbox(xa, xb, RAIL_FACE - 0.01, HDL_U1 + 0.01, RAIL_Z0, RAIL_Z0 + HDL_HT))
        for k, f in enumerate(HDL_FILLET):
            blk.append(rbox(xa - f, xb + f, RAIL_FACE - 0.01 + 0.2 * k, RAIL_FACE + 0.2 * (k + 1), RAIL_Z0,
                            RAIL_Z0 + HDL_HT + f))
    black = union(blk)
    return union([white] + adds + [boss]) - black, black


def curtain():
    """The whole curtain, seated as drawn, in garage coords."""
    return union(list(curtain_parts()))


def coil_box():
    """The head over the roll-up doorway between its king studs: behind the siding (u 0..SD) from the
    opening's top to the top plates, so the siding and casing over the 68 mm opening don't bridge. The
    curtain's rebate is cut in its inside face (rebate())."""
    return rbox(-RU_W / 2, RU_W / 2, 0, SD, MOUTH - 0.01, ZWT - PLATE_TOP + 0.01)


def jamb_stops():
    """The two 45 degree stops up the jambs behind the curtain's chamfered back edges, from the floor top
    to RU_STOP_TOP, 0.01 into the king studs so they join them. Each prints narrowing 0.2 a layer; its first
    layer (u 0 to 0.25) starts RU_STOP_FOOT out from the stop's edge, so it can't meet the curtain's first layer."""
    a, e = RU_STOP_X0, RU_W / 2 + 0.01
    poly = [(a + RU_STOP_FOOT, 0), (e, 0), (e, e - a), (a + 0.25, 0.25), (a + RU_STOP_FOOT, 0.25)]
    return [plan_prism([(sg * x, u) for x, u in poly], ZF, RU_STOP_TOP) for sg in (1, -1)]


def threshold_lip():
    """The white threshold lip across the doorway, LIP_H high, its front the siding face and its back the
    45 degree wedge the curtain hangs on, exactly u = LIP_U0 + (z - ZF) right down to its foot 0.01 under ZF
    (0.2 a layer): every layer of the wedge is joined to the skirt under it (u SD up) in its own layer. It stands
    over the floor's edge gap and the skirt, so its 0.01 under ZF touches no floor."""
    return wall_section(RUE, [(LIP_U0 - 0.01, ZF - 0.01), (WT, ZF - 0.01), (WT, ZF + LIP_H), (LIP_U0 + LIP_H, ZF + LIP_H)],
                        -RU_W / 2 - 0.01, RU_W / 2 + 0.01)


def post_extensions():
    """Each curtain post carried on over the floor top up to the lip's top, so the lip and the doorway's
    edge are held at every post."""
    return [rbox(c - SW / 2, c + SW / 2, 0, POST_EXT_U, ZF - 0.01, ZF + LIP_H) for c in CURTAIN_POSTS]


def rebate():
    """The rebate in the head's inside face over the doorway, open to the room: the curtain's tongue goes
    up into it, and its top is the rigid lift stop."""
    return rbox(-RU_W / 2, RU_W / 2, -1, REB_U, MOUTH - 0.01, MOUTH + REB_H)


def rebate_ribs_pads():
    """Put back in the rebate: three ribs across it, which anchor its ceiling's bridges, and the two pads the
    spring fingers' bumps press up against."""
    out = [rbox(x - RIB_W / 2, x + RIB_W / 2, 0, REB_U + 0.01, MOUTH, MOUTH + REB_H + 0.01) for x in RIB_XS]
    return out + [rbox(*sorted([sg * PAD_X0, sg * PAD_X1]), 0, REB_U + 0.01, PAD_Z, MOUTH + REB_H + 0.01)
                  for sg in (1, -1)]


def curtain_regions():
    """Where the curtain's springs are (garage coords, seated as drawn): {name: [box per side]}. The checker
    takes these out of the curtain to tell its springs from its rigid body."""
    zt0 = Z_TT - TAB_W
    out = {"finger strip": [], "finger bump": [], "tab plate": [], "tab bump": []}
    for sg in (1, -1):
        def sb(x0, x1, u0, u1, z0, z1):
            return rbox(*sorted([sg * x0, sg * x1]), u0, u1, z0, z1)
        out["finger strip"].append(sb(FING_TIP, FING_ROOT, -1, TONGUE_T + 0.5, Z_TT - FING_H, Z_TT))
        out["finger bump"].append(sb(BUMP_X0, BUMP_X1, -1, BUMP_U + 0.5, Z_TT, Z_TT + BUMP_H + 0.5))
        out["tab plate"].append(sb(TAB_TIP, TAB_ROOT, -1, TAB_T, zt0, Z_TT))
        out["tab bump"].append(sb(TAB_BUMP_X0, TAB_BUMP_X1, TAB_T, TAB_BUMP_U + 0.5, zt0, Z_TT))
    return out


# ---------------------------------------------------------------- trim
def tbox(name, a0, a1, z0, z1):
    """A trim board on a wall's face: EMBED into the siding, PROUD out of it."""
    return wall_box(name, a0, a1, WT - EMBED, WT + PROUD, z0, z1)


def faux_window():
    """The faux loft window on the roll-up end's gable: trim nailed to the siding, not an opening
    (part-gable-frame skill), a frame FAUX_BAR wide and a triangle in each inside corner; the
    siding shows through it."""
    n = "roll-up end"
    x0, x1 = -FAUX_W / 2, FAUX_W / 2
    z0, z1 = FAUX_ZC - FAUX_H / 2, FAUX_ZC + FAUX_H / 2
    b, t = FAUX_BAR, FAUX_TRI
    p = [tbox(n, x0, x1, z0, z0 + b), tbox(n, x0, x1, z1 - b, z1), tbox(n, x0, x0 + b, z0, z1), tbox(n, x1 - b, x1, z0, z1)]
    for cx, cz, sx, sz in ((x0 + b, z0 + b, 1, 1), (x1 - b, z0 + b, -1, 1), (x0 + b, z1 - b, 1, -1), (x1 - b, z1 - b, -1, -1)):
        e = 0.1                                            # into the bars, so it joins them
        tri = [(cx - sx * e, cz - sz * e), (cx + sx * t, cz - sz * e), (cx + sx * t, cz), (cx, cz + sz * t),
               (cx - sx * e, cz + sz * t)]
        p.append(face_prism(n, tri, WT - EMBED, WT + PROUD))
    return p


def trims():
    """The gable bands (the back end's at the loft line, the roll-up end's at the wall top), the
    rake board round each barn end under the roof, the roll-up's casing, the faux loft window, and
    the steel door's and window's casings (raised so they print in the second colour). The corners
    have no boards printed on the walls: the corner angles are separate. The roll-up's latch plate is
    on the lift-out curtain (curtain_parts())."""
    p = []
    g = gable_cs()
    above = m3.CrossSection.square([4 * W, 400]).translate([-2 * W, ZWT])
    rake = (g.offset(-0.1, m3.JoinType.Miter) - g.offset(-(0.1 + RAKE_W), m3.JoinType.Miter)) ^ above
    gable_shape = prism_xz(GABLE, -L, L)
    for sy, bz in ((1, BACK_BAND_Z), (-1, FRONT_BAND_Z)):
        ya, yb = sorted([sy * (L / 2 - EMBED), sy * (L / 2 + PROUD)])
        p.append(box(-W / 2, W / 2, ya, yb, bz, bz + TRIM) ^ gable_shape)       # gable band
        p.append(prism_xz(rake, ya, yb))                                        # rake board
    n = "roll-up end"
    top = ZF + RU_H
    for s in (1, -1):                                                           # roll-up casing
        a0, a1 = sorted([s * RU_W / 2, s * (RU_W / 2 + TRIM)])
        p.append(tbox(n, a0, a1, ZF, top + TRIM))
    p.append(tbox(n, -RU_W / 2 - TRIM, RU_W / 2 + TRIM, top, top + TRIM))
    p += faux_window()
    n = "door side"
    top = ZF + DOOR_OPEN_H                                                      # steel door casing
    p.append(tbox(n, DOOR_YC - JAMB - TRIM, DOOR_YC - JAMB, ZF, top + TRIM))
    p.append(tbox(n, DOOR_YC + JAMB, DOOR_YC + JAMB + TRIM, ZF, top + TRIM))
    p.append(tbox(n, DOOR_YC - JAMB - TRIM, DOOR_YC + JAMB + TRIM, top, top + TRIM))
    y0, y1 = WIN_YC - WIN_W / 2, WIN_YC + WIN_W / 2                             # window casing, four sides
    z0, z1 = ZF + WIN_TOP - WIN_H, ZF + WIN_TOP
    p.append(tbox(n, y0 - TRIM, y0, z0 - TRIM, z1 + TRIM))
    p.append(tbox(n, y1, y1 + TRIM, z0 - TRIM, z1 + TRIM))
    p.append(tbox(n, y0 - TRIM, y1 + TRIM, z1, z1 + TRIM))
    p.append(tbox(n, y0 - TRIM, y1 + TRIM, z0 - TRIM, z0))
    return p


def casing_sides():
    """The side boards of the door side's casings: [(outer edge y, which way is out, z0, z1)]."""
    dz1 = ZF + DOOR_OPEN_H + TRIM
    wz0, wz1 = ZF + WIN_TOP - WIN_H - TRIM, ZF + WIN_TOP + TRIM
    return [(DOOR_YC - JAMB - TRIM, -1, ZF, dz1), (DOOR_YC + JAMB + TRIM, 1, ZF, dz1),
            (WIN_YC - WIN_W / 2 - TRIM, -1, wz0, wz1), (WIN_YC + WIN_W / 2 + TRIM, 1, wz0, wz1)]


def groove_fills():
    """A siding groove whose edge comes within GROOVE_W of the outside of a casing's side board is
    filled beside that board, from its bottom to its top, so it shows as if under the casing, as the
    grooves over the door do; above and below the board it runs on. With the door on the 4 ft mark
    this is the -56 in groove, 1/2 in past the latch-side casing: the model's grooves are 0.5 mm
    (18 mm at full size, wider than real ones), so it would run 0.1 mm from the casing's edge, a slot
    along it (review, Nov 3 2026). ASSUMED"""
    out = []
    for edge, out_dir, z0, z1 in casing_sides():
        for y in layout(-L / 2, L / 2, GROOVE_OC):
            d = out_dir * (y - edge)                 # the groove's centre out from the casing's edge
            if -GROOVE_W / 2 < d < GROOVE_W * 1.5:   # it straddles the edge or its near edge is within GROOVE_W
                a0, a1 = sorted([edge - out_dir * 0.01, y + out_dir * (GROOVE_W / 2 + 0.01)])
                out.append(wall_box("door side", a0, a1, WT - GROOVE_D - 0.01, WT, z0, z1))
    return out


def eave_line(u):
    """Height of the line ROOF_CLR under the steep lower roof sheets, square to them, u mm out
    from the long walls' siding face (in from it where u < 0)."""
    return ZWT - u * LOW_M - ROOF_CLR * math.sqrt(1 + LOW_M ** 2)


def roof_clearance():
    """What comes out of the walls for the roof: the long walls stop 0.15 under the wall top, so
    the roof bears on the barn ends only, and everything at or outside the long walls keeps
    ROOF_CLR clear of the steep lower sheets, square to them."""
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
        for sy in (1, -1):                                                 # the long walls' corners too
            ya, yb = sorted([sy * (L / 2 - WT), sy * (L / 2 + 1)])
            out.append(box(xa, xb, ya, yb, ZWT - 0.15, ZWT + 0.01) ^ mitred(0, sx))
    return out


# ---------------------------------------------------------------- lofts
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
    """The open notches in the long walls' top plates the loft lugs drop into: FIT round the lug,
    open to the room, from the walls' top down to the top plates' underside exactly (at 1:36 the
    plates stand only 1.97 over it, so a notch stopped short would leave a sliver of plate)."""
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
    joist, along the long wall's inside face. Without it the top plate between that notch and the
    mitre starts on the bed as a sliver about 0.25 wide, which Flash Studio warns about as a
    floating region (barn, Nov 3 2026)."""
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
    notch in the plate, so it can't slide. The lugs are the joist's own width, so in the loft's
    upside-down print they stand straight up off the joist."""
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


# ---------------------------------------------------------------- the steel door's hinge
def door_stop():
    """The stop on the steel door's latch jamb, outside the shut door, the full opening height, so
    the door only swings in. It reaches 0.05 into the jamb so it joins it."""
    yj = DOOR_YC + JAMB
    poly = [(-0.05, STOP[0][1] - 0.05)] + STOP[1:3] + [(-0.05, WT)]
    pts = [(W / 2 - WT + u, yj - d) for d, u in poly]
    return prism(pts, 0, 1, 2, DOOR_OPEN_H).translate([0, 0, ZF])


def door_holes():
    """The hinge pin holes (bottom in the sill post, top in the flat header) and the trench the
    bottom pin slides in along, inward from the bottom hole out through the sill post's inside face.
    No groove in the floor: the door is hung in the loose door side and is captive once that wall is
    on the floor, which closes the trench's mouth: a groove in the floor would have to run 7 to 9 mm
    over the joist cavity before the bottom pin could rise out of it."""
    return [cyl_z(AXIS_X, AXIS_Y, ZF - HOLE_BOTTOM_DEPTH, ZF + 1, PIN_HOLE_D),
            cyl_z(AXIS_X, AXIS_Y, ZF + DOOR_OPEN_H - 1, ZF + DOOR_OPEN_H + HOLE_TOP_DEPTH, PIN_HOLE_D),
            box(W / 2 - WT - 0.01, AXIS_X, AXIS_Y - PIN_HOLE_D / 2, AXIS_Y + PIN_HOLE_D / 2, ZF - TRENCH_DEPTH, ZF + 1)]


def opening_cuts():
    """The openings, through the siding and framing, from 0.5 inside to 2 past the siding face."""
    out = []
    for name in WALL_SIDE:
        for kind, a0, a1, z0, z1 in openings(name):
            out.append(wall_box(name, a0, a1, -0.5, WT + 2, z0, z1))
    return out


def walls():
    """All four walls in one, assembled; wall_pieces() cuts them apart for printing. Built in this
    order (the lift-out addendum's): (1) the siding, framing with the roll-up's coil box between its
    king studs, posts (the curtain posts and end-stud posts on the roll-up end, none under its jambs),
    prongs, trim (no latch plate: it is on the curtain) and groove fills; (2) the openings cut; (3) the
    window, the vent frames, the roll-up's jamb stops, threshold lip and post extensions added; (4) the
    vents cut and their slats added; (5) the steel door's stop added; (6) the pin holes, trench, roof
    clearance and loft notches cut, then the curtain's rebate, and its ribs and pads put back; (7) the
    prongs' reliefs cut LAST, so nothing added after fills them; (8) the roof pegs and notch fills. The
    curtain itself is a separate part (curtain_parts())."""
    shell = prism_xz(GABLE, -L / 2, L / 2)
    # the siding only; below the floor's top it is the skirt that hangs over the floor's edge
    cuts = [box(-W / 2 + TS, W / 2 - TS, -L / 2 + TS, L / 2 - TS, -1, 400)]
    for y in layout(-L / 2, L / 2, GROOVE_OC):                                  # siding grooves
        for sx in (1, -1):
            xa, xb = sorted([sx * (W / 2 - GROOVE_D), sx * (W / 2 + 1)])
            cuts.append(box(xa, xb, y - GROOVE_W / 2, y + GROOVE_W / 2, -1, ZWT + 1))
    for x in layout(-W / 2, W / 2, GROOVE_OC):
        for sy in (1, -1):
            ya, yb = sorted([sy * (L / 2 - GROOVE_D), sy * (L / 2 + 1)])
            cuts.append(box(x - GROOVE_W / 2, x + GROOVE_W / 2, ya, yb, -1, ZPK + 1))
    shell = shell - union(cuts)

    framing = wall_framing("door side") + wall_framing("plain side")
    framing += [end_wall_framing("back end"), end_wall_framing("roll-up end")]
    for name in WALL_SIDE:
        framing += under_floor(name)
    for sx in (1, -1):              # corner posts, solid into the corner so each wall's mitred end is a solid
        for sy in (1, -1):          # 45 degree wedge; they go down through the floor's corners
            xa, xb = sorted([sx * (W / 2 - WT), sx * (W / 2 - TS + 0.01)])     # 0.01 into the siding,
            ya, yb = sorted([sy * (L / 2 - TS + 0.01), sy * (L / 2 - WT - SW)])  # so they don't just touch
            framing.append(box(xa, xb, ya, yb, 0, ZWT))
    b = union([shell] + framing + [coil_box()] + trims() + groove_fills())      # (1)
    b = b - union(opening_cuts())                                               # (2)
    vents = [gable_vent(1), gable_vent(-1)]
    b = union([b] + window_unit(WIN_YC) + [v[0] for v in vents] + jamb_stops() + [threshold_lip()]
              + post_extensions())                                              # (3)
    b = union([b - union([c for v in vents for c in v[1]])] + [sl for v in vents for sl in v[2]])  # (4)
    b = b + door_stop()                                                         # (5)
    b = b - union(door_holes() + roof_clearance() + loft_notches())             # (6)
    b = (b - rebate()) + union(rebate_ribs_pads())
    b = b - union([prong_relief(name, ac) for name in WALL_SIDE for ac in prong_spots(name)])   # (7)
    return b + union(roof_pegs() + notch_fills())                               # (8)


def body():
    """The assembled body: four walls and the floor."""
    return union(list(wall_pieces(walls()).values()) + [floor()])


# the four walls meet at 45 degree mitres through the inside and outside corners, so each wall
# carries only the trim on its own face and it all prints on top (Alan, Nov 1 2026). Each prints
# lying flat on the inside face of its framing, outside up. At each outside corner both walls have
# a recess for a corner angle glued on after (Alan, Nov 3 2026).
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
    """Above the top of the wall plates on one end of the garage: all of it goes with the end
    wall, where it lies on the bed."""
    return M.cube([2 * BIG] * 3, True).trim_by_plane([0, 0, 1], ZWT).trim_by_plane([0, sign, 0], 0)


WALL_CUTS = {
    "door side": mitred(0, 1) - above_plate(1) - above_plate(-1),
    "plain side": mitred(0, -1) - above_plate(1) - above_plate(-1),
    "roll-up end": mitred(1, -1) + above_plate(-1),
    "back end": mitred(1, 1) + above_plate(1),
}
# garage coords to print coords, inside face down (each a rotation, det +1)
WALL_TO_PRINT = {
    "door side": [[0, 1, 0], [0, 0, 1], [1, 0, 0]],
    "plain side": [[0, -1, 0], [0, 0, 1], [-1, 0, 0]],
    "back end": [[-1, 0, 0], [0, 0, 1], [0, 1, 0]],
    "roll-up end": [[1, 0, 0], [0, 0, 1], [0, -1, 0]],
}


def split_walls(w):
    return {name: w ^ cut for name, cut in WALL_CUTS.items()}


def cbox(u0, u1, v0, v1, z0, z1):
    """A box at the (+x, +y) corner: u out from the long wall's siding face, v out from the end
    wall's, z up. The outside corner of the siding is u = v = 0."""
    return box(W / 2 + u0, W / 2 + u1, L / 2 + v0, L / 2 + v1, z0, z1)


def at_corner(m, sx, sy):
    """A part made at the (+x, +y) corner, moved to the corner on side sx of the width and sy of
    the length: mirrored, so each corner gets its own hand."""
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


def angle_reach():
    """How far a corner angle's legs cover each wall's face from the corner: (long wall, end wall)."""
    return ANGLE_REACH, ANGLE_UP - (ANGLE_T - POCKET_D)


def corner_angle(sx=1, sy=1):
    """The black L glued on a corner (Alan, Nov 3 2026), made at (+x, +y) and moved to (sx, sy):
    a leg on each wall's face, ANGLE_T thick, its inside face on the floor of the recess in the
    wall and ANGLE_P of it out of the siding, with a 45 degree fillet in its inside corner. Each leg
    covers 3.0 of its wall from the corner; the end-face leg is ANGLE_UP wide, a whole number of
    layers as it stands in the print. Its foot is level with the bottom of the skirts. Its top keeps
    ROOF_CLR under the lower roof sheets, and the end-face leg stops RAKE_CLR under the rake board
    (back end) or the front band (roll-up end). It prints lying on the long-face leg's outside
    face, the end-face leg standing up."""
    d, f, e = POCKET_D, ANGLE_FILLET, 0.2
    rl, re = angle_reach()
    x, y = W / 2 - d, L / 2 - d                                   # the inside corner of the legs
    fillet = prism([(x - f, y + e), (x - f, y), (x, y - f), (x + e, y - f), (x + e, y + e)], 0, 1, 2, ZWT)
    a = union([cbox(-d, ANGLE_P, -rl, ANGLE_P, 0, ZWT), cbox(-re, ANGLE_P, -d, ANGLE_P, 0, ZWT), fillet])
    return at_corner(corner_top(a, ANGLE_P, ZWT - RAKE_CLR), sx, sy)


def corner_recess(sx=1, sy=1):
    """What comes out of the walls at a corner for its angle, made at (+x, +y) and moved to (sx,
    sy): a recess POCKET_D deep in each wall's face, reaching the leg's reach + POCKET_CLR along it
    from the corner, from under the skirts up to POCKET_CLR over the angle's top; and the walls'
    outside corner cut off at 45 degrees, square to the mitre, CORNER_CHAMFER past where the recess
    floors meet. The long wall's recess has a level top, so the angle presses straight in under
    it. Neither goes higher than the top of the wall plates."""
    rl, re = angle_reach()
    cl, ce, d = rl + POCKET_CLR, re + POCKET_CLR, POCKET_D
    k = -(2 * d + CORNER_CHAMFER)                                 # the chamfer: u + v > k
    h = 1 / math.sqrt(2)
    chamfer = cbox(-4, 2, -4, 2, -1, ZWT).trim_by_plane([h, h, 0], (k + W / 2 + L / 2) * h)
    top = eave_line(ANGLE_P) + ANGLE_P + d + POCKET_CLR           # POCKET_CLR over the angle's inside top edge
    end_recess = corner_top(cbox(-ce, 2, -d, 2, -1, ZWT), ANGLE_P, ZWT - POCKET_CLR, lift=POCKET_CLR)
    return at_corner(union([cbox(-d, 2, -cl, 2, -1, top), end_recess, chamfer]), sx, sy)


CORNERS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
# a corner angle from garage coords to print coords: lying on the long-face leg's outside face, its
# foot at the left, the end-face leg standing up (each a rotation, det +1)
CORNER_TO_PRINT = {1: [[0, 0, 1], [0, 1, 0], [-1, 0, 0]], -1: [[0, 0, 1], [0, -1, 0], [1, 0, 0]]}


def corner_walls(sx, sy):
    """(long wall, end wall) that meet at the corner on side sx, sy."""
    return ("door side" if sx > 0 else "plain side"), ("back end" if sy > 0 else "roll-up end")


def corner_prints():
    """The four corner angles, each lying the way it prints: [(name, part)]."""
    return [("%s at %s" % corner_walls(sx, sy), to_print(CORNER_TO_PRINT[sx], [corner_angle(sx, sy)])[0])
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
    """Everything standing proud of the siding that is trim (gable bands, rake boards, casings,
    faux window). It prints in the second colour."""
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
    """Matrix taking a roof sheet's own coords (X = y along the garage, Y = up from its underside,
    Z = down the slope from a) to garage coords, for the slope from a to b in (x, z)."""
    a = np.asarray(a, dtype=float)
    d = unit(np.asarray(b, dtype=float) - a)
    nrm = np.array([-d[1], d[0]])                  # out of the roof, for a +x slope
    return np.column_stack([[0, 1, 0], [nrm[0], 0, nrm[1]], [d[0], 0, d[1]], [a[0], 0, a[1]]])


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
    """The +x upper roof sheet in garage coords (the -x one is its mirror image): ridge to knee,
    and its tail on past the knee over the lower sheet, with the ridge cap along its top. It sits
    on the barn ends, held by a peg at each end."""
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
    """The +x lower roof sheet in garage coords: knee to eave, its top cut to the line of the
    upper sheet, which laps over it. It sits on the steep edges of the barn ends, on a peg standing
    up at each end, so it only comes off straight up, and the upper sheet's tail is in the way."""
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
    """Lay a +x roof sheet on the bed, underside down: X down the slope, Y along the garage."""
    mat = panel_frame(a, b)
    R, p0 = mat[:, :3], mat[:, 3]
    to_local = np.column_stack([R.T, -R.T @ p0])                          # (y, n, s)
    swap = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], dtype=float)        # (s, y, n), det +1
    p = r.transform(np.column_stack([swap @ to_local[:, :3], swap @ to_local[:, 3]]))
    bb = p.bounding_box()
    return p.translate([-bb[0], -bb[1], -bb[2]])


# ---------------------------------------------------------------- door
def door_slab(dw, dh, panels, knob_y):
    """A steel door in print coords: X across the door from the pin line, Y up the door from its
    bottom, Z through it (Z=0 is the inside face, on the bed). Rounded hinge edge, the two pins,
    the panels' outlines grooved into the outside face (panels: their outer edges (X0, X1, Y0, Y1)
    in these coords), the knob standing off it near the latch edge. All one piece, all white
    (designer: steel doors are always white)."""
    t = 2 * DOOR_R
    slab = box(0, dw, 0, dh, 0, t)
    edge = cyl_y(0, 0, dh, DOOR_R, 2 * DOOR_R)                              # rounded hinge edge
    pin_top = cyl_y(0, dh - 0.5, dh + PIN_TOP_LEN, DOOR_R, PIN_D, 40)
    pin_bot = cyl_y(0, -PIN_BOTTOM_LEN, 0.5, DOOR_R, PIN_D, 40)
    door = union([slab, edge, pin_top, pin_bot])
    gw, gd = PANEL_GROOVE
    grooves = []
    for x0, x1, y0, y1 in panels:
        grooves.append(box(x0, x1, y0, y1, t - gd, t + 1) - box(x0 + gw, x1 - gw, y0 + gw, y1 - gw, t - 2, t + 2))
    door = door - union(grooves)
    kin, _, kd, kup = KNOB
    return door + cyl_z(dw - kin, knob_y, t - 0.1, t + kup, kd)


def door_panels():
    """The six panels' outer edges (X0, X1, Y0, Y1) in door print coords, at the designer's fractions of
    the opening: across from the hinge-side jamb (the pin line is DOOR_R + DOOR_GAP in from it), up from the
    floor (the door's bottom is DOOR_BOTTOM_GAP over it), as door-steel.js and the 12x24 Garage place them."""
    x_jamb, y_floor = -(DOOR_R + DOOR_GAP), -DOOR_BOTTOM_GAP
    return [(x_jamb + c0 * DOOR_OPEN_W, x_jamb + c1 * DOOR_OPEN_W, y_floor + r0 * DOOR_OPEN_H, y_floor + r1 * DOOR_OPEN_H)
            for c0, c1 in PANEL_COLS for r0, r1 in PANEL_ROWS]


def door_parts():
    """The 36 in steel 6-panel door (designer d36in, draw steel-6panel), in print coords."""
    return door_slab(DOOR_W, DOOR_H, door_panels(), KNOB[1] * DOOR_H)


def door_to_shed(theta_deg=0.0):
    """Matrix from door print coords to garage coords, swung theta degrees INTO the garage (the
    latch edge toward -x)."""
    base = np.array([[0, 0, 1, AXIS_X - DOOR_R], [1, 0, 0, AXIS_Y], [0, 1, 0, ZF + DOOR_BOTTOM_GAP]], dtype=float)
    th = math.radians(theta_deg)
    rot = np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]])
    pivot = np.array([AXIS_X, AXIS_Y, 0])
    R = rot @ base[:, :3]
    t = rot @ (base[:, 3] - pivot) + pivot
    return np.column_stack([R, t])


def hang_pose(mat, lift, d, pivot_z, h):
    """mat (a door's shut pose) lifted by lift, then tipped about a horizontal line along the wall
    through the top pin (at pivot_z on the pin line) so the bottom pin's centre, h below the pivot,
    is d mm toward the room (-x). The way the door is hung: top pin up the head hole, pushed up,
    the bottom pin swung out along the trench and dropped."""
    m = mat.copy()
    m[2, 3] += lift
    a = math.asin(max(-1.0, min(1.0, d / h)))
    c, sn = math.cos(a), math.sin(a)
    R = np.array([[c, 0, sn], [0, 1, 0], [-sn, 0, c]])
    piv = np.array([mat[0, 3] + DOOR_R, 0, pivot_z + lift])
    return np.column_stack([R @ m[:, :3], R @ (m[:, 3] - piv) + piv])


# ---------------------------------------------------------------- skids
def skid():
    """An inner skid lying along X, notched where the joists, the floor's end bands and the end
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


def outer_skid():
    """An outer skid lying along X, its outer face at Y = 0: under the floor's rim band and the
    long walls' posts, so no joist notches; flat on top and only SKID_H - NOTCH tall, so its bottom
    is level with the inner skids'. Under each long-wall prong it is cut down SKID_RELIEF from 0.4
    inside the barb outward, so the barb and leg never touch it; two pegs push up into holes in the
    rim band, in the end bay at each end (an end-band hole here would cut into the end studs'
    notches)."""
    h = OUTER_SKID_H
    s = box(0, L, 0, SKID_W, 0, h)
    rw = SKID_OUT_X + SKID_W / 2 - SKID_RELIEF_X
    cuts = []
    for ac in prong_spots("door side"):
        (a0, a1), _ = prong_spans(ac)
        cuts.append(box(a0 - FIT - 1.0 + L / 2, a1 + FIT + 1.0 + L / 2, -1, rw, h - SKID_RELIEF, h + 1))
    s = s - union(cuts)
    py = SKID_OUT_X + SKID_W / 2 - OUTER_PEG_X
    pegs = [cyl_z(L / 2 + sy * OUTER_PEG_Y, py, h - 0.01, h + OUTER_PEG_UP, OUTER_PEG_D) for sy in (1, -1)]
    return s + union(pegs)


def skids_to_shed():
    """[(kind, matrix)]: "inner" places skid() and "outer" places outer_skid() under the floor,
    every skid's bottom at z = -(SKID_H - NOTCH). The -x outer skid is the same part turned end for
    end, so its outer face is out."""
    z = -(SKID_H - NOTCH)
    out = [("inner", np.array([[0, -1, 0, sx * SKID_IN_X + SKID_W / 2], [1, 0, 0, -L / 2], [0, 0, 1, z]], dtype=float))
           for sx in (-1, 1)]
    out.append(("outer", np.array([[0, 1, 0, -SKID_OUT_X - SKID_W / 2], [-1, 0, 0, L / 2], [0, 0, 1, z]], dtype=float)))
    out.append(("outer", np.array([[0, -1, 0, SKID_OUT_X + SKID_W / 2], [1, 0, 0, -L / 2], [0, 0, 1, z]], dtype=float)))
    return out


def placed_skids():
    """The four skids in garage coords: [(name, part)]."""
    made = {"inner": skid(), "outer": outer_skid()}
    names = ["inner skid, plain side", "inner skid, door side", "outer skid, plain side", "outer skid, door side"]
    return [(n, made[k].transform(m)) for n, (k, m) in zip(names, skids_to_shed())]


SKID_TO_PRINT = np.array([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0]], dtype=float)   # its length along y


def skids():
    """All four skids side by side for printing (the .stl), SKID_PITCH apart as on plate 4, so a
    5 mm brim added round each doesn't merge with the next."""
    parts = [skid(), skid(), outer_skid(), outer_skid()]
    return union([p.translate([0, i * SKID_PITCH, 0]) for i, p in enumerate(parts)])


# ---------------------------------------------------------------- fit test
FIT_LONG, FIT_END = "plain side", "roll-up end"   # the corner the fit test copies: the roll-up's
FIT_END_X = -23.0                                 # the bit of floor is cut here, 0.965 past the post notch at -35 in
FIT_WALL_X = -(35 * S - GROOVE_W / 2) - 0.1       # -24.544: the short roll-up end stops over that post (x -25.223
                                                  # ..-24.165), so its skirt ends on it (cut at FIT_END_X it would hang
                                                  # 1.17 mm past it with nothing under it), and inside the siding's -35 in
                                                  # groove, so its top layer ends at the groove, not in a strip of siding
                                                  # thinner than a line (review reconciliation, Nov 4 2026)
FIT_STUB = 20.0                                   # length of its stub of corner angle, from the foot
FIT_SKID = 23.0                                   # length of its stub of outer skid, with one peg
FIT_FRAME_X0 = -(59 * S + GROOVE_W / 2) + 0.03    # -41.848: the half doorway is the real roll-up end from inside the
                                                  # siding's -59 in groove, which keeps 0.74 of its end stud, to the
                                                  # doorway's middle (cut at the end stud's far side, -42.2, its top layer
                                                  # kept a 0.32 strip of siding past the groove)
FIT_XM = -RU_W / 4                                # -16.933: the half doorway's middle; the real -x jamb strip
                                                  # is mirrored about it to close the half doorway at x 0
FIT_STUB_END = -RU_CLR_X                          # -0.3: the half door's +x end, the real -x end mirrored


def corner_test(pieces, f):
    """The corner where the plain side meets the roll-up end, made short: the bottom 8 mm of each
    wall above the floor joined to its top 10 mm below the wall top, on that corner of the floor
    (the end wall's gable left off), the bottom FIT_STUB of that corner's angle and the end
    FIT_SKID of the outer skid under it. The roll-up end runs to x = FIT_WALL_X, over the post at -35 in
    and inside the siding groove there, and the bit of floor to FIT_END_X (the post notch at -35 in stays
    whole, with 0.965 of floor past it; cut there, the wall's skirt would hang 1.17 past the post), with its
    prong at -36.2 rooted in the bottom plate, the jamb studs, jamb stop, threshold lip, the post at -35 in,
    casing, coil box and head casing; its curtain rebate is filled solid here (the half doorway tests the
    rebate; here it would be a 9.9 mm overhang held on one edge). The plain side runs to 0.1 inside the siding
    groove over its stud at -112 in, so it ends on that stud's post with 0.68 of the stud kept and its top
    layer ends at the groove (cut on the groove's edge it could leave a sliver; at the stud's far side, a 0.28
    strip of siding past the groove), with its prong; the bit of floor ends at the stud's far side, in the
    notch round its post. Returns (long wall, end wall, floor, angle stub, skid stub) in garage coords."""
    z_lo, z_hi = ZF + 8, ZWT - 10
    y_cut = LONG_STUDS[1] + SW / 2
    y_wall = LONG_STUDS[1] + GROOVE_W / 2 - 0.1  # -78.872: the 16 in marks fall on the 8 in siding grooves

    def short(piece, xa, xb, ya, yb):
        keep = box(xa, xb, ya, yb, -5, ZWT)
        lo = piece ^ keep ^ box(-BIG, BIG, -BIG, BIG, -5, z_lo)
        hi = piece ^ keep ^ box(-BIG, BIG, -BIG, BIG, z_hi, ZWT)
        return lo + hi.translate([0, 0, z_lo - z_hi])
    stub = corner_angle(-1, -1) ^ box(-BIG, BIG, -BIG, BIG, -1, FIT_STUB)
    sk = dict(placed_skids())["outer skid, plain side"] ^ box(-BIG, BIG, -L / 2 - 1, -L / 2 + FIT_SKID, -BIG, BIG)
    fill = rbox(-RU_W / 2 - 0.01, FIT_END_X + 1, 0, REB_U + 0.01, MOUTH - 0.01, MOUTH + REB_H + 0.01)
    return (short(pieces[FIT_LONG], -W / 2 - 2, -(W / 2 - 10), -L / 2 - 2, y_wall),
            short(pieces[FIT_END] + fill, -W / 2 - 2, FIT_WALL_X, -L / 2 - 2, -(L / 2 - 10)),
            f ^ box(-W / 2, FIT_END_X, -L / 2, y_cut, -5, 400), stub, sk)


def curtain_frame(ru_piece):
    """The fit test's full-height half doorway, in garage coords: the real roll-up end from x
    FIT_FRAME_X0 to the doorway's middle and from the bottom of the skirt to the wall top (the -x jamb
    with its prong and stop, the lip and its wedge, the posts at -35 and -16 in and half the one at 0, the
    rebate with its rib at -14.5 and half the one at 0, the pad, the coil box, plates and the 0.833 strip,
    the casing), closed at x 0 by the real jamb strip (FIT_FRAME_X0 to the jamb face) mirrored about
    FIT_XM, with its stop. So its opening is 33.87 wide, half the real one, and its rebate ceiling has
    the real spans. It stands on its own skirt and posts: the curtain hangs on the wall, not the floor."""
    real = ru_piece ^ box(FIT_FRAME_X0, 0.0, -BIG, BIG, -1, ZWT)
    strip = ru_piece ^ box(FIT_FRAME_X0, -RU_W / 2 + 0.01, -BIG, BIG, -1, ZWT)
    return union([real, mirror_x(strip, FIT_XM), mirror_x(jamb_stops()[1], FIT_XM)])


def curtain_stub():
    """The fit test's full-height half door, seated in curtain_frame() as drawn, in garage coords:
    (white, black). It is the real curtain's -x half, x -33.567 to FIT_STUB_END, the full height, with
    its bottom zone, wedge edge and post notches, rail, slat grooves, bevel, and its tongue with one real
    finger and one real tab and the rib notches at -14.5 and 0, and a CUR_CHAMF back chamfer added at its
    +x end, up to CHAMF_TOP as at the real ends, for the mirrored stop. The full-size handle is centred on
    its rail at FIT_XM, its middle, so it lifts level. A little over half the real door's weight (STUB_WEIGHT_G:
    the handle is full size) on half its springs, so it holds and lifts about as the real door does."""
    w, b = curtain_parts(handle_x=FIT_XM)
    keep = box(-BIG, FIT_STUB_END, -BIG, BIG, -BIG, BIG)
    xe = FIT_STUB_END
    cham = plan_prism([(xe - CUR_CHAMF - 0.01, -0.01), (xe + 0.01, -0.01), (xe + 0.01, CUR_CHAMF + 0.01)], ZF, CHAMF_TOP)
    return (w ^ keep) - cham, b ^ keep


def corner_test_parts(pieces, f):
    """The short corner and its stubs from corner_test(), each lying the way it prints:
    [(name, part)]."""
    lw, ew, fl, stub, sk = corner_test(pieces, f)
    return [("short plain side", to_print(WALL_TO_PRINT[FIT_LONG], [lw])[0]),
            ("short roll-up end", to_print(WALL_TO_PRINT[FIT_END], [ew])[0]),
            ("bit of floor", to_print(FLOOR_TO_PRINT, [fl])[0]),
            ("corner angle stub", to_print(CORNER_TO_PRINT[-1], [stub])[0]),
            ("outer skid stub", on_bed(sk))]


def curtain_test_parts(pieces):
    """The half doorway and half door, each lying the way it prints (as the roll-up end and the curtain
    do), all one filament: [(name, part)]."""
    return [("half roll-up doorway", to_print(WALL_TO_PRINT[RUE], [curtain_frame(pieces[RUE])])[0]),
            ("half roll-up door", to_print(WALL_TO_PRINT[RUE], [union(list(curtain_stub()))])[0])]


FIT_OW, FIT_OH = 14.0, 24.0       # the fit test's doorway
FIT_ZF = 3.0                      # its sill block


def fit_doorway():
    """A short in-swing doorway in garage coords on the door side's plane (as the real one: u 0 to
    WT, the pin line DOOR_AXIS_U out from the inside face, the same holes, the inward trench and the
    real stop on the latch jamb), standing on its own sill block with NO floor: the real door is
    hung in the loose door side."""
    jamb = FIT_OW / 2
    ax_x, ax_y = W / 2 - WT + DOOR_AXIS_U, -jamb + DOOR_R + DOOR_GAP
    x0 = W / 2 - WT
    zf, oh = FIT_ZF, FIT_OH
    frame = [box(x0, W / 2, -jamb - 6, jamb + 6, 0, zf), box(x0, W / 2, -jamb - 6, -jamb, zf, zf + oh + 6),
             box(x0, W / 2, jamb, jamb + 6, zf, zf + oh + 6), box(x0, W / 2, -jamb - 6, jamb + 6, zf + oh, zf + oh + 6)]
    f = union(frame)
    poly = [(-0.05, STOP[0][1] - 0.05)] + STOP[1:3] + [(-0.05, WT)]
    f = f + prism([(x0 + u, jamb - d) for d, u in poly], 0, 1, 2, oh).translate([0, 0, zf])
    return f - union([cyl_z(ax_x, ax_y, zf - HOLE_BOTTOM_DEPTH, zf + 1, PIN_HOLE_D),
                      cyl_z(ax_x, ax_y, zf + oh - 1, zf + oh + HOLE_TOP_DEPTH, PIN_HOLE_D),
                      box(x0 - 0.01, ax_x, ax_y - PIN_HOLE_D / 2, ax_y + PIN_HOLE_D / 2, zf - TRENCH_DEPTH, zf + 1)])


def fit_door():
    """The short door for fit_doorway(), in print coords: the same slab, hinge edge and pins, one
    panel groove and the knob."""
    jamb = FIT_OW / 2
    ax_y = -jamb + DOOR_R + DOOR_GAP
    dw = (jamb - DOOR_GAP) - ax_y
    dh = FIT_OH - DOOR_BOTTOM_GAP - DOOR_TOP_GAP
    full = dw + DOOR_R                                                     # hinge edge to latch edge
    return door_slab(dw, dh, [(-DOOR_R + 0.2 * full, -DOOR_R + 0.75 * full, 0.15 * dh, 0.4 * dh)], 0.55 * dh)


def fit_door_to_shed(theta_deg=0.0):
    """Matrix from the short door's print coords to garage coords in fit_doorway(), swung in theta."""
    jamb = FIT_OW / 2
    ax_x, ax_y = W / 2 - WT + DOOR_AXIS_U, -jamb + DOOR_R + DOOR_GAP
    base = np.array([[0, 0, 1, ax_x - DOOR_R], [1, 0, 0, ax_y], [0, 1, 0, FIT_ZF + DOOR_BOTTOM_GAP]], dtype=float)
    th = math.radians(theta_deg)
    rot = np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]])
    pivot = np.array([ax_x, ax_y, 0])
    return np.column_stack([rot @ base[:, :3], rot @ (base[:, 3] - pivot) + pivot])


def peg_block():
    """A roof peg on a block lying like an end wall, so the peg lies on the bed as the end walls'
    pegs do, and a bit of roof sheet with the peg hole: (block, coupon), each on the bed."""
    blk = box(-6, 6, 0, 6, 0, WT) + cyl_y(0, 5, 6 + PEG_UP, PEG_D / 2, PEG_D)
    cpn = box(-6, 6, -6, 6, 0, ROOF_T) - cyl_z(0, 0, -1, PEG_HOLE_UP, PEG_HOLE_D)
    return on_bed(blk), on_bed(cpn)


def door_test_parts():
    """Fit test plate 2, each lying as it prints: [(name, part)]."""
    dwy = to_print(WALL_TO_PRINT["door side"], [fit_doorway()])[0]
    blk, cpn = peg_block()
    return [("short doorway", dwy), ("short door", on_bed(fit_door())), ("roof peg block", blk), ("roof coupon", cpn)]


def fit_test(pieces, whole_floor):
    """Both fit test plates in one, a row behind the other (for fit test.stl)."""
    rows = [door_test_parts(), corner_test_parts(pieces, whole_floor), curtain_test_parts(pieces)]
    out, y = [], 0.0
    for row in rows:
        x, depth = 0.0, 0.0
        for _, part in row:
            out.append(part.translate([x, y, 0]))
            x += size(part)[0] + 6
            depth = max(depth, size(part)[1])
        y += depth + 6
    return union(out)


# ---------------------------------------------------------------- files
def write_stl(man, name, folder=HERE):
    """A binary STL. An STL holds its corners as 32-bit floats, which rounds together corners that the
    booleans left a few millionths of a mm apart, and the triangles between them collapse. So the part's
    corners are rounded to 32 bits and merged, and any triangle left with two corners the same is dropped:
    the file is a closed surface with no collapsed triangles. The part is NOT simplified first: on the long
    walls simplify() collapsed edges across the studs' faces and cut wedges out of 12 studs and the steel
    door's head casing (293 mm3 gone from the door side, 26 from the plain side; final audit, Nov 4 2026), at
    any tolerance. The triangles written are summed back to a volume, and if that isn't the part's, nothing is
    written; check_barn_garage.py also reads each file back layer by layer against its part."""
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
    path = os.path.join(folder, name)
    with open(path, "wb") as f:
        f.write(NAME.encode().ljust(80, b" "))
        f.write(struct.pack("<I", len(t)))
        rec = np.zeros(len(t), dtype=[("n", "<f4", 3), ("a", "<f4", 3), ("b", "<f4", 3), ("c", "<f4", 3), ("x", "<u2")])
        rec["n"], rec["a"], rec["b"], rec["c"] = n, a, b, c
        f.write(rec.tobytes())
    return path


def write_3mf(name, plates, folder=HERE):
    """A plain 3MF project for Orca. plates: [(plate name, items), ...], each a plate in Orca in
    that order. items: (object name, [(part name, manifold, filament), ...], (x, y)) placed with
    its lower-left corner at x, y on its plate, and optionally a dict of that object's own
    settings after (x, y) (copied from the Side Utility's make_shed.py). An object with two parts
    opens in Orca as one object, each part already set to its filament (1 siding, 2 trim, roof and
    angles, 3 floor, skids and lofts). A "modifier" in the settings, [(name, manifold, settings), ...] in
    the parts' coords, is written as modifier parts with those settings and no filament of their own;
    where the object lies on the plate comes from its parts alone."""
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
    with zipfile.ZipFile(os.path.join(folder, name), "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", types)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)
        z.write(os.path.join(HERE, "flash studio settings.json"), "Metadata/project_settings.config")
        z.writestr("Metadata/model_settings.config",
                   '<?xml version="1.0" encoding="UTF-8"?>\n<config>' + "".join(cfg + plate_cfg) + '</config>')


def on_bed(man):
    bb = man.bounding_box()
    return man.translate([-bb[0], -bb[1], -bb[2]])


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
# bridges every seam. Left to itself, Flash Studio laid those bridges along the two long seams, in every slice: one
# strand 193 mm long over each 0.4 mm slot, which sags into it (bridge review, Nov 4 2026). Laid along the short
# seams instead, they would be 22 to 34 mm. So that one layer carries modifiers: FLOOR_STRIP either side of each long
# seam sets ACROSS_LONG_SEAMS, 180, along the bed's X, and the rest of the floor ACROSS_SHORT_SEAMS, 90, along its Y.
# Every line then crosses its seam: 0.4 mm, or 1.2 mm where a short seam runs into a long one. There the slicer fills
# the strip and the box beside it apart, and their lines stop a hair short of each other over the short seam: a spot
# of its bottom up to about 0.4 by 0.4 mm is left to the layer over it, a dip 0.2 mm deeper (15 of them, 1.4 mm2 in
# all, 0.3 of it at the short seams' ends by the notches, as before), too small to see (floor review). Nothing else on
# the floor hangs over anything, so no other bridge is set. The face under it prints as before. In the end bands,
# where the skid pegs' holes end, the slicer moves a few lines of solid infill on the 3.05 to 3.45 layers: less of the
# 3.25 layer is an internal bridge and some of the 3.45 layer is one now, and more solid lines on the 3.25 to 3.65
# layers cross gaps in the sparse infill (71 mm of such runs on these layers against 56 before, the longest 4.3 mm
# against 5.1). On the 0.85, 1.05, 3.65 and 4.05 layers it lays the same lines in another order (floor review).
# ASSUMED (as sliced)
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
    parts["door"] = door_parts()
    parts["curtain white"], parts["curtain black"] = curtain_parts()
    parts["curtain"] = union([parts["curtain white"], parts["curtain black"]])
    parts["skids"] = skids()
    parts["fit"] = fit_test(pieces, f)
    return parts


def curtain_print(p):
    """(white, black) of the roll-up curtain, lying on its back (its inside face) on the bed, slats and
    handle up, as the roll-up end prints: u is its print height."""
    return tuple(to_print(WALL_TO_PRINT[RUE], [p["curtain white"], p["curtain black"]]))


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


TURN = np.array([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0]], dtype=float)   # a quarter turn on the bed
SKID_GAP = 6.2         # from a skid to any other part: its 5.1 mm brim (5 + the 0.1 brim gap) and a mm
SKID_PITCH = 13.5      # skid to skid: 11.0 between them, so their brims (5.1 each) don't merge


def plates(p):
    """The plates of each Orca project, from build()'s parts, as write_3mf() takes them:
    {file name: [(plate name, items)]}.

    2 all plates.3mf has a plate for each print: both long walls and the door (all white but the
    door side's casings), the roof and the corner angles (black), both end walls, then the floor,
    skids and lofts (brown). The prime tower goes at x 165, y 195 on the two-colour plates, so
    they keep that corner clear; the skids get a 5 mm brim, the angles and roof sheets none."""
    zone = trim_zone()
    walls_p = {name: wall_parts(p, name, zone) for name in WALL_CUTS}
    fl = to_print(FLOOR_TO_PRINT, [p["floor"]])[0]
    fl_seams = across_seams(fl, [x - p["floor"].bounding_box()[0] for x in LONG_SEAMS])   # FLOOR_TO_PRINT keeps x
    lf = to_print(LOFT_TO_PRINT, [p["loft"]])[0]
    up = panel_to_print(p["upper"], UPPER_A, UPPER_B)
    lo = panel_to_print(p["lower"], LOWER_A, LOWER_B)
    sk_in = on_bed(skid().transform(SKID_TO_PRINT))
    sk_out = on_bed(outer_skid().transform(SKID_TO_PRINT))
    loft_p = on_bed(lf.transform(TURN))
    door = on_bed(p["door"])

    def wall_item(name, x, y, split=None):
        """A wall lying flat at x, y, its siding bridged across the studs (across_studs, split as there)."""
        siding, trim = walls_p[name]                 # the plain side has no trim
        return (name, [("siding", siding, 1)] + ([] if trim.is_empty() else [("trim", trim, 2)]), (x, y),
                across_studs(union(walls_p[name]), split))

    def collar_y(name):
        """Where GABLE_SPLIT_Z is on an end wall lying flat (its height runs along y, from its lowest point)."""
        return GABLE_SPLIT_Z - p[name].bounding_box()[2]

    def row(parts, filament, own=None, gap=6.0):
        """[(name, part)] side by side along x, gap apart, the row centred on the bed."""
        x = (220 - sum(size(m)[0] for _, m in parts) - gap * (len(parts) - 1)) / 2
        out = []
        for name, m in parts:
            item = (name, [(name, m, filament)], (x, (220 - size(m)[1]) / 2))
            out.append(item + ((own[name],) if own and name in own else ()))
            x += size(m)[0] + gap
        return out

    # plate 1: the long walls one behind the other, the door behind them at the left
    lw, lh = size(union(walls_p["door side"]))
    dw, dh = size(door)
    x1 = (220 - lw) / 2
    plate1 = [wall_item("door side", x1, 3.0), wall_item("plain side", x1, 3.0 + lh + 3),
              ("door", [("door", door, 1)], (x1, 3.0 + 2 * lh + 9))]
    # plate 2: the four corner angles turned to run along y, in two columns of two at the left, then
    # the upper and lower sheets
    angles = [("corner angle, " + n, on_bed(m.transform(TURN))) for n, m in corner_prints()]
    aw, ah = size(angles[0][1])
    uw, uh = size(up)
    lw2, lh2 = size(lo)
    total = 2 * aw + 6 + 6 + 2 * uw + 2 * lw2 + 3 * 4
    x0 = (220 - total) / 2
    ay = (220 - 2 * ah - 6) / 2
    plate2 = [(n, [("corner angle", m, 2)], (x0 + (i // 2) * (aw + 6), ay + (i % 2) * (ah + 6)), NO_BRIM)
              for i, (n, m) in enumerate(angles)]
    xs = x0 + 2 * aw + 12
    plate2 += [("upper roof 1", [("upper roof", up, 2)], (xs, (220 - uh) / 2), NO_BRIM),
               ("upper roof 2", [("upper roof", up, 2)], (xs + uw + 4, (220 - uh) / 2), NO_BRIM),
               ("lower roof 1", [("lower roof", lo, 2)], (xs + 2 * uw + 8, (220 - lh2) / 2), NO_BRIM),
               ("lower roof 2", [("lower roof", lo, 2)], (xs + 2 * uw + lw2 + 12, (220 - lh2) / 2), NO_BRIM)]
    # plate 3: both end walls side by side, the roll-up curtain on its back 4 mm behind the roll-up end,
    # white with its black latch plate and handle (the black starts on the 5.05 layer: one colour change)
    ew, eh = size(union(walls_p["roll-up end"]))
    cur_w, cur_b = curtain_print(p)
    x3 = (220 - 2 * ew - 6) / 2
    plate3 = [wall_item("roll-up end", x3, 4, collar_y("roll-up end")),
              wall_item("back end", (220 + 6) / 2, 4, collar_y("back end")),
              ("roll-up curtain", [("curtain", cur_w, 1), ("latch plate and handle", cur_b, 2)], (x3, 4 + eh + 4))]
    # plate 4: the floor, the four skids on edge with room for their brims, the two lofts turned
    fw, fh = size(fl)
    sw_, sh_ = size(sk_in)
    lfw, lfh = size(loft_p)
    total = fw + SKID_GAP + 3 * SKID_PITCH + sw_ + SKID_GAP + lfw
    fx = (220 - total) / 2
    sx0 = fx + fw + SKID_GAP
    plate4 = [("floor", [("floor", fl, 3)], (fx, (220 - fh) / 2), fl_seams)]
    for i, (n, m) in enumerate((("inner skid 1", sk_in), ("inner skid 2", sk_in), ("outer skid 1", sk_out),
                                ("outer skid 2", sk_out))):
        plate4.append((n, [("skid", m, 3)], (sx0 + i * SKID_PITCH, (220 - size(m)[1]) / 2), SKID_BRIM))
    lx = sx0 + 3 * SKID_PITCH + sw_ + SKID_GAP
    plate4 += [("loft 1", [("loft", loft_p, 3)], (lx, (220 - 2 * lfh - 6) / 2)),
               ("loft 2", [("loft", loft_p, 3)], (lx, (220 + 6) / 2))]
    all_plates = [("long walls and door", plate1), ("roof and corner angles", plate2),
                  ("end walls and roll-up curtain", plate3), ("floor, skids and lofts", plate4)]

    # the fit test, one filament: plate 1 is the half doorway and half door alone, so, as on plate 3, nothing but
    # the door's handle prints above the walls' 5.65 layer (the bit of floor is 6.8 tall and the skid stub 5.8);
    # plate 2 the roll-up corner in front, the door and roof peg behind it
    ct = corner_test_parts({n: p[n] for n in WALL_CUTS}, p["floor"])
    cu = curtain_test_parts({n: p[n] for n in WALL_CUTS})
    dt = door_test_parts()
    own = {"outer skid stub": SKID_BRIM, "corner angle stub": NO_BRIM,
           **{n: across_studs(m) for n, m in ct if n in ("short plain side", "short roll-up end")}}
    fit1 = row(cu, 1, own={"half roll-up doorway": across_studs(dict(cu)["half roll-up doorway"])}, gap=8.0)
    da, db = max(size(m)[1] for _, m in ct), max(size(m)[1] for _, m in dt)
    y0 = (220 - da - 8 - db) / 2
    fit2 = [(n, ps, (x, y0 + (da - size(ps[0][1])[1]) / 2), *o) for n, ps, (x, _), *o in row(ct, 1, own, gap=SKID_GAP + 1)]
    fit2 += [(n, ps, (x, y0 + da + 8 + (db - size(ps[0][1])[1]) / 2), *o) for n, ps, (x, _), *o in row(dt, 1)]
    return {"1 fit test.3mf": [("roll-up door", fit1), ("roll-up corner, door and roof peg", fit2)],
            "2 all plates.3mf": all_plates}


def stl_parts(p):
    """{.stl file name: the part it is written from, lying as it prints}, from build()'s parts. Each wall is the
    whole wall, not its siding and trim joined again (the same place on the bed, and fewer edges where two bodies
    touch: 0 against 6 on the door side; the 12x24 Garage's way, final audit, Nov 4 2026)."""
    out = {"floor.stl": to_print(FLOOR_TO_PRINT, [p["floor"]])[0]}
    out.update({name + ".stl": to_print(WALL_TO_PRINT[name], [p[name]])[0] for name in WALL_CUTS})
    out.update({"upper roof.stl": panel_to_print(p["upper"], UPPER_A, UPPER_B),
                "lower roof.stl": panel_to_print(p["lower"], LOWER_A, LOWER_B),
                "loft.stl": to_print(LOFT_TO_PRINT, [p["loft"]])[0], "door.stl": on_bed(p["door"]),
                "skids.stl": p["skids"], "fit test.stl": on_bed(p["fit"]),
                "corner angle.stl": stacked(corner_prints()), "roll-up curtain.stl": union(list(curtain_print(p)))})
    return out


def main():
    p = build()
    zone = trim_zone()
    walls_p = {name: wall_parts(p, name, zone) for name in WALL_CUTS}
    fl = to_print(FLOOR_TO_PRINT, [p["floor"]])[0]
    lf = to_print(LOFT_TO_PRINT, [p["loft"]])[0]
    up = panel_to_print(p["upper"], UPPER_A, UPPER_B)
    lo = panel_to_print(p["lower"], LOWER_A, LOWER_B)
    for name, part in stl_parts(p).items():
        write_stl(part, name)
    for name, pl in plates(p).items():
        write_3mf(name, pl)
    for name, (siding, trim) in walls_p.items():
        bb = union([siding, trim]).bounding_box()
        print(f"{name:12s} flat {bb[3]-bb[0]:7.1f} x {bb[4]-bb[1]:7.1f} x {bb[5]-bb[2]:6.1f} mm  " +
              ("no trim" if trim.is_empty() else
               f"trim {trim.volume()/1000:5.2f} cm3, from {trim.bounding_box()[2]:.2f} mm up"))
    for k, v in list(p.items()) + [("upper flat", up), ("lower flat", lo), ("loft flat", lf),
                                   ("angle flat", corner_prints()[0][1])]:
        bb = v.bounding_box()
        print(f"{k:12s} {bb[3]-bb[0]:7.1f} x {bb[4]-bb[1]:7.1f} x {bb[5]-bb[2]:6.1f} mm  "
              f"{v.volume()/1000:6.1f} cm3  {v.num_tri()} triangles")
    print("dropped layout marks:", DROPPED_MARKS)


if __name__ == "__main__":
    main()
