# 8x12 Side Utility model — read me first

A 1:24 model of the shop-standard 8x12 Side Utility (one inch on the model = two feet on
the real building). It snaps together with no glue. Half the roof lifts off so you can see
the framing inside, and the 48 in wooden door swings open on two small pins.

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
| `1 fit test.3mf` | A short doorway and door, a roof peg and a bit of roof, and one short corner of the shed (a bit of floor and short pieces of the door wall and end wall) | Any | about 27 min. **Print this first.** See "Checking the fit" below. |
| `2 all plates.3mf` | Everything else, one plate per print: | | |
| plate 1 | Both long walls | 1 white, 2 black | about 2 h 40 min, 1 colour change |
| plate 2 | Both roof halves | 2 black only | about 1 h 5 min |
| plate 3 | The door | 1 white, 2 black | about 22 min, 3 colour changes |
| plate 4 | Both end walls | 1 white, 2 black | about 2 h 15 min, 3 colour changes |
| plate 5 | The floor and both skids | 3 brown only | about 1 h 30 min |

Start Flash Studio first, then open them with **File → Open Project** (Ctrl+O), or **Open
Project** on its Home page. Starting Flash Studio by opening the file itself can leave it stuck
on "Loading". If Flash Studio says the file is from a newer version, click OK; it loads fine. If
it asks about unsaved changes to your settings, click **Discard** (the file brings its own). The
files carry their settings: the Flashforge AD5X 0.4, `0.20mm Standard @FF AD5X`, and three
filaments, 1 white, 2 black and 3 brown. Pick a plate, then Slice plate and Print plate as usual.

Each wall prints lying flat, inside face down, so its trim (corner boards, door and window
casings, gable bands) is on top and already set to **filament 2**; the siding is filament 1.
Filament 1 (white) is the siding on every plate, filament 2 (black) the trim and the roof, and
filament 3 (brown) the floor and skids. For other colours, click a filament's colour square in
the Filament panel. When you send the print, match filaments 1, 2 and 3 to slots 1, 2 and 3 in
the AD5X's material station. The prime tower goes in the back
right corner of the plate; every plate is laid out to keep it clear.

The walls meet at the corners on 45-degree mitres, so each wall carries only the trim on its
own face, all in the top 0.6 mm. On the long walls the colour changes once, for the last three
layers. On the end walls the white vent louvres come up level with the trim, and on the door the
black trim sits round the white hinge edge, so those plates change on each of the last three
trim layers.

The `.stl` files are the same pieces one at a time, all one colour, if you'd rather set up
a plate yourself (`end wall.stl` serves for both ends, `floor.stl` is already upside down).
For two colours use the `.3mf` files.

**Settings:** already in the file: `0.20mm Standard @FF AD5X` with **Wall generator →
Arachne** (it shows in orange as changed), because the siding is only 1.4 mm thick and Arachne
fills thin walls solid. **Elephant foot compensation** is 0.1 mm, the AD5X's own setting (Quality
tab, under Precision); keep it there: the barbs, stops and posts under the
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
  out. The back wall has three prongs, the door wall and each end wall two. Once clicked in, a
  wall can't lift off, lean out or slide along.
- **Corner hooks.** The top of each long wall's corner post carries on past the mitre into the
  end wall's corner as a hook, with a small tip that drops into a pocket in the end wall. That
  ties the tops of the corners together and holds the end walls down. In front of each pocket
  a slope catches the tip and pulls the end wall upright as the long wall goes down.
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
3. Set the bit of floor face up. Of the two short wall pieces, the end wall is the one with the
   sloping top; the side with the raised corner board and the siding grooves faces out. Press
   it straight down onto the floor's short edge: its prong should click into its slot with a
   firm push, and the siding should hang down over the floor's edge. Then lower the other piece
   (the long wall) straight down beside it, so its hook goes into the end wall's corner and its
   prong clicks. The corner should close on its mitre, and neither wall should lift off. If a
   prong won't click, or a wall lifts off after clicking, tell Claude which.

Pin holes are already 0.35 mm bigger than their pins, peg holes 0.4 mm bigger than the pegs,
and the snap parts have 0.2 mm round them. Each barb hooks 0.45 mm under its ledge. If
anything is too tight or too loose, ask Claude to change that gap by 0.1 mm (or the barbs'
catch, if the prongs won't click or won't hold) and remake the files. The sizes are at the
top of `make_shed.py`.

