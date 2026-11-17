"""Light, open-back iPhone 15 Pro case, TPU, for the Flashforge AD5X (Nov 17 2026).

Run:  python3 make_case.py      (needs: pip install manifold3d numpy)

As little TPU as does the job: 1.5 mm walls, soft chamfered edges and a raised lip that stands
1.6 mm over the screen, round a back that is mostly open. Only what works stays solid: a band
inside the walls, a frame round the camera, and a frame round a 57.5 mm opening where a MagSafe
charger drops in and sits right on the phone. The rest of the back is a Voronoi web of 1.6 mm struts. The buttons are open
cut-outs with wide 45 degree scoops, so your thumb finds them and presses the phone's own buttons.

Bonus: two TPU dust plugs that press into the case's USB-C and speaker openings.

Where the phone's buttons, ports and camera are: measured off the two iPhone 15 Pro cases in
`desktop prints` (`iphone 15 Pro v5.stl` and `iPhone 15 Pro case - Case.stl`, which Alan
printed in TPU). Both put the camera at the same place to 0.01 mm; the button and port
openings come from the v5 case, which has them, with a little more room.

Axes: the phone's middle at x = y = 0, x across (+x is the right side, the side button, seen
from the screen), y along (+y is the top, the camera end), z up from the back (z = 0 is the
case's back face, which prints on the bed).
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
    """Top of layer n from the bed (first layer 0.25, then 0.2)."""
    return 0.05 + 0.2 * n


# ---------------------------------------------------------------- the phone (Apple: 146.6 x 70.6 x 8.25 mm)
PHONE_W, PHONE_L, PHONE_T = 70.6, 146.6, 8.25
PHONE_R = 11.3                      # corner radius in plan (the reference cases' cavities measure 11.45-11.5)
FIT = 0.15                          # room all round: TPU stretches, so the fit can be close

# ---------------------------------------------------------------- the case
WALL = 1.5
BACK = layer(6)                     # 1.25
CAV_W, CAV_L, CAV_R = PHONE_W + 2 * FIT, PHONE_L + 2 * FIT, PHONE_R + FIT
CAV_TOP = BACK + PHONE_T + FIT      # 9.65: the side walls run straight to here ...
LIP_IN = 1.6                        # ... then slope in at 45 degrees, 1.6 mm over the screen's edge
TOP = CAV_TOP + LIP_IN              # 11.25: the lip stands 1.6 mm over the screen (layer 56)
BACK_EDGE = 0.6                     # the cavity's back edge is cut at 45 degrees to follow the phone's rounded edge
OUT_W, OUT_L, OUT_R = CAV_W + 2 * WALL, CAV_L + 2 * WALL, CAV_R + WALL
CH_BED, CH_TOP = 0.8, 1.0           # outer chamfers: the back edge (45 degrees on the bed) and the lip's outer edge
MID = BACK + PHONE_T / 2            # 5.375: the height of the middle of the phone's side

# buttons and ports: openings measured off the v5 case (phone's middle at 0), drawn as rounded slots
SCOOP = 1.0                         # every side opening widens 1 mm at the outside, at 45 degrees
SIDE_BTN = (7.0, 27.1)              # right side: the side button (v5: 7.25-26.85)
VOLUME = (7.1, 34.9)                # left side: both volume buttons in one slot (v5: 7.35-20.45 and 21.55-34.65)
ACTION = (37.5, 46.0)               # left side: the Action button (v5: 37.75-45.75)
BTN_H = 4.2                         # each button slot's height, centred on the phone's side (v5: 4.2)
USB = (13.0, 6.2)                   # bottom: USB-C, width and height (v5: 12.2 x 6.2, the printed case 13.9 x 5.0)
SPEAKER = (9.9, 21.7)               # bottom, right of the port: the speaker (v5 holes 10.7-20.9, printed case 9.7-21.9)
MIC = (-17.3, -9.9)                 # bottom, left of the port: the microphone (v5 -16.35 to -10.7, printed case -17.35 to -9.7)
GRILLE_H = 2.8

# camera: both reference cases centre it at (12.2, 49.5); the hole is 1 mm bigger than the printed case's all round
CAM_X, CAM_Y = 12.2, 49.5
CAM_W, CAM_L, CAM_R = 42.0, 43.4, 12.0
CAM_CH = 0.8                        # its edge on the back face is cut back 45 degrees

# the back: an open lattice. Only the parts that do a job stay solid: a band round the edge, a ring round the
# camera, and a frame round the MagSafe opening. The rest is a Voronoi web of
# 1.6 mm struts, about 9 mm cells.
EDGE_BAND = 3.0                     # solid back inside the walls, all round
CAM_FRAME = 2.5                     # solid ring round the camera hole
MAG_R0 = 28.75                      # the MagSafe opening: 57.5 across, so a MagSafe charger (55.9 across) drops in and
#                                     sits right on the phone, with nothing between its magnets and the phone's
MAG_R1 = MAG_R0 + 2.5               # a solid frame round the opening
MEET_R = 3.0                        # where the opening meets the camera hole, rounded this much
STRUT = 1.6                         # the web's struts: four lines of a 0.4 nozzle
CELL_ROUND = 1.6                    # each opening's corners rounded this much
CELL = 9.0                          # the web's cells are about this far apart
CELL_SEED = 15                      # the web is the same every run
MIN_HOLE = 12.0                     # openings smaller than this (mm2) are left solid
LLOYD = 3                           # rounds of evening the cells out

# dust plugs: press into the case's openings
PLUG_FIT = 0.05                     # each plug's body is this much smaller than its opening all round
FLANGE = 0.8                        # its flange: this much bigger than the opening all round ...
FLANGE_T = layer(3)                 # ... and 0.65 thick
PLUG_LEN = layer(11) - FLANGE_T     # 1.6: the body reaches 0.05 short of the phone


# ---------------------------------------------------------------- helpers
def box(x0, x1, y0, y1, z0, z1):
    return M.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def union(parts):
    parts = [p for p in parts if p is not None]
    return M.batch_boolean(parts, m3.OpType.Add) if len(parts) > 1 else parts[0]


def rrect(w, l, r, cx=0.0, cy=0.0, grow=0.0):
    w, l, r = w + 2 * grow, l + 2 * grow, max(0.05, r + grow)
    cs = m3.CrossSection.square([w - 2 * r, l - 2 * r]).translate([cx - w / 2 + r, cy - l / 2 + r])
    return cs.offset(r, m3.JoinType.Round, 2.0, 96)


def slab(cs, z0, z1):
    return M.extrude(cs, z1 - z0).translate([0, 0, z0])


def pts(man):
    return np.asarray(man.to_mesh().vert_properties)[:, :3]


def loft(levels):
    """The convex hull of several plan shapes at several heights: [(cross section, z), ...]."""
    return M.hull_points(np.vstack([pts(slab(cs, z, z + 0.001)) for cs, z in levels]))


def stadium(length, height):
    """A rounded slot in its own (u, v) plane, centred on 0."""
    r = height / 2
    return m3.CrossSection.square([max(0.01, length - height), 0.001]).translate([-(length - height) / 2, 0]) \
        .offset(r, m3.JoinType.Round, 2.0, 48)


def side_cut(side, y0, y1, h):
    """A slot through the left (-1) or right (+1) wall, from y0 to y1, centred at the phone's middle height,
    widening SCOOP at the outside."""
    L = y1 - y0
    inner = stadium(L, h)
    outer = stadium(L + 2 * SCOOP, h + 2 * SCOOP)
    x_in, x_out = CAV_W / 2 - 1.0, OUT_W / 2
    def at(cs, x):           # place a (u = y, v = z) slot at wall position x
        m = M.extrude(cs, 0.001).transform(np.array([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0]], dtype=float))
        return m.translate([x * side, (y0 + y1) / 2, MID])
    through = M.hull_points(np.vstack([pts(at(inner, x_in)), pts(at(inner, x_out + 1))]))
    scoop = M.hull_points(np.vstack([pts(at(inner, x_out - SCOOP)), pts(at(outer, x_out + 0.01)),
                                     pts(at(outer, x_out + 1))]))
    return through + scoop


def bottom_cut(x0, x1, h, scoop=SCOOP):
    """A slot through the bottom wall, x0 to x1."""
    L = x1 - x0
    inner = stadium(L, h)
    outer = stadium(L + 2 * scoop, h + 2 * scoop)
    y_in, y_out = CAV_L / 2 - 1.0, OUT_L / 2
    def at(cs, y):           # (u = x, v = z) slot at wall position -y
        m = M.extrude(cs, 0.001).transform(np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]], dtype=float))
        return m.translate([(x0 + x1) / 2, -y, MID])
    through = M.hull_points(np.vstack([pts(at(inner, y_in)), pts(at(inner, y_out + 1))]))
    if not scoop:
        return through
    s = M.hull_points(np.vstack([pts(at(inner, y_out - scoop)), pts(at(outer, y_out + 0.01)), pts(at(outer, y_out + 1))]))
    return through + s


# ---------------------------------------------------------------- the case
def body():
    full = rrect(OUT_W, OUT_L, OUT_R)
    return loft([(rrect(OUT_W, OUT_L, OUT_R, grow=-CH_BED), 0.0), (full, CH_BED), (full, TOP - CH_TOP),
                 (rrect(OUT_W, OUT_L, OUT_R, grow=-CH_TOP), TOP)])


def cavity():
    cav = rrect(CAV_W, CAV_L, CAV_R)
    phone = loft([(rrect(CAV_W, CAV_L, CAV_R, grow=-BACK_EDGE), BACK), (cav, BACK + BACK_EDGE), (cav, CAV_TOP)])
    lip = loft([(cav, CAV_TOP - 0.001), (rrect(CAV_W, CAV_L, CAV_R, grow=-LIP_IN), TOP)])
    opening = slab(rrect(CAV_W, CAV_L, CAV_R, grow=-LIP_IN), TOP - 0.01, TOP + 1)
    return union([phone, lip, opening])


def camera_hole():
    hole = rrect(CAM_W, CAM_L, CAM_R, CAM_X, CAM_Y)
    return union([slab(hole, -1, BACK + 1),
                  loft([(rrect(CAM_W, CAM_L, CAM_R, CAM_X, CAM_Y, grow=CAM_CH), -0.001), (hole, CAM_CH)])])


def lattice_region():
    """Where the back may be opened: inside the edge band, outside the camera's frame and the MagSafe ring."""
    inner = rrect(CAV_W, CAV_L, CAV_R, grow=-(BACK_EDGE + EDGE_BAND))
    keep = m3.CrossSection.batch_boolean([
        rrect(CAM_W, CAM_L, CAM_R, CAM_X, CAM_Y, grow=CAM_FRAME + STRUT / 2),
        m3.CrossSection.circle(MAG_R1 + STRUT / 2, 192)], m3.OpType.Add)
    return inner - keep


