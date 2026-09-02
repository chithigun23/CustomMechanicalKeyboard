"""Paths and tool discovery, resolved relative to this file.

The project folder IS the git clone of the keyboard repo, so the KiCad tree at
its root is the single source of truth for all geometry - the CAD, the GLB
exports and the renders are all derived from it. Do not copy it elsewhere.
"""
import glob
import os

HERE = os.path.dirname(os.path.abspath(__file__))     # ...\src\render
SRC = os.path.dirname(HERE)                           # ...\src
PROJECT = os.path.dirname(SRC)                        # ...\keyboardProject

KICAD = os.path.join(PROJECT, "KiCAD")
CAD = os.path.join(SRC, "cad")
GLB = os.path.join(HERE, "glb")
RENDERS = os.path.join(HERE, "renders")

MCU_PCB = os.path.join(KICAD, "mcuBoard", "mcu_DaughterBoard.kicad_pcb")
KB_PCB = os.path.join(KICAD, "keyBoard", "keyboardKiCad.kicad_pcb")

# forward-slash forms for anything handed to kicad-cli
KICAD_URL = KICAD.replace("\\", "/")
PROJ_URL = PROJECT.replace("\\", "/")     # what ${KEYBOARD_PROJ_DIR} must be
CASE_URL = CAD.replace("\\", "/")


def kicad_cli():
    """The board files are saved in KiCad 10.99 format, so the 10.0 CLI cannot
    read them. GLB is a neutral output format, so using the nightly is safe."""
    for p in (r"C:\Program Files\KiCad\10.99\bin\kicad-cli.exe",
              r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"):
        if os.path.exists(p):
            return p
    hits = sorted(glob.glob(r"C:\Program Files\KiCad\*\bin\kicad-cli.exe"))
    if hits:
        return hits[-1]
    raise SystemExit("kicad-cli not found - edit src/render/config.py")


def blender():
    hits = sorted(glob.glob(
        r"C:\Program Files\Blender Foundation\Blender *\blender.exe"))
    if not hits:
        raise SystemExit("blender.exe not found - edit src/render/config.py")
    return hits[-1]


if __name__ == "__main__":
    print("PROJECT   ", PROJECT)
    print("KICAD     ", KICAD, " exists:", os.path.isdir(KICAD))
    print("MCU_PCB    exists:", os.path.exists(MCU_PCB))
    print("KB_PCB     exists:", os.path.exists(KB_PCB))
    print("3D models  exists:",
          os.path.isdir(os.path.join(KICAD, "kbProjectLib", "3d")))
    print("kicad-cli ", kicad_cli())
    print("blender   ", blender())
