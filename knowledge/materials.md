# Choosing a material

The numbers (temps, density) live in `materials.toml`, which the checker reads.
This page is about which one to pick on our **Flashforge AD5X**, which is
open-frame (no enclosure).

| Use | Pick | Why |
|-----|------|-----|
| Indoor prototype, fit test, scale model | **PLA** | Cheapest, easiest, crisp detail |
| Hardware on a shed (latches, vents, brackets) | **PETG** | Tough, handles weather |
| Parts in full sun all day (signs, trim, lot displays) | **PETG**, painted or UV-stabilized | ASA is the best for sun, but needs an enclosure. The AD5X has none (see below) |
| Bumpers, door stops, feet, gaskets | **TPU** | Flexible. Feed it straight into the extruder, **not through the IFS** |
| Stiff brackets, jigs | **PLA-CF / PETG-CF** | Stiffer than plain. Flashforge supports these on the AD5X |

Rules:

- **Never PLA outside or in a closed shed.** It softens around 55 °C. A shed in summer gets hotter than that.
- Prototype in PLA to check the fit, then print the real part in PETG. PETG shrinks a little more than PLA, so re-check tight fits.
- **ASA/ABS on the AD5X:** the hotend and bed get hot enough, but with no enclosure, parts bigger than about 50 mm tend to warp and split between layers. Only use them for small parts, with a draft shield or an aftermarket enclosure. Otherwise use PETG.
- **Multi-color (IFS):** all colors in one print should be the same material. PLA and PETG don't bond to each other well.
- Keep PETG and TPU dry. Wet filament strings, pops and prints weak. Dry PETG at 65 °C for 6 h right before printing (see `lessons-learned.md`).
- PETG goes on the textured PEI plate. On smooth PEI it can tear the sheet unless you put down glue stick first.