def voronoi_cells(points, region):
    """Each point's Voronoi cell, cut to the region: the region cut by the half-plane nearer that point than each other."""
    x0, y0, x1, y1 = region.bounds()
    big = max(x1 - x0, y1 - y0) * 4
    cells = []
    for i, p in enumerate(points):
        cell = region
        for j, q in enumerate(points):
            if i == j or np.hypot(*(q - p)) > 40:
                continue
            mid, d = (p + q) / 2, (q - p) / np.hypot(*(q - p))
            n = np.array([-d[1], d[0]])
            half = [mid + n * big, mid + n * big - d * big, mid - n * big - d * big, mid - n * big]   # the side nearer p
            cell = cell ^ m3.CrossSection([[tuple(v) for v in half]])
            if cell.area() <= 0:
                break
        cells.append(cell)
    return cells


def centroid(cs):
    best = None
    for poly in cs.to_polygons():
        p = np.asarray(poly)
        a = p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1]
        A = a.sum() / 2
        if A <= 0 or (best and A < best[0]):
            continue
        cx = ((p[:, 0] + np.roll(p[:, 0], -1)) * a).sum() / (6 * A)
        cy = ((p[:, 1] + np.roll(p[:, 1], -1)) * a).sum() / (6 * A)
        best = (A, np.array([cx, cy]))
    return best[1] if best else None


