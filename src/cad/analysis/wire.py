from build123d import *

D3 = "C:/Claude/CustomMechanicalKeyboard/KiCAD/kbProjectLib/3d/"
shp = import_step(D3 + "Stabilizer_Cherry_MX_2.00u.stp")
solids = sorted(shp.solids(), key=lambda s: -s.volume)
wire = solids[4]
b = wire.bounding_box()
print("WIRE solid bbox: X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f" % (
    b.min.X, b.max.X, b.min.Y, b.max.Y, b.min.Z, b.max.Z))

print()
print("Wire cross-section vs X slice (the plate is solid where |X| < 8.56):")
x = -13.0
while x < 13.0:
    probe = Pos((x + 0.5), 0, 6) * Box(1.0, 40, 30)
    try:
        cut = wire & probe
        if cut.volume > 1e-6:
            c = cut.bounding_box()
            print("  X %6.2f..%6.2f   Y %7.2f..%7.2f   Z %6.2f..%6.2f" % (
                x, x + 1, c.min.Y, c.max.Y, c.min.Z, c.max.Z))
    except Exception:
        pass
    x += 1.0

print()
print("Housing solids (0,1) cross-section at their centre, and stems (2,3):")
for i in (0, 2):
    s = solids[i]
    b = s.bounding_box()
    print("  solid %d: X %7.2f..%7.2f  Y %7.2f..%7.2f  Z %7.2f..%7.2f" % (
        i, b.min.X, b.max.X, b.min.Y, b.max.Y, b.min.Z, b.max.Z))

print()
print("What the plate band (Z 2.2..4.8) intersects, per solid:")
band = Pos(0, 0, (2.2 + 4.8) / 2) * Box(200, 60, 4.8 - 2.2)
for i, s in enumerate(solids):
    try:
        v = s & band
        if v.volume > 1e-6:
            c = v.bounding_box()
            print("  solid %d vol=%8.2f  X %7.2f..%7.2f  Y %7.2f..%7.2f" % (
                i, v.volume, c.min.X, c.max.X, c.min.Y, c.max.Y))
    except Exception as e:
        print("  solid %d probe failed %s" % (i, e))
