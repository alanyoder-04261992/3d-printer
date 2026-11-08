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
    out by a springy arm. Its load goes into the carrier, never the arm. It catches on a short
    catch at each end of a PLA rail in the base plate, and floats out against the knob bar in
    between. The rail sits between two TPU cushions, which take the knock when the blade
    bounces back off its pad.
  * Each riser wears a TPU cap where the sled lands on it, so no knock is plastic on plastic.
  * The screws thread into posts printed on the top plate, so they clamp all three plates.

Parts (print files in this folder)
  handle 1 base.stl, handle 2 middle.stl, handle 3 top.stl   three plates, four screws
  blade.stl          blade and carrier with the lug and the latch arm
  latch block.stl    rail.stl    sled F.stl    sled B.stl
  knob slider.stl    the bar with its two cams, two risers and the knob
  screw.stl (4), nut.stl (a thread gauge), handle 3 top loose.stl (if the fit test says so)
  band.stl, pad.stl (2), rail cushion.stl (2), riser cap.stl (2)   TPU; band strong.stl for a soft
                     TPU, band soft.stl for a stiff one
  1 fit test.3mf        the four screws and three gauge nuts, and a latch test piece: find the thread fit
                        and try the latch first
  2 knife plates.3mf    Flash Studio project: handle and small parts (black), blade, knob slider and
                        latch block (white)
  3 TPU parts.3mf       band, pads, cushions and riser caps, set up for TPU

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
BLK_X0, BLK_L, BLK_D = 22.5, 3.6, layer(27)   # 3.6 long, so it can't go in on its side; 5.45 deep, so it sits
                                        # 2.95 into its slot when out and can't lean past its chamfers.
                                        # It prints lying on its inner face, so its first layer is there.
BLK_Z0, BLK_Z1 = CAR_Z0 - 0.1, CAR_Z1 + 0.1   # 4.45 tall: 0.175 off the channel floor and the middle plate
BLK_CHAMFER = 0.6                   # on all four upright edges: either way round, the trailing corner can't catch
BLK_SLOT = 0.25                     # play each side of the block in its slot
FOOT = 0.15                         # first layers set back this far where a part slides on a first layer
X_BLK = C0 + BLK_X0                 # 44.5: block's back face, closed
ARM_ROOT = 54.0                     # the arm's root on the carrier (x)
ARM_Y0, ARM_T = 4.8, 0.9            # the arm, as printed (free)
ARM_GAP = 0.5                       # the gaps round the arm: inside one print, so wider than a sliding fit
ARM_RELIEF = 0.5                    # radius of the round ends of those gaps at the arm's root
NOSE_C, NOSE_HW = BLK_X0 + BLK_L / 2, 0.8     # the arm's nose: 1.6 wide, under the middle of the block
PRELOAD = 0.5                       # the arm still pushes 0.5 when the block is out
# block's outer face (y): out in a window it rests on the knob bar; on the rail; pushed by a cam
Y_OUT, Y_RAIL, Y_CAM = 13.45, CHAN_Y, 11.05
NOSE_TOP = Y_OUT - BLK_D + PRELOAD  # 8.5: the arm's nose reaches here when free

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
SEG_RAMP_Y = 13.9
RAMP_L = (SEG_RAMP_Y - RAIL_Y0) / math.tan(math.radians(SEG_RAMP))   # 6.44
TAPER_L = 8.0                       # ... then a long taper into the spine, so the catch has no square step
SEG_L = SEG_FLAT + RAMP_L + TAPER_L
WIN_Y1 = Y_OUT + 0.15               # the block's path (windows and between the catches) is cut out to here
SPINE_Y0 = WIN_Y1 + 1.05            # 14.65: 0.8 of base plate between its groove and the path
SPINE_Y1 = SPINE_Y0 + 1.6           # 16.25
GROOVE_Y0, GROOVE_Y1 = SPINE_Y0 - 0.25, SPINE_Y1 + 0.25   # an easy sliding fit
SPINE_WIDEN = 0.4                   # the spine is 2.0 wide between the catches, 1.6 at its ends
SPINE_X0, SPINE_X1 = RAIL_X0 - 3.0, RAIL_X1 + 3.0  # the spine runs 3 mm past each catch ...
CUSH_L, CUSH_HELD = 12.0, 4.0       # ... to a TPU cushion at each end, its outer 4 mm pressed into a narrow end
CUSH_TOP = RAIL_Z0 + layer(14)      # 3.90
CUSH_GRIP = 0.05                    # how much narrower the groove's ends are than a cushion, each side
W_FAR = 5.0                         # far end of each window: past the block's overrun
RAIL_MOVE = 4.0                     # the rail can move this far each way in its groove

