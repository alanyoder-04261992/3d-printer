# 12x24 Garage model — read me first

A 1:36 model of the shop-standard 12x24 Garage (one inch on the model = three feet on the real
building). You asked for it on Nov 3 2026 ("garage and lift garage 12x24"), at a scale where it
fits the bed. It is built from the
[8x12 Side Utility model](../shed%20model%208x12%20side%20utility/read%20me%20first.md): the
walls snap onto the floor with no glue, a black corner angle is glued over each corner, and the
two roof halves lift off so you can see the framing inside. The 8 ft roll-up door is its own
piece: it hangs in its doorway on little hidden springs, and you lift it out the front by a black
handle at its bottom middle, with the roof on (your choice, Nov 3 2026: "Do 4 the lift out add a
handle in the bottom middle to lift it up"). The white steel door swings in on two small pins.
The garage stands on four skids.

Sizes come from the 3D designer's shop numbers for the Garage (style G), with yours where you
gave them: 134 in actual width (the 12-wide is 11 ft 2 in, your rule of Sep 30 2026), 93 1/2 in
walls (89 in studs and three plates), 5/12 roof, 4 in eaves measured level. Both gables have a
louvred vent and a black band across them.

**Layout: your standard.** On Nov 3 2026 you asked us to go on yoder-storage-barns.com and see
the standard layout. The site's 3D builder loads your `designer-standards.js`, which puts the
doors and windows where your copy-this-build codes have them (Aug 2026), and the real garages in
the site's gallery agree. The model follows it:

- the 8 x 6.4 ft roll-up centred on the roll-up end;
- the 36 in steel door on the door side (the long side on your right as you face the roll-up),
  at the roll-up end: its near edge 4 ft in from the corner, its centre 6.5 ft from the middle
  of the wall;
- the window on the same side, centred between the steel door and the back end, 3.5 ft from the
  middle toward the back.

The first plan had the door 7.6 ft toward the back and the window 7.6 ft toward the roll-up end.
That was the designer's stock layout, from before your standards file.

| | |
|---|---|
| Footprint | 94.5 x 203.2 mm walls (3 3/4 x 8 in), 100.2 x 210.8 mm with the roof on |
| Height on its skids | about 100 mm |
| Roll-up door | lifts out, 96 x 76.8 in opening (8 x 6.4 ft); 2 1/4 in slats, bottom rail, black latch plate and a black lift handle at the bottom middle |
| Steel door | 36 x 75.6 in, white six-panel, swings in, knob outside only; 4 ft in from the roll-up corner |
| Window | 25.2 x 34.8 in, open, no glass, so you can look in through it; halfway between the steel door and the back end |
| Inside you can see | studs 16 in apart, your king studs and full studs, your 5 in loft header over the steel door, your flat window plate, rough sill, cripples, the roll-up's king studs running up to the double top plate, the end trusses' 2x6 bottom and top chords, gable studs, the vents' kings and sills, floor sheet seams |

## What to print, in this order

| File | What's on it | Filament | Time on the AD5X |
|---|---|---|---|
| `1 fit test.3mf` | Two plates. Plate 1, **roll-up door**: half a roll-up doorway and half a roll-up door, both full height, cut from the real ones; the door lifts out just like the real one, and the two are alone on the plate so its handle prints just as the real door's does on plate 3. Plate 2, **roll-up corner, door and roof peg**: a bit of floor, short pieces of the plain side and the roll-up end (its prong is under the side of the doorway), a 20 mm stub of corner angle and a 23 mm stub of outer skid, and behind them a short in-swing doorway and its door, a roof peg and a bit of roof | Any, one colour | plate 1 24 min (11.4 g), plate 2 24 min (8.4 g). **Print these first.** See "Checking the fit" below. |
| `2 all plates.3mf` | Everything else, one plate per print: | | |
| plate 1 | Both long walls and the steel door | 1 white, 2 black | 2 h 40 min, 70.2 g white and 0.5 g black, 1 colour change |
| plate 2 | Both roof halves and the four corner angles | 2 black only | 1 h 20 min, 56.6 g |
| plate 3 | Both end walls and the roll-up door | 1 white, 2 black | 1 h 34 min, 42.1 g white and 0.8 g black, 1 colour change |
| plate 4 | The floor and the four skids | 3 brown only | 1 h 57 min, 53.5 g |

The times and grams are Flash Studio's own for each plate (sliced again Nov 4 2026, with the
lift-out roll-up door and the walls' and floor's bridge settings): about 7 1/2 hours for
`2 all plates.3mf`, with about 112 g of white, 58 g of black and 54 g of brown. The roll-up door
itself is about 11.5 g of white (sliced on its own); the end wall lost the solid printed-shut door,
so plate 3 grew by only about half a gram and 4 minutes.

Start Flash Studio first, then open them with **File → Open Project** (Ctrl+O), or **Open
Project** on its Home page. Starting Flash Studio by opening the file itself can leave it stuck
on "Loading". If Flash Studio says the file is from a newer version, click OK; it loads fine. If
it asks about unsaved changes to your settings, click **Discard** (the file brings its own). The
files carry their settings: the Flashforge AD5X 0.4, `0.20mm Standard @FF AD5X`, and three
filaments, 1 white, 2 black and 3 brown. Pick a plate, then Slice plate and Print plate as usual.

**Check the slots in the Send dialog every time.** Flash Studio matches each filament to the slot
whose colour on the printer is closest, and the printer still shows the old colours. Click each
filament's slot box and pick it by number: filament 1 (white) on slot 1, 2 (black) on slot 2,
3 (brown) on slot 3.

Each wall prints lying flat, inside face down, so its trim (door, window and roll-up casings, the
band across each gable) is on top and already set to **filament 2**; the siding is filament 1.
Nothing white stands higher than the siding's top layer, so the wall plates change colour once,
for the last three layers. The plain side has no trim at all. The steel door is all white, so it
rides on the long-walls plate and adds no change. **The roll-up door prints on its back beside
the end walls,** white with a black handle and latch plate, still one colour change: its black
starts on the same layer as the walls' trim, and above the walls only its handle is still
printing, in black, which costs no change. On plates 1 and 3 the prime tower goes in the back
right corner, and those plates are laid out to keep it clear; plates 2 and 4 are one colour and
need no tower.

