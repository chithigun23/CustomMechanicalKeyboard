"""
Case, switch plate and encoder knob for chithigun23/CustomMechanicalKeyboard.

Every position in here is read straight out of
    KiCAD/keyBoard/keyboardKiCad.kicad_pcb
via fps.json (see parse_pcb.py), so the parts track the real board.

CAD coordinate system
    X  0 .. 354   left -> right   (PCB left edge = 0)
    Y  0 .. 132   front -> back   (PCB front edge = 0, spacebar side)
    Z  0 upwards  0 = outside of the case floor
KiCad -> CAD:  cad_x = kx - 25 ,  cad_y = 215 - ky   (KiCad Y runs downwards)

Reference heights above the PCB top face, from the vendor STEP models:
    Kailh Choc V2   body 15.0 x 15.0, top of body   5.30
                    MX cross stem, top              8.60
    Cherry stab     housing top                     7.25
                    wire (horizontal run) top       2.39   <- sets PLATE_GAP
    DO-35 diode     top of glass body               1.80   <- sets PLATE_GAP
    EC11            body top (11.7 x 12.0)          4.29
                    upper housing (11.2 x 8.3) top 12.50

Measured off the real keyboard and converted to the same datum (M_* constants
below are quoted from the PCB bottom, so they are 1.6 larger):
    USB-C housing, top              7.40   agrees with the modelled 7.40
    keycap top, unpressed          11.60
    keycap top, fully pressed       8.40   <- sets the plate top
    EC11 stem top, D type          24.80   supersedes the STEP's 24.50
    EC11 flat starts at            14.80   (10.0 mm of flat, round below)
    keycap footprint          16.0 x 17.0
"""

import copy
import json
import math
import os

from build123d import *

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "out")
os.makedirs(OUTDIR, exist_ok=True)

# ===========================================================================
#  PARAMETERS  - everything you are likely to want to change lives here
# ===========================================================================

# ---- the PCB (measured from the kicad_pcb, do not change) ----
PCB_W, PCB_H, PCB_R, PCB_T = 354.0, 132.0, 10.0, 1.6

# ---- measured off the real keyboard, quoted from the PCB *bottom* face -------
# (the rest of this file works from the PCB *top* face, so PCB_T is subtracted)
M_USB_TOP = 9.0  # bottom of PCB -> top of the USB-C housing
M_CAP_TOP_UP = 13.2  # bottom of PCB -> top of an unpressed keycap
M_CAP_TOP_DN = 10.0  # bottom of PCB -> top of a fully pressed keycap
M_ENC_STEM_TOP = 26.4  # bottom of PCB -> top of the EC11 stem (D type)
M_ENC_FLAT_LEN = 10.0  # length of the flatted (D) part, measured down from the top
M_CAP_W, M_CAP_H = 16.0, 17.0  # keycap footprint, 1u

USB_TOP_ABOVE_PCB = M_USB_TOP - PCB_T  # 7.40
CAP_TOP_UP_ABOVE_PCB = M_CAP_TOP_UP - PCB_T  # 11.60
CAP_TOP_DN_ABOVE_PCB = M_CAP_TOP_DN - PCB_T  # 8.40
ENC_STEM_TOP_ABOVE_PCB = M_ENC_STEM_TOP - PCB_T  # 24.80
# the shaft is round below this, so the flat in the bore must not start lower
ENC_FLAT_START_ABOVE_PCB = ENC_STEM_TOP_ABOVE_PCB - M_ENC_FLAT_LEN  # 14.80
KEY_TRAVEL = M_CAP_TOP_UP - M_CAP_TOP_DN  # 3.20

# How tall a keycap is, bottom rim to top.  The plate top has to stay below
# (CAP_TOP_DN_ABOVE_PCB - CAP_HEIGHT) or a bottomed-out cap lands on the plate.
# The row pitch is 17.0 and the caps are 17.0 deep, so caps touch edge to edge
# and the plate web between rows sits directly under the cap rim - there is no
# way to route around this, the plate simply has to be lower than the cap rim.
CAP_HEIGHT = 4.4  # MEASURED off the real caps

