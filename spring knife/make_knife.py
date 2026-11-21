"""Double-action spring knife toy for the Flashforge AD5X, designed from scratch (v3).

Run:  python3 make_knife.py      (needs: pip install manifold3d numpy)

A blunt plastic fidget toy. Push the knob on the side 28 mm forward: the blade snaps out
86 mm and locks. Pull it back: the blade snaps in and locks. Every part is printed, the
screws and nuts too.

How it works
  * One TPU band runs between two sleds that ride over the blade: sled F behind the blade's
    lug, sled B in front of it. The band goes straight through a slot in the lug.
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
    out by a springy arm, thin at its nose and thicker toward its root so it bends evenly and
    lasts. Its load goes into the carrier, never the arm. It catches on a short
    catch at each end of a PLA rail in the base plate, and floats out against the knob bar in
    between. The rail sits between two TPU cushions, which take the knock when the blade
    bounces back off its pad.
  * Each riser wears a TPU cap where the sled lands on it, and the knob lands on a TPU stop of its
    own at each end of its travel, just before its sled meets its pad: a block outside the handle
    in front of a guard on the handle's side, which meets the knob's end face square on at about
    the height the thumb pushes. So the thumb's push and its weight stop at the knob instead of
    running down the knob's thin bar. Every landing on a riser, pad, knob stop or cushion is on
    TPU. The lug picking up the parked sled and the latch block meeting the rail's end are PLA on
    PLA, but the light sled and rail keep them under 10 MPa.
  * The knob is a long block (38 mm) on a carriage that rides a rib left standing in the knob's slot, with a
    sliding fit on both sides. The thumb, resting in a saddle at the knob's middle, pushes the knob 7 mm out to the
    side of its bar, so every push and every landing tries to turn the knob flat in the handle; the carriage takes that
    turn on its rib, over its whole length, and the plain bar each side of it is free in the slot to follow the little
    it still turns.
  * The band is fitted 12.5 mm over its printed length, and is thinner to match: the same energy for the throw with
    a flatter pull, so the thumb pushes less at the end of the push.
  * The screws thread into posts printed on the top plate, so they clamp all three plates.

Parts (print files in this folder)
  handle 1 base.stl, handle 2 middle.stl, handle 3 top.stl   three plates, four screws; each plate
                     carries its part of the two guards on the knob's side
  blade.stl          blade and carrier with the lug and the latch arm
  latch block.stl    rail.stl    sled F.stl    sled B.stl
  knob slider.stl    the bar with its two cams, two risers, and the knob on its carriage
  screw.stl (4), nut.stl (a thread gauge), handle 3 top loose.stl (if the fit test says so)
  band.stl (and two spares), pad.stl (2), rail cushion.stl (2), riser cap.stl (2), knob stop rear.stl and
                     knob stop front.stl (mirror images: their faces are cut back on the inner half)   TPU;
                     band strong.stl for a soft TPU, band soft.stl for a stiff one: a hang test picks the band
                     (hang a normal band from a full half-litre bottle: HANG_STRONG and HANG_SOFT below)
  1 fit test.3mf        the four screws and three gauge nuts (1, 2 and 3 corners cut off), a piece of the knob's
                        rib, and in white a latch test piece with the lug and a piece of the knob's carriage: find
                        the thread fit and try the latch and the knob first
  2 knife plates.3mf    Flash Studio project: handle and small parts (black), blade and latch block
                        (white), and the knob slider (white) on a plate of its own
  3 TPU parts.3mf       the band and two spares, pads, cushions, riser caps and knob stops, set up for TPU and
                        printed solid; three strong bands and three soft bands each on a plate of their own

Axes for the assembled knife: x along it (the blade comes out at +x), y across it (the knob is
on +y), z through it (z = 0 is the outside of the base plate). The blade's travel is c (0 closed,
86 open) and the knob's is s (0 back, 28 forward).
"""

import json
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
CHAMFER = layer(3)                  # 0.65 round the two outside faces: keeps a full ring round each screw head
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
CAR_CUT_Y = 10.6                    # the carrier's knob side is cut back to here above ...
CAR_CUT_Z = CAR_Z0 + layer(9)       # ... 4.375, so the cams pass it with room to spare
CAR_CUT_X2, CAR_CUT_Y2 = 26.35, 10.3  # and further, to 10.3, from the block slot's front wall (carrier
#                                     x 26.35) to the carrier's front end: with the thumb held on the knob at an end of its
#                                     travel, or the knob landing on its rear stop, the knob's push turns the slider, and its far
#                                     cam swings in 0.5-0.75 over the arriving carrier. Behind the block's slot it stays at 10.6
GAP = 0.3                           # sliding gap at the sides
CHAN_Y = CAR_W / 2 + GAP            # 11.3
SLOT_Y = BLADE_W / 2 + GAP          # 9.3
C0 = 22.0                           # carrier's back end, closed
TRAVEL = 86.0                       # blade travel: 79 mm comes out
OVERRUN = 5.0                       # room for the blade past each end (pads squash)
REAR_IN = C0 - OVERRUN              # 17 channel's back end
FRONT_IN = C0 + CAR_L + TRAVEL + OVERRUN - 0.5    # 167.5 channel's front end
GROOVE_X0, GROOVE_X1 = 100.0, 138.0  # the blade's fuller (carrier x): starts 30 mm outside the mouth when open
GROOVE_D = 0.4

# the lug: stands up from the carrier into the band level; the band runs through its slot
LUG_X0, LUG_L = 12.0, 8.0           # on the carrier
LUG_HW = 5.2                        # half width
LUG_TOP = CAR_Z0 + layer(36)        # 9.775
BAND_SLOT = 1.05                    # half width of the slot the band runs in
BAND_SLOT_Z = CAR_Z0 + layer(27)    # 7.975 floor of that slot
X_L0 = C0 + LUG_X0                  # 34: lug's back face, closed

# latch: a separate block in a slot through the carrier's +y side, pushed out by an arm
BLK_X0, BLK_L, BLK_D = 22.5, 3.6, layer(32)   # 3.6 long, so it can't go in on its side; 6.45 deep, so it sits
                                        # 3.7 into its slot when out, 3.45 with the bar out at the end of its play,
                                        # and can't lean past its chamfers (5.65 deep leaned 0.73 with the bar out).
                                        # It prints lying on its inner face, so its first layer is there.
BLK_Z0, BLK_Z1 = CAR_Z0 - 0.075, CAR_Z1 + 0.075   # 4.40 tall: 0.2 off the channel floor and the middle plate
BLK_CHAMFER = 0.6                   # on all four upright edges: either way round, the trailing corner can't catch
BLK_SLOT = 0.25                     # play each side of the block in its slot
FOOT = 0.15                         # first layers set back this far where a part slides on a first layer
X_BLK = C0 + BLK_X0                 # 44.5: block's back face, closed
ARM_ROOT = 54.0                     # the arm's root on the carrier (x), as far forward as the carrier's 22 mm goes
ARM_Y0, ARM_T = 4.8, 0.85           # the arm, as printed (free): its inner face, and 0.85 thick at its nose (over two
#                                     lines). It bends twice every stroke, so it is shaped to bend evenly (arm_t): a
#                                     plain 0.95 arm bent 0.99 % at its root, and PLA bent that often lasts a few
#                                     thousand out-and-in strokes at most (check_knife: 0.65 % for 10,000)
ARM_T_ROOT = 1.025                  # it thickens toward the root as a beam of even strength, to 1.025 ...
ARM_FLARE, ARM_FLARE_L = 0.3, 3.0   # ... and flares 0.3 more over the last 3 mm, so the root's round ends, where
#                                     the stress is raised, see less than the arm itself: stiff enough (0.145 N/mm) to
#                                     throw the block out against the friction while the pad stops the blade
ARM_GAP = 0.5                       # the gaps round the arm: inside one print, so wider than a sliding fit
ARM_RELIEF = 1.0                    # radius of the round ends of those gaps at the arm's root (they end at the
#                                     carrier's front end, 55)
NOSE_C, NOSE_HW = BLK_X0 + BLK_L / 2, 0.8     # the arm's nose: 1.6 wide, under the middle of the block
PRELOAD = 0.3                       # the arm still pushes 0.3 when the block is out (0.05 with the bar out): little,
#                                     so the block barely presses the bar between the catches, with a stiffer arm
#                                     doing the throwing out
# block's outer face (y): out in a window it rests on the knob bar; on the rail; pushed by a cam.
# Out 2.45 past the rail's face, so it pops out far enough to bite the catch before the blade
# bounces back (check_knife's pop-out model)
Y_OUT, Y_RAIL, Y_CAM = 13.75, CHAN_Y, 11.05
BAR_OUT = 0.25                      # the knob bar can sit this far out in its lane (its sliding fit), and the
                                    # arm pushes the block out after it, to Y_OUT + BAR_OUT
NOSE_TOP = Y_OUT - BLK_D + PRELOAD  # 7.6: the arm's nose reaches here when free

# rail: two short catches, one at each end of the blade's travel, joined by a spine that runs
# beside the block's path; it floats between two TPU cushions. The block rides a catch only
# near each end; in between it is out against the knob bar and barely rubs.
RAIL_Y0 = CHAN_Y                               # 11.3 the catches' inner face, in line with the channel's side
RAIL_Z0 = layer(5)                             # 1.05 the groove's floor
RAIL_TOP = RAIL_Z0 + layer(15)                 # 4.10 (printed standing on its bottom face)
LANE_Z0 = layer(21)                            # 4.25 floor of the knob bar's lane
RAIL_CHAMFER = 0.15                 # on the inner corner of each catching end
E_CATCH = 0.3                       # the block sits this far from the rail end at rest
RAIL_X0 = X_BLK + BLK_L + E_CATCH   # 48.4: closed catch (the block's front face bears here)
RAIL_X1 = X_BLK + TRAVEL - E_CATCH  # 130.2: open catch (the block's back face bears here)
SEG_FLAT = 4.0                      # each catch: a flat the block rides in on ...
SEG_RAMP = 22.0                     # ... then a 22 degree ramp, out past anywhere the block can be ...
SEG_RAMP_Y = 14.2                   # (0.2 past the block with the bar out, Y_OUT + BAR_OUT)
RAMP_L = (SEG_RAMP_Y - RAIL_Y0) / math.tan(math.radians(SEG_RAMP))   # 7.18
TAPER_L = 8.0                       # ... then a long taper into the spine, so the catch has no square step
SEG_L = SEG_FLAT + RAMP_L + TAPER_L
WIN_Y1 = Y_OUT + BAR_OUT + 0.05     # 14.05: the block's path (windows and between the catches) is cut out to
                                    # here, 0.05 past the block with the bar at the outer end of its play
SPINE_Y0 = WIN_Y1 + 1.05            # 15.10: 0.8 of base plate between its groove and the path
SPINE_Y1 = SPINE_Y0 + 1.6           # 16.70
GROOVE_Y0, GROOVE_Y1 = SPINE_Y0 - 0.25, SPINE_Y1 + 0.25   # an easy sliding fit
SPINE_WIDEN = 0.4                   # the spine is 2.0 wide between the catches, 1.6 at its ends; its groove's
                                    # wide part (17.35) is flush with the lane's outside wall
SPINE_X0, SPINE_X1 = RAIL_X0 - 3.0, RAIL_X1 + 3.0  # the spine runs 3 mm past each catch ...
CUSH_L, CUSH_HELD = 12.0, 4.0       # ... to a TPU cushion at each end, its outer 4 mm pressed into a narrow end
CUSH_TOP = RAIL_Z0 + layer(14)      # 3.90
CUSH_GRIP = 0.05                    # how much narrower the groove's ends are than a cushion, each side
W_FAR = 5.0                         # far end of each window: past the block's overrun
RAIL_MOVE = 4.0                     # the rail can move this far each way in its groove

