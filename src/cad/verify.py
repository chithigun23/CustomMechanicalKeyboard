"""Geometric sanity checks on the generated parts."""
import math
import keyboard_cad as K

FAIL = []
WARN = []


def chk(ok, msg, warn=False):
    if ok:
        print("  ok    %s" % msg)
    else:
        print("  %s  %s" % ("WARN" if warn else "FAIL", msg))
        (WARN if warn else FAIL).append(msg)


def rects():
    """Every through-cutout in the plate as (x0,x1,y0,y1,label)."""
    out = []
    merged = {}
    for center, size in K.STABS:
        r, s, hw, yc, hh = K.stab_rects(center, size)
        web = (s - hw) - K.SW_CUT / 2.0
        key = min(K.SWITCHES, key=lambda k: math.hypot(k[0][0] - center[0],
                                                       k[0][1] - center[1]))[0]
        if web < K.MERGE_GAP:
            merged[key] = (center, s + hw)
        else:
            for i, (x0, x1, y0, y1) in enumerate(r):
                out.append((x0, x1, y0, y1, "stab%.2f_%d" % (size, i)))
    for center, size in K.SWITCHES:
        if center in merged:
            sc, half = merged[center]
            out.append((sc[0] - half, sc[0] + half,
                        center[1] - K.SW_CUT / 2, center[1] + K.SW_CUT / 2,
                        "sw%.2f_merged" % size))
        else:
            out.append((center[0] - K.SW_CUT / 2, center[0] + K.SW_CUT / 2,
                        center[1] - K.SW_CUT / 2, center[1] + K.SW_CUT / 2,
                        "sw%.2f" % size))
    out.append((K.ENC[0] - 6.25, K.ENC[0] + 6.25,
                K.ENC[1] - 6.4, K.ENC[1] + 6.4, "encoder"))
    out.append((K.MCU_X0 - K.MCU_BAY_CLEAR, K.MCU_X1 + K.MCU_BAY_CLEAR,
                K.MCU_Y0 - K.MCU_BAY_CLEAR, K.CY + K.PLATE_H / 2 + 1.0, "mcu_bay"))
    return out


def rrect_dist(px, py, x0, x1, y0, y1, r):
    """Distance from a point to a rounded rectangle; negative if inside."""
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    hx, hy = (x1 - x0) / 2.0 - r, (y1 - y0) / 2.0 - r
    dx = abs(px - cx) - hx
    dy = abs(py - cy) - hy
    outside = math.hypot(max(dx, 0.0), max(dy, 0.0))
    return outside + min(max(dx, dy), 0.0) - r


def gap(a, b):
    dx = max(a[0] - b[1], b[0] - a[1])
    dy = max(a[2] - b[3], b[2] - a[3])
    if dx >= 0 or dy >= 0:
        return max(dx, dy)
    return -min(-dx, -dy)  # overlapping


R = rects()
print("PLATE: %d through-cutouts" % len(R))

print()
print("-- web between neighbouring cutouts --")
worst = (1e9, None, None)
overlaps = []
for i in range(len(R)):
    for j in range(i + 1, len(R)):
        g = gap(R[i], R[j])
        if g < -0.001:
            overlaps.append((R[i][4], R[j][4], g))
        elif g < worst[0]:
            worst = (g, R[i][4], R[j][4])
chk(not overlaps, "no cutouts overlap each other (%d overlaps)" % len(overlaps))
for a, b, g in overlaps[:6]:
    print("        %s <-> %s  overlap %.2f" % (a, b, -g))
chk(worst[0] >= 0.8, "thinnest web %.2f mm  (%s <-> %s)" % worst, warn=worst[0] >= 0.8)

print()
print("-- cutout vs screw collar (OD %.1f) --" % K.COLLAR_D)
wc = (1e9, None)
for x, y in K.HOLES:
    cr = (x - K.COLLAR_D / 2, x + K.COLLAR_D / 2, y - K.COLLAR_D / 2, y + K.COLLAR_D / 2)
    for r in R:
        if r[4] == "mcu_bay":
            # the bay has a 4.25 mm corner radius; use true distance
            g = rrect_dist(x, y, r[0], r[1], r[2], r[3],
                           K.MCU_BOARD_R + K.MCU_BAY_CLEAR) - K.COLLAR_D / 2
        else:
            g = gap(cr, r)
        if g < wc[0]:
            wc = (g, r[4])
chk(wc[0] > 0.4, "closest cutout to a collar: %.2f mm (%s)" % wc)