# knob bar: in a lane beside the channel, above the rail
BAR_Y0, BAR_Y1 = Y_OUT, 16.8
LANE_Y1 = 17.05
BAR_Z0 = LANE_Z0 + 0.2              # 4.45 (bar prints on this face)
BAR_Z1 = BAR_Z0 + layer(11)         # 6.70
RISER_Y1 = 15.8                     # the risers are narrower than the bar: the middle plate's floor
RISER_SLOT_Y0, RISER_SLOT_Y1 = BAR_Y0 - 0.3, RISER_Y1 + 0.3   # keeps a ledge over the bar's outer 0.4
THROW = 28.0                        # knob travel
SOFT = 0.3                          # the knob can go this far past each end before a sled meets its pad
KNOB_ROOM = 5.0                     # and this much further before anything but TPU stops it
G_P = 0.3                           # a parked sled sits this far from the lug
RISER_L = 12.7                      # each riser, from its face (the TPU cap's face) to its far end
RISER_TOP = BAR_Z0 + layer(26)      # 9.70
CAP_T, TONGUE_L, TONGUE_W = 2.5, 2.4, 0.8   # TPU cap: 2.5 in front of a 0.8 wide PLA tongue it is pressed onto
CAP_TOP = BAR_Z1 + layer(15)       # 9.75, 0.35 under the top plate
CAP_L = CAP_T + TONGUE_L
CAM_ANGLE = 20.0
RAMP = (Y_OUT - Y_CAM) / math.tan(math.radians(CAM_ANGLE))   # 6.59: 20 degree cam ramps
CAM_FLAT = 2.0
C_TRIP = E_CATCH + 0.6              # the blade creeps this far while cocked: to the rail, then into its cushions
C_COCK = C_TRIP + 0.9               # and never more than this
STEM_X0, STEM_X1 = 84.0, 98.0
KNOB_Y0 = HW / 2 + 0.7              # 0.7 clear of the handle's side
KNOB_TOP = BAR_Z0 + layer(37)       # 11.90
LIP = 1.5                           # the knob's two end lips stand this far proud: they keep the thumb on

# band level: two sleds, one band, two pads
SLED_H = layer(10)                  # 2.05
SLED_Z0, SLED_Z1 = Z_FLOOR, Z_FLOOR + SLED_H   # 7.70 to 9.75
SLED_LEN, SLED_HW, WING_L = 22.0, 7.0, 14.0    # long, so a riser pushing its wing can't twist it much
POST_D, EYE_PLAY = 3.0, 0.4
POST_BACK = 10.5                    # the band's post is this far from the sled's lug face
POCKET_Z = SLED_Z0 + layer(4)       # 8.55 the band sits on this: 0.85 of floor under the post
CAV_Y0, CAV_Y1 = -SLED_HW - 0.3, RISER_Y1 + 0.3  # band level cavity
R_B = LUG_L + TRAVEL + G_P - THROW  # 66.3: sled B's lug face from the lug's back face (closed), knob back
PAD_L, PAD_HW, PAD_IN = 9.5, 2.5, 4.0          # TPU pads 9.5 x 5, the back 4.0 pressed into a pocket
PAD_X0 = X_L0 - G_P - SOFT - SLED_LEN - PAD_L  # 2.9: rear pad, sled F's soft stop
PAD_X1 = X_L0 + R_B + THROW + SOFT + SLED_LEN + PAD_L   # 159.1: front pad, sled B's soft stop
BAND = (layer(5), 0.95, 1.3)        # height, strand width, eye ring width
BAND_STRONG = (layer(6), 1.3, 1.8)   # for a soft TPU
BAND_SOFT = (layer(4), 0.95, 1.3)    # for a stiff TPU
BAND_W = BAND[0]
BAND_FILLET = 1.0                   # where the strand meets each eye
EYE_D = POST_D + 2 * EYE_PLAY + 2 * BAND_STRONG[2] + 0.6   # 8.0 the eye's pocket in each sled
BAND_PRELOAD = 5.0
BAND_RELAXED = R_B + G_P + 2 * POST_BACK - BAND_PRELOAD  # 82.6 eye to eye: taut by 5 mm when parked

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
BOSS_AF = 8.5                       # the top plate's four threaded posts ...
BOSS_Z0 = HT - layer(25)            # ... reach down to 7.30, 0.25 short of the base plate, so they clamp through
THREAD_TOP = HT - layer(3)          # their thread stops at 11.70, under 0.65 of top skin
NUT_POCKET_AF = 9.0                 # the posts stand in these pockets through the middle plate
NUT_AF, NUT_H = 8.6, layer(21)      # the fit test's gauge nuts, 4.25 thick
PEGS = [(14.0, -15.0), (164.0, -15.0)]
PEG_D, PEG_H, PEG_HOLE_D = 3.0, 1.0, 3.8      # 0.4 all round (holes print small)
PEG_HOLE_H2, PEG_HOLE_H3 = layer(6), 1.20     # in the middle plate (from its bottom) and the top plate (from its top)