# knob bar: in a lane beside the channel, above the rail
BAR_Y0, BAR_Y1 = Y_OUT, 17.1
LANE_Y1 = BAR_Y1 + BAR_OUT          # 17.35: 1.65 of side wall outside it
LANE_IN = 0.25                      # the lane runs this far inside the cams' faces (where the channel doesn't take its wall)
BAR_Z0 = LANE_Z0 + 0.2              # 4.45 (bar prints on this face)
BAR_Z1 = BAR_Z0 + layer(11)         # 6.70
RISER_Y1 = 16.1                     # the risers are narrower than the bar: the middle plate's floor
BAR_IN = 0.3                        # the thumb pressing the knob inward pushes the bar this far in, until its risers
#                                     meet their slots' walls, and the block in after it
RISER_SLOT_Y0, RISER_SLOT_Y1 = BAR_Y0 - BAR_IN, RISER_Y1 + 0.3   # keeps a ledge over the bar's outer 0.7
RISER_F_Y1 = RISER_Y1               # riser F's outer face
RISER_F_SLOT_Y1 = RISER_F_Y1 + 0.3  # riser F's slot's outer side, before the room below
RISER_B_ROOM = 0.1                  # riser B's slot, and the band level beside it, are 0.1 wider outward too (a ledge of 0.6
#                                     left): a knob landing on its rear stop turns the carriage's front end out, and riser B,
#                                     at the carriage's front, met its slot's outer wall
RISER_F_ROOM = 0.1                  # riser F's slot, and the band level beside it, are this much wider outward over riser
#                                     F's sweep: when the knob's carriage turns, the bar behind it swings out, and riser F,
#                                     only 10 mm behind the carriage, would hold it in and bend it. The sideways check finds
#                                     riser F swings out at most 0.32, so 0.4 of room in all is enough, and the middle plate's
#                                     floor still covers the bar's outer 0.6 beside it (0.2 with the middle plate as far off as
#                                     its pegs let it; it was 0.5 more room and a 0.2 ledge). The slot's inner side, which
#                                     stops the thumb pushing the bar in (BAR_IN), stays
THROW = 28.0                        # knob travel
SOFT = 0.3                          # the knob can go this far past each end before a sled meets its pad ...
KNOB_SOFT = 0.2                     # ... but meets its own TPU stop (below) here, 0.1 before; not nearer the end of its
#                                     travel than 0.2, so the latest let-go (s 26.62) stays 1.5 before the knob's stop
SLED_ROOM = 5.0                     # a sled can run on this far past its pad's face (it squashes a pad 3.5 at most)
G_P = 0.3                           # a parked sled sits this far from the lug
RISER_L = 12.7                      # each riser, from its face (the TPU cap's face) to its far end
RISER_TOP = BAR_Z0 + layer(26)      # 9.70
CAP_T, TONGUE_L, TONGUE_W = layer(12), 2.4, 0.8   # TPU cap: 2.45 in front of a 0.8 wide PLA tongue it is pressed
#                                     onto; the tongue stands on a full-width foot up to the sleds' floor
SOLE_TOP = BAR_Z0 + layer(14)       # 7.30: and the riser runs on, as a full-width sole 0.6 tall, right out to the cap's
#                                     face under the cap's front block, which stands on it. A knock on the cap then bends
#                                     the bar at the riser's face, not 2.5 in under the cap: in the let-go landing the
#                                     bar takes 25.0 MPa, 29.1 with the cap's front block on the bar (limit 30). The
#                                     stiffer front puts a little more on the tongue's root layer, 11.2 MPa against 9.7
#                                     (limit 12); with the foot's full height run on instead it was 13.1, and a 45 degree
#                                     ramp up to the tongue 12.8
CAP_TOP = BAR_Z1 + layer(15)       # 9.75, 0.35 under the top plate
CAP_L = CAP_T + TONGUE_L            # 4.85 = layer(24): the cap prints on its front face
CAP_GRIP = 0.09                     # the cap's slot is this much narrower than the tongue each side: about 0.05 N of grip
CAM_ANGLE = 20.0
RAMP = (Y_OUT - Y_CAM) / math.tan(math.radians(CAM_ANGLE))   # 7.42: 20 degree cam ramps
CAM_FLAT = 2.0
CAM_LEAD = 2.0                      # each cam's top reaches the block's corner this far from the end of the
                                    # push, so the real block, chamfered and leaning, is let go at least 1.5
                                    # before the knob meets its stop
C_TRIP = E_CATCH + 0.6              # the blade creeps this far while cocked: to the rail, then into its cushions
C_COCK = C_TRIP + 0.9               # and never more than this
STEM_X0, STEM_X1 = 60.0, 98.0       # the knob and its carriage: 38 long (the knob was 14). The thumb pushes the knob 7.3 mm
#                                     out to the side of the bar's line, and its stops push back 6.5 out, so every push and
#                                     every landing turns the knob flat in the handle. The carriage takes that turn itself: it
#                                     rides a rib with a sliding fit on both sides over its whole length, so it can only turn
#                                     0.5 / 38 of a radian, and the plain bar each side of it, free in the knob's slot, follows
#                                     that easily (check_knife: the knob bar sideways). Its front stays at 98: the slot it
#                                     sweeps ends KNOB_ROOM past 98 + 28, before cam B pushes the block (x 129.6 on), which
#                                     needs the lane's wall behind the bar. Its back at 60 (it was 56 on a 42 mm carriage)
#                                     leaves 13.6 of plain bar to riser F: pulled back, a knob landing on its rear stop turns
#                                     the carriage until riser F meets its slot's inner wall, and over 9.6 the bar between them
#                                     bent 20.8 MPa sideways and up and down together, 17.3 over 13.6
STEM_TOP = BAR_Z1                   # 6.70: the carriage's roof, over the rib, comes up to the bar's top
GUIDE = 0.25                        # the carriage's sliding fit: 0.5 of play across its rib in all, 0.25 a side if it sat in
#                                     the middle ...
GUIDE_LEG, GUIDE_FOOT = 0.15, 0.35  # ... but it is drawn off the middle: its inner leg 0.15 from the rib's inner face, the
#                                     knob's foot 0.35 from its outer face. A push turns the carriage in its play, and whichever
#                                     end swings out is stopped by the leg on the rib, 0.1 before the bar reaches its lane's
#                                     wall at the cam beyond (BAR_OUT 0.25), so the bar between them bends far less (the
#                                     hardest push 17.3 MPa sideways and up and down together with 0.25 a side, 14.8 now; the
#                                     return push 20.0, 17.8). The foot's side goes in further, but a cam's lane wall and riser
#                                     B's slot (BAR_IN) stop the slider going in before the foot
GUIDE_LEAD, GUIDE_CROWN = 3.5, 0.065   # each of the carriage's two guide faces is crowned in plan over its last 3.5 mm,
GUIDE_R = GUIDE_LEAD ** 2 / (2 * GUIDE_CROWN)   # 0.065 back at its end (a 94 mm radius; it was 0.1 over 2, 20 mm): the
#                                     carriage turns a little in its play, and a square end would dig its corner into the rib;
#                                     a crowned end bears on it like a rounded edge, where the crown's slope matches the turn
#                                     (R x the turn in from where the crown starts, under half its lead), and leads in. The
#                                     flatter crown bears more gently on the rib's short height (Hertz's line contact)
RIB_Y0 = 17.6                       # the rib: the bottom of the handle's side wall, left standing in the knob's slot, 1.4
RIB_TOP = layer(26)                 # wide (y 17.6 to the handle's side, 19.0) and 1.0 tall (to 5.25). The plain bar has 0.5
#                                     to it, room to follow the carriage's turn
LEG_Y1 = RIB_Y0 - GUIDE_LEG         # 17.45: over the carriage the bar is 0.35 wider (its inner leg, beside the rib) ...
ROOF_Z0 = BAR_Z0 + layer(5)         # ... and its roof, from 5.50 up to the bar's top, crosses over the rib to the knob: 1.2
#                                     thick and 38 long (the stem was 2.25 thick and 14 long). Not thinner: the rib would bear
#                                     more, but a let-go knob's twist would pass 12 MPa across the roof's layers
KNOB_Y0 = HW / 2 + 0.7              # 0.7 clear of the handle's side above the base plate, so a middle or top plate set a
#                                     little off can't pinch it ...
KNOB_FOOT_Y0 = HW / 2 + GUIDE_FOOT  # ... and its foot, up to the roof's top, rides the rib's outer face (19.35)
END_CUT_Y0 = KNOB_FOOT_Y0 - 1       # the knob's end cuts (END_CUT, END_Y) start this far in
LANE_RELIEF_X0 = 52.5               # behind the knob's slot the lane's outer wall is cut back to the rib's line from here: the
#                                     plain bar behind the carriage, at the rear end of the knob's travel, then has the same
#                                     0.5 of room it has beside the rib, not 0.25 against the lane's wall 2 mm behind the
#                                     carriage (a knob landing on its rear stop turns the carriage, and that wall held the
#                                     bar right behind it). Not further back: the latch block rests on the bar up to x 49.9,
#                                     and cam A pushes it in against the wall up to x 52.3
FRONT_TAPER_TOP = LANE_Y1 - 0.05    # in front the widening stops here: past the knob's slot the lane's wall is at LANE_Y1
GUIDE_LEAD_FRONT = 4.7              # at the front end the roof's cut-back starts from the bar's own face and trims the inner leg's
#                                     last ~1.2 (front_crown_trim), so the leg's crown there is longer, on the same radius
ROOF_CUTS = (2.4, 2.4, 2.4, 2.4, 2.4, 2.4)   # the roof's ends over the rib's channel are cut back (end_cutbacks) with a
#                                     quarter-ellipse from the inner leg's face at the end face (the bar's face at the front end)
#                                     ROOF_CUTS[n] along, out to the knob's foot, on each of the roof's six printed layers (n 0 its
#                                     first, z BAR_Z0 + layer(5) to layer(6)), and the foot in the roof's height cut back as far;
#                                     under the roof the foot runs on to the end cut. All six alike: cut back step by step from the
#                                     first layer up (0.4, 0.8 ... 2.4), so that the first layer's strands land on the foot too,
#                                     the roof keeps thin layers out where the bar's sideways bending runs into the carriage, and
#                                     check_knife's plan FE read the roof's ends at 2.0 to 2.2 times the plain bar (1.2 with one
#                                     smooth cut); a square cut-back held at both ends, rounded into the leg, read 1.6 to 2.1
ROOF_CUT = ROOF_CUTS[-1]            # 2.4: the top layer's cut-back, the most of any
END_TAPER = (6.0, 0.0)              # the bar meets the carriage's back end (and its front end) smoothly: over this length its
#                                     outer face widens, flat where it leaves the bar and where it meets the carriage, to the
#                                     inner leg's guide face (to its crowned end under the roof, to LEG_Y1 in the roof's height),
#                                     and in the roof's height the roof's inner end is cut back with a quarter-ellipse
#                                     (ROOF_CUTS), so the bar's outer face runs into the carriage with no square corner
#                                     (check_knife works out what is left in a plan FE)
KNOB_TOP = BAR_Z0 + layer(37)       # 11.90
LIP, LIP_L = 1.0, 2.5               # the knob's two end lips stand this far proud, 2.5 long: the stops meet them. 1.0 (it
#                                     was 1.5 on a 3.0 knob)
SADDLE, SADDLE_L = 13.0, 2.5        # the thumb rests in a saddle at the knob's middle: two ridges 13 apart, each 2.5 long and
#                                     LIP proud, with grip grooves between them. The thumb pushes the front ridge to push and
#                                     the rear one to pull back, so it never moves along the knob to change direction (on a
#                                     38 mm knob the end lips are 33 apart). The end lips stay: the knob's stops meet them
END_Z = BAR_Z0 + layer(1)           # 4.70: the knob's end faces are cut back END_CUT below this and inside END_Y, so a stop
END_Y = 20.9                        # meets only the knob's outer part, from 4.70 up and from 20.9 out: the middle of what
END_CUT = 0.5                       # it meets is 0.3 under the thumb's height and 0.48 inside the thumb's line (0.75 on the
#                                     2.5 knob, 1.7 on the 14 mm knob), so the thumb's push and a stop's hardly turn the knob.
#                                     Not higher: a let-go knob, with no thumb on it, would twist the roof more
# the knob's own TPU stops, one at each end of its travel. Each stands outside the handle against the face of a guard,
# a bump on the handle's knob side (all three plates carry their part of it), and meets the knob's end face, the lips
# (its outer part: END_Y, END_Z), square on at about the height the thumb pushes, KNOB_SOFT past the end of its
# travel. Then the thumb's push and its weight stop at the knob and never run down the bar, and the knob's bar has no
# bumpers of its own any more: nothing reaches its lane's ends
KNOB_T = 2.0                        # the knob stands this far out from KNOB_Y0, its lips and ridges LIP further, 3.7 proud of
#                                     the handle's side (it was 2.5, 3.5 and 3.0 before that): 0.5 thinner, the thumb pushes 0.5
#                                     nearer the bar's line and a stop 0.25 nearer, so every push and every landing turns the
#                                     knob less. In a landing with the thumb held rigid the thumb and the stop squeeze the knob
#                                     from either end, and what turns it is their push times the gap between their two lines
#                                     across, so the two lines are kept close (check_knife works out the knob bar sideways)
LIP_Y1 = KNOB_Y0 + KNOB_T + LIP     # 22.7: the outer face of the knob's lips and the saddle's ridges
STOP_Y1 = LIP_Y1 - 0.2              # the stops stand to just inside it
STOP_L = math.ceil(3.5 * (STOP_Y1 - END_Y - 0.05) / 2.05 * 20 - 1e-6) / 20   # 2.65: each stop's length along the knob's
#                                     travel, standing free of the guard. On the 2.5 knob a 3.5 stop met 2.05 of the knob's end
#                                     face across (y 20.95 to 23.0); on the 2.0 knob it meets 1.55, so it is shorter in step
#                                     (to the next 0.05 up), to keep E A / L, and so the stop's stiffness, as it was: a softer
#                                     stop lets the riser's cap and the pad take more of the landing and turns the knob more
STOP_SQ = 0.55 * STOP_L             # 1.46: the most it may squash (the knob-landing checks prove it never comes near)
KNOB_ROOM = KNOB_SOFT + STOP_SQ + 0.3   # 1.96: the knob goes this far past each end of its travel before its carriage meets
#                                     the end of its slot, if a stop is ever left out
STOP_Y0 = HW / 2 + 0.1              # across: 0.1 off the handle's side, to just inside the lips' outer face (STOP_Y1, below)
STOP_Z0 = BAR_Z0                    # 4.45 = layer(22) of the base plate, the knob's bottom: the stop stands on its T ...
STOP_H = layer(34)                  # ... 6.85 tall, to 11.30, 0.6 under the knob's top. It meets the knob from END_Z up,
#                                     so the middle of what it meets is at the thumb's line (it was 0.4 under it, toward
#                                     the bar's own weight, for a let-go knob, and a short stem's twist): every throw the
#                                     thumb and the stop then squeeze the knob straight, and the long carriage takes the
#                                     let-go knob's twist (check_knife works both out)
T_NECK_W, T_NECK_L = 1.6, 1.3       # a T on the stop's back, at its foot, drops into a T-slot in the base plate's guard:
T_HEAD_W, T_HEAD_L = 3.6, 1.4       # the head can't pass the slot's 1.2 thick shoulders, so the stop can't come out ...
T_H = layer(12)                     # ... and stands 0.15 under the middle plate
T_GRIP = 0.05                       # the slot is this much narrower than the head each side, and wider than the neck
STOP_RECESS = round(STOP_SQ + 0.25, 2)   # 1.71: the stop's face is cut back this far inside END_Y + 0.05 (it was flat): the
#                                     knob's inner part, cut back END_CUT, met the flat face once the stop squashed past 0.5,
#                                     and the hard landings squash it 1.4, so the stop got stiffer and pushed on a line further
#                                     in. Cut back more than the most it may squash (STOP_SQ + 0.2), it meets only the knob's
#                                     outer part. It was 2.15 on the 3.5 stop; on the 2.65 stop that would leave its inner part
#                                     0.5 long, under two lines, so it is STOP_SQ + 0.25 and the inner part 0.94. So the rear
#                                     and the front stop are mirror images, not one part turned round ...
T_OFFSET = 0.4                      # ... and the T stands this far outward of the stop's middle, so a stop turned round to go
#                                     at the wrong end has its T 0.8 off its slot and won't go in
GUARD_Y1 = 24.2                     # the guards stand out to here, 1.5 past the lips (as far as they did on the 3.5 knob, the
#                                     handle 43.2 wide there): the stop's T-slot needs two lines of wall outside its head ...
GUARD_TOP = 4.0                     # ... 4 mm flat along the top, then a 45 degree slope back into the handle's side

