# Lessons learned

What our printer and materials actually did, as opposed to the rules of thumb.
Add an entry whenever a print teaches something that applies to future
designs. If it changes a rule, update `design-rules.md` too.

The first entries come from the notes in `collapsible blade/` and `knife/`.

| Date | Project | What happened | Rule going forward |
|------|---------|---------------|--------------------|
| 2026 | Collapsible sword blade | PLA blade snapped along a layer line. It was sliced at 210 °C with the part fan **and** the aux blower at 100 %, so each layer had cooled before the next landed. An "aligned" seam stacked every layer's weak point in one line down a 0.8 mm wall. | Parts that flex or take hits, in PLA/PLA+: **230 °C (232 °C first layer), part fan 40 %, aux blower off, 60 mm/s walls, flow 1.02, acceleration 3000.** About 25 % slower, much tougher. If it strings, drop to 225 °C. |
| 2026 | Collapsible sword blade | Classic wall generator squeezes two 0.42 mm lines into a 0.8 mm wall and leaves a hairline gap between them. | Thin walls: Orca → Quality → **Wall generator: Arachne**. **Seam: Random or Scarf**, never Aligned, on thin parts that take load. |
| 2026 | Collapsible sword blade (tip) | The tip segment was modeled solid, not as a tube. The slicer filled it with 15 % infill and a solid cap, and gave it only one wall line. | Model hollow parts as hollow. Before printing, check the slicer preview for infill where there shouldn't be any. |
| 2026 | Collapsible sword blade (PETG) | An earlier PETG test came out weaker than PLA+. The likely cause was damp filament: water flashes to steam in the nozzle and leaves bubbles inside the walls. | **Dry PETG first: 65 °C for 6 h** in a dryer, or on the bed at 70 °C under a cardboard box. Print right after drying. Popping, hissing or foggy/stringy output means it's wet. |
| 2026 | Collapsible sword blade (PETG) | PETG at 80 °C bonds so hard to smooth PEI that it can tear chunks out of the sheet. | PETG goes on the **textured PEI plate**. On smooth PEI, wipe on a thin layer of glue stick first as a release agent. |
| 2026 | Collapsible sword blade (PETG) | Tough PETG settings that worked on the AD5X. | **245 °C, bed 80 °C, part fan 25 %, aux off, 50 mm/s, retraction 1.2 mm, pressure advance 0.045.** Heavy cooling makes PETG delaminate. Pull stringing out of tubes and bores before assembly. |
| 2026-10-26 | Flash drive check | Orca-Flashforge's AD5X start G-code draws the purge line just off the front edge (Y −1 to −1.4). The upstream OrcaSlicer profile draws it at the back. | `printers/printer.toml` has `y_min = -1.5`. Our slices use the front-edge purge. |
| 2026-10-26 | Flash drive check | Almost every AD5X slice carries Orca's warning "bed temperature too high than filament": the bed is at 55 °C, above Generic PLA's 45 °C softening point. | Harmless on our open frame. It only matters in an enclosure, where the heat builds up and can jam the nozzle. |
