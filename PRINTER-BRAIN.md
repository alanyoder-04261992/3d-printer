# Printer Brain

Everything about our 3D printing setup in one place: the printer, the slicer, the
filament, the settings that work, and what we've learned the hard way.
**Keep it up to date** — when something changes or a print teaches us something, add it here.

_Last updated: 2026-10-31_

---

## The printer

| | |
|---|---|
| Printer | **Flashforge AD5X** |
| Colour system | IFS 4-spool multi-colour feeder |
| Build volume | **220 × 220 × 220 mm** |
| Nozzle fitted | **0.4 mm** (0.25, 0.6 and 0.8 mm profiles are also installed in the slicer) |
| Build plates | **Textured PEI** (used for almost everything), High Temp Plate (used a few times) |
| Firmware | 3.1.5 (update file `AD5X-3.1.5-…-20260626.tgz` is on the flash drive, not in this repo) |

## The slicer

| | |
|---|---|
| Software | **Orca-Flashforge** v01.10.01.50 |
| Printer profile | `Flashforge AD5X 0.4 nozzle` |
| Usual print profile | `0.20mm Standard @FF AD5X` (129 of 134 files) |
| Saved custom presets | **None yet.** Everything uses the built-in profiles. |
| Settings folder | `%APPDATA%\Orca-Flashforge` (custom presets would go in `user\`) |

### What the stock profile actually does
Pulled from the settings saved inside our print files:

| Setting | Stock value |
|---|---|
| Layer height | 0.20 mm |
| Walls | 2 |
| Infill | 15 % grid |
| Wall generator | Classic |
| Seam | Aligned |
| Part cooling fan | 100 % |
| Aux side blower | 70 % (some profiles 100 %) |
| Outer wall speed | 200 mm/s |
| Acceleration | 10 000 mm/s² |
| Retraction | 0.8 mm |
| Brim | Auto |
| Supports | Off by default (turned on for 29 files) |

---

## Filament we use

Temperatures are the ones we've actually printed with.

| Filament (slicer preset) | Nozzle | Bed | Notes |
|---|---|---|---|
| Generic PLA | 220 °C | 55 °C | The everyday default. Most-used colours: teal `#26A69A` and black. |
| Flashforge PLA Pro (PLA+) | 210 °C | 60 °C | |
| Generic / Flashforge PLA Silk | 230 °C | 55–60 °C | Helmets, book covers, catapult legs |
| Generic PLA Matte | 220 °C | 55 °C | Vases, army men, knife handle |
| Flashforge PLA Color Change | 220 °C | 55–60 °C | |
| Generic PLA High Speed | 220 °C | 55 °C | |
| Generic TPU (flexible) | 240 °C | 35 °C | iPhone 15 Pro case, airless ball, TPU knife blade |
| PETG | 245–255 °C | 80 °C | Sword blades. **Dry it first** — see below. |

**Still to fill in:** which colours are loaded in the IFS slots right now, and what spools are
on the shelf.

---

## Lessons learned

### Strong parts (anything that bends, flexes or gets hit)
The stock profile runs cool with both fans at full blast. That's fine for looks and terrible
for strength, because the layers don't weld together. For swords, springs and toys that get
played with, change these:

| | Stock | Strong PLA | Tough PETG |
|---|---|---|---|
| Nozzle | 210–220 °C | **230 °C** | **245 °C** |
| Bed | 55–60 °C | 60 °C | **80 °C** |
| Part fan | 100 % | **40–50 %** | **25 %** |
| Aux blower | 70–100 % | **off** | **off** |
| Speed | up to 200 mm/s | **60 mm/s** | **50 mm/s** |
| Acceleration | 10 000 | **3 000** | 3 000 |
| Flow | 0.98 | 1.02 | 1.00 |
| Retraction | 0.8 mm | 0.8 mm | **1.2 mm** |

- **Wall generator → Arachne** for thin walls (anything 0.8–2.5 mm). Classic leaves a hairline
  gap down the middle of thin walls; Arachne fills them solid.
- **Seam → Random or Scarf joint** on tall thin parts, so the seam doesn't form a weak vertical line.
- **PETG beats PLA/PLA+ for impact**, roughly 2×. PCTG is the next step up. Avoid PETG-CF for
  anything that needs to survive a hit — it's stiffer but more brittle.

### PETG
- **Dry it before every print:** 65 °C for 6 h in a dryer, or on the bed at 70 °C under a
  cardboard box for 6 h. Wet PETG hisses and pops, comes out foggy and stringy, and is
  weaker than PLA.
- Use the **textured plate**. On smooth PEI it can tear the sheet, so put glue stick down
  first as a release layer.
- Expect stringing. Clean the webs out of hollow parts before assembling them.

### Fit and clearance
- Print a **fit test** before any long print with sliding or snap parts.
- **0.2 mm per side** = snug (stars stood firm but were tight). **0.25–0.3 mm per side** = easy
  fit. 0.4 mm = loose.
- If a fit is off, **scale the small part** (the star or the blade) by 1 % at a time, never the
  big part it fits into.
- **Holes print small.** For a pin or peg that goes into a hole, make the hole at least
  **0.35–0.4 mm bigger all round** than the pin (Alan, Oct 2026).

### Bed adhesion
- Long, thin parts or parts with a small footprint need a **5 mm brim** (knife handle, sword
  blade, star board).
- Tall thin parts: keep the bottom few layers solid so the part has something to hold the bed with.

---

## Project index

| Folder | What's in it | Notes |
|---|---|---|
| `collapsible blade/` | Telescoping sword: blade, handle, cap | Read `blade strength notes.md`, `PETG blade - read before printing.md`, `tip rework notes.md` |
| `knife/` | OTF fidget knife, sheath, TPU blade | `read me first.md`, `OTF knife - PLA+ print guide.md`. Model licence CC BY-NC-SA: OK to print, not to sell. |
| `new prints/star reward board/` | Kids' star reward board, v1–v4 | v4 (7 × 2, 0.3 mm slots) is the current one and uses the v3 stars |
| `new prints/` | Voronoi vase, eclipse bloom vase, army men | PLA / matte / silk versions |
| `3d print guns/` | Toy shooters: toothpick, rubber band, disc | |
| `calpalt/` | Macshay catapult | |
| `tiny book/` | Tiny book covers and pages (sets of 20) | |
| `paw key chain/` | Animal paw key chains (sets of 20) | 2-colour |
| `snake and d/` | Articulated snake, dragon egg fidget | Biggest jobs: 4 dragon eggs ≈ 24 h |
| `flying prop/` | Flying propeller toy | |
| `test print/` | Sword blade PLA vs PETG tests | |
| `desktop prints/` | Project files (.3mf) and big STLs | The 4 biggest STLs are stored with Git LFS |
| `shed model 8x12 side utility/` | 1:24 model of the 8x12 Side Utility: body, two lift-off roof halves, opening door, skids | Read `read me first.md`. Print `1 fit test.3mf` first. Made by `make_shed.py`; `check_shed.py` proves the parts fit |
| Top level | Piggy banks, mushrooms, Mandalorian helmet, Connect 4, latches, iPhone case, vase | |

**File naming:** Orca names sliced files `name_FILAMENT_time.gcode.3mf`. A file ending in
`.gcode.3mf` is sliced and ready to send to the printer. A plain `.3mf` is a project file
you open in Orca to edit.

---

## Print log

Add a line after each print worth remembering, good or bad.

| Date | Print | Filament | Result / what to change next time |
|---|---|---|---|
| | | | |

---

## How this folder works

- This folder lives at `Documents\3D Prints` and is backed up to GitHub:
  https://github.com/alanyoder-04261992/3d-printer (**public**).
- To save changes: open **GitHub Desktop**, type a summary, click **Commit to main**, then
  **Push origin**.
- Files over 100 MB must go through Git LFS. Ask Claude to set that up before committing one.
- The flash drive (E:) is a separate copy. New prints saved there need copying into this folder.
