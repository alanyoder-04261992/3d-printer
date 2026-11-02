# 8x12 Side Lofted Barn model — read me first

A 1:24 model of the shop-standard 8x12 Side Lofted Barn (one inch on the model = two feet on
the real building). It snaps together with no glue, the same way as the
[8x12 Side Utility model](../shed%20model%208x12%20side%20utility/read%20me%20first.md). The
barn roof comes off in four sheets so you can see the framing and the two lofts inside, and
the 48 in wooden door swings open on two small pins.

Sizes come from the 3D designer's shop numbers for the Side Lofted Barn: 6 ft 7 1/2 in walls
(75 in studs and three 2x4 plates), a barn roof 43 3/4 in from the top of the upper plate to
the peak of the trusses, the eave 1 3/4 in out from the wall, a 4 ft loft at each end, the
48 in wooden door (48 1/4 x 71 1/2 in opening) in the middle of the long side, a 2x3 window
centred between the door and each end, a louvred vent and a trim band across each barn end,
and two 4x6 skids.

The framing is built the way you taught the 3D designer for this barn:

- studs 16 in apart, with a double stud at every 4 ft mark;
- over the door and each window a 5 in loft header (two 2x4s on edge on a flat one) right
  under the top plate, a king stud under each end of it and a full stud beside that;
- under each window a flat window plate on short studs that keep to the 16 in layout;
- on each end wall's upper plate the 2x6 gable board, then gable studs 24 in apart measured
  from the outside of the end wall (the middle one runs up to the peak), and gable backing
  across the gable 11 in above the upper plate;
- the end truss's four chords under the roof line;
- each loft is 2x6 joists 16 in apart on the long walls' top plates, with the loft floor on top;
- the floor is 4x8 sheets, an 8 ft and a 4 ft sheet in each row, the seams staggered.

The end truss also has a collar tie across the knees, as the 3D designer draws barn trusses.

| | |
|---|---|
| Footprint | 103 x 154 mm walls (4 x 6 in), 110 x 158 mm with the roof on |
| Height on its skids | about 147 mm |
| Windows | open, no glass, so you can look in through them |
| Inside you can see | the studs and double studs, loft headers, king studs, window plates, the end trusses, gable board, gable studs and backing, both lofts, floor sheet seams |

## What to print, in this order

| File | What's on it | Filament | Time on the AD5X |
|---|---|---|---|
| `1 fit test.3mf` | A short doorway and door, a roof peg and a bit of roof, and one short corner of the barn (a bit of floor and short pieces of the back wall and an end wall) | Any | about 25 min. **Print this first.** See "Checking the fit" below. |
| `2 all plates.3mf` | Everything else, one plate per print: | | |
| plate 1 | Both long walls | 1 white, 2 black | about 2 h 20 min, 1 colour change |
| plate 2 | The four roof sheets: two upper, two lower | 2 black only | about 1 h 25 min |
| plate 3 | The door | 1 white, 2 black | about 20 min, 3 colour changes |
| plate 4 | Both end walls | 1 white, 2 black | about 2 h 50 min, 3 colour changes |
| plate 5 | The floor, both skids and both lofts | 1 white only | about 2 h 10 min |

The times are worked out from the Side Utility's, which Flash Studio sliced; Flash Studio shows
the real time for each plate when you slice it.

Open them in Flash Studio with **File → Open Project** (Ctrl+O). Flash Studio says the file
is from a newer version: click OK, it loads fine. The files carry no printer settings, so the
printer stays the Flashforge AD5X 0.4. Pick a plate, then Slice plate and Print plate as usual.

Each wall prints lying flat, inside face down, so its trim (corner boards, door and window
casings, the band across each barn end and the rake board under the roof edge) is on top and
already set to **filament 2**; the siding is filament 1. Before slicing, add a second filament
in the Filament panel (the **+** next to Filament) and make it black, or whatever colour you
want the trim and roof. Filament 1 is the siding colour on every plate, filament 2 the trim
and the roof. When you send the print, match filament 1 and 2 to the right spools in the
AD5X's material station. On the two-colour plates (1, 3 and 4) the prime tower goes in the
back right corner, and those plates are laid out to keep it clear; plates 2 and 5 are one
colour and need no tower. The roof prints on its own, so if you want a grey roof and white
trim, load the grey spool as filament 2 just for plate 2.

