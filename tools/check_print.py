#!/usr/bin/env python3
"""Pre-print checker: will this STL, 3MF or G-code file work on our printer?

Usage:
    python3 tools/check_print.py FILE_OR_FOLDER [...] [--printer PROFILE]
                                 [--material NAME] [--summary]

Checks STL models for size vs. build volume, units, holes in the mesh,
inverted normals and overhangs. Checks G-code for the printer it was sliced
for, moves outside the bed, height, temperatures and nozzle size.

3MF files from Orca-Flashforge / OrcaSlicer: sliced ones (.gcode.3mf) get the
G-code checks for every plate plus the slicer's own warnings; unsliced
project files get the model checks for every object.

Folders are searched for all supported files.

Standard library only (Python 3.11+). Exit code is 1 if any file FAILs;
warnings don't fail.
"""
import argparse
import io
import json
import math
import re
import struct
import sys
import tomllib
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PRINTER = ROOT / "printers" / "printer.toml"
MATERIALS_FILE = ROOT / "knowledge" / "materials.toml"

# Below this much steep overhang (mm²) we don't bother warning; the tops of
# small horizontal holes and chamfers print fine without support.
OVERHANG_WARN_MM2 = 25.0

GCODE_SUFFIXES = (".gcode", ".gco", ".g")
SUPPORTED_SUFFIXES = (".stl", ".3mf") + GCODE_SUFFIXES


class Report:
    def __init__(self, path):
        self.path = path
        self.items = []

    def info(self, msg):
        self.items.append(("INFO", msg))

    def ok(self, msg):
        self.items.append(("OK", msg))

    def warn(self, msg):
        self.items.append(("WARN", msg))

    def fail(self, msg):
        self.items.append(("FAIL", msg))

    def section(self, title):
        self.items.append(("HEAD", title))

    @property
    def failed(self):
        return any(level == "FAIL" for level, _ in self.items)

    @property
    def warned(self):
        return any(level == "WARN" for level, _ in self.items)

    def print(self):
        print(f"\n== {self.path}")
        for level, msg in self.items:
            if level == "HEAD":
                print(f"  -- {msg}")
            else:
                print(f"  [{level:<4}] {msg}")
        verdict = "FAIL - fix before printing" if self.failed else "PASS"
        print(f"  => {verdict}")

    def print_summary_line(self):
        """One line: verdict, path, and the first problem if there is one."""
        for level in ("FAIL", "WARN"):
            first = next((m for lvl, m in self.items if lvl == level), None)
            if first:
                print(f"[{level}] {self.path}: {first}")
                return
        print(f"[PASS] {self.path}")


def load_toml(path):
    with open(path, "rb") as f:
        return tomllib.load(f)


# ---------------------------------------------------------------- STL

def read_stl(path):
    """Return a list of triangles, each a tuple of three (x, y, z) vertices."""
    data = Path(path).read_bytes()
    if data.startswith(b"version https://git-lfs"):
        raise ValueError("This is a Git LFS placeholder, not the model. "
                         "Run `git lfs pull` to download the real file.")
    is_ascii = data[:5].lower() == b"solid" and b"facet" in data[:1024]
    if not is_ascii and len(data) >= 84:
        count = struct.unpack_from("<I", data, 80)[0]
        if len(data) >= 84 + 50 * count:
            tris = []
            for i in range(count):
                v = struct.unpack_from("<12f", data, 84 + 50 * i)
                tris.append((v[3:6], v[6:9], v[9:12]))
            return tris
    text = data.decode("ascii", errors="replace")
    verts = [tuple(map(float, m)) for m in
             re.findall(r"vertex\s+(\S+)\s+(\S+)\s+(\S+)", text)]
    if not verts or len(verts) % 3:
        raise ValueError("not a readable STL file")
    return [tuple(verts[i:i + 3]) for i in range(0, len(verts), 3)]


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _in_triangle_2d(x, y, t):
    """Is point (x, y) inside triangle t, looking straight down?"""
    def side(p, q):
        return (q[0] - p[0]) * (y - p[1]) - (q[1] - p[1]) * (x - p[0])
    d1, d2, d3 = side(t[0], t[1]), side(t[1], t[2]), side(t[2], t[0])
    has_neg = d1 < 0 or d2 < 0 or d3 < 0
    has_pos = d1 > 0 or d2 > 0 or d3 > 0
    return not (has_neg and has_pos)


