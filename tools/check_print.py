#!/usr/bin/env python3
"""Pre-print checker: will this STL or G-code file work on our printer?

Usage:
    python3 tools/check_print.py FILE [FILE ...] [--printer PROFILE] [--material NAME]

Checks STL models for size vs. build volume, units, holes in the mesh,
inverted normals and overhangs. Checks G-code for moves outside the bed,
height, temperatures and nozzle size.

Standard library only (Python 3.11+). Exit code is 1 if any file FAILs;
warnings don't fail.
"""
import argparse
import math
import re
import struct
import sys
import tomllib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PRINTER = ROOT / "printers" / "printer.toml"
MATERIALS_FILE = ROOT / "knowledge" / "materials.toml"

# Below this much steep overhang (mm²) we don't bother warning; the tops of
# small horizontal holes and chamfers print fine without support.
OVERHANG_WARN_MM2 = 25.0


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

    @property
    def failed(self):
        return any(level == "FAIL" for level, _ in self.items)

    def print(self):
        print(f"\n== {self.path}")
        for level, msg in self.items:
            print(f"  [{level:<4}] {msg}")
        verdict = "FAIL - fix before printing" if self.failed else "PASS"
        print(f"  => {verdict}")


def load_toml(path):
    with open(path, "rb") as f:
        return tomllib.load(f)


# ---------------------------------------------------------------- STL

def read_stl(path):
    """Return a list of triangles, each a tuple of three (x, y, z) vertices."""
    data = Path(path).read_bytes()
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


def check_stl(path, printer, material, report):
    tris = read_stl(path)
    if not tris:
        report.fail("STL has no triangles")
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
    def key(v):
        return (round(v[0], 4), round(v[1], 4), round(v[2], 4))

    edges = Counter()
    degenerate = 0
    volume = 0.0
    for a, b, c in tris:
        ka, kb, kc = key(a), key(b), key(c)
        if ka == kb or kb == kc or ka == kc:
            degenerate += 1
            continue
        for e in ((ka, kb), (kb, kc), (kc, ka)):
            edges[tuple(sorted(e))] += 1
        volume += _dot(a, _cross(b, c)) / 6.0

    open_edges = sum(1 for n in edges.values() if n == 1)
    shared_edges = sum(1 for n in edges.values() if n > 2)
    if open_edges:
        report.fail(f"Mesh has holes ({open_edges} open edges) - not a closed solid. "
                    "Repair it (slicer 'fix model', or fix the CAD) before printing.")
    if shared_edges:
        report.fail(f"Mesh has {shared_edges} non-manifold edges (more than two faces "
                    "meet). Usually overlapping parts that weren't unioned.")
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
    overhang = 0.0
    for a, b, c in tris:
        n = _cross(_sub(b, a), _sub(c, a))
        length = math.sqrt(_dot(n, n))
        if length == 0:
            continue
        if flip * n[2] / length < threshold and max(a[2], b[2], c[2]) > z_min + 0.05:
            overhang += length / 2.0
    if overhang > OVERHANG_WARN_MM2:
        report.warn(f"{overhang / 100:.1f} cm² of overhang steeper than {limit}° in "
                    "this orientation - turn on supports, or reorient/redesign "
                    "(chamfers instead of flat ceilings).")
    else:
        report.ok(f"No significant overhangs past {limit}° - prints without supports")


# ---------------------------------------------------------------- G-code

_NUM = re.compile(r"^[-+]?(\d+\.?\d*|\.\d+)$")


def check_gcode(path, printer, material, materials, material_given, report):
    absolute, abs_e = True, True
    pos = {"X": 0.0, "Y": 0.0, "Z": 0.0, "E": 0.0}
    lo = {"X": math.inf, "Y": math.inf}
    hi = {"X": -math.inf, "Y": -math.inf, "Z": -math.inf}
    nozzle_temps, bed_temps = set(), set()
    meta = {}
    extruding_moves = 0

    with open(path, encoding="utf-8", errors="replace") as f:
        for raw in f:
            code, _, comment = raw.partition(";")
            comment = comment.strip()
            # Orca/Prusa list one value per filament slot: "PLA;PLA;PETG" or "0.4,0.4".
            m = re.match(r"(filament_type|nozzle_diameter)\s*[=:]\s*(\S+)", comment, re.I)
            if m:
                values = [v for v in re.split(r"[,;]", m.group(2)) if v]
                meta.setdefault(m.group(1).lower(), values)
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
    if max(temps) > max_temp:
        report.fail(f"{label} temp {max(temps):g} °C is over the printer limit of {max_temp:g} °C")
        return
    if material and key in material:
        low, high = material[key]
        if min(temps) < low - 5 or max(temps) > high + 5:
            report.warn(f"{label} temp {shown} °C is outside the usual "
                        f"{material['name']} range {low}-{high} °C")
            return
    report.ok(f"{label} temp {shown} °C")


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--printer", type=Path, default=DEFAULT_PRINTER,
                    help="printer profile TOML (default: printers/printer.toml)")
    ap.add_argument("--material", help="material name from knowledge/materials.toml")
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

    any_failed = False
    for path in args.files:
        report = Report(path)
        try:
            suffix = path.suffix.lower()
            if suffix == ".stl":
                check_stl(path, printer, material, report)
            elif suffix in (".gcode", ".gco", ".g"):
                check_gcode(path, printer, material, materials,
                            bool(args.material), report)
            else:
                report.fail(f"Don't know how to check {suffix or 'this'} files "
                            "(supported: .stl, .gcode)")
        except (OSError, ValueError) as e:
            report.fail(str(e))
        report.print()
        any_failed |= report.failed
    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main())
