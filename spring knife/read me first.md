# Spring knife toy — read me first

> **Don't print this one: it jams (Nov 11 2026).** Alan printed it. The blade wouldn't slide without tapping and
> wouldn't lock unless pushed home with a tool. The middle plate, the one that holds the band, pinched the blade.
> It has been replaced by a simpler design in the **`spring knife simple`** folder. This folder stays as a record.

A double-action fidget toy designed from scratch (Nov 2026). Push the **knob** on the side
**forward** about 28 mm: near the end the blade snaps 86 mm out and locks. Pull it **back**:
near the end the blade snaps back in and locks. Every part is printed, the screws too:
nothing to buy.

It's a toy: the blade is 4 mm thick plastic with round edges and a round tip. It does come out
with a snap, so point it away from faces. Don't use the blade as a lever or press its tip into
a table: it's plastic.

**This is a test version (Nov 10).** You asked for something to print now, while the fixed
version is worked on. A review of the "third look" version below found these problems, and this
test version doesn't fix them yet. The fixed version will, and you'll most likely need to print
the knob slider and the three handle plates again for it. The screws, nuts, sleds, blade, latch
block and TPU parts may well carry over, but that isn't certain yet. In order of what matters for
this print:

1. **The pegs are a tight fit: test them before you print the rest of the knife.** The middle and
   top plates sit on two pegs each, through D-shaped holes. A D-shaped hole has less room than a
   round one: if it prints more than 0.15 mm small all round, the plate won't go on (a round hole
   would take 0.35).
   - Do the peg test in the fit test first ("Pegs", under "The fit test").
   - A pass doesn't promise the knife's own pegs. They print by themselves at the top of the base
     plate, in very short layers (under 2 seconds each, where the test's peg gets 10 to 14), so
     they can come out a little different. So print plate 1 of `2 knife plates.3mf` (the three
     handle plates) on its own first. Peel the brims and stack the three plates with nothing
     inside: the middle plate on the base plate's pegs, then the top plate on the middle plate's.
     Press each down while you nudge it toward the knob's side, as in steps 7 and 10.
   - If the peg test's lid, or either plate, won't go down flat by hand, stop and tell Claude
     before you print plates 2 to 4. Don't scrape or drill the holes bigger: opened on the wrong
     side, a hole lets the plate sit toward the blade, and that bends the knob's bar more.
2. **Closing the blade bends the knob slider harder than allowed.** When you pull the knob back,
   your thumb also presses it into the handle a little. The checks counted that press for how hard
   your thumb has to push, but left it out of how hard the knob's bar bends. Counted, the joint
   where the bar meets the back of the knob's carriage takes, on every close:
   - with a normal TPU (about 30 mm on the hang test), about 21 MPa, and 24 with the knob's fit at
     its loosest, against the 19.5 allowed for a part that bends on every push. By the same tests
     the 19.5 comes from, half of such bars would crack at that joint by about 3,000 to 8,000
     closes;
   - with the stiffest band the read me lets you fit (23 mm on the check of the band you fit) and
     the most rubbing the checks allow, 35, and 23 on the plain bar beside it. Half of such bars
     would crack within about 150 closes.

   Opening the blade is fine: counting the press, those numbers go down. So:
   - pull the knob back along the handle, pressing it into the handle as little as you can. That
     press is what bends the bar (this hasn't been worked out, but it can only help);
   - look at the knob's bar where it runs into the back of the knob now and then. White marks or a
     hairline there mean it's starting to crack;
   - if it cracks, print a new knob slider (plate 4 of `2 knife plates.3mf`), take the knife apart
     down to the base plate (steps 11 back to 4), move the two riser caps onto the new slider and
     put it back together.

   The knob landing on its stop with your thumb still pushing, the rib and riser B's sole haven't
   been rechecked with the press either. Apart from the return push row, the table under "How it
   was checked" shows the numbers without it.
3. **The knob carriage's roof.** Its first layer may droop a little into the groove at its curved
   ends: see "Not proven yet" below, and look at the fit test's carriage piece.
4. **Nudge each plate toward the knob's side as you press it on** (steps 7 and 10). Set straight
   down, a plate catches on a small step at the top of each peg and sits about half a millimetre
   high (the top plate nearly a millimetre). Nudged over, it drops. The flat side of each hole
   then keeps it from sitting toward the blade. The knife has no spare room that way (a plate even
   0.05 mm toward the blade bends the knob's bar more), so never scrape the holes.
5. **Ask Claude to slice the knob slider three times from the command line** (on your computer,
   with the command in the brain) before you print it, to see Flash Studio keeps its roof's bridge
   straight across the groove. Nobody has done that yet.

**New knob (Nov 9).** Your thumb pushes the knob out to the side of the bar it drives, so every
push tries to turn the knob flat in the handle, and the old 14 mm knob let its bar bend sideways
too much (about 24 MPa on an ordinary push, up to 45; a part that bends on every push should stay
under 19.5). Now:

- The knob is a 38 mm long carriage that rides a low rib in its slot, with a sliding fit on both
  sides, so it can hardly turn. The bar either side of it is free to follow the little it does.
- The knob is 1 mm thinner, so your thumb pushes 1 mm nearer the bar's line and turns it less.
- Your thumb sits in a saddle at the middle of the knob, between two ridges. Push on the front
  ridge, pull on the back one.
- The band is longer and thinner and is fitted with more stretch. It gives the blade the same
  throw with less pull at the end of the push, so your thumb pushes less.

**A second look (Nov 9).** A review found things the checks had missed, and this version fixes
most of them:

- Pulling the knob back is not a mirror of pushing it, and it had never been worked out: it bent
  the bar 20 MPa. The knob's carriage now sits off the middle of its rib (0.15 mm on the bar's
  side, 0.35 on the knob's, the same half millimetre of play in all), and the lane's wall behind
  the knob's slot is cut back 5 mm: now at most 17.8 as drawn, 19.0 with the carriage's fit
  printed 0.05 looser each side (that left out your thumb pressing the knob in: see the top).
- The pegs that line the plates up fit 0.35 mm all round (they were 0.4, the brain's rule is
  0.35 to 0.4; the holes are D-shaped now, see "A third look"), so the middle plate can't sit far enough off to pinch the knob's carriage.
- The knob stops' faces are cut back on their inner half, so the knob's inner part can't reach
  them however hard it lands. The two stops are now a mirrored pair (see step 3).
- The carrier is cut back a little more ahead of the latch block, so the far cam can't touch
  the blade arriving under it while your thumb is still on the knob.
- The knob slider and the fit test's carriage piece print with no brim (a brim would fill the
  groove under the carriage's roof).
- The band: stretch it 10 times before the hang test, and check the band you fit too.

**A third look (Nov 10).** The two things that were not proven are fixed:

- **The plates can't sit toward the blade any more.** The middle and top plates sit on two pegs
  each. Their holes were round, 0.35 mm bigger all round, so a plate could sit 0.35 mm off toward
  the blade, and then riser F's slot pushed the knob's bar in and bent it up to 20.6 MPa (32.5 on a
  let-go knob). Now each peg hole is D-shaped: a round hole with one flat side, on the knob's side,
  drawn 0.05 mm into the peg. Pressed on, a plate slides 0.05 mm toward the knob's side and can't
  sit the other way at all. Toward the knob's side it can still move about 0.3 mm, which does no
  harm. Steps 7 and 10 below say how to put the plates on, and the fit test has a peg test.
- **No square step where the bar meets the knob.** The bar used to step square into the knob's
  carriage. A square step like that has no fixed stress factor at all: it never settles on one number,
  however finely you work it out (the old check counted it as 1.3 times). Now the bar widens smoothly over its
  last 6 mm into the back of the carriage, and the carriage's roof is cut back at both ends in a
  rounded curve. A model of the real shape, checked against a textbook case (Peterson's stepped
  bar), puts what is left at 1.15 times at the back (the roof 1.22) and 1.18 at the front.
- **The knob is 0.5 mm thinner.** Its lips and ridges stand 3.7 mm out from the handle's side
  instead of 4.2 (still 1 mm proud of the knob). Your thumb then pushes 0.5 mm nearer the bar and the
  stop meets it 0.25 mm nearer, so the knob turns less every time it lands. The knob stops are shorter
  to match (2.65 mm instead of 3.5) so they're just as stiff.
- The check now also works the plates out turned (one peg's end where it's drawn, the other 0.35 mm
  out), eight ways in all, and holds every one of them to the limits. (It left out your thumb
  pressing the knob in, though: see the test version note at the top.)

**Not proven yet.** The first layer of the knob carriage's roof is a bridge over the groove the
rib runs in. Near each end of the roof, where it is cut back in a curve, that first layer is held
by the bar's side only, out to 1.2 mm past what the layer under it reaches (the check allows
0.4). A strand held at one end can droop a little toward the rib under it. A roof cut back
step by step, layer by layer, would hold every strand at both ends, but it leaves thin layers right
where the bar bends into the knob, and the stress there came out much higher, so the knife keeps
the one smooth cut. The fit test's carriage piece shows it before you print the knife: see "Knob on
its rib" below. Nothing has been printed yet.

| | |
|---|---|
| Handle | 178 x 38 x 12.4 mm, three plates held by four printed screws; finger scallops on the side away from the knob, and on the knob's side a guard at each end of the knob's slot (43 mm wide there) |
| Blade out | 78 mm |
| Knob | 38 mm long, its lips 3.7 mm out from the handle's side, a saddle for your thumb in the middle and a lip at each end; it slides 28 mm (the blade moves 86 mm), about 17 N (1.7 kg) at the end of the push |
| Spring | one printed TPU band, no metal, and two spares |

## How it works

- **One band, two sleds.** A TPU band runs straight through a slot in a post on the blade
  (the lug), from **sled F** behind the lug to **sled B** in front of it. Each sled leans on a
  post (a riser) on the knob's bar, so when the knife sits shut or open the band pulls its two
  sleds onto their risers and pulls on nothing else. The band is always a little stretched, so
  over months it slowly loses some of its pull; if the throw gets weak, fit a spare.
- **Push.** Sled F is stopped by the lug, so the band stretches while the bar carries sled B
  forward.
- **Snap.** A few millimetres from the end of the push, a cam on the bar pushes the latch
  block in. The band throws the blade about 22 mm, sled F stops on its riser, and the blade
  coasts the rest of the way. It stops against sled B, which leans on a TPU pad, and the block
  drops into the open window.
- **The latch.** A small block in the blade's carrier is pushed out by a springy arm into a
  window in the handle wall, and catches on the end of the rail. The rail floats between two
  TPU cushions, which take the knock when the blade bounces back off its pad.
- **A light, tough latch arm.** The arm bends twice on every push: the cam pushes it in, then
  the far ramp kicks it. So it is shaped to bend evenly along its length, not all at one spot.
  It is thin at its tip (0.85 mm), gets thicker toward the blade, and flares into big round ends
  where it joins the blade. It only bends about half a percent, and printed PLA takes that
  about 10,000 times. It presses the block out only lightly where the block just rubs along the
  bar, but it is stiff enough to throw the block out hard where it has to catch.
- **Little friction on the way.** The block only rides a short catch at each end of the rail.
  In between it floats out against the knob's bar, barely touching anything, and a ramp on the
  far catch guides it back in just before the end.
- **Back.** Pull the knob back and it all happens the other way round.
- **A band with a flatter pull.** The band is fitted 12.5 mm longer than it prints (it was 5),
  and it is longer and thinner (0.85 mm square). It stores the same energy for the throw as the
  old band did, but it pulls less at the end of the push: 0.85 of what the old one pulled. The
  thumb pushes the band's pull through the twisting sled and the cam, so that is what your thumb
  feels. Fully pushed it stretches 44 %.
- **Soft landings for the sleds.** Each riser wears a small TPU cap where its sled lands on it.
  The cap grips a thin fin at the end of the riser, and the fin stands on a foot as wide as the
  riser, so a knock pulls on the foot's wide root, not on the thin fin. A low sole runs on from
  the foot under the cap, so a knock bends the knob's bar at the riser's face, not under the cap.
- **The knob lands on its own stops.** Your thumb keeps pushing after the blade lets go, so on
  every push the knob runs on to the end with your thumb behind it. Your thumb weighs about four
  times as much as the knob slider. At each end of the knob's travel a TPU block, the knob stop,
  stands on the outside of the handle in front of a guard. A little T at its foot sits in a
  T-shaped slot in the guard, under the middle plate, so it can't come out. The knob's end face
  lands on it square on, at about the height your thumb pushes and near the line it pushes on,
  just before its sled meets its pad. The knob's ends are cut back a little low down and on the
  inside, and the stop's face is cut back 1.7 mm on its inner half, so however hard the knob lands
  the stop meets only the knob's outer part. (With a flat stop the knob's inner part reached it
  once it squashed half a millimetre, and the hard landings squash it more than that.) So the
  two stops are mirror images, a rear one and a front one. Your push and your thumb's weight
  stop right there at the knob. They don't run down the knob's thin bar.
- **The knob rides a rib.** The knob slides along the handle's side, and inside its slot the
  bottom of the handle's wall is left standing as a low rib, 1.4 mm wide and 1 mm tall, the whole
  length of the slot. The knob's carriage straddles it: a foot on the knob's inner face runs down
  the rib's outside, a wider part of the bar runs down its inside, and a roof joins them over the
  top. It has half a millimetre of play across the rib, the brain's sliding fit, over 38 mm, but
  it sits off the middle: 0.15 mm on the bar's side and 0.35 on the knob's. So when your thumb
  pushes the knob 7 mm off the bar's line, and the stop pushes back, the carriage turns a little,
  and the end that swings outward stops on the rib a tenth of a millimetre before the bar reaches
  the lane's wall at the cam beyond; the bar between them bends much less. The plain bar either
  side of the knob has room in the slot to follow the little the knob still turns, and behind the
  slot the lane's wall is cut back another 5 mm for the same reason. The ends of the carriage's two
  faces that run on the rib are rounded off 0.065 mm over their last 3.5 mm, so a tilted carriage
  rides on a gently rounded edge instead of digging a corner into the rib. Where the bar meets the
  back of the carriage it widens smoothly over its last 6 mm, and the roof's ends are cut back in a
  curve, so there is no square step for a crack to start from.
- **The plates are lined up by D-shaped holes.** Each of the two pegs that line a plate up goes
  into a hole with one flat side, on the knob's side. The flat touches its peg, so the plate can't
  sit off toward the blade, where it would push the knob's bar in through riser F's slot.
- **A saddle for your thumb.** Two ridges stand up 1 mm in the middle of the knob, 13 mm apart,
  with grip grooves between them. Rest your thumb between them: push the front ridge to push the
  knob forward, the back ridge to pull it back. You don't have to move your thumb along the knob
  to change direction. The lips at the knob's two ends are what the knob stops meet.
- **Two knocks are still plastic on plastic, and they're fine.** At the end of each throw the
  blade's lug picks up the waiting sled. When the blade bounces back off its pad, the latch
  block meets the end of the rail before the rail rides into its cushion. The parts that get
  hit are light (a sled weighs about 1 gram, and the rail floats on its cushions), so each is a
  quick tap: about 8 and 7 MPa at the faces that meet, well under the 19.5 MPa allowed for a
  knock on every throw.
- **The screws** thread into four posts printed on the top plate, which reach down through the
  middle plate, so tightening them pulls all three plates together.

## What to print

Open these from inside Flash Studio (File → Open Project).

| File | Plate | What's on it | Filament |
|---|---|---|---|
| `1 fit test.3mf` | 1 | The knife's four screws, three gauge nuts with 1, 2 and 3 corners cut off, a short piece of the rib the knob rides, and the peg test: a small square of the base plate with its peg, and a square of the middle plate with the D-shaped hole that goes over it | Black (filament 2) |
| | 2 | A latch test: the part of the blade round the latch, with its post (the lug), and a latch block; and a short piece of the knob's carriage | White (filament 1) |
| `3 TPU parts.3mf` | 1 | Three normal bands (one for the knife, two spares), two pads, two rail cushions, two riser caps, a rear and a front knob stop | **TPU** in slot 4 |
| | 2 | Three strong bands: print it only if the hang test says so | TPU |
| | 3 | Three soft bands: print it only if the hang test says so | TPU |
| `2 knife plates.3mf` | 1 | The three handle plates, each with its part of the two guards for the knob stops | Black |
| | 2 | Sled F, sled B, rail | Black |
| | 3 | Blade, latch block | White |
| | 4 | Knob slider (on its own plate, so the latch block prints as it does in the fit test) | White |

The knob slider and the fit test's carriage piece each carry a small setting (a modifier) over
the first layer of the carriage's roof, where it bridges the groove the rib runs in. It makes
Flash Studio lay that bridge straight across the groove, not along it. Leave it on. Don't turn
the knob slider or the carriage piece on the plate, and don't let Arrange turn them: the
setting's direction is fixed to the bed, so a turned part gets its bridge laid along the groove.

Print them in that order: the fit test, then TPU plate 1 and the hang test (below), then the
knife plates.

The PLA projects are set up for strong parts, as the brain says for anything that gets hit:
230 °C, part fan 45 %, side blower off, slower acceleration. The parts that move or take knocks
print solid with slow walls. The handle plates, the rail and the fit test's rib piece get a
5 mm brim: peel it off before you put them together. The knob slider and the fit test's
carriage piece print with no brim on purpose: their first layer is two strips either side of the
groove the rib runs in, and a brim would fill that groove under the roof, where you couldn't get
it out. In the Send dialog, check the slots by number (1 white, 2 black).

The TPU project already has filament 1 set to Generic TPU (240 °C, slow), and every TPU part
prints solid. Load the TPU in **slot 4** and, in the Send dialog, pick **slot 4** for
filament 1. After printing, pick any strings out of the bands' eyes and the riser caps' slots.

The small TPU parts on plate 1, so you can tell them apart:

| Part | How many | Size as it prints |
|---|---|---|
| Pad | 2 | 9.5 x 5 mm, 2 mm tall |
| Rail cushion | 2 | 12 mm long, 1.6 mm wide, 2.85 mm tall |
| Riser cap | 2 | a little U, 2.45 x 2.35 mm, standing 4.85 mm tall |
| Knob stop | 2, a rear one and a front one | a block 2.65 x 3.4 mm, 6.85 mm tall, with a little T on its back at its foot; half its face is cut back 1.7 mm |

The soft band is 0.65 mm thick, the normal one 0.85 and the strong one 1.05. They are hard to
tell apart, so keep each kind in its own bag.

### The fit test first

Print `1 fit test.3mf`, both plates, about an hour. Keep the four screws: they are the
knife's screws.

- **Thread.** The three gauge nuts have the same thread as the posts on the top plate, each a
  little looser than the one before. They are marked by their corners: nut 1 has one corner cut
  off, nut 2 has two and nut 3 has three. Screw each nut onto a screw by hand and count how
  many turn on.
  - **Two or three turn on:** the top plate will fit. Go ahead. (If all three are loose, that's
    fine too: the screws will just be a bit loose.)
  - **Only one turns on (the one with three corners cut off):** in the knife project, swap the
    top plate for `handle 3 top loose.stl` (right-click `handle 3 top`, Replace with STL).
  - **None turns on:** tell Claude before printing the knife.
- **Latch.** Lay the white test piece flat, its tall post up (the post is the blade's lug: it's
  there so the block prints the way it does on the knife's own plate). Drop the latch block into
  the slot. It goes in two ways and only one is right. The right way, its top stands only a hair
  proud of the flat top beside it (0.15 mm), with its cut-off corners standing upright. On end,
  it stands about 2.2 mm proud: lift it out, turn it a quarter turn and drop it in again. Press
  it in flush with a fingertip and let go: it must spring straight back out on its own. If it
  sticks, pick any strings out of the slot and the thin gaps round the springy arm. If it still
  sticks, tell Claude before printing the knife.
- **Knob on its rib.** The black rib piece is a short length of the rib in the knob's slot, cut
  from the base plate, on a strip of floor. The white carriage piece is the back 24 mm of the knob
  slider: a length of bar, the knob, and the roof joining them with a groove under it. Stand the
  rib piece on the table, rib up. Drop the carriage piece over it from above, so the rib goes into
  the groove under the roof: the knob's side outside the rib, the bar inside it. Slide it from end
  to end. It's right when it slides easily all the way and you can feel a little play side to
  side. Resting, its roof may sit a hair up on the rib's top: that's fine. If it binds, pick any
  strings out of the groove and off the rib and try again. If it still binds, or it drops loose
  over the rib, tell Claude before printing the knife. (The knife's own rib prints faster, with
  the base plate, than this little piece does, so it can come out a touch different.) Then turn
  the carriage piece over and look into the groove at the end where the roof's end is cut back in
  a curve (the other end is cut straight across): the curved edge of the roof should stand level
  with the rest of the roof. If it sags down into the groove, even a little, most likely where the
  curve meets the knob's side, tell Claude (see "Not proven yet" at the top).
- **Pegs.** The two small black squares are the peg test. One is a piece of the base plate with a
  peg on it, the other a piece of the middle plate with the D-shaped hole that goes over that peg.
  Each has one corner cut off. Before you put it on, look into the hole from underneath: one side
  of it is flat. Put a pen mark on the edge of the piece that the flat side faces (one of the two
  edges beside the cut corner): once it's on you can't see the flat. Put the hole piece on the peg
  piece, cut corner over cut corner, and press it down while you nudge it toward the pen mark, as
  you will the plates in step 7. It's right when it goes on and comes off by hand, and then:
  - pushed straight toward the pen mark, it moves about 0.3 mm;
  - pushed straight back the other way, it doesn't move;
  - pushed along the marked edge, either way, it slides about 0.35 mm. That's right too.

  If it won't go on, or goes on only with a hard push, the hole printed small. If it goes on by
  hand but hardly moves toward the pen mark, it printed a little small. Either way, stop and tell
  Claude before printing the knife, and don't scrape the hole bigger (see the test version note
  at the top).

### The hang test: which band

TPU varies a lot from brand to brand, and the band has to suit yours. This test tells you which
band to use. You need a full half-litre (500 ml) bottle of water (about half a kilo), a ruler,
and two thin round things about 3 mm thick that fit through a band's eye: two nails, two
bamboo skewers or two 3 mm Allen keys. The eye's hole is under 4 mm across, so a pencil is too
fat.

1. Print plate 1 of `3 TPU parts.3mf`. It has three normal bands.
2. First stretch the band about 10 times, slowly, until its eyes are about 130 mm apart (one and
   a half times its length). TPU goes softer the first few times it is stretched further than
   before, so this makes the test measure the band as it will work in the knife.
3. Put one nail through each eye of the band. Rest the top nail across a gap where a bottle can
   hang free below it, for example between the backs of two chairs pushed close together, or
   have someone hold it level. The band hangs straight down with the other nail at the bottom.
4. Measure from the top of the top nail to the top of the bottom nail.
5. Tie a loop of string round the bottle's neck and hang it on the bottom nail. Let it settle
   for about 10 seconds and measure again, the same way. Take the bottle off.
6. The second number less the first is the stretch. Read it to the nearest millimetre:

| Stretch | What it means | Fit |
|---|---|---|
| 26 to 38 mm | a normal TPU | the normal band. Keep the other two as spares |
| 39 to 60 mm | a soft TPU | a strong band: print plate 2 of `3 TPU parts.3mf` |
| 20 to 25 mm | a stiff TPU | a soft band: print plate 3 of `3 TPU parts.3mf` |
| more than 60 mm or less than 20 mm | outside what was worked out | tell Claude before printing the knife |

In a normal TPU it stretches about 30 mm.

**Then check the band you're going to fit,** whichever kind it is: stretch it 10 times to 130 mm
as in step 2 and hang the bottle on it the same way. It must stretch **23 to 39 mm**. Outside
that, tell Claude before fitting it. (If the band you tested is the one you fit, you've already
done this.)

## Putting it together

The handle is a stack of three plates. You build it up from the bottom with everything in
sight, then screw it shut. "Front" is the end the blade comes out of. "The knob side" is the
side with the slot.

1. **Base plate** (handle 1) on the table, the open side up.
2. **Rail cushions and rail.** On the knob side there is a long narrow groove a little way out
   from the blade's channel, narrower at each end. Press a TPU cushion's end down into each
   narrow end, flush against the end. Lay the rail in: its long back goes in the groove between
   the two cushions, its two catches point toward the channel. It goes in either way up and
   either way round. Push it along: it should give a little each way and spring back.
3. **Knob stops.** On the knob's side of the handle there is a guard, a bump, at each end of the
   knob's slot. In the top of each guard is a small T-shaped slot that opens toward the knob.
   Drop a knob stop's T down into each slot, so the block stands up in front of the guard. The
   two stops are not the same: they are mirror images, a rear one and a front one. Each has half
   of its face, the side toward the knob, cut back 1.7 mm; that half goes next to the handle. Its T
   is a little off the middle, so a stop at the wrong end, or the wrong way round, won't drop
   into the slot: swap them. It goes in only one way up (the T at the bottom). The T's head is
   squeezed a little, so press it all the way down. It's right when:
   - the stop stands straight up, its flat back flat against the guard's face, with no gap;
   - its foot sits down on the slot's floor, and its top stands about 4 mm above the base
     plate (the middle and top plates' parts of the guard go behind it later);
   - it doesn't wobble when you touch it.
4. **Riser caps and knob slider.** The end of each riser on the bar is a thin fin standing on a
   wide foot, with a low sole in front of it. Press a TPU riser cap down over each fin until its
   two legs sit on the foot and its front block on the sole. The caps fit either riser, either
   way round. Lay the bar in the lane (the outside lane, beyond the rail), cams toward the
   channel, the knob out through the slot in the side, between the two knob stops. Let it down
   straight from above: the knob's carriage drops over the low rib in the slot, the knob's foot
   outside the rib and the bar's wide part inside it, just as the fit test's pieces went
   together. Slide it back until the knob's back edge just touches the rear knob stop. Then slide
   it all the way forward and back by hand. It's right when:
   - it slides easily all the way, with a little play you can feel side to side;
   - the bar lies flat in its lane all along (the carriage's roof may rest a hair up on the rib's
     top, as in the fit test: that's fine);
   - at each end the knob's end face meets its stop's face squarely and stops softly, with no
     click.
5. **Blade.** Lay it in the channel, lug up. Slide it back until the square slot near its back
   end lines up with the first opening in the channel's knob-side wall.
6. **Latch block.** Drop it into that slot from above, sliding it down along the inside face of
   the knob's bar and pressing the springy arm in with it. It goes in two ways and only one is
   right: its top stands only a hair proud of the blade's top face. If it stands about 2.2 mm
   proud, it's on end: lift it out, turn it a quarter turn and drop it in again. Then pull the
   blade forward until the block stops against the end of the rail.
7. **Middle plate** (handle 2) on top. Its two peg holes are D-shaped, with the flat side toward
   the knob's side. Set it on the pegs and press it down while you nudge it toward the knob's side:
   it settles 0.05 mm over that way and can't sit the other way. The pegs line up, its part of each
   guard sits on the base plate's, behind the knob stop, and the blade's lug and the two risers,
   caps and all, come up through its slots. Now the knob stops' T's are covered and they can't come
   out. If the whole plate sits about half a millimetre high, it hasn't moved over yet: keep
   nudging it toward the knob's side as you press. If only one end won't go down (it stands about
   4 mm up), its part of the guard is sitting on top of that end's knob stop: don't force it down,
   slide the plate a hair toward that end and it drops.
8. **Pads.** Press a TPU pad into the small pocket at each end of the long room in the middle
   plate, so 5 1/2 mm of each pad's 9 1/2 stands out.
9. **Band and sleds.** Hook one eye of the band over the post on sled F, the other over the
   post on sled B. Put sled F behind the lug, between the lug and the rear pad, and sled B in
   front of the lug, with the band lying in the lug's slot. Each sled's wing goes on the knob
   side: sled F's just behind the rear riser's cap and sled B's just in front of the front
   riser's cap. The band stretches 12.5 mm to get there: pull sled B forward to stretch it,
   then let it settle against its riser's cap.
10. **Top plate** (handle 3) on. Its four round posts go down into the round holes at the
    corners of the middle plate, and its two D-shaped peg holes go over the middle plate's pegs:
    press it down while you nudge it toward the knob's side, as you did the middle plate. If it
    sits nearly a millimetre high, it hasn't moved over yet. If one end won't go down, that end's
    part of the guard is on top of a knob stop: don't force it, slide the plate a hair toward that
    end.
11. **Screws.** Hold the stack together and turn it over, top plate down. Push each screw into
    its hole and turn it with a coin in the slot until its head is down in its recess and the
    screw goes snug, then stop. They are printed, so don't crank them.

Try it: hold the knife with your fingers in the scallops on its side and the knob on top, under
your thumb. Push the knob forward all the way and keep your thumb on it until the blade has
locked out (about three hundredths of a second). Then pull it back the same way. The blade
lets go only in the last few millimetres. Keep your thumb in the saddle in the middle of the
knob: push the front ridge to send the blade out, pull the back ridge to bring it in.

## If it doesn't work right

- **The throw gets weak, or the blade stops short of locking:** fit a new band first. Take the
  top plate off (four screws), lift the old band off the sleds' posts and hook on a spare. The
  band is always held a little stretched, so it slowly loses some of its pull over months and
  with use. If a new band doesn't fix it, check the latch
  block slides freely in its slot. If a new band from the same plate still stops short, do the
  hang test again on it.
- **Blade stops part way out after your thumb flicked off the knob:** push the blade the rest
  of the way by hand, out or in. It locks at either end.
- **Blade snaps out but won't stay open:** the latch block is in on end (see step 6).
- **Knob too stiff:** do the hang test again. If the stretch is 25 mm or less, fit a soft band.
- **Blade doesn't let go at the end of the push:** push the knob all the way.
- **Blade won't stay locked:** the block must spring out into its window. Clean any strings
  out of its slot and the gaps round the springy arm (the fit test shows this).
- **The knob feels rough or sticks partway:** take the top two plates off and pick any strings
  off the rib in the knob's slot and out of the groove under the knob's carriage. Check the bar
  lies flat in its lane, not up on the rib.
- **The knob clacks hard at the end of its push:** a knob stop is missing or loose (the knob's
  carriage then stops on the end of its slot). Take the top two plates off, press the stop's T back
  down into its slot as in step 3, or print a new one (the rear and the front stop are different).
  Then put the middle plate back over it.
- **The blade clacks hard as it stops:** a pad has come out of its pocket. Press it back in so
  5 1/2 mm stands out (step 8).
- **A sled clacks on its riser:** a riser cap has come off. Press it back down until its legs
  sit on the fin's foot.

## Taking care of it

- **Keep it out of the heat.** Don't leave it on a car's dashboard or in a sunny car window. A
  dashboard gets to about 70 °C, and PLA goes soft at about 57 °C, so the parts can bend out of
  shape.
- **Look it over after about 500 flicks.** Check the band's two eyes, and the latch arm where it
  joins the blade, near the blade's back end (with the top two plates off you can see it from
  above).
  White marks in the plastic are stress marks. If the band's eyes show them, fit a spare band.
  If the latch arm shows them, print a new blade. Look at the knob's bar too, where it runs into
  the back of the knob: white marks there mean print a new knob slider (see the test version
  note at the top).

## How it was checked

`make_knife.py` makes every part from the numbers at the top of the file. `check_knife.py`
walks a whole cycle and proves (231 checks pass; 1 does not yet, see the last points):

- every moving part clears the handle and every other part at every stage of a cycle, and
  every 0.5 mm along each stroke, with the latch block out, on a catch, on a ramp or pushed in
  by a cam, and with the knob driven 1.5 mm into either knob stop (and, with a stop left out,
  on until its carriage meets the end of its slot). The knob slider also clears everything
  moved 0.25 mm in (until a cam meets its lane's wall) or 0.15 out (until its carriage meets
  the rib);
- it goes together in the order above: the knob slider let straight down into the base plate
  over the rib, the blade past it, the middle plate over them and the top plate on, each
  without touching anything on the way;
- the cams leave the block alone at rest (the nearer one is 18 mm of knob away) and until the
  last 8 to 9 1/2 mm of each push, let it go at least 1.74 mm before the knob meets its stop,
  and have it fully in before the end. That is worked out from the block's real chamfered
  outline, leaning as the latch's load turns it, with the bar and the rail anywhere in their
  play, the bar pushed in by your thumb pressing the knob sideways too. A cam or the rail holds
  it in until it is past the rail's end;
- the block can't lean past its chamfers or catch on a corner (it leans at most 0.53 mm).
  Latched, it bears 1.70 mm deep on the rail's end; with the bar, the rail and the block at the
  worst ends of their play it still bites 1.15 mm deep;
- a step-by-step model of the block popping out has it biting the open catch at least 0.60 mm
  deep, more than the 0.45 needed, before the blade bounces back there, in all 20,736 cases;
- at rest the band pulls only its sleds onto their risers (it is 100.6 mm eye to eye, 12.5 mm
  over its printed 88.1), and fully pushed it stretches 44 %, under the 45 % allowed;
- a step-by-step model of a throw, worked out from the real parts, gets the blade to its lock
  with any reasonable TPU, friction and print weight, held flat or tilted up the worst way: 108
  cases with the band, 108 with the strong band in a soft TPU, 72 with the soft band in a stiff
  one, with 0.40 N of extra friction to spare normally and 0.11 N in the worst case. A band that
  has aged (held stretched for months: its pull at rest down to 0.8 and its stiffness to 0.9)
  still locks in every hang-test case, with 0.018 N to spare in the worst one, so fit a spare
  when the throw gets weak. It also locks in every case when your thumb flicks off the knob as
  it lands;
- the thumb force counts the sled being pushed twisting against its walls, the cam pushing the
  block into the rail, the rubbing of the walls that hold the knob slider straight (the rib, the
  lane's wall and the risers' slots, all pushed as your thumb turns the knob, pushing or pulling
  back), and your thumb pressing the knob in to hold the ridge (0.3 of its push): 16.9 N with a
  normal TPU, 11.5 to 30.9 N over the whole range of TPU and friction, and up to 32.5 N with the
  stiffest band the hang test fits, under the 33 N allowed;
- the hang test: under the bottle's 4.9 N the normal band stretches 59.7 mm in a very soft TPU
  (10 MPa), 39.8 at 15 MPa, 29.9 at 20, 23.0 at 26 and 19.9 at 30, worked out from the same band
  the throws use. Each band works over every stretch the table above fits it at, even with the
  stretch read 1 mm out either way: the strong band at 38 to 61 mm (TPU 9.8 to 15.7 MPa), the
  normal band at 25 to 39 mm (15.3 to 23.9) and the soft band at 19 to 26 mm (23.0 to 31.4). In
  each it gets the blade to its lock in all 72 throws tried (all 36 aged too), and the band is
  never stiffer than the stiffest one the knocks below were worked out for. The band you fit
  must stretch 23 to 39 mm: the stiffest and the softest band all this was worked out for;
- the pads squash at most 3.4 of their 9.5 mm, the rail cushions 3.1 of their 8 mm free, and the
  hardest arrival runs the blade on 4.0 mm, inside the 5 mm of room at the end of each window;
- the knob stops: a model of a stop's real shape shows a TPU block pushed on part of its face is
  stiffer than its pushed area alone says (1.23 to 1.41 times flat, 1.06 to 1.11 with the face cut
  back), so every landing is worked out with the stop 1 and 1.25 times that stiff. Each stop meets
  10.6 mm2 of the knob's end face and is 2.65 mm long, as stiff as the 3.5 mm stop was on the
  thicker knob (its E A / L within 0.1 % of the old one). Pushed into a stop as far as the checks drive it (1.5 mm), the knob
  still touches only the half of the stop's face that is not cut back, with only its own outer part;
- the knocks, and what they put in the plastic (MPa, with the limit in brackets: 19.5 for
  anything that bends on every throw, 30 for a rare knock, 12 across a printed layer). "Sideways"
  is the knob's bar bent flat in its lane with its bending up and down added; "where it meets the
  knob" is the same where the bar runs into the knob's carriage, raised by the factor the model of
  the real shape gives there:

| Knock | How hard | Stress (limit) | |
|---|---|---|---|
| Every push, at the moment the blade lets go | your thumb 16.2 N (31.5 N with the stiffest band and the most friction); 16.9 N (32.9 N) counting your thumb pressing the knob in | sideways 9.4 and where it meets the knob 12.4 (19.5); 13.2 and 16.6 at worst. Counting your thumb pressing the knob in, these go down | ok |
| Every return push, the same pulling back | 15.7 N (30.2 N); 16.5 N (32.8 N with the stiffest band and the most friction) counting your thumb pressing the knob in | sideways 11.8 and where it meets the knob 14.1 (19.5); 18.5 and 18.8 at worst. **Counting your thumb pressing the knob in: where it meets the knob 21.3 (19.5), 24.1 at worst; with the stiffest band and the most friction 35.4, and 22.6 sideways (19.5)** | **over: see the top** |
| A sled meets its riser's TPU cap, every throw | 4.1 m/s, 15 N; the cap squashes 0.5 of 2.45 mm | bar 7.8 (19.5), sideways 10.6 and where it meets the knob 13.2 (19.5), fin's first layer 2.7 (12), sled's wing 2.3 (19.5) | ok |
| Thumb flicked off as the knob lands | 7.7 m/s, 28 N | bar 14.2 (30), sideways 14.4 (30), fin 5.8 (12), wing 4.3 (30) | ok |
| Knob let go just before the blade lets go | 7.2 m/s, 26 N | bar 12.9 (30), sideways 13.1 (30), fin 5.3 (12), wing 4.0 (30) | ok |
| The same knob landing on its stop, either end | 84 mJ; cap 51 N, the knob stop 80 N, squashed 0.71 of its 2.65 mm | bar 23.8 (30), fin 10.6 (12), wing 7.9 (30), sideways 24.3 and where it meets the knob 28.8 (30), the knob's roof over its rib 16.3 (30) and its twist across its layers 11.6 (12), the rib 12.0 (18) | ok |
| The knob, with your thumb's 10 g held stiff behind it, landing on its stop every throw | up to 3.9 m/s, the thumb still pushing 28 N; the stop 202 N, squashed 1.28 of its 2.65 mm; cap 31 N | bar 15.2 (19.5), sideways 16.8 and where it meets the knob 18.2 (19.5), fin 6.3 (12), wing 4.7 (19.5), the saddle's ridge 13.1 (19.5), the roof 7.7 (19.5), the stop on its guard 10.7 (19.5), the T-slot's shoulders 18.1 (19.5), the rib 7.6 (12) | ok |
| The same, counting your thumb as a soft pad | the stop 74 N, cap 20 N | bar 8.7 (19.5), sideways 15.2 and where it meets the knob 17.8 (19.5), fin 4.0 (12), roof 9.9 (19.5) | ok |
| The rail, a normal bounce | 25 N | 16.4 (19.5) | ok |
| The rail, the hardest bounce | 37 N | 23.2 (30) | ok |
| The lug picks up the waiting sled, plastic on plastic | 3.9 m/s | 8.1 (19.5) | ok |
| The latch block meets the rail's end, plastic on plastic | 3.3 m/s | 6.8 (19.5) | ok |

- the knob's bar sideways: the bar worked out lying flat in its lane, as a beam on every wall it can
  meet, read off the three plates; the knob's push and return push, its stops and the sleds
  landing on the risers' caps turn it, the rib takes the turn, and the bar's bending flat is added
  to its bending up and down (the table). It is worked out eight ways: the carriage's fit as drawn
  and 0.05 mm looser each side (a print can come out that much off, and the rounded ends wear),
  each with the middle and top plates where drawn, 0.35 mm off away from the blade, and turned
  about either peg with the other peg's end 0.35 mm out. They can't sit off toward the blade: the
  flat in each D-shaped peg hole meets its peg -0.05 mm as printed, layer by layer, so a plate
  pressed on sits 0.05 mm the other way. Every one of the eight is held to the limits, but
  without your thumb pressing the knob in (see the top). Where the
  bar runs into the knob's carriage, a flat model of the slider's real shape there, each bit as
  thick as the slider is tall, gives what the joint raises the bending to: 1.15 times at the
  back of the carriage (1.22 in the roof), 1.18 at the front (1.08). That model was
  first checked against Peterson's textbook case of a stepped bar with rounded corners: 1.96 and
  1.56 against the book's 1.95 and 1.56. Bent that way the slider still clears everything,
  the blade too, sitting on the channel wall its latch arm presses it to with 0.1 mm to spare,
  also with your thumb held on the knob at either end while the blade arrives (5 to 32 N): the
  plain bar keeps 0.17 mm of its 0.50 to the rib, riser F 0.10 of its 0.40 to its slot's
  wall. Your thumb can press the slider in at most 0.30 mm, as the latch checks take it. The rib is
  pushed at most 6.4 N at one end of the carriage on every throw: 7.6 MPa across its root's layers
  (limit 12), and the carriage's rounded end presses it 15.0 MPa (limit 19.5) over the 0.19 mm of
  height they share with the bar lifted to the middle plate (0.54 as drawn). Where riser B's front
  stands in its slot only the top 0.25 mm of its sole is plastic, and the slot pushes it at most
  5.8 N there on every throw, 10.6 N on a let-go knob (16.6 MPa, limit 30);
- the bar's bending up and down is worked out on the room the plates really give it, with the
  slider's real stiffness all along (the risers and the knob's carriage 29 to 52 times as stiff
  as the plain bar), resting on its floor, where drawn or lifted to the middle plate (all the
  same), and again with the middle and top plates 0.35 mm off across either way, which also covers
  them turned: at most 15.2 MPa on every throw and 23.8 on the let-go knob (limit 30). The middle
  plate's floor covers the bar's outer 0.6 mm beside the risers' slots, so 0.25 mm still holds it
  down with the plates that far off;
- the knob's stops meet the outer part of its end face, 0.30 mm under the height your thumb
  pushes at and 0.47 mm inside its line, and squash at most 1.28 of their 2.65 mm; the guards they
  stand against, the T-slots that hold them and the knob's ridges, lips and roof all stay under
  their limits at the hardest landing (the table);
- the latch arm bends at most 0.53 % on every push, under the 0.65 % that printed PLA takes
  about 10,000 times. Everything else PLA that bends on every throw stays under 19.5 MPa, the
  same limit (at most 18.8, where the knob's bar runs into the back of its carriage on a hard
  return push; counting your thumb pressing the knob in, that joint is over it, see the top). That limit is where half of such parts crack by 10,000 pushes, so it is a pass
  line, not a promise: 15 or less would be better, and the knob's bar is not there yet. A knob let
  go before the blade is the rare knock, held to 30 (good for about a hundred of them); it reaches
  28.8;
- the printed screws mesh with the top plate's posts with 0.36 mm of clearance all round, over
  3.55 mm of thread, and lifting the top plate 1 mm (or the loose one) runs it into the screws,
  so they hold all three plates; the posts sit in round holes with 0.4 mm all round, and the pegs
  in D-shaped holes, 0.35 mm round the round part, but a D-shaped hole that prints more than
  0.15 mm small all round won't go on (the checker says 0.30 because it lets only the round part
  shrink; see the top); the gauge nuts take the screws, and each cut-off corner leaves a 2.08 mm flat you can
  count, with 0.94 mm of wall left over the thread. The peg test's two pieces, cut from the plates,
  fit each other as the plates do as drawn (the knife's own pegs print in much shorter layers:
  see the top);
