# Printer Brain

Everything about our 3D printing setup in one place: the printer, the slicer, the
filament, the settings that work, and what we've learned the hard way.
**Keep it up to date** — when something changes or a print teaches us something, add it here.

_Last updated: 2026-11-11_

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
  about 1.8 % strain going in (keep it under 2 % for PLA: a snap fit only bends a few times; a part
  that flexes on every use needs far less, see Spring toys). Put each size on a layer line
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
- **Mark gauge pieces by cutting off whole corners** (spring knife gauge nuts, Nov 8 2026). Notches
  drawn for a hex nut's flat landed on a corner: two of the three came out as faint nicks, so the
  nuts couldn't be told apart, and the clear one left 0.37 mm over the thread. Cut off 1, 2 or 3
  alternate corners, 0.6 mm deep: each leaves a 2.1 mm flat you can count and 0.9 mm of wall. And
  word the read me's choice by how many fit, not only by the marks.
- **A post in a pocket is a peg in a hole: 0.35-0.4 all round** (spring knife, Nov 8 2026). Make
  both round when a hex with that room would leave under two lines, and measure the pocket's wall
  on every layer: the knife's middle plate had a cavity running under its rear screws, so a 9.9 mm
  pocket left 0.75 there and 9.7 (with an 8.9 post) leaves 0.85.

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
- **Check where a modifier is, not only how big it is** (spring knife, Nov 9 2026). A check that
  compared a bridge modifier's size with the bridge still passed with the modifier moved 21 mm off
  it. Compare its corners with the bridge itself, read off the part's first layer that hangs.
- **A bridge whose edge is cut back in plan leaves strands held at one end** (spring knife, Nov 10
  2026). The knife's carriage roof bridges a 1.9 mm channel, and its ends are cut back in a curve.
  Where that curve crosses the middle of the channel, each bridge line ends in mid-air: held at the
  leg only, 1.2 mm past what the layer below reaches. A strand like that droops. Measure it along
  the bridge's own direction: every line across what hangs must land on the layer below at both ends,
  or be short (0.4). The fix that suggests itself, cutting each layer back a little more than the
  one under it so the first layer reaches the far side, put thin layers where the part bends most
  and raised the stress there from 1.2 to 2.2 times; a square cut-back held at both ends, rounded
  into the leg, 1.6 to 2.1. Work the stress out on the shape the printer will make before choosing.
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

### Practical first (the first spring knife, printed Nov 11 2026)
- **A design that passes every check can still jam.** The first spring knife passed over 200 checks of stress, fatigue
  and knocks, and printed as a toy that wouldn't slide. The checks were about parts breaking; the print failed on
  rubbing and pinching. For a toy, check first that it moves: room round everything that slides, and how many
  surfaces rub at once. Don't worry much about breakage until it works (Alan).
- **Find where it binds by putting it together a step at a time.** Bare part, then each plate, then the screws, then
  the springs, tilting it at every step: the step where it stops sliding is the culprit. It took two minutes and found
  the cause that the checks had missed.
- **Never put a thin printed plate just over a sliding part.** The band's plate had a 0.65 mm floor 0.275 mm over the
  blade, and with it on the blade stuck. A thin plate full of cut-outs needn't print flat, and 0.275 leaves no room
  for that. Lay moving parts side by side in one layer under a solid lid instead, and give 0.45 mm at the sides and
  about 1 mm up and down.
- **A band only drives as far as the knob moves.** The rest of the blade's travel is a slide on its own, which any
  rubbing stops. Keep that slide short (the simple knife: 38 mm of push for 60 of travel), and keep anything springy
  off the blade except where it clicks in.
- **Parts that float in a lane lift when the toy is turned over.** Give them something to hold them down, such as
  dovetail keys in a floor channel with short gaps to drop them in, placed where no key is ever over a gap when the
  part is working.
- **A latch tooth needs its own slot to take the load.** A tooth on the end of a springy arm puts the band's pull
  along the arm and buckles it. Make the tooth a separate block in a slot; the arm only pushes it out.

