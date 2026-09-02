"""Export the MCU daughterboard as one GLB per object, all in the same frame.

The board files are saved in KiCad 10.99 format so the 10.0 CLI cannot read
them; 10.99 is used here.  GLB is a neutral format, so the usual caution about
the nightly emitting KiCad files 10.0.5 cannot open does not apply.  Export is
read-only - the input checksum is verified afterwards.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import KICAD, KICAD_URL, PROJ_URL, kicad_cli

import hashlib
import json
import os
import subprocess
import sys

CLI = kicad_cli()
PCB = os.path.join(KICAD, "mcuBoard", "mcu_DaughterBoard.kicad_pcb")
VAR = "KEYBOARD_PROJ_DIR=" + PROJ_URL
HERE = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(HERE, "glb")
os.makedirs(GLB, exist_ok=True)


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


before = md5(PCB)
parts = json.load(open(os.path.join(HERE, "mcu_parts.json")))
todo = [p for p in parts if p["model"]]

print("exporting %d components" % len(todo))
ok, fail = 0, []
for p in todo:
    ref = p["ref"]
    out = os.path.join(GLB, "mcu_part_%s.glb" % ref)
    cmd = [CLI, "pcb", "export", "glb", "-o", out, "-D", VAR, "--force",
           "--subst-models", "--no-board-body", "--component-filter", ref, PCB]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 0:
        ok += 1
        print("  %-6s %-24s %8.0f kB" % (ref, p["val"][:24], os.path.getsize(out) / 1024))
    else:
        fail.append((ref, (r.stderr or r.stdout).strip()[:120]))
        print("  %-6s FAILED  %s" % (ref, (r.stderr or r.stdout).strip()[:80]))

print()
print("exported %d/%d" % (ok, len(todo)))
for ref, err in fail:
    print("  fail %s: %s" % (ref, err))

after = md5(PCB)
print()
print("input pcb unchanged:", before == after)
if before != after:
    sys.exit("INPUT WAS MODIFIED - stop and investigate")