# ---- fits and wall sections ----
PCB_CLEAR = 0.4  # per side, PCB edge -> case pocket wall
WALL = 3.5  # main wall thickness (below the plate ledge)
FLOOR = 3.0  # case floor thickness
STANDOFF = 6.0  # inside of floor -> underside of PCB (EC11 legs need 5.44)
LEDGE_W = 1.5  # width of the internal ledge the plate lands on
# Drop the ledge slightly below the plate underside so the plate always lands on
# the 18 collars (which reference the PCB, and therefore the keycap clearance)
# rather than on the ledge.  Without this, a ledge machined 0.2 high would lift
# the plate 0.2 and eat half the keycap clearance.
LEDGE_DROP = 0.15
PLATE_CLEAR = 0.3  # per side, plate edge -> its pocket

# ---- the plate ----
# Squeezed from both sides:
#   floor   all 83 DO-35 diodes sit under solid plate and top out at 1.80
#           the stabiliser wire tops out at 2.39 (relieved by a pocket, below)
#   ceiling a bottomed-out keycap: CAP_TOP_DN_ABOVE_PCB - CAP_HEIGHT
# With CAP_HEIGHT = 4.4 the cap rim reaches 4.00 at bottom-out, so 2.2 + 1.4
# puts the plate top at 3.60 and leaves 0.40 there.  Dropping to 2.2 would only
# leave 0.40 over the diodes, so they get relief pockets too and end up with
# 1.00 - the diode height is the one number here that is nominal rather than
# measured, so that is where the slack belongs.
PLATE_GAP = 2.2  # PCB top face -> plate underside
PLATE_T = 1.4  # plate thickness
CAP_CLEAR = 0.3  # wanted gap between a bottomed-out cap rim and the plate top
WIRE_RELIEF_D = 0.6  # pocket depth in the plate underside over the stab wire
# The wire's horizontal run, from the stabiliser STEP model, as CAD offsets from
# the stabiliser origin (the model gives KiCad y -8.74..-7.14, which flips)
WIRE_Y0, WIRE_Y1 = 7.14, 8.74
WIRE_MARGIN = 0.4
DIODE_RELIEF = True  # pocket the plate underside over every DO-35
DIODE_RELIEF_D = 0.6
DIODE_POCKET_W, DIODE_POCKET_L = 3.0, 8.2  # X, Y - all 83 diodes are at rot -90
SW_CUT = 15.6  # square cutout; the Choc V2 body is 15.0, this drops over it
SW_CUT_R = 1.5  # corner radius (free on a printer, saves a CNC tool change)
STAB_CLEAR = 0.5  # per side, added to the library 6.75 x 12.30 stab cutout
MERGE_GAP = 1.5  # merge switch+stab cutouts if the web between them is thinner

# ---- fasteners: M3 throughout, 18 places ----
BOSS_D = 8.0  # case boss OD (2.0 mm wall around the insert)
# 16 of the 18 bosses sit 1.4-1.9 mm from the pocket wall.  Left as islands that
# is a 6 mm deep slot needing a ~1.2 mm cutter, so any boss closer than this to a
# wall gets blended into it instead.  The rib lives under the PCB, so it costs
# nothing, and it prints better too.
BOSS_WALL_MERGE = 4.5
TAP_DRILL_D = 2.5  # M3 x 0.5 tapping size, for the machined variant
COLLAR_D = 6.0  # plate spacer OD, bears on the PCB (6.0 keeps the
#                 collar at KiCad (312,115) clear of the MCU bay corner)
# Heat-set insert pocket.  These are HOLE dimensions, not insert dimensions -
# a heat-set insert melts into a hole smaller than its own OD.  4.0 x 6.2 suits
# the common M3 insert (OD 4.6, length 5.7, e.g. Ruthex / CNC Kitchen), which
# wants hole depth = insert length + ~0.5.  Measure yours before printing.
INSERT_D = 4.0  # hole diameter
INSERT_L = 6.2  # hole depth
SCREW_D = 3.4  # M3 clearance
CSK_HEAD_D = 6.4  # M3 countersunk head at the plate surface, 90 deg