### Spring toys (spring knife design reviews, Nov 7-10 2026; not printed yet)
- **Don't let two stretched bands fight each other.** A plan with two preloaded TPU bands
  pulling opposite ways stalled half way in the model. TPU loses energy in proportion to how
  hard each band pulls, and roller friction does too, so the losses swamped the small
  difference that moves the blade. Let one band work at a time, and leave it just taut at rest.
- **Take a latch's knock in a separate block, not in its spring arm.** A 1.6 mm PLA arm with
  the tooth on it can't take a blade landing at 3 m/s. A loose block in a slot carries the
  load into the carrier; the arm only pushes it out. Cushion the bounce-back on TPU.
- **A trailing corner can catch on the edge it just left.** A block that leans in its slot as
  it leaves a window can hit the end of the next wall. Chamfer its corners more than it can lean,
  and count the lean where the block sits furthest out of its slot: following the knob's bar out
  to the end of its 0.25 mm of play, a 5.65 mm deep block leaned 0.73 mm, past its 0.6 chamfers;
  6.45 deep it leans 0.53.
- **A part pushed off its line of pull twists against its walls.** The knob's riser pushes a
  sled 13.45 mm out from the band's line, so the sled turns until two corners bear on the
  walls, and they rub. That made the thumb push 1.5 to 1.9 times what the band alone needs.
  A longer part cuts it: the sleds went from 15 to 22 mm long. Count the twist in the force.
- **Don't let a latch rub the whole way.** The spring arm pressing the latch block on an 82 mm
  rail was most of the friction the blade had to coast through, so the band, and the thumb,
  had to be stronger. Now the block rides a short catch at each end and floats out, barely
  touching, in between; a 22 degree ramp brings it back in at the far catch.
