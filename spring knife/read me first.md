# Spring knife toy — read me first

A double-action fidget toy designed from scratch (Nov 2026). Push the **knob** on the side
**forward** about 28 mm: near the end the blade snaps 86 mm out and locks. Pull it **back**:
near the end the blade snaps back in and locks. Every part is printed, the screws and nuts too:
nothing to buy.

It's a toy: the blade is 4 mm thick plastic with round edges and a round tip. It does come out
with a snap, so point it away from faces.

| | |
|---|---|
| Handle | 178 x 38 x 12.4 mm, three plates held by four printed screws and nuts; finger scallops on the side away from the knob |
| Blade out | 78 mm |
| Knob push | 28 mm (the blade moves 86 mm) |
| Spring | one printed TPU band, no metal |

## How it works

- **One band, two sleds.** A TPU band runs straight through a slot in a post on the blade
  (the lug), from **sled F** behind the lug to **sled B** in front of it. Each sled leans on a
  post (a riser) on the knob's bar, so when the knife sits shut or open the band is only just
  taut and pulls on nothing. It doesn't wear out sitting in a drawer.
- **The latch.** A small block in the blade's carrier is pushed out by a springy arm into a
  window in the handle wall, and catches on the end of a rail. The rail sits on a TPU cushion,
  which takes the knock when the blade bounces.
- **Push.** Sled F is stopped by the lug, so the band stretches while the bar carries sled B
  forward.
- **Snap.** A few millimetres from the end of the push, a cam on the bar pushes the latch
  block in. The band throws the blade about 24 mm, sled F stops on its riser, and the blade
  coasts the rest of the way. It stops against sled B, which leans on a TPU pad, and the block
  drops into the open window.
- **Back.** Pull the knob back and it all happens the other way round.

## What to print

Open these from inside Flash Studio (File → Open Project).

| File | Plate | What's on it | Filament |
|---|---|---|---|
| `1 fit test.3mf` | | One screw and three nuts with 1, 2 and 3 notches | Black (filament 2) |
| `2 knife plates.3mf` | 1 | The three handle plates | Black |
| | 2 | Sled F, sled B, rail, latch block, 4 screws, 4 nuts | Black |
| | 3 | Blade, knob slider | White (filament 1) |
| `3 TPU parts.3mf` | | Band, two pads, rail cushion | **TPU**: before slicing, click filament 1 and pick your TPU preset |

Print the fit test first, about 20 minutes. Screw each nut onto the screw by hand:

- **The 2-notch nut turns on by hand:** the nuts on plate 2 will fit. Go ahead.
- **Only the 3-notch nut turns on:** on plate 2, swap the four nuts for `nut loose.stl`.
- **Even the 1-notch nut is loose:** that's fine too; the nuts on plate 2 will just be a bit loose.

Every project uses 0.20mm Standard with **Arachne**, which the thin band needs. The screws and
nuts are set to 6 walls and 100 % infill so they come out solid. Flash Studio is set to bridge
the screw-head recesses in the base plate ("counterbore hole bridging": partially bridge), so
their ceilings print clean. In the Send dialog, check the slots by number (1 white, 2 black).

TPU varies a lot from brand to brand. The band on the TPU plate suits a normal 95A TPU. If the
blade stops short of locking, print `band strong.stl`. If the knob is too stiff to push, print
`band soft.stl`.

## Putting it together

The handle is a stack of three plates. You build it up from the bottom with everything in
sight, then screw it shut. "Front" is the end the blade comes out of. "The knob side" is the
side with the slot.

1. **Base plate** (handle 1) on the table, the open side up.
2. **Rail cushion and rail.** Drop the TPU rail cushion, joined side down, into the small
   pocket beside the channel on the knob side. Lay the rail in the long groove next to it, flat
   face toward the channel, with its tab down in the gap in the middle of the cushion. Push
   the rail along: it should give a little each way and spring back.
3. **Latch block.** Slide it into the slot on the knob side of the blade's carrier, chamfered
   edges facing out. The springy arm behind it pushes it out.
4. **Blade.** Lay it in the channel, pushed all the way back (shut), the block toward the rail.
5. **Knob slider.** Lay its bar in the lane outside the rail, cams toward the blade, the knob
   out through the slot in the side. Push it all the way back.
6. **Middle plate** (handle 2) on top. The pegs line up, and the blade's lug and the bar's two
   risers come up through its slots.
7. **Band and sleds.** Hook one eye of the band over the post on sled F, the other over the
   post on sled B. Put sled F behind the lug and sled B in front of it, with the band lying in
   the lug's slot. Each sled's wing goes on the knob side, sled F's just behind the rear riser
   and sled B's just in front of the front riser. The band stretches 4 mm to get there.
8. **Pads.** One TPU pad goes in the pocket behind sled F, the other in the pocket in front of
   sled B.
9. **Top plate** (handle 3) on.
10. **Screws.** Drop a nut into each hex pocket on top. Push each screw up from the bottom and
    turn it with a coin in the slot until the head sits down in its recess, then stop. They
    are printed, so don't crank them.

Try it: push the knob forward until the blade snaps out, then pull it back until it snaps in.
Push or pull the knob all the way: the blade lets go only in the last few millimetres.

## If it doesn't work right

- **Blade stops short of locking:** print `band strong.stl`. Also check the latch block
  slides freely in its slot.
- **Knob too stiff:** print `band soft.stl`.
- **Blade doesn't let go at the end of the push:** push the knob all the way. Check the latch
  block has its chamfered edges facing out.
- **Blade won't stay locked:** the block must drop into its window. Clean any strings out of
  its slot so the springy arm can push it out.

## How it was checked

`make_knife.py` makes every part from the numbers at the top of the file. `check_knife.py`
walks a whole cycle and proves:

- every moving part clears the handle and every other part at every stage of a cycle, and
  every 0.5 mm along each stroke, with the latch block out, on the rail or pushed in by a cam;
- the cams leave the block alone at rest and until the last 8 mm of each push. They have it
  pushed in before the end, and hold it in until it's clear of its window;
- at rest the band pulls on nothing, and fully pushed it stretches 36 %;
- a step-by-step model of a throw, worked out from the real parts, gets the blade to its lock
  with any reasonable TPU, friction and print weight. It reports how hard the blade lands
  (about 50 mJ, 3 m/s) and how far the pads and cushion squash;
- the knob, let go mid-push, is stopped by a TPU pad, not by plastic;
- the printed screws mesh with their nuts with 0.36 mm of clearance all round;
- every clearance follows the brain's rules, every part prints without anything hanging in
  the air, and every height sits on a layer line.

Nothing has been printed yet.
