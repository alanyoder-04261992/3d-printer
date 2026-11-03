# 8x12 Side Lofted Barn model — read me first

A 1:24 model of the shop-standard 8x12 Side Lofted Barn (one inch on the model = two feet on
the real building). It snaps together the same way as the
[8x12 Side Utility model](../shed%20model%208x12%20side%20utility/read%20me%20first.md), except
at the corners: a black corner angle is glued over each one (Alan, Nov 3 2026). The barn roof
comes off in four sheets so you can see the framing and the two lofts inside, and the 48 in
wooden door swings open on two small pins.

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
| `1 fit test.3mf` | Two plates. Plate 1, **new corner**: one short corner of the barn (a bit of floor and short pieces of the back wall and an end wall, with the new corner recesses) and a 20 mm stub of corner angle. Plate 2: a short doorway and door, a roof peg and a bit of roof, as before | Any, one colour | about 17 min and 9 min. **Print these first.** See "Checking the fit" below. |
| `2 all plates.3mf` | Everything else, one plate per print: | | |
| plate 1 | Both long walls | 1 white, 2 black | about 2 h 15 min, 1 colour change |
| plate 2 | The four roof sheets and the four corner angles | 2 black only | about 1 h 35 min |
| plate 3 | The door | 1 white, 2 black | about 20 min, 3 colour changes |
| plate 4 | Both end walls | 1 white, 2 black | about 2 h 30 min, 1 colour change |
| plate 5 | The floor, both skids and both lofts | 3 brown only | about 1 h 50 min |
| `3 corner caps for printed walls.3mf` | **Only for walls printed before Nov 3 2026** (the ones with corner hooks and black corner boards printed on). Four black caps that glue over the old corner boards. See "Walls already printed" below | 2 black only | about 9 min |

The times are Flash Studio's own for each plate (sliced Nov 3 2026): about 8 1/2 hours for
`2 all plates.3mf`, with about 129 g of white, 68 g of black and 59 g of brown. The caps are
2.4 g of black.

Start Flash Studio first, then open them with **File → Open Project** (Ctrl+O), or **Open
Project** on its Home page. Starting Flash Studio by opening the file itself can leave it stuck
on "Loading". If Flash Studio says the file is from a newer version, click OK; it loads fine. If
it asks about unsaved changes to your settings, click **Discard** (the file brings its own). The
files carry their settings: the Flashforge AD5X 0.4, `0.20mm Standard @FF AD5X`, and three
filaments, 1 white, 2 black and 3 brown. Pick a plate, then Slice plate and Print plate as usual.

Each wall prints lying flat, inside face down, so its trim (door and window casings, the band
across each barn end and the rake board under the roof edge) is on top and already set to
**filament 2**; the siding is filament 1. Filament 1 (white) is the siding on every plate,
filament 2 (black) the trim, the roof and the corner angles, and filament 3 (brown) the floor,
skids and lofts. For other colours, click a filament's colour square in the Filament panel. When
you send the print, match filaments 1, 2 and 3 to slots 1, 2 and 3 in the AD5X's material
station. On the two-colour plates (1, 3 and 4) the prime tower goes in the back right corner,
and those plates are laid out to keep it clear; plates 2 and 5 are one colour and need no tower.
The roof and the corner angles print together, so if you want a grey roof and white trim, load
the grey spool as filament 2 just for plate 2, and the angles come out grey too.

The walls meet at the corners on 45-degree mitres. There are no corner boards printed on the
walls any more: the black corner angles from plate 2 are the corner boards, glued on after
(Alan, Nov 3 2026). Each wall's trim is all in its top 0.6 mm, and nothing white stands any
higher, so the long walls and the end walls each change colour once, for the last three layers.
The back wall has no trim left at all. The gable vent is set into the siding now instead of
standing out (Alan, Nov 3 2026: keep it white, but it doesn't have to stick out past the wall):
its frame is flush with the siding, with a groove round it, and its louvres sit in a recess,
three layers of siding behind them. On the door the black trim sits round the white hinge edge,
so plate 3 still changes on each of the last three trim layers.

The `.stl` files are the same pieces one at a time, all one colour, if you'd rather set up
a plate yourself (`end wall.stl`, `upper roof.stl`, `lower roof.stl` and `loft.stl` each print
twice; `floor.stl` and `loft.stl` are already upside down; `corner angle.stl` and `corner cap.stl`
each have all four). For two colours use the `.3mf` files.

**Settings:** already in the file: `0.20mm Standard @FF AD5X` with **Wall generator →
Arachne** (it shows in orange as changed), because the siding is only 1.4 mm thick and Arachne
fills thin walls solid. **Elephant foot compensation** is 0.1 mm, the AD5X's own setting (Quality
tab, under Precision); keep it there: the barbs, stops and posts under the
walls print on the bed and fit with 0.2 mm to spare, and the floor's face with 0.4 mm, so a
flared first layer would make them tight. No supports or brim are needed: each corner angle
lies on the plate on one leg, its other leg standing up, and has 386 mm² on the plate.

