# Minimal iPhone 15 Pro case: read me first

A slim TPU case with soft chamfered edges and a raised lip round the screen. The buttons are
open, so you press the phone's own buttons. On the back, the MagSafe ring is cut in as a groove,
with three thinner rings rippling out from it. Two TPU dust plugs come with it.

**Not printed yet (Nov 17 2026).**

![The back](picture%20back.png)
![The buttons](picture%20buttons.png)
![The dust plugs](picture%20plugs.png)

## What to print

Open **`iphone 15 pro case TPU.3mf`** in Flash Studio with File → Open Project. It has:
- the case;
- two USB-C plugs;
- two speaker plugs (one of each is a spare).

It is all on filament 1, set to Generic TPU (240 °C, bed 35 °C). Put TPU in a slot and pick that
slot in the Send dialog.

- **The case prints back face down**, so the rings on the back come out crisp.
- **No brim:** it would have to be peeled off soft TPU.
- **Solid:** 4 walls and 100 % infill, so the thin walls are solid TPU.

Flash Studio shows the time when it slices. The TPU case you printed before took about 1½ hours.

## The design

| | |
|---|---|
| Size | 73.9 × 149.9 × 11.25 mm. The phone is 70.6 × 146.6 × 8.25 |
| Walls | 1.5 mm at the sides, 1.25 mm on the back |
| Screen lip | Stands 1.6 mm over the screen and reaches 1.45 mm in over its edge, sloped at 45 degrees |
| Fit | 0.15 mm of room all round. TPU stretches, so the case pulls snug |
| Buttons | Open cut-outs that widen 1 mm at the outside at 45 degrees, so your thumb finds them. The side button has its own slot. Both volume buttons share one long slot, and the Action button has its own |
| Bottom | USB-C, speaker and microphone openings, also widened at the outside |
| Camera | An opening about 0.5 mm bigger all round than the one on the case you printed, its edge cut at 45 degrees |
| MagSafe | The back is 1.25 mm of TPU, thin enough for MagSafe chargers and wallets to grip through. The groove on the back (56 mm across) shows where a MagSafe charger sits |

## The dust plugs

Each plug has a body that presses into the case's opening and a thin flange outside.
- **USB-C plug:** fills the case's charging opening. It doesn't go into the phone's port, so it
  can't harm it.
- **Speaker plug:** fills the speaker opening. It muffles the speaker while it's in.
- **Getting them out:** each has a small nick in the flange to lift it with a fingernail.

The microphone opening is left open, so calls still work.

## Where the measurements come from

Apple gives the phone's size. The positions of the buttons, ports and camera came from the two
iPhone 15 Pro cases already in `desktop prints`:
- the one you printed in TPU, `iPhone 15 Pro case - Case.stl`;
- `iphone 15 Pro v5.stl`.

Both put the camera in exactly the same place. The button and port openings follow the v5
case, which has them, with a little more room.

## If something's off

- **Too tight or too loose:** tell Claude. The fit is one number (`FIT` in `make_case.py`).
- **An opening doesn't line up with a button or the port:** tell Claude which one, and which way
  it's out and by about how much.
- **The camera:** the lenses stand out past the back of the case, as they did on your last case.
  If you want a raised ring round the camera, say so. It needs supports, or a separate ring
  glued on, because the case prints back face down.

## Files

| File | What it is |
|---|---|
| `make_case.py` | Draws the case and plugs, and writes the STL and project files |
| `iphone 15 pro case TPU.3mf` | The project to print |
| `case.stl`, `plug USB-C.stl`, `plug speaker.stl` | The parts on their own |
| `picture *.png` | The pictures above |