FINGERS = [60.0, 84.0, 108.0]
FINGER_R, FINGER_DEPTH = 9.0, 1.6

# print settings (PRINTER-BRAIN, strong parts): hotter, less fan, slower walls, solid
STRONG_PLA = {"nozzle_temperature": "230", "nozzle_temperature_initial_layer": "230", "fan_min_speed": "45",
              "fan_max_speed": "45", "additional_cooling_fan_speed": "0", "filament_flow_ratio": "1.02"}
STRONG_PROCESS = {"default_acceleration": "3000", "outer_wall_acceleration": "3000",
                  "inner_wall_acceleration": "3000", "internal_solid_infill_acceleration": "3000"}
SOLID = {"wall_loops": "6", "sparse_infill_density": "100%"}                       # printed screws
THREADS = {**SOLID, "outer_wall_speed": "40", "inner_wall_speed": "40"}            # gauge nuts print like ...
LID = {"wall_loops": "4", "outer_wall_speed": "40", "inner_wall_speed": "40"}      # ... the top plate's posts
MOVING = {"wall_loops": "4", "sparse_infill_density": "100%", "outer_wall_speed": "60", "inner_wall_speed": "60",
          "internal_solid_infill_speed": "60", "top_surface_speed": "60", "gap_infill_speed": "60"}  # parts that take knocks
BRIM = {"brim_type": "outer_only", "brim_width": "5"}                              # long thin parts (PRINTER-BRAIN)


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


def nut(x=0.0, y=0.0, play=THREAD_PLAY, notches=0, z0=BOSS_Z0):
    """A gauge nut for the fit test: the top plate's post thread, in a nut. notches marks it."""
    z1 = z0 + NUT_H
    body = extrude(hexagon(NUT_AF).translate([x, y]), z0, z1)
    hole = thread(x, y, z0 - 0.5, z1 + 0.5, THREAD_MIN / 2 + play, THREAD_MAJ / 2 + play, GROOVE_WIDEN)
    cuts = [hole]
    r_flat = NUT_AF / 2
    for i in range(notches):
        cuts.append(box(x + r_flat - 0.5, x + r_flat + 1, y - 2.0 + 1.6 * i, y - 1.2 + 1.6 * i, z0 - 1, z1 + 1))
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
    return union([cyl_z(x, y, z, z + PEG_H, PEG_D) for x, y in PEGS])


def peg_holes(z, depth):
    return union([cyl_z(x, y, z - 0.01, z + depth, PEG_HOLE_D) for x, y in PEGS])


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
    return STEM_X0 - SOFT - KNOB_ROOM - 0.3, STEM_X1 + THROW + SOFT + KNOB_ROOM + 0.3


