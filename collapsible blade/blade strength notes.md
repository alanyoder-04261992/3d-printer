# Collapsible sword blade — why it snaps, and how to fix it

## What I found inside your sliced file

I pulled apart `1 set collapsible sword blade_PLA_2h14m.gcode.3mf` and measured the
actual toolpaths. Three things are working against you:

**1. The blade wall really is paper-thin.** Each segment is a hollow tube with a wall
of about **0.8 mm** — literally just two lines of plastic side by side, with nothing in
between. I checked all 850 layers: there is not a single "inner wall" extrusion in the
whole print. Your wall count is set to 2, but the model is too thin for the slicer to
fit a second pair of loops, so raising that number does nothing. This is a limit of the
model, not your settings.

**2. The layers were barely being welded together.** This is the big one. The nozzle
was at 210 °C, the part-cooling fan was at **100 % on every single layer**, and the
auxiliary side blower was also at 100 %. Each layer had ~9 seconds to cool with two
fans on it before the next layer landed. By the time the new layer arrived, the one
below was cold, so they never properly fused. A 170 mm tall tube built out of 850
weakly-glued rings snaps along a layer line the first time you bend it.

**3. The seam is stacked in one place.** Seam position was set to "aligned", which puts
the start/stop point of every layer at the same spot. On a wall that's only two lines
thick, that's 850 tiny weak points stacked into a vertical perforated line running the
full length of the blade. Have a look at your broken piece — I'd bet the crack starts
there.

---

## The file I made you

**`1 set collapsible sword blade STRONG_PLA.gcode.3mf`** — drop it on the AD5X and print.

I rewrote the print instructions without touching a single coordinate. I verified this:
every X, Y and Z value is byte-for-byte identical to your original, so **the telescoping
fit is exactly the same** — the segments will still slide together the way they do now.

| | Before | Now | Why |
|---|---|---|---|
| Part cooling fan | 100 % | 40 % | Layers stay hot enough to actually weld |
| Aux side blower | 100 % | off | It was quenching every layer |
| Nozzle | 210 °C | 230 °C | Hotter plastic diffuses deeper into the layer below |
| Print speed | up to 81 mm/s | 60 mm/s | More heat transferred into the previous layer |
| Flow | 0.98 | 1.02 | Closes the tiny void running down the middle of the wall |
| Acceleration | 10 000 | 3 000 | Steadier pressure, no thin spots at corners |
| Print time | 2 h 14 m | ~2 h 49 m | The cost |

Two things to watch on the first run:

- **Stringy webs between the four segments?** Drop the nozzle to 225 °C.
- **Top few centimetres looking rough or droopy?** Bump the fan back up to 60 %.

Everything else should look the same, just tougher.

---

## When you re-slice it yourself (bigger wins)

These need the original model file, and they'll beat what I could do to the sliced file.
All of them are in Orca-Flashforge:

**Switch the wall generator to Arachne.** *Quality → Wall generator → Arachne*
(yours is on "Classic"). This is the single best free change. Classic mode jams two
0.42 mm lines into your 0.8 mm wall and leaves a hairline gap down the middle. Arachne
recognises a thin wall and lays down **one solid 0.8 mm line** instead — no internal
seam, no gap. Same plastic, noticeably stronger.

**Change the seam to Random or Scarf joint.** *Quality → Seam position*. Kills the
vertical zipper line described above. Scarf joint is best if your version has it.

**Then apply the same numbers from the table** — 230 °C, 40 % fan, aux fan off,
60 mm/s walls, 1.02 flow, 3000 acceleration.

---

## If it still breaks

At 0.8 mm walls you are fighting physics, and PLA is a brittle plastic. Two real fixes:

**Print it in PETG instead of PLA.** Biggest improvement available to you. PETG bends
where PLA cracks — for something that gets swung around, it's the right material. Print
it at 240 °C, bed 80 °C, fan 30 %. It'll come out slightly less crisp and the segments
may need a bit of sanding to slide freely, but it won't shatter.

**Or fit a 0.6 mm nozzle.** Then the 0.8 mm wall prints as one fat line at 0.6 mm wide
plus a bit of overlap — thicker, fully fused, and faster too.

One last option that costs nothing: after printing, run a thin bead of superglue
(cyanoacrylate) down the inside of each blade segment and let it wick along the wall. It
soaks into the layer lines and stiffens the tube considerably. Ugly, effective, and it
won't affect the outside diameter.

---

*Your handle file (`1h53m`) has the same temperature, fan and seam settings, so it's
worth applying the same changes there. The handle is a chunkier part though, so it's
much less likely to be your failure point — say the word and I'll do that file too.*
