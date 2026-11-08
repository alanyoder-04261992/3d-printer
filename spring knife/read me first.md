# Spring knife toy — read me first

A double-action fidget toy designed from scratch (Nov 2026). Push the **knob** on the side
**forward** about 28 mm: near the end the blade snaps 86 mm out and locks. Pull it **back**:
near the end the blade snaps back in and locks. Every part is printed, the screws and nuts too:
nothing to buy.

It's a toy: the blade is 4 mm thick plastic with round edges and a round tip. It does come out
with a snap, so point it away from faces. Don't use the blade as a lever or press its tip into
a table: it's plastic.

| | |
|---|---|
| Handle | 178 x 38 x 12.4 mm, three plates held by four printed screws and nuts; finger scallops on the side away from the knob |
| Blade out | 78 mm |
| Knob push | 28 mm (the blade moves 86 mm), about 16 N (1.6 kg) at the end of the push |
| Spring | one printed TPU band, no metal |

## How it works

- **One band, two sleds.** A TPU band runs straight through a slot in a post on the blade
  (the lug), from **sled F** behind the lug to **sled B** in front of it. Each sled leans on a
  post (a riser) on the knob's bar, so when the knife sits shut or open the band is only just
  taut and pulls on nothing. It doesn't wear out sitting in a drawer.
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

## What to print

Open these from inside Flash Studio (File → Open Project).

| File | Plate | What's on it | Filament |
|---|---|---|---|
| `1 fit test.3mf` | 1 | One screw and three nuts with 1, 2 and 3 notches | Black (filament 2) |
| | 2 | A latch test: the part of the blade round the latch, and a latch block | White (filament 1) |
| `2 knife plates.3mf` | 1 | The three handle plates | Black |
| | 2 | Sled F, sled B, rail, latch block, 4 screws, 4 nuts | Black |
| | 3 | Blade, knob slider | White |
| `3 TPU parts.3mf` | | Band, two pads, two rail cushions | **TPU** in slot 4 |

The PLA projects are set up for strong parts, as the brain says for anything that gets hit:
230 °C, part fan 45 %, side blower off. The parts that move or take knocks print solid with
slow walls, and the screws and nuts are solid too. The base plate's screw-head recesses are
set to bridge cleanly. In the Send dialog, check the slots by number (1 white, 2 black).

The TPU project already has filament 1 set to Generic TPU (240 °C, slow). Load the TPU in
**slot 4** and, in the Send dialog, pick **slot 4** for filament 1. After printing, pick any
strings out of the band's eyes before fitting it.

TPU varies a lot from brand to brand. The band on the TPU plate suits a normal 95A TPU. If the
blade stops short of locking, print `band strong.stl`. If the knob is too stiff to push, print
`band soft.stl`.

### The fit test first

Print `1 fit test.3mf`, both plates, about 40 minutes.

- **Nuts.** Screw each nut onto the screw by hand.
  - **The 2-notch nut turns on by hand:** the nuts in the knife project will fit. Go ahead.
  - **Only the 3-notch nut turns on:** in the knife project, swap the four nuts for `nut loose.stl`.
  - **Even the 1-notch nut is loose:** that's fine too; the nuts will just be a bit loose.
- **Latch.** Drop the latch block into the slot in the white test piece. It only fits one way
  up, either way round. Press it in flush with a fingertip and let go: it must spring straight
  back out on its own. If it sticks, pick any strings out of the slot and the thin gaps round
  the springy arm. If it still sticks, tell Claude before printing the knife.

## Putting it together

The handle is a stack of three plates. You build it up from the bottom with everything in
sight, then screw it shut. "Front" is the end the blade comes out of. "The knob side" is the
side with the slot.

1. **Base plate** (handle 1) on the table, the open side up.
2. **Rail cushions and rail.** On the knob side there is a long narrow groove a little way out
   from the blade's channel. Drop a TPU cushion into each end of it. Lay the rail in: its long
   back goes in the groove between the two cushions, its two catches point toward the channel.
   It goes in either way up and either way round. Push it along: it should give a little each
   way and spring back.