## Cleaning up the parts

- Let the plate cool right down before you flex the parts off. Don't push a scraper under
  the ends of a wall (the mitred ends come to a thin edge with the black trim on top) or under
  the prongs: each prong's leg is a thin strip lifted just off the plate, joined to the wall at
  the top and to its barb at the foot.
- With a fresh hobby knife, take a light chamfer off the first-layer lip (the edge that was
  on the plate) on: the posts, stops and barbs under each wall, the inside edge of the mitre at
  both ends of every wall, the floor's face all round its edge, the door's two pins (so they're
  round), and the mouths of the peg holes under each roof half. A lip on a post, stop or barb
  makes it tight in its slot; a lip round the floor's face rubs on the skirts. Don't scrape the
  mitre faces, and don't trim the barbs' flat tops.
- If the siding has sagged a little on the inside of the end walls' top corners (just above
  where the long walls' hooks go), shave off any loose strands there.
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
   solid band across each end of the floor, and the joists drop into the notches. The holes put
   the skids in the right place. They are a snug push fit; if they fall out when you pick the
   shed up, a drop of glue on each peg keeps them.
3. **End walls.** Hold an end wall over one end of the floor, peak up and trim facing out,
   with its siding outside the floor's edge. Line up the posts along its bottom with the
   notches in the floor and its two prongs with their slots, then press straight down on the
   top of the wall above each prong in turn until it clicks. Do the other end the same way. They
   stand on their own, leaning out a little at the top until the long walls are on.
4. **Back wall.** Hold the back wall (the one without the door) over the back side of the
   floor (the side with a notch for every stud), trim facing out, and lower it straight down
   between the end walls, keeping it level: the hooks on its top corners slide down into the
   end walls' corners, its posts and prongs into the floor, and its mitred ends close against
   the end walls'. As the hooks go in, their tips slide down a slope into their pockets and pull
   the leaning end walls upright; if a tip sits on top of an end wall's corner instead, push
   that end wall's top in a little. Press down over each of its three prongs (one stud bay in
   from each end, and in the middle) until it clicks.
5. **Door wall.** The same way on the door side; it has two prongs, one stud bay in from each
   end. Check that the black corner boards meet top to bottom, and the floor is level with the
   doorway threshold.
6. **Door.** Hang it the same way as in step 1.
7. **Roof.** Each end wall has a peg on each sloping edge, and each roof half has a hole
   under each end. Set a half ribs up with its raised ridge strip at the peak, so its two
   holes drop over the two pegs on that side. Either half lifts straight off; always lift
   straight up, never slide it along the pegs.

**Taking it apart:** lift off the roof and the door, and lift the shed off its skids. Look
underneath: just inside each wall you can see the barbs in their slots. Push each barb out,
toward the siding, with a small flat screwdriver, only just far enough to clear its ledge
(about half a millimetre; don't lever it hard against the far side of the slot), and ease that
end of the wall up a little. When all of a long wall's prongs are free, lift it straight up.
Take the long walls off first; the end walls can't come off until they're gone. If you want it
permanent instead, a drop of glue down each inside corner does it.

## Old files

`all on one.3mf` and `all lay out.3mf` are your own Flash Studio projects of the earlier,
glue-together version. Its walls and floor don't fit these, so don't print from them.

## Changing it

Everything is made by `make_shed.py` from the numbers at the top of the file (building
size, wall height, pitch, door and window positions, clearances, the snap joints). It writes
the `.stl` files and both `.3mf` files. `check_shed.py` then proves the parts still fit:

- each wall goes on straight down (the end walls first, then the long walls between them) with
  nothing in the way but its barbs, stands on the floor, and can't lift, lean or slide once
  clicked in;
- the corner hooks tie the walls together, and find their pockets even with an end wall
  leaning out 2 mm at the top;
- the barbs still catch once the parts are cut into 0.2 mm layers and anything thinner than a
  line is rounded off, and the prong legs bend less than PLA can take;
- the door swings to about 98 degrees and won't swing in; each roof half rests on the gable
  ends and is held by its pegs; the skids fit under the joists;
- each wall and the floor print flat, with nothing steeper than 45 degrees that isn't a bridge
  held at both ends (apart from a small flap of siding over each corner hook on the end walls),
  the walls' trim all in the top 0.6 mm, and nothing on the bed thinner than one line.

To make a different size or style, ask Claude to change the numbers and run both.