# ---- MCU daughterboard / USB-C ----
MCU_GAP = 2.54  # main PCB top -> daughterboard underside (header body height)
MCU_BAY_CLEAR = 0.75   # plate bay opening vs the daughterboard outline
MCU_BOARD_R = 3.5      # daughterboard corner radius, from mcu_DaughterBoard.kicad_pcb
MCU_PCB_T = 1.6
USB_BODY_H = 3.26  # USB-C receptacle height above the daughterboard
#  MCU_GAP + MCU_PCB_T + USB_BODY_H = 7.40 above the PCB top face, which is
#  exactly the measured 9.0 from the PCB bottom - the header assumption checks out
USB_W, USB_OPEN_BOT, USB_OPEN_TOP = 13.0, 12.6, 18.3
USB_CHAMFER = 1.0

# ---- outer form ----
WALL_TOP = 20.5  # top of the back/side walls
FRONT_RAMP = True  # drop the front wall to the plate line for wrist comfort
RAMP_Y0, RAMP_Y1 = 26.0, 62.0  # ramp starts / finishes (CAD Y)
BOT_CHAMFER = 1.0
FOOT_D, FOOT_DEPTH = 14.0, 1.0

# ---- knob ----
KNOB_D = 20.0
KNOB_BOT_CLEAR = 1.0  # knob underside above the plate top face
KNOB_CAP = 0.6  # material above the end of the shaft bore
KNOB_COUNTERBORE_D = 14.0  # clears the 11.2 x 8.3 upper housing (diag 13.94)
KNOB_CB_CLEAR = 0.3
SHAFT_D = 6.0
SHAFT_FIT = 0.2  # added to the bore diameter
SHAFT_FLAT = 4.5  # D-shaft: material left across the flat
FLAT_MARGIN = 0.3  # start the bore's flat this far above the shaft's flat
FLUTES, FLUTE_R = 24, 1.0
FLUTE_INSET_BOT, FLUTE_INSET_TOP = 2.5, 2.7
KNOB_TOP_CHAMFER, KNOB_BOT_CHAMFER = 2.0, 1.0
# Milling a flat inside a 20 mm deep blind 6.2 bore is awkward and a shop will
# quote it accordingly.  The machined variant uses a plain round bore plus an
# M3 grub screw bearing on the shaft's flat, which is how knobs are normally done.
GRUB_TAP_D = 2.5  # M3 x 0.5 tapping size
# Tapped the full 6.9 of wall, no counterbore.  The shaft flat is 8.5 in from
# the OD, so this needs an M3 x 10 set screw, which ends up ~1.5 proud.  That is
# deliberate - a flush screw would need a counterbore and it is only cosmetic.
GRUB_Z_FRAC = 0.55  # up the flat's length, 0 = flat start, 1 = shaft top

# ===========================================================================
#  DERIVED
# ===========================================================================
CX, CY = PCB_W / 2.0, PCB_H / 2.0

Z_FLOOR = FLOOR
Z_PCB_BOT = Z_FLOOR + STANDOFF
Z_PCB_TOP = Z_PCB_BOT + PCB_T
Z_PLATE_BOT = Z_PCB_TOP + PLATE_GAP
Z_PLATE_TOP = Z_PLATE_BOT + PLATE_T

POCKET_W, POCKET_H = PCB_W + 2 * PCB_CLEAR, PCB_H + 2 * PCB_CLEAR
POCKET_R = PCB_R + PCB_CLEAR
PLATE_POCKET_W = POCKET_W + 2 * LEDGE_W
PLATE_POCKET_H = POCKET_H + 2 * LEDGE_W
PLATE_POCKET_R = POCKET_R + LEDGE_W
PLATE_W = PLATE_POCKET_W - 2 * PLATE_CLEAR
PLATE_H = PLATE_POCKET_H - 2 * PLATE_CLEAR
PLATE_R = PLATE_POCKET_R - PLATE_CLEAR
OUT_W, OUT_H = POCKET_W + 2 * WALL, POCKET_H + 2 * WALL
OUT_R = POCKET_R + WALL

PLATE_TOP_ABOVE_PCB = PLATE_GAP + PLATE_T
CAP_HEIGHT_MAX = CAP_TOP_DN_ABOVE_PCB - PLATE_TOP_ABOVE_PCB - CAP_CLEAR
CAP_RIM_DOWN = CAP_TOP_DN_ABOVE_PCB - CAP_HEIGHT  # cap rim at bottom-out
CAP_GAP = CAP_RIM_DOWN - PLATE_TOP_ABOVE_PCB       # what is left over the plate

