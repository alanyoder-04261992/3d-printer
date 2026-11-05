# 10x20 Cabin model — read me first

A 1:32 model of the shop-standard 10x20 Cabin (one inch on the model = 2 2/3 feet on the real
building). You asked for it on Nov 3 2026 ("create a cabin and loft cabin and garage and loft
garage"), then "Move to higher scale so it fits" and "Do the cabin and loft cabin 10x20". At 1:32
every piece prints whole on the 220 mm bed; nothing is split.

It is built the same way as the
[8x12 Side Utility model](../shed%20model%208x12%20side%20utility/read%20me%20first.md): the
walls print flat with their trim on top in black, snap onto the floor with no glue, and a black
corner angle is glued over each back corner. What's new is the front porch: three brown posts on
the deck, a black frame round the top, a white ceiling, a porch gable over it, railings down both
sides and one across the left of the front. The 11-lite door hangs on two small pins on its right
side, next to the right side wall, and swings **in** toward that wall (your answer, Nov 4 2026), and
both roof halves lift off so you can see the framing inside.

Where the door, the windows, the porch posts and the front railing go is **your standard
layout**, from your website, as you asked on Nov 3 2026 ("go on yoder-storage-barns.com to see
standard layout"): the site's 3D builder opens each building with your own standard doors and
windows (its `designer-standards.js`, laid out by you in the designer, your copy-this-build codes,
Aug 2026), and the site's style pictures and gallery agree with it. The sizes of the parts come
from the 3D designer's Cabin (style C), except the ones you gave. On Nov 4 2026 you answered
"Cabin 93.5 , roof pitch 5/12" (questions 1 and 2). So the walls are your 93 1/2 in utility wall,
and the roof is your 5/12 with a 4 in eave measured level, as on your sheds and garages. You chose
to keep the door as the builder draws it, 36 x 75.6 in (Nov 3 2026, question 15). Every other
size is the designer's (Barnwright's) until you give yours. They are listed at the end, with the
questions only you can answer.

| | |
|---|---|
| Building | 10 ft x 20 ft, with a 4 ft front porch inside the 20 ft (a 10 x 16 ft room) |
| Footprint | 95 x 191 mm (3 3/4 x 7 1/2 in), 102 x 199 mm with the roof on |
| Height on its skids | about 109 mm |
| Walls | 93 1/2 in from the floor to the top of the top plates: 89 in studs, one bottom plate and two top plates (your answer, Nov 4 2026) |
| Roof | gable, 5/12, rising 25 in over the plates, with a 4 in eave measured level (your answer, Nov 4 2026); 0.45 ft of rake |
| Door | 36 in 11-lite door, 36 x 75.6 in opening, on the front wall right of its middle (your standard); hinged on the right as seen from the porch, next to the right side wall, and swings in (your answer, Nov 4 2026) |
| Windows | three 2x3 windows: one on the front wall left of the door, and one in the middle of each side wall (your standard). Open, no glass, so you can look in |
| Porch | three 4x4 posts, one at each front corner and one just left of the middle; railings down both sides and one across the front from the left corner post to the middle post, under the window. The bay right of the middle post, in front of the door, is the way in, 56 in clear |
| Inside you can see | studs 16 in apart, your king studs and the full studs beside them, the door's 5 in loft header, the window headers, rough sills and cripples, the double top plate, the end-truss chords and studs on both gables, the framing round each vent, the floor sheet seams |

### Your standard layout, as built

Positions are the designer's: feet from the middle of the wall, + to the right as you stand in
front of the porch looking at the door. "Model" is millimetres on the model from the middle.

| | Your standard | Model |
|---|---|---|
| 11-lite door, front wall | 1.74 ft right of the middle | centre 16.57 mm right (opening 2.29 to 30.86) |
| Window, front wall (one) | 2.57 ft left of the middle | centre 24.48 mm left (opening 34.48 to 14.48 left) |
| Window, right side wall | in the middle of the wall | centre 19.05 mm behind the building's middle (the middle of the 16 ft room) |
| Window, left side wall | in the middle of the wall | the same, the right side's mirror image |
| Porch posts | one at each front corner, one 0.3 ft left of the middle | corner posts 44.96 mm each side, middle post 2.86 mm left |
| Front railing | one, from the left corner post to the middle post, under the window | x 43.13 to 4.68 mm left, 0.2 mm off each post |
| Way in | the bay from the middle post to the right corner post, in front of the door | 44.6 mm (56 in) clear, nothing in it but deck |

The side walls used to be called "window side" and "plain side"; both have a window now, so the
files call them **right side** and **left side**, as seen from in front of the porch.
`how it goes together.png` has the cabin straight from the front at the top right.

## What to print, in this order

| File | What's on it | Filament | Time and filament (Flash Studio) |
|---|---|---|---|
| `1 fit test.3mf` | Two plates. **Plate 1, porch joints:** a corner of the deck, a short post, a corner of the porch frame, the foot of the porch gable and the end of a side railing, each cut from the real part. **Plate 2:** the front left corner made short (a bit of floor, a short piece of the front wall and of the left side wall), a short doorway and door that swings in, hinged on the right like the real one, a roof peg and a bit of roof. | Any, one colour | plate 1 7 min, 1.2 g; plate 2 25 min, 8.8 g. **Print this first.** See "Checking the fit" below. |
| `2 all plates.3mf` | Everything else, one plate per print: | | |
| plate 1 | Both side walls and the door | 1 white, 2 black | 2 h 18 min, 58.5 g white and 0.5 g black, 1 colour change |
| plate 2 | Both roof halves, the porch frame and the two corner angles | 2 black only | 1 h 22 min, 56.5 g |
| plate 3 | The back wall, the front wall, the porch gable and the porch ceiling | 1 white, 2 black | 1 h 48 min, 44.4 g white and 0.8 g black, 1 colour change |
| plate 4 | The floor, both skids, the three porch posts and the three railings | 3 brown only | 2 h 3 min, 53.4 g |

The times and grams are Flash Studio's own, sliced from these files on Nov 4 2026 (with every
bridge modifier below in; the same in every slice): about 7 1/2 hours for `2 all plates.3mf`, with
about 103 g of white, 58 g of black and 53 g of brown.

