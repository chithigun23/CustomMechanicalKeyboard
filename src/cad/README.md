# Case, plate and knob — CustomMechanicalKeyboard

Single-piece tray case with an open top, a drop-over switch plate, and a knob for
the EC11. Every coordinate is read out of `KiCAD/keyBoard/keyboardKiCad.kicad_pcb`
at build time, so the parts track the real board rather than a redrawn copy.

## Files

| File | What it is |
|---|---|
| `out/keyboard_case.step` / `.stl` | The case, **Ø4.0 heat-set pockets** — for printing. 361.8 × 139.8 × 20.5 mm |
| `out/keyboard_case_cnc_tapped.step` | Same case with **Ø2.5 tapping holes** — upload this one to JLC |
| `out/keyboard_plate.step` / `.stl` | Switch plate. 357.2 × 135.2 × 3.6 mm (1.4 plate + 2.2 collars) |
| `out/encoder_knob_D_shaft.step` / `.stl` | **This is the one** — D bore matched to your 10 mm flat |
| `out/encoder_knob_cnc_grubscrew.step` | Round bore + M3 grub screw — **the machinable knob**, see below |
| `out/encoder_knob_round.step` / `.stl` | Plain round bore, no grub screw, spare |
| `out/assembly_print.step` | Printed config in position (heat-set case + D-bore knob) |
| `out/assembly_cnc.step` | Machined config in position (tapped case + grub-screw knob) |
| `out/keyboard_plate_flat.dxf` / `.svg` | Plate flat pattern, if you'd rather have it cut from metal |
| `keyboard_cad.py` | The model. All parameters are at the top |
| `verify.py` | 40-odd clearance checks — run after changing any parameter |

Rebuild with `python keyboard_cad.py`, then `python verify.py`.

Finished files are split across two folders under Desktop/keyboardProject:
**CNC Files** (the three parts to upload to JLC, plus a reference assembly) and
**3D Print Files** (STLs and their STEP sources, plus the flat DXF, which is
not part of the order). Each folder has a `_READ ME FIRST.txt` with the
settings, hardware list and gotchas for that route.

## Measurements this is built on

Yours, quoted from the **PCB bottom** face (the model works from the PCB top, so
it subtracts the 1.6 mm board thickness):

| Measured | From PCB bottom | Above PCB top | Used for |
|---|---|---|---|
| USB-C housing, top | 9.0 | 7.40 | USB opening height |
| Keycap top, unpressed | 13.2 | 11.60 | — |
| Keycap top, pressed | 10.0 | 8.40 | **sets the plate top** |
| Keycap height (rim to top) | — | 4.40 | **sets the plate top** |
| EC11 stem top, D type | 26.4 | 24.80 | knob height, bore depth |
| EC11 flat length | 10.0 | flat spans 14.80 → 24.80 | **where the bore is keyed** |
| Keycap footprint | 16.0 × 17.0 | — | wall clearance |

The USB figure is a useful cross-check: the model predicted 7.40 mm from a
2.54 mm header stack plus a 1.6 mm daughterboard plus a 3.26 mm receptacle, and
your 9.0 − 1.6 = 7.40 agrees exactly, so the daughterboard stack height is confirmed.

And from the KiCad files and the vendor STEP models:

| Measurement | Value | Consequence |
|---|---|---|
| Board outline | 354 × 132, R10, 1.6 thick | Case pocket 354.8 × 132.8 |
| Mounting holes | 18 × Ø3.2 | 18 M3 bosses; ≥7.3 mm clear radius at every one |
| Switches | 83 × Kailh Choc V2, 18 × 17 mm pitch | Body is 15.0 × 15.0 |
| Stabilisers | 4 × Cherry PCB-mount (2u ×2, 3u, 6.25u) | Wire runs at 0.79–2.39 mm above the PCB |
| Diodes | 83 × DO-35 | Top out 1.80 mm up, all under solid plate |
| MCU board | 29.8 × 29.0, stacked **above** the main PCB | Bay in the plate; USB-C above the plate line |

## The three things that shaped the design

**The plate cannot clip onto the switches.** They're soldered, so it has to drop
down over them. Cutouts are **15.6 mm** (0.3 mm clearance around the 15.0 mm
Choc V2 body) rather than the 14.5 mm a clip-in plate would use. It's held by
the screws, not by the switches.

**The plate is squeezed from both sides, hard.** A bottomed-out keycap's rim
reaches 8.40 − 4.40 = **4.00 mm** above the PCB, and because the caps are 17.0 mm
deep on a 17.0 mm row pitch they touch edge to edge — the plate web between rows
sits directly under the cap rim, so there is nowhere to route around it.
Underneath, the stabiliser wire runs up to 2.39 mm and all 83 diodes top out at
1.80 mm. The plate therefore sits at **2.2 → 3.6 mm**, leaving **0.40 mm** under
a bottomed-out cap. Relief pockets 0.6 mm deep in the underside clear the stab
wire by 0.41 mm and the diodes by 1.00 mm — the diode height is the only figure
in the stack that's nominal rather than measured, so that's where the slack went.

