# OTF fidget knife — sliced and ready

**`OTF fidget knife 3 parts PLA+.gcode.3mf`** — all three parts on one plate.
**47 layers, 9.85 mm tall, 19.66 g, 1 h 28 m.**

## One thing you should know up front

I don't have Orca-Flashforge in here, so this was sliced with **PrusaSlicer**. What makes
it safe is that none of the machine-specific parts are invented:

- The **start and end G-code are yours, character for character** — pulled out of your own
  sliced sword file. Same bed heat, same nozzle preheat, same purge line down the front
  edge, same shutdown.
- The **bed is your 220 × 220**, and I checked every single move: nothing goes outside it
  except your own purge routine, which is meant to.
- The **file container** is rebuilt from your own AD5X export — same member names, same
  md5 sidecar, same slice-info and settings blocks. The printer sees a file shaped exactly
  like one its own slicer made.

It should just run. But it's the first file I've built from scratch rather than edited, so
**watch the first layer** rather than walking away.

## What's in it

| | |
|---|---|
| Wall generator | **Arachne** — the whole point, see below |
| Walls | 4 |
| Infill | 40 % gyroid |
| Nozzle | 230 °C (232 first layer) |
| Bed | 60 °C |
| Part fan | 50 % (80 % on bridges), off for the first 2 layers |
| Brim | 5 mm |
| Supports | none |
| Layer height | 0.2 mm (0.25 first) |
| Retraction | 0.8 mm — your printer's own value |

## The bit that matters

I checked the sliced result at the spring's height. Across those 23 layers there are
**240 perimeters, 213 external perimeters, and exactly 1 internal-infill move.** That means
Arachne is filling the 2.2 mm spring fin entirely with walls — no gap-fill seam down the
middle, which is what would otherwise crack after a few hundred flicks.

That was the whole reason for slicing it myself rather than just handing you settings.

## Checks I ran on the finished file

- Every move inside the 220 × 220 bed. The only negative-Y coordinates are your purge line.
- Max Z 9.85 mm — matches the handle plus brim, so nothing got flattened or lost.
- All three parts present and arranged (see `plate_preview.png` — that's the actual first
  layer from the file, not a mock-up).
- Relative extrusion with `G92 E0` on all 47 layers, so the extruder can't drift.
- Fan values are whole numbers, and there are 45 progress lines so the printer's time
  estimate tracks properly.
- Zero support material. Brim present. End G-code intact.
- File checksum rewritten and the archive verifies clean.

## After it prints

Snap the brim off, then dry-fit before forcing anything. If the blade binds, sand its
edges lightly first — only scale the **blade** (99.5 %) if that isn't enough, never the
handle.

And print a spare slider at some point. It's the part that eventually goes, it's 20
minutes, and you'll be glad it's in a drawer.