def check_stl(path, printer, material, report):
    check_mesh([read_stl(path)], printer, material, report)


def check_mesh(parts, printer, material, report, supports=False):
    """parts: one triangle list per separate mesh. An STL is one part; a 3MF
    object can be several (one per color, say) that touch each other, so
    watertightness is checked per part, and size/overhangs for the whole.
    supports: the slicer project already has supports turned on."""
    tris = [t for part in parts for t in part]
    if not tris:
        report.fail("Model has no triangles")
        return
    report.info(f"{len(tris):,} triangles")

    xs = [v[0] for t in tris for v in t]
    ys = [v[1] for t in tris for v in t]
    zs = [v[2] for t in tris for v in t]
    size = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    z_min = min(zs)
    report.info(f"Size: {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm "
                f"({size[0] / 25.4:.2f} x {size[1] / 25.4:.2f} x {size[2] / 25.4:.2f} in)")

    biggest = max(size)
    if biggest < 1:
        report.warn("Model is under 1 mm across - it was probably exported in "
                    "meters or inches. Re-export in millimeters.")
    elif biggest > 2000:
        report.warn("Model is over 2 m across - check the export units (should be mm).")

    # Fit on the bed, allowing a 90° turn.
    vol = printer["build_volume"]
    bed_x = vol["x_max"] - max(vol["x_min"], 0)
    bed_y = vol["y_max"] - max(vol["y_min"], 0)
    bed_z = vol["z_max"]
    fits_z = size[2] <= bed_z
    fits_flat = size[0] <= bed_x and size[1] <= bed_y
    fits_turned = size[0] <= bed_y and size[1] <= bed_x
    if fits_z and fits_flat:
        report.ok(f"Fits the build volume ({bed_x:g} x {bed_y:g} x {bed_z:g} mm)")
    elif fits_z and fits_turned:
        report.ok("Fits the build volume if turned 90° on the bed")
    else:
        long_side, short_side = max(size[:2]), min(size[:2])
        scale = min(max(bed_x, bed_y) / long_side if long_side else 1,
                    min(bed_x, bed_y) / short_side if short_side else 1,
                    bed_z / size[2] if size[2] else 1)
        report.fail(f"Too big for the build volume ({bed_x:g} x {bed_y:g} x {bed_z:g} mm). "
                    f"Split it into parts, lay it on another side, or scale to "
                    f"{math.floor(scale * 100)}% or less.")

    # Mesh integrity: every edge of a closed solid is shared by exactly 2 triangles.
    # Vertices are matched on a grid scaled to the model, so a model exported in
    # meters doesn't get its vertices merged together.
    grid = min(1e-4, biggest * 1e-6) or 1e-4

    def key(v):
        return (round(v[0] / grid), round(v[1] / grid), round(v[2] / grid))

    edges = Counter()
    degenerate = 0
    volume = 0.0
    for i, part in enumerate(parts):
        for a, b, c in part:
            ka, kb, kc = key(a), key(b), key(c)
            if ka == kb or kb == kc or ka == kc:
                degenerate += 1
                continue
            for e in ((ka, kb), (kb, kc), (kc, ka)):
                edges[(i,) + tuple(sorted(e))] += 1
            volume += _dot(a, _cross(b, c)) / 6.0

    # Slicers usually print through these (Orca patches small holes), so they
    # warn rather than fail. Our own OpenSCAD exports are always closed.
    open_edges = sum(1 for n in edges.values() if n == 1)
    shared_edges = sum(1 for n in edges.values() if n > 2)
    if open_edges:
        report.warn(f"Mesh has holes ({open_edges} open edges). The slicer usually "
                    "patches small ones; check the sliced preview for gaps.")
    if shared_edges:
        report.warn(f"Mesh has {shared_edges} non-manifold edges (more than two faces "
                    "meet, usually overlapping shells). The slicer usually copes; "
                    "check the sliced preview.")
    if not open_edges and not shared_edges:
        report.ok("Mesh is closed (watertight)")
    if degenerate:
        report.info(f"{degenerate} zero-size triangles skipped (harmless, slicer ignores them)")

    if volume < 0:
        report.warn("Normals point inward (inside-out mesh). Most slicers fix this, "
                    "but check the CAD export.")
    flip = -1.0 if volume < 0 else 1.0
    volume = abs(volume)
    cm3 = volume / 1000.0
    density = material.get("density") if material else None
    if density:
        report.info(f"Solid volume {cm3:.1f} cm³ = {cm3 * density:.0f} g of filament "
                    "at 100% infill (real prints use less)")
    else:
        report.info(f"Solid volume {cm3:.1f} cm³")

    # Overhangs: downward-facing area steeper than the limit, ignoring the bed face.
    limit = printer.get("defaults", {}).get("max_overhang_deg", 45)
    # Small margin so faces right at the limit (a 45° chamfer) don't trip on float error.
    threshold = -math.sin(math.radians(limit)) - 0.01
    normals = []
    tops = {}  # flat upward faces by height: a part stacked on one (multi-color) is supported
    for t in tris:
        n = _cross(_sub(t[1], t[0]), _sub(t[2], t[0]))
        length = math.sqrt(_dot(n, n))
        nz = flip * n[2] / length if length else 0.0
        normals.append((nz, length))
        if nz > 0.99:
            tops.setdefault(round(t[0][2] / 0.01), []).append(t)

    def rests_on_top_face(t):
        cx = (t[0][0] + t[1][0] + t[2][0]) / 3
        cy = (t[0][1] + t[1][1] + t[2][1]) / 3
        return any(_in_triangle_2d(cx, cy, top) for top in tops.get(round(t[0][2] / 0.01), ()))

    overhang = 0.0
    for t, (nz, length) in zip(tris, normals):
        if nz < threshold and max(v[2] for v in t) > z_min + 0.05:
            if nz < -0.99 and rests_on_top_face(t):
                continue
            overhang += length / 2.0
    if overhang > OVERHANG_WARN_MM2 and supports:
        report.info(f"{overhang / 100:.1f} cm² of overhang steeper than {limit}° - "
                    "supports are on in this project")
    elif overhang > OVERHANG_WARN_MM2:
        report.warn(f"{overhang / 100:.1f} cm² of overhang steeper than {limit}° in "
                    "this orientation - turn on supports, or reorient/redesign "
                    "(chamfers instead of flat ceilings).")
    else:
        report.ok(f"No significant overhangs past {limit}° - prints without supports")


