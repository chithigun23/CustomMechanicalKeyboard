import json

fps = json.load(open("C:/Claude/CustomMechanicalKeyboard/case/fps.json"))

print("=== MOUNTING HOLES (unnamed footprints, 1 pad w/ drill) ===")
mh = [f for f in fps if not f["lib"] and len(f["holes"]) == 1]
mh.sort(key=lambda f: (round(f["y"], 2), round(f["x"], 2)))
for f in mh:
    hx, hy, drill = f["holes"][0]
    print(
        "  (%7.2f, %7.2f)  padoff=(%.2f,%.2f) drill=%s"
        % (f["x"], f["y"], hx, hy, drill)
    )
print("count:", len(mh))

print()
print("=== SWITCHES ===")
sw = [f for f in fps if "SW_Kailh" in f["lib"]]
for f in sw:
    f["u"] = f["lib"].split("_")[-1].replace("u", "")
sizes = {}
for f in sw:
    sizes[f["u"]] = sizes.get(f["u"], 0) + 1
print("sizes:", sizes, "total:", len(sw))
xs = sorted(set(round(f["x"], 3) for f in sw))
ys = sorted(set(round(f["y"], 3) for f in sw))
print("distinct Y rows:", ys)
print("X range: %.3f .. %.3f" % (min(xs), max(xs)))

print()
print("=== ROWS ===")
for y in ys:
    row = sorted([f for f in sw if round(f["y"], 3) == y], key=lambda f: f["x"])
    print(
        "  y=%7.3f  n=%2d  x: %8.3f .. %8.3f  sizes=%s"
        % (
            y,
            len(row),
            row[0]["x"],
            row[-1]["x"],
            ",".join(f["u"] for f in row),
        )
    )

print()
print("=== STABILIZERS ===")
for f in fps:
    if "Stabilizer" in f["lib"]:
        print(
            "  %-4s %-40s (%7.3f, %7.3f) rot=%s"
            % (f["ref"], f["lib"].split(":")[-1], f["x"], f["y"], f["rot"])
        )
        for h in f["holes"]:
            print("        pad off (%6.3f, %6.3f) drill=%s" % (h[0], h[1], h[2]))

print()
print("=== ENCODER + CONNECTOR ===")
for f in fps:
    if "EC11" in f["lib"] or "mcuConnector" in f["lib"]:
        print("  %-5s %s  (%7.3f, %7.3f) rot=%s" % (f["ref"], f["lib"], f["x"], f["y"], f["rot"]))
        hs = f["holes"]
        if hs:
            print(
                "     pad-x %.3f..%.3f  pad-y %.3f..%.3f  n=%d"
                % (
                    min(h[0] for h in hs),
                    max(h[0] for h in hs),
                    min(h[1] for h in hs),
                    max(h[1] for h in hs),
                    len(hs),
                )
            )
            for h in hs[:8]:
                print("       (%7.3f,%7.3f) %s" % (h[0], h[1], h[2]))