def lattice_holes():
    """The openings in the back: a relaxed Voronoi web over the region."""
    region = lattice_region()
    x0, y0, x1, y1 = region.bounds()
    rng = np.random.default_rng(CELL_SEED)
    # seeds on a hexagonal grid, shaken a little so the web looks grown, not tiled
    pts = []
    row = 0
    y = y0 - CELL
    while y < y1 + CELL:
        x = x0 - CELL + (CELL / 2 if row % 2 else 0)
        while x < x1 + CELL:
            p = np.array([x, y]) + rng.uniform(-0.3, 0.3, 2) * CELL
            pts.append(p)
            x += CELL
        y += CELL * math.sqrt(3) / 2
        row += 1
    near = lambda p: (region ^ m3.CrossSection.circle(CELL * 0.6, 24).translate(list(p))).area() > 0
    pts = np.array([p for p in pts if near(p)])
    for _ in range(LLOYD):                               # Lloyd's relaxation: move each point to its cell's middle;
        cells = voronoi_cells(pts, region)               # a few rounds even the cells out but keep the grading
        new = []
        for p, c in zip(pts, cells):
            m = centroid(c)
            new.append(p if m is None else m)
        pts = np.array(new)
    holes = []
    for c in voronoi_cells(pts, region):
        h = c.offset(-STRUT / 2, m3.JoinType.Miter).offset(-CELL_ROUND, m3.JoinType.Round, 2.0, 32) \
            .offset(CELL_ROUND, m3.JoinType.Round, 2.0, 32)
        if h.area() >= MIN_HOLE:
            holes.append(h)
    window = m3.CrossSection.circle(MAG_R0, 192)        # the MagSafe opening
    return m3.CrossSection.batch_boolean(holes + [window], m3.OpType.Add)