Z_MCU_TOP = Z_PCB_TOP + MCU_GAP + MCU_PCB_T
Z_USB_TOP = Z_MCU_TOP + USB_BODY_H

# ===========================================================================
#  BOARD GEOMETRY  (from the kicad_pcb)
# ===========================================================================
FPS = json.load(open(os.path.join(HERE, "fps.json")))


def cad(kx, ky):
    return (kx - 25.0, 215.0 - ky)


HOLES = [cad(f["x"], f["y"]) for f in FPS if not f["lib"] and len(f["holes"]) == 1]
SWITCHES = [
    (cad(f["x"], f["y"]), float(f["lib"].rsplit("_", 1)[-1].replace("u", "")))
    for f in FPS
    if "SW_Kailh" in f["lib"]
]
STABS = [
    (cad(f["x"], f["y"]), float(f["lib"].rsplit("_", 1)[-1].replace("u", "")))
    for f in FPS
    if "Stabilizer" in f["lib"]
]
ENC = cad(*[(f["x"], f["y"]) for f in FPS if "EC11" in f["lib"]][0])
CNN = [(f["x"], f["y"]) for f in FPS if "mcuConnector" in f["lib"]][0]

# Stab wire spacing per size, from the library footprints
STAB_SPACING = {2.0: 11.938, 3.0: 19.05, 6.25: 50.0}

# Daughterboard: its CNN1 lands on the main board's CNN1, so the board outline
# (30,22)-(59.7995,51) in mcuBoard space maps by this offset.
MCU_OFF = (CNN[0] - 35.0, CNN[1] - 25.85)
_m0 = cad(30.0 + MCU_OFF[0], 22.0 + MCU_OFF[1])
_m1 = cad(59.799533 + MCU_OFF[0], 51.0 + MCU_OFF[1])
MCU_X0, MCU_X1 = min(_m0[0], _m1[0]), max(_m0[0], _m1[0])
MCU_Y0, MCU_Y1 = min(_m0[1], _m1[1]), max(_m0[1], _m1[1])
USB_CX = cad(47.75 + MCU_OFF[0], 27.12 + MCU_OFF[1])[0]

assert len(HOLES) == 18, len(HOLES)
assert len(SWITCHES) == 83, len(SWITCHES)
assert len(STABS) == 4, len(STABS)


def rr(w, h, r):
    return RectangleRounded(w, h, min(r, min(w, h) / 2 - 1e-6))


def prism(w, h, r, z0, z1, cx=None, cy=None):
    cx = CX if cx is None else cx
    cy = CY if cy is None else cy
    return Pos(cx, cy, z0) * extrude(rr(w, h, r), amount=z1 - z0)


def cyl(d, z0, z1, x, y):
    return Pos(x, y, (z0 + z1) / 2.0) * Cylinder(radius=d / 2.0, height=z1 - z0)


def box(x0, x1, y0, y1, z0, z1, r=None):
    if r:
        return Pos((x0 + x1) / 2, (y0 + y1) / 2, z0) * extrude(
            rr(x1 - x0, y1 - y0, r), amount=z1 - z0
        )
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(
        x1 - x0, y1 - y0, z1 - z0
    )


