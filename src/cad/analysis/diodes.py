import json, math

fps = json.load(open("C:/Claude/CustomMechanicalKeyboard/case/fps.json"))

SW_CUT = 15.6  # plate cutout for switches
sw = [f for f in fps if "SW_Kailh" in f["lib"]]
di = [f for f in fps if "DO-35" in f["lib"]]

print("diodes: %d   switches: %d" % (len(di), len(sw)))
print()
print("Diode centre offset from its nearest switch centre, and whether the")
print("diode body (4.0 x 2.0 mm) falls inside that switch's %.1f mm cutout:" % SW_CUT)

half = SW_CUT / 2.0
inside = 0
outside = []
for d in di:
    best = min(sw, key=lambda s: math.hypot(s["x"] - d["x"], s["y"] - d["y"]))
    dx = d["x"] - best["x"]
    dy = d["y"] - best["y"]
    # diode body extent, rotation applied (body 4.0 long along its axis, 2.0 wide)
    a = math.radians(d["rot"])
    hw = abs(2.0 * math.cos(a)) + abs(1.0 * math.sin(a))
    hh = abs(2.0 * math.sin(a)) + abs(1.0 * math.cos(a))
    ok = (abs(dx) + hw <= half) and (abs(dy) + hh <= half)
    if ok:
        inside += 1
    else:
        outside.append((d["ref"], best["ref"], dx, dy, hw, hh, d["rot"]))

print("  fully inside a switch cutout : %d" % inside)
print("  NOT fully inside             : %d" % len(outside))
print()
if outside:
    print("  worst offenders (first 15):")
    for r, sr, dx, dy, hw, hh, rot in sorted(
        outside, key=lambda t: -(max(abs(t[2]) + t[4], abs(t[3]) + t[5]))
    )[:15]:
        need = max(abs(dx) + hw, abs(dy) + hh) * 2
        print(
            "    %-4s near %-4s  offset (%6.2f,%6.2f) rot=%-5s -> needs %.1f mm cutout"
            % (r, sr, dx, dy, rot, need)
        )

print()
print("Distinct diode rotations:", sorted(set(d["rot"] for d in di)))
print("Distinct |offset| from nearest switch:")
offs = sorted(set((round(d["x"] - min(sw, key=lambda s: math.hypot(s["x"]-d["x"], s["y"]-d["y"]))["x"], 2),
                   round(d["y"] - min(sw, key=lambda s: math.hypot(s["x"]-d["x"], s["y"]-d["y"]))["y"], 2))
                  for d in di))
for o in offs[:20]:
    print("   ", o)