def back_cut():
    # the MagSafe opening runs into the camera hole (the charger sits just below the camera): round off the two points
    # of TPU left where they meet
    both = m3.CrossSection.batch_boolean([rrect(CAM_W, CAM_L, CAM_R, CAM_X, CAM_Y), m3.CrossSection.circle(MAG_R0, 192)],
                                         m3.OpType.Add)
    meet = both.offset(MEET_R, m3.JoinType.Round, 2.0, 64).offset(-MEET_R, m3.JoinType.Round, 2.0, 64)
    return slab(m3.CrossSection.batch_boolean([lattice_holes(), meet], m3.OpType.Add), -1, BACK + BACK_EDGE + 0.5)


def case():
    cuts = [cavity(), camera_hole(), back_cut(),
            side_cut(+1, *SIDE_BTN, BTN_H), side_cut(-1, *VOLUME, BTN_H), side_cut(-1, *ACTION, BTN_H),
            bottom_cut(-USB[0] / 2, USB[0] / 2, USB[1]), bottom_cut(*SPEAKER, GRILLE_H), bottom_cut(*MIC, GRILLE_H)]
    return body() - union(cuts)


def phone():
    """The phone as a rounded block, for checking the fit."""
    return loft([(rrect(PHONE_W, PHONE_L, PHONE_R, grow=-0.8), BACK + FIT), (rrect(PHONE_W, PHONE_L, PHONE_R), BACK + FIT + 0.8),
                 (rrect(PHONE_W, PHONE_L, PHONE_R), BACK + FIT + PHONE_T - 0.8),
                 (rrect(PHONE_W, PHONE_L, PHONE_R, grow=-0.8), BACK + FIT + PHONE_T)])


# ---------------------------------------------------------------- dust plugs (printed flange down)
def plug(length, height):
    body_ = M.extrude(stadium(length - 2 * PLUG_FIT, height - 2 * PLUG_FIT), PLUG_LEN + 0.01).translate([0, 0, FLANGE_T - 0.01])
    fl = stadium(length + 2 * FLANGE, height + 2 * FLANGE)
    flange = loft([(stadium(length + 2 * FLANGE - 0.6, height + 2 * FLANGE - 0.6), 0.0), (fl, 0.3), (fl, FLANGE_T)])
    notch = box(length / 2 + FLANGE - 1.2, length / 2 + FLANGE + 1, -0.6, 0.6, -1, layer(1))   # a nick to lift it with a nail
    return (flange + body_) - notch


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
        f.write(b"Minimal iPhone 15 Pro case".ljust(80, b" "))
        f.write(struct.pack("<I", len(tri)))
        rec = np.zeros(len(tri), dtype=[("n", "<f4", 3), ("a", "<f4", 3), ("b", "<f4", 3), ("c", "<f4", 3), ("x", "<u2")])
        rec["n"], rec["a"], rec["b"], rec["c"] = n, a, b, c
        f.write(rec.tobytes())


def project_settings(process=None):
    """Flash Studio's project settings with filament 1 turned into Generic TPU (as the shop's TPU projects)."""
    with open(os.path.join(HERE, "flash studio settings.json")) as f:
        d = json.load(f)
    with open(os.path.join(HERE, "flash studio TPU filament.json")) as f:
        tpu = {k_: v for k_, v in json.load(f).items() if not k_.startswith("_")}
    for key, v in tpu.items():
        d[key][0] = v
    diff = d["different_settings_to_system"]
    for key, v in (process or {}).items():
        d[key] = v
    if process:
        diff[0] = ";".join(sorted(set(filter(None, diff[0].split(";"))) | set(process)))
    return json.dumps(d, indent=4) + "\n"


