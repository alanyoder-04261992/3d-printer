# Spring knife toy — read me first

A double-action fidget toy designed from scratch (Nov 2026). Push the **knob** on the side
**forward** about 28 mm: near the end the blade snaps 86 mm out and locks. Pull it **back**:
near the end the blade snaps back in and locks. Every part is printed, the screws too:
nothing to buy.

It's a toy: the blade is 4 mm thick plastic with round edges and a round tip. It does come out
with a snap, so point it away from faces. Don't use the blade as a lever or press its tip into
a table: it's plastic.

| | |
|---|---|
| Handle | 178 x 38 x 12.4 mm, three plates held by four printed screws; finger scallops on the side away from the knob |
| Blade out | 78 mm |
| Knob push | 28 mm (the blade moves 86 mm), about 17 N (1.7 kg) at the end of the push |
| Spring | one printed TPU band, no metal |

## How it works

- **One band, two sleds.** A TPU band runs straight through a slot in a post on the blade
  (the lug), from **sled F** behind the lug to **sled B** in front of it. Each sled leans on a
  post (a riser) on the knob's bar, so when the knife sits shut or open the band is only just
  taut and pulls on nothing. It doesn't wear out sitting in a drawer.
- **Soft landings.** Each riser wears a small TPU cap where its sled lands on it, so no knock
  in the toy is plastic on plastic.
- **The latch.** A small block in the blade's carrier is pushed out by a springy arm into a
  window in the handle wall, and catches on the end of the rail. The rail floats between two
  TPU cushions, which take the knock when the blade bounces.
- **Push.** Sled F is stopped by the lug, so the band stretches while the bar carries sled B
  forward.
- **Snap.** A few millimetres from the end of the push, a cam on the bar pushes the latch
  block in. The band throws the blade about 23 mm, sled F stops on its riser, and the blade
  coasts the rest of the way. It stops against sled B, which leans on a TPU pad, and the block
  drops into the open window.
- **Little friction on the way.** The block only rides a short catch at each end of the rail.
  In between it floats out against the knob's bar, barely touching anything, and a ramp on the
  far catch guides it back in just before the end.
- **Back.** Pull the knob back and it all happens the other way round.
- **The screws** thread into four posts printed on the top plate, which reach down through the
  middle plate, so tightening them pulls all three plates together.

## What to print

Open these from inside Flash Studio (File → Open Project).

| File | Plate | What's on it | Filament |
|---|---|---|---|
| `1 fit test.3mf` | 1 | The knife's four screws, and three gauge nuts with 1, 2 and 3 notches | Black (filament 2) |
| | 2 | A latch test: the part of the blade round the latch, and a latch block | White (filament 1) |
| `2 knife plates.3mf` | 1 | The three handle plates | Black |
| | 2 | Sled F, sled B, rail | Black |
| | 3 | Blade, knob slider, latch block | White |
| `3 TPU parts.3mf` | 1 | Band, two pads, two rail cushions, two riser caps | **TPU** in slot 4 |
| | 2 | `band strong` and `band soft`: print one only if the band needs changing (see below) | TPU |

The PLA projects are set up for strong parts, as the brain says for anything that gets hit:
230 °C, part fan 45 %, side blower off, slower acceleration. The parts that move or take knocks
print solid with slow walls. The handle plates, the rail and the knob slider get a 5 mm brim:
peel it off before you put them together. In the Send dialog, check the slots by number
(1 white, 2 black).

The TPU project already has filament 1 set to Generic TPU (240 °C, slow). Load the TPU in
**slot 4** and, in the Send dialog, pick **slot 4** for filament 1. After printing, pick any
strings out of the band's eyes and the riser caps' slots.

TPU varies a lot from brand to brand. The band on plate 1 suits a normal 95A TPU. If the blade
stops short of locking, print `band strong` (plate 2 of the TPU project). If the knob is too
stiff to push, print `band soft`.

### The fit test first

Print `1 fit test.3mf`, both plates, about 45 minutes. Keep the four screws: they are the
knife's screws.

- **Thread.** The gauge nuts have the same thread as the posts on the top plate. Screw each
  nut onto a screw by hand.
  - **The 2-notch nut turns on by hand:** the top plate will fit. Go ahead.
  - **Only the 3-notch nut turns on:** in the knife project, swap the top plate for
    `handle 3 top loose.stl` (right-click `handle 3 top`, Replace with STL).
  - **Even the 1-notch nut is loose:** that's fine; the screws will just be a bit loose.
  - **No nut turns on:** tell Claude before printing the knife.