The `.stl` files are the same pieces one at a time, all one colour, if you'd rather set up a plate
yourself: `floor.stl` (already upside down), `door side.stl` (the long wall with the steel door
near one end and the window), `plain side.stl`, `roll-up end.stl`, `roll-up curtain.stl` (the
roll-up door), `back end.stl`, `roof half.stl` (prints twice), `corner angle.stl` (all four
angles, side by side), `door.stl`, `skids.stl` (all four skids) and `fit test.stl` (every fit-test
piece of both plates together: print the fit test from `1 fit test.3mf` instead, so the half door
prints alone on its plate). For two colours, and for the walls' and floor's bridge settings, use
the `.3mf` files.

**Settings:** already in the file: `0.20mm Standard @FF AD5X` with **Wall generator →
Arachne** (it shows in orange as changed), because the siding is only 1.4 mm thick and Arachne
fills thin walls solid. **Elephant foot compensation** is 0.1 mm (Quality tab, under Precision);
keep it there: the barbs, stops and posts under the walls print on the bed and fit with 0.2 mm to
spare, and the roll-up door's two little tab springs are its first three layers. No supports are
needed. Each wall, and each fit-test piece cut from one, carries a modifier, "bridges across the
studs", over its siding: it sets **External bridge infill direction** to 180, which Flash Studio
reads as straight across the studs. Left to itself, Flash Studio picks the direction afresh each
time you slice: it laid the half doorway's siding along its two end stud bays in 62 mm strands,
which sag, and now and then the door side's along all its bays, and every wall's bays are that
long. Across the studs none is over about 15 mm. It starts above the framing, so the prongs'
springy legs still print along their length. The floor has its own, on its second layer only, the
one over the floor sheet seams: "bridges across the long seams" over each long seam and "bridges
across the short seams" everywhere else. Left to itself, Flash Studio laid that layer along the
long seams, in strands about 195 mm long, each lying over a seam for up to about 70 mm and sagging
into it; now every strand crosses a seam. Leave them all in, and don't turn a wall or the floor on
the plate: the modifiers lay the bridges along the bed, not along the part, so a wall turned a
quarter turn would get the 62 mm strands every time, and the floor long strands down its long
seams again.

**Brims:** the four skids are set in the file to a **5 mm brim**, outer only. They are 203 mm long
and only 2.5 mm wide, and long thin parts need a brim. They stand 12 mm apart, so their brims don't
run together. The roof halves and the corner angles are set to **no brim**: each roof half is
210.8 mm long, only 4.6 mm short of each end of the bed, and on an angle a brim would leave a lip
along a board's edge. Snap the skids' brims off and shave the edge with the knife.

**Trim:** it stands 0.6 mm proud of the siding, the corner angles 0.65 mm. If you'd rather print
it all one colour, set every part to filament 1 and use a black paint pen on the raised trim, the
angles, the roll-up door's handle and its latch plate.

## How it holds together

- **The walls stand on the floor.** The floor reaches out under each wall, and the wall's siding
  carries on down past the floor as a skirt, hiding the floor's edge.
- **Posts and prongs.** Under every stud a short post drops into a notch in the floor's edge.
  Ten prongs go down slots in the floor: three on each long wall and two on each end wall. Each
  prong is a springy leg with a barb on its foot: going down, the barb pushes the leg out toward
  the siding; at the bottom it springs back in under a ledge with a click. Beside each leg a stiff
  stop keeps the wall's foot from sliding out. The roll-up end has two, under the sides of the
  doorway, one near each corner.
- **End walls first, long walls last.** Each end wall's gable takes in the corners above the wall
  plates, so the long walls are lowered in between the end walls, the same as the Side Utility.
- **The corners are glued.** Each wall has a recess two layers (0.4 mm) deep down its face beside
  each corner, and the outside corner itself is cut off at 45 degrees. Once all four walls are on,
  two rubber bands pull the corners shut and a black L angle is glued into the two recesses at
  each corner. Each leg covers 3 mm of its wall (4 1/4 in at full size). It sits on a strip of
  recess floor 1.45 mm wide on each wall, so use small dots of glue. With the angles glued the
  four walls are one box. The box still unclips from the floor, and the roof still comes off.
- **The roll-up door is its own piece.** It hangs on the white threshold's sloped back and leans
  back against two little slopes up the sides of the doorway, which stop it going in. A tongue along
  its top goes up behind the trim over the doorway. Hidden up there, two springy fingers press it
  down and two small tabs press it in, so it sits tight and doesn't rattle, even upside down. It
  never touches the floor. It comes out the front: lift it by its handle until it stops (about a
  millimetre), let it down a hair, pull the bottom toward you and let it drop, roof on or off. It
  doesn't stay part open: it's either in or out.
- **The roof.** Each half sits on three pegs: one on each gable's top chords, and one on the top
  plates in the middle of its long wall. The long walls are 203 mm long, and that middle peg lets
  the roof hold their middles straight too.
- **The steel door** swings in on two pins, as a real in-swing door does, to about 100 degrees.
  When shut it rests against a strip outside it on the latch side, so it can't swing out. It is
  hung in the door side before that wall goes on the floor. After that it can't come off: the
  floor closes the slot its bottom pin came in by.
- **The skids.** The two inner skids (37 in in from each side) are notched where the floor joists
  sit on them and have a peg at each end into the floor's end bands. The two outer skids (8 in in
  from each side) are flat on top, under the floor's edge, with a thin peg into the floor near
  each end. Those pegs stand a little nearer the skid's outside face than its inside one, so an
  outer skid goes on only one way round. All four stand the same height. The two outer skids are
  the same part, turned end for end; so are the two inner ones.