# ===========================================================================
#  CASE
# ===========================================================================
def build_case(tapped=False):
    case = prism(OUT_W, OUT_H, OUT_R, 0, WALL_TOP)
    try:
        bot = case.faces().sort_by(Axis.Z)[0]
        case = chamfer(bot.edges(), BOT_CHAMFER)
    except Exception as e:
        print("   (bottom chamfer skipped: %s)" % e)
    envelope = copy.copy(case)  # to trim the boss ribs back to the outer skin

    # interior: PCB pocket, then a wider pocket above the ledge for the plate
    case -= prism(POCKET_W, POCKET_H, POCKET_R, Z_FLOOR, Z_PLATE_BOT)
    case -= prism(
        PLATE_POCKET_W, PLATE_POCKET_H, PLATE_POCKET_R,
        Z_PLATE_BOT - LEDGE_DROP, WALL_TOP + 1
    )

    # 18 bosses up to the underside of the PCB, blended into the wall where they
    # would otherwise leave a slot too narrow to machine
    px0, px1 = CX - POCKET_W / 2, CX + POCKET_W / 2
    py0, py1 = CY - POCKET_H / 2, CY + POCKET_H / 2
    r = BOSS_D / 2
    for x, y in HOLES:
        case += cyl(BOSS_D, Z_FLOOR, Z_PCB_BOT, x, y)
        out = WALL + 2.0
        if (x - r) - px0 < BOSS_WALL_MERGE:
            case += box(px0 - out, x, y - r, y + r, Z_FLOOR, Z_PCB_BOT, r=r)
        if px1 - (x + r) < BOSS_WALL_MERGE:
            case += box(x, px1 + out, y - r, y + r, Z_FLOOR, Z_PCB_BOT, r=r)
        if (y - r) - py0 < BOSS_WALL_MERGE:
            case += box(x - r, x + r, py0 - out, y, Z_FLOOR, Z_PCB_BOT, r=r)
        if py1 - (y + r) < BOSS_WALL_MERGE:
            case += box(x - r, x + r, y, py1 + out, Z_FLOOR, Z_PCB_BOT, r=r)

    # the ribs above run out past the wall on purpose; trim them to the skin
    case = case & envelope

    # heat-set insert pocket + screw over-travel, blind so nothing shows outside
    cutters = []
    for x, y in HOLES:
        if tapped:
            # one tapping-size hole; JLC cuts the M3 thread
            cutters.append(cyl(TAP_DRILL_D, 1.5, Z_PCB_BOT + 0.01, x, y))
        else:
            cutters.append(cyl(INSERT_D, Z_PCB_BOT - INSERT_L, Z_PCB_BOT + 0.01, x, y))
            cutters.append(cyl(SCREW_D, 1.5, Z_PCB_BOT - INSERT_L + 0.01, x, y))

    # USB-C opening in the back wall, with an outside chamfer for fat cables
    y_out = CY + OUT_H / 2.0
    cutters.append(
        box(
            USB_CX - USB_W / 2,
            USB_CX + USB_W / 2,
            CY + POCKET_H / 2 - 1.0,
            y_out + 1.0,
            USB_OPEN_BOT,
            USB_OPEN_TOP,
            r=1.5,
        )
    )
    cutters.append(
        box(
            USB_CX - USB_W / 2 - USB_CHAMFER,
            USB_CX + USB_W / 2 + USB_CHAMFER,
            y_out - USB_CHAMFER,
            y_out + 1.0,
            USB_OPEN_BOT - USB_CHAMFER,
            USB_OPEN_TOP + USB_CHAMFER,
            r=1.5,
        )
    )

    # rubber feet
    for fx, fy in [(30, 18), (177, 18), (324, 18), (30, 114), (177, 114), (324, 114)]:
        cutters.append(cyl(FOOT_D, -0.01, FOOT_DEPTH, fx, fy))

    case = case.cut(*cutters)

    if FRONT_RAMP:
        pts = [
            (-20.0, Z_PLATE_TOP),
            (RAMP_Y0, Z_PLATE_TOP),
            (RAMP_Y1, WALL_TOP),
            (RAMP_Y1, WALL_TOP + 20),
            (-20.0, WALL_TOP + 20),
        ]
        wedge = Pos(-20, 0, 0) * extrude(
            Plane.YZ * make_face(Polyline(*pts, close=True)), amount=OUT_W + 40
        )
        case -= wedge
    return case


# ===========================================================================
#  PLATE
# ===========================================================================
def stab_rects(center, size):
    """Housing cutouts for one stabiliser, in CAD coords."""
    s = STAB_SPACING[size]
    cx, cy = center
    hw = 3.375 + STAB_CLEAR
    hh = 6.15 + STAB_CLEAR
    yc = cy - 0.62  # library cutout spans KiCad y -5.53..+6.77, centre +0.62
    return [(cx - s - hw, cx - s + hw, yc - hh, yc + hh),
            (cx + s - hw, cx + s + hw, yc - hh, yc + hh)], s, hw, yc, hh


