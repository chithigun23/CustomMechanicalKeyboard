import json, math

fps = json.load(open("C:/Claude/CustomMechanicalKeyboard/case/fps.json"))

mh = [f for f in fps if not f["lib"] and len(f["holes"]) == 1]
mh.sort(key=lambda f: (round(f["y"], 2), round(f["x"], 2)))

# absolute pad positions of every non-mounting-hole footprint
pads = []
for f in fps:
    if f in mh:
        continue
    a = math.radians(f["rot"])
    ca, sa = math.cos(a), math.sin(a)
    for hx, hy, drill in f["holes"]:
        # KiCad footprint rotation is CCW in screen coords (y down)
        px = f["x"] + hx * ca + hy * sa
        py = f["y"] - hx * sa + hy * ca
        try:
            d = float(drill[0])
        except Exception:
            d = 1.0
        pads.append((px, py, d, f["ref"], f["lib"].split(":")[-1]))

print("=== CLEARANCE AROUND EACH MOUNTING HOLE ===")
print("(distance from hole centre to nearest through-hole pad EDGE)")
worst = []
for f in mh:
    best = None
    for px, py, d, ref, lib in pads:
        dist = math.hypot(px - f["x"], py - f["y"]) - d / 2.0
        if best is None or dist < best[0]:
            best = (dist, ref, lib, px, py)
    worst.append((best[0], f["x"], f["y"], best[1], best[2]))
    print(
        "  hole (%7.2f,%7.2f)  nearest pad edge %6.2f mm  -> %s (%s)"
        % (f["x"], f["y"], best[0], best[1], best[2])
    )
worst.sort()
print()
print("TIGHTEST: %.2f mm at (%.2f, %.2f) [%s %s]" % worst[0])
print("  -> max safe boss/collar radius = %.2f mm (diameter %.2f)" % (worst[0][0], 2 * worst[0][0]))

print()
print("=== BOARD-EDGE DISTANCE FOR EACH HOLE ===")
X0, Y0, X1, Y1 = 25.0, 83.0, 379.0, 215.0
for f in mh:
    print(
        "  (%7.2f,%7.2f)  left %6.2f  right %6.2f  top %6.2f  bottom %6.2f"
        % (f["x"], f["y"], f["x"] - X0, X1 - f["x"], f["y"] - Y0, Y1 - f["y"])
    )
