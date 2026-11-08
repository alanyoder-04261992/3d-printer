# Printer Brain

Everything about our 3D printing setup in one place: the printer, the slicer, the
filament, the settings that work, and what we've learned the hard way.
**Keep it up to date** — when something changes or a print teaches us something, add it here.

_Last updated: 2026-11-08_

---

## The printer

| | |
|---|---|
| Printer | **Flashforge AD5X** |
| Colour system | IFS 4-spool multi-colour feeder |
| Build volume | **220 × 220 × 220 mm** |
| Nozzle fitted | **0.4 mm** (0.25, 0.6 and 0.8 mm profiles are also installed in the slicer) |
| Build plates | **Textured PEI** (used for almost everything), High Temp Plate (used a few times) |
| Firmware | 3.1.5 (update file `AD5X-3.1.5-…-20260626.tgz` is on the flash drive, not in this repo) |

## The slicer

| | |
|---|---|
| Software | **Orca-Flashforge** v01.10.01.50, and now **Flash Studio Desktop 1.7.20** (Flashforge's newer slicer; it reports itself as Orca 2.4.0.2) |
| Printer profile | `Flashforge AD5X 0.4 nozzle` |
| Usual print profile | `0.20mm Standard @FF AD5X` (129 of 134 files) |
| Saved custom presets | **None yet.** Everything uses the built-in profiles. |
| Settings folder | `%APPDATA%\Orca-Flashforge` (custom presets would go in `user\`) |

### What the stock profile actually does
Pulled from the settings saved inside our print files:

| Setting | Stock value |
|---|---|
| Layer height | 0.20 mm |
| Walls | 2 |
| Infill | 15 % grid |
| Wall generator | Classic |
| Seam | Aligned |
| Part cooling fan | 100 % |
| Aux side blower | 70 % (some profiles 100 %) |
| Outer wall speed | 200 mm/s |
| Acceleration | 10 000 mm/s² |
| Retraction | 0.8 mm |
| Brim | Auto |
| Supports | Off by default (turned on for 29 files) |

---

## Filament we use

Temperatures are the ones we've actually printed with.

| Filament (slicer preset) | Nozzle | Bed | Notes |
|---|---|---|---|
| Generic PLA | 220 °C | 55 °C | The everyday default. Most-used colours: teal `#26A69A` and black. |
| Flashforge PLA Pro (PLA+) | 210 °C | 60 °C | |
| Generic / Flashforge PLA Silk | 230 °C | 55–60 °C | Helmets, book covers, catapult legs |
| Generic PLA Matte | 220 °C | 55 °C | Vases, army men, knife handle |
| Flashforge PLA Color Change | 220 °C | 55–60 °C | |
| Generic PLA High Speed | 220 °C | 55 °C | |
| Generic TPU (flexible) | 240 °C | 35 °C | iPhone 15 Pro case, airless ball, TPU knife blade |
| PETG | 245–255 °C | 80 °C | Sword blades. **Dry it first** — see below. |

**IFS slots (Nov 2 2026):** 1 white, 2 black, 3 brown, 4 empty. The printer's screen still shows
them as teal, orange and magenta because their colours weren't changed there.
**Still to fill in:** what spools are on the shelf.

---

## Lessons learned

### Strong parts (anything that bends, flexes or gets hit)
The stock profile runs cool with both fans at full blast. That's fine for looks and terrible
for strength, because the layers don't weld together. For swords, springs and toys that get
played with, change these:

| | Stock | Strong PLA | Tough PETG |
|---|---|---|---|
| Nozzle | 210–220 °C | **230 °C** | **245 °C** |
| Bed | 55–60 °C | 60 °C | **80 °C** |
| Part fan | 100 % | **40–50 %** | **25 %** |
| Aux blower | 70–100 % | **off** | **off** |
| Speed | up to 200 mm/s | **60 mm/s** | **50 mm/s** |
| Acceleration | 10 000 | **3 000** | 3 000 |
| Flow | 0.98 | 1.02 | 1.00 |
| Retraction | 0.8 mm | 0.8 mm | **1.2 mm** |

- **Wall generator → Arachne** for thin walls (anything 0.8–2.5 mm). Classic leaves a hairline
  gap down the middle of thin walls; Arachne fills them solid.
- **Seam → Random or Scarf joint** on tall thin parts, so the seam doesn't form a weak vertical line.
- **PETG beats PLA/PLA+ for impact**, roughly 2×. PCTG is the next step up. Avoid PETG-CF for
  anything that needs to survive a hit — it's stiffer but more brittle.

### PETG
- **Dry it before every print:** 65 °C for 6 h in a dryer, or on the bed at 70 °C under a
  cardboard box for 6 h. Wet PETG hisses and pops, comes out foggy and stringy, and is
  weaker than PLA.
- Use the **textured plate**. On smooth PEI it can tear the sheet, so put glue stick down
  first as a release layer.
- Expect stringing. Clean the webs out of hollow parts before assembling them.

### Fit and clearance
- Print a **fit test** before any long print with sliding or snap parts.
- **0.2 mm per side** = snug (stars stood firm but were tight). **0.25–0.3 mm per side** = easy
  fit. 0.4 mm = loose.
- If a fit is off, **scale the small part** (the star or the blade) by 1 % at a time, never the
  big part it fits into.
- **Holes print small.** For a pin or peg that goes into a hole, make the hole at least
  **0.35–0.4 mm bigger all round** than the pin (Alan, Oct 2026).
- **Snap fits instead of glue** (shed model, Nov 2026). Build the barb out of layers, not
  out of line width. On a part printed flat, a barb drawn in the bed plane has to be wider than
  about two lines (0.8 mm) or the slicer rounds it off: a 0.55 mm barb came out level with the
  slot wall and would have held nothing. Instead make the leg bend up and down through the
  layers, with the barb stacked from the bed in 0.2 mm layers: the shed's leg is 3 mm wide,
  0.8 mm thick and 5.5 mm long, the barb hooks 0.45 mm under its ledge, 0.2 mm gap all round,
  about 1.8 % strain going in (keep it under 2 % for PLA). Put each size on a layer line
  (first layer 0.25, then 0.2). Use Elephant foot compensation 0.1 mm.
- **Glue a corner piece over a mitre; don't hook it** (shed and barn models, Nov 3 2026). The
  hooks that tied the tops of the corners had tips only 1.0 × 1.2 mm, printed into the flat
  walls. On the first barn they snapped, held nothing, and the mitres showed a hairline gap.
  Now each wall has a shallow recess beside the corner, exactly 2 layers (0.4 mm) deep. A
  separate L angle in the trim colour glues into both recesses, covering the joint from bottom
  to top. It hides the gap and holds the corner along its whole height. The angles print on
  the one-colour roof plate, so they add no colour changes. For walls already printed with
  the old corner boards, a thin L cap glues over the old boards instead.
- **Check a fit as printed, not just as drawn** (Nov 3 2026). The angle's 1.0 mm inside fillet
  cleared the walls' 45 degree corner chamfer by 0.1 mm in CAD, but sliced into 0.2 mm layers
  both became staircases, and the steps ran into each other. A leg drawn 4.354 mm tall printed
  22 layers (4.45) and used up its clearance. Put every height on a layer line, and test parts
  that meet on a slope layer by layer. `check_shed.py` and `check_barn.py` do this now; the
  fillet is 0.8.
- **The taller wall goes on last** (barn model, Nov 2026). Where one wall stands much taller
  than the other at a corner (a barn end's gable over the long wall), put the corner hooks on
  the tall wall and fit it last. A hook on the short wall would have to come down through the
  tall wall's corner, leaving a big flap of siding over nothing when the tall wall prints flat.
  (The corner hooks are gone now, see above, but the end walls still go on last.)
- **Check where a tall wall's weight is.** A wall with no door or windows has most of its
  weight in its siding, out past the edge of the floor it stands on, so it leans out on its own
  (the barn's back wall: 2 1/2 mm at the top, more than a corner hook can catch). Tie the tops
  before the hooks go on (the barn's lofts do it), and put a 45 degree bevel where an edge
  could land flat on another edge.
- **A bent roof prints as flat sheets.** A barn (gambrel) roof side can't lie flat with its
  ribs up in one piece, so print the upper and lower sheets separately, ribs up, and let the
  upper sheet's tail lap over the lower one, the way the real steel goes on. Give the steep
  sheets pegs standing straight up, not square to the slope: square to the slope, the sheet's
  bottom swings out and it falls off with the model tipped about 20 degrees. Put each hole its
  clearance further out than its peg so the sheet rests where it's drawn, and leave about
  0.4 mm under anything that laps over it: a slot through a sloping sheet prints in steps, so
  the sheet sits up to 0.3 mm higher than drawn. Put roof pegs on the face of a wall that prints
  on the bed, so they lie on the bed instead of in the air.
- **Pick the scale from the bed** (cabin and garage models, Nov 3 2026). The longest wall has
  to lie flat on the 220 mm bed beside the prime tower. 1:24 suits a 12 ft shed (152 mm), but a
  20 ft wall needs 1:32 (190 mm) and a 24 ft wall 1:36 (203 mm).
- **Stop decorative grooves short of holes** (cabin models, Nov 3 2026). Deck-board grooves
  that ran past the railing peg holes left strips of floor 0.16 to 0.27 mm wide, under one
  line, which print loose or not at all. Stop a groove 0.6 mm short of any hole, and check the
  first layer for strips thinner than a line.
- **Keep thin glue in the top half of a joint that runs into the floor** (cabin models, Nov 3
  2026). Water-thin super glue wicks to the bottom of a joint. Where the joint runs down into
  the floor's notch, it glues the walls to the floor and the model no longer comes apart.
- **Let a peg bottom in its hole.** Make the peg 0.05 mm shorter than its hole is deep, so the
  part stands at its drawn height instead of dropping until something else stops it.
- **Make fit-test pieces stand up by themselves** (cabin models, Nov 3 2026). The porch frame's
  corner sat on one short post with its weight 2 mm past the post's top, so it fell off, and
  that would have looked like a loose socket. Cut a piece that rests on one support so its
  centre of mass is at least 0.4 mm inside the support, more than the joint's play. Then try the
  test pieces in the read me's order: the railing end couldn't go in with the frame corner on.
- **Cut through the middle of a groove, never just beside it.** A fit-test cut 0.025 mm short
  of a siding groove left a strip thinner than a line, and the slicer dropped it.
- **Nothing but the floor should land on a skid.** When the cabin's door moved over a skid, the
  door sill's foot ended up resting on the skid's notch at the same height as the floor's
  underside. Raise anything like that 0.3 mm (`SILL_UP`).
- **Check a sliding fit on its first layer, with the part pushed to one side** (garage models,
  Nov 4 2026). The roll-up door leans on two 45 degree stops up the sides of its doorway. Drawn
  and centred it cleared them, but printed, both first layers spread, and with the door pushed
  sideways its first layer could meet theirs. The stops' first layer now stands back 0.45 mm from
  the slope, 0.1 mm more than the layer above.
- **Test a tall thin part on a plate like its real one.** The roll-up door's black handle stands
  above everything else on its plate, so its top layers print alone, 1 to 3 seconds a layer. A
  fit test with taller parts beside it would print the handle differently and prove nothing, so
  the fit plate holds only the half door and its doorway. If the grip comes out slumped, set
  filament 2's Min print speed to 5.
- **A spring put in wrong can feel the same as one put in right.** Leaned in too far, the roll-up
  door's hidden springs go up behind the little blocks they should press on, not under them.
  Nothing printable can stop that: it would have to stand behind the wall's inside face, the face
  the wall prints on. So the read me gives a check you can feel: lift the door a little and let
  go. Seated right, it snaps back down; seated wrong, it stays up.

### Checking a print file without opening it
- Flash Studio slices from the command line without opening a window:
  `"C:\Program Files\Flashforge\Orca-Flashforge\flash studio.exe" --slice 0 --debug 2 --outputdir <folder> <file>.3mf`.
  It needs printer and print settings inside the `.3mf` (`Metadata/project_settings.config`,
  copied from any project Flash Studio saved) and an `OrcaSlicer 2.4.2` version tag. Without
  `--debug 2` it prints nothing, warnings included; with it, look for lines containing
  "slicing warnings" ("floating regions", "floating cantilever"). It writes one `.gcode` per
  plate with the time, grams and colour changes at the top.
- "Floating regions" on a part printed flat can be a thin sliver that starts in mid-air: for
  example a slot cut in from the bed side with more of the part on its far side.
- **Flash Studio can bridge a wall's siding the long way, and not the same way every slice**
  (Nov 4 2026). The model walls print framing side down, so the first siding layer bridges the
  stud bays. Left to itself, Flash Studio sometimes laid it as 60–94 mm strands along the bays
  instead of 10–16 mm across them, and the same file came out either way from one slice to the
  next: the 8x12 Side Utility's door wall went the long way in 7 of 25 slices. The fix is a
  modifier box over the wall, from just under the siding up, that sets **External bridge infill
  direction** to 180 (Flash Studio reads that as along the bed's X, across the studs). Where
  across would leave a gap, as in a barn end's triangles above the collar tie, split the box at a
  framing member and set 90 above it. The direction is fixed to the bed, not the part, so never
  turn a part that carries one; the `.stl` files don't carry it at all. Give a fit-test piece
  the same modifier as its real wall, because a modifier also moves a little infill nearby.
- **A groove cut into the first layer is a slot the second layer has to bridge.** The model
  floors print face down with 0.4 mm sheet seams in that face, and Flash Studio bridged the
  second layer along the seams: single strands over the slot, 41 mm long on the cabins and up to
  193 mm on the garages, every slice. Modifiers on that one layer, setting the bridge direction
  straight across each seam, fixed it. A modifier on one layer also makes Flash Studio shift a
  little hidden infill on a few other layers of that part; nothing that shows.
- **A bridge direction of 0 means "pick it yourself"** to Flash Studio, however it's written
  (`0`, `0.0`). A modifier must set a real angle, and a check must compare it with the planned
  number. Flash Studio also uses a modifier's real shape, not the box around it.
- To find long bridges without printing, read the G-code: measure how much of each "Bridge" line
  has nothing under it on the layer below. Slice three or more times, because the direction can
  change between runs. The command line's G-code isn't byte-identical run to run either (loops
  start in different places), so compare runs by how much each part extrudes per layer, not by
  the text. All four 10x20 and 12x24 models now have no bridge over 20 mm on any plate.

### Two colours on the IFS
- **Put the second colour on the top layers only.** Every layer that has both colours costs
  a filament change (time plus purge). Raised trim on a part printed flat costs one change if
  nothing in the first colour reaches the trim layers, otherwise one per trim layer (3 for
  0.6 mm); the same trim standing up the side of a part costs one per layer. The shed walls went from
  25–28 changes a plate to 1–3 by mitring the corners so every wall's trim is on top
  (Alan, Nov 2026). The barn's white gable vent stood out past the siding into the trim layers
  and cost the end-wall plate 3 changes; sunk flush with the siding, it costs 1 (Nov 3 2026).
- A change happens on every layer that has both colours. Something tall in the second colour
  (a handle, a knob) only adds changes while the first colour is still printing on those
  layers; above the last of the first colour it is free.
- **A `.3mf` made by a script must carry Flash Studio's project settings**
  (`Metadata/project_settings.config`, taken from a project Flash Studio saved) and both version
  tags (`Application` BambuStudio-02.06.00.51 and `OrcaSlicer` 2.4.2). Without them Flash Studio
  opens it as a plain model: it moves the whole layout so its middle sits on plate 1 (parts end
  up off their plates) and puts every part on filament 1. A setting changed from the stock
  preset (Arachne) only sticks if `different_settings_to_system` names it, as Flash Studio saves
  it: `["wall_generator", "", "", "", ""]` (the process, then each filament, then the printer).
  The shed and barn folders keep these settings in `flash studio settings.json` (Alan, Nov 2026).
- **Open a project from inside Flash Studio** (File → Open Project, or Open Project on its Home
  page). Starting Flash Studio with a project file, while other Flash Studio windows were open,
  stuck at about two-thirds of "Loading" with one CPU core busy, even for a file Flash Studio had
  saved itself (Nov 2026).
- **Check the slots in the Send dialog every time.** Flash Studio matches each filament to the
  slot whose colour on the printer is closest, and the printer still has the old colours, so it
  put white on slot 2 and black on slot 1. Click each filament's slot box and pick the slot by
  number: 1 white, 2 black, 3 brown. After Send, a red "No Flashforge-AD5X idle printer" note
  can appear: that only means the printer is now busy with the job, and the Device tab shows
  it printing (Nov 2 2026).

### Models of Yoder buildings
- **Take the layout from the live site, and the sizes from its 3D builder** (Nov 3 2026). The
  design page on yoder-storage-barns.com loads Alan's own `designer-standards.js`, which puts
  each building's doors, windows and porch posts where he puts them. The local Barnwright
  designer copy still has the older stock layout, and the first four cabin and garage models
  had to be moved. The building pages' text gives other door sizes (7 x 9 ft roll-up, 36 x 80 in
  doors); Alan chose the builder's ("Keep builder sizes"): 8 x 6.4 ft roll-up, 3 x 6.3 ft doors.
- **Alan's answers carry over to the next model** (Nov 4 2026): a gable-roof cabin gets his
  93 1/2 in utility wall (89 in studs and three plates), not the designer's 88.8 in, and his 5/12
  roof with a 4 in level eave, not the designer's 6.48/12; the cabins' 11-lite door hinges on the
  right as seen from the porch, next to the side wall, and swings in; a 12-wide is modelled at its
  actual 134 in. A lofted barn cabin gets his 79 1/2 in lofted wall (75 in studs and three
  plates), not the designer's 82.8 in. That leaves no room over the builder's 75.6 in door for
  any header, so Alan chose a 73 1/2 in door under his two flat 2x4s: 72 in king studs, with
  the header right under the top plates. The Lofted Barn Garage still has 82.8 in walls.
- **Twin models share parts: change them in both** (Nov 4 2026). The 12x24 Garage and Lofted
  Barn Garage have the same lift-out roll-up door. Fixed separately, the two drifted apart within
  a day (different pads, stops and checks). Make a change to a shared part in both folders, then
  prove the two doors are the same solid.
- **The garage checkers are slow**: about 4 minutes for the Garage and 11 for the Lofted Barn
  Garage, each on a full core. Many of them running at once filled all 8 cores and made the work
  look stalled, so run one or two at a time.
- **A "rests on it" proof must drop the part far less than a layer** (cabin checkers, Nov 4
  2026). The Cabin checker lowered a roof half 0.3 mm and called any overlap "rests on it".
  That passed a gable standing 0.25 mm low everywhere except at its peak. The checker now
  lowers it 0.02 mm and needs contact in every 1 mm along the slope. The same weak test was
  fixed in one group and left in another, which still printed a false ok when that group ran
  on its own. So when you make a proof stronger, search the checker (and its twin) for every
  copy of it.
- **To change a door's hinge side, mirror the door; don't turn it** (cabins, Nov 4 2026).
  Turning it puts the knob and muntins on the wrong face. Mirror it in its print position, swing
  it the other way, and prove the new hand by measuring the pins, holes, knob and stop off the
  parts. A moved pin can also land beside a floor sheet seam.
- **After a pitch or wall-height change, work the checker's numbers out from the new values**
  (Cabin, Nov 4 2026). A bevel line written in as 47.34 would have proven nothing once the
  roof went to 5/12 (it moved to 47.265). A flatter roof also dropped an end stud from the short
  porch gable, so look at the gable framing again.
- **Lowering a wall more than its door can push trim into the porch** (Lofted Barn Cabin, Nov 4
  2026). The door's head casing rose 1.1 in above the porch frame's bottom, behind its back beam.
  After a height change, check every casing against the porch frame and ceiling.
- **The designer draws the 11-lite door from its height** (`door-lite.js`): the glass starts
  at 0.42 of the height, the arch's top sits 0.55 ft under the head, and the knob is at 0.44 of
  the height. So a shorter door gets shorter glass and a lower knob, not the same lites moved
  down. Give the door function a height, and twins of different heights can be proven the same
  door through it.
- **Type a held size into the checker; don't read it from the generator** (cabins, Nov 4
  2026). The read mes turn the 1.6 mm bottom plate into a 2 in plate and the studs into 88 1/2
  in (Cabin) or 74 1/2 in (Lofted Barn Cabin). Checked against the generator's own number, a
  1.8 mm plate passed while those inch figures were wrong. The same goes for tolerances: set a
  "same solid" limit from the measured difference (about 0.0000003 mm3 here), not a guessed
  0.1 mm3, which let a knob 0.08 mm taller pass.
- **Git Bash's `sed -i` turns a CRLF file into LF.** Edit CRLF files with the Edit tool or with
  Python working on bytes.

### Spring toys (spring knife design reviews, Nov 7-8 2026; not printed yet)
- **Don't let two stretched bands fight each other.** A plan with two preloaded TPU bands
  pulling opposite ways stalled half way in the model. TPU loses energy in proportion to how
  hard each band pulls, and roller friction does too, so the losses swamped the small
  difference that moves the blade. Let one band work at a time, and leave it just taut at rest.
- **Take a latch's knock in a separate block, not in its spring arm.** A 1.6 mm PLA arm with
  the tooth on it can't take a blade landing at 3 m/s. A loose block in a slot carries the
  load into the carrier; the arm only pushes it out. Cushion the bounce-back on TPU.
- **A trailing corner can catch on the edge it just left.** A block that leans in its slot as
  it leaves a window can hit the end of the next wall. Chamfer its corners more than it can lean.
- **A part pushed off its line of pull twists against its walls.** The knob's riser pushes a
  sled 13.45 mm out from the band's line, so the sled turns until two corners bear on the
  walls, and they rub. That made the thumb push 1.5 to 1.9 times what the band alone needs.
  A longer part cuts it: the sleds went from 15 to 22 mm long. Count the twist in the force.
- **Don't let a latch rub the whole way.** The spring arm pressing the latch block on an 82 mm
  rail was most of the friction the blade had to coast through, so the band, and the thumb,
  had to be stronger. Now the block rides a short catch at each end and floats out, barely
  touching, in between; a 30 degree ramp brings it back in at the far catch.
- **The hardest knock is a knob let go just before the trip.** The band throws the light
  knob slider back with all its energy, and it lands through a riser on a sled, plastic on
  plastic. Make the part it hits as long as the riser (the sleds' wings went from 6 to 14 mm),
  stop it on TPU, and check the bar it runs on, not only the parts that touch.
- **Gaps inside one part need 0.45 to 0.5 mm.** The latch arm's 0.3 mm gaps are the brain's
  sliding fit, but that is for two separate parts. Inside one print a strand or a smear can
  weld the arm solid. Print a latch test with the fit test.
- **Two parts that slide on each other must not both print their first layer there.** The
  latch block and its slot both started on the bed at the same height, and each first layer
  spreads about 0.1, leaving 0.05 of play. Set the first layer back 0.15 on both.
- **Press TPU pads into pockets.** A pad lying loose in a long room can drift where nothing
  pushes it home, and then the blade lands on plastic.

### Bed adhesion
- Long, thin parts or parts with a small footprint need a **5 mm brim** (knife handle, sword
  blade, star board).
- Tall thin parts: keep the bottom few layers solid so the part has something to hold the bed with.

---

## Project index

| Folder | What's in it | Notes |
|---|---|---|
| `collapsible blade/` | Telescoping sword: blade, handle, cap | Read `blade strength notes.md`, `PETG blade - read before printing.md`, `tip rework notes.md` |
| `knife/` | OTF fidget knife, sheath, TPU blade | `read me first.md`, `OTF knife - PLA+ print guide.md`. Model licence CC BY-NC-SA: OK to print, not to sell. |
| `new prints/star reward board/` | Kids' star reward board, v1–v4 | v4 (7 × 2, 0.3 mm slots) is the current one and uses the v3 stars |
| `new prints/` | Voronoi vase, eclipse bloom vase, army men | PLA / matte / silk versions |
| `3d print guns/` | Toy shooters: toothpick, rubber band, disc | |
| `calpalt/` | Macshay catapult | |
| `tiny book/` | Tiny book covers and pages (sets of 20) | |
| `paw key chain/` | Animal paw key chains (sets of 20) | 2-colour |
| `snake and d/` | Articulated snake, dragon egg fidget | Biggest jobs: 4 dragon eggs ≈ 24 h |
| `flying prop/` | Flying propeller toy | |
| `test print/` | Sword blade PLA vs PETG tests | |
| `desktop prints/` | Project files (.3mf) and big STLs | The 4 biggest STLs are stored with Git LFS |
| `shed model 8x12 side utility/` | 1:24 model of the 8x12 Side Utility: floor, four mitred walls that snap onto the floor and print flat with two-colour trim, black corner angles glued over the corners, two lift-off roof halves, opening door, skids | Read `read me first.md`. Print `1 fit test.3mf` first (plate 1 is the new corner), then the five plates in `2 all plates.3mf`. Made by `make_shed.py`; `check_shed.py` proves the parts fit, snap together and print flat, also layer by layer as sliced |
| `shed model 8x12 side lofted barn/` | 1:24 model of the 8x12 Side Lofted Barn, built from the Side Utility model with the same snap joints and glued black corner angles: floor, four mitred walls with your loft framing, two lofts, a barn roof in four lift-off sheets, opening door, skids | Read `read me first.md`. Print `1 fit test.3mf` first, then the five plates in `2 all plates.3mf`. Long walls go on first, then the lofts, end walls last. Made by `make_barn.py`; `check_barn.py` proves the parts fit, snap together and print flat; `draw_barn.py` draws the assembly picture |
| `shed model 10x20 cabin/` | 1:32 model of the 10x20 Cabin in Alan's standard layout (door right of the middle with one window left of it, a window on each long wall, one middle porch post with the railing under the window), built on the shed's snap joints with Alan's 93 1/2 in walls and 5/12 roof (4 in level eave): floor with a front porch deck, four walls that snap onto the floor (glued butt joints at the front corners, black corner angles over the back ones), in-swing door hinged on the right, porch posts, railings, black porch frame, white ceiling, porch gable, two lift-off roof halves, two skids | Read `read me first.md`. Print `1 fit test.3mf` first, then the four plates in `2 all plates.3mf` (about 7 1/2 h). Made by `make_cabin.py`; `check_cabin.py` proves the parts fit, snap together and print flat; `draw_cabin.py` draws the assembly picture |
| `shed model 10x20 lofted barn cabin/` | 1:32 model of the 10x20 Lofted Barn Cabin: the cabin's floor, porch, snap walls, in-swing door and standard layout, with Alan's 79 1/2 in lofted walls and a 73 1/2 in door under two flat 2x4s, with the faux loft window in the porch gable (the octagon is an option), front and back lofts and a barn roof in four lift-off sheets | Read `read me first.md`. Print `1 fit test.3mf` first, then the four plates in `2 all plates.3mf` (about 8 1/3 h). Lift the front loft out before gluing the front corners. Made by `make_barn_cabin.py`; `check_barn_cabin.py` proves the parts fit and print flat; `draw_barn_cabin.py` draws the assembly picture |
| `shed model 12x24 garage/` | 1:36 model of the 12x24 Garage in Alan's standard layout (8 x 6.4 ft roll-up centred in one end; on the right-hand side, the steel door 4 ft in from the roll-up corner and a window halfway between it and the back), built on the shed's snap joints: floor, four walls that snap onto the floor, black corner angles glued over the corners, a lift-out roll-up door with a black handle at its bottom middle, in-swing steel door, two lift-off roof halves, four skids | Read `read me first.md`. Print `1 fit test.3mf` first (plate 1 is half the roll-up door in half its doorway, to practise putting it in and taking it out), then the four plates in `2 all plates.3mf` (about 7 1/2 h). The roll-up door goes in last. To take it out: lift it by its handle until it stops (about a millimetre), let it down a hair, pull the bottom toward you and let it drop. Made by `make_garage.py`; `check_garage.py` proves the parts fit, the door's springs hold it and it comes out; `draw_garage.py` draws the assembly picture |
| `shed model 12x24 lofted barn garage/` | 1:36 model of the 12x24 Lofted Barn Garage: the Garage's floor, snap walls, standard layout and lift-out roll-up door, with a faux loft window in the gable over the roll-up, a 4 ft loft at each end and a barn roof in four lift-off sheets | Read `read me first.md`. Print `1 fit test.3mf` first, then the four plates in `2 all plates.3mf` (about 8 1/2 h). The roll-up door goes in and comes out the same way as on the Garage, roof on or off. Made by `make_barn_garage.py`; `check_barn_garage.py` proves the parts fit and the door works; `draw_barn_garage.py` draws the assembly picture |
| `spring knife/` | Double-action spring knife fidget toy designed from scratch (Nov 2026) to replace the one from the Flashforge app. Push the side knob 28 mm (about 16 N) and the blade snaps 86 mm out and locks; pull it back and it snaps in. One TPU band runs between two sleds that rest on the knob bar's risers, so at rest it pulls on nothing; a cam lets the latch block go, the band throws the blade and it coasts the rest of the way onto a TPU pad. The latch block catches on a short catch at each end of a rail that floats between two TPU cushions, and floats out, barely rubbing, in between. Three black handle plates held by printed screws and captive printed nuts. Blunt, round-tipped toy | Read `read me first.md`. Print `1 fit test.3mf` first (a screw and three nuts, and a latch test), then the three plates in `2 knife plates.3mf` and `3 TPU parts.3mf` (TPU in slot 4); nothing to buy. Made by `make_knife.py`; `check_knife.py` walks a whole cycle, models a throw from the real parts over a range of TPU, friction and print weight, held flat or pointing up, works out the thumb force and every knock, and proves the screws mesh, nothing hangs in the air, no wall is under two lines and every flat face sits on a layer line |
| Top level | Piggy banks, mushrooms, Mandalorian helmet, Connect 4, latches, iPhone case, vase | |

**File naming:** Orca names sliced files `name_FILAMENT_time.gcode.3mf`. A file ending in
`.gcode.3mf` is sliced and ready to send to the printer. A plain `.3mf` is a project file
you open in Orca to edit.

---

## Print log

Add a line after each print worth remembering, good or bad.

| Date | Print | Filament | Result / what to change next time |
|---|---|---|---|
| 2026-11-03 | Shed model 8x12 side lofted barn, first set of walls | PLA white + black | The little corner hooks snapped and held nothing, and a hairline gap showed at the corners. Redesigned both shed models: black L corner angles glued into 2-layer recesses, and a gable vent sunk flush (end-wall plate down from 3 colour changes to 1). For the walls already printed: `3 corner caps for printed walls.3mf`. Print the new fit test's plate 1 first. |

---

## How this folder works

- This folder lives at `Documents\3D Prints` and is backed up to GitHub:
  https://github.com/alanyoder-04261992/3d-printer (**public**).
- To save changes: open **GitHub Desktop**, type a summary, click **Commit to main**, then
  **Push origin**.
- Files over 100 MB must go through Git LFS. Ask Claude to set that up before committing one.
- The flash drive (E:) is a separate copy. New prints saved there need copying into this folder.