**Trim:** it stands 0.6 mm proud of the siding, the corner angles 0.65 mm. If you'd rather print
it all one colour, set every part to filament 1 and use a black paint pen on the raised trim and
the angles.

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
  walls hold them upright, so they go in before the end walls. A small bevel along the top of
  each long wall's mitre guides an end wall past a long wall that leans in.
- **The corners are glued.** On the first barn the little hook tips that tied the corners
  snapped, and the corners showed a gap, so there are no hooks now (Alan, Nov 3 2026). Each wall
  has a recess 0.4 mm deep (two layers) in its face along each corner, and the outside corner
  itself is cut off at 45 degrees, so neither wall ends in a thin edge there. Once all four
  walls are on, two rubber bands round them pull the corners shut, and a black corner angle is
  glued into the two recesses at each corner. It covers the joint by 3.7 mm on the long wall's
  face and 3.6 mm on the end wall's, so no gap can show, and it ties the walls into one box. The
  box still unclips from the floor, and the roof, lofts and door still come off.
- **The corner angles** are L-shaped, each leg 1.05 mm thick: 0.4 of it sits in the recess and
  0.65 stands out. As printed there's a hairline gap past the edge of each leg in its recess,
  about 0.1 mm on the long wall and 0.2 mm on the end wall, so it still goes in with the corner
  pulled shut. The long wall's recess has a level top, so the angle presses straight
  in. Its foot is level with the bottom of the skirts, its top stays 0.2 mm under the roof
  sheets, and on the end wall it stops just under the rake board. They come in two hands, two of
  each: one hand fits the door wall at end wall 1 and the back wall at end wall 2, the other the
  two other corners.
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

Before you start the big prints, print both plates of `1 fit test.3mf` and try them:

1. **New corner (plate 1).** Set the bit of floor face up. Of the two short wall pieces, the
   long one is the back wall; the side with the siding grooves faces out. Press it straight down
   onto the floor's longer edge: its prong should click into its slot with a firm push, and the
   siding should hang down over the floor's edge. Then lower the end wall piece straight down
   onto the short edge until its prong clicks. The two should meet on their mitre, with a
   shallow recess down each face beside the corner and the corner itself cut off. Press the
   20 mm stub of corner angle into the corner, its foot level with the bottom of the skirts:
   it should sit flat in both recesses without rocking, with a hairline gap round its edges.
   Squeeze the corner shut with your fingers while you look; nothing should hold it open. If the
   stub is tight, rocks, or won't go flat, or a prong won't click, tell Claude which.
2. **Door (plate 2).** Stand the little doorway up on its thin (3 mm) bottom edge, the one with
   the little groove running out to the shallow hole, and hang the little door in it the same
   way as the real one (step 1 of "Putting it together"). It should swing out freely and stop
   against the strip inside the right-hand side so it can't swing in.
3. **Roof peg (plate 2).** Stand the peg block up so the peg points up, and set the bit of roof
   on it. It should drop on and lift off without forcing.

Pin holes are already 0.35 mm bigger than their pins, peg holes 0.4 mm bigger than the pegs,
the snap parts have 0.2 mm round them, and each corner angle has about 0.1 mm round it in its
recesses. Each barb hooks 0.45 mm under its ledge. If anything is too tight or too loose, ask
Claude to change that gap by 0.1 mm (by 0.05 mm for the corner angle, or the barbs' catch, if
the prongs won't click or won't hold) and remake the files. The sizes are at the top of
`make_barn.py`.

## Cleaning up the parts