def lane_x():
    return bar_x(-SOFT - KNOB_ROOM)[0] - 0.3, bar_x(THROW + SOFT + KNOB_ROOM)[1] + 0.3


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
    rail's groove and its cushions' pocket, the knob bar's lane and the knob's slot."""
    p = slab(0, Z1, chamfer_bottom=True)
    lx0, lx1 = lane_x()
    kx0, kx1 = knob_slot_x()
    cuts = [box(REAR_IN, FRONT_IN, -CHAN_Y, CHAN_Y, WALL_T, Z1 + 1),                  # channel
            box(FRONT_IN - 1, HL + 1, -SLOT_Y, SLOT_Y, WALL_T, Z1 + 1),               # blade slot
            box(lx0, lx1, Y_CAM - 0.25, LANE_Y1, LANE_Z0, Z1 + 1),                     # cams' and bar's lane
            box(kx0, kx1, LANE_Y1 - 0.1, HW / 2 + 1, LANE_Z0, Z1 + 1),                 # knob slot
            rail_groove(), front_screw_joins()]
    cuts += [box(w0, w1, CHAN_Y - 0.01, WIN_Y1, WALL_T, RAIL_TOP + 1) for w0, w1 in windows()]
    cuts += [cyl_z(x, y, -1, HEAD_H, COUNTERBORE, 64) for x, y in SCREWS]
    p = p - union(cuts) - screw_holes(0, Z1)
    return p + pegs(Z1)


def lug_slot_x():
    return X_L0 - OVERRUN - 0.3, X_L0 + LUG_L + TRAVEL + OVERRUN + 0.3


def riser_sweep(x0, x1):
    """The risers' slots run 0.3 further than the lane, so at the very end of the knob's room
    the bar's own end meets the lane's end, square on, before a riser meets anything."""
    return x0 - SOFT - KNOB_ROOM - 0.6, x1 + THROW + SOFT + KNOB_ROOM + 0.6


def riser_x():
    """(x0, x1) of riser F and riser B on the bar at s = 0."""
    f = (X_L0 - G_P, X_L0 - G_P + RISER_L)
    b = (X_L0 + R_B - RISER_L, X_L0 + R_B)
    return f, b


def wing_room_x():
    """x range of the band level's wide part, where the sleds' wings go."""
    return X_L0 - G_P - SOFT - KNOB_ROOM - WING_L - 0.3, X_L0 + R_B + THROW + SOFT + KNOB_ROOM + WING_L + 0.3


def plate2():
    """Middle plate: the floor over the channel (with the lug's slot and the risers' slots),
    and the band level above it, open at the top, where the sleds, the band and the pads go.
    The top plate's threaded posts stand in pockets right through it. Prints with its bottom
    face on the bed, so nothing bridges."""
    p = slab(Z1, Z2)
    (f0, f1), (b0, b1) = riser_x()
    wx0, wx1 = wing_room_x()
    pad_y = PAD_HW - 0.1                                     # the pads are pressed in
    cuts = [box(*lug_slot_x(), -LUG_HW - 0.7, LUG_HW + 0.7, Z1 - 1, Z_FLOOR + 1),
            box(*riser_sweep(f0, f1), RISER_SLOT_Y0, RISER_SLOT_Y1, Z1 - 1, Z_FLOOR + 1),
            box(*riser_sweep(b0, b1), RISER_SLOT_Y0, RISER_SLOT_Y1, Z1 - 1, Z_FLOOR + 1),   # a web between the two
            # band level: the sleds' bodies, their wings, and the pads' pockets at the two ends
            box(PAD_X0 + PAD_IN, PAD_X1 - PAD_IN, CAV_Y0, -CAV_Y0, Z_FLOOR, Z2 + 1),
            box(wx0, wx1, CAV_Y0, CAV_Y1, Z_FLOOR, Z2 + 1),
            box(PAD_X0, PAD_X0 + PAD_IN + 0.01, -pad_y, pad_y, Z_FLOOR, Z2 + 1),
            box(PAD_X1 - PAD_IN - 0.01, PAD_X1, -pad_y, pad_y, Z_FLOOR, Z2 + 1),
            peg_holes(Z1, PEG_HOLE_H2), screw_holes(Z1, Z2)]
    cuts += [extrude(hexagon(NUT_POCKET_AF).translate([x, y]), Z1 - 1, Z2 + 1) for x, y in SCREWS]
    p = p - union(cuts)
    return p + pegs(Z2)


def plate3(play=THREAD_PLAY):
    """Top plate: the lid over the band level, with a threaded post at each screw that reaches
    down through the middle plate. Prints top face down, so the posts stand up from it."""
    p = slab(Z2, HT, chamfer_top=True)
    posts = union([extrude(hexagon(BOSS_AF).translate([x, y]), BOSS_Z0, Z2 + 0.01) for x, y in SCREWS])
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


def arm_dy(x, deflect):
    """How far the arm's centre line has moved toward -y at x, bent deflect at the nose: a
    cantilever's curve to the nose, and straight on (at the nose's slope) past it."""
    L = arm_L()
    xi = (ARM_ROOT - x) / L
    if xi <= 0:
        return 0.0
    if xi <= 1:
        return deflect * xi * xi * (3 - xi) / 2
    return deflect * (1 + 1.5 * (xi - 1))


def arm_slope(deflect):
    return 1.5 * deflect / arm_L()


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
    deflect_max = arm_deflect_for(Y_CAM) + 0.1
    top_gap = ARM_Y0 + ARM_T + ARM_GAP
    cuts = [
        prism(arm_gap_poly(deflect_max), z0 - 1, z1 + 1),                                   # room to bend
        box(BLK_X0 - 0.3, ARM_ROOT, ARM_Y0 - 0.01, top_gap, z0 - 1, z1 + 1),               # the arm, and the gap over it
        cyl_z(ARM_ROOT, ARM_Y0 + ARM_T + ARM_RELIEF, z0 - 1, z1 + 1, 2 * ARM_RELIEF, 32),  # round ends at the root
        cyl_z(ARM_ROOT, ARM_Y0 - ARM_RELIEF, z0 - 1, z1 + 1, 2 * ARM_RELIEF, 32),
        box(BLK_X0 - BLK_SLOT, BLK_X0 + BLK_L + BLK_SLOT, ARM_Y0 + ARM_T, CAR_W / 2 + 1, z0 - 1, z1 + 1),  # block slot
        box(BLK_X0 - BLK_SLOT - FOOT, BLK_X0 + BLK_L + BLK_SLOT + FOOT, ARM_Y0 + ARM_T, CAR_W / 2 + 1,
            z0 - 1, z0 + layer(1)),                                                          # its first layer set back
        box(-1, CAR_L + 1, CAR_CUT_Y, CAR_W / 2 + 1, CAR_CUT_Z, z1 + 1),                    # room for the cams
        extrude(m3.CrossSection.square([GROOVE_X1 - GROOVE_X0, 2.6]).translate([GROOVE_X0, 1.6])
                .offset(0.6, m3.JoinType.Round, 2.0, 16), z1 - GROOVE_D, z1 + 1),
    ]
    body = body - union(cuts)
    # the arm, bent if asked, and its nose turned with it
    x_tip = NOSE_C - NOSE_HW
    top, bot = [], []
    for i in range(0, 41):
        x = ARM_ROOT - i / 40 * (ARM_ROOT - x_tip)
        dy = arm_dy(x, arm_deflect)
        top.append((x, ARM_Y0 + ARM_T - dy))
        bot.append((x, ARM_Y0 - dy))
    arm = prism(top + list(reversed(bot)), z0, z1)
    nose = prism(nose_poly(arm_deflect), z0, z1)
    root = box(ARM_ROOT - 0.01, ARM_ROOT + ARM_RELIEF + 0.5, ARM_Y0, ARM_Y0 + ARM_T, z0, z1)
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


CAM_A_TOP = X_BLK + C_TRIP - (THROW - 1)           # cam A's top at s = 0: it reaches the block's back corner at s = 27
CAM_B_TOP = X_BLK + TRAVEL - C_TRIP + BLK_L - 1    # cam B's top at s = 0: it reaches the block's front corner at s = 1


def knob_bar(s=0.0):
    """Bar with cam A, cam B, riser F, riser B, the stem and the knob, at knob travel s. Each
    riser ends in a tongue that its TPU cap presses onto; the cap's face is the riser's face."""
    x0, x1 = bar_x(0)
    z0, z1 = BAR_Z0, BAR_Z1
    parts = [box(x0, x1, BAR_Y0, BAR_Y1, z0, z1),
             cam(CAM_A_TOP, True, z0, z1), cam(CAM_B_TOP, False, z0, z1)]
    (f0, f1), (b0, b1) = riser_x()
    ty0 = (BAR_Y0 + RISER_Y1) / 2 - TONGUE_W / 2
    parts += [box(f0 + CAP_L, f1, BAR_Y0, RISER_Y1, z1 - 0.01, RISER_TOP),
              box(f0 + CAP_T + 0.1, f0 + CAP_L + 0.01, ty0, ty0 + TONGUE_W, z1 - 0.01, RISER_TOP),
              box(b0, b1 - CAP_L, BAR_Y0, RISER_Y1, z1 - 0.01, RISER_TOP),
              box(b1 - CAP_L - 0.01, b1 - CAP_T - 0.1, ty0, ty0 + TONGUE_W, z1 - 0.01, RISER_TOP)]
    parts += [box(STEM_X0, STEM_X1, BAR_Y1 - 0.01, KNOB_Y0 + 0.1, z0, z1 - 0.2)]
    k_out = KNOB_Y0 + 3.0
    knob = box(STEM_X0, STEM_X1, KNOB_Y0, k_out, z0, KNOB_TOP)
    lips = box(STEM_X0, STEM_X0 + 2.0, k_out - 0.01, k_out + LIP, z0, KNOB_TOP) + \
        box(STEM_X1 - 2.0, STEM_X1, k_out - 0.01, k_out + LIP, z0, KNOB_TOP)
    ridges = union([box(STEM_X0 + 4.0 + 2.5 * i, STEM_X0 + 5.0 + 2.5 * i, k_out - 0.5, k_out + 1, z0 - 1, KNOB_TOP + 1)
                    for i in range(3)])
    parts.append(knob - ridges + lips)
    return union(parts).translate([s, 0, 0])


def riser_cap(which, s=0.0):
    """The TPU cap on riser F ('F', on its back face) or riser B ('B', on its front face): a U
    pressed down over the riser's tongue, standing on the bar."""
    (f0, f1), (b0, b1) = riser_x()
    x0 = f0 if which == "F" else b1 - CAP_L
    ty0 = (BAR_Y0 + RISER_Y1) / 2 - TONGUE_W / 2
    cap = box(x0, x0 + CAP_L, BAR_Y0, RISER_Y1, BAR_Z1, CAP_TOP)
    sx0, sx1 = (x0 + CAP_T, x0 + CAP_L + 1) if which == "F" else (x0 - 1, x0 + TONGUE_L)
    slot = box(sx0, sx1, ty0 + 0.025, ty0 + TONGUE_W - 0.025, BAR_Z1 - 1, CAP_TOP + 1)   # grips the tongue
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
        z.writestr("Metadata/project_settings.config", settings or project_settings())
        z.writestr("Metadata/model_settings.config",
                   '<?xml version="1.0" encoding="UTF-8"?>\n<config>' + "".join(cfg + plate_cfg) + '</config>')