- **A knob let go just before the trip is thrown back hard.** The band throws the light knob
  slider back with all its energy (up to 86 mJ), and it lands through a riser on a sled. Make
  the part it hits as long as the riser (the sleds' wings went from 6 to 14 mm), stop it on TPU,
  and check the bar it runs on, not only the parts that touch.
- **Gaps inside one part need 0.45 to 0.5 mm.** The latch arm's 0.3 mm gaps are the brain's
  sliding fit, but that is for two separate parts. Inside one print a strand or a smear can
  weld the arm solid. Print a latch test with the fit test.
- **Two parts that slide on each other must not both print their first layer there.** The
  latch block and its slot both started on the bed at the same height, and each first layer
  spreads about 0.1, leaving 0.05 of play. Set the first layer back 0.15 on both.
- **Press TPU pads, cushions and stops into pockets.** A pad lying loose in a long room, or a
  cushion in a groove that is open above, can drift or fall out where nothing pushes it home, and
  then the blade lands on plastic. Narrow the pocket 0.05 to 0.1 a side over part of the TPU's
  length. A TPU stop that stands out in the open needs more than grip: give it a T at its foot
  that drops into a T-slot, with the next plate over the slot, so it can't come out at all.
- **A nut trapped between plates can't clamp the plate above it.** Screwing up from the base
  plate into a nut that sits on the base plate clamps only the base plate: the top plate lifted
  straight off. Thread the far plate itself: posts printed on the top plate reach down through
  the middle plate, and the screws pull all three together. Prove it by lifting each plate 1 mm
  in the checker and finding the screws.
- **Joining two slots can free a long thin strip.** Longer risers merged their two slots in the
  middle plate's floor and left a 105 mm strip of floor held only at its ends. Leave a web.
- **Count the thumb pushing on after the trip.** The band keeps working while the thumb pushes
  the knob on to its end: up to a third more energy, so the knocks are harder than the throw
  alone says.
- **Put TPU where a part lands every cycle, but not where it must carry a slow squeeze.** A cap
  on each riser softens the sled landing on it, but a 2 x 2.35 mm TPU face can't also carry the
  knob's whole landing at a sane strain.
- **A knob that keeps going after the trip lands hard on every throw: give it its own TPU stop.**
  The thumb drives it on at up to 4.3 m/s, still pushing 32 N; landing through a riser's cap,
  that squashed the cap past half.
- **A part the thumb drives must end its stroke on a stop at the height of the thumb's push**, or
  the thumb's knock bends whatever carries it. The thumb is the heaviest thing that lands: about
  10 g of thumb follows the 1.9 g knob slider on to its stop. A TPU bumper at each end of the
  bar's lane stopped the bar square on, but on its own line, 2.6 mm under the thumb's
  push and at the far end of the bar, so the thumb's push and weight ran down the bar and bent it
  just in front of the knob: 50 MPa against 20. Now a TPU block at each end of the knob's travel,
  standing outside the handle against a guard, meets the knob's own end face 0.4 mm under the
  thumb's line, 0.1 mm before its sled meets its pad, and the bumpers are gone: the bar takes 15.4
  MPa with the thumb held stiff, 12.1 on a soft thumb (Nov 9 2026). Check the lips the thumb
  pushes too (the knob's lips went from 2 to 2.5 mm long: 15.3 MPa).
- **A stop's push twists whatever joins it to the part it moves.** The knob stop pushes the knob
  2.2 mm above the stem that joins the knob to its bar, so a let-go knob, with nothing but the
  stop behind it, twists the stem: 12.1 MPa across its layers at its ends, over the 12 a layer
  takes. The stem made as tall as the bar, and the stop's middle a little lower and its TPU a
  little longer (softer), brought it to 9.8.
- **Count a TPU cap as TPU in a stiffness model, not as the plastic it sits on.** The checker
  took a whole 12.7 mm riser as stiff PLA, but 4.9 mm of it was the TPU cap, so the bar came out
  too stiff and its worst stress in the wrong place. Stiffen only the PLA.
- **A TPU cap's fin needs a full-width foot.** The cap's push comes into a 0.8 mm PLA fin, and as
  the riser tips it pulls the fin's first layer off the bar: 22-25 MPa on a hard landing, where a
  printed layer takes about 12. A foot as wide as the riser, 1 mm tall, under the fin puts that
  pull on the foot's wide root: 3 to 10 MPa now on the sleds' landings. A low sole run on from the
  foot right out to the riser's face, under the cap's front block, makes a knock bend the bar at
  the riser's face instead of 2.5 mm in under the cap (the let-go landing: 25.0 MPa, was 29.1, of
  30), but a stiffer front puts a little more on the fin's root (11.2 against 9.7, of 12). Running
  the foot's full height on, or a 45 degree ramp up to the fin, was worse there (13.1, 12.8).
- **Check what slides past a pressed-on TPU part.** A riser cap rubbed past the latched block's
  top on every stroke, with more drag than its grip, so it could work its way off. Set it back
  0.3 mm where the block passes, or stand it higher: the caps now stand on the risers' soles and
  feet, wholly above the block's top.
- **Count every plastic-on-plastic knock, even small ones.** The read me said none were left,
  but the lug picking up the parked sled and the latch block meeting the rail's end still were.
  A sudden stop puts about 2 MPa per m/s into PLA's struck face, so these light parts at 3 to
  4 m/s see 7 to 8 MPa: fine, but now proven.
- **Check a latch block that pops out as a moving part.** It bounces off what stops it, and while
  the pad stops the blade the carrier presses it on its slot's wall, so friction holds it back
  against its arm: the plain sum said it bit 0.85 mm, a step-by-step model 0.09 to 0.29 at worst.
  Set 0.3 mm further out, it bit 0.49; with the stiffer, evenly bending arm (below) it bites 0.56,
  0.60 with the flatter band, over the 0.45 needed.
- **A solver in a checker must say when it doesn't settle.** The rail's old contact loop never
  settled above about 20 N and printed whatever it tried last: a believable 17-23 MPa, or 118 at
  30 N. Put the load on in steps, solve each until what's left over is tiny, and FAIL any step
  that doesn't get there.
- **Run a catch into its spine with a long taper, not a square step.** A rail pushed on one
  side of its length bends at any step; the square step put 31-40 MPa in it on every bounce,
  an 8 mm taper and a wider middle brought a normal bounce down to 17 (the hardest is 24,
  under its 30).
- **A PLA part that flexes on every cycle must stay under about 0.65 % strain at its root to last
  thousands of cycles.** The 2 % for snap fits is for one that bends a few times. Printed PLA
  bent back and forth lasts about 10,000 cycles at about 20 MPa, 0.65 % at 3 GPa (Ezeh and
  Susmel). The knife's latch arm bends twice a stroke (the cam pushes it in, the far ramp kicks
  it) and a plain 0.95 mm arm reached 0.99 % at its root: a few thousand strokes at most. Shape
  it to bend evenly instead: thin at its free end (0.85, still two lines), thickening toward the
  root as a beam of even strength does (thickness squared in step with the bending), then a
  smooth 3 mm flare into big round ends (1 mm radius), so the stress raiser at the root sees
  less than the arm does. The same length then bends 0.53 % and is stiffer (0.145 N/mm). Less
  preload (0.3 mm, still above the bar's play) with a stiffer arm presses less where the block
  only rubs, and throws it out just as hard where it has to bite. Hold everything else that
  bends on every throw to the same limit, 19.5 MPa (Nov 9 2026). That is the median life at
  10,000 cycles (half crack by then), a pass line rather than a safe value: aim for 15.
- **A thumb pressing a knob sideways moves its cam.** The knob's bar can go 0.3 mm in, until its
  risers meet their slots, and the cam on it then lets the blade go 0.8 mm of push earlier, with
  less in the band. Count the bar's play both ways in the let-go, and the throw from the earliest.
- **Count the weight once when the toy is tilted.** Tilted up from flat, the weight pulls back
  along the channel (sine) and presses a wall (cosine, rubbing mu of it). The worst tilt gives
  the square root of 1 + mu squared of the weight (1.08 at mu 0.4), not 1 + mu (1.4): held
  straight up, nothing presses the floor.
- **Pick a TPU band by hanging a known weight on it.** TPU's stiffness varies so much from brand to
  brand (10 to 30 MPa in the knife's sums) that one band can't suit them all: too soft, the blade
  stops short; too stiff, the knob is too hard to push. Hang the band from a full half-litre bottle of
  water (4.9 N) and measure the stretch: the knife's normal band stretches 40 mm in 15 MPa TPU, 30
  in 20 and 23 in 26. Work the stretch out from the same band model the throw uses, set the
  limits so a reading 1 mm out still fits a band that works, and print spare bands with the first.
- **Fit a spring band with more stretch for a flatter pull.** The throw needs a set energy over a
  set stroke; the thumb feels the band's pull at the end of the push. A band fitted further over
  its printed length, and softer to match, stores the same energy with less pull at the end: the
  knife's band went from 5 to 12.5 mm over (and 1.05 x 0.95 to 0.85 x 0.85) and pulls 0.85 of what
  it did at the trip, with the same throw margin. The limit is how far it stretches fully cocked
  (45 %): moving the band's posts 6.5 mm further apart on the sleds made the band 13 mm longer.
- **Put the big stretch in TPU, not in a PLA spring.** A printed PLA clock spring held to the
  0.65 % it survives stores about 0.02 mJ per mm3; the knife's TPU band, stretched 44 %, stores
  1.0 to 2.9 (10 to 30 MPa TPU): 46 to 138 times as much. Use PLA springs only for small pushes,
  like the latch arm.
- **A knob on the side pushes off its bar's line: check the bar bending sideways too.** The knife's
  thumb pushes 8 mm out from the 3.35 mm bar it drives, and the knob's slot takes away the lane
  wall beside the bar for 48.5 mm. A sliding fit (0.25-0.3 a side) lets the short block of knob
  and riser turn until its guides take it, and the bar bends to follow: 24 MPa at its corner on
  an ordinary push, up to 45 on a hard push or a landing, against 20 (Nov 9 2026). What fixed it:
  a long stiff carriage that takes the turn itself, guided on BOTH sides over its whole length on
  one plate (a rib left standing in the slot, 0.25 a side); the plain bar either side of it left
  free to follow (0.5 to the rib), with enough of it before the next guide (13.6 mm to riser F's
  slot: over 9.6 a hard landing bent it 20.8 MPa, over 13.6 17.3); and the thumb and the stops
  brought nearer the bar's line (a knob 1 mm thinner). Guides on two plates can pinch: the plates
  sit 0.35 apart at most (the pegs' play). And a push through a wide carriage bends it only by how
  far the push is from the carriage's own middle, not the bar's. A second review (Nov 9 2026) found
  the return push, never worked out, at 20 MPa, and the fit's loose end, the plates off and the
  carriage's square ends all made it worse: see the next lessons.
- **A stroke's return is not its mirror.** The knife's knob slider has riser B inside the carriage's
  front and riser F 13.6 mm behind it, and cam B at the far end, so the return push loads it quite
  differently from the push. The checker called it the push's mirror and never solved it, and it
  was the worst every-throw case (20.0 MPa against 19.5). Work out both directions, every knock too.
- **Draw a carriage off its rib's middle when a cam beyond it is held by a wall.** A push turns the
  knob's carriage in its play, and whichever end swings out drags the bar out after it until the
  lane's wall stops it at the cam beyond: the bar between bends to fit. With the carriage 0.15 from
  the rib on the bar's side (0.35 on the other, still 0.5 of sliding fit in all), its end stops 0.1
  before the bar meets the wall at the cam, and the return push fell to about 18 MPa. Check the
  slider doesn't pinch with the plates off: the risers' slots then push it out 0.1, so the pegs were
  tightened to 0.35 all round to leave 0.1 of play.
- **Prove a sliding fit at its loose end, and count the plates' play in every model.** The bar's
  sideways bending rose about 2.6 MPa for every 0.05 mm more play on the carriage, and the check had
  only looked at the drawn 0.25. And the up-and-down check counted the plates sitting 0.4 off across,
  but the sideways one didn't: with the middle plate off inward, riser F's slot held the bar 13.6 mm
  behind the carriage, 9 MPa became 21. Each tolerance at its worst belongs in the model.
- **A square step where a thin bar meets a wide block has no stress factor at all.** It is a sharp
  inside corner, so it never settles on one number however finely you work it out (on the knife a
  square end read 2.8 to 3.7 depending on the mesh), and a factor like 1.3 typed in for it is not
  safe. Give the joint
  a real fillet or a smooth widening (the knife's bar now widens over 6 mm into its carriage, and the
  roof's ends are cut back in a quarter-ellipse), and work its factor out from the real shape with a
  plan FE: each element as thick as the part is tall there. Check that FE against Peterson's stepped
  bar first, read the same way.
- **Check a model against the chart's own fit, not a value read off a small chart.** Peterson's
  stepped flat bar in bending, D/d 2, r/d 0.1, is 1.95 by Pilkey's fit (Roark's Formulas, Table
  6-1); a reading of 1.7 off an older chart made a sound FE look 9 % high. A plan FE that reads the
  stress in the elements just inside the edge reads low on a coarse mesh and climbs as it gets
  finer (1.75, 1.86, 1.92 at 0.025, 0.0167, 0.0125): take the finer mesh pushed on by its last rise
  (1.96), and never the coarse mesh alone.
- **Locate a floating plate with a D-shaped peg hole.** Round peg holes have to be 0.35 bigger all
  round (holes print small), so a plate can sit 0.35 off either way. On the knife, the middle plate
  sitting 0.35 toward the blade let riser F's slot push the knob's bar in: 20.6 MPa on a hard push,
  32.5 on a let-go knob. Give each hole a flat on the side the harm comes from, drawn 0.05 into its
  peg: pressed on, the plate slides 0.05 the other way and can't sit off toward the harm at all.
  But the flat shrinks with the rest of the hole, so a D-shaped hole goes on only if it prints at
  most 0.15 small all round, where a round one takes 0.35: give the test pieces' and the plates'
  holes the same room, and have a looser lid ready (Nov 10 2026). Set the plate's first layer back
  at the flat, make the peg's lead-in a slope, not a step (a 0.2 step left the plates sitting
  0.55 to 0.8 mm high until nudged over), and print a peg test with the fit test whose peg prints
  in layers as short as the knife's own pegs.
- **More room at a guide moves the contact; it doesn't remove it.** Giving riser F more room in its
  slot to stop it holding the knob's bar moved the push to the carriage's foot, and the plain bar
  went from 19 to 24 MPa. Find what really turns the part and take that down instead.
- **Read the bending in z at a junction on each element's own section.** Where the knob's bar runs
  into its carriage, the check added the bar's bending up and down from plain-bar elements only and
  missed some of it: on the let-go knob 28.4 became 28.8 once each element's own section was read.
  Read it on the section that is really there, and add the carriage's own bending to its roof's term.
- **Count a force the same way in every check of the same push** (spring knife, Nov 10 2026). The
  thumb check counted the thumb pressing the knob into the handle (0.3 of its push), but the stress
  checks of that same push left it out and passed the return push at 14 MPa. Counted, it is 21 to
  24 against 19.5. When one check finds a force, search every other check of that push for it.
- **When the thumb and a stop squeeze a knob, the gap between their lines turns it.** In a landing
  with the thumb held stiff behind the knob, the thumb and the stop push it from either end with
  about the same force, so what turns it is that force times the distance between the two lines.
  Keep the lines close: the knife's knob is 0.5 thinner now (the thumb 0.5 nearer the bar, the stop
  0.25), which took the hardest landing from 22.3 to 18.2 MPa; a stop shortened to keep its E A /
  L where it meets less of the knob stays as stiff (a softer stop made it worse).
- **Count the guides' rubbing in the push force.** Whatever holds a part straight against a turning
  push is pressed by that turn, and the part slides along it: mu times each push. On the knife the
  rib, the lane's wall and the risers' slots rub 0.6 to 3.9 N of the thumb's push (12 % at the
  worst friction), and leaving that out had hidden a thumb force over the limit. Work it out with
  the same model that finds the turn, until it settles, and put it in the force every check uses.