- Let the plate cool right down before you flex the parts off. Don't push a scraper under
  the ends of a wall (the mitred ends come to a thin edge) or under the prongs: each prong's leg
  is a thin strip lifted just off the plate, joined to the wall at the top and to its barb at
  the foot. Flex the plate to free the corner angles; don't bend them.
- With a fresh hobby knife, take a light chamfer off the first-layer lip (the edge that was
  on the plate) on: the posts, stops and barbs under each wall, the inside edge of the mitre at
  both ends of every wall, the floor's face all round its edge, the roof pegs on the end walls
  (so they're round), the door's two pins, and the mouths of the peg holes under each roof
  sheet. A lip on a post, stop or barb makes it tight in its slot; a lip round the floor's face
  rubs on the skirts. Don't scrape the mitre faces, and don't trim the barbs' flat tops.
- Look down each corner recess and pick out any string or blob with the knife tip, so the
  angles sit flat.
- The corner angles' outside face on the long wall was on the plate. A lip along its edges sits
  outside the wall, so it doesn't change the fit, but it shows: if you can see one, shave it off
  with the knife held flat.
- Snip any loose strands between the studs on the inside with flush cutters. Don't sand
  the outside; it would fill the siding grooves.
- Cut any strings in the windows at the point where they join, holding the thin window
  bars from behind with a fingertip.
- Lay each wall on glass. If it rocks or a sheet of paper slides under the middle, set the
  bed to 55 °C, lay the wall framing-side down on it under a sheet of paper and a flat board
  with about 1 kg on top, leave it 10 minutes, then let it cool before lifting the weight.

## Putting it together

You'll need your fingers, two rubber bands that go round the barn (or painter's tape), glue for
the corners, and tweezers or a small flat screwdriver if you ever take it apart. For the glue,
gel super glue is fine in small dots; clear contact cement (E6000) or 5-minute epoxy can't leave
a white haze on black plastic the way super glue's fumes sometimes do. `how it goes together.png`
shows the order.

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
2. **Floor.** Lay the floor face up on a flat table, without the skids. The skids go on last,
   so that the corner angles' feet can be glued level with the bottom of the skirts.
3. **Back wall.** Hold the back wall (the one without the door) over the back side of the
   floor (the side with a notch for every stud), trim facing out, with its siding outside the
   floor's edge. Line up the posts along its bottom with the notches and press straight down
   on the top of the wall above each of its three prongs (one stud bay in from each end, and in
   the middle) until it clicks. It will lean out a little at the top; that's fine for now.
4. **Door wall.** The same way on the door side; it has two prongs, one stud bay in from each
   end.
5. **Lofts.** Push the top of the back wall in so it stands straight, and lower a loft in at
   one end, floor side up, its end lined up with the ends of the long walls' top plates: its
   joists rest on the top plates of both long walls and the two lugs at each side drop into the
   notches in the plates. Either way round fits. Do the other end the same way. The lofts then
   keep the back wall straight.
6. **End walls.** Hold an end wall over one end of the floor, peak up and trim facing out,
   and lower it straight down past the end of the loft, so its posts and prongs go into the
   floor and its mitred ends close against the long walls'. Press down over each of its two
   prongs until it clicks. Do the other end the same way. Check that the floor is level with
   the doorway threshold.