**The encoder's flat is only on the top 10 mm.** Below 14.80 mm the shaft is
round, so a full-height D bore would jam on the round section before the knob
seated. The bore is round Ø6.2 up to 15.10 mm and keyed above it, giving 9.7 mm
of engagement along the flat.

## Vertical stack

```
 20.5  top of the back and side walls
 14.2  plate top  ← front wall is here, ramping up to 20.5 between Y 26 and 62
 12.8  plate underside          (2.2 above the PCB)
 10.6  PCB top face
  9.0  PCB underside / top of the 18 bosses
  3.0  inside of the floor      (6.0 mm of space for solder tails)
  0.0  outside of the floor
```

The front wall stops at the plate line and ramps up to full height toward the
back, so there is no lip in front of the spacebar.

## Assembly

1. **Heat-set 18 × M3 inserts** into the bosses. Pockets are Ø4.0 × 5.0 deep.
   Measure yours first — brass M3 inserts run Ø4.0 to Ø4.6; if yours are larger,
   change `INSERT_D` and rebuild. The pocket is blind, so nothing shows outside.
2. Drop the PCB in. It lands on the bosses; the pocket locates it with 0.4 mm
   clearance per side.
3. Lower the plate over the switches. The 18 collars on its underside sit on the
   PCB and set the 2.2 mm gap; the rim lands on the internal ledge. It should go
   down without force — if it rocks, something underneath is proud.
4. **18 × M3 × 10 countersunk** screws from the top, through the plate and PCB
   into the inserts. Grip is 5.2 mm plus 5.0 mm of thread engagement.
5. Press the knob on, lining the flat in the bore up with the flat on the shaft.
6. Six Ø14 × 1.0 recesses in the underside take stick-on rubber feet.

### BOM

- 18 × M3 heat-set insert (OD 4.6 × 5.7 — the Ø4.0 × 6.2 hole is deliberately
  smaller than the insert; that is how heat-set inserts work)
- 18 × M3 × 10 countersunk (90°) machine screw
- 6 × Ø12–14 self-adhesive rubber foot

## Printing