def build_plate():
    plate = prism(PLATE_W, PLATE_H, PLATE_R, Z_PLATE_BOT, Z_PLATE_TOP)
    plate += [
        cyl(COLLAR_D, Z_PCB_TOP, Z_PLATE_BOT + 0.01, x, y) for x, y in HOLES
    ]

    zc0, zc1 = Z_PLATE_BOT - 1.0, Z_PLATE_TOP + 1.0
    cutters = []

    # which switches carry a stabiliser, and does the web between them survive?
    merged = {}
    for center, size in STABS:
        rects, s, hw, yc, hh = stab_rects(center, size)
        web = (s - hw) - SW_CUT / 2.0
        key = min(SWITCHES, key=lambda k: math.hypot(k[0][0] - center[0],
                                                     k[0][1] - center[1]))[0]
        if web < MERGE_GAP:
            merged[key] = (center, s + hw)
        else:
            for x0, x1, y0, y1 in rects:
                cutters.append(box(x0, x1, y0, y1, zc0, zc1, r=SW_CUT_R))
        # Wire relief.  The horizontal run of the stabiliser wire sits
        # 0.79..2.39 above the PCB, i.e. above the plate underside, and it runs
        # between the two housings where the plate is otherwise solid.  A pocket
        # in the underside lets it through without opening a slot in the plate.
        cutters.append(
            box(center[0] - s - hw, center[0] + s + hw,
                center[1] + WIRE_Y0 - WIRE_MARGIN,
                center[1] + WIRE_Y1 + WIRE_MARGIN,
                Z_PLATE_BOT - 0.01, Z_PLATE_BOT + WIRE_RELIEF_D)
        )

    for center, size in SWITCHES:
        if center in merged:
            sc, half = merged[center]
            cutters.append(
                box(sc[0] - half, sc[0] + half,
                    center[1] - SW_CUT / 2, center[1] + SW_CUT / 2,
                    zc0, zc1, r=SW_CUT_R)
            )
        else:
            cutters.append(
                box(center[0] - SW_CUT / 2, center[0] + SW_CUT / 2,
                    center[1] - SW_CUT / 2, center[1] + SW_CUT / 2,
                    zc0, zc1, r=SW_CUT_R)
            )

    # EC11 body is 11.7 x 12.0 where it crosses the plate
    cutters.append(box(ENC[0] - 6.25, ENC[0] + 6.25,
                       ENC[1] - 6.4, ENC[1] + 6.4, zc0, zc1, r=1.5))

    # MCU bay: open to the back edge of the plate so the USB-C can breathe.
    # Corner radius follows the daughterboard so the bay hugs the board without
    # eating into the screw collar at KiCad (312,115).
    cutters.append(box(MCU_X0 - MCU_BAY_CLEAR, MCU_X1 + MCU_BAY_CLEAR,
                       MCU_Y0 - MCU_BAY_CLEAR, CY + PLATE_H / 2 + 1.0,
                       zc0, zc1, r=MCU_BOARD_R + MCU_BAY_CLEAR))

    # relief pockets over the THT diodes - all 83 sit under solid plate
    if DIODE_RELIEF:
        for f in FPS:
            if "DO-35" not in f["lib"]:
                continue
            assert abs(f["rot"]) == 90.0, f["rot"]
            dx, dy = cad(f["x"], f["y"])
            cutters.append(
                box(dx - DIODE_POCKET_W / 2, dx + DIODE_POCKET_W / 2,
                    dy - DIODE_POCKET_L / 2, dy + DIODE_POCKET_L / 2,
                    Z_PLATE_BOT - 0.01, Z_PLATE_BOT + DIODE_RELIEF_D, r=1.0)
            )

    # screw holes + 90 deg countersinks
    for x, y in HOLES:
        cutters.append(cyl(SCREW_D, Z_PCB_TOP - 1.0, Z_PLATE_TOP + 1.0, x, y))
        csk_r = SCREW_D / 2.0
        top_r = CSK_HEAD_D / 2.0 + 0.2
        h = top_r - csk_r
        cutters.append(
            Pos(x, y, Z_PLATE_TOP + 0.2 - h / 2.0)
            * Cone(bottom_radius=csk_r, top_radius=top_r, height=h)
        )

    return plate.cut(*cutters)


