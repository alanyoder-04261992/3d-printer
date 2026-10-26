# PETG blade — toughest version. Read this first.

**`1 set collapsible sword blade PETG TOUGH.gcode.3mf`** — same geometry, verified
byte-for-byte identical coordinates, so the telescoping fit is unchanged. ~3 h 21 m.

I was optimising for the wrong thing before. You want **toughness** — survive a hit —
not stiffness. On that measure PETG beats PLA+ by roughly 2x, and your earlier test was
almost certainly measuring a badly-printed PETG rather than PETG itself.

---

## Step 1 — dry the filament. Do not skip this.

This is most likely why your PETG came out weak. PETG pulls moisture out of the air far
faster than PLA. When damp filament hits the nozzle the water flashes to steam and blows
microscopic bubbles through the middle of every extrusion. The part looks fine and is
full of holes. Damp PETG is genuinely weaker than PLA+ — so your test wasn't wrong, it
just wasn't testing PETG.

- Filament dryer: **65 °C for 6 hours**.
- No dryer: put the spool on the printer bed, set the bed to **70 °C**, cover it with a
  cardboard box, leave it 6 hours.
- You'll know it was wet if the old print hissed, popped or crackled while running, or
  came out foggy and stringy instead of glossy.

Print it straight after drying. Don't dry it Monday and print it Friday.

## Step 2 — bed prep

PETG at 80 °C bonds *very* aggressively to smooth PEI and can tear chunks out of the
sheet. Use the **textured plate** if you have it. If you only have the smooth one, wipe
a thin layer of plain glue stick over the print area first — it acts as a release agent,
not an adhesive.

## Step 3 — print it, then clean the bores

Expect some stringing between the four segments; that's normal for PETG and I've already
bumped the retraction to 1.2 mm to limit it. **Check inside each tube and pull out any
webs before you assemble the sword**, or the segments will bind when they collapse.

---

## What I changed and why

| | PLA original | PETG version | Why |
|---|---|---|---|
| Nozzle | 210 °C | 245 °C | This is the one that matters — hot plastic welds deep into the layer below |
| Bed | 60 °C | 80 °C | PETG requirement |
| Part fan | 100 % | 25 % | **The big one.** PETG delaminates with heavy cooling — it needs to stay hot to bond |
| Aux blower | 100 % | off | Same |
| Speed | up to 81 mm/s | 50 mm/s | PETG has less flow headroom, and slow means more heat into the layer below |
| Retraction | 0.8 mm | 1.2 mm | Controls stringing inside the bores |
| Pressure advance | 0.03 | 0.045 | Correct value for PETG on direct drive |
| Flow | 0.98 | 1.00 | |

If your first PETG attempt used anything near a 100 % fan, that alone explains the
result. PLA tolerates being blasted with air. PETG does not.

---

## Where the materials actually rank for impact

Roughly, notched impact strength — how well it survives a hit:

- **PLA** — worst. Shatters.
- **PLA+** — better than PLA, still brittle.
- **PETG** — around 2x PLA+. Bends and dents where PLA cracks. *You already own this.*
- **PCTG** — the upgrade. Prints almost exactly like PETG, noticeably tougher. Worth
  buying if PETG still isn't enough.
- **ABS / ASA** — tougher again, but a 170 mm tall thin-walled part will warp and split
  unless your printer is enclosed and you don't mind the smell. I wouldn't for this.

There's also **PETG-CF** — avoid it here. Carbon fibre makes PETG stiffer but *more*
brittle, which is the opposite of what you want in a sword.

## If it still breaks

The wall is only 0.8 mm — that's the real ceiling, and no material fully solves it.
Two things that will:

1. **Reinforce the tip segment.** Nothing slides inside the smallest one, so its ~10 mm
   bore is free space. Epoxy a 3/8" wooden dowel or a carbon tube up inside it.
2. **Find the original STL** and let me re-slice properly with the Arachne wall
   generator — it lays one solid 0.8 mm bead instead of two thin lines with a seam
   between them. That, plus PETG, is as far as this design goes.