The walls meet at the corners on 45-degree mitres, so each wall carries only the trim on its
own face, all in the top 0.6 mm. On the long walls the colour changes once, for the last three
layers. On the end walls the white vent louvres come up level with the trim, and on the door the
black trim sits round the white hinge edge, so those plates change on each of the last three
trim layers.

The `.stl` files are the same pieces one at a time, all one colour, if you'd rather set up
a plate yourself (`end wall.stl`, `upper roof.stl`, `lower roof.stl` and `loft.stl` each print
twice; `floor.stl` and `loft.stl` are already upside down). For two colours use the `.3mf` files.

**Settings:** `0.20mm Standard @FF AD5X` is fine. Set **Wall generator → Arachne**: the
siding is only 1.4 mm thick, and Arachne fills thin walls solid. Set **Elephant foot
compensation** to 0.1 mm (Quality tab, under Precision): the barbs, stops and posts under the
walls print on the bed and fit with 0.2 mm to spare, and the floor's face with 0.4 mm, so a
flared first layer would make them tight. No supports or brim are needed.

**Trim:** it stands 0.6 mm proud of the siding. If you'd rather print it all one colour, set
every part to filament 1 and use a black paint pen on the raised trim.

## How it holds together

- **The walls stand on the floor.** The floor reaches out under each wall, and the wall's
  siding carries on down past the floor as a skirt, hiding the floor's edge.
- **Posts and prongs.** Under every stud a short post drops into a notch in the floor's edge.
  A few prongs go down slots in the floor. Each prong is a springy leg with a barb on its foot:
  going down, the barb pushes the leg out toward the siding; at the bottom it springs back in
  under a ledge with a click. Beside each leg a stiff stop keeps the wall's foot from sliding
  out. The back wall has three prongs, the door wall and each end wall two.
- **Long walls first, then the lofts, end walls last.** This is the other way round from the
  Side Utility. A barn end's gable stands tall right over its corners, so a long wall couldn't
  come down past it. The back wall has no door or windows, so most of its weight is in its
  siding and it leans out about 2 1/2 mm at the top on its own. The lofts sitting on both long
  walls hold them upright, so they go in before the end walls.
- **Corner hooks.** The top plates of each end wall carry on past the mitre over the long
  wall's corner as a hook, with a small tip that drops into a pocket in the long wall. That ties
  the tops of the corners together and holds the long walls down. In front of each pocket a
  slope catches the tip and pulls a long wall upright if it leans out a little, and a small
  bevel along the top of each long wall's mitre guides an end wall past a long wall that leans in.
- **The lofts** rest on the long walls' top plates, 4 ft in from each end. Two lugs under each
  loft at each wall drop into notches in the top plate, so it can't slide, even with the roof
  pressing it. A loft goes in either way round.
- **The roof** is four sheets, the way the real steel goes on. A lower sheet sits on each steep
  edge of the barn ends, on a peg standing up from the middle of each steep edge. An upper sheet
  sits on the shallow slopes, on a peg standing up halfway up each one, and its tail laps over
  the top of the lower sheet. Every sheet only comes off straight up, and the upper sheet's tail
  is in the way of the lower sheet's, so the lower sheets are locked on until the upper ones
  are off.
- **Which side is which.** The floor has a door side and a back side. The door side has one long
  notch in the middle of its edge, under the doorway; the back side has a notch for every stud
  and a prong slot in the middle.

## Checking the fit

Before you start the big prints, try the fit test:

1. Stand the little doorway up on its thin (3 mm) bottom edge, the one with the little groove
   running out to the shallow hole, and hang the little door in it the same way as the real
   one (step 1 of "Putting it together"). It should swing out freely and stop against the
   strip inside the right-hand side so it can't swing in.
2. Stand the peg block up so the peg points up, and set the bit of roof on it. It should
   drop on and lift off without forcing.
3. Set the bit of floor face up. Of the two short wall pieces, the end wall is the one with a
   little hook sticking out past its mitre at the top; the side with the raised corner board and
   the siding grooves faces out. Press the other piece (the long wall) straight down onto the
   floor's longer edge: its prong should click into its slot with a firm push, and the siding
   should hang down over the floor's edge. Then lower the end wall piece straight down onto the
   short edge, so its hook goes into the long wall's corner and its prong clicks. The corner
   should close on its mitre, and neither wall should lift off. If a prong won't click, or a
   wall lifts off after clicking, tell Claude which.