- **Crown a sliding guide's ends, gently.** A carriage that tilts in its play bears on its guide with
  an end corner, a line of contact that wears and digs in. Round each guide face off at its ends in
  plan: it then bears like a rounded edge, where the crown's slope matches the carriage's turn (R x
  the turn in from where the crown starts: keep that, with the contact's half-width, inside the
  crown's lead, and the turn under half its end slope). Hertz's line contact, p = sqrt(q E / (2 pi
  (1 - nu^2) R)), q the push per mm of height, goes down with a flatter crown: the knife's went from
  0.1 over 2 mm (R 20) to 0.065 over 3.5 (R 94). Count only the height that really meets: a guide
  face's first layer set back doesn't, and the slider can lift. The knife's carriage meets its 1 mm
  tall rib over only 0.54 of its height as drawn (its guide faces start above their set-back first
  layer, and the bar sits 0.2 over its floor) and 0.19 lifted to the middle plate: 29.8 MPa with the
  old crown; with the flatter crown 15.0 on every throw and 18.8 on a let-go knob.
- **A stop that meets the knob on the thumb's own line stops the knob without turning it.** Every
  throw the thumb and the stop squeeze the knob between them, 170 N each way; 1.7 mm between their
  lines turned it 300 N mm. Cutting the knob's end back low down and on its inner part, so the stop
  meets only the outer part (0.7 mm from the thumb's line, at its height), cut that to under half. A
  shorter stop (3.5 instead of 5 mm) kept it stiff enough that the knob, not the riser's cap, still
  takes the landing. But a cut-back only works until the stop squashes that far: the knob's inner
  part, cut back 0.5, met the flat stop from 0.5 of squash, and the hard landings squash it 1.4. Cut
  the stop's own face back past the most it squashes, and the stops become a mirrored pair: key them
  (an off-centre T) so neither fits the wrong end. Leave two lines of the stop behind its recess:
  on the 2.65 stop of the thinner knob the recess is 1.71 (it was 2.15 on the 3.5 stop).
- **A TPU block pushed on part of its face is stiffer than E A / L.** Its unpushed part is dragged
  along: a plane-stress model of the knife's flat knob stop, pushed on 2.05 of its 3.9 width, gave
  1.23-1.39 times; with its unpushed part recessed, 1.06-1.12. Work the landings out over the range.
- **A TPU band held stretched loses pull.** The knife's band is fitted 12.5 mm (14 %) over its length
  for good, and TPU held stretched relaxes and takes a set, and softens the first few times it goes
  further than before. Stretch a band 10 times to about 1.5 times its length before a hang test, hang
  the band you fit too, and check an aged band (its rest pull x 0.8, its stiffness x 0.9) still does
  its job: the knife's still locks, with 0.02 N of friction to spare at the worst corner (0.11 fresh).
- **Count the thumb pressing a ridge in.** A thumb pushing a ridge 1 mm proud also presses the knob
  sideways, about 0.3 of its push, and the guides rub mu of that: on the knife about 1.5 N more.
- **With the thumb kept on the knob, the far cam swings in.** Held at the end of its travel, the
  thumb's push and the stop's turn the slider in its play, and the cam at its far end moved in 0.5 to
  0.6 over where the blade arrives, past the 0.45 of room drawn. Cut the carrier back there (0.75
  now), and check it with the carrier on the wall its latch arm presses it to.
- **Print TPU springs and pads solid if the sums take them as solid.** At the stock 15 % infill a
  2 mm TPU pad gets sparse layers inside and comes out about 11 % softer than worked out. Set
  Sparse infill density to 100 % on each TPU part.

### Bed adhesion
- Long, thin parts or parts with a small footprint need a **5 mm brim** (knife handle, sword
  blade, star board).
- Tall thin parts: keep the bottom few layers solid so the part has something to hold the bed with.
- **A brim fills the gap between two islands of one part.** An outer-only brim skips holes, but a
  gap between two islands of the first layer is outside, so the brim is laid in it. The spring
  knife's knob slider has a 2.2 mm groove under its roof for a rib to run in, so its first layer
  is two strips; a 5 mm brim would have put about 75 mm2 of brim in the groove, under the roof,
  where it can't be peeled out. A part whose first layer has a groove under a roof gets no brim
  (Nov 9 2026).

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
| `spring knife/` | The first double-action spring knife (Nov 2026): side knob, three plates, TPU band, caps, pads and stops. **Doesn't work: don't print it.** Printed Nov 11: the middle plate pinched the blade, and it stalled and wouldn't lock (see the Print log) | Kept as a record. Replaced by `spring knife simple/` |
| `spring knife simple/` | Double-action spring knife fidget toy, redrawn simply after the first one jammed (Nov 11 2026). Push the knob on top 38 mm and the blade snaps 59 mm out and locks; pull it back and it snaps in. Two plates (base and lid), three printed screws. Everything moves in one layer: the blade in a channel, kept straight by a rib in the floor; two sleds and one TPU band in a lane beside it; the knob's bar beside them with two risers and two cams. The latch block slides in a slot in the blade and clicks past a catch hanging from the lid at each end; nothing else springy touches the blade. 0.45 mm of room at every side, about 1 mm up and down. Dovetail keys under the sleds stop them lifting when held upside down. The band is the only TPU part: thin, normal and thick (1.2 mm wide, 1.05 to 1.45 thick). Not printed yet | Read `read me first.md`. Print `1 slide test.3mf` first: the back of the handle with two blade pieces (normal and loose) and a latch block; the blade should slide on its own when tilted and click when pushed home. Then `2 knife plates.3mf` and `3 bands TPU.3mf`. Made by `make_knife.py`; `check_knife.py` walks a whole cycle with every part at both ends of its play and finds no two parts touching, checks the latch holds by 0.95 mm and lets go before the knob's end, and checks every part prints in one piece on layer lines |
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
| 2026-11-11 | Spring knife (first design, test version) | PLA + TPU | Horrible. The blade wouldn't slide without tapping and wouldn't lock unless pushed home with a tool. The plate that holds the band pinched it (found by putting it together a step at a time). Redrawn from scratch as `spring knife simple`: no plate between the blade and the band, 0.45 mm of room, fewer rubbing parts, a longer knob push and a thicker band. Print its slide test first. |

---

## How this folder works

- This folder lives at `Documents\3D Prints` and is backed up to GitHub:
  https://github.com/alanyoder-04261992/3d-printer (**public**).
- To save changes: open **GitHub Desktop**, type a summary, click **Commit to main**, then
  **Push origin**.
- Files over 100 MB must go through Git LFS. Ask Claude to set that up before committing one.
- The flash drive (E:) is a separate copy. New prints saved there need copying into this folder.