3. **Blade.** Lay it in the channel, lug up. Slide it back until the square slot near its back
   end lines up with the first opening in the channel's knob-side wall.
4. **Latch block.** Drop it into that slot from above, pushing the springy arm in a little. It
   only fits one way up. Then pull the blade forward until the block stops against the end of
   the rail.
5. **Knob slider.** Lay its bar in the lane outside the rail, cams toward the blade, the knob
   out through the slot in the side. Slide it so the knob's back edge is about 5 mm from the
   back end of its slot.
6. **Middle plate** (handle 2) on top. The pegs line up, and the blade's lug and the bar's two
   risers come up through its slots.
7. **Nuts.** Drop a nut into each of the four hex holes at the corners of the middle plate.
   They sit on the base plate.
8. **Pads.** Press a TPU pad into the small pocket at each end of the long room in the middle
   plate, so about half of each pad stands out.
9. **Band and sleds.** Hook one eye of the band over the post on sled F, the other over the
   post on sled B. Put sled F behind the lug, between the lug and the rear pad, and sled B in
   front of the lug, with the band lying in the lug's slot. Each sled's wing goes on the knob
   side: sled F's just behind the rear riser and sled B's just in front of the front riser. The
   band stretches 5 mm to get there.
10. **Top plate** (handle 3) on.
11. **Screws.** Hold the stack together and turn it over, top plate down. Push each screw into
    its hole and turn it with a coin in the slot until its head sits down in its recess, then a
    quarter turn more, and stop. They are printed, so don't crank them.

Try it: push the knob forward all the way and keep your thumb on it until the blade has
snapped out (it takes a hundredth of a second). Then pull it back the same way. The blade
lets go only in the last few millimetres. The two little lips on the knob are there to keep
your thumb on it.

## If it doesn't work right

- **Blade stops short of locking:** print `band strong.stl`. Also check the latch block
  slides freely in its slot.
- **Blade stops part way out after your thumb flicked off the knob:** push the blade the rest
  of the way by hand, out or in. It locks at either end.
- **Knob too stiff:** print `band soft.stl`.
- **Blade doesn't let go at the end of the push:** push the knob all the way.
- **Blade won't stay locked:** the block must spring out into its window. Clean any strings
  out of its slot and the gaps round the springy arm (the fit test shows this).

## How it was checked

`make_knife.py` makes every part from the numbers at the top of the file. `check_knife.py`
walks a whole cycle and proves:

- every moving part clears the handle and every other part at every stage of a cycle, and
  every 0.5 mm along each stroke, with the latch block out, on a catch, on a ramp or pushed in
  by a cam;
- the cams leave the block alone at rest and until the last 6 to 8 mm of each push, have it pushed
  in before the end, and hold it in until it's on the rail; the block can't catch on a corner
  as it goes, and it is back out in its window before the blade can bounce back past it;
- at rest the band pulls on nothing, and fully pushed it stretches 38 %;
- a step-by-step model of a throw, worked out from the real parts, gets the blade to its lock
  with any reasonable TPU, friction and print weight, held flat or pointing up, and with
  margin to spare. It also gets there when your thumb flicks off the knob as it lands;
- the thumb force counts the sled being pushed twisting against its walls: about 16 N with a
  normal TPU, 12 to 27 N over the whole range of TPU and friction;
- every knock is checked: the sled running into its riser on every throw, the pads and
  cushions, and the hardest one, the knob let go just before the blade lets go. That lands on
  a TPU pad and stays under the limits for the sled's wing, the riser and the bar;
- the printed screws mesh with their nuts with 0.36 mm of clearance all round, and the nuts
  are shut in so they can't ride up;
- every clearance follows the brain's rules, every part prints without anything hanging in
  the air, every flat face sits on a layer line, no wall is thinner than two lines, no gap
  inside one part is under 0.45 mm, and the latch block's first layer and its slot's are set
  back so their spread doesn't make them rub.

Nothing has been printed yet.
