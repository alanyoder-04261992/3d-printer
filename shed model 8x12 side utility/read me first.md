# 8x12 Side Utility model — read me first

A 1:24 model of the shop-standard 8x12 Side Utility (one inch on the model = two feet on
the real building). The walls snap onto the floor with no glue, and a black corner angle is
glued over each corner. Half the roof lifts off so you can see the framing inside, and the
48 in wooden door swings open on two small pins.

Sizes come from the 3D designer's shop numbers: 7 ft 9 1/2 in walls, 5/12 roof, 4 in
eaves, 48 1/4 x 76 1/2 in door opening centred on the long side, a 2x3 window centred
between the door and each end wall, louvred vents in both gable ends, two 4x6 skids.

| | |
|---|---|
| Footprint | 102 x 152 mm (4 x 6 in) |
| Height on its skids | about 136 mm |
| Windows | open, no glass, so you can look in through them |
| Inside you can see | studs 16 in apart, king and jack studs, headers, rough sills, cripples, double top plate, gable-end studs and truss, floor sheet seams |

## What to print, in this order

| File | What's on it | Filament | Time on the AD5X |
|---|---|---|---|
| `1 fit test.3mf` | Two plates. **Plate 1, new corner:** one short corner of the shed (a bit of floor and short pieces of the door wall and end wall, with the recesses for the corner angle) and a 20 mm stub of corner angle. **Plate 2:** a short doorway and door, a roof peg and a bit of roof, the same as before. | Any, one colour | plate 1 about 19 min, plate 2 about 9 min. **Print this first.** See "Checking the fit" below. If you printed the doorway and peg test before, only plate 1 is new. |
| `2 all plates.3mf` | Everything else, one plate per print: | | |
| plate 1 | Both long walls | 1 white, 2 black | about 2 h 35 min, 1 colour change |
| plate 2 | Both roof halves and the four corner angles | 2 black only | about 1 h 10 min |
| plate 3 | The door | 1 white, 2 black | about 22 min, 3 colour changes |
| plate 4 | Both end walls | 1 white, 2 black | about 2 h 7 min, 1 colour change |
| plate 5 | The floor and both skids | 3 brown only | about 1 h 27 min |

Start Flash Studio first, then open them with **File → Open Project** (Ctrl+O), or **Open
Project** on its Home page. Starting Flash Studio by opening the file itself can leave it stuck
on "Loading". If Flash Studio says the file is from a newer version, click OK; it loads fine. If
it asks about unsaved changes to your settings, click **Discard** (the file brings its own). The
files carry their settings: the Flashforge AD5X 0.4, `0.20mm Standard @FF AD5X`, and three
filaments, 1 white, 2 black and 3 brown. Pick a plate, then Slice plate and Print plate as usual.

Each wall prints lying flat, inside face down, so its trim (door and window casings, gable
bands) is on top and already set to **filament 2**; the siding is filament 1. Filament 1
(white) is the siding on every plate, filament 2 (black) the trim, the roof and the corner
angles, and filament 3 (brown) the floor and skids. For other colours, click a filament's
colour square in the Filament panel. When you send the print, match filaments 1, 2 and 3 to
slots 1, 2 and 3 in the AD5X's material station. The prime tower goes in the back
right corner of the plate; every plate is laid out to keep it clear.

The walls meet at the corners on 45-degree mitres. The corner boards aren't printed on the
walls any more: each corner gets a separate black corner angle, printed with the roof halves
and glued on (Alan, Nov 3 2026). So each wall carries only the trim on its own face, all in the
top 0.6 mm. The door wall and the end walls change colour once, for the last three layers, and
the back wall has no black at all. The gable vents stay white, but their louvres are set into
the siding now instead of standing out past it (Alan, Nov 3 2026), so they no longer come up
into the black layers. On the door the black trim sits round the white hinge edge, so that plate
still changes on each of the last three trim layers.

The `.stl` files are the same pieces one at a time, all one colour, if you'd rather set up
a plate yourself (`end wall.stl` serves for both ends, `floor.stl` is already upside down,
`corner angle.stl` has all four angles). For two colours use the `.3mf` files.

