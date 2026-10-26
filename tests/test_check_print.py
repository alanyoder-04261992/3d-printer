import io
import struct
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import check_print  # noqa: E402

PRINTER = {
    "printer": {"name": "Test", "confirmed": True, "firmware": "marlin", "enclosure": False},
    "build_volume": {"x_min": 0, "x_max": 220, "y_min": 0, "y_max": 220, "z_max": 250},
    "nozzle": {"diameter": 0.4, "max_temp": 260},
    "bed": {"max_temp": 100},
    "defaults": {"material": "PLA", "max_overhang_deg": 45},
}
MATERIALS = {k.upper(): v for k, v in check_print.load_toml(check_print.MATERIALS_FILE).items()}
PLA = dict(MATERIALS["PLA"], name="PLA")


def box_tris(sx, sy, sz, z0=0.0):
    """Outward-facing triangles of an axis-aligned box."""
    p = [(x, y, z) for x in (0, sx) for y in (0, sy) for z in (z0, z0 + sz)]
    quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    tris = []
    for a, b, c, d in quads:
        tris += [(p[a], p[b], p[c]), (p[a], p[c], p[d])]
    return tris


def write_binary_stl(path, tris):
    with open(path, "wb") as f:
        f.write(b"\0" * 80 + struct.pack("<I", len(tris)))
        for t in tris:
            f.write(struct.pack("<12fH", 0, 0, 0, *t[0], *t[1], *t[2], 0))


def write_ascii_stl(path, tris):
    lines = ["solid test"]
    for t in tris:
        lines += ["facet normal 0 0 0", "outer loop"]
        lines += [f"vertex {v[0]} {v[1]} {v[2]}" for v in t]
        lines += ["endloop", "endfacet"]
    Path(path).write_text("\n".join(lines + ["endsolid test"]))


class CheckerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def stl(self, tris, ascii=False):
        path = self.dir / "m.stl"
        (write_ascii_stl if ascii else write_binary_stl)(path, tris)
        report = check_print.Report(path)
        check_print.check_stl(path, PRINTER, PLA, report)
        return report

    def gcode(self, text, material=PLA, given=True):
        path = self.dir / "m.gcode"
        path.write_text(text)
        report = check_print.Report(path)
        check_print.check_gcode(path, PRINTER, material, MATERIALS, given, report)
        return report

    def messages(self, report, level):
        return [m for lvl, m in report.items if lvl == level]

    # --- STL

    def test_closed_box_passes(self):
        for ascii in (False, True):
            r = self.stl(box_tris(20, 20, 20), ascii=ascii)
            self.assertFalse(r.failed, r.items)
            self.assertFalse(self.messages(r, "WARN"), r.items)
            self.assertTrue(any("8.0 cm³" in m for m in self.messages(r, "INFO")))

    def test_too_big_fails(self):
        r = self.stl(box_tris(300, 50, 10))
        self.assertTrue(any("Too big" in m for m in self.messages(r, "FAIL")))

    def test_fits_when_turned(self):
        printer = dict(PRINTER, build_volume=dict(PRINTER["build_volume"], y_max=100))
        path = self.dir / "m.stl"
        write_binary_stl(path, box_tris(50, 150, 10))
        r = check_print.Report(path)
        check_print.check_stl(path, printer, PLA, r)
        self.assertFalse(r.failed, r.items)
        self.assertTrue(any("turned 90" in m for m in self.messages(r, "OK")))

    def test_open_mesh_fails(self):
        r = self.stl(box_tris(20, 20, 20)[:-2])
        self.assertTrue(any("holes" in m for m in self.messages(r, "FAIL")))

    def test_wrong_units_warns(self):
        r = self.stl(box_tris(0.02, 0.02, 0.02))
        self.assertTrue(any("meters" in m for m in self.messages(r, "WARN")))

    def test_inverted_normals_warn(self):
        r = self.stl([(a, c, b) for a, b, c in box_tris(20, 20, 20)])
        self.assertTrue(any("inward" in m for m in self.messages(r, "WARN")))
        # Flipped normals must not make the walls look like overhangs.
        self.assertFalse(any("overhang" in m for m in self.messages(r, "WARN")))

    def test_floating_ceiling_is_overhang(self):
        # Two separate boxes: one on the bed, one floating whose bottom is a flat ceiling.
        tris = box_tris(10, 10, 10) + [
            tuple((x + 30, y, z) for x, y, z in t) for t in box_tris(20, 20, 5, z0=10)]
        r = self.stl(tris)
        self.assertTrue(any("overhang" in m for m in self.messages(r, "WARN")))

    def test_45_degree_chamfer_is_not_overhang(self):
        # Square frustum: 20 mm base on the bed widening to 30 mm at 5 mm up (45° walls).
        b = [(5, 5, 0), (25, 5, 0), (25, 25, 0), (5, 25, 0)]
        t = [(0, 0, 5), (30, 0, 5), (30, 30, 5), (0, 30, 5)]
        tris = [(b[0], b[2], b[1]), (b[0], b[3], b[2]),
                (t[0], t[1], t[2]), (t[0], t[2], t[3])]
        for i in range(4):
            j = (i + 1) % 4
            tris += [(b[i], b[j], t[j]), (b[i], t[j], t[i])]
        r = self.stl(tris)
        self.assertFalse(r.failed, r.items)
        self.assertFalse(self.messages(r, "WARN"), r.items)

    # --- G-code

    GOOD = (
        "; nozzle_diameter = 0.4\n"
        "M140 S60\nM104 S205\nG28\nG90\nM82\nG92 E0\n"
        "G1 Z0.2 F3000\nG1 X10 Y10\nG1 X100 Y10 E5\nG1 X100 Y100 E10\n"
        "G1 Z20\nG1 X50 Y50 E12\n"
    )

    def test_good_gcode_passes(self):
        r = self.gcode(self.GOOD)
        self.assertFalse(r.failed, r.items)
        self.assertFalse(self.messages(r, "WARN"), r.items)

    def test_outside_bed_fails(self):
        r = self.gcode(self.GOOD + "G1 X300 Y50 E14\n")
        self.assertTrue(any("outside the bed" in m for m in self.messages(r, "FAIL")))

    def test_travel_outside_bed_is_fine(self):
        r = self.gcode(self.GOOD + "G0 X-5 Y-5\n")
        self.assertFalse(r.failed, r.items)

    def test_relative_extrusion(self):
        r = self.gcode("M104 S205\nM140 S60\nG90\nM83\nG1 X10 Y10 Z0.2\n"
                       "G1 X20 E1\nG1 X30 E1\n")
        self.assertFalse(r.failed, r.items)
        self.assertTrue(any("2 extrusion" in m for m in self.messages(r, "INFO")))

    def test_too_tall_fails(self):
        r = self.gcode(self.GOOD + "G1 Z300\nG1 X60 E13\n")
        self.assertTrue(any("tall" in m for m in self.messages(r, "FAIL")))

    def test_wrong_nozzle_fails(self):
        r = self.gcode(self.GOOD.replace("0.4", "0.6"))
        self.assertTrue(any("nozzle" in m for m in self.messages(r, "FAIL")))

    def test_temp_over_limit_fails(self):
        r = self.gcode(self.GOOD.replace("M104 S205", "M104 S280"))
        self.assertTrue(any("over the printer limit" in m for m in self.messages(r, "FAIL")))

    def test_temp_wrong_for_material_warns(self):
        r = self.gcode(self.GOOD.replace("M104 S205", "M104 S245"))
        self.assertTrue(any("PLA range" in m for m in self.messages(r, "WARN")))

    def test_material_from_slicer_comment(self):
        text = "; filament_type = ASA\n" + self.GOOD.replace("M104 S205", "M104 S250") \
            .replace("M140 S60", "M140 S100")
        r = self.gcode(text, given=False)
        self.assertFalse(r.failed, r.items)
        self.assertTrue(any("enclosure" in m for m in self.messages(r, "WARN")))

    def test_no_extrusion_fails(self):
        r = self.gcode("G28\nG1 X10 Y10\n")
        self.assertTrue(r.failed)

    # --- CLI

    def test_cli_exit_codes(self):
        good = self.dir / "good.stl"
        write_binary_stl(good, box_tris(20, 20, 20))
        bad = self.dir / "bad.stl"
        write_binary_stl(bad, box_tris(20, 20, 20)[:-1])
        with redirect_stdout(io.StringIO()):
            self.assertEqual(check_print.main([str(good)]), 0)
            self.assertEqual(check_print.main([str(good), str(bad)]), 1)


if __name__ == "__main__":
    unittest.main()