# band level: two sleds, one band, two pads
SLED_H = layer(10)                  # 2.05
SLED_Z0, SLED_Z1 = Z_FLOOR, Z_FLOOR + SLED_H   # 7.70 to 9.75
SLED_LEN, SLED_HW, WING_L = 22.0, 7.0, 14.0    # long, so a riser pushing its wing can't twist it much
POST_D, EYE_PLAY = 3.0, 0.4
POST_BACK = 17.0                    # the band's post is this far from the sled's lug face, near the sled's far end (it
#                                     was 10.5): the band is 13 mm longer, so it can be fitted with more stretch (below)
POCKET_Z = SLED_Z0 + layer(4)       # 8.55 the band sits on this: 0.85 of floor under the post
CAV_Y0, CAV_Y1 = -SLED_HW - 0.3, RISER_Y1 + 0.3  # band level cavity
R_B = LUG_L + TRAVEL + G_P - THROW  # 66.3: sled B's lug face from the lug's back face (closed), knob back
PAD_L, PAD_HW, PAD_IN = 9.5, 2.5, 4.0          # TPU pads 9.5 x 5, the back 4.0 pressed into a pocket
PAD_X0 = X_L0 - G_P - SOFT - SLED_LEN - PAD_L  # 1.9: rear pad, sled F's soft stop
PAD_X1 = X_L0 + R_B + THROW + SOFT + SLED_LEN + PAD_L   # 160.1: front pad, sled B's soft stop
BAND = (layer(4), 0.85, 1.3)        # height, strand width, eye ring width (it was 1.05 x 0.95, fitted 5 mm over: below)
BAND_STRONG = (layer(5), 1.12, 1.8)  # for a soft TPU (it was 1.25 x 1.3)
BAND_SOFT = (layer(3), 0.9, 1.3)     # for a stiff TPU (it was 0.85 x 0.95)
BAND_W = BAND[0]
# which band to fit: TPU's stiffness varies a lot from brand to brand, so hang a normal band from a full half-litre
# bottle of water (about 0.5 kg with its bottle, 4.9 N) and measure how far it stretches. check_knife works out the
# stretch from the same band model its throws use, and proves each band below gets to its lock, with the thumb under
# 33 N, over every stretch it is fitted at, even read 1 mm out
HANG_N = 4.9
HANG_STRONG = 39.0                  # the normal band stretches this much or more: the TPU is soft, fit band strong
HANG_SOFT = 25.0                    # this much or less: the TPU is stiff, fit band soft
HANG_MIN, HANG_MAX = 20.0, 60.0     # outside these the TPU is stiffer or softer than check_knife has worked out (the band
#                                     is longer and softer than it was, so it stretches further: these were 27, 17, 14, 41)
HANG_FIT_LO, HANG_FIT_HI = 23.0, 39.0   # and the band you are about to fit, whichever kind, hung the same way, must stretch this
#                                     much: the stiffest and the softest band the throws and knocks were worked out for
HANG_CONDITION = 130.0              # before any hang test, stretch the band about 10 times to this far eye to eye (1.5 times
#                                     its length): TPU softens the first few times it is stretched further than before
BAND_FILLET = 1.0                   # where the strand meets each eye
EYE_D = POST_D + 2 * EYE_PLAY + 2 * BAND_STRONG[2] + 0.6   # 8.0 the eye's pocket in each sled
BAND_PRELOAD = 12.5                 # the band is fitted 12.5 mm over its printed length (it was 5), and is thinner: it
#                                     gives the blade the same energy over the same throw with a flatter pull, 0.85 of what it
#                                     pulled at the trip, so the thumb pushes less. A band stores kb/2 (x_t^2 - x_e^2) between
#                                     its stretch at the trip x_t and where the sleds land x_e = BAND_PRELOAD, x_t - x_e the throw
#                                     (21.9): more stretch at rest and a softer band (kb x 0.68 here) gives the same energy with
#                                     less pull at x_t. Fully cocked it stretches 44 %, under check_knife's 45 %
BAND_RELAXED = R_B + G_P + 2 * POST_BACK - BAND_PRELOAD  # 88.1 eye to eye: taut by 12.5 mm when parked

# printed screws: M6-ish, 2 mm pitch, threaded into posts on the top plate
SCREWS = [(6.0, 13.0), (6.0, -13.0), (172.0, 13.0), (172.0, -13.0)]
THREAD_MAJ, THREAD_MIN, PITCH = 6.0, 4.4, 2.0
THREAD_PLAY = 0.38                  # nut thread bigger all round ...
GROOVE_WIDEN = 0.15                 # ... and its groove 0.15 wider on each flank
SCREW_HOLE = 6.8
HEAD_D, HEAD_H = 8.0, layer(7)      # 1.45 tall, so it stays under the channel floor
COUNTERBORE = HEAD_D + 0.8
COIN_W, COIN_D = 2.0, layer(4)      # the coin slot: a penny or a quarter fits
SCREW_TIP = layer(57)               # 11.45
BOSS_D = 8.9                        # the top plate's four threaded posts, round, 1.07 of wall over the thread ...
BOSS_Z0 = HT - layer(25)            # ... reach down to 7.30, 0.25 short of the base plate, so they clamp through
THREAD_TOP = HT - layer(3)          # their thread stops at 11.70, under 0.65 of top skin
POST_POCKET_D = 9.7                 # the posts stand in these round pockets through the middle plate: 0.4 all round,
#                                     as for any peg in a hole (holes print small). Round, because a hex pocket with
#                                     that room would leave under two lines to the outline and over the thread. Not
#                                     9.9: the band level's cavity runs under the rear screws (its side at y 7.3 at
#                                     x 6), and 9.9 would leave 0.75 there; 9.7 leaves 0.85, two lines
LOOSE_PLAY = THREAD_PLAY + 0.05     # handle 3 top loose's thread, if the fit test says so
NUT_AF, NUT_H = 8.6, layer(21)      # the fit test's gauge nuts, 4.25 thick ...
NUT_CUT = 0.6                       # ... marked by cutting corners off this deep: each leaves a 2.08 flat
FIT_PLAYS = (THREAD_PLAY - 0.05, THREAD_PLAY, LOOSE_PLAY)   # nuts 1, 2 and 3: a little tighter than the posts,
#                                                             the same, and as the loose top plate
PEGS = [(14.0, -15.0), (164.0, -15.0)]
PEG_D, PEG_H, PEG_HOLE_D = 3.0, 1.0, 3.7      # 0.35 all round (holes print small: the brain's 0.35-0.4), the tightest of the
#                                               plates' locators, so the middle plate sits at most 0.35 off the base plate
#                                               across (it was 0.4), and the risers' slots in it can't pinch the knob's carriage
PEG_HOLE_H2, PEG_HOLE_H3 = layer(6), 1.20     # in the middle plate (from its bottom) and the top plate (from its top)
PEG_FLAT = -0.05                    # each peg hole in the middle and top plates is a D: the round hole with a flat on its knob
#                                     side (+y), drawn 0.05 into its peg. Pressed on, a plate slides that far away from the
#                                     blade, and it can't sit off toward the blade past the flat; away from it it still has the
#                                     round hole's 0.35, less the 0.05. The flat is a straight wall, which prints where it is
#                                     drawn to within a print's PRINT_OFF; the round part prints small, which only pushes the
#                                     plate further away from the blade
PRINT_OFF = 0.05                    # how far a printed straight wall can come out from where it is drawn (as the carriage's fit)
PLATE_IN = max(0.0, PEG_FLAT + PRINT_OFF)   # 0: so the middle and top plates never sit off toward the blade
PEG_LEAD = 0.2                      # each peg's top layer is set back this far on its knob side: a lead-in for the flat

FINGERS = [60.0, 84.0, 108.0]
FINGER_R, FINGER_DEPTH = 9.0, 1.6

# print settings (PRINTER-BRAIN, strong parts): hotter, less fan, slower walls, solid
STRONG_PLA = {"nozzle_temperature": "230", "nozzle_temperature_initial_layer": "230", "fan_min_speed": "45",
              "fan_max_speed": "45", "additional_cooling_fan_speed": "0", "filament_flow_ratio": "1.02"}
STRONG_PROCESS = {"default_acceleration": "3000", "outer_wall_acceleration": "3000",
                  "inner_wall_acceleration": "3000", "internal_solid_infill_acceleration": "3000"}
SLOW = {"outer_wall_speed": "60", "inner_wall_speed": "60", "internal_solid_infill_speed": "60",
        "top_surface_speed": "60", "gap_infill_speed": "60"}                       # strong PLA's 60 mm/s
SOLID = {"wall_loops": "6", "sparse_infill_density": "100%", **SLOW}               # printed screws
THREADS = {**SOLID, "outer_wall_speed": "40", "inner_wall_speed": "40"}            # gauge nuts print like ...
LID = {"wall_loops": "4", "outer_wall_speed": "40", "inner_wall_speed": "40"}      # ... the top plate's posts
MOVING = {"wall_loops": "4", "sparse_infill_density": "100%", **SLOW}              # parts that take knocks
BRIM = {"brim_type": "outer_only", "brim_width": "5"}                              # long thin parts (PRINTER-BRAIN)
NO_BRIM = {"brim_type": "no_brim"}                  # a part whose first layer has a groove under a roof: a brim would fill
#                                                     the groove (it brims the gap between two islands of one part)
TPU_SOLID = {"sparse_infill_density": "100%"}       # every TPU part prints solid, as check_knife models it (the stock
#                                                     15 % leaves sparse layers inside a pad, about 11 % softer)


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
    """Screw as fitted: head in the base plate's counterbore, tip inside its nut."""
    head = cyl_z(x, y, 0, HEAD_H, HEAD_D, 64) - box(x - HEAD_D, x + HEAD_D, y - COIN_W / 2, y + COIN_W / 2, -1, COIN_D)
    tip = SCREW_TIP
    shank = thread(x, y, HEAD_H - 0.01, tip - 0.6, THREAD_MIN / 2, THREAD_MAJ / 2)
    point = M.cylinder(0.6, THREAD_MAJ / 2 - 0.1, THREAD_MIN / 2, 48).translate([x, y, tip - 0.6]) \
        ^ thread(x, y, tip - 0.6, tip, THREAD_MIN / 2, THREAD_MAJ / 2)
    return union([head, shank, point, cyl_z(x, y, HEAD_H - 0.01, tip, THREAD_MIN - 0.01)])