**Settings:** already in the file: `0.20mm Standard @FF AD5X` with **Wall generator →
Arachne** (it shows in orange as changed), because the siding is only 1.4 mm thick and Arachne
fills thin walls solid. **Elephant foot compensation** is 0.1 mm, the AD5X's own setting (Quality
tab, under Precision); keep it there: the barbs, stops and posts under the
walls print on the bed and fit with 0.2 mm to spare, and the floor's face with 0.4 mm, so a
flared first layer would make them tight. No supports or brim are needed. The corner angles
are set to no brim in the file: each lies on its outside face, and a brim would leave a lip
along the edge of a board.

**Trim:** it stands 0.6 mm proud of the siding, the corner angles 0.65 mm. If you'd rather print
it all one colour, set every part to filament 1 and use a black paint pen on the raised trim
and the angles.

## How it holds together

- **The walls stand on the floor.** The floor reaches out under each wall, and the wall's
  siding carries on down past the floor as a skirt, hiding the floor's edge.
- **Posts and prongs.** Under every stud a short post drops into a notch in the floor's edge.
  A few prongs go down slots in the floor. Each prong is a springy leg with a barb on its foot:
  going down, the barb pushes the leg out toward the siding; at the bottom it springs back in
  under a ledge with a click. Beside each leg a stiff stop keeps the wall's foot from sliding
  out. The back wall has three prongs, the door wall and each end wall two. Once clicked in, a
  wall's foot can't lift off or slide in, out or along; the corner angles hold the tops.
- **Corner angles.** On the barn the little hooks that tied the tops of the corners snapped and
  the corners stood open a little, so the hooks are gone from both models (Alan, Nov 3 2026).
  Instead each corner has a black L angle glued over it. Each wall has a shallow recess, two
  layers (0.4 mm) deep, down its outside face next to the corner, and the angle sits in the
  recesses of both walls, from the bottom of the skirt to just under the roof. It covers the
  mitre on both faces and, once glued, holds the corner shut from top to bottom. Under it the
  walls' outside corner is cut off at 45 degrees, so neither wall ends in a thin edge. With the
  angles glued, the four walls are one box. That box still unclips from the floor, and the roof
  and door still come off.
- **The angles.** Each leg is 1.05 mm thick and stands 0.65 mm proud of the siding. The leg
  that lay flat on the plate (the flat leg) goes on the long wall; the one that stood up in the
  print (the standing leg, with the long sloping top) goes on the end wall, sloped end up. Two
  are mirror images of the other two, so each fits two corners, diagonally opposite; in Flash
  Studio each is named for one of the corners it fits. There's 0.15 mm round its edges in the
  recesses.
- **Which side is which.** The floor has a door side and a back side. The door side has one long
  notch in the middle of its edge, under the doorway; the back side has a notch for every stud
  and a prong slot in the middle.

## Checking the fit

Before you start the big prints, try the fit test. Plate 1 is the new corner; plate 2 is the
doorway and roof peg, the same as before, so skip it if you've already tried those.

1. **The corner (plate 1).** Set the bit of floor face up on the table. Of the two short wall
   pieces, the end wall is the one with the sloping top; the side with the siding grooves and
   the shallow recess along one edge faces out. Press it straight down onto the floor's short
   edge: its prong should click into its slot with a firm push, and the siding should hang down
   over the floor's edge. Then lower the other piece (the long wall) straight down beside it
   until its prong clicks. The corner should close on its mitre, and neither wall should lift
   off. Hold the corner shut and press the stub of corner angle into the two recesses, flat leg
   on the long wall and its foot on the table. It should go in without forcing and sit flat in
   both recesses without rocking, with a hairline gap along both edges. Don't glue it. If a
   prong won't click, a wall lifts off after clicking, or the stub is tight or rocks, tell
   Claude which.
2. **The door (plate 2).** Stand the little doorway up on its thin (3 mm) bottom edge, the one
   with the little groove running out to the shallow hole, and hang the little door in it the
   same way as the real one (step 1 of "Putting it together"). It should swing out freely and
   stop against the strip inside the right-hand side so it can't swing in.
3. **The roof peg (plate 2).** Stand the peg block up so the peg points up, and set the bit of
   roof on it. It should drop on and lift off without forcing.

Pin holes are already 0.35 mm bigger than their pins, peg holes 0.4 mm bigger than the pegs,
and the snap parts have 0.2 mm round them. Each barb hooks 0.45 mm under its ledge. If anything
is too tight or too loose, ask Claude to change that gap by 0.1 mm (by 0.05 mm for the barbs'
catch, if the prongs won't click or won't hold) and remake the files. The corner angle has
0.15 mm round its edges in the recesses. If the stub is tight, ask Claude to open that gap by
0.05 mm; it can't be made tighter, because then a wall's foot sitting a little in or out would
bind on the angle. The sizes are at the top of `make_shed.py`.

