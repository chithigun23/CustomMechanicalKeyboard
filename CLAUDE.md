# CustomMechanicalKeyboard — case, plate, knob, and assembly renders

Custom 83-key + rotary-encoder mechanical keyboard. The PCBs and firmware already
exist and work (`github.com/chithigun23/CustomMechanicalKeyboard`). This project
adds two things on top:

1. **A case, switch plate and encoder knob** — finished, files are order-ready.
2. **A Blender assembly animation** — in progress, 1 of 5 stages done.

Everything geometric is derived from the KiCad files rather than redrawn, so the
parts track the real boards.

---

## Layout

**This folder is the git clone of the keyboard repo.** `KiCAD/` at its root is
the single source of truth for all geometry — the CAD, the GLB exports and the
renders are all derived from it. Don't copy it anywhere; point at it.

```
keyboardProject/            <- git clone of CustomMechanicalKeyboard
  CLAUDE.md                 this file
  KiCAD/                    the boards + footprint/3D libraries  (upstream)
  Datasheets/  gerbers/     upstream
  CNC Files/                3 STEPs to upload to JLC + order notes  (order-ready)
  3D Print Files/           STLs + STEP sources + plate DXF          (print-ready)
  Render/                   double-click kit to render the finished animation
  src/
    cad/                    keyboard_cad.py (the model), verify.py (~40 checks)
    render/                 Blender pipeline, GLB exports, .blend files
```

`src/render/config.py` resolves every path relative to itself, so the tree can
live anywhere, and auto-finds `kicad-cli.exe` and `blender.exe`. Run
`python src/render/config.py` to self-check that everything resolves.

**Tooling:** Blender 5.2, KiCad 10.99 CLI, Python with `build123d` (CAD only).

---

## Hardware facts — measured, do not re-derive

From the KiCad files:

| | |
|---|---|
| Keyboard PCB | 354 × 132 mm, R10 corners, 1.6 thick, **black** soldermask |
| MCU daughterboard | 29.8 × 29.0 mm, R3.5, **blue** soldermask, stacks **above** the main PCB |
| Mounting holes | 18 × Ø3.2, ≥7.3 mm clear radius at every one |
| Switches | 83 × Kailh Choc V2, **18 × 17 mm** pitch, body 15.0 × 15.0 |
| Stabilisers | 4 × Cherry PCB-mount (2u ×2, 3u, 6.25u) |
| Diodes | 83 × DO-35, all under solid plate, top out 1.80 above the PCB |
| Encoder | EC11 at CAD (338, 116) |

Measured off the real hardware, quoted **from the PCB bottom** (the CAD works
from the PCB top, so it subtracts the 1.6 board thickness):

| | from PCB bottom | above PCB top |
|---|---|---|
| USB-C housing top | 9.0 | 7.40 |
| Keycap top, unpressed | 13.2 | 11.60 |
| Keycap top, pressed | 10.0 | 8.40 |
| Keycap height, rim to top | — | 4.40 |
| EC11 stem top (D type) | 26.4 | 24.80 |
| EC11 flat length | 10.0 | flat spans 14.80 → 24.80 |
| Keycap footprint | — | 16.0 × 17.0 |
| Keycaps | orange PLA, 3D printed | |

---

## Case — finished

Single-piece tray case, open top, 361.8 × 139.8 × 20.5 mm. Front wall stops at
the plate line and ramps up to full height between Y 26 and 62.

**The three constraints that shaped it:**

1. **The plate cannot clip onto the switches** — they're soldered, so it drops
   over them. Cutouts are 15.6 mm, not the usual 14.5.
2. **The plate is squeezed from both sides.** A bottomed-out keycap rim reaches
   4.00 above the PCB, and caps are 17.0 deep on a 17.0 row pitch so they touch
   edge to edge — the plate web between rows sits directly under the rim, with
   nowhere to route around it. Underneath, the stab wire runs to 2.39 and the
   diodes to 1.80. Plate therefore sits **2.2 → 3.6**, leaving **0.40 mm**.
   **Never increase `PLATE_T`.** 0.6 relief pockets clear the wire and diodes.
3. **The encoder flat is only the top 10 mm** — below 14.80 the shaft is round,
   so a full-height D bore would jam before seating.

**Vertical stack** (from the outside of the case floor):
```
20.5  wall top      14.2  plate top      12.8  plate underside
10.6  PCB top        9.0  PCB underside / boss tops
 3.0  floor inside   0.0  floor outside
```

Rebuild: `python src/cad/keyboard_cad.py` then `python src/cad/verify.py`
(0 failures, 0 warnings expected).