# ===========================================================================
#  KNOB
# ===========================================================================
def build_knob(d_shaft=True, grub=False):
    z_hous_top = Z_PCB_TOP + 12.50
    z_shaft_top = Z_PCB_TOP + ENC_STEM_TOP_ABOVE_PCB
    z0 = Z_PLATE_TOP + KNOB_BOT_CLEAR
    z_cb = z_hous_top + KNOB_CB_CLEAR
    z_bore = z_shaft_top + 0.5
    z1 = z_bore + KNOB_CAP

    knob = cyl(KNOB_D, z0, z1, 0, 0)
    # chamfer while it is still a plain cylinder - two clean circular edges
    for zf, cham in ((z0, KNOB_BOT_CHAMFER), (z1, KNOB_TOP_CHAMFER)):
        try:
            face = [g for g in knob.faces().filter_by(Plane.XY)
                    if abs(g.center().Z - zf) < 1e-6][0]
            knob = chamfer(face.edges(), cham)
        except Exception as e:
            print("   (knob chamfer at z=%.1f skipped: %s)" % (zf, e))

    cutters = [cyl(KNOB_COUNTERBORE_D, z0 - 0.01, z_cb, 0, 0)]

    bore = cyl(SHAFT_D + SHAFT_FIT, z_cb - 0.01, z_bore, 0, 0)
    if grub:
        # plain round bore; an M3 grub screw clamps onto the shaft's flat.
        # It enters along +X, the same side the flat faces.
        z_flat0 = Z_PCB_TOP + ENC_FLAT_START_ABOVE_PCB
        z_g = z_flat0 + GRUB_Z_FRAC * (Z_PCB_TOP + ENC_STEM_TOP_ABOVE_PCB - z_flat0)
        # sit it halfway between two flutes so the entry is on a full round face
        adeg = 360.0 / FLUTES / 2.0
        L = KNOB_D
        h = Rot(0, 90, 0) * Cylinder(radius=GRUB_TAP_D / 2.0, height=L)
        h = Pos(2.0 + L / 2.0, 0, 0) * h  # start inside the bore, run outward only
        h = Rot(0, 0, adeg) * h
        cutters.append(Pos(0, 0, z_g) * h)
    elif d_shaft:
        # The flat is only on the top 10 mm of the shaft; below that it is round.
        # Keying the whole bore would make it foul on the round section, so the
        # flat only starts where the shaft's flat starts (plus a little margin).
        z_flat = Z_PCB_TOP + ENC_FLAT_START_ABOVE_PCB + FLAT_MARGIN
        keep = SHAFT_FLAT + 0.1 - (SHAFT_D + SHAFT_FIT) / 2.0
        bore -= box(keep, keep + 10, -10, 10, z_flat, z_bore + 0.01)
    cutters.append(bore)

    for i in range(FLUTES):
        a = 2 * math.pi * i / FLUTES
        cutters.append(
            cyl(FLUTE_R * 2, z0 + FLUTE_INSET_BOT, z1 - FLUTE_INSET_TOP,
                math.cos(a) * KNOB_D / 2.0, math.sin(a) * KNOB_D / 2.0)
        )
    return knob.cut(*cutters)


