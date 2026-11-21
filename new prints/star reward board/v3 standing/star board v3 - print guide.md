# Star reward board — v3. Stars stand upright in slots.

You were right again. I had the stars lying flat on the board both times. In the video
they **stand up** — each one is a plate pushed edge-first into a slot, which is why the
empty positions look like long thin capsules rather than holes for a peg.

That one correction changes almost everything, and mostly for the better.

## What's different

| | v2 (wrong) | v3 |
|---|---|---|
| Stars | lying flat, peg into a socket | **standing upright**, tang into a slot |
| Board | 200 × 175 mm | **171 × 110 mm** — a compact bar |
| Board volume | 188 cm³ | 119 cm³ |
| Row spacing | 24 mm | **16 mm** |

The board got much smaller because standing stars only need room for their 4 mm thickness
front-to-back, not their full 22 mm height. Rows can sit closer together than the stars
are tall, so each row partly overlaps the one behind it — which is exactly what makes the
board in the video a chunky little bar instead of a big sheet.

## Files

| File | What | Qty |
|---|---|---|
| `fit_test_v3.stl` | Two slots on a small plate + one star. **Print first.** ~25 min | 1 |
| `star_board_6x6_v3.stl` | The board, 171 × 110 × 8.2 mm | 1 |
| `star_token_v3.stl` | One star | **36** |

## How it goes together

The star prints **lying flat**, then you stand it up and push the tang on its bottom edge
into a slot. It stands 19 mm proud, 23 mm wide, and the bottom of the star sits right on
the board face with the tang hidden inside the slot.

Slots go **all the way through** the board — nothing has to bridge, and it means the board
only needs to be 7 mm thick to give the tang a full 6.8 mm of grip.

## Print the fit test first

Push the star's tang into a slot.

- **Firm push, stands up straight, doesn't flop** → perfect.
- **Won't go in / needs force** → scale the *star* to 99 %.
- **Falls over or rattles** → scale the *star* to 101 %.

Tang is 4.0 × 13.0 mm, slot is 4.4 × 13.4 mm — **0.2 mm of slack per side**. That's a
deliberately snug fit, because a standing star needs to actually stand.

Only ever scale the star, never the board.

## Settings

Plain PLA. Layer height 0.2 mm, 3 walls on the board and 2 on the stars, 10–15 % infill,
supports **off**, brim on the board.

Neither part has a single overhang. The star lies flat with the dome facing **up**, so every
layer is smaller than the one below it and the puffy face you look at is the top surface —
the best finish your printer can give. The board is a flat plate with through-slots.

Stars in yellow, board in orange or red, and it'll look like the video.

Rough numbers: board **~5 hours and 60 g**, the 36 stars **~4–5 hours and 55 g**.

## Checks I ran

- Star seated in **all 36 slots**: zero interference, every one.
- Tang sits flush with the underside — nothing pokes out the bottom.
- Neighbouring stars in the same row: no collision. Star in the row in front: no collision.
- Wobble is under about 1° — it stands essentially straight rather than flopping.
- Eye recesses confirmed as real 1.0 mm oval dishes that follow the dome.
- Both meshes watertight.

Two things I caught and fixed while building this, in case it's useful: the star's lower
arms are up to 6 mm thick where the dome swells, so at first they jammed in a 4.4 mm slot —
everything below the board line is now clipped off and the uniform 4 mm tang is the only
part that enters. And the tang's ends are square while my first slot was a rounded stadium,
which pinched all four corners.

## Board details

- 171 × 110 mm, 7 mm plate with a 1.2 mm raised border.
- 6 rows of 6 slots. 24 mm between stars across a row, 16 mm between rows.
- Blank 18 mm band along the front — good for a label or a strip of vinyl.
- No hanging holes: with the stars standing up this is a desk or shelf piece, same as the
  video. Say the word if you'd rather have it on a wall and I'll rework the retention.

Still fully parametric. Rows, star size, hearts instead of stars, eyes on or off, engraved
numbers along the front — all quick changes.