- **Which end is which.** The floor's roll-up end has five short notches across the middle of its
  edge: one in the very middle and two each side of it, the same on both sides. Near each corner
  it has a clip slot, the same distance in from each corner. The other end's notches aren't the
  same each side. Along the door side there is one long notch under the doorway, near the
  roll-up end (the doorway's near edge is 4 ft in from that corner). The plain side has a notch
  for every stud.

## Checking the fit

Before you start the big prints, print both plates of `1 fit test.3mf` and try them. Plate 1 is
new for the lift-out roll-up door: half its doorway and half the door, alone on the plate. Plate 2
has the roll-up corner, and the same little doorway as before (moving the steel door and window to
your standard layout didn't change it: it is a piece of its own with the real doorway's section,
pins, slot and stop).

1. **Roll-up corner (plate 2).** Set the bit of floor face up. Its two outside edges (where the
   walls go) are about the same length (22 and 21 mm), so go by the slots: the roll-up end's edge
   has its clip slot near the corner and ends in a narrow notch with a sliver of floor past it; the
   plain side's edge has its slot farther from the corner and ends in an open notch. The short
   wall with the roll-up's raised casing and the sloped threshold is the roll-up end: press it
   straight down on its edge until its prong clicks. That prong is under
   the side of the doorway, which is new. Then lower the other short wall (the plain side) straight
   down onto the other edge until its prong clicks. Pushed outward at the foot, neither should
   move, and neither should lift off. The two should meet on their mitre. Press the stub of corner
   angle into the corner, its foot on the table; its two legs are the same, so it goes in either
   way round. It should sit flat in both recesses with a hairline round it. Don't glue it. Then
   push the skid stub's thin peg up into the hole near the corner under the plain side's edge, the
   stub lying along that edge with the end nearer its peg at the corner; it should sit flat under
   the floor. Look at the casing's edge and the white threshold's slope: they should be clean. If a
   prong won't click, a wall lifts off, or the stub is tight or rocks, tell Claude which.
2. **Roll-up door (plate 1).** Plate 1 is half a roll-up doorway and half a roll-up door, both
   full height, cut from the real ones, and they work just like the real ones (the half door is a
   little over half the real door's weight, because its handle is full size, on half its springs).
   Stand the doorway on the table and put the door in (step 11 below), its bottom about 6 mm out.
   It takes a little knack, and you can tell which way you're off:
   - If it stops dead about 2 to 3 mm early, before it gets springy, it is caught on the trim.
     Don't push harder (that can snap the little tab at its top); let it down, lean its top in a
     bit more and push again.
   - If it goes in, but lifted a little by its handle and let go it stays up or only creeps down,
     its top went in leaned too far: its spring went up behind the little block it should press
     on, not under it, and you don't feel that going in. Look at the doorway from behind: the
     spring's bump sticks out toward you beside the block over the door's top, instead of hiding
     under it. Take it out and put it back leaning the top in less.
   - If it won't come all the way in under the trim, its top is leaned in much too far (its sides
     meet the tops of the little slopes up the sides of the doorway): lean it less.

   Do it until it goes in first time. Then:
   - lift it a little by its handle and let go: it should snap straight back down;
   - it should settle and pull itself in, with a hairline all round and no wobble;
   - turn the doorway face down, then upside down, and shake it gently: the door should stay put
     and not tick;
   - lift it by its handle with a fingernail until it stops: it should feel light, about the
     weight of an egg (the whole door, on both its springs, takes about twice that). Let it down a
     hair, pull the bottom toward you, let it drop, and it comes out;
   - in and out ten times: the little springs should spring back and nothing should crack;
   - with the door out, hang a full litre bottle from the handle on a string for a few seconds; it
     should hold;
   - look into the slot over the doorway from behind: its far wall, the face the door's top tabs
     press on (it prints as a bridge), should be clean, not sagging toward you. Look at the
     threshold's slope (clean), and at the handle: the grip and the gap behind it should come out
     square, not slumped. Plate 1 has nothing on it taller than the doorway but the half door, so
     above the walls its handle prints on its own, just as the real door's does on plate 3, and
     comes out the way the real one will.

   If it's too stiff, too loose, or the handle is soft, see "If the roll-up door isn't right" at
   the end of "Changing it".
3. **Door (plate 2).** The little doorway has a short slot running in from its inside face to the
   bottom pin hole. Hang the little door from the inside, the same way as the real one (step 1 of
   "Putting it together"). It should swing in freely past 90 degrees, and it should stop against
   the strip on the latch side so it can't swing out.
4. **Roof peg (plate 2).** Stand the peg block up so the peg points up, and set the bit of roof on
   it. It should drop on and lift off without forcing.

Pin holes are already 0.35 mm bigger all round than their pins and the roof peg holes 0.4 mm
bigger all round than their pegs; the snap parts and the skids' pegs have 0.2 mm round them (the
skid pegs are a snug push fit), each corner angle has 0.15 mm round its edges in the recesses, and
the roll-up door has 0.3 mm at each side. Each barb hooks 0.45 mm under its ledge.
If anything is too tight or too loose, ask Claude to change that gap by 0.1 mm (by 0.05 mm for the
corner angle, or the barbs' catch, if the prongs won't click or won't hold; a tight skid peg is the
gap round the skid pegs, not the snaps') and remake the files. The sizes are at the top of
`make_garage.py`.

## Cleaning up the parts

- Let the plate cool right down before you flex the parts off. Don't push a scraper under the
  ends of a wall (the mitred ends come to a thin edge) or under the prongs: each prong's leg is a
  thin strip lifted just off the plate, joined to the wall at the top and to its barb at the foot.
  Flex the plate to free the corner angles and the roll-up door; don't bend them.
- With a fresh hobby knife, take a light chamfer off the first-layer lip (the edge that was on the
  plate) on: the posts, stops and barbs under each wall, the inside edge of the mitre at both ends
  of every wall, the floor's face all round its edge, the roof pegs (on the gables and in the
  middle of each long wall, so they're round), the door's two pins, the skids' pegs, and the mouths
  of the peg holes under each roof half. A lip on a post, stop or barb makes it tight in its slot;
  a lip round the floor's face rubs on the skirts. Don't scrape the mitre faces, and don't trim
  the barbs' flat tops.
- Leave the four little springs in the top edge of the roll-up door alone. Don't trim them or glue
  anything near them.
- Look down each corner recess and pick out any string or blob with the knife tip, so the angles
  sit flat. Do the same along the roll-up door's slat grooves.
- The corner angles' outside face on the long wall was on the plate. A lip along its edges sits
  outside the wall, so it doesn't change the fit, but it shows: shave it off with the knife held
  flat.
- Snip any loose strands between the studs on the inside with flush cutters. Don't sand the
  outside; it would fill the siding grooves.
- Cut any strings in the window at the point where they join, holding the thin window bars from
  behind with a fingertip.
- Lay each wall on glass. If it rocks or a sheet of paper slides under the middle, set the bed to
  55 °C, lay the wall framing-side down on it under a sheet of paper and a flat board with about
  1 kg on top, leave it 10 minutes, then let it cool before lifting the weight. The long walls are
  203 mm long, so check them along their whole length.

## Putting it together

You'll need your fingers, two rubber bands that go round the garage (or painter's tape), glue for
the corners, and tweezers or a small flat screwdriver if you ever take it apart. For the glue,
gel super glue is fine in small dots; clear contact cement (E6000) or 5-minute epoxy can't leave a
white haze on black plastic the way super glue's fumes sometimes do. Not water-thin super glue: it
runs down the corner into the floor's notch and glues the walls to the floor, and then the model
no longer comes apart. `how it goes together.png` shows the order.

