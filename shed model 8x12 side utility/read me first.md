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
| `2 door wall and door.3mf` | The door wall and the door | 1 white, 2 black | about 1 h 55 min, 15 colour changes |
| `3 back wall and floor.3mf` | The back wall and the floor | 1 white, 2 black | about 2 h 20 min, 4 colour changes |
| `4 end walls.3mf` | Both gable ends | 1 white, 2 black | about 2 h, 3 colour changes |
| `5 roof and skids.3mf` | Two roof halves, two skids | Black only | Roof halves print flat with the ribs up. |

**Two colours:** add a second filament in the Filament panel before slicing (the **+** next
to Filament), and make it black, or whatever colour you want the trim. When you send the
print, match filament 1 and 2 to the right spools in the AD5X's material station. The back
right corner of each plate is kept clear for the prime tower.

The walls meet at the corners on 45-degree mitres, so each wall carries only the trim on its
own face, corner boards included, and all of it is in the top 0.6 mm: the colour only
changes on the last three layers. On plate 2 the door's trim and its pull handle sit lower
than the wall's top, which adds the other changes.

The `.stl` files are the same pieces one at a time, all one colour, if you'd rather set up
a plate yourself (`end wall.stl` serves for both ends). For two colours use the `.3mf` files.

**Settings:** `0.20mm Standard @FF AD5X` is fine. Set **Wall generator → Arachne**: the
siding is only 1.4 mm thick, and Arachne fills thin walls solid. Set **Elephant foot
compensation** to 0.1 mm (Quality tab, under Precision): the walls' first layer is the
inside edge of every mitre, and a flared first layer holds the corners open. No supports or
brim are needed: the siding between the studs prints as short bridges.

**Trim:** it stands 0.6 mm proud of the siding. If you'd rather print it all one colour, set
every part to filament 1 and use a black paint pen on the raised trim.

## Checking the fit

The fit test prints lying flat, the same way as the walls, so its pin holes and peg come out
the way the real ones will. Before you start the wall prints:

1. Stand the little doorway up on its thick bottom edge and hang the little door in it the
   same way as the real one (step 1 of "Putting it together"). It should swing out freely
   and stop against the strip inside the right-hand side so it can't swing in.
2. Stand the peg block up so the peg points up, and set the bit of roof on it. It should
   drop on and lift off without forcing.

Holes are already 0.35 mm bigger than their pins and 0.4 mm bigger than the pegs all round.
If either is too tight or too loose, ask Claude to change the pin hole or peg hole size
by 0.1 mm and remake the files. The sizes are at the top of `make_shed.py`.

## Cleaning up the parts

- Let the plate cool right down before you flex the parts off. Don't push a scraper under
  the ends of a wall: the mitred ends come to a thin edge with the black trim on top.
- With a fresh hobby knife, take a light chamfer off the first-layer lip (the edge that was
  on the plate) on: the bottom edge of every wall, the inside edge of the mitre at both ends
  of every wall, the floor's bottom edge all round, the door's two pins (so they're round),
  and the mouths of the peg holes under each roof half. A lip under a wall tips it out of
  plumb; a lip on the floor eats its 0.15 mm clearance. Don't scrape the mitre faces.
- Snip any loose strands between the studs on the inside with flush cutters. Don't sand
  the outside; it would fill the siding grooves.
- Cut any strings in the windows at the point where they join, holding the thin window
  bars from behind with a fingertip.
- Lay each wall on glass. If it rocks or a sheet of paper slides under the middle, set the
  bed to 55 °C, lay the wall framing-side down on it under a sheet of paper and a flat board
  with about 1 kg on top, leave it 10 minutes, then let it cool before lifting the weight.

## Putting it together

You'll need: a sheet of glass or a smooth tile with baking paper on it, 15- or 30-minute
epoxy (or medium super glue), two rubber bands, a bit of card, masking tape, a hobby knife,
and a small square or a LEGO brick to check the corners.

1. **Try the door first, in the loose door wall.** Stand on the outside of the doorway and
   hold the door with the black trim and handle facing you and the pins on the left. The
   longer pin goes at the top. Tip the bottom out, push the top pin up into the hole in the
   left-hand corner of the doorway's head, and **keep pushing the door up** (about half a
   millimetre) while you swing the bottom in, so the bottom pin rides along the little
   groove in the threshold. Then let it drop into its hole. It swings out to about 98
   degrees, where it meets the door casing, and when shut it rests against a thin strip
   inside the right-hand side of the doorway, so it can't swing in. If a pin is tight,
   twist a 2.7 mm drill bit by hand in its hole; never lever the door. Take the door off
   again (lift it a little and tip the bottom out) before gluing.
