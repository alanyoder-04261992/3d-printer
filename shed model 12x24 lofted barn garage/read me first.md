# 12x24 Lofted Barn Garage model — read me first

A 1:36 model of the shop-standard 12x24 Lofted Barn Garage (one inch on the model = three feet on
the real building). You asked for it on Nov 3 2026 ("create a cabin and loft cabin and garage and
loft garage", then "Move to higher scale so it fits", then "Do the cabin and loft cabin 10x20 and
garage and lift garage 12x24"). At 1:32 the 24 ft side would be 228.6 mm, more than the 220 mm bed,
so it is 1:36, the largest scale at which every piece prints whole.

It is built from the
[8x12 Side Lofted Barn model](../shed%20model%208x12%20side%20lofted%20barn/read%20me%20first.md):
the same snap joints, the same glued black corner angles, two lofts and a barn roof in four lift-off
sheets. Its twin is the 12x24 Garage model, which has the very same roll-up door and steel door. Its
floor and skids are the same size and made the same way, and its inner skids are the same, but its
floor and outer skids don't swap with this one's: its long walls have three clips each, at other places,
so its floor's clip slots and its outer skids' notches are elsewhere. The roll-up door lifts out: it
is its own piece, with a black handle at the bottom middle of its bottom rail, and you lift it by the
handle and take it out the front, with the roof on (you, Nov 3 2026: "Do 4 the lift out add a handle
in the bottom middle to lift it up", and then "Front lift-out"). The steel door opens, inward, on
two small pins.

Sizes come from the 3D designer's shop numbers for the Lofted Barn Garage, at your actual 12-wide
width of 134 in (11 ft 2 in; you, Sep 30 2026): 6.9 ft walls (82.8 in), a barn roof 51 in from the
top of the upper plate to the peak of the trusses (your shop number, Oct 11 2026), a 4 ft loft at
each end, the 8 ft roll-up door (96 x 76.8 in) in the front end with a faux loft window in the gable
above it, the 36 in steel door (36 x 75.6 in) and a 2x3 window on the right-hand side, a louvred
vent in each gable, and four 4x6 skids.

**Where the door and window go is your standard layout.** You asked on Nov 3 2026: "go on
yoder-storage-barns.com to see standard layout". The site's 3D builder loads your
`designer-standards.js`, which opens each building with your standard doors and windows (your
copy-this-build codes, Aug 2026). For the garages it says: the walk door goes on the same end as the
roll-up, its edge 4 ft in from the corner, and the window sits centred between the walk door and the
back of the building. So on the right-hand side (the door side), from the outside corner at the
roll-up end:

| | From the roll-up end's corner | From the middle of the side |
|---|---|---|
| Steel door opening | 48 to 84 in (4 ft to 7 ft) | centre 6 ft 6 in toward the roll-up end |
| Window opening | 173.4 to 198.6 in (centre 15 ft 6 in) | centre 3 ft 6 in toward the back |

The window's centre is 8 ft 6 in from the door's back edge and 8 ft 6 in from the back. The model
first had the 3D designer's stock places (the door 7.6 ft toward the back, the window 7.6 ft toward
the roll-up end); the site's style pictures and the real garages in its gallery match your standard.
The roll-up, the faux loft window and the vents don't move.

The framing is built the way you taught the 3D designer:

- studs 16 in apart, with a double stud at every 4 ft mark;
- over the window your 5 in loft header (two 2x4s on edge on a flat one) right under the top
  plate, a king stud under each end of it and a full stud beside that, and a flat window plate
  under it on short studs that keep to the 16 in layout;
- over the steel door your two flat 2x4s (3 in) "for a taller door", because the 5 in header doesn't
  fit under the plates on a 6.9 ft wall, with short studs on the layout marks up to the top plate;
  the door's edge is on the 4 ft mark, so its hinge-side king stud stands just where that mark's
  first stud would;
- round the roll-up your garage-door way: king studs up to the top plate, no header;
- on each end wall's upper plate the 2x6 gable board, gable studs 24 in apart measured from the
  outside of the end wall, and on the back end gable backing 11 in above the upper plate (the
  front end has the faux loft window, so no backing);
- the end truss's four chords, one 2x4 deep under the roof line;
- the floor is 4x8 sheets in rows 48, 48 and 38 in wide, each next row started with a 4 ft piece.

The end truss also has a collar tie and a king post, as the 3D designer draws barn trusses. The
lofts are the 3D designer's too (it assumed them; open question 8): 4 ft deep at each end, 2x6
joists 16 in apart on the long walls' top plates, with the loft floor on top.

| | |
|---|---|
| Footprint | 94.5 x 203.2 mm walls (3.7 x 8 in), 102.2 x 207.2 mm with the roof on |
| Height on its skids | about 108.7 mm |
| Doors | the roll-up door lifts out the front by its handle (it doesn't roll up or stay part open); the steel door swings in |
| Roll-up door | lifts out, 96 x 76.8 in opening |
| Window | open, no glass, so you can look in |
| Inside you can see | the studs and double studs, the loft header, window plate, the steel door's flat header and short studs, the roll-up's king studs and the slot over it where the door's top goes, the end trusses, gable board, gable studs and backing, both lofts, floor sheet seams |

## What to print, in this order

| File | What's on it | Filament | Time on the AD5X |
|---|---|---|---|
| `1 fit test.3mf` | Two plates. Plate 1, **roll-up door**: half a roll-up doorway and half a roll-up door, both full height, cut from the real ones; the door lifts out just like the real one, and the two are alone on the plate so its handle prints just as the real door's does on plate 3. Plate 2, **roll-up corner, door and roof peg**: a bit of floor, short pieces of the plain side and the roll-up end (its prong is under the side of the doorway), a 20 mm stub of corner angle and a 23 mm stub of outer skid, and behind them a short in-swing doorway and its door, a roof peg and a bit of roof | Any, one colour | plate 1 22 min (10.2 g), plate 2 24 min (8.2 g). **Print these first.** See "Checking the fit" below. |
| `2 all plates.3mf` | Everything else, one plate per print: | | |
| plate 1 | Both long walls and the steel door | 1 white, 2 black | 2 h 31 min, 65.8 g white and 0.5 g black, 1 colour change |
| plate 2 | The four roof sheets and the four corner angles | 2 black only | 1 h 45 min, 70.8 g |
| plate 3, "end walls and roll-up curtain" | Both end walls and the roll-up door | 1 white, 2 black | 1 h 53 min, 48.2 g white and 1.3 g black, 1 colour change |
| plate 4 | The floor, the four skids and both lofts | 3 brown only | 2 h 13 min, 63.2 g |

The times and grams are Flash Studio's own (sliced again Nov 4 2026, with the walls' and floor's bridge
settings and the steel door's panels at the designer's places): about 8 h 22 min for `2 all plates.3mf`,
with about 114 g of white, 72.5 g of black and 63 g of brown. The roll-up door only adds about 4 minutes
and half a gram to plate 3: the end wall no longer has the solid printed-shut door in it.

Start Flash Studio first, then open them with **File → Open Project** (Ctrl+O), or **Open
Project** on its Home page. Starting Flash Studio by opening the file itself can leave it stuck on
"Loading". If Flash Studio says the file is from a newer version, click OK; it loads fine. If it asks
about unsaved changes to your settings, click **Discard** (the file brings its own). The files carry
their settings: the Flashforge AD5X 0.4, `0.20mm Standard @FF AD5X`, and three filaments, 1 white,
2 black and 3 brown. Pick a plate, then Slice plate and Print plate as usual.

**Check the slots in the Send dialog every time.** Flash Studio matches each filament to the slot
whose colour on the printer is closest, and the printer still shows the old colours. Click each
filament's slot box and pick it by number: 1 white, 2 black, 3 brown.

Each wall prints lying flat, inside face down, so its trim (the casings, the faux loft window, the
bands across the ends and the rake boards) is on top, already set to **filament 2**. All the black is
in the last three layers and nothing white stands any higher, so plates 1 and 3 change colour once.
The roll-up door prints on its back beside the end walls, slats and handle up, white with a black
handle and latch plate: its black starts on the same layer as the walls' trim, and above the trim
only its handle prints, so it is still one colour change. (Above the trim the handle prints alone:
its legs in about 1.3 seconds a layer, its grip in 2.3 to 3.3. Fit-test plate 1 has only the half
doorway and the half door, so its handle prints alone on just the same layers, in just the same
times, and you see how it comes out before plate 3.) The plain side has no black at all, and the steel door is all
white (the designer's steel doors always are), so it rides on plate 1 for free. On plates 1 and 3
the prime tower goes in the back right corner, and those plates are laid out to keep it clear;
plates 2 and 4 are one colour and need no tower.

**Brims:** the four skids are long and thin (2.5 mm wide, 203 mm long), so each one has its own
**5 mm brim, outer only**, set in the file, as the printer brain says for long thin parts. Sliced,
Flash Studio put it on: ten lines reaching 4.6 mm out round each skid, and the skids are spaced so
the brims don't touch each other or the floor and lofts. The corner angles and roof sheets are set
to no brim (a brim lip would show on an edge you see). If a skid ever comes up without a brim,
right-click it, Brim, Outer only, 5 mm. The fit test's skid stub has the same brim.

**Settings:** already in the file: `0.20mm Standard @FF AD5X` with **Wall generator → Arachne** (it
shows in orange as changed), because the siding is only 1.4 mm thick and the studs 1.06 mm, and
Arachne fills thin walls solid. **Elephant foot compensation** is 0.1 mm, the AD5X's own setting
(Quality tab, under Precision); keep it there: the barbs, stops and posts under the walls print on
the bed and fit with 0.2 mm to spare, so a flared first layer would make them tight. No supports.
Each wall, and each fit-test piece cut from one, carries a modifier, "bridges across the studs",
over its siding: it sets **External bridge infill direction** to 180, which Flash Studio reads as
straight across the studs. Left to itself, Flash Studio picks the direction afresh each time you
slice: about every other time it laid the door side's siding along four of its stud bays in 55 mm
strands, which sag, and every wall's bays are that long. Across the studs none is over about 16 mm.
On each end wall it stops halfway up the collar tie, and a second modifier over it, "bridges up the
gable", sets 90: across, the top of the gable would be 31 mm strands; up it, none is over about 9 mm.
They start above the framing, so the prongs' springy legs still print along their length. The floor
has its own, on its second layer only, the one over the floor sheet seams: "bridges across the long
seams" over each long seam and "bridges across the short seams" everywhere else. Left to itself,
Flash Studio laid that layer along the long seams, one 193 mm strand over each, which sags into the
seam; now every strand crosses a seam. Leave them all in, and don't turn a wall or the floor on the
plate: the modifiers lay the bridges along the bed, not along the part, so a wall turned a quarter
turn would get the 55 mm strands every time, and the floor long strands down its long seams again.

The `.stl` files are the same pieces one at a time, all one colour, if you'd rather set up a plate
yourself (`upper roof.stl`, `lower roof.stl` and `loft.stl` each print twice; `floor.stl` and
`loft.stl` are already upside down; `skids.stl` has all four, spaced so a 5 mm brim round each
doesn't run into the next, `corner angle.stl` all four angles, `roll-up curtain.stl` the roll-up
door on its back, and `fit test.stl` every fit-test piece of both plates together: print the fit test
from `1 fit test.3mf` instead, so the half door prints alone on its plate). For two colours, and for the
walls' and floor's bridge settings, use the `.3mf` files.

## How it holds together

- **The walls stand on the floor.** The floor reaches out under each wall, and the wall's siding
  carries on down past the floor as a skirt, hiding the floor's edge.
- **Posts and prongs.** Under the studs short posts drop into notches in the floor's edge. A few
  prongs go down slots in the floor: each is a springy leg with a barb on its foot that clicks in
  under a ledge, with a stiff stop beside it. Each long wall has four (about one stud bay in from
  each end, and either side of the middle; on the door side the one just back of the middle is
  under the window, low in the wall). The roll-up end has two, under the sides of the doorway,
  one near each corner. The back end has two, one near each corner but not the same distance in
  (the stud bay next to the plain side's corner is too narrow).
- **Long walls first, then the lofts, end walls last.** A barn end's gable stands right over its
  corners, so a long wall couldn't come down past it. The plain side has no door or window, so
  most of its weight is in its siding, and on its own it leans out about 1.7 mm at the top. The
  lofts sitting on both long walls hold them upright (their weight holds it 2.1 to 1, over the
  barn's 2 to 1 rule), so they go in before the end walls. A small bevel along the top of each long wall's mitre guides an end wall
  past a long wall that leans in.
- **The corners are glued.** Each wall has a recess 0.4 mm deep (two layers) in its face along each
  corner, and the outside corner itself is cut off at 45 degrees. Once all four walls are on, two
  rubber bands pull the corners shut, and a black corner angle is glued into the two recesses at
  each corner (Alan, Nov 3 2026). Each leg is 1.05 mm thick, 0.65 of it standing out of the siding,
  and covers 3 mm of its wall from the corner, so each sits on about 1.5 mm of glue on each recess
  floor. As printed there's a hairline gap past the edge of each leg. They come in two hands, two
  of each.
- **The lofts** rest on the long walls' top plates, 4 ft in from each end. Two lugs under each loft
  at each wall drop into open notches cut down through the whole top plate, so it can't slide.
  With the roof on, a loft can only rise about 1 mm, and its lugs are 1.77 mm deep, so they stay
  in. A loft goes in either way round. The loft at the roll-up end ends right where the steel door
  begins (both are 4 ft in from the end): on the door side its inner lug drops into a notch over the
  door's hinge-side king stud, 1 mm above the end of the door's header.
- **The roof** is four sheets, as the barn's: a lower sheet on pegs standing up from the middle of
  each steep edge of the barn ends, an upper sheet on pegs halfway up each shallow slope, its tail
  lapping over the lower sheet. Every sheet only comes off straight up, and the upper sheets lock
  the lower ones on.
- **The steel door** swings in on two pins, to about 101 degrees, where it meets the king stud
  beside its hinge. Shut, it rests against a thin strip on the latch side, outside it, so it can't
  swing out. The bottom pin goes in along a little slot in the sill from the inside. So you hang
  the door in the door side **before** that wall goes on the floor: once it's on, the floor closes
  the slot and the door can't come off until the door side is unclipped again.
- **The roll-up door is its own piece.** It hangs on the white threshold's sloped back and leans back
  against two little slopes up the sides of the doorway, which stop it going in. A tongue along its top
  goes up behind the trim over the doorway. Hidden up there, two springy fingers press it down and two
  small tabs press it in, so it sits tight and doesn't rattle, even upside down. It never touches the
  floor. It comes out the front: lift it by its handle until it stops (about a millimetre), let it down
  a hair, pull the bottom toward you and let it drop, roof on or off, and it misses the loft (by about a
  third of a millimetre at the closest). It doesn't stay part open: it's either in or out.
- **The skids.** The two inner skids are notched on top for the floor joists, with a peg at each
  end into the floor's end band. The two outer skids sit under the floor's long edges, flat on top,
  each with two small pegs into holes near the ends. All four stand the same height under the
  floor, so the garage sits on all four.
- **Which side is which.** The floor has a door side and a plain side. The door side has one long
  notch under the doorway, near the roll-up end; the plain side has a notch for every stud. The
  floor's roll-up end has five short notches across the middle of its edge: one in the very middle
  and two each side of it, the same on both sides. Near each corner it has a clip slot, the same
  distance in from each corner. The other end's notches aren't the same each side.

## Checking the fit

Before you start the big prints, print both plates of `1 fit test.3mf` and try them:

1. **Roll-up corner (plate 2).** Set the bit of floor face up. The roll-up end piece is the one
   with the raised casing along the edge of the roll-up on its outside face; the plain side piece
   has only siding outside. The plain side goes on the floor's edge that has a small hole
   underneath about 3.5 mm in from it (the skid stub's peg hole; it is about 6.7 mm in from the
   other edge), the roll-up end on the other edge. Press the plain side straight down onto its edge:
   its prong should click into its slot with a firm push, and the siding should hang down over the
   floor's edge. Then lower the roll-up end piece straight down onto the other edge until its
   prong, under the side of the doorway, clicks. The two should meet on their mitre. Press the 20 mm
   stub of corner angle into the corner, its foot level with the bottom of the skirts: it should
   sit flat in both recesses without rocking, with a hairline gap round its edges. Push the skid
   stub's little peg up into the hole under the floor near the corner: the skid should sit flat
   under the floor. Look at the edge of the casing: it should be clean. If anything is tight, rocks,
   or won't click, tell Claude which.
2. **Roll-up door (plate 1).** Plate 1 is half a roll-up doorway and half a roll-up door, both full
   height, cut from the real ones, and they work just like the real ones (the half door is a little over
   half the real door's weight, because its handle is full size, on half its springs). Stand the doorway
   on the table and put the door in (step 12 below), its bottom about 6 mm out. It takes a little knack,
   and you can tell which way you're off:
   - If it stops dead about 2 to 3 mm early, before it gets springy, it is caught on the trim. Don't push
     harder (that can snap the little tab at its top); let it down, lean its top in a bit more and push
     again.
   - If it goes in, but lifted a little by its handle and let go it stays up or only creeps down, its top
     went in leaned too far: its spring went up behind the little block it should press on, not under it,
     and you don't feel that going in. Look at the doorway from behind: the spring's bump sticks out
     toward you beside the block over the door's top, instead of hiding under it. Take it out and put it
     back leaning the top in less.
   - If it won't come all the way in under the trim, its top is leaned in much too far (its sides meet
     the tops of the little slopes up the sides of the doorway): lean it less.

   Do it until it goes in first time. Then:
   - lift it a little by its handle and let go: it should snap straight back down;
   - it should settle and pull itself in, with a hairline all round and no wobble;
   - turn the doorway face down, then upside down, and shake it gently: the door should stay put and
     not tick;
   - lift it by its handle with a fingernail until it stops: it should feel light, about the weight of
     an egg (the whole door, on both its springs, takes about twice that). Let it down a hair, pull the
     bottom toward you, let it drop, and it comes out;
   - in and out ten times: the little springs should spring back and nothing should crack;
   - with the door out, hang a full litre bottle from the handle on a string for a few seconds; it
     should hold;
   - look into the slot over the doorway from behind: its far wall, the face the door's top tabs press
     on (it prints as a bridge), should be clean, not sagging toward you. Look at the threshold's slope
     (clean), and at the handle: the grip and the gap behind it should come out square, not slumped.
     Plate 1 has nothing on it taller than the doorway but the half door, so above the walls its handle
     prints on its own, just as the real door's does on plate 3, and comes out the way the real one
     will.

   If it's too stiff, too loose, or the handle is soft, see "If the roll-up door isn't right" at the end
   of "Changing it".
3. **Door (plate 2).** Hold the little doorway upright with its 3 mm thick sill at the bottom and
   the side with the slot in the sill toward you (that's the inside). Hang the little door the same
   way as the real one (step 1 of "Putting it together"), pushing it up about 0.4 mm while you swing
   the bottom pin out along the slot. It should swing in freely past 90 degrees and stop against the
   strip on the latch side so it can't swing out. The little door is short, so it has to tip about
   7 degrees to hang where the real one tips 3, and it has less room in its slot: it goes in pushed
   up anywhere from 0.25 to 0.475 mm, the real one from 0.275 to 0.55. If it scrapes but goes
   in, the real door will be easier; tell Claude only if it won't go in at all. (The little doorway
   is built like the real one, not cut out of the wall, so moving the door along the wall to your
   standard place didn't change it.)
4. **Roof peg (plate 2).** Stand the peg block up so the peg points up, and set the bit of roof on
   it. It should drop on and lift off without forcing.

Pin holes are already 0.35 mm bigger all round than their pins and the roof peg holes 0.4 mm bigger
all round than their pegs; the snap parts and the skids' pegs have 0.2 mm round them (the skid pegs are
a snug push fit), and each corner angle has about 0.1 mm round it in its recesses. Each barb hooks
0.45 mm under its ledge. If anything is too tight or too loose, ask Claude to change that gap by 0.1 mm
(by 0.05 mm for the corner angle, or the barbs' catch; a tight skid peg is the gap round the skid pegs,
not the snaps') and remake the files. The sizes are at the top of `make_barn_garage.py`.

## Cleaning up the parts

- Let the plate cool right down before you flex the parts off. Don't push a scraper under the ends
  of a wall (the mitred ends come to a thin edge) or under the prongs: each prong's leg is a thin
  strip lifted just off the plate, joined to the wall at the top and to its barb at the foot. Flex
  the plate to free the corner angles; don't bend them.
- Peel the brim off each skid and trim what's left along its bottom edge with the knife. Mind the
  outer skids' little pegs (1.6 mm); don't snap them.
- With a fresh hobby knife, take a light chamfer off the first-layer lip on: the posts, stops and
  barbs under each wall, the inside edge of the mitre at both ends of every wall, the floor's face
  all round its edge, the roof pegs on the end walls, the door's two pins, and the mouths of the peg
  holes under each roof sheet. Don't scrape the mitre faces, and don't trim the barbs' flat tops.
- Look down each corner recess and pick out any string or blob with the knife tip, so the angles
  sit flat.
- Snip any loose strands between the studs on the inside with flush cutters. Don't sand the
  outside; it would fill the siding grooves and the slat grooves on the roll-up door.
- Leave the four little springs in the top edge of the roll-up door alone. Don't trim them or glue
  anything near them. The two tabs among them are the first three layers of the door's print, so flex
  the plate to free the door rather than pushing a scraper under its top edge.
- Cut any strings in the window at the point where they join, holding the thin window bars from
  behind with a fingertip.
- Lay each long wall on glass. At 201 mm long with 1 mm studs it may bow a little. If it rocks or a
  sheet of paper slides under the middle, set the bed to 55 °C, lay the wall framing-side down on it
  under a sheet of paper and a flat board with about 1 kg on top, leave it 10 minutes, then let it
  cool before lifting the weight.

## Putting it together

You'll need two rubber bands that go round the garage (or painter's tape), and glue for the
corner angles. Gel super glue is fine in small dots; clear contact cement (E6000) or 5-minute epoxy
can't leave a white haze on black plastic the way super glue's fumes sometimes do. Not water-thin super
glue: it runs down the corner into the floor's notch and glues the walls to the floor, and then the
model no longer comes apart. `how it goes together.png` shows the order.

1. **Door, in the loose door side, and leave it there.** Hold the door side upright, inside toward
   you. Hold the door with its knob away from you (it faces the outside), the pins on the side
   toward the roll-up end (the nearer corner), the longer pin up. Push the top pin up into the hole in the doorway's head,
   **keep pushing up** (about half a millimetre), swing the bottom toward the wall so the bottom pin
   slides along the little slot in the sill, and let it drop into its hole. It swings in past 90
   degrees and, shut, rests against the strip on the latch side. If a pin is tight, twist a 2.7 mm
   drill bit by hand in its hole; never lever the door. Leave it in: once the wall is on the floor
   the floor closes the slot and the door can't come off. A bit of painter's tape across the inside
   holds it shut while you handle the wall.
2. **Floor.** Lay the floor face up on a flat table, without the skids. The skids go on after the
   corner angles, so the angles' feet can be glued level with the bottom of the skirts.
3. **Plain side.** Hold it over the side of the floor with a notch for every stud (no long notch),
   siding outside the floor's edge. Line up the posts along its bottom with the notches and press
   straight down on the top of the wall over each of its four prongs until it clicks. It leans out a
   little at the top; that's fine for now.
4. **Door side**, with its door hung, the same way on the side with the long notch under the
   doorway. Press on the wall, not the door; four prongs. Take the tape off.
5. **Lofts.** Push the top of the plain side in so it stands straight, and lower a loft in at one
   end, floor side up, its end lined up with the ends of the long walls' top plates: its joists rest
   on the top plates of both long walls and its four lugs drop into the notches. Either way round
   fits. Do the other end the same way (at the roll-up end the loft's edge lines up with the door's
   hinge side, over the end of its header; the door swings in under it without touching). The lofts
   then hold both long walls straight.
6. **Roll-up end.** Hold it over the end of the floor nearer the door (the end whose edge has a
   short notch in the very middle and two more each side), peak up, roll-up facing out, and lower it
   straight down past the loft and the long walls' mitres. Its two prongs are under the sides of the
   doorway, one near each corner; press over each until it clicks. The roll-up door is not in yet.
7. **Back end.** The same way at the other end, past the other loft. Its two prongs
   are one near each corner.
8. **Band the corners.** Put a rubber band (or a loop of painter's tape) round the walls about
   15 mm above the table, and another about 10 mm under the top of the long walls, just tight enough
   that each corner closes on its mitre top to bottom. Not tighter: too tight bows the long walls in.
9. **Corner angles.** The angles come in two hands, two of each: one hand fits the door side's back
   corner and the plain side's roll-up corner, the other hand the other two. Hold an angle foot down,
   its inside corner to the garage's corner. The leg whose top stands a little higher, with its outer
   corner cut off at a slope, goes on the end wall, its top just under the black trim band across the
   top of the roll-up end, or just under the rake board on the back end; the other leg goes on the
   long wall. If the higher leg would come on the long wall, it's the other hand: try it on the next
   corner (forced in, its top catches on the long wall and it won't press flat). Try all four dry
   first: ease the rubber bands out from the corner with a finger, press the angle straight into its
   two recesses with its foot on the table, and let the bands back over it. It should sit flat with a
   hairline gap along both edges. Then glue them one at a time: take the angle out and put 3 or 4
   pin-head dots of gel super glue in a row down each recess floor, in the half nearest the corner
   (each floor is a strip about 1.6 mm wide, and the angle covers the 1.45 mm of it nearest the
   corner), the lowest at least 10 mm above the table (the floor's top is about 7 mm up) and the
   highest at least 2 mm under the top of the long wall, so no glue reaches the floor or the roof; or a
   hair-thin line of contact cement or epoxy down the same half, between the same heights. Press the
   angle back in with its foot on the table, let the bands back over it, and hold it for half a
   minute. Leave the bands on for 15 minutes for super glue, an hour for epoxy, or overnight for
   contact cement; then take them off.
10. **Skids.** Lay the two inner skids (notched on top) on the table under where the joists go,
    their end pegs up, and the two outer skids (flat on top) under the floor's long edges, their two
    small pegs up. The outer skids only go one way round: each one's pegs sit nearer one face, and
    the four shallow notches along its top are on that face too; that face goes to the outside.
    Lift the garage onto them: the inner skids' pegs go into the holes in the floor's
    end bands, the outer skids' pegs into the holes near each end of the long edges. They are a snug
    push fit. If the inner (notched) skids fall out when you pick the garage up, a drop of glue on
    their pegs keeps them. Never glue the outer skids: they lie right under the long walls' barbs,
    and glued on, the walls could never be unclipped from the floor. If one drops out, put it back
    and stand the garage on it.
11. **Roof.** Lower sheets first: hold one ribs out with its cut-off edge at the top over the steep
    edges, and lower it straight down so its two slots drop over the two pegs on that side. Do the
    other side. Then the upper sheets: ribs up, the raised ridge strip at the peak, so the two holes
    drop over the two pegs on that side and the tail laps over the lower sheet. Always lift a roof
    sheet straight up, never slide it along its pegs.
12. **Roll-up door, last**, from outside, roof on or off (any time after the bands come off in step 9).
    Hold it by its handle, slats out, its bottom about 6 mm (1/4 in, a pencil's thickness) out from the
    wall and its top leaning in a little more, so the top goes up just inside the wall. Push it straight
    up under the trim over the doorway until it stops: it gets springy just before it stops. Let it down
    about a millimetre, then push the bottom in over the white threshold: the top comes out as it goes.
    Let go. It settles on the threshold's slope and pulls itself in against the sides. **Then check
    it:** lift it a little by its handle and let go. It must snap straight back down. If the lean was
    off, you can tell which way:
    - **It stops dead about 2 to 3 mm early, before it gets springy:** it is caught on the trim. Don't
      push harder; that can snap the two little tabs at its top. Let it down, lean the top in a little
      more, and push up again.
    - **Lifted a little and let go, it stays up or only creeps down** (and it lifted with no spring): its
      top was leaned in too far, and its two hidden springs went up behind the little blocks they press
      on instead of under them. You don't feel that going in, and nothing is harmed. Take it out (see
      "Taking it apart") and put it back with the top leaned in a little less.
    - **It won't come all the way in under the trim:** its top is leaned in much too far, and its sides
      meet the tops of the two little slopes up the sides of the doorway. Lean the top in less.

## Taking it apart

**Roll-up door first:** a fingernail under its handle, lift until it stops (about a millimetre),
let it down a hair, pull the bottom toward you, let it drop, and take it out. Don't force it past
where it stops. It comes out with the roof on or off. (If you leave it in, it rides with the glued
box, because it hangs on the end wall, not on the floor.)

Then lift the upper sheets straight off, then the lower sheets. Lift each loft straight up. Lift the
garage off its skids: the outer two must come off, because they cover the long walls' barbs (glued
inner skids can stay on). The four walls are glued into one box, but the box still unclips from the
floor: look underneath, and just inside each wall you can see the barbs in their slots. Push each
barb out, toward the siding, with a small flat screwdriver, only just far enough to clear its ledge
(about half a millimetre), and ease that side of the box up a little. Work round the box; when all
12 barbs are free, lift it straight up off the floor. The door comes off only now, with the box off
the floor: lift it about half a millimetre and tip the bottom in, out of the slot.

## Where the model differs from the real garage

- **Held at the base models' sizes so the joints that worked in print stay the same** (they would
  be too small at 1:36): the siding is 1.4 mm thick (about 2 in at full size); the studs are as deep
  as the barn's, 3.7 mm (they look 5 1/4 in deep from inside, and the walls 7.2 in thick at the
  openings); the floor joists are 5.8 mm (the floor's skirt reads 9.7 in); the bottom plate is
  1.6 mm (2.3 in), so the studs in the model are 77.5 in, not 78.3; every snap joint, the corner
  recesses and the vent recess are the barn's exactly. The stud, plate and joist widths, the
  heights, the openings and the overall size are true to scale.
- The door is 2 mm thick (2.8 in; a real one is 1 3/4 in), so its pins are strong enough.
- Every framing member runs the full depth of the wall, so each wall prints lying flat on it. Your
  gable studs and backing are 2x4s laid flat; on the model they show their 3 1/2 in face but are as
  deep as the wall. The truss chords are drawn their true 3 1/2 in deep.
- The end truss has a collar tie and king post, as the 3D designer draws barn trusses; your end
  truss lesson had only the four chords. There are no trusses or roof deck between the barn ends, so
  you can see in with the roof off.
- On the real building the side wall's upper plate laps over the end wall. On the model the walls
  meet on mitres, glued, with the black corner angle over the joint as the corner board. Each angle
  covers 4 1/4 in of each wall (3 mm), a little more than a 3 1/2 in corner board, so it has enough
  glue under it.
- The roll-up door lifts out. It doesn't roll up or stay part open, and there's no drum or track
  inside.
- The dark gap under the trim over the doorway is 3.1 in (the drawing's is 2.2 in). In places you can
  see through it into the garage, where the door's hidden springs need room.
- The white threshold strip is 0.94 in (the diamond plate is 0.66 in); the diamond plate itself is not
  modelled.
- There are 0.43 in gaps at the sides of the roll-up door.
- **Where the roll-up door sits depends a little on how your printer prints:** its springs push it to
  its stops, and in a print whose holes come out small it sits about 0.2 mm further out and 0.3 mm
  higher than drawn (up to 0.4 mm higher if they come out smaller still). Its slats are then about
  flush with the siding (drawn, they are 0.4 in behind it),
  a thin dark line up to about 3/4 in high shows over the white threshold, and the dark gap under the
  trim is about 2.7 in instead of 3.1.
- The roll-up door's handle is 16 x 2.8 in, standing 4.5 in out, about 2 3/4 times a real one, so a
  fingernail can lift it. The drawing has no handle; you asked for one at the bottom middle.
- Seen from inside, the roll-up door is a thick white block (6.9 in).
- A 2.3 in deep slot runs along the inside of the top plates over the roll-up doorway, where the
  door's top goes.
- The gable vents are set into the siding instead of standing out (Alan, Nov 3 2026), with four
  louvres instead of the designer's five: with five, the louvres would print thinner than a line.
  The bottom louvre stands on the frame, so the vent shows four slots and three free louvres; a
  gap under it would be too narrow to print open.
- The roll-up end's band sits right on the wall top, 1/4 in higher than the designer draws it, so it
  is clear of the corner angles.
- On the door side the window's head trim is 0.8 in lower than the steel door's: the window top
  follows your lofted-wall rule (74.8 in) and the door opening is 75.6 in tall. With the door and
  window about 7 ft 5 in apart (opening to opening) in your standard layout it hardly shows.
- Beside the steel door's latch-side casing, the siding groove 1/2 in past it (56 in from the middle
  toward the roll-up end) is left out from the floor to the top of the casing, as if the casing
  covered it; above the casing and in the skirt it runs on, as the grooves over the door do. The
  model's grooves are about 3/4 in wide at full size, wider than real ones, so that one would have
  run right along the casing's edge as a slot.
- The steel door hinges on its left as you look at it from outside, toward the roll-up end, as the
  designer's door does, so it swings in toward the near corner. Your standard says where the door
  goes, not which way it hangs.
- The sizes stay the 3D builder's: your building page's text lists a "7 ft x 9 ft" roll-up and a
  36 x 72 in walk door, but the site's 3D builder, with your standards file, still draws the
  8 x 6.4 ft roll-up and the 36 x 75.6 in (3 x 6.3 ft) door, and so does the model, as you chose on
  Nov 3 2026 ("Keep builder sizes", question 14).
- Four 16 in layout marks land on other framing and their studs are left out (the framing they
  hit stands there): on the door side the stud 96 3/4 in from the middle toward the roll-up end, the
  first of the double at the 4 ft mark: the door's edge is on that mark, so the door's hinge-side king
  stud stands exactly where it would (over the header there is a short stud on its partner, 95 1/4 in,
  but none on it); on the roll-up end the stud 51 in from the middle toward the plain side (it would
  overlap the roll-up's full stud by 0.75 in); and on each end, the roll-up end and the back end, the
  stud 61 in from the middle toward the door side (it runs into the corner, past the end stud).
  (Before the door moved, the door side's was the stud 112 in toward the back end, against the
  door's latch-side full stud.)
- Under the floor top, out of sight: posts under the roll-up doorway (at the middle, 16 in and
  35 in each way; none under its sides, where the clips are), and on the back end a post 20 5/8 in
  from the middle toward the door side, with no stud over it.
  They hold the skirt up in the print; without the 35 in ones and that one the skirt would bridge
  22 mm, more than the 20 mm a bridge should be. With them the longest is about 16 mm.

**Numbers that are the 3D designer's or our choice, not yours yet.** Everything not listed here is
yours (the 134 x 288 in size, the 51 in roof, where the door and window go (your standard layout),
the framing rules, the stud layout, the gable board, backing and stud spacing, the 4x8 floor layout,
the trim boards, the flush vent, the glued corner angles). The questions are the ones to answer;
the model uses the default in brackets.

| Number | In the model | Whose | Question (default used) |
|---|---|---|---|
| Width | 134 in actual | yours (Sep 30 2026, confirmed Nov 4 2026), but the designer still draws 144 | 1. Model a 12-wide at its actual 134 in, or the designer's 12 ft? **Answered Nov 4 2026: 134 in** |
| Window top | 74.8 in (sill 40 in) | your lofted-wall rule from the Side Lofted Barn, carried over | 2. Your rule (5 in header right under the top plate, 74.8 in), the designer's 77.8 in, or 75.6 in to line up with the door, with a 3 in flat header? [74.8 in] |
| Steel door framing | 36 x 75.6 in opening, two flat 2x4s over it, short studs to the top plate, hinged on the left from outside (toward the roll-up end, the near corner), hung before the door side goes on | designer's door, your "taller door" rule; which side it hangs on is the designer's, your standard doesn't say | 3. Right, and hinged on that side? [yes] |
| Stud cut on the 6.9 ft wall | 78.3 in (82.8 less three 1 1/2 in plates) | worked out | 4. Is that your cut? [78.3 in] |
| Roll-up door | lifts out the front: lift it by its handle until it stops, let it down a hair, pull the bottom out, let it drop | yours | 5. Should it open? **Answered Nov 3 2026: "Do 4 the lift out add a handle in the bottom middle to lift it up"; "Front lift-out"** |
| Lift-out only | it is either in or out; it doesn't stay part open | ours (the lift-out design) | 15. Is lift-out only OK? [yes] |
| Roll-up handle | black, 16 in long, 2.8 in tall, standing 4.5 in out, at the bottom middle of the rail | its place yours; its size ours | 16. Right size, or smaller (12 in) or bigger? [16 in] |
| Threshold | white strip 0.94 in high under the door (the door's bottom hangs on its sloped back) | ours; the designer's diamond plate is 0.66 in | 17. OK? [0.94 in] |
| Dark gap over the roll-up | 3.1 in under the trim (the drawing's 2.2 in), see-through in places where the hidden springs are | ours | 18. OK? [yes] |
| Slot over the roll-up | 2.3 in deep along the inside of the top plates over the doorway, seen from inside with the roof off | ours | 19. OK? [yes] |
| Roll-up end's clips | under the doorway's sides, 51 in each side of the middle | ours | 20. OK? [yes] |
| Roll-up door's plate | prints with the end walls, still one colour change | ours | 21. Or on its own plate? [with the end walls] |
| Putting the roll-up door back | takes a little knack: its top leans in about half a millimetre as you push it up (the fit test teaches it; too little and it stops early, too much and it goes in without its springs holding it down, which the let-go check in step 12 shows); the two tabs that need this stop it ticking when the model is face down (without them it goes in with no knack, but its top can move about 0.6 mm) | ours | 22. Keep the tabs? [keep them] |
| Black filament's Min print speed | 20 mm/s (Cooling), as saved in the file for all three filaments. Above the walls on plate 3 only the roll-up door's black handle prints, about 1 to 3 seconds a layer; Flash Studio slows a layer down to give it 8 seconds, but not below this speed | Flash Studio's, in the settings the file carries | 23. Keep 20, or set filament 2 (black) to 5 mm/s before you slice plate 3, so the grip has time to cool? [keep 20] (change it if the fit test's grip comes out soft: see the last row of "If the roll-up door isn't right") |
| Roll-up side gaps | 0.43 in each side | ours | |
| Roll-up framing | king studs to the top plate, no header, bottom plate cut out across it | your garage-door rule; the bottom plate cut-out is ours | 6. Right? [yes] |
| Gable studs | 24 in apart, the tape hooked at the plain-side edge of both ends (the left of the roll-up end as you look at it): 43 and 19 in toward the plain side, 5, 29 and 53 in toward the door side | spacing yours, starting end ours | 7. Which end does the tape start from? [the plain-side edge, on both ends] |
| Lofts | 4 ft deep at both ends, 2x6 joists 16 in apart | designer, who assumed it too | 8. Your loft depth? [4 ft] |
| Skids | four 4x6, centres 8 in and 37 in in from each side | designer's skid table | 9. Right? [yes] |
| Front band | right at the wall top | ours: 1/4 in higher than the designer draws it, so it clears the corner angles | 10. OK? [at the wall top] |
| Collar tie and king post | in the end trusses | designer | 11. Keep them? [yes] |
| Corner angles | 4 1/4 in on each face | our choice (glue land) | 12. OK wider than a 3 1/2 in board? [yes] |
| Four layout studs | left out where they land on other framing (see above) | our choice | 13. Drop them, or move them (which way, how far)? On the door side, where the king stud is on the 4 ft mark, should a short stud go on that mark over the header? [drop all four; no short stud there] |
| Wall height | 6.9 ft (82.8 in) | designer; you said keep the walls as they are (Oct 11 2026) | |
| Roof shape | knee 0.38 of the width out, rises in the designer's ratio, eave 0.42 ft down the slope (2.03 in level), sheets 1.2 in past the ends, the upper ones 1.62 in further | designer's bend at your 51 in peak | |
| Opening sizes | roll-up 96 x 76.8 in (8 x 6.4 ft), centred; steel door 36 x 75.6 in (3 x 6.3 ft); window 25.2 x 34.8 in | the designer's items, which the site's 3D builder still draws with your standards file | 14. Your building page lists a "7 ft x 9 ft" roll-up and a 36 x 72 in walk door for the Lofted Barn Garage. Which sizes should the model have? **Answered Nov 3 2026: "Keep builder sizes"** (8 x 6.4 ft roll-up, 36 x 75.6 in door) |
| Roll-up details | 32 slats 2 1/4 in, bottom rail, latch plate 0.72 x 0.38 ft at 0.42 of the height, 0.62 ft in from the right (now on the lift-out door) | designer (your photograph for the slats) | |
| Steel door details | six panels at the designer's spacing, knob 0.32 ft in from the latch edge at 0.44 of the height, all white | designer | |
| Faux loft window | 31.2 x 22.8 in, bottom 7.44 in over the wall top, 3.6 in frame | designer | |
| Gable vents | 13.4 x 9.1 in, 11 in under the roof line's peak, both ends; four louvres | designer; four is ours | |
| Back band | 20.6 in over the wall top (the loft line) | designer | |
| Floor joists | 2x6, 16 in apart | designer | |
| Roof deck | 7/16 in under the steel: the roof is drawn on top of it, 51.46 in to the top of the deck | designer | |
| Siding grooves | 8 in apart; the one 1/2 in past the steel door's latch-side casing left out beside the casing | designer's look; leaving that one out is ours | |
| Rake board | a black board under the roof's edge round each barn end | designer's look (2 mm wide on the model) | |
| Hidden posts under the floor top | under the roll-up doorway at the middle, 16 in and 35 in each way (none under its sides); on the back end one 20 5/8 in from the middle toward the door side, with no stud over it | ours, so the skirt prints | |

**Where the roll-up door is built a little differently from its plan** (`spec_rollup.md`, Nov 3 2026), and
why. The checks measure the real parts at 141 places along the doorway, and as printed at every place near
its sides where a layer's outline changes (about 190 in all), where the plan's own proofs used 77; that,
and two reviews, turned up a few things:

- **The two slopes up the sides of the doorway stand back 0.45 mm on their first layer.** As printed,
  their first layer and the door's (0.25 mm thick, where every other layer is 0.2) can overlap in a strip
  just inside the door's back edges, between the plan's places. That holds the printed door out a whole
  layer and takes a quarter of a millimetre off its lift. Stood back 0.45 mm they clear it at every print
  accuracy tried, with 0.125 mm to spare even with the door pushed sideways as far as the slopes let it,
  and the door sits where the plan says (as printed 0.20 out and 0.30 up, stopping at 1.15 mm and coming
  out from 0.55). Nothing changes as drawn.
- **The two little blocks the springs press up against are 0.7 mm wide, not 1.4.** A bent spring finger
  slopes (about 12 degrees at the top of the lift), so a flat block presses on its bump only along the
  block's edge nearer the finger's root. The plan's 1.4 mm block put that edge 0.7 mm nearer the root
  than the plan's own spring numbers assumed: as printed the finger would have bent to about 1.86 %
  strain instead of 1.71 % at the top of the lift, and going back in its tip would have reached the
  bottom of its slot. Ending the block at the middle of the bump puts the press where the plan worked its
  numbers out: 1.71 % (1.73 % as printed), the tip 0.24 mm clear as printed, and the springs as strong as
  planned.
- **Under the latch plate the slat grooves stop square,** at the latch's rectangle, as they did on the
  printed-shut door, and the plate's white boss sits on that fill. Stopped at the plate's cut corners,
  two grooves would end in tapers thinner than a line, or run on under the boss with its corners over
  air.
- **The white threshold's sloped back is exactly 45 degrees right down to its foot** under the floor
  top. The plan's foot point tilted it about 1 degree, so it stepped 0.203 mm a layer instead of 0.2.
- **The fit test's short walls and half doorway are cut inside a siding groove.** The short roll-up end
  stops over its post 35 in from the middle, 1.5 mm short of the bit of floor, which is cut where the plan
  says (cut there too, its skirt would hang past the post with nothing under it); the short plain side
  stops inside the groove over its stud 112 in from the middle; the half doorway starts in the groove
  over its end stud. Cut beside a groove, each kept a strip of siding about 0.3 mm wide on its top layer,
  thinner than a line.
- **Fit-test plate 1 is the half doorway and half door alone.** With the corner's bit of floor and skid
  stub on the same plate, they were still printing while the half door's handle was, which gave the
  handle's layers about 7 seconds each, where on plate 3 the real handle prints on its own at 1.3 seconds
  a layer. Now nothing but the handle prints over the walls on plate 1 either, so the fit test shows how
  the real one comes out. The whole corner is on plate 2.
- **Going back in, a spring finger bends up to 2.23 mm** where the plan says 2.15 at most: the door
  reaches its stop tipped, and the finger's bump meets its block with its front corner first. At 2.23 mm
  the finger is still under 2 % strain (1.79 % as printed) and its tip stays 0.15 mm clear of the bottom
  of its slot as printed.
- **Leaned in too far going back in, it still goes in, but wrong.** The plan says its top won't come out;
  it does come out, pushing the two springs back behind their blocks (up to about 1.5 mm), where they
  don't press the door down, and you don't feel it. That bend is under 1 % strain, so nothing is hurt,
  and the door comes out the usual way; the let-go check in step 12 shows it. Leaned in further still, it
  won't come all the way in: its sides meet the tops of the two slopes.
- **Printed numbers:** the door stops 1.15 mm up as printed (the plan says 1.10) and has a 0.60 mm window
  to come out (0.55). At the other print accuracies the plan tried, it stops 0.95 mm up or more and the
  window is 0.40 mm or more (the plan's least is 0.30), and its bottom has no play (the plan allowed up to
  0.14 mm).

## Changing it

Everything is made by `make_barn_garage.py` from the numbers at the top of the file (building size,
wall height, roof, door, roll-up and window sizes and positions, loft, skids, clearances, the snap
joints, the corner angles), each with a note saying whose number it is. It writes the `.stl` files
and the two `.3mf` files. `draw_barn_garage.py` draws `how it goes together.png`.
`check_barn_garage.py` then proves, in about 12 minutes (most of it the roll-up door's motions), that
the parts still fit and print:

- the files: the `.stl` and `.3mf` files in the folder are exactly what `make_barn_garage.py` makes now
  (it is run again in a scratch folder and every file compared), with no others, so none is left over
  from an older version;
- the pieces: each is one solid piece that fits the bed, and the walls and floor make up the body
  with 0.2 mm round every post and prong; the `.stl` files, read back as written, have no collapsed
  triangles and no open edges, each holds the same piece as the `.3mf`, layer by layer, and each
  fits the bed as it opens;
- the snap joints: each wall goes on straight down in the order above (the door side with its door
  hung) with nothing in the way but its barbs, stands on the floor, and can't lift or slide once
  clicked in; every prong's leg is free up to where it bends from (the roll-up end's too); the barbs
  still catch once cut into layers the way they print; the floor keeps at least 0.9 mm between its
  notches and slots; the plain side leans out 1.7 mm on its own but the lofts hold it 2.1 to 1;
- the walls print flat with nothing steeper than 45 degrees that isn't a short bridge (the longest
  is about 18 mm, the ceiling of the door's slot over the roll-up doorway; the longest skirt bridge
  is about 16 mm, on the back end), all the black in the top 0.6 mm and nothing white above the
  siding's top layer (one colour change), the latch plate no longer in the wall (it is on the door),
  the four dropped studs exactly the ones listed above; round the roll-up doorway the ceiling of the
  door's slot, the threshold's slope (exactly 45 degrees, 0.2 mm a layer) and the side slopes print as
  designed, the side slopes' first layer set back so it can't catch the door's first layer;
- your standard layout: the door side's studs, the door's and window's full and king studs, the
  short studs over the door's header and under the window's plate are where the 16 in layout and the
  two openings put them; nothing is in the door's opening but its stop, or in the window's but its
  sashes; no siding groove runs within 0.5 mm of a casing's edge; the prongs keep clear of the
  doorway (the one under the window hangs from the bottom plate, 27 mm under the sill); and the loft
  at the roll-up end has its lug over the door's hinge-side king stud, 1 mm over the header, with the
  header and full stud under its notch whole;
- the corners: each angle sits in both recesses on about 1.5 mm of each floor, 0.1 mm clear all
  round, presses straight in, still fits with a wall 0.15 mm out or in, also as printed, and keeps
  0.2 mm under the roof and 0.15 mm under the band or rake board;
- the gables: the vent's four gaps (the one under the frame's top bar too) and its three free
  louvres are each wider than a printed line on every layer, the bottom louvre standing on the
  frame, and the gable board, studs, chords, collar, king post and backing are where they go;
- the roll-up opening is 96 x 76.8 in; the lofts rest on the plates, can't slide, drop in past
  the hung door, and can't lift out of their notches under the roof;
- the roll-up door, on sections of the real parts at 141 places along the doorway (every 0.05 mm
  where the side slopes meet it), as drawn, as printed (holes 0.1 mm small, the door 0.05 mm big; and
  then also at every place near the side slopes where a printed layer's outline changes, about 190 in
  all) and at four other print accuracies, and in 3D on the parts cut into their layers: it is one
  piece, black only from the walls' trim layer up, and prints with nothing thinner than a line; under
  the latch plate its slat grooves are filled square; it sits in with nothing rigid touching and
  settles where its springs push it (in 3D too, touching nothing at each printed seat); pushed any
  way, rigid parts stop it, and pushed sideways the side slopes stop it before its side gaps close; it
  holds upside down (1.6 to 2.3 times its weight) and face down (1.7 to 2.4 times what it needs), with
  the springs' numbers taken where the little blocks really press on them; lifted, it meets a rigid
  stop at 1.7 mm (1.15 as printed) with the springs under 2 % strain and their tips clear of their
  slots, and from 0.8 mm (0.55 as printed) to just under the stop it comes out by the planned motion
  and three others a hand makes (at the stop itself one of them binds, hence "let it down a hair"); it
  goes back in leaned 0.3 to 0.75 mm at every swing tried, and it catches if not leaned, stopping dead
  2 to 3 mm early with no spring to feel (pushing harder would load its two tabs edgewise, which take
  about 3 1/2 times the hardest lift: hence "don't push harder"); leaned further it still goes in, but
  with its springs behind their blocks instead of under them (up to 1.5 mm, under 1 % strain), which
  you don't feel but the let-go test in step 12 shows (seated so, it is pushed down 0.03 N at most,
  against 0.67 N seated right), and it comes out the usual way; leaned further still it won't come all
  the way in; nothing of the door itself rises over the front loft, which it misses by 0.35 mm at the
  closest, or the roof (leaned in too far, one of its little springs can brush the loft and bend out of
  the way); the steel door and its casing are over 10 mm away, and there's room in front for a hand;
  the handle takes about 22 N (2.2 kg) to break, and has a gap behind its grip 1.6 mm deep and 5.3 mm
  wide for a fingernail, with nothing under the grip;
- the steel door fits shut, swings in to about 101 degrees, won't swing out, hangs on the loose door
  side the way step 1 says (pushed up anywhere from 0.275 to 0.55 mm), and is captive once the wall is
  on the floor; the fit test's door does the same, also as printed; the steel door's six panels are
  where the designer draws them, at fractions of the opening, so it is the 12x24 Garage's door;
- the roof sheets rest on the barn ends, are held by their pegs, lock each other on, and go on and
  off straight up;
- the skids fit under the floor, are held by their pegs, clear the barbs, and stand level;
- every plate's parts are inside the bed and apart, clear of the prime tower, the skids far enough
  apart for their brims, and the brim settings in the file are the ones above; on plate 3 the white
  stops at the 5.05 layer and only the roll-up door's handle stands over the trim, and on fit-test
  plate 1 only the half door's handle stands over the doorway, layer for layer the real one's, so it
  prints the same way; in the fit test only the skid stub and the angle stub have brim settings of
  their own; every wall and every fit-test piece cut from one carry the bridge modifier, over their
  whole siding and nothing under it, and laid across the studs as it sets them no bridge is over
  15.7 mm; on the end walls it stops halfway up the collar tie, and the second one lays the gable over
  it in bridges running up the wall, 9.1 mm at most; the floor carries its modifiers on the layer over
  its seams, the only layer of it over anything, and every bridge there crosses a seam; every modifier
  is a plain box with just the direction it should set, and every piece lies on its plate unturned;
  nothing else has an overhang more than 5.2 mm across, in any direction, as high as the siding, or
  anywhere a slot like a floor seam, so it can't sag whichever way Flash Studio lays it;
- the fit test's half doorway and half door are cut from the real parts and move as the real door
  does, drawn and as printed (the same seat, stop, least lift, way out and lean at every swing), the
  half door, at its own weight, holds about as the real one does (upside down 1.5 to 2.1 times its
  weight, the real door 1.6 to 2.3), and where its short walls and half doorway are cut, inside siding
  grooves, no layer is left with a strip thinner than a line;
- measured off the parts, at full size: 134 x 288 in, 82.8 in walls, the 51 in roof, the 2.03 in
  eave, every opening and where the door and window are (the door's edge 48 in from the roll-up
  end's corner, its centre 6 ft 6 in toward the roll-up end; the window's centre 3 ft 6 in toward
  the back, halfway between the door and the back), the faux window, bands, vents, gable framing,
  skid positions, the 4 ft lofts, the angles' 4 1/4 in and the 1 1/2 in studs.

To make a different size, ask Claude to change the numbers and run all three.

**If the roll-up door isn't right** after the fit test, tell Claude what you saw. The fixes below are
numbers in `make_barn_garage.py` (with the roll-up door's other numbers), one row at a time. Each was tried
in Nov 2026: the files remade with it and `check_barn_garage.py` run on them. Whatever is changed, the files
must be remade and the checker must pass again before anything is reprinted.

| What you see | Change | What the checker said |
|---|---|---|
| Lifted a little and let go, it stays up or only creeps down | Nothing to change: it went in with its top leaned in too far, its springs behind the little blocks they press on. Take it out and put it back leaning the top in less (step 12) | no harm: pushed back there the springs bend under 1 % strain, and it comes out the usual way |
| It slides when the model is upside down | `PRELOAD` 0.6 **and** `FING_SLOT` 2.84: the springs pressed down 0.05 more (the most there is: 0.6 is the bumps' height), and the slot under each spring 0.1 deeper, which cuts 0.1 into the door's top, so the springs' tips keep their room | passes: it then holds 1.8 to 2.6 times its weight upside down; each spring's tip keeps 0.28 mm of its slot at the stop as printed (at least 0.2) and 0.2 mm going back in (at least 0.1). `PRELOAD` 0.6 on its own fails: the tips keep only 0.18 and about 0.1 |
| It ticks when the model is face down | `TAB_T` 0.85: the two top tabs one layer thicker, about twice as stiff | passes: it then holds 3.8 to 5.4 times what it needs face down, and goes back in with the same lean. (`TAB_BUMP_U` 0.2 more would press harder too, but fails: the lean that puts it back in shrinks under 0.3 mm) |
| Too stiff to lift, or it won't seat | First look for a string or blob at its sides or on the threshold's slope. Lighter springs would be `PRELOAD` 0.45 (0.1 less) | fails: it then holds only 1.3 to 1.8 times its weight upside down, under the checker's 1.5 rule. Only worth doing if your fit test shows the springs stiffer than the checker assumes |
| It hits its stop before its bottom clears the threshold | `LIP_H` 0.466: the white threshold 0.2 lower (0.66 in, the designer's diamond plate), so the bottom needs 0.2 less lift. Not `REB_H` more: on this model that lifts the door's springs into the front loft | passes: it then comes out from 0.6 mm (0.35 as printed), leaving 1.1 mm under the stop (0.83 as printed). The checker's threshold size (`THRESHOLD_IN`, open question 17) goes to 0.66 in with it |
| Seen from behind, the far wall of the slot over the doorway sags toward you, onto the door's top | `REB_U` 1.85 **and** `TAB_BUMP_U` 2.05: the slot 0.2 deeper and the tabs' bumps 0.2 taller (one layer each), so the tabs keep their push | passes: the same stop, window, holds and lean as now |
| The handle cracks | `HDL_LEG` 3.3: its legs 0.3 wider, inward | passes: it then takes about 24 N instead of 22; the gap between the legs for a fingernail is 4.7 mm instead of 5.3 (at least 4.5, so no wider than 3.3) |
| The handle's grip comes out soft or rounded | Not a number in the file: in Flash Studio, filament 2 (black) → Cooling → **Min print speed** 5 mm/s (it is 20) before you slice plate 3. Above the walls only the handle prints, about 1 to 3 seconds a layer; slower, it has time to cool. It changes nothing on the set's other layers. The fit test prints on filament 1, so to see it there, set filament 1's too | (a setting, not the model) |
