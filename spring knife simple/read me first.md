# Simple spring knife: read me first

A blunt plastic fidget toy. Push the knob on top forward and the blade snaps out and locks.
Pull the knob back and the blade snaps in and locks.

**Not printed yet (Nov 11 2026).** Print the slide test first (step 1 below). It takes a
fraction of the time of the whole knife and tells us whether the blade slides freely.

## Why there is a new knife

The first spring knife (the `spring knife` folder) jammed:
- **Pinched blade.** The blade wouldn't slide without tapping. The plate that held the band
  sat right over the blade, 0.275 mm above it, and squeezed it once it was on.
- **Too many rubbing parts.** The knob rode a rib, the latch rubbed a rail, and there were
  TPU caps, pads and stops. Each one added a little drag.
- **A long slide on its own.** The band only pulls the blade as far as the knob moves. The
  knob moved 28 mm and the blade had to slide another 58 mm on its own, so it stalled.

This one is redrawn from scratch to be practical:

| | First spring knife | This one |
|---|---|---|
| Plates | 3: base, middle (band), top | 2: base and lid. Nothing between the blade and the band |
| Room where things slide | 0.25–0.3 mm at the sides, 0.275 above and below | 0.45 mm at the sides, about 1 mm in all up and down |
| Knob push | 28 mm, on the side | 38 mm, on top |
| Blade out | 79 mm | 59 mm |
| Slide on its own | 58 mm | 22 mm |
| TPU parts | band, pads, cushions, caps, knob stops | the band only, thicker, in three thicknesses |
| What rubs the blade on the way | the latch block on its rail | nothing, except the click at each end |
| Screws | 4 printed | 3 printed |

## How it works

- **The band.** One TPU band runs between two little sleds in a lane beside the blade.
  - Sled F sits behind a lug on the blade, sled B in front of it.
  - Each sled rests against a post (riser) on the knob's bar. At rest the band pulls on the
    bar, not on the blade.
- **Pushing the knob.**
  - The blade is locked closed, so the lug holds sled F back. Riser B carries sled B forward
    and the band stretches.
  - At the end of the push, a ramp on the bar (cam A) pushes the latch block in, and the
    band pulls the blade out.
  - The latch block clicks past the open catch. Then the lug runs into sled B, and the band
    stops the blade there.
- **Pulling the knob back.** The same happens the other way round. Cam B lets the blade go,
  and it clicks in at the closed catch.
- **The latch block.** It is a small separate part that slides in a slot in the blade. A
  springy arm in the blade pushes it out. It is separate so the band's pull and every knock
  go into the blade, never into the thin arm. The two catches hang from the lid.
- **Upside down.** Each sled has two small dovetail keys that run in a channel in the floor.
  They keep the sled straight, and stop it lifting into the latch parts when you hold the
  knife upside down.

## What to print

Everything is set up in the three project files. Open each one in Flash Studio with File →
Open Project, then check the slots in the Send dialog: 1 white, 2 black, TPU in slot 4.

1. **`1 slide test.3mf`**: the back end of the handle (base and lid), two short blade pieces
   (normal and loose), two screws and a latch block.
2. **`2 knife plates.3mf`**: three plates.
   - Handle base and lid, in black.
   - The blade and two latch blocks (one spare), in white.
   - The knob bar and knob in white; the two sleds and the three screws in black.
3. **`3 bands TPU.3mf`**: three bands, thin, normal and thick. Print all three; each is a few
   grams.

Each part has its print settings in the project already: hot and slow strong PLA, solid
moving parts, and brims on the long parts. Flash Studio shows the times once it slices.

## Step 1: the slide test

1. Screw the test lid onto the test base with the two screws. Use a coin; snug, not tight.
2. **The slide.** Slide the normal blade piece in from the cut end, groove down over the rib
   in the floor. Tilt the piece both ways.
   - **It slides in and out on its own:** good. Use `blade.stl`.
   - **It needs a push:** try the loose piece. If that one slides on its own, print
     `blade loose.stl` instead of the blade in project 2.
   - **Even the loose piece sticks:** stop and tell Claude where it rubs.
3. **The click.** Take the lid off and drop the latch block into its slot in the blade piece,
   with the wide end inside and the tooth sticking out. Press the springy arm aside with a
   fingernail to get it in. Put the lid back on.
4. Push the blade piece all the way in. It should click as the latch block rides over the
   catch, then not pull back out.
5. Push a toothpick down through the small window in the lid, beside the tooth, and press
   the tooth in. The piece should pull out again.

**Tell Claude how the slide test went** before printing the whole knife, especially if
anything sticks.

## Step 2: putting the knife together

