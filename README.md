# 3d-printer

Central place for designing new 3D prints for the shed business: what our
printer can do, design rules that work on it, one folder per part, and a
checker that catches problems before you waste filament.

## Quick start

```sh
# Start a new part
python3 tools/new_project.py "Vent louver clip"

# After exporting the STL (or slicing to G-code), check it against our printer
python3 tools/check_print.py projects/vent-louver-clip/model.stl --material PETG
```

The checker reports each problem as **FAIL** (fix before printing) or
**WARN** (look at it):

- **STL:** fits the bed (including turned 90°), wrong export units, holes in
  the mesh, inside-out normals, overhangs that need supports, filament weight
- **G-code:** prints outside the bed or too tall, wrong nozzle size,
  temperatures over the printer's limit or outside the material's range,
  materials that need an enclosure

It needs only Python 3.11+; nothing to install.

## Set up your printer

Edit `printers/printer.toml` with your printer's bed size, max height,
nozzle and temp limits, then set `confirmed = true`. Until then the checker
uses a generic 220 x 220 x 250 mm printer and warns on every run.

## Where things are

| Path | What |
|------|------|
| `CLAUDE.md` | How Claude should design prints in this repo |
| `printers/printer.toml` | Our printer's specs |
| `knowledge/design-rules.md` | Wall thickness, tolerances, overhangs, shed fastener sizes, scale-model sizes |
| `knowledge/materials.md` | PLA vs PETG vs ASA vs TPU |
| `knowledge/lessons-learned.md` | What our prints actually taught us |
| `projects/` | One folder per part |
| `tools/` | Checker and new-project script |