def on_bed(man):
    bb = man.bounding_box()
    return man.translate([-bb[0], -bb[1], -bb[2]])


FLIP = np.array([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0]], dtype=float)


def latch_test():
    """Fit-test piece: the carrier round the latch block's slot and the whole arm."""
    return carrier() ^ box(C0 + 20.5, C0 + 58.0, -CAR_W, CAR_W, CAR_Z0 - 1, CAR_Z1 + 1)


ON_INNER_FACE = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0]], dtype=float)   # y-min face down


def print_parts():
    """Every part turned the way it prints, sitting on the bed."""
    return {
        "handle 1 base": on_bed(plate1()),
        "handle 2 middle": on_bed(plate2()),
        "handle 3 top": on_bed(plate3().transform(FLIP)),
        "handle 3 top loose": on_bed(plate3(THREAD_PLAY + 0.05).transform(FLIP)),
        "blade": on_bed(carrier()),
        "latch block": on_bed(latch_block().transform(ON_INNER_FACE)),
        "rail": on_bed(rail()),
        "knob slider": on_bed(knob_bar()),
        "riser cap": on_bed(riser_cap("F")),
        "sled F": on_bed(sled(0.0, "F")),
        "sled B": on_bed(sled(0.0, "B")),
        "screw": on_bed(screw()),
        "nut": on_bed(nut(z0=0.0)),
        "band": on_bed(band_print(BAND)),
        "band strong": on_bed(band_print(BAND_STRONG)),
        "band soft": on_bed(band_print(BAND_SOFT)),
        "pad": on_bed(pad(0.0)),
        "rail cushion": on_bed(cushion("R")),
    }