# ===========================================================================
#  BUILD + EXPORT
# ===========================================================================
def build_plate_2d():
    """Flat pattern of the plate: outline minus every through-cutout.

    Use this if you want the plate laser-cut / waterjetted from 1.6 mm metal
    instead of printed.  The 18 spacer collars become loose 6 x 2.8 mm
    standoffs in that case.
    """
    sk = rr(PLATE_W, PLATE_H, PLATE_R)
    holes = []
    merged = {}
    for center, size in STABS:
        rects, s, hw, yc, hh = stab_rects(center, size)
        key = min(SWITCHES, key=lambda k: math.hypot(k[0][0] - center[0],
                                                     k[0][1] - center[1]))[0]
        if (s - hw) - SW_CUT / 2.0 < MERGE_GAP:
            merged[key] = (center, s + hw)
        else:
            for x0, x1, y0, y1 in rects:
                holes.append(Pos((x0 + x1) / 2 - CX, (y0 + y1) / 2 - CY)
                             * rr(x1 - x0, y1 - y0, SW_CUT_R))
    for center, size in SWITCHES:
        if center in merged:
            sc, half = merged[center]
            holes.append(Pos(sc[0] - CX, center[1] - CY)
                         * rr(2 * half, SW_CUT, SW_CUT_R))
        else:
            holes.append(Pos(center[0] - CX, center[1] - CY)
                         * rr(SW_CUT, SW_CUT, SW_CUT_R))
    holes.append(Pos(ENC[0] - CX, ENC[1] - CY) * rr(12.5, 12.8, 1.5))
    bx0, bx1 = MCU_X0 - MCU_BAY_CLEAR, MCU_X1 + MCU_BAY_CLEAR
    by0, by1 = MCU_Y0 - MCU_BAY_CLEAR, CY + PLATE_H / 2 + 1.0
    holes.append(Pos((bx0 + bx1) / 2 - CX, (by0 + by1) / 2 - CY)
                 * rr(bx1 - bx0, by1 - by0, MCU_BOARD_R + MCU_BAY_CLEAR))
    for x, y in HOLES:
        holes.append(Pos(x - CX, y - CY) * Circle(SCREW_D / 2.0))
    for h in holes:
        sk -= h
    return sk


def save(part, name):
    sp = os.path.join(OUTDIR, name + ".step")
    st = os.path.join(OUTDIR, name + ".stl")
    export_step(part, sp)
    export_stl(part, st, tolerance=0.02, angular_tolerance=0.2)
    b = part.bounding_box()
    print("   %-22s %7.1f x %6.1f x %6.1f mm   vol %9.1f mm3"
          % (name, b.size.X, b.size.Y, b.size.Z, part.volume))
    return part


if __name__ == "__main__":
    print("Z stack:  floor %.1f | PCB %.1f-%.1f | plate %.1f-%.1f | wall top %.1f"
          % (Z_FLOOR, Z_PCB_BOT, Z_PCB_TOP, Z_PLATE_BOT, Z_PLATE_TOP, WALL_TOP))
    print("USB-C body %.2f-%.2f, opening %.1f-%.1f" %
          (Z_MCU_TOP, Z_USB_TOP, USB_OPEN_BOT, USB_OPEN_TOP))
    print("MCU bay X %.1f..%.1f  Y %.1f..%.1f   USB centre X %.2f"
          % (MCU_X0, MCU_X1, MCU_Y0, MCU_Y1, USB_CX))
    print("encoder at (%.1f, %.1f)" % ENC)
    print()
    print("building...")
    case = save(build_case(), "keyboard_case")
    case_cnc = save(build_case(tapped=True), "keyboard_case_cnc_tapped")
    plate = save(build_plate(), "keyboard_plate")
    knob = save(build_knob(True), "encoder_knob_D_shaft")
    save(build_knob(False), "encoder_knob_round")
    knob_grub = save(build_knob(False, grub=True), "encoder_knob_cnc_grubscrew")

    # one assembly per route, so each matches the parts actually being made
    for name, c, k in (("assembly_print", case, knob),
                       ("assembly_cnc", case_cnc, knob_grub)):
        asm = Compound(children=[
            copy.copy(c), copy.copy(plate), Pos(ENC[0], ENC[1], 0) * copy.copy(k)
        ])
        export_step(asm, os.path.join(OUTDIR, name + ".step"))
        print("   %-22s %s.step" % ("", name))

    # flat pattern, in case you want the plate cut from metal
    from build123d.exporters import ExportDXF, ExportSVG

    flat = Pos(CX, CY) * build_plate_2d()
    dxf = ExportDXF(unit=Unit.MM)
    dxf.add_shape(flat)
    dxf.write(os.path.join(OUTDIR, "keyboard_plate_flat.dxf"))
    svg = ExportSVG(unit=Unit.MM)
    svg.add_shape(flat)
    svg.write(os.path.join(OUTDIR, "keyboard_plate_flat.svg"))
    print("   %-22s keyboard_plate_flat.dxf / .svg" % "")
    print("done ->", OUTDIR)