def nut(x=0.0, y=0.0, play=THREAD_PLAY, corners=0, z0=BOSS_Z0):
    """A gauge nut for the fit test: the top plate's post thread, in a nut. It is marked by cutting
    `corners` of its corners off, every other one (at 0, 120 and 240 degrees: hexagon() puts a
    corner at +x), NUT_CUT deep through its whole height: flats you can see and count, with 0.9 or
    more of wall left over the thread."""
    z1 = z0 + NUT_H
    body = extrude(hexagon(NUT_AF).translate([x, y]), z0, z1)
    hole = thread(x, y, z0 - 0.5, z1 + 0.5, THREAD_MIN / 2 + play, THREAD_MAJ / 2 + play, GROOVE_WIDEN)
    r_v = NUT_AF / math.sqrt(3)         # 4.965 to each corner
    cuts = [hole] + [box(r_v - NUT_CUT, r_v + 2, -3, 3, z0 - 1, z1 + 1).rotate([0, 0, 120 * i]).translate([x, y, 0])
                     for i in range(corners)]
    return body - union(cuts)


def lid_thread(x, y, play=THREAD_PLAY):
    """The thread cut up through a post of the top plate, blind under its top skin."""
    return thread(x, y, BOSS_Z0 - 0.5, THREAD_TOP, THREAD_MIN / 2 + play, THREAD_MAJ / 2 + play, GROOVE_WIDEN)


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
    """The pegs on a plate's top face at z: round, their top layer set back PEG_LEAD on the knob side, a lead-in for the
    flat in the hole above."""
    return union([cyl_z(x, y, z, z + PEG_H, PEG_D) - box(x - 3, x + 3, y + PEG_D / 2 - PEG_LEAD, y + 3, z + PEG_H - 0.2,
                                                         z + PEG_H + 1) for x, y in PEGS])


def peg_flat_y(y):
    """The y of the flat in the D-shaped hole for the peg at y: drawn PEG_FLAT off the peg's knob side."""
    return y + PEG_D / 2 + PEG_FLAT


def peg_holes(z, depth, foot=0.0):
    """The D-shaped peg holes from z, depth deep: the round PEG_HOLE_D hole with a flat on its knob side (peg_flat_y).
    foot: where the plate prints on this face, its first layer is set back this much more at the flat (it spreads)."""
    out = []
    for x, y in PEGS:
        rnd = cyl_z(x, y, z - 0.01, z + depth, PEG_HOLE_D)
        out.append(rnd ^ box(x - 3, x + 3, y - 3, peg_flat_y(y), z - 1, z + depth + 1))
        if foot:
            out.append(rnd ^ box(x - 3, x + 3, y - 3, peg_flat_y(y) + foot, z - 1, z + layer(1)))
    return union(out)


def windows():
    """(x0, x1) of the closed and open windows in the latch wall."""
    return (X_BLK - W_FAR, RAIL_X0), (RAIL_X1, X_BLK + TRAVEL + BLK_L + W_FAR)


def rail_groove():
    """The rail's room in the base plate: the spine's groove, narrowed at each end where a
    cushion's outer part is pressed in; a pocket for each catch; and the block's path between
    the two catches."""
    c0, c1 = SPINE_X0 - 0.1 - CUSH_L, SPINE_X1 + 0.1 + CUSH_L
    gy0, gy1 = SPINE_Y0 + CUSH_GRIP, SPINE_Y1 - CUSH_GRIP
    return union([
        box(c0 + CUSH_HELD, c1 - CUSH_HELD, GROOVE_Y0, GROOVE_Y1, RAIL_Z0, LANE_Z0 + 1),
        box(RAIL_X0 + SEG_L - RAIL_MOVE - 0.5, RAIL_X1 - SEG_L + RAIL_MOVE + 0.5, GROOVE_Y0, GROOVE_Y1 + SPINE_WIDEN,
            RAIL_Z0, LANE_Z0 + 1),
        box(c0, c0 + CUSH_HELD + 0.01, gy0, gy1, RAIL_Z0, LANE_Z0 + 1),
        box(c1 - CUSH_HELD - 0.01, c1, gy0, gy1, RAIL_Z0, LANE_Z0 + 1),
        box(RAIL_X0 - RAIL_MOVE, RAIL_X0 + SEG_L + RAIL_MOVE, RAIL_Y0 - 0.1, GROOVE_Y1, RAIL_Z0, LANE_Z0 + 1),
        box(RAIL_X1 - SEG_L - RAIL_MOVE, RAIL_X1 + RAIL_MOVE, RAIL_Y0 - 0.1, GROOVE_Y1, RAIL_Z0, LANE_Z0 + 1),
        box(RAIL_X0 + SEG_FLAT + RAMP_L - RAIL_MOVE, RAIL_X1 - SEG_FLAT - RAMP_L + RAIL_MOVE, CHAN_Y - 0.01, WIN_Y1,
            WALL_T, LANE_Z0 + 1)])


def rail_y(x, dx=0.0):
    """The rail's inner face at x (rail shifted dx), or None where there is no catch."""
    t = math.tan(math.radians(SEG_RAMP))
    for x_end, sgn in ((RAIL_X0 + dx, 1), (RAIL_X1 + dx, -1)):
        u = (x - x_end) * sgn                  # distance in from the catching end
        if 0 <= u <= RAIL_CHAMFER:
            return RAIL_Y0 + RAIL_CHAMFER - u
        if RAIL_CHAMFER < u <= SEG_FLAT:
            return RAIL_Y0
        if SEG_FLAT < u <= SEG_FLAT + RAMP_L:
            return RAIL_Y0 + (u - SEG_FLAT) * t
    return None


def bar_x(s=0.0):
    """x range of the bar's body at knob travel s."""
    return CAM_A_TOP - CAM_FLAT + s, CAM_B_TOP + CAM_FLAT + s


def knob_slot_x():
    """The carriage's slot through the base plate's side (the rib left standing in it): its ends are KNOB_ROOM past
    the carriage's two ends of travel."""
    return STEM_X0 - KNOB_ROOM, STEM_X1 + THROW + KNOB_ROOM


def lane_x():
    """The lane's two ends: 0.3 past the bar's ends with the carriage on an end of its slot."""
    return bar_x(-KNOB_ROOM - 0.3)[0], bar_x(THROW + KNOB_ROOM + 0.3)[1]


def stop_face_x():
    """x of the rear and the front knob stop's face, where the knob's back and front faces meet them."""
    return STEM_X0 - KNOB_SOFT, STEM_X1 + THROW + KNOB_SOFT


def guard_face_x():
    """x of the two guards' faces, which the stops' backs stand against."""
    r, f = stop_face_x()
    return r - STOP_L, f + STOP_L


def t_y():
    """The middle (y) of a knob stop's T, and of its slot: T_OFFSET outward of the stop's middle."""
    return (STOP_Y0 + STOP_Y1) / 2 + T_OFFSET


def knob_stop(which):
    """One TPU knob stop: 'R' in front of the rear guard, 'F' in front of the front guard. A block that
    the knob's end face meets, with a T on its back at its foot, in the base plate's guard. Its face is
    recessed STOP_RECESS inside END_Y + 0.05, so it meets only the knob's outer part: the front stop is
    the rear one's mirror image."""
    yc = t_y()
    z0, zt = STOP_Z0, STOP_Z0 + T_H
    part = union([box(0, STOP_L, STOP_Y0, STOP_Y1, z0, z0 + STOP_H),
                  box(-T_NECK_L - 0.01, 0.01, yc - T_NECK_W / 2, yc + T_NECK_W / 2, z0, zt),
                  box(-T_NECK_L - T_HEAD_L, -T_NECK_L, yc - T_HEAD_W / 2, yc + T_HEAD_W / 2, z0, zt)])
    part = part - box(STOP_L - STOP_RECESS, STOP_L + 1, STOP_Y0 - 1, END_Y + 0.05, z0 - 1, z0 + STOP_H + 1)   # the recess
    gr, gf = guard_face_x()
    if which == "R":
        return part.translate([gr, 0, 0])
    return part.mirror([1, 0, 0]).translate([gf, 0, 0])


def stop_slots():
    """The T-slots in the base plate's two guards: a mouth T_GRIP wider than the stop's neck through
    the guard's 1.2 thick face, and behind it a pocket T_GRIP narrower than the T's head, with 0.1 of
    play along x each way, so the stop's back, not its T, bears on the guard."""
    yc = t_y()
    wn, wh = T_NECK_W / 2 + T_GRIP, T_HEAD_W / 2 - T_GRIP
    m0, h0 = T_NECK_L - 0.1, T_NECK_L + T_HEAD_L + 0.1          # 1.2, 2.8 behind the face
    out = []
    for xf, sgn in zip(guard_face_x(), (-1, 1)):
        xs = sorted((xf, xf + sgn * m0))
        xh = sorted((xf + sgn * m0, xf + sgn * h0))
        out += [box(xs[0] - 0.01, xs[1] + 0.01, yc - wn, yc + wn, STOP_Z0, Z1 + 1),
                box(xh[0], xh[1], yc - wh, yc + wh, STOP_Z0, Z1 + 1)]
    return union(out)


def guard_poly(which):
    """The plan of the rear ('R') or front ('F') guard: its face toward the knob, GUARD_TOP flat along
    its top, then a 45 degree slope back into the handle's side; drawn from inside the side wall (y 17.5)."""
    gr, gf = guard_face_x()
    y0, y1 = 17.5, GUARD_Y1
    if which == "R":
        return [(gr, y0), (gr, y1), (gr - GUARD_TOP, y1), (gr - GUARD_TOP - (y1 - y0), y0)]
    return [(gf, y0), (gf + GUARD_TOP + (y1 - y0), y0), (gf + GUARD_TOP, y1), (gf, y1)]


def guards(z0, z1, chamfer_bottom=False, chamfer_top=False):
    """Both guards, between z0 and z1, with the handle's chamfer on the outside face if asked."""
    out = []
    for which in "RF":
        cs = m3.CrossSection([guard_poly(which)])
        if cs.area() <= 0:
            cs = m3.CrossSection([list(reversed(guard_poly(which)))])
        inner = cs.offset(-CHAMFER, m3.JoinType.Miter, 2.0)
        pts = lambda c, za, zb: np.asarray(extrude(c, za, zb).to_mesh().vert_properties)[:, :3]
        if chamfer_bottom:
            out.append(M.hull_points(np.vstack([pts(inner, z0, z0 + 0.01), pts(cs, z0 + CHAMFER, z1)])))
        elif chamfer_top:
            out.append(M.hull_points(np.vstack([pts(cs, z0, z1 - CHAMFER), pts(inner, z1 - 0.01, z1)])))
        else:
            out.append(extrude(cs, z0, z1))
    return union(out)


def front_screw_joins():
    """The front screw holes run into the blade slot: cut each join as one smooth shape, so no
    thin sliver or cusp of plastic is left between them."""
    joins = []
    for yy in (13.0, -13.0):
        sgn = 1 if yy > 0 else -1
        strip = box(172.0 - SCREW_HOLE / 2, 172.0 + SCREW_HOLE / 2, sgn * (SLOT_Y + 0.5) - 0.05, sgn * (SLOT_Y + 0.5) + 0.05,
                    WALL_T, Z1 + 1)
        joins.append((cyl_z(172.0, yy, WALL_T, Z1 + 1, SCREW_HOLE, 64) + strip).hull())
    joins.append(box(172.0 - SCREW_HOLE / 2, 172.0 + SCREW_HOLE / 2, -SLOT_Y - 0.5, SLOT_Y + 0.5, WALL_T, Z1 + 1))
    return union(joins)