**Hardware:** 18 × M3×10 CSK Torx T10 (with plate) or M3×6 button (without),
1 × M3×10 grub screw for the knob, 6 rubber feet, plus 18 × M3 heat-set inserts
(OD 4.6 × 5.7) on the printed route only.

---

## Renders — stage 1 of 5 done

**Vision:** components fly in onto the MCU PCB → MCU PCB onto the keyboard PCB →
each switch flies in → the assembly drops into the case with plate and knob →
keycaps drop on.

**Done:** the MCU assembly. 25 separately-animatable objects (board + 24
components, named `MCU_<refdes>`), 250 frames at 30 fps = 8.3 s, 1920×1080,
EEVEE, 96 samples. Components fall from above; J1 and CNN1 rise up through the
floor. Camera orbits 26°.

**How the geometry gets in:** `kicad-cli pcb export glb` — the board comes in as
real geometry (copper, pads, silkscreen, mask), not textures. The bare board is
exported once, then each component separately with `--component-filter`, all in
one shared coordinate frame, so importing them all without moving anything puts
every part exactly where it belongs.

**Look:** bright white studio, house exposure baked into `bl_studio.py`
(`WHITE_INTENSITY = 0.90`, `WHITE_EXPOSURE = -0.45`, `WHITE_LOOK = "AgX - Punchy"`).
Later stages inherit it automatically.

**Scripts** (`src/render/`):
```
config.py           paths, tool discovery
bl_studio.py        lights, camera framing, exposure
bl_materials.py     PCB material roles, JLC colour palette
list_mcu.py         parse a board's footprints -> mcu_parts.json
export_mcu.py       one GLB per object via kicad-cli
bl_import_mcu.py    GLB -> named Blender objects, mm scale
bl_animate_mcu.py   builds the animation -> mcu_anim.blend
bl_render_mcu.py    still renders
```

---

## Gotchas that already cost time — don't rediscover these

- **Board files are KiCad 10.99 format.** The 10.0 CLI refuses them. Use the
  nightly for GLB export; GLB is neutral so the usual "nightly writes files 10.0
  can't open" caution doesn't apply. Export is read-only — checksum the input.
- **glTF imports in metres and parks component placement on parent empties.**
  Delete the empties without applying their transform and all 24 parts collapse
  onto the origin. Scale ×1000 for mm.
- **KiCad's GLB material slots are anonymous** (`mat_0`..`mat_6`) and their roles
  are *not* what the Z-order suggests. Established empirically: **slot 6 is the
  board face**, 0/1 pads, 2/3 silkscreen, 4/5 mask-over-copper (reads as faint
  raised traces). Colouring slot 4 gives blue *traces on a tan board*.
- **KiCad exports boards semi-transparent** (mask alpha 0.83, substrate 0.98,
  BLEND) so viewers can see inner layers. Left alone the board looks translucent
  and vias show through. `bl_materials.opaque()` forces alpha 1.0.
- **Parenting a camera to an orbit pivot silently collapses it onto the pivot**
  if you assign `matrix_world` after setting `.parent` — the parent matrix is
  stale in background mode. Use `matrix_parent_inverse` after a
  `view_layer.update()`. There's an assert guarding this now.
- **Blender light energy is watts and assumes metres.** In a mm scene a light 45
  units away is treated as 45 m away. `bl_studio.add_area()` takes a target
  irradiance and solves the wattage.
- **Blender 5.2 renamed EEVEE Next back to `BLENDER_EEVEE`**, and the AgX look is
  `"AgX - Base Contrast"` / `"AgX - Punchy"`, not `"AgX - Medium Contrast"`.
- **Check renders numerically before eyeballing them.** Measuring the fraction of
  non-background pixels caught 250 frames of empty grey instantly.
- **Bash heredocs here eat backslashes.** Write Python to a file rather than
  piping it inline, or a `\f` in a string becomes a form feed.

---

## Next: stage 2 — the keyboard PCB

Same pipeline, pointed at `src/kicad/keyBoard/keyboardKiCad.kicad_pcb`, with
`mask=M.JLC_BLACK`. Watch for:

- ~172 components (83 switches, 83 diodes, 4 stabs, encoder, connector) — that's
  172 `kicad-cli` invocations for separate objects. Fine, but not instant.
- The board is 354 × 132, roughly 50× the MCU board's area. With full copper the
  mesh could get very heavy — the 30 mm MCU board alone was 5.8 MB / 130 k verts.
  Fall back to dropping `--include-tracks` (keeping pads and silk) if it bogs
  down; at whole-keyboard framing individual traces are sub-pixel anyway.
- The house exposure was tuned against a *blue* board. Black reflects far less,
  so it may want more light or a stronger rim to keep its edges off the shadow
  side. Check rather than assume.