print()
print("-- MCU bay clears the daughterboard outline --")
bd = 1e9
for ang in range(0, 360, 3):
    # walk the daughterboard rounded outline and measure into the bay
    a = math.radians(ang)
    hx = (K.MCU_X1 - K.MCU_X0) / 2.0 - K.MCU_BOARD_R
    hy = (K.MCU_Y1 - K.MCU_Y0) / 2.0 - K.MCU_BOARD_R
    bx = (K.MCU_X0 + K.MCU_X1) / 2.0 + math.copysign(hx, math.cos(a)) + K.MCU_BOARD_R * math.cos(a)
    by = (K.MCU_Y0 + K.MCU_Y1) / 2.0 + math.copysign(hy, math.sin(a)) + K.MCU_BOARD_R * math.sin(a)
    d = rrect_dist(bx, by, K.MCU_X0 - K.MCU_BAY_CLEAR, K.MCU_X1 + K.MCU_BAY_CLEAR,
                   K.MCU_Y0 - K.MCU_BAY_CLEAR, K.CY + K.PLATE_H / 2 + 1.0,
                   K.MCU_BOARD_R + K.MCU_BAY_CLEAR)
    bd = min(bd, -d)
chk(bd > 0.3, "daughterboard sits inside the bay by at least %.2f mm" % bd)

print()
print("-- cutout inside the plate outline --")
px0, px1 = K.CX - K.PLATE_W / 2, K.CX + K.PLATE_W / 2
py0, py1 = K.CY - K.PLATE_H / 2, K.CY + K.PLATE_H / 2
edge = 1e9
for r in R:
    if r[4] == "mcu_bay":
        continue
    edge = min(edge, r[0] - px0, px1 - r[1], r[2] - py0, py1 - r[3])
chk(edge > 1.0, "closest cutout to the plate edge: %.2f mm" % edge)

print()
print("-- keycaps vs the case wall (caps %.1f x %.1f at 18.0 x 17.0 pitch) --"
      % (K.M_CAP_W, K.M_CAP_H))
wall_in_x0, wall_in_x1 = K.CX - K.PLATE_POCKET_W / 2, K.CX + K.PLATE_POCKET_W / 2
wall_in_y0, wall_in_y1 = K.CY - K.PLATE_POCKET_H / 2, K.CY + K.PLATE_POCKET_H / 2
m = 1e9
for (cx, cy), size in K.SWITCHES:
    # a size-u cap spans (size-1) extra pitches plus one cap width
    hw = ((size - 1.0) * 18.0 + K.M_CAP_W) / 2.0
    hh = K.M_CAP_H / 2.0
    m = min(m, cx - hw - wall_in_x0, wall_in_x1 - (cx + hw),
            cy - hh - wall_in_y0, wall_in_y1 - (cy + hh))
chk(m > 3.0, "closest keycap edge to the wall: %.2f mm" % m)

print()
print("-- keycap vs plate (the tight one) --")
print("  info  measured: cap top %.2f unpressed / %.2f pressed above the PCB,"
      % (K.CAP_TOP_UP_ABOVE_PCB, K.CAP_TOP_DN_ABOVE_PCB))
print("  info            travel %.2f mm" % K.KEY_TRAVEL)
print("  info  plate top sits %.2f mm above the PCB" % K.PLATE_TOP_ABOVE_PCB)
print("  info  => keycaps must be shorter than %.2f mm (rim to top)"
      % (K.CAP_HEIGHT_MAX + K.CAP_CLEAR))
chk(K.CAP_GAP >= 0.35, "measured cap height %.2f leaves %.2f mm at bottom-out"
    % (K.CAP_HEIGHT, K.CAP_GAP))

print()
print("-- knob clearances (D %.1f at %.1f,%.1f) --" % (K.KNOB_D, K.ENC[0], K.ENC[1]))
kr = K.KNOB_D / 2
chk(K.ENC[0] + kr < wall_in_x1 - 2, "knob to right wall: %.2f mm" % (wall_in_x1 - K.ENC[0] - kr))
chk(K.ENC[1] + kr < wall_in_y1 - 2, "knob to back wall: %.2f mm" % (wall_in_y1 - K.ENC[1] - kr))
chk(K.ENC[0] - kr > K.MCU_X1 + 1.5, "knob to MCU bay: %.2f mm" % (K.ENC[0] - kr - K.MCU_X1))
nearest_sw = min(K.SWITCHES, key=lambda s: math.hypot(s[0][0] - K.ENC[0], s[0][1] - K.ENC[1]))
d = math.hypot(nearest_sw[0][0] - K.ENC[0], nearest_sw[0][1] - K.ENC[1])
chk(d - kr - nearest_sw[1] * 18 / 2 > 1.0,
    "knob to nearest keycap: %.2f mm" % (d - kr - nearest_sw[1] * 18 / 2))

