"""Are the THT diodes actually under solid plate, or do they fall inside cutouts?

The first pass of this compared each diode to its *nearest switch centre*, which
picked the wrong switch for diodes sitting in a row gap.  This one tests every
diode against every through-cutout in the plate.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import keyboard_cad as K

FPS = json.load(open(os.path.join(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))), "fps.json")))

# every through-cutout, same construction as the plate
cuts = []
merged = {}
for center, size in K.STABS:
    rects, s, hw, yc, hh = K.stab_rects(center, size)
    key = min(K.SWITCHES, key=lambda k: math.hypot(k[0][0] - center[0],
                                                   k[0][1] - center[1]))[0]
    if (s - hw) - K.SW_CUT / 2.0 < K.MERGE_GAP:
        merged[key] = (center, s + hw)
    else:
        cuts += [(x0, x1, y0, y1) for x0, x1, y0, y1 in rects]
for center, size in K.SWITCHES:
    if center in merged:
        sc, half = merged[center]
        cuts.append((sc[0] - half, sc[0] + half,
                     center[1] - K.SW_CUT / 2, center[1] + K.SW_CUT / 2))
    else:
        cuts.append((center[0] - K.SW_CUT / 2, center[0] + K.SW_CUT / 2,
                     center[1] - K.SW_CUT / 2, center[1] + K.SW_CUT / 2))
cuts.append((K.MCU_X0 - K.MCU_BAY_CLEAR, K.MCU_X1 + K.MCU_BAY_CLEAR,
             K.MCU_Y0 - K.MCU_BAY_CLEAR, K.CY + K.PLATE_H / 2 + 1.0))

# diode bodies: DO-35, 3.65 half-length along its axis, 0.9 half-width, rot -90
diodes = []
for f in FPS:
    if "DO-35" not in f["lib"]:
        continue
    x, y = K.cad(f["x"], f["y"])
    a = math.radians(f["rot"])
    hw = abs(3.65 * math.cos(a)) + abs(0.9 * math.sin(a))
    hh = abs(3.65 * math.sin(a)) + abs(0.9 * math.cos(a))
    diodes.append((f["ref"], x - hw, x + hw, y - hh, y + hh))

print("diodes: %d   cutouts: %d" % (len(diodes), len(cuts)))


def inside(d, c):
    return d[1] >= c[0] and d[2] <= c[1] and d[3] >= c[2] and d[4] <= c[3]


def overlaps(d, c):
    return not (d[2] <= c[0] or d[1] >= c[1] or d[4] <= c[2] or d[3] >= c[3])


full = [d for d in diodes if any(inside(d, c) for c in cuts)]
part = [d for d in diodes
        if d not in full and any(overlaps(d, c) for c in cuts)]
under = [d for d in diodes if d not in full and d not in part]

print()
print("  fully inside a cutout (plate never touches them) : %d" % len(full))
print("  straddling a cutout edge                          : %d" % len(part))
print("  fully under solid plate                           : %d" % len(under))

if under:
    print()
    print("  diodes under solid plate (these set the minimum PLATE_GAP):")
    for d in under[:20]:
        print("    %-5s x %7.2f..%7.2f  y %7.2f..%7.2f" % d)
    if len(under) > 20:
        print("    ... and %d more" % (len(under) - 20))
if part:
    print()
    print("  straddling (partially covered):")
    for d in part[:20]:
        print("    %-5s x %7.2f..%7.2f  y %7.2f..%7.2f" % d)
    if len(part) > 20:
        print("    ... and %d more" % (len(part) - 20))
