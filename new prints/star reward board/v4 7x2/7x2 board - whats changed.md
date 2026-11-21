# Star board — 7 wide × 2 deep, looser slots

**`star_board_7x2_v4.stl`** — 179 × 38 × 8.2 mm, 43 cm³. Holds **14 stars**.

## Keep your existing stars

**The star file has not changed.** I only opened up the slots in the board, so
`star_token_v3.stl` is exactly the same part — I checked it vertex for vertex against the
one I sent you. Any stars you've already printed drop straight into this board, and you
just need 14 in total.

## What changed

| | Before | Now |
|---|---|---|
| Layout | 6 × 6 = 36 slots | **7 × 2 = 14 slots** |
| Board | 171 × 110 mm | **179 × 38 mm** |
| Plastic | 119 cm³ | **43 cm³** — a third of it |
| Slot | 4.4 × 13.4 mm | **4.6 × 13.6 mm** |
| Clearance | 0.2 mm per side | **0.3 mm per side** |

### The slots

You said they fit but tight, so I went from 0.2 to **0.3 mm of clearance per side** — half
again as much room. That's a real difference going in without letting the stars flop
about; I checked and a seated star still can't lean more than about a degree.

If it's *still* tight after printing, tell me and I'll take it to 0.4. Don't sand the slots
to fix it — sanding a 4.6 mm slot evenly by hand is miserable, and it's a two-minute change
on my end.

### The wasted space

Most of it was margin around the edges, so I pulled it in:

- **Side margin 14 mm → 6 mm.** The raised rim is 4 mm wide, so 6 mm leaves the outermost
  star 2 mm of daylight over it — any tighter and the star's body would foul the rim.
- **Back margin 12 → 8 mm**, **front band 18 → 14 mm.** The front band is what you grab, so
  I left a bit; there's about 10 mm of flat surface there if you want a label.

I checked all four corner stars against the rim, and every one of the 14 slots against the
tang: zero interference anywhere.

## Printing

Same as before — flat on the bed, **no supports**, brim on. Board is roughly **2–2½ hours
and 25 g**; 14 stars another **1½ hours and 20 g**. Much quicker than the 6 × 6.

`fit_test_v4.stl` is two slots at the new size plus a spare star, about 25 minutes, if you'd
rather check the fit before committing to the board.