Nothing needs support. The case is 362 × 140 mm, so it needs a 400 mm-class bed
(or a 350 with the part rotated — it's 388 mm on the diagonal).

- **Case**: floor down, 0.2 mm layers, 4 perimeters, ≥25% infill.
- **Plate**: face down, so the relief pockets are on the top during printing and
  need no bridging. At 1.4 mm over a 354 mm span it will feel flexible before
  it's bolted down — expected, and it stops mattering once it's on the 18 collars
  and the perimeter ledge. PETG or ABS over PLA. Thinnest web is 1.14 mm, next to
  the Caps Lock stabiliser, so use a 0.4 mm nozzle. **Do not increase `PLATE_T`** —
  there is only 0.40 mm over it before keycaps start landing on the plate.
- **Knob**: flat end down, no support. The 24 flutes print cleanly.

## CNC at JLC

Kept machinable on purpose: no undercuts, radiused internal corners, nothing
needs 5-axis. Upload the `.step` files, not the STLs. Three DFM changes were
made specifically for machining — see "What changed for CNC" at the bottom.

### Case — upload `keyboard_case_cnc_tapped.step`

| Setting | Value |
|---|---|
| Material | **Aluminium 6061-T6** (6082 if cheaper in your region) |
| Finish | **Bead blast + black anodise, Type II** |
| Tolerance | ISO 2768-m (JLC default) is fine — see the callouts below |
| Threads | **M3 × 0.5, 18 places, 5 mm minimum full thread** |
| Deburr | Break all sharp edges 0.2 mm |
| Quantity | 1 |

Finished mass ≈ **534 g** in 6061. Stock will be 25 mm plate (the part is
20.5 mm tall), roughly 368 × 146 × 24.5 mm, and about **1116 cm³ — 85 % of the
block — gets removed.** That is the dominant cost of the whole project; there is
no way around it for a tray case.

Notes to put in the order comments:

- *"18 × Ø2.5 holes to be tapped M3 × 0.5, 5 mm min full thread."*
- *"Threads to be free of anodise, or chased after anodising."*
- *"Pocket 354.8 × 132.8 must not be undersize (+0.3 / −0)."* It's the PCB seat.
- *"Boss top faces to be 9.00 ± 0.1 from the outer bottom face."* This one feeds
  straight into the 0.40 mm of keycap clearance, so it is the tightest thing in
  the part.
- *"Internal corners where the boss ribs meet the wall may be radiused up to R2."*

Don't use powder coat — at 60–100 µm it is thick enough to matter in the PCB
pocket. Anodising at 10–25 µm costs about 0.05 mm across the pocket, which is
nothing against the 0.8 mm of clearance. Skip polishing too; it shows every tool
mark on a face this large.

### Plate — upload `keyboard_plate.step`

| Setting | Value |
|---|---|
| Material | **Aluminium 6061-T6** |
| Finish | Bead blast + anodise (black to match, or clear for contrast) |
| Tolerance | ISO 2768-m, **except the outline** — see below |
| Deburr | **Essential.** 89 through-cutouts, both faces |
| Quantity | 1 |

Mass ≈ **95 g** in 6061 (brass would be 300 g, 304 stainless 280 g, if you want
the extra heft and don't mind the cost).

- *"Outline 357.2 × 135.2 must not be oversize (−0.3 / +0)."* It drops into a
  357.8 pocket, so 2768-m's ±0.5 at that size could leave it 0.05 mm oversize
  and it wouldn't go in.
- The 15.6 mm switch cutouts are safe at 2768-m — even 0.2 mm undersize still
  clears the 15.0 mm switch bodies.
- It's a 1.4 mm part with 89 holes, so it is floppy in the vice. Expect the shop
  to use tabs or vacuum; ask for *"tab witness marks on the underside only."*

Machining this part removes 86 % of a 5 mm plate and it has 89 cutouts + 87
relief pockets + 18 countersinks, so per gram it is the most expensive of the
three. `keyboard_plate_flat.dxf` exists as a laser/waterjet alternative, **but
read this before using it**: a flat-cut plate has no relief pockets, so it must
sit 2.7 mm up to clear the stabiliser wire, which puts its top at 4.1 mm — 0.1 mm
*above* where a bottomed-out keycap reaches. It only works if you drop to 1.0 mm
stock. Machining the plate as modelled is the version that actually satisfies all
three constraints at once.

If you want to cut cost, `DIODE_RELIEF = False` removes 83 of the 87 pockets.
The plate then clears the diodes by 0.40 mm instead of 1.00 mm — fine if you are
confident every diode is seated flat, not worth it otherwise.

### Knob — upload `encoder_knob_cnc_grubscrew.step`

| Setting | Value |
|---|---|
| Material | **Brass H62** (37 g, nice contrast) or 6061 anodised to match (12 g) |
| Finish | Brass: as-machined or polished. Aluminium: bead blast + anodise |
| Tolerance | ISO 2768-m |
| Threads | **M3 × 0.5 grub screw hole, 1 place** |
| Quantity | 1 |

**Use the grub-screw version, not the D-bore one.** The D bore needs a flat
milled inside a Ø6.2 blind bore 20 mm deep — a 5:1 reach with a stub end mill,
which a shop will either surcharge or reject at DFM review. The grub-screw
version is a plain round bore plus an M3 set screw that clamps onto the shaft's
flat, which is how commercial knobs do it. It is also removable, which the
interference-fit D bore isn't.

The grub screw sits 20.3 mm above the PCB — 55 % of the way up the shaft's 10 mm
flat — with 6.9 mm of thread through the wall, tucked between two flutes. You'll
need **1 × M3 × 6 set screw** (cup point, hex 1.5 mm). The hole is counterbored
Ø3.2 × 3.0 with only the inner 3.9 mm tapped, because the wall is 6.9 mm thick
and the shaft flat is 8.5 mm in — a screw short enough to sit flush in a fully
tapped hole could never reach the flat.

Keep the D-bore STL for printing; it needs no hardware there.

### What changed for CNC

1. **16 of the 18 bosses now blend into the wall.** As free-standing islands
   they sat 1.4–1.9 mm from the pocket wall, i.e. a 6 mm deep slot needing a
   ~1.2 mm cutter at 5:1. The ribs live under the PCB so they cost nothing, and
   they print better too.
2. **The ledge dropped 0.15 mm** below the plate underside, so the plate always
   lands on the 18 collars rather than on the ledge. Without it, a ledge machined
   0.2 mm high would lift the plate and eat half the keycap clearance — this
   removes a tolerance you would otherwise have had to pay for.
3. **The knob gained a grub-screw variant**, above.

## Note on the knob proportions

Ø20 × 21.3 mm, which is tall for a keyboard knob. That's set by the shaft: it
ends 24.8 mm above the PCB, 10.6 mm above the plate, and the knob covers it
completely rather than leaving the tip out. If you cut the shaft down, set
`M_ENC_STEM_TOP` to the new figure and the knob height follows automatically —
but note `M_ENC_FLAT_LEN` then shortens too, so cut from the top and remeasure
both. Ø20 × ~14 mm looks more conventional.