Start Flash Studio first, then open them with **File → Open Project** (Ctrl+O), or **Open
Project** on its Home page. Starting Flash Studio by opening the file itself can leave it stuck
on "Loading". If Flash Studio says the file is from a newer version, click OK; it loads fine. If
it asks about unsaved changes to your settings, click **Discard** (the file brings its own). The
files carry their settings: the Flashforge AD5X 0.4, `0.20mm Standard @FF AD5X`, and three
filaments, 1 white, 2 black and 3 brown. Pick a plate, then Slice plate and Print plate as usual.

**Check the slots in the Send dialog every time.** Flash Studio matches each filament to the
slot whose colour on the printer is closest, and the printer still shows the old colours, so it
can put white on slot 2. Click each filament's slot box and pick the slot by number: filament 1
white on slot 1, filament 2 black on slot 2, filament 3 brown on slot 3.

Each wall prints lying flat, inside face down, so its trim (the door and window casings, the
gable band across the back) is on top and already set to **filament 2**. Nothing white stands
any higher than the siding's top layer, so plates 1 and 3 change colour once, for the last three
layers. Both side walls have a window casing now; the door, the porch gable and the ceiling are
all white. The gable
vents are set into the siding (Alan, Nov 3 2026), so they don't reach the black layers. On the
two-colour plates the prime tower goes in the back right corner, and those plates are laid out
to keep it clear; plates 2 and 4 are one colour and need no tower.

The `.stl` files are the same pieces one at a time, all one colour, if you'd rather set up a
plate yourself (`roof half.stl` prints twice, `porch post.stl` three times, `side railing.stl`
twice, `front railing.stl` once; `right side.stl` and `left side.stl` are the two side walls;
`floor.stl` is already upside down; `corner angle.stl` has both
angles; `skids.stl` has both skids, 12 mm apart, so add a 5 mm brim yourself; `fit test.stl` has
every fit-test piece from both plates laid out on one bed). A plate set up from `.stl` files gets
none of the settings the `.3mf` files carry: set **Wall generator → Arachne** yourself, and set the
posts, railings, corner angles, roof halves and porch frame to no brim. For two colours, and for
the walls' and floor's bridge settings, use the `.3mf` files.

**Settings:** already in the file: `0.20mm Standard @FF AD5X` with **Wall generator →
Arachne** (it shows in orange as changed), because the siding is only 1.4 mm thick and Arachne
fills thin walls solid. **Elephant foot compensation** is 0.1 mm, the AD5X's own setting; keep
it: the barbs, stops and posts under the walls print on the bed and fit with 0.2 mm to spare, so
a flared first layer would make them tight.

**Brims:** the two skids get a **5 mm brim** each (set in the file), because they're long and
thin. The posts, railings, porch frame, roof halves and corner angles are set to **no brim**: a
brim's lip would show along an edge you see. Nothing needs supports.

**Bridge modifiers, leave them in:** the four walls, and the fit test's short walls and doorway,
each carry a modifier, "bridges across the studs". It sets **External bridge infill direction** to
180, which lays the siding's first layer straight across the studs (13 mm at most). Left to itself
Flash Studio sometimes laid it along the stud bays in 66 mm strands, which sag. The porch gable
needs none: its bays are short every way (15 mm at most). The floor carries seven, "bridges across
the seams", on its second layer only. It prints face down, and left to itself Flash Studio laid the
bridge over each floor sheet seam that runs across the plate along the seam, in strands up to 39 mm;
now every seam and deck-board groove is bridged straight across, except the last 2 mm of a seam
where it runs into another, and no strand over a seam hangs free for more than 2.1 mm. Don't turn
the walls or the floor on the plate: the modifiers lay the bridges along the bed, not along the
part, so a wall turned a quarter turn would get the 66 mm strands every time.

## How it holds together

- **The walls stand on the floor.** The floor reaches out under each wall, and the side walls'
  and back wall's siding carries on down past the floor as a skirt, hiding its edge.
- **The front wall stands on the porch deck,** 4 ft back from the front edge, with no skirt. Its
  posts and the door's sill go down into pockets in the deck that are closed all round: 0.3 mm
  to spare along the wall, 0.2 mm across. Its two end columns go down through notches at the
  corners of the floor.