# ---------------------------------------------------------------- G-code

_NUM = re.compile(r"^[-+]?(\d+\.?\d*|\.\d+)$")


def _norm_model(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _check_sliced_for(model, printer, report):
    """FAIL if the slicer's printer model isn't ours ("Flashforge-AD5X" == "Flashforge AD5X")."""
    ours = printer["printer"]["name"]
    if _norm_model(model) == _norm_model(ours):
        report.ok(f"Sliced for our printer ({model})")
    else:
        report.fail(f"Sliced for a {model}, not our {ours}. Re-slice it with the "
                    f"{ours} printer profile.")


def check_gcode(path, printer, material, materials, material_given, report):
    with open(path, encoding="utf-8", errors="replace") as f:
        check_gcode_lines(f, printer, material, materials, material_given, report)


def check_gcode_lines(lines, printer, material, materials, material_given, report,
                      sliced_for=None):
    """Check G-code read from any iterable of lines (a file, or a plate inside a 3MF).

    sliced_for is the printer model from outside the G-code (3MF metadata),
    used when the G-code itself doesn't name one.
    """
    absolute, abs_e = True, True
    pos = {"X": 0.0, "Y": 0.0, "Z": 0.0, "E": 0.0}
    lo = {"X": math.inf, "Y": math.inf}
    hi = {"X": -math.inf, "Y": -math.inf, "Z": -math.inf}
    nozzle_temps, bed_temps = set(), set()
    meta = {}
    extruding_moves = 0

    for raw in lines:
        code, _, comment = raw.partition(";")
        comment = comment.strip()
        # Orca/Prusa list one value per filament slot: "PLA;PLA;PETG" or "0.4,0.4".
        m = re.match(r"(filament_type|nozzle_diameter)\s*[=:]\s*(\S+)", comment, re.I)
        if m:
            values = [v for v in re.split(r"[,;]", m.group(2)) if v]
            meta.setdefault(m.group(1).lower(), values)
        m = re.match(r"printer_model\s*=\s*(.+)", comment)
        if m and m.group(1).strip():
            meta.setdefault("printer_model", m.group(1).strip())
        m = re.match(r"FLAVOR:\s*(\S+)", comment)
        if m:
            meta.setdefault("flavor", m.group(1))
        words = code.upper().split()
        if not words:
            continue
        cmd = words[0]
        if cmd in ("PRINT_START", "START_PRINT"):
            meta.setdefault("flavor", "Klipper macro")
        params = {w[0]: float(w[1:]) for w in words[1:]
                  if len(w) > 1 and w[0].isalpha() and _NUM.match(w[1:])}

        if cmd == "G90":
            absolute, abs_e = True, True
        elif cmd == "G91":
            absolute, abs_e = False, False
        elif cmd == "M82":
            abs_e = True
        elif cmd == "M83":
            abs_e = False
        elif cmd == "G92":
            for axis in pos:
                if axis in params:
                    pos[axis] = params[axis]
        elif cmd == "G28":
            for axis in ("X", "Y", "Z"):
                pos[axis] = 0.0
        elif cmd in ("G0", "G1", "G2", "G3"):
            start = dict(pos)
            for axis in ("X", "Y", "Z"):
                if axis in params:
                    pos[axis] = params[axis] if absolute else pos[axis] + params[axis]
            de = 0.0
            if "E" in params:
                de = params["E"] - pos["E"] if abs_e else params["E"]
                pos["E"] = params["E"] if abs_e else pos["E"] + params["E"]
            if cmd != "G0" and de > 0:
                extruding_moves += 1
                for p in (start, pos):
                    for axis in ("X", "Y"):
                        lo[axis] = min(lo[axis], p[axis])
                        hi[axis] = max(hi[axis], p[axis])
                hi["Z"] = max(hi["Z"], pos["Z"])
        elif cmd in ("M104", "M109") and params.get("S"):
            nozzle_temps.add(params["S"])
        elif cmd in ("M140", "M190") and params.get("S"):
            bed_temps.add(params["S"])

    model = meta.get("printer_model") or sliced_for
    if model:
        _check_sliced_for(model, printer, report)

    if "flavor" in meta:
        report.info(f"G-code flavor: {meta['flavor']} (printer firmware: "
                    f"{printer['printer'].get('firmware', '?')})")
    if not extruding_moves:
        report.fail("No extrusion moves found - this doesn't look like a print file.")
        return
    report.info(f"{extruding_moves:,} extrusion moves")

    vol = printer["build_volume"]
    tol = 0.5
    out = []
    if lo["X"] < vol["x_min"] - tol or hi["X"] > vol["x_max"] + tol:
        out.append(f"X {lo['X']:.1f}..{hi['X']:.1f} (bed {vol['x_min']:g}..{vol['x_max']:g})")
    if lo["Y"] < vol["y_min"] - tol or hi["Y"] > vol["y_max"] + tol:
        out.append(f"Y {lo['Y']:.1f}..{hi['Y']:.1f} (bed {vol['y_min']:g}..{vol['y_max']:g})")
    if out:
        report.fail("Prints outside the bed: " + "; ".join(out) +
                    ". It was sliced for a different printer or placed off the bed.")
    else:
        report.ok(f"All extrusion inside the bed (X {lo['X']:.1f}..{hi['X']:.1f}, "
                  f"Y {lo['Y']:.1f}..{hi['Y']:.1f})")
    if hi["Z"] > vol["z_max"] + tol:
        report.fail(f"Print is {hi['Z']:.1f} mm tall; printer max is {vol['z_max']:g} mm")
    else:
        report.ok(f"Height {hi['Z']:.1f} mm is within {vol['z_max']:g} mm")

    nozzle = printer["nozzle"]
    if meta.get("nozzle_diameter"):
        sliced = float(meta["nozzle_diameter"][0])
        if abs(sliced - nozzle["diameter"]) > 1e-3:
            report.fail(f"Sliced for a {sliced:g} mm nozzle; printer has "
                        f"{nozzle['diameter']:g} mm")
        else:
            report.ok(f"Sliced for the {sliced:g} mm nozzle")

    # Material named in the slicer comments wins unless one was passed explicitly.
    sliced_types = sorted({t.upper() for t in meta.get("filament_type", [])})
    if not material_given and len(sliced_types) == 1 and sliced_types[0] in materials:
        name = sliced_types[0]
        material = dict(materials[name], name=name)
        report.info(f"Slicer says material is {name}")
    elif not material_given and len(sliced_types) == 1:
        report.info(f"Slicer says material is {sliced_types[0]} (not in "
                    "knowledge/materials.toml, so only printer limits are checked)")
        material = None
    elif not material_given and len(sliced_types) > 1:
        # Multi-color job with different materials; one range can't cover them all.
        material = None
        report.info(f"Slicer lists materials {', '.join(sliced_types)} - "
                    "checking temps against printer limits only")

    _check_temps(report, "Nozzle", nozzle_temps, nozzle["max_temp"],
                 material, "nozzle")
    _check_temps(report, "Bed", bed_temps, printer["bed"]["max_temp"],
                 material, "bed")
    if material and material.get("enclosure") and not printer["printer"].get("enclosure"):
        report.warn(f"{material['name']} needs an enclosure; printer profile says "
                    "it has none. Expect warping/cracks.")


def _check_temps(report, label, temps, max_temp, material, key):
    if not temps:
        report.warn(f"No {label.lower()} temperature set in the file")
        return
    shown = ", ".join(f"{t:g}" for t in sorted(temps))
    hottest = max(temps)
    if hottest > max_temp:
        report.fail(f"{label} temp {hottest:g} °C is over the printer limit of {max_temp:g} °C")
        return
    if material and key in material:
        # Judge the hottest setting; lower ones are preheat / nozzle-wipe temps.
        low, high = material[key]
        if not low - 5 <= hottest <= high + 5:
            report.warn(f"{label} temp {shown} °C is outside the usual "
                        f"{material['name']} range {low}-{high} °C")
            return
    report.ok(f"{label} temp {shown} °C")


# ---------------------------------------------------------------- 3MF

_NS_CORE = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
_NS_PROD = "{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}"
_ROOT_MODEL = "/3D/3dmodel.model"
_IDENTITY = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (0.0, 0.0, 0.0))


