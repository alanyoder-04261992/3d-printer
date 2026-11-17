# Light iPhone 15 Pro case: read me first

A TPU case made from as little material as does the job, in three designs. All three have:
- **The same sides:** 1.5 mm walls, soft chamfered edges and a raised lip round the screen.
- **Covered buttons that press easily:** a raised pad over each button, set in a thinned wall
  (see below).
- **A mostly open back:** solid TPU stays only where it does a job:
  - a band inside the walls;
  - a frame round the camera;
  - a frame round a 57.5 mm MagSafe opening. A MagSafe charger (55.9 mm across) drops in and sits
    right on the phone.
- **Two dust plugs:** one for the charging port, one for the speaker.

**Not printed yet (Nov 17 2026).**

## The three designs

| Web | Honeycomb | Ripple |
|---|---|---|
| ![Web](picture%20web.png) | ![Honeycomb](picture%20honeycomb.png) | ![Ripple](picture%20ripple.png) |
| A Voronoi web of 1.6 mm struts, like a leaf's veins | Regular hexagons, 8 mm across | Rings rippling out from the MagSafe opening, broken by 10 spokes |
| About 14.7 g of TPU | About 14.1 g | About 14.4 g |

Each design is on its own plate in the project file, with the dust plugs.

## The buttons

![The buttons](picture%20buttons.png)

Cut-outs can be hard to press, so each button is covered by a pad you press instead.
- **The pad:** stands 0.6 mm proud of the side, so your thumb finds it without looking.
- **The wall round it:** thinned from inside to 0.65 mm over the button and 3 mm round it, so the
  thin TPU spans 2.8 mm above and below the pad. That thin band bends, not the pad, so the pad
  moves in with a light press.
- **Inside:** the pad stops about 0.1 mm short of the phone's button, so it doesn't press the
  button on its own, but reaches it straight away when you press.
- **How light, roughly:** about 1 to 4 N more than the phone's own click. The Action button is
  the lightest; the long side button is the firmest. That is about a tenth of a 0.95 mm wall, and
  less again than the full-thickness bump on the case you printed before. These are sums from
  TPU's stiffness, not a measurement. If a pad feels stiff, tell Claude which one.
- **Which buttons:**
  - the side button on the right;
  - volume down, volume up and Action on the left, each with its own pad.

The button positions are the middle of the openings on the v5 case and of the button pockets on
the case you printed. The two agree to 0.2 mm.

## The dust plugs

![The dust plugs](picture%20plugs.png)

Each plug presses into the case's opening and has a thin flange outside.
- **USB-C plug:** fills the charging opening. It doesn't go into the phone's port, so it can't
  harm it.
- **Speaker plug:** fills the speaker opening. It muffles the speaker while it's in.
- **Getting them out:** each has a small nick in the flange to lift it with a fingernail.
- **Spares:** each plate has one spare of each.

The microphone opening is left open, so calls still work.

## What to print

Open **`iphone 15 pro case TPU.3mf`** in Flash Studio with File → Open Project. It has three
plates, one per design, each with the case and the four dust plugs. Print the plate for the
design you want.

It is all on filament 1, set to Generic TPU (240 °C, bed 35 °C). Put TPU in a slot and pick that
slot in the Send dialog.

- **The case prints back face down.** The back's pattern is just the first few layers on the
  bed, so it needs no supports.
- **No brim:** it would have to be peeled off soft TPU.
- **Solid:** 4 walls and 100 % infill, so the thin parts are solid TPU.

Flash Studio shows the time when it slices. The TPU case you printed before took about 1½ hours.

## The design in numbers

| | |
|---|---|
| Size | 75.1 × 149.9 × 11.25 mm, button pads included. The phone is 70.6 × 146.6 × 8.25 |
| Walls | 1.5 mm at the sides. The back is 1.25 mm, with the pattern and the MagSafe opening cut through it |
| Screen lip | Stands 1.6 mm over the screen and reaches 1.45 mm in over its edge, sloped at 45 degrees |
| Fit | 0.15 mm of room all round. TPU stretches, so the case pulls snug |
| Bottom | USB-C, speaker and microphone openings, widened 1 mm at the outside |
| Camera | An opening about 0.5 mm bigger all round than the one on the case you printed, its edge cut at 45 degrees |
| MagSafe | A 57.5 mm opening at the middle of the back. A MagSafe charger drops in and sits right on the phone. A wallet or stand is bigger than the opening, so it rests on the case round it, through 1.25 mm of TPU |

## Where the measurements come from

Apple gives the phone's size. The button, port and camera positions came from the two
iPhone 15 Pro cases already in `desktop prints`:
- the one you printed in TPU, `iPhone 15 Pro case - Case.stl`;
- `iphone 15 Pro v5.stl`.

## If something's off

- **Too tight or too loose:** tell Claude. The fit is one number (`FIT` in `make_case.py`).
- **A button presses on its own, or is hard to reach:** tell Claude which one. The pad's gap is
  one number (`PAD_GAP`).
- **An opening or pad doesn't line up:** tell Claude which one, and which way it's out and by
  about how much.
- **The charger doesn't drop into the MagSafe opening:** tell Claude. Moving or widening the
  opening is one setting.
- **The camera:** the lenses stand out past the back of the case, as on your last case.

## Files

| File | What it is |
|---|---|
| `make_case.py` | Draws the cases and plugs, and writes the STL and project files |
| `iphone 15 pro case TPU.3mf` | The project to print: one plate per design |
| `case web.stl`, `case honeycomb.stl`, `case ripple.stl` | The three cases on their own |
| `plug USB-C.stl`, `plug speaker.stl` | The dust plugs |
| `picture *.png` | The pictures above |
