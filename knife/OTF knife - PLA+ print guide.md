# OTF fidget knife — printing it in PLA+ on the AD5X

I measured all three STLs. Good news: the model is well set up — every part is already
oriented correctly in the file, and the author is right that it needs no supports. Print
them exactly as they come out of the zip.

| Part | Size | Plastic |
|---|---|---|
| `handle.stl` | 108.5 × 28.6 × 9.4 mm | 6.7 cm³ |
| `slider.stl` | 97.5 × 31.4 × 8.5 mm | 5.3 cm³ |
| `blade.stl` | 105.1 × 21.7 × 2.5 mm | 2.9 cm³ |

All three fit on the bed at once. Figure on roughly **2–3 hours and 20 g** for the set.

---

## The two things that actually matter

### 1. The spring — switch the wall generator to Arachne

The slider's spring is a serpentine fin **2.2 mm thick standing 5.5 mm tall**. That
measurement is the whole ballgame, because 2.2 mm is an awkward number for a 0.4 mm
nozzle.

Your profile uses the **Classic** wall generator with a fixed 0.42 mm wall width. Two walls
fit on each side (1.68 mm), leaving a **0.52 mm gap down the centre of the spring** that
gets filled by a single squashed gap-fill line. That's a seam running the entire length of
the spring, and it's exactly where a flexing part tears itself apart.

**Fix: Quality → Wall generator → Arachne.** Arachne varies the wall width to fit, so it
lays four 0.55 mm walls that fill the 2.2 mm exactly — no seam, no gap. Same plastic, same
time, dramatically better spring. See `spring_walls.png`.

Belt and braces if you want it: set **infill to 100 %** on the slider. It's a tiny part,
it costs you almost nothing.

### 2. The handle sits on two knife edges — use a brim

The handle is two long rails with a channel between them, and the bottom edges are
chamfered. It touches the bed on **two strips about 1.1 mm wide**, which works out to only
~210 mm² of contact holding down a 108 mm long part. That will peel.

- **Brim on, 5 mm minimum.** Non-negotiable for this part.
- Slow the first layer down and don't let the fan touch it.

The slider and blade are fine — they're flat plates with 1300–1500 mm² of contact.

---

## Settings

Start from your `0.20mm Standard @FF AD5X` profile and change these:

| | Stock | Use | Why |
|---|---|---|---|
| **Wall generator** | Classic | **Arachne** | The spring. See above. |
| Walls | 2 | **4** | Everything is thin here; nothing is really "infill" |
| Infill | 15 % | **40 %** (slider **100 %**) | |
| Nozzle | 210 °C | **230 °C** | A flexing spring lives or dies on layer bonding |
| Part fan | 100 % | **50 %** | Enough to keep detail, not enough to stop the layers welding |
| Aux blower | 100 % | **off** | It was quenching every layer |
| Brim | auto | **on, 5 mm** | Handle especially |
| Supports | — | **off** | Genuinely not needed |
| Layer height | 0.2 mm | 0.2 mm | Fine as is |

The temperature and fan numbers are the same ones that fixed your sword blade — your stock
profile runs cool with both fans at full blast, which is the worst combination for anything
that has to flex or take a knock.

---

## If it doesn't work first time

**Parts bind / won't slide.** The design runs about 0.25 mm of clearance per side, which is
normal but leaves nothing for over-extrusion. Try a light sand on the blade edges first. If
it's still tight, scale the **blade** to 99.5 % and reprint — never the handle, since the
handle sets all the other dimensions.

**Too loose and rattly.** Scale the blade to 100.5 %.

**Spring snaps.** Almost always the Arachne thing above. If you already did that, the next
lever is temperature — go to 235 °C.

**Print a spare slider.** It's the part that fails, it's 5 cm³, and it costs you 20 minutes.
Cheapest insurance there is.

---

## A note on the blade

The remixer says he shaved it down and you may want to sand it. It's a 2.5 mm flat plate,
105 mm long, so it will have some flex — that's inherent to the design, not a print
problem. PLA+ is a good choice here: it's stiffer than PETG, and since nothing on this
model takes a real impact, brittleness isn't the concern it was on the sword.

Licence on the model is CC BY-NC-SA — fine for printing for yourself, just not for selling.
