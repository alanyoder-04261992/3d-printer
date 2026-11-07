# Spring knife toy — read me first

A fidget toy designed from scratch (Nov 2026), to replace the spring knife from the Flashforge
app. Press the **back button** on the side and two printed TPU bands snap the blade out until
it locks open. Press the **front button** and push the blade back in until it clicks; that
stretches the bands again for the next go.

It's a toy: the blade is 4 mm thick plastic with round edges and a round tip. It does come out
with a snap, so point it away from faces.

| | |
|---|---|
| Handle | 165 x 30 x 15 mm, finger scallops on the side away from the buttons |
| Blade out | 79 mm |
| Spring | two TPU bands round two rollers, no metal spring |
| Hardware | 4 x **M3 x 16 mm** screws (any hardware store) |

## What to print

Open these from inside Flash Studio (File → Open Project).

| File | What's on it | Filament |
|---|---|---|
| `1 knife plates.3mf` plate 1 | Both handle halves, the pin, two rollers | Black (filament 2) |
| `1 knife plates.3mf` plate 2 | The blade, with its latch arm | White (filament 1) |
| `2 bands (TPU).3mf` | Two bands | **TPU**: before slicing, click filament 1 and pick your TPU preset (Generic TPU) |

Both projects already use 0.20mm Standard with **Arachne**, which the thin band walls and
buttons need. In the Send dialog, check the slots by number (1 white, 2 black).

The bands come in two strengths. `band.stl` (1.0 mm) is on the plate. If the blade comes out
lazily, print `band firm.stl` (1.3 mm) instead.

## Putting it together

1. **Rollers.** Drop a roller over the front post in each handle half.
2. **Bottom band.** In the bottom half, put one band's single eye over the back post, and wrap
   the loop round the roller.
3. **Blade.** Push the pin through the hole in the carrier so it sticks out both sides. Lay
   the blade in the bottom half **open**: blade out through the front, carrier against the
   front wall. Hook the bottom band's free eye over the bottom of the pin. Open, the bands are
   barely stretched, so this is easy.
4. **Top band.** Hook the second band's free eye over the top of the pin. Lay it forward
   along the blade, put the top half's roller inside its loop, and rest its back eye at the
   back of the handle.
5. **Top half.** Lower it straight down. The pointed posts find the back eye and the roller.
   If something won't sit flat, lift it and look; don't force it.
6. **Screws.** Four M3 x 16 mm screws from the top. Snug, not tight; they cut their own
   thread in the plastic.
7. **First close.** Press the front button and push the blade's tip against your palm until
   it clicks. Press the back button: it should snap out.

## If it doesn't work right

- **Blade sticks partway out:** the bands are too weak. Print the firm pair.
- **Won't stay closed:** look in the back window on the button side. The latch tooth should be
  sitting in it. If the blade slides a little in and out, the tooth isn't catching. Tell
  Claude and the tooth can be made deeper.
- **Button won't fire it:** press the middle of the tab, right over the window.

## How it was checked

`make_knife.py` makes every part from the numbers at the top of the file. `check_knife.py`
proves:

- the blade slides its whole 86 mm without rubbing;
- the tooth locks it shut and locks it open;
- each button presses in far enough to free the tooth, with room behind it;
- the latch arm and buttons bend under 1 % (PLA is fine under 2 %);
- the bands, pin and rollers stay clear all the way;
- every hole is 0.4 mm bigger all round than its pin;
- every height sits on a layer line.

Nothing has been printed yet.