def _parse_transform(text):
    """3MF transform "m00 m01 m02 m10 ... m32": rows of a 4x3 matrix, row-vector convention."""
    if not text:
        return _IDENTITY
    v = [float(x) for x in text.split()]
    return (tuple(v[0:3]), tuple(v[3:6]), tuple(v[6:9]), tuple(v[9:12]))


def _apply(m, p):
    return tuple(p[0] * m[0][i] + p[1] * m[1][i] + p[2] * m[2][i] + m[3][i] for i in range(3))


def _compose(first, then):
    """Transform that applies `first`, then `then`."""
    rows = tuple(tuple(sum(first[r][k] * then[k][c] for k in range(3)) for c in range(3))
                 for r in range(3))
    return rows + (_apply(then, first[3]),)


def read_3mf_objects(zf):
    """Return [(name, meshes)] for each object placed on the build plate, with
    its placement (rotation/scale) applied. meshes is one triangle list per part."""
    files = {}

    def load(path):
        if path not in files:
            root = ET.fromstring(zf.read(path.lstrip("/")))
            objects = {}
            for obj in root.iter(_NS_CORE + "object"):
                mesh = obj.find(_NS_CORE + "mesh")
                verts, faces = [], []
                if mesh is not None:
                    verts = [(float(v.get("x")), float(v.get("y")), float(v.get("z")))
                             for v in mesh.iter(_NS_CORE + "vertex")]
                    faces = [(int(t.get("v1")), int(t.get("v2")), int(t.get("v3")))
                             for t in mesh.iter(_NS_CORE + "triangle")]
                parts = [(c.get(_NS_PROD + "path") or path, c.get("objectid"),
                          _parse_transform(c.get("transform")))
                         for c in obj.iter(_NS_CORE + "component")]
                objects[obj.get("id")] = (obj.get("name"), verts, faces, parts)
            files[path] = (root, objects)
        return files[path]

    def flatten(path, oid, m, depth=0):
        """Triangle lists, one per mesh, for an object and its components."""
        if depth > 16:
            raise ValueError("3MF components nest too deep (loop?)")
        _, verts, faces, components = load(path)[1][oid]
        moved = [_apply(m, v) for v in verts]
        meshes = [[(moved[a], moved[b], moved[c]) for a, b, c in faces]] if faces else []
        for part_path, part_id, part_m in components:
            meshes += flatten(part_path, part_id, _compose(part_m, m), depth + 1)
        return meshes

    root, objects = load(_ROOT_MODEL)
    placed = []
    build = root.find(_NS_CORE + "build")
    for i, item in enumerate(build.findall(_NS_CORE + "item") if build is not None else [], 1):
        path = item.get(_NS_PROD + "path") or _ROOT_MODEL
        oid = item.get("objectid")
        name = load(path)[1][oid][0] or f"object {i}"
        placed.append((name, flatten(path, oid, _parse_transform(item.get("transform")))))
    return placed


