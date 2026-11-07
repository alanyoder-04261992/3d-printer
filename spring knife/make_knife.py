"""Spring knife toy for the Flashforge AD5X, designed from scratch.

Run:  python3 make_knife.py      (needs: pip install manifold3d numpy)

A blunt plastic fidget toy. Press the rear button on the side and two printed TPU bands
pull the blade out until it locks open. Press the front button and push the blade back
in until it clicks shut, which also stretches the bands for the next go.

Makes the print files in this folder:
  handle bottom.stl   lower half of the handle, inside up
  handle top.stl      upper half with the two buttons, printed inside up (outside on the bed)
  blade.stl           blade and the carrier it slides on, with the latch arm
  pin.stl             the pin through the carrier that both bands hook onto
  roller.stl          print TWO; each spins on a post at the front of the handle
  band.stl            print TWO in TPU (band firm.stl is a stronger pair)
  1 knife plates.3mf    Flash Studio project: plate 1 handle, pin, rollers (black),
                        plate 2 blade (white)
  2 bands (TPU).3mf     the two bands; pick your TPU filament before slicing

Axes for the assembled knife: x along the knife (blade comes out at +x), y across it
(buttons on +y), z through it. z = 0 is the outside of the bottom half; the halves
meet at z = 7.5. The carrier is drawn closed; open is 86 mm further along x.
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

# Every height sits on a layer line (first layer 0.25, then 0.2: 0.25, 0.45, 0.65 ...),
# measured from the face each part prints on (PRINTER-BRAIN, "Check a fit as printed").
def layer(n):
    """Top of layer n (n = 1 is the first, 0.25 mm)."""
    return 0.05 + 0.2 * n


# ---------------------------------------------------------------- handle
HL, HW = 165.0, 30.0                # length, width
SPLIT = layer(37)                   # 7.45: each half's thickness
HT = 2 * SPLIT                      # 14.9
CORNER_R = 6.0
CHAMFER = layer(7)                  # 1.45
WALL_T = layer(11)                  # 2.25: top and bottom walls
GAP = 0.3                           # sliding gap at the sides of the carrier and blade

# ---------------------------------------------------------------- carrier and blade
CAR_L, CAR_W, CAR_T = 55.0, 22.0, layer(21)    # carrier 4.25 thick
BLADE_L, BLADE_W = 90.0, 18.0       # blade in front of the carrier
CAR_Z0 = SPLIT - CAR_T / 2          # 5.325
CHAN_Y = CAR_W / 2 + GAP            # 11.3
CHAN_Z0 = layer(25)                 # 5.05: channel floor, 0.275 under the carrier
CHAN_Z1 = HT - CHAN_Z0              # 9.85
SLOT_Y = BLADE_W / 2 + GAP          # 9.3
FRONT_IN = 159.0                    # inside face of the front wall
CLOSED_X = 18.0                     # carrier's back end when closed
TRAVEL = FRONT_IN - CAR_L - CLOSED_X   # 86: closed to open
REAR_STOP = CLOSED_X - 0.4          # back end of the carrier channel

# latch: an arm cut from the carrier, a tooth that pops into a window in the +y wall
ARM_X0, ARM_X1 = 15.0, 40.0         # arm along the carrier (free end at ARM_X0)
ARM_T = 1.6
ARM_GAP = 1.4                       # room for the arm to bend in
TOOTH_L = 4.0
TOOTH_OUT = 1.3                     # past the carrier's side, 1.0 into the wall
TOOTH_Z0 = CAR_Z0 + layer(11)      # 7.575: top 10 layers of the carrier (as it prints)
TOOTH_Z1 = CAR_Z0 + CAR_T          # 9.575
WIN_PAD = 0.3                       # window bigger than the tooth, each end

# buttons: a flexible tab in the outside of the +y wall, over each window
SKIN = 0.8                          # wall between the channel and the button pocket
POCKET = 1.6                        # room for the tab to press in (tab left 1.3 thick)
TAB_L = 18.0
TAB_Z0 = HT - layer(34)             # 7.85: the tab, measured from the top half's outside face
TAB_Z1 = HT - layer(12)             # 12.45
SLIT_TOP = HT - layer(8)            # 13.25: top of the slit over the tab
SLIT = 0.8
NUB_Z0, NUB_Z1 = HT - layer(35), HT - layer(27)     # 7.85 to 9.45, inside the tooth's height
WIN_Z1 = HT - layer(24)             # 10.05: top of the window
NUB_GAP = 0.1                       # nub to tooth, unpressed
PRESS = 1.45                        # how far a button goes in: tooth ends 0.35 clear of the wall

# bands: TPU straps from a rear post, round a roller at the front, back to the carrier pin
CAV_Y = 7.5
CAV_Z1 = layer(26)                  # 5.25: top of the bottom band cavity (floor is WALL_T)
STRAND_Y = 4.0
ANCHOR_X = 10.0
ROLLER_X = 150.0
PIN_X = 8.0                         # along the carrier
POST_D = 3.0
PIN_D = 3.0
HOLE_PLAY = 0.4                     # holes print small: 0.4 mm all round (PRINTER-BRAIN)
ROLLER_D = 7.0
ROLLER_H = layer(13)                # 2.65
BAND_H = layer(12)                  # 2.45
POST_TOP = layer(25)                # 5.05: posts stop short of the carrier (5.325)
BAND_T = 1.0
BAND_T_FIRM = 1.3
BAND_RELAXED = 180.0                # printed length between the two eye centres

# screws: four M3 x 16 mm, self-tapping into the bottom half
SCREWS = [(11.0, 11.0), (11.0, -11.0), (162.0, 12.3), (162.0, -12.3)]
SCREW_CLEAR, SCREW_PILOT = 3.6, 2.8
HEAD_D, HEAD_DEPTH = 6.2, layer(15)   # 3.05


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


def rounded_rect(x0, x1, y0, y1, r):
    cs = m3.CrossSection.square([x1 - x0 - 2 * r, y1 - y0 - 2 * r]).translate([x0 + r, y0 + r])
    return cs.offset(r, m3.JoinType.Round, 2.0, 64)


def mirror_z(man):
    """Mirror about the plane where the halves meet."""
    return man.mirror([0, 0, 1]).translate([0, 0, HT])


def window_x(open_):
    """x range of the tooth window for the closed (False) or open (True) carrier."""
    x = CLOSED_X + (TRAVEL if open_ else 0) + ARM_X0
    return x - WIN_PAD, x + TOOTH_L + WIN_PAD


def tabs():
    """(x start, x end, free end x) of the rear and front buttons; the free end is over the window."""
    r0, r1 = window_x(False)
    f0, f1 = window_x(True)
    rear = (r1 + 0.5 - TAB_L, r1 + 0.5, r1 + 0.5)
    front = (f0 - 0.5, f0 - 0.5 + TAB_L, f0 - 0.5)
    return [(rear, (r0, r1)), (front, (f0, f1))]


# ---------------------------------------------------------------- handle halves
FINGERS = [55.0, 78.0, 101.0]       # finger scallops along the -y side (the side away from the buttons)
FINGER_R, FINGER_DEPTH = 9.0, 1.6


def half_shell():
    """Bottom half's outside: a rounded slab with a chamfer round the outside face, and three
    shallow finger scallops in the -y side. Grip texture on the faces would be grooves in the
    first layers, which the slicer has to bridge (PRINTER-BRAIN), so the grip is in the outline."""
    outline = rounded_rect(0, HL, -HW / 2, HW / 2, CORNER_R)
    inner = rounded_rect(CHAMFER, HL - CHAMFER, -HW / 2 + CHAMFER, HW / 2 - CHAMFER, CORNER_R - CHAMFER)
    slab = M.hull_points(np.vstack([
        np.asarray(extrude(inner, 0, 0.01).to_mesh().vert_properties)[:, :3],
        np.asarray(extrude(outline, CHAMFER, SPLIT).to_mesh().vert_properties)[:, :3]]))
    scallops = union([cyl_z(x, -HW / 2 - FINGER_R + FINGER_DEPTH, -1, SPLIT + 1, 2 * FINGER_R, 64)
                      for x in FINGERS])
    return slab - scallops


def inside_cuts_bottom():
    """Channel, blade slot and band cavity in the bottom half (z up to the split)."""
    return union([
        box(REAR_STOP, FRONT_IN, -CHAN_Y, CHAN_Y, CHAN_Z0, SPLIT + 1),
        box(FRONT_IN - 1, HL + 1, -SLOT_Y, SLOT_Y, CHAN_Z0, SPLIT + 1),
        box(ANCHOR_X - 5, ROLLER_X + 6, -CAV_Y, CAV_Y, WALL_T, CAV_Z1),
    ])


POST_TIP = layer(4)                 # 0.85: pointed tip, so a band eye or roller finds the post blind


def post(x, y):
    tip = M.cylinder(POST_TIP, POST_D / 2, POST_D / 4, 40).translate([x, y, POST_TOP - POST_TIP])
    return cyl_z(x, y, WALL_T - 0.5, POST_TOP - POST_TIP, POST_D) + tip


def posts_bottom():
    return union([post(ANCHOR_X, -STRAND_Y), post(ROLLER_X, 0)])


def handle_bottom():
    h = half_shell() - inside_cuts_bottom()
    h = h - union([cyl_z(x, y, SPLIT - 6, SPLIT + 1, SCREW_PILOT) for x, y in SCREWS])
    return h + posts_bottom()


def handle_top():
    h = mirror_z(half_shell()) - mirror_z(inside_cuts_bottom())
    h = h - union([cyl_z(x, y, SPLIT - 1, HT + 1, SCREW_CLEAR) for x, y in SCREWS])
    h = h - union([cyl_z(x, y, HT - HEAD_DEPTH, HT + 1, HEAD_D) for x, y in SCREWS])
    h = h + mirror_z(posts_bottom())
    # buttons in the +y wall
    y_skin = CHAN_Y + SKIN                  # outside of the skin
    y_tab = y_skin + POCKET                 # inside of the tab
    cuts, adds = [], []
    for (ta, tb, free), (w0, w1) in tabs():
        lo, hi = min(ta, tb), max(ta, tb)
        slit_lo, slit_hi = (lo, hi + SLIT) if free == hi else (lo - SLIT, hi)
        cuts += [box(slit_lo, slit_hi, y_skin, y_tab, SPLIT - 0.01, SLIT_TOP),             # pocket
                 box(slit_lo, slit_hi, y_skin, HW / 2 + 1, TAB_Z1, SLIT_TOP),               # slit above
                 box(slit_lo, slit_hi, y_skin, HW / 2 + 1, SPLIT - 0.01, TAB_Z0),           # gap below
                 (box(hi, hi + SLIT, y_skin, HW / 2 + 1, SPLIT - 0.01, SLIT_TOP) if free == hi
                  else box(lo - SLIT, lo, y_skin, HW / 2 + 1, SPLIT - 0.01, SLIT_TOP)),     # slit at the free end
                 box(w0, w1, CHAN_Y - 0.5, y_skin + 0.01, SPLIT - 0.01, WIN_Z1)]            # window
        tooth_out = CAR_W / 2 + TOOTH_OUT
        adds.append(box(w0 + 0.3, w1 - 0.3, tooth_out + NUB_GAP, y_tab + 0.2, NUB_Z0, NUB_Z1))
    return (h - union(cuts)) + union(adds)


# ---------------------------------------------------------------- blade and carrier
def blade_outline():
    """Blade from the carrier forward, as seen from above: a drop point with a round tip."""
    x0, x1 = CAR_L - 3, CAR_L + BLADE_L
    w = BLADE_W / 2
    pts = [(x0, -w), (CAR_L + 40, -w)]
    for i in range(1, 21):                    # edge sweeping up to the tip
        t = i / 20
        pts.append((CAR_L + 40 + t * (x1 - CAR_L - 40), -w + (w + 1.5) * t ** 1.8))
    for i in range(1, 21):                    # back of the blade dropping to the tip
        t = 1 - i / 20
        pts.append((CAR_L + 62 + t * (x1 - CAR_L - 62), w - (w - 1.5) * t ** 1.4))
    pts.append((x0, w))
    cs = m3.CrossSection([pts])
    return cs.offset(-2.5, m3.JoinType.Round, 2.0, 32).offset(2.5, m3.JoinType.Round, 2.0, 32)


def carrier_parts(at=0.0):
    """(body without the tooth, tooth), drawn closed and moved `at` mm toward open."""
    z0, z1 = CAR_Z0, CAR_Z0 + CAR_T
    body = box(0, CAR_L, -CAR_W / 2, CAR_W / 2, z0, z1) + extrude(blade_outline(), z0, z1)
    y_arm = CAR_W / 2 - ARM_T
    body = body - union([
        box(ARM_X0 - 1.4, ARM_X1, y_arm - ARM_GAP, y_arm, z0 - 1, z1 + 1),          # slot behind the arm
        box(ARM_X0 - 1.4, ARM_X0, y_arm - ARM_GAP, CAR_W / 2 + 1, z0 - 1, z1 + 1),   # frees the arm's end
        cyl_z(PIN_X, STRAND_Y, z0 - 1, z1 + 1, PIN_D + 2 * HOLE_PLAY),
        # fuller along the top of the blade
        extrude(m3.CrossSection.square([44, 2.6]).translate([CAR_L + 8, 1.6])
                .offset(0.6, m3.JoinType.Round, 2.0, 16), z1 - 0.8, z1 + 1),
    ])
    tooth = box(ARM_X0, ARM_X0 + TOOTH_L, CAR_W / 2 - 0.2, CAR_W / 2 + TOOTH_OUT, TOOTH_Z0, TOOTH_Z1)
    return body.translate([CLOSED_X + at, 0, 0]), tooth.translate([CLOSED_X + at, 0, 0])


def carrier(at=0.0):
    b, t = carrier_parts(at)
    return b + t


def pin(at=0.0):
    x = CLOSED_X + at + PIN_X
    return cyl_z(x, STRAND_Y, WALL_T + 0.2, HT - WALL_T - 0.2, PIN_D)


def rollers():
    one = cyl_z(ROLLER_X, 0, WALL_T, WALL_T + ROLLER_H, ROLLER_D, 48) - \
        cyl_z(ROLLER_X, 0, 0, HT, POST_D + 2 * HOLE_PLAY)
    return one + mirror_z(one)


# ---------------------------------------------------------------- bands
def band_2d(ax, bx, t):
    """Band seen from above: eye at (ax, -STRAND_Y), round the roller, eye at (bx, +STRAND_Y)."""
    r = ROLLER_D / 2 + t / 2
    eye_in = POST_D + 2 * HOLE_PLAY
    eye_out = eye_in + 2 * t
    sq = m3.CrossSection.square
    parts = [sq([ROLLER_X + 0.01 - ax, t]).translate([ax, -r - t / 2]),    # 0.01 into the arc so they join
             sq([ROLLER_X + 0.01 - bx, t]).translate([bx, r - t / 2]),
             ((m3.CrossSection.circle(r + t / 2, 64) - m3.CrossSection.circle(r - t / 2, 64))
              - sq([30, 30]).translate([-30, -15])).translate([ROLLER_X, 0]),
             m3.CrossSection.circle(eye_out / 2, 32).translate([ax, -r]),
             m3.CrossSection.circle(eye_out / 2, 32).translate([bx, r])]
    cs = m3.CrossSection.batch_boolean(parts, m3.OpType.Add)
    holes = m3.CrossSection.batch_boolean([m3.CrossSection.circle(eye_in / 2, 32).translate([ax, -r]),
                                           m3.CrossSection.circle(eye_in / 2, 32).translate([bx, r])],
                                          m3.OpType.Add)
    return cs - holes


def band_path(ax, bx, t):
    r = ROLLER_D / 2 + t / 2
    return (ROLLER_X - ax) + math.pi * r + (ROLLER_X - bx)


def band_print(t):
    """A band as printed: relaxed, BAND_RELAXED long between eye centres."""
    r = ROLLER_D / 2 + t / 2
    a = 133.0
    b = BAND_RELAXED - a - math.pi * r
    return extrude(band_2d(ROLLER_X - a, ROLLER_X - b, t), 0, BAND_H)


def bands_fitted(at=0.0, t=BAND_T):
    """Both bands stretched into place for the carrier at `at`."""
    bx = CLOSED_X + at + PIN_X
    z0 = WALL_T + (CAV_Z1 - WALL_T - BAND_H) / 2
    one = extrude(band_2d(ANCHOR_X, bx, t), z0, z0 + BAND_H)
    return one + mirror_z(one)


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
    manifold, filament, (x, y) of its lower-left corner on that plate). It carries Flash
    Studio's project settings (flash studio settings.json: AD5X 0.4, 0.20mm Standard, Arachne,
    filaments 1 white, 2 black, 3 brown) and its version tags, or Flash Studio would pile every
    part on plate 1 and filament 1 (PRINTER-BRAIN). Same writer as the shed model's."""
    root = math.sqrt(len(plates))
    cols = round(root) + (1 if root > round(root) else 0)
    stride = 220 * 1.2                    # Orca's plate grid: a fifth of a bed apart
    res, build, cfg, plate_cfg, oid = [], [], [], [], 1
    for i, (plate_name, items) in enumerate(plates):
        ox, oy = (i % cols) * stride, -(i // cols) * stride
        plate_cfg.append(f'<plate><metadata key="plater_id" value="{i + 1}"/>'
                         f'<metadata key="plater_name" value={quoteattr(plate_name)}/>'
                         f'<metadata key="locked" value="false"/>')
        for obj_name, man, filament, (x, y) in items:
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
                       f'<part id="{oid}" subtype="normal_part"><metadata key="name" value={quoteattr(obj_name)}/>'
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


def print_parts():
    """Every part turned the way it prints, sitting on the bed."""
    flip = np.array([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, HT]], dtype=float)   # top half, outside down
    return {
        "handle bottom": on_bed(handle_bottom()),
        "handle top": on_bed(handle_top().transform(flip)),
        "blade": on_bed(carrier()),
        "pin": on_bed(cyl_z(0, 0, 0, HT - 2 * WALL_T - 0.4, PIN_D)
                      .transform(np.array([[0, 0, 1, 0], [0, 1, 0, 0], [-1, 0, 0, 0]], dtype=float))
                      ^ box(-20, 20, -20, 20, PIN_D / 2 - layer(13), 20)),     # lying down, flat underneath, 2.65 tall
        "roller": on_bed(cyl_z(0, 0, 0, ROLLER_H, ROLLER_D, 48) - cyl_z(0, 0, -1, 4, POST_D + 2 * HOLE_PLAY)),
        "band": on_bed(band_print(BAND_T)),
        "band firm": on_bed(band_print(BAND_T_FIRM)),
    }


