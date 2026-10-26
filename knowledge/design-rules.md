# Design rules

FDM rules of thumb for a 0.4 mm nozzle at 0.2 mm layers. When a test print
shows our printer needs a different number, change it here and note why in
`lessons-learned.md`.

## Walls and features

| Thing | Minimum | Good default |
|-------|---------|--------------|
| Wall thickness | 0.8 mm (2 perimeters) | 1.6 mm, 2.4+ mm for anything that takes load |
| Floor / roof thickness | 0.6 mm (3 layers) | 1.0–1.2 mm |
| Pin / post diameter | 2 mm | 4 mm+ (thin posts snap along layer lines) |
| Embossed / engraved text | 0.4 mm stroke, 0.6 mm deep | 8 mm tall letters, bold font |
| Gap between separate moving parts | 0.3 mm | 0.4–0.5 mm |

## Tolerances (add to the real size)

Holes print **small** and posts print **large**. Design with these offsets:

| Fit | Add to hole diameter |
|-----|----------------------|
| Press fit (won't come out) | +0.1 mm |
| Snug, by hand | +0.2 mm |
| Slides / rotates freely | +0.3–0.4 mm |
| Loose, screw clearance | +0.5 mm |

## Overhangs and supports

- Up to **45° from vertical** prints clean without support.
- Flat ceilings: bridges up to ~10 mm are fine; past that, add support or redesign.
- Swap flat ceilings for **45° chamfers** or teardrop-shaped holes when holes run horizontal.
- Put a **0.5 mm chamfer on bottom edges** to hide elephant's foot (first-layer squish).

## Strength and orientation

- Parts are weakest **between layers** (pulling along Z). Turn parts so the load runs along the layers, not across them.
- More walls beat more infill. 4 walls + 20% infill is stronger than 2 walls + 50%.
- Round inside corners (fillet ≥ 1 mm) where a part bends under load.
- Screws into plastic: use heat-set inserts (M3 insert → 4.0 mm hole, 5 mm deep) or design for wood screws biting into a 75%-of-diameter pilot.

## Shed hardware sizes

US shed builds mostly use these fasteners. Clearance holes already include tolerance.

| Fastener | Shank | Clearance hole | Head recess |
|----------|-------|----------------|-------------|
| #8 wood screw | 4.2 mm | 4.7 mm | 8.5 mm, 82° countersink |
| #10 wood screw | 4.8 mm | 5.3 mm | 9.8 mm, 82° countersink |
| 1/4" bolt / lag | 6.35 mm | 6.9 mm | 11.5 mm hex (7/16") |
| 5/16" bolt / lag | 7.9 mm | 8.5 mm | 13 mm hex (1/2") |

Lumber is smaller than its name: a 2x4 is 1.5" x 3.5" (38 x 89 mm); a 2x6 is 1.5" x 5.5" (38 x 140 mm).

## Scale models of sheds

Pick the scale so the footprint fits the bed. At 1:24, 1 ft = 12.7 mm; at 1:48, 1 ft = 6.35 mm.

| Building | 1:24 footprint | 1:48 footprint |
|----------|----------------|----------------|
| 8x10 | 102 x 127 mm | 51 x 64 mm |
| 10x12 | 127 x 152 mm | 64 x 76 mm |
| 12x16 | 152 x 203 mm | 76 x 102 mm |
| 12x24 | 152 x 305 mm (split it) | 76 x 152 mm |

At 1:48, trim and siding details under 0.4 mm won't print. Exaggerate them to at least 0.6 mm.