def _read_slice_info(zf):
    """Per-plate slicer metadata from Metadata/slice_info.config (Orca/Bambu)."""
    try:
        root = ET.fromstring(zf.read("Metadata/slice_info.config"))
    except KeyError:
        return {}
    plates = {}
    for plate in root.iter("plate"):
        meta = {m.get("key"): m.get("value") for m in plate.findall("metadata")}
        plates[meta.get("index", "1")] = {
            "meta": meta,
            "filaments": [f.attrib for f in plate.findall("filament")],
            "warnings": [w.get("msg", "") for w in plate.findall("warning")],
        }
    return plates


def _slicer_warning(code, printer, report):
    if code == "bed_temperature_too_high_than_filament" and not printer["printer"].get("enclosure"):
        # Orca compares the bed to the filament's softening point (45 °C for
        # Generic PLA). Heat only builds up enough to jam the nozzle in an enclosure.
        report.info("Slicer note: bed is hotter than the filament's softening point. "
                    "Only a problem in an enclosed printer; fine on our open frame.")
    else:
        report.warn(f"Slicer warning: {code.replace('_', ' ')}")


def check_3mf(path, printer, material, materials, material_given, report):
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        with open(path, "rb") as f:
            head = f.read(40)
        if head.startswith(b"version https://git-lfs"):
            raise ValueError("This is a Git LFS placeholder, not the file. "
                             "Run `git lfs pull` to download the real file.")
        raise ValueError("not a readable 3MF file (expected a zip archive)")
    with zf:
        try:
            settings = json.loads(zf.read("Metadata/project_settings.config"))
        except (KeyError, ValueError):
            settings = {}
        plates = sorted((n for n in zf.namelist()
                         if re.fullmatch(r"Metadata/plate_\d+\.gcode", n)),
                        key=lambda n: int(re.search(r"\d+", n).group()))
        if plates:
            info = _read_slice_info(zf)
            for name in plates:
                number = re.search(r"\d+", name).group()
                plate = info.get(number, {"meta": {}, "filaments": [], "warnings": []})
                if len(plates) > 1:
                    report.section(f"Plate {number}")
                if plate["meta"].get("outside") == "true":
                    report.fail("Slicer says part of this plate is outside the printable area")
                for warning in plate["warnings"]:
                    _slicer_warning(warning, printer, report)
                used = [f"{f.get('type', '?')} {f.get('used_g', '?')} g" for f in plate["filaments"]]
                if used:
                    report.info("Filament: " + ", ".join(used))
                sliced_for = plate["meta"].get("printer_model_id") or settings.get("printer_model")
                with zf.open(name) as raw:
                    check_gcode_lines(io.TextIOWrapper(raw, encoding="utf-8", errors="replace"),
                                      printer, material, materials, material_given, report,
                                      sliced_for=sliced_for)
            return

        report.info("Project file, not sliced - checking the models")
        if settings.get("printer_model"):
            _check_sliced_for(settings["printer_model"], printer, report)
        types = {t.upper() for t in settings.get("filament_type", [])}
        if not material_given and len(types) == 1 and next(iter(types)) in materials:
            name = types.pop()
            material = dict(materials[name], name=name)
        objects = read_3mf_objects(zf)
        if not objects:
            report.fail("This 3MF is empty: no sliced G-code and no objects on the "
                        "plate. Re-save it from the slicer with the model in it.")
        supports = str(settings.get("enable_support", "0")) in ("1", "true")
        for name, meshes in objects:
            if len(objects) > 1:
                report.section(name)
            check_mesh(meshes, printer, material, report, supports=supports)


