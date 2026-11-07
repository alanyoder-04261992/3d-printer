# Spring knife toy — read me first

A double-action fidget toy designed from scratch (Nov 2026). Slide the **knob** on the side
**forward** and the blade snaps out and locks. Slide it **back** and the blade snaps back in.
Every part is printed, the screws and nuts too: nothing to buy.

It's a toy: the blade is 4 mm thick plastic with round edges and a round tip. It does come out
with a snap, so point it away from faces.

| | |
|---|---|
| Handle | 178 x 38 x 17.6 mm, four plates held by four printed screws and nuts; finger scallops on the side away from the knob |
| Blade out | 78 mm |
| Knob travel | 96 mm |
| Springs | two printed TPU bands round four rollers, no metal |

## How it works

- **Two bands pull opposite ways.** Band F (top level) pulls the blade toward the knob from in
  front, band B (lower level) from behind. With the knob level with the blade they balance.
- **Cocking.** The blade is held by a tooth on a springy arm, sitting in a window in the
  handle wall. Slide the knob forward and band F stretches.
- **Firing.** In the last 12 mm of the stroke the knob drags a pushrod along. A bump on the
  pushrod rides over the tooth and pushes it out of its window. Band F snaps the blade out,
  and the tooth drops into the window for open.
- **Back in.** Sliding the knob back stretches band B instead. At the end, the pushrod's
  other bump frees the tooth and the blade snaps home.

## What to print

Open these from inside Flash Studio (File → Open Project).

| File | Plate | What's on it | Filament |
|---|---|---|---|
| `1 knife plates.3mf` | 1 | The four handle plates | Black (filament 2) |
| | 2 | Pushrod, 2 pins, 4 rollers, 4 screws, 4 nuts | Black |
| | 3 | Blade, slider with its knob | White (filament 1) |
| `2 bands (TPU).3mf` | | Two bands | **TPU**: before slicing, click filament 1 and pick your TPU preset |

Both projects use 0.20mm Standard with **Arachne**, which the thin band walls need. The screws
and nuts are already set to 6 walls and 100 % infill, so they come out solid. In the Send
dialog, check the slots by number (1 white, 2 black).

The bands come in two strengths. `band.stl` (1.0 mm) is on the plate. If the knob is too
stiff to slide, print `band soft.stl` (0.8 mm) instead.

## Putting it together

The handle is a stack of four plates. You build it up from the bottom with everything in
sight, then screw it shut.

1. **Pins.** Press the long pin into the hole in the blade's carrier, flush with the bottom.
   Press the short pin into the slider, flush with its top. If a pin is loose, add a drop of
   glue.
2. **Base plate** (handle 1) on the table, pegs up. Lay the blade in its channel **closed**
   (pushed all the way back), pin up.
3. **Channel plate** (handle 2) on top: its pegs and holes line up, and the blade pin comes up
   through the slot.
4. **Pushrod** into its lane beside the blade. The bumps face the blade, the end tabs face
   out. Push it all the way back.
5. **Slider.** Drop it in beside the pushrod, outside the thin wall, knob out through the slot
   in the side. Set it about 5 mm from the back of the slot.
6. **Band B.** Put a roller on each of the channel plate's two posts. Hook one eye of a band
   over the blade pin. Take it back round the rear roller, forward round the front roller, and
   back to the knob's pin. It stretches by about half to get there.
7. **Band deck** (handle 3) on: the blade pin through its slot.
8. **Band F.** Rollers on the deck's two posts. Hook the second band on the blade pin, forward
   round the front roller, back round the rear roller, and forward to the knob's pin.
9. **Top plate** (handle 4) on: the top of the blade pin slides in the groove underneath.
10. **Screws.** Drop a nut into each hex pocket on top. Push each screw up from the bottom and
    turn it with a coin in the slot until it's snug. The hex pocket stops the nut turning.

Try it: slide the knob forward until it snaps out, then back until it snaps in.

## If it doesn't work right

- **Knob too stiff:** print the soft bands.
- **Blade stops a little short:** finish sliding the knob to the end; the bands pull it the
  rest of the way.
- **Blade doesn't let go at the end of the stroke:** the pushrod may be in backwards. Its bumps
  must face the blade.
- **Won't stay locked:** look for the tooth in its window, on the knob side of the base plate.
  If it doesn't drop in, tell Claude and the tooth can be made deeper.

## How it was checked

`make_knife.py` makes every part from the numbers at the top of the file. `check_knife.py` walks
through a whole cycle and proves:

- the blade slides its 86 mm without rubbing, stops at both ends, and the tooth locks it shut
  and open;
- the pushrod's bumps leave the tooth alone at rest. Crossing over, they push it 1.15 mm in,
  free of the wall, even with the pushrod shoved back against its backing wall;
- the knob slides its 96 mm and moves the pushrod only in the last 12 mm at each end. It is let
  go about 9 mm from the end, when the blade gets pulled to 82 of its 86 mm and the rest of the
  stroke pulls it to the stop;
- at all four points of a cycle, both bands clear everything and stay tight: they stretch from
  3 % to 92 %;
- the printed screws mesh with their nuts and lock;
- every hole follows the 0.4 mm rule;
- every height sits on a layer line.

Nothing has been printed yet.
