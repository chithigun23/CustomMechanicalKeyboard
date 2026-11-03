PLATE + STABILISER PARTS, ONE PLATE, PRUSA XL (5 TOOL, TOOL 3 ONLY)
===================================================================

keyboard_plate_stabs_XL_IS_tool3_PLA.gcode   ready to print, ASCII g-code
PrusaSlicer_XL5T_IS_tool3_PLA_0.15_settings.ini  full resolved settings (PrusaSlicer 2.9.6)

Printer   Original Prusa XL - 5T Input Shaper 0.4 nozzle profile, tool 3 only (T2 in the g-code)
Filament  Prusament PLA @XLIS, 230 C first layer then 225 C, 60 C bed
Quality   0.15mm SPEED @XLIS 0.4 (Prusa has no QUALITY preset for Input Shaper), 3 perimeters
Supports  auto, build plate only, threshold 40 deg (only the stabiliser parts need them)
Estimate  3 h 01 m, 49.8 g

LAYOUT
------
The plate is printed top face down (relief pockets and collars face up) and
rotated 45 degrees so the 357 mm part fits the 360 mm bed with about 10 mm
margin. The four stabiliser sets sit in the two free corners:
2u x2, 3u x1, 6.25u x1 = 4 wires, 8 sliders, 8 housings.

NOTES
-----
- The stabiliser parts come from the KiCad 3D models in KiCAD/kbProjectLib/3d.
  They are laid out as separate parts, not as an assembled stabiliser. The
  sliders were repaired (the STEP solid is invalid) and are about 0.07 mm
  oversize. A printed PLA wire will not flex like the steel one.
- The 2.2 mm collars and the 1.4 mm plate thickness are unchanged. Do not
  scale the plate.
- The slicer was run headless and the g-code was checked for bounds, tool and
  temperatures, not printed. Watch the first layer on a 357 mm part.
(layout STL is on the USB copy only)