def write_3mf(name, plates, settings):
    """A Flash Studio project (the spring knife's writer). plates: [(plate name, items)];
    items: (object name, manifold, filament, (x, y) of its lower-left corner[, own settings])."""
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
            bb = man.bounding_box()
            mid = np.array([(bb[0] + bb[3]) / 2, (bb[1] + bb[4]) / 2, (bb[2] + bb[5]) / 2])
            mesh = man.to_mesh()
            v = np.asarray(mesh.vert_properties)[:, :3] - mid
            tri = np.asarray(mesh.tri_verts)
            vs = "".join(f'<vertex x="{a:.4f}" y="{b:.4f}" z="{c:.4f}"/>' for a, b, c in v)
            ts = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tri)
            res.append(f'<object id="{oid}" name={quoteattr(obj_name)} type="model"><mesh>'
                       f'<vertices>{vs}</vertices><triangles>{ts}</triangles></mesh></object>')
            top = oid + 1
            res.append(f'<object id="{top}" name={quoteattr(obj_name)} type="model"><components>'
                       f'<component objectid="{oid}"/></components></object>')
            cfg.append(f'<object id="{top}"><metadata key="name" value={quoteattr(obj_name)}/>'
                       f'<metadata key="extruder" value="{filament}"/>'
                       + "".join(f'<metadata key="{key}" value={quoteattr(v)}/>' for key, v in own.items())
                       + f'<part id="{oid}" subtype="normal_part"><metadata key="name" value={quoteattr(obj_name)}/>'
                       f'<metadata key="extruder" value="{filament}"/></part></object>')
            build.append(f'<item objectid="{top}" transform="1 0 0 0 1 0 0 0 1 '
                         f'{ox + x + mid[0] - bb[0]:.4f} {oy + y + mid[1] - bb[1]:.4f} {mid[2] - bb[2]:.4f}"/>')
            plate_cfg.append(f'<model_instance><metadata key="object_id" value="{top}"/>'
                             f'<metadata key="instance_id" value="0"/></model_instance>')
            oid = top + 1
        plate_cfg.append('</plate>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             '<metadata name="Title">Minimal iPhone 15 Pro case</metadata>'
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
        z.writestr("Metadata/project_settings.config", settings)
        z.writestr("Metadata/model_settings.config",
                   '<?xml version="1.0" encoding="UTF-8"?>\n<config>' + "".join(cfg + plate_cfg) + '</config>')


def on_bed(man):
    bb = man.bounding_box()
    return man.translate([-bb[0], -bb[1], -bb[2]])


# TPU: slow and solid; no brim (it would have to be peeled off a soft part); the stock walls are fine at 1.5 mm
CASE_SET = {"wall_loops": "4", "sparse_infill_density": "100%", "brim_type": "no_brim", "seam_position": "back"}
PLUG_SET = {"wall_loops": "3", "sparse_infill_density": "100%", "brim_type": "no_brim"}


def print_parts():
    return {
        "case": on_bed(case()),
        "plug USB-C": on_bed(plug(*USB)),
        "plug speaker": on_bed(plug(SPEAKER[1] - SPEAKER[0], GRILLE_H)),
    }


def main():
    p = print_parts()
    for name, man in p.items():
        write_stl(man, name + ".stl")
    w = lambda n: p[n].bounding_box()[3] - p[n].bounding_box()[0]
    items = [("case", p["case"], 1, ((220 - w("case")) / 2, 25), CASE_SET),
             ("plug USB-C", p["plug USB-C"], 1, (20, 190), PLUG_SET),
             ("plug USB-C spare", p["plug USB-C"], 1, (45, 190), PLUG_SET),
             ("plug speaker", p["plug speaker"], 1, (150, 190), PLUG_SET),
             ("plug speaker spare", p["plug speaker"], 1, (175, 190), PLUG_SET)]
    write_3mf("iphone 15 pro case TPU.3mf", [("case and dust plugs (TPU)", items)], project_settings())
    for name, man in p.items():
        bb = man.bounding_box()
        print(f"{name:14s} {bb[3]-bb[0]:6.1f} x {bb[4]-bb[1]:6.1f} x {bb[5]-bb[2]:5.2f} mm  {man.volume()/1000:5.2f} cm3")


if __name__ == "__main__":
    main()
