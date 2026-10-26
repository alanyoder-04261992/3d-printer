# Sliding star reward board — 6 rows × 6 stars

Three files:

| File | What it is | Qty to print |
|---|---|---|
| `fit_test.stl` | Short stub of track + one star. **Print this first.** | 1 |
| `star_board_6x6.stl` | The board, 200 × 148 × 8.5 mm | 1 |
| `star_token.stl` | One star, 18 mm across | **36** (set the quantity in the slicer) |

Everything prints flat on the bed with **no supports**. Every overhang in the design is a
shallow 34° taper, not a square undercut — that's deliberate.

---

## Print the fit test first

This is a 20-minute print that tells you whether the sliding fit is right before you
commit 8 hours to the board. Print it with the exact same settings and filament you'll
use for the real thing.

Drop the star into the square opening at the left end, then slide it along.

- **Slides with a little friction** → perfect. Print the rest.
- **Too tight / won't go in** → in the slicer, scale the *star* to **99 %** and retry.
  Each 1 % is about 0.11 mm off the foot.
- **Rattles around loosely** → scale the *star* to **101 %**.

Only ever scale the star, never the board — that way one test tells you everything.

## Settings

Standard PLA settings are fine. PLA is the right material here; nothing on this part is
load-bearing, so none of the toughness stuff from the sword applies.

- Layer height **0.2 mm**
- Walls **3** on the board (it's 200 mm long and wants the stiffness), 2 on the stars
- Infill **15 %** board, **20 %** stars
- Supports **off**
- Brim helps on the board — it's a big flat part and the corners can lift

Rough expectations on your AD5X: the board is around **7–9 hours and 80 g**, the 36 stars
together around **2–3 hours and 25 g**. Print the stars in a second colour and it looks
like the video.

If the board is more time than you want, drop it to 10 % infill — there's nothing
structural about the middle of it.

## Assembly

1. Each track has a **square loading port** at the left end. Drop a star's foot straight
   down into it.
2. Slide the star to the right and it's captured — it can't lift out anywhere else along
   the track.
3. Repeat 36 times.

To reset the board, slide stars back to the port and lift them out.

## The board itself

- **200 × 148 mm**, 7 mm thick with a 1.5 mm raised border.
- **Two 4.5 mm holes** in the top band for screws or nails if you want it on a wall.
  Otherwise it sits fine on a desk.
- The top band is deliberately blank — good spot for a label strip or a bit of vinyl if
  you want to title it.
- Each row has ~70 mm of free travel with all six stars in it, so a full row of stars can
  sit entirely on the left or entirely on the right.

## How the track works

Cross-section through one row:

```
        <------ 8.0 ------>        slot opening
       |                   |
        \                 /        dovetail taper, ~34° - prints clean, no support
         <---- 12.0 ---->
    ___________________________    2 mm solid floor
```

The star's foot is the same profile 0.4 mm smaller all round. That 0.4 mm is the whole
design — too little and it seizes, too much and it rattles. It's the one number the fit
test is checking.

## Want it different?

Say the word and I can change any of it — more or fewer rows, longer tracks, bigger or
smaller stars, hearts instead of stars, engraved numbers down the side, a slot for a name
card. It's all parametric on my end, so changes are quick.