2. **Dry fit.** On the glass, set the floor in the middle, joists down. Stand the four walls
   round it with the black trim facing out. The bottom of a long wall is the edge with the
   solid band about 8 mm deep on the inside; the end walls go peak up, vent outside. The
   mitred ends close into square corners. Put a rubber band round the walls about 5 mm up
   and another near the top, with a folded bit of card under each band at every corner so
   it doesn't crush the black corner boards. Check: each corner closes from bottom to top;
   the corner boards and the black bands meet with no step; the floor is level with the
   doorway threshold; both roof halves drop onto their pegs; and the two diagonals across
   the top of the walls measure the same.
3. **Glue the four corners at once**, the way a picture frame is glued; a single mitre
   slides when you press on it. Lay the four walls in a row outside face up (end wall, long
   wall, end wall, long wall) with their bottom edges against a ruler and the outside
   corners touching, and put masking tape across each of the three joints, over the black
   corner boards. Turn the row over. Put epoxy on the inner half of each mitre (the half
   nearest the inside corner) and on the solid part at the bottom, keeping the outer 2–3 mm
   next to the black corner dry. Fold the row up round the floor, tape the fourth corner,
   and put the bands back on with the card under them. Check the corners are square, and
   wipe any squeeze-out with a cotton bud dipped in rubbing alcohol. Keep the floor centred
   with an even gap all round, keep glue off the doorway threshold and the hinge holes, and
   leave it to set (about 2 hours for epoxy). The roof halves can sit on their pegs while
   it sets to hold the gables the right distance apart; don't glue them. With super glue
   instead: tape and band it up dry, then run medium super glue into each inside corner
   from inside the box. Super glue fumes can leave a white haze on the black trim, so keep
   the air moving and keep the roof off until it has cured. Don't sand the mitre faces or
   round off the outside corners: the black is only 0.6 mm thick there.
4. **Glue the floor.** Turn the box on its side and run a little glue from underneath
   along the line where the floor's edge meets the solid bottom of each wall.
5. **Skids.** Lay the two skids on the glass, notches up, ends level, 38 mm apart between
   their inside faces (each about 28 mm in from its long wall's white siding). Put a dab of
   glue in each notch and on the low step at each end, then lower the shed straight down:
   the floor joists drop into the narrow notches and the bottom of each end wall sits on
   the step at the ends. The skid ends finish flush with the end walls. The long walls hang
   just clear of the table; that's right.
6. **Door.** Hang it the same way as in step 1.
7. **Roof.** Each end wall has a peg on each sloping edge, and each roof half has a hole
   under each end. Set a half ribs up with its raised ridge strip at the peak, so its two
   holes drop over the two pegs on that side. Either half lifts straight off; always lift
   straight up, never slide it along the pegs. To fix the back half for good, put a dab of
   glue in its two holes only, away from the ridge.

## Changing it

Everything is made by `make_shed.py` from the numbers at the top of the file (building
size, wall height, pitch, door and window positions, clearances). `check_shed.py` then
proves the parts still fit: the door swings to about 98 degrees and won't swing in, each
roof half rests on the gable ends and is held by its pegs, and the skids fit under the
joists. It also proves each wall lies flat, has nothing steeper than 45 degrees, and has all
its trim in the top 0.6 mm, and nothing on the bed is thinner than one line. To make a
different size or style, ask Claude to change the numbers and run both.