def plate1():
    """Base plate: bottom wall, the blade's channel, the latch wall with its two windows, the
    rail's groove and its cushions' pocket, the knob bar's lane, the knob's slot, and its part of
    the two guards with the knob stops' T-slots."""
    p = slab(0, Z1, chamfer_bottom=True) + guards(0, Z1, chamfer_bottom=True)
    lx0, lx1 = lane_x()
    kx0, kx1 = knob_slot_x()
    cuts = [box(REAR_IN, FRONT_IN, -CHAN_Y, CHAN_Y, WALL_T, Z1 + 1),                  # channel
            box(FRONT_IN - 1, HL + 1, -SLOT_Y, SLOT_Y, WALL_T, Z1 + 1),               # blade slot
            box(lx0, lx1, Y_CAM - LANE_IN, LANE_Y1, LANE_Z0, Z1 + 1),                  # cams' and bar's lane
            box(kx0, kx1, LANE_Y1 - 0.1, HW / 2 + 1, LANE_Z0, Z1 + 1),                 # knob slot
            box(LANE_RELIEF_X0, kx0 + 0.01, LANE_Y1 - 0.01, RIB_Y0, LANE_Z0, Z1 + 1),    # the lane's wall relieved behind it
            stop_slots(), rail_groove(), front_screw_joins()]
    cuts += [box(w0, w1, CHAN_Y - 0.01, WIN_Y1, WALL_T, RAIL_TOP + 1) for w0, w1 in windows()]
    cuts += [cyl_z(x, y, -1, HEAD_H, COUNTERBORE, 64) for x, y in SCREWS]
    p = p - union(cuts) - screw_holes(0, Z1)
    return p + pegs(Z1) + rib()


def rib():
    """The knob's slot leaves the bottom of the side wall standing: a rib 1.4 wide (RIB_Y0 to the handle's side) and 1.0
    tall (LANE_Z0 to RIB_TOP) the knob's carriage rides on, its inner leg on the rib's inner face and the knob's foot on its
    outer face."""
    kx0, kx1 = knob_slot_x()
    return box(kx0 - 0.01, kx1 + 0.01, RIB_Y0, HW / 2, LANE_Z0 - 0.01, RIB_TOP)


def lug_slot_x():
    return X_L0 - OVERRUN - 0.3, X_L0 + LUG_L + TRAVEL + OVERRUN + 0.3


def riser_sweep(x0, x1):
    """The risers' slots run 0.6 past the knob's room, so even with a stop left out the carriage meets
    the end of its slot before a riser could meet the end of its own."""
    return x0 - KNOB_ROOM - 0.6, x1 + THROW + KNOB_ROOM + 0.6


def riser_x():
    """(x0, x1) of riser F and riser B on the bar at s = 0."""
    f = (X_L0 - G_P, X_L0 - G_P + RISER_L)
    b = (X_L0 + R_B - RISER_L, X_L0 + R_B)
    return f, b


def wing_room_x():
    """x range of the band level's wide part, where the sleds' wings go: SLED_ROOM past where each
    sled meets its pad."""
    return X_L0 - G_P - SOFT - SLED_ROOM - WING_L - 0.3, X_L0 + R_B + THROW + SOFT + SLED_ROOM + WING_L + 0.3


def plate2():
    """Middle plate: the floor over the channel (with the lug's slot and the risers' slots),
    and the band level above it, open at the top, where the sleds, the band and the pads go.
    The top plate's threaded posts stand in round pockets right through it. Its part of the two
    guards on the knob's side. Prints with its bottom face on the bed, so nothing bridges."""
    p = slab(Z1, Z2) + guards(Z1, Z2)
    (f0, f1), (b0, b1) = riser_x()
    wx0, wx1 = wing_room_x()
    pad_y = PAD_HW - 0.1                                     # the pads are pressed in
    cuts = [box(*lug_slot_x(), -LUG_HW - 0.7, LUG_HW + 0.7, Z1 - 1, Z_FLOOR + 1),
            box(*riser_sweep(f0, f1), RISER_SLOT_Y0, RISER_SLOT_Y1, Z1 - 1, Z_FLOOR + 1),
            box(*riser_sweep(f0, f1), RISER_F_SLOT_Y1 - 0.01, RISER_F_SLOT_Y1 + RISER_F_ROOM, Z1 - 1, Z2 + 1),   # room out
            box(*riser_sweep(b0, b1), RISER_SLOT_Y0, RISER_SLOT_Y1, Z1 - 1, Z_FLOOR + 1),   # a web between the two
            box(*riser_sweep(b0, b1), RISER_SLOT_Y1 - 0.01, RISER_SLOT_Y1 + RISER_B_ROOM, Z1 - 1, Z2 + 1),
            # band level: the sleds' bodies, their wings, and the pads' pockets at the two ends
            box(PAD_X0 + PAD_IN, PAD_X1 - PAD_IN, CAV_Y0, -CAV_Y0, Z_FLOOR, Z2 + 1),
            box(wx0, wx1, CAV_Y0, CAV_Y1, Z_FLOOR, Z2 + 1),
            box(PAD_X0, PAD_X0 + PAD_IN + 0.01, -pad_y, pad_y, Z_FLOOR, Z2 + 1),
            box(PAD_X1 - PAD_IN - 0.01, PAD_X1, -pad_y, pad_y, Z_FLOOR, Z2 + 1),
            peg_holes(Z1, PEG_HOLE_H2, FOOT), screw_holes(Z1, Z2)]
    cuts += [cyl_z(x, y, Z1 - 1, Z2 + 1, POST_POCKET_D, 96) for x, y in SCREWS]
    p = p - union(cuts)
    return p + pegs(Z2)


def plate3(play=THREAD_PLAY):
    """Top plate: the lid over the band level, with a threaded post at each screw that reaches
    down through the middle plate, and its part of the two guards. Prints top face down, so the
    posts stand up from it."""
    p = slab(Z2, HT, chamfer_top=True) + guards(Z2, HT, chamfer_top=True)
    posts = union([cyl_z(x, y, BOSS_Z0, Z2 + 0.01, BOSS_D, 96) for x, y in SCREWS])
    return (p + posts) - union([peg_holes(Z2, PEG_HOLE_H3)] + [lid_thread(x, y, play) for x, y in SCREWS])


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


def arm_L():
    """Bending length of the latch arm: root to the middle of its nose."""
    return ARM_ROOT - NOSE_C


def arm_t(x):
    """The arm's thickness at x. Its inner face (toward -y, the way it bends) runs straight along
    ARM_Y0; its outer face is ARM_Y0 + arm_t(x). ARM_T from its tip to the middle of its nose, then
    growing toward the root as a beam of even strength does (t squared rising in step with the
    bending moment), to ARM_T_ROOT, and over the last ARM_FLARE_L a smooth flare ARM_FLARE thicker
    still, flat where it meets the round ends of the gaps at the root."""
    u = min(max((x - NOSE_C) / arm_L(), 0.0), 1.0)
    t = math.sqrt(ARM_T ** 2 + (ARM_T_ROOT ** 2 - ARM_T ** 2) * u)
    f = (x - (ARM_ROOT - ARM_FLARE_L)) / ARM_FLARE_L
    if f > 0:
        f = min(f, 1.0)
        t += ARM_FLARE * f * f * (3 - 2 * f)
    return t


_ARM_BEND = {}


def arm_bend(n=600):
    """The arm pushed at the middle of its nose by 1 N, worked out as a beam from its root (s = 0) to
    the nose (s = arm_L()), as thick as arm_t and CAR_T tall: (s, how far the centre line moves per
    mm the nose moves, the nose's slope per mm it moves, and the nose's movement per N times the
    PLA's stiffness E, mm MPa / N)."""
    key = (ARM_ROOT, ARM_T, ARM_T_ROOT, ARM_FLARE, ARM_FLARE_L, NOSE_C, CAR_T, n)
    if key not in _ARM_BEND:
        L = arm_L()
        s = np.linspace(0.0, L, n + 1)
        t = np.array([arm_t(ARM_ROOT - v) for v in s])
        kappa = (L - s) / (CAR_T * t ** 3 / 12)          # curvature times E, per N at the nose
        theta = np.concatenate([[0.0], np.cumsum((kappa[1:] + kappa[:-1]) / 2 * np.diff(s))])
        w = np.concatenate([[0.0], np.cumsum((theta[1:] + theta[:-1]) / 2 * np.diff(s))])
        _ARM_BEND[key] = (s, w / w[-1], theta[-1] / w[-1], w[-1])
    return _ARM_BEND[key]


def arm_dy(x, deflect):
    """How far the arm's centre line has moved toward -y at x, bent deflect at the nose: the bent
    beam's curve to the nose (arm_bend), and straight on (at the nose's slope) past it."""
    s_, w_, slope, _ = arm_bend()
    L = arm_L()
    s = ARM_ROOT - x
    if s <= 0:
        return 0.0
    if s <= L:
        return deflect * float(np.interp(s, s_, w_))
    return deflect * (1 + slope * (s - L))


def arm_slope(deflect):
    return arm_bend()[2] * deflect


def nose_poly(deflect):
    """The nose as bent: on the arm's tip, turned with it."""
    yc = ARM_Y0 + ARM_T / 2
    th = arm_slope(deflect)
    pts = [(NOSE_C - NOSE_HW, ARM_Y0 + ARM_T - 0.01), (NOSE_C + NOSE_HW, ARM_Y0 + ARM_T - 0.01),
           (NOSE_C + NOSE_HW, NOSE_TOP), (NOSE_C - NOSE_HW, NOSE_TOP)]
    c, s = math.cos(th), math.sin(th)
    dy = arm_dy(NOSE_C, deflect)
    return [(NOSE_C + (x - NOSE_C) * c - (y - yc) * s, yc - dy + (x - NOSE_C) * s + (y - yc) * c) for x, y in pts]


def nose_top_y(deflect):
    return max(y for _, y in nose_poly(deflect))


def arm_deflect_for(y_out):
    """How far the arm bends (at its nose) when the block's outer face is at y_out."""
    target = y_out - BLK_D
    d = NOSE_TOP - target
    for _ in range(30):
        d += nose_top_y(d) - target
    return d


def arm_room():
    """How far the arm's nose can bend before it meets the floor of its room, less ARM_GAP: 0.1 past
    the most the cam bends it, with the thumb pressing the bar in."""
    return arm_deflect_for(Y_CAM - BAR_IN) + 0.1


def arm_gap_poly(deflect):
    """The room under the arm (toward -y) for it to bend in, from root to past its tip."""
    x_end = BLK_X0 - 0.3
    pts = []
    for i in range(0, 41):
        x = ARM_ROOT - i / 40 * (ARM_ROOT - x_end)
        pts.append((x, ARM_Y0 - arm_dy(x, deflect) - ARM_GAP))
    pts += [(x_end, ARM_Y0 + 0.01), (ARM_ROOT, ARM_Y0 + 0.01)]
    return pts


def carrier(c=0.0, arm_deflect=0.0):
    """Blade, carrier, lug and latch arm (the arm drawn bent by arm_deflect toward -y)."""
    z0, z1 = CAR_Z0, CAR_Z1
    body = box(0, CAR_L, -CAR_W / 2, CAR_W / 2, z0, z1) + extrude(blade_outline(), z0, z1)
    deflect_max = arm_room()
    t_root = arm_t(ARM_ROOT)
    over = [(x, ARM_Y0 + arm_t(x) + ARM_GAP) for x in np.linspace(BLK_X0 - 0.3, ARM_ROOT, 61)]   # the gap's far side
    cuts = [
        prism(arm_gap_poly(deflect_max), z0 - 1, z1 + 1),                                   # room to bend
        prism([(BLK_X0 - 0.3, ARM_Y0 - 0.01), (ARM_ROOT, ARM_Y0 - 0.01)] + list(reversed(over)),
              z0 - 1, z1 + 1),                                                               # the arm, and the gap over it
        cyl_z(ARM_ROOT, ARM_Y0 + t_root + ARM_RELIEF, z0 - 1, z1 + 1, 2 * ARM_RELIEF, 48),  # round ends at the root
        cyl_z(ARM_ROOT, ARM_Y0 - ARM_RELIEF, z0 - 1, z1 + 1, 2 * ARM_RELIEF, 48),
        box(BLK_X0 - BLK_SLOT, BLK_X0 + BLK_L + BLK_SLOT, ARM_Y0 + ARM_T, CAR_W / 2 + 1, z0 - 1, z1 + 1),  # block slot
        box(BLK_X0 - BLK_SLOT - FOOT, BLK_X0 + BLK_L + BLK_SLOT + FOOT, ARM_Y0 + ARM_T, CAR_W / 2 + 1,
            z0 - 1, z0 + layer(1)),                                                          # its first layer set back
        box(-1, CAR_L + 1, CAR_CUT_Y, CAR_W / 2 + 1, CAR_CUT_Z, z1 + 1),                    # room for the cams
        box(CAR_CUT_X2, CAR_L + 1, CAR_CUT_Y2, CAR_W / 2 + 1, CAR_CUT_Z, z1 + 1),           # more, ahead of the block
        extrude(m3.CrossSection.square([GROOVE_X1 - GROOVE_X0, 2.6]).translate([GROOVE_X0, 1.6])
                .offset(0.6, m3.JoinType.Round, 2.0, 16), z1 - GROOVE_D, z1 + 1),
    ]
    body = body - union(cuts)
    # the arm, bent if asked, and its nose turned with it
    x_tip = NOSE_C - NOSE_HW
    top, bot = [], []
    for i in range(0, 61):
        x = ARM_ROOT - i / 60 * (ARM_ROOT - x_tip)
        dy = arm_dy(x, arm_deflect)
        top.append((x, ARM_Y0 + arm_t(x) - dy))
        bot.append((x, ARM_Y0 - dy))
    arm = prism(top + list(reversed(bot)), z0, z1)
    nose = prism(nose_poly(arm_deflect), z0, z1)
    root = box(ARM_ROOT - 0.01, ARM_ROOT + ARM_RELIEF + 0.5, ARM_Y0, ARM_Y0 + t_root, z0, z1)
    lug = box(LUG_X0, LUG_X0 + LUG_L, -LUG_HW, LUG_HW, z1 - 0.01, LUG_TOP) \
        - box(LUG_X0 - 1, LUG_X0 + LUG_L + 1, -BAND_SLOT, BAND_SLOT, BAND_SLOT_Z, LUG_TOP + 1)
    return union([body, arm, nose, root, lug]).translate([C0 + c, 0, 0])