## Cleaning up the parts

- Let the plate cool right down before you flex the parts off. Don't push a scraper under
  the ends of a wall (the mitred ends come to a thin edge on the plate) or under the prongs:
  each prong's leg is a thin strip lifted just off the plate, joined to the wall at the top and
  to its barb at the foot. Flex the plate to free the corner angles too; don't bend them.
- With a fresh hobby knife, take a light chamfer off the first-layer lip (the edge that was
  on the plate) on: the posts, stops and barbs under each wall, the inside edge of the mitre at
  both ends of every wall, the floor's face all round its edge, the door's two pins (so they're
  round), and the mouths of the peg holes under each roof half. A lip on a post, stop or barb
  makes it tight in its slot; a lip round the floor's face rubs on the skirts. Don't scrape the
  mitre faces, and don't trim the barbs' flat tops.
- The corner angles' outside face was on the plate. A lip along its edges sits outside the wall,
  so it doesn't change the fit, but it shows: if you can see one, shave it off with the knife
  held flat.
- Clear any blob or string out of the recesses at the corners of each wall; one stops an
  angle sitting flat.
- Snip any loose strands between the studs on the inside with flush cutters. Don't sand
  the outside; it would fill the siding grooves.
- Cut any strings in the windows at the point where they join, holding the thin window
  bars from behind with a fingertip.
- Lay each wall on glass. If it rocks or a sheet of paper slides under the middle, set the
  bed to 55 °C, lay the wall framing-side down on it under a sheet of paper and a flat board
  with about 1 kg on top, leave it 10 minutes, then let it cool before lifting the weight.

## Putting it together

Glue for the corner angles (and, if they're loose, the skid pegs). You'll need your fingers,
two rubber bands that go round the shed (or painter's tape), gel super glue (or clear contact
cement such as E6000, or 5-minute epoxy), and tweezers or a small flat screwdriver if you ever
unclip it from the floor.
`how it goes together.png` is from before the corner angles (it still shows the hooks, and the
skids going on first), so follow the steps here.

1. **Try the door first, in the loose door wall.** Stand on the outside of the doorway and
   hold the door with the black trim and handle facing you and the pins on the left. The
   longer pin goes at the top. Tip the bottom out, push the top pin up into the hole in the
   left-hand corner of the doorway's head, and **keep pushing the door up** (about half a
   millimetre) while you swing the bottom in, so the bottom pin rides along the little
   groove in the threshold. Then let it drop into its hole. It swings out to about 98
   degrees, where it meets the door casing, and when shut it rests against a thin strip
   inside the right-hand side of the doorway, so it can't swing in. If a pin is tight,
   twist a 2.7 mm drill bit by hand in its hole; never lever the door. Take the door off
   again (lift it a little and tip the bottom out) so the wall is easier to handle.
2. **Floor.** Set the floor face up on a flat table, without the skids; they go on at the end
   (step 8). Standing on the table, the bottom of the floor and the bottoms of the skirts are
   level, so in step 7 each corner angle's foot only has to touch the table.
3. **End walls.** Hold an end wall over one end of the floor, peak up and trim facing out,
   with its siding outside the floor's edge. Line up the posts along its bottom with the
   notches in the floor and its two prongs with their slots, then press straight down on the
   top of the wall above each prong in turn until it clicks. Do the other end the same way. They
   stand on their own, leaning out a little at the top until the corners are glued.
4. **Back wall.** Hold the back wall (the one without the door) over the back side of the
   floor (the side with a notch for every stud), trim facing out, and lower it straight down
   between the end walls, keeping it level: its posts and prongs go into the floor, and its
   mitred ends close against the end walls'. Press down over each of its three prongs (one stud
   bay in from each end, and in the middle) until it clicks.
5. **Door wall.** The same way on the door side; it has two prongs, one stud bay in from each
   end. Check that the floor is level with the doorway threshold.
6. **Pull the corners shut.** Put one rubber band round the walls about 15 mm above the table
   and one about 10 mm under the top of the long walls (or a strip of painter's tape across each
   corner at the same two heights). Push the tops of the end walls in until every mitre is
   closed top to bottom; look down on each corner from above to check.