print()
print("-- vertical stack --")
# the plate underside is below the wire; the relief pocket is what clears it
chk(K.PLATE_GAP + K.WIRE_RELIEF_D - 2.39 > 0.35,
    "wire relief pocket ceiling %.2f clears the wire (2.39) by %.2f mm"
    % (K.PLATE_GAP + K.WIRE_RELIEF_D, K.PLATE_GAP + K.WIRE_RELIEF_D - 2.39))
_wy0 = K.WIRE_Y0 - K.WIRE_MARGIN
_wy1 = K.WIRE_Y1 + K.WIRE_MARGIN
chk(_wy0 < K.WIRE_Y0 and _wy1 > K.WIRE_Y1,
    "pocket spans %.2f..%.2f vs wire %.2f..%.2f (margins %.2f / %.2f mm)"
    % (_wy0, _wy1, K.WIRE_Y0, K.WIRE_Y1, K.WIRE_Y0 - _wy0, _wy1 - K.WIRE_Y1))
chk(_wy1 <= 17.0 - K.SW_CUT / 2 + 0.05,
    "pocket top %.2f stays inside the row-above cutout edge %.2f"
    % (_wy1, 17.0 - K.SW_CUT / 2))
for _c, _sz in K.STABS:
    _s = K.STAB_SPACING[_sz]
    _wire_half = _s + 0.8   # the wire runs ~0.8 past each stab centre
    _pocket_half = _s + 3.375 + K.STAB_CLEAR
    chk(_pocket_half > _wire_half,
        "%.2fu pocket half-span %.2f covers the wire half-span %.2f"
        % (_sz, _pocket_half, _wire_half))
dz = K.PLATE_GAP + (K.DIODE_RELIEF_D if K.DIODE_RELIEF else 0.0)
chk(dz - 1.80 > 0.35, "plate clears a DO-35 diode (1.80) by %.2f mm%s"
    % (dz - 1.80, " (with relief pockets)" if K.DIODE_RELIEF else ""))
chk(K.PLATE_T - max(K.DIODE_RELIEF_D, K.WIRE_RELIEF_D) >= 0.7,
    "plate left over a relief pocket: %.2f mm"
    % (K.PLATE_T - max(K.DIODE_RELIEF_D, K.WIRE_RELIEF_D)))
chk(K.Z_PLATE_TOP <= K.Z_PCB_TOP + 5.30,
    "plate top is %.2f mm below the Choc V2 shoulder (5.30)"
    % (K.Z_PCB_TOP + 5.30 - K.Z_PLATE_TOP))
chk(K.PLATE_GAP + K.WIRE_RELIEF_D > 2.39 + 0.4,
    "stab wire relief pocket clears the wire by %.2f mm"
    % (K.PLATE_GAP + K.WIRE_RELIEF_D - 2.39))
chk(K.STANDOFF > 5.44, "floor clears the EC11 legs (5.44) by %.2f mm" % (K.STANDOFF - 5.44))
chk(abs((K.Z_USB_TOP - K.Z_PCB_TOP) - K.USB_TOP_ABOVE_PCB) < 0.01,
    "modelled USB top %.2f matches the measured %.2f above the PCB"
    % (K.Z_USB_TOP - K.Z_PCB_TOP, K.USB_TOP_ABOVE_PCB))
chk(K.Z_USB_TOP < K.USB_OPEN_TOP, "USB body top %.2f under opening top %.2f"
    % (K.Z_USB_TOP, K.USB_OPEN_TOP))
chk(K.WALL_TOP - (K.USB_OPEN_TOP + K.USB_CHAMFER) >= 1.0,
    "wall left above the USB chamfer: %.2f mm"
    % (K.WALL_TOP - K.USB_OPEN_TOP - K.USB_CHAMFER))
chk(K.WALL_TOP - K.USB_OPEN_TOP >= 1.5, "wall above the USB opening: %.2f mm"
    % (K.WALL_TOP - K.USB_OPEN_TOP))
chk(K.USB_OPEN_BOT < K.Z_MCU_TOP, "opening bottom %.2f below daughterboard top %.2f"
    % (K.USB_OPEN_BOT, K.Z_MCU_TOP))

print()
print("-- knob vs the measured encoder stem --")
z_stem = K.Z_PCB_TOP + K.ENC_STEM_TOP_ABOVE_PCB
print("  info  stem top %.2f above the PCB (case Z %.2f)"
      % (K.ENC_STEM_TOP_ABOVE_PCB, z_stem))
knob = K.build_knob(True)
kb = knob.bounding_box()
chk(kb.max.Z > z_stem, "knob top %.2f covers the stem top %.2f" % (kb.max.Z, z_stem))
chk(kb.min.Z > K.Z_PLATE_TOP, "knob underside %.2f clears the plate top %.2f"
    % (kb.min.Z, K.Z_PLATE_TOP))
print("  info  knob is %.1f dia x %.1f tall" % (kb.size.X, kb.size.Z))