- **Posts and prongs.** Under every stud a short post drops into a notch in the floor. Ten prongs
  go down slots in the floor: two under the back wall, two under the front wall, three under each
  side wall. Each prong is a springy leg with a barb on its foot that clicks under a ledge, with a
  stiff stop beside it. Once clicked in, a wall's foot can't lift off or slide.
- **The front corners are glued butt joints.** The designer draws no corner board under the
  porch. The front wall runs right across; each side wall stops 0.1 mm behind it. The joint sits in
  the bottom of a groove that looks like the other siding grooves: a small notch down the side
  wall's front edge and a small bevel on the front wall's end column. Thin super glue wicked into
  the joint holds it.
- **The back corners get black corner angles,** glued into a shallow recess in both walls, as on
  the shed and barn (Alan, Nov 3 2026). They come in two hands, one for each back corner. Each leg
  covers 3.0 mm of its wall (3.8 in at this scale).
- **The door swings in,** like a real 11-lite door. Seen from the porch it hangs on the right of
  its doorway, next to the right side wall (your answer, Nov 4 2026: "hinges on the right side"),
  so its knob is on the left, toward the middle of the wall. It is hung in the front wall
  **before** that wall goes on the floor. Its bottom pin goes in along a little slot in the
  threshold from the inside; once the wall is on the floor, the floor closes the end of that slot,
  so the door can't come out until the walls are unclipped again. A thin stop on the latch side
  (the left), outside the door, stops it swinging out. It swings in toward the right side wall to
  about 102 degrees, where it touches the doorway's right-hand stud; it stays 6.5 mm (about 8 in)
  clear of that wall.
- **The porch.** The three posts (one at each front corner, one just left of the middle) stand in
  sockets in the deck, dry, with a small tenon at each end. The black porch frame sits on their
  tops, and their top tenons are glued into it. The
  frame's two side bands are also glued to the front wall's face. The posts and frame then come
  off the floor together with the walls. The railings' end balusters run down into holes in the
  deck as pegs and are glued there; the railings are not glued to the posts. There is one front
  railing, in the left bay under the window; the right bay, in front of the door, is the way in
  and has nothing in it but deck. The white ceiling
  drops into the frame onto a small lip and lifts out again. The porch gable sits on the frame's
  front beam on two square pegs, with a dot of glue on each so it doesn't lift with the roof.
- **The roof** is two halves. Each rests on the back gable and the porch gable and drops over two
  pegs; lift either one straight off.
- **The skids** have a front end: both corners are cut off at the end that goes under the porch.
  Turned round they don't fit.
- **Which side is which.** Both side walls have a window in the middle, so they're named as you
  see them standing in front of the porch: `right side` and `left side` (each file says which).
  The front wall's door is right of its middle and its window left; the middle post and the front
  railing are on the left too. The floor's porch end is the deck with the board grooves, and the
  line of closed pockets across it is where the front wall goes: the long one is under the door.

## Checking the fit

Before you start the big prints, print both plates of `1 fit test.3mf` and try them:

1. **Porch joints (plate 1).** Set the deck piece face up with the board grooves running away
   from you and the post's socket in the near right-hand corner: the edge toward you is the
   porch's front edge, the one on your right its side edge. The post's tenons are small tabs flush
   with one face of it: turn the post so that face is toward the right-hand side edge, not toward
   you, and push its tenon into the socket. It should go in by hand and stand square. Drop the
   frame corner onto the post's top tenon: it should sit flat on the post by itself, its side
   edge flush with the deck's and its front edge standing a little (0.6 mm) proud of the deck's
   front edge, like the real header band. Push the gable foot's peg into the frame corner's other
   socket; it should sit flat, and the two should still stand on the post by themselves. Lift them
   off again: on the short post the frame corner is where the railing end goes, so the railing end
   won't go in with it on. Push the railing end's peg into its hole in the deck piece. It stands on
   that one peg, so it leans back a little: hold it upright, and its end should stand about 0.2 mm
   off the post. If the post stands off its spot (over the deck's edge, or so the frame corner
   won't line up with the deck), it is turned the wrong way: turn it so its tenons face the
   right-hand side edge.
2. **Front corner (plate 2).** This is the front **left** corner (the right one is beside the
   door now). Set the bit of floor face up. Press the short front wall piece down onto it: its
   end column goes into the notch at the corner, its two posts into their closed pockets without
   forcing, and its prong clicks. Then lower the short side wall piece straight down beside it,
   its end against the back of the front wall piece, until its prong clicks. The joint should sit
   in the bottom of a groove on the side.
3. **Door (plate 2).** The little door hangs on the right, like the real one. Hang it in the little
   doorway the same way as the real one (step 1 of "Putting it together"), from the inside, its
   pins on your left: top pin up, bottom swung toward the doorway along the slot, let it drop. The little door is short, so it tips over more than the
   real one as you swing its bottom along the slot, and its top corner may rub the top of the
   doorway slightly at the start; that's expected, the top pin's play takes it up. The real door
   only just clears there too, so a light rub on it is fine. What matters is that once hung it
   swings in freely and stops against the strip on the latch side when shut. Look at the doorway's flat back face: there should be no slot showing over the
   top pin's hole.
4. **Roof peg (plate 2).** Stand the peg block up so the peg points up, and set the bit of roof on
   it. It should drop on and lift off without forcing.

Holes print small, so each hole is bigger all round than what goes in it: the door's pin holes
0.35 mm, the peg holes under the roof 0.4 mm, and the porch's tenon sockets, the porch gable's
peg sockets and the railings' peg holes 0.35 mm. The front wall's closed pockets have 0.3 mm
along the wall and 0.2 mm across, the other snap parts 0.2 mm, and the skids' pegs 0.2 mm (a snug
push fit on purpose, the same as on the shed and barn). If anything is tight or loose, tell Claude
which, and it will change that gap by 0.05 or 0.1 mm and remake the files. The sizes are at the
top of `make_cabin.py`.

