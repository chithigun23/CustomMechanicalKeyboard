from build123d import *

D3 = "C:/Claude/CustomMechanicalKeyboard/KiCAD/kbProjectLib/3d/"
LC = "C:/Claude/CustomMechanicalKeyboard/KiCAD/kbProjectLib/easyeda2kicad/easyeda2kicad.3dshapes/"

files = [
    ("Choc V2 switch (blue.step)", D3 + "blue.step"),
    ("Cherry stab 2.00u", D3 + "Stabilizer_Cherry_MX_2.00u.stp"),
    ("EC11 encoder", LC + "SW-TH_EC11XXXXXXXX-L11.7-W12.0-H24.5-P2.5-LS14.5.step"),
]

for label, path in files:
    print("=" * 70)
    print(label)
    try:
        shp = import_step(path)
    except Exception as e:
        print("   import failed:", e)
        continue
    solids = shp.solids()
    print("   solids: %d" % len(solids))
    bb = shp.bounding_box()
    print(
        "   OVERALL  X %8.3f..%8.3f (%7.3f)  Y %8.3f..%8.3f (%7.3f)  Z %8.3f..%8.3f (%7.3f)"
        % (
            bb.min.X, bb.max.X, bb.size.X,
            bb.min.Y, bb.max.Y, bb.size.Y,
            bb.min.Z, bb.max.Z, bb.size.Z,
        )
    )
    for i, s in enumerate(sorted(solids, key=lambda s: -s.volume)[:8]):
        b = s.bounding_box()
        print(
            "     solid %d vol=%9.1f  X %7.2f..%7.2f (%6.2f)  Y %7.2f..%7.2f (%6.2f)  Z %7.2f..%7.2f (%6.2f)"
            % (
                i, s.volume,
                b.min.X, b.max.X, b.size.X,
                b.min.Y, b.max.Y, b.size.Y,
                b.min.Z, b.max.Z, b.size.Z,
            )
        )