- each knob stop's T is squeezed 0.05 mm a side in its slot and can't pull out past the slot's
  shoulders, and each riser cap grips its fin 0.09 mm a side; the caps stand wholly above the
  latched block's top, so nothing rubs a cap off;
- every clearance follows the brain's rules, every part prints without anything hanging in
  the air (the carriage's roof is a short bridge over its groove), every flat face sits on a
  layer line, no wall is thinner than two lines, no gap inside one part is under 0.45 mm, and the
  latch block's slot and the carriage's faces on the rib have their first layer set back so its
  spread doesn't make them rub (read off the parts);
- the three project files, read back, have every part on its own plate, clear of the others,
  with its filament and its settings, and hold what the tables above say to print: the screws at
  60 mm/s, all 17 TPU parts solid, the knob's roof modifier over the roof's bridge where it is,
  with a real direction (straight across), no brim under any part (the knob slider and the
  carriage piece have none), the fit test's carriage piece sliding on its rib piece with the same
  play as the knife; and the fit test's latch block prints its top layers beside the lug, 8 seconds
  a layer, as on the knife's own plate.

Not passing yet: the roof's bridge. Along its bridge lines, the first layer of the carriage's roof
is held at one end only for up to 1.2 mm past what the layer below reaches, near both ends of
the roof (the check allows 0.4; see "Not proven yet" at the top). Over the limit too, though the
checker doesn't say so yet: the return push counting your thumb pressing the knob in (see the
test version note at the top).

Not checked yet: the roof's bridge direction is set, but nobody has sliced the knob slider in
Flash Studio to see it hold (ask Claude to slice it three times from the command line, as the brain says,
before printing). Nothing has been printed yet.