## Cleaning up the parts

- Let the plate cool right down before you flex the parts off. Don't push a scraper under the
  prongs: each prong's leg is a thin strip lifted just off the plate.
- With a fresh hobby knife, take a light chamfer off the first-layer lip (the edge that was on
  the plate) on: the posts, stops and barbs under each wall, the front wall's end columns, the
  floor's face all round its edge and round the mouth of every socket and peg hole in the deck,
  the porch frame's sockets, the porch posts' tenons, the railings' pegs (the end balusters'
  feet), the porch gable's two square pegs, the roof pegs on both gables, the door's two pins
  (so they're round), and the mouths of the peg holes under each roof half. A lip on a post, peg
  or tenon makes it tight in its socket.
- Clear any blob or string out of the back corners' recesses and out of the door's slot in the
  threshold.
- The posts and railings print with no brim. If a post lifted at its ends, print it again with a
  5 mm brim and shave the lip off: a bent post won't stand square in its sockets. Snip strings
  between the railings' balusters with flush cutters; don't sand them.
- Snip loose strands between the studs with flush cutters. Cut strings in the windows and the
  door's lites where they join, holding the thin bars from behind with a fingertip.
- Lay each wall on glass. If it rocks, set the bed to 55 °C, lay the wall framing-side down on it
  under a sheet of paper and a flat board with about 1 kg on top, leave it 10 minutes, then let
  it cool before lifting the weight.

## Putting it together

You'll need your fingers, two rubber bands that go round the cabin, thin (water-thin) super glue
for the front corners, gel super glue or 5-minute epoxy for the rest, and a small flat
screwdriver if you ever take it apart. `how it goes together.png` shows the order.

1. **Door into the front wall, before that wall goes on the floor** (it stays in from now on).
   Hold the front wall upright with its inside toward you. Hold the door with the knob away from
   you (toward the porch side) and the pins on your left (the right as seen from the porch, the
   end of the wall that meets the right side wall), longer pin up. Push the top pin into the hole
   in the top of the doorway, keep pushing up until the door's top touches the top of the doorway
   (about half a millimetre), swing the bottom toward the wall along the little slot in the
   threshold until the bottom pin is over its hole, and let it drop. It swings in, toward you and
   round to your left, and when shut rests against the strip on the latch side (on your right)
   so it can't swing out. If a pin is stiff, take the
   door out again and twist a 2.7 mm drill bit by hand in that pin's hole now, before the wall
   goes on the floor; never lever the door. Leave it in: once the wall is clipped to the floor,
   the floor closes the slot and the door can't come out.
2. **Floor** face up on the table, without the skids.
3. **Back wall.** Lower it over the back end, trim out, posts into the notches, and press down
   over each of its 2 prongs until it clicks.
4. **Front wall, with its door.** Hold the door shut with a finger and lower the wall onto the
   line of pockets 4 ft back from the front edge, trim out (toward the porch), its two end
   columns into the notches at the corners. Press down over its 2 prongs until each clicks.
5. **Side walls, dry.** Lower each one straight down between the back wall and the front wall
   (mitre at the back, flat end down past the back of the front wall) and press down over its 3
   prongs until they click. No glue yet.
6. **Band it.** Put rubber bands round all four walls, one about 15 mm above the table and one
   about 10 mm under the top, and close the two back mitres. Look along each side: the side wall's
   face should be flush with the front wall's end column, and the groove at the front corner even
   from top to bottom. If a side wall leans out a little on its own, the band pulls it back in
   line.
7. **Front corners, with the bands on.** Touch thin super glue to the top end of each front joint
   (the hairline between the side wall's end and the back of the front wall), at its inside edge,
   and let it wick down. If it doesn't get halfway, put a second small drop there. Don't put any
   glue lower than halfway: at the floor the joint runs down into the floor's corner notch, and glue
   there would fix the walls to the floor (if you see it get down there, wipe it off at once).
   Leave the bands on 10 minutes.
8. **Back corner angles.** Try both dry first: the flat leg on the side wall, the sloped end up,
   the foot on the table. If one won't sit, it's the other hand: swap them. Then glue them one at
   a time with pin-head dots of gel super glue in the half of each recess floor nearest the
   corner. Each floor is a strip about 1.6 mm wide, and the angle covers the 1.45 mm of it nearest
   the corner. Press the angle in, let the bands back over it, and hold it for half a minute.
   Leave the bands on 15 minutes (an hour for epoxy), then take them off.
9. **Railings, before the posts.** The two side railings go down the sides. The one front
   railing (the longer one) goes across the front between the left corner post's socket and the
   middle post's socket, under the window. Each railing's cap overhangs one side: turn it so the
   cap overhangs inward, over the porch (on the side railings toward the middle of the porch, on
   the front railing toward the front wall); turned round, the pegs still go in but the cap sticks
   out past the deck's edge. The bay to the right of the middle post, in front of the door, stays
   open: it's the way in. Put a drop of glue in each peg hole and press the pegs home until they
   bottom in their holes (each peg is 0.05 mm shorter than its hole is deep, room for the glue).
10. **Posts and porch frame.** Stand the three posts in their sockets in the deck, dry. Each post's
    tenons are small tabs flush with one face of it: turn the right corner post so that face is
    toward the right side wall, and the left corner post and the middle post so it is toward the
    left side wall (the middle post is just left of the middle), never toward the front, the back
    or the way in. A post turned any other way still drops into its socket, but it stands off its
    spot: up against a railing or out past the deck's edge. The railings' ends keep them roughly
    upright. Put a small drop of gel super glue (or 5-minute epoxy) on each post's top tenon.
    Lower the porch frame straight down over them, guiding each top tenon into its socket, until
    the frame sits on all three posts. The back ends of its side bands then stand a hair (0.2 mm)
    off the front wall: leave that gap, don't push the frame back to close it, and put one drop of
    glue into each of the two gaps; the drop fills it. Don't move it until the glue has set: the
    deck holds each post's foot and the frame its top, so the posts set where their sockets are.
    Don't glue the railings to the posts.
11. **Ceiling.** Drop it into the frame, the face that was on the plate down, onto the lip.
12. **Porch gable.** Vent out, its two pegs into the frame's front beam, a dot of glue on each peg.
13. **Skids.** They have a front end (corners cut off, peg nearer the end). Lay them notches and
    pegs up, front ends the same way, and lower the cabin onto them with the porch over the front
    ends, pegs into the holes in the floor's back and front bands. Pick the cabin up by the floor,
    never by the porch (from now on, lift it by the floor or the skids). Turned round the skids
    don't sit flat. They are a snug push fit; if a peg won't go in, twist a 2.5 mm drill bit by
    hand into that hole from underneath, only to the bottom of the hole: it is 2.8 mm deep and
    doesn't go through the floor, so don't push on into the deck or floor above it. If they fall
    out when you pick the cabin up, a drop of glue on each peg keeps them.
14. **Roof.** Each half ribs up, its holes over the pegs on the back gable and the porch gable.
    Lift straight up to take it off.

## Taking it apart

Lift off the roof halves. Push the ceiling up from under the porch with a fingertip (it sits down
inside the frame) and lift it out. The walls, porch frame, posts, porch gable and door are
now one glued unit, but it still unclips from the floor. Lift the cabin off its skids and look
underneath: just inside each wall you can see the barbs in their slots. Push each barb out,
toward the siding, with a small flat screwdriver, only just far enough to clear its ledge (about
half a millimetre), and ease that bit of wall up a little. Work round until all ten barbs are
free, then lift the whole unit straight up: the post feet slide out of their sockets past the
railings. With it off the floor, the door comes off the way it went on: lift it, swing the bottom
out of the slot toward the inside, and lower it out.

## Where the model differs from the real building

- The siding is 1.4 mm thick (about 1.8 in at this scale) so it prints solid, and on the side
  walls and back wall it hangs down over the whole edge of the floor to hide the snaps.
- The wall's depth and the floor's are held at the 1:24 models' millimetres, because the snaps
  are proven at those sizes; at true 1:32 the snap slot would break out of the floor's edge. So
  the walls read 6.4 in thick at the door and windows (a real 2x4 wall with its siding is about
  4 1/8 in), and the floor's and porch deck's edge shows 6.8 mm (8.6 in) instead of 6.1 in. The studs, joists, top plates, headers, trim, openings and siding grooves are all true
  to scale.
- The bottom plate is 1.6 mm (2 in) instead of 1 1/2 in, to hold the snaps' legs. The top plates'
  underside is still at your 90 1/2 in, so the studs are 88 1/2 in instead of 89.
- The side walls and the front wall stop 0.15 mm (about 3/16 in) under the roof, so the roof rests
  on the two gables only. Only the back wall reaches your 93 1/2 in; the other three are 93 5/16 in
  to the top of their top plates. The side walls' top plates are 3/16 in thinner. The front wall's
  are whole but sit 3/16 in lower, so its studs are about 88 5/16 in.
- The corner angles cover 3.0 mm (3.8 in) of each wall, a little more than a 3 1/2 in board,
  so each sits on 1.45 mm of glue.
- The back corners are mitred under a black corner angle, as on the shed and barn models (my
  choice, so they use the proven joint); the designer runs the front and back walls through and
  butts the side walls between them.
- The front corners have no corner board, as the designer draws them under the porch.
- Every framing member runs the full depth of the wall, so the wall prints lying flat.
- The gable vents are set into the siding instead of standing out (Alan, Nov 3 2026).
- The porch posts are 3.25 mm square, the designer's drawn size held to a print layer.
- The porch's side bands (the frame down each side) are flush with the side walls; the designer
  has them 1/4 in (0.02 ft) proud.
- Three of the twenty deck-board grooves stop short: two start just behind the middle post's
  socket and the front railing's right-hand end baluster instead of at the deck's front edge, and
  one stops 0.8 mm short of the front wall's face. Laid out as the designer does, they would run
  into or pass within 0.6 mm of a post socket, a railing peg hole or the gap round a front-wall
  post, leaving deck too thin to print on the floor's first layer. So every socket and peg hole
  keeps 0.6 mm of plain deck round it.
- The railings' caps overhang toward the porch instead of being centred, so each railing prints
  lying on its outside face; the gap under the cap is filled. The balusters are centred in each
  panel (nine on the front railing, seven on each side railing), so the two side panels are the
  same part.
- The railings stand on their pegs: each end baluster runs on 1.2 mm into a 1.25 mm deep hole in
  the deck, so pressed home in its glue a railing sits 0.05 mm (about 1/16 in) under its drawn
  height.
- The door's sill runs over the right-hand skid now that the door is right of the middle, so its
  foot stops 0.3 mm up inside its pocket instead of flush with the floor's underside, and only the
  floor stands on that skid: a sill printed a hair long can't lift the front wall off the deck.
- The ceiling is a lift-out panel sitting 0.65 mm above the bottom of the header band.
- The door's knob is 2.2 mm in from the latch edge (the designer's 0.30 ft would put it over the
  glass).
- The window casings have no sill nose, and the heads and sills are plain boards, as on the shed
  (you confirmed that for the shed and barn models, Oct 31 2026).
- There are no trusses or roof deck between the gables, so you can see in with a roof half off.

**Your standard layout (yours, from your site).** Where the door, the three windows, the porch
posts and the front railing go is your standard (designer-standards.js on yoder-storage-barns.com,
your copy-this-build codes, Aug 2026): door 1.74 ft right of the front wall's middle, one window
2.57 ft left of the middle, a window in the middle of each side wall, a post at each front corner and one
0.3 ft left of the middle, one front railing from the left corner post to the middle post. The
designer's stock layout, which this model had before, put the door in the middle with a window
either side, a window on the right side wall only, four posts and two front railings.

**Not your numbers yet.** Apart from the walls and the roof (questions 1 and 2), the door's size,
which you chose to keep as the builder draws it (question 15), and its hinge side (question 16),
you haven't confirmed any cabin sizes, so these are the designer's (Barnwright's) or my choice.
Each open question has the default the model uses; tell Claude if yours is different and it will
change the numbers, not the method.

| # | Question | Default used in the model |
|---|---|---|
| 1 | Cabin wall height: the designer's 7.4 ft (88.8 in), or your 93 1/2 in utility wall? You answered on Nov 4 2026: "Cabin 93.5". | **Answered:** 93 1/2 in from the floor to the top of the top plates: 89 in studs, one bottom plate and two top plates, as on your utility sheds. The doors and windows stay where they were, with longer cripples over their headers |
| 2 | Cabin roof: the designer's rise of 0.27 x width (6.48/12) with 0.42 ft of eave along the slope, or your 5/12 with a 4 in level eave? You answered on Nov 4 2026: "roof pitch 5/12". | **Answered:** 5/12, rising 25 in over the plates, with a 4 in eave measured level past the side walls. The rake stays the designer's 0.45 ft |
| 3 | Porch 4 ft deep? | 4 ft, the designer's |
| 4 | Is there a step up to the porch at the way in? (The posts' places are your standard now.) | No step, as the designer |
| 5 | Corner boards where the front wall meets the side walls under the porch? | None: a plain corner, the joint hidden in a groove |
| 6 | Porch ceiling white, at the bottom of the header band? | A white lift-out panel, 0.65 mm above the band's bottom |
| 7 | The 11-lite door swings in? | In-swing, hung in the front wall before that wall goes on the floor; after that it comes out only with the walls unclipped. (An out-swing door like the shed's could go on and off any time, if you prefer.) |
| 8 | Window tops at 76 1/2 in, level with the wooden-door height (0.9 in above the 75.6 in lite door's head), with the designer's 2x6 doubled headers? | As the designer |
| 9 | Gable band on the back gable at the eave line, like the shed, rather than the designer's slightly higher band? | At the eave line |
| 10 | Skids: two, inside face 30 in from the outside wall (your 10x16 lesson, Sep 27 2026), or the designer's table (centre 30 in from the edge, 1 3/4 in further out)? | Your lesson |
| 11 | Railing 34 1/2 in tall with 2x2 balusters about 5 1/4 in apart, cap toward the porch? | As the designer, cap toward the porch so it prints |
| 12 | Corner angles a bit wider than scale (3.8 in on each wall against a 3 1/2 in board), so each sits on 1.45 mm of glue? | Yes |
| 13 | Door header: your usual 5 in loft header (two 2x4s on edge on a flat 2x4) over the 75.6 in door, or the designer's doubled 2x6 (5 1/2 in)? | Your 5 in header |
| 14 | Six 16 in layout studs land on other framing: on each side wall 16 in each side of the window's middle (on the window's full studs), on the front wall 44 in left of the middle (on the window's left king stud), and on the back wall 52 in toward the left side, at the corner. Drop them (the stud they hit stands there), or move them? | Drop |
| 15 | Door size. Your building pages list the Cabin's 11-lite door as 36 x 80 in, but your site's own 3D builder, with your standards file applied, still draws it 3 x 6.3 ft (36 x 75.6 in), the size this model and the designer use. Which is right? You answered on Nov 3 2026: "Keep builder sizes". | **Answered:** 36 x 75.6 in, as the builder draws it |
| 16 | Door hinge side. Your standard layout puts the door right of the middle but doesn't say which side it hinges on. The designer hinges the 11-lite door on the left as seen from the porch, which puts the hinges toward the middle of the wall, so the door swings in toward the middle of the room with the knob toward the right side wall. Keep that, or hinge it on the right, next to the right side wall? You answered on Nov 4 2026: "hinges on the right side". | **Answered:** hinged on the right as seen from the porch, next to the right side wall; it still swings in, now toward that wall, with the knob toward the middle of the wall. The door is where it was |

Also the designer's, not yours: the 2x3 windows (25.2 x 34.8 in),
the vents (1.12 x 0.76 ft, 0.92 ft under the ridge), the
porch's header and side bands (0.29 ft deep, held at 2.85 mm to print), the rake (0.45 ft), the
floor and wall framing (2x6 joists, and 2x4 studs 16 in apart; their 89 in length and the three
plates are your wall's), the window
headers (2x6 doubled), the porch deck boards (5 1/2 in with 1/4 in gaps) and the two 4x6 skids
on edge. The skids are as long as the building, which is my choice (real skids come in their own
lengths). The way the floor sheets are laid (4x8 sheets in rows 4 ft across, staggered 4 ft)
follows the designer's skill for laying out a floor.

## Changing it

Everything is made by `make_cabin.py` from the numbers at the top of the file (building size,
wall height, roof, porch, door and window positions, clearances, the snap joints, the corner
angles). It writes the `.stl` files and both `.3mf` files. `draw_cabin.py` draws
`how it goes together.png`. `check_cabin.py` then proves the parts still fit, about 230 checks
in twelve groups:

- every piece is one solid piece and fits the bed; with the whole cabin put together, no two of
  its 21 parts overlap; the walls and floor fit round each other with their gaps (0.2 mm, 0.3
  along the front wall's pockets, 0.4 inside the skirts), with 1.8 mm of solid floor either side
  of the front wall's pockets and, measured along each wall, at least 0.93 mm between
  neighbouring pockets and slots;
- each wall stands on the floor, its barbs hold it down, and it goes on straight down from
  140 mm in the order above (the front wall with its door hung in it), nothing in the way but
  its barbs; as printed, each barb still hooks 0.3 mm or more under its ledge; every prong stands
  in a stud bay and none is under the door or its sill;
- each wall prints flat with nothing steeper than 45 degrees that isn't a short bridge, the trim
  only in the top 0.6 mm and nothing white above the siding's top layer; the six dropped layout
  studs are exactly the ones listed above; nothing stands in a doorway or window but the door's
  stop and the window sashes, and each window has its whole sash; the floor's first layers have
  nothing thinner than a line;
- each back corner angle sits on both recess floors (1.45 mm of glue land each) and touches
  nothing else, also as printed; each front joint is 0.1 mm and sits at the bottom of a groove;
- each gable vent's louvres and the gaps between them are wider than a printed line on every
  layer, and the vent is framed with kings, a flat sill and a cripple;
- the porch: each tenon and peg 0.35 mm clear in its socket (at least 0.25 as printed), every
  socket in solid floor or frame, the ceiling 0.2 mm off the beams on 1.0 mm of lip, the frame
  and gable resting where they should, 0.15 mm under
  the roof, the railings 0.2 mm off the posts and their pegs 0.05 mm short of their holes' floor,
  the one front railing between the left corner post and the middle post under the window, the
  way in open with the doorway inside it, and the walls, posts, frame and gable lifting off the
  floor together past the railings;
- the door hangs on the right as seen from the porch (its pins and both pin holes centred 1.35 mm in
  from the doorway's right-hand jamb, its knob and the stop on the left), swings in toward the right
  side wall to about 102 degrees, at least as far as it did hinged on the left, without touching
  the floor, any wall, corner angle, the porch or the roof, won't swing out, hangs in the loose
  front wall by the slot, and is captive once the wall is on the floor (a floor sheet seam now
  runs into the room right beside the bottom pin, but it is a fifth as wide as the pin and can't
  help it out); the door is the Lofted Barn Cabin's door but for its height (that one is 73 1/2 in,
  under that model's lower walls, drawn the designer's way; built 75.6 in tall by
  `make_barn_cabin.py` it is this door exactly), and the fit test's door and doorway are the same
  solid (the checker loads that model's `make_barn_cabin.py`, in the folder beside this one, to
  compare);
- the roof halves rest on both gables all the way along the slope (lowered 0.02 mm, each meets
  both in every millimetre from the ridge out to 45 mm) and are held by their pegs; the skids
  fit, and don't fit turned round, and the front wall touches neither of them (the door sill's
  foot is 0.3 mm up); every plate's parts are on the bed, 3 mm apart, clear of the prime tower, with
  one colour change on plates 1 and 3 and the right brims; the bridge modifiers are on the walls,
  fit-test pieces and floor above, each read as the shape it is, the walls' starting over the
  framing and the floor's on its second layer only, each laying the bridges across its seam (or
  the deck boards' grooves), and the bridges they lay are 20 mm or less, and so is every bridge
  they leave to Flash Studio, whichever way it lays it (on the floor, even where a groove runs out
  into a slot or off an edge); the `.stl` and
  `.3mf` files in the folder are exactly what `make_cabin.py` makes now, so a file left from an
  older run fails;
- the fit test's pieces are cut from the real parts and go together the same way, its short door
  hangs on the right like the real one, no cut in a fit-test piece leaves a strip thinner than a
  line, and the frame corner, with the gable foot on it, stands on the short post by itself;
- measured off the parts, the back wall is your 93 1/2 in to the top of its top plates and the
  other three walls 3/16 in (0.15 mm) less, where they stop under the roof; the top plates'
  underside is at 90 1/2 in (89 in studs on a 1 1/2 in plate), 3/16 in lower on the front wall;
  the gable band's top is on the plates' top, and the roof is your 5/12 with a 4 in eave measured
  level; the other sizes are the designer's, and the door, the three windows and the
  three posts are where your standard layout puts them (the checker has your numbers written in
  itself, so a wrong number in `make_cabin.py` fails); each window is framed the shop's way, a
  king stud and a full stud each side, the 2x6 doubled header bearing 1.5 in on each king, a
  rough sill and cripples on the 16 in marks, compared slice for slice with that plan.

The last review (Nov 3 2026) raised the door sill's foot 0.3 mm off the right-hand skid,
made the railings' pegs 0.05 mm shorter than their holes are deep (as on the Lofted Barn Cabin),
and cut the fit test's frame corner smaller, about 7 mm each way from the corner instead of
15 x 12 mm, with its gable peg moved in beside the post, so it balances on the short post by
itself (the bigger one hung 2 mm past the post's top and fell off). The steps above were tidied
to match.

A check after that (Nov 3 2026, as on the Lofted Barn Cabin) moved the end of the fit test's gable
foot from 41.0 to 41.275 mm right of the middle, the middle of a siding groove: at 41.0 it left a
strip of siding 0.025 mm wide at that end in its top layers, thinner than one line, which Flash
Studio leaves out. And step 1 of "Checking the fit" now has you lift the frame corner and gable
foot off the short post before the railing end goes in: on the short post the frame corner sits
where the railing end's peg baluster and rails go.

Moving to your standard layout (Nov 3 2026) changed, besides the openings and the porch: the
front wall's framing (each opening has its own king and full studs each side now), its right-hand
prong, moved from 34.1 to 37.1 mm right of the middle because its slot would have run into the
door's sill pocket, the floor's pockets, sockets and peg holes, the porch frame's sockets, and the
fit test's front corner, now the left one, cut from x 47.6 to 20.5 mm left of the middle (the
right one is in the door). The old `window side.stl` and `plain side.stl` are gone; the side
walls are `right side.stl` and `left side.stl`.

Your answer on Nov 4 2026, "hinges on the right side", moved the door's hinges to the other side of
the same doorway: its two pin holes are now centred 1.35 mm in from the right-hand jamb (29.5 mm right of
the middle), the stop strip is on the left-hand jamb, and the door is the mirror image of the old
one, its knob 2.2 mm in from its left edge. It still swings in about 102 degrees, now toward the
right side wall. Nothing else moved. The fit test's little doorway and door hang the same new way,
and the print times and grams stayed the same. `how it goes together.png` now shows the door
from above at the bottom, swung open.

Your answers on Nov 4 2026, "Cabin 93.5 , roof pitch 5/12", made every wall 3.73 mm (4.7 in)
taller, 93 1/2 in to the top of the top plates, and the roof flatter: 5/12, rising 25 in over the
plates instead of 32.4, with a 4 in eave measured level instead of 0.42 ft along the slope. Even
with the taller walls, the ridge is 2.14 mm (2.7 in) lower than before. The door and the windows
did not move (the window tops are still at 76 1/2 in): the cripples over their headers are longer.
The posts are 3.73 mm longer, and the porch frame, ceiling and porch gable sit that much higher.
The gable band is still on the top of the plates, and the vents are still 0.92 ft under the ridge.
The porch gable has one stud fewer, the one 44 in left of the middle: under the flatter roof there
is no room for it between the two chords (the designer leaves out any stud shorter than 0.05 ft).
The roof halves are 3.5 mm narrower, and the corner angles 3.4 mm longer. The fit test's pieces
are cut from the new parts. Plate 1 now takes 2 h 18 min instead of 2 h 14 min, and plate 2
1 h 22 min instead of 1 h 26 min; every plate still fits the bed, and plates 1 and 3 still change
colour once. `how it goes together.png` shows the new walls and roof.

A check of those changes (Nov 4 2026) moved no part. The side walls and the front wall are 3/16 in
short of your 93 1/2 in on purpose, where they stop under the roof, and the read me now says so
(see "Where the model differs"). The checker now measures each wall as it is, proves each roof
half rests on both gables all the way along, and compares the door with the Lofted Barn Cabin's,
which is the same door but for its height (that model's door became 73 1/2 in later the same day,
when its walls went to your 79 1/2 in).

To make a different size, ask Claude to change the numbers and run all three.
