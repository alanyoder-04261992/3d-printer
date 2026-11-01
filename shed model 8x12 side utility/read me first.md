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

The four walls and the floor are separate pieces. Each wall prints lying flat, inside face
down, so the trim (corner boards, door and window casings, gable bands, and the trim on the
door) is a separate part on top, already set to **filament 2**. The siding is filament 1.

Import these in Flash Studio with **File → Import** (Ctrl+I). Each one is a plate that's
already laid out. Flash Studio says the file is from a newer version: click OK, it loads fine.
The files carry no printer settings, so the printer stays the Flashforge AD5X 0.4.

| File | What's on it | Filament | Time on the AD5X |
|---|---|---|---|
| `1 fit test.3mf` | A short doorway and door, a roof peg and a bit of roof | Any | **Print this first.** See "Checking the fit" below. |
| `2 door wall and door.3mf` | The door wall and the door | 1 white, 2 black | about 2 h 15 min, 25 colour changes |
| `3 back wall and floor.3mf` | The back wall and the floor | 1 white, 2 black | about 3 h 5 min, 28 colour changes |
| `4 end walls.3mf` | Both gable ends | 1 white, 2 black | about 1 h 55 min, 3 colour changes |
| `5 roof and skids.3mf` | Two roof halves, two skids | Black only | Roof halves print flat with the ribs up. |

**Two colours:** add a second filament in the Filament panel before slicing (the **+** next
to Filament), and make it black, or whatever colour you want the trim. When you send the
print, match filament 1 and 2 to the right spools in the AD5X's material station. The back
right corner of each plate is kept clear for the prime tower.

Only the top three layers of each wall have trim on their faces. The long walls also carry
the corner boards for the gable ends standing up along each end, which is why plates 2 and
3 change colour on most layers.

The `.stl` files are the same pieces one at a time, all one colour, if you'd rather set up
a plate yourself (`end wall.stl` serves for both ends). For two colours use the `.3mf` files.

**Settings:** `0.20mm Standard @FF AD5X` is fine. Set **Wall generator → Arachne**: the
siding is only 1.4 mm thick, and Arachne fills thin walls solid. No supports or brim are
needed: the siding between the studs prints as short bridges.

**Trim:** it stands 0.6 mm proud of the siding. If you'd rather print it all one colour, set
every part to filament 1 and use a black paint pen on the raised trim.

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

1. **Floor and skids.** Set the floor on the two skids so the joists drop into the notches,
   and glue them.
2. **Walls.** Stand the four walls round the floor: the long walls along its sides, the end
   walls between them with their bottoms down in the notches at the ends of the skids. Glue
   the corners and the walls to the edge of the floor. The floor fits inside with 0.15 mm
   all round, and its top lines up with the bottom of the door opening.
3. **Door.** Hold the door with its bottom tipped out a little. Push the top pin up into
   the hole above the opening, swing the bottom in so its pin slides along the small slot
   in the floor, then let it drop into its hole. To take it off, lift it slightly and tip
   the bottom out.
4. **Roof.** Set each half on the gable ends so the two pegs at each end go into the holes
   underneath. Either half lifts straight off. Glue the back half down if you only want
   the door side to come off.

## Changing it

Everything is made by `make_shed.py` from the numbers at the top of the file (building
size, wall height, pitch, door and window positions, clearances). `check_shed.py` then
proves the parts still fit: the door swings to about 98 degrees and won't swing in, each
roof half rests on the gable ends and is held by its pegs, and the skids fit under the
joists. To make a different size or style, ask Claude to change the numbers and run both.