def main():
    p = print_parts()
    for name, man in p.items():
        write_stl(man, name + ".stl")
    hb, ht, bl = p["handle bottom"], p["handle top"], p["blade"]
    hbw = hb.bounding_box()[3]
    y0 = (220 - (2 * HW + 8)) / 2
    write_3mf("1 knife plates.3mf", [
        ("handle (black)", [                      # filament 2
            ("handle bottom", hb, 2, ((220 - hbw) / 2, y0)),
            ("handle top", ht, 2, ((220 - hbw) / 2, y0 + HW + 8)),
            ("pin", p["pin"], 2, ((220 - hbw) / 2, y0 - 14)),
            ("roller 1", p["roller"], 2, ((220 - hbw) / 2 + 20, y0 - 14)),
            ("roller 2", p["roller"], 2, ((220 - hbw) / 2 + 32, y0 - 14)),
        ]),
        ("blade (white)", [                       # filament 1
            ("blade", bl, 1, ((220 - bl.bounding_box()[3]) / 2, 110 - CAR_W / 2)),
        ]),
    ])
    bp = p["band"]
    bw, bh = bp.bounding_box()[3], bp.bounding_box()[4]
    write_3mf("2 bands (TPU).3mf", [
        ("bands (TPU)", [("band 1", bp, 1, ((220 - bw) / 2, 110 - bh - 5)),
                         ("band 2", bp, 1, ((220 - bw) / 2, 115))]),
    ])
    for name, man in p.items():
        bb = man.bounding_box()
        print(f"{name:14s} {bb[3]-bb[0]:6.1f} x {bb[4]-bb[1]:6.1f} x {bb[5]-bb[2]:5.1f} mm  {man.volume()/1000:5.1f} cm3")


if __name__ == "__main__":
    main()