def block_poly(y_out):
    x0, x1, y1 = BLK_X0, BLK_X0 + BLK_L, y_out
    y0, ch = y1 - BLK_D, BLK_CHAMFER
    return [(x0, y0 + ch), (x0 + ch, y0), (x1 - ch, y0), (x1, y0 + ch),
            (x1, y1 - ch), (x1 - ch, y1), (x0 + ch, y1), (x0, y1 - ch)]


def latch_block(c=0.0, y_out=Y_OUT):
    """The latch block with its outer face at y_out; all four upright edges chamfered."""
    return prism(block_poly(y_out), BLK_Z0, BLK_Z1).translate([C0 + c, 0, 0])


def rail(dx=0.0):
    """The rail, shifted dx by its cushions: the spine, and a catch at each end with its flat,
    its ramp and a long taper into the spine. It prints standing on its bottom face, the same
    either way up."""
    top = SPINE_Y0 + 0.01
    r0, r1 = RAIL_X0 + SEG_FLAT + RAMP_L, RAIL_X1 - SEG_FLAT - RAMP_L
    closed = [(RAIL_X0, RAIL_Y0 + RAIL_CHAMFER), (RAIL_X0 + RAIL_CHAMFER, RAIL_Y0), (RAIL_X0 + SEG_FLAT, RAIL_Y0),
              (r0, SEG_RAMP_Y), (RAIL_X0 + SEG_L, top), (RAIL_X0, top)]
    opened = [(RAIL_X1, RAIL_Y0 + RAIL_CHAMFER), (RAIL_X1, top), (RAIL_X1 - SEG_L, top), (r1, SEG_RAMP_Y),
              (RAIL_X1 - SEG_FLAT, RAIL_Y0), (RAIL_X1 - RAIL_CHAMFER, RAIL_Y0)]
    w0, w1, wy = RAIL_X0 + SEG_L, RAIL_X1 - SEG_L, SPINE_Y1 + SPINE_WIDEN
    wide = [(w0, SPINE_Y1 - 0.01), (w1, SPINE_Y1 - 0.01), (w1 - SPINE_WIDEN, wy), (w0 + SPINE_WIDEN, wy)]
    cs = m3.CrossSection.batch_boolean([m3.CrossSection([closed]), m3.CrossSection([opened]), m3.CrossSection([wide]),
                                        m3.CrossSection.square([SPINE_X1 - SPINE_X0, SPINE_Y1 - SPINE_Y0]).translate([SPINE_X0, SPINE_Y0])],
                                       m3.OpType.Add)
    r = extrude(cs, RAIL_Z0, RAIL_TOP)
    # first layer set back on its outer faces, where it slides on the groove's wall
    foot = extrude(cs - cs.translate([0, -FOOT]), RAIL_Z0 - 1, RAIL_Z0 + layer(1))
    return (r - foot).translate([dx, 0, 0])


def cushion(which):
    """One TPU cushion: 'R' behind the spine's back end, 'F' in front of its front end. Its
    outer CUSH_HELD mm press into the groove's narrow end."""
    x0 = SPINE_X0 - 0.1 - CUSH_L if which == "R" else SPINE_X1 + 0.1
    return box(x0, x0 + CUSH_L, SPINE_Y0, SPINE_Y1, RAIL_Z0, CUSH_TOP)


def rail_cushions():
    return cushion("R") + cushion("F")


# ---------------------------------------------------------------- knob bar and sleds
def cam(x_top, rises_back, z0, z1):
    """A cam on the bar's inner face: a CAM_ANGLE ramp up to Y_CAM at x_top, then a flat.
    rises_back: the ramp rises toward -x (cam A, which meets the block from behind)."""
    s = 1 if rises_back else -1
    pts = [(x_top + s * RAMP, Y_OUT + 0.01), (x_top, Y_CAM), (x_top - s * CAM_FLAT, Y_CAM), (x_top - s * CAM_FLAT, Y_OUT + 0.01)]
    return prism(pts, z0, z1)


CAM_A_TOP = X_BLK + C_TRIP - (THROW - CAM_LEAD)          # cam A's top at s = 0: it reaches the block's back corner at s = 26
CAM_B_TOP = X_BLK + TRAVEL - C_TRIP + BLK_L - CAM_LEAD   # cam B's top at s = 0: it reaches the block's front corner at s = 2


def knob_bar(s=0.0):
    """Bar with cam A, cam B, riser F, riser B, the knob's carriage and the knob, at knob travel s. Each
    riser ends in a tongue that its TPU cap presses onto; the cap's face is the riser's face.
    The tongue stands on a full-width foot as high as the sleds' floor, so a knock on the cap
    pulls on the foot's wide root, not on the thin tongue's, and a low sole runs on from the foot
    right out to the riser's face under the cap, so the knock bends the bar at the riser's face."""
    x0, x1 = bar_x(0)
    z0, z1 = BAR_Z0, BAR_Z1
    parts = [box(x0, x1, BAR_Y0, BAR_Y1, z0, z1),
             cam(CAM_A_TOP, True, z0, z1), cam(CAM_B_TOP, False, z0, z1)]
    (f0, f1), (b0, b1) = riser_x()
    ty0 = (BAR_Y0 + RISER_Y1) / 2 - TONGUE_W / 2
    parts += [box(f0 + CAP_L, f1, BAR_Y0, RISER_Y1, z1 - 0.01, RISER_TOP),
              box(f0 + CAP_T + 0.1, f0 + CAP_L + 0.01, ty0, ty0 + TONGUE_W, z1 - 0.01, RISER_TOP),
              box(f0 + CAP_T + 0.1, f0 + CAP_L + 0.01, BAR_Y0, RISER_Y1, z1 - 0.01, SLED_Z0),
              box(f0, f0 + CAP_T + 0.11, BAR_Y0, RISER_Y1, z1 - 0.01, SOLE_TOP),
              box(b0, b1 - CAP_L, BAR_Y0, RISER_Y1, z1 - 0.01, RISER_TOP),
              box(b1 - CAP_L - 0.01, b1 - CAP_T - 0.1, ty0, ty0 + TONGUE_W, z1 - 0.01, RISER_TOP),
              box(b1 - CAP_L - 0.01, b1 - CAP_T - 0.1, BAR_Y0, RISER_Y1, z1 - 0.01, SLED_Z0),
              box(b1 - CAP_T - 0.11, b1, BAR_Y0, RISER_Y1, z1 - 0.01, SOLE_TOP)]
    # the carriage: the bar's inner leg beside the rib, the roof over it, and the knob's foot beside it
    parts += [box(STEM_X0, STEM_X1, BAR_Y1 - 0.01, LEG_Y1, z0, STEM_TOP),
              box(STEM_X0, STEM_X1, BAR_Y1 - 0.01, KNOB_Y0 + 0.1, ROOF_Z0, STEM_TOP),
              box(STEM_X0, STEM_X1, KNOB_FOOT_Y0, KNOB_Y0 + 0.01, z0, STEM_TOP)]
    k_out = KNOB_Y0 + KNOB_T
    knob = box(STEM_X0, STEM_X1, KNOB_Y0, k_out, z0, KNOB_TOP)
    lips = box(STEM_X0, STEM_X0 + LIP_L, k_out - 0.01, k_out + LIP, z0, KNOB_TOP) + \
        box(STEM_X1 - LIP_L, STEM_X1, k_out - 0.01, k_out + LIP, z0, KNOB_TOP)
    xm = (STEM_X0 + STEM_X1) / 2
    saddle = box(xm - SADDLE / 2 - SADDLE_L, xm - SADDLE / 2, k_out - 0.01, k_out + LIP, z0, KNOB_TOP) + \
        box(xm + SADDLE / 2, xm + SADDLE / 2 + SADDLE_L, k_out - 0.01, k_out + LIP, z0, KNOB_TOP)
    n_r = int((SADDLE - 2.0) / 2.5) + 1                        # grip grooves in the saddle, between its ridges
    r0 = xm - 2.5 * (n_r - 1) / 2 - 0.5
    ridges = union([box(r0 + 2.5 * i, r0 + 1.0 + 2.5 * i, k_out - 0.5, k_out + 1, z0 - 1, KNOB_TOP + 1)
                    for i in range(n_r)])
    ends = union([box(x - END_CUT, x + END_CUT, END_CUT_Y0, k_out + LIP + 1, z0 - 1, END_Z) for x in (STEM_X0, STEM_X1)]
                 + [box(x - END_CUT, x + END_CUT, END_CUT_Y0, END_Y, z0 - 1, KNOB_TOP + 1) for x in (STEM_X0, STEM_X1)])
    # where the carriage slides on its rib its first layer (which spreads about 0.1 on the bed) is set back FOOT, as the
    # rail's is on its groove
    first = box(STEM_X0 - END_TAPER[0] - 1, STEM_X1 + END_TAPER[1] + 1, LEG_Y1 - FOOT, KNOB_FOOT_Y0 + FOOT, z0 - 1,
                z0 + layer(1))
    # the guide faces' crowned ends, under the roof: the inner leg's face from the carriage's ends, the knob's foot's from
    # where the end cut leaves it
    crown = crowns([(STEM_X0, 1, END_CUT), (STEM_X1, -1, END_CUT, GUIDE_LEAD_FRONT)])
    parts.append(knob - ridges + lips + saddle)
    tapers = end_tapers()
    if tapers is not None:
        parts.append(tapers)
    return (union(parts) - ends - end_cutbacks() - first - crown).translate([s, 0, 0])


def end_tapers():
    """Where the bar meets each end of the carriage: its outer face widens over END_TAPER from BAR_Y1 to the inner leg's
    face, flat at both ends of the widening (3 t^2 - 2 t^3), under the roof to the leg's crowned end, in the roof's height
    to LEG_Y1."""
    out = []
    for x_e, sgn, L in ((STEM_X0, 1, END_TAPER[0]), (STEM_X1, -1, END_TAPER[1])):
        if L <= 0:
            continue
        cap = FRONT_TAPER_TOP if sgn < 0 else 99.0
        for z0_, z1_, y_top in ((BAR_Z0, ROOF_Z0, min(cap, LEG_Y1 - GUIDE_CROWN)), (ROOF_Z0, STEM_TOP, min(cap, LEG_Y1))):
            n = 32
            pts = [(x_e - sgn * L, BAR_Y1 - 0.01)]
            for i in range(n + 1):
                t = i / n
                pts.append((x_e - sgn * L * (1 - t), BAR_Y1 + (y_top - BAR_Y1) * (3 * t * t - 2 * t ** 3)))
            pts += [(x_e + sgn * 0.01, y_top), (x_e + sgn * 0.01, BAR_Y1 - 0.01)]
            out.append(prism(pts, z0_, z1_))
    return union(out) if out else None


def front_crown_trim():
    """How far in from the carriage's front end the roof's cut-back, starting from the bar's face, takes the inner leg's
    crowned face away: where the quarter-ellipse rises through the crown."""
    y0 = min(LEG_Y1, FRONT_TAPER_TOP) if END_TAPER[1] > 0 else BAR_Y1
    a, b = ROOF_CUT, KNOB_FOOT_Y0 - y0
    crown = lambda d: LEG_Y1 - max(0.0, GUIDE_LEAD_FRONT - d) ** 2 / (2 * GUIDE_R)
    ell = lambda d: (y0 + b) - b * math.sqrt(max(0.0, 1 - (d / a) ** 2)) if d < a else 99.0
    lo, hi = 0.0, a
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if ell(mid) < crown(mid) else (lo, mid)
    return lo