- **Latch.** Drop the latch block into the slot in the white test piece. It goes in two ways
  and only one is right: its top sits nearly flush with the test piece's top, with the cut-off
  corners standing upright. If it stands nearly a millimetre proud, it's on end: lift it out,
  turn it a quarter turn and drop it in again. Press it in flush with a fingertip and let go: it
  must spring straight back out on its own. If it sticks, pick any strings out of the slot and
  the thin gaps round the springy arm. If it still sticks, tell Claude before printing the
  knife.

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
3. **Knob slider.** Press a TPU riser cap down over the thin fin at the end of each riser on
   the bar, until it sits on the bar. Lay the bar in the lane outside the rail, cams toward the
   channel, the knob out through the slot in the side. Slide it so the knob's back edge is about
   5 mm from the back end of its slot.
4. **Blade.** Lay it in the channel, lug up. Slide it back until the square slot near its back
   end lines up with the first opening in the channel's knob-side wall.
5. **Latch block.** Drop it into that slot from above, sliding it down along the inside face of
   the knob's bar and pressing the springy arm in with it. It goes in two ways and only one is
   right: its top sits nearly flush with the blade's top face. If it stands nearly a millimetre
   proud, it's on end: lift it out, turn it a quarter turn and drop it in again. Then pull the
   blade forward until the block stops against the end of the rail.
6. **Middle plate** (handle 2) on top. The pegs line up, and the blade's lug and the two risers,
   caps and all, come up through its slots.
7. **Pads.** Press a TPU pad into the small pocket at each end of the long room in the middle
   plate, so about half of each pad stands out.
8. **Band and sleds.** Hook one eye of the band over the post on sled F, the other over the
   post on sled B. Put sled F behind the lug, between the lug and the rear pad, and sled B in
   front of the lug, with the band lying in the lug's slot. Each sled's wing goes on the knob
   side: sled F's just behind the rear riser's cap and sled B's just in front of the front
   riser's cap. The band stretches 5 mm to get there.
9. **Top plate** (handle 3) on. Its four posts go down into the hex holes at the corners of the
   middle plate.
10. **Screws.** Hold the stack together and turn it over, top plate down. Push each screw into
    its hole and turn it with a coin in the slot until its head is down in its recess and the
    screw goes snug, then stop. They are printed, so don't crank them.

Try it: push the knob forward all the way and keep your thumb on it until the blade has
locked out (about three hundredths of a second). Then pull it back the same way. The blade
lets go only in the last few millimetres. The two little lips on the knob are there to keep
your thumb on it.

## If it doesn't work right

- **Blade stops short of locking:** print `band strong`. Also check the latch block slides
  freely in its slot.
- **Blade stops part way out after your thumb flicked off the knob:** push the blade the rest
  of the way by hand, out or in. It locks at either end.
- **Blade snaps out but won't stay open:** the latch block is in on end (see step 5).
- **Knob too stiff:** print `band soft`.
- **Blade doesn't let go at the end of the push:** push the knob all the way.
- **Blade won't stay locked:** the block must spring out into its window. Clean any strings
  out of its slot and the gaps round the springy arm (the fit test shows this).

## How it was checked

`make_knife.py` makes every part from the numbers at the top of the file. `check_knife.py`
walks a whole cycle and proves:

- every moving part clears the handle and every other part at every stage of a cycle, and
  every 0.5 mm along each stroke, with the latch block out, on a catch, on a ramp or pushed in
  by a cam;
- the cams leave the block alone at rest and until the last 6 to 8 mm of each push, have it
  pushed in before the end, and hold it in until it's on the rail; the block can't lean past its
  chamfers or catch on a corner, it still bites the catch with the bar, the rail and the block
  at the worst ends of their play, and it is back out in its window before the blade can bounce
  back past it;
- at rest the band pulls on nothing, and fully pushed it stretches 38 %;
- a step-by-step model of a throw, worked out from the real parts, gets the blade to its lock
  with any reasonable TPU, friction and print weight, held flat or pointing up, and with
  margin to spare. It also gets there when your thumb flicks off the knob as it lands;
- the thumb force counts the sled being pushed twisting against its walls and the cam pushing
  the block into the rail: about 17 N with a normal TPU, 12 to 32 N over the whole range of TPU
  and friction;
- every knock lands on TPU and stays under its limits in the sleds' wings, the risers, the
  knob's bar and the rail: the sled meeting its riser's cap on every throw, a thumb flicked off
  the knob, a knob let go just before the blade lets go, and the bounces on the rail;
- the printed screws mesh with the top plate's posts with 0.36 mm of clearance all round, over
  3.55 mm of thread, and lifting the top plate runs it into the screws, so they hold all three
  plates;
- every clearance follows the brain's rules, every part prints without anything hanging in
  the air, every flat face sits on a layer line, no wall is thinner than two lines, no gap
  inside one part is under 0.45 mm, and the latch block's slot has its first layer set back so
  its spread doesn't make the block rub.

Nothing has been printed yet.
