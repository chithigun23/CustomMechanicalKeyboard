
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import KICAD, KICAD_URL, PROJ_URL, kicad_cli

import re, json
src = open(KICAD_URL + "/mcuBoard/mcu_DaughterBoard.kicad_pcb", encoding="utf-8").read()
out = []
for m in re.finditer(r'\(footprint "([^"]*)"(.*?)\n\t\)\n', src, re.S):
    lib, body = m.groups()
    tr = re.search(r'\(transform\s*\(translate ([-\d.]+) ([-\d.]+)\)\s*\(rotate ([-\d.]+)\)', body)
    ref = re.search(r'\(property "Reference" "([^"]*)"', body)
    val = re.search(r'\(property "Value" "([^"]*)"', body)
    mdl = re.findall(r'\(model "([^"]*)"', body)
    if not (tr and ref):
        continue
    out.append(dict(ref=ref.group(1), val=val.group(1) if val else "",
                    lib=lib, x=float(tr.group(1)), y=float(tr.group(2)),
                    rot=float(tr.group(3)), model=mdl[0].split("/")[-1] if mdl else None))
out.sort(key=lambda d: (d["ref"][0], int(re.sub(r"\D", "", d["ref"]) or 0)))
print("%-6s %-22s %-9s %-8s %s" % ("REF", "VALUE", "POS", "ROT", "3D MODEL"))
for d in out:
    print("%-6s %-22s %5.1f,%-5.1f %-8.0f %s" % (d["ref"], d["val"][:22], d["x"], d["y"], d["rot"], d["model"] or "-- none --"))
print()
print("total footprints:", len(out), " with models:", sum(1 for d in out if d["model"]))
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcu_parts.json"), "w"), indent=1)