1. **Door, in the loose door side, and leave it there.** Lay the door side flat, inside up, or
   hold it so you are on the inside of the doorway. Hold the door with its knob facing away from
   you (outward) and its pins on the side away from the strip. The longer pin goes at the top.
   Push the top pin up into the hole in the head, **keep pushing the door up** (about half a
   millimetre), and swing the bottom out along the short slot in the sill until the bottom pin
   drops into its hole. Check it swings in freely now: once the wall is on the floor the door
   can't come off. A strip of painter's tape across the inside holds it shut while you handle the
   wall. If a pin is tight, twist a 2.7 mm drill bit by hand in its hole; never lever the door.
2. **Floor.** Lay the floor face up on a flat table, without the skids. The skids go on after the
   corner angles, so the angles' feet can be glued level with the bottom of the skirts.
3. **Roll-up end.** Hold it over the end of the floor whose edge has a short notch in the very
   middle and two more each side, the same on both sides, roll-up facing out, its siding outside
   the floor's edge. Its two prongs are under the sides of the doorway, one near each corner, the
   same distance in. Line up the posts with the notches and press straight down over each prong
   until it clicks. The roll-up door is not in yet.
4. **Back end.** Over the other end the same way. It has two prongs, one near each corner but not
   the same distance in.
5. **Plain side** (no door or window). Hold it over its side of the floor, siding grooves facing
   out (studs inside), and lower it straight down between the end walls, keeping it level. Press
   down over each of its three prongs until it clicks.
6. **Door side**, with its door hung, the same way: the doorway goes at the roll-up end, over the
   long notch in the floor's edge, the window toward the back. Straight down, pressing on the
   wall, not on the door. Take the tape off. The floor is level with the door's threshold.