7. **Band the corners.** Put a rubber band (or a loop of painter's tape) round the walls about
   15 mm above the table, and another about 10 mm under the top of the long walls, just tight
   enough that each corner closes on its mitre top to bottom. Not tighter: too tight bows the
   long walls in. Look down on each corner from above to check.
8. **Corner angles.** The bands cross each corner right over its recesses. Each angle goes in
   under them, so the bands end up over the angles, never under. The angles come in two hands,
   two of each. Hold one foot down: the leg whose top steps up about 2 mm goes on the end wall, just
   under the rake board, and the other leg on the long wall. Each one then only fits two of the
   corners. First try all four dry: ease the bands out from the corner with a finger (with tape,
   peel that corner's strips back), press the angle straight into its two recesses with its foot
   on the table, and let the bands back over it. It should sit flat in both recesses with a
   hairline gap along both edges. Then glue them one at a time: take the angle out and put 3 or
   4 pin-head dots of gel super glue in a row down each recess floor. The floors are only about
   2 mm wide, so keep the dots in the half nearest the corner, at least 1 mm in from the recess's
   outer edge (the side where the hairline gap shows) and from its top and bottom. Glue that
   spreads toward the corner goes into a hidden gap under the angle. Or use a hair-thin line of
   contact cement or epoxy down the same half. Press the angle back in with its foot on the
   table, let the bands (or the tape) back over it, and hold it for half a minute. Leave the
   bands on for 15 minutes for super glue, an hour for epoxy, or overnight (a full day is
   better) for contact cement, which stays soft for hours; then take them off.
9. **Skids.** Lay the two skids on the table, notches and pegs up, about where they go, and lift
   the barn onto them: the peg at each end of a skid goes into the hole in the solid band across
   each end of the floor, and the joists drop into the notches. They are a snug push fit; if they
   fall out when you pick the barn up, a drop of glue on each peg keeps them.
10. **Door.** Hang it the same way as in step 1.
11. **Roof, lower sheets.** Each barn end has a peg standing up from the middle of each steep
    edge, and each lower sheet has a slot under each end. Hold a lower sheet ribs out with its
    cut-off edge at the top, over the steep edges, and lower it straight down so its two slots
    drop over the two pegs on that side. Do the other side.
12. **Roof, upper sheets.** Each barn end has a peg standing up halfway up each shallow slope,
    and each upper sheet has a hole under each end. Set an upper sheet ribs up with its raised
    ridge strip at the peak, so its two holes drop over the two pegs on that side and its tail
    laps over the top of the lower sheet. Do the other side. Always lift a roof sheet straight
    up, never slide it along its pegs.

**Taking it apart:** lift the upper sheets straight off, then the lower sheets. Lift out the
door and the lofts. The four walls are glued into one box now, but the box still unclips from
the floor: lift the barn off its skids, look underneath, and just inside each wall you can see
the barbs in their slots. Push each barb out, toward the siding, with a small flat screwdriver,
only just far enough to clear its ledge (about half a millimetre; don't lever it hard against
the far side of the slot), and ease that side of the box up a little. Work round the box; when
all nine barbs are free, lift it straight up off the floor.

## Walls already printed (before Nov 3 2026)

If you printed the walls from the earlier files, with the corner hooks and the black corner
boards printed on them, you don't need to print them again. `3 corner caps for printed
walls.3mf` has four black caps, about 9 minutes and 2.4 g. Each one is an L that glues over the
old corner boards at one corner: its legs are 0.6 mm thick, sit 0.1 mm off the old boards, and
reach 0.2 mm past the boards' inner edges, so the joint can't show. A small groove along the
cap's inside corner leaves room for a blob on the old boards' corner or on either board's end.
The corners then stand 1.3 mm out instead of 0.6. Like the angles, they come in two hands: the
leg whose top steps up goes on the end wall, just under the rake board. The flat outside face
of each cap was on the plate; shave any lip along its edges off with the knife held flat.

1. Snip what's left of each broken hook tip flush with the underside of the end wall's hook
   arm. Leave the arms on.
2. Pick any chips out of the slots at the top of each long wall's ends, where the tips went. A
   chip there holds the corner open.
3. With a hobby knife, take the first-layer lip off the inside edge of each mitre. Never cut
   the outer 2 mm of a mitre (the white siding and the black board on it).
4. Put it together as before, floor on the table without the skids: the long walls, the
   lofts, then the end walls, whose hooks go down over the long walls' corners.
5. Band the box about 15 mm above the table and about 10 mm under the top of the long walls,
   until the black corner boards meet top to bottom.
6. Try each cap dry: ease the bands out from the corner with a finger (with tape, peel that
   corner's strips back), slip the cap over the old boards with its foot on the table, and let
   the bands back over it. The bands go over the caps, never under. If a cap rocks on a blob
   on the old boards' corner, shave just the blob flat. Then glue them one at a time with clear
   contact cement (E6000) or 5-minute epoxy, a thin line down the middle of each leg's inside.
   Not super glue: on black plastic its fumes can leave a white haze, and the cap is all on
   show. Leave the bands on for an hour for epoxy, or overnight (a full day is better) for
   contact cement, which stays soft for hours; then take them off and put on the skids, the
   door and the roof.

Don't mix old and new walls at one corner: an old end wall's hook arm runs into a new long
wall's corner, and the old corner boards keep a new angle out of its recesses.

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
- On the real barn the side wall's upper plate laps over the end wall. On the model the walls
  meet on mitres at the corners, glued, with the black corner angle over the joint as the
  corner boards.
- The gable vent is set into the siding instead of standing out past it, so the end walls change
  colour only once (Alan, Nov 3 2026).
- The windows' tops are at the loft header, level with the top of the door (71 1/2 in), as you
  taught for a lofted wall and confirmed is right (Nov 2 2026), and each window is centred
  between the door and the corner, as on the Side Utility model. The 3D designer still puts a
  loft barn's window top 5 in under the wall top (74 1/2 in, 3 in higher, which would run into
  the loft header), and centres each window 4.4 ft from the middle (about 4 3/4 in further from
  the door).
- The loft depth (4 ft from the outside of each end wall) is what the 3D designer assumes;
  nobody has given the shop's number yet. Tell Claude if your lofts are a different depth.

## Changing it

Everything is made by `make_barn.py` from the numbers at the top of the file (building
size, wall height, barn roof, door and window positions, loft, clearances, the snap joints, the
corner angles). It writes the `.stl` files and the three `.3mf` files. `draw_barn.py` draws
`how it goes together.png`. `check_barn.py` then proves the parts still fit:

- each wall goes on straight down in the order above (the long walls, then the lofts, then the
  end walls past the lofts and the long walls' mitred ends) with nothing in the way but its
  barbs, stands on the floor, and can't lift or slide once clicked in;
- the back wall can't stand straight on its own, but stays straight with the lofts on it once
  you push it straight, and a bevel guides an end wall past a long wall pushed in up to 0.5 mm;
- each corner angle sits in both recesses touching only their floors, about 0.1 mm clear
  everywhere else, still fits with either wall sitting 0.15 mm out or in, and presses straight
  in without catching; cut into layers the way it and the walls print, it still sits on both
  recess floors without touching the walls, even with the mitre pulled shut; it covers the
  corner by 3.7 mm on the long wall's face and 3.6 mm on the end wall's from the bottom of the
  skirts up, keeps 0.2 mm under the roof (still clear with the roof 0.15 mm lower) and 0.15 mm
  under the rake board, and clears the lofts and the door;
- each recess's floor prints exactly two layers under the siding's top layer (4.65 and 5.05 mm
  up in the print), and near the corners nothing is thinner than a printed line;
- the gable vent's louvres sit in a recess with three layers of siding behind it, and nothing of
  the vent stands out past the siding;
- each cap for the walls already printed clears those walls (built from the Nov 2 `make_barn.py`
  in git) and their boards by 0.1 mm, also with a wall's foot 0.15 mm out, leaves room for a
  blob on the old boards' corner, clears the roof, and covers the old corner;
- the barbs still catch once the parts are cut into 0.2 mm layers and anything thinner than a
  line is rounded off, and the prong legs bend less than PLA can take;
- the four roof sheets rest on the barn ends, are held by their pegs, don't touch each other,
  go on and off straight up without touching anything, and the upper sheets lock the lower
  ones on; printed in layers, a lower sheet sits a little higher but the upper sheet still rests
  on the barn ends; the lofts rest on the top plates, can't slide (even pushed up against the
  roof), clear the roof and the end walls coming down, and fit either way round; the door swings
  out to at least 90 degrees (about 98 as made) and won't swing in; the skids fit under the
  joists;
- each wall, the floor, the lofts, the roof sheets, the corner angles and the caps print flat,
  with nothing steeper than 45 degrees that isn't a bridge held at both ends and nothing starting
  in mid-air (for the angles and caps, even once anything thinner than a line is left out, the
  way the slicer does); the walls' trim is all in the top 0.6 mm with nothing white above the
  siding's top layer, so each wall plate changes colour once, and the back wall has no black
  left at all; nothing on the walls' first layers is thinner than one line, even where each loft
  notch stops just short of a long wall's mitre;
- every plate's parts are inside the bed, at least 3 mm apart, and clear of the prime tower;
- measured off the parts: the walls are 79 1/2 in, the barn roof 43 3/4 in to the peak of the
  trusses, the eave 1 3/4 in and the door opening 48 1/4 x 71 1/2 in, the same as the 3D
  designer's shop standard, and the window tops are at your loft header, level with the door's.

To make a different size, ask Claude to change the numbers and run all three.
