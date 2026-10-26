# Star reward board — v2, rebuilt

You were right, and there were two things wrong with the first version:

1. **The star was a flat cookie-cutter plate.** The video's stars are puffy domed
   pillows with eyes. Mine was a 3 mm slab with hard 90° edges.
2. **A real bug I should have caught:** the sliding foot underneath was wider than the
   star at its narrow points, so it stuck out past the star's outline at 3 and 9 o'clock.
   You'd have seen two little tabs poking out of the front of every star.

## What changed

The stars now **lift and place** into positions instead of sliding along a track. That
swap is what makes the domed star possible at all — with a sliding foot hanging
underneath, the star is forced to stay a flat plate. Now:

- **Star** prints flat-back-down, **dome up**. Every layer is smaller than the one below
  it, so there is not a single overhang in the part, and the puffy face you actually look
  at is the top surface — the best finish your printer can produce.
- **Board** prints flat with the pegs standing up. Pegs are just little towers.

**No supports anywhere, on either part.**

Each board position is a **capsule-shaped peg**; each star has a matching capsule socket
in its back. Capsule and not round on purpose — a round peg would let stars spin, a
capsule keeps every one of them pointing up.

## Files

| File | What | Qty |
|---|---|---|
| `fit_test_v2.stl` | Two pegs on a small plate + one star. **Print first.** ~25 min | 1 |
| `star_board_6x6_v2.stl` | The board, 200 × 175 × 7.8 mm | 1 |
| `star_token_v2.stl` | One star, 23 × 22 × 6.2 mm | **36** |

## Print the fit test first

Drop the star onto a peg. Peg is 4.5 × 10.5 mm, socket is 5.0 × 11.0 mm — **0.25 mm of
slack per side**, which should be a clean drop-on with no wobble.

- **Drops on, sits flat, doesn't rock** → perfect, print the rest.
- **Too tight** → scale the *star* to 101 %.
- **Wobbles** → scale the *star* to 99 %.

Only ever scale the star, never the board, so one test stays valid.

## Settings

Plain PLA, nothing special. Layer height 0.2 mm, 3 walls on the board and 2 on the stars,
10–15 % infill, supports **off**, brim on the board.

Print the stars in yellow and the board in orange or red and it'll look like the video.

**Be warned, this is a chunky project:** the board is roughly **8–10 hours and ~85 g**,
and the 36 stars another **3 hours and ~40 g**. If that's more than you want, I can shrink
the board or cut it to 4 rows in a couple of minutes — just say. You can also print six
stars first to see how they look before committing to all 36.

## Checks I ran before sending

- Star seated on the peg at **all 36 positions**: zero interference, every one.
- Star's back sits flat on the board with 0.20 mm of depth to spare — it won't perch on
  the peg tip.
- Eye recesses confirmed present as real 1.0 mm oval dishes (they follow the curve of the
  dome instead of being flat-bottomed, which would have left crescent shapes).
- 6.0 mm clear between stars along a row, 2.0 mm between rows — nothing collides.
- Both meshes watertight.

## Board details

- 200 × 175 mm, 5 mm plate with a 1.5 mm raised border, pegs 2.8 mm tall.
- Two 4.5 mm holes in the blank top band for screws or nails.
- The blank band is there on purpose — good spot for a label or a strip of vinyl.
- Stars stand 6.2 mm proud, so they're easy to pick up even for small fingers.

Everything's parametric on my end. Number of rows, star size, hearts instead of stars,
eyes or no eyes, engraved numbers down the side — all quick changes.