Lay the base plate inside up, with the mouth (the slot the blade comes out of) away from you.

1. **Blade.** Lay it in the channel, groove down over the floor's rib, and push it all the
   way back.
2. **Latch block.** Drop it into its slot near the back of the blade, wide end inside,
   pressing the arm aside with a fingernail. It should spring back out.
3. **Sled F.** The dovetail channel in the floor beside the blade has short openings where
   the lips are cut away.
   - Drop sled F in at the first pair of openings, nearest the back, with its band pocket
     at the back.
   - Slide it forward until its front end is just behind the lug on the blade's side.
4. **Sled B.** Drop it in at the second pair of openings, just in front of the lug, with its
   band pocket at the front. Slide it forward about 7 mm.
5. **Knob bar.** Lower it in with its key in the groove along the outside of the floor. The
   long ramps (cams) go toward the blade.
   - Riser F, the post nearer the back, goes just in front of sled F.
   - Riser B goes just behind sled B.
   - Push the bar all the way back.
6. **Band.** Drop one head into sled F's back pocket. Stretch the band about 3 mm and drop
   the other head into sled B's front pocket, with the strand lying in the sleds' slots.
   Each sled now rests on its riser.
7. **Lid.** Put the lid on; the screw posts go into the round pockets. Turn the knife over
   and put the three screws in from the bottom. Use a coin; snug, not tight.
8. **Knob.** Push the knob's stem down through the slot in the lid into the hole in the bar.
   If it is loose, put a small drop of **gel** super glue on the end of the stem only. Thin
   glue would run down and glue the bar to the lid.

## Using it

- **Open:** push the knob forward all the way. Near the end you feel the latch let go, and
  the blade snaps out and clicks.
- **Close:** pull the knob back all the way. The blade snaps in and clicks.
- **Thumb cut-out:** the lid has a U cut out of its front end, over the blade. If the blade
  ever stops part way, press it with a finger there and push it back in.
- **If it's stuck out:** pull the knob back first, so the latch lets it go, then push.

## Which band

- **Start with the normal band.**
- **Blade doesn't make it out or in and lock every time:** fit the thick band.
- **The knob is too hard to push:** fit the thin band.
- TPU brands vary a lot in stiffness, which is why there are three. Rough sums for the push
  at the end of the stroke, from soft to stiff TPU:

  | Band | Push at the end |
  |---|---|
  | Thin | about 10–21 N |
  | Normal | about 11–25 N |
  | Thick | about 12–28 N |

  A firm thumb push is about 30 N.

## If something goes wrong

- **The blade sticks somewhere.** Take the lid off and slide the blade by hand. If it sticks
  with the lid off, it rubs the base; if only with the lid on, it rubs the lid. Then print
  `blade loose.stl`.
- **The blade won't lock out or in.**
  - Check the latch block springs out when you press it in and let go.
  - Check each sled is on its riser.
  - Then try the thick band.
- **The blade fires on its own while you push.** Tell Claude: the latch is slipping off its
  catch.

## Files

| File | What it is |
|---|---|
| `make_knife.py` | Draws every part and writes the STL and project files |
| `check_knife.py` | Checks the design. Its last run is in `out_check.txt` |
| `handle base.stl`, `handle lid.stl` | The handle |
| `blade.stl`, `blade loose.stl` | The blade. The loose one's groove is 0.15 mm wider each side |
| `latch block.stl`, `knob bar.stl`, `knob.stl` | Small parts |
| `sled F.stl`, `sled B.stl`, `screw.stl` | Small parts |
| `band thin.stl`, `band.stl`, `band thick.stl` | TPU bands: 1.2 mm wide, 1.05, 1.25 and 1.45 mm thick |
| `slide test *.stl` | The slide test's pieces |

## What the checks prove (and what they don't)

**Run with `python3 check_knife.py`.**

- **The whole cycle.** It walks the knife through push, throw out, pull and throw in. At
  every step it checks that no two parts overlap. It also tries each part pushed to either
  end of its play across: the blade, the knob bar, the sleds and the lid.
- **The latch.**
  - It holds by at least 0.95 mm at the worst.
  - Each cam pushes it clear about 0.7 mm before the end of the knob's travel.
  - It clicks in 1.35 mm before the blade's hard stop.
  - Between the two catches, nothing springy touches the blade.
- **Rough sums.** The band's pull, the thumb's push, and how much energy the band gives the
  blade compared with what friction can take on the way, using pessimistic friction.
- **Printing.** Each part is one piece, every flat face is on a layer line, everything fits
  on the bed, and the thin walls are at least two lines.

**What they don't prove:** how it feels in the hand. That is what the slide test is for.
