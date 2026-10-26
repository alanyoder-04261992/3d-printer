# 3D print brain

This repo is the central place for designing new 3D prints for the shed
business: shed hardware, dealer-lot displays, scale models, signs, jigs.
Every session that designs a print starts here and leaves what it learned here.

## Before designing anything

1. Read `printers/printer.toml`. Our printer is a **Flashforge AD5X**:
   220 x 220 x 220 mm, 0.4 mm nozzle, open frame (no enclosure), 4-color IFS,
   sliced in Orca-Flashforge / OrcaSlicer. If the user mentions a different
   printer or nozzle, update the profile first.
2. Read `knowledge/design-rules.md` and `knowledge/lessons-learned.md`.
   Lessons learned override the general rules.
3. Pick the material with `knowledge/materials.md`. Anything outdoors or in a
   closed shed is PETG, never PLA (ASA warps on the open-frame AD5X).

## Making a new print

1. `python3 tools/new_project.py "Name of part"` creates `projects/<name>/`.
2. Fill in the brief in its `README.md`. Ask the user for anything you'd
   otherwise guess: real measurements of what it attaches to, indoor/outdoor,
   load, quantity.
3. Design in `model.scad` (OpenSCAD). Keep every dimension a named parameter at
   the top, in millimeters, with tolerances from `design-rules.md` applied.
   Convert inches to mm (1 in = 25.4 mm).
4. Export: `openscad -o projects/<name>/model.stl projects/<name>/model.scad`.
   If OpenSCAD isn't installed where you're running, tell the user to export
   locally and commit the STL. For multi-color prints, export one STL per color
   (see "Multi-color" in `design-rules.md`) and check each.
5. Check: `python3 tools/check_print.py projects/<name>/model.stl --material PETG`.
   Fix every FAIL. Explain each WARN to the user or fix it. Paste the
   result into the project README.
6. Sliced files can be checked the same way: `.gcode`, and Orca-Flashforge's
   `.gcode.3mf` / project `.3mf`. Pass a folder to check everything in it
   (`--summary` for one line per file). This catches files sliced for the
   wrong printer, nozzle or temperatures, and shows the slicer's own warnings.

## After the user prints it

Record the result in the project's print log. If it teaches something
general (a tolerance that was off, a material that failed), add a row to
`knowledge/lessons-learned.md` and update `design-rules.md`.

## Layout

- `printers/printer.toml`: the printer everything is checked against
- `knowledge/`: design rules, materials (`materials.toml` is read by the checker), lessons learned
- `projects/<name>/`: one folder per part (brief, `model.scad`, `model.stl`, print log)
- `projects/_template/`: what `new_project.py` copies
- `tools/check_print.py`: pre-print checker (STL, 3MF and G-code, Python stdlib only)
- `tests/`: `python3 -m unittest discover tests`