7. **Corner angles.** Each one goes on with its flat leg on the long wall and its standing leg,
   the one with the long sloping top, on the end wall, sloped end up and its foot on the table.
   If one won't sit that way, it's the mirror one: try it on the next corner. First try all four
   dry: ease the bands out from the corner with a finger, press the angle into its two recesses
   and let the bands back over it. (With tape, peel that corner's strips back, press the angle
   in, and tape back over it.) It should sit flat in both recesses with a hairline gap along
   both edges. Then glue them one at a time: take the angle out and put 3 or 4 small dots of gel
   super glue in a row down each recess floor. The floors are only about 2 mm wide, so keep the
   dots in the half nearest the corner: at least 1 mm in from the recess's outer edge (the side
   where the hairline gap shows) and 1 mm from the top and bottom. Glue that spreads toward the
   corner goes into a hidden gap under the angle. Press the angle back in with its foot on the
   table, let the bands (or the tape) back over it and hold it for 20 seconds. Super glue can
   leave a white haze on black plastic where its fumes settle; clear contact cement (E6000) or
   5-minute epoxy can't, and gives you a few minutes to slide the angle into place. Leave the
   bands on for 15 minutes for super glue, an hour for epoxy, or overnight (a full day is
   better) for contact cement, which stays soft for hours; then take them off.
8. **Skids.** Lay the two skids on the table, notches and pegs up, about where they go, and
   lower the shed onto them: the peg at each end of a skid goes into the hole in the solid band
   across each end of the floor, and the joists drop into the notches. The holes put the skids
   in the right place. They are a snug push fit; if they fall out when you pick the shed up, a
   drop of glue on each peg keeps them.
9. **Door.** Hang it the same way as in step 1.
10. **Roof.** Each end wall has a peg on each sloping edge, and each roof half has a hole
    under each end. Set a half ribs up with its raised ridge strip at the peak, so its two
    holes drop over the two pegs on that side. Either half lifts straight off; always lift
    straight up, never slide it along the pegs.

**Taking it apart:** lift off the roof and the door, and lift the shed off its skids. The four
walls are glued into one box now, but it still unclips from the floor. Look underneath: just
inside each wall you can see the barbs in their slots. Push each barb out, toward the siding,
with a small flat screwdriver, only just far enough to clear its ledge (about half a
millimetre; don't lever it hard against the far side of the slot), and ease that bit of wall up
a little. Work round the shed until all nine prongs are free, then lift the walls off together.

## Old files

`all on one.3mf` and `all lay out.3mf` are your own Flash Studio projects of the earlier,
glue-together version. Its walls and floor don't fit these, so don't print from them.

## Changing it

Everything is made by `make_shed.py` from the numbers at the top of the file (building
size, wall height, pitch, door and window positions, clearances, the snap joints, the corner
angles and their recesses). It writes the `.stl` files and both `.3mf` files. `check_shed.py`
then proves the parts still fit:

- each wall goes on straight down (the end walls first, then the long walls between them) with
  nothing in the way but its barbs, stands on the floor, and its foot can't lift or slide once
  clicked in;
- each corner angle sits on the floors of its two recesses and touches nothing else (0.09 mm
  clear all round, and still clear with either wall's foot 0.15 mm in or out); the same once the
  walls and the angle are cut into their print layers, where the recess floors come out 0.05 mm
  deeper and the cut-off corner and the angle's inside corner come out stepped; it covers the
  corner by 3.6 mm or more on each face (2.6 mm or more past the joint between the walls) from
  the bottom of the skirt up, stays 0.2 mm under the roof (still clear with the roof 0.15 mm
  lower) and clear of the other trim and the door;
- the barbs still catch once the parts are cut into 0.2 mm layers and anything thinner than a
  line is rounded off, and the prong legs bend less than PLA can take;
- the door swings to about 98 degrees and won't swing in; each roof half rests on the gable
  ends and is held by its pegs; the skids fit under the joists;
- each wall and the floor print flat, with nothing steeper than 45 degrees that isn't a bridge
  held at both ends, the walls' trim all in the top 0.6 mm, nothing white above the siding's
  top layer, the gaps between the vents' louvres wider than one line on every layer, the
  recesses two layers deep with no thin edge where the walls meet under the angle, and nothing
  on the bed thinner than one line; the angles print with nothing hanging over;
- every plate's parts are on the bed, 3 mm or more apart, clear of the prime tower.

To make a different size or style, ask Claude to change the numbers and run both.