# ---------------------------------------------------------------- main

def find_files(paths):
    """Expand folders into the supported files inside them."""
    for path in paths:
        if path.is_dir():
            yield from sorted(f for f in path.rglob("*")
                              if f.is_file() and f.suffix.lower() in SUPPORTED_SUFFIXES)
        else:
            yield path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("files", nargs="+", type=Path, help="files or folders")
    ap.add_argument("--printer", type=Path, default=DEFAULT_PRINTER,
                    help="printer profile TOML (default: printers/printer.toml)")
    ap.add_argument("--material", help="material name from knowledge/materials.toml")
    ap.add_argument("--summary", action="store_true",
                    help="one line per file instead of the full report")
    args = ap.parse_args(argv)

    printer = load_toml(args.printer)
    materials = {k.upper(): v for k, v in load_toml(MATERIALS_FILE).items()}
    name = (args.material or printer.get("defaults", {}).get("material", "")).upper()
    if name and name not in materials:
        ap.error(f"unknown material {name!r}; known: {', '.join(materials)}")
    material = dict(materials[name], name=name) if name else None

    print(f"Printer: {printer['printer']['name']}  |  Material: {name or '?'}")
    if not printer["printer"].get("confirmed"):
        print("  [WARN] printers/printer.toml is a placeholder - set your real "
              "printer's specs and confirmed = true.")

    reports = []
    for path in find_files(args.files):
        report = Report(path)
        try:
            suffix = path.suffix.lower()
            if suffix == ".stl":
                check_stl(path, printer, material, report)
            elif suffix == ".3mf":
                check_3mf(path, printer, material, materials, bool(args.material), report)
            elif suffix in GCODE_SUFFIXES:
                check_gcode(path, printer, material, materials,
                            bool(args.material), report)
            else:
                report.fail(f"Don't know how to check {suffix or 'this'} files "
                            "(supported: .stl, .3mf, .gcode)")
        except (OSError, ValueError, KeyError, ET.ParseError, zipfile.BadZipFile) as e:
            report.fail(str(e) or type(e).__name__)
        if args.summary:
            report.print_summary_line()
        else:
            report.print()
        reports.append(report)

    if len(reports) > 1:
        failed = sum(r.failed for r in reports)
        warned = sum(r.warned and not r.failed for r in reports)
        print(f"\n{len(reports)} files: {len(reports) - failed - warned} pass, "
              f"{warned} pass with warnings, {failed} fail")
    if not reports:
        print("No .stl, .3mf or .gcode files found")
    return 1 if any(r.failed for r in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
