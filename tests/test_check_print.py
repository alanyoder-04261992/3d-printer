import io
import json
import struct
import sys
import tempfile
import unittest
import zipfile
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

    def test_open_mesh_warns(self):
        # Slicers print through small holes, so it's a warning, not a failure.
        r = self.stl(box_tris(20, 20, 20)[:-2])
        self.assertFalse(r.failed, r.items)
        self.assertTrue(any("holes" in m for m in self.messages(r, "WARN")))

    def test_wrong_units_warns(self):
        r = self.stl(box_tris(0.02, 0.02, 0.02))
        self.assertTrue(any("meters" in m for m in self.messages(r, "WARN")))
        # Tiny coordinates must not be merged into one point by the vertex matching.
        self.assertTrue(any("watertight" in m for m in self.messages(r, "OK")))

    def test_touching_parts_are_checked_separately(self):
        # Two closed boxes stacked so they share a face, like a 2-color model.
        bottom = box_tris(20, 20, 10)
        top = box_tris(20, 20, 10, z0=10)
        r = check_print.Report("parts")
        check_print.check_mesh([bottom, top], PRINTER, PLA, r)
        self.assertFalse(self.messages(r, "WARN"), r.items)
        # Merged into one mesh, the shared face shows up as non-manifold edges.
        r = check_print.Report("merged")
        check_print.check_mesh([bottom + top], PRINTER, PLA, r)
        self.assertTrue(any("non-manifold" in m for m in self.messages(r, "WARN")))

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
        # Same model in a project that already has supports on: just a note.
        r = check_print.Report("supported")
        check_print.check_mesh([tris], PRINTER, PLA, r, supports=True)
        self.assertFalse(self.messages(r, "WARN"), r.items)
        self.assertTrue(any("supports are on" in m for m in self.messages(r, "INFO")))

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
        r = self.gcode(self.GOOD.replace("M104 S205", "M104 S250"))
        self.assertTrue(any("PLA range" in m for m in self.messages(r, "WARN")))

    def test_preheat_temp_is_ignored(self):
        # Slicers preheat at 140-150 °C before homing; only the print temp counts.
        r = self.gcode(self.GOOD.replace("M104 S205", "M104 S150\nM104 S230"))
        self.assertFalse(self.messages(r, "WARN"), r.items)

    def test_material_from_slicer_comment(self):
        text = "; filament_type = ASA\n" + self.GOOD.replace("M104 S205", "M104 S250") \
            .replace("M140 S60", "M140 S100")
        r = self.gcode(text, given=False)
        self.assertFalse(r.failed, r.items)
        self.assertTrue(any("enclosure" in m for m in self.messages(r, "WARN")))

    def test_orca_multi_slot_comments(self):
        # Orca lists one value per IFS slot.
        text = "; filament_type = PETG;PETG;PETG;PETG\n; nozzle_diameter = 0.4,0.4\n" + \
            self.GOOD.replace("M104 S205", "M104 S240").replace("M140 S60", "M140 S80")
        r = self.gcode(text, given=False)
        self.assertFalse(r.failed, r.items)
        self.assertFalse(self.messages(r, "WARN"), r.items)
        self.assertTrue(any("material is PETG" in m for m in self.messages(r, "INFO")))

    def test_mixed_materials_skip_range_check(self):
        text = "; filament_type = PLA;PETG\n" + self.GOOD.replace("M104 S205", "M104 S240")
        r = self.gcode(text, given=False)
        self.assertFalse(r.failed, r.items)
        self.assertFalse(self.messages(r, "WARN"), r.items)
        self.assertTrue(any("PETG, PLA" in m for m in self.messages(r, "INFO")))

    def test_no_extrusion_fails(self):
        r = self.gcode("G28\nG1 X10 Y10\n")
        self.assertTrue(r.failed)

    # --- 3MF

    def threemf(self, files, name="m.3mf"):
        path = self.dir / name
        with zipfile.ZipFile(path, "w") as z:
            for arcname, data in files.items():
                z.writestr(arcname, data)
        report = check_print.Report(path)
        check_print.check_3mf(path, PRINTER, PLA, MATERIALS, False, report)
        return report

    @staticmethod
    def slice_info(outside="false", warning=None):
        warn = f'<warning msg="{warning}" level="1" />' if warning else ""
        return ('<config><plate><metadata key="index" value="1"/>'
                '<metadata key="printer_model_id" value="Test"/>'
                f'<metadata key="outside" value="{outside}"/>'
                f'<filament id="1" type="PLA" used_g="12.29"/>{warn}</plate></config>')

    def test_sliced_3mf_checks_plate_gcode(self):
        r = self.threemf({"Metadata/plate_1.gcode": self.GOOD,
                          "Metadata/slice_info.config": self.slice_info()},
                         name="m.gcode.3mf")
        self.assertFalse(r.failed, r.items)
        self.assertTrue(any("our printer (Test)" in m for m in self.messages(r, "OK")))
        self.assertTrue(any("PLA 12.29 g" in m for m in self.messages(r, "INFO")))

    def test_sliced_3mf_reports_slicer_problems(self):
        r = self.threemf({"Metadata/plate_1.gcode": self.GOOD,
                          "Metadata/slice_info.config": self.slice_info(
                              outside="true", warning="filament_not_enough")})
        self.assertTrue(any("outside the printable area" in m for m in self.messages(r, "FAIL")))
        self.assertTrue(any("filament not enough" in m for m in self.messages(r, "WARN")))

    def test_bed_softening_warning_only_matters_enclosed(self):
        files = {"Metadata/plate_1.gcode": self.GOOD,
                 "Metadata/slice_info.config": self.slice_info(
                     warning="bed_temperature_too_high_than_filament")}
        r = self.threemf(files)
        self.assertFalse(self.messages(r, "WARN"), r.items)
        self.assertTrue(any("open frame" in m for m in self.messages(r, "INFO")))

        enclosed = dict(PRINTER, printer=dict(PRINTER["printer"], enclosure=True))
        r = check_print.Report("enclosed")
        check_print._slicer_warning("bed_temperature_too_high_than_filament", enclosed, r)
        self.assertTrue(any("bed temperature" in m for m in self.messages(r, "WARN")))

    def test_empty_3mf_fails(self):
        ns = 'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"'
        r = self.threemf({"3D/3dmodel.model": f"<model {ns}><resources/><build/></model>"})
        self.assertTrue(any("empty" in m for m in self.messages(r, "FAIL")))

    def test_project_3mf_applies_component_and_build_transforms(self):
        # Orca layout: the root model has a component pointing at a mesh in another
        # file; the build item scales it 2x and moves it on the plate.
        tris = box_tris(20, 10, 5)
        verts = sorted({v for t in tris for v in t})
        index = {v: i for i, v in enumerate(verts)}
        vxml = "".join(f'<vertex x="{x}" y="{y}" z="{z}"/>' for x, y, z in verts)
        txml = "".join(f'<triangle v1="{index[a]}" v2="{index[b]}" v3="{index[c]}"/>'
                       for a, b, c in tris)
        ns = ('xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
              'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06"')
        part = (f'<model {ns}><resources><object id="1" type="model"><mesh>'
                f'<vertices>{vxml}</vertices><triangles>{txml}</triangles>'
                '</mesh></object></resources></model>')
        root = (f'<model {ns}><resources><object id="2" name="bracket" type="model">'
                '<components><component p:path="/3D/Objects/object_1.model" objectid="1"/>'
                '</components></object></resources><build>'
                '<item objectid="2" transform="2 0 0 0 2 0 0 0 2 100 100 0"/></build></model>')
        r = self.threemf({"3D/3dmodel.model": root, "3D/Objects/object_1.model": part,
                          "Metadata/project_settings.config": json.dumps(
                              {"printer_model": "Test", "filament_type": ["PETG"]})})
        self.assertFalse(r.failed, r.items)
        self.assertTrue(any("40.0 x 20.0 x 10.0 mm" in m for m in self.messages(r, "INFO")))
        # Material comes from the project: 8 cm³ at PETG's 1.27 g/cm³.
        self.assertTrue(any("8.0 cm³ = 10 g" in m for m in self.messages(r, "INFO")))

    def test_lfs_placeholder_is_explained(self):
        for name in ("big.stl", "big.3mf"):
            path = self.dir / name
            path.write_text("version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 9\n")
            r = check_print.Report(path)
            with self.assertRaisesRegex(ValueError, "git lfs pull"):
                if name.endswith(".stl"):
                    check_print.check_stl(path, PRINTER, PLA, r)
                else:
                    check_print.check_3mf(path, PRINTER, PLA, MATERIALS, False, r)

    # --- Real repo config

    def test_repo_printer_profile_is_ad5x(self):
        printer = check_print.load_toml(check_print.DEFAULT_PRINTER)
        self.assertTrue(printer["printer"]["confirmed"])
        self.assertIn(printer["defaults"]["material"].upper(), MATERIALS)
        vol = printer["build_volume"]
        self.assertEqual((vol["x_max"], vol["y_max"], vol["z_max"]), (220, 220, 220))

    def test_ad5x_start_gcode_stays_on_bed(self):
        # Purge lines from both AD5X profiles: Orca-Flashforge (front edge, what our
        # printed files use) and upstream OrcaSlicer (back edge).
        printer = check_print.load_toml(check_print.DEFAULT_PRINTER)
        for purge in ("G1 X50 Y-1 Z0.25 F9000\nG1 X70 E3 F900\nG1 X200 E10 F1800\n"
                      "G0 Y-1.4\nG1 X130 E5 F1800\n",
                      "G1 X50 Y220 Z0.25 F4800\nG1 X70 E3 F900\nG1 X200 E10 F1800\n"
                      "G0 Y219.6\nG1 X130 E5 F1800\n"):
            path = self.dir / "ad5x.gcode"
            path.write_text("; printer_model = Flashforge AD5X\nM190 S55\nM104 S220\n"
                            "G90\nM83\nG1 Z2 F6000\n" + purge + "G92 E0\n"
                            "G1 X100 Y100 Z0.2 E1\n")
            r = check_print.Report(path)
            check_print.check_gcode(path, printer, PLA, MATERIALS, True, r)
            self.assertFalse(r.failed, r.items)
            self.assertTrue(any("our printer" in m for m in self.messages(r, "OK")))

    def test_sliced_for_other_printer_fails(self):
        r = self.gcode("; printer_model = Creality Ender-3 S1\n" + self.GOOD)
        self.assertTrue(any("Ender-3" in m for m in self.messages(r, "FAIL")))

    def test_asa_on_open_frame_warns(self):
        printer = check_print.load_toml(check_print.DEFAULT_PRINTER)
        path = self.dir / "asa.gcode"
        path.write_text(self.GOOD.replace("M104 S205", "M104 S250").replace("M140 S60", "M140 S100"))
        r = check_print.Report(path)
        check_print.check_gcode(path, printer, dict(MATERIALS["ASA"], name="ASA"), MATERIALS, True, r)
        self.assertTrue(any("enclosure" in m for m in self.messages(r, "WARN")))

    # --- CLI

    def test_cli_exit_codes(self):
        good = self.dir / "good.stl"
        write_binary_stl(good, box_tris(20, 20, 20))
        bad = self.dir / "bad.stl"
        write_binary_stl(bad, box_tris(300, 20, 20))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(check_print.main([str(good)]), 0)
            self.assertEqual(check_print.main([str(good), str(bad)]), 1)


if __name__ == "__main__":
    unittest.main()