# probe the bore: below the shaft's flat it must be a full round hole
from build123d import Pos, Cylinder
z_flat_shaft = K.Z_PCB_TOP + K.ENC_FLAT_START_ABOVE_PCB
solid_at = {}
for z in (z_flat_shaft - 1.5, z_flat_shaft - 0.5, z_flat_shaft + 1.0,
          z_flat_shaft + 5.0):
    # material inside a 6.2 dia cylinder = the flat intruding into the bore
    # must be a CYLINDER: a square probe against a round bore always catches
    # the corners and reads as a false positive
    probe = Pos(0, 0, z) * Cylinder(
        radius=(K.SHAFT_D + K.SHAFT_FIT) / 2.0 - 0.05, height=0.2)
    v = knob & probe
    solid_at[round(z - K.Z_PCB_TOP, 2)] = 0.0 if v is None else v.volume
for z, vol in sorted(solid_at.items()):
    tag = "flat present" if vol > 1e-6 else "clear round bore"
    print("  info  %5.2f above PCB: %-16s (%.3f mm3 in the bore envelope)"
          % (z, tag, vol))
below = [v for z, v in solid_at.items() if z < K.ENC_FLAT_START_ABOVE_PCB]
above = [v for z, v in solid_at.items() if z > K.ENC_FLAT_START_ABOVE_PCB + 0.5]
chk(all(v < 1e-6 for v in below),
    "bore is fully round below the shaft flat (starts %.2f above the PCB)"
    % K.ENC_FLAT_START_ABOVE_PCB)
chk(all(v > 1e-6 for v in above), "bore is keyed above the shaft flat")
eng = K.ENC_STEM_TOP_ABOVE_PCB - (K.ENC_FLAT_START_ABOVE_PCB + K.FLAT_MARGIN)
chk(eng > 5.0, "keyed engagement along the flat: %.2f mm" % eng)

print()
print("-- fasteners --")
boss_wall = (K.BOSS_D - K.INSERT_D) / 2
chk(boss_wall >= 1.5, "wall around the heat-set insert: %.2f mm" % boss_wall)
grip = K.PLATE_T + K.PLATE_GAP + K.PCB_T
print("  info  screw grip under head: %.2f mm  + %.1f into the insert = %.2f"
      % (grip, K.INSERT_L, grip + K.INSERT_L))
print("  info  -> use M3 x %d countersunk" % (round((grip + K.INSERT_L) / 2) * 2))
chk(K.FLOOR - 1.5 >= 1.0, "material under the screw pilot: %.2f mm" % (K.FLOOR - 1.5))
chk(K.INSERT_L + 1.0 <= K.STANDOFF + K.FLOOR - 1.5,
    "insert pocket fits in boss+floor (%.1f available)" % (K.STANDOFF + K.FLOOR - 1.5))

print()
print("-- machinability: boss islands --")
px0, px1 = K.CX - K.POCKET_W / 2, K.CX + K.POCKET_W / 2
py0, py1 = K.CY - K.POCKET_H / 2, K.CY + K.POCKET_H / 2
r = K.BOSS_D / 2
free, merged_n, narrow = [], 0, []
for x, y in K.HOLES:
    g = min((x - r) - px0, px1 - (x + r), (y - r) - py0, py1 - (y + r))
    if g < K.BOSS_WALL_MERGE:
        merged_n += 1
    else:
        free.append(g)
        if g < 4.0:
            narrow.append((x, y, g))
print("  info  %d bosses blended into the wall, %d free-standing"
      % (merged_n, len(free)))
chk(not narrow, "no boss leaves a slot under 4.0 mm (%d do)" % len(narrow))
chk(not free or min(free) >= 4.0,
    "narrowest remaining slot: %.1f mm" % (min(free) if free else 999))

print()
print("-- ledge --")
chk(K.LEDGE_DROP > 0.05,
    "ledge sits %.2f mm below the plate underside, so the plate lands on the "
    "collars not the ledge" % K.LEDGE_DROP)

print()
print("-- bosses vs pocket wall --")
bm = 1e9
for x, y in K.HOLES:
    bm = min(bm, x - K.BOSS_D / 2 - (K.CX - K.POCKET_W / 2),
             (K.CX + K.POCKET_W / 2) - (x + K.BOSS_D / 2),
             y - K.BOSS_D / 2 - (K.CY - K.POCKET_H / 2),
             (K.CY + K.POCKET_H / 2) - (y + K.BOSS_D / 2))
print("  info  nominal boss-to-wall gap before blending: %.2f mm" % bm)

print()
print("=" * 60)
print("FAILURES: %d   WARNINGS: %d" % (len(FAIL), len(WARN)))
for f in FAIL:
    print("  FAIL", f)