def main():
    p = print_parts()
    for name, man in p.items():
        write_stl(man, name + ".stl")
    if os.path.exists(os.path.join(HERE, "nut loose.stl")):
        os.remove(os.path.join(HERE, "nut loose.stl"))           # replaced by handle 3 top loose.stl
    strong = project_settings({1: STRONG_PLA, 2: STRONG_PLA}, process=STRONG_PROCESS)
    # fit test: the knife's four screws and three gauge nuts, a little tighter (1 notch), as the
    # top plate's posts (2) and looser (3); and the latch: the carrier round its arm and slot,
    # with the block. Everything printed the way the knife's own parts print.
    fit = [(f"screw {i + 1}", p["screw"], 2, (20 + 16 * i, 90), SOLID) for i in range(4)]
    for i, play in enumerate((THREAD_PLAY - 0.05, THREAD_PLAY, THREAD_PLAY + 0.05)):
        fit.append((f"nut {i + 1} notch", on_bed(nut(play=play, notches=i + 1, z0=0.0)), 2, (90 + 16 * i, 90), THREADS))
    lt = on_bed(latch_test())
    latch = [("latch test", lt, 1, (80, 90), MOVING),
             ("latch block", p["latch block"], 1, (130, 90), {**MOVING, "brim_type": "no_brim"})]
    write_3mf("1 fit test.3mf", [("screws and gauge nuts (black)", fit), ("latch test (white)", latch)], strong)
    x0 = (220 - HL) / 2
    handle_items, y = [], 20.0
    for name, own in (("handle 1 base", BRIM), ("handle 2 middle", BRIM), ("handle 3 top", {**BRIM, **LID})):
        handle_items.append((name, p[name], 2, (x0, y), own))
        y += HW + 12
    small = [("sled F", p["sled F"], 2, (20, 20), MOVING), ("sled B", p["sled B"], 2, (60, 20), MOVING),
             ("rail", p["rail"], 2, (20, 70), {**MOVING, **BRIM})]
    bl, kb = p["blade"], p["knob slider"]
    write_3mf("2 knife plates.3mf", [
        ("handle (black)", handle_items),
        ("sleds and rail (black)", small),
        ("blade, knob slider and latch block (white)", [
            ("blade", bl, 1, ((220 - bl.bounding_box()[3]) / 2, 40), MOVING),
            ("knob slider", kb, 1, ((220 - kb.bounding_box()[3]) / 2, 110), {**MOVING, **BRIM}),
            ("latch block", p["latch block"], 1, (20, 85), {**MOVING, "brim_type": "no_brim"})]),
    ], strong)
    bp = p["band"]
    seam = {"seam_position": "back"}            # on top of an eye ring, not where the strand meets it
    write_3mf("3 TPU parts.3mf", [
        ("TPU parts", [("band", bp, 1, ((220 - bp.bounding_box()[3]) / 2, 70), seam),
                       ("pad 1", p["pad"], 1, (60, 120)), ("pad 2", p["pad"], 1, (80, 120)),
                       ("rail cushion 1", p["rail cushion"], 1, (110, 120)),
                       ("rail cushion 2", p["rail cushion"], 1, (130, 120)),
                       ("riser cap 1", p["riser cap"], 1, (60, 140)), ("riser cap 2", p["riser cap"], 1, (75, 140))]),
        ("other bands (print one only if the read me says so)",
         [("band strong", p["band strong"], 1, (40, 70), seam), ("band soft", p["band soft"], 1, (40, 120), seam)]),
    ], project_settings(tpu_filament=1))
    for name, man in p.items():
        bb = man.bounding_box()
        print(f"{name:18s} {bb[3]-bb[0]:6.1f} x {bb[4]-bb[1]:6.1f} x {bb[5]-bb[2]:5.2f} mm  {man.volume()/1000:5.2f} cm3")


if __name__ == "__main__":
    main()