def roof_layers():
    """The roof's printed layers over the rib's channel, [(n, z0, z1)]: from ROOF_Z0 (the slider's layer 5) to its top
    (layer 11), one for each of ROOF_CUTS."""
    out = [(n, BAR_Z0 + layer(5 + n), BAR_Z0 + layer(6 + n)) for n in range(len(ROOF_CUTS))]
    assert abs(out[0][1] - ROOF_Z0) < 1e-9 and abs(out[-1][2] - STEM_TOP) < 1e-9
    return out


def roof_cut_y0(sgn):
    """Where each roof layer's cut-back starts at the end face: the inner leg's face at the back end (sgn +1: the bar widens
    to it), the bar's own face at the front end (it can't widen there: past the knob's slot the lane's wall is at LANE_Y1)."""
    return LEG_Y1 if sgn > 0 else (min(LEG_Y1, FRONT_TAPER_TOP) if END_TAPER[1] > 0 else BAR_Y1)


def quarter_ellipse(x_e, sgn, y_c, a, b, y_top, n=32):
    """The plan of a cut at the carriage's end face x_e: a quarter-ellipse with its centre at (x_e, y_c), a along the carriage
    and b across (from y_c - b at the end face), and on from y_c to y_top as wide as a (a margin past the end face)."""
    pts = [(x_e - sgn * 0.01, y_top), (x_e - sgn * 0.01, y_c - b + 0.01)]
    for i in range(n + 1):
        th = math.pi / 2 * i / n
        pts.append((x_e + sgn * a * math.sin(th), y_c - b * math.cos(th)))
    if y_top > y_c + 1e-9:
        pts.append((x_e + sgn * a, y_top))
    return pts


def roof_layer_cut(x_e, sgn, n):
    """The plan of roof layer n's cut-back at the end face x_e, as a CrossSection: a quarter-ellipse ROOF_CUTS[n] along, from
    the leg's face (the bar's at the front) at the end face out to the knob's foot, with the foot cut back as far."""
    y0, cy = roof_cut_y0(sgn), KNOB_FOOT_Y0
    pts = quarter_ellipse(x_e, sgn, cy, ROOF_CUTS[n], cy - y0, KNOB_Y0)
    area2 = sum(x0 * y1 - x1 * y0_ for (x0, y0_), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    return m3.CrossSection([pts if area2 > 0 else pts[::-1]])


def end_cutbacks():
    """At each end of the carriage, the roof's end cut back over the rib's channel on each of its printed layers
    (roof_layer_cut), so the roof meets the leg with no square corner and takes the bar's sideways bending on gradually; no
    layer is cut back less than the one above it, so none hangs past the one below. Under the roof the knob's foot runs on to
    the end cut, and at the front end the inner leg's last ~1.2 is trimmed along the top layer's quarter-ellipse from the bar's
    face."""
    out = []
    for x_e, sgn in ((STEM_X0, 1), (STEM_X1, -1)):
        for n, z0_, z1_ in roof_layers():
            cs = roof_layer_cut(x_e, sgn, n)
            out.append(extrude(cs, z0_, z1_ + 0.001 if n < len(ROOF_CUTS) - 1 else KNOB_TOP + 1))
        y0 = roof_cut_y0(sgn)
        if y0 < LEG_Y1 - 1e-9:                         # the leg's trim under the roof (in front)
            trim = prism(quarter_ellipse(x_e, sgn, KNOB_FOOT_Y0, ROOF_CUT, KNOB_FOOT_Y0 - y0, KNOB_FOOT_Y0 + 0.01), BAR_Z0 - 1,
                         ROOF_Z0)
            out.append(trim ^ box(x_e - 3 * ROOF_CUT, x_e + 3 * ROOF_CUT, y0 - 1, LEG_Y1 + 0.01, BAR_Z0 - 2, ROOF_Z0 + 1))
    return union(out)


def crowns(ends):
    """What crowns the carriage's two guide faces in plan, under its roof, at each of ends [(x of the end, +1 for a back end
    or -1 for a front end, how far in the knob's foot's face starts, and optionally how long the leg's crown is)]: each face
    curves back over its last GUIDE_LEAD (the leg's at the front end GUIDE_LEAD_FRONT), radius GUIDE_R."""
    crown = []
    for end in ends:
        x_end, sgn, foot_in = end[:3]
        lead_leg = end[3] if len(end) > 3 else GUIDE_LEAD
        for y_face, out, x_start, lead in ((LEG_Y1, -1, x_end, lead_leg), (KNOB_FOOT_Y0, 1, x_end + sgn * foot_in, GUIDE_LEAD)):
            arc = [(x_start + sgn * lead * (1 - i / 8), y_face + out * (lead * i / 8) ** 2 / (2 * GUIDE_R))
                   for i in range(9)]
            arc = [(x_start - sgn * 0.01, arc[-1][1])] + arc[::-1][:-1] + [arc[0]]
            pts = arc + [(arc[-1][0], y_face - out * 0.01), (arc[0][0], y_face - out * 0.01)]
            if (pts[1][0] - pts[0][0]) * (pts[2][1] - pts[0][1]) - (pts[1][1] - pts[0][1]) * (pts[2][0] - pts[0][0]) < 0:
                pts = pts[::-1]
            crown.append(prism(pts, BAR_Z0 - 1, ROOF_Z0))
    return union(crown)


def saddle_x():
    """The middle of the saddle's ridge the thumb pushes, at s = 0: the front one to push the knob forward, the rear one
    to pull it back."""
    xm = (STEM_X0 + STEM_X1) / 2
    return xm + SADDLE / 2 + SADDLE_L / 2, xm - SADDLE / 2 - SADDLE_L / 2


def riser_cap(which, s=0.0):
    """The TPU cap on riser F ('F', on its back face) or riser B ('B', on its front face): a U
    pressed down over the riser's tongue. Its front block, in front of the tongue, stands on the
    riser's sole, its two legs beside the tongue on the riser's foot, so all of it is above the
    latched block's top. The same either way round, so one cap fits both risers."""
    (f0, f1), (b0, b1) = riser_x()
    x0 = f0 if which == "F" else b1 - CAP_L
    ty0 = (BAR_Y0 + RISER_Y1) / 2 - TONGUE_W / 2
    fb = (x0, x0 + CAP_T) if which == "F" else (x0 + TONGUE_L, x0 + CAP_L)       # the front block
    cap = box(x0, x0 + CAP_L, BAR_Y0, RISER_Y1, SLED_Z0, CAP_TOP) + box(fb[0], fb[1], BAR_Y0, RISER_Y1, SOLE_TOP, CAP_TOP)
    sx0, sx1 = (x0 + CAP_T, x0 + CAP_L + 1) if which == "F" else (x0 - 1, x0 + TONGUE_L)
    slot = box(sx0, sx1, ty0 + CAP_GRIP, ty0 + TONGUE_W - CAP_GRIP, SLED_Z0 - 1, CAP_TOP + 1)   # grips the tongue
    return (cap - slot).translate([s, 0, 0])


def sled(front_face_x, kind):
    """Sled F (kind 'F': its lug face is its front, +x) or sled B (lug face at its back).
    front_face_x is the x of its lug face. Its wing (on the knob side, as long as the riser it
    leans on) and the band's post are at the lug end; the rest of its length keeps it square."""
    z0, z1 = SLED_Z0, SLED_Z1
    if kind == "F":
        x0, x1 = front_face_x - SLED_LEN, front_face_x
        post_x = front_face_x - POST_BACK
        wing = box(x1 - WING_L, x1, SLED_HW - 0.01, RISER_Y1, z0, z1)
        slot = box(post_x, x1 + 1, -BAND_SLOT, BAND_SLOT, POCKET_Z, z1 + 1)
    else:
        x0, x1 = front_face_x, front_face_x + SLED_LEN
        post_x = front_face_x + POST_BACK
        wing = box(x0, x0 + WING_L, SLED_HW - 0.01, RISER_Y1, z0, z1)
        slot = box(x0 - 1, post_x, -BAND_SLOT, BAND_SLOT, POCKET_Z, z1 + 1)
    body = box(x0, x1, -SLED_HW, SLED_HW, z0, z1) + wing
    body = body - slot - cyl_z(post_x, 0, POCKET_Z, z1 + 1, EYE_D, 48)
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
    return extrude(band_shape(xa, xb, band), POCKET_Z + 0.01, POCKET_Z + band[0])


def band_shape(xa, xb, band):
    _, w, wr = band
    ri = POST_D / 2 + EYE_PLAY
    ring = lambda x: (m3.CrossSection.circle(ri + wr, 64) - m3.CrossSection.circle(ri, 64)).translate([x, 0])
    strand = m3.CrossSection.square([xb - xa - 2 * ri - wr, w]).translate([xa + ri + wr / 2, -w / 2])
    cs = m3.CrossSection.batch_boolean([ring(xa), ring(xb), strand], m3.OpType.Add)
    # round the corners where the strand meets each eye
    return cs.offset(BAND_FILLET, m3.JoinType.Round, 2.0, 32).offset(-BAND_FILLET, m3.JoinType.Round, 2.0, 32)


def band_length(c, s):
    p_f, p_b = sled_positions(c, s)
    return (p_b + POST_BACK) - (p_f - POST_BACK)


def band_print(band):
    return extrude(band_shape(0.0, BAND_RELAXED, band), 0, band[0])


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


def project_settings(filaments=None, tpu_filament=None, process=None):
    """Flash Studio's project settings (flash studio settings.json), with changes for some
    filaments. filaments: {filament number: {key: value}}, each change also named in
    different_settings_to_system so Flash Studio keeps it. tpu_filament: a filament number to
    turn into Generic TPU (flash studio TPU filament.json, taken from the shop's TPU project)."""
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
    """A Flash Studio project. plates: [(plate name, items), ...] in order; items: (object name,
    manifold, filament, (x, y) of its lower-left corner on that plate[, own settings]). It
    carries Flash Studio's project settings (AD5X 0.4, 0.20mm Standard, Arachne, counterbores
    partly bridged, filaments 1 white, 2 black, 3 brown, with any changes in settings) and its
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
            own = dict(own[0]) if own else {}
            mods = own.pop("modifier", [])             # [(name, manifold in man's own coordinates, its settings)]
            bb = man.bounding_box()
            mid = np.array([(bb[0] + bb[3]) / 2, (bb[1] + bb[4]) / 2, (bb[2] + bb[5]) / 2])
            parts = [(oid + i, nm, m_) for i, (nm, m_) in enumerate([(obj_name, man)] + [(nm, m_) for nm, m_, _ in mods])]
            for pid, nm, m_ in parts:
                mesh = m_.to_mesh()
                v = np.asarray(mesh.vert_properties)[:, :3] - mid
                tri = np.asarray(mesh.tri_verts)
                vs = "".join(f'<vertex x="{a:.4f}" y="{b:.4f}" z="{c:.4f}"/>' for a, b, c in v)
                ts = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tri)
                res.append(f'<object id="{pid}" name={quoteattr(nm)} type="model"><mesh>'
                           f'<vertices>{vs}</vertices><triangles>{ts}</triangles></mesh></object>')
            top = oid + len(parts)
            res.append(f'<object id="{top}" name={quoteattr(obj_name)} type="model"><components>'
                       + "".join(f'<component objectid="{pid}"/>' for pid, _, _ in parts) + '</components></object>')
            # a modifier part changes the settings where it is and prints nothing (as the shed models' bridge modifiers)
            cfg.append(f'<object id="{top}"><metadata key="name" value={quoteattr(obj_name)}/>'
                       f'<metadata key="extruder" value="{filament}"/>'
                       + "".join(f'<metadata key="{key}" value={quoteattr(v)}/>' for key, v in own.items())
                       + f'<part id="{oid}" subtype="normal_part"><metadata key="name" value={quoteattr(obj_name)}/>'
                       f'<metadata key="extruder" value="{filament}"/></part>'
                       + "".join(f'<part id="{oid + 1 + i}" subtype="modifier_part"><metadata key="name" value={quoteattr(nm)}/>'
                                 + "".join(f'<metadata key="{key}" value={quoteattr(v)}/>' for key, v in st.items()) + '</part>'
                                 for i, (nm, _, st) in enumerate(mods))
                       + '</object>')
            build.append(f'<item objectid="{top}" transform="1 0 0 0 1 0 0 0 1 '
                         f'{ox + x + mid[0] - bb[0]:.4f} {oy + y + mid[1] - bb[1]:.4f} {mid[2] - bb[2]:.4f}"/>')
            plate_cfg.append(f'<model_instance><metadata key="object_id" value="{top}"/>'
                             f'<metadata key="instance_id" value="0"/></model_instance>')
            oid = top + 1
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
        z.writestr("Metadata/project_settings.config", settings or project_settings())
        z.writestr("Metadata/model_settings.config",
                   '<?xml version="1.0" encoding="UTF-8"?>\n<config>' + "".join(cfg + plate_cfg) + '</config>')


def on_bed(man):
    bb = man.bounding_box()
    return man.translate([-bb[0], -bb[1], -bb[2]])


FLIP = np.array([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0]], dtype=float)


def latch_test():
    """Fit-test piece: the carrier round the latch block's slot and the whole arm, and the lug. The
    block prints on its inner face and stands 1.4 over the carrier; with the lug beside it its top
    layers print as slowly as on the knife's plate, where the blade's lug, the risers and the knob
    print beside them, not alone and fast (PRINTER-BRAIN: test a tall thin part on a plate like its
    real one)."""
    return carrier() ^ box(C0 + LUG_X0 - 0.5, C0 + 58.0, -CAR_W, CAR_W, CAR_Z0 - 1, LUG_TOP + 1)


TEST_X0, TEST_X1 = STEM_X0, STEM_X0 + 24.0     # the fit test's carriage piece: the carriage's back 24 mm, crowned end and all


def rib_test():
    """Fit-test piece: the rib the knob's carriage rides, cut from the base plate itself (so it follows any change to the
    rib), on a strip of the lane's floor; on the same layers as there: the floor's top at layer(5) here as it is at
    layer(21) there."""
    x0 = max(TEST_X0 - 2, knob_slot_x()[0] + 0.5)      # inside the knob's slot, clear of the side wall before it
    base = box(x0, TEST_X1 + 3, BAR_Y0 - 1.0, HW / 2 + 1.0, LANE_Z0 - layer(5), LANE_Z0)
    return base + (plate1() ^ box(x0, TEST_X1 + 3, RIB_Y0 - 0.3, HW / 2 + 0.3, LANE_Z0 - 0.01, ROOF_Z0))


def carriage_test():
    """Fit-test piece: the back 24 mm of the knob slider's carriage, bar, roof, knob's foot and knob, cut from the slider
    itself, so it prints as the slider does; its cut end crowned as the carriage's own ends are."""
    return (knob_bar() ^ box(TEST_X0 - 0.01, TEST_X1, BAR_Y0 - 5, 40, -1, 20)) - crowns([(TEST_X1, -1, 0.0)])


