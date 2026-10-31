# 8x12 Side Utility model — read me first

A 1:24 model of the shop-standard 8x12 Side Utility (one inch on the model = two feet on
the real building). Half the roof lifts off so you can see the framing inside, and the
48 in wooden door swings open on two small pins.

Sizes come from the 3D designer's shop numbers: 7 ft 9 1/2 in walls, 5/12 roof, 4 in
eaves, 48 1/4 x 76 1/2 in door opening centred on the long side, a 2x3 window centred
between the door and each end wall, louvred vents in both gable ends, two 4x6 skids.

| | |
|---|---|
| Footprint | 102 x 152 mm (4 x 6 in) |
| Height on its skids | about 134 mm |
| Windows | open, no glass, so you can look in through them |
| Inside you can see | studs 16 in apart, king and jack studs, headers, rough sills, cripples, double top plate, gable-end studs and truss, floor sheet seams |

## What to print, in this order

Open these in Orca-Flashforge. Each one is a plate that's already laid out.

| File | What's on it | Filament | Notes |
|---|---|---|---|
| `1 fit test.3mf` | A short doorway and door, a roof peg and a bit of roof | Any | **Print this first.** See "Checking the fit" below. |
| `2 body and door.3mf` | The body (floor frame, floor, walls, windows and trim in one piece) and the door beside it | White PLA | The body stands up on its floor joists. Turn on a **5 mm brim**. No supports needed. The door lies flat, trim side up. |
| `3 roof and skids.3mf` | Two roof halves, two skids | Black PLA | Roof halves print flat with the ribs up. |

The `.stl` files are the same parts one at a time, if you'd rather set up a plate yourself.

**Settings:** `0.20mm Standard @FF AD5X` is fine. Set **Wall generator → Arachne**: the
siding is only 1.4 mm thick, and Arachne fills thin walls solid.

**Trim:** the corner boards, door and window casings, gable bands and the trim on the
door (frame, middle rail, clipped corners, handle) stand 0.6 mm proud of the siding, so a
black paint pen follows them easily. Printing them
black in the same print would mean a colour change on almost every layer.

## Checking the fit

Before you start the long body print:

1. Put the little door in the little doorway the same way as the real one (step 2 below).
   It should swing out freely and stop against the inside of the latch side so it can't
   swing in.
2. Set the bit of roof on the peg. It should drop on and lift off without forcing.

Holes are already 0.35 mm bigger than their pins and 0.4 mm bigger than the pegs all round.
If either is too tight or too loose, ask Claude to change the pin hole or peg hole size
by 0.1 mm and remake the files. The sizes are at the top of `make_shed.py`.

## Putting it together

1. **Skids.** Set the body on the two skids so the floor joists drop into the notches.
   A drop of glue holds them.
2. **Door.** Hold the door with its bottom tipped out a little. Push the top pin up into
   the hole above the opening, swing the bottom in so its pin slides along the small slot
   in the floor, then let it drop into its hole. To take it off, lift it slightly and tip
   the bottom out.
3. **Roof.** Set each half on the gable ends so the two pegs at each end go into the holes
   underneath. Either half lifts straight off. Glue the back half down if you only want
   the door side to come off.

## Changing it

Everything is made by `make_shed.py` from the numbers at the top of the file (building
size, wall height, pitch, door and window positions, clearances). `check_shed.py` then
proves the parts still fit: the door swings to about 98 degrees and won't swing in, each
roof half rests on the gable ends and is held by its pegs, and the skids fit under the
joists. To make a different size or style, ask Claude to change the numbers and run both.
