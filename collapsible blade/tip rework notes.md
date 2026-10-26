# Tip segment reworked — hollow, two-line wall, open top

**`1 set collapsible sword blade STRONG_PLA hollow-tip.gcode.3mf`** — drop it on the AD5X.
Keeps all the strength settings from the last file (230 °C, 40 % fan, aux off, 60 mm/s,
1.02 flow). 2 h 49 m → **2 h 55 m**, 46.5 g → **48.7 g**.

## What was wrong

You were right that something was stuffed inside the tip piece, though it wasn't support
material — it was **infill**. That fourth segment wasn't modelled as a tube at all. It was
a solid blade, so the slicer treated it like one:

- **15 % sparse infill on 842 layers** — the criss-cross you were seeing inside it
- **a solid cap over the top** — an internal bridge at layer 845, four solid layers above
  that, and a top surface at 849
- **only one wall line** (0.42 mm), because with infill behind it the slicer didn't need
  a second one

So it was the odd one out in every way. The other three segments are proper tubes with a
0.80 mm wall made of two lines side by side.

## What I changed

| | Before | After |
|---|---|---|
| Inside the tip | 15 % infill, every layer | empty |
| Top of the tip | solid cap, 5 layers | **open** |
| Tip wall | 1 line, 0.42 mm | **2 lines, 0.80 mm** |
| Other 3 segments | — | untouched |

The second wall line is offset **0.381 mm** inside the first. That's not a guess — I
measured the spacing the other three segments actually use (0.380–0.382 mm) and matched
it, so the tip's wall is now 0.80 mm, the same as everything else. Verified at five
heights up the blade; it holds within 0.01 mm.

`tip-before-after.png` shows it: the infill and the cap are gone, and there are now two
concentric wall lines instead of one.

## One thing I did NOT remove

**The bottom 3 layers of the tip are still solid.** That's the only thing holding a
170 mm tall part to the bed — open it up and you're gambling the whole 3-hour print on a
0.8 mm ring of plastic. The other segments get away with it because they're wider and have
more perimeter down there.

If you want it fully open both ends, say so and I'll strip those three layers too. Just
run a brim and watch the first few minutes.

## Checks I ran before sending

- Every X/Y/Z/E value on the other three segments is unchanged — only the on-screen
  time-remaining numbers moved.
- Retract and de-retract counts still balance, so the extruder can't drift.
- No move exceeds the 60 mm/s cap from the strength pass.
- The tip segment now contains only wall lines from layer 3 up — no infill, no bridge, no
  top surface anywhere.
- 850 layers in, 850 layers out; file checksum rewritten so the printer accepts it.

## Worth knowing

The tip is now the **weakest** segment rather than the strongest — it went from a solid
blade to a hollow tube. That's what you asked for and it matches the others, but if the
sword starts breaking at the tip instead of mid-blade, that's why. The dowel trick from
before still applies: nothing telescopes inside the tip, so you can epoxy a rod up it and
it'll be stiffer than the original solid version ever was.