PEG_TEST = (PEGS[0][0] - 3.5, PEGS[0][0] + 4.5, PEGS[0][1] - 3.5, PEGS[0][1] + 3.5)   # the peg test's pieces, round the rear peg


def peg_test_corner():
    """The corner cut off both peg test pieces, on the knob's side (+y), the side the D-shaped hole's flat is on: put the lid
    on the base cut corner to cut corner."""
    x0, x1, y0, y1 = PEG_TEST
    return prism([(x1 - 1.5, y1 + 0.01), (x1 + 0.01, y1 + 0.01), (x1 + 0.01, y1 - 1.5)], Z1 - 3, Z1 + 3)


def peg_test_base():
    """Fit-test piece: the base plate's top 1.05 round its rear peg, cut from the base plate itself, so the peg prints on the
    same layers as there (its foot at layer(5) here, layer(35) there); the corner on the knob's side cut off, as the lid's."""
    x0, x1, y0, y1 = PEG_TEST
    return (plate1() ^ box(x0, x1, y0, y1, Z1 - layer(5), Z1 + PEG_H + 0.1)) - peg_test_corner()


def peg_test_lid():
    """Fit-test piece: the middle plate's bottom 2.05 round the D-shaped hole over that peg, cut from the middle plate
    itself (its first layer set back at the flat, as there); the corner on the flat's side cut off so you can tell it."""
    x0, x1, y0, y1 = PEG_TEST
    return (plate2() ^ box(x0, x1, y0, y1, Z1, Z1 + layer(10))) - peg_test_corner()


def roof_bridge(x0, x1):
    """A modifier over the carriage's roof's first layer, where it bridges the rib's channel 1.9 across: it sets the
    bridge's lines straight across the channel (Flash Studio's External bridge infill direction 90, along the bed's y, the
    slider lying along x), never left for the slicer to pick: Flash Studio can lay a bridge the long way (PRINTER-BRAIN)."""
    return box(x0 - 0.5, x1 + 0.5, LEG_Y1 - 0.3, KNOB_FOOT_Y0 + 0.3, ROOF_Z0 - 0.1, ROOF_Z0 + 0.25)


ROOF_BRIDGE = {"bridge_angle": "90"}


def bed_shift(man):
    """What on_bed moves man by."""
    bb = man.bounding_box()
    return [-bb[0], -bb[1], -bb[2]]


ON_INNER_FACE = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0]], dtype=float)   # y-min face down
ON_FRONT_FACE = np.array([[0, 0, -1, 0], [0, 1, 0, 0], [1, 0, 0, 0]], dtype=float)   # x-min face down


def print_parts():
    """Every part turned the way it prints, sitting on the bed."""
    return {
        "handle 1 base": on_bed(plate1()),
        "handle 2 middle": on_bed(plate2()),
        "handle 3 top": on_bed(plate3().transform(FLIP)),
        "handle 3 top loose": on_bed(plate3(LOOSE_PLAY).transform(FLIP)),
        "blade": on_bed(carrier()),
        "latch block": on_bed(latch_block().transform(ON_INNER_FACE)),
        "rail": on_bed(rail()),
        "knob slider": on_bed(knob_bar()),
        "riser cap": on_bed(riser_cap("F").transform(ON_FRONT_FACE)),     # the face a wing meets, down
        "knob stop rear": on_bed(knob_stop("R")),                         # on its foot, its T on the bed too
        "knob stop front": on_bed(knob_stop("F")),                        # the rear one's mirror image
        "sled F": on_bed(sled(0.0, "F")),
        "sled B": on_bed(sled(0.0, "B")),
        "screw": on_bed(screw()),
        "nut": on_bed(nut(z0=0.0)),
        "band": on_bed(band_print(BAND)),
        "band strong": on_bed(band_print(BAND_STRONG)),
        "band soft": on_bed(band_print(BAND_SOFT)),
        "pad": on_bed(pad(0.0)),
        "rail cushion": on_bed(cushion("R")),
        "rib test": on_bed(rib_test()),
        "peg test base": on_bed(peg_test_base()),
        "peg test lid": on_bed(peg_test_lid()),
        "carriage test": on_bed(carriage_test()),
    }


def fit_nuts():
    """The fit test's three gauge nuts as they print: nut 1 (one corner cut off) a little tighter
    than the top plate's posts, nut 2 (two corners) the same, nut 3 (three corners) as the loose
    top plate."""
    return [(f"nut {i + 1} corner" + ("s" if i else ""), on_bed(nut(play=play, corners=i + 1, z0=0.0)))
            for i, play in enumerate(FIT_PLAYS)]


def projects(p):
    """The three Flash Studio projects: [(file name, plates, settings)], plates as write_3mf takes
    them. p: print_parts()."""
    strong = project_settings({1: STRONG_PLA, 2: STRONG_PLA}, process=STRONG_PROCESS)
    # fit test: the knife's four screws and the three gauge nuts; and the latch: the carrier round
    # its arm, slot and lug, with the block. Everything printed the way the knife's own parts print.
    fit = [(f"screw {i + 1}", p["screw"], 2, (20 + 16 * i, 90), SOLID) for i in range(4)]
    fit += [(name, man, 2, (90 + 16 * i, 90), THREADS) for i, (name, man) in enumerate(fit_nuts())]
    # and the knob's carriage on its rib: drop the carriage piece over the rib piece and slide it along. The rib piece prints
    # as the base plate does (its own settings), the carriage piece as the knob slider does, in white with no brim
    fit += [("rib test", p["rib test"], 2, (40, 135), BRIM)]
    # and the plates' D-shaped peg holes: press the piece with the hole onto the piece with the peg, cut corner to cut corner
    fit += [("peg test base", p["peg test base"], 2, (120, 135), BRIM), ("peg test lid", p["peg test lid"], 2, (150, 135), BRIM)]
    lt = on_bed(latch_test())
    latch = [("latch test", lt, 1, (80, 90), MOVING),
             ("latch block", p["latch block"], 1, (135, 90), {**MOVING, "brim_type": "no_brim"}),
             ("carriage test", p["carriage test"], 1, (80, 140),
              {**MOVING, **NO_BRIM, "modifier": [("roof bridge", roof_bridge(TEST_X0, TEST_X1).translate(bed_shift(carriage_test())),
                                                   ROOF_BRIDGE)]})]
    x0 = (220 - HL) / 2
    handle_items, y = [], 20.0
    for name, own in (("handle 1 base", BRIM), ("handle 2 middle", BRIM), ("handle 3 top", {**BRIM, **LID})):
        handle_items.append((name, p[name], 2, (x0, y), own))
        bb = p[name].bounding_box()
        y += (bb[4] - bb[1]) + 12                           # 43.2 wide with the guards: 12 apart round two 5 mm brims
    small = [("sled F", p["sled F"], 2, (20, 20), MOVING), ("sled B", p["sled B"], 2, (60, 20), MOVING),
             ("rail", p["rail"], 2, (20, 70), {**MOVING, **BRIM})]
    bl, kb = p["blade"], p["knob slider"]
    mid_x = lambda man: (220 - man.bounding_box()[3]) / 2
    seam = {"seam_position": "back", **TPU_SOLID}    # on top of an eye ring, not where the strand meets it
    # each band plate has the band and two spares of the same kind, 12 apart: a worn band is a two-minute swap
    bands = lambda name: [(name + suffix, p[name], 1, (mid_x(p[name]), y), seam)
                          for suffix, y in (("", 70), (" spare 1", 82), (" spare 2", 94))]
    tpu = bands("band") + [
           ("pad 1", p["pad"], 1, (60, 120), TPU_SOLID), ("pad 2", p["pad"], 1, (80, 120), TPU_SOLID),
           ("rail cushion 1", p["rail cushion"], 1, (110, 120), TPU_SOLID),
           ("rail cushion 2", p["rail cushion"], 1, (130, 120), TPU_SOLID),
           ("riser cap 1", p["riser cap"], 1, (60, 140), TPU_SOLID),
           ("riser cap 2", p["riser cap"], 1, (75, 140), TPU_SOLID),
           ("knob stop rear", p["knob stop rear"], 1, (95, 140), TPU_SOLID),
           ("knob stop front", p["knob stop front"], 1, (112, 140), TPU_SOLID)]
    return [
        ("1 fit test.3mf", [("screws, gauge nuts and the knob's rib test (black)", fit),
                            ("latch test and the knob's carriage test (white)", latch)], strong),
        ("2 knife plates.3mf", [
            ("handle (black)", handle_items),
            ("sleds and rail (black)", small),
            ("blade and latch block (white)", [
                ("blade", bl, 1, (mid_x(bl), 40), MOVING),
                ("latch block", p["latch block"], 1, (20, 85), {**MOVING, "brim_type": "no_brim"})]),
            # the knob slider on a plate of its own: beside the blade its long knob would slow the latch block's top layers
            # to 9.7 s, and the fit test's block would no longer print as the knife's does
            ("knob slider (white)", [("knob slider", kb, 1, (mid_x(kb), 110),
                                      {**MOVING, **NO_BRIM, "modifier": [("roof bridge", roof_bridge(STEM_X0, STEM_X1)
                                                                          .translate(bed_shift(knob_bar())), ROOF_BRIDGE)]})])],
         strong),
        # the strong and the soft bands each on a plate of their own, so printing a plate prints only the bands it names
        ("3 TPU parts.3mf", [
            ("TPU parts", tpu),
            (f"strong bands (the hang test stretched the band {HANG_STRONG:g} mm or more)", bands("band strong")),
            (f"soft bands (the hang test stretched the band {HANG_SOFT:g} mm or less)", bands("band soft"))],
         project_settings(tpu_filament=1)),
    ]


def main():
    p = print_parts()
    for name, man in p.items():
        write_stl(man, name + ".stl")
    for gone in ("nut loose.stl", "bumper.stl", "knob stop.stl"):   # replaced by handle 3 top loose.stl, the knob stops, and
    #                                                                 the rear and front knob stops
        if os.path.exists(os.path.join(HERE, gone)):
            os.remove(os.path.join(HERE, gone))
    for name, plates, settings in projects(p):
        write_3mf(name, plates, settings)
    for name, man in p.items():
        bb = man.bounding_box()
        print(f"{name:18s} {bb[3]-bb[0]:6.1f} x {bb[4]-bb[1]:6.1f} x {bb[5]-bb[2]:5.2f} mm  {man.volume()/1000:5.2f} cm3")


if __name__ == "__main__":
    main()