7. **Band the corners.** Put a rubber band (or a loop of painter's tape) round the walls about
   15 mm above the table, and another about 10 mm under the top of the long walls, just tight
   enough that each corner closes on its mitre top to bottom. Not tighter: too tight bows the long
   walls in. Look down on each corner from above to check. The lower band crosses the empty
   roll-up doorway.
8. **Corner angles.** Each one goes on with its flat leg on the long wall and its standing leg,
   the one with the sloping top, on the end wall, sloped end up, foot on the table. They come in
   two hands, two of each; if one won't sit that way, it's the other hand: try it on the next
   corner. First try all four dry: ease the bands out from the corner with a finger (with tape,
   peel that corner's strips back), press the angle into its two recesses and let the bands back
   over it. The bands go over the angles, never under. It should sit flat in both recesses with a
   hairline gap along both edges. Then glue them one at a time: take the angle out and put 3 small
   dots of gel super glue (or E6000, or 5-minute epoxy), each about 1 mm across, down each recess
   floor, the lowest at least 10 mm above the table (the floor's top is about 7 mm up) and the
   highest at least 2 mm under the top of the long wall, so no glue reaches the floor or the roof.
   Each floor is a strip about 1.6 mm wide beside the corner's chamfer, and the angle covers the
   1.45 mm of it nearest the corner: put the dots in the half nearest the corner, so the squeeze-out
   stays under the angle. Press the angle back in, let the bands back over it and hold it 20
   seconds. Leave the bands on 15 minutes for super glue, an hour for epoxy, or overnight for
   contact cement; then take them off.
9. **Skids.** Lay the four skids on the table about where they go: the two notched ones in the
   middle, notches and pegs up, the two flat-topped ones near the long edges, pegs up and nearer
   the outside edge (turned the other way their pegs miss the holes). Lift the garage onto them:
   the inner skids' end pegs go into the holes in the floor's end bands and the joists drop into
   their notches; each outer skid's two pegs go into the holes near each end of the floor's long
   edges. All four are the same height. They are a snug push fit. If the inner (notched) skids fall
   out when you pick the garage up, a drop of glue on their pegs keeps them. Never glue the outer
   skids: they lie right under the long walls' barbs, and glued on, the walls could never be
   unclipped from the floor. If one drops out, put it back and stand the garage on it.
10. **Roof.** Set each half ribs up with its raised ridge strip at the peak, so its holes drop over
    the two pegs on the gables. Then nudge the top of that long wall in or out until its middle peg
    drops into the third hole. Always lift a roof half straight up, never slide it along its pegs.
11. **Roll-up door, last**, from outside, roof on or off (any time after the bands come off in
    step 8). Hold it by its handle, slats out, its bottom about 6 mm (1/4 in, a pencil's thickness)
    out from the wall and its top leaning in a little more, so the top goes up just inside the
    wall. Push it straight up under the trim over the doorway until it stops: it gets springy just
    before it stops. Let it down about a millimetre, then push the bottom in over the white
    threshold: the top comes out as it goes. Let go. It settles on the threshold's slope and pulls
    itself in against the sides. **Then check it:** lift it a little by its handle and let go. It
    must snap straight back down. If the lean was off, you can tell which way:
    - **It stops dead about 2 to 3 mm early, before it gets springy:** it is caught on the trim.
      Don't push harder; that can snap the two little tabs at its top. Let it down, lean the top in
      a little more, and push up again.
    - **Lifted a little and let go, it stays up or only creeps down** (and it lifted with no
      spring): its top was leaned in too far, and its two hidden springs went up behind the little
      blocks they press on instead of under them. You don't feel that going in, and nothing is
      harmed. Take it out (see "Taking it apart") and put it back with the top leaned in a little
      less.
    - **It won't come all the way in under the trim:** its top is leaned in much too far, and its
      sides meet the tops of the two little slopes up the sides of the doorway. Lean the top in
      less.

## Taking it apart

**Roll-up door first:** a fingernail under its handle, lift until it stops (about a millimetre),
let it down a hair, pull the bottom toward you, let it drop, and take it out. Don't force it past
where it stops. It comes out with the roof on or off. (If you leave it in, it rides with the
glued box, because it hangs on the end wall, not on the floor.)

Then lift the roof halves straight off. Lift the garage off its skids: the outer two must come off,
because they cover the long walls' barbs (glued inner skids can stay on). The four walls are glued
into one box, but the box still unclips from the floor: look underneath, and just inside each wall
you can see the barbs in their slots. Push each barb toward the siding with a small flat
screwdriver, only just far enough to clear its ledge (about half a millimetre; don't lever it hard
against the far side of the slot), and ease that side of the box up a little. Work round the box;
when all ten barbs are free, lift it straight up off the floor. The roll-up end's two barbs are
under the sides of its doorway. The steel door comes off only with the door side off the floor:
lift the door, swing its bottom in, and drop it out.

## Where the model differs from the real building

- **Held at the base models' sizes**, so the proven snaps, corners and layers fit (Nov 2026). The
  siding is 1.4 mm thick (2 in at full size). The studs are 3.7 mm deep, so the walls read 7.2 in
  thick at the openings instead of 4 in. The bottom plate is 1.6 mm (2 1/4 in). The floor is 6.8 mm
  deep, 9.7 in where the real one is about 6 in, and the siding hangs down over its whole edge as a
  skirt to hide the snaps. The door is 2.8 in thick. Every stud, joist, plate, header and trim board
  is its true width, and all the openings and overall sizes are true.
- **Framing runs the full depth of the wall**, so each wall prints lying flat on it. The corners
  are mitres with a glued black angle as the corner boards; the designer draws 3-stud corners with
  the end walls running through. There are no trusses or roof deck between the gable ends, so you
  can see in with the roof off.
- **The roll-up door lifts out.** It doesn't roll up or stay part open. Seen from inside, it is a
  thick white block (6.9 in), with two little slopes up the sides of the doorway at its back
  corners and a slot along the inside of the drum box over the doorway, where its top goes.
- **The dark gap under the trim over the doorway is 3.1 in** (the drawing's is 2.2 in), so the
  door has room to rise and tip under the trim. In places you can see through it into the garage,
  where the door's hidden springs need room.
- **The white threshold strip is 0.94 in** (the diamond plate is 0.66 in): the door's bottom hangs
  on its sloped back.
- **There are 0.43 in gaps at the sides** of the roll-up door; they read as the dark guide strips.
- **Where the roll-up door sits depends a little on how your printer prints:** its springs push it
  to its stops, and in a print whose holes come out small it sits about 0.2 mm further out and
  0.3 mm higher than drawn (up to 0.4 mm higher if they come out smaller still). Its slats are then
  about flush with the siding (drawn, they are 0.4 in behind it), a thin dark line up to about
  3/4 in high shows over the white threshold, and the dark gap under the trim is about 2.7 in
  instead of 3.1.
- **The roll-up door's handle is 16 x 2.8 in, standing 4.5 in out,** about 2 3/4 times a real one,
  so a fingernail can lift it. The designer draws no handle.
- **Over the roll-up a solid block fills from the doorway's top to the top plates** (13.7 in): the
  door's drum box. It holds up the siding over the opening, and the door's top goes up into a slot
  in its inside face.
- **Under the roll-up door** the posts that drop into the floor are in the middle and 16 in and
  35 in each side of it, and the end wall's two prongs are under the sides of the doorway. On the
  back end the stud 29 in right of the middle (seen from outside) has its post 2.5 mm to one side,
  clear of an inner skid's peg hole. These posts are under the floor top and don't show.
- **The vents have 4 louvres** instead of the designer's 5: with 5 at this scale the slats would
  print thinner than a line.
- **The corner angles** cover 4 1/4 in of each wall, not the 3 1/2 in of a corner board, so each
  sits on enough glue.
- **The skids** are as long as the building; the designer draws them 0.1 ft past each end.
- **The door and window are where your standard puts them** (your `designer-standards.js` on
  yoder-storage-barns.com), not where the designer's stock layout and the first plan had them.
  The steel door's hinge-side edge lands right on a 16 in layout mark (96 in from the middle), so
  that stud would sit 3/4 in on the door's king stud: it is left out and the king stud stands
  there. Nothing else had to move: the door side's three prongs, its posts, the corner recesses
  and the roof peg in the middle of the wall are all clear of both openings. One siding groove,
  1/2 in past the steel door's latch-side casing, is filled beside the casing: the model's grooves
  are about 3/4 in (18 mm) wide at full size, and it would have left a strip of siding there too
  thin to print.
- **The sizes are the site builder's, not the building page's.** The Garage's page lists a 7 x 9 ft
  roll-up and a 36 x 80 in walk door; the site's own 3D builder, with your standards file applied,
  still draws the 8 x 6.4 ft roll-up and the 3 x 6.3 ft (36 x 75.6 in) door, and the model keeps
  those, as you chose on Nov 3 2026 ("Keep builder sizes", question 12 below).

**Numbers that are the designer's or ours, not yours yet, and the open questions.** The model
uses the default in the last column until you say otherwise.

| What | Number used | Where it's from | Open question, default used |
|---|---|---|---|
| Width | 134 in (11 ft 2 in) | yours (Sep 30 2026, confirmed Nov 4 2026); the designer still draws 12 ft | 1. Model the 12-wide at 134 in or 12 ft? **Answered Nov 4 2026: 134 in** |
| Roll-up framing and size | your king studs to the top plate, no header; 8 x 6.4 ft door; drum box 13.7 in over it | arrangement yours; door size yours (the builder's 8 x 6.4 ft, kept by your answer to question 12); drum box ours | 2. Your arrangement (king studs to the top plate, no header), or the designer's doubled 2x10 header (9 1/4 in)? **Your arrangement** |
| Roll-up door | lifts out the front by a handle at its bottom middle, with the roof on | **yours (Nov 3 2026): "Do 4 the lift out add a handle in the bottom middle to lift it up"; you picked the front lift-out the same day** | 3. Shut or rolled up? **Answered: it lifts out** |
| Roll-up door: no part opening | lift it until it stops, let it down a hair, and it comes out the front; it doesn't stay part open | ours | 14. Is lift-out only OK? **Yes** |
| Roll-up door's handle | black, 16 in long, 2.8 in tall, standing 4.5 in out, at the bottom middle | its place yours; its size ours | 15. Right size, or smaller (12 in) or bigger? **16 in** |
| Threshold | a white strip 0.94 in high under the door (the diamond plate is 0.66 in); the door's bottom hangs on its sloped back | ours (the designer's diamond plate is 0.055 ft) | 16. 0.94 in OK? **Yes** |
| Dark gap over the roll-up door | 3.1 in (the drawing's shade band is 2.2 in), see-through in places where the hidden springs are | ours (the designer's shade band is 0.18 ft) | 17. OK? **Yes** |
| Roll-up end's clips | two, under the sides of the doorway, 51 in each side of the middle | ours | 18. OK there? **Yes** |
| Where the roll-up door prints | on the end walls' plate, still one colour change | ours | 19. With the end walls, or on its own plate? **With the end walls** |
| Putting the roll-up door back | takes a little knack: its top leans in about half a millimetre as you push it up (the fit test teaches it; too little and it stops early, too much and it goes in without its springs holding it down, which the let-go check in step 11 shows); the two tabs that need this stop it ticking when the model is face down (without them it goes in with no knack, but its top can move about 0.6 mm) | ours | 20. Keep the tabs? **Keep them** |
| Black filament's Min print speed | 20 mm/s (Cooling), as saved in the file for all three filaments. Above the walls on plate 3 only the roll-up door's black handle prints, about 1 to 3 seconds a layer; Flash Studio slows a layer down to give it 8 seconds, but not below this speed | Flash Studio's, in the settings the file carries | 21. Keep 20, or set filament 2 (black) to 5 mm/s before you slice plate 3, so the grip has time to cool? **Keep 20** (change it if the fit test's grip comes out soft: see the last row of "If the roll-up door isn't right") |
| Roll-up door's other numbers | side gaps 0.43 in; the slot over the doorway 2.3 in deep (in the drum box); the door's top 2.6 in up into it | ours | none |
| Steel door header | your usual 5 in loft header | yours (your usual header); the designer's rule gives doubled 2x6, 5 1/2 in | 4. Your 5 in header or the designer's 2x6? **Your 5 in header** |
| Steel door | opens, in-swing, hung before the wall goes on | the door's swing the designer's; the pins ours | 5. Opening or printed shut? **Opens** |
| Window top | 76 1/2 in, under your utility window plate (12 1/2 in under the top plates) | the designer's rule, and your window plate | 6. (a) 76 1/2 in, (b) level with the door at 75.6 in, or (c) sill at 2.9 ft (top 69.6 in)? **(a)** |
| Gable band | top level with the plates, as on the shed models | ours (from the shed models) | 7. There, or 3 1/4 in higher as the designer draws it? **As on the shed models** |
| Roof on the long walls | a peg in the middle of each long wall | ours | 8. Pegs or truss ties? **Pegs, no ties** |
| Corner angles | 4 1/4 in on each face | ours (for glue land) | 9. Wider than the 3 1/2 in board? **Yes** |
| Skids | four 4x6, centres 8 and 37 in in from each side | the designer's skid sheet | 10. Four skids there? **Yes** |
| Studs that land on other framing | dropped: door side 96 in from the middle toward the roll-up end (on the steel door's hinge-side king stud, 0.75 in overlap: the door's edge is on that mark); roll-up end 51 in toward the plain side (on the roll-up's full stud, 0.75 in); 61 in at both ends (into the corner) | ours | 11. Drop them or move them? **Drop** |
| Steel door, window, roll-up positions | steel door on the door side at the roll-up end, near edge 4 ft in from the corner (centre 6.5 ft from the middle); window centred between it and the back end (3.5 ft from the middle); roll-up centred | yours: your standard layout, `designer-standards.js` on yoder-storage-barns.com (your copy-this-build codes, Aug 2026; read Nov 3 2026). The first plan's +7.6 / -7.6 ft was the designer's stock layout | none |
| Sizes on the building page | the builder's sizes: roll-up 8 x 6.4 ft (96 x 76.8 in), steel door 36 x 75.6 in opening (3 x 6.3 ft) | the site's 3D builder, which still draws these with your standards file applied; the building page's text says a 7 x 9 ft roll-up and a 36 x 80 in walk door | 12. Keep the builder's sizes, or go by the page's 7 x 9 ft roll-up and 36 x 80 in door? **Answered Nov 3 2026: "Keep builder sizes"** |
| Steel door's hinge side | hinged on the left seen from outside (the roll-up corner's side), knob on the right; it swings in toward the roll-up end | the designer's (door-steel.js); your standard says where the door goes, not which way it swings | 13. Keep it hinged on the corner side? **Yes** |
| Steel door and window sizes | steel door 36 x 75.6 in opening; window 25.2 x 34.8 in clear opening | the designer's standard items (d36in, w23); the door's size kept by your answer to question 12 | none |
| Steel door look | six panels, knob 0.32 ft from the latch edge at 0.44 of the height | the designer's | none |
| Roll-up look | 2 1/4 in slats, bottom rail, latch plate 0.72 x 0.38 ft | the designer's | none |
| Studs and plates | 2x4 studs 16 in apart from each wall's left end; one bottom and two top plates | the designer's (the 89 in stud and the 93 1/2 in wall are yours) | none |
| Gable framing | bottom chord on the plates, gable studs on the end wall's own marks, kings and a flat sill at the vent | the designer's; your 2x6 chords | none |
| Rake | 5.4 in past each gable | the designer's | none |
| Gable vent | 1.12 x 0.76 ft, 0.92 ft under the ridge, 4 louvres | the designer's size; 4 louvres ours | none |
| Floor | 2x6 joists 16 in apart from the back end; 4x8 sheets in rows of 48, 48 and 38 in from the plain side | the designer's; the rows worked out, where they start ours | none |
| Window casing | the same 1x4 on all four sides | yours on the shed models (Oct 31 2026), carried over | none |

**Where the roll-up door is built a little differently from its plan** (`spec_rollup.md`, Nov 3
2026), and why. The checks measure the real parts at about 250 places along the doorway, and as
printed at every place near its sides where a layer's outline changes, where the plan's own proofs
used 77; that, and two reviews, turned up a few things:

- **The two slopes up the sides of the doorway stand back 0.45 mm on their first layer.** As
  printed, their first layer and the door's (0.25 mm thick, where every other layer is 0.2) can
  overlap in a strip just inside the door's back edges, between the plan's places. That holds the
  printed door out a whole layer and takes a quarter of a millimetre off its lift. Stood back
  0.45 mm they clear it at every print accuracy tried, with 0.125 mm to spare even with the door
  pushed sideways as far as the slopes let it, and the door sits where the plan says (as printed
  0.20 out and 0.30 up, stopping at 1.15 mm and coming out from 0.55). Nothing changes as drawn.
- **The two little blocks the springs press up against are 0.7 mm wide, not 1.4.** A bent spring
  finger slopes (about 12 degrees at the top of the lift), so a flat block presses on its bump
  only along the block's edge nearer the finger's root. The plan's 1.4 mm block put that edge
  0.7 mm nearer the root than the plan's own spring numbers assumed: as printed the finger would
  have bent to about 1.86 % strain instead of 1.71 % at the top of the lift, and going back in its
  tip would have reached the bottom of its slot. Ending the block at the middle of the bump puts
  the press where the plan worked its numbers out: 1.71 % (1.73 % as printed), the tip 0.24 mm
  clear as printed, and the springs as strong as planned.
- **Under the latch plate the slat grooves stop square,** at the latch's rectangle, as they did on
  the printed-shut door, and the plate's white boss sits on that fill. Stopped at the plate's cut
  corners, two grooves would end in tapers thinner than a line, or run on under the boss with its
  corners over air.
- **The white threshold's sloped back is exactly 45 degrees right down to its foot** under the
  floor top. The plan's foot point tilted it about 1 degree, so it stepped 0.203 mm a layer
  instead of 0.2.
- **The fit test's short walls and half doorway are cut inside a siding groove.** The short
  roll-up end stops over its post 35 in from the middle, 1.5 mm short of the bit of floor, which is
  cut where the plan says (cut there too, its skirt would hang past the post with nothing under
  it); the short plain side stops inside the groove over its stud 112 in from the middle; the half
  doorway starts in the groove over its end stud. Cut beside a groove, each kept a strip of siding
  about 0.3 mm wide on its top layer, thinner than a line.
- **Fit-test plate 1 is the half doorway and half door alone.** With the corner's bit of floor and
  skid stub on the same plate, they were still printing while the half door's handle was, which
  gave the handle's layers about 7 seconds each, where on plate 3 the real handle prints on its own
  at 1.3 seconds a layer. Now nothing but the handle prints over the walls on plate 1 either, so
  the fit test shows how the real one comes out. The whole corner is on plate 2.
- **Going back in, a spring finger bends up to 2.23 mm** where the plan says 2.15 at most: the door
  reaches its stop tipped, and the finger's bump meets its block with its front corner first. At
  2.23 mm the finger is still under 2 % strain (1.79 % as printed) and its tip stays 0.15 mm clear
  of the bottom of its slot as printed.
- **Leaned in too far going back in, it still goes in, but wrong.** The plan says its top won't
  come out; it does come out, pushing the two springs back behind their blocks (up to about
  1.5 mm), where they don't press the door down, and you don't feel it. That bend is under 1 %
  strain, so nothing is hurt, and the door comes out the usual way; the let-go check in step 11
  shows it. Leaned in further still, it won't come all the way in: its sides meet the tops of the
  two slopes.
- **Printed numbers:** the door stops 1.15 mm up as printed (the plan says 1.10) and has a 0.60 mm
  window to come out (0.55). At the other print accuracies the plan tried, it stops 0.95 mm up or
  more and the window is 0.40 mm or more (the plan's least is 0.30), and its bottom has no play
  (the plan allowed up to 0.14 mm).

## Changing it

Everything is made by `make_garage.py` from the numbers at the top of the file (building size,
wall height, the openings, the roll-up door, clearances, the snap joints, the corner angles). It
writes the `.stl` files and both `.3mf` files. `draw_garage.py` draws `how it goes together.png`.
`check_garage.py` then proves the parts still fit, one line per proof with the numbers it measured
(it takes about four to seven minutes and needs the `shapely` package as well):

- the `.stl` and `.3mf` files in the folder are exactly what `make_garage.py` makes now (it is run
  again in a scratch folder and every file compared), with no others, so none is left over from an
  older version;
- every piece is one solid and fits the bed; the `.stl` files are closed, with no collapsed
  triangles, each holds the same solid as its part in the `.3mf` files, layer by layer, and each
  fits the bed as it opens; the walls and floor make up the whole body without overlapping; the
  roll-up door seated in its doorway touches nothing but where its springs press;
- each wall goes on straight down (the end walls first, then the long walls between them, the
  door side with its door hung) with nothing in the way but its barbs, stands on the floor, and
  can't lift or slide once clicked in; each of the ten prong legs is free up to where it bends,
  the roll-up end's two under the sides of its doorway; the floor keeps at least 1.09 mm between
  any two of its cuts;
- each wall prints flat with nothing hanging over that isn't a short bridge, all its black in the
  top three layers and nothing white above the siding's top layer, so each wall plate changes
  colour once; every size that matters sits on a layer line;
- each corner angle sits on both recess floors touching nothing else, also once it and the walls
  are cut into their print layers, clear of the roof and the gable band;
- each vent has 4 louvres and every gap and louvre is at least a line wide on every layer;
- the roll-up door: it prints in one piece, white to the siding's top layer and black from there,
  nothing thinner than a line, nothing over air but one short bridge under the handle's grip; it
  settles where its springs push it and is held there, upside down, face down and sideways;
  lifted, it stops rigidly before its springs are overbent (measured where its blocks really press
  on them); it comes out the front at every lift you can give it under that stop, by the way
  above and by three other ways a hand might move it; it goes back in by step 11, leaned within a
  band about half a millimetre wide, and either side of that band it does what step 11 says
  (stops dead 2 to 3 mm short; goes in with its springs behind their blocks, which bends them
  only mildly, still lets it out, and shows in the let-go check, which it then fails by a wide
  margin; or, leaned in much too far, won't come all the way in); pushed hard while it is stopped
  dead, its two tabs would take about 3 1/2 times its hardest lift before breaking; its handle
  leaves room for a fingernail behind the grip. All of this is proved on the real parts
  cut into sections every few tenths of a millimetre along the doorway (as printed, at every place
  near its sides where a layer's outline changes), both as drawn and as printed (cut into layers,
  the holes 0.1 mm small and the door 0.05 mm big), and at four more print accuracies, and its
  printed seats again in 3D; and it never gets near the roof, the steel door or a hand at its
  handle;
- the steel door swings in to about 100 degrees and can't swing out, hangs by the way above in the
  loose door side, and is captive once that wall is on the floor; its six panels are where the
  designer draws them, at fractions of the opening, so it is the Lofted Barn Garage's door;
- each roof half rests on the gables and is held by its three pegs, and all six pegs lie on the
  bed in their walls' prints; the skids fit, each peg with 0.2 mm round it in its hole, all four
  bottoms level;
- every plate's parts are inside the bed, apart, clear of the prime tower, with the skids' brims
  and the no-brim settings in the file; each two-colour plate changes colour once; every wall and
  every fit-test piece cut from one carry the bridge modifier, over their whole siding and nothing
  under it, and laid across the studs as it sets them no bridge is over 15.4 mm; the floor carries
  its modifiers on the layer over its seams, the only layer of it over anything, and every bridge
  there crosses a seam; every modifier is a plain box with just the direction it should set, and
  every piece lies on its plate unturned; nothing else has an overhang more than 5.2 mm across, in
  any direction, as high as the siding, or anywhere a slot like a floor seam, so it can't sag
  whichever way Flash Studio lays it;
- the fit test's half doorway and half door are cut from the real ones and move exactly as the
  real door does in its real doorway, and the half door holds at its own weight; the corner's
  pieces are the real ones below their join, and the short walls are cut where no strip thinner
  than a line is left; and plate 1 holds only the half doorway and half door, so nothing but the
  half door's handle prints above the walls, as on the real plate;
- measured off the parts: 134 x 288 in, 93 1/2 in walls, 5/12, 4 in eaves, the roll-up 96 x 76.8 in
  with its king studs to the plates, the roll-up door 95.15 in wide with 2 1/4 in slats, a 16 in
  handle at its bottom middle, a 0.94 in threshold and a 3.1 in dark gap, the steel door 36 x 75.6
  in, the window 25.2 x 34.8 in with its top at 76 1/2 in, your 5 in header, the window plate 12 1/2
  in under the top plates, studs on the 16 in marks (36 full studs, counted against your layout,
  and the 4 cripples and window studs), trim 3 1/2 in, the gable bands' tops level with the plates;
- the door side's framing, measured through the middle of its studs from one end wall to the
  other and from the floor to the plates' top, against your rules for the openings where the
  casings put them: a full stud and a king stud each side of each opening, the 5 in header and the
  window plate bearing on the kings, the rough sill under the window, the cripples over the header
  (80 and 64 in toward the roll-up end) and the studs over the window plate and under the sill (32
  and 48 in toward the back) on their 16 in marks, and only the 96 in mark dropped (on the door's
  king stud);
- the layout, by your standard, found off the casings: the steel door's near edge 4 ft in from the
  roll-up corner (centre 6.5 ft from the middle), the window halfway between the door and the back
  (3.5 ft from the middle); nothing in the doorway but the stop and nothing in the window but its
  sashes; under the doorway only the sill post's notch in the floor; no prong under either opening,
  and the middle roof peg and the corner recesses clear of both casings.

**If the roll-up door isn't right** after the fit test, tell Claude what you saw. The fixes below
are numbers in `make_garage.py` (with the roll-up door's other numbers), one row at a time. Each
was tried in Nov 2026: the files remade with it and `check_garage.py` run on them. Whatever is
changed, the files must be remade and the checker must pass again before anything is reprinted.

| What you see | Change | What the checker said |
|---|---|---|
| Lifted a little and let go, it stays up or only creeps down | Nothing to change: it went in with its top leaned in too far, its springs behind the little blocks they press on. Take it out and put it back leaning the top in less (step 11) | no harm: pushed back there the springs bend under 1 % strain, and it comes out the usual way |
| It slides when the model is upside down | `PRELOAD` 0.6 **and** `FING_SLOT` 2.84: the springs pressed down 0.05 more (the most there is: 0.6 is the bumps' height), and the slot under each spring 0.1 deeper, which cuts 0.1 into the door's top, so the springs' tips keep their room | passes: it then holds 1.8 to 2.6 times its weight upside down; each spring's tip keeps 0.28 mm of its slot at the stop as printed (at least 0.2) and 0.2 mm going back in (at least 0.1). `PRELOAD` 0.6 on its own fails: the tips keep only 0.18 and about 0.1 |
| It ticks when the model is face down | `TAB_T` 0.85: the two top tabs one layer thicker, about twice as stiff | passes: it then holds 3.8 to 5.4 times what it needs face down, and goes back in with the same lean. (`TAB_BUMP_U` 0.2 more would press harder too, but fails: the lean that puts it back in shrinks under 0.3 mm) |
| Too stiff to lift, or it won't seat | First look for a string or blob at its sides or on the threshold's slope. Lighter springs would be `PRELOAD` 0.45 (0.1 less) | fails: it then holds only 1.3 to 1.8 times its weight upside down, under the checker's 1.5 rule. Only worth doing if your fit test shows the springs stiffer than the checker assumes |
| It hits its stop before its bottom clears the threshold | `LIP_H` 0.466: the white threshold 0.2 lower (0.66 in, the designer's diamond plate), so the bottom needs 0.2 less lift | passes: it then comes out from 0.6 mm (0.35 as printed), leaving 1.1 mm under the stop (0.83 as printed). The checker's threshold size (`THRESHOLD_IN`, open question 16) goes to 0.66 in with it |
| Seen from behind, the far wall of the slot over the doorway sags toward you, onto the door's top | `REB_U` 1.85 **and** `TAB_BUMP_U` 2.05: the slot 0.2 deeper and the tabs' bumps 0.2 taller (one layer each), so the tabs keep their push | passes: the same stop, window, holds and lean as now |
| The handle cracks | `HDL_LEG` 3.3: its legs 0.3 wider, inward | passes: it then takes about 24 N instead of 22; the gap between the legs for a fingernail is 4.7 mm instead of 5.3 (at least 4.5, so no wider than 3.3) |
| The handle's grip comes out soft or rounded | Not a number in the file: in Flash Studio, filament 2 (black) → Cooling → **Min print speed** 5 mm/s (it is 20) before you slice plate 3. Above the walls only the handle prints, about 1 to 3 seconds a layer; slower, it has time to cool. It changes nothing on the set's other layers. The fit test prints on filament 1, so to see it there, set filament 1's too | (a setting, not the model) |

To make a different size, ask Claude to change the numbers and run all three.