Pin holes are already 0.35 mm bigger than their pins, peg holes 0.4 mm bigger than the pegs,
and the snap parts have 0.2 mm round them. Each barb hooks 0.45 mm under its ledge. If
anything is too tight or too loose, ask Claude to change that gap by 0.1 mm (or the barbs'
catch, if the prongs won't click or won't hold) and remake the files. The sizes are at the
top of `make_barn.py`.

## Cleaning up the parts

- Let the plate cool right down before you flex the parts off. Don't push a scraper under
  the ends of a wall (the mitred ends come to a thin edge with the black trim on top) or under
  the prongs: each prong's leg is a thin strip lifted just off the plate, joined to the wall at
  the top and to its barb at the foot.
- With a fresh hobby knife, take a light chamfer off the first-layer lip (the edge that was
  on the plate) on: the posts, stops and barbs under each wall, the inside edge of the mitre at
  both ends of every wall, the floor's face all round its edge, the roof pegs on the end walls
  (so they're round), the door's two pins, and the mouths of the peg holes under each roof
  sheet. A lip on a post, stop or barb makes it tight in its slot; a lip round the floor's face
  rubs on the skirts. Don't scrape the mitre faces, and don't trim the barbs' flat tops.
- If the siding has sagged a little on the inside of the long walls' top corners (just under
  where the end walls' hooks go), shave off any loose strands there.
- Snip any loose strands between the studs on the inside with flush cutters. Don't sand
  the outside; it would fill the siding grooves.
- Cut any strings in the windows at the point where they join, holding the thin window
  bars from behind with a fingertip.
- Lay each wall on glass. If it rocks or a sheet of paper slides under the middle, set the
  bed to 55 °C, lay the wall framing-side down on it under a sheet of paper and a flat board
  with about 1 kg on top, leave it 10 minutes, then let it cool before lifting the weight.

## Putting it together

No glue. You'll need your fingers, and tweezers or a small flat screwdriver if you ever take
it apart. `how it goes together.png` shows the order.

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
2. **Skids.** Lay the two skids on the table, notches and pegs up, about where they go, and
   lower the floor onto them, face up: the peg at each end of a skid goes into the hole in the
   solid band across each end of the floor, and the joists drop into the notches. They are a
   snug push fit; if they fall out when you pick the barn up, a drop of glue on each peg keeps
   them.
3. **Back wall.** Hold the back wall (the one without the door) over the back side of the
   floor (the side with a notch for every stud), trim facing out, with its siding outside the
   floor's edge. Line up the posts along its bottom with the notches and press straight down
   on the top of the wall above each of its three prongs (one stud bay in from each end, and in
   the middle) until it clicks. It will lean out a little at the top; that's fine for now.
4. **Door wall.** The same way on the door side; it has two prongs, one stud bay in from each
   end.
5. **Lofts.** Push the top of the back wall in so it stands straight, and lower a loft in at
   one end, floor side up, its end lined up with the ends of the long walls' top plates: its joists rest
   on the top plates of both long walls and the two lugs at each side drop into the notches in
   the plates. Either way round fits. Do the other end the same way. The lofts then keep the
   back wall straight.
6. **End walls.** Hold an end wall over one end of the floor, peak up and trim facing out,
   and lower it straight down past the end of the loft: the hooks on its top corners go down
   over the long walls' corners, its posts and prongs into the floor, and its mitred ends close
   against the long walls'. As the hooks go in, their tips slide down a slope into their
   pockets. If a tip sits on top of a long wall's corner instead, push the top of that long
   wall in a little. Press down over each of its two prongs until it clicks. Do the other end
   the same way. Check that the black corner boards meet top to bottom, and the floor is level
   with the doorway threshold.
7. **Door.** Hang it the same way as in step 1.
8. **Roof, lower sheets.** Each barn end has a peg standing up from the middle of each steep
   edge, and each lower sheet has a slot under each end. Hold a lower sheet ribs out with its
   cut-off edge at the top, over the steep edges, and lower it straight down so its two slots
   drop over the two pegs on that side. Do the other side.
9. **Roof, upper sheets.** Each barn end has a peg standing up halfway up each shallow slope,
   and each upper sheet has a hole under each end. Set an upper sheet ribs up with its raised
   ridge strip at the peak, so its two holes drop over the two pegs on that side and its tail
   laps over the top of the lower sheet. Do the other side. Always lift a roof sheet straight
   up, never slide it along its pegs.

**Taking it apart:** lift the upper sheets straight off, then the lower sheets. Lift out the
door, then take the end walls off: look underneath, and just inside each wall you can see the
barbs in their slots. Push each barb out, toward the siding, with a small flat screwdriver,
only just far enough to clear its ledge (about half a millimetre; don't lever it hard against
the far side of the slot), and ease that end of the wall up a little. When both of an end
wall's barbs are free, lift it straight up. Lift out the lofts, then take the long walls off
the same way, and lift the barn off its skids. If you want it permanent instead, a drop of glue
down each inside corner does it.

## Where the model differs from the real barn

- The siding is 1.4 mm thick (about 1 1/3 in at full size) so it prints solid, and it hangs
  down over the whole edge of the floor to hide the snaps; on the real barn it stops 3 1/2 in
  below the bottom plate.
- Every framing member runs the full depth of the wall, so each wall can print lying flat on
  its framing. Your gable studs and gable backing are 2x4s laid flat (wide face out); on the
  model they show their 3 1/2 in face but are as deep as the wall.
- The end truss has a collar tie across the knees, as the 3D designer draws the trusses inside
  a barn. Your end truss lesson had only the four chords, so the collar tie is extra. There are
  no trusses or roof deck between the two barn ends, so you can see in when the roof is off.
- On the real barn the side wall's upper plate laps over the end wall. On the model the end
  walls' top plates lap over the long walls' corners instead, because the end walls go on last.
- The windows' tops are at the loft header, level with the top of the door (71 1/2 in), as you
  taught for a lofted wall, and each window is centred between the door and the corner, as on
  the Side Utility model. The 3D designer puts a loft barn's window top 5 in under the wall top
  (74 1/2 in, 3 in higher, which would run into the loft header), and centres each window
  4.4 ft from the middle (about 4 3/4 in further from the door).
- The loft depth (4 ft from the outside of each end wall) is what the 3D designer assumes;
  nobody has given the shop's number yet. Tell Claude if your lofts are a different depth.

## Changing it

Everything is made by `make_barn.py` from the numbers at the top of the file (building
size, wall height, barn roof, door and window positions, loft, clearances, the snap joints). It
writes the `.stl` files and both `.3mf` files. `draw_barn.py` draws `how it goes together.png`.
`check_barn.py` then proves the parts still fit:

- each wall goes on straight down in the order above (the long walls, then the lofts, then the
  end walls past the lofts and over the long walls' corners) with nothing in the way but its
  barbs, stands on the floor, and can't lift, lean or slide once clicked in;
- the back wall can't stand straight on its own, but stays straight with the lofts on it once
  you push it straight;
- the corner hooks tie the walls together and find their pockets with a long wall leaning out up
  to about 1 3/4 mm at the top, and a bevel guides an end wall past a long wall pushed in up to
  0.5 mm;
- the barbs still catch once the parts are cut into 0.2 mm layers and anything thinner than a
  line is rounded off, and the prong legs bend less than PLA can take;
- the four roof sheets rest on the barn ends, are held by their pegs, don't touch each other,
  go on and off straight up without touching anything, and the upper sheets lock the lower
  ones on; printed in layers, a lower sheet sits a little higher but the upper sheet still rests
  on the barn ends; the lofts rest on the top plates, can't slide (even pushed up against the
  roof), clear the roof and the end walls coming down, and fit either way round; the door swings out to at least 90 degrees (about 98
  as made) and won't swing in; the skids fit under the joists;
- each wall, the floor, the lofts and the roof sheets print flat, with nothing steeper than 45
  degrees that isn't a bridge held at both ends (apart from a small flap of siding over each
  corner hook on the long walls), the walls' trim all in the top 0.6 mm, and nothing on the
  walls' first layers thinner than one line;
- measured off the parts: the walls are 79 1/2 in, the barn roof 43 3/4 in to the peak of the
  trusses, the eave 1 3/4 in and the door opening 48 1/4 x 71 1/2 in, the same as the 3D
  designer's shop standard, and the window tops are at your loft header, level with the door's.

To make a different size, ask Claude to change the numbers and run all three.
